"""结果图闸门:汇总 figures/ 的图面自检结果,有硬伤就退出码 1。

智能体看不见自己画出来的图,压字、空面板、平线、双轴柱这类毛病靠「打开看一眼」
是拦不住的。plot_style 在 savefig 时已就地体检并把结果写进
``figures/_figure_lint.json``;本脚本把它汇总成一道可执行的闸门:

    python check_figures.py          # 退出码 0 = 无硬伤
    python check_figures.py --json   # 机器可读

AI 生成的机理图/流程图(image2 出图,非 matplotlib)不参与体检。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# 闸门自身的版本戳。项目里的副本是从技能 assets/style/ 复制过去的,**复制之后不会自动更新**;
# 旧版(≤2.3.21 早期)在找不到 figures/ 时只打印一句「没有需要体检的结果图」就 exit 0,
# 等于闸门静默放行。`python check_figures.py --version` 可核对手上这份是不是新版。
GATE_VERSION = "2.4.0"

# 工程根怎么定:脚本会被复制到工程根、也可能躺在 code/ 里。按「脚本所在目录」找
# figures/ 会让 code/check_figures.py 去读 code/figures/(不存在),什么都不查就退出码 0
# ——闸门形同虚设。所以按 当前目录 → 脚本目录 的顺序向上找「含 figures/ 的工程根」。
_PROJECT_MARKERS = ("code", "paper", "reports", "results",
                    "meta.json", "research_plan.json")


def _looks_like_project(d: str) -> bool:
    """只有 figures/ 还不够:上层目录里可能躺着别人的 figures/。要像工程才认。"""
    if not os.path.isdir(d):
        return False
    if not os.path.isdir(os.path.join(d, "figures")):
        return False
    return any(os.path.exists(os.path.join(d, m)) for m in _PROJECT_MARKERS)


def _walk_up(start: str, depth: int = 6) -> str:
    """从 start 向上最多 depth 层找工程根;找不到返回空串。"""
    cur = os.path.abspath(start)
    for _ in range(depth + 1):
        if _looks_like_project(cur):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return ""


def resolve_root(explicit: str = "") -> str:
    """工程根 = 含 figures/ 的那一层。显式 > 环境变量 > 当前目录向上 > 脚本目录向上 2 层。"""
    for cand in (explicit, os.environ.get("MS_PROJECT_ROOT", ""), os.getcwd()):
        if cand and os.path.isdir(cand):
            hit = _walk_up(cand)
            if hit:
                return hit
    return _walk_up(os.path.dirname(os.path.abspath(__file__)), depth=2)


ROOT = resolve_root() or os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(ROOT, "figures")
LINT = os.path.join(FIGDIR, "_figure_lint.json")
EXTS = (".png", ".svg", ".pdf")
# image2 生成或系统托管的图:不由 matplotlib 产出,自然没有体检记录
SKIP_PREFIX = ("algo_", "schematic_", "flowchart", "flow_", "paper_",
               "mech_", "_")
SKIP_SUFFIX = ("_mechanism",)


# 出图分两段:实验阶段放开设计,只有下面这几类(内容不对或读不了)算硬伤;其余版式问题标「终审」,
# 不计入退出码,配图终审统一重出图并按一区标准升级。与 studio/domain/figure_policy.py 保持一致。
# `--final` 或 MS_FIG_STAGE=final 恢复终审口径(全部 error 都算硬伤)。
DESIGN_HARD = frozenset({"empty_panel", "mojibake_text", "missing_glyphs", "cjk_font_missing", "cjk_in_mathtext",
                         "cjk_in_en_figure", "pinyin_labels", "raw_subscript", "pie_chart", "radar_chart", "bad_cmap",
                         "no_vector_copy"})


# 两张图的数据取值重合到这个比例,就判定它们画的是同一批数。
# 留 0.9 的余量:同一批数换个图型画,坐标/误差棒会带进几个额外取值。
DUP_OVERLAP = 0.9
DUP_MIN_VALUES = 5      # 五个 Sobol/权重指标已足以判重;两三个值仍不参与


def _skip(stem: str, has_record: bool = False) -> bool:
    """非 matplotlib 产的图（机理/流程图/主图）跳过体检；但**有 lint 记录的照查**。"""
    if has_record:
        return False
    return (stem.startswith(SKIP_PREFIX) or stem.endswith(SKIP_SUFFIX)
            or ".old" in stem)


def _overlap(a: dict, b: dict) -> float:
    """包含率(交集 / 较小那一方);与 plot_style.data_overlap 同口径。"""
    va = set((a or {}).get("values") or [])
    vb = set((b or {}).get("values") or [])
    if not va or not vb:
        return 0.0
    return len(va & vb) / min(len(va), len(vb))


def duplicates(figs: dict) -> list:
    """找出画的是同一批数据的图对。

    一道题往往只有一组核心结果,而「把角色配齐」的要求会诱使人把同一组数换个
    图型再画一遍(实测 problemN.png 是分组柱、problemN_comparison.png 是误差点,
    数一模一样),两张都插进论文,评委一眼看出是凑数。文件名与字节哈希都认不出
    这种重复,只有比对图里画进去的数值才认得出。
    """
    items = [(stem, it["data"]) for stem, it in figs.items()
             if (it.get("data") or {}).get("values")
             and len(it["data"]["values"]) >= DUP_MIN_VALUES]
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ov = _overlap(items[i][1], items[j][1])
            if ov >= DUP_OVERLAP:
                out.append({"a": items[i][0], "b": items[j][0],
                            "overlap": round(ov, 3)})
    return out


def color_conflicts(figs: dict) -> list:
    """同一个量在不同图里用了不同颜色。

    实测:「光伏出力」在 problem1_data 里是红色、在 problem3_data 里是绿色,
    两张图各自体检都通过——**单张图怎么看都看不出来**,只有攒齐全套图才判得了。
    读者翻到第二张时会以为这是另一个量。根因是按 `PALETTE[i]` 下标取色:
    各脚本各排各的序,同一个量的下标自然对不上。
    """
    seen: dict[str, dict[str, list]] = {}
    for stem, item in figs.items():
        for label, color in (item.get("series") or {}).items():
            seen.setdefault(label, {}).setdefault(color, []).append(stem)
    out = []
    for label, by_color in sorted(seen.items()):
        if len(by_color) < 2:
            continue
        where = [(c, sorted(s)) for c, s in by_color.items()]
        out.append({"label": label, "where": sorted(where)})
    return out


# 一张图只画了柱子,没有第二类证据(误差棒/趋势线/分布/热图),读者翻到它只能读出几个高低——
# 信息量撑不起一张正文插图。绘图契约里「简单柱不许单独成图」是软约束,实测会被绕过
# (2026-10-07 项目 122:9 个出图脚本 7 个是 bar),所以在这里做成确定性闸门。
# kinds 词表见 plot_style._chart_kinds:surface/box/line/bar/scatter/heatmap/band/errorbar。
# 横柱也记成 bar,所以纯柱判定就是 kinds == {"bar"}。
_BAR_ONLY = {"bar"}
# 高级图种靠模板写进图里的标记认(plot_style 存图时核验后记为 data.tags);
# 没标记的老图,只有这两种能从图元可靠认出来。
_ADVANCED_TOKENS = {"heatmap": "heatmap", "surface3d": "surface"}
# 本身用柱子画的图种,不算柱状图。与 plot_style.BAR_NATIVE_KINDS 一致。
BAR_NATIVE_KINDS = frozenset({"tornado", "waterfall", "shap", "polar_heatmap", "stacked_bar"})
# 柱状图占比:单个任务最多 1 张;全篇 4 张图以上时柱状图不超过这个比例。
BAR_PER_TASK = 1
BAR_SHARE_MAX = 0.3
BAR_SHARE_MIN_FIGS = 4


def low_information(figs: dict) -> list:
    """纯柱状图 → 硬伤;图里一个数据点都没画 → 提醒。返回 [(stem, level, msg)]。"""
    out = []
    for stem, item in sorted(figs.items()):
        data = item.get("data") or {}
        kinds = set(data.get("kinds") or [])
        n = int(data.get("n") or 0)
        if kinds == _BAR_ONLY:
            out.append((stem, "error",
                        f"只画了柱子({n} 个数),没有第二类证据——读者只能读出几个高低,撑不起一张正文插图。\n"
                        "    改法任选一条:①组图(值+残差/误差棒):`fig, axes = combo_axes(2)`,"
                        "左格柱或折线给值、右格给残差或分布;②把同一批数按另一个维度铺开画热图"
                        "(方案×指标、参数×参数),格子里写数;③密采样成趋势线+区间带。\n"
                        "    实在只有三五个数,删图改三线表,表后配一句把结论说出来——换载体不丢证据。"))
        elif not kinds and n == 0:
            out.append((stem, "warn",
                        "图里没认出任何数据图元(可能是纯示意图)。若它本该画数据,检查是不是把数据画在了"
                        "别的画布上;若确实是示意图,无需处理。"))
    return out


def unused_advanced_kinds(figs: dict) -> list:
    """用户勾了高级图种却一张都没用上 → 提醒。返回 [(kind_id, token)]。"""
    want = []
    try:
        with open(os.path.join(ROOT, "meta.json"), encoding="utf-8") as f:
            opts = (json.load(f) or {}).get("gen_options") or {}
        want = [str(k) for k in (opts.get("figure_kinds") or []) if str(k).strip()]
    except (OSError, ValueError, AttributeError):
        return []
    kinds, tags = set(), set()
    for item in figs.values():
        data = item.get("data") or {}
        kinds |= set(data.get("kinds") or [])
        tags |= set(data.get("tags") or [])
    out = []
    for k in want:
        token = _ADVANCED_TOKENS.get(k, k)
        if k in tags or (k in _ADVANCED_TOKENS and token in kinds):
            continue
        out.append((k, token))
    return out


def _kinds_used(figs: dict) -> tuple:
    kinds, tags = set(), set()
    for item in figs.values():
        data = item.get("data") or {}
        kinds |= set(data.get("kinds") or [])
        tags |= set(data.get("tags") or [])
    return kinds, tags


def _candidates(fig: dict) -> list:
    """一条推荐可接受的图种:主图种 + 备选画法(画成「也可画成」里的那种同样算用上了)。"""
    out = []
    for k in [fig.get("kind")] + list(fig.get("alt_kinds") or []):
        k = str(k or "").strip()
        if k and k != "custom" and k not in out:
            out.append(k)
    return out


def unused_plan_kinds(figs: dict, final: bool = False, skip=()) -> list:
    """研究方案的推荐图没落实 → 提醒。返回 [(task, [kind_id…])]。

    作者在方案页勾过图(picked)的任务:勾的每一张都得画,逐张核对,没画的各报一条。
    没勾过的任务:推荐是候选清单,按数据挑着画,没画全不算问题;一种都没用上才说明又退回了素图。
    任务 N 的图名以 problemN 开头,只拿它自己的图来认;还没开始出图的任务不报
    (实验按任务顺序跑,前面的任务不该被后面的推荐催)。终审口径下全部报。
    skip:已经按「用户勾选」报过的图种;主图种在里面的推荐连同备选画法都不再重复报。
    """
    try:
        with open(os.path.join(ROOT, "research_plan.json"), encoding="utf-8") as f:
            tasks = (json.load(f) or {}).get("tasks") or []
    except (OSError, ValueError, AttributeError):
        return []
    out = []
    for i, t in enumerate(tasks if isinstance(tasks, list) else [], start=1):
        task = f"problem{i}"
        mine = {s: it for s, it in figs.items() if _task_of(s) == task}
        if not isinstance(t, dict) or not (final or mine):
            continue
        recs = [f for f in t.get("figures") or []
                if isinstance(f, dict) and str(f.get("kind") or "").strip() not in skip]
        picked = [f for f in recs if f.get("picked")]
        kinds, tags = _kinds_used(mine)

        def used(want):
            return any(k in tags or (k in _ADVANCED_TOKENS and _ADVANCED_TOKENS[k] in kinds) for k in want)

        groups = [_candidates(f) for f in picked] if picked else [
            [k for f in recs for k in _candidates(f)]]
        for want in groups:
            want = list(dict.fromkeys(want))
            if want and not used(want):
                out.append((task, want))
    return out


def _task_of(stem: str) -> str:
    m = re.match(r"problem(\d+)", stem)
    return f"problem{m.group(1)}" if m else ""


def is_bar_figure(item: dict) -> bool:
    data = item.get("data") or {}
    return "bar" in (data.get("kinds") or []) and not (set(data.get("tags") or []) & BAR_NATIVE_KINDS)


def bar_heavy(figs: dict) -> list:
    """柱状图太多:带柱子就算(加误差棒、叠折线照样算),龙卷风/瀑布这类本身是柱子的图种除外。

    只拦纯柱时,实测主图清一色「柱+误差棒+均值线」(2026-10 项目 121:8 张柱图里 6 张是这个组合)。
    返回 [(范围, level, msg)]。
    """
    data_figs = {s: it for s, it in figs.items() if (it.get("data") or {}).get("kinds")}
    bars = sorted(s for s, it in data_figs.items() if is_bar_figure(it))
    out = []
    by_task: dict = {}
    for s in bars:
        if _task_of(s):
            by_task.setdefault(_task_of(s), []).append(s)
    alt = ("多次运行的对比改画每次运行的散点+均值与置信区间、同种子配对的斜率图、箱线+散点或效应量森林图;"
           "方法×指标改热力矩阵;参数影响改龙卷风图或响应曲面")
    for task, names in sorted(by_task.items()):
        if len(names) > BAR_PER_TASK:
            out.append((task, "error",
                        f"{task} 有 {len(names)} 张柱状图({'、'.join(names)}),每个任务最多 {BAR_PER_TASK} 张。"
                        f"\n    换图种:{alt}。"))
    if len(data_figs) >= BAR_SHARE_MIN_FIGS and len(bars) / len(data_figs) > BAR_SHARE_MAX:
        out.append(("全篇", "error",
                    f"全篇 {len(data_figs)} 张数据图里 {len(bars)} 张是柱状图({len(bars) / len(data_figs):.0%}),"
                    f"上限 {BAR_SHARE_MAX:.0%}。\n    换图种:{alt}。"))
    return out


def collect() -> dict:
    """按图名(stem)汇总:每张图的问题清单与是否做过自检。"""
    records = {}
    if os.path.isfile(LINT):
        try:
            with open(LINT, encoding="utf-8") as f:
                records = (json.load(f) or {}).get("figures") or {}
        except (OSError, ValueError):
            records = {}

    out: dict[str, dict] = {}
    selected: dict[str, tuple[float, int]] = {}
    if not os.path.isdir(FIGDIR):
        return out
    # 有体检记录的 stem 不按前缀跳过；同一 stem 的矢量判据只算一次
    _stem_records = {os.path.splitext(n)[0] for n in records}
    _vec_cache: dict[str, list] = {}
    for name in sorted(os.listdir(FIGDIR)):
        stem, ext = os.path.splitext(name)
        # 旧版存图留下的 x.png.png 与 x.png 是同一张图
        while os.path.splitext(stem)[1].lower() in EXTS + (".jpg", ".jpeg"):
            stem = os.path.splitext(stem)[0]
        if ext.lower() not in EXTS or _skip(stem, stem in _stem_records):
            continue
        rec = records.get(name)
        out.setdefault(stem, {"issues": [], "checked": False,
                              "data": {}, "series": {}})
        # 矢量版判据与体检记录无关：没跑过 plot_style 的 data_*.pdf 也要查，
        # 否则「无 lint 记录 → continue」会把假 PDF 一起放过去；同一 stem 只算一次
        if stem not in _vec_cache:
            _vec_cache[stem] = _vector_issues(stem)
        vec = _vec_cache[stem]
        if not isinstance(rec, dict):
            out[stem]["issues"].extend(vec)
            continue
        # 同一张图常同时存 PNG/PDF/SVG。旧实现把各后缀 issues 做并集:
        # 只重存 PNG 后,旧 PDF 的历史硬伤仍会阴魂不散。按 checked_at 选最新记录,
        # 时间相同则优先用户实际预览的 PNG,整条记录一起替换。
        priority = (
            float(rec.get("checked_at") or 0.0),
            {".png": 3, ".svg": 2, ".pdf": 1}.get(ext.lower(), 0))
        if priority < selected.get(stem, (-1.0, -1)):
            continue
        selected[stem] = priority
        out[stem] = {
            "issues": vec + list(rec.get("issues") or []),
            "checked": True,
            "data": dict(rec.get("data") or {}),
            "series": dict(rec.get("series") or {}),
        }
        # 「有体检记录」不等于「按规范存的」：裸 plt.savefig 也会写记录。
        if rec.get("saved_by") == "savefig":
            out[stem]["issues"].append({
                "level": "warn", "code": "raw_savefig", "panel": "",
                "msg": "未经 save_publication 存图：没有矢量版、也没走 tidy 收尾；改成 save_publication(fig, stem)"})
    return out


def _vector_issues(stem: str) -> list:
    """数据图必须有真矢量版：只 isfile 不够，PNG 改后缀、手写 %PDF- 头都要挡。"""
    if not stem.startswith("data_"):
        return []
    pdf_path = os.path.join(FIGDIR, stem + ".pdf")
    if not os.path.isfile(pdf_path):
        return [{"level": "error", "code": "no_vector_copy", "panel": "",
                 "msg": "只有位图，没有同名 .pdf；save_publication 会同时出 png/pdf/svg"}]
    try:
        with open(pdf_path, "rb") as fh:
            head = fh.read(5)
    except OSError:
        return []
    if head != b"%PDF-":
        return [{"level": "error", "code": "no_vector_copy", "panel": "",
                 "msg": "同名 .pdf 的文件头不是 %PDF-（多半是把 PNG 改了后缀），不是真矢量版"}]
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []
    try:
        with fitz.open(pdf_path) as doc:
            if doc.page_count < 1:
                return [{"level": "error", "code": "no_vector_copy", "panel": "",
                         "msg": "同名 .pdf 没有页面（伪造文件头），不是真矢量版"}]
            pg = doc[0]
            if not (pg.get_text().strip() or pg.get_drawings() or pg.get_images()):
                return [{"level": "error", "code": "no_vector_copy", "panel": "",
                         "msg": "同名 .pdf 是空白页（无文字/无图形/无图像），不是真矢量版"}]
    except Exception:  # noqa: BLE001
        return [{"level": "error", "code": "no_vector_copy", "panel": "",
                 "msg": "同名 .pdf 打不开，不是真矢量版"}]
    return []


def main() -> int:
    # GBK 控制台遇到 m²、✅ 这类字符会让 print 直接抛 UnicodeEncodeError 把闸门打挂
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="结果图闸门")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--final", action="store_true", help="终审口径:全部 error 都算硬伤")
    ap.add_argument("--version", action="version",
                    version=f"check_figures {GATE_VERSION}")
    ap.add_argument("--root", default="",
                    help="工程根(含 figures/ 的那一层);默认按当前目录向上自动找")
    args = ap.parse_args()
    global ROOT, FIGDIR, LINT
    if args.root:
        ROOT = os.path.abspath(args.root)
        FIGDIR = os.path.join(ROOT, "figures")
        LINT = os.path.join(FIGDIR, "_figure_lint.json")

    def _die(msg: str, code: int = 2) -> int:
        """体检不到任何东西 ≠ 通过:闸门必须打出来,否则等于没跑。"""
        if args.json:
            print(json.dumps({"ok": False, "reason": msg, "root": ROOT, "figdir": FIGDIR,
                              "cwd": os.getcwd()}, ensure_ascii=False, indent=1))
        else:
            print(f"[闸门未执行] {msg}", file=sys.stderr)
            print(f"    工程根：{ROOT}", file=sys.stderr)
            print(f"    体检目录：{FIGDIR}", file=sys.stderr)
            print(f"    当前目录：{os.getcwd()}", file=sys.stderr)
            print("    在工程根（含 figures/ 的那一层）下运行，或用 --root 指定。", file=sys.stderr)
        return code

    if not os.path.isdir(ROOT):
        return _die(f"工程根不存在：{ROOT}")
    if not os.path.isdir(FIGDIR):
        return _die("找不到 figures/ 目录——这次没体检任何图，不能算通过")
    final = (args.final or os.environ.get("MS_FIG_STAGE", "").strip().lower() == "final"
             or os.path.isfile(os.path.join(FIGDIR, ".final_stage")))

    def grade(issue) -> str:
        if issue.get("level") != "error":
            return "提醒"
        return "硬伤" if final or issue.get("code") in DESIGN_HARD else "终审"

    figs = collect()
    errors = warns = deferred = 0
    unchecked = []
    for stem, item in figs.items():
        for i in item["issues"]:
            g = grade(i)
            errors += g == "硬伤"
            deferred += g == "终审"
            warns += g == "提醒"
        if not item["checked"]:
            unchecked.append(stem)
    dups = duplicates(figs)
    errors += len(dups)
    clashes = color_conflicts(figs)
    if final:
        errors += len(clashes)
    else:
        deferred += len(clashes)
    thin = low_information(figs)
    for _s, lv, _m in thin:
        if lv != "error":
            warns += 1
        elif final:
            errors += 1
        else:
            deferred += 1
    heavy = bar_heavy(figs)
    for _s, lv, _m in heavy:
        if lv != "error":
            warns += 1
        elif final:
            errors += 1
        else:
            deferred += 1
    missing_kinds = unused_advanced_kinds(figs)
    warns += len(missing_kinds)
    missing_plan = unused_plan_kinds(figs, final, skip={k for k, _t in missing_kinds})
    warns += len(missing_plan)

    if args.json:
        print(json.dumps({"ok": errors == 0 and not unchecked and bool(figs),
                          "reason": "" if figs else "figures/ 下没有需要体检的结果图",
                          "root": ROOT, "figdir": FIGDIR,
                          "errors": errors, "warns": warns, "deferred": deferred,
                          "stage": "final" if final else "design",
                          "unchecked": unchecked, "duplicates": dups,
                          "color_conflicts": clashes,
                          "low_information": [{"figure": s, "level": lv, "msg": m} for s, lv, m in thin],
                          "bar_heavy": [{"scope": s, "level": lv, "msg": m} for s, lv, m in heavy],
                          "unused_advanced_kinds": [k for k, _t in missing_kinds],
                          "unused_plan_kinds": [{"task": t, "kinds": ks} for t, ks in missing_plan],
                          "figures": figs},
                         ensure_ascii=False, indent=1))
        if not figs:
            return 2
        return 0 if (errors == 0 and not unchecked) else 1

    if not figs:
        return _die("figures/ 下没有需要体检的结果图——这次没体检到任何图，不能算通过"
                    "（还没出图属正常，出图后再跑；目录不对见上面的「体检目录」）")
    # 先亮明这次到底看了哪个目录:路径报错时人一眼能看出脚本在替谁体检
    print(f"体检目录:{FIGDIR}")
    # 标记只用 GBK 也能编码的字符:控制台不是 UTF-8 时,✓/✗ 会让整个脚本崩在 print 上
    order = {"硬伤": 0, "终审": 1, "提醒": 2}
    for stem, item in figs.items():
        if not item["checked"]:
            print(f"[未自检] {stem}:请用 plot_style.apply() 后重新出图")
            for i in item["issues"]:
                print(f"    [{grade(i)}] {i.get('panel', '')}{i.get('msg', '')}")
            continue
        if not item["issues"]:
            print(f"[通过] {stem}")
            continue
        worst = min((grade(i) for i in item["issues"]), key=order.get)
        print(f"[{worst}] {stem}")
        for i in item["issues"]:
            print(f"    [{grade(i)}] {i.get('panel', '')}{i.get('msg', '')}")

    for stem, level, msg in thin + heavy:
        mark = "提醒" if level != "error" else ("硬伤" if final else "终审")
        print(f"[{mark}] {stem}")
        print(f"    [{mark}] {msg}")

    if missing_kinds:
        names = "、".join(k for k, _t in missing_kinds)
        print(f"[提醒] 用户勾选的高级图种一张都没用上:{names}")
        print("    [提醒] 这是开题向导里明确勾的硬性偏好。凡数据支持就该优先采用;"
              "本题数据确实不匹配,要在实验纪要里写一句原因,不能默默用柱状图替代。"
              "照模板改的图要保留模板里的 fig.set_gid(\"ms-kind:…\"),自己画的调 plot_style.mark_kind(fig, \"图种\"),"
              "否则认不出你用了哪种图。")

    if missing_plan:
        names = "；".join(f"{t}(可用:{'、'.join(ks)})" for t, ks in missing_plan)
        print(f"[提醒] 研究方案里的图还没画:{names}")
        print("    [提醒] 作者在方案页勾选的图每张都要画;没勾选的任务至少挑一种数据撑得起的候选。"
              "方案文本写了每张证明什么、画哪份数据、怎么画,照 figure-templates 里对应模板改造并保留 "
              "fig.set_gid(\"ms-kind:…\")。确实撑不起就换成「也可画成」里的画法,在实验纪要里写一句原因,"
              "不要退回成柱状图。")

    for d in dups:
        print(f"[硬伤] {d['a']} 与 {d['b']} 画的是同一批数据"
              f"(取值重合 {d['overlap']:.0%})")
        print("    [硬伤] 同一组数换个图型再画一遍算重复,不算两张图:"
              "合成一张 (a)(b) 多面板并删掉多余那张,或只留信息量大的那张")

    cmark = "硬伤" if final else "终审"
    for c in clashes:
        where = "；".join(
            f"{col} 用在 {'、'.join(stems)}" for col, stems in c["where"])
        print(f"[{cmark}] 「{c['label']}」在不同图里换了颜色:{where}")
        print(f"    [{cmark}] 同一个量全篇必须同一种颜色,读者翻到第二张会以为是另一个量:"
              "改成 `ax.plot(x, y, label=名, **plot_style.series_style(名))`"
              "(只要颜色用 `plot_style.series_color(名)`),别写 PALETTE[下标]——"
              "各脚本各排各的序,同一个量的下标对不上")

    print(f"\n合计:{len(figs)} 张图 · 硬伤 {errors} · 终审处理 {deferred} · 提醒 {warns}"
          + (f" · 重复 {len(dups)} 对" if dups else "")
          + (f" · 换色 {len(clashes)} 个量" if clashes else "")
          + (f" · 未自检 {len(unchecked)}" if unchecked else ""))
    if errors or unchecked:
        print("硬伤必须改到 0 才算完成:按上面每条的建议改绘图代码并重跑脚本。")
        return 1
    if deferred:
        print("没有硬伤。标「终审」的是版式问题,现在可以不改:配图终审会统一重出图并按一区标准升级。")
        return 0
    print("图面自检通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
