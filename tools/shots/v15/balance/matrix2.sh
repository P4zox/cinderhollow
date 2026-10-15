#!/bin/sh
# like matrix.sh, but limited to some types: TYPES='["sns","spear"]' sh matrix2.sh <outdir> '<o>' '<seeds>' kinds...
D=$(cd "$(dirname "$0")" && pwd); OUT=$1; O=${2:-'{}'}; S=${3:-'[1,2]'}; shift 3 2>/dev/null
mkdir -p "$OUT"; TY=${TYPES:-null}
KINDS=${*:-"hound oswin coven warden omen vessel kalden librarian unwritten ferryman choir champion ice_warden twins butler sanguine executioners vael bellringer cindervane overseer colossus scarab pharaoh orrery astrel enforcer saint0 sentinels sovereign first_ember venn"}
export D OUT O S TY
for k in $KINDS; do echo $k; done | xargs -P ${PAR:-4} -n 1 sh -c 'sh "$D/run.sh" "$D/matrix.js" "$OUT/_$0" "{\"kinds\":[\"$0\"],\"types\":$TY,\"seeds\":$S,\"o\":$O}" > "$OUT/$0.json" 2>&1; echo "done $0"'
