# ============================================================ THORNVEIL WOOD (agent T) -- the Root's first seedlings, grown wild
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# An early optional region (after Gravetusk): entered by climbing out of a crack in the Ossuary's vault (C2) -- the
# climb needs the Hound's Talon (wall-jump). Tiles (web/src/30_thornveil.js):
#   '('  thorn bramble (id 35): non-solid bush, hurts on contact (foes too)
#   ')'  thorn wall    (id 36): solid until slashed apart (stays cut)
# Custom spawns: tv_prop (decor; back=True paints giant trees into the room's back layer), tv_fog (a drifting fog
# bank that hides whatever is inside it until you are close), tv_pod (spore pod: drops a spore cloud when you pass
# below), tv_gate (boss fog reaching the ceiling), tv_hatch (the thorn lattice in TV7's floor: the shortcut).
#
#   TV1 The Rootclimb           48..53  x 28..41   wall-jump shaft up from C2's vault
#   TV2 Mossgrave Verge          0..47  x 28..41   shrine; the hatch shaft to TV7 (shortcut, opened from above)
#   TV3 The Bramble Thicket    -48..-1  x 28..41   Briarheart Shrine (before the Coven); brambles, a thorn wall, briar scythe
#   TV4 Hollow of the Coven    -84..-49 x 28..41   mini-boss: the Thorn Coven
#   TV5 Mistfell Ascent       -108..-85 x 15..41   the climb; hook-only alcove (c_moss)
#   TV6 The Hanging Canopy     -84..-25 x 15..27   thorn pit, branches, a thorn wall, thornwood staff
#   TV7 Warden's Threshold     -24..11  x 15..27   Antlergate Shrine (before the Warden); lever -> thorn hatch into TV2; grave
#   TV8 The Antlered Grove      12..59  x 15..27   main boss: the Antlered Warden
SOLID.add(')')
FLYING.add('tv_wisp')


def _tv_paint(r, rows):
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            r.g[y][x] = ch
    return r


def _tv(kind, x, y, **kw):
    return dict(t='tv_prop', kind=kind, x=x, y=y, **kw)


def _en(type_, x, y, **kw):
    return dict(t='enemy', type=type_, x=x, y=y, **kw)


# ---------------------------------------------------------------- C2 (anchor): a crack in the Ossuary's vault
_c2 = ROOM('C2')
_c2.fill(1, 0, 3, 1, '.')                  # the crack (global x 49..51) -> TV1
_c2.fill(5, 2, 5, 6)                       # a hanging root-mass: with the west wall it makes a wall-jump chimney

# ---------------------------------------------------------------- TV1 The Rootclimb
r = Room('TV1', 'The Rootclimb', 'thornveil', 48, 28, 6, 14, indoor=True)
_tv_paint(r, [
    "######",   # 0
    "######",   # 1
    ".....#",   # 2  -> Mossgrave Verge
    ".....#",   # 3
    ".....#",   # 4
    ".....#",   # 5
    "#....#",   # 6
    "#....#",   # 7
    "#....#",   # 8
    "#....#",   # 9
    "#....#",   # 10
    "#....#",   # 11
    "#....#",   # 12
    "#...##",   # 13 <- the crack in C2's vault
])
r.put(2, 6, 'r').put(3, 10, 'x')

# ---------------------------------------------------------------- TV2 Mossgrave Verge (shrine)
r = Room('TV2', 'Mossgrave Verge', 'thornveil', 0, 28, 48, 14, indoor=True, shrine='Mossgrave Shrine',
         graves=['tv1'], items=['emberstone'],
         spawns=[_en('tv_husk', 13, 10),
                 _tv('tree', 9, 10, back=True), _tv('tree', 36, 10, back=True, v=1), _tv('tree', 21, 10, back=True, v=2),
                 _tv('idol', 22, 10), _tv('ribbons', 31, 10), _tv('fern', 3, 10), _tv('fern', 16, 10), _tv('fern', 38, 10),
                 _tv('shroom', 44, 5), _tv('fern', 43, 5)])
_tv_paint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "####...#########################################",  # 0   the hatch shaft (x 4..6) up to TV7
    "####...#########################################",  # 1
    "####............................................",  # 2   -> Rootclimb (east, rows 2..5)
    "####............................................",  # 3
    "#...............................................",  # 4
    "#...====........................................",  # 5
    "#.......................................########",  # 6   the root ledge
    "........................................########",  # 7   <- Bramble Thicket (west, rows 7..10)
    "........====........................===.########",  # 8
    "........................................########",  # 9
    "........................................########",  # 10
    "################################################",  # 11
    "################################################",  # 12
    "################################################",  # 13
])
for x, y, ch in [(28, 10, 'S'), (18, 10, 'g'), (5, 4, 'i'), (2, 10, 'k'), (34, 10, 'k'), (12, 2, 'x'), (30, 2, 'x'),
                 (24, 2, 'r'), (41, 2, 'r'), (15, 10, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV3 The Bramble Thicket
r = Room('TV3', 'The Bramble Thicket', 'thornveil', -48, 28, 48, 14, indoor=True, shrine='Briarheart Shrine', chests=['w:briar_scythe'], items=['emberstone'],
         spawns=[_en('tv_hound', 9, 10), _en('tv_hound', 41, 10), _en('tv_wisp', 18, 5, air=True), _en('tv_husk', 35, 10),
                 dict(t='tv_fog', x=34, y=2, w=13, h=9),
                 dict(t='tv_pod', x=16, y=2), dict(t='tv_pod', x=40, y=2),
                 _tv('tree', 5, 10, back=True, v=1), _tv('tree', 40, 10, back=True), _tv('fern', 13, 10), _tv('fern', 44, 10),
                 _tv('ribbons', 25, 10), _tv('shroom', 2, 4)])
_tv_paint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "################################################",  # 0
    "################################################",  # 1
    "#..........)...........###########.............#",  # 2   nook behind a thorn wall (chest)
    "#..........)...........###########.............#",  # 3
    "#..........)...........###########.............#",  # 4
    "#############..........###########.............#",  # 5   shelf over the west door
    "#############..........###########.............#",  # 6
    "............................)...................",  # 7   thorn wall across the path (col 28)
    "..............===...........)...................",  # 8
    "............................)...................",  # 9
    "....((....((................)........(((........",  # 10  brambles
    "################################################",  # 11
    "################################################",  # 12
    "################################################",  # 13
])
for x, y, ch in [(20, 10, 'S'), (4, 4, 'C'), (45, 10, 'i'), (8, 1, 'r'), (18, 1, 'x'), (38, 1, 'r'), (44, 1, 'x'), (33, 10, 'b'), (16, 10, 'k')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV4 Hollow of the Coven (mini-boss)
r = Room('TV4', 'Hollow of the Coven', 'thornveil', -84, 28, 36, 14, indoor=True, boss='coven', entry='E',
         spawns=[dict(t='boss', kind='coven', x=16, y=10),
                 dict(t='tv_gate', kind='coven', x=1, y=10, top=2, exit=True),
                 dict(t='tv_gate', kind='coven', x=34, y=10, top=2),
                 _tv('tree', 8, 10, back=True, v=2), _tv('tree', 27, 10, back=True, v=1),
                 _tv('idol', 5, 10), _tv('idol', 30, 10, v=1), _tv('ribbons', 12, 10), _tv('ribbons', 23, 10)])
_tv_paint(r, [
    #0         1         2         3
    #012345678901234567890123456789012345
    "####################################",  # 0
    "####################################",  # 1
    "#..................................#",  # 2
    "#..................................#",  # 3
    "#..................................#",  # 4
    "#..................................#",  # 5
    "#..................................#",  # 6
    ".......====..............====.......",  # 7   -> Mistfell (west) / <- Thicket (east)
    "....................................",  # 8
    "....................................",  # 9
    "....................................",  # 10
    "####################################",  # 11
    "####################################",  # 12
    "####################################",  # 13
])
for x, y, ch in [(6, 2, 'x'), (17, 2, 'r'), (29, 2, 'x'), (3, 10, 'k'), (32, 10, 'k')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV5 Mistfell Ascent (the climb, hook alcove)
r = Room('TV5', 'Mistfell Ascent', 'thornveil', -108, 15, 24, 27, indoor=True, graves=['tv2'], items=['c_moss'],
         spawns=[_en('tv_wisp', 12, 9, air=True), _en('tv_wisp', 7, 16, air=True), _en('tv_husk', 8, 23),
                 dict(t='tv_fog', x=5, y=9, w=12, h=9),
                 dict(t='tv_pod', x=14, y=3), dict(t='tv_pod', x=8, y=3),
                 _tv('tree', 11, 23, back=True, v=2), _tv('fern', 3, 23), _tv('fern', 19, 9), _tv('shroom', 3, 6),
                 _tv('vine', 17, 3), _tv('vine', 20, 3)])
_tv_paint(r, [
    #0         1         2
    #012345678901234567890123
    "########################",  # 0
    "########################",  # 1
    "########################",  # 2
    "#.......................",  # 3   the moss alcove (hook-only: the shelf overhangs the wall below;
    "#.......................",  # 4    it is reached by swinging from the rope-roots)
    "#.......................",  # 5
    "#.......................",  # 6   -> Hanging Canopy (east, rows 6..9)
    "#####...................",  # 7
    "#####...................",  # 8
    "#.......................",  # 9
    "#...............########",  # 10  top ledge
    "#...............########",  # 11
    "#.......................",  # 12
    "#..........===..........",  # 13
    "#.......................",  # 14
    "#...........====........",  # 15
    "#.......................",  # 16
    "#.......................",  # 17
    "#......====.............",  # 18
    "#.......................",  # 19
    "#.......................",  # 20  <- Hollow of the Coven (east, rows 20..23)
    "#.............====......",  # 21
    "#.......................",  # 22
    "#.......................",  # 23
    "########################",  # 24
    "########################",  # 25
    "########################",  # 26
])
# the east edge above/below the doors is open space inside the room: close it
r.fill(23, 1, 23, 5).fill(23, 10, 23, 19).fill(23, 1, 23, 2)
for x, y, ch in [(2, 6, 'i'), (4, 23, 'g'), (12, 3, '@'), (7, 3, '@'), (20, 23, 'k'), (15, 1, 'x'), (9, 1, 'r'), (2, 9, 'r')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV6 The Hanging Canopy
r = Room('TV6', 'The Hanging Canopy', 'thornveil', -84, 15, 60, 13, indoor=True, items=['emberstone', 'w:thornwood_staff'],
         spawns=[_en('tv_hound', 14, 9), _en('tv_husk', 51, 9), _en('tv_wisp', 30, 6, air=True), _en('tv_wisp', 54, 3, air=True),
                 dict(t='tv_fog', x=43, y=1, w=16, h=9),
                 dict(t='tv_pod', x=24, y=1), dict(t='tv_pod', x=41, y=1),
                 _tv('tree', 7, 9, back=True), _tv('tree', 44, 9, back=True, v=2), _tv('tree', 55, 9, back=True, v=1),
                 _tv('ribbons', 17, 9), _tv('fern', 3, 9), _tv('fern', 45, 9), _tv('vine', 26, 1), _tv('vine', 36, 1)])
_R = ['#' * 60,
      '#' + '.' * 45 + '###' + '.' * 10 + '#']
_tv_paint(r, _R + [_R[1]] + [
    _R[1],
    _R[1], _R[1],
    '.' * 46 + '###' + '.' * 11,                                            # 6   <- Mistfell / -> Threshold
    '.' * 47 + ')' + '.' * 4 + '====' + '.' * 4,                            # 7   thorn wall under the root-knot
    '.' * 22 + '====' + '.' * 5 + '====' + '.' * 4 + '====' + '.' * 4 + ')' + '.' * 12,   # 8  branches over the pit
    '.' * 47 + ')' + '.' * 12,                                              # 9
    '#' * 21 + '^' * 22 + '#' * 17,                                         # 10  the thorn pit
    '#' * 60, '#' * 60])
for x, y, ch in [(32, 7, 'i'), (53, 6, 'i'), (6, 1, 'r'), (13, 1, 'x'), (39, 1, 'x'), (54, 1, 'r'), (57, 9, 'k'), (10, 9, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV7 Warden's Threshold (the shortcut lever)
r = Room('TV7', 'Warden\'s Threshold', 'thornveil', -24, 15, 36, 13, indoor=True, shrine='Antlergate Shrine', graves=['tv3'], chests=['shard'],
         spawns=[dict(t='tv_hatch', x=28, y=10, w=3),
                 _tv('tree', 5, 9, back=True, v=1), _tv('tree', 19, 9, back=True, v=2),
                 _tv('idol', 13, 9, v=1), _tv('idol', 31, 9), _tv('ribbons', 9, 9), _tv('fern', 22, 9), _tv('fern', 2, 9)])
_tv_paint(r, [
    #0         1         2         3
    #012345678901234567890123456789012345
    "####################################",  # 0
    "#..................................#",  # 1
    "#..................................#",  # 2
    "#..................................#",  # 3
    "#..................................#",  # 4
    "#..................................#",  # 5
    "....................................",  # 6   <- Canopy / -> the Grove
    "....................................",  # 7
    "....................................",  # 8
    "....................................",  # 9
    "############################...#####",  # 10  the thorn hatch (cols 28..30, global x 4..6) -> TV2
    "############################...#####",  # 11
    "############################...#####",  # 12
])
for x, y, ch in [(20, 9, 'S'), (16, 9, 'g'), (25, 9, 'L'), (6, 9, 'C'), (8, 1, 'x'), (21, 1, 'r'), (30, 1, 'x'), (33, 9, 'k'), (11, 9, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- TV8 The Antlered Grove (main boss)
r = Room('TV8', 'The Antlered Grove', 'thornveil', 12, 15, 48, 13, indoor=True, boss='warden', entry='W',
         spawns=[dict(t='boss', kind='warden', x=32, y=10),
                 dict(t='tv_gate', kind='warden', x=2, y=10, top=1),
                 _tv('tree', 9, 10, back=True, v=2), _tv('tree', 24, 10, back=True), _tv('tree', 39, 10, back=True, v=1),
                 _tv('idol', 44, 10, v=1), _tv('ribbons', 5, 10)])
_tv_paint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "################################################",  # 0
    "#..............................................#",  # 1
    "#..............................................#",  # 2
    "#..............................................#",  # 3
    "#..............................................#",  # 4
    "#..............................................#",  # 5
    "...............................................#",  # 6   <- Threshold (rows 6..9)
    "...............................................#",  # 7
    "...............................................#",  # 8
    "...............................................#",  # 9
    "##.............................................#",  # 10  a root step down into the grove
    "################################################",  # 11
    "################################################",  # 12
])
for x, y, ch in [(12, 1, 'r'), (20, 1, 'x'), (31, 1, 'r'), (42, 1, 'x'), (46, 10, 'k')]:
    r.put(x, y, ch)
