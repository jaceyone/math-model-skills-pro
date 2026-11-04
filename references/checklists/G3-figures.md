# G3 图件门禁

- [ ] 图件按四路分工，无跨路线重复
- [ ] 数据图只来自真实结果
- [ ] 数据图统一走 `plot_style.apply()`，横排组图（无 `subplots(3,1)` 竖堆）
- [ ] 数据图无雷达图/饼图/jet 彩虹/3D 柱饼
- [ ] `python check_figures.py` 退出码 0（压字/空面板/平线/双轴柱/图例压数据/乱码为 0）
- [ ] 数据图已 `read_image` 目检：轴标签带单位、图例不压数据、字够大
- [ ] 数据图张数符合档位（国赛每问 4–5，上限 6），角色后缀命名正确
- [ ] 机理图 xelatex 编译 0 error / 0 overfull
- [ ] 机理图 PNG 已肉眼检查
- [ ] 论文主图有 SVG + PDF + PNG
- [ ] 流程图路线已判：有判定/回边 → `tools/flowchart`；全文分工总览 → 模板 TikZ（`2.总体分析.tex`）；同一内容不画两张
- [ ] 流程图节点不重叠、分支有出口、循环有回边
- [ ] 每张图有 caption（写清画的是哪些量、在对照什么）
- [ ] 每张图有正文分析（≥100 字）
- [ ] `figures/manifest.json` 每张图都有记录，含宽高比与建议宽度
- [ ] manifest 的 `outputs` 全部存在
- [ ] 正文引用图都在 manifest 中
- [ ] `reports/FIGURE_REPORT.md` 已写
- [ ] 没有为凑数量生成无意义图

通过后进入 S4。
