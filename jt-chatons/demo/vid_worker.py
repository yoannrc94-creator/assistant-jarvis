import json, math, os, subprocess, time, urllib.request
import vid
D = vid.D
TALK = ("The {who} talks into the vintage microphone, mouth moving as if speaking, blinking, nodding, small expressive gestures with its free paw, "
        "subtle slow camera push-in. Keep exactly the same character, outfit, lighting and background. 3D animated film style.")
JOBS = [  # (nom, image de départ, fichier voix pour la durée, prompt)
    ('anchor', 'v_anchor', 0, "The kitten news anchor talks to the camera, mouth moving as if speaking, blinking, small paw gestures on the desk, subtle slow camera push-in. Keep exactly the same character, outfit, lighting and background. 3D animated film style."),
    ('lfi', 'v_lfi_a', 1, TALK.format(who='kitten reporter')),
    ('rn', 'v_rn_a', 2, TALK.format(who='kitten reporter')),
    ('ren', 'v_ren_a', 3, TALK.format(who='kitten reporter')),
    ('ps', 'v_ps_a', 4, TALK.format(who='kitten reporter')),
    ('eelv', 'v_eelv_a', 5, TALK.format(who='kitten reporter')),
    ('lr', 'v_lr_a', 6, TALK.format(who='kitten reporter')),
    ('outro', 'v_outro', 7, "The kitten news anchor happily waves its paw goodbye to the camera and smiles, blinking, subtle camera pull-back. Keep exactly the same character, outfit, lighting and background. 3D animated film style."),
]
def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)
def voice_len(i):
    p = os.path.join(D, f'tk_voice{i}.mp3')
    return float(json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', p]))['format']['duration'])
DEADLINE = time.time() + float(os.environ.get('MINUTES', '115')) * 60
for name, img, vi, prompt in JOBS:
    out = os.path.join(D, 'clips', name + '.mp4')
    if os.path.exists(out): log('déjà fait', name); continue
    secs = 5  # clips courts : fabriqués plus vite, la scène enchaîne ensuite sur le gros plan
    frame = vid.data_uri(img)
    for attempt in range(2):
        vid_id = None
        while time.time() < DEADLINE:
            code, r = vid.create(prompt, frame, secs)
            if code == 200 and (r.get('video_id') or r.get('id')):
                vid_id = r.get('video_id') or r.get('id'); log('ACCEPTÉ', name, vid_id, f'{secs}s'); break
            msg = json.dumps(r)[:200]
            if code in (429, 503) or 'queue' in msg:
                wait = 60 if code == 429 else 30
                log('file pleine', name, code); time.sleep(wait); continue
            log('REFUS', name, code, msg); break
        if not vid_id: break
        t0 = time.time()
        while time.time() - t0 < 25 * 60:
            time.sleep(10)
            code, r = vid.status(vid_id)
            st = str(r.get('status', '')).lower() if isinstance(r, dict) else ''
            if st == 'completed' and r.get('url'):
                urllib.request.urlretrieve(r['url'], out); log('TERMINÉ', name, round(time.time() - t0), 's'); break
            if st == 'failed':
                log('ÉCHEC serveur', name, json.dumps(r.get('error'))[:200]); break
        if os.path.exists(out): break
    if time.time() >= DEADLINE: log('délai de 2 h atteint'); break
log('FIN', sorted(os.listdir(os.path.join(D, 'clips'))))
