import base64, io, json, os, sys, time, urllib.request, urllib.error
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(D, '.agnes_key')).read().strip()
MODEL = 'agnes-video-2.5-flash'
def call(method, url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method=method,
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    try:
        return 200, json.loads(urllib.request.urlopen(req, timeout=120).read())
    except urllib.error.HTTPError as e:
        t = e.read().decode()
        try: return e.code, json.loads(t)
        except Exception: return e.code, {'raw': t[:300]}
def data_uri(name, w=720):
    im = Image.open(os.path.join(D, 'img', name + '.png')).convert('RGB')
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=88)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
def create(prompt, first_frame=None, seconds='5', ratio='9:16'):
    body = {'model': MODEL, 'prompt': prompt, 'seconds': str(seconds), 'size': '720P', 'n': 1}
    if first_frame: body.update(mode='keyframe', first_frame=first_frame)
    else: body.update(mode='text', aspect_ratio=ratio)
    return call('POST', 'https://apihub.agnes-ai.com/v1/videos', body)
def status(vid):
    return call('GET', f'https://apihub.agnes-ai.com/agnesapi?video_id={vid}&model_name={MODEL}')
if __name__ == '__main__':
    code, r = create('The kitten news anchor blinks, tilts its head and talks to the camera, small paw gestures, gentle camera push-in.', data_uri('v_anchor'), 5)
    print(code, json.dumps(r)[:500])
