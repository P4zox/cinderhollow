#!/bin/sh
# usage: tools/shots/v17/boss/run.sh <test.js> [outdir] [args-json]   (SHOT_HTML defaults to web/dist/v17_boss.html)
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -t hktest).js
{ echo "const ARGS = ${3:-null} || {};"; cat "$D/_lib.js" "$1"; } > "$T"
SHOT_HTML=${SHOT_HTML:-$D/../../../../web/dist/v17_boss.html} node "$D/../../shot.js" "$T" "${2:-$D/out}"; rm -f "$T"
