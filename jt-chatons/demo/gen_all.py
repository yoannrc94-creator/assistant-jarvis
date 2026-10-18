import time, gen_img
STYLE = ("Wes Anderson film still, perfectly symmetrical centered composition, flat pastel color palette, meticulous dollhouse-like "
         "miniature set, soft even lighting, 35mm film grain, whimsical deadpan mood. No text, no letters, no writing, no logos, no flags, no humans. ")
REP = ("In the exact center stands a {cat} kitten field reporter facing the camera with a serious expression, wearing a {col} retro "
       "motorcycle helmet with the visor up and cat ears poking out, and a {col} Shaolin kung-fu robe with a {trim} belt, holding a tiny "
       "vintage silver microphone in its front paws. ")
JOBS = [
 ('lfi',  REP.format(cat='Siamese', col='crimson red', trim='gold') + "Background: a grand symmetrical neoclassical parliament hemicycle with tiered crimson velvet benches and cream columns."),
 ('rn',   REP.format(cat='blue-gray Chartreux', col='deep navy blue', trim='gold') + "Background: a symmetrical retro campaign office with rows of identical wooden desks, rotary telephones and navy blue filing cabinets."),
 ('ren',  REP.format(cat='brown tabby Maine Coon', col='bright tangerine orange', trim='sky blue') + "Background: a sunny symmetrical Provence village square with an empty wooden stage, lavender planters and pastel facades."),
 ('ps',   REP.format(cat='cream Persian', col='rose pink', trim='lavender') + "Background: a symmetrical pastel room with a row of vintage voting booths with pink curtains and transparent ballot boxes."),
 ('eelv', REP.format(cat='white Turkish Angora', col='jade green', trim='lemon yellow') + "Background: a symmetrical Victorian glass greenhouse full of lush plants, ferns and potted lemon trees."),
 ('lr',   REP.format(cat='gray-brown Norwegian Forest', col='royal blue', trim='white') + "Background: a symmetrical old French school classroom with wooden desks in rows, a blank green chalkboard and a globe."),
 ('anchor_outro', "A retro 1970s TV news studio. In the exact center, behind a polished wooden news desk, a fluffy ginger tabby kitten news anchor wearing a cream and gold retro motorcycle helmet and a cream Shaolin kung-fu robe with a mustard sash raises one paw to wave goodbye to the camera, gentle smile. Two symmetrical brass lamps, a large rounded mint and pink screen behind."),
]
for i, (name, p) in enumerate(JOBS):
    t = time.time()
    gen_img.gen(name, STYLE + p)
    time.sleep(max(0, 14 - (time.time() - t)))   # 2K gratuit : 5 images/min
