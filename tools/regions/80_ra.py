# ============================================================ EXPANSION 3 · agent RA: Ashen Ramparts, Rootbound Catacombs, Sunken Cathedral
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, free_spot). Engine: web/src/50_ra.js.
# Decor spawns: {t:'ra', k:<prop>, x, y, ...} (painted into the back layer or drawn as props; see 50_ra.js RA_PROPS).
# Special spawns: ra_amb (statue / booth ambushers), ra_chand (restyles a kit crumble as a chandelier), ra_water (black
# knee-deep water), ra_wall (painted back walls inside outdoor rooms), ra_hint (puzzle hint toasts).
#
# ASHEN RAMPARTS (zone x -112..15, y -90..-1; outdoor walls above the first shrine)
#   RA wing: R2 --arch door--> R5 Long Wall (grand) -> R6 Stable Yard -> R7 Barracks -> R8 Siege Undercroft
#            -> winch lift (lever above, one-way the first time) -> ladder door -> R1 (first shrine)
#   R5 west tower -> R9 Signal Tower Stair -> R10 Crenel Run (parkour) -> R11 Watcher's Perch (vista)
#   side rooms: R12 Winch House (puzzle, off R8), R13 Muster Yard (gauntlet, under R6), R14 Sentry's Cache (secret, behind
#   a cracked wall in R5's stables)
# ROOTBOUND CATACOMBS (zone x -299..-113, y 43..112; door-linked pocket)
#   C1 --crack door--> C7 Rootbound Passage -> C8 Great Ossuary (grand) -> C9 Drop Shaft -> C10 Burial Tunnels
#            -> gate (lever inside, one-way the first time) -> crack door -> C4 (Rootgate Shrine)
#   side rooms: C11 Bone Lift Shaft (parkour, off C8; its top gallery is the Ossuary's hidden upper route), C12 Crypt of
#   Lanterns (puzzle, off C9), C13 Charnel Pit (gauntlet, off C9), C14 Gravedigger's Stash (secret: false tomb in C10),
#   C15 The Sealed Niche (secret: Cinder Slam floor in C8)
# SUNKEN CATHEDRAL (zone x 372..491, y -160..-15; above the Crown's open sky, which stays clear at y -15)
#   K1 --arch door--> K5 Pilgrims' Aisle -> K6 Flooded Crypt Stair -> K7 The Clerestory (grand) -> K8 Confessional Row
#            -> gate (lever inside) -> arch door -> K3 (Bell Ascent)
#   side rooms: K9 Chandelier Crossing (parkour, K6 <-> K8), K10 Organ Loft (puzzle), K11 The Rose Window (vista),
#   K12 Bellrope Trial (double jump), K13 The Walled Sacristy (secret, behind the altar)


def _ra_paint(r, rows, marks=None):
    """rows: ASCII map; digits (and marks' keys) are placeholders stripped to '.' and turned into spawns at that cell."""
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    marks = marks or {}
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            if ch in marks:
                m = marks[ch]
                for s in (m if isinstance(m, list) else [m]):
                    r.kw['spawns'].append(dict(s, x=x + s.get('dx', 0), y=y + s.get('dy', 0)))
                ch = '.'
            r.g[y][x] = ch
    for s in r.kw['spawns']: s.pop('dx', None); s.pop('dy', None)
    return r


def _ra_room(id, name, biome, gx, gy, w, h, **kw):
    kw.setdefault('x3', True); kw.setdefault('needs', ['start']); kw.setdefault('spawns', [])
    return Room(id, name, biome, gx, gy, w, h, **kw)


def D(kind, **kw): return dict(t='ra', k=kind, **kw)          # decor
def KT(kind, **kw): return dict(t='kit', kind=kind, **kw)     # kit mechanic
def SY(kind, **kw): return dict(t='sys', kind=kind, **kw)     # kit system
def EN(type_, **kw): return dict(t='enemy', type=type_, **kw)


def _add(r, *spawns):
    r.kw.setdefault('spawns', []).extend(spawns)


def _put(r, pts):
    for x, y, ch in pts: r.put(x, y, ch)


# ================================================================================================ ASHEN RAMPARTS
# Final coordinates (EXPANSION3 §8.1: x -112..99, y -69..-1). The Long Wall is the sky over the first two old rooms: its
# lower rows are open air above R1/R2, so falling off its sally port lands you at the first shrine.
#   in:   R3 (Gatehouse Tower) -> a stair up through its roof -> R5's east shaft
#   out:  R8's lower tunnel -> R5's sally port -> drop onto R1 beside the shrine (the lift in R8 is the shortcut's lock)
# ---------------------------------------------------------------- R5 The Long Wall (grand): high wall-walk, low stables
r = _ra_room('R5', 'The Long Wall', 'ramparts', -28, -22, 128, 22, grand=True, shrine='Shrine of the Wall-Walk')
r.fill(0, 0, 1, 16).fill(127, 0, 127, 21)                     # the west tower's outer wall; the east edge
r.fill(0, 0, 23, 0).fill(9, 0, 12, 0, '.')                    # tower roof; the stair up into R9
r.fill(0, 1, 1, 4, '.')                                       # tower door -> the Barracks (R7)
r.fill(22, 1, 23, 14).fill(22, 5, 23, 8, '.').fill(22, 11, 23, 14, '.')   # tower east wall: doors onto the walk and the stables
r.fill(2, 5, 8, 5)                                            # landing inside the Barracks door
for y, x0, x1 in [(12, 3, 6), (9, 9, 21), (6, 14, 18), (3, 6, 10), (1, 9, 12)]:
    r.fill(x0, y, x1, y, '=')                                 # tower stair
r.fill(24, 9, 118, 10).fill(0, 15, 119, 16)                   # the wall-walk; the wall's base (stables floor)
for x0, x1 in [(36, 40), (70, 74), (86, 90)]:                 # collapsed spans: the walk fell into the stables
    r.fill(x0, 9, x1, 10, '.').fill(x0 + 1, 9, x1 - 1, 9, '=').fill(x0 + 1, 11, x1 - 1, 11, '=').fill(x0, 13, x1, 14)
r.fill(0, 20, 29, 21)                                         # the sally port under the wall (R8 -> R5 -> a drop onto R1)
r.fill(24, 17, 29, 19, '.')
r.fill(48, 2, 53, 5).fill(108, 2, 113, 5)                     # gatehouse arches over the walk (archers on top)
for y, x0, x1 in [(6, 43, 46), (4, 44, 47), (6, 114, 117), (4, 114, 117)]:
    r.fill(x0, y, x1, y, '=')
r.fill(119, 9, 126, 9, '=')                                   # the east stair out of the Gatehouse Tower
for y, x0, x1 in [(12, 122, 125), (15, 119, 122), (18, 122, 125)]:
    r.fill(x0, y, x1, y, '=')
r.fill(123, 21, 124, 21).fill(125, 21, 126, 21, '=')         # the roof hatch of R3 (one-way: ↓+jump drops back in)
_put(r, [(30, 8, 's'), (62, 8, 'w'), (96, 8, 's'), (50, 1, 'a'), (111, 1, 'a'), (30, 14, 'c'), (47, 14, 'c'), (66, 14, 's'), (81, 14, 'c'),
         (26, 8, 'u'), (102, 8, 'u'), (104, 8, 'S'), (116, 14, 'b'), (8, 14, 'k'), (15, 14, 'b'), (5, 2, 'x'), (18, 2, 'x'), (3, 4, 'l'), (18, 1, 'l'),
         (12, 19, 'k'), (4, 19, 'b'), (20, 17, 'l')])
_add(r, SY('lore', x=52, y=14, page='ra_2', look='corpse'),
     dict(t='ra_hint', x=125, y=20, near=24, text='Hold ↓ and press jump to drop back into the Gatehouse Tower.'),
     dict(t='ra_hint', x=27, y=19, near=40, text='The sally port ends in air. Far below: the Shrine of First Ash.'))

# ---------------------------------------------------------------- R9 Signal Tower Stair (on the Long Wall's west tower)
r = _ra_room('R9', 'Signal Tower Stair', 'ramparts', -28, -50, 24, 28, indoor=True, ra_bg=0.94, chests=['gold'])
r.walls().fill(0, 26, 23, 27).fill(9, 26, 12, 27, '.').fill(9, 26, 12, 26, '=')
r.open('E', 4, 7)
for y, x0, x1 in [(23, 13, 22), (20, 1, 10), (17, 13, 22), (14, 1, 10), (8, 15, 22), (5, 1, 8)]:
    r.fill(x0, y, x1, y + 1)
r.fill(9, 11, 13, 11, '=').fill(9, 5, 12, 5, '=')
r.fill(22, 19, 22, 22, 'B').fill(23, 19, 23, 22, '.')         # the cracked wall: the Sentry's Cache is behind it
_put(r, [(18, 22, 's'), (5, 19, 's'), (19, 16, 'a'), (4, 13, 's'), (2, 4, 'C'), (6, 1, 'l'), (17, 1, 'l'), (20, 25, 'k'), (2, 25, 'b')])
_add(r, dict(t='ra_hint', x=19, y=22, near=40, text='The mortar here is cracked and dry. A few good blows might bring it down.'))

# ---------------------------------------------------------------- R10 Crenel Run (parkour): broken battlements over the stakes
r = _ra_room('R10', 'Crenel Run', 'ramparts', -4, -50, 64, 16, parkour=True, chests=['gold'])
r.fill(0, 15, 63, 15).fill(0, 14, 63, 14, '^')
r.fill(0, 0, 0, 3).fill(63, 0, 63, 3)
for x0, x1, top in [(0, 5, 8), (10, 12, 8), (17, 18, 9), (27, 29, 7), (34, 35, 9), (47, 49, 8), (53, 54, 7), (58, 63, 8)]:
    r.fill(x0, top, x1, 14)
_put(r, [(61, 7, 'C')])
_add(r, KT('crumble', x=22, y=8, w=2, delay=0.8), KT('crumble', x=38, y=9, w=2, delay=0.8), KT('crumble', x=42, y=8, w=2, delay=0.8))

# ---------------------------------------------------------------- R11 Watcher's Perch (vista): the highest tower
r = _ra_room('R11', "Watcher's Perch", 'ramparts', 60, -50, 40, 24, vista=True)
r.fill(0, 0, 0, 3).fill(0, 8, 6, 9).fill(0, 10, 1, 23).fill(7, 8, 10, 8, '=').fill(11, 6, 26, 7).fill(15, 8, 21, 23)
r.fill(0, 23, 39, 23).fill(38, 2, 39, 22).fill(39, 0, 39, 1)
_add(r, SY('bench', x=19, y=5, id='bench', view=[29, 9], lore='ra_1'),
     dict(t='ra_void', x=2, y=19, w=36, h=4), dict(t='ra_mist', x=2, y=16, w=36, h=8))

# ---------------------------------------------------------------- R14 Sentry's Cache (secret, behind R9's cracked wall)
r = _ra_room('R14', "Sentry's Cache", 'ramparts', -4, -34, 16, 11, indoor=True, ra_bg=0.94, secret=True, chests=['emberstone'])
r.walls().open('W', 3, 6).fill(0, 7, 15, 10).fill(9, 4, 12, 4, '=')
_put(r, [(12, 6, 'C'), (3, 6, 'k'), (8, 1, 'l'), (14, 6, 'b')])
_add(r, SY('lore', x=6, y=6, page='ra_5', look='corpse'))

# ---------------------------------------------------------------- R7 The Barracks (first shield wardens; a shrine)
r = _ra_room('R7', 'The Barracks', 'ramparts', -76, -28, 48, 14, indoor=True, ra_bg=0.94, shrine='Shrine of the Last Muster')
r.walls().open('E', 7, 10).open('N', 40, 43).fill(0, 11, 47, 13)
r.fill(4, 11, 7, 13, '.').fill(2, 11, 3, 12, '.').fill(8, 11, 9, 12, '.')
for y, x0, x1 in [(2, 39, 42), (5, 43, 46), (8, 38, 42)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(20, 10, 'w'), (31, 10, 'w'), (13, 10, 's'), (36, 10, 'S'), (6, 1, 'l'), (22, 1, 'l'), (34, 1, 'l'), (45, 10, 'u'), (26, 10, 'k')])

# ---------------------------------------------------------------- R6 The Stable Yard (above the Barracks)
r = _ra_room('R6', 'The Stable Yard', 'ramparts', -76, -42, 48, 14, indoor=True, ra_bg=0.94)
r.walls().open('W', 7, 10).fill(0, 11, 47, 13)
r.fill(40, 11, 43, 13, '.').fill(38, 11, 39, 12, '.').fill(44, 11, 45, 12, '.')
for y, x0, x1 in [(8, 13, 16), (5, 18, 30)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(22, 4, 'a'), (28, 4, 'a'), (20, 10, 'c'), (33, 10, 's'), (8, 10, 'c'), (5, 1, 'l'), (24, 1, 'l'), (38, 1, 'l'), (3, 10, 'b'), (32, 10, 'b')])

# ---------------------------------------------------------------- R13 Muster Yard (gauntlet, west of the Stable Yard)
r = _ra_room('R13', 'Muster Yard', 'ramparts', -112, -42, 36, 14, indoor=True, ra_bg=0.94, gauntlet=True)
r.walls().open('E', 7, 10).fill(0, 11, 35, 13)
_put(r, [(31, 10, 'k'), (8, 1, 'l'), (22, 1, 'l')])
_add(r, KT('gate', x=26, y=10, id='gM', open=True),
     SY('gauntlet', x=12, y=10, id='muster', look='banner', name='The Muster Yard', gates=['gM'],
        waves=[[EN('hollow_soldier', x=3, y=10), EN('hollow_soldier', x=22, y=10)],
               [EN('hollow_soldier', x=2, y=10), EN('hollow_soldier', x=23, y=10), EN('hollow_archer', x=5, y=10)],
               [EN('hollow_soldier', x=4, y=10), EN('hollow_soldier', x=20, y=10), EN('hollow_archer', x=2, y=10), EN('rot_crawler', x=17, y=10)],
               [EN('shield_warden', x=4, y=10), EN('hollow_archer', x=22, y=10)]],
        reward=['shard', 'gold']))

# ---------------------------------------------------------------- R8 Siege Undercroft: the winch lift, the sally port home
r = _ra_room('R8', 'Siege Undercroft', 'ramparts', -76, -14, 48, 14, indoor=True, ra_bg=0.94)
r.walls().open('N', 4, 7).open('W', 3, 6).open('E', 9, 11)
r.fill(0, 7, 47, 8).fill(20, 7, 22, 8, '.').fill(0, 12, 47, 13).fill(20, 12, 22, 12, '.')
r.fill(4, 1, 5, 1, '=').fill(3, 4, 8, 4, '=')
_put(r, [(12, 6, 'c'), (34, 6, 's'), (40, 6, 'c'), (10, 11, 'c'), (16, 1, 'l'), (32, 1, 'l'), (30, 9, 'l'), (44, 11, 'b'), (2, 11, 'k')])
_add(r, KT('lever', x=16, y=6, id='winch', targets=[], once=True, msg='The winch groans free. The lift will answer now.'),
     KT('lift', x=20, y=12, to=7, w=3, id='lift'),
     dict(t='ra_lock', x=21, y=11, target='lift', src='winch', text='The lift is chained fast. Its winch is somewhere above.'),
     SY('lore', x=33, y=11, page='ra_3', look='corpse'))

# ---------------------------------------------------------------- R12 Winch House (puzzle): two winches hold one portcullis
r = _ra_room('R12', 'Winch House', 'ramparts', -108, -20, 32, 20, indoor=True, ra_bg=0.94, puzzle=True, chests=['emberstone'])
r.walls().open('E', 9, 12).fill(0, 17, 31, 19).fill(25, 13, 30, 14)
for y, x0, x1 in [(14, 18, 22), (11, 13, 17), (8, 10, 13)]:
    r.fill(x0, y, x1, y, '=')
r.fill(1, 5, 8, 6)
_put(r, [(2, 4, 'C'), (6, 1, 'l'), (16, 1, 'l'), (26, 1, 'l'), (19, 16, 'b'), (3, 16, 'k')])
_add(r, KT('lever', x=27, y=16, id='wA', targets=['port'], timer=8),
     KT('lever', x=7, y=4, id='wB', targets=['port'], timer=6),
     KT('gate', x=4, y=4, id='port', logic='all', persist=True),
     SY('lore', x=22, y=16, page='ra_4', look='tablet'),
     dict(t='ra_hint', x=15, y=16, watch='port', src=['wA', 'wB'], text='Strike the low winch, then run the stairs for the high one: both must hold at once.'))

# ---------------------------------------------------------------- anchors: R3's roof becomes a stair up onto the Long Wall
_r3 = ROOM('R3')
_r3.fill(1, 0, 2, 0, '.')
for _y, _x0, _x1 in [(8, 3, 6), (5, 1, 4), (2, 1, 3)]:
    _r3.fill(_x0, _y, _x1, _y, '=')


# ================================================================================================ ROOTBOUND CATACOMBS
# Final coordinates (EXPANSION3 §8.1: x 36..145, y 57..145; the Ossuary Well W2 is ours to dress, x 83..88).
#   in:   C2 (the Ossuary Shrine) -> its old floor-well W2 (shortened) -> C8 The Great Ossuary
#   out:  C8 -> C7 Rootbound Passage -> gate (lever inside, one-way the first time) -> up through C3's floor
#   the Necropolis road still runs C2 -> W2 -> C8 -> C9 -> NV1 (C9 ends on NV1's roof opening)
# ---------------------------------------------------------------- C7 Rootbound Passage: roots split the walls, crawlers drop
r = _ra_room('C7', 'Rootbound Passage', 'catacombs', 89, 56, 48, 16, indoor=True)
r.walls().open('N', 44, 46).open('S', 6, 9).fill(0, 13, 47, 15)
r.fill(6, 13, 9, 15, '.').fill(4, 13, 5, 14, '.').fill(10, 13, 11, 14, '.')      # the climb up out of the Ossuary
r.fill(13, 1, 20, 2).fill(15, 3, 17, 3).fill(34, 1, 35, 4)   # root masses in the vault
r.fill(22, 11, 25, 12)
for y, x0, x1 in [(10, 42, 46), (7, 38, 41), (4, 42, 46), (1, 44, 46)]:
    r.fill(x0, y, x1, y, '=')                                                  # the climb up into the Hall of Roots
_put(r, [(18, 12, 's'), (27, 12, 'c'), (2, 12, 'b'), (36, 12, 'b'), (14, 12, 'k'), (8, 1, 'r'), (26, 1, 'r'), (12, 1, 'l'), (28, 1, 'l'), (33, 12, 'k')])
_add(r, KT('lever', x=28, y=12, id='glv', targets=['gt'], once=True, msg='The gate lifts. The way up to the Hall of Roots is open.'),
     KT('gate', x=30, y=12, id='gt', persist=True),
     dict(t='ra_amb', type='rot_crawler', x=12, y=3, look='ceiling'), dict(t='ra_amb', type='rot_crawler', x=24, y=4, look='ceiling'),
     dict(t='ra_hint', x=40, y=12, near=30, text='The Hall of Roots is above. The gate only lifts from the far side.'))

# ---------------------------------------------------------------- C8 The Great Ossuary (grand): bone shelves on three levels; a shrine
r = _ra_room('C8', 'The Great Ossuary', 'catacombs', 64, 72, 72, 32, indoor=True, grand=True, chests=['gold'], shrine='Shrine of the Named Bones')
r.walls().open('N', 20, 23).open('N', 31, 34).open('W', 24, 27).open('W', 2, 5).open('S', 26, 29).fill(0, 29, 71, 31).fill(1, 28, 3, 28)
r.fill(26, 29, 29, 31, '.').fill(23, 29, 25, 30, '.').fill(30, 29, 32, 30, '.')   # the drop shaft down to C9 (and the Necropolis)
r.fill(4, 29, 7, 31, 'Y')                                                         # the sealed niche (Cinder Slam)
r.fill(1, 6, 19, 7).fill(19, 1, 19, 5, 'B')                                        # the hidden upper gallery (+ its cracked end)
r.fill(24, 11, 46, 12).fill(52, 11, 66, 12)                                        # the high shelves
r.fill(3, 20, 17, 21).fill(36, 20, 56, 21)                                         # the middle shelves
for y, x0, x1 in [(26, 18, 21), (23, 19, 22), (26, 34, 37), (23, 32, 35), (17, 47, 49), (14, 47, 49), (8, 20, 23), (5, 20, 23), (2, 20, 22),
                  (8, 32, 35), (5, 28, 31), (2, 31, 34), (17, 60, 63), (14, 67, 70)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(12, 28, 'c'), (40, 28, 'c'), (58, 28, 'K'), (44, 19, 's'), (10, 19, 'c'), (40, 10, 'e'), (30, 15, 'f'), (62, 22, 'f'), (48, 28, 'S'),
         (8, 5, 'C'), (4, 5, 'k'), (16, 5, 'k'), (6, 19, 'k'), (54, 19, 'k'), (28, 10, 'k'), (60, 10, 'k'), (20, 28, 'k'), (36, 28, 'k'), (68, 28, 'k'),
         (10, 1, 'l'), (40, 1, 'l'), (54, 1, 'l'), (66, 1, 'l'), (28, 13, 'l'), (62, 13, 'l'), (14, 22, 'l'), (46, 22, 'l')])
_add(r, SY('lore', x=13, y=5, page='ra_6', look='corpse'))

# ---------------------------------------------------------------- C11 Bone Lift Shaft (parkour, off the Ossuary; its top is the gallery)
r = _ra_room('C11', 'Bone Lift Shaft', 'catacombs', 40, 72, 24, 48, indoor=True, parkour=True, chests=['gold'])
r.walls().open('E', 24, 27).open('E', 2, 5).fill(0, 45, 23, 47).fill(1, 44, 22, 44, '^')
r.fill(17, 28, 22, 29).fill(12, 6, 22, 7).fill(12, 8, 22, 8, 'v')
r.fill(1, 22, 1, 38, '^').fill(22, 10, 22, 22, '^').fill(18, 36, 21, 37).fill(18, 35, 21, 35, '^')
_put(r, [(18, 5, 'C'), (20, 27, 'k'), (5, 1, 'l'), (17, 1, 'l'), (14, 5, 'b')])
_add(r, KT('lift', x=11, y=40, to=26, w=3, auto=True, id='L1'), KT('lift', x=3, y=30, to=16, w=3, auto=True, id='L2'),
     KT('lift', x=7, y=20, to=8, w=3, auto=True, id='L3'))

# ---------------------------------------------------------------- C13 Charnel Pit (gauntlet, off the Ossuary Well)
r = _ra_room('C13', 'Charnel Pit', 'catacombs', 47, 58, 36, 14, indoor=True, gauntlet=True)
r.walls().open('E', 7, 10).fill(28, 11, 35, 13).fill(0, 12, 35, 13)
r.fill(9, 1, 11, 2).fill(20, 1, 21, 3)
_put(r, [(31, 10, 'k'), (3, 11, 'b'), (14, 11, 'b'), (30, 1, 'l'), (6, 1, 'l'), (16, 1, 'l')])
_add(r, KT('gate', x=27, y=11, id='gC', open=True),
     SY('gauntlet', x=23, y=11, id='charnel', look='bell', name='The Charnel Pit', gates=['gC'],
        waves=[[EN('rot_crawler', x=5, y=11), EN('rot_crawler', x=17, y=11)],
               [EN('rot_crawler', x=4, y=11), EN('rot_crawler', x=12, y=11), EN('rot_crawler', x=20, y=11)],
               [EN('rot_crawler', x=6, y=11), EN('rot_crawler', x=16, y=11), EN('gloom_wisp', x=9, y=6), EN('gloom_wisp', x=19, y=6)],
               [EN('grave_knight', x=12, y=11)]],
        reward=['shard', 'gold']))

# ---------------------------------------------------------------- C9 The Drop Shaft: ledges and coffin shelves, down to the Necropolis
r = _ra_room('C9', 'The Drop Shaft', 'catacombs', 78, 104, 22, 42, indoor=True)
r.walls().open('N', 12, 15).open('W', 1, 3).open('W', 26, 29).open('E', 7, 10).open('S', 6, 8)
r.fill(6, 41, 8, 41, '=')                                                     # the lip of the Necropolis roof
r.fill(12, 2, 15, 2, '=')
for y, x0, x1 in [(39, 10, 17), (36, 1, 8), (33, 12, 20), (30, 1, 8), (27, 12, 20), (24, 1, 8), (21, 12, 20), (18, 1, 8), (15, 12, 20),
                  (12, 1, 8), (11, 12, 20), (8, 1, 8), (5, 12, 16)]:
    r.fill(x0, y, x1, y, '=')                                                 # coffin shelves, a zigzag you can climb both ways
_put(r, [(17, 10, 'c'), (5, 17, 'f'), (15, 25, 'f'), (4, 7, 'k'), (16, 32, 'b'), (3, 29, 'b'), (18, 14, 'u'), (6, 1, 'l'), (19, 1, 'l'), (10, 16, 'l'), (8, 35, 'k'), (14, 38, 'b')])

# ---------------------------------------------------------------- C15 The Sealed Niche (secret: Cinder Slam through C8's floor)
r = _ra_room('C15', 'The Sealed Niche', 'catacombs', 64, 104, 14, 14, indoor=True, secret=True, needs=['slam'], chests=['seed'])
r.walls().open('N', 4, 7).open('E', 1, 3).fill(0, 10, 13, 13).fill(8, 4, 12, 4).fill(4, 7, 7, 7, '=')
_put(r, [(2, 9, 'C'), (11, 9, 'k'), (5, 9, 'b')])

# ---------------------------------------------------------------- C12 Crypt of Lanterns (puzzle): kindle them as the tombs are numbered
r = _ra_room('C12', 'Crypt of Lanterns', 'catacombs', 38, 120, 40, 16, indoor=True, puzzle=True, chests=['emberstone'])
r.walls().open('E', 10, 13).fill(0, 14, 39, 15).fill(6, 1, 6, 9).fill(1, 1, 5, 7)
_put(r, [(3, 13, 'C'), (37, 13, 'b'), (2, 13, 'k')])
_add(r, KT('gate', x=6, y=13, id='vault', persist=True),
     KT('lantern', x=12, y=13, id='L3', group='crypt'), KT('lantern', x=18, y=13, id='L1', group='crypt'),
     KT('lantern', x=24, y=13, id='L4', group='crypt'), KT('lantern', x=30, y=13, id='L2', group='crypt'),
     KT('seq', x=34, y=13, id='crypt', group='crypt', order=['L1', 'L2', 'L3', 'L4'], targets=['vault'], msg='The vault door grinds open.'),
     SY('lore', x=35, y=13, page='ra_7', look='stone'),
     dict(t='ra_hint', x=33, y=13, seq='crypt', text='The numerals on the tombs give the order: I, then II, then III, then IV.'))

# ---------------------------------------------------------------- C10 Burial Tunnels: niches, and things that crawl out of them; a shrine
r = _ra_room('C10', 'Burial Tunnels', 'catacombs', 100, 104, 46, 14, indoor=True, shrine='Shrine of the Last Niche')
r.walls().open('W', 7, 10).fill(0, 11, 45, 13).fill(1, 1, 44, 4)
r.fill(34, 11, 36, 12, 'B').fill(34, 13, 36, 13, '.').fill(32, 11, 33, 11, '.').fill(37, 11, 38, 11, '.')    # the false tomb: its slab is hollow
for x0 in (8, 17, 26):
    r.fill(x0, 3, x0 + 1, 4, '.')
_put(r, [(28, 10, 's'), (21, 10, 'b'), (4, 10, 'k'), (43, 10, 'k'), (13, 5, 'l'), (39, 5, 'l'), (14, 10, 'S')])
_add(r, dict(t='ra_amb', type='rot_crawler', x=8, y=4, look='niche'), dict(t='ra_amb', type='rot_crawler', x=17, y=4, look='niche'),
     dict(t='ra_amb', type='rot_crawler', x=26, y=4, look='niche'),
     dict(t='ra_hint', x=35, y=10, near=36, text='This tomb rings hollow underfoot. Strike down through its lid.'))

# ---------------------------------------------------------------- C14 Gravedigger's Stash (secret: under the false tomb in C10)
r = _ra_room('C14', "Gravedigger's Stash", 'catacombs', 130, 118, 16, 14, indoor=True, secret=True, chests=['emberstone'])
r.walls().open('N', 4, 6).fill(0, 10, 15, 13)
for y, x0, x1 in [(1, 3, 7), (4, 5, 9), (7, 1, 5)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(12, 9, 'C'), (1, 9, 'k'), (8, 2, 'l')])
_add(r, SY('lore', x=6, y=9, page='ra_8', look='corpse'))

# ---------------------------------------------------------------- anchors: C3's floor opens onto the passage below (the way back up)
_c3 = ROOM('C3')
_c3.fill(13, 11, 15, 13, '.').fill(13, 12, 15, 12, '=')


def _ra_dress_w2():   # the Ossuary Well: from C2's floor down to the Great Ossuary, with a side door into the Charnel Pit
    W = ROOM('W2')
    W.gx, W.gy, W.w, W.h, W.biome = 83, 56, 6, 16, 'catacombs'
    W.g = [['.'] * 6 for _ in range(16)]
    W.walls().open('N', 1, 3).open('S', 1, 3).open('W', 9, 12)
    for y, x0, x1 in [(15, 3, 4), (13, 1, 2), (10, 3, 4), (7, 1, 2), (4, 3, 4), (1, 1, 3)]:
        W.fill(x0, y, x1, y, '=')
    W.put(4, 12, 'k')
globals().setdefault('POST_LINKS', []).append(_ra_dress_w2)


# ================================================================================================ SUNKEN CATHEDRAL
# Final coordinates (EXPANSION3 §8.1: x 252..347, y -69..13, plus the band above K3s at x 356..419).
#   in:   K1 (the Nave) -> up through its vault -> K5 Pilgrims' Aisle -> K7 The Clerestory (grand)
#   out:  K7 -> K8 Confessional Row -> gate (lever inside, one-way the first time) -> down through K2's vault
#   side: K13 behind K5's altar; K9 (over the Clerestory) -> K10 above it; K11 over the Clerestory
#   and from K3s (the Reliquary of Wings): up through its ceiling -> K6 Flooded Crypt Stair -> K12 Bellrope Trial
_T = ['talon']


def _ra_mirror(r):   # flip a room left-right: map, and every spawn's x (decor keeps its look, facing flipped)
    r.g = [row[::-1] for row in r.g]
    for s in r.kw.get('spawns', []):
        s['x'] = r.w - 1 - s['x']
        if 'dx' in s: s['dx'] = -s['dx']
        if s.get('t') == 'ra': s['flip'] = 0 if s.get('flip') else 1
    return r


# ---------------------------------------------------------------- K13 The Walled Sacristy (secret, behind K5's altar)
r = _ra_room('K13', 'The Walled Sacristy', 'cathedral', 252, 0, 16, 14, indoor=True, needs=_T, secret=True, chests=['shard'])
r.walls().open('E', 7, 10).fill(0, 11, 15, 13)
_put(r, [(4, 10, 'C'), (2, 10, 'k'), (8, 2, 'l')])
_add(r, SY('lore', x=9, y=10, page='ra_11', look='book'))

# ---------------------------------------------------------------- K5 Pilgrims' Aisle: rows of kneeling statues (a few are not statues); a shrine
r = _ra_room('K5', "Pilgrims' Aisle", 'cathedral', 268, 0, 40, 14, indoor=True, needs=_T, shrine='Shrine of the Kneeling')
r.walls().open('N', 28, 31).open('S', 14, 16).fill(0, 11, 39, 13).fill(27, 1, 27, 4).fill(32, 1, 32, 4)
r.fill(14, 11, 16, 13, '.').fill(14, 13, 16, 13, '=')                        # the stair up out of the Nave's vault
r.fill(1, 7, 1, 10, 'B').fill(0, 7, 0, 10, '.')                              # behind the altar: the walled sacristy
r.fill(27, 8, 32, 8, '=').fill(28, 5, 31, 5, '=').fill(28, 2, 31, 2, '=')
_put(r, [(33, 10, 'e'), (22, 10, 'S'), (6, 1, 'l'), (18, 1, 'l'), (36, 1, 'l'), (38, 10, 'u'), (2, 10, 'k'), (11, 10, 'k')])
_add(r, dict(t='ra_amb', type='hollow_soldier', x=9, y=10, look='kneel'), dict(t='ra_amb', type='hollow_soldier', x=25, y=10, look='kneel', face=-1),
     dict(t='ra_amb', type='grave_knight', x=36, y=10, look='kneel', face=-1))

# ---------------------------------------------------------------- K8 Confessional Row: the booths are not empty; a shrine; the way home
r = _ra_room('K8', 'Confessional Row', 'cathedral', 308, 0, 40, 14, indoor=True, needs=_T, shrine='Shrine of the Last Confession')
r.walls().open('N', 32, 35).open('S', 1, 3).fill(0, 11, 39, 13).fill(1, 11, 3, 12, '.').fill(1, 13, 3, 13, '=')
for y, x0, x1 in [(8, 36, 38), (5, 32, 35), (2, 33, 36)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(28, 10, 's'), (31, 10, 'S'), (5, 1, 'l'), (17, 1, 'l'), (27, 1, 'l'), (38, 10, 'k'), (9, 10, 'k')])
_add(r, KT('gate', x=5, y=10, id='gk', persist=True),
     KT('lever', x=7, y=10, id='klv', targets=['gk'], once=True, msg='The iron grille lifts. The Flooded Aisle lies below.'),
     dict(t='ra_amb', type='hollow_soldier', x=12, y=10, look='booth'), dict(t='ra_amb', type='ember_acolyte', x=18, y=10, look='booth'),
     dict(t='ra_amb', type='hollow_soldier', x=24, y=10, look='booth'), D('booth', x=15, y=10), D('booth', x=21, y=10),
     dict(t='ra_hint', x=4, y=10, near=28, text='The grille lifts from this side. Below: the Flooded Aisle. Hold ↓ and press jump to drop through.'))

# ---------------------------------------------------------------- K7 The Clerestory (grand): floor, rafters, clerestory walk
r = _ra_room('K7', 'The Clerestory', 'cathedral', 252, -30, 96, 30, indoor=True, needs=_T, grand=True, chests=['gold'])
r.walls().open('N', 2, 4).open('N', 74, 77).open('S', 44, 47).open('S', 88, 91).fill(0, 27, 95, 29)
r.fill(44, 27, 47, 29, '.').fill(42, 27, 43, 28, '.').fill(48, 27, 49, 28, '.')    # down to the Pilgrims' Aisle
r.fill(88, 27, 91, 29, '.').fill(86, 27, 87, 28, '.').fill(92, 27, 93, 28, '.')    # down to Confessional Row
for y, x0, x1 in [(24, 30, 33), (21, 30, 33), (24, 66, 69), (21, 66, 69)]:
    r.fill(x0, y, x1, y, '=')
for x0, x1 in [(12, 40), (46, 72), (78, 94)]:
    r.fill(x0, 18, x1, 18, '=')                                                  # the rafters
r.fill(4, 8, 24, 9).fill(30, 8, 62, 9).fill(68, 8, 94, 9)                         # the clerestory walk
r.fill(4, 10, 5, 23)                                                             # the chimney pillar (wall-jump up to the walk)
r.fill(2, 5, 4, 5, '=').fill(2, 2, 4, 2, '=').fill(74, 5, 77, 5, '=').fill(74, 2, 77, 2, '=')
_put(r, [(38, 26, 's'), (60, 26, 's'), (54, 26, 'K'), (58, 17, 'a'), (46, 7, 'e'), (36, 14, 'f'), (80, 14, 'f'), (84, 7, 'C'),
         (12, 1, 'l'), (40, 1, 'l'), (66, 1, 'l'), (88, 1, 'l'), (3, 26, 'k'), (70, 26, 'k'), (94, 26, 'u'), (20, 7, 'u')])
_add(r, SY('lore', x=10, y=7, page='ra_12', look='book'))

# ---------------------------------------------------------------- K9 Chandelier Crossing (parkour, over the Clerestory): they sway, then they fall
r = _ra_room('K9', 'Chandelier Crossing', 'cathedral', 252, -50, 56, 20, indoor=True, needs=_T, parkour=True, chests=['emberstone'])
r.walls().open('N', 48, 51).fill(1, 11, 6, 19).fill(0, 18, 55, 19).fill(7, 17, 43, 17, '^').fill(44, 8, 54, 17)
r.fill(2, 11, 4, 19, '.').fill(2, 19, 4, 19, '=').fill(2, 16, 4, 16, '=').fill(2, 13, 4, 13, '=')   # the stair up from the Clerestory
r.fill(46, 5, 53, 5, '=').fill(48, 2, 51, 2, '=').fill(23, 4, 27, 4)
_put(r, [(25, 3, 'C'), (6, 10, 'k'), (52, 7, 'k'), (10, 1, 'l'), (36, 1, 'l')])
for i, (x, y) in enumerate([(9, 11), (15, 10), (21, 12), (27, 10), (33, 9), (39, 10), (18, 7)]):
    _add(r, KT('crumble', x=x, y=y, w=3, delay=1.0, respawn=2.5, id=f'ch{i}'), dict(t='ra_chand', x=x + 1, y=y - 1, target=f'ch{i}'))

# ---------------------------------------------------------------- K10 Organ Loft (puzzle, above the chandeliers): the hymn in the choir book
r = _ra_room('K10', 'Organ Loft', 'cathedral', 276, -68, 32, 18, indoor=True, needs=_T, puzzle=True, chests=['emberstone'])
r.walls().open('S', 4, 7).fill(0, 15, 31, 17).fill(4, 15, 7, 17, '.').fill(2, 15, 3, 16, '.').fill(8, 15, 9, 16, '.').fill(4, 17, 5, 17, '=')
_put(r, [(29, 14, 'C'), (6, 1, 'l'), (25, 1, 'l'), (2, 14, 'k'), (30, 14, 'k')])
_add(r, KT('stop', x=11, y=13, id='moon', group='hymn', note=2), KT('stop', x=14, y=13, id='root', group='hymn', note=0),
     KT('stop', x=17, y=13, id='sun', group='hymn', note=4), KT('stop', x=20, y=13, id='bell', group='hymn', note=7),
     KT('seq', x=12, y=14, id='hymn', group='hymn', order=['sun', 'bell', 'moon', 'root'], targets=['vestry'], msg='The hymn is whole. Something unlocks behind the organ.'),
     KT('gate', x=26, y=14, id='vestry', persist=True),
     SY('lore', x=23, y=14, page='ra_9', look='book'),
     dict(t='ra_hint', x=22, y=14, seq='hymn', text='The choir book sings of the Sun, then the Bell, then the Moon, then the Root. Mark the carvings over the stops.'),
     D('organ', x=15, y=14, dx=8, sc=2), D('emblem', x=11, y=11, v=1), D('emblem', x=14, y=11, v=2), D('emblem', x=17, y=11, v=0), D('emblem', x=20, y=11, v=3),
     D('votive', x=4, y=14), D('lancet', x=9, y=14, v='gold', dy=-20), D('censer', x=26, y=1))
_ra_mirror(r)

# ---------------------------------------------------------------- K11 The Rose Window (vista, over the Clerestory)
r = _ra_room('K11', 'The Rose Window', 'cathedral', 308, -50, 40, 20, indoor=True, needs=_T, vista=True)
r.walls().open('S', 18, 21).fill(0, 17, 39, 19).fill(18, 17, 21, 19, '.').fill(16, 17, 17, 18, '.').fill(22, 17, 23, 18, '.').fill(18, 19, 19, 19, '=')
_put(r, [(3, 16, 'k'), (36, 16, 'k'), (8, 1, 'l'), (31, 1, 'l')])
_add(r, SY('bench', x=11, y=16, id='bench', view=[20, 10], lore='ra_10'))

# ---------------------------------------------------------------- K6 Flooded Crypt Stair (above the Reliquary of Wings): down into black water; a shrine
r = _ra_room('K6', 'Flooded Crypt Stair', 'cathedral', 372, -27, 24, 27, indoor=True, needs=_T, shrine='Shrine of the Drowned Stair')
r.walls().open('N', 8, 11).open('S', 2, 4).fill(0, 25, 23, 26).fill(2, 25, 4, 26, '.')
for k in range(7): r.fill(5 + 2 * k, 22 - k, 6 + 2 * k, 22 - k, '=')       # the lower flight (timber treads over the black water), up to the east
r.fill(19, 16, 22, 17)                                                   # the turn
for k in range(6): r.fill(17 - 2 * k, 13 - k, 18 - 2 * k, 13 - k, '=')   # the upper flight, back to the west
r.fill(1, 8, 6, 9)
r.fill(8, 5, 11, 5, '=').fill(8, 2, 11, 2, '=')
_put(r, [(3, 7, 'S'), (12, 18, 'f'), (1, 24, 'k'), (21, 15, 'k'), (5, 1, 'l'), (18, 1, 'l'), (14, 9, 'l')])
_add(r, dict(t='ra_water', x=7, y=24, w=16), dict(t='ra_amb', type='rot_crawler', x=13, y=24, look='water'),
     dict(t='ra_amb', type='rot_crawler', x=19, y=24, look='water'))

# ---------------------------------------------------------------- K12 Bellrope Trial: climb the ropes before the bell tolls thrice
r = _ra_room('K12', 'Bellrope Trial', 'cathedral', 372, -69, 24, 42, indoor=True, needs=['talon', 'wings'], trial=True)
r.walls().open('S', 8, 11).fill(0, 39, 23, 41).fill(8, 39, 11, 41, '.').fill(6, 39, 7, 40, '.').fill(12, 39, 13, 40, '.').fill(8, 41, 9, 41, '=')
r.fill(1, 10, 1, 34, '^').fill(22, 11, 22, 34, '^')
_ROPES = [(15, 30), (8, 23), (15, 16), (8, 9)]
for x, y in _ROPES:
    r.fill(x - 1, y - 1, x + 1, y - 1)                                     # the beams the ropes hang from
r.fill(16, 8, 22, 9)
_put(r, [(3, 38, 'k'), (22, 38, 'k'), (5, 1, 'l'), (18, 1, 'l')])
_add(r, SY('trial', x=20, y=38, id='bellrope', par=18, reward='c_x3_chime', region='Sunken Cathedral', name='The Bellrope Trial'),
     SY('trial_goal', x=19, y=7, trial='bellrope'),
     *[KT('swing', x=x, y=y, len=6, amp=25, period=2.6, phase=i * 0.3, rope='rope') for i, (x, y) in enumerate(_ROPES)])

# ---------------------------------------------------------------- anchors: the Nave's vault, the Flooded Aisle's vault, the Reliquary's ceiling
_k1 = ROOM('K1')
_k1.fill(30, 0, 32, 0, '.').fill(29, 4, 32, 4, '=').fill(30, 1, 32, 1, '=')
_k2 = ROOM('K2')
_k2.fill(9, 0, 11, 0, '.').fill(8, 8, 11, 8, '=').fill(10, 5, 13, 5, '=').fill(9, 2, 11, 2, '=')
_k3s = ROOM('K3s')
_k3s.fill(2, 0, 4, 0, '=').fill(1, 6, 5, 6, '=').fill(2, 3, 4, 3, '=')


# ================================================================================================ decor (50_ra.js RA_P)
def _deco(id, *items):
    _add(ROOM(id), *[D(k, x=x, y=y, **kw) for (k, x, y, *rest) in items for kw in [rest[0] if rest else {}]])


# ---- ramparts
_add(ROOM('R5'), dict(t='ra_wall', x=2, y=1, w=20, h=14, a=1), dict(t='ra_wall', x=24, y=11, w=95, h=4, a=1), dict(t='ra_wall', x=0, y=17, w=30, h=3, a=1))
_deco('R5', *[('crenel', x, 8) for x in range(26, 118, 4) if not any(a - 2 <= x <= b + 2 for a, b in [(36, 40), (70, 74), (86, 90)])],
      ('trebuchet', 80, 8, {'dx': 8, 'sc': 2}), ('beacon', 52, 1), ('wbanner', 49, 6), ('wbanner', 52, 6, {'flip': 1}), ('wbanner', 110, 6), ('wbanner', 113, 6, {'flip': 1}),
      ('pbanner', 33, 8), ('pbanner', 65, 8, {'flip': 1}), ('pbanner', 99, 8),
      ('stall', 44, 14), ('stall', 50, 14), ('hay', 64, 14), ('horse', 78, 14), ('barrels', 93, 14), ('cart', 110, 14), ('rubble', 38, 12), ('rubble', 72, 12), ('rubble', 88, 12),
      ('wbanner', 11, 1), ('rack', 5, 14), ('barrels', 17, 14), ('rubble', 30, 14), ('dummy', 26, 14), ('barrels', 8, 19), ('rubble', 22, 19), ('flag', 122, 8))
_deco('R9', ('wbanner', 16, 1), ('beacon', 6, 4), ('rack', 17, 22), ('barrels', 7, 19), ('rack', 5, 13, {'flip': 1}), ('rubble', 17, 7), ('wbanner', 4, 1, {'flip': 1}))
_deco('R10', ('flag', 28, 6), ('pbanner', 48, 7), ('rubble', 11, 7), ('rubble', 53, 6), ('flag', 3, 7, {'flip': 1}), ('pbanner', 61, 7, {'flip': 1}))
_deco('R11', ('flag', 25, 5), ('beacon', 13, 5), ('pbanner', 3, 7), ('rubble', 23, 5))
_deco('R6', ('stall', 20, 10), ('stall', 26, 10), ('stall', 32, 10), ('hay', 36, 10), ('horse', 24, 10), ('cart', 11, 10), ('barrels', 46, 10), ('hay', 24, 4))
_deco('R7', ('bunk', 10, 10), ('bunk', 24, 10), ('bunk', 41, 10), ('dummy', 28, 10), ('barrels', 17, 10), ('wbanner', 16, 1), ('wbanner', 30, 1), ('rack', 3, 10))
_deco('R8', ('winch', 27, 6), ('barrels', 40, 6), ('rubble', 10, 11), ('cart', 36, 11), ('barrels', 6, 11), ('wbanner', 42, 1), ('rack', 17, 6))
_deco('R12', ('winch', 23, 16, {'flip': 1}), ('barrels', 2, 16), ('rubble', 13, 16), ('winch', 9, 16), ('wbanner', 19, 1))
_deco('R13', ('pbanner', 1, 10), ('pbanner', 24, 10, {'flip': 1}), ('rack', 2, 10), ('dummy', 7, 10), ('dummy', 18, 10), ('wbanner', 10, 1), ('wbanner', 15, 1, {'flip': 1}), ('barrels', 33, 10))
_deco('R14', ('barrels', 10, 6), ('wbanner', 4, 1), ('rack', 1, 6), ('hay', 13, 6, {'alpha': 0.9}))

# ---- catacombs

# ---- cathedral


# ---- more light in the dark places (candles 'k', lanterns 'l'), and the Ossuary's heart
# ---- torches, arrow slits and trophies on the walls
_deco('R5', ('torch', 30, 12), ('torch', 64, 12), ('torch', 82, 12), ('torch', 112, 12), ('torch', 12, 12), ('torch', 16, 6), ('slit', 4, 8), ('slit', 19, 10), ('shields', 104, 12), ('torch', 16, 18))
_deco('R9', ('torch', 12, 21), ('torch', 11, 16), ('torch', 14, 9), ('slit', 3, 9), ('slit', 20, 3), ('shields', 5, 17))
_deco('R6', ('torch', 14, 7), ('torch', 35, 8), ('slit', 8, 5), ('slit', 41, 4))
_deco('R7', ('torch', 6, 7), ('torch', 33, 7), ('shields', 16, 7), ('shields', 28, 7), ('slit', 21, 3), ('slit', 12, 2))
_deco('R8', ('torch', 12, 4), ('torch', 36, 4), ('torch', 15, 10), ('torch', 40, 10))
_deco('R12', ('torch', 27, 8), ('torch', 3, 12), ('slit', 16, 4), ('shields', 21, 13))
_deco('R13', ('torch', 5, 6), ('torch', 30, 6), ('shields', 13, 6), ('slit', 18, 3), ('slit', 27, 3))
_deco('R14', ('torch', 13, 3), ('shields', 7, 3))
# ---- lamps for the tower and the flooded stair

# ---- catacombs decor (final layout)
_deco('C7', ('rootc', 11, 3), ('rootc', 22, 3), ('rootc', 31, 1), ('bshelf', 16, 12), ('bshelf', 38, 12), ('skulls', 3, 12), ('coffin', 34, 12), ('skulls', 45, 12),
      ('torch', 10, 9), ('torch', 26, 8))
_put(ROOM('C7'), [(24, 10, 'k'), (21, 12, 'k')])
_deco('C8', ('bshelf', 12, 28), ('bshelf', 36, 28), ('bshelf', 62, 28), ('bshelf', 10, 19), ('bshelf', 46, 19), ('bshelf', 34, 10), ('bshelf', 58, 10),
      ('skullpillar', 16, 28), ('skullpillar', 52, 28), ('bonechand', 30, 1), ('bonechand', 48, 1), ('rootc', 60, 1), ('rootc', 6, 8),
      ('sarc', 44, 19), ('coffin', 14, 19), ('skulls', 66, 28), ('skulls', 5, 27), ('skulls', 60, 10), ('coffin', 10, 5), ('sarc', 30, 10), ('skulls', 16, 5),
      ('rootheart', 44, 1, {'sc': 1.6}))
_deco('C9', ('coffin', 16, 10), ('coffin', 5, 11), ('coffin', 16, 14), ('coffin', 5, 17), ('coffin', 15, 20), ('coffin', 5, 23), ('bshelf', 15, 32), ('rootc', 6, 1),
      ('skulls', 12, 26), ('skulls', 5, 7), ('sarc', 5, 35))
_put(ROOM('C9'), [(18, 10, 'k'), (7, 17, 'k'), (14, 20, 'k'), (2, 29, 'k'), (17, 32, 'k')])
_deco('C11', ('skulls', 20, 27), ('rootc', 10, 1), ('coffin', 21, 5), ('bonechand', 17, 9), ('skulls', 13, 44, {'alpha': 0.8}))
_put(ROOM('C11'), [(14, 9, 'l'), (20, 9, 'l'), (21, 5, 'k'), (22, 27, 'k')])
_deco('C13', ('bshelf', 6, 11), ('bshelf', 16, 11), ('skulls', 2, 11), ('skulls', 10, 11), ('skulls', 21, 11), ('rootc', 14, 1), ('skullpillar', 26, 11, {'dx': -6}),
      ('torch', 6, 7), ('torch', 24, 7))
_put(ROOM('C13'), [(8, 11, 'k'), (18, 11, 'k'), (25, 11, 'k')])
_deco('C12', ('tomb', 10, 13, {'v': 2}), ('tomb', 16, 13, {'v': 0}), ('tomb', 22, 13, {'v': 3}), ('tomb', 28, 13, {'v': 1}), ('bonechand', 20, 1), ('skulls', 36, 13), ('bshelf', 3, 8))
_put(ROOM('C12'), [(8, 13, 'k'), (33, 13, 'k'), (12, 1, 'l'), (28, 1, 'l')])
_deco('C10', ('bshelf', 8, 10), ('bshelf', 22, 10), ('bshelf', 40, 10), ('skulls', 43, 10), ('rootc', 30, 5), ('torch', 11, 8), ('torch', 30, 8),
      ('sarc', 35, 10, {'back': False}))
_put(ROOM('C10'), [(24, 10, 'k'), (31, 10, 'k'), (22, 5, 'l')])
_deco('C14', ('digger', 9, 9), ('skulls', 14, 9), ('bshelf', 5, 9), ('coffin', 2, 9))
_deco('C15', ('sarc', 7, 9), ('skulls', 3, 9), ('bonechand', 7, 1), ('bshelf', 11, 9))
_put(ROOM('C15'), [(9, 3, 'k'), (11, 1, 'l')])

# ---- cathedral decor (final layout)
_deco('K13', ('saint', 12, 10), ('votive', 6, 10), ('censer', 3, 1), ('altar', 8, 10, {'alpha': 0.95}))
_deco('K5', *[('lancet', x, 10, {'dy': -24, 'v': v}) for x, v in [(8, 'gold'), (19, 'rose'), (35, 'blue')]],
      *[('kneel', x, 10, {'flip': x > 20}) for x in (6, 13, 28, 34)], ('altar', 3, 10), ('votive', 17, 10), ('pew', 30, 10))
_deco('K8', ('lancet', 20, 10, {'v': 'rose', 'dy': -40}), ('lancet', 34, 9, {'v': 'blue', 'dy': -40}), ('votive', 36, 10), ('censer', 16, 1), ('saint', 2, 10))
_deco('K7', *[('lancet', x, 7, {'v': v}) for x, v in [(8, 'gold'), (16, 'rose'), (36, 'blue'), (44, 'gold'), (52, 'rose'), (72, 'blue'), (80, 'gold'), (90, 'rose')]],
      *[('lancet', x, 17, {'v': v, 'alpha': 0.95}) for x, v in [(24, 'rose'), (38, 'gold'), (56, 'blue'), (64, 'rose'), (86, 'gold')]],
      *[('pew', x, 26) for x in (34, 40, 52, 62, 76)], ('saint', 82, 26, {'sc': 2}), ('votive', 20, 26), ('votive', 58, 26),
      ('chand', 46, 10), ('chand', 84, 10), ('chand', 20, 10), ('censer', 60, 1), ('saint', 12, 26))
_deco('K9', ('lancet', 13, 16, {'v': 'blue'}), ('lancet', 25, 16, {'v': 'rose'}), ('lancet', 37, 16, {'v': 'gold'}), ('rubble', 20, 16), ('rubble', 31, 16), ('votive', 48, 7), ('saint', 53, 7))
_deco('K11', ('pew', 7, 16), ('pew', 30, 16), ('saint', 4, 16), ('saint', 35, 16), ('votive', 16, 16), ('votive', 25, 16), ('censer', 12, 1))
_add(ROOM('K11'), dict(t='ra_rose', x=19, y=4, dx=8))
_deco('K12', ('bigbell', 19, 7), ('lancet', 12, 22, {'v': 'blue'}), ('lancet', 12, 36, {'v': 'rose'}), ('wbanner', 4, 1), ('votive', 5, 38))
_put(ROOM('K12'), [(x + 1, y, 'l') for x, y in _ROPES] + [(12, 38, 'k'), (16, 38, 'k')])
_deco('K6', ('saint', 2, 7), ('votive', 5, 7), ('censer', 12, 1), ('lancet', 14, 22, {'v': 'rose', 'dy': -40, 'alpha': 0.9}), ('coffin', 21, 15), ('sarc', 20, 24, {'alpha': 0.9}))
