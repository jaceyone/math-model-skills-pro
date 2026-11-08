#!/usr/bin/env python3
"""G2 结果门禁：契约里立的键，一个不漏地填上了吗？

S2 的验收不是"代码跑通了"，而是**契约被填满**：

    1. results/schema.json 里每个键都能在 results.json 里取到值（缺一个就是漏算）
    2. 每个键的 producer 脚本真实存在，且脚本里出现该键名（防"声明了但没人写"）
    3. 每个 figure:data_x 消费者对应的图片真实存在
    4. results/tables/*.md|.tex 与 results.json 一致（没渲染或改完代码没重渲染都算失败）
    5. results.json 里没申报的数值列出来（--strict 时算 ERROR）

用法：
    python check_results.py --project 项目N
    python check_results.py --project 项目N --strict    # 未申报键也算失败
    python check_results.py --project 项目N --json

退出码：0 = 通过／1 = 有 ERROR／2 = 契约未建立（先回去跑 check_contract）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import fill_tables as ft
except Exception as exc:  # noqa: BLE001 - 同目录脚本缺失或被改名
    print(f"[FAIL] 找不到同目录的 fill_tables.py：{exc}")
    raise SystemExit(1) from exc

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_]*(\.[a-z0-9_]+)+$")
# results.json 里这些键是元信息/运行痕迹，不要求申报
META_PREFIX = ("environment", "generated_at", "project", "seed", "version", "meta", "_")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)


def flatten_numbers(obj, prefix: str = "") -> dict[str, float]:
    """把 results.json 摊平成 {点号路径: 数值}，只收数字（bool 不算）。"""
    out: dict[str, float] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten_numbers(v, f"{prefix}{k}."))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out.update(flatten_numbers(v, f"{prefix}{i}."))
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out[prefix.rstrip(".")] = float(obj)
    return out


def script_mentions(path: Path, key: str) -> bool:
    """脚本里是否出现这个键（允许只写末段，兼容 dict 组装式写法）。"""
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    if key in text:
        return True
    tail = key.rsplit(".", 1)[-1]
    return len(tail) >= 3 and tail in text


def check_schema_filled(schema: dict, results: dict, project: Path, rpt: Report) -> None:
    keys = schema["keys"]
    missing = [k for k in keys if not ft.resolve(results, k)[0]]
    for k in sorted(missing):
        rpt.err(f"结果键未填：{k}（schema 声明了 {keys[k].get('label', '')}，results.json 里没有）")
    for k in sorted(set(keys) - set(missing)):
        prod = str(keys[k].get("producer", "")).strip()
        if not prod:
            continue
        path = project / prod
        if not path.is_file():
            rpt.err(f"生产者缺失：{k} ← {prod} 不存在")
        elif not script_mentions(path, k):
            rpt.warn(f"生产者可疑：{prod} 里找不到键名 {k}（可能是拼错或由别的脚本写入）")
    if keys:
        print(f"  键覆盖：{len(keys) - len(missing)}/{len(keys)} 已填")


def check_consumers(schema: dict, project: Path, rpt: Report) -> None:
    for k, spec in schema["keys"].items():
        for c in spec.get("consumers") or []:
            s = str(c).strip()
            kind, _, target = s.partition(":")
            kind, target = kind.strip(), target.strip()
            if kind == "figure":
                if not target.startswith("data_"):
                    continue          # 机理图/流程图在 S3 才出，G2 不管
                hits = list((project / "figures").glob(f"{target}.*")) if (project / "figures").is_dir() else []
                if not hits:
                    rpt.err(f"图未出：{k} 声明 consumer figure:{target}，但 figures/{target}.* 不存在")
            elif kind == "table":
                stem = target[:-3] if target.endswith(".md") else target
                stem = Path(stem).name
                if not (project / "reports" / "tables" / f"{stem}.tpl.md").is_file():
                    rpt.err(f"表未建：{k} 声明 consumer table:{target}，但 reports/tables/{stem}.tpl.md 不存在")


def check_undeclared(schema: dict, results: dict, rpt: Report, strict: bool) -> None:
    declared = set(schema["keys"])
    flat = flatten_numbers(results)
    undeclared = []
    for path in flat:
        if path in declared or path.startswith(META_PREFIX):
            continue
        # 允许用父级键申报整块（如 p2.params 覆盖 p2.params.cadd）
        if any(path.startswith(d + ".") or d.startswith(path + ".") for d in declared):
            continue
        undeclared.append(path)
    if not undeclared:
        print("  未申报键：0（results.json 全是契约里立过的数）")
        return
    msg = (f"results.json 里有 {len(undeclared)} 个数值没在 schema 申报："
           + ", ".join(sorted(undeclared)[:12]) + (" …" if len(undeclared) > 12 else ""))
    (rpt.err if strict else rpt.warn)(msg)


def check_tables_fresh(project: Path, results: dict, schema: dict, rpt: Report) -> None:
    tdir = project / "reports" / "tables"
    tpls = sorted(tdir.glob("*.tpl.md")) if tdir.is_dir() else []
    if not tpls:
        rpt.err("没有表格骨架 reports/tables/*.tpl.md：论文表只能手抄，数值必然漂")
        return
    schema_keys = schema["keys"]
    outdir = project / "results" / "tables"
    before = len(rpt.errors)
    for tpl in tpls:
        stem = tpl.name[: -len(".tpl.md")]
        md_text, tx_text, info = ft.render_one(tpl, results, schema_keys)
        for msg in info["problems"]:
            if "缺失" in msg or "不能用于" in msg:
                rpt.err(f"{tpl.name}: {msg}")
            else:
                rpt.warn(f"{tpl.name}: {msg}")
        for path, want in ((outdir / f"{stem}.md", md_text), (outdir / f"{stem}.tex", tx_text)):
            if not path.is_file():
                rpt.err(f"表未渲染：{path.relative_to(project).as_posix()}（跑 fill_tables.py）")
            elif path.read_text(encoding="utf-8-sig", errors="replace") != want:
                rpt.err(f"表已过期：{path.relative_to(project).as_posix()} 与 results.json 不一致（重跑 fill_tables.py）")
    if tpls and len(rpt.errors) == before:
        print(f"  表格：{len(tpls)} 张已渲染且与 results.json 一致")


def check_allow_file(project: Path, rpt: Report) -> None:
    path = project / "results" / "numbers_allow.txt"
    if not path.is_file():
        return
    for i, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
        s = line.split("#", 1)[0].strip()
        if not s:
            continue
        try:
            re.compile(s)
        except re.error as exc:
            rpt.warn(f"numbers_allow.txt:{i} 正则不合法（会让 check_paper 直接崩）：{exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description="G2 结果门禁：契约键是否全部填满、表是否最新")
    ap.add_argument("--project", default=".", help="项目根目录")
    ap.add_argument("--strict", action="store_true", help="未申报键也算 ERROR")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    rpt = Report()

    res_path = project / "results" / "results.json"
    sch_path = project / "results" / "schema.json"
    if not sch_path.is_file():
        payload = {"status": "NO_CONTRACT", "message": f"缺少 {sch_path}",
                   "hint": "先跑 check_contract.py 建契约，再写代码"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json
              else f"[FAIL] 契约未建立：{payload['message']}\n  {payload['hint']}")
        return 2
    if not res_path.is_file():
        rpt.err(f"缺少 {res_path}")
        results: dict = {}
        schema: dict = {"keys": {}}
    else:
        schema = ft.load_json(sch_path)
        schema["keys"] = {k: v for k, v in (schema.get("keys") or {}).items() if not k.startswith("_")}
        try:
            results = ft.load_json(res_path)
        except json.JSONDecodeError as exc:
            rpt.err(f"{res_path} 不是合法 JSON：{exc}")
            results = {}

    if args.json is False:
        print(f"== G2 结果门禁  {project.name} ==")
    if results:
        check_schema_filled(schema, results, project, rpt)
        check_undeclared(schema, results, rpt, args.strict)
        check_consumers(schema, project, rpt)
        check_tables_fresh(project, results, schema, rpt)
        check_allow_file(project, rpt)

    code = 1 if rpt.errors else 0
    if args.json:
        print(json.dumps({"status": "PASS" if code == 0 else "FAIL", "project": str(project),
                          "keys": len(schema["keys"]), "errors": rpt.errors, "warns": rpt.warns},
                         ensure_ascii=False, indent=2))
    else:
        for msg in rpt.warns:
            print(f"  [WARN] {msg}")
        for msg in rpt.errors:
            print(f"  [FAIL] {msg}")
        print(f"  合计：ERROR {len(rpt.errors)} / WARN {len(rpt.warns)}")
        print()
        print("结果门禁通过：契约键全填、表已渲染、未申报键已说明。" if code == 0
              else "结果门禁未过：先把上面 ERROR 清掉再进 S3。")
    return code


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
