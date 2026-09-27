# Route planner for the trial pilots: breadth-first search over tools/reach.py's frame-accurate player simulation, keeping
# the parent edge of every node, then writes the chosen route as per-frame inputs a headless test can replay.
# python3 tools/shots/rc/plan.py ROOM sx sy gx gy [needs,csv] [out.json]
import sys, json
RC_ARGS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
import reach
from reach import Grid, Reach, Body, prog, MAXV, TILE, standable

rid, sx, sy, gx, gy = RC_ARGS[0], int(RC_ARGS[1]), int(RC_ARGS[2]), int(RC_ARGS[3]), int(RC_ARGS[4])
R = next(q for q in ROOMS if q.id == rid)
needs = RC_ARGS[5].split(',') if len(RC_ARGS) > 5 and RC_ARGS[5] else [n for n in R.kw.get('needs', []) if n != 'start']
out_path = RC_ARGS[6] if len(RC_ARGS) > 6 else None
hz = ''.join(sorted(HAZARD))
G = Grid(R, cell, SOLID, needs, hz)
rc = Reach(G, needs)
sim = rc.sim
gpx, gpy = gx * TILE + 8, (gy + 1) * TILE - 4


def recorded(fac):
    rec = []
    f = fac()
    def g(i, t, b, info):
        r = f(i, t, b, info); rec.append([int(r[0]), bool(r[1]), bool(r[2]), bool(r[3])]); return r
    return g, rec


def touches_goal(o):
    return any(abs(x - gpx) < 12 and abs(y - 4 - gpy) < 20 for x, y in o['pts']) or (o['land'] and abs(o['land'][0] - gpx) < 12 and abs(o['land'][1] - (gy + 1) * TILE) < 6)


start = ('stand', sx, sy)
seen = {start: None}
seen_spans = {rc.span_of.get((sx, sy))}
queue = [start]
found = None
qi = 0
while qi < len(queue) and not found:
    node = queue[qi]; qi += 1
    trials = []
    if node[0] == 'stand':
        tx, ty = node[1], node[2]
        si = rc.span_of.get((tx, ty))
        if si is None: continue
        _, x0, x1 = rc.spans[si]
        starts = [(x * TILE + 8, 0) for x in range(x0, x1 + 1)]
        for x in range(x0, x1 + 1):
            for d in (1, -1):
                if (x - x0 if d > 0 else x1 - x) >= 1 and (x1 - x if d > 0 else x - x0) <= 1: starts.append((x * TILE + 8, d))
        starts += [(x1 * TILE + 8 + 3, 1), (x0 * TILE + 8 - 3, -1)]
        for (bx, sd) in starts:
            for name, fac in rc.man:
                d = Reach._dir(fac())
                if sd and d != sd: continue
                trials.append(('stand', bx, (ty + 1) * TILE, sd, name, fac, False))
        for (bx, d) in ((x1 * TILE + 8 + 3, 1), (x0 * TILE + 8 - 3, -1)):
            for name, fac in rc.walk:
                if Reach._dir(fac()) != d: continue
                trials.append(('stand', bx, (ty + 1) * TILE, d, name, fac, True))
    else:
        _, x, y, side, aj = node
        facs = []
        for post in (side, -side, 0):
            facs.append(('wj%+d' % post, lambda post=post: prog(post)))
            facs.append(('wjdash%+d' % post, lambda post=post: prog(post, dash='apex', dash_d=-side)))
            if 'gale' in needs: facs.append(('wjglide%+d' % post, lambda post=post: prog(post, glide=True)))
        for tt in (0.2, 0.3, 0.4):
            facs.append(('wjback%.1f' % tt, lambda tt=tt: prog(-side, steer=(tt, side))))
            facs.append(('wjhang%.1f' % tt, lambda tt=tt: prog(-side, steer=(tt, 0))))
        for name, fac in facs: trials.append(('wall', x, y, side, name, fac, aj))
    for tr in trials:
        g, rec = recorded(tr[5])
        if tr[0] == 'stand':
            _, bx, by, sd, name, fac, walk = tr
            b = Body(bx, by, sd * MAXV if sd else 0, 0, True, rc.aj_max, False, True)
        else:
            _, bx, by, side, name, fac, aj = tr
            b = Body(bx, by, 0, 30, False, aj, False, True); b.mode = 'wall'; b.wall = side
        o = sim.run(b, g, max_t=4.5)
        if o['dead']: continue
        edge = dict(kind=tr[0], x=bx, y=by, d=(tr[3] if tr[0] == 'stand' else tr[3]), name=name, inputs=rec, end=None)
        if touches_goal(o):
            edge['end'] = ['goal']; found = (node, edge); break
        nxt = None
        if o['land']:
            lx, ly = o['land'][0], o['land'][1]
            nx, ny = int(lx // TILE), int(round(ly / TILE)) - 1
            if (nx, ny) not in rc.span_of:
                for dx in (-1, 1):
                    if (int((lx + dx * 4) // TILE), ny) in rc.span_of: nx = int((lx + dx * 4) // TILE); break
            if (nx, ny) in rc.span_of: nxt = ('stand', nx, ny); edge['end'] = ['stand', lx, ly]
        elif o['wall']:
            wx, wy, side, aj, ms = o['wall']
            nxt = ('wall', round(wx, 1), round(wy, 1), side, aj); edge['end'] = ['wall', wx, wy, side]
        if not nxt or nxt in seen: continue
        if nxt[0] == 'stand':
            sp = rc.span_of.get((nxt[1], nxt[2]))
            if sp in seen_spans: continue
            seen_spans.add(sp)
        elif any(k and k[0] == 'wall' and abs(k[1] - nxt[1]) < 6 and abs(k[2] - nxt[2]) < 6 and k[3] == nxt[3] for k in seen): continue
        seen[nxt] = (node, edge); queue.append(nxt)

if not found:
    print('NO ROUTE', rid, 'nodes', len(seen)); sys.exit(1)
route = [found[1]]
node = found[0]
while seen.get(node):
    parent, edge = seen[node]; route.append(edge); node = parent
route.reverse()
print(rid, 'route', len(route), 'edges:', ' > '.join(f"{e['kind'][0]}{e['name']}@{e['x'] / 16:.1f},{e['y'] / 16:.1f}" for e in route))
if out_path:
    json.dump(route, open(out_path, 'w'))
