#!/usr/bin/env python3
"""JSON 流程规格 -> TikZ -> PDF/PNG。

用法：
  python flowchart.py flow.json
  python flowchart.py flow.json --no-compile
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

LATEX_SPECIALS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


_MATH_SPAN = re.compile(r"\$[^$]*\$")


def escape(text: str) -> str:
    """转义 LaTeX 特殊字符，但 $...$ 数学段原样保留。

    旧实现逐字符转义，节点里写 `$F^\\star$` 会变成
    `\\$F\\textasciicircum{}...`，xelatex 直接报 Missing $ inserted。
    """
    out, pos = [], 0
    for m in _MATH_SPAN.finditer(text):
        out.append("".join(LATEX_SPECIALS.get(ch, ch) for ch in text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append("".join(LATEX_SPECIALS.get(ch, ch) for ch in text[pos:]))
    return "".join(out)


def load_spec(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "nodes" not in data or not isinstance(data["nodes"], list):
        raise ValueError("spec 缺少 nodes 数组")
    if "edges" not in data or not isinstance(data["edges"], list):
        raise ValueError("spec 缺少 edges 数组")
    return data


def levels(nodes: list[dict], edges: list[list]) -> tuple[dict[str, int], set[tuple[str, str]], list[str]]:
    ids = [n["id"] for n in nodes]
    index = {nid: i for i, nid in enumerate(ids)}
    outgoing: dict[str, list[str]] = defaultdict(list)
    valid = []
    for edge in edges:
        if len(edge) < 2:
            continue
        u, v = edge[0], edge[1]
        if u not in index or v not in index:
            continue
        outgoing[u].append(v)
        valid.append((u, v))

    # DFS 找回边（环）
    state: dict[str, int] = {nid: 0 for nid in ids}  # 0 未访问，1 访问中，2 完成
    back_edges: set[tuple[str, str]] = set()

    def dfs(u: str) -> None:
        state[u] = 1
        for v in outgoing[u]:
            if state[v] == 1:
                back_edges.add((u, v))
            elif state[v] == 0:
                dfs(v)
        state[u] = 2

    for nid in ids:
        if state[nid] == 0:
            dfs(nid)

    # 去掉回边后做 DAG 分层
    indegree = {nid: 0 for nid in ids}
    dag_out: dict[str, list[str]] = defaultdict(list)
    for u, v in valid:
        if (u, v) in back_edges:
            continue
        dag_out[u].append(v)
        indegree[v] += 1

    level = {nid: 0 for nid in ids}
    queue = deque([nid for nid in ids if indegree[nid] == 0])
    while queue:
        u = queue.popleft()
        for v in dag_out[u]:
            level[v] = max(level[v], level[u] + 1)
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return level, back_edges, ids


def build_tex(spec: dict) -> tuple[str, list[str]]:
    nodes = spec["nodes"]
    edges = spec["edges"]
    warnings: list[str] = []
    node_ids = {n["id"] for n in nodes}
    valid_edges = []
    for edge in edges:
        if len(edge) < 2:
            warnings.append(f"忽略无效边：{edge}")
            continue
        if edge[0] not in node_ids or edge[1] not in node_ids:
            warnings.append(f"边引用了不存在的节点：{edge}")
            continue
        valid_edges.append(edge)

    level, back_edges, ids = levels(nodes, valid_edges)
    layout = spec.get("layout", "linear")
    direction = spec.get("direction", "LR" if layout in {"pipeline", "multi_question"} else "TB")
    spacing_x = float(spec.get("spacing_x", 4.2 if direction == "LR" else 4.0))
    # 节点文本按约 20 字折行：层距固定时多行节点会互贴、回边跑出画布，
    # 这里按最长文本自动加层距（单行布局的间距保持原样）
    def _lines_of(text: str) -> int:
        return max(1, -(-len(str(text or "")) // 20))

    max_lines = max((_lines_of(n.get("text", "")) for n in nodes), default=1)
    base_y = float(spec.get("spacing_y", 2.0 if direction == "LR" else 1.8))
    spacing_y = base_y * (1 + 0.45 * (max_lines - 1))

    by_level: dict[int, list[str]] = defaultdict(list)
    for nid in ids:
        by_level[level[nid]].append(nid)

    positions: dict[str, tuple[float, float]] = {}
    for lv, group in by_level.items():
        count = len(group)
        for i, nid in enumerate(group):
            offset = (i - (count - 1) / 2) * spacing_x
            if direction == "LR":
                x = lv * spacing_x
                y = -offset
            else:
                x = offset
                y = -lv * spacing_y
            positions[nid] = (x, y)

    node_by_id = {n["id"]: n for n in nodes}
    lines = [
        r"\documentclass[tikz,border=10pt]{standalone}",
        r"\usepackage{ctex}",
        r"\usetikzlibrary{shapes.geometric,shapes.misc,arrows.meta,positioning,calc,backgrounds}",
        r"\begin{document}",
        r"\begin{tikzpicture}[",
        r"  start/.style={rounded rectangle, draw, fill=green!8, minimum width=2.4cm, minimum height=0.8cm, align=center},",
        r"  end/.style={rounded rectangle, draw, fill=red!8, minimum width=2.4cm, minimum height=0.8cm, align=center},",
        r"  process/.style={rectangle, draw, fill=blue!5, text width=3.2cm, minimum height=0.9cm, align=center},",
        r"  decision/.style={diamond, draw, fill=orange!10, aspect=2.2, text width=2.6cm, align=center, inner sep=2pt},",
        r"  io/.style={trapezium, trapezium left angle=70, trapezium right angle=110, draw, fill=purple!5, text width=3.0cm, align=center},",
        r"  subprocess/.style={rectangle, draw, double, fill=gray!5, text width=3.2cm, minimum height=0.9cm, align=center},",
        r"  edge/.style={-Latex, thick},",
        r"]",
    ]

    title = spec.get("title", "")
    if title:
        lines.append(rf"\node[font=\bfseries\large] at (0, 1.0) {{{escape(title)}}};")

    for nid in ids:
        node = node_by_id[nid]
        kind = node.get("type", "process")
        style = kind if kind in {"start", "end", "process", "decision", "io", "subprocess"} else "process"
        x, y = positions[nid]
        if isinstance(node.get("pos"), (list, tuple)) and len(node["pos"]) == 2:
            x, y = float(node["pos"][0]), float(node["pos"][1])
        text = escape(str(node.get("text", ""))).replace("\n", r"\\")
        lines.append(rf"\node[{style}] ({nid}) at ({x:.2f},{y:.2f}) {{{text}}};")

    for edge in valid_edges:
        u, v = edge[0], edge[1]
        label = str(edge[2]) if len(edge) >= 3 else ""
        route = str(edge[3]) if len(edge) >= 4 else ""
        label_tex = rf" node[midway, above, font=\scriptsize] {{{escape(label)}}}" if label else ""
        if route in {"left", "right"}:
            if direction == "LR":
                anchor = "south" if route == "left" else "north"
                angle = -90 if route == "left" else 90
            else:
                anchor = "west" if route == "left" else "east"
                angle = 180 if route == "left" else 0
            lines.append(
                rf"\draw[edge] ({u}.{anchor}) to[out={angle},in={angle},looseness=1.25]{label_tex} ({v}.{anchor});"
            )
        elif (u, v) in back_edges:
            if direction == "LR":
                lines.append(
                    rf"\draw[edge] ({u}.south) to[out=-90,in=-90,looseness=1.25]{label_tex} ({v}.south);"
                )
            else:
                lines.append(
                    rf"\draw[edge] ({u}.east) to[out=0,in=0,looseness=1.25]{label_tex} ({v}.east);"
                )
        else:
            lines.append(rf"\draw[edge] ({u}) --{label_tex} ({v});")

    lines += [r"\end{tikzpicture}", r"\end{document}", ""]
    return "\n".join(lines), warnings


def compile_tex(tex: Path, dpi: int = 300) -> tuple[bool, str]:
    if not shutil.which("xelatex"):
        return False, "未找到 xelatex"
    proc = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=str(tex.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        tail = (proc.stdout or "").strip().splitlines()[-8:]
        return False, "\n".join(tail)
    pdf = tex.with_suffix(".pdf")
    if pdf.exists():
        png = tex.with_suffix(".png")
        # 先删旧 PNG：否则上一轮幸存的文件会让 exists() 判成功，PDF 更新了 PNG 还是旧的
        if png.exists():
            try:
                png.unlink()
            except OSError:
                pass
        note = ""
        if shutil.which("pdftoppm"):
            ppm = subprocess.run(
                ["pdftoppm", "-png", "-r", str(dpi), "-singlefile", str(pdf), str(tex.with_suffix(""))],
                cwd=str(tex.parent),
                capture_output=True,
                text=True,
                errors="replace",
            )
            if not png.exists():
                # 旧实现把 stderr 吞了：编译成功但 PNG 静默缺失，调用方以为一切正常
                tail = (ppm.stderr or ppm.stdout or "").strip().splitlines()[-3:]
                note = "PDF 已出，但 PNG 没生成：" + " / ".join(tail)
        else:
            note = "本机没有 pdftoppm，改走 PyMuPDF 兜底"
        if not png.exists():
            # pdftoppm 缺失或失败：用 PyMuPDF 兜底出 PNG（主链路只要求 PDF，PNG 是预览用）
            try:
                import fitz  # PyMuPDF

                with fitz.open(str(pdf)) as doc:
                    doc[0].get_pixmap(dpi=dpi).save(str(png))
                note = ""
            except Exception as exc:  # noqa: BLE001
                note = (note + f"；PyMuPDF 兜底也失败：{exc}") if note else f"PNG 未生成：{exc}"
        return True, note
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 TikZ 流程图")
    parser.add_argument("spec", help="flow.json 规格文件")
    parser.add_argument("--out", help="输出 .tex 路径")
    parser.add_argument("--no-compile", action="store_true", help="只生成 .tex")
    parser.add_argument("--dpi", type=int, default=300, help="PNG dpi")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"规格不存在：{spec_path}", file=sys.stderr)
        return 1
    try:
        spec = load_spec(spec_path)
    except Exception as exc:
        print(f"规格解析失败：{exc}", file=sys.stderr)
        return 1

    tex_text, warnings = build_tex(spec)
    out = Path(args.out) if args.out else spec_path.with_suffix(".tex")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tex_text, encoding="utf-8")
    print(f"已生成 {out}")
    for warning in warnings:
        print(f"  WARN {warning}", file=sys.stderr)

    if not args.no_compile:
        ok, error = compile_tex(out, args.dpi)
        if not ok:
            print("xelatex 编译失败：\n" + error, file=sys.stderr)
            return 1
        print(f"已生成 {out.with_suffix('.pdf')}")
        if out.with_suffix(".png").exists():
            print(f"已生成 {out.with_suffix('.png')}")
        elif error:
            print(f"  WARN {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
