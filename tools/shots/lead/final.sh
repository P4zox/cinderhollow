#!/bin/bash
# Lead's final world check: validation, build, edges, phantom damage, all-room sweep, stress, bosses, controls.
cd "$(dirname "$0")/../../.." || exit 1
set -o pipefail
echo "== validate (STRICT, full reach)"; STRICT=1 python3 tools/rooms.py 2>&1 | grep -E "^(ERR|WARN)|wrote" | tail -12
echo "== build"; python3 web/build_web.py 2>&1 | tail -1
python3 tools/shots/lead/gen_edges.py
python3 - <<'PY'
import re,json
s=open('web/src/02_rooms.js').read(); out=[]; spots=[]
for m in re.finditer(r'\{ \.\.\.(\{.*?\}), map: \[(.*?)\] \}', s, re.S):
    d=json.loads(m.group(1))
    if d.get('test'): continue
    rows=[json.loads('"%s"'%r) for r in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))]
    h=len(rows); w=len(rows[0]); cand=[]; best=None
    for y in range(2,h-1):
        for x in range(2,w-2):
            if rows[y][x]=='.' and rows[y-1][x]=='.' and rows[y+1][x] in '#=':
                dd=abs(x-w/2)+abs(y-h/2)
                if best is None or dd<best[0]: best=(dd,x,y)
            if not d.get('boss') and all(rows[y-k][x+dx]=='.' for k in (0,1,2) for dx in (-1,0,1)) and all(rows[y+1][x+dx]=='#' for dx in (-1,0,1)): cand.append((x,y))
    if best: spots.append([d['id'],best[1],best[2]])
    if cand: out.append([d['id'],[cand[0],cand[len(cand)//2],cand[-1]]])
json.dump(out,open('tools/shots/lead/safespots.json','w')); json.dump(spots,open('tools/shots/lead/allspots.json','w'))
print(len(out),'phantom rooms,',len(spots),'sweep rooms')
PY
node -e "
const fs=require('fs'),L='tools/shots/lead/';
const chunk=(tpl,key,data,n,name)=>{const arr=JSON.parse(fs.readFileSync(L+data,'utf8'));const sz=Math.ceil(arr.length/n);for(let i=0;i<n;i++)fs.writeFileSync(L+name+i+'.js',fs.readFileSync(L+tpl,'utf8').replace(key,JSON.stringify(arr.slice(i*sz,(i+1)*sz))));};
chunk('edges.js','TESTS','edges.json',3,'edges_p');chunk('phantom.js','SPOTS','safespots.json',3,'phantom_p');chunk('allrooms.js','SPOTS','allspots.json',2,'allrooms_p');"
cd tools/shots; mkdir -p lead/logs; rm -f lead/logs/*.log
# everything at once, each test in its own headless browser
for t in lead/edges_p0.js lead/edges_p1.js lead/edges_p2.js lead/phantom_p0.js lead/phantom_p1.js lead/phantom_p2.js lead/allrooms_p0.js lead/allrooms_p1.js stress.js dormant_chk.js v19_test.js keys_test.js air_test.js; do
  n=$(basename $t .js); node shot.js $t lead/out > lead/logs/$n.log 2>&1 &
done
wait
for f in lead/logs/*.log; do echo "== $(basename $f .log)"; grep -v '^ *"OK' $f | tail -40; done
