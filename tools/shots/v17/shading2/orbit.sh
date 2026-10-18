#!/bin/sh
# usage: orbit.sh <html> <outdir> [settings-json]   (TUNE / NTUNE env as in shoot.sh)
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -t orbit).js; SET=${3:-'{}'}
{ echo "window.__shSet = $SET; window.__shTune = ${TUNE:-null}; window.__shNTune = ${NTUNE:-null}; window.__shDbg = ${DBG:-null};"; cat "$D/orbit.js"; } > "$T"
SHOT_HTML=$1 node "$D/../../shot.js" "$T" "$2"; rm -f "$T"
