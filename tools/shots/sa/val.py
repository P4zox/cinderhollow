"""SA: validate only SA rooms (+ anchors). usage: python3 tools/shots/sa/val.py [--reach] [ROOM ...]"""
import sys, os, io, contextlib
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, T)
src = open(os.path.join(T, 'rooms.py')).read().split("if __name__ == '__main__':")[0]
g = {'__file__': os.path.abspath(os.path.join(T, 'rooms.py')), '__name__': 'sa_val'}
buf = io.StringIO()
with contextlib.redirect_stdout(buf): exec(compile(src, 'rooms.py', 'exec'), g)
for l in buf.getvalue().splitlines():
    if 'SA ' in l or '83_sa' in l: print(l)
MINE = ('TV', 'DB', 'CM')
ids = [a for a in sys.argv[1:] if not a.startswith('--')]
def mine(m): return any(m.startswith(p) for p in MINE) and (not ids or any(m.startswith(i + ':') or m.startswith(i + ' ') for i in ids))
for e in g['validate']():
    if mine(e): print('ERR', e)
if '--reach' in sys.argv:
    import reach
    R = [r for r in g['ROOMS'] if r.id.startswith(MINE) and (not ids or r.id in ids)]
    for l, m in reach.check_all(R, g['cell'], g['SOLID'], ''.join(sorted(g['HAZARD']))):
        print(l, m)
print('done')
