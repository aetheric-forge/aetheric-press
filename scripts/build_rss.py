#!/usr/bin/env python3
import os, re, sys, hashlib, datetime, email.utils, xml.sax.saxutils as esc
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"
CFG = yaml.safe_load((ROOT / "config.yml").read_text())

FM_RE = re.compile(r"^\ufeff?\s*---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

def _parse_date_any(s: str):
    """Try ISO first; if it's just a date, add midnight; accept ' ' instead of 'T'."""
    s = s.strip()
    try:
        return datetime.datetime.fromisoformat(s.replace(" ", "T"))
    except Exception:
        # bare YYYY-MM-DD?
        try:
            return datetime.datetime.fromisoformat(s + "T00:00:00")
        except Exception:
            return None

def parse_article(p: Path):
    txt = p.read_text(encoding="utf-8")
    m = FM_RE.match(txt)
    if not m:
        print(f"[genrss] skip (no front-matter match): {p}", file=sys.stderr)
        return None

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        print(f"[genrss] skip (YAML error {e!r}): {p}", file=sys.stderr)
        return None

    if fm.get("draft", False):
        print(f"[genrss] skip (draft=true): {p}", file=sys.stderr)
        return None

    if "title" not in fm:
        print(f"[genrss] skip (missing title): {p}", file=sys.stderr)
        return None

    if "date" not in fm:
        print(f"[genrss] skip (missing date): {p}", file=sys.stderr)
        return None

    dt = _parse_date_any(str(fm["date"]))
    if not dt:
        print(f"[genrss] skip (unparsable date: {fm['date']}): {p}", file=sys.stderr)
        return None

    # Build URL
    base_url = CFG["base_url"].rstrip("/")
    slug = (fm.get("slug") or p.stem).strip()
    url = f"{base_url}/{slug}.html"

    # Summaries and tags are optional
    summary = (fm.get("summary") or "").strip()
    tags = fm.get("tags") or []

    return {
        "path": p,
        "title": fm["title"],
        "date": dt,
        "rfc822": email.utils.format_datetime(dt.astimezone()),
        "author": fm.get("author", CFG.get("author", "Valkyr")),
        "summary": summary[:500],
        "tags": tags,
        "url": url,
        "guid": hashlib.sha1(url.encode()).hexdigest(),
        "persona": fm.get("persona"),
    }

def gen_rss(items):
    now = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<rss version="2.0">')
    out.append("<channel>")
    out.append(f"<title>{esc.escape(CFG['feed']['title'])}</title>")
    out.append(f"<link>{esc.escape(CFG['base_url'])}</link>")
    out.append(f"<description>{esc.escape(CFG['feed']['description'])}</description>")
    out.append(f"<language>{CFG['feed'].get('language','en')}</language>")
    out.append(f"<lastBuildDate>{now}</lastBuildDate>")
    for it in items:
        out.append("<item>")
        out.append(f"<title>{esc.escape(it['title'])}</title>")
        out.append(f"<link>{esc.escape(it['url'])}</link>")
        out.append(f"<guid isPermaLink='false'>{it['guid']}</guid>")
        out.append(f"<pubDate>{it['rfc822']}</pubDate>")
        if it["summary"]:
            out.append(f"<description>{esc.escape(it['summary'])}</description>")
        for tag in it["tags"]:
            out.append(f"<category>{esc.escape(tag)}</category>")
        out.append("</item>")
    out.append("</channel></rss>")
    return "\n".join(out)

def iter_markdown(root: Path):
    # robust: recursive, case-insensitive, files only
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".md":
            yield p

def main():
    items = []
    found = 0
    for p in sorted(iter_markdown(ARTICLES)):
        found += 1
        item = parse_article(p)
        if item:
            items.append(item)
    if found == 0:
        print(f"[genrss] No .md files found under {ARTICLES.resolve()}", file=sys.stderr)
    else:
        print(f"[genrss] Discovered {found} .md files; {len(items)} publishable", file=sys.stderr)
    items.sort(key=lambda x: x["date"], reverse=True)
    rss = gen_rss(items)
    (ROOT / "feed.xml").write_text(rss, encoding="utf-8")
    # lightweight index for humans
    idx_lines = [f"# {CFG['site_title']}\n\n_{CFG['site_subtitle']}_\n\n## Latest\n"]
    for it in items:
        idx_lines.append(f"- **{it['date'].date()}** — [{it['title']}]({it['url']}) — {it['summary']}")
    (ROOT / "index.md").write_text("\n".join(idx_lines), encoding="utf-8")

if __name__ == "__main__":
    sys.exit(main())
