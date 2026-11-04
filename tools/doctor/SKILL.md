---
name: doctor
description: 数学建模 Pro 环境检查。用于“检查环境 / 缺什么依赖 / 为什么编译失败”等任务。检查 Python 包、xelatex、pandoc、pdftoppm、字体与 LaTeX 模板，输出 ENV_REPORT.md。
---

# 环境检查

## 使用

```bash
python scripts/doctor.py
python scripts/doctor.py --project 项目1
python scripts/doctor.py --json
```

`--project` 会把报告写入 `项目1/reports/ENV_REPORT.md`。

## 检查项

| 类别 | 内容 |
|---|---|
| 命令 | xelatex、pandoc、pdftoppm、pdftotext、pdfinfo、drawio（可选） |
| Python 包 | numpy、pandas、matplotlib、scipy、sklearn、openpyxl、python-docx、pypdf、fitz、PIL |
| 字体 | 宋体、黑体、楷体、Times New Roman、Arial |
| 模板 | CUMCMThesis、MCM、华为杯、通用 |

## 判定

- 必选项缺失 → 退出码 1，不进入 S1，先安装或降级。
- 可选项缺失 → 记录，不阻塞主流程。
- 不静默安装；安装命令只作建议。

## 常见安装

```powershell
winget install MiKTeX.MiKTeX
winget install JohnMacFarlane.Pandoc
winget install oschwartz10612.poppler
```

字体缺失时，安装宋体/黑体/楷体/Times New Roman，或在模板中改用已安装字体。

## 边界

- 不检查论文内容。
- 不生成论文或报告。
- 不自动修改系统环境。
