# -*- coding: utf-8 -*-
"""流程图路线 B：SVG -> 可编辑 HTML -> PNG / PDF（纯标准库，Edge 无头渲染）。

路线 A（TikZ）见同目录 flowchart.py：JSON -> .tex -> xelatex -> .pdf/.png。
本脚本只管 SVG 路线：SVG 是 XML，可直接内联进 HTML 在浏览器里改字/挪框，
再用 Edge（或 cairosvg，若已装）导回 PNG/PDF，全程不需要 LaTeX。

用法：
  python svg_flow.py figures/flow_q1.svg                  # html + png + pdf
  python svg_flow.py figures/flow_q1.svg --html           # 只出可编辑 HTML
  python svg_flow.py figures/flow_q1.svg --png -s 3       # 只出 PNG，3 倍分辨率
  python svg_flow.py figures/flow_q1.svg --pdf --outdir figures

产物（与 SVG 同目录、同名）：
  flow_q1.html  浏览器打开即可改字；「下载 SVG」把改好的图存回 .svg
  flow_q1.png   预览/汇报用（默认 2 倍，即 DPI≈192）
  flow_q1.pdf   进论文用（矢量）

改完 SVG 后重跑本脚本刷新 PNG/PDF，并把 manifest 里该图 status 置回 ok。
"""

from __future__ import annotations

import argparse
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
    "/usr/bin/google-chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

EDITOR_HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>{title}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin:0; font:14px/1.6 "Microsoft YaHei",sans-serif; background:#eef1f5; color:#111; }}
  header {{ position:sticky; top:0; z-index:9; display:flex; gap:12px; align-items:center;
            padding:10px 16px; background:#fff; box-shadow:0 1px 6px #0002; }}
  header b {{ font-size:15px; }}
  header span {{ color:#555; }}
  button {{ font:inherit; padding:6px 12px; border:1px solid #c9cfd8; border-radius:6px;
            background:#fff; cursor:pointer; }}
  button:hover {{ background:#f3f6fa; }}
  main {{ background:#fff; margin:20px auto; padding:12px; width:min(96vw,{w}px);
          box-shadow:0 6px 24px #0001; }}
  main svg {{ width:100%; height:auto; display:block; }}
  svg text {{ cursor:text; }}
  svg text:focus {{ outline:1px dashed #2563eb; }}
</style></head><body>
<header>
  <b>{name}</b>
  <span>点图里的文字即可直接改；改完点「下载 SVG」覆盖源文件，再重跑 svg_flow.py 出 PNG/PDF。</span>
  <button id="dl">下载 SVG</button>
</header>
<main id="stage">{svg}</main>
<script>
document.querySelectorAll('#stage svg text').forEach(function (t) {{
  t.setAttribute('contenteditable', 'true');
  t.addEventListener('blur', function () {{
    // 浏览器会把连续空格折成一个，导出前统一回收，避免字距被吃
    t.textContent = t.textContent.replace(/\\s+/g, ' ').trim();
  }});
}});
document.getElementById('dl').addEventListener('click', function () {{
  var svg = document.querySelector('#stage svg').cloneNode(true);
  svg.querySelectorAll('text').forEach(function (t) {{ t.removeAttribute('contenteditable'); }});
  var text = '<?xml version="1.0" encoding="UTF-8"?>\\n' + new XMLSerializer().serializeToString(svg);
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {{type: 'image/svg+xml'}}));
  a.download = {name_json};
  a.click();
  URL.revokeObjectURL(a.href);
}});
</script>
</body></html>
"""


def find_edge() -> str:
    for candidate in EDGE_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    found = shutil.which("msedge") or shutil.which("microsoft-edge") or shutil.which("google-chrome")
    if found:
        return found
    sys.exit("找不到 Edge/Chrome。设环境变量 MSEDGE 指向浏览器可执行文件，或改用 --html 手工截图。")


def parse_svg_size(svg_text: str) -> tuple[float, float]:
    match = re.search(
        r'viewBox\s*=\s*["\']\s*([\d.eE+-]+)[\s,]+([\d.eE+-]+)[\s,]+([\d.eE+-]+)[\s,]+([\d.eE+-]+)',
        svg_text,
    )
    if match:
        return float(match.group(3)), float(match.group(4))
    width = re.search(r'\bwidth\s*=\s*["\']([\d.]+)', svg_text)
    height = re.search(r'\bheight\s*=\s*["\']([\d.]+)', svg_text)
    if not width or not height:
        sys.exit("无法解析 SVG 尺寸：需要 width/height 或 viewBox（四元 viewBox 最稳）")
    return float(width.group(1)), float(height.group(1))


def strip_xml_head(svg_text: str) -> str:
    svg_text = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", svg_text, flags=re.I)
    svg_text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg_text, flags=re.I)
    svg_text = re.sub(r"^\s*<!--.*?-->\s*", "", svg_text, flags=re.S)
    return svg_text.strip()


def page_html(svg_text: str, width: float, height: float, scale: float = 1.0) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>@page{{size:{width * scale}px {height * scale}px;margin:0}}"
        "html,body{margin:0;padding:0;background:#fff}"
        f"svg{{width:{width * scale}px;height:{height * scale}px;display:block}}</style>"
        "</head><body>" + svg_text + "</body></html>"
    )


def shot(edge: str, html_path: Path, out_png: Path, width: int, height: int) -> None:
    with tempfile.TemporaryDirectory(prefix="svgflow_") as td:
        target = Path(td) / "shot.png"
        subprocess.run(
            [edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             f"--screenshot={target}", f"--window-size={width},{height}",
             "--default-background-color=FFFFFFFF", html_path.as_uri()],
            capture_output=True, timeout=180,
        )
        if not target.exists():
            sys.exit("Edge 截图失败：未产出 PNG（检查 Edge 是否支持 --headless=new）")
        shutil.copy2(target, out_png)


def main() -> int:
    ap = argparse.ArgumentParser(description="流程图 SVG -> HTML/PNG/PDF")
    ap.add_argument("svg", help="输入 .svg（flow_*.svg）")
    ap.add_argument("--html", action="store_true", help="输出可编辑 HTML")
    ap.add_argument("--png", action="store_true", help="输出 PNG")
    ap.add_argument("--pdf", action="store_true", help="输出 PDF")
    ap.add_argument("-s", "--scale", type=float, default=float(os.environ.get("FLOW_SCALE") or 2),
                    help="PNG 倍率（默认 2，≈192 dpi；论文用 3）")
    ap.add_argument("--outdir", help="产物目录（默认与 SVG 同目录）")
    args = ap.parse_args()

    svg_path = Path(args.svg).resolve()
    if not svg_path.is_file():
        sys.exit(f"找不到 {svg_path}")
    svg_text = strip_xml_head(svg_path.read_text(encoding="utf-8", errors="replace"))
    if "<svg" not in svg_text or "</svg>" not in svg_text:
        sys.exit("SVG 未正常闭合（缺 </svg>），先修图再渲染。")
    width, height = parse_svg_size(svg_text)

    outdir = Path(args.outdir).resolve() if args.outdir else svg_path.parent
    outdir.mkdir(parents=True, exist_ok=True)
    stem = svg_path.with_suffix("").name

    do_all = not (args.html or args.png or args.pdf)
    made: list[str] = []

    if args.html or do_all:
        html = EDITOR_HTML.format(title=svg_path.name, name=svg_path.name, w=int(width) + 40,
                                  svg=svg_text, name_json=repr(svg_path.name).replace("'", '"'))
        html_path = outdir / f"{stem}.html"
        html_path.write_text(html, encoding="utf-8")
        made.append(str(html_path))

    edge = None
    if args.png or args.pdf or do_all:
        edge = find_edge()

    if args.png or do_all:
        png_path = outdir / f"{stem}.png"
        try:  # 有 cairosvg 就直接转，最省事
            import cairosvg  # type: ignore

            cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=str(png_path),
                             scale=args.scale)
        except ImportError:
            with tempfile.TemporaryDirectory(prefix="svgflow_html_") as td:
                html_path = Path(td) / "page.html"
                html_path.write_text(page_html(svg_text, width, height, args.scale), encoding="utf-8")
                shot(edge, html_path, png_path, int(width * args.scale), int(height * args.scale))
        made.append(str(png_path))

    if args.pdf or do_all:
        pdf_path = outdir / f"{stem}.pdf"
        with tempfile.TemporaryDirectory(prefix="svgflow_pdf_") as td:
            html_path = Path(td) / "page.html"
            html_path.write_text(page_html(svg_text, width, height, 1.0), encoding="utf-8")
            subprocess.run(
                [edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                 f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                capture_output=True, timeout=180,
            )
        if not pdf_path.is_file():
            sys.exit("Edge 打印 PDF 失败（检查 --print-to-pdf 是否可用）")
        made.append(str(pdf_path))

    print(f"SVG 尺寸：{int(width)}x{int(height)}  产物目录：{outdir}")
    for item in made:
        print("  ->", item)
    print("下一步：把 PNG 打开目检（字不压线、箭头闭合、色数≤3），"
          "再把本图登记进 figures/manifest.json（route=flow）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
