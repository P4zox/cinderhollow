#!/bin/sh
# per skill node: the bot matrix (BOSSES x every type x SEEDS) with just that node learned -> <outdir>/<node>.json
# usage: sweep.sh <outdir> [nodes...]   (env BOSSES, SEEDS, O)
D=$(cd "$(dirname "$0")" && pwd); OUT=$1; shift; mkdir -p "$OUT"
NODES=${*:-"none keen_edge heavy_hand fourth_strike measured_cut flowing_form charged_arts sunder executioner blade_dancer crushing_weight tireless relentless quickstep iron_flask riposte_mastery deflect evasive_strike steadfast enduring second_wind ironskin featherfoot light_feet shadowstep bloodthirst open_wounds hemorrhage vein_burst blood_drinker last_stand wrath frenzy blood_price crimson_veil leech crimson_pact"}
export D OUT; export BOSSES=${BOSSES:-'["hound","omen","kalden","champion","bellringer","pharaoh"]'} SEEDS=${SEEDS:-'[1,2]'} O=${O:-'{"secs":180,"retreat":30,"rollToward":true}'}
for n in $NODES; do echo $n; done | xargs -P ${PAR:-6} -n 1 sh -c 'SK=$([ "$0" = none ] && echo "[]" || echo "[\"$0\"]"); OO=$(echo "$O" | sed "s/}\$/,\"skills\":$SK}/"); sh "$D/run.sh" "$D/matrix.js" "$OUT/_$0" "{\"kinds\":$BOSSES,\"seeds\":$SEEDS,\"o\":$OO}" > "$OUT/$0.json" 2>&1; echo "done $0"'
