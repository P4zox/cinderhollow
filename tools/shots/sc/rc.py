# SC dev helper: reach-check some rooms (python3 tools/shots/sc/rc.py SF10 SF16 [--show] [--needs=a,b])
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import reach
mod = reach._load_rooms()
ids = [a for a in sys.argv[1:] if not a.startswith('--')]
na = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--needs=')), None)
H = ''.join(sorted(getattr(mod, 'HAZARD', set('^v*('))))
for rid in ids:
    R = mod.ROOM(rid); t = time.time()
    if na is not None: R.kw['needs'] = [n for n in na.split(',') if n]
    msgs = reach.check_room(R, mod.cell, mod.SOLID, H)
    for m in msgs: print(*m)
    print(f'{rid}: {len(msgs)} msgs, {time.time() - t:.1f}s')
    if '--show' in sys.argv:
        needs = [n for n in (R.kw.get('needs') or []) if n != 'start']
        G = reach.Grid(R, mod.cell, mod.SOLID, needs, H); rc = reach.Reach(G, needs)
        res = rc.search([s for _, seeds, _ in reach.entrances(G, R) for s in seeds])
        print(reach.show(R, G, res, rc))
