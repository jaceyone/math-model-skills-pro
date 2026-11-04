---
name: xlsx
description: 读、写、重算 Excel 数据表。用于“读附件 xlsx / 写结果表 / 重算公式 / 检查表格数字”。不用于做财务报表或套模板。
license: Proprietary. LICENSE.txt has complete terms
---

# Excel 数据表（读 / 写 / 重算）

数模里只做三件事：**把附件读成 DataFrame → 把结果写成表 → 公式要对得上**。

## 1. 读

```python
import pandas as pd

xl = pd.ExcelFile("data/附件1.xlsx")
print(xl.sheet_names)                       # 先看有哪些表
df = pd.read_excel(xl, sheet_name="Sheet1", header=0)
df = df.dropna(how="all")                   # 去掉尾部空行
```

- 多表附件逐表读，别只读第一张。
- 合并单元格会读成 `Unnamed: n`，先 `ffill()` 或按题面人工对齐。
- 数字被存成文本（`'12.5'`）时 `pd.to_numeric(errors="coerce")` 后统计缺失。

## 2. 写

```python
from openpyxl import load_workbook

wb = load_workbook("results/结果表.xlsx")     # 改表用 load，别新建覆盖
ws = wb["汇总"]
ws["B2"] = 0.8731
wb.save("results/结果表.xlsx")
```

- 新建表用 `pd.DataFrame(...).to_excel(path, index=False)`。
- 只写数值，格式（列宽、小数位）交给 `openpyxl.styles`。
- 进论文的表用 `df.to_latex(index=False, float_format="%.4f")`，套 `booktabs` 三线表。

## 3. 重算公式

openpyxl 只写公式、不算值；读回来前先重算：

```bash
python tools/xlsx/scripts/recalc.py results/结果表.xlsx 60
```

- 依赖 LibreOffice（`soffice`）；输出 JSON：`status` / `total_errors` / `error_summary`。
- `status: errors_found` 时按 `#VALUE! / #REF! / #DIV/0!` 定位到单元格再改。
- 没有 LibreOffice 时：公式改写成 Python 算，再把**数值**写进表。

## 4. 常见坑

- 只写公式不重算 → 论文里引用到空值。
- 表头有子行（两行表头）→ 读的时候 `header=[0,1]`。
- 列名带空格/换行 → 读取后统一 `df.columns = df.columns.str.strip()`。
- 单位混用（mg/L 与 g/L）→ 读入即统一，写进 `plan.md`。
- 结果表与 `results.json` 数值不一致 → 以脚本输出为准，重出表。

## 验收

- [ ] 每个附件都读过，字段与单位写进 `plan.md`
- [ ] 结果表的数来自脚本输出，不是手抄
- [ ] `recalc.py` 返回 `success`，或已确认无公式
- [ ] 进论文的表是 `booktabs` 三线表，列宽不溢出
