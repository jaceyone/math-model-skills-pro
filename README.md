# 数学建模 Pro v2.3.23

数学建模竞赛工作流：**5 阶段 + 5 门禁 + 四路图件**。默认主链路 **LaTeX → PDF**（默认模板 `default`，`ctexart`）；赛题强制 Word 时走 **Word 原生分支**，不经过 LaTeX。

## 特性

- **5 阶段**：启动 → 建模分析 → 代码实现 → 图件制作 → 论文撰写。
- **5 门禁**：每阶段有可勾选清单，不达标不进入下一阶段。
- **写作提示词独立成库**：17 节逐章口径在 `references/knowledge/10-chapter-writing-prompts.md`，按「章」组织、不绑定模板文件名；`default/main.tex` 顶部另有 6 条写作提示。模板章节名不同时按 `references/stages/04-writing.md` §2 的映射表落地。
- **写作口径可追溯**：人称、断句、禁 AI 高频词、去 AI 味 10 条自查，口径参考开源项目 `XiaoMaColtAI/math-modeling-skill` 的《论文手说明》，落地为模板注释块与 `references/knowledge/13-writing-injection.md` 第七节。
- **四路图件**（路径与执行顺序见 `SKILL.md` 同名小节）：
  - 数据图：`plot_style`（中文字体 + 9 套期刊配色 + 组图 API）+ `check_figures.py` 闸门 + 11 个科研图模板；
  - 机理图：TikZ，12 类，`xelatex` → `pdfcrop`（可跳过）→ `pdftoppm`，中文图只出 PDF+PNG；
  - 论文主图：5 张实拍母版 → SVG → `render_figure.py` → PDF/PNG；
  - 流程图两条路线：**A · TikZ**（`flow_*.json` → `tools/flowchart/scripts/flowchart.py` → PDF/PNG，进 LaTeX 论文）与 **B · SVG**（`flow_*.svg` → `tools/flowchart/scripts/svg_flow.py` → 可编辑 HTML + PNG/PDF，可在浏览器里直接改字），独立成路、互不混用。

- **LaTeX 模板**：default（默认，`ctexart`：摘要/目录/8 章/参考文献/附录）、MCM（英文）、华为杯；用户自带模板可直接替换。
- **Word 原生报告**：`reference.docx` + `report_kit.py`（三线表、目录/页码域、公式编号、题注），产出 `report/数据分析报告.docx`。
- **得分点驱动**：S1 立可核验得分点 → S2 逐条核账补证据 → S4 落到公式号/图号/表号。
- **数值可追溯**：`results/results.json` 是唯一事实源。
- **图件可追溯**：`figures/manifest.json` 登记每张图的来源、数据、章节、宽高比。
- **LaTeX → Word 改稿**：仅 LaTeX 模式使用 Pandoc + python-docx，带差异报告。
- **论文搜索**：Crossref + arXiv 双源，缓存、去重、DOI 校验。
- **评委式评审**：100 分结构、格式质量系数、P0–P3 问题、优先提分建议（`tools/review`）。

## 快速开始

```text
/math-modeling-pro 帮我做这道数学建模题
```

> 脚本路径相对于技能根目录；若在项目目录运行，使用 `python <skill-root>/scripts/xxx.py --project 项目N`。

分阶段：

```text
/math-modeling-pro 进行建模分析
/math-modeling-pro 进行代码实现
/math-modeling-pro 画技术路线图
/math-modeling-pro 画问题一求解流程图
/math-modeling-pro 进行论文撰写
/math-modeling-pro 第五章模型的建立怎么写
/math-modeling-pro 写 Word 报告（赛题强制时）
/math-modeling-pro 评审论文，看看能拿多少分
```

## 目录

```text
math-modeling-pro/
├── SKILL.md                 # 入口路由
├── references/
│   ├── stages/              # 5 份阶段手册
│   ├── contracts/           # 产物契约
│   ├── checklists/          # G0–G4 门禁
│   ├── knowledge/           # 建模规范 + 现役口径 10–14
│   └── algorithms/          # 7 类算法库
├── assets/
│   ├── templates/latex/     # 3 套 LaTeX 模板（default 为默认，另 MCM / 华为杯）
│   ├── templates/docx/      # Word 模板 + report_kit.py
│   ├── style/               # plot_style.py、check_figures.py
│   ├── scaffold/            # run_all.py
│   └── figures/             # 精选参考图
├── tools/
│   ├── doctor/ pdf/ xlsx/
│   ├── paper-search/
│   ├── mechanism-diagram/
│   ├── paper-figure/
│   ├── flowchart/
│   ├── figure-templates/
│   └── review/
├── scripts/
│   ├── doctor.py
│   ├── build_paper.py
│   ├── check_paper.py
│   ├── check_links.py
│   ├── latex2docx.py
│   └── make_manifest.py
```

## 环境

| 功能 | 依赖 |
|---|---|
| LaTeX 编译 | MiKTeX / TeX Live（xelatex） |
| 数据图 | Python + numpy / pandas / matplotlib / scipy / scikit-learn |
| 机理图 / 流程图 | xelatex + TikZ |
| 论文主图 | Python + Edge（SVG→PNG/PDF） |
| Word 报告 / 导出 | python-docx、comtypes（Word COM）、Pandoc 3.10+、pdftoppm |
| 论文搜索 | Python 标准库，无 API Key |

> `default` 模板走 `fontset=windows`（系统宋体/黑体/楷体），不依赖模板自带字体；macOS 改 `fontset=mac`。

检查环境：

```bash
python scripts/doctor.py
```

## 编译与导出

```bash
python scripts/build_paper.py --project 项目1
python scripts/latex2docx.py --project 项目1
```

## 版本

当前 `2.3.23`。详见 `CHANGELOG.md`。第三方资产见 `VENDORED.md`，使用限制见 `LICENSE_NOTICE.md`。
