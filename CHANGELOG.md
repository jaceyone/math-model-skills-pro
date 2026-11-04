# CHANGELOG

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
