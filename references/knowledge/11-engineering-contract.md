# 11 · 建模工程契约（执行纪律，全程生效）

> 本文件是建模全流程的执行纪律硬约束，**与具体题型无关，S0–S4 全程生效。**

## 一、执行纪律

1. **无人值守**：不等待批准、不中途提问、不「先给方案就交差」。有歧义就先读完整题面与附件；仍消不掉时选**可验证且保守**的解释，把备选解释与假设写进 `reports/`，不静默猜测。
2. **边做边说**：过程用中文简述思路（一句话一步），不写成长篇；结论与数字才值得展开。
3. **禁止干耗**：一条命令跑完、输出在手就推进下一步；不 sleep 等结果、不轮询文件、不反复读同一份输出、不重复确认已知事实。
4. **子智能体分担**：检索、代码勘察、批量核对可交子智能体；最终求解脚本必须自己写、自己跑通。

## 二、目录与路径

```text
项目N/
├── code/          求解脚本（问题一.py / problem1.py，一题一文件）
├── data/          原始与中间数据（只读原始数据，清洗后另存）
├── figures/       全部成图（data_* / mech_* / paper_* / flow_*）
├── results/       results.json、tables/*.csv、logs/
├── reports/       各阶段报告
└── paper/         论文（LaTeX 模式）
```

- 路径一律按脚本自身定位：`ROOT = Path(__file__).resolve().parents[1]`，再 `ROOT / "figures"`、`ROOT / "results"`、`ROOT / "data"`。
- **禁止 `../figures/`、`../data/`**：工作目录一变就落到项目外，图和结果直接丢。
- 每个问题脚本 `python code/problem1.py` 能独立跑通，**不得 import 另一个 `problemN`**；复用逻辑进 `code/utils.py`（数据加载、指标、绘图）。
- 模块化按职责与复用关系决定，不按行数决定：跨题复用的进共享模块，只服务本题的内聚实现留在 `problemN.py`；不造空壳模块，不设行数目标。

## 三、解释器与依赖

- Windows 统一写 `python`（或绝对路径），**不写 `python3`**（常命中微软商店假入口，Exit 49）。
- 依赖自理：写代码前就把需要的库装齐，别等 `ModuleNotFoundError`；**装库与跑代码必须同一个解释器**。
- 本项目实测可用解释器：`E:\Scripts\python.exe`（含 matplotlib / statsmodels / sklearn / python-docx）。系统 `python` 若不在此路径，一律用全路径。
- 不升级破坏栈：`numpy` 保持现有版本（≥2.5 与 numba 冲突）；加速优先向量化 / scipy，装不上就换方案，不反复折腾版本。

## 四、先验后证据

1. **SMOKE 先行**：小规模跑通代码、数据流、指标定义，确认口径对了再上全量。
2. **生产规模**：结论必须由足以支撑 claim 的规模/重复次数/收敛判据决定，不设「十分钟上限」。方案里的方法是优先基线，不是不可违抗的命令 —— 若诊断显示不适配，可换或组合方法，但必须保留可比基线、记录依据、同步更新 `results.json` 与结论。
3. 不为无实质收益的百分点反复刷指标；也不为省事降级方法。

## 五、覆盖式迭代

初版结果先落 `figures/` 与 `results/`（界面立刻可见）；之后跑出更好的结果**覆盖同名文件**，不堆 `_v2` / `_final` / `_new`。文件名稳定，论文引用才稳定。

## 六、完成线（三条同时成立才算完）

- 「脚本退出码 0 + `results/` 有数 + `figures/` 有图」**只是可运行基线**，不是完成。
- 还要：逐条覆盖题目的得分点与 claim；做适用本题的基线/诊断/灵敏度或稳健性验证；`results` 的数字、图的结论、正文表述三者一致。
- 证据完整后停止低边际收益的微优化。新实验推翻原方案 → 修正方法与结论，不退回「能跑但明知不可靠」的版本。

## 七、长计算分阶段落盘

- SMOKE 规模只用于排错；最终样本数、种子数、epoch、网格、求解容差由收敛性/置信区间/稳定性/题目精度要求决定。
- 长实验分阶段保存 checkpoint 与中间表，先留下可恢复产物，再继续加规模；**禁止把所有 `savefig` 堆在长仿真末尾** —— 中途被打断不能只剩零产出。
- 不要用 `time` 包装长命令；直接前台 `python code/problemN.py`。
- 资源确实不足时才用近似方案，并量化误差或写明局限。

## 八、缓存不作废

`results/` 里已落盘的中间缓存（`*_partial.json`、`*_cache*.csv`）是断点续跑的依据：不改版本号/键名、不删缓存、不为调参把整表重训。只补缺的那组；确需改参数，只重算受影响的组合。

## 九、进程卫生

- 跑实验/装库/自检**一律前台**：不传 `run_in_background`、不用 `nohup` / 管道 `tee` 变相后台；等退出码与 stdout/stderr 回来再继续。
- 防挂死可以用 `timeout`（毫秒）——它只是到时杀进程，不算后台。
- 控制单次实验规模（种子数、网格、轮数适度），别开一堆并行重活拖垮机器。

## 十、文件写入与编码（Windows 实测坑）

| 坑 | 现象 | 正解 |
|---|---|---|
| `Set-Content -Encoding utf8` 写 JSON | 文件头多 BOM，Python `json.load` 报 `Unexpected UTF-8 BOM` | 用 `[System.IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding($false)))`，或直接用 Python 写 |
| pandas 读中文 CSV | `UnicodeDecodeError: gbk` | `pd.read_csv(path, encoding="gbk")` 先试，失败换 `utf-8-sig` |
| pandas 写 CSV 给 Excel 看 | Excel 里中文乱码 | `to_csv(path, encoding="utf-8-sig", index=False)` |
| PowerShell here-string 写代码 | `<<'PY'` 不被支持，且 heredoc 里的引号/反斜杠被吞（曾把整份脚本的 `f` 换成 `i`） | 用 `write` 工具写真实 `.py` 文件，再执行 |
| PowerShell 变量赋值 `$m=@{}` 拼字符串 | 花括号展开把字符吃掉 | 大段文本一律走文件写入，不在命令行拼 |

## 十一、库版本坑（踩过的）

- **matplotlib ≥3.9**：`ax.boxplot(labels=...)` 已移除 → 用 `tick_labels=`。
- **matplotlib 中文字体**：`SimHei` 缺 `²`/`≥`/上下标字形会打印 `Missing glyph R□` → 换 `Microsoft YaHei`；统一走 `plot_style.apply()`，不要自己设 `font.family`。
- **pandas 3.x**：`dict_keys` 不可直接索引 → 先 `list(...)`；`df.isna().sum().reindex([...])` 遇未命中索引返回 NaN → 先 `rename` 索引再取。
- **python-docx**：设置中文字体必须写 `w:rFonts` 的 `w:eastAsia`，只设 `run.font.name` 中文不生效（见 `assets/templates/docx/report_kit.py`）。
- **Word COM（comtypes）**：`Document.Fields.Update()` 更新目录/页码域后再 `SaveAs2(pdf)`；无 Word 时 PDF 由 LibreOffice 兜底。

## 十二、收工自查

1. 所有脚本从头跑一遍退出码 0（不是「应该能跑」）。
2. `results/results.json` 有全部关键数值；`figures/` 里每张图都有生成脚本。
3. 论文里每个数字都能指到 `results.json` 的键；每张图都在 `figures/manifest.json`。
4. 得分点逐条勾：方法/公式/数值/图/表/检验，缺哪条补哪条。
5. 无 `TODO`、无 `pass`、无伪代码、无占位符、无内部文件名泄漏。
