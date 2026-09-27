#!/bin/bash
# usage: tools/shots/sc/look.sh prefix 'SF10,12,11' 'SF16,5,10,tag' ...
cd "$(dirname "$0")/../../.."
pre=$1; shift
js="const SPOTS = ["
for s in "$@"; do IFS=, read r x y t <<< "$s"; js+="['$r',$x,$y,'${pre}_${t:-$r}'],"; done
js+="];"
echo "$js" > tools/shots/sc/_look.js; cat tools/shots/sc/look.js >> tools/shots/sc/_look.js
SHOT_HTML=web/dist/sc.html node tools/shots/shot.js tools/shots/sc/_look.js tools/shots/sc/out 2>&1 | tail -40
