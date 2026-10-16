#!/bin/sh
# fblade contact sheets: sh tools/shots/v16/fblade/snap_all.sh  (SHOT_HTML defaults to web/dist/v16_fblade.html)
cd "$(dirname "$0")/../../../.." || exit 1
export SHOT_HTML=${SHOT_HTML:-web/dist/v16_fblade.html}
D=tools/shots/v16/fblade; S=$D/snapsrc; mkdir -p $S $D/snaps
one() {  # name type arena prep at
  echo "window.__type='$2'; window.__arena=$3; window.__prep=$4; window.__at=$5;" > $S/$1.js
  cat $D/snaps.js >> $S/$1.js
  rm -f $D/snaps/$1/*.png; sh tools/shots/wm/run.sh $S/$1.js $D/snaps/$1 > $D/snaps/$1.txt 2>&1
  python3 tools/shots/v16/fatality/sheet.py $D/snaps/$1 boss $D/${1}_boss_sheet.png
  python3 tools/shots/v16/fatality/sheet.py $D/snaps/$1 foe $D/${1}_foe_sheet.png
}
one kt katana "['K4','omen',6,10]" "null" "[150,290,310,340,420,600,700,900,1000,1040,1150,1300,1440,1490]"
one sx saxe "['TV8','warden',5,10]" "'P.sxG = 55'" "[120,285,330,450,520,610,700,860,1100,1160,1200,1260,1400,1640]"
one sxa saxe "['HF7','twins',4,13]" "'sxSetAxe(true); P.sxG = 70'" "[100,240,290,450,560,620,800,1100,1155,1200,1300,1450,1600,1690]"
one scy scythe "['NV5','executioners',30,10]" "'P.scySouls = 0'" "[120,240,295,420,560,600,640,700,760,900,1100,1300,1450,1580]"
