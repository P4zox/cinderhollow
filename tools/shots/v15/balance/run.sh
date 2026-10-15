#!/bin/sh
# usage: tools/shots/v15/balance/run.sh <test.js> [outdir] [args-json]   (SHOT_HTML defaults to web/dist/v15_balance.html)
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -t bbtest).js
{ echo "const ARGS = ${3:-null} || {};"; cat "$D/bot_lib.js" "$1"; } > "$T"
SHOT_HTML=${SHOT_HTML:-$D/../../../../web/dist/v15_balance.html} node "$D/../../shot.js" "$T" "${2:-$D/out}"; rm -f "$T"
