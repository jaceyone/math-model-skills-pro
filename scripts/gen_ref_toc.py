#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为长参考文档插入/刷新目录块（带行号，便于按 offset 跳读）。

为什么需要：references/algorithms/ 七份文档合计 1.2 万行，最长 2590 行且无目录。
上下文里只能整篇 read 才能找到 "TOPSIS 在第几行"，代价就是模型干脆不读、凭记忆答题，
算法库退化成死重量。目录块给出行号，读之前就知道该 read(offset=N, limit=M)。

用法：
  python scripts/gen_ref_toc.py            # 只检查，过期/缺失退出码 1
  python scripts/gen_ref_toc.py --write    # 写入/刷新
  python scripts/gen_ref_toc.py --write --min-lines 200 --path references tools

块标记固定，重跑覆盖而非追加，因此可安全重复执行。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from pathlib import Path

BEGIN = "<!-- TOC:BEGIN 自动生成，勿手改；重跑 python scripts/gen_ref_toc.py --write -->"
END = "<!-- TOC:END -->"
HEADER = "## 目录（按行号跳读，不必整篇加载）"

H1 = re.compile(r"^#\s+\S")
H2 = re.compile(r"^##\s+(.+?)\s*$")
SKIP_H2 = {"目录", "目录（按行号跳读，不必整篇加载）"}


def read_lines(path: Path) -> list[str]:
    return io.open(path, encoding="utf-8").read().split("\n")


def strip_toc(lines: list[str]) -> list[str]:
    """移除已有 TOC 块（含前后空行归一）。"""
    if BEGIN not in lines:
        return lines
    i = lines.index(BEGIN)
    j = lines.index(END, i) if END in lines[i:] else len(lines) - 1
    # 去掉块前的 H2 标题（HEADER）
    if i > 0 and lines[i - 1].strip() == HEADER:
        i -= 1
    out = lines[:i] + lines[j + 1:]
    # 折叠三连空行
    while True:
        s = "\n".join(out)
        if "\n\n\n" in s:
            out = s.replace("\n\n\n", "\n\n").split("\n")
        else:
            break
    return out


def build_block(lines: list[str], offset: int) -> list[str]:
    """按 offset（块本身占的行数）重算行号并生成块。"""
    rows = []
    for idx, line in enumerate(lines, 1):
        m = H2.match(line)
        if not m:
            continue
        title = m.group(1)
        if title in SKIP_H2:
            continue
        rows.append((idx + offset, title))
    if len(rows) < 3:
        return []
    out = [BEGIN, HEADER, "", "| # | 小节 | 行号 |", "|---|---|---|"]
    for n, (ln, title) in enumerate(rows, 1):
        out.append(f"| {n} | {title} | {ln} |")
    out += ["", END]
    return out


def desired(lines: list[str]) -> list[str]:
    """返回应有的完整行序列；offset 迭代到自洽（块行数影响行号）。"""
    base = strip_toc(lines)
    first_h2 = next((i for i, l in enumerate(base) if l.startswith("## ")), None)
    if first_h2 is None:
        return base
    cur = base
    for _ in range(4):
        blk = build_block(base, offset=len(cur) - len(base))
        if not blk:
            return base
        cand = base[:first_h2] + blk + [""] + base[first_h2:]
        if cand == cur:
            return cand
        cur = cand
    return cur


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="技能根目录（默认本脚本上一级）")
    ap.add_argument("--path", nargs="*", default=["references", "tools"],
                    help="相对技能根目录的扫描目录")
    ap.add_argument("--min-lines", type=int, default=300,
                    help="超过多少行才要求目录（skill-creator 建议 300）")
    ap.add_argument("--write", action="store_true", help="写盘（默认只检查）")
    args = ap.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    targets = []
    for sub in args.path:
        for p in (root / sub).rglob("*.md"):
            if "__pycache__" in p.parts:
                continue
            n = len(read_lines(p))
            if n > args.min_lines:
                targets.append((n, p))
    targets.sort()

    stale, added = [], 0
    for n, p in targets:
        lines = read_lines(p)
        want = desired(lines)
        if want == lines:
            continue
        stale.append((n, p, BEGIN in lines))
        if args.write:
            io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(want))
            added += 1

    if not stale:
        print(f"目录体检通过：{len(targets)} 份长文档（>{args.min_lines} 行）目录均为最新")
        return 0

    verb = "已刷新" if args.write else "目录过期/缺失"
    print(f"{verb}：{len(stale)} / {len(targets)} 份长文档")
    for n, p, had in stale:
        print(f"  {'更新' if had else '新增'}  {n:5d} 行  {p.relative_to(root).as_posix()}")
    if not args.write:
        print("\n修复：python scripts/gen_ref_toc.py --write")
        return 1
    print(f"\n写入完成：{added} 份。现在重跑 python scripts/gen_ref_toc.py 应为 0。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
