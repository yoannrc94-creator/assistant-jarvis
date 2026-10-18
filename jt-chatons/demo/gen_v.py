import time, gen_img
S = ('3D animated feature film still, cute stylized characters with big expressive eyes and soft fur, warm golden cinematic lighting, '
     'rich saturated colors, shallow depth of field, high quality 3D render, vertical shot. No text, no letters, no writing, no logos, no flags, no humans. ')
CAT = ('an adorable {cat} kitten field reporter wearing a {col} retro motorcycle helmet with the visor up and its cat ears poking out, '
       'and a {col} kung-fu robe with a {trim} belt, holding a tiny vintage silver microphone')
P = {
 'lfi':  dict(cat='Siamese', col='crimson red', trim='gold', bg='a grand parliament hemicycle with tiered red velvet benches and cream columns'),
 'rn':   dict(cat='blue-gray Chartreux', col='deep navy blue', trim='gold', bg='a busy retro campaign office with wooden desks, rotary phones and filing cabinets'),
 'ren':  dict(cat='fluffy brown tabby Maine Coon', col='bright tangerine orange', trim='sky blue', bg='a sunny Provence village square with a small wooden stage and lavender planters'),
 'ps':   dict(cat='fluffy cream Persian', col='rose pink', trim='lavender', bg='a cozy room with vintage voting booths with pink curtains and transparent ballot boxes'),
 'eelv': dict(cat='fluffy white Turkish Angora', col='jade green', trim='lemon yellow', bg='a sunlit glass greenhouse full of lush plants and lemon trees'),
 'lr':   dict(cat='fluffy gray-brown Norwegian Forest', col='royal blue', trim='white', bg='an old French school classroom with wooden desks, a blank green chalkboard and a globe'),
}
JOBS = []
for k, d in P.items():
    c = CAT.format(**d)
    JOBS.append((f'v_{k}_a', f'Medium-wide shot of {c}, standing in the center and talking to the camera with an earnest expression. Background: {d["bg"]}.'))
    JOBS.append((f'v_{k}_b', f'Close-up portrait of {c}, raising its eyebrows with a funny, surprised expression, leaning toward the camera. Blurred background: {d["bg"]}.'))
JOBS.append(('v_outro', 'A retro TV news studio. Behind a glossy wooden news desk, an adorable fluffy ginger tabby kitten news anchor wearing a cream and gold retro motorcycle helmet and a cream kung-fu robe with a mustard sash happily waves one paw goodbye to the camera with a big smile. Brass lamps and a glowing vintage TV screen behind.'))
for name, p in JOBS:
    t = time.time(); gen_img.gen(name, S + p, size='2K', ratio='9:16'); time.sleep(max(0, 13 - (time.time() - t)))
