#!/bin/sh
# usage: shoot.sh <html> <outdir> [settings-json] [shot names...]   world-only captures (snap.js)
# env: ALT='{"refloff":{"refl":0}}' (same frame, other settings)  TUNE (LX_TUNE)  NTUNE (LXN_TUNE)  TUNE4 (LX4_TUNE)  DBG='[11]'  SPOTS='[[...]]'
D=$(cd "$(dirname "$0")" && pwd); H=$1; O=$2; SET=${3:-'{}'}; shift 3 2>/dev/null
T=$(mktemp -t shade4).js
{ echo "window.__shSet = $SET; window.__shTune = ${TUNE:-null}; window.__shNTune = ${NTUNE:-null}; window.__sh4Tune = ${TUNE4:-null}; window.__shDbg = ${DBG:-null}; window.__shSpots = ${SPOTS:-null}; window.__shAlt = ${ALT:-null};"; if [ $# -gt 0 ]; then printf 'window.__shOnly = ['; for n in "$@"; do printf "'%s'," "$n"; done; echo '];'; fi; cat "$D/snap.js"; } > "$T"
SHOT_HTML=$H node "$D/../../shot.js" "$T" "$O"; rm -f "$T"
