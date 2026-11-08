# 变更记录

> **读法**：本文件按时间倒序记「当时改了什么」，条目里的路径写的是**改动发生时的目录结构**。
> 其后被改名、合并或删除的路径（`workshop/`、`cumcmthesis/`、`scripts/build_prompts.py`、
> `scripts/verify_paper.py`、`references/roles/`、旧的 `knowledge/06`–`09` 编号等）**不会回改**——
> 想核对某个路径现在在哪，看 `SKILL.md` 的索引，不要照本文件的历史条目去找。
> 自动核对：`python scripts/check_links.py`（只看现役文档）；加 `--all` 会连本文件一起查，
> 历史条目报失联属预期。

## 2.5.0 — 技能自检 + 算法库可跳读（按 skill-creator 的包规范体检）

> 触发：拿 anthropics/skills 的 `skill-creator`（SKILL.md + `quick_validate.py`）对技能包做一遍体检。
> 基础项其实都过：frontmatter 合法、`name` kebab、`description` 452 字符、SKILL.md 338 行、链接 0 失联。
> 但体检暴露两处**结构性缺陷**——都是"内容在，但模型到不了"。

### 1. 1.2 万行算法库此前不可检索：七份文档全部没有目录

- 现象：`references/algorithms/` 七份合计 12191 行（最长 `03-评价类` 2590 行），全部没有目录。
  SKILL.md 只字未提这份库，唯一入口是 `stages/01-analysis.md` 的一行「（按题型选算法）」。
  于是"要用 TOPSIS"的实际路径是：在 2590 行里找——模型的选择是不读，凭记忆答。
  **算法库变成死重量**：占了仓库体积，没进过上下文。
- 改法：新增 `scripts/gen_ref_toc.py`，按 `## ` 标题生成**带行号的目录块**（`<!-- TOC:BEGIN -->` 标记，幂等覆盖）。
  行号是核心——目录给出行号，模型就能 `read(offset=893, limit=150)` 只取那一节，而不是整篇加载。
- 落地：9 份 >300 行文档全部生成（7 份算法 + `tikz_rules.md` + `mechanism-diagram/SKILL.md`）；
  逐条核对行号与标题一一对应（mismatch 0）；再跑一遍零变化（幂等）。
- 同时改 SKILL.md：新增「算法库：先查路由，再按行号跳读」小节，写清三步——先读 `README.md`
  的三张路由表定位文档 → 读前 40 行拿目录 → 按行号取节。并把它挂进「知识库索引」表。

### 2. 技能本体一直没有门禁：只剩 `check_links.py` 管链接

- 现象：项目有 G0–G4 五道门禁，技能自己没有。而技能坏掉的方式全是**静默**的：
  `description` 少一个触发词 → 模型不加载，报错为零；参考文件改名 → 模型读到空文件，报错为零；
  SKILL.md 涨过 500 行 → 模型读到一半丢掉后半段，报错为零。三种都只在交稿后暴露。
- 改法：新增 `scripts/check_skill.py`（G-Skill），九项：frontmatter 合法性（含子工具 SKILL.md）、
  SKILL.md ≤500 行、内部路径全部可达、长文档目录同步、37 个 `.py` 语法可编译、无 BOM、
  `evals/evals.json` 结构、孤儿文档（WARN）。
- 首次运行就抓到一处真问题：`tools/mechanism-diagram/SKILL.md` 的 frontmatter 用了非法键 `phases`
  （只允许 name/description/license/allowed-tools/metadata/compatibility），严格校验的宿主会直接拒载。
  改为 `metadata.phases`，信息不丢、键名合法。

### 3. 新增 `evals/`：把"改技能"变成可自证

- `evals/evals.json`：6 条任务用例（整题 / 填表 / 查数 / 出图 / Word 分支 / 评审），
  每条 assertion 都是退出码判据（`check_contract` / `fill_tables --check` / `check_paper` / `check_figures`），
  不靠人读产出。
- `evals/trigger_evals.json`：18 条触发用例，10 条该触发 + 8 条**不该**触发（纯 matplotlib 出图、
  xlsx 重算公式、查 TOPSIS 论文、docx 删页眉——都是共享关键词的 near-miss）。
- `evals/README.md` 写清为什么不套 benchmark 打分：本技能每条断言都是确定性退出码，
  同一输入同一输出，统计方差为零；只保留「改前过、改后不过」的退化和触发两类错误率。
  这是 `skill-creator` 循环的裁剪版：它面向主观产出（写作/设计）要 pass_rate±stddev，
  本技能面向流程，确定性判据更硬。

### 4. `description` 重写：补赛事名与"没说建模"的说法

- 现象：`description` 是唯一的触发机制，原文只有 CUMCM / MCM / ICM 三个赛事名。
  用户说"帮我按数维杯格式写摘要""华为杯的页数限制是多少"时，描述里没有这些词，
  模型可能不加载技能——**内容再好也没机会出场**。
- 改法：补国内赛事（数维杯 / 华为杯 / 研赛 / 国赛 / 美赛）、补交付动作（摘要怎么写、排版格式、
  页数超了、导出 Word）、并写死一句"即使没说建模两个字"。这是 `skill-creator` 说的
  "模型天生偏向**不触发**技能，描述要稍微主动一点"。
- 收支：452 → 642 字符（上限 1024），无尖括号。触发反例（只要一张箱线图、xlsx 重算、
  查论文、删页眉）仍留在 `evals/trigger_evals.json` 里守边界。

### 5. 清理与版本

- 删掉 `assets/figures/_figure_lint.json`（12.5 KB）：作者自测遗留的 lint 记录，无人引用，
  内容还是自己演示图违反自己规则的报错——留在包内只会误导。
- `default/main.tex` 页眉默认关闭（上一轮改的，随本版一并提交）。
- SKILL.md 338 → 367 行；frontmatter 补 `compatibility`（xelatex / Python / Edge / Pandoc 依赖清单），
  让只读元数据的宿主也能判断环境能不能跑。
- 门禁终态：`check_skill.py` 0 失败 0 警告，`check_links.py` 81 份 md 失联 0，
  `gen_ref_toc.py` 9/9 已同步。

## 2.4.1 — 用真实论文回填 2.4.0：四处"设计对、落地卡"的修正

> 触发：拿一篇已完稿的论文（数维杯 A 题，22 页英文，5 张表 + 8 张图）按 2.4.0 的契约流程回填。
> 结论：四张数值表迁成生成物、133 个基键立成 schema 之后，四条门禁全绿；同时暴露 4 处缺口——
> 都是"规则写了，工具没接住"。

### 1. 单位换算：`fill_tables` 支持 `*factor`

- 现象：论文表里写 `10.00 mm`，`results.json` 存的是 `0.01 m`；模板拿不到换算能力，
  只能要么在 results.json 里再加一组 mm 键，要么在模板里手打——后者的下一站就是手抄表。
- 改法：占位符支持 `{{key:*1000:.2f}}`（换算因子可写 `1e-3` 这种科学计数），与 `pct`/`si`
  组合成 `*1000:.2f`。**边界**：`*factor` 只做单位换算（m→mm、N→kN）；
  比值、降幅、误差率这类**结论量必须在 results.json 里立键**，不许在模板里现算——现算那步没人复核。
- 回填实例：`peak |x|`、`r.m.s. u`、`peak |u|` 三行靠它还原成 10.00 / 8.04 / 49.06，与原文一致。

### 2. `tex_escape` 不再转义反斜杠

- 现象：模板里写 `\lvert x\rvert`、`r.m.s.\ $a_y$` 会被转成 `\textbackslash{}lvert`，
  生成的表一编译就乱；反过来已经带反斜杠的 `\%` 被二次转义成 `\\%`（换行 + 注释），整张表塌掉。
- 改法：只转义 `% & _ #`，且用 `(?<!\\)` 跳过已转义的写法；`$...$` 内一律不动。
  模板里因此可以直接写 LaTeX——本来就是 LaTeX 表。

### 3. 键名允许大写：`const.M` / `const.T`

- 现象：`KEY_RE` 只认小写，物理符号常量（`const.M`、`const.T`、`problem2.capacity_8Hz`）被判 `KEY_BAD_NAME`。
- 改法：正则放宽到 `[A-Za-z0-9_]`，仍要求至少两级；文档口径改成"小写 snake_case 优先，
  物理符号允许大写"。

### 4. `check_results` 认 `__r<位数>` 变体 + 短键名不再误报

- 现象 A：`make_results.py` 会给每个键生成 `__r4/__r3/__r2` 四舍五入副本（论文里每个打印精度都要能对上），
  被算成"未申报键"，一篇 566 键的结果文件一上来就报 200+ 条。
- 现象 B：`problem2.params.f1`、`bw1.0` 这类短键名（末段 2 字符）在脚本里必然搜不到，
  报"生产者可疑"，全是假阳性。
- 改法：A → 去掉 `__r\d+$` 后按基键判定；B → 末段 <3 字符时降为 INFO「生产者无法文本核对」，不冒充 WARN。

### 5. `check_paper` 把 `results/tables/*.tex` 算进论文

- 现象：表迁到生成物后，论文里的 `\begin{table}` 少 4 个、`tab:p1` 之类 `\label` 也不再出现在 `paper/`，
  于是 ① SCORE_MAP 的"表 3/表 5"落点被判超量，② `\ref{tab:p1}` 落点被判无效——都是"表其实在，只是搬了家"。
- 改法：`check_artifacts` 统计表数与收集 `\label` 时，把 `results/tables/*.tex` 一起并入；
  数字一致性仍只扫 `paper/`（生成表的数由 `fill_tables --check` 守着，不重复扫）。

### 6. 回填结论（同一篇论文，迁移前后）

| 项 | 迁移前 | 迁移后 |
|---|---|---|
| 数值表 | 5 张全部手抄（其中 4 张含结果数字） | 4 张由 `fill_tables.py` 生成，正文 `\input`；符号表仍手写（无数字） |
| 论文正文数字 | 209 处 | 171 处（约 38 个下沉到生成表，由 `--check` 逐字守护） |
| 结果键 | 无 schema，566 个 JSON 键无人认领 | 140 个键（133 基键 + 7 派生比值/百分数），未申报键 0 |
| 门禁 | 只有 `check_paper.py` | 契约 0 / 表一致 0 / 结果 0 / 论文 0 / 出图 0 |
| 编译 | 22 页 0 error | 22 页 0 error 0 Overfull（表宽、`\%`、`\lvert` 均未破版） |

顺手修的论文缺陷（不是流程问题，是流程没覆盖到的地方）：

- `data_p3_estimate` 面板 (a) 原先画 `F̂` 的原始波形，而 `F̂` 含漏积分器把加速度计偏置变成的常量偏移
  （末时刻约 269 kN，真值 ±25 kN），图上像"估计值比真值大一个量级"，与正文"带内误差 5.2 %"矛盾。
  改为画 6.9–9.1 Hz 带内波形，图题与正文各补一句说明偏移被两个带通通道拒掉；指标未改。
  为此给 `problem3.py` 加了 `--plot-only`：只读 `outputs/*.npz` 重画图，不重跑仿真（回填时不动已定稿的数字）。

## 2.4.0 — 流程改向：契约先行（表格 → 数值 → 图 → 论文）

> 触发：数维杯 Problem A 全流程实测的复盘。步骤本身没错，**顺序错了**——报告、数据表、得分点是
> 后来才补的，`results.json` 成了"跑完看哪个数好写"的仓库，表格是照结果拼的。于是看着一步没落，
> 实际上是"为了完成任务而完成任务"：报告在追认结果，表在迁就结果，论文再抄一遍表。
> 本次把「先写表 → 再解题 → 表与正文同源」变成可执行的门禁，而不是一句倡议。

### 1. 新增 `scripts/check_contract.py`（G1 契约门禁）

- 查 `results/schema.json`：每个键必须有 `label` / `unit` / `producer` / `consumers`，键名至少两级
  snake_case，`consumers` 只认 `table:` / `figure:` / `paper:` / `check:` 四种写法，无消费者的键判 ERROR。
- 查 `reports/tables/*.tpl.md`：必须带 `<!-- table: … | caption: … | label: … -->` 前置注释；
  占位符里的每个键必须在 schema 声明；**结果格里写死的数值判 ERROR**（题面常数走列头或格尾 `*` 显式声明）。
- 查 `reports/图件规划.md`：每张 `data_*` 必须声明 `reads:`，且 reads 里的键都已声明
  （历史工程回填用 `--tolerate-plan` 降级为 WARN）。
- 查 `reports/SCORE_MAP.md`：标了"已证/√"的得分点却指不到键/图/表/式/节的判 ERROR；未证但无锚点的 WARN。
- 查 `reports/symbols.md` 与三份 `QC_S1_ROUND.{1,2,3}.md` 的 `结论：PASS`。
- 退出码：0 通过 / 1 有 ERROR / **2 = 契约尚未建立**（schema 不存在），与"通过"区分开。

### 2. 新增 `scripts/fill_tables.py`（表格渲染）

- `reports/tables/*.tpl.md` + `results.json` → `results/tables/<名>.md|.tex`，并写 `_render.json`
  （行/列/用到哪些键/模板 sha/渲染时间）。
- 占位语法：`{{key}}`（按 schema 的 `digits`）、`{{key:.3f}}`（Python 格式串）、
  `{{key:pct}}`（×100 加 `%`，tex 自动写 `\%`）、`{{key:si}}`（千分位，tex 用 `\,`）。
- 键名解析同时支持扁平点号键与嵌套对象；键名写错时该格渲染成 `??` 并 ERROR 退出，不静默变空。
- 生成的 tex 自带 `\caption`/`\label`/`toprule`；`format: fixed` 按【列宽记账】`1.04 − 0.04N`
  分配 `p{}` 列宽并把舍入差额塞进最后一列（实测 5 列 0.21+0.16×4=0.85→修正为合计 0.84）。
- `--check` 逐字比对磁盘上的生成物与当前 `results.json` 的重渲染结果：**过期即失败**。

### 3. 新增 `scripts/check_results.py`（G2 结果门禁）

- 键覆盖：schema 里每个键在 `results.json` 里必须有值（缺一个即 ERROR，不再出现"以为算了"）。
- 生产者：`producer` 脚本必须存在（ERROR），脚本里查不到该键名则 WARN（兼容 dict 动态组装）。
- 消费者：`figure:data_*` 必须已有对应图（ERROR），`table:*` 必须有同名模板（ERROR）。
- 未申报键：`results.json` 里没立过键的数值列出来（默认 WARN，`--strict` 升为 ERROR），
  并识别"父级键覆盖子路径"（声明 `p2.params` 即覆盖 `p2.params.cadd`）。
- 表新鲜度：复用 `fill_tables` 的渲染逻辑逐字比对；顺带校验 `numbers_allow.txt` 的正则合法性
  （非法正则会让 `check_paper.py` 直接崩）。

### 4. 文档与门禁同步（顺序写进流程，不是写进口号）

- `SKILL.md`：铁律 0 从「报告先行、文件驱动」改写为「**契约先行（先写表 → 再解题 → 最后写文）**」，
  给出 7 步链路与四条机器命令；阶段表 S1 产出加 `results/schema.json` + `reports/tables/*.tpl.md`，
  S2 产出加 `results/tables/*`，G1/G2/G4 门禁各自挂上对应脚本；二选一表新增
  「先立键还是先跑代码」「表格手抄还是生成」「键名怎么起」三行；关键规则 0–2 重写（契约先行／
  数值单一事实源／表格是生成物）。
- `references/stages/01-analysis.md`：步骤重排为「拆题立得分点 → **契约三件套** → 假设预检 → 数据理解 →
  模型与算法 → 证据链 → 代码任务清单（= 谁来填哪些键）」；新增"为什么表要在写模型前定"一段；
  三轮回质检的第 1/2/3 轮判据分别加上契约在不在、`{{key}}` 是否都在 schema、每个键是否有 producer。
- `references/stages/02-coding.md`：进入条件从 3 条变 4 条（含 `check_contract.py` 退出码 0）；
  新增第 3 步"按契约填键"（含只更新自己那几键的写法）、第 4 步"生成表格"；门禁加两条命令。
- `references/stages/04-writing.md`：§4 图表插入改为「数值表一律 `\input` 生成物」+ 改表改模板的路径；
  §5 机器校验先跑 `fill_tables.py --check` 与 `check_results.py`，并说明 `check_paper.py` 管不到表过期。
- `references/contracts/results-schema.md`：重写为**两步契约**（schema 先立键 → results 填值），
  补 `digits` 字段、消费者语法、键名规则（= `results.json` 路径）、派生量也立键。
- 新增 `references/contracts/table-template.md`：模板写法、占位语法、`*` 字面值规则、
  `format: fixed` 列宽、论文 `\input` 用法、六类反例。
- `references/contracts/pipeline.md`：闭环表新增 schema / 表骨架 / 生成物 / `_render.json` 四行，
  各自的生产者-消费者-门禁-断链后果；口径表加"表格骨架与生成"一行；自检从四条变五条。
- `references/contracts/project-layout.md`、`stages/00-start.md`：骨架加 `results/schema.json`
  （S0 先写空壳）与 `reports/tables/`，命名表加结果键与表模板两条。
- 清单：`G1-analysis.md` 新增第〇节契约三件套 9 条（含退出码 0），`G2-coding.md` 新增第〇节
  契约兑现 7 条（含 `--check`），`G4-writing.md` 新增"数值表是生成物"两条。
- `knowledge/04-coding-and-results.md` 补"先看契约再动手"；`knowledge/14-figure-contract.md`
  红线加第 7 条"`data_*` 只读 `reads:` 声明的键，图内关键数值同样取自这些键"。

### 5. 自测（本地夹具，不进库）

- 用真实结果值（97.4432 / 379.8121 / 5.1102 / 0.9766 / 13.2891）建了一个最小工程：
  `check_contract` 0（1 WARN：未证得分点无锚点）→ `fill_tables` 0（2 张表，扁平键与嵌套键都命中）
  → `check_results` 0（键覆盖 6/6，表新鲜）→ 负向各打一次：表里写死 `97.44`、`{{p1.rati0}}` 键名错、
  `reads` 指向未声明键、QC 结论改 FAIL，四条 ERROR 全部被拦下。
- 生成的 `p_index.tex` 与 `q_param.tex`（含 `pct`、`si`、`fixed` 列宽、`*` 字面值）
  在 `ctexart + booktabs + array` 下编译：**0 error / 0 Overfull**。
- `scripts/check_links.py` 与三份 `*_ROUND` 之外的现役文档路径复核通过。

## 2.3.23 — 修三处「门禁误杀合规稿」

> 触发：2026 HMCM Problem A 全流程实测（英文稿、16 城评价模型、5 张数据图 + 1 张 TikZ 流程图）。
> 三处都不是风格问题，而是**合规交付被判 fail**。

### 1. `scripts/check_paper.py` — 符号表判定对多字符下标全盘误杀

- 现象：31 行规范符号表（`$r_{ij}$`、`$w^{A}_{j}$`、`$\bar{U}_{i}$`）只算出 9 个命中，
  报「要求 ≥60%」→ structure FAIL；同时 `Symbol` 表头被当成符号混入统计。
- 根因：`_notation_symbols` 把 token 的 `{}` 剥掉（`r_{ij}` → `r_ij`），而比对侧
  `s in math_text` 用的是未剥括号的正文，两侧口径不一致；longtable 续页表头
  （`\endfirsthead` 后第二段「表头 + \midrule」）被 `seen_body` 当成数据行。
- 修法：新增 `_flat_math()` 对正文做同样的花括号归一化后参与比对；新增
  `_NOTATION_HEADER_FIRST/_SECOND` 词表剔除表头行。
- 回归：同一篇论文换成下标写法符号表 → 30/30 命中（旧版 9/31）；正式稿 26/26。

### 2. `assets/style/plot_style.py` — 英文稿被中文拼音规则判硬伤

- 现象：英文图标签 `Pupils per teacher`、`Median income` 被切成拼音音节，
  报 `pinyin_labels` **error**，必须改词才能过闸门。
- 根因：`paper_lang()` 只认 `MS_PAPER_LANG` 环境变量和 `figures/_house_style.json`，
  MCM/ICM 英文稿在 S0 不会生成该文件 → 一律回落 `"zh"`。
- 修法：新增 `_lang_from_sources()`，无标记时读 `paper*/**/*.tex` 判定：
  **剥掉 `%` 注释**后数汉字（模板自带中文注释，不剥会把英文稿判成中文），
  ≥30 个汉字判 `zh`，有 tex 但无汉字判 `en`，读不到才回落 `zh`。

### 3. `assets/style/plot_style.py` — 区间图被当成「一根光秃折线」

- 现象：`hlines` 画的 16 段名次/置信区间 + 均值点，被判 `sparse_line_figure`
  与 `thin_sample_figure` 双 error（区间段在 `ax.collections` 里是 `LineCollection`，
  旧版不数它；均值点因 y 恒定被 `_is_guide_line` 当成参考线）。
- 修法：新增 `_has_interval_bars(ax)`（LineCollection ≥5 段即认定区间证据），
  在 `_thin_line_figure_issues` 里置 `has_band`，在 `_thin_sample_figure_issues` 里直接放行。
- 回归：区间图 lint 仅剩 `narrow_figure`（版式提醒），两条 error 消失。

### 4. 版本号统一到 2.3.23

- 三处主版本（`VERSION` / `SKILL.md` 标题 / `README.md` 标题）此前已齐在 2.3.22，
  但 `README.md` 正文「版本」段仍停在 `2.3.19`（2.3.22 那条「版本号三处不一」只改了**标题**，
  正文漏改），而 2.3.23 的代码（`plot_style.py` / `check_paper.py`）已先落进工作区 → 号没升。
- 本次一次改齐：`VERSION` / `SKILL.md` 标题 / `README.md` 标题 / `README.md` §版本 /
  `assets/style/check_figures.py` 的 `GATE_VERSION` 全部 = **2.3.23**。
- 顺带修 `README.md` 两处陈旧引用：删掉已移除的 `scripts/build_prompts.py`（见本文件开头「读法」段），
  目录树的 `scripts/` 补上实存的 `check_paper.py` / `check_links.py`；`SKILL.md` 脚本索引补 `check_links.py`。

### 未改但已核实

- `scripts/build_paper.py` 退出码本就是 `PASS=0 / FAIL=1 / WARN=2`，实测 25 页 0 Overfull 得 0；
  早前误报的 "exit 1" 是 PowerShell 管道的 `$LASTEXITCODE`，不是脚本返回值。

## 2.3.22 — 修三类「工具静默失效」+ 路径写法归一

> 本轮由一次外部实测审计触发：61 个 md、31 个 py、36 个 tex、347 条内部路径引用、19 个脚本逐个跑 `--help`。
> 审计共报 P0 2 条 / P1 2 条 / P2 2 条，逐条复核后**多数已在 2.3.21 前后修掉**（PDF 工具已改惰性导入
> 三级兜底、`soffice.py` 已加 Windows 守卫、闸门已能报「未体检」），真正遗留的是下面四类——都已落地。

- **修（P0·闸门静默放行）**：`assets/style/check_figures.py` 加 `GATE_VERSION = "2.3.22"` 与 `--version`。
  闸门是**复制**进项目的，技能升级后副本不会自己变；旧副本在 `figures/` 不存在时只打印一句
  「没有需要体检的结果图」就 `exit 0`，两次实测都被骗过。现在三条路都堵死：找不到 `figures/` → `exit 2` 并打印
  工程根/体检目录/当前目录；`--version` 可核对手上这份是不是新的；`doctor.py --project` 新增
  「项目内的出图闸门副本」节，按字节比对技能原件，不一致或 `code/` 下多铺一份即点名 `STALE`。
- **修（P0·副本根源在 S0）**：`stages/00-start.md` 第 3 步原来是「`plot_style.py` + `check_figures.py` → `code/`，
  闸门再复制一份到项目根」，两份一模一样正是静默放行的来源。改为 **`plot_style.py` → `code/`（供 import）、
  `check_figures.py` 只放项目根**；`knowledge/14-figure-contract.md` 三件套表、`checklists/G2-coding.md`
  同步写清「退出码 2 = 没体检任何图 = 没过」。
- **修（P1·`--help` 打不开）**：`tools/pdf/scripts/convert_pdf_to_images.py` 改 argparse，支持 `--help` /
  `--dpi`，缺参时打印用法并 `exit 1`（原来只认 `sys.argv`，`--help` 会被当成 PDF 路径去打开）。实测四个后端
  兜底链在没装 pdf2image 的机器上仍能出图（`pdftoppm → pdf2image → PyMuPDF`）。
- **修（P0·文档路径失联）**：7 处裸文件名补全为可定位路径——`SKILL.md`(④A 命令、manifest `source` 字段、
  正交铁律)、`README.md`、`knowledge/05-figures.md`、`checklists/G3-figures.md`、`assets/templates/README.md`
  里的 `flowchart.py` / `svg_flow.py` 统一写 `tools/flowchart/scripts/…`；`SKILL.md` G1 行的
  `checklists/G1-analysis.md` 补成 `references/checklists/G1-analysis.md`。其中 manifest `source` 一处是**真不一致**
  ——`make_manifest.py` 实际写入的就是全路径，文档却写裸名。
- **修（P2·自检器自相矛盾）**：`scripts/check_links.py --all` 原本把 CHANGELOG 的 19 条历史路径计入失败、
  退出码 1，与文件头写的「历史条目报失联属预期」打架。改为：现役文档失联才算失败；CHANGELOG 历史条目只在一行里
  报数量（`CHANGELOG 历史条目 19 条（预期，不计失败）`），要逐条看用新增的 `--strict-history`。
- **修（P1·`soffice.py --help`）**：`tools/xlsx/scripts/office/soffice.py` 原来把 `--help` 原样透传给 soffice
  二进制，没装 LibreOffice 就报「找不到 soffice」，逐脚本体检会误判成脚本自己崩了。现在 `--help` / 无参时打印用途，
  退出码 0。
- **改（P2·版本号三处不一）**：`VERSION` / `SKILL.md` 标题 / `README.md` 标题统一到 **2.3.22**
  （此前分别是 2.3.21 / 2.3.20 / 2.3.19）。
- **验证**：`python scripts/check_links.py` → 60 个 md / 201 条内部路径 / 失联 0（`exit 0`）；
  20 个入口脚本 `--help` 全部可起（`plot_style.py` 是 import 用的模块库、`soffice.py` 无 LibreOffice 时给安装提示，
  两者非 CLI 入口，属预期）；闸门在「`code/` 下无 `figures/`」场景实测 `exit 2`。

## 2.3.21 — 论文自检加第 7 项：百分号转义

- **加**：`scripts/check_paper.py` 新增 `check_escaped_percent`——正文里 `35.7 %` 这种「数字 + 裸 `%`」会被 LaTeX 当注释，**吞掉整行后半句**；而 build 仍是 PASS、0 Overfull，数字检查也照样通过（`35.7` 还在）。这是唯一一类"门禁全绿、论文却是残句"的缺陷，必须由机器兜住：命中即退出码 1，改法是把 `%` 写成 `\%`。`lstlisting` 内的代码与整行注释不算命中。
- **改**：`check_paper.py` 从 6 项变 7 项；`SKILL.md` 脚本索引与 `stages/04-writing.md` 的验收集合同步。
- **背景**：实测中一篇 23 页稿件摘要里有 8 处裸 `%`，四道门禁（build / check_paper / 图件闸门 / 逐页目检以外的自动检查）全部放行，人工读 PDF 才发现句子被吃断。此类缺陷只能靠新增的这一项查出。
## 2.3.20 — 报告先行 + S1 三轮回质检 + 流程图正交约束

- **流程改为文件驱动**：新增「铁律 0：报告先行」，`ANALYSIS_MODELING_REPORT.md` 未过 G1 之前不许写模型代码 / 出数据图 / 进 S3、S4；S2 期间改模型必须先改报告。
- **S1 增加三轮回质检**：G1 从"清单打勾"升级为"清单 + 3 轮留痕"（结构覆盖 → 一致性冲突 → 可执行性与校验），产物 `reports/QC_S1_ROUND.1..3.md`，三份结论行必须都是 `结论：PASS`；`stages/01-analysis.md`、`checklists/G1-analysis.md`、`stages/02-coding.md`（进入条件）、`contracts/pipeline.md`（闭环表登记 QC 产物）同步改写。
- **新增「二选一消除表」**：把 6 处含糊选择落成判据——报告 vs 代码、③ 主图 vs ④B 总流程图、④A vs ④B、机理图语言、数据图 outputs 登记格式、模板选择。
- **④A TikZ 流程图走向铁律：直来直去**：`tools/flowchart/scripts/flowchart.py` 改为全正交布线（`--` / `-|` / `|-` / `-- ++`），回边只从外侧绕、判定框两分支不再共用 `south` 锚点；`tools/flowchart/SKILL.md` 增补禁用列表与四条目检验收。
## 2.3.19（2026-11-04）

### 流程图路线纠正：总流程图 = SVG（④B），算法细节 = TikZ（④A）；新增 5 套总流程图实例母版

- **加**：`assets/figures/reference/totalflow/` —— 用户实拍入库的 **5 张总流程图**（`src/*.jpg`）+ **SVG 复刻渲染的 PNG**（`preview/*.png`）+ `index.json` + `README.md`。版式：`quadrant`（四象限任务分组）、`multi-panel`（流程+分析+分类）、`nested`（议题嵌套包裹，任务 1–5）、`pipeline-groups`（左入右出流水线）、`five-steps`（五步骤阶段图）。
- **加**：`tools/flowchart/assets/totalflow/tf_*.svg` —— 5 套**可编辑 SVG 复刻**（1440×800，虚线分组框 + 任务标签页 + 淡色填充 + 正交箭头 + 空心跨组箭头），以及 PNG 2×（2880×1600）。
- **加**：`tools/flowchart/scripts/build_totalflow.py` —— 五套版式的 SVG 生成器（坐标在代码里，改一个数就能重排），`--png` 顺带调 `svg_flow.py` 出图，实测 5/5 成功。
- **改（路线纠正）**：`tools/flowchart/SKILL.md`、`SKILL.md` ④、`03-figures.md` §4、`05-figures.md` 统一口径 —— **总流程图/问题分析总览 = ④B SVG**（`svg_flow.py`，母版 5 套）；**算法流程/判定/回边 = ④A TikZ**（`flowchart.py`，母版 8 套）；几何/物理机理仍归 ② `mechanism-diagram`。此前把总流程图默认写成 TikZ，是错的。
- **改**：`05-figures.md` 原「一问一列的分工总览走哪条」重写为「总流程图与算法流程图走哪条」——2.3.18 把分工总览推给 `paper-figure` 也不对，它属于 ④B。
- **改**：`tools/flowchart/SKILL.md` 的定位表拆成「总流程图（B 路）/ 算法流程（A 路）」两行；边界条不再把总流程图推给 `paper-figure`。
- **实测**：5 套 SVG 全部渲染成功（PNG 2×），逐张目检：文字不压线、箭头闭合、跨组空心箭头对齐；`build_totalflow.py --png` 一次跑通。

## 2.3.18（2026-11-04）

### 按用户要求移除 `workshop/` 与 `cumcmthesis/`，默认模板改为 `default/`

- **删**：`assets/templates/latex/workshop/`（17 章 + `format.cls` + 3 个字体，30.8 MB）与 `assets/templates/latex/cumcmthesis/`（4 个文件）从工作副本移除；随后用 `git filter-branch` 清理历史提交并强推，仓库里不再有这两套模板（体积从约 31 MB 降到 1 MB 量级）。
- **改**：默认论文模板 → `assets/templates/latex/default/`（`ctexart`：标题页 + `\abstractcn` + `\tocpage` + 8 章 + `\referencescn` + `\appendixcn`，自带 `\fig` / `\tabcaption` / `\threelinetable`）。`SKILL.md`、`00-start.md`、`G0-start.md`、`G4-writing.md`、`03-figures.md`、`04-writing.md`、`05-figures.md`、`README.md`、`scripts/doctor.py` 全部改为 default。
- **改**：写作提示词转为**独立口径库**——`knowledge/10` 不再从模板注释抽取（`scripts/build_prompts.py` 删除、`00-index.md` 同步），17 节按「章」组织；`04-writing.md` §2 新增「`knowledge/10` ↔ `default/sections`」映射表（摘要→`\abstractcn`、引言/总体→`1_restatement`、假设→`2_assumptions`、符号→`3_symbols`、各问→`4_problem1`/`5_problem2`/`6_problem3`、检验→`7_sensitivity`、评价→`8_evaluation`、参考文献→`references.tex`、附录→`A_code.tex`）。
- **改**：`04-writing.md` §4 图表写法翻转为「default 自带 `\fig{宽}{路径}{题}{label}` 与 `\tabcaption{题}{label}{列格式}{表头}{表体}`，直接调用；只有跨页长表才手写 `longtable`」。
- **改**：`05-figures.md` 的「§2 的总体分析图：模板 TikZ 还是 `tools/flowchart`」整节重写为「一问一列的分工总览走哪条」——模板内置 TikZ 随 workshop 移除，分工总览归 ③ `paper-figure`（SVG），有判定/回边的才走 ④。
- **改**：`VENDORED.md` 删除 CUMCMThesis 条目并记录移除；`LICENSE_NOTICE.md` 同步（AI 声明不再依赖模板宏）。
- **实测**：`default` 首编 **8 页 / 0 error / 0 Overfull**；`doctor.py` 三项检查全绿；`check_paper.py` 六项退出码 0。

## 2.3.17（2026-11-04）

### 流程图补 B 路（SVG）+ `SKILL.md` 写死路径与执行顺序

- **加**：`tools/flowchart/scripts/svg_flow.py` —— 流程图 **B 路**：`flow_*.svg` → 可编辑 `flow_*.html`（浏览器里点字直改、一键「下载 SVG」回写源文件）→ `flow_*.png` / `flow_*.pdf`。渲染走 Edge 无头（`--screenshot` / `--print-to-pdf`），若装了 `cairosvg` 自动改走它，**全程不需要 LaTeX**。
- **加**：`tools/flowchart/assets/flow_svg_template.svg` —— B 路母版：判定 + 回边的最小骨架，3 色、文字纯黑，改文字即可用。
- **改**：`SKILL.md` 的「四路图件」重写为「**路径 / 读取顺序 / 执行顺序**」：每条路线写清先读哪几个文件（顺序不能跳）、跑哪条命令、产物落到哪、manifest 怎么登记；流程图拆成 **④A（TikZ）** 与 **④B（SVG）** 并给出选路判据，禁止同一张图两路各出一份。
- **加**：`assets/templates/README.md` —— 模板总览：5 套论文模板的文档类 / 文件清单 / 空白首编实测（workshop 10 页、cumcmthesis 4 页、mcm 11 页、华为杯 10 页、default 8 页，均 0 error / 0 Overfull）+ Word 模板 + 四路图件母版（数据图 11 / 机理 12 / 主图 5 / 流程图 8+1）与选型口径。
- **修**：`workshop/README.md` 写「12 个章节文件」，实际 17 章 + `main.tex`；写「首编 8 处 Overfull」，实测 0 Overfull、2 处 `fig:xxx` 占位未定义引用（同一标签）。按实测改正。
- **改**：`references/stages/03-figures.md`、`references/checklists/G3-figures.md`、`references/knowledge/05-figures.md`、`tools/flowchart/SKILL.md`、`README.md` 同步两条流程图路线；05-figures 只留「走哪一路」，命令与顺序统一指向 `SKILL.md`，不再两处各写一份。
- **修**：`check_paper.py` 的文献检查把 `%` 注释里的 `\bibitem{标签}` 当成真实条目（workshop 模板注释自带 `\bibitem{标签}` 与 `\bibitem{behzadian2012topsis}` 两枚）→ 用模板写出来的论文**永远过不了「文献引用」这一项**，G4 无法达标。现在先剥注释再提取键；`\cite` 与 `\nocite` 扫描同样剥注释（注掉一枚角标不再算「引用过」）。
- **修**：`make_manifest.py` 给所有 `route=flow` 的图硬写 `spec=figures/<stem>.json`，B 路（SVG 源）会写成不存在的 json。改为按实际存在的 `.svg` / `.json` 推断，`source` 同步写对脚本（`svg_flow.py` / `flowchart.py`）。
- **修**：`mechanism-diagram` 把 `pdfcrop` 写成必经步骤，本机缺 Perl 时它直接报 `MiKTeX could not find the script engine 'perl'`（实测），会让人误判图坏了。改为「可选步骤，报错即跳过」——`standalone` 的 `border=3pt` 已紧裁，`pdfinfo` 看 `Page size` 无大留白即可。
- **实测**：机理图链路 `xelatex → pdfcrop(跳过) → pdftoppm -r 300` 出 588×401 PNG、0 error / `Page size 140.96×96.04 pt`；流程图 A 路 `loop.json` 出 983×1469 PNG；B 路母版出 1800×1120 PNG + 矢量 PDF，中文与箭头均正常；`manifest` 两条路各自登记到正确的 `spec` / `source`。

## 2.3.16（2026-11-04）

### 第 4 轮终验（R4-A）后的 5 处修复

- **修**：`mcm/main.tex` 用 `\newcommand{\SummaryText}{...}` 装摘要，宏不是 `\long`，摘要里一分段就报 `Paragraph ended before \new@command was complete`，**而且日志不指向摘要**（实测卡了 20 分钟）。改为 `\newcommand{\SummaryText}{\input{summary}}` + 新增 `mcm/summary.tex`。
- **修**：`check_figures.py` 同一 stem 有 png/pdf/svg 三份且无 lint 记录时，同一个 `no_vector_copy` 被计 **3 次**；人读输出还只打「未自检」，看不到「PDF 是改后缀的 PNG」。矢量判据按 stem 只算一次，未自检的图也把 issue 原因打出来。
- **修**：`check_figures._skip` 把 `paper_/mech_/flow_` 前缀一律跳过——即使这张图真有 lint 记录。改为「有记录就照查」。
- **修**：`build_paper.py` 把 Underfull 也计入 WARN（退出码 2），与 `04-writing.md`「Underfull 可留」冲突。改为只按 error / 缺文件 / 未定义引用 / Overfull 判 WARN。
- **修**：`make_manifest.py` 的 `setdefault` 让同一张图两次出现时取到「附录里那条无 section」的记录（status=warn）。改为保留信息更全的一条。
- **试过但回退**：把小整数豁免阈值从 20 压到 10（想让 `T=10 s` 写成 9 s 也能被抓）→ **R1/R2/R1B/R4 四份合规稿当场被误杀**（「5 Hz」「3 个问题」全判未命中）。回退到 20，并把这条写进 `04-writing.md` 的已知盲区：小整数的错只能靠人核。

## 2.3.15（2026-11-04）

### 第 3 轮中文链路（R3-B）后的 3 处修复

- **修（2.3.9 那条「每框 ≤4 字」是错判据）**：`2.总体分析.tex` 的 TikZ 分工图盒宽由 `format.cls` 的 `minimum width=3.2cm` 锁死，5 问起列距（3.15cm）小于盒宽 → **必然重叠，压字无效**。改为按列数自适应：`totalw = min(16.3*(nq-1)/nq, max(12.6, 3.5*(nq-1)))`、`boxw = min(3.2, step-0.35)`，根节点落在 `totalw/2`。4/5/6 问实测 **0 error / 0 overfull**。
- **修**：`check_paper.py` 的数字检查仍按**文件名**跳过文献（`references.tex`），而 workshop 把 bib 内联在 `10.参考文献.tex` → 卷期页码（2649/2655 等）被判「未命中」，只能靠 `numbers_allow.txt` 兜。现在抽出 `_bib_file()`，数字检查与文献检查共用同一识别结果。
- **修**：TikZ 里的版式数字（`\def\ystep{1.73}`、`at (6.3,0)`）被当内容数字 → 扫描时整段跳过 `tikzpicture` 环境。

## 2.3.14（2026-11-04）

### 第 4 轮绕过测试（R4-C 第三轮 6 招）后的 5 处加固

这一轮 3 招被抓住、3 招（及 3 个换写法变体）骗过：

- **符号「出现过」太松**（3 个符号各只出现 1 次、塞脚注/图注，甚至塞进 `%` 注释也算）：现在正文**先剥注释**，且只认**数学语境**——`$...$`、`equation/align` 环境、`tabular/longtable` 表体里的出现才算。
- **符号说明被 `\input` 两次**（正文前一次、附录后一次，只比位置判不出）：现在 `len(idxs_n) > 1` 直接报「被 \input 了 N 次」。
- **落点编号 or 语义**（同格塞一个合法 `\ref` 就能顶掉越界的 `Table 99`）：图/表编号改成「整格所有编号都要合法，任一越界即判空」；公式与节号写法太多（`\tag`、`5.1.2 节`），只要求指得到、不做上限，避免误杀合规稿。
- **图件跨目录借**（`manifest.outputs` 指向别的目录里一张真 PDF，`check_paper` 认任意路径、`check_figures` 只看 `figures/`，两闸视野不重叠）：`outputs` 必须 `resolve()` 后落在工程自己的 `figures/` 下。
- **假阳性面**：`\pagebreak[100]`、`\num[...]{...}`/`\qty[...]{...}` 的可选参数不再被当内容数字。

## 2.3.13（2026-11-04）

### 第 3 轮英文链路（R3-A）后的 4 处修复

- **修**：`make_manifest.py` 的 caption 正则 `\{([^}]*)\}` 遇首个 `}` 就截断，含 `\ref{}`/`\eqref{}` 的图注被切掉半句（实测 3 条）。改为**括号配对**提取。
- **修**：`check_figures.py` 里矢量版判据写在 `if not isinstance(rec, dict): continue` 之后 → **没有 lint 记录的 `data_*.pdf` 直接被跳过**，假 PDF 首轮实验判「硬伤 0」。抽成 `_vector_issues()` 并在 continue 之前调用；顺带 `sys.stdout.reconfigure(errors="replace")`，GBK 控制台遇 `m²`/`✅` 不再把闸门打挂。
- **改**：`check_paper.py` 的落点白名单只认缩写（`Tab.`/`Fig.`/`Eq.`/`§`），写全词 `Table 6` 会被拒。扩展为 `Table|Figure|Equation|Section` 全词。
- **改**：`04-writing.md` 把 `check_paper` 六项检查的**落点写法**写清（`\ref{key}` 的 key 必须在全文 `\label` 里，或 `图 N/表 N/式(N)/§N` 且 N 不超过实际数量），文档与代码对齐。

## 2.3.12（2026-11-04）

### 第 2 轮中文链路（R2-B）后的 5 处修复

- **修**：`make_manifest.py` 的 `caption/section` 只在**单个文件内**向前找 `\(sub)?section`，而 workshop 模板把 `\section` 放包装文件、图放 `5.X.Y` 子文件（还常用 `\subsubsection`）→ 12 张图 11 张 `warn`。改为按 `\input/\include` **递归摊平全文**再定位章节上下文，实测 12/12 `ok`。
- **修**：`flowchart.py` 用 `png.exists()` 判活，上一轮幸存的旧 PNG 会让「已生成」骗过（实测 PDF 更新、PNG 还是旧的）。渲染前先删旧 PNG。
- **修**：`format.cls` 没设 `\lstlistingname`，中文稿的代码块题注印成英文「Listing:」。补 `\renewcommand{\lstlistingname}{代码}`。
- **改**：`0.摘要.tex` 的提示词写死「28~30 页」，与 12–22 页的赛题冲突（G4 已改档位口径但提示词没跟上，单一事实源没落到一处）。改为「按赛制档位，以 `plan.md` 为准」。
- **改**：`02-coding.md` 补两条实测坑——① `print` 只用 GBK 可编码字符（打印 `f̂`/`✅` 会 `UnicodeEncodeError` 把脚本打挂）；② numpy ≥ 2.0 删了 `np.trapz`（改 `np.trapezoid`），且加速度二次积分会漂移出假位移，要用状态递推。

## 2.3.11（2026-11-04）

### 第 3 轮绕过测试（R3-C 第二轮 8 招）后的加固：把「存在性检查」升级成「内容检查」

上一轮 8 招里 6 招骗过。逐条补：

- **符号表垃圾行**（放 3 行正文不用的符号就过）：现在把表里的符号 token 拿去正文里找，**≥60% 必须在正文出现**，否则列出没出现过的。
- **manifest 自我豁免**（id 与文件名不一致、dict 形态整段跳过校验）：`figures` 是 dict 时先归一成 list；stem **以 `outputs` 的真实文件名为准**，`id ≠ outputs[0]` 直接判失败；`outputs` 逐条 `exists` + `%PDF-` 头 + PyMuPDF 打开验页面内容。
- **空白 PDF 壳**（`%PDF-1.4` + 1 页空白就能过）：现在要求首页有文字/图形/图像之一，空壳判「不是真矢量版」；`check_figures.py` 同步。
- **SCORE_MAP 落点**（`Sec. 1`、`§4.7`、`见正文` 都能过）：现在 `\ref{key}` 的 key 必须真在全文 `\label` 里，或 `图/表/式 N` 的 N 不超过论文实际图/表/公式数；表头按内容识别（多张子表各自重置列定位），行内多余的 `|`（如 `max|ω|`）退回最后一格。
- **宏拆内部名 / `%` 续行**（`\newcommand{\rr}{reports/}` + `\rr` 能过）：扫描前先把行尾 `%` 的续行拼起来、做一层宏展开，再查黑名单。
- **小数逗号**（`$3{,}14159$`、`\num{}`、`\SI{}{}`）：`{,}` 归一到小数点、`\num{}`/`\SI{}{}` 取首参，`0{,}7` 不再被 ≤20 豁免放行。
- **一次性群引**（`\cite{r1,…,r8}` 算 8 条都被引用）：>3 个键的 `\cite` 只算「出现过」，每个键必须至少单独或小组（≤3 键）引用一次。
- **`\include`**（只认 `\input`，导致合规稿被误杀）：`\\(?:input|include)\{...\}` 同等对待。
- **顺带**：`make_manifest.py` 遇到 dict 形态 manifest 直接 `AttributeError` 崩，已修。

## 2.3.10（2026-11-04）

### 第 2 轮英文链路（R2-A）后的 7 处修复

- **修（会让 2.3.7 的第 4 条修复失效）**：`plot_style.paper_lang()` 直接拼 `dirname(__file__)/figures/_house_style.json`，本文件被复制到 `code/` 后指向 `code/figures/`，工程根的 house-style **永远读不到** → 英文稿的拼音规则实际关不掉，只能靠环境变量。改为走 `_figdir_hint()` 逐级上溯。
- **修（会让整条链路崩）**：`run_all.py` 的 `subprocess.run(text=True)` 缺 `encoding`，父进程 `PYTHONIOENCODING=utf-8` + cp936 控制台时实测 `UnicodeDecodeError`、退出码 −1。补 `encoding="utf-8", errors="replace"`。
- **修**：`make_manifest.py` 的 `status` 取 `old.get("status", …)`，旧 `warn` 会粘住——论文补好 caption 重跑仍是 warn。改为每次重算。
- **修**：`check_paper.py` 的图件契约把 manifest `outputs` 里的文件名也收进白名单 → **manifest 可以自我豁免**。只认 `id`/`stem`。
- **修**：矢量版判据再加一层。只读 `%PDF-` 头也能被手写伪造，现在用 PyMuPDF 打开确认真有页面；`check_figures.py` 与 `check_paper.py` 同步。
- **改**：`build_paper.py` 的措辞从「其中表格 N 条」改为「alignment 类 N 条」，并写明 `tabular` 列宽溢出 LaTeX 常报 `in paragraph`、要按行号回源文件定位（原来那句【列宽记账】提示是死分支）。
- **改**：`flowchart.py` 层距按最长节点文本自动放大（多行节点不再互贴、回边不出画布）；`04-writing.md` 写明「≤20 的整数不做数字校验」的已知盲区，数量词要自己核。

## 2.3.9（2026-11-04）

### 第 1 轮中文链路（R1-B）后的 5 处修复

- **修**：`scripts/check_paper.py` 的文献检查写死 `paper/references.tex`，而 `workshop` 模板把 bib **内联在 `10.参考文献.tex`** → 中文稿一律被判「缺少 references.tex」。现在按内容识别：优先 `references.tex`，找不到就取第一个含 `\begin{thebibliography}` 或 `\bibitem` 的 `.tex`，并在输出里注明用的是哪个文件。
- **修**：`scripts/doctor.py` 把 `pandoc` / `pdftoppm` 列为 required → 只写 LaTeX 论文的机器 G0 永久「必选项缺失」。改为可选：主链路只要 `xelatex` + numpy/pandas，pandoc 只影响 Word 旁路、pdftoppm 只影响 PNG 预览。
- **修**：`tools/flowchart/scripts/flowchart.py` 无 `pdftoppm` 时不出 PNG。现在 pdftoppm 缺失或失败会走 **PyMuPDF 兜底**，仍失败才报警。
- **改**：`00-start.md` 写明 `fonts/` 必须与 `main.tex` 同级（漏复制直接编译失败），并写清哪些工具是可选。
- **改**：`2.总体分析.tex` 的提示词补实测列距（4 问 4.2cm、5 问 3.15cm，而盒子最小宽 3.2cm）——**5 问以上每框必须 ≤4 字**，否则相邻列压在一起。

## 2.3.8（2026-11-04）

### 第 2 轮绕过测试（R2-C）后的 8 处加固

R2-C 用 8 种手法攻击 v2.3.7 的 6 项检查，**4 条完全骗过、3 条半骗、1 条被抓住**。逐条补：

- **章节结构**（骗过 #1：`3_notation.tex` 只留表头、零行符号）：现在打开符号说明文件数真行——`&` 分隔、首列有符号、次列有说明，**少于 3 行判失败**，空表头不再算。
- **顺序**（骗过 #7：把前位 `\input` 注释掉、真 input 挪到模型章后）：取 `\input` 序列前先逐行剥注释，并按**最后一次**出现判序。
- **产物闭环**（半骗 #2：`—`/`TBD` 被抓、换 `待定`/`N/A` 就过）：落点列改**白名单**——必须能指到 `\ref{`／式(／图 N／表 N／`Eq.`/`Fig.`/`Tab.`/`§`／数字，占位词表扩到 12 个。
- **内部文件名**（骗过 #4：全角 `ｒｅｐｏｒｔｓ／`、断词 `re\-ports/`）：先 NFKC 折半角，再剥 `\-`、`{}`、`\,`、`\allowbreak`；附录 `lstlisting` 内的代码不再误伤，但附录正文照样查。
- **数字**（骗过 #5a：全角 `３．１４` 被拆成 ３+１４ 后撞「≤20 免检」）：NFKC 折叠后再抽数字，`NUM_RE` 收紧到 ASCII `[0-9]`；顺手把 `\pagebreak[100]` 的参数剥掉（它曾被当内容数字）。
- **文献**（骗过 #6：`\nocite{*}` 让未引用条目「看起来被引用」）：`\nocite` 不算引用并显式提示；**`unused` 非空也判失败**——只「有键不引」同样对不上角标。
- **图件契约**（骗过 #8：manifest 图名写全、`outputs` 指向不存在文件）：`outputs` 逐条 `exists`，且 `.pdf` 读文件头必须是 `%PDF-`。
- **图闸门**（骗过 #3：PNG 改名成同名 `.pdf`）：`data_*` 的 `.pdf` 不再只 `isfile`，读 `%PDF-` 头判真假矢量。

## 2.3.7（2026-11-04）

### 第 1 轮正向实测（R1-A 英文全链路）后的 12 处修复

- **修**：`assets/scaffold/run_all.py` 写死 `src/`（契约是 `code/`）→ 空模板直接「找不到脚本」。改为 `code/` 优先、`src/` 兜底，找不到就明确报错。同时把 `达标 ✅/未达标 ❌` 换成 `[OK]/[FAIL]`：GBK 控制台下 ✅ 会让整个脚本 `UnicodeEncodeError` 崩掉。
- **修**：`mcm/main.tex` 的 `lstset` 用 `\color[gray]{.97}` 却没加载 `xcolor` → 论文里一有真代码块就 `Undefined control sequence`；补 `\usepackage{xcolor}`，并加 `\hypersetup{hidelinks}`（否则每个 `\ref`/`\cite` 都套红框）。
- **修**：`plot_style.py` 的拼音检测在英文稿里把 `envelope`、`sensitivity` 这类正常英文词判成「拼音硬伤」→ 英文稿（`paper_lang() == "en"`）直接跳过该规则。
- **修**：`tools/flowchart/scripts/flowchart.py` 逐字符转义，节点写 `$F^\star$` 会变成 `\$F\textasciicircum{}…` 并 `Missing $ inserted` → `escape()` 改为保留 `$...$` 数学段；PNG 导出不再吞 stderr，`pdftoppm` 失败会打印原因而不是静默只出 PDF。
- **修**：`scripts/make_manifest.py` 的 `caption`/`section` 恒为空 → 每张图 `status=warn`，G3 无法只靠脚本过。现在默认从 `paper/` 的 `figure` 环境自动提取 caption 与所在 section，另加 `--meta` 手工覆盖、`--no-paper` 关闭提取。
- **新增**：`scripts/check_paper.py` 第 6 项「图件契约」——正文 `\includegraphics` 的图必须登记在 `figures/manifest.json`（原来 manifest 号称唯一来源却无人消费）。
- **改**：`SKILL.md` 与 `04-writing.md` 把 `check_paper` 从「2 项」补成「6 项」；`04-writing.md` 写明逐章提示词只覆盖 `workshop`（mcm/华为杯/国赛模板没有提示词文件）；`BUILD_REPORT` 的 WARN 口径写清（Overfull 必须清零，Underfull 可留但要在报告里说明）。

## 2.3.6（2026-11-04）

### 第 1 轮反向门禁实测后的补洞（R1-C 报告驱动）

- **修**：`assets/style/plot_style.py` 的 lint 记录加 `saved_by` 字段（`save_publication` / `savefig`）。裸 `plt.savefig` 也会走 `apply()` 装的 savefig 钩子写体检记录，闸门只看「记录在不在」根本分不出调用方式——这是「以为在管、其实完全没管」的唯一真漏洞。
- **修**：`assets/style/check_figures.py` 按 `saved_by` 判调用方式（`savefig` → 提醒 `raw_savefig`）；`data_*` 缺同名 `.pdf` 算硬伤 `no_vector_copy`（进 `DESIGN_HARD`）。顺手删掉 `DESIGN_HARD` 整段重复两遍的代码。
- **修**：`scripts/check_paper.py` 从 2 项扩到 5 项：新增「章节结构」（符号说明必须独立成章且排在模型章之前，读 `main.tex` 的 `\input` 序列判位）、「产物闭环」（`plan.md`/`symbols.md`/`SCORE_MAP.md`/`RESULTS_REPORT.md`/`FIGURE_REPORT.md`/`journal_problem*.md`/`results.json`/`manifest.json` 缺一即失败，并查 `SCORE_MAP` 落点列是否留空）、「内部文件名」（`reports/`、`code/`、`results.json`、`manifest.json`、`plan.md`、`TODO`、`待补充` 命中即失败）。另修 `\newcommand{\TeamNumber}{2500}` 被当成结果值误报。
- **修**：`scripts/build_paper.py` 保留日志里的 Overfull 明细（`pt` + 行号 + paragraph/alignment），`BUILD_REPORT.md` 单列「其中表格 N 条」并给【列宽记账】提示；明确退出码语义 **0=PASS / 1=FAIL / 2=WARN**。
- **修**：`assets/templates/latex/mcm/references.tex` 开头残留的 `\section{Sensitivity Analysis}` 与无关正文（会重复出章、正文印在 References 下）已删，改为干净的 `thebibliography` 占位。
- **修**：`mcm/main.tex` 的 `\threelinetable` 把 `table` 整段包进宏、`\label` 只能写在宏外（`\ref` 会指到 section）；改为 5 参数（caption/label/colspec/header/body），`\label` 进浮动体。
- **改**：`G4-writing.md` 的页数口径从写死的「28–30 页（国赛）」改为「符合赛制档位」，美赛 13 页不再被误杀；`BUILD_REPORT` 勾选项写清退出码语义。
- **改**：`14-figure-contract.md` 闸门一节补 `saved_by` 与矢量版判据；`SKILL.md` 版本号与 `VERSION` 对齐到 2.3.6。

## 2.3.5（2026-11-03）

### 符号说明前移 + 四套模板同口径（跑完 2025 数维杯 A 题后修）

- **改**：`assets/templates/latex/mcm/` 补 `sections/3_notation.tex`，章节文件整体后移一位（`3_model_design`→`4_model_design` … `7_conclusions`→`8_conclusions`），`main.tex` 的 `\input` 顺序与目录同步。此前英文链条只有 1 Introduction → 2 Assumptions → 3 Model Design，**没有符号说明槽位**，符号表只能塞进模型章，读者先见符号后见表。
- **改**：`cumcmthesis/main.tex`、`default/sections/3_symbols.tex`、`huaweibei/sections/4_symbols.tex`、`workshop/4.符号说明.tex` 四份符号表统一成 longtable 两列（符号 + 说明，单位写在说明末尾括号里），去掉「单位」列与加粗表头。此前 huaweibei 是 `tabular{ccc}` + 加粗表头 + 单位列，cumcmthesis 是 `tabular{lll}`，default 只有一句正文，四套模板与 `10-chapter-writing-prompts.md` 的口径互相打架。
- **修**：列宽规则补 `\tabcolsep` 记账。原文「列宽总和 = 1.04 − 0.04×N」漏算首尾 `\tabcolsep`，N=2 的 0.96 实测 Overfull 5.2–5.9 pt；改为「首尾加 `@{}` 后 0.96 成立，不加 `@{}` 时须降到 0.94」。四份模板与总则注释同步。
- **修**：`mcm/main.tex` 目录页原来手写 `\mcmtocentry{1}{Introduction}{2}{1}`，页码是假值；改 `\tableofcontents`。`\TotalPages` 从写死的 `4` 改 `\pageref{LastPage}`（补 `lastpage` 宏包），页脚「Page x of N」不再靠手改。顺手去掉与 `fontspec` 重复的 `times`，补 `array` / `longtable`。
- **新增**：符号表前移到 S1 —— `reports/symbols.md` 列入 `01-analysis.md` 的必须产出，`G1-analysis.md` 加勾选项，`02-coding.md` / `04-writing.md` 把它列为输入。符号口径在建模阶段定死，S2 变量名与 S4 符号表照抄，不再各写一套。
- **新增**：总则加【英文链条】一行，英文赛题的 Notation 与中文「符号说明」同位，一律排在模型建立之前。
- **新增**：`references/contracts/pipeline.md` —— 全流程串联契约（产物 → 生产者 → 消费者 → 门禁）。原来 5 个阶段各自写「输入/必须产出」，没人管产出是否被下游读、输入是否真有人产：`术语表格.md`、`results/logs/`、`BUILD_REPORT.md`、`REVIEW_REPORT.md` 是孤儿，`SCORE_MAP`、`symbols.md` 是缺口，`default` 模板被标成「通用英文结构」（实为 `ctexart` 中文模板）。现在：新增第 13 条硬规则「产物闭环」；`SCORE_MAP.md` 补进 S2 产出与 G2/G4 门禁；`04-writing.md` 的输入补齐 `journal_problemN.md`、`SCORE_MAP.md`、`plan.md`；`03-figures.md` 的输入补 `symbols.md`（图内符号与正文同源）；`BUILD_REPORT.md` 定为「回改输入」而非日志；G4 的列宽口径同步 `@{}` 记账。
- **新增**：`scripts/check_paper.py` —— 全流程最后两个"没人查"的口子补成机器校验。① 正文数字 ↔ `results.json`（四舍五入、百分比、kN/MN 换算都算命中；命中不了的要写进 `results/numbers_allow.txt` 并注明来源）；② 文献闭环：`references.tex` 必须是 `thebibliography` + `\bibitem{key}`，正文 `\cite` 与键一一对应，`enumerate` 手写条目直接判失败。实测本项目：234 个正文数字全部命中、8 条文献 / 8 个 `\cite` 键，退出码 0。配套：`04-writing.md` 第 5 步加机器校验、G4 加勾选、`pipeline.md` 加两行产物与第 4 条自检、`SKILL.md` 脚本索引与规则 4。
- **改**：AI 声明不再凭空写 —— `plan.md` 模板加「AI 使用记录」段（用了什么 / 哪一步 / 产出与人工改动），G4 要求照抄；不新增文件。
- **删**：`SKILL.md` 里重复 `04-writing.md` 的编译命令与 Word 分支两段，改成一行指向 04（口径单点定义）。
- **新增**：流程图两条路线的判据。此前 `05-figures.md` 说「四路、不做第五种」，`10-chapter-writing-prompts.md` 又说「流程图一律走 `tools/flowchart`」，而 workshop 模板自带一张 TikZ 总体分析图且标为「必需」，三处打架。现在定性：§2 那张是**路线 ③ 的内置变体**（树状分工图，无判定/回边，全文 1 张，随文编译）；有判定、有回边的才走 `tools/flowchart`（JSON→TikZ→PDF/PNG，每问 ≤1、全文 ≤3）。判据与反模式写进 `05-figures.md`，`build_prompts.py` 的头部说明、`tools/flowchart/SKILL.md` 边界、`03-figures.md` 四路边界、`G3` 门禁同步。

## 2.3.4（2026-11-03）

### 精简 01–05：只留「10–14 里没有的」那一层

- **删**：`03-pitfalls-by-type.md` 的「编码阶段常见错误」11 条 —— 与 `04-coding-and-results.md` 逐字相同（`scipy` 约束方向、取整复验、条件数、JSON 落盘…），改成一行指向 `04`；文件从 31 行降到 24 行，只留题型速查。
- **改**：`04-coding-and-results.md` 收拢为编码坑的**唯一来源**，后半段重写为「结果落盘」5 条，数值口径、验证强度、图件登记改指 `12` / `14`，不再复述；删掉与 `11` 重复的路径/编码提醒。
- **改**：`05-figures.md` 只保留「图种怎么选 + 四路路由」，版式/闸门指 `14`、图题措辞指 `13` 三.10；并写明主图只参考那 5 张母版。
- **改**：`02-model-selection.md` 的 `scipy` 方向与约束符号两条 → 指 `04`（原为第三份副本）；`01-problem-understanding.md` 的「启发式不称全局最优」→ 指 `12` 五。
- **净效果**：01–05 五份共去重 34 行，重复口径从三份降为一份。

### 主图母版：换高清原图 + 瘦身 + 骨架规格

- **换**：`assets/figures/reference/roadmap/src/*.jpg` 换成用户提供的 5 张原图（1439 px，255–331 KB），替换原先 130–170 KB 的压缩版。
- **删**：5 张 2400 px PNG（约 4.9 MB）与 5 张 PDF（约 0.9 MB）—— 都是同一张图的位图壳，锁死在 2400 px 且白占体积。目录 6.19 MB → **1.41 MB**。
- **新**：`roadmap/README.md` —— 选版式表（用它的题 / 别用它）、5 段骨架（结构 + 布局 + 三点复刻要点）、通用视觉规范（唯一来源，含配色与字号）、用法与版权边界。
- **改**：`index.json` 每条加 `skeleton`（一句话骨架）与 `avoid`（什么时候别用），`file` 指向 `src/*.jpg`，删掉 `pdf` 字段。
- **改**：`tools/paper-figure/SKILL.md` 不再复述视觉规范，改为指向 `roadmap/README.md`；硬约束「只用这 5 张，不引入外部图库/别处论文配图」，验收加勾选项；`select_reference.py` 去掉 `--pdf`，详情输出结构/适用/别用。
- **改**：`import_plate.py` 只入一份 jpg（去白边、宽 ≤1439 px、q88），不再生成 PNG/PDF；新增 `--avoid` / `--skeleton`。
- **修**：两个脚本加 `errors="replace"` 兜底 —— 中文 Windows 的 GBK 控制台打印骨架里的 `⊃` 会抛 `UnicodeEncodeError`。
- **同步**：`assets/figures/reference/README.md`、`VENDORED.md`、`LICENSE_NOTICE.md` 去掉「2400 px PNG + PDF」旧口径。

## 2.3.3（2026-11-03）

### 去重：知识库 06 / 08 / 09 三份重复文件合并

- **删**：`references/knowledge/09-cumcm-rubric.md` —— 与 `tools/review/` 逐条重复（100 分结构 + 格式质量系数 = `references/rubric.md`；AIGC 高风险信号 + 修改原则 = `references/aigc.md`；评审输出清单 = `tools/review/SKILL.md`），无独有内容。评审口径唯一出口改为 `tools/review/`。
- **删**：`references/knowledge/08-mcm-icm.md` —— 页数 25 与 `13-writing-injection.md` 的「美赛/亚太约 22」冲突；评分维度 = `tools/review`；可视化 = `14-figure-contract.md`；题型与「王炸组合」= `02-model-selection.md` 决策树。独有条款折叠：常用组合表与美赛题号 → `02`；25 页上限 / Summary Sheet 独立页 / AI 报告附录不计页 / 英文 → `13` 三.13。删除无来源的「获奖论文图表占比 68%」。
- **删**：`references/knowledge/06-writing.md` —— 摘要写法 = `10` 第 0 章 + `13` 一节；假设/符号/检验 = `10` 第 3/4/6 章与 `13` 二.12；且「中国赛摘要不超过两页」与 `10`/`13` 的「摘要一页铁律」冲突。独有条款折叠：±10%/±20% 扰动水平、Tornado 图、按题型选扰动对象 → `12` 四.3（新增）；结构完整性九项已由 `10` 章节链承担。
- **改**：`references/knowledge/07-verification.md` → `06-verification.md`，保持 `01`–`06` 连续编号。
- **改**：`references/knowledge/00-index.md` 重写为「现场必读（10–14 + tools/review）/ 基础方法库（01–06）」两表，并在末尾说明三份文件已合并的去向。
- **改**：`VENDORED.md` 归属指向（BZD 一节不再指 09；MathModelAgent 一节记录 9 → 7 个拆分文件的收敛）。
- **净变化**：knowledge 目录 15 → 12 个文件，`06`+`08`+`09` 共 11438 字节重复内容下线，独有条款 5 处并入 `02`/`12`/`13`/`14`。

## 2.3.2（2026-11-03）

### 参考 XiaoMaColtAI/math-modeling-skill：把语言规范与去 AI 味写进 tex

- **新**：`workshop/main.tex` 增加第二块 `% 【全文语言规范与去 AI 味】`（人称、断句、禁 AI 高频词、禁套式、禁排版腔、去填充、要具体、要有节奏、承认局限 + 自查 10 条），与【全文写作总则】并列成为模板级硬约束。
- **改**：逐章提示词补齐参考口径 —— 摘要（300~1000 字、关键词 3~5 个、五要素：数学归类/建模思想/算法思想/建模特点/主要结果）；模型假设（5~8 条、合理/简化/明确、关键假设不缺）；符号说明（一符一义、按出现顺序）；模型建立（奥卡姆：初等优先、点明原理与假设编号）；模型求解（算法选择依据 + 软件版本、中间过程不进正文、最终数值单独突出）；模型检验（结果不合理须分析原因并给修正）；模型评价（给证据、写局限、推广不造概念）。
- **改**：`scripts/build_prompts.py` 的 `extract_omnibus()` 改为抽取 `main.tex` 顶部**整段**注释区（原来遇第一条分隔线即停，去 AI 味块抽不到）；md 由 18754 → 22498 字节，节标题改为「总纲 · 全文写作总则与语言规范」。
- **新**：`references/knowledge/13-writing-injection.md` 增「七、语言规范与去 AI 味」9 条；`00-index.md` 与 `G4-writing.md` 各补一处入口（G4 增「10 条自查」勾选项）。
- **同步**：`E:\桌面\论文` 的 `论文.tex` 写入同一份【全文语言规范与去 AI 味】，7 个章节文件提示词同步更新（入口名仍是 `论文.tex`）；xelatex 两遍各 0 error，`论文.pdf` 仍 10 页。

## 2.3.1（2026-11-03）

### 去耦：只留本技能自身的检查项与提示词

- **改**：`references/checklists/G0-start.md`、`G4-writing.md` 去掉其他模板分支的指涉（CUMCMThesis / MCM / 华为杯的「另选」条目），模板项统一写成「本技能默认模板 `assets/templates/latex/workshop/`」；G4 的「CUMCM 模板：AI 声明已填」改为「`9.AI说明.tex` 已填」。
- **改**：G4 每章自查项改为指向该章 `.tex` 末尾【本章节写作提示词】，并新增「`main.tex` 顶部【全文写作总则】」的入口。
- **新**：`assets/templates/latex/workshop/main.tex` 顶部新增 `% 【全文写作总则】` 注释块（章节链、问题复制、数值单一来源、图件单一来源、表格列宽、段落成文、禁占位符、编译口径 9 条），从此写作提示词的「总纲」也在 `.tex` 里，不再只存在于 Markdown。
- **改**：`0.摘要.tex`、`1.引言.tex` 提示词里的入口名 `论文.tex` → `main.tex`，去掉对旧工程入口名的依赖。
- **删**：`main.tex` 头部「来源：E:\桌面\论文\论文.tex」的路径注释；`knowledge/11–14` 与 `00-index.md` 的「来源：科研工坊 …」漂移注记改为中性说明（第三方许可署名保留在 `LICENSE_NOTICE.md` / `VENDORED.md`，另有 `01–09`、`tools/review` 的许可署名行保留不动）。
- **改**：统一默认模板称呼 `数模工坊模板` → `默认论文模板（workshop）`（`SKILL.md`、`README.md`、`stages/04-writing.md`、模板 `README.md`、`scripts/doctor.py` 自检标签），并清掉 `plot_style.py`、`run_all.py` 注释里的外部产品名。
- **改**：`scripts/build_prompts.py` 增加 `extract_omnibus()`，从 `main.tex` 抽取【全文写作总则】写进 `10-chapter-writing-prompts.md` 的「总纲」节；重建后 18574 → 18754 字节，17 章提示词与模板逐字一致。

## 2.3.0（2026-11-03）

### 瘦身：去掉正常跑用不到的部分

- **修**：`assets/templates/latex/cumcmthesis/` 原来只有 `example.tex` 没有入口文件，`build_paper.py` 找不到 `main.tex` 直接编译不了。新增 `main.tex`（摘要 + 关键词 + 各章占位 + AI 声明 + 三线表符号表 + 附录），xelatex 实测 4 页 0 error。
- **删**：cumcmthesis 官方 demo `example.tex` 与 `figures/` 6 张演示图（f1/cat/smokeblk/upload/gongzhonghao×2）—— 正常流程不编译它们。
- **删**：运行产物与缓存 —— `texput.log`、`tools/paper-search/.cache/`（7 个 JSON）。
- **删**：无人引用的 `assets/templates/latex/huaweibei/title-img-01.png`、`tools/mechanism-diagram/references/mechanism-templates.pdf`。
- **删**：`references/knowledge/_source_norms.md`（索引里已写明“仅作溯源，不直接读取”），`00-index.md` 同步去掉该行。
- **删**：`assets/figures/reference/flowchart/` 下 8 份 `.tex` —— `flowchart.py --out` 由 `.json` 一秒钟重建；只留 spec + PDF/PNG 预览。
- **重写**：`tools/pdf/SKILL.md`（312 → 62 行）、`tools/xlsx/SKILL.md`（292 → 70 行）从上游通用手册改成数模实际用法（读题面/抽表/转图；读附件/写结果表/重算公式/进论文三线表），删上游 `pdf/reference.md`。
- **改**：`references/knowledge/05-figures.md` 去掉 DrawIO / 生成式图片的过时建议（与四路图件冲突），换成「要画什么 → 走哪一路」对照表。

## 2.2.2（2026-11-03）

### 论文主图母版换成实拍图（用户上传件入库）

- `assets/figures/reference/roadmap/` 手绘 8 张 SVG 版式全部撤掉，换成用户上传的 **5 张实拍母版**：`grouped-tasks`（任务分组横排）、`nested-cluster`（总分嵌套）、`quad-matrix`（2×2 任务矩阵）、`multi-panel`（多面板拼合）、`staged-steps`（分步串联）。
- 每张出三件：`src/*.jpg`（原始件，保出处）、`*.png`（去白边、2400 px 宽）、`*.pdf`（300 dpi 嵌入）。`index.json` 补 `use` / `pdf` / `source` 字段。
- 视觉规范重新按母版实测写：虚线/点划线双档、深蓝 #1F4E79 左上角标、capsule 节点、竖排指标条、灰底椭圆方法标注、块状大箭头、线上约束词、红叉弃用分支；配色取母版采样值（#92D051 / #ADC9A4 / #FFD966 / #FDEBB5 / #A4BAE0 / #CCDFEA / #F8CCB0 / #DAC3DE / #A8C6C9）。
- 删除 `tools/paper-figure/scripts/build_reference_sheets.py`（重绘生成器随旧母版一起下线）；新增 `import_plate.py`：`--src` 一张新图即自动去白边、出 2400 px PNG + PDF、写进 `index.json`。`select_reference.py` 支持 `--pdf` 复制 PDF。
- 同步更新 `tools/paper-figure/SKILL.md`、`assets/figures/reference/README.md`、`references/stages/03-figures.md`、`LICENSE_NOTICE.md`、`VENDORED.md`。

## 2.2.1（2026-11-03）

### 论文主图参考版式重绘

- `assets/figures/reference/roadmap/` 8 张母版（SVG + PNG + PDF）全部重绘，换成「虚线分组框 + 左上角标 + 多色圆角节点 + 细黑箭头」的框架图风格。
- 配色照架构图取色：蓝 #BDD7EE/#DEEBF7、金 #FFD966/#FFC000、绿 #A9D18E/#D5E8D4、蜜桃 #F8CBAD/#F4B183、淡紫 #D9C3E9、钢蓝 #4472C4、墨青 #23566B；分组框五族淡底 + 同族虚线。
- 八张各走一套结构：纵向 / 横向 / 分层（三面板）/ 三栏（三面板）/ 中心椭圆辐射 / 2×2 闭环 / 时间轴（上下交错）/ 模块（2×3 + 输出条）。
- 版面按内容定高（900pt 宽，高 315–540pt），节点文字增大到 22px（15cm 插入约 9pt 可读），不加副标题、编号、页脚等说明文字，内容沿用原版标签。
- 新增 `tools/paper-figure/scripts/build_reference_sheets.py`：一条命令重出 8 张 SVG；`render_figure.py` 再导 PNG/PDF。
- `tools/paper-figure/SKILL.md` 与 `assets/figures/reference/README.md` 补「视觉规范」表（分组框/角标/节点/箭头/配色/字号），复刻母版时照抄。

## 2.2.0（2026-11-03）

### 默认模板换成「数模工坊模板」

- 新增 `assets/templates/latex/workshop/`：`format.cls` + `main.tex` + 17 个章节 `.tex` + `fonts/`（思源宋体 + 隶书），整目录复制即可编译（已 xelatex 实测 0 error）。
- **设为默认模板**：S4 未指定赛事时一律用它；CUMCMThesis / MCM / 华为杯 / default 降为按赛事选用。
- 每个章节文件末尾自带【本章节写作提示词】（摘要版式、引言结构、模型建立三段式、检验/评价写法、表格列宽公式、图宽档位等）。
- 新增 `scripts/build_prompts.py`：把这些提示词抽成 `references/knowledge/10-chapter-writing-prompts.md`，改模板后可一键重建。

### 科研工坊提示词移植（不含流程图）

- 新增 `references/knowledge/11-engineering-contract.md`：无人值守、目录/路径、解释器与依赖、SMOKE→生产、覆盖式迭代、完成线、长计算分阶段、缓存不作废、进程卫生、Windows 编码与库版本坑。
- 新增 `references/knowledge/12-scoring-validation.md`：得分点驱动、证据链、验证强度、学术分寸。
- 新增 `references/knowledge/13-writing-injection.md`：摘要句链与数值纪律、建模推导三段式、写作一致性、有数才成表、统计口径、引用管理。
- 新增 `references/knowledge/14-figure-contract.md`：绘图契约（横排组图、角色命名、图数档位）、防乱码/防遮挡、`plot_style` API 速查。
- **流程图相关提示词一律不移植**：`tools/flowchart` 与模板内 TikZ 流程图维持原样。

### 绘图与脚手架资产

- 新增 `assets/style/plot_style.py`（统一中文字体 + 9 套期刊配色 + `combo_axes`/`response_surface`/`legend_outside` + 存图自动体检）。
- 新增 `assets/style/check_figures.py`（出图闸门，硬伤退出码 1）与 `assets/scaffold/run_all.py`。
- 新增 `assets/templates/docx/report_kit.py`（Word 排版工具箱：三线表、目录/页码域、公式编号、题注、`page_break_before` 分页）。

### 阶段与门禁

- S0：工程资产一次铺好；无人值守时按默认填 plan 并写假设，不再卡在提问。
- S1：新增得分点表与证据链表、预测类「不预设深度模型」条款、数据图张数与角色。
- S2：`plot_style` + `check_figures.py` 闸门、得分点核账、`journal_problemN.md`。
- S3：数据图过闸门再登记 manifest；manifest 记宽高比与建议宽度。
- S4：改为「逐章读提示词 → 写 → 自查」；新增 workshop 图表语法（`longtable` 定宽列、图宽档位）；Word 分支补 W1–W5（`report_kit` 用法、域更新、验收线）。
- G1/G2/G3/G4 清单同步扩写。

### 清理

- 删除残留 `scripts/__pycache__/`、`tools/xlsx/scripts/__pycache__/`（含已废弃的 `package_submission` / `verify_docx` 字节码）。
- 明确「不做提交打包、不生成压缩包」；`04-writing.md` 交付边界同步去掉打包。

## 2.1.2（2026-11-01）

### 精简

- 移除验收/打包分支：`scripts/verify_paper.py`、`scripts/verify_docx.py`、`scripts/package_submission.py`、S5/G5 与 `tests/`。
- 技能收敛为 S0–S4、G0–G4。
- README、SKILL、契约、`tools/doctor`、`tools/review` 同步移除验收与提交包引用。

## 2.1.1（2026-11-01）

### 模板与交付

- `assets/templates/latex/default/` 补 `graphicx` / `float` / `caption` / `longtable` / `placeins`，新增 `\fig` / `\tabcaption`（自动 `\caption` + `\label`）。
- `main.tex` 顶部加入写作提示块；S4 强制复制模板、只改 `sections/`，禁止临时加包。
- 新增 Word 原生分支：S0 交付形态、S4 Word 步骤、G4/G5 Word 清单、`scripts/verify_docx.py`。
- `scripts/package_submission.py` 支持 LaTeX PDF / Word DOCX 双模式。
- `tools/paper_search` 重命名为 `tools/paper-search`，与 `name` 对齐。
- 清理未使用资产：`tests/fixtures/demo_lp`、xlsx 的 docx/pptx 校验器与 XML schema、pdf 表单脚本与 `forms.md`；体积约 8.2MB → 4.7MB。

## 2.1.0（2026-11-01）

### 结构

- 从“三阶段 + 三路图件”升级为 **6 阶段 + 6 门禁 + 四路图件**。
- 主链路改为 **LaTeX → PDF**；移除 Typst 与 17 套模板全量引入。
- 取消 `references/roles/` 角色卡；职责并入阶段文档、契约与门禁清单。
- 新增 `references/stages/`、`contracts/`、`checklists/`、`knowledge/`。
- `算法/` 迁移为 `references/algorithms/`。

### 图件

- 四路图件：数据图 / 机理图 / 论文主图 / 流程图。
- 流程图独立为 `tools/flowchart`（JSON → TikZ → PDF）。
- 论文主图精简为路线图/框架图；移除 1381 图库与 gallery 脚本。
- 新增 8 张路线图参考 + 8 张流程图参考（重绘版式）。
- 接入 11 个科研数据图模板。

### LaTeX / Word

- 引入 CUMCMThesis 2026（含 AI 使用声明）。
- 新增 MCM / 华为杯 / 通用 LaTeX 模板，并适配 Windows `fontset`。
- 新增 `scripts/latex2docx.py`：Pandoc + python-docx，支持 PDF 图转 PNG、模板宏替换、差异报告。

### 验收

- 新增 `scripts/verify_paper.py`、`build_paper.py`、`make_manifest.py`、`package_submission.py`。
- 新增 `results/results.json` 与 `figures/manifest.json` 契约。
- 新增 G0–G5 门禁清单。

### 论文搜索

- 从单一 OpenAlex 改为 Crossref + arXiv 双源；OpenAlex / Semantic Scholar 可选。
- 新增缓存、限速、退避、去重、DOI 校验。

### 评委式评审

- 新增 `tools/review/`：100 分结构、格式质量系数、P0–P3 问题、优先提分建议。
- 新增摘要独立可读性、格式门禁、AIGC 风险、模型适配性检查。
- 方法参考 BZD 评审框架与近年国赛评阅细则，本地改写，未复制原文。

### 归档

- 1381 图库 → 技能外 `_archive/paper-figure-gallery-1381/`
- 旧 `tools/docx/`、`references/roles/`、旧 `SKILL.md` 及旧 `paper-figure` / `paper_search` 说明已清理，不再随技能分发。
