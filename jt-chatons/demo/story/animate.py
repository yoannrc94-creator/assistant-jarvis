"""Anime les scènes de l'histoire avec Agnes, une par une (1 par minute en gratuit), avec un délai maximum."""
import os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vid
import wan
import importlib
MODS = sys.argv[2].split(',') if len(sys.argv) > 2 else ['scenes']
SCENES = [sc for mo in MODS for sc in importlib.import_module(mo).SCENES]
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
deadline = time.time() + float(sys.argv[1] if len(sys.argv) > 1 else 110) * 60
STOP_UTC = os.environ.get('STOP_UTC')  # ex. 06:00 : on libère la file Agnes avant la vidéo du matin
if STOP_UTC:
    import datetime as _dt
    now = _dt.datetime.utcnow(); h, mi = map(int, STOP_UTC.split(':'))
    stop = now.replace(hour=h, minute=mi, second=0)
    if stop <= now: stop += _dt.timedelta(days=1)
    deadline = min(deadline, time.time() + (stop - now).total_seconds())
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
DESC = {n: d for n, d, _ in SCENES}
todo = [n for n, _, _ in SCENES if not os.path.exists(os.path.join(D, 'clips', f'story_{n}.mp4'))]
pending = {}
wan_ok = os.path.exists(os.path.join(D, '.hf_key')); echecs = {}
while (todo or pending) and time.time() < deadline:
    if todo:
        n = todo[0]
        try:
          code, r = vid.create("The characters move naturally and expressively, small lively gestures, blinking, subtle slow camera push-in." + wan.motion(DESC[n]) + " Keep exactly the same characters, style, lighting and background. 3D animated film style.",
                             vid.data_uri('story_' + n), 6)
        except Exception as e:  # coupure réseau passagère : on réessaie au tour suivant
          code, r = 0, {'err': str(e)}
        if code == 200 and (r.get('video_id') or r.get('id')):
            pending[n] = r.get('video_id') or r.get('id'); todo.pop(0); log('accepté', n)
        else:
            log('file pleine', n, code)
            echecs[n] = echecs.get(n, 0) + 1
            if wan_ok and echecs[n] >= 3:      # Agnes saturée : secours gratuit Hugging Face
                try:
                    wan.animate('story_' + n, os.path.join(D, 'clips', f'story_{n}.mp4'), wan.PROMPT + wan.motion(DESC[n])); todo.pop(0); log('reçu (secours Wan)', n)
                except wan.QuotaEpuise as e:
                    wan_ok = False; log('secours Wan : quota du jour épuisé')
                except Exception as e:
                    log('secours Wan en échec', n, str(e)[:120])
    for n, vid_id in list(pending.items()):
        try: code, r = vid.status(vid_id)
        except Exception: continue
        st = str(r.get('status', '')).lower() if isinstance(r, dict) else ''
        if st == 'completed' and r.get('url'):
            urllib.request.urlretrieve(r['url'], os.path.join(D, 'clips', f'story_{n}.mp4')); log('reçu', n); pending.pop(n)
        elif st == 'failed':
            log('refusé', n); pending.pop(n)
    time.sleep(62)
log('FIN', 'restant :', todo, list(pending))
