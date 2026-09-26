# ============================================================ THE STARFALL CRATER (agent SF) — where a star fell and killed the old gods
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING).
# Zone x 470..760, y -100..-16. Entered from X4 (Crown Shrine): a fallen star lies under a crust of black glass on
# X4's floor; a Cinder Slam onto it wakes a stair of floating shards up into SF1 (web/src/35_starfall.js).
# Tiles: '+' starlight (id 60, non-solid: low gravity inside), '?' star-glass (id 61, solid, too smooth to cling to).
# Enemies: sf_pilgrim, sf_golem, sf_wisp (flying). Bosses: orrery (SF5, mini), astrel (SF7).
# Moonstep secrets (post-boss): the floating island in SF2 and the Last Light (SF9) off the Crater Rim.
SOLID.update('?')
FLYING.add('sf_wisp')


def _sfd(kind, x, y, **kw):
    return dict(t='sf_prop', kind=kind, x=x, y=y, **kw)


def _en(tp, x, y, **kw):
    return dict(t='enemy', type=tp, x=x, y=y, **kw)


def _zone(r, x0, y0, x1, y1):
    """paint starlight ('+', low gravity) over empty cells only"""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if r.g[y][x] == '.':
                r.g[y][x] = '+'


# ---------------------------------------------------------------- X4 (anchor): the fallen star under the glass + the shard stair
_x4 = ROOM('X4')
_x4.kw.setdefault('spawns', []).extend([
    dict(t='sf_cairn', x=5, y=10),
])

# ---------------------------------------------------------------- SF1 The Shard Stair (connector; open bottom onto X4's sky)
r = Room('SF1', 'The Shard Stair', 'starfall', 492, -40, 24, 26, items=['emberstone'],
         spawns=[_en('sf_wisp', 17, 17, air=True), _sfd('shard', 6, 4), _sfd('shard', 19, 18), _sfd('arch', 19, 4)])
r.fill(0, 0, 0, 25).fill(23, 0, 23, 0).fill(23, 5, 23, 25)
r.fill(15, 5, 22, 12)                        # the ledge up to the plains (east exit rows 1..4)
r.fill(15, 12, 22, 12, '?')                  # its glassy underside
for y, x0, x1 in [(23, 2, 5), (19, 8, 11), (15, 2, 5), (11, 8, 11), (8, 11, 13), (7, 2, 5)]:
    r.fill(x0, y, x1, y, '=')
r.put(3, 6, 'i')
_zone(r, 1, 12, 14, 24)
_zone(r, 15, 13, 22, 24)

# ---------------------------------------------------------------- SF2 The Black Glass Plains
r = Room('SF2', 'The Black Glass Plains', 'starfall', 516, -48, 64, 16, chests=['w:meteor_maul'], items=['shard'],
         spawns=[_en('sf_pilgrim', 15, 12), _en('sf_golem', 39, 12), _en('sf_pilgrim', 54, 12), _en('sf_wisp', 28, 6, air=True),
                 _sfd('godbone', 8, 12), _sfd('spire', 17, 12), _sfd('spire', 41, 12), _sfd('godbone', 61, 12), _sfd('shard', 24, 3),
                 _sfd('shard', 52, 5)])
r.fill(0, 0, 0, 8).fill(63, 0, 63, 8)
r.fill(0, 13, 63, 15)
r.fill(20, 13, 25, 14, '.').fill(20, 14, 25, 14, '^')     # a rift of glass teeth
r.fill(10, 11, 13, 12).fill(9, 12, 14, 12)                # low mound
r.fill(31, 11, 35, 12).fill(32, 10, 34, 10)                # the chest mound
r.put(33, 9, 'C')
r.fill(44, 10, 49, 12)                                     # the tall mound (launch for the Moonstep island)
r.fill(56, 11, 59, 12)
r.fill(44, 2, 48, 2, '?').fill(45, 3, 47, 3, '?')          # a floating shard of star-glass, far out of reach
r.put(46, 1, 'i')
_zone(r, 19, 4, 26, 12)

# ---------------------------------------------------------------- SF3 Shrine of the Fallen Sky
r = Room('SF3', 'Shrine of the Fallen Sky', 'starfall', 580, -48, 24, 16, shrine='Shrine of the Fallen Sky', graves=['sf_shrine'],
         spawns=[_sfd('idol', 5, 12), _sfd('spire', 20, 12), _sfd('shard', 16, 4)])
r.fill(0, 0, 0, 8).fill(23, 0, 23, 8).fill(0, 13, 23, 15)
r.put(12, 12, 'S').put(17, 12, 'g')

# ---------------------------------------------------------------- SF4 The Shattered Observatory (tower)
r = Room('SF4', 'The Shattered Observatory', 'starfall', 604, -84, 28, 52, items=['sp:comet', 'emberstone'], shrine='Observatory Shrine',
         spawns=[_en('sf_pilgrim', 10, 48), _en('sf_golem', 8, 39), _en('sf_pilgrim', 20, 30), _en('sf_pilgrim', 12, 21),
                 _en('sf_wisp', 12, 26, air=True), _en('sf_wisp', 16, 7, air=True),
                 _sfd('telescope', 7, 21), _sfd('lens', 20, 48), _sfd('arch', 12, 12), _sfd('shard', 6, 4), _sfd('orrering', 22, 39)])
r.fill(0, 0, 0, 51).fill(27, 0, 27, 51).fill(0, 49, 27, 51)
r.fill(0, 45, 0, 48, '.').fill(27, 45, 27, 48, '.').fill(27, 9, 27, 12, '.')
r.fill(1, 40, 18, 40).fill(9, 31, 26, 31).fill(1, 22, 18, 22).fill(9, 13, 26, 13)
for y, x0, x1 in [(44, 21, 24), (36, 3, 6), (27, 21, 24), (18, 3, 6)]:
    r.fill(x0, y, x1, y, '=')
r.fill(1, 3, 2, 5, '?').fill(25, 3, 26, 6, '?').fill(3, 2, 4, 2, '?').fill(22, 1, 24, 2, '?')   # the broken dome
r.put(3, 21, 'i').put(25, 30, 'i').put(21, 12, 'S')

# ---------------------------------------------------------------- SF5 The Orrery Hall (mini-boss)
r = Room('SF5', 'Hall of the Orrery', 'starfall', 632, -84, 40, 16, boss='orrery',
         spawns=[dict(t='boss', kind='orrery', x=20, y=12), _sfd('lens', 6, 12), _sfd('lens', 33, 12)])
r.fill(0, 0, 0, 15).fill(39, 0, 39, 15).fill(0, 13, 39, 15)
r.fill(0, 9, 0, 12, '.').fill(39, 9, 39, 12, '.')
r.fill(1, 0, 6, 1).fill(33, 0, 38, 1).fill(1, 2, 3, 2).fill(36, 2, 38, 2)   # stumps of the fallen dome
r.put(1, 12, 'F').put(38, 12, 'F')

# ---------------------------------------------------------------- SF6 The Crater Rim (descent; Moonstep ledge to the Last Light)
r = Room('SF6', 'The Crater Rim', 'starfall', 672, -84, 28, 52, shrine='Crater Heart Shrine',
         spawns=[_en('sf_golem', 23, 19), _en('sf_pilgrim', 22, 32), _en('sf_wisp', 16, 28, air=True), _en('sf_pilgrim', 4, 12),
                 _sfd('spire', 2, 48), _sfd('godbone', 12, 48), _sfd('shard', 18, 6)])
r.fill(0, 0, 0, 51).fill(27, 0, 27, 51, '?').fill(0, 49, 27, 51)
r.fill(0, 9, 0, 12, '.').fill(0, 45, 0, 48, '.').fill(27, 45, 27, 48, '.').fill(27, 2, 27, 4, '.')
r.fill(0, 13, 8, 14)                          # the rim you arrive on
r.fill(13, 12, 15, 12, '=')                   # a shard to hop across on
r.fill(21, 13, 26, 14).fill(21, 15, 26, 15, '?')   # the high ledge under the Last Light (8 tiles below it)
r.fill(9, 18, 12, 18, '=')
for y, x0, x1 in [(24, 7, 10), (36, 7, 10)]:
    r.fill(x0, y, x1, y, '=')
r.fill(1, 30, 4, 30).fill(1, 42, 4, 42)
r.fill(20, 20, 26, 21).fill(18, 33, 26, 34)   # east ledges
r.fill(22, 22, 26, 25, '?')
_zone(r, 2, 16, 12, 47)
r.put(21, 48, 'S')

# ---------------------------------------------------------------- SF8 The Undercroft of Lenses (shortcut: lever gate back to the tower)
r = Room('SF8', 'The Undercroft of Lenses', 'starfall', 632, -48, 40, 16, indoor=True,
         spawns=[_en('sf_golem', 22, 12), _en('sf_wisp', 18, 6, air=True), _sfd('lens', 14, 12), _sfd('lens', 28, 12)])
r.walls().fill(0, 13, 39, 15)
r.fill(0, 9, 0, 12, '.').fill(39, 9, 39, 12, '.')
r.fill(1, 1, 9, 8).fill(34, 1, 38, 8)
r.put(5, 9, 'G').fill(5, 1, 5, 8)
r.put(36, 12, 'L')

# ---------------------------------------------------------------- SF7 The Crater Heart (Astrel)
r = Room('SF7', 'The Crater Heart', 'starfall', 700, -52, 48, 20, boss='astrel', graves=['sf_astrel'],
         spawns=[dict(t='boss', kind='astrel', x=30, y=16), _sfd('spire', 4, 16), _sfd('spire', 44, 16)])
r.fill(0, 0, 0, 19).fill(47, 0, 47, 19).fill(0, 17, 47, 19)
r.fill(0, 13, 0, 16, '.')
r.put(1, 16, 'F').put(45, 16, 'g')

# ---------------------------------------------------------------- SF9 The Last Light (Moonstep secret)
r = Room('SF9', 'The Last Light', 'starfall', 700, -92, 20, 14, secret=True, items=['c_orrery', 'emberstone'], graves=['sf_lastlight'],
         spawns=[_sfd('shard', 10, 4), _sfd('idol', 15, 12)])
r.fill(0, 0, 0, 13).fill(19, 0, 19, 13).fill(0, 13, 19, 13)
r.fill(0, 10, 0, 12, '.')
r.put(8, 12, 'i').put(12, 12, 'i').put(4, 12, 'g')
