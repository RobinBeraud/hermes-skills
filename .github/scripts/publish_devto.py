#!/usr/bin/env python3
import urllib.request, json, os, subprocess

# Get commit context
commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode().strip()
changed_files = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"]).decode().strip()

# Read changed skill files
skill_content = ""
for f in changed_files.splitlines():
    if "SKILL.md" in f and os.path.exists(f):
        content = open(f).read()[:2000]
        skill_content += f"\n\n## {f}\n{content}"

prompt = f"""You are a technical writer for Dev.to. A new commit was pushed to the hermes-skills GitHub repo (open-source skills for the Hermes AI agent).

Commit: {commit_msg}
Changed files: {changed_files}

Skill content:
{skill_content if skill_content else "(general update — no skill files changed)"}

Write a short Dev.to article (300-500 words) in English about this update.
- Engaging title (not clickbait)
- Brief intro: what problem this solves
- How it works (include a short code/markdown snippet if relevant)
- How to use it with the Hermes AI agent
- End with a CTA to star the repo on GitHub

Return ONLY valid JSON with this exact structure:
{{"title": "...", "body_markdown": "...", "tags": ["tag1","tag2","tag3","tag4"]}}

Tags must only use: hermes, ai, automation, productivity, seo, wordpress, marketing, opensource, python, agile"""

payload = json.dumps({
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 1500,
    "messages": [{"role": "user", "content": prompt}]
}).encode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=payload,
    headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
)
resp = json.loads(urllib.request.urlopen(req).read())
text = resp["content"][0]["text"].strip()

# Strip markdown code block if present
if "```" in text:
    parts = text.split("```")
    text = parts[1]
    if text.startswith("json"):
        text = text[4:]
    text = text.strip()

article = json.loads(text)
print(f"Title: {article['title']}")

# Publish to Dev.to
payload2 = json.dumps({
    "article": {
        "title": article["title"],
        "body_markdown": article["body_markdown"],
        "published": True,
        "tags": article["tags"][:4]
    }
}).encode()

req2 = urllib.request.Request(
    "https://dev.to/api/articles",
    data=payload2,
    headers={
        "api-key": os.environ["DEVTO_API_KEY"],
        "Content-Type": "application/json"
    }
)
resp2 = json.loads(urllib.request.urlopen(req2).read())
url = resp2.get("url", "")
if url:
    print(f"Published: {url}")
else:
    print(f"Error: {resp2}")
