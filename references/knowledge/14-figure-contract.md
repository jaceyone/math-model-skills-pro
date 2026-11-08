# 14 · 绘图契约（plot_style + 闸门 + 实测坑）

> 本文件是数据图的版式与出图闸门契约，工具侧落地为本技能 `assets/style/`。
> **只讲数据图（路线①）**。机理图见路线②、论文主图见路线③、流程图见路线④（`tools/flowchart`，本文件不涉及）。

## 一、三件套

| 文件 | 放哪 | 干什么 |
|---|---|---|
| `assets/style/plot_style.py` | 复制到项目 `code/` | 统一字体/配色/版式，`savefig` 时自动体检 |
| `assets/style/check_figures.py` | **只复制到项目根**，不要放 `code/` | 读 `figures/_figure_lint.json`，有硬伤退出码 1；找不到 `figures/` 时退出码 2（`[闸门未执行]`），不再静默放行 |
| `assets/scaffold/run_all.py` | 复制到项目根 | 依次跑 `code/` 下脚本，批量出图 |

```python
from plot_style import (apply, combo_axes, mosaic_axes, response_surface,
                        series_style, series_color, role_color,
                        legend_outside, figure_legend_above, tidy,
                        panel_labels, save_publication, figsize, PALETTE)
apply()                       # 必备第一行：中文宋体 + 西文 Times + 公式 STIX
```

**禁止在脚本里再设 `rcParams["font.family"]` / `font.sans-serif"]`** —— 覆盖后中文必变方块；要换配色用 `apply(palette="nejm")`（可选 nature/okabe/nejm/lancet/jama/muted/morandi/earth/mma），一篇论文只用一套。

## 二、红线

1. 数据只从 `results/`、`data/` 读，禁止捏造点；每张图都要有生成脚本，脚本可重跑。
2. 路径：`ROOT = Path(__file__).resolve().parents[1]` 再拼 `figures/`；**禁止 `../figures/`**。
3. 标签里只要有 `$`，整句交给数学字体，汉字变 `¤`；变量写明文（`T`、`W_0`、`ΔV`），下标写 `_0` 不写 `₀`。出现 Glyph missing 必须改标签重画。
4. 禁用雷达图、饼图、jet/彩虹配色；禁 3D 柱、3D 饼。双参数灵敏度用 `response_surface`。配色要在灰度打印下仍能区分（`okabe` 为色盲友好方案），不靠红绿单通道对立。
5. 不同角色的图不共用文件名：`_layout` 必须是真排布图，不许用柱状图冒充。
6. 用图模板（`tools/figure-templates`）时先复制脚本再换真值，**禁止交模板自带模拟数据的复刻图**。

7. **`data_*` 只读图件规划 `reads:` 声明过的键**：`reads` 在 S1 就写好了，画图时按单取数；临时翻 `results.json` 挑好看的数，等于让图脱离契约。图内标注的关键数值同样取自这些键（`f"{res['problem2.reduction_pct']*100:.2f}%"`），不许手打。

## 三、默认版式＝横排组图占满版心

```python
fig, axes = combo_axes(2)          # 两格横排；三格 combo_axes(3)
# 左格主证据、右格另一类证据（趋势/分布/热图/等高线）
figure_legend_above(fig, axes)     # 收尾合并图例；(a)(b)(c) 存图时自动补
```

- **面板不许竖着堆**（`subplots(3,1)` 是硬伤）：一律横排，超过 3 格拆成两张；只有共用 x 轴时才竖排。
- **简单柱 / 三点散点 / 光秃折线不许单独成图**：对照并成组图（值 + 残差）；灵敏度密采样 ≥11 点。
- 多指标量纲不同 → 不共用「数值」轴、不用双 y 轴柱；归一化或拆面板。
- 右格没有真数据就不要塞文字板；凑不出就删图改三线表 + 一句解读 —— 换载体不丢证据，得分点一条不能少。
- 灵敏度没有变化 → 不画水平直线，写成一句话；扰动只有两三个水平 → 改三线表。
- 别给柱子加 hatch；图例压数据时 `legend_outside(ax)`。
- 画布优先 `combo_axes`，单图 `figsize("wide")`；自己填 `(14, 8)` 会把字缩没。**最多 2×2**。

## 四、图数与角色

- 国赛：每问结果图 4–5 张（上限 6）；美赛/亚太：每问 3 张（上限 5）；华为杯：每问 8 张（上限 10）。
- 角色后缀：`_data`（探索）、`_diagnostic`（诊断）、`_comparison`（对照/消融）、`_sensitivity`（灵敏度）、`_layout`（排布/路径）、`_mechanism`（机理，走路线②）。
- 角色按证据需要选，不凑齐；没有数据支撑的角色就不画。

## 五、闸门（不许自己「看着还行」）

```bash
python check_figures.py          # 退出码 0 = 无硬伤
python check_figures.py --json   # 机器可读
```

- 硬伤（压字、空面板、平线、双轴柱、图例压数据、重复系列、乱码）必须为 0 才进 S4。
- 闸门只覆盖 matplotlib 出的数据图；机理图/流程图不参与体检。
- 闸门看 `_figure_lint.json` 的 `saved_by`：`savefig` 记一条「未经 `save_publication`」提醒（裸 `plt.savefig` 也会写体检记录，别以为有记录就合规）；`data_*` 缺同名 `.pdf` 直接算硬伤 `no_vector_copy`。
- 闸门之外还要**目检**：`read_image` 打开成图看轴/图例/配色/字号，不满意就重画。

## 六、防乱码与防遮挡

- 中文字体：`apply()` 已配好；若某台机器缺宋体，自动回退到 Microsoft YaHei / SimHei。不要手写 `SimHei`（缺 `²`、`≥`、`□` 等字形，会打印 Missing glyph）。
- 轴标签带单位（`时间 t / s`、`质量分数 / %`）；图例、刻度全中文；图内标题按版式预设决定，去标题时把题意写进图题。
- `ax.annotate(文字, xy=(x, y), xytext=(12, 10), textcoords="offset points")`，偏移 ±40 点以内；**禁止把 `xytext` 写成远处的数据坐标** —— 文字会飞出坐标区，存图时画布被撑大，成图变成一大片空白配一根长箭头。
- x 轴长分类标签收尾用 `plot_style.tidy(fig)` 斜排。
- 图内只标 1–2 个关键数（AUC/R²/最优值/改进幅度写进图例或角标，柱顶/散点旁标数值）；不要把每个点都标一遍。

## 七、实测坑（这些是真踩过的）

| 坑 | 现象 | 正解 |
|---|---|---|
| `ax.boxplot(labels=...)` | matplotlib ≥3.9 报 `unexpected keyword` | 改 `tick_labels=` |
| 字体缺字 | `Missing glyph R□`（`R²` 印不出来） | 换 Microsoft YaHei 或 `apply()` 默认字体栈 |
| 图按 15 cm 嵌入后字太小 | 论文里看不清 | 先定插入宽度，再反推 `figsize`（如 15 cm ≈ 5.9 in，两侧留白后正文图 7–8 in 合适）；或减少面板数 |
| 图例压住标题/曲线 | 遮挡 | `legend_outside(ax)` 或 `figure_legend_above(fig, axes)`；去图内标题 |
| 3D 双格各挂一条色标 | 版面冗余 | 只在一格 `colorbar=True`，另一格 `colorbar=False` |
| 存成 PDF 后字体丢失 | 期刊要求矢量 | `save_publication(fig, stem)` 同时出 PNG + PDF，PDF 用 `pdf.fonttype=42` |
| dpi 过高文件巨大 | 论文超 10 MB | 正文图 260–300 dpi 足够；`apply(dpi=300)` 或 `save_publication(..., dpi=300)` |

## 八、plot_style API 速查

| 函数 | 用途 |
|---|---|
| `apply(dpi=, base_size=, palette=)` | 初始化全局版式（必备） |
| `combo_axes(n, rows=, projections=)` | 横排组图，`projections=("3d", None)` 混 3D |
| `mosaic_axes(["ab", "cccc"])` | 不规则拼图（上两格、下一排） |
| `response_surface(X, Y, Z, mark=)` | 双参数灵敏度 3D 曲面 |
| `series_style(名)` / `series_color(名)` | 多条曲线自动分色分线型，同名同色 |
| `role_color("ours")` / `role_style(...)` | 本文/对照/消融按角色取色 |
| `legend_outside(ax)` / `figure_legend_above(fig, axes)` | 图例移到坐标区外 / 合并置顶 |
| `tidy(fig, rotate=30)` | 刻度标签过长自动斜排 |
| `panel_labels(axes)` / `auto_panel_labels` | 补 (a)(b)(c) 面板标号 |
| `figsize(kind)` | 预设画布尺寸（`wide`/`square`…） |
| `lint_figure(fig)` | 手动体检，返回问题列表 |
| `save_publication(fig, stem)` | 存 PNG + PDF（带体检与和声化） |
| `strip_titles(fig)` | 一键去图内标题 |
