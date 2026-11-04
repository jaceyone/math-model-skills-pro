---
name: flowchart
description: 数学建模论文流程图。用于“画流程图 / 算法流程 / 求解步骤 / 判定分支 / 循环迭代 / 多阶段流水线”等任务。从 8 张精选版式中选母版，写 flowchart.json，生成 TikZ，编译为 PDF/PNG。只做流程，不画数据图、机理图、技术路线图。
---

# 流程图（TikZ）

## 定位

流程图回答“先做什么、判断什么、循环什么、输出什么”。它和另外三路的分工：

| 图 | 工具 | 画什么 |
|---|---|---|
| 数据图 | matplotlib | 真实数据 |
| 机理图 | `mechanism-diagram` | 几何/公式/物理关系 |
| 论文主图 | `paper-figure` | 整体路线/框架 |
| **流程图** | **本工具** | **步骤/判断/循环/流水线** |

## 8 张母版

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

## 使用

```bash
python tools/flowchart/scripts/flowchart.py figures/flow_q1_solution.json
python tools/flowchart/scripts/flowchart.py figures/flow_q1_solution.json --no-compile
```

输出：

- `figures/flow_q1_solution.tex`
- `figures/flow_q1_solution.pdf`
- `figures/flow_q1_solution.png`（300 dpi）

## 验收

- [ ] 选对母版，不是“框+箭头”随便画
- [ ] 每个判定有“是/否”出口
- [ ] 循环有回边
- [ ] 节点不重叠，箭头不穿核心节点
- [ ] 术语与论文一致
- [ ] 图内不写求解结果数值
- [ ] 有 caption，正文有 ≥100 字分析
- [ ] 登记 `figures/manifest.json`（route=`flow`）

## 边界

- 不画 §2 的「总体分析」分工图：那张是 workshop 模板内置 TikZ（1 根 → N 问 → 每问等长步骤，无判定/回边），改 `assets/templates/latex/workshop/2.总体分析.tex` 的 `\rows`，不要用本工具重画。
- 不画数据图、机理图、技术路线图。
- 不为了凑图生成没有信息量的流程。
- 复杂图拆成主流程 + 子流程，不堆在一张图里。

## 与模板 TikZ 的分工

| 判据 | 用哪个 |
|---|---|
| 有「是/否」判定框、有回边 | 本工具（`decision` / `loop` / `algorithm` 母版） |
| 只是「全文一问一列各几步」的分工总览 | 模板 TikZ（`workshop/2.总体分析.tex`） |
| 要独立成件、可复用、单独渲染质检 | 本工具 |
