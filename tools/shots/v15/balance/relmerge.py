#!/usr/bin/env python3
# relative TTK / damage taken per type (geo mean over bosses) from a base matrix dir, with some types' rows replaced from other dirs
# usage: relmerge.py <base dir> [type=dir ...]
import json, glob, sys, statistics as S
def load(d):
    rows = []
    for f in glob.glob(d + '/*.json'):
        t = open(f).read()
        try: rows += [r for r in json.loads(t[:t.rindex(']') + 1]) if 'err' not in r]
        except Exception: pass
    return rows
skip = set('warden ferryman choir colossus saint0 sovereign venn'.split())
rows = load(sys.argv[1]); repl = dict(a.split('=') for a in sys.argv[2:])
for t, d in repl.items(): rows = [r for r in rows if r['type'] != t] + [r for r in load(d) if r['type'] == t]
rows = [r for r in rows if r['kind'] not in skip]
def ttk(r): return r['secs'] if r['killed'] else r['secs'] / max(1 - (r['hpLeft'] or 1), 0.05)
by = {}
for r in rows: by.setdefault((r['kind'], r['type']), []).append(r)
types = sorted({r['type'] for r in rows}); kinds = sorted({r['kind'] for r in rows})
rel = {t: [] for t in types}; relk = {t: [] for t in types}; st = {t: [] for t in types}
for k in kinds:
    v = {t: S.mean(ttk(r) for r in by[(k, t)]) for t in types if (k, t) in by}; g = S.geometric_mean(list(v.values()))
    vk = {t: S.mean(r['taken'] + 0.1 for r in by[(k, t)]) for t in types if (k, t) in by}; gk = S.geometric_mean(list(vk.values()))
    for t in v: rel[t].append(v[t] / g); relk[t].append(vk[t] / gk); st[t] += [r['staggers'] for r in by[(k, t)]]
for t in types: print(f"{t:11} ttk {S.geometric_mean(rel[t]):.2f}  taken {S.geometric_mean(relk[t]):.2f}  staggers/fight {S.mean(st[t]):.1f}")
