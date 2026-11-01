#!/usr/bin/env python3
"""Check a website for broken URLs starting from its sitemap (stdlib only).

Usage:
  sitemap_check.py https://example.com/sitemap.xml [--links] [--max-urls N]
  sitemap_check.py --selftest
"""
import argparse, gzip, json, sys, threading, time
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

UA = "sitemap-link-checker/1.0 (+local script)"


def fetch(url, method="GET", timeout=15, max_bytes=2_000_000):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(max_bytes) if method == "GET" else b""
            return r.status, dict(r.headers), body, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b"", url
    except Exception as e:  # DNS, timeout, TLS...
        return None, {"error": type(e).__name__ + ": " + str(e)[:120]}, b"", url


def parse_sitemap(url, depth=0, seen=None):
    """Return list of page URLs; follows sitemap indexes and .gz files."""
    seen = seen if seen is not None else set()
    if url in seen or depth > 3:
        return []
    seen.add(url)
    status, _h, body, _u = fetch(url, max_bytes=50_000_000)
    if status != 200:
        raise SystemExit(f"cannot read sitemap {url}: status={status} {_h.get('error','')}")
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    root = ET.fromstring(body)
    tag = root.tag.split("}")[-1]
    locs = [e.text.strip() for e in root.iter() if e.tag.split("}")[-1] == "loc" and e.text]
    if tag == "sitemapindex":
        out = []
        for child in locs:
            out += parse_sitemap(child, depth + 1, seen)
        return out
    return locs


def check_url(url):
    """HEAD first; some servers reject HEAD (405/501/403) so retry with GET."""
    t0 = time.time()
    status, hdr, _b, final = fetch(url, "HEAD")
    if status is None or status in (403, 405, 501):
        status, hdr, _b, final = fetch(url, "GET")
    return {"url": url, "status": status, "final": final if final != url else None,
            "ms": int((time.time() - t0) * 1000), "error": hdr.get("error")}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def page_links(url):
    status, hdr, body, final = fetch(url)
    if status != 200 or "html" not in hdr.get("Content-Type", hdr.get("content-type", "html")):
        return []
    p = LinkParser()
    try:
        p.feed(body.decode("utf-8", "replace"))
    except Exception:
        return []
    out = []
    for h in p.links:
        h = h.strip()
        if h.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absu = urllib.parse.urldefrag(urllib.parse.urljoin(final, h))[0]
        if absu.startswith(("http://", "https://")):
            out.append(absu)
    return out


def run(sitemap, follow_links=False, max_urls=200, workers=8):
    pages = list(dict.fromkeys(parse_sitemap(sitemap)))[:max_urls]
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(check_url, pages))
        broken_links = []
        if follow_links:
            src_of = {}
            for page, links in zip(pages, ex.map(page_links, pages)):
                for l in links:
                    src_of.setdefault(l, set()).add(page)
            targets = [u for u in src_of if u not in set(pages)][: max_urls * 5]
            for r in ex.map(check_url, targets):
                if r["status"] is None or r["status"] >= 400:
                    r["found_on"] = sorted(src_of[r["url"]])[:3]
                    broken_links.append(r)
    bad = [r for r in results if r["status"] is None or r["status"] >= 400]
    redirects = [r for r in results if r["final"]]
    return {"sitemap": sitemap, "checked": len(results), "broken": bad,
            "redirected": redirects, "broken_outlinks": broken_links}


def selftest():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_HEAD(self): self.route(False)
        def do_GET(self): self.route(True)
        def route(self, body):
            base = f"http://127.0.0.1:{self.server.server_port}"
            p = self.path
            if p == "/sitemap.xml":
                data = (f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                        f'<url><loc>{base}/ok</loc></url><url><loc>{base}/missing</loc></url>'
                        f'<url><loc>{base}/old</loc></url></urlset>').encode()
                ctype, code = "application/xml", 200
            elif p == "/ok":
                data = b'<a href="/dead-link">x</a><a href="/ok">y</a>'; ctype, code = "text/html", 200
            elif p == "/old":
                self.send_response(301); self.send_header("Location", "/ok"); self.end_headers(); return
            else:
                data, ctype, code = b"nope", "text/plain", 404
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data))); self.end_headers()
            if body: self.wfile.write(data)
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    rep = run(f"http://127.0.0.1:{srv.server_port}/sitemap.xml", follow_links=True)
    srv.shutdown()
    assert rep["checked"] == 3, rep
    assert [b["url"].endswith("/missing") for b in rep["broken"]] == [True], rep
    assert len(rep["redirected"]) == 1, rep
    assert len(rep["broken_outlinks"]) == 1 and rep["broken_outlinks"][0]["url"].endswith("/dead-link"), rep
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sitemap", nargs="?")
    ap.add_argument("--links", action="store_true", help="also check outgoing links found on each page")
    ap.add_argument("--max-urls", type=int, default=200)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.sitemap:
        ap.error("sitemap URL required")
    rep = run(a.sitemap, a.links, a.max_urls, a.workers)
    if a.json:
        print(json.dumps(rep, indent=2)); sys.exit(1 if rep["broken"] or rep["broken_outlinks"] else 0)
    print(f"Checked {rep['checked']} sitemap URLs: {len(rep['broken'])} broken, {len(rep['redirected'])} redirected")
    for r in rep["broken"]:
        print(f"  BROKEN {r['status'] or 'ERR'} {r['url']} {r['error'] or ''}")
    for r in rep["redirected"]:
        print(f"  REDIRECT {r['status']} {r['url']} -> {r['final']}")
    for r in rep["broken_outlinks"]:
        print(f"  DEAD LINK {r['status'] or 'ERR'} {r['url']} (on {', '.join(r['found_on'])})")
    sys.exit(1 if rep["broken"] or rep["broken_outlinks"] else 0)


if __name__ == "__main__":
    main()
