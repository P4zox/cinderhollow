#!/bin/sh
# v15 platform: build a test page and run the platform tests, the ws/* type-system tests and the v14 route tests.
# usage: sh tools/shots/v15/platform/run_all.sh   (from the repo root; outputs + logs in tools/shots/v15/platform/out/)
cd "$(dirname "$0")/../../../.." || exit 1
H=web/dist/v15_platform.html; O=tools/shots/v15/platform/out; mkdir -p $O
BUILD_OUT=$H python3 web/build_web.py | tail -1
run() { echo "== $1: $(grep -cE '"(OK|PASS)' $O/$2.log) ok, $(grep -cE '"(FAIL|BAD)' $O/$2.log) fail $(grep -q ERRORS $O/$2.log && echo '(page errors!)')"; }
SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/v15/platform/types.js $O/types > $O/types.log 2>&1 & 
SHOT_HTML=$H node tools/shots/shot.js tools/shots/v15/platform/ui.js $O/ui > $O/ui.log 2>&1 &
SHOT_HTML=$H node tools/shots/shot.js tools/shots/v15/platform/saves.js $O/saves > $O/saves.log 2>&1 &
for t in loot mastery migration select skilltree switching; do SHOT_HTML=$H node tools/shots/shot.js tools/shots/ws/$t.js $O/ws_$t > $O/ws_$t.log 2>&1 & done
wait
for g in blade dual guard heavy reach; do SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/v14/$g/routes.js $O/v14_$g > $O/v14_$g.log 2>&1 & done
SHOT_HTML=$H sh tools/shots/wm/run.sh tools/shots/wm/mech.js $O/wm_mech > $O/wm_mech.log 2>&1 &
wait
for t in types ui saves ws_loot ws_mastery ws_migration ws_select ws_skilltree ws_switching v14_blade v14_dual v14_guard v14_heavy v14_reach wm_mech; do run $t $t; done
