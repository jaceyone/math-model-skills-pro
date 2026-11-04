# 结果 JSON 契约

`results/results.json` 是论文数值的唯一事实源。

## 最小结构

```json
{
  "project": "CUMCM-2026-A",
  "generated_at": "2026-09-05T10:00:00+08:00",
  "environment": {
    "python": "3.11.9",
    "packages": {"numpy": "1.26.4", "scipy": "1.11.4", "pandas": "2.2.2"}
  },
  "seed": 42,
  "problems": {
    "Q1": {
      "model": "MILP",
      "metrics": {
        "objective": 123.45,
        "gap": 0.001,
        "runtime_sec": 12.3
      },
      "tables": ["results/tables/q1_solution.csv"],
      "figures": ["data_q1_convergence"],
      "validation": {
        "constraint_violations": 0,
        "checks": ["all_demand_met", "capacity_ok"]
      }
    }
  },
  "sensitivity": {
    "Q2": {
      "parameter": "alpha",
      "values": [0.8, 0.9, 1.0, 1.1],
      "objective": [120.1, 121.5, 123.45, 126.0]
    }
  }
}
```

## 必填

| 字段 | 说明 |
|---|---|
| `project` | 题目标识 |
| `generated_at` | ISO 8601 时间 |
| `seed` | 随机种子；无随机则为 `null` |
| `problems` | 以 `Q1`、`Q2`… 为键 |
| `problems.Qn.model` | 模型/算法名 |
| `problems.Qn.metrics` | 关键数值；键名稳定 |
| `problems.Qn.validation` | 约束/一致性校验结果 |

## 规则

1. 键名用英文 snake_case，单位在论文中写清。
2. 所有论文中出现的核心数值必须能在 `metrics` 或 `tables` 中找到。
3. 百分比统一存小数（0.85 表示 85%），论文中再格式化。
4. 不覆盖旧结果；重跑时写 `generated_at` 与 `environment`。
5. 不允许在代码里硬编码论文数值；必须从计算结果写入。
6. `sensitivity` 记录参数、取值、结果，供论文灵敏度节使用。
