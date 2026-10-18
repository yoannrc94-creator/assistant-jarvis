"""Contrôle des images d'un JT avant animation (étape 4 du plan du 18 octobre).

Une planche (une miniature par plan, numérotée) est envoyée une seule fois à Gemini, qui signale
les humains et le texte visible. Rien n'est modifié : le résultat va dans un nouveau fichier JSON.
Ce contrôle ne remplace pas la lecture humaine de la planche.

Usage : python3 verifier_images.py config.json [dossier_de_sortie]
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(D, '.gemini_key')).read().strip()
MODELES = ['gemini-3.8-flash', 'gemini-flash-latest']
PROMPT = (
    "Tu contrôles des images de dessin animé destinées à une vidéo. Chaque vignette porte un numéro en haut à gauche. "
    "Pour chaque numéro, indique : humain (true si on voit une personne, un visage humain, une main ou un bras humain, "
    "une silhouette humaine, même partiellement), texte (true si on voit des lettres, des mots, des chiffres lisibles "
    "ou un logo, sur un panneau, un écran, une feuille ou un objet), et detail (au plus 12 mots). "
    "Réponds uniquement par un tableau JSON : [{\"plan\": 1, \"humain\": false, \"texte\": false, \"detail\": \"...\"}]."
)

def noms(cfg):
    """Noms des images du JT, comme dans make_multi.py."""
    return [(k, f"multi_{cfg['date']}_{cfg['slot']}_{cfg['party']}_s{k}") for k in range(len(cfg['segments']))]

def planche(paires, sortie):
    """Une grille de vignettes 360 px de large, numérotées (les numéros sont ceux des plans, à partir de 1)."""
    try: police = ImageFont.load_default(size=44)
    except TypeError: police = ImageFont.load_default()
    cols = 5; w, h = 360, 640
    lignes = (len(paires) + cols - 1) // cols
    fond = Image.new('RGB', (cols * w, lignes * h), (30, 30, 30))
    for i, (k, chemin) in enumerate(paires):
        im = Image.open(chemin).convert('RGB').resize((w, h))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 90, 60), fill=(0, 0, 0))
        d.text((12, 6), str(k + 1), fill=(255, 255, 0), font=police)
        fond.paste(im, ((i % cols) * w, (i // cols) * h))
    fond.save(sortie, quality=88)
    return sortie

def appeler(image_path):
    """Un seul appel par planche. S'arrête si le quota du jour est épuisé (pas de nouvel essai inutile)."""
    b64 = base64.b64encode(open(image_path, 'rb').read()).decode()
    corps = {'contents': [{'parts': [{'inline_data': {'mime_type': 'image/jpeg', 'data': b64}}, {'text': PROMPT}]}],
             'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0}}
    derniere = None
    for mdl in MODELES:
        req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent',
                                     data=json.dumps(corps).encode(), headers={'x-goog-api-key': KEY, 'Content-Type': 'application/json'})
        try:
            txt = json.loads(urllib.request.urlopen(req, timeout=180).read())['candidates'][0]['content']['parts'][0]['text']
            return mdl, json.loads(txt)
        except urllib.error.HTTPError as e:
            derniere = f'{mdl} {e.code} ' + e.read().decode()[:160]
            if e.code == 429 and 'per day' in derniere: raise SystemExit('QUOTA DU JOUR ATTEINT : ' + derniere[:160])
        except Exception as e:
            derniere = f'{mdl} {type(e).__name__}'
    raise SystemExit('contrôle impossible : ' + str(derniere))

def controler(cfg_path, sortie_dir):
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    paires, absentes = [], []
    for k, nom in noms(cfg):
        p = os.path.join(D, 'img', nom + '.png')
        (paires if os.path.exists(p) else absentes).append((k, p))
    os.makedirs(sortie_dir, exist_ok=True)
    feuille = planche(paires, os.path.join(sortie_dir, f"planche-{cfg['date']}-{cfg['slot']}.jpg"))
    modele, resultats = appeler(feuille)
    par_plan = {int(r['plan']): r for r in resultats}
    rapport = []
    for k, _ in paires:
        r = par_plan.get(k + 1, {'humain': None, 'texte': None, 'detail': 'pas de réponse pour ce plan'})
        if r.get('humain') or r.get('texte'): niveau = 'ÉCHEC'
        elif r.get('humain') is None: niveau = 'ALERTE'
        else: niveau = 'OK'
        rapport.append({'plan': k + 1, 'niveau': niveau, 'humain': r.get('humain'), 'texte': r.get('texte'), 'detail': r.get('detail', '')})
    for k, _ in absentes:
        rapport.append({'plan': k + 1, 'niveau': 'ALERTE', 'detail': 'image absente'})
    rapport.sort(key=lambda x: x['plan'])
    json.dump({'config': os.path.basename(cfg_path), 'modele': modele, 'planche': os.path.basename(feuille), 'plans': rapport},
              open(os.path.join(sortie_dir, f"controle-images-{cfg['date']}-{cfg['slot']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    echecs = [r for r in rapport if r['niveau'] == 'ÉCHEC']
    print(f"{cfg['date']} {cfg['slot']} : {len(rapport)} plans, {len(echecs)} à refaire (modèle {modele})")
    for r in rapport:
        if r['niveau'] != 'OK': print(f"  {r['niveau']} plan {r['plan']} : humain={r.get('humain')} texte={r.get('texte')} ({r.get('detail', '')})")
    return rapport

if __name__ == '__main__':
    controler(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(D, 'controle-images'))
