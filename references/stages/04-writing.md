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
- `results/results.json`、`results/schema.json`（键名与单位照抄）、`results/tables/*.tex`（表直接用 `\input`）
- `figures/manifest.json`
- `references/knowledge/10-chapter-writing-prompts.md`（**逐章写作提示词，写哪章读哪节**）
- `references/knowledge/13-writing-injection.md`（摘要句链、推导三段式、一致性、表格、统计、引用）
- `assets/templates/latex/default/`（LaTeX 默认模板）
- `assets/templates/docx/reference.docx` + `assets/templates/docx/report_kit.py`（Word 模式）

## 步骤

### 0. 交付形态判断

- `plan.md` 写 **LaTeX PDF**：执行 1–6 步。
- `plan.md` 写 **Word**：直接跳到「Word 原生分支」，不要复制 LaTeX 模板，也不要跑 `latex2docx.py`。

### 1. 选模板

| 场景 | 模板 |
|---|---|
| **默认（国赛/省赛/校赛/课程论文，无特殊要求）** | `assets/templates/latex/default/`（`ctexart`：摘要宏 + 目录 + 8 章 + 参考文献 + 附录，`\fig`/`\tabcaption`/`\threelinetable` 现成） |
| MCM/ICM（英文） | `assets/templates/latex/mcm/` |
| 华为杯 | `assets/templates/latex/huaweibei/` |
| 用户自带模板 | 用户指定目录；整目录复制到 `paper/`，按该模板自己的宏写，不混用 `\fig`/`\tabcaption` |

**整目录复制到 `paper/`，不要从零写文档类**。`default` 走 `fontset=windows`（系统宋体/黑体/楷体），不依赖模板自带字体；用自带字体的模板时，字体目录必须与 `main.tex` 同级，并在 `paper/` 目录内编译。

> **写作提示词与模板解耦**：口径全部在 `references/knowledge/10-chapter-writing-prompts.md`（17 节，按「章」组织，不绑定文件名），`default/` 的 `main.tex` 顶部另有一份 6 条写作提示。用 `mcm` 走英文链条（见 `knowledge/10` 的【英文链条】），用 `huaweibei` 按它自己的 `sections/` 顺序；**章节名不同不影响读哪一节**，映射见下表。

### 2. 章节骨架

```text
paper/
├── main.tex                 标题页 + \abstractcn{摘要}{关键词} + \tocpage + 页眉页脚
│                            + \fig{宽}{路径}{图题}{label} / \tabcaption{题}{label}{列格式}{表头}{表体}
├── references.tex           \bibitem 条目（\referencescn 引出）
└── sections/
    ├── 1_restatement.tex    一、问题重述（背景 + 总体思路）
    ├── 2_assumptions.tex    二、模型假设
    ├── 3_symbols.tex        三、符号说明（longtable 两列）
    ├── 4_problem1.tex       四、问题一（\subsection 分「分析/准备/建立/求解」）
    ├── 5_problem2.tex       五、问题二
    ├── 6_problem3.tex       六、问题三（问数不足就删文件并改 main.tex 的 \input）
    ├── 7_sensitivity.tex    七、模型检验（误差 + 灵敏度）
    ├── 8_evaluation.tex     八、模型评价与推广
    └── A_code.tex           附录 A 核心代码（\appendixcn 引出）
```

问数 >3 时照 `4_problem1.tex` 复制 `7_problem4.tex` 并在 `main.tex` 里加 `\input`；问内固定四小节「具体分析 → 模型准备 → 模型建立 → 模型求解」。

用 MCM / 华为杯 / 用户自带模板时，骨架按该模板 `sections/` 的既有文件走，不套 `default` 的文件名。

**`knowledge/10` 与 `default/sections` 的映射**（提示词按左列读，内容按右列写）：

| knowledge/10 的节 | 写到哪 |
|---|---|
| 0 · 摘要 | `main.tex` 的 `\abstractcn{}{}` |
| 1 · 引言 | `1_restatement.tex` 前半（背景 + 意义） |
| 2 · 总体分析 | `1_restatement.tex` 后半（总体思路/技术路线），不单列一章 |
| 3 · 模型假设 | `2_assumptions.tex` |
| 4 · 符号说明 | `3_symbols.tex` |
| 5 / 5.1 / 5.1.1–5.1.4 · 主体与逐问 | `4_problem1.tex` / `5_problem2.tex` / `6_problem3.tex`，问内 `\subsection` 对应「具体分析 → 模型准备 → 模型建立 → 模型求解」 |
| 6 · 模型检验 | `7_sensitivity.tex` |
| 7 · 模型评价 + 8 · 改进推广 | `8_evaluation.tex` |
| 9 · AI 说明 | 赛题要求时在 `8_evaluation.tex` 末尾加 `\section*{AI 工具使用声明}` |
| 10 · 参考文献 | `references.tex`（`\bibitem`）+ 正文 `\cite` |
| 11 · 附录 | `sections/A_code.tex` |

### 3. 逐章写作（先读提示词，再动笔）

对每一章：

1. 读 `references/knowledge/10-chapter-writing-prompts.md` 里该章那一节（按 §2 的映射表找到对应文件）；
2. 按提示词给定的结构、句式、字数、表格列宽写；
3. 写完对着该节里的硬性项（【禁止】【格式】【列宽】【caption/label】等，各节标签不完全相同，凡带【】的约束都逐条过）；
4. 数值从 `results.json` 取，图号表号按插入顺序。

**顺序**：先写主体（问题一/二/三）→ 模型检验 → 评价与推广 → 问题重述+总体思路 → 假设 → 符号 → **最后写摘要**（摘要必须在全文完成后提炼，且写满一页不溢出）。参考文献与附录随写随补。

### 4. 图表插入

**数值表一律引生成物，不要手写。** 表骨架在 S1 就写好了（`reports/tables/*.tpl.md`），S2 用 `fill_tables.py` 渲染成 `results/tables/*.tex`，这里只 `\input`：

```latex
\input{../results/tables/q2_index.tex}     % 表题/标签/toprule 都在里面

如表~\ref{tab:q2_index}，双通道把 $I_h$ 从 217.96 压到 5.11，降幅 97.66\%。
```

- 想改表：改 `reports/tables/*.tpl.md` 后重跑 `fill_tables.py`，**不要改 `results/tables/*.tex`**（下次 `--check` 会判过期）；
- 模板里还没有骨架、又临时需要一张表？先补骨架（哪怕三行），再渲染——手打的那张表以后一定会和结果对不上；
- 跨页长表（符号表、参数表）仍走手写 `longtable`，但表里的数照样从 `results.json` 取。

`default` 模板自带两个排版宏，图与手写表直接调用，不要另写 `figure`/`table` 环境：

```latex
\fig{0.75}{../figures/data_q1_fit.png}{问题一模型输出与实测位移对比}{fig:q1_fit}
\tabcaption{符号说明}{tab:symbols}{>{\centering\arraybackslash}p{0.18\textwidth}>{\raggedright\arraybackslash}p{0.78\textwidth}}{符号 & 说明}{$x_1$ & 固定酸度（g/L）}
```

`\fig` 参数：宽（相对 `\textwidth`）、图片路径、图题、`label`；`\tabcaption` 参数：表题、`label`、列格式、表头、表体（内部是 `tabular`，**不跨页**）。跨页长表（符号表、参数表、结果表）改手写环境：

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

- **图片路径按 `main.tex` 所在目录解析**（xelatex 在 `paper/` 下跑）：图片写 `../figures/xxx.png`。这条只针对 LaTeX；Python 脚本里禁止 `../figures/`（见 `11-engineering-contract.md`）。
- **宽度按宽高比档位**：宽高比 ≥0.9（竖图）用 `0.55~0.65\textwidth`；0.6~0.9 用 `0.60~0.70`；<0.6（宽幅）用 `0.65~0.75`；并排两张各 `0.45~0.50`。只给 `width=`，不要只给 `height=`。
- **跨页表一律 `longtable` + 定宽列**，首尾加 `@{}` 后列宽总和 = `1.04 − 0.04×N`（N 为列数），表头列名不加粗，必须带 `\caption`（小表用 `\tabcaption`，见上）：

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
- 用 MCM / 华为杯 / 用户自带模板时，按该模板 `main.tex` 顶部的写法来（有 `\fig` 之类 helper 就用它），**不要混用两套写法**。

### 5. 数值与一致性核账

- 每个数字都能指到 `results.json` 的键；不允许「论文阶段重新估算」或换一套四舍五入。
- 同一指标在摘要、正文、检验节、模型评价四处必须同值同口径（`13-writing-injection.md` 第一节第 4/6 条）。
- 实验预算（样本量、种子、重复次数、超参数）全文只有一套。
- 正文不出现 `reports/`、`code/`、`results.json`、`plan.md`、`manifest.json` 等内部名字。
- 图必须被正文引用并解读；连续三张以上图表中间必须有文字。
- **机器校验**（别靠眼看）——先确认表是新的，再查正文数字：

  ```bash
  python <skill-root>/scripts/fill_tables.py  --project 项目1 --check   # 表与 results.json 一致（退出码 0）
  python <skill-root>/scripts/check_results.py --project 项目1          # 键覆盖/未申报键（退出码 0）
  python <skill-root>/scripts/check_paper.py   --project 项目1          # 正文七项（退出码 0）
  ```

  七项都要退出码 0：① 正文每个数字都能在 `results.json` 里找到同值（四舍五入、百分比、kN 换算都算命中）；命中不了的，要么是常数/派生量 → 写进 `results/numbers_allow.txt` 并注明来源，要么是凭记忆写的 → 改掉。② `references.tex` 的 `\bibitem` 键与正文 `\cite` 一一对应，且不能是 `enumerate` 手写条目（手写等于没有引用）。③ 符号说明独立成章且排在模型章之前，表里符号要在正文出现过。④ 必产文件齐全、`SCORE_MAP.md` 落点列填满——**落点写法**：`\ref{key}`（key 必须真在全文 `\label` 里）或 `图 N / 表 N / 式(N) / §N`（N 不超过论文里实际的图/表/公式/节数）。⑤ 正文无内部文件名与占位符（会先做宏展开与 `%` 续行拼接）。⑥ 正文 `\includegraphics` 的图都登记在 `figures/manifest.json`，且 `id` 与文件名一致、`outputs` 里的文件真实可打开。⑦ **百分号一律写 `\%`**：正文里写 `35.7 %` 会被 LaTeX 当注释，吞掉整行后半句，而编译仍是 0 error / 0 Overfull、数字检查也照样通过——这是唯一一类"门禁全绿、论文却是残句"的缺陷，只能靠这一项机器检查兜住。

  注意 `check_paper.py` 管不到"表里的数是不是旧的"——那一项由 `fill_tables.py --check` 负责：它拿当前 `results.json` 重渲染一遍，与磁盘逐字比对；两条命令都要跑。

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
