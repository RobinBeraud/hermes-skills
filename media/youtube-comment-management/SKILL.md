---
name: youtube-comment-management
description: "Lister, modérer et répondre aux commentaires de chaînes YouTube via l'API v3, avec maillage SEO vers vos sites WordPress."
version: 1.0
category: media
tags: [youtube, comments, moderation, seo]
requires:
  python_packages:
    - google-api-python-client
    - google-auth
---

# YouTube Comment Management

Workflow réutilisable pour lister, modérer et répondre aux commentaires de chaînes YouTube, et y ajouter du maillage SEO.

## Scripts réutilisables (dans ~/.hermes/scripts/)

- `yt_cm_pending.py` — liste les commentaires SANS réponse de la chaîne. Sortie JSON: `[{id, date, author, likes, replies, videoId, text}]`
- `yt_cm_act.py` — agir sur un commentaire : `reply <id> "<texte>"` poste une réponse, `reject <id>` masque (modération)
- `yt_pending_count.py` — compte les commentaires récents (< 6 mois) sans réponse

Tous ces scripts construisent le client via `Credentials(...).refresh(Request())` en lisant depuis le fichier token (access_token + refresh_token + client_id + client_secret + token_uri + scope).

## Pièges critiques (vérifiés en réel)

### 1. Scope `youtube.force-ssl` requis pour lister/écrire les commentaires
Lister tous les commentaires d'une chaîne (`commentThreads().list(allThreadsRelatedToChannelId=...)`) ET écrire (reply/reject) exigent le scope `https://www.googleapis.com/auth/youtube.force-ssl`.
- Diagnostic rapide : `python3 -c "import json;d=json.load(open('TOKEN'));print(d.get('scope') or d.get('scopes'))"`. Chercher `force-ssl` dans la sortie.
- Si le scope manque : régénérer le token OAuth avec ce scope.

### 2. Token-swap pour LIRE les commentaires publics d'une autre chaîne
La lecture de commentaires publics ne demande pas d'être propriétaire. Pour lire une chaîne sans son propre token force-ssl, utiliser le token d'une autre chaîne qui a ce scope avec `allThreadsRelatedToChannelId=<chaîne cible>`. Fonctionne pour la LECTURE, pas pour poster au nom de la chaîne cible.

### 3. Faux positif « Not all requested scopes were granted »
Le warning `Not all requested scopes were granted` affiché par google-auth peut être un FAUX POSITIF : l'écriture peut fonctionner malgré le message. Filtrer ce warning dans la sortie. NE PAS le confondre avec un vrai 403.

### 4. Compter « récents » = parcourir par date, pas par vidéos récentes
Les commentaires récents arrivent sur d'ANCIENNES vidéos. Pour compter les commentaires < N mois, parcourir `commentThreads().list(allThreadsRelatedToChannelId=..., order="time")` du plus récent au plus ancien et s'arrêter sous le cutoff. Ne pas se baser sur les vidéos publiées récemment.

## Maillage SEO dans les réponses

Quand on répond à un commentaire légitime, insérer autant que possible UN lien pertinent vers un article réel de vos sites.

- **Charger le catalogue d'URLs RÉELLES** via le post-sitemap WordPress :
  `curl -s -L -A "Mozilla/5.0" --max-time 25 https://votre-site.com/post-sitemap.xml`
- **Ne JAMAIS inventer une URL.** Utiliser uniquement des `<loc>` présentes dans le sitemap. UN seul lien par réponse. Si aucun article ne colle, répondre SANS lien.

## Politique de modération

- **Légitime** (positif, vraie question, remarque constructive) : répondre, ton chaleureux/pro/bref, dans la langue du commentaire. + maillage SEO si pertinent.
- **Scam/spam** (crypto, seed phrase, phishing, pub) : `reject`, pas de réponse.
- **Toxique/haineux/insulte** : `reject` automatique. Le noter dans le rapport.
- **Ambigu / critique argumentée** : NE PAS masquer par défaut. Signaler pour arbitrage humain. Dans le doute, choisir ambigu plutôt que masquer.

## Style rédactionnel (réponses)
- PAS de tirets longs/cadratins (—) : utiliser virgules, parenthèses, deux-points.
- Rester naturel, jamais "corporate creux".
- Répondre FR si le commentaire est FR, EN s'il est EN.
