---
name: gandi
category: infrastructure
description: Gère les domaines, DNS et emails via l'API Gandi v5. Permet de lister les domaines, consulter/modifier les enregistrements DNS, gérer les boîtes mail et configurer les redirections.
tags: [dns, domaine, gandi, email, infrastructure, hébergement]
requires:
  env_vars:
    - GANDI_API_TOKEN
---

# Skill: Gandi — Domaines & DNS

## Description
Gestion complète des domaines et DNS via l'**API Gandi v5**.

**Base URL** : `https://api.gandi.net/v5`
**Auth** : `Authorization: Bearer $GANDI_API_TOKEN`

## Quand utiliser ce skill
- "Liste mes domaines Gandi"
- "Quel est l'enregistrement DNS de [domaine] ?"
- "Ajoute / modifie un enregistrement DNS sur [domaine]"
- "Quand expire [domaine] ?"
- "Configure un CNAME / A / MX / TXT sur [domaine]"
- "Vérifie la config DNS de [domaine]"
- "Ajoute une redirection mail sur [domaine]"

## Fonction utilitaire

```python
import os, urllib.request, json

BASE = "https://api.gandi.net/v5"
TOKEN = os.environ["GANDI_API_TOKEN"]

def gandi(method, path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        method=method
    )
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return json.loads(body) if body else {}
```

## Exemples

### Lister tous les domaines
```python
domains = gandi("GET", "domain/domains")
for d in domains:
    print(f"{d['fqdn']} — expire: {d.get('dates',{}).get('registry_ends_at','?')[:10]}")
```

### Détails d'un domaine
```python
domain = gandi("GET", "domain/domains/example.com")
print(f"Statut: {domain['status']}")
print(f"Nameservers: {domain.get('nameservers')}")
print(f"Expire: {domain['dates']['registry_ends_at'][:10]}")
```

### Lister les enregistrements DNS
```python
records = gandi("GET", "livedns/domains/example.com/records")
for r in records:
    print(f"{r['rrset_type']:6} {r['rrset_name']:20} -> {r['rrset_values']}")
```

### Ajouter / modifier un enregistrement DNS
```python
# Ajouter un CNAME
gandi("POST", "livedns/domains/example.com/records/www/CNAME", {
    "rrset_values": ["example.com."],
    "rrset_ttl": 3600
})

# Modifier un enregistrement A
gandi("PUT", "livedns/domains/example.com/records/blog/A", {
    "rrset_values": ["1.2.3.4"],
    "rrset_ttl": 300
})
```

### Supprimer un enregistrement DNS
```python
gandi("DELETE", "livedns/domains/example.com/records/old-subdomain/A")
```

### Ajouter un enregistrement TXT (SPF, DKIM, vérification)
```python
gandi("PUT", "livedns/domains/example.com/records/@/TXT", {
    "rrset_values": ["v=spf1 include:_spf.gandi.net ~all"],
    "rrset_ttl": 3600
})
```

### Boîtes mail (Gandi Mail)
```python
mailboxes = gandi("GET", "email/mailboxes/example.com")
for m in mailboxes:
    print(f"{m['login']}@example.com — quota: {m.get('quota_used',0)}/{m.get('quota',0)} Mo")
```

### Redirections mail
```python
redirects = gandi("GET", "email/forwards/example.com")
for r in redirects:
    print(f"{r['source']} -> {r['destinations']}")

gandi("POST", "email/forwards/example.com", {
    "source": "contact",
    "destinations": ["admin@example.com"]
})
```

## Notes
- **LiveDNS** : API DNS principale (`livedns/domains/{fqdn}/records`)
- **TTL recommandé** : 300s pour les changements fréquents, 3600s pour les configs stables
- **Documentation** : https://api.gandi.net/docs/
