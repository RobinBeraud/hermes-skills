# Hermes Skills

A curated collection of skills for [Hermes AI Agent](https://github.com/Hermes-Agent/hermes) — plug-and-play modules that extend what your AI agent can do.

## What are Hermes Skills?

Skills are Markdown files that give Hermes contextual knowledge and step-by-step instructions to interact with external services. Think of them as "how-to guides" your agent reads before taking action.

## Available Skills

### 🔍 SEO
- **[NeuronWriter](seo/neuronwriter/SKILL.md)** — Content analysis and optimization via NeuronWriter API. Analyze keywords, get recommendations, score content, and automate your SEO workflow.

### 🌐 WordPress
- **[WPBakery](wordpress/wpbakery/SKILL.md)** — Build professional WordPress pages with WPBakery shortcodes. Includes ready-to-use templates (hero, features, CTA, FAQ, testimonials) and REST API integration.

### 📢 Marketing
- **[Waitlister](marketing/waitlister/SKILL.md)** — Manage waitlists via Waitlister.me API. Add subscribers, check status, log views, and build launch strategies.

## How to Use

1. Copy the skill file(s) you need into your Hermes `~/.hermes/skills/` directory
2. Set the required environment variables (listed in each skill)
3. Ask Hermes to use the skill

## Contributing

PRs welcome! Skills should:
- Use environment variables for all credentials (never hardcode)
- Include working code examples
- Document all API endpoints used

## License

MIT
