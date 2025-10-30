#!/usr/bin/env python3
import os, re, sys, hashlib, datetime, email.utils, xml.sax.saxutils as esc
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"
CFG = yaml.safe_load((ROOT / "config.yml").read_text())

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def parse_article(p: Path):
    text = p.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    if fm.get("draft", False):
        return None
    body = text[m.end():].strip()
    # compute absolute URL
    slug = fm.get("slug") or p.stem
    url = f"{CFG['base_url'].rstrip('/')}/{slug}.html"
    dt = datetime.datetime.fromisoformat(str(fm["date"]))
    return {
        "path": p,
        "title": fm["title"],
        "date": dt,
        "rfc822": email.utils.format_datetime(dt.astimezone()),
        "author": fm.get("author", CFG["author"]),
        "summary": fm.get("summary", "")[:500],
        "tags": fm.get("tags", []),
        "url": url,
        "guid": hashlib.sha1(url.encode()).hexdigest(),
        "body": body
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

def main():
    items = []
    for p in sorted(ARTICLES.glob("*.md")):
        item = parse_article(p)
        if item:
            items.append(item)
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
