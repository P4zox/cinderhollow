# python3 tools/shots/rc/mkreplay.py route.json ROOM out.js [trial=1] [shots=4] [pre.js]
import sys, json
route, room, out = sys.argv[1], sys.argv[2], sys.argv[3]
trial = sys.argv[4] if len(sys.argv) > 4 else '1'
shots = sys.argv[5] if len(sys.argv) > 5 else '4'
pre = open(sys.argv[6]).read() if len(sys.argv) > 6 else ''
tpl = open('tools/shots/rc/replay_tpl.js').read()
waits = sys.argv[7] if len(sys.argv) > 7 else '[0]'
head = f"const WAITS = {waits}; const ROUTE = {open(route).read()}; const ROOM = '{room}'; const TRIAL = {trial}; const SHOTS = {shots};\nconst sign = v => v > 0 ? 1 : v < 0 ? -1 : 0;\nconst PRE = async (G, S, log) => {{ {pre} }};\n"
open(out, 'w').write(head + tpl)
