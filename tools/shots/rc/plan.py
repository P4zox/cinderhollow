# Route planner for the trial pilots: breadth-first search over tools/reach.py's frame-accurate player simulation, keeping
# the parent edge of every node, then writes the chosen route as per-frame inputs a headless test can replay.
# python3 tools/shots/rc/plan.py ROOM sx sy gx gy [needs,csv] [out.json] [nokit]
# goal: a cell (gx gy), or an exit: gx = 'W'|'E'|'N'|'S' and gy = 'a:b' (the edge rows/cols to leave through).
# nokit: ignore movers, lifts, winds and swings (they aren't where the checker's swept-area model puts them at replay time).
import sys, json
RC_ARGS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
import reach
from reach import Grid, Reach, Body, prog, MAXV, TILE, standable

rid = RC_ARGS[0]
BODY0 = None
if RC_ARGS[1].startswith('{'):
    BODY0 = json.loads(RC_ARGS[1]); sx, sy = int(BODY0['x'] // 16), int(round(BODY0['y'] / 16)) - 1
else:
    sx, sy = int(RC_ARGS[1]), int(RC_ARGS[2])
EXIT_GOAL = None
if RC_ARGS[3] in 'WENS':
    _a, _b = RC_ARGS[4].split(':'); EXIT_GOAL = (RC_ARGS[3], int(_a), int(_b)); gx = gy = -99
else:
    gx, gy = int(RC_ARGS[3]), int(RC_ARGS[4])
R = next(q for q in ROOMS if q.id == rid)
if len(RC_ARGS) > 8 and RC_ARGS[8]:   # cells the game has already broken open (cracked floors/walls)
    for c in RC_ARGS[8].split(';'):
        _x, _y = map(int, c.split(',')); R.g[_y][_x] = '.'
ORIG_SPAWNS = list(R.kw.get('spawns', []))
if len(RC_ARGS) > 7 and RC_ARGS[7] == 'nokit':
    R.kw = dict(R.kw); R.kw['spawns'] = [q for q in R.kw.get('spawns', []) if not (q.get('t') == 'kit' and q.get('kind') in ('mover', 'lift', 'wind', 'swing'))]
needs = RC_ARGS[5].split(',') if len(RC_ARGS) > 5 and RC_ARGS[5] else [n for n in R.kw.get('needs', []) if n != 'start']
out_path = RC_ARGS[6] if len(RC_ARGS) > 6 else None
hz = ''.join(sorted(HAZARD))
G = Grid(R, cell, SOLID, needs, hz)
if len(RC_ARGS) > 7 and RC_ARGS[7] == 'nokit':   # steer clear of the draughts the sim can't model (it would drift in them)
    for q in ORIG_SPAWNS:
        if q.get('t') == 'kit' and q.get('kind') == 'wind':
            for yy in range(q['y'], q['y'] + int(q.get('h', 4))):
                for xx in range(q['x'], q['x'] + int(q.get('w', 4))):
                    if 0 <= xx < G.w and 0 <= yy < G.h and G.t[yy * G.w + xx] in (0, 7): G.t[yy * G.w + xx] = 5
    G._pad()
rc = Reach(G, needs)
CRUMBLE = {(q['x'] + dx, q['y']) for q in ORIG_SPAWNS if q.get('t') == 'kit' and q.get('kind') == 'crumble' for dx in range(int(q.get('w', 2)))}
sim = rc.sim
gpx, gpy = gx * TILE + 8, (gy + 1) * TILE - 4


POGO = [False]
def recorded(fac):
    rec = []
    f = fac()
    def g(i, t, b, info):
        if b.vy > 0 and reach.pogo_ready(b, G): POGO[0] = True   # the sim bounces off thorns here (the replay must down-strike)
        r = f(i, t, b, info); rec.append([int(r[0]), bool(r[1]), bool(r[2]), bool(r[3])]); return r
    return g, rec


def touches_goal(o):
    if EXIT_GOAL: return bool(o.get('exit')) and o['exit'][0] == EXIT_GOAL[0] and EXIT_GOAL[1] <= o['exit'][1] <= EXIT_GOAL[2]
    return bool(o['land']) and abs(o['land'][0] - gpx) < 12 and abs(o['land'][1] - (gy + 1) * TILE) < 6   # a cell goal means standing there


if not BODY0 and (sx, sy) not in rc.span_of:   # standing on a lip: the neighbouring cell carries the feet
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1)):
        if (sx + _dx, sy + _dy) in rc.span_of: sx, sy = sx + _dx, sy + _dy; break
start = ('body',) if BODY0 else ('stand', sx, sy)
if not BODY0 and not EXIT_GOAL and rc.span_of.get((gx, gy)) is not None and rc.span_of.get((gx, gy)) == rc.span_of.get((sx, sy)):
    route = [dict(kind='stand', x=gx * TILE + 8, y=(gy + 1) * TILE, d=0, name='walk', inputs=[], end=['goal'])]   # same floor: just walk over
    print(rid, 'route 1 edges: walk'); print('JSON' + json.dumps(route)) if out_path == '-' else (out_path and json.dump(route, open(out_path, 'w'))); sys.exit(0)
for ALLOW_POGO in (False, True):   # prefer routes that never need a down-strike off thorns
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
            if EXIT_GOAL and EXIT_GOAL[0] in 'WE' and EXIT_GOAL[1] <= ty <= EXIT_GOAL[2] and ((EXIT_GOAL[0] == 'W' and x0 == 0) or (EXIT_GOAL[0] == 'E' and x1 == G.w - 1)):
                d = -1 if EXIT_GOAL[0] == 'W' else 1
                found = (node, dict(kind='walkout', x=(tx * TILE + 8), y=(ty + 1) * TILE, d=d, name='walkout', inputs=[[d, False, False, False]] * 90, end=['exit'])); break
            starts = [(x * TILE + 8, 0) for x in range(x0, x1 + 1)]
            crumbly = any((x, ty + 1) in CRUMBLE for x in range(x0, x1 + 1))   # a crumbling block: jump straight off it, no run-up
            for x in (range(x0, x1 + 1) if not crumbly else ()):
                for d in (1, -1):
                    if (x - x0 if d > 0 else x1 - x) >= 1 and (x1 - x if d > 0 else x - x0) <= 1: starts.append((x * TILE + 8, d))
            if not crumbly: starts += [(x1 * TILE + 8 + 3, 1), (x0 * TILE + 8 - 3, -1)]
            for (bx, sd) in starts:
                for name, fac in rc.man:
                    d = Reach._dir(fac())
                    if sd and d != sd: continue
                    trials.append(('stand', bx, (ty + 1) * TILE, sd, name, fac, False))
            for (bx, d) in (((x1 * TILE + 8 + 3, 1), (x0 * TILE + 8 - 3, -1)) if not crumbly else ()):
                for name, fac in rc.walk:
                    if Reach._dir(fac()) != d: continue
                    trials.append(('stand', bx, (ty + 1) * TILE, d, name, fac, True))
            for x in range(x0, x1 + 1):   # ↓ + jump through a one-way floor
                if G.at(x, ty + 1) == reach.PLAT:
                    for d in (0, 1, -1):
                        trials.append(('drop', x * TILE + 8, (ty + 1) * TILE, d, 'drop%+d' % d, (lambda d=d: (lambda i, t, b, info: (d, False, False, False))), False))
        elif node[0] == 'body':
            B = BODY0
            def hold_prog(d, jh=True, steer=None, rel=None):
                def f(i, t, b, info):
                    ax = d if steer is None or t < steer[0] else steer[1]
                    return (ax, jh and (rel is None or t < rel), False, False)
                return f
            facs = []
            for d in (1, 0, -1):
                facs.append(('air%+d' % d, lambda d=d: hold_prog(d)))
                facs.append(('drop%+d' % d, lambda d=d: hold_prog(d, False)))
                for tt in ((0.15, 0.3, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0) if 'gale' in needs else (0.15, 0.3, 0.5)):   # ride a draught up, then steer out
                    for d2 in (1, 0, -1):
                        if d2 != d: facs.append(('air%+d>%+d@%.2f' % (d, d2, tt), lambda d=d, d2=d2, tt=tt: hold_prog(d, True, (tt, d2))))
            if 'gale' in needs:   # glide on, then let go over a ledge
                for d in (1, 0, -1):
                    for tt in (0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0):
                        facs.append(('air%+d~rel%.1f' % (d, tt), lambda d=d, tt=tt: hold_prog(d, True, None, tt)))
            if B.get('mode') == 'wall':
                side = B.get('wall') or 1
                for post in (side, -side, 0):
                    facs.append(('wj%+d' % post, lambda post=post: prog(post)))
                for tt in (0.2, 0.3, 0.4):
                    facs.append(('wjback%.1f' % tt, lambda tt=tt: prog(-side, steer=(tt, side))))
            for name, fac in facs: trials.append(('body', B['x'], B['y'], 0, name, fac, 0))
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
            elif tr[0] == 'body':
                _, bx, by, _d, name, fac, _a = tr
                b = Body(bx, min(by, G.ph - 1), BODY0.get('vx', 0), BODY0.get('vy', 0), False, rc.aj_max if BODY0.get('aj') else 0, False, bool(BODY0.get('dash', True)))
                if BODY0.get('mode') == 'wall': b.mode = 'wall'; b.wall = BODY0.get('wall') or 1
                elif BODY0.get('mode') == 'glide' and 'gale' in needs: b.mode = 'glide'
            elif tr[0] == 'drop':
                _, bx, by, _d, name, fac, _w = tr
                b = Body(bx, by + 2, 0, 0, False, rc.aj_max, False, True); b.drop = 0.25
            else:
                _, bx, by, side, name, fac, aj = tr
                b = Body(bx, by, 0, 30, False, aj, False, True); b.mode = 'wall'; b.wall = side
            POGO[0] = False
            o = sim.run(b, g, max_t=8.0 if 'gale' in needs else 4.5)
            if POGO[0] and not ALLOW_POGO: continue
            if o['dead']: continue
            if o['land'] and any(r[3] for r in rec[-26:]): continue
            if not o['land'] and o['wall'] and tr[0] == 'stand' and any(r[3] for r in rec[-45:]): continue   # dashing into a wall from a standstill: the game's roll outlasts the sim's
            if o['land'] and not any(py < o['land'][1] - 4 for px, py in o['pts'][-30:]): continue   # scraped over the lip: too fine a margin to replay
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
    if found: break
if not found:
    print('NO ROUTE', rid, 'nodes', len(seen)); sys.exit(1)
route = [found[1]]
node = found[0]
while seen.get(node):
    parent, edge = seen[node]; route.append(edge); node = parent
route.reverse()
print(rid, 'route', len(route), 'edges:', ' > '.join(f"{e['kind'][0]}{e['name']}@{e['x'] / 16:.1f},{e['y'] / 16:.1f}" for e in route))
if out_path and out_path != '-':
    json.dump(route, open(out_path, 'w'))
elif out_path == '-':
    print('JSON' + json.dumps(route))
