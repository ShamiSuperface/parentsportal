"""Rebuild the city list on the home page and the sitemap from cities.json.
Usage: python3 tools/sync_cities.py   (run from the repo root)
cities.json is the one source for the list of cities: the home page and sitemap come from here,
and every city page reads it at runtime for its "other city" switch."""
import json, re, html

SITE = 'https://parentsportal.org.il'
cities = json.load(open('cities.json', encoding='utf-8'))
for c in cities:
    assert re.fullmatch(r'[a-z-]+', c['slug']) and c['name'], c

e = html.escape
nav = ('<nav class="cities" aria-label="ערים">'
       + ''.join(f'<a class="city" href="/{c["slug"]}/"><span class="cn">{e(c["name"])}</span><span class="cd">{e(c.get("desc", ""))}</span></a>' for c in cities)
       + '</nav>')
s = open('index.html', encoding='utf-8').read()
s2, k = re.subn(r'<nav class="cities" aria-label="ערים">.*?</nav>', lambda m: nav, s, count=1, flags=re.S)
assert k == 1
open('index.html', 'w', encoding='utf-8').write(s2)

sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      f'  <url><loc>{SITE}/</loc></url>\n'
      + ''.join(f'  <url><loc>{SITE}/{c["slug"]}/</loc></url>\n' for c in cities)
      + '</urlset>\n')
open('sitemap.xml', 'w', encoding='utf-8').write(sm)
print('home page and sitemap:', ', '.join(c['slug'] for c in cities))
