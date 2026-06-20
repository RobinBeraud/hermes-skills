#!/usr/bin/env python3
import urllib.request, json, os, subprocess, re

def call_claude(prompt):
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2000,
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
    return resp["content"][0]["text"].strip()

def extract_json(text):
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip ```json ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]+?)```', text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass
    # Find first { ... } block
    match = re.search(r'\{[\s\S]+\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None

# Get commit context
commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode().strip()
changed_files = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"]).decode().strip()

# Skip if only workflow files changed
non_workflow = [f for f in changed_files.splitlines() if not f.startswith(".github")]
if not non_workflow:
    print("Only workflow files changed, skipping Dev.to post.")
    exit(0)

# Read changed skill files
skill_content = ""
for f in non_workflow:
    if "SKILL.md" in f and os.path.exists(f):
        content = open(f).read()[:2000]
        skill_content += f"\n\n## {f}\n{content}"

prompt = f"""You are a technical writer for Dev.to. A commit was pushed to the hermes-skills GitHub repo (open-source skills for the Hermes AI agent).

Commit: {commit_msg}
Changed files: {changed_files}

Skill content:
{skill_content if skill_content else "(general update)"}

Write a Dev.to article (300-500 words) in English.
- Engaging title
- Intro: what problem this solves
- How it works (short code/markdown snippet if relevant)
- How to use it with Hermes AI agent
- CTA to star the GitHub repo

Respond with ONLY a JSON object — no prose, no markdown fences:
{{"title": "article title here", "body_markdown": "full article body in markdown", "tags": ["hermes", "ai", "automation", "opensource"]}}"""

text = call_claude(prompt)
article = extract_json(text)

if not article:
    print("Failed to parse JSON from Claude. Raw response:")
    print(text[:500])
    exit(1)

print(f"Title: {article['title']}")

# Publish to Dev.to
payload2 = json.dumps({
    "article": {
        "title": article["title"],
        "body_markdown": article["body_markdown"],
        "published": True,
        "tags": article.get("tags", ["hermes", "ai", "automation", "opensource"])[:4]
    }
}).encode()

req2 = urllib.request.Request(
    "https://dev.to/api/articles",
    data=payload2,
    headers={
        "api-key": os.environ["DEVTO_API_KEY"],
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; HermesSkillsBot/1.0; +https://github.com/RobinBeraud/hermes-skills)"
    }
)
resp2 = json.loads(urllib.request.urlopen(req2).read())
url = resp2.get("url", "")
if url:
    print(f"Published: {url}")
else:
    print(f"Dev.to error: {resp2}")
    exit(1)
