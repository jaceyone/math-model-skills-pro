#!/usr/bin/env python3
"""G1 契约门禁：先有"要交什么"，才许写模型代码。

本脚本检查 S1 阶段必须先落盘的三份契约，把"报告先行"从口号变成可执行的判据：

    results/schema.json          结果键清单（论文里每个数先在这里立名）
    reports/tables/*.tpl.md      表格骨架（列名/单位/行标签先写，数值格留 {{key}}）
    reports/图件规划.md          图件清单（每张数据图声明 reads: 哪些键）

外加 reports/SCORE_MAP.md（得分点 → 证据 → 落点）与三轮回质检留痕。

用法：
    python check_contract.py --project 项目N
    python check_contract.py --project 项目N --json
    python check_contract.py --project 项目N --tolerate-plan   # 历史工程回填：图件 reads 缺失降级为 WARN

退出码：0 = 通过（可有 WARN）／1 = 契约有 ERROR／2 = 契约尚未建立（schema.json 不存在）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 正则与常量

PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
META = re.compile(r"<!--(.*?)-->", re.S)
# 键名 = results.json 里的路径：小写 snake_case 优先；物理符号（const.M / const.T）允许大写
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+$")
SEP_CELL = re.compile(r"^:?-{2,}:?$")
NUM_CELL = re.compile(
    r"^[-+]?\d+(?:[.,]\d+)?\s*"
    r"(?:%|‰|kN|N|kg|t|mm|cm|m|s|ms|min|h|Hz|kHz|rad/s|rad/s\^?2|m/s|m/s\^?2|"
    r"m/s²|N·s/m|N/m|m\^?2|m²|°|deg)?$"
)
FIG_ID = re.compile(r"\b(data|mech|paper|flow)_[a-z0-9_]+")
READS = re.compile(r"reads\s*[:：=]\s*(.+)$", re.I)

# 表格模板前置注释里允许出现的字段
META_FIELDS = {"table", "id", "caption", "label", "format", "note", "width"}
FORMATS = {"auto", "fixed"}


class Report:
    """收集检查结果：ERROR 决定退出码，WARN 只提示。"""

    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, level: str, code: str, where: str, msg: str) -> None:
        self.items.append({"level": level, "code": code, "where": where, "msg": msg})

    def err(self, code: str, where: str, msg: str) -> None:
        self.add("ERROR", code, where, msg)

    def warn(self, code: str, where: str, msg: str) -> None:
        self.add("WARN", code, where, msg)

    def info(self, code: str, where: str, msg: str) -> None:
        self.add("INFO", code, where, msg)

    @property
    def errors(self) -> list[dict]:
        return [i for i in self.items if i["level"] == "ERROR"]

    @property
    def warns(self) -> list[dict]:
        return [i for i in self.items if i["level"] == "WARN"]

    def print(self, title: str) -> None:
        print(f"== {title} ==")
        order = {"ERROR": 0, "WARN": 1, "INFO": 2}
        rows = sorted(self.items, key=lambda i: (order[i["level"]], i["code"]))
        if not rows:
            print("  [OK] 无问题")
        for it in rows:
            tag = {"ERROR": "[FAIL]", "WARN": "[WARN]", "INFO": "[INFO]"}[it["level"]]
            print(f"  {tag} {it['code']} @ {it['where']}")
            print(f"         {it['msg']}")
        print(f"  合计：ERROR {len(self.errors)} / WARN {len(self.warns)}"
              f" / INFO {len(self.items) - len(self.errors) - len(self.warns)}")
        print()


# ---------------------------------------------------------------- 通用工具

def read_text(path: Path) -> str:
    """统一按 utf-8-sig 读：PowerShell / 记事本存盘会带 BOM，普通 utf-8 会崩。"""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def split_meta(text: str) -> tuple[dict, str]:
    """取出模板顶部的 <!-- table: id | caption: ... --> 注释，返回 (字段, 去掉注释的正文)。"""
    meta: dict[str, str] = {}
    body = text
    for m in META.finditer(text):
        chunk = m.group(1)
        if ":" not in chunk and "：" not in chunk:
            continue
        for part in re.split(r"[|;]", chunk):
            if not part.strip():
                continue
            mm = re.match(r"\s*([A-Za-z_]+)\s*[:：]\s*(.*)$", part)
            if mm:
                meta[mm.group(1).strip().lower()] = mm.group(2).strip()
        body = body.replace(m.group(0), "")
    return meta, body


def table_rows(body: str) -> tuple[list[str] | None, list[list[str]]]:
    """从 markdown 里抽第一张表：(表头列表, 数据行)。抽不到返回 (None, [])。"""
    lines = body.splitlines()
    header: list[str] | None = None
    rows: list[list[str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|"):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(SEP_CELL.match(c) or c == "" for c in cells):
            continue
        rows.append(cells)
    return header, rows


def placeholder_keys(cell: str) -> list[str]:
    out = []
    for m in PLACEHOLDER.finditer(cell):
        raw = m.group(1).strip()
        key = raw.split(":", 1)[0].strip()
        if key:
            out.append(key)
    return out


def load_schema(project: Path) -> tuple[dict | None, str]:
    path = project / "results" / "schema.json"
    if not path.is_file():
        return None, f"缺少 {path}"
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return None, f"{path} 不是合法 JSON：{exc}"
    if not isinstance(data, dict) or not isinstance(data.get("keys"), dict):
        return None, f'{path} 缺少顶层 "keys" 对象（见 references/contracts/results-schema.md）'
    keys = {k: v for k, v in data["keys"].items() if not k.startswith("_")}
    data["keys"] = keys
    return data, ""


# ---------------------------------------------------------------- 各项检查

def check_schema(schema: dict, project: Path, rpt: Report) -> None:
    keys = schema["keys"]
    if not keys:
        rpt.err("SCHEMA_EMPTY", "results/schema.json",
                "keys 为空：S1 必须先把论文要出现的每个数立成键（含义/单位/生产者/消费者）")
        return
    for name, spec in keys.items():
        where = f"results/schema.json#{name}"
        if not KEY_RE.match(name):
            rpt.err("KEY_BAD_NAME", where,
                    "键名须至少两级、只含字母数字下划线（小写 snake_case 优先，物理符号允许大写，"
                    "如 const.M）；单段键会把不同问题的同名指标混在一起")
        if not isinstance(spec, dict):
            rpt.err("KEY_BAD_SPEC", where, "键的值必须是对象：label/unit/producer/consumers")
            continue
        for field in ("label", "unit", "producer"):
            if not str(spec.get(field, "")).strip():
                rpt.err("KEY_NO_FIELD", where, f"缺 {field}（unit 无单位也要显式写 \"-\"）")
        digits = spec.get("digits")
        if digits is not None and (not isinstance(digits, int) or not 0 <= digits <= 8):
            rpt.err("KEY_BAD_DIGITS", where, f"digits 须为 0–8 的整数，现为 {digits!r}")
        cons = spec.get("consumers")
        if not isinstance(cons, list) or not cons:
            rpt.err("KEY_NO_CONSUMER", where,
                    "缺 consumers：声明了这个键却没声明谁读它（table:/figure:/paper:§N）"
                    "——没有消费者的键就是没人要的数，删掉")
            continue
        for c in cons:
            s = str(c)
            if not re.match(r"^(table|figure|paper|check)\s*:", s):
                rpt.err("CONSUMER_BAD", where,
                        f"consumer {s!r} 须写成 table:x / figure:data_x / paper:§5.1 / check:x")
        producer = str(spec.get("producer", "")).strip()
        if producer and not re.match(r"^[\w./\\-]+\.py$", producer):
            rpt.err("PRODUCER_BAD", where, f"producer 须写脚本相对路径（如 code/problem1.py），现为 {producer!r}")
        elif producer and not (project / producer).is_file():
            rpt.info("PRODUCER_PENDING", where, f"{producer} 尚未创建（S1 允许，G2 必须有）")


def check_tables(schema: dict, project: Path, rpt: Report) -> None:
    keys = set(schema["keys"])
    tdir = project / "reports" / "tables"
    tpls = sorted(tdir.glob("*.tpl.md")) if tdir.is_dir() else []
    if not tpls:
        if tdir.is_dir() and any(tdir.iterdir()):
            rpt.err("TABLE_NO_TPL", "reports/tables/",
                    "目录里有文件但没有 *.tpl.md：表格模板必须留后缀 .tpl.md，"
                    "生成物由 fill_tables.py 写到 results/tables/")
        else:
            rpt.err("TABLE_NO_TPL", "reports/tables/",
                    "没有表格骨架。S1 必须先把论文的每张数值表写成 *.tpl.md（列名/单位/行标签先写，"
                    "数值格留 {{key}}），代码阶段只负责把这些格子填上")
        return

    for tpl in tpls:
        where = tpl.relative_to(project).as_posix()
        text = read_text(tpl)
        meta, body = split_meta(text)
        stem = tpl.name[: -len(".tpl.md")]
        if not meta:
            rpt.err("TABLE_NO_META", where,
                    '缺前置注释：<!-- table: %s | caption: 表题 | label: tab:%s -->（caption/label 供论文 \\input）'
                    % (stem, stem))
        else:
            for k in meta:
                if k not in META_FIELDS:
                    rpt.warn("TABLE_META_UNKNOWN", where, f"未知前置字段 {k!r}（可用：{sorted(META_FIELDS)}）")
            if not meta.get("caption"):
                rpt.err("TABLE_NO_CAPTION", where, "前置注释缺 caption（表题在表上，S4 直接复用）")
            label = meta.get("label", "")
            if label and not re.match(r"^tab:[A-Za-z0-9:_-]+$", label):
                rpt.err("TABLE_BAD_LABEL", where, f"label 须写成 tab:xxx，现为 {label!r}")
            fmt = meta.get("format", "auto")
            if fmt not in FORMATS:
                rpt.err("TABLE_BAD_FORMAT", where, f"format 只能是 {sorted(FORMATS)}，现为 {fmt!r}")

        header, rows = table_rows(body)
        if header is None or not rows:
            rpt.err("TABLE_NOT_PARSED", where,
                    "没解析出 markdown 表（需要 | 列名 | … | 加一行 |---|---| 再加数据行）")
            continue
        literal_cols = {i for i, h in enumerate(header) if h.rstrip().endswith("*")}

        used = 0
        for ridx, cells in enumerate(rows, 1):
            for cidx, cell in enumerate(cells):
                for key in placeholder_keys(cell):
                    used += 1
                    if key not in keys:
                        rpt.err("TABLE_UNKNOWN_KEY", f"{where}:行{ridx}",
                                f"{{{{{key}}}}} 未在 results/schema.json 声明——先在 schema 里立键，再填表")
                if "{{" in cell:
                    continue
                forced = cell.rstrip().endswith("*")
                probe = cell.rstrip().rstrip("*").replace("$", "").replace("\\", "").strip()
                if NUM_CELL.match(probe):
                    head = header[cidx] if cidx < len(header) else "?"
                    if cidx in literal_cols or forced:
                        rpt.info("TABLE_LITERAL", f"{where}:行{ridx}",
                                 f"列「{head}」的字面值 {probe!r}（列头带 * 或格尾带 *，按设计常数处理）")
                    else:
                        rpt.err("TABLE_HARDCODE", f"{where}:行{ridx}",
                                f"列「{head}」里写死了数值 {cell!r}。结果格只能写 {{{{key}}}}；"
                                f"若这列确是设计常数，把表头写成「{head}*」显式声明")
        if used == 0:
            rpt.err("TABLE_NO_PLACEHOLDER", where,
                    "整张表没有 {{key}} 占位：这张表是手抄的，不是从 results.json 生成的")
        rpt.info("TABLE_OK", where, f"{len(rows)} 行 × {len(header)} 列，占位 {used} 个")


def check_figure_plan(schema: dict, project: Path, rpt: Report, tolerate: bool) -> None:
    keys = set(schema["keys"])
    cands = [project / "reports" / "图件规划.md", project / "reports" / "FIGURE_PLAN.md",
             project / "reports" / "figure_plan.md"]
    plan = next((p for p in cands if p.is_file()), None)
    if plan is None:
        rpt.err("PLAN_MISSING", "reports/图件规划.md",
                "缺图件规划：四路图件（data_/mech_/paper_/flow_）先在这张表里定，再谈画法")
        return
    where = plan.relative_to(project).as_posix()
    lines = read_text(plan).splitlines()
    data_ids = 0
    for i, line in enumerate(lines):
        for m in FIG_ID.finditer(line):
            fid = m.group(0)
            if not fid.startswith("data_"):
                continue
            data_ids += 1
            window = " ".join(lines[i: i + 3])
            rm = READS.search(window)
            if not rm:
                msg = (f"数据图 {fid} 未声明 reads：数据图只能读 results.json 里已立键的值，"
                       f"写成 `reads: key1, key2`（同一行或紧随其下两行内）")
                if tolerate:
                    rpt.warn("FIG_NO_READS", f"{where}:{i + 1}", msg)
                else:
                    rpt.err("FIG_NO_READS", f"{where}:{i + 1}", msg)
                continue
            raw = rm.group(1)
            for key in [k.strip(" `,，") for k in re.split(r"[,，\s]+", raw) if k.strip(" `,，")]:
                if not KEY_RE.match(key):
                    continue
                if key not in keys:
                    rpt.err("FIG_UNKNOWN_KEY", f"{where}:{i + 1}",
                            f"{fid} 的 reads 里有未声明键 {key!r}")
    if data_ids == 0:
        rpt.warn("PLAN_NO_DATA_FIG", where, "没有出现 data_* 数据图：确认本题确实不需要数值图")
    else:
        rpt.info("PLAN_OK", where, f"{data_ids} 张数据图")


def check_score_map(schema: dict, project: Path, rpt: Report) -> None:
    path = project / "reports" / "SCORE_MAP.md"
    if not path.is_file():
        rpt.err("SCORE_MISSING", "reports/SCORE_MAP.md", "缺得分点表：S1 先立点，S2 核账，S4 落点")
        return
    where = path.relative_to(project).as_posix()
    keys = set(schema["keys"])
    header, rows = table_rows(read_text(path))
    if header is None or not rows:
        rpt.err("SCORE_NOT_PARSED", where, "没解析出 markdown 表")
        return
    anchor = re.compile(r"tab:|fig:|表\s*\d|图\s*\d|式\s*[\(（]?\d|§|附录|reads")
    for ridx, cells in enumerate(rows, 1):
        line = " | ".join(cells)
        has_key = any(k in line for k in keys)
        has_anchor = bool(anchor.search(line))
        done = bool(re.search(r"[√✓✔]|已证|PASS", line))
        if (has_key or has_anchor):
            continue
        if done:
            rpt.err("SCORE_ROW_NO_ANCHOR", f"{where}:行{ridx}",
                    "这条得分点标了已证，却既没有结果键、也没有图号/表号/式号/节号可指——"
                    "「已证」必须能点到东西")
        else:
            rpt.warn("SCORE_ROW_THIN", f"{where}:行{ridx}",
                     "这条得分点没挂结果键，S4 无法核对；建议补 table:/figure:/key")


def check_report_mentions(schema: dict, project: Path, rpt: Report) -> None:
    """报告与契约互相兜底：schema 里的键，报告里得有它的定义。"""
    path = project / "reports" / "ANALYSIS_MODELING_REPORT.md"
    if not path.is_file():
        rpt.err("REPORT_MISSING", "reports/ANALYSIS_MODELING_REPORT.md",
                "缺建模分析报告：模型、公式、算法、校验方法都在这里，契约只定义交付")
        return
    text = read_text(path)
    missing = []
    for name, spec in schema["keys"].items():
        label = str(spec.get("label", "")).strip()
        if name in text or (label and label in text):
            continue
        missing.append(name)
    if missing:
        rpt.warn("REPORT_NO_KEY", "reports/ANALYSIS_MODELING_REPORT.md",
                 f"{len(missing)} 个键在报告里找不到定义（键名或其 label 都没出现）："
                 + ", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")
                 + "。报告定义模型，契约定义交付，两边必须对得上")
    else:
        rpt.info("REPORT_OK", "reports/ANALYSIS_MODELING_REPORT.md",
                 f"{len(schema['keys'])} 个键都能在报告里找到定义")


def check_qc(project: Path, rpt: Report) -> None:
    rounds = [project / "reports" / f"QC_S1_ROUND.{i}.md" for i in (1, 2, 3)]
    missing = [p.name for p in rounds if not p.is_file()]
    if missing:
        rpt.err("QC_MISSING", "reports/", f"缺质检留痕：{', '.join(missing)}（G1 要求 3 轮全做完）")
        return
    for p in rounds:
        txt = read_text(p)
        tail = "\n".join([ln for ln in txt.splitlines() if ln.strip()][-3:])
        if "结论：PASS" not in tail and "结论: PASS" not in tail:
            rpt.err("QC_NOT_PASS", p.relative_to(project).as_posix(),
                    "最后一行不是 `结论：PASS`（该轮未过或没写结论）")
        else:
            rpt.info("QC_OK", p.name, "结论：PASS")


def check_symbols(project: Path, rpt: Report) -> None:
    path = project / "reports" / "symbols.md"
    if not path.is_file():
        rpt.err("SYMBOLS_MISSING", "reports/symbols.md",
                "缺符号表：S2 变量名、S3 图内标注、S4 符号说明章都照它抄")
        return
    header, rows = table_rows(read_text(path))
    if header is None or not rows:
        rpt.err("SYMBOLS_NOT_PARSED", "reports/symbols.md", "没解析出符号表")
    else:
        rpt.info("SYMBOLS_OK", "reports/symbols.md", f"{len(rows)} 个符号")


# ---------------------------------------------------------------- 入口

def main() -> int:
    ap = argparse.ArgumentParser(description="G1 契约门禁（schema / 表格骨架 / 图件规划 / 得分点 / 质检）")
    ap.add_argument("--project", default=".", help="项目根目录（默认当前目录）")
    ap.add_argument("--json", action="store_true", help="输出 JSON，便于外层脚本消费")
    ap.add_argument("--tolerate-plan", action="store_true",
                    help="历史工程回填：图件规划缺 reads 由 ERROR 降为 WARN")
    ap.add_argument("--no-qc", action="store_true", help="跳过三轮回质检检查（只查契约）")
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        print(f"[FAIL] 项目目录不存在：{project}")
        return 1

    rpt = Report()
    schema, why = load_schema(project)
    if schema is None:
        payload = {
            "status": "NO_CONTRACT",
            "project": str(project),
            "message": why,
            "hint": "先在 results/schema.json 里把论文要出现的每个数立成键"
                    "（label/unit/producer/consumers），再写 reports/tables/*.tpl.md，"
                    "最后才允许写模型代码。见 references/contracts/results-schema.md",
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("== G1 契约门禁 ==")
            print(f"  [FAIL] {why}")
            print(f"  {payload['hint']}")
        return 2

    check_schema(schema, project, rpt)
    check_tables(schema, project, rpt)
    check_figure_plan(schema, project, rpt, args.tolerate_plan)
    check_score_map(schema, project, rpt)
    check_report_mentions(schema, project, rpt)
    check_symbols(project, rpt)
    if not args.no_qc:
        check_qc(project, rpt)

    code = 1 if rpt.errors else 0
    if args.json:
        print(json.dumps({
            "status": "PASS" if code == 0 else "FAIL",
            "project": str(project),
            "keys": len(schema["keys"]),
            "errors": rpt.errors,
            "warns": rpt.warns,
        }, ensure_ascii=False, indent=2))
    else:
        rpt.print(f"G1 契约门禁  {project.name}（结果键 {len(schema['keys'])} 个）")
        if code:
            print("契约未过：先把上面 ERROR 改完。契约阶段改一行，比 S4 回头改一章便宜。")
        else:
            print("契约通过：接下来写代码只许产出 schema 里声明的键。")
    return code


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - 老 Python 或重定向流没有 reconfigure
        pass
    raise SystemExit(main())
