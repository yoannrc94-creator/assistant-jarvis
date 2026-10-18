"""Transcrit un audio avec Gemini : renvoie [(début_s, phrase)] pour vérifier et caler les sous-titres."""
import base64, json, os, re, urllib.request
KEY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.gemini_key')).read().strip()
def transcribe(path):
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    body = {'contents': [{'parts': [{'inline_data': {'mime_type': 'audio/wav', 'data': b64}},
            {'text': "Transcris cet audio en français, mot pour mot. Une ligne par phrase ou groupe de mots entre deux pauses, au format : début_en_secondes | texte. Rien d'autre."}]}]}
    import time
    txt, err = None, None
    for k in range(8):
        mdl = ['gemini-3.8-flash', 'gemini-flash-latest'][k % 2]
        req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent',
                                     data=json.dumps(body).encode(), headers={'x-goog-api-key': KEY, 'Content-Type': 'application/json'})
        try:
            txt = json.loads(urllib.request.urlopen(req, timeout=180).read())['candidates'][0]['content']['parts'][0]['text']; break
        except Exception as e:
            err = e; time.sleep(8 * (k + 1))
    if txt is None: raise RuntimeError(f'transcription impossible : {err}')
    return [(float(a), b.strip()) for a, b in re.findall(r'(\d+(?:[.,]\d+)?)\s*\|\s*(.+)', txt)]
if __name__ == '__main__':
    import sys
    for a, b in transcribe(sys.argv[1]): print(a, '|', b)
