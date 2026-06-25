---
name: photogpt
description: "Générer des photos réalistes de personnes via PhotoGPT AI — portraits, headshots, mises en scène — en utilisant des modèles personnels entraînés (ex: modèle Robin) ou des modèles publics. Upload possible dans Mural via le flow assets."
---

# PhotoGPT — Génération de photos réalistes

## Rôle
Générer des photos réalistes de personnes (portraits, headshots, mises en scène professionnelles ou créatives) via l'API PhotoGPT. Supporte les modèles personnels entraînés sur des photos réelles et les modèles publics.

## Auth
- **Base URL** : `https://developer.photogptai.com/api`
- **Headers obligatoires** :
  - `Authorization: Bearer $PHOTOGPT_API_KEY`
  - `API-Version: 1`
  - `Content-Type: application/json`
- Credentials dans `~/.hermes/.env` :
  - `PHOTOGPT_API_KEY` — clé API
  - `PHOTOGPT_MODEL_ROBIN` — ID du modèle personnel Robin

⚠️ **Cloudflare bloque `urllib` Python** — utiliser `curl` via `subprocess` (voir exemples ci-dessous).

## Modèles disponibles

### Modèle personnel Robin
- **ID** : `019abc8d-e721-7066-80ee-e7286e27d007` (var: `PHOTOGPT_MODEL_ROBIN`)
- **Status** : `ready`
- Homme, 45 ans, caucasien, yeux verts
- Coût : **10 crédits** par image

### Modèles publics (gratuits ou moins chers)
| modelID | Description |
|---|---|
| `nanobanana` | Modèle de base rapide |
| `nanobanana-pro` | Qualité supérieure |
| `nanobanana-2` | V2 améliorée |
| `seedream` | Style photoréaliste |
| `seedream-4_5` | Version 4.5 |
| `seedream-5-lite` | Version 5 lite |
| `gpt-image-2` | Basé sur GPT Image 2 (OpenAI) |

## Endpoints

### Santé
```
GET /ping
→ {"message": "pong!", "status": "OK"}
```

### Modèles
```
GET  /models           — lister tous les modèles disponibles
GET  /models/{id}      — détail d'un modèle (status: ready/training/failed)
```

### Génération d'images (asynchrone)
```
POST /images/generation  → retourne un jobId
GET  /jobs/{jobId}       → poller jusqu'à status "completed"
```

### Upscaling
```
POST /images/upscaling   → améliorer la résolution d'une image existante
```

### Génération vidéo
```
POST /videos/generation  → générer une vidéo à partir d'une image
GET  /videos             → lister les vidéos générées
```

### Assets images
```
POST /images   — uploader une image de référence
GET  /images   — lister les assets
```

## Paramètres de génération

### Avec modèle personnel (ex: Robin)
| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `modelID` | string | ✅ | ID du modèle entraîné |
| `prompt` | string | ✅ | Description de la photo souhaitée |
| `numImages` | integer | ❌ | Nombre d'images (défaut: 1) |
| `width` | integer | ❌ | Largeur en pixels |
| `height` | integer | ❌ | Hauteur en pixels |
| `enhanceFace` | boolean | ❌ | Amélioration du visage (recommandé: true) |
| `seed` | integer | ❌ | Graine pour résultats reproductibles |
| `steps` | integer | ❌ | Nombre d'étapes de génération |
| `styleStrength` | number | ❌ | Force du style si image de référence |
| `inputImageId` | string | ❌ | ID d'une image de référence uploadée |

### Avec modèle public
| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `modelID` | string | ✅ | Ex: `seedream`, `gpt-image-2` |
| `prompt` | string | ✅ | Description de l'image |
| `aspectRatio` | string | ❌ | `1:1`, `16:9`, `9:16`, `3:4`, etc. |
| `numImages` | integer | ❌ | 1 à 4 |
| `referenceImageURLs` | array | ❌ | URLs publiques d'images de référence |

## Fonction clé en main (Python + curl)

```python
import subprocess, json, time

def photogpt(prompt, model_id=None, width=1024, height=1024, enhance_face=True, num_images=1):
    """
    Génère une image PhotoGPT et retourne l'URL du résultat.
    Utilise curl pour contourner Cloudflare (urllib bloqué).
    """
    env = {}
    with open('/home/ubuntu/.hermes/.env') as f:
        for line in f:
            k, _, v = line.strip().partition('=')
            if k: env[k] = v

    KEY = env['PHOTOGPT_API_KEY']
    model_id = model_id or env['PHOTOGPT_MODEL_ROBIN']
    BASE = 'https://developer.photogptai.com/api'

    def api(method, path, body=None):
        cmd = ['curl', '-s', '-X', method,
               '-H', f'Authorization: Bearer {KEY}',
               '-H', 'API-Version: 1',
               '-H', 'Content-Type: application/json',
               f'{BASE}{path}']
        if body:
            cmd += ['-d', json.dumps(body)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout)

    # Lancer la génération
    payload = {
        'modelID': model_id,
        'prompt': prompt,
        'numImages': num_images,
        'width': width,
        'height': height,
        'enhanceFace': enhance_face,
    }
    resp = api('POST', '/images/generation', payload)
    if resp.get('status') == 'NOK':
        raise Exception(f"PhotoGPT error: {resp.get('message')} — {resp.get('reason', '')}")

    job_id = resp['result']['jobId']
    print(f'Job lancé: {job_id}')

    # Poller jusqu'à completion
    for i in range(30):
        time.sleep(5)
        status = api('GET', f'/jobs/{job_id}')
        st = status.get('result', {}).get('status', '?')
        print(f'  [{i+1}] {st}')
        if st == 'completed':
            images = status['result'].get('images', [])
            return [img['url'] for img in images]
        if st in ('failed', 'error'):
            raise Exception(f'Job failed: {status}')

    raise Exception('Timeout — job non terminé en 150s')
```

## Exemples d'utilisation

### Portrait professionnel de Robin
```python
urls = photogpt(
    'professional headshot, business agile coach, confident smile, '
    'white background, navy suit, corporate style',
    enhance_face=True
)
print(urls[0])
```

### Robin en contexte de formation
```python
urls = photogpt(
    'Robin presenting in front of a whiteboard, agile training workshop, '
    'energetic pose, casual business attire, modern office background',
    width=1280, height=720  # format paysage pour slides
)
```

### Robin pour les réseaux sociaux
```python
urls = photogpt(
    'Robin smiling with arms crossed, outdoor urban background, '
    'LinkedIn profile photo style, professional yet approachable',
    width=800, height=800  # format carré LinkedIn
)
```

### Modèle public (sans crédits personnels)
```python
urls = photogpt(
    'minimalist flat vector illustration of agile team sprint planning',
    model_id='seedream',
    width=1024, height=1024
)
```

## Crédits
- **10 crédits** par image avec modèle personnel
- Vérifier le solde : `GET /ping` ne retourne pas les crédits — vérifier sur https://platform.photogptai.com
- Si `"message": "insufficient credits"` → recharger sur la plateforme

## Combiner avec Mural
Après génération PhotoGPT, injecter l'image dans un mural via le flow assets Mural :

```python
import urllib.request, base64

def photogpt_to_mural(prompt, x, y, w, h, mural_id, mural_token):
    """Génère une photo PhotoGPT et la place dans un mural Mural.co."""
    # 1. Générer avec PhotoGPT
    img_urls = photogpt(prompt)
    img_data = urllib.request.urlopen(img_urls[0], timeout=30).read()

    # 2. Uploader dans Mural (flow presigned Azure Blob)
    asset = json.loads(urllib.request.urlopen(urllib.request.Request(
        f'https://app.mural.co/api/public/v1/murals/{mural_id}/assets',
        data=json.dumps({'fileExtension': 'png'}).encode(),
        headers={'Authorization': f'Bearer {mural_token}', 'Content-Type': 'application/json'}
    )).read())['value']

    urllib.request.urlopen(urllib.request.Request(
        asset['url'], data=img_data, method='PUT',
        headers={**asset['headers'], 'Content-Type': 'image/png'}
    ), timeout=30)

    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f'https://app.mural.co/api/public/v1/murals/{mural_id}/widgets/image',
        data=json.dumps({'x': x, 'y': y, 'width': w, 'height': h, 'name': asset['name']}).encode(),
        headers={'Authorization': f'Bearer {mural_token}', 'Content-Type': 'application/json'}
    ), timeout=15).read())['value']['id']
```

## Cas d'usage Hermes
- "Génère une photo de moi en tenue de consultant pour LinkedIn"
- "Crée une photo de Robin présentant devant un tableau Kanban"
- "Génère une photo de Robin en chef cuisinier pour le post Corporate Mavericks"
- "Ajoute une photo de Robin dans le mural CHANEL Day 1"
- "Génère 3 variantes de headshot pour mon profil"

## Erreurs fréquentes
- **`insufficient credits`** : recharger sur https://platform.photogptai.com
- **`403 error code: 1010`** : Cloudflare bloque urllib Python — toujours utiliser `curl` via subprocess
- **`status: training`** : modèle pas encore prêt — poller `GET /models/{id}` jusqu'à `ready`
- **Job timeout** : génération peut prendre 30-90s — patience avec le polling

## Setup
1. Créer un compte sur https://platform.photogptai.com
2. Générer une clé API dans les settings
3. Entraîner un modèle personnel avec 10-20 photos
4. Récupérer le model ID depuis `GET /models`
5. Ajouter dans `~/.hermes/.env` :
   ```
   PHOTOGPT_API_KEY=ta-cle-api
   PHOTOGPT_MODEL_ROBIN=ton-model-id
   ```
