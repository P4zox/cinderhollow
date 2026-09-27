# python3 tools/shots/rc/show.py SP17 [SP8 ...]: print rooms as built (no validation, no reach)
import sys
RC_IDS = sys.argv[1:]
exec(open('tools/shots/rc/rload.py').read())
for i in RC_IDS:
    R = ROOM(i); print(R.id, R.name, R.gx, R.gy, R.w, R.h)
    for y, row in enumerate(R.rows()): print(f'{y:3d} {row}')
