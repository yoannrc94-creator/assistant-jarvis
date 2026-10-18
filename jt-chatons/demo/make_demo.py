"""Exemple de JT des chatons rendu image par image (PIL) puis encodé avec ffmpeg."""
import math, subprocess, json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from gtts import gTTS

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, S, FPS = 1280, 720, 2, 24          # rendu en 2x puis réduit (anti-crénelage)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = lambda p, size: ImageFont.truetype(p, int(size * S))

SCENES = [
    dict(kind='anchor', text="Bonsoir, et bienvenue dans le JT des chatons. Ce soir, nos reporters font le tour des partis politiques."),
    dict(kind='reporter', text="Ici notre reporter, en direct. Dans la version complète, ce texte est écrit par l'intelligence artificielle à partir des actualités du jour."),
]

def tts(i, text):
    path = os.path.join(OUT, f'voice{i}.mp3')
    gTTS(text, lang='fr').save(path)
    d = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', path]))['format']['duration'])
    return path, d

def P(*xy):  # coordonnées logiques -> rendu 2x
    return [v * S for v in xy]

# ── Chat ───────────────────────────────────────────────────────────
def draw_cat(d, cx, cy, sc, fur, mask, helmet, trim, robe, blink, mouth, mic=False, stripes=False, stripe='#c8641e'):
    k = lambda v: v * sc
    # robe (corps)
    d.polygon(P(cx - k(95), cy + k(260), cx - k(70), cy + k(95), cx + k(70), cy + k(95), cx + k(95), cy + k(260)), fill=robe)
    d.polygon(P(cx - k(30), cy + k(95), cx, cy + k(160), cx + k(30), cy + k(95)), fill=trim)       # col
    d.rectangle(P(cx - k(88), cy + k(185), cx + k(88), cy + k(205)), fill=trim)                       # ceinture
    # pattes
    for sx in (-1, 1):
        d.ellipse(P(cx + sx * k(62) - k(22), cy + k(150), cx + sx * k(62) + k(22), cy + k(190)), fill=fur)
    if mic:
        d.rectangle(P(cx + k(55), cy + k(95), cx + k(66), cy + k(165)), fill='#5a5a66')
        d.ellipse(P(cx + k(42), cy + k(62), cx + k(80), cy + k(102)), fill='#2b2b33')
        d.ellipse(P(cx + k(62) - k(22), cy + k(140), cx + k(62) + k(22), cy + k(180)), fill=fur)
    # tête
    d.ellipse(P(cx - k(92), cy - k(80), cx + k(92), cy + k(105)), fill=fur)
    if mask:
        d.ellipse(P(cx - k(52), cy - k(10), cx + k(52), cy + k(95)), fill=mask)
    if stripes:
        for sx in (-1, 1):
            for j in range(3):
                y = cy + k(10 + j * 18)
                d.line(P(cx + sx * k(92), y, cx + sx * k(62), y + k(4)), fill=stripe, width=int(k(6) * S))
    # casque (dôme) + visière relevée
    d.chord(P(cx - k(104), cy - k(140), cx + k(104), cy + k(60)), 180, 360, fill=helmet)
    d.rectangle(P(cx - k(104), cy - k(42), cx + k(104), cy - k(30)), fill=trim)
    d.rounded_rectangle(P(cx - k(70), cy - k(128), cx + k(70), cy - k(100)), radius=int(k(10) * S), fill='#b7d9e6')
    # yeux
    for sx in (-1, 1):
        ex = cx + sx * k(36)
        if blink:
            d.line(P(ex - k(14), cy + k(22), ex + k(14), cy + k(22)), fill='#1e1e24', width=int(k(5) * S))
        else:
            d.ellipse(P(ex - k(15), cy + k(5), ex + k(15), cy + k(40)), fill='#1e1e24')
            d.ellipse(P(ex - k(7), cy + k(10), ex + k(1), cy + k(19)), fill='white')
    # nez, bouche, moustaches
    d.polygon(P(cx - k(10), cy + k(50), cx + k(10), cy + k(50), cx, cy + k(61)), fill='#e98a9a')
    if mouth:
        d.ellipse(P(cx - k(11), cy + k(62), cx + k(11), cy + k(82)), fill='#7a2e3a')
    else:
        d.line(P(cx - k(12), cy + k(70), cx, cy + k(63), cx + k(12), cy + k(70)), fill='#1e1e24', width=int(k(3) * S))
    for sx in (-1, 1):
        for dy in (-6, 6):
            d.line(P(cx + sx * k(22), cy + k(60), cx + sx * k(95), cy + k(60 + dy * 1.6)), fill='#f5f0e4', width=int(k(2) * S))

# ── Décors ─────────────────────────────────────────────────────────
def studio():
    im = Image.new('RGB', (W * S, H * S), '#f4c9c4')
    d = ImageDraw.Draw(im)
    d.rectangle(P(0, 470, W, H), fill='#a9d8c4')                     # sol menthe
    for i in range(0, W, 80):                                         # lambris symétriques
        d.rectangle(P(i + 8, 300, i + 72, 460), outline='#e8b3ad', width=3 * S)
    d.ellipse(P(W / 2 - 230, 40, W / 2 + 230, 400), fill='#fbe7c6', outline='#d9a441', width=8 * S)  # écran rond
    d.text(P(W / 2, 220), 'JT', font=font(FB, 120), fill='#d9a441', anchor='mm')
    for sx in (-1, 1):                                                # lampes
        x = W / 2 + sx * 430
        d.rectangle(P(x - 6, 150, x + 6, 470), fill='#d9a441')
        d.chord(P(x - 60, 100, x + 60, 200), 180, 360, fill='#fbe7c6')
    return im

def desk(d):
    d.rectangle(P(W / 2 - 320, 470, W / 2 + 320, 640), fill='#b5794a')
    d.rectangle(P(W / 2 - 340, 455, W / 2 + 340, 480), fill='#8c5a34')
    for i in range(-2, 3):
        x = W / 2 + i * 120
        d.rectangle(P(x - 40, 505, x + 40, 610), outline='#d9a441', width=4 * S)

def square(accent):
    im = Image.new('RGB', (W * S, H * S), '#bfe0ee')
    d = ImageDraw.Draw(im)
    d.rectangle(P(0, 500, W, H), fill='#e9d8b4')
    for i in range(0, W, 60):
        d.line(P(i, 500, W / 2 + (i - W / 2) * 1.8, H), fill='#d8c39a', width=2 * S)
    cols = ['#f6d3c8', '#fbe7c6', '#d9ead3', '#fbe7c6', '#f6d3c8']
    for n, c in enumerate(cols):                                       # façades symétriques
        x0 = 40 + n * 244
        top = 150 if n in (0, 4) else 110 if n in (1, 3) else 70
        d.rectangle(P(x0, top, x0 + 220, 500), fill=c)
        d.polygon(P(x0 - 10, top, x0 + 110, top - 50, x0 + 230, top), fill='#c98b7a')
        for r in range(3):
            for q in range(3):
                wx, wy = x0 + 30 + q * 62, top + 40 + r * 95
                d.rectangle(P(wx, wy, wx + 36, wy + 55), fill='#8fb9cc', outline='white', width=3 * S)
        d.rectangle(P(x0 + 90, 430, x0 + 130, 500), fill='#8c5a34')
    for i in range(14):                                                # fanions couleur du parti
        x = 40 + i * 92
        d.polygon(P(x, 40, x + 60, 40, x + 30, 85), fill=accent if i % 2 == 0 else '#fbe7c6')
    d.line(P(0, 40, W, 40), fill='#8c5a34', width=3 * S)
    return im

# ── Habillage ──────────────────────────────────────────────────────
def overlay(im, color, tag, title, sub, example):
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle(P(28, 26, 380, 72), fill=(10, 10, 18, 190))
    d.text(P(44, 49), 'JT DES CHATONS · DIRECT', font=font(FB, 20), fill='#e5c15a', anchor='lm')
    if example:
        d.rectangle(P(W - 200, 26, W - 28, 72), fill=(200, 60, 60, 220))
        d.text(P(W - 114, 49), 'EXEMPLE', font=font(FB, 20), fill='white', anchor='mm')
    y = H - 168
    d.rectangle(P(0, y, 130, y + 110), fill=color)
    d.rectangle(P(130, y, W, y + 110), fill=(245, 240, 228, 240))
    d.text(P(65, y + 55), tag, font=font(FB, 30), fill='white', anchor='mm')
    size = 28
    while size > 16 and d.textlength(title, font=font(FB, size)) > (W - 180) * S: size -= 1
    d.text(P(154, y + 38), title, font=font(FB, size), fill='#16161f', anchor='lm')
    size = 19
    while size > 12 and d.textlength(sub, font=font(FR, size)) > (W - 180) * S: size -= 1
    d.text(P(154, y + 80), sub, font=font(FR, size), fill='#4a4858', anchor='lm')

def frame(scene, t, dur):
    blink = (t % 2.7) < 0.12
    talking = 0.4 < t < dur - 0.6
    mouth = talking and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.2) * 4
    if scene['kind'] == 'anchor':
        im = studio(); d = ImageDraw.Draw(im)
        draw_cat(d, W / 2, 300 + bob, 1.0, fur='#f0a35e', mask=None, helmet='#f6ead2', trim='#d9a441',
                 robe='#f6ead2', blink=blink, mouth=mouth, stripes=True)
        desk(d)
        ov = ('#e5c15a', 'JT', 'Le JT des Chatons', 'Maître Moustache · Présentateur', True)
        zoom = 1 + 0.07 * (t / dur)                                     # lent travelling avant
    else:
        accent = '#cc2444'
        im = square(accent); d = ImageDraw.Draw(im)
        draw_cat(d, W / 2, 250 + bob, 1.05, fur='#f3e6cf', mask='#6b4a3a', helmet=accent, trim='#e5c15a',
                 robe=accent, blink=blink, mouth=mouth, mic=True)
        ov = (accent, 'LFI', "Titre de l'actualité du parti", 'Reporter chaton siamois · En duplex · Source : média', True)
        zoom = 1.06 - 0.06 * (t / dur)
    cw, ch = W * S / zoom, H * S / zoom
    x0, y0 = (W * S - cw) / 2, (H * S - ch) / 2
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W * S, H * S), Image.BILINEAR)
    overlay(im, *ov)                                                    # habillage fixe, hors zoom
    return im.resize((W, H), Image.LANCZOS)

def main():
    voices, durs = [], []
    for i, sc in enumerate(SCENES):
        p, d = tts(i, sc['text']); voices.append(p); durs.append(max(6.0, d + 0.9))
    total = sum(durs)
    # audio : voix placées au début de chaque scène
    filt, inputs, start = [], [], 0.0
    for i, (p, d) in enumerate(zip(voices, durs)):
        inputs += ['-i', p]
        filt.append(f'[{i}:a]adelay={int((start + 0.4) * 1000)}|{int((start + 0.4) * 1000)}[a{i}]')
        start += d
    filt.append(''.join(f'[a{i}]' for i in range(len(voices))) + f'amix=inputs={len(voices)}:normalize=0,apad,atrim=0:{total}[aout]')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[aout]', os.path.join(OUT, 'audio.wav')])

    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', os.path.join(OUT, 'audio.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', os.path.join(OUT, 'exemple-jt-chatons.mp4')],
                           stdin=subprocess.PIPE)
    for sc, dur in zip(SCENES, durs):
        n = int(dur * FPS)
        for f in range(n):
            t = f / FPS
            im = frame(sc, t, dur)
            fade = min(1, t / 0.3, (dur - t) / 0.3)                        # fondu entre scènes
            if fade < 1:
                im = Image.blend(Image.new('RGB', (W, H)), im, max(0, fade))
            enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()
    print('durée', round(total, 1), 's')

if __name__ == '__main__':
    main()
