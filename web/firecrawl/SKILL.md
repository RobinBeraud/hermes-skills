---
name: firecrawl
category: web
description: Scrape, search et interagit avec le web via Firecrawl — extrait du contenu propre en Markdown depuis n'importe quelle URL, recherche sur le web, crawl de sites entiers, et interaction avec des pages dynamiques (clics, formulaires). Clef API dans FIRECRAWL_API_KEY.
tags: [web, scraping, recherche, crawl, markdown, browser]
requires:
  env_vars:
    - FIRECRAWL_API_KEY
---

# Skill: Firecrawl — Web Scraping & Search

## Description
Firecrawl transforme n'importe quelle page web en **Markdown propre**, fait des recherches web, crawle des sites entiers, et interagit avec des pages dynamiques via browser automation.

**Base URL** : `https://api.firecrawl.dev/v2`  
**Auth** : `Authorization: Bearer $FIRECRAWL_API_KEY`

## Quand utiliser ce skill
- "Scrape cette page / extrait le contenu de cette URL"
- "Cherche sur le web [requête]"
- "Analyse / résume ce site web"
- "Crawle toutes les pages de [domaine]"
- "Clique sur ce bouton / remplis ce formulaire sur [URL]"
- "Extrait les données de cette page dynamique (JS)"
- "Compare le contenu de ces deux URLs"
- Toute tâche nécessitant du contenu web propre pour analyse

## Fonction utilitaire

```python
import os, urllib.request, json

BASE = "https://api.firecrawl.dev/v2"
KEY = os.environ["FIRECRAWL_API_KEY"]

def firecrawl(endpoint, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}/{endpoint}",
        data=data,
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json"
        }
    )
    return json.loads(urllib.request.urlopen(req).read())
```

## Exemples

### Scraper une URL → Markdown
```python
result = firecrawl("scrape", {
    "url": "https://example.com",
    "formats": ["markdown"]
})
print(result["data"]["markdown"])
```

### Scraper avec métadonnées
```python
result = firecrawl("scrape", {
    "url": "https://example.com",
    "formats": ["markdown", "extract"],
    "extract": {
        "prompt": "Extrais le titre, l'auteur, la date et le résumé."
    }
})
print(result["data"]["extract"])
```

### Recherche web
```python
result = firecrawl("search", {
    "query": "Hermes AI agent python",
    "limit": 5,
    "scrapeOptions": {"formats": ["markdown"]}
})
for r in result["data"]:
    print(f"{r['title']} — {r['url']}")
    print(r.get("markdown", "")[:200])
```

### Crawl d'un site entier
```python
# Lancer le crawl
job = firecrawl("crawl", {
    "url": "https://docs.example.com",
    "limit": 50,
    "scrapeOptions": {"formats": ["markdown"]}
})
job_id = job["id"]

# Vérifier le statut
import time
while True:
    status = firecrawl(f"crawl/{job_id}", {})
    if status["status"] == "completed":
        break
    time.sleep(3)

# Récupérer les résultats
for page in status["data"]:
    print(f"{page['metadata']['title']} — {page['metadata']['sourceURL']}")
```

### Interaction avec page dynamique (clics, formulaires)
```python
result = firecrawl("interact", {
    "url": "https://example.com/login",
    "actions": [
        {"type": "fill", "selector": "#email", "value": "user@example.com"},
        {"type": "fill", "selector": "#password", "value": "password"},
        {"type": "click", "selector": "#submit"},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scrape", "formats": ["markdown"]}
    ]
})
print(result["data"]["markdown"])
```

### Extraction structurée (JSON)
```python
result = firecrawl("scrape", {
    "url": "https://shop.example.com/product/123",
    "formats": ["extract"],
    "extract": {
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number"},
                "availability": {"type": "string"},
                "description": {"type": "string"}
            }
        }
    }
})
print(result["data"]["extract"])
# → {"name": "...", "price": 29.99, "availability": "In Stock", ...}
```

### Mapper les URLs d'un site
```python
result = firecrawl("map", {"url": "https://example.com"})
for url in result["links"][:20]:
    print(url)
```

## Cas d'usage typiques

### Résumé de page web
```python
result = firecrawl("scrape", {"url": url, "formats": ["markdown"]})
content = result["data"]["markdown"][:3000]
# → passer à Claude pour résumé
```

### Veille concurrentielle
```python
competitors = ["https://competitor1.com", "https://competitor2.com"]
for url in competitors:
    r = firecrawl("scrape", {"url": url, "formats": ["markdown"]})
    print(f"=== {url} ===")
    print(r["data"]["markdown"][:500])
```

### Recherche + synthèse
```python
results = firecrawl("search", {"query": "meilleur framework Python 2026", "limit": 5})
sources = "\n\n".join([f"# {r['title']}\n{r.get('markdown','')[:500]}" for r in results["data"]])
# → passer à Claude pour synthèse
```

## Notes
- **Formats disponibles** : `markdown`, `html`, `rawHtml`, `screenshot`, `extract`
- **Actions interact** : `click`, `fill`, `wait`, `scroll`, `screenshot`, `scrape`
- **Rate limits** : dépend du plan (Free: 500 crédits/mois)
- **Documentation** : https://docs.firecrawl.dev
