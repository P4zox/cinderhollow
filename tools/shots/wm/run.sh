#!/bin/sh
# usage: tools/shots/wm/run.sh <test.js> [outdir]   (SHOT_HTML defaults to web/dist/wm.html)
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -t wmtest).js
cat "$D/_prelude.js" "$1" > "$T"
SHOT_HTML=${SHOT_HTML:-$D/../../../web/dist/wm.html} node "$D/../shot.js" "$T" "${2:-$D/out}"; rm -f "$T"
