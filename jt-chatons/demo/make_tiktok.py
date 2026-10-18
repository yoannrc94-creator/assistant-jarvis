"""JT des chatons, format vertical 1080x1920 : images Agnes (style 3D), voix neuronales, sous-titres mot à mot."""
import asyncio, json, math, os, ssl, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import edge_tts, edge_tts.communicate as _c

_c._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')  # proxy de la machine

D = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(D, 'img')
W, H, FPS = 1080, 1920, 30
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
F = lambda s: ImageFont.truetype(FB, s)

SCENES = [
    dict(kind='anchor', shots=['v_anchor'], voice='fr-FR-HenriNeural', color='#e5b93c', tag='JT DES CHATONS', who='Maître Moustache',
         text="Bonsoir, et bienvenue dans le JT des chatons ! Ce soir, nos six reporters font le tour des partis politiques."),
    dict(shots=['v_lfi_a', 'v_lfi_b'], voice='fr-FR-DeniseNeural', color='#cc2444', tag='LFI', who='Pacha le Siamois · Source : LCP',
         text="Ici Pacha, en direct. La France insoumise prépare sa niche parlementaire du 29 octobre. Selon LCP, ses textes porteront notamment sur les salaires, les pesticides et les AESH."),
    dict(shots=['v_rn_a', 'v_rn_b'], voice='fr-FR-RemyMultilingualNeural', color='#1b3a75', tag='RN', who='Gaspard le Chartreux · Source : site du RN',
         text="Ici Gaspard. Au Rassemblement national, l'équipe de campagne de Marine Le Pen accueille de nouveaux membres. Le parti a annoncé ces nominations sur son site."),
    dict(shots=['v_ren_a', 'v_ren_b'], voice='fr-FR-VivienneMultilingualNeural', color='#ff8a00', tag='RENAISSANCE', who='Mandarine la Maine Coon · Sources : BFM, France 3 Régions',
         text="Ici Mandarine. Gabriel Attal, candidat Renaissance, était en meeting à Lyon ce samedi, selon BFM. Il y a présenté son pacte pour la jeunesse, rapporte France 3 Régions."),
    dict(shots=['v_ps_a', 'v_ps_b'], voice='fr-FR-DeniseNeural', color='#e75480', tag='PS', who='Pivoine la Persane · Source : BFM',
         text="Ici Pivoine. La primaire du Parti socialiste et de Place publique se poursuit. Selon BFM, plus de 91 000 votants étaient comptabilisés ce samedi à 14 heures."),
    dict(shots=['v_eelv_a', 'v_eelv_b'], voice='fr-FR-RemyMultilingualNeural', color='#3aaa35', tag='LES ÉCOLOGISTES', who="Flocon l'Angora · Source : franceinfo",
         text="Ici Flocon. Chez Les Écologistes, Sandrine Rousseau appelle à accélérer le processus de désignation pour la présidentielle, rapporte franceinfo."),
    dict(shots=['v_lr_a', 'v_lr_b'], voice='fr-FR-VivienneMultilingualNeural', color='#0066cc', tag='LR', who='Bjorn le Norvégien · Source : Ouest-France',
         text="Ici Bjorn. Pour Bruno Retailleau, candidat à la présidentielle, il faut une refonte complète du système éducatif. Il l'affirme dans un entretien à Ouest-France."),
    dict(kind='anchor', shots=['v_outro'], voice='fr-FR-HenriNeural', color='#e5b93c', tag='JT DES CHATONS', who='Sources : presse du 8 au 10 octobre 2026',
         text="C'est la fin de ce journal. Merci de l'avoir suivi, et à très vite !"),
]

async def tts(i, sc):
    if sc.get('gvoice') and not os.environ.get('NO_GEMINI'):
        try:
            import gem_tts
            wav, dur, words, mdl = gem_tts.say_aligned(sc['text'], os.path.join(D, f'tk_voice{i}.wav'), sc['gvoice'], sc.get('gstyle', ''))
            print('voix Gemini', sc['gvoice'], mdl, flush=True)
            return wav, dur, words
        except BaseException as e:                      # quota épuisé ou panne : on garde l'ancienne voix
            print('voix Gemini indisponible :', str(e)[:120], flush=True)
    try:                                                # secours NVIDIA (14 octobre) : Microsoft refuse désormais la connexion
        import nv_tts
        wav, dur, words, v = nv_tts.say(sc['text'], os.path.join(D, f'tk_voice{i}.wav'), sc.get('voice', ''))
        print('voix NVIDIA', v, flush=True)
        return wav, dur, words
    except BaseException as e:
        print('voix NVIDIA indisponible, ancienne voix :', str(e)[:120], flush=True)
    return await _tts_edge(i, sc)

async def _tts_edge(i, sc, tries=4):
    """Ancienne voix ; recommence si le service renvoie un audio vide (incident passager déjà vu)."""
    for k in range(tries):
        res = await _tts_edge_once(i, sc)
        if res[1] > max(0.8, len(sc['text']) / 40): return res
        print('voix vide, nouvel essai', flush=True); await asyncio.sleep(5 * (k + 1))
    raise RuntimeError('voix indisponible (audio vide)')

async def _tts_edge_once(i, sc):
    path = os.path.join(D, f'tk_voice{i}.mp3')
    words = []
    com = edge_tts.Communicate(sc['text'], sc['voice'], rate=sc.get('rate', '+6%'), pitch=sc.get('pitch', '+0Hz'), boundary='WordBoundary')
    with open(path, 'wb') as f:
        async for ch in com.stream():
            if ch['type'] == 'audio':
                f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                words.append((ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']))
    dur = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', path]))['format']['duration'])
    return path, dur, words

def attach_punct(words, text):
    """Recolle la ponctuation qui suit chaque mot dans le texte d'origine."""
    out, pos = [], 0
    for a, b, w in words:
        i = text.find(w, pos)
        if i < 0: out.append((a, b, w)); continue
        j = i + len(w)
        while j < len(text) and text[j] in ' \u202f\xa0' and j + 1 < len(text) and text[j + 1] in '.,!?;:': j += 1
        k = j
        while k < len(text) and text[k] in '.,!?;:': k += 1
        out.append((a, b, text[i:k].replace(' ', '\u00a0')) if k > j else (a, b, w)); pos = k
    return out

def chunks(words, maxc=20):
    """Regroupe les mots en sous-titres courts (style TikTok), coupés aux fins de phrase."""
    out, cur = [], []
    for w in words:
        if cur and (sum(len(x[2]) + 1 for x in cur) + len(w[2]) > maxc or cur[-1][2][-1:] in '.,!?;:'):
            out.append(cur); cur = []
        cur.append(w)
    if cur: out.append(cur)
    return out

_img_cache = {}
def base(name):
    if name not in _img_cache:
        im = Image.open(os.path.join(IMG, name + '.png')).convert('RGB')
        sw = int(W * 1.16); sh = int(im.height * sw / im.width)
        _img_cache[name] = im.resize((sw, sh), Image.LANCZOS)
    return _img_cache[name]

def kenburns(name, p, mode):
    im = base(name)
    z = 1.0 + 0.14 * p if mode == 'in' else 1.14 - 0.10 * p          # facteur de zoom
    cw, ch = W / z, H / z                                               # l'image fait 1,16 x la largeur finale
    cx, cy = im.width / 2, im.height * 0.47
    x0 = max(0, min(im.width - cw, cx - cw / 2)); y0 = max(0, min(im.height - ch, cy - ch / 2))
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

CLIP_NAMES = ['anchor', 'lfi', 'rn', 'ren', 'ps', 'eelv', 'lr', 'outro']

class ClipReader:
    """Lit un clip animé image par image, recadré en 1080x1920 ; fige la dernière image si le clip est plus court."""
    def __init__(self, path):
        # Version aller-retour du clip (avant puis à l'envers), lue en boucle : le chaton bouge toute la scène.
        pp = os.path.join(D, 'clips_pp', os.path.basename(path))
        if not os.path.exists(pp) or os.path.getmtime(pp) < os.path.getmtime(path):
            os.makedirs(os.path.dirname(pp), exist_ok=True)
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', path, '-filter_complex',
                                   '[0:v]fps=30,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]', '-map', '[v]',
                                   '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', pp])
        vf = f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}'
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-stream_loop', '-1', '-i', pp, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.last = None
    def next(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3: self.last = Image.frombytes('RGB', (W, H), buf)
        return self.last.copy()
    def close(self):
        self.p.kill()

# Zone sûre TikTok : en haut, les onglets couvrent environ 12 % de l'image ; à droite, les boutons couvrent
# environ 20 % de la largeur entre 45 % et 85 % de la hauteur ; en bas, la description couvre les 20 derniers %.
SAFE_TOP = 250

def badge(d, sc):
    f = F(46); tw = d.textlength(sc['tag'], font=f)
    y0 = SAFE_TOP
    d.rounded_rectangle((60, y0, 60 + tw + 150, y0 + 90), radius=45, fill=sc['color'])
    d.ellipse((92, y0 + 30, 122, y0 + 60), fill='#ff3b3b' if sc.get('kind') != 'anchor' else 'white')
    d.text((140, y0 + 45), sc['tag'], font=f, fill='white', anchor='lm')
    if sc.get('episode'):                                       # étiquette de série, constante sur toute la vidéo
        lab = f"JT DES CHATONS · ÉPISODE {sc['episode']}"
        fe = F(36); yl = y0 + 175
        d.rounded_rectangle((60, yl, 60 + d.textlength(lab, font=fe) + 40, yl + 62), radius=31, fill=(0, 0, 0))
        d.text((80, yl + 31), lab, font=fe, fill='#ffe14d', anchor='lm')
    size = 34
    while size > 20 and d.textlength(sc['who'], font=F(size)) > W - 260: size -= 1
    d.text((64, y0 + 130), sc['who'], font=F(size), fill='white', anchor='lm', stroke_width=4, stroke_fill='black')

def caption(d, groups, t):
    cur = None
    for g in groups:
        if g[0][0] - 0.05 <= t <= g[-1][1] + 0.35: cur = g
    if not cur: return
    f = F(84); space = d.textlength(' ', font=f)
    widths = [d.textlength(w[2], font=f) for w in cur]
    lines, line, lw = [], [], 0                                         # retour à la ligne si trop large
    for w, wd in zip(cur, widths):
        if line and lw + space + wd > W - 300: lines.append((line, lw)); line, lw = [], 0
        lw = lw + (space if line else 0) + wd; line.append((w, wd))
    lines.append((line, lw))
    y = 1180 - (len(lines) - 1) * 55                      # au-dessus de la description TikTok
    for line, lw in lines:
        x = (W - 120 - lw) / 2                                  # décalé à gauche des boutons TikTok
        for w, wd in line:
            spoken = w[0] <= t
            d.text((x, y), w[2], font=f, fill='#ffe14d' if spoken and t <= w[1] + 0.15 else 'white', anchor='lm', stroke_width=8, stroke_fill='black')
            x += wd + space
        y += 110

def jingle(path, total):
    """Petit jingle synthétique (3 notes) au début et à la fin."""
    notes = "sine=f=784:d=0.18,afade=out:st=0.1:d=0.08[a];sine=f=988:d=0.18,afade=out:st=0.1:d=0.08[b];sine=f=1175:d=0.5,afade=out:st=0.2:d=0.3[c];[a][b][c]concat=n=3:v=0:a=1,volume=0.35"
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-filter_complex', notes, '-t', '1', path])

def main():
    loop = asyncio.new_event_loop()
    res = [loop.run_until_complete(tts(i, sc)) for i, sc in enumerate(SCENES)]
    LEAD, TAIL = 0.35, 0.55
    durs = [LEAD + d + TAIL for _, d, _ in res]
    durs[0] += 0.9                                                       # place pour le jingle d'ouverture
    total = sum(durs)
    jg = os.path.join(D, 'tk_jingle.wav'); jingle(jg, total)
    inputs, filt, start = [], [], 0.0
    for i, ((p, d, _), dur) in enumerate(zip(res, durs)):
        inputs += ['-i', p]
        off = start + LEAD + (0.9 if i == 0 else 0)
        filt.append(f'[{i}:a]aresample=48000,adelay={int(off*1000)}:all=1[v{i}]')
        start += dur
    n = len(res)
    inputs += ['-i', jg, '-i', jg]
    filt.append(f'[{n}:a]aresample=48000[j0]')
    filt.append(f'[{n+1}:a]aresample=48000,adelay={int((total-1.3)*1000)}:all=1[j1]')
    filt.append(''.join(f'[v{i}]' for i in range(n)) + f'[j0][j1]amix=inputs={n+2}:normalize=0,apad,atrim=0:{total}[out]')
    wav = os.path.join(D, 'tk_audio.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[out]', wav])

    dest = os.path.join(D, os.environ.get('OUT_NAME', 'JT-des-chatons-vertical.mp4'))
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', dest], stdin=subprocess.PIPE)
    for i, (sc, (_, d, words), dur) in enumerate(zip(SCENES, res, durs)):
        off = LEAD + (0.9 if i == 0 else 0)
        groups = chunks([(a + off, b + off, w) for a, b, w in attach_punct(words, sc['text'])])
        nf = int(dur * FPS)
        cp = os.path.join(D, 'clips', CLIP_NAMES[i] + '.mp4')
        reader = ClipReader(cp) if os.path.exists(cp) else None
        reader_len = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', cp]))['format']['duration']) if reader else 0
        print(f'scène {i+1} : ' + ('clip animé' if reader else 'image fixe (pas de clip)'), flush=True)
        for fi in range(nf):
            t = fi / FPS; p = t / dur
            shots = sc['shots']
            if reader:
                im = reader.next()                       # clip animé en aller-retour pendant toute la réplique
            else:
                k = 0 if len(shots) == 1 or p < 0.55 else 1
                sp = p / 0.55 if k == 0 and len(shots) > 1 else (p - 0.55) / 0.45 if len(shots) > 1 else p
                im = kenburns(shots[k], min(1, sp), 'in' if k == 0 else 'out')
            d = ImageDraw.Draw(im)
            badge(d, sc)
            caption(d, groups, t)
            fade = min(1, (t + 1 / FPS) / 0.2, (dur - t) / 0.2)
            if fade < 1: im = Image.blend(Image.new('RGB', (W, H)), im, max(0, fade))
            enc.stdin.write(im.tobytes())
        if reader: reader.close()
        print(f'scène {i+1}/{len(SCENES)}', flush=True)
    enc.stdin.close(); enc.wait()
    print('TERMINÉ', dest, round(total, 1), 's', flush=True)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        sc = SCENES[1]
        groups = chunks([(0.0, 0.5, 'La'), (0.5, 1.0, 'France'), (1.0, 1.5, 'insoumise'), (1.5, 2.0, 'prépare')])
        im = kenburns(sc['shots'][0], 0.3, 'in'); d = ImageDraw.Draw(im); badge(d, sc); caption(d, groups, 0.7)
        im.resize((W // 2, H // 2)).save(os.path.join(D, 'tk_preview.jpg'), quality=85)
    else:
        main()
