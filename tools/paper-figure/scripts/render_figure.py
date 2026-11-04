# -*- coding: utf-8 -*-
"""论文主图渲染：SVG -> PNG（Edge 无头截图）+ PDF（Edge 打印）。

用法：
  python render_figure.py figure.svg
  python render_figure.py figure.svg --no-pdf
  python render_figure.py figure.svg --html

默认输出同目录同名 .png 与 .pdf；--html 额外输出预览页。
依赖：Windows/macOS 的 Edge；无需第三方包。
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE_CANDIDATES = [
    os.environ.get("MSEDGE", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/microsoft-edge",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_edge() -> str:
    for candidate in EDGE_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    found = shutil.which("msedge") or shutil.which("microsoft-edge")
    if found:
        return found
    sys.exit("找不到 Edge（PNG/PDF 渲染需要）。可设环境变量 MSEDGE 指向 msedge.exe。")


def parse_svg_size(svg_text: str) -> tuple[float, float]:
    match = re.search(
        r'viewBox\s*=\s*["\']\s*([\d.eE+-]+)[\s,]+([\d.eE+-]+)[\s,]+([\d.eE+-]+)[\s,]+([\d.eE+-]+)',
        svg_text,
    )
    if match:
        return float(match.group(3)), float(match.group(4))
    width = re.search(r'width\s*=\s*["\']([\d.]+)', svg_text)
    height = re.search(r'height\s*=\s*["\']([\d.]+)', svg_text)
    if not width or not height:
        sys.exit("无法解析 SVG 尺寸（需要 width/height 或 viewBox）")
    return float(width.group(1)), float(height.group(1))


def inline_html(svg_text: str, width: float, height: float, scale: float = 1.0) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>@page{{size:{width * scale}px {height * scale}px;margin:0}}"
        "html,body{margin:0;padding:0;background:#fff}"
        f"svg{{width:{width * scale}px;height:{height * scale}px;display:block}}</style>"
        "</head><body>" + svg_text + "</body></html>"
    )


def screenshot(edge: str, html_path: Path, out_png: Path, width: int, height: int) -> None:
    with tempfile.TemporaryDirectory(prefix="figshot_") as td:
        shot = Path(td) / "shot.png"
        subprocess.run(
            [
                edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                f"--screenshot={shot}", f"--window-size={width},{height}",
                "--default-background-color=FFFFFFFF", html_path.as_uri(),
            ],
            capture_output=True,
            timeout=120,
        )
        if not shot.exists():
            sys.exit("Edge 截图失败：未产出 PNG（检查 Edge 版本是否支持 --headless=new）")
        shutil.copy2(shot, out_png)


def print_pdf(edge: str, html_path: Path, out_pdf: Path) -> None:
    subprocess.run(
        [
            edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={out_pdf}", html_path.as_uri(),
        ],
        capture_output=True,
        timeout=120,
    )
    if not out_pdf.exists():
        sys.exit("Edge 打印 PDF 失败（检查 --print-to-pdf 是否可用）")


def main() -> int:
    parser = argparse.ArgumentParser(description="SVG -> PNG + PDF")
    parser.add_argument("svg", help="输入 .svg 文件")
    parser.add_argument("-s", "--scale", type=float, default=float(os.environ.get("PF_SCALE") or 2),
                        help="PNG 缩放倍数（默认 2）")
    parser.add_argument("--no-png", action="store_true", help="不出 PNG")
    parser.add_argument("--no-pdf", action="store_true", help="不出 PDF")
    parser.add_argument("--html", action="store_true", help="额外输出 HTML 预览")
    args = parser.parse_args()

    svg_path = Path(args.svg).resolve()
    if not svg_path.exists():
        sys.exit(f"找不到 {svg_path}")
    svg_text = svg_path.read_text(encoding="utf-8")
    if "</svg>" not in svg_text:
        sys.exit("SVG 未正常闭合（缺 </svg>），先修图再渲染。")
    width, height = parse_svg_size(svg_text)
    stem = svg_path.with_suffix("")

    if args.html:
        html = (
            "<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'>"
            f"<title>{svg_path.name}</title>"
            "<style>body{margin:0;background:#f3f4f6;display:flex;justify-content:center;"
            "align-items:flex-start;min-height:100vh}main{background:#fff;box-shadow:0 4px 24px #0002;"
            f"margin:24px;max-width:min(96vw,{int(width)}px)}}main svg{{width:100%;height:auto;display:block}}"
            "</style></head><body><main>" + svg_text + "</main></body></html>"
        )
        html_path = stem.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        print(f"HTML 预览: {html_path}")

    edge = find_edge()
    tmp_dir = Path(tempfile.mkdtemp(prefix="figrender_"))

    if not args.no_png:
        html_png = tmp_dir / "png.html"
        html_png.write_text(inline_html(svg_text, width, height, args.scale), encoding="utf-8")
        out_png = stem.with_suffix(".png")
        screenshot(edge, html_png, out_png, int(width * args.scale), int(height * args.scale))
        print(f"PNG: {out_png}（{int(width * args.scale)}x{int(height * args.scale)}）")

    if not args.no_pdf:
        html_pdf = tmp_dir / "pdf.html"
        html_pdf.write_text(inline_html(svg_text, width, height, 1), encoding="utf-8")
        out_pdf = stem.with_suffix(".pdf")
        print_pdf(edge, html_pdf, out_pdf)
        print(f"PDF: {out_pdf}")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
