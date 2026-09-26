# ============================================================ THE DROWNED BARROWS (agent B) — tombs beneath the Cathedral, flooded by a black tide
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING). All module-level names are prefixed _db.
# Zone x 253..372, y 29..69; the connector DB1 starts one row higher (gy 28) because it hangs directly under its anchor
# K2 (bottom row gy 27). Entered through a grate in K2's floor (cols 39-40, clear of the spike pit 12-14 and slam cache 24-26).
# Gate: DB2 "The Flooded Crypt" — 24 tiles of black water whose surface tide drags you back east; cross on the Root Hook rings.
# Tiles: '"' deep water (id 40, non-solid; swimming = web/src/31_barrows.js, works in any room). '`' is reserved (id 41).
# Custom spawns (31_barrows.js): db_prop (decor), db_current (surface current rect), db_boat (the Ferryman's boat),
# boss ferryman / choir; Room kw tide=<row> gives a room a dynamic water line. Enemies: db_pilgrim, db_eel (swims: FLYING), db_barnacle.
FLYING.add('db_eel')


def _db_paint(r, rows):
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            r.g[y][x] = ch
    return r


def _db_deco(kind, x, y, **kw):
    return dict(t='db_prop', kind=kind, x=x, y=y, **kw)


def _db_en(type, x, y, **kw):
    return dict(t='enemy', type=type, x=x, y=y, **kw)


# ---------------------------------------------------------------- K2 (anchor): a rusted grate in the aisle floor (↓+Space)
_k2 = ROOM('K2')
if all(_k2.g[y][x] == '#' for x in (39, 40) for y in (11, 12, 13)):
    for _x in (39, 40):
        _k2.g[11][_x] = '='          # the grate: a one-way lid (the engine draws db_grate over it + a prompt)
        _k2.g[12][_x] = '.'
        _k2.g[13][_x] = '.'
else:
    print('barrows: K2 floor at cols 39-40 changed; grate skipped')

# ---------------------------------------------------------------- DB1 The Drowned Grate (connector, x 336..355, y 28..45)
r = Room('DB1', 'The Drowned Grate', 'barrows', 336, 28, 20, 18, indoor=True, items=['emberstone'], graves=['db1'],
         spawns=[_db_en('db_pilgrim', 9, 13),
                 _db_deco('lamp', 1, 13), _db_deco('bell', 12, 4), _db_deco('bones', 17, 13), _db_deco('window', 15, 13)])
_db_paint(r, [
    #0         1
    #01234567890123456789
    "###..###############",  # 0   chimney up to K2's grate (wall-jump; the grate is one-way)
    "###..###############",  # 1
    "###..###############",  # 2
    "###..###############",  # 3
    "#..................#",  # 4
    "#..................#",  # 5
    "#=======...........#",  # 6   rung that catches the drop
    "#..................#",  # 7
    "#..................#",  # 8
    "#..........=====...#",  # 9
    "....................",  # 10  <- Flooded Crypt (west) · Tide Stair gate (east, opened from the far side)
    "....................",  # 11
    ".....====...........",  # 12
    "....................",  # 13
    "#############\"\"\"\"\"##",  # 14  a still sump in the floor
    "#############\"\"\"\"\"##",  # 15
    "####################",  # 16
    "####################",  # 17
])
r.put(3, 5, 'i').put(5, 13, 'g')

# ---------------------------------------------------------------- DB2 The Flooded Crypt (hook gate, x 298..335, y 32..47)
# 24 tiles of black water between the landings; a surface tide drags anything afloat back east. Three golden rings.
# With Tidebreath you can dive beneath the tide (and fetch the relic lying on the bottom).
r = Room('DB2', 'The Flooded Crypt', 'barrows', 298, 32, 38, 16, indoor=True, items=['emberstone'],
         spawns=[dict(t='db_current', x=7, y=11, w=24, h=2, v=165, gate=True),
                 _db_en('db_eel', 17, 13), _db_en('db_pilgrim', 3, 9),
                 _db_deco('lamp', 32, 9), _db_deco('lamp', 5, 9), _db_deco('bell', 18, 2), _db_deco('statue', 34, 9)])
_W = '"' * 24
_db_paint(r, [
    #0         1         2         3
    #01234567890123456789012345678901234567
    "######################################",  # 0
    "######################################",  # 1
    "#....................................#",  # 2
    "#....................................#",  # 3
    "#....................................#",  # 4
    "#....................................#",  # 5
    "......................................",  # 6   <- Ossuary (west) · Drowned Grate (east)
    "......................................",  # 7
    "......................................",  # 8
    "......................................",  # 9
    "#######........................#######",  # 10
    "#######" + _W + "#######",                # 11  water surface (the tide runs here)
    "#######" + _W + "#######",                # 12
    "#######" + _W + "#######",                # 13
    "#######" + _W + "#######",                # 14
    "######################################",  # 15
])
for _x, _y in [(26, 3), (19, 2), (12, 3)]:
    r.put(_x, _y, '@')
r.put(19, 14, 'i')                           # on the bottom, under the tide (Tidebreath)

# ---------------------------------------------------------------- DB3 Ossuary of the Tide (shrine, x 274..297, y 32..47)
r = Room('DB3', 'Ossuary of the Tide', 'barrows', 274, 32, 24, 16, indoor=True, shrine='Tidewater Shrine', graves=['db2'],
         spawns=[_db_deco('lamp', 8, 9), _db_deco('lamp', 15, 9), _db_deco('bones', 3, 9), _db_deco('bones', 21, 9),
                 _db_deco('bell', 12, 2), _db_deco('window', 6, 9), _db_deco('window', 18, 9)])
_db_paint(r, [
    #0         1         2
    #012345678901234567890123
    "########################",  # 0
    "########################",  # 1
    "#......................#",  # 2
    "#......................#",  # 3
    "#......................#",  # 4
    "#......................#",  # 5
    "........................",  # 6   <- Sunken Chapels (west) · Flooded Crypt (east)
    "........................",  # 7
    "........................",  # 8
    "........................",  # 9
    "#####\"\"\"\"##########\"\"\"##",  # 10  two still pools in the floor
    "#####\"\"\"\"##########\"\"\"##",  # 11
    "########################",  # 12
    "########################",  # 13
    "########################",  # 14
    "########################",  # 15
])
r.put(12, 9, 'S').put(16, 9, 'g')

# ---------------------------------------------------------------- DB4 The Sunken Chapels (descent, x 253..273, y 30..55)
r = Room('DB4', 'The Sunken Chapels', 'barrows', 253, 30, 21, 26, indoor=True, items=['c_gill'], chests=['w:tidecleaver'],
         graves=['db3'], shrine='Mere Shrine',
         spawns=[_db_en('db_pilgrim', 16, 11), _db_en('db_barnacle', 11, 17), _db_en('db_eel', 7, 19),
                 _db_en('db_pilgrim', 7, 24, hidden=True),
                 _db_deco('bell', 16, 1), _db_deco('bell', 8, 1), _db_deco('window', 17, 11), _db_deco('lamp', 15, 24),
                 _db_deco('lamp', 9, 24), _db_deco('bones', 3, 17), _db_deco('lamp', 13, 11)])
_db_paint(r, [
    #0         1         2
    #012345678901234567890
    "#####################",  # 0
    "#...................#",  # 1
    "#...................#",  # 2
    "#...................#",  # 3
    "#...................#",  # 4
    "#...................#",  # 5
    "#.####..............#",  # 6   hook ledge (c_gill)
    "#...................#",  # 7
    "#...................#",  # 8
    "#...................#",  # 9
    "#...................#",  # 10
    "#....................",  # 11  <- Ossuary (east door rows 8..11)
    "#.....========#######",  # 12  level A + bridge
    "#.............#######",  # 13
    "#.............#######",  # 14
    "#........===......###",  # 15
    "#...................#",  # 16
    "#...................#",  # 17
    "#####\"\"\"\"\"####......#",  # 18  level B (a drowned chapel pool)
    "#####\"\"\"\"\"####......#",  # 19
    "#####\"\"\"\"\"#####==...#",  # 20
    "#....#####..........#",  # 21
    "#..............===..#",  # 22
    "#...................#",  # 23
    "#...................#",  # 24  level C
    "##....###############",  # 25  -> Ferryman's Mere below
])
for _y in (8, 9, 10, 11):
    r.g[_y][20] = '.'
r.put(10, 2, '@').put(3, 5, 'i').put(2, 17, 'C').put(12, 24, 'S').put(18, 24, 'g')

# ---------------------------------------------------------------- DB5 Ferryman's Mere (mini-boss, x 253..299, y 56..69)
r = Room('DB5', 'Ferryman\'s Mere', 'barrows', 253, 56, 47, 14, indoor=True, boss='ferryman', chests=['emberstone'],
         spawns=[dict(t='boss', kind='ferryman', x=30, y=8, air=True),
                 dict(t='db_boat', x=13, y=8, x0=10, x1=39),
                 _db_deco('lamp', 1, 4), _db_deco('lamp', 44, 7), _db_deco('statue', 42, 7), _db_deco('bones', 4, 4)])
_WL = '"' * 30
_db_paint(r, [
    #0         1         2         3         4
    #01234567890123456789012345678901234567890123456
    "##....#########################################",  # 0   <- Sunken Chapels above
    "#.............................................#",  # 1
    "#....====.....................................#",  # 2
    "#.............................................#",  # 3
    "#..............................................",  # 4   -> the Choir's Hollow (east door rows 4..7)
    "#######........................................",  # 5
    "#######........................................",  # 6
    "#######........................................",  # 7
    "##########..............................#######",  # 8   jetty (7-9) · east shore (40-46)
    "##########" + _WL + "#######",                     # 9   the black mere
    "##########" + _WL + "#######",                     # 10
    "##########" + _WL + "#######",                     # 11
    "##########" + _WL + "#######",                     # 12
    "###############################################",  # 13
])
for _x in (7, 8, 9):
    r.g[8][_x] = '#'
r.put(44, 7, 'F').put(24, 12, 'C')          # fog at the east door · a drowned coffer on the bottom (Tidebreath)

# ---------------------------------------------------------------- DB9 The Reliquary of Breath (shrine + Tidebreath, x 300..315, y 48..69)
# The last dry room before the Choir: a shrine, and on the altar by the arena door the relic that lets you breathe the black water.
r = Room('DB9', 'The Reliquary of Breath', 'barrows', 300, 48, 16, 22, indoor=True, shrine='Reliquary Shrine', items=['tidebreath'],
         spawns=[_db_deco('lamp', 1, 15), _db_deco('lamp', 14, 6), _db_deco('bones', 8, 15), _db_deco('window', 11, 15), _db_deco('statue', 10, 6)])
_db_paint(r, [
    #0123456789012345
    "################",  # 0
    "################",  # 1
    "#..............#",  # 2
    "#...............",  # 3   -> the Choir's Hollow (east door rows 3..6)
    "#...............",  # 4
    "#...............",  # 5
    "#...............",  # 6
    "#.........######",  # 7   the altar landing
    "#..............#",  # 8
    "#..............#",  # 9
    "#...====.......#",  # 10
    "#..............#",  # 11
    "...............#",  # 12  <- Ferryman's Mere (west door rows 12..15)
    ".........====..#",  # 13
    "...............#",  # 14
    "...............#",  # 15
    "################",  # 16
    "################",  # 17
    "################",  # 18
    "################",  # 19
    "################",  # 20
    "################",  # 21
])
r.put(4, 15, 'S').put(12, 6, 'i')

# ---------------------------------------------------------------- DB6 The Choir's Hollow (boss arena, x 316..355, y 48..69)
# A deep drowned pool under a sunken bell. The Choir hunts you in the water and seals the surface with a membrane of the
# drowned; strike the bell hanging in the middle to shatter the seal and breathe.
r = Room('DB6', 'The Choir\'s Hollow', 'barrows', 316, 48, 40, 22, indoor=True, boss='choir', clear=True,
         spawns=[dict(t='boss', kind='choir', x=24, y=19, air=True),
                 _db_deco('bell', 19, 6),
                 _db_deco('window', 9, 6, air=True), _db_deco('window', 30, 6, air=True)])
_P = '"' * 36
_db_paint(r, [
    #0         1         2         3
    #0123456789012345678901234567890123456789
    "########################################",  # 0
    "########################################",  # 1
    "#......................................#",  # 2
    "........................................",  # 3   doors rows 3..6 (west <- Reliquary, east -> Tide Stair)
    "........................................",  # 4
    "........................................",  # 5
    "........................................",  # 6
    "##" + _P + "##",                              # 7   the surface
    "##" + _P + "##",                              # 8
    "##" + _P + "##",                              # 9
    "##" + _P + "##",                              # 10
    "##" + _P + "##",                              # 11
    "##" + _P + "##",                              # 12
    "##" + _P + "##",                              # 13
    "##" + _P + "##",                              # 14
    "##" + _P + "##",                              # 15
    "##" + _P + "##",                              # 16
    "##" + _P + "##",                              # 17
    "##" + _P + "##",                              # 18
    "##" + _P + "##",                              # 19
    "########################################",  # 20
    "########################################",  # 21
])
r.put(1, 6, 'F').put(38, 6, 'F')

# ---------------------------------------------------------------- DB7 The Tide Stair (post-boss shortcut, x 356..372, y 36..61)
r = Room('DB7', 'The Tide Stair', 'barrows', 356, 36, 17, 26, indoor=True, items=['emberstone'],
         spawns=[_db_deco('lamp', 3, 5), _db_deco('lamp', 3, 23), _db_deco('bell', 9, 1), _db_deco('bones', 15, 23)])
_db_paint(r, [
    #0         1
    #01234567890123456
    "#################",  # 0
    "##..............#",  # 1   (solid above the gate: it reaches the ceiling)
    "................#",  # 2   <- Drowned Grate (west door rows 2..5, gate at col 1)
    "................#",  # 3
    "................#",  # 4
    "................#",  # 5
    "#########.......#",  # 6
    "#...............#",  # 7
    "#...............#",  # 8
    "#.........====..#",  # 9
    "#...............#",  # 10
    "#...............#",  # 11
    "#.....====......#",  # 12
    "#...............#",  # 13
    "#...............#",  # 14
    "..........====..#",  # 15  <- the Choir's Hollow (west door rows 15..18)
    "................#",  # 16
    "................#",  # 17
    "....====........#",  # 18
    "####............#",  # 19
    "#...............#",  # 20
    "#.........====..#",  # 21
    "#...............#",  # 22
    "#...............#",  # 23
    "##########\"\"\"\"###",  # 24  a flooded well down to the Pearl Cistern (Tidebreath)
    "##########\"\"\"\"###",  # 25
])
r.put(1, 2, 'G').put(8, 5, 'L').put(5, 5, 'i')

# ---------------------------------------------------------------- DB8 The Pearl Cistern (secret, underwater, x 356..372, y 62..69)
r = Room('DB8', 'The Pearl Cistern', 'barrows', 356, 62, 17, 8, indoor=True, secret=True, chests=['shard'], graves=['db4'],
         spawns=[_db_en('db_eel', 8, 3), _db_deco('bones', 14, 6)])
_A = '"'
_db_paint(r, [
    #0         1
    #01234567890123456
    "##########" + _A * 4 + "###",  # 0   <- the well from the Tide Stair
    "#....####" + _A * 7 + "#",      # 1   an air pocket to breathe (top-left)
    "#" + _A * 15 + "#",             # 2
    "#" + _A * 15 + "#",             # 3
    "#" + _A * 15 + "#",             # 4
    "#" + _A * 15 + "#",             # 5
    "#" + _A * 15 + "#",             # 6
    "#################",             # 7
])
r.put(3, 6, 'C').put(11, 6, 'g')
