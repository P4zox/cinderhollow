# ============================================================ v17 — agent AREA: THE COLD FORGE (+ THE ASHEN THRESHOLD)
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, HAZARD). Engine: web/src/82_forge.js.
# Art: art/gen_forge_env.py -> tiles_forge, tiles_threshold, bg_forge_far/mid, bg_threshold_far/mid, cf_props.
# Every module-level name here is prefixed _cf / _CF.  Contract: docs/v17/FORGE_CONTRACT.md, notes: docs/v17/forge_area.md.
#
# The forge lies under the Last Hearth (E6). The Expanse (E5) fills the ground right below the hearth, so the flue first
# runs east under the floor (the Ash Pit), along a soot duct over the Trial of the First Flame (the Long Flue), and only
# then drops (the Flue) into the cold workshops beneath the Expanse. Everything is walked edge to edge (no doors).
#
#   E6  The Last Hearth        (patched) a grate beside the hearth: Cinder Slam breaks it, the ash pit opens east
#   CF1 The Ash Pit            592..635 x  1..18   W: E6 (under the grate)        E (high): CF2
#   CF2 The Long Flue          636..699 x  0..8    W: CF1                         E: CF3 (top)
#   CF3 The Flue               700..727 x  0..61   W (top): CF2   W (foot): CF4   E (foot): CF12 (one-way gate)
#   CF4 The Hall of Racks      610..699 x 49..62   E: CF3   W (dais, anvil shutter): CF9   floor drain: CF5   (shrine)
#   CF9 The Reject Pile        572..609 x 49..60   E: CF4            the Unforged (mini-arena 1)
#   CF5 The Quench Cisterns    601..680 x 63..84   roof drain: CF4   E: CF6   cracked pier (slam): CF10
#   CF10 The Quenchmaster's Well 640..680 x 85..98 roof shaft: CF5   (secret)
#   CF6 The Bellows Gallery    681..760 x 68..86   W: CF5   E: CF7   floor grating: CF13   (two anvil shutters, vents)
#   CF13 The Tempering Vault   718..757 x 87..100  roof shaft: CF6   the Unforged (mini-arena 2)
#   CF7 The Anvil Court        761..804 x 68..86   W: CF6   E: CF8   roof W: CF12   roof E: CF11   (shrine)
#   CF12 The Slag Chute        728..772 x 40..67   W: CF3 (gate, lever inside)   floor: CF7   E: CF11
#   CF11 The Ledger Room       773..804 x 50..67   W: CF12   floor grating: CF7   (puzzle: three anvils in order)
#   CF8 The Hearth Below       805..862 x 66..86   W: CF7   E (the Great Furnace's doors): CT1   (boss: hearthkeeper)
#   CT1 The Ashen Threshold    863..902 x 70..86   W: CF8 (through the furnace)   E: CT2   (shrine)
#   CT2 The Last Gate          903..994 x 52..86   W: CT1   the shut gate (World 2 hook: CT_GATE in 82_forge.js) (vista)
#
# Custom spawns (82_forge.js): t='cf' kind = anvil | vents | bellows | rack | seal | grate | flueshaft | deco | furnace |
#   coals | gate2 | guardian | tank | steam | marker ...;  t='cf_foe' = a forge enemy (stand-in until FOES' type exists).
import os as _cf_os

SOLID.add('0')                   # the Great Furnace's breast in CF8: solid, drawn by the furnace sprite (82_forge.js)
_CF_NEEDS = ['talon', 'slam']
_CF_ROOT = _cf_os.path.join(_cf_os.path.dirname(_cf_os.path.abspath(__file__)), '..')   # (__file__ is tools/rooms.py: modules run in its namespace)


def _cf_foes_ready():
    """FOES' enemy ids, once their file defines them (until then the spawns are t='cf_foe' stand-ins)."""
    p = _cf_os.path.join(_CF_ROOT, 'web', 'src', '83_forge_foes.js')
    try:
        src = open(p).read()
    except OSError:
        return set()
    return {k for k in ('cf_smith', 'cf_wraith', 'cf_hulk', 'cf_mite', 'cf_unforged') if k in src}


_CF_READY = _cf_foes_ready()
_CF_AIR = set()                  # (no forge foe floats: the wraiths lie on the floor until they rise)


def _cf_room(id, name, gx, gy, w, h, biome='forge', **kw):
    kw.setdefault('needs', list(_CF_NEEDS))
    kw.setdefault('x3', True)
    kw.setdefault('indoor', True)
    return Room(id, name, biome, gx, gy, w, h, **kw)


def _sp(r, *items):
    r.kw.setdefault('spawns', []).extend(items)
    return r


def _K(kind, x, y, **kw): return dict(t='kit', kind=kind, x=x, y=y, **kw)
def _Y(kind, x, y, **kw): return dict(t='sys', kind=kind, x=x, y=y, **kw)
def _D(kind, x, y, **kw): return dict(t='cfa', kind=kind, x=x, y=y, **kw)


def _E(tp, x, y, **kw):
    air = tp in _CF_AIR or kw.pop('air', False)
    if tp in _CF_READY:
        d = dict(t='enemy', type=tp, x=x, y=y, **kw)
        if air: d['air'] = True
        return d
    return dict(t='cf_foe', type=tp, x=x, y=y, ground=not air, **kw)


# ================================================================================================ E6 (anchor)
# The Last Hearth: the hearth's stone floor runs on to the east wall over a soot grate (4 cells, flush with the hearth).
# Cinder Slam breaks it; the pit beneath opens east into the Ash Pit. E6's own grate down to the Expanse is untouched.
_e6 = ROOM('E6')
if all(_e6.g[15][x] == '.' for x in (28, 29, 30)) and all(_e6.g[16][x] == '#' for x in (28, 29, 30, 31)) and _e6.g[15][31] == '#':
    _e6.fill(28, 15, 31, 15, 'Y')                                 # the grate (slam), the east wall's cell included
    _e6.fill(28, 16, 31, 16, '.')                                 # the pit under it, open east into the Ash Pit
    for _s in _e6.kw.get('spawns', []):
        if _s.get('x') in (28, 29, 30, 31) and _s.get('y') == 15: _s['y'] = 14   # SC's ash pile now sits on the grate
    _e6.kw['needs'] = ['talon', 'slam']                          # (E6 is only reached through the Expanse, which needs slam)
    _sp(_e6, _D('grate', 28, 14, w=4), _D('draught', 29, 14))
else:
    print('FORGE: E6 floor changed; the grate down to the Cold Forge skipped')

# ================================================================================================ CF1 The Ash Pit
# Under the hearths, where their ash has fallen for a thousand years. The roof climbs east like the flue it is; dunes of
# old ash, the bones of a smith who came down to find out why the forge went cold. Warm light only at the grate.
r = _cf_room('CF1', 'The Ash Pit', 592, 1, 44, 18)
r.walls().open('W', 15, 16).open('E', 2, 5)
for _y in range(1, 15):
    r.fill(0, _y, min(42, 6 + (14 - _y) * 2), _y)                # the roof rises east from the low crawl under the grate
r.fill(38, 6, 42, 16)                                           # the high mouth of the duct (landing)
r.fill(12, 16, 17, 16).fill(13, 15, 16, 15)                     # an ash dune
r.fill(29, 16, 32, 16)
r.fill(19, 13, 23, 13, '=')                                     # a fallen iron flue-pipe
r.fill(26, 10, 30, 10)                                          # a corbel of flue brick
r.fill(33, 7, 36, 7, '=')
for x, y, ch in [(24, 11, 'r'), (31, 8, 'r'), (36, 5, 'x'), (9, 13, 'r'), (13, 11, 'r'), (17, 9, 'x'), (21, 7, 'r'), (27, 4, 'r'), (33, 2, 'x'), (40, 1, 'r')]:
    r.put(x, y, ch)
_sp(r, _E('cf_mite', 15, 14), _E('cf_mite', 21, 12), _E('cf_mite', 28, 9),
    _Y('lore', 8, 16, page='cfa_1', look='corpse'),
    _D('hearthglow', 1, 16), _D('ventlight', 37, 1), _D('ashdrift', 20, 16, w=22), _D('pipe', 34, 16), _D('soot', 31, 2, w=11),
    _D('deco', 25, 16, tag='scrap'), _D('deco', 40, 5, tag='flue_mouth', back=True))

# ================================================================================================ CF2 The Long Flue
# A soot duct that runs east above the Trial of the First Flame. A cold draught breathes up it from below, in pulses:
# the great bellows of the forge, still working with no fire to feed.
r = _cf_room('CF2', 'The Long Flue', 636, 0, 64, 9)
r.walls().open('W', 3, 6).open('E', 2, 6)
r.fill(0, 7, 63, 7)
r.fill(9, 7, 12, 7, '.').fill(30, 7, 34, 7, '.')                 # sunken flags (soot pools)
r.fill(14, 1, 17, 2).fill(40, 1, 44, 1).fill(52, 1, 54, 3)        # soot-caked brick hanging from the roof
r.fill(22, 6, 26, 6).fill(45, 6, 47, 6)                          # collapsed brick
for x, y, ch in [(6, 1, 'x'), (27, 1, 'x'), (37, 1, 'r'), (58, 1, 'x'), (19, 1, 'r')]:
    r.put(x, y, ch)
_sp(r, _K('wind', 18, 1, w=42, h=6, vx=-80, period=5, on=[0, 0.32], offset=0.2),
    _E('cf_mite', 20, 6), _E('cf_mite', 33, 7), _E('cf_mite', 49, 6), _E('cf_smith', 58, 6),
    _D('soot', 2, 1, w=60), _D('draughtmark', 62, 4), _D('ventlight', 30, 1), _D('ventlight', 58, 4), _D('deco', 28, 6, tag='scrap'), _D('deco', 41, 6, tag='bucket'))

# ================================================================================================ CF3 The Flue
# The great chimney down into the forge. One warm shaft falls from a grate at the top (the fires of the world above),
# lighting only the ledges it touches; below, the cold. Ledges every three courses; a chain hangs in the dark.
r = _cf_room('CF3', 'The Flue', 700, 0, 28, 62)
r.walls().open('W', 2, 6).open('W', 57, 60).open('E', 57, 60)
r.fill(1, 7, 5, 7)                                              # landing from the Long Flue
for y, x0, x1, ch in [(10, 7, 11, '='), (13, 14, 18, '#'), (16, 7, 11, '='), (19, 14, 19, '#'), (22, 21, 26, '='),
                      (25, 15, 19, '#'), (28, 5, 12, '='),
                      (31, 7, 11, '='), (34, 1, 5, '='), (37, 7, 11, '='), (40, 1, 5, '='), (43, 7, 11, '='),
                      (46, 3, 8, '='), (49, 10, 14, '='), (52, 17, 22, '#'), (55, 10, 15, '='), (58, 4, 8, '=')]:
    r.fill(x0, y, x1, y, ch)
r.fill(18, 28, 24, 28)                                          # an iron cross-beam (the chain hangs from it)
r.fill(12, 30, 15, 45)                                          # the flue's dividing pier
r.fill(22, 37, 26, 37)                                          # a ledge only the chain reaches easily
r.fill(17, 43, 21, 43, '=').fill(17, 46, 22, 46, '=')
r.fill(11, 60, 16, 60)                                          # the soot heap at the foot
r.fill(0, 56, 0, 56).fill(27, 56, 27, 56)
for x, y, ch in [(3, 1, 'x'), (24, 1, 'x'), (14, 29, 'x'), (6, 29, 'r'), (20, 53, 'r')]:
    r.put(x, y, ch)
_sp(r, _K('swing', 21, 29, len=7, rope='chain', amp=20),
    _E('cf_mite', 16, 12), _E('cf_mite', 23, 21), _E('cf_mite', 3, 33), _E('cf_mite', 19, 51),
    _Y('lore', 24, 36, page='cfa_2', look='corpse'),
    _D('flueshaft', 14, 1), _D('soot', 1, 1, w=26), _D('band', 1, 9, w=26), _D('band', 1, 27, w=26), _D('band', 1, 47, w=26),
    _D('deco', 21, 51, tag='bucket'), _D('deco', 13, 59, tag='scrap'))

# ================================================================================================ CF4 The Hall of Racks
# Thousands of unfinished blades hang point-down in arched bays: the Hallow's arms, never quenched. An anvil stands
# before an iron shutter; strike it hard and its ring lifts the shutter for a few breaths. A second shutter at the far
# end answers a second anvil: behind it, the pile where failed blades were thrown, and something they made of themselves.
r = _cf_room('CF4', 'The Hall of Racks', 610, 49, 90, 14, shrine='Shrine of the Racks')
r.walls().open('E', 8, 11).open('W', 6, 9)
r.fill(0, 12, 89, 12).fill(0, 1, 89, 1)
r.fill(59, 2, 61, 6)                                            # the lintel over shutter A (reaches the roof)
r.fill(0, 2, 3, 5).fill(1, 10, 8, 11)                           # the west dais and shutter B's lintel
r.fill(12, 12, 14, 13, '.')                                     # the drain down to the cisterns
r.fill(20, 10, 22, 11)                                          # an ingot stack (step up to the gallery)
r.fill(24, 8, 42, 8, '=')                                       # the racking gallery
r.fill(44, 5, 50, 5, '=')                                       # the high shelf
r.fill(72, 11, 74, 11)                                          # a quench trough
r.put(84, 11, 'S')
for x, y, ch in [(30, 2, 'x'), (47, 2, 'x'), (68, 2, 'x'), (80, 2, 'r'), (16, 2, 'x')]:
    r.put(x, y, ch)
_sp(r, _K('gate', 60, 11, id='sA', skin='iron'), _K('gate', 2, 9, id='sB', skin='iron'),
    _D('anvil', 66, 11, id='aA', keys=['sA'], note=0, mark='hammer'), _D('anvil', 55, 11, id='aA2', keys=['sA'], note=0, mark='hammer', small=True),
    _D('anvil', 17, 11, id='aB', keys=['sB'], note=3, mark='tongs'),
    _D('mark', 60, 7, mark='hammer'), _D('mark', 2, 6, mark='tongs'),
    _E('cf_smith', 40, 11), _E('cf_smith', 30, 7), _E('cf_mite', 47, 4), _E('cf_mite', 8, 9),
    _Y('lore', 49, 4, page='cfa_3', look='tablet'),
    *[_D('rack', x, 11, v=i % 3, back=True) for i, x in enumerate((26, 34, 42, 50, 70, 78))],
    _D('rack', 33, 7, v=1, small=True), _D('rack', 39, 7, v=2, small=True),
    _D('drainmark', 13, 11), _D('ventlight', 32, 2), _D('ventlight', 76, 2),
    _D('deco', 73, 10, tag='trough_blades'), _D('deco', 10, 11, tag='scrap'), _D('deco', 64, 11, tag='tongs_rack', back=True))

# ================================================================================================ CF9 The Reject Pile
# Where the failed blades were thrown. They did not stay thrown.
r = _cf_room('CF9', 'The Reject Pile', 572, 49, 38, 12, items=['emberstone'])
r.walls().open('E', 6, 9)
r.fill(0, 10, 37, 10).fill(0, 1, 37, 1)
r.fill(1, 2, 6, 3).fill(30, 2, 37, 5)
r.put(3, 9, 'i')
_sp(r, _E('cf_unforged', 13, 9, elite=1), _D('seal', 37, 9, h=4, foe='cf_unforged', flag='cf:unforged1', gate='sB'),
    _D('heap', 9, 9, w=10), _D('heap', 22, 9, w=6), _D('ventlight', 18, 2), _D('deco', 5, 9, tag='scrap'), _Y('lore', 33, 9, page='cfa_4', look='none'),
    _D('deco', 33, 9, tag='broken_rack'))

# ================================================================================================ CF5 The Quench Cisterns
# Where the blades were quenched. The water has stood still so long it has forgotten it was ever hot: black, mirror-still,
# and not empty. A drain from the Hall above; iron gratings over the tanks; the low road from pier to pier.
r = _cf_room('CF5', 'The Quench Cisterns', 601, 63, 80, 22)
r.walls().open('E', 11, 14)
r.fill(21, 0, 23, 0, '.').fill(18, 1, 20, 3).fill(24, 1, 26, 3)   # the drain shaft from the Hall of Racks
r.fill(16, 6, 28, 6, '=')                                        # the grating under the drain
r.fill(14, 9, 19, 9, '=').fill(22, 12, 26, 12, '=')                # the way down (and back up)
r.fill(33, 6, 40, 6, '=').fill(45, 7, 51, 7, '=').fill(56, 6, 63, 6, '=')   # the high road over the tanks
r.fill(64, 9, 67, 9, '=').fill(64, 12, 67, 12, '=')
r.fill(0, 15, 79, 21)                                           # the stone the tanks are cut into
for x0, x1 in [(7, 16), (21, 32), (37, 50), (55, 66)]:
    r.fill(x0, 15, x1, 20, '"')                                 # black water
for x0, x1 in [(11, 12), (26, 27), (43, 44), (60, 61)]:
    r.fill(x0, 14, x1, 20)                                      # stepping posts
r.fill(52, 15, 53, 21, 'Y')                                     # a cracked pier: slam, and it opens on the Well below
for x, y, ch in [(5, 1, 'x'), (32, 1, 'x'), (48, 1, 'x'), (71, 1, 'x'), (13, 1, 'r'), (58, 1, 'r')]:
    r.put(x, y, ch)
_sp(r, _E('cf_wraith', 19, 14), _E('cf_wraith', 35, 14), _E('cf_wraith', 54, 14), _E('cf_smith', 72, 14),
    _Y('lore', 3, 14, page='cfa_5', look='stone'),
    _D('stillwater', 8, 13), _D('ventlight', 40, 1), _D('ventlight', 70, 1), _D('steam', 14, 14), _D('steam', 40, 14), _D('steam', 63, 14),
    _D('tank', 22, 5, w=6, back=True), _D('crackhint', 52, 14), _D('drainmark', 22, 5, up=True),
    _D('deco', 75, 14, tag='quench_rack'), _D('deco', 2, 14, tag='bucket'))

# ================================================================================================ CF10 The Quenchmaster's Well (secret)
r = _cf_room('CF10', "The Quenchmaster's Well", 640, 85, 41, 14, secret=True, items=['shard'])
r.walls().fill(13, 0, 14, 0, '.')
r.fill(12, 1, 12, 3).fill(15, 1, 15, 3)                         # the shaft (the pier's core) comes down
r.fill(0, 12, 40, 12)
r.fill(9, 5, 17, 5, '=').fill(20, 7, 24, 7, '=')
r.fill(1, 8, 29, 11, '"')                                       # the well
r.fill(30, 8, 39, 11)                                           # the quenchmaster's step
r.fill(5, 9, 6, 11).fill(17, 10, 18, 11)
r.put(36, 7, 'i')
_sp(r, _Y('lore', 33, 7, page='cfa_6', look='corpse'), _D('stillwater', 8, 7), _D('deco', 38, 7, tag='ledger_desk', back=True),
    _D('deco', 31, 7, tag='bucket'))

# ================================================================================================ CF6 The Bellows Gallery
# The great bellows still breathe. Nothing feeds them; they breathe anyway, and every breath sends a gust down the gallery
# and wakes the old hearth vents in the floor for a moment: a wave of fire, then cold again. Two shutters, two anvils.
r = _cf_room('CF6', 'The Bellows Gallery', 681, 68, 80, 19)
r.walls().open('W', 6, 9).open('E', 12, 15)
r.fill(0, 1, 79, 1).fill(0, 16, 79, 17)
r.fill(1, 10, 6, 15)                                            # the landing from the cisterns
r.fill(9, 11, 27, 11, '=')                                      # the catwalk (anvil 1)
r.fill(31, 2, 33, 10)                                           # shutter 1's lintel
r.fill(36, 13, 39, 13, '=').fill(40, 10, 43, 10, '=').fill(44, 7, 47, 7, '=').fill(46, 5, 52, 5, '=')   # the ingot stair, the high ledge
r.fill(44, 16, 46, 16, '=').fill(44, 17, 46, 18, '.')            # the grating over the vault below
r.fill(57, 2, 59, 10)                                           # shutter 2's lintel
r.fill(66, 13, 69, 15)                                          # a dead hearth (step)
for x, y, ch in [(14, 2, 'x'), (24, 2, 'x'), (40, 2, 'x'), (52, 2, 'x'), (70, 2, 'x'), (64, 2, 'r')]:
    r.put(x, y, ch)
_sp(r, _K('gate', 32, 15, id='s1', skin='iron'), _K('gate', 58, 15, id='s2', skin='iron'),
    _D('anvil', 11, 10, id='a1', keys=['s1'], note=1, mark='flame', dur=8), _D('anvil', 35, 15, id='a1b', keys=['s1'], note=1, mark='flame', small=True),
    _D('anvil', 50, 4, id='a2', keys=['s2'], note=4, mark='ox', dur=8), _D('anvil', 61, 15, id='a2b', keys=['s2'], note=4, mark='ox', small=True),
    _D('mark', 32, 11, mark='flame'), _D('mark', 58, 11, mark='ox'),
    _D('vents', 9, 15, w=21, period=3.2, wave=1.1), _D('vents', 62, 15, w=4, period=2.4, wave=0.4, phase=0.5), _D('vents', 71, 15, w=6, period=2.4, wave=0.6, phase=1.2),
    _D('bellows', 19, 2, len=4, gust=dict(x=7, w=24, y=6, h=10, vx=-150), period=3.2, phase=0.0),
    _D('bellows', 41, 2, len=2, gust=dict(x=34, w=22, y=6, h=10, vx=-170), period=3.2, phase=1.6),
    _D('bellows', 53, 2, len=5, period=3.2, phase=1.6),
    _D('dropmark', 45, 15, to='CF13'), _D('ventlight', 64, 2), _D('ventlight', 24, 2),
    _E('cf_hulk', 50, 15), _E('cf_wraith', 64, 15), _E('cf_mite', 20, 10), _E('cf_mite', 38, 12), _E('cf_mite', 68, 12), _E('cf_smith', 26, 15),
    _Y('lore', 3, 9, page='cfa_7', look='tablet'),
    _D('deco', 76, 15, tag='ingots'), _D('deco', 8, 15, tag='scrap'))

# ================================================================================================ CF13 The Tempering Vault
# Below the gallery: the vault where finished blades were tempered. Something waits there, made of the ones that broke.
r = _cf_room('CF13', 'The Tempering Vault', 718, 87, 40, 14, items=['seed'])
r.walls().fill(0, 12, 39, 12)
r.fill(7, 0, 9, 0, '.').fill(6, 1, 6, 2).fill(10, 1, 10, 2)        # the shaft from the gallery
r.fill(4, 6, 9, 6, '=').fill(11, 9, 15, 9, '=')
r.fill(30, 2, 38, 3).fill(1, 2, 3, 3)
r.put(36, 11, 'i')
_sp(r, _E('cf_unforged', 26, 11, elite=2), _D('seal', 7, 1, w=3, horiz=True, foe='cf_unforged', flag='cf:unforged2'),
    _D('heap', 18, 11, w=8), _D('ventlight', 22, 1), _D('deco', 33, 11, tag='temper_rack', back=True), _D('deco', 3, 11, tag='scrap'),
    _Y('lore', 38, 11, page='cfa_8', look='none'), _D('deco', 38, 11, tag='quench_rack'))

# ================================================================================================ CF7 The Anvil Court
# The heart of the forge: the great anvil the Hallow's first sword was beaten on, cold as the rest. A shrine; two chimneys
# up to the ledger room and the slag chute (a shortcut back to the Flue).
r = _cf_room('CF7', 'The Anvil Court', 761, 68, 44, 19, shrine='Shrine of the Cold Anvil')
r.walls().open('W', 12, 15).open('E', 12, 15)
r.fill(0, 16, 43, 17)
r.fill(3, 0, 5, 0, '.').fill(0, 1, 2, 3).fill(6, 1, 9, 3)          # the west chimney (up to the Slag Chute)
r.fill(30, 0, 32, 0, '.').fill(26, 1, 29, 3).fill(33, 1, 36, 3)    # the east chimney (up to the Ledger Room)
r.fill(10, 1, 25, 1).fill(37, 1, 42, 1)
r.fill(4, 12, 8, 12, '=').fill(1, 9, 5, 9, '=').fill(4, 6, 8, 6, '=')
r.fill(28, 12, 32, 12, '=').fill(34, 9, 38, 9, '=').fill(28, 6, 33, 6, '=')
r.fill(17, 14, 25, 15)                                          # the great anvil's plinth
r.put(12, 15, 'S')
_sp(r, _D('anvil', 21, 13, id='aG', keys=[], note=2, mark='crown', great=True),
    _D('deco', 39, 15, tag='tongs_rack', back=True), _D('ventlight', 21, 2), _D('soot', 10, 2, w=16),
    _Y('lore', 37, 15, page='cfa_9', look='stone'), _D('deco', 2, 15, tag='ingots'))

# ================================================================================================ CF12 The Slag Chute
# The chute where the last slag ran out of the forge, set hard in a black river. A gate at its foot opens onto the Flue.
r = _cf_room('CF12', 'The Slag Chute', 728, 40, 45, 28)
r.walls().open('W', 17, 20).open('E', 22, 25)
r.fill(0, 1, 44, 1).fill(0, 2, 2, 16)
r.fill(1, 21, 22, 26)                                           # the upper floor (west)
r.fill(23, 22, 26, 26).fill(27, 23, 30, 26).fill(31, 24, 34, 26)   # the slag steps down
r.fill(31, 26, 44, 26)                                          # the lower floor (east)
r.fill(36, 26, 38, 27, '.').fill(35, 27, 35, 27).fill(39, 27, 39, 27)   # the chimney down to the Anvil Court
r.fill(9, 17, 14, 17, '=').fill(16, 13, 21, 13, '=').fill(24, 10, 30, 10)   # the slag fall (frozen) and its ledges
r.fill(33, 14, 38, 14, '=').fill(40, 18, 43, 18, '=')
for x, y, ch in [(12, 2, 'x'), (27, 2, 'r'), (40, 2, 'x')]:
    r.put(x, y, ch)
_sp(r, _K('gate', 1, 20, id='gS', skin='iron', persist=True),
    _K('lever', 4, 20, id='lS', targets=['gS'], once=True, msg='The gate grinds up. The Flue is just beyond.'),
    _E('cf_wraith', 12, 20), _E('cf_mite', 28, 9), _E('cf_hulk', 40, 25),
    _D('slagriver', 3, 2, w=40), _D('ventlight', 34, 2), _D('soot', 3, 2, w=38), _D('deco', 18, 20, tag='slag_cart'), _D('dropmark', 37, 25, to='CF7'))

# ================================================================================================ CF11 The Ledger Room (puzzle)
# The forge-master's room. His ledger lies open; three practice anvils, each stamped with a sign.
r = _cf_room('CF11', 'The Ledger Room', 773, 50, 32, 18, puzzle=True, items=['emberstone'])
r.walls().open('W', 12, 15)
r.fill(0, 16, 31, 16).fill(0, 1, 31, 1)
r.fill(18, 16, 20, 16, '=').fill(18, 17, 20, 17, '.')             # the grating down to the Anvil Court
r.fill(26, 2, 30, 10)                                           # the reliquary housing
r.fill(8, 12, 12, 12, '=').fill(14, 9, 19, 9, '=')
r.put(29, 15, 'i')
_sp(r, _K('gate', 27, 15, id='gR', skin='iron'),
    _D('anvil', 5, 15, id='p1', keys=[], note=4, mark='ox', small=True, seq='ledger'),
    _D('anvil', 11, 15, id='p2', keys=[], note=0, mark='hammer', small=True, seq='ledger'),
    _D('anvil', 23, 15, id='p3', keys=[], note=1, mark='flame', small=True, seq='ledger'),
    _D('ledger', 15, 15, order=['p1', 'p3', 'p2'], gate='gR', flag='cf:ledger'),
    _Y('lore', 15, 15, page='cfa_10', look='none'), _D('dropmark', 19, 15, to='CF7'),
    _D('deco', 2, 15, tag='ledger_desk', back=True), _D('deco', 16, 8, tag='scrap'), _E('cf_smith', 8, 15))

# ================================================================================================ CF8 The Hearth Below (boss)
# The forge's heart. The Great Furnace fills the far end, sealed by its own heat; a bed of coals before it is the only
# warm light in the forge. The keeper waits beside the fire. (Arena contract: docs/v17/forge_area.md.)
r = _cf_room('CF8', 'The Hearth Below', 805, 66, 58, 21, boss='hearthkeeper', entry='W')
r.walls().open('W', 14, 17).open('E', 12, 17)
r.fill(0, 18, 57, 19).fill(0, 1, 57, 1)
r.fill(51, 2, 57, 11, '0')                                      # the furnace's flank (invisible solid: its sprite draws it)
r.put(1, 17, 'F')
_sp(r, dict(t='boss', kind='hearthkeeper', x=40, y=17),
    _D('furnace', 47, 17), _D('coals', 38, 17, w=11), _D('bellows', 9, 2, len=3, arena=True), _D('bellows', 31, 2, len=3, arena=True),
    _D('soot', 2, 2, w=36))

# ================================================================================================ CT1 The Ashen Threshold
# Through the furnace's cold throat: a hall of pale stone, the way the keeper guarded. A shrine; a broken arch to the east.
r = _cf_room('CT1', 'The Ashen Threshold', 863, 70, 40, 17, biome='threshold', shrine='Shrine of the Threshold')
r.walls().open('W', 8, 13).open('E', 6, 13)
r.fill(0, 14, 39, 15).fill(0, 1, 39, 1)
r.fill(1, 2, 3, 7)                                              # the furnace's throat (its open leaf stands against it)
r.fill(30, 2, 39, 3).fill(34, 4, 39, 5)                         # the broken arch
r.put(14, 13, 'S')
_sp(r, _D('hall', 5, 13, w=30), _D('furnacedoor', 2, 13), _Y('lore', 22, 13, page='cfa_11', look='stone'), _D('ashup', 20, 13, w=20),
    _D('archlight', 36, 9))

# ================================================================================================ CT2 The Last Gate (vista)
# A causeway runs out into sourceless ash-light. At its end, alone, a gate older than the Hallow, shut.
r = _cf_room('CT2', 'The Last Gate', 903, 52, 92, 35, biome='threshold', vista=True, indoor=False)
r.walls(top=False).open('W', 24, 31)
r.fill(0, 32, 91, 33)
r.fill(1, 0, 3, 23)                                             # the threshold hall's outer wall
_sp(r, _Y('bench', 22, 31, id='bench', view=[72, 19], lore='cfa_12', face=1),
    _Y('lore', 46, 31, page='cfa_13', look='stone'),
    _D('gate2', 84, 31), _D('guardian', 76, 31), _D('guardian', 90, 31, face=-1),
    _D('balustrade', 4, 31, w=78), _D('ashup', 4, 31, w=86))
