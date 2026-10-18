"""Titres politiques des dernières 24 h par parti (Google Actualités), du plus récent au plus ancien."""
import urllib.request, xml.etree.ElementTree as ET, email.utils, datetime, json, sys
Q = {'lfi': '%22La+France+insoumise%22+OR+LFI+OR+M%C3%A9lenchon', 'rn': '%22Rassemblement+National%22+OR+Bardella+OR+%22Marine+Le+Pen%22',
     'ren': 'Renaissance+Attal+OR+Macron', 'ps': '%22Parti+socialiste%22+OR+Faure+OR+primaire+socialiste',
     'eelv': '%22Les+%C3%89cologistes%22+OR+Tondelier+OR+Rousseau', 'lr': '%22Les+R%C3%A9publicains%22+OR+Retailleau'}
out = {}
now = datetime.datetime.now(datetime.timezone.utc)
for k, q in Q.items():
    url = f'https://news.google.com/rss/search?q={q}+when:1d&hl=fr&gl=FR&ceid=FR:fr'
    try:
        x = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25).read()
        items = []
        for it in ET.fromstring(x).iter('item'):
            t = it.findtext('title') or ''; src = it.findtext('source') or ''; d = it.findtext('pubDate')
            if src and t.endswith(' - ' + src): t = t[:-(len(src) + 3)]
            dt = email.utils.parsedate_to_datetime(d) if d else None
            age = round((now - dt).total_seconds() / 3600, 1) if dt else None
            items.append({'age_h': age, 'source': src, 'title': t})
        items.sort(key=lambda i: i['age_h'] if i['age_h'] is not None else 99)
        out[k] = items[:10]
    except Exception as e:
        out[k] = [{'error': str(e)}]
json.dump(out, open('daily_news.json', 'w'), ensure_ascii=False, indent=1)
for k, v in out.items():
    print('==', k)
    for i in v: print(f"  {i.get('age_h')}h | {i.get('source')} | {i.get('title', i.get('error'))}")
