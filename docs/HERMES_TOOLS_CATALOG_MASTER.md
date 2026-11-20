# HERMES TOOLS CATALOG — MCP, APIs & Skills

> **Master reference — 29 September 2026**
>
> This file **supersedes** `HERMES_MCP_API_REFERENTIAL` and `HERMES_FREE_API_CATALOG_V2`.
> Give this file to Claude Code together with the separate Hermes `SKILL.md`.
>
> **Goal:** provide a single decision catalog of external capabilities for Hermes: MCP servers, direct APIs, free/open-data sources, free-tier services, and the skill architecture that should orchestrate them.
>
> **Do not install everything automatically.** First inspect the current Hermes installation, detect existing equivalents, re-check current official documentation/free tiers/licences, then propose `INSTALL`, `OPTIONAL`, or `SKIP`.

---

## 1. The model: Skill vs MCP vs API

```text
SKILL  = brain / procedure / routing
MCP    = standardized tool interface, especially useful for actions
API    = external data/service
SCRIPT = optional adapter between Hermes and an API
```

A Hermes skill does **not** itself create access to an API. It teaches Hermes when and how to use capabilities that actually exist behind it.

### Recommended principle

- Use **MCPs for action capabilities**: browser, filesystem, Git/GitHub, memory, rich interactive tools.
- Use **official APIs directly for structured data**: finance, news, science, weather, companies, geo, security, books, culture.
- Use **skills to orchestrate/rout** those MCPs and APIs.
- Prefer an official REST API to a community MCP wrapper when the REST integration is simple.

---

# 2. MCP CATALOG

| MCP | Type | Cost | Purpose | Why give it to Hermes | Priority |
|---|---|---|---|---|---|
| **Playwright MCP** | MCP / browser automation | Open source | Navigate sites, click, fill forms, interact with dynamic Web apps | Gives Hermes real browser action capability | **P0** |
| **Filesystem MCP** | MCP | Open source | Read/write/move/manage files | Fundamental for an agent running on a VPS | **P0** |
| **GitHub MCP Server** | Official GitHub MCP | Open source; GitHub quotas apply | Repos, code, issues, PRs, Actions, security | Major capability for coding, maintenance and Claude Code workflows | **P0** |
| **Git MCP** | MCP | Open source | Commits, branches, history, diffs, local repos | Lets Hermes version its own work/projects | **P0/P1** |
| **Fetch MCP** | MCP | Open source | Retrieve HTTP/Web content | Lightweight alternative to full browser automation | **P1** |
| **Memory MCP** | MCP | Open source | Persistent knowledge graph | Useful if it adds value beyond Hermes native memory | **P2** |
| **Time MCP** | MCP | Open source | Dates, time zones, time operations | Useful only if Hermes lacks equivalent native capability | **P3** |

### Suggested filesystem boundaries

```text
/data
/projects
/knowledge
/reports
/inbox
/cache
```

Use least privilege. Browser, filesystem, Git and GitHub are **action tools** and should be treated as more sensitive than read-only data APIs.

---

# 3. API CATALOG — 50 candidates

Free-level legend:

- **A — Open/free:** generally usable without payment, often without a key.
- **B — Free tier:** account/key with a permanent free allocation.
- **C — Free but constrained:** low quota and/or important dev, commercial or redistribution restrictions.

Priorities:

- **P0:** very high value.
- **P1:** integrate quickly if not redundant.
- **P2:** useful depending on actual Hermes use.
- **P3:** specialized.

# Les 50 API candidates

| # | API | Domaine | Gratuité | Auth | Ce qu'elle apporte à Hermes | Pourquoi l'intégrer | Priorité |
|---:|---|---|---|---|---|---|---|
| 1 | **Tavily** | Web search | B | Key | Recherche + extraction orientées agents | Recherche Web structurée, très adaptée aux LLM | P0 |
| 2 | **Brave Search API** | Web search | B | Key | Index Web indépendant | Fallback/validation croisée de Tavily | P1 |
| 3 | **Wikipedia / MediaWiki** | Knowledge | A | Non | Articles, catégories, liens | Encyclopédie structurée et rapide | P1 |
| 4 | **Wikidata SPARQL** | Knowledge graph | A | Non | Entités + relations structurées | Graphe de connaissances mondial interrogeable | P0 |
| 5 | **OpenAlex** | Science | A/B | Optionnelle | Papers, auteurs, institutions, citations | Recherche académique de premier niveau | P0 |
| 6 | **Crossref** | Science | A | Non | DOI et métadonnées scientifiques | Validation et déduplication des publications | P1 |
| 7 | **arXiv** | Science/AI | A | Non | Preprints récents | Très utile pour veille IA/tech | P1 |
| 8 | **Semantic Scholar** | Science | B | Key selon usage | Papers, citations, auteurs | Complément académique et graphe de citations | P2 |
| 9 | **Europe PMC** | Biomédical | A | Non | Littérature biomédicale | Source spécialisée de qualité | P2 |
| 10 | **CORE** | Science/Open Access | B | Key | Publications Open Access | Accès supplémentaire au texte/recherche académique | P2 |
| 11 | **FRED** | Macro/finance | A/B | Key gratuite | Séries macro US/internationales | Données économiques de référence | P1 |
| 12 | **World Bank Indicators** | Macro | A | Non | PIB, inflation, population, emploi, etc. | Comparaisons internationales historiques | P1 |
| 13 | **ECB Data API** | Finance/macro | A | Non | Taux, devises, statistiques zone euro | Source officielle européenne | P1 |
| 14 | **Frankfurter** | FX | A | Non | Taux de change | Conversion et historique FX simple | P1 |
| 15 | **Alpha Vantage** | Marchés | C | Key | Actions, ETF, FX, crypto, indicateurs | Large couverture mais quota gratuit faible | P2 |
| 16 | **Financial Modeling Prep** | Marchés | B/C | Key | Fondamentaux, sociétés cotées, prix | Analyse d'entreprises cotées | P1 |
| 17 | **Finnhub** | Marchés/news finance | B | Key | Marchés, sociétés, actualités financières | Bon enrichissement finance temps quasi-réel | P1 |
| 18 | **Twelve Data** | Marchés | B | Key | Actions, FX, crypto, séries temporelles | Bon moteur de données de marché | P1 |
| 19 | **CoinGecko** | Crypto | A/B | Selon offre | Prix, market cap, tokens, exchanges | Référence crypto généraliste | P1 |
| 20 | **CoinCap** | Crypto | A/B | Selon usage | Marchés crypto et historique | Fallback crypto léger | P2 |
| 21 | **GNews** | News | B/C | Key | Recherche d'actualités mondiales | Veille temps réel / récente | P1 |
| 22 | **NewsData.io** | News | B/C | Key | Actualités multi-pays/langues | Bonne couverture internationale | P1 |
| 23 | **Mediastack** | News | B/C | Key | News + sources | Source supplémentaire de veille | P2 |
| 24 | **The Guardian Open Platform** | News | B/C | Key | Articles Guardian | Source éditoriale structurée | P2 |
| 25 | **New York Times APIs** | News/archive | B/C | Key | Articles, archives, livres | Recherche presse/archives ; vérifier usage commercial | P2 |
| 26 | **Hacker News API** | Tech news | A | Non | Posts, commentaires, tendances | Signal tech/IA/startups très utile | P1 |
| 27 | **Open-Meteo** | Météo | A | Non | Prévisions, historique, variables météo | Excellent ratio valeur/coût | P1 |
| 28 | **OpenStreetMap / Nominatim** | Geo | A | Non | Géocodage/reverse | Couverture mondiale ; respecter usage policy | P1 |
| 29 | **Geo API Gouv** | Geo FR | A | Non | Communes, départements, régions, EPCI | Référence administrative française | P1 |
| 30 | **Géoplateforme / IGN** | Geo FR | A/B | Selon service | Adresses, POI, géodonnées | Géocodage et données françaises officielles | P1 |
| 31 | **REST Countries** | Geo | A | Non | Pays, langues, monnaies, capitales | Petit outil universel très pratique | P2 |
| 32 | **GeoNames** | Geo | B | Compte gratuit | Lieux et toponymie | Recherche géographique mondiale | P2 |
| 33 | **OpenRouteService** | Routing | B | Key | Itinéraires, matrices, isochrones | Donne une vraie capacité de calcul de trajets | P2 |
| 34 | **Recherche Entreprises API Gouv** | Business FR | A | Non | SIREN/SIRET, activité, dirigeants, établissements | Recherche business française immédiate | P0 |
| 35 | **INPI / RNE** | Business FR | A/B | Compte selon accès | Actes, statuts, comptes, événements légaux | Recherche entreprise approfondie | P2 |
| 36 | **data.gouv.fr API** | Open data FR | A | Non | Catalogue de datasets publics | Porte d'entrée générique Open Data France | P1 |
| 37 | **transport.data.gouv.fr** | Transport FR | A | Non/variable | GTFS, transports et mobilité | Mobilité française structurée | P2 |
| 38 | **NVD** | Cyber défense | A/B | Key optionnelle | CVE, CVSS, produits vulnérables | Analyse sécurité des dépendances | P1 |
| 39 | **CISA KEV** | Cyber défense | A | Non | Vulnérabilités exploitées | Priorisation opérationnelle des CVE | P1 |
| 40 | **RDAP** | Internet | A | Non | Domaines, IP, registrars | Remplaçant structuré de WHOIS | P2 |
| 41 | **crt.sh / Certificate Transparency** | Internet/security | A | Non | Certificats et sous-domaines publics | Inventaire défensif d'infrastructure | P2 |
| 42 | **GitHub REST/GraphQL API** | Dev | B | Token recommandé | Repos, code, releases, issues | Source essentielle pour agent développeur | P0 |
| 43 | **Stack Exchange API** | Dev knowledge | B | Key optionnelle | Q/R techniques, tags | Complément à docs officielles et GitHub | P2 |
| 44 | **Open Library** | Livres | A | Non | ISBN, titres, auteurs, éditions, couvertures | Recherche bibliographique simple | P1 |
| 45 | **Internet Archive** | Archives | A | Selon action | Livres, médias, archives | Profondeur historique et archives | P2 |
| 46 | **Art Institute of Chicago API** | Culture/images | A | Non | Art, images, domaine public | Contenu culturel réutilisable avec métadonnées | P2 |
| 47 | **Met Museum API** | Culture/images | A | Non | Collections et images | Très vaste catalogue Open Access | P2 |
| 48 | **GBIF** | Biodiversité | A | Non pour lectures | Taxonomie et observations | Base mondiale spécialisée | P3 |
| 49 | **Open Food Facts** | Produits/alimentation | A | Non pour lectures | Produits, ingrédients, nutrition | Très utile pour analyse de produits alimentaires | P2 |
| 50 | **YouTube Data API** | Vidéo | B | Key/OAuth | Vidéos, chaînes, playlists, recherche | Recherche/veille vidéo et formation | P1 |

---

---

# 4. MCP vs API — decision rule

Use this default:

```text
Need to ACT on a system?
        │
        ├── yes → trusted/official MCP when appropriate
        │
        └── no
             ↓
Need structured external DATA?
        │
        ├── yes → official API directly
        │
        └── no → existing Hermes capability first
```

Examples:

| Need | Preferred integration |
|---|---|
| Browse/click/login/form | Playwright MCP |
| Manipulate local files | Filesystem MCP |
| PR/issues/repo actions | GitHub MCP |
| Local repository operations | Git MCP |
| Search papers | OpenAlex/Crossref API |
| Weather | Open-Meteo API |
| Market data | Finance API |
| Company registry | Official registry API |
| CVEs | NVD + CISA API/data |
| Knowledge graph | Wikidata API |

---

# 5. Recommended Hermes skill architecture

Do **not** expose 50 independent tools to the model unless necessary.

```text
HERMES
│
├── web-research
│   ├── Tavily
│   ├── Brave
│   ├── Wikipedia
│   ├── Wikidata
│   └── Playwright when interaction is required
│
├── news-research
│   ├── GNews / NewsData
│   ├── Hacker News
│   └── Web-search fallback
│
├── scientific-research
│   ├── OpenAlex
│   ├── Crossref
│   ├── arXiv
│   ├── Semantic Scholar
│   ├── Europe PMC
│   └── CORE
│
├── finance-research
│   ├── FRED
│   ├── World Bank
│   ├── ECB
│   ├── FMP / Finnhub / Twelve Data
│   ├── CoinGecko
│   └── Frankfurter
│
├── company-research
│   ├── Recherche Entreprises API Gouv
│   ├── INPI/RNE
│   ├── Wikidata
│   └── Web/news
│
├── geo-intelligence
│   ├── OSM/Nominatim
│   ├── Geo API Gouv
│   ├── IGN/Géoplateforme
│   ├── OpenRouteService
│   ├── Open-Meteo
│   └── transport.data.gouv.fr
│
├── security-intelligence
│   ├── NVD
│   ├── CISA KEV
│   ├── RDAP
│   └── Certificate Transparency
│
├── books-culture
│   ├── Open Library
│   ├── Internet Archive
│   ├── Met Museum
│   └── Art Institute Chicago
│
└── dev-intelligence
    ├── GitHub MCP/API
    ├── Git MCP
    ├── Stack Exchange
    └── Hacker News
```

The separate `SKILL.md` can serve as the initial **Data Intelligence Router** implementing this routing logic.

---

# 6. Recommended packs

## Pack 0 — Hermes Core

Evaluate first:

1. Playwright MCP
2. Filesystem MCP
3. GitHub MCP
4. Git MCP
5. Tavily
6. Fetch MCP

**Outcome:** Hermes can search, browse, act, read/write and develop.

## Pack 1 — Structured Intelligence

High-value candidates:

1. Wikidata
2. Wikipedia
3. OpenAlex
4. Crossref
5. arXiv
6. World Bank
7. FRED
8. ECB
9. Recherche Entreprises API Gouv
10. Open-Meteo
11. Geo API Gouv
12. NVD
13. CISA KEV
14. Open Library
15. CoinGecko

## Pack 2 — Current / Extended Intelligence

Evaluate according to actual need:

- Brave Search
- GNews or NewsData.io
- Finnhub / Twelve Data / FMP
- Semantic Scholar
- Europe PMC
- CORE
- Frankfurter
- Alpha Vantage
- INPI/RNE
- data.gouv.fr
- transport.data.gouv.fr
- OpenRouteService
- RDAP
- Certificate Transparency
- YouTube Data API
- Internet Archive
- Stack Exchange
- Hacker News
- Met Museum
- Art Institute Chicago

## Pack 3 — Specialized

- GBIF
- NASA or other specialist scientific sources if later selected
- Open Food Facts
- other domain-specific APIs justified by real Hermes usage

---

# 7. Finance strategy

Do not install every overlapping finance API blindly.

Route by data type:

```text
Macroeconomics US/global → FRED
International development → World Bank
Euro area / official EU monetary data → ECB
FX reference/conversion → Frankfurter / ECB
Listed-company fundamentals → choose FMP/Finnhub/Twelve Data after testing
Market series → chosen market provider
Crypto → CoinGecko
Fallback/technical indicators → Alpha Vantage if useful
```

### Critical warning

Free finance plans may provide **delayed quotes**, restricted exchanges, small quotas or limited historical data. Never label a value as `real-time` unless the actual endpoint/free plan guarantees it.

---

# 8. News strategy

Do not pay the context cost of many overlapping news tools.

Recommended evaluation:

```text
Primary news API → choose GNews OR NewsData.io after testing
General Web corroboration → Tavily / Brave
Tech community signal → Hacker News
Specialized publishers → Guardian / NYT only if they add real value
```

For important breaking claims, cross-check independent sources.

---

# 9. Scientific research strategy

```text
Question
   ↓
OpenAlex → discovery/citation graph
   +
Crossref → DOI/metadata verification
   +
arXiv → recent preprints
   +
Semantic Scholar → enrichment when useful
   +
Europe PMC → biomedical queries
   ↓
deduplicate by DOI / normalized title
   ↓
distinguish preprints from peer-reviewed work
   ↓
synthesis + provenance
```

---

# 10. Company research strategy

For France:

```text
Recherche Entreprises API Gouv
        ↓
official identity / SIREN / SIRET / activity
        │
        ├── INPI/RNE for deeper legal information
        ├── Wikidata for entity context
        └── Tavily/news for current context
```

Never mix official registry facts and Web claims without identifying their source.

---

# 11. Geo strategy

```text
Global geocoding       → OSM/Nominatim
French administration  → Geo API Gouv
French address/geo     → IGN/Géoplateforme
Routes/isochrones      → OpenRouteService
Weather                → Open-Meteo
Transport FR           → transport.data.gouv.fr
Country metadata       → REST Countries
Place names            → GeoNames
```

Respect Nominatim's public-service policy. Do not use the public instance as an unlimited bulk geocoder.

---

# 12. Security strategy

Defensive use:

```text
NVD      → known CVEs / CVSS / affected products
CISA KEV → known exploitation in the wild
RDAP     → domain/IP registration information
CT       → public TLS certificate inventory
```

Do not infer exploitability solely from CVSS.

---

# 13. Shared API infrastructure

Claude Code should avoid 20 unrelated one-off clients.

Create a common provider layer with:

- HTTP client;
- timeouts;
- retries with exponential backoff;
- provider-specific rate limiting;
- cache + TTL;
- typed errors;
- provenance;
- usage metrics;
- per-provider enable/disable;
- secrets through environment variables or a secret store;
- no secrets in prompts, repositories or logs.

### Normalized result contract

```json
{
  "provider": "openalex",
  "query": "AI software engineering productivity",
  "retrieved_at": "ISO-8601",
  "source_url": "https://...",
  "cached": false,
  "data": {},
  "warnings": []
}
```

### Example cache guidance

- breaking news/search: 5–15 min;
- market quotes: provider-dependent, typically very short;
- weather: 15–60 min;
- company registry: ~24 h;
- Wikidata/Wikipedia: 6–24 h;
- academic metadata: 1–7 days;
- historical macro: 1–7 days;
- CVE/KEV: 1–6 h.

Provider terms always override these defaults.

---

# 14. Decision criteria for Claude Code

For every candidate, evaluate:

| Criterion | Question |
|---|---|
| **Existing capability** | Does Hermes already do this well? |
| **Incremental value** | Does this provider add a genuinely new capability? |
| **Redundancy** | Is 90% of the need already covered? |
| **Cost** | Is the free tier sufficient? |
| **Authentication** | None, API key, OAuth? |
| **Commercial use** | Is our intended usage allowed? |
| **Stability** | Official and maintained? |
| **Security** | Does it add read or action privileges? |
| **Quota** | Can we stay within limits? |
| **Cacheability** | Can calls be reduced safely? |
| **Fallback** | Is there a secondary source? |
| **Provenance** | Can Hermes retain source URL/provider/time? |
| **Context cost** | Should this be hidden behind a skill rather than exposed directly? |

---

# 15. Priority matrix

## P0 — Evaluate/install first

- Playwright MCP
- Filesystem MCP
- GitHub MCP
- Git MCP
- Tavily
- Wikidata
- OpenAlex
- Recherche Entreprises API Gouv

## P1 — High value

- Fetch MCP
- Brave Search
- Wikipedia
- Crossref
- arXiv
- FRED
- World Bank
- ECB
- Frankfurter
- chosen market-data provider
- CoinGecko
- chosen news provider
- Open-Meteo
- OSM/Nominatim
- Geo API Gouv
- Géoplateforme
- NVD
- CISA KEV
- Open Library
- GitHub API
- YouTube Data API

## P2 — Add when justified

- Memory MCP
- Semantic Scholar
- Europe PMC
- CORE
- secondary finance providers
- INPI/RNE
- data.gouv.fr
- transport.data.gouv.fr
- OpenRouteService
- GeoNames
- RDAP
- Certificate Transparency
- Stack Exchange
- Hacker News
- Internet Archive
- Met Museum
- Art Institute Chicago
- Open Food Facts

## P3 — Specialized

- Time MCP if Hermes already handles time well
- GBIF
- other specialist sources only when a concrete use case exists

---

# 16. Mission for Claude Code

**Do not modify Hermes immediately.**

First:

1. inspect the currently installed Hermes version;
2. inventory existing tools, MCPs, skills and API integrations;
3. identify duplicates with this master catalog;
4. re-check each candidate against its **current official documentation**;
5. verify free tier, exact quota, authentication, licence, commercial restrictions and redistribution rights;
6. test whether the free plan actually provides the advertised useful data;
7. decide the best integration mechanism;
8. evaluate security/permissions;
9. define caching, rate limiting, timeout and retry behavior;
10. preserve source provenance;
11. propose a phased plan **before making changes**.

For every provider/tool, output:

```text
Provider:
Category:
Existing equivalent:
Decision: INSTALL | OPTIONAL | SKIP
Integration: MCP | DIRECT_API | SCRIPT_ADAPTER | SKILL_ONLY
Free tier:
Exact quota:
Auth:
Commercial restrictions:
Expected value:
Redundancy:
Security impact:
Skill/router:
Reason:
```

### Specific request for overlapping providers

Benchmark rather than automatically installing all alternatives:

- FMP vs Finnhub vs Twelve Data;
- GNews vs NewsData.io vs Mediastack;
- Tavily vs Brave for their respective roles;
- native Hermes memory vs Memory MCP;
- native Hermes fetch/browser capabilities vs Fetch/Playwright MCP.

---

# 17. Target architecture

The target is **not**:

```text
Hermes + 50 APIs + 20 MCPs all exposed simultaneously
```

The target is:

```text
Hermes
  │
  ├── 5–10 trusted general tools/MCPs
  │
  ├── 8–10 intelligent routing skills
  │
  ├── ~15–25 useful configured APIs
  │
  ├── common cache/rate-limit/provenance layer
  │
  └── progressive activation based on real usage
```

The goal is an agent capable of **searching, verifying, cross-checking, acting, coding and exploiting structured data** while remaining maintainable, economical and auditable.

---

# 18. Relationship with the separate SKILL.md

Keep `SKILL.md` separate from this catalog.

- **This file** = inventory + architecture + decision framework.
- **SKILL.md** = runtime procedural knowledge used by Hermes to route actual research tasks.
- **Claude Code** = audits the current installation, implements approved adapters/MCPs, and updates the skill to match the providers actually installed.

Once Claude Code has selected the final providers, update the skill so it references **only capabilities that really exist** in the Hermes environment.
