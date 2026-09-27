"""Level builder: rooms on a global tile grid -> web/src/02_rooms.js (+ validation).

Legend: '@' hook point, '%' ash veil, '|' updraft, 'Y' cracked floor (slam), '~' poison water, '#' solid, '=' one-way platform, '^' floor spikes, 'v' ceiling spikes, 'B' breakable wall,
'.' empty. Entities (cell = feet cell): P player start, S shrine, s w c f a e K enemies, u urn,
l lantern (hangs from cell top), C chest, i item, L lever, G gate (top cell, 4 tall), H hound,
M Morvain, F fog wall (bottom cell, 5 tall). Decor: x chain, r roots, k candles, b bones.
"""
import json, os, sys

ROOMS = []
SOLID = set('#BY')
ENEMY = {'s': 'hollow_soldier', 'w': 'shield_warden', 'c': 'rot_crawler', 'f': 'gloom_wisp',
         'a': 'hollow_archer', 'e': 'ember_acolyte', 'K': 'grave_knight'}


# ---- Expansion 3 world layout: the top row of regions moves up and the bottom row moves down, opening two bands of
# space through the middle of the world for the new wings. Old rooms keep writing their original coordinates and are
# shifted here; new rooms (x3=True) are placed in final coordinates. The six links cut by the move become shafts (below).
WORLD_UP = {'spire', 'archives', 'starfall'}
WORLD_LO = {'necropolis', 'mire', 'deep', 'dunes', 'barrows', 'crimson'}
WORLD_HU, WORLD_HB = 70, 90
def world_shift(biome):
    return -WORLD_HU if biome in WORLD_UP else WORLD_HB if biome in WORLD_LO else 0

class Room:
    def __init__(self, id, name, biome, gx, gy, w, h, **kw):
        if not kw.get('x3') and not kw.get('test'): gy += world_shift(biome)
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
r = Room('R1', 'Cliffside Landing', 'ramparts', 0, 0, 48, 14, shrine='Shrine of First Ash', npcs=['venn'], graves=['r1'])
r.fill(0, 0, 1, 13).fill(0, 11, 47, 13)
r.fill(26, 11, 33, 12, '.').fill(26, 12, 33, 12, '^')
r.fill(27, 8, 32, 8, '=')
r.fill(14, 9, 18, 10).fill(15, 6, 17, 6, '=')
for x, y, ch in [(4, 10, 'P'), (8, 10, 'S'), (12, 10, 'u'), (22, 10, 's'), (40, 10, 's'), (44, 10, 'u'), (36, 10, 'b'), (19, 10, 'u'), (11, 10, 'N'), (29, 7, 'g')]:
    r.put(x, y, ch)

r = Room('R2', 'Broken Rampart', 'ramparts', 48, 0, 48, 14, items=['c_heel'])
r.fill(0, 11, 47, 13).fill(47, 0, 47, 4)
r.fill(20, 7, 25, 10).fill(16, 9, 18, 9, '=')
r.fill(38, 11, 40, 12, '.').fill(38, 12, 40, 12, '^')
r.fill(43, 8, 46, 8, '=')
for x, y, ch in [(10, 10, 's'), (23, 6, 'a'), (28, 10, 'c'), (34, 10, 'w'), (14, 10, 'u'), (45, 10, 'u'), (5, 10, 'b'), (21, 6, 'i')]:
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

r = Room('R4', 'Rampart Summit', 'ramparts', 120, 0, 40, 14, items=['w:greatsword'], chests=['shard'], npcs=['kalden'])
r.fill(0, 9, 7, 13).fill(8, 11, 39, 13).fill(39, 0, 39, 13).fill(0, 0, 0, 2)
r.fill(16, 7, 19, 7, '=').fill(28, 8, 30, 8, '=')
for x, y, ch in [(12, 10, 'c'), (26, 10, 'K'), (37, 10, 'i'), (34, 10, 'C'), (22, 10, 'b'), (3, 8, 'u'), (6, 8, 'N')]:
    r.put(x, y, ch)

# ============================================================ ROOTBOUND CATACOMBS (indoor)
r = Room('C1', 'The Descent', 'catacombs', 96, 28, 24, 28, indoor=True, chests=['w:dagger'])
r.walls().open('N', 10, 13).open('W', 21, 24).open('E', 21, 24)
r.fill(0, 25, 23, 27)
for y, x0, x1 in [(6, 3, 8), (10, 14, 20), (14, 4, 10), (18, 13, 19)]:
    r.fill(x0, y, x1, y, '=')
for x, y, ch in [(6, 9, 'f'), (17, 15, 'f'), (12, 24, 'c'), (4, 1, 'l'), (19, 1, 'l'), (2, 24, 'b'), (21, 24, 'k'), (8, 1, 'r'), (16, 1, 'r'), (18, 24, 'C')]:
    r.put(x, y, ch)

r = Room('C2', 'The Ossuary', 'catacombs', 48, 42, 48, 14, indoor=True, shrine='Ossuary Shrine', npcs=['ashwright'])
r.walls().open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(0, 8, 0, 10, 'B')
r.fill(9, 9, 15, 10)
r.fill(25, 11, 27, 12, '.').fill(25, 12, 27, 12, '^')
r.fill(19, 7, 23, 7, '=')
for x, y, ch in [(40, 10, 'S'), (12, 8, 'e'), (22, 10, 'c'), (31, 10, 'c'), (5, 10, 's'), (21, 6, 'u'), (35, 10, 'k'), (44, 10, 'k'),
                 (3, 10, 'b'), (18, 10, 'b'), (7, 2, 'l'), (29, 2, 'l'), (14, 2, 'r'), (36, 2, 'x'), (33, 10, 'N')]:
    r.put(x, y, ch)

r = Room('C2s', 'Forgotten Crypt', 'catacombs', 36, 42, 12, 14, indoor=True, secret=True, items=['shard'], chests=['c_thorn'])
r.walls().open('E', 8, 10)
r.fill(0, 11, 11, 13).fill(0, 0, 11, 1)
for x, y, ch in [(5, 10, 'i'), (2, 10, 'u'), (8, 10, 'k'), (3, 2, 'l'), (9, 10, 'C')]:
    r.put(x, y, ch)

r = Room('C3', 'Hall of Roots', 'catacombs', 120, 42, 48, 14, indoor=True, items=['c_azure'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(22, 11, 24, 12, '.').fill(22, 12, 24, 12, '^')
r.fill(37, 7, 44, 8)                       # acolyte ledge
r.fill(31, 8, 34, 8, '=').fill(8, 7, 12, 7, '=')
r.fill(14, 2, 18, 3)                       # hanging masonry
r.fill(40, 11, 42, 13, '.').fill(40, 11, 42, 11, '=').fill(40, 13, 42, 13, '=')   # trapdoor down to the Mire
for x, y, ch in [(20, 5, 'f'), (34, 4, 'f'), (40, 6, 'e'), (16, 10, 's'), (29, 10, 's'), (45, 10, 'u'), (10, 6, 'u'),
                 (5, 2, 'r'), (26, 2, 'r'), (42, 2, 'r'), (12, 10, 'b'), (3, 10, 'k'), (27, 2, 'l'), (43, 6, 'i')]:
    r.put(x, y, ch)

r = Room('C4', 'Rootgate', 'catacombs', 168, 42, 24, 14, indoor=True, shrine='Rootgate Shrine', npcs=['venn', 'kalden'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 23, 13).fill(0, 0, 23, 1)
for x, y, ch in [(12, 10, 'S'), (5, 2, 'l'), (19, 2, 'l'), (3, 10, 'k'), (20, 10, 'k'), (8, 10, 'b'), (16, 2, 'r'), (6, 10, 'N'), (18, 10, 'N')]:
    r.put(x, y, ch)

r = Room('C5', 'Den of the Hound', 'catacombs', 192, 42, 36, 14, indoor=True, boss='hound')
r.walls().open('W', 7, 10).open('E', 6, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
r.fill(8, 7, 11, 7, '=').fill(24, 7, 27, 7, '=')
for x, y, ch in [(1, 10, 'F'), (34, 10, 'F'), (26, 10, 'H'), (6, 2, 'r'), (18, 2, 'r'), (30, 2, 'r'), (4, 10, 'b'), (31, 10, 'b')]:
    r.put(x, y, ch)

r = Room('C6', 'Root Shaft', 'catacombs', 228, 14, 24, 42, indoor=True, items=['w:katana'])
r.walls().open('W', 34, 38).open('E', 3, 8)
r.fill(0, 39, 23, 41)
r.fill(1, 10, 7, 33).fill(14, 9, 22, 33)
r.fill(9, 36, 12, 36, '=')
for y, x0 in [(28, 8), (22, 12), (16, 8)]:
    r.fill(x0, y, x0 + 1, y, '=')
for x, y, ch in [(10, 20, 'f'), (4, 38, 'k'), (18, 38, 'b'), (5, 1, 'l'), (18, 1, 'l'), (10, 1, 'r'), (20, 8, 'u'), (4, 9, 'i')]:
    r.put(x, y, ch)

# ============================================================ THE SUNKEN CATHEDRAL (indoor)
r = Room('K1', 'Nave of the Pale Root', 'cathedral', 252, 14, 48, 14, indoor=True, shrine='Cathedral Shrine', npcs=['scribe'], graves=['k1'])
r.walls().open('W', 3, 8).open('E', 7, 10)
r.fill(0, 9, 5, 13).fill(6, 11, 47, 13)
r.fill(18, 7, 28, 7, '=').fill(13, 9, 15, 9, '=')
for x, y, ch in [(3, 8, 'S'), (24, 6, 'a'), (38, 10, 'e'), (14, 10, 's'), (31, 10, 's'), (10, 1, 'l'), (34, 1, 'l'),
                 (44, 10, 'u'), (20, 10, 'k'), (42, 1, 'x'), (9, 10, 'N'), (27, 6, 'g')]:
    r.put(x, y, ch)

r = Room('K2', 'Flooded Aisle', 'cathedral', 300, 14, 48, 14, indoor=True, chests=['w:oathbrand'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13)
r.fill(12, 11, 14, 12, '.').fill(12, 12, 14, 12, '^')
r.fill(30, 8, 33, 8, '=').fill(35, 5, 40, 5, '=')
for x, y, ch in [(44, 7, 'G'), (38, 4, 'L'), (20, 10, 'K'), (8, 10, 'c'), (34, 10, 'c'), (26, 4, 'f'), (4, 1, 'l'), (24, 1, 'l'),
                 (46, 10, 'u'), (2, 10, 'k'), (17, 1, 'x'), (36, 4, 'C')]:
    r.put(x, y, ch)
r.fill(44, 1, 44, 6)          # wall above the gate up to the ceiling: no jumping over it

r = Room('K3', 'Bell Ascent', 'cathedral', 348, 0, 24, 28, indoor=True, items=['emberstone'])
r.walls().open('W', 21, 24).open('E', 21, 24).open('E', 4, 8).open('N', 2, 5)
r.fill(0, 25, 23, 27)
for y, x0, x1 in [(16, 3, 6), (13, 6, 9), (10, 2, 5), (7, 6, 9), (4, 2, 5), (1, 2, 5)]:
    r.fill(x0, y, x1, y, '=')
r.fill(19, 9, 22, 20)                      # pillar (top = ledge to the secret)
r.fill(11, 3, 12, 13)                      # free column: wall-jump between it and the pillar
r.fill(14, 22, 17, 22, '=').fill(8, 19, 10, 19, '=').fill(14, 16, 17, 16, '=')
for x, y, ch in [(16, 15, 'a'), (8, 24, 's'), (8, 8, 'f'), (8, 1, 'l'), (17, 1, 'l'), (2, 24, 'k'), (21, 8, 'u'), (4, 24, 'i')]:
    r.put(x, y, ch)

r = Room('K3s', 'Reliquary of Wings', 'cathedral', 372, 0, 24, 14, indoor=True, secret=True, items=['wings'], chests=['shard'])
r.walls().open('W', 4, 8)
r.fill(0, 9, 23, 13)
for x, y, ch in [(12, 8, 'i'), (18, 8, 'C'), (4, 8, 'k'), (20, 8, 'k'), (8, 1, 'l'), (16, 1, 'l')]:
    r.put(x, y, ch)

r = Room('K4', 'Throne of Ash', 'cathedral', 372, 14, 48, 14, indoor=True, boss='omen')
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
for x, y, ch in [(1, 10, 'F'), (46, 10, 'F'), (34, 10, 'M'), (8, 2, 'l'), (24, 2, 'l'), (40, 2, 'l'), (4, 10, 'k'), (44, 10, 'k')]:
    r.put(x, y, ch)


# ============================================================ THE WEEPING MIRE (below the catacombs)
r = Room('M1', 'Rotting Descent', 'mire', 152, 56, 24, 28, indoor=True, items=['herb'])
r.walls().open('N', 8, 10).open('E', 21, 24)
r.fill(0, 25, 23, 27)
r.fill(7, 2, 11, 2, '=')
for y, x0 in [(4, 12), (7, 5), (10, 12), (13, 5), (16, 12), (19, 6), (22, 12)]:
    r.fill(x0, y, x0 + 4, y, '=')
r.fill(1, 24, 4, 24, '~')
for x, y, ch in [(14, 21, 'p'), (20, 24, 'i'), (4, 1, 'r'), (18, 1, 'l'), (9, 24, 'b')]:
    r.put(x, y, ch)

r = Room('M2', 'The Weeping Mire', 'mire', 176, 70, 48, 14, indoor=True, items=['c_ember', 'emberstone'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(10, 11, 17, 12, '~')
r.fill(28, 11, 37, 12, '~').fill(30, 9, 31, 9, '=').fill(34, 9, 35, 9, '=')
for x, y, ch in [(6, 10, 'p'), (24, 10, 'm'), (43, 10, 'h'), (21, 10, 'i'), (46, 10, 'i'), (5, 2, 'l'), (26, 2, 'l'), (40, 2, 'r'), (14, 2, 'r'), (2, 10, 'b')]:
    r.put(x, y, ch)

r = Room('M3', 'Drowned Chapel', 'mire', 224, 70, 24, 14, indoor=True, shrine='Mire Shrine', graves=['m3'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 23, 13).fill(0, 0, 23, 1)
r.fill(10, 11, 13, 13, '.').fill(10, 11, 13, 11, '=').fill(10, 13, 13, 13, '=')   # trapdoor to the Vessel's pit
for x, y, ch in [(5, 10, 'S'), (18, 10, 'g'), (4, 2, 'l'), (19, 2, 'l'), (21, 10, 'k'), (2, 10, 'k')]:
    r.put(x, y, ch)

r = Room('M6', 'The Vessel\'s Pit', 'mire', 212, 84, 36, 14, indoor=True, boss='vessel')
r.walls().open('N', 22, 25)
r.fill(0, 11, 35, 13)
for y in (8, 5, 2):
    r.fill(22, y, 25, y, '=')
r.fill(28, 11, 34, 12, '~')
for x, y, ch in [(10, 10, 'V'), (3, 1, 'r'), (16, 1, 'r'), (31, 1, 'r'), (2, 10, 'b'), (18, 10, 'b')]:
    r.put(x, y, ch)

r = Room('M4', 'Sunken Road', 'mire', 248, 70, 48, 14, indoor=True, chests=['w:maul'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(8, 11, 40, 12, '~')
for x0 in (10, 16, 22, 28, 34):
    r.fill(x0, 9, x0 + 2, 9, '=')
r.fill(19, 10, 20, 12)                     # a drowned pillar
for x, y, ch in [(6, 10, 'h'), (17, 8, 'p'), (29, 8, 'p'), (44, 10, 'm'), (45, 10, 'C'), (3, 2, 'l'), (24, 2, 'l'), (38, 2, 'r'), (12, 2, 'r')]:
    r.put(x, y, ch)

r = Room('M5', 'Kalden\'s Vigil', 'mire', 296, 70, 36, 14, indoor=True, boss='kalden', graves=['m5'])
r.walls().open('W', 7, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
for x, y, ch in [(1, 10, 'F'), (24, 10, 'Q'), (33, 10, 'g'), (8, 2, 'l'), (27, 2, 'l'), (18, 2, 'r'), (31, 10, 'k')]:
    r.put(x, y, ch)

# ============================================================ THE PALE CROWN (atop the fallen tree, open sky)
r = Room('X1', 'The Bell Gate', 'crown', 420, 14, 24, 14)
r.walls(top=False).fill(0, 11, 23, 13).open('W', 7, 10)
r.fill(1, 0, 17, 0).fill(22, 0, 23, 0)
for y, x0 in [(8, 15), (5, 18), (2, 15)]:
    r.fill(x0, y, x0 + 3, y, '=')
for x, y, ch in [(12, 7, 'G'), (8, 10, 'O'), (3, 10, 'k'), (20, 10, 'o')]:
    r.put(x, y, ch)
r.fill(12, 1, 12, 6)          # wall above the gate up to the ceiling: no jumping over it

r = Room('X2', 'Pale Ascent', 'crown', 420, -14, 24, 28, items=['herb'])
r.walls(top=False).open('E', 3, 8)
r.fill(1, 27, 17, 27).fill(22, 27, 22, 27)
r.fill(18, 27, 21, 27, '=')
for y, x0 in [(24, 13), (21, 6), (18, 12), (15, 5), (12, 11)]:
    r.fill(x0, y, x0 + 3, y, '=')
r.fill(16, 9, 22, 13)
for x, y, ch in [(7, 20, 'i'), (9, 12, 'y'), (14, 17, 'o')]:
    r.put(x, y, ch)

r = Room('X3', 'Boughs of the Crown', 'crown', 444, -14, 48, 14, items=['c_veil'], chests=['emberstone'])
r.walls(top=False).open('W', 3, 8).open('E', 7, 10)
r.fill(0, 9, 6, 13).fill(7, 11, 47, 13)
r.fill(20, 7, 24, 7, '=').fill(32, 6, 36, 6, '=')
for x, y, ch in [(14, 10, 'o'), (18, 10, 'o'), (28, 10, 'n'), (34, 3, 'y'), (22, 6, 'i'), (41, 10, 'C'), (10, 10, 'k')]:
    r.put(x, y, ch)

r = Room('X4', 'Crown Shrine', 'crown', 492, -14, 24, 14, shrine='Crown Shrine', npcs=['venn'], graves=['x4'])
r.walls(top=False).open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 23, 13)
for x, y, ch in [(13, 10, 'S'), (8, 10, 'N'), (19, 10, 'g'), (3, 10, 'k')]:
    r.put(x, y, ch)

r = Room('X5', 'Heart of the Pale Root', 'crown', 516, -14, 48, 14, boss='sovereign')
r.walls(top=False).open('W', 7, 10)
r.fill(0, 11, 47, 13)
for x, y, ch in [(1, 10, 'F'), (30, 10, 'Z'), (44, 10, 'T')]:
    r.put(x, y, ch)


# ============================================================ THE ASHEN ARCHIVES (library tower above the Bell Ascent)
r = Room('A1', 'The Lower Stacks', 'archives', 348, -28, 24, 28, indoor=True, items=['emberstone'])
r.walls().open('S', 2, 5).open('W', 3, 8)
r.fill(2, 26, 6, 26, '=')
r.fill(1, 9, 5, 13)                          # ledge to the western door
for y, x0, x1 in [(23, 7, 11), (20, 13, 17), (17, 18, 21), (14, 12, 15), (11, 6, 9)]:
    r.fill(x0, y, x1, y, '=')
for x, y, ch in [(12, 15, 'q'), (3, 8, 'd'), (19, 16, 'i'), (8, 1, 'l'), (16, 1, 'x'), (20, 1, 'l'), (4, 8, 'k'), (14, 26, 'E'), (11, 1, 'R')]:
    r.put(x, y, ch)

r = Room('A2', 'Reading Galleries', 'archives', 300, -28, 48, 14, indoor=True, shrine='Archive Shrine', items=['herb'])
r.walls().open('E', 3, 8).open('W', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1).fill(40, 9, 47, 10)
r.fill(16, 7, 20, 7, '=').fill(26, 7, 30, 7, '=')
for x, y, ch in [(44, 8, 'S'), (30, 10, 'j'), (12, 10, 'j'), (23, 5, 'q'), (18, 6, 'i'), (6, 2, 'l'), (24, 2, 'l'), (36, 2, 'x'), (3, 10, 'k'), (35, 10, 'b'), (8, 10, 'E'), (20, 10, 'I'), (38, 10, 'I'), (15, 2, 'R'), (29, 2, 'R')]:
    r.put(x, y, ch)

r = Room('A3', 'The Scriptorium', 'archives', 276, -28, 24, 14, indoor=True, boss='librarian', entry='E')
r.walls().open('E', 7, 10).open('W', 7, 10)
r.fill(0, 11, 23, 13).fill(0, 0, 23, 1)
for x, y, ch in [(22, 10, 'F'), (1, 10, 'F'), (9, 10, 'J'), (5, 2, 'l'), (18, 2, 'l'), (12, 2, 'x'), (4, 10, 'I'), (18, 10, 'I')]:
    r.put(x, y, ch)

r = Room('A4', 'Spiral of Shelves', 'archives', 252, -42, 24, 28, indoor=True, chests=['emberstone'])
r.walls().open('E', 21, 24).open('E', 3, 8)
r.fill(0, 25, 23, 27).fill(18, 9, 22, 13)
for y, x0, x1 in [(22, 14, 18), (19, 8, 12), (16, 13, 17), (13, 7, 11), (10, 12, 16)]:
    r.fill(x0, y, x1, y, '=')
for x, y, ch in [(9, 12, 'q'), (15, 6, 'q'), (9, 18, 'C'), (4, 1, 'l'), (19, 1, 'l'), (3, 24, 'k'), (20, 8, 'j')]:
    r.put(x, y, ch)

r = Room('A5', 'Chained Stacks', 'archives', 276, -42, 48, 14, indoor=True, shrine='Inkwell Shrine', chests=['shard'], graves=['a5'])
r.walls().open('W', 3, 8).open('E', 7, 10)
r.fill(0, 9, 5, 13).fill(6, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(22, 7, 26, 7, '=')
for x, y, ch in [(3, 8, 'S'), (20, 10, 'd'), (32, 10, 'd'), (40, 10, 'j'), (24, 6, 'C'), (14, 10, 'g'), (10, 2, 'l'), (30, 2, 'l'), (44, 10, 'k'), (12, 10, 'E'), (27, 10, 'I'), (36, 2, 'R')]:
    r.put(x, y, ch)

r = Room('A6', 'The Inkwell', 'archives', 324, -42, 36, 14, indoor=True, boss='unwritten')
r.walls().open('W', 7, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
for x, y, ch in [(1, 10, 'F'), (24, 10, 'W'), (8, 2, 'l'), (18, 2, 'x'), (28, 2, 'l'), (33, 10, 'k')]:
    r.put(x, y, ch)

# ============================================================ TEST CHAMBER (debug only, sealed, reached via __game.tp)
r = Room('T0', 'Proving Grounds', 'crown', -200, 0, 48, 20, indoor=True, test=True)
r.walls().fill(0, 17, 47, 19)
r.fill(12, 17, 17, 18, 'Y')                        # cracked floor over a pit
r.fill(12, 19, 17, 19, '#')
r.fill(22, 10, 22, 16, '%')                        # ash veil wall
r.fill(22, 1, 22, 9)                               # wall above it
r.fill(30, 4, 30, 16, '|')                         # updraft column
r.fill(33, 5, 38, 5, '=')                          # ledge only the updraft reaches
for x, y in [(6, 7), (41, 6)]:
    r.put(x, y, '@')
r.fill(40, 10, 47, 16).fill(39, 1, 39, 5)
for x, y, ch in [(3, 16, 's'), (26, 16, 's')]:
    r.put(x, y, ch)

# ============================================================ region modules (tools/regions/*.py, loaded in name order)
# Each module runs in this namespace: use Room(...), SOLID, GROUNDED, FLYING and patch existing rooms via ROOM('R4').
def ROOM(id):
    return next(R for R in ROOMS if R.id == id)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reach as _reach   # tools/reach.py (KS): placement helper + reachability
def free_spot(near_gx, near_gy, w, h, zone, margin=0):
    """nearest free w x h spot (top-left gx, gy) inside zone ('Spire' or (x0, x1, y0, y1)) that overlaps no room built so far"""
    return _reach.free_spot(ROOMS, near_gx, near_gy, w, h, zone, margin)
HAZARD = set('^v*(')    # touch = hurt (reachability treats these as deadly); regions may add chars
GROUNDED = set('PSswcaeKuCiLHMFNAOTgVQZhmnodjJWEI')
FLYING = set()          # enemy types in spawns= that don't need ground under them
_rdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'regions')
if os.path.isdir(_rdir):
    for _fn in sorted(os.listdir(_rdir)):
        if _fn.endswith('.py'):
            try:
                exec(compile(open(os.path.join(_rdir, _fn)).read(), _fn, 'exec'), globals())
            except Exception as _e:
                print(f'REGION MODULE ERROR {_fn}: {_e!r}')

# ---- the shafts that rejoin the regions the world layout pulled apart (upper room, lower room)
WORLD_LINKS = [('R3', 'SP1', 'W1', 'The Sea-Wall Climb', 'spire'), ('C2', 'NV1', 'W2', 'The Ossuary Well', 'necropolis'),
               ('C3', 'M1', 'W3', 'The Root Drop', 'mire'), ('K2', 'DB1', 'W4', 'The Drowned Shaft', 'barrows'),
               ('K3', 'A1', 'W5', 'The Ink Stair', 'archives'), ('X4', 'SF1', 'W6', 'The Sky Stair', 'starfall')]
def _world_shafts():
    for a, b, wid, name, biome in WORLD_LINKS:
        A, B = ROOM(a), ROOM(b)
        up, lo = (A, B) if A.gy < B.gy else (B, A)
        top, bot = up.gy + up.h, lo.gy
        if bot <= top: continue
        cols = [x for x in range(max(up.gx, lo.gx), min(up.gx + up.w, lo.gx + lo.w))
                if up.g[up.h - 1][x - up.gx] not in SOLID and lo.g[0][x - lo.gx] not in SOLID]
        if not cols: print(f'WORLD LINK {a}-{b}: no shared opening'); continue
        x0, x1 = min(cols) - 1, max(cols) + 1
        while x1 - x0 + 1 < 6: x1 += 1
        w, h = x1 - x0 + 1, bot - top
        r = Room(wid, name, biome, x0, top, w, h, indoor=True, x3=True, world_link=True, needs=[])
        r.fill(0, 0, 0, h - 1).fill(w - 1, 0, w - 1, h - 1).fill(0, 0, w - 1, 0).fill(0, h - 1, w - 1, h - 1)
        for x in cols: r.g[0][x - x0] = '.'; r.g[h - 1][x - x0] = '.'
        # zigzag one-way ledges every 3 rows, so the climb back up needs nothing but a jump
        inner = w - 2; lw = max(2, min(4, inner // 2 + 1))
        for i, y in enumerate(range(h - 4, 2, -3)):
            xa = 1 if i % 2 == 0 else w - 1 - lw
            r.fill(xa, y, xa + lw - 1, y, '=')
_world_shafts()

# ============================================================ validation
def cell(gx, gy):
    for R in ROOMS:
        if R.gx <= gx < R.gx + R.w and R.gy <= gy < R.gy + R.h:
            return R, R.g[gy - R.gy][gx - R.gx]
    return None, None


def validate():
    errs = []
    ids = [R.id for R in ROOMS]
    errs += [f'duplicate room id {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]
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
            if ch in SOLID and ch not in 'BY': continue
            O, och = cell(R.gx + x + dx, R.gy + y + dy)
            if O is None:
                if dy == -1 and not R.kw.get('indoor'): continue      # open sky
                errs.append(f'{R.id}: leak at ({x},{y}) dir ({dx},{dy})')
            elif och in SOLID and och not in 'BY':
                errs.append(f'{R.id}: opening ({x},{y}) blocked by {O.id}')
        n_i = sum(row.count('i') for row in R.rows()); n_c = sum(row.count('C') for row in R.rows())
        if n_i != len(R.kw.get('items', [])): errs.append(f'{R.id}: {n_i} item cells vs {R.kw.get("items")}')
        if n_c != len(R.kw.get('chests', [])): errs.append(f'{R.id}: {n_c} chest cells vs {R.kw.get("chests")}')
        for y, row in enumerate(R.rows()):
            for x, ch in enumerate(row):
                grounded = ch in GROUNDED
                if grounded and (y + 1 >= R.h or R.g[y + 1][x] not in SOLID | {'='}):
                    errs.append(f'{R.id}: {ch} at ({x},{y}) not standing on ground')
        for s in R.kw.get('spawns', []):
            x, y = s['x'], s['y']
            if not (0 <= x < R.w and 0 <= y < R.h): errs.append(f'{R.id}: spawn {s} outside room'); continue
            if R.g[y][x] in SOLID: errs.append(f'{R.id}: spawn {s} inside solid')
            if s.get('ground', s.get('t') in ('enemy', 'boss', 'prop')) and s.get('type') not in FLYING and not s.get('air') and (y + 1 >= R.h or R.g[y + 1][x] not in SOLID | {'='}):
                errs.append(f'{R.id}: spawn {s.get("type") or s.get("kind")} at ({x},{y}) not standing on ground')
    errs += validate_sys()
    return errs


# ---- Expansion 3 systems (KS): door pairs, sys spawns, reachability (tools/reach.py)
SYS_KINDS = {'door', 'passage', 'trial', 'trial_goal', 'gauntlet', 'bench', 'lore'}
SYS_GROUNDED = {'door', 'trial', 'trial_goal', 'bench', 'lore', 'gauntlet'}
def validate_sys():
    errs = []
    by = {R.id: R for R in ROOMS}
    def door_of(R, id):
        return next((s for s in R.kw.get('spawns', []) if s.get('t') == 'sys' and s.get('kind') == 'door' and s.get('id') == id), None)
    for R in ROOMS:
        sp = [s for s in R.kw.get('spawns', []) if s.get('t') == 'sys']
        ids = {}
        for s in sp:
            k, x, y = s.get('kind'), s.get('x'), s.get('y')
            tag = f"sys {k} {s.get('id') or s.get('page') or s.get('trial') or ''}".rstrip()
            if k not in SYS_KINDS: errs.append(f'{R.id}: {tag}: unknown sys kind'); continue
            if k in ('door', 'trial', 'gauntlet') and not s.get('id'): errs.append(f'{R.id}: {tag}: needs an id'); continue
            if s.get('id'):
                key = (k if k != 'trial_goal' else 'goal', s['id'])
                if key in ids: errs.append(f'{R.id}: {tag}: duplicate id')
                ids[key] = s
            if k in SYS_GROUNDED and 0 <= x < R.w and 0 <= y < R.h:
                if R.g[y][x] in SOLID or (y > 0 and R.g[y - 1][x] in SOLID): errs.append(f'{R.id}: {tag} at ({x},{y}): its cell or the one above is solid')
                elif y + 1 >= R.h or R.g[y + 1][x] not in SOLID | {'='}: errs.append(f'{R.id}: {tag} at ({x},{y}) not standing on ground')
            if k == 'door':
                to, toId = s.get('to'), s.get('toId', s.get('id'))
                if to not in by: errs.append(f"{R.id}: door {s['id']} -> {to}:{toId}: no such room"); continue
                t = door_of(by[to], toId)
                if not t: errs.append(f"{R.id}: door {s['id']} -> {to}:{toId}: the partner door doesn't exist")
                elif t.get('to') != R.id or t.get('toId', t.get('id')) != s['id']: errs.append(f"{R.id}: door {s['id']} -> {to}:{toId}: the partner points to {t.get('to')}:{t.get('toId', t.get('id'))}, not back here")
            elif k == 'trial_goal':
                if not any(q.get('kind') == 'trial' and q.get('id') == s.get('trial') for q in sp): errs.append(f"{R.id}: {tag}: no trial sigil with id {s.get('trial')!r} in this room")
            elif k == 'trial':
                if not any(q.get('kind') == 'trial_goal' and q.get('trial') == s.get('id') for q in sp): errs.append(f'{R.id}: {tag}: no trial_goal for it')
            elif k == 'gauntlet':
                if not s.get('waves'): errs.append(f'{R.id}: {tag}: no waves')
                kit_ids = {q.get('id') for q in R.kw.get('spawns', []) if q.get('t') == 'kit' and q.get('kind') == 'gate'}
                for g in s.get('gates', []):
                    if g not in kit_ids: errs.append(f'{R.id}: {tag}: gate {g!r} is not a kit gate in this room')
                for wi, w in enumerate(s.get('waves', [])):
                    for e in w:
                        if not (0 <= e.get('x', -1) < R.w and 0 <= e.get('y', -1) < R.h) or R.g[e['y']][e['x']] in SOLID: errs.append(f'{R.id}: {tag}: wave {wi + 1} spawn {e} is outside the room or in rock')
            elif k == 'lore':
                if not isinstance(s.get('page'), str) or not s.get('page'): errs.append(f'{R.id}: {tag}: needs page=<LORE_PAGES id>')
            elif k == 'passage':
                w, h = s.get('w', 1), s.get('h', 3)
                cells = [(xx, yy) for yy in range(y - h + 1, y + 1) for xx in range(x, x + w)]
                bad = next((c for c in cells if not (0 <= c[0] < R.w and 0 <= c[1] < R.h)), None)
                if bad: errs.append(f'{R.id}: {tag}: cell {bad} outside the room')
                elif any(R.g[yy][xx] in SOLID for xx, yy in cells): errs.append(f'{R.id}: {tag}: its cells must be open in the map (the engine walls them up while closed)')
    return errs


def validate_reach():
    """(errors, warnings) from tools/reach.py: ERR for rooms with needs/x3, WARN for old rooms"""
    if os.environ.get('NOREACH'): return [], []
    msgs = _reach.check_all(ROOMS, cell, SOLID, ''.join(sorted(HAZARD)))
    return [m for l, m in msgs if l == 'ERR'], [m for l, m in msgs if l != 'ERR']


if __name__ == '__main__':
    if '--zones' in sys.argv:
        print(_reach.zones_report(ROOMS, _reach.ZONES)); sys.exit(0)
    errs = validate()
    rerrs, rwarns = validate_reach()
    errs += rerrs
    for e in errs: print('ERR', e)
    for w in rwarns: print('WARN', w)
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
    sys.exit(1 if errs and os.environ.get('STRICT') else 0)
