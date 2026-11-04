#!/usr/bin/env python3
"""论文搜索：Crossref + arXiv 双源，OpenAlex / Semantic Scholar 可选。

无 API Key；带缓存、限速、退避、去重、GB/T 7714 / APA 输出。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

CACHE_VERSION = 1
DEFAULT_TIMEOUT = 30
USER_AGENT = "math-modeling-pro/2.1 (paper_search; mailto:test@example.com)"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


@dataclass
class Paper:
    title: str
    authors: list[str]
    year: int | None
    venue: str
    doi: str
    url: str
    abstract: str
    citation_count: int
    source: str
    verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cache_key(source: str, query: str, limit: int, year_from: int | None, year_to: int | None) -> str:
    raw = json.dumps([CACHE_VERSION, source, query, limit, year_from, year_to], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def read_cache(cache_dir: Path, key: str, ttl_days: int = 7) -> dict | None:
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_days * 86400:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_cache(cache_dir: Path, key: str, data: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"{key}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def http_get(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = 2) -> bytes | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  429 限流，{wait}s 后重试：{url[:80]}", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTP {exc.code}：{url[:100]}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"  请求失败：{exc}", file=sys.stderr)
            time.sleep(1)
    return None


def crossref(query: str, limit: int, year_from: int | None, year_to: int | None, timeout: int) -> list[Paper]:
    params = {
        "query.bibliographic": query,
        "rows": str(limit),
        "select": "DOI,title,author,issued,container-title,abstract,is-referenced-by-count,URL,type",
    }
    if year_from or year_to:
        filters = []
        if year_from:
            filters.append(f"from-pub-date:{year_from}")
        if year_to:
            filters.append(f"until-pub-date:{year_to}")
        params["filter"] = ",".join(filters)
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    body = http_get(url, timeout=timeout)
    if body is None:
        return []
    try:
        items = json.loads(body)["message"]["items"]
    except Exception:
        return []
    papers = []
    for item in items:
        authors = []
        for author in item.get("author", []):
            name = " ".join(x for x in (author.get("given"), author.get("family")) if x)
            if name:
                authors.append(name)
        year = None
        parts = item.get("issued", {}).get("date-parts", [[None]])
        if parts and parts[0]:
            year = parts[0][0]
        doi = item.get("DOI", "")
        papers.append(Paper(
            title=clean(" ".join(item.get("title", []))),
            authors=authors,
            year=year,
            venue=clean(" ".join(item.get("container-title", []))),
            doi=doi,
            url=item.get("URL", "") or (f"https://doi.org/{doi}" if doi else ""),
            abstract=clean(item.get("abstract", ""))[:1200],
            citation_count=int(item.get("is-referenced-by-count", 0) or 0),
            source="crossref",
        ))
    return papers


def arxiv(query: str, limit: int, year_from: int | None, year_to: int | None, timeout: int) -> list[Paper]:
    search = f'all:"{query}"'
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": search,
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    body = http_get(url, timeout=timeout)
    if body is None:
        return []
    try:
        root = ET.fromstring(body)
    except Exception:
        return []
    papers = []
    for entry in root.findall("a:entry", ATOM):
        title = clean(" ".join((entry.findtext("a:title", "", ATOM) or "").split()))
        summary = clean(entry.findtext("a:summary", "", ATOM))[:1200]
        published = entry.findtext("a:published", "", ATOM)
        year = int(published[:4]) if published[:4].isdigit() else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        authors = [
            clean(a.findtext("a:name", "", ATOM))
            for a in entry.findall("a:author", ATOM)
        ]
        link = entry.findtext("a:id", "", ATOM)
        doi = ""
        for ext in entry.findall("{http://arxiv.org/schemas/atom}doi"):
            doi = ext.text or ""
        papers.append(Paper(
            title=title,
            authors=[a for a in authors if a],
            year=year,
            venue="arXiv",
            doi=doi,
            url=link,
            abstract=summary,
            citation_count=0,
            source="arxiv",
        ))
    return papers


def openalex(query: str, limit: int, year_from: int | None, year_to: int | None, timeout: int, email: str | None) -> list[Paper]:
    params = {
        "search": query,
        "per_page": str(limit),
        "select": "display_name,authorships,publication_year,doi,cited_by_count,abstract_inverted_index,primary_location",
    }
    if email:
        params["mailto"] = email
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    body = http_get(url, timeout=timeout)
    if body is None:
        return []
    try:
        items = json.loads(body).get("results", [])
    except Exception:
        return []
    papers = []
    for item in items:
        year = item.get("publication_year")
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        index = item.get("abstract_inverted_index") or {}
        words: list[tuple[int, str]] = []
        for word, positions in index.items():
            for pos in positions:
                words.append((pos, word))
        abstract = clean(" ".join(w for _, w in sorted(words)))[:1200]
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships", [])
        ]
        doi = (item.get("doi") or "").replace("https://doi.org/", "")
        loc = item.get("primary_location") or {}
        source = loc.get("source") or {}
        papers.append(Paper(
            title=clean(item.get("display_name", "")),
            authors=[a for a in authors if a],
            year=year,
            venue=clean(source.get("display_name", "")),
            doi=doi,
            url=item.get("doi", "") or "",
            abstract=abstract,
            citation_count=int(item.get("cited_by_count", 0) or 0),
            source="openalex",
        ))
    return papers


def semantic_scholar(query: str, limit: int, year_from: int | None, year_to: int | None, timeout: int) -> list[Paper]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,venue,abstract,citationCount,externalIds,url",
    })
    body = http_get(url, timeout=timeout)
    if body is None:
        return []
    try:
        items = json.loads(body).get("data", [])
    except Exception:
        return []
    papers = []
    for item in items:
        year = item.get("year")
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        external = item.get("externalIds") or {}
        papers.append(Paper(
            title=clean(item.get("title", "")),
            authors=[a.get("name", "") for a in item.get("authors", []) if a.get("name")],
            year=year,
            venue=clean(item.get("venue", "")),
            doi=external.get("DOI", "") or "",
            url=item.get("url", "") or "",
            abstract=clean(item.get("abstract", ""))[:1200],
            citation_count=int(item.get("citationCount", 0) or 0),
            source="s2",
        ))
    return papers


def dedupe(papers: Iterable[Paper]) -> list[Paper]:
    seen: set[str] = set()
    out = []
    for paper in papers:
        key = (paper.doi or "").lower().strip() or re.sub(r"\W+", "", paper.title.lower())[:80]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(paper)
    return out


def verify_doi(paper: Paper, timeout: int) -> Paper:
    if not paper.doi:
        return paper
    url = "https://api.crossref.org/works/" + urllib.parse.quote(paper.doi)
    body = http_get(url, timeout=timeout, retries=1)
    if body:
        try:
            data = json.loads(body)["message"]
            if data.get("DOI"):
                paper.verified = True
        except Exception:
            pass
    return paper


def format_authors(authors: list[str], max_n: int = 3) -> str:
    if not authors:
        return "Unknown"
    shown = authors[:max_n]
    text = ", ".join(shown)
    if len(authors) > max_n:
        text += ", et al."
    return text


def format_gbt(paper: Paper) -> str:
    authors = format_authors(paper.authors)
    kind = "J" if paper.source in {"crossref", "openalex", "s2"} else "EB/OL"
    year = paper.year or "n.d."
    venue = f". {paper.venue}" if paper.venue else ""
    doi = f". DOI: {paper.doi}" if paper.doi else ""
    url = f". {paper.url}" if paper.url and not paper.doi else ""
    return f"{authors}. {paper.title}[{kind}]{venue}, {year}{doi}{url}."


def format_apa(paper: Paper) -> str:
    authors = format_authors(paper.authors)
    year = f"({paper.year})" if paper.year else "(n.d.)"
    venue = f" {paper.venue}." if paper.venue else ""
    doi = f" https://doi.org/{paper.doi}" if paper.doi else (f" {paper.url}" if paper.url else "")
    return f"{authors} {year}. {paper.title}.{venue}{doi}".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="数学建模论文搜索")
    parser.add_argument("query", help="关键词/标题")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--source", default="auto", choices=["auto", "crossref", "arxiv", "openalex", "s2"])
    parser.add_argument("--format", default="markdown", choices=["json", "markdown", "gbt7714", "apa"])
    parser.add_argument("--year-from", type=int)
    parser.add_argument("--year-to", type=int)
    parser.add_argument("--verify-doi", action="store_true")
    parser.add_argument("--cache-dir", default=str(Path(__file__).resolve().parent.parent / ".cache"))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--email", help="OpenAlex 礼貌池邮箱（可选）")
    parser.add_argument("--out", help="输出到文件")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    key = cache_key(args.source, args.query, args.limit, args.year_from, args.year_to)
    data = None if args.no_cache else read_cache(cache_dir, key)
    if data:
        papers = [Paper(**item) for item in data.get("papers", [])]
        print(f"（缓存命中：{len(papers)} 条）", file=sys.stderr)
    else:
        sources = []
        if args.source == "auto":
            sources = ["crossref", "arxiv", "openalex", "s2"]
        else:
            sources = [args.source]
        collected: list[Paper] = []
        for source in sources:
            if len(dedupe(collected)) >= args.limit and args.source == "auto":
                break
            try:
                if source == "crossref":
                    batch = crossref(args.query, args.limit, args.year_from, args.year_to, args.timeout)
                elif source == "arxiv":
                    batch = arxiv(args.query, args.limit, args.year_from, args.year_to, args.timeout)
                elif source == "openalex":
                    batch = openalex(args.query, args.limit, args.year_from, args.year_to, args.timeout, args.email)
                elif source == "s2":
                    batch = semantic_scholar(args.query, args.limit, args.year_from, args.year_to, args.timeout)
                else:
                    batch = []
            except Exception as exc:
                print(f"  {source} 失败：{exc}", file=sys.stderr)
                batch = []
            if batch:
                print(f"  {source}: {len(batch)} 条", file=sys.stderr)
                collected.extend(batch)
            time.sleep(1.0)
        papers = dedupe(collected)[: args.limit]
        if args.verify_doi:
            papers = [verify_doi(p, args.timeout) for p in papers]
            time.sleep(1.0)
        write_cache(cache_dir, key, {"papers": [p.to_dict() for p in papers]})

    if args.format == "json":
        text = json.dumps([p.to_dict() for p in papers], ensure_ascii=False, indent=2)
    elif args.format == "gbt7714":
        text = "\n".join(f"[{i + 1}] {format_gbt(p)}" for i, p in enumerate(papers))
    elif args.format == "apa":
        text = "\n".join(format_apa(p) for p in papers)
    else:
        lines = ["| # | 标题 | 作者 | 年份 | 来源 | DOI/URL |", "|---|---|---|---|---|---|"]
        for i, p in enumerate(papers, 1):
            link = f"https://doi.org/{p.doi}" if p.doi else p.url
            lines.append(
                f"| {i} | {p.title.replace('|', ' ')} | {format_authors(p.authors)} | "
                f"{p.year or ''} | {p.source} | {link} |"
            )
        text = "\n".join(lines)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print(text)
    return 0 if papers else 1


if __name__ == "__main__":
    raise SystemExit(main())
