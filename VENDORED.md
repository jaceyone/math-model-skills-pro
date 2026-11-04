# 第三方资产与来源

本技能包含以下第三方资产。分发或商用前请再次确认上游许可证。

> **2026-11-04（2.3.18）**：`assets/templates/latex/workshop/`（自建模板）与 `assets/templates/latex/cumcmthesis/`（上游 CUMCMThesis 快照）已按用户要求**从技能包与仓库中移除**，默认论文模板改为 `assets/templates/latex/default/`。写作提示词不随模板走，落成独立口径库 `references/knowledge/10-chapter-writing-prompts.md`。

## MathModelAgent

- 来源：https://github.com/jihe520/MathModelAgent
- 快照：main（2026-11-01）
- 使用部分：
  - 阶段流程与产物契约（改写）
  - `math_modeling_norms.md`（拆分；2026-11-03 由 9 个拆分文件收敛为 7 个，见下条）
  - `mathmodel-figure-templates`（11 个数据图模板）
  - `doctor`、`6verity` 思路（改写）
  - MCM / 华为杯 / 通用 LaTeX 模板（复制并适配 `fontset`）
- 许可证：`docs/md/License.md`：
  - 个人免费使用；
  - 请勿商业用途；
  - 禁止闭源分发；
  - 不可在其基础上提供商业服务。
- 处理：保留署名；不商业化；分发前确认条款；必要时改为“引用 + 下载脚本”
- 2026-11-03：拆分文件 `06-writing.md`、`08-mcm-icm.md` 的独有条款（灵敏度扰动水平与 Tornado 图、赛制页数与 Summary Sheet 口径、常用组合表、美赛题号口径）并入 `02-model-selection.md`、`12-scoring-validation.md`、`13-writing-injection.md`、`14-figure-contract.md`；其余条款与 `10` / `13` 重复，删文件不删归属。

## BZD Math Modeling Skills（仅参考评审方法）

- 来源：https://github.com/BZDmathclub/bzd-math-modeling-skills
- 快照：main（2026-11-01）
- 使用方式：**只参考其评委式评审框架、评分维度、格式/摘要/AIGC 检查思路**，本地改写为 `tools/review/`（100 分结构、格式质量系数、AIGC 风险分级与 P0–P3 输出）；**未复制其 SKILL 文本、脚本、模型字典、评分资料或 2026 模板**。
- 落地变化（2026-11-03）：`references/knowledge/09-cumcm-rubric.md` 与本工具内容重复（100 分结构、格式系数、AIGC 信号、评审输出逐条对应 `tools/review/references/rubric.md`、`aigc.md`、`SKILL.md`），已删除；评审口径统一由 `tools/review/` 承担，得分点驱动逻辑在 `references/knowledge/12-scoring-validation.md`。
- 许可证：仓库未发现显式 LICENSE；其 `数模资料/` 含官方评阅细则与模板，版权归原权利人。本技能不分发这些资料。
- 处理：在文档中注明方法参考来源；不用于商业服务；不声称官方评分。

## 其他

- 优秀论文 PDF：来自公开竞赛论文，仅作结构与写法参考；不直接复制原文。
- 参考图母版：`assets/figures/reference/roadmap/` 为 5 张入库样张（只存一份原始分辨率 jpg 于 `src/`，不再出 PNG/PDF 派生件），只作版式参考，成品图按本论文内容重画；选版式表、骨架与视觉规范见该目录 `README.md`。
- 数据图模板预览：来自 MathModelAgent `mathmodel-figure-templates`，遵循其许可证。

## 修改记录

- 2026-11-01：创建 v2.1 结构；复制 CUMCMThesis、MathModelAgent 模板与图模板；移除 1381 图库；适配 Windows `fontset=windows`。
- 2026-11-03：知识库去重 —— 删除 `06-writing.md`、`08-mcm-icm.md`、`09-cumcm-rubric.md`，独有条款并入 `02`/`12`/`13`/`14`，`07-verification.md` 改号 `06-verification.md`。
- 2026-11-03：主图母版换高清原图并瘦身 —— 删掉 2400 px PNG 与 PDF 派生件（6.19 MB → 1.41 MB），骨架与视觉规范收敛到 `roadmap/README.md`，`select_reference.py` 去掉 `--pdf`。
