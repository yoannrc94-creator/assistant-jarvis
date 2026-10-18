"""JT multi-sujets : plusieurs scènes animées coordonnées dans une même vidéo (demandé le 15 octobre).

Usage : python3 make_multi.py config.json
config : date, slot, party, source, hook1, hook2, description, question (optionnel), reaction (optionnel),
         segments : [{"text": "...", "bg": "décor en anglais", "action": "action en anglais", "accessory": "..."}, ...]
Chaque segment a son décor et son action ; le même chaton présente tout le JT.
Ordre des animations : Agnes, puis Hugging Face (plusieurs essais), puis image animée en zoom (dernier recours).
Une seule requête de voix pour toute la vidéo (quota Gemini).
"""
import asyncio, json, math, os, re, subprocess, sys, time, urllib.request
from PIL import Image, ImageDraw
import make_daily as md, make_tiktok as m, make_shorts as s, gen_img, vid, wan

D = m.D
W, H, FPS = m.W, m.H, m.FPS
LEAD = s.LEAD

def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

HF_FAILS, HF_PAUSE = 0, 0

def ltx_animate(name, out, prompt):
    """LTX-Video (Space Lightricks) : image -> 4 s de vidéo en 544x960, puis agrandie en 1080x1920."""
    from gradio_client import Client, handle_file
    tmp = os.path.join(D, f'_ltx_{name}.jpg')
    Image.open(os.path.join(D, 'img', name + '.png')).convert('RGB').resize((544, 960)).save(tmp, quality=92)
    c = Client('Lightricks/ltx-video-distilled', token=open(os.path.join(D, '.hf_key')).read().strip(), verbose=False)
    r = c.predict(prompt=prompt, negative_prompt='worst quality, blurry, distorted, text, watermark, humans, people',
                  input_image_filepath=handle_file(tmp), height_ui=960, width_ui=544, mode='image-to-video',
                  duration_ui=4, ui_frames_to_use=41, seed_ui=42, randomize_seed=False, ui_guidance_scale=1, api_name='/image_to_video')
    v = r[0]; p = v['video'] if isinstance(v, dict) else v
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', p, '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-crf', '18', '-an', out])
    return out

def make_scene_clip(name, p, seg, clip_seconds):
    global HF_FAILS, HF_PAUSE
    """Image du segment (même chaton, décor et action propres) puis animation. Renvoie le chemin du clip ou None."""
    img_path = os.path.join(D, 'img', name + '.png')
    if not os.path.exists(img_path):
        subj = seg.get('subject') or f"A realistic {p['cat']} kitten wearing a {p['col']} retro helmet (its signature), "
        prompt = (md.STYLE + subj
                  + (f"with {seg['accessory']}, " if seg.get('accessory') else '')
                  + f"{seg['action']}. Setting: {seg['bg']}.")
        gen_img.gen(name, prompt, size='2K', ratio='9:16')
    clip = os.path.join(D, 'clips', name + '.mp4')
    if os.path.exists(clip): return clip
    anim = (f"The kitten keeps doing the action with fast, realistic movement: {seg['action']}. "
            "Dynamic camera tracking, motion blur." + wan.motion(seg.get('bg', '')))
    # 0. LTX-Video en premier : il répond depuis mon serveur (15 octobre), environ 15 secondes par plan
    for essai in range(2):
        try:
            ltx_animate(name, clip, anim); log('LTX OK', name); return clip
        except Exception as e:
            log('LTX essai', essai + 1, str(e)[:60]); time.sleep(10)
    # 1. Agnes (file souvent pleine : on n'attend pas longtemps)
    t0 = time.time(); vid_id = None
    while os.environ.get('USE_AGNES') and time.time() - t0 < 240 and not vid_id:
        code, r = vid.create(anim, vid.data_uri(name), clip_seconds)
        if code == 200 and (r.get('video_id') or r.get('id')): vid_id = r.get('video_id') or r.get('id')
        else: time.sleep(30)
    while vid_id and time.time() - t0 < 900:  # attente Agnes
        time.sleep(10)
        try: code, r = vid.status(vid_id)
        except Exception: continue
        st = str(r.get('status', '')).lower() if isinstance(r, dict) else ''
        if st == 'completed' and r.get('url'):
            urllib.request.urlretrieve(r['url'], clip); log('Agnes OK', name); return clip
        if st == 'failed': break
    # 2. Hugging Face : 2 essais par plan ; après 3 plans ratés de suite, pause de 20 minutes (le service est en panne)
    if time.time() >= HF_PAUSE:
        for essai in range(2):
            try:
                wan.animate(name, clip, anim, seconds=3.5); HF_FAILS = 0; log('Hugging Face OK', name); return clip
            except Exception as e:
                log('Hugging Face essai', essai + 1, str(e)[:60]); time.sleep(20)
        HF_FAILS += 1
        if HF_FAILS >= 3: HF_PAUSE = time.time() + 1200; HF_FAILS = 0; log('Hugging Face en pause 20 minutes')
    log('pas d animation pour', name, '-> image en zoom')
    return None

def recale(vpath, words, seg_tokens):
    """Recale le début de chaque phrase sur la vraie pause de la voix : les temps de mots de Gemini peuvent glisser de plusieurs dixièmes de seconde."""
    err = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', vpath, '-af', 'silencedetect=noise=-40dB:d=0.12', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    ev = [float(x) for _, x in re.findall(r'silence_(start|end): ([0-9.]+)', err)]
    sil = []
    for a, b in zip(ev[0::2], ev[1::2]):
        if sil and a - sil[-1][1] < 0.02: sil[-1][1] = b          # une pause coupée par un petit bruit reste une seule pause
        else: sil.append([a, b])
    cands = [(a, b) for a, b in sil if b - a >= 0.25 and a > 0.05]  # pauses de fin de phrase (pas le blanc du début)
    out, pos, shift = [], 0, 0.0
    for k, n in enumerate(seg_tokens):
        if k:
            g = words[pos][0]
            near = [c for c in cands if abs(c[0] - g) <= 0.9]
            shift = (max(near, key=lambda c: c[1] - c[0])[1] - g) if near else 0.0
            log(f'phrase {k + 1} : recalée de {shift:+.2f} s')
        out += [(a + shift, b + shift, w) for a, b, w in words[pos:pos + n]]
        pos += n
    return out

def _rgba(h, a=235):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)

def _syllabes(texte):
    """Nombre approximatif de syllabes d'une phrase française : sert seulement à répartir la voix entre les plans."""
    n = 0
    for w in re.split(r"[\s\-'’]+", texte.lower()):        # « lisez-le », « l'abattement » : chaque partie compte
        mot = w.strip(".,;:!?…»«\"")
        if not mot: continue
        if any(c.isdigit() for c in mot):
            n += max(1, round(1.5 * sum(c.isdigit() for c in mot))) + (2 if ',' in mot else 0)
            continue
        if mot == '%': n += 2; continue
        g = len(re.findall(r"[aeiouyàâäéèêëîïôöùûüœæ]+", mot))
        if g > 1 and re.search(r"(e|es|ent)$", mot) and not mot.endswith(('ée', 'ées')): g -= 1
        n += max(1, g)
    return max(1, n)

def _silences(path, noise='-45dB', d=0.06):
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).decode().strip())
    err = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', f'silencedetect=noise={noise}:d={d}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    ev = [float(x) for _, x in re.findall(r'silence_(start|end): ([0-9.]+)', err)]
    fins = ev[1::2] + ([dur] if len(ev) % 2 else [])
    sil = []
    for a, b in zip(ev[0::2], fins):
        if sil and a - sil[-1][1] < 0.03: sil[-1][1] = b      # une pause coupée par un petit bruit reste une seule pause
        else: sil.append([a, b])
    return dur, [(a, b) for a, b in sil if a > 0.02 and b < dur - 0.02]

def aligner_voix(brut, textes, sortie, cap=0.25, lam=1.0, noise='-45dB'):   # lam 1,0 : retrouve les calages validés du 16 octobre
    """Voix d'un seul tenant (Google) : silences du début et de la fin retirés, début exact de chaque plan, longs silences
    ramenés à cap secondes. Les frontières sont choisies parmi les vraies pauses, au plus près d'un débit régulier par syllabe
    (méthode validée sur les JT du 16 octobre). Renvoie (débuts des plans, durée, syllabes)."""
    import wave
    from array import array
    rog = sortie + '.rogne.wav'
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', brut, '-af',
        'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,'
        'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse', '-ar', '48000', '-ac', '1', rog])
    syl = [_syllabes(t) for t in textes]
    dur, gaps = _silences(rog, noise=noise)
    N = len(textes)
    choisis = []
    if N > 1:
        r = (dur - sum(b - a for a, b in gaps)) / sum(syl)
        cands = [(b, b - a, i) for i, (a, b) in enumerate(gaps)]
        M, INF = len(cands), 1e18
        if M < N - 1: raise RuntimeError(f'{M} pauses seulement pour {N} plans')
        dp = [[INF] * M for _ in range(N)]; back = [[-1] * M for _ in range(N)]
        for j, (t, g, _) in enumerate(cands): dp[1][j] = (t - r * syl[0]) ** 2 - lam * g
        for k in range(2, N):
            for j, (t, g, _) in enumerate(cands):
                best, arg = INF, -1
                for i in range(j):
                    if dp[k - 1][i] >= INF: continue
                    c = dp[k - 1][i] + (t - cands[i][0] - r * syl[k - 1]) ** 2
                    if c < best: best, arg = c, i
                if arg >= 0: dp[k][j] = best - lam * g; back[k][j] = arg
        best, arg = INF, -1
        for j, (t, g, _) in enumerate(cands):
            if dp[N - 1][j] >= INF: continue
            c = dp[N - 1][j] + (dur - t - r * syl[N - 1]) ** 2
            if c < best: best, arg = c, j
        if arg < 0: raise RuntimeError('calage impossible')
        j = arg
        for k in range(N - 1, 0, -1): choisis.append(cands[j][2]); j = back[k][j]
        choisis.reverse()
    w = wave.open(rog); sr = w.getframerate(); x = array('h'); x.frombytes(w.readframes(w.getnframes())); w.close()
    bornes = [0.0] + [b for _, b in gaps]; fins = [a for a, _ in gaps] + [dur]
    debut_seg, buf, n = [], array('h'), 0
    for j in range(len(bornes)):
        debut_seg.append(n / sr); seg = x[int(bornes[j] * sr):int(fins[j] * sr)]; buf.extend(seg); n += len(seg)
        if j < len(gaps):
            z = int(min(gaps[j][1] - gaps[j][0], cap) * sr); buf.extend(array('h', [0]) * z); n += z
    w = wave.open(sortie, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(buf.tobytes()); w.close()
    os.remove(rog)
    ons = [0.0] + [debut_seg[g + 1] for g in choisis]
    return ons, n / sr, syl, [0.0] + [gaps[g][1] for g in choisis]

ELEVEN_VOICE = 'aQROLel5sQbj1vuIVi6B'     # voix clonée de l'utilisateur (secours de la voix Google uniquement)

def eleven_say(texte, out):
    """Secours : voix ElevenLabs de l'utilisateur, écrite en WAV 24 kHz. Clé dans ELEVENLABS_API_KEY ou demo/.elevenlabs_key."""
    import wave, urllib.request
    clé = os.environ.get('ELEVENLABS_API_KEY') or open(os.path.join(D, '.elevenlabs_key')).read().strip()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}?output_format=pcm_24000',
        data=json.dumps({'text': texte, 'model_id': 'eleven_multilingual_v2'}).encode(),
        headers={'xi-api-key': clé, 'Content-Type': 'application/json'})
    pcm = urllib.request.urlopen(req, timeout=120).read()
    if len(pcm) < 24000 * 2 * 0.3 * len(texte.split()): raise RuntimeError('audio ElevenLabs trop court')   # moins de 0,3 s par mot : échec
    w = wave.open(out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm); w.close()
    return out

def speech_span(path):
    """Début et fin de la parole dans un fichier audio : les silences au début et à la fin sont retirés."""
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).decode().strip())
    err = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'silencedetect=noise=-40dB:d=0.05', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    ev = [float(x) for _, x in re.findall(r'silence_(start|end): ([0-9.]+)', err)]
    lead = ev[1] if len(ev) >= 2 and ev[0] < 0.02 else 0.0
    end = ev[-1] if len(ev) % 2 else dur
    return lead, end

def main(cfg_path):
    cfg = json.load(open(cfg_path))
    p = md.PARTIES.get(cfg['party']) or dict(cat='ginger tabby', col='navy', name='Maître Moustache', voice='fr-FR-HenriNeural',
        gvoice=md.ANCHOR_VOICE[0], gstyle=md.ANCHOR_VOICE[1], tag='LE JT DES CHATONS', color='#e5b93c', rate='+8%', pitch='+0Hz')
    p = dict(p, color=cfg.get('couleur', p['color']))     # chaque JT a sa couleur (pastille, cadre de l'accroche, carte de fin)
    day, slot = cfg['date'], cfg['slot']
    out_dir = cfg.get('dossier_sortie') or os.path.join(D, 'daily', day); os.makedirs(out_dir, exist_ok=True)
    segs = cfg['segments']; clip_seconds = int(cfg.get('clip_seconds', 6))
    v2 = bool(cfg.get('format_v2'))      # règles du 16 octobre : phrase 1 directe, voix dès 0,05 s, carte de fin courte
    lead_v = 0.05 if v2 else LEAD
    if v2:   # le spectateur moyen n'entend que les 8 à 12 premiers mots : la phrase 1 donne le fait, sans introduction
        p1 = segs[0]['text'].strip(); bas = p1.lower().replace('’', "'")
        nmots = len(re.findall(r"[\w’'-]+", re.sub(r'(\d) (?=\d{3}\b)', r'\1', p1)))
        if nmots > 8 or bas.startswith(('bonjour', 'bonsoir', 'salut', "aujourd'hui", 'on parle', 'le jt', 'voici', 'ce matin', 'ce midi', 'ce soir')):
            raise SystemExit(f'phrase 1 refusée (introduction ou plus de 8 mots) : {p1}')
        if re.search(r'\?[\s!»"”]*$', cfg['hook1'].strip()):
            raise SystemExit(f"titre refusé : il doit affirmer le fait, pas poser une question : {cfg['hook1']}")
        for k, sg in enumerate(segs):
            if re.search(r'[:;?!]\s*[^\s?!.…»"”)]', sg['text'].strip()):
                raise SystemExit(f"plan {k + 1} refusé : ponctuation au milieu de la phrase, la voix y ferait une pause : {sg['text']}")
    # 1. Images et animations, un segment après l'autre
    names, clips = [], []
    for k, seg in enumerate(segs):
        name = f"multi_{day}_{slot}_{cfg['party']}_s{k}"
        names.append(name); clips.append(make_scene_clip(name, p, seg, clip_seconds))
    # 2. Une seule voix pour tout le JT
    tail = [x for x in (cfg.get('reaction', ''), cfg.get('question', 'Et toi, tu en penses quoi ?')) if x]
    full = ' '.join([sg['text'].strip() for sg in segs] + tail)
    sc = dict(kind='party', voice=p['voice'], color=p['color'], tag=p['tag'], gvoice=p['gvoice'], gstyle=cfg.get('gstyle', p['gstyle']),
              rate=p['rate'], pitch=p['pitch'], text=full, who=f"{p['name']} · Source : {cfg['source']}")
    loop = asyncio.new_event_loop()
    cale = False                       # True : débuts de plans déjà exacts, pas de recalage approximatif
    mode_google = bool(cfg.get('voix_google')) and not cfg.get('voix_existante') and not os.environ.get('NO_GEMINI')
    if mode_google:                    # une seule voix Google pour tout le JT (quota), puis calage sur les vraies pauses
        textes = [sg['text'].strip() for sg in segs]
        brut, vpath = os.path.join(D, f'tk_gbrut-{day}-{slot}.wav'), os.path.join(D, f'tk_gcale-{day}-{slot}.wav')
        try:
            import gem_tts
            if cfg.get('voix_brute_gardee') and os.path.exists(brut): mdl = 'voix gardée'
            else: _, mdl = gem_tts.say(' '.join(textes), brut, sc['gvoice'], sc['gstyle'])
            for seuil in ('-45dB', '-40dB', '-35dB'):     # plusieurs seuils de pause sur la même voix avant d'en demander une autre
                ons, vdur, syl, _ = aligner_voix(brut, textes, vpath, noise=seuil)
                durees = [(ons + [vdur])[k + 1] - ons[k] for k in range(len(textes))]   # le dernier plan va jusqu'au bout de la voix
                moy = sum(durees) / sum(syl)
                douteux = [k + 1 for k, (dk, sk) in enumerate(zip(durees, syl)) if not 0.5 <= dk / (moy * sk) <= 1.6]
                log('voix Google', mdl, '| seuil', seuil, '| débuts', [round(o, 2) for o in ons], '| durées', [round(x, 2) for x in durees], '| durée', round(vdur, 2), 's')
                if not douteux: break
            ons_e = ons + [vdur - 0.2]; words = []
            for k, t in enumerate(textes):
                toks = t.split(); span = (ons_e[k + 1] - 0.08 - ons[k]) / len(toks)
                words += [(ons[k] + j * span, ons[k] + (j + 0.9) * span, w) for j, w in enumerate(toks)]
            if douteux and not cfg.get('calage_force'):
                raise SystemExit(f'CALAGE DOUTEUX, plans {douteux} : durées {[round(x, 2) for x in durees]} pour {syl} syllabes. '
                                 f'Voix gardée dans {brut}. Relancer (nouvelle voix) ou ajouter "calage_force": true.')
            cale = True
            full = ' '.join(textes)            # la voix Google ne lit que les plans : pas de question ajoutée en queue
        except SystemExit as e:
            if 'CALAGE DOUTEUX' in str(e): raise
            if cfg.get('sans_secours'): raise SystemExit('Google indisponible, secours interdit pour cette vidéo : ' + str(e)[:150])
            log('VOIX DE SECOURS : voix Google indisponible :', str(e)[:150]); mode_google = False
        except Exception as e:
            if cfg.get('sans_secours'): raise SystemExit('Google indisponible, secours interdit pour cette vidéo : ' + str(e)[:150])
            log('VOIX DE SECOURS : voix Google indisponible ou calage impossible :', str(e)[:150]); mode_google = False
    if mode_google:
        pass
    elif cfg.get('par_plan') or (cfg.get('voix_google') and not cfg.get('voix_existante')):
        # une voix par plan, mises bout à bout avec une courte pause : chaque plan démarre sur sa propre voix
        secours = bool(cfg.get('voix_google')) and not cfg.get('par_plan')   # repli de voix_google : ElevenLabs directement, sans réessayer Google
        full = ' '.join(sg['text'].strip() for sg in segs)                   # seuls les plans sont lus
        pad = float(cfg.get('pad', 0.3)); parts, ons, words, pos = [], [], [], 0.0
        for k, sg in enumerate(segs):
            pk = os.path.join(D, f'tk_voice{9100 + k}.wav')
            if os.path.exists(pk): os.remove(pk)            # jamais une voix d'un autre passage
            if secours:                  # repli de la voix Google : voix ElevenLabs de l'utilisateur ; NVIDIA seulement sans clé
                pk = os.path.join(D, f'tk_voice{9100 + k}.wav')
                try: eleven_say(sg['text'].strip(), pk); log('secours ElevenLabs, plan', k + 1)
                except Exception as e:
                    log('secours ElevenLabs indisponible, NVIDIA :', str(e)[:120])
                    pk, _, _ = loop.run_until_complete(m.tts(9100 + k, dict(sc, text=sg['text'].strip(), gvoice=None)))
            else:
                pk, _, _ = loop.run_until_complete(m.tts(9100 + k, dict(sc, text=sg['text'].strip())))
            lead, end = speech_span(pk); d = end - lead
            toks = sg['text'].split(); span = d / len(toks)
            ons.append(pos); parts.append((pk, lead, end))
            words += [(pos + j * span, pos + (j + 0.9) * span, w) for j, w in enumerate(toks)]
            pos += d + pad
        vdur = pos - pad; vpath = os.path.join(D, f"tk_{'gsecours' if secours else 'par'}-{day}-{slot}.wav")
        fc = ';'.join(f'[{k}:a]atrim=start={l:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,aresample=48000,adelay={int(ons[k] * 1000)}:all=1[p{k}]'
                      for k, (_, l, e) in enumerate(parts))
        fc += ';' + ''.join(f'[p{k}]' for k in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0:duration=longest[vv]'
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *sum([['-i', p] for p, _, _ in parts], []), '-filter_complex', fc, '-map', '[vv]', vpath])
        log('voix par plan', [round(o, 2) for o in ons], 'durée', round(vdur, 2), 's')
        cale = True
    elif cfg.get('voix_existante'):      # montage refait sur une voix déjà générée, débuts de phrases mesurés sur l'audio (sans appel vocal)
        vpath = cfg['voix_existante']
        vdur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vpath]).decode().strip())
        ons = list(cfg['debuts']) + [vdur - 0.2]
        words = []
        for k, sg in enumerate(segs):
            toks = sg['text'].split(); span = (ons[k + 1] - 0.08 - ons[k]) / len(toks)
            words += [(ons[k] + j * span, ons[k] + (j + 0.9) * span, w) for j, w in enumerate(toks)]
        log('voix existante', vpath, round(vdur, 2), 's')
        cale = True
    else:
        vpath, vdur, words = loop.run_until_complete(m.tts(900, sc))
    if fin_v2 := (v2 and cfg.get('fin', True)):
        # carte de fin courte qui annonce le prochain JT ; voix Google, sinon la signature d'origine (jamais NVIDIA, qui lit « jeu »)
        import hashlib, wave
        def _google_ok(f):
            try:
                with wave.open(f) as w: return w.getframerate() == 24000 and w.getnframes() / 24000 >= 0.25 * len(cfg['fin_voix'].split())
            except Exception: return False
        nom = 'gem_fin_' + hashlib.sha1((cfg['fin_voix'] + sc['gvoice'] + sc['gstyle']).encode()).hexdigest()[:10] + '.wav'
        cache = os.path.join(D, nom)
        if not _google_ok(cache) and not os.environ.get('NO_GEMINI'):
            tmp = cache + '.tmp.wav'
            try:
                import gem_tts; gem_tts.say(cfg['fin_voix'], tmp, sc['gvoice'], sc['gstyle'], tries=2)
                if _google_ok(tmp): os.replace(tmp, cache)
            except (Exception, SystemExit) as e:
                log('fin : voix Google indisponible, signature d origine :', str(e)[:100])
            if os.path.exists(tmp): os.remove(tmp)
        if _google_ok(cache):
            cfg['fin_cache'] = nom
        else:
            cfg['fin_cache'] = 'gem_signature.wav'; cfg['fin_sous_titre'] = 'Un nouveau JT des chatons chaque jour'
            log('fin : signature d origine utilisée (plus longue, vérifier les 25 secondes)')
    epath, edur, _ = loop.run_until_complete(s.tts_end(cfg.get('fin_voix'), cfg.get('fin_cache', 'gem_signature.wav')))
    # 3. Début de chaque segment dans la voix : mots exacts si le compte tombe juste, sinon proportionnel aux lettres
    seg_tokens = [len(sg['text'].split()) for sg in segs]
    total_tail = len(full.split()) - sum(seg_tokens)
    if len(words) == len(full.split()):
        if not cale: words = recale(vpath, words, seg_tokens)
        starts, idx = [], 0
        for n in seg_tokens: starts.append(words[idx][0] + lead_v if idx else 0.0); idx += n
    else:
        lens = [len(sg['text']) + 1 for sg in segs]; acc, starts = 0, []
        for n in lens: starts.append(vdur * acc / sum(lens + [1]) if acc else 0.0); acc += n
    body = lead_v + vdur + 0.5
    fin = cfg.get('fin', True)                 # False : pas de carte de fin ni de signature (vidéo sans générique)
    total = body + ((max(1.8, edur + 0.5) if v2 else max(s.END_DUR, edur + 0.6)) if fin else 0.5)   # v2 : carte réduite à sa phrase
    if v2 and total > 25: log('ATTENTION durée', round(total, 2), 's : plus de 25 secondes')
    # 4. Audio : jingle, voix, signature (même montage que les vidéos courtes)
    jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
    wav = os.path.join(out_dir, '_multi.wav')
    mus = os.path.join(D, 'music', 'happy-days.mp3')           # FSM Team, CC BY 4.0 (crédit dans la description)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', jg, '-i', vpath, '-i', epath, '-stream_loop', '-1', '-i', mus, '-filter_complex',
        f'[0:a]aresample=48000,volume={0.6 if fin else 0},adelay={int(body*1000)}:all=1[j];'
        f'[1:a]aresample=48000,adelay={int(lead_v*1000)}:all=1[v];'
        f'[2:a]aresample=48000,volume={1 if fin else 0},adelay={int((body+0.2)*1000)}:all=1[e];'
        f'[v][e]amix=inputs=2:normalize=0,asplit=2[ve1][ve2];'
        f'[3:a]aresample=48000,atrim=0:{total},volume=0.3[mus];'
        f'[mus][ve1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=350[musd];'
        f'[j][ve2][musd]amix=inputs=3:normalize=0,apad,atrim=0:{total}[o]',
        '-map', '[o]', wav])
    groups = m.chunks([(a + lead_v, b + lead_v, w) for a, b, w in m.attach_punct(words, full)])
    def _ts(x): h, r = divmod(int(round(x * 1000)), 3600000); mi, r = divmod(r, 60000); se, ms = divmod(r, 1000); return f'{h:02}:{mi:02}:{se:02},{ms:03}'
    bounds_s = starts + [body]
    with open(os.path.join(out_dir, f'sous-titres-{slot}.srt'), 'w', encoding='utf-8') as f:
        for k, sg in enumerate(segs):
            f.write(f"{k + 1}\n{_ts(bounds_s[k])} --> {_ts(max(bounds_s[k] + 0.5, bounds_s[k + 1] - 0.05))}\n{sg['text']}\n\n")
    # 5. Images : une par segment, avec un coup de zoom et une caméra qui tremble légèrement à chaque coupe
    s.HOOKS[900] = (cfg['hook1'], cfg.get('hook2', ''))
    s.SLUG[900] = f"JT-chatons-{day}-{slot}-{cfg['party']}"; s.OUT = out_dir
    out = os.path.join(out_dir, s.SLUG[900] + '.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    bounds = starts[1:] + [body]
    readers, cur, last = {}, -1, None
    for fi in range(int(total * FPS)):
        t = fi / FPS
        if t < body:
            k = max(i for i, st in enumerate(starts) if st <= t)
            if k != cur:
                if cur in readers and readers[cur] is not None: readers[cur].p.kill()
                cur = k
                if clips[k]: readers[k] = m.ClipReader(clips[k])
                else: readers[k] = None
                seg_t0 = starts[k]
            if readers.get(k) is not None:
                im = readers[k].next()
            else:
                q = min(1.0, (t - seg_t0) / max(0.1, bounds[k] - seg_t0))
                im = m.kenburns(names[k], q, 'in' if k % 2 == 0 else 'out')
            since = t - seg_t0
            if since < 0.25 and k > 0:       # coup de zoom à chaque changement de scène
                z = 1 + 0.07 * (1 - since / 0.25); cw, ch = W / z, H / z
                im = im.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR)
            dx, dy = int(9 * math.sin(t * 2.3) + 4 * math.sin(t * 5.1)), int(7 * math.cos(t * 1.9) + 3 * math.sin(t * 4.3))
            im = im.crop((14 + dx, 14 + dy, W - 14 + dx, H - 14 + dy)).resize((W, H), Image.BILINEAR)
            if t < 0.5:
                z = 1 + 0.12 * (1 - t / 0.5) ** 2; cw, ch = W / z, H / z
                im = im.crop((int((W - cw) / 2), int((H - ch) * 0.4), int((W + cw) / 2), int((H - ch) * 0.4 + ch))).resize((W, H), Image.BILINEAR)
            last = im
            d = ImageDraw.Draw(im)
            m.badge(d, sc)
            if t > s.HOOK_SECONDS: m.caption(d, groups, t)
            s.hook(d, sc, 900, t)
        else:
            if v2 and fin:                   # sous la carte, le plan 1 repart : quand TikTok relance la vidéo, elle s'enchaîne
                if 'fin' not in readers:
                    if readers.get(cur) is not None: readers[cur].p.kill()
                    readers['fin'] = m.ClipReader(clips[0]) if clips[0] else None
                im = readers['fin'].next() if readers['fin'] else m.kenburns(names[0], min(1.0, (t - body) / 2.0), 'in')
            else:
                im = last.copy() if last is not None else Image.new('RGB', (W, H))
            if fin: s.end_card(im, (t - body) / s.END_DUR, cfg.get('fin_sous_titre', 'Un nouveau JT des chatons chaque jour'), _rgba(cfg.get('couleur', '#e5b93c')))
            if v2: m.badge(ImageDraw.Draw(im), sc)
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    for rd in readers.values():
        if rd is not None: rd.p.kill()
    if cfg.get('description'):
      with open(os.path.join(out_dir, f'description-{slot}.txt'), 'w') as f:
        f.write(cfg['description'].strip() + '\nMusique : FSM Team, free-stock-music.com (licence CC BY 4.0)\n')
    log('TERMINÉ', out, round(total, 1), 's', [('animé' if c else 'zoom') for c in clips])

if __name__ == '__main__':
    main(sys.argv[1])
