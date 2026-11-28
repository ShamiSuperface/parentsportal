"""Add the "other city" switch to the welcome screen of every city page.
Usage: python3 tools/city_switch_patch.py   (run from the repo root; safe to run twice)
The list of cities is read at runtime from /cities.json, so a new city needs no code change:
add it to cities.json and run tools/sync_cities.py."""
import re, glob, json

MARK = 'id="wcity"'
CSS = ('.wcity{display:inline-flex;align-items:center;margin-inline-start:8px;vertical-align:middle;border:1.5px solid color-mix(in srgb,var(--ink) 35%,transparent);'
       'background:var(--surface);color:var(--ink);border-radius:999px;padding:2px 12px;min-height:32px;font:inherit;font-size:.82rem;font-weight:700;cursor:pointer}\n'
       '.wcity:hover{border-color:var(--accent)}\n'
       '.wcity[aria-expanded="true"]{border-color:var(--accent);color:var(--accent)}\n'
       '.wcities{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin:2px 0 0}\n'
       '.wcities[hidden]{display:none}\n'
       '.wcities a{display:inline-flex;align-items:center;min-height:40px;padding:6px 14px;border-radius:999px;border:2px solid var(--line);background:var(--paper);color:var(--ink);text-decoration:none;font-weight:700;font-size:.92rem}\n'
       '.wcities a:hover{border-color:var(--accent)}\n'
       '.wcity:focus-visible,.wcities a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}\n')
JS = r"""
/* other cities on the welcome screen: the list comes from /cities.json (one source for all cities) */
(()=>{const b=document.getElementById('wcity'),n=document.getElementById('wcities');if(!b||!n)return;
  const fill=l=>{n.textContent='';l.forEach(c=>{if(!c||typeof c.slug!=='string'||!/^[a-z-]+$/.test(c.slug)||c.slug===CFG.slug||!c.name)return;
    const a=document.createElement('a');a.href='/'+c.slug+'/';a.textContent=String(c.name);a.addEventListener('click',()=>track('city',null,c.slug));n.appendChild(a);});};
  fetch('/cities.json').then(r=>r.ok?r.json():null).then(l=>{if(Array.isArray(l))fill(l);}).catch(()=>{});
  b.onclick=()=>{if(!n.children.length){location.href='/';return;}
    const o=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(o));n.hidden=!o;if(o)track('cities');};
})();
"""
ANCHOR_JS = "document.getElementById('homeBtn').addEventListener('click',()=>track('install'));\n"

for f in sorted(glob.glob('*/index.html')):
    s = open(f, encoding='utf-8').read()
    if MARK in s:
        print(f, 'already patched'); continue
    m = re.search(r'<p class="wsub">([^<]+)</p>', s)
    assert m, f
    s = s.replace(m.group(0),
        '<p class="wsub">' + m.group(1) + ' <button type="button" class="wcity" id="wcity" aria-expanded="false" aria-controls="wcities">החלפת עיר</button></p>\n'
        '    <nav class="wcities" id="wcities" aria-label="ערים נוספות" hidden></nav>', 1)
    i = s.index('</style>\n</head>')
    s = s[:i] + CSS + s[i:]
    assert s.count(ANCHOR_JS) == 1, f
    s = s.replace(ANCHOR_JS, ANCHOR_JS + JS.lstrip('\n'), 1)
    open(f, 'w', encoding='utf-8').write(s)
    print(f, 'patched')
