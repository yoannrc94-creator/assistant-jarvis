"""Contrôle d'une vidéo finie avant envoi (étape 2 du plan du 18 octobre). Ne modifie aucun fichier.

Usage : python3 verifier_video.py [--histoire] video.mp4 [autres.mp4 ...]
Chaque contrôle donne OK, ALERTE (à regarder) ou ÉCHEC (à corriger avant publication).
Code de sortie : 1 si au moins un ÉCHEC.
"""
import json, os, re, struct, subprocess, sys

HASHTAGS_FIXES = ('#jtdeschatons', '#actu', '#viepratique')

def ffprobe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))

def ffmpeg_log(path, filtres, audio=True):
    """Lance un filtre d'analyse ffmpeg et renvoie son journal (rien n'est écrit sur le disque)."""
    opt = ['-af', filtres, '-vn'] if audio else ['-vf', filtres, '-an']
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, *opt, '-f', 'null', '-'], capture_output=True, text=True)
    return r.stderr

def moov_avant_mdat(path):
    """Démarrage rapide (faststart) : l'index du fichier doit précéder les données."""
    with open(path, 'rb') as f:
        while True:
            h = f.read(8)
            if len(h) < 8: return False
            taille, typ = struct.unpack('>I4s', h)
            if typ == b'moov': return True
            if typ == b'mdat': return False
            if taille == 1: taille = struct.unpack('>Q', f.read(8))[0]; f.seek(taille - 16, 1)
            elif taille == 0: return False
            else: f.seek(taille - 8, 1)

def lire_srt(path):
    def sec(t): h, m, r = t.split(':'); s, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    blocs = []
    for b in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().strip()):
        lignes = b.strip().splitlines()
        if len(lignes) >= 3 and '-->' in lignes[1]:
            a, z = [x.strip() for x in lignes[1].split('-->')]
            blocs.append((sec(a), sec(z), ' '.join(lignes[2:])))
    return blocs

def fichiers_associes(path):
    """JT-chatons-<date>-<créneau>-<présentateur>.mp4 -> sous-titres, description et commentaire du même créneau."""
    m = re.match(r'JT-chatons-\d{4}-\d{2}-\d{2}-(.+)-[^-]+\.mp4$', os.path.basename(path))
    if not m: return None, {}
    slot, d = m.group(1), os.path.dirname(path)
    return slot, {k: os.path.join(d, f'{k}-{slot}.{ext}') for k, ext in (('sous-titres', 'srt'), ('description', 'txt'), ('commentaire', 'txt'))}

def verifier(path, histoire=False):
    res = []
    def note(niveau, quoi, detail): res.append((niveau, quoi, detail))
    info = ffprobe(path)
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    duree = float(info['format']['duration'])

    # 1. Format
    if not v: note('ÉCHEC', 'image', 'aucune piste vidéo'); return res, duree
    taille = f"{v['width']} par {v['height']}"
    note('OK' if (v['width'], v['height']) == (1080, 1920) else 'ÉCHEC', 'format', taille + ' (attendu 1080 par 1920, vertical)')
    num, den = map(int, v['r_frame_rate'].split('/')); fps = num / den
    note('OK' if abs(fps - 30) < 0.01 else 'ÉCHEC', 'images par seconde', f'{fps:g} (attendu 30)')
    ok_codec = v['codec_name'] == 'h264' and v.get('pix_fmt') == 'yuv420p'
    note('OK' if ok_codec else 'ÉCHEC', 'codage vidéo', f"{v['codec_name']}, {v.get('pix_fmt')} (attendu h264, yuv420p)")
    note('OK' if a and a['codec_name'] == 'aac' else 'ÉCHEC', 'piste son', a['codec_name'] if a else 'absente')
    note('OK' if moov_avant_mdat(path) else 'ALERTE', 'démarrage rapide', 'oui' if moov_avant_mdat(path) else 'non, la lecture en ligne démarrera plus lentement')

    # 2. Durée
    if histoire: ok = 66 <= duree <= 70; cible = 'entre 66 et 70 secondes'
    else: ok = duree <= 25; cible = '25 secondes au plus'
    note('OK' if ok else 'ÉCHEC', 'durée', f'{duree:.1f} secondes ({cible})')

    # 3. Son
    if a:
        j = ffmpeg_log(path, 'loudnorm=print_format=json')
        j = json.loads(j[j.rindex('{'):j.rindex('}') + 1])
        lufs, crete = float(j['input_i']), float(j['input_tp'])
        note('OK' if -18 <= lufs <= -10 else 'ALERTE', 'volume moyen', f'{lufs:.1f} LUFS (repère courant : -14, plage acceptée -18 à -10)')
        note('OK' if crete <= -1.0 else 'ALERTE', 'crête du son', f'{crete:.1f} dBTP (au-dessus de -1, risque de grésillement)')
        trous = [(float(x), float(y)) for x, y in re.findall(r'silence_start: ([\d.]+).*?silence_duration: ([\d.]+)',
                 ffmpeg_log(path, 'silencedetect=noise=-45dB:d=0.7'), re.S)]
        trous = [t for t in trous if t[0] > 0.3]
        note('OK' if not trous else 'ALERTE', 'temps morts sonores',
             'aucun' if not trous else ', '.join(f'{t:.1f} s pendant {d:.1f} s' for t, d in trous))

    # 4. Image
    noirs = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', ffmpeg_log(path, 'blackdetect=d=0.3:pix_th=0.08', audio=False))
    note('OK' if not noirs else 'ÉCHEC', 'écran noir', 'aucun' if not noirs else ', '.join(f'de {x} à {y} s' for x, y in noirs))
    figes = re.findall(r'freeze_start: ([\d.]+).*?freeze_duration: ([\d.]+)', ffmpeg_log(path, 'freezedetect=n=0.003:d=1.5', audio=False), re.S)
    note('OK' if not figes else 'ALERTE', 'image figée plus de 1,5 s',
         'aucune' if not figes else ', '.join(f'à {float(x):.1f} s pendant {float(d):.1f} s' for x, d in figes))

    # 5. Fichiers d'accompagnement
    slot, assoc = fichiers_associes(path)
    if slot is None:
        note('ALERTE', 'fichiers associés', 'nom de vidéo inhabituel, sous-titres et description non contrôlés'); return res, duree
    srt = assoc['sous-titres']
    if not os.path.exists(srt): note('ÉCHEC', 'sous-titres', 'fichier absent')
    else:
        blocs = lire_srt(srt)
        fin = max(z for _, z, _ in blocs) if blocs else 0
        note('OK' if blocs and fin <= duree else 'ÉCHEC', 'sous-titres', f'{len(blocs)} phrases, la dernière finit à {fin:.1f} s sur {duree:.1f} s')
        ordre = all(blocs[k][1] <= blocs[k + 1][0] + 0.01 for k in range(len(blocs) - 1))
        note('OK' if ordre else 'ÉCHEC', 'ordre des sous-titres', 'sans chevauchement' if ordre else 'des phrases se chevauchent')
        courts = [k + 1 for k, (x, z, _) in enumerate(blocs) if z - x < 0.8]
        rapides = [k + 1 for k, (x, z, t) in enumerate(blocs) if len(t) / max(0.1, z - x) > 25]
        note('OK' if not courts else 'ALERTE', 'temps de lecture', 'chaque phrase reste au moins 0,8 s' if not courts else f'phrases trop brèves : {courts}')
        note('OK' if not rapides else 'ALERTE', 'vitesse de lecture', 'au plus 25 caractères par seconde' if not rapides else f'phrases trop rapides : {rapides}')
    desc = assoc['description']
    if not os.path.exists(desc): note('ÉCHEC', 'description', 'fichier absent')
    else:
        tags = re.findall(r'#\w+', open(desc, encoding='utf-8').read().lower())
        manque = [h for h in HASHTAGS_FIXES if h not in tags]
        autres = [h for h in tags if h not in HASHTAGS_FIXES]
        if manque: note('ÉCHEC', 'hashtags', 'il manque ' + ', '.join(manque))
        else: note('OK' if len(autres) <= 2 else 'ALERTE', 'hashtags', f'les 3 fixes, plus {len(autres)} de sujet (2 au plus)')
    note('OK' if os.path.exists(assoc['commentaire']) else 'ALERTE', 'commentaire épinglé', 'présent' if os.path.exists(assoc['commentaire']) else 'absent')
    return res, duree

if __name__ == '__main__':
    args = sys.argv[1:]; histoire = '--histoire' in args; args = [x for x in args if x != '--histoire']
    echec_total = 0
    for p in args:
        res, duree = verifier(p, histoire)
        nb = {n: sum(1 for r in res if r[0] == n) for n in ('ÉCHEC', 'ALERTE')}
        echec_total += nb['ÉCHEC']
        print(f"{os.path.basename(p)} : {duree:.1f} secondes, {nb['ÉCHEC']} échec, {nb['ALERTE']} alerte")
        for niveau, quoi, detail in res:
            print(f'  {niveau} {quoi} : {detail}')
        print()
    sys.exit(1 if echec_total else 0)
