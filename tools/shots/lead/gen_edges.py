# Builds the list of every walkable side opening and drop-down opening between two rooms, for edges_run.js.
import re, json, sys, os
ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
s = open(os.path.join(ROOT, 'web/src/02_rooms.js')).read()
R = {}
for m in re.finditer(r'\{ \.\.\.(\{.*?\}), map: \[(.*?)\] \}', s, re.S):
    d = json.loads(m.group(1))
    if d.get('test'): continue
    d['rows'] = [json.loads('"%s"' % r) for r in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))]
    R[d['id']] = d
cell = {}
for d in R.values():
    for y in range(d['h']):
        for x in range(d['w']): cell[(d['gx'] + x, d['gy'] + y)] = d['id']
SOLID = set('#BY')
flo = lambda d, x, y: 0 <= y < d['h'] and 0 <= x < d['w'] and d['rows'][y][x] in SOLID | {'='}
tests = []
for d in R.values():
    w, h = d['w'], d['h']
    # side openings: a run of open cells on the W/E edge with floor under its lowest cell -> walk across
    for side, x, dx in (('W', 0, -1), ('E', w - 1, 1)):
        y = 0
        while y < h:
            if d['rows'][y][x] in SOLID: y += 1; continue
            y0 = y
            while y < h and d['rows'][y][x] not in SOLID: y += 1
            y1 = y - 1
            if y1 - y0 < 1: continue
            o = cell.get((d['gx'] + x + dx, d['gy'] + y1))
            if not o or o == d['id']: continue
            # stand 2 cells in from the edge on the floor at the bottom of the gap
            sx = x - 2 * dx
            if flo(d, sx, y1 + 1) and d['rows'][y1][sx] not in SOLID and d['rows'][y1 - 1][sx] not in SOLID:
                tests.append({'kind': 'walk', 'from': d['id'], 'to': o, 'x': sx, 'y': y1, 'dir': 'right' if dx > 0 else 'left'})
    # floor openings: drop through
    y = h - 1
    xx = 0
    while xx < w:
        if d['rows'][y][xx] in SOLID or d['rows'][y][xx] == '=': xx += 1; continue
        x0 = xx
        while xx < w and d['rows'][y][xx] not in SOLID and d['rows'][y][xx] != '=': xx += 1
        mid = (x0 + xx - 1) // 2
        o = cell.get((d['gx'] + mid, d['gy'] + h))
        if o and o != d['id']:
            tests.append({'kind': 'drop', 'from': d['id'], 'to': o, 'x': mid, 'y': max(1, h - 4)})
json.dump(tests, open(os.path.join(os.path.dirname(__file__), 'edges.json'), 'w'))
print(len(tests), 'edge tests')
