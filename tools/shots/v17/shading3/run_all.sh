#!/bin/sh
# Shading phase 3: every capture for one build.   run_all.sh <html> <prefix: before|after>
# (before = main at 1286646: BUILD_OUT=web/dist/shading3_before.html python3 web/build_web.py on main)
set -e; D=$(cd "$(dirname "$0")" && pwd); H=$1; P=$2; R=$D/../../../..; S1=$D/../shading/shoot.sh; SHOT=$D/../../shot.js
cd "$D"; for s in "" _proto _boss _orbit _storm _expo _stress _off _classic _hard _smooth _toggle; do rm -rf "$P$s"; done
sh "$S1" "$H" "$D/$P" '{}' >/dev/null                                                    # phase-1 spots: every region, vistas (seated), dark, hot
./shoot.sh "$H" "${P}_proto" '{}' >/dev/null                                              # the prototype rooms with their foes
SHOT_HTML=$H sh "$R/tools/shots/v17/boss/run.sh" "$D/../shading2/boss.js" "$D/${P}_boss" '{"arena":1}' >/dev/null   # the Hearthkeeper, CF8, phases 1 and 3
./orbit.sh "$H" "${P}_orbit" >/dev/null
SHOT_HTML=$H node "$SHOT" "$D/storm.js" "$D/${P}_storm" >/dev/null
SHOT_HTML=$H node "$SHOT" "$D/expo.js" "$D/${P}_expo" > "$D/${P}_expo.txt"
sh "$S1" "$H" "$D/${P}_stress" '{"bright":2,"bloom":2,"rays":2}' r_ramparts d_catacombs r_lastfield h_forge_hearth >/dev/null
sh "$S1" "$H" "$D/${P}_off" '{"shaders":0}' r_ramparts d_catacombs r_lastfield d_lightsout >/dev/null
sh "$S1" "$H" "$D/${P}_classic" '{"light":0}' r_ramparts d_catacombs r_lastfield >/dev/null
sh "$S1" "$H" "$D/${P}_hard" '{"light":2}' r_dunes d_catacombs r_ramparts >/dev/null
sh "$S1" "$H" "$D/${P}_smooth" '{"lband":1}' d_catacombs d_hermit r_ramparts >/dev/null
if [ "$P" = after ]; then   # the new toggles: the same frame with each new option off / partly on
  ALT='{"cshoff":{"csh":0},"cshcon":{"csh":1},"matoff":{"mat":0}}' ./shoot.sh "$H" "${P}_toggle" '{}' p_cat_lamp p_ramparts p_C8 p_forge p_deep >/dev/null
fi
