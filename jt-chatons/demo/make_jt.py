"""JT des chatons complet : plateau, 6 duplex (un par parti), clôture. Réutilise les dessins de make_demo."""
import json, os, subprocess
from PIL import Image, ImageDraw
import make_demo as m

OUT = m.OUT
DATE = 'samedi 10 octobre 2026'

ANCHOR = dict(fur='#f0a35e', mask=None, helmet='#f6ead2', trim='#d9a441', robe='#f6ead2', stripes=True, stripe='#c8641e')

# Textes rédigés uniquement à partir des titres de presse récupérés (news.json), source citée.
REPORTS = [
    dict(tag='LFI', color='#cc2444', trim='#e5c15a', fur='#f3e6cf', mask='#6b4a3a', stripes=False, stripe=None,
         name='Pacha le Siamois', source='LCP',
         title='Niche parlementaire : les textes de LFI',
         text="La France insoumise prépare sa niche parlementaire du 29 octobre. Selon LCP, ses textes porteront notamment sur les salaires, les pesticides et les AESH."),
    dict(tag='RN', color='#1b3a75', trim='#e5c15a', fur='#8c96a6', mask=None, stripes=False, stripe=None,
         name='Gaspard le Chartreux', source='site du Rassemblement national',
         title="Nouvelles nominations dans l'équipe de Marine Le Pen",
         text="Au Rassemblement national, l'équipe de campagne de Marine Le Pen accueille de nouveaux membres. Le parti a annoncé ces nominations sur son site."),
    dict(tag='REN', color='#ff8a00', trim='#3b6fd1', fur='#a8744a', mask=None, stripes=True, stripe='#6b4423',
         name='Mandarine la Maine Coon', source='Le Dauphiné Libéré',
         title='Gabriel Attal en meeting dans la Drôme',
         text="Chez Renaissance, Gabriel Attal tient un meeting dans la Drôme. Selon Le Dauphiné Libéré, le maire de Montélimar, Julien Cornillet, doit y prendre la parole."),
    dict(tag='PS', color='#e75480', trim='#b9a7e0', fur='#f7ede2', mask=None, stripes=False, stripe=None,
         name='Pivoine la Persane', source='BFM',
         title='Primaire PS : plus de 91 000 votants à 14 h',
         text="La primaire du Parti socialiste et de Place publique se poursuit. Selon BFM, plus de quatre-vingt-onze mille votants étaient comptabilisés ce samedi à quatorze heures."),
    dict(tag='EELV', color='#3aaa35', trim='#f2e14b', fur='#fbfbf7', mask=None, stripes=False, stripe=None,
         name="Flocon l'Angora", source='franceinfo',
         title='Sandrine Rousseau veut accélérer la désignation',
         text="Chez Les Écologistes, Sandrine Rousseau appelle à accélérer le processus de désignation pour la présidentielle, rapporte franceinfo."),
    dict(tag='LR', color='#0066cc', trim='#ffffff', fur='#9a8a78', mask=None, stripes=True, stripe='#5e5246',
         name='Bjorn le Norvégien', source='Ouest-France',
         title="Bruno Retailleau veut refondre l'école",
         text="Pour Bruno Retailleau, candidat à la présidentielle, il faut une refonte complète du système éducatif. Il l'affirme dans un entretien à Ouest-France."),
]

SCENES = [dict(kind='anchor', title=f'Le JT des Chatons · {DATE}', sub='Maître Moustache · Présentateur',
               text="Bonsoir, et bienvenue dans le JT des chatons. Ce soir, nos six reporters font le tour des partis politiques.")]
SCENES += [dict(kind='reporter', **r) for r in REPORTS]
SCENES += [dict(kind='anchor', title='Fin du journal', sub='Sources : titres de presse du 8 au 10 octobre 2026, via Google Actualités',
                text="C'est la fin de ce journal. Merci de l'avoir suivi, et bonne soirée.")]

_bg_cache = {}
def background(sc):
    key = sc.get('tag', 'studio')
    if key not in _bg_cache:
        _bg_cache[key] = m.studio() if sc['kind'] == 'anchor' else m.square(sc['color'])
    return _bg_cache[key].copy()

def frame(sc, t, dur):
    W, H, S = m.W, m.H, m.S
    import math
    blink = (t % 2.7) < 0.12
    mouth = 0.4 < t < dur - 0.6 and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.2) * 4
    im = background(sc); d = ImageDraw.Draw(im)
    if sc['kind'] == 'anchor':
        m.draw_cat(d, W / 2, 300 + bob, 1.0, blink=blink, mouth=mouth, **ANCHOR)
        m.desk(d)
        ov = ('#e5c15a', 'JT', sc['title'], sc['sub'], False)
        zoom = 1 + 0.07 * (t / dur)
    else:
        m.draw_cat(d, W / 2, 250 + bob, 1.05, fur=sc['fur'], mask=sc['mask'], helmet=sc['color'], trim=sc['trim'],
                   robe=sc['color'], blink=blink, mouth=mouth, mic=True, stripes=sc['stripes'], stripe=sc['stripe'] or '#000')
        ov = (sc['color'], sc['tag'], sc['title'], f"{sc['name']} · En duplex · Source : {sc['source']}", False)
        zoom = 1.06 - 0.06 * (t / dur)
    cw, ch = W * S / zoom, H * S / zoom
    x0, y0 = (W * S - cw) / 2, (H * S - ch) / 2
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W * S, H * S), Image.BILINEAR)
    m.overlay(im, *ov)
    return im.resize((W, H), Image.LANCZOS)

def main():
    W, H, FPS = m.W, m.H, m.FPS
    voices, durs = [], []
    for i, sc in enumerate(SCENES):
        p, d = m.tts(f'jt{i}', sc['text']); voices.append(p); durs.append(max(6.0, d + 1.0))
    total = sum(durs)
    filt, inputs, start = [], [], 0.0
    for i, (p, d) in enumerate(zip(voices, durs)):
        inputs += ['-i', p]
        ms = int((start + 0.4) * 1000)
        filt.append(f'[{i}:a]adelay={ms}|{ms}[a{i}]')
        start += d
    filt.append(''.join(f'[a{i}]' for i in range(len(voices))) + f'amix=inputs={len(voices)}:normalize=0,apad,atrim=0:{total}[aout]')
    wav = os.path.join(OUT, 'jt_audio.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[aout]', wav])
    dest = os.path.join(OUT, 'JT-des-chatons-2026-10-10.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', dest], stdin=subprocess.PIPE)
    for n_sc, (sc, dur) in enumerate(zip(SCENES, durs)):
        for f in range(int(dur * FPS)):
            t = f / FPS
            im = frame(sc, t, dur)
            fade = min(1, t / 0.3, (dur - t) / 0.3)
            if fade < 1:
                im = Image.blend(Image.new('RGB', (W, H)), im, max(0, fade))
            enc.stdin.write(im.tobytes())
        print(f'scène {n_sc + 1}/{len(SCENES)} rendue', flush=True)
    enc.stdin.close(); enc.wait()
    print('TERMINÉ', dest, round(total, 1), 's', flush=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        tiles = [frame(sc, 3.0, 9) for sc in SCENES[1:7]]
        sheet = Image.new('RGB', (m.W, m.H))
        for i, t in enumerate(tiles):
            sheet.paste(t.resize((m.W // 3, m.H // 3)), ((i % 3) * m.W // 3, (i // 3) * m.H // 3))
        sheet.crop((0, 0, m.W, 2 * m.H // 3)).save(os.path.join(OUT, 'preview.png'))
    else:
        main()
