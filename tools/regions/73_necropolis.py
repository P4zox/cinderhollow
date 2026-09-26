# ============================================================ THE NECROPOLIS OF VAEL (agent N) — a vertical city of the dead
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Zone x -60..149, y 57..140 (the connector NV1 starts at y 56: C2's floor is y 53..55, so row 56 must belong to it).
# Entered through C2's floor (a double grate at C2 cols 36..38, like the Mire trapdoor in C3). Gate: the Ossuary Sump's
# drowned U-bend under a wall (B's deep-water tile '"', needs Tidebreath); a lever on the far side opens a dry gate
# (shortcut). Second shortcut: the Sealed Stair from the Charnel Gate shrine down to the Tolling Streets (lever gate).
# Tiles: '{' bell walkway A, '}' bell walkway B (ids 50/51) — solid only while their bell phase holds; web/src/33_necropolis.js.
# Custom spawns: nv_bell (a tolling great bell), nv_plat (bell-hung platform that shifts on each toll), nv_prop (decor),
# enemies nv_noble / nv_ringer / nv_hound, bosses executioners (NV5) and vael (NV7).
SOLID.update('{}')


def _nv_deco(kind, x, y, **kw):
    return dict(t='nv_prop', kind=kind, x=x, y=y, **kw)


def _nv_blank(r):
    r.fill(0, 0, r.w - 1, r.h - 1)
    return r


# ---------------------------------------------------------------- C2 (anchor): a grated trapdoor in the Ossuary floor
_c2 = ROOM('C2')
_c2.fill(36, 11, 38, 13, '.').fill(36, 11, 38, 11, '=').fill(36, 13, 38, 13, '=')   # global x 84..86

# ---------------------------------------------------------------- NV1 The Ossuary Sump (connector + the drowned gate)
r = Room('NV1', 'The Ossuary Sump', 'necropolis', 72, 56, 24, 30, indoor=True, items=['emberstone'], graves=['nv1'],
         spawns=[_nv_deco('candles', 3, 21), _nv_deco('skulls', 14, 21), _nv_deco('candles', 22, 21),
                 _nv_deco('brazier', 9, 21)])
_nv_blank(r)
r.fill(6, 1, 15, 17, '.')                  # the shaft
r.fill(12, 0, 14, 0, '.')                  # under C2's grate (global x 84..86)
r.fill(2, 16, 15, 21, '.')                 # the west landing
r.fill(17, 16, 22, 21, '.').fill(23, 18, 23, 21, '.')   # the east chamber -> the Charnel Gate
r.fill(16, 19, 16, 21, '.').put(16, 18, 'G')            # the dry gate (lever on the far side)
for y, x0, x1 in [(2, 12, 14), (5, 11, 15), (8, 7, 9), (11, 11, 13), (14, 7, 9), (17, 11, 13), (20, 7, 9)]:
    r.fill(x0, y, x1, y, '=')
# the drowned U-bend: west pool, the tunnel under the wall, east pool
r.fill(3, 22, 7, 27, '"').fill(3, 25, 19, 27, '"').fill(17, 22, 19, 27, '"')
r.fill(6, 25, 7, 25, "=").fill(17, 25, 18, 25, "=")       # rests inside the pools (only matter when you can't swim)
# (a bone grate over the east pool is a one-way dyn platform in 33_necropolis.js: B floods '=' cells that touch water)
r.put(21, 21, 'L').put(10, 21, 'i').put(13, 21, 'g')
for x, y, ch in [(8, 1, 'x'), (4, 16, 'x'), (20, 16, 'x')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- NV2 The Charnel Gate (first shrine; grate down the Sealed Stair)
r = Room('NV2', 'The Charnel Gate', 'necropolis', 96, 67, 34, 14, indoor=True, shrine='Charnel Shrine', items=['emberstone'],
         graves=['nv2'],
         spawns=[dict(t='enemy', type='nv_hound', x=28, y=10), _nv_deco('statue', 11, 10), _nv_deco('candles', 3, 10),
                 _nv_deco('coffin', 26, 10), _nv_deco('brazier', 15, 10), _nv_deco('brazier', 31, 10),
                 _nv_deco('banner', 9, 2), _nv_deco('banner', 25, 2)])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 33, 13).fill(0, 0, 33, 1)
r.fill(19, 11, 23, 13, '.').fill(19, 11, 23, 11, '=')    # the Sealed Stair grate (global x 115..119)
r.fill(12, 8, 15, 8, '=')
r.put(6, 10, 'S').put(14, 7, 'i').put(3, 10, 'g')
for x, y, ch in [(18, 2, 'x'), (30, 2, 'x'), (27, 10, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- NVs The Sealed Stair (shortcut shaft: fall straight down the middle)
r = Room('NVs', 'The Sealed Stair', 'necropolis', 114, 81, 7, 10, indoor=True)
r.walls().open('N', 1, 5).open('S', 1, 5)
for y, x0 in [(0, 1), (3, 4), (6, 1), (9, 4)]:
    r.fill(x0, y, x0 + 1, y, '=')

# ---------------------------------------------------------------- NV3 The Bone Spire (bell bridges; the great bell tolls them in and out)
r = Room('NV3', 'The Bone Spire', 'necropolis', 130, 66, 20, 46, indoor=True, items=['emberstone'],
         bells=dict(every=6.0, warn=1.4),
         spawns=[dict(t='nv_bell', x=10, y=1, big=1),
                 dict(t='enemy', type='nv_ringer', x=15, y=23), dict(t='enemy', type='nv_hound', x=4, y=35),
                 dict(t='enemy', type='nv_noble', x=15, y=11),
                 _nv_deco('candles', 2, 11), _nv_deco('skulls', 16, 29), _nv_deco('candles', 5, 41), _nv_deco('brazier', 12, 41)])
_nv_blank(r)
r.fill(1, 1, 18, 44, '.')
r.fill(0, 8, 0, 11, '.')                   # <- the Charnel Gate
r.fill(0, 38, 0, 41, '.')                  # <- the Tolling Streets
r.fill(0, 42, 19, 45)                      # floor
A, B = '{', '}'
for y, kind in [(12, 'A'), (18, 'B'), (24, 'A'), (30, 'B'), (36, 'A')]:
    if kind == 'A':   # west ledge, bridge A, east ledge, gap at the east wall
        r.fill(0 if y == 12 else 1, y, 5, y).fill(6, y, 11, y, A).fill(12, y, 16, y)
    else:             # gap at the west wall, west ledge, bridge B, east ledge
        r.fill(3, y, 7, y).fill(8, y, 12, y, B).fill(13, y, 18, y)
for y, x0 in [(15, 17), (21, 1), (27, 17), (33, 1), (39, 17)]:   # climbing rests under each gap
    r.fill(x0, y, x0 + 1, y, '=')
r.fill(14, 6, 18, 6, B)                    # a bell-walkway alcove high on the east wall (loot)
r.fill(11, 9, 12, 9, '=')                  # step up to it from the first east ledge
r.put(17, 5, 'i')
for x, y, ch in [(3, 1, 'x'), (16, 1, 'x'), (9, 41, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- NV4 The Tolling Streets (bridges, a bell-hung platform, the sealed stair's gate)
r = Room('NV4', 'The Tolling Streets', 'necropolis', 58, 91, 72, 20, indoor=True, chests=['w:gravechain'], shrine='Yard Gate Shrine',
         bells=dict(every=5.5, warn=1.4),
         spawns=[dict(t='nv_bell', x=31, y=2),
                 dict(t='nv_plat', x=36, y=17, w=3, dx=7),
                 dict(t='enemy', type='nv_noble', x=12, y=16), dict(t='enemy', type='nv_noble', x=50, y=16),
                 dict(t='enemy', type='nv_ringer', x=66, y=16), dict(t='enemy', type='nv_hound', x=30, y=16),
                 dict(t='enemy', type='nv_ringer', x=27, y=8),
                 _nv_deco('statue', 9, 16), _nv_deco('coffin', 17, 16), _nv_deco('banner', 12, 2), _nv_deco('banner', 48, 2),
                 _nv_deco('brazier', 33, 16), _nv_deco('brazier', 54, 16), _nv_deco('candles', 68, 16), _nv_deco('skulls', 64, 16),
                 _nv_deco('candles', 31, 8), _nv_deco('skulls', 17, 8)])
r.walls().open('W', 13, 16).open('E', 13, 16)
r.fill(0, 17, 71, 19).fill(0, 0, 71, 1)
# pit 1: spikes, bridged by walkway A
r.fill(20, 17, 27, 18, '.').fill(20, 18, 27, 18, '^').fill(20, 17, 27, 17, A)
# pit 2: spikes, crossed on the bell-hung platform (it shifts 7 tiles on each toll)
r.fill(36, 17, 45, 18, '.').fill(36, 18, 45, 18, '^')
# rooftops: an upper route over pit 1 to the gravechain chest
r.fill(14, 9, 19, 9, '=')                                 # a bone roof
r.fill(9, 14, 11, 14, '=').fill(12, 12, 13, 12, '=')
r.fill(20, 9, 25, 9, B).fill(26, 9, 31, 9, '=')           # walkway B to the bell loft
r.fill(32, 12, 34, 12, '=').fill(33, 15, 35, 15, '=')     # steps down off the loft
r.put(30, 8, 'C')
# the Sealed Stair's attic: the shaft ends in a sealed chamber above the street; its gate opens onto a ledge (lever there)
r.fill(56, 0, 56, 5).fill(56, 5, 67, 5)
r.put(62, 1, 'G').put(65, 4, 'L')
r.fill(57, 2, 58, 2, '=')
r.fill(66, 14, 68, 14, '=').fill(69, 11, 70, 11, '=').fill(68, 8, 69, 8, '=')      # climb from the street to the ledge
r.fill(57, 0, 61, 1, '.')                                 # open to the stair above
for x, y, ch in [(40, 2, 'x'), (6, 2, 'x'), (67, 2, 'x'), (52, 16, 'b'), (5, 16, 'S')]:   # shrine before the Headsman's Yard
    r.put(x, y, ch)

# ---------------------------------------------------------------- NV5 The Headsman's Yard (the Twin Executioners)
r = Room('NV5', 'The Headsman\'s Yard', 'necropolis', 22, 97, 36, 14, indoor=True, boss='executioners', entry='E',
         spawns=[dict(t='boss', kind='executioners', x=12, y=10),
                 _nv_deco('block', 8, 10), _nv_deco('gallows', 24, 10), _nv_deco('brazier', 4, 10), _nv_deco('brazier', 30, 10)])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
for x, y, ch in [(1, 10, 'F'), (34, 10, 'F'), (10, 2, 'x'), (18, 2, 'x'), (26, 2, 'x'), (15, 10, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- NV6 The Hollow Court (second shrine, the court of hollow nobles)
r = Room('NV6', 'The Hollow Court', 'necropolis', -14, 93, 36, 18, indoor=True, shrine='Court Shrine', items=['c_court'],
         chests=['shard', 'emberstone'], graves=['nv3', 'nv4'],
         spawns=[dict(t='enemy', type='nv_noble', x=12, y=14), dict(t='enemy', type='nv_noble', x=20, y=7),
                 dict(t='enemy', type='nv_ringer', x=8, y=7),
                 _nv_deco('banner', 6, 2), _nv_deco('banner', 18, 2), _nv_deco('banner', 29, 2),
                 _nv_deco('statue', 31, 14), _nv_deco('brazier', 15, 14), _nv_deco('candles', 33, 14), _nv_deco('coffin', 23, 14)])
r.walls().open('W', 11, 14).open('E', 11, 14)
r.fill(0, 15, 35, 17).fill(0, 0, 35, 1)
r.fill(4, 8, 24, 8).fill(24, 9, 24, 10)                  # the gallery of the court
r.fill(25, 12, 27, 12, '=').fill(25, 9, 27, 9, '=')     # up to the gallery
r.put(5, 14, 'S').put(14, 7, 'i').put(5, 7, 'C').put(21, 14, 'C').put(26, 14, 'g').put(10, 7, 'g')   # the Court Shrine sits by the throne-room door
for x, y, ch in [(12, 2, 'x'), (24, 2, 'x')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- NV7 The Hollow Throne (King Vael)
r = Room('NV7', 'The Hollow Throne', 'necropolis', -60, 95, 46, 16, indoor=True, boss='vael', entry='E',
         spawns=[dict(t='boss', kind='vael', x=16, y=12),
                 _nv_deco('throne', 5, 12), _nv_deco('brazier', 11, 12), _nv_deco('brazier', 36, 12),
                 _nv_deco('banner', 9, 2), _nv_deco('banner', 22, 2), _nv_deco('banner', 35, 2)])
r.walls().open('E', 9, 12)
r.fill(0, 13, 45, 15).fill(0, 0, 45, 1)
for x, y, ch in [(44, 12, 'F'), (16, 2, 'x'), (29, 2, 'x')]:
    r.put(x, y, ch)
