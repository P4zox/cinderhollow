

# ============================================================================================ THORNVEIL WOOD
# Zone (§8.1) x -112..35, y 43..140, under TV2..TV5. Every room joins the next by an edge; the top row sits at y 42 so the
# wing touches the old rooms' floors (y 41).
#   TV10 The Hunter's Trail  -24..31  x 42..57   path: in through a root-hole in TV2's floor; shrine; down into the Canopy
#   TV13 The Coven Circle    -64..-25 x 42..57   gauntlet: west of the trail's far end
#   TV11 Under the Roots    -112..-65 x 42..57   path: up from the Canopy; the gate, then up into TV5 (the loop-back)
#   TV9  The Elder Canopy   -112..-1  x 58..89   grand: shrine; down to the Vine Swing, east to the Glade and the Larder
#   TV16 Witch's Larder        0..15  x 58..71   secret: behind the burning thorn curtain in the Canopy's east wall
#   TV14 Mossbed Glade         0..35  x 72..89   vista: off the Canopy's east floor; the Sprint's goal shaft comes up in it
#   TV12 Vine Swing         -112..-49 x 90..109  parkour: down a root chimney from the Canopy floor
#   TV15 Bramble Sprint      -48..7   x 90..109  trial: east of the Vine Swing; its goal shaft climbs into the Glade

# ---------------------------------------------------------------- TV2 / TV5 (anchors): the way in and the loop-back
ROOM('TV2').fill(8, 11, 10, 13, '.')                            # a root-hole in the Verge's floor, down to the Hunter's Trail
ROOM('TV2').kw.setdefault('spawns', []).append(dict(t='xsa', kind='sign', x=9, y=10, text='A hole among the roots. Hunters\' cord is knotted to them, going down.'))
ROOM('TV5').fill(10, 24, 12, 26, '.').fill(10, 24, 12, 24, '=')   # a lid of woven roots over the hollow below (the wing comes up here)
ROOM('TV5').kw.setdefault('spawns', []).append(dict(t='xsa', kind='sign', x=11, y=23, text='A lid of woven roots. Something hollow lies beneath (↓ + Jump to drop through).'))

# ---------------------------------------------------------------- TV10 The Hunter's Trail (path; the way in)
_sa_r = Room('TV10', 'The Hunter\'s Trail', 'thornveil', -24, 42, 56, 16, indoor=True, needs=['talon'], x3=True, shrine='Snarewood Shrine',
             spawns=[_sa_tv('tree', 6, 11, back=True, v=2), _sa_tv('tree', 28, 11, back=True, v=1), _sa_tv('tree', 50, 11, back=True),
                     _sa_prop('snare', 17, 11), _sa_prop('snare', 26, 11), _sa_prop('snare', 42, 11),
                     _sa_prop('skullpost', 4, 11), _sa_prop('skullpost', 21, 11), _sa_prop('skullpost', 53, 11), _sa_prop('hide', 24, 6),
                     _sa_prop('antlers', 33, 11), _sa_prop('mossrock', 15, 11), _sa_tv('fern', 2, 11), _sa_tv('fern', 45, 11), _sa_tv('fern', 23, 11),
                     _sa_tv('shroom', 51, 8), _sa_tv('ribbons', 49, 11), _sa_tv('vine', 19, 1), _sa_tv('vine', 44, 1), _sa_prop('rootcurtain', 8, 1),
                     _sa_prop('fungus', 38, 11), _sa_prop('nest', 16, 9),
                     dict(t='xsa', kind='motes', x=28, y=6, w=54, h=10, n=12), dict(t='xsa', kind='flies', x=30, y=6, w=24, h=8, n=8),
                     _sa_en('tv_hound', 20, 11), _sa_en('tv_husk', 40, 11), _sa_en('tv_wisp', 28, 4, air=True)])
_sa_r.fill(0, 0, 55, 0).fill(0, 0, 0, 15).fill(55, 0, 55, 15).fill(0, 12, 55, 15)
_sa_r.fill(32, 0, 34, 0, '.').fill(31, 1, 31, 6).fill(35, 1, 35, 6)   # the root-hole from TV2: a wall-jump chimney
_sa_r.fill(31, 9, 35, 9, '=')                                         # the hunters' step under it
_sa_r.fill(0, 8, 0, 11, '.')                                          # -> the Coven Circle (west)
_sa_r.fill(10, 12, 12, 15, '.')                                       # the drop into the Canopy (the path goes on down)
_sa_r.fill(18, 6, 21, 6).fill(22, 7, 27, 7, '=').fill(14, 9, 16, 9, '=').fill(43, 9, 47, 9, '=')   # boughs; the hunter's blind
for _x, _y, _ch in [(47, 11, 'S'), (12, 1, 'r'), (30, 1, 'x'), (50, 1, 'r'), (52, 11, 'k'), (7, 11, 'b')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV13 The Coven Circle (gauntlet)
_sa_W = [[dict(type='tv_hound', x=6, y=11), dict(type='tv_hound', x=24, y=11)],
         [dict(type='tv_husk', x=5, y=11), dict(type='tv_husk', x=26, y=11), dict(type='tv_wisp', x=15, y=5)],
         [dict(type='tv_hound', x=4, y=11), dict(type='tv_husk', x=25, y=11), dict(type='tv_wisp', x=8, y=4), dict(type='tv_wisp', x=22, y=4)],
         [dict(type='xsa_elder_husk', x=15, y=11)]]
_sa_r = Room('TV13', 'The Coven Circle', 'thornveil', -64, 42, 40, 16, indoor=True, needs=['talon'], x3=True, gauntlet=True,
             spawns=[_sa_k('gate', 31, 11, id='gc', open=True),
                     _sa_s('gauntlet', 15, 11, id='coven', look='stones', name='The Coven Circle', gates=['gc'], waves=_sa_W,
                           reward=['emberstone', 'gold']),
                     dict(t='xsa', kind='rite', x=1, y=11, w=30, gauntlet='coven'),
                     _sa_prop('stone_l', 5, 11), _sa_prop('stone_s', 10, 11), _sa_prop('stone_s', 20, 11), _sa_prop('stone_l', 25, 11),
                     _sa_prop('cauldron', 35, 11), _sa_prop('herbs', 35, 5), _sa_prop('shelves', 37, 11),
                     _sa_tv('idol', 2, 11, v=1), _sa_tv('idol', 28, 11), _sa_tv('ribbons', 13, 11), _sa_tv('ribbons', 18, 11),
                     _sa_tv('tree', 8, 11, back=True, v=2), _sa_tv('tree', 23, 11, back=True, v=1), _sa_tv('shroom', 33, 11),
                     dict(t='xsa', kind='motes', x=16, y=6, w=30, h=10, n=12, col='150,255,190')])
_sa_r.fill(0, 0, 39, 0).fill(0, 0, 0, 15).fill(39, 0, 39, 15).fill(0, 12, 39, 15)
_sa_r.fill(39, 8, 39, 11, '.')                                        # <- the Hunter's Trail (east)
_sa_r.fill(31, 1, 31, 7)                                              # the arch over the gate (it reaches this)
_sa_r.fill(32, 1, 38, 4)                                              # the antechamber's low ceiling
_sa_r.fill(7, 7, 10, 7, '=').fill(21, 7, 24, 7, '=')
for _x, _y, _ch in [(6, 1, 'r'), (15, 1, 'x'), (24, 1, 'r'), (36, 11, 'k')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV11 Under the Roots (path; up into TV5)
_sa_r = Room('TV11', 'Under the Roots', 'thornveil', -112, 42, 48, 16, indoor=True, needs=['talon'], x3=True,
             spawns=[_sa_k('gate', 21, 11, id='gR', persist=True),
                     _sa_k('lever', 24, 11, id='lR', targets=['gR'], once=True, skin='wood', msg='The root-gate lifts. A way up to the Mistfell.'),
                     _sa_prop('fungus', 6, 11), _sa_prop('fungus', 19, 11), _sa_prop('fungus', 31, 8), _sa_prop('fungus', 44, 11),
                     _sa_prop('rootcurtain', 11, 2), _sa_prop('rootcurtain', 38, 2), _sa_prop('rootcurtain', 29, 2),
                     _sa_tv('shroom', 9, 11), _sa_tv('shroom', 27, 11), _sa_tv('shroom', 42, 11), _sa_tv('fern', 3, 11), _sa_tv('fern', 33, 11),
                     _sa_prop('skullpost', 26, 11), _sa_prop('antlers', 46, 11), _sa_prop('mossrock', 35, 11),
                     dict(t='xsa', kind='motes', x=24, y=7, w=46, h=10, n=14, col='120,255,170'),
                     _sa_en('tv_husk', 33, 11), _sa_en('tv_wisp', 30, 6, air=True),
                     _sa_s('lore', 5, 11, page='sa_3', look='corpse')])
_sa_r.fill(0, 0, 47, 1).fill(0, 0, 0, 15).fill(47, 0, 47, 15).fill(0, 12, 47, 15)
_sa_r.fill(14, 0, 16, 1, '.').fill(13, 2, 13, 6).fill(17, 2, 17, 6)   # up into TV5: a wall-jump chimney under the root-lid
_sa_r.fill(13, 9, 17, 9, '=')
_sa_r.fill(21, 2, 21, 7)                                              # over the root-gate (the gate reaches it)
_sa_r.fill(38, 12, 40, 15, '.')                                       # down into the Canopy
_sa_r.fill(1, 2, 4, 3).fill(7, 2, 10, 2).fill(24, 2, 27, 3).fill(33, 2, 35, 2).fill(42, 2, 46, 3)   # hanging root-masses
_sa_r.fill(29, 9, 32, 11)                                             # a knot of roots across the tunnel (jump it)
_sa_r.fill(26, 6, 29, 6, '=')
for _x, _y, _ch in [(6, 4, 'r'), (18, 2, 'r'), (31, 3, 'r'), (45, 4, 'r'), (11, 11, 'b')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV9 The Elder Canopy (grand)
_sa_sp = [
    _sa_tv('tree', 10, 27, back=True, v=1), _sa_tv('tree', 26, 27, back=True, v=2), _sa_tv('tree', 44, 27, back=True),
    _sa_tv('tree', 73, 27, back=True, v=1), _sa_tv('tree', 88, 27, back=True, v=2), _sa_tv('tree', 102, 27, back=True),
    _sa_prop('elder', 56, 27, sheet='xsa_elder', back=True),
    _sa_prop('rootarch', 13, 27, sheet='xsa_tvbig', back=True), _sa_prop('rootarch', 33, 27, sheet='xsa_tvbig', back=True), _sa_prop('rootarch', 77, 27, sheet='xsa_tvbig', back=True),
    _sa_prop('rootarch', 95, 27, sheet='xsa_tvbig', back=True),
    _sa_tv('fern', 9, 27), _sa_tv('fern', 23, 27), _sa_tv('fern', 38, 27), _sa_tv('fern', 64, 24), _sa_tv('fern', 86, 27),
    _sa_tv('fern', 101, 27), _sa_tv('shroom', 18, 25), _sa_tv('shroom', 55, 27), _sa_tv('shroom', 72, 24), _sa_tv('shroom', 107, 11),
    _sa_tv('shroom', 22, 10), _sa_tv('shroom', 90, 10), _sa_tv('ribbons', 49, 18), _sa_tv('idol', 62, 18, v=1),
    _sa_tv('vine', 26, 2), _sa_tv('vine', 47, 2), _sa_tv('vine', 69, 2), _sa_tv('vine', 84, 2), _sa_tv('vine', 104, 2),
    _sa_prop('fungus', 57, 27), _sa_prop('fungus', 31, 27), _sa_prop('fungus', 99, 27), _sa_prop('skullpost', 103, 27),
    _sa_prop('nest', 70, 10), _sa_prop('mossrock', 45, 27), _sa_prop('mossrock', 81, 27),
    _sa_prop('rootcurtain', 21, 2), _sa_prop('rootcurtain', 50, 2), _sa_prop('rootcurtain', 88, 2), _sa_prop('rootcurtain', 107, 2),
    _sa_prop('fungus', 44, 18), _sa_prop('fungus', 88, 19), _sa_prop('fungus', 104, 18), _sa_prop('nest', 24, 10), _sa_prop('antlers', 36, 27),
    _sa_tv('shroom', 64, 10), _sa_tv('shroom', 84, 10), _sa_tv('fern', 40, 18), _sa_tv('fern', 67, 18), _sa_tv('ribbons', 100, 18),
    _sa_prop('mossbank', 13, 27), _sa_prop('stones', 92, 27),
    dict(t='xsa', kind='flies', x=60, y=19, w=40, h=14, n=16),
    dict(t='xsa', kind='motes', x=46, y=15, w=108, h=26, n=26),
    dict(t='tv_fog', x=8, y=20, w=18, h=8), dict(t='tv_pod', x=60, y=2), dict(t='tv_pod', x=82, y=2),
    _sa_k('swing', 71, 2, len=6, rope='vine', amp=20), _sa_k('swing', 86, 2, len=7, rope='vine', amp=20),
    _sa_en('tv_hound', 92, 27), _sa_en('tv_husk', 20, 18), _sa_en('tv_husk', 74, 27), _sa_en('tv_wisp', 64, 6, air=True),
    _sa_en('tv_wisp', 20, 15, air=True),
    _sa_s('lore', 55, 27, page='sa_2', look='none'),           # the Elder's heart (the hollow)
]
_sa_r = Room('TV9', 'The Elder Canopy', 'thornveil', -112, 58, 112, 32, indoor=True, needs=['talon'], x3=True, grand=True,
             shrine='Elderroot Shrine', items=['emberstone', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 111, 1).fill(0, 0, 1, 31).fill(110, 0, 111, 31).fill(0, 28, 111, 31)
_sa_r.fill(110, 24, 111, 27, '.')                       # -> Mossbed Glade (east, on the forest floor)
_sa_r.fill(110, 8, 111, 11, '.')                        # -> the Witch's Larder, behind its thorn curtain (east, up in the boughs)
_sa_r.fill(38, 0, 40, 1, '.')                           # up into Under the Roots (a chimney through the leaves)
_sa_r.fill(98, 0, 100, 1, '.')                          # up into the Hunter's Trail
_sa_r.fill(4, 28, 6, 31, '.')                           # down into the Vine Swing
_sa_r.fill(18, 26, 21, 27).fill(64, 25, 71, 27).fill(62, 26, 63, 27).fill(104, 26, 107, 27)   # root mounds
_sa_r.fill(40, 27, 50, 27, '(').fill(84, 27, 88, 27, '(')
_sa_r.fill(12, 2, 14, 22).fill(32, 2, 34, 21).fill(76, 2, 78, 22).fill(94, 2, 96, 22)   # trunks (the low route passes under their root arches)
# the Elder: solid heartwood with a hollow at its roots (thorn curtains either side) and a branch hole through it
_sa_r.fill(52, 2, 59, 27)
_sa_r.fill(53, 22, 58, 27, '.').fill(52, 22, 52, 27, ')').fill(59, 22, 59, 27, ')').fill(52, 22, 59, 22)
_sa_r.fill(52, 8, 59, 10, '.')
_sa_r.fill(52, 7, 59, 7)
for _x0, _x1, _y in [(15, 24, 19), (35, 47, 19), (60, 70, 19), (79, 90, 20), (97, 107, 19),
                     (2, 11, 11), (15, 30, 11), (35, 51, 11), (60, 75, 11), (79, 93, 11), (97, 109, 12)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
for _x0, _x1, _y in [(9, 11, 24), (8, 10, 21), (2, 5, 17), (6, 9, 14),       # west ladder -> high west walkway
                     (27, 30, 24), (23, 26, 22), (36, 38, 23), (44, 47, 23), (21, 23, 16), (26, 28, 14), (40, 42, 15), (46, 49, 16),
                     (61, 63, 23), (66, 68, 16), (61, 63, 13), (72, 74, 22), (82, 84, 24), (86, 89, 17), (91, 93, 14), (99, 101, 23), (104, 107, 16), (102, 104, 21), (100, 102, 14),
                     (60, 62, 6), (64, 67, 4),                                 # the crown of the Elder (emberstone)
                     (41, 43, 8), (38, 40, 5), (38, 40, 2),                    # up to Under the Roots
                     (101, 103, 9), (98, 100, 6), (98, 100, 3)]:               # up to the Hunter's Trail
    _sa_r.fill(_x0, _y, _x1, _y, '=')
for _x, _y, _ch in [(65, 3, 'i'), (57, 27, 'i'), (28, 27, 'S'), (19, 10, 'r'), (43, 18, 'r'), (84, 10, 'r'), (104, 11, 'r'), (9, 23, 'b'), (73, 24, 'k')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('leaves', 0, 0, 112, 2), ('bark', 12, 2, 3, 21), ('bark', 32, 2, 3, 20), ('elder', 52, 2, 8, 26),
          ('bark', 76, 2, 3, 21), ('bark', 94, 2, 3, 21))
_sa_r.kw['reach_open'] = [(52, _y) for _y in range(23, 28)] + [(59, _y) for _y in range(23, 28)]   # the slashable thorn curtains

# ---------------------------------------------------------------- TV16 The Witch's Larder (secret; Ember Dash through the thorn curtain)
_sa_r = Room('TV16', 'The Witch\'s Larder', 'thornveil', 0, 58, 16, 14, indoor=True, needs=['talon', 'emberdash'], x3=True, secret=True,
             chests=['shard'],
             spawns=[_sa_prop('shelves', 5, 11), _sa_prop('shelves', 11, 11), _sa_prop('herbs', 5, 2), _sa_prop('herbs', 9, 2), _sa_prop('herbs', 12, 2),
                     _sa_prop('cauldron', 8, 11), _sa_tv('shroom', 14, 11), _sa_tv('shroom', 2, 11),
                     _sa_s('lore', 3, 11, page='sa_4', look='book'),
                     dict(t='xsa', kind='motes', x=8, y=6, w=14, h=10, n=8, col='255,190,120')])
_sa_r.walls().fill(0, 12, 15, 13)
_sa_r.fill(0, 8, 0, 11, '%')                            # the burning thorn curtain (the Ember Dash goes through)
_sa_r.fill(1, 1, 15, 3).fill(4, 1, 13, 3, '.').fill(4, 1, 13, 1)
for _x, _y, _ch in [(12, 11, 'C'), (6, 4, 'k'), (10, 4, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- TV14 Mossbed Glade (vista)
_sa_r = Room('TV14', 'Mossbed Glade', 'thornveil', 0, 72, 36, 18, indoor=True, needs=['talon'], x3=True, vista=True,
             spawns=[_sa_prop('motheroak', 19, 13, sheet='xsa_oak', back=True),
                     _sa_tv('tree', 3, 13, back=True, v=2), _sa_tv('tree', 30, 13, back=True, v=1),
                     _sa_s('bench', 14, 13, id='bench', view=[19, 7], lore='sa_1'),
                     _sa_prop('mossbank', 10, 13), _sa_prop('mossbank', 27, 13), _sa_prop('stones', 23, 13),
                     _sa_tv('fern', 2, 13), _sa_tv('fern', 8, 13), _sa_tv('fern', 30, 13), _sa_tv('shroom', 17, 13), _sa_tv('shroom', 21, 13),
                     _sa_tv('shroom', 33, 9), _sa_tv('ribbons', 25, 13), _sa_tv('idol', 29, 13, v=1),
                     dict(t='xsa', kind='flies', x=18, y=8, w=32, h=10, n=40, col='190,255,150'),
                     dict(t='xsa', kind='shaft', x=21, y=8, w=6, h=12, col='200,255,200', a=0.1),
                     dict(t='xsa', kind='shaft', x=9, y=8, w=3, h=12, col='200,255,200', a=0.07),
                     dict(t='xsa', kind='motes', x=18, y=8, w=32, h=12, n=16, col='220,255,200')])
_sa_r.fill(0, 0, 35, 1).fill(0, 0, 0, 17).fill(35, 0, 35, 17).fill(0, 14, 35, 17)
_sa_r.fill(0, 10, 0, 13, '.')                                   # <- the Elder Canopy (west, on the forest floor)
_sa_r.fill(4, 14, 6, 17, '.')                                   # the Bramble Sprint's goal shaft comes up here
_sa_r.fill(31, 12, 34, 13).fill(32, 10, 34, 11)                 # a mossy bank against the east wall
for _x, _y, _ch in [(10, 2, 'r'), (25, 2, 'r'), (4, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('leaves', 0, 0, 36, 2))

# ---------------------------------------------------------------- TV12 Vine Swing (parkour)
_sa_sp = [_sa_tv('tree', 12, 15, back=True, v=1), _sa_tv('tree', 33, 15, back=True, v=2), _sa_tv('tree', 60, 10, back=True),
          _sa_prop('thornbed', 20, 16), _sa_prop('thornbed', 44, 16),
          _sa_tv('fern', 9, 15), _sa_tv('fern', 58, 10), _sa_tv('shroom', 2, 15), _sa_tv('shroom', 28, 10), _sa_prop('nest', 43, 6),
          _sa_prop('fungus', 61, 10), _sa_prop('rootcurtain', 18, 2), _sa_prop('rootcurtain', 38, 2), _sa_prop('rootcurtain', 51, 2), _sa_prop('skullpost', 9, 15),
          dict(t='xsa', kind='motes', x=32, y=9, w=60, h=14, n=16), dict(t='xsa', kind='flies', x=34, y=8, w=20, h=8, n=6),
          dict(t='tv_fog', x=12, y=13, w=42, h=4),
          _sa_en('tv_wisp', 36, 5, air=True)]
for _i, (_x, _ln) in enumerate([(14, 9), (21, 9), (34, 8), (41, 9), (49, 8)]):
    _sa_sp.append(_sa_k('swing', _x, 2, len=_ln, rope='vine', amp=24, period=2.6, phase=_i * 0.3))
_sa_sp += [_sa_k('crumble', 36, 12, w=2, delay=0.45, respawn=2.5)]
_sa_r = Room('TV12', 'Vine Swing', 'thornveil', -112, 90, 64, 20, indoor=True, needs=['talon'], x3=True, parkour=True,
             items=['seed'], spawns=_sa_sp)
_sa_r.fill(0, 0, 63, 1).fill(0, 0, 1, 19).fill(62, 0, 63, 19).fill(0, 16, 63, 19)
_sa_r.fill(4, 0, 6, 1, '.')                                      # up into the Elder Canopy (a chimney through the leaves)
for _x0, _y in [(7, 13), (2, 10), (7, 7), (4, 4)]:
    _sa_r.fill(_x0, _y, _x0 + 2, _y, '=')                        # the west ladder of branches
_sa_r.fill(11, 16, 55, 17, '.').fill(11, 17, 55, 17, '^')        # the thorn pit
_sa_r.fill(27, 11, 28, 17)                                       # a mossy stump halfway (rest)
_sa_r.fill(11, 2, 13, 2, 'v').fill(30, 2, 32, 2, 'v').fill(53, 2, 55, 2, 'v')   # thorn-hung boughs: don't swing too high
_sa_r.fill(44, 5, 46, 5, '=')                                    # a high nest (seed): release a vine at the top of its arc
_sa_r.fill(56, 11, 61, 19)                                       # the east landing, up at the Bramble Sprint's door
_sa_r.fill(62, 7, 63, 10, '.')                                   # -> Bramble Sprint (east)
for _x, _y, _ch in [(45, 4, 'i'), (8, 2, 'r'), (25, 2, 'x'), (46, 2, 'r'), (59, 2, 'r'), (60, 10, 'k')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('leaves', 0, 0, 64, 2), ('bark', 27, 11, 2, 6))

# ---------------------------------------------------------------- TV15 Bramble Sprint (trial: a pogo run; c_x3_thorn)
# Start on the ledge by the west door; walk off (don't jump: the thorn ceiling), pogo across the first bramble field,
# hop the crumbling boughs under the low thorns, pogo up the bramble-crowned stumps under the thorn bough, land on
# the goal bough. The goal nook climbs out into Mossbed Glade (leaving the room ends a trial, so it can't be skipped).
_sa_sp = [_sa_s('trial', 3, 10, id='sprint', par=9, reward='c_x3_thorn', region='Thornveil', name='Bramble Sprint'),
          _sa_s('trial_goal', 49, 6, trial='sprint'),
          _sa_tv('tree', 10, 15, back=True, v=1), _sa_tv('tree', 27, 15, back=True), _sa_tv('tree', 45, 5, back=True, v=2),
          _sa_tv('shroom', 5, 10), _sa_tv('fern', 1, 10), _sa_tv('shroom', 53, 6), _sa_tv('fern', 46, 6),
          dict(t='xsa', kind='motes', x=28, y=9, w=54, h=14, n=16),
          _sa_k('crumble', 22, 12, w=2, delay=0.35, respawn=2.5), _sa_k('crumble', 26, 12, w=2, delay=0.35, respawn=2.5),
          _sa_k('crumble', 30, 12, w=2, delay=0.35, respawn=2.5)]
_sa_r = Room('TV15', 'Bramble Sprint', 'thornveil', -48, 90, 56, 20, indoor=True, needs=['talon'], x3=True, trial=True, spawns=_sa_sp)
_sa_r.fill(0, 0, 55, 1).fill(0, 0, 0, 19).fill(55, 0, 55, 19).fill(0, 16, 55, 19)
_sa_r.fill(0, 7, 0, 10, '.')                                     # <- the Vine Swing (west, rows 7..10)
_sa_r.fill(0, 11, 6, 15)                                         # the start ledge
_sa_r.fill(7, 15, 43, 15, '(')                                   # the bramble floor
_sa_r.fill(9, 9, 16, 9, 'v').fill(22, 7, 31, 7, 'v')             # thorn-hung boughs: walk off the ledge, hop low
_sa_r.fill(19, 12, 20, 15)                                       # a bare stump to catch your breath
_sa_r.fill(32, 12, 33, 15).fill(32, 11, 33, 11, '(')             # bramble-crowned stumps: pogo up them
_sa_r.fill(36, 10, 37, 15).fill(36, 9, 37, 9, '(')
_sa_r.fill(40, 10, 41, 15).fill(40, 9, 41, 9, '(')
_sa_r.fill(35, 3, 42, 3, 'v')                                     # a thorn bough over the crowned stumps: pogo no higher than you must
_sa_r.fill(44, 7, 55, 15)                                        # the goal bough
_sa_r.fill(52, 0, 54, 6, '.').fill(51, 0, 51, 4)                 # the root shaft up into Mossbed Glade
_sa_skins(_sa_r, ('leaves', 0, 0, 51, 2), ('bark', 19, 12, 2, 4), ('bark', 32, 12, 2, 4), ('bark', 36, 10, 2, 6), ('bark', 40, 10, 2, 6))
