#!/usr/bin/env python3
"""编译 LaTeX 论文为 PDF，并检查错误、未定义引用与页数。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_main(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    for candidate in (root / "paper/main.tex", root / "main.tex"):
        if candidate.exists():
            return candidate
    return None


def parse_log(log: Path) -> dict:
    text = read_text(log)
    errors = []
    for match in re.finditer(r"^! (.+)$", text, re.MULTILINE):
        errors.append(match.group(1).strip())
    undefined = re.findall(r"LaTeX Warning: Reference `([^']+)' on page", text)
    missing_files = re.findall(r"LaTeX Error: File `([^']+)' not found", text)
    overfull_hits = []
    for m in re.finditer(r"Overfull \\hbox \(([\d.]+)pt too wide\) in (\w+) at lines (\d+)--(\d+)", text):
        overfull_hits.append({"pt": float(m.group(1)), "kind": m.group(2),
                              "from": int(m.group(3)), "to": int(m.group(4))})
    overfull = len(re.findall(r"Overfull \\hbox", text))
    # alignment = 表格；G4 的列宽记账就是治这个（首尾加 @{} 或把总和降到 0.94）
    table_overfull = sum(1 for h in overfull_hits if h["kind"] == "alignment")
    underfull = len(re.findall(r"Underfull \\hbox", text))
    pages = None
    match = re.search(r"Output written on .+?\((\d+) pages?", text)
    if match:
        pages = int(match.group(1))
    return {
        "errors": errors,
        "undefined_refs": sorted(set(undefined)),
        "missing_files": sorted(set(missing_files)),
        "overfull": overfull,
        "overfull_detail": overfull_hits[:12],
        "table_overfull": table_overfull,
        "underfull": underfull,
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="编译 LaTeX 论文")
    parser.add_argument("--project", default=".", help="项目目录")
    parser.add_argument("--main", help="论文入口 .tex")
    parser.add_argument("--once", action="store_true", help="只编译一遍")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    main_tex = find_main(root, args.main)
    if main_tex is None:
        print("未找到 paper/main.tex 或 main.tex", file=sys.stderr)
        return 1

    paper_dir = main_tex.parent
    runs = 1 if args.once else 2
    results = []
    for i in range(runs):
        proc = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", main_tex.name],
            cwd=str(paper_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        results.append(proc.returncode)
        if proc.returncode != 0:
            break

    log_path = main_tex.with_suffix(".log")
    parsed = parse_log(log_path) if log_path.exists() else {
        "errors": ["未生成 .log"],
        "undefined_refs": [],
        "missing_files": [],
        "overfull": 0,
        "underfull": 0,
        "pages": None,
    }
    pdf_path = main_tex.with_suffix(".pdf")
    pdf_ok = pdf_path.exists() and pdf_path.stat().st_size > 1024
    pdf_pages = parsed.get("pages")
    pdf_size = None
    if pdf_ok and PdfReader is not None:
        try:
            reader = PdfReader(str(pdf_path))
            pdf_pages = len(reader.pages)
            box = reader.pages[0].mediabox
            pdf_size = (float(box.width), float(box.height))
        except Exception:
            pass

    status = "PASS"
    if not pdf_ok or any(code != 0 for code in results) or parsed["errors"] or parsed["missing_files"]:
        status = "FAIL"
    elif parsed["undefined_refs"] or parsed["overfull"]:
        # Underfull 只影响美观（行内空隙大），按 04-writing.md 的口径不判 WARN
        status = "WARN"

    data = {
        "status": status,
        "main": str(main_tex),
        "returns": results,
        "pdf": str(pdf_path) if pdf_ok else "",
        "pdf_pages": pdf_pages,
        "pdf_size_pt": pdf_size,
        **parsed,
    }

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"编译结果：{status}")
        print(f"入口：{main_tex}")
        print(f"PDF：{pdf_path}（{pdf_pages or '?'} 页）")
        if parsed["errors"]:
            print("错误：")
            for err in parsed["errors"][:10]:
                print(f"  - {err}")
        if parsed["undefined_refs"]:
            print(f"未定义引用：{len(parsed['undefined_refs'])} 个")
        if parsed["overfull"] or parsed["underfull"]:
            print(f"Overfull：{parsed['overfull']}（alignment 类 {parsed['table_overfull']}）；Underfull：{parsed['underfull']}")
            for hit in parsed["overfull_detail"][:5]:
                print(f"  - {hit['pt']}pt {hit['kind']} lines {hit['from']}--{hit['to']}")

    lines = [
        "# 编译报告",
        "",
        f"## 结论\n\n**{status}**",
        "",
        "## 输入输出",
        "",
        f"- 入口：`{main_tex}`",
        f"- PDF：`{pdf_path}`（{pdf_pages or '?'} 页）",
        f"- 编译次数：{len(results)}",
        "",
        "## 错误",
        "",
    ]
    if parsed["errors"]:
        for err in parsed["errors"]:
            lines.append(f"- {err}")
    else:
        lines.append("- 0 error")
    lines += ["", "## 警告", ""]
    if parsed["undefined_refs"]:
        lines.append(f"- 未定义引用：{', '.join(parsed['undefined_refs'])}")
    if parsed["missing_files"]:
        lines.append(f"- 缺失文件：{', '.join(parsed['missing_files'])}")
    if parsed["overfull"]:
        lines.append(f"- Overfull hbox：{parsed['overfull']}（alignment 类 {parsed['table_overfull']} 条）")
        for hit in parsed["overfull_detail"]:
            where = "表格列宽（alignment）" if hit["kind"] == "alignment" else "段落断行"
            lines.append(f"  - {hit['pt']}pt · {where} · lines {hit['from']}--{hit['to']}")
        if parsed["table_overfull"]:
            lines.append("  - 表格 Overfull 按【列宽记账】处理：首尾加 `@{}`，总和取 1.04 − 0.04×N；不加 `@{}` 时降到 0.94")
        if parsed["overfull"] > parsed["table_overfull"]:
            lines.append("  - 注意：`tabular` 里列宽溢出 LaTeX 常报 `in paragraph` 而不是 `in alignment`，按上面的行号回到源文件定位")
    if parsed["underfull"]:
        lines.append(f"- Underfull hbox：{parsed['underfull']}")
    if not any((parsed["undefined_refs"], parsed["missing_files"], parsed["overfull"], parsed["underfull"])):
        lines.append("- 无")
    lines.append("")
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "BUILD_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    return 0 if status == "PASS" else (1 if status == "FAIL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
