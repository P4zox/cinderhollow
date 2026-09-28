import json, os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, '..', '..', '..')
groups = [['R5','R6','R7','R8','R9'], ['R10','R11','R12','R13','R14'], ['C7','C8','C9','W2'], ['C10','C11','C12','C13','C14','C15'], ['K5','K6','K7','K8'], ['K9','K10','K11','K12','K13']]
body = open(os.path.join(H, 'phantom.js')).read()
for g in groups:
    tmp = os.path.join(H, '_phantom_run.js'); open(tmp, 'w').write(f'window.__ids = {json.dumps(g)};\n' + body)
    subprocess.run(['node', os.path.join(ROOT, 'tools/shots/shot.js'), tmp, os.path.join(H, 'out')], env=dict(os.environ, SHOT_HTML=os.path.join(ROOT, 'web/dist/ra.html')))
