# -*- coding: utf-8 -*-
"""Word 报告排版工具箱（python-docx）：样式、图表、公式、页眉页脚、目录域。"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
TAB = ROOT / "results" / "tables"
TEXT_W = 16.0  # cm

CN_BODY = "宋体"
CN_HEAD = "黑体"
EN_BODY = "Times New Roman"


def _set_run_font(run, cn=CN_BODY, en=EN_BODY, size=None, bold=None, color=None, italic=None):
    run.font.name = en
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), en)
    rFonts.set(qn("w:hAnsi"), en)
    rFonts.set(qn("w:eastAsia"), cn)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _shade(cell_or_par, hex_color: str):
    el = cell_or_par._tc if hasattr(cell_or_par, "_tc") else cell_or_par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    if hasattr(cell_or_par, "_tc"):
        cell_or_par._tc.get_or_add_tcPr().append(shd)
    else:
        el.append(shd)


def _borders(par_or_cell, edges: dict):
    """edges: {'top': (sz, color), ...} sz 单位为 1/8 磅。"""
    if hasattr(par_or_cell, "_tc"):
        pr = par_or_cell._tc.get_or_add_tcPr()
        tag = "w:tcBorders"
    else:
        pr = par_or_cell._p.get_or_add_pPr()
        tag = "w:pBdr"
    borders = pr.find(qn(tag))
    if borders is None:
        borders = OxmlElement(tag)
        pr.append(borders)
    for edge, (sz, color) in edges.items():
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)


class Report:
    def __init__(self, template: Path):
        self.doc = Document(str(template))
        self.fig_no = 0
        self.tab_no = 0
        self.eq_no = 0
        self._setup_page()
        self._setup_styles()

    # ---------------------------------------------------------------- 基础样式
    def _setup_page(self):
        s = self.doc.sections[0]
        s.page_width = Cm(21.0)
        s.page_height = Cm(29.7)
        s.left_margin = Cm(2.5)
        s.right_margin = Cm(2.5)
        s.top_margin = Cm(2.5)
        s.bottom_margin = Cm(2.5)
        s.header_distance = Cm(1.4)
        s.footer_distance = Cm(1.4)

    def _setup_styles(self):
        st = self.doc.styles["Normal"]
        st.font.name = EN_BODY
        st.font.size = Pt(12)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), CN_BODY)
        pf = st.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.first_line_indent = Pt(24)

        for name, size, before, after in (("Heading 1", 16, 18, 10), ("Heading 2", 14, 12, 6), ("Heading 3", 12, 8, 4)):
            s = self.doc.styles[name]
            s.font.name = EN_BODY
            s.font.size = Pt(size)
            s.font.bold = True
            s.font.color.rgb = RGBColor(0, 0, 0)
            s.element.rPr.rFonts.set(qn("w:eastAsia"), CN_HEAD)
            s.paragraph_format.space_before = Pt(before)
            s.paragraph_format.space_after = Pt(after)
            s.paragraph_format.first_line_indent = Pt(0)
            s.paragraph_format.line_spacing = 1.3
            s.paragraph_format.keep_with_next = True

        cap = self.doc.styles["Caption"]
        cap.font.name = EN_BODY
        cap.font.size = Pt(10.5)
        cap.font.bold = False
        cap.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        cap.element.rPr.rFonts.set(qn("w:eastAsia"), CN_BODY)
        cap.paragraph_format.first_line_indent = Pt(0)
        cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(3)
        cap.paragraph_format.space_after = Pt(8)
        cap.paragraph_format.line_spacing = 1.15

    # ---------------------------------------------------------------- 页眉页脚
    def header_footer(self, header_text: str):
        sec = self.doc.sections[0]
        sec.different_first_page_header_footer = True
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = hp.add_run(header_text)
        _set_run_font(run, size=9, color=RGBColor(0x59, 0x59, 0x59))
        _borders(hp, {"bottom": (6, "BFBFBF")})

        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = fp.add_run("第 ")
        _set_run_font(r1, size=9, color=RGBColor(0x59, 0x59, 0x59))
        self._add_field(fp, "PAGE")
        r2 = fp.add_run(" 页")
        _set_run_font(r2, size=9, color=RGBColor(0x59, 0x59, 0x59))

    @staticmethod
    def _add_field(par, instr: str, placeholder: str = "1"):
        run = par.add_run()
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        instr_el = OxmlElement("w:instrText")
        instr_el.set(qn("xml:space"), "preserve")
        instr_el.text = f" {instr} "
        fld_sep = OxmlElement("w:fldChar")
        fld_sep.set(qn("w:fldCharType"), "separate")
        t = OxmlElement("w:t")
        t.text = placeholder
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        for el in (fld_begin, instr_el, fld_sep, t, fld_end):
            run._r.append(el)
        _set_run_font(run, size=9, color=RGBColor(0x59, 0x59, 0x59))

    # ---------------------------------------------------------------- 段落
    def p(self, text: str = "", indent: bool = True, size: float = 12, bold: bool = False,
          align="justify", space_after: float = 0, color=None, cn=CN_BODY, en=EN_BODY,
          line_spacing: float = 1.5, italic: bool = False):
        par = self.doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(size * 2) if indent else Pt(0)
        par.paragraph_format.line_spacing = line_spacing
        par.paragraph_format.space_after = Pt(space_after)
        par.paragraph_format.space_before = Pt(0)
        par.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                         "left": WD_ALIGN_PARAGRAPH.LEFT,
                         "center": WD_ALIGN_PARAGRAPH.CENTER,
                         "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
        if text:
            run = par.add_run(text)
            _set_run_font(run, cn=cn, en=en, size=size, bold=bold, color=color, italic=italic)
        return par

    def rich(self, parts, indent=True, size=12, align="justify", line_spacing=1.5, space_after=0):
        """parts: [(text, {'bold':True,...}), ...] 便于句内加粗。"""
        par = self.doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(size * 2) if indent else Pt(0)
        par.paragraph_format.line_spacing = line_spacing
        par.paragraph_format.space_after = Pt(space_after)
        par.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                         "left": WD_ALIGN_PARAGRAPH.LEFT,
                         "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
        for text, kw in parts:
            run = par.add_run(text)
            _set_run_font(run, size=kw.get("size", size), bold=kw.get("bold", False),
                          color=kw.get("color"), italic=kw.get("italic", False),
                          cn=kw.get("cn", CN_BODY), en=kw.get("en", EN_BODY))
        return par

    def h1(self, text: str, page_break: bool = False):
        par = self.doc.add_heading(text, level=1)
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if page_break:
            par.paragraph_format.page_break_before = True
        return par

    def h2(self, text: str):
        par = self.doc.add_heading(text, level=2)
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        return par

    def h3(self, text: str):
        par = self.doc.add_heading(text, level=3)
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        return par

    def bullet(self, text: str, bold_head: str = ""):
        par = self.doc.add_paragraph()
        par.paragraph_format.left_indent = Pt(24)
        par.paragraph_format.first_line_indent = Pt(0)
        par.paragraph_format.line_spacing = 1.5
        par.paragraph_format.space_after = Pt(0)
        if not bold_head[:1] in "①②③④⑤⑥⑦⑧⑨":
            run = par.add_run("▪ ")
            _set_run_font(run, size=12, color=RGBColor(0x2F, 0x55, 0x97))
        if bold_head:
            r = par.add_run(bold_head)
            _set_run_font(r, size=12, bold=True)
        r = par.add_run(text)
        _set_run_font(r, size=12)
        return par

    def callout(self, title: str, lines: list[str]):
        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Cm(TEXT_W)
        _shade(cell, "EAF1FB")
        _borders(cell, {"left": (18, "2F5597"), "top": (4, "B4C7E7"),
                        "bottom": (4, "B4C7E7"), "right": (4, "B4C7E7")})
        par = cell.paragraphs[0]
        par.paragraph_format.space_before = Pt(4)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.first_line_indent = Pt(0)
        r = par.add_run(title)
        _set_run_font(r, size=10.5, bold=True, color=RGBColor(0x1F, 0x3B, 0x73))
        for line in lines:
            p2 = cell.add_paragraph()
            p2.paragraph_format.space_before = Pt(0)
            p2.paragraph_format.space_after = Pt(2)
            p2.paragraph_format.first_line_indent = Pt(0)
            p2.paragraph_format.line_spacing = 1.25
            r = p2.add_run(line)
            _set_run_font(r, size=10, color=RGBColor(0x33, 0x33, 0x33))
        self.p("", indent=False, space_after=4)

    def eq(self, text: str, font_size: float = 11.5):
        self.eq_no += 1
        par = self.doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(0)
        par.paragraph_format.line_spacing = 1.5
        par.paragraph_format.space_before = Pt(3)
        par.paragraph_format.space_after = Pt(3)
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # 制表符布局：左空 + 居中公式 + 右编号
        tabs = par.paragraph_format.tab_stops
        tabs.add_tab_stop(Cm(TEXT_W / 2), 1)   # center
        tabs.add_tab_stop(Cm(TEXT_W - 0.2), 2)  # right
        run = par.add_run("\t")
        r = par.add_run(text)
        _set_run_font(r, size=font_size, italic=True, cn="宋体", en="Cambria Math")
        r2 = par.add_run(f"\t({self.eq_no})")
        _set_run_font(r2, size=11)
        return self.eq_no

    def page_break(self):
        self.doc.add_page_break()

    def blank(self, n: int = 1, size: float = 12):
        for _ in range(n):
            self.p("", indent=False, size=size)

    # ---------------------------------------------------------------- 图
    def fig(self, name: str, caption: str, width: float = 15.0):
        path = FIG / f"{name}.png" if not str(name).endswith(".png") else Path(name)
        self.fig_no += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.first_line_indent = Pt(0)
        par.paragraph_format.space_before = Pt(6)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(path), width=Cm(width))
        cap = self.doc.add_paragraph(style="Caption")
        r = cap.add_run(f"图 {self.fig_no}  ")
        _set_run_font(r, size=10.5, bold=True, cn=CN_HEAD)
        r2 = cap.add_run(caption)
        _set_run_font(r2, size=10.5, bold=False)
        return self.fig_no

    def fig_ref(self, no: int) -> str:
        return f"图 {no}"

    # ---------------------------------------------------------------- 表
    def table(self, header: list[str], rows: list[list], caption: str,
              widths: list[float] | None = None, font_size: float = 8.5,
              header_fill: str = "E8EEF7", align_first_left: bool = True,
              note: str = ""):
        self.tab_no += 1
        cap = self.doc.add_paragraph(style="Caption")
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_before = Pt(8)
        cap.paragraph_format.space_after = Pt(3)
        r = cap.add_run(f"表 {self.tab_no}  ")
        _set_run_font(r, size=10.5, bold=True, cn=CN_HEAD)
        r2 = cap.add_run(caption)
        _set_run_font(r2, size=10.5)

        n_col = len(header)
        tbl = self.doc.add_table(rows=1 + len(rows), cols=n_col)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        widths = widths or [TEXT_W / n_col] * n_col
        tblPr = tbl._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge, sz in (("top", 12), ("bottom", 12), ("left", 0), ("right", 0), ("insideH", 0), ("insideV", 0)):
            el = OxmlElement(f"w:{edge}")
            if sz == 0:
                el.set(qn("w:val"), "none")
                el.set(qn("w:sz"), "0")
            else:
                el.set(qn("w:val"), "single")
                el.set(qn("w:sz"), str(sz))
                el.set(qn("w:color"), "404040")
            el.set(qn("w:space"), "0")
            borders.append(el)
        tblPr.append(borders)

        # 表头
        for j, text in enumerate(header):
            cell = tbl.rows[0].cells[j]
            cell.width = Cm(widths[j])
            _shade(cell, header_fill)
            _borders(cell, {"bottom": (8, "404040")})
            par = cell.paragraphs[0]
            par.paragraph_format.first_line_indent = Pt(0)
            par.paragraph_format.space_before = Pt(2)
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.line_spacing = 1.0
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = par.add_run(str(text))
            _set_run_font(r, size=font_size, bold=True, cn=CN_HEAD)
        trPr = tbl.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader")
        th.set(qn("w:val"), "true")
        trPr.append(th)

        for i, row in enumerate(rows, start=1):
            for j, val in enumerate(row):
                cell = tbl.rows[i].cells[j]
                cell.width = Cm(widths[j])
                par = cell.paragraphs[0]
                par.paragraph_format.first_line_indent = Pt(0)
                par.paragraph_format.space_before = Pt(1.5)
                par.paragraph_format.space_after = Pt(1.5)
                par.paragraph_format.line_spacing = 1.0
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and align_first_left) else WD_ALIGN_PARAGRAPH.CENTER
                text = "" if (val is None or (isinstance(val, float) and pd.isna(val)) or str(val) == "nan") else str(val)
                r = par.add_run(text)
                _set_run_font(r, size=font_size, en=EN_BODY)
        if note:
            pnote = self.doc.add_paragraph()
            pnote.paragraph_format.first_line_indent = Pt(0)
            pnote.paragraph_format.space_before = Pt(2)
            pnote.paragraph_format.space_after = Pt(8)
            r = pnote.add_run(note)
            _set_run_font(r, size=8.5, color=RGBColor(0x59, 0x59, 0x59))
        else:
            self.p("", indent=False, space_after=2, size=6)

        # 小表（≤8 行）避免跨页断行；大表允许跨页并重复表头
        if len(rows) <= 8:
            for row in tbl.rows[:-1]:
                trPr = row._tr.get_or_add_trPr()
                cant = OxmlElement("w:cantSplit")
                trPr.append(cant)
                for cell in row.cells:
                    for par in cell.paragraphs:
                        par.paragraph_format.keep_with_next = True
        return self.tab_no

    def csv_table(self, name: str, caption: str, cols: list[str] | None = None,
                  widths: list[float] | None = None, nd: int = 3, font_size: float = 8.5,
                  max_rows: int | None = None, note: str = "", index_col: bool = False):
        df = pd.read_csv(TAB / f"{name}.csv", encoding="utf-8-sig")
        if not index_col and df.columns[0].startswith("Unnamed"):
            df = df.iloc[:, 1:]
        if cols:
            df = df[cols]
        if max_rows:
            df = df.head(max_rows)

        def fmt(v):
            if isinstance(v, float):
                return f"{v:.{nd}f}"
            return v

        header = list(df.columns)
        rows = [[fmt(v) for v in rec] for rec in df.itertuples(index=False)]
        return self.table(header, rows, caption, widths=widths, font_size=font_size, note=note)

    # ---------------------------------------------------------------- 封面/目录
    def cover(self, org: str, title: str, subtitle: str, meta: list[tuple[str, str]]):
        self.blank(2)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(org)
        _set_run_font(r, size=18, bold=True, cn=CN_HEAD)

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        r = p.add_run("数 据 分 析 报 告")
        _set_run_font(r, size=15, color=RGBColor(0x2F, 0x55, 0x97), cn=CN_HEAD)

        self.blank(3)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run(title)
        _set_run_font(r, size=26, bold=True, cn=CN_HEAD)

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        r = p.add_run(subtitle)
        _set_run_font(r, size=13, color=RGBColor(0x40, 0x40, 0x40))

        self.blank(6)
        for k, v in meta:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            r = p.add_run(f"{k}：")
            _set_run_font(r, size=12, bold=True, cn=CN_HEAD)
            r2 = p.add_run(v)
            _set_run_font(r2, size=12)

    def toc(self, title: str = "目  录"):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.page_break_before = True
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(14)
        r = p.add_run(title)
        _set_run_font(r, size=16, bold=True, cn=CN_HEAD)

        par = self.doc.add_paragraph()
        par.paragraph_format.first_line_indent = Pt(0)
        run = par.add_run()
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = r' TOC \o "1-3" \h \z \u '
        fld_sep = OxmlElement("w:fldChar")
        fld_sep.set(qn("w:fldCharType"), "separate")
        t = OxmlElement("w:t")
        t.text = "打开文档后按 Ctrl+A、F9 更新目录；或在 Word 中右键“更新域”。"
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        for el in (fld_begin, instr, fld_sep, t, fld_end):
            run._r.append(el)
        _set_run_font(run, size=10.5, color=RGBColor(0x7F, 0x7F, 0x7F))

    def set_update_fields(self):
        settings = self.doc.settings.element
        el = settings.find(qn("w:updateFields"))
        if el is None:
            el = OxmlElement("w:updateFields")
            settings.append(el)
        el.set(qn("w:val"), "true")

    def save(self, path: Path):
        self.set_update_fields()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(path))


def load_results() -> dict:
    return json.loads((ROOT / "results" / "results.json").read_text(encoding="utf-8"))
