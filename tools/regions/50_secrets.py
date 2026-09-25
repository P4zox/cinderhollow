# X — secrets & mini-bosses (docs/EXPANSION_CONTRACT.md §2 agent X). Runs inside tools/rooms.py's namespace.
#   Hermit's Hollow (H1) behind R1's west cliff: golden seal '$' (only a fully charged heavy breaks it), Oswin.
#   Hollow Champion gauntlet inside R4 (challenger's banner), Gilded Sentinel pair inside X3,
#   Knight's Sword & Shield chest in R2, and Ember's Hollow (E1-E3) beneath X4's cracked floor (First Ember).
# Map chars: '$' golden seal (tile id 25, solid until broken, JS side) · '&' sky gap in a cave's back wall (id 26).
# Everything else is placed with spawns=[...] (handlers in web/src/24_secrets.js).

# ------------------------------------------------------------------ R1: the golden seal on the far-left cliff wall
r = ROOM('R1')
for y in (8, 9, 10):
    r.put(0, y, '$').put(1, y, '$')
r.kw.setdefault('spawns', []).append({'t': 'sc_seal', 'x': 2, 'y': 10})

# ------------------------------------------------------------------ H1: The Hermit's Hollow (x -40..-1, y 0..13)
r = Room('H1', "The Hermit's Hollow", 'hermit', -40, 0, 40, 14, indoor=True, secret=True, boss='oswin')
r.walls().open('E', 8, 10)
r.fill(0, 11, 39, 13)                               # floor
r.fill(0, 0, 39, 1)                                 # ceiling
r.fill(28, 0, 39, 7)                                # low roof over the narrow passage
r.fill(24, 2, 27, 3).fill(26, 4, 27, 5)             # the roof steps down into the passage
r.fill(1, 2, 3, 4).fill(1, 5, 1, 6)                 # rock shoulder, top-left
r.fill(1, 9, 5, 10)                                 # a raised stone shelf (the hermit's bed-ledge)
r.fill(9, 2, 10, 2)                                 # stalactite stubs
for y in range(3, 8):                               # the gap in the rock: the Pale Root beyond
    for x in range(15, 22):
        if not ((y == 3 and x in (15, 21)) or (y == 7 and x in (15, 21))):
            r.put(x, y, '&')
for x, y, ch in [(3, 8, 'k'), (25, 10, 'k'), (8, 2, 'r'), (23, 4, 'r'), (34, 10, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'sc_fire', 'x': 9, 'y': 10},
    {'t': 'sc_flags', 'x': 4, 'y': 2, 'x1': 24},
    {'t': 'sc_mat', 'x': 18, 'y': 10},
    {'t': 'sc_cairn', 'x': 23, 'y': 10},
    {'t': 'boss', 'kind': 'oswin', 'x': 12, 'y': 10},
    {'t': 'sc_fog', 'x': 27, 'y': 10, 'kind': 'oswin', 'top': 4},
]

# ------------------------------------------------------------------ R2: the Knight's Sword & Shield on the high ledge
r = ROOM('R2')
r.put(45, 7, 'C')
r.kw['chests'] = r.kw.get('chests', []) + ['w:knight_shield']

# ------------------------------------------------------------------ R4: the Hollow Champion's gauntlet
r = ROOM('R4')
r.kw.setdefault('spawns', []).extend([
    {'t': 'sc_banner', 'x': 19, 'y': 10},
    {'t': 'boss', 'kind': 'champion', 'x': 28, 'y': 10},
    {'t': 'sc_fog', 'x': 8, 'y': 10, 'kind': 'champion', 'top': 0, 'gauntlet': 1},
    {'t': 'sc_fog', 'x': 38, 'y': 10, 'kind': 'champion', 'top': 0, 'gauntlet': 1},
])

# ------------------------------------------------------------------ X3: the Gilded Sentinel pair (replaces the lone 'n')
r = ROOM('X3')
r.put(28, 10, '.')
r.put(14, 10, '.').put(18, 10, '.').put(34, 3, '.')     # clear the root-spawns and the seraph: a clean duel
r.kw.setdefault('spawns', []).extend([
    {'t': 'boss', 'kind': 'sentinels', 'x': 30, 'y': 10},
    {'t': 'sc_fog', 'x': 7, 'y': 10, 'kind': 'sentinels', 'top': 0},
    {'t': 'sc_fog', 'x': 46, 'y': 10, 'kind': 'sentinels', 'top': 0},
])
r.kw['boss'] = 'sentinels'

# ------------------------------------------------------------------ X4: cracked floor (Cinder Slam) into Ember's Hollow
r = ROOM('X4')
r.fill(16, 11, 18, 13, 'Y')

# ------------------------------------------------------------------ Ember's Hollow (x 444..600, y 0..40)
# E1: the Cinder Well — fall in under X4's cracked floor, burn through an ash veil (Ember Dash), drop to the bottom.
r = Room('E1', 'The Cinder Well', 'ember', 500, 0, 24, 24, indoor=True, secret=True)
r.walls().open('N', 8, 10).open('W', 19, 22)
r.fill(1, 7, 15, 8)                                 # ledge A (landing)
r.fill(15, 1, 15, 2)
r.fill(15, 3, 15, 6, '%')                           # ash veil: only Ember Dash passes
r.fill(16, 1, 22, 1)
r.fill(18, 13, 22, 13, '=').fill(16, 17, 19, 17, '=')   # ledges that break the long fall
r.fill(1, 9, 3, 18)                                 # rock column under ledge A
r.fill(4, 9, 6, 11)
r.fill(6, 22, 9, 22, '^')                           # ember thorns (jump them on the way west)
for x, y, ch in [(3, 6, 'k'), (20, 22, 'k'), (12, 1, 'r'), (19, 12, 'b'), (5, 6, 'b')]:
    r.put(x, y, ch)

# E2: the Ashen Span — a chasm of ember thorns crossed on Root Hook rings; a shrine on the far side.
r = Room('E2', 'The Ashen Span', 'ember', 452, 12, 48, 14, indoor=True, shrine="Ember's Hollow")
r.walls().open('E', 7, 10)
r.fill(0, 0, 47, 1)
r.fill(0, 11, 11, 13).fill(36, 11, 47, 13)          # the two banks
r.fill(12, 13, 35, 13).fill(12, 12, 35, 12, '^')    # the chasm floor: thorns
r.fill(2, 11, 4, 13, '.')                           # the drop into the Hollow below
for y in range(5, 14):
    r.put(3, y, '|')                                # a hot updraft: the way back up (Gale Cloak)
r.fill(21, 2, 22, 2)                                # a hanging rock
for x, y in [(31, 2), (25, 2), (19, 3), (13, 2)]:
    r.put(x, y, '@')
for x, y, ch in [(8, 10, 'S'), (44, 10, 'k'), (38, 10, 'b'), (22, 2, 'r'), (40, 2, 'r'), (6, 10, 'k')]:
    r.put(x, y, ch)

# E3: Ember's Hollow — the First Ember's arena.
r = Room('E3', "Ember's Hollow", 'ember', 452, 26, 48, 14, indoor=True, boss='first_ember')
r.walls().open('N', 2, 4)
r.fill(0, 11, 47, 13)
for y in range(1, 11):
    r.put(3, y, '|')
r.fill(12, 1, 14, 2).fill(33, 1, 36, 2)             # hanging basalt
for x, y, ch in [(9, 10, 'k'), (40, 10, 'k'), (20, 1, 'r'), (28, 1, 'r'), (44, 10, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'sc_ashes', 'x': 28, 'y': 10},
    {'t': 'boss', 'kind': 'first_ember', 'x': 28, 'y': 10},
]
