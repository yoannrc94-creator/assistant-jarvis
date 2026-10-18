import math
"""Package TikTok : une vidéo courte par parti (accroche + reportage + appel à s'abonner)."""
import asyncio, os, re, subprocess, sys
from PIL import Image, ImageDraw
import make_tiktok as m

D, W, H, FPS = m.D, m.W, m.H, m.FPS
OUT = os.path.join(D, 'package_tiktok')
os.makedirs(OUT, exist_ok=True)

# Accroches affichées dès la première image (2 lignes max, neutres, sans avis).
HOOKS = {
    1: ('Ce que prépare LFI', 'expliqué par un chaton'),
    2: ('Le RN recrute', 'le chaton te dit tout'),
    3: ('Attal dans la Drôme', 'le chaton était là'),
    4: ('Primaire PS : 91 000 votants', 'le chaton a compté'),
    5: ('Les Écolos pressés ?', 'le chaton enquête'),
    6: ('Retailleau veut refaire l’école', 'le chaton t’explique'),
}
SLUG = {1: '1-LFI', 2: '2-RN', 3: '3-Renaissance', 4: '4-PS', 5: '5-Ecologistes', 6: '6-LR'}
END_TEXT = "C'était le JT des Chatons, abonne-toi pour l'épisode de demain !"
END_DUR = 2.6
LEAD = 0.15  # la voix démarre tout de suite, sans blanc

def wrap_center(d, text, font, y, maxw, fill='white', cx=W / 2):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur)
    for ln in lines:
        d.text((cx, y), ln, font=font, fill=fill, anchor='mm', stroke_width=8, stroke_fill='black')
        y += font.size * 1.2
    return y

HOOK_SECONDS = 3.0

def _wrap(d, text, font, maxw):
    text = re.sub(r'(\d) (?=\d{3}\b)', '\\1\u00a0', text)        # « 100 000 » jamais coupé
    text = re.sub(r' ([:!?;])', '\u00a0\\1', text)
    text = re.sub(r'(\d) (?=[^\W\d])', '\\1\u00a0', text)          # « 60 ans » jamais coupé                  # ponctuation jamais seule en début de ligne
    words, lines, cur = [w for w in text.split(' ') if w], [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if cur and d.textlength(t, font=font) > maxw: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur)
    return lines

def hook(d, sc, i, t):
    """Accroche des 3 premières secondes : gros bloc centré, texte jaune en majuscules sur fond noir."""
    if t > HOOK_SECONDS: return
    a, b = HOOKS[i]
    a = a.upper()
    maxw = W - 280
    size = 88
    while True:
        fa = m.F(size); la = _wrap(d, a, fa, maxw)
        if (len(la) <= 3 and max(d.textlength(x, font=fa) for x in la) <= maxw) or size <= 56: break
        size -= 6
    fb = m.F(54); lb = _wrap(d, b, fb, maxw) if b else []
    lh_a, lh_b = fa.size * 1.18, fb.size * 1.25
    box_h = len(la) * lh_a + len(lb) * lh_b + 70
    box_w = max([d.textlength(x, font=fa) for x in la] + [d.textlength(x, font=fb) for x in lb]) + 90
    top = min(1240 - box_h / 2, H * 0.80 - box_h)  # sous le visage du chaton, au-dessus de la description TikTok
    d.rounded_rectangle(((W - 120 - box_w) / 2, top, (W - 120 + box_w) / 2, top + box_h), radius=28, fill=(0, 0, 0))
    d.rounded_rectangle(((W - 120 - box_w) / 2, top, (W - 120 + box_w) / 2, top + box_h), radius=28, outline=sc['color'], width=8)
    y = top + 35 + lh_a / 2
    for x in la:
        d.text(((W - 120) / 2, y), x, font=fa, fill='#ffe14d', anchor='mm'); y += lh_a
    for x in lb:
        d.text(((W - 120) / 2, y - lh_a / 2 + lh_b / 2), x, font=fb, fill='white', anchor='mm'); y += lh_b

def end_card(im, p, sous_titre='Un nouveau JT des chatons chaque jour', couleur=(229, 185, 60, 235)):
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(110 * min(1, p * 3))))
    d.rounded_rectangle((60, 1000, W - 200, 1380), radius=40, fill=couleur)
    y = wrap_center(d, 'ABONNE-TOI', m.F(96), 1090, W - 300, cx=(W - 140) / 2)
    wrap_center(d, sous_titre, m.F(50), y + 20, W - 320, cx=(W - 140) / 2)

async def tts_end(texte=None, cache_name='gem_signature.wav'):
    texte = texte or END_TEXT
    cache = os.path.join(D, cache_name)
    if os.path.exists(cache):
        import wave
        with wave.open(cache) as w: return cache, w.getnframes() / w.getframerate(), []
    if not os.environ.get('NO_GEMINI'):
        try:
            import gem_tts
            gem_tts.say(texte, cache, 'Charon', "présentateur de journal télévisé, voix chaleureuse et souriante, rythme dynamique")
            return await tts_end(texte, cache_name)
        except BaseException as e:
            print('signature Gemini indisponible :', e, flush=True)
    try:
        import nv_tts
        wav, dur, _, _ = nv_tts.say(texte, cache, '')
        return wav, dur, []
    except BaseException as e:
        print('signature NVIDIA indisponible :', e, flush=True)
    sc = dict(text=texte, voice='fr-FR-HenriNeural')
    return await m._tts_edge('end', sc)

SHOT = 2.4

def render(i, loop):
    sc = m.SCENES[i]
    path, vdur, words = loop.run_until_complete(m.tts(i, sc))
    epath, edur, _ = loop.run_until_complete(tts_end())
    body = LEAD + vdur + 0.5
    total = body + max(END_DUR, edur + 0.6)
    jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
    wav = os.path.join(OUT, f'_a{i}.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', jg, '-i', path, '-i', epath, '-filter_complex',
        f'[0:a]aresample=48000,volume=0.6,adelay={int(body*1000)}:all=1[j];[1:a]aresample=48000,adelay={int(LEAD*1000)}:all=1[v];'
        f'[2:a]aresample=48000,adelay={int((body+0.2)*1000)}:all=1[e];[j][v][e]amix=inputs=3:normalize=0,apad,atrim=0:{total}[o]',
        '-map', '[o]', wav])
    groups = m.chunks([(a + LEAD, b + LEAD, w) for a, b, w in m.attach_punct(words, sc['text'])])
    cp = os.path.join(D, 'clips', m.CLIP_NAMES[i] + '.mp4')
    reader = m.ClipReader(cp) if os.path.exists(cp) else None
    out = os.path.join(OUT, f'{SLUG[i]}.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        t = fi / FPS
        if reader: im = reader.next()
        elif len(sc['shots']) > 2:   # plan B sans animation : plusieurs plans, coupe toutes les 2,4 s, zoom alterné, caméra à l'épaule
            k = int(t / SHOT); q = (t - k * SHOT) / SHOT
            im = m.kenburns(sc['shots'][k % len(sc['shots'])], q, 'in' if k % 2 == 0 else 'out')
            if t - k * SHOT < 0.25 and k > 0:   # petit coup de zoom à chaque coupe
                z = 1 + 0.07 * (1 - (t - k * SHOT) / 0.25); cw, ch = W / z, H / z
                im = im.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR)
            dx, dy = int(9 * math.sin(t * 2.3) + 4 * math.sin(t * 5.1)), int(7 * math.cos(t * 1.9) + 3 * math.sin(t * 4.3))
            im = im.crop((14 + dx, 14 + dy, W - 14 + dx, H - 14 + dy)).resize((W, H), Image.BILINEAR)
        else: im = m.kenburns(sc['shots'][0] if t < body * 0.55 else sc['shots'][-1], (t % (body * 0.55)) / (body * 0.55), 'in')
        if t < 0.5:  # petit zoom d'entrée : l'image bouge dès la première image
            z = 1 + 0.12 * (1 - t / 0.5) ** 2; cw, ch = W / z, H / z
            im = im.crop((int((W - cw) / 2), int((H - ch) * 0.4), int((W + cw) / 2), int((H - ch) * 0.4 + ch))).resize((W, H), Image.BILINEAR)
        d = ImageDraw.Draw(im)
        if t < body:
            m.badge(d, sc)
            if t > HOOK_SECONDS: m.caption(d, groups, t)  # pas de sous-titre sous l'accroche
            hook(d, sc, i, t)
        else:
            end_card(im, (t - body) / END_DUR)
        enc.stdin.write(im.tobytes())
    if reader: reader.close()
    enc.stdin.close(); enc.wait(); os.remove(wav)
    print('OK', out, round(total, 1), 's', 'animé' if reader else 'image fixe', flush=True)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    which = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6]
    for i in which: render(i, loop)
