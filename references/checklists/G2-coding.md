# G2 代码门禁

## 〇、契约兑现（机器判据）

- [ ] `python scripts/check_results.py --project 项目N` 退出码 0（键覆盖、生产者存在、表未过期）
- [ ] `python scripts/fill_tables.py --project 项目N --check` 退出码 0（表与 `results.json` 一致）
- [ ] schema 里声明的键**全部**在 `results.json` 里有值（缺一个就是漏算，要么补算要么回 S1 删键）
- [ ] 新算出来的指标已先补进 schema（未申报键已被逐条说明或删掉；`--strict` 下为 0）
- [ ] 每个键的 `producer` 脚本真实存在且确实写这个键
- [ ] `results/tables/*.md|.tex` 是 `fill_tables.py` 生成的，**没有手改过生成物**
- [ ] 论文要用的表都已在 `reports/tables/` 有骨架（S2 结束时不剩"以后手打一张表"的债）

## 一、代码与工程

- [ ] 每个子问题有独立代码文件，能单独 `python code/problemN.py`
- [ ] `plot_style.py` 已从 `assets/style/` 复制进 `code/`，绘图脚本第一行 `apply()`
- [ ] 未在脚本里改 `rcParams["font.family"]/["font.sans-serif"]`
- [ ] 代码从头到尾可运行（`run_all.py` 全 0，不是"应该能跑"）
- [ ] 随机种子固定；多次独立运行用可复现种子序列
- [ ] 长实验分阶段落盘（有 checkpoint / 中间表），savefig 不在末尾一次性执行
- [ ] 未后台跑任务、未删已有缓存、未堆 `_v2/_final`
- [ ] 运行命令写入 `code/README.md`
- [ ] 依赖写入 `requirements.txt` 或环境说明
- [ ] `results/results.json` 已生成，且**只填 schema 里的键**（键名逐字一致）
- [ ] 约束/边界校验通过，结果写进 `validation`
- [ ] 中间数组落 `code/outputs/`，`results.json` 只有标量与小表
- [ ] 路径用 `ROOT = Path(__file__).resolve().parents[1]`，无 `../figures/`
- [ ] 数据图输出到 `figures/data_*.png/.pdf`，≥260 dpi，且只读图件规划 `reads:` 里的键
- [ ] 在**项目根**跑 `python check_figures.py` 退出码 0（压字/空面板/平线/乱码为 0）；退出码 2 表示「没找到 figures/、没体检任何图」，等于没过，别当通过
- [ ] 数据图与 `results.json` 数值一致
- [ ] 灵敏度分析已真实重跑并写入 `sensitivity`（每个扫描点也立键，或在 schema 里声明父级键）
- [ ] 得分点逐条核账无 missing/unbacked
- [ ] `reports/SCORE_MAP.md` 已建表：每条得分点有「证据（结果键/图表名）→ 计划落点（哪一节）」；落点列留空给 S4 填
- [ ] `reports/RESULTS_REPORT.md` 已写
- [ ] `reports/journal_problemN.md` 每问一份（关键数值/图表结论/结果表格/结论核对/遗留）
- [ ] 没有硬编码论文数值

通过后进入 S3。
