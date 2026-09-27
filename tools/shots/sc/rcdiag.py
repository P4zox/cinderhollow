# reach diagnosis like check_room, printing the map of the main (pruned) search: python3 tools/shots/sc/rcdiag.py SF10
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import reach
mod = reach._load_rooms()
H = ''.join(sorted(mod.HAZARD))
cap = {}
orig = reach.Reach.search
def search(self, seeds, targets_fn=None, stop_on_exit=False, budget=60000):
    cnt = [0]; o = self.sim.run
    def run(*a, **k): cnt[0] += 1; return o(*a, **k)
    self.sim.run = run
    r = orig(self, seeds, targets_fn, stop_on_exit, budget)
    self.sim.run = o
    if not stop_on_exit and 'res' not in cap: cap['res'] = r; cap['rc'] = self; cap['n'] = cnt[0]
    return r
reach.Reach.search = search
for rid in sys.argv[1:]:
    cap.clear(); R = mod.ROOM(rid); t = time.time()
    msgs = reach.check_room(R, mod.cell, mod.SOLID, H)
    for m in msgs: print(*m)
    rc = cap['rc']; res = cap['res']
    unreached = [(ty, a, b) for si, (ty, a, b) in enumerate(rc.spans) if si not in res['stand']]
    print(f'{rid}: {len(msgs)} msgs, {time.time() - t:.1f}s, main sims {cap["n"]}, spans {len(rc.spans)}, unreached {unreached[:30]}')
    print(reach.show(R, rc.G, res, rc))
