"""Build the Holon data, walk and city blocks from raw sources.
Usage: python3 tools/holon_build.py RAW_DIR OUT_DIR
RAW_DIR holds all.json (GIS + OSM, collected in the browser), meonot.json (Education Ministry), tipot.json (Health Ministry).
Writes data.json and walk.json to OUT_DIR."""
import json, math, sys, re, collections, os

RAW, OUT = sys.argv[1], sys.argv[2]
A = json.load(open(os.path.join(RAW, 'all.json'), encoding='utf-8'))
G = A['gis']
LAT0, LON0 = 32.0137, 34.785
CO = math.cos(math.radians(LAT0)) * 111320
P = lambda lat, lon: (round((lon - LON0) * CO), round((lat - LAT0) * 110540))
Pf = lambda lat, lon: ((lon - LON0) * CO, (lat - LAT0) * 110540)


def enc(pts):
    pts = [(round(x), round(y)) for x, y in pts]
    o = [pts[0][0], pts[0][1]]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        if (c - a, d - b) == (0, 0):
            continue
        o += [c - a, d - b]
    return o


def dp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    best, bi = -1, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * (x - x1) - dx * (y - y1)) / L if (dx or dy) else math.hypot(x - x1, y - y1)
        if d > best:
            best, bi = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return dp(pts[:bi + 1], eps)[:-1] + dp(pts[bi:], eps)


def pip(x, y, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def centroid(rings):
    best = max(rings, key=len)
    a = cx = cy = 0
    for (x1, y1), (x2, y2) in zip(best, best[1:] + best[:1]):
        f = x1 * y2 - x2 * y1
        a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
    if abs(a) < 1e-6:
        return sum(p[0] for p in best) / len(best), sum(p[1] for p in best) / len(best)
    return cx / (3 * a), cy / (3 * a)


def grings(f):  # esri polygon (lon/lat) to metric rings
    return [[Pf(y, x) for x, y in r] for r in f['g']['rings']]


def gpt(f):
    return P(f['g']['y'], f['g']['x'])


clean = lambda s: re.sub(r'\s+', ' ', (s or '').replace('\r', ' ').replace('\n', ' ')).strip()

# ---------- boundary ----------
BR = grings(G['114']['f'][0])
inside = lambda x, y: any(pip(x, y, r) for r in BR)
bx = [p[0] for r in BR for p in r]; by = [p[1] for r in BR for p in r]
BB = (min(bx) - 1300, min(by) - 1300, max(bx) + 1300, max(by) + 1300)
inbb = lambda x, y: BB[0] <= x <= BB[2] and BB[1] <= y <= BB[3]


def dist_to_boundary(x, y):
    best = 1e18
    for r in BR:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            vx, vy = x2 - x1, y2 - y1
            l2 = vx * vx + vy * vy or 1
            t = max(0, min(1, ((x - x1) * vx + (y - y1) * vy) / l2))
            best = min(best, math.hypot(x - x1 - t * vx, y - y1 - t * vy))
    return best


boundary = [enc(dp(r + [r[0]], 1.5)) for r in BR]

# ---------- neighbourhoods (service areas) ----------
HOODS = []
for f in G['48']['f']:
    rr = grings(f)
    HOODS.append((clean(f['a']['zone_ser']), rr))


def hood_at(x, y):
    for n, rr in HOODS:
        if any(pip(x, y, r) for r in rr):
            return n
    return None


hoods = []
for n, rr in HOODS:
    cx, cy = centroid(rr)
    hoods.append([n, round(cx), round(cy)])

# ---------- registration zones ----------
zones = []
for f in G['22']['f']:
    n = clean(f['a']['Zone_Name'])
    zones.append({'n': 'אזור רישום ' + n, 'city': 'r', 'r': [enc(dp(r, 1.5)) for r in grings(f)]})

# ---------- OSM roads ----------
RC = {'motorway': 0, 'trunk': 0, 'motorway_link': 0, 'trunk_link': 0, 'primary': 1, 'primary_link': 1,
      'secondary': 2, 'secondary_link': 2, 'tertiary': 3, 'tertiary_link': 3,
      'residential': 4, 'unclassified': 4, 'living_street': 4, 'road': 4,
      'service': 5, 'pedestrian': 5}
WALK = set(RC) - {'motorway', 'motorway_link', 'trunk_link'} | {'footway', 'path', 'steps', 'cycleway', 'track', 'corridor'}
roads, labels_src, walk_ways = [], [], []
for e in A['hw']:
    tg = e['tg'] or {}
    h = tg.get('highway')
    g = [p for p in (e.get('g') or []) if p]
    if len(g) < 2:
        continue
    pts = [Pf(a, b) for a, b in g]
    if not any(inbb(x, y) for x, y in pts):
        continue
    if h in RC and tg.get('area') != 'yes':
        roads.append([RC[h]] + enc(dp(pts, 1.5)))
        nm = clean(tg.get('name:he') or tg.get('name'))
        if nm and re.search('[֐-׿]', nm):
            labels_src.append((nm, RC[h], pts))
    if h in WALK and tg.get('area') != 'yes' and tg.get('access') not in ('private', 'no') and tg.get('foot') not in ('no', 'private'):
        walk_ways.append(pts)

# labels: one per long stretch, near the middle, deduped by name within 260 m
LCLS = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}
labels, placed = [], collections.defaultdict(list)
for nm, rc, pts in sorted(labels_src, key=lambda t: (t[1], -sum(math.dist(a, b) for a, b in zip(t[2], t[2][1:])))):
    L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    if L < 70:
        continue
    half, acc = L / 2, 0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if acc + d >= half and d > 0:
            t = (half - acc) / d
            x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            break
        acc += d
    if not inside(x, y):
        continue
    if any(math.dist((x, y), q) < 260 for q in placed[nm]):
        continue
    placed[nm].append((x, y))
    labels.append([nm, round(x), round(y), round(ang, 2), LCLS[rc]])

# ---------- OSM green ----------
GT = {'park': 0, 'garden': 0, 'grass': 0, 'meadow': 0, 'village_green': 0, 'recreation_ground': 0, 'dog_park': 0, 'playground': 0,
      'water': 1, 'pitch': 2, 'forest': 3, 'wood': 3, 'scrub': 3, 'cemetery': 3}
green = []
for e in A['gr']:
    tg = e['tg'] or {}
    k = tg.get('leisure') or tg.get('landuse') or tg.get('natural') or ('water' if tg.get('water') else None)
    if k not in GT:
        continue
    rings = []
    if e['t'] == 'w' and e.get('g'):
        rings = [[Pf(a, b) for a, b in e['g'] if True]]
    elif e['t'] == 'r':
        rings = [[Pf(a, b) for a, b in [p for p in m['g'] if p]] for m in e.get('m', []) if m['r'] == 'outer']
    for r in rings:
        if len(r) < 3 or not any(inbb(x, y) for x, y in r):
            continue
        s = dp(r, 1.5)
        if len(s) >= 3:
            green.append([GT[k]] + enc(s))

# ---------- address index (GIS house numbers) ----------
addr = collections.defaultdict(dict)
bycode = {}
for f in G['112']['f']:
    a = f['a']
    st = clean(a['STREET_NAM']); hn = clean(str(a['HOUSE'] or ''))
    if not st or not hn:
        continue
    x, y = gpt(f)
    addr[st].setdefault(hn, (x, y))
    bycode[(int(a['STREET_COD']), hn)] = (x, y, st)


def numkey(h):
    m = re.match(r'(\d+)(.*)', h)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 6, h)


addr_out = {st: [[h, x, y] for h, (x, y) in sorted(v.items(), key=lambda kv: numkey(kv[0]))] for st, v in addr.items()}
streets = {}
for nm, rc, pts in labels_src:
    if nm in addr_out or nm in streets:
        continue
    mid = pts[len(pts) // 2]
    if inside(*mid):
        streets[nm] = [round(mid[0]), round(mid[1])]


def norm(s):
    s = clean(s).replace('״', '"').replace("׳", "'").replace('`', "'")
    s = re.sub(r'^(שד\'?|שדרות|רח\'?|רחוב|דרך)\s+', '', s)
    return s


NORM = collections.defaultdict(list)
for st in addr_out:
    NORM[norm(st)].append(st)
    NORM[norm(st).replace('"', '').replace("'", '')].append(st)


def geocode(street, num, code=None):
    """Returns (x, y, approx) or None. approx 2 = nearest number with the same parity."""
    num = str(num or '').strip()
    if code is not None and (code, num) in bycode:
        x, y, _ = bycode[(code, num)]
        return x, y, 0
    cands = NORM.get(norm(street)) or NORM.get(norm(street).replace('"', '').replace("'", ''))
    if not cands:
        w = set(norm(street).split())
        cands = [s for s in addr_out if w and w <= set(norm(s).split())]
    if not cands and code is not None:
        cands = sorted({st for (c, _), (_, _, st) in bycode.items() if c == code})
    for st in cands:
        v = addr[st]
        if num in v:
            return v[num] + (0,)
    for st in cands:
        nums = [(numkey(h)[0], h) for h in addr[st] if numkey(h)[0] < 10 ** 6]
        if num.isdigit() and nums:
            n = int(num)
            same = [t for t in nums if t[0] % 2 == n % 2] or nums
            t = min(same, key=lambda t: abs(t[0] - n))
            if abs(t[0] - n) <= 6:
                return addr[st][t[1]] + (2,)
    return None


def split_addr(a):
    m = re.match(r'^(.*?)\s+(\d+[א-ת]?)(?:\s*-\s*\d+)?\s*$', clean(a))
    return (m.group(1), m.group(2)) if m else (clean(a), '')


# ---------- points ----------
pts = []


def add(p):
    x, y = p['x'], p['y']
    if not p.get('noLoc') and not p.get('out') and not inside(x, y):
        return False
    if not p.get('noLoc') and not p.get('out'):
        h = hood_at(x, y)
        if h and 'hood' not in p:
            p['hood'] = h
    p['city'] = 'r'
    pts.append({k: v for k, v in p.items() if v not in (None, '', [])})
    return True


# kindergartens (GIS 16)
seen = set()
for f in G['16']['f']:
    a = f['a']; x, y = gpt(f)
    n = clean(a['Name']); ad = clean(a['Address'])
    key = (n, ad, x, y)
    if key in seen:
        continue
    seen.add(key)
    meg = 'דתי' if n.startswith('דתי ') else 'חרדי' if n.startswith('חרדי ') else None
    nm = n if n.startswith(('גן', 'בית', 'בן ', 'בני ')) else 'גן ' + n
    add({'c': 'gan', 'x': x, 'y': y, 'n': nm, 'a': ad, 'meg': meg, 'src': 'g'})

# daycares: Education Ministry first, then GIS-only (layer 44)
M = [m for m in json.load(open(os.path.join(RAW, 'meonot.json'), encoding='utf-8'))['list'] if m['codE_YISHUV_MISGERET'] == 66001]
no_loc_dc = []
e_pts = []
for m in M:
    st = clean(m['rechoV_MISGERET']); hn = str(m['mispaR_BAIT'] or '').strip()
    if hn in ('0', 'None'):
        hn = ''
    g = geocode(st, hn, m.get('codE_RECHOV_MISGERET'))
    ph = ''
    if m.get('telephonE_MAON'):
        ph = (str(m.get('kidomeT_TELEPHONE') or '').strip() + '-' + str(m['telephonE_MAON'])).strip('-')
    p = {'c': 'daycare', 'n': clean(m['sheM_MISGERET_IRGUNIT']).strip(' -'), 'a': (st + ' ' + hn).strip(),
         'st': clean(m['teuR_STATUS_RISHUY']), 'ph': ph, 'own': clean(m['sheM_BAALUT']),
         'sem': str(m['semeL_MISGERET_IRGUNIT']), 't': 'מעון יום בפיקוח משרד החינוך', 'src': 'e'}
    if m.get('semeL_MAON_KLKALA_MEHASAVA'):
        p['rec'] = 1
    if m.get('teuR_SHLAV_TIPUL') and 'צו הפסקה' in m['teuR_SHLAV_TIPUL']:
        p['warn'] = 1
    if g:
        p['x'], p['y'] = g[0], g[1]
        if g[2]:
            p['approx'] = g[2]
    else:
        p['x'], p['y'], p['noLoc'] = 0, 0, 1
        no_loc_dc.append(p['n'] + ' | ' + p['a'])
    if add(p):
        e_pts.append(p)
gis_only_dc = 0
for f in G['44']['f']:
    a = f['a']; x, y = gpt(f)
    ad = clean(a['Address'])
    near = [p for p in e_pts if not p.get('noLoc') and math.dist((p['x'], p['y']), (x, y)) < 40]
    sa = split_addr(ad)
    same_addr = [p for p in e_pts if split_addr(p['a']) == sa or (norm(split_addr(p['a'])[0]) == norm(sa[0]) and split_addr(p['a'])[1] == sa[1])]
    if near or same_addr:
        continue
    if add({'c': 'daycare', 'x': x, 'y': y, 'n': clean(a['Name']), 'a': ad, 't': 'מעון יום, לפי שכבת העירייה', 'src': 'g'}):
        gis_only_dc += 1

# tipat halav: Health Ministry, in the city plus nearby stations outside it (out:1, oc)
DAYS = 'אבגדהוש'
T = json.load(open(os.path.join(RAW, 'tipot.json'), encoding='utf-8'))
for t in T:
    if not t.get('yCordinate') or not t.get('xCordinate') or t.get('close'):
        continue
    x, y = P(t['yCordinate'], t['xCordinate'])
    cn = clean(t['cityName'])
    if not inbb(x, y):
        continue
    ins = inside(x, y) or cn == 'חולון'
    if not ins and (dist_to_boundary(x, y) > 1200):
        continue
    hrs = []
    for o in t.get('openingTimes') or []:
        iv = ', '.join(w['intervalOfTime'] for w in o.get('workingHours') or [] if w.get('intervalOfTime'))
        if iv and 1 <= o['dayNumber'] <= 7:
            hrs.append(DAYS[o['dayNumber'] - 1] + ' ' + iv)
    p = {'c': 'tipa', 'x': x, 'y': y, 'n': clean(t['stationName']), 'a': (clean(t['streetName']) + ' ' + clean(str(t.get('buildingNum') or ''))).strip(),
         'own': clean(t['ownerShip']), 'ph': clean(t.get('phone1')), 'st': clean(t.get('status')), 'h': ' | '.join(hrs), 'src': 'm'}
    if not ins:
        p['out'] = 1; p['oc'] = cn
        pts.append({**{k: v for k, v in p.items() if v not in (None, '')}, 'city': 'r'})
    else:
        if not inside(x, y):
            p['x'], p['y'] = x, y
            pts.append({**{k: v for k, v in p.items() if v not in (None, '')}, 'city': 'r', 'hood': hood_at(x, y)})
        else:
            add(p)

# gardens: GIS 30 (centroids), then named OSM parks/gardens not near a GIS garden
KEEP_PT = {'גן ציבורי': 'גינה ציבורית', 'גן סיפור': 'גן סיפור', 'פארק': 'פארק', 'חורשה': 'חורשה', 'גינה קהילת': 'גינה קהילתית'}
story = {clean(f['a']['PARKNAME']): f for f in G['31']['f']}
g_gardens = []
for f in G['30']['f']:
    a = f['a']; pt = clean(a.get('PARKTYPE'))
    if pt not in KEEP_PT:
        continue
    cx, cy = centroid(grings(f))
    n = clean(a.get('PARKNAME')) or KEEP_PT[pt]
    p = {'c': 'garden', 'x': round(cx), 'y': round(cy), 'n': n, 't': KEEP_PT[pt], 'src': 'g'}
    if pt == 'גן סיפור' and n in story:
        p['a'] = clean(story[n]['a'].get('PARKADDRES'))
    if add(p):
        g_gardens.append((p['x'], p['y']))
osm_gardens = 0
for e in A['pt']:
    tg = e['tg'] or {}
    if tg.get('leisure') not in ('park', 'garden') or not e.get('c'):
        continue
    nm = clean(tg.get('name:he') or tg.get('name'))
    if not nm or not re.search('[֐-׿]', nm):
        continue
    x, y = P(*e['c'])
    if any(math.dist((x, y), q) < 120 for q in g_gardens):
        continue
    if add({'c': 'garden', 'x': x, 'y': y, 'n': nm, 't': 'פארק' if tg['leisure'] == 'park' else 'גן', 'src': 'o'}):
        g_gardens.append((x, y)); osm_gardens += 1

# playgrounds: OSM, plus accessible play facilities from GIS 28
acc_pts = []
for f in G['28']['f']:
    cx, cy = centroid(grings(f))
    acc_pts.append((round(cx), round(cy), clean(f['a'].get('PARKNAME'))))
used_acc = set()
for e in A['pt']:
    tg = e['tg'] or {}
    if tg.get('leisure') != 'playground' or not e.get('c'):
        continue
    x, y = P(*e['c'])
    nm = clean(tg.get('name:he') or tg.get('name'))
    if nm and not re.search('[֐-׿]', nm):
        nm = ''
    p = {'c': 'play', 'x': x, 'y': y, 'n': nm or 'גן שעשועים', 'src': 'o'}
    near = [i for i, q in enumerate(acc_pts) if math.dist((x, y), q[:2]) < 60 and i not in used_acc]
    if near:
        used_acc.add(near[0]); p['t'] = 'כולל מתקני משחק נגישים, לפי העירייה'
    add(p)
for i, (x, y, n) in enumerate(acc_pts):
    if i in used_acc:
        continue
    add({'c': 'play', 'x': x, 'y': y, 'n': ('מתקני משחק נגישים, ' + n) if n else 'מתקני משחק נגישים', 't': 'מתקני משחק נגישים, לפי העירייה', 'src': 'g'})

# community centres: GIS 47, then OSM not within 80 m
c_pts = []
for f in G['47']['f']:
    a = f['a']; x, y = gpt(f)
    web = clean(a.get('Website'))
    p = {'c': 'comm', 'x': x, 'y': y, 'n': clean(a['Name']), 'a': clean(a['Address']), 't': 'מרכז קהילתי', 'src': 'g'}
    if web.startswith('https://') and 'holonet' in web and len(web) < 80:
        p['web'] = web
    if add(p):
        c_pts.append((x, y))
for e in A['pt']:
    tg = e['tg'] or {}
    if tg.get('amenity') != 'community_centre' or not e.get('c'):
        continue
    x, y = P(*e['c'])
    nm = clean(tg.get('name:he') or tg.get('name'))
    if not nm or not re.search('[֐-׿]', nm) or any(math.dist((x, y), q) < 80 for q in c_pts):
        continue
    if add({'c': 'comm', 'x': x, 'y': y, 'n': nm, 't': 'מתנ"ס' if 'מתנ' in nm else 'מרכז קהילתי', 'src': 'o'}):
        c_pts.append((x, y))

# shelters: GIS 35
for f in G['35']['f']:
    a = f['a']; x, y = gpt(f)
    add({'c': 'shelter', 'x': x, 'y': y, 'n': 'מקלט ציבורי ' + clean(a['Name']), 'a': clean(a['Address']), 't': 'מקלט ציבורי', 'src': 'g'})

# business: remote service, same as Rishon LeZion
pts.append({'c': 'biz', 'x': 0, 'y': 0, 'noLoc': 1, 'n': 'שירי אוסטרובסקי, יועצת שינה לתינוקות', 't': 'ייעוץ שינה לתינוקות: ליווי אישי, מפגש יחיד והרצאות',
            'a': 'ייעוץ טלפוני או בזום', 'ph': '050-7919871', 'web': 'https://www.shiri-sleep.co.il/', 'src': 'b',
            'gr': {'r': '5.0', 'n': 7, 'd': '13.11.2026', 'u': 'https://www.google.com/maps?cid=2806561564369078982'}, 'city': 'r'})

# ---------- walking network ----------
Q = 2.5
key = lambda p: (round(p[0] / Q), round(p[1] / Q))
cnt = collections.Counter()
ways = []
for w in walk_ways:
    if not any(inbb(x, y) for x, y in w):
        continue
    ks = [key(p) for p in w]
    ways.append((w, ks))
    for i, k in enumerate(ks):
        cnt[k] += 1 if 0 < i < len(ks) - 1 else 2
jid, JX = {}, []
edges = []
for w, ks in ways:
    start = 0
    for i in range(1, len(w)):
        if i == len(w) - 1 or cnt[ks[i]] >= 2:
            seg = w[start:i + 1]
            a, b = ks[start], ks[i]
            for k, p in ((a, seg[0]), (b, seg[-1])):
                if k not in jid:
                    jid[k] = len(JX); JX.append((k[0] * Q, k[1] * Q))
            L = sum(math.dist(p, q) for p, q in zip(seg, seg[1:]))
            if jid[a] != jid[b] or L > 5:
                edges.append((jid[a], jid[b], L, seg))
            start = i
# largest connected component
par = list(range(len(JX)))
def fd(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for a, b, _, _ in edges:
    par[fd(a)] = fd(b)
comp = collections.Counter(fd(i) for i in range(len(JX)))
big = comp.most_common(1)[0][0]
keep = [i for i in range(len(JX)) if fd(i) == big]
remap = {o: n for n, o in enumerate(keep)}
j = []
px = py = 0
for o in keep:
    x, y = round(JX[o][0]), round(JX[o][1])
    j += [x - px, y - py]; px, py = x, y
e_out = []
for a, b, L, seg in edges:
    if a not in remap or b not in remap or (a == b and L < 5):
        continue
    mid = dp(seg, 1.5)[1:-1]
    r = [remap[a], remap[b], max(1, round(L))]
    qx, qy = round(JX[a][0]), round(JX[a][1])
    for x, y in mid:
        x, y = round(x), round(y)
        r += [x - qx, y - qy]; qx, qy = x, y
    e_out.append(r)

data = {'boundary': boundary, 'roads': roads, 'green': green, 'hoods': hoods, 'addr': addr_out, 'streets': streets,
        'pts': pts, 'zones': zones, 'labels': labels}
os.makedirs(OUT, exist_ok=True)
json.dump(data, open(os.path.join(OUT, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'j': j, 'e': e_out}, open(os.path.join(OUT, 'walk.json'), 'w'), separators=(',', ':'))
c = collections.Counter(p['c'] for p in pts)
print('points', dict(c))
print('by src', dict(collections.Counter((p['c'], p['src']) for p in pts)))
print('daycare rec', sum(1 for p in pts if p.get('rec')), 'approx', sum(1 for p in pts if p.get('approx')), 'noLoc', no_loc_dc, 'gis-only', gis_only_dc)
print('tipa out', [(p['n'], p.get('oc')) for p in pts if p['c'] == 'tipa' and p.get('out')])
print('roads', len(roads), 'green', len(green), 'labels', len(labels), 'streets idx', len(addr_out), 'nums', sum(len(v) for v in addr_out.values()), 'streets w/o nums', len(streets))
print('walk nodes', len(keep), 'of', len(JX), 'edges', len(e_out))
print('sizes', len(json.dumps(data, ensure_ascii=False, separators=(',', ':'))), len(json.dumps({'j': j, 'e': e_out}, separators=(',', ':'))))
