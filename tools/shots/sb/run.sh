#!/bin/sh
# usage: tools/shots/sb/run.sh <test.js> [outdir]   (prepends prelude.js)
D=$(cd "$(dirname "$0")" && pwd); mkdir -p "$D/tmp"; T="$D/tmp/run_$$.js"
O=${2:-$D/out}; mkdir -p "$O"; O=$(cd "$O" && pwd)
cat "$D/prelude.js" "$1" > "$T"
cd "$D/../../.." && SHOT_HTML=${SHOT_HTML:-web/dist/sb.html} node ${RUNNER:-tools/shots/shot.js} "$T" "$O"; rm -f "$T"
