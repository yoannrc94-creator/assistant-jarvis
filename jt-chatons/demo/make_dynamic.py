"""Version « dynamique » : le chaton alterne avec des illustrations du sujet, chiffres clés en grand, petit zoom à chaque plan.

Usage : python3 make_dynamic.py config.json sortie.mp4
config (en plus des champs habituels) : "illus": [[mot_déclencheur, image, étiquette], ...]
  ex. [["Un", "test_vote", "100 000 VOTANTS"], ["Deux", "test_cyber", "VOTE PROLONGÉ"], ...]
"""
import asyncio, json, os, subprocess, sys
from PIL import Image, ImageDraw
import make_tiktok as m, make_shorts as s, make_daily as dly

D, W, H, FPS = m.D, m.W, m.H, m.FPS
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
p = dly.PARTIES[cfg['party']]
text = ' '.join(x for x in (cfg['text'].rstrip(), cfg.get('reaction', p['catch']), cfg.get('question', '')) if x)
ep = cfg.get('episode')
sc = dict(kind='party', episode=ep, voice=p['voice'], color=p['color'], tag=p['tag'],
          who=f"{p['name']} · Sources : {cfg['source']}", text=text, rate=p['rate'], pitch=p['pitch'])
m.SCENES.append(sc); i = len(m.SCENES) - 1
s.HOOKS[i] = (cfg['hook1'], cfg['hook2'])
loop = asyncio.new_event_loop()
path, vdur, words = loop.run_until_complete(m.tts(i, sc))
epath, edur, _ = loop.run_until_complete(s.tts_end())
LEAD = s.LEAD; body = LEAD + vdur + 0.5; total = body + max(s.END_DUR, edur + 0.6)

# fenêtres d'illustration : du mot déclencheur jusqu'au suivant (4,5 s max)
starts = []
for trig, img, label in cfg['illus']:
    t = next((a for a, b, w in words if w.strip('.,:!?') == trig and a + LEAD > (starts[-1][0] + 0.5 if starts else s.HOOK_SECONDS)), None)
    if t is not None: starts.append((t + LEAD, img, label))
wins = []
for k, (t, img, label) in enumerate(starts):
    nxt = starts[k + 1][0] if k + 1 < len(starts) else body - 3
    wins.append((t, min(t + 4.5, nxt - 0.4), img, label))
print('plans illustrés :', [(round(a, 1), round(b, 1), img) for a, b, img, _ in wins], flush=True)

jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
wav = os.path.join(D, '_dyn.wav')
subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', jg, '-i', path, '-i', epath, '-filter_complex',
    f'[0:a]aresample=48000,volume=0.6,adelay={int(body*1000)}:all=1[j];[1:a]aresample=48000,adelay={int(LEAD*1000)}:all=1[v];'
    f'[2:a]aresample=48000,adelay={int((body+0.2)*1000)}:all=1[e];[j][v][e]amix=inputs=3:normalize=0,apad,atrim=0:{total}[o]',
    '-map', '[o]', wav])
groups = m.chunks([(a + LEAD, b + LEAD, w) for a, b, w in m.attach_punct(words, text)])
reader = m.ClipReader(os.path.join(D, 'clips', cfg['clip'] + '.mp4'))

def punch(im, dt, amount=0.10, dur=0.3):
    if dt >= dur: return im
    z = 1 + amount * (1 - dt / dur) ** 2; cw, ch = W / z, H / z
    return im.crop((int((W - cw) / 2), int((H - ch) * 0.4), int((W + cw) / 2), int((H - ch) * 0.4 + ch))).resize((W, H), Image.BILINEAR)

def pop(d, label, dt, color):
    """Chiffre clé en grand, avec un petit rebond à l'apparition."""
    if dt < 0: return
    k = min(1, dt / 0.18); scale = 0.6 + 0.5 * k if k < 1 else 1.1 - 0.1 * min(1, (dt - 0.18) / 0.12)
    f = m.F(int(92 * scale)); tw = d.textlength(label, font=f)
    while tw > W - 260 and f.size > 40: f = m.F(f.size - 4); tw = d.textlength(label, font=f)
    cx, cy = (W - 120) / 2, 820
    d.rounded_rectangle((cx - tw / 2 - 40, cy - f.size * 0.75, cx + tw / 2 + 40, cy + f.size * 0.75), radius=26, fill='#ffe14d', outline=color, width=8)
    d.text((cx, cy), label, font=f, fill='black', anchor='mm')

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
cut = 0.0
for fi in range(int(total * FPS)):
    t = fi / FPS
    cat = reader.next()                                   # le clip avance toujours, pour rester fluide
    w = next((x for x in wins if x[0] <= t < x[1]), None)
    if w:
        a, b, img, label = w
        im = m.kenburns(img, (t - a) / max(0.1, b - a), 'in' if wins.index(w) % 2 == 0 else 'out'); cut = a
    else:
        im = cat
        prev = [x[1] for x in wins if x[1] <= t]
        cut = max(prev) if prev else 0.0
    im = punch(im, t - cut)
    d = ImageDraw.Draw(im)
    if t < body:
        m.badge(d, sc)
        if w: pop(d, w[3], t - w[0] - 0.4, sc['color'])
        if t > s.HOOK_SECONDS: m.caption(d, groups, t)
        s.hook(d, sc, i, t)
    else:
        s.end_card(im, (t - body) / s.END_DUR)
    enc.stdin.write(im.tobytes())
reader.close(); enc.stdin.close(); enc.wait(); os.remove(wav)
print('OK', out, round(total, 1), 's', flush=True)
