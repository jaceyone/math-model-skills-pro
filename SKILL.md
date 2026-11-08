---
name: math-modeling-pro
description: 数学建模竞赛与项目工作流。用于“数学建模 / 建模比赛 / 数模论文 / 数学建模竞赛 / 建模分析 / 建模求解 / 结果键契约 / 数据表生成 / CUMCM / MCM / ICM / 画流程图 / 画机理图 / 技术路线图 / LaTeX 论文 / PDF 论文 / LaTeX 导出 Word / Word 数据分析报告 / 章节写作提示词 / 论文图片风格 / 得分点 / 论文搜索 / 论文评审 / 能拿多少分 / 怎么提分”等任务。主链路“先立结果键 → 写表格骨架 → 解题填数 → 出图 → 写文”，默认 LaTeX → PDF，默认模板为 default 中文论文模板（ctexart：摘要/目录/8 章/参考文献/附录，含 \fig/\tabcaption 排版宏）；赛题强制 Word 时走 Word 原生分支。内置数据图（plot_style 统一版式 + 出图闸门）、机理图、论文主图、流程图四路图件，S0–S4 阶段门禁、契约与数值单一事实源、得分点驱动验证与评委式评审。
---

# 数学建模 Pro v2.4.1

本技能把数学建模拆成 **5 个阶段 + 5 个门禁**。默认主链路 **LaTeX → PDF**（默认模板 `default`）；赛题强制 Word 时走 **Word 原生分支**，不经过 LaTeX。

## 铁律 0：契约先行（先写表 → 再解题 → 最后写文）

**顺序是「表格 → 数值 → 图 → 论文」，不是「跑出数来再想怎么摆」。** 一张表的列名、单位、行标签先定死，这道题要交什么就已经写清楚了；剩下的工作是把空格填上。

```
S1 ① results/schema.json       论文里每个数先在这里立键：label / unit / producer / consumers
S1 ② reports/tables/*.tpl.md   表格骨架：列名、单位、行标签先写，数值格只许留 {{key}}
S1 ③ 图件规划 reads:           每张数据图声明读哪些键
S2 ④ code/ 只产出 schema 里声明过的键（多出来的数要么申报，要么删）
S2 ⑤ fill_tables.py 把表填上 —— 人一格都不手抄
S3 ⑥ 数据图只画 results.json 里的键（reads 已在 ③ 声明）
S4 ⑦ 正文 \input 生成的表，数字与表同源
```

**为什么是这个顺序**：报告正文回答"用什么模型"，契约（schema + 表骨架）回答"要交哪几个数、每个数长什么样"。后者才是编码的施工图——先有它，代码不会算一堆没人要的中间量；先没它，只能等跑完再回头看哪个数好写进论文，那就是**用结果倒推模型**。

五条硬约束：

1. **没有 `results/schema.json` 就不许写模型代码。** 键名 = `results.json` 里的路径；每个键必须有含义、单位、生产者脚本、消费者（谁读它：哪张表/哪张图/论文哪一节）。没人读的键删掉。
2. **表里结果格只能是 `{{key}}`。** 手写数字的表会被 `check_contract.py` 判死；确属设计常数（题面给定参数）的列，在列头写 `*` 显式声明。
3. **代码只填契约键。** `check_results.py` 要能报"键覆盖 N/N、表已渲染、未申报键 0"；跑出新指标 → 先改 schema 再改代码（和"改模型先改报告"同一条纪律）。
4. **论文里的数值表一律 `\input{../results/tables/x.tex}`**，不手抄、不改数字；重跑代码后表自动跟着变。
5. **建模报告仍要 3 轮质检**（结构 → 一致性 → 可执行性），留痕 `reports/QC_S1_ROUND{.1,.2,.3}.md`；报告与契约互相兜底：报告里出现的指标必须在 schema 里有键，schema 里的键必须在报告里有定义。

机器判据（在技能根目录跑，退出码 0 才算过）：

```bash
python scripts/check_contract.py --project 项目N   # G1：键/表骨架/图件 reads/得分点/质检（2=契约未建立）
python scripts/fill_tables.py    --project 项目N   # S2：把表填上（--check 只校验不写盘）
python scripts/check_results.py  --project 项目N   # G2：键覆盖/生产者/表新鲜度/未申报键
python scripts/check_paper.py    --project 项目N   # G4：正文数字 ↔ results.json
```

## 二选一消除表（不留模糊选择，只留判据）

| 曾经可以"二选一" | 现在怎么定 |
|---|---|
| 先立结果键还是先跑代码 | **先立键**（`results/schema.json`）。没有键的代码只会在跑完之后逼你回忆"这个数叫什么" |
| 先写报告还是先跑代码 | **先报告 + 先契约**。代码只允许在 G1 之后写；"先跑个数出来再补报告"= 违规 |
| 表格手抄还是程序生成 | **生成**：`reports/tables/*.tpl.md` → `results/tables/*.tex` → 论文 `\input`。手抄表在 S4 必漂 |
| 键名怎么起 | **= `results.json` 里的路径**（`problem2.control_index`）。另起一套中文名到 S4 就对不上 |
| 总览图走 ③ 论文主图还是 ④B 总流程图 | **默认 ④B**（回答"题怎么解、任务怎么分组"，评委最先看）；只有需要展示**模型内部技术栈**（数据→模型→验证的层级流）时才加 ③，一张论文里两者各自最多一张，**不许互相替代** |
| 流程图走 ④B（SVG）还是 ④A（TikZ） | 判据只有一条：**步骤/判定/回边** → ④A；**任务分组/问题拆解** → ④B。两者都不许画成另一条路线的样子 |
| 机理图内写中文还是英文 | 不设二选一：**图内语言 = 论文语言**。英文稿 `MH_FIG_LANG=en`（去掉 ctex，可额外出 SVG）；中文稿 `zh` |
| 数据图的 `outputs` 登记哪些格式 | 固定登记 **pdf + png**；`.svg` 只作改图中间物，不进 manifest |
| 模板用哪套 | 由赛事决定：MCM/ICM→`mcm`，华为杯→`huaweibei`，其余→`default`。用户自带模板优先 |

## 快速开始

| 用户说 | 做什么 |
|---|---|
| “帮我做这道数模题” | 从 S0 启动，依次执行 S0 → S4（S1 内部顺序：拆题 → 立键 → 写表 → 才动模型） |
| “进行建模分析” | 只执行 S1（含契约三件套） |
| “先定数据表 / 得分点 / 要交哪些数” | 只做 S1 的契约部分：`results/schema.json` + `reports/tables/*.tpl.md` + 图件 `reads` |
| “进行代码实现” | 只执行 S2（先 `check_results.py` 确认契约，再填键） |
| “画技术路线图 / 框架图” | S3，路线 ③ `tools/paper-figure` |
| “画流程图” | S3，路线 ④ 先选路：总流程图/问题分析 → ④B `tools/flowchart/scripts/svg_flow.py`（SVG→HTML/PNG）；算法/判定 → ④A `tools/flowchart/scripts/flowchart.py`（JSON→TikZ） |
| “画可行域 / 相平面 / 受力图” | S3，路线 ② `tools/mechanism-diagram` |
| “写论文 / 编译 PDF” | S4 LaTeX 分支，默认 `assets/templates/latex/default/` |
| “这一章怎么写 / 摘要怎么写” | 读 `references/knowledge/10-chapter-writing-prompts.md` 对应节 |
| “写 Word 报告（赛题强制）” | S4 Word 分支，`report_kit.py` 产出 `report/数据分析报告.docx` |
| “导出 Word 改稿副本” | 仅 LaTeX 模式，运行 `scripts/latex2docx.py` |
| “评审论文 / 能拿多少分 / 怎么提分” | 可选，读 `tools/review/SKILL.md`，产出 `reports/REVIEW_REPORT.md` |

## 5 阶段

| 阶段 | 职责别名 | 输入 | 必须产出 | 门禁 | 下一阶段 |
|---|---|---|---|---|---|
| S0 启动 | 总控 | 题面、附件、偏好 | `plan.md`、`todo.md`、项目骨架 + 工程资产、环境报告 | G0 | S1 |
| S1 建模分析 | 建模手 | 题面、附件、`plan.md` | **`results/schema.json`（结果键清单）**、**`reports/tables/*.tpl.md`（表格骨架）**、`reports/ANALYSIS_MODELING_REPORT.md`（七件套 + 得分点表 + 证据链）、`symbols.md`、`图件规划.md`（含 `reads:`）、`SCORE_MAP.md`、代码任务清单 | **G1（`check_contract.py` 退出码 0）+ S1 质检 ≥3 轮** | S2 |
| S2 代码实现 | 编程手 | 契约（**已过 G1**）+ 分析报告 | `code/`（只产出声明过的键）、`results/results.json`、**`results/tables/*.md|.tex`（`fill_tables.py` 生成）**、`RESULTS_REPORT.md`、`journal_problemN.md`、数据图 + 出图闸门 | **G2（`check_results.py` 退出码 0）** | S3 |
| S3 图件制作 | 图件手 | 分析 + 结果 + 图件规划 | 机理图、论文主图、流程图、`FIGURE_REPORT.md`、`figures/manifest.json` | G3 | S4 |
| S4 论文撰写 | 论文手 | 全部报告 + 图 + 结果 | LaTeX：`paper/main.tex` + 各章 `.tex`（数值表用 `\input` 引生成物）+ `paper/main.pdf`；Word：`report/数据分析报告.docx` | **G4（`check_paper.py` + `fill_tables.py --check` 双双 0）** | 完成 |

阶段细节按需读取：

- `references/stages/00-start.md`
- `references/stages/01-analysis.md`
- `references/stages/02-coding.md`
- `references/stages/03-figures.md`
- `references/stages/04-writing.md`

## 默认资产（S0 一次性铺好）

| 资产 | 用途 | 铺到哪 |
|---|---|---|
| `assets/templates/latex/default/` | **默认论文模板**（`ctexart`）：`main.tex` 内含摘要宏、目录、页眉、`\fig`/`\tabcaption`；`sections/` 8 章 + `references.tex` + `A_code.tex` | `paper/` |
| `assets/style/plot_style.py` | 统一绘图版式（中文字体 + 期刊配色 + 组图 + 存图体检） | `code/` |
| `assets/style/check_figures.py` | 出图闸门，硬伤退出码 1 | 项目根 |
| `assets/scaffold/run_all.py` | 批量跑 `code/` 下脚本 | 项目根 |
| `assets/templates/docx/reference.docx` + `report_kit.py` | Word 报告模板与排版工具箱 | `report/` |

## 四路图件：路径 / 读取顺序 / 执行顺序

四路产物全部落在项目 `figures/`，前缀固定 `data_` / `mech_` / `paper_` / `flow_`。**前缀决定 manifest 的 `route`**（`scripts/make_manifest.py` 按前缀识别），前缀写错图就登记错路线。下表里 `<skill>` = 本技能根目录，`<项目>` = 当前项目根。

| # | 路线 | 驱动器 | 输入（读什么） | 中间产物 | 终产物 | 阶段 |
|---|---|---|---|---|---|---|
| ① | 数据图 | matplotlib + `assets/style/plot_style.py` | `code/outputs/*.csv`、`results/results.json`（键已在图件规划 `reads:` 声明） | `figures/data_*.png/.pdf` | 同左 + `figures/_figure_lint.json` | S2 |
| ② | 机理图 | `tools/mechanism-diagram`（TikZ） | 正文公式、题面几何、`reports/symbols.md` | `figures/mech_*.tex` | `figures/mech_*.pdf/.png` + `figures/mech_includes.tex` | S3 |
| ③ | 论文主图 | `tools/paper-figure`（SVG） | `assets/figures/reference/roadmap/` 5 张母版 | `figures/paper_*.svg` | `figures/paper_*.pdf/.png` | S3 |
| ④B | 总流程图（SVG） | `tools/flowchart/scripts/svg_flow.py` | `figures/flow_*.svg`（母版 `assets/figures/reference/totalflow/` 5 套：`quadrant`/`multi-panel`/`nested`/`pipeline-groups`/`five-steps`，可编辑源 `tools/flowchart/assets/totalflow/`） | `figures/flow_*.html` | `figures/flow_*.png/.pdf` | S3 |
| ④A | 算法流程（TikZ） | `tools/flowchart/scripts/flowchart.py` | `figures/flow_*.json`（`assets/figures/reference/flowchart/` 8 张母版改造） | `figures/flow_*.tex` | `figures/flow_*.pdf/.png` | S3 |

**边界判据**：有真实数据点/数值结果 → ①；价值在精确几何/公式刻度/符号 → ②；价值在“整体路线/框架一眼讲清” → ③；价值在“问题怎么分析、任务怎么分组”（总流程图）→ ④B；价值在“步骤、判断、循环、回边”（算法细节）→ ④A。
**禁止**：一种图跨两条路线重复生成；用 TikZ 画数据图；用 matplotlib 画流程图/路线图；把总流程图塞进 ③ `paper-figure` 或画成 TikZ 树；同一张流程图 ④A、④B 两路各出一份混着用。

### ① 数据图

- 读取顺序：`assets/style/plot_style.py`（S0 已复制进 `code/`）→ `references/knowledge/14-figure-contract.md` → 需要现成版式再读 `tools/figure-templates/SKILL.md`。
- 执行顺序：`apply()` → `save_publication(fig, <项目>/figures/data_x)` → `python check_figures.py`（硬伤 0 才算过）→ `read_image` 目检 → 登记 manifest。
- 不出 SVG、不写 TikZ。

### ② 机理图（TikZ，`.tex` 才是交付主体）

- **读取顺序（照这个顺序读，别跳步）**：
  1. `tools/mechanism-diagram/SKILL.md`（产出规格、配色铁律、编译链）
  2. `tools/mechanism-diagram/references/diagram-taxonomy.md`（§1 该不该由本件画、§2 六类模型→图型触发表、§3 数据红线）
  3. `tools/mechanism-diagram/references/tikz_rules.md`（配色专用规则、≤3 色、几何示意图自检 6 条）
  4. `tools/mechanism-diagram/references/mechanism-templates.tex`（12 个骨架，抄构造方式不抄坐标）
  5. 落笔写 `figures/mech_<图名>.tex`
- **执行顺序**（在项目根跑）：
  ```bash
  xelatex -interaction=nonstopmode -halt-on-error -output-directory=figures figures/mech_x.tex
  pdfcrop figures/mech_x.pdf figures/mech_x.pdf     # 可选：缺 perl 会报 script engine 错 → 跳过，standalone border=3pt 已紧裁
  pdftoppm -r 300 -png -singlefile figures/mech_x.pdf figures/mech_x
  grep -c "Overfull\|Underfull" figures/mech_x.log   # 必须为 0
  ```
- 产物：`figures/mech_<图名>.{tex,pdf,png}` + `figures/mech_includes.tex`（`\begin{figure}` 片段，`width=0.82\textwidth`，`\label` 每张唯一）。
- 只出 PDF + PNG：`ctex` 中文图出不了 SVG（`dvisvgm` 只吃纯英文 `latex` 产出的 dvi）。图内不写求解结果数值。

### ③ 论文主图（SVG）

- 读取顺序：`tools/paper-figure/SKILL.md` → `assets/figures/reference/roadmap/README.md`（骨架表 + 视觉规范）→ 对应母版 `assets/figures/reference/roadmap/src/*.jpg`。
- 执行顺序：`python tools/paper-figure/scripts/select_reference.py --list` 选版式 → 写 `figures/paper_<图名>.svg` → `python tools/paper-figure/scripts/render_figure.py figures/paper_x.svg`（Edge 无头渲染，默认出 `.png` + `.pdf`，`--html` 额外出预览页）。
- 环境变量：`MSEDGE` 指 Edge 可执行文件（留空自动探测），`PF_SCALE` 控 PNG 倍率。

### ④ 流程图：两条实现路线（总流程图走 SVG，算法细节走 TikZ）

| 判据 | B · SVG 路（**总流程图默认**） | A · TikZ 路（算法/判定细节） |
|---|---|---|
| 画什么 | 问题分析总流程、任务分组、总体思路、多面板总图 | 算法流程、判定分支、循环迭代、多阶段流水线 |
| 载体 | 手写/改 `.svg` → 可编辑 HTML → Edge 渲染 | JSON 规格 → 生成 `.tex` → xelatex |
| 适合 | 要交人改、要嵌 HTML/PPT、机器没 MiKTeX、要拖拽微调坐标 | 判定框 + 回边、要与正文公式字体一致、直接进 LaTeX |
| 改图方式 | 浏览器打开 `.html` 点字直改，或直接改 `.svg` | 改 `.json` 重跑脚本（**别手改生成的 `.tex`**） |
| 产物 | `flow_*.{svg,html,png,pdf}` | `flow_*.{json,tex,pdf,png}` |
| manifest | `route=flow`、`spec` 填 `.svg`、`source` 填 `tools/flowchart/scripts/svg_flow.py` | `route=flow`、`spec` 填 `.json`、`source` 填 `tools/flowchart/scripts/flowchart.py` |

**B · SVG 路（读取 → 执行）**：`tools/flowchart/SKILL.md` → **总流程图 5 套实例母版** `assets/figures/reference/totalflow/`（`quadrant`／`multi-panel`／`nested`／`pipeline-groups`／`five-steps`，实拍图 + 复刻 SVG + PNG）→ 复制 `tools/flowchart/assets/totalflow/tf_*.svg` 成 `figures/flow_<图名>.svg` → 改字 → 出图：

```bash
python tools/flowchart/scripts/svg_flow.py figures/flow_total.svg --html   # 生成可编辑页面
python tools/flowchart/scripts/svg_flow.py figures/flow_total.svg -s 3     # 3 倍 PNG + 矢量 PDF
python tools/flowchart/scripts/build_totalflow.py --png                    # 重生成 5 套母版
```

**A · TikZ 路（读取 → 执行）**：`tools/flowchart/SKILL.md` → `assets/figures/reference/flowchart/<母版>.json`（`linear` / `decision` / `loop` / `pipeline` / `parallel` / `layered` / `algorithm` / `multi_question`）→ 写 `figures/flow_<图名>.json` →

```bash
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json            # 出 tex+pdf+png（300 dpi）
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json --no-compile  # 只出 tex
```

SVG 本质是 XML：`figures/flow_total.html` 在浏览器里点文字即可改，改完点「下载 SVG」覆盖源文件，重跑脚本刷新 PNG/PDF；没有 Edge 时该 HTML 也可直接手工截图或交给浏览器「打印为 PDF」。`cairosvg` 若已安装则自动改走它转 PNG，不依赖浏览器。

### ④A 走向铁律：直来直去

TikZ 流程图**只许正交折线**：`--`（同一列/行直接连）、`-|`（先横后竖）、`|-`（先竖后横）、`-- ++(dx,0) |-`（让开再拐）。`tools/flowchart/scripts/flowchart.py` 已按此实现，改图时不要退回曲线：

- **禁止** `to[out=..,in=..]`、`bend left/right`、`looseness`、`controls` 等任何曲线写法——弧线在流程图里既难读又容易压住别的框。
- **回边**只从外侧走（TB 从东/西侧 `-- ++(0.9,0) |-`，LR 从南/北侧 `-- ++(0,-0.9) -|`），不许从框内穿过，不许横穿节点。
- **判定框的两个分支**不许都从 `south` 出：左分支走 `(d.west) -|`，右分支走 `(d.east) -|`。
- **验收**：编译后在 PNG 上目检「全是直角、无曲线、无斜线穿框、箭头落在框边上」，四条都过才算完；发现曲线说明 spec 里写了个非法 route 字段，改 spec 不改脚本。

**选路一句话**：讲「全文怎么分析、任务怎么分组」的总流程图 → B（SVG，母版 5 套）；讲「这个算法怎么跑、判定什么、什么时候回边」的细节 → A（TikZ，母版 8 套，正交布线）。**几何/物理机理**（可行域、受力、光路）不在这两路，走 ② `mechanism-diagram`。

## 项目骨架

```text
项目N/
├── plan.md
├── todo.md
├── input/
├── reports/
│   ├── ANALYSIS_MODELING_REPORT.md
│   ├── symbols.md
│   ├── SCORE_MAP.md
│   ├── 图件规划.md            # 数据图行必须带 reads: 键清单
│   ├── tables/                # 表格骨架（S1 写，只留 {{key}}），如 q2_index.tpl.md
│   ├── RESULTS_REPORT.md
│   ├── journal_problem1.md …
│   └── FIGURE_REPORT.md
├── code/
│   ├── problem1.py …  utils.py
│   ├── plot_style.py
│   └── outputs/
├── check_figures.py
├── run_all.py
├── results/
│   ├── schema.json            # 契约：结果键清单（S1 先立，代码照着填）
│   ├── results.json           # 事实：键 → 值
│   ├── numbers_allow.txt
│   ├── tables/                # 生成物：*.md / *.tex（论文 \input）+ _render.json
│   └── logs/
├── figures/
│   ├── data_*.pdf/.png
│   ├── mech_*.tex/.pdf/.png
│   ├── paper_*.svg/.pdf/.png
│   ├── flow_*.json/.tex/.pdf/.png      # ④A TikZ 路
│   ├── flow_*.svg/.html/.png/.pdf      # ④B SVG 路
│   ├── _figure_lint.json
│   └── manifest.json
└── paper/                      # LaTeX 模式（Word 模式换成 report/）
    ├── main.tex                # 标题页 + 摘要宏 + 目录 + 页眉 + \fig/\tabcaption
    ├── references.tex
    └── sections/1_restatement … 8_evaluation + A_code.tex
```

契约：

- `references/contracts/pipeline.md`（**全流程串联：产物 → 生产者 → 消费者 → 门禁**）
- `references/contracts/project-layout.md`
- `references/contracts/results-schema.md`（`schema.json` 先立键 → `results.json` 填值）
- `references/contracts/table-template.md`（表格骨架写法 + `fill_tables.py` + 论文 `\input`）
- `references/contracts/figure-manifest.md`

## 门禁

| 门禁 | 一句话 |
|---|---|
| G0 启动 | 赛事/语言/子问题数已定（可默认 + 写假设），`plan.md`/`todo.md` 存在，工程资产已铺，`results/schema.json` 空壳与 `reports/tables/` 已建，环境检查完成 |
| G1 契约 + 建模 + 质检 | **`check_contract.py` 退出码 0**：schema 键齐全（label/unit/producer/consumers）、表骨架无手写数值、数据图声明 `reads`、得分点可锚定；七件套齐全；**建模报告跑满 3 轮质检并留痕**——不过不许进 S2 |
| G2 结果 | **`check_results.py` 退出码 0**：契约键全填、生产者存在、`figure:data_*` 已出图、`results/tables/*` 已渲染且不落后于 `results.json`、未申报键已说明；代码从头跑通、约束校验通过、种子固定；出图闸门 0 硬伤；得分点逐条核账 |
| G3 图件 | 四路不混用，每图有来源，数据图过闸门 + 目检，机理图/流程图编译 0 error，manifest 完整 |
| G4 论文 | 章节齐全、逐章对照写作提示词自查，**数值表为 `\input{../results/tables/*.tex}` 生成物**，正文数值来自 `results.json`，`check_paper.py` 与 `fill_tables.py --check` 双双退出码 0，无占位符/内部文件名，AI 声明已填 |

清单：`references/checklists/G0-start.md` … `G4-writing.md`。

## LaTeX 模板

| 场景 | 模板 | 文件数 | 空白首编实测 |
|---|---|---|---|
| **默认**（国赛/省赛/校赛/课程论文，无特殊要求） | `assets/templates/latex/default/`（`ctexart`：摘要/目录/8 章/参考文献/附录，`\fig`/`\tabcaption` 现成） | 11 | 8 页 / 0 error / 0 Overfull |
| MCM/ICM（英文） | `assets/templates/latex/mcm/`（Summary Sheet + 8 章英文链条） | 12 | 11 页 / 0 error / 0 Overfull |
| 华为杯 | `assets/templates/latex/huaweibei/`（封面 logo/title PDF 内置） | 14 | 10 页 / 0 error / 0 Overfull |

模板清单、每套的文件/章节结构、Word 模板与四路图件母版（数据图 11 / 机理 12 / 主图 5 / 流程图 8+1）见 **`assets/templates/README.md`**；选模板先看那张总览表，再看这里的场景列。

编译与 Word 分支的细节见 `references/stages/04-writing.md`（xelatex 两遍、图片路径相对 `main.tex`、Word 原生分支不经过 LaTeX）。禁止用 Typst。

## 关键规则

0. **契约先行**：`results/schema.json`（结果键）+ `reports/tables/*.tpl.md`（表骨架）+ 图件 `reads` 三件套没立、`check_contract.py` 不是 0 之前，不许写模型代码、不许出数据图、不许进 S3/S4。报告与契约是唯一口径；S2/S4 期间要改模型，先改报告与 schema 再改代码再重跑质检。
1. **数值单一事实源**：论文中的关键数值只能来自 `results/results.json`，且必须先作为键写进 `results/schema.json`；不得凭记忆写数。
2. **表格是生成物**：论文里的数值表一律 `\input{../results/tables/*.tex}`，由 `scripts/fill_tables.py` 从 `results.json` 渲染；手抄表等于给自己埋一个 S4 才会爆的雷。
3. **图件单一来源**：正文只引用 `figures/manifest.json` 中登记的图；数据图只读图件规划 `reads:` 里声明过的键。
4. **权威版本按交付形态定**：LaTeX 模式以 PDF 为准，Word 只作改稿副本；Word 模式以 DOCX 为准，PDF 只作预览。
5. **不编造文献**：`paper/references.tex` 用 `thebibliography` + `\bibitem{key}`，正文用 `\cite{key}`，键与条目一一对应、条目带完整出版信息；`scripts/check_paper.py` 机器校验，不通过的参考文献等于装饰。
6. **不泄露内部文件名**：论文正文不得出现 `reports/`、`code/`、`results.json`、`plan.md`。
7. **AI 声明**：赛题要求 AI 使用声明时按赛事口径写（模板无对应宏就用无编号小节 + 一句话声明），不得留空。
8. **先门禁后推进**：上一阶段不达标，不进入下一阶段；门禁能机器判的就不靠自觉，四条命令各自退出码 0 才算过。
9. **评审提分**：终稿前跑 `tools/review`，先修 P0/P1，再修格式与摘要；评分只作定位，不承诺获奖。
10. **无人值守**：不中途提问、不停在方案阶段；歧义取保守可验证解释并写进 `plan.md` 假设段（`references/knowledge/11-engineering-contract.md`）。
11. **前台执行**：跑实验/装库/自检一律前台，不后台、不 sleep 轮询；长计算分阶段落盘，缓存不作废。
12. **逐章照提示词**：写哪一章先读 `references/knowledge/10-chapter-writing-prompts.md` 对应节，硬约束逐条自查。
13. **得分点驱动**：S1 立可核验得分点（每条挂 schema 键或图表号）→ S2 逐条核账补证据 → S4 正文逐条落到公式号/图号/表号（`12-scoring-validation.md`）。
14. **产物闭环**：每个产物必须有消费者、每个输入必须有生产者；新增报告先登记 `references/contracts/pipeline.md` 的闭环表，登记不上就不写；schema 里没人读的键直接删。

## 知识库索引

| 什么时候读 | 文件 |
|---|---|
| 逐章写作（摘要/引言/建模/检验/评价/附录） | `references/knowledge/10-chapter-writing-prompts.md` |
| 执行纪律、路径、编码与版本坑 | `references/knowledge/11-engineering-contract.md` |
| 得分点、证据链、验证强度、学术分寸 | `references/knowledge/12-scoring-validation.md` |
| 摘要句链、推导三段式、一致性、表格、统计、引用 | `references/knowledge/13-writing-injection.md` |
| 数据图版式、防乱码、出图闸门、plot_style API | `references/knowledge/14-figure-contract.md` |
| 题面拆解 / 选型 / 题型防错 / 图种 / 写作底线 / 评审 | `references/knowledge/01`–`06`、`10`–`14`（见 `00-index.md`；`07`–`09` 已随模板移除，编号不重排） |

## 工具索引

| 工具 | 用途 |
|---|---|
| `tools/doctor` | 环境检查 |
| `tools/pdf` | 读题面 PDF |
| `tools/xlsx` | 读/写数据表 |
| `tools/paper-search` | Crossref + arXiv 论文搜索 |
| `tools/mechanism-diagram` | 机理图（TikZ） |
| `tools/paper-figure` | 路线图/框架图（SVG → PDF/PNG） |
| `tools/flowchart` | 流程图：A 路 `tools/flowchart/scripts/flowchart.py`（JSON → TikZ → PDF/PNG）、B 路 `tools/flowchart/scripts/svg_flow.py`（SVG → 可编辑 HTML → PNG/PDF） |
| `tools/figure-templates` | 11 个科研数据图模板 |
| `tools/review` | 评委式评审：100 分评分、格式系数、P0–P3 问题、提分建议 |

## 脚本索引

> 脚本路径相对于技能根目录；在项目目录运行时用 `python <skill-root>/scripts/xxx.py --project 项目N`。

| 脚本 | 用途 |
|---|---|
| `scripts/doctor.py` | 环境检查（xelatex 必选；pandoc / pdftoppm 可选） |
| `scripts/check_contract.py` | **G1 契约门禁**：`results/schema.json` 键完整性、表骨架无手写数值/无未声明键、数据图 `reads`、得分点可锚定、QC 三轮 PASS（退出码 0=PASS / 1=FAIL / 2=契约未建立） |
| `scripts/fill_tables.py` | **表格渲染**：`reports/tables/*.tpl.md` + `results.json` → `results/tables/*.md|.tex`（`--check` 只校验是否最新，G2/G4 用） |
| `scripts/check_results.py` | **G2 结果门禁**：契约键覆盖、生产者存在、`figure:data_*` 已出图、表未过期、未申报键清单（`--strict` 把未申报键升级为失败） |
| `scripts/build_paper.py` | xelatex 编译 + PDF 页检查（退出码 0=PASS / 1=FAIL / 2=WARN） |
| `scripts/check_paper.py` | 论文自检 7 项：数字↔`results.json`、文献↔`\cite`、章节结构（符号说明独立且前置）、产物闭环（含 SCORE_MAP 落点；`\label` 与表数把 `results/tables/*.tex` 一并算入）、内部文件名、图件↔`manifest.json`、满载百分号转义（正文写 `35.7 %` 会被注释吞掉整行后半句，编译却是 0 error）（G4 前必跑，退出码 0 才算过） |
| `scripts/check_links.py` | 文档链接体检：扫现役 md 里的技能内部路径（`--all` 连 `CHANGELOG.md` 历史条目一起查，历史失联属预期） |
| `scripts/latex2docx.py` | LaTeX → Word 旁路导出 |
| `scripts/make_manifest.py` | 扫描 `figures/` 生成 manifest（自动从 `paper/` 抓 caption/section；`flow_*` 按实存的 `.svg`/`.json` 推断 `spec`） |
| `tools/flowchart/scripts/svg_flow.py` | 流程图 B 路：`--html`（可编辑页）/ `--png` / `--pdf`，Edge 无头渲染，`cairosvg` 可选 |

## 兼容别名

旧说法仍可用，但统一路由到新阶段：

- “进行建模分析” → S1
- “进行代码实现” → S2
- “进行论文撰写” → S3 → S4
- “建模手 / 编程手 / 论文手” → 仅作沟通别名，不单独建角色文件

## 不做什么

- 不做 Typst；
- 不做 17 套模板全量引入；
- 不做 docx 主模板（Word 仅原生分支）；
- 不强制 drawio；
- 不把 1381 张图库放进主包；
- 不做自动验收与提交打包，不生成提交用压缩包；
- 不做后端/前端/Docker/RAG/HIL。
