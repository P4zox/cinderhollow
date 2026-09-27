# python3 tools/shots/rc/rshow.py ROOM [needs,csv]: reach map with the real hazard set
import sys
RC_RID = sys.argv[1]; RC_ND = sys.argv[2].split(',') if len(sys.argv) > 2 else None
exec(open('tools/shots/rc/rload.py').read())
import reach
R = next(q for q in ROOMS if q.id == RC_RID); print(R.id, R.w, R.h); hz = ''.join(sorted(HAZARD)); needs = RC_ND or [n for n in R.kw.get('needs', []) if n != 'start']
G = reach.Grid(R, cell, SOLID, needs, hz); rc = reach.Reach(G, needs)
res = rc.search([s for _, seeds, _ in reach.entrances(G, R) for s in seeds])
print(reach.show(R, G, res, rc))
