"""run.py TEST.js : inject spots.json as window.__spots and run it against web/dist/ra.html"""
import json, os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, '..', '..', '..')
body = open(sys.argv[1]).read(); spots = open(os.path.join(H, 'spots.json')).read().replace('\n', '')
tmp = os.path.join(H, '_run_' + os.path.basename(sys.argv[1]))
open(tmp, 'w').write('window.__spots = ' + json.dumps(spots) + ';\n' + body)
subprocess.run(['node', os.path.join(ROOT, 'tools/shots/shot.js'), tmp, os.path.join(H, 'out')], env=dict(os.environ, SHOT_HTML=os.environ.get('SHOT_HTML', os.path.join(ROOT, 'web/dist/ra.html'))))
