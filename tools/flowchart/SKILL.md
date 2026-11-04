---
name: flowchart
description: 数学建模论文流程图。两条路线：总流程图 / 问题分析总览用 SVG（5 套实拍母版 → 可编辑 HTML → PNG/PDF，不需要 LaTeX）；算法流程 / 判定分支 / 循环迭代用 TikZ（8 套 JSON 母版 → TeX → PDF/PNG）。触发词：画流程图 / 问题分析流程图 / 总流程图 / 算法流程 / 求解步骤 / 判定分支 / 循环迭代。只做流程，不画数据图、机理图、技术路线图。
---

# 流程图（两条路线：TikZ / SVG）

## 定位

流程图回答“先做什么、判断什么、循环什么、输出什么”。它和另外三路的分工：

| 图 | 工具 | 画什么 |
|---|---|---|
| 数据图 | matplotlib | 真实数据 |
| 机理图 | `mechanism-diagram` | 几何/公式/物理关系（可行域/受力/光路） |
| 论文主图 | `paper-figure` | 整体路线/框架 |
| **总流程图** | **本工具 · B 路（SVG）** | **问题怎么分析、任务怎么分组（5 套实拍母版）** |
| **算法流程** | **本工具 · A 路（TikZ）** | **步骤/判断/循环/流水线（8 套 JSON 母版）** |

## 两条路线（先选路，再动笔）

本工具同一件事有两种载体，**一张图只走一条**，不许两路各出一份混着用。

| 判据 | B · SVG 路（**总流程图默认**） | A · TikZ 路（算法/判定细节） |
|---|---|---|
| 入口 | `scripts/svg_flow.py` + `figures/flow_*.svg` | `scripts/flowchart.py` + `figures/flow_*.json` |
| 画什么 | 问题分析总流程、任务分组、总体思路、多面板总图 | 算法流程、判定分支、循环迭代、多阶段流水线 |
| 适合 | 要交人改、要嵌 HTML/PPT、机器没 MiKTeX、要拖拽微调坐标 | 判定框 + 回边、要与正文公式字体一致、直接进 LaTeX |
| 改图 | 浏览器打开 `.html` 点字直改，或直接改 SVG 坐标 | 改 JSON 重跑脚本（别手改生成的 `.tex`） |
| 产物 | `flow_*.svg` / `.html` / `.png` / `.pdf` | `flow_*.json` / `.tex` / `.pdf` / `.png` |
| manifest | `route=flow`，`spec` 填 `.svg`，`source` 填 `svg_flow.py` | `route=flow`，`spec` 填 `.json`，`source` 填 `flowchart.py` |

### A · TikZ 路（JSON → TikZ → PDF/PNG）

```bash
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json              # tex + pdf + png(300dpi)
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json --no-compile # 只出 .tex
python tools/flowchart/scripts/flowchart.py figures/flow_q1.json --dpi 600    # 改 PNG 分辨率
```

链路：`flow_*.json` → `flow_*.tex`（脚本生成，不手改）→ `xelatex` → `flow_*.pdf` → `pdftoppm`（或 PyMuPDF）→ `flow_*.png`。

### B · SVG 路（SVG → 可编辑 HTML → PNG/PDF，不需要 LaTeX）

```bash
cp tools/flowchart/assets/flow_svg_template.svg figures/flow_q1.svg   # 从母版起手
python tools/flowchart/scripts/svg_flow.py figures/flow_q1.svg        # 默认 html + png + pdf
python tools/flowchart/scripts/svg_flow.py figures/flow_q1.svg -s 3   # 3 倍图，进论文用
python tools/flowchart/scripts/svg_flow.py figures/flow_q1.svg --html # 只出可编辑页面
```

**改字闭环**：打开 `figures/flow_q1.html` → 点图里的文字直接改 → 「下载 SVG」覆盖 `flow_q1.svg` → 重跑脚本刷 PNG/PDF。SVG 是 XML，本来就能内联进 HTML 改；没有 Edge 时这个 HTML 也能手工截图或浏览器「打印为 PDF」。装了 `cairosvg` 的话脚本自动改走它转 PNG，不依赖浏览器。

母版两档：

- **总流程图 5 套实拍母版**：`assets/figures/reference/totalflow/`（`src/` 实拍图 + `preview/` 复刻 PNG + `index.json`），可编辑 SVG 在 `tools/flowchart/assets/totalflow/tf_*.svg`，`build_totalflow.py` 可重生；
- **最小骨架**：`tools/flowchart/assets/flow_svg_template.svg`（判定 + 回边，改文字即可用）。

色数 ≤3（最多 5）、文字纯黑、图内不写结果数值，与 A 路同一套验收。

## 8 张母版（A 路）

`assets/figures/reference/flowchart/` 下有 8 份 `*.json` 与对应 PDF/PNG：

| 母版 | 适用 |
|---|---|
| `linear` | 简单线性求解 |
| `decision` | if/else 判定分支 |
| `loop` | 迭代/收敛判断 |
| `pipeline` | 数据→预处理→模型→求解→结果 |
| `parallel` | 并行分支/融合 |
| `layered` | 主流程 + 子流程 |
| `algorithm` | 初始化→迭代→终止 |
| `multi_question` | Q1→Q2→Q3 串联 |

选图：

| 题目结构 | 母版 |
|---|---|
| 优化迭代 | `loop` / `algorithm` |
| 预测流水线 | `pipeline` |
| 评价流程 | `pipeline` / `layered` |
| 判定规则 | `decision` |
| 多算法并行 | `parallel` |
| 多子问题 | `multi_question` |
| 简单线性 | `linear` |

## 规格

```json
{
  "layout": "loop",
  "direction": "TB",
  "title": "问题一求解流程",
  "nodes": [
    {"id": "start", "type": "start", "text": "输入数据"},
    {"id": "init", "type": "process", "text": "初始化参数"},
    {"id": "solve", "type": "process", "text": "求解模型"},
    {"id": "check", "type": "decision", "text": "满足收敛条件?"},
    {"id": "update", "type": "process", "text": "更新参数"},
    {"id": "end", "type": "end", "text": "输出结果"}
  ],
  "edges": [
    ["start", "init"],
    ["init", "solve"],
    ["solve", "check"],
    ["check", "end", "是"],
    ["check", "update", "否"],
    ["update", "solve"]
  ]
}
```

节点类型：`start`、`process`、`decision`、`io`、`subprocess`、`end`。

## 使用（A 路的产物清单）

```bash
python tools/flowchart/scripts/flowchart.py figures/flow_q1_solution.json
python tools/flowchart/scripts/flowchart.py figures/flow_q1_solution.json --no-compile
```

输出：

- `figures/flow_q1_solution.tex`
- `figures/flow_q1_solution.pdf`
- `figures/flow_q1_solution.png`（300 dpi）

B 路同名产物是 `flow_q1_solution.svg / .html / .png / .pdf`，两路的 PDF 形态不同：A 是 TikZ 矢量、字体跟随 LaTeX；B 是浏览器打印的矢量、字体跟随系统。

## 验收（两条路通用）

- [ ] 选对路线：要进 LaTeX 且结构含判定/回边 → A；要交人改/进网页 → B
- [ ] 选对母版，不是“框+箭头”随便画
- [ ] 每个判定有“是/否”出口
- [ ] 循环有回边
- [ ] 节点不重叠，箭头不穿核心节点
- [ ] 术语与论文一致
- [ ] 图内不写求解结果数值
- [ ] B 路额外：`svg_flow.py` 跑完 PNG 与 PDF 都要真实存在，`id`（文件名 stem）与 manifest 一致
- [ ] 有 caption，正文有 ≥100 字分析
- [ ] 登记 `figures/manifest.json`（route=`flow`；A 填 `spec` 为 `.json`，B 填 `spec` 为 `.svg`）

## 边界

- 不画几何/物理机理（可行域、受力、光路）→ ② `mechanism-diagram`；不画技术路线图 → ③ `paper-figure`。总流程图的“任务分组/问题分析”仍由本工具 B 路承担，别推给 paper-figure。
- 不画数据图、机理图、技术路线图。
- 同一张流程图不许 A、B 两路各出一份（manifest 只登记一条）。
- 不为了凑图生成没有信息量的流程。
- 复杂图拆成主流程 + 子流程，不堆在一张图里。


## 与 paper-figure / mechanism-diagram 的分工

| 判据 | 用哪个 |
|---|---|
| 有「是/否」判定框、有回边 | 本工具（`decision` / `loop` / `algorithm` 母版） |
| 「问题怎么分析、任务怎么分组」的总流程图 | 本工具 B 路（SVG，`totalflow` 5 套母版） |
| 要独立成件、可复用、单独渲染质检 | 本工具 |
