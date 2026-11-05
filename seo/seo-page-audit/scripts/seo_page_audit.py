#!/usr/bin/env python3
"""On-page SEO audit for one URL or local HTML file. Python 3 stdlib only.

Usage:
  seo_page_audit.py https://example.com/page [--json]
  seo_page_audit.py page.html [--json]
  seo_page_audit.py --selftest
Exit code: 0 no high-priority issue, 1 at least one high issue, 2 fetch/usage error.
"""
import argparse
import json
import re
import sys
import threading
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; seo-page-audit/1.0)"
HEAD_RE = re.compile(r"h[1-6]")


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.canonical = None
        self.lang = None
        self.headings = []
        self._h = None
        self._htxt = []
        self.links = []
        self._cur_a = None
        self.images = []
        self.jsonld = 0
        self.text = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang") or None
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href", "")
        elif HEAD_RE.fullmatch(tag):
            self._h = int(tag[1])
            self._htxt = []
        elif tag == "a" and "href" in a:
            self._cur_a = {"href": a["href"], "text": ""}
            self.links.append(self._cur_a)
        elif tag == "img":
            self.images.append({
                "src": a.get("src", ""),
                "alt": a.get("alt"),
                "has_dims": bool(a.get("width") and a.get("height")),
            })
        elif tag == "script":
            self._skip += 1
            if a.get("type", "").lower() == "application/ld+json":
                self.jsonld += 1
        elif tag == "style":
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif HEAD_RE.fullmatch(tag) and self._h:
            self.headings.append((self._h, " ".join("".join(self._htxt).split())))
            self._h = None
        elif tag == "a":
            self._cur_a = None
        elif tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._h:
            self._htxt.append(data)
        if self._cur_a is not None:
            self._cur_a["text"] += data
        if not self._skip:
            self.text.append(data)


def fetch(target):
    if re.match(r"https?://", target):
        req = urllib.request.Request(target, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read(3_000_000)
            enc = r.headers.get_content_charset() or "utf-8"
            return raw.decode(enc, "replace"), r.geturl()
    with open(target, "rb") as f:
        return f.read().decode("utf-8", "replace"), None


def audit(html, base=None):
    p = Parser()
    p.feed(html)
    issues = []

    def add(prio, code, msg):
        issues.append({"priority": prio, "code": code, "message": msg})

    title = " ".join(p.title.split())
    if not title:
        add("high", "title-missing", "No <title> element.")
    elif len(title) > 60:
        add("medium", "title-long", f"Title is {len(title)} chars; may be truncated in results (aim for about 60 or fewer).")
    elif len(title) < 20:
        add("low", "title-short", f"Title is only {len(title)} chars.")

    desc = " ".join(p.meta.get("description", "").split())
    if not desc:
        add("high", "meta-description-missing", "No meta description.")
    elif len(desc) > 160:
        add("low", "meta-description-long", f"Meta description is {len(desc)} chars (aim for about 160 or fewer).")
    elif len(desc) < 70:
        add("low", "meta-description-short", f"Meta description is only {len(desc)} chars.")

    h1 = [t for lvl, t in p.headings if lvl == 1]
    if not h1:
        add("high", "h1-missing", "No <h1>.")
    elif len(h1) > 1:
        add("medium", "h1-multiple", f"{len(h1)} <h1> elements; usually one is clearer.")
    elif not h1[0]:
        add("high", "h1-empty", "The <h1> is empty.")
    prev = 0
    for lvl, _ in p.headings:
        if prev and lvl > prev + 1:
            add("low", "heading-skip", f"Heading level jumps from h{prev} to h{lvl}.")
            break
        prev = lvl

    if not p.canonical:
        add("medium", "canonical-missing", "No rel=canonical link.")
    if not p.lang:
        add("medium", "lang-missing", "<html> has no lang attribute.")
    if "viewport" not in p.meta:
        add("medium", "viewport-missing", "No meta viewport (mobile rendering).")
    if "noindex" in p.meta.get("robots", "").lower():
        add("high", "noindex", "Page has robots noindex: it will not be indexed.")
    if not any(k.startswith("og:") for k in p.meta):
        add("low", "og-missing", "No Open Graph tags (link previews).")

    noalt = [i["src"] for i in p.images if i["alt"] is None]
    if noalt:
        add("medium", "img-alt-missing", f"{len(noalt)} of {len(p.images)} images have no alt attribute (first: {noalt[0][:60]}).")
    nodims = [i for i in p.images if not i["has_dims"]]
    if nodims:
        add("low", "img-dimensions", f"{len(nodims)} images lack width/height (layout shift).")

    host = urlparse(base).netloc if base else None
    internal = external = empty_anchor = 0
    for lk in p.links:
        href = lk["href"].strip()
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        net = urlparse(urljoin(base or "", href)).netloc
        if host and net and net != host:
            external += 1
        else:
            internal += 1
        if not " ".join(lk["text"].split()):
            empty_anchor += 1
    if empty_anchor:
        add("low", "link-empty-text", f"{empty_anchor} links have no visible text (check aria-label or image alt).")
    if not internal:
        add("medium", "no-internal-links", "No internal links found.")

    words = len(re.findall(r"\w+", " ".join(p.text)))
    if words < 300:
        add("medium", "thin-content", f"About {words} words of visible text; may be thin for a content page.")

    order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: order[i["priority"]])
    return {
        "title": title, "title_length": len(title), "meta_description_length": len(desc),
        "h1": h1, "headings": len(p.headings), "words": words,
        "images": len(p.images), "links_internal": internal, "links_external": external,
        "canonical": p.canonical, "lang": p.lang, "structured_data_blocks": p.jsonld,
        "issues": issues,
    }


def render(r):
    out = [
        f"Title ({r['title_length']}): {r['title'] or '-'}",
        f"H1: {r['h1'] or '-'} | headings: {r['headings']} | words: {r['words']}",
        f"Images: {r['images']} | links internal/external: {r['links_internal']}/{r['links_external']} | JSON-LD blocks: {r['structured_data_blocks']}",
        "",
    ]
    if not r["issues"]:
        out.append("No issues found.")
    for i in r["issues"]:
        out.append(f"[{i['priority'].upper():6}] {i['code']}: {i['message']}")
    return "\n".join(out)


BAD = "<html><head><title>Hi</title></head><body><h2>Sub</h2><img src='a.png'><a href='/x'></a><p>short</p></body></html>"
GOOD = (
    "<html lang='en'><head><title>A reasonably descriptive page title here</title>"
    "<meta name='description' content='A clear summary of the page that is long enough to be useful in search results.'>"
    "<meta name='viewport' content='width=device-width'><meta property='og:title' content='x'>"
    "<link rel='canonical' href='https://example.com/p'></head><body><h1>Main</h1><h2>Part</h2>"
    "<img src='a.png' alt='A' width='1' height='1'><a href='/more'>More</a><p>" + "word " * 320 + "</p></body></html>"
)


def selftest():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    bad = {i["code"] for i in audit(BAD, "https://example.com/")["issues"]}
    for c in ("title-short", "meta-description-missing", "h1-missing", "canonical-missing", "lang-missing",
              "viewport-missing", "img-alt-missing", "link-empty-text", "thin-content"):
        assert c in bad, f"expected {c} in {sorted(bad)}"
    good = audit(GOOD, "https://example.com/p")
    assert not [i for i in good["issues"] if i["priority"] in ("high", "medium")], good["issues"]
    ni = audit("<html><head><meta name='robots' content='noindex'></head></html>")
    assert any(i["code"] == "noindex" for i in ni["issues"])

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(BAD.encode())

        def log_message(self, *args):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    html, final = fetch(f"http://127.0.0.1:{srv.server_port}/")
    assert audit(html, final)["h1"] == [] and final.startswith("http://127.0.0.1")
    srv.shutdown()
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.target:
        ap.print_usage()
        sys.exit(2)
    try:
        html, base = fetch(a.target)
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"error: cannot load {a.target}: {e}", file=sys.stderr)
        sys.exit(2)
    r = audit(html, base)
    print(json.dumps(r, indent=2, ensure_ascii=False) if a.json else render(r))
    sys.exit(1 if any(i["priority"] == "high" for i in r["issues"]) else 0)


if __name__ == "__main__":
    main()
