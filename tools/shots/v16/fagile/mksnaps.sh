#!/bin/sh
# usage: tools/shots/v16/fagile/mksnaps.sh <type> <room> <boss> <x> <y> <at-list>   -> out_<type>/ + <type>_boss_sheet.png / <type>_foe_sheet.png
D=$(cd "$(dirname "$0")" && pwd); R=$D/../../../..
T=$1; S=$D/snap_$T.js
printf "window.__type='%s'; window.__arena=['%s','%s',%s,%s]; window.__at=[%s];\n" "$T" "$2" "$3" "$4" "$5" "$6" > $S
cat $D/../fatality/snaps.js >> $S
mkdir -p $D/out_$T; rm -f $D/out_$T/*.png
SHOT_HTML=${SHOT_HTML:-$R/web/dist/v16_fagile.html} sh $R/tools/shots/wm/run.sh $S $D/out_$T > $D/snap_${T}_result.txt 2>&1
python3 $D/../fatality/sheet.py $D/out_$T boss $D/${T}_boss_sheet.png 4
python3 $D/../fatality/sheet.py $D/out_$T foe $D/${T}_foe_sheet.png 4
