# ============================================================ EXPANSION 3 — agent SC: Starfall Crater, NEO-HALLOW, The Ember, The Hermit's Hollow
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, HAZARD, free_spot). Engine: web/src/55_sc.js.
# Decor / region mechanics are `t:'xsc'` spawns (handled in 55_sc.js); kit + sys objects per docs/KIT_API.md.
#
# Every link is a walkable room edge (EXPANSION3_CONTRACT §8); the only gated seams are `passage`s that open when a boss rests.
# STARFALL (zones x 492..760, y -300..-163 and x 749..900, y -170..-70; old Starfall shifted up 70)
#   Wing A (east road): SF7 --passage (Astrel rests)--> SF10 Observatory Road (shrine) -> SF16 The Stargazer's Seat (vista)
#                       SF10 -> up SF13 Meteor Steps -> SF14 Gravity Wells -> SF17 The Crater Edge (vista)
#   Wing B (high glass): SF14 -> SF11 The Glass Expanse (shrine) -> SF12 Glass Canyon -> SF15 The Lens Array (puzzle)
#                       SF11 roof grate -> SF18 Moonstep Trial -> SF19 The Comet's Heart (secret); SF11 pool drop -> SF9 (loop)
#   W6 (X4 -> SF1 sky stair) is dressed here (POST_LINKS).
# NEO-HALLOW (zone x 1000..1400, y -150..150)
#   Wing A (undercity): NH4 grate -> NH8 The Megablock (shrine) -> NH10 Service Tunnels -> NH9 Back Alleys -> NH13 Firewall
#                       side: NH14 Security Lockdown (gauntlet), NH17 The Dev Room
#   Wing B (skyway):    NH8 -> NH11 Data Highway (shrine) -> NH12 Billboard Climb -> grate up into NH6
#                       side: NH16 Glitch Run (trial), NH15 Neon Skyline (vista)
# THE EMBER (zone x 452..760, y 0..60): E3 --passage (First Ember rests)--> E4 The Cinder Road (shrine) -> E5 The Ashen
#                       Expanse (shrine) -> E1; side: E6 The Last Hearth (vista), E7 Trial of the First Flame
# THE HERMIT'S HOLLOW (zone x -140..-41, y 0..14): H1 --passage (Oswin rests)--> H2 The Hidden Path (shrine) -> H3 The
#                       Hermit's Garden (vista) --rotten boards--> H4 Oswin's Stash (secret)

HAZARD.add('1')           # the NEO-HALLOW data abyss burns (reach: deadly, not a floor)


def _sc_paint(r, rows):
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            r.g[y][x] = ch
    return r


def _sp(r, *items):
    r.kw.setdefault('spawns', []).extend(items)
    return r


def _K(kind, x, y, **kw): return dict(t='kit', kind=kind, x=x, y=y, **kw)
def _Y(kind, x, y, **kw): return dict(t='sys', kind=kind, x=x, y=y, **kw)
def _D(kind, x, y, **kw): return dict(t='xsc', kind=kind, x=x, y=y, **kw)      # SC decor / region mechanics (55_sc.js)
def _E(tp, x, y, **kw): return dict(t='enemy', type=tp, x=x, y=y, **kw)
def _SF(kind, x, y, **kw): return dict(t='sf_prop', kind=kind, x=x, y=y, **kw)   # Starfall's own props (35_starfall.js)
def _NH(kind, x, y, **kw): return dict(t='nh_deco', kind=kind, x=x, y=y, **kw)   # NEO-HALLOW's own props (36_neohallow.js)


def _star(r, x0, y0, x1, y1):
    """paint starlight ('+', low gravity) over empty cells only"""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if r.g[y][x] == '.':
                r.g[y][x] = '+'


def _X3(**kw):
    kw.setdefault('x3', True)
    return kw


# ================================================================================================ STARFALL CRATER
# EXPANSION3 §8 layout (final coordinates). The wing leaves Astrel's arena (SF7) through its east wall, which splits once
# Astrel has fallen, runs east along the old pilgrims' road, climbs the meteor crater and the gravity wells, and comes out
# west onto the Glass Expanse high above the crater. The Expanse's starlight pool drains into the Last Light (SF9), which
# opens west onto the Crater Rim (SF6): the loop back. Side rooms: the Seat (end of the road), the Crater Edge (off the
# wells), the Canyon and the Lens Array (west of the Expanse), the Moonstep Trial and the Comet's Heart (above it).
#   SF10 Observatory Road   748..803  x -117..-104   west: SF7 (passage)  east: SF16  roof grate: SF13
#   SF16 Stargazer's Seat   804..839  x -123..-104   west: SF10
#   SF13 Meteor Steps       748..803  x -141..-118   floor: SF10  roof: SF14
#   SF14 Gravity Wells      749..796  x -170..-142   floor: SF13  west: SF11  east: SF17
#   SF17 The Crater Edge    797..836  x -165..-148   west: SF14
#   SF11 The Glass Expanse  629..748  x -194..-163   east: SF14  west: SF12  floor pit: SF9  roof: SF18
#   SF12 Glass Canyon       581..628  x -187..-168   east: SF11  west: SF15
#   SF15 The Lens Array     541..580  x -191..-168   east: SF12
#   SF18 The Moonstep Trial 680..727  x -242..-195   floor: SF11  east (cracked seam): SF19
#   SF19 The Comet's Heart  728..743  x -242..-229   west: SF18
# (§8.1 lists Starfall's east strip from x 749; SF10/SF13 use x 748, the column that meets SF7's east wall at x 747.)

# ---------------------------------------------------------------- SF7 (anchor): Astrel's arena splits open to the east
_sf7 = ROOM('SF7')
if all(_sf7.g[y][47] == '#' for y in range(13, 17)):
    _sf7.fill(47, 13, 47, 16, '.')
    _sp(_sf7, _Y('passage', 47, 16, w=1, h=4, id='xs_east', cond={'flag': 'boss:astrel'}, drift='star', light='190,210,255', wind=1))
else:
    print('SC: SF7 east wall changed; the Observatory Road passage skipped')

# ---------------------------------------------------------------- SF10 Observatory Road (path)
r = Room('SF10', 'Observatory Road', 'starfall', 748, -117, 56, 14, **_X3(needs=['talon']), shrine="Pilgrims' Rest", indoor=True)
_sc_paint(r, [
    #0         1         2         3         4         5
    #01234567890123456789012345678901234567890123456789012345
    "??????????????????################################===###",  # 0  the crater's glass lip roofs the road
    "#?????????.......................................#.....#",  # 1
    "#??????................................................#",  # 2
    "#??....................................................#",  # 3
    "#......................................................#",  # 4
    "#.........................????.........................#",  # 5
    "#......................???####???......................#",  # 6
    "#......................##########......................#",  # 7
    ".......................##########......................#",  # 8  <- Astrel's arena
    "....................???##########???....................",  # 9  -> the Stargazer's Seat
    "....................################....=====...........",  # 10
    "....................################....................",  # 11
    "#########.....######################^^^^^^^^############",  # 12
    "########################################################",  # 13
])
r.fill(20, 1, 34, 1).fill(22, 2, 31, 2, '?')                 # the lip sags over the ridge
for x0, x1, y in [(45, 47, 8), (48, 50, 5), (50, 52, 3)]:
    r.fill(x0, y, x1, y, '=')                                 # a stair of glass shards up to the grate in the roof
r.put(49, 1, '.')
r.put(11, 12, 'S')
_sp(r, _D('gratehint', 51, 1), _E('sf_pilgrim', 48, 11), _E('sf_pilgrim', 29, 4), _E('sf_wisp', 44, 5, air=True),
    _SF('idol', 4, 11), _SF('spire', 17, 11), _SF('godbone', 53, 11), _SF('shard', 33, 4), _SF('arch', 25, 4),
    _D('wayshrine', 47, 11), _D('glassgrass', 8, 11), _D('glassgrass', 53, 11), _D('glassgrass', 3, 11), _D('emberrock', 49, 11),
    _Y('lore', 6, 11, page='sc_2', look='corpse'))

# ---------------------------------------------------------------- SF16 The Stargazer's Seat (vista), at the road's end
r = Room('SF16', "The Stargazer's Seat", 'starfall', 804, -123, 36, 20, **_X3(needs=['talon'], vista=True))
r.fill(0, 0, 0, 14).fill(35, 0, 35, 19).fill(0, 18, 35, 19)
r.fill(26, 11, 34, 17)                        # the lookout (bench)
r.fill(32, 10, 34, 10, '?')                   # a glass lip behind the bench
r.fill(23, 13, 25, 17)                        # step
r.fill(14, 15, 22, 17)                        # the terrace under the ruined dome
r.fill(12, 16, 13, 17)
_star(r, 5, 3, 24, 9)
_sp(r, _Y('bench', 30, 10, id='bench', view=[14, 6], lore='sc_1', face=-1),
    _SF('telescope', 27, 10, face=-1), _D('dome', 19, 14), _SF('shard', 8, 7), _SF('shard', 4, 3), _SF('idol', 33, 9),
    _D('meteorshower', 17, 2), _SF('lens', 14, 14), _D('glassgrass', 7, 17), _D('glassgrass', 20, 14), _D('glassgrass', 29, 10),
    _SF('shard', 29, 3), _SF('spire', 15, 14), _D('glassgrass', 3, 17), _D('emberrock', 10, 17))

# ---------------------------------------------------------------- SF13 Meteor Steps (parkour): up from the road, out through the roof
# Meteors fall, strike, cool into stepping stones, then crack apart (kit `phase` slabs drawn as meteors).
r = Room('SF13', 'Meteor Steps', 'starfall', 748, -141, 56, 24, **_X3(needs=['talon'], parkour=True))
r.fill(0, 0, 0, 23).fill(55, 0, 55, 23).fill(0, 22, 55, 23).fill(0, 0, 48, 0)
r.fill(6, 0, 8, 0, '.')                                                          # up into the wells
r.fill(9, 22, 48, 22, '^')                                                       # the crater floor: glass teeth
r.fill(50, 22, 52, 23, '.').fill(50, 21, 52, 21, '=')                            # up from the road: a grate in the floor
r.fill(42, 17, 43, 21).fill(41, 18, 44, 21, '?').fill(42, 17, 43, 17)           # pillar 1 (glass skirt)
r.fill(29, 12, 31, 21).fill(32, 16, 32, 21, '?').fill(28, 14, 28, 21, '?')       # pillar 2
r.fill(17, 9, 18, 21, '?')                                                       # a splinter of star-glass
r.fill(1, 7, 8, 21).fill(9, 11, 9, 21, '?')                                      # the exit shelf
r.fill(47, 1, 54, 2, '?').fill(51, 3, 54, 4, '?').fill(53, 5, 54, 7)             # a glass overhang, top-right
r.fill(10, 1, 19, 1, '?').fill(12, 2, 15, 2, '?')
r.fill(6, 4, 8, 4, '=').fill(6, 1, 8, 1, '=')                                    # up from the shelf to the roof
_star(r, 19, 3, 27, 8)
_sp(r, _D('gratehint', 51, 20, down=True),
    *[_K('phase', x, y, w=2, period=4.4, on=[0.12, 0.86], offset=o, look='meteor', id=f'm{i}')
      for i, (x, y, o) in enumerate([(46, 20, 0.0), (38, 15, 0.16), (34, 13, 0.30), (25, 10, 0.46), (21, 9, 0.6), (13, 8, 0.74)])],
    _E('sf_wisp', 35, 6, air=True), _E('sf_wisp', 11, 5, air=True),
    _D('meteorfall', 27, 1), _D('crater', 52, 20), _D('crater', 5, 6), _SF('spire', 5, 6), _SF('shard', 41, 8), _SF('shard', 24, 16),
    _D('glassgrass', 53, 20), _D('glassgrass', 2, 6), _D('emberrock', 30, 11), _D('emberrock', 43, 16), _SF('shard', 47, 8), _SF('shard', 11, 12))

# ---------------------------------------------------------------- SF14 Gravity Wells (parkour)
# Splinters of the star float in the shaft; each drags whatever leaps past it (55_sc.js `well`).
r = Room('SF14', 'Gravity Wells', 'starfall', 749, -170, 48, 29, **_X3(needs=['talon'], parkour=True), items=['emberstone'], indoor=True)
r.walls().fill(5, 28, 7, 28, '.').fill(5, 27, 7, 27, '=')          # up from the meteor crater
r.open('W', 1, 4).open('E', 14, 16)
r.fill(1, 27, 4, 27).fill(8, 27, 46, 27, '^')
for x0, x1, y, ch in [(10, 14, 24, '#'), (18, 22, 21, '#'), (26, 30, 18, '#'), (34, 38, 15, '#'), (41, 46, 17, '#'), (26, 30, 12, '#'),
                      (17, 21, 9, '#'), (8, 12, 7, '?'), (1, 6, 5, '#'), (38, 42, 8, '?'), (29, 34, 4, '?')]:
    r.fill(x0, y, x1, y + 1, ch)
r.fill(1, 16, 3, 17).fill(1, 18, 2, 20, '?').fill(44, 19, 46, 23, '?').fill(40, 1, 46, 2, '?')
r.put(2, 15, 'i')
_sp(r, _D('well', 16, 18, r=5), _D('well', 30, 14, r=5), _D('well', 36, 18, r=4), _D('well', 8, 12, r=4), _D('gratehint', 6, 26, down=True),
    _E('sf_wisp', 24, 5, air=True), _SF('shard', 12, 4), _SF('spire', 44, 16), _D('glassgrass', 3, 4), _D('emberrock', 27, 10),
    _SF('shard', 40, 11), _D('glassgrass', 20, 20), _D('glassgrass', 33, 13), _D('reflect', 24, 18))

# ---------------------------------------------------------------- SF17 The Crater Edge (vista), off the wells
r = Room('SF17', 'The Crater Edge', 'starfall', 797, -165, 40, 18, **_X3(needs=['talon'], vista=True))
r.fill(0, 0, 0, 17).fill(39, 0, 39, 17).fill(0, 16, 39, 17).open('W', 9, 11)
r.fill(1, 12, 14, 15).fill(15, 13, 18, 15)                    # the rim: a promontory over the crater
r.fill(19, 15, 31, 15)
r.fill(32, 12, 38, 15).fill(35, 9, 38, 11).fill(36, 5, 38, 8, '?').fill(37, 2, 38, 4, '?')   # the crag, east
r.fill(30, 11, 31, 11, '?')
_sp(r, _Y('bench', 8, 11, id='bench', view=[18, 5], lore='sc_5', face=1),
    _D('craterglow', 21, 12), _SF('idol', 12, 11), _SF('spire', 16, 12), _SF('shard', 20, 5), _SF('shard', 30, 3), _D('glassgrass', 4, 11),
    _D('glassgrass', 34, 11), _D('meteorshower', 12, 1), _SF('godbone', 26, 14), _D('emberrock', 21, 14), _D('glassgrass', 29, 14))
_star(r, 17, 1, 34, 9)

# ---------------------------------------------------------------- SF11 The Glass Expanse (grand)
# Low road: across the crater plain (a crater of glass teeth, the Fallen Star's plateau, the starlight pool that drains down
# into the Last Light). High road: floating glass islands west to the canyon and up to the Moonstep Spire. Secret: a cracked
# seam in the plateau hides a cave. Landmark: the Fallen Star, lodged in the plateau, visible from everywhere.
r = Room('SF11', 'The Glass Expanse', 'starfall', 629, -194, 120, 32, **_X3(needs=['talon'], grand=True), items=['seed'], shrine='Glassfall Shrine')
r.fill(0, 0, 0, 31).fill(119, 0, 119, 31).fill(0, 27, 119, 31)
r.open('W', 11, 14).open('E', 25, 28)
r.fill(100, 27, 118, 28, '.')                                  # the east end sits lower (you come in from the wells)
# the Moonstep Spire's foot overhead: a crust of black glass with one grate
r.fill(51, 0, 98, 0).fill(51, 1, 58, 1, '?').fill(64, 1, 71, 1, '?').fill(88, 1, 98, 1, '?').fill(92, 2, 98, 2, '?')
r.fill(81, 0, 83, 0, '=')
# west shelf (the canyon mouth) + the drop to the plain
r.fill(0, 15, 11, 26).fill(12, 19, 14, 26).fill(15, 23, 16, 26).fill(10, 15, 11, 15, '?')
# crater A (glass teeth) with a floating shard
r.fill(20, 27, 28, 28, '.').fill(20, 28, 28, 28, '^').fill(19, 27, 19, 27, '?').fill(29, 27, 29, 27, '?')
r.fill(23, 24, 25, 24, '=')
r.fill(33, 24, 35, 26, '?').fill(32, 25, 36, 26, '?').fill(34, 23, 34, 23, '?')     # a glass boss
# the Fallen Star's plateau (step, plateau, the cave behind a cracked seam)
r.fill(44, 24, 49, 26).fill(50, 21, 66, 26).fill(67, 24, 69, 26)
r.fill(51, 22, 60, 23, '.').fill(50, 22, 50, 23, 'B')
r.put(57, 23, 'i')
# the starlight pool: it drains through the crater floor into the Last Light below (SF9)
r.fill(72, 27, 89, 31, '.').fill(71, 27, 71, 31, '?').fill(90, 27, 90, 31, '?')
r.fill(76, 24, 77, 24, '=').fill(83, 23, 84, 23, '=')
_star(r, 72, 14, 89, 31)
r.fill(92, 24, 97, 26).fill(91, 25, 91, 26, '?').fill(93, 23, 96, 23, '?')          # a mound (the golem)
# high road: floating glass islands
for x0, x1, y in [(15, 19, 12), (23, 27, 10), (31, 35, 7), (38, 44, 4), (48, 51, 8), (57, 61, 7), (66, 70, 10), (75, 79, 12), (86, 90, 15), (104, 108, 19)]:
    r.fill(x0, y, x1, y, '?').fill(x0 + 1, y + 1, x1 - 1, y + 1)
    if x1 - x0 >= 4: r.fill(x0 + 2, y + 2, x1 - 2, y + 2, '?')
r.fill(79, 7, 82, 7, '=').fill(82, 3, 84, 3, '=')               # up to the grate under the Spire
r.fill(112, 22, 116, 22, '=').fill(96, 16, 99, 16, '=')         # up from the east end to the high road
r.put(6, 14, 'S')
_sp(r, _E('sf_pilgrim', 17, 26), _E('sf_golem', 40, 26), _E('sf_pilgrim', 64, 20), _E('sf_golem', 94, 22), _E('sf_pilgrim', 106, 28),
    _E('sf_wisp', 29, 4, air=True), _E('sf_wisp', 72, 8, air=True), _E('sf_wisp', 104, 14, air=True),
    _D('fallenstar', 58, 20), _SF('godbone', 9, 14), _SF('godbone', 114, 28), _SF('spire', 46, 23), _SF('spire', 68, 23),
    _SF('spire', 101, 28), _SF('shard', 20, 3), _SF('shard', 92, 6), _SF('arch', 41, 3), _SF('idol', 13, 18),
    _D('crater', 39, 26), _D('crater', 110, 28), _D('glassgrass', 3, 14), _D('glassgrass', 30, 26), _D('glassgrass', 62, 20),
    _D('glassgrass', 99, 26), _D('glassgrass', 117, 28), _D('emberrock', 45, 23), _D('emberrock', 116, 28), _D('craterglow', 80, 29),
    _Y('lore', 55, 23, page='sc_3', look='corpse', face=-1),
    _SF('shard', 10, 5), _SF('shard', 50, 3), _SF('shard', 78, 5), _SF('shard', 110, 9), _SF('shard', 64, 13),
    _D('glassgrass', 9, 14), _D('glassgrass', 40, 26), _D('glassgrass', 55, 20), _SF('godbone', 62, 20), _D('emberrock', 47, 23),
    _D('emberrock', 18, 26), _D('meteorfall', 30, 3))

# ---------------------------------------------------------------- SF12 Glass Canyon (path), west of the Expanse
r = Room('SF12', 'Glass Canyon', 'starfall', 581, -187, 48, 20, **_X3(needs=['talon']))
r.fill(0, 0, 0, 19).fill(47, 0, 47, 19).fill(0, 18, 47, 19)
r.open('W', 15, 17).open('E', 4, 7)
r.fill(40, 8, 46, 17).fill(39, 11, 39, 17, '?').fill(43, 1, 46, 3, '?').fill(45, 0, 46, 0)     # the east cliff (you arrive on it)
r.fill(30, 11, 35, 12).fill(31, 13, 34, 13, '?')                                               # shelves down the canyon
r.fill(20, 14, 25, 15).fill(21, 16, 24, 16, '?')
r.fill(1, 2, 5, 14).fill(6, 5, 7, 14, '?').fill(6, 3, 6, 4, '?').fill(1, 0, 3, 1)             # the west wall of the canyon
r.fill(12, 15, 13, 17, '?').fill(28, 16, 29, 17, '?').fill(36, 16, 36, 17, '?')
_sp(r, _E('sf_golem', 32, 17), _E('sf_pilgrim', 33, 10), _E('sf_wisp', 18, 6, air=True),
    _SF('spire', 42, 7), _SF('shard', 26, 4), _SF('godbone', 9, 17), _D('glassgrass', 23, 13), _D('glassgrass', 44, 7), _D('glassgrass', 3, 17),
    _D('reflect', 24, 2), _SF('shard', 12, 6), _SF('shard', 36, 3), _SF('spire', 24, 13), _D('emberrock', 32, 10), _D('glassgrass', 15, 17), _D('glassgrass', 38, 17))

# ---------------------------------------------------------------- SF15 The Lens Array (puzzle) — x 576..615, y -162..-139
# A lens in the vault's roof gathers starlight into a beam. Turn the four lenses so the light finds each of the three
# sockets in turn; each lit socket lifts one of the three bars sealing the reliquary. Clue: the old light-paths are still
# etched into the walls as faint glowing veins (55_sc.js `veins`), and the astronomer's slate by the door.
r = Room('SF15', 'The Lens Array', 'starfall', 541, -191, 40, 24, **_X3(needs=['talon'], puzzle=True), indoor=True, chests=['emberstone'])
r.walls().open('E', 19, 21).fill(0, 22, 39, 23)
r.fill(1, 18, 8, 18).fill(1, 17, 8, 17, '?')          # the reliquary roof (the third socket sits on it)
r.put(2, 21, 'C')
r.fill(14, 18, 24, 18, '=')                            # lower gallery (reach the second lens)
r.fill(24, 14, 27, 14, '=')                            # step
r.fill(14, 10, 26, 10, '=').fill(30, 10, 37, 10, '=')  # upper galleries (the first and third lenses)
r.fill(28, 1, 38, 2).fill(36, 3, 38, 8)                # masonry, top-right
r.fill(1, 1, 10, 3).fill(1, 4, 2, 9)                   # masonry, top-left (the first socket in its niche)
r.fill(3, 4, 3, 5, '.').fill(4, 4, 4, 5)
r.fill(36, 11, 38, 15, '?').fill(37, 16, 38, 17, '?')   # a glass buttress by the door
_sp(r, _K('beam', 20, 1, dir='down', id='sky', style='star'),
    _K('mirror', 20, 6, id='L1', rot=2), _K('mirror', 20, 14, id='L2', rot=0), _K('mirror', 34, 6, id='L3', rot=2), _K('mirror', 8, 14, id='L4', rot=0),
    _K('socket', 3, 6, id='s1', targets=['b1']), _K('socket', 34, 17, id='s2', targets=['b2']), _K('socket', 8, 16, id='s3', targets=['b3']),
    _K('gate', 5, 21, id='b1'), _K('gate', 6, 21, id='b2'), _K('gate', 7, 21, id='b3'),
    _D('veins', 12, 20, paths=[[[20, 1], [20, 6], [3, 6]], [[20, 1], [20, 6], [34, 6], [34, 17]], [[20, 1], [20, 14], [8, 14], [8, 16]]]),
    _D('lenshint', 13, 20, mirrors=['L1', 'L2', 'L3', 'L4']),
    _Y('lore', 27, 21, page='sc_4', look='tablet'), _SF('orrering', 12, 21), _SF('lens', 26, 21), _D('glassgrass', 22, 21))

# ---------------------------------------------------------------- SF18 Moonstep Trial — x 664..711, y -206..-159
# A tower of star-glass above the wells. Nothing to cling to until the very top: posts over glass teeth, meteors on a
# beat, a splinter that slings you across, then the long leap to the reliquary. Needs every jump you have (triple jump).
r = Room('SF18', 'The Moonstep Spire', 'starfall', 680, -242, 48, 48, **_X3(needs=['talon', 'wings', 'moonstep'], trial=True), indoor=True)
r.walls().fill(30, 47, 32, 47, '.')
r.fill(24, 45, 29, 46).fill(33, 45, 46, 46).fill(30, 45, 32, 45, '=')   # the ledges you rise between (the sigil stands right)
r.fill(1, 46, 23, 46, '^')                                   # glass teeth under the posts
for x, top in [(18, 42), (11, 39), (4, 36)]:
    r.fill(x, top, x, 45, '?')
r.fill(10, 29, 13, 30, '?').fill(11, 31, 12, 31, '?')        # L2: an island after the triple jump
r.fill(37, 22, 42, 23).fill(38, 24, 41, 24, '?').fill(43, 22, 46, 35, '?')   # L3 and the east glass wall
r.fill(36, 36, 46, 41, '?').fill(37, 35, 46, 35, '?')        # the glass mass under L3's wall
r.fill(18, 16, 24, 17).fill(19, 18, 23, 18, '?')             # L4
r.fill(12, 4, 13, 18).fill(17, 4, 17, 11).fill(14, 16, 17, 18)   # the rock chimney (you walk in at its foot, climb out the top)
r.fill(24, 4, 31, 5).fill(25, 6, 30, 6, '?')                 # the reliquary ledge
r.fill(20, 1, 38, 1, 'v').fill(1, 1, 11, 1, 'v')              # teeth in the roof: don't overshoot
r.fill(36, 8, 46, 9).fill(41, 10, 46, 11, '?')               # the crag beyond the reliquary (a cracked seam: the Comet's Heart)
r.fill(47, 5, 47, 7, '.').fill(46, 5, 46, 7, 'B')   # (a breakable on the room edge can't be walked back through)
r.fill(36, 12, 42, 12, 'v')
_sp(r, _D('gratehint', 31, 44, down=True), _Y('trial', 36, 44, id='moon', par=25, reward='c_x3_moon', region='Moonstep Spire', name='The Moonstep Trial'),
    _Y('trial_goal', 28, 3, trial='moon'),
    *[_K('phase', x, y, w=2, period=3.0, on=[a, round((a + 0.55) % 1, 3)], look='meteor', id=f'tm{i}')
      for i, (x, y, a) in enumerate([(17, 27, 0.0), (22, 25, 0.27), (27, 26, 0.54), (32, 24, 0.81)])],
    _D('well', 30, 15, r=5), _D('well', 26, 38, r=4),
    _SF('shard', 43, 5), _SF('shard', 8, 20), _SF('spire', 44, 44), _D('glassgrass', 26, 44))


# ---------------------------------------------------------------- SF19 The Comet's Heart (secret) — x 712..727, y -206..-193
# Behind a cracked seam in the Moonstep Spire's crown: the comet that followed the star down, its heart still burning.
r = Room('SF19', "The Comet's Heart", 'starfall', 728, -242, 16, 14, **_X3(needs=['talon', 'wings', 'moonstep'], secret=True), indoor=True, items=['shard'])
r.walls().open('W', 5, 7)
r.fill(0, 8, 4, 13).fill(0, 12, 15, 13).fill(11, 9, 14, 11, '?').fill(12, 8, 14, 8, '?')
r.fill(1, 1, 4, 2, '?').fill(10, 1, 14, 3, '?')
r.put(7, 11, 'i')
_sp(r, _D('comet', 8, 6), _Y('lore', 10, 11, page='sc_6', look='tablet', face=-1), _SF('shard', 3, 4), _D('glassgrass', 2, 7))


# ================================================================================================ NEO-HALLOW
def _slab(r, x0, x1, top, ch='#', th=2):
    r.fill(x0, top, x1, top + th - 1, ch)


# ---------------------------------------------------------------- NH9 Back Alleys — x 1040..1087, y 64..79 (rain)
r = Room('NH9', 'Back Alleys', 'neohallow', 1040, 64, 48, 16, **_X3(needs=['talon']))
r.fill(0, 0, 0, 15).fill(47, 0, 47, 15).fill(0, 13, 47, 15)
r.open('W', 10, 12).open('E', 10, 12)
r.fill(1, 0, 6, 5).fill(1, 6, 3, 9)                         # the tenement on the west (its doorway opens on the Firewall below)
r.fill(18, 11, 24, 12)                                      # a loading dock
r.fill(38, 3, 46, 5).fill(41, 6, 46, 7)                     # the east block's overhang (a rooftop on it)
for x0, x1, y in [(27, 30, 10), (32, 35, 7), (27, 30, 4)]:
    r.fill(x0, y, x1, y, '=')                               # fire escape
r.fill(36, 4, 37, 4, '=')
r.fill(9, 13, 14, 13, '1').fill(9, 14, 14, 15)              # a gutter of data abyss
_sp(r,     _E('nh_cyborg', 21, 10), _E('nh_cyborg', 34, 12), _E('nh_drone', 16, 6, air=True),
    _D('vending', 17, 12), _D('vending', 26, 12), _D('dumpster', 36, 12), _D('puddles', 2, 12, w=44), _D('cables', 7, 1, x1=37, sag=3),
    _NH('sign', 11, 12, v=1), _NH('lamp', 30, 12), _NH('vent', 22, 10), _NH('sign', 45, 2, v=0), _NH('antenna', 39, 2),
    _D('neonstrip', 38, 6, w=8, c=1), _D('windows', 7, 1, rx=1, ry=0, w=6, h=6), _D('windows', 40, 8, rx=38, ry=3, w=9, h=3),
    _Y('lore', 43, 2, page='sc_7', look='corpse', face=-1))

# ---------------------------------------------------------------- NH10 Service Tunnels — x 1088..1135, y 66..79
r = Room('NH10', 'Service Tunnels', 'neohallow', 1088, 66, 48, 14, **_X3(needs=['talon']), indoor=True)
r.walls().fill(0, 11, 47, 13)
r.open('W', 8, 10).open('E', 8, 10)
r.fill(1, 1, 47, 2)                                          # the tunnel roof (pipes run under it)
r.fill(10, 3, 12, 5).fill(24, 3, 27, 6).fill(38, 3, 40, 5)   # ducts hanging from the roof
for x0, x1 in [(5, 9), (15, 21), (30, 36), (42, 45)]:
    r.fill(x0, 6, x1, 6, '=')                                # cable trays
r.fill(18, 9, 21, 10)                                        # a junction box on the floor
_sp(r, _D('steam', 14, 10, period=3.0, phase=0.0), _D('steam', 28, 10, period=3.0, phase=1.0), _D('steam', 33, 10, period=3.0, phase=2.0),
    _E('nh_drone', 24, 8, air=True), _E('nh_turret', 44, 10), _E('nh_cyborg', 8, 10),
    _D('pipes', 1, 3, w=46), _NH('rack', 3, 10), _NH('glyph', 20, 8), _NH('lamp', 36, 10), _NH('vent', 41, 10), _D('warnstripes', 18, 8, w=4),
    _D('hazardlamp', 14, 3), _D('hazardlamp', 30, 3))

# ---------------------------------------------------------------- NH8 The Megablock (grand) — x 1136..1183, y 16..79
# A hollowed tower block: the west stair of catwalks, the east elevator, data-abyss floors, a hologram in the atrium.
# Up top a maintenance shaft climbs (wall-jumps) to a grate in the Server Cathedral's floor (NH4). A cracked panel on the
# seventh floor hides the Dev Room.
r = Room('NH8', 'The Megablock', 'neohallow', 1136, 16, 48, 64, **_X3(needs=['talon'], grand=True), indoor=True, shrine='Maintenance Shrine')
r.walls().open('W', 58, 60).open('W', 37, 39).open('E', 40, 42)
r.fill(35, 0, 36, 0, '.').fill(47, 7, 47, 9, '.').fill(46, 7, 46, 9, 'B')
_slab(r, 1, 46, 61, th=3); r.fill(17, 61, 27, 62, '1')        # ground floor, a data abyss in the middle
r.fill(41, 61, 43, 61, '.')                                   # the elevator pit (home stop flush with the floor)
for x0, x1, t in [(3, 7, 58), (15, 19, 55), (4, 8, 49), (10, 14, 46), (17, 21, 43), (21, 23, 58), (43, 46, 40), (41, 44, 37), (14, 17, 37),
                  (38, 42, 31), (32, 36, 28), (3, 7, 22), (10, 14, 19), (26, 30, 13), (25, 29, 7)]:
    r.fill(x0, t, x1, t, '=')
_slab(r, 1, 14, 52, '=', 1); _slab(r, 1, 16, 40, '=', 1)      # west mezzanines, steel catwalks (the Lockdown opens off the upper one)
_slab(r, 30, 46, 43); r.fill(41, 43, 43, 44, '.')              # the highway landing + the elevator's upper stop
_slab(r, 18, 40, 34, '=', 1); r.fill(26, 34, 28, 34, '1')      # floor 4 (a burnt-out data gap)
_slab(r, 8, 30, 25, '=', 1)                                    # floor 5
_slab(r, 16, 40, 16, '=', 1); r.fill(22, 16, 24, 16, '1')      # floor 6
_slab(r, 32, 46, 10, '=', 1)                                   # floor 7 (the cracked panel)
_slab(r, 31, 44, 4); r.fill(34, 1, 34, 1).fill(37, 1, 37, 1)   # the roof slab and the maintenance shaft
_sp(r, _K('lift', 41, 61, to=43, w=3, skin='neon', id='elev'),
    _E('nh_cyborg', 10, 60), _E('nh_cyborg', 34, 60), _E('nh_turret', 45, 42), _E('nh_drone', 22, 48, air=True),
    _E('nh_cyborg', 20, 24), _E('nh_drone', 30, 10, air=True), _E('nh_turret', 38, 15),
    _D('holo', 22, 57), _D('vending', 32, 60), _D('vending', 13, 51), _D('windows', 2, 2, w=16, h=46, grid=1), _D('windows', 30, 46, w=10, h=12, grid=1),
    _NH('billboard', 7, 51, v=2), _NH('billboard', 26, 33, v=0), _NH('sign', 12, 39, v=1), _NH('sign', 38, 15, v=2), _NH('lamp', 44, 60),
    _NH('lamp', 2, 60), _NH('rack', 21, 15), _NH('vent', 14, 24), _NH('antenna', 26, 3), _NH('lamp', 44, 9), _NH('canopy', 6, 39),
    _D('neonstrip', 18, 33, w=23, c=0), _D('neonstrip', 16, 15, w=25, c=1), _D('neonstrip', 30, 42, w=17, c=2),
    _D('gratehint', 35, 3), _D('cables', 1, 27, x1=46, sag=4), _D('cables', 1, 56, x1=46, sag=3))
ROOM('NH8').put(12, 60, 'S')
_n4 = ROOM('NH4')
if all(_n4.g[y][x] == '#' for y in range(25, 30) for x in (14, 15, 16, 17)):
    _n4.fill(15, 26, 16, 29, '.').fill(15, 25, 16, 25, '=')    # a maintenance grate in the Server Cathedral's floor
    _sp(_n4, _D('gratehint', 15, 24, down=True))
else:
    print('SC: NH4 floor changed; Megablock grate skipped')

# ---------------------------------------------------------------- NH17 The Dev Room (secret) — x 1184..1199, y 16..29
r = Room('NH17', 'The Dev Room', 'neohallow', 1184, 16, 16, 14, **_X3(needs=['talon'], secret=True), indoor=True, chests=['seed'])
r.walls().open('W', 7, 9).fill(0, 10, 15, 13)
r.fill(1, 1, 14, 2)
r.put(12, 9, 'C')
_sp(r, _D('devdesk', 6, 9), _D('tpose', 9, 9), _D('missingtex', 13, 3, w=2, h=3), _D('missingtex', 2, 3, w=1, h=2),
    _Y('lore', 3, 9, page='sc_8', look='book'), _NH('rack', 14, 9), _D('glitchroom', 0, 9))

# ---------------------------------------------------------------- NH14 Security Lockdown (gauntlet) — x 1096..1135, y 41..56
r = Room('NH14', 'Security Lockdown', 'neohallow', 1096, 41, 40, 16, **_X3(needs=['talon'], gauntlet=True), indoor=True)
r.walls().open('E', 12, 14).fill(0, 15, 39, 15)
r.fill(36, 1, 36, 10)                                         # the shutter housing (the shutter drops to the floor)
r.fill(6, 9, 11, 9, '=').fill(26, 9, 31, 9, '=').fill(15, 6, 22, 6, '=')
r.fill(1, 1, 35, 1)
_sp(r, _K('gate', 36, 14, id='shut', open=True, skin='neon'),
    _Y('gauntlet', 18, 14, id='lock', look='terminal', name='Security Lockdown', gates=['shut'],
       waves=[[dict(type='nh_drone', x=8, y=6), dict(type='nh_drone', x=28, y=6), dict(type='nh_cyborg', x=5, y=14)],
              [dict(type='nh_cyborg', x=4, y=14), dict(type='nh_cyborg', x=31, y=14), dict(type='nh_turret', x=18, y=5)],
              [dict(type='nh_drone', x=6, y=4), dict(type='nh_drone', x=30, y=4), dict(type='nh_turret', x=8, y=8), dict(type='nh_turret', x=28, y=8)],
              [dict(type='nh_cyborg', x=6, y=14), dict(type='nh_cyborg', x=30, y=14), dict(type='nh_cyborg', x=18, y=5), dict(type='nh_drone', x=18, y=3)]],
       reward=['emberstone', 'shard']),
    _NH('rack', 2, 14), _NH('rack', 34, 14), _NH('lamp', 12, 14), _NH('lamp', 25, 14), _D('alarmlamp', 9, 2), _D('alarmlamp', 27, 2),
    _D('warnstripes', 1, 14, w=35), _NH('glyph', 18, 5), _D('windows', 3, 2, w=30, h=3, grid=1))

# ---------------------------------------------------------------- NH13 Firewall (puzzle) — x 1000..1039, y 60..79
# Four terminals in the gallery each flip two laser gates in the corridor below. Coloured cables run from every terminal
# to the gates it drives (the clue). Every gate must stand open at once to reach the vault.
r = Room('NH13', 'Firewall', 'neohallow', 1000, 60, 40, 20, **_X3(needs=['talon'], puzzle=True), indoor=True, chests=['emberstone'])
r.walls().open('E', 14, 16).fill(0, 17, 39, 19)
r.fill(1, 10, 30, 10)                                          # the corridor roof / gallery floor
r.fill(1, 1, 38, 1)
r.put(3, 16, 'C')
r.fill(33, 14, 36, 14, '=')
_sp(r, *[_K('lever', 9 + 6 * i, 9, id=t, targets=tg, skin='neon') for i, (t, tg) in enumerate([('A', ['G1', 'G2']), ('B', ['G2', 'G3']), ('C', ['G3', 'G4']), ('D', ['G4', 'G1'])])],
    *[_K('gate', x, 16, id=f'G{i + 1}', skin='neon') for i, x in enumerate([8, 14, 20, 26])],
    _D('wiring', 1, 11, links={'A': [9, [8, 14]], 'B': [15, [14, 20]], 'C': [21, [20, 26]], 'D': [27, [26, 8]]}),
    _D('firehint', 2, 11, levers=['A', 'B', 'C', 'D'], gates=['G1', 'G2', 'G3', 'G4']),
    _NH('rack', 32, 16), _NH('rack', 37, 16), _NH('glyph', 34, 13), _NH('lamp', 4, 9), _NH('lamp', 30, 16),
    _Y('lore', 29, 9, page='sc_9', look='tablet', face=-1), _D('windows', 2, 2, w=26, h=5, grid=1))

# ---------------------------------------------------------------- NH11 Data Highway (parkour) — x 1184..1279, y 44..61
# Two maglev lanes over the data abyss: eastbound low, westbound high. Cars surface out of the stream at one end and sink
# back into it at the other (kit movers on a loop whose return leg runs inside the abyss, where they're hidden).
r = Room('NH11', 'Data Highway', 'neohallow', 1184, 44, 96, 18, **_X3(needs=['talon'], parkour=True), shrine='Terminus Line Shrine')
r.fill(0, 0, 0, 17).fill(95, 0, 95, 17).fill(0, 17, 95, 17).fill(64, 0, 94, 0)
r.open('W', 12, 14).open('E', 12, 14).fill(70, 0, 72, 0, '.')
r.fill(1, 15, 6, 16)                                           # the on-ramp
r.fill(7, 15, 63, 16, '1')                                     # the data abyss
r.fill(22, 13, 24, 16).fill(42, 13, 44, 16)                    # pylons
r.fill(7, 13, 14, 16).fill(55, 13, 62, 16)                     # the portals the cars surface from and sink into
r.fill(63, 15, 94, 16)                                         # the station
r.fill(31, 0, 35, 1).fill(50, 0, 54, 1)                        # sign gantries (laser emitters)
for x0, x1, y in [(66, 69, 12), (71, 74, 9), (66, 69, 6), (69, 72, 3)]:
    r.fill(x0, y, x1, y, '=')
_sp(r, *[_K('mover', 7, 12, w=4, path=[[7, 12], [59, 12], [59, 16], [7, 16]], loop=True, speed=3.5, wait=0.1, offset=i / 5, look='maglev', id=f'ca{i}')
         for i in range(5)],
    *[_K('mover', 55, 8, w=4, path=[[55, 8], [11, 8], [11, 16], [55, 16]], loop=True, speed=4.2, wait=0.1, offset=i / 4 + 0.1, look='maglev', id=f'cb{i}')
      for i in range(4)],
    dict(t='nh_laser', x=33, y=14, y0=2, y1=14, period=3.6, on=1.0, phase=0.0), dict(t='nh_laser', x=52, y=14, y0=2, y1=14, period=3.6, on=1.0, phase=1.8),
    _E('nh_drone', 28, 5, air=True), _E('nh_drone', 48, 6, air=True), _E('nh_turret', 90, 14),
    _NH('sign', 23, 12, v=1), _NH('sign', 43, 12, v=2), _NH('lamp', 3, 14), _NH('lamp', 78, 14), _NH('canopy', 84, 14), _NH('antenna', 92, 14),
    _NH('billboard', 88, 14, v=0), _D('datastream', 15, 14, w=40), _D('holo', 13, 6, small=True), _D('holo', 60, 5, small=True),
    _D('neonstrip', 64, 14, w=31, c=1), _D('railing', 64, 14, w=31))

# ---------------------------------------------------------------- NH16 Glitch Run (trial) — x 1280..1343, y 38..61
# The platforms only exist on their half of the beat; glitch veils (burn through with the Ember Dash) wall the way.
r = Room('NH16', 'Glitch Run', 'neohallow', 1280, 38, 64, 24, **_X3(needs=['talon', 'emberdash'], trial=True), indoor=True)
r.walls().open('W', 18, 20).fill(0, 21, 63, 23)
r.fill(8, 21, 62, 22, '1')
r.fill(20, 1, 20, 9).fill(20, 10, 20, 20, '%')                 # veil 1 (burn through low)
r.fill(27, 16, 29, 20).fill(28, 15, 28, 15)                    # a static island
r.fill(38, 9, 39, 20)                                          # a server tower
r.fill(42, 11, 42, 20).fill(42, 2, 42, 10, '%').fill(42, 1, 42, 1)   # veil 2 (burn through high)
r.fill(56, 6, 62, 7).fill(58, 8, 62, 20)                       # the goal ledge
r.fill(1, 1, 62, 1, 'v').fill(1, 1, 19, 1, '#')                # data spikes in the roof over the run
r.fill(44, 2, 55, 2, 'v').fill(43, 1, 55, 1)                   # ... and hanging low over the last stretch
BEAT = 1.6
_sp(r, _Y('trial', 4, 20, id='glitch', par=15, reward='c_x3_glitch', region='Glitch Run', name='The Glitch Run'),
    _Y('trial_goal', 60, 5, trial='glitch'),
    *[_K('phase', x, y, w=2, period=BEAT, on=[0, 0.42] if g == 'A' else [0.5, 0.92], look='glitch', group='g' + g, id=f'p{i}')
      for i, (x, y, g) in enumerate([(9, 19, 'A'), (13, 18, 'B'), (17, 17, 'A'), (23, 17, 'B'), (32, 13, 'A'), (35, 10, 'B'),
                                     (45, 9, 'A'), (49, 7, 'B'), (53, 7, 'A')])],
    dict(t='nh_laser', x=26, y=20, y0=2, y1=20, period=BEAT, on=0.5, warn=0.3, phase=0.4),
    dict(t='nh_laser', x=47, y=8, y0=2, y1=20, period=BEAT, on=0.55, warn=0.3, phase=0.1),
    _D('beat', 32, 12, period=BEAT), _NH('rack', 2, 20), _NH('glyph', 5, 16), _D('glitchroom', 0, 20))

# ---------------------------------------------------------------- NH12 Billboard Climb (parkour) — x 1248..1279, y 2..43
# Stacked billboards on a tower face; the dark ones aren't there (kit `phase` slabs drawn as flickering billboards).
r = Room('NH12', 'Billboard Climb', 'neohallow', 1248, 2, 32, 42, **_X3(needs=['talon'], parkour=True))
r.fill(0, 0, 0, 41).fill(31, 0, 31, 41).fill(0, 0, 31, 0).fill(0, 41, 31, 41)
r.fill(6, 41, 8, 41, '.').fill(2, 0, 3, 0, '.').open('W', 22, 24)
r.fill(1, 1, 1, 5).fill(2, 2, 3, 2, '=').fill(2, 0, 3, 0, '=')     # maintenance steps up to the Vestibule's grate
r.fill(1, 39, 5, 40).fill(9, 39, 14, 40).fill(6, 39, 8, 39, '=')   # landings beside the shaft up from the highway
for x0, x1, t in [(18, 23, 36), (3, 7, 30), (1, 6, 25), (16, 20, 19), (13, 17, 13), (14, 18, 7), (2, 10, 4)]:
    r.fill(x0, t, x1, t + 1)                                    # ledges, AC units and balconies
r.fill(25, 30, 30, 31).fill(27, 32, 30, 36, '#').fill(1, 26, 1, 38)
_sp(r, _D('gratehint', 7, 38, down=True), *[_K('phase', x, y, w=w, period=p, on=on, offset=o, look='billboard', id=f'bb{i}')
         for i, (x, y, w, p, on, o) in enumerate([(11, 33, 4, 3.0, [0, 0.62], 0.0), (12, 27, 4, 3.0, [0, 0.62], 0.35), (9, 22, 4, 2.8, [0, 0.6], 0.2),
                                                  (24, 16, 4, 2.8, [0, 0.62], 0.5), (8, 10, 4, 3.0, [0, 0.6], 0.1), (26, 24, 3, 2.4, [0.1, 0.7], 0.7)])],
    _E('nh_drone', 16, 26, air=True), _E('nh_drone', 22, 8, air=True),
    _NH('sign', 20, 35, v=0), _NH('antenna', 4, 29), _NH('vent', 18, 18), _NH('lamp', 3, 24), _NH('sign', 14, 6, v=1),
    _D('windows', 12, 38, rx=1, ry=4, w=30, h=35, grid=1), _D('neonstrip', 18, 35, w=6, c=2), _D('gratehint', 2, 2), _D('cables', 1, 10, x1=30, sag=5))
ROOM('NH11').put(81, 14, 'S')
_n6 = ROOM('NH6')
if all(_n6.g[y][x] == '#' for y in range(13, 16) for x in (13, 14, 15, 16)):
    _n6.fill(14, 14, 15, 15, '.').fill(14, 13, 15, 13, '=')     # a grate in the Null Vestibule's floor
    _sp(_n6, _D('gratehint', 14, 12, down=True))
else:
    print('SC: NH6 floor changed; Billboard grate skipped')

# ---------------------------------------------------------------- NH15 Neon Skyline (vista) — x 1208..1247, y 10..29
r = Room('NH15', 'Neon Skyline', 'neohallow', 1208, 10, 40, 20, **_X3(needs=['talon'], vista=True))
r.fill(0, 0, 0, 19).fill(39, 0, 39, 19).fill(0, 17, 39, 19)
r.open('E', 14, 16)
r.fill(1, 13, 12, 16).fill(1, 12, 3, 12)                        # the raised roof (the bench looks out over the city)
r.fill(20, 15, 25, 16)                                          # a roof hatch housing
_sp(r, _Y('bench', 8, 12, id='bench', view=[20, 7], lore='sc_10', face=1),
    _D('watertower', 30, 16), _NH('antenna', 2, 11), _NH('billboard', 17, 16, v=1), _NH('lamp', 36, 16), _NH('vent', 23, 14),
    _D('railing', 4, 12, w=9), _D('puddles', 13, 16, w=26), _D('skytraffic', 20, 3), _NH('sign', 11, 11, v=2))


# ================================================================================================ THE EMBER
# EXPANSION3 §8 layout (final coordinates): out of the Cinder Well's floor to the east, across the Ashen Expanse, west down the
# Cinder Road beneath Ember's Hollow, and up through the Hollow's floor once the First Ember has gone out (the loop).
#   E5 The Ashen Expanse     524..635  x 19..48   west (high): E1 · west (low): E4 · east: E7 · roof grate: E6
#   E4 The Cinder Road       468..523  x 40..53   east: E5 · roof chimney: E3 (a passage in its floor)
#   E6 The Last Hearth       560..591  x  1..18   floor grate: E5
#   E7 Trial of the First Flame 636..699 x 9..48  west: E5 (built facing east, mirrored at the end of this file)
# (§8.1's Ember zone starts at x 525 / y 41; E5 and E4 use x 524 and y 40, the column and row that meet E1 and E3.)

# ---------------------------------------------------------------- E1 / E3 (anchors)
_e1 = ROOM('E1')
if all(_e1.g[y][23] == '#' for y in (20, 21, 22)):
    _e1.fill(23, 20, 23, 22, '.')                                  # the Cinder Well's floor runs on east, into the ash
else:
    print('SC: E1 east wall changed; the Ashen Expanse entry skipped')
_e3 = ROOM('E3')
if all(_e3.g[y][x] == '#' for y in (11, 12, 13) for x in (35, 36, 37, 38, 39)):
    _e3.fill(36, 11, 38, 13, '.')
    _sp(_e3, _Y('passage', 36, 13, w=3, h=3, id='xs_road', cond={'flag': 'boss:first_ember'}, drift='ember', light='255,150,80', wind=-1))
else:
    print("SC: E3 floor changed; the Cinder Road's way up skipped")

# ---------------------------------------------------------------- E4 The Cinder Road (path), beneath Ember's Hollow
# The last road: burnt-out wayshrines, each a little colder than the one before. It ends under the Hollow, where a chimney
# of old flue-stone climbs to a seam in the Hollow's floor (sealed until the First Ember is gone).
r = Room('E4', 'The Cinder Road', 'ember', 468, 40, 56, 14, **_X3(needs=['talon']), indoor=True, items=['emberstone'], shrine='Shrine of the Last Road')
r.walls().fill(0, 11, 55, 13).fill(0, 0, 55, 1)
r.fill(20, 0, 22, 1, '.').fill(19, 2, 19, 8).fill(23, 2, 23, 8)   # the flue: wall-jump up into the Hollow
r.open('E', 3, 6).fill(44, 7, 55, 13).fill(36, 9, 43, 13)       # the road climbs east to the Expanse
r.fill(8, 10, 12, 10).fill(9, 9, 11, 9)                         # an ash drift
r.fill(28, 2, 28, 8).fill(32, 6, 32, 8).fill(32, 4, 35, 5)      # a split rock hanging from the roof: climb its chimney for the emberstone
r.fill(2, 2, 6, 3).fill(40, 2, 44, 3).fill(47, 2, 49, 2)        # the roof hangs low in places
r.put(34, 3, 'i').put(14, 10, 'S')
for x, y, ch in [(26, 2, 'r'), (38, 2, 'r'), (53, 2, 'r')]:
    r.put(x, y, ch)
_sp(r, _E('ember_acolyte', 30, 10), _E('ember_acolyte', 48, 6),
    _D('deadshrine', 40, 8, n=0), _D('deadshrine', 26, 10, n=1), _D('deadshrine', 6, 10, n=2), _D('ashpile', 10, 8), _D('ashpile', 33, 10),
    _D('embercrack', 42, 8), _D('deadtree', 17, 10), _D('embercrack', 10, 8), _D('embercrack', 52, 6), dict(t='sc_ashes', x=24, y=10),
    _D('ruins', 1, 5), _D('ashfall', 21, 2), _Y('lore', 3, 10, page='sc_11', look='stone'))

# ---------------------------------------------------------------- E5 The Ashen Expanse (grand)
# The field of ash on the way to the Hollow. Low road across the ash; high road along a fallen colonnade; a cracked hearth-
# stone over a hollow full of old embers (Cinder Slam). Landmark: the Cinder Tree, still burning inside.
r = Room('E5', 'The Ashen Expanse', 'ember', 524, 19, 112, 30, **_X3(needs=['talon', 'slam'], grand=True), indoor=True,
         items=['shard', 'emberstone'], shrine='Ashfield Shrine')
r.walls().open('W', 1, 3).open('W', 24, 27).open('E', 25, 27).fill(0, 28, 111, 29)
r.fill(0, 0, 111, 1).fill(50, 0, 52, 1, '.').fill(50, 1, 52, 1, '=')   # a grate in the roof: up to the Last Hearth
r.fill(0, 1, 8, 1, '.')
for x0, x1, y1 in [(14, 16, 2), (22, 27, 4), (33, 36, 2), (40, 43, 3), (58, 62, 2), (68, 74, 4), (78, 80, 2), (92, 97, 3), (103, 108, 2)]:
    r.fill(x0, 2, x1, y1)                                      # the roof sags and drips
r.fill(1, 4, 4, 5)                                             # the ledge you step onto out of the Cinder Well
r.fill(5, 6, 5, 24).fill(8, 3, 8, 24)                          # a basalt flue beside it: down into the ash, wall-jump back up
# the fallen bell tower under the roof grate (climb it to the Last Hearth)
r.fill(46, 25, 48, 27).fill(52, 22, 56, 22).fill(45, 19, 48, 19).fill(52, 16, 56, 16).fill(45, 13, 48, 13).fill(52, 10, 56, 10).fill(45, 7, 48, 7)
r.fill(50, 4, 52, 4, '=').fill(53, 4, 53, 5)
r.fill(44, 6, 44, 24).fill(57, 11, 57, 24).fill(44, 4, 46, 5)      # the tower's walls (the old bell tower lies on its side here)
# the colonnade (high road) east
for x0, x1 in [(58, 63), (67, 72), (76, 80)]:
    r.fill(x0, 10, x1, 11)
r.fill(82, 7, 88, 8).fill(90, 10, 94, 11).fill(81, 4, 89, 4, '=')
# low road: ash dunes, thorn pits, the cracked hearthstone
r.fill(10, 26, 16, 27).fill(12, 25, 14, 25)
r.fill(20, 27, 25, 27, '^')
r.fill(30, 25, 36, 27)
r.fill(60, 27, 66, 27, '^').fill(88, 27, 93, 27, '^')
r.fill(69, 25, 79, 27).fill(70, 26, 78, 27, '.').fill(72, 25, 74, 25, 'Y')
r.put(76, 27, 'i')
r.fill(98, 25, 103, 27).fill(100, 24, 102, 24)
r.put(40, 27, 'i').put(7, 27, 'S')
_sp(r, _D('gratehint', 51, 3), _E('ember_acolyte', 33, 24), _E('dp_magma_crawler', 56, 27), _E('ember_acolyte', 84, 27), _E('dp_magma_crawler', 96, 27),
    _E('gloom_wisp', 70, 14, air=True), _E('ember_acolyte', 69, 9),
    _D('embertree', 42, 27), _D('deadtree', 18, 27), _D('deadtree', 94, 27), _D('ashpile', 3, 27), _D('ashpile', 58, 27), _D('ashpile', 104, 24),
    _D('deadshrine', 106, 27, n=3), _D('embercrack', 64, 26), _D('embercrack', 24, 26), _D('hearthstone', 73, 24),
    dict(t='sc_ashes', x=33, y=24), dict(t='sc_ashes', x=86, y=27), dict(t='sc_cairn', x=100, y=23),
    _D('ashfall', 56, 2), _Y('lore', 62, 9, page='sc_12', look='corpse'),
    _D('embercrack', 17, 27), _D('embercrack', 34, 24), _D('embercrack', 90, 26), _D('embercrack', 52, 27), _D('embercrack', 104, 23),
    dict(t='sc_ashes', x=14, y=24), dict(t='sc_ashes', x=66, y=9), dict(t='sc_ashes', x=99, y=23), _D('deadshrine', 22, 24, n=1), _D('deadshrine', 84, 6, n=0),
    _D('ruins', 11, 9), _D('deadtree', 3, 3), _D('deadtree', 74, 27), _D('ashpile', 27, 27), _D('ashpile', 82, 27), _D('ashpile', 50, 9))

# ---------------------------------------------------------------- E6 The Last Hearth (vista), above the Expanse
r = Room('E6', 'The Last Hearth', 'ember', 560, 1, 32, 18, **_X3(needs=['talon'], vista=True), indoor=True)
r.walls().fill(0, 16, 31, 17).fill(0, 0, 31, 1)
r.fill(14, 16, 16, 17, '.').fill(14, 16, 16, 16, '=')          # the grate down to the Expanse
r.fill(1, 2, 3, 6).fill(1, 7, 2, 9).fill(27, 2, 30, 4).fill(29, 5, 30, 8)
r.fill(18, 15, 27, 15)                                         # the hearth's stone floor
for y in range(4, 12):
    for x in range(5, 12):
        if r.g[y][x] == '.' and not (y == 4 and x in (5, 11)):
            r.put(x, y, '&')                                    # a window onto the ashen field
_sp(r, _Y('bench', 19, 14, id='bench', view=[16, 8], lore='sc_13', face=1), _D('gratehint', 15, 15, down=True),
    _D('hearth', 24, 14), _D('rug', 21, 14), _D('embershelf', 4, 15), _D('ashpile', 12, 15), _D('ashpile', 29, 15),
    _D('hangingpots', 20, 2), dict(t='sc_mat', x=8, y=15), _D('firewood', 28, 14))
for x, y, ch in [(2, 15, 'k'), (10, 15, 'k'), (13, 2, 'r'), (24, 2, 'r')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- E7 Trial of the First Flame — x 565..628, y 44..83
# The hardest trial in the game: every technique, in order, no mistakes. Ember Dash through a veil, Root Hook over the
# thorns, Cinder Slam through the hearthstone, glide the updraft, climb the chimney, triple jump, swing, and burn through
# the last veil to the reliquary.
r = Room('E7', 'Trial of the First Flame', 'ember', 636, 9, 64, 40,
         **_X3(needs=['talon', 'wings', 'hook', 'emberdash', 'gale', 'slam', 'moonstep'], trial=True), indoor=True)
r.walls().open('E', 35, 37).fill(0, 38, 63, 39).fill(0, 0, 63, 1)
r.fill(22, 13, 62, 27)                                          # the heart of the rock (the course winds around it)
r.fill(22, 12, 55, 12, '^')                                     # the high road's floor: thorns
r.fill(52, 28, 52, 37, '%')                                     # veil 1
r.fill(34, 38, 48, 38, '^')                                     # the thorn pit (hook across)
r.put(46, 30, '@').put(39, 30, '@')
r.fill(30, 34, 33, 37)                                          # post (you land here, then leap to the hearthstone)
r.fill(22, 32, 29, 33).fill(24, 32, 26, 33, 'Y')                # the hearthstone: slam through it
r.fill(21, 20, 21, 33)                                          # (no way over it)
r.fill(1, 38, 13, 38, '^')                                      # thorns under the updraft
r.fill(1, 13, 3, 38)                                            # a pillar of basalt (its top is where the updraft leaves you)
r.fill(4, 11, 7, 37, '|')                                       # the updraft: glide into it against the pillar, ride it up
r.fill(9, 14, 12, 15)                                           # B2
r.fill(16, 2, 16, 11).fill(19, 6, 19, 15).fill(16, 14, 19, 15)  # the chimney (you walk in at its foot)
r.fill(19, 4, 25, 5)                                            # C1
r.fill(31, 11, 31, 11, '?').fill(31, 12, 31, 12)                # post P1 (low)
r.fill(38, 4, 38, 11, '?')                                      # post P2 (high: triple jump)
r.put(45, 2, '@')
r.fill(49, 8, 50, 11, '?')                                      # post P3
r.fill(53, 2, 53, 11, '%')                                      # veil 2
r.fill(56, 6, 62, 12)                                           # the reliquary ledge
_sp(r, _Y('trial', 58, 37, id='flame', par=28, reward='c_x3_flame', region='First Flame', name='The Trial of the First Flame'),
    _Y('trial_goal', 60, 5, trial='flame'),
    _D('embercrack', 56, 36), _D('hearthstone', 25, 31), dict(t='sc_ashes', x=60, y=37), _D('ashfall', 30, 2), _D('ashfall', 10, 20))


# ================================================================================================ THE HERMIT'S HOLLOW
# ---------------------------------------------------------------- H1 (anchor): once Oswin has rested, his path opens
_h1 = ROOM('H1')
if all(_h1.g[y][0] == '#' for y in (8, 9, 10)):
    _h1.fill(0, 8, 0, 10, '.')
    _sp(_h1, _Y('passage', 0, 10, w=1, h=3, id='hidden', cond={'flag': 'boss:oswin'}, drift='petal', light='255,220,170', wind=1))
else:
    print('SC: H1 west wall changed; hidden path skipped')

# ---------------------------------------------------------------- H2 The Hidden Path — x -88..-41, y 0..13
# Fog in a cleft of the cliff; cairns and prayer flags show the way over the stepping stones.
r = Room('H2', 'The Hidden Path', 'hermit', -88, 0, 48, 14, **_X3(needs=['start']), indoor=True, items=['emberstone'], shrine='Cairn Shrine')
r.walls().fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.open('E', 8, 10).open('W', 8, 10)
r.fill(16, 11, 30, 12, '.').fill(16, 12, 30, 12, '^')           # the fog-filled cleft (thorns in the dark below)
r.fill(18, 10, 19, 12).fill(23, 9, 24, 12).fill(28, 10, 29, 12)  # stepping stones
r.fill(1, 2, 8, 5).fill(1, 6, 4, 7).fill(38, 2, 46, 4).fill(42, 5, 46, 6)   # the cliff overhangs
r.fill(9, 2, 12, 2).fill(30, 2, 33, 3)
r.fill(34, 8, 37, 8, '=')                                       # a ledge in the fog (the emberstone)
r.put(35, 7, 'i')
for y in range(3, 8):
    for x in range(14, 34):
        if r.g[y][x] == '.' and not (y == 3 and x in (14, 33)) and not (y == 7 and x in (14, 33)):
            r.put(x, y, '&')                                    # the cleft opens on the dusk sky
for x, y, ch in [(11, 10, 'k'), (3, 10, 'b'), (40, 10, 'k'), (13, 2, 'r'), (36, 4, 'r')]:
    r.put(x, y, ch)
r.put(6, 10, 'S')
_sp(r, dict(t='sc_cairn', x=9, y=10), dict(t='sc_cairn', x=33, y=10), dict(t='sc_flags', x=9, y=3, x1=33),
    _E('gloom_wisp', 22, 5, air=True), _E('gloom_wisp', 40, 6, air=True),
    _D('fog', 14, 10, w=18), _D('fog', 1, 10, w=46, thin=True), _D('lantern', 15, 10), _D('lantern', 32, 10), _D('grass', 4, 10), _D('grass', 44, 10),
    _D('pine', 38, 10), _Y('lore', 42, 10, page='sc_14', look='stone', face=-1))

# ---------------------------------------------------------------- H3 The Hermit's Garden (vista) — x -120..-89, y 0..13
r = Room('H3', "The Hermit's Garden", 'hermit', -120, 0, 32, 14, **_X3(needs=['start'], vista=True), indoor=True)
r.walls().fill(0, 11, 31, 13).fill(0, 0, 31, 1).open('E', 8, 10)
r.fill(0, 8, 0, 10, '.').fill(1, 8, 1, 10, 'B')                                        # rotten boards behind the hut: Oswin's stash
r.fill(1, 2, 5, 4).fill(1, 5, 2, 7).fill(26, 2, 30, 3)
for y in range(3, 9):
    for x in range(7, 26):
        if r.g[y][x] == '.' and not (y == 3 and x in (7, 25)):
            r.put(x, y, '&')                                    # the garden opens on the evening sky
_sp(r, _Y('bench', 21, 10, id='bench', view=[15, 5], lore='sc_15', face=-1),
    _D('hut', 7, 10),
    _D('herbs', 12, 10, w=5), _D('chimes', 18, 2), _D('chimes', 25, 4), _D('stonelantern', 27, 10), _D('grass', 17, 10), _D('grass', 29, 10),
    _D('pine', 3, 10), dict(t='sc_flags', x=10, y=2, x1=26))
for x, y, ch in [(24, 10, 'k')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- H4 Oswin's Stash (secret) — x -136..-121, y 0..13
r = Room('H4', "Oswin's Stash", 'hermit', -136, 0, 16, 14, **_X3(needs=['start'], secret=True), indoor=True, chests=['emberstone', 'shard'])
r.walls().fill(0, 11, 15, 13).fill(0, 0, 15, 2).open('E', 8, 10)
r.fill(1, 3, 3, 5).fill(12, 3, 14, 4)
r.put(4, 10, 'C').put(11, 10, 'C')
_sp(r, _D('shelves', 12, 10), _D('jars', 2, 10), _Y('lore', 6, 10, page='sc_16', look='book'), dict(t='sc_mat', x=9, y=10))
for x, y, ch in [(14, 10, 'k'), (1, 10, 'k'), (7, 3, 'x')]:
    r.put(x, y, ch)


# ================================================================================================ finishing passes
def _deglass(r):
    """star-glass reads best as thin edges: glass masses (not 1-wide columns) become the crater's black-glass rock"""
    G = [row[:] for row in r.g]
    for y in range(r.h):
        for x in range(r.w):
            if G[y][x] != '?': continue
            thin = (x == 0 or G[y][x - 1] != '?') and (x == r.w - 1 or G[y][x + 1] != '?')
            if not thin: r.g[y][x] = '#'


for _rid in ('SF10', 'SF11', 'SF12', 'SF13', 'SF14', 'SF15', 'SF16', 'SF17', 'SF19'):
    _deglass(ROOM(_rid))

# more of the crater's own furniture: floating shards over the plains, crystal spires, cooled meteors, glass grass
_sp(ROOM('E7'), _D('embercrack', 40, 37), _D('embercrack', 24, 31), _D('embercrack', 60, 5), dict(t='sc_ashes', x=10, y=13), dict(t='sc_ashes', x=22, y=3),
    _D('embercrack', 48, 37), _D('ruins', 1, 2))


def _rind(r):
    """keep star-glass only as a rind on faces the player can touch (no-cling stays where it matters); the core is rock"""
    G = [row[:] for row in r.g]
    for y in range(r.h):
        for x in range(r.w):
            if G[y][x] != '?': continue
            if all(0 <= x + dx < r.w and 0 <= y + dy < r.h and G[y + dy][x + dx] in '?#' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                r.g[y][x] = '#'


_rind(ROOM('SF18'))


# ================================================================================================ §8 finishing: mirrored rooms, the Sky Stair
_SLAB_W = {'mover': 3, 'lift': 3, 'crumble': 2, 'sinker': 2, 'phase': 2}


def _mirror(r):
    """flip a room east-west (grid and spawns): E7 was built facing east and now opens west onto the Ashen Expanse"""
    for row in r.g:
        row.reverse()
    for s in r.kw.get('spawns', []):
        w = int(s.get('w', _SLAB_W.get(s.get('kind'), 1))) if s.get('t') == 'kit' and s.get('kind') in _SLAB_W else 1
        s['x'] = r.w - s['x'] - w
        if 'face' in s: s['face'] = -s['face']
        if 'view' in s: s['view'] = [r.w - 1 - s['view'][0], s['view'][1]]


_mirror(ROOM('E7'))


# W6 The Sky Stair (X4 -> SF1), generated by tools/rooms.py after the region modules: dress it as a starfall stair
def _sc_dress_w6():
    try:
        r = ROOM('W6')
    except StopIteration:
        return
    r.kw['spawns'] = r.kw.get('spawns', []) + [
        _SF('shard', 4, 10), _SF('shard', r.w - 5, 26), _SF('shard', 5, 44), _SF('shard', r.w - 6, 58), _D('reflect', 10, 30),
        _D('meteorfall', r.w // 2, 2)]
    for y in range(4, r.h - 4, 9):                                  # starlight pools every few ledges: the stair floats
        _star(r, 2, y, r.w - 3, y + 2)


POST_LINKS = globals().get('POST_LINKS', [])
POST_LINKS.append(_sc_dress_w6)

