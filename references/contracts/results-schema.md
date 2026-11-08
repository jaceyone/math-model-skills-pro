# 结果契约：先立键（schema.json），再填值（results.json）

两份文件，两种职责，顺序不能反：

| 文件 | 什么时候写 | 写什么 | 谁读 |
|---|---|---|---|
| `results/schema.json` | **S1，写代码之前** | 论文里要出现的每个数的**键名、含义、单位、生产者、消费者** | S2 代码照着填、S3 图照着取、S4 正文与表格照着引 |
| `results/results.json` | S2，代码跑完 | 键 → 值（唯一数值事实源） | `fill_tables.py`、`check_results.py`、`check_paper.py`、绘图脚本 |

先有 schema，代码才知道该算什么；先有 results 再补 schema，就是给结果倒着编一套名目。

## 一、`results/schema.json`

```json
{
  "version": 1,
  "project": "CUMCM-2026-A",
  "keys": {
    "problem2.control_index": {
      "label": "双通道控制后振动指标",
      "unit": "m^2 s^-3",
      "digits": 2,
      "producer": "code/problem2.py",
      "consumers": ["table:q2_index", "figure:data_p2_response", "paper:§5.3"]
    }
  }
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `label` | ✔ | 中文含义，S4 写正文/表头时直接用，不再另起名字 |
| `unit` | ✔ | 单位；无量纲写 `"-"`。表头与摘要里的单位照抄这一格 |
| `digits` | 选 | 论文里保留几位小数（0–8）；`fill_tables` 的默认格式取它 |
| `producer` | ✔ | 写这个键的脚本相对路径（`code/problem2.py`）。G2 会核对文件存在且脚本里出现该键名 |
| `consumers` | ✔ | 谁读它，至少一个：`table:<模板名>` / `figure:data_<图名>` / `paper:§5.3` / `check:<校验名>` |

**键名规则**

1. 键名 = `results.json` 里的路径，至少两级，小写 snake_case：`problem1.passive_index`、`sensitivity.damping.k_minus`。
2. 扁平点号键与嵌套对象两种写法都支持（`{"problem1": {"passive_index": …}}` 与 `{"problem1.passive_index": …}` 等价）。
3. 不同问题的同名指标必须带问题前缀，否则 `index` 这种键会被后写的覆盖。
4. **没有消费者的键删掉**：`check_contract.py` 会报 `KEY_NO_CONSUMER`。声明了没人读，等于给自己加维护成本。

## 二、`results/results.json`

```json
{
  "project": "CUMCM-2026-A",
  "generated_at": "2026-09-05T10:00:00+08:00",
  "environment": {"python": "3.11.9", "packages": {"numpy": "1.26.4", "scipy": "1.11.4"}},
  "seed": 42,
  "problem1": {
    "passive_index": 97.44,
    "active_index": 379.81,
    "validation": {"constraint_violations": 0, "checks": ["energy_balance"]}
  }
}
```

必填：`project`、`generated_at`、`seed`（无随机写 `null`）、`problems.*.validation`（约束/一致性校验结果）。

规则：

1. **键名先定后写**：先写进 schema 再写进 results；`check_results.py` 会列出"未申报键"，那些数要么申报，要么就是没人要的中间量。
2. 百分比统一存小数（`0.9766` = 97.66 %），论文里再格式化；表格用 `{{key:pct}}` 自动乘 100。
3. 单位不在 JSON 里重复写，单位在 schema 的 `unit` 里定义一次。
4. 不覆盖旧结果：重跑时更新 `generated_at` 与 `environment`，键名保持稳定。
5. 中间数组/轨迹存 `code/outputs/*.npz|csv`，`results.json` 只放标量与关键小表，别把 10 万个采样点塞进去。
6. 派生量（比值、降幅、误差百分比）也立键，别在论文里现算——现算那一步没人复核。

## 三、机器校验

```bash
python scripts/check_contract.py --project 项目N   # G1：schema 结构、消费者语法、生产者字段
python scripts/check_results.py  --project 项目N   # G2：键覆盖、生产者、表新鲜度、未申报键
```

- 退出码 0 = 过；1 = 有 ERROR；2 = schema 还没建（契约未建立）。
- 历史工程回填：先补 schema（把已经写进论文的键补全），再用 `check_results.py`（默认未申报键只 WARN）逐个收口；`--strict` 留给新工程。
- `--json` 输出结构化结果，方便外层脚本串起来跑。
