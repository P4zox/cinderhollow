# print a bench_real JSON (or a before/after pair) as a table: python3 table.py after.json [before.json]
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
cols = ['dps', 'sig', 'sigPct', 'status', 'statusPct', 'far60', 'farRsig', 'artDps', 'healPerMin', 'heavies', 'light']
print('%-18s %-6s ' % ('weapon', 'cls') + ' '.join('%8s' % c[:8] for c in cols))
for k, v in sorted(a.items(), key=lambda kv: (kv[1]['cls'], -kv[1]['dps'])):
    def cell(c):
        x = v.get(c, 0)
        return '%8s' % (('%d>%d' % (b[k].get(c, 0), x)) if b and k in b and b[k].get(c, 0) != x else x)
    print('%-18s %-6s ' % (k, v['cls']) + ' '.join(cell(c) for c in cols))
