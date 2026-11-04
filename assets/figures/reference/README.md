# 精选参考图

本目录只保留 **13 张参考版式**（5 张主图母版 + 8 张流程图版式），不包含 1381 张全量图库。

## roadmap/（5 张母版）

论文主图版式母版，取自真实获奖论文／优秀答卷的 Figure，**只作版式参考，不进论文**：

| id | 版式 | 一句话结构 |
|---|---|---|
| `grouped-tasks` | 任务分组横排 | 输入 → 3–4 个任务组 → 目标 |
| `nested-cluster` | 总分嵌套 | 上位主题框住若干并列任务 |
| `quad-matrix` | 2×2 任务矩阵 | 四个并列任务 + 方法椭圆 + 竖排指标条 |
| `multi-panel` | 多面板拼合 | 五块面板各讲一件事，密度最高 |
| `staged-steps` | 分步串联 | 步骤 1–5 串联成回路 |

- `src/*.jpg`：母版唯一副本（原始分辨率，5 张合计 1.4 MB）
- `index.json`：id、标题、pattern、骨架、适用、别用它
- `README.md`：**选版式表 + 每张骨架 + 视觉规范（唯一来源）**，复刻前先读这一份

不再存 2400 px PNG 与 PDF 派生件（同一张图的位图壳，白占 4 MB）；要预览直接开 jpg，要进论文按结构重画 SVG。

再加一张母版：

```bash
python tools/paper-figure/scripts/import_plate.py --src refs/new.jpg --id three-band --title "三段并排" \
    --use "三问并列" --avoid "任务不足三段" --skeleton "A → B → C"
```

## flowchart/（8 张）

流程图版式：linear、decision、loop、pipeline、parallel、layered、algorithm、multi_question。

- `*.json`：TikZ 生成规格（`flowchart.py` 由它重建 `.tex`）
- `*.pdf` / `*.png`：成品/预览

## 版权与用途

- roadmap 母版为入库样张，仅作版式参考；最终论文替换为本论文术语与数据。
- 只用这 5 张，不引入其他图库或其他论文配图。
- 完整 1381 图库已移出主包，放在 `_archive/paper-figure-gallery-1381/`，不随技能分发。
