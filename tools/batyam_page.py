"""Create bat-yam/index.html from the Holon page (shared code), with Bat Yam's three JSON blocks and fixed strings.
Usage: python3 tools/batyam_page.py DATA_JSON WALK_JSON   (run from the repository root)"""
import json, re, sys, urllib.parse, os

SRC = 'holon/index.html'
s = open(SRC, encoding='utf-8').read()
data = open(sys.argv[1], encoding='utf-8').read()
walk = open(sys.argv[2], encoding='utf-8').read()
D = json.loads(data)
cnt = lambda c: sum(1 for p in D['pts'] if p['c'] == c)

INFO = f'''
  <p>הפורטל מרכז לתושבי בת ים עם ילדים מלידה ועד גיל 4 את המקומות הרלוונטיים בעיר.</p>
  <h3>מה תמצאו בפורטל</h3>
  <ul>
   <li>גני ילדים עירוניים, עם הגילאים של כל גן לשנת תשפ״ז.</li>
   <li>מעונות יום.</li>
   <li>מתנ״סים, המרכז לגיל הרך וספריות.</li>
   <li>טיפות חלב של משרד הבריאות, וגם תחנות סמוכות בחולון וביפו.</li>
   <li>גינות ציבוריות.</li>
   <li>גני שעשועים.</li>
   <li>מקלטים ציבוריים ומקלטים פתוחים.</li>
  </ul>
  <p>במעונות היום מסומנים המעונות המוכרים לסבסוד, לפי רשימת משרד החינוך. אפשר לשמור גנים ומעונות ב"רשימה שלי" כדי להשוות ולהתקשר.</p>
  <h3>מה כדאי לדעת</h3>
  <ul>
   <li>"בתהליך רישוי" פירושו שהמעון עדיין לא קיבל רישיון בתוקף. לפני רישום בדקו מחיר, זמינות מקום וסטטוס עדכני.</li>
   <li>הגילאים והכתובות של הגנים לקוחים מרשימת גני הילדים לתשפ״ז באתר העירייה. {sum(1 for p in D['pts'] if p['c'] == 'gan' and not p.get('age'))} גנים מופיעים בנתוני העירייה לתשפ״ו ולא ברשימה של תשפ״ז, והם מסומנים בכרטיס. כדאי לברר עליהם באגף הגיל הרך.</li>
   <li>בנתוני העירייה אין מפה של אזורי רישום לגנים, ולכן אזור הרישום לא מוצג. השיבוץ נעשה באגף הגיל הרך.</li>
   <li>גני השעשועים מגיעים מ־OpenStreetMap בלבד, כי בנתוני העירייה אין רשימה שלהם. ייתכן שחסרים גני שעשועים. אפשר להציע אותם בכפתור "הציעו מקום".</li>
   <li>פתיחת מקלטים ומצבם משתנים. בשעת חירום פעלו לפי הנחיות פיקוד העורף ועדכוני העירייה. בבניינים רבים יש מרחב מוגן או מקלט בניין שלא מופיעים כאן.</li>
   <li>תורים לטיפת חלב: מוקד משרד הבריאות ‎*5400.</li>
  </ul>
  <h3>מדידת מרחק</h3>
  <p>כפתור "מדידה" בצד המפה מפעיל מדידת מרחק בין נקודות ציון. כל לחיצה על המפה מוסיפה נקודה, ומוצגים המרחק של כל קטע, המרחק הכולל וזמן הליכה משוער. המרחק בכל קטע מחושב כמסלול הליכה לפי רשת הרחובות. כשנקודה רחוקה מרחוב, הקטע שלה נמדד בקו אווירי, ותיבת המדידה מציינת זאת. המסלול משוער ולא מתחשב במעברי חצייה וברמזורים.</p>
  <h3>הוספת מקומות</h3>
  <p>חסר מקום? בכל קטגוריה יש כפתור "הציעו מקום". ההצעה נשלחת בהודעת WhatsApp למנהל המפה, ומקומות שאושרו מתווספים למפה בעדכון הבא ומסומנים במקור "הצעת גולשים".</p>
  <h3>פרטיות</h3>
  <p>הפורטל סופר כניסות ושימוש באופן אנונימי, כדי לדעת מה מועיל להורים: כמה נכנסו, אילו סוגי מקומות נבחרו ואילו כרטיסים נפתחו. הכתובת שאתם מזינים והמיקום שלכם נשארים במכשיר שלכם ולא נשלחים לשום מקום. לא נאספים שמות או מספרי טלפון, ואין עוגיות.</p>
  <h3>מקורות המידע</h3>
  <p class="note">מערכת ה־GIS של עיריית בת ים (גני ילדים, מעונות יום, גינות ציבוריות, מתנ״סים, ספריות, מקלטים, שכונות ומספרי בתים), רשימת גני הילדים לתשפ״ז באתר עיריית בת ים (כתובות וגילאים), משרד החינוך (מעונות יום בפיקוח), משרד הבריאות (טיפות חלב) ו־OpenStreetMap (גני שעשועים, גינות ומרכזים נוספים ומפת הרקע; © תורמי OpenStreetMap, ברישיון ODbL). הנתונים נאספו ב־28 בנובמבר 2026.</p>
  <p class="copy">© כל הזכויות שמורות ל־SuperFace שמי אוסטרובסקי 2026</p>'''

CITY = {
    'full': 'בת ים', 'lat0': 32.013, 'lon0': 34.7476,
    'src': {'g': 'עיריית בת ים: GIS ורשימת גני הילדים באתר העירייה', 'm': 'משרד הבריאות, מאתר טיפות החלב', 'o': 'OpenStreetMap',
            'e': 'משרד החינוך, איתור מעונות יום בפיקוח', 'u': 'הצעת גולשים, אושרה על ידי מנהל המפה'},
    'keys': {'state': 'bykids1', 'theme': 'pp-theme', 'intro': 'bykids-intro'},
    'code': 'BY1', 'main': 'r', 'names': {'r': 'בת ים'}, 'multi': False,
    'zoneKind': {'r': 'אזור רישום לגנים'},
    'inCity': 'בבת ים',
    'introSrc': 'המידע מגיע מעיריית בת ים וממשרדי הממשלה. השימוש בפורטל חינם.',
    'devNote': '',
    'contacts': {'cards': [{'t': 'אגף הגיל הרך, עיריית בת ים', 'rows': [
        ['טלפון', {'tel': '03-5556398'}],
        ['טלפון נוסף', {'tel': '03-5556328'}],
        ['כתובת', 'החשמונאים 27, חדר 108'],
        ['מענה טלפוני', 'א׳, ב׳, ד׳, ה׳ 08:30-13:30, ג׳ 08:30-12:30'],
        ['קבלת קהל', 'א׳, ב׳, ד׳, ה׳ 08:30-13:30, ג׳ 16:00-18:00'],
        ['רישום לגנים', {'href': 'https://www.bat-yam.muni.il/he/884/', 'label': 'רישום לגני הילדים, באתר העירייה'}],
        ['רשימת הגנים', {'href': 'https://www.bat-yam.muni.il/he/818/', 'label': 'רשימת גני הילדים לתשפ״ז, באתר העירייה'}]]}],
        'notes': ['הפרטים נלקחו מאתר העירייה ב־28.11.2026. מועדי הרישום לתשפ״ח עוד לא נמצאו באתר העירייה, ומומלץ לבדוק שם לפני הרישום.']},
    'info': INFO, 'slug': 'bat-yam', 'site': 'https://parentsportal.org.il/bat-yam/'}


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
txt = urllib.parse.unquote(fab.split('text=', 1)[1]).replace('חולון', 'בת ים').replace('/holon/', '/bat-yam/')
head = head.replace(fab, 'https://wa.me/?text=' + urllib.parse.quote(txt, safe=''))


def rep(a, b, n=None):
    global head
    c = head.count(a)
    assert c and (n is None or c == n), (a, c)
    head = head.replace(a, b)


rep('בחולון', 'בבת ים', 3)
rep('חולון', 'בת ים')
rep('/holon/', '/bat-yam/')
rep('גני ילדים ומעונות יום, עם אזור הרישום שלכם</li>', 'גני ילדים עירוניים ומעונות יום</li>', 1)
rep('למשל סוקולוב 20', 'למשל בלפור 50', 1)
assert 'חולון' not in head and 'holon' not in head, [m.start() for m in re.finditer('holon|חולון', head)]
os.makedirs('bat-yam', exist_ok=True)
open('bat-yam/index.html', 'w', encoding='utf-8').write(head + rest)
print('ok', len(head + rest))
