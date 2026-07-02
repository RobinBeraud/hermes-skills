<p align="center">
  <h1 align="center">hermes-skills</h1>
  <p align="center">Open-source skills library for <a href="https://github.com/NousResearch/hermes-agent">Hermes AI Agent</a> — plug-and-play integrations for finance, web, marketing and more.</p>
</p>

<p align="center">
  <a href="https://github.com/RobinBeraud/hermes-skills/stargazers"><img src="https://img.shields.io/github/stars/RobinBeraud/hermes-skills?style=flat-square" alt="Stars"></a>
  <a href="https://dev.to/YOUR_DEVTO"><img src="https://img.shields.io/badge/Dev.to-articles-0a0a0a?style=flat-square&logo=devdotto" alt="Dev.to"></a>
  <img src="https://img.shields.io/badge/skills-6-blue?style=flat-square" alt="Skills count">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

---

## What are Hermes Skills?

Skills are Markdown files that give Hermes contextual knowledge and reusable code patterns to interact with external services. Drop a `SKILL.md` into `~/.hermes/skills/` and your agent knows how to use the service.

## Available Skills

### 💹 Finance
| Skill | Description | Requires |
|-------|-------------|----------|
| [FMP](finance/fmp/SKILL.md) | Real-time stock quotes, company fundamentals, income statements, ratios, screener, crypto & forex via Financial Modeling Prep | `FMP_API_KEY` |

### 🌐 Web
| Skill | Description | Requires |
|-------|-------------|----------|
| [Firecrawl](web/firecrawl/SKILL.md) | Scrape any URL to clean Markdown, web search, full-site crawl, dynamic page interaction (clicks/forms), structured JSON extraction | `FIRECRAWL_API_KEY` |

### 📱 WhatsApp
| Skill | Description | Requires |
|-------|-------------|----------|
| [WBizTool](whatsapp/wbiztool/SKILL.md) | Contact lookup and management — find a number by name, identify unknown numbers, stats by country | WhatsApp bridge running |

### 🔍 SEO
| Skill | Description | Requires |
|-------|-------------|----------|
| [NeuronWriter](seo/neuronwriter/SKILL.md) | Content analysis and optimization via NeuronWriter API | `NEURONWRITER_API_KEY` |

### 🌐 WordPress
| Skill | Description | Requires |
|-------|-------------|----------|
| [WPBakery](wordpress/wpbakery/SKILL.md) | Build WordPress pages with WPBakery shortcodes and REST API | WordPress credentials |

### 📢 Marketing
| Skill | Description | Requires |
|-------|-------------|----------|
| [Waitlister](marketing/waitlister/SKILL.md) | Manage waitlists via Waitlister.me API | `WAITLISTER_API_KEY` |

## Quick Start

```bash
# Copy a skill to your Hermes installation
cp -r finance/fmp ~/.hermes/skills/finance/

# Add required env vars
echo "FMP_API_KEY=your_key_here" >> ~/.hermes/.env

# Restart Hermes gateway
hermes gateway restart
```

Then ask Hermes naturally:
- *"What's the current price of Apple stock?"*
- *"Scrape https://example.com and summarize it"*
- *"What's the number of [contact name]?"*

## Contributing

PRs welcome! Skills should:
- Use environment variables for all credentials (never hardcode keys)
- Include working Python code examples
- Follow the SKILL.md format (see any existing skill)

## Auto-publishing

New skills are automatically published as Dev.to articles via GitHub Actions on each push. Follow [dev.to/YOUR_DEVTO](https://dev.to/YOUR_DEVTO) for updates.

## License

MIT