#!/bin/sh
# usage: matrix.sh <outdir> '<o json>' '<seeds json>' [kinds...]   one process per boss, 4 at a time; each writes <outdir>/<kind>.json
D=$(cd "$(dirname "$0")" && pwd); OUT=$1; O=${2:-'{}'}; S=${3:-'[1,2]'}; shift 3 2>/dev/null
mkdir -p "$OUT"
KINDS=${*:-"hound oswin coven warden omen vessel kalden librarian unwritten ferryman choir champion ice_warden twins butler sanguine executioners vael bellringer cindervane overseer colossus scarab pharaoh orrery astrel enforcer saint0 sentinels sovereign first_ember venn"}
export D OUT O S
for k in $KINDS; do echo $k; done | xargs -P ${PAR:-4} -n 1 sh -c 'sh "$D/run.sh" "$D/matrix.js" "$OUT/_$0" "{\"kinds\":[\"$0\"],\"seeds\":$S,\"o\":$O}" > "$OUT/$0.json" 2>&1; echo "done $0"'
