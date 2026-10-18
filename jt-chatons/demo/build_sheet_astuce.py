import csv, json, os, sys
sys.path.insert(0, os.getcwd())
import make_daily as md
import wan

cfg = json.load(open('daily/multi-2026-10-15-astuce.json', encoding='utf-8'))
blocs = open('daily/2026-10-15/sous-titres-astuce.srt', encoding='utf-8').read().strip().split('\n\n')


def sec(x):
    h, m, r = x.split(':')
    s, ms = r.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def hms(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


debuts = [sec(b.split('\n')[1].split(' --> ')[0]) for b in blocs]
fins = [sec(b.split('\n')[1].split(' --> ')[1]) for b in blocs]

rows = [["Plan", "Début", "Fin", "Durée (s)", "Personnage", "Décor", "Action",
         "Dialogue exact", "Texte à l'écran", "Prompt visuel (image)", "Prompt d'animation", "Transition"]]
for k, (sg, d, f) in enumerate(zip(cfg['segments'], debuts, fins), 1):
    subj = sg['subject']
    if 'ginger' in subj:
        perso = 'Présentateur (chaton roux en costume)'
    elif 'cardigan' in subj:
        perso = 'Testeur (chaton blanc en gilet bleu)'
    else:
        perso = 'Copain (chaton noir et blanc)'
    acc = sg.get('accessory', '')
    image_prompt = md.STYLE + sg['subject'] + (f"with {acc}, " if acc else '') + f"{sg['action']}. Setting: {sg['bg']}."
    anim_prompt = (f"The kitten keeps doing the action with fast, realistic movement: {sg['action']}. "
                   "Dynamic camera tracking, motion blur." + wan.motion(sg.get('bg', '')))
    ecran = f"Accroche au début : « {cfg['hook1']} » puis « {cfg['hook2']} ». Sous-titres incrustés : la phrase du plan." if k == 1 \
        else 'Sous-titres incrustés : la phrase du plan.'
    rows.append([k, hms(d), hms(f), f"{f - d:.2f}", perso, sg['bg'], sg['action'], sg['text'], ecran,
                 image_prompt, anim_prompt, 'Zoom bref à la coupe, puis plan suivant' if k < len(debuts) else 'Fin de la voix, la vidéo s’arrête'])

out = 'daily/2026-10-15/decoupage-astuce.csv'
with open(out, 'w', encoding='utf-8-sig', newline='') as fh:
    csv.writer(fh, delimiter=';').writerows(rows)
print('écrit', out, '| plans :', len(rows) - 1)
