"""Animation de secours gratuite (Hugging Face, modèle Wan 2.2, environ 5 minutes de calcul par jour) quand la file Agnes est pleine."""
import os, shutil, subprocess
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
SPACE = 'zerogpu-aoti/wan2-2-fp8da-aoti-faster'
PROMPT = "The characters move naturally and expressively, small lively gestures, blinking, subtle slow camera push-in. Keep exactly the same characters, style and background. 3D animated film style."

AMBIANCES = [  # mot du décor -> ce qui bouge en fond
    (('confetti', 'party', 'celebration', 'celebrating', 'fête'), 'confetti falling and swirling'),
    (('park', 'garden', 'tree', 'grass', 'forest', 'field'), 'leaves and grass swaying gently in the breeze'),
    (('sky', 'pigeon', 'bird', 'cloud'), 'clouds drifting slowly across the sky'),
    (('chandelier', 'candle', 'lamp', 'light bulb', 'neon', 'lights'), 'lights flickering and glowing softly'),
    (('crowd', 'kittens', 'audience', 'chamber', 'parliament', 'meeting', 'rally', 'arena', 'stadium'), 'background characters moving, chatting and reacting'),
    (('paper', 'document', 'book', 'scroll', 'folder'), 'pages fluttering slightly'),
    (('rain',), 'rain falling'), (('snow',), 'snowflakes falling'),
    (('street', 'city', 'traffic', 'station', 'gas station', 'pump'), 'distant cars and passers-by moving'),
    (('flag', 'banner'), 'flags and banners waving'),
    (('screen', 'tv', 'television', 'studio'), 'screens glowing and changing'),
    (('hourglass', 'clock'), 'sand flowing, clock hands moving'),
    (('sea', 'water', 'river', 'beach'), 'water rippling and shimmering'),
]

def motion(desc):
    """Phrase d'ambiance pour le fond, tirée de la description de la scène (au plus 2 éléments)."""
    import re
    d = (desc or '').lower(); amb = [m for keys, m in AMBIANCES if any(re.search(r'\b' + re.escape(k) + r'(s|es)?\b', d) for k in keys)][:2]
    return (' Background comes alive: ' + ', '.join(amb) + '.') if amb else ' Subtle ambient motion in the background (light, air, small details).'

class QuotaEpuise(Exception): pass

def animate(img_name, out, prompt=PROMPT, seconds=3.5):
    """img/<img_name>.png -> out (mp4). Lève QuotaEpuise si le quota du jour est consommé."""
    from gradio_client import Client, handle_file
    src = os.path.join(D, 'img', img_name + '.png'); tmp = os.path.join(D, '_wan_in.jpg')
    im = Image.open(src).convert('RGB'); im.thumbnail((720, 1280)); im.save(tmp, quality=92)
    tok = open(os.path.join(D, '.hf_key')).read().strip()
    # plusieurs services du même modèle : si l'un est en panne, on passe au suivant (14 octobre)
    essais = [(SPACE, lambda c: c.predict(handle_file(tmp), prompt, 6, duration_seconds=seconds, api_name='/generate_video')),
              ('r3gm/wan2-2-fp8da-aoti-preview', lambda c: c.predict(input_image=handle_file(tmp), last_image=None, prompt=prompt, duration_seconds=seconds, api_name='/generate_video')),
              ('multimodalart/wan2-1-fast', lambda c: c.predict(input_image=handle_file(tmp), prompt=prompt, height=832, width=480, duration_seconds=min(seconds, 3), api_name='/generate_video'))]
    v, err = None, None
    for sp, call in essais:
        try:
            r = call(Client(sp, token=tok, verbose=False)); v = r[0] if isinstance(r, (list, tuple)) else r; break
        except Exception as e:
            if 'quota' in str(e).lower() or 'limit' in str(e).lower(): raise QuotaEpuise(str(e)[:200])
            err = e; print('service', sp, 'en panne :', type(e).__name__, flush=True)
    if v is None: raise err
    p = v['video'] if isinstance(v, dict) else v
    # remise à la taille des autres clips (1080 de large, 9:16)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', p, '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-crf', '18', '-an', out])
    return out
