# ============================================================ THE CRIMSON MANOR (agent C) — a vampiric estate past Kalden's Vigil
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Zone: x 373..451 for y 29..69, x 332..451 for y 70..83 (column x 332 is the only way to meet M5's east wall at x 331).
# Gate: a blood veil ('%', the ash-veil mechanic re-skinned by web/src/32_crimson.js) in CM1 — needs Ember Dash.
# Route: M5 -> CM1 Threshold (veil) -> CM2 Blood-Rain Court (climb; cellar door at the bottom) -> CM3 Grand Foyer (shrine)
#        -> CM6 Butler's Hall (mini-boss, stair shaft up) -> CM4 Portrait Gallery (lever opens the gate back to the Court:
#        shortcut) -> CM8 Vestibule (shrine) -> CM7 Sanguine Ballroom (Countess Sanguine).  CM5 Blood Cellars: side area.
# Custom spawns (32_crimson.js): cm_prop (decor), cm_portrait (lore / eyes / ambush), cm_chandelier (swinging hazard),
# cm_pool (blood pool), cm_perch (gargoyle-bats asleep on a ledge), cm_diary (lore lectern), boss butler / sanguine.
FLYING.add('cm_gargoyle')


def _cm(kind, x, y, **kw):
    return dict(t='cm_prop', kind=kind, x=x, y=y, **kw)


def _pt(x, y, subj, **kw):
    return dict(t='cm_portrait', x=x, y=y, subj=subj, **kw)


# ---------------------------------------------------------------- M5 (anchor): open the east wall into the Threshold
_m5 = ROOM('M5')
_m5.fill(35, 7, 35, 10, '.')           # east door (global x 331, y 77..80)
_m5.put(34, 10, 'F')                   # exit fog: sealed while Ser Kalden lives

# ---------------------------------------------------------------- CM1 The Crimson Threshold (connector, blood-veil gate)
r = Room('CM1', 'The Crimson Threshold', 'crimson', 332, 70, 41, 14, indoor=True,
         spawns=[dict(t='enemy', type='cm_servant', x=17, y=10),
                 dict(t='enemy', type='cm_hound', x=35, y=10),
                 _cm('candelabra', 14, 10), _cm('candelabra', 38, 10), _cm('statue', 29, 10, sub='gargoyle'),
                 _cm('sconce', 17, 6), _cm('sconce', 33, 6)])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 11, 40, 13).fill(0, 0, 40, 1)
r.fill(0, 2, 11, 6)                    # the low cave tunnel from Kalden's Vigil
r.fill(7, 7, 7, 10, '%')               # the blood veil (solid rock above it up to the ceiling)
r.fill(22, 9, 27, 10)                  # a raised terrace
r.fill(31, 6, 34, 6, '=')
for x, y, ch in [(18, 2, 'l'), (36, 2, 'l'), (27, 2, 'x'), (13, 10, 'k'), (20, 10, 'b'), (3, 10, 'b')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- CM2 The Blood-Rain Court (outdoor, vertical climb)
r = Room('CM2', 'The Blood-Rain Court', 'crimson', 373, 44, 24, 40, items=['emberstone'],
         rain=dict(every=[7.5, 11.0], dur=3.0),
         spawns=[dict(t='enemy', type='cm_servant', x=19, y=36),
                 dict(t='cm_perch', x=19, y=13, n=2), dict(t='cm_perch', x=5, y=20, n=1),
                 dict(t='cm_pool', x=9, y=37, w=4),
                 _cm('fountain', 11, 37), _cm('carriage', 4, 36), _cm('statue', 18, 26, sub='lady'),
                 _cm('candelabra', 21, 26), _cm('candelabra', 21, 13)])
r.fill(0, 0, 0, 39).fill(23, 0, 23, 39).fill(0, 37, 23, 39)
r.open('W', 33, 36).open('E', 33, 36).open('E', 23, 26).open('E', 10, 13)
r.fill(9, 37, 12, 37, '.')             # the blood basin under the fountain (jumpable)
r.fill(16, 27, 22, 28)                 # foyer balcony (shelter from the rain beneath it)
r.fill(16, 14, 22, 15)                 # gallery balcony (gated door, opened from inside the gallery)
for y, x0 in [(34, 3), (31, 8), (28, 12), (24, 10), (21, 4), (18, 9), (15, 12)]:
    r.fill(x0, y, x0 + 3, y, '=')
r.fill(11, 11, 14, 11, '=').fill(5, 8, 8, 8, '=')    # up from the gallery balcony to the gargoyle ledge
r.fill(1, 5, 3, 5)                     # a gargoyle ledge high on the west facade
r.put(2, 4, 'i')

# ---------------------------------------------------------------- CM3 The Grand Foyer (shrine)
r = Room('CM3', 'The Grand Foyer', 'crimson', 397, 61, 24, 12, indoor=True, shrine='Crimson Foyer',
         spawns=[dict(t='cm_chandelier', x=12, y=2, len=40, swing=0),
                 _pt(5, 6, 'a', lore='cm_countess'), _pt(19, 6, 'b', lore='cm_count'),
                 dict(t='cm_diary', x=8, y=9, lore='cm_diary1'),
                 _cm('candelabra', 3, 9), _cm('candelabra', 21, 9)])
r.walls().open('W', 6, 9).open('E', 6, 9)
r.fill(0, 10, 23, 11).fill(0, 0, 23, 1)
r.put(13, 9, 'S')

# ---------------------------------------------------------------- CM6 The Butler's Hall (mini-boss; stair shaft up to the gallery)
r = Room('CM6', 'The Butler\'s Hall', 'crimson', 421, 61, 31, 12, indoor=True, boss='butler',
         spawns=[dict(t='boss', kind='butler', x=17, y=9),
                 _cm('table', 12, 9), _cm('candelabra', 4, 9), _cm('candelabra', 22, 9),
                 _pt(8, 5, 'd', lore='cm_hunter'), _pt(17, 5, 'e', lore='cm_widow'), _cm('sconce', 27, 8)])
r.walls().open('W', 6, 9)
r.fill(0, 10, 30, 11).fill(0, 0, 30, 1)
r.fill(1, 2, 1, 4).put(1, 9, 'F')      # entry fog, sealed to the ceiling
r.fill(25, 2, 25, 4).put(25, 9, 'F')   # exit fog before the stair shaft
r.fill(26, 0, 29, 1, '.')              # shaft up into the gallery floor
for y in (2, 5, 8):
    r.fill(26, y, 29, y, '=')

# ---------------------------------------------------------------- CM4 The Portrait Gallery (ambushes, swinging chandeliers, shortcut lever)
r = Room('CM4', 'The Portrait Gallery', 'crimson', 397, 47, 55, 14, indoor=True, items=['shard', 'emberstone'], chests=['sp:blood_lance'],
         spawns=[dict(t='enemy', type='cm_servant', x=24, y=10),
                 dict(t='enemy', type='cm_servant', x=41, y=10),
                 dict(t='cm_chandelier', x=19, y=2, len=88, swing=52, period=3.2, phase=0.0),
                 dict(t='cm_chandelier', x=34, y=2, len=88, swing=52, period=3.2, phase=0.5),
                 _pt(13, 6, 'c', ambush=True), _pt(29, 6, 'b', ambush=True), _pt(46, 6, 'd', ambush=True),
                 _pt(16, 6, 'a', lore='cm_gallery_a'), _pt(24, 6, 'e'), _pt(38, 6, 'c', lore='cm_child'), _pt(51, 6, 'a'),
                 dict(t='cm_diary', x=33, y=10, lore='cm_diary2'),
                 _cm('statue', 9, 10, sub='lady'), _cm('candelabra', 21, 10), _cm('candelabra', 43, 10), _cm('sconce', 3, 6)])
r.walls().open('W', 7, 10)
r.fill(0, 11, 54, 13).fill(0, 0, 54, 1)
r.fill(1, 2, 1, 6).put(1, 7, 'G').put(4, 10, 'L')      # gate onto the Court balcony, wall above it to the ceiling
r.fill(7, 0, 10, 1, '.')                                # stair shaft up to the Vestibule
for y in (8, 5, 2):
    r.fill(7, y, 10, y, '=')
r.fill(50, 11, 53, 13, '.').fill(50, 11, 53, 11, '=').fill(50, 13, 53, 13, '=')  # the Butler's stair comes up here
r.fill(39, 8, 41, 8, '=').fill(43, 6, 46, 6, '=')       # a gallery ledge (shard)
r.put(44, 5, 'i').put(28, 10, 'i').put(30, 10, 'C')
for x, y, ch in [(20, 10, 'k'), (48, 10, 'k'), (12, 2, 'r'), (27, 2, 'r'), (42, 2, 'r')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- CM8 The Crimson Vestibule (shrine before the ballroom)
r = Room('CM8', 'The Crimson Vestibule', 'crimson', 397, 33, 12, 14, indoor=True, shrine='Crimson Vestibule',
         spawns=[_pt(1, 6, 'a', lore='cm_vestibule'), _cm('candelabra', 6, 10), _cm('sconce', 10, 6)])
r.walls().open('E', 7, 10)
r.fill(0, 11, 11, 13).fill(0, 0, 11, 1)
r.fill(7, 11, 10, 13, '.').fill(7, 11, 10, 11, '=').fill(7, 13, 10, 13, '=')
r.put(3, 10, 'S').put(9, 2, 'r')

# ---------------------------------------------------------------- CM7 The Sanguine Ballroom (Countess Sanguine)
r = Room('CM7', 'The Sanguine Ballroom', 'crimson', 409, 29, 43, 18, indoor=True, boss='sanguine',
         spawns=[dict(t='boss', kind='sanguine', x=29, y=14),
                 dict(t='cm_chandelier', x=12, y=2, len=30, swing=0, big=True),
                 dict(t='cm_chandelier', x=30, y=2, len=30, swing=0, big=True),
                 _cm('candelabra', 5, 14), _cm('candelabra', 39, 14)])
r.walls().open('W', 11, 14)
r.fill(0, 15, 42, 17).fill(0, 0, 42, 1)
r.put(1, 14, 'F')

# ---------------------------------------------------------------- CM5 The Blood Cellars (side area: pools, hounds, loot)
r = Room('CM5', 'The Blood Cellars', 'crimson', 397, 73, 55, 11, indoor=True, items=['c_bloodvial', 'emberstone'], chests=['w:crimson_scythe'],
         spawns=[dict(t='enemy', type='cm_hound', x=21, y=7),
                 dict(t='enemy', type='cm_hound', x=38, y=7),
                 dict(t='enemy', type='cm_hound', x=47, y=7),
                 dict(t='enemy', type='cm_servant', x=8, y=7),
                 dict(t='cm_pool', x=12, y=8, w=5), dict(t='cm_pool', x=30, y=8, w=5), dict(t='cm_pool', x=42, y=8, w=3),
                 _cm('winerack', 4, 7), _cm('barrel', 19, 7), _cm('winerack', 25, 7), _cm('coffin', 37, 7, sub='closed'),
                 _cm('coffin', 40, 7, sub='open'), _cm('barrel', 50, 7), dict(t='cm_diary', x=46, y=7, lore='cm_diary3')])
r.walls().open('W', 4, 7)
r.fill(0, 8, 54, 10)
for x0, x1 in [(12, 16), (30, 34), (42, 44)]:
    r.fill(x0, 8, x1, 8, '.')          # sunken blood basins
r.fill(22, 1, 23, 2).fill(35, 1, 36, 2)                  # vault ribs
r.fill(26, 4, 29, 4, '=').put(27, 3, 'i')                # a wine shelf (c_bloodvial)
r.put(51, 7, 'i').put(53, 7, 'C')
for x, y, ch in [(9, 1, 'x'), (31, 1, 'x'), (45, 1, 'x'), (6, 7, 'k'), (18, 7, 'b')]:
    r.put(x, y, ch)
