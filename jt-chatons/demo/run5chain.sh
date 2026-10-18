#!/bin/bash
cd /tmp/claude-0/-home-user-assistant-jarvis/45b2ce9a-ba2b-5f9f-98c9-bdcc4dc5d6fd/scratchpad/demo
for s in midi soir; do
  NO_GEMINI=1 python3 make_multi.py "daily/multi-2026-10-16-$s.json" > "run5-16-$s.log" 2>&1
  echo "FIN $s $?" >> run5-16-fin.log
done
echo CHAINE5_FIN >> run5-16-fin.log
