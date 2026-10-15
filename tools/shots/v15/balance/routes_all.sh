#!/bin/sh
# every v14 route suite + wm/mech.js on SHOT_HTML; prints pass/n and the BAD lines. usage: routes_all.sh [outdir]
cd "$(dirname "$0")/../../../.."; H=${SHOT_HTML:-web/dist/v15_balance.html}; O=${1:-/tmp/routes15}; mkdir -p $O
for t in blade heavy guard dual reach; do (SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/v14/$t/routes.js $O/$t > $O/$t.json 2>&1) & done
(SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/wm/mech.js $O/mech > $O/mech.json 2>&1) &
wait
for t in saxe bow fist scythe bell; do (SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/v15/$t/routes.js $O/$t > $O/$t.json 2>&1) & done
wait
for t in blade heavy guard dual reach mech saxe bow fist scythe bell; do printf "%-6s " $t; python3 "$(pwd)/tools/shots/v15/balance/routes_parse.py" $O/$t.json; done
