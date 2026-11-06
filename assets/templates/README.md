# 模板总览（assets/templates/）

本目录是技能自带的全部模板/母版：**论文模板 3 套 + Word 一套 + 四类图件母版（含 5 套总流程图实例）**，全部在本机实测编译/渲染通过（2.3.18，2026-11-04，MiKTeX + xelatex）。

> 2.3.18 起 **`workshop/` 与 `cumcmthesis/` 已按用户要求移出本包**，默认模板改为 `default/`；写作提示词不随模板走，统一在 `references/knowledge/10-chapter-writing-prompts.md`。

## 一、论文模板（LaTeX，`assets/templates/latex/`）

| 目录 | 文档类 / 引擎 | 文件 | 空白首编 | 适用场景 |
|---|---|---|---|---|
| `default/` | `ctexart` + `fontset=windows` + xelatex | 11（`main.tex` + `sections/` 8 篇 + `references.tex` + `A_code.tex`） | **8 页** / 0 error / 0 Overfull | **默认**：国赛、省赛、校赛、课程论文，无赛事特殊要求时一律用它 |
| `mcm/` | `article` + `fontspec`（英文） | 12（`main.tex` + `summary.tex` + `references.tex` + `sections/` 9 篇） | 11 页 / 0 error / 0 Overfull | MCM/ICM 与英文赛事：Summary Sheet + 8 章英文链条 |
| `huaweibei/` | `ctexart` + `fontset=windows` | 14（`main.tex` + `logo.pdf` + `title.pdf` + `sections/` 9 篇 + `references.tex`） | 10 页 / 0 error / 0 Overfull | 华为杯（研究生数学建模），封面四枚主办方 logo 已内置 |

### default（默认）

- `main.tex` 一次装好：标题页（`\papertitle`）→ 摘要与关键词（`\abstractcn{摘要}{关键词}`）→ 目录（`\tocpage`）→ 8 章 → 参考文献（`\referencescn`）→ 附录（`\appendixcn`）。
- 现成排版宏：`\fig{宽}{路径}{图题}{label}`、`\tabcaption{表题}{label}{列格式}{表头}{表体}`（内部 `tabular`，不跨页）、`\threelinetable`；跨页长表手写 `longtable`。
- 章节文件：`1_restatement` / `2_assumptions` / `3_symbols` / `4_problem1` / `5_problem2` / `6_problem3` / `7_sensitivity` / `8_evaluation` / `A_code`；问数不足就删文件并改 `main.tex` 的 `\input`，问数多于 3 就照 `4_problem1.tex` 复制。
- 顶部带 6 条写作提示（复制到 `paper/`、摘要写数值、`\fig`/`\tabcaption` 用法、图表后 ≥100 字分析、xelatex 两遍、别重复加载宏包）。
- 字体走系统（宋体/黑体/楷体 + Times New Roman），不依赖模板自带字体，所以只有 10 KB 量级。

### mcm

- 英文链路：`summary.tex`（Summary Sheet）→ 1 Introduction → 2 Assumptions → 3 Notation → 4 Model Design → 5 Solution → 6 Sensitivity → 7 Strengths and Weaknesses → 8 Conclusions → `A_code.tex`。
- `\SummaryText` 用 `\input{summary}` 装载（2.3.16 修过：宏不是 `\long`，摘要里一分段就报错且日志不指向摘要）。

### huaweibei

- `ctexart` + `\ctexset` + `titlesec` + `tocloft` 调中文标题与目录；`fontset=windows` 走系统字体。
- 两个 PDF 资源：`logo.pdf`（四枚主办方标识）、`title.pdf`（赛事名称艺术字），封面页由它们拼装。
- 章节文件名英文（`1_restatement` … `9_evaluation` + `A_code`），与 `check_paper.py` 的 `is_notation` / `is_model` 判据兼容（`4_symbols` / `5_problem1` 能被识别）。

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
| ① 数据图 | `tools/figure-templates/scripts/templates/` | 11 个 matplotlib 脚本 | `render_template.py --id <id>`，id 见 `tools/figure-templates/references/figure-catalog.md`：多分类 SHAP 组合、配对云雨、CV-ROC 置信区间、Taylor、相关矩阵组合、预测边缘分布、RF-TPE 3D 曲面、分组相关+半边小提琴、分组环形热图、城市降温组合、Nature 和弦图 |
| ② 机理图 | `tools/mechanism-diagram/references/mechanism-templates.tex` | 12 类 TikZ 骨架 | 可行域、相平面/向量场、自由体受力、光路、几何推导（旗舰）、SEIR 仓室、控制体微元、马尔可夫状态转移、PINN 内部机理、指标层次、元胞自动机邻域、临界双态对比 |
| ③ 论文主图 | `assets/figures/reference/roadmap/src/` | 5 张实拍母版（jpg）+ `index.json` + `README.md` | `grouped-tasks` / `nested-cluster` / `quad-matrix` / `multi-panel` / `staged-steps`；`select_reference.py --list` |
| ④A 流程图（TikZ） | `assets/figures/reference/flowchart/` | 8 套 JSON + 对应 PDF/PNG | `linear` / `decision` / `loop` / `pipeline` / `parallel` / `layered` / `algorithm` / `multi_question` |
| ④B 总流程图（SVG） | `assets/figures/reference/totalflow/`（实拍 + 复刻 PNG）、`tools/flowchart/assets/totalflow/`（可编辑 SVG） | **5 套 + 1 骨架** | 任务分组 / 多面板 / 议题嵌套 / 左入右出 / 五步骤；`tools/flowchart/scripts/svg_flow.py` 出 HTML/PNG/PDF，`tools/flowchart/scripts/build_totalflow.py` 可重生 |

> 四路的路径与执行顺序以 `SKILL.md`「四路图件：路径 / 读取顺序 / 执行顺序」为唯一权威；本文件只回答“有哪些模板、各自适合什么”。

## 四、模板怎么选

1. 用户自带模板 → 先用用户的（整目录复制到 `paper/`，按它的宏写）；
2. 赛事有官方格式（MCM/ICM、华为杯）→ 对应模板；
3. 国赛、省赛、校赛、课程论文 → `default`；
4. 赛题强制 Word → `assets/templates/docx/`（不碰 LaTeX）；
5. 图件永远先用母版改造，不从零画（母版的线型、间距、配色已过闸门）。
