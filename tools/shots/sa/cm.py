

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
