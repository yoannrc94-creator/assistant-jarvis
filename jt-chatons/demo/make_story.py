"""Format « histoire » (test) : une scène par phrase, voix du narrateur, animation Agnes si disponible sinon zoom lent."""
import asyncio, os, subprocess, sys
from PIL import Image, ImageDraw
import make_tiktok as m, make_shorts as s
from make_daily import ANCHOR_VOICE
sys.path.insert(0, os.path.join(m.D, 'story')); import importlib
EP = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else 'scenes'); SCENES = EP.SCENES

D, W, H, FPS = m.D, m.W, m.H, m.FPS
OUT = os.path.join(D, 'bonus', EP.SLUG + '.mp4')
BASE = dict(kind='anchor', voice='fr-FR-HenriNeural', rate='+12%', color='#7b3fe4', tag='LA POLITIQUE EXPLIQUÉE',
            who='Raconté par Maître Moustache · Sources : vie-publique.fr', gvoice=ANCHOR_VOICE[0],
            gstyle="conteur de dessin animé, voix chaleureuse, enjouée et claire, rythme vif")
SEGS = [dict(BASE, name=n, text=t) for n, _, t in SCENES]
STORY_END = "C'était La politique expliquée, abonne-toi pour le prochain épisode !"  # pas de « demain » : 2 à 3 histoires par semaine
SEGS[-1]['text'] += ' ' + STORY_END; SEGS[-1]['end'] = True
s.HOOKS['story'] = EP.TITLE

def main():
    loop = asyncio.new_event_loop()
    if os.environ.get('REUSE_VOICES'):  # remontage sans reconsommer le quota : voix déjà générées
        import gem_align
        def _reuse(i, sc):
            p = os.path.join(D, f'tk_voicestory{i}.wav'); d = m.probe(p) if hasattr(m, 'probe') else float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))
            ws = []
            for a, b, w in gem_align.words_timing(p, sc['text'], d):   # « ? » et « ! » isolés : collés au mot précédent
                if ws and not any(ch.isalnum() for ch in w): ws[-1] = (ws[-1][0], b, ws[-1][2] + '\u00a0' + w)
                else: ws.append((a, b, w))
            return p, d, ws
        res = [_reuse(i, sc) for i, sc in enumerate(SEGS)]
    else:
        res = [loop.run_until_complete(m.tts(f'story{i}', sc)) for i, sc in enumerate(SEGS)]
    LEAD = 0.08
    durs = [LEAD + d + 0.15 for _, d, _ in res]; durs[-1] += 0.8
    total = sum(durs)
    jg = os.path.join(D, 'tk_jingle.wav'); m.jingle(jg, total)
    inputs, filt, start = [], [], 0.0
    for i, ((p, d, _), dur) in enumerate(zip(res, durs)):
        inputs += ['-i', p]; filt.append(f'[{i}:a]aresample=48000,adelay={int((start + LEAD) * 1000)}:all=1[v{i}]'); start += dur
    n = len(res); inputs += ['-i', jg]
    filt.append(f'[{n}:a]aresample=48000,volume=0.6,adelay={int((total - 1.2) * 1000)}:all=1[j]')
    filt.append(''.join(f'[v{i}]' for i in range(n)) + f'[j]amix=inputs={n+1}:normalize=0,apad,atrim=0:{total}[o]')
    wav = os.path.join(D, '_story.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[o]', wav])
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    gt, animated = 0.0, 0
    for i, (sc, (_, d, words), dur) in enumerate(zip(SEGS, res, durs)):
        groups = m.chunks([(a + LEAD, b + LEAD, w) for a, b, w in m.attach_punct(words, sc['text'])])
        cp = os.path.join(D, 'clips', f"story_{sc['name']}.mp4")
        reader = m.ClipReader(cp) if os.path.exists(cp) else None; animated += bool(reader)
        sig = None
        if sc.get('end'): sig = next((a for a, b, w in words if w.startswith("C'ét")), d * 0.6) + LEAD
        for fi in range(int(dur * FPS)):
            t = fi / FPS; g = gt + t
            im = reader.next() if reader else m.kenburns('story_' + sc['name'], t / dur, 'in' if i % 2 == 0 else 'out')
            if t < 0.3:                                    # petit zoom à chaque changement de scène
                z = 1 + 0.08 * (1 - t / 0.3) ** 2; cw, ch = W / z, H / z
                im = im.crop((int((W - cw) / 2), int((H - ch) * 0.4), int((W + cw) / 2), int((H - ch) * 0.4 + ch))).resize((W, H), Image.BILINEAR)
            dr = ImageDraw.Draw(im)
            if sig is not None and t >= sig:
                s.end_card(im, (t - sig) / 1.5)
            else:
                m.badge(dr, sc)
                if g > s.HOOK_SECONDS: m.caption(dr, groups, t)
                s.hook(dr, sc, 'story', g)
            enc.stdin.write(im.tobytes())
        if reader: reader.close()
        gt += dur
    enc.stdin.close(); enc.wait(); os.remove(wav)
    print('OK', OUT, round(total, 1), 's', f'{animated}/{len(SEGS)} scènes animées', flush=True)

if __name__ == '__main__':
    main()
