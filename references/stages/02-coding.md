# S2 代码实现（编程手）

## 进入条件（先看这条，再往下读）

**S1 报告没过 G1 就不许开始写模型代码。** 开工前先确认三件事，缺一件先回 S1：

1. `reports/ANALYSIS_MODELING_REPORT.md` 已落盘，且七件套齐全；
2. `reports/QC_S1_ROUND.1.md`、`.2.md`、`.3.md` 三份留痕的结论行都是 `结论：PASS`；
3. `reports/symbols.md` 已定稿（代码变量名照它取）。

**报告是唯一口径**：代码里出现的每个公式都必须能指回报告的一节；实现时发现报告缺参数、缺边界条件，先补报告再改代码，不许在代码里私设一个值了事——那个值到 S4 就没人认领了。

## 目标

把 `reports/ANALYSIS_MODELING_REPORT.md` 落实为可复现代码，跑出可信结果，生成数据图，并把所有关键数值写入 `results/results.json`。

## 输入

- `reports/ANALYSIS_MODELING_REPORT.md`（含得分点表与证据链表）
- `reports/symbols.md`（符号表；代码里的变量名与物理量一律照它取，符号改了要回写这张表）
- `plan.md`（子问题数、语言、交付形态；子问题数与 `problemN.py` 数量必须一致）
- `reports/术语表格.md`（变量命名与注释用词跟它对齐，中英稿共用一套）
- `input/` 数据
- `references/knowledge/11-engineering-contract.md`（**执行纪律、路径、编码、库版本坑**）
- `references/knowledge/12-scoring-validation.md`（得分点核账与验证强度）
- `references/knowledge/14-figure-contract.md`（`plot_style` + 出图闸门）
- `references/algorithms/`
- `tools/figure-templates/`
- `assets/style/`、`assets/scaffold/run_all.py`

## 步骤

### 1. 建代码骨架

```text
code/
├── problem1.py
├── problem2.py
├── problem3.py
├── utils.py            # 数据加载/清洗、共用指标、绘图工具
├── plot_style.py       # 从 assets/style/ 复制，不修改
└── outputs/
```

项目根另放 `check_figures.py`（从 `assets/style/` 复制）与 `run_all.py`（从 `assets/scaffold/` 复制）。

子问题数量按题面调整，不硬凑三个。路径一律 `ROOT = Path(__file__).resolve().parents[1]`，禁止 `../figures/`。

### 2. 逐子问题实现

每个子问题必须完成：

1. 读取数据；
2. 实现模型/算法；
3. 验证约束；
4. 输出核心结果；
5. 绘制数据图；
6. 写 `reports/RESULTS_REPORT.md`。

题型要求：

- 优化：先保证可行解，再优化目标；记录目标值、gap、约束违反数。
- 预测：训练/验证划分；记录 MAE/RMSE/MAPE/R² 等。
- 评价：说明指标方向、归一化方法、权重来源；记录排序与得分。
- 机理/仿真：说明参数、初值、边界、守恒量、稳定性。

### 3. 结果 JSON（必须）

写入 `results/results.json`，格式见 `references/contracts/results-schema.md`。

要求：

- 关键指标全部有键名；
- 单位写清；
- 随机种子固定；
- 中间数据保存到 `code/outputs/` 或 `results/tables/`；
- 图表所用数据必须能追溯。

### 4. 数据图（路线 ①）

按 `14-figure-contract.md` 执行，不要自创风格：

```python
from plot_style import apply, combo_axes, figure_legend_above, save_publication
apply()                                    # 必备第一行：中文字体 + 期刊配色
fig, axes = combo_axes(2)                  # 横排组图，不竖堆
...
save_publication(fig, "data_q3_fit")       # 同时出 PNG + PDF，并自动体检
```

- 输出 `figures/data_*.png`（≥260 dpi）与 `.pdf`（矢量）；
- 图内不写大标题，标题交给图题；轴标签带单位，图例全中文；
- 图内只标 1–2 个关键数；数据铺满时 `legend_outside(ax)` 或 `figure_legend_above(fig, axes)`；
- 出完图跑闸门：`python check_figures.py`，硬伤必须为 0，再 `read_image` 目检；
- 可用 `tools/figure-templates` 的模板，但**必须换成项目真值**，禁止交模板自带模拟数据的复刻图。

### 5. 校验、灵敏度与得分点核账

- 约束校验：可行解数量、违反量、边界；
- 数值校验：与解析解/小规模枚举/历史结果对比；
- 灵敏度：关键参数 ±10% / ±20% 或规模扫描，**真实重跑**，结果写入 `results.json` 的 `sensitivity` 字段；离散扰动改三线表，密采样画响应曲线；
- **得分点逐条核账**：对 `reports/ANALYSIS_MODELING_REPORT.md` 的得分点表逐行勾 —— 要的数值在 `results` 里吗？要的图画了且角色命名对吗？要的对比真跑了吗？缺口现在补，S4 再发现就只能承认局限；
- 每问跑通后立刻写 `reports/journal_problemN.md`：关键数值 / 图表结论 / 结果表格 / 结论核对 / 遗留。

编码坑（BOM、gbk、pandas 3.x、matplotlib 3.9+、docx 字体）见 `11-engineering-contract.md` 第十至十一节，写代码前扫一眼。

### 6. 可复现

- `requirements.txt` 或环境说明；
- 固定随机种子；
- 运行命令写入 `README.md`；
- 输出日志到 `results/logs/`。
- **print 只用 GBK 可编码的字符**：控制台是 cp936 时，打印 `f̂`(U+0302)、`✅`、`θ̂` 这类字符会直接 `UnicodeEncodeError` 把脚本打挂（实测踩过）。要打印特殊符号就写 ASCII（`f_hat`、`[OK]`），或在脚本头加 `sys.stdout.reconfigure(errors="replace")`。
- **numpy ≥ 2.0 删了 `np.trapz`**：改 `np.trapezoid`；别把加速度二次积分当位移（会漂移出假位移），用状态递推积分。

## 必须产出

- `code/` 可运行代码（`run_all.py` 从头跑一遍退出码全 0）
- `results/results.json`
- `results/tables/*.csv`
- `figures/data_*.pdf/.png` + `figures/_figure_lint.json`
- `reports/RESULTS_REPORT.md`
- `reports/journal_problemN.md`（每问一份）
- `reports/SCORE_MAP.md`（得分点 → 证据 → 承载物；S2 建表，S4 补公式号/图号/表号）
- `code/README.md`

## 边界

- 不画机理图、论文主图、流程图（交给 S3）。
- 不写论文正文。
- 不修改分析报告的模型口径；如必须改，回写分析报告并说明。
- 不后台跑长任务、不删已有缓存、不堆 `_v2/_final` 版本文件。

## 门禁

通过 `references/checklists/G2-coding.md` 后进入 S3。
