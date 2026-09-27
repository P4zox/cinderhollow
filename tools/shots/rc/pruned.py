# which spans does reach.py's pruned search reach in a room? python3 tools/shots/rc/pruned.py ROOM
import sys
RC_R = sys.argv[1]
exec(open('tools/shots/rc/rload.py').read())
import reach
R = next(q for q in ROOMS if q.id == RC_R); hz = ''.join(sorted(HAZARD))
e = reach.edge_codes(R, cell, SOLID); nd = [n for n in R.kw.get('needs', []) if n != 'start']
G = reach.Grid(R, e, SOLID, nd, hz); rc = reach.Reach(G, nd)
tg = reach.room_targets(R); allseeds = [s for _, seeds, _ in reach.entrances(G, R) for s in seeds]
def fn(x0, x1, y0, y1, stand, pts, exits):
    for si, (ty, a, b) in enumerate(rc.spans):
        if si not in stand and b >= x0 and a <= x1 and y0 <= ty <= y1: return True
    for (label, tx, ty, kind) in tg:
        if x0 <= tx <= x1 and y0 <= ty <= y1 and not reach.target_met({'stand': stand, 'pts': pts}, R, tx, ty, kind, rc): return True
    return False
res = rc.search(allseeds, fn)
print(sorted(rc.spans[si] for si in res['stand']), 'walls', len(res['walls']))
