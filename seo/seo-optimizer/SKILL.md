---
name: seo-optimizer
description: >-
  Système automatisé d'optimisation SEO continue pour sites WordPress.
  Google Search Console, détection de sujets et tendances, NeuronWriter,
  amélioration ou rédaction de contenu, republication WordPress/WPBakery.
  Deux boucles : optimisation des pages existantes ET création d'articles
  sur sujets réellement recherchés.
---

# Skill: seo-optimizer

Système d'amélioration continue SEO à deux boucles pour sites WordPress.

## Quand l'utiliser
- Lancer un cycle d'optimisation SEO sur un site WordPress
- Identifier les pages avec potentiel de progression vers le top 10
- Améliorer le score NeuronWriter d'une page existante
- Détecter les sujets réellement recherchés sur Google pour écrire de nouveaux articles
- Combiner demande Google (GSC) + veille éditoriale (blogwatcher) pour briefer la rédaction
- Publier un article optimisé SEO avec WPBakery

---

## ÉTAT OPÉRATIONNEL

- **Google Search Console OAuth** : Token à `~/.hermes/credentials/gsc-token.json`, credentials à `~/.hermes/credentials/gsc-credentials.json`. Lib : `googleapiclient` + `google.oauth2.credentials`, refresh auto si `creds.expired and creds.refresh_token`.
  - **IMPORTANT** : utiliser `siteUrl='sc-domain:votre-domaine.com'`. La forme `https://votre-domaine.com/` renvoie un **403**. Lister les sites accessibles avec `service.sites().list()`.
- **NeuronWriter** : clé `NEURONWRITER_API_KEY` dans `~/.hermes/.env`, project ID à configurer.
- **WordPress** : credentials dans le skill `wpbakery`. **User-Agent: Mozilla/5.0 obligatoire** sinon Cloudflare bloque.

### Scripts en place (`~/.hermes/scripts/seo/`)
| Script | Rôle |
|--------|------|
| `gsc_fetch.py` + `score_pages.py` | Récup GSC + scoring pages -> `~/.hermes/data/pages_to_optimize.json` |
| `seo_optimize.py daily` | Boucle d'optimisation : 3 pages HIGH (NeuronWriter -> Claude -> publish) |
| `seo_batch.py N` | Optimise les N prochaines pages HIGH non encore traitées aujourd'hui |
| `gsc_trending.py` | Détecte sujets tendance GSC (RISING / GAP / STRIKING) |
| `gsc_veille_brief.py` | Brief combiné GSC + veille blogwatcher |

### Crons recommandés
- `gsc_fetch` + `score_pages` hebdomadaire (ex: lundi 7h)
- `seo_optimize.py daily` quotidien (ex: 3h)
- Article quotidien (ex: 16h) : `gsc_veille_brief.py` injecte le brief -> skills `wpbakery` + `neuronwriter`

---

## Les deux boucles

```
BOUCLE 1 — OPTIMISER L'EXISTANT (nuit)
  GSC positions -> score_pages -> pages HIGH (pos 8-20, impressions hautes)
    -> NeuronWriter analyse -> Claude enrichit -> WordPress republie

BOUCLE 2 — CRÉER DU NEUF (après-midi)
  gsc_veille_brief : GSC dit QUOI écrire + veille dit AVEC QUELLE MATIÈRE
    -> agent choisit sujet GSC prioritaire -> lit sources veille -> NeuronWriter -> rédige -> publie
```

---

## Modèle de combinaison GSC + veille (clé de la boucle 2)

- **GSC = QUOI écrire** (le pilote). Sujets réellement recherchés par votre audience, triés : `OPPORTUNITE` > `TENDANCE` > `STRIKING`.
- **Veille (blogwatcher) = AVEC QUELLE MATIÈRE.** Une fois le sujet GSC choisi, rattacher les articles récents pertinents.
- **Matching anti-faux-positif** : exiger 2+ mots communs OU un mot spécifique >= 6 lettres.
- **Fenêtre de matching** : `veille_articles(days=3650)` pour le matching (pertinence prime), section "veille chaude" filtre à 21 jours.

---

## PITFALLS

- **BUG TRONCATURE** : `enrich_with_claude` ne doit PAS tronquer le contenu (`content[:7000]`). Envoyer `{content}` complet + `max_tokens: 16000`. La troncature produit du contenu dégradé (seconde moitié réécrite à l'aveugle).
- **Modèle** : utiliser `claude-sonnet-4-5-20250929`, pas Haiku. Haiku fait baisser le score NeuronWriter.
- **Timeout HTTP** : Sonnet régénérant un article complet dépasse 60s. `timeout=300` obligatoire.
- **QUOTA NeuronWriter mensuel** : TOUJOURS réutiliser les `query_id` existants (cache) plutôt que recréer. Quota se reset en début de mois.
- **Format du token GSC** : utiliser `Credentials.from_authorized_user_file(TOKEN)` + `creds.refresh(Request())` si `not creds.valid`. Re-écrire le token après refresh : `open(TOKEN,'w').write(creds.to_json())`.
- **GSC 403** : utiliser `sc-domain:votre-domaine.com`, PAS `https://votre-domaine.com/`.
- **Cloudflare WordPress** : User-Agent `Mozilla/5.0` obligatoire sur toutes les requêtes REST.
- **Script cron Hermes** : chemin `script=` doit être RELATIF à `~/.hermes/scripts/`.

---

## Règles de validation (optimisation existant)
- **RÈGLE STRICTE : (re)publier UNIQUEMENT si le score NeuronWriter monte d'au moins +5.** Jamais si le score baisse, stagne, ou progresse trop peu.
- Constante `MIN_GAIN = 5` dans `optimize_page`.
- Logger CHAQUE tentative dans `seo_history.jsonl` avec `published: true/false`.
- Max 2-3 cycles d'enrichissement par page.

## Suivi post-publication
Attendre 2-4 semaines avant de mesurer l'impact GSC. Comparer DEUX fenêtres distinctes (AVANT / APRÈS modif) sur les mêmes requêtes, pas une moyenne globale.

## Rollback via révisions WordPress
WordPress conserve toutes les révisions via l'API REST :
1. `GET {base}/posts/{id}/revisions?context=edit` (le `context=edit` est OBLIGATOIRE)
2. Choisir la dernière révision dont `modified < DATE_CUTOFF`
3. Lire : `GET {base}/posts/{id}/revisions/{rev}?context=edit&_fields=content`
4. Restaurer : `POST {base}/posts/{id}` avec `{content: raw, status: 'publish'}`

## Style rédaction (articles)
- PAS de tirets longs/cadratins. Utiliser virgules, parenthèses, deux-points.
- Éviter le mot "rituel".
- Publication directe, pas de cycle de validation intermédiaire.
