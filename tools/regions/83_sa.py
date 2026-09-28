# ============================================================ EXPANSION 3 — agent SA: Thornveil Wood, Drowned Barrows, Crimson Manor
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, free_spot). Engine: web/src/53_sa.js.
# Art: art/gen_xsa*.py -> assets/xsa_*. Every module-level name here is prefixed _sa.
#
# Custom spawns (53_sa.js): xsa, kind = prop | skins | frontpaint | flies | motes | shaft | bubbles | pearls | petals | leak |
#   sign | rite | tide | floodgates | trialgate | gaze | bookcase | keygate | glasshouse | piano
#   prop      : decor sprite from the xsa_* sheets (sheet, tag), back=True paints it into the room's back layer
#   skins     : repaints solid cells of the front layer (bark trunks, leaf canopy, roof slates, glass) — _sa_skins()
#   bookcase  : a false bookcase over wall cells that are open in the map; solid until struck three times (a secret)
#   keygate   : a KM gate held shut until the three study keys are turned in it
# Wings (docs/EXPANSION3_CONTRACT.md §8: walkable, edge to edge, no doors):
#   Thornveil: TV2 (a root-hole in the floor) -> TV10 -> TV9 -> TV11 -> TV5 (a gate in TV11 opens the shortcut)
#   Barrows:   DB3 (a hole in the roof) -> DB11 -> DB10 -> DB12 -> DB4 (a gate in DB12 opens the shortcut).
#              W4, the drowned shaft from K2 down to DB1, is rebuilt here: side rooms open off it (it's the region's spine)
#   Crimson:   CM4 (the gallery's east window) -> CM9 -> CM11 -> CM10 -> CM8 (a gate in CM10 opens the shortcut)


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
_sa_r.fill(0, 8, 0, 11, '.').fill(1, 8, 1, 11, '%')   # one column in from the edge: a veil on a room's edge traps you at the seam                            # the burning thorn curtain (the Ember Dash goes through)
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


# ============================================================================================ THE DROWNED BARROWS
# Zone (§8.1) x 253..379, y 29..117, between the Cathedral above and DB1..DB5 below. W4 — the drowned shaft from K2's grate
# down to DB1 — runs through the middle of it (x 336..343) and is rebuilt here as the wing's spine: the side rooms open
# off it. Rooms on the old rooms' roofs reach down to y 119/121 to meet them edge to edge.
#   W4   The Drowned Shaft    336..343 x 28..117   the region's link (K2 -> DB1), dressed; openings to DB14, DB15, DB13, DB16, DB10
#   DB11 Grave Causeway       289..335 x 108..121  path: in through the roof of DB3 (the Ossuary of the Tide)
#   DB10 The Sunken Nave      253..335 x 68..107   grand: the east stair up from the Causeway, the rafters, the west stair down
#   DB12 Tomb Galleries       253..288 x 108..119  path: shrine; the gate, then down through DB4's roof (the loop-back)
#   DB16 Breathless Dive      272..335 x 44..67    trial: its dry corridor opens into W4
#   DB14 The Floodgates       344..379 x 29..52    puzzle: its walkway opens into W4; the drain falls into the Lagoon
#   DB15 Pearl Lagoon         344..379 x 53..72    vista: under the Floodgates' drain; a gate from its shelf into W4
#   DB13 Tide Steps           344..379 x 73..96    parkour: off W4 at the Nave's height
#   DB17 The Drowned Bell     356..371 x 97..110   secret: down the bricked-up well in the Tide Steps' floor
_SA_WL = '"'

# ---------------------------------------------------------------- the old rooms: the drowned shaft's foot, the roof of DB3, DB4
_sa_db1 = ROOM('DB1')                                            # the shaft now meets DB1 two columns east (x 341..342), so the
_sa_db1.fill(3, 0, 4, 3).fill(5, 0, 6, 3, '.')                   # generated W4 (K2's grate is at x 339..340) steps aside for ours
_sa_db3 = ROOM('DB3')
_sa_db3.fill(17, 0, 19, 1, '.')                                  # a hole in the Ossuary's roof, up to the Grave Causeway
_sa_db3.fill(16, 7, 17, 7, '=').fill(18, 4, 19, 4, '=')
_sa_db3.kw.setdefault('spawns', []).append(dict(t='xsa', kind='sign', x=18, y=9, text='Cold air falls through a hole in the roof. The tide-keepers\' causeway lies above.'))
_sa_db4 = ROOM('DB4')
_sa_db4.fill(15, 0, 16, 0, '.').fill(17, 0, 18, 0, '=')          # up through the Chapels' roof into the Tomb Galleries
_sa_db4.fill(15, 9, 16, 9, '=').fill(17, 6, 18, 6, '=').fill(15, 3, 16, 3, '=')

# ---------------------------------------------------------------- W4 The Drowned Shaft (the link from K2 to DB1, rebuilt)
_SA_W4_SIDE = {6: 'E', 21: 'W', 36: 'E', 51: 'W', 63: 'E'}      # ledge rows that are the floors of side openings
_sa_sp = [_sa_db('lamp', 5, 5), _sa_db('lamp', 2, 20), _sa_db('lamp', 5, 35), _sa_db('lamp', 2, 50), _sa_db('lamp', 5, 62),
          _sa_prop('chainlamp', 4, 1, sheet='xsa_db'), _sa_prop('chainlamp', 3, 28, sheet='xsa_db'), _sa_prop('chainlamp', 4, 70, sheet='xsa_db'),
          _sa_prop('weeds', 5, 86, sheet='xsa_db'), _sa_db('bones', 2, 44),
          dict(t='xsa', kind='leak', x=2, y=1), dict(t='xsa', kind='leak', x=5, y=40), dict(t='xsa', kind='leak', x=2, y=66),
          dict(t='xsa', kind='motes', x=4, y=45, w=6, h=88, n=20, col='140,230,215')]
_sa_r = Room('W4', 'The Drowned Shaft', 'barrows', 336, 28, 8, 90, indoor=True, x3=True, world_link=True, needs=[], spawns=_sa_sp)
_sa_r.fill(0, 0, 7, 0).fill(0, 0, 0, 89).fill(7, 0, 7, 89).fill(0, 89, 7, 89)
_sa_r.fill(3, 0, 4, 0, '.')                                      # <- K2's grate
_sa_r.fill(5, 89, 6, 89, '.')                                    # -> DB1
for _i, _y in enumerate(range(87, 2, -3)):                       # zigzag one-way ledges, three rows apart (the W-shaft standard)
    _side = _SA_W4_SIDE.get(_y, 'E' if _i % 2 == 0 else 'W')
    if _side == 'E': _sa_r.fill(4, _y, 6, _y, '=')
    else: _sa_r.fill(1, _y, 3, _y, '=')
_sa_r.fill(7, 2, 7, 5, '.')                                      # -> the Floodgates' walkway (east)
_sa_r.fill(0, 18, 0, 20, '.')                                    # -> the Breathless Dive's corridor home (west)
_sa_r.fill(7, 32, 7, 35, '.')                                    # -> Pearl Lagoon (east, behind its gate)
_sa_r.fill(0, 47, 0, 50, '.')                                    # -> the Sunken Nave's east triforium (west)
_sa_r.fill(7, 59, 7, 62, '.')                                    # -> the Tide Steps (east)

# ---------------------------------------------------------------- DB11 Grave Causeway (path; in through DB3's roof)
_sa_r = Room('DB11', 'Grave Causeway', 'barrows', 289, 108, 47, 14, indoor=True, needs=['talon'], x3=True, items=['gold'],
             spawns=[_sa_db('lamp', 7, 10), _sa_db('lamp', 24, 7), _sa_db('lamp', 44, 10), _sa_db('bones', 12, 10), _sa_db('statue', 37, 3),
                     _sa_prop('gravecross', 18, 7, sheet='xsa_db'), _sa_prop('gravestone', 16, 7, sheet='xsa_db'), _sa_prop('cairn', 29, 7, sheet='xsa_db'),
                     _sa_prop('gravestone', 31, 7, sheet='xsa_db', flip=True), _sa_prop('weeds', 22, 12, sheet='xsa_db'),
                     _sa_prop('weeds', 25, 12, sheet='xsa_db'), _sa_prop('chainlamp', 21, 2, sheet='xsa_db'), _sa_prop('chainlamp', 9, 2, sheet='xsa_db'),
                     dict(t='xsa', kind='leak', x=11, y=2), dict(t='xsa', kind='leak', x=25, y=2), dict(t='xsa', kind='leak', x=31, y=2),
                     dict(t='xsa', kind='motes', x=24, y=6, w=46, h=8, n=12, col='140,230,215'),
                     _sa_en('db_pilgrim', 17, 7), _sa_en('db_pilgrim', 42, 10), _sa_en('db_eel', 12, 12)])
_sa_r.fill(0, 0, 46, 1).fill(0, 0, 0, 13).fill(46, 0, 46, 13).fill(0, 13, 46, 13)
_sa_r.fill(1, 11, 9, 12).fill(39, 11, 45, 12)                     # the landings
_sa_r.fill(10, 11, 38, 12, _SA_WL)                                # black water between the mounds
_sa_r.fill(14, 10, 21, 12).fill(15, 9, 20, 9).fill(16, 8, 19, 8)  # a burial mound
_sa_r.fill(26, 10, 33, 12).fill(27, 9, 32, 9).fill(28, 8, 31, 8)  # a second mound
_sa_r.fill(23, 11, 24, 12)                                        # a broken causeway pier
_sa_r.fill(36, 4, 38, 12).fill(34, 6, 35, 6, '=')                  # the barrow-tomb, a rotten bier-plank up onto it
_sa_r.fill(2, 11, 4, 13, '.')                                     # <- the hole in DB3's roof
_sa_r.fill(41, 0, 44, 1, '.')                                     # up into the Sunken Nave's east stair
_sa_r.fill(43, 8, 44, 8, '=').fill(39, 5, 40, 5, '=').fill(43, 2, 44, 2, '=')
for _x, _y, _ch in [(37, 3, 'i'), (6, 2, 'x'), (29, 2, 'x'), (14, 2, 'r'), (45, 2, 'r')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB10 The Sunken Nave (grand)
# Dry route: up the east stair from the Causeway to the east triforium (shrine; W4 opens here), west over the rafters and
# the Drowned Saint's head to the west triforium, down the west stair to the Tomb Galleries. Swim route: down among the
# drowned pews to the altar (emberstone), the air pocket in the east chapel. Clear water, so the church reads from above.
_sa_sp = [_sa_prop('rosewin', 41, 13, sheet='xsa_rosewin', back=True, alpha=0.85, dy=-16),
          _sa_prop('saint', 41, 13, sheet='xsa_saint', back=True, dy=384),
          dict(t='xsa', kind='frontpaint', x=41, y=13, dy=384, sheet='xsa_saint', tag='saint', rect=[36, 13, 11, 25]),
          _sa_db('window', 11, 10), _sa_db('window', 70, 10), _sa_db('lamp', 13, 10), _sa_db('lamp', 74, 10), _sa_db('lamp', 8, 10),
          _sa_db('statue', 78, 10), _sa_db('bones', 10, 10), _sa_db('bell', 26, 3), _sa_db('bell', 58, 3),
          _sa_prop('pew', 12, 37, sheet='xsa_db'), _sa_prop('pew', 21, 37, sheet='xsa_db'), _sa_prop('pew', 29, 37, sheet='xsa_db'),
          _sa_prop('pew', 51, 37, sheet='xsa_db'), _sa_prop('pew', 48, 37, sheet='xsa_db'),
          _sa_prop('weeds', 24, 37, sheet='xsa_db'), _sa_prop('weeds', 33, 37, sheet='xsa_db'), _sa_prop('weeds', 55, 37, sheet='xsa_db'),
          _sa_prop('weeds', 69, 37, sheet='xsa_db'), _sa_prop('candles_db', 58, 33, sheet='xsa_db'), _sa_prop('candles_db', 73, 17, sheet='xsa_db'), _sa_prop('pearlclam', 66, 37, sheet='xsa_db'),
          _sa_prop('chainlamp', 21, 3, sheet='xsa_db'), _sa_prop('chainlamp', 50, 3, sheet='xsa_db'), _sa_prop('chainlamp', 31, 3, sheet='xsa_db'),
          dict(t='xsa', kind='shaft', x=41, y=11, w=6, h=16, col='170,240,235', a=0.08, lean=0.2),
          dict(t='xsa', kind='shaft', x=24, y=13, w=3, h=20, col='170,240,235', a=0.05, lean=0.3),
          dict(t='xsa', kind='shaft', x=58, y=13, w=3, h=20, col='170,240,235', a=0.05, lean=0.3),
          dict(t='xsa', kind='bubbles', x=27, y=28, w=30, h=16, n=14), dict(t='xsa', kind='bubbles', x=57, y=28, w=16, h=16, n=10),
          dict(t='xsa', kind='motes', x=41, y=8, w=76, h=12, n=20, col='150,230,220'),
          _sa_en('db_eel', 26, 30), _sa_en('db_eel', 58, 32), _sa_en('db_pilgrim', 12, 10), _sa_en('db_barnacle', 80, 10)]
_sa_r = Room('DB10', 'The Sunken Nave', 'barrows', 253, 68, 83, 40, indoor=True, needs=['talon', 'tidebreath'], x3=True, grand=True, clear=True,
             shrine='Saint\'s Watch Shrine', chests=['emberstone'], items=['gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 82, 2).fill(0, 0, 1, 39).fill(81, 0, 82, 39).fill(0, 38, 82, 39)
_sa_r.fill(8, 18, 73, 37, _SA_WL)                                 # the drowned nave
# the west stair (dry, behind the pillar wall) down to the Tomb Galleries
_sa_r.fill(6, 13, 7, 37).fill(2, 38, 5, 39, '.')
for _i, _y in enumerate(range(39, 11, -3)):
    _sa_r.fill(4 if _i % 2 == 0 else 2, _y, 5 if _i % 2 == 0 else 3, _y, '=')
# the east stair (dry, behind its own wall) up from the Grave Causeway
_sa_r.fill(74, 13, 74, 37).fill(77, 38, 80, 39, '.')
for _i, _y in enumerate(range(39, 11, -3)):
    _sa_r.fill(79 if _i % 2 == 0 else 75, _y, 80 if _i % 2 == 0 else 76, _y, '=')
# the triforium galleries (row 11) and the rafters between them
_sa_r.fill(6, 11, 16, 12).fill(69, 11, 74, 12).fill(79, 11, 80, 12)
_sa_r.fill(81, 7, 82, 10, '.')                                    # -> the Drowned Shaft (W4) from the east triforium
for _x0, _x1 in [(19, 24), (28, 33), (48, 52), (57, 61), (64, 66)]:   # (and two low beams either side of the Saint, row 12)
    _sa_r.fill(_x0, 11, _x1, 11, '=')
for _x in (17, 34, 53, 62):
    _sa_r.fill(_x, 13, _x + 1, 37)
# the Drowned Saint: plinth under water, shoulders and head above it (a perch in the middle of the crossing)
_sa_r.fill(36, 33, 46, 37).fill(38, 15, 44, 32)
_sa_r.fill(39, 14, 43, 14, '=').fill(34, 12, 36, 12, '=').fill(45, 12, 47, 12, '=')
# the altar (under water)
_sa_r.fill(56, 34, 60, 37)
_sa_r.fill(69, 13, 73, 15).fill(69, 16, 73, 17, '.').fill(69, 18, 73, 18)   # the east chapel's alcove (the reliquary) over the water
# vault ribs
for _x in (16, 33, 52, 61):
    _sa_r.fill(_x, 3, _x + 2, 3)
_sa_r.fill(40, 3, 42, 4)
for _x, _y, _ch in [(71, 17, 'C'), (41, 13, 'i'), (72, 10, 'S'), (9, 10, 'k'), (66, 10, 'k'), (3, 3, 'x'), (27, 3, 'x'), (48, 3, 'x'), (78, 3, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB12 Tomb Galleries (path; the gate, down into DB4)
_sa_r = Room('DB12', 'Tomb Galleries', 'barrows', 253, 108, 36, 12, indoor=True, needs=['talon'], x3=True, shrine='Tombwarden Shrine',
             items=['gold'],
             spawns=[_sa_k('gate', 12, 9, id='gG', persist=True),
                     _sa_k('lever', 10, 9, id='lG', targets=['gG'], once=True, skin='stone', msg='The tomb-gate grinds up. A way down to the Sunken Chapels.'),
                     _sa_prop('tomb', 22, 9, sheet='xsa_db'), _sa_prop('tomb_leak', 27, 9, sheet='xsa_db'), _sa_prop('tomb', 32, 9, sheet='xsa_db'),
                     _sa_prop('tomb_leak', 5, 9, sheet='xsa_db'),
                     _sa_db('lamp', 1, 9), _sa_db('lamp', 20, 9), _sa_db('bones', 30, 9),
                     dict(t='xsa', kind='leak', x=27, y=4, pool=True), dict(t='xsa', kind='leak', x=5, y=4, pool=True), dict(t='xsa', kind='leak', x=24, y=1),
                     dict(t='xsa', kind='motes', x=18, y=5, w=34, h=8, n=10, col='140,230,215'),
                     _sa_s('lore', 25, 9, page='sa_8', look='tablet'),
                     _sa_en('db_barnacle', 23, 9), _sa_en('db_pilgrim', 31, 9, hidden=True)])
_sa_r.fill(0, 0, 35, 0).fill(0, 0, 0, 11).fill(35, 0, 35, 11).fill(0, 10, 35, 11)
_sa_r.fill(2, 0, 5, 0, '.')                                       # <- the Sunken Nave's west stair
_sa_r.fill(2, 7, 3, 7, '=').fill(4, 4, 5, 4, '=').fill(2, 1, 3, 1, '=')
_sa_r.fill(12, 1, 12, 5)                                          # over the tomb-gate (the gate reaches it)
_sa_r.fill(15, 10, 18, 11, '.')                                   # down through DB4's roof (the loop-back)
_sa_r.fill(30, 5, 34, 5, '=')
for _x, _y, _ch in [(6, 9, 'S'), (33, 4, 'i'), (9, 1, 'x'), (27, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB16 Breathless Dive (trial: one breath, c_x3_lung)
# The sigil stands on the landing; the course runs down into sealed water (no air anywhere on it), east along the upper
# run past the swinging blades, down the spiked throat, back under it along the lower run and up the east shaft into the
# goal chamber. The dry corridor over the top runs from W4 to the landing; its gate is shut while a trial runs.
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
_sa_r = Room('DB16', 'Breathless Dive', 'barrows', 272, 44, 64, 24, indoor=True, needs=['tidebreath'], x3=True, trial=True, spawns=_sa_sp)
_sa_r.fill(0, 0, 63, 0).fill(0, 0, 0, 23).fill(63, 0, 63, 23).fill(0, 23, 63, 23)
_sa_r.fill(1, 6, 6, 9, '.')
_sa_r.fill(1, 10, 6, 22)                                          # the landing (the sigil)
_sa_r.fill(5, 10, 6, 14, _SA_WL)                                  # the dive pool: open to the air, then the lid
_sa_r.fill(7, 5, 62, 10)                                          # the lid over the course: no air under it
_sa_r.fill(3, 2, 55, 4, '.').fill(7, 5, 55, 5)                    # the dry corridor (over the lid)
_sa_r.fill(1, 1, 2, 5).fill(3, 5, 6, 5, '=')                      # its floor over the landing: a one-way drop at cols 3..6
_sa_r.fill(7, 11, 62, 22, _SA_WL)                                 # the sealed water
_sa_r.fill(7, 15, 41, 17)                                         # floor of the upper run / roof of the lower
_sa_r.fill(46, 11, 52, 17)                                        # a block the upper run ends against
_sa_r.fill(7, 18, 37, 22)                                         # dead water under the upper run: solid
_sa_r.fill(38, 21, 52, 22)                                        # the lower run's floor
_sa_r.fill(53, 11, 55, 22).fill(53, 18, 55, 21, _SA_WL)           # the east wall of the throat; the lower run passes under it
_sa_r.fill(56, 9, 58, 20, _SA_WL).fill(59, 9, 62, 22).fill(56, 21, 58, 22)   # the east shaft up to the goal chamber
_sa_r.fill(56, 6, 62, 7, '.').fill(56, 8, 58, 8, '.')             # the goal chamber (air; the shaft surfaces at row 9)
_sa_r.fill(56, 2, 62, 5, '.').fill(56, 5, 58, 5, '=')             # the climb up into the corridor
_sa_r.fill(63, 2, 63, 4, '.')                                     # -> the Drowned Shaft (W4)
_sa_r.fill(13, 11, 14, 11, 'v').fill(26, 11, 27, 11, 'v').fill(38, 14, 40, 14, '^')   # teeth
_sa_r.fill(42, 15, 45, 17, _SA_WL)                                # the throat
_sa_r.fill(41, 20, 41, 20, '^').fill(47, 18, 47, 18, 'v')
_sa_r.fill(38, 18, 41, 20, _SA_WL)
for _x, _y, _ch in [(12, 1, 'x'), (40, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB14 The Floodgates (puzzle)
# Three basins (A, B, C) under a dry walkway; a wheel on each basin's floor. A wheel turns only from dry ground, and each one
# turns two floodgates: A's wheel swaps A and B, B's swaps B and C, C's swaps C and A (the pipes on the wall show which).
# Start: A dry, B and C full. B's high niche holds the chest (B full); the drain gate at the foot of C opens only while C
# is dry, and the drain drops into the Pearl Lagoon. (53_sa.js owns the rule: kind 'floodgates'.)
_sa_sp = [dict(t='xsa', kind='floodgates', x=9, y=4, basins=['lA', 'lB', 'lC'], wheels=['wA', 'wB', 'wC'], start=[0, 1, 1], drain='gX',
               pairs=[['lA', 'lB'], ['lB', 'lC'], ['lC', 'lA']]),
          _sa_k('level', 1, 7, w=10, h=15, states=[22, 7], fluid='water', id='lA', speed=4),
          _sa_k('level', 12, 7, w=11, h=15, states=[22, 7], fluid='water', id='lB', speed=4),
          _sa_k('level', 24, 7, w=7, h=15, states=[22, 7], fluid='water', id='lC', speed=4),
          _sa_k('lever', 4, 21, id='wA', skin='stone', msg=''), _sa_k('lever', 16, 21, id='wB', skin='stone', msg=''),
          _sa_k('lever', 27, 21, id='wC', skin='stone', msg=''),
          _sa_k('gate', 31, 21, id='gX', persist=False),
          _sa_s('lore', 20, 4, page='sa_6', look='tablet'),
          _sa_db('lamp', 2, 4), _sa_db('lamp', 11, 4), _sa_db('lamp', 33, 4), _sa_prop('chainlamp', 17, 1, sheet='xsa_db'),
          _sa_prop('sluice', 7, 21, sheet='xsa_db'), _sa_prop('sluice', 19, 21, sheet='xsa_db'), _sa_prop('sluice', 25, 21, sheet='xsa_db'),
          dict(t='xsa', kind='motes', x=18, y=3, w=32, h=4, n=8, col='150,230,220')]
_sa_r = Room('DB14', 'The Floodgates', 'barrows', 344, 29, 36, 24, indoor=True, needs=['talon', 'tidebreath'], x3=True, puzzle=True,
             chests=['emberstone'], spawns=_sa_sp)
_sa_r.fill(0, 0, 35, 0).fill(0, 0, 0, 23).fill(35, 0, 35, 23).fill(0, 22, 35, 23)
_sa_r.fill(0, 1, 0, 4, '.')                                       # <- the Drowned Shaft (W4), at walkway height
_sa_r.fill(1, 5, 34, 6)                                           # the walkway
_sa_r.fill(4, 5, 6, 6, '.').fill(16, 5, 18, 6, '.').fill(26, 5, 28, 6, '.')   # a hatch over each basin
_sa_r.fill(11, 7, 11, 21).fill(23, 7, 23, 21)                     # the basin walls
_sa_r.fill(31, 7, 34, 17)                                         # C's east wall; the drain tunnel runs under it
_sa_r.fill(33, 22, 34, 23, '.')                                   # the drain: down into the Pearl Lagoon
_sa_r.fill(12, 10, 14, 10).put(13, 9, 'C')                        # B's niche (reach it only by swimming up)
for _x, _y, _ch in [(9, 1, 'x'), (26, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB15 Pearl Lagoon (vista)
_sa_r = Room('DB15', 'Pearl Lagoon', 'barrows', 344, 53, 36, 20, indoor=True, needs=['talon', 'tidebreath'], x3=True, vista=True, clear=True,
             spawns=[_sa_k('gate', 2, 10, id='gL', persist=True),
                     _sa_k('lever', 4, 10, id='lL', targets=['gL'], once=True, skin='stone', msg='The shelf-gate lifts onto the drowned shaft.'),
                     _sa_s('bench', 8, 10, id='bench', view=[21, 12], lore='sa_5'),
                     _sa_prop('lagoonback', 22, 17, sheet='xsa_lagoon', back=True, dy=48),
                     _sa_prop('pearlclam', 15, 17, sheet='xsa_db'), _sa_prop('pearlclam', 26, 17, sheet='xsa_db', flip=True), _sa_prop('pearlclam', 20, 17, sheet='xsa_db'),
                     _sa_prop('weeds', 13, 17, sheet='xsa_db'), _sa_prop('weeds', 18, 17, sheet='xsa_db'), _sa_prop('weeds', 24, 17, sheet='xsa_db'),
                     _sa_prop('weeds', 31, 17, sheet='xsa_db'), _sa_db('statue', 29, 17), _sa_prop('candles_db', 10, 10, sheet='xsa_db'),
                     _sa_prop('coral', 16, 17, sheet='xsa_db'), _sa_prop('coral', 22, 17, sheet='xsa_db'), _sa_prop('coral', 33, 17, sheet='xsa_db'),
                     dict(t='xsa', kind='shaft', x=20, y=9, w=5, h=16, col='190,250,245', a=0.11, lean=0.25),
                     dict(t='xsa', kind='shaft', x=28, y=9, w=3, h=16, col='190,250,245', a=0.08, lean=0.25),
                     dict(t='xsa', kind='shaft', x=14, y=9, w=2, h=16, col='190,250,245', a=0.06, lean=0.25),
                     dict(t='xsa', kind='pearls', x=23, y=14, w=22, h=8, n=22),
                     dict(t='xsa', kind='bubbles', x=23, y=15, w=22, h=6, n=14),
                     dict(t='xsa', kind='motes', x=18, y=6, w=32, h=8, n=16, col='200,250,245'),
                     _sa_prop('chainlamp', 16, 2, sheet='xsa_db'), _sa_prop('rootcurtain', 22, 2), _sa_prop('rootcurtain', 9, 3),
                     dict(t='xsa', kind='leak', x=25, y=2, pool=True), dict(t='xsa', kind='leak', x=12, y=2),
                     _sa_prop('weeds', 6, 10, sheet='xsa_db'), _sa_db('bones', 3, 10)])
_sa_r.fill(0, 0, 35, 1).fill(0, 0, 0, 19).fill(35, 0, 35, 19).fill(0, 18, 35, 19)
_sa_r.fill(33, 0, 34, 1, '.')                                     # <- the Floodgates' drain, falling from the roof
_sa_r.fill(0, 7, 0, 10, '.')                                      # -> the Drowned Shaft (W4), behind the shelf-gate
_sa_r.fill(1, 11, 11, 17)                                         # the grotto shelf (the bench) and the rock under it
_sa_r.fill(2, 2, 2, 6).fill(1, 2, 6, 3)                           # rock over the shelf-gate (the gate reaches it)
_sa_r.fill(12, 12, 34, 17, _SA_WL)                                # the lagoon
_sa_r.fill(30, 9, 32, 9, '=').fill(33, 6, 34, 6, '=').fill(33, 3, 34, 3, '=')   # rungs up to the drain
_sa_r.fill(30, 2, 34, 2).fill(33, 2, 34, 2, '.')
for _x, _y, _ch in [(20, 2, 'r'), (27, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB13 Tide Steps (parkour: the tide rises and falls)
# kw tide = the low-water row; 53_sa.js swings the line between tide and tide_hi (four-row steps: float up at high water).
_sa_r = Room('DB13', 'Tide Steps', 'barrows', 344, 73, 36, 24, indoor=True, needs=['talon', 'tidebreath'], x3=True, parkour=True,
             tide=20, tide_hi=6, tide_period=16, items=['seed'],
             spawns=[dict(t='xsa', kind='tide', x=2, y=17),
                     _sa_db('lamp', 3, 17), _sa_db('lamp', 33, 3), _sa_db('statue', 30, 3), _sa_db('bones', 20, 10),
                     _sa_prop('tidemark', 7, 18, sheet='xsa_db'), _sa_prop('tidemark', 13, 14, sheet='xsa_db'), _sa_prop('tidemark', 24, 6, sheet='xsa_db'),
                     _sa_prop('weeds', 8, 18, sheet='xsa_db'), _sa_prop('weeds', 21, 10, sheet='xsa_db'), _sa_prop('weeds', 25, 6, sheet='xsa_db'),
                     _sa_prop('chainlamp', 11, 2, sheet='xsa_db'), _sa_prop('chainlamp', 27, 2, sheet='xsa_db'), _sa_prop('wellcover', 17, 21, sheet='xsa_db'),
                     dict(t='xsa', kind='leak', x=6, y=2), dict(t='xsa', kind='leak', x=25, y=2),
                     dict(t='xsa', kind='motes', x=18, y=10, w=32, h=16, n=14, col='150,230,220'),
                     _sa_en('db_barnacle', 21, 10)])
_sa_r.fill(0, 0, 35, 1).fill(0, 0, 0, 23).fill(35, 0, 35, 23).fill(0, 23, 35, 23)
_sa_r.fill(0, 14, 0, 17, '.')                                     # <- the Drowned Shaft (W4)
_sa_r.fill(1, 18, 4, 22)                                          # the landing
_sa_r.fill(5, 19, 9, 22)                                          # step one (low: walk on at low water)
_sa_r.fill(10, 22, 11, 22, '^')                                   # the spiked gutter
_sa_r.fill(12, 15, 15, 22)                                        # step two  (four rows up: float up at high water)
_sa_r.fill(16, 22, 18, 22, 'B').fill(16, 23, 18, 23, '.')         # the old well, bricked over (strike it): down to the Drowned Bell
_sa_r.fill(19, 11, 22, 22)                                        # step three
_sa_r.fill(23, 7, 26, 22)                                         # step four
_sa_r.fill(27, 22, 28, 22, '^')
_sa_r.fill(29, 4, 34, 22)                                         # the top step (seed)
for _x, _y, _ch in [(32, 3, 'i'), (9, 2, 'x'), (21, 2, 'x'), (31, 2, 'r')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- DB17 The Drowned Bell (secret, under the Tide Steps' well)
_sa_r = Room('DB17', 'The Drowned Bell', 'barrows', 356, 97, 16, 14, indoor=True, needs=['tidebreath'], x3=True, secret=True, clear=True,
             chests=['shard'],
             spawns=[_sa_prop('bigbell', 8, 1, sheet='xsa_bell'), _sa_s('lore', 14, 3, page='sa_7', look='none'),
                     _sa_db('bones', 3, 12), _sa_prop('pearlclam', 10, 12, sheet='xsa_db'), _sa_prop('weeds', 6, 12, sheet='xsa_db'),
                     dict(t='xsa', kind='bubbles', x=8, y=8, w=12, h=8, n=10)])
_sa_r.walls()
_sa_r.fill(1, 1, 14, 12, _SA_WL)
_sa_r.fill(10, 1, 14, 3, '.').fill(9, 1, 9, 3).fill(12, 4, 14, 4)   # an air pocket in the corner (the lore stone's ledge)
_sa_r.fill(4, 0, 6, 1, '.')                                      # the well from the Tide Steps (the water starts below its lip)
_sa_r.put(12, 3, 'C')


# ============================================================================================ THE CRIMSON MANOR
# Zone (§8.1) x 380..600, y 61..111, above the Crimson rooms. The rooms that meet the manor reach down past y 111 to touch
# it edge to edge: the East Wing sits against CM7/CM4's east wall (x 452), the Grand Staircase on the Vestibule's roof.
#   CM9  The East Wing        452..535 x 119..146  grand: in through the Portrait Gallery's east window; three floors; shrine
#   CM16 Moonlit Conservatory 536..571 x 129..146  vista: off the East Wing's ground floor (open to the sky)
#   CM17 Behind the Bookcase  536..551 x 115..128  secret: behind the false bookcase at the top floor's east end (the Silver Key)
#   CM11 Servants' Corridor   409..456 x 105..118  path: up the servants' stair from the East Wing; west to the Grand Staircase
#   CM13 The Portrait Riddle  457..496 x 101..118  puzzle: east of the corridor (the Portrait Key)
#   CM14 The Locked Study     497..528 x 101..118  puzzle: through the three-key gate east of the Riddle
#   CM10 The Grand Staircase  385..408 x 91..122   path: shrine; the gate, then down through the Vestibule's roof (the loop-back)
#   CM15 Servants' Quarters   409..448 x 91..104   gauntlet: off the stair's upper landing
#   CM12 Blood-Rain Rooftops  380..443 x 71..90    parkour: out of the top of the stairwell into the red rain (the Rook's Key)

# ---------------------------------------------------------------- the old rooms: the gallery's east window, the Vestibule's roof
_sa_cm4 = ROOM('CM4')
_sa_cm4.fill(54, 6, 54, 8, '.')                                   # the gallery's east window: into the East Wing
_sa_cm4.kw.setdefault('spawns', []).append(dict(t='xsa', kind='sign', x=52, y=10, text='Rain hammers on a tall window at the end of the gallery. It is unlatched.'))
_sa_cm8 = ROOM('CM8')
_sa_cm8.fill(5, 0, 8, 1, '.')                                     # up through the Vestibule's roof into the Grand Staircase
_sa_cm8.fill(7, 8, 8, 8, '=').fill(5, 5, 6, 5, '=').fill(7, 2, 8, 2, '=')

# ---------------------------------------------------------------- CM9 The East Wing (grand)
# Three floors. Top: the long gallery (portraits) and the false bookcase at its east end (-> CM17). Middle: guest rooms.
# Ground: the servants' hall (shrine), the window in from the Portrait Gallery, the door east into the Conservatory. The
# servants' stair climbs the west end through every floor and on up into the Servants' Corridor. The library in the
# middle has fallen through both floors: its shelves are the way down (and up; emberstone on the top shelf).
_sa_sp = [dict(t='xsa', kind='bookcase', x=82, y=7, cells=[[83, 4], [83, 5], [83, 6], [83, 7]]),
          dict(t='cm_chandelier', x=24, y=1, len=40, swing=0), dict(t='cm_chandelier', x=70, y=9, len=40, swing=0),
          dict(t='cm_chandelier', x=30, y=18, len=30, swing=0),
          _sa_prop('fallenchandelier', 52, 23, sheet='xsa_chand', dy=48),
          _sa_prop('bookcase', 45, 26, sheet='xsa_cm'), _sa_prop('bookcase_fallen', 60, 26, sheet='xsa_cm'), _sa_prop('bookcase', 64, 16, sheet='xsa_cm'),
          _sa_prop('bookcase', 40, 7, sheet='xsa_cm'), _sa_prop('bookcase', 68, 7, sheet='xsa_cm'), _sa_prop('bookcase', 76, 7, sheet='xsa_cm'),
          _sa_prop('books', 47, 26, sheet='xsa_cm'), _sa_prop('books', 58, 26, sheet='xsa_cm'), _sa_prop('books', 53, 16, sheet='xsa_cm'),
          _sa_pt(10, 4, 'a'), _sa_pt(17, 4, 'c', ambush=True), _sa_pt(26, 4, 'e'), _sa_pt(34, 4, 'd'),
          _sa_cm('candelabra', 7, 7), _sa_cm('candelabra', 37, 7), _sa_cm('candelabra', 66, 7),
          _sa_cm('table', 14, 16), _sa_cm('candelabra', 22, 16), _sa_prop('bed', 29, 16, sheet='xsa_cm'), _sa_prop('wardrobe', 35, 16, sheet='xsa_cm'),
          _sa_prop('bed', 72, 16, sheet='xsa_cm', flip=True), _sa_cm('candelabra', 78, 16),
          _sa_cm('winerack', 20, 26), _sa_cm('barrel', 25, 26), _sa_cm('table', 31, 26), _sa_prop('hearth', 8, 26, sheet='xsa_cm'),
          _sa_prop('bellboard', 37, 26, sheet='xsa_cm'), _sa_cm('candelabra', 28, 26), _sa_cm('candelabra', 79, 26), _sa_cm('statue', 73, 26, sub='lady'),
          _sa_cm('sconce', 70, 13), _sa_cm('sconce', 40, 22), _sa_cm('sconce', 18, 13),
          dict(t='xsa', kind='motes', x=52, y=14, w=26, h=22, n=18, col='255,210,170'),
          _sa_en('cm_servant', 24, 7), _sa_en('cm_servant', 18, 16), _sa_en('cm_hound', 30, 26), _sa_en('cm_servant', 76, 26),
          _sa_en('cm_hound', 72, 7)]
_sa_r = Room('CM9', 'The East Wing', 'crimson', 452, 119, 84, 28, indoor=True, needs=['talon'], x3=True, grand=True,
             shrine='Servants\' Hall Shrine', items=['emberstone', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 83, 0).fill(0, 0, 0, 27).fill(83, 0, 83, 27).fill(0, 27, 83, 27)
_sa_r.fill(1, 8, 82, 8).fill(1, 17, 82, 17)                       # the floors
_sa_r.fill(0, 24, 0, 26, '.')                                     # <- the Portrait Gallery's east window
_sa_r.fill(83, 23, 83, 26, '.')                                   # -> Moonlit Conservatory (east, ground floor)
_sa_r.fill(83, 4, 83, 7, '.')                                     # -> Behind the Bookcase (the bookcase stands in it until struck)
# the servants' stair: a narrow shaft up the west end, through both floors and the ceiling (into the Servants' Corridor)
_sa_r.fill(1, 0, 3, 0, '.').fill(1, 8, 3, 8, '.').fill(1, 17, 3, 17, '.')
for _i, _y in enumerate(range(24, 2, -3)):
    _sa_r.put(3 if _i % 2 == 0 else 1, _y, '=')
_sa_r.put(3, 0, '=')
_sa_r.fill(4, 1, 4, 5).fill(4, 9, 4, 13).fill(4, 18, 4, 21)       # the stair's wall (the landings are its gaps)
# the collapsed library: both floors gone between cols 42..62; its shelves are the way down (and up)
_sa_r.fill(42, 8, 62, 8, '.').fill(42, 17, 62, 17, '.')
_sa_r.fill(40, 8, 41, 8, '=').fill(63, 8, 64, 8, '=')
for _x0, _x1, _y in [(44, 47, 11), (51, 54, 10), (58, 61, 12), (46, 49, 14), (54, 57, 15), (43, 45, 20), (49, 52, 20),
                     (57, 60, 21), (62, 62, 18), (47, 49, 5), (53, 55, 3), (60, 62, 24), (43, 45, 24)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
_sa_r.fill(50, 24, 55, 26)                                        # the fallen chandelier's wreck (a heap to climb)
for _x, _y, _ch in [(54, 2, 'i'), (80, 16, 'i'), (14, 26, 'S'), (12, 1, 'x'), (30, 1, 'x'), (72, 1, 'x'), (6, 26, 'k'), (80, 7, 'k')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM17 Behind the Bookcase (secret: the Silver Key)
_sa_r = Room('CM17', 'Behind the Bookcase', 'crimson', 536, 115, 16, 14, indoor=True, needs=['talon'], x3=True, secret=True,
             items=['xsa_key1'],
             spawns=[_sa_s('lore', 9, 6, page='sa_11', look='corpse'), _sa_prop('chalk', 12, 11, sheet='xsa_cm'),
                     _sa_prop('lamp_cm', 6, 11, sheet='xsa_cm'), _sa_prop('pipes', 13, 6, sheet='xsa_cm'),
                     dict(t='xsa', kind='motes', x=8, y=7, w=14, h=10, n=8, col='255,200,160')])
_sa_r.walls().fill(0, 12, 15, 13)
_sa_r.fill(0, 8, 0, 11, '.')                                      # <- the East Wing's false bookcase
_sa_r.fill(3, 7, 10, 7).fill(8, 7, 9, 7, '=')                     # a crawl shelf
_sa_r.fill(1, 1, 15, 2).fill(4, 3, 6, 3, '.')
for _x, _y, _ch in [(4, 6, 'i'), (14, 3, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM16 Moonlit Conservatory (vista; open to the sky through the glass)
_sa_r = Room('CM16', 'Moonlit Conservatory', 'crimson', 536, 129, 36, 18, needs=['talon'], x3=True, vista=True,
             spawns=[_sa_s('bench', 10, 16, id='bench', view=[18, 9], lore='sa_9', skin='wood'),
                     dict(t='xsa', kind='glasshouse', x=18, y=10),
                     _sa_prop('piano', 22, 16, sheet='xsa_cm'), dict(t='xsa', kind='piano', x=22, y=16),
                     _sa_prop('roses', 6, 16, sheet='xsa_cm'), _sa_prop('roses', 16, 16, sheet='xsa_cm'), _sa_prop('roses', 30, 16, sheet='xsa_cm'),
                     _sa_prop('trellis', 13, 16, sheet='xsa_cm'), _sa_prop('trellis', 27, 16, sheet='xsa_cm'), _sa_cm('fountain', 18, 16),
                     _sa_prop('roses', 32, 11, sheet='xsa_cm'),
                     dict(t='xsa', kind='shaft', x=18, y=9, w=6, h=16, col='210,220,255', a=0.09, lean=-0.3),
                     dict(t='xsa', kind='shaft', x=28, y=9, w=3, h=16, col='210,220,255', a=0.06, lean=-0.3),
                     dict(t='xsa', kind='petals', x=18, y=9, w=32, h=14, n=18),
                     dict(t='xsa', kind='motes', x=18, y=9, w=32, h=14, n=14, col='220,225,255')])
_sa_r.fill(0, 0, 35, 1).fill(0, 0, 0, 17).fill(35, 0, 35, 17).fill(0, 17, 35, 17)
_sa_r.fill(0, 13, 0, 16, '.')                                     # <- the East Wing (west, ground floor)
_sa_r.fill(30, 12, 34, 12)                                        # a raised rose bed along the glass
_sa_r.fill(3, 2, 4, 3).fill(31, 2, 32, 3)                         # iron ribs of the glasshouse
_sa_skins(_sa_r, ('glass', 0, 0, 36, 2), ('glass', 0, 2, 1, 11), ('glass', 35, 2, 1, 15))

# ---------------------------------------------------------------- CM11 Servants' Corridor (path; the hidden halls)
_sa_r = Room('CM11', 'Servants\' Corridor', 'crimson', 409, 105, 48, 14, indoor=True, needs=['talon'], x3=True, items=['gold'],
             spawns=[_sa_prop('canvasback', 8, 11, sheet='xsa_cm'), _sa_prop('canvasback', 24, 11, sheet='xsa_cm'),
                     _sa_prop('pipes', 13, 11, sheet='xsa_cm'), _sa_prop('pipes', 30, 11, sheet='xsa_cm'), _sa_prop('lamp_cm', 4, 11, sheet='xsa_cm'),
                     _sa_prop('lamp_cm', 27, 11, sheet='xsa_cm'), _sa_prop('laundry', 20, 1, sheet='xsa_cm'), _sa_cm('barrel', 11, 11),
                     _sa_prop('spyhole', 37, 11, sheet='xsa_cm'), _sa_prop('lamp_cm', 41, 11, sheet='xsa_cm'),
                     _sa_en('cm_servant', 20, 11), _sa_en('cm_hound', 36, 11)])
_sa_r.fill(0, 0, 47, 0).fill(0, 0, 0, 13).fill(47, 0, 47, 13).fill(0, 12, 47, 13)
_sa_r.fill(0, 8, 0, 11, '.')                                      # -> the Grand Staircase (west)
_sa_r.fill(47, 8, 47, 11, '.')                                    # -> the Portrait Riddle (east)
_sa_r.fill(44, 12, 46, 13, '.')                                   # <- the East Wing's servants' stair comes up here
_sa_r.fill(1, 6, 14, 6).fill(10, 6, 12, 6, '=')                   # the upper crawl (a gap in its floor)
_sa_r.fill(22, 6, 32, 6).fill(26, 6, 28, 6, '=')
_sa_r.fill(9, 9, 11, 9, '=').fill(25, 9, 27, 9, '=')                # crates stacked under the gaps
_sa_r.fill(16, 1, 16, 9).fill(34, 1, 34, 9)                       # low beams: duck under
for _x, _y, _ch in [(3, 5, 'i'), (9, 1, 'x'), (29, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM13 The Portrait Riddle (puzzle; the Portrait Key)
# The Countess's great portrait looks from one family portrait to the next (53_sa.js draws her gaze). Strike them in the
# order she looks; the panel high on the east wall slides open on the key. A brass plate (lore sa_12) says so.
_sa_fr = [(4, 7, 'f1'), (8, 5, 'f2'), (12, 7, 'f3'), (27, 7, 'f4'), (30, 5, 'f5'), (33, 11, 'f6')]
_sa_sp = [dict(t='xsa', kind='gaze', x=20, y=7, seq='gaze', frames=[f[2] for f in _sa_fr], order=['f4', 'f2', 'f6', 'f1', 'f5']),
          _sa_prop('familyportrait', 20, 10, sheet='xsa_portrait'),
          *[_sa_k('frame', x, y, id=i, group='gaze') for x, y, i in _sa_fr],
          _sa_k('seq', 20, 15, id='gaze', group='gaze', order=['f4', 'f2', 'f6', 'f1', 'f5'], targets=['gK'],
                msg='High on the east wall, a panel slides back.'),
          _sa_k('gate', 34, 7, id='gK'),
          _sa_s('lore', 17, 15, page='sa_12', look='tablet'),
          _sa_cm('candelabra', 2, 15), _sa_cm('candelabra', 24, 15), _sa_cm('candelabra', 30, 15), _sa_cm('table', 10, 15),
          _sa_prop('rug', 20, 15, sheet='xsa_cm'), _sa_cm('sconce', 16, 10), _sa_cm('sconce', 36, 12)]
_sa_r = Room('CM13', 'The Portrait Riddle', 'crimson', 457, 101, 40, 18, indoor=True, needs=['talon'], x3=True, puzzle=True,
             items=['xsa_key2', 'gold'], spawns=_sa_sp)
_sa_r.fill(0, 0, 39, 1).fill(0, 0, 0, 17).fill(39, 0, 39, 17).fill(0, 16, 39, 17)
_sa_r.fill(0, 12, 0, 15, '.')                                     # <- the Servants' Corridor (west)
_sa_r.fill(39, 12, 39, 15, '.')                                   # -> the Locked Study (its three-key gate is on the far side)
_sa_r.fill(34, 2, 38, 8).fill(34, 5, 38, 7, '.')                  # the panel niche high on the east wall, behind its gate
_sa_r.fill(27, 13, 30, 13, '=').fill(31, 10, 33, 10, '=')         # a sideboard and a picture rail: up to the niche
for _x, _y, _ch in [(36, 7, 'i'), (37, 7, 'i'), (6, 2, 'x'), (20, 2, 'r'), (28, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM14 The Locked Study (puzzle: three keys)
_sa_r = Room('CM14', 'The Locked Study', 'crimson', 497, 101, 32, 18, indoor=True, needs=['talon'], x3=True, puzzle=True,
             chests=['shard'], items=['gold'],
             spawns=[_sa_k('gate', 1, 15, id='gS'),
                     dict(t='xsa', kind='keygate', x=2, y=15, gate='gS', keys=['xsa_key1', 'xsa_key2', 'xsa_key3'], flag='xsa:study'),
                     _sa_prop('desk', 15, 15, sheet='xsa_cm'), _sa_prop('bookcase', 6, 15, sheet='xsa_cm'), _sa_prop('bookcase', 23, 15, sheet='xsa_cm'),
                     _sa_prop('globe', 19, 15, sheet='xsa_cm'), _sa_prop('grandclock', 29, 9, sheet='xsa_cm'), _sa_cm('candelabra', 10, 15),
                     _sa_pt(15, 10, 'b'), _sa_cm('sconce', 9, 11), _sa_cm('sconce', 21, 11),
                     _sa_s('lore', 12, 15, page='sa_10', look='book'),
                     dict(t='xsa', kind='motes', x=16, y=9, w=28, h=14, n=10, col='255,215,170')])
_sa_r.fill(0, 0, 31, 1).fill(0, 0, 0, 17).fill(31, 0, 31, 17).fill(0, 16, 31, 17)
_sa_r.fill(0, 12, 0, 15, '.')                                     # <- the Portrait Riddle (west), through the study gate
_sa_r.fill(1, 2, 1, 11)                                           # the door-frame over the gate (the gate reaches it)
_sa_r.fill(24, 10, 31, 10).fill(4, 10, 8, 10, '=')                # the mezzanine (the clock, the chest); a book-ladder rail
_sa_r.fill(14, 13, 16, 13, '=').fill(19, 12, 21, 12, '=')
for _x, _y, _ch in [(27, 9, 'C'), (5, 9, 'i'), (15, 2, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM10 The Grand Staircase (path; the loop-back hub)
_sa_sp = [_sa_k('gate', 15, 29, id='gV', persist=True),
          _sa_k('lever', 13, 29, id='lV', targets=['gV'], once=True, skin='wood', msg='The stair-gate swings open over the Vestibule.'),
          _sa_pt(4, 7, 'a'), _sa_pt(19, 7, 'b'), _sa_pt(12, 4, 'c'), _sa_pt(19, 20, 'd'), _sa_pt(5, 18, 'e'), _sa_pt(6, 25, 'b'),
          dict(t='cm_chandelier', x=12, y=2, len=120, swing=0, big=True),
          _sa_cm('candelabra', 2, 29), _sa_cm('candelabra', 17, 11), _sa_cm('candelabra', 22, 25), _sa_cm('statue', 7, 29, sub='lady'),
          _sa_prop('grandclock', 4, 29, sheet='xsa_cm'), _sa_prop('bust', 21, 11, sheet='xsa_cm'),
          _sa_cm('sconce', 11, 20), _sa_cm('sconce', 11, 11),
          _sa_en('cm_servant', 18, 25), _sa_en('cm_hound', 5, 29)]
_sa_r = Room('CM10', 'The Grand Staircase', 'crimson', 385, 91, 24, 32, indoor=True, needs=['talon'], x3=True, shrine='Vermeil Stair Shrine',
             spawns=_sa_sp)
_sa_r.fill(0, 0, 23, 0).fill(0, 0, 0, 31).fill(23, 0, 23, 31).fill(0, 30, 23, 31)
_sa_r.fill(4, 0, 7, 0, '.')                                       # up into the Blood-Rain Rooftops
_sa_r.fill(23, 8, 23, 11, '.')                                    # -> the Servants' Quarters (the upper landing)
_sa_r.fill(23, 22, 23, 25, '.')                                   # <- the Servants' Corridor (the lower landing)
_sa_r.fill(15, 12, 22, 12).fill(15, 26, 22, 26)                   # the landings
_sa_r.fill(16, 27, 22, 29, '.').fill(15, 27, 15, 29, '.')         # the Vestibule stair (behind its gate, under the lower landing)
_sa_r.fill(17, 30, 20, 31, '.')                                   # down through the Vestibule's roof (the loop-back)
for _x0, _x1, _y in [(11, 13, 28), (2, 6, 27), (8, 12, 24), (2, 6, 21), (8, 12, 18), (13, 16, 15), (8, 12, 12), (2, 6, 9),
                     (8, 12, 6), (3, 8, 3), (4, 5, 0)]:
    _sa_r.fill(_x0, _y, _x1, _y, '=')
for _x, _y, _ch in [(10, 29, 'S'), (12, 1, 'r'), (2, 1, 'x'), (21, 1, 'x')]:
    _sa_r.put(_x, _y, _ch)

# ---------------------------------------------------------------- CM15 Servants' Quarters (gauntlet: ring the service bell)
_sa_W = [[dict(type='cm_servant', x=8, y=11), dict(type='cm_servant', x=30, y=11)],
         [dict(type='cm_hound', x=6, y=11), dict(type='cm_hound', x=33, y=11), dict(type='cm_servant', x=20, y=11)],
         [dict(type='cm_servant', x=7, y=11), dict(type='cm_servant', x=32, y=11), dict(type='cm_hound', x=12, y=11), dict(type='cm_hound', x=26, y=11)],
         [dict(type='xsa_head_butler', x=20, y=11)]]
_sa_r = Room('CM15', 'Servants\' Quarters', 'crimson', 409, 91, 40, 14, indoor=True, needs=['talon'], x3=True, gauntlet=True,
             spawns=[_sa_k('gate', 2, 11, id='gq', open=True),
                     _sa_s('gauntlet', 20, 11, id='quarters', look='bell', name='The Servants\' Quarters', gates=['gq'], waves=_sa_W,
                           reward=['emberstone', 'gold']),
                     _sa_prop('cot', 8, 11, sheet='xsa_cm'), _sa_prop('cot', 14, 11, sheet='xsa_cm'), _sa_prop('cot', 26, 11, sheet='xsa_cm'),
                     _sa_prop('cot', 32, 11, sheet='xsa_cm', flip=True), _sa_prop('bellboard', 20, 7, sheet='xsa_cm'),
                     _sa_prop('stove', 36, 11, sheet='xsa_cm'), _sa_prop('laundry', 12, 1, sheet='xsa_cm'), _sa_prop('laundry', 28, 1, sheet='xsa_cm'),
                     _sa_prop('lamp_cm', 23, 11, sheet='xsa_cm'), _sa_cm('table', 17, 11)])
_sa_r.fill(0, 0, 39, 0).fill(0, 0, 0, 13).fill(39, 0, 39, 13).fill(0, 12, 39, 13)
_sa_r.fill(0, 8, 0, 11, '.')                                      # <- the Grand Staircase's upper landing (west)
_sa_r.fill(2, 1, 2, 7)                                            # the partition over the gate
_sa_r.fill(6, 7, 10, 7, '=').fill(30, 7, 34, 7, '=')

# ---------------------------------------------------------------- CM12 Blood-Rain Rooftops (parkour; blood rain)
# Up out of the Grand Staircase's stairwell onto the roofs. Slates, railings of spikes in the gutters, chimneys, gargoyles
# asleep on the ledges, and the Rook's Key in a nest on the tallest chimney. The rain burns: shelter under the eaves.
_sa_r = Room('CM12', 'Blood-Rain Rooftops', 'crimson', 380, 71, 64, 20, needs=['talon'], x3=True, parkour=True,
             rain=dict(every=[6.0, 9.0], dur=2.6), items=['xsa_key3'],
             spawns=[dict(t='cm_perch', x=20, y=10, n=1), dict(t='cm_perch', x=59, y=7, n=1),
                     _sa_cm('statue', 8, 13, sub='gargoyle'), _sa_cm('sconce', 12, 11),
                     _sa_prop('chimney', 22, 10, sheet='xsa_cm'), _sa_prop('chimney', 48, 11, sheet='xsa_cm'), _sa_prop('weathervane', 58, 7, sheet='xsa_cm'),
                     _sa_prop('crows', 37, 4, sheet='xsa_cm'), _sa_prop('gutterspout', 16, 17, sheet='xsa_cm'),
                     dict(t='xsa', kind='motes', x=32, y=9, w=62, h=14, n=12, col='255,120,120'),
                     _sa_en('cm_servant', 25, 10)])
_sa_r.fill(0, 0, 0, 19).fill(0, 19, 63, 19).fill(63, 0, 63, 19)
_sa_r.fill(9, 19, 12, 19, '.')                                    # <- up out of the Grand Staircase's stairwell
_sa_r.fill(7, 14, 14, 18).fill(9, 14, 12, 18, '.')                # the stair turret (hollow)
_sa_r.fill(11, 16, 12, 16, '=')
_sa_r.fill(1, 18, 6, 18, '^').fill(15, 18, 17, 18, '^')           # the spiked railings in the gutters
_sa_r.fill(18, 11, 27, 18).fill(19, 8, 24, 8).fill(24, 9, 24, 10)  # the second roof and its dormer (open west: shelter)
_sa_r.fill(28, 18, 30, 18, '^')
_sa_r.fill(31, 10, 40, 18)                                        # the third roof
_sa_r.fill(36, 6, 37, 9)                                          # the tall chimney (the Rook's Key on top)
_sa_r.fill(33, 7, 34, 7, '=')                                     # a lead ledge up to it
_sa_r.fill(41, 18, 43, 18, '^')
_sa_r.fill(44, 12, 52, 18)                                        # the fourth roof
_sa_r.fill(53, 18, 55, 18, '^')
_sa_r.fill(56, 8, 62, 18)                                         # the tower's roof (a gargoyle sleeps on it)
_sa_r.fill(56, 4, 57, 4)                                          # a lintel over the tower's dead door (shelter)
_sa_r.fill(1, 11, 4, 11).fill(7, 10, 10, 10)                      # eaves over the west gutter
for _x, _y, _ch in [(36, 5, 'i')]:
    _sa_r.put(_x, _y, _ch)
_sa_skins(_sa_r, ('slate', 7, 14, 8, 5), ('slate', 18, 8, 10, 11), ('slate', 31, 10, 10, 9), ('slate', 44, 12, 9, 7), ('slate', 56, 8, 7, 11),
          ('brick', 36, 6, 2, 4), ('slate', 1, 11, 4, 1), ('slate', 7, 10, 4, 1), ('brick', 56, 4, 2, 1))
