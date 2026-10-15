#!/usr/bin/env python3
# compare each node's matrix with 'none': TTK and damage-taken change per type (%, geo mean over bosses), and the spread
import json, sys, glob, os, statistics as S
d = sys.argv[1]
def load(f):
    t = open(f).read(); return [r for r in json.loads(t[:t.rindex(']') + 1]) if 'err' not in r]
def ttk(r): return r['secs'] if r['killed'] else r['secs'] / max(1 - (r['hpLeft'] if r['hpLeft'] is not None else 1), 0.05)
base = load(os.path.join(d, 'none.json'))
def key(r): return (r['kind'], r['type'])
def agg(rows, fn):
    m = {}
    for r in rows: m.setdefault(key(r), []).append(fn(r))
    return {k: S.mean(v) for k, v in m.items()}
bt, bk = agg(base, ttk), agg(base, lambda r: r['taken'] + 0.1)
types = []
for r in base:
    if r['type'] not in types: types.append(r['type'])
print(f"{'node':>16}  ttk% " + ' '.join(f"{t[:6]:>6}" for t in types) + "  | taken% all   value")
res = []
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    n = os.path.basename(f)[:-5]
    if n == 'none': continue
    try: rows = load(f)
    except Exception as e: print(n, 'bad'); continue
    nt, nk = agg(rows, ttk), agg(rows, lambda r: r['taken'] + 0.1)
    per = {}
    for t in types:
        ks = [k for k in nt if k[1] == t and k in bt]
        per[t] = (S.geometric_mean([nt[k] / bt[k] for k in ks]) - 1) * 100 if ks else 0
    allt = (S.geometric_mean([nt[k] / bt[k] for k in nt if k in bt]) - 1) * 100
    allk = (S.geometric_mean([nk[k] / bk[k] for k in nk if k in bk]) - 1) * 100
    # value: % less time-to-kill plus % less damage taken (rough "how much easier the fight got")
    res.append((n, per, allt, allk, -allt - allk))
for n, per, allt, allk, v in sorted(res, key=lambda x: -x[4]):
    print(f"{n:>16} {allt:5.0f} " + ' '.join(f"{per[t]:6.0f}" for t in types) + f"  | {allk:6.0f}  {v:6.0f}")
