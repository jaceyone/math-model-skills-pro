#!/usr/bin/env python3
r"""把表格骨架填成真表：reports/tables/*.tpl.md + results.json → results/tables/*.

设计意图（对应 SKILL.md 铁律 0）：**表格先写骨架，数值后填，论文只 \input 生成物**。
人只负责写列名、单位、行标签和 {{key}}；数值一格都不许手抄。这样 S4 写论文时不存在
"把 5.11 抄成 5.12" 的可能，重跑代码后表格也跟着变。

模板写法：

    <!-- table: q2_index | caption: 场景 2 指标对照 | label: tab:q2_index | format: auto -->
    | 情形 | 振动指标 $I_h$ | 降幅 |
    |---|---|---|
    | 被动 | {{p2.passive_index:.2f}} | — |
    | 双通道 | {{p2.control_index:.2f}} | {{p2.reduction_pct:pct}} |

占位格式（键名就是 results.json 里的路径，扁平点号键与嵌套路径都支持）：

    {{key}}              按 schema 的 digits 格式化
    {{key:.3f}}          Python 格式串
    {{key:pct}}          乘 100 加百分号（tex 里自动写成 \%）
    {{key:si}}           千分位（md 用逗号，tex 用细空格 7\,225\,200）

用法：
    python fill_tables.py --project 项目N            # 渲染（写 results/tables/）
    python fill_tables.py --project 项目N --check    # 只校验是否最新，不写盘（G2/G4 用）
    python fill_tables.py --project 项目N --json

退出码：0 = 一致／1 = 有错误或过期／2 = 没有模板可填
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
META = re.compile(r"<!--(.*?)-->", re.S)
SEP_CELL = re.compile(r"^:?-{2,}:?$")
THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")


# ---------------------------------------------------------------- 读入

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def split_meta(text: str) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    body = text
    for m in META.finditer(text):
        for part in re.split(r"[|;]", m.group(1)):
            mm = re.match(r"\s*([A-Za-z_]+)\s*[:：]\s*(.*)$", part)
            if mm:
                meta[mm.group(1).strip().lower()] = mm.group(2).strip()
        body = body.replace(m.group(0), "")
    return meta, body


def resolve(data, key: str):
    """按键取值：先按扁平点号键，再按嵌套路径走。返回 (ok, value)。"""
    if isinstance(data, dict) and key in data:
        return True, data[key]
    cur = data
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return False, None
    return True, cur


# ---------------------------------------------------------------- 格式化

def tex_escape(text: str) -> str:
    """只转义正文里的危险字符（% & _ #），$ ... $ 内的数学原样保留。

    反斜杠不转义：模板里本来就允许写 LaTeX（`\\lvert`、`\\max`）；已经带反斜杠的 `\\%`
    也不会被二次转义，否则会变成 `\\\\%`（换行 + 注释），把整张表打烂。
    """
    out: list[str] = []
    for i, chunk in enumerate(text.split("$")):
        if i % 2 == 1:            # 数学模式
            out.append(chunk)
            continue
        out.append(re.sub(r"(?<!\\)([%&_#])", r"\\\1", chunk))
    return "$".join(out)


def fmt_value(value, spec: str | None, digits: int | None) -> tuple[str, str]:
    """返回 (markdown 文本, LaTeX 文本) 两种写法。

    spec 支持：`pct`（×100 加 %）、`si`（千分位）、`*factor`（单位换算，如 `*1000` 把 m 变 mm）、
    以及它们的组合 `*1000:.2f`；`*factor` 只用于**单位换算**，比值/降幅这类结论量必须在
    results.json 里立键，不许在模板里现算（现算那一步没人复核）。
    """
    if isinstance(value, bool):
        text = "是" if value else "否"
        return text, text
    if not isinstance(value, (int, float)):
        text = str(value)
        return text, tex_escape(text)

    v = float(value)
    spec = (spec or "").strip()
    if spec.startswith("*"):
        head, _, rest = spec.partition(":")
        try:
            v *= float(head[1:].strip())
        except ValueError as exc:
            raise ValueError(f"换算因子写错了：{spec!r}（写法 `*1000:.2f`）") from exc
        spec = rest.strip()
    if spec == "pct":
        nd = 2 if digits is None else digits
        md = f"{v * 100:.{nd}f} %"
        tx = f"{v * 100:.{nd}f}\\,\\%"
        return md, tx
    if spec == "si":
        nd = 0 if digits is None else digits
        md = f"{v:,.{nd}f}"
        return md, md.replace(",", r"\,")
    if spec:
        try:
            text = format(v, spec)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"格式串 {spec!r} 不能用于 {v!r}：{exc}") from exc
    elif digits is not None:
        text = f"{v:.{digits}f}"
    else:
        text = f"{v:g}"
    return text, text


def render_cell(cell: str, results: dict, schema_keys: dict, problems: list[str]) -> tuple[str, str]:
    """占位符换成数值，其余文字原样保留（LaTeX 侧转义危险字符）。"""
    md_parts: list[str] = []
    tx_parts: list[str] = []
    pos = 0
    for m in PLACEHOLDER.finditer(cell):
        lit = cell[pos:m.start()]
        md_parts.append(lit)
        tx_parts.append(tex_escape(lit))
        pos = m.end()
        raw = m.group(1).strip()
        key, _, spec = raw.partition(":")
        key, spec = key.strip(), spec.strip()
        ok, value = resolve(results, key)
        if not ok:
            problems.append(f"结果键缺失：{{{{{key}}}}}（results.json 里没有这个键，先跑代码或改键名）")
            md_parts.append("??")
            tx_parts.append(r"\textbf{??}")
            continue
        if key not in schema_keys:
            problems.append(f"未声明键：{{{{{key}}}}} 没写进 results/schema.json（表格在偷用结果）")
        try:
            md_s, tx_s = fmt_value(value, spec, (schema_keys.get(key) or {}).get("digits"))
        except ValueError as exc:
            problems.append(str(exc))
            md_s, tx_s = "??", r"\textbf{??}"
        md_parts.append(md_s)
        tx_parts.append(tx_s)
    lit = cell[pos:]
    md_parts.append(lit)
    tx_parts.append(tex_escape(lit))
    return "".join(md_parts), "".join(tx_parts)


# ---------------------------------------------------------------- 渲染

def parse_table(body: str) -> tuple[list[str], list[list[str]], str]:
    """返回 (表头, 数据行, 表后的说明文字)。只取第一张表。"""
    lines = body.splitlines()
    header: list[str] | None = None
    rows: list[list[str]] = []
    consumed_until = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|"):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        consumed_until = i + 1
        if header is None:
            header = cells
            continue
        if all(SEP_CELL.match(c) or c == "" for c in cells):
            continue
        rows.append(cells)
    tail = "\n".join(lines[consumed_until:]).strip()
    return (header or []), rows, tail


def tex_table(header: list[str], rows: list[list[str]], meta: dict, tail_tx: str) -> str:
    ncol = max([len(header)] + [len(r) for r in rows]) if (header or rows) else 0
    if ncol == 0:
        return ""
    heads = [h.rstrip("*").strip() for h in header] + [""] * (ncol - len(header))
    fmt = meta.get("format", "auto")
    if fmt == "fixed":
        total = round(1.04 - 0.04 * ncol, 2)
        first = round(total * 1.3 / (ncol + 0.3), 2)
        rest = round((total - first) / max(ncol - 1, 1), 2) if ncol > 1 else 0.0
        widths = [first] + [rest] * (ncol - 1)
        # 分列舍入会攒出 0.01 的误差，把差额塞进最后一列，保证列宽之和正好等于 total
        widths[-1] = round(widths[-1] + (total - sum(widths)), 2)
        cols = (f">{{\\raggedright\\arraybackslash}}p{{{widths[0]}\\textwidth}}"
                + "".join(f">{{\\raggedleft\\arraybackslash}}p{{{w}\\textwidth}}" for w in widths[1:]))
    else:
        cols = "@{}l" + "r" * (ncol - 1) + "@{}"

    out = ["\\begin{table}[htbp]", "  \\centering", f"  \\caption{{{tex_escape(meta.get('caption', ''))}}}"]
    if meta.get("label"):
        out.append(f"  \\label{{{meta['label']}}}")
    out += [f"  \\begin{{tabular}}{{{cols}}}", "    \\toprule",
            "    " + " & ".join(heads) + " \\\\", "    \\midrule"]
    for r in rows:
        cells = [c for c in r] + [""] * (ncol - len(r))
        out.append("    " + " & ".join(cells) + " \\\\")
    out += ["    \\bottomrule", "  \\end{tabular}"]
    if tail_tx:
        out.append("  \\par\\vspace{2pt}{\\footnotesize " + tail_tx + "}")
    out.append("\\end{table}")
    return "\n".join(out) + "\n"


def render_one(tpl: Path, results: dict, schema_keys: dict) -> tuple[str, str, dict]:
    text = read_text(tpl)
    meta, body = split_meta(text)
    problems: list[str] = []
    header, rows, tail = parse_table(body)

    md_header = [h.rstrip("*").strip() for h in header]
    md_rows, tx_rows = [], []
    for r in rows:
        md_cells, tx_cells = [], []
        for c in r:
            bare = c[:-1].rstrip() if c.endswith("*") else c   # 尾随 * = 显式字面值
            a, b = render_cell(bare, results, schema_keys, problems)
            md_cells.append(a)
            tx_cells.append(b)
        md_rows.append(md_cells)
        tx_rows.append(tx_cells)
    md_head_cells, tx_head_cells = [], []
    for h in header:
        h = h.rstrip("*").strip()
        a, b = render_cell(h, results, schema_keys, problems)
        md_head_cells.append(a)
        tx_head_cells.append(b)

    stem = tpl.name[: -len(".tpl.md")]
    md_lines = [f"<!-- 由 fill_tables.py 从 {tpl.name} 生成，勿手改 -->", ""]
    if meta.get("caption"):
        md_lines += [f"**{meta['caption']}**", ""]
    md_lines.append("| " + " | ".join(md_head_cells) + " |")
    md_lines.append("|" + "|".join(["---"] * len(md_head_cells)) + "|")
    for r in md_rows:
        md_lines.append("| " + " | ".join(r) + " |")
    if tail:
        md_lines += ["", tail]
    md_text = "\n".join(md_lines) + "\n"

    tail_md, tail_tx = render_cell(tail, results, schema_keys, problems) if tail else ("", "")
    tx_meta = dict(meta)
    if not tx_meta.get("label"):
        tx_meta["label"] = f"tab:{stem}"
    tx_text = tex_table(tx_head_cells, tx_rows, tx_meta, tail_tx)

    info = {"tpl": tpl.relative_to(tpl.parents[2]).as_posix(),
            "rows": len(md_rows), "cols": len(md_head_cells),
            "keys": sorted({k.split(":", 1)[0].strip()
                            for k in PLACEHOLDER.findall(text)}),
            "problems": problems}
    return md_text, tx_text, info


# ---------------------------------------------------------------- 入口

def main() -> int:
    ap = argparse.ArgumentParser(description="把 reports/tables/*.tpl.md 用 results.json 填成真表")
    ap.add_argument("--project", default=".", help="项目根目录")
    ap.add_argument("--check", action="store_true", help="只校验是否与 results.json 一致，不写盘")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    tdir = project / "reports" / "tables"
    tpls = sorted(tdir.glob("*.tpl.md")) if tdir.is_dir() else []
    res_path = project / "results" / "results.json"
    sch_path = project / "results" / "schema.json"

    if not tpls:
        print(f"[FAIL] 没有表格骨架：{tdir}/*.tpl.md 不存在。"
              f"S1 必须先把表格写成模板，S2 才有东西可填。")
        return 2
    if not res_path.is_file():
        print(f"[FAIL] 缺少 {res_path}：先跑 code/ 把结果写出来")
        return 1

    results = load_json(res_path)
    schema_keys: dict = {}
    if sch_path.is_file():
        schema = load_json(sch_path)
        schema_keys = {k: v for k, v in (schema.get("keys") or {}).items() if not k.startswith("_")}

    outdir = project / "results" / "tables"
    outdir.mkdir(parents=True, exist_ok=True)
    record_path = outdir / "_render.json"
    record = {}
    if record_path.is_file():
        try:
            record = load_json(record_path)
        except json.JSONDecodeError:
            record = {}

    errors, warns, rendered = [], [], []
    for tpl in tpls:
        stem = tpl.name[: -len(".tpl.md")]
        md_path = outdir / f"{stem}.md"
        tx_path = outdir / f"{stem}.tex"
        md_text, tx_text, info = render_one(tpl, results, schema_keys)
        sha = hashlib.sha256(tpl.read_bytes()).hexdigest()[:16]

        for msg in info["problems"]:
            (errors if "缺失" in msg or "不能用于" in msg else warns).append(f"{tpl.name}: {msg}")

        stale = False
        if args.check:
            for path, want in ((md_path, md_text), (tx_path, tx_text)):
                if not path.is_file():
                    errors.append(f"{path.relative_to(project).as_posix()} 不存在（还没渲染过）")
                    stale = True
                elif read_text(path) != want:
                    errors.append(f"{path.relative_to(project).as_posix()} 与 results.json 不一致（过期）")
                    stale = True
        else:
            md_path.write_text(md_text, encoding="utf-8")
            tx_path.write_text(tx_text, encoding="utf-8")
        record[stem] = {**info, "tpl_sha": sha, "stale": stale,
                        "rendered_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")}
        rendered.append(stem)

    if not args.check:
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    code = 1 if errors else 0
    if args.json:
        print(json.dumps({"status": "PASS" if code == 0 else "FAIL", "mode": "check" if args.check else "fill",
                          "tables": rendered, "errors": errors, "warns": warns},
                         ensure_ascii=False, indent=2))
    else:
        verb = "校验" if args.check else "渲染"
        print(f"== 表格{verb}  {project.name} ==")
        for stem in rendered:
            info = record[stem]
            print(f"  [OK] {stem}: {info['rows']} 行 × {info['cols']} 列，键 {len(info['keys'])} 个")
        for msg in warns:
            print(f"  [WARN] {msg}")
        for msg in errors:
            print(f"  [FAIL] {msg}")
        if code == 0:
            if args.check:
                print(f"  合计 {len(rendered)} 张表与 results.json 一致")
            else:
                print(f"  合计生成 {len(rendered)} 张表 → results/tables/*.md|.tex（论文用 \\input 引用 .tex）")
        else:
            print(f"  合计 {len(errors)} 条错误：改模板或补结果键后重跑")
    return code


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
