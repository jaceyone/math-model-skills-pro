# Word 报告模板与排版工具箱

赛题强制 Word 时用（S4 Word 原生分支）。**不要**先写 LaTeX 再 `latex2docx.py` 导出。

## 文件

| 文件 | 用途 |
|---|---|
| `reference.docx` | 空白模板：A4、2.5 cm 页边距、宋体/Times、1.5 倍行距、内置样式齐全 |
| `report_kit.py` | 排版工具箱：`Report` 类封装样式、三线表、图题、公式编号、页眉页脚、目录域 |

## 最小用法

```python
from pathlib import Path
from report_kit import Report

r = Report(Path("report/reference.docx"))        # 模板副本
r.cover("赛事名", "报告标题", "副标题", [("组别", "…"), ("姓名", "…")])
r.p("摘要正文……")                                # 正文段落（首行缩进 2 字符）
r.toc()                                          # 目录域（打开后按 F9 更新）
r.h1("一、项目概述", page_break=True)             # 一级标题另起一页
r.rich([("关键指标 ", {}), ("R² = 0.375", {"bold": True})])   # 句内加粗
r.csv_table("q3_coef", "回归系数表", widths=[4, 6, 3, 3], nd=3, note="注：…")
r.fig("data_q2_corr", "特征相关性热力图", width=15)            # 从 figures/ 取 PNG
r.eq("y = \\beta_0 + \\beta_1 x_1 + \\cdots + \\varepsilon")   # 自动编号 (1)
r.save(Path("report/数据分析报告.docx"))          # 自动置 updateFields
```

## 约定与坑

- `ROOT = Path(__file__).resolve().parent.parent`：把 `report_kit.py` 放在 `code/` 下，`figures/`、`results/` 才找得到。
- 中文字体必须写 `w:rFonts` 的 `w:eastAsia`，只设 `run.font.name` 中文不生效 —— 工具箱已处理，别绕过它自己设字体。
- 表格：`table()` 已内置三线表、表头重复、NaN→空、≤8 行防跨页；宽表给 `widths`，12 列以上用短表头 + `note=`。
- 图：`fig(width=15)` 是正文满宽；多图并排改成 12–13.4；图内不要 `set_title()`，标题交给图注。
- 分页：用 `h1(..., page_break=True)`（内部是 `page_break_before`），**不要**再 `add_page_break()`，否则出空白页。
- 目录/页码：`toc()` 与页脚 `PAGE` 都是域，交付前必须更新（Word COM：`doc.Fields.Update()`，或打开后 Ctrl+A、F9）。
- 页数核对：导出 PDF 后与 DOCX 比对，页数应一致。
