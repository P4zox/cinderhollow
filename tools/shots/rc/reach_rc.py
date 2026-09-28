# uncached reach check of the RC rooms (+ the old rooms RC patched): python3 tools/shots/rc/reach_rc.py
import sys
RC_ARGS = []
exec(open('tools/shots/rc/rload.py').read())
import reach
IDS = 'SP9 SP10 SP11 SP12 SP8 SP15 SP14 SP17 SP13 SP16 LF1 D9 D10 D11 D12 D13 D14 D15 D16 D17 X6 X10 X11 X7 X8 X9 X12 SP3 SP7 D4 D6 X5 W1'.split()
hz = ''.join(sorted(HAZARD)); bad = 0
for R in ROOMS:
    if R.id not in IDS: continue
    msgs = reach.check_room(R, cell, SOLID, hz, cache=None)
    for m in msgs: print(*m); bad += m[0] == 'ERR'
    if not msgs: print('ok', R.id)
print('ERR total', bad)
