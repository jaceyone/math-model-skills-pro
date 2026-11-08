---
name: mechanism-diagram
description: "数学建模论文的机理图 / 几何示意图：从论文正文、题目分析报告或数据表读出模型，产出可编译的 TikZ 源码并出图（中文图交 pdf+png，svg 仅纯英文图）。覆盖可行域、相平面、受力自由体、光路、几何推导构造、仓室传播链、控制体微元、状态转移、模型内部机理、指标层次、元胞自动机、临界双态共 12 类。何时用：需要'讲清方法怎么来的'的示意图、几何推导配图、模型结构图，或用户提到机理图/示意图/可行域/相平面/受力图/光路/ TikZ。不画数据结果图（走 matplotlib），也不画技术路线图和流程图（走架构件）。触发词：机理图、机制图、示意图、原理图、可行域、相平面、受力分析、光路图、几何推导、SEIR、马尔可夫、控制体、PINN、TikZ、公式推导配图。"
metadata:
  phases: model-build, assemble, chat
---

# 机理图（TikZ · 数学建模论文）

TikZ 在"数学符号 + 精确几何 + 公式标注"这类图上是天花板：矢量无损、公式与正文字体统一、
坐标和角度可以精确到小数点后。本件负责把**已有的模型和几何关系**翻译成一篇论文里那些
"讲清机理"的示意图，交付的是**能编译、能裁边、能出图的 .tex 源码**，不是一张画出来的像素图。

三条不可协商的前提：

1. **先探环境再动笔**（下面「探环境」节）。TikZ 版本、可用库、出图链路决定了能写什么语法。
2. **绝不编造数据**（「数据红线」节）。图里没有的数字，宁可不画。
3. **规范来自 `references/tikz_rules.md`**，本件只补机理图特有的判定与出图闭环，不重复抄写规则正文。

<!-- TOC:BEGIN 自动生成，勿手改；重跑 python scripts/gen_ref_toc.py --write -->
## 目录（按行号跳读，不必整篇加载）

| # | 小节 | 行号 |
|---|---|---|
| 1 | 从材料到产出 | 38 |
| 2 | 不画什么（越界就换工具，别硬用 TikZ） | 59 |
| 3 | 探环境（换机器必跑，本机已实测可跳过） | 71 |
| 4 | 配置 | 142 |
| 5 | 画哪张图 | 171 |
| 6 | 数据红线 | 186 |
| 7 | 编写规范 | 204 |
| 8 | 编译与出图 | 261 |
| 9 | 交付清单 | 313 |
| 10 | 机理图交付 | 318 |

<!-- TOC:END -->

## 从材料到产出

| 你手上的材料 | 能出什么 |
|---|---|
| 论文正文（含模型假设、建模公式、`\begin{figure}` 占位） | 与公式一一对应的机理图；正文里已有的符号直接进图 |
| 题目分析报告 / 赛题原文 | 题面给定常量、几何关系、约束条件，出可行域、受力、光路、几何构造图 |
| 数据表（csv/xlsx） | **只用于判断"该画哪张图"**；表里的数据本身不进机理图（那是结果，归 matplotlib 数据图） |
| 口述的模型结构（"我用了 SEIR + 马尔可夫"） | 符号级机理图：仓室链、状态转移、模型内部数据流 |
| 材料不足以确定几何关系（缺尺寸、缺约束式） | 只画**符号级**图（用 $L$、$\theta$、$H$ 占位），并在交付清单里写明哪张图因缺材料未画 |

产出物：每张图固定三件套（`.tex` 是交付主体）+ 一份全图汇总，都落在 `MH_OUT_DIR`（默认 `figures/`）：

```
<MH_OUT_DIR>/mech_<图名>.tex     % 独立可编译源码（一图一文件）
<MH_OUT_DIR>/mech_<图名>.pdf     % 矢量，\includegraphics 用这个
<MH_OUT_DIR>/mech_<图名>.png     % 肉眼验收/预览用，MH_PNG_DPI（默认 300）
<MH_OUT_DIR>/mech_includes.tex   % 各图的 \begin{figure} 嵌入片段汇总
```

`.svg` 不是默认产出：只有图内文字是纯英文（`MH_FIG_LANG=en`）时才补一份，中文图出不了 svg。

## 不画什么（越界就换工具，别硬用 TikZ）

| 需求 | 该用什么 | 为什么不是这里 |
|---|---|---|
| 散点/折线/柱状/热图/箱线等**结果图** | matplotlib | 数据点多、要程序化生成，TikZ 手写坐标必错 |
| 技术路线图、研究流程图、甘特图、组织结构 | 架构图件（④B SVG 流程图 / ③ roadmap 母版） | 本件范围只做**机理与几何示意**，`tikz_rules.md` 的技术路线图模板 4/9/10 不在本件内 |
| 写实三维场景、透视效果图 | 图像生成模型 | TikZ 的 3D 是示意级，写实会失真 |
| 简单框图但需要拖拽改 | ④B SVG 流程图（浏览器里点字直改） | 交付形态不同 |

边界判据一句话：**这张图的价值在于"精确的几何关系 / 公式刻度 / 符号标注"吗？** 是，归本件；
只是"几个框加箭头"，归架构图件。

## 探环境（换机器必跑，本机已实测可跳过）

**不要凭记忆写语法。** PGF 各版本键名不兼容，本机就实测踩到过 6 处
（见「编写规范」末尾的 3.1.11a 坑清单）。

**1. 工具链在不在**

```bash
for b in xelatex pdflatex lualatex latex latexmk pdfcrop pdftoppm dvisvgm pdffonts gs convert miktex; do
  command -v "$b" >/dev/null 2>&1 && echo "$b OK" || echo "$b MISSING"
done
```

**2. TikZ/PGF 版本**——用 Write 工具落一个探测文件（ 别用 shell 内联 LaTeX，反斜杠开头会被
命令安全校验当成 UNC 路径拒掉），内容：

```latex
\documentclass{article}
\usepackage{tikz}
\typeout{PROBE_PGF=\pgfversion}
\begin{document}
x
\end{document}
```

```bash
xelatex -interaction=nonstopmode probe.tex >/dev/null 2>&1; grep -m1 "^PROBE_" probe.log
```

**3. 本件需要的库能不能加载**——同样用 Write 落一个文件，把要用的库一次 `\usetikzlibrary`：

```latex
\documentclass{article}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc,patterns,
  decorations.pathmorphing,automata,quotes,shadows,backgrounds,fadings,fit}
\begin{document}
\begin{tikzpicture}\node[draw,rounded corners,fill=blue!5]{probe};\end{tikzpicture}
\end{document}
```

退出码非 0 时，log 里的 `Unknown library` 会点名是哪个库，摘掉它重试，并**把摘掉的库记进
「已知坑」**，别让下一张图再撞。

**4. 中文链路**——`ctex` + `xelatex` 出一个"测试"字，能出 PDF 且肉眼看得见字才算通。
报字体缺失时在 preamble 里就地换字体（`SimHei` / `Microsoft YaHei` / `SimSun` 这三个 Windows
自带名先试，或调 `ctex` 的 `fontset` 选项）——这是就地排错，不设配置项。

**别用 `pdftotext` 判断中文有没有渲染。** 本机实测本机实测 `xelatex` 和 `pdflatex` 产出的 PDF 里
中文**都提不出文本**（`pdffonts` 看字体才是准）。

本件默认 `xelatex`：`pdffonts` 显示中文以 `CID TrueType / Identity-H` 正确嵌入。
`pdflatex + ctex` 在本机**实测也能出中文**（不是"会挂"），但它退化成
`TrueType / WinAnsi` 8-bit 子集，字形数超 256 有截断风险，所以不作默认。

**本机实测结论（2026-09-27，MiKTeX）**，直接抄进 `.env`：

- PGF/TikZ **3.1.11a**；`xelatex pdflatex lualatex latex latexmk pdfcrop pdftoppm dvisvgm miktex` 全在。
- **没有** `tlmgr`（MiKTeX 不用它，装包走 `miktex-console` 或自动装）、**没有** ImageMagick、
  **没有** Ghostscript。
- PNG 只能 `pdftoppm` 从 PDF 出，不要试 `convert` / `gs`；SVG 只能 `dvisvgm` 从
  **`latex` 产出的真 `.dvi`** 出（且图内无中文），PDF 无法二次转 SVG。全表见「编译与出图」。
- 出图链路已端到端复验（2026-09-27）：单图 `[border=3pt]{standalone}` 依次跑 `xelatex`、
  `pdfcrop`、`pdftoppm -r 300`，得 571×396 px，0 error / 0 overfull。
- 库可用性：`automata patterns decorations.* backgrounds shadows shadows.blur fadings
  intersections arrows.meta positioning calc shapes.geometric shapes.misc matrix trees
  quotes scopes petri fit spy through` 全部 OK；`graphdrawing`（要 LuaTeX）、
  `circuits.electrical`、`bayes` 三个 **不可用**。宏包 `tikz-3dplot circuitikz pgfplots ctex
  standalone animate` OK。
- 单张 standalone 图编译约 3 秒；`references/mechanism-templates.tex` 全量 13 页 ≈ 40 秒。

## 配置

`.env.template` 复制成工作区根目录的 `.env`（或写进 `AGENTS.md` 同名条目）。
优先级：**环境变量 > `.env` > 下表默认值**。开画前先 `cat .env`，读不到的项按默认值走，不猜。

表里只放**因机器或题目而异、用户确实可能给相反要求**的项，别的不要往里加：

| 开关 | 默认 | 管什么 |
|---|---|---|
| `MH_XELATEX` | 自动探测 | 编译器绝对路径；留空 = `command -v xelatex` |
| `MH_FIG_LANG` | `zh` | 图内文字语种；`en` = 英文论文/美赛。一张图内不许中英混排（LSTM、PINN 这类术语缩写除外） |
| `MH_PNG_DPI` | `300` | PNG 分辨率；投稿常 300 或 600 |
| `MH_COLOR_SCHEME` | `auto` | 框图类走 A–F 六套；**几何示意类不走 A–F**，走配色铁律 |
| `MH_OUT_DIR` | `figures` | 产出目录，相对工作区根 |

**其余一律是写死的规则，不设开关，也不要自行加开关**——用户要例外会自己开口：

- **产出**：`.tex` + `.pdf` + `.png` 三件套一律出（`.tex` 是交付主体，`.pdf` 进论文，`.png` 用来肉眼验收）；
  只有图内纯英文时才额外补 `.svg`。要"只出源码别编译"或别的规格，问用户。
- **命名**：`<MH_OUT_DIR>/mech_<图名>.{tex,pdf,png}`，前缀固定 `mech_`。
- **排版**：`standalone` 留白固定 `border=3pt`（标注被切时才调大）；编译后跑一次 `pdfcrop`
  （本机缺 Perl 时 `pdfcrop` 会报 `could not find the script engine 'perl'`，**直接跳过**，
  `standalone` 已紧裁，用 `pdfinfo` 看 `Page size` 确认无大留白即可）；
  图下说明只进不超过 `0.5\textwidth` 的窄 parbox，长公式进正文。
- **配色**：同一篇论文的多张图共用一套配色，不逐张换。
- **验收**：编译 0 error / 0 overfull **加**用 Read 打开 PNG 逐张肉眼看，两条都过才算完。
- **自修**：报错最多改 3 轮，仍不过就把 log 的 `! ` 行原文交给人，不许为过编译删内容。
- **清理**：编译成功后清掉 `.aux`/`.log`；编译失败时留着 log 一并报人。

## 画哪张图

判定表在 `references/diagram-taxonomy.md`：先按它的第 1 节确认这张图该不该由本件画，
再按第 2 节「模型类别对应的机理图触发表」（优化类 / 微分方程·动力系统 / 几何·物理机理 /
评价·决策 / 预测·随机过程 / 机器学习模型类六大类）逐行匹配，每行都写了**画什么、关键技巧、
易翻车**。

命中多行时按两条原则取舍：**一图一机理**（一张图只讲一件事，两件事就两张图）、
**优先画"评委看不懂模型时才需要看"的那张**（几何构造 > 通用模型结构图）。
默认一张图说清；只有同一机理的步骤挤在一起糊掉了、或阶段之间跳跃太大时，才拆成多面板序列图。

现成骨架：`references/mechanism-templates.tex`，12 个模板 + 标注技巧片段，
**全部在本机 3.1.11a 上编译通过并逐张肉眼验收过**（13 页 0 error / 0 overfull）。
用它是"抄构造方式"，不是"抄内容"——坐标、符号、标注必须换成当前题目的。

## 数据红线

图里的数字只有三类合法（详表见 `diagram-taxonomy.md` 第 3 节）：

- **题面给定的常量**：螺距 55cm、焦距 $f$、初速、$k=10^4$——来自原题、可追溯、恒定。
- **符号量**：$t^*$、$L_i$、$\theta_c$、$x^*_1$——用符号表达"得到了什么"。
- **这张图自身的几何量**：为了把图画对而反推的坐标、角度、比例（例如为了满足
  $1/u+1/v=1/f$ 而定的像点位置）。这是"画得对"，不是"编数据"。

**绝对禁止：**

- **代码求解算出的结果数值**写进图（`t^*=412.473838`、$p_{\min}=45.03\,\text{cm}$）。
  理由：`.tex` 里手敲的数字**没有任何溯源闸**，一旦与正文/`results.json` 不符查不出来，
  是三不管地带。结果数交给数据图、结果表、正文——那里有闸。
- **编造材料里没有的数据、几何尺寸、约束式**。缺就画符号级图，缺材料的图在交付清单写
  "缺材料，未画"，不许用"看起来合理"的数字把图填满。
- 把数据表里的**样本观测值**当机理图内容（那是结果图）。

## 编写规范

`references/tikz_rules.md` 是本件的规范正文（原样收录，未删减）。**适用小节**：

| 小节 | 怎么用 |
|---|---|
| TikZ 适用范围 | 动笔前先过一遍 |
| 赛题特征到 TikZ 图类型的触发表 | 与 `diagram-taxonomy.md` 第 2 节并用，后者更细 |
| 几何示意图配色专用规则 | **本件主用小节**。颜色铁律表、≤3 色上限、几何示意图禁止项 1–5、自检清单 6 条 |
| 零容忍的低级错误（编译/视觉灾难/重叠/箭头/尺寸） | 全量适用 |
| 建议（文字标签/尺寸控制/布局技巧/preamble 依赖） | 全量适用 |
| 自检清单 + 中文节点宽度计算公式 + 防遮挡规则 | 全量适用 |

**不适用小节**（本件范围外）：

- `布局模板参考` 里的技术路线图模板 4/9/10、`流程/路线布局`、以及任何"按论文类型随机选模板"
  的要求——那些属于架构图/技术路线图，不是机理图。
- `编译后自检（必须执行）` 小节里对 `tikz_check.sh` 的调用。本件不带这个脚本，
  验证方式见「编译与出图」；该小节其余部分（`grep Overfull` 那一条）照用。

两条最高频翻车的铁律就地复述（其余去读原文）：

1. **文字、数字、公式、符号、坐标轴标签、图例文字一律纯黑**（`black`，要低调可 `black!85`，
   禁止低于 `!80`）。彩色只给**线条 / 曲线 / 箭头 / 关键点 / 区域填充**。要强调用
   `\bfseries` 加粗或加大字号，绝不靠把字变红变蓝。
2. **节点选项里有 `fill=<非 none>` 时，设文字色必须写 `text=black`，绝不裸写 `black`**。
   裸色名等价于 `color=`，会同时设描边和填充，把浅填充覆盖成黑填充，整块渲染成一条纯黑块，
   文字全看不见。这是"图例框变黑块"的唯一根因。

preamble 骨架（一图一文件）：

```latex
\documentclass[border=3pt]{standalone}   % 留白固定 3pt；外侧标注被切时才调大这个值
\usepackage{ctex}            % 中文图必备，配 xelatex；纯英文图（MH_FIG_LANG=en）去掉这行，届时 pdflatex 也能用
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc,patterns,
                decorations.pathmorphing,automata,quotes,shadows}
\begin{document}
\begin{tikzpicture}[scale=0.9,font=\footnotesize,line width=0.7pt]
  % 图内只放：坐标/曲线/辅助线/关键点/短符号标注
  % 长公式推导、多行参数说明一律写进论文正文，不焊进这个文件
\end{tikzpicture}
\end{document}
```

多张图合一（批量预览用的联系表）才把 documentclass 换成 `[multi=tikzpicture,border=3pt]`，
每个 `tikzpicture` 自动单独成页。

**3.1.11a 实测坑**（写新图同样注意；`references/mechanism-templates.tex` 头部也记了其中几条）：

- `grid[x step=.., y step=..]` 报未知键，改用默认步长 `\draw[gray!50,very thin] (0,0) grid (X,Y);`
- `drop shadow` 必须 `\usetikzlibrary{shadows}`
- 自定义样式名不要用 `dash`（与内置 `/tikz/dash` 冲突，报 "key requires a value"），换 `grpbox`
- 节点文字里不要出现裸 `/`（会被当路径分隔符），改"与"或 `\slash`
- `positioning` 的 `above right=.. of \p` 只吃**具名节点**，不吃字面坐标，改用显式 `at (x,y)`
- 分组虚线框必须在节点**之前**画；`fill=gray!2` 后画会盖住节点，看起来"节点消失"

## 编译与出图

```bash
XELATEX="${MH_XELATEX:-xelatex}"
tex="figures/mech_xxx.tex"; base="${tex%.tex}"

# 1) 编译（-halt-on-error 让错误立刻停，别静默出残页）
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$(dirname "$tex")" "$tex"

# 2) 裁边（可选）——缺 Perl 时 pdfcrop 直接报 script engine 错，跳过即可：
#    standalone 的 border=3pt 已经是紧裁，pdfinfo 看 Page size 没有大留白就别管它
pdfcrop "$base.pdf" "$base.pdf"

# 3) 出 PNG——本机唯一可用链路
pdftoppm -r "${MH_PNG_DPI:-300}" -png -singlefile "$base.pdf" "$base"

# 4) 需要 SVG 时（只对纯英文图成立，中文图跳过这步）：
#    latex 自己就写 .dvi（不需要 -no-pdf），dvisvgm 能吃；中文图用 ctex 会注入 PDF special，全废
latex -interaction=nonstopmode "$tex" && dvisvgm -n -o "$base.svg" "$base.dvi"
```

**SVG 的三条实测死路**，别再试：

| 命令 | 实测结果 |
|---|---|
| `xelatex -no-pdf` 出的 `.xdv` 喂 `dvisvgm` | dvisvgm 报 `277 PDF specials ignored`，页面框错量成 9pt×7pt，SVG 内容跑到视窗外 |
| `pdflatex -no-pdf` | MiKTeX 直接 FATAL：`unknown option`（pdflatex 不认这个开关） |
| PDF 转 SVG | 本机无 Ghostscript、无 ImageMagick，没有可用转换器 |

结论：**中文机理图只能交 PDF 加 PNG**。要 SVG 就得把图内文字换成英文并去掉 `ctex`，
且接受公式字体与正文不一致。所以 `.svg` 只在 `MH_FIG_LANG=en` 时才出，不是默认产出。

**验收 = 编译 0 error/0 overfull + 肉眼读 PNG**，两条都要过：

```bash
grep -c "Overfull\|Underfull" "$base.log"   # 必须是 0
```

然后用 Read 工具**打开渲染出的 PNG 逐张看**。编译通过只说明语法对，
不说明图画对——本件模板库实测抓出的缺陷**全部**是"0 error 但图是错的"：方块浮在斜面上方、
光路不满足 $1/u+1/v=1/f$、视线三点不共线、标签压在框边线上、分组框盖住节点、
角度弧量错了基准边、Moore 邻域的跨度箭头压在网格上。**这些 grep 永远查不出来。**

看的时候按 `tikz_rules.md`「几何示意图自检清单」6 条走一遍：主曲线颜色对不对、总色数 ≤3、
文字是否全黑、同焦点标签是否用引线分散、远端标签是否有引线、长公式是否已挪进正文。

报错自修：改完重编译，最多 3 轮。仍不过就停下来，把 log 里的
`! ` 行原文交给人，不要为了过编译把内容删掉。

**本件不带自检脚本。** `tikz_rules.md` 里提到的 `tikz_check.sh` 不在本件范围内，
不要去找它、不要为它改路径、不要因为缺它而中止。验证就是上面那两条。

## 交付清单

交付时逐张列全，缺材料的图也要列出来写明未画：

```markdown
## 机理图交付
| 文件 | 对应模型/公式 | 图型 | 材料来源 | 验收 |
|---|---|---|---|---|
| figures/mech_feasible_region.pdf | 问题1 的 LP 模型 (2) | 可行域 | 题目分析报告 §2.1 | 编译 0/0 + 已读图 |
| figures/mech_optics.pdf | 问题3 成像关系 (7) | 光路 | 题面给定 f=1.5 | 编译 0/0 + 已读图 |
| —（未画） | 问题4 三维接触几何 | — | 缺材料：无表面方程 | — |

嵌入：figures/mech_includes.tex（各图 \begin{figure} 片段，width=0.82\textwidth + keepaspectratio + 唯一 \label）
```

嵌入片段固定写法（图例只在 ≤2 行窄 parbox 内，长公式进正文）：

```latex
\begin{figure}[H]\centering
  \includegraphics[width=0.82\textwidth,keepaspectratio]{figures/mech_feasible_region.pdf}
  \\[2pt]
  \parbox{0.5\textwidth}{\footnotesize\centering   % 宽度上限 0.5\textwidth，禁 0.85~0.92 满宽
    实线：约束边界\quad 虚线：等高线\quad ●红：最优点}
  \caption{线性规划可行域与最优解的几何位置}\label{fig:mech-feasible}
\end{figure}
```

`keepaspectratio` 不许省（省了宽图会被拉扁）；`\label` 每张唯一；图内不写图题
（图题是 `\caption` 的活，写进 tikz 会撑大 bounding box）。
