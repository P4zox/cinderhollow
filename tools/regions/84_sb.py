# ============================================================ EXPANSION 3 · agent SB: Necropolis of Vael + Sunscorched Dunes
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, du_slope from 74_dunes.py).
# Engine: web/src/54_sb.js (props 'xsb', lore pages sb_*, trial charms, puzzle hints, room dressing). Art: art/gen_xsb.py.
#
# NECROPOLIS WING "The Deadward" (zone x -112..149, y 113..260). Enters from the Bone Spire's floor (NV3, a stair-arch
# beside the main route), runs west under the city as a spine, climbs the Catafalque Stair, and loops back into the
# Tolling Streets beside the Yard Gate Shrine (NV4) through a barred door whose bar is lifted from the stair side.
# After the Twin Executioners fall, the sealed door at the stair's summit opens into the Hollow Court (NV6).
#   NV8  The Cemetery Gate      84..131 x 158..171  path     <- door NV3; shaft up to NV13
#   NV13 The Legion Yard        84..131 x 142..157  gauntlet (war drum)
#   NV9  Street of Lanterns     20..83  x 157..172  path     drop grate down to NV11
#   NV10 The Catafalque Stair  -28..19  x 113..172  grand    -> door NV4 (loop), door NV6 (after the Executioners)
#   NV14 Charnel Barracks       20..59  x 143..156  gauntlet (axe rack), off the stair's east ledge
#   NV11 The Bellwalk           20..83  x 173..190  parkour  (bell walkways swap on every toll)
#   NV12 The Dirge             -12..19  x 173..192  puzzle   (ring the bells as the dirge slab shows) -> shortcut up into NV10
#   NV15 The Headsman's Run    -84..-29 x 141..160  trial    (axes + ash veils; Ember Dash) -> c_x3_hood
#   NV16 Ossuary of Kings      -44..-29 x 113..126  secret   (Cinder Slam through the throne landing)
#
# DUNES WING "The Buried Road" (zone x 400..584, y 147..260). Enters from the foot of the Sandfall Shaft (DU4), crosses
# the Sea of Dunes, goes down through the Tomb Entry Hall and loops back into the Hieroglyph Halls beside the Scarab Gate
# Shrine (DU5) through a barred door.
#   DU9  Caravan Road          520..583 x 159..174  path     <- door DU4; crack to DU18; grate down to DU16
#   DU10 The Sea of Dunes      400..519 x 147..174  grand    (sandstorm, quicksand, the buried sun-spire)
#   DU15 The Last Oasis        400..435 x 175..192  vista
#   DU17 The Nameless Tomb     404..419 x 193..206  secret   (Cinder Slam through the oasis dune)
#   DU11 Tomb Entry Hall       436..483 x 175..190  path     -> door DU5 (loop); the painted titles (clue for DU14)
#   DU14 The Hieroglyph Seal   436..467 x 191..210  puzzle
#   DU12 Sinking Sands         484..539 x 175..192  parkour
#   DU13 The Sun Dial          500..539 x 193..216  puzzle   (mirrors carry the sun to the hieroglyph door)
#   DU16 Sandfall Descent      560..583 x 175..238  trial    (Gale Cloak) -> c_x3_scarab
#   DU18 Scarab Cache          540..555 x 175..188  secret   (follow the golden scarab into the crack)


def _xd(kind, x, y, **kw):          # SB decor prop (54_sb.js SPAWNS.xsb)
    return dict(t='xsb', kind=kind, x=x, y=y, **kw)


def _xa(kind, x, y, **kw):          # SB decor that hangs / floats (not grounded)
    return dict(t='xsb', kind=kind, x=x, y=y, air=True, **kw)


def _door(x, y, id, to, toId=None, look='arch', **kw):
    return dict(t='sys', kind='door', x=x, y=y, id=id, to=to, toId=toId or id, look=look, **kw)


def _lore(x, y, page, look='stone', **kw):
    return dict(t='sys', kind='lore', x=x, y=y, page=page, look=look, **kw)


def _en(type, x, y, **kw):
    return dict(t='enemy', type=type, x=x, y=y, **kw)


def _nvd(kind, x, y, **kw):         # the Necropolis' own decor (33_necropolis.js)
    return dict(t='nv_prop', kind=kind, x=x, y=y, **kw)


# ================================================================== anchors (old rooms: door spawns only)
ROOM('NV3').kw['spawns'].append(_door(15, 41, 'xw', 'NV8', look='arch'))           # the Bone Spire's foot: down to the Deadward
ROOM('NV4').kw['spawns'].append(_door(14, 16, 'xl', 'NV10', look='arch'))          # beside the Yard Gate Shrine (barred from the stair side)
ROOM('NV6').kw['spawns'].append(_door(9, 14, 'xt', 'NV10', look='arch'))           # the Hollow Court: down the Catafalque Stair
ROOM('DU4').kw['spawns'].append(_door(17, 35, 'xr', 'DU9', look='arch'))           # the Sandfall Shaft's foot: the Buried Road
ROOM('DU5').kw['spawns'].append(_door(15, 11, 'xh', 'DU11', look='arch'))          # beside the Scarab Gate Shrine (barred from the hall side)

# ================================================================== NECROPOLIS
# ---------------------------------------------------------------- NV8 The Cemetery Gate (path)
r = Room('NV8', 'The Cemetery Gate', 'necropolis', 84, 158, 48, 14, indoor=True, needs=['talon'], x3=True,
         xsb_paint=[['fence', 6, 10], ['fence', 39, 10], ['gateleaves', 23.5, 10]],
         spawns=[_door(44, 10, 'xw', 'NV3'), _lore(40, 10, 'sb_1'),
                 _en('nv_hound', 26, 10), _en('nv_noble', 11, 10), _en('nv_ringer', 23, 4),
                 _xd('lamppost', 36, 10), _xd('lamppost', 7, 10), _xd('headstone', 32, 10), _xd('headstone', 15, 10, v=1),
                 _xd('mourner', 47 - 13, 4, face=-1), _xd('tombchest', 20, 10), _xa('cage', 41, 2), _xa('cage', 9, 2),
                 _nvd('candles', 29, 10), _nvd('skulls', 4, 10)])
r.walls().open('W', 7, 10)
r.fill(0, 0, 47, 1).fill(2, 0, 5, 1, '.')                  # the shaft up to the Legion Yard
r.fill(0, 11, 47, 13)
for _y in (8, 5, 2):
    r.fill(2, _y, 5, _y, '=')
r.fill(17, 5, 30, 6)                                        # the gatehouse: its wall-walk is a lintel over the road
r.fill(17, 2, 17, 4).fill(30, 2, 30, 3)                     # merlons (the east one leaves a gap to hop through)
r.fill(12, 8, 14, 8, '=').fill(33, 8, 35, 8, '=')           # steps up to the wall-walk
r.fill(44, 2, 46, 4)                                        # a heavy lintel over the Bone Spire stair
for _x, _y, _ch in [(20, 10, 'b'), (38, 10, 'k'), (3, 10, 'k'), (24, 2, 'x'), (10, 2, 'x'), (37, 2, 'x')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV13 The Legion Yard (gauntlet)
r = Room('NV13', 'The Legion Yard', 'necropolis', 84, 142, 48, 16, indoor=True, needs=['talon'], x3=True, gauntlet=True,
         xsb_paint=[['fence', 15, 12], ['fence', 38, 12]],
         spawns=[dict(t='kit', kind='gate', x=7, y=12, id='gY', open=True),
                 dict(t='sys', kind='gauntlet', x=27, y=12, id='legion', look='drum', name='The Legion Yard', gates=['gY'],
                      waves=[[_en('nv_hound', 14, 12), _en('hollow_soldier', 20, 12), _en('hollow_soldier', 38, 12), _en('nv_hound', 42, 12)],
                             [_en('nv_noble', 16, 12), _en('hollow_archer', 13, 8), _en('hollow_archer', 40, 8), _en('nv_noble', 36, 12)],
                             [_en('nv_ringer', 22, 12), _en('shield_warden', 34, 12), _en('nv_hound', 12, 12), _en('nv_hound', 44, 12)],
                             [_en('grave_knight', 30, 12), _en('nv_noble', 18, 12)]],
                      reward=['emberstone']),
                 _xd('rack', 45, 12), _xd('rack', 10, 12, face=-1), _xd('dummy', 40, 12), _xd('dummy', 17, 12),
                 _nvd('banner', 16, 2), _nvd('banner', 27, 2), _nvd('banner', 38, 2), _nvd('brazier', 22, 12), _nvd('brazier', 33, 12),
                 _nvd('statue', 3, 12)])
r.walls()
r.fill(0, 0, 47, 1)
r.fill(0, 13, 47, 15).fill(2, 13, 5, 15, '.')               # the shaft down to the Cemetery Gate
r.fill(2, 15, 5, 15, '=').fill(2, 13, 5, 13, '=')
r.fill(11, 9, 16, 9, '=').fill(37, 9, 42, 9, '=')           # the archers' galleries
r.fill(7, 2, 7, 3)                                          # the gate's yoke under the ceiling (it reaches rock)
for _x, _y, _ch in [(25, 12, 'b'), (46, 12, 'k'), (30, 2, 'x'), (20, 2, 'x')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV9 Street of Lanterns (path)
r = Room('NV9', 'Street of Lanterns', 'necropolis', 20, 157, 64, 16, indoor=True, needs=['talon'], x3=True,
         xsb_paint=[['tombwall', 19, 11], ['tombwall', 38, 11], ['tombwall', 56, 11]],
         spawns=[_en('nv_noble', 40, 11), _en('nv_ringer', 27, 7), _en('nv_hound', 16, 11), _en('gloom_wisp', 50, 5, air=True),
                 *[_xd('lamppost', _x, 11) for _x in (6, 21, 35, 49, 61)],
                 _xd('tombchest', 45, 8), _xd('headstone', 31, 11), _xd('headstone', 3, 11, v=1), _xd('mourner', 12, 8),
                 _xd('tombchest', 27, 7, v=1), _nvd('candles', 18, 11), _nvd('skulls', 55, 11), _nvd('coffin', 38, 11),
                 _xa('dropmark', 57, 11)])
r.walls().open('E', 8, 11).open('W', 8, 11)
r.fill(0, 0, 63, 1)
r.fill(0, 12, 63, 15)
r.fill(56, 12, 58, 15, '.').fill(56, 12, 58, 12, '=').fill(56, 15, 58, 15, '=')    # a grate over the Bellwalk
r.fill(9, 9, 14, 11)                                        # mausoleum
r.fill(24, 8, 30, 11)                                       # the great mausoleum (a ringer keeps its roof)
r.fill(15, 6, 23, 6, '=')                                   # a lantern-wire walk between the roofs
r.fill(31, 6, 35, 6, '=').fill(43, 9, 47, 11)               # and on east over the street
r.fill(36, 4, 40, 4, '=')
r.put(38, 3, 'i')                                           # gold on the highest cornice
r.kw['items'] = ['gold']
for _x, _y, _ch in [(8, 2, 'x'), (32, 2, 'x'), (52, 2, 'x'), (20, 11, 'b'), (52, 11, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV10 The Catafalque Stair (grand)
# Three ways up: the east ledges (main), the west chimney (talon), the bell walkways across the middle (timed by the
# great bell hung under the throne landing). The summit: the catafalque of the last king (the landmark), a sealed door to
# the Hollow Court, and a cracked slab over the Ossuary of Kings.
r = Room('NV10', 'The Catafalque Stair', 'necropolis', -28, 113, 48, 60, indoor=True, needs=['talon'], x3=True, grand=True,
         bells=dict(every=4.2, warn=1.3),
         xsb_paint=[['catafalque', 18, 7], ['tombwall', 6, 55], ['tombwall', 40, 19], ['tombwall', 24, 44]],
         reach_open=[(x, y) for x in (1, 2, 3) for y in (8, 9)],
         spawns=[_door(44, 7, 'xt', 'NV6'), _door(44, 28, 'xl', 'NV4'),
                 dict(t='sys', kind='passage', x=38, y=7, w=2, h=3, id='throne', cond={'flag': 'boss:executioners'}, drift='nvghost',
                      light='150,200,255'),
                 dict(t='kit', kind='gate', x=40, y=28, id='bar', persist=True),
                 dict(t='kit', kind='lever', x=37, y=28, id='lbar', targets=['bar'], once=True, msg='The bar lifts. The Tolling Streets lie beyond.'),
                 dict(t='nv_bell', x=20, y=10, big=1),
                 _lore(10, 7, 'sb_2'),
                 _en('nv_hound', 8, 55), _en('nv_noble', 24, 22), _en('nv_ringer', 35, 16), _en('gloom_wisp', 25, 40, air=True),
                 _en('nv_noble', 30, 7), _en('nv_hound', 42, 40),
                 _xd('lamppost', 6, 40), _xd('lamppost', 44, 40), _xd('lamppost', 8, 25), _xd('lamppost', 33, 7), _xd('lamppost', 3, 7),
                 _xd('tombchest', 30, 49, v=1), _xd('tombchest', 37, 52), _xd('tombchest', 25, 22), _xd('tombchest', 36, 16, v=1),
                 _xd('mourner', 12, 25), _xd('mourner', 26, 7, face=-1), _xd('headstone', 13, 55), _xd('headstone', 42, 55, v=1),
                 _nvd('brazier', 6, 7), _nvd('candles', 28, 7), _nvd('skulls', 11, 40), _nvd('candles', 39, 28), _nvd('brazier', 26, 55),
                 _xa('cage', 32, 1), _xa('cage', 14, 13), _xa('cage', 45, 31)])
r.walls().open('E', 52, 55).open('W', 37, 40).open('E', 37, 40).open('W', 10, 12)
r.fill(0, 56, 47, 59)
r.fill(17, 57, 20, 59, '.').fill(17, 56, 20, 56, '=').fill(17, 59, 20, 59, '=')     # grate down to the Dirge's well
# the summit: the throne landing, its one-way gap, the Ossuary slab and pocket, the sealed door's niche
r.fill(0, 8, 27, 9).fill(36, 8, 47, 9).fill(28, 8, 35, 8, '=')
r.fill(1, 8, 3, 9, 'Y')
r.fill(1, 10, 3, 12, '.').fill(4, 10, 4, 12).fill(0, 13, 4, 13)
r.fill(36, 1, 47, 3).fill(38, 4, 39, 4)
# the lower flights (east entrance -> west)
r.fill(34, 53, 39, 55).fill(28, 50, 33, 55)
r.fill(22, 47, 26, 47, '=').fill(14, 44, 18, 44, '=')
r.fill(1, 41, 10, 42)                                        # L1: the west landing (the Headsman's Run lies beyond)
# east ledges -> the Barracks ledge -> the barred door's ledge
r.fill(36, 47, 39, 47, '=').fill(31, 44, 34, 44, '=')
r.fill(38, 41, 46, 41)                                       # the Barracks ledge
r.fill(32, 38, 35, 38, '=').fill(26, 35, 29, 35, '=').fill(30, 32, 33, 32, '=')
r.fill(36, 29, 46, 29)                                       # the barred door's ledge
r.fill(38, 20, 47, 23)                                       # rock over the door's alcove (the bar reaches it)
# the west chimney (talon) and L2
r.fill(4, 28, 5, 38).fill(4, 26, 12, 27)
r.fill(1, 18, 3, 19)
# bell walkways across the middle (A '{' / B '}': the great bell swaps them)
r.fill(12, 38, 15, 38, '{').fill(16, 35, 19, 35, '}').fill(12, 32, 15, 32, '{').fill(16, 29, 19, 29, '}')
# the upper flights (both routes meet on the tomb tier)
r.fill(30, 26, 33, 26, '=').fill(22, 23, 27, 24).fill(15, 23, 18, 23, '=')
r.fill(29, 20, 32, 20, '=').fill(33, 17, 38, 18)
r.fill(27, 14, 30, 14, '=').fill(31, 11, 34, 11, '=')
for _x, _y, _ch in [(20, 1, 'x'), (9, 1, 'x'), (30, 10, 'x'), (6, 10, 'x'), (44, 24, 'x'), (13, 45, 'x'), (24, 45, 'x'), (3, 55, 'b'),
                    (22, 55, 'k'), (45, 55, 'b'), (9, 40, 'b'), (7, 25, 'k'), (46, 40, 'k'), (44, 51, 'x')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV14 Charnel Barracks (gauntlet)
r = Room('NV14', 'Charnel Barracks', 'necropolis', 20, 143, 40, 14, indoor=True, needs=['talon'], x3=True, gauntlet=True,
         spawns=[dict(t='kit', kind='gate', x=3, y=10, id='gB', open=True),
                 dict(t='sys', kind='gauntlet', x=31, y=10, id='charnel', look='rack', name='Charnel Barracks', gates=['gB'],
                      waves=[[_en('nv_noble', 12, 10), _en('nv_noble', 24, 10), _en('hollow_soldier', 36, 10)],
                             [_en('nv_hound', 8, 10), _en('nv_hound', 37, 10), _en('nv_ringer', 20, 6), _en('hollow_archer', 12, 6)],
                             [_en('hollow_soldier', 10, 10), _en('shield_warden', 26, 10), _en('nv_ringer', 36, 10), _en('nv_noble', 18, 10)],
                             [_en('grave_knight', 20, 10), _en('nv_ringer', 34, 10)]],
                      reward=['emberstone']),
                 _lore(36, 10, 'sb_3', look='corpse', face=-1),
                 _xd('rack', 8, 10), _xd('rack', 16, 10, face=-1), _xd('bunk', 13, 6), _xd('bunk', 25, 6), _xd('drum', 22, 10),
                 _nvd('block', 27, 10), _nvd('brazier', 5, 10), _nvd('brazier', 38, 10), _nvd('banner', 20, 2), _xa('cage', 33, 2)])
r.walls().open('W', 7, 10)
r.fill(0, 0, 39, 1).fill(0, 11, 39, 13)
r.fill(10, 7, 15, 7, '=').fill(22, 7, 27, 7, '=')           # the bunk tiers
r.fill(3, 2, 3, 2)
for _x, _y, _ch in [(19, 10, 'b'), (7, 2, 'x'), (30, 2, 'x'), (34, 10, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV11 The Bellwalk (parkour)
r = Room('NV11', 'The Bellwalk', 'necropolis', 20, 173, 64, 18, indoor=True, needs=['talon'], x3=True, parkour=True,
         bells=dict(every=3.2, warn=1.1), items=['gold'], xsb_paint=[['tombwall', 4, 13], ['tombwall', 57, 13]],
         spawns=[dict(t='nv_bell', x=34, y=2, big=1), dict(t='nv_bell', x=13, y=2),
                 _xd('lamppost', 3, 13), _xd('lamppost', 52, 13), _xd('headstone', 60, 13), _nvd('candles', 55, 13),
                 _nvd('skulls', 5, 13), _xa('cage', 25, 2), _xa('cage', 45, 2)])
r.walls().open('W', 10, 13)
r.fill(0, 0, 63, 1).fill(56, 0, 58, 1, '.')
for _y in (2, 5, 8, 11):
    r.fill(56, _y, 58, _y, '=')
r.fill(0, 14, 63, 17)
r.fill(8, 14, 47, 16, '.').fill(8, 16, 47, 16, '^')         # the pit: bone spikes, a fall below the walkways
r.fill(42, 14, 47, 14, '{').fill(36, 12, 41, 12, '}')       # S1  A -> B
r.fill(33, 11, 35, 16)                                      # P1
r.fill(27, 11, 32, 11, '{').fill(21, 13, 26, 13, '}')       # S2  A -> B
r.fill(18, 12, 20, 16)                                      # P2
r.fill(13, 10, 17, 10, '}').fill(8, 12, 12, 12, '{')        # S3  B -> A
r.fill(29, 7, 31, 7, '}').fill(24, 5, 27, 6)                # up from P1 to the gold on the old bell loft
r.put(25, 4, 'i')
for _x, _y, _ch in [(34, 10, 'b'), (19, 11, 'k'), (60, 2, 'x'), (6, 2, 'x'), (50, 13, 'b')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV12 The Dirge (puzzle)
# Five bells hang at five heights; the lower a bell hangs, the lower it sounds. The dirge slab by the door shows the
# melody as marks on a stave. Ring it and the well gate (up into the Catafalque Stair) and the crypt gate open.
_DB = [('b1', 9, 7, 4), ('b2', 13, 9, 0), ('b3', 17, 5, 7), ('b4', 21, 8, 2), ('b5', 25, 6, 5)]     # id, col, row, note
r = Room('NV12', 'The Dirge', 'necropolis', -12, 173, 32, 20, indoor=True, xsb_hall=True, needs=['talon'], x3=True, puzzle=True, chests=['shard'],
         xsb_paint=[['dirgeslab', 28, 8]],
         spawns=[*[dict(t='kit', kind='bell', x=_x, y=_y, id=_i, group='dirge', note=_n) for _i, _x, _y, _n in _DB],
                 dict(t='kit', kind='seq', x=15, y=12, id='dirge', group='dirge', order=['b2', 'b1', 'b4', 'b3', 'b5', 'b2'],
                      targets=['gw', 'gc'], msg='The dirge is sung. Stone grinds somewhere below.'),
                 dict(t='kit', kind='gate', x=5, y=13, id='gw', persist=True),
                 dict(t='kit', kind='gate', x=20, y=18, id='gc', persist=True),
                 _lore(25, 13, 'sb_4', look='tablet'),
                 _nvd('candles', 29, 13), _nvd('brazier', 7, 13), _nvd('coffin', 12, 18), _xd('mourner', 16, 13, face=-1),
                 _nvd('skulls', 15, 18)])
r.walls().open('E', 10, 13)
r.fill(0, 0, 31, 1).fill(1, 0, 4, 1, '.')
for _y in (2, 5, 8, 11):
    r.fill(1, _y, 4, _y, '=')
r.fill(0, 14, 31, 19)
r.fill(8, 15, 23, 18, '.')                                  # the crypt under the hall
r.fill(22, 14, 23, 14, '.').fill(21, 16, 23, 16, '=')       # its stair-hole
r.fill(8, 11, 10, 11, '=').fill(16, 11, 18, 11, '=').fill(24, 11, 26, 11, '=')
r.put(11, 18, 'C')
for _x, _y, _ch in [(3, 13, 'k'), (30, 13, 'k'), (9, 18, 'b'), (18, 18, 'b')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV15 The Headsman's Run (trial: axes under a low roof, crumbling ledges, an ash veil, a chimney)
# The axes hang low from the execution roof: jump each blade as it sweeps under you, or dash through it. Between the two
# corridor axes there is one hand's breadth of safety. Then the crumbling ledges (a third axe over the middle one), the
# ash veil (Ember Dash), and a wall-jump chimney up to the reliquary.
r = Room('NV15', "The Headsman's Run", 'necropolis', -84, 141, 56, 20, indoor=True, needs=['talon', 'emberdash'], x3=True, trial=True,
         spawns=[dict(t='sys', kind='trial', x=51, y=12, id='run', par=8, reward='c_x3_hood', name="The Headsman's Run"),
                 dict(t='sys', kind='trial_goal', x=4, y=3, trial='run'),
                 dict(t='kit', kind='pendulum', x=45, y=9, len=3, period=1.6, amp=70, phase=0.0),
                 dict(t='kit', kind='pendulum', x=38, y=9, len=3, period=1.6, amp=70, phase=0.5),
                 dict(t='kit', kind='pendulum', x=29, y=9, len=3, period=1.4, amp=70, phase=0.25),
                 *[dict(t='kit', kind='crumble', x=_x, y=13, w=2, delay=0.35, respawn=2.0) for _x in (32, 28, 24)],
                 _xd('axestump', 53, 12), _nvd('block', 48, 12), _nvd('candles', 19, 12), _xd('kingskull', 7, 3, v=1),
                 _xa('cage', 16, 1)])
r.walls().open('E', 9, 12)
r.fill(0, 0, 55, 0).fill(22, 0, 55, 8)                     # the execution roof
r.fill(35, 13, 55, 19)                                      # the start platform and the axe walk
r.fill(23, 14, 34, 19).fill(23, 18, 34, 18, '^').fill(23, 14, 34, 17, '.')   # the pit under the crumbling ledges
r.fill(18, 13, 23, 19)                                      # the veil landing
r.fill(22, 9, 22, 12, '%')                                  # an ash veil: only an Ember Dash passes
r.fill(12, 4, 12, 19).fill(17, 1, 17, 8)                    # the chimney walls
r.fill(13, 18, 17, 18, '^').fill(13, 19, 17, 19)            # spikes at its foot
r.fill(1, 4, 11, 19)                                        # the upper ledge (the goal)
r.fill(3, 1, 7, 1, 'v')
for _x, _y, _ch in [(50, 12, 'b'), (10, 3, 'k'), (41, 12, 'b')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- NV16 Ossuary of Kings (secret)
r = Room('NV16', 'Ossuary of Kings', 'necropolis', -44, 113, 16, 14, indoor=True, xsb_hall=True, needs=['talon', 'slam'], x3=True, secret=True,
         chests=['seed'],
         spawns=[_lore(9, 12, 'sb_5', look='tablet'), _xd('kingskull', 5, 12), _xd('kingskull', 12, 12, v=1),
                 _nvd('candles', 3, 12), _nvd('candles', 11, 12), _xa('cage', 8, 2)])
r.walls().open('E', 10, 12)
r.fill(0, 0, 15, 1).fill(0, 13, 15, 13)
r.fill(1, 5, 3, 5, '=').fill(12, 5, 14, 5, '=')
r.put(7, 12, 'C')
for _x, _y, _ch in [(4, 4, 'b'), (13, 4, 'b'), (14, 12, 'k'), (2, 12, 'k'), (8, 2, 'x')]:
    r.put(_x, _y, _ch)

# ================================================================== SUNSCORCHED DUNES
def _rungs(r, x0, x1, rows):
    for _y in rows:
        r.fill(x0, _y, x1, _y, '=')
    return r


# ---------------------------------------------------------------- DU9 Caravan Road (path)
r = Room('DU9', 'Caravan Road', 'dunes', 520, 159, 64, 16, indoor=True, needs=['talon'], x3=True,
         xsb_paint=[['wagon', 38, 11], ['wagon2', 15, 8], ['camelbones', 55, 11]],
         spawns=[_door(58, 11, 'xr', 'DU4'), _lore(50, 11, 'sb_6'),
                 _en('du_scarab', 36, 9), _en('du_scarab', 40, 9), _en('du_scarab', 15, 8), _en('du_priest', 4, 11),
                 dict(t='xsb_scarab', x=31, y=11, crack=[28, 29]),
                 _xd('jars', 33, 11), _xd('jars', 1, 11, v=1), _xd('crates', 45, 8), _xd('obelisk', 61, 11), _xd('palmdead', 24, 11),
                 _xa('dropmark', 45, 11), _xd('banner_du', 27, 11)])
r.walls().open('W', 8, 11)
r.fill(0, 0, 63, 1).fill(0, 12, 63, 15)
du_slope(r, 6, 12, 13, 9)
r.fill(13, 9, 18, 15)
du_slope(r, 19, 9, 26, 12)
r.fill(28, 12, 29, 15, '.').fill(28, 14, 29, 14, '=')        # the crack (the golden scarab's hole) down to the Scarab Cache
r.fill(35, 10, 42, 10, '=')                                  # the great wagon's bed (planks you can stand on)
r.fill(44, 9, 46, 9, '=')                                    # a wagon roof
r.fill(43, 12, 48, 15, '.').fill(43, 12, 48, 12, '=').fill(43, 15, 48, 15, '=')    # grate over the Sandfall Descent
for _x, _y, _ch in [(8, 2, 'x'), (27, 2, 'x'), (50, 2, 'x'), (32, 11, 'b'), (52, 11, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU18 Scarab Cache (secret)
r = Room('DU18', 'Scarab Cache', 'dunes', 540, 175, 16, 14, indoor=True, xsb_hall=True, needs=['talon'], x3=True, secret=True,
         chests=['emberstone'], items=['gold'],
         spawns=[_xd('scarabidol', 12, 11), _xd('hoard', 5, 11), _xd('jars', 2, 11), _en('du_scarab', 10, 11)])
r.walls().open('N', 8, 9)
r.fill(0, 0, 15, 1).fill(8, 0, 9, 1, '.').fill(0, 12, 15, 13)
_rungs(r, 8, 9, [0]).fill(7, 3, 10, 3, '=').fill(6, 6, 9, 6, '=').fill(8, 9, 11, 9, '=')
r.put(3, 11, 'C').put(14, 11, 'i')
for _x, _y, _ch in [(1, 11, 'k'), (13, 2, 'x')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU16 Sandfall Descent (trial: glide down a spiked sandfall shaft)
r = Room('DU16', 'Sandfall Descent', 'dunes', 560, 175, 24, 64, indoor=True, needs=['talon', 'gale'], x3=True, trial=True,
         spawns=[dict(t='sys', kind='trial', x=5, y=3, id='fall', reward='c_x3_scarab', name='The Sandfall Descent', par=27),
                 dict(t='sys', kind='trial_goal', x=15, y=60, trial='fall'),
                 dict(t='kit', kind='wind', x=20, y=1, w=3, h=60, vy=-340),
                 *[{'t': 'du_sandfall', 'x': _x, 'y': _y0, 'y1': _y1, 'air': True, 'thin': _t} for _x, _y0, _y1, _t in
                   [(8, 11, 16, False), (13, 25, 30, True), (12, 39, 44, False), (6, 46, 51, True)]],
                 _xd('jars', 2, 3), _xa('sunshaft', 12, 1), _xa('dropmark', 13, 3)])
r.walls().open('N', 3, 8)
r.fill(0, 0, 23, 0).fill(3, 0, 8, 0, '.')
r.fill(1, 4, 8, 5)                                           # the sigil's ledge
r.fill(9, 4, 17, 4, '=')                                     # a thin bridge over the fall: drop through it to begin; the updraft brings you back to it
r.fill(4, 1, 7, 1, '=')                                      # a step up to the grate
r.fill(18, 4, 19, 56)                                        # the wall between the fall and the updraft
for _y, _g0 in [(10, 13), (17, 3), (24, 10), (31, 15), (38, 6), (45, 1), (52, 9)]:    # spiked shelves, each with a 3-wide slot
    r.fill(1, _y, 17, _y).fill(1, _y - 1, 17, _y - 1, '^').fill(_g0, _y - 1, _g0 + 2, _y, '.')
r.fill(1, 61, 23, 63).fill(1, 60, 12, 60, '^')              # a floor of sun-bleached spikes; the landing pad lies east
r.fill(13, 60, 17, 60, '.')

# ---------------------------------------------------------------- DU10 The Sea of Dunes (grand)
# Low road: over the dunes, through two quicksand basins (sinking stones) — the sandstorm shoves you about.
# High road: the broken colonnade of the sun-road, lintel to lintel (talon up the first column).
# The landmark: the buried sun-spire on the plateau, its gilded disc still burning.
r = Room('DU10', 'The Sea of Dunes', 'dunes', 400, 147, 120, 28, indoor=True, needs=['talon'], x3=True, grand=True, items=['gold'],
         xsb_paint=[['sunspire', 63, 17], ['wagon2', 115, 23], ['ruinarch', 45.5, 22], ['colossushand', 9, 21]],
         spawns=[{'t': 'du_storm', 'x': 2, 'y': 21, 'air': True, 'dir': 1},
                 _lore(60, 17, 'sb_10'),
                 _en('du_scarab', 9, 21), _en('du_scarab', 94, 22), _en('du_jackal', 66, 17), _en('du_priest', 111, 23),
                 _en('du_scarab', 49, 22),
                 *[dict(t='kit', kind='sinker', x=_x, y=23, w=2, depth=2) for _x in (36, 39)],
                 *[dict(t='kit', kind='sinker', x=_x, y=23, w=2, depth=3, rate=0.9) for _x in (80, 84)],
                 _xd('palm', 2, 21), _xd('obelisk', 42, 22), _xd('jars', 67, 17), _xd('palmdead', 99, 20), _xd('obelisk', 105, 18),
                 _xa('dropmark', 5, 21), _xa('dropmark', 45, 22), _xa('dropmark', 91, 22), _xd('banner_du', 103, 18)])
r.walls().open('E', 20, 23)
r.fill(0, 0, 119, 1).fill(0, 25, 119, 27)
r.fill(0, 22, 11, 24)                                        # the west flats (the chute to the oasis)
du_slope(r, 12, 22, 20, 17)
r.fill(20, 17, 25, 24)
du_slope(r, 26, 17, 34, 23)
r.fill(34, 23, 49, 24)
r.fill(36, 23, 41, 24, '-')                                  # quicksand basin (shallow: jump out)
du_slope(r, 50, 23, 58, 18)
r.fill(58, 18, 68, 24)                                       # the sun-spire's plateau
du_slope(r, 69, 18, 78, 23)
r.fill(78, 23, 95, 24)
r.fill(79, 23, 88, 25, '-')                                  # the deep basin
du_slope(r, 96, 23, 103, 19)
r.fill(103, 19, 107, 24)
du_slope(r, 108, 19, 113, 24)
r.fill(113, 24, 119, 24)
# holes down (each with a slab to climb back)
r.fill(4, 22, 7, 27, '.').fill(4, 22, 7, 22, '=').fill(4, 25, 7, 25, '=').fill(4, 27, 7, 27, '=')        # -> the Last Oasis
r.fill(44, 23, 47, 27, '.').fill(44, 23, 47, 23, '=').fill(44, 26, 47, 26, '=')  # -> the Tomb Entry Hall
r.fill(90, 23, 93, 27, '.').fill(90, 23, 93, 23, '=').fill(90, 26, 93, 26, '=')  # -> the Sinking Sands
# the colonnade (high road)
r.fill(27, 11, 28, 16)                                       # first column, rising from the crest's shoulder
r.fill(22, 14, 25, 14, '=')
r.fill(29, 11, 36, 11, '=').fill(40, 10, 46, 10, '=')
r.fill(52, 9, 53, 17).fill(54, 9, 59, 9, '=')               # the second column over the plateau
r.fill(64, 10, 70, 10, '=').fill(74, 10, 75, 22).fill(76, 11, 82, 11, '=')
r.fill(86, 10, 92, 10, '=').fill(96, 9, 97, 18)             # the last column; its capital holds a sun-gilded purse
r.put(96, 8, 'i')
r.fill(0, 2, 5, 3).fill(30, 2, 33, 4).fill(60, 2, 70, 3).fill(104, 2, 110, 5)   # rock hanging from the cavern roof
for _x, _y, _ch in [(16, 2, 'x'), (48, 2, 'x'), (86, 2, 'x'), (1, 21, 'b'), (62, 17, 'k'), (116, 23, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU15 The Last Oasis (vista)
r = Room('DU15', 'The Last Oasis', 'dunes', 400, 175, 36, 18, indoor=True, needs=['talon'], x3=True, vista=True,
         xsb_sky='sunset', reach_open=[(x, y) for x in (9, 10, 11) for y in (13, 14)],
         spawns=[dict(t='sys', kind='bench', x=31, y=12, id='bench', view=[18, 8], lore='sb_7'),
                 dict(t='xsb_pool', x=16, y=13, w=12, air=True),
                 _xd('palm', 14, 12), _xd('palm', 29, 12, v=1), _xd('palm', 3, 12, v=2), _xd('reeds', 16, 12), _xd('reeds', 27, 12, v=1),
                 _xd('reeds', 21, 12, v=2), _xd('jars', 34, 12), _xd('ruincol', 25, 12), _xd('ruincol', 7, 12, v=1)])
r.walls().open('N', 4, 7)
r.fill(0, 0, 35, 0).fill(4, 0, 7, 0, '.')
_rungs(r, 4, 7, [1, 4, 7, 10])
r.fill(0, 13, 35, 17)
r.fill(16, 13, 27, 13, '.')                                  # the pool basin (still water, knee-deep)
r.fill(9, 13, 11, 14, 'Y').fill(9, 15, 11, 17, '.').fill(9, 16, 11, 16, '=')    # under the dune mound: the Nameless Tomb
r.fill(0, 11, 2, 12)                                         # the west bank
for _x, _y, _ch in [(34, 12, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU17 The Nameless Tomb (secret)
r = Room('DU17', 'The Nameless Tomb', 'dunes', 404, 193, 16, 14, indoor=True, xsb_hall=True, needs=['talon', 'slam'], x3=True, secret=True,
         chests=['seed'],
         spawns=[_lore(11, 11, 'sb_9', look='tablet'), _xd('sarcophagus', 13, 11), _xd('jars', 2, 11), _xd('jars', 9, 11, v=1)])
r.walls().open('N', 5, 7)
r.fill(0, 0, 15, 1).fill(5, 0, 7, 1, '.').fill(0, 12, 15, 13)
_rungs(r, 5, 7, [0, 3, 6, 9])
r.put(3, 11, 'C')
for _x, _y, _ch in [(1, 11, 'k'), (14, 11, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU11 Tomb Entry Hall (path)
# The painted hall: four cartouches spell the Pharaoh's titles in order (the Hieroglyph Seal below asks for them).
r = Room('DU11', 'Tomb Entry Hall', 'dunes', 436, 175, 48, 16, indoor=True, xsb_hall=True, needs=['talon'], x3=True,
         xsb_paint=[['titles', 34, 8]],
         spawns=[_door(3, 11, 'xh', 'DU5'),
                 dict(t='kit', kind='gate', x=6, y=11, id='bar', persist=True),
                 dict(t='kit', kind='lever', x=13, y=11, id='lbar', targets=['bar'], once=True, msg='The bar lifts. The Hieroglyph Halls lie beyond.'),
                 _en('du_priest', 29, 11), _en('du_jackal', 41, 11), _en('du_scarab', 17, 11),
                 _xd('sarcophagus', 25, 11, v=1), _xd('sarcophagus', 44, 11), _xd('jars', 16, 11), _xd('brazier_du', 27, 11),
                 _xd('brazier_du', 42, 11), _xd('statue_du', 19, 11)])
r.walls().open('E', 8, 11)
r.fill(0, 0, 47, 1).fill(8, 0, 11, 1, '.').fill(0, 12, 47, 15)
_rungs(r, 8, 11, [0, 3, 6, 9])
r.fill(6, 2, 6, 2)
r.fill(20, 12, 22, 15, '.').fill(20, 12, 22, 12, '=').fill(20, 15, 22, 15, '=')   # the stair down to the Seal
for _x, _y, _ch in [(15, 2, 'x'), (39, 2, 'x'), (33, 11, 'k'), (46, 11, 'b')]:
    r.put(_x, _y, _ch)
r.kw['spawns'].append(_xa('dropmark', 21, 11))

# ---------------------------------------------------------------- DU14 The Hieroglyph Seal (puzzle)
# Six title-glyphs on the walls; touch the four the painted hall names, in its order, and the seal rolls aside.
_GL = [('g1', 12, 13, 5), ('g2', 16, 11, 1), ('g3', 25, 13, 2), ('g4', 28, 10, 7), ('g5', 13, 8, 3), ('g6', 26, 6, 0)]   # id, col, row, sym
r = Room('DU14', 'The Hieroglyph Seal', 'dunes', 436, 191, 32, 20, indoor=True, xsb_hall=True, needs=['talon'], x3=True, puzzle=True, chests=['shard'],
         xsb_paint=[['sealdoor', 9, 16]],
         spawns=[*[dict(t='kit', kind='glyph', x=_x, y=_y, id=_i, group='titles', sym=_s, note=_n) for _n, (_i, _x, _y, _s) in enumerate(_GL)],
                 dict(t='kit', kind='seq', x=18, y=15, id='titles', group='titles', order=['g3', 'g1', 'g6', 'g4'], targets=['seal'],
                      msg='The seal knows its king. It rolls aside.'),
                 dict(t='kit', kind='gate', x=9, y=16, id='seal', persist=True),
                 _lore(6, 16, 'sb_8', look='tablet'),
                 _xd('brazier_du', 30, 16), _xd('brazier_du', 11, 16), _xd('jars', 3, 16), _xd('statue_du', 23, 16, face=-1)])
r.walls().open('N', 20, 22)
r.fill(0, 0, 31, 1).fill(20, 0, 22, 1, '.').fill(0, 17, 31, 19)
_rungs(r, 20, 22, [2, 5, 8, 11, 14])
r.fill(14, 12, 17, 12, '=').fill(25, 11, 29, 11, '=').fill(12, 9, 15, 9, '=').fill(24, 7, 28, 7, '=')
r.put(4, 16, 'C')
for _x, _y, _ch in [(2, 16, 'k'), (29, 16, 'k')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU12 Sinking Sands (parkour)
r = Room('DU12', 'Sinking Sands', 'dunes', 484, 175, 56, 18, indoor=True, needs=['talon'], x3=True, parkour=True, du_abyss=True,
         items=['gold'],
         spawns=[*[dict(t='kit', kind='sinker', x=_x, y=12, w=2, depth=4, rate=1.1, delay=0.1) for _x in (15, 19, 32, 40)],
                 *[dict(t='kit', kind='crumble', x=_x, y=11, w=2, delay=0.4, respawn=2.5) for _x in (28, 43)],
                 _en('du_scarab', 50, 11), _xd('palmdead', 3, 11), _xd('obelisk', 11, 11), _xd('jars', 53, 11),
                 _xa('dropmark', 51, 11)])
r.walls().open('W', 8, 11)
r.fill(0, 0, 55, 1).fill(6, 0, 9, 1, '.').fill(0, 12, 55, 17)
_rungs(r, 6, 9, [0, 3, 6, 9])
r.fill(14, 12, 45, 16, '-')                                  # the lake: sink too deep and the sand swallows you
r.fill(24, 10, 25, 16).fill(36, 11, 37, 16)                  # two drowned pillars to rest on
r.put(36, 10, 'i')
r.fill(50, 12, 52, 17, '.').fill(50, 12, 52, 12, '=').fill(50, 15, 52, 15, '=')    # the stair down to the Sun Dial
for _x, _y, _ch in [(20, 2, 'x'), (44, 2, 'x'), (2, 11, 'k'), (54, 11, 'b')]:
    r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DU13 The Sun Dial (puzzle)
# Noon falls through a hole in the roof. Three mirrors carry it down, across and up to the sun-socket over the door.
r = Room('DU13', 'The Sun Dial', 'dunes', 500, 193, 40, 24, indoor=True, xsb_hall=True, needs=['talon'], x3=True, puzzle=True, chests=['emberstone'],
         xsb_paint=[['sundial', 20, 17], ['sealdoor', 4, 17]],
         spawns=[dict(t='kit', kind='beam', x=26, y=2, dir='down', id='sun'),
                 dict(t='kit', kind='mirror', x=26, y=13, id='M1', rot=0),
                 dict(t='kit', kind='mirror', x=14, y=13, id='M2', rot=2),
                 dict(t='kit', kind='mirror', x=14, y=6, id='M3', rot=0),
                 dict(t='kit', kind='mirror', x=20, y=9, id='M4', rot=1),
                 dict(t='kit', kind='socket', x=6, y=6, id='so', targets=['door'], msg='The sun reaches the door. It opens.'),
                 dict(t='kit', kind='gate', x=4, y=17, id='door', persist=True),
                 _lore(31, 17, 'sb_11', look='tablet'),
                 _xd('brazier_du', 9, 17), _xd('statue_du', 38, 17, face=-1), _xd('jars', 29, 17), _xa('sunshaft', 26, 2)])
r.walls().open('N', 34, 36)
r.fill(0, 0, 39, 1).fill(34, 0, 36, 1, '.').fill(0, 18, 39, 23)
_rungs(r, 34, 36, [0, 3, 6, 9, 12, 15])
r.fill(12, 9, 16, 9, '=')                                    # a ledge to reach the high mirror
r.put(2, 17, 'C')
for _x, _y, _ch in [(1, 17, 'k'), (38, 2, 'x')]:
    r.put(_x, _y, _ch)
