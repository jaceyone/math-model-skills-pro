# 图件注册表契约

`figures/manifest.json` 是论文图件的唯一来源。

## 结构

```json
{
  "figures": [
    {
      "id": "data_q1_convergence",
      "route": "data",
      "source": "code/problem1.py",
      "data": "code/outputs/q1_history.csv",
      "outputs": ["figures/data_q1_convergence.pdf", "figures/data_q1_convergence.png"],
      "caption": "问题一求解收敛曲线",
      "section": "5_problem1",
      "status": "ok"
    },
    {
      "id": "flow_q1_solution",
      "route": "flow",
      "source": "tools/flowchart/scripts/flowchart.py",
      "spec": "figures/flow_q1_solution.json",
      "outputs": ["figures/flow_q1_solution.pdf", "figures/flow_q1_solution.png"],
      "caption": "问题一求解流程",
      "section": "5_problem1",
      "status": "ok"
    }
  ]
}
```

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 唯一标识，与文件名一致 |
| `route` | 是 | `data` / `mech` / `paper` / `flow` |
| `source` | 是 | 生成脚本或工具 |
| `data` / `spec` | 视情况 | 数据图写 `data`；流程图写 `spec` |
| `outputs` | 是 | 实际文件路径列表 |
| `caption` | 是 | 论文图注 |
| `section` | 是 | 放入的章节文件名（不含扩展名） |
| `status` | 是 | `ok` / `warn` / `missing` |

## 规则

1. 每张进论文的图必须登记。
2. `outputs` 中的文件必须存在。
3. `route` 只能是四路之一。
4. 同一张图不得跨路线重复登记。
5. 数据图 `data` 必须指向真实数据文件。
6. 论文正文引用的图必须在 manifest 中；生成但未引用的图标记 `warn`。
7. `scripts/make_manifest.py` 可生成初版，人工补 `caption` / `section`。
