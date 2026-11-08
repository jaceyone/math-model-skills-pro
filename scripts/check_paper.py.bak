#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文自检：正文数字 ↔ `results/results.json`，文献 ↔ `\\cite`。

两个检查都是"能不能指回去"的检查，不是风格检查：

1. **数字**：正文里的每个数都要能在 `results.json` 里找到同值（允许四舍五入、百分比、kN/MN 换算）。
   找不到的，要么是常数/派生量（写进 `results/numbers_allow.txt`），要么是凭记忆写的（改掉）。
2. **文献**：`references.tex` 里的条目与正文 `\\cite{}` 必须一一对应；用 `enumerate` 手写条目等于没有引用，
   直接判失败（正文角标对不上条目，评委一眼看出）。

用法（在项目根目录，或 `--project 项目N`）：

    python <skill-root>/scripts/check_paper.py --project 项目1
    python <skill-root>/scripts/check_paper.py --project 项目1 --numbers-only
    python <skill-root>/scripts/check_paper.py --project 项目1 --update-allow   # 把未命中项写进允许清单

退出码：0 = 两个检查都过；1 = 有未命中数字或引用不闭环。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# 正文里这些命令的参数不是"内容数字"，先整段抹掉
STRIP_CMDS = (
    "ref", "eqref", "label", "cite", "citep", "citet", "input", "include",
    "includegraphics", "begin", "end", "usepackage", "documentclass", "setlength",
    "addtolength", "newcommand", "renewcommand", "hspace", "vspace", "rule",
    "fontsize", "arraystretch", "def", "pgfmathsetmacro", "pgfmathtruncatemacro",
    "setcounter", "cline", "cmidrule", "multicolumn", "bibliography",
    "bibliographystyle", "url", "href", "pageref", "captionsetup", "color",
    "pagebreak", "nopagebreak", "nocite",
)
STRIP_RE = re.compile(r"\\(" + "|".join(STRIP_CMDS) + r")\*?(\[[^\]]*\])?\{[^{}]*\}")
FONTSIZE_RE = re.compile(r"\\fontsize\{[^{}]*\}\{[^{}]*\}")
# \newcommand{\TeamNumber}{2500} 这类宏定义里的数字是元信息，不是结果值
NEWCMD_RE = re.compile(r"\\(?:re)?newcommand\*?\{[^{}]*\}(?:\[[^\]]*\])?\{[^{}]*\}")
# \pagebreak[100] 这类只有可选参数的排版命令，参数不是内容数字
PAGEBREAK_RE = re.compile(r"\\(?:pagebreak|nopagebreak|vspace|hspace)\*?\[[^\]]*\]")
# siunitx 的可选参数：\num[round-mode=places]{3.14159}
SIOPT_RE = re.compile(r"\\(?:num|qty|SI|ang)\s*\[[^\]]*\]\s*\{")
# 数字后面紧跟排版单位 → 版式参数，不是内容数字
UNIT_RE = re.compile(r"\s*(pt|em|ex|cm|mm|in|\\textwidth|\\linewidth|\\textheight|\\baselineskip)")
NUM_RE = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
COMMENT_RE = re.compile(r"(?<!\\)%.*$")
# 7\,225\,200 这种千分位写法：先把数字间的细空格去掉，否则会被切成 7 / 225 / 200
THINSPACE_RE = re.compile(r"(?<=\d)\\,\s*(?=\d)")


def _nfkc(text: str) -> str:
    """全角数字/字母折成半角：`３．１４` 不折会被拆成 ３ + １４ 逃过检查。"""
    return unicodedata.normalize("NFKC", text)


def iter_numbers(obj, out: list[float]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            iter_numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            iter_numbers(v, out)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        out.append(float(obj))


def value_variants(v: float) -> set[float]:
    """一个结果值可能以这些形式出现在正文里：原值/绝对值/百分数/千倍/百万倍/四舍五入。"""
    cands: set[float] = set()
    for base in (v, abs(v)):
        for scaled in (base, base * 100.0, base / 100.0, base * 1e3, base / 1e3, base * 1e6, base / 1e6):
            cands.add(scaled)
            for nd in (1, 2, 3, 4):
                cands.add(round(scaled, nd))
    return cands


def load_allow(path: Path) -> list[re.Pattern[str]]:
    if not path.is_file():
        return []
    pats = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        s = line.split("#", 1)[0].strip()
        if not s:
            continue
        pats.append(re.compile(r"^" + s + r"$"))
    return pats


def _bib_file(paper: Path) -> Path | None:
    """文献文件：优先 references.tex，否则找第一个含 thebibliography/\\bibitem 的 .tex。"""
    refs = paper / "references.tex"
    if refs.is_file():
        return refs
    for p in sorted(paper.rglob("*.tex")):
        try:
            t = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if re.search(r"\\begin\{thebibliography\}|\\bibitem", t):
            return p
    return None


def scan_tex(paper: Path) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    bib = _bib_file(paper)
    skip = {bib.resolve()} if bib is not None else set()
    for path in sorted(paper.rglob("*.tex")):
        if path.name == "A_code.tex" or path.resolve() in skip:
            continue
        in_tikz = False
        for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            s = raw.strip()
            # TikZ 里的坐标/间距是版式参数，不是内容数字
            if s.startswith("\\begin{tikzpicture}"):
                in_tikz = True
                continue
            if s.startswith("\\end{tikzpicture}"):
                in_tikz = False
                continue
            if in_tikz:
                continue
            line = _nfkc(COMMENT_RE.sub("", raw))
            if not line.strip():
                continue
            line = FONTSIZE_RE.sub(" ", line)
            line = NEWCMD_RE.sub(" ", line)
            line = PAGEBREAK_RE.sub(" ", line)
            line = STRIP_RE.sub(" ", line)
            line = THINSPACE_RE.sub("", line)
            # siunitx / 手工小数逗号：{,} 是排版写法，语义是小数点
            line = line.replace("{,}", ".")
            line = SIOPT_RE.sub("{", line)
            line = line.replace("\\num{", "{").replace("\\SI{", "{").replace("\\qty{", "{")
            for m in NUM_RE.finditer(line):
                tok = m.group(0)
                if UNIT_RE.match(line[m.end():]):
                    continue
                # 跳过：年份、小节/公式编号残留、小整数（系数、下标、条数）。
                # 阈值 20 是权衡：压到 10 会把「5 Hz」「3 个问题」这类正常小整数全判成未命中，
                # 三份合规稿当场被误杀；小整数的错只能靠人核（已写进 04-writing.md 的已知盲区）
                if re.fullmatch(r"(19|20)\d{2}", tok):
                    continue
                val = float(tok)
                if abs(val) <= 20 and "." not in tok:
                    continue
                hits.append((path, lineno, tok))
    return hits


def check_numbers(project: Path, tol: float = 5e-3) -> tuple[int, list[str]]:
    res_path = project / "results" / "results.json"
    if not res_path.is_file():
        return 1, [f"缺少 {res_path}"]
    try:
        # utf-8-sig：PowerShell / 记事本存盘会带 BOM，普通 utf-8 读会直接崩
        raw = json.loads(res_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return 1, [f"{res_path} 不是合法 JSON：{exc}"]
    values: list[float] = []
    iter_numbers(raw, values)
    cands: set[float] = set()
    for v in values:
        cands |= value_variants(v)

    allow = load_allow(project / "results" / "numbers_allow.txt")
    paper = project / "paper"
    if not paper.is_dir():
        paper = project / "paper_zh"
    hits = scan_tex(paper)

    misses: list[str] = []
    ok = 0
    for path, lineno, tok in hits:
        val = float(tok)
        mag = abs(val)
        if any(abs(mag - abs(c)) <= max(1e-9, tol * abs(c)) for c in cands):
            ok += 1
            continue
        if any(p.match(tok) for p in allow):
            ok += 1
            continue
        rel = path.relative_to(project).as_posix()
        misses.append(f"  {rel}:{lineno}  {tok}")

    lines = [
        f"results.json 数值 {len(values)} 个，正文数字 {len(hits)} 个，命中 {ok} 个，未命中 {len(misses)} 个",
    ]
    if misses:
        lines += misses[:40]
        if len(misses) > 40:
            lines.append(f"  … 另有 {len(misses) - 40} 条")
        lines.append("未命中项若确为常数/派生量，写进 results/numbers_allow.txt（每行一个正则，可加 # 注释）")
    return (0 if not misses else 1), lines


def check_refs(project: Path) -> tuple[int, list[str]]:
    paper = project / "paper"
    if not paper.is_dir():
        paper = project / "paper_zh"
    # 文献不强制叫 references.tex：有的模板把 bib 内联在某个章节 .tex 里
    refs = _bib_file(paper)
    if refs is None:
        return 1, [f"{paper} 下没有任何文件含 \\begin{{thebibliography}} 或 \\bibitem"]

    raw = refs.read_text(encoding="utf-8-sig", errors="replace")
    # 注释里的 \bibitem{标签} 是写法示例，不是条目：不剥注释会把模板示例键当真实文献
    text = "\n".join(COMMENT_RE.sub("", line) for line in raw.splitlines())
    keys = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", text))
    n_items = len(re.findall(r"\\item\b", text))
    lines: list[str] = []
    if refs.name != "references.tex":
        lines.append(f"文献文件：{refs.relative_to(project).as_posix()}（非 references.tex，按内容识别）")

    if not keys:
        lines.append(
            f"references.tex 用 enumerate 手写 {n_items} 条，没有 \\bibitem 键 → 正文无法 \\cite，角标与条目对不上"
        )
        lines.append("改法：\\begin{thebibliography}{9} + \\bibitem{key}，正文用 \\cite{key}")
        return 1, lines

    cited_all: set[str] = set()
    cited_small: set[str] = set()
    for path in sorted(paper.rglob("*.tex")):
        if path.name == refs.name:
            continue
        # 注释掉的 \cite 不算引用（否则注掉一枚角标就能让未引条目蒙混过关）
        body = "\n".join(COMMENT_RE.sub("", line)
                         for line in path.read_text(encoding="utf-8-sig").splitlines())
        for m in re.finditer(r"\\cite[a-z]*\{([^}]+)\}", body):
            ks = [k.strip() for k in m.group(1).split(",") if k.strip()]
            cited_all |= set(ks)
            # 一次 cite 一堆键 = 没真读：>3 个键的组只算「出现过」，不算「被引用」
            if len(ks) <= 3:
                cited_small |= set(ks)

    missing = sorted(cited_all - keys)
    unused = sorted(keys - cited_small)
    nocite = False
    for p in paper.rglob("*.tex"):
        body = "\n".join(COMMENT_RE.sub("", line)
                         for line in p.read_text(encoding="utf-8-sig").splitlines())
        if re.search(r"\\nocite\{", body):
            nocite = True
            break
    lines.append(f"条目 {len(keys)} 条；\\cite 覆盖 {len(cited_all)} 个键，"
                 f"其中单独或小组（≤3 键）引用 {len(cited_small)} 个")
    if missing:
        lines.append("引用了不存在的条目：" + ", ".join(missing))
    if unused:
        lines.append("有条目只被群引或从未引用（要求每个键至少单独/小组引用一次）：" + ", ".join(unused))
    if nocite:
        lines.append("检测到 \\nocite：它不算引用，条目必须真的被 \\cite 到")
    if not cited_all:
        lines.append("正文一次都没引用 → 参考文献等于装饰，G4 的「角标与条目一一对应」不成立")
    bad = bool(missing) or bool(unused) or not cited_all
    return (0 if not bad else 1), lines


def _paper_dir(project: Path) -> Path:
    paper = project / "paper"
    return paper if paper.is_dir() else project / "paper_zh"


def _notation_symbols(path: Path) -> list[str]:
    r"""符号表里的符号 token（跳过表头与分隔线；一格里写多个符号就拆开）。"""
    if not path.is_file():
        return []
    out: list[str] = []
    seen_body = False
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        s = COMMENT_RE.sub("", raw).strip()
        if re.match(r"\\midrule|\\bottomrule", s):
            seen_body = True
            continue
        if not seen_body or "&" not in s or s.startswith("\\"):
            continue
        cells = [c.strip() for c in s.rstrip("\\").strip().strip("&").split("&")]
        if len(cells) < 2:
            continue
        first, second = cells[0], cells[1]
        if not second.strip() or not first.strip():
            continue
        if set(first) <= set("-: "):
            continue
        for tok in re.split(r"[,，、]", first):
            t = tok.replace("$", "").replace("{", "").replace("}", "").strip()
            t = t.lstrip("\\").strip()
            if len(t) >= 1 and not set(t) <= set("-: ."):
                out.append(t)
    return out


def check_structure(project: Path) -> tuple[int, list[str]]:
    """章节结构：符号说明独立成章、排在模型建立之前、表里真有符号且正文真用到。"""
    paper = _paper_dir(project)
    main = paper / "main.tex"
    if not main.is_file():
        return 1, [f"缺少 {main}"]
    text = main.read_text(encoding="utf-8-sig")
    # 先剥注释：注释掉的 \input 不算数（否则把前位的 input 注掉就能骗过顺序检查）
    body = "\n".join(COMMENT_RE.sub("", line) for line in text.splitlines())
    raw_inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", body)
    order = [Path(p).stem for p in raw_inputs]

    def is_notation(stem: str) -> bool:
        s = stem.lower()
        return "notation" in s or "symbol" in s or "符号说明" in stem

    def is_model(stem: str) -> bool:
        s = stem.lower()
        return ("model_design" in s or "模型建立" in stem or "模型的建立" in stem
                or "solution" in s or "problem1" in s or "问题一" in stem)

    idxs_n = [i for i, s in enumerate(order) if is_notation(s)]
    if not idxs_n:
        extra = ""
        sec = paper / "sections"
        if sec.is_dir() and any(is_notation(p.stem) for p in sec.glob("*.tex")):
            extra = "（sections/ 里有符号说明文件，但 main.tex 没 \\input 它）"
        return 1, ["没有独立的「符号说明 / Notation」章：文件名与 \\section 都找不到" + extra,
                   "符号表不许并进模型章——读者必须在第一条用到符号的公式之前见到它"]
    if len(idxs_n) > 1:
        return 1, [f"符号说明被 \\input 了 {len(idxs_n)} 次（第 "
                   + "、".join(str(i + 1) for i in idxs_n) + " 位）：只能出现一次"]

    # 表里必须真有符号行，空表头不算
    notation_path = None
    for raw_path in raw_inputs:
        p = raw_path if raw_path.endswith(".tex") else raw_path + ".tex"
        cand = paper / p
        if is_notation(Path(raw_path).stem) and cand.is_file():
            notation_path = cand
            break
    if notation_path is None:
        notation_path = next((p for p in (paper / "sections").glob("*.tex") if is_notation(p.stem)), None)
    symbols = _notation_symbols(notation_path) if notation_path else []
    if len(symbols) < 3:
        return 1, [f"符号说明章只有 {len(symbols)} 行符号（要求 ≥3）：表头或占位符不算数",
                   f"文件：{notation_path}"]
    # 垃圾行防护：符号必须在正文的**数学语境**里真出现过（注释、纯文字提及不算）
    body_text = ""
    for p in sorted(paper.rglob("*.tex")):
        if notation_path is not None and p.resolve() == notation_path.resolve():
            continue
        body_text += "\n".join(COMMENT_RE.sub("", ln) for ln in
                               p.read_text(encoding="utf-8-sig", errors="replace").splitlines())
    # 只留数学语境：$...$、equation/align 环境、tabular 表体
    math_bits: list[str] = []
    math_bits += re.findall(r"\$[^$]*\$", body_text)
    math_bits += re.findall(r"\\begin\{(?:equation|align|gather|multline)\*?\}(.*?)"
                            r"\\end\{(?:equation|align|gather|multline)\*?\}", body_text, re.S)
    math_bits += re.findall(r"\\begin\{(?:tabular|longtable)\}(.*?)\\end\{(?:tabular|longtable)\}",
                            body_text, re.S)
    math_text = "\n".join(math_bits)
    used = [s for s in symbols if s in math_text]
    if len(used) < max(3, int(0.6 * len(symbols))):
        missing_sym = [s for s in symbols if s not in used][:8]
        return 1, [f"符号表 {len(symbols)} 行，只有 {len(used)} 个符号在正文出现过（要求 ≥60%）",
                   "没出现过的：" + "、".join(missing_sym),
                   "表里塞占位符号不算数——每个符号都要在正文公式/表格里真用到"]
    idx_m = next((i for i, s in enumerate(order) if is_model(s)), None)
    if idx_m is not None and idxs_n[-1] > idx_m:
        return 1, [f"「符号说明」排在模型章之后（第 {idxs_n[-1] + 1} 位 vs 第 {idx_m + 1} 位）",
                   "必须在模型假设之后、模型建立之前"]
    pos = f"第 {idxs_n[-1] + 1} 位" if idx_m is None else f"第 {idxs_n[-1] + 1} 位，在模型章（第 {idx_m + 1} 位）之前"
    return 0, [f"章节共 {len(order)} 个 \\input/\\include；符号说明{pos}；表内 {len(symbols)} 行，"
               f"其中 {len(used)} 个符号在正文出现"]


REQUIRED_ARTIFACTS = (
    "plan.md", "todo.md",
    "reports/ANALYSIS_MODELING_REPORT.md", "reports/symbols.md", "reports/SCORE_MAP.md",
    "reports/RESULTS_REPORT.md", "reports/FIGURE_REPORT.md",
    "results/results.json", "figures/manifest.json", "paper/main.tex",
)


def check_artifacts(project: Path) -> tuple[int, list[str]]:
    """产物闭环：必产文件在不在，SCORE_MAP 的落点列填没填。"""
    missing = [p for p in REQUIRED_ARTIFACTS if not (project / p).exists()]
    if not list((project / "reports").glob("journal_problem*.md")):
        missing.append("reports/journal_problemN.md")
    lines: list[str] = []
    if missing:
        lines.append("缺少必产文件：" + ", ".join(missing))
    score = project / "reports" / "SCORE_MAP.md"
    empty_rows: list[str] = []
    if score.is_file():
        paper = _paper_dir(project)
        body = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                         for p in sorted(paper.rglob("*.tex")))
        labels = set(re.findall(r"\\label\{([^}]+)\}", body))
        n_fig = len(re.findall(r"\\begin\{figure\*?\}", body))
        n_tab = len(re.findall(r"\\begin\{(?:table|longtable)\*?\}", body))
        n_eq = len(re.findall(r"\\begin\{(?:equation|align)\*?\}", body))
        n_sec = len(re.findall(r"\\(?:sub)?section\{", body))
        col = None
        n_cols = 0
        for raw in score.read_text(encoding="utf-8-sig").splitlines():
            s = raw.strip()
            if not s.startswith("|") or set(s) <= set("|-: "):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells:
                continue
            # 每张子表都有自己的表头：见到表头就重置列定位，别把表头当数据
            if any("得分点" in c for c in cells) or cells[0] in ("#", "编号", "ID"):
                hits = [i for i, c in enumerate(cells) if "落点" in c or ("公式" in c and "图" in c)]
                col = hits[-1] if hits else len(cells) - 1   # 「计划落点 / 落点（S4 补）」并存时取最后一列
                n_cols = len(cells)
                continue
            if col is None:
                col = len(cells) - 1
                n_cols = len(cells)
            # 行内可能有多余的 |（如 max|ω|），格数对不上就退回最后一格
            idx = col if (len(cells) == n_cols and col < len(cells)) else len(cells) - 1
            cell = _nfkc(cells[idx]).strip()
            placeholder = cell in ("", "—", "-", "–", "TBD", "待填", "待补", "待定",
                                   "N/A", "NA", "?", "无", "略", "…", "...", "见正文", "同上")
            ok_anchor = False
            over_cap = False
            for key in re.findall(r"\\ref\{([^}]+)\}", cell):
                if key.strip() in labels:        # 指到的 label 必须真的存在
                    ok_anchor = True
            # 编号校验：图/表能可靠数出来，超量即判空；公式与节号写法太多（\tag、5.1.2 节），
            # 只要求「指得到」，不做上限，否则会把合规稿误杀
            for pat, cap in ((r"(?:图|Fig(?:ure)?\.?)\s*(\d+)", n_fig),
                             (r"(?:表|Tab(?:le)?\.?)\s*(\d+)", n_tab),
                             (r"(?:式|Eq(?:uation)?\.?|公式)\s*\(?(\d+)", None),
                             (r"(?:Sec(?:tion)?\.?|§)\s*(\d+)", None)):
                for m in re.finditer(pat, cell):
                    num = int(m.group(1))
                    if cap is None:
                        if num >= 1:
                            ok_anchor = True
                    elif 1 <= num <= max(cap, 1):
                        ok_anchor = True
                    else:
                        over_cap = True
            if over_cap:
                ok_anchor = False
            if placeholder or not ok_anchor:
                empty_rows.append(s[:60])
    if empty_rows:
        lines.append(f"SCORE_MAP 有 {len(empty_rows)} 行落点列没填（公式号/图号/表号）：")
        lines += [f"  {row}" for row in empty_rows[:8]]
    if not lines:
        lines.append(f"必产文件 {len(REQUIRED_ARTIFACTS)} 项齐全；SCORE_MAP 落点列已填")
    return (1 if missing or empty_rows else 0), lines


FORBIDDEN = (
    (r"reports/", "内部目录 reports/"),
    (r"(?<![A-Za-z0-9_])code/", "内部目录 code/"),
    (r"results\.json", "内部文件名 results.json"),
    (r"manifest\.json", "内部文件名 manifest.json"),
    (r"plan\.md", "内部文件名 plan.md"),
    (r"_figure_lint", "内部文件名 _figure_lint"),
    (r"\bTODO\b", "占位符 TODO"),
    (r"待补充", "占位符 待补充"),
    (r"待填", "占位符 待填"),
)


def _deobfuscate(line: str) -> str:
    """拆掉断词与全角伪装：re\\-ports/、ｒｅｐｏｒｔｓ／、re{}ports/ 都要还原成 reports/。"""
    s = _nfkc(line)
    for junk in ("\\-", "\\allowbreak", "\\allowbreak{}", "{}", "\\hspace{0pt}", "\\,"):
        s = s.replace(junk, "")
    return s


def check_forbidden(project: Path) -> tuple[int, list[str]]:
    """正文不许出现内部文件名与占位符（宏展开、% 续行拼接后再查）。"""
    paper = _paper_dir(project)
    # 一层宏展开：\newcommand{\rr}{reports/} 之后写 \rr 也是内部文件名
    defs: dict[str, str] = {}
    for p in sorted(paper.rglob("*.tex")):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        for m in re.finditer(r"\\(?:re)?newcommand\*?\{?\\([A-Za-z@]+)\}?\{([^{}]*)\}", t):
            defs["\\" + m.group(1)] = m.group(2)
        for m in re.finditer(r"\\def\\([A-Za-z@]+)\{([^{}]*)\}", t):
            defs.setdefault("\\" + m.group(1), m.group(2))

    hits: list[str] = []
    for path in sorted(paper.rglob("*.tex")):
        if path.name == "references.tex":
            continue
        raw_lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        # LaTeX 里行尾 % 会吃掉换行：先把续行拼起来，再剥注释
        joined: list[tuple[int, str]] = []
        buf, start = "", 0
        for i, raw in enumerate(raw_lines, 1):
            if not buf:
                start = i
            if raw.rstrip().endswith("%") and not raw.rstrip().endswith("\\%"):
                buf += raw.rstrip()[:-1]
                continue
            joined.append((start, buf + raw))
            buf = ""
        if buf:
            joined.append((start, buf))

        in_listing = False
        for lineno, raw in joined:
            s = raw.strip()
            if s.startswith("\\begin{lstlisting}"):
                in_listing = True
                continue
            if s.startswith("\\end{lstlisting}"):
                in_listing = False
                continue
            if in_listing:
                continue
            line = _deobfuscate(COMMENT_RE.sub("", raw))
            for name, body in defs.items():
                if name in line:
                    line = line.replace(name, body)
            for pat, label in FORBIDDEN:
                if re.search(pat, line):
                    hits.append(f"  {path.relative_to(project).as_posix()}:{lineno}  {label}")
    if not hits:
        return 0, ["正文无内部文件名、无占位符（已做宏展开与续行拼接）"]
    return 1, [f"命中 {len(hits)} 处："] + hits[:30]


def check_figures_refs(project: Path) -> tuple[int, list[str]]:
    """图件契约：正文 \\includegraphics 的图必须在 figures/manifest.json 里登记过。"""
    paper = _paper_dir(project)
    manifest = project / "figures" / "manifest.json"
    if not manifest.is_file():
        return 1, [f"缺少 {manifest}"]
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return 1, [f"{manifest} 不是合法 JSON：{exc}"]
    figs = raw.get("figures") if isinstance(raw, dict) else raw
    if isinstance(figs, dict):
        figs = list(figs.values())          # dict 形态统一成 list，走同一套校验
    stems, id_mismatch = set(), []
    for item in figs or []:
        if not isinstance(item, dict):
            continue
        outs = [str(o) for o in (item.get("outputs") or [])]
        # stem 以真实文件名为准（outputs），id 只是标签
        for out in outs:
            stems.add(Path(out).stem)
        if outs:
            first = Path(outs[0]).stem
            ident = item.get("id")
            if ident and Path(str(ident)).stem != first:
                id_mismatch.append(f"  id=`{ident}` 与 outputs[0]=`{outs[0]}` 不一致")
        else:
            for key in ("stem", "id", "file", "path", "name"):
                if item.get(key):
                    stems.add(Path(str(item[key])).stem)
                    break
    used, missing, dead = [], [], []
    for path in sorted(paper.rglob("*.tex")):
        if path.name == "A_code.tex":
            continue
        for lineno, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = COMMENT_RE.sub("", raw_line)
            for arg in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", line):
                stem = Path(arg).stem
                used.append(stem)
                if stem not in stems:
                    missing.append(f"  {path.relative_to(project).as_posix()}:{lineno}  {arg}")
    # manifest 里登记的 outputs 必须真的存在，且 pdf 要是真 PDF（改后缀的 PNG 会被抓）
    for item in figs or []:
        if not isinstance(item, dict):
            continue
        for out in item.get("outputs") or []:
            f = project / str(out)
            # 图必须在工程自己的 figures/ 下：跨目录借一张真 PDF 也算不合规
            try:
                f.resolve().relative_to((project / "figures").resolve())
            except ValueError:
                dead.append(f"  {out} 不在 figures/ 目录下（图件不许跨目录借）")
                continue
            if not f.exists():
                dead.append(f"  manifest 指向不存在的文件：{out}")
            elif f.suffix.lower() == ".pdf":
                with f.open("rb") as fh:
                    head = fh.read(5)
                if head != b"%PDF-":
                    dead.append(f"  {out} 不是真 PDF（文件头不是 %PDF-，多半是把 PNG 改了后缀）")
                else:
                    # 手写个 %PDF- 头也能骗过文件头检查：再用 fitz 打开确认真有页面
                    try:
                        import fitz  # PyMuPDF

                        with fitz.open(str(f)) as doc:
                            if doc.page_count < 1:
                                dead.append(f"  {out} 是 PDF 但没有页面（伪造头）")
                            else:
                                pg = doc[0]
                                if not (pg.get_text().strip() or pg.get_drawings() or pg.get_images()):
                                    dead.append(f"  {out} 是空白 PDF（无文字/无图形/无图像），不是真矢量版")
                    except ImportError:
                        pass
                    except Exception as exc:  # noqa: BLE001
                        dead.append(f"  {out} 打不开：{exc}")
    if id_mismatch:
        return 1, ["manifest 的 id 与 outputs 文件名不一致（契约规定 id = stem）："] + id_mismatch[:10]
    if dead:
        return 1, [f"manifest 有 {len(dead)} 条输出不可用："] + dead[:15]
    if not used:
        return 0, ["正文没有 \\includegraphics（若图表全在附录则忽略这条）"]
    if missing:
        return 1, [f"正文引用了 {len(set(used))} 张图，其中 {len(missing)} 处不在 manifest.json："] + missing[:20]
    return 0, [f"正文 {len(set(used))} 张图全部登记在 manifest.json（共 {len(stems)} 条）"]


def check_escaped_percent(project: Path) -> tuple[int, list[str]]:
    r"""正文把 `%` 当百分号写：LaTeX 会把它当注释，吞掉整行后半句。

    编译 0 error、0 Overfull，数字检查也照样通过（`35.7 ` 还在），但读者看到的是
    "suppressing internal loading by 35.7" 接"the two attractors"——整句被吃掉。
    这是唯一一类"门禁全绿、论文却是残句"的缺陷，所以单独设一项检查。
    """
    paper = _paper_dir(project)
    hits: list[str] = []
    for path in sorted(paper.rglob("*.tex")):
        in_listing = False
        for lineno, raw in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            s = raw.strip()
            if s.startswith("\\begin{lstlisting}"):
                in_listing = True
                continue
            if s.startswith("\\end{lstlisting}"):
                in_listing = False
                continue
            if in_listing or s.startswith("%"):
                continue
            pos = 0
            while True:
                pos = raw.find("%", pos)
                if pos < 0:
                    break
                if pos > 0 and raw[pos - 1] == "\\":
                    pos += 1
                    continue
                before = raw[:pos].rstrip()
                after = raw[pos + 1:].strip()
                if before and before[-1].isdigit() and after:
                    hits.append(f"  {path.relative_to(project).as_posix()}:{lineno}"
                                f"  {raw.strip()[:70]}")
                break
    if not hits:
        return 0, ["正文没有未转义的百分号"]
    return 1, [f"命中 {len(hits)} 处「数字 + 裸 %」——会被当成注释吞掉整行后半句，"
               f"改成 `\\%`："] + hits[:30]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".", help="项目根目录（含 results/ 与 paper/）")
    ap.add_argument("--numbers-only", action="store_true")
    ap.add_argument("--refs-only", action="store_true")
    ap.add_argument("--update-allow", action="store_true", help="把当前未命中数字写入 results/numbers_allow.txt")
    ap.add_argument("--skip", default="", help="跳过的检查，逗号分隔：structure,artifacts,forbidden")
    args = ap.parse_args()
    project = Path(args.project).resolve()

    rc = 0
    if not args.refs_only:
        code, lines = check_numbers(project)
        print("== 数字一致性 ==")
        print("\n".join(lines))
        if args.update_allow and code:
            allow = project / "results" / "numbers_allow.txt"
            allow.parent.mkdir(parents=True, exist_ok=True)
            old = allow.read_text(encoding="utf-8") if allow.is_file() else ""
            extra = [ln.split()[-1] for ln in lines if ln.startswith("  ") and ":" in ln]
            with allow.open("a", encoding="utf-8") as fh:
                if not old:
                    fh.write("# 允许清单：常数、派生量、外部给定值；每行一个正则\n")
                for tok in dict.fromkeys(extra):
                    fh.write(tok + "\n")
            print(f"已把 {len(set(extra))} 项追加到 {allow}")
        rc |= code

    if not args.numbers_only:
        code, lines = check_refs(project)
        print("\n== 文献引用 ==")
        print("\n".join(lines))
        rc |= code

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    if not (args.numbers_only or args.refs_only):
        for name, label, fn in (("structure", "章节结构", check_structure),
                                ("artifacts", "产物闭环", check_artifacts),
                                ("forbidden", "内部文件名", check_forbidden),
                                ("figures", "图件契约", check_figures_refs),
                                ("percent", "百分号转义", check_escaped_percent)):
            if name in skip:
                continue
            code, lines = fn(project)
            print(f"\n== {label} ==")
            print("\n".join(lines))
            rc |= code

    print(f"\n退出码 {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
