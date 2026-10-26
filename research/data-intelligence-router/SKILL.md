---
name: data-intelligence-router
description: Route research tasks to the best structured data sources (open APIs via dataapi.py, Firecrawl, FMP) with provenance
version: 1.1.0
platforms: [linux]
metadata:
  hermes:
    tags: [research, api, finance, news, science, open-data]
    category: research
    requires_toolsets: [terminal]
---

# Data Intelligence Router

Selectionner, interroger, recouper et citer des sources de donnees structurees.
Preferer les API officielles et les outils Hermes existants au scraping navigateur.

## Quand l'utiliser
Recherche web structuree, actualite/tendances tech, litterature scientifique, finance/macro/FX/crypto,
fiches entreprises, geo/meteo, vulnerabilites, livres, verification croisee.
Ne pas le charger pour une question a laquelle Hermes repond deja avec certitude.

## Capacites REELLEMENT installees (verifie 2026-10-02)

Adaptateur sans cle, sortie JSON normalisee (provider, query, retrieved_at, source_url, cached, data, warnings), cache TTL integre :

```bash
python3 ~/.hermes/scripts/dataapi.py <provider> "<requete>" [--limit N] [--no-cache]
```

| Domaine | Provider | Format de requete |
|---|---|---|
| Web/encyclopedie | `wikipedia`, `wikidata` | texte libre |
| Science | `openalex`, `crossref`, `arxiv` | texte libre (arxiv = preprints, NON relus) |
| Macro | `worldbank` | `FR:NY.GDP.MKTP.CD` (pays:indicateur) |
| Macro/FX | `ecb` | cle SDMX ex `EXR/D.USD.EUR.SP00.A` |
| FX | `frankfurter` | `EUR:USD` |
| Entreprises FR | `entreprises` | nom ou SIREN |
| Geo FR / monde | `geoapi`, `nominatim` | nom de commune / adresse |
| Meteo | `meteo` | nom de ville |
| Securite | `nvd` (CVE-ID ou mot-cle), `kev` (CVE/vendor/produit) | |
| Livres | `openlibrary` | titre/auteur |
| Tech community | `hackernews` | texte libre |
| Crypto | `coingecko` | id coin ex `bitcoin` |

Autres outils deja presents : Firecrawl (recherche/extraction web, FIRECRAWL_API_KEY), FMP (fondamentaux cotes, FMP_API_KEY), navigateur Hermes, skills `github-*`, `grounded-citations`, `competitor-news-monitor`.

NON installes (ne pas pretendre les utiliser) : Tavily, Brave, GNews/NewsData, Finnhub, Twelve Data, FRED, Semantic Scholar, INPI/RNE, OpenRouteService, MCP (Playwright/Git/Filesystem). Si une cle est ajoutee dans ~/.hermes/.env, creer l'adaptateur correspondant puis mettre ce tableau a jour.

## Routage

- Web general : Firecrawl > wikipedia > wikidata (relations entre entites) > navigateur seulement si interaction requise.
- News : Firecrawl avec filtre de recence + hackernews (signal communautaire, jamais source d'autorite). Actu sensible : 2 sources independantes.
- Science : openalex (decouverte) > crossref (validation DOI) > arxiv (recent). Dedoublonner par DOI puis titre normalise. Distinguer article relu / preprint.
- Finance : macro `worldbank`/`ecb`, FX `frankfurter`/`ecb`, crypto `coingecko`, fondamentaux via FMP. Un cours gratuit est souvent retarde : ne jamais ecrire "temps reel". Toujours donner symbole, devise, horodatage.
- Entreprises FR : `entreprises` (faits officiels) puis wikidata/web pour le contexte. Separer faits registre et affirmations web. Un nom peut renvoyer plusieurs entites legales.
- Geo : `geoapi` (admin FR), `nominatim` (monde, usage ponctuel, pas de bulk), `meteo`.
- Securite (defensif uniquement) : `nvd` puis `kev`. Donner CVE, severite + source, statut KEV. Ne pas deduire l'exploitabilite du seul CVSS.
- Livres : `openlibrary`.

## Procedure
1. Analyser le besoin, la fraicheur requise, le(s) domaine(s).
2. Choisir le minimum de providers. Interroger la source primaire.
3. Recouper si : temps reel/recent, source incomplete, decision importante, faible confiance.
4. Normaliser entites, dates, devises, unites. Resoudre les conflits par autorite puis fraicheur.
5. Repondre : reponse d'abord, horodatage si temporel, source/provider cites, incertitudes signalees, pas de dump brut.

Autorite : registre officiel > editeur/fournisseur primaire > base structuree reconnue > source secondaire serieuse > communaute.

## Regles
- Ne jamais inventer un resultat. Une erreur renvoie `{"error": ...}` : le dire, tenter un fallback, sinon l'indiquer.
- Respecter limites et licences des providers. Ne jamais afficher de cle API dans une sortie ou un log.
- Le cache est dans ~/.hermes/cache/dataapi (TTL par provider). `--no-cache` pour forcer.
- Aucun provider ne doit bloquer une tache : en cas d'echec, continuer sans.

## Pitfalls
Quotas gratuits changeants ; Nominatim non adapte au bulk ; doublons academiques ; symboles boursiers ambigus entre places ; disponibilite d'une API != droit de redistribution ; un MCP communautaire ajoute un risque supply-chain par rapport a une simple API REST.

## Ajouter un provider
Verifier la doc officielle, le quota et l'usage commercial, ajouter une fonction dans dataapi.py (meme contrat), la tester (succes, timeout, erreur), documenter la variable d'env, mettre a jour le tableau ci-dessus.

## Installation
Copier `scripts/dataapi.py` dans `~/.hermes/scripts/`. Aucune cle requise pour les adaptateurs ; `FIRECRAWL_API_KEY` et `FMP_API_KEY` sont facultatives.
