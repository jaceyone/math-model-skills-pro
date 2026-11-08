# 流程串联契约：每个产物都必须有人读

> 一句话：**产物没有消费者就是垃圾，输入没有生产者就是幻觉。**
> 本文件是全流程唯一的串联表。阶段文档只写"我产出什么、我读什么"，不再各自解释上下游；判据与口径只在这里汇总指向。

## 一、产物闭环表

| 产物 | 生产者 | 消费者 | 门禁 | 断链后果 |
|---|---|---|---|---|
| `plan.md` | S0 | S1 拆题、S2 子问题数/语言、S3 图数档位、S4 模板与语言/AI 声明、G4 | G0 | 语言/模板/页数口径各写各的；AI 声明只能凭记忆编 |
| `todo.md` | S0 | S0–S4 全程 | G0 | 卡在哪个阶段说不清 |
| `reports/ENV_REPORT.md` | S0 `scripts/doctor.py` | 报错时回查，不阻塞 | G0 | — |
| `reports/QC_S1_ROUND.1..3.md` | S1（三轮回质检） | S2 开工前的准入、S4 回改时查"这条结论当初怎么过的" | **G1（硬门禁：缺一轮不许进 S2）** | 报告没验就用，S2 与 S4 两张皮 |
| `results/schema.json` | **S1（写代码之前立键）** | S2 代码照着填、S3 数据图取键、S4 表格与正文取值、`check_contract.py`、`check_results.py` | **G1（缺它不许写代码）** | 键名事后凑，代码算一堆没人要的中间量 |
| `reports/tables/*.tpl.md` | **S1（表格骨架）** | `scripts/fill_tables.py`、`check_contract.py` | **G1** | 表只能手抄，S4 与结果两张皮 |
| `results/tables/*.md\|.tex` | **S2 `scripts/fill_tables.py`** | S4 论文 `\input`、md 报告、`check_results.py` 新鲜度校验 | **G2 / G4** | 手抄表，重跑代码后表不更新 |
| `results/tables/_render.json` | `scripts/fill_tables.py` | `check_results.py` 追溯"哪张表用了哪些键" | G2 | 表与键的对应关系说不清 |
| `reports/ANALYSIS_MODELING_REPORT.md` | S1 | S2 实现口径、S3 图件规划、S4 章节骨架 | G1 | 代码与论文模型不一致 |
| `reports/symbols.md` | S1 | S2 变量名、S3 图内标注、S4 符号说明章 | G1 | 代码/图/正文三套符号 |
| `reports/术语表格.md` | S1 | S2 变量命名与注释、S4 中英对照 | G1 | 中英稿术语漂移 |
| `reports/图件规划.md` | S1 | S3 出图、`check_contract.py`（数据图 `reads:` 校验） | G1 | 图凑数或漏关键图；数据图不知道该读哪个键 |
| `code/`、`results/results.json` | S2（只填 schema 里声明过的键） | S3 数据图、S4 全部数值、`fill_tables.py` | **G2（`check_results.py`）** | 数值凭记忆写 |
| `reports/RESULTS_REPORT.md` | S2 | S4 | G2 | 结论与数据脱节 |
| `reports/journal_problemN.md` | S2 | S4 逐图逐表摘抄 | G2 | 图注与图内容对不上 |
| `reports/SCORE_MAP.md` | S1 立点，S2 核账，S4 补落点列 | S4、G4 | G1/G2/G4 | 得分点无处验收 |
| `figures/_figure_lint.json` | S2 `plot_style.save_publication` | `check_figures.py` | G2 | 出图闸门形同虚设 |
| `figures/manifest.json` | S3 `scripts/make_manifest.py` | S4（只许引这里的图）、G3 | G3 | 引了不存在的图 |
| `reports/FIGURE_REPORT.md` | S3 | S4 | G3 | 图与正文两张皮 |
| `paper/main.pdf` | S4 | `scripts/build_paper.py` | G4 | 页数/引用错误无人管 |
| `reports/BUILD_REPORT.md` | `scripts/build_paper.py` | S4 回改、G4 | G4 | 编译错误带进终稿 |
| `reports/REVIEW_REPORT.md` | `tools/review`（可选） | S4 按 P0/P1 回改 | G4 终稿前 | 评审结论不落地 |
| `report/数据分析报告.docx` | S4 Word 分支 | 交付 | G4 | — |
| `results/numbers_allow.txt` | S4（`check_paper.py --update-allow` 生成，人工补注释） | `check_paper.py` | G4 | 派生量无处申报，只能混进正文 |
| `paper/references.tex` | S4（`\bibitem` 键 + 完整出版信息） | `\cite`、`check_paper.py` | G4 | 手写条目 = 没有引用，角标对不上 |

## 二、三条硬规则

1. **无消费者不产出**：新增任何 `reports/*.md`，必须在本表登记"谁读、读来干什么、哪道门禁看它"；登记不上就不写。
2. **无生产者不引用**：阶段文档写"读 X"，X 必须在本表有生产者；没有就先补生产者，不许靠记忆补内容。
3. **口径单点定义**：同一件事只在一处定义，别处只写"见 X"，不复述。

## 三、口径单点定义表

| 口径 | 唯一定义处 | 别处怎么写 |
|---|---|---|
| 四路图件与选路判据 | `knowledge/05-figures.md` | `SKILL.md`、`03-figures.md` 只列路线名，不复述判据 |
| 模板选择 | `stages/04-writing.md` §1 | `SKILL.md` 表格标"详见 04" |
| 章节链与逐章写法 | `knowledge/10-chapter-writing-prompts.md`（独立口径库，不绑定模板） | 别处不重复列章节顺序；与 `default/sections` 的映射见 `stages/04-writing.md` §2 |
| 页数口径 | `knowledge/13-writing-injection.md`（赛制档位） | G4 只写"符合档位" |
| 表格列宽 | `knowledge/10-chapter-writing-prompts.md`【列宽记账】 | 模板与门禁只引不复述 |
| 表格骨架/占位符/生成 | `contracts/table-template.md` | 阶段文档只写"用 `fill_tables.py`"，不复述语法 |
| 数值 | `results/schema.json` 立键 → `results/results.json` 存值（派生量在 `results/numbers_allow.txt` 申报） | 全文引用，不复制 |
| 表格 | `reports/tables/*.tpl.md`（骨架）+ `scripts/fill_tables.py`（生成） | 论文只 `\input{../results/tables/*.tex}`，不手抄 |
| 图 | `figures/manifest.json` | 正文只写 `\ref` |
| 文献 | `paper/references.tex`（`\bibitem` 键 + 出版信息） | 正文只写 `\cite{key}` |
| 符号 | `reports/symbols.md` | 代码变量名、图内标注、符号说明章一律照抄 |
| 得分点 | `ANALYSIS_MODELING_REPORT.md` 的得分点表 | `SCORE_MAP.md` 只加"落点"列，不改得分点措辞 |

## 四、每次推进前的五个自检

1. **孤儿检查**：列 `reports/` 下每个文件，逐个回答"谁读它"；答不出的删掉或补消费者。
2. **缺口检查**：把本阶段文档「输入」里的每个路径 grep 一遍，找不到生产者的当场补。
3. **落点检查**：每个得分点在 `SCORE_MAP.md` 里都有公式号/图号/表号；G4 逐条点名，缺一条不算过。
4. **机器校验**：`python scripts/check_paper.py --project 项目N` 退出码 0 —— 数字全部指回 `results.json`，`\cite` 与 `\bibitem` 一一对应。
5. **契约检查**：`python scripts/check_contract.py --project 项目N`（G1，退出码 0）与 `python scripts/check_results.py --project 项目N`（G2，退出码 0）—— schema 键全填、表不是手抄的、未申报键已收口。
