#!/bin/sh
# usage: shoot.sh <html> <outdir> [settings-json] [shot names...]   world-only captures (snap.js)
D=$(cd "$(dirname "$0")" && pwd); H=$1; O=$2; SET=${3:-'{}'}; shift 3 2>/dev/null
T=$(mktemp -t shade).js
{ echo "window.__shSet = $SET; window.__shTune = ${TUNE:-null}; window.__shTone = ${TONE:-null};"; if [ $# -gt 0 ]; then printf 'window.__shOnly = ['; for n in "$@"; do printf "'%s'," "$n"; done; echo '];'; fi; cat "$D/snap.js"; } > "$T"
SHOT_HTML=$H node "$D/../../shot.js" "$T" "$O"; rm -f "$T"
