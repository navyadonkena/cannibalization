#!/usr/bin/env python3
"""Check a blog topic idea against already-published posts to avoid keyword cannibalization.

    python cannibalization.py sync https://example.com/sitemap.xml --filter /blog/
    python cannibalization.py check "how to reduce churn in saas"

`sync` crawls the sitemap and stores each post's title, headings and description
in index.json. `check` shortlists the posts whose wording is closest to a topic
(no network needed). It does not decide cannibalization: that is a judgment on
keyword, topic and intent overlap, done per candidate (see the skill).
Standard library only.
"""
import argparse
import json
import math
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

INDEX_FILE = Path(__file__).with_name("index.json")

STOPWORDS = set(
    "a an and are as at be by for from how in into is it of on or that the this to "
    "what when where which who why with your you best top guide complete ultimate "
    "tips ways using use vs versus".split()
)


def tokens(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOPWORDS:
            continue
        for suffix in ("ing", "ed", "es", "s"):  # crude stemming: "reducing" ~ "reduce"
            if len(w) > len(suffix) + 3 and w.endswith(suffix):
                w = w[: -len(suffix)]
                break
        out.append(w)
    return out


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.description, self.headings = "", "", []
        self._tag = None

    def handle_starttag(self, tag, attrs):
        if tag in ("title", "h1", "h2", "h3"):
            self._tag = tag
            if tag != "title":
                self.headings.append("")
        elif tag == "meta":
            a = dict(attrs)
            if a.get("name", "").lower() == "description":
                self.description = a.get("content") or ""

    def handle_endtag(self, tag):
        if tag == self._tag:
            self._tag = None

    def handle_data(self, data):
        if self._tag == "title":
            self.title += data
        elif self._tag:
            self.headings[-1] += data


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cannibalization-checker/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def sitemap_urls(url):
    """Yield page URLs from a sitemap, following sitemap indexes."""
    root = ET.fromstring(fetch(url))
    locs = [e.text.strip() for e in root.iter() if e.tag.endswith("}loc") or e.tag == "loc"]
    if root.tag.endswith("sitemapindex"):
        for child in locs:
            yield from sitemap_urls(child)
    else:
        yield from locs


def cmd_sync(args):
    posts = []
    urls = [u for u in sitemap_urls(args.sitemap) if not args.filter or args.filter in u]
    for i, url in enumerate(urls, 1):
        try:
            p = PageParser()
            p.feed(fetch(url))
        except Exception as e:  # keep going; one bad page shouldn't kill the sync
            print(f"  skip {url}: {e}", file=sys.stderr)
            continue
        posts.append({
            "url": url,
            "title": p.title.strip(),
            "headings": [h.strip() for h in p.headings if h.strip()],
            "description": p.description.strip(),
        })
        print(f"[{i}/{len(urls)}] {url}", file=sys.stderr)
    INDEX_FILE.write_text(json.dumps(posts, indent=2))
    print(f"Indexed {len(posts)} posts -> {INDEX_FILE.name}")


def doc_weights(post):
    """Title and slug count most, then headings, then description."""
    slug = urlparse(post["url"]).path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
    c = Counter()
    for text, weight in ((post["title"], 3), (slug, 3), (" ".join(post["headings"]), 2),
                         (post["description"], 1)):
        for t in tokens(text):
            c[t] += weight
    return c


def score_topic(topic, posts):
    q = Counter(tokens(topic))
    if not q:
        sys.exit("Topic has no meaningful words after removing stopwords.")
    docs = [doc_weights(p) for p in posts]
    df = Counter(t for d in docs for t in d)
    n = len(docs)
    idf = lambda t: math.log((n + 1) / (df.get(t, 0) + 1)) + 1

    def vec(c):
        return {t: v * idf(t) for t, v in c.items()}

    qv = vec(q)
    qn = math.sqrt(sum(v * v for v in qv.values()))
    results = []
    for post, d in zip(posts, docs):
        dv = vec(d)
        dn = math.sqrt(sum(v * v for v in dv.values()))
        cosine = sum(v * dv.get(t, 0) for t, v in qv.items()) / (qn * dn) if dn else 0
        # How many of the topic's words already appear in the title/URL?
        head = set(tokens(post["title"])) | set(tokens(urlparse(post["url"]).path.replace("-", " ")))
        coverage = sum(1 for t in q if t in head) / len(q)
        results.append((0.5 * cosine + 0.5 * coverage, post))
    return sorted(results, key=lambda r: r[0], reverse=True)


def cmd_check(args):
    if not INDEX_FILE.exists():
        sys.exit("No index found. Run `sync` first.")
    posts = json.loads(INDEX_FILE.read_text())
    ranked = score_topic(args.topic, posts)[: args.top]
    print(f"Topic: {args.topic}")
    print("Shortlist by word overlap only. The score is NOT a cannibalization verdict:")
    print("judge each candidate on keyword, topic and intent overlap.\n")
    for score, p in ranked:
        print(f"  {score:.2f}  {p['title'] or p['url']}\n        {p['url']}")
        if args.details:
            if p["description"]:
                print(f"        description: {p['description']}")
            for h in p["headings"]:
                print(f"        - {h}")
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="crawl a sitemap and build the local index")
    s.add_argument("sitemap")
    s.add_argument("--filter", help="only index URLs containing this text, e.g. /blog/")
    s.set_defaults(fn=cmd_sync)
    c = sub.add_parser("check", help="check a topic against the index")
    c.add_argument("topic")
    c.add_argument("--top", type=int, default=5)
    c.add_argument("--details", action="store_true", help="also print each candidate's description and headings")
    c.set_defaults(fn=cmd_check)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
