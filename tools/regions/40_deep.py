# ============================================================ THE BURNING DEEP (agent D) -- the root-forges beneath the Mire
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Tiles (web/src/23_deep.js): '*' lava (id 20, hazard), '<' / '>' conveyor belts (ids 21 / 22, solid).
# Gate: D2 is a lava chasm whose far ledge sits higher than the take-off -> only the Gale Cloak (glide into the
# thermal updraft) crosses it.  Shortcut: a forge hatch between D7 (lever) and D1's floor.
#
#   D1 Cinder Throat    280..303 x  84..97    entered from M4's floor (cols 41-43, a thin trapdoor)
#   D2 Molten Chasm     304..351 x  84..99    the glide gate (updraft over the lava)
#   D3 Slag Wards       352..399 x  84..99    shrine; imps, a sentry, a crawler pool, conveyors
#   D4 Slag Chute       376..399 x 100..133   the descent
#   D5 Foundry Halls    328..375 x 120..133   mini-boss: the Forge Overseer
#   D6 Sluice Stair     304..327 x 100..133   rising-magma escape (climb)
#   D7 Crucible Gate    280..303 x  98..115   shrine + the hatch lever (shortcut up into D1)
#   D8 The Crucible     228..279 x  98..115   main boss: the Molten Colossus
SOLID |= set('<>')

# ---- anchor: a thin trapdoor in the Sunken Road's floor (drop through with down + jump)
_m4 = ROOM('M4')
_m4.fill(41, 11, 43, 13, '.').fill(41, 13, 43, 13, '=')

# ---------------------------------------------------------------- D1 Cinder Throat
r = Room('D1', 'Cinder Throat', 'deep', 280, 84, 24, 14, indoor=True)
r.walls().open('N', 9, 11).open('E', 7, 10)
r.fill(0, 11, 23, 13)
r.fill(3, 11, 4, 13, '.').fill(3, 13, 4, 13, '=')          # the forge hatch (closed by a grate until opened from D7)
r.fill(9, 2, 12, 2, '=').fill(6, 5, 9, 5, '=').fill(12, 8, 15, 8, '=')
for x, y, ch in [(5, 1, 'x'), (18, 1, 'x'), (20, 10, 'k'), (15, 10, 'b'), (1, 10, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'dp_hatch', 'x': 3, 'y': 11, 'side': 'top'}]

# ---------------------------------------------------------------- D2 Molten Chasm (glide gate)
r = Room('D2', 'Molten Chasm', 'deep', 304, 84, 48, 16, indoor=True, items=['emberstone'])
r.walls().open('W', 7, 10).open('E', 5, 8)
r.fill(0, 0, 47, 1)
r.fill(0, 11, 9, 15)                                        # take-off ledge (floor row 11)
r.fill(40, 9, 47, 15)                                       # far ledge: two rows HIGHER than the take-off
r.fill(10, 15, 39, 15).fill(10, 13, 39, 14, '*')            # the lava river
r.fill(24, 5, 25, 12, '|')                                  # thermal updraft rising off the lava
r.fill(19, 4, 22, 4, '=')                                   # a perch only a glider reaches
for x, y, ch in [(20, 3, 'i'), (7, 2, 'x'), (15, 2, 'x'), (33, 2, 'x'), (43, 2, 'x'), (3, 10, 'b'), (44, 8, 'k')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- D3 Slag Wards (shrine)
r = Room('D3', 'Slag Wards', 'deep', 352, 84, 48, 16, indoor=True, shrine='Slag Ward Shrine',
         items=['c_slag'], chests=['emberstone'])
r.walls().open('W', 5, 8)
r.fill(0, 0, 47, 1)
r.fill(0, 9, 9, 15)                                         # shrine ledge
r.fill(10, 11, 17, 15)                                      # lower ward
r.fill(12, 11, 16, 11, '>')                                 # conveyor toward the pool
r.fill(18, 14, 24, 15).fill(18, 12, 24, 13, '*')            # slag pool (a crawler lurks)
r.fill(19, 8, 23, 8, '=')                                   # catwalk over the pool
r.fill(25, 11, 39, 15)
r.fill(28, 6, 33, 7)                                        # imp perch
r.fill(34, 11, 38, 11, '<')                                 # conveyor back toward the sentry
r.fill(40, 11, 42, 15, '.')                                 # drop into the Slag Chute
r.fill(43, 11, 47, 15)
for x, y, ch in [(4, 8, 'S'), (21, 7, 'i'), (45, 10, 'C'), (7, 8, 'A'), (2, 2, 'x'), (14, 2, 'x'), (26, 2, 'x'), (37, 2, 'x'),
                 (11, 10, 'k'), (27, 10, 'b'), (46, 10, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'enemy', 'type': 'dp_magma_crawler', 'x': 21, 'y': 12, 'air': True},
    {'t': 'enemy', 'type': 'dp_slag_imp', 'x': 30, 'y': 5},
    {'t': 'enemy', 'type': 'dp_forge_sentry', 'x': 33, 'y': 10},
    {'t': 'enemy', 'type': 'dp_slag_imp', 'x': 44, 'y': 10},
]

# ---------------------------------------------------------------- D4 Slag Chute (descent)
r = Room('D4', 'Slag Chute', 'deep', 376, 100, 24, 34, indoor=True, items=['sp:magma_orb'], chests=['w:forge_cleaver'])
r.walls().open('N', 16, 18).open('W', 27, 30)
r.fill(13, 6, 22, 7)                                        # A: landing under the hole
r.fill(1, 11, 9, 12)                                        # B
r.fill(13, 16, 22, 18).fill(15, 16, 20, 17, '*').fill(15, 18, 20, 18)   # C: slag basin with a crawler
r.fill(13, 16, 14, 16).fill(21, 16, 22, 16)
r.fill(1, 21, 9, 22)                                        # D
r.fill(14, 25, 22, 26)                                      # E
r.fill(0, 31, 23, 33)
r.fill(10, 31, 15, 32, '*')                                 # lava channel at the bottom
r.fill(16, 31, 19, 31, '<')                                 # conveyor carrying slag toward the channel
r.fill(1, 16, 3, 16, '=')                                   # side alcove for the spell
for x, y, ch in [(2, 15, 'i'), (21, 30, 'C'), (4, 1, 'x'), (19, 1, 'x'), (11, 1, 'x'), (5, 10, 'k'), (17, 24, 'b'), (3, 30, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'enemy', 'type': 'dp_slag_imp', 'x': 5, 'y': 10},
    {'t': 'enemy', 'type': 'dp_magma_crawler', 'x': 17, 'y': 16, 'air': True},
    {'t': 'enemy', 'type': 'dp_forge_sentry', 'x': 5, 'y': 20},
    {'t': 'enemy', 'type': 'dp_slag_imp', 'x': 19, 'y': 24},
    {'t': 'enemy', 'type': 'dp_magma_crawler', 'x': 12, 'y': 31, 'air': True},
]

# ---------------------------------------------------------------- D5 Foundry Halls (mini-boss arena)
r = Room('D5', 'Foundry Halls', 'deep', 328, 120, 48, 14, indoor=True, boss='overseer', entry='E', items=['emberstone'])
r.walls().open('E', 7, 10).open('W', 7, 10)
r.fill(0, 11, 47, 13).fill(0, 0, 47, 1)
r.fill(8, 11, 13, 11, '>').fill(34, 11, 39, 11, '<')        # belts feeding the centre of the floor
r.fill(20, 7, 27, 7, '=')
for x, y, ch in [(46, 10, 'F'), (1, 10, 'F'), (23, 6, 'i'), (6, 2, 'x'), (17, 2, 'x'), (30, 2, 'x'), (41, 2, 'x'),
                 (3, 10, 'k'), (44, 10, 'k'), (16, 10, 'b'), (31, 10, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'boss', 'kind': 'overseer', 'x': 16, 'y': 10}]

# ---------------------------------------------------------------- D6 Sluice Stair (rising magma escape)
r = Room('D6', 'Sluice Stair', 'deep', 304, 100, 24, 34, indoor=True, items=['emberstone'])
r.walls().open('E', 27, 30).open('W', 1, 4)
r.fill(0, 31, 23, 33)
r.fill(0, 5, 5, 5)                                          # exit ledge (west door)
steps = [(28, 15, 19), (25, 8, 12), (22, 2, 6), (19, 8, 11), (16, 14, 18), (13, 19, 22), (10, 12, 15), (7, 5, 9)]
for y, x0, x1 in steps:
    r.fill(x0, y, x1, y, '=')
r.fill(16, 20, 18, 21)                                      # a hot iron block to get around
r.fill(19, 13, 22, 13, '>')                                 # conveyor ledge: rides you into the wall-jump nook
r.put(15, 5, '@')                                           # hook ring over the last gap
r.fill(20, 4, 22, 4, '=')                                   # side perch (loot)
for x, y, ch in [(21, 3, 'i'), (3, 1, 'x'), (12, 1, 'x'), (20, 1, 'x'), (21, 30, 'k'), (2, 30, 'b'), (2, 4, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'dp_sluice', 'x': 12, 'y': 30, 'air': True}]

# ---------------------------------------------------------------- D7 Crucible Gate (shrine, shortcut lever)
r = Room('D7', 'Crucible Gate', 'deep', 280, 98, 24, 18, indoor=True, shrine='Crucible Shrine', items=['shard'])
r.walls().open('E', 3, 6).open('W', 11, 14).open('N', 3, 4)
r.fill(0, 15, 23, 17)
r.fill(18, 7, 23, 8)                                        # entry ledge from the Sluice Stair
for y, x0, x1 in [(13, 6, 9), (10, 1, 4), (7, 6, 9), (4, 1, 4), (1, 2, 5)]:
    r.fill(x0, y, x1, y, '=')                               # climb to the hatch
r.fill(11, 5, 13, 5, '=')
for x, y, ch in [(13, 14, 'S'), (8, 14, 'L'), (17, 14, 'A'), (12, 4, 'i'), (10, 2, 'x'), (20, 2, 'x'), (2, 14, 'k'), (21, 14, 'b'),
                 (20, 6, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'dp_hatch', 'x': 3, 'y': 0, 'side': 'bottom'}]

# ---------------------------------------------------------------- D8 The Crucible (Molten Colossus)
r = Room('D8', 'The Crucible', 'deep', 228, 98, 52, 18, indoor=True, boss='colossus', entry='E')
r.walls().open('E', 11, 14)
r.fill(0, 15, 51, 17).fill(0, 0, 51, 1)
r.fill(3, 10, 7, 10, '=').fill(44, 10, 48, 10, '=')         # side ledges above the pour
for x, y, ch in [(50, 14, 'F'), (4, 2, 'x'), (12, 2, 'x'), (39, 2, 'x'), (47, 2, 'x'), (2, 14, 'k'), (48, 14, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'boss', 'kind': 'colossus', 'x': 16, 'y': 14}, {'t': 'dp_crucible', 'x': 26, 'y': 2, 'air': True}]
