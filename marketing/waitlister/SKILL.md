# Skill: waitlister

## Description
Gestion des waitlists Corporate Mavericks via Waitlister.me — consulter les inscrits, ajouter des leads, analyser les sources de trafic.

## Quand l'utiliser
- Consulter les inscrits d'une waitlist
- Ajouter manuellement un inscrit (lead entrant, import)
- Analyser d'ou viennent les inscrits (LinkedIn, Google, direct...)
- Strategiser pour maximiser les inscriptions

---

## Auth
**Header :** `X-Api-Key: $WAITLISTER_API_KEY`
**Base URL :** `https://waitlister.me/api/v1/waitlist/{waitlist-key}`

## Waitlists connues

| Waitlist | Key | URL |
|----------|-----|-----|
| Corporate Mavericks (principale) | `YOUR_WAITLIST_KEY` | waitlist.your-site.com |

---

## Endpoints

### Lister les inscrits
```bash
curl -s "https://waitlister.me/api/v1/waitlist/YOUR_WAITLIST_KEY/subscribers" \
  -H "X-Api-Key: $WAITLISTER_API_KEY"
# Parametres optionnels: ?page=1&limit=20
```

Response: `{success, data: {subscribers[], total, page, limit, pages}}`

Chaque subscriber contient:
- `id`, `email`, `name`, `position`, `points`
- `referral_code`, `referred_by`, `referral_count`
- `referring_domain` (linkedin.com, google.com, direct...)
- `country`, `city`, `timezone`
- `joined_at` (timestamp ms), `joined_with`
- `deliverability` (probably_deliverable, risky, etc.)

### Obtenir un inscrit (par email ou ID)
```bash
curl -s "https://waitlister.me/api/v1/waitlist/YOUR_WAITLIST_KEY/subscribers/user@example.com" \
  -H "X-Api-Key: $WAITLISTER_API_KEY"
```

### Ajouter un inscrit
```bash
curl -s -X POST "https://waitlister.me/api/v1/waitlist/YOUR_WAITLIST_KEY/sign-up" \
  -H "X-Api-Key: $WAITLISTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "lead@example.com",
    "name": "Prenom Nom",
    "metadata": {
      "referred_by": "code-parrain",
      "referring_domain": "linkedin.com"
    }
  }'
```

### Mettre a jour un inscrit
```bash
curl -s -X PUT "https://waitlister.me/api/v1/waitlist/YOUR_WAITLIST_KEY/subscribers/SUBSCRIBER_ID" \
  -H "X-Api-Key: $WAITLISTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Nouveau Nom"}'
```

### Logger une vue (analytics)
```bash
curl -s -X POST "https://waitlister.me/api/v1/waitlist/YOUR_WAITLIST_KEY/log-view" \
  -H "X-Api-Key: $WAITLISTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"visitor_id": "uid-unique", "metadata": {"referring_domain": "google.com"}}'
```

---

## Analyse des inscrits actuels (juin 2026)

5 inscrits sur Corporate Mavericks :
- Sources : LinkedIn (3), direct (2)
- Pays : France, Canada, Maroc, Suisse, Espagne
- Tous "probably_deliverable"
- Systeme de referral actif (chaque inscrit a un referral_code)

---

## Strategies pour maximiser les inscriptions

### Referral viral
Chaque inscrit recoit un `referral_code` unique. Partager ce code dans les emails de confirmation fait monter le score (`points`) et la position dans la file.
- Encourager le partage dans l email de bienvenue
- Mettre en avant le gain de position pour chaque parrainage

### Sources a exploiter
- LinkedIn est la source #1 (60%) : continuer posts LinkedIn avec CTA vers la waitlist
- Creer une campagne Google Ads ciblant les managers / RH
- Ajouter le lien waitlist dans la bio LinkedIn de Robin

### Contenu
- Publier des teasers du contenu de la formation (extraits Management 3.0)
- Creer urgence : "X personnes devant vous dans la liste"
- Email drip aux inscrits pour les garder engages

### Partenariats
- Contacter les inscrits deja convertis (arnaudgarnier@gc-agiles.fr = cabinet agile) pour cross-promo
