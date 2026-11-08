# 技能回归用例（evals）

本技能改的是**流程**，流程退化不报错：SKILL.md 少一句「先立键」，代码照样能跑，只是回到"跑出数来再想怎么摆"的老路。所以每次改技能，用这里的东西自证一次，而不是靠"感觉顺了"。

## 文件

| 文件 | 内容 |
|---|---|
| `evals.json` | 6 条任务用例。每条带 `assertions`，断言全是可以直接跑的判据（`check_contract.py` / `fill_tables.py --check` / `check_paper.py` 退出码），不靠人读产出 |
| `trigger_evals.json` | 18 条触发用例：10 条该触发、8 条**不该**触发（含 near-miss：纯 matplotlib 出图、xlsx 重算公式、查 TOPSIS 论文、docx 删页眉）。触发判定看 SKILL.md 的 `description` |

## 怎么跑

本技能没有测速的意义——判据是确定性的，跑得慢是因为 LaTeX 编译，不是因为技能差。所以只做 A/B 对比：

1. **改之前先快照**：`cp -r <skill> _tmp/skill-snapshot/`（`_tmp/` 已在 `.gitignore`）。
2. 用快照跑一遍用例 1–6，记下每条 assertion 过没过。
3. 改完技能，用新版本再跑一遍同一批 prompt。
4. 只关心**退化**：原来是 PASS 的变 FAIL。原 FAIL 变 PASS 是意外收获，别当成指标去优化。

每条用例的工作区独立，互不继承：`_tmp/evals/<用例名>/`，避免上一轮的 `results/schema.json` 让下一轮"看起来"通过。

## 为什么不用 benchmark 打分

`skill-creator` 里那套 pass_rate ± stddev、token/时长对比，是为**主观产出**（写作、设计）设计的——同一个 prompt 跑三次结果不一样，所以要统计。本技能的每个 assertion 都是退出码，同一输入永远同一输出，统计方差是零，跑三次只是浪费。所以这里只保留"用过 / 没过"，再加上触发用例的两类错误率：

- **该触发没触发**：用户说"帮我做这道数模题"却没人理 SKILL.md → 最贵的失败，`description` 漏了词。修 `description`，不修正文。
- **不该触发却触发**：用户只是要一张箱线图，技能却铺开 5 阶段骨架 → 用户被流程绑架。修 `description` 的边界词，或在 SKILL.md「不做什么」里补一条。

## 触发用例的判据

`description` 是唯一的触发机制，正文写得多好都不影响"要不要用"。本技能的边界：

- 该触发：出现**交付物**（论文 / 报告 / 表格 / 图要进论文）、出现**赛制**（CUMCM / MCM / 数维杯 / 华为杯）、出现**契约**（要交哪些数、表怎么跟着变）。
- 不该触发：只要**单个工具动作**（出张图、合并 PDF、重算公式、删页眉），或主题挨着但不是建模交付（查论文、推公式、写后端）。

改动 `description` 后重跑 `trigger_evals.json`，目标：10 条 true 全中，8 条 false 全不中。命中 9/8 可接受，掉到 8/8 以下说明边界词被写坏了。

## 与技能自检的分工

| | 管什么 | 命令 |
|---|---|---|
| `scripts/check_skill.py` | **包本身**能不能被正确加载：frontmatter、SKILL.md 行数、内部路径、目录、语法、BOM | `python scripts/check_skill.py` |
| `evals/` | **流程**有没有退化：同一句话还能不能把模型带到"契约先行"的路上 | 人工按上面 1–4 跑 |

前者是机器门禁，进提交前必跑；后者是改动较大时（改 SKILL.md 主链路、改门禁定义、改阶段顺序）才跑。
