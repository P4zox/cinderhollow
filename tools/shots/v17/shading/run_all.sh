#!/bin/sh
# Shading phase 1: every capture + montage + table for one build.   run_all.sh <html> <prefix: before|after>
# (run it for both builds; the before build is main at daec1c7: BUILD_OUT=web/dist/shading_before.html python3 web/build_web.py)
set -e; D=$(cd "$(dirname "$0")" && pwd); H=$1; P=$2; R=$D/../../../..
cd "$D"; rm -rf "$P" "${P}_stress" "${P}_off" "${P}_classic" "${P}_hard" "${P}_bright0" "${P}_bright2" "buffers_$P"
./shoot.sh "$H" "$P" '{}' >/dev/null
SHOT_HTML=$H "$R/tools/shots/v17/boss/run.sh" "$D/boss.js" "$D/$P" '{"arena":1}' >/dev/null
./shoot.sh "$H" "${P}_stress" '{"bright":2,"bloom":2,"rays":2}' r_ramparts d_catacombs r_lastfield r_crown h_forge_hearth r_dunes >/dev/null
./shoot.sh "$H" "${P}_off" '{"shaders":0}' r_ramparts d_catacombs r_lastfield d_lightsout >/dev/null
./shoot.sh "$H" "${P}_classic" '{"light":0}' r_ramparts d_catacombs r_lastfield >/dev/null
./shoot.sh "$H" "${P}_hard" '{"light":2}' r_dunes d_catacombs r_ramparts >/dev/null
for b in 0 2; do ./shoot.sh "$H" "${P}_bright$b" "{\"bright\":$b}" r_ramparts d_catacombs r_lastfield r_crimson >/dev/null; done
T=$(mktemp -t buf).js; { echo "window.__dbgD=[2,3,0]; window.__dbgSpots=[['du','DU10',47,22],['cat','C10',26,10],['her','H2',24,8]];"; cat buffers.js; } > "$T"
SHOT_HTML=$H node ../../shot.js "$T" "buffers_$P" >/dev/null; rm -f "$T"
