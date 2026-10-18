#!/bin/bash
cd /tmp/claude-0/-home-user-assistant-jarvis/45b2ce9a-ba2b-5f9f-98c9-bdcc4dc5d6fd/scratchpad/demo
# arrêter les anciennes chaînes et fabrications (par identifiant de processus)
for p in $(pgrep -f "[r]un3-16-") $(pgrep -f "[p]ython3 make_multi"); do
  [ "$p" != "$$" ] && kill "$p" 2>/dev/null
done
sleep 3
# fin courte pour les trois JT
python3 - <<'PY'
import json
for slot in ("matin", "midi", "soir"):
    p = f"daily/multi-2026-10-16-{slot}.json"
    cfg = json.load(open(p, encoding="utf-8"))
    cfg["fin_voix"] = "C'était le JT des chatons."
    cfg["fin_cache"] = "gem_signature_jt_court.wav"
    json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(slot, "fin ok")
PY
nohup bash relance4chain.sh > /dev/null 2>&1 &
echo "relance 4 lancée"
