import os, sys, time
sys.path.insert(0, os.path.join(os.getcwd(), 'story'))
import ep2
import make_multi as mm

for name, desc, text in ep2.SCENES:
    out = os.path.join('clips', f'story_{name}.mp4')
    if name == 'e2s1' or os.path.exists(out):
        print('déjà animée', name, flush=True)
        continue
    prompt = desc + ' The characters move naturally, gentle camera movement, cinematic motion.'
    for essai in range(3):
        try:
            mm.ltx_animate('story_' + name, out, prompt)
            print('LTX OK', name, flush=True)
            break
        except Exception as e:
            print('LTX essai', essai + 1, name, str(e)[:120], flush=True)
            time.sleep(10)
    else:
        print('ÉCHEC', name, flush=True)
print('FIN_ANIM', flush=True)
