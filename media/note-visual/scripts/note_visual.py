#!/usr/bin/env python3
"""
Génère des schémas minimalistes « dessinés à la main » pour les Substack Notes de Corporate Mavericks (PIL, texte exact).

  note_visual.py render SPEC.json SORTIE.png
  note_visual.py demo DOSSIER            (un exemple de chaque modèle)

SPEC.json : {"type": "compare|matrix|funnel|steps", "titre": "...", ...}
  compare : lignes A et B de barres (labelA, labelB, formeA, formeB parmi croissance|plateau|stop|vague, axe)
  matrix  : axes x et y, quadrants [4 libellés : haut-gauche, haut-droite, bas-gauche, bas-droite], point (0-3)
  funnel  : etapes [3 a 6 libellés]
  steps   : etapes [3 a 6 libellés]
Les schémas sont des illustrations de concepts, jamais des données : une mention « schéma illustratif » est ajoutée.
"""
import json, math, os, random, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

W = H = 1080
INK = (34, 30, 48)
VIOLET, TEAL, CYAN, CORAL, GOLD = (187, 68, 187), (40, 172, 134), (28, 186, 200), (255, 100, 77), (245, 166, 35)
FONTS = ['/tmp/Caveat-Bold.ttf', os.path.expanduser('~/.hermes/assets/Caveat-Bold.ttf')]
FALLBACK = '/tmp/Montserrat-Bold.ttf'


def font(size):
    for f in FONTS + [FALLBACK]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def ensure_font():
    if any(os.path.exists(f) for f in FONTS):
        return
    os.makedirs(os.path.expanduser('~/.hermes/assets'), exist_ok=True)
    try:
        urllib.request.urlretrieve('https://github.com/googlefonts/caveat/raw/main/fonts/ttf/Caveat-Bold.ttf', FONTS[1])
        ImageFont.truetype(FONTS[1], 20)
    except Exception:
        if os.path.exists(FONTS[1]):
            os.remove(FONTS[1])


def wob(pts, d, color=INK, width=7, amp=2.2, seed=0):
    rnd = random.Random(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 18))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t + rnd.uniform(-amp, amp), y0 + (y1 - y0) * t + rnd.uniform(-amp, amp)))
    out.append(pts[-1])
    d.line(out, fill=color, width=width, joint='curve')
    for p in (out[0], out[-1]):
        d.ellipse([p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2], fill=color)


def arrow(d, x0, y0, x1, y1, color=INK, seed=1):
    wob([(x0, y0), (x1, y1)], d, color, 7, 1.6, seed)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (-0.45, 0.45):
        wob([(x1, y1), (x1 - 34 * math.cos(a + s), y1 - 34 * math.sin(a + s))], d, color, 7, 1.2, seed + 3)


def text_c(d, xy, s, size, color=INK, anchor='mm'):
    d.text(xy, s, font=font(size), fill=color, anchor=anchor)


def wrap(s, n):
    words, lines, cur = s.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + ([cur] if cur else [])


def canvas(titre):
    im = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    if titre:
        for i, l in enumerate(wrap(titre, 30)[:2]):
            text_c(d, (W / 2, 95 + i * 70), l, 64, INK)
    return im, d


def footer(d):
    text_c(d, (W / 2, H - 38), os.environ.get('NOTE_VISUAL_FOOTER', 'schéma illustratif'), 30, (150, 150, 165))


def bars(shape, n, hmax):
    if shape == 'croissance':
        return [hmax * (0.05 + 0.95 * (i / (n - 1)) ** 3) for i in range(n)]
    if shape == 'plateau':
        return [hmax * 0.12 for _ in range(n)]
    if shape == 'stop':
        return [hmax * 0.12 if i < n // 3 else 0 for i in range(n)]
    return [hmax * (0.3 + 0.25 * math.sin(i / 1.6)) for i in range(n)]


def render_compare(s):
    im, d = canvas(s.get('titre'))
    for row, (lab, shape, col, y0) in enumerate([(s['labelA'], s.get('formeA', 'croissance'), GOLD, 470), (s['labelB'], s.get('formeB', 'stop'), VIOLET, 860)]):
        n, x = 18, 120
        for i, h in enumerate(bars(shape, n, 250)):
            if h > 0:
                d.rectangle([x + i * 46, y0 - h, x + i * 46 + 26, y0], fill=col, outline=INK, width=4)
        arrow(d, 90, y0 + 4, 1000, y0 + 4, seed=row + 4)
        text_c(d, (W / 2, y0 + 48), lab.upper(), 46, INK)
    text_c(d, (1010, 575), s.get('axe', 'temps'), 34, (110, 110, 125), 'rm')
    footer(d)
    return im


def render_matrix(s):
    im, d = canvas(s.get('titre'))
    x0, y0, x1, y1 = 170, 230, 960, 950
    wob([(x0, y1), (x0, y0 - 20)], d, INK, 8, 1.5, 1); wob([(x0 - 20, y1), (x1, y1)], d, INK, 8, 1.5, 2)
    xm, ym = (x0 + x1) / 2 + 20, (y0 + y1) / 2
    wob([(xm, y0), (xm, y1)], d, (190, 190, 205), 5, 1.5, 3); wob([(x0, ym), (x1, ym)], d, (190, 190, 205), 5, 1.5, 4)
    q = s['quadrants']
    centers = [((x0 + xm) / 2, (y0 + ym) / 2), ((xm + x1) / 2, (y0 + ym) / 2), ((x0 + xm) / 2, (ym + y1) / 2), ((xm + x1) / 2, (ym + y1) / 2)]
    for i, (c, lab) in enumerate(zip(centers, q)):
        for j, l in enumerate(wrap(lab, 16)[:3]):
            text_c(d, (c[0], c[1] - 30 + j * 46), l, 44, INK)
    p = s.get('point')
    if p is not None:
        c = centers[p]; d.ellipse([c[0] - 150, c[1] - 120, c[0] + 150, c[1] + 120], outline=CORAL, width=9)
    text_c(d, (x0 + (x1 - x0) / 2, y1 + 40), s.get('x', '').upper(), 40, (110, 110, 125))
    ylab = Image.new('RGBA', (500, 70), (0, 0, 0, 0)); ImageDraw.Draw(ylab).text((250, 35), s.get('y', '').upper(), font=font(40), fill=(110, 110, 125), anchor='mm')
    im.paste(ylab.rotate(90, expand=True), (60, int((y0 + y1) / 2 - 250)), ylab.rotate(90, expand=True))
    footer(d)
    return im


def render_funnel(s):
    im, d = canvas(s.get('titre'))
    et = s['etapes'][:6]; n = len(et); top, bot = 230, 940; hh = (bot - top) / n
    cols = [TEAL, CYAN, VIOLET, GOLD, CORAL, INK]
    for i, lab in enumerate(et):
        wt, wb = 780 * (1 - i / (n + 2.2)), 780 * (1 - (i + 1) / (n + 2.2))
        y = top + i * hh
        poly = [(W / 2 - wt / 2, y), (W / 2 + wt / 2, y), (W / 2 + wb / 2, y + hh - 10), (W / 2 - wb / 2, y + hh - 10)]
        d.polygon(poly, fill=cols[i % 6] + (0,) if False else cols[i % 6])
        wob(poly + [poly[0]], d, INK, 5, 1.4, i + 5)
        text_c(d, (W / 2, y + hh / 2 - 4), lab, 46, (255, 255, 255))
    footer(d)
    return im


def render_steps(s):
    im, d = canvas(s.get('titre'))
    et = s['etapes'][:6]; n = len(et); bw = 780 / n
    cols = [TEAL, CYAN, VIOLET, GOLD, CORAL, INK]
    for i, lab in enumerate(et):
        h = 120 + i * (560 / n)
        x = 150 + i * bw
        d.rectangle([x, 930 - h, x + bw - 14, 930], fill=cols[i % 6], outline=INK, width=5)
        for j, l in enumerate(wrap(lab, max(8, int(bw / 17)))[:3]):
            text_c(d, (x + bw / 2 - 7, 930 - h + 40 + j * 40), l, 36, (255, 255, 255))
    arrow(d, 130, 960, 960, 960, seed=9)
    footer(d)
    return im


RENDERERS = {'compare': render_compare, 'matrix': render_matrix, 'funnel': render_funnel, 'steps': render_steps}


def render(spec, out):
    ensure_font()
    im = RENDERERS[spec['type']](spec)
    im.save(out, optimize=True)
    return out


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'render':
        print(render(json.load(open(sys.argv[2])), sys.argv[3]))
    elif len(sys.argv) >= 3 and sys.argv[1] == 'demo':
        os.makedirs(sys.argv[2], exist_ok=True)
        demos = [
            {'type': 'compare', 'titre': "Ce qu'on mesure / ce qui compte", 'labelA': "Quand on mesure l'impact", 'labelB': "Quand on mesure l'activité", 'formeA': 'croissance', 'formeB': 'stop', 'axe': 'temps'},
            {'type': 'matrix', 'titre': "Où est votre IA ?", 'x': 'Usage', 'y': 'Impact', 'quadrants': ['Peu utilisée, utile', 'Utilisée et utile', 'Ni utilisée ni utile', 'Beaucoup utilisée, peu utile'], 'point': 3},
            {'type': 'funnel', 'titre': "De l'euro dépensé à la valeur", 'etapes': ['Investir', 'Adopter', 'Accélérer', 'Fluidifier', 'Livrer', 'Impacter']},
            {'type': 'steps', 'titre': 'Cinq étapes pour une équipe soudée', 'etapes': ['Former', 'Tempêter', 'Normer', 'Performer', 'Clôturer']},
        ]
        for i, sp in enumerate(demos):
            print(render(sp, f'{sys.argv[2]}/demo_{sp["type"]}.png'))
    else:
        print(__doc__)
