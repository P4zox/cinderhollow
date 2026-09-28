"""wmap.py x0 x1 y0 y1 [step] : ASCII of the final world in a global rect (' ' = no room). Room ids listed below."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.environ['NOREACH'] = '1'
import reach
mod = reach._load_rooms()
x0, x1, y0, y1 = map(int, sys.argv[1:5]); st = int(sys.argv[5]) if len(sys.argv) > 5 else 1
seen = {}
for gy in range(y0, y1 + 1, st):
    row = ''
    for gx in range(x0, x1 + 1, st):
        R, ch = mod.cell(gx, gy)
        if R is None: row += ' '
        else:
            seen[R.id] = (R.gx, R.gy, R.w, R.h)
            row += ch if st == 1 else ('#' if ch in mod.SOLID else '.')
    print(f'{gy:5d} {row}')
for k, v in sorted(seen.items(), key=lambda t: (t[1][1], t[1][0])): print(k, v)
