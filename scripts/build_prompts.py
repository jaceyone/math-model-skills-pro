# -*- coding: utf-8 -*-
"""重建 `references/knowledge/10-chapter-writing-prompts.md`。

从 `assets/templates/latex/workshop/*.tex` 每个文件末尾的【本章节写作提示词】注释块
抽取成可检索的 Markdown 副本。改过模板里的提示词后跑一次即可同步。

用法（任意目录）：
    python <skill-root>/scripts/build_prompts.py
"""
from __future__ import annotations

import re
from pathlib import Path

SK = Path(__file__).resolve().parents[1]
TPL = SK / "assets" / "templates" / "latex" / "workshop"
OUT = SK / "references" / "knowledge" / "10-chapter-writing-prompts.md"

HEADER = """# 10 · 章节写作提示词（模板内置，逐章照做）

这些提示词是国赛评委口径的写作要求，随 `assets/templates/latex/workshop/` 每个章节文件
末尾的 `% 【本章节写作提示词】` 注释块一起发货；`main.tex` 顶部另有 `% 【全文写作总则】`。
**写哪一章就先读哪一节**，读完立刻落笔，不要通读全文浪费时间。

使用规则：

1. 章节顺序与文件名、`main.tex` 的 `\\input` 顺序一一对应；多问题复制 `5.1.*` 四件套为 `5.2.*`、`5.3.*`。
2. 提示词里给了版式与句式模板（如摘要「针对问题N，」句链、假设「**假设名**：口径」）→ 直接套用，不自由发挥。
3. 提示词里的「必须/禁止/不得」是硬约束，写完逐条自查；软要求（篇幅、语气）按实际内容取舍。
4. 数值一律来自 `results/results.json`，图一律来自 `figures/manifest.json`；提示词不改变这两条。
5. 本文件是 `*.tex` 末尾注释的可检索副本 —— **两者不一致时以模板 `.tex` 为准**。
6. **流程图分两路，别混**：§2「总体分析」的 TikZ 分工图（1 根 → N 问 → 每问等长步骤，无判定、无回边）保持原样，
   只换 `\\rows` 里的文字，不动坐标与连线；**有判定分支、循环回边的算法流程图一律走 `tools/flowchart`**。
   判据见 `references/knowledge/05-figures.md`「§2 的总体分析图」。

> 本文件由 `scripts/build_prompts.py` 生成，不要手改。

"""


def clean(line: str) -> str:
    return re.sub(r"^%\s?", "", line.rstrip()).rstrip()


def is_noise(s: str) -> bool:
    if not s.strip():
        return True
    return set(s.strip()) <= set("┈═-—")


def split_name(stem: str) -> tuple[str, str]:
    """'5.1.3.模型建立' -> ('5.1.3', '模型建立')；'0.摘要' -> ('0', '摘要')。"""
    m = re.match(r"^([0-9][0-9.]*)\.(.+)$", stem)
    if not m:
        return "", stem
    return m.group(1).rstrip("."), m.group(2)


def order_key(path: Path):
    nums = re.findall(r"\d+", path.stem)
    return tuple(int(n) for n in nums) if nums else (999,)


def drop_flowchart(body: list[str]) -> list[str]:
    """剔除流程图相关提示词条目（含其后的 ①②③ 续行），流程图统一交给 tools/flowchart。"""
    out: list[str] = []
    skipping = False
    for line in body:
        s = line.strip()
        if s.startswith("【流程图") or ("流程图" in s and s.startswith("【")):
            skipping = True
            continue
        if skipping:
            if s.startswith("【"):
                skipping = False
            elif not s or s[0] in "①②③④⑤⑥⑦⑧⑨⑩" or not s.startswith("【"):
                # 流程图条目的续行（缩进说明或编号子项）
                if s[:1] in "①②③④⑤⑥⑦⑧⑨⑩" or line.startswith(("  ", "\u3000")):
                    continue
                skipping = False
        if "流程图" in s:
            continue
        out.append(line)
    return out


def extract_omnibus(main_tex: Path) -> list[str]:
    """抽取 main.tex 顶部所有【…】注释块（总则 + 语言规范/去 AI 味），去掉分隔线与空行。"""
    if not main_tex.is_file():
        return []
    lines = main_tex.read_text(encoding="utf-8").splitlines()
    marks = [i for i, l in enumerate(lines) if "【全文写作总则】" in l]
    if not marks:
        return []
    body: list[str] = []
    for raw in lines[marks[-1]:]:
        stripped = raw.strip()
        if stripped and not stripped.startswith("%"):
            break  # 注释区结束（如 \PassOptionsToPackage）
        s = clean(raw).strip()
        if not s:
            continue
        if set(s) <= set("═┈-—"):
            continue
        body.append(clean(raw).rstrip())
    return body


def main() -> int:
    if not TPL.is_dir():
        print(f"找不到模板目录：{TPL}")
        return 1
    files = sorted((p for p in TPL.glob("*.tex") if p.name != "main.tex"), key=order_key)
    parts: list[str] = [HEADER]
    omnibus = extract_omnibus(TPL / "main.tex")
    if omnibus:
        parts.append("## 总纲 · 全文写作总则与语言规范\n\n源文件：`assets/templates/latex/workshop/main.tex`\n")
        parts.append("\n".join(omnibus).rstrip() + "\n")
    missing: list[str] = []
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        # 文件头会「预告」末尾有提示词，只有独立成行的标记才是块首；取最后一个。
        marks = [i for i, l in enumerate(lines) if clean(l).strip() == "【本章节写作提示词】"]
        if not marks:
            marks = [i for i, l in enumerate(lines) if "【本章节写作提示词】" in l]
        if not marks:
            missing.append(path.name)
            continue
        idx = marks[-1]
        num, title = split_name(path.stem)
        body = [clean(l) for l in lines[idx + 1:]]
        body = [l for l in body if not is_noise(l)]
        body = drop_flowchart(body)
        while body and not body[-1].strip():
            body.pop()
        head = f"## {num} · {title}" if num else f"## {title}"
        parts.append(f"{head}\n\n源文件：`assets/templates/latex/workshop/{path.name}`\n")
        parts.append("\n".join(body).rstrip() + "\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"写入 {OUT}（{OUT.stat().st_size} 字节，{len(files)} 个章节文件）")
    if missing:
        print("无提示词块：" + "; ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
