import json,sys; t=sys.stdin.read(); d=json.loads(t[t.index('{'):t.rindex('}')+1]); b=d.get('none')
for k,v in d.items():
  b=d['none_c'] if k.endswith('_c') and 'none_c' in d else d['none_cb'] if (k.endswith('_cb') or k.endswith('_wc')) and 'none_cb' in d else d['none']
  print(f"{k:12s} dps {v['dps']:5d} ({(v['dps']/b['dps']-1)*100:+4.0f}%)  taken {v['taken']:5d} healed {v['healed']:5d} landed {v['landed']:6s} net/min {v['netPerMin']:6d} maxHp {v['maxHp']} survive {v['surviveS']:4d}s ({(v['surviveS']/b['surviveS']-1)*100:+4.0f}%) cost {v['cost']}")
if 'ERRORS' in t: print(t[t.index('ERRORS'):][:800])
