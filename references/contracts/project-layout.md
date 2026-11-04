# 项目骨架契约

每个建模项目独立建目录，建议 `项目N/`。

```text
项目N/
├── plan.md
├── todo.md
├── input/                       # 题面、附件、原始数据（只读）
├── reports/
│   ├── ENV_REPORT.md
│   ├── ANALYSIS_MODELING_REPORT.md
│   ├── symbols.md                # 符号表（S1 定稿，S2/S3/S4 照抄）
│   ├── SCORE_MAP.md              # 得分点 → 证据 → 公式/图/表号（S2 建表，S4 补落点）
│   ├── RESULTS_REPORT.md
│   ├── journal_problemN.md       # 每问一份：关键数值/图表结论/结果表格/结论核对/遗留
│   ├── FIGURE_REPORT.md
│   ├── REVIEW_REPORT.md          # 评委式评审
│   ├── BUILD_REPORT.md           # 编译报告
│   ├── DOCX_EXPORT_REPORT.md     # 可选
│   └── 术语表格.md
├── code/
│   ├── problem1.py ... problemN.py
│   ├── utils.py
│   ├── plot_style.py             # 从 assets/style/ 复制，不修改
│   ├── requirements.txt
│   ├── README.md
│   └── outputs/
├── check_figures.py              # 出图闸门（从 assets/style/ 复制）
├── run_all.py                    # 批量跑 code/（从 assets/scaffold/ 复制）
├── results/
│   ├── results.json
│   ├── tables/*.csv
│   └── logs/
├── figures/
│   ├── data_*.pdf/.png
│   ├── mech_*.tex/.pdf/.png
│   ├── paper_*.svg/.pdf/.png
│   ├── flow_*.tex/.pdf/.png
│   ├── _figure_lint.json         # 闸门结果
│   └── manifest.json
├── paper/                       # LaTeX 模式（默认 default 模板）
│   ├── main.tex
│   ├── format.cls
│   ├── fonts/
│   ├── 0.摘要.tex … 11.附录.tex
│   ├── main.pdf
│   └── 论文.docx                # 可选改稿副本
├── report/                      # Word 模式
│   ├── reference.docx            # 模板副本
│   ├── 数据分析报告.docx
│   └── 数据分析报告.pdf          # 可选预览
```

交付形态二选一：LaTeX 模式用 `paper/`，Word 模式用 `report/`；不要同时把两套都当权威版本。

## 命名

| 类型 | 规则 | 示例 |
|---|---|---|
| 代码 | `problem<题号>.py` | `problem1.py` |
| 数据图 | `data_q<题号>_<内容>.pdf` | `data_q1_convergence.pdf` |
| 机理图 | `mech_<内容>.pdf` | `mech_feasible_region.pdf` |
| 论文主图 | `paper_<内容>.svg` | `paper_roadmap.svg` |
| 流程图 | `flow_q<题号>_<内容>.tex` | `flow_q1_solution.tex` |
| 结果表 | `results/tables/q<题号>_<内容>.csv` | `q1_solution.csv` |

## 规则

1. `input/` 原样保存，不修改。
2. 所有数值以 `results/results.json` 为准。
3. 所有图以 `figures/manifest.json` 为准。
4. 论文正文不出现内部文件名。
5. 临时文件放 `code/outputs/` 或 `results/logs/`，不散落在根目录。
6. 不做自动验收与提交打包。
