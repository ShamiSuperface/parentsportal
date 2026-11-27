"""Build parentsportal.org.il from the live shared-code portals.
Usage: python3 build_site.py <ramat-gan live html> <rishon live html> <out dir>
Applies the same hosting patch to every city, so the code stays identical across cities."""
import sys, re, json, os, urllib.parse

SITE = 'https://parentsportal.org.il'
SB_URL = 'https://wuhmhrwbuchckrugirvo.supabase.co/rest/v1/events'
SB_KEY = 'sb_publishable_tL910FnvCbiPD9MVIylx5A_gmX_eg5_'

CITIES = [
    dict(slug='ramat-gan', src=sys.argv[1], name='רמת גן וגבעתיים',
         desc='גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים ברמת גן ובגבעתיים, על מפה אחת. מה הכי קרוב לבית, ומתי נרשמים.'),
    dict(slug='rishon-lezion', src=sys.argv[2], name='ראשון לציון',
         desc='גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים בראשון לציון, על מפה אחת. מה הכי קרוב לבית, ומתי נרשמים.'),
]
OUT = sys.argv[3]

LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            + ''.join(f'<g transform="rotate({r} 50 50)"><path d="M54 46 L54 26 A20 20 0 0 1 74 6 A20 20 0 0 1 94 26 A20 20 0 0 1 74 46 Z" fill="{c}"/><circle cx="74" cy="26" r="6.5" fill="#fff"/></g>'
                      for r, c in [(0, '#e0566b'), (90, '#3a86c8'), (180, '#d9a21b'), (270, '#3aa05c')])
            + '<circle cx="50" cy="50" r="3" fill="#2f6f5e"/></svg>')
FAVICON = 'data:image/svg+xml,' + urllib.parse.quote(LOGO_SVG)

TRACK_JS = r"""
/* ---------- anonymous usage counters (parentsportal.org.il only) ---------- */
const TRK_U='%s',TRK_K='%s';
try{const q=location.search;if(/[?&]notrack=1/.test(q))localStorage.setItem('pp-notrack','1');if(/[?&]notrack=0/.test(q))localStorage.removeItem('pp-notrack');}catch(e){}
const TRK_SID=(()=>{const mk=()=>(Math.random().toString(36).slice(2)+'00000000').slice(0,10);try{let s=sessionStorage.getItem('pp-sid');if(!s||!/^[a-z0-9]{8,16}$/.test(s)){s=mk();sessionStorage.setItem('pp-sid',s);}return s;}catch(e){return mk();}})();
const TRK_DEV=matchMedia('(max-width:760px)').matches?'m':'d';
const TRK_REF=(()=>{try{const u=new URLSearchParams(location.search).get('utm_source');if(u)return u.slice(0,60);const h=document.referrer?new URL(document.referrer).hostname:'';return h&&h!==location.hostname?h.slice(0,60):null;}catch(e){return null;}})();
function track(ev,cat,item,val){try{
  if(!/(^|\.)parentsportal\.org\.il$/.test(location.hostname))return;
  if(navigator.doNotTrack==='1')return;
  try{if(localStorage.getItem('pp-notrack')==='1')return;}catch(e){}
  fetch(TRK_U,{method:'POST',keepalive:true,headers:{'apikey':TRK_K,'Content-Type':'application/json','Prefer':'return=minimal'},
    body:JSON.stringify({city:CFG.slug,ev:ev,cat:cat||null,item:item?String(item).slice(0,120):null,val:val?String(val).slice(0,60):null,sid:TRK_SID,dev:TRK_DEV,ref:TRK_REF})}).catch(()=>{});
}catch(e){}}
let trkLastCard=null;
""" % (SB_URL, SB_KEY)

CLICK_JS = r"""
/* usage counters: clicks on links and the registration box */
document.addEventListener('click',e=>{const a=e.target&&e.target.closest?e.target.closest('a'):null;if(!a)return;const h=a.getAttribute('href')||'';
  const sel=state.sel&&state.sel.c?state.sel:null;const cat=sel?sel.c:null,item=sel?sel.n:null;let d=h;try{d=decodeURIComponent(h);}catch(_){}
  if(h.startsWith('tel:'))track('call',cat,item);
  else if(a.id==='shareFab'||/^https:\/\/wa\.me\/\?text=/.test(h))track('share');
  else if(h.indexOf('wa.me/'+WA)>=0)track(d.indexOf('לפרסם עסק')>=0?'biz':(d.indexOf('הצעה לפורטל')>=0?'suggest':'contact'));
  else if(/wa\.me\/972/.test(h))track('wa',cat,item);
  else if(/waze\.com|google\.[a-z.]+\/maps|maps\.google|maps\.apple|moovit/.test(h))track('nav',cat,item);
},true);
document.addEventListener('toggle',e=>{const t=e.target;if(t&&t.classList&&t.classList.contains('regbox')&&t.open)track('reg');},true);
document.getElementById('homeBtn').addEventListener('click',()=>track('install'));
/* my location (works on the hosted site) */
document.getElementById('wgeo').onclick=()=>{const er=document.getElementById('werr');
  if(!navigator.geolocation){er.textContent='הדפדפן לא מאפשר לאתר מיקום. הזינו כתובת.';return;}
  er.textContent='מאתרים את המיקום...';
  navigator.geolocation.getCurrentPosition(pos=>{
    const x=(pos.coords.longitude-LON0)*KX,y=(pos.coords.latitude-LAT0)*KY;
    let a=1e9,b=-1e9,c=1e9,d=-1e9;P.forEach(p=>{if(p.noLoc||p.out)return;a=Math.min(a,p.x);b=Math.max(b,p.x);c=Math.min(c,p.y);d=Math.max(d,p.y);});
    if(x<a-1500||x>b+1500||y<c-1500||y>d+1500){er.textContent='נראה שאתם מחוץ ל'+CFG.full+'. הזינו כתובת, או סמנו את הבית על המפה.';return;}
    er.textContent='';track('geo');const first=wMode==='first';hideWelcome(first);setHome(x,y,'המיקום שלי');
    if(first)showChooser(true);else setTimeout(()=>{flyTo(x,y,1.5);toMap();},60);
  },()=>{er.textContent='לא הצלחנו לאתר את המיקום. אפשר לאשר גישה למיקום בדפדפן, או להזין כתובת.';},{enableHighAccuracy:true,timeout:10000,maximumAge:60000});};
"""

PRIVACY = ('<h3>פרטיות</h3>\n  <p>הפורטל סופר כניסות ושימוש באופן אנונימי, כדי לדעת מה מועיל להורים: כמה נכנסו, '
           'אילו סוגי מקומות נבחרו ואילו כרטיסים נפתחו. הכתובת שאתם מזינים והמיקום שלכם נשארים במכשיר שלכם ולא נשלחים לשום מקום. '
           'לא נאספים שמות או מספרי טלפון, ואין עוגיות.</p>\n  ')


def rep(s, old, new, count=1):
    n = s.count(old)
    if n != count:
        sys.exit(f'ANCHOR x{n}: {old[:90]!r}')
    return s.replace(old, new)


def share_meta(img, title, desc, alt):
    """og:image and Twitter tags. The images are built by tools/make_share_images.py."""
    return (f'<meta property="og:site_name" content="פורטל הגיל הרך">\n'
            f'<meta property="og:image" content="{img}">\n<meta property="og:image:secure_url" content="{img}">\n'
            f'<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            f'<meta property="og:image:alt" content="{alt}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="{title}">\n'
            f'<meta name="twitter:description" content="{desc}">\n<meta name="twitter:image" content="{img}">\n<meta name="twitter:image:alt" content="{alt}">\n')


def share_href(name, url):
    t = f'היי, יש פה את "פורטל הגיל הרך - {name}" - גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות, מרכזים קהילתיים ומקלטים על מפה אחת - שווה לבדוק > {url}'
    return 'https://wa.me/?text=' + urllib.parse.quote(t, safe='')


def build_city(c):
    s = open(c['src'], encoding='utf-8').read()
    url = f"{SITE}/{c['slug']}/"
    title = f"פורטל הגיל הרך - {c['name']}"
    # city config
    m = re.search(r'(<script id="city" type="application/json">)(.*?)(</script>)', s, re.S)
    cfg = json.loads(m.group(2).replace('<\\/', '</'))
    cfg['slug'] = c['slug']
    cfg['site'] = url
    cfg['keys']['theme'] = 'pp-theme'
    if 'פרטיות</h3>' not in cfg['info']:
        cfg['info'] = rep(cfg['info'], '<h3>מקורות המידע</h3>', PRIVACY + '<h3>מקורות המידע</h3>')
    cj = json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/')
    s = s[:m.start(2)] + cj + s[m.end(2):]
    # head
    head = (f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta name="description" content="{c["desc"]}">\n'
            f'<link rel="canonical" href="{url}">\n'
            f'<meta property="og:type" content="website">\n<meta property="og:locale" content="he_IL">\n'
            f'<meta property="og:title" content="{title}">\n<meta property="og:description" content="{c["desc"]}">\n'
            f'<meta property="og:url" content="{url}">\n'
            + share_meta(url + 'share.jpg', title, c['desc'], f'פורטל הגיל הרך, {c["name"]}: מפת העיר עם גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים')
            + f'<meta name="theme-color" content="#2f6f5e">\n'
            f'<link rel="icon" href="{FAVICON}">')
    s = rep(s, '<meta name="viewport" content="width=device-width, initial-scale=1">', head)
    # share link
    s = re.sub(r'(id="shareFab" class="fab" href=")[^"]+(")', lambda mm: mm.group(1) + share_href(c['name'], url) + mm.group(2), s, count=1)
    # direct call and my location
    s = rep(s, "const c=el('button',{class:'mini',type:'button'},'העתקה');",
            "w.append(el('a',{class:'mini',href:'tel:'+d,'aria-label':'חיוג אל '+n},'חיוג'));const c=el('button',{class:'mini',type:'button'},'העתקה');")
    s = rep(s, '<button type="button" class="linkbtn" id="wpick">',
            '<button type="button" class="linkbtn" id="wgeo">המיקום שלי</button><button type="button" class="linkbtn" id="wpick">')
    # counters
    s = rep(s, "const CFG=JSON.parse(document.getElementById('city').textContent);",
            "const CFG=JSON.parse(document.getElementById('city').textContent);" + TRACK_JS)
    s = rep(s, 'function setHome(x,y,label){', "function setHome(x,y,label){track('addr');")
    s = rep(s, '  CATS.forEach(c=>{state.on[c.id]=chSel.has(c.id);',
            "  track('choose',null,null,[...chSel].join(','));\n  CATS.forEach(c=>{state.on[c.id]=chSel.has(c.id);")
    s = rep(s, 'function detail(p){', "function detail(p){if(trkLastCard!==p){trkLastCard=p;track('card',p.c,p.n);}")
    s = rep(s, "document.getElementById('regBtn').onclick=openReg;",
            CLICK_JS + "track('visit');\ndocument.getElementById('regBtn').onclick=openReg;")
    for bad in ['claude.ai/artifact']:
        if bad in s:
            sys.exit('left: ' + bad)
    os.makedirs(f"{OUT}/{c['slug']}", exist_ok=True)
    open(f"{OUT}/{c['slug']}/index.html", 'w', encoding='utf-8').write(s)
    return url


def landing():
    cards = ''.join(f'<a class="city" href="/{c["slug"]}/"><span class="cn">{c["name"]}</span><span class="cd">גנים, מעונות, טיפות חלב, גני שעשועים, גינות ומקלטים</span></a>' for c in CITIES)
    return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>פורטל הגיל הרך</title>
<meta name="description" content="מפות לגיל הרך לפי עיר: גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים, ומתי נרשמים.">
<link rel="canonical" href="{SITE}/">
<meta property="og:type" content="website"><meta property="og:locale" content="he_IL">
<meta property="og:title" content="פורטל הגיל הרך"><meta property="og:url" content="{SITE}/">
<meta property="og:description" content="מפות לגיל הרך לפי עיר: גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים.">
{share_meta(SITE + '/share.jpg', 'פורטל הגיל הרך', 'מפות לגיל הרך לפי עיר: גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים.', 'פורטל הגיל הרך: מפות לגיל הרך לפי עיר')}<meta name="theme-color" content="#2f6f5e">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--paper:#f6f4ee;--surface:#fff;--ink:#1d2a24;--muted:#56645c;--line:#dcd8cc;--accent:#2f6f5e}}
:root[data-theme="dark"]{{--paper:#0b0b0b;--surface:#161616;--ink:#ececec;--muted:#a8a8a8;--line:#2c2c2c;--accent:#6cc8a3}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Rubik,system-ui,sans-serif;background:var(--paper);color:var(--ink);min-height:100vh;display:flex;flex-direction:column;align-items:center}}
.wrap{{width:100%;max-width:560px;padding:28px 18px 40px;display:flex;flex-direction:column;align-items:center;gap:14px}}
.top{{width:100%;display:flex;justify-content:flex-start}}
.theme{{border:2px solid color-mix(in srgb,var(--ink) 35%,transparent);background:var(--surface);color:var(--ink);border-radius:999px;padding:4px 14px;min-height:36px;font:inherit;font-size:.85rem;font-weight:700;cursor:pointer}}
.theme:focus-visible,.city:focus-visible{{outline:3px solid var(--accent);outline-offset:3px}}
.logo{{width:92px;height:92px}}
h1{{margin:0;font-size:2rem;font-weight:700;text-align:center}}
.lead{{margin:0;color:var(--muted);text-align:center;line-height:1.55;font-size:1.02rem}}
h2{{margin:14px 0 0;font-size:1.05rem;align-self:flex-start}}
.cities{{width:100%;display:flex;flex-direction:column;gap:10px}}
.city{{display:flex;flex-direction:column;gap:2px;padding:16px 20px;border-radius:24px;border:2px solid var(--line);background:var(--surface);color:var(--ink);text-decoration:none;min-height:56px}}
.city:hover{{border-color:var(--accent)}}
.cn{{font-size:1.2rem;font-weight:700}}.cd{{font-size:.9rem;color:var(--muted)}}
.copy{{margin-top:22px;font-size:.85rem;color:var(--muted);text-align:center}}
</style>
</head>
<body>
<main class="wrap">
  <div class="top"><button type="button" class="theme" id="theme">תצוגה כהה</button></div>
  <div class="logo" aria-hidden="true">{LOGO_SVG}</div>
  <h1>פורטל הגיל הרך</h1>
  <p class="lead">כל מה שהורים לילדים מלידה עד גיל 4 צריכים, על מפה אחת: גני ילדים, מעונות יום, טיפות חלב, גני שעשועים, גינות ומקלטים. מה הכי קרוב לבית, ומתי נרשמים.</p>
  <h2>בחרו עיר</h2>
  <nav class="cities" aria-label="ערים">{cards}</nav>
  <p class="copy">© כל הזכויות שמורות ל־SuperFace שמי אוסטרובסקי 2026</p>
</main>
<script>
(function(){{const b=document.getElementById('theme');let t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';try{{const s=localStorage.getItem('pp-theme');if(s==='light'||s==='dark')t=s;}}catch(e){{}}
const ap=()=>{{document.documentElement.setAttribute('data-theme',t);b.textContent=t==='dark'?'תצוגה בהירה':'תצוגה כהה';}};ap();
b.onclick=()=>{{t=t==='dark'?'light':'dark';try{{localStorage.setItem('pp-theme',t);}}catch(e){{}}ap();}};
try{{const q=location.search;if(/[?&]notrack=1/.test(q))localStorage.setItem('pp-notrack','1');if(/[?&]notrack=0/.test(q))localStorage.removeItem('pp-notrack');}}catch(e){{}}
try{{if(/(^|\\.)parentsportal\\.org\\.il$/.test(location.hostname)&&navigator.doNotTrack!=='1'&&localStorage.getItem('pp-notrack')!=='1'){{
 let sid;try{{sid=sessionStorage.getItem('pp-sid');if(!sid){{sid=(Math.random().toString(36).slice(2)+'00000000').slice(0,10);sessionStorage.setItem('pp-sid',sid);}}}}catch(e){{sid=(Math.random().toString(36).slice(2)+'00000000').slice(0,10);}}
 let ref=null;try{{const u=new URLSearchParams(location.search).get('utm_source');const h=document.referrer?new URL(document.referrer).hostname:'';ref=u?u.slice(0,60):(h&&h!==location.hostname?h.slice(0,60):null);}}catch(e){{}}
 fetch('{SB_URL}',{{method:'POST',keepalive:true,headers:{{'apikey':'{SB_KEY}','Content-Type':'application/json','Prefer':'return=minimal'}},body:JSON.stringify({{city:'home',ev:'visit',sid:sid,dev:matchMedia('(max-width:760px)').matches?'m':'d',ref:ref}})}}).catch(()=>{{}});
}}}}catch(e){{}}
}})();
</script>
</body>
</html>
'''


os.makedirs(OUT, exist_ok=True)
urls = [build_city(c) for c in CITIES]
open(f'{OUT}/index.html', 'w', encoding='utf-8').write(landing())
open(f'{OUT}/CNAME', 'w').write('parentsportal.org.il\n')
open(f'{OUT}/.nojekyll', 'w').write('')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
open(f'{OUT}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in [SITE + '/'] + urls) + '</urlset>\n')
open(f'{OUT}/404.html', 'w', encoding='utf-8').write(
    '<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>הדף לא נמצא</title><meta http-equiv="refresh" content="0; url=/"></head><body><p><a href="/">לדף הבית של פורטל הגיל הרך</a></p></body></html>')
print('built', urls)
