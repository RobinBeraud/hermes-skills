---
name: note-visual
description: Generate minimalist hand-drawn style diagrams (compare, 2x2 matrix, funnel, steps) as PNG images for social posts such as Substack Notes or LinkedIn
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [image, diagram, social-media, substack, linkedin]
    category: media
    requires_toolsets: [terminal]
---

# Note Visual

Creates simple square (1080x1080) hand-drawn style schemas with exact text (no AI image model, so no misspelled words). Useful as the picture of a one-line social post.

## Requirements
Python 3 and Pillow (`pip install pillow`). The Caveat-Bold font is downloaded on first use to `~/.hermes/assets/` (falls back to another font if the download fails).

## Usage
```bash
python3 scripts/note_visual.py demo ./out                 # one example of each template
python3 scripts/note_visual.py render spec.json out.png   # render your own
```

`spec.json` examples:
```json
{"type":"compare","titre":"Measure impact, not activity","labelA":"Measuring impact","labelB":"Measuring activity","formeA":"croissance","formeB":"stop","axe":"time"}
{"type":"matrix","titre":"Where is your AI?","x":"Usage","y":"Impact","quadrants":["Low use, useful","Used and useful","Neither","Heavy use, low value"],"point":3}
{"type":"funnel","titre":"From spend to value","etapes":["Invest","Adopt","Speed up","Deliver","Impact"]}
{"type":"steps","titre":"Five steps","etapes":["Form","Storm","Norm","Perform","Close"]}
```
Shapes for `compare`: `croissance` (growth), `plateau`, `stop`, `vague`. Funnel/steps accept 3 to 6 stages. Keep labels short (keywords, not sentences).

Set `NOTE_VISUAL_FOOTER` to change the small footer text (default: "schéma illustratif").

## Rules
- These are illustrations of concepts, never real data: do not use them to present invented figures.
- Keep the footer or an equivalent mention so readers do not mistake a sketch for a chart of facts.

## Limits
Fixed 1080x1080 layout; four templates; French keys in the JSON spec (`titre`, `etapes`, `formeA`...).
