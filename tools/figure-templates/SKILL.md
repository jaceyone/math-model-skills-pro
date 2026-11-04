---
name: figure-templates
description: 数学建模数据图模板库。用于“画 SHAP / ROC / 泰勒图 / 云雨图 / 相关矩阵 / 环形热图 / 和弦图 / 3D 曲面”等科研图表。内置 11 个可运行 matplotlib 模板，输出 PNG/PDF/SVG。只做数据图，不画流程图/机理图/技术路线图。
---

# 科研数据图模板（11 个）

## 定位

本工具属于四路图件的 **① 数据图**。输入必须是真实结果数据；模板只提供版式，不提供结论。

## 模板清单

| id | 图 |
|---|---|
| `multiclass-shap-combo` | 多分类 SHAP 柱状图 + 蜂群图 |
| `paired-raincloud` | 配对云雨图 |
| `cv-roc-ci` | 交叉验证 ROC + 置信区间 |
| `taylor-diagram` | 多模型泰勒图 |
| `correlation-pairgrid` | 分布 + 拟合线 + 相关系数组合 |
| `prediction-marginal-grid` | 预测值/真实值边缘分布 |
| `rf-tpe-surface` | TPE 优化 RF 3D 曲面 |
| `grouped-corr-split-violin` | 下三角相关矩阵 + 分组小提琴 |
| `grouped-circular-heatmap` | 分组环形热图 |
| `urban-park-cooling-combo` | 堆叠图 + 云雨图 + 箱线图 |
| `nature-chord-diagram` | Nature 风格和弦图 |

详细说明：`references/figure-catalog.md`、`references/plot-recipes.md`。

## 使用

```bash
python tools/figure-templates/scripts/render_template.py --list
python tools/figure-templates/scripts/render_template.py paired-raincloud --project code/figure_workspace
```

输出在 `code/figure_workspace/outputs/`，包含 PNG/PDF/SVG。

### 接入论文

1. 先跑模板看版式；
2. 把生成的 `scripts/make_*.py` 复制到 `code/`；
3. 替换为本题真实数据（不要用模板的模拟数据）；
4. 输出到 `figures/data_<题号>_<内容>.pdf` 与 `.png`；
5. 登记 `figures/manifest.json`（route=`data`）。

## 规则

- 模板默认用模拟数据，只用于看版式；**不得把模拟数据结果写进论文**。
- 图内不写大标题，标题交给论文 caption。
- 中文论文用中文坐标轴/图例；英文论文用英文。
- 每问 1–2 张核心图，不堆图。
- 颜色不超过 3 个主色；同一论文风格统一。
- 输出优先 PDF 矢量；PNG 仅预览。

## 边界

- 不画流程图（`flowchart`）。
- 不画机理图（`mechanism-diagram`）。
- 不画技术路线图（`paper-figure`）。
- 不编造数据；没有真实结果就不画。
