# ============================================================ THE SUNSCORCHED DUNES (agent DU) -- the buried desert of the sun-kings
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Tiles (web/src/34_dunes.js): '-' quicksand (id 55, sinks you; jump out), '/' dune slope (id 56, the sand wedge under a
# sand-surfing slope; the slope line itself lives in the room's `du_slopes` list and the JS snaps bodies onto it).
# Gate: DU1 is a sand chasm over bottomless quicksand, far too wide to leap: only the Gale Cloak (gliding from thermal to
# thermal) crosses it. Shortcut: a sun-bronze hatch in DU1's east ledge, opened by DU7's lever, drops straight into DU7.
#
#   DU1 The Sand Gate          400..447 x  84..101   glide gate (thermals, a sand-fall), entered through D3's east wall
#   DU2 Sunward Shrine         448..495 x  84..103   shrine; first sand-surf slope, quicksand pit
#   DU3 The Colossus Dunes     496..559 x  84..105   dunes over a buried sun-king; sandstorms; c_scarab on the hand
#   DU4 Sandfall Shaft         560..583 x  84..123   the descent (sand-falls, climb back up)
#   DU5 Hieroglyph Halls       488..559 x 108..123   sun-altar beams on a timer; w:sun_sceptre
#   DU6 The Scarab's Pit       448..487 x 108..123   mini-boss: the Scarab Knight
#   DU7 Antechamber of the Sun 408..447 x 102..127   shrine + the hatch lever (shortcut up to DU1)
#   DU8 The Veiled Sanctum     400..455 x 128..145   main boss: the Veiled Pharaoh
SOLID |= set()          # '-' and '/' are not solid

# ---- anchor: open D3 (Slag Wards) east wall onto the Sand Gate
_d3 = ROOM('D3')
_d3.fill(47, 7, 47, 10, '.')


def du_slope(r, x0, y0, x1, y1):
    """A straight sand-surfing slope whose surface runs from tile corner (x0, y0) to (x1, y1) (x0 < x1).
    Cells crossed by the line (or just under it) become '/' (the non-solid sand wedge), cells well below become '#'."""
    r.kw.setdefault('du_slopes', []).append([x0, y0, x1, y1])
    k = (y1 - y0) / (x1 - x0)

    def ly(px):
        return (y0 + (px / 16.0 - x0) * k) * 16.0
    for cx in range(x0, x1):
        a, b = ly(cx * 16), ly(cx * 16 + 16)
        lo, hi = min(a, b), max(a, b)
        for cy in range(0, r.h):
            top = cy * 16
            if top >= hi + 3:
                r.g[cy][cx] = '#'
            elif top + 16 > lo:
                r.g[cy][cx] = '/'
    return r


# ---------------------------------------------------------------- DU1 The Sand Gate (glide gate)
r = Room('DU1', 'The Sand Gate', 'dunes', 400, 84, 48, 18, indoor=True, items=['emberstone'])
r.walls().open('W', 7, 10).open('E', 7, 10)
r.fill(0, 0, 47, 1)
r.fill(0, 11, 8, 17)                                        # take-off ledge (the door from the Deep)
r.fill(9, 17, 38, 17).fill(9, 12, 38, 16, '-')              # the chasm: bottomless quicksand (it swallows you)
r.fill(39, 11, 47, 17)                                      # far ledge
r.fill(41, 11, 42, 17, '.')                                 # hatch shaft down to DU7 (shortcut)
for _y in (11, 14, 17):
    r.fill(41, _y, 42, _y, '=')
r.fill(15, 4, 16, 11, '|').fill(31, 4, 32, 11, '|')         # thermals rising off the sun-baked sand
r.fill(34, 6, 37, 6, '=')                                   # a sun-king's broken lintel only a glider reaches
for x, y, ch in [(35, 5, 'i'), (4, 2, 'x'), (13, 2, 'x'), (27, 2, 'x'), (44, 2, 'x'), (2, 10, 'b'), (46, 10, 'k'), (39, 10, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'du_sandfall', 'x': 23, 'y': 2, 'y1': 11, 'air': True},
    {'t': 'du_hatch', 'x': 41, 'y': 11, 'side': 'top', 'air': True},
    {'t': 'du_stele', 'x': 5, 'y': 10, 'lore': 'du_gate'},
]
r.kw['du_abyss'] = True                                     # quicksand here is bottomless: sinking in = swallowed

# ---------------------------------------------------------------- DU2 Sunward Shrine
r = Room('DU2', 'Sunward Shrine', 'dunes', 448, 84, 48, 20, indoor=True, shrine='Sunward Shrine', chests=['emberstone'])
r.walls().open('W', 7, 10).open('E', 13, 16)
r.fill(0, 0, 47, 1)
r.fill(0, 11, 12, 19)                                       # shrine terrace
r.fill(13, 17, 47, 19)                                      # dune floor
du_slope(r, 13, 11, 25, 17)                                 # the first sand-surf slope
r.fill(29, 17, 33, 18, '-')                                 # quicksand pit (shallow: jump out)
r.fill(36, 12, 41, 12, '=')                                 # a toppled lintel over the pit
for x, y, ch in [(5, 10, 'S'), (46, 16, 'C'), (3, 2, 'x'), (20, 2, 'x'), (38, 2, 'x'), (10, 10, 'k'), (2, 10, 'b'), (27, 16, 'b'), (43, 16, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'enemy', 'type': 'du_priest', 'x': 38, 'y': 11},
    {'t': 'enemy', 'type': 'du_scarab', 'x': 40, 'y': 16},
    {'t': 'du_stele', 'x': 8, 'y': 10, 'lore': 'du_shrine'},
]

# ---------------------------------------------------------------- DU3 The Colossus Dunes (sandstorms)
r = Room('DU3', 'The Colossus Dunes', 'dunes', 496, 84, 64, 22, indoor=True, items=['c_scarab'], chests=['emberstone'])
r.walls().open('W', 13, 16).open('E', 11, 14)
r.fill(0, 0, 63, 1)
r.fill(0, 17, 10, 21)                                       # west flats
du_slope(r, 11, 17, 19, 13)                                 # up the dune
r.fill(19, 13, 24, 21)                                      # the crest
du_slope(r, 25, 13, 37, 19)                                 # the long slide down
r.fill(37, 19, 63, 21)
r.fill(38, 19, 44, 20, '-')                                 # quicksand basin
r.fill(40, 10, 43, 11)                                      # the colossus' upturned palm, risen out of the sand
r.fill(38, 7, 39, 18, '|')                                  # heat rising off the basin: glide up to the palm
du_slope(r, 45, 19, 53, 15)                                 # back up to the plateau
r.fill(53, 15, 63, 21)
for x, y, ch in [(41, 9, 'i'), (60, 14, 'C'), (6, 2, 'x'), (30, 2, 'x'), (50, 2, 'x'), (4, 16, 'b'), (21, 12, 'b'), (57, 14, 'k')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'enemy', 'type': 'du_scarab', 'x': 7, 'y': 16},
    {'t': 'enemy', 'type': 'du_priest', 'x': 22, 'y': 12},
    {'t': 'enemy', 'type': 'du_jackal', 'x': 57, 'y': 14},
    {'t': 'du_colossus', 'x': 30, 'y': 4, 'air': True},
    {'t': 'du_storm', 'x': 2, 'y': 16, 'air': True, 'dir': 1},
]

# ---------------------------------------------------------------- DU4 Sandfall Shaft (the descent)
r = Room('DU4', 'Sandfall Shaft', 'dunes', 560, 84, 24, 40, indoor=True, items=['shard'])
r.walls().open('W', 11, 14).open('W', 32, 35)
r.fill(0, 0, 23, 1)
r.fill(0, 15, 6, 16)                                        # entry ledge
r.fill(0, 36, 23, 39)                                       # the floor far below
for y, x0, x1 in [(18, 9, 13), (21, 15, 19), (24, 9, 13), (27, 3, 7), (30, 9, 13), (33, 15, 19)]:
    r.fill(x0, y, x1, y, '=')                               # the zigzag down (and back up)
r.fill(9, 12, 12, 12, '=').fill(16, 9, 19, 9, '=').fill(19, 6, 22, 6, '=')   # up to the shard alcove
r.fill(20, 7, 22, 8)                                        # the alcove's broken sill
for x, y, ch in [(21, 5, 'i'), (4, 2, 'x'), (13, 2, 'x'), (3, 35, 'b'), (20, 35, 'k'), (5, 14, 'k'), (11, 17, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'du_sandfall', 'x': 21, 'y': 2, 'y1': 5, 'air': True},
    {'t': 'du_sandfall', 'x': 14, 'y': 2, 'y1': 35, 'air': True, 'thin': True},
    {'t': 'du_sandfall', 'x': 1, 'y': 17, 'y1': 35, 'air': True},
    {'t': 'enemy', 'type': 'du_priest', 'x': 5, 'y': 26},
    {'t': 'enemy', 'type': 'du_scarab', 'x': 11, 'y': 35},
]

# ---------------------------------------------------------------- DU5 Hieroglyph Halls (sun-altar beams)
r = Room('DU5', 'Hieroglyph Halls', 'dunes', 488, 108, 72, 16, indoor=True, chests=['w:sun_sceptre'], items=['sp:sunbeam'])
r.walls().open('E', 8, 11).open('W', 8, 11)
r.fill(0, 0, 71, 1)
r.fill(0, 12, 71, 15)
r.fill(30, 9, 41, 11)                                       # the sun dais
r.fill(33, 6, 38, 6, '=')                                   # a gallery over the dais
r.fill(8, 8, 12, 8, '=').fill(58, 8, 62, 8, '=')
for x, y, ch in [(36, 5, 'i'), (35, 8, 'C'), (5, 2, 'x'), (20, 2, 'x'), (50, 2, 'x'), (66, 2, 'x'), (2, 11, 'k'), (69, 11, 'k'),
                 (26, 11, 'b'), (46, 11, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [
    {'t': 'du_altar', 'x': 16, 'y': 2, 'air': True, 'ph': 0.0},
    {'t': 'du_altar', 'x': 24, 'y': 2, 'air': True, 'ph': 1.1},
    {'t': 'du_altar', 'x': 47, 'y': 2, 'air': True, 'ph': 0.0},
    {'t': 'du_altar', 'x': 55, 'y': 2, 'air': True, 'ph': 1.1},
    {'t': 'enemy', 'type': 'du_jackal', 'x': 62, 'y': 11},
    {'t': 'enemy', 'type': 'du_priest', 'x': 36, 'y': 8},
    {'t': 'enemy', 'type': 'du_jackal', 'x': 12, 'y': 11},
    {'t': 'enemy', 'type': 'du_scarab', 'x': 50, 'y': 11},
    {'t': 'du_stele', 'x': 68, 'y': 11, 'lore': 'du_halls'},
    {'t': 'du_stele', 'x': 4, 'y': 11, 'lore': 'du_pharaoh'},
]

# ---------------------------------------------------------------- DU6 The Scarab's Pit (mini-boss arena)
r = Room('DU6', "The Scarab's Pit", 'dunes', 448, 108, 40, 16, indoor=True, boss='scarab', entry='E', items=['emberstone'])
r.walls().open('E', 8, 11).open('W', 8, 11)
r.fill(0, 12, 39, 15).fill(0, 0, 39, 1)
r.fill(1, 2, 1, 6).fill(38, 2, 38, 6)                        # wall above both fogs up to the ceiling
for x, y, ch in [(38, 11, 'F'), (1, 11, 'F'), (20, 8, 'i'), (6, 2, 'x'), (19, 2, 'x'), (32, 2, 'x'), (4, 11, 'b'), (35, 11, 'b')]:
    r.put(x, y, ch)
r.fill(18, 9, 22, 9, '=')
r.kw['spawns'] = [{'t': 'boss', 'kind': 'scarab', 'x': 14, 'y': 11}]

# ---------------------------------------------------------------- DU7 Antechamber of the Sun (shrine, shortcut lever)
r = Room('DU7', 'Antechamber of the Sun', 'dunes', 408, 102, 40, 26, indoor=True, shrine='Antechamber Shrine', items=['emberstone'])
r.walls().open('E', 14, 17).open('N', 33, 34).open('S', 2, 4)
r.fill(0, 18, 39, 21)                                       # hall floor
r.fill(0, 22, 39, 25)
r.fill(1, 19, 5, 24, '.').fill(2, 18, 4, 25, '.')         # the stair-well down to the Sanctum
r.fill(2, 18, 4, 18, '=')                                   # thin floor over it (drop: hold down + jump; col 2 falls straight through)
r.fill(4, 19, 5, 19, '=').fill(4, 22, 5, 22, '=').fill(3, 25, 4, 25, '=')   # the climb back up
r.fill(0, 0, 31, 7).fill(36, 0, 39, 7)                      # heavy masonry above the hall
r.fill(32, 0, 32, 9).fill(35, 0, 35, 9)                     # the shaft up to the Sand Gate
for y in (2, 5, 8):
    r.fill(33, y, 34, y, '=')
r.fill(33, 11, 34, 11, '=').fill(33, 14, 34, 14, '=')
r.fill(28, 15, 31, 15, '=')
for x, y, ch in [(20, 17, 'S'), (30, 17, 'L'), (29, 14, 'i'), (8, 9, 'x'), (16, 9, 'x'), (25, 9, 'x'), (12, 17, 'k'), (38, 17, 'k'),
                 (7, 17, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'du_hatch', 'x': 33, 'y': 0, 'side': 'bottom', 'air': True}, {'t': 'du_stele', 'x': 15, 'y': 17, 'lore': 'du_ante'},
                  {'t': 'du_dropmark', 'x': 2, 'y': 17, 'air': True}]

# ---------------------------------------------------------------- DU8 The Veiled Sanctum (the Veiled Pharaoh)
r = Room('DU8', 'The Veiled Sanctum', 'dunes', 400, 128, 56, 18, indoor=True, boss='pharaoh', entry='W')
r.walls().open('N', 10, 12)
r.fill(0, 15, 55, 17).fill(0, 0, 9, 0).fill(13, 0, 55, 0)
r.fill(15, 0, 15, 9)                                        # wall above the fog, up to the ceiling
for y, x0, x1 in [(2, 10, 12), (5, 10, 12), (6, 5, 8), (9, 10, 13), (12, 5, 8)]:
    r.fill(x0, y, x1, y, '=')                               # the climb back up out of the lobby
for x, y, ch in [(15, 14, 'F'), (3, 14, 'k'), (12, 14, 'b'), (22, 3, 'x'), (34, 3, 'x'), (46, 3, 'x'), (52, 14, 'b')]:
    r.put(x, y, ch)
r.kw['spawns'] = [{'t': 'boss', 'kind': 'pharaoh', 'x': 40, 'y': 14}]
