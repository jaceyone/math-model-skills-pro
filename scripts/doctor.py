#!/usr/bin/env python3
"""环境检查：LaTeX / Pandoc / Python 包 / 字体 / 模板。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent

COMMANDS = [
    ("xelatex", "LaTeX 编译", True),
    ("pandoc", "LaTeX -> Word（旁路，可选）", False),
    ("pdftoppm", "PDF -> PNG 预览（可选）", False),
    ("pdftotext", "PDF 文本提取", False),
    ("pdfinfo", "PDF 页数/尺寸", False),
    ("drawio", "drawio 导出（可选）", False),
]

PACKAGES = [
    ("numpy", "数值计算", True),
    ("pandas", "数据处理", True),
    ("matplotlib", "数据图", True),
    ("scipy", "科学计算", False),
    ("sklearn", "机器学习", False),
    ("openpyxl", "Excel 读写", False),
    ("docx", "Word 后处理", True),
    ("pypdf", "PDF 检查", False),
    ("fitz", "PDF 渲染/文本", False),
    ("PIL", "图片处理", False),
]

FONTS = {
    "Windows": [
        (Path(r"C:\Windows\Fonts\simsun.ttc"), "宋体 SimSun"),
        (Path(r"C:\Windows\Fonts\simhei.ttf"), "黑体 SimHei"),
        (Path(r"C:\Windows\Fonts\simkai.ttf"), "楷体 KaiTi"),
        (Path(r"C:\Windows\Fonts\times.ttf"), "Times New Roman"),
        (Path(r"C:\Windows\Fonts\arial.ttf"), "Arial"),
    ],
    "Darwin": [
        (Path("/System/Library/Fonts/STHeiti Light.ttc"), "黑体"),
        (Path("/System/Library/Fonts/Supplemental/Songti.ttc"), "宋体"),
        (Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"), "Times New Roman"),
    ],
}

TEMPLATES = [
    (SKILL_ROOT / "assets/templates/latex/default/main.tex", "默认论文模板（default）"),
    (SKILL_ROOT / "assets/templates/latex/mcm/main.tex", "MCM"),
    (SKILL_ROOT / "assets/templates/latex/huaweibei/main.tex", "华为杯"),
]

# 默认模板/工具箱资产：缺了会导致 S2 出图闸门或 S4 Word 分支直接跑不动
ASSETS = [
    (SKILL_ROOT / "assets/style/plot_style.py", "plot_style 数据图版式"),
    (SKILL_ROOT / "assets/style/check_figures.py", "check_figures 出图闸门"),
    (SKILL_ROOT / "assets/scaffold/run_all.py", "run_all 批量运行"),
    (SKILL_ROOT / "assets/templates/docx/report_kit.py", "report_kit Word 排版"),
    (SKILL_ROOT / "assets/templates/docx/reference.docx", "Word 报告模板"),
    (SKILL_ROOT / "references/knowledge/10-chapter-writing-prompts.md", "章节写作提示词"),
]


def check_command(name: str) -> str | None:
    return shutil.which(name)


def check_package(name: str) -> str | None:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return None
    return spec.origin if spec else None


def font_rows() -> list[dict]:
    system = platform.system()
    rows = []
    for path, label in FONTS.get(system, []):
        rows.append({"name": label, "path": str(path), "ok": path.exists()})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="数学建模 Pro 环境检查")
    parser.add_argument("--project", help="项目目录；给出时写入 reports/ENV_REPORT.md")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    commands = []
    for name, purpose, required in COMMANDS:
        path = check_command(name)
        commands.append({
            "name": name,
            "purpose": purpose,
            "required": required,
            "ok": bool(path),
            "path": path or "",
        })

    packages = []
    for name, purpose, required in PACKAGES:
        path = check_package(name)
        packages.append({
            "name": name,
            "purpose": purpose,
            "required": required,
            "ok": bool(path),
            "path": path or "",
        })

    templates = []
    for path, label in TEMPLATES:
        templates.append({"name": label, "path": str(path), "ok": path.exists()})

    assets = []
    for path, label in ASSETS:
        assets.append({"name": label, "path": str(path), "ok": path.exists()})

    fonts = font_rows()

    required_ok = all(x["ok"] for x in commands if x["required"])
    required_ok = required_ok and all(x["ok"] for x in packages if x["required"])
    required_ok = required_ok and any(x["ok"] for x in templates)
    required_ok = required_ok and all(x["ok"] for x in assets)

    data = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "skill_root": str(SKILL_ROOT),
        "required_ok": required_ok,
        "commands": commands,
        "packages": packages,
        "fonts": fonts,
        "templates": templates,
        "assets": assets,
    }

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        lines = [
            "# 环境检查报告",
            "",
            f"- 平台：{data['platform']}",
            f"- Python：{data['python']}",
            f"- 必选项：{'通过' if required_ok else '缺失'}",
            "",
            "## 命令",
            "",
            "| 命令 | 用途 | 必需 | 状态 | 路径 |",
            "|---|---|---|---|---|",
        ]
        for x in commands:
            lines.append(
                f"| `{x['name']}` | {x['purpose']} | {'是' if x['required'] else '否'} | "
                f"{'OK' if x['ok'] else 'MISS'} | {x['path'] or '-'} |"
            )
        lines += [
            "",
            "## Python 包",
            "",
            "| 包 | 用途 | 必需 | 状态 |",
            "|---|---|---|---|",
        ]
        for x in packages:
            lines.append(
                f"| `{x['name']}` | {x['purpose']} | {'是' if x['required'] else '否'} | "
                f"{'OK' if x['ok'] else 'MISS'} |"
            )
        lines += [
            "",
            "## 字体",
            "",
            "| 字体 | 状态 | 路径 |",
            "|---|---|---|",
        ]
        for x in fonts:
            lines.append(f"| {x['name']} | {'OK' if x['ok'] else 'MISS'} | {x['path']} |")
        lines += [
            "",
            "## 模板",
            "",
            "| 模板 | 状态 | 路径 |",
            "|---|---|---|",
        ]
        for x in templates:
            lines.append(f"| {x['name']} | {'OK' if x['ok'] else 'MISS'} | {x['path']} |")
        lines += [
            "",
            "## 默认资产",
            "",
            "| 资产 | 状态 | 路径 |",
            "|---|---|---|",
        ]
        for x in assets:
            lines.append(f"| {x['name']} | {'OK' if x['ok'] else 'MISS'} | {x['path']} |")
        lines += [
            "",
            "## 缺失时的安装建议（Windows）",
            "",
            "- xelatex：`winget install MiKTeX.MiKTeX`",
            "- pandoc：`winget install JohnMacFarlane.Pandoc`",
            "- poppler（pdftoppm/pdftotext）：`winget install oschwartz10612.poppler`",
            "- 字体：安装宋体/黑体/楷体/Times New Roman，或在模板中改用已安装字体",
            "",
        ]
        report = "\n".join(lines)
        print(report)
        if args.project:
            project = Path(args.project)
            reports = project / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            (reports / "ENV_REPORT.md").write_text(report, encoding="utf-8")
            print(f"\n已写入 {reports / 'ENV_REPORT.md'}")

    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
