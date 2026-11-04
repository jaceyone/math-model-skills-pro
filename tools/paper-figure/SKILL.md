---
name: paper-figure
description: 数学建模论文主图。用于“技术路线图 / 方法框架图 / 总览图 / 分类图 / Figure 1”等任务。只从 5 张入库母版中选版式，复刻结构并换成本论文内容，生成可编辑 SVG，再导出 PDF/PNG。只做整体路线/框架，不画流程图、数据图、机理图，也不引入其他图库。
---

# 论文主图（SVG → PDF/PNG）

## 定位

论文主图回答“整条路线/框架一眼怎么讲清”。它和另外三路的分工：

| 图 | 工具 | 画什么 |
|---|---|---|
| 数据图 | matplotlib | 真实数据 |
| 机理图 | `mechanism-diagram` | 几何/公式/物理关系 |
| **论文主图** | **本工具** | **技术路线/框架/总览/分类** |
| 流程图 | `flowchart` | 步骤/判断/循环 |

**禁止**：用本工具画流程图；用 TikZ 画数据图；引入外部图库、别处论文配图或网络模板。

## 5 张母版（只用这 5 张）

`assets/figures/reference/roadmap/` 只有 5 张实拍母版（`src/*.jpg`，原始分辨率，5 张合计 1.4 MB）、`index.json` 与 `README.md`。**选版式只看它们，不新造版式。**

| id | 版式 | 适用 |
|---|---|---|
| `grouped-tasks` | 任务分组横排 | 输入 → 3–4 个任务组 → 目标，任务间有先后 |
| `nested-cluster` | 总分嵌套 | 一个上位主题包住若干并列任务 |
| `quad-matrix` | 2×2 任务矩阵 | 四个并列任务 + 方法标注 + 流程折返 |
| `multi-panel` | 多面板拼合 | 一张图同时交代流程、方法细节与结果结构 |
| `staged-steps` | 分步串联 | 分阶段方法链（评估 → 优化 → 协议 → 扩展 → 落地） |

**骨架排布、视觉规范（组框/角标/节点/箭头/配色/字号）、每张的「别用它」条件，全部在 `assets/figures/reference/roadmap/README.md`** —— 先读它，再开对应 jpg 核对一眼线型与间距。那 5 张图只作版式参考，不进论文。

```bash
python tools/paper-figure/scripts/select_reference.py --list
python tools/paper-figure/scripts/select_reference.py --id quad-matrix --json
python tools/paper-figure/scripts/select_reference.py --id quad-matrix --copy-to refs/quad-matrix.jpg
```

再加一张母版（只入一份 jpg，不生成 PNG/PDF 派生件）：

```bash
python tools/paper-figure/scripts/import_plate.py --src refs/new.jpg \
    --id three-band --title "三段并排" --pattern framework \
    --description "左中右三段各带小标题" --use "三问并列" --avoid "任务不足三段"
```

`render_figure.py` 认两个环境变量：`PF_SCALE`（PNG 倍率，默认 2）、`MSEDGE`（Edge 路径，留空自动探测）；模板见 `tools/paper-figure/.env.template`。

## 工作流

1. **定目标**：技术路线 / 框架 / 总览 / 分类。
2. **选母版**：读 `roadmap/README.md` 的选版式表，挑最接近的一张，对着它抄结构；不许混搭两张版式。
3. **写版式规格**：
   - layout：横排分组 / 总分嵌套 / 2×2 矩阵 / 多面板 / 分步串联；
   - elements：几块组框、每组几个框、箭头方向、竖排条与方法标注放哪；
   - palette：从母版取 3–5 个 HEX，亮色填节点、深蓝做角标；
   - hierarchy：组标题、节点、线上注释三级字号。
4. **生成 SVG**：按母版结构重排，文字换成本论文术语；节点太多就拆成两块。
5. **导出**：
   ```bash
   python tools/paper-figure/scripts/render_figure.py figures/paper_framework.svg
   ```
   默认输出 `.png` 与 `.pdf`；`--html` 才出预览页。
6. **自检**：文字不溢出、箭头闭合、色数 ≤3（最多 5）、术语一致、PDF/PNG 肉眼检查。
7. **登记** `figures/manifest.json`（route=`paper`）。

## 输出

- `figures/paper_*.svg`（可编辑源）
- `figures/paper_*.pdf`（进论文）
- `figures/paper_*.png`（预览）

## 验收

- [ ] 选对母版，结构服务论证，没有混搭两种版式
- [ ] 只参考那 5 张母版，没有引入外部图库或其他论文配图
- [ ] 文字不溢出、不被箭头穿过
- [ ] 色数 ≤3（最多 5），风格统一
- [ ] 术语与论文一致
- [ ] 有 caption，正文有 ≥100 字分析
- [ ] PDF 非空、页面正常
- [ ] manifest 已登记

## 边界

- 不画流程图（用 `flowchart`）。
- 不画数据图（用 matplotlib）。
- 不画几何/公式机理图（用 `mechanism-diagram`）。
- 不为了“好看”堆装饰；主图只讲一条主线。
- 母版只有这 5 张；真需要新版式，先问「现有 5 张里哪张最接近」，仍不够才 `import_plate.py` 入库并写明理由。
