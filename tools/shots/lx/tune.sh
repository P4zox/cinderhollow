#!/bin/sh
# usage: tune.sh '{"gain":1.4}' [rooms js array]  -> scratchpad/t_<room>.png pairs (top classic, bottom dynamic+shadows)
cd /Users/halstonchen/Claude/cinderhollow
SP=/private/tmp/claude-501/-Users-halstonchen-Claude/d9e70c0e-50d7-4ca2-a3a7-cb024d7c01c1/scratchpad/lx; mkdir -p $SP
sed "s/^const TUNE = .*/const TUNE = ${1:-{\}};/" tools/shots/lx/tune.js > $SP/tune_run.js
[ -n "$2" ] && sed -i '' "s/^const R = .*/const R = $2;/" $SP/tune_run.js
rm -f tools/shots/lx/t/*.png
SHOT_HTML=web/dist/lx.html node tools/shots/shot.js $SP/tune_run.js tools/shots/lx/t | grep -v '^\[\|^\]\|"ok"'
for f in tools/shots/lx/t/t_*_0.png; do b=$(basename $f _0.png); python3 tools/shots/lx/cmp.py tools/shots/lx/t $SP/$b.png ${b}_0 ${b}_2; done

