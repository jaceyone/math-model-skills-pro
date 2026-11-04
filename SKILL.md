---
name: math-modeling-pro
description: 数学建模竞赛与项目工作流。用于“数学建模 / 建模比赛 / 数模论文 / 数学建模竞赛 / 建模分析 / 建模求解 / CUMCM / MCM / ICM / 画流程图 / 画机理图 / 技术路线图 / LaTeX 论文 / PDF 论文 / LaTeX 导出 Word / Word 数据分析报告 / 章节写作提示词 / 论文图片风格 / 得分点 / 论文搜索 / 论文评审 / 能拿多少分 / 怎么提分”等任务。主链路默认 LaTeX → PDF，默认模板为 workshop 论文模板（17 章逐章写作提示词 + main.tex 全文写作总则）；赛题强制 Word 时走 Word 原生分支。内置数据图（plot_style 统一版式 + 出图闸门）、机理图、论文主图、流程图四路图件，S0–S4 阶段门禁、得分点驱动验证与评委式评审。
---

# 数学建模 Pro v2.3.17

本技能把数学建模拆成 **5 个阶段 + 5 个门禁**。默认主链路 **LaTeX → PDF**（默认模板 `workshop`）；赛题强制 Word 时走 **Word 原生分支**，不经过 LaTeX。

## 快速开始

| 用户说 | 做什么 |
|---|---|
| “帮我做这道数模题” | 从 S0 启动，依次执行 S0 → S4 |
| “进行建模分析” | 只执行 S1 |
| “进行代码实现” | 只执行 S2 |
| “画技术路线图 / 框架图” | S3，路线 ③ `tools/paper-figure` |
| “画流程图” | S3，路线 ④ 先选路：A `tools/flowchart/scripts/flowchart.py`（JSON→TikZ）/ B `tools/flowchart/scripts/svg_flow.py`（SVG→HTML/PNG） |
| “画可行域 / 相平面 / 受力图” | S3，路线 ② `tools/mechanism-diagram` |
| “写论文 / 编译 PDF” | S4 LaTeX 分支，默认 `assets/templates/latex/workshop/` |
| “这一章怎么写 / 摘要怎么写” | 读 `references/knowledge/10-chapter-writing-prompts.md` 对应节 |
| “写 Word 报告（赛题强制）” | S4 Word 分支，`report_kit.py` 产出 `report/数据分析报告.docx` |
| “导出 Word 改稿副本” | 仅 LaTeX 模式，运行 `scripts/latex2docx.py` |
| “评审论文 / 能拿多少分 / 怎么提分” | 可选，读 `tools/review/SKILL.md`，产出 `reports/REVIEW_REPORT.md` |

## 5 阶段

| 阶段 | 职责别名 | 输入 | 必须产出 | 门禁 | 下一阶段 |
|---|---|---|---|---|---|
| S0 启动 | 总控 | 题面、附件、偏好 | `plan.md`、`todo.md`、项目骨架 + 工程资产、环境报告 | G0 | S1 |
| S1 建模分析 | 建模手 | 题面、附件、`plan.md` | `reports/ANALYSIS_MODELING_REPORT.md`（含得分点表与证据链）、术语表、图件规划、代码任务清单 | G1 | S2 |
| S2 代码实现 | 编程手 | 分析报告 | `code/`、`results/results.json`、`RESULTS_REPORT.md`、`journal_problemN.md`、数据图 + 出图闸门 | G2 | S3 |
| S3 图件制作 | 图件手 | 分析 + 结果 + 图件规划 | 机理图、论文主图、流程图、`FIGURE_REPORT.md`、`figures/manifest.json` | G3 | S4 |
| S4 论文撰写 | 论文手 | 全部报告 + 图 + 结果 | LaTeX：`paper/main.tex` + 各章 `.tex` + `paper/main.pdf`；Word：`report/数据分析报告.docx` | G4 | 完成 |

阶段细节按需读取：

- `references/stages/00-start.md`
- `references/stages/01-analysis.md`
- `references/stages/02-coding.md`
- `references/stages/03-figures.md`
- `references/stages/04-writing.md`

## 默认资产（S0 一次性铺好）

| 资产 | 用途 | 铺到哪 |
|---|---|---|
| `assets/templates/latex/workshop/` | **默认论文模板**：`format.cls` + 17 个章节文件（每个都带【本章节写作提示词】）+ `fonts/` | `paper/` |
| `assets/style/plot_style.py` | 统一绘图版式（中文字体 + 期刊配色 + 组图 + 存图体检） | `code/` |
| `assets/style/check_figures.py` | 出图闸门，硬伤退出码 1 | 项目根 |
| `assets/scaffold/run_all.py` | 批量跑 `code/` 下脚本 | 项目根 |
| `assets/templates/docx/reference.docx` + `report_kit.py` | Word 报告模板与排版工具箱 | `report/` |

## 四路图件：路径 / 读取顺序 / 执行顺序

四路产物全部落在项目 `figures/`，前缀固定 `data_` / `mech_` / `paper_` / `flow_`。**前缀决定 manifest 的 `route`**（`scripts/make_manifest.py` 按前缀识别），前缀写错图就登记错路线。下表里 `<skill>` = 本技能根目录，`<项目>` = 当前项目根。

| # | 路线 | 驱动器 | 输入（读什么） | 中间产物 | 终产物 | 阶段 |
|---|---|---|---|---|---|---|
| ① | 数据图 | matplotlib + `assets/style/plot_style.py` | `code/outputs/*.csv`、`results/results.json` | `figures/data_*.png/.pdf` | 同左 + `figures/_figure_lint.json` | S2 |
| ② | 机理图 | `tools/mechanism-diagram`（TikZ） | 正文公式、题面几何、`reports/symbols.md` | `figures/mech_*.tex` | `figures/mech_*.pdf/.png` + `figures/mech_includes.tex` | S3 |
| ③ | 论文主图 | `tools/paper-figure`（SVG） | `assets/figures/reference/roadmap/` 5 张母版 | `figures/paper_*.svg` | `figures/paper_*.pdf/.png` | S3 |
| ④A | 流程图（TikZ） | `tools/flowchart/scripts/flowchart.py` | `figures/flow_*.json`（8 张母版 JSON 二选一改造） | `figures/flow_*.tex` | `figures/flow_*.pdf/.png` | S3 |
| ④B | 流程图（SVG） | `tools/flowchart/scripts/svg_flow.py` | `figures/flow_*.svg`（母版 `tools/flowchart/assets/flow_svg_template.svg`） | `figures/flow_*.html` | `figures/flow_*.png/.pdf` | S3 |

**边界判据**：有真实数据点/数值结果 → ①；价值在精确几何/公式刻度/符号 → ②；价值在“整体路线/框架一眼讲清” → ③；价值在“步骤、判断、循环、输入输出” → ④（A 或 B）。
**禁止**：一种图跨两条路线重复生成；用 TikZ 画数据图；用 matplotlib 画流程图/路线图；把流程图塞进 `paper-figure`；同一张流程图 A、B 两路各出一份混着用。

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

### ④ 流程图：两条实现路线，先选路再动笔

| 判据 | A · TikZ 路（默认） | B · SVG 路 |
|---|---|---|
| 载体 | JSON 规格 → 生成 `.tex` → xelatex | 手写/改 `.svg` → Edge 渲染 |
| 适合 | 判定框 + 回边、要与正文公式字体一致、直接进 LaTeX | 要交人改、要嵌 HTML/PPT、机器没 MiKTeX、要拖拽微调坐标 |
| 改图方式 | 改 `.json` 重跑脚本（**别手改生成的 `.tex`**） | 浏览器打开 `.html` 点字直改，或直接改 `.svg` |
| 产物 | `flow_*.{json,tex,pdf,png}` | `flow_*.{svg,html,png,pdf}` |
| manifest | `route=flow`、`spec` 填 `.json` | `route=flow`、`spec` 填 `.svg`、`source` 填 `svg_flow.py` |

**A · TikZ 路（读取 → 执行）**：`tools/flowchart/SKILL.md` → `assets/figures/reference/flowchart/<母版>.json`（`linear` / `decision` / `loop` / `pipeline` / `parallel` / `layered` / `algorithm` / `multi_question`）→ 写 `figures/flow_<图名>.json` → 

```bash
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json            # 出 tex+pdf+png（300 dpi）
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json --no-compile  # 只出 tex
```

**B · SVG 路（读取 → 执行）**：`tools/flowchart/SKILL.md` → `tools/flowchart/assets/flow_svg_template.svg` → 复制成 `figures/flow_<图名>.svg` →

```bash
python tools/flowchart/scripts/svg_flow.py figures/flow_q1.svg        # 默认出 html + png + pdf
python tools/flowchart/scripts/svg_flow.py figures/flow_q1.svg -s 3   # 3 倍图，进论文用
```

SVG 本质是 XML：脚本产出的 `figures/flow_q1.html` 在浏览器里点文字即可改，改完点「下载 SVG」覆盖源文件，重跑脚本刷新 PNG/PDF；没有 Edge 时该 HTML 也可直接手工截图或交给浏览器「打印为 PDF」。`cairosvg` 若已安装则自动改走它转 PNG，不依赖浏览器。

**选路一句话**：要进 LaTeX 论文且结构是“判定 + 回边”→ A；要给人改、要进网页/PPT、或机器上没有 LaTeX → B。

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
│   ├── results.json
│   ├── numbers_allow.txt
│   ├── tables/
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
    ├── main.tex
    ├── format.cls
    ├── fonts/
    └── 0.摘要.tex … 11.附录.tex
```

契约：

- `references/contracts/pipeline.md`（**全流程串联：产物 → 生产者 → 消费者 → 门禁**）
- `references/contracts/project-layout.md`
- `references/contracts/results-schema.md`
- `references/contracts/figure-manifest.md`

## 门禁

| 门禁 | 一句话 |
|---|---|
| G0 启动 | 赛事/语言/子问题数已定（可默认 + 写假设），`plan.md`/`todo.md` 存在，工程资产已铺，环境检查完成 |
| G1 建模 | 每问目标、变量、假设、目标函数/约束、算法、输入输出、校验方法齐全；**得分点表与证据链表已写** |
| G2 代码 | 代码从头跑通，结果写入 `results.json`，约束校验通过，种子固定；出图闸门 0 硬伤；得分点逐条核账 |
| G3 图件 | 四路不混用，每图有来源，数据图过闸门 + 目检，机理图/流程图编译 0 error，manifest 完整 |
| G4 论文 | 章节齐全、逐章对照写作提示词自查，数值来自 `results.json`，图表按节插入，无占位符/内部文件名，AI 声明已填；LaTeX 与 Word 分支分别过 G4 |

清单：`references/checklists/G0-start.md` … `G4-writing.md`。

## LaTeX 模板

| 场景 | 模板 |
|---|---|
| **默认**（国赛/省赛/校赛/课程论文） | `assets/templates/latex/workshop/`（默认论文模板，17 章带写作提示词 + `main.tex` 顶部【全文写作总则】） |
| CUMCM 官方格式 | `assets/templates/latex/cumcmthesis/`（CUMCMThesis 2026，含 AI 声明） |
| MCM/ICM（英文） | `assets/templates/latex/mcm/` |
| 华为杯 | `assets/templates/latex/huaweibei/` |
| 通用中文结构（`ctexart`，无竞赛格式要求时） | `assets/templates/latex/default/` |

编译与 Word 分支的细节见 `references/stages/04-writing.md`（编译两遍、`fonts/` 同级、Word 原生分支不经过 LaTeX）。禁止用 Typst。

## 关键规则

1. **数值单一事实源**：论文中的关键数值只能来自 `results/results.json`；不得凭记忆写数。
2. **图件单一来源**：正文只引用 `figures/manifest.json` 中登记的图。
3. **权威版本按交付形态定**：LaTeX 模式以 PDF 为准，Word 只作改稿副本；Word 模式以 DOCX 为准，PDF 只作预览。
4. **不编造文献**：`paper/references.tex` 用 `thebibliography` + `\bibitem{key}`，正文用 `\cite{key}`，键与条目一一对应、条目带完整出版信息；`scripts/check_paper.py` 机器校验，不通过的参考文献等于装饰。
5. **不泄露内部文件名**：论文正文不得出现 `reports/`、`code/`、`results.json`、`plan.md`。
6. **AI 声明**：CUMCM 使用 `\CumcmAIUsed{...}` 或 `\CumcmAINotUsed`，不得留空。
7. **先门禁后推进**：上一阶段不达标，不进入下一阶段。
8. **评审提分**：终稿前跑 `tools/review`，先修 P0/P1，再修格式与摘要；评分只作定位，不承诺获奖。
9. **无人值守**：不中途提问、不停在方案阶段；歧义取保守可验证解释并写进 `plan.md` 假设段（`references/knowledge/11-engineering-contract.md`）。
10. **前台执行**：跑实验/装库/自检一律前台，不后台、不 sleep 轮询；长计算分阶段落盘，缓存不作废。
11. **逐章照提示词**：写哪一章先读 `references/knowledge/10-chapter-writing-prompts.md` 对应节，硬约束逐条自查。
12. **得分点驱动**：S1 立可核验得分点 → S2 逐条核账补证据 → S4 正文逐条落到公式号/图号/表号（`12-scoring-validation.md`）。
13. **产物闭环**：每个产物必须有消费者、每个输入必须有生产者；新增报告先登记 `references/contracts/pipeline.md` 的闭环表，登记不上就不写。

## 知识库索引

| 什么时候读 | 文件 |
|---|---|
| 逐章写作（摘要/引言/建模/检验/评价/附录） | `references/knowledge/10-chapter-writing-prompts.md` |
| 执行纪律、路径、编码与版本坑 | `references/knowledge/11-engineering-contract.md` |
| 得分点、证据链、验证强度、学术分寸 | `references/knowledge/12-scoring-validation.md` |
| 摘要句链、推导三段式、一致性、表格、统计、引用 | `references/knowledge/13-writing-injection.md` |
| 数据图版式、防乱码、出图闸门、plot_style API | `references/knowledge/14-figure-contract.md` |
| 题面拆解 / 选型 / 题型防错 / 图种 / 写作底线 / 评审 | `references/knowledge/01`–`09`（见 `00-index.md`） |

## 工具索引

| 工具 | 用途 |
|---|---|
| `tools/doctor` | 环境检查 |
| `tools/pdf` | 读题面 PDF |
| `tools/xlsx` | 读/写数据表 |
| `tools/paper-search` | Crossref + arXiv 论文搜索 |
| `tools/mechanism-diagram` | 机理图（TikZ） |
| `tools/paper-figure` | 路线图/框架图（SVG → PDF/PNG） |
| `tools/flowchart` | 流程图：A 路 `scripts/flowchart.py`（JSON → TikZ → PDF/PNG）、B 路 `scripts/svg_flow.py`（SVG → 可编辑 HTML → PNG/PDF） |
| `tools/figure-templates` | 11 个科研数据图模板 |
| `tools/review` | 评委式评审：100 分评分、格式系数、P0–P3 问题、提分建议 |

## 脚本索引

> 脚本路径相对于技能根目录；在项目目录运行时用 `python <skill-root>/scripts/xxx.py --project 项目N`。

| 脚本 | 用途 |
|---|---|
| `scripts/doctor.py` | 环境检查（xelatex 必选；pandoc / pdftoppm 可选） |
| `scripts/build_paper.py` | xelatex 编译 + PDF 页检查（退出码 0=PASS / 1=FAIL / 2=WARN） |
| `scripts/check_paper.py` | 论文自检 6 项：数字↔`results.json`、文献↔`\cite`、章节结构（符号说明独立且前置）、产物闭环（含 SCORE_MAP 落点）、内部文件名、图件↔`manifest.json`（G4 前必跑，退出码 0 才算过） |
| `scripts/build_prompts.py` | 从 workshop 模板重建 `knowledge/10-chapter-writing-prompts.md` |
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
