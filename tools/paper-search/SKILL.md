---
name: paper-search
description: 数学建模论文搜索。用于“找参考文献 / 查算法原始论文 / 生成引用”等任务。默认 Crossref + arXiv 双源，无 API Key；OpenAlex / Semantic Scholar 可选；带缓存、限速、去重、DOI 校验。
---

# 论文搜索

## 设计

| 源 | 角色 | Key |
|---|---|---|
| Crossref | 元数据 / DOI 权威 | 不需要 |
| arXiv | 预印本发现 | 不需要 |
| OpenAlex | 可选增强（摘要/引用数） | 不需要（建议 mailto） |
| Semantic Scholar | 可选增强（相关性） | 可选 |

`auto` 顺序：Crossref → arXiv → OpenAlex → Semantic Scholar。某个源 429 时自动降级，不阻塞。

## 使用

```bash
python tools/paper-search/scripts/paper_search.py "grey prediction model" --limit 8
python tools/paper-search/scripts/paper_search.py "entropy weight TOPSIS" --format gbt7714
python tools/paper-search/scripts/paper_search.py "LSTM forecasting" --source arxiv --format json
```

参数：

| 参数 | 说明 |
|---|---|
| `--limit` | 返回条数，默认 8 |
| `--source` | `auto` / `crossref` / `arxiv` / `openalex` / `s2` |
| `--format` | `markdown` / `json` / `gbt7714` / `apa` |
| `--year-from` / `--year-to` | 年份过滤 |
| `--verify-doi` | 用 Crossref 校验 DOI |
| `--cache-dir` | 缓存目录，默认 `tools/paper-search/.cache/` |
| `--no-cache` | 跳过缓存 |
| `--email` | OpenAlex 礼貌池邮箱（可选） |
| `--out` | 写入文件 |

## 输出字段

`title`、`authors`、`year`、`venue`、`doi`、`url`、`abstract`、`citation_count`、`source`、`verified`。

## 规则

1. 只引用返回结果中真实存在、可校验的条目。
2. 有 DOI 优先用 DOI；没有 DOI 用 arXiv ID 或 URL。
3. 不编造作者、期刊、年份、DOI。
4. `verified=false` 的条目不得直接进论文。
5. 中文文献优先有 DOI 的期刊；无 DOI 的教材/标准单独标注。
6. 搜索结果是候选，不是综述；论文中只引用与论点直接相关的 5–15 篇。

## 缓存

- 目录：`tools/paper-search/.cache/`
- TTL：7 天
- key：source + query + limit + 年份过滤
- 429 时：指数退避（2s/4s/8s），仍失败则换源

## 实测

- OpenAlex / Semantic Scholar 在部分网络下会返回 429；Crossref / arXiv 可用。
- 因此默认双源 + 可选增强，不把任何单一 API 作为硬依赖。
