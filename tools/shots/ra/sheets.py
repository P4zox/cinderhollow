"""usage: python3 tools/shots/ra/sheets.py ROOM:tx:ty [...]  -> tools/shots/ra/out/sheet_<ROOM>.png (full-room renders)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
ids = [[a.split(':')[0], int(a.split(':')[1]), int(a.split(':')[2])] for a in sys.argv[1:]]
tmp = os.path.join(HERE, '_sheet_run.js')
open(tmp, 'w').write(f'window.__ids = {json.dumps(ids)};\n' + open(os.path.join(HERE, 'sheet.js')).read())
env = dict(os.environ, SHOT_HTML=os.environ.get('SHOT_HTML', os.path.join(ROOT, 'web/dist/ra.html')))
subprocess.run(['node', os.path.join(ROOT, 'tools/shots/shot.js'), tmp, os.path.join(HERE, 'out')], env=env)
