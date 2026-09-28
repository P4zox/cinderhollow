# every floor spot the reach checker can stand on in the RC rooms -> JSON {room: [[x, y], ...]} for phantom.js
import sys, json
RC_ARGS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
import reach
IDS = RC_ARGS[0].split(',')
out = {}
hz = ''.join(sorted(HAZARD))
for R in ROOMS:
    if R.id not in IDS: continue
    needs = [n for n in (R.kw.get('needs') or []) if n != 'start']
    edges = reach.edge_codes(R, cell, SOLID)
    G = reach.Grid(R, edges, SOLID, needs, hz)
    rc = reach.Reach(G, needs)
    ents = reach.entrances(G, R)
    seeds = [s for _, sd, _ in ents for s in sd]
    res = rc.search(seeds)
    G0 = reach.Grid(R, edges, SOLID, needs, hz, kit=False)   # only real floor: not the swept paths of movers, lifts and draughts
    crumble = {(q['x'] + dx, q['y']) for q in R.kw.get('spawns', []) if q.get('t') == 'kit' and q.get('kind') == 'crumble' for dx in range(int(q.get('w', 2)))}
    pts = []
    for si in res['stand']:
        ty, x0, x1 = rc.spans[si]
        xs = sorted(set(list(range(x0, x1 + 1, 2)) + [x1]))
        pts += [[x, ty] for x in xs if reach.standable(G0, x, ty) and (x, ty + 1) not in crumble]
    out[R.id] = sorted(pts)
json.dump(out, open(RC_ARGS[1], 'w'))
print({k: len(v) for k, v in out.items()}, sum(len(v) for v in out.values()))
