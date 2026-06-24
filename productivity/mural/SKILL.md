---
name: mural
description: "Créer, lire, modifier et organiser des murals (tableaux de collaboration visuelle mural.co) via l'API Mural — workspaces, rooms, widgets (stickies, formes, textes, images, connecteurs)."
---

# Mural — Collaboration visuelle & murals

## Rôle
Créer, lire, modifier et organiser des murals (tableaux de collaboration visuelle) via l'API Mural. Gérer les workspaces, rooms, widgets (stickies, formes, textes, images).

## Auth
- **Base URL** : `https://app.mural.co/api/public/v1`
- **Header** : `Authorization: Bearer $MURAL_ACCESS_TOKEN`
- Token stocké dans `~/.hermes/.env` sous `MURAL_ACCESS_TOKEN`
- Token valide 15 min — si 401, rafraîchir avec `MURAL_REFRESH_TOKEN` (voir section Refresh)

## Refresh du token (quand 401)

⚠️ IMPORTANT : Mural EXIGE l'authentification client en **HTTP Basic** (header
`Authorization: Basic base64(client_id:client_secret)`). Mettre `client_id` /
`client_secret` dans le body renvoie `400 invalid_client`. Seuls `grant_type`
et `refresh_token` vont dans le body.

```
POST https://app.mural.co/api/public/v1/authorization/oauth2/token
Authorization: Basic base64(MURAL_CLIENT_ID:MURAL_CLIENT_SECRET)
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=$MURAL_REFRESH_TOKEN
```
→ Nouveau `access_token` (valide 900s) + `refresh_token` rotatif à resauvegarder.

### Client prêt à l'emploi (recommandé)
Un client Python gère tout ça automatiquement (refresh Basic + réécriture des
tokens dans `.env` + retry 401) : `~/.hermes/scripts/mural_api.py`
```bash
python3 ~/.hermes/scripts/mural_api.py refresh                # force un refresh
python3 ~/.hermes/scripts/mural_api.py get /workspaces        # appel GET auto-refresh
python3 ~/.hermes/scripts/mural_api.py get /workspaces/<wsId>/murals
```
Ne PAS sourcer le token dans une commande shell inline : il est caviardé par le
DLP et casse l'appariement des guillemets. Passer par le script (il lit `.env`).

### Workspaces connus (compte Robin)
- `agilecookbook4150` — **Corporate mavericks** (workspace principal, ~100+ murals)
- `zenikabordeaux5861` — Mathilde Pro (OLD_ZBDX)

## Endpoints principaux

### Workspaces
- `GET /workspaces` — lister les workspaces
- `GET /workspaces/{workspaceId}` — détail d'un workspace

### Rooms
- `GET /workspaces/{workspaceId}/rooms` — lister les rooms
- `POST /workspaces/{workspaceId}/rooms` — créer une room
- `GET /rooms/{roomId}` — détail d'une room

### Murals
- `GET /workspaces/{workspaceId}/murals` — lister les murals d'un workspace
- `GET /rooms/{roomId}/murals` — lister les murals d'une room
- `POST /rooms/{roomId}/murals` — créer un mural
- `GET /murals/{muralId}` — détail d'un mural
- `PATCH /murals/{muralId}` — modifier titre/description
- `DELETE /murals/{muralId}` — supprimer un mural
- `POST /murals/{muralId}/duplicate` — dupliquer un mural

### Widgets (stickies, formes, textes, images, connecteurs)
- `GET /murals/{muralId}/widgets` — lister tous les widgets
- `POST /murals/{muralId}/widgets/sticky-note` — créer un sticky
- `POST /murals/{muralId}/widgets/shape` — créer une forme
- `POST /murals/{muralId}/widgets/text` — créer un texte
- `POST /murals/{muralId}/widgets/image` — créer une image (URL)
- `POST /murals/{muralId}/widgets/connector` — créer un connecteur
- `PATCH /murals/{muralId}/widgets/{widgetId}` — modifier un widget
- `DELETE /murals/{muralId}/widgets` — supprimer des widgets (body: `{"widgetIds": [...]}`)

### Membres
- `GET /murals/{muralId}/members` — lister les membres
- `POST /murals/{muralId}/members` — inviter des membres

### Templates
- `GET /workspaces/{workspaceId}/templates` — lister les templates
- `POST /murals/{muralId}/duplicate` avec `templateId` — créer depuis template

## Exemples d'utilisation

### Lister les murals d'un workspace
```python
import urllib.request, json, os

TOKEN = os.environ["MURAL_ACCESS_TOKEN"]
WS_ID = "mon-workspace-id"

req = urllib.request.Request(
    f"https://app.mural.co/api/public/v1/workspaces/{WS_ID}/murals",
    headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
)
data = json.loads(urllib.request.urlopen(req).read())
for m in data.get("value", []):
    print(m["id"], m["title"])
```

### Créer un sticky note
```python
import urllib.request, json, os

TOKEN = os.environ["MURAL_ACCESS_TOKEN"]
MURAL_ID = "123456789"

body = json.dumps({
    "x": 100, "y": 100,
    "width": 200, "height": 200,
    "text": "Mon idée",
    "style": {"backgroundColor": "#FFF176"}  # jaune
}).encode()

req = urllib.request.Request(
    f"https://app.mural.co/api/public/v1/murals/{MURAL_ID}/widgets/sticky-note",
    data=body,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)
resp = json.loads(urllib.request.urlopen(req).read())
print("Widget créé:", resp["value"]["id"])
```

### Créer un mural dans une room
```python
import urllib.request, json, os

TOKEN = os.environ["MURAL_ACCESS_TOKEN"]
ROOM_ID = "ma-room-id"

body = json.dumps({
    "title": "Nouveau mural",
    "width": 4000,
    "height": 3000
}).encode()

req = urllib.request.Request(
    f"https://app.mural.co/api/public/v1/rooms/{ROOM_ID}/murals",
    data=body,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)
resp = json.loads(urllib.request.urlopen(req).read())
print("Mural créé:", resp["value"]["id"], resp["value"]["visitorsSettings"]["link"])
```

## Cas d'usage typiques pour Hermes
- "Crée un mural de rétrospective dans la room Scrum"
- "Ajoute 5 stickies avec nos risques projet sur le mural X"
- "Liste les murals du workspace et trouve celui sur la roadmap"
- "Duplique le mural template de sprint planning"
- "Montre moi les widgets du mural de dernière rétro"

## Erreurs fréquentes
- **401** : Token expiré → rafraîchir avec `MURAL_REFRESH_TOKEN`
- **403** : Scope insuffisant (`murals:write` requis pour créer/modifier)
- **404** : ID mural/room/workspace incorrect — vérifier avec un GET d'abord
- **429** : Rate limit atteint — attendre quelques secondes

## Setup initial (première fois)
1. Créer une app sur https://app.mural.co/me/apps
2. OAuth flow pour obtenir `access_token` + `refresh_token`
3. Ajouter dans `~/.hermes/.env` :
   ```
   MURAL_ACCESS_TOKEN=eyJ...
   MURAL_REFRESH_TOKEN=eyJ...
   MURAL_CLIENT_ID=ton-client-id
   MURAL_CLIENT_SECRET=ton-client-secret
   ```
