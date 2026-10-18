#!/bin/bash
# Attend les clips Agnes puis monte la vidéo automatiquement.
cd "$(dirname "$0")"
MINUTES=${MINUTES:-115} python3 vid_worker.py >> vid.log 2>&1
n=$(ls clips/*.mp4 2>/dev/null | wc -l)
echo "$(date +%H:%M:%S) clips disponibles : $n/8" >> vid.log
if [ "$n" -gt 0 ]; then OUT_NAME=JT-des-chatons-anime.mp4 python3 make_tiktok.py >> vid.log 2>&1; fi
echo "$(date +%H:%M:%S) RUN_ALL FINI ($n clips)" >> vid.log
