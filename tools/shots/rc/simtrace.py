# python3 tools/shots/rc/simtrace.py ROOM '{"x":..,"y":..,"vx":..,"vy":..,"mode":"wall","wall":1,"aj":0,"dash":true}' '[[ax,jh,jp,rp],...]'
import sys, json
RC_A = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
import reach
from reach import Grid, Body, Sim
R = next(q for q in ROOMS if q.id == RC_A[0]); B = json.loads(RC_A[1]); I = json.loads(RC_A[2])
R.kw = dict(R.kw); R.kw['spawns'] = [q for q in R.kw.get('spawns', []) if not (q.get('t') == 'kit' and q.get('kind') in ('mover', 'lift', 'wind', 'swing'))]
G = Grid(R, cell, SOLID, [n for n in R.kw.get('needs', []) if n != 'start'], ''.join(sorted(HAZARD)))
sim = Sim(G, set(R.kw.get('needs', [])))
b = Body(B['x'], B['y'], B.get('vx', 0), B.get('vy', 0), B.get('ground', False), 0, False, B.get('dash', True))
if B.get('mode') == 'wall': b.mode = 'wall'; b.wall = B.get('wall', 1)
tr = []
def prog(i, t, bb, info):
    r = I[i] if i < len(I) else [0, False, False, False]
    if i % 6 == 0: tr.append(f'{bb.x/16:.2f},{bb.y/16:.2f}{bb.mode[0]}')
    return tuple(r)
o = sim.run(b, prog, max_t=len(I) / 60)
print(' '.join(tr)); print('END', o['land'], o['wall'])
