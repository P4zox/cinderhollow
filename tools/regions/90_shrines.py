# ---- a shrine right before every boss (integrator). Region agents place shrines in their own regions; this covers the
# older rooms. Each shrine goes in the room you walk in from, on a free floor cell as close as possible to the arena door.
def _place_shrine(rid, toward, name):
    r = ROOM(rid); b = ROOM(toward)
    if r.kw.get('shrine'): return
    taken = {(s['x'], s['y']) for s in r.kw.get('spawns', [])}
    # which side of r faces the boss room
    cx_b = b.gx + b.w / 2 - r.gx
    order = sorted(range(2, r.w - 2), key=lambda x: abs(x - cx_b))
    for x in order:
        for y in range(r.h - 2, 1, -1):
            if (r.g[y][x] == '.' and r.g[y - 1][x] == '.' and r.g[y + 1][x] in SOLID
                    and all(r.g[y][xx] in '.' for xx in (x - 1, x + 1)) and (x, y) not in taken
                    and not any(abs(s['x'] - x) <= 1 and abs(s['y'] - y) <= 1 for s in r.kw.get('spawns', []))):
                r.put(x, y, 'S'); r.kw['shrine'] = name; return
    print('no shrine spot in', rid)

for _rid, _boss_room, _name in [
    ('K3', 'K4', 'Shrine of the Ascent'),          # Morvain
    ('M4', 'M5', 'Roadside Shrine'),                # Ser Kalden
    ('HF3', 'HF4', 'Sluice Shrine'),                # Ice Golem Warden
    ('D4', 'D5', 'Chute Shrine'),                   # Forge Overseer
    ('SP4', 'SP5', 'Hamlet Shrine'),                # Bell-Ringer
    ('X2', 'X3', 'Ascent Shrine'),                  # Gilded Sentinels
    ('R3', 'R4', 'Gatehouse Shrine'),               # Hollow Champion
]:
    _place_shrine(_rid, _boss_room, _name)
