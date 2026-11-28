"""Other cities on the welcome screen of every city page: a line "כנסו לראות מידע בערים נוספות"
and a button for each other city, at the bottom of the welcome card.
Usage: python3 tools/city_switch_patch.py   (run from the repo root; safe to run twice)
The list of cities is read at runtime from /cities.json, so a new city needs no code change:
add it to cities.json and run tools/sync_cities.py.
Also removes the earlier "החלפת עיר" switch (PR 6) from pages that have it."""
import re, glob

# ---- the earlier version (PR 6), removed when found ----
V1_HTML = re.compile(r' <button type="button" class="wcity" id="wcity" aria-expanded="false" aria-controls="wcities">החלפת עיר</button></p>\n'
                     r'    <nav class="wcities" id="wcities" aria-label="ערים נוספות" hidden></nav>')
V1_CSS = '.wcity{display:inline-flex;align-items:center;margin-inline-start:8px;vertical-align:middle;border:1.5px solid color-mix(in srgb,var(--ink) 35%,transparent);background:var(--surface);color:var(--ink);border-radius:999px;padding:2px 12px;min-height:32px;font:inherit;font-size:.82rem;font-weight:700;cursor:pointer}\n.wcity:hover{border-color:var(--accent)}\n.wcity[aria-expanded="true"]{border-color:var(--accent);color:var(--accent)}\n.wcities{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin:2px 0 0}\n.wcities[hidden]{display:none}\n.wcities a{display:inline-flex;align-items:center;min-height:40px;padding:6px 14px;border-radius:999px;border:2px solid var(--line);background:var(--paper);color:var(--ink);text-decoration:none;font-weight:700;font-size:.92rem}\n.wcities a:hover{border-color:var(--accent)}\n.wcity:focus-visible,.wcities a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}\n'
V1_JS = "\n/* other cities on the welcome screen: the list comes from /cities.json (one source for all cities) */\n(()=>{const b=document.getElementById('wcity'),n=document.getElementById('wcities');if(!b||!n)return;\n  const fill=l=>{n.textContent='';l.forEach(c=>{if(!c||typeof c.slug!=='string'||!/^[a-z-]+$/.test(c.slug)||c.slug===CFG.slug||!c.name)return;\n    const a=document.createElement('a');a.href='/'+c.slug+'/';a.textContent=String(c.name);a.addEventListener('click',()=>track('city',null,c.slug));n.appendChild(a);});};\n  fetch('/cities.json').then(r=>r.ok?r.json():null).then(l=>{if(Array.isArray(l))fill(l);}).catch(()=>{});\n  b.onclick=()=>{if(!n.children.length){location.href='/';return;}\n    const o=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(o));n.hidden=!o;if(o)track('cities');};\n})();\n"

# ---- current version ----
MARK = 'id="wmore"'
HTML = ('\n    <section class="wmore" id="wmore" aria-labelledby="wmoret" hidden>\n'
        '      <p class="wmoret" id="wmoret">כנסו לראות מידע בערים נוספות</p>\n'
        '      <nav class="wmorel" id="wmorel" aria-labelledby="wmoret"></nav>\n'
        '    </section>')
ANCHOR_HTML = '<button type="button" class="linkbtn" id="wcancel" hidden>ביטול וחזרה</button></div>'
CSS = ('.wmore{margin-top:10px;padding-top:14px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:10px}\n'
       '.wmore[hidden]{display:none}\n'
       '.wmoret{margin:0;font-weight:700;font-size:1rem}\n'
       '.wmorel{display:flex;flex-wrap:wrap;justify-content:center;gap:8px}\n'
       '.wmorel a{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:8px 16px;border-radius:999px;border:2px solid var(--line);background:var(--paper);color:var(--ink);text-decoration:none;font-weight:700;font-size:.95rem}\n'
       '.wmorel a:hover{border-color:var(--accent)}\n'
       '.wmorel a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}\n')
JS = r"""
/* other cities at the bottom of the welcome screen: the list comes from /cities.json (one source for all cities) */
(()=>{const box=document.getElementById('wmore'),nav=document.getElementById('wmorel');if(!box||!nav)return;
  const add=(href,name,slug)=>{const a=document.createElement('a');a.href=href;a.textContent=name;a.addEventListener('click',()=>track('city',null,slug));nav.appendChild(a);};
  fetch('/cities.json').then(r=>r.ok?r.json():Promise.reject()).then(l=>{if(!Array.isArray(l))throw 0;
    l.forEach(c=>{if(c&&typeof c.slug==='string'&&/^[a-z-]+$/.test(c.slug)&&c.slug!==CFG.slug&&c.name)add('/'+c.slug+'/',String(c.name),c.slug);});
    box.hidden=!nav.children.length;})
  .catch(()=>{nav.textContent='';add('/','לכל הערים','home');box.hidden=false;});
})();
"""
ANCHOR_JS = "document.getElementById('homeBtn').addEventListener('click',()=>track('install'));\n"

for f in sorted(glob.glob('*/index.html')):
    s = open(f, encoding='utf-8').read()
    done = []
    s, k = V1_HTML.subn('</p>', s)
    if k:
        assert s.count(V1_CSS) == 1 and s.count(V1_JS.lstrip('\n')) == 1, f
        s = s.replace(V1_CSS, '', 1).replace(V1_JS.lstrip('\n'), '', 1)
        done.append('removed the earlier switch')
    if MARK not in s:
        assert s.count(ANCHOR_HTML) == 1 and s.count(ANCHOR_JS) == 1, f
        s = s.replace(ANCHOR_HTML, ANCHOR_HTML + HTML, 1)
        i = s.index('</style>\n</head>')
        s = s[:i] + CSS + s[i:]
        s = s.replace(ANCHOR_JS, ANCHOR_JS + JS.lstrip('\n'), 1)
        done.append('other cities at the bottom')
    open(f, 'w', encoding='utf-8').write(s)
    print(f, ', '.join(done) or 'already patched')
