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
# ---------------------------------------------------------------- R5 The Long Wall (grand): high wall-walk, low stables
r = _ra_room('R5', 'The Long Wall', 'ramparts', -112, -62, 128, 22, grand=True, items=[], chests=[])
r.fill(0, 19, 127, 21).fill(0, 0, 1, 21).fill(126, 0, 127, 21)
r.fill(0, 0, 23, 0).fill(9, 0, 12, 0, '.')                   # west tower roof; the stair up into R9
r.fill(22, 1, 23, 18).fill(22, 8, 23, 11, '.').fill(22, 15, 23, 18, '.')   # tower wall + doorways (walk, stables)
r.fill(24, 12, 125, 13)                                       # the wall-walk
for y, x0, x1 in [(16, 3, 6), (13, 8, 12), (12, 14, 21), (9, 9, 13), (6, 14, 18), (3, 6, 10), (1, 9, 12)]:
    r.fill(x0, y, x1, y, '=')                                 # tower stair
for x0, x1 in [(36, 40), (70, 74), (86, 90)]:                 # collapsed spans: the walk fell into the stables
    r.fill(x0, 12, x1, 13, '.').fill(x0 + 1, 13, x1 - 1, 13, '=').fill(x0, 16, x1, 18).fill(x0 - 1, 17, x0 - 1, 18).fill(x1 + 1, 17, x1 + 1, 18)
r.fill(56, 19, 59, 21, '.').fill(53, 19, 55, 20, '.').fill(60, 19, 62, 20, '.')    # stair down to the Stable Yard
r.fill(99, 14, 99, 18, 'B')                                   # the cracked wall (first breakable wall)
r.fill(102, 19, 104, 21, '.').fill(100, 19, 101, 20, '.').fill(105, 19, 107, 20, '.')   # down to the Sentry's Cache
r.fill(48, 3, 53, 7).fill(108, 3, 113, 7)                     # gatehouse arches over the walk (archers on top)
for y, x0, x1 in [(9, 43, 46), (6, 43, 47), (9, 114, 117), (6, 114, 118)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(30, 11, 's'), (62, 11, 'w'), (96, 11, 's'), (50, 2, 'a'), (111, 2, 'a'), (30, 18, 'c'), (47, 18, 'c'), (66, 18, 's'), (81, 18, 'c'),
         (26, 11, 'u'), (104, 11, 'u'), (118, 18, 'b'), (8, 18, 'k'), (15, 18, 'b'), (5, 2, 'x'), (18, 2, 'x'), (4, 11, 'l'), (18, 1, 'l')])
_add(r, SY('door', x=121, y=11, id='r2', to='R2', toId='r5', look='arch', face=-1),
     SY('lore', x=52, y=18, page='ra_2', look='corpse'))

# ---------------------------------------------------------------- R9 Signal Tower Stair
r = _ra_room('R9', 'Signal Tower Stair', 'ramparts', -112, -90, 24, 28, indoor=True, ra_bg=0.94, chests=['gold'])
r.walls().fill(0, 26, 23, 27).fill(9, 26, 12, 27, '.').fill(9, 26, 12, 26, '=')
r.open('E', 4, 7)
for y, x0, x1 in [(23, 13, 22), (20, 1, 10), (17, 13, 22), (14, 1, 10), (8, 15, 22), (5, 1, 8)]:
    r.fill(x0, y, x1, y + 1)
r.fill(9, 11, 13, 11, '=').fill(9, 5, 12, 5, '=')
_put(r, [(18, 22, 's'), (5, 19, 's'), (19, 16, 'a'), (4, 13, 's'), (2, 4, 'C'), (6, 1, 'l'), (17, 1, 'l'), (20, 25, 'k'), (2, 25, 'b')])

# ---------------------------------------------------------------- R10 Crenel Run (parkour): broken battlements over the stakes
r = _ra_room('R10', 'Crenel Run', 'ramparts', -88, -90, 64, 16, parkour=True, chests=['gold'])
r.fill(0, 15, 63, 15).fill(0, 14, 63, 14, '^')
r.fill(0, 0, 0, 3).fill(63, 0, 63, 3)
for x0, x1, top in [(0, 5, 8), (10, 12, 8), (17, 18, 9), (27, 29, 7), (34, 35, 9), (47, 49, 8), (53, 54, 7), (58, 63, 8)]:
    r.fill(x0, top, x1, 14)
_put(r, [(61, 7, 'C')])
_add(r, KT('crumble', x=22, y=8, w=2, delay=0.8), KT('crumble', x=38, y=9, w=2, delay=0.8), KT('crumble', x=42, y=8, w=2, delay=0.8))

# ---------------------------------------------------------------- R11 Watcher's Perch (vista): the highest tower
r = _ra_room('R11', "Watcher's Perch", 'ramparts', -24, -90, 40, 24, vista=True)
r.fill(0, 0, 0, 3).fill(0, 8, 6, 9).fill(0, 10, 1, 23).fill(7, 8, 10, 8, '=').fill(11, 6, 26, 7).fill(15, 8, 21, 23)
r.fill(0, 23, 39, 23).fill(38, 2, 39, 22).fill(39, 0, 39, 1)
_add(r, SY('bench', x=19, y=5, id='bench', view=[29, 9], lore='ra_1'),
     dict(t='ra_void', x=2, y=19, w=36, h=4), dict(t='ra_mist', x=2, y=16, w=36, h=8))

# ---------------------------------------------------------------- R6 The Stable Yard
r = _ra_room('R6', 'The Stable Yard', 'ramparts', -64, -40, 48, 14, indoor=True, ra_bg=0.94)
r.walls().open('N', 8, 11).open('W', 6, 9)
r.fill(1, 10, 14, 13).fill(15, 11, 46, 13)
r.fill(42, 11, 45, 13, '.').fill(40, 11, 41, 12, '.').fill(46, 11, 46, 12, '.')
for y, x0, x1 in [(1, 7, 12), (4, 3, 7), (7, 8, 12), (9, 15, 17), (6, 18, 30)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(22, 5, 'a'), (28, 5, 'a'), (20, 10, 'c'), (35, 10, 's'), (12, 9, 'c'), (5, 1, 'l'), (24, 1, 'l'), (38, 1, 'l'), (3, 9, 'b'), (32, 10, 'b')])

# ---------------------------------------------------------------- R7 The Barracks (first shield wardens)
r = _ra_room('R7', 'The Barracks', 'ramparts', -112, -36, 48, 14, indoor=True, ra_bg=0.94)
r.walls().open('E', 2, 5).fill(0, 11, 47, 13)
r.fill(4, 11, 7, 13, '.').fill(2, 11, 3, 12, '.').fill(8, 11, 9, 12, '.')
r.fill(40, 6, 46, 7).fill(35, 8, 38, 8, '=')
_put(r, [(20, 10, 'w'), (31, 10, 'w'), (13, 10, 's'), (6, 1, 'l'), (22, 1, 'l'), (38, 1, 'l'), (44, 5, 'u'), (26, 10, 'k')])

# ---------------------------------------------------------------- R8 Siege Undercroft: the winch lift down to the first shrine
r = _ra_room('R8', 'Siege Undercroft', 'ramparts', -112, -22, 48, 14, indoor=True, ra_bg=0.94)
r.walls().open('N', 4, 7).open('E', 3, 6)
r.fill(0, 7, 47, 8).fill(20, 7, 22, 8, '.').fill(0, 12, 47, 13).fill(20, 12, 22, 12, '.')
r.fill(4, 1, 7, 1, '=').fill(3, 4, 8, 4, '=')
_put(r, [(14, 6, 'c'), (34, 6, 's'), (40, 6, 'c'), (10, 11, 'c'), (16, 1, 'l'), (32, 1, 'l'), (30, 9, 'l'), (44, 11, 'b'), (2, 11, 'k')])
_add(r, KT('lever', x=24, y=6, id='winch', targets=[], once=True, msg='The winch groans free. The lift will answer now.'),
     KT('lift', x=20, y=12, to=7, w=3, id='lift'),
     dict(t='ra_lock', x=21, y=11, target='lift', src='winch', text='The lift is chained fast. Its winch is somewhere above.'),
     SY('door', x=40, y=11, id='r1', to='R1', toId='r8', look='hatch'),
     SY('lore', x=33, y=11, page='ra_3', look='corpse'))

# ---------------------------------------------------------------- R12 Winch House (puzzle): two winches hold one portcullis
r = _ra_room('R12', 'Winch House', 'ramparts', -64, -26, 32, 20, indoor=True, ra_bg=0.94, puzzle=True, chests=['emberstone'])
r.walls().open('W', 7, 10).fill(0, 17, 31, 19).fill(1, 11, 6, 12)
for y, x0, x1 in [(14, 9, 13), (11, 14, 18), (8, 18, 21)]:
    r.fill(x0, y, x1, y, '=')
r.fill(23, 5, 30, 6)
_put(r, [(29, 4, 'C'), (6, 1, 'l'), (16, 1, 'l'), (26, 1, 'l'), (12, 16, 'b'), (28, 16, 'k')])
_add(r, KT('lever', x=4, y=16, id='wA', targets=['port'], timer=8),
     KT('lever', x=24, y=4, id='wB', targets=['port'], timer=6),
     KT('gate', x=27, y=4, id='port', logic='all', persist=True),
     SY('lore', x=9, y=16, page='ra_4', look='tablet'),
     dict(t='ra_hint', x=16, y=16, watch='port', src=['wA', 'wB'], text='Strike the low winch, then run the stairs for the high one: both must hold at once.'))

# ---------------------------------------------------------------- R13 Muster Yard (gauntlet)
r = _ra_room('R13', 'Muster Yard', 'ramparts', -24, -26, 40, 14, indoor=True, ra_bg=0.94, gauntlet=True)
r.walls().open('N', 2, 5).fill(0, 11, 39, 13).fill(1, 10, 8, 10)
for y, x0, x1 in [(7, 2, 6), (4, 3, 7), (1, 1, 6)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(4, 9, 'k'), (16, 1, 'l'), (32, 1, 'l')])
_add(r, KT('gate', x=9, y=10, id='gM', open=True),
     SY('gauntlet', x=25, y=10, id='muster', look='banner', name='The Muster Yard', gates=['gM'],
        waves=[[EN('hollow_soldier', x=14, y=10), EN('hollow_soldier', x=35, y=10)],
               [EN('hollow_soldier', x=13, y=10), EN('hollow_soldier', x=36, y=10), EN('hollow_archer', x=31, y=10)],
               [EN('hollow_soldier', x=14, y=10), EN('hollow_soldier', x=20, y=10), EN('hollow_archer', x=35, y=10), EN('rot_crawler', x=30, y=10)],
               [EN('shield_warden', x=33, y=10), EN('hollow_archer', x=14, y=10)]],
        reward=['shard', 'gold']))

# ---------------------------------------------------------------- R14 Sentry's Cache (secret, behind R5's cracked wall)
r = _ra_room('R14', "Sentry's Cache", 'ramparts', -16, -40, 16, 14, indoor=True, ra_bg=0.94, secret=True, chests=['emberstone'])
r.walls().open('N', 6, 8).fill(0, 10, 15, 13)
for y, x0, x1 in [(7, 9, 12), (4, 2, 5), (1, 5, 9)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(12, 9, 'C'), (3, 9, 'k'), (8, 3, 'l'), (14, 9, 'b')])
_add(r, SY('lore', x=6, y=9, page='ra_5', look='corpse'))

# ---------------------------------------------------------------- anchors: R2 (way in), R1 (the ladder back to the first shrine)
_add(ROOM('R2'), SY('door', x=27, y=10, id='r5', to='R5', toId='r2', look='arch'))
_add(ROOM('R1'), SY('door', x=6, y=10, id='r8', to='R8', toId='r1', look='ladder'))


# ================================================================================================ ROOTBOUND CATACOMBS
# ---------------------------------------------------------------- C7 Rootbound Passage: roots split the walls, crawlers drop
r = _ra_room('C7', 'Rootbound Passage', 'catacombs', -160, 52, 48, 14, indoor=True)
r.walls().open('W', 6, 9).fill(0, 11, 47, 13).fill(1, 10, 9, 10).fill(1, 1, 46, 1)
r.fill(6, 2, 10, 2).fill(19, 2, 26, 3).fill(21, 4, 23, 4).fill(35, 2, 38, 2).fill(27, 9, 31, 10).fill(26, 10, 26, 10)
r.fill(44, 2, 46, 5).fill(45, 6, 46, 6)                               # a root-mass shoulders out of the east wall
_put(r, [(18, 10, 's'), (38, 10, 'c'), (4, 9, 'b'), (34, 10, 'b'), (13, 10, 'k'), (15, 2, 'r'), (30, 2, 'r'), (41, 2, 'r'), (12, 2, 'l'), (33, 2, 'l')])
_add(r, SY('door', x=43, y=10, id='c1', to='C1', toId='c7', look='crack', face=-1),
     dict(t='ra_amb', type='rot_crawler', x=16, y=2, look='ceiling'), dict(t='ra_amb', type='rot_crawler', x=33, y=3, look='ceiling'),
     dict(t='ra_amb', type='rot_crawler', x=24, y=5, look='ceiling'))

# ---------------------------------------------------------------- C8 The Great Ossuary (grand): bone shelves on three levels
r = _ra_room('C8', 'The Great Ossuary', 'catacombs', -256, 44, 96, 32, indoor=True, grand=True, chests=['gold'])
r.walls().open('W', 24, 27).open('W', 2, 5).open('E', 14, 17).fill(0, 29, 95, 31).fill(1, 28, 3, 28)
r.fill(64, 29, 67, 31, '.').fill(61, 29, 63, 30, '.').fill(68, 29, 70, 30, '.')   # the drop shaft
r.fill(84, 29, 87, 31, 'Y')                                                       # the sealed niche (Cinder Slam)
r.fill(76, 18, 94, 19)                                                            # east ledge -> C7
r.fill(6, 20, 30, 21).fill(38, 20, 58, 21)                                         # the middle shelves
r.fill(10, 11, 28, 12).fill(44, 11, 62, 12).fill(72, 11, 86, 12)                   # the high shelves
r.fill(1, 6, 44, 7).fill(45, 1, 45, 5, 'B').fill(46, 6, 50, 7)                     # the hidden upper gallery (+ its cracked end)
for y, x0, x1 in [(26, 1, 4), (23, 2, 5), (26, 32, 35), (23, 34, 37), (26, 71, 75), (23, 71, 75), (20, 71, 74),
                  (17, 31, 34), (14, 29, 32), (17, 60, 63), (14, 63, 66), (14, 67, 70), (8, 50, 53)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(20, 28, 'c'), (46, 28, 'c'), (80, 28, 'K'), (52, 19, 's'), (18, 19, 'c'), (54, 10, 'e'), (30, 15, 'f'), (78, 22, 'f'),
         (20, 5, 'C'), (6, 28, 'b'), (36, 28, 'b'), (58, 28, 'k'), (90, 28, 'b'), (8, 5, 'k'), (24, 10, 'u'), (84, 17, 'u'),
         (12, 1, 'l'), (40, 8, 'l'), (70, 1, 'l'), (88, 1, 'l'), (28, 1, 'r'), (56, 1, 'r'), (80, 1, 'r')])
_add(r, SY('lore', x=10, y=5, page='ra_6', look='corpse'))

# ---------------------------------------------------------------- C11 Bone Lift Shaft (parkour): bone lifts between spikes
r = _ra_room('C11', 'Bone Lift Shaft', 'catacombs', -280, 44, 24, 48, indoor=True, parkour=True, chests=['gold'])
r.walls().open('E', 24, 27).open('E', 2, 5).fill(0, 45, 23, 47).fill(1, 44, 22, 44, '^')
r.fill(17, 28, 22, 29).fill(12, 6, 22, 7).fill(12, 8, 22, 8, 'v')
r.fill(1, 22, 1, 38, '^').fill(22, 10, 22, 22, '^').fill(18, 36, 21, 37).fill(18, 35, 21, 35, '^')
_put(r, [(18, 5, 'C'), (20, 27, 'k'), (5, 1, 'l'), (17, 1, 'l'), (14, 5, 'b')])
_add(r, KT('lift', x=11, y=40, to=26, w=3, auto=True, id='L1'), KT('lift', x=3, y=30, to=16, w=3, auto=True, id='L2'),
     KT('lift', x=7, y=20, to=8, w=3, auto=True, id='L3'))

# ---------------------------------------------------------------- C9 The Drop Shaft: ledges and coffin shelves
r = _ra_room('C9', 'The Drop Shaft', 'catacombs', -200, 76, 24, 37, indoor=True)
r.walls().open('N', 8, 11).open('W', 6, 9).open('W', 26, 29).open('E', 30, 33).open('E', 1, 3).fill(0, 34, 23, 36)
r.fill(8, 1, 11, 1, '=').fill(6, 4, 11, 4, '=')
for y, x0, x1 in [(7, 13, 21), (10, 1, 8), (13, 13, 21), (16, 3, 10), (19, 13, 20), (22, 3, 9), (25, 12, 19), (28, 12, 18), (30, 1, 8), (31, 14, 21)]:
    r.fill(x0, y, x1, y)
_put(r, [(17, 6, 'c'), (12, 20, 'f'), (6, 27, 'f'), (4, 9, 'k'), (16, 33, 'b'), (3, 29, 'b'), (18, 12, 'u'), (6, 1, 'l'), (19, 1, 'l'), (11, 17, 'l')])

# ---------------------------------------------------------------- C13 Charnel Pit (gauntlet): the bone bell calls the dead
r = _ra_room('C13', 'Charnel Pit', 'catacombs', -236, 76, 36, 14, indoor=True, gauntlet=True)
r.walls().open('E', 6, 9).fill(28, 10, 35, 13).fill(0, 12, 35, 13)
r.fill(9, 1, 11, 2).fill(20, 1, 21, 3)
_put(r, [(31, 9, 'k'), (3, 11, 'b'), (14, 11, 'b'), (30, 1, 'l'), (6, 1, 'l'), (16, 1, 'l')])
_add(r, KT('gate', x=27, y=11, id='gC', open=True),
     SY('gauntlet', x=23, y=11, id='charnel', look='bell', name='The Charnel Pit', gates=['gC'],
        waves=[[EN('rot_crawler', x=5, y=11), EN('rot_crawler', x=17, y=11)],
               [EN('rot_crawler', x=4, y=11), EN('rot_crawler', x=12, y=11), EN('rot_crawler', x=20, y=11)],
               [EN('rot_crawler', x=6, y=11), EN('rot_crawler', x=16, y=11), EN('gloom_wisp', x=9, y=6), EN('gloom_wisp', x=19, y=6)],
               [EN('grave_knight', x=12, y=11)]],
        reward=['shard', 'gold']))

# ---------------------------------------------------------------- C12 Crypt of Lanterns (puzzle): kindle them as the tombs are numbered
r = _ra_room('C12', 'Crypt of Lanterns', 'catacombs', -240, 92, 40, 16, indoor=True, puzzle=True, chests=['emberstone'])
r.walls().open('E', 10, 13).fill(0, 14, 39, 15).fill(6, 1, 6, 9).fill(1, 1, 5, 7)
_put(r, [(3, 13, 'C'), (37, 13, 'b'), (2, 13, 'k')])
_add(r, KT('gate', x=6, y=13, id='vault', persist=True),
     KT('lantern', x=12, y=13, id='L3', group='crypt'), KT('lantern', x=18, y=13, id='L1', group='crypt'),
     KT('lantern', x=24, y=13, id='L4', group='crypt'), KT('lantern', x=30, y=13, id='L2', group='crypt'),
     KT('seq', x=34, y=13, id='crypt', group='crypt', order=['L1', 'L2', 'L3', 'L4'], targets=['vault'], msg='The vault door grinds open.'),
     SY('lore', x=35, y=13, page='ra_7', look='stone'),
     dict(t='ra_hint', x=33, y=13, seq='crypt', text='The numerals on the tombs give the order: I, then II, then III, then IV.'))

# ---------------------------------------------------------------- C10 Burial Tunnels: niches, and things that crawl out of them
r = _ra_room('C10', 'Burial Tunnels', 'catacombs', -176, 99, 48, 14, indoor=True)
r.walls().open('W', 7, 10).fill(0, 11, 47, 13).fill(1, 1, 46, 4).fill(47, 7, 47, 10, 'B')
for x0 in (8, 17, 26):
    r.fill(x0, 3, x0 + 1, 4, '.')
_put(r, [(28, 10, 's'), (20, 10, 'b'), (4, 10, 'k'), (44, 10, 'k'), (13, 5, 'l'), (39, 5, 'l')])
_add(r, dict(t='ra_amb', type='rot_crawler', x=8, y=4, look='niche'), dict(t='ra_amb', type='rot_crawler', x=17, y=4, look='niche'),
     dict(t='ra_amb', type='rot_crawler', x=26, y=4, look='niche'),
     KT('lever', x=34, y=10, id='glv', targets=['gt'], once=True, msg='The gate lifts. The way to the Rootgate is open.'),
     KT('gate', x=36, y=10, id='gt', persist=True),
     SY('door', x=41, y=10, id='c4', to='C4', toId='c10', look='crack'))

# ---------------------------------------------------------------- C14 Gravedigger's Stash (secret: a false tomb in C10)
r = _ra_room('C14', "Gravedigger's Stash", 'catacombs', -128, 99, 16, 14, indoor=True, secret=True, chests=['emberstone'])
r.walls().open('W', 7, 10).fill(0, 11, 15, 13)
_put(r, [(12, 10, 'C'), (3, 10, 'k'), (8, 2, 'l')])
_add(r, SY('lore', x=6, y=10, page='ra_8', look='corpse'))

# ---------------------------------------------------------------- C15 The Sealed Niche (secret: Cinder Slam through C8's floor)
r = _ra_room('C15', 'The Sealed Niche', 'catacombs', -176, 76, 16, 14, indoor=True, secret=True, needs=['slam'], chests=['seed'])
r.walls().open('N', 4, 7).open('W', 1, 3).fill(0, 10, 15, 13).fill(1, 4, 5, 4).fill(6, 7, 9, 7, '=')
_put(r, [(12, 9, 'C'), (14, 9, 'k'), (10, 9, 'b')])

# ---------------------------------------------------------------- anchors: C1 (the root-crack), C4 (the gate back to the Rootgate)
_add(ROOM('C1'), SY('door', x=15, y=24, id='c7', to='C7', toId='c1', look='crack'))
_add(ROOM('C4'), SY('door', x=10, y=10, id='c10', to='C10', toId='c4', look='crack'))


# ================================================================================================ SUNKEN CATHEDRAL
_T = ['talon']
# ---------------------------------------------------------------- K5 Pilgrims' Aisle: rows of kneeling statues (a few are not statues)
r = _ra_room('K5', "Pilgrims' Aisle", 'cathedral', 372, -36, 48, 14, indoor=True, needs=_T)
r.walls().open('N', 28, 31).fill(0, 11, 47, 13).fill(27, 1, 27, 4).fill(32, 1, 32, 4)
r.fill(27, 8, 32, 8, '=').fill(28, 5, 31, 5, '=')
_put(r, [(24, 10, 'e'), (6, 1, 'l'), (18, 1, 'l'), (40, 1, 'l'), (45, 10, 'u'), (2, 10, 'k'), (22, 10, 'k')])
_add(r, SY('door', x=3, y=10, id='k1', to='K1', toId='k5', look='arch'),
     dict(t='ra_amb', type='hollow_soldier', x=15, y=10, look='kneel'), dict(t='ra_amb', type='hollow_soldier', x=37, y=10, look='kneel', face=-1),
     dict(t='ra_amb', type='grave_knight', x=44, y=10, look='kneel', face=-1))

# ---------------------------------------------------------------- K6 Flooded Crypt Stair: down into knee-deep black water
r = _ra_room('K6', 'Flooded Crypt Stair', 'cathedral', 396, -64, 24, 28, indoor=True, needs=_T)
r.walls().open('N', 16, 19).open('S', 4, 7).open('E', 21, 24).fill(0, 25, 23, 27).fill(4, 25, 7, 27, '.')
r.fill(16, 1, 19, 1, '=').fill(12, 4, 22, 4)
for k in range(5): r.fill(10 - 2 * k, 5 + k, 11 - 2 * k, 5 + k)          # first flight, down to the west
r.fill(1, 12, 5, 12)
for k in range(9): r.fill(min(22, 6 + 2 * k), 13 + k, min(22, 7 + 2 * k), 13 + k)   # second flight, down to the east
r.fill(21, 23, 22, 23, '=')
_put(r, [(8, 18, 'f'), (2, 11, 'k'), (20, 3, 'k'), (5, 1, 'l'), (18, 7, 'l')])
_add(r, dict(t='ra_water', x=1, y=24, w=22), dict(t='ra_amb', type='rot_crawler', x=14, y=24, look='water'),
     dict(t='ra_amb', type='rot_crawler', x=19, y=24, look='water'))

# ---------------------------------------------------------------- K7 The Clerestory (grand): floor, rafters, clerestory walk
r = _ra_room('K7', 'The Clerestory', 'cathedral', 388, -100, 104, 36, indoor=True, needs=_T, grand=True, chests=['gold'])
r.walls().open('N', 4, 7).open('N', 54, 57).open('N', 88, 91).open('S', 24, 27).open('S', 92, 95).fill(0, 33, 103, 35)
r.fill(24, 33, 27, 35, '.').fill(22, 33, 23, 34, '.').fill(28, 33, 29, 34, '.')
r.fill(92, 33, 95, 35, '.').fill(90, 33, 91, 34, '.').fill(96, 33, 97, 34, '.')
r.fill(1, 28, 14, 32).fill(15, 31, 16, 32).fill(0, 24, 0, 27, 'B')             # the altar dais; the sacristy wall behind it
for y, x0, x1 in [(29, 30, 33), (26, 30, 33), (29, 78, 81), (26, 78, 81)]:
    r.fill(x0, y, x1, y, '=')
for x0, x1 in [(18, 44), (50, 76), (82, 97)]:
    r.fill(x0, 22, x1, 22, '=')                                                  # the rafters

r.fill(1, 10, 24, 11).fill(30, 10, 62, 11).fill(68, 10, 97, 11)                  # the clerestory walk
r.fill(98, 11, 99, 20)                                                           # the chimney pillar (wall-jump up to the walk)
for x0 in (4, 54, 88):
    for y in (7, 4, 1):
        r.fill(x0, y, x0 + 3, y, '=')
_put(r, [(40, 32, 's'), (70, 32, 's'), (60, 32, 'K'), (62, 21, 'a'), (46, 9, 'e'), (36, 16, 'f'), (86, 16, 'f'), (80, 9, 'C'),
         (12, 1, 'l'), (40, 1, 'l'), (72, 1, 'l'), (98, 1, 'l'), (3, 27, 'k'), (13, 27, 'k'), (101, 32, 'u'), (20, 9, 'u')])
_add(r, SY('lore', x=10, y=27, page='ra_12', look='book'))

# ---------------------------------------------------------------- K8 Confessional Row: the booths are not empty
r = _ra_room('K8', 'Confessional Row', 'cathedral', 440, -64, 48, 14, indoor=True, needs=_T)
r.walls().open('N', 40, 43).open('S', 28, 31).fill(0, 11, 47, 13).fill(28, 11, 31, 13, '.').fill(26, 11, 27, 12, '.').fill(32, 11, 33, 12, '.')
r.fill(36, 10, 46, 10).fill(38, 7, 45, 7, '=').fill(39, 4, 44, 4, '=').fill(40, 1, 43, 1, '=')
_put(r, [(38, 9, 's'), (5, 1, 'l'), (17, 1, 'l'), (34, 1, 'l'), (2, 10, 'k'), (46, 9, 'k')])
_add(r, SY('door', x=3, y=10, id='k3', to='K3', toId='k8', look='arch'),
     KT('gate', x=7, y=10, id='gk', persist=True),
     KT('lever', x=9, y=10, id='klv', targets=['gk'], once=True, msg='The iron grille lifts. The Bell Ascent lies beyond.'),
     dict(t='ra_amb', type='hollow_soldier', x=12, y=10, look='booth'), dict(t='ra_amb', type='ember_acolyte', x=20, y=10, look='booth'),
     dict(t='ra_amb', type='hollow_soldier', x=24, y=10, look='booth'), D('booth', x=16, y=10))

# ---------------------------------------------------------------- K9 Chandelier Crossing (parkour): they sway, then they fall
r = _ra_room('K9', 'Chandelier Crossing', 'cathedral', 420, -50, 56, 20, indoor=True, needs=_T, parkour=True, chests=['emberstone'])
r.walls().open('W', 7, 10).open('N', 48, 51).fill(1, 11, 6, 19).fill(0, 18, 55, 19).fill(7, 17, 43, 17, '^').fill(44, 8, 54, 17)
r.fill(46, 4, 53, 4, '=').fill(48, 1, 51, 1, '=').fill(23, 4, 27, 4)
_put(r, [(25, 3, 'C'), (3, 10, 'k'), (52, 7, 'k'), (10, 1, 'l'), (36, 1, 'l')])
for i, (x, y) in enumerate([(9, 11), (15, 10), (21, 12), (27, 10), (33, 9), (39, 10), (18, 7)]):
    _add(r, KT('crumble', x=x, y=y, w=3, delay=1.0, respawn=2.5, id=f'ch{i}'), dict(t='ra_chand', x=x + 1, y=y - 1, target=f'ch{i}'))

# ---------------------------------------------------------------- K10 Organ Loft (puzzle): the hymn in the choir book
r = _ra_room('K10', 'Organ Loft', 'cathedral', 388, -118, 32, 18, indoor=True, needs=_T, puzzle=True, chests=['emberstone'])
r.walls().open('S', 4, 7).fill(0, 15, 31, 17).fill(4, 15, 7, 17, '.').fill(2, 15, 3, 16, '.').fill(8, 15, 9, 16, '.').fill(4, 17, 5, 17, '=')
_put(r, [(29, 14, 'C'), (6, 1, 'l'), (25, 1, 'l'), (2, 14, 'k'), (30, 14, 'k')])
_add(r, KT('stop', x=11, y=13, id='moon', group='hymn', note=2), KT('stop', x=14, y=13, id='root', group='hymn', note=0),
     KT('stop', x=17, y=13, id='sun', group='hymn', note=4), KT('stop', x=20, y=13, id='bell', group='hymn', note=7),
     KT('seq', x=12, y=14, id='hymn', group='hymn', order=['sun', 'bell', 'moon', 'root'], targets=['vestry'], msg='The hymn is whole. Something unlocks behind the organ.'),
     KT('gate', x=26, y=14, id='vestry', persist=True),
     SY('lore', x=23, y=14, page='ra_9', look='book'),
     dict(t='ra_hint', x=22, y=14, seq='hymn', text='The choir book sings of the Sun, then the Bell, then the Moon, then the Root. Mark the carvings over the stops.'))

# ---------------------------------------------------------------- K11 The Rose Window (vista)
r = _ra_room('K11', 'The Rose Window', 'cathedral', 424, -120, 40, 20, indoor=True, needs=_T, vista=True)
r.walls().open('S', 18, 21).fill(0, 17, 39, 19).fill(18, 17, 21, 19, '.').fill(16, 17, 17, 18, '.').fill(22, 17, 23, 18, '.').fill(18, 19, 19, 19, '=')
_put(r, [(3, 16, 'k'), (36, 16, 'k'), (8, 1, 'l'), (31, 1, 'l')])
_add(r, SY('bench', x=11, y=16, id='bench', view=[20, 10], lore='ra_10'))

# ---------------------------------------------------------------- K12 Bellrope Trial: climb the ropes before the bell tolls thrice
r = _ra_room('K12', 'Bellrope Trial', 'cathedral', 468, -156, 24, 56, indoor=True, needs=['talon', 'wings'], trial=True)
r.walls().open('S', 8, 11).fill(0, 53, 23, 55).fill(8, 53, 11, 55, '.').fill(6, 53, 7, 54, '.').fill(12, 53, 13, 54, '.').fill(8, 55, 9, 55, '=')
r.fill(1, 14, 1, 46, '^').fill(22, 10, 22, 46, '^')
_ROPES = [(15, 44), (8, 36), (15, 28), (8, 20), (15, 12)]
for x, y in _ROPES:
    r.fill(x - 1, y - 1, x + 1, y - 1)                                     # the beams the ropes hang from
r.fill(1, 11, 7, 12)
_put(r, [(3, 52, 'k'), (22, 52, 'k'), (5, 1, 'l'), (18, 1, 'l')])
_add(r, SY('trial', x=20, y=52, id='bellrope', par=22, reward='c_x3_chime', region='Sunken Cathedral', name='The Bellrope Trial'),
     SY('trial_goal', x=4, y=10, trial='bellrope'),
     *[KT('swing', x=x, y=y, len=6, amp=25, period=2.6, phase=i * 0.3, rope='rope') for i, (x, y) in enumerate(_ROPES)])

# ---------------------------------------------------------------- K13 The Walled Sacristy (secret, behind the altar)
r = _ra_room('K13', 'The Walled Sacristy', 'cathedral', 372, -82, 16, 14, indoor=True, needs=_T, secret=True, chests=['shard'])
r.walls().open('E', 6, 9).fill(0, 10, 15, 13)
_put(r, [(4, 9, 'C'), (2, 9, 'k'), (8, 2, 'l')])
_add(r, SY('lore', x=9, y=9, page='ra_11', look='book'))

# ---------------------------------------------------------------- anchors: K1 (the arch in the nave), K3 (the grille at the Bell Ascent)
_add(ROOM('K1'), SY('door', x=41, y=10, id='k5', to='K5', toId='k1', look='arch'))
_add(ROOM('K3'), SY('door', x=13, y=24, id='k8', to='K8', toId='k3', look='arch'))


# ================================================================================================ decor (50_ra.js RA_P)
def _deco(id, *items):
    _add(ROOM(id), *[D(k, x=x, y=y, **kw) for (k, x, y, *rest) in items for kw in [rest[0] if rest else {}]])


# ---- ramparts
_add(ROOM('R5'), dict(t='ra_wall', x=2, y=1, w=20, h=18, a=1), dict(t='ra_wall', x=24, y=14, w=102, h=5, a=1), dict(t='ra_wall', x=53, y=19, w=10, h=3, a=1),
     dict(t='ra_wall', x=100, y=19, w=8, h=3, a=1),
     dict(t='ra_hint', x=97, y=18, near=40, text='The mortar here is cracked and dry. A few good blows might bring it down.'))
_deco('R5', *[('crenel', x, 11) for x in range(26, 124, 4) if not any(a - 2 <= x <= b + 2 for a, b in [(36, 40), (70, 74), (86, 90)])],
      ('trebuchet', 80, 11, {'dx': 8, 'sc': 2}), ('beacon', 52, 2), ('wbanner', 49, 8), ('wbanner', 52, 8, {'flip': 1}), ('wbanner', 110, 8), ('wbanner', 113, 8, {'flip': 1}),
      ('pbanner', 33, 11), ('pbanner', 65, 11, {'flip': 1}), ('pbanner', 101, 11),
      ('stall', 44, 18), ('stall', 50, 18), ('hay', 64, 18), ('horse', 78, 18), ('barrels', 93, 18), ('cart', 113, 18), ('rubble', 38, 15), ('rubble', 72, 15), ('rubble', 88, 15),
      ('wbanner', 11, 1), ('rack', 5, 18), ('barrels', 17, 18), ('rubble', 30, 18), ('dummy', 26, 18))
_deco('R9', ('wbanner', 16, 1), ('beacon', 6, 4), ('rack', 20, 22), ('barrels', 7, 19), ('rack', 5, 13, {'flip': 1}), ('rubble', 17, 7), ('wbanner', 4, 1, {'flip': 1}))
_deco('R10', ('flag', 28, 6), ('pbanner', 48, 7), ('rubble', 11, 7), ('rubble', 53, 6), ('flag', 3, 7, {'flip': 1}), ('pbanner', 61, 7, {'flip': 1}))
_deco('R11', ('flag', 25, 5), ('beacon', 13, 5), ('pbanner', 3, 7), ('rubble', 23, 5))
_deco('R6', ('stall', 20, 10), ('stall', 26, 10), ('stall', 32, 10), ('hay', 37, 10), ('horse', 24, 10), ('cart', 8, 9), ('barrels', 39, 10), ('hay', 24, 5), ('rack', 45, 10, {'flip': 1}))
_deco('R7', ('bunk', 10, 10), ('bunk', 24, 10), ('bunk', 38, 10), ('rack', 41, 5), ('dummy', 28, 10), ('barrels', 17, 10), ('wbanner', 16, 1), ('wbanner', 30, 1), ('rack', 46, 5, {'flip': 1}))
_deco('R8', ('winch', 27, 6), ('barrels', 40, 6), ('rubble', 10, 11), ('cart', 36, 11), ('barrels', 6, 11), ('wbanner', 42, 1), ('rack', 17, 6))
_deco('R12', ('winch', 8, 16), ('barrels', 29, 16), ('rubble', 18, 16), ('winch', 22, 16, {'flip': 1}), ('wbanner', 12, 1))
_deco('R13', ('pbanner', 14, 10), ('pbanner', 34, 10, {'flip': 1}), ('rack', 37, 10, {'flip': 1}), ('dummy', 18, 10), ('dummy', 30, 10), ('wbanner', 22, 1), ('wbanner', 27, 1, {'flip': 1}), ('barrels', 5, 9))
_deco('R14', ('barrels', 10, 9), ('wbanner', 4, 1), ('rack', 1, 9), ('hay', 13, 9, {'alpha': 0.9}))

# ---- catacombs
_deco('C7', ('rootc', 13, 2), ('rootc', 28, 4), ('rootc', 40, 3), ('bshelf', 16, 10), ('bshelf', 38, 10), ('skulls', 6, 9), ('coffin', 34, 10), ('skulls', 44, 10), ('rootc', 3, 5))
_deco('C8', ('bshelf', 8, 28), ('bshelf', 24, 28), ('bshelf', 44, 28), ('bshelf', 76, 28), ('bshelf', 90, 28), ('bshelf', 18, 19), ('bshelf', 48, 19), ('bshelf', 84, 17),
      ('bshelf', 18, 10), ('bshelf', 54, 10), ('bshelf', 80, 10), ('skullpillar', 34, 28), ('skullpillar', 59, 28), ('skullpillar', 73, 28),
      ('bonechand', 40, 1), ('bonechand', 64, 1), ('bonechand', 88, 1), ('rootc', 50, 1), ('rootc', 22, 1), ('rootc', 76, 13),
      ('sarc', 48, 19), ('coffin', 12, 19), ('skulls', 70, 28), ('skulls', 8, 28), ('skulls', 90, 17), ('skulls', 30, 5), ('coffin', 38, 5), ('sarc', 20, 10), ('skulls', 60, 10))
_deco('C11', ('skulls', 20, 27), ('rootc', 10, 1), ('coffin', 21, 5), ('bonechand', 17, 9), ('skulls', 13, 44, {'alpha': 0.8}))
_deco('C9', ('coffin', 16, 6), ('coffin', 6, 15), ('coffin', 17, 18), ('coffin', 5, 21), ('coffin', 15, 24), ('coffin', 4, 29), ('bshelf', 11, 33), ('rootc', 16, 1), ('skulls', 18, 12), ('skulls', 4, 9), ('sarc', 18, 30))
_deco('C13', ('bshelf', 6, 11), ('bshelf', 16, 11), ('skulls', 2, 11), ('skulls', 10, 11), ('skulls', 21, 11), ('rootc', 14, 1), ('skullpillar', 26, 11, {'dx': -6}))
_deco('C12', ('tomb', 10, 13, {'v': 2}), ('tomb', 16, 13, {'v': 0}), ('tomb', 22, 13, {'v': 3}), ('tomb', 28, 13, {'v': 1}), ('bonechand', 20, 1), ('skulls', 36, 13), ('bshelf', 3, 8))
_deco('C10', ('bshelf', 8, 10), ('bshelf', 22, 10), ('bshelf', 34, 10), ('sarc', 14, 10), ('skulls', 43, 10), ('coffin', 45, 10, {'back': False, 'dx': 26, 'hideIf': [47, 8]}), ('rootc', 30, 5))
_deco('C14', ('digger', 9, 10), ('skulls', 14, 10), ('bshelf', 7, 10), ('coffin', 2, 10))
_deco('C15', ('sarc', 7, 9), ('skulls', 3, 9), ('bonechand', 8, 1), ('bshelf', 12, 9))

# ---- cathedral
_deco('K5', *[('lancet', x, 10, {'dy': -24, 'v': v}) for x, v in [(9, 'gold'), (19, 'rose'), (38, 'blue'), (45, 'gold')]],
      *[('kneel', x, 10, {'flip': x > 24}) for x in (7, 11, 19, 33, 41)], ('saint', 25, 10), ('votive', 13, 10), ('pew', 4, 10))
_deco('K6', ('saint', 2, 11), ('sarc', 12, 24), ('votive', 20, 3), ('censer', 9, 1), ('lancet', 21, 16, {'v': 'blue', 'dy': -8}), ('coffin', 19, 24))
_deco('K7', *[('lancet', x, 9, {'v': v}) for x, v in [(8, 'gold'), (16, 'rose'), (36, 'blue'), (44, 'gold'), (52, 'rose'), (74, 'blue'), (82, 'gold'), (94, 'rose')]],
      *[('lancet', x, 21, {'v': v, 'alpha': 0.95}) for x, v in [(24, 'rose'), (40, 'gold'), (60, 'blue'), (70, 'rose'), (90, 'gold')]],
      *[('pew', x, 32) for x in (36, 44, 52, 66, 74)], ('saint', 86, 32, {'sc': 2}), ('altar', 7, 27), ('votive', 20, 32), ('votive', 58, 32),
      ('chand', 46, 12), ('chand', 84, 12), ('chand', 20, 12), ('censer', 60, 1), ('saint', 3, 27))
_deco('K8', ('lancet', 20, 10, {'v': 'rose', 'dy': -40}), ('lancet', 38, 9, {'v': 'blue', 'dy': -40}), ('votive', 40, 9), ('censer', 17, 1), ('pew', 44, 9), ('saint', 5, 10))
_deco('K9', ('lancet', 13, 16, {'v': 'blue'}), ('lancet', 25, 16, {'v': 'rose'}), ('lancet', 37, 16, {'v': 'gold'}), ('rubble', 20, 16), ('rubble', 31, 16), ('votive', 48, 7), ('saint', 53, 7))
_deco('K10', ('organ', 15, 14, {'dx': 8, 'sc': 2}), ('emblem', 11, 11, {'v': 1}), ('emblem', 14, 11, {'v': 2}), ('emblem', 17, 11, {'v': 0}), ('emblem', 20, 11, {'v': 3}),
      ('votive', 4, 14), ('lancet', 9, 14, {'v': 'gold', 'dy': -20}), ('censer', 26, 1))
_deco('K11', ('pew', 7, 16), ('pew', 30, 16), ('saint', 4, 16), ('saint', 35, 16), ('votive', 16, 16), ('votive', 25, 16), ('censer', 12, 1))
_add(ROOM('K11'), dict(t='ra_rose', x=19, y=4, dx=8))
_deco('K12', ('bigbell', 6, 10), ('lancet', 12, 30, {'v': 'blue'}), ('lancet', 12, 46, {'v': 'rose'}), ('wbanner', 4, 1), ('votive', 5, 52))
_deco('K13', ('saint', 12, 9), ('votive', 6, 9), ('censer', 3, 1), ('altar', 8, 9, {'alpha': 0.95}))


# ---- more light in the dark places (candles 'k', lanterns 'l'), and the Ossuary's heart
_put(ROOM('C8'), [(8, 19, 'k'), (27, 19, 'k'), (41, 19, 'k'), (57, 19, 'k'), (15, 10, 'k'), (50, 10, 'k'), (84, 10, 'k'), (78, 17, 'k'), (4, 5, 'k'), (42, 5, 'k'),
                  (26, 28, 'k'), (50, 28, 'k'), (93, 28, 'k'), (24, 13, 'l'), (54, 13, 'l'), (84, 13, 'l'), (8, 22, 'l')])
_deco('C8', ('rootheart', 66, 1, {'sc': 1.6}))
_put(ROOM('C7'), [(24, 10, 'k'), (40, 10, 'k'), (22, 5, 'l')])
_put(ROOM('C9'), [(20, 6, 'k'), (8, 15, 'k'), (14, 24, 'k'), (20, 30, 'k'), (3, 21, 'k'), (18, 18, 'k'), (5, 23, 'l')])
_put(ROOM('C10'), [(24, 10, 'k'), (32, 10, 'k'), (22, 5, 'l')])
_put(ROOM('C11'), [(14, 9, 'l'), (20, 9, 'l'), (21, 5, 'k'), (22, 27, 'k')])
_put(ROOM('C12'), [(8, 13, 'k'), (33, 13, 'k'), (12, 1, 'l'), (28, 1, 'l')])
_put(ROOM('C13'), [(8, 11, 'k'), (18, 11, 'k'), (26, 11, 'k')])
_put(ROOM('C15'), [(4, 3, 'k'), (2, 1, 'l')])
# ---- torches, arrow slits and trophies on the walls
_deco('R5', ('torch', 30, 16), ('torch', 64, 16), ('torch', 82, 16), ('torch', 116, 16), ('torch', 12, 16), ('torch', 16, 8), ('slit', 4, 6), ('slit', 19, 12), ('shields', 108, 16))
_deco('R9', ('torch', 12, 21), ('torch', 11, 16), ('torch', 14, 9), ('slit', 3, 9), ('slit', 20, 3), ('shields', 5, 17))
_deco('R6', ('torch', 14, 7), ('torch', 35, 8), ('slit', 8, 5), ('slit', 41, 4))
_deco('R7', ('torch', 6, 7), ('torch', 33, 7), ('shields', 16, 7), ('shields', 28, 7), ('slit', 21, 3), ('slit', 43, 2))
_deco('R8', ('torch', 12, 4), ('torch', 36, 4), ('torch', 15, 10), ('torch', 40, 10))
_deco('R12', ('torch', 4, 8), ('torch', 28, 12), ('slit', 15, 4), ('shields', 10, 13))
_deco('R13', ('torch', 12, 6), ('torch', 38, 6), ('shields', 25, 6), ('slit', 18, 3), ('slit', 32, 3))
_deco('R14', ('torch', 13, 5), ('shields', 7, 6))
_deco('C7', ('torch', 10, 6), ('torch', 36, 6))
_deco('C10', ('torch', 14, 8), ('torch', 30, 8))
_deco('C13', ('torch', 6, 7), ('torch', 24, 7))
# ---- lamps for the tower and the flooded stair
_put(ROOM('K12'), [(x + 1, y, 'l') for x, y in _ROPES] + [(12, 52, 'k'), (16, 52, 'k')])
_put(ROOM('K6'), [(3, 13, 'l'), (14, 5, 'l'), (4, 11, 'k'), (21, 17, 'k'), (22, 3, 'k')])
_deco('K6', ('votive', 13, 3), ('lancet', 9, 24, {'v': 'rose', 'dy': -60, 'alpha': 0.9}))
