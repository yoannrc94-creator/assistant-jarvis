import json, sys, time, urllib.request, os
KEY = open(os.path.join(os.path.dirname(__file__), '.agnes_key')).read().strip()
def gen(name, prompt, size='2K', ratio='16:9', tries=6):
    body = json.dumps({'model': 'agnes-image-2.5-flash', 'prompt': prompt, 'size': size, 'ratio': ratio,
                       'extra_body': {'response_format': 'url'}}).encode()
    for i in range(tries):
        req = urllib.request.Request('https://apihub.agnes-ai.com/v1/images/generations', data=body,
                                     headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=300).read())
            d = r['data'][0]
            out = os.path.join(os.path.dirname(__file__), 'img', name + '.png')
            if d.get('url'):
                urllib.request.urlretrieve(d['url'], out)
            else:
                import base64; open(out, 'wb').write(base64.b64decode(d['b64_json']))
            print('OK', name, out, flush=True); return out
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:200]; print('HTTP', e.code, name, msg, flush=True)
            if e.code in (429, 500, 502, 503, 504): time.sleep(20 * (i + 1)); continue
            raise
    raise SystemExit('échec ' + name)
if __name__ == '__main__':
    gen(sys.argv[1], sys.argv[2])
