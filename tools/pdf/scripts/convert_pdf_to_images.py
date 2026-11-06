"""PDF → PNG 逐页图。

三条后端按可用性自动选,谁在就用谁(顺序执行,不并行):

1. **pdftoppm**(poppler,最稳、无 Python 依赖)
2. **pdf2image**(包装 pdftoppm,得有 poppler 才真能用)
3. **PyMuPDF / fitz**(纯 pip 安装,Windows 上没有 poppler 也能跑)

2026-11 实测:开发机上只装了 PyMuPDF(LaTeX 工作流本来就依赖它),
`pdf2image` 没装,旧版 `from pdf2image import convert_from_path` 在 import 阶段
就抛 `ModuleNotFoundError`,连 `--help` 都打不开。现在改成惰性导入 + 三级兜底。
"""
import os
import shutil
import subprocess
import sys

PDF2IMAGE_HINT = ("pip install pdf2image 并安装 poppler 后重试；"
                  "或改用已装好的 PyMuPDF：pip install pymupdf")


def _fit(img_w, img_h, max_dim):
    """等比缩到最长边 ≤ max_dim。"""
    if img_w <= max_dim and img_h <= max_dim:
        return img_w, img_h
    scale = min(max_dim / img_w, max_dim / img_h)
    return max(1, int(img_w * scale)), max(1, int(img_h * scale))


def _convert_pdftoppm(pdf_path, output_dir, max_dim, dpi=200):
    exe = shutil.which("pdftoppm")
    if not exe:
        return 0
    prefix = os.path.join(output_dir, "page")
    cmd = [exe, "-r", str(dpi), "-png", pdf_path, prefix]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return 0
    if r.returncode != 0:
        print(f"pdftoppm 失败：{(r.stderr or '').strip()[:300]}")
        return 0
    made = sorted(f for f in os.listdir(output_dir)
                  if f.startswith("page") and f.endswith(".png"))
    if not made:
        return 0
    # pdftoppm 出的是 page-1.png / page-01.png,统一成 page_1.png,并顺手压尺寸
    from PIL import Image
    out = 0
    for i, name in enumerate(made, 1):
        src = os.path.join(output_dir, name)
        with Image.open(src) as im:
            w, h = _fit(im.width, im.height, max_dim)
            if (w, h) != (im.width, im.height):
                im = im.resize((w, h))
            dst = os.path.join(output_dir, f"page_{i}.png")
            im.save(dst)
        if os.path.normcase(src) != os.path.normcase(dst):
            os.remove(src)
        print(f"Saved page {i} as {dst} (size: {w}x{h})")
        out += 1
    return out


def _convert_pdf2image(pdf_path, output_dir, max_dim, dpi=200):
    try:
        from pdf2image import convert_from_path
    except Exception:  # noqa: BLE001  —— 没装或 poppler 不在 PATH
        return 0
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:  # noqa: BLE001
        print(f"pdf2image 失败：{str(e).strip()[:300]}")
        return 0
    for i, image in enumerate(images, 1):
        w, h = _fit(image.width, image.height, max_dim)
        if (w, h) != image.size:
            image = image.resize((w, h))
        path = os.path.join(output_dir, f"page_{i}.png")
        image.save(path)
        print(f"Saved page {i} as {path} (size: {w}x{h})")
    return len(images)


def _convert_fitz(pdf_path, output_dir, max_dim, dpi=200):
    try:
        import fitz  # PyMuPDF
    except Exception:  # noqa: BLE001
        return 0
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:  # noqa: BLE001
        print(f"PyMuPDF 打不开 {pdf_path}：{str(e).strip()[:300]}")
        return 0
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    n = 0
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        path = os.path.join(output_dir, f"page_{i}.png")
        pix.save(path)
        # 只缩不放大:先按 max_dim 压,再覆盖
        try:
            from PIL import Image
            with Image.open(path) as im:
                w, h = _fit(im.width, im.height, max_dim)
                if (w, h) != (im.width, im.height):
                    im.resize((w, h)).save(path)
                print(f"Saved page {i} as {path} (size: {w}x{h})")
        except Exception:  # noqa: BLE001  —— PIL 不在就直接用原尺寸
            print(f"Saved page {i} as {path} (size: {pix.width}x{pix.height})")
        n += 1
    doc.close()
    return n


def convert(pdf_path, output_dir, max_dim=1000, dpi=200):
    if not os.path.isfile(pdf_path):
        raise SystemExit(f"找不到 PDF：{pdf_path}")
    os.makedirs(output_dir, exist_ok=True)
    for fn, name in ((_convert_pdftoppm, "pdftoppm"),
                     (_convert_pdf2image, "pdf2image"),
                     (_convert_fitz, "PyMuPDF")):
        n = fn(pdf_path, output_dir, max_dim, dpi)
        if n:
            print(f"Converted {n} pages to PNG images（后端：{name}）")
            return n
    raise SystemExit("三条后端都没跑通：没找到 pdftoppm、没装 pdf2image、也没装 PyMuPDF。\n"
                     + PDF2IMAGE_HINT)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="PDF → PNG 逐页图，三条后端自动兜底（pdftoppm → pdf2image → PyMuPDF）",
        epilog="示例：python convert_pdf_to_images.py 题面.pdf out/ 1000",
    )
    ap.add_argument("pdf", nargs="?", help="输入 PDF 路径")
    ap.add_argument("outdir", nargs="?", help="输出目录（不存在会自动创建）")
    ap.add_argument("max_dim", nargs="?", type=int, default=1000,
                    help="单页最长边像素上限，默认 1000（只缩不放大）")
    ap.add_argument("--dpi", type=int, default=200, help="渲染 DPI，默认 200")
    args = ap.parse_args()
    if not args.pdf or not args.outdir:
        ap.print_help()
        print("\n缺少参数：需要 [input pdf] [output directory]", file=sys.stderr)
        sys.exit(1)
    convert(args.pdf, args.outdir, args.max_dim, args.dpi)
