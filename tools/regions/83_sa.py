# ============================================================ EXPANSION 3 — agent SA: Thornveil Wood, Drowned Barrows, Crimson Manor
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, free_spot). Engine: web/src/53_sa.js.
# Art: art/gen_xsa*.py -> assets/xsa_*. Every module-level name here is prefixed _sa.
#
# Custom spawns (53_sa.js): xsa, kind = prop | skins | frontpaint | flies | motes | shaft | bubbles | pearls | petals | leak |
#   sign | seal | rite | tide | floodgates | trialgate | gaze | bookcase | keygate | glasshouse | piano | reachhelp
#   prop      : decor sprite from the xsa_* sheets (sheet, tag), back=True paints it into the room's back layer
#   skins     : repaints solid cells of the front layer (bark trunks, leaf canopy, roof slates, glass) — _sa_skins()
#   seal      : a one-way shortcut: the sys door `door` in this room stays sealed until you arrive through it from its partner
#   reachhelp : see _sa_swim(): stand-ins that tell tools/reach.py where the player can swim (removed at runtime)
# Wings (docs/EXPANSION3_CONTRACT.md §7.3):
#   Thornveil: TV3 (door by the Briarheart Shrine) -> TV10 -> TV9 -> TV11 -> door -> TV6 (sealed until you come out)
#   Barrows:   DB3 (door by the Tidewater Shrine) -> DB11 -> DB12 -> DB10 -> door -> DB1 (sealed until you come out)
#   Crimson:   CM4 (the east window, a door) -> CM12 -> (tower door) CM10 -> CM9 -> CM5 (gate, opened from the East Wing side)
#              CM3 (servants' door) <-> CM11 <-> CM10 (second wing; the Foyer door is sealed until you come out)


def _sa_paint(r, rows, x0=0, y0=0):
    for y, row in enumerate(rows):
        if x0 == 0 and len(row) != r.w: print(f'SA PAINT {r.id} row {y0 + y}: {len(row)} cols, want {r.w}')
        for x, ch in enumerate(row):
            if ch != ' ':
                r.g[y0 + y][x0 + x] = ch
    return r


def _sa_prop(tag, x, y, sheet='xsa_tv', **kw):
    return dict(t='xsa', kind='prop', sheet=sheet, tag=tag, x=x, y=y, **kw)


def _sa_skins(r, *rects):
    """repaint solid cells of the front layer (bark, leaves, slates, glass...). The spawn sits in any open cell."""
    x, y = next((x, y) for y in range(r.h) for x in range(r.w) if r.g[y][x] == '.')
    r.kw.setdefault('spawns', []).append(dict(t='xsa', kind='skins', x=x, y=y, list=[list(q) for q in rects]))


def _sa_swim(r, *rects):
    """tools/reach.py has no swimming model yet (NEEDS in the report). Until it does, each deep-water area the player swims
    through is described to the checker as a strong updraft (it rides those like a ladder); 53_sa.js removes these helper
    winds the moment the room is built, so they never exist in play. rects: (x0, y0, x1, y1) inclusive."""
    sp = r.kw.setdefault('spawns', []); ids = []
    for i, (x0, y0, x1, y1) in enumerate(rects):
        rid = f'swimhelp{i}'; ids.append(rid)
        sp.append(dict(t='kit', kind='wind', x=x0, y=y0, w=x1 - x0 + 1, h=y1 - y0 + 1, vy=-200, id=rid, period=9, on=[0.0, 0.0]))
    x, y = next((x, y) for y in range(r.h) for x in range(r.w) if r.g[y][x] == '.')
    sp.append(dict(t='xsa', kind='reachhelp', x=x, y=y, ids=ids))


def _sa_k(kind, x, y, **kw):
    return dict(t='kit', kind=kind, x=x, y=y, **kw)


def _sa_s(kind, x, y, **kw):
    return dict(t='sys', kind=kind, x=x, y=y, **kw)


def _sa_en(type_, x, y, **kw):
    return dict(t='enemy', type=type_, x=x, y=y, **kw)


def _sa_pt(x, y, subj, **kw):
    return dict(t='cm_portrait', x=x, y=y, subj=subj, **kw)


def _sa_tv(kind, x, y, **kw):
    return dict(t='tv_prop', kind=kind, x=x, y=y, **kw)


def _sa_db(kind, x, y, **kw):
    return dict(t='db_prop', kind=kind, x=x, y=y, **kw)


def _sa_cm(kind, x, y, **kw):
    return dict(t='cm_prop', kind=kind, x=x, y=y, **kw)


# ============================================================================================ THORNVEIL WOOD
# Zone x -330..-141, y -120..42 (west of everything). Door-linked from TV3 / TV6.
#   TV9  The Elder Canopy   -312..-201 x -58..-27   grand: three levels between giant trunks, the Elder in the middle
#   TV10 The Hunter's Trail -200..-145 x -40..-27   path: snares and skulls; the door from TV3 at its east end
#   TV11 Under the Roots    -312..-265 x -26..-13   path: fungus-lit tunnels; the door out to TV6 at its west end
#   TV12 Vine Swing         -312..-249 x -78..-59   parkour: vines over a thorn pit, up from the canopy's west ladder
#   TV13 The Coven Circle   -200..-161 x -26..-11   gauntlet: the standing stones, under the trail
#   TV14 Mossbed Glade      -248..-213 x -76..-59   vista: the bench under the Mother Oak; drops back into the canopy
#   TV15 Bramble Sprint     -264..-209 x -26..-7    trial: a pogo run over the brambles (c_x3_thorn)
#   TV16 Witch's Larder     -160..-145 x -26..-13   secret: behind a thorn curtain the Ember Dash burns through

# ---------------------------------------------------------------- TV9 The Elder Canopy (grand)
_sa_sp = [
    # the forest floor: giant trees painted behind, ferns and fungus in front
    _sa_tv('tree', 10, 27, back=True, v=1), _sa_tv('tree', 26, 27, back=True, v=2), _sa_tv('tree', 44, 27, back=True),
    _sa_tv('tree', 73, 27, back=True, v=1), _sa_tv('tree', 88, 27, back=True, v=2), _sa_tv('tree', 108, 27, back=True),
    _sa_prop('elder', 56, 27, sheet='xsa_elder', back=True),                     # the Elder: a vast trunk painted behind its solid core
    _sa_prop('rootarch', 13, 27, sheet='xsa_tvbig', back=True), _sa_prop('rootarch', 33, 27, sheet='xsa_tvbig', back=True), _sa_prop('rootarch', 77, 27, sheet='xsa_tvbig', back=True),
    _sa_prop('rootarch', 95, 27, sheet='xsa_tvbig', back=True),
    _sa_tv('fern', 4, 25), _sa_tv('fern', 23, 27), _sa_tv('fern', 38, 27), _sa_tv('fern', 64, 24), _sa_tv('fern', 86, 27),
    _sa_tv('fern', 99, 27), _sa_tv('shroom', 18, 25), _sa_tv('shroom', 55, 27), _sa_tv('shroom', 72, 24), _sa_tv('shroom', 107, 18),
    _sa_tv('shroom', 22, 10), _sa_tv('shroom', 90, 10), _sa_tv('ribbons', 49, 18), _sa_tv('idol', 62, 18, v=1),
    _sa_tv('vine', 26, 2), _sa_tv('vine', 43, 2), _sa_tv('vine', 69, 2), _sa_tv('vine', 86, 2), _sa_tv('vine', 103, 2),
    _sa_prop('fungus', 57, 27), _sa_prop('fungus', 29, 27), _sa_prop('fungus', 99, 27), _sa_prop('skullpost', 103, 27),
    _sa_prop('nest', 70, 10), _sa_prop('mossrock', 45, 27), _sa_prop('mossrock', 81, 27),
    _sa_prop('rootcurtain', 21, 2), _sa_prop('rootcurtain', 47, 2), _sa_prop('rootcurtain', 83, 2), _sa_prop('rootcurtain', 101, 2),
    _sa_prop('fungus', 44, 18), _sa_prop('fungus', 88, 19), _sa_prop('fungus', 104, 18), _sa_prop('nest', 24, 10), _sa_prop('antlers', 36, 27),
    _sa_tv('shroom', 64, 10), _sa_tv('shroom', 84, 10), _sa_tv('fern', 40, 18), _sa_tv('fern', 67, 18), _sa_tv('ribbons', 100, 18),
    _sa_prop('mossbank', 5, 25), _sa_prop('stones', 92, 27),
    dict(t='xsa', kind='flies', x=60, y=19, w=40, h=14, n=16),
    dict(t='xsa', kind='motes', x=46, y=15, w=108, h=26, n=26),
    dict(t='tv_fog', x=2, y=20, w=24, h=8), dict(t='tv_pod', x=40, y=2), dict(t='tv_pod', x=82, y=2),
    # vines to swing across the high gaps (grab by touch)
    _sa_k('swing', 71, 2, len=6, rope='vine', amp=20), _sa_k('swing', 86, 2, len=7, rope='vine', amp=20),
    # a wandering thornveil host
    _sa_en('tv_hound', 92, 27), _sa_en('tv_husk', 20, 18), _sa_en('tv_husk', 74, 27), _sa_en('tv_wisp', 64, 6, air=True),
    _sa_en('tv_wisp', 20, 15, air=True),
    _sa_s('lore', 55, 27, page='sa_2', look='none'),           # the Elder's heart (the hollow)
]
_sa_r = Room('TV9', 'The Elder Canopy', 'thornveil', -312, -58, 112, 32, indoor=True, needs=['talon'], x3=True, grand=True,
             items=['emberstone', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 111, 1).fill(0, 0, 1, 31).fill(110, 0, 111, 31).fill(0, 28, 111, 31)
_sa_r.fill(110, 24, 111, 27, '.')                       # -> the Hunter's Trail (east)
_sa_r.fill(4, 0, 6, 1, '.').fill(4, 1, 6, 1, '=')       # the west chimney up into the Vine Swing
_sa_r.fill(24, 28, 26, 31, '.')                         # the root shaft down to Under the Roots
_sa_r.fill(100, 28, 102, 31, '.')                       # the root shaft down to the Bramble Sprint's goal nook
_sa_r.fill(90, 0, 91, 1, '.')                           # the moss-choked drop from Mossbed Glade
# forest floor: root mounds, a bramble dip before the Elder
_sa_r.fill(2, 26, 8, 27).fill(18, 26, 21, 27).fill(64, 25, 71, 27).fill(62, 26, 63, 27).fill(104, 26, 107, 27)
_sa_r.fill(40, 27, 50, 27, '(')
_sa_r.fill(84, 27, 88, 27, '(')
# trunks (the bark skin repaints them); the low route passes under their root arches
_sa_r.fill(12, 2, 14, 22).fill(32, 2, 34, 21).fill(76, 2, 78, 22).fill(94, 2, 96, 22)
# the Elder: solid heartwood with a hollow at its roots (thorn curtains either side) and a branch hole through it
_sa_r.fill(52, 2, 59, 27)
_sa_r.fill(53, 22, 58, 27, '.').fill(52, 22, 52, 27, ')').fill(59, 22, 59, 27, ')').fill(52, 22, 59, 22)
_sa_r.fill(52, 8, 59, 10, '.')
# mid walkways (platform row 19/20) and high walkways (row 11/12)
for _x0, _x1, _y in [(15, 24, 19), (35, 47, 19), (60, 70, 19), (79, 90, 20), (97, 107, 19),
                     (2, 11, 11), (15, 30, 11), (35, 51, 11), (60, 75, 11), (79, 93, 11), (97, 107, 12)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
# the ladders between the levels: branch stubs three rows apart
for _x0, _x1, _y in [(9, 11, 24), (8, 10, 21), (2, 5, 17), (6, 9, 14),       # west ladder -> high west walkway
                     (2, 7, 8), (2, 6, 4),                                     # up to the chimney
                     (27, 30, 24), (23, 26, 22),                               # onto the mid walkway (west)
                     (36, 38, 23), (44, 47, 23),                               # mid walkway (Elder west)
                     (21, 23, 16), (26, 28, 14),                               # mid -> high (west)
                     (40, 42, 15), (46, 49, 16),                               # mid -> high (Elder)
                     (61, 63, 23), (66, 68, 15), (72, 74, 22),                 # east of the Elder
                     (82, 84, 24), (86, 89, 17), (91, 93, 14), (99, 101, 23), (104, 107, 16),
                     (60, 62, 6), (64, 67, 4)]:                                # the crown of the Elder (emberstone)
    _sa_r.fill(_x0, _y, _x1, _y, '=')
_sa_r.fill(52, 7, 59, 7)                                # heartwood above the branch hole
for _x, _y, _ch in [(65, 3, 'i'), (19, 10, 'r'), (43, 18, 'r'), (84, 10, 'r'), (104, 11, 'r'), (9, 23, 'b'), (73, 24, 'k')]:
    _sa_r.put(_x, _y, _ch)
_sa_r.put(57, 27, 'i')                                  # gold in the hollow, beside the Elder's heart
_sa_skins(_sa_r, ('leaves', 0, 0, 112, 2), ('bark', 12, 2, 3, 21), ('bark', 32, 2, 3, 20), ('elder', 52, 2, 8, 26),
          ('bark', 76, 2, 3, 21), ('bark', 94, 2, 3, 21))
_sa_r.kw['reach_open'] = [(52, _y) for _y in range(23, 28)] + [(59, _y) for _y in range(23, 28)]

# ---------------------------------------------------------------- TV10 The Hunter's Trail (path; the way in from TV3)
_sa_r = Room('TV10', 'The Hunter\'s Trail', 'thornveil', -200, -40, 56, 14, indoor=True, needs=['talon'], x3=True,
             spawns=[_sa_s('door', 51, 9, id='tv_in', to='TV3', toId='tv_in', look='arch'),
                     _sa_tv('tree', 8, 9, back=True, v=2), _sa_tv('tree', 30, 9, back=True, v=1), _sa_tv('tree', 47, 9, back=True),
                     _sa_prop('snare', 14, 9), _sa_prop('snare', 25, 9), _sa_prop('snare', 42, 9),
                     _sa_prop('skullpost', 6, 9), _sa_prop('skullpost', 20, 6), _sa_prop('skullpost', 48, 9), _sa_prop('hide', 30, 5),
                     _sa_prop('antlers', 38, 9), _sa_prop('mossrock', 11, 9), _sa_tv('fern', 3, 9), _sa_tv('fern', 45, 9), _sa_tv('fern', 22, 9),
                     _sa_tv('shroom', 53, 5), _sa_tv('ribbons', 33, 9), _sa_tv('vine', 17, 1), _sa_tv('vine', 40, 1),
                     dict(t='xsa', kind='motes', x=28, y=5, w=54, h=9, n=10), dict(t='xsa', kind='flies', x=30, y=6, w=20, h=6, n=6),
                     _sa_en('tv_hound', 18, 9), _sa_en('tv_husk', 40, 9), _sa_en('tv_wisp', 28, 3, air=True)])
_sa_paint(_sa_r, [
    #0         1         2         3         4         5
    #01234567890123456789012345678901234567890123456789012345
    "########################################################",  # 0
    "#......................................................#",  # 1
    "#......................................................#",  # 2
    "#......................................................#",  # 3
    "#..................................................=====",  # 4   a hunter's shelf over the door
    "#.................####.....=======.....................#",  # 5   the blind (hide) on a bough
    "......................................................##",  # 6   <- the Canopy (west, rows 6..9)
    "..........................................=====.......##",  # 7
    "..............===......................................#",  # 8
    "........................................................",  # 9
    "##################################...###################",  # 10  the pit down to the Coven Circle (cols 34..36)
    "##################################...###################",  # 11
    "##################################...###################",  # 12
    "##################################...###################",  # 13
])
_sa_r.fill(55, 4, 55, 9)                                # east wall; the door stands at the trail's end
for _x, _y, _ch in [(12, 1, 'r'), (36, 1, 'x'), (50, 1, 'r'), (53, 3, 'k'), (8, 9, 'b')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV11 Under the Roots (path; the way out to TV6)
_sa_r = Room('TV11', 'Under the Roots', 'thornveil', -312, -26, 48, 14, indoor=True, needs=['talon'], x3=True,
             spawns=[_sa_s('door', 2, 10, id='tv_out', to='TV6', toId='tv_out', look='crack'),
                     _sa_prop('fungus', 6, 10), _sa_prop('fungus', 19, 10), _sa_prop('fungus', 31, 7), _sa_prop('fungus', 44, 10),
                     _sa_prop('rootcurtain', 11, 3), _sa_prop('rootcurtain', 38, 2), _sa_prop('rootcurtain', 29, 2),
                     _sa_tv('shroom', 9, 10), _sa_tv('shroom', 29, 10), _sa_tv('shroom', 41, 10), _sa_tv('shroom', 15, 4),
                     _sa_tv('fern', 13, 10), _sa_tv('fern', 45, 10), _sa_prop('skullpost', 4, 10),
                     _sa_prop('antlers', 23, 10), _sa_prop('mossrock', 41, 10), _sa_prop('fungus', 35, 7),
                     dict(t='xsa', kind='motes', x=24, y=6, w=46, h=9, n=14, col='120,255,170'),
                     _sa_en('tv_husk', 33, 7), _sa_en('tv_wisp', 16, 5, air=True),
                     _sa_s('lore', 7, 10, page='sa_3', look='corpse')])
_sa_r.fill(0, 0, 47, 1).fill(0, 0, 0, 13).fill(47, 0, 47, 13).fill(0, 11, 47, 13)
_sa_r.fill(47, 7, 47, 10, '.')                                   # -> Bramble Sprint (east, rows 7..10)
_sa_r.fill(1, 2, 4, 3).fill(9, 2, 13, 2).fill(32, 2, 35, 2).fill(40, 2, 46, 3).fill(1, 4, 2, 4)   # hanging root-masses
_sa_r.fill(23, 1, 23, 7).fill(27, 1, 27, 7).fill(24, 0, 26, 7, '.')     # the wall-jump chimney up to the Canopy
_sa_r.fill(22, 8, 28, 8, '=').fill(12, 5, 15, 5, '=')            # a root ledge under the shaft; a shelf of fungus
_sa_r.fill(33, 8, 37, 10)                                        # a knot of roots across the tunnel (jump it)
_sa_r.fill(14, 10, 17, 10, '(')                                  # brambles in the dip
for _x, _y, _ch in [(6, 3, 'r'), (16, 2, 'r'), (31, 4, 'r'), (43, 3, 'r'), (20, 10, 'b')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV12 Vine Swing (parkour)
_sa_sp = [_sa_tv('tree', 3, 15, back=True, v=1), _sa_tv('tree', 33, 15, back=True, v=2), _sa_tv('tree', 60, 15, back=True),
          _sa_prop('thornbed', 20, 16), _sa_prop('thornbed', 44, 16),
          _sa_tv('fern', 9, 15), _sa_tv('fern', 57, 15), _sa_tv('shroom', 2, 15), _sa_tv('shroom', 28, 10), _sa_prop('nest', 43, 6),
          _sa_prop('fungus', 58, 15), _sa_prop('rootcurtain', 18, 2), _sa_prop('rootcurtain', 38, 2), _sa_prop('rootcurtain', 50, 2), _sa_prop('skullpost', 5, 15),
          dict(t='xsa', kind='motes', x=32, y=9, w=60, h=14, n=16), dict(t='xsa', kind='flies', x=34, y=8, w=20, h=8, n=6),
          dict(t='tv_fog', x=10, y=13, w=46, h=5),
          _sa_en('tv_wisp', 36, 5, air=True)]
for _i, (_x, _ln) in enumerate([(14, 9), (21, 9), (34, 8), (41, 9), (49, 9)]):
    _sa_sp.append(_sa_k('swing', _x, 2, len=_ln, rope='vine', amp=24, period=2.6, phase=_i * 0.3))
_sa_sp += [_sa_k('crumble', 36, 12, w=2, delay=0.45, respawn=2.5)]
_sa_r = Room('TV12', 'Vine Swing', 'thornveil', -312, -78, 64, 20, indoor=True, needs=['talon'], x3=True, parkour=True,
             items=['seed'], spawns=_sa_sp)
_sa_r.fill(0, 0, 63, 1).fill(0, 0, 1, 19).fill(62, 0, 63, 19).fill(0, 16, 63, 19)
_sa_r.fill(62, 12, 63, 15, '.')                                  # -> Mossbed Glade (east, rows 12..15)
_sa_r.fill(4, 16, 6, 19, '.').fill(3, 16, 3, 19).fill(7, 16, 7, 19)
_sa_r.fill(4, 16, 6, 16, '=').fill(4, 18, 6, 18, '=')           # the chimney up from the Canopy
_sa_r.fill(11, 16, 55, 17, '.').fill(11, 17, 55, 17, '^')        # the thorn pit
_sa_r.fill(27, 11, 28, 17)                                       # a mossy stump halfway (rest)
_sa_r.fill(11, 2, 13, 2, 'v').fill(30, 2, 32, 2, 'v').fill(53, 2, 56, 2, 'v')   # thorn-hung boughs: don't swing too high
_sa_r.fill(44, 5, 46, 5, '=')                                    # a high nest (seed): release a vine at the top of its arc
for _x, _y, _ch in [(45, 4, 'i'), (8, 2, 'r'), (25, 2, 'x'), (46, 2, 'r'), (59, 2, 'r'), (58, 15, 'k')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('leaves', 0, 0, 64, 2), ('bark', 27, 11, 2, 6))

# ---------------------------------------------------------------- TV14 Mossbed Glade (vista)
_sa_r = Room('TV14', 'Mossbed Glade', 'thornveil', -248, -76, 36, 18, indoor=True, needs=['talon'], x3=True, vista=True,
             spawns=[_sa_prop('motheroak', 17, 13, sheet='xsa_oak', back=True),
                     _sa_tv('tree', 3, 13, back=True, v=2), _sa_tv('tree', 29, 13, back=True, v=1),
                     _sa_s('bench', 12, 13, id='bench', view=[17, 7], lore='sa_1'),
                     _sa_prop('mossbank', 6, 13), _sa_prop('mossbank', 27, 13), _sa_prop('stones', 22, 13),
                     _sa_tv('fern', 2, 13), _sa_tv('fern', 9, 13), _sa_tv('fern', 30, 13), _sa_tv('shroom', 15, 13), _sa_tv('shroom', 20, 13),
                     _sa_tv('shroom', 33, 9), _sa_tv('ribbons', 24, 13), _sa_tv('idol', 29, 13, v=1),
                     dict(t='xsa', kind='flies', x=18, y=8, w=32, h=10, n=40, col='190,255,150'),
                     dict(t='xsa', kind='shaft', x=20, y=8, w=6, h=12, col='200,255,200', a=0.1),
                     dict(t='xsa', kind='shaft', x=7, y=8, w=3, h=12, col='200,255,200', a=0.07),
                     dict(t='xsa', kind='motes', x=18, y=8, w=32, h=12, n=16, col='220,255,200')])
_sa_r.fill(0, 0, 35, 1).fill(0, 0, 0, 17).fill(35, 0, 35, 17).fill(0, 14, 35, 17)
_sa_r.fill(0, 10, 0, 13, '.')                                   # <- Vine Swing (west, rows 10..13)
_sa_r.fill(26, 14, 27, 17, '.')                                 # a moss-choked drop back into the Canopy
_sa_r.fill(31, 12, 34, 13).fill(32, 10, 34, 11)               # a mossy bank against the east wall
for _x, _y, _ch in [(10, 2, 'r'), (25, 2, 'r'), (4, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('leaves', 0, 0, 36, 2))

# ---------------------------------------------------------------- TV13 The Coven Circle (gauntlet)
_sa_W = [[dict(type='tv_hound', x=6, y=12), dict(type='tv_hound', x=24, y=12)],
         [dict(type='tv_husk', x=5, y=12), dict(type='tv_husk', x=26, y=12), dict(type='tv_wisp', x=15, y=5)],
         [dict(type='tv_hound', x=4, y=12), dict(type='tv_husk', x=25, y=12), dict(type='tv_wisp', x=8, y=4), dict(type='tv_wisp', x=22, y=4)],
         [dict(type='xsa_elder_husk', x=15, y=12)]]
_sa_r = Room('TV13', 'The Coven Circle', 'thornveil', -200, -26, 40, 16, indoor=True, needs=['talon'], x3=True, gauntlet=True,
             spawns=[_sa_k('gate', 31, 12, id='gc', open=True),
                     _sa_s('gauntlet', 15, 12, id='coven', look='stones', name='The Coven Circle', gates=['gc'], waves=_sa_W,
                           reward=['emberstone', 'gold']),
                     dict(t='xsa', kind='rite', x=1, y=12, w=30, gauntlet='coven'),
                     _sa_prop('stone_l', 5, 12), _sa_prop('stone_s', 10, 12), _sa_prop('stone_s', 20, 12), _sa_prop('stone_l', 25, 12),
                     _sa_prop('cauldron', 35, 12), _sa_prop('thorncurtain', 39, 12),
                     _sa_tv('idol', 2, 12, v=1), _sa_tv('idol', 28, 12), _sa_tv('ribbons', 13, 12), _sa_tv('ribbons', 18, 12),
                     _sa_tv('tree', 8, 12, back=True, v=2), _sa_tv('tree', 23, 12, back=True, v=1), _sa_tv('shroom', 33, 12),
                     dict(t='xsa', kind='motes', x=16, y=6, w=30, h=11, n=12, col='150,255,190')])
_sa_paint(_sa_r, [
    #0         1         2         3
    #0123456789012345678901234567890123456789
    "##################################...###",  # 0   <- the pit from the Hunter's Trail (cols 34..36)
    "#.............................####...###",  # 1
    "#.............................####...###",  # 2
    "#.............................####...###",  # 3
    "#.............................####...###",  # 4
    "#..............................#.......#",  # 5
    "#..............................#.......#",  # 6
    "#......====..........====......#.....==#",  # 7
    "#......................................#",  # 8   (gate cells rows 8..12, col 31)
    "#......................................%",  # 9
    "#...............................==.....%",  # 10
    "#......................................%",  # 11
    "#......................................%",  # 12
    "########################################",  # 13
    "########################################",  # 14
    "########################################",  # 15
])
_sa_r.fill(31, 5, 31, 7)                                        # the arch over the gate (it reaches this)
for _x, _y, _ch in [(6, 1, 'r'), (15, 1, 'x'), (24, 1, 'r'), (38, 5, 'k')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV16 The Witch's Larder (secret; Ember Dash through the thorn curtain)
_sa_r = Room('TV16', 'The Witch\'s Larder', 'thornveil', -160, -26, 16, 14, indoor=True, needs=['talon', 'emberdash'], x3=True, secret=True,
             chests=['shard'],
             spawns=[_sa_prop('shelves', 5, 12), _sa_prop('shelves', 11, 12), _sa_prop('herbs', 5, 2), _sa_prop('herbs', 9, 2), _sa_prop('herbs', 12, 2),
                     _sa_prop('cauldron', 8, 12), _sa_tv('shroom', 14, 12), _sa_tv('shroom', 2, 12),
                     _sa_s('lore', 3, 12, page='sa_4', look='book'),
                     dict(t='xsa', kind='motes', x=8, y=6, w=14, h=11, n=8, col='255,190,120')])
_sa_r.walls().fill(0, 9, 0, 12, '.').fill(0, 13, 15, 13)
_sa_r.fill(1, 1, 15, 3).fill(4, 1, 13, 3, '.').fill(4, 1, 13, 1)
for _x, _y, _ch in [(12, 12, 'C'), (6, 4, 'k'), (10, 4, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV15 Bramble Sprint (trial: a pogo run; c_x3_thorn)
# Start on the ledge by the west door; walk off (don't jump: the thorn ceiling), pogo across the first bramble field,
# hop the crumbling boughs under the low thorns, pogo up the bramble-crowned stumps under the thorn bough, land on
# the goal bough. The goal nook climbs out into the Canopy (leaving the room ends a trial, so it can't be skipped).
_sa_sp = [_sa_s('trial', 3, 10, id='sprint', par=9, reward='c_x3_thorn', region='Thornveil', name='Bramble Sprint'),
          _sa_s('trial_goal', 49, 6, trial='sprint'),
          _sa_tv('tree', 10, 15, back=True, v=1), _sa_tv('tree', 27, 15, back=True), _sa_tv('tree', 45, 5, back=True, v=2),
          _sa_tv('shroom', 5, 10), _sa_tv('fern', 1, 10), _sa_tv('shroom', 53, 6), _sa_tv('fern', 46, 6),
          dict(t='xsa', kind='motes', x=28, y=9, w=54, h=14, n=16),
          _sa_k('crumble', 22, 12, w=2, delay=0.35, respawn=2.5), _sa_k('crumble', 26, 12, w=2, delay=0.35, respawn=2.5),
          _sa_k('crumble', 30, 12, w=2, delay=0.35, respawn=2.5),
          ]
_sa_r = Room('TV15', 'Bramble Sprint', 'thornveil', -264, -26, 56, 20, indoor=True, needs=['talon'], x3=True, trial=True, spawns=_sa_sp)
_sa_r.fill(0, 0, 55, 1).fill(0, 0, 0, 19).fill(55, 0, 55, 19).fill(0, 16, 55, 19)
_sa_r.fill(0, 7, 0, 10, '.')                                     # <- Under the Roots (west, rows 7..10)
_sa_r.fill(0, 11, 6, 15)                                         # the start ledge
_sa_r.fill(7, 15, 43, 15, '(')                                   # the bramble floor
_sa_r.fill(9, 9, 16, 9, 'v').fill(22, 7, 31, 7, 'v')             # thorn-hung boughs: walk off the ledge, hop low
_sa_r.fill(19, 12, 20, 15)                                       # a bare stump to catch your breath
_sa_r.fill(32, 12, 33, 15).fill(32, 11, 33, 11, '(')             # bramble-crowned stumps: pogo up them
_sa_r.fill(36, 10, 37, 15).fill(36, 9, 37, 9, '(')
_sa_r.fill(40, 10, 41, 15).fill(40, 9, 41, 9, '(')
_sa_r.fill(35, 3, 42, 3, 'v')                                     # a thorn bough over the crowned stumps: pogo no higher than you must
_sa_r.fill(44, 7, 55, 15)                                        # the goal bough
_sa_r.fill(52, 0, 54, 6, '.').fill(51, 0, 51, 4)                 # the root shaft up into the Canopy
_sa_skins(_sa_r, ('leaves', 0, 0, 52, 2), ('bark', 19, 12, 2, 4), ('bark', 32, 12, 2, 4), ('bark', 36, 10, 2, 6), ('bark', 40, 10, 2, 6))

# ---------------------------------------------------------------- Thornveil anchors (old rooms: door spawns only)
ROOM('TV3').kw.setdefault('spawns', []).extend([
    _sa_s('door', 17, 10, id='tv_in', to='TV10', toId='tv_in', look='arch'),     # a hollow in a great trunk by the Briarheart Shrine
    dict(t='xsa', kind='sign', x=17, y=10, text='A hunters\' track runs west into the deep wood.')])
ROOM('TV6').kw.setdefault('spawns', []).extend([
    _sa_s('door', 8, 9, id='tv_out', to='TV11', toId='tv_out', look='crack'),
    dict(t='xsa', kind='seal', x=8, y=9, door='tv_out', look='roots',
         msg='Roots have grown shut over a crack in the rock. Something on the far side holds them.')])


# ============================================================================================ THE DROWNED BARROWS
# Zone x 585..760, y 84..220 (a door-linked pocket far east). Door-linked from DB3 / DB1.
#   DB11 Grave Causeway      600..647 x 100..113   path: a causeway through black water between burial mounds; door from DB3
#   DB12 Tomb Galleries      648..695 x  98..113   path: two tiers of sealed tombs, some leaking; the floor gives way into the Nave
#   DB10 The Sunken Nave     600..695 x 114..153   grand: the first nave, drowned. Dry route along the rafters, swim route below
#   DB13 Tide Steps          696..743 x 114..137   parkour: the tide rises and falls; float up the steps at high water
#   DB17 The Drowned Bell    712..727 x 138..151   secret: under the sealed well in the Tide Steps' floor
#   DB14 The Floodgates      600..639 x 154..177   puzzle: three wheels, three basins; a wheel won't turn under water
#   DB15 Pearl Lagoon        640..679 x 154..173   vista: light through clear water, drifting pearls, the bench on the grotto shelf
#   DB16 Breathless Dive     680..743 x 154..177   trial: one breath, end to end (c_x3_lung)
_SA_WL = '"'

# ---------------------------------------------------------------- DB11 Grave Causeway (path; the way in from DB3)
_sa_r = Room('DB11', 'Grave Causeway', 'barrows', 600, 100, 48, 14, indoor=True, needs=['talon'], x3=True, items=['gold'],
             spawns=[_sa_s('door', 3, 10, id='db_in', to='DB3', toId='db_in', look='arch'),
                     _sa_db('lamp', 7, 10), _sa_db('lamp', 27, 7), _sa_db('lamp', 45, 10), _sa_db('bones', 12, 10), _sa_db('statue', 40, 3),
                     _sa_prop('gravecross', 18, 7, sheet='xsa_db'), _sa_prop('gravestone', 16, 7, sheet='xsa_db'), _sa_prop('cairn', 33, 7, sheet='xsa_db'),
                     _sa_prop('gravestone', 35, 7, sheet='xsa_db', flip=True), _sa_prop('weeds', 23, 12, sheet='xsa_db'),
                     _sa_prop('weeds', 29, 12, sheet='xsa_db'), _sa_prop('chainlamp', 21, 2, sheet='xsa_db'), _sa_prop('chainlamp', 43, 2, sheet='xsa_db'),
                     dict(t='xsa', kind='leak', x=11, y=2), dict(t='xsa', kind='leak', x=25, y=2), dict(t='xsa', kind='leak', x=38, y=2),
                     dict(t='xsa', kind='motes', x=24, y=6, w=46, h=8, n=12, col='140,230,215'),
                     _sa_en('db_pilgrim', 17, 7), _sa_en('db_pilgrim', 42, 10), _sa_en('db_eel', 27, 12)])
_sa_r.fill(0, 0, 47, 1).fill(0, 0, 0, 13).fill(47, 0, 47, 13).fill(0, 13, 47, 13)
_sa_r.fill(47, 7, 47, 10, '.')                                   # -> Tomb Galleries (east, rows 7..10)
_sa_r.fill(1, 11, 9, 12).fill(46, 11, 46, 12).fill(42, 11, 45, 12)   # the landings
_sa_r.fill(10, 11, 45, 12, _SA_WL)                                # black water between the mounds
_sa_r.fill(14, 10, 21, 12).fill(15, 9, 20, 9).fill(16, 8, 19, 8)  # a burial mound
_sa_r.fill(30, 10, 37, 12).fill(31, 9, 36, 9).fill(32, 8, 35, 8)  # a second mound
_sa_r.fill(24, 11, 26, 12)                                        # a broken causeway pier
_sa_r.fill(38, 4, 40, 12)                                         # the barrow-tomb: climb it (wall-jump chimney below the ceiling pillar)
_sa_r.fill(35, 2, 35, 5)                                          # the pillar that makes the chimney
_sa_r.fill(41, 11, 45, 12)
for _x, _y, _ch in [(39, 3, 'i'), (6, 2, 'x'), (30, 2, 'x'), (14, 2, 'r'), (45, 2, 'r')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB12 Tomb Galleries (path; drops into the Nave)
_sa_r = Room('DB12', 'Tomb Galleries', 'barrows', 648, 98, 48, 16, indoor=True, needs=['talon'], x3=True, items=['gold'],
             spawns=[_sa_prop('tomb', 5, 12, sheet='xsa_db'), _sa_prop('tomb_leak', 11, 12, sheet='xsa_db'), _sa_prop('tomb', 17, 12, sheet='xsa_db'),
                     _sa_prop('tomb', 23, 12, sheet='xsa_db'), _sa_prop('tomb_leak', 29, 12, sheet='xsa_db'), _sa_prop('tomb', 35, 12, sheet='xsa_db'),
                     _sa_prop('tomb', 7, 6, sheet='xsa_db'), _sa_prop('tomb_leak', 14, 6, sheet='xsa_db'), _sa_prop('tomb', 21, 6, sheet='xsa_db'),
                     _sa_prop('tomb', 35, 6, sheet='xsa_db'), _sa_prop('tomb_leak', 41, 6, sheet='xsa_db'),
                     _sa_db('lamp', 2, 12), _sa_db('lamp', 26, 12), _sa_db('lamp', 44, 6), _sa_db('bones', 32, 12), _sa_db('bones', 19, 6),
                     dict(t='xsa', kind='leak', x=11, y=8, pool=True), dict(t='xsa', kind='leak', x=29, y=8, pool=True), dict(t='xsa', kind='leak', x=14, y=2),
                     dict(t='xsa', kind='leak', x=41, y=2),
                     dict(t='xsa', kind='motes', x=24, y=8, w=46, h=12, n=12, col='140,230,215'),
                     _sa_s('lore', 25, 6, page='sa_8', look='tablet'),
                     _sa_en('db_barnacle', 20, 12), _sa_en('db_pilgrim', 33, 12, hidden=True), _sa_en('db_pilgrim', 10, 6)])
_sa_r.fill(0, 0, 47, 1).fill(0, 0, 0, 15).fill(47, 0, 47, 15).fill(0, 13, 47, 15)
_sa_r.fill(0, 9, 0, 12, '.')                                      # <- Grave Causeway (west, rows 9..12)
_sa_r.fill(38, 13, 41, 15, '.')                                   # the floor gave way here: down into the Nave
_sa_r.fill(4, 7, 36, 7).fill(37, 7, 44, 7, '=')                   # the upper gallery (a rotted plank run over the gap)
_sa_r.fill(1, 2, 3, 4).fill(44, 2, 46, 3)                         # corbels
_sa_r.fill(1, 10, 2, 12, '.')
_sa_r.fill(46, 8, 46, 12)                                         # the east wall pier: wall-jump up to the gallery
_sa_r.fill(43, 11, 44, 11, '=')                                   # a ledge on the way up
_sa_r.fill(40, 14, 41, 14, '=')                                   # a rung in the broken floor (the way back up from the Nave)
for _x, _y, _ch in [(44, 6, 'i'), (10, 2, 'x'), (24, 2, 'x'), (38, 2, 'x'), (4, 12, 'b')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB10 The Sunken Nave (grand)
# Dry route: from the broken floor (top east) along the east triforium, west over the rafters and the Drowned Saint's
# shoulders to the west triforium and the door home (DB1). Swim route: down among the drowned pews to the altar (emberstone),
# an air pocket in the east chapel, the ledge out to the Tide Steps. A dry stairwell inside the west wall leads down to the
# Floodgates. Clear water (kw clear) so the whole drowned church reads from the rafters.
_sa_sp = [_sa_s('door', 4, 9, id='db_out', to='DB1', toId='db_out', look='arch'),
          _sa_prop('rosewin', 51, 15, sheet='xsa_rosewin', back=True, alpha=0.85, dy=-48),
          _sa_prop('saint', 51, 15, sheet='xsa_saint', back=True, dy=352),
          dict(t='xsa', kind='frontpaint', x=51, y=15, dy=352, sheet='xsa_saint', tag='saint', rect=[46, 13, 11, 25]),
          _sa_db('window', 12, 9), _sa_db('window', 88, 9), _sa_db('lamp', 14, 9), _sa_db('lamp', 82, 9), _sa_db('lamp', 3, 9),
          _sa_db('statue', 91, 9), _sa_db('bones', 9, 9), _sa_db('bell', 30, 3), _sa_db('bell', 70, 3),
          _sa_prop('pew', 12, 37, sheet='xsa_db'), _sa_prop('pew', 22, 37, sheet='xsa_db'), _sa_prop('pew', 30, 37, sheet='xsa_db'),
          _sa_prop('pew', 62, 37, sheet='xsa_db'), _sa_prop('pew', 70, 37, sheet='xsa_db'),
          _sa_prop('weeds', 26, 37, sheet='xsa_db'), _sa_prop('weeds', 36, 37, sheet='xsa_db'), _sa_prop('weeds', 66, 37, sheet='xsa_db'),
          _sa_prop('weeds', 75, 37, sheet='xsa_db'), _sa_prop('candles_db', 84, 33, sheet='xsa_db'), _sa_prop('pearlclam', 44, 37, sheet='xsa_db'),
          _sa_prop('chainlamp', 24, 3, sheet='xsa_db'), _sa_prop('chainlamp', 62, 3, sheet='xsa_db'), _sa_prop('chainlamp', 45, 3, sheet='xsa_db'),
          dict(t='xsa', kind='shaft', x=51, y=10, w=6, h=16, col='170,240,235', a=0.08, lean=0.2),
          dict(t='xsa', kind='shaft', x=30, y=12, w=3, h=20, col='170,240,235', a=0.05, lean=0.3),
          dict(t='xsa', kind='shaft', x=70, y=12, w=3, h=20, col='170,240,235', a=0.05, lean=0.3),
          dict(t='xsa', kind='bubbles', x=30, y=28, w=80, h=18, n=26),
          dict(t='xsa', kind='motes', x=48, y=8, w=90, h=12, n=20, col='150,230,220'),
          _sa_k('swing', 66, 3, len=6, rope='chain', amp=18, period=3.0),
          _sa_en('db_eel', 30, 30), _sa_en('db_eel', 68, 32), _sa_en('db_pilgrim', 86, 9), _sa_en('db_barnacle', 77, 11)]
_sa_r = Room('DB10', 'The Sunken Nave', 'barrows', 600, 114, 96, 40, indoor=True, needs=['talon', 'tidebreath'], x3=True, grand=True, clear=True,
             chests=['emberstone'], items=['gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 95, 2).fill(0, 0, 1, 39).fill(94, 0, 95, 39).fill(0, 38, 95, 39)
_sa_r.fill(86, 0, 89, 2, '.')                                     # the broken floor of the Tomb Galleries above
_sa_r.fill(86, 1, 87, 1, '=').fill(88, 4, 89, 4, '=').fill(86, 7, 87, 7, '=')   # rungs back up through it
_sa_r.fill(8, 18, 93, 37, _SA_WL)                                 # the drowned nave
# the west stairwell (dry, inside the wall) down to the Floodgates
_sa_r.fill(6, 12, 7, 39).fill(2, 38, 5, 39, '.')
for _y, _x0 in [(15, 2), (18, 4), (21, 2), (24, 4), (27, 2), (30, 4), (33, 2), (36, 4), (39, 2)]:
    _sa_r.fill(_x0, _y, _x0 + 1, _y, '=')
# the triforium galleries
_sa_r.fill(2, 10, 16, 11).fill(2, 11, 5, 11, '.').fill(2, 12, 5, 12, '=')        # west (the stairwell opens under it)
_sa_r.fill(80, 10, 93, 11)
# the rafters (the dry route) and the pillars under them
for _x0, _x1 in [(20, 26), (31, 37), (42, 46), (57, 63), (69, 75)]:
    _sa_r.fill(_x0, 10, _x1, 10, '=')
for _x in (18, 39, 55, 77):
    _sa_r.fill(_x, 12, _x + 1, 37)
# the Drowned Saint: plinth under water, shoulders and head above it (a perch in the middle of the crossing)
_sa_r.fill(46, 32, 56, 37).fill(48, 13, 54, 31, _SA_WL).fill(48, 18, 54, 31)
_sa_r.fill(49, 13, 53, 13, '=')
_sa_r.fill(48, 14, 54, 17, '.')
# the altar (the drowned pews are only furniture)
_sa_r.fill(82, 34, 88, 37)
# the east chapel: an air pocket under the gallery; the ledge out to the Tide Steps
_sa_r.fill(86, 20, 93, 21).fill(87, 22, 93, 24, '.').fill(86, 22, 86, 24, _SA_WL)
_sa_r.fill(90, 18, 93, 19).fill(94, 14, 95, 17, '.')
# vault ribs
for _x in (17, 38, 54, 76):
    _sa_r.fill(_x, 3, _x + 3, 3)
_sa_r.fill(50, 3, 52, 4)
_sa_swim(_sa_r, (8, 18, 93, 37))
for _x, _y, _ch in [(85, 33, 'C'), (51, 12, 'i'), (10, 9, 'k'), (84, 9, 'k'), (3, 3, 'x'), (33, 3, 'x'), (60, 3, 'x'), (92, 3, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB13 Tide Steps (parkour: the tide rises and falls)
# kw tide = the low-water row; 53_sa.js swings the line between tide and tide_hi. The map is painted with water up to the
# high line so the reachability check sees the room at high tide (the engine clears those cells: the tide owns them).
_sa_r = Room('DB13', 'Tide Steps', 'barrows', 696, 114, 48, 24, indoor=True, needs=['tidebreath'], x3=True, parkour=True,
             tide=20, tide_hi=6, tide_period=16, items=['seed'],
             spawns=[dict(t='xsa', kind='tide', x=2, y=17),
                     _sa_db('lamp', 3, 17), _sa_db('lamp', 44, 3), _sa_db('statue', 40, 3), _sa_db('bones', 26, 10),
                     _sa_prop('tidemark', 10, 18, sheet='xsa_db'), _sa_prop('tidemark', 19, 14, sheet='xsa_db'), _sa_prop('tidemark', 31, 6, sheet='xsa_db'),
                     _sa_prop('weeds', 7, 18, sheet='xsa_db'), _sa_prop('weeds', 25, 10, sheet='xsa_db'), _sa_prop('weeds', 30, 6, sheet='xsa_db'),
                     _sa_prop('chainlamp', 14, 2, sheet='xsa_db'), _sa_prop('chainlamp', 36, 2, sheet='xsa_db'), _sa_prop('wellcover', 22, 21, sheet='xsa_db'),
                     dict(t='xsa', kind='leak', x=9, y=2), dict(t='xsa', kind='leak', x=33, y=2),
                     dict(t='xsa', kind='motes', x=24, y=10, w=44, h=16, n=14, col='150,230,220'),
                     _sa_en('db_barnacle', 26, 10)])
_sa_r.fill(0, 0, 47, 1).fill(0, 0, 0, 23).fill(47, 0, 47, 23).fill(0, 23, 47, 23)
_sa_r.fill(0, 14, 0, 17, '.')                                     # <- the Sunken Nave (west, rows 14..17)
_sa_r.fill(1, 18, 5, 22)                                          # the landing
_sa_r.fill(6, 19, 12, 22)                                         # step one (low: walk on at low water)
_sa_r.fill(13, 22, 15, 22, '^')                                   # the spiked gutter
_sa_r.fill(16, 15, 20, 22)                                        # step two  (four rows up: float up at high water)
_sa_r.fill(21, 22, 23, 22, 'B')                                   # the old well, bricked over (strike it)
_sa_r.fill(21, 23, 23, 23, '.')
_sa_r.fill(24, 11, 28, 22)                                        # step three
_sa_r.fill(29, 7, 33, 22)                                         # step four
_sa_r.fill(34, 22, 37, 22, '^')
_sa_r.fill(38, 4, 46, 22)                                         # the top step (seed)
_sa_swim(_sa_r, (1, 6, 46, 23))                                   # high water (the tide), for the reachability check
for _x, _y, _ch in [(43, 3, 'i'), (12, 2, 'x'), (27, 2, 'x'), (41, 2, 'r')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB17 The Drowned Bell (secret, under the Tide Steps' well)
_sa_r = Room('DB17', 'The Drowned Bell', 'barrows', 712, 138, 16, 14, indoor=True, needs=['tidebreath'], x3=True, secret=True, clear=True,
             chests=['shard'],
             spawns=[_sa_prop('bigbell', 8, 1, sheet='xsa_bell'), _sa_s('lore', 13, 2, page='sa_7', look='none'),
                     _sa_db('bones', 3, 12), _sa_prop('pearlclam', 12, 12, sheet='xsa_db'), _sa_prop('weeds', 6, 12, sheet='xsa_db'),
                     dict(t='xsa', kind='bubbles', x=8, y=8, w=12, h=8, n=10)])
_sa_r.walls().fill(5, 0, 7, 0, '.')                               # the well from the Tide Steps
_sa_r.fill(1, 1, 14, 12, _SA_WL)
_sa_r.fill(10, 1, 14, 2, '.').fill(9, 1, 9, 2).fill(12, 3, 14, 3)   # an air pocket in the corner (the lore stone's ledge)
_sa_r.fill(5, 0, 7, 1, _SA_WL)
_sa_r.put(10, 12, 'C')
_sa_swim(_sa_r, (1, 1, 14, 12), (5, 0, 7, 0))

# ---------------------------------------------------------------- DB14 The Floodgates (puzzle)
# Three basins (A, B, C) under a dry walkway; a wheel on each basin's floor. A wheel turns only from dry ground, and each one
# turns two floodgates: A's wheel swaps A and B, B's swaps B and C, C's swaps C and A (the pipes on the wall show which).
# Start: A dry, B and C full. B's high niche holds the chest (B full); the drain to the Pearl Lagoon opens only while C is dry.
# (53_sa.js owns the rule: kind 'floodgates'. The map is painted full so the reachability check sees every basin swimmable.)
_sa_sp = [dict(t='xsa', kind='floodgates', x=9, y=4, basins=['lA', 'lB', 'lC'], wheels=['wA', 'wB', 'wC'], start=[0, 1, 1], drain='gX',
               pairs=[['lA', 'lB'], ['lB', 'lC'], ['lC', 'lA']]),
          _sa_k('level', 1, 7, w=11, h=15, states=[22, 7], fluid='water', id='lA', speed=4),
          _sa_k('level', 13, 7, w=13, h=15, states=[22, 7], fluid='water', id='lB', speed=4),
          _sa_k('level', 27, 7, w=12, h=15, states=[22, 7], fluid='water', id='lC', speed=4),
          _sa_k('lever', 4, 21, id='wA', skin='stone', msg=''), _sa_k('lever', 16, 21, id='wB', skin='stone', msg=''),
          _sa_k('lever', 30, 21, id='wC', skin='stone', msg=''),
          _sa_k('gate', 37, 21, id='gX', persist=False),
          _sa_s('lore', 24, 4, page='sa_6', look='tablet'),
          _sa_db('lamp', 1, 4), _sa_db('lamp', 13, 4), _sa_db('lamp', 36, 4), _sa_prop('chainlamp', 19, 1, sheet='xsa_db'),
          _sa_prop('sluice', 6, 21, sheet='xsa_db'), _sa_prop('sluice', 20, 21, sheet='xsa_db'), _sa_prop('sluice', 33, 21, sheet='xsa_db'),
          dict(t='xsa', kind='motes', x=20, y=3, w=36, h=4, n=8, col='150,230,220')]
_sa_r = Room('DB14', 'The Floodgates', 'barrows', 600, 154, 40, 24, indoor=True, needs=['tidebreath'], x3=True, puzzle=True,
             chests=['emberstone'], spawns=_sa_sp)
_sa_r.fill(0, 0, 39, 0).fill(0, 0, 0, 23).fill(39, 0, 39, 23).fill(0, 22, 39, 23)
_sa_r.fill(2, 0, 5, 0, '.')                                       # <- the stairwell from the Sunken Nave
_sa_r.fill(1, 5, 38, 6)                                           # the walkway
_sa_r.fill(5, 5, 7, 6, '.').fill(18, 5, 20, 6, '.').fill(31, 5, 33, 6, '.')   # a hatch over each basin
_sa_r.fill(12, 7, 12, 21).fill(26, 7, 26, 21)                     # the basin walls
_sa_r.fill(37, 7, 38, 17)                                         # C's east wall; the drain tunnel runs under it
_sa_r.fill(4, 2, 5, 2, '=')                                       # a rung up into the Nave's stairwell
_sa_r.fill(39, 18, 39, 21, '.')                                   # -> the Pearl Lagoon (east, rows 18..21)
_sa_r.fill(13, 10, 15, 10).put(14, 9, 'C')                        # B's niche (reach it only by swimming up)
_sa_swim(_sa_r, (1, 7, 11, 21), (13, 7, 25, 21), (27, 7, 36, 21))  # the basins at their fullest, for the reachability check
for _x, _y, _ch in [(10, 1, 'x'), (29, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB15 Pearl Lagoon (vista)
_sa_r = Room('DB15', 'Pearl Lagoon', 'barrows', 640, 154, 40, 24, indoor=True, needs=['tidebreath'], x3=True, vista=True, clear=True,
             spawns=[_sa_s('bench', 32, 9, id='bench', view=[17, 13], lore='sa_5'),
                     _sa_prop('lagoonback', 20, 21, sheet='xsa_lagoon', back=True, dy=16),
                     _sa_prop('pearlclam', 8, 21, sheet='xsa_db'), _sa_prop('pearlclam', 21, 21, sheet='xsa_db', flip=True), _sa_prop('pearlclam', 14, 21, sheet='xsa_db'),
                     _sa_prop('weeds', 4, 21, sheet='xsa_db'), _sa_prop('weeds', 11, 21, sheet='xsa_db'), _sa_prop('weeds', 18, 21, sheet='xsa_db'),
                     _sa_prop('weeds', 25, 21, sheet='xsa_db'), _sa_db('statue', 24, 21), _sa_prop('candles_db', 36, 9, sheet='xsa_db'),
                     _sa_prop('coral', 6, 21, sheet='xsa_db'), _sa_prop('coral', 16, 21, sheet='xsa_db'), _sa_prop('coral', 27, 21, sheet='xsa_db'),
                     dict(t='xsa', kind='shaft', x=12, y=10, w=5, h=18, col='190,250,245', a=0.11, lean=0.25),
                     dict(t='xsa', kind='shaft', x=22, y=10, w=3, h=18, col='190,250,245', a=0.08, lean=0.25),
                     dict(t='xsa', kind='shaft', x=6, y=10, w=2, h=18, col='190,250,245', a=0.06, lean=0.25),
                     dict(t='xsa', kind='pearls', x=16, y=16, w=26, h=10, n=22),
                     dict(t='xsa', kind='bubbles', x=16, y=17, w=26, h=10, n=14),
                     dict(t='xsa', kind='motes', x=20, y=6, w=36, h=8, n=16, col='200,250,245'),
                     _sa_prop('chainlamp', 9, 2, sheet='xsa_db'), _sa_prop('chainlamp', 24, 2, sheet='xsa_db'), _sa_prop('rootcurtain', 16, 2),
                     _sa_prop('rootcurtain', 36, 4), dict(t='xsa', kind='leak', x=18, y=2, pool=True), dict(t='xsa', kind='leak', x=27, y=2),
                     _sa_prop('weeds', 36, 9, sheet='xsa_db'), _sa_db('bones', 30, 9)])
_sa_r.fill(0, 0, 39, 1).fill(0, 0, 0, 23).fill(39, 0, 39, 23).fill(0, 22, 39, 23)
_sa_r.fill(0, 18, 0, 21, '.')                                     # <- the Floodgates' drain (west, underwater)
_sa_r.fill(39, 6, 39, 9, '.')                                     # -> the Breathless Dive (east)
_sa_r.fill(1, 12, 38, 21, _SA_WL)                                 # the lagoon
_sa_r.fill(28, 10, 38, 11)                                        # the grotto shelf (the bench)
_sa_r.fill(28, 12, 30, 14).fill(31, 12, 38, 16)                   # the shelf's rock falling into the water
_sa_r.fill(1, 2, 5, 5).fill(1, 6, 3, 8).fill(34, 2, 38, 3)        # rock around the old skylight
_sa_swim(_sa_r, (1, 12, 38, 21), (0, 18, 0, 21))
for _x, _y, _ch in [(10, 2, 'r'), (20, 2, 'r'), (29, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB16 Breathless Dive (trial: one breath, c_x3_lung)
# The sigil stands on the landing; the course runs down into sealed water (no air anywhere on it), east through the blade
# gallery, down the spiked throat, back along the lower run and up the east shaft into the goal chamber. The dry corridor
# over the top leads home; its gate is shut while a trial runs.
_sa_sp = [_sa_s('trial', 2, 9, id='dive', par=16, reward='c_x3_lung', region='Drowned Barrows', name='Breathless Dive'),
          _sa_s('trial_goal', 60, 7, trial='dive'),
          dict(t='xsa', kind='trialgate', x=48, y=4, gate='gR', trial='dive'),
          _sa_k('gate', 48, 4, id='gR', open=True),
          _sa_k('pendulum', 20, 12, len=4, period=2.4, amp=55, phase=0.0, skin='stone'),
          _sa_k('pendulum', 32, 12, len=4, period=2.4, amp=55, phase=0.5, skin='stone'),
          _sa_db('lamp', 2, 9), _sa_db('lamp', 61, 7), _sa_db('bones', 62, 7), _sa_prop('chainlamp', 30, 1, sheet='xsa_db'),
          _sa_prop('weeds', 44, 20, sheet='xsa_db'), _sa_prop('weeds', 50, 20, sheet='xsa_db'), _sa_prop('coral', 20, 14, sheet='xsa_db'),
          dict(t='xsa', kind='bubbles', x=26, y=12, w=38, h=4, n=18),
          dict(t='xsa', kind='motes', x=30, y=3, w=50, h=2, n=8, col='150,230,220')]
_sa_r = Room('DB16', 'Breathless Dive', 'barrows', 680, 154, 64, 24, indoor=True, needs=['tidebreath'], x3=True, trial=True, spawns=_sa_sp)
_sa_r.fill(0, 0, 63, 0).fill(0, 0, 0, 23).fill(63, 0, 63, 23).fill(0, 23, 63, 23)
_sa_r.fill(0, 6, 0, 9, '.')                                       # <- Pearl Lagoon (west, rows 6..9)
_sa_r.fill(1, 10, 6, 22)                                          # the landing (the sigil)
_sa_r.fill(5, 10, 6, 14, _SA_WL)                                  # the dive pool: open to the air, then the lid
_sa_r.fill(7, 5, 62, 10)                                          # the lid over the course: no air under it
_sa_r.fill(3, 2, 55, 4, '.').fill(7, 5, 55, 5)                    # the dry corridor home (over the lid)
_sa_r.fill(1, 1, 2, 5).fill(3, 5, 6, 5)                           # (its floor over the landing: a one-way drop at cols 3..6)
_sa_r.fill(3, 5, 6, 5, '=')
_sa_r.fill(7, 11, 62, 22, _SA_WL)                                 # the sealed water
# the course: upper run (rows 11..14) east, the throat down at 42..45, lower run (rows 18..21) east, up the east shaft
_sa_r.fill(7, 15, 41, 17)                                         # floor of the upper run / roof of the lower
_sa_r.fill(46, 11, 52, 17)                                        # a block the upper run ends against
_sa_r.fill(7, 18, 37, 22)                                         # dead water under the upper run: solid
_sa_r.fill(38, 21, 52, 22)                                        # the lower run's floor
_sa_r.fill(53, 11, 55, 22).fill(53, 18, 55, 21, _SA_WL)           # the east wall of the throat; the lower run passes under it
_sa_r.fill(56, 9, 58, 20, _SA_WL).fill(59, 9, 62, 22).fill(56, 21, 58, 22)   # the east shaft up to the goal chamber
_sa_r.fill(56, 6, 62, 7, '.').fill(56, 8, 58, 8, '.')             # the goal chamber (air; the shaft surfaces at row 9)
_sa_r.fill(56, 2, 62, 5, '.').fill(56, 5, 58, 5, '=')             # the climb up into the corridor home
_sa_r.fill(13, 11, 14, 11, 'v').fill(26, 11, 27, 11, 'v').fill(38, 14, 40, 14, '^')   # teeth
_sa_r.fill(42, 16, 45, 17, _SA_WL).fill(42, 15, 45, 15, _SA_WL)   # the throat
_sa_r.fill(41, 20, 41, 20, '^').fill(47, 18, 47, 18, 'v')
_sa_r.fill(38, 18, 41, 20, _SA_WL)
for _x, _y, _ch in [(12, 1, 'x'), (40, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)
_sa_swim(_sa_r, (5, 10, 58, 22))

# ---------------------------------------------------------------- Barrows anchors (old rooms: door spawns only)
ROOM('DB3').kw.setdefault('spawns', []).extend([
    _sa_s('door', 10, 9, id='db_in', to='DB11', toId='db_in', look='arch'),
    dict(t='xsa', kind='sign', x=10, y=9, text='Cold air moves behind the arch. The tide-keepers\' causeway runs east.')])
ROOM('DB1').kw.setdefault('spawns', []).extend([
    _sa_s('door', 7, 13, id='db_out', to='DB10', toId='db_out', look='arch'),
    dict(t='xsa', kind='seal', x=7, y=13, door='db_out', look='chains', msg='An arch chained shut from the other side. Water drips through the links.')])


# ============================================================================================ THE CRIMSON MANOR
# Zone x 453..564, y 41..83 (east of CM7/CM4/CM6/CM5). The list's nine rooms don't fit in 112x43 even at -25%, so the
# servants' tower and the grand stair rise into the unclaimed pocket above it (x 500..563, y 1..40, clear of E1 and X5):
#   CM12 Blood-Rain Rooftops  452..499 x 41..57   parkour (outdoor, blood rain): out through the gallery window
#   CM10 The Grand Staircase  500..523 x 24..57   path: landings under watching portraits; the hub of the wing
#   CM13 The Portrait Riddle  524..563 x 41..57   puzzle: follow the painted eyes (the Portrait Key)
#   CM9  The East Wing        452..535 x 58..83   grand: three floors, servants' stairs, a collapsed library; gate to CM5
#   CM16 Moonlit Conservatory 536..563 x 59..83   vista: glass, dead roses, the piano that plays itself
#   CM11 Servants' Corridor   524..563 x 30..40   path: the hidden halls; the servants' door to CM3 (second wing)
#   CM15 Servants' Quarters   524..563 x 19..29   gauntlet: ring the service bell
#   CM14 The Locked Study     524..547 x  1..18   puzzle: three keys open its door (found behind the bookcase)
#   CM17 Behind the Bookcase  548..563 x  5..18   secret: through the library's false bookcase (the Silver Key)

# ---------------------------------------------------------------- CM12 Blood-Rain Rooftops (parkour; blood rain)
# In through the gallery window and out through the stair tower's door: both are sys doors rather than open edges, because
# tools/reach.py's flood from one edge seed starves the other in this many-walled room (NEEDS in the SA report).
_sa_r = Room('CM12', 'Blood-Rain Rooftops', 'crimson', 452, 41, 48, 17, needs=['talon'], x3=True, parkour=True,
             rain=dict(every=[6.0, 9.0], dur=2.6), items=['xsa_key3'],
             spawns=[_sa_s('door', 3, 15, id='cm_win', to='CM4', toId='cm_win', look='arch'),
                     _sa_s('door', 44, 6, id='cm_roof', to='CM10', toId='cm_roof', look='arch'),
                     dict(t='cm_perch', x=24, y=7, n=1), dict(t='cm_perch', x=44, y=6, n=1),
                     _sa_cm('statue', 10, 11, sub='gargoyle'), _sa_cm('sconce', 45, 4),
                     _sa_prop('chimney', 13, 11, sheet='xsa_cm'), _sa_prop('chimney', 29, 9, sheet='xsa_cm'), _sa_prop('weathervane', 43, 6, sheet='xsa_cm'),
                     _sa_prop('crows', 36, 4, sheet='xsa_cm'), _sa_prop('gutterspout', 3, 15, sheet='xsa_cm'),
                     dict(t='xsa', kind='motes', x=24, y=5, w=46, h=10, n=10, col='255,120,120'),
                     _sa_en('cm_servant', 21, 10)])
_sa_r.fill(0, 0, 0, 16).fill(0, 16, 47, 16).fill(47, 0, 47, 16)
_sa_r.fill(7, 13, 15, 15).fill(8, 12, 14, 12)                     # the first roof (lead flashing along its ridge)
_sa_r.fill(5, 11, 8, 11)                                          # an eave over the gutter walk: shelter from the rain
_sa_r.fill(16, 15, 18, 15, '^')                                   # the spiked railings between the roofs
_sa_r.fill(19, 11, 27, 15).fill(20, 8, 25, 8).fill(25, 9, 25, 10)   # the second roof and its dormer (open west: shelter)
_sa_r.fill(28, 15, 30, 15, '^')
_sa_r.fill(31, 9, 38, 15)                                         # the third roof
_sa_r.fill(35, 5, 36, 8)                                          # the tall chimney (the Rook's Key on top)
_sa_r.fill(32, 6, 33, 6, '=')                                     # a lead ledge up to it
_sa_r.fill(39, 15, 40, 15, '^')
_sa_r.fill(41, 7, 46, 15)                                         # the stair tower's roof
_sa_r.fill(41, 3, 42, 3)                                          # a lintel over the stair tower's door (shelter)
for _x, _y, _ch in [(35, 4, 'i')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('slate', 7, 12, 9, 4), ('slate', 19, 8, 9, 8), ('slate', 31, 9, 8, 7), ('slate', 41, 7, 6, 9), ('brick', 35, 5, 2, 4),
          ('slate', 5, 11, 4, 1), ('brick', 41, 3, 2, 1))

# ---------------------------------------------------------------- CM10 The Grand Staircase (path; the hub)
_sa_sp = [_sa_s('door', 3, 23, id='cm_roof', to='CM12', toId='cm_roof', look='arch'),
          _sa_pt(4, 7, 'a'), _sa_pt(19, 7, 'b'), _sa_pt(12, 4, 'c'),
          _sa_pt(18, 13, 'd'), _sa_pt(5, 18, 'e'), _sa_pt(18, 23, 'a'), _sa_pt(6, 28, 'b'), _sa_pt(16, 28, 'c'),
          dict(t='cm_chandelier', x=12, y=2, len=120, swing=0, big=True),
          _sa_cm('candelabra', 2, 31), _sa_cm('candelabra', 21, 31), _sa_cm('candelabra', 21, 15), _sa_cm('candelabra', 2, 23),
          _sa_cm('statue', 12, 31, sub='lady'), _sa_prop('grandclock', 7, 31, sheet='xsa_cm'), _sa_prop('bust', 16, 7, sheet='xsa_cm'),
          _sa_cm('sconce', 11, 20), _sa_cm('sconce', 11, 11),
          _sa_en('cm_servant', 17, 19), _sa_en('cm_hound', 6, 31)]
_sa_r = Room('CM10', 'The Grand Staircase', 'crimson', 500, 24, 24, 34, indoor=True, needs=['talon'], x3=True, spawns=_sa_sp)
_sa_r.fill(0, 0, 23, 1).fill(0, 0, 0, 33).fill(23, 0, 23, 33).fill(0, 32, 23, 33)
_sa_r.fill(23, 12, 23, 15, '.')                                   # -> the Servants' Corridor (a jib door in the panelling)
_sa_r.fill(23, 28, 23, 31, '.')                                   # -> the Portrait Riddle
_sa_r.fill(9, 32, 12, 33, '.')                                    # the stair goes on down into the East Wing
_sa_r.fill(1, 24, 8, 24)                                          # the west landing (from the Rooftops)
_sa_r.fill(14, 16, 22, 16)                                        # the east landing (the servants' door)
_sa_r.fill(1, 8, 22, 8).fill(8, 8, 15, 8, '=')                    # the top landing, a gallery round the stairwell
_sa_r.fill(9, 32, 12, 32, '=')                                    # (the well of the stair: step down through it)
for _x0, _x1, _y in [(15, 20, 28), (3, 8, 28), (10, 14, 26), (16, 21, 20), (10, 13, 22), (4, 9, 20), (4, 8, 16), (9, 12, 18),
                     (10, 13, 13), (4, 8, 12), (16, 20, 12)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
for _x, _y, _ch in [(12, 1, 'r'), (3, 2, 'x'), (20, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM13 The Portrait Riddle (puzzle; the Portrait Key)
# The Countess's great portrait looks from one family portrait to the next (53_sa.js draws her gaze). Strike them in the
# order she looks; the panel beside her slides open on the key. A brass plate (lore sa_12) says so.
_sa_fr = [(4, 7, 'f1'), (8, 5, 'f2'), (12, 7, 'f3'), (27, 7, 'f4'), (30, 5, 'f5'), (33, 7, 'f6')]
_sa_sp = [dict(t='xsa', kind='gaze', x=20, y=6, seq='gaze', frames=[f[2] for f in _sa_fr], order=['f4', 'f2', 'f6', 'f1', 'f5']),
          _sa_prop('familyportrait', 20, 9, sheet='xsa_portrait'),
          *[_sa_k('frame', x, y, id=i, group='gaze') for x, y, i in _sa_fr],
          _sa_k('seq', 20, 14, id='gaze', group='gaze', order=['f4', 'f2', 'f6', 'f1', 'f5'], targets=['gK'],
                msg='Somewhere behind the panelling, a latch lifts.'),
          _sa_k('gate', 35, 14, id='gK'),
          _sa_s('lore', 17, 14, page='sa_12', look='tablet'),
          _sa_cm('candelabra', 2, 14), _sa_cm('candelabra', 24, 14), _sa_cm('candelabra', 31, 14), _sa_cm('table', 10, 14),
          _sa_prop('rug', 20, 14, sheet='xsa_cm'), _sa_cm('sconce', 12, 10), _sa_cm('sconce', 29, 10)]
_sa_r = Room('CM13', 'The Portrait Riddle', 'crimson', 524, 41, 40, 17, indoor=True, needs=['talon'], x3=True, puzzle=True,
             items=['xsa_key2', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 39, 1).fill(0, 0, 0, 16).fill(39, 0, 39, 16).fill(0, 15, 39, 16)
_sa_r.fill(0, 11, 0, 14, '.')                                     # <- the Grand Staircase (west, rows 11..14)
_sa_r.fill(35, 2, 38, 10).fill(36, 11, 38, 14, '.')               # the panel alcove behind the gate
for _x, _y, _ch in [(37, 14, 'i'), (38, 14, 'i'), (6, 2, 'x'), (20, 2, 'r'), (30, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM9 The East Wing (grand)
# Three floors. Top: the long gallery (from the Grand Staircase); the library's false bookcase (-> CM17).
# Middle: guest rooms and the servants' landing. Bottom: the servants' hall, the gate to the Blood Cellars (CM5) that
# opens from this side (the loop back), the door east into the Conservatory. The library in the middle has fallen
# through both floors: its shelves are the secret route down (emberstone on the top shelf).
_sa_sp = [_sa_s('door', 76, 6, id='cm_bc', to='CM17', toId='cm_bc', look='arch'),
          dict(t='xsa', kind='bookcase', x=76, y=6, door='cm_bc'),
          _sa_k('gate', 1, 22, id='gW', persist=True), _sa_k('lever', 4, 22, id='lW', targets=['gW'], once=True, skin='wood',
                                                             msg='The cellar gate grinds up. A way back to the Blood Cellars.'),
          dict(t='cm_chandelier', x=20, y=1, len=40, swing=0), dict(t='cm_chandelier', x=66, y=9, len=40, swing=0),
          dict(t='cm_chandelier', x=30, y=17, len=30, swing=0),
          _sa_prop('fallenchandelier', 52, 19, sheet='xsa_chand', dy=48),
          _sa_prop('bookcase', 45, 22, sheet='xsa_cm'), _sa_prop('bookcase_fallen', 58, 22, sheet='xsa_cm'), _sa_prop('bookcase', 60, 14, sheet='xsa_cm'),
          _sa_prop('bookcase', 42, 6, sheet='xsa_cm'), _sa_prop('bookcase', 70, 6, sheet='xsa_cm'), _sa_prop('bookcase', 80, 6, sheet='xsa_cm'),
          _sa_prop('books', 48, 22, sheet='xsa_cm'), _sa_prop('books', 58, 22, sheet='xsa_cm'), _sa_prop('books', 53, 14, sheet='xsa_cm'),
          _sa_pt(8, 4, 'a'), _sa_pt(16, 4, 'c', ambush=True), _sa_pt(26, 4, 'e'), _sa_pt(34, 4, 'd'),
          _sa_cm('candelabra', 3, 6), _sa_cm('candelabra', 38, 6), _sa_cm('candelabra', 64, 6),
          _sa_cm('table', 12, 14), _sa_cm('candelabra', 20, 14), _sa_prop('bed', 28, 14, sheet='xsa_cm'), _sa_prop('wardrobe', 34, 14, sheet='xsa_cm'),
          _sa_cm('winerack', 16, 22), _sa_cm('barrel', 22, 22), _sa_cm('table', 30, 22), _sa_prop('hearth', 8, 22, sheet='xsa_cm'),
          _sa_prop('bellboard', 36, 22, sheet='xsa_cm'), _sa_cm('candelabra', 26, 22), _sa_cm('candelabra', 79, 22), _sa_cm('statue', 72, 22, sub='lady'),
          _sa_cm('sconce', 70, 12), _sa_cm('sconce', 42, 20),
          dict(t='xsa', kind='motes', x=52, y=14, w=26, h=20, n=18, col='255,210,170'),
          _sa_en('cm_servant', 24, 6), _sa_en('cm_servant', 18, 14), _sa_en('cm_hound', 28, 22), _sa_en('cm_servant', 76, 22),
          _sa_en('cm_hound', 70, 14)]
_sa_r = Room('CM9', 'The East Wing', 'crimson', 452, 58, 84, 26, indoor=True, needs=['talon'], x3=True, grand=True,
             items=['emberstone', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 83, 0).fill(0, 0, 0, 25).fill(83, 0, 83, 25).fill(0, 23, 83, 25)
_sa_r.fill(0, 19, 0, 22, '.')                                     # <- the Blood Cellars (west, rows 19..22; the gate)
_sa_r.fill(83, 19, 83, 22, '.')                                   # -> the Conservatory (east)
_sa_r.fill(57, 0, 60, 0, '.')                                     # the Grand Staircase comes down here
_sa_r.fill(1, 7, 82, 7).fill(1, 15, 82, 15)                       # the floors
_sa_r.fill(1, 16, 1, 18)                                          # over the cellar gate (it reaches this)
# the servants' stairs at the west end (a narrow shaft through both floors, rungs)
_sa_r.fill(5, 7, 7, 7, '.').fill(5, 15, 7, 15, '.')
for _y in (4, 10, 13, 18, 21):
    _sa_r.fill(5, _y, 6, _y, '=')
_sa_r.fill(5, 7, 7, 7, '=').fill(5, 15, 7, 15, '=')
# the grand stair's landing under CM10 (top floor) and the gallery's east end
_sa_r.fill(56, 4, 61, 4, '=')
# the collapsed library: both floors gone between cols 42..62; its shelves are the way down (and up)
_sa_r.fill(42, 7, 62, 7, '.').fill(42, 15, 62, 15, '.')
_sa_r.fill(40, 7, 41, 7, '=').fill(63, 7, 64, 7, '=')             # broken floor edges
for _x0, _x1, _y in [(44, 47, 10), (51, 54, 9), (58, 61, 11), (46, 49, 13), (54, 57, 14), (43, 45, 17), (49, 52, 18),
                     (57, 60, 19), (62, 62, 16), (47, 49, 3), (53, 55, 2)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
_sa_r.fill(50, 20, 55, 22)                                        # the fallen chandelier's wreck (a heap to climb)
for _x, _y, _ch in [(54, 1, 'i'), (48, 2, 'i'), (10, 1, 'x'), (30, 1, 'x'), (70, 1, 'x'), (4, 22, 'k'), (80, 14, 'k')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM16 Moonlit Conservatory (vista; open to the sky through the glass)
_sa_r = Room('CM16', 'Moonlit Conservatory', 'crimson', 536, 59, 28, 25, needs=['talon'], x3=True, vista=True,
             spawns=[_sa_s('bench', 9, 21, id='bench', view=[15, 10], lore='sa_9', skin='wood'),
                     dict(t='xsa', kind='glasshouse', x=14, y=12),
                     _sa_prop('piano', 19, 21, sheet='xsa_cm'), dict(t='xsa', kind='piano', x=19, y=21),
                     _sa_prop('roses', 4, 21, sheet='xsa_cm'), _sa_prop('roses', 14, 21, sheet='xsa_cm'), _sa_prop('roses', 25, 21, sheet='xsa_cm'),
                     _sa_prop('trellis', 7, 21, sheet='xsa_cm'), _sa_prop('trellis', 23, 21, sheet='xsa_cm'), _sa_cm('fountain', 14, 21),
                     _sa_prop('roses', 2, 16, sheet='xsa_cm'), _sa_prop('roses', 26, 16, sheet='xsa_cm'),
                     dict(t='xsa', kind='shaft', x=14, y=12, w=6, h=20, col='210,220,255', a=0.09, lean=-0.3),
                     dict(t='xsa', kind='shaft', x=6, y=12, w=3, h=20, col='210,220,255', a=0.06, lean=-0.3),
                     dict(t='xsa', kind='petals', x=14, y=12, w=26, h=20, n=18),
                     dict(t='xsa', kind='motes', x=14, y=12, w=26, h=18, n=14, col='220,225,255')])
_sa_r.fill(0, 0, 27, 1).fill(0, 0, 0, 24).fill(27, 0, 27, 24).fill(0, 22, 27, 24)
_sa_r.fill(0, 18, 0, 21, '.')                                     # <- the East Wing (west, rows 18..21)
_sa_r.fill(1, 17, 4, 17).fill(23, 17, 26, 17)                     # raised rose beds along the glass
_sa_r.fill(2, 2, 3, 3).fill(24, 2, 25, 3)                         # iron ribs of the glasshouse
_sa_skins(_sa_r, ('glass', 0, 0, 28, 2), ('glass', 0, 2, 1, 16), ('glass', 27, 2, 1, 20))

# ---------------------------------------------------------------- CM11 Servants' Corridor (path; the hidden halls)
_sa_r = Room('CM11', 'Servants\' Corridor', 'crimson', 524, 30, 40, 11, indoor=True, needs=['talon'], x3=True, items=['gold'],
             spawns=[_sa_s('door', 37, 9, id='cm_srv', to='CM3', toId='cm_srv', look='hatch'),
                     _sa_prop('canvasback', 8, 9, sheet='xsa_cm'), _sa_prop('canvasback', 20, 9, sheet='xsa_cm'),
                     _sa_prop('pipes', 14, 9, sheet='xsa_cm'), _sa_prop('pipes', 28, 9, sheet='xsa_cm'), _sa_prop('lamp_cm', 4, 9, sheet='xsa_cm'),
                     _sa_prop('lamp_cm', 25, 9, sheet='xsa_cm'), _sa_prop('laundry', 17, 1, sheet='xsa_cm'), _sa_cm('barrel', 11, 9),
                     _sa_prop('spyhole', 30, 9, sheet='xsa_cm'),
                     _sa_en('cm_servant', 18, 9), _sa_en('cm_hound', 30, 3)])
_sa_r.fill(0, 0, 39, 0).fill(0, 0, 0, 10).fill(39, 0, 39, 10).fill(0, 10, 39, 10)
_sa_r.fill(0, 6, 0, 9, '.')                                       # <- the Grand Staircase (west, rows 6..9)
_sa_r.fill(34, 0, 36, 0, '.')                                     # the back stair up to the Servants' Quarters
for _y in (1, 4, 7):
    _sa_r.fill(34, _y, 35, _y, '=')
_sa_r.fill(1, 1, 3, 3).fill(1, 4, 14, 4).fill(10, 4, 12, 4, '=')  # the upper crawl (a gap in its floor)
_sa_r.fill(22, 4, 32, 4).fill(26, 4, 28, 4, '=')
_sa_r.fill(14, 5, 14, 6).fill(22, 5, 22, 6)                       # low beams: duck under
_sa_r.fill(37, 1, 38, 3)
for _x, _y, _ch in [(3, 5, 'i'), (9, 1, 'x'), (29, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)
_sa_r.put(3, 5, '.').put(2, 9, 'i')

# ---------------------------------------------------------------- CM15 Servants' Quarters (gauntlet: ring the service bell)
_sa_W = [[dict(type='cm_servant', x=6, y=9), dict(type='cm_servant', x=26, y=9)],
         [dict(type='cm_hound', x=4, y=9), dict(type='cm_hound', x=28, y=9), dict(type='cm_servant', x=16, y=9)],
         [dict(type='cm_servant', x=5, y=9), dict(type='cm_servant', x=27, y=9), dict(type='cm_hound', x=10, y=9), dict(type='cm_hound', x=22, y=9)],
         [dict(type='xsa_head_butler', x=16, y=9)]]
_sa_r = Room('CM15', 'Servants\' Quarters', 'crimson', 524, 19, 40, 11, indoor=True, needs=['talon'], x3=True, gauntlet=True,
             spawns=[_sa_k('gate', 32, 9, id='gq', open=True),
                     _sa_s('gauntlet', 16, 9, id='quarters', look='bell', name='The Servants\' Quarters', gates=['gq'], waves=_sa_W,
                           reward=['emberstone', 'gold']),
                     _sa_prop('cot', 7, 9, sheet='xsa_cm'), _sa_prop('cot', 12, 9, sheet='xsa_cm'), _sa_prop('cot', 21, 9, sheet='xsa_cm'),
                     _sa_prop('cot', 26, 9, sheet='xsa_cm', flip=True), _sa_prop('bellboard', 16, 5, sheet='xsa_cm', dy=-16),
                     _sa_prop('stove', 36, 9, sheet='xsa_cm'), _sa_prop('laundry', 24, 1, sheet='xsa_cm'), _sa_prop('lamp_cm', 18, 9, sheet='xsa_cm'),
                     _sa_cm('table', 30, 9)])
_sa_r.fill(0, 0, 39, 0).fill(0, 0, 0, 10).fill(39, 0, 39, 10).fill(0, 10, 39, 10)
_sa_r.fill(34, 10, 36, 10, '.')                                   # the back stair down to the Servants' Corridor
_sa_r.fill(35, 0, 37, 0, '.')                                     # a hatch from the walls above (Behind the Bookcase)
_sa_r.fill(32, 1, 32, 3)                                          # the partition over the arena gate
_sa_r.fill(33, 7, 38, 7, '=')

# ---------------------------------------------------------------- CM14 The Locked Study (puzzle: three keys; its door is in the walls, CM17)
_sa_r = Room('CM14', 'The Locked Study', 'crimson', 524, 1, 24, 18, indoor=True, needs=['talon'], x3=True, puzzle=True,
             chests=['shard'], items=['gold'],
             spawns=[_sa_s('door', 3, 16, id='cm_study', to='CM17', toId='cm_study', look='arch'),
                     _sa_prop('desk', 12, 16, sheet='xsa_cm'), _sa_prop('bookcase', 4, 16, sheet='xsa_cm'), _sa_prop('bookcase', 20, 16, sheet='xsa_cm'),
                     _sa_prop('globe', 16, 16, sheet='xsa_cm'), _sa_prop('grandclock', 22, 9, sheet='xsa_cm'), _sa_cm('candelabra', 8, 16),
                     _sa_pt(12, 11, 'b'), _sa_cm('sconce', 6, 12), _sa_cm('sconce', 18, 12),
                     _sa_s('lore', 14, 16, page='sa_10', look='book'),
                     dict(t='xsa', kind='motes', x=12, y=9, w=20, h=14, n=10, col='255,215,170')])
_sa_r.fill(0, 0, 23, 1).fill(0, 0, 0, 17).fill(23, 0, 23, 17).fill(0, 17, 23, 17)
_sa_r.fill(17, 10, 23, 10).fill(1, 10, 5, 10, '=')                # the mezzanine (the clock, the gold)
_sa_r.fill(9, 13, 11, 13, '=')
for _x, _y, _ch in [(19, 9, 'C'), (2, 9, 'i'), (12, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM17 Behind the Bookcase (secret: the Silver Key)
_sa_r = Room('CM17', 'Behind the Bookcase', 'crimson', 548, 5, 16, 14, indoor=True, needs=['talon'], x3=True, secret=True,
             items=['xsa_key1'],
             spawns=[_sa_s('door', 2, 12, id='cm_bc', to='CM9', toId='cm_bc', look='crack'),
                     _sa_s('door', 7, 12, id='cm_study', to='CM14', toId='cm_study', look='arch'),
                     dict(t='xsa', kind='keygate', x=7, y=12, door='cm_study', keys=['xsa_key1', 'xsa_key2', 'xsa_key3'], flag='xsa:study'),
                     _sa_s('lore', 9, 6, page='sa_11', look='corpse'), _sa_prop('chalk', 12, 12, sheet='xsa_cm'),
                     _sa_prop('lamp_cm', 6, 12, sheet='xsa_cm'), _sa_prop('pipes', 13, 6, sheet='xsa_cm'),
                     dict(t='xsa', kind='motes', x=8, y=7, w=14, h=10, n=8, col='255,200,160')])
_sa_r.walls()
_sa_r.fill(1, 7, 10, 7).fill(8, 7, 9, 7, '=')                     # a crawl shelf
_sa_r.fill(11, 13, 13, 13, '.')                                   # a loose board: drop into the Servants' Quarters
_sa_r.fill(1, 1, 15, 2).fill(4, 3, 6, 3, '.')
for _x, _y, _ch in [(3, 6, 'i'), (14, 3, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- Crimson anchors
_sa_cm4 = ROOM('CM4')
_sa_cm4.kw.setdefault('spawns', []).extend([                      # the gallery's east window: out onto the roofs
    _sa_s('door', 49, 10, id='cm_win', to='CM12', toId='cm_win', look='arch'),
    dict(t='xsa', kind='sign', x=49, y=10, text='Rain hammers on a tall window at the end of the gallery. It is unlatched.')])
_sa_cm5 = ROOM('CM5')
_sa_cm5.fill(54, 4, 54, 7, '.')                                   # the cellar's east arch (the East Wing's gate: opened from there)
ROOM('CM3').kw.setdefault('spawns', []).extend([
    _sa_s('door', 17, 9, id='cm_srv', to='CM11', toId='cm_srv', look='hatch'),
    dict(t='xsa', kind='seal', x=17, y=9, door='cm_srv', look='bolt', msg='A servants\' door, flush with the panelling. It is bolted from the other side.')])
