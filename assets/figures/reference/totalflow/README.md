# 总流程图实例模板（totalflow）

用户实拍入库的 5 张 **总流程图**（问题分析/总体思路级：任务分组、多面板、嵌套包裹、左入右出流水线、多步骤），
每张都配了一份**可编辑 SVG 复刻**与渲染出的 **PNG**。这是路线 ④B（SVG）的母版库，不是 TikZ。

```
totalflow/
├── src/       5 张实拍图（原始 jpg，只作版式参考，不进论文）
└── preview/   5 张 SVG 复刻渲染的 PNG（2×，2880×1600）
```

对应的 SVG 在 `tools/flowchart/assets/totalflow/`，由 `tools/flowchart/scripts/build_totalflow.py` 生成。

## 五套版式

| id | 版式 | 适用场景 | 别用它 |
|---|---|---|---|
| `tf_01_quadrant_tasks` | 四象限任务分组（任务 1–4 + 标签页 + 跨组空心箭头） | 3–4 个任务并列，且任务间有先后/派生关系 | 任务超过 5 个、或只有一个任务（用 `pipeline`） |
| `tf_02_multi_panel` | 多面板（左竖链 + 中两段 + 右两块） | 一张图要同时交代「模型流程 + 特征分析 + 难点分类」 | 只有一条主线（会显得空） |
| `tf_03_nested_sustainability` | 嵌套大框（外层议题 → 内层子议题 → 任务 1–5） | 有「总议题 / 子议题」两层归类，且任务分属不同议题 | 层级只有一层（用 `quadrant`） |
| `tf_04_pipeline_groups` | 左入右出流水线（数据 → 任务 1–4 → 目标与行动） | 一条完整链路，每组是一段方法（网络分析/指标/组建…） | 有回边、有判定循环（用 ④A TikZ） |
| `tf_05_five_steps` | 五步骤（上排 1/2 + 下排 3/4/5 + 步骤间空心箭头） | 方法分「评估 → 优化 → 协议 → 扩展 → 落地」这类阶段 | 步骤数 ≤3（用 `linear`/`pipeline`） |

## 怎么用（三步）

```bash
# 1) 复制母版成自己的图（改文字、不用从零画）
cp tools/flowchart/assets/totalflow/tf_01_quadrant_tasks.svg figures/flow_total.svg

# 2) 浏览器里点字直改（生成可编辑 HTML，改完「下载 SVG」覆盖）
python tools/flowchart/scripts/svg_flow.py figures/flow_total.svg --html

# 3) 出图（PNG 3 倍 + 矢量 PDF，Edge 无头渲染，不需要 LaTeX）
python tools/flowchart/scripts/svg_flow.py figures/flow_total.svg -s 3
```

要改结构（加/删框、挪组）时改 SVG 里的 `x/y/width/height`；想批量重生五套母版：
`python tools/flowchart/scripts/build_totalflow.py --png`。

## 共同视觉规范（五套一致）

1. **虚线分组框 + 实色标签页**：组框虚线 `#4472c4`，任务标签页 `#2f5597` 白字；
2. **淡色填充**：蓝 `#bdd7ee`、绿 `#a9d18e`、黄 `#ffe699`、粉 `#fbe5d6`、紫 `#d9d2e9`；
3. **文字纯黑**，强调只靠加粗与字号；
4. **正交折线箭头**，跨组用**空心大箭头**；
5. 一张图只讲一条主线，组内 ≤5 个框；
6. 图内不写求解结果数值（数值进正文/表）。

## 与另外三路的分工

| 要画什么 | 走哪条 |
|---|---|
| 问题分析总流程、任务分组、总体思路（本目录 5 套） | **④B SVG**（`svg_flow.py`） |
| 算法流程、判定分支、循环迭代 | ④A TikZ（`flowchart.py`，8 套 JSON 母版） |
| 几何/物理机理（可行域、受力、光路） | ② `mechanism-diagram`（TikZ） |
| 技术路线图（5 张实拍母版风格） | ③ `paper-figure`（SVG） |
