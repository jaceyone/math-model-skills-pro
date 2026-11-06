# 图表与可视化

> 改编自 MathModelAgent math_modeling_norms.md（个人使用许可），按主题拆分；保留原意，调整结构与标题。
>
> **本技能现行口径**：数据图的版式、配色与出图闸门照 `14-figure-contract.md`（`plot_style.apply()` + `check_figures.py`）；图题/表题怎么写照 `13-writing-injection.md` 三.10。本文件只管一件事：**图种怎么选、走哪一路**。

## 图种怎么选

- 一张图只回答一个问题：趋势、分布、对比、关系、结构或流程。回答不了就删图，不为凑数量画。
- 有数据：趋势用折线，排名用条形/棒棒糖，分布用箱线/小提琴/直方图，关系用散点/热力图，模型对比用分组柱或指标矩阵。
- 没数据：技术路线、方法框架、总览、分类、数据处理流程、求解流程、变量关系、模型结构、指标体系 —— 一律走下面四路之一，不做第五种（§2 的总体分析图是路线 ③ 的内置变体，见下，不算第五种）。
- 图中文字、坐标轴、图例与 caption 的语言随论文语言；图内不写长标题，标题交给 caption。

## 非数据图走哪一路

本技能只有四路图件，别的工具不要引：

| 要画什么 | 走哪一路 |
|---|---|
| 技术路线图、方法框架图、总览图、分类图 | `tools/paper-figure`（5 张母版 → SVG → PDF/PNG） |
| 问题分析总流程、任务分组、总体思路（总流程图） | `tools/flowchart` **B 路** `tools/flowchart/scripts/svg_flow.py`（SVG → 可编辑 HTML → PNG/PDF；母版 5 套在 `assets/figures/reference/totalflow/`） |
| 算法流程、判定分支、循环迭代、多阶段流水线 | `tools/flowchart` **A 路** `tools/flowchart/scripts/flowchart.py`（JSON → TikZ → PDF/PNG；母版 8 套） |
| 可行域、相平面、受力、光路、状态转移、控制体 | `tools/mechanism-diagram`（TikZ） |
| 折线/散点/柱状/热图/ROC/Taylor 等 | matplotlib + `assets/style/plot_style.py` |

四路的**路径、读取顺序、执行顺序**只有一份权威版：`SKILL.md` 的「四路图件：路径 / 读取顺序 / 执行顺序」一节。本节只判“走哪一路”，不复述命令。

主图只参考 `assets/figures/reference/roadmap/` 那 5 张母版（选版式看 `roadmap/README.md` 的骨架表），不引入其他图库或其他论文配图；一张图只回答一个问题，同类图风格统一、配色能灰度区分。

## 「总流程图」与「算法流程图」走哪条

总流程图（问题怎么分析、任务怎么分组、总体思路）**用 SVG（④B）**；算法细节（判定、回边、循环）**用 TikZ（④A）**。两者都在 `tools/flowchart` 下，但母版与产物完全不同：

| | 总流程图（④B · SVG） | 算法流程图（④A · TikZ） |
|---|---|---|
| 图论语义 | 分组树 / 多面板：任务或模块并列，箭头表示先后与派生，**通常无判定、无回边** | 有向图：◇ 判定双出口、loop 回边、parallel 汇合 |
| 回答什么 | 全文怎么分析、任务怎么分工 | 某个算法怎么跑（先算什么、判断什么、不满足怎么回去） |
| 母版 | `assets/figures/reference/totalflow/` 5 套（quadrant / multi-panel / nested / pipeline-groups / five-steps） | `assets/figures/reference/flowchart/` 8 套 JSON |
| 载体 | `flow_*.svg` → `tools/flowchart/scripts/svg_flow.py` → 可编辑 HTML / PNG / PDF，登记 `manifest.json`（route=`flow`，spec=.svg） | `flow_*.json` → `flow_*.tex` → xelatex → PDF/PNG，登记 route=`flow`，spec=.json |
| 位置与数量 | 问题分析/总体思路处，全文 1 张 | 各问「模型求解」小节，每问 ≤1、全文 ≤3 |
| 改法 | 浏览器打开 `.html` 点字直改，或改 SVG 坐标 | 改 JSON 重跑脚本，别手改生成的 `.tex` |

三问判据，按顺序问，先命中先定：

1. 图里有「是/否」分叉，或「不满足就回去」的回边？→ 有 = ④A TikZ（选 `decision` / `loop` / `algorithm` 母版）。
2. 这张图讲的是「问题怎么分析、任务怎么分工」还是「某个算法怎么跑」？→ 前者 = ④B SVG（`totalflow` 5 套母版）；后者 = ④A。
3. 要不要进 LaTeX 正文、字号线宽与正文一致？→ 要 = ④A；只要一张能改的图、要进 HTML/PPT = ④B。

反模式：

- 用 ④A 画「三问六步」的分工图：出来的是一棵没有判定框的树，JSON 布局还把它拉成竖条，不如 `totalflow` 的 `quadrant` 母版。
- 用 ④B 塞判定/循环：`totalflow` 五套版式都是分组/面板，画流程会画成「框 + 箭头」的假流程图。
- 同一内容画两张（总体思路一张 + 某问再一张）：违反「一张图只回答一个问题」。
- 想要出版级、任务分组风格的总览，却去手写 TikZ：直接用 `totalflow` 母版，别重复造。

兜底：`totalflow` 5 套装不下（多阶段 + 判定 + 回边的复合结构），先按 `layered` / `multi_question` 拆成两张（④A）；仍装不下才手写 standalone TikZ（`figures/flow_*.tex`），照样登记 `manifest.json` 的 `route=flow`，并在 `reports/FIGURE_REPORT.md` 写明哪条判据用不上母版。
