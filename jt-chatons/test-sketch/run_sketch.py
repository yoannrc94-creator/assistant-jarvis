"""Test : scène à deux chatons qui parlent, voix clonée de l'utilisateur, images et animations. Fiction."""
import json, os, sys, subprocess, wave
DEMO = '/tmp/claude-0/-home-user-assistant-jarvis/45b2ce9a-ba2b-5f9f-98c9-bdcc4dc5d6fd/scratchpad/demo'
SK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DEMO); os.chdir(DEMO)
import make_multi as mm, gen_img, make_daily as md
scene = json.load(open(os.path.join(SK, 'scene.json'), encoding='utf-8'))
out_dir = os.path.join(SK, 'out'); os.makedirs(out_dir, exist_ok=True)
p = dict(cat='ginger tabby', col='navy', name='Maître Moustache', tag='LE JT DES CHATONS')
clips, audios, durs = [], [], []
for i, pl in enumerate(scene['plans']):
    perso = scene['personnages'][pl['qui']]
    name = f"sketch_{i}"
    img = os.path.join(DEMO, 'img', name + '.png')
    if not os.path.exists(img):
        gen_img.gen(name, md.STYLE + perso + ', ' + pl['action'] + '. Setting: a town hall waiting room with posters and plastic chairs.', size='2K', ratio='9:16')
    seg = dict(subject=perso + ', ', action=pl['action'], bg='a town hall waiting room with posters and plastic chairs, no people')
    clip = mm.make_scene_clip(name, p, seg, 4)
    clips.append(clip)
    wav = os.path.join(out_dir, f'voix_{i}.wav')
    import nv_tts
    for essai in range(3):   # la voix NVIDIA renvoie parfois un audio trop court : on réessaie
        try:
            _, d, _, _ = nv_tts.say(pl['texte'], wav, pl['qui']); break
        except RuntimeError as e:
            print('essai', essai + 1, 'plan', i, str(e), flush=True)
    with wave.open(wav) as w: d = w.getnframes() / w.getframerate()
    audios.append(wav); durs.append(max(3.0, d + 0.6))
    print('plan', i, 'clip', clip is not None, 'voix', round(d, 2), flush=True)
print('durées plans', durs, 'total', round(sum(durs), 2), flush=True)
json.dump({'durees': durs, 'clips': clips, 'voix': audios}, open(os.path.join(out_dir, 'manifest.json'), 'w'), ensure_ascii=False)
