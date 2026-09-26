#!/bin/sh
# Private build for agent N: the real web/src minus other agents' in-progress region files (they can break boot mid-edit).
# NV_EXCLUDE (space separated basenames) overrides the default exclusion list. Output: web/dist/n.html
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
T=/private/tmp/claude-501/nbuild
rm -rf "$T"; mkdir -p "$T/web/src"
ln -s "$ROOT/assets" "$T/assets"; ln -s "$ROOT/tools" "$T/tools"
cp "$ROOT/web/build_web.py" "$T/web/"; ln -s "$ROOT/web/shell.html" "$T/web/shell.html"
[ -d "$ROOT/web/.pngcache" ] && ln -s "$ROOT/web/.pngcache" "$T/web/.pngcache"
EX=${NV_EXCLUDE-"30_thornveil.js 32_crimson.js 34_dunes.js 35_starfall.js 36_neohallow.js 37_venn.js"}
for f in "$ROOT"/web/src/*.js; do
  b=$(basename "$f"); skip=0
  for e in $EX; do [ "$b" = "$e" ] && skip=1; done
  [ $skip = 0 ] && ln -s "$f" "$T/web/src/$b"
done
cd "$T" && BUILD_OUT="$ROOT/web/dist/n.html" python3 web/build_web.py | grep -E "wrote |Error"
