#!/bin/bash
# headless walk-through of every SC wing (no teleporting inside a wing): prints each wing's room-change log
cd "$(dirname "$0")/../../.."
for w in sf nh e h; do
  cat tools/shots/sc/pilot.js tools/shots/sc/walk_pre.js tools/shots/sc/walk_$w.js > tools/shots/sc/_run_walk_$w.js
  echo "=== wing $w"; SHOT_HTML=${SHOT_HTML:-web/dist/sc.html} node tools/shots/shot.js tools/shots/sc/_run_walk_$w.js tools/shots/sc/out 2>&1 | tr -d '\n' | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print('\n'.join(d['rooms'])); print('problems:', [l for l in d['log'] if 'EXPECTED' in l or 'FAILED into' in l] or 'none')"
done
