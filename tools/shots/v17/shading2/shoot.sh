#!/bin/sh
# usage: shoot.sh <html> <outdir> [settings-json] [shot names...]   world-only captures (snap.js)
# env: ALT='{"surfoff":{"surf":0,"rim":0}}' (same frame, other settings)  TUNE='{"sk":0.8}' (LX_TUNE)  NTUNE='{"inner":0.4}' (LXN_TUNE)  DBG='[8]' (debug views)  SPOTS='[[...]]'
D=$(cd "$(dirname "$0")" && pwd); H=$1; O=$2; SET=${3:-'{}'}; shift 3 2>/dev/null
T=$(mktemp -t shade2).js
{ echo "window.__shSet = $SET; window.__shTune = ${TUNE:-null}; window.__shNTune = ${NTUNE:-null}; window.__shDbg = ${DBG:-null}; window.__shSpots = ${SPOTS:-null}; window.__shAlt = ${ALT:-null};"; if [ $# -gt 0 ]; then printf 'window.__shOnly = ['; for n in "$@"; do printf "'%s'," "$n"; done; echo '];'; fi; cat "$D/snap.js"; } > "$T"
SHOT_HTML=$H node "$D/../../shot.js" "$T" "$O"; rm -f "$T"
