---
name: fmp
category: finance
description: Accède aux données financières via Financial Modeling Prep (FMP) — cours boursiers, profil d'entreprise, bilans, ratios, actualités, screener, indices, crypto et forex.
tags: [finance, bourse, actions, crypto, forex, analyse-fondamentale, marché]
requires:
  env_vars:
    - FMP_API_KEY
---

# Skill: Financial Modeling Prep (FMP)

## Description
Accès complet aux données financières via l'API **Financial Modeling Prep** (endpoints stables v2025+).

**Base URL** : `https://financialmodelingprep.com/stable`  
**Auth** : paramètre `apikey` dans chaque requête (valeur : variable d'env `FMP_API_KEY`)

> 🔑 Crée ton compte et récupère ta clef sur [financialmodelingprep.com](https://financialmodelingprep.com)

## Quand utiliser ce skill
- "Quel est le cours de [TICKER] ?"
- "Donne-moi le profil / les financials / les ratios de [entreprise]"
- "Quelles sont les actualités sur [TICKER] ?"
- "Compare [TICKER1] et [TICKER2]"
- "Quel est le PE ratio / rendement dividende de [entreprise] ?"
- "Cherche des actions avec une cap > X et un PE < Y" (screener)
- "Quel est le cours du Bitcoin / EUR/USD ?"
- "Quels sont les indices aujourd'hui (CAC40, S&P500, Nasdaq) ?"
- "Quelles actions ont le plus monté/baissé aujourd'hui ?"

## Installation

Ajoute ta clef dans `~/.hermes/.env` :
```bash
FMP_API_KEY=ta_clef_ici
```

## Fonction utilitaire de base

```python
import os, urllib.request, json

API = "https://financialmodelingprep.com/stable"
KEY = os.environ["FMP_API_KEY"]

def fmp(path, **params):
    params["apikey"] = KEY
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{API}/{path}?{qs}"
    return json.loads(urllib.request.urlopen(url).read())
```

## Exemples d'utilisation

### Cours en temps réel
```python
prix = fmp("quote", symbol="AAPL")
print(f"{prix[0]['symbol']}: ${prix[0]['price']} ({prix[0]['changesPercentage']:+.2f}%)")
```

### Profil d'entreprise
```python
p = fmp("profile", symbol="TSLA")[0]
print(f"{p['companyName']} — {p['sector']} — Cap: ${p['marketCap']:,.0f}")
print(f"CEO: {p['ceo']} | {p['description'][:200]}")
```

### Compte de résultat
```python
income = fmp("income-statement", symbol="MSFT", period="quarter", limit=4)
for q in income:
    print(f"{q['date']}: Revenue ${q['revenue']:,.0f} | Net ${q['netIncome']:,.0f}")
```

### Ratios fondamentaux
```python
r = fmp("ratios", symbol="AAPL", period="annual", limit=1)[0]
print(f"PE: {r['priceEarningsRatio']:.1f} | ROE: {r['returnOnEquity']*100:.1f}%")
print(f"Marge nette: {r['netProfitMargin']*100:.1f}% | Dividende: {r['dividendYield']*100:.2f}%")
```

### Screener d'actions
```python
results = fmp("stock-screener",
    marketCapMoreThan=10000000000,
    peRatioLowerThan=20,
    sector="Technology",
    country="US",
    limit=20)
for s in results:
    print(f"{s['symbol']} — PE: {s['peRatio']:.1f} — Cap: ${s['marketCap']:,.0f}")
```

### Indices boursiers
```python
indices = fmp("quotes/index")
for idx in indices:
    if idx['symbol'] in ['^GSPC', '^IXIC', '^DJI', '^FCHI']:
        print(f"{idx['name']}: {idx['price']:,.2f} ({idx['changesPercentage']:+.2f}%)")
```

### Crypto & Forex
```python
btc = fmp("quote", symbol="BTCUSD")[0]
eur = fmp("quote", symbol="EURUSD")[0]
print(f"BTC: ${btc['price']:,.2f} | EUR/USD: {eur['price']:.4f}")
```

### Actualités
```python
news = fmp("stock-news", tickers="AAPL,MSFT", limit=5)
for n in news:
    print(f"[{n['publishedDate'][:10]}] {n['title']}")
```

### Gainers / Losers du jour
```python
gainers = fmp("stock_market/gainers")
for s in gainers[:5]:
    print(f"{s['ticker']}: +{s['changesPercentage']:.1f}%")
```

### DCF (valorisation intrinsèque)
```python
dcf = fmp("discounted-cash-flow", symbol="AAPL")[0]
print(f"DCF estimé: ${dcf['dcf']:.2f} vs cours actuel: ${dcf['stockPrice']:.2f}")
```

## Symboles utiles
| Type | Symboles |
|------|----------|
| Indices | `^GSPC` (S&P500), `^IXIC` (Nasdaq), `^DJI` (Dow Jones), `^FCHI` (CAC40) |
| Crypto | `BTCUSD`, `ETHUSD`, `SOLUSD` |
| Forex | `EURUSD`, `GBPUSD`, `USDJPY` |

### Chercher un ticker
```python
results = fmp("search", query="LVMH", limit=5)
for r in results:
    print(f"{r['symbol']} — {r['name']} ({r['exchangeShortName']})")
```

## Documentation
- [FMP Developer Docs](https://site.financialmodelingprep.com/developer/docs)
- Rate limit : dépend du plan souscrit
