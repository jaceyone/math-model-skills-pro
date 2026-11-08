#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能自检（G-Skill）：技能包本身是否符合 skill 包的工程约定。

项目的 S0–S4 有门禁，但技能自己一直没有。SKILL.md 的 frontmatter 写坏、引用的
参考文件被改名、SKILL.md 涨到读不动、新加的脚本语法错——这些都不会在跑项目时
报错，只会让模型悄悄不触发或悄悄读错文件。本脚本把这类"静默失效"变成退出码。

检查项（FAIL 即退出码 1）：
  S1  SKILL.md frontmatter：name（kebab ≤64）/ description（≤1024，无尖括号）/ 键名合法
  S2  子工具 SKILL.md frontmatter 同样合法
  S3  SKILL.md 正文 ≤ 500 行（skill-creator 的渐进披露上限）
  S4  SKILL.md 里出现的 references/ scripts/ tools/ assets/ 路径全部解析得到
  S5  长参考文档（>300 行）目录块与正文同步（gen_ref_toc.py）
  S6  所有 .py 语法可编译
  S7  md/py/tex 无 UTF-8 BOM
  S8  evals/evals.json 存在且结构合法
  S9  没有任何 .md 完全无人引用（WARN，不判失败）

用法：
  python scripts/check_skill.py
  python scripts/check_skill.py --quiet     # 只打 FAIL/WARN
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_FM = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_TOKEN = re.compile(r"(?:^|[\s`(（«\[])((?:references|scripts|tools|assets)/[A-Za-z0-9_./\-*<>{}]+)")
SKIP_DIRS = {".git", "_tmp", "__pycache__", "node_modules", ".venv"}


class Report:
    def __init__(self) -> None:
        self.fails: list[str] = []
        self.warns: list[str] = []

    def check(self, ok: bool, label: str, detail: str = "", warn: bool = False) -> None:
        if ok:
            print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))
        elif warn:
            self.warns.append(label)
            print(f"  WARN  {label}" + (f"  ({detail})" if detail else ""))
        else:
            self.fails.append(label)
            print(f"  FAIL  {label}" + (f"  ({detail})" if detail else ""))


def load_frontmatter(path: Path) -> tuple[dict, str, str]:
    text = io.open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text, ""
    raw = m.group(1)
    fm: dict = {}
    for line in raw.split("\n"):
        mm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if mm:
            val = mm.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            fm[mm.group(1)] = val
    return fm, text, m.group(0)


def check_frontmatter(rep: Report, path: Path, rel: str) -> None:
    fm, text, blk = load_frontmatter(path)
    rep.check(bool(blk), f"{rel} 有 YAML frontmatter")
    if not blk:
        return
    rep.check("name" in fm, f"{rel} 有 name")
    rep.check("description" in fm, f"{rel} 有 description")
    name = fm.get("name", "")
    rep.check(bool(KEBAB.match(name)) and len(name) <= 64,
              f"{rel} name 为 kebab-case 且 ≤64 字符", f"name={name!r}")
    desc = fm.get("description", "")
    rep.check(0 < len(desc) <= 1024, f"{rel} description 长度 1–1024", f"{len(desc)} 字符")
    rep.check(not ("<" in desc or ">" in desc), f"{rel} description 无尖括号")
    bad = set(fm) - ALLOWED_FM
    rep.check(not bad, f"{rel} frontmatter 键均合法", f"多余键={sorted(bad)}" if bad else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    skill_md = root / "SKILL.md"
    rep = Report()

    print("S1 SKILL.md frontmatter")
    if not skill_md.exists():
        print("  FAIL  SKILL.md 不存在")
        return 1
    check_frontmatter(rep, skill_md, "SKILL.md")

    print("\nS2 子工具 SKILL.md frontmatter")
    subs = sorted(p for p in (root / "tools").rglob("SKILL.md") if "__pycache__" not in p.parts)
    for p in subs:
        check_frontmatter(rep, p, p.relative_to(root).as_posix())
    if not subs:
        print("  PASS  （无子 SKILL.md）")

    print("\nS3 SKILL.md 行数预算")
    n_lines = len(io.open(skill_md, encoding="utf-8").read().split("\n"))
    rep.check(n_lines <= 500, "SKILL.md ≤ 500 行",
              f"{n_lines} 行" + ("，建议把细节移入 references/" if n_lines > 460 else ""))

    print("\nS4 SKILL.md 内部路径解析")
    text = io.open(skill_md, encoding="utf-8").read()
    files = [p.relative_to(root).as_posix() for p in root.rglob("*")
             if p.is_file() and not (set(p.parts) & SKIP_DIRS)]
    dirs = {str(Path(f).parent.as_posix()) for f in files} | {""}
    tokens = sorted(set(PATH_TOKEN.findall(text)))
    missing = []
    for tok in tokens:
        t = tok.rstrip(".,;)）]」")
        if (root / t).exists() or any(f == t or f.startswith(t + "/") for f in files) or t in dirs:
            continue
        if "*" in t or "<" in t or "{" in t:          # 通配/占位写法：父目录在即可
            if Path(t).parent.as_posix() in dirs or (root / Path(t).parent).exists():
                continue
        if any(f.startswith(t) for f in files):        # 前缀匹配（如 01 → 01-xxx.md）
            continue
        missing.append(t)
    rep.check(not missing, f"SKILL.md 引用的 {len(tokens)} 条路径全部可达",
              "失联=" + ", ".join(missing) if missing else "")

    print("\nS5 长参考文档目录同步")
    toc = subprocess.run([sys.executable, str(root / "scripts" / "gen_ref_toc.py"),
                          "--root", str(root)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    rep.check(toc.returncode == 0, "长文档（>300 行）目录块与正文同步",
              (toc.stdout or "").strip().splitlines()[0] if toc.stdout else "")

    print("\nS6 脚本语法")
    py = [p for p in root.rglob("*.py") if not (set(p.parts) & SKIP_DIRS)]
    broken = []
    for p in py:
        try:
            compile(io.open(p, encoding="utf-8").read(), str(p), "exec")
        except Exception as e:  # noqa: BLE001
            broken.append(f"{p.relative_to(root).as_posix()}: {type(e).__name__}")
    rep.check(not broken, f"{len(py)} 个 .py 语法可编译", "; ".join(broken[:5]))

    print("\nS7 编码（无 BOM）")
    bom = []
    for p in root.rglob("*"):
        if not p.is_file() or (set(p.parts) & SKIP_DIRS) or p.suffix not in {".md", ".py", ".tex"}:
            continue
        with open(p, "rb") as fh:
            if fh.read(3) == b"\xef\xbb\xbf":
                bom.append(p.relative_to(root).as_posix())
    rep.check(not bom, "md/py/tex 无 UTF-8 BOM", ", ".join(bom[:5]))

    print("\nS8 evals")
    ev = root / "evals" / "evals.json"
    if ev.exists():
        try:
            data = json.load(io.open(ev, encoding="utf-8"))
            items = data.get("evals", [])
            ok = bool(items) and all(i.get("prompt") for i in items)
            rep.check(ok, "evals/evals.json 结构合法", f"{len(items)} 条用例")
        except json.JSONDecodeError as e:
            rep.check(False, "evals/evals.json 可解析", str(e)[:80])
    else:
        rep.check(False, "evals/evals.json 存在", "缺回归用例：技能改动无法自证有效")

    print("\nS9 孤儿文档（WARN）")
    md = [f for f in files if f.endswith(".md")]
    corpus = "\n".join(io.open(root / f, encoding="utf-8").read() for f in md
                       if f != "CHANGELOG.md")
    orphans = [f for f in md if f != "CHANGELOG.md" and Path(f).name not in corpus
               and f not in ("README.md", "SKILL.md", "VENDORED.md", "LICENSE_NOTICE.md")]
    rep.check(not orphans, "所有 .md 至少被引用一次", ", ".join(orphans[:6]), warn=True)

    print("\n" + "=" * 60)
    if rep.fails:
        print(f"G-Skill FAIL：{len(rep.fails)} 项失败，{len(rep.warns)} 项警告")
        for f in rep.fails:
            print(f"  - {f}")
        return 1
    print(f"G-Skill PASS：0 项失败，{len(rep.warns)} 项警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
