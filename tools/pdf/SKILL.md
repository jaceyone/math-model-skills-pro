---
name: pdf
description: 读取 PDF 题面/论文：提取文本、表格、图片，把页面渲染成 PNG。用于“读题面 PDF / 提取 PDF 文字 / PDF 转图片”。不用于填表、合并拆分、加水印、加密。
license: Proprietary. LICENSE.txt has complete terms
---

# 读 PDF（题面 / 参考论文）

数模里只有四件事：**提取文字 → 提取表格 → 页面转图 → 看扫描件**。别的 PDF 编辑需求不归本工具。

## 1. 先定类型

```bash
# 有文字层的 PDF
pdftotext -layout 题目.pdf - | head -60

# 扫描件／图片型：抽不到字就转图
pdftoppm -r 150 -png 题目.pdf pages/题目
```

## 2. 提取

| 要什么 | 用什么 | 命令 |
|---|---|---|
| 正文文字（保版式） | `pdftotext -layout` | `pdftotext -layout in.pdf out.txt` |
| 表格 | pdfplumber | `page.extract_tables()` |
| 图片 | pypdf / pdfplumber | `page.images` / `page.to_image()` |
| 页面图片 | 本工具脚本 | `python tools/pdf/scripts/convert_pdf_to_images.py in.pdf out_dir/` |
| 字体/是否嵌字 | pdffonts | `pdffonts in.pdf` |

`convert_pdf_to_images.py` 用 pdf2image（需 poppler），DPI 固定 200，长边压到 1000 px，输出 `page_1.png`…

## 3. 读题流程

1. `pdftotext -layout` 出全文，先通读题面与附件说明；
2. 表格在 PDF 里时用 pdfplumber 抽，别手抄；
3. 只有图片时转 PNG 逐页看，把关键约束抄进 `plan.md`；
4. 数据附件另存到 `data/`，列清字段与单位。

## 4. 常见坑

- `pdftotext` 排序乱：加 `-layout`；双栏论文加 `-raw` 对比。
- 抽出中文变方块：PDF 字体未嵌字，转图看。
- pdfplumber 抽表要指定 `table_settings`，否则整页当一张表。
- 扫描件 OCR 不在本工具范围；先转图，再人工核对关键数字。

## 验收

- [ ] 题面每问的输入、输出、约束都落到了 `plan.md`
- [ ] 附件数据与题面字段一一对应，无漏列
- [ ] 引用的数字能在原文定位到页
