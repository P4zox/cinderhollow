# ============================================================ THE HOARFROST AQUEDUCT (agent H) — zone x 160…250, y −44…14
# A frozen aqueduct and its cisterns in the mountains east of the Rampart Summit.
# Map chars owned here:  '_' ice floor (solid, slippery)  ':' freezing water  ',' icicle (hangs from the cell above)
# Spawns: enemies hf_wraith / hf_golem / hf_lurker, bosses ice_warden / twins, 'hf_fall' = decorative frozen waterfall.
#
#   HF6 Frozen Aqueduct (sky) ── HF7 The Still Reservoir (Twins)
#   HF5 Gatehouse ── HF4 Sluice Gates (Warden) ── HF3 Sluice Stair (shaft)
#   R4 ── HF1 Broken Span (Root Hook gap) ── HF2 Cistern of Rime ──┘
# Shortcut: the hole in the Gatehouse floor drops back onto the Span Shrine ledge in HF1.
SOLID.add('_')
FLYING.update({'hf_wraith', 'hf_lurker'})


def _put(r, pts):
    for x, y, ch in pts:
        r.put(x, y, ch)


ROOM('R4').open('E', 3, 10)

# ---------------------------------------------------------------- HF1: the Root Hook gate
r = Room('HF1', 'The Broken Span', 'hoarfrost', 160, 0, 40, 15, indoor=True, shrine='Span Shrine',
         spawns=[{'t': 'hf_fall', 'x': 15, 'y': 4, 'h': 9}, {'t': 'hf_fall', 'x': 23, 'y': 4, 'h': 9}])
r.walls().open('W', 3, 10).open('E', 7, 10)
r.fill(1, 11, 7, 13)                        # west ledge (continues the Rampart Summit)
r.fill(30, 11, 38, 13)                      # far ledge
r.fill(8, 13, 29, 13, '^')                  # the gorge: a bed of ice shards
r.fill(8, 1, 29, 2).fill(10, 3, 27, 3)      # the collapsed upper channel hangs over the gorge
r.fill(31, 0, 33, 0, '.')                   # shortcut hole from the Gatehouse above
_put(r, [(12, 4, '@'), (19, 4, '@'), (26, 4, '@'),
         (35, 10, 'S'), (37, 10, 'k'), (2, 10, 'b'), (5, 1, ','), (36, 1, 'x'), (3, 1, 'r')])

# ---------------------------------------------------------------- HF2: frozen cistern
r = Room('HF2', 'Cistern of Rime', 'hoarfrost', 200, -4, 32, 18, indoor=True, items=['emberstone'],
         spawns=[{'t': 'enemy', 'type': 'hf_lurker', 'x': 16, 'y': 14, 'air': True},
                 {'t': 'enemy', 'type': 'hf_golem', 'x': 25, 'y': 14},
                 {'t': 'enemy', 'type': 'hf_wraith', 'x': 12, 'y': 7}])
r.walls().open('W', 11, 14).open('E', 11, 14)
r.fill(1, 15, 30, 16)
r.fill(6, 15, 11, 15, '_')                  # glazed floor
r.fill(13, 15, 20, 16, ':')                 # the cistern: freezing water, two deep
r.fill(22, 15, 27, 15, '_')
r.fill(8, 11, 11, 11, '=').fill(15, 8, 18, 8, '=').fill(22, 11, 25, 11, '=')
r.fill(26, 6, 30, 7)                        # upper ledge
_put(r, [(28, 5, 'i'), (9, 1, ','), (17, 1, ','), (24, 1, ','), (2, 14, 'k'), (5, 1, 'x'), (29, 14, 'b'), (13, 1, 'r')])

# ---------------------------------------------------------------- HF3: the climb
r = Room('HF3', 'Sluice Stair', 'hoarfrost', 232, -22, 18, 36, indoor=True, items=['shard'],
         spawns=[{'t': 'enemy', 'type': 'hf_wraith', 'x': 9, 'y': 21}, {'t': 'enemy', 'type': 'hf_wraith', 'x': 6, 'y': 9},
                 {'t': 'hf_fall', 'x': 16, 'y': 25, 'h': 8}])
r.walls().open('W', 29, 32).open('W', 11, 14)
r.fill(1, 33, 16, 34)
r.fill(1, 15, 6, 16)                        # landing in front of the Sluice Gates
r.fill(10, 30, 14, 30, '=').fill(3, 27, 7, 27, '=')
r.fill(11, 24, 16, 24, '_')                 # iced ledge
r.fill(4, 21, 8, 21, '=').fill(8, 18, 12, 18, '=')
r.fill(13, 14, 16, 14)                      # shard alcove across the shaft: swing to it from the Sluice landing
_put(r, [(9, 8, '@'), (14, 13, 'i'), (13, 25, ','), (2, 32, 'k'), (15, 32, 'k'), (4, 1, 'x'), (12, 1, 'x'), (8, 1, 'r'), (2, 14, 'b')])

# ---------------------------------------------------------------- HF4: mini-boss arena
r = Room('HF4', 'The Sluice Gates', 'hoarfrost', 196, -18, 36, 14, indoor=True, boss='ice_warden', entry='E',
         spawns=[{'t': 'boss', 'kind': 'ice_warden', 'x': 11, 'y': 10}])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 35, 13).fill(0, 0, 35, 1)
_put(r, [(1, 10, 'F'), (34, 10, 'F'), (6, 2, ','), (13, 2, ','), (22, 2, ','), (29, 2, ','),
         (9, 2, 'x'), (26, 2, 'x'), (4, 10, 'k'), (31, 10, 'k')])

# ---------------------------------------------------------------- HF5: gatehouse (shortcut + climb)
r = Room('HF5', 'The Gatehouse', 'hoarfrost', 164, -18, 32, 18, indoor=True, chests=['sp:glacial_wall'],
         spawns=[{'t': 'enemy', 'type': 'hf_golem', 'x': 12, 'y': 16}, {'t': 'enemy', 'type': 'hf_wraith', 'x': 14, 'y': 7}])
r.walls().open('E', 7, 10)
r.fill(24, 11, 30, 12)                      # landing in front of the Sluice Gates
r.fill(27, 17, 29, 17, '.')                 # the hole: a long drop onto the Span Shrine ledge
r.fill(3, 0, 5, 0, '.')                     # up to the aqueduct
r.fill(17, 8, 21, 8, '=').fill(9, 5, 13, 5, '=').fill(2, 3, 8, 3, '=').fill(3, 1, 5, 1, '=')
_put(r, [(4, 16, 'C'), (15, 1, ','), (22, 1, ','), (2, 16, 'k'), (20, 16, 'b'), (11, 1, 'x'), (26, 1, 'r'), (7, 16, 'u'), (19, 16, 'u')])

# ---------------------------------------------------------------- HF6: the open aqueduct channel (sky)
r = Room('HF6', 'The Frozen Aqueduct', 'hoarfrost', 164, -34, 48, 16, shrine='Reservoir Shrine',
         items=['w:frostbrand', 'emberstone'], chests=['c_frostheart'],
         spawns=[{'t': 'enemy', 'type': 'hf_lurker', 'x': 18, 'y': 12, 'air': True},
                 {'t': 'enemy', 'type': 'hf_golem', 'x': 27, 'y': 10},
                 {'t': 'enemy', 'type': 'hf_wraith', 'x': 18, 'y': 6}, {'t': 'enemy', 'type': 'hf_wraith', 'x': 34, 'y': 6}])
r.walls(top=False).open('E', 6, 9)
r.fill(1, 13, 12, 14)
r.fill(3, 13, 5, 14, '.').fill(3, 15, 5, 15, '=')    # the stair head from the Gatehouse
r.fill(13, 13, 22, 14, ':')                 # flooded channel
r.fill(15, 10, 17, 10, '=').fill(20, 10, 21, 10, '=')
r.fill(23, 11, 30, 14).fill(24, 11, 29, 11, '_')       # iced pier
r.fill(31, 14, 36, 14, '^')                 # broken span over ice shards
r.fill(37, 10, 46, 14)
r.fill(6, 9, 9, 9, '=')
r.fill(26, 8, 30, 8)                        # high ledge above the iced pier
_put(r, [(7, 8, 'i'), (28, 7, 'i'), (41, 9, 'S'), (39, 9, 'C'), (45, 9, 'k'), (2, 12, 'b'), (44, 9, 'r')])

# ---------------------------------------------------------------- HF7: the Frostbound Twins
r = Room('HF7', 'The Still Reservoir', 'hoarfrost', 212, -38, 38, 16, boss='twins',
         spawns=[{'t': 'boss', 'kind': 'twins', 'x': 24, 'y': 13},
                 {'t': 'hf_fall', 'x': 8, 'y': 3, 'h': 11}, {'t': 'hf_fall', 'x': 31, 'y': 2, 'h': 12}])
r.walls(top=False).open('W', 10, 13)
r.fill(1, 14, 36, 14)
r.fill(1, 0, 3, 7).fill(34, 0, 36, 5)       # cliffs framing the reservoir
r.fill(15, 14, 22, 14, '_')                 # the frozen heart of the reservoir
_put(r, [(1, 13, 'F'), (5, 13, 'k'), (33, 13, 'k')])
