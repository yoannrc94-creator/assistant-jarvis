"""Minutage approximatif des mots d'un audio Gemini (pas d'horodatage fourni) : on repère les silences,
puis on répartit les mots sur les passages parlés au prorata de leur longueur."""
import re, subprocess, json

def speech_segments(path, total):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', 'silencedetect=noise=-38dB:d=0.16', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    segs, cur = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s - cur > 0.05: segs.append((cur, s))
        cur = e
    if total - cur > 0.05: segs.append((cur, total))
    return segs

def words_timing(path, text, total):
    segs = speech_segments(path, total)
    toks = text.split()
    weights = [len(t) + 2 for t in toks]
    speech = sum(b - a for a, b in segs); per = speech / sum(weights)
    out, si, pos = [], 0, segs[0][0]
    for t, w in zip(toks, weights):
        d = w * per
        if pos >= segs[si][1] - 1e-3 and si + 1 < len(segs): si += 1; pos = segs[si][0]
        a = pos; pos = min(pos + d, segs[si][1]) if si + 1 < len(segs) else pos + d
        out.append((a, pos, t.strip('«»"')))
    return out

def _norm(w):
    import unicodedata
    w = unicodedata.normalize('NFD', w.lower()); return ''.join(ch for ch in w if ch.isalnum() and not unicodedata.combining(ch))

def words_timing_anchored(path, text, total, chunks):
    """chunks = [(début, texte transcrit)] : on cale chaque morceau transcrit sur le texte d'origine
    (comparaison mot à mot tolérante), puis on répartit les mots entre deux repères."""
    import difflib
    toks = text.split(); nt = [_norm(t) for t in toks]
    tw, tstart = [], []
    for st, ch in chunks:
        for j, w in enumerate(ch.split()):
            tw.append(_norm(w)); tstart.append(st if j == 0 else None)
    anchors = {0: 0.0}
    sm = difflib.SequenceMatcher(None, nt, tw, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            if tstart[b + k] is not None: anchors[a + k] = tstart[b + k]
    idx = sorted(anchors); idx.append(len(toks)); times = [anchors[i] for i in idx[:-1]] + [total]
    segs = speech_segments(path, total)
    def speech_between(t0, t1):
        return [(max(a, t0), min(b, t1)) for a, b in segs if b > t0 and a < t1] or [(t0, t1)]
    out = []
    for k in range(len(idx) - 1):
        i0, i1, t0, t1 = idx[k], idx[k + 1], times[k], times[k + 1]
        part = speech_between(t0, t1); sp = sum(b - a for a, b in part)
        ws = [len(x) + 2 for x in toks[i0:i1]]; per = sp / max(1, sum(ws)); si, pos = 0, part[0][0]
        for tok, w in zip(toks[i0:i1], ws):
            d = w * per
            while si + 1 < len(part) and pos >= part[si][1] - 1e-3: si += 1; pos = part[si][0]
            a = pos; pos = pos + d
            out.append((a, min(pos, t1), tok.strip('«»"')))
    return out
