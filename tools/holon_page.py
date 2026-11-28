"""Create holon/index.html from the Rishon LeZion page (shared code), with Holon's three JSON blocks and fixed strings.
Usage: python3 tools/holon_page.py DATA_JSON WALK_JSON   (run from the repository root)"""
import json, re, sys, urllib.parse, os

SRC = 'rishon-lezion/index.html'
s = open(SRC, encoding='utf-8').read()
data = open(sys.argv[1], encoding='utf-8').read()
walk = open(sys.argv[2], encoding='utf-8').read()
D = json.loads(data)
cnt = lambda c: sum(1 for p in D['pts'] if p['c'] == c)

INFO = f'''
  <p>הפורטל מרכז לתושבי חולון עם ילדים מלידה ועד גיל 4 את המקומות הרלוונטיים בעיר.</p>
  <h3>מה תמצאו בפורטל</h3>
  <ul>
   <li>גני ילדים, ואזורי הרישום לגנים.</li>
   <li>מעונות יום.</li>
   <li>מרכזים קהילתיים.</li>
   <li>טיפות חלב של משרד הבריאות, וגם תחנות סמוכות בערים השכנות.</li>
   <li>גינות ציבוריות וגני הסיפור של חולון.</li>
   <li>גני שעשועים, כולל מתקני משחק נגישים.</li>
   <li>מקלטים ציבוריים.</li>
  </ul>
  <p>במעונות היום מסומנים המעונות המוכרים לסבסוד, לפי רשימת משרד החינוך. אפשר לשמור גנים ומעונות ב"רשימה שלי" כדי להשוות ולהתקשר.</p>
  <h3>מה כדאי לדעת</h3>
  <ul>
   <li>"בתהליך רישוי" פירושו שהמעון עדיין לא קיבל רישיון בתוקף. לפני רישום בדקו מחיר, זמינות מקום וסטטוס עדכני.</li>
   <li>פתיחת מקלטים ומצבם משתנים. בשעת חירום פעלו לפי הנחיות פיקוד העורף ועדכוני העירייה.</li>
   <li>תורים לטיפת חלב: מוקד משרד הבריאות ‎*5400.</li>
   <li>בנתוני הגנים של העירייה אין גילאים לכל גן, ולכן הסינון לפי גיל לא מוצג. אזור הרישום של הכתובת מוצג לפי מפת אזורי הרישום של העירייה. השיבוץ עצמו נעשה באגף גני ילדים.</li>
   <li>בנתוני העירייה יש {cnt('shelter')} מקלטים ציבוריים. בבניינים רבים יש מרחב מוגן או מקלט בניין שלא מופיעים כאן.</li>
  </ul>
  <h3>מדידת מרחק</h3>
  <p>כפתור "מדידה" בצד המפה מפעיל מדידת מרחק בין נקודות ציון. כל לחיצה על המפה מוסיפה נקודה, ומוצגים המרחק של כל קטע, המרחק הכולל וזמן הליכה משוער. המרחק בכל קטע מחושב כמסלול הליכה לפי רשת הרחובות. כשנקודה רחוקה מרחוב, הקטע שלה נמדד בקו אווירי, ותיבת המדידה מציינת זאת. המסלול משוער ולא מתחשב במעברי חצייה וברמזורים.</p>
  <h3>הוספת מקומות</h3>
  <p>חסר מקום? בכל קטגוריה יש כפתור "הציעו מקום". ההצעה נשלחת בהודעת WhatsApp למנהל המפה, ומקומות שאושרו מתווספים למפה בעדכון הבא ומסומנים במקור "הצעת גולשים".</p>
  <h3>פרטיות</h3>
  <p>הפורטל סופר כניסות ושימוש באופן אנונימי, כדי לדעת מה מועיל להורים: כמה נכנסו, אילו סוגי מקומות נבחרו ואילו כרטיסים נפתחו. הכתובת שאתם מזינים והמיקום שלכם נשארים במכשיר שלכם ולא נשלחים לשום מקום. לא נאספים שמות או מספרי טלפון, ואין עוגיות.</p>
  <h3>מקורות המידע</h3>
  <p class="note">מערכת ה־GIS של עיריית חולון (גני ילדים, אזורי רישום לגנים, מעונות יום, גינות ופארקים, גני סיפור, מתקני משחק נגישים, מרכזים קהילתיים, מקלטים ציבוריים, שכונות ומספרי בתים), משרד החינוך (מעונות יום בפיקוח), משרד הבריאות (טיפות חלב) ו־OpenStreetMap (גני שעשועים, מרכזים קהילתיים נוספים ומפת הרקע; © תורמי OpenStreetMap, ברישיון ODbL). הנתונים נאספו ב־28 בנובמבר 2026.</p>
  <p class="copy">© כל הזכויות שמורות ל־SuperFace שמי אוסטרובסקי 2026</p>'''

CITY = {
    'full': 'חולון', 'lat0': 32.0137, 'lon0': 34.785,
    'src': {'g': 'GIS עיריית חולון', 'm': 'משרד הבריאות, מאתר טיפות החלב', 'o': 'OpenStreetMap',
            'e': 'משרד החינוך, איתור מעונות יום בפיקוח', 'u': 'הצעת גולשים, אושרה על ידי מנהל המפה'},
    'keys': {'state': 'holkids1', 'theme': 'pp-theme', 'intro': 'holkids-intro'},
    'code': 'HOL1', 'main': 'r', 'names': {'r': 'חולון'}, 'multi': False,
    'zoneKind': {'r': 'אזור רישום לגנים'},
    'inCity': 'בחולון',
    'introSrc': 'המידע מגיע מעיריית חולון וממשרדי הממשלה. השימוש בפורטל חינם.',
    'devNote': '',
    'contacts': {'cards': [{'t': 'אגף גני ילדים, עיריית חולון', 'rows': [
        ['טלפון', {'tel': '03-5027140'}],
        ['WhatsApp', {'href': 'https://wa.me/972506007010', 'label': '050-6007010'}],
        ['דוא״ל', {'ltr': 'rgan@holon.muni.il'}],
        ['רישום לגנים', {'href': 'https://www.holon.muni.il/Residents/Education/KinderGardens/pages/registrationprocess1.aspx', 'label': 'רישום ושיבוץ לגני הילדים, באתר העירייה'}]]}],
        'notes': ['לפי אתר העירייה, הרישום לגני הילדים לשנת תשפ״ח מתקיים בין 10.1.2027 ל־31.1.2027, באופן מקוון בלבד. הפרטים נלקחו מאתר העירייה ב־28.11.2026, ומומלץ לבדוק שם לפני הרישום.']},
    'info': INFO, 'slug': 'holon', 'site': 'https://parentsportal.org.il/holon/'}


def block(s, bid, content):
    pat = re.compile(r'(<script id="%s" type="application/json">)(.*?)(</script>)' % bid, re.S)
    assert len(pat.findall(s)) == 1, bid
    return pat.sub(lambda m: m.group(1) + content.replace('</', '<\\/') + m.group(3), s)


s = block(s, 'data', data)
s = block(s, 'walk', walk)
s = block(s, 'city', json.dumps(CITY, ensure_ascii=False))

# fixed strings: only in the head and the static HTML before the main script
cut = s.index('<script id="data"')
head, rest = s[:cut], s[cut:]
fab = re.search(r'id="shareFab" class="fab" href="([^"]+)"', head).group(1)
txt = urllib.parse.unquote(fab.split('text=', 1)[1]).replace('ראשון לציון', 'חולון').replace('rishon-lezion', 'holon')
head = head.replace(fab, 'https://wa.me/?text=' + urllib.parse.quote(txt, safe=''))


def rep(a, b, n=None):
    global head
    c = head.count(a)
    assert c and (n is None or c == n), (a, c)
    head = head.replace(a, b)


rep('בראשון לציון', 'בחולון', 3)
rep('ראשון לציון', 'חולון')
rep('rishon-lezion', 'holon')
rep('גני ילדים עירוניים ומעונות יום</li>', 'גני ילדים ומעונות יום, עם אזור הרישום שלכם</li>', 1)
rep('למשל רוטשילד 20', 'למשל סוקולוב 20', 1)
assert 'ראשון' not in head and 'rishon' not in head
os.makedirs('holon', exist_ok=True)
open('holon/index.html', 'w', encoding='utf-8').write(head + rest)
print('ok', len(head + rest))
