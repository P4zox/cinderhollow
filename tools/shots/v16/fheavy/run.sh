#!/bin/sh
# fheavy tests. usage: sh tools/shots/v16/fheavy/run.sh <arenas|foes|snaps> [type] [arena-json]   (from the repo root)
# SHOT_HTML defaults to web/dist/v16_fheavy.html
cd "$(dirname "$0")/../../../.." || exit 1
export SHOT_HTML=${SHOT_HTML:-web/dist/v16_fheavy.html}
D=tools/shots/v16/fheavy; F=tools/shots/v16/fatality; T=$(mktemp -t fheavy).js
case "$1" in
  arenas)  # real boss arenas incl. multi-body (executioners, twins, sentinels)
    printf "window.__type = '%s'; window.__cases = %s;\n" "$2" "${3:-[['K4','omen',6,10],['NV5','executioners',30,10],['SP5','bellringer',3,10],['HF7','twins',4,13],['M5','kalden',6,10]]}" > "$T"
    cat $F/arenas.js >> "$T"; sh tools/shots/wm/run.sh "$T" $D/out ;;
  foes)
    cat $D/foes.js > "$T"; sh tools/shots/wm/run.sh "$T" $D/out ;;
  snaps)   # contact-sheet snapshots: $2 type, $3 arena json, $4 at list
    printf "Math.random = (() => { let s = 11; return () => (s = (s * 16807) %% 2147483647) / 2147483647; })();\nwindow.__type = '%s'; window.__arena = %s; window.__at = %s; window.__foe = '%s';\n" "$2" "${3:-['K4','omen',6,10]}" "${4:-null}" "${5:-hollow_soldier}" > "$T"
    cat $F/snaps.js >> "$T"; sh tools/shots/wm/run.sh "$T" $D/snaps_$2$6 ;;
esac
rm -f "$T"
