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
| 算法流程、判定分支、循环迭代、多阶段流水线 | `tools/flowchart`（JSON → TikZ → PDF） |
| 可行域、相平面、受力、光路、状态转移、控制体 | `tools/mechanism-diagram`（TikZ） |
| 折线/散点/柱状/热图/ROC/Taylor 等 | matplotlib + `assets/style/plot_style.py` |

主图只参考 `assets/figures/reference/roadmap/` 那 5 张母版（选版式看 `roadmap/README.md` 的骨架表），不引入其他图库或其他论文配图；一张图只回答一个问题，同类图风格统一、配色能灰度区分。

## §2 的总体分析图：模板 TikZ 还是 `tools/flowchart`

`assets/templates/latex/workshop/2.总体分析.tex` 自带一张 TikZ 分工图（1 根 → N 问 → 每问 6 步，黑白、自动布局）。它是**路线 ③ 的内置轻量变体**，不是路线 ④；两者的区别不在画法，在图回答的问题：

| | 模板内置 TikZ（§2 总体分析图） | `tools/flowchart`（路线 ④） |
|---|---|---|
| 图论语义 | 树：根 → N 问 → 每问等长步骤，**无判定、无回边** | 有向图：◇ 判定双出口、loop 回边、parallel 汇合 |
| 回答什么 | 全文怎么分工（一问一列） | 某个算法怎么跑（先算什么、判断什么、不满足怎么回去） |
| 载体 | 写在 `.tex` 里随正文编译，字体/线宽/字号与正文一致 | JSON → TikZ → PDF/PNG，独立图件，登记 `manifest.json`（route=`flow`） |
| 位置与数量 | 固定 §2 末尾，全文 1 张 | 各问「模型求解」小节，每问 ≤1、全文 ≤3 |
| 复用与质检 | 与本文强绑定，不跨项目 | 可复用、可单独渲染、可逐张目检 |

三问判据，按顺序问，先命中先定：

1. 图里有「是/否」分叉，或「不满足就回去」的回边？→ 有 = `tools/flowchart`（选 `decision` / `loop` / `algorithm` 母版）。
2. 这张图讲的是「全文分工」还是「某个算法怎么跑」？→ 分工 = 模板 TikZ；算法 = `tools/flowchart`。
3. 要不要独立成件（跨文档复用、单独渲染质检、进附录）？→ 要 = `tools/flowchart`；随文排版 = 模板 TikZ。

反模式：

- 用 `tools/flowchart` 画「三问六步」：出来的是一棵没有判定框的树，JSON 布局还把它拉成竖条，不如模板 TikZ。
- 用模板 TikZ 塞判定/循环：`\rows` 只支持每问等长步骤，手改坐标必断线（模板注释已警告）。
- 同一内容画两张（§2 一张 + §5 再一张）：违反「一张图只回答一个问题」。
- 想要出版级视觉、母版风格的技术路线图 → 走路线 ③ `tools/paper-figure`，不要拿模板 TikZ 硬撑。

兜底：母版确实装不下（多阶段 + 判定 + 回边的复合结构），先按 `layered` / `multi_question` 拆成两张；仍装不下才手写 standalone TikZ（`figures/flow_*.tex`），照样登记 `manifest.json` 的 `route=flow`，并在 `reports/FIGURE_REPORT.md` 写明哪条判据用不上母版。
