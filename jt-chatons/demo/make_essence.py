"""Édition spéciale essence : le présentateur puis les 6 reporters, chacun donne la proposition de son parti (sources citées)."""
import asyncio, os, subprocess
from PIL import Image, ImageDraw
import make_tiktok as m, make_shorts as s
from make_daily import PARTIES, ANCHOR_VOICE

D, W, H, FPS = m.D, m.W, m.H, m.FPS
OUT = os.path.join(D, 'bonus'); os.makedirs(OUT, exist_ok=True)
ANCHOR = dict(kind='anchor', voice='fr-FR-HenriNeural', color='#b3262e', tag='ÉDITION SPÉCIALE', who='Maître Moustache · Sources : Brut, Le Parisien', rate='+14%', gvoice=ANCHOR_VOICE[0], gstyle=ANCHOR_VOICE[1])
LINES = {
    'lfi':  ("franceinfo", "Pacha, pour LFI ! Les insoumis veulent bloquer le prix de l'essence à un euro soixante-dix le litre, et bloquer les marges des raffineurs !"),
    'rn':   ("franceinfo", "Gaspard, pour le RN. Le parti veut baisser la TVA sur les carburants, le fioul et le gaz, de 20 à 5,5 pour cent."),
    'ren':  ("franceinfo", "Mandarine, Renaissance ! Gabriel Attal appelle les distributeurs à plafonner leurs prix, et veut des aides ciblées pour ceux qui doivent prendre leur voiture."),
    'ps':   ("Capital", "Pivoine, pour la gauche. Raphaël Glucksmann, candidat à la primaire du PS et de Place publique, refuse de baisser les taxes sur l'essence."),
    'eelv': ("Midi Libre", "Flocon, pour Les Écologistes. Dans leur projet de budget, ils proposent une taxe sur les pétroliers."),
    'lr':   ("franceinfo", "Bjorn, pour LR. Bruno Retailleau veut supprimer les certificats d'économie d'énergie, pour baisser l'essence de 15 à 17 centimes, sans toucher à la TVA."),
}
SEGS = [dict(ANCHOR, clip='anchor', text="Le gazole à 2 euros 41, record battu ! Le gouvernement vise une baisse de 12 à 18 centimes. Et les partis, ils proposent quoi ?")]
for k, (src, txt) in LINES.items():
    p = PARTIES[k]
    SEGS.append(dict(clip=k, voice=p['voice'], color=p['color'], tag=p['tag'], who=f"{p['name']} · Source : {src}", rate=f"{int(p['rate'].rstrip('%'))+8:+d}%", pitch=p['pitch'],
                     gvoice=p['gvoice'], gstyle=p['gstyle'], text=txt))
SEGS.append(dict(ANCHOR, clip='outro', who='Maître Moustache, présentateur', text="Et toi, tu choisis laquelle ? Dis-le en commentaire ! " + s.END_TEXT, end=True))
s.HOOKS['cast'] = ('Essence, qui a la solution ?', 'Édition spéciale, 6 reporters')

def main():
    loop = asyncio.new_event_loop()
    res = [loop.run_until_complete(m.tts(f'ess{i}', sc)) for i, sc in enumerate(SEGS)]
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
    wav = os.path.join(OUT, '_essence.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[o]', wav])
    out = os.path.join(OUT, 'Bonus-edition-speciale-essence.mp4')
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
