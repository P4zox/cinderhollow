"""Level builder: rooms on a global tile grid -> web/src/02_rooms.js (+ validation).

Legend: '#' solid, '=' one-way platform, '^' floor spikes, 'v' ceiling spikes, 'B' breakable wall,
'.' empty. Entities (cell = feet cell): P player start, S shrine, s w c f a e K enemies, u urn,
l lantern (hangs from cell top), C chest, i item, L lever, G gate (top cell, 4 tall), H hound,
M Morvain, F fog wall (bottom cell, 5 tall). Decor: x chain, r roots, k candles, b bones.
"""
import json, os, sys

ROOMS = []
SOLID = set('#B')
ENEMY = {'s': 'hollow_soldier', 'w': 'shield_warden', 'c': 'rot_crawler', 'f': 'gloom_wisp',
         'a': 'hollow_archer', 'e': 'ember_acolyte', 'K': 'grave_knight'}


class Room:
    def __init__(self, id, name, biome, gx, gy, w, h, **kw):
        self.id, self.name, self.biome, self.gx, self.gy, self.w, self.h = id, name, biome, gx, gy, w, h
        self.g = [['.'] * w for _ in range(h)]
        self.kw = kw
        ROOMS.append(self)

    def fill(self, x0, y0, x1, y1, ch='#'):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.g[y][x] = ch
        return self

    def put(self, x, y, ch):
        self.g[y][x] = ch
        return self

    def walls(self, top=True, bottom=True, left=True, right=True):
        if top: self.fill(0, 0, self.w - 1, 0)
        if bottom: self.fill(0, self.h - 1, self.w - 1, self.h - 1)
        if left: self.fill(0, 0, 0, self.h - 1)
        if right: self.fill(self.w - 1, 0, self.w - 1, self.h - 1)
        return self

    def open(self, side, a, b):
        for k in range(a, b + 1):
            if side == 'W': self.g[k][0] = '.'
            if side == 'E': self.g[k][self.w - 1] = '.'
            if side == 'N': self.g[0][k] = '.'
            if side == 'S': self.g[self.h - 1][k] = '.'
        return self

    def rows(self):
        return [''.join(r) for r in self.g]


# ============================================================ THE ASHEN RAMPARTS (outdoor, sky above)
r = Room('R1', 'Cliffside Landing', 'ramparts', 0, 0, 48, 14, shrine='Shrine of First Ash')
r.fill(0, 0, 1, 13).fill(0, 11, 47, 13)
r.fill(26, 11, 33, 12, '.').fill(26, 12, 33, 12, '^')
r.fill(27, 8, 32, 8, '=')
r.fill(14, 9, 18, 10).fill(15, 6, 17, 6, '=')
for x, y, ch in [(4, 10, 'P'), (8, 10, 'S'), (12, 10, 'u'), (22, 10, 's'), (40, 10, 's'), (44, 10, 'u'), (36, 10, 'b'), (19, 10, 'u')]:
    r.put(x, y, ch)

r = Room('R2', 'Broken Rampart', 'ramparts', 48, 0, 48, 14)
r.fill(0, 11, 47, 13).fill(47, 0, 47, 4)
r.fill(20, 7, 25, 10).fill(16, 9, 18, 9, '=')
r.fill(38, 11, 40, 12, '.').fill(38, 12, 40, 12, '^')
r.fill(43, 8, 46, 8, '=')
for x, y, ch in [(10, 10, 's'), (23, 6, 'a'), (28, 10, 'c'), (34, 10, 'w'), (14, 10, 'u'), (45, 10, 'u'), (5, 10, 'b')]:
    r.put(x, y, ch)

r = Room('R3', 'Gatehouse Tower', 'ramparts', 96, 0, 24, 28, indoor=True, chests=['seed'])
r.walls().open('W', 5, 10).open('E', 3, 8)
r.fill(1, 11, 9, 12)                       # west entry ledge
r.fill(18, 9, 22, 10)                      # east exit ledge
r.fill(12, 9, 16, 9, '=')
r.fill(0, 25, 23, 27).fill(10, 25, 13, 27, '.')   # bottom floor with the drop hole
for y, x0 in [(22, 15), (19, 9), (16, 14), (13, 10)]:
    r.fill(x0, y, x0 + 3, y, '=')
for x, y, ch in [(20, 8, 'a'), (12, 18, 'f'), (5, 24, 's'), (20, 24, 'C'), (3, 24, 'u'), (4, 1, 'l'), (19, 1, 'l'), (7, 10, 'u')]:
    r.put(x, y, ch)

r = Room('R4', 'Rampart Summit', 'ramparts', 120, 0, 40, 14, items=['gold'], chests=['shard'])
r.fill(0, 9, 7, 13).fill(8, 11, 39, 13).fill(39, 0, 39, 13).fill(0, 0, 0, 2)
r.fill(16, 7, 19, 7, '=').fill(28, 8, 30, 8, '=')
for x, y, ch in [(12, 10, 'c'), (26, 10, 'K'), (37, 10, 'i'), (34, 10, 'C'), (22, 10, 'b'), (3, 8, 'u')]:
    r.put(x, y, ch)

# ============================================================ ROOTBOUND CATACOMBS (indoor)
r = Room('C1', 'The Descent', 'catacombs', 96, 28, 24, 28, indoor=True)
r.walls().open('N', 10, 13).open('W', 21, 24).open('E', 21, 24)
r.fill(0, 25, 23, 27)
for y, x0, x1 in [(6, 3, 8), (10, 14, 20), (14, 4, 10), (18, 13, 19)]:
    r.fill(x0, y, x1, y, '=')
for x, y, ch in [(6, 9, 'f'), (17, 15, 'f'), (12, 24, 'c'), (4, 1, 'l'), (19, 1, 'l'), (2, 24, 'b'), (21, 24, 'k'), (8, 1, 'r'), (16, 1, 'r')]:
    r.put(x, y, ch)

r = Room('C2', 'The Ossuary', 'catacombs', 48, 42, 48, 14, indoor=True, shrine='Ossuary Shrine')
r.walls().open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(0, 8, 0, 10, 'B')
r.fill(9, 9, 15, 10)
r.fill(25, 11, 27, 12, '.').fill(25, 12, 27, 12, '^')
r.fill(19, 7, 23, 7, '=')
for x, y, ch in [(40, 10, 'S'), (12, 8, 'e'), (22, 10, 'c'), (31, 10, 'c'), (5, 10, 's'), (21, 6, 'u'), (35, 10, 'k'), (44, 10, 'k'),
                 (3, 10, 'b'), (18, 10, 'b'), (7, 2, 'l'), (29, 2, 'l'), (14, 2, 'r'), (36, 2, 'x')]:
    r.put(x, y, ch)

r = Room('C2s', 'Forgotten Crypt', 'catacombs', 36, 42, 12, 14, indoor=True, secret=True, items=['shard'])
r.walls().open('E', 8, 10)
r.fill(0, 11, 11, 13).fill(0, 0, 11, 1)
for x, y, ch in [(5, 10, 'i'), (2, 10, 'u'), (8, 10, 'k'), (3, 2, 'l')]:
    r.put(x, y, ch)

r = Room('C3', 'Hall of Roots', 'catacombs', 120, 42, 48, 14, indoor=True)
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(22, 11, 24, 12, '.').fill(22, 12, 24, 12, '^')
r.fill(37, 7, 44, 8)                       # acolyte ledge
r.fill(31, 8, 34, 8, '=').fill(8, 7, 12, 7, '=')
r.fill(14, 2, 18, 3)                       # hanging masonry
for x, y, ch in [(20, 5, 'f'), (34, 4, 'f'), (40, 6, 'e'), (16, 10, 's'), (29, 10, 's'), (45, 10, 'u'), (10, 6, 'u'),
                 (5, 2, 'r'), (26, 2, 'r'), (42, 2, 'r'), (12, 10, 'b'), (3, 10, 'k'), (27, 2, 'l')]:
    r.put(x, y, ch)

r = Room('C4', 'Rootgate', 'catacombs', 168, 42, 24, 14, indoor=True, shrine='Rootgate Shrine')
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 23, 13).fill(0, 0, 23, 1)
for x, y, ch in [(12, 10, 'S'), (5, 2, 'l'), (19, 2, 'l'), (3, 10, 'k'), (20, 10, 'k'), (8, 10, 'b'), (16, 2, 'r')]:
    r.put(x, y, ch)

r = Room('C5', 'Den of the Hound', 'catacombs', 192, 42, 36, 14, indoor=True, boss='hound')
r.walls().open('W', 7, 10).open('E', 6, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
r.fill(8, 7, 11, 7, '=').fill(24, 7, 27, 7, '=')
for x, y, ch in [(1, 10, 'F'), (34, 10, 'F'), (26, 10, 'H'), (6, 2, 'r'), (18, 2, 'r'), (30, 2, 'r'), (4, 10, 'b'), (31, 10, 'b')]:
    r.put(x, y, ch)

r = Room('C6', 'Root Shaft', 'catacombs', 228, 14, 24, 42, indoor=True)
r.walls().open('W', 34, 38).open('E', 3, 8)
r.fill(0, 39, 23, 41)
r.fill(1, 10, 7, 33).fill(14, 9, 22, 33)
r.fill(9, 36, 12, 36, '=')
for y, x0 in [(28, 8), (22, 12), (16, 8)]:
    r.fill(x0, y, x0 + 1, y, '=')
for x, y, ch in [(10, 20, 'f'), (4, 38, 'k'), (18, 38, 'b'), (5, 1, 'l'), (18, 1, 'l'), (10, 1, 'r'), (20, 8, 'u')]:
    r.put(x, y, ch)

# ============================================================ THE SUNKEN CATHEDRAL (indoor)
r = Room('K1', 'Nave of the Pale Root', 'cathedral', 252, 14, 48, 14, indoor=True, shrine='Cathedral Shrine')
r.walls().open('W', 3, 8).open('E', 7, 10)
r.fill(0, 9, 5, 13).fill(6, 11, 47, 13)
r.fill(18, 7, 28, 7, '=').fill(13, 9, 15, 9, '=')
for x, y, ch in [(3, 8, 'S'), (24, 6, 'a'), (38, 10, 'e'), (14, 10, 's'), (31, 10, 's'), (10, 1, 'l'), (34, 1, 'l'),
                 (44, 10, 'u'), (20, 10, 'k'), (42, 1, 'x')]:
    r.put(x, y, ch)

r = Room('K2', 'Flooded Aisle', 'cathedral', 300, 14, 48, 14, indoor=True)
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13)
r.fill(12, 11, 14, 12, '.').fill(12, 12, 14, 12, '^')
r.fill(30, 8, 33, 8, '=').fill(35, 5, 40, 5, '=')
for x, y, ch in [(44, 7, 'G'), (38, 4, 'L'), (20, 10, 'K'), (8, 10, 'c'), (34, 10, 'c'), (26, 4, 'f'), (4, 1, 'l'), (24, 1, 'l'),
                 (46, 10, 'u'), (2, 10, 'k'), (17, 1, 'x')]:
    r.put(x, y, ch)

r = Room('K3', 'Bell Ascent', 'cathedral', 348, 0, 24, 28, indoor=True)
r.walls().open('W', 21, 24).open('E', 21, 24).open('E', 4, 8)
r.fill(0, 25, 23, 27)
r.fill(19, 9, 22, 20)                      # pillar (top = ledge to the secret)
r.fill(11, 3, 12, 13)                      # free column: wall-jump between it and the pillar
r.fill(14, 22, 17, 22, '=').fill(8, 19, 10, 19, '=').fill(14, 16, 17, 16, '=')
for x, y, ch in [(16, 15, 'a'), (8, 24, 's'), (5, 8, 'f'), (4, 1, 'l'), (17, 1, 'l'), (2, 24, 'k'), (21, 8, 'u')]:
    r.put(x, y, ch)

r = Room('K3s', 'Reliquary of Wings', 'cathedral', 372, 0, 24, 14, indoor=True, secret=True, items=['wings'], chests=['shard'])
r.walls().open('W', 4, 8)
r.fill(0, 9, 23, 13)
for x, y, ch in [(12, 8, 'i'), (18, 8, 'C'), (4, 8, 'k'), (20, 8, 'k'), (8, 1, 'l'), (16, 1, 'l')]:
    r.put(x, y, ch)

r = Room('K4', 'Throne of Ash', 'cathedral', 372, 14, 48, 14, indoor=True, boss='omen')
r.walls().open('W', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
for x, y, ch in [(1, 10, 'F'), (34, 10, 'M'), (8, 2, 'l'), (24, 2, 'l'), (40, 2, 'l'), (4, 10, 'k'), (44, 10, 'k')]:
    r.put(x, y, ch)


# ============================================================ validation
def cell(gx, gy):
    for R in ROOMS:
        if R.gx <= gx < R.gx + R.w and R.gy <= gy < R.gy + R.h:
            return R, R.g[gy - R.gy][gx - R.gx]
    return None, None


def validate():
    errs = []
    for R in ROOMS:
        for O in ROOMS:
            if O is R: continue
            if R.gx < O.gx + O.w and R.gx + R.w > O.gx and R.gy < O.gy + O.h and R.gy + R.h > O.gy:
                errs.append(f'overlap {R.id} {O.id}')
        edges = []
        for y in range(R.h):
            edges += [(0, y, -1, 0), (R.w - 1, y, 1, 0)]
        for x in range(R.w):
            edges += [(x, 0, 0, -1), (x, R.h - 1, 0, 1)]
        for x, y, dx, dy in edges:
            ch = R.g[y][x]
            if ch in SOLID and ch != 'B': continue
            O, och = cell(R.gx + x + dx, R.gy + y + dy)
            if O is None:
                if dy == -1 and not R.kw.get('indoor'): continue      # open sky
                errs.append(f'{R.id}: leak at ({x},{y}) dir ({dx},{dy})')
            elif och in SOLID and och != 'B':
                errs.append(f'{R.id}: opening ({x},{y}) blocked by {O.id}')
        n_i = sum(row.count('i') for row in R.rows()); n_c = sum(row.count('C') for row in R.rows())
        if n_i != len(R.kw.get('items', [])): errs.append(f'{R.id}: {n_i} item cells vs {R.kw.get("items")}')
        if n_c != len(R.kw.get('chests', [])): errs.append(f'{R.id}: {n_c} chest cells vs {R.kw.get("chests")}')
        for y, row in enumerate(R.rows()):
            for x, ch in enumerate(row):
                grounded = ch in 'PSswcaeKuCiLHMF'
                if grounded and (y + 1 >= R.h or R.g[y + 1][x] not in SOLID | {'='}):
                    errs.append(f'{R.id}: {ch} at ({x},{y}) not standing on ground')
    return errs


if __name__ == '__main__':
    errs = validate()
    for e in errs: print('ERR', e)
    out = ['// generated by tools/rooms.py — edit there, not here', 'const ROOMS = [']
    for R in ROOMS:
        meta = dict(id=R.id, name=R.name, biome=R.biome, gx=R.gx, gy=R.gy, w=R.w, h=R.h, **R.kw)
        out.append('  { ...' + json.dumps(meta) + ', map: [')
        for row in R.rows():
            out.append('    ' + json.dumps(row) + ',')
        out.append('  ] },')
    out.append('];')
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'src', '02_rooms.js')
    open(path, 'w').write('\n'.join(out) + '\n')
    print(f'wrote {len(ROOMS)} rooms, {len(errs)} errors')
    if '--show' in sys.argv:
        for R in ROOMS:
            print(R.id, R.name); print('\n'.join(R.rows())); print()
    sys.exit(1 if errs else 0)
