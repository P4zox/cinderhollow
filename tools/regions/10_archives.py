# Ashen Archives finale (agent A): The Unwritten's arena, the Unbound Folio above it, Archives loot.
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).

# ---------------------------------------------------------------- A6 The Inkwell: rebuilt taller (11 rows of air)
# so the Unwritten can rise above the floor and fill the room with ink; the floor is 3 rows thick so the camera
# keeps the fight above the HUD. Its west door and floor stay where they
# were (global rows -35..-32 / -31), the room just grows upward into the Archives zone (gy -46).
r = ROOM('A6')
r.gy, r.h = -46, 18
r.g = [['.'] * r.w for _ in range(r.h)]
r.walls().open('W', 11, 14)
r.fill(0, 0, 35, 3).fill(0, 15, 35, 17)
r.fill(5, 0, 7, 3, '.')                      # a shaft up to the Unbound Folio (sealed by ink until the boss falls)
for x, y, ch in [(1, 14, 'F'), (11, 4, 'l'), (18, 4, 'x'), (25, 4, 'l'), (33, 14, 'k'), (21, 14, 'k'), (31, 4, 'x'),
                 (9, 14, 'I'), (17, 14, 'I'), (32, 14, 'I'), (2, 4, 'l')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'boss', 'kind': 'unwritten', 'x': 26, 'y': 14},
    {'t': 'ar2_book', 'x': 29, 'y': 14},
]

# ---------------------------------------------------------------- A7 The Unbound Folio (secret, above the Inkwell)
r = Room('A7', 'The Unbound Folio', 'archives', 324, -60, 24, 14, indoor=True, secret=True,
         items=['emberstone', 'emberstone'], chests=['art:backstep_slash'],
         spawns=[{'t': 'ar2_lore', 'x': 14, 'y': 12}])
r.walls().fill(5, 13, 7, 13, '=')                   # the shaft mouth: a thin ledge you can jump up through (drop: down + jump)
r.fill(20, 1, 22, 9)                                # a stack of fallen shelves in the corner ...
r.fill(20, 10, 20, 12, 'B')                         # ... hiding a nook behind a weak wall
for x, y, ch in [(10, 12, 'i'), (22, 12, 'i'), (17, 12, 'C'), (2, 12, 'k'), (12, 12, 'k'), (4, 1, 'l'), (15, 1, 'l'),
                 (9, 1, 'R'), (2, 1, 'x')]:
    r.put(x, y, ch)

# ---------------------------------------------------------------- loot through the Archives
r = ROOM('A1')                                      # a sealed reading nook low in the Lower Stacks
r.fill(1, 19, 5, 23)
r.fill(1, 21, 4, 22, '.')
r.fill(5, 21, 5, 22, 'B')
r.put(6, 23, '=')
r.put(2, 22, 'i')
r.kw['items'] = list(r.kw.get('items', [])) + ['shard']

r = ROOM('A2')                                      # beside the Archive Shrine, on the gallery's high end
r.put(41, 8, 'C')
r.kw['chests'] = list(r.kw.get('chests', [])) + ['sp:ink_seal']

r = ROOM('A4')                                      # on the top shelf of the spiral
r.put(14, 9, 'i')
r.kw['items'] = list(r.kw.get('items', [])) + ['w:pagecutter']

# ---------------------------------------------------------------- falling shelves (hazard)
# hanging shelf-cages drop when you pass beneath them; top-heavy bookcases topple toward you (creak + dust first)
def _cage(room_id, x, y):
    r = ROOM(room_id)
    if r.g[y][x] == 'R':
        r.put(x, y, '.')
    r.kw.setdefault('spawns', []).append({'t': 'ar2_cage', 'x': x, 'y': y})


for _rid, _x, _y in [('A2', 15, 2), ('A2', 29, 2), ('A5', 36, 2)]:
    _cage(_rid, _x, _y)
ROOM('A2').kw.setdefault('spawns', []).append({'t': 'ar2_topple', 'x': 24, 'y': 10, 'ground': True})
ROOM('A5').kw.setdefault('spawns', []).append({'t': 'ar2_topple', 'x': 17, 'y': 10, 'ground': True})
