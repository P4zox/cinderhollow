# Old-area secrets + lore graves (agent A, round 2). Runs inside tools/rooms.py's namespace after every region module.
#   Cinder Slam caches: a cracked floor 'Y' over a pocket dug into a thick floor (slam through, grab the loot, jump out).
#   Root Hook secrets: a lone ledge high under the ceiling, out of reach of jumps, with a golden ring '@' beside it.
#   Lore graves 'g' in the new regions (text lives in LORE, web/src/10_story.js).
# Every edit checks the cells it needs first and skips (with a note) if another module has changed that spot.

def _scan_lists(r, new_cells):
    """rebuild r.kw items / chests / graves in scan order after new cells were placed.
    new_cells: {(x, y): value}; old values keep their relative order."""
    for ch, key in (('i', 'items'), ('C', 'chests'), ('g', 'graves')):
        old = list(r.kw.get(key, []))
        out = []
        for y in range(r.h):
            for x in range(r.w):
                if r.g[y][x] != ch:
                    continue
                if (x, y) in new_cells:
                    out.append(new_cells[(x, y)])
                elif old:
                    out.append(old.pop(0))
        if out or key in r.kw:
            r.kw[key] = out


def _cells_are(r, cells, allowed):
    return all(0 <= x < r.w and 0 <= y < r.h and r.g[y][x] in allowed for x, y in cells)


def slam_cache(room_id, x0, x1, row, ch, item):
    """Y at `row` (x0..x1) over a one-row pocket; the loot `ch` ('i' or 'C') sits in the pocket's middle"""
    r = next((R for R in ROOMS if R.id == room_id), None)
    if r is None:
        print(f'oldsecrets: no room {room_id}'); return
    need = [(x, y) for x in range(x0 - 1, x1 + 2) for y in (row, row + 1, row + 2)]
    if not _cells_are(r, need, '#'):
        print(f'oldsecrets: {room_id} floor at {x0}-{x1},{row} changed; slam cache skipped'); return
    for x in range(x0, x1 + 1):
        r.g[row][x] = 'Y'
        r.g[row + 1][x] = '.'
    cx = (x0 + x1) // 2
    r.g[row + 1][cx] = ch
    _scan_lists(r, {(cx, row + 1): item})


def hook_ledge(room_id, x0, x1, row, ch, item, hook):
    """a one-row stone ledge under the ceiling with loot on it, and a hook ring nearby"""
    r = next((R for R in ROOMS if R.id == room_id), None)
    if r is None:
        print(f'oldsecrets: no room {room_id}'); return
    hx, hy = hook
    need = [(x, y) for x in range(x0 - 1, x1 + 2) for y in (row - 2, row - 1, row, row + 1) if y >= 1] + [(hx, hy)]
    if not _cells_are(r, need, '.xrl'):
        print(f'oldsecrets: {room_id} air at {x0}-{x1},{row} changed; hook ledge skipped'); return
    for x in range(x0, x1 + 1):
        r.g[row][x] = '#'
    cx = (x0 + x1) // 2
    r.g[row - 1][cx] = ch
    r.g[hy][hx] = '@'
    _scan_lists(r, {(cx, row - 1): item})


def lore_grave(room_id, key, pref_x):
    """put a grave on the lowest walkable floor near pref_x, clear of doors and spawns"""
    r = next((R for R in ROOMS if R.id == room_id), None)
    if r is None:
        print(f'oldsecrets: no room {room_id} for grave {key}'); return
    busy = {(s['x'], s['y']) for s in r.kw.get('spawns', [])}
    busy |= {(s['x'] + dx, s['y']) for s in r.kw.get('spawns', []) for dx in (-1, 1)}
    for dx in sorted(range(-(r.w), r.w), key=abs):
        x = pref_x + dx
        if not (2 <= x < r.w - 2):
            continue
        for y in range(r.h - 2, 0, -1):
            near = {r.g[y][xx] for xx in range(max(0, x - 3), min(r.w, x + 4))}
            if r.g[y][x] == '.' and r.g[y + 1][x] == '#' and (x, y) not in busy and not (near & set('SNCALGiEgOT|%@')) \
                    and r.g[y][x - 1] in '.#' and r.g[y][x + 1] in '.#' and r.g[y - 1][x] == '.' \
                    and all(abs(sx - x) > 2 or sy != y for sx, sy in busy):
                r.g[y][x] = 'g'
                _scan_lists(r, {(x, y): key})
                return
    print(f'oldsecrets: no spot for grave {key} in {room_id}')


# ---------------------------------------------------------------- Cinder Slam caches (need Cinder Slam, from the Colossus)
slam_cache('C4', 14, 16, 11, 'i', 'charmslot')      # Rootgate: under the shrine hall's worn flagstones
slam_cache('R2', 29, 31, 11, 'i', 'shard')          # Broken Rampart: a sealed sally-port in the wall-walk
slam_cache('K2', 24, 26, 11, 'C', 'slot')           # Flooded Aisle: a buried reliquary under the nave
slam_cache('C3', 5, 7, 11, 'i', 'emberstone')       # Hall of Roots: a root-choked ossuary niche

# ---------------------------------------------------------------- Root Hook secrets (need the Root Hook, from the Unwritten)
# The ring hangs high, ~90px to the side: jump, grab it at full rope length, swing through, let go at the top of the
# swing above the ledge. The ledges sit 96px over the floor, just past the apex of a double jump.
hook_ledge('M2', 9, 13, 5, 'i', 'herb', (19, 2))            # the Weeping Mire: a drowned saint's shelf
hook_ledge('K1', 40, 43, 5, 'C', 'emberstone', (33, 2))     # the Nave: an organ loft no stair reaches

# ---------------------------------------------------------------- lore graves in the new regions (text: LORE in 10_story.js)
for _rid, _key, _x in [('HF5', 'hf1', 6), ('HF6', 'hf2', 40), ('SP4', 'sp1', 25), ('SP6', 'sp2', 6),
                       ('D3', 'dp1', 8), ('D7', 'dp2', 12), ('E2', 'e1', 24)]:
    lore_grave(_rid, _key, _x)
