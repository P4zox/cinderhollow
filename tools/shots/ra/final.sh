#!/bin/sh
# RA regression: walks, mechanics, stress, dormant -> tools/shots/ra/out/*.txt
cd "$(dirname "$0")/../../.."
O=tools/shots/ra/out
for t in walk_ramp walk_cata walk_cath puzzles gaunt trial trial_reset amb vista smoke; do python3 tools/shots/ra/run.py tools/shots/ra/$t.js > $O/$t.txt 2>&1; done
python3 tools/shots/ra/phantom_run.py > $O/phantom.txt 2>&1
SHOT_HTML=web/dist/ra.html node tools/shots/shot.js tools/shots/ra/stress_ra.js $O > $O/stress_ra.txt 2>&1
SHOT_HTML=web/dist/ra.html node tools/shots/shot.js tools/shots/stress.js $O > $O/stress.txt 2>&1
SHOT_HTML=web/dist/ra.html node tools/shots/shot.js tools/shots/dormant_chk.js $O > $O/dormant.txt 2>&1
echo done > $O/final.flag
