"""
Helper for running LibreOffice (soffice) in environments where AF_UNIX
sockets may be blocked (e.g., sandboxed VMs).  Detects the restriction
at runtime and applies an LD_PRELOAD shim if needed.

Usage:
    from office.soffice import run_soffice, get_soffice_env

    # Option 1 – run soffice directly
    result = run_soffice(["--headless", "--convert-to", "pdf", "input.docx"])

    # Option 2 – get env dict for your own subprocess calls
    env = get_soffice_env()
    subprocess.run(["soffice", ...], env=env)
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows 上 soffice 常不在 PATH:找几个默认安装位置兜底
_WIN_SOFFICE = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)


def find_soffice() -> str:
    """返回可执行的 soffice 路径;找不到就抛 SystemExit 并说清怎么办。"""
    exe = shutil.which("soffice") or shutil.which("soffice.exe") or shutil.which("libreoffice")
    if exe:
        return exe
    for p in _WIN_SOFFICE:
        if os.path.isfile(p):
            return p
    raise SystemExit("找不到 LibreOffice（soffice）。装一个或用到的命令换成 openpyxl 直接读写；"
                     "Windows 默认装在 C:\\Program Files\\LibreOffice\\。")


def get_soffice_env() -> dict:
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"

    if _needs_shim():
        shim = _ensure_shim()
        env["LD_PRELOAD"] = str(shim)

    return env


def run_soffice(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    env = get_soffice_env()
    return subprocess.run([find_soffice()] + args, env=env, **kwargs)



_SHIM_SO = Path(tempfile.gettempdir()) / "lo_socket_shim.so"


def _needs_shim() -> bool:
    # LD_PRELOAD 是 Linux 的东西;Windows / 没编 AF_UNIX 的 Python 连常量都没有,
    # 旧代码直接 socket.AF_UNIX 抛 AttributeError,import 本模块即崩。
    if sys.platform.startswith("win") or not hasattr(socket, "AF_UNIX"):
        return False
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.close()
        return False
    except (OSError, AttributeError):
        return True


def _ensure_shim() -> Path:
    if _SHIM_SO.exists():
        return _SHIM_SO

    src = Path(tempfile.gettempdir()) / "lo_socket_shim.c"
    src.write_text(_SHIM_SOURCE)
    subprocess.run(
        ["gcc", "-shared", "-fPIC", "-o", str(_SHIM_SO), str(src), "-ldl"],
        check=True,
        capture_output=True,
    )
    src.unlink()
    return _SHIM_SO



_SHIM_SOURCE = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

static int (*real_socket)(int, int, int);
static int (*real_socketpair)(int, int, int, int[2]);
static int (*real_listen)(int, int);
static int (*real_accept)(int, struct sockaddr *, socklen_t *);
static int (*real_close)(int);
static int (*real_read)(int, void *, size_t);

/* Per-FD bookkeeping (FDs >= 1024 are passed through unshimmed). */
static int is_shimmed[1024];
static int peer_of[1024];
static int wake_r[1024];            /* accept() blocks reading this */
static int wake_w[1024];            /* close()  writes to this      */
static int listener_fd = -1;        /* FD that received listen()    */

__attribute__((constructor))
static void init(void) {
    real_socket     = dlsym(RTLD_NEXT, "socket");
    real_socketpair = dlsym(RTLD_NEXT, "socketpair");
    real_listen     = dlsym(RTLD_NEXT, "listen");
    real_accept     = dlsym(RTLD_NEXT, "accept");
    real_close      = dlsym(RTLD_NEXT, "close");
    real_read       = dlsym(RTLD_NEXT, "read");
    for (int i = 0; i < 1024; i++) {
        peer_of[i] = -1;
        wake_r[i]  = -1;
        wake_w[i]  = -1;
    }
}

/* ---- socket ---------------------------------------------------------- */
int socket(int domain, int type, int protocol) {
    if (domain == AF_UNIX) {
        int fd = real_socket(domain, type, protocol);
        if (fd >= 0) return fd;
        /* socket(AF_UNIX) blocked – fall back to socketpair(). */
        int sv[2];
        if (real_socketpair(domain, type, protocol, sv) == 0) {
            if (sv[0] >= 0 && sv[0] < 1024) {
                is_shimmed[sv[0]] = 1;
                peer_of[sv[0]]    = sv[1];
                int wp[2];
                if (pipe(wp) == 0) {
                    wake_r[sv[0]] = wp[0];
                    wake_w[sv[0]] = wp[1];
                }
            }
            return sv[0];
        }
        errno = EPERM;
        return -1;
    }
    return real_socket(domain, type, protocol);
}

/* ---- listen ---------------------------------------------------------- */
int listen(int sockfd, int backlog) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        listener_fd = sockfd;
        return 0;
    }
    return real_listen(sockfd, backlog);
}

/* ---- accept ---------------------------------------------------------- */
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        /* Block until close() writes to the wake pipe. */
        if (wake_r[sockfd] >= 0) {
            char buf;
            real_read(wake_r[sockfd], &buf, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return real_accept(sockfd, addr, addrlen);
}

/* ---- close ----------------------------------------------------------- */
int close(int fd) {
    if (fd >= 0 && fd < 1024 && is_shimmed[fd]) {
        int was_listener = (fd == listener_fd);
        is_shimmed[fd] = 0;

        if (wake_w[fd] >= 0) {              /* unblock accept() */
            char c = 0;
            write(wake_w[fd], &c, 1);
            real_close(wake_w[fd]);
            wake_w[fd] = -1;
        }
        if (wake_r[fd] >= 0) { real_close(wake_r[fd]); wake_r[fd]  = -1; }
        if (peer_of[fd] >= 0) { real_close(peer_of[fd]); peer_of[fd] = -1; }

        if (was_listener)
            _exit(0);                        /* conversion done – exit */
    }
    return real_close(fd);
}
"""



if __name__ == "__main__":
    import sys

    # 本文件主要被 recalc.py / docx 转换内部 import;偶尔被当 CLI 直接跑。
    # 以前 `--help` 会被原样透传给 soffice,没装 LibreOffice 就报「找不到 soffice」,
    # 体检脚本逐个跑 `--help` 时会误判成"脚本自己崩了"。
    if any(a in ("-h", "--help") for a in sys.argv[1:]) or len(sys.argv) == 1:
        print(
            "soffice.py —— LibreOffice 无头调用封装(通常由 recalc.py 等内部 import)\n"
            "\n"
            "用法:\n"
            "  python soffice.py <soffice 参数...>   原样透传给 soffice 二进制\n"
            "  python soffice.py --help              显示本说明\n"
            "\n"
            "本机没装 LibreOffice 时只打印安装提示,不影响用 openpyxl 直读直写。\n"
            "Windows 默认安装位置:C:\\Program Files\\LibreOffice\\program\\soffice.exe"
        )
        sys.exit(0)
    result = run_soffice(sys.argv[1:])
    sys.exit(result.returncode)
