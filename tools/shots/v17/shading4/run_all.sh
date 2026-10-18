#!/bin/zsh
# Shading phase 4: every capture for one build.   run_all.sh <html> <prefix: before|after>
# (before = main at ad34746: BUILD_OUT=web/dist/shading4_before.html python3 web/build_web.py on main)
set -e; D=$(cd "$(dirname "$0")" && pwd); H=$1; P=$2; R=$D/../../../..; S1=$D/../shading/shoot.sh; SHOT=$D/../../shot.js
cd "$D"; for s in "" _proto _boss _orbit _storm _stress _off _classic _hard _smooth _toggle; do rm -rf "$P$s"; done
sh "$S1" "$H" "$D/$P" '{}' >/dev/null                                                    # phase-1 spots: every region, vistas (seated), dark, hot
./shoot.sh "$H" "${P}_proto" '{}' >/dev/null                                              # the phase-4 prototype rooms (reflections, particles, shafts, haze, effects)
SHOT_HTML=$H sh "$R/tools/shots/v17/boss/run.sh" "$D/../shading2/boss.js" "$D/${P}_boss" '{"arena":1}' >/dev/null   # the Hearthkeeper, CF8, phases 1 and 3
./orbit.sh "$H" "${P}_orbit" >/dev/null
SHOT_HTML=$H node "$SHOT" "$D/storm.js" "$D/${P}_storm" >/dev/null                        # lightning (+ its reflection in the Spire's puddles)
sh "$S1" "$H" "$D/${P}_stress" '{"bright":2,"bloom":2,"rays":2}' r_ramparts d_catacombs r_lastfield h_forge_hearth r_cathedral >/dev/null
sh "$S1" "$H" "$D/${P}_off" '{"shaders":0}' r_ramparts d_catacombs r_lastfield d_lightsout r_mire r_barrows >/dev/null
sh "$S1" "$H" "$D/${P}_classic" '{"light":0}' r_ramparts d_catacombs r_lastfield r_mire r_barrows >/dev/null
sh "$S1" "$H" "$D/${P}_hard" '{"light":2}' r_dunes d_catacombs r_ramparts r_cathedral >/dev/null
sh "$S1" "$H" "$D/${P}_smooth" '{"lband":1}' d_catacombs d_hermit r_ramparts >/dev/null
if [ "$P" = after ]; then   # the new toggles: the same frame with each new option off (and Light shafts Strong)
  ALT='{"refloff":{"refl":0},"partoff":{"lpart":0},"hazeoff":{"dhaze":0},"raysoff":{"rays":0},"raysstrong":{"rays":2},"alloff":{"refl":0,"lpart":0,"dhaze":0,"rays":0}}' ./shoot.sh "$H" "${P}_toggle" '{}' rf_CF5 rf_M7 rf_HF8 pt_C10m pt_K7m sh_K7 sh_K11 sh_C10 hz_R11 fx_flame >/dev/null
fi
