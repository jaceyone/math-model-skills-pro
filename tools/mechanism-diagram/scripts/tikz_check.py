#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机理图 TikZ 静态自检：能机判的三件交给它，判不了的明确交给人。

为什么只做这几件：节点重叠、中文超宽、连线穿框都需要知道每个节点的真实
包围盒，静态解析 TikZ 算不准（`text width` / `minimum width` / 字体宽度 / 缩放
互相影响）。写一个"看起来能判"的检测器比没有更糟——它会把假阳性报成
CRITICAL，人就再也不信 CRITICAL 了。所以只收**确定性**检查，其余列进目检清单。

检查项：
  T1 编译日志  `! ` 报错 / `Overfull \\hbox` → CRITICAL；`Underfull` → WARN
  T2 裸颜色    同一个节点选项里有 `fill=<非 none>`，它的文本里又写裸颜色名
               → CRITICAL（裸颜色会覆盖填充，那块图直接变成单色）
  T3 环境配对  tikzpicture / scope / axis 的 begin 与 end 数量不符 → CRITICAL
  T4 曲线      `to[out=`、`bend left/right`、`controls` → WARN
               （机理图允许，流程图/技术路线图要求正交折线，按图种自己判）
  T5 结果数值  文本里出现带 kN / N / % 的数值 → WARN（机理图不标求解结果；
               几何尺寸如 12 mm 属参数，不报）

明确不做（必须目检）：节点重叠、中文超宽、连线穿过节点、箭头是否落在框边。

用法：
  python tools/mechanism-diagram/scripts/tikz_check.py figures/mech_x.tex
  python tools/mechanism-diagram/scripts/tikz_check.py figures/mech_x.tex --log figures/mech_x.log
  （不给 --log 时，同目录同名 .log 存在就自动读）

退出码：0 无 CRITICAL / 1 有 CRITICAL / 2 用法或文件错误
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

COLORS = (
    "black white red green blue cyan magenta yellow gray grey orange purple "
    "brown lime olive teal violet pink lightgray darkgray lightblue darkred"
).split()

BARE_COLOR = re.compile(r"(?<![A-Za-z\\{])(?:%s)(?![A-Za-z])" % "|".join(COLORS))
FILL = re.compile(r"fill\s*=\s*([A-Za-z0-9_!]+)")
# 一个节点：连续选项 + 可选 at 坐标 + 文本
NODE = re.compile(r"(?:\\node|(?<![\w\\])node)\s*((?:\[[^\]]*\]\s*)+)(?:at\s*\([^()]*\)\s*)?\{([^{}]*)\}")
NUMBER_CLAIM = re.compile(r"[=≈][ \t]*-?\d+(?:\.\d+)?[ \t]*(?:kN|N|%)")


class Report:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, str]] = []

    def add(self, level: str, code: str, msg: str, cap: int | None = None) -> None:
        if cap is not None and sum(1 for _, c, _ in self.items if c == code) >= cap:
            return
        self.items.append((level, code, msg))

    def count(self, level: str) -> int:
        return sum(1 for lv, _, _ in self.items if lv == level)

    def dump(self) -> None:
        order = {"CRITICAL": 0, "WARN": 1, "INFO": 2}
        for level, code, msg in sorted(self.items, key=lambda x: order.get(x[0], 9)):
            print(f"[{level}] {code}  {msg}")


def lineno(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def check_tex(path: str, rep: Report) -> None:
    text = io.open(path, encoding="utf-8", errors="replace").read()

    # T3 环境配对
    for env in ("tikzpicture", "scope", "axis", "pgfonlayer"):
        b = len(re.findall(r"\\begin\{%s\}" % env, text))
        e = len(re.findall(r"\\end\{%s\}" % env, text))
        if b != e:
            rep.add("CRITICAL", "T3", f"{env}: begin={b} 与 end={e} 不配对")

    # T2 裸颜色（节点作用域）
    for m in NODE.finditer(text):
        opts, body = m.group(1), m.group(2)
        fills = FILL.findall(opts)
        if not fills or all(f.lower() == "none" for f in fills):
            continue
        bare = sorted({c.group(0) for c in BARE_COLOR.finditer(body)})
        if bare:
            rep.add("CRITICAL", "T2",
                    f"第 {lineno(text, m.start())} 行：节点 fill={fills[0]}，文本里又有裸颜色名 "
                    f"{bare} —— 会盖掉填充，改成 text=<颜色>")

    # T4 曲线
    for pat, why in ((r"to\s*\[\s*out\s*=", "to[out=..]"),
                     (r"bend\s+(?:left|right)", "bend left/right"),
                     (r"\bcontrols\b", "controls")):
        for m in re.finditer(pat, text):
            rep.add("WARN", "T4",
                    f"第 {lineno(text, m.start())} 行用了 {why}——机理图可以，"
                    f"流程图/技术路线图须改正交折线", cap=3)

    # T5 结果数值
    for m in NUMBER_CLAIM.finditer(text):
        rep.add("WARN", "T5",
                f"第 {lineno(text, m.start())} 行文本里有结果数值「{m.group(0).strip()}」"
                f"——机理图不标求解结果", cap=3)


def check_log(path: str, rep: Report) -> None:
    if not os.path.exists(path):
        rep.add("INFO", "T1", f"没有编译日志 {path}（先 xelatex 一遍再来）")
        return
    log = io.open(path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"^! (.+)$", log, re.M):
        rep.add("CRITICAL", "T1", f"编译报错：{m.group(1)[:120]}")
    over = len(re.findall(r"Overfull \\hbox", log))
    under = len(re.findall(r"Underfull \\hbox", log))
    if over:
        rep.add("CRITICAL", "T1", f"Overfull \\hbox × {over}（排版溢出，出图必改）")
    if under:
        rep.add("WARN", "T1", f"Underfull \\hbox × {under}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex", help="机理图 .tex 路径")
    ap.add_argument("--log", default=None, help="编译日志路径（默认同目录同名 .log）")
    args = ap.parse_args()

    if not os.path.exists(args.tex):
        print(f"找不到 {args.tex}")
        return 2
    log = args.log or os.path.splitext(args.tex)[0] + ".log"

    rep = Report()
    check_tex(args.tex, rep)
    check_log(log, rep)

    if not rep.items:
        print("T1 编译日志 / T2 裸颜色 / T3 环境配对 / T4 曲线 / T5 结果数值：全部通过")
    else:
        rep.dump()

    crit = rep.count("CRITICAL")
    print()
    print(f"CRITICAL {crit} / WARN {rep.count('WARN')} / INFO {rep.count('INFO')}")
    print("仍需目检（静态判不了）：节点是否重叠、中文是否超宽、连线是否穿框、箭头是否落在框边")
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main())
