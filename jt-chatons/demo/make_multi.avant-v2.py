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
    out_dir = os.path.join(D, 'daily', day); os.makedirs(out_dir, exist_ok=True)
    segs = cfg['segments']; clip_seconds = int(cfg.get('clip_seconds', 6))
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
    if cfg.get('par_plan'):           # une voix par plan, mises bout à bout avec une courte pause : chaque plan démarre sur sa propre voix
        pad = float(cfg.get('pad', 0.3)); parts, ons, words, pos = [], [], [], 0.0
        for k, sg in enumerate(segs):
            pk = os.path.join(D, f'tk_voice{9100 + k}.wav')
            if os.path.exists(pk): os.remove(pk)            # jamais une voix d'un autre passage
            pk, _, _ = loop.run_until_complete(m.tts(9100 + k, dict(sc, text=sg['text'].strip())))
            lead, end = speech_span(pk); d = end - lead
            toks = sg['text'].split(); span = d / len(toks)
            ons.append(pos); parts.append((pk, lead, end))
            words += [(pos + j * span, pos + (j + 0.9) * span, w) for j, w in enumerate(toks)]
            pos += d + pad
        vdur = pos - pad; vpath = os.path.join(D, f'tk_par-{day}-{slot}.wav')
        fc = ';'.join(f'[{k}:a]atrim=start={l:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,aresample=48000,adelay={int(ons[k] * 1000)}:all=1[p{k}]'
                      for k, (_, l, e) in enumerate(parts))
        fc += ';' + ''.join(f'[p{k}]' for k in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0:duration=longest[vv]'
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *sum([['-i', p] for p, _, _ in parts], []), '-filter_complex', fc, '-map', '[vv]', vpath])
        log('voix par plan', [round(o, 2) for o in ons], 'durée', round(vdur, 2), 's')
    elif cfg.get('voix_existante'):      # montage refait sur une voix déjà générée, débuts de phrases mesurés sur l'audio (sans appel vocal)
        vpath = cfg['voix_existante']
        vdur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vpath]).decode().strip())
        ons = list(cfg['debuts']) + [vdur - 0.2]
        words = []
        for k, sg in enumerate(segs):
            toks = sg['text'].split(); span = (ons[k + 1] - 0.08 - ons[k]) / len(toks)
            words += [(ons[k] + j * span, ons[k] + (j + 0.9) * span, w) for j, w in enumerate(toks)]
        log('voix existante', vpath, round(vdur, 2), 's')
    else:
        vpath, vdur, words = loop.run_until_complete(m.tts(900, sc))
    epath, edur, _ = loop.run_until_complete(s.tts_end(cfg.get('fin_voix'), cfg.get('fin_cache', 'gem_signature.wav')))
    # 3. Début de chaque segment dans la voix : mots exacts si le compte tombe juste, sinon proportionnel aux lettres
    seg_tokens = [len(sg['text'].split()) for sg in segs]
    total_tail = len(full.split()) - sum(seg_tokens)
    if len(words) == len(full.split()):
        if not (cfg.get('voix_existante') or cfg.get('par_plan')): words = recale(vpath, words, seg_tokens)
        starts, idx = [], 0
        for n in seg_tokens: starts.append(words[idx][0] + LEAD if idx else 0.0); idx += n
    else:
        lens = [len(sg['text']) + 1 for sg in segs]; acc, starts = 0, []
        for n in lens: starts.append(vdur * acc / sum(lens + [1]) if acc else 0.0); acc += n
    body = LEAD + vdur + 0.5
    fin = cfg.get('fin', True)                 # False : pas de carte de fin ni de signature (vidéo sans générique)
    total = body + (max(s.END_DUR, edur + 0.6) if fin else 0.5)
    # 4. Audio : jingle, voix, signature (même montage que les vidéos courtes)
    jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
    wav = os.path.join(out_dir, '_multi.wav')
    mus = os.path.join(D, 'music', 'happy-days.mp3')           # FSM Team, CC BY 4.0 (crédit dans la description)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', jg, '-i', vpath, '-i', epath, '-stream_loop', '-1', '-i', mus, '-filter_complex',
        f'[0:a]aresample=48000,volume={0.6 if fin else 0},adelay={int(body*1000)}:all=1[j];'
        f'[1:a]aresample=48000,adelay={int(LEAD*1000)}:all=1[v];'
        f'[2:a]aresample=48000,volume={1 if fin else 0},adelay={int((body+0.2)*1000)}:all=1[e];'
        f'[v][e]amix=inputs=2:normalize=0,asplit=2[ve1][ve2];'
        f'[3:a]aresample=48000,atrim=0:{total},volume=0.3[mus];'
        f'[mus][ve1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=350[musd];'
        f'[j][ve2][musd]amix=inputs=3:normalize=0,apad,atrim=0:{total}[o]',
        '-map', '[o]', wav])
    groups = m.chunks([(a + LEAD, b + LEAD, w) for a, b, w in m.attach_punct(words, full)])
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
            im = last.copy() if last is not None else Image.new('RGB', (W, H))
            if fin: s.end_card(im, (t - body) / s.END_DUR, cfg.get('fin_sous_titre', 'Un nouveau JT des chatons chaque jour'), _rgba(cfg.get('couleur', '#e5b93c')))
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    with open(os.path.join(out_dir, f'description-{slot}.txt'), 'w') as f:
        f.write(cfg['description'].strip() + '\nMusique : FSM Team, free-stock-music.com (licence CC BY 4.0)\n')
    log('TERMINÉ', out, round(total, 1), 's', [('animé' if c else 'zoom') for c in clips])

if __name__ == '__main__':
    main(sys.argv[1])
