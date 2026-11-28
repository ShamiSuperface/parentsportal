"""Build the link-preview images (og:image) for every city and for the landing page.
Usage: python3 tools/make_share_images.py   (run from the repository root)
Reads the city map from each city's data block, so the image follows the data.
Writes <slug>/share.jpg and share.jpg at the root, 1200x630, JPEG, well under 300KB (WhatsApp)."""
import json, re, os, sys, tempfile, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITIES = [('ramat-gan', 'רמת גן וגבעתיים'), ('rishon-lezion', 'ראשון לציון'), ('holon', 'חולון'), ('bat-yam', 'בת ים')]
COLORS = {'gan': '#d1495b', 'daycare': '#e07a1f', 'tipa': '#2f7fc1', 'play': '#c99400', 'garden': '#2e9e4f',
          'comm': '#7a4fb5', 'shelter': '#3b3f46', 'biz': '#c2417a'}
LOGO = ''.join(f'<g transform="rotate({r} 50 50)"><path d="M54 46 L54 26 A20 20 0 0 1 74 6 A20 20 0 0 1 94 26 A20 20 0 0 1 74 46 Z" fill="{c}"/><circle cx="74" cy="26" r="6.5" fill="#fff"/></g>'
               for r, c in [(0, '#d1495b'), (90, '#2f7fc1'), (180, '#c99400'), (270, '#2e9e4f')]) + '<circle cx="50" cy="50" r="3" fill="#1f6b52"/>'
W, H = 1200, 630


def dec(a):
    o = [(a[0], a[1])]
    for i in range(2, len(a), 2):
        o.append((o[-1][0] + a[i], o[-1][1] + a[i + 1]))
    return o


def city_svg(slug):
    """The city map, scaled to cover the whole image (the card in the middle hides its centre)."""
    s = open(os.path.join(ROOT, slug, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    d = json.loads(m.group(1).replace('<\\/', '</'))
    rings = [dec(r) for r in d['boundary']]
    xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    # frame the built-up area (where the places are), not the whole municipal boundary
    P = sorted(p['x'] for p in d['pts'] if not p.get('noLoc') and not p.get('out'))
    Q = sorted(p['y'] for p in d['pts'] if not p.get('noLoc') and not p.get('out'))
    q = lambda v, f: v[int(f * (len(v) - 1))]
    x0, x1, y0, y1 = q(P, .03), q(P, .97), q(Q, .03), q(Q, .97)
    sc = max(W / (x1 - x0), H / (y1 - y0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    T = lambda x, y: (round(W / 2 + (x - cx) * sc, 1), round(H / 2 - (y - cy) * sc, 1))
    path = lambda pts, close: 'M' + 'L'.join(f'{a},{b}' for a, b in (T(x, y) for x, y in pts)) + ('Z' if close else '')
    bd = ''.join(path(r, True) for r in rings)
    greens = ''.join(path(dec(g[1:]), True) for g in d['green'] if g[0] in (0, 3))
    water = ''.join(path(dec(g[1:]), True) for g in d['green'] if g[0] == 1)
    main = ''.join(path(dec(r[1:]), False) for r in d['roads'] if r[0] <= 1)
    sec = ''.join(path(dec(r[1:]), False) for r in d['roads'] if r[0] in (2, 3))
    order = ['shelter', 'comm', 'garden', 'play', 'tipa', 'daycare', 'gan', 'biz']
    dots = []
    for c in order:
        ps = [T(p['x'], p['y']) for p in d['pts'] if p.get('c') == c and not p.get('noLoc') and not p.get('out')]
        dots.append(f'<g fill="{COLORS.get(c, "#888")}" stroke="#fff" stroke-width="1.2">' + ''.join(f'<circle cx="{x}" cy="{y}" r="5.5"/>' for x, y in ps) + '</g>')
    return (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><clipPath id="cb"><path d="{bd}" clip-rule="evenodd"/></clipPath></defs>'
            f'<path d="{bd}" fill="#f7f8f4" fill-rule="evenodd"/>'
            f'<g clip-path="url(#cb)"><path d="{greens}" fill="#cfe3c4"/><path d="{water}" fill="#bcd8e6"/>'
            f'<path d="{sec}" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{main}" fill="none" stroke="#f0dc9f" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></g>'
            f'<path d="{bd}" fill="none" stroke="#8aa596" stroke-width="2.5" stroke-dasharray="8 6"/>'
            + ''.join(dots) + '</svg>')


def page(name, url_text, map_svg):
    """Everything that matters sits in the centre square (285..915), because WhatsApp status and
    small previews crop a square from the middle. The wide view shows the map around the card."""
    bg = map_svg or ''
    return f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@600;700&family=Secular+One&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#e9ece4;font-family:Assistant,sans-serif;color:#1d2b25;position:relative}}
.bg{{position:absolute;inset:0}}
.card{{position:absolute;left:{(W - 600) // 2}px;top:15px;width:600px;height:600px;background:#fff;border-radius:44px;
  box-shadow:0 10px 40px rgba(20,40,30,.28);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 40px;overflow:hidden}}
.bar{{position:absolute;top:0;left:0;right:0;height:14px;display:flex}}.bar i{{flex:1}}
.logo{{width:150px;height:150px;margin-bottom:18px}}
.brand{{font-family:'Secular One',sans-serif;font-size:50px;line-height:1.1;color:#1f6b52}}
.city{{font-family:'Secular One',sans-serif;font-size:{80 if len(name) < 12 else 64}px;line-height:1.08;margin-top:6px}}
.sub{{font-size:27px;line-height:1.3;color:#3f4d46;margin-top:18px;font-weight:600}}
.url{{font-size:25px;font-weight:700;color:#1f6b52;direction:ltr;margin-top:18px}}
</style></head><body>
<div class="bg">{bg}</div>
<div class="card">
<div class="bar"><i style="background:#d1495b"></i><i style="background:#2f7fc1"></i><i style="background:#c99400"></i><i style="background:#2e9e4f"></i></div>
<svg class="logo" viewBox="0 0 100 100">{LOGO}</svg>
<div class="brand">פורטל הגיל הרך</div>
<div class="city">{name}</div>
<div class="sub">גנים, מעונות, טיפות חלב, גינות<br>וגני שעשועים, על מפה אחת</div>
<div class="url">{url_text}</div>
</div></body></html>'''


def main():
    jobs = [(os.path.join(ROOT, slug, 'share.jpg'), page(name, f'parentsportal.org.il/{slug}', city_svg(slug))) for slug, name in CITIES]
    jobs.append((os.path.join(ROOT, 'share.jpg'), page('מפות לפי עיר', 'parentsportal.org.il', None)))
    tmp = tempfile.mkdtemp()
    todo = []
    for i, (out, html) in enumerate(jobs):
        f = os.path.join(tmp, f'{i}.html')
        open(f, 'w', encoding='utf-8').write(html)
        todo.append([f, out])
    # Chromium through the Node Playwright that is installed with the browser
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"const pg=await b.newPage({{viewport:{{width:{W},height:{H}}},deviceScaleFactor:1}});"
          "for(const [f,o] of JSON.parse(process.argv[1])){await pg.goto('file://'+f,{waitUntil:'networkidle'});"
          "await pg.evaluate(()=>document.fonts.ready);await pg.screenshot({path:o,type:'jpeg',quality:88});}await b.close();})();")
    subprocess.run(['node', '-e', js, json.dumps(todo)], check=True)
    for _, out in todo:
        print(out, os.path.getsize(out), 'bytes')

if __name__ == '__main__':
    main()
