"""Vidéo bonus : les 6 reporters du JT des chatons se présentent (à épingler sur le profil)."""
import asyncio, os, subprocess
from PIL import Image, ImageDraw
import make_tiktok as m, make_shorts as s
from make_daily import PARTIES

D, W, H, FPS = m.D, m.W, m.H, m.FPS
OUT = os.path.join(D, 'bonus'); os.makedirs(OUT, exist_ok=True)
ANCHOR = dict(kind='anchor', voice='fr-FR-HenriNeural', color='#e5b93c', tag='JT DES CHATONS', who='Maître Moustache, présentateur', rate='+14%')
LINES = {
    'lfi':  "Pacha le siamois, La France insoumise. Toujours à fond, même pendant la sieste !",
    'rn':   "Gaspard le chartreux, Rassemblement national. Calme. Trop calme ?",
    'ren':  "Mandarine, Renaissance ! Pardon, j'ai trois réunions en même temps !",
    'ps':   "Pivoine la persane, Parti socialiste. J'ai compté mes moustaches : vingt-quatre.",
    'eelv': "Flocon l'angora, Les Écologistes. Je rêve d'un monde en herbe à chat.",
    'lr':   "Bjorn le norvégien, Les Républicains. Je ne souris jamais. Sauf le dimanche.",
}
SEGS = [dict(ANCHOR, clip='anchor', text="Six chatons, six partis. Lequel te ressemble ?")]
for k, txt in LINES.items():
    p = PARTIES[k]
    SEGS.append(dict(clip=k, voice=p['voice'], color=p['color'], tag=p['tag'], who=p['name'], rate=f"{int(p['rate'].rstrip('%'))+8:+d}%", pitch=p['pitch'], text=txt))
SEGS.append(dict(ANCHOR, clip='outro', text="Ton préféré ? Dis-le en commentaire ! " + s.END_TEXT, end=True))
s.HOOKS['cast'] = ('6 chatons, 6 partis', 'Lequel te ressemble ?')

def main():
    loop = asyncio.new_event_loop()
    res = [loop.run_until_complete(m.tts(f'cast{i}', sc)) for i, sc in enumerate(SEGS)]
    LEAD, TAIL = 0.1, 0.0
    durs = [LEAD + d + TAIL for _, d, _ in res]; durs[-1] += 0.6
    total = sum(durs)
    jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
    inputs, filt, start, offs = [], [], 0.0, []
    for i, ((p, d, _), dur) in enumerate(zip(res, durs)):
        inputs += ['-i', p]; offs.append(start)
        filt.append(f'[{i}:a]aresample=48000,adelay={int((start + LEAD) * 1000)}:all=1[v{i}]'); start += dur
    n = len(res); inputs += ['-i', jg]
    filt.append(f'[{n}:a]aresample=48000,volume=0.8[j]')
    filt.append(''.join(f'[v{i}]' for i in range(n)) + f'[j]amix=inputs={n+1}:normalize=0,apad,atrim=0:{total}[o]')
    wav = os.path.join(OUT, '_cast.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[o]', wav])
    out = os.path.join(OUT, 'Bonus-les-6-chatons.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    gt = 0.0
    for i, (sc, (_, d, words), dur) in enumerate(zip(SEGS, res, durs)):
        groups = m.chunks([(a + LEAD, b + LEAD, w) for a, b, w in m.attach_punct(words, sc['text'])])
        reader = m.ClipReader(os.path.join(D, 'clips', sc['clip'] + '.mp4'))
        sig_start = None
        if sc.get('end'):  # la carte « abonne-toi » arrive avec la phrase signature
            sig_word = s.END_TEXT.split()[0]
            sig_start = next((a for a, b, w in words if w.startswith(sig_word.rstrip("'")[:4])), d * 0.5) + LEAD
        for fi in range(int(dur * FPS)):
            t = fi / FPS; g = gt + t
            im = reader.next(); dr = ImageDraw.Draw(im)
            if sig_start is not None and t >= sig_start:
                s.end_card(im, (t - sig_start) / 1.5)
            else:
                m.badge(dr, sc)
                if g > s.HOOK_SECONDS: m.caption(dr, groups, t)
                s.hook(dr, sc, 'cast', g)
            fade = min(1, (t + 1 / FPS) / 0.12, (dur - t) / 0.12)
            if fade < 1: im = Image.blend(Image.new('RGB', (W, H)), im, max(0, fade))
            enc.stdin.write(im.tobytes())
        reader.close(); gt += dur
    enc.stdin.close(); enc.wait(); os.remove(wav)
    print('OK', out, round(total, 1), 's', flush=True)

if __name__ == '__main__':
    main()
