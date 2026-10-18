"""Règle de l'utilisateur : 5 hashtags max. Les 2 premiers toujours #actu #politique (très utilisés),
les 3 autres tournent parmi des hashtags populaires."""
import re
TAGS = {'1-RN-dimanche-11': '#marinelepen #france #info', '2-Renaissance-lundi-12': '#attal #info #chat',
        '3-Ecologistes-mardi-13': '#ecologie #france #chat', '4-LR-mercredi-14': '#education #france #humour',
        '5-LFI-jeudi-15': '#melenchon #info #humour'}
for slug, tags in TAGS.items():
    p = f'descriptions/{slug}.txt'
    body = re.sub(r'\n?#.*$', '', open(p, encoding='utf-8').read().strip(), flags=re.S).strip()
    open(p, 'w', encoding='utf-8').write(body + '\n#actu #politique ' + tags + '\n')
    print(open(p, encoding='utf-8').read())
