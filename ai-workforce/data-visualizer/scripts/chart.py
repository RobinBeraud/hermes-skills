#!/usr/bin/env python3
"""Turn a CSV into a clean, accessible SVG chart (line, bar or horizontal bar), no plotting library needed.

  chart.py data.csv --x month --y revenue[,costs] [--type line|bar|hbar] [--title "..."] [--subtitle "..."]
           [--highlight "2026-06"] [--unit "EUR"] [--out chart.svg] [--width 800] [--height 420]

Design rules built in: one message per chart (put it in --title as a sentence), zero-based axes for bars,
a readable colour-blind-safe palette, direct labels instead of a legend when possible, a highlight colour for the
point that matters and grey for context. The SVG has a <title> and <desc> for screen readers and opens in any browser.
Standard library only.
"""
import argparse, csv, html, math

PALETTE = ['#2563EB', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6', '#0EA5E9']
GREY, INK, MUTED, GRID = '#9CA3AF', '#111827', '#6B7280', '#E5E7EB'


def nice_max(v):
    if v <= 0:
        return 1
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * e >= v:
            return m * e
    return 10 * e


def fmt(v, unit=''):
    a = abs(v)
    s = f'{v / 1e6:.1f}M' if a >= 1e6 else f'{v / 1e3:.1f}k' if a >= 1e4 else (f'{v:.0f}' if a >= 100 or float(v).is_integer() else f'{v:.2f}')
    return s.replace('.0M', 'M').replace('.0k', 'k') + (f' {unit}' if unit else '')


def render(xs, series, kind, title, subtitle, highlight, unit, W, H):
    e = html.escape
    left, right, top, bottom = (150 if kind == 'hbar' else 64), 110 if kind == 'line' else 40, 78 if subtitle else 60, 48
    pw, ph = W - left - right, H - top - bottom
    vmax = nice_max(max(max(v for v in s if v is not None) for s in series.values()))
    vmin = min(0, min(min(v for v in s if v is not None) for s in series.values()))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" font-family="Inter,Segoe UI,Arial,sans-serif">',
           f'<title>{e(title)}</title><desc>{e(subtitle or title)}: ' + '; '.join(f"{e(k)} " + ', '.join(f'{e(x)} {fmt(v, unit)}' for x, v in zip(xs, s) if v is not None) for k, s in series.items()) + '</desc>',
           f'<rect width="{W}" height="{H}" fill="#fff"/>',
           f'<text x="{left}" y="30" font-size="19" font-weight="700" fill="{INK}">{e(title)}</text>']
    if subtitle:
        out.append(f'<text x="{left}" y="54" font-size="13.5" fill="{MUTED}">{e(subtitle)}</text>')
    n = len(xs)
    if kind == 'hbar':
        s = list(series.values())[0]
        bh = ph / n
        for i in range(6):
            v = vmax * i / 5; x = left + pw * v / vmax
            out.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + ph}" stroke="{GRID}"/><text x="{x:.1f}" y="{top + ph + 18}" font-size="11.5" fill="{MUTED}" text-anchor="middle">{fmt(v)}</text>')
        for i, (lab, v) in enumerate(zip(xs, s)):
            y = top + i * bh + bh * 0.15
            c = PALETTE[0] if (not highlight or lab == highlight) else GREY
            w = pw * (v or 0) / vmax
            out.append(f'<text x="{left - 10}" y="{y + bh * 0.42:.1f}" font-size="12.5" fill="{INK}" text-anchor="end" dominant-baseline="middle">{e(lab)}</text>')
            out.append(f'<rect x="{left}" y="{y:.1f}" width="{w:.1f}" height="{bh * 0.7:.1f}" rx="3" fill="{c}"/>')
            out.append(f'<text x="{left + w + 6:.1f}" y="{y + bh * 0.42:.1f}" font-size="12" fill="{INK}" dominant-baseline="middle">{fmt(v or 0, unit)}</text>')
        out.append('</svg>')
        return '\n'.join(out)
    span = vmax - vmin
    Y = lambda v: top + ph * (1 - (v - vmin) / span)
    for i in range(6):
        v = vmin + span * i / 5
        out.append(f'<line x1="{left}" y1="{Y(v):.1f}" x2="{left + pw}" y2="{Y(v):.1f}" stroke="{GRID}"/><text x="{left - 8}" y="{Y(v) + 4:.1f}" font-size="11.5" fill="{MUTED}" text-anchor="end">{fmt(v)}</text>')
    step = max(1, math.ceil(n / 12))
    slot = pw / n
    for i, x in enumerate(xs):
        if i % step == 0 or i == n - 1:
            out.append(f'<text x="{left + slot * (i + 0.5):.1f}" y="{top + ph + 20}" font-size="11.5" fill="{MUTED}" text-anchor="middle">{e(x)}</text>')
    k = len(series)
    for si, (name, s) in enumerate(series.items()):
        col = PALETTE[si % len(PALETTE)]
        if kind == 'bar':
            bw = slot * 0.72 / k
            for i, v in enumerate(s):
                if v is None:
                    continue
                c = col if (not highlight or xs[i] == highlight or k > 1) else GREY
                x = left + slot * i + slot * 0.14 + bw * si
                y0, y1 = Y(max(v, 0)), Y(min(v, 0))
                out.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1 - y0, 0.5):.1f}" rx="2" fill="{c}"><title>{e(name)} {e(xs[i])}: {fmt(v, unit)}</title></rect>')
                if highlight and xs[i] == highlight:
                    out.append(f'<text x="{x + bw / 2:.1f}" y="{y0 - 6:.1f}" font-size="12" font-weight="700" fill="{INK}" text-anchor="middle">{fmt(v, unit)}</text>')
        else:
            pts = [(left + slot * (i + 0.5), Y(v)) for i, v in enumerate(s) if v is not None]
            out.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{col}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>')
            for i, v in enumerate(s):
                if v is not None and highlight and xs[i] == highlight:
                    cx, cy = left + slot * (i + 0.5), Y(v)
                    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{col}" stroke="#fff" stroke-width="2"/><text x="{cx:.1f}" y="{cy - 10:.1f}" font-size="12" font-weight="700" fill="{INK}" text-anchor="middle">{fmt(v, unit)}</text>')
            lx, ly = pts[-1]
            out.append(f'<text x="{lx + 8:.1f}" y="{ly + 4:.1f}" font-size="12.5" font-weight="600" fill="{col}">{e(name)}</text>')
    if kind == 'bar' and k > 1:
        for si, name in enumerate(series):
            out.append(f'<rect x="{W - right - 120}" y="{12 + si * 18}" width="10" height="10" fill="{PALETTE[si % len(PALETTE)]}"/><text x="{W - right - 104}" y="{21 + si * 18}" font-size="12" fill="{INK}">{e(name)}</text>')
    out.append('</svg>')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv'); ap.add_argument('--x', required=True); ap.add_argument('--y', required=True)
    ap.add_argument('--type', choices=['line', 'bar', 'hbar'], default='line'); ap.add_argument('--title', default='')
    ap.add_argument('--subtitle', default=''); ap.add_argument('--highlight'); ap.add_argument('--unit', default='')
    ap.add_argument('--sort', action='store_true', help='sort hbar descending'); ap.add_argument('--out', default='chart.svg')
    ap.add_argument('--width', type=int, default=800); ap.add_argument('--height', type=int, default=420)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, encoding='utf-8-sig', newline='')))
    ys = [c.strip() for c in a.y.split(',')]
    if a.sort:
        rows.sort(key=lambda r: -float(r[ys[0]] or 0))
    xs = [r[a.x] for r in rows]
    series = {c: [float(r[c].replace(',', '.')) if r.get(c) not in (None, '') else None for r in rows] for c in ys}
    svg = render(xs, series, a.type, a.title or f"{', '.join(ys)} by {a.x}", a.subtitle, a.highlight, a.unit, a.width, a.height)
    open(a.out, 'w', encoding='utf-8').write(svg)
    print(f'{a.type} chart of {len(xs)} points written to {a.out}')


if __name__ == '__main__':
    main()
