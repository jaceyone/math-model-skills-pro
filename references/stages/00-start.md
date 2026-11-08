# S0 启动（总控）

## 目标

把“要做哪道题、按什么规则交付”确定下来，生成项目骨架和状态文件。本阶段不建模、不写代码、不画图。

## 输入

- 题面（PDF / 文本 / 图片）
- 附件数据（xlsx / csv / 图片 / 压缩包）
- 用户偏好

## 只问会实质影响流程的问题

1. **赛事**：CUMCM / MCM / ICM / 华为杯 / 其他。
2. **语言**：中文 / 英文（MCM/ICM 默认英文）。
3. **子问题数量**：已知 N 个 / 待分析确定。
4. **交付形态**：LaTeX → PDF（默认）/ Word（赛题强制）/ 两者都要。
5. **模板**：默认 `assets/templates/latex/default/`；要官方格式再换 MCM / 华为杯，用户自带模板优先用用户的。Word 模式默认 `assets/templates/docx/reference.docx`。

排版引擎默认 **LaTeX**；如果赛题明确要求 Word 报告，直接走 Word 原生分支，不要先 LaTeX 再导出。

**无人值守时不要卡在这里**：题面能推出答案的自己定，推不出的按默认填（赛事=通用、语言=中文、子问题=待 S1 确定、交付=LaTeX + default 模板），把「这么定的理由 + 备选解释」写进 `plan.md` 的「假设」段，然后直接进 S1。执行纪律见 `references/knowledge/11-engineering-contract.md`。

## 执行步骤

1. 创建项目目录 `项目N/`（已有项目则递增编号）。
2. 建骨架：`input/`、`reports/tables/`（表格骨架目录）、`code/outputs/`、`results/tables/`、`results/logs/`、`figures/`；LaTeX 模式另建 `paper/sections/`，Word 模式另建 `report/`。
   - 顺手写一个空的 `results/schema.json` 壳（`{"version": 1, "keys": {}}`），S1 开工就是在里面立键；S1 不建这个文件，S2 会被 `check_contract.py` 挡在门口（退出码 2）。
3. **把工程资产复制进项目**（一次到位，后面不再折腾环境）：
   - `assets/style/plot_style.py` → 项目 `code/`（脚本要 `from plot_style import ...`）；
   - `assets/style/check_figures.py` → **只放项目根，不要复制到 `code/`**。闸门按「含 `figures/` 的工程根」找图：放 `code/` 那份会在 `code/figures/` 下找不到图，旧版还会打印「没有需要体检的结果图」并 **exit 0**——闸门形同虚设。项目里发现两份就删掉 `code/` 那份；
   - `assets/scaffold/run_all.py` → 项目根；
   - LaTeX 模式：`assets/templates/latex/default/` 整目录 → `paper/`（`main.tex` + `sections/` + `references.tex`）；
   - Word 模式：`assets/templates/docx/reference.docx` + `report_kit.py` → `report/`。
4. 保存题面与附件到 `input/`，不要修改原始文件。
5. 写 `plan.md`：赛事、语言、子问题数、交付形态、模板、交付物、阶段计划、假设、**AI 使用记录**、风险。
6. 写 `todo.md`：G0–G4 checklist。
7. 运行 `python <skill-root>/scripts/doctor.py`，把结果写入 `reports/ENV_REPORT.md`。**pandoc / pdftoppm 是可选项**（只影响 Word 旁路与 PNG 预览），主链路只要 xelatex + numpy/pandas；必选项缺失才停。
   铺模板时整目录一起复制，别只拷 `main.tex`；用自带字体的模板时字体目录必须与 `main.tex` 同级，漏复制会直接编译失败。
8. 若缺少 xelatex/pandoc/pdftoppm，给出安装建议，并记录降级方案。

## `plan.md` 模板

```markdown
# 方案

## 基本信息
- 赛事：
- 语言：
- 交付形态：LaTeX PDF / Word / 两者
- 模板：默认 default（`assets/templates/latex/default/`）
- 子问题数量：
- 交付：PDF 或 DOCX（按赛题）

## 阶段
- [ ] S0 启动
- [ ] S1 建模分析
- [ ] S2 代码实现
- [ ] S3 图件制作
- [ ] S4 论文撰写

## 假设（无人值守时按默认填，写清理由与备选）
- 赛事判定：
- 交付形态判定：
- 子问题判定：

## AI 使用记录（S4 的 AI 声明照抄这里，不许凭记忆补）
- 用了什么（工具/模型）：
- 做在哪一步（S0–S4）：
- 产出物与人工改动：

## 风险
- 数据缺失：
- 环境缺失：
- 时间风险：
```

## 必须产出

- `plan.md`
- `todo.md`
- `reports/ENV_REPORT.md`
- 项目骨架

## 边界

- 不选模型、不写公式、不写代码。
- 不生成论文。
- 不跳环境检查。

## 门禁

通过 `references/checklists/G0-start.md` 后进入 S1。
