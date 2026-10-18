#!/bin/sh
# Shading phase 2: every capture for one build.   run_all.sh <html> <prefix: before|after>
# (before = main at 08d2a1c: git stash / worktree, BUILD_OUT=web/dist/shading2_before.html python3 web/build_web.py)
set -e; D=$(cd "$(dirname "$0")" && pwd); H=$1; P=$2; R=$D/../../../..; S1=$D/../shading/shoot.sh
cd "$D"; for s in "" _foes _stress _off _classic _hard _smooth _dith _bright0 _bright2 _toggle _boss _orbit; do rm -rf "$P$s"; done
sh "$S1" "$H" "$D/$P" '{}' >/dev/null                                                     # phase-1 spots: every region, vistas, dark, hot
./shoot.sh "$H" "${P}_foes" '{}' >/dev/null                                                # prototype rooms with their foes in frame
SHOT_HTML=$H sh "$R/tools/shots/v17/boss/run.sh" "$D/boss.js" "$D/${P}_boss" '{"arena":1}' >/dev/null
./orbit.sh "$H" "${P}_orbit" >/dev/null
sh "$S1" "$H" "$D/${P}_stress" '{"bright":2,"bloom":2,"rays":2}' r_ramparts d_catacombs r_lastfield r_crown h_forge_hearth r_dunes >/dev/null
sh "$S1" "$H" "$D/${P}_off" '{"shaders":0}' r_ramparts d_catacombs r_lastfield d_lightsout >/dev/null
sh "$S1" "$H" "$D/${P}_classic" '{"light":0}' r_ramparts d_catacombs r_lastfield >/dev/null
sh "$S1" "$H" "$D/${P}_hard" '{"light":2}' r_dunes d_catacombs r_ramparts >/dev/null
sh "$S1" "$H" "$D/${P}_smooth" '{"lband":1}' d_catacombs d_hermit r_ramparts >/dev/null
sh "$S1" "$H" "$D/${P}_dith" '{"lband":2}' d_catacombs d_hermit r_ramparts >/dev/null
for b in 0 2; do sh "$S1" "$H" "$D/${P}_bright$b" "{\"bright\":$b}" r_ramparts d_catacombs r_lastfield r_crimson >/dev/null; done
if [ "$P" = after ]; then   # the new toggles (the before build has neither): the same frame with surface lighting / rim off
  ALT='{"surfoff":{"surf":0,"rim":0},"rimoff":{"rim":0}}' ./shoot.sh "$H" "${P}_toggle" '{}' p_cat_lamp p_ramparts p_C8 p_deep p_X11 >/dev/null
fi
