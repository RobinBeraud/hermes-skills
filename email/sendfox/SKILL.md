---
name: sendfox
category: email
description: Gère les listes email, contacts, campagnes et automatisations SendFox via l'API. Intégration avec WooCommerce, WordPress et workflows marketing.
tags: [email, marketing, newsletter, automation, woocommerce]
requires:
  env_vars:
    - SENDFOX_API_KEY
  python_packages:
    - requests
---

# Skill: SendFox

## Description
Gestion des listes email, contacts, campagnes et automatisations **SendFox** via l'API officielle.

## Authentification
- **API Token** : `SENDFOX_API_KEY` dans `.env`
- **Base URL** : `https://api.sendfox.com`
- **Rate Limits** : 60 requêtes/minute

## Endpoints Principaux

### 1. Listes
- `GET /lists` — lister les listes (id, name, subscriber_count)
- `POST /lists` — créer une liste
- `DELETE /lists/{id}` — supprimer

### 2. Contacts
- `GET /contacts?limit=100&offset=0` — lister avec pagination
- `POST /contacts` — ajouter un contact
- `PUT /contacts/{id}` — mettre à jour
- `DELETE /contacts/{id}` — supprimer

Exemple body ajout :
```json
{
  "email": "contact@example.com",
  "first_name": "Prénom",
  "lists": [LIST_ID],
  "tags": ["VIP", "Client"],
  "custom_fields": {"formation": "Manager 3.0"}
}
```

### 3. Campagnes
- `GET /campaigns` — lister
- `POST /campaigns` — créer
- `POST /campaigns/{id}/send` — envoyer
- `GET /campaigns/{id}/stats` — open_rate, click_rate, unsubscribe_rate

### 4. Automatisations
- `GET /automations` — lister (lecture seule via API, création uniquement dans l'UI)

### 5. Analytics
- `GET /lists/{id}/growth` — croissance des abonnés (30 jours)

## Fonctions Python clé en main

```python
import os, requests, re

BASE = "https://api.sendfox.com"
HEADERS = {"Authorization": f"Bearer {os.getenv('SENDFOX_API_KEY')}"}

def list_lists():
    r = requests.get(f"{BASE}/lists", headers=HEADERS)
    data = r.json()
    return data['data'] if isinstance(data, dict) and 'data' in data else data

def add_contact(email, list_name, tags=None, first_name=None, custom_fields=None):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("Email invalide")
    lists = list_lists()
    list_id = next((l["id"] for l in lists if l["name"] == list_name), None)
    if not list_id:
        raise ValueError(f"Liste '{list_name}' introuvable")
    body = {"email": email, "lists": [list_id], "status": "subscribed"}
    if first_name: body["first_name"] = first_name
    if tags: body["tags"] = tags
    if custom_fields: body["custom_fields"] = custom_fields
    return requests.post(f"{BASE}/contacts", headers={**HEADERS, "Content-Type": "application/json"}, json=body).json()

def create_campaign(name, subject, content, list_name, scheduled_at=None):
    lists = list_lists()
    list_id = next((l["id"] for l in lists if l["name"] == list_name), None)
    body = {"name": name, "subject": subject, "content": content, "list_ids": [list_id]}
    if scheduled_at: body["scheduled_at"] = scheduled_at
    return requests.post(f"{BASE}/campaigns", headers={**HEADERS, "Content-Type": "application/json"}, json=body).json()

def send_campaign(campaign_id):
    return requests.post(f"{BASE}/campaigns/{campaign_id}/send", headers=HEADERS).json()

def campaign_stats(campaign_id):
    return requests.get(f"{BASE}/campaigns/{campaign_id}/stats", headers=HEADERS).json()
```

## Exemples d'usage

### Lister les listes
```python
lists = list_lists()
for lst in lists:
    count = lst.get("email_count") or lst.get("contact_count") or lst.get("subscribed_contacts_count", "?")
    print(f"- {lst['name']} ({count} abonnés)")
```

### Ajouter un contact après un achat
```python
add_contact(
    email="client@example.com",
    list_name="Ma Liste",
    tags=["Client", "Formation_Agile"],
    custom_fields={"formation": "Manager 3.0", "date_achat": "2026-01-01"}
)
```

### Créer et envoyer une campagne
```python
campaign = create_campaign(
    name="Lancement Formation",
    subject="Nouvelle session disponible !",
    content="<html><body><h1>Inscrivez-vous</h1></body></html>",
    list_name="Ma Liste",
    scheduled_at="2026-09-01T09:00:00Z"
)
send_campaign(campaign["id"])
```

## Pitfalls

1. **Rate Limiting** : 60 req/min — `time.sleep(1)` en boucle
2. **Doublons** : vérifier `search_contacts(email=...)` avant ajout
3. **Structure API variable** : subscriber count peut être `email_count`, `contact_count`, ou `subscribed_contacts_count`
4. **Automatisations** : API en lecture seule, création uniquement via UI
5. **Phone Numbers** : non supportés par SendFox
6. **Contenu en prod** : toujours utiliser des données RÉELLES (articles WP via REST API), jamais de contenu factice/hardcodé
7. **NeuronWriter** : scorer le HTML est un bonus, jamais bloquant. Si erreur/quota → dégrader en silence et envoyer quand même
