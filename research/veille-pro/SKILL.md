---
name: veille-pro
description: Veille professionnelle quotidienne pour nourrir la création de contenu. Suit une liste de blogs et de flux RSS de référence avec blogwatcher-cli, récupère aussi ceux qui bloquent les serveurs grâce à Firecrawl, puis choisit le sujet le plus actionnable du jour et prépare un brief d'article sourcé, sans doublon avec ce qui est déjà publié. À utiliser pour publier régulièrement (blog, newsletter, LinkedIn) à partir d'une veille fiable plutôt que d'idées au hasard.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [veille, rss, blogs, content, newsletter, editorial, firecrawl]
    category: research
    requires_toolsets: [terminal, web]
---

# Veille pro

Une veille qui tourne toute seule et qui sert à écrire. Hermes surveille les blogs qui comptent dans ton domaine, repère ce qui est frais et pertinent, et te livre chaque jour un brief prêt à rédiger : le sujet, pourquoi il est d'actualité, les sources à lire et l'angle proposé.

Ce skill ne publie rien de lui-même. La rédaction et la publication (WordPress, Substack, LinkedIn…) se branchent ensuite avec tes propres skills.

## When to use
- Tu veux publier régulièrement (article, newsletter, post) sans repartir d'une page blanche.
- Tu veux que chaque contenu s'appuie sur une source récente et réelle, citée correctement.
- Tu veux éviter de traiter deux fois le même sujet.

## Requirements
- `blogwatcher-cli`, un lecteur de flux RSS/Atom en ligne de commande :
  `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
  ou le binaire Linux :
  `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C ~/.local/bin blogwatcher-cli`
- Python 3 (bibliothèque standard seulement) pour le script de secours.
- Facultatif : une clé Firecrawl (`FIRECRAWL_API_KEY` dans `~/.hermes/.env`) pour les blogs qui bloquent les serveurs (Cloudflare, erreur 403). Le palier gratuit suffit pour quelques flux par jour.

## Usage

### 1. Choisir ses sources (une fois)
Demande à l'utilisateur son domaine, son audience et 8 à 15 sources qu'il respecte. Ajoute-les :

```bash
blogwatcher-cli add "Harvard Business Review" https://hbr.org --feed-url https://feeds.feedburner.com/harvardbusiness
blogwatcher-cli add "MIT Sloan Review" https://sloanreview.mit.edu --feed-url http://feeds.feedburner.com/mitsmr
blogwatcher-cli blogs
```

Sans flux connu, `blogwatcher-cli add` tente de le découvrir, sinon il lit la page HTML. Une liste de départ pour le management, l'agilité et la transformation est dans `references/sources-exemple.md`.

### 2. Les blogs qui bloquent le serveur
Certains sites refusent les adresses de serveurs (erreur 403). Ajoute-les quand même dans blogwatcher-cli, puis récupère leur flux par Firecrawl :

```bash
python3 scripts/veille_firecrawl.py --feed "Age of Product=https://age-of-product.com/feed/" --dry-run
python3 scripts/veille_firecrawl.py --feed "Age of Product=https://age-of-product.com/feed/"
```

Le script ajoute les nouveaux articles dans la base de blogwatcher-cli : ils apparaissent ensuite avec les autres. Il ne publie rien et n'envoie aucun e-mail.

### 3. Le scan
```bash
blogwatcher-cli scan
blogwatcher-cli articles
```

À planifier deux fois par jour (par exemple 7h30 et 15h), avec le script Firecrawl lancé juste avant.

### 4. Le brief du jour
À partir des articles non lus :
1. **Filtrer** ce qui parle vraiment à l'audience de l'utilisateur. Écarter les annonces produit, les offres d'emploi et les sujets hors cible.
2. **Choisir un seul sujet**, le plus actionnable et le plus d'actualité. Un sujet repris par plusieurs sources est un bon signal de tendance.
3. **Vérifier les doublons** : comparer avec les 10 à 20 derniers contenus publiés par l'utilisateur (flux RSS de son blog ou API de son CMS). Si le sujet est déjà traité, prendre un angle complémentaire et prévoir un lien vers l'ancien contenu.
4. **Lire la source** en entier, avec l'outil d'extraction web. Ne jamais inventer de citation ni de chiffre : tout ce qui est repris est attribué à sa source.
5. **Livrer le brief** dans ce format :

```text
Sujet : …
Pourquoi maintenant : … (sources et dates)
Angle proposé pour [audience] : …
Mot-clé principal : …
Plan en H2 : …
Sources à citer : titre, auteur, lien
Déjà publié sur le sujet : liens (pour le maillage interne)
```

6. Marquer les articles traités comme lus : `blogwatcher-cli read <id>`.

### 5. Brancher la suite (facultatif)
Le brief peut alimenter un job planifié de rédaction et de publication. Dans ce cas :
- la publication ne doit jamais dépendre d'un outil facultatif, par exemple un outil SEO à quota : s'il échoue, on continue sans lui ;
- vérifier la page publiée (code 200, liens corrects) avant de déclarer le travail fini ;
- respecter le style de l'utilisateur : vocabulaire à éviter, ponctuation, tutoiement ou vouvoiement.

## Pitfalls
- **Flux morts** : un blog qui ne renvoie plus rien pendant des semaines a souvent changé d'adresse de flux. Le vérifier avec `blogwatcher-cli blogs` (date du dernier scan).
- **Trop de sources** : au-delà d'une vingtaine, le brief devient du bruit. Mieux vaut 10 sources excellentes.
- **Copier au lieu de s'inspirer** : reformuler, apporter l'angle de l'utilisateur, citer la source. Ne jamais republier l'article d'un autre.
- **Secrets** : la clé Firecrawl reste dans `~/.hermes/.env`, jamais dans le brief, le contenu ou un dépôt.

## Verification
- `blogwatcher-cli blogs` liste toutes les sources avec une date de scan récente.
- `python3 scripts/veille_firecrawl.py --feed "Nom=URL" --dry-run` affiche des articles sans erreur.
- Le brief cite au moins une source datée de moins de 7 jours, avec son lien.
