#!/bin/bash
cd /tmp/claude-0/-home-user-assistant-jarvis/45b2ce9a-ba2b-5f9f-98c9-bdcc4dc5d6fd/scratchpad/demo
M=make_multi.py
for s in matin midi soir; do
  NO_GEMINI=1 python3 "$M" "daily/multi-2026-10-16-$s.json" > "run4-16-$s.log" 2>&1
  echo "FIN_PROCESSUS $s $?" >> "run4-16-$s.log"
  ffprobe -v error -show_entries format=duration -of csv=p=0 "daily/2026-10-16/JT-chatons-2026-10-16-$s-jt.mp4" > "duree4-16-$s.txt" 2>/dev/null
  cp tk_voice900.wav "tk_voice900-16-$s-v4.wav" 2>/dev/null
done
echo CHAINE4_FIN > run4-16-fin.log
