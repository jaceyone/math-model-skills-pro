# 表格契约：骨架手写，数值机填

一句话：**人在 S1 写列名、单位、行标签和 `{{key}}`；S2 由 `fill_tables.py` 把数填进去；S4 只 `\input` 生成的 `.tex`。**

手抄一张表 = 给自己埋一个只会在终稿前炸的雷：代码改了、数变了、表还是旧的，而 `check_paper.py` 只能核对"正文数字在不在 results.json 里"，核不到"表里那格是不是三个月前的值"。表格生成后，三者永远同源。

## 一、文件与位置

| 文件 | 谁写 | 内容 |
|---|---|---|
| `reports/tables/<名>.tpl.md` | 人（S1） | markdown 表 + 前置注释 + `{{key}}` 占位 |
| `results/tables/<名>.md` | `fill_tables.py` | 填好的表（人读、贴进 md 报告） |
| `results/tables/<名>.tex` | `fill_tables.py` | booktabs 表（论文 `\input`） |
| `results/tables/_render.json` | `fill_tables.py` | 每张表的行数/列数/用到的键/渲染时间 |

模板名（去掉 `.tpl.md`）就是 schema 里 `table:<名>` 引用它的名字，也是 `\label{tab:<名>}` 的默认值。改名要三处一起改。

## 二、模板写法

```markdown
<!-- table: q2_index | caption: 场景 2 指标对照 | label: tab:q2_index | format: auto -->

| 情形 | 指标 $I_h$ | 降幅 |
|---|---|---|
| 被动 | {{problem2.passive_index:.2f}} | — |
| 双通道 | {{problem2.control_index:.2f}} | {{problem2.reduction_pct:pct}} |
| 主质量 $M$ | 2000* | — |

注：$I_h$ 单位为 $\mathrm{m^2\,s^{-3}}$，$T=10$ s。
```

前置注释字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `table` | ✔ | 表 id，与文件名一致 |
| `caption` | ✔ | 表题（表上方）。S4 不再重写表题，直接沿用 |
| `label` | 建议 | `tab:<名>`，默认由文件名生成；论文 `\ref` 用它 |
| `format` | 选 | `auto`（默认，`@{}lrrr@{}` 自然列宽）／`fixed`（定宽列，列宽之和 = 1.04 − 0.04N，与【列宽记账】一致） |
| `note` | 选 | 表注；表后 `\footnotesize` 一段 |

## 三、占位语法

| 写法 | 输出 | 用途 |
|---|---|---|
| `{{key}}` | 按 schema 的 `digits` 格式化 | 大多数指标 |
| `{{key:.3f}}` | Python 格式串 | 指定精度/科学计数 `:.3e` |
| `{{key:pct}}` | 乘 100 加百分号（tex 自动 `\%`） | 降幅、占比（JSON 里存小数） |
| `{{key:si}}` | 千分位（md 逗号，tex 细空格 `7\,225\,200`） | 刚度、质量这类大数 |

规则：

1. **结果格里不许出现裸数字**：`97.44` 会被 `check_contract.py` 判 `TABLE_HARDCODE`。
2. **设计常数（题面给定）**：把该列表头写成 `取值*`，或在格子里写 `2000*` 显式声明；这两种写法只用于题面参数、实验设定，不许用来塞结果。
3. 格式化后的值不参与"再四舍五入"：`digits` 定一次，摘要、正文、表里都用它。
4. 占位符可以出现在表头（如单位列），一样会校验。
5. 表里只放数；长说明进 `note` 或正文，不要塞整句。

## 四、渲染与校验

```bash
python <skill-root>/scripts/fill_tables.py --project 项目N            # 渲染
python <skill-root>/scripts/fill_tables.py --project 项目N --check    # 只校验（G2/G4 必跑）
```

退出码：`0` 一致／`1` 有错误（键缺失、格式串非法、生成物落后于 `results.json`）／`2` 一张模板都没有。

- `--check` 会把"磁盘上的 `.md`/`.tex` 与用当前 `results.json` 重新渲染的结果"逐字比较：不一致就是过期，必须重跑。
- 键名写错时不会静默变成空：该格渲染成 `??` 并以 ERROR 退出（tex 里是 `\textbf{??}`，编译能过但你一定看得见）。

## 五、论文里怎么用

```latex
% paper/sections/5_problem2.tex
\input{../results/tables/q2_index.tex}

如表~\ref{tab:q2_index}，双通道把 $I_h$ 从 217.96 压到 5.11，降幅 97.66\%。
```

- 路径相对 `paper/main.tex`；与前缀 `../figures/` 同理，只出现在 LaTeX 里，Python 脚本禁止写相对 `../`。
- 生成的 `table` 环境自带 `\caption`、`\label`、`\toprule/\midrule/\bottomrule`，模板 `default`/`mcm`/`huaweibei` 都加载了 `booktabs` + `array`，可直接用。
- 跨页长表（几十行）不放模板里生成：`fill_tables` 只出 `table`，长表由 S4 手写 `longtable` 并同样从 `results.json` 取键值（或用 `fill_tables` 生成后改成 `longtable` 环境）。
- `format: fixed` 生成的列宽已按 `1.04 − 0.04×N` 记账，直接用，别再手改宽度。

## 六、反例

| 反例 | 后果 |
|---|---|
| S4 直接从论文里复制数字建表 | 重跑代码后表不更新，且 `check_paper` 查不出（数字本身还在 results.json 里） |
| 表里手写 `97.44` 又没标 `*` | G1 直接判 `TABLE_HARDCODE` |
| 表模板里用了 `problem1.index`，schema 里写的是 `p1.index` | 键名对不上，渲染出 `??` |
| 渲染完又手改 `results/tables/*.tex` | 下次 `--check` 报过期；改模板才对 |
