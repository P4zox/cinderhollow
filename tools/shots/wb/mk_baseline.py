"""Make a 'before WB' build from a current build: swap WB's files back to their pre-pass versions (tools/shots/wb/baseline/)
and drop 60_wbal.js, keeping every other agent's work as it is -- so before/after benches differ only by this pass.
usage: python3 tools/shots/wb/mk_baseline.py web/dist/wb.html web/dist/wb_base.html"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
src, out = sys.argv[1], sys.argv[2]
html = open(src).read()
for f in sorted(os.listdir(os.path.join(HERE, 'baseline'))):
    cur = open(os.path.join(ROOT, 'web', 'src', f)).read(); old = open(os.path.join(HERE, 'baseline', f)).read()
    assert html.count(cur) == 1, f'{f}: current source not found once in {src} (rebuild first)'
    html = html.replace(cur, old)
cur = open(os.path.join(ROOT, 'web', 'src', '60_wbal.js')).read()
assert html.count(cur) == 1; html = html.replace(cur, '')
open(out, 'w').write(html); print('wrote', out)
