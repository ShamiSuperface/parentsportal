"""Build the link-preview images (og:image) for every city and for the landing page.
Usage: python3 tools/make_share_images.py   (run from the repository root)
Reads the city map from each city's data block, so the image follows the data.
Writes <slug>/share.jpg and share.jpg at the root, 1200x630, JPEG, well under 300KB (WhatsApp)."""
import json, re, os, sys, tempfile, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITIES = [('ramat-gan', 'רמת גן וגבעתיים'), ('rishon-lezion', 'ראשון לציון')]
COLORS = {'gan': '#d1495b', 'daycare': '#e07a1f', 'tipa': '#2f7fc1', 'play': '#c99400', 'garden': '#2e9e4f',
          'comm': '#7a4fb5', 'shelter': '#3b3f46', 'biz': '#c2417a'}
LOGO = ''.join(f'<g transform="rotate({r} 50 50)"><path d="M54 46 L54 26 A20 20 0 0 1 74 6 A20 20 0 0 1 94 26 A20 20 0 0 1 74 46 Z" fill="{c}"/><circle cx="74" cy="26" r="6.5" fill="#fff"/></g>'
               for r, c in [(0, '#d1495b'), (90, '#2f7fc1'), (180, '#c99400'), (270, '#2e9e4f')]) + '<circle cx="50" cy="50" r="3" fill="#1f6b52"/>'
W, H = 1200, 630
MAP_W = 520  # map panel on the left; text on the right


def dec(a):
    o = [(a[0], a[1])]
    for i in range(2, len(a), 2):
        o.append((o[-1][0] + a[i], o[-1][1] + a[i + 1]))
    return o


def city_svg(slug):
    s = open(os.path.join(ROOT, slug, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    d = json.loads(m.group(1).replace('<\\/', '</'))
    rings = [dec(r) for r in d['boundary']]
    xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = 26
    sc = min((MAP_W - 2 * pad) / (maxx - minx), (H - 2 * pad) / (maxy - miny))
    ox = (MAP_W - (maxx - minx) * sc) / 2; oy = (H - (maxy - miny) * sc) / 2
    T = lambda x, y: (round(ox + (x - minx) * sc, 1), round(oy + (maxy - y) * sc, 1))
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
        dots.append(f'<g fill="{COLORS.get(c, "#888")}" stroke="#fff" stroke-width="1">' + ''.join(f'<circle cx="{x}" cy="{y}" r="4"/>' for x, y in ps) + '</g>')
    return (f'<svg width="{MAP_W}" height="{H}" viewBox="0 0 {MAP_W} {H}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><clipPath id="cb"><path d="{bd}" clip-rule="evenodd"/></clipPath></defs>'
            f'<path d="{bd}" fill="#f7f8f4" fill-rule="evenodd"/>'
            f'<g clip-path="url(#cb)"><path d="{greens}" fill="#cfe3c4"/><path d="{water}" fill="#bcd8e6"/></g>'
            f'<g clip-path="url(#cb)"><path d="{sec}" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{main}" fill="none" stroke="#f0dc9f" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
            f'<path d="{bd}" fill="none" stroke="#8aa596" stroke-width="2" stroke-dasharray="7 5"/>'
            + ''.join(dots) + '</svg>')


def page(name, url_text, map_svg):
    left = (f'<div class="map">{map_svg}</div>' if map_svg else '')
    return f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@600;700&family=Secular+One&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#f4f6f1;font-family:Assistant,sans-serif;color:#1d2b25;display:flex;position:relative}}
.map{{position:absolute;left:0;top:0;width:{MAP_W}px;height:{H}px;background:#e9ece4}}
.txt{{position:absolute;right:0;top:0;width:{W - (MAP_W if map_svg else 0)}px;height:{H}px;padding:0 70px 0 56px;display:flex;flex-direction:column;justify-content:center;{'align-items:center;text-align:center;' if not map_svg else ''}}}
.logo{{width:112px;height:112px;margin-bottom:22px}}
.brand{{font-family:'Secular One',sans-serif;font-size:46px;line-height:1.1;color:#1f6b52}}
.city{{font-family:'Secular One',sans-serif;font-size:{84 if len(name) < 14 else 70}px;line-height:1.08;margin-top:8px}}
.sub{{font-size:31px;line-height:1.35;color:#3f4d46;margin-top:22px;font-weight:600}}
.url{{position:absolute;bottom:40px;right:70px;font-size:26px;font-weight:700;color:#1f6b52;direction:ltr}}
{'.url{right:auto;left:50%;transform:translateX(-50%)}' if not map_svg else ''}
.bar{{position:absolute;top:0;right:0;height:12px;width:{W - (MAP_W if map_svg else 0)}px;display:flex}}
.bar i{{flex:1}}
</style></head><body>
{left}
<div class="bar"><i style="background:#d1495b"></i><i style="background:#2f7fc1"></i><i style="background:#c99400"></i><i style="background:#2e9e4f"></i></div>
<div class="txt">
<svg class="logo" viewBox="0 0 100 100">{LOGO}</svg>
<div class="brand">פורטל הגיל הרך</div>
<div class="city">{name}</div>
<div class="sub">גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים, על מפה אחת</div>
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
