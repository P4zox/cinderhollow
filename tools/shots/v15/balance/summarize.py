#!/usr/bin/env python3
# summarize a matrix dir: per boss x type mean TTK (s, '*' = not killed in time: projected from HP left), damage taken (x max HP), staggers
import json, sys, glob, os, statistics as S
d = sys.argv[1]; field = sys.argv[2] if len(sys.argv) > 2 else 'ttk'
rows = []
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    try: txt = open(f).read(); rows += json.loads(txt[:txt.rindex(']') + 1])
    except Exception as e: print('bad', f, e)
types = []; kinds = []
for r in rows:
    if 'err' in r: continue
    if r['type'] not in types: types.append(r['type'])
    if r['kind'] not in kinds: kinds.append(r['kind'])
STAGE = {r['kind']: r['stage'] for r in rows if 'stage' in r}
SKIP = set(os.environ.get('SKIP', 'warden ferryman choir colossus saint0 sovereign venn').split())
kinds = [k for k in kinds if k not in SKIP]
kinds.sort(key=lambda k: STAGE.get(k, 99))
def ttk(r):  # projected time to kill
    if r['killed']: return r['secs']
    done = 1 - (r['hpLeft'] if r['hpLeft'] is not None else 1)
    return r['secs'] / max(done, 0.05)
def val(r):
    if field == 'ttk': return ttk(r)
    if field == 'taken': return r['taken']
    if field == 'rate': return r['taken'] / ttk(r) * 60   # max HP lost per minute
    if field == 'life': return r['taken'] * 1.0          # same as taken
    return r.get(field, 0)
print(f"{field:>13} " + ' '.join(f"{t[:6]:>7}" for t in types) + '   mean  spread')
allv = {t: [] for t in types}
for k in kinds:
    vals = []
    for t in types:
        rs = [r for r in rows if r.get('kind') == k and r.get('type') == t and 'err' not in r]
        v = S.mean(val(r) for r in rs) if rs else float('nan'); vals.append(v); allv[t].append(v)
    good = [v for v in vals if v == v]
    m = S.mean(good) if good else 0
    print(f"{k[:9]:>9} {STAGE.get(k,0):>3} " + ' '.join(f"{v:7.1f}" for v in vals) + f" {m:6.1f}  {max(good)/max(min(good),0.01):5.2f}")
print(f"{'mean':>13} " + ' '.join(f"{S.mean(v):7.1f}" for t, v in allv.items()))
# per type relative to the boss mean (geometric), the cross-boss average
rel = {t: [] for t in types}
for i, k in enumerate(kinds):
    good = [allv[t][i] for t in types if allv[t][i] == allv[t][i] and allv[t][i] > 0]
    if not good: continue
    g = S.geometric_mean(good)
    for t in types:
        if allv[t][i] > 0: rel[t].append(allv[t][i] / g)
print(f"{'rel (geo)':>13} " + ' '.join(f"{S.geometric_mean(v):7.2f}" for t, v in rel.items()))
