#!/bin/sh
# usage: tools/shots/wb/run_bench.sh <html> <out.json> [secs] [far] [js prelude]
# runs bench_real.js with options prepended; writes the JSON result
H=$1; O=$2; SECS=${3:-60}; FAR=${4:-12}; PRE=${5:-}
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -t wbbench).js
{ echo "const BENCH_SECS = $SECS, FAR_SECS = $FAR; $PRE"; cat "$D/bench_real.js"; } > "$T"
cd "$D/.." && SHOT_HTML="$H" node shot.js "$T" "$D/out" > "$O.raw" 2>&1
python3 - "$O.raw" "$O" <<'PY'
import sys, json
raw = open(sys.argv[1]).read(); i = raw.index('{'); j = raw.rindex('}')
d = json.loads(raw[i:j+1]); json.dump(d, open(sys.argv[2], 'w'), indent=1)
if 'ERRORS' in raw: print(raw[raw.index('ERRORS'):][:2000])
print(len(d), 'weapons')
PY
rm -f "$T"
