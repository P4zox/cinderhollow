#!/bin/sh
# usage: tools/shots/v15/scythe/prev.sh out.png tag tag ...   (rows with the Requiem, hit boxes outlined)
out=$1; shift; args=""
for t in "$@"; do args="$args $t:requiem_scythe"; done
HB=1 python3 art/player_preview.py rows "$out" $args
