#!/usr/bin/env python3
"""从 5 张实拍论文主图母版中选版式。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX = SKILL_ROOT / "assets" / "figures" / "reference" / "roadmap" / "index.json"

# 中文 Windows 控制台默认 GBK：遇到打印不出的字符只替换，不抛异常
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")


def load() -> list[dict]:
    if not INDEX.exists():
        return []
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    return data.get("references", [])


def main() -> int:
    parser = argparse.ArgumentParser(description="选择论文主图参考版式")
    parser.add_argument("--list", action="store_true", help="列出全部版式")
    parser.add_argument("--id", help="版式 id")
    parser.add_argument("--pattern", help="按 pattern 过滤")
    parser.add_argument("--copy-to", help="复制母版 jpg 到目标路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    refs = load()
    if args.pattern:
        refs = [r for r in refs if r.get("pattern") == args.pattern]

    if args.id:
        match = next((r for r in refs if r.get("id") == args.id), None)
        if match is None:
            print(f"未找到版式：{args.id}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(match, ensure_ascii=False, indent=2))
        else:
            print(f"{match['id']} | {match['title']} | {match['pattern']}")
            print(f"  结构：{match.get('skeleton', '')}")
            print(f"  适用：{match.get('use', '')}")
            print(f"  别用：{match.get('avoid', '')}")
        if args.copy_to:
            src = INDEX.parent / match["file"]
            dst = Path(args.copy_to)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"已复制到 {dst}")
        return 0

    if args.json:
        print(json.dumps(refs, ensure_ascii=False, indent=2))
        return 0

    print("| id | 版式 | 类型 | 适用 |")
    print("|---|---|---|---|")
    for ref in refs:
        print(f"| {ref['id']} | {ref['title']} | {ref['pattern']} | {ref.get('use', '')} |")
    print("\n骨架与视觉规范见 assets/figures/reference/roadmap/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
