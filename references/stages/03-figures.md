# S3 图件制作（图件手）

## 目标

按四路图件体系补齐论文所需图件，登记 `figures/manifest.json`，确保每张图有来源、有用途、能进论文。

## 输入

- `reports/ANALYSIS_MODELING_REPORT.md`
- `reports/RESULTS_REPORT.md`
- `results/results.json`
- `reports/图件规划.md`
- `reports/symbols.md`（图内标注的符号与正文、代码同源；图里写 `m_e` 就不许正文写 `m_b`）
- `reports/journal_problemN.md`（图上该标哪 1–2 个关键数，以纪要为准）
- `figures/` 已有数据图
- `references/knowledge/14-figure-contract.md`（数据图的版式契约与出图闸门）

## 四路边界

| 路线 | 画什么 | 工具 | 产出 |
|---|---|---|---|
| ① 数据图 | 真实数据可视化 | matplotlib + `plot_style` + `tools/figure-templates` | `data_*.pdf/.png` |
| ② 机理图 | 几何/公式/物理关系 | `tools/mechanism-diagram`（TikZ） | `mech_*.tex/.pdf/.png` |
| ③ 论文主图 | 技术路线/框架/总览 | `tools/paper-figure`（SVG） | `paper_*.svg/.pdf/.png` |
| ④B 总流程图（SVG） | 问题分析总流程/任务分组 | `tools/flowchart/scripts/svg_flow.py` | `flow_*.svg/.html/.png/.pdf` |
| ④A 算法流程（TikZ） | 步骤/判断/循环/流水线 | `tools/flowchart/scripts/flowchart.py` | `flow_*.json/.tex/.pdf/.png` |

判据：

- 真实数据点 → ①；
- 精确几何/公式刻度 → ②；
- 整体路线/框架一眼讲清 → ③；
- 步骤、判断、循环、输入输出 → ④。

> 「一问一列各几步」的分工总览（1 根 → N 问 → 每问等长步骤）没有判定/回边，归路线 ③ `paper-figure`（SVG），不占 ④ 的额度；有判定/回边的才走 ④。判据见 `references/knowledge/05-figures.md`「一问一列的分工总览走哪条」。

禁止跨路线重画。

数据图（路线 ①）的图数按下表，角色后缀写进文件名：`_data`（探索）、`_diagnostic`（诊断）、`_comparison`（对照/消融）、`_sensitivity`（灵敏度）、`_layout`（排布/路径）、`_mechanism`（机理，走路线②）。

| 赛事 | 每问结果图 | 上限 |
|---|---|---|
| 国赛 | 4–5 | 6 |
| 美赛/亚太 | 3 | 5 |
| 华为杯 | 8 | 10 |

角色按证据需要选，不凑齐；没有数据支撑的角色就不画。

## 步骤

### 1. 盘点

读取分析报告、结果报告、`figures/` 列表，列出：

- 已有图（路线、文件名、用途）；
- 缺失图（路线、需求、放置章节）；
- 可合并/可删除的图。

### 2. 机理图（路线 ②）

- **读取顺序**：`tools/mechanism-diagram/SKILL.md` → `tools/mechanism-diagram/references/diagram-taxonomy.md`（选图型 + 数据红线）→ `tools/mechanism-diagram/references/tikz_rules.md`（配色铁律 + 自检 6 条）→ `tools/mechanism-diagram/references/mechanism-templates.tex`（抄构造）→ 写 `figures/mech_*.tex`；
- 产出 `.tex` + `.pdf` + `.png`：`xelatex -interaction=nonstopmode -halt-on-error` → `pdfcrop`（缺 perl 会报 `script engine` 错，**直接跳过**，`standalone` 的 `border=3pt` 已紧裁）→ `pdftoppm -r 300 -png -singlefile`；
- 编译 0 error / 0 overfull（`grep -c "Overfull\|Underfull" *.log` 必须 0）；PNG 必须 `read_image` 目检；
- 图内不写求解结果数值。

### 3. 论文主图（路线 ③）

- 读 `tools/paper-figure/SKILL.md`；
- 从 5 张实拍母版（`grouped-tasks` / `nested-cluster` / `quad-matrix` / `multi-panel` / `staged-steps`）中选结构最接近的一张，对着抄；
- 生成 `paper_*.svg`，再转 `.pdf` + `.png`；
- 技术路线图通常至少 1 张，放在问题重述/总体思路。

### 4. 流程图（路线 ④：总流程图走 B/SVG，算法细节走 A/TikZ）

先按判据选路，再动笔；一张图只走一条。

| 判据 | B · SVG 路（总流程图默认） | A · TikZ 路（算法细节） |
|---|---|---|
| 什么时候用 | 问题分析总流程、任务分组、总体思路（要交人改/进网页也用它） | 算法流程含判定/回边、要进 LaTeX、与正文公式字体一致 |
| 入口 | `figures/flow_*.svg`（母版 `assets/figures/reference/totalflow/` 5 套，可编辑源在 `tools/flowchart/assets/totalflow/`） | `figures/flow_*.json`（母版 `assets/figures/reference/flowchart/` 8 套） |
| 产物 | `.svg/.html/.png/.pdf` | `.json/.tex/.pdf/.png` |

**B · SVG 路（总流程图）**

- 读 `tools/flowchart/SKILL.md` 与 `assets/figures/reference/totalflow/README.md`；
- 按版式表选一套：`quadrant`（任务分组）/ `multi-panel`（多面板）/ `nested`（议题包裹）/ `pipeline-groups`（左入右出）/ `five-steps`（多步骤）；
- 复制 `tools/flowchart/assets/totalflow/tf_*.svg` → `figures/flow_*.svg`，改文字与框位；
- `python tools/flowchart/scripts/svg_flow.py figures/flow_total.svg`（默认出 `.html` + `.png` + `.pdf`；`-s 3` 出 3 倍图）；
- 改字闭环：浏览器打开 `figures/flow_total.html` 点字直改 → 「下载 SVG」覆盖源文件 → 重跑脚本刷 PNG/PDF；
- 没有 Edge 时：`--html` 出的页面可手工截图，或浏览器「打印为 PDF」。

**A · TikZ 路（算法流程）**

- 从 `assets/figures/reference/flowchart/` 的 8 张母版里选版式；
- 写 `figures/flow_*.json` 规格；
- `python tools/flowchart/scripts/flowchart.py figures/flow_q1.json`（脚本内部 xelatex + pdftoppm）；
- 检查节点不重叠、分支有出口、循环有回边、术语一致。

### 5. 出图闸门（进 manifest 之前）

数据图一律先过闸门，再登记：

```bash
python check_figures.py          # 退出码 0 = 无硬伤
python check_figures.py --json
```

- 压字、空面板、平线、双轴柱、图例压数据、重复系列、乱码 → 必须为 0，重画后重跑；
- 闸门只覆盖 matplotlib 数据图；机理图/流程图看编译日志与肉眼检查；
- 闸门之外再 `read_image` 目检轴/图例/字号/配色。

### 6. 登记 manifest

每张图登记到 `figures/manifest.json`：

- `id`、`route`、`source`、`spec`/`data`、`outputs`、`caption`、`section`、`status`。

### 7. 写图件报告

`reports/FIGURE_REPORT.md` 至少包含：

- 图件清单（id / 路线 / 文件 / 用途 / 章节）；
- 未生成图及原因；
- 编译/导出记录与闸门结果；
- 给论文阶段的插入建议（含建议宽度档位）。

## 必须产出

- `figures/mech_*`、`paper_*`、`flow_*`
- `figures/manifest.json`（含全部数据图的宽高比与建议宽度）
- `figures/_figure_lint.json`（闸门结果）
- `reports/FIGURE_REPORT.md`

## 边界

- 不重跑模型、不修改 `results.json` 的数值结论。
- 不重复生成 S2 已完成的数据图。
- 不为凑数量生成无意义图。

## 门禁

通过 `references/checklists/G3-figures.md` 后进入 S4。
