

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
