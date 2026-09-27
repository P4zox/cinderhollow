# print SC rooms' maps: python3 tools/shots/sc/show.py NH8 NH9
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import reach
mod = reach._load_rooms()
for rid in sys.argv[1:]:
    R = mod.ROOM(rid); print(rid, R.name, R.gx, R.gy, R.w, R.h)
    print('    ' + ''.join(str(x // 10 % 10) for x in range(R.w))); print('    ' + ''.join(str(x % 10) for x in range(R.w)))
    for y, row in enumerate(R.rows()): print(f'{y:3d} {row}')
