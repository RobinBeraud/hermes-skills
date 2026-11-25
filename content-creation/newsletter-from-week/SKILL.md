---
name: newsletter-from-week
description: Build a weekly newsletter draft from the posts, videos and episodes a creator published this week, with a subject line, short intro, pick of the week and links; use it when you want a consistent letter without rewriting everything by hand.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [newsletter, content-creation, weekly, email, creators]
    category: content-creation
    requires_toolsets: [terminal]
---

# Newsletter From the Week

Turns a list of what you published in the last seven days into a ready-to-edit newsletter. The agent writes only from the titles, links and notes you provide. It never invents numbers, quotes or results.

## When to use

- You publish across several places (blog, video channel, podcast, social posts) and want one weekly letter.
- You have a list or export of your posts and need a draft in a few minutes.
- You want a repeatable structure: subject options, intro, pick of the week, list of posts, closing question.

## Requirements

- Python 3 (standard library only). No API key, no network access.
- A CSV file with a header row and these columns: `date` (YYYY-MM-DD), `title`, `url`, `summary` (optional, one line), `favorite` (optional, put `yes` on the post you want to feature).
- If you have no CSV, ask the agent to build one from a pasted list. It must ask for any missing date or link instead of guessing.

## Usage

1. Collect the week's posts into `posts.csv`:

   ```
   date,title,url,summary,favorite
   2026-03-02,Five lessons from my first video,https://example.com/lessons,What I would redo,yes
   2026-03-04,Behind the edit,https://example.com/edit,A look at my editing flow,
   ```

2. Generate the skeleton (the default window is the 7 days ending today):

   ```
   python3 scripts/week_digest.py posts.csv --end 2026-03-08 --name "Maker Notes"
   ```

   The script filters by date, removes duplicate links (ignoring case, trailing slash and tracking parameters), skips rows with a bad date or link, and prints notes on stderr. Exit code is 1 if no post matched.

3. The agent then fills the placeholders, following these rules:
   - SUBJECT OPTIONS: three subject lines, each under 60 characters, built only from the titles. No fake urgency, no all caps, no "you won't believe".
   - INTRO: two sentences in the creator's voice. No claim about audience size or results unless the creator supplied it.
   - Every `TODO: summary missing` line: ask the creator for one sentence, or write a neutral line that restates only the title. Never invent content.
   - OUTRO: one question inviting a reply.
   - Sponsored or affiliated posts: label them clearly ("Sponsored", "Contains affiliate links") if the creator flagged them.

4. Show the final draft and the list of notes. Let the creator copy it into their email tool. The skill does not send anything.

## Example output

```
# Maker Notes: week of 2026-03-02

SUBJECT OPTIONS: ...
INTRO: ...

## Pick of the week
[Five lessons from my first video](https://example.com/lessons)
What I would redo

## This week's posts
- **[Five lessons from my first video](https://example.com/lessons)** (2026-03-02): What I would redo
- **[Behind the edit](https://example.com/edit)** (2026-03-04): A look at my editing flow

OUTRO: ...
```

## Limits

- It does not fetch your posts or check that links work. The creator provides the list.
- Only one featured post is used; extra `favorite` marks are reported and ignored.
- The date filter works on whole days, with no time zones.
- Subject lines and intro are written by the agent, so quality depends on the model. Always read before sending.
- Not connected to any email service.

## Testing

```
python3 scripts/week_digest.py --selftest
```

The selftest checks date filtering, duplicate removal, bad-row handling, the pick of the week and missing-summary flags, then prints `SELFTEST OK`. A real run on a two-row CSV and a CSV with a missing column (clear error, exit 1) were also checked.

Tested on Hermes v0.23.1 on 2026-11-25 (script only; the agent-written parts were not evaluated automatically).
