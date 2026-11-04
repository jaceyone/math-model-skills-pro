# G4 论文门禁

按 `plan.md` 的交付形态，选择 LaTeX 或 Word 清单；两种模式都要通过。

## 通用（两种模式都要过）

- [ ] 每一章都对照该章 `.tex` 末尾【本章节写作提示词】自查过（可检索副本：`references/knowledge/10-chapter-writing-prompts.md`；总纲见 `main.tex` 顶部【全文写作总则】）
- [ ] 摘要最后写：写满一页、不溢出、无公式、逐问「针对问题N」段落、含 ≥3 个带单位定量结果
- [ ] 论文数值全部来自 `results.json`；摘要—正文—检验—评价四处同值同口径
- [ ] 实验预算（样本量/种子/重复次数/超参）全文只有一套
- [ ] 每个得分点在正文有可指认论述 + 一个支撑物（公式号/图号/表号）
- [ ] `reports/SCORE_MAP.md` 的落点列已填满，逐条与正文的公式号/图号/表号对得上
- [ ] `reports/BUILD_REPORT.md` 是终稿那一版：退出码 0（PASS）；1=FAIL（error/缺图/未定义引用）、2=WARN（Overfull/Underfull）都必须清零，清不掉的在报告里写明理由
- [ ] 跑过 `tools/review` 的话，`reports/REVIEW_REPORT.md` 的 P0/P1 已逐条回改或写明不采纳理由
- [ ] 图表题注具体（写清画的是哪些量、在对照什么），不用「结果图/示意图」这类空题注
- [ ] 表题在上、图题在下；表格里全是数，无整句与长说明列
- [ ] 模型假设 5–8 条、每条 ≤60 字，且每条在正文推导中被引用
- [ ] 无占位符（TODO / 待补充 / 示例数据）
- [ ] 正文无内部文件名（reports/code/results.json/manifest.json 等）
- [ ] 参考文献真实可查，角标与条目一一对应
- [ ] 全文段落成文，无要点列表式草稿；无过程旁白
- [ ] 过一遍 `main.tex`【全文语言规范与去 AI 味】10 条自查：无 AI 高频词、无否定平行/强行三连、破折号每页 ≤1 处、无空泛积极结论

## LaTeX 模式

- [ ] 模板已确认：本技能默认 `assets/templates/latex/workshop/`（未混入其他模板文件、未另写文档类）
- [ ] 已整目录复制到 `paper/`（含 `format.cls` 与 `fonts/`），只改章节 `.tex` 与 `main.tex` 的队伍信息
- [ ] 未在 `paper/main.tex` 临时加包或另写文档类
- [ ] 章节文件齐全，`\input` 顺序正确；多问题已复制 `5.2.*`、`5.3.*`
- [ ] 图用标准 `figure`+`\includegraphics[width=...]`（或该模板提供的 helper），宽度按宽高比档位
- [ ] 表用 longtable 定宽列，**首尾加 `@{}`** 后列宽总和 = 1.04 − 0.04×N（见【列宽记账】），带 `\caption` 与续页表头
- [ ] 图片路径 `../figures/xxx.png` 正确（相对 `paper/main.tex`）
- [ ] 无占位符、无 Overfull 满屏
- [ ] `xelatex` 两遍编译通过，0 error、0 缺失文件、0 未定义引用
- [ ] `paper/main.pdf` 非空，页数符合赛制档位（国赛 28–30、华为杯 50+、美赛 ≤25，见 `13-writing-injection.md`）；逐页目检无空白页/重叠/乱码
- [ ] `python scripts/check_paper.py --project 项目N` 退出码 0：数字能指回 `results.json`、`\cite` 与 `\bibitem` 一一对应、符号说明独立成章且在模型章之前、必产文件齐全且 SCORE_MAP 落点列填满、正文无内部文件名与占位符
- [ ] AI 使用声明（`9.AI说明.tex`）照 `plan.md` 的「AI 使用记录」填写，未留空、未凭记忆编
- [ ] Word 改稿副本（如需要）已生成差异报告

## Word 模式

- [ ] `report/数据分析报告.docx` 存在
- [ ] 封面、摘要/关键词、目录、正文章节齐全
- [ ] 目录、页码用域实现，`set_update_fields()` 已置；导出 PDF 前已更新域
- [ ] 图表已编号，正文引用与图表编号一致
- [ ] 图表有题注与分析（每图/表后 ≥100 字）
- [ ] 分页用 `page_break_before`，无空白页
- [ ] 小表不跨页断裂、大表每页重复表头
- [ ] 目录页码已更新，PDF 预览逐页检查无空白/重叠/乱码
- [ ] DOCX 与 PDF 页数一致

通过后完成。
