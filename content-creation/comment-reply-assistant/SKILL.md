---
name: comment-reply-assistant
description: Sorts an export of comments into questions, praise, criticism and spam, then drafts replies in the creator's own voice for human approval. Use when a creator has a pile of comments to answer.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [comments, community, replies, creators, social-media]
    category: content-creation
    requires_toolsets: [terminal]
---

# Comment Reply Assistant

Turns a pile of comments into a short, sorted reply sheet. The agent drafts replies that sound like you. Nothing is posted: you read, edit and publish every reply yourself.

## When to use

- You exported comments from a video, post or newsletter and want to answer them without spending an evening on it.
- You want questions answered first, spam ignored, and critical comments flagged for a careful human reply.
- You want replies that match your usual tone instead of generic "Thanks for watching!" text.

## Requirements

- Python 3 (standard library only). No account, no API key, no internet.
- A comments file: a CSV with a column named `comment`, `text`, `message` or `body` (an `author` or `username` column is optional), or a plain text file with one comment per line.
- Optional: 3 to 5 replies you have really written before, so the agent can copy your tone. Without them, ask the user for two or three adjectives describing their voice (for example "warm, short, a bit funny").

## Usage

1. Ask the user for the comments file and, if possible, a few past replies of theirs. Do not invent a voice.
2. Sort the comments:

```bash
python3 scripts/triage_comments.py comments.csv --out reply_sheet.csv --summary
```

3. Read `reply_sheet.csv`. Each row has `category` (question, praise, criticism, spam, other), a short `reason`, `needs_human_care`, an empty `draft_reply` and `status` set to `draft`. The sorting is rule based (English and French keywords), so re-check it: move a row to another category if it is clearly wrong.
4. Write the `draft_reply` for each row, following these rules:
   - **question**: answer it directly in the first sentence. If the answer needs facts you do not have (prices, dates, personal details), write `[YOU: fill in ...]` instead of guessing.
   - **praise**: one specific, short thank-you that refers to something in the comment. Avoid copy-pasted phrases across rows.
   - **criticism**: only a calm draft, marked `needs_human_care`. If the point is fair, acknowledge it. If it is wrong, give the fact politely. Never argue, never get sarcastic. If the wording is abusive, leave the draft empty and suggest hiding or ignoring it.
   - **spam**: no reply. List these separately so the user can report or delete them.
   - **other**: reply only if there is something to say, otherwise leave empty.
   - Match length and punctuation habits of the user's past replies. Do not promise anything (refunds, dates, features) on the user's behalf. Do not pretend to be a different person or to have read things the user has not.
5. Show the user the sheet grouped by category, questions first, with the number of rows in each group. Keep `status` as `draft` until the user says a reply is approved, then change it to `approved`.
6. Tell the user clearly: replies are suggestions, they must be posted by hand (or with the platform's own tools). If a reply mentions a sponsor or product, remind them to keep the collaboration disclosed.

## Example output

Command output:

```
Wrote 4 rows to reply_sheet.csv
# Comment triage

Total comments: 4
- question: 1
- praise: 1
- criticism: 1
- spam: 1
- other: 0
- needing extra care: 1
```

Reply sheet after drafting (shortened):

```
id,author,comment,category,needs_human_care,draft_reply,status
1,alice,"Great video, I learned a lot!",praise,no,"Thank you Alice, glad the editing tips helped!",draft
2,bob,Can you do one on lighting?,question,no,"Yes, lighting is on my list. [YOU: add a date or say 'no date yet']",draft
3,carol,"Too long, clickbait title.",criticism,yes,"Fair point on the length, I will tighten the next one. [YOU: check tone]",draft
4,dave,sub4sub follow me,spam,no,,draft
```

## Limits

- Sorting uses simple keyword rules, not understanding. Irony, mixed messages ("great video but wrong") and languages other than English and French can be misfiled. Always review.
- Identical messages of 20 characters or more are treated as spam, even if a fan really did post twice.
- The script never contacts any platform and never posts. It also does not download comments; you provide the export.
- It does not give legal advice and cannot tell you whether a comment breaks a platform's rules.
- Replies drafted by the agent are only as close to your voice as the examples you provide.

## Testing

```bash
python3 scripts/triage_comments.py --selftest
```

Expected last line: `selftest OK`. A real CSV run (4 invented comments, see Example output) produced the sorted sheet shown above.

Tested on Hermes v0.23.1 on 2026-11-16 (script selftest and a CSV run). The agent drafting step was not scored automatically.
