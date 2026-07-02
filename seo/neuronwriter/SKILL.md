---
name: neuronwriter
description: "Analyse SEO de mots-clés et scoring de contenu via NeuronWriter API. Automate your SEO pipeline from keyword research to WordPress publishing."
---

# Skill: neuronwriter

## Description
Analyse SEO de mots-clés et scoring de contenu via NeuronWriter (Contadu).

## Quand l'utiliser
- Optimiser un article pour le SEO avant publication
- Trouver les termes sémantiques à inclure dans un contenu
- Scorer un texte existant pour voir son potentiel SEO
- Analyser les concurrents sur un mot-clé

---

## 🚦 SEUIL DE PUBLICATION (règle ferme — your-site.com)

**Score `evaluate-content` ≥ 55 obligatoire avant de publier** (viser 60). C'est une des conditions du gate qualité décrit dans le skill `wpbakery` (avec : WPBakery, 0 tiret long `—`/`–`, 0 mot « rituel », image de une). Si < 55 : enrichir (FAQ People Also Ask + cas d'usage) AVANT publication. Exception documentée : le plafond sur mots-clés transactionnels (voir pitfall plus bas) — dans ce cas seulement, publier au score plafond une fois tous les termes `content_basic_w_ranges` couverts.

---

## Auth
**Header :** `X-API-KEY: $NEURONWRITER_API_KEY`
**Base URL :** `https://app.neuronwriter.com/neuron-api/0.5/writer`
**Methode :** POST uniquement, Content-Type: application/json

---

## Endpoints

### Lister les projets
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/list-projects \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Creer une analyse (new-query)
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/new-query \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "management 3.0",
    "language": "fr",
    "search_engine": "google.fr",
    "project_id": "ID_PROJET"
  }'
```
Retourne un query_id. Attendre status="done" avant get-query (polling toutes les 30s).

### Recuperer les recommandations (get-query)
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/get-query \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query_id": "QUERY_ID"}'
```
Contient: termes recommandes, questions PAA, concurrents, score cible.

### Lister les analyses
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/list-queries \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "ID_PROJET"}'
```

### Scorer un contenu (evaluate-content)
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/evaluate-content \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "QUERY_ID",
    "content": "<h1>Titre</h1><p>Contenu HTML de article...</p>"
  }'
```
Retourne un score SEO + termes manquants.

### Importer le contenu dans editeur
```bash
curl -s -X POST https://app.neuronwriter.com/neuron-api/0.5/writer/import-content \
  -H "X-API-KEY: $NEURONWRITER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "QUERY_ID",
    "content": "<h1>Titre</h1><p>Contenu...</p>"
  }'
```

---

## Workflow typique : rediger un article SEO optimise

1. **Creer une analyse** : new-query avec le mot-cle cible
2. **Attendre status=done** : polling get-query toutes les 30s
3. **Extraire les recommandations** : termes obligatoires, questions PAA
4. **Rediger l article** en integrant les termes recommandes
5. **Scorer** : evaluate-content pour verifier le score
6. **Importer** : import-content pour sauvegarder dans NeuronWriter

---

## ⚠️ Noms de champs réels de l'API (vérifiés en prod)

La doc historique de ce skill utilisait des noms de champs qui RENVOIENT UNE ERREUR. Valeurs réellement acceptées par l'API 0.5 :

| Action | Champ doc (❌) | Champ réel (✅) |
|---|---|---|
| new-query | `project_id` | `project` |
| new-query | `search_engine` | `engine` |
| new-query | `language: "fr"` | `language: "French"` (nom complet) |
| get-query / evaluate-content | `query_id` | `query` |
| evaluate-content / import-content | `content` | `html` |

- `new-query` renvoie `{"query": "<id>", ...}` (pas `query_id`).
- Statut de polling : la valeur de fin est `ready` (pas seulement `done`). Boucler get-query jusqu'à `status` ∈ {ready, done}.
- `get-query` retourne `terms_txt` (sous-clés : `title`, `desc_title`, `h1`, `h2`, `content_basic`, `content_basic_w_ranges`, `content_extended`), `ideas.people_also_ask`, et `metrics.word_count.target` (longueur cible).
- `evaluate-content` retourne `{"content_score": NN}`. Viser ≥ 60 ; enrichir si < 55 (ajouter une FAQ reprenant les People Also Ask + des cas d'usage augmente le score et la longueur).

⚠️ **PITFALL — plafond de score sur mots-clés transactionnels.** Pour un mot-clé à intention « fiche métier / salaire / avenir / offres d'emploi » (SERP dominée par les job boards : Indeed, Welcome to the Jungle, etc.), un article éditorial/d'opinion plafonne souvent autour de 43-47 même avec TOUS les termes cibles couverts et la bonne longueur. Ce n'est PAS un défaut de rédaction : le corpus de référence NeuronWriter est constitué d'annonces d'emploi structurées, impossible à matcher avec un article de blog. **Ne pas sur-bourrer le texte de mots-clés pour gratter 5 points** (ça dégrade la lecture et déclenche du keyword stuffing). Une fois tous les termes `content_basic_w_ranges` couverts dans leurs fourchettes mini et le `scrum master`/terme principal SOUS son plafond max (ex. 14x), considérer le score acceptable et publier. Vérifier la couverture terme par terme avec un petit script Python (count par terme vs fourchette `content_basic_w_ranges`) plutôt que de deviner.
- Construire les payloads JSON via `python3 -c "...json.dumps..."` + `--data @fichier.json` pour éviter les soucis d'échappement (accents, guillemets).

## Notes
- Consomme les credits mensuels du plan (identique a l interface)
- Plan Gold minimum requis
- language: "French", "English", etc. (nom complet, pas le code ISO)
- engine: "google.fr", "google.com", "google.co.uk", etc.
- Project ID : `YOUR_NW_PROJECT_ID` (ex: French / google.fr)

## Publier l'article optimisé sur WordPress
Pour le pipeline complet veille → analyse SEO → rédaction Gutenberg → publication WordPress (your-site.com), voir `references/wordpress-publishing.md`.

## Ré-optimiser des articles DÉJÀ classés (GSC → NeuronWriter → WP)
Pour retravailler des articles existants bien positionnés afin de gagner des
places (boucle quotidienne pilotée par Google Search Console, scripts
`~/.hermes/scripts/seo/`, crons système), voir `references/gsc-reoptimization-loop.md`.

⚠️ Règle ferme issue de la prod : sur une RÉ-optimisation d'article existant,
ne republier QUE si le score `evaluate-content` monte d'au moins +5. Un petit
LLM fait souvent BAISSER le score d'un article déjà dense ; republier quand même
dégrade le contenu jour après jour. Et toujours mesurer l'effet ranking
après coup (compare position GSC avant/après sur fenêtres distinctes, pas une
moyenne 28 j).
