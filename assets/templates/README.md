# 模板总览（assets/templates/）

本目录是技能自带的全部模板/母版。**论文模板 5 套 + Word 一套 + 四类图件母版**，全部在本机实测编译/渲染通过（2.3.17，2026-11-04，MiKTeX + xelatex）。

## 一、论文模板（LaTeX，`assets/templates/latex/`）

| 目录 | 文档类 / 引擎 | 文件 | 空白首编 | 适用场景 |
|---|---|---|---|---|
| `workshop/` | `format`（自定义 cls）+ xelatex | 23（17 章 + `main.tex` + `format.cls` + 3 字体 + README） | **10 页** / 0 error / 0 Overfull / 2 处占位引用 | **默认**：国赛、省赛、校赛、课程论文，无赛事特殊要求时一律用它 |
| `cumcmthesis/` | `cumcmthesis`（v2.9）+ `cumcm2026.sty` | 4（`main.tex` 单文件装正文） | 4 页 / 0 error / 0 Overfull | CUMCM 官方格式，要官方封面、编号页、**AI 工具使用声明**宏 |
| `mcm/` | `article` + `fontspec`（英文） | 12（`main.tex` + `summary.tex` + `references.tex` + `sections/` 9 篇） | 11 页 / 0 error / 0 Overfull | MCM/ICM 与英文赛事：Summary Sheet + 8 章英文链条 |
| `huaweibei/` | `ctexart` + `fontset=windows` | 14（`main.tex` + `logo.pdf` + `title.pdf` + `sections/` 9 篇 + `references.tex`） | 10 页 / 0 error / 0 Overfull | 华为杯（研究生数学建模），封面四枚主办方 logo 已内置 |
| `default/` | `ctexart` + `fontset=windows` | 11（`main.tex` + `sections/` 8 篇 + `references.tex`） | 8 页 / 0 error / 0 Overfull | 通用中文结构，赛制无格式要求时的最小骨架 |

### workshop（默认）

- 章节顺序 = 文件名 = `main.tex` 里 `\input` 顺序：摘要 → 引言 → 总体分析 → 模型假设 → 符号说明 → 模型的建立与求解（`5.1.*` 四小节）→ 模型检验 → 模型评价 → 改进推广 → AI 说明 → 参考文献 → 附录。
- 每个章节文件末尾带 `% 【本章节写作提示词】`，`main.tex` 顶部带 `% 【全文写作总则】` 与 `% 【全文语言规范与去 AI 味】`；可检索副本在 `references/knowledge/10-chapter-writing-prompts.md`（由 `scripts/build_prompts.py` 从模板重建）。
- `format.cls` 从 `./fonts/` 取思源宋体（正文）与隶书（封面/标题），**`fonts/` 必须与 `main.tex` 同级**，否则 `File 'SourceHanSerifCN-Regular.otf' not found`。
- 内置 TikZ：`2.总体分析.tex` 的分工图（1 根 → N 问 → 每问等长步骤），改 `\rows` 即可，不要重画；`5.1.1.具体分析.tex` 另有一张分析流程 TikZ。
- 目录默认关闭（`withoutpreface`），需要时取消 `0.摘要.tex` 后 `\tableofcontents` 的注释。

### cumcmthesis

- `cumcmthesis.cls` 为上游 v2.9 快照（来源见 `VENDORED.md`），`cumcm2026.sty` 补 2026 赛季要求的 AI 声明。
- 正文全写在 `main.tex` 一个文件里，**没有 `sections/`**：因此没有逐章写作提示词，按 `references/knowledge/10` 的【英文链条】外的中文结构自行分章（`stages/04-writing.md` §1 已注明）。
- 电子版提交用 `\documentclass[withoutpreface,bwprint]{cumcmthesis}`；要封面去掉 `withoutpreface`。

### mcm

- 英文链路：`summary.tex`（Summary Sheet）→ 1 Introduction → 2 Assumptions → 3 Notation → 4 Model Design → 5 Solution → 6 Sensitivity → 7 Strengths and Weaknesses → 8 Conclusions → `A_code.tex`。
- `\SummaryText` 用 `\input{summary}` 装载（2.3.16 修过：宏不是 `\long`，摘要里一分段就报错且日志不指向摘要）。

### huaweibei / default

- 两者都是 `ctexart`，靠 `\ctexset` + `titlesec` + `tocloft` 调中文标题与目录样式；`fontset=windows` 走系统字体（宋体/黑体/楷体）。
- 华为杯多两个 PDF 资源（`logo.pdf` 四枚主办方标识、`title.pdf` 赛事名称艺术字），封面页由它们拼装。
- 章节文件名用英文（`1_restatement` … `A_code`），与 `check_paper.py` 的 `is_notation` / `is_model` 判据兼容（`4_symbols` / `5_problem1` 能被识别）。

## 二、Word 模板（`assets/templates/docx/`）

| 文件 | 作用 |
|---|---|
| `reference.docx` | 样式源（页面、正文宋体、标题层级、页脚），`report_kit.py` 以它为底 |
| `report_kit.py` | 排版工具箱：`cover()` / `toc()`（目录域）/ `h1..h3` / `p` / `fig` / `csv_table` / `eq` / `callout` / `save()`（自动置 `updateFields`） |
| `README.md` | 用法与字段说明 |

Word 原生分支（赛题强制 Word 时）用它生成 `report/数据分析报告.docx`，不经过 LaTeX；LaTeX 模式要改稿副本才用 `scripts/latex2docx.py`。

## 三、图件母版（四路）

| 路线 | 母版位置 | 数量 | 用法 |
|---|---|---|---|
| ① 数据图 | `tools/figure-templates/scripts/templates/` | 11 个 matplotlib 脚本 | `render_template.py --id <id>`，id 见 `references/figure-catalog.md`：多分类 SHAP 组合、配对云雨、CV-ROC 置信区间、Taylor、相关矩阵组合、预测边缘分布、RF-TPE 3D 曲面、分组相关+半边小提琴、分组环形热图、城市降温组合、Nature 和弦图 |
| ② 机理图 | `tools/mechanism-diagram/references/mechanism-templates.tex` | 12 类 TikZ 骨架 | 可行域、相平面/向量场、自由体受力、光路、几何推导（旗舰）、SEIR 仓室、控制体微元、马尔可夫状态转移、PINN 内部机理、指标层次、元胞自动机邻域、临界双态对比 |
| ③ 论文主图 | `assets/figures/reference/roadmap/src/` | 5 张实拍母版（jpg）+ `index.json` + `README.md` | `grouped-tasks` / `nested-cluster` / `quad-matrix` / `multi-panel` / `staged-steps`；选版式只看这 5 张，`select_reference.py --list` |
| ④A 流程图（TikZ） | `assets/figures/reference/flowchart/` | 8 套 JSON + 对应 PDF/PNG | `linear` / `decision` / `loop` / `pipeline` / `parallel` / `layered` / `algorithm` / `multi_question` |
| ④B 流程图（SVG） | `tools/flowchart/assets/flow_svg_template.svg` | 1 套骨架 | 判定 + 回边最小结构，改文字即用；`svg_flow.py` 转 HTML/PNG/PDF |

> 四路的路径与执行顺序以 `SKILL.md`「四路图件：路径 / 读取顺序 / 执行顺序」为唯一权威；本文件只回答“有哪些模板、各自适合什么”。

## 四、模板怎么选

1. 赛事有官方格式（CUMCM / MCM / 华为杯）→ 对应模板；
2. 国赛、省赛、校赛、课程论文 → `workshop`；
3. 只要一个能装中文的最小骨架 → `default`；
4. 赛题强制 Word → `assets/templates/docx/`（不碰 LaTeX）；
5. 图件永远先用母版改造，不从零画（母版的线型、间距、配色已过闸门）。
