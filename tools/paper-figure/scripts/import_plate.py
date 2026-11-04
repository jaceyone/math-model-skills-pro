#!/usr/bin/env python3
"""把一张新母版图装进 assets/figures/reference/roadmap/。

只存一份 jpg（去白边、宽度上限 1439 px），不生成 PNG/PDF 派生件 —— 母版仅作版式参考，
进论文的是按结构重画的 SVG。条目写进 index.json，骨架描述请同步补进 roadmap/README.md。

    python tools/paper-figure/scripts/import_plate.py --src refs/new.jpg \
        --id three-band --title "三段并排" --pattern framework \
        --description "左中右三段各带小标题，段内竖排节点" \
        --use "三问并列、逐问给方法" --avoid "任务不足三段"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ROADMAP = SKILL_ROOT / "assets" / "figures" / "reference" / "roadmap"
INDEX = ROADMAP / "index.json"
MAX_WIDTH = 1439
QUALITY = 88

# 中文 Windows 控制台默认 GBK：遇到打印不出的字符只替换，不抛异常
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")


def trim(im: Image.Image, tol: int = 246, pad: int = 12) -> Image.Image:
    """按近白背景裁掉四周空白。"""
    gray = im.convert("L").point(lambda v: 255 if v < tol else 0)
    box = gray.getbbox()
    if not box:
        return im
    left, top, right, bottom = box
    return im.crop(
        (
            max(0, left - pad),
            max(0, top - pad),
            min(im.width, right + pad),
            min(im.height, bottom + pad),
        )
    )


def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text(encoding="utf-8"))
    return {"references": []}


def seq_of(ref: dict) -> int:
    head = str(ref.get("file", "")).split("/")[-1].split("-")[0]
    return int(head) if head.isdigit() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="把新母版装进 roadmap/")
    parser.add_argument("--src", required=True, help="源图片（jpg/png/webp）")
    parser.add_argument("--id", required=True, help="版式 id，如 three-band")
    parser.add_argument("--title", required=True, help="中文版式名")
    parser.add_argument("--pattern", default="framework", choices=["pipeline", "framework", "taxonomy", "conceptual"])
    parser.add_argument("--description", default="", help="结构描述")
    parser.add_argument("--use", default="", help="适用场景")
    parser.add_argument("--avoid", default="", help="什么时候别用它")
    parser.add_argument("--skeleton", default="", help="一句话骨架，如 A → B → C")
    parser.add_argument("--seq", type=int, help="序号；默认取现有最大值 +1")
    args = parser.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.is_file():
        print(f"找不到源图：{src}")
        return 1

    data = load_index()
    refs = data.setdefault("references", [])
    seq = args.seq or (max([seq_of(r) for r in refs] or [0]) + 1)
    stem = f"{seq:02d}-{args.id}"

    (ROADMAP / "src").mkdir(parents=True, exist_ok=True)
    dst = ROADMAP / "src" / f"{stem}.jpg"

    im = trim(Image.open(src).convert("RGB"))
    if im.width > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)

    entry = {
        "id": args.id,
        "title": args.title,
        "pattern": args.pattern,
        "file": f"src/{stem}.jpg",
        "skeleton": args.skeleton,
        "description": args.description,
        "use": args.use,
        "avoid": args.avoid,
    }
    refs = [r for r in refs if r.get("id") != args.id] + [entry]
    refs.sort(key=lambda r: r.get("file", ""))
    data["references"] = refs
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已入库 {stem}：{im.width}x{im.height} → roadmap/src/{stem}.jpg（{dst.stat().st_size // 1024} KB）")
    print("记得把「一句话结构 / 布局 / 要点」补进 roadmap/README.md 第二节。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
