"""RA validation: python3 tools/shots/ra/val.py [ROOM ...]  -> structural ERRs for RA rooms (+ anchors), then reach per room (parallel)."""
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
MINE = ['R%d' % i for i in range(5, 15)] + ['C%d' % i for i in range(7, 16)] + ['K%d' % i for i in range(5, 14)]
ANCH = ['R1', 'R2', 'C1', 'C4', 'K1', 'K3']
out = subprocess.run([sys.executable, 'tools/rooms.py'], cwd=ROOT, env=dict(os.environ, NOREACH='1'), capture_output=True, text=True).stdout
pat = re.compile(r'\b(' + '|'.join(MINE + ANCH) + r')\b')
for l in out.splitlines():
    if ('80_ra' in l) or (l.startswith(('ERR', 'REGION')) and pat.search(l.split(':')[0] if ':' in l else l)): print(l)
ids = sys.argv[1:] or MINE
def one(r):
    p = subprocess.run([sys.executable, 'tools/reach.py', r], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() + (p.stderr.strip()[-400:] if p.returncode else '')
with ThreadPoolExecutor(6) as ex:
    for r, res in zip(ids, ex.map(one, ids)): print(res)
