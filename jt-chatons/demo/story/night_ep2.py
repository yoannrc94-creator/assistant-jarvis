import os, sys, time, subprocess
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, D); sys.path.insert(0, os.path.join(D, 'story'))
import gen_img, ep2
from scenes import STYLE
for n, desc, _ in ep2.SCENES:
    out = os.path.join(D, 'img', f'story_{n}.png')
    if os.path.exists(out): continue
    gen_img.gen(f'story_{n}', STYLE + desc, tries=8)
    time.sleep(5)
print('IMAGES FIN', flush=True)
subprocess.run([sys.executable, '-u', os.path.join(D, 'story', 'animate.py'), '110', 'ep2'], cwd=D)
subprocess.run([sys.executable, '-u', os.path.join(D, 'make_story.py'), 'ep2'], cwd=D)
print('CHAIN FIN', flush=True)
