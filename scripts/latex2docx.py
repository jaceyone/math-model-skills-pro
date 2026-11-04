#!/usr/bin/env python3
"""LaTeX -> Word 旁路导出：Pandoc + python-docx 后处理。

面向数学建模论文：展开 \\input、补全图片扩展名、PDF 图转 PNG、
替换模板宏、处理常见表格/引用，再交给 Pandoc 生成 docx。
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

try:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt
except Exception:  # pragma: no cover
    Document = None


SKILL_ROOT = Path(__file__).resolve().parent.parent

TEMPLATE_MACROS = {
    "tihao": "赛题",
    "baominghao": "报名号",
    "schoolname": "学校",
    "membera": "队员一",
    "memberb": "队员二",
    "memberc": "队员三",
    "supervisor": "指导教师",
    "yearinput": "年份",
    "monthinput": "月份",
    "dayinput": "日期",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def find_main(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    for candidate in (root / "paper/main.tex", root / "main.tex"):
        if candidate.exists():
            return candidate
    return None


def convert_pdf_to_png(pdf: Path, out_dir: Path) -> Path | None:
    if not shutil.which("pdftoppm"):
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (pdf.stem + ".png")
    if target.exists():
        return target
    proc = subprocess.run(
        ["pdftoppm", "-png", "-r", "300", "-singlefile", str(pdf), str(out_dir / pdf.stem)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return target if proc.returncode == 0 and target.exists() else None


def normalize_images(text: str, source: Path, paper_root: Path, temp_root: Path, warnings: list[str]) -> tuple[str, int, int]:
    converted = 0
    missing = 0

    def repl(match: re.Match) -> str:
        nonlocal converted, missing
        options = match.group(1) or ""
        raw = match.group(2).strip()
        search_dirs = [paper_root, source.parent, temp_root, temp_root / "figures", paper_root / "figures"]
        candidates = [d / raw for d in search_dirs]
        if Path(raw).suffix == "":
            candidates = [d / (raw + ext) for d in search_dirs for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps")]
        hit = next((p for p in candidates if p.exists()), None)
        if hit is None:
            missing += 1
            warnings.append(f"图片不存在：{raw}（{source}）")
            return match.group(0)
        if hit.suffix.lower() == ".pdf":
            png = convert_pdf_to_png(hit, temp_root / "converted_png")
            if png is not None:
                converted += 1
                hit = png
            else:
                missing += 1
                warnings.append(f"PDF 图无法转 PNG：{raw}")
                return match.group(0)
        # 统一相对 paper/ 的路径，Pandoc 在 paper/ 下运行
        try:
            rel = os.path.relpath(hit, paper_root)
        except ValueError:
            rel = str(hit)
        rel = rel.replace("\\", "/")
        return f"\\includegraphics{('[' + options + ']') if options else ''}{{{rel}}}"

    new = re.sub(r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}", repl, text)
    return new, converted, missing


def expand_inputs(main: Path, paper_root: Path, temp_root: Path, warnings: list[str]) -> tuple[str, int, int, int]:
    seen: set[Path] = set()
    images_converted = 0
    images_missing = 0
    inputs = 0

    def walk(path: Path) -> str:
        nonlocal images_converted, images_missing, inputs
        path = path.resolve()
        if path in seen or not path.exists():
            return ""
        seen.add(path)
        text = read_text(path)
        text, c, m = normalize_images(text, path, paper_root, temp_root, warnings)
        images_converted += c
        images_missing += m

        def repl(match: re.Match) -> str:
            nonlocal inputs
            name = match.group(1).strip()
            candidate = path.parent / name
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".tex")
            if not candidate.exists():
                warnings.append(f"\\input 文件不存在：{name}")
                return ""
            inputs += 1
            return "\n" + walk(candidate) + "\n"

        return re.sub(r"\\(?:input|include)\{([^}]+)\}", repl, text)

    return walk(main), images_converted, images_missing, inputs


def parse_labels(paper_root: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for aux in paper_root.glob("*.aux"):
        text = read_text(aux)
        for match in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", text):
            labels[match.group(1)] = match.group(2)
    return labels


def replace_template_macros(text: str) -> str:
    for macro, label in TEMPLATE_MACROS.items():
        text = re.sub(rf"\\{macro}\{{([^}}]*)\}}", rf"{label}：\1", text)
    text = re.sub(r"\\CumcmAIUsed\{([^}]*)\}", r"AI 使用声明：\1", text)
    text = text.replace("\\CumcmAINotUsed", "AI 使用声明：未使用 AI 工具。")
    text = re.sub(r"\\keywords\{([^}]*)\}", r"\\textbf{关键词：}\1", text)
    return text


def preprocess(combined: str, paper_root: Path, temp_root: Path, warnings: list[str]) -> tuple[str, int]:
    text = combined
    # 只保留 document 环境
    begin = text.find("\\begin{document}")
    if begin >= 0:
        text = text[begin + len("\\begin{document}"):]
    end = text.rfind("\\end{document}")
    if end >= 0:
        text = text[:end]

    # 标题：从 \title 提取，正文前加居中标题
    title = ""
    match = re.search(r"\\title\{((?:[^{}]|\{[^{}]*\})*)\}", text)
    if match:
        title = match.group(1).strip()
    text = re.sub(r"\\title\{((?:[^{}]|\{[^{}]*\})*)\}", "", text)
    text = re.sub(r"\\author\{[^}]*\}", "", text)
    text = re.sub(r"\\date\{[^}]*\}", "", text)
    text = text.replace("\\maketitle", "")

    # 模板环境
    text = text.replace("\\begin{cumcmabstract}", "\\section*{摘要}")
    text = text.replace("\\end{cumcmabstract}", "")
    text = text.replace("\\begin{abstract}", "\\section*{摘要}")
    text = text.replace("\\end{abstract}", "")
    text = text.replace("\\begin{appendices}", "\\appendix")
    text = text.replace("\\end{appendices}", "")
    text = re.sub(r"\\begin\{figure\}\[[^\]]*\]", r"\\begin{figure}", text)
    text = re.sub(r"\\begin\{table\}\[[^\]]*\]", r"\\begin{table}", text)

    # 定理/证明等自定义环境：去壳保内容
    for env in (
        "assumption", "axiom", "conjecture", "corollary", "definition", "example",
        "lemma", "principle", "problem", "proof", "solution", "theorem", "framee", "minipage",
    ):
        text = text.replace(f"\\begin{{{env}}}", "")
        text = text.replace(f"\\end{{{env}}}", "")

    # 代码环境 -> verbatim
    text = re.sub(r"\\begin\{tcode\}(?:\[[^\]]*\])?", r"\\begin{verbatim}", text)
    text = text.replace("\\end{tcode}", "\\end{verbatim}")
    text = re.sub(r"\\begin\{lstlisting\}(?:\[[^\]]*\])?", r"\\begin{verbatim}", text)
    text = text.replace("\\end{lstlisting}", "\\end{verbatim}")

    # 表格
    text = text.replace("\\begin{tabularx}", "\\begin{tabular}")
    text = text.replace("\\end{tabularx}", "\\end{tabular}")
    text = re.sub(r"\\begin\{tabular\}\{[^}]*\}\{[^}]*\}", lambda m: "\\begin{tabular}{" + re.sub(r"[XLYRC]", "l", m.group(0).split("}{")[-1][:-1]) + "}", text)
    text = text.replace("\\toprule", "\\hline").replace("\\midrule", "\\hline").replace("\\bottomrule", "\\hline")
    text = re.sub(r"\\multirow\{[^}]*\}\{[^}]*\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", r"\1", text)
    text = re.sub(r"\\multicolumn\{[^}]*\}\{[^}]*\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", r"\1", text)

    # 代码文件内联
    def lstinput(match: re.Match) -> str:
        raw = match.group(1).strip()
        candidate = paper_root / raw
        if not candidate.exists():
            warnings.append(f"\\lstinputlisting 文件不存在：{raw}")
            return ""
        code = read_text(candidate)
        return "\\begin{lstlisting}\n" + code + "\n\\end{lstlisting}"

    text = re.sub(r"\\lstinputlisting(?:\[[^\]]*\])?\{([^}]+)\}", lstinput, text)

    # 引用编号
    labels = parse_labels(paper_root)
    def ref(match: re.Match) -> str:
        key = match.group(1)
        if key in labels:
            return labels[key]
        warnings.append(f"未解析引用：{key}")
        return f"[{key}]"

    text = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(" + ref(m) + ")", text)
    text = re.sub(r"\\ref\{([^}]+)\}", ref, text)

    # 文献编号
    bib_order = {key: str(i + 1) for i, key in enumerate(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", text))}
    def cite(match: re.Match) -> str:
        keys = [k.strip() for k in match.group(1).split(",")]
        nums = [bib_order.get(k, k) for k in keys]
        return "[" + ",".join(nums) + "]"

    text = re.sub(r"\\cite[a-z]*\{([^}]+)\}", cite, text)

    # 清理命令
    for cmd in ("zihao", "vspace", "hspace", "setlength", "addcontentsline", "bibliographystyle"):
        text = re.sub(rf"\\{cmd}\{{[^}}]*\}}", "", text)
    for token in (
        "\\tableofcontents", "\\newpage", "\\clearpage", "\\pagestyle", "\\thispagestyle",
        "\\noindent", "\\centering", "\\small", "\\large", "\\Large", "\\LARGE",
        "\\heiti", "\\songti", "\\kaishu", "\\fangsong", "\\bfseries", "\\mdseries",
    ):
        text = text.replace(token, "")
    text = re.sub(r"\\begin\{center\}", "", text)
    text = re.sub(r"\\end\{center\}", "", text)

    text = replace_template_macros(text)
    if title:
        text = "\\begin{center}\\textbf{\\Large " + title + "}\\end{center}\n\n" + text
    return text, len(bib_order)


def run_pandoc(tex: Path, out: Path, reference_doc: Path | None, warnings: list[str]) -> bool:
    cmd = ["pandoc", str(tex.name), "-f", "latex", "-t", "docx", "--wrap=none", "-o", str(out.name)]
    if reference_doc and reference_doc.exists():
        cmd.extend(["--reference-doc", str(reference_doc)])
    proc = subprocess.run(
        cmd,
        cwd=str(tex.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        warnings.append("Pandoc 失败：" + (proc.stderr or proc.stdout or "")[-2000:])
        return False
    if proc.stderr.strip():
        for line in proc.stderr.strip().splitlines():
            warnings.append("Pandoc: " + line)
    return True


def postprocess(docx_path: Path, warnings: list[str]) -> None:
    if Document is None:
        warnings.append("python-docx 不可用，跳过样式后处理")
        return
    try:
        doc = Document(str(docx_path))
    except Exception as exc:
        warnings.append(f"python-docx 打开失败：{exc}")
        return

    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    def set_font(run, east="宋体", ascii_font="Times New Roman", size=12, bold=None):
        run.font.name = ascii_font
        run.font.size = Pt(size)
        if bold is not None:
            run.bold = bold
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        rfonts.set(qn("w:eastAsia"), east)
        rfonts.set(qn("w:ascii"), ascii_font)
        rfonts.set(qn("w:hAnsi"), ascii_font)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.first_line_indent = Pt(24)
    normal.paragraph_format.line_spacing = 1.5

    for style_name, size, bold in (("Heading 1", 16, True), ("Heading 2", 14, True), ("Heading 3", 12, True)):
        try:
            style = doc.styles[style_name]
            style.font.size = Pt(size)
            style.font.bold = bold
            style.font.name = "Times New Roman"
            style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "黑体" if size >= 14 else "宋体")
        except KeyError:
            pass

    for para in doc.paragraphs:
        style = (para.style.name or "").lower()
        for run in para.runs:
            if style.startswith("heading"):
                set_font(run, east="黑体", size=16 if "1" in style else 14, bold=True)
            else:
                set_font(run, east="宋体", size=12)
        if style.startswith("heading"):
            para.paragraph_format.first_line_indent = Pt(0)
            if "1" in style:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            para.paragraph_format.first_line_indent = Pt(24)

    for table in doc.tables:
        try:
            table.style = "Table Grid"
        except Exception:
            pass
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        set_font(run, size=10.5)

    for shape in doc.inline_shapes:
        try:
            max_width = Cm(15.5)
            if shape.width > max_width:
                ratio = max_width / shape.width
                shape.width = max_width
                shape.height = int(shape.height * ratio)
        except Exception:
            pass

    # 页脚页码
    for section in doc.sections:
        footer = section.footer
        para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        fld_char1 = OxmlElement("w:fldChar")
        fld_char1.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = "PAGE"
        fld_char2 = OxmlElement("w:fldChar")
        fld_char2.set(qn("w:fldCharType"), "end")
        run._r.append(fld_char1)
        run._r.append(instr)
        run._r.append(fld_char2)

    try:
        doc.save(str(docx_path))
    except Exception as exc:
        warnings.append(f"保存 docx 失败：{exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="LaTeX -> Word 旁路导出")
    parser.add_argument("--project", default=".", help="项目目录")
    parser.add_argument("--main", help="论文入口 .tex")
    parser.add_argument("--out", help="输出 .docx")
    parser.add_argument("--reference-doc", help="Pandoc 参考样式 docx")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    main_tex = find_main(root, args.main)
    if main_tex is None:
        print("未找到 paper/main.tex 或 main.tex", file=sys.stderr)
        return 1
    if not shutil.which("pandoc"):
        print("未找到 pandoc，请先安装", file=sys.stderr)
        return 1

    paper_dir = main_tex.parent
    figures_dir = root / "figures"
    out_path = Path(args.out) if args.out else (paper_dir / "论文.docx")
    if args.reference_doc:
        reference_doc = Path(args.reference_doc)
    else:
        local_ref = root / "assets/templates/docx/reference.docx"
        reference_doc = local_ref if local_ref.exists() else (
            SKILL_ROOT / "assets/templates/docx/reference.docx"
        )

    temp_root = Path(tempfile.mkdtemp(prefix="mmpro_docx_"))
    warnings: list[str] = []
    try:
        temp_paper = temp_root / "paper"
        shutil.copytree(
            paper_dir,
            temp_paper,
            ignore=shutil.ignore_patterns("*.log", "*.out", "*.toc", "*.pdf", "__pycache__"),
        )
        if figures_dir.exists():
            shutil.copytree(figures_dir, temp_root / "figures", ignore=shutil.ignore_patterns("__pycache__"))
        code_dir = root / "code"
        if code_dir.exists():
            shutil.copytree(
                code_dir,
                temp_root / "code",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "outputs"),
            )
        if reference_doc.exists():
            shutil.copy2(reference_doc, temp_root / "reference.docx")
            temp_ref = temp_root / "reference.docx"
        else:
            temp_ref = None
            warnings.append(f"参考样式不存在：{reference_doc}")

        main_rel = main_tex.relative_to(paper_dir)
        temp_main = temp_paper / main_rel
        combined, images_converted, images_missing, inputs = expand_inputs(
            temp_main, temp_paper, temp_root, warnings
        )
        preprocessed, bib_count = preprocess(combined, temp_paper, temp_root, warnings)
        pre_path = temp_paper / "main_docx.tex"
        write_text(pre_path, preprocessed)

        temp_out = temp_paper / "out.docx"
        if not run_pandoc(pre_path, temp_out, temp_ref, warnings):
            print("Pandoc 转换失败：", file=sys.stderr)
            for item in warnings[-10:]:
                print("  - " + item, file=sys.stderr)
            if args.keep_temp:
                print(f"临时目录：{temp_root}", file=sys.stderr)
            write_report(root, main_tex, out_path, inputs, images_converted, images_missing, bib_count, warnings)
            return 1
        postprocess(temp_out, warnings)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_out, out_path)
        write_report(root, main_tex, out_path, inputs, images_converted, images_missing, bib_count, warnings)
        print(f"已导出：{out_path}")
        print(f"报告：{root / 'reports/DOCX_EXPORT_REPORT.md'}")
        if args.keep_temp:
            print(f"临时目录：{temp_root}")
        return 0
    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


def write_report(root: Path, main_tex: Path, out_path: Path, inputs: int, images_converted: int, images_missing: int, bib_count: int, warnings: list[str]) -> None:
    report = [
        "# Word 导出报告",
        "",
        f"- 入口：`{main_tex}`",
        f"- 输出：`{out_path}`",
        f"- 展开 `\\input`：{inputs} 个",
        f"- PDF 图转 PNG：{images_converted} 张",
        f"- 缺失图片：{images_missing} 张",
        f"- 参考文献：{bib_count} 条",
        f"- 警告：{len(warnings)} 条",
        "",
        "## 说明",
        "",
        "- Word 是改稿副本，不是权威版本；最终以 PDF 为准。",
        "- 复杂 TikZ 图、multirow、合并单元格可能降级。",
        "",
        "## 警告",
        "",
    ]
    if warnings:
        for item in warnings:
            report.append(f"- {item}")
    else:
        report.append("- 无")
    report.append("")
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "DOCX_EXPORT_REPORT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
