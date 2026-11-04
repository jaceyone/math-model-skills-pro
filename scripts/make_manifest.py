#!/usr/bin/env python3
"""扫描 figures/ 生成或更新 figures/manifest.json。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROUTE_BY_PREFIX = {
    "data_": "data",
    "mech_": "mech",
    "paper_": "paper",
    "flow_": "flow",
}
SUFFIX_ORDER = (".pdf", ".png", ".svg", ".tex", ".html")
IGNORE_SUFFIX = {".aux", ".log", ".out", ".toc", ".json", ".md"}


def load_existing(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    figs = data.get("figures", []) if isinstance(data, dict) else data
    if isinstance(figs, dict):          # dict 形态：{stem: {...}}
        figs = list(figs.values())
    return {item.get("id"): item for item in figs
            if isinstance(item, dict) and item.get("id")}


COMMENT_RE = re.compile(r"(?<!\\)%.*$")
INCLUDE_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")


def _flatten(path: Path, seen: set | None = None) -> list[str]:
    """按 \\input/\\include 顺序把整篇论文摊平成行序列（跨文件累积章节上下文）。"""
    seen = seen if seen is not None else set()
    if path in seen or not path.is_file():
        return []
    seen.add(path)
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = COMMENT_RE.sub("", raw)
        incs = INCLUDE_RE.findall(line)
        if incs:
            for inc in incs:
                target = path.parent / (inc if inc.endswith(".tex") else inc + ".tex")
                out.extend(_flatten(target, seen))
            continue
        out.append(line)
    return out


def _braced(text: str, open_idx: int) -> str:
    """从 `{` 位置起按括号配对取内容：caption 里常有 \\ref{...}，按首个 } 截断会切坏。"""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i]
    return ""


def _caption_of(body: str) -> str:
    m = re.search(r"\\caption\s*\{", body)
    return _braced(body, m.end() - 1).strip() if m else ""


def captions_from_paper(root: Path) -> dict:
    """从 paper/ 抓 caption 与所在章节。

    按 `\\input` 顺序把全文摊平后再定位：workshop 模板的 `\\section` 在包装文件里、
    图在 `5.X.Y` 子文件里（还常用 `\\subsubsection`），只在本文件内向前找必然找不到。
    """
    paper = root / "paper"
    if not paper.is_dir():
        return {}
    main = paper / "main.tex"
    lines = _flatten(main) if main.is_file() else [
        ln for p in sorted(paper.rglob("*.tex")) for ln in p.read_text(
            encoding="utf-8-sig", errors="replace").splitlines()]
    text = "\n".join(lines)
    fig_re = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.S)
    head_re = re.compile(r"\\(?:sub)*section\*?\{([^}]*)\}")
    out: dict[str, dict] = {}
    for m in fig_re.finditer(text):
        body = m.group(1)
        inc = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
        cap_text = _caption_of(body)
        if not inc or not cap_text:
            continue
        heads = head_re.findall(text[:m.start()])
        stem = Path(inc.group(1)).stem
        cand = {"caption": cap_text, "section": heads[-1].strip() if heads else ""}
        # 同一张图出现两次（附录先出现时 section 为空）时，保留信息更全的那条
        old = out.get(stem)
        if old is None or (not old.get("section") and cand["section"]):
            out[stem] = cand
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="生成图件 manifest")
    parser.add_argument("--project", default=".", help="项目目录")
    parser.add_argument("--figures", help="figures 目录")
    parser.add_argument("--out", help="manifest 输出路径")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写入")
    parser.add_argument("--meta", help="caption/section 元信息 JSON：{stem: {caption, section}}（覆盖自动提取）")
    parser.add_argument("--no-paper", action="store_true", help="不从 paper/ 自动提取 caption/section")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    figures = Path(args.figures) if args.figures else root / "figures"
    out = Path(args.out) if args.out else figures / "manifest.json"
    if not figures.is_dir():
        print(f"figures 目录不存在：{figures}", file=sys.stderr)
        return 1

    # caption/section 先按 paper/ 里的 figure 环境自动提取，再用 --meta 覆盖
    meta = {} if args.no_paper else captions_from_paper(root)
    if args.meta:
        try:
            meta.update(json.loads(Path(args.meta).read_text(encoding="utf-8-sig")))
        except (OSError, ValueError) as exc:
            print(f"--meta 读不了：{exc}", file=sys.stderr)
            return 1

    existing = load_existing(out)
    stems: dict[str, list[Path]] = {}
    for path in figures.iterdir():
        if not path.is_file() or path.suffix.lower() in IGNORE_SUFFIX:
            continue
        prefix = next((p for p in ROUTE_BY_PREFIX if path.name.startswith(p)), None)
        if prefix is None:
            continue
        if path.suffix.lower() not in SUFFIX_ORDER:
            continue
        stem = path.stem
        stems.setdefault(stem, []).append(path)

    items = []
    for stem, paths in sorted(stems.items()):
        route = next(v for k, v in ROUTE_BY_PREFIX.items() if stem.startswith(k))
        old = existing.get(stem, {})
        outputs = []
        for suffix in SUFFIX_ORDER:
            hit = next((p for p in paths if p.suffix.lower() == suffix), None)
            if hit is not None:
                try:
                    outputs.append(str(hit.relative_to(root)).replace("\\", "/"))
                except ValueError:
                    outputs.append(str(hit).replace("\\", "/"))
        # 以论文里当前的 caption 为准（改了论文就重跑一次），旧值只作兜底
        caption = meta.get(stem, {}).get("caption") or old.get("caption", "")
        section = meta.get(stem, {}).get("section") or old.get("section", "")
        status = "ok"
        if not outputs:
            status = "missing"
        elif not caption or not section:
            status = "warn"
        item = {
            "id": stem,
            "route": route,
            "source": old.get("source", ""),
            "outputs": outputs,
            "caption": caption,
            "section": section,
            # 状态每次重算：旧 warn 会粘住，论文补好 caption 后重跑也降不下来
            "status": status,
        }
        if route == "flow":
            spec = old.get("spec", f"figures/{stem}.json")
            item["spec"] = spec
        else:
            data = old.get("data", "")
            if data:
                item["data"] = data
        items.append(item)

    payload = {"figures": items}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.dry_run:
        print(text)
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"已写入 {out}（{len(items)} 张图）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
