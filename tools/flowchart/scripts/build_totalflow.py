# -*- coding: utf-8 -*-
"""总流程图母版（SVG）生成器：五套版式，对应 assets/figures/reference/totalflow/src/ 的 5 张实拍图。

用法：
    python tools/flowchart/scripts/build_totalflow.py            # 重写 5 个 .svg
    python tools/flowchart/scripts/build_totalflow.py --png       # 顺便调 svg_flow.py 出 PNG

产物：tools/flowchart/assets/totalflow/tf_*.svg
风格：① 虚线分组框 + 任务标签页；② 淡色填充（蓝/绿/黄/粉/紫）；③ 正交折线箭头；
      ④ 文字纯黑，颜色只给框与箭头；⑤ 全图 ≤6 色系，灰度可辨。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "totalflow"

# ---------- 配色（对应实拍图的淡色系） ----------
INK = "#1f1f1f"
GROUP_BLUE = "#4472c4"      # 分组虚线
GROUP_GRAY = "#808080"
TAB = "#2f5597"             # 任务标签页
BOX_STROKE = "#7f7f7f"
BLUE = "#bdd7ee"
BLUE_D = "#8faadc"
GREEN = "#a9d18e"
GREEN_L = "#c6e0b4"
YELLOW = "#ffe699"
ORANGE = "#f4b183"
RED = "#e06666"
PURPLE = "#d9d2e9"
PINK = "#fbe5d6"
GRAY_L = "#e7e6e6"


class Svg:
    """极简 SVG 生成器：只做总流程图需要的框、虚线组、文字、正交箭头、3D 轴。"""

    def __init__(self, width: int = 1440, height: int = 800) -> None:
        self.w, self.h = width, height
        self.parts: list[str] = []
        self.parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            'font-family="Microsoft YaHei, SimHei, Source Han Sans SC, sans-serif">'
        )
        self.parts.append(
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" '
            'markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
            f'fill="{INK}"/></marker>'
            '<marker id="ahh" viewBox="0 0 12 12" refX="7" refY="6" markerWidth="7" '
            'markerHeight="7" orient="auto"><path d="M2,1 L9,6 L2,11 z" fill="#ffffff" '
            'stroke="#7f7f7f" stroke-width="1.4"/></marker></defs>'
        )
        self.parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')

    # ---------- 基础图元 ----------
    def text(self, x, y, s, fs=15, anchor="middle", bold=False, color=INK, family=None):
        weight = ' font-weight="bold"' if bold else ""
        fam = f' font-family="{family}"' if family else ""
        lines = str(s).split("\n")
        for i, line in enumerate(lines):
            dy = i * (fs + 3)
            self.parts.append(
                f'<text x="{x}" y="{y + dy}" font-size="{fs}" text-anchor="{anchor}" '
                f'fill="{color}"{weight}{fam}>{_esc(line)}</text>'
            )

    def rect(self, x, y, w, h, fill="none", stroke=BOX_STROKE, sw=1.4, rx=4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def box(self, x, y, w, h, text="", fill=BLUE, stroke=BOX_STROKE, fs=15, rx=4,
            bold=False, tcolor=INK, sw=1.4, dash=None):
        self.rect(x, y, w, h, fill, stroke, sw, rx, dash)
        if text:
            n = len(str(text).split("\n"))
            self.text(x + w / 2, y + h / 2 + fs * 0.35 - (n - 1) * (fs + 3) / 2, text, fs, bold=bold,
                      color=tcolor)

    def group(self, x, y, w, h, label="", tab_fill=TAB, dash="7 5", color=GROUP_BLUE, rx=10):
        self.rect(x, y, w, h, "none", color, 1.6, rx, dash)
        if label:
            tw = max(96, 30 + len(label) * 15)
            self.rect(x + 22, y - 17, tw, 34, tab_fill, tab_fill, 1.0, 3)
            self.text(x + 22 + tw / 2, y + 5, label, 15, bold=True, color="#ffffff")

    def arrow(self, pts, label=None, label_at=None, lw=1.7, both=False, dashed=False):
        d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        start = ' marker-start="url(#ah)"' if both else ""
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{lw}"{dash} '
            f'marker-end="url(#ah)"{start}/>'
        )
        if label:
            lx, ly = label_at if label_at else ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
            self.text(lx, ly, label, 13, color=INK)

    def hollow_arrow(self, x, y, w=34, h=44, direction="down"):
        if direction == "down":
            pts = f"{x - w/2},{y} {x + w/2},{y} {x + w/2},{y + h*0.55} {x + w},{y + h*0.55} {x},{y + h} {x - w},{y + h*0.55} {x - w/2},{y + h*0.55}"
        elif direction == "left":
            pts = f"{x},{y - h/2} {x},{y + h/2} {x - w*0.55},{y + h/2} {x - w*0.55},{y + h} {x - w},{y} {x - w*0.55},{y - h} {x - w*0.55},{y - h/2}"
        else:  # right
            pts = f"{x},{y - h/2} {x},{y + h/2} {x + w*0.55},{y + h/2} {x + w*0.55},{y + h} {x + w},{y} {x + w*0.55},{y - h} {x + w*0.55},{y - h/2}"
        self.parts.append(f'<polygon points="{pts}" fill="#ffffff" stroke="{BOX_STROKE}" stroke-width="1.6"/>')

    def axis3d(self, x, y, size=150):
        o = (x, y)
        self.parts.append(
            f'<path d="M{o[0]},{o[1]} L{o[0] - 60},{o[1] + 45}" stroke="#2e75b6" stroke-width="2"/>'
            f'<path d="M{o[0]},{o[1]} L{o[0] + size},{o[1]}" stroke="#548235" stroke-width="2"/>'
            f'<path d="M{o[0]},{o[1]} L{o[0]},{o[1] - size * 0.8}" stroke="#bf8f00" stroke-width="2"/>'
        )
        self.text(o[0] - 72, o[1] + 56, "x", 15, color="#2e75b6")
        self.text(o[0] + size + 12, o[1] + 5, "y", 15, color="#548235")
        self.text(o[0] - 12, o[1] - size * 0.8 - 8, "z", 15, color="#bf8f00")

    def render(self, path: Path) -> None:
        self.parts.append("</svg>")
        path.write_text("\n".join(self.parts), encoding="utf-8")


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ══════════════════════════════════════════════════════════════════════
# 版式 1：四象限任务分组（任务标签页 + 四社区应用）
# ══════════════════════════════════════════════════════════════════════
def layout_quadrant_tasks() -> Svg:
    s = Svg(1440, 800)

    # 任务 1
    s.group(165, 40, 640, 380, "任务 1")
    s.rect(200, 78, 232, 306, "none", "#9e9e9e", 1.2, 18, "3 4")
    s.text(316, 108, "高级指标", 16)
    for i, name in enumerate(["社会", "生态", "交通", "能源"]):
        s.box(214, 126 + i * 62, 204, 46, name, YELLOW, "#bf9000", 15, 3)
    s.box(452, 150, 132, 228, "指标识别", GREEN, "#548235", 16, 14)
    s.arrow([(604, 250), (648, 250)])
    s.text(626, 238, "EWM", 12, anchor="middle")
    s.box(654, 120, 128, 268, "光污染风险\n等级评估的\n多层因子\n指标体系", GREEN, "#548235", 15, 14)

    # 任务 2
    s.group(810, 40, 500, 380, "任务 2")
    s.text(960, 224, "K-Means", 14)
    s.rect(905, 208, 110, 32, GRAY_L, "#7f7f7f", 1.2, 16)
    s.text(960, 229, "K-Means", 13)
    for i, name in enumerate(["在保护区位置\n的应用", "在农村社区\n的应用", "在城市社区\n的应用", "在郊区社区\n的应用"]):
        y = 78 + i * 84
        s.box(1050, y, 232, 62, name, PINK, "#c55a11", 14, 3)
        s.arrow([(1015, 224), (1048, y + 31)] if i == 0 else [(1015, 224), (1032, 224), (1032, y + 31), (1048, y + 31)])

    # 任务 3
    s.group(690, 492, 556, 288, "任务 3")
    s.box(712, 556, 128, 168, "影响水平\n预测", GREEN, "#548235", 15, 12)
    s.box(872, 556, 118, 168, "三种策略", GREEN, "#548235", 15, 12)
    s.box(1012, 520, 216, 62, "四个地点的\n平均情况", BLUE_D, "#2e75b6", 14, 3)
    s.box(1012, 662, 216, 62, "四个位置的\n理想愿景", BLUE_D, "#2e75b6", 14, 3)
    s.arrow([(990, 570), (1010, 570)])
    s.arrow([(1120, 584), (1120, 600), (1120, 660)])
    s.arrow([(1010, 693), (930, 693), (930, 640)])

    # 任务 4
    s.group(160, 492, 470, 288, "任务 4")
    s.box(196, 556, 118, 168, "效果分析", GREEN, "#548235", 15, 12)
    s.box(392, 520, 200, 62, "郊区社区", BLUE, "#2e75b6", 15, 3)
    s.box(392, 662, 200, 62, "城市社区", BLUE, "#2e75b6", 15, 3)
    s.text(300, 536, "能源\n策略", 13)
    s.text(300, 678, "城市规\n划策略", 13)
    s.arrow([(390, 551), (318, 551)])
    s.arrow([(390, 693), (318, 693)])

    # 跨任务箭头
    s.hollow_arrow(1180, 428, 34, 52, "down")
    s.hollow_arrow(660, 636, 34, 44, "left")
    return s


# ══════════════════════════════════════════════════════════════════════
# 版式 2：多面板（模型链 + 特征分析 + 难点分类）
# ══════════════════════════════════════════════════════════════════════
def layout_multi_panel() -> Svg:
    s = Svg(1440, 800)

    # 左：GPU 预测模型（竖链）
    s.group(22, 40, 340, 730, "GPU 预测模型", dash="6 4", color="#548235")
    s.box(120, 96, 140, 44, "输入", "#ffd966", "#bf9000", 15, 3)
    s.box(96, 186, 188, 150, "GPU 模型", GREEN, "#548235", 18, 10)
    s.arrow([(190, 142), (190, 184)])
    s.arrow([(190, 338), (190, 396)])
    s.box(120, 398, 140, 44, "输出", "#ffd966", "#bf9000", 15, 3)
    s.box(120, 486, 140, 44, "预测", "#ffd966", "#bf9000", 15, 3)
    s.arrow([(190, 444), (190, 484)])
    s.box(96, 574, 188, 48, "2023年3月1日", ORANGE, "#c55a11", 14, 3)
    s.arrow([(190, 532), (190, 572)])
    # 循环门
    s.parts.append('<path d="M96,232 C60,232 60,290 96,290" fill="none" stroke="#1f1f1f" stroke-width="1.5" marker-end="url(#ah)"/>')
    s.parts.append('<path d="M284,232 C320,232 320,290 284,290" fill="none" stroke="#1f1f1f" stroke-width="1.5" marker-end="url(#ah)"/>')
    s.text(52, 216, "去噪门", 12, anchor="start")
    s.text(318, 216, "更新门", 12, anchor="end")

    # 中上：词属性与百分比得分
    s.group(388, 40, 700, 300, "词属性与百分比得分的关系", dash="6 4", color="#c00000")
    s.text(738, 78, "score = w₁·Σ f_word + w₂·f_letter", 14, family="Cambria Math, serif")
    s.text(520, 116, "回归分析单词频率", 14, bold=True)
    s.text(948, 116, "箱线图分析", 14, bold=True)
    s.box(452, 142, 62, 40, "f_word", PINK, "#c55e3a", 13, 2)
    s.box(534, 142, 62, 40, "f_letter", PINK, "#c55e3a", 13, 2)
    s.text(483, 132, "词频", 12)
    s.text(565, 132, "字母频率", 12)
    s.box(880, 142, 62, 40, "代表", PINK, "#c55e3a", 13, 2)
    s.box(958, 142, 62, 40, "词性", PINK, "#c55e3a", 13, 2)
    s.text(911, 132, "字母重复", 12)
    s.box(430, 206, 236, 40, "回归分析", PINK, "#c55e3a", 14, 2)
    s.box(866, 206, 180, 40, "箱长差异", PINK, "#c55e3a", 13, 2)
    s.arrow([(483, 182), (483, 204)])
    s.arrow([(565, 182), (565, 204)])
    s.arrow([(911, 182), (911, 204)])
    s.arrow([(548, 246), (548, 372)])
    s.arrow([(956, 246), (956, 372)])

    # 中下：预测流程
    s.group(388, 352, 700, 240, "", dash="6 4", color="#2e75b6")
    s.box(430, 376, 610, 38, "输入", BLUE, "#2e75b6", 15, 2)
    s.box(430, 434, 190, 66, "网格搜索\n最佳参数", BLUE, "#2e75b6", 14, 2)
    s.box(430, 522, 190, 52, "随机森林", "#2e75b6", "#1f3864", 15, 2, tcolor="#ffffff")
    s.box(660, 434, 176, 66, "2023年3月1日\n可怕的", "#ed7d31", "#c55a11", 13, 2)
    s.box(866, 434, 160, 66, "预测", BLUE, "#2e75b6", 14, 2)
    s.box(866, 522, 160, 52, "输出", BLUE, "#2e75b6", 14, 2)
    s.arrow([(700, 414), (700, 432)])
    s.arrow([(525, 414), (525, 432)])
    s.arrow([(525, 500), (525, 520)])
    s.arrow([(620, 470), (658, 470)])
    s.arrow([(836, 470), (864, 470)])
    s.arrow([(946, 500), (946, 520)])

    # 右上：数据的有趣特征
    s.group(1112, 40, 306, 300, "数据的有趣特征", dash="6 4", color="#7030a0")
    s.box(1128, 126, 90, 42, "词属性", PURPLE, "#7030a0", 13, 2)
    s.box(1244, 96, 156, 34, "非线性相关", "#7030a0", "#3f1f5c", 12, 2, tcolor="#ffffff")
    s.box(1244, 150, 156, 34, "无明显差异", "#7030a0", "#3f1f5c", 12, 2, tcolor="#ffffff")
    s.box(1244, 206, 156, 44, "困难模式\n百分比", PURPLE, "#7030a0", 12, 2)
    s.arrow([(1220, 140), (1242, 116)])
    s.arrow([(1220, 154), (1242, 166)])
    s.arrow([(1322, 188), (1322, 204)])
    s.box(1124, 276, 148, 36, '最"地狱"级别:PAPER', PURPLE, "#7030a0", 11, 2)
    s.box(1288, 276, 116, 36, "难以猜测", "#7030a0", "#3f1f5c", 12, 2, tcolor="#ffffff")
    s.arrow([(1274, 294), (1286, 294)])

    # 右下：K-Means++ 难度路径分类
    s.group(1112, 360, 306, 410, "难度路径分类", dash="6 4", color="#548235")
    s.text(1265, 400, "基于 K-Means++ 的难度路径分类模型", 11, color="#404040")
    s.text(1265, 420, "δ = w₁·Σ f_word + w₂·f_letter", 11, family="Cambria Math, serif")
    s.box(1136, 438, 96, 52, "难度率", GREEN_L, "#548235", 13, 2)
    s.box(1136, 560, 96, 56, "K-Means\n聚类分析", GREEN_L, "#548235", 12, 2)
    s.box(1252, 560, 96, 56, "难度分类", GREEN_L, "#548235", 13, 2)
    s.box(1292, 438, 96, 44, "怪异的", GREEN_L, "#548235", 12, 2)
    s.arrow([(1184, 492), (1184, 558)])
    s.arrow([(1234, 588), (1250, 588)])
    s.arrow([(1348, 558), (1344, 486)])
    for i in range(4):
        s.rect(1252 + i * 5, 452 + i * 7, 38, 30, GREEN, "#548235", 1.0, 1)
    return s


# ══════════════════════════════════════════════════════════════════════
# 版式 3：嵌套大框（可持续性 / 气候缓解 两层包裹）
# ══════════════════════════════════════════════════════════════════════
def layout_nested_sustainability() -> Svg:
    s = Svg(1440, 800)
    s.rect(40, 40, 1360, 720, "none", "#b4c6e7", 2.0, 90)
    s.rect(120, 66, 1200, 668, "none", "#b4c6e7", 1.6, 80, "8 6")
    s.text(720, 88, "可持续性", 17, bold=True)
    s.text(720, 712, "气候缓解", 17, bold=True)

    # 任务 1
    s.group(160, 150, 560, 270, "任务 1", dash="6 4", color="#4472c4")
    s.box(196, 236, 132, 42, "GGDP", "#ffd966", "#bf9000", 15, 3)
    s.box(392, 166, 236, 42, "二氧化碳排放", GREEN_L, "#548235", 15, 3)
    s.box(392, 236, 236, 42, "自然资源消耗", BLUE, "#2e75b6", 15, 3)
    s.box(392, 306, 236, 42, "废物利用成本", PINK, "#c55a11", 15, 3)
    s.arrow([(430, 256), (392, 256)], lw=1.4)
    s.text(360, 252, "关联", 11)

    # 任务 4 + 任务 5
    s.group(748, 150, 540, 270, "任务 4", dash="6 4", color="#4472c4")
    s.box(780, 176, 132, 60, "产业结构", "#fbe5d6", "#c55a11", 14, 3)
    s.box(780, 292, 132, 60, "废物处理", GREEN_L, "#548235", 14, 3)
    s.box(944, 236, 110, 60, "澳大利亚", BLUE, "#2e75b6", 15, 3)
    s.arrow([(912, 206), (942, 250)])
    s.arrow([(912, 322), (942, 282)])
    s.box(1094, 172, 150, 44, "政策", "#ffe699", "#bf9000", 13, 3)
    s.box(1094, 300, 150, 44, "报告", "#d9d2e9", "#7030a0", 13, 3)
    s.arrow([(1054, 250), (1088, 200)])
    s.arrow([(1088, 296), (1054, 276)])
    s.text(1210, 286, "任务 5", 14, bold=True)

    # 任务 2
    s.group(190, 470, 360, 230, "任务 2", dash="6 4", color="#4472c4")
    s.box(212, 566, 96, 36, "气候", GREEN_L, "#548235", 13, 3)
    s.box(360, 484, 170, 40, "气温", BLUE, "#2e75b6", 13, 3)
    s.box(360, 552, 170, 46, "环境污染程度", "#f4b183", "#c55a11", 13, 3)
    s.box(360, 630, 170, 40, "生态系统稳定性", "#ffe699", "#bf9000", 13, 3)
    s.arrow([(310, 584), (330, 584), (330, 504), (358, 504)])
    s.arrow([(310, 584), (358, 575)])
    s.arrow([(310, 584), (330, 584), (330, 650), (358, 650)])

    # 任务 3
    s.group(600, 470, 690, 230, "任务 3", dash="6 4", color="#4472c4")
    s.box(620, 544, 128, 66, "趋势预测", "#dbe5f1", "#2e75b6", 14, 3)
    s.box(806, 544, 152, 66, "优势与劣势", "#f8cbad", "#c55a11", 14, 3)
    s.box(1006, 544, 140, 66, "博弈论", GREEN_L, "#548235", 14, 3)
    s.arrow([(750, 577), (804, 577)], label="时间", label_at=(777, 566))
    s.arrow([(958, 577), (1004, 577)], label="空间", label_at=(981, 566))
    s.text(690, 640, "时间剖面", 11, color="#595959")
    s.text(1120, 640, "空间博弈", 11, color="#595959")
    return s


# ══════════════════════════════════════════════════════════════════════
# 版式 4：左入右出三组流水线
# ══════════════════════════════════════════════════════════════════════
def layout_pipeline_groups() -> Svg:
    s = Svg(1440, 800)
    s.box(30, 166, 96, 66, "给定\n数据", BLUE, "#2e75b6", 14, 6)
    s.box(30, 400, 96, 66, "哈士奇\n团队", BLUE, "#2e75b6", 14, 6)
    s.arrow([(78, 234), (78, 398)])
    s.arrow([(126, 432), (176, 432)])

    # 任务 1
    s.group(170, 150, 430, 440, "任务 1 网络分析", dash="6 4", color="#7f7f7f")
    s.box(250, 200, 270, 44, "通过质量网络", "#ffffff", "#404040", 14, 2)
    s.rect(252, 264, 136, 116, "none", "#2e75b6", 1.4, 4, "6 4")
    s.box(264, 276, 112, 40, "二元配置", "#ffffff", "#404040", 13, 2)
    s.text(320, 334, "＋", 18, bold=True)
    s.box(264, 344, 112, 40, "三元配置", "#ffffff", "#404040", 13, 2)
    s.box(400, 286, 110, 66, "团队组建", "#ffffff", "#404040", 13, 2)
    s.box(250, 412, 270, 44, "时间和空间", "#ffffff", "#404040", 14, 2)
    s.arrow([(385, 244), (385, 286)])
    s.arrow([(320, 244), (320, 274)])
    s.arrow([(320, 386), (320, 410)])
    s.arrow([(455, 352), (455, 410)], dashed=True)
    s.box(280, 500, 200, 36, "fullevents.csv", BLUE, "#2e75b6", 13, 3)
    s.arrow([(380, 456), (380, 498)])

    # 任务 2
    s.group(618, 150, 330, 440, "任务 2 确定绩效合作指标", dash="6 4", color="#7f7f7f")
    s.box(648, 200, 270, 44, "指标确定", "#ffffff", "#404040", 14, 2)
    s.box(648, 292, 270, 44, "绩效指标量化", "#ffffff", "#404040", 14, 2)
    s.rect(668, 372, 230, 62, "none", "#2e75b6", 1.4, 4, "6 4")
    s.box(686, 386, 88, 34, "双基点法", BLUE, "#2e75b6", 12, 2)
    s.text(800, 406, "＋", 16, bold=True)
    s.box(820, 386, 100, 34, "层次分析法", BLUE, "#2e75b6", 12, 2)
    s.box(648, 470, 270, 50, "团队合作的三维动态模型", "#ffffff", "#404040", 13, 2)
    s.arrow([(783, 244), (783, 290)])
    s.arrow([(783, 336), (783, 370)])
    s.arrow([(783, 434), (783, 468)])

    # 任务 3 + 任务 4
    s.group(962, 150, 330, 240, "任务 3 T团队组建与培训方法", dash="6 4", color="#7f7f7f")
    s.box(986, 196, 130, 46, "团队形成\n利用度", "#ffffff", "#404040", 12, 2)
    s.box(1140, 196, 130, 46, "寻找有效\n队形", "#ffffff", "#404040", 12, 2)
    s.box(1010, 280, 230, 46, "五个成功衡量指标", "#ffffff", "#404040", 13, 2)
    s.arrow([(1051, 242), (1051, 278)])
    s.arrow([(1205, 242), (1205, 278)])
    s.group(962, 424, 330, 166, "任务 4 良好社会团队的指标", dash="6 4", color="#7f7f7f")
    s.box(1000, 486, 120, 44, "获得的指标", "#ffffff", "#404040", 13, 2)
    s.box(1150, 486, 120, 44, "附加指标", "#ffffff", "#404040", 13, 2)
    s.arrow([(1120, 508), (1148, 508)], both=True)
    s.arrow([(1240, 326), (1240, 466)], dashed=True)

    # 跨组箭头与出口
    s.arrow([(600, 372), (616, 372)])
    s.arrow([(948, 372), (960, 372)])
    s.box(1316, 300, 96, 106, "目标\n与\n行动", BLUE_D, "#2e75b6", 15, 6)
    s.arrow([(1292, 340), (1314, 340)])
    return s


# ══════════════════════════════════════════════════════════════════════
# 版式 5：五步骤（上排 1/2 + 下排 3/4/5）
# ══════════════════════════════════════════════════════════════════════
def layout_five_steps() -> Svg:
    s = Svg(1440, 800)
    # 步骤 1
    s.rect(24, 36, 880, 322, "#ffffff", "#7f7f7f", 1.6, 4, "6 4")
    s.text(42, 66, "步骤1:评估", 16, anchor="start", bold=True)
    s.text(42, 90, "(DAS 成熟度评估模型)", 12, anchor="start", color="#595959")
    inputs = [("IR,WE,WQ", 122), ("SA,CA,Rob,\nDPC", 202), ("MC,DS,DQ,D\nPE,DACSR", 282)]
    for text, y in inputs:
        s.box(96, y, 176, 56, text, "#fbd5d5", "#c55a11", 12, 2)
    for i, (label, y) in enumerate([("人员", 130), ("技术", 210), ("过程", 290)]):
        s.parts.append(f'<ellipse cx="382" cy="{y}" rx="52" ry="30" fill="#9dc3e6" stroke="#2e75b6" stroke-width="1.4"/>')
        s.text(382, y + 5, label, 14)
        s.arrow([(274, y + 6), (328, y)])
    s.box(486, 172, 116, 56, "FESM", "#f4e1d2", "#c55a11", 13, 2)
    s.box(486, 258, 116, 56, "EWM-AHP", "#f4e1d2", "#c55a11", 13, 2)
    s.arrow([(432, 150), (470, 150), (470, 196), (484, 196)])
    s.arrow([(432, 290), (470, 290), (470, 280), (484, 280)])
    s.box(632, 194, 240, 60, "成熟度水平", "#ffffff", "#404040", 15, 2)
    s.arrow([(604, 200), (630, 210)])
    s.arrow([(604, 286), (630, 244)])

    # 步骤 2
    s.rect(944, 36, 472, 640, "none", "#7f7f7f", 1.6, 4, "6 4")
    s.text(962, 66, "步骤2:优化", 16, anchor="start", bold=True)
    s.text(962, 90, "(VOM 模型)", 12, anchor="start", color="#595959")
    for i, label in enumerate(["x:人员表现", "y:技术性能", "z:过程性能"]):
        s.box(972, 116 + i * 62, 416, 46, label, "#9dc3e6", "#2e75b6", 14, 23)
    s.rect(972, 306, 416, 236, "#dbe5f1", "#8faadc", 1.2, 4)
    s.axis3d(1080, 480, 150)
    s.arrow([(1180, 546), (1180, 590)])
    s.box(1004, 592, 330, 50, "优化提案", "#f8cbda", "#c55a11", 14, 2)

    # 步骤 3 / 4 / 5（下排，右到左串联）
    s.rect(660, 396, 262, 280, "none", "#7f7f7f", 1.6, 4, "6 4")
    s.text(678, 426, "步骤3:协议", 15, anchor="start", bold=True)
    s.box(690, 450, 204, 60, "模型使用\n文本指令", "#ffffff", "#404040", 13, 2)
    s.box(690, 540, 204, 60, "通过流程图\n进行可视化", "#ffffff", "#404040", 13, 2)
    s.arrow([(792, 512), (792, 538)])

    s.rect(396, 396, 246, 280, "none", "#7f7f7f", 1.6, 4, "6 4")
    s.text(414, 426, "步骤4:模型扩展", 15, anchor="start", bold=True)
    s.box(420, 450, 198, 56, "规模-需求方法", "#fbe5d6", "#c55a11", 13, 2)
    s.box(420, 540, 92, 56, "分析\n不同规模", "#fbe5d6", "#c55a11", 12, 2)
    s.box(526, 540, 92, 56, "分析\n不同行业", "#fbe5d6", "#c55a11", 12, 2)
    s.arrow([(519, 508), (466, 538)])
    s.arrow([(519, 508), (572, 538)])

    s.rect(24, 396, 350, 280, "none", "#7f7f7f", 1.6, 4, "6 4")
    s.text(42, 426, "步骤5:一页信函", 15, anchor="start", bold=True)
    s.box(44, 470, 130, 90, "致Post用户\n的一封信", "#fbe5d6", "#c55a11", 12, 2)
    s.box(196, 450, 150, 54, "评估模型\n指令", "#ffe699", "#bf9000", 12, 2)
    s.box(196, 530, 150, 54, "建立信心", "#ffe699", "#bf9000", 12, 2)
    s.arrow([(194, 500), (176, 500)])
    s.arrow([(194, 552), (176, 540)])

    # 步骤链路：1→2，2→3→4→5
    s.hollow_arrow(908, 196, 30, 34, "right")
    s.hollow_arrow(940, 536, 26, 30, "left")
    s.hollow_arrow(636, 536, 26, 30, "left")
    return s


LAYOUTS = {
    "tf_01_quadrant_tasks": layout_quadrant_tasks,
    "tf_02_multi_panel": layout_multi_panel,
    "tf_03_nested_sustainability": layout_nested_sustainability,
    "tf_04_pipeline_groups": layout_pipeline_groups,
    "tf_05_five_steps": layout_five_steps,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="生成总流程图 SVG 母版")
    ap.add_argument("--png", action="store_true", help="顺便调用 svg_flow.py 出 PNG")
    ap.add_argument("--scale", type=float, default=2.0, help="PNG 倍率")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, fn in LAYOUTS.items():
        path = OUT / f"{name}.svg"
        fn().render(path)
        made.append(path)
        print("SVG:", path)

    if args.png:
        script = Path(__file__).resolve().parent / "svg_flow.py"
        for path in made:
            r = subprocess.run([sys.executable, str(script), str(path), "--png", "-s", str(args.scale)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            print(r.stdout.strip() or r.stderr.strip()[-300:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
