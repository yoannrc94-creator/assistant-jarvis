"""Voix Gemini (gratuite) : texte + façon de dire (annotation « style », jamais lue) -> wav."""
import base64, json, os, sys, time, urllib.request
KEY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gemini_key')).read().strip()
MODELS = ['gemini-3.8-flash-tts', 'gemini-3.8-flash-lite-tts']

def say(text, out, voice='Kore', style='', model=None, tries=4):
    part = {'type': 'text', 'text': text}
    if style: part['annotations'] = [{'type': 'speech_metadata', 'style': style}]
    last = None
    for mdl in ([model] if model else MODELS):
        body = {'model': mdl, 'input': [{'type': 'user_input', 'content': [part]}],
                'response_format': {'type': 'audio'}, 'generation_config': {'speech_config': [{'voice': voice}]}}
        for i in range(tries):
            req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/interactions', data=json.dumps(body).encode(),
                                         headers={'x-goog-api-key': KEY, 'Content-Type': 'application/json'})
            try:
                r = json.loads(urllib.request.urlopen(req, timeout=240).read())
                aud = next(c for st in r['steps'] for c in st.get('content', []) if c.get('type') == 'audio')
                open(out, 'wb').write(base64.b64decode(aud['data']))
                import subprocess
                d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out]))
                if d < 0.32 * len(text.split()) and i < tries - 1:   # fin de phrase coupée (déjà vu) : on recommence
                    last = f'{mdl} audio trop court ({d:.1f} s)'; print(last, flush=True); continue
                return out, mdl
            except urllib.error.HTTPError as e:
                last = f'{mdl} {e.code} {e.read().decode()[:300]}'; print(last, flush=True)
                if e.code == 429 and 'per day' in last: break          # quota du jour épuisé : modèle suivant
                if e.code in (429, 500, 503): time.sleep(20 * (i + 1)); continue
                break
    raise SystemExit('voix Gemini indisponible : ' + str(last))

if __name__ == '__main__':
    print(say(sys.argv[1], sys.argv[2], *(sys.argv[3:5])))

def say_timed(text, out, voice='Kore', style='', gap=0.12):
    """Génère phrase par phrase (minutage exact de chaque phrase), puis assemble.
    Renvoie (wav, durée, [(début, fin, mot)]) comme make_tiktok.tts."""
    import re, wave, gem_align
    sents = [x for x in re.split(r'(?<=[.!?])\s+', text.strip()) if x]
    frames, words, t, params = [], [], 0.0, None
    for k, sent in enumerate(sents):
        tmp = out + f'.{k}.wav'; say(sent, tmp, voice, style)
        with wave.open(tmp) as w:
            params = params or w.getparams(); data = w.readframes(w.getnframes()); dur = w.getnframes() / w.getframerate()
        for a, b, wd in gem_align.words_timing(tmp, sent, dur): words.append((t + a, t + b, wd))
        frames.append(data); t += dur
        if k + 1 < len(sents):
            sil = b'\x00' * (int(params.framerate * gap) * params.sampwidth * params.nchannels); frames.append(sil); t += gap
        os.remove(tmp)
    with wave.open(out, 'wb') as w:
        w.setparams(params); w.writeframes(b''.join(frames))
    return out, t, words

def say_aligned(text, out, voice='Kore', style=''):
    """Un seul appel de voix par vidéo (quota gratuit limité), puis calage des sous-titres grâce à une transcription."""
    import wave, gem_align, gem_check
    out, mdl = say(text, out, voice, style)
    with wave.open(out) as w: dur = w.getnframes() / w.getframerate()
    try: chunks = gem_check.transcribe(out)
    except Exception as e: print('transcription impossible', e); chunks = []
    words = gem_align.words_timing_anchored(out, text, dur, chunks) if chunks else gem_align.words_timing(out, text, dur)
    return out, dur, words, mdl
