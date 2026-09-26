# ============================================================ NEO-HALLOW (agent NH) -- the secret otherworld
# A rain-soaked neon megacity built on the fossilised Pale Root, thousands of years later. Disconnected zone
# x 1000..1300, y -50..100: reached ONLY through a glitching crack in reality hidden in the Root Shaft (C6),
# behind a breakable wall 'B' off the shaft's middle catwalk. Return portal + shrine in NH1.
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Tiles (web/src/36_neohallow.js): '1' data abyss (id 66, solid, burns and throws you out / respawns you),
#                                  '2' deletable arena floor (id 67, solid; SAINT-0 deletes and restores it).
# Spawns (web/src/36_neohallow.js): nh_portal, nh_laser, nh_term, nh_door, nh_plat, nh_train, nh_fog, nh_deco,
#                                   enemies nh_drone (flying) / nh_cyborg / nh_turret, bosses enforcer / saint0.
#
#   NH1 Glitch Terminus   1000..1035 x  0..15   arrival rooftop: return portal + Terminus Shrine
#   NH2 Neon Rooftops     1036..1091 x  0..15   laser grids on timers, a security drone, a cyborg, a turret
#   NH3 The Maglev Line   1092..1155 x  0..15   a maglev car shuttles across the data abyss; laser gate on the ride
#   NH4 Server Cathedral  1156..1191 x -14..15  terminals raise hard-light stairs; c_hack alcove; B-closet shard
#   NH5 Enforcer's Plaza  1192..1235 x -14..1   mini-boss: the Enforcer Mech
#   NH6 Null Vestibule    1236..1259 x -14..1   Vestibule Shrine + the plasma katana
#   NH7 The Null Sanctum  1260..1299 x -12..1   main boss: SAINT-0, the Null Saint (deletable floor over the abyss)
SOLID.update('12')
FLYING.add('nh_drone')


def _nh_paint(r, rows):
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            r.g[y][x] = ch
    return r


def _nh_deco(kind, x, y, **kw):
    return dict(t='nh_deco', kind=kind, x=x, y=y, **kw)


# ---------------------------------------------------------------- C6 (the portal's hiding place): a pocket carved into
# the Root Shaft's east rock, behind a breakable wall off the catwalk at row 22 (cols 12-13). Global x 243..248.
_c6 = ROOM('C6')
if all(_c6.g[y][x] == '#' for y in range(17, 24) for x in range(14, 22)) and _c6.g[22][12] == '=':
    _c6.fill(15, 18, 20, 21, '.')              # the pocket (4 rows of headroom)
    _c6.fill(14, 19, 14, 21, 'B')              # cracked rock: three hits open it (the wall above it stays solid)
    _c6.kw.setdefault('spawns', []).append({'t': 'nh_portal', 'x': 18, 'y': 21, 'to': 'NH1', 'tx': 7, 'ty': 12})
else:
    print('neohallow: C6 rock changed; portal pocket skipped')

# ---------------------------------------------------------------- NH1 Glitch Terminus (arrival)
r = Room('NH1', 'Glitch Terminus', 'neohallow', 1000, 0, 36, 16, shrine='Terminus Shrine', items=['emberstone'],
         spawns=[dict(t='nh_portal', x=4, y=12, to='C6', tx=16, ty=21, back=True),
                 _nh_deco('sign', 9, 12, v=0), _nh_deco('antenna', 30, 12), _nh_deco('billboard', 18, 12, v=0),
                 _nh_deco('lamp', 2, 12), _nh_deco('lamp', 16, 12), _nh_deco('vent', 33, 12)])
_nh_paint(r, [
    #0         1         2         3
    #012345678901234567890123456789012345
    "#...................................",  # 0
    "#...................................",  # 1
    "#...................................",  # 2
    "#...................................",  # 3
    "#...................................",  # 4
    "#...................................",  # 5
    "#...................................",  # 6
    "#...................................",  # 7
    "#...................................",  # 8
    "#...................................",  # 9
    "#.....................######........",  # 10  rooftop housing (the emberstone sits on it)
    "#.....................######........",  # 11
    "#.....................######........",  # 12
    "####################################",  # 13
    "####################################",  # 14
    "####################################",  # 15
])
r.put(12, 12, 'S').put(24, 9, 'i')

# ---------------------------------------------------------------- NH2 Neon Rooftops (timed laser grids)
r = Room('NH2', 'Neon Rooftops', 'neohallow', 1036, 0, 56, 16, items=['emberstone'],
         spawns=[dict(t='nh_laser', x=25, y=10, y0=5, y1=10, period=3.4, on=1.1, phase=0.0),
                 dict(t='nh_laser', x=29, y=10, y0=5, y1=10, period=3.4, on=1.1, phase=1.7),
                 dict(t='enemy', type='nh_drone', x=27, y=6, air=True),
                 dict(t='enemy', type='nh_cyborg', x=46, y=12),
                 dict(t='enemy', type='nh_turret', x=53, y=12),
                 _nh_deco('sign', 6, 12, v=1), _nh_deco('lamp', 11, 12), _nh_deco('billboard', 40, 12, v=1),
                 _nh_deco('lamp', 21, 10), _nh_deco('vent', 33, 10), _nh_deco('sign', 49, 12, v=2)])
_nh_paint(r, [
    #0         1         2         3         4         5
    #01234567890123456789012345678901234567890123456789012345
    "........................................................",  # 0
    "........................................................",  # 1
    "........................................................",  # 2
    "........................................................",  # 3
    ".......................#########........................",  # 4   laser gantry (the emitters hang from it)
    "........................................................",  # 5
    "........................................................",  # 6
    "........................................................",  # 7
    "........................................................",  # 8
    "................................................===.....",  # 9   neon awning (emberstone)
    "........................................................",  # 10
    "..................#################.....................",  # 11  rooftop B (2 rows up)
    "..................#################.....................",  # 12
    "##############....#################...##################",  # 13
    "##############1111#################111##################",  # 14  data abyss in the alleys
    "##############1111#################111##################",  # 15
])
r.put(49, 8, 'i')

# ---------------------------------------------------------------- NH3 The Maglev Line (ride the car across the abyss)
r = Room('NH3', 'The Maglev Line', 'neohallow', 1092, 0, 64, 16,
         spawns=[dict(t='nh_item', x=24, y=7, item='sp:pulse_shot'),   # hangs over the lane: jump from the moving car
                 dict(t='nh_train', x=12, x0=12, x1=51, y=11, w=6, wait=2.2, speed=104),
                 dict(t='nh_laser', x=32, y=10, y0=4, y1=10, period=4.2, on=0.9, phase=0.8),
                 dict(t='enemy', type='nh_drone', x=44, y=5, air=True),
                 dict(t='enemy', type='nh_turret', x=60, y=10),
                 _nh_deco('canopy', 5, 12), _nh_deco('canopy', 57, 10), _nh_deco('sign', 2, 12, v=2),
                 _nh_deco('lamp', 10, 10), _nh_deco('lamp', 53, 10), _nh_deco('pylon', 22, 12), _nh_deco('pylon', 42, 12)])
_nh_paint(r, [
    #0         1         2         3         4         5         6
    #0123456789012345678901234567890123456789012345678901234567890123
    "...............................................................#",  # 0
    "...............................................................#",  # 1
    "...............................................................#",  # 2
    "............................#########..........................#",  # 3   power gantry (laser emitter)
    "...............................................................#",  # 4
    "...............................................................#",  # 5
    "...............................................................#",  # 6
    "................................................................",  # 7   -> Server Cathedral
    "................................................................",  # 8
    "................................................................",  # 9
    "................................................................",  # 10
    ".......#####........................................############",  # 11  platform edges at the car's roof height
    ".......#####........................................############",  # 12
    "############1111111111111111111111111111111111111111############",  # 13  the data abyss
    "############1111111111111111111111111111111111111111############",  # 14
    "############1111111111111111111111111111111111111111############",  # 15
])

# ---------------------------------------------------------------- NH4 Server Cathedral (terminals + hard-light)
# Climb (basic jumps only, every step <= 3 rows): floor 25 -> catwalk 22 -> hard-light 19 -> 16 -> {vault balcony 13 | 13}
# -> the exit balcony (row 13, east). The STAIR terminal (ground) raises the hard-light steps; the VAULT terminal (exit
# balcony) opens the energy door of the vault alcove (c_hack); the vault's cracked back wall hides a shard.
r = Room('NH4', 'Server Cathedral', 'neohallow', 1156, -14, 36, 30, indoor=True, items=['shard'], chests=['c_hack'],
         spawns=[dict(t='nh_term', x=4, y=24, links=['a'], label='STAIR'),
                 dict(t='nh_plat', x=13, y=19, w=4, id='a', on=False),
                 dict(t='nh_plat', x=18, y=16, w=3, id='a', on=False),
                 dict(t='nh_plat', x=23, y=13, w=3, id='a', on=False),
                 dict(t='nh_term', x=30, y=12, links=['c'], label='VAULT'),
                 dict(t='nh_door', x=9, y=12, h=4, id='c', open=False),
                 dict(t='nh_laser', x=21, y=24, y0=2, y1=24, period=3.8, on=1.1, phase=0.0),
                 dict(t='enemy', type='nh_cyborg', x=26, y=24),
                 dict(t='enemy', type='nh_turret', x=33, y=12),
                 dict(t='enemy', type='nh_drone', x=16, y=7, air=True),
                 _nh_deco('rack', 8, 24), _nh_deco('rack', 13, 24), _nh_deco('rack', 29, 24), _nh_deco('rack', 33, 24),
                 _nh_deco('lamp', 28, 12), _nh_deco('glyph', 18, 24), _nh_deco('lamp', 12, 12)])
_nh_paint(r, [
    #0         1         2         3
    #012345678901234567890123456789012345
    "####################################",  # 0
    "####################################",  # 1
    "#..................................#",  # 2
    "#..................................#",  # 3
    "#..................................#",  # 4
    "#..................................#",  # 5
    "#..................................#",  # 6
    "#..................................#",  # 7
    "##########.........................#",  # 8   vault ceiling (col 9 = rock over the energy door)
    "#..B................................",  # 9   the vault (door at col 9) / -> Enforcer's Plaza
    "#..B................................",  # 10
    "#..B................................",  # 11
    "#..B................................",  # 12
    "################............########",  # 13  vault floor + balcony (cols 10..15) / exit balcony (28..35)
    "#######.....................########",  # 14
    "#######.....................########",  # 15
    "#######.....................########",  # 16
    "#######.....................########",  # 17
    "#######............................#",  # 18
    "#######............................#",  # 19
    "#######............................#",  # 20
    "...................................#",  # 21  <- Maglev Line
    "........====.......................#",  # 22  catwalk
    "...................................#",  # 23
    "...................................#",  # 24
    "####################################",  # 25
    "####################################",  # 26
    "####################################",  # 27
    "####################################",  # 28
    "####################################",  # 29
])
r.put(6, 12, 'C')                            # c_hack
r.put(1, 12, 'i')                            # shard, in the closet behind the cracked wall

# ---------------------------------------------------------------- NH5 Enforcer's Plaza (mini-boss)
r = Room('NH5', "Enforcer's Plaza", 'neohallow', 1192, -14, 44, 16, boss='enforcer', items=['emberstone'],
         spawns=[dict(t='boss', kind='enforcer', x=30, y=12),
                 dict(t='nh_fog', x=2, y=12, kind='enforcer'), dict(t='nh_fog', x=41, y=12, kind='enforcer', exit=True),
                 _nh_deco('billboard', 14, 12, v=2), _nh_deco('lamp', 8, 12), _nh_deco('lamp', 36, 12),
                 _nh_deco('sign', 24, 12, v=0)])
_nh_paint(r, [
    #0         1         2         3         4
    #01234567890123456789012345678901234567890123
    "###.......................................##",  # 0
    "###.......................................##",  # 1
    "###.......................................##",  # 2
    "###.......................................##",  # 3
    "###.......................................##",  # 4
    "###.......................................##",  # 5
    "###.......................................##",  # 6
    "###.......................................##",  # 7
    "#.........................................##",  # 8
    "............................................",  # 9   <- Server Cathedral / -> Vestibule
    "..........====..............====............",  # 10
    "............................................",  # 11
    "............................................",  # 12
    "############################################",  # 13
    "############################################",  # 14
    "############################################",  # 15
])
r.put(2, 8, '#').put(1, 8, '#')
r.put(40, 12, 'i')

# ---------------------------------------------------------------- NH6 Null Vestibule (shrine + the plasma katana)
r = Room('NH6', 'Null Vestibule', 'neohallow', 1236, -14, 24, 16, indoor=True, shrine='Vestibule Shrine', chests=['w:plasma_katana'],
         spawns=[_nh_deco('glyph', 16, 12), _nh_deco('lamp', 3, 12), _nh_deco('lamp', 21, 12), dict(t='nh_lore', x=13, y=12)])
_nh_paint(r, [
    "########################",  # 0
    "########################",  # 1
    "#......................#",  # 2
    "#......................#",  # 3
    "#......................#",  # 4
    "#......................#",  # 5
    "#......................#",  # 6
    "#......................#",  # 7
    "#......................#",  # 8
    "........................",  # 9
    "........................",  # 10
    "........................",  # 11
    "........................",  # 12
    "########################",  # 13
    "########################",  # 14
    "########################",  # 15
])
r.put(8, 12, 'S').put(19, 12, 'C')

# ---------------------------------------------------------------- NH7 The Null Sanctum (SAINT-0)
r = Room('NH7', 'The Null Sanctum', 'neohallow', 1260, -12, 40, 14, indoor=True, boss='saint0',
         spawns=[dict(t='boss', kind='saint0', x=27, y=10),
                 dict(t='nh_fog', x=2, y=10, kind='saint0')])
_nh_paint(r, [
    #0         1         2         3
    #0123456789012345678901234567890123456789
    "########################################",  # 0
    "#......................................#",  # 1
    "#......................................#",  # 2
    "#......................................#",  # 3
    "#......................................#",  # 4
    "#......................................#",  # 5
    "#......................................#",  # 6
    ".......................................#",  # 7   <- Null Vestibule
    ".......................................#",  # 8
    ".......................................#",  # 9
    ".......................................#",  # 10
    "####222222222222222222222222222222222###",  # 11  deletable floor
    "####111111111111111111111111111111111###",  # 12  the abyss one tile beneath it
    "########################################",  # 13
])
