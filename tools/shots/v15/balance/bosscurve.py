#!/usr/bin/env python3
# per boss: stage, HP in light hits (at the expected build), mean TTK / damage taken across types (geo mean), worst/best type
import json, sys, glob, os, statistics as S
d = sys.argv[1]; rows = []
for f in glob.glob(os.path.join(d, '*.json')):
    t = open(f).read()
    try: rows += json.loads(t[:t.rindex(']') + 1])
    except Exception: pass
SKIP = set(os.environ.get('SKIP', 'warden ferryman choir colossus saint0 sovereign venn').split())
def ttk(r): return r['secs'] if r['killed'] else r['secs'] / max(1 - (r['hpLeft'] if r['hpLeft'] is not None else 1), 0.05)
by = {}
for r in rows:
    if 'err' in r or r['kind'] in SKIP: continue
    by.setdefault(r['kind'], []).append(r)
print(f"{'boss':>12} stage  hp/light  ttk(geo)  taken(geo)  taken/min  stag  bestTTK  worstTTK  maxHit")
for k, rs in sorted(by.items(), key=lambda kv: kv[1][0]['stage']):
    t = S.geometric_mean([ttk(r) for r in rs]); tk = S.geometric_mean([max(r['taken'], 0.02) for r in rs])
    per = {}
    for r in rs: per.setdefault(r['type'], []).append(ttk(r))
    pm = {ty: S.mean(v) for ty, v in per.items()}; b = min(pm, key=pm.get); w = max(pm, key=pm.get)
    print(f"{k:>12} {rs[0]['stage']:5} {rs[0]['bossMax']/rs[0]['light']:8.0f} {t:9.0f} {tk:10.2f} {tk/t*60:10.2f} {S.mean(r['staggers'] for r in rs):5.1f}  {b[:6]:>6} {pm[b]:4.0f}  {w[:6]:>6} {pm[w]:4.0f}  {max(r['maxHit'] for r in rs):.2f}")
