"""文档链接体检:把 md 里写的技能内部路径逐条对到磁盘上,不存在的报出来。

技能里的 md 是给智能体读的说明书,写错一条路径,智能体就整段绕路或干脆读不到规范。
这类错在渲染、编译、跑闸门时全都看不出来(CHANGELOG 里就记过一次 `references/...`
写错、`scripts/build_prompts.py` 删了没改),所以单列一道静态检查:

    python scripts/check_links.py             # 只看现役文档
    python scripts/check_links.py --all       # 连 CHANGELOG 一起看(历史条目会有意失效)
    python scripts/check_links.py --fix-hint  # 顺便给出最可能的正确路径

判定范围:只查**技能内部**路径——以技能顶层目录开头的写法定点核对;
`figures/`、`code/`、`paper/`、`results/` 这些是工程侧路径,不查。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 技能顶层条目:路径以这些开头才算「技能内部路径」
TOP = ("assets", "references", "scripts", "tools")
TOP_FILES = ("SKILL.md", "README.md", "CHANGELOG.md", "VERSION", "LICENSE")
# 工程侧目录:出现在文档里是正常的,不对着技能核
PROJECT_DIRS = ("figures", "code", "paper", "reports", "results", "input",
                "output", "data", "templates", "src", "build")
EXTS = (".md", ".py", ".tex", ".json", ".svg", ".png", ".pdf", ".jpg", ".jpeg",
        ".yaml", ".yml", ".bib", ".sh", ".txt", ".sty", ".cls", ".html", ".csv")
# 反引号里的整段内容才当路径候选;正文里的裸路径不猜
TICK = re.compile(r"`([^`\n]+)`")
MDLINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
# 中文标点、结尾的引号括号句号,都不是路径的一部分
TRIM = " \t\"'`,.;:!?()[]{}<>，。；：！？、（）【】「」“”‘’*"
# 运行时才生成的目录:文档里写它是正常的,磁盘上没有也正常
RUNTIME = ("/.cache/", "__pycache__", "/.git/")
# 一行里明说「已删除」的,是在记历史,不是写错了链接
REMOVAL = ("已删除", "已移除", "已废弃", "移除", "删除", "deleted", "removed")


def _strip_comment(path: str) -> str:
    """`foo.py  # 说明` / `foo.py（说明）` 只留路径。"""
    for sep in ("  ", " #", "\t", "（", " ("):
        if sep in path:
            path = path.split(sep, 1)[0]
    return path.strip().strip(TRIM)


def candidates(text: str) -> list:
    """从一段 md 文本里抽出可能的技能内部路径。"""
    out = []
    for pat in (TICK, MDLINK):
        for m in pat.finditer(text):
            raw = m.group(1)
            for piece in re.split(r"[\s|]+", raw):
                p = _strip_comment(piece)
                if p:
                    out.append(p)
    return out


def is_skill_path(p: str) -> bool:
    if not p or "://" in p or p.startswith(("http", "mailto:", "#", "-", "~", "$")):
        return False
    # `<母版>.json` 这种是占位符,不是路径
    if any(ch in p for ch in "<>{}") or "…" in p:
        return False
    if any(seg in p.replace("\\", "/") for seg in RUNTIME):
        return False
    if p in TOP_FILES:
        return True
    head = re.split(r"[\\/]", p)[0]
    if head in PROJECT_DIRS:
        return False
    if head not in TOP:
        return False
    # 纯目录名(assets、tools)本身不核;带后缀或带下层的才核
    if p.rstrip("/\\") in TOP:
        return False
    return ("/" in p or "\\" in p or p.lower().endswith(EXTS))


def resolve(p: str, md_dir: str) -> str:
    """按 技能根 → md 所在目录 → 其上各级目录 依次解析。

    文档里三种写法都有:从技能根数起的全路径、从工具根数起的
    `scripts/render_template.py`、从当前目录数起的相对路径。
    """
    rel = p.replace("\\", "/")
    bases = [ROOT]
    cur = os.path.abspath(md_dir)
    while True:
        if cur not in bases:
            bases.append(cur)
        if os.path.normcase(cur) == os.path.normcase(ROOT):
            break
        parent = os.path.dirname(cur)
        if parent == cur or len(parent) < len(ROOT):
            break
        cur = parent
    for base in bases:
        full = os.path.normpath(os.path.join(base, rel))
        if os.path.exists(full):
            return full
        # 允许写成通配:assets/figures/reference/totalflow/*.svg
        if "*" in p or "?" in p:
            import glob
            if glob.glob(full):
                return full
    return ""


def suggest(p: str) -> list:
    """按文件名在技能里找同名文件,给出最短的几个可能是想写的路径。"""
    base = os.path.basename(p.rstrip("/\\").replace("\\", "/"))
    if not base or "*" in base:
        return []
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "__pycache__", ".cache", "node_modules")]
        if base in filenames or base in dirnames:
            rel = os.path.relpath(os.path.join(dirpath, base), ROOT).replace("\\", "/")
            hits.append((rel.count("/"), rel))
    hits.sort()
    return [h[1] for h in hits[:3]]


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="文档链接体检")
    ap.add_argument("--all", action="store_true",
                    help="连 CHANGELOG.md 一起查(历史条目里的旧路径会有意失效)")
    ap.add_argument("--strict-history", action="store_true",
                    help="CHANGELOG 的历史失联也算失败(默认只提示,因为条目录的是改动当时的目录结构)")
    ap.add_argument("--fix-hint", action="store_true", default=True,
                    help="给出最可能的正确路径(默认开)")
    ap.add_argument("--no-hint", dest="fix_hint", action="store_false")
    args = ap.parse_args()

    md_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "__pycache__", ".cache", "node_modules")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
            if not args.all and rel.startswith("CHANGELOG"):
                continue
            md_files.append(rel)
    md_files.sort()

    total = checked = 0
    bad = []           # [(md, 行号, 路径, 建议)]
    for rel in md_files:
        full = os.path.join(ROOT, rel)
        try:
            with open(full, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError as e:
            print(f"[读不了] {rel}: {e}")
            continue
        seen = set()
        for lineno, line in enumerate(lines, 1):
            if any(m in line for m in REMOVAL):
                continue          # 这一行在记「某物已删除」,不是失效链接
            for p in candidates(line):
                total += 1
                if not is_skill_path(p) or p in seen:
                    continue
                seen.add(p)
                checked += 1
                if not resolve(p, os.path.dirname(full)):
                    historic = rel.startswith("CHANGELOG")
                    bad.append((rel, lineno, p, suggest(p) if args.fix_hint else [],
                                historic))

    historic_bad = [b for b in bad if b[4]]
    current_bad = [b for b in bad if not b[4]]
    if not bad:
        print(f"链接体检通过:{len(md_files)} 个 md,核对 {checked} 条技能内部路径,失联 0 条。")
        return 0

    if current_bad:
        print(f"链接体检:{len(md_files)} 个 md,核对 {checked} 条技能内部路径,"
              f"**现役文档失联 {len(current_bad)} 条**\n")
        for rel, lineno, p, hints, _ in current_bad:
            print(f"[失联] {rel}:{lineno}  ->  {p}")
            for h in hints:
                print(f"    可能是:{h}")
        print("\n改法:把文档里的路径改成磁盘上真实存在的写法;"
              "确实删掉的东西,把引用一并删掉或标注「已删除」。")
        return 1

    # 只剩 CHANGELOG 的历史条目:按本文件头的「读法」声明,历史路径有意失效,不算失败
    print(f"链接体检通过:{len(md_files)} 个 md,现役文档失联 0 条;"
          f"CHANGELOG 历史条目 {len(historic_bad)} 条(预期,不计失败)")
    if args.strict_history:
        print("\n--strict-history:以下历史条目的路径已不存在\n")
        for rel, lineno, p, hints, _ in historic_bad:
            print(f"[历史] {rel}:{lineno}  ->  {p}")
            for h in hints:
                print(f"    现在在这:{h}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
