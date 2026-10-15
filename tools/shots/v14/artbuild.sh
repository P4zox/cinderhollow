#!/bin/sh
# Full player-sheet build (assets/player* + wpn_*), one at a time across agents (mkdir lock). Usage: tools/shots/v14/artbuild.sh
cd "$(dirname "$0")/../../.." || exit 1
L=/tmp/cinderhollow_artbuild.lock
n=0; until mkdir "$L" 2>/dev/null; do n=$((n+1)); [ $n -gt 360 ] && { echo "lock wait timeout ($L)"; exit 1; }; sleep 5; done
trap 'rmdir "$L"' EXIT INT TERM
python3 art/gen_player.py
