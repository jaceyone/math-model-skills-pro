# S4 论文撰写（论文手）

## 目标

按 `plan.md` 的交付形态写论文：**LaTeX 模式**编译 PDF（默认），**Word 模式**生成 DOCX（赛题强制时）。所有数值来自 `results/results.json`，所有图来自 `figures/manifest.json`。

## 输入

- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/RESULTS_REPORT.md`
- `reports/FIGURE_REPORT.md`
- `reports/symbols.md`（符号表；「符号说明 / Notation」章直接照抄，不重排、不改名、不并进模型章）
- `reports/journal_problemN.md`（图表结论优先摘抄纪要，不凭记忆写图注）
- `reports/SCORE_MAP.md`（得分点落点表；本章负责把公式号/图号/表号补齐）
- `plan.md`（语言、模板、交付形态、页数档位）
- `results/results.json`、`results/tables/*.csv`
- `figures/manifest.json`
- `references/knowledge/10-chapter-writing-prompts.md`（**逐章写作提示词，写哪章读哪节**）
- `references/knowledge/13-writing-injection.md`（摘要句链、推导三段式、一致性、表格、统计、引用）
- `assets/templates/latex/workshop/`（LaTeX 默认模板）
- `assets/templates/docx/reference.docx` + `assets/templates/docx/report_kit.py`（Word 模式）

## 步骤

### 0. 交付形态判断

- `plan.md` 写 **LaTeX PDF**：执行 1–6 步。
- `plan.md` 写 **Word**：直接跳到「Word 原生分支」，不要复制 LaTeX 模板，也不要跑 `latex2docx.py`。

### 1. 选模板

| 场景 | 模板 |
|---|---|
| **默认（国赛/省赛/校赛/课程论文，无特殊要求）** | `assets/templates/latex/workshop/`（默认论文模板：`format.cls` + 17 个带写作提示词的章节文件） |
| CUMCM 官方格式（要 AI 声明宏、官方封面） | `assets/templates/latex/cumcmthesis/` |
| MCM/ICM（英文） | `assets/templates/latex/mcm/` |
| 华为杯 | `assets/templates/latex/huaweibei/` |
| 通用中文结构（`ctexart`，无竞赛格式要求时） | `assets/templates/latex/default/` |

**整目录复制到 `paper/`，不要从零写文档类**。workshop 模板的 `fonts/` 必须跟 `main.tex` 同级（`format.cls` 用 `./fonts/` 相对路径取思源宋体与隶书），并在 `paper/` 目录内编译。

> 逐章写作提示词只覆盖 `workshop`（17 个 `.tex` 末尾的【本章节写作提示词】）。用 `mcm` / `huaweibei` / `cumcmthesis` 时没有对应提示词文件：按该模板 `sections/` 里的注释块与总则【英文链条】走，不要硬套中文提示词；章节顺序见 `knowledge/10` 的【英文链条】。

### 2. 章节骨架

```text
paper/
├── main.tex                 入口：队伍信息 + 标题 + \input 各章
├── format.cls               模板类文件（不改）
├── fonts/                   三套字体（不删）
├── 0.摘要.tex
├── 1.引言.tex
├── 2.总体分析.tex
├── 3.模型假设.tex
├── 4.符号说明.tex
├── 5.模型的建立与求解.tex   \input 5.1.问题一.tex
├── 5.1.问题一.tex
├── 5.1.1.具体分析.tex
├── 5.1.2.模型准备.tex
├── 5.1.3.模型建立.tex
├── 5.1.4.模型求解.tex
├── 6.模型检验.tex
├── 7.模型评价.tex
├── 8.模型改进推广.tex
├── 9.AI说明.tex
├── 10.参考文献.tex
└── 11.附录.tex
```

问题数 >1 时，把 `5.1.*` 五件套复制成 `5.2.*`、`5.3.*`，在 `5.模型的建立与求解.tex` 里依次 `\input`；每问内部仍是「具体分析 → 模型准备 → 模型建立 → 模型求解」四小节。

用 CUMCMThesis / MCM / 华为杯模板时，骨架按该模板 `sections/` 的既有文件走，不套 workshop 的文件名。

### 3. 逐章写作（先读提示词，再动笔）

对每一章：

1. 读 `references/knowledge/10-chapter-writing-prompts.md` 里该章那一节（模板 `.tex` 末尾也有同一份注释）；
2. 按提示词给定的结构、句式、字数、表格列宽写；
3. 写完对着该节末尾的「【禁止】/【格式】」逐条自查；
4. 数值从 `results.json` 取，图号表号按插入顺序。

**顺序**：先写 5.X（主体）→ 6 检验 → 7 评价 → 8 推广 → 2 总体分析 → 1 引言 → 3 假设 → 4 符号 → **最后写 0 摘要**（摘要必须在全文完成后提炼，且写满一页不溢出）。参考文献与附录随写随补。

### 4. 图表插入

workshop 模板不带 `\fig` / `\tabcaption` 辅助宏，直接写标准环境：

```latex
\begin{figure}[ht]
  \centering
  \includegraphics[width=0.8\textwidth]{../figures/data_q3_fit.png}
  \caption{训练集拟合值与真实值对比}
  \label{fig:q3_fit}
\end{figure}
```

- **图片路径按 `main.tex` 所在目录解析**（xelatex 在 `paper/` 下跑）：图片写 `../figures/xxx.png`。这条只针对 LaTeX；Python 脚本里禁止 `../figures/`（见 `11-engineering-contract.md`）。
- **宽度按宽高比档位**：宽高比 ≥0.9（竖图）用 `0.55~0.65\textwidth`；0.6~0.9 用 `0.60~0.70`；<0.6（宽幅）用 `0.65~0.75`；并排两张各 `0.45~0.50`。只给 `width=`，不要只给 `height=`。
- **表格一律 `longtable` + 定宽列**，首尾加 `@{}` 后列宽总和 = `1.04 − 0.04×N`（N 为列数），表头列名不加粗，必须带 `\caption`：

```latex
\begin{longtable}{>{\centering\arraybackslash}p{0.18\textwidth}>{\centering\arraybackslash}p{0.78\textwidth}}
  \caption{符号说明}
  \label{tab:symbols} \\
  \toprule
  符号 & 说明 \\
  \midrule
  \endfirsthead
  \caption{符号说明（续）} \\
  \toprule
  符号 & 说明 \\
  \midrule
  \endhead
  \bottomrule
  \endfoot
  $x_1$ & 固定酸度（g/L） \\
\end{longtable}
```

- 表题在表上、图题在图下；题注写清「画的是哪些量、在对照什么」（见 `13-writing-injection.md` 第三节第 10 条）。
- 用 CUMCMThesis 等带 helper 的模板时，按该模板 `main.tex` 顶部的写作提示用 `\fig{宽度}{路径}{题}{label}` / `\tabcaption{题}{label}{列格式}{内容}`，不要混用两套写法。

### 5. 数值与一致性核账

- 每个数字都能指到 `results.json` 的键；不允许「论文阶段重新估算」或换一套四舍五入。
- 同一指标在摘要、正文、检验节、模型评价四处必须同值同口径（`13-writing-injection.md` 第一节第 4/6 条）。
- 实验预算（样本量、种子、重复次数、超参数）全文只有一套。
- 正文不出现 `reports/`、`code/`、`results.json`、`plan.md`、`manifest.json` 等内部名字。
- 图必须被正文引用并解读；连续三张以上图表中间必须有文字。
- **机器校验**（别靠眼看）：

  ```bash
  python <skill-root>/scripts/check_paper.py --project 项目1
  ```

  六项都要退出码 0：① 正文每个数字都能在 `results.json` 里找到同值（四舍五入、百分比、kN 换算都算命中）；命中不了的，要么是常数/派生量 → 写进 `results/numbers_allow.txt` 并注明来源，要么是凭记忆写的 → 改掉。② `references.tex` 的 `\bibitem` 键与正文 `\cite` 一一对应，且不能是 `enumerate` 手写条目（手写等于没有引用）。③ 符号说明独立成章且排在模型章之前，表里符号要在正文出现过。④ 必产文件齐全、`SCORE_MAP.md` 落点列填满——**落点写法**：`\ref{key}`（key 必须真在全文 `\label` 里）或 `图 N / 表 N / 式(N) / §N`（N 不超过论文里实际的图/表/公式/节数）。⑤ 正文无内部文件名与占位符（会先做宏展开与 `%` 续行拼接）。⑥ 正文 `\includegraphics` 的图都登记在 `figures/manifest.json`，且 `id` 与文件名一致、`outputs` 里的文件真实可打开。

### 6. 编译与验收

```bash
cd paper && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex
# 或
python <skill-root>/scripts/build_paper.py --project 项目1
```

`build_paper.py` 会输出 `reports/BUILD_REPORT.md`：错误数、未定义引用、缺图、Overfull/Underfull、页数。**这份报告是回改的输入，不是日志**：有 error / 未定义引用 / 缺图就改到清零再重跑，页数超档就按 `13-writing-injection.md` 的档位删内容；终稿必须附一份全零的 `BUILD_REPORT.md`。

验收线：0 error、0 缺失文件、未定义引用 0、Overfull 0（Underfull 与 Overfull 都计入 `BUILD_REPORT` 的 WARN，Overfull 必须清零，Underfull 可留但要在报告里写一句原因）；页数符合赛制档位（见 `13-writing-injection.md`）；摘要严格一页。查页用 `pdftoppm -png -r 80 main.pdf pages/p` 转图后逐页看版面。

> 空白模板首编会有 1 个占位符未定义引用（`fig:xxx`）和若干 Overfull，属正常；插入真实图表后必须清零，否则不许交付。

## Word 原生分支（赛题强制 Word）

### W1 模板与骨架

复制 `assets/templates/docx/reference.docx` 到 `report/`，用 `assets/templates/docx/report_kit.py` 生成 `report/数据分析报告.docx`。不要建 `paper/`，不要跑 xelatex 或 `latex2docx.py`。

```python
from pathlib import Path
from report_kit import Report

r = Report(Path("report/reference.docx"))       # ROOT = 本文件父目录的父目录（即项目根）
r.cover("2026 全国大学生大数据分析技术技能竞赛", "报告标题", "副标题", [("组别", "…"), ("姓名", "…")])
r.p("摘要正文，含 3–4 个关键数值……")
r.toc()                                          # 目录域，打开后更新
r.h1("一、项目概述", page_break=True)
...
r.save(Path("report/数据分析报告.docx"))          # 自动置 updateFields
```

章节函数化：`code/sections_a.py`（前半）、`code/sections_b.py`（后半）、`code/make_report.py`（拼装），改一章不用动全篇。

### W2 报告结构

封面 → 摘要与关键词 → 目录 → 项目概述 → 数据理解 → 数据清洗 → 数据整理 → 数据分析 → 模型/回归 → 可视化 → 结论 → 附录。按赛题提纲增删；每一章用 `h1(..., page_break=True)` 起新页。

### W3 图表

- 图：`r.fig("data_q2_corr", "图题", width=15)`，从 `figures/` 取 `manifest.json` 登记的图；正文宽表多时降到 13.4 cm；图题由图注承担，图内不要 `set_title()`。
- 表：`r.csv_table("q3_coef", "回归系数表", widths=[...], nd=3, note="注：…")`，表题在表上。
- 12 列宽表：用短表头（固定酸/挥发酸/游离SO2/总SO2/评分）+ 表下注释，不要硬塞全称。
- 小表（≤8 行）已自动 `cantSplit` 防跨页；大表重复表头。
- 每个图表后至少一段（≥100 字）分析。

### W4 域更新与 PDF

```python
# code/to_pdf.py 用 Word COM（comtypes）更新目录/页码域并导出 PDF，同时回读页数
```
无 Word 时用 LibreOffice 兜底：`soffice --headless --convert-to pdf report/数据分析报告.docx`。

### W5 验收

- 目录页码与正文一致（域已更新）；页脚「第 N 页」为 PAGE 域而不是死数字。
- 无空白页（分页用 `page_break_before`，不要 `add_page_break()` 叠加）。
- 表格不跨页断裂、表头在每页重复；图不模糊（PNG ≥260 dpi）。
- 文档属性里作者/标题已填，正文无内部文件名。
- DOCX 为权威版本，PDF 只作预览；两者页数一致。

## 必须产出

LaTeX 模式：

- `paper/main.tex`、`paper/sections or 各章 .tex`、`paper/main.pdf`
- 可选：`paper/论文.docx`（用 `scripts/latex2docx.py` 导出的改稿副本）

Word 模式：

- `report/数据分析报告.docx`（必须）
- `report/数据分析报告.pdf`（预览）
- `figures/manifest.json`

## 边界

- 不重新建模、不重跑大规模实验；数值缺失回 S2 补，不在写作阶段口头补数。
- 不编造数值、参考文献、实验结果。
- 不用 Typst。
- LaTeX 模式不改模板导言区补包；Word 模式不复制 LaTeX 模板。
- 不做提交打包（压缩包由用户自行打）。

## 门禁

通过 `references/checklists/G4-writing.md` 后完成。
