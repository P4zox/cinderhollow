# list the walkable links between rooms (shared open edge cells) for the RC wings: python3 tools/shots/rc/links.py ID...
import sys
RC_ARGS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
ids = set(RC_ARGS)
byid = {r.id: r for r in ROOMS}
def openc(r, x, y): return r.g[y][x] not in SOLID
out = []
for a in ROOMS:
    if a.id not in ids: continue
    for b in ROOMS:
        if b is a: continue
        # a's east edge against b's west edge etc.
        for side, cond in (('E', a.gx + a.w == b.gx), ('W', b.gx + b.w == a.gx), ('S', a.gy + a.h == b.gy), ('N', b.gy + b.h == a.gy)):
            if not cond: continue
            cells = []
            if side in 'EW':
                for wy in range(max(a.gy, b.gy), min(a.gy + a.h, b.gy + b.h)):
                    ax = a.w - 1 if side == 'E' else 0; bx = 0 if side == 'E' else b.w - 1
                    if openc(a, ax, wy - a.gy) and openc(b, bx, wy - b.gy): cells.append(wy - a.gy)
            else:
                for wx in range(max(a.gx, b.gx), min(a.gx + a.w, b.gx + b.w)):
                    ay = a.h - 1 if side == 'S' else 0; by = 0 if side == 'S' else b.h - 1
                    if openc(a, wx - a.gx, ay) and openc(b, wx - b.gx, by): cells.append(wx - a.gx)
            if cells: out.append(f"{a.id} {side} {min(cells)}:{max(cells)} -> {b.id}  ({len(cells)} cells)")
print('\n'.join(out))
