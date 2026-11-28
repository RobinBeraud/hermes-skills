---
name: linkedin-post-reviewer
description: Reviews a LinkedIn (or similar) post draft for hook, layout, readability, link and hashtag use and call to action, using countable checks plus a short editorial pass. Use before publishing a post.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [linkedin, social-media, copywriting, editing, content-creation]
    category: content-creation
    requires_toolsets: [terminal]
---

# LinkedIn Post Reviewer

Gives a draft post a structured review: measurable checks from a small script, then a human-style editorial read by the agent. It never predicts reach and never invents numbers.

## When to use
- A creator, freelancer or marketer has a post draft and wants a second pair of eyes before publishing.
- You want to compare two versions of the same post.
- Works for other text-first platforms too (adjust the hook length).

## Requirements
- Python 3 (standard library only). No API key, no network.
- The draft saved as a plain text file, or pasted by the user (write it to a temp file first).

## Usage
1. Save the draft to `/tmp/post.txt` (exactly as the user wrote it, do not edit it).
2. Run the counter:
   ```
   python3 scripts/post_review.py /tmp/post.txt
   python3 scripts/post_review.py /tmp/post.txt --hook-chars 120   # stricter hook limit
   python3 scripts/post_review.py /tmp/post.txt --json              # machine-readable
   ```
   The default hook limit (140 characters) is an approximation, not an official platform value. Ask the user to adjust it if they know what their feed shows before the "see more" cut.
3. Read the flags, then do the editorial pass yourself, in this order:
   - **Hook**: does the first line make a specific promise, tension or question? Is it understandable without the rest?
   - **One idea**: can the post be summed up in one sentence? If not, say which ideas compete.
   - **Proof**: does the post contain a concrete example, step or detail, or only claims? Do not add facts the user did not provide.
   - **Ending**: is there ONE clear ask (a question, a link, a reply)?
   - **Honesty**: if the post promotes a product, partnership or paid collaboration, check that it is disclosed. Flag it if not.
4. Report in this format:
   - Verdict in one line (ready / small fixes / rework the hook).
   - Top 3 changes, most valuable first, each with a short reason.
   - Two alternative first lines, written in the user's voice, clearly labelled as suggestions.
   - Do not rewrite the entire post unless asked.

## Example output
```
Characters: 390 | Words: 69 | Paragraphs: 4
First line (172 chars): Most of my posts flop because I write the ending first ...
Avg sentence: 9.9 words | Longest: 34 | Longest paragraph: 34
URLs: 1 | Hashtags: 2 | Emojis: 0

Flags:
- HOOK: first line is 172 chars (> 140); the part shown before a 'see more' cut may end mid-thought.
- LINK: a URL is in the body; some platforms may show posts with links differently. ...
```
Then the agent adds: verdict, top 3 changes, two alternative first lines.

## Limits
- The script only counts: lengths, links, hashtags, emojis, a short list of stock phrases, the presence of a question or call-to-action word near the end. It cannot judge tone, truth or originality.
- Stock-phrase and call-to-action word lists are English only and small.
- Thresholds are rules of thumb, not platform rules. Nothing here predicts impressions or engagement.
- Link advice is a prompt to test on your own account, not a proven effect.

## Testing
```
python3 scripts/post_review.py --selftest
```
Expected: `selftest OK`. The selftest checks a deliberately bad post (long hook, wall of text, cliché, link, many hashtags) and a clean one.
Tested on Hermes (script run directly, Python 3) on 2026-11-28: selftest passed and a sample post using example.com produced the output shown above. The editorial pass is agent instructions and was not tested separately.
