---
name: hook-lab
description: Generate 10 hooks for a post or video, then score them on explicit criteria (specificity, curiosity, promise kept) and flag over-promising. Use when a creator needs an opening line for a post, Reel, short or video.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hooks, copywriting, social-media, video, creators]
    category: content-creation
    requires_toolsets: [terminal]
---

# Hook Lab

Write ten different openings for one piece of content, score them against clear criteria, and keep only hooks the content can actually deliver on.

## When to use

- "Give me hooks for this video / post / newsletter."
- A draft exists but the first line feels flat.
- You want to compare options with reasons instead of gut feeling.

## Requirements

- Python 3 (standard library only). No API key, no network.
- The user's topic, the audience, and ideally the draft text or script (the "body").

## Usage

1. **Collect the inputs.** Ask for: topic, platform (short video, LinkedIn, newsletter...), target audience, and the body text if it exists. If the body does not exist yet, ask for 3 facts that will really be in it (a number, a result, a story).
2. **Write 10 hooks**, each using a different angle. Use at least these angles: a concrete result, a mistake, a question, a contrast ("I expected X, got Y"), a first-person moment, a myth to correct, a specific number, a "before / after", a direct audience callout, a plain statement. Rules:
   - Use only facts the user gave. Never invent figures, results, quotes or testimonials.
   - No fake urgency, no "secret", no promise the body cannot keep.
   - If the post is sponsored, the hook must not hide that (leave the disclosure to the post itself, do not contradict it).
3. **Save them** one per line to a text file, e.g. `/tmp/hooks.txt`.
4. **Score them:**

   ```bash
   python3 scripts/hook_score.py /tmp/hooks.txt --body /tmp/draft.txt
   ```

   Without `--body` the "promise kept" check is skipped. Add `--json` for machine output.
5. **Review with judgment.** The script is a rough filter. For the top 3, the agent adds its own read on each criterion:
   - *Specificity*: could this hook only be about this content?
   - *Curiosity*: does it open a question the viewer wants closed?
   - *Promise kept*: does the body answer it within the content? If not, rewrite or drop it.
6. **Present** a short ranked list: top 3 with one-line reasons, then the rest in a compact list. Offer one rewrite of the weakest-but-promising hook. The user decides.

### Scoring criteria (as implemented)

- **Specificity (0-10):** numbers, units of time or quantity, named things, a first-hand situation, sensible length; penalty for vague words ("amazing", "secret", "tips") and for very short or very long lines.
- **Curiosity (0-10):** a question, contrast words ("but", "instead", "until"), gap words ("why", "mistake", "wrong").
- **Promise risk (0-10, lower is better):** risky phrases ("guaranteed", "overnight", "you won't believe"), absolute words, shouting; with `--body`, numbers in the hook that do not appear in the body, and low overlap between the hook's key words and the body.
- **Total:** average of specificity, curiosity, and (10 - promise risk).

## Example output

```
1. [7.3] spec 9 | curiosity 3 | risk 0  Why my 12 minute video lost viewers at minute 3
2. [7.0] spec 7 | curiosity 4 | risk 0  I rewrote my intro 4 times, but the first draft won.
3. [5.0] spec 9 | curiosity 2 | risk 6  I made 500 euros in 2 days
     - number(s) in hook not found in body: 500
     - body covers only 0% of the hook's key words
4. [1.7] spec 1 | curiosity 2 | risk 8  Amazing secret hacks nobody tells you!!
     - vague words: amazing, hacks, secret
     - risky phrases: nobody tells you
     - shouting (caps/!!)
```

## Limits

- The scoring is keyword and pattern based, English only. It cannot judge tone, humor, or whether a hook fits your voice, and it does not predict views.
- A high score is not proof a hook will perform; test against your own analytics.
- The overlap check compares words, not meaning: a body can mention the words and still not deliver.
- Hook writing itself relies on the agent's judgment and the facts you provide.

## Testing

```bash
python3 scripts/hook_score.py --selftest
```

Expected: `selftest OK`. Also run it on a small hooks file with and without `--body` and check that a hook containing a number missing from the body gets flagged.

Status: tested (self-test and a sample hooks file, no network needed). Tested on Hermes on 2026-11-11 (local script run).
