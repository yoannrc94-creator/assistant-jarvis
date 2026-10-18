"""JT des chatons du jour : image Agnes -> animation Agnes (avec délai max) -> montage vertical -> description.

Usage : python3 make_daily.py config.json
config.json : {"date": "2026-10-11", "slot": "matin|midi|soir|bonus", "party": "ps", "hook1": "...", "hook2": "...", "text": "...",
               "source": "Libération", "bg": "décor en anglais", "description": "...", "accessory": "accessoire en anglais (facultatif)", "video_minutes": 100}
"""
import wan
import asyncio, json, os, subprocess, sys, time, urllib.request
from PIL import Image, ImageDraw
import gen_img, vid, make_tiktok as m, make_shorts as s

D = m.D
PARTIES = {
    'lfi':  dict(gvoice='Fenrir', gstyle="jeune reporter surexcité, parle très vite, plein d'énergie, s'emballe, enthousiaste", tag='LFI', color='#cc2444', name='Pacha le Siamois', voice='fr-FR-DeniseNeural', cat='Siamese', col='crimson red', trim='gold', catch="Et moi, je file chasser un papillon.", rate='+16%', pitch='+12Hz', tags='#lfi #franceinsoumise'),
    'rn':   dict(gvoice='Algenib', gstyle="reporter blasé, voix grave et lasse, débit posé, soupire légèrement, pince-sans-rire", tag='RN', color='#1b3a75', name='Gaspard le Chartreux', voice='fr-FR-RemyMultilingualNeural', cat='blue-gray Chartreux', col='deep navy blue', trim='gold', catch="Et moi, je retourne à ma sieste.", rate='-6%', pitch='-8Hz', tags='#rn #rassemblementnational'),
    'ren':  dict(gvoice='Laomedeia', gstyle="reporter pressée et débordée, parle très vite, un peu essoufflée, dynamique", tag='RENAISSANCE', color='#ff8a00', name='Mandarine la Maine Coon', voice='fr-FR-VivienneMultilingualNeural', cat='fluffy brown tabby Maine Coon', col='bright tangerine orange', trim='sky blue', catch="Et moi, je vais faire mes griffes sur le pupitre.", rate='+20%', pitch='+4Hz', tags='#renaissance #gabrielattal'),
    'ps':   dict(gvoice='Kore', gstyle="jeune journaliste de télé précieuse et perfectionniste, très expressive et enjouée, rythme rapide et dynamique, petit air fier sur les chiffres", tag='PS', color='#e75480', name='Pivoine la Persane', voice='fr-FR-DeniseNeural', cat='fluffy cream Persian', col='rose pink', trim='lavender', catch="Et moi, je vais compter mes pelotes de laine.", rate='+2%', pitch='+10Hz', tags='#partisocialiste #ps'),
    'eelv': dict(gvoice='Enceladus', gstyle="reporter rêveur et doux, voix calme et légèrement soufflée, un peu dans la lune mais clair", tag='LES ÉCOLOGISTES', color='#3aaa35', name="Flocon l'Angora", voice='fr-FR-RemyMultilingualNeural', cat='fluffy white Turkish Angora', col='jade green', trim='lemon yellow', catch="Et moi, je retourne arroser l'herbe à chat.", rate='-4%', pitch='+6Hz', tags='#lesecologistes #ecologie'),
    'lr':   dict(gvoice='Alnilam', gstyle="reporter bougon, voix grave et ferme, ton ronchon et pince-sans-rire, phrases sèches", tag='LR', color='#0066cc', name='Bjorn le Norvégien', voice='fr-FR-VivienneMultilingualNeural', cat='fluffy gray-brown Norwegian Forest', col='royal blue', trim='white', catch="Et moi, je retourne réviser ma leçon de ronronnement.", rate='-2%', pitch='-12Hz', tags='#lr #lesrepublicains'),
}
ANCHOR_VOICE = ('Charon', "présentateur de journal télévisé, voix posée, chaleureuse et claire, rythme dynamique")
STYLE = ('Photorealistic cinematic action shot, realistic fluffy kitten with real fur texture, bright natural daylight, '
         'rich colors, motion blur on the background, dynamic camera angle, shallow depth of field, vertical shot. '
         'No text, no letters, no writing, no logos, no humans, no people in the background. ')

def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def main(cfg_path):
    cfg = json.load(open(cfg_path))
    p = PARTIES[cfg['party']]
    day = cfg['date']; out_dir = os.path.join(D, 'daily', day); os.makedirs(out_dir, exist_ok=True)
    slot = cfg.get('slot', 'midi')                     # matin (7h30), midi (12h30), soir (18h30), bonus (20h30) ; apm (15h30) ancien
    tag = f'{day}_{slot}_{cfg["party"]}'
    img_name = f'daily_{tag}'
    img_path = os.path.join(D, 'img', img_name + '.png')
    # 1. Image
    if not os.path.exists(img_path):
        if cfg.get('action'):   # style « action réaliste » (14 octobre) : le chaton fait quelque chose lié au sujet
            prompt = (STYLE + f"A realistic {p['cat']} kitten wearing a {p['col']} retro helmet (its signature), "
                      + (f"with {cfg['accessory']}, " if cfg.get('accessory') else '')
                      + f"{cfg['action']}. Setting: {cfg['bg']}.")
        else:
            prompt = (STYLE + f"A realistic {p['cat']} kitten field reporter wearing a {p['col']} retro helmet, holding a tiny vintage silver microphone, "
                      f"talking to the camera. " + (f"Accessory: {cfg['accessory']}. " if cfg.get('accessory') else '') + f"Setting: {cfg['bg']}.")
        gen_img.gen(img_name, prompt, size='2K', ratio='9:16')
    log('image prête')
    # 2. Animation Agnes (délai max, sinon image avec zoom)
    clip = os.path.join(D, 'clips', f'daily_{tag}.mp4')
    deadline = time.time() + float(cfg.get('video_minutes', 100)) * 60
    if not os.path.exists(clip):
        frame = vid.data_uri(img_name)
        prompt = ((f"The kitten keeps doing the action with fast, realistic movement: {cfg['action']}. Dynamic camera tracking, motion blur." if cfg.get('action') else
                   "The kitten reporter talks into the vintage microphone, mouth moving as if speaking, blinking, nodding, small expressive gestures with its free paw, subtle slow camera push-in.") + wan.motion(cfg.get('bg', '')) + " Keep exactly the same character, outfit, lighting and background. 3D animated film style.")
        vid_id = None
        while time.time() < deadline and not vid_id:
            code, r = vid.create(prompt, frame, int(cfg.get('clip_seconds', 10)))
            if code == 200 and (r.get('video_id') or r.get('id')):
                vid_id = r.get('video_id') or r.get('id'); log('animation acceptée', vid_id)
            else:
                log('Agnes indisponible', code); time.sleep(60 if code == 429 else 30)
        while vid_id and time.time() < deadline + 25 * 60:
            time.sleep(10)
            code, r = vid.status(vid_id)
            st = str(r.get('status', '')).lower() if isinstance(r, dict) else ''
            if st == 'completed' and r.get('url'):
                urllib.request.urlretrieve(r['url'], clip); log('animation reçue'); break
            if st == 'failed':
                log('animation refusée', r.get('error')); break
    if not os.path.exists(clip) and os.path.exists(os.path.join(D, '.hf_key')):   # Agnes n'a rien donné : secours gratuit
        for essai in range(6):                      # Hugging Face est capricieux : plusieurs essais espacés (15 octobre)
            try:
                wan.animate(img_name, clip, prompt); log('animation reçue (secours Hugging Face)'); break
            except Exception as e:
                log('secours Hugging Face indisponible, essai', essai + 1, str(e)[:80]); time.sleep(90)
    # 2 bis. Plan B sans animation : 3 plans de plus (gros plan, plan large, détail) pour un montage vivant
    shots = [img_name]
    if not os.path.exists(clip):
        perso = (f"an adorable {p['cat']} kitten field reporter wearing a {p['col']} retro motorcycle helmet with the visor up, "
                 f"a {p['col']} kung-fu robe with a {p['trim']} belt, holding a tiny vintage silver microphone"
                 + (f", with {cfg['accessory']}" if cfg.get('accessory') else ''))
        plans = [('gros', f"Close-up portrait of {perso}, expressive face, mouth open as if speaking, background softly blurred: {cfg['bg']}."),
                 ('large', f"Wide establishing shot of {cfg['bg']}, with {perso} small in the scene walking toward the camera."),
                 ('detail', f"Low-angle dynamic shot of {perso}, gesturing with its free paw, slightly tilted camera, background: {cfg['bg']}.")]
        for suf, pr in plans:
            nm = f'{img_name}_{suf}'
            try:
                if not os.path.exists(os.path.join(D, 'img', nm + '.png')): gen_img.gen(nm, STYLE + pr, size='2K', ratio='9:16')
                shots.append(nm)
            except BaseException as e:
                log('plan', suf, 'indisponible', str(e)[:80])
        log('plan B :', len(shots), 'plans')
    # 3. Montage (réutilise l'habillage des vidéos courtes)
    # numéro d'épisode : prévu dans episodes.json pour les dates déjà planifiées, sinon le suivant
    ep_path = os.path.join(D, 'episodes.json'); eps = json.load(open(ep_path))
    episode = None
    if slot != 'bonus':                                 # les bonus n'ont pas de numéro d'épisode
        eps.setdefault(slot, {}); episode = eps[slot].get(day)
        if episode is None:
            episode = eps['dernier'] + 1; eps[slot][day] = episode; eps['dernier'] = episode
            json.dump(eps, open(ep_path, 'w'), ensure_ascii=False, indent=1)
    sc = dict(kind='party', shots=shots, episode=episode, voice=p['voice'], color=p['color'], tag=p['tag'],
              who=f"{p['name']} · Source : {cfg['source']}", text=' '.join(x for x in (cfg['text'].rstrip(), cfg.get('reaction', p['catch']), cfg.get('question', 'Et toi, tu en penses quoi ?')) if x),  # infos, gag du chaton, question ouverte
              rate=p['rate'], pitch=p['pitch'], gvoice=p['gvoice'], gstyle=p['gstyle'])
    m.SCENES.append(sc); i = len(m.SCENES) - 1
    m.CLIP_NAMES.append(f'daily_{tag}')
    s.HOOKS[i] = (cfg['hook1'], cfg['hook2'])
    s.SLUG[i] = f'JT-chatons-{day}-{slot}-{cfg["party"]}'
    s.OUT = out_dir
    s.render(i, asyncio.new_event_loop())
    with open(os.path.join(out_dir, f'description-{slot}.txt'), 'w') as f:
        f.write(cfg['description'].strip() + '\n')
    log('TERMINÉ', out_dir, 'animé' if os.path.exists(clip) else 'image avec zoom')

if __name__ == '__main__':
    main(sys.argv[1])
