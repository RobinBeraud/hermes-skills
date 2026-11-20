# Dépôts GitHub à connaître pour Hermes

> **Référence, 20 novembre 2026.** Les étoiles et la date de dernière activité ont été relevées ce jour-là sur l'API GitHub : elles bougent vite, à revérifier avant de citer un chiffre.
>
> À lire avec le [catalogue MCP / API](HERMES_TOOLS_CATALOG_MASTER.md) et le [guide du second cerveau](INSTRUCTIONS_SECOND_BRAIN_VPS_HERMES.md).

## Comment s'en servir

- **Ne pas tout installer.** Choisir un ou deux dépôts qui répondent à un besoin réel, les tester, puis garder ce qui sert.
- **Lire avant d'installer.** Un skill ou un MCP s'exécute avec les droits de ton agent. Parcours le `SKILL.md` ou le README, et passe-le au scanner de sécurité (voir SkillSpector ci-dessous).
- **Préférer les dépôts vivants** : activité récente, issues traitées, licence claire.

Pour installer un skill compatible Hermes depuis GitHub :

```bash
hermes skills inspect <propriétaire>/<dépôt>/<chemin-du-skill>   # aperçu, n'installe rien
hermes skills install <propriétaire>/<dépôt>/<chemin-du-skill>
```

---

## 1. Les incontournables de la formation

| Dépôt | ⭐ | À quoi ça sert | Pourquoi l'avoir |
|---|---:|---|---|
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 264 904 | L'agent Hermes lui-même | La source officielle : installation, documentation, mises à jour |
| [anthropics/skills](https://github.com/anthropics/skills) | 197 935 | Les skills officiels d'Anthropic (format Agent Skills) | Le modèle de référence pour écrire un bon skill |
| [RobinBeraud/hermes-skills](https://github.com/RobinBeraud/hermes-skills) | 10 | 102 skills prêts à l'emploi pour Hermes, un nouveau chaque jour | La bibliothèque de la formation |
| [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector) | 27 029 | Scanner de sécurité pour les skills d'agents : failles, comportements malveillants, injections de prompt | À passer sur tout skill téléchargé avant de l'installer |

## 2. Skills métier à succès

| Dépôt | ⭐ | À quoi ça sert | Pourquoi l'avoir |
|---|---:|---|---|
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 61 647 | Skills marketing : conversion, copywriting, SEO, analytics, croissance | Une équipe marketing complète pour ton agent |
| [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) | 31 072 | Suite SEO : 26 sous-skills et 19 sous-agents (technique, E-E-A-T, schema, GEO, local…) | Audit SEO complet de ton site, porté dans hermes-skills (`seo/seo-suite`) |
| [career-ops-hq/career-ops](https://github.com/career-ops-hq/career-ops) | 83 906 | Agent de recherche d'emploi : scanne les offres, les note de 1 à 5 face à ton CV | Le projet d'origine, très populaire |
| [starMagic/career-ops-hermes](https://github.com/starMagic/career-ops-hermes) | 6 | Career-Ops porté sur Hermes, avec 17 skills natifs | La version prête pour Hermes. Jeune et peu suivie : à tester avant d'en dépendre |
| [wshobson/agents](https://github.com/wshobson/agents) | 42 731 | Agents, skills et commandes pour Claude Code et d'autres outils | Une grande réserve de rôles d'agents dont s'inspirer |

## 3. MCP : donner des mains à ton agent

| Dépôt | ⭐ | À quoi ça sert | Pourquoi l'avoir |
|---|---:|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 92 134 | Serveurs MCP de référence : fichiers, Git, fetch, mémoire, heure… | Les briques de base, maintenues par l'équipe du protocole |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 39 931 | Piloter un vrai navigateur : cliquer, remplir, naviguer | Pour les sites sans API |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | 34 615 | Le MCP officiel de GitHub : dépôts, issues, pull requests, Actions | Pour que ton agent gère ses propres dépôts (sauvegarde, skills) |
| [tavily-ai/tavily-mcp](https://github.com/tavily-ai/tavily-mcp) | 2 499 | Recherche web, extraction et exploration pensées pour les agents | Une recherche web propre, avec un palier gratuit |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 98 302 | Annuaire des serveurs MCP de la communauté | Pour trouver un MCP avant d'en coder un |

## 4. Web, données et automatisation

| Dépôt | ⭐ | À quoi ça sert | Pourquoi l'avoir |
|---|---:|---|---|
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 204 888 | Lire et explorer n'importe quel site, même protégé, en Markdown propre | La veille et l'extraction de contenu (skill `web/firecrawl`) |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 121 596 | Bibliothèque Python d'agents qui naviguent sur le web | Alternative à Playwright pour les tâches web longues |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 211 518 | Automatisation de workflows visuelle, avec de l'IA intégrée | Quand une automatisation fixe suffit, sans agent |
| [public-apis/public-apis](https://github.com/public-apis/public-apis) | 500 441 | Liste collective d'API gratuites | Le réflexe avant de chercher une source de données |
| [JulienTant/blogwatcher-cli](https://github.com/JulienTant/blogwatcher-cli) | 35 | Suivi de blogs et de flux RSS en ligne de commande | Le moteur du skill `research/veille-pro` |

## 5. Second cerveau et contenu

| Dépôt | ⭐ | À quoi ça sert | Pourquoi l'avoir |
|---|---:|---|---|
| [obsidianmd/obsidian-releases](https://github.com/obsidianmd/obsidian-releases) | 23 416 | Versions d'Obsidian et liste officielle des extensions et thèmes | Pour installer Obsidian et choisir ses extensions |
| [Vinzent03/obsidian-git](https://github.com/Vinzent03/obsidian-git) | 12 305 | Synchronise un coffre Obsidian avec Git, automatiquement | Le lien entre ton Obsidian et le second cerveau de Hermes |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 87 310 | Montage vidéo par IA, en HTML, open source | Pour transformer tes contenus en vidéos |

## 6. Pour aller plus loin

| Dépôt | ⭐ | À quoi ça sert |
|---|---:|---|
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 58 428 | Sélection des meilleures ressources pour Claude Code, dont beaucoup réutilisables avec Hermes |
| [RobinBeraud/claude-qa-skills](https://github.com/RobinBeraud/claude-qa-skills) | 0 | 119 skills qualité et développement pour Claude Code (stratégie de test, mutation testing, DORA…) |

---

## Règles de prudence

- **Secrets :** une clé d'API va dans `~/.hermes/.env`, jamais dans un skill, un dépôt ou une conversation.
- **Droits :** un MCP qui agit (navigateur, fichiers, GitHub) est plus sensible qu'une API en lecture seule. Ne lui donner que ce dont il a besoin.
- **Popularité ≠ sécurité :** beaucoup d'étoiles ne garantit rien. Lire, scanner, tester sur un petit périmètre.
- **Licences :** vérifier la licence avant un usage commercial ou une redistribution.
