#!/usr/bin/env python3
"""Veille des blogs qui bloquent les serveurs (Cloudflare, erreur 403 avec blogwatcher-cli).

Récupère leur flux RSS par Firecrawl, qui passe par ses propres proxys, puis ajoute les nouveaux
articles dans la base de blogwatcher-cli (table `articles`, une ligne par URL) pour que
`blogwatcher-cli articles` les affiche avec les autres. Ne publie rien et n'envoie aucun e-mail.

Le blog doit déjà exister dans blogwatcher-cli (`blogwatcher-cli add "Nom" https://site`).
La clé est lue dans la variable FIRECRAWL_API_KEY, sinon dans ~/.hermes/.env.

Usage :
  veille_firecrawl.py --feed "Age of Product=https://age-of-product.com/feed/" [--feed ...] [--dry-run]
"""
import argparse, os, sys, re, json, sqlite3, urllib.request, urllib.error, html, datetime
from email.utils import parsedate_to_datetime

DB = os.path.expanduser("~/.blogwatcher-cli/blogwatcher-cli.db")
MAX_ITEMS = 15


def firecrawl_key():
    if os.environ.get("FIRECRAWL_API_KEY"):
        return os.environ["FIRECRAWL_API_KEY"].strip()
    env = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.startswith("FIRECRAWL_API_KEY="):
                return line.strip().split("=", 1)[1].strip().strip("\"'")
    sys.exit("FIRECRAWL_API_KEY introuvable (variable d'environnement ou ~/.hermes/.env)")


def fetch(url, key):
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=json.dumps({"url": url, "formats": ["rawHtml"]}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    raw = (r.get("data") or {}).get("rawHtml") or ""
    if "<item>" not in raw:
        raise RuntimeError("flux illisible ou vide (%d caractères)" % len(raw))
    return raw


def parse(raw):
    out = []
    for it in re.findall(r"<item>(.*?)</item>", raw, re.S)[:MAX_ITEMS]:
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        l = re.search(r"<link>(.*?)</link>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        if not (t and l):
            continue
        try:
            pub = parsedate_to_datetime(d.group(1).strip()).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if d else None
        except Exception:
            pub = None
        out.append((html.unescape(t.group(1).strip()), l.group(1).strip(), pub))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feed", action="append", required=True, help='"Nom du blog=URL du flux"')
    ap.add_argument("--dry-run", action="store_true", help="affiche sans rien écrire")
    a = ap.parse_args()

    feeds = {}
    for f in a.feed:
        if "=" not in f:
            sys.exit('format attendu : --feed "Nom=URL"')
        name, url = f.split("=", 1)
        feeds[name.strip()] = url.strip()

    if not os.path.exists(DB):
        sys.exit("base blogwatcher-cli introuvable (%s) : lance d'abord blogwatcher-cli add puis scan" % DB)

    key = firecrawl_key()
    con = sqlite3.connect(DB, timeout=30)
    total_new, errors = 0, []
    for name, feed in feeds.items():
        row = con.execute("select id from blogs where name=?", (name,)).fetchone()
        if not row:
            errors.append(name + " : blog absent de blogwatcher-cli")
            continue
        try:
            items = parse(fetch(feed, key))
        except (urllib.error.URLError, RuntimeError, ValueError) as e:
            errors.append("%s : %s" % (name, e))
            continue
        new = 0
        for title, url, pub in items:
            if con.execute("select 1 from articles where url=?", (url,)).fetchone():
                continue
            new += 1
            print(("[essai] " if a.dry_run else "") + "nouvel article %s | %s | %s" % (name, (pub or "")[:10], title[:80]))
            if not a.dry_run:
                con.execute("insert into articles (blog_id, title, url, published_date, is_read) values (?,?,?,?,0)", (row[0], title, url, pub))
        if not a.dry_run:
            con.execute("update blogs set last_scanned=? where id=?", (datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), row[0]))
        total_new += new
    if not a.dry_run:
        con.commit()
    print("%s : %d nouvel(s) article(s), %d erreur(s)" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), total_new, len(errors)))
    for e in errors:
        print("ERREUR", e, file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
