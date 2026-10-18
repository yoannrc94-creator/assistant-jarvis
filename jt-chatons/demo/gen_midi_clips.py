import json, os, sys
DEMO = os.path.dirname(os.path.abspath(__file__))
os.chdir(DEMO); sys.path.insert(0, DEMO)
import make_multi as mm, make_daily as md
cfg = json.load(open("daily/multi-2026-10-16-midi.json", encoding="utf-8"))
p = md.PARTIES.get("jt") or dict(cat="ginger tabby", col="navy")
for k, seg in enumerate(cfg["segments"]):
    name = f"multi_{cfg['date']}_{cfg['slot']}_{cfg['party']}_s{k}"
    c = mm.make_scene_clip(name, p, seg, int(cfg.get("clip_seconds", 4)))
    print(k, name, "OK" if c else "ZOOM", flush=True)
print("CLIPS_FIN", flush=True)
