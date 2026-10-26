#!/usr/bin/env python3
"""Adaptateur unique pour API ouvertes (sans cle). Sortie JSON normalisee.
Usage: dataapi.py <provider> <query> [--limit N] [--no-cache]
Providers: wikipedia wikidata openalex crossref arxiv worldbank ecb frankfurter
           entreprises geoapi meteo nominatim nvd kev openlibrary hackernews coingecko
"""
import argparse, hashlib, json, os, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET

CACHE_DIR = os.path.expanduser('~/.hermes/cache/dataapi')
UA = 'HermesDataAPI/1.0 (contact: admin@localhost)'
TTL = {'hackernews': 600, 'coingecko': 300, 'meteo': 1800, 'frankfurter': 3600, 'ecb': 3600,
       'nvd': 7200, 'kev': 7200, 'entreprises': 86400, 'wikipedia': 43200, 'wikidata': 43200,
       'openalex': 86400, 'crossref': 86400, 'arxiv': 86400, 'worldbank': 86400,
       'geoapi': 86400, 'nominatim': 86400, 'openlibrary': 86400}
LAST_CALL = {}


def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def jget(url):
    return json.loads(http_get(url))


def q(**kw):
    return urllib.parse.urlencode({k: v for k, v in kw.items() if v is not None})


def wikipedia(query, n):
    lang = 'fr'
    u = f'https://{lang}.wikipedia.org/w/api.php?' + q(action='query', list='search', srsearch=query, srlimit=n, format='json')
    d = jget(u)
    res = [{'title': x['title'], 'snippet': x['snippet'].replace('<span class="searchmatch">', '').replace('</span>', ''),
            'url': f'https://{lang}.wikipedia.org/wiki/' + urllib.parse.quote(x['title'].replace(' ', '_'))}
           for x in d['query']['search']]
    return u, res


def wikidata(query, n):
    u = 'https://www.wikidata.org/w/api.php?' + q(action='wbsearchentities', search=query, language='fr', limit=n, format='json')
    d = jget(u)
    return u, [{'id': x['id'], 'label': x.get('label'), 'description': x.get('description'), 'url': x['concepturi']} for x in d['search']]


def openalex(query, n):
    u = 'https://api.openalex.org/works?' + q(search=query, per_page=n, sort='relevance_score:desc')
    d = jget(u)
    return u, [{'title': w['title'], 'year': w.get('publication_year'), 'doi': w.get('doi'), 'cited_by': w.get('cited_by_count'),
                'type': w.get('type'), 'authors': [a['author']['display_name'] for a in w.get('authorships', [])[:4]]} for w in d['results']]


def crossref(query, n):
    u = 'https://api.crossref.org/works?' + q(query=query, rows=n)
    d = jget(u)
    return u, [{'title': (i.get('title') or [''])[0], 'doi': i.get('DOI'), 'type': i.get('type'),
                'container': (i.get('container-title') or [''])[0], 'year': (i.get('issued', {}).get('date-parts') or [[None]])[0][0]}
               for i in d['message']['items']]


def arxiv(query, n):
    u = 'https://export.arxiv.org/api/query?' + q(search_query='all:' + query, max_results=n, sortBy='submittedDate', sortOrder='descending')
    root = ET.fromstring(http_get(u))
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    return u, [{'title': ' '.join(e.find('a:title', ns).text.split()), 'published': e.find('a:published', ns).text,
                'url': e.find('a:id', ns).text, 'status': 'preprint'} for e in root.findall('a:entry', ns)]


def worldbank(query, n):
    # query = "PAYS:INDICATEUR" ex: FR:NY.GDP.MKTP.CD
    country, ind = query.split(':', 1)
    u = f'https://api.worldbank.org/v2/country/{country}/indicator/{ind}?' + q(format='json', per_page=n)
    d = jget(u)
    return u, [{'year': r['date'], 'value': r['value'], 'indicator': r['indicator']['value'], 'country': r['country']['value']} for r in d[1]]


def ecb(query, n):
    # query = cle SDMX ex: EXR/D.USD.EUR.SP00.A
    u = f'https://data-api.ecb.europa.eu/service/data/{query}?' + q(format='jsondata', lastNObservations=n)
    d = jget(u)
    ser = list(d['dataSets'][0]['series'].values())[0]['observations']
    times = d['structure']['dimensions']['observation'][0]['values']
    return u, [{'date': times[int(k)]['id'], 'value': v[0]} for k, v in ser.items()]


def frankfurter(query, n):
    # query = "EUR:USD" ou "EUR"
    base, _, sym = query.partition(':')
    u = 'https://api.frankfurter.app/latest?' + q(**{'from': base or 'EUR', 'to': sym or None})
    d = jget(u)
    return u, {'base': d['base'], 'date': d['date'], 'rates': d['rates']}


def entreprises(query, n):
    u = 'https://recherche-entreprises.api.gouv.fr/search?' + q(q=query, per_page=n)
    d = jget(u)
    return u, [{'nom': r.get('nom_complet'), 'siren': r.get('siren'), 'siege_siret': (r.get('siege') or {}).get('siret'),
                'activite': r.get('activite_principale'), 'etat': r.get('etat_administratif'),
                'creation': r.get('date_creation'), 'effectif': r.get('tranche_effectif_salarie'),
                'dirigeants': [x.get('nom') or x.get('denomination') for x in r.get('dirigeants', [])[:3]],
                'ville': (r.get('siege') or {}).get('libelle_commune')} for r in d['results']]


def geoapi(query, n):
    u = 'https://geo.api.gouv.fr/communes?' + q(nom=query, fields='nom,code,codesPostaux,population,departement,region', limit=n)
    return u, jget(u)


def meteo(query, n):
    g = jget('https://geocoding-api.open-meteo.com/v1/search?' + q(name=query, count=1, language='fr'))
    p = g['results'][0]
    u = 'https://api.open-meteo.com/v1/forecast?' + q(latitude=p['latitude'], longitude=p['longitude'], current='temperature_2m,wind_speed_10m,precipitation',
                                                      daily='temperature_2m_max,temperature_2m_min,precipitation_sum', timezone='auto', forecast_days=3)
    d = jget(u)
    return u, {'place': p['name'], 'country': p.get('country'), 'current': d['current'], 'daily': d['daily']}


def nominatim(query, n):
    u = 'https://nominatim.openstreetmap.org/search?' + q(q=query, format='jsonv2', limit=n)
    return u, [{'name': r['display_name'], 'lat': r['lat'], 'lon': r['lon'], 'type': r['type']} for r in jget(u)]


def nvd(query, n):
    # query = CVE-XXXX-YYYY ou mot-cle
    if query.upper().startswith('CVE-'):
        u = 'https://services.nvd.nist.gov/rest/json/cves/2.0?' + q(cveId=query.upper())
    else:
        u = 'https://services.nvd.nist.gov/rest/json/cves/2.0?' + q(keywordSearch=query, resultsPerPage=n)
    d = jget(u)
    out = []
    for v in d.get('vulnerabilities', []):
        c = v['cve']
        m = c.get('metrics', {})
        score = None
        for k in ('cvssMetricV31', 'cvssMetricV40', 'cvssMetricV30', 'cvssMetricV2'):
            if k in m:
                score = m[k][0]['cvssData'].get('baseScore'); break
        out.append({'id': c['id'], 'published': c['published'], 'cvss': score,
                    'desc': next((x['value'] for x in c['descriptions'] if x['lang'] == 'en'), '')[:300]})
    return u, out


def kev(query, n):
    u = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
    d = jget(u)
    ql = query.lower()
    hits = [v for v in d['vulnerabilities'] if ql in v['cveID'].lower() or ql in v['vendorProject'].lower() or ql in v['product'].lower()]
    return u, [{'cve': v['cveID'], 'vendor': v['vendorProject'], 'product': v['product'], 'added': v['dateAdded'],
                'ransomware': v.get('knownRansomwareCampaignUse')} for v in hits[:n]]


def openlibrary(query, n):
    u = 'https://openlibrary.org/search.json?' + q(q=query, limit=n)
    return u, [{'title': b.get('title'), 'author': b.get('author_name'), 'year': b.get('first_publish_year'), 'key': b.get('key')} for b in jget(u)['docs']]


def hackernews(query, n):
    u = 'https://hn.algolia.com/api/v1/search?' + q(query=query, tags='story', hitsPerPage=n)
    return u, [{'title': h['title'], 'points': h['points'], 'comments': h['num_comments'], 'url': h.get('url'),
                'hn': f"https://news.ycombinator.com/item?id={h['objectID']}"} for h in jget(u)['hits']]


def coingecko(query, n):
    u = 'https://api.coingecko.com/api/v3/simple/price?' + q(ids=query.lower(), vs_currencies='usd,eur', include_24hr_change='true', include_last_updated_at='true')
    return u, jget(u)


PROVIDERS = {f.__name__: f for f in (wikipedia, wikidata, openalex, crossref, arxiv, worldbank, ecb, frankfurter, entreprises,
                                      geoapi, meteo, nominatim, nvd, kev, openlibrary, hackernews, coingecko)}


def run(provider, query, n, use_cache=True):
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha1(f'{provider}|{query}|{n}'.encode()).hexdigest()
    path = os.path.join(CACHE_DIR, key + '.json')
    if use_cache and os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL.get(provider, 3600):
        out = json.load(open(path)); out['cached'] = True
        return out
    try:
        src, data = PROVIDERS[provider](query, n)
        out = {'provider': provider, 'query': query, 'retrieved_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'source_url': src, 'cached': False, 'data': data, 'warnings': []}
        json.dump(out, open(path, 'w'), ensure_ascii=False)
        return out
    except Exception as e:
        return {'provider': provider, 'query': query, 'error': type(e).__name__, 'message': str(e)[:200]}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('provider', choices=sorted(PROVIDERS))
    ap.add_argument('query')
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--no-cache', action='store_true')
    a = ap.parse_args()
    print(json.dumps(run(a.provider, a.query, a.limit, not a.no_cache), ensure_ascii=False, indent=2))
