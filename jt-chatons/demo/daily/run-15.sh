cd "$(dirname "$0")/.."
for s in matin midi soir; do timeout 3000 python3 make_daily.py daily/config-2026-10-15-$s.json > daily/log-15-$s.txt 2>&1; echo "FIN $s" >> daily/log-15-$s.txt; done
