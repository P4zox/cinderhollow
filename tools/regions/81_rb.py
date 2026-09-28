# Expansion 3, agent RB: new rooms for the Weeping Mire (M7-M14), the Ashen Archives (A8-A16) and the Hoarfrost
# Aqueduct (HF8-HF15). Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, HAZARD, free_spot).
# Engine side: web/src/51_rb.js (decor 'xrb' spawns, ink abyss tile '9', index/cipher puzzles, freezing basins, charms).
# Art: art/gen_xrb.py -> assets xrb_*.
# Every module-level name here is prefixed _rb / RB so region modules sharing this namespace never collide.
#
# Wings (EXPANSION3 §8: every link is an edge you walk, jump or drop through; no doors):
#   Mire      W3 (the Root Drop, C3 -> M1, redesigned here) -> east into M7 Drowned Grove -> M8 Boardwalk -> M10 Sinking Stones
#             -> M11 Rotwood Bridges -> M9 Reed Maze -> down through a gated trapdoor into M1 (the loop-back shortcut).
#             Off the spine: M13 Leech Pits (gauntlet, off M8), M14 Fisherman's Rest (vista, off M10), M12 Valve House
#             (puzzle, joins M11's high exit and M9's low exit). Shrines: M7, M9.
#   Archives  A5 (Chained Stacks) -> up into A8 Grand Stacks -> A10 Ladder Well -> A9 Copy Room / A11 Page Storm -> A14 ...;
#             the loop-back is a drop from A8's west end into A4 (Spiral of Shelves). Off the spine: A13 Cipher Wall -> A12
#             Index Room (east of A8), A15 Hookline Trial (off A10; its goal climbs out into A9), A16 Forbidden Annex (behind
#             a false bookcase in A9), A11 Page Storm -> A14 Reading Nook. Shrines: A8, A10.
#   Hoarfrost HF6 -> up through HF16 the Rime Stair -> HF10 Frozen Conduit -> HF8 Frozen Falls -> HF11 Long Slide -> HF12
#             Icicle Gallery -> HF9 Pump Station -> east into the Falls' west cliff -> down to the Conduit -> HF6.
#             Off the spine: HF13 Brazier Locks (a puzzle shortcut from HF9 down to HF10), HF14 Frostbitten Overlook and
#             HF15 Rimebreaker Trial (both off HF11; the trial's goal steps out into the Overlook). Shrines: HF10, HF11.

HAZARD.add('9')                            # '9' ink abyss (Archives): not solid, a hazard you fall into
FLYING.update({'gloom_wisp', 'hf_wraith', 'hf_lurker', 'grimoire'})


def _rbK(kind, x, y, **kw):                 # KM kit part
    return dict(t='kit', kind=kind, x=x, y=y, **kw)


def _rbS(kind, x, y, **kw):                 # KS system
    return dict(t='sys', kind=kind, x=x, y=y, **kw)


def _rbD(deco, x, y, **kw):                 # RB decor (web/src/51_rb.js XRB_DECO); k= is the fog density etc.
    return dict(t='xrb', d=deco, x=x, y=y, **kw)


def _rbE(type, x, y, **kw):                 # enemy spawn
    return dict(t='enemy', type=type, x=x, y=y, **kw)


def _rbput(r, pts):
    for x, y, ch in pts:
        r.put(x, y, ch)


def _rbgate(r, gx, gy, lx, lintel_top=0):
    """the loop-back's one-way shortcut gate (EXPANSION3 §8.2): a gate at column gx (hanging from a lintel that reaches the
    ceiling) and a once-lever at (lx, gy) on the wing side. Coming up from the old room first you meet the closed gate."""
    r.fill(gx, lintel_top, gx, gy - 4)
    return [_rbK('gate', gx, gy, id='scg', persist=True),
            _rbK('lever', lx, gy, id='scl', targets=['scg'], once=True, msg='The gate lifts. A way back opens.')]


# ======================================================================================================== WEEPING MIRE
# zone (§8.1) x 153..252, y 57..145, between the Catacombs and the shifted Mire; W3 (the story shaft C3 -> M1) runs down
# its west side at x 153..164 and is redesigned below (POST_LINKS). The wing hangs east of it:
#   M7 Drowned Grove (165, 64) 78x24
#   M8 Boardwalk (165, 88) 48x14       M13 Leech Pits (213, 88) 30x14
#   M10 Sinking Stones (165,102) 48x16 M14 Fisherman's Rest (213,102) 30x16
#   M11 Rotwood Bridges (165,118) 42x14 M12 Valve House (207,118) 36x24
#   M9 Reed Maze (165,132) 42x14   -> its floor trapdoor drops into M1 (the loop-back)
_RBM = (15, -35)                              # (dx, dy) from the wing's first layout: every internal link keeps its alignment
def _rbM(x, y): return x + _RBM[0], y + _RBM[1]

# M1: a second opening in its roof (the Reed Maze's trapdoor lands here) and a ledge to reach it from M1's own stair
_rb = ROOM('M1')
_rb.open('N', 15, 17).fill(14, 1, 18, 1, '=')

# ---------------------------------------------------------------- W3 The Root Drop (the story shaft C3 -> M1), redesigned
# Twelve wide instead of six: a root-choked chasm with a zigzag of ledges every three rows (climbable with no abilities),
# the Grove's mouth opening east halfway down. Built after the generated shafts exist (rooms.py POST_LINKS).
def _rbW3():
    r = ROOM('W3')
    top_open = [x for x in range(r.w) if r.g[0][x] != '#']            # the generator's openings (C3's trapdoor / M1's roof)
    gx0 = r.gx + min(top_open); bot_open = [r.gx + x for x in range(r.w) if r.g[r.h - 1][x] != '#']
    r.gx, r.w = 153, 12
    r.g = [['.'] * r.w for _ in range(r.h)]
    r.walls()
    for gx in range(gx0, gx0 + len(top_open)): r.g[0][gx - r.gx] = '.'
    for gx in bot_open: r.g[r.h - 1][gx - r.gx] = '='          # thin boards over M1's roof: stand on them, drop through
    h = r.h
    mid = [x - r.gx for x in range(gx0, gx0 + len(top_open))]
    r.fill(min(mid) - 1, 2, max(mid) + 1, 2, '=')                 # just under C3's trapdoor
    ys = list(range(h - 4, 4, -3))
    for i, y in enumerate(ys):
        x0 = 1 if i % 2 == 0 else 6
        r.fill(x0, y, x0 + 4, y, '=')
    r.open('E', 20, 23).fill(6, 24, 11, 24, '=')                  # the Grove's mouth (M7's west wall rows 12..15)
    r.fill(1, 44, 4, 45)                                          # a root-shelf halfway down
    for x0, y0, x1, y1 in [(1, 10, 1, 16), (10, 30, 10, 38), (1, 58, 1, 66), (10, 70, 10, 80)]:
        r.fill(x0, y0, x1, y1)                                    # root buttresses along the walls
    r.kw['spawns'] = [
        *[_rbD('m_moss', x, y) for x, y in [(3, 1), (8, 1), (5, 20), (9, 40), (2, 50), (7, 62), (4, 75), (9, 85)]],
        *[_rbD('m_mush', x, y) for x, y in [(2, 43), (3, 43), (7, 23), (2, 86)]],
        _rbD('m_lantpost', 4, 43), _rbD('m_lantpost', 9, 23), _rbD('m_fog', 1, 70, w=10, h=18),
        _rbD('m_fireflies', 1, 30, w=10, h=30),
    ]
    _rbput(r, [(3, 1, 'r'), (8, 1, 'r'), (6, 30, 'l'), (4, 60, 'l')])
POST_LINKS = globals().setdefault('POST_LINKS', [])
POST_LINKS.append(_rbW3)

# ---------------------------------------------------------------- M7 The Drowned Grove (grand)
# High route: the arrival ledge (NE), over the Weeping Tree's limbs to the west bank. Low route: down the east bank and
# across the marsh on islands and sinking lily pads. Secret route: a rotten wall in the tree's mound opens the hollow roots.
r = Room('M7', 'The Drowned Grove', 'mire', *_rbM(150, 99), 78, 24, indoor=True, x3=True, grand=True, needs=['talon'],
         items=['emberstone'], shrine='Shrine of the Weeping Tree')
r.walls()
r.fill(0, 0, 77, 1)                                 # the root ceiling
for x0, x1, y in [(8, 13, 2), (24, 30, 2), (41, 44, 2), (55, 61, 2), (66, 70, 2), (27, 28, 3), (58, 59, 3)]:
    r.fill(x0, y, x1, y)                            # hanging root masses
r.fill(0, 21, 77, 23)                               # peat floor
r.fill(2, 21, 4, 23, '.').fill(2, 23, 4, 23, '=')   # the drop to the Boardwalk (thin boards)
r.fill(7, 21, 19, 22, '~')                          # west pool
r.fill(28, 21, 31, 22, '~')
r.fill(44, 21, 57, 22, '~')                         # east pool
r.fill(21, 19, 26, 20)                              # spitter island
r.fill(32, 17, 42, 20)                              # the Weeping Tree's mound
r.fill(33, 18, 40, 20, '.')                         # ... hollow inside (the secret route)
r.fill(32, 18, 32, 20, 'B').fill(41, 18, 41, 20, 'B')   # rotten root walls, west and east
r.fill(33, 20, 40, 20, '#')                         # hollow floor
r.fill(59, 19, 64, 20)                              # witch island
r.fill(67, 16, 76, 20)                              # east bank
r.fill(66, 7, 76, 8)                                # the old fishers' lookout (NE)
r.open('W', 12, 15).put(0, 16, '=')                 # in from the Root Drop, onto the lowest limb
r.fill(58, 10, 62, 10, '=').fill(62, 13, 65, 13, '=')    # steps down to the east bank
# high route: limbs of the Weeping Tree and the dead trees
for x0, x1, y in [(55, 61, 8), (46, 52, 6), (36, 43, 5), (28, 34, 8), (18, 24, 7), (10, 15, 9), (3, 8, 12), (1, 4, 16)]:
    r.fill(x0, y, x1, y, '=')
_rbput(r, [(36, 19, 'i'), (24, 18, 'p'), (61, 18, 'm'), (70, 15, 'h'), (48, 5, 'f'), (20, 6, 'c'), (12, 20, 'r'),
           (5, 2, 'l'), (34, 2, 'l'), (50, 2, 'l'), (63, 2, 'l'), (74, 6, 'k'), (67, 6, 'b'), (9, 20, 'b'), (6, 20, 'S')])
r.kw['spawns'] = [
    *[_rbK('sinker', x, 21, w=2, depth=2, rate=0.6) for x in (9, 13, 17, 46, 50, 54)],
    _rbD('m_bigtree', 36, 16, ox=32, layer='back'), _rbD('m_tree', 13, 20, v=1, layer='back'), _rbD('m_tree', 62, 18, v=0, layer='back', flip=1),
    _rbD('m_tree', 26, 18, v=2, layer='back'),
    *[_rbD('m_reeds', x, 20, v=v) for x, v in [(20, 1), (27, 0), (43, 1), (58, 0), (66, 1)]],
    *[_rbD('m_lily', x, 20) for x in (8, 15, 48, 52)],
    *[_rbD('m_moss', x, y) for x, y in [(10, 3), (26, 3), (29, 4), (43, 3), (57, 3), (68, 3), (18, 2), (47, 2)]],
    *[_rbD('m_mush', x, y) for x, y in [(22, 18), (40, 16), (60, 18), (75, 15), (34, 16), (1, 20)]],
    _rbD('m_lantpost', 1, 20), _rbD('m_lantpost', 69, 6),
    _rbD('m_fog', 1, 16, w=76, h=6), _rbD('m_fireflies', 41, 10, w=30, h=8),
    _rbE('gloom_wisp', 30, 12), _rbE('rot_crawler', 42, 4), _rbE('bog_spitter', 10, 8),
]

# ---------------------------------------------------------------- M8 Boardwalk of Stilts (path)
r = Room('M8', 'Boardwalk of Stilts', 'mire', *_rbM(150, 123), 48, 14, indoor=True, x3=True, needs=['talon'])
r.walls()
r.fill(2, 0, 4, 0, '.')                             # up to the Grove
r.fill(1, 2, 5, 2, '=').fill(3, 5, 8, 5, '=')       # landing + step
r.fill(0, 8, 5, 13)                                 # west bank
r.fill(6, 11, 37, 12, '~').fill(6, 13, 37, 13)      # the rot under the boards
r.fill(38, 10, 46, 13)                              # east bank
r.fill(40, 10, 42, 12, '.').fill(40, 13, 42, 13, '=')   # the drop to the Sinking Stones
r.open('E', 5, 9)                                   # to the Leech Pits
for x0, x1 in [(6, 11), (15, 21), (24, 29), (33, 37)]:
    r.fill(x0, 9, x1, 9, '=')                       # the boardwalk sections
r.fill(12, 6, 14, 6, '=').fill(30, 6, 32, 6, '=')   # the old high boards over the gaps
_rbput(r, [(44, 9, 'm'), (9, 1, 'l'), (27, 1, 'l'), (40, 1, 'l'), (2, 7, 'b'), (18, 1, 'x'), (35, 1, 'x')])
r.kw['spawns'] = [
    *[_rbD('m_stilt', x, 12) for x in (7, 11, 15, 21, 24, 29, 33, 37)],
    *[_rbD('m_reeds', x, 10, v=v, fg=1) for x, v in [(13, 0), (22, 1), (31, 0)]],
    *[_rbD('m_lily', x, 10) for x in (9, 19, 26, 35)],
    _rbD('m_boat', 36, 10), _rbD('m_net', 44, 9, layer='back'), _rbD('m_lantpost', 5, 7), _rbD('m_sign', 43, 9, v=1),
    _rbD('m_moss', 7, 1), _rbD('m_moss', 23, 1), _rbD('m_moss', 38, 1), _rbD('m_tree', 20, 12, v=2, layer='back'),
    _rbD('m_fog', 6, 8, w=32, h=5),
    dict(t='xrb_ambush', type='bog_spitter', x=13, y=8, r=70), dict(t='xrb_ambush', type='rot_crawler', x=26, y=8, r=60),
    dict(t='xrb_ambush', type='bog_spitter', x=34, y=8, r=70),
]

# ---------------------------------------------------------------- M13 Leech Pits (gauntlet, off the Boardwalk)
r = Room('M13', 'Leech Pits', 'mire', *_rbM(198, 123), 30, 14, indoor=True, x3=True, gauntlet=True, needs=['talon'])
r.walls()
r.fill(0, 0, 29, 1)
r.open('W', 5, 9).fill(0, 10, 5, 13)                # entry ledge from the Boardwalk
r.fill(6, 11, 29, 13)
r.fill(9, 11, 12, 12, '~').fill(18, 11, 21, 12, '~')    # the leech pits
r.fill(24, 8, 28, 10)                               # the witch's bank
r.fill(8, 6, 11, 6, '=').fill(19, 6, 22, 6, '=')    # spitter perches
r.fill(3, 2, 3, 5)                                  # lintel over the gate
_rbput(r, [(10, 2, 'l'), (21, 2, 'l'), (27, 7, 'b'), (15, 10, 'b'), (1, 9, 'k')])
r.kw['spawns'] = [
    _rbK('gate', 3, 9, id='gW', open=True),
    _rbS('gauntlet', 15, 10, id='leech', look='stake', name='The Leech Pits', gates=['gW'],
         waves=[[_rbE('rot_crawler', 8, 10), _rbE('rot_crawler', 16, 10), _rbE('rot_crawler', 23, 10)],
                [_rbE('bog_spitter', 9, 5), _rbE('bog_spitter', 20, 5), _rbE('rot_crawler', 14, 10)],
                [_rbE('mire_witch', 26, 7), _rbE('rot_crawler', 8, 10), _rbE('bog_spitter', 20, 5)],
                [_rbE('rot_hulk', 15, 10)]],
         reward=['emberstone', 800]),
    *[_rbD('m_stakes', x, 10) for x in (7, 14, 23)], _rbD('m_mush', 26, 7), _rbD('m_mush', 17, 10),
    _rbD('m_moss', 6, 2), _rbD('m_moss', 14, 2), _rbD('m_moss', 25, 2), _rbD('m_reeds', 13, 10, v=1),
    _rbD('m_fog', 6, 8, w=24, h=4),
]

# ---------------------------------------------------------------- M10 Sinking Stones (parkour)
r = Room('M10', 'Sinking Stones', 'mire', *_rbM(150, 137), 48, 16, indoor=True, x3=True, parkour=True, needs=['talon'])
r.walls()
r.fill(40, 0, 42, 0, '.')                           # up to the Boardwalk
r.fill(40, 2, 42, 2, '=').fill(44, 4, 46, 4, '=').fill(43, 7, 46, 7, '=')
r.fill(36, 9, 47, 15)                               # east bank
r.open('E', 5, 8)                                   # to the Fisherman's Rest
r.fill(9, 11, 35, 14, '~')                          # deep rot
r.fill(8, 11, 8, 15)                                # stake lip of the west bank
r.fill(0, 13, 7, 15)                                # west bank
r.fill(2, 13, 4, 14, '.').fill(2, 15, 4, 15, '=')   # the drop to the Rotwood Bridges
r.fill(9, 14, 10, 14, '=').fill(34, 12, 35, 12, '=')    # climb-outs for the unlucky
r.fill(20, 1, 24, 2).fill(30, 1, 31, 3)             # root masses
_rbput(r, [(44, 8, 'k'), (5, 12, 'b'), (38, 8, 'b'), (14, 1, 'l'), (31, 4, 'l'), (6, 1, 'r'), (27, 1, 'r')])
r.kw['spawns'] = [
    *[_rbK('sinker', x, 11, w=2, depth=3, rate=1.1, delay=0.5) for x in (31, 26, 21, 16, 11)],
    _rbD('m_mush', 1, 12), _rbD('m_lantpost', 6, 12), _rbD('m_sign', 3, 12, v=1),
    *[_rbD('m_moss', x, y) for x, y in [(21, 3), (23, 3), (30, 4), (10, 1), (17, 1), (36, 1)]],
    _rbD('m_tree', 42, 8, v=0, layer='back'), _rbD('m_stakes', 37, 8), _rbD('m_reeds', 45, 8, v=1),
    _rbD('m_fog', 9, 9, w=27, h=4), _rbD('m_fireflies', 22, 6, w=14, h=4),
    _rbE('gloom_wisp', 22, 5),
]

# ---------------------------------------------------------------- M14 Fisherman's Rest (vista)
r = Room('M14', "Fisherman's Rest", 'mire', *_rbM(198, 137), 30, 16, indoor=True, x3=True, vista=True, needs=['talon'])
r.walls().open('W', 5, 8)
r.fill(0, 9, 3, 15)                                 # the dock's landing
r.fill(4, 12, 28, 13, '~').fill(4, 14, 28, 15)      # the still marsh
r.fill(4, 9, 22, 9, '=')                            # the dock
r.fill(9, 8, 20, 8, '.')
r.fill(11, 9, 19, 9)                                # the hut's floor (on stilts)
_rbput(r, [(2, 8, 'k')])
r.kw['spawns'] = [
    _rbD('m_hut', 15, 8, layer='back'), _rbD('m_backdrop', 1, 1, w=30, h=16, scene='mire'),
    *[_rbD('m_stilt', x, 11) for x in (5, 9, 12, 18, 21)],
    _rbD('m_table', 18, 8), _rbD('m_lantpost', 21, 8), _rbD('m_net', 7, 8, layer='back'), _rbD('m_boat', 25, 11),
    *[_rbD('m_lily', x, 11) for x in (23, 27, 7)], _rbD('m_reeds', 27, 11, v=0), _rbD('m_reeds', 5, 11, v=1),
    _rbD('m_fog', 0, 7, w=30, h=7, k=1.4), _rbD('m_fireflies', 20, 6, w=16, h=5),
    _rbS('bench', 13, 8, id='bench', view=[22, 6], lore='rb_2'),
    _rbS('lore', 18, 8, page='rb_1', look='none'),
]

# ---------------------------------------------------------------- M11 Rotwood Bridges (parkour)
r = Room('M11', 'Rotwood Bridges', 'mire', *_rbM(150, 153), 42, 14, indoor=True, x3=True, parkour=True, needs=['talon'],
         items=['seed'])
r.walls()
r.fill(2, 0, 4, 0, '.')                             # up to the Sinking Stones
r.fill(1, 2, 5, 2, '=').fill(5, 4, 7, 4, '=')
r.fill(0, 6, 7, 13)                                 # west cliff
r.fill(20, 6, 22, 13)                               # the middle stack
r.fill(34, 6, 41, 13)                               # east cliff
r.fill(36, 6, 38, 12, '.').fill(36, 13, 38, 13, '=')    # down through the cliff to the Reed Maze
r.open('E', 2, 5)                                   # the Valve House's high door
r.fill(8, 11, 19, 12, '~').fill(23, 11, 33, 12, '~')
r.fill(8, 12, 19, 12, '^').fill(23, 12, 33, 12, '^')    # rotten stakes under the rot
r.fill(26, 2, 29, 2, '=')                           # the seed ledge (reach it from the rope)
_rbput(r, [(28, 1, 'i'), (3, 5, 'b'), (41, 5, 'k'), (14, 1, 'l'), (31, 1, 'x'), (10, 1, 'r')])
r.kw['spawns'] = [
    *[_rbK('crumble', x, 6, w=2, delay=0.35, respawn=4.5) for x in (8, 10, 12, 14, 16, 18)],
    *[_rbK('crumble', x, 6, w=2, delay=0.35, respawn=4.5) for x in (23, 25, 27, 29, 31)],
    _rbK('crumble', 33, 6, w=1, delay=0.35, respawn=4.5),
    _rbK('swing', 24, 1, len=5, rope='vine'),
    _rbD('m_posts', 7, 5), _rbD('m_posts', 20, 5), _rbD('m_posts', 22, 5), _rbD('m_posts', 34, 5),
    dict(t='xrb_ropes', x=8, y=5, spans=[[7, 20, 6], [22, 34, 6]]),
    _rbD('m_mush', 2, 5), _rbD('m_mush', 21, 5), _rbD('m_sign', 37, 5, v=1),
    *[_rbD('m_moss', x, 1) for x in (8, 17, 24, 33)], _rbD('m_fog', 8, 8, w=26, h=4),
    _rbE('gloom_wisp', 14, 3), _rbE('bog_spitter', 40, 5),
]

# ---------------------------------------------------------------- M9 The Reed Maze (path) -> door to M4
r = Room('M9', 'The Reed Maze', 'mire', *_rbM(150, 167), 42, 14, indoor=True, x3=True, needs=['talon'], chests=['gold'],
         shrine='Reedwater Shrine')
r.walls()
r.fill(36, 0, 38, 0, '.')                           # up to the Rotwood Bridges
r.fill(35, 2, 39, 2, '=').fill(31, 4, 34, 4, '=')
r.fill(0, 11, 41, 13)                               # floor
r.fill(36, 9, 41, 10)                               # east rise
r.open('E', 5, 8)                                   # the Valve House's low door
r.fill(0, 0, 4, 6)                                  # the vestibule's roof
r.fill(2, 11, 4, 12, '.').fill(2, 13, 4, 13, '=')   # ... and its trapdoor down into M1 (Rotting Descent)
r.fill(12, 11, 16, 12, '~').fill(25, 11, 28, 12, '~')   # rot sloughs
r.fill(18, 8, 23, 10).fill(18, 5, 21, 5, '=')       # a hummock
r.fill(8, 6, 11, 6, '=').fill(26, 6, 30, 6, '=')
r.fill(30, 8, 33, 10)                               # a second hummock, the nook under it
r.fill(31, 9, 33, 10, '.')
_rbput(r, [(32, 10, 'C'), (22, 7, 'b'), (10, 1, 'l'), (24, 1, 'l'), (39, 8, 'k'), (15, 1, 'r'), (29, 1, 'x'), (34, 10, 'S')])
r.kw['spawns'] = [
    *_rbgate(r, 5, 10, 7),
    *[_rbD('m_reeds', x, y, v=i % 2, fg=1, tall=1) for i, (x, y) in enumerate([(9, 10), (13, 10), (17, 10), (21, 7), (25, 10), (29, 10)])],
    _rbD('m_mush', 19, 7), _rbD('m_mush', 38, 8), _rbD('m_lantpost', 36, 8), _rbD('m_stakes', 6, 10),
    *[_rbD('m_moss', x, 1) for x in (7, 19, 27, 33)], _rbD('m_fog', 5, 7, w=31, h=5),
    dict(t='xrb_ambush', type='rot_crawler', x=14, y=10, r=46, hide=1), dict(t='xrb_ambush', type='bog_spitter', x=24, y=10, r=50, hide=1),
    dict(t='xrb_ambush', type='rot_hulk', x=10, y=10, r=56, hide=1), dict(t='xrb_ambush', type='rot_crawler', x=31, y=7, r=44, hide=1),
]

# ---------------------------------------------------------------- M12 The Valve House (puzzle)
# The water starts high: it floats you from the high door out to the shard on the pillar. Each valve (one on the high
# shelf, one on the basin floor) flips it: low water opens the tunnel gate to the low door, high water is the only way
# back up to the shelf (it overhangs the basin, so no wall-jumping onto it).
r = Room('M12', 'The Valve House', 'mire', *_rbM(192, 153), 36, 24, indoor=True, x3=True, puzzle=True, needs=['talon'],
         chests=['shard'])
r.walls()
r.fill(0, 0, 35, 1)                                 # roof
r.open('W', 2, 5)                                   # high door (Rotwood Bridges)
r.fill(0, 6, 9, 7)                                  # the high shelf, overhanging the basin
r.fill(0, 8, 1, 17)
r.fill(0, 18, 8, 18)                                # tunnel roof
r.open('W', 19, 22)                                 # low door (Reed Maze)
r.fill(24, 9, 24, 22)                               # the pillar's stem ...
r.fill(22, 7, 26, 8)                                # ... and its cap (the shard waits on it)
for x0, x1, y in [(29, 33, 20), (27, 30, 17), (29, 33, 14), (27, 30, 11), (27, 29, 9)]:
    r.fill(x0, y, x1, y, '=')                       # pump gantries up the east wall
_rbput(r, [(24, 6, 'C'), (5, 2, 'l'), (18, 2, 'l'), (31, 2, 'l'), (34, 22, 'k'), (15, 22, 'b')])
r.kw['spawns'] = [
    _rbK('level', 10, 7, w=25, h=16, id='lvl', states=[7, 23, 7], fluid='water', speed=3),
    _rbK('level', 2, 8, w=8, h=15, id='lvl2', states=[7, 23, 7], fluid='water', speed=3),
    _rbK('lever', 4, 5, id='vHigh', targets=['lvl', 'lvl2', 'gT']),
    _rbK('lever', 11, 22, id='vLow', targets=['lvl', 'lvl2', 'gT']),
    _rbK('gate', 6, 22, id='gT'),
    _rbD('m_pump', 20, 22, layer='back'), _rbD('m_valve', 4, 5), _rbD('m_valve', 11, 22),
    _rbD('m_pipes', 12, 3, w=22, layer='back'), _rbD('m_gauge', 32, 13),
    _rbD('m_mush', 2, 5), _rbD('m_moss', 12, 2), _rbD('m_moss', 28, 2), _rbD('m_sign', 9, 5, v=2),
    _rbS('lore', 7, 5, page='rb_3', look='tablet'),
]


# ======================================================================================================== ASHEN ARCHIVES
# zone (§8.1) x 250..371, y -260..-131 above the shifted Archives; the Grand Stacks reaches down to the Archives' roof
# (A4/A5 tops at y -112; the rows between are nobody's zone) so the wing is entered and left by real openings:
#   A11 Page Storm (252,-226) 56x16          A14 Reading Nook (308,-226) 24x14
#   A10 Ladder Well (252,-210) 24x50         A9 Copy Room (276,-210) 48x14      A16 Forbidden Annex (324,-212) 16x14
#                                            A15 Hookline Trial (276,-196) 48x32 A12 Index Room (324,-168) 32x20
#   A8 Grand Stacks (252,-160) 64x48                                             A13 Cipher Wall (316,-148) 40x18
#   ... sitting on A4 (x 252..275) and A5 (x 276..323).
# A5 (Chained Stacks, by the Inkwell Shrine): a hole in its roof and two ledges up to it -> the Grand Stacks' floor
_rb = ROOM('A5')
_rb.open('N', 31, 33).fill(31, 1, 33, 1, '.').fill(28, 9, 31, 9, '=').fill(26, 5, 30, 5, '=').fill(31, 2, 33, 2, '=').put(30, 2, '.').put(19, 2, 'l')
# A4 (Spiral of Shelves): the Grand Stacks' west trapdoor drops in here (the loop-back)
_rb = ROOM('A4')
_rb.open('N', 2, 4).put(4, 1, '.').put(7, 1, 'l')


def _rbmirror(r, area_w=None):
    """flip a finished room left-right (map + spawns). area spawns keep their extent: x' = w - x - width."""
    W = r.w
    r.g = [row[::-1] for row in r.g]
    for s in r.kw.get('spawns', []):
        wid = None
        if s.get('t') == 'xrb_books': wid = s['cols']
        elif s.get('t') == 'xrb' and s.get('d') in ('a_shelf',): wid = s.get('w', 2)
        elif s.get('t') == 'xrb' and 'w' in s and s.get('d') not in ('a_stack',): wid = s['w']
        s['x'] = W - s['x'] - wid if wid else W - 1 - s['x']
        if 'ox' in s: s['ox'] = -s['ox']
    return r


# the scribe's cipher: four numbered leaves pinned around the Archives, each showing one rune (kit glyph sym)
RB_CIPHER = [5, 2, 7, 0]                    # leaf I..IV -> rune; the Cipher Wall's glyph ids are 'g<sym>'

# ---------------------------------------------------------------- A8 The Grand Stacks (grand)
# Three stacks of shelves under a hanging codex the size of a house, standing on the Archives' own roof. You climb in
# from the Chained Stacks (east trapdoor); the west trapdoor drops you into the Spiral of Shelves. Routes: the reading
# floor (low), the west galleries (a reading balcony), the east shelf-stair to the Cipher Wall's door and on up to the
# stack tops, the rolling ladder across them and the reading bridge to the Ladder Well.
r = Room('A8', 'The Grand Stacks', 'archives', 252, -160, 64, 48, indoor=True, x3=True, grand=True, needs=['talon'],
         shrine='Shrine of the Hanging Codex')
r.walls()
r.fill(0, 0, 63, 1)
r.fill(10, 0, 12, 1, '.').fill(9, 2, 13, 2, '=')    # up to the Ladder Well
r.fill(0, 45, 63, 47)
r.fill(55, 45, 57, 46, '.').fill(55, 47, 57, 47, '=')   # up from the Chained Stacks (A5)
r.fill(2, 45, 4, 46, '.').fill(2, 47, 4, 47, '=')   # down into the Spiral of Shelves (A4): the loop-back
r.fill(1, 31, 10, 32)                               # the west reading balcony
r.fill(14, 6, 16, 38)                               # stack A
r.fill(30, 14, 33, 40)                              # stack B (the codex hangs in front of it)
r.fill(46, 6, 49, 38)                               # stack C
r.fill(55, 33, 62, 34)                              # the east balcony
r.open('E', 23, 26)                                 # -> the Cipher Wall
for x0, x1, y in [(4, 8, 42), (10, 13, 39), (4, 8, 36), (11, 13, 33)]:
    r.fill(x0, y, x1, y, '=')                       # west galleries (floor -> the reading balcony)
for x0, x1, y in [(50, 54, 42), (56, 60, 39), (50, 54, 36), (50, 54, 30), (50, 54, 24), (56, 60, 21),
                  (50, 54, 18), (56, 60, 15), (50, 54, 12), (56, 60, 9)]:
    r.fill(x0, y, x1, y, '=')                       # the east shelf-stair
r.fill(55, 27, 62, 28)                              # the Cipher Wall's landing
r.fill(10, 4, 13, 4, '=')                           # from stack A's top to the Ladder Well
r.fill(17, 28, 29, 28, '=').fill(34, 22, 45, 22, '=').fill(17, 16, 22, 16, '=')
r.fill(24, 41, 29, 41, '=').fill(34, 36, 38, 36, '=')
_rbput(r, [(24, 7, '@'), (39, 5, '@'), (58, 4, '@'),
           (7, 2, 'l'), (27, 2, 'l'), (40, 2, 'l'), (54, 2, 'l'), (8, 44, 'k'), (60, 32, 'k'), (18, 44, 'I'), (40, 44, 'I'),
           (26, 44, 'E'), (8, 30, 'k'), (36, 44, 'j'), (60, 44, 'd'), (24, 27, 'q'), (40, 21, 'q'), (44, 44, 'S')])
r.kw['spawns'] = [
    _rbK('mover', 17, 7, w=3, path=[[17, 7], [43, 7]], speed=2.2, wait=0.8, solid=False),
    _rbK('mover', 34, 32, w=3, path=[[34, 32], [42, 32]], speed=1.6, wait=0.6),
    _rbK('mover', 17, 22, w=3, path=[[17, 22], [26, 22]], speed=1.6, wait=0.6),
    _rbD('a_codex', 31, 13, layer='back'),
    _rbD('a_rail', 17, 6, w=29), _rbD('a_rail', 34, 31, w=11), _rbD('a_rail', 17, 21, w=12),
    _rbD('a_stack', 14, 5, w=3, r0=6, r1=38), _rbD('a_stack', 46, 5, w=4, r0=6, r1=38), _rbD('a_stack', 30, 13, w=4, r0=14, r1=40),
    *[_rbD('a_shelf', x, 44, layer='back', h=hh) for x, hh in [(6, 9), (11, 7), (25, 6), (37, 8), (46, 5), (50, 7), (61, 9)]],
    *[_rbD('a_shelf', x, y, layer='back', h=hh) for x, y, hh in [(5, 30, 6), (20, 27, 8), (43, 21, 7), (61, 32, 8), (20, 15, 6)]],
    _rbD('a_books', 12, 44), _rbD('a_books', 33, 44), _rbD('a_books', 57, 32), _rbD('a_books', 3, 30),
    _rbD('a_candles', 16, 44), _rbD('a_candles', 58, 26), _rbD('a_note', 48, 43, n=3, sym=RB_CIPHER[2]),
    _rbD('a_pages', 25, 20, w=34, h=30), _rbD('a_chain', 27, 2, len=6), _rbD('a_chain', 35, 2, len=11),
    _rbE('ink_hound', 20, 44), _rbE('lantern_monk', 58, 32), _rbE('grimoire', 36, 12, air=True),
]

# ---------------------------------------------------------------- A10 Ladder Well (path)
# A shaft of ladders and shelves between floors: from the Grand Stacks' roof up past the Hookline's door (and its shrine)
# to the Copy Room and the Page Storm. (Its first 36 rows are the old well, 14 rows lower; the top 14 are new.)
_o = 14
r = Room('A10', 'Ladder Well', 'archives', 252, -210, 24, 50, indoor=True, x3=True, needs=['talon'], shrine='Ladderwell Shrine')
r.walls()
r.fill(6, 0, 8, 0, '.').fill(5, 2, 9, 2, '=')       # up into the Page Storm
r.open('E', 7, 10).fill(16, 11, 23, 11)             # the Copy Room's landing
for x0, x1, y in [(3, 7, 5), (8, 12, 8), (14, 18, 14)]:
    r.fill(x0, y, x1, y, '=')                       # the new upper well
r.fill(0, 33 + _o, 23, 35 + _o)                     # floor ...
r.fill(10, 33 + _o, 12, 34 + _o, '.').fill(10, 35 + _o, 12, 35 + _o, '=')   # ... and the trapdoor down to the Grand Stacks
r.fill(9, 2 + _o, 13, 2 + _o, '=')
r.open('E', 25 + _o, 28 + _o).fill(16, 29 + _o, 23, 30 + _o)   # the landing before the Hookline Trial
for x0, x1, y in [(3, 8, 30), (9, 14, 27), (3, 7, 24), (13, 18, 21), (4, 9, 18), (14, 19, 15), (5, 9, 12),
                  (14, 19, 9), (8, 12, 5)]:
    r.fill(x0, y + _o, x1, y + _o, '=')
r.fill(0, 20 + _o, 1, 22 + _o).fill(22, 11 + _o, 23, 13 + _o)   # shelf stubs on the walls
r.fill(15, 10 + _o, 21, 10 + _o)                    # the old high landing
_rbput(r, [(4, 1, 'l'), (19, 1, 'l'), (2, 32 + _o, 'k'), (21, 32 + _o, 'I'), (6, 32 + _o, 'E'), (6, 17 + _o, 'q'), (17, 20 + _o, 'd'),
           (22, 28 + _o, 'k'), (18, 28 + _o, 'S'), (20, 10, 'k')])
r.kw['spawns'] = [
    *[_rbD('a_shelf', x, y + _o, layer='back', h=hh) for x, y, hh in [(2, 32, 7), (21, 32, 6), (1, 19, 5), (22, 9, 8), (12, 26, 4)]],
    _rbD('a_shelf', 1, 12, layer='back', h=8), _rbD('a_shelf', 20, 10, layer='back', h=6),
    _rbD('a_note', 20, 26 + _o, n=2, sym=RB_CIPHER[1]), _rbD('a_books', 8, 32 + _o), _rbD('a_books', 16, 14 + _o),
    _rbD('a_candles', 10, 4 + _o), _rbD('a_candles', 17, 10),
    _rbD('a_pages', 2, 3, w=20, h=40), _rbD('a_chain', 6, 1, len=10), _rbD('a_chain', 17, 1, len=7),
]

# ---------------------------------------------------------------- A9 The Copy Room (path)
r = Room('A9', 'The Copy Room', 'archives', 276, -210, 48, 14, indoor=True, x3=True, needs=['talon'])
r.walls()
r.fill(0, 0, 47, 1)
r.fill(0, 11, 47, 13)
r.open('W', 7, 10)                                  # from the Ladder Well
r.fill(45, 11, 46, 12, '.').fill(45, 13, 46, 13, '=')   # the Hookline's climb comes up through the floor here
r.fill(13, 7, 17, 7, '=').fill(24, 7, 28, 7, '=').fill(38, 7, 46, 7, '=')   # the copy galleries
r.fill(47, 4, 47, 6, '.').fill(46, 4, 46, 6, 'B')   # a false bookcase just inside the east wall (the Forbidden Annex)
_rbput(r, [(9, 2, 'l'), (22, 2, 'l'), (34, 2, 'l'), (11, 10, 'I'), (36, 10, 'I'), (26, 6, 'k'), (15, 6, 'k'), (40, 6, 'k')])
r.kw['spawns'] = [
    *[_rbD('a_desk', x, 10) for x in (8, 14, 20, 26, 32, 40)],
    *[dict(t='xrb_ambush', type='lantern_monk', x=x, y=10, r=54, rise='ink') for x in (14, 26)],
    dict(t='xrb_ambush', type='ink_hound', x=38, y=10, r=70, rise='ink'),
    *[_rbD('a_shelf', x, 10, layer='back', h=hh) for x, hh in [(5, 7), (22, 5), (30, 7), (43, 3)]],
    _rbD('a_note', 23, 9, n=1, sym=RB_CIPHER[0]), _rbD('a_books', 34, 10), _rbD('a_pages', 4, 3, w=40, h=7),
    _rbD('a_falseshelf', 45, 6, ox=16),
    _rbE('grimoire', 20, 4, air=True),
]

# ---------------------------------------------------------------- A13 The Cipher Wall (puzzle)
# (laid out as first built, then mirrored: its door faces the Grand Stacks' east landing)
r = Room('A13', 'The Cipher Wall', 'archives', 316, -148, 40, 18, indoor=True, x3=True, puzzle=True, needs=['talon'],
         chests=['emberstone'])
r.walls()
r.fill(0, 0, 39, 1)
r.fill(0, 15, 39, 17)
r.open('E', 11, 14).fill(36, 15, 39, 15)
r.fill(3, 0, 5, 1, '.').fill(2, 3, 6, 3, '=')       # up to the Index Room
r.fill(8, 2, 8, 10)                                 # the sealed stair's wall ...
r.fill(1, 12, 3, 12, '=').fill(4, 9, 7, 9, '=').fill(1, 6, 3, 6, '=')
_rbput(r, [(2, 14, 'C'), (14, 2, 'l'), (32, 2, 'l'), (11, 14, 'k'), (35, 14, 'k'), (22, 14, 'E')])
r.kw['spawns'] = [
    _rbK('gate', 8, 14, id='gc', persist=True),
    *[_rbK('glyph', 11 + 3 * i, 11 + (i % 2), id=f'g{i}', group='cipher', sym=i, note=[0, 2, 4, 5, 7, 9, 3, 6][i]) for i in range(8)],
    _rbK('seq', 20, 12, id='cipher', group='cipher', order=[f'g{s}' for s in RB_CIPHER], targets=['gc'],
         msg='The runes answer. Stone grinds aside.'),
    _rbS('lore', 22, 14, page='rb_5', look='none'),
    dict(t='xrb_hint', x=20, y=12, seq='cipher', text='The scribe numbered his leaves I to IV and pinned them where he worked. Strike the runes in that order.'),
    _rbD('a_mural', 23, 5, layer='back'),
    *[_rbD('a_shelf', x, 14, layer='back', h=hh) for x, hh in [(12, 5), (33, 7), (28, 4)]],
    _rbD('a_books', 30, 14), _rbD('a_candles', 25, 14), _rbD('a_pages', 10, 3, w=26, h=10),
]
_rbmirror(r)

# ---------------------------------------------------------------- A12 The Index Room (puzzle, above the Cipher Wall; mirrored too)
r = Room('A12', 'The Index Room', 'archives', 324, -168, 32, 20, indoor=True, x3=True, puzzle=True, needs=['talon'],
         chests=['shard'])
r.walls()
r.fill(0, 0, 31, 1)
r.fill(0, 17, 31, 18).fill(3, 19, 5, 19, '=')
r.fill(3, 17, 5, 18, '.')
r.fill(1, 14, 7, 14, '=')
r.fill(24, 9, 30, 16)                               # the hidden shelf's case ...
r.fill(24, 12, 29, 15, '.')                         # ... with its alcove (opened by the index)
r.fill(12, 12, 21, 12, '=')                         # the reading step in front of the book wall
_rbput(r, [(27, 15, 'C'), (6, 2, 'l'), (18, 2, 'l'), (10, 16, 'E'), (2, 16, 'k'), (22, 16, 'I')])
r.kw['spawns'] = [
    _rbK('gate', 24, 15, id='gi', persist=True, msg=None),
    dict(t='xrb_books', x=12, y=10, cols=8, rows=2, ys=[11, 16], gate='gi', answer=[3, 9, 14], id='index'),
    _rbD('a_card', 10, 16, nums=[3, 9, 14]),
    _rbS('lore', 10, 16, page='rb_6', look='none'),
    dict(t='xrb_hint', x=12, y=10, books='index', text='The card on the lectern names three books. Pull only those; the rest must stay shelved.'),
    _rbD('a_shelf', 3, 13, layer='back', h=6), _rbD('a_shelf', 22, 16, layer='back', h=4), _rbD('a_books', 15, 16),
    _rbD('a_candles', 20, 11), _rbD('a_note', 7, 12, n=4, sym=RB_CIPHER[3]), _rbD('a_pages', 8, 3, w=16, h=12),
]
_rbmirror(r)

# ---------------------------------------------------------------- A11 Page Storm (parkour)
# Gusts from the broken stacks below lift loose pages into platforms for a heartbeat. Under them: ink.
r = Room('A11', 'Page Storm', 'archives', 252, -226, 56, 16, indoor=True, x3=True, parkour=True, needs=['talon'])
r.walls()
r.fill(0, 0, 55, 0)
r.fill(0, 11, 10, 15)                               # west ledge (up from the Ladder Well)
r.fill(6, 11, 8, 14, '.').fill(6, 15, 8, 15, '=')
r.fill(3, 8, 5, 8, '=')
r.fill(11, 13, 45, 14, '9').fill(11, 15, 45, 15)    # the ink below
r.fill(21, 9, 23, 15).fill(33, 7, 35, 15)           # broken stacks standing out of the ink
r.fill(46, 10, 55, 15)                              # east ledge
r.open('E', 6, 9)                                   # -> Reading Nook
_rbput(r, [(5, 1, 'l'), (28, 1, 'l'), (50, 1, 'l'), (52, 9, 'k'), (2, 10, 'k')])
_ph = lambda x, y, w, per, a, b, off=0: _rbK('phase', x, y, w=w, period=per, on=[a, b], offset=off)
r.kw['spawns'] = [
    _ph(12, 10, 2, 2.4, 0.0, 0.55), _ph(16, 9, 2, 2.4, 0.3, 0.85), _ph(25, 8, 2, 2.0, 0.0, 0.5), _ph(29, 7, 2, 2.0, 0.35, 0.85),
    _ph(37, 7, 2, 2.2, 0.0, 0.55), _ph(41, 8, 2, 2.2, 0.35, 0.9),
    _rbK('wind', 12, 3, w=10, h=8, vy=-60, vx=30, period=2.4, on=[0.0, 0.5]),
    _rbK('wind', 25, 2, w=7, h=8, vy=-60, vx=30, period=2.0, on=[0.0, 0.5]),
    _rbK('wind', 37, 2, w=8, h=8, vy=-60, vx=30, period=2.2, on=[0.0, 0.55]),
    _rbD('a_books', 51, 9),
    _rbD('a_pages', 11, 1, w=35, h=12, k=3), _rbD('a_shelf', 2, 10, layer='back', h=5), _rbD('a_shelf', 53, 9, layer='back', h=5),
    _rbD('a_stack', 21, 8, w=3, r0=9, r1=12, broken=1), _rbD('a_stack', 33, 6, w=3, r0=7, r1=12, broken=1),
    _rbE('grimoire', 28, 3, air=True),
]

# ---------------------------------------------------------------- A14 The Reading Nook (vista)
r = Room('A14', 'The Reading Nook', 'archives', 308, -226, 24, 14, indoor=True, x3=True, vista=True, needs=['talon'])
r.walls()
r.fill(0, 0, 23, 0)
r.fill(0, 10, 23, 13)
r.open('W', 6, 9)
r.fill(13, 9, 21, 9)                                # the window seat
_rbput(r, [(3, 9, 'k'), (8, 9, 'I'), (22, 8, 'k')])
r.kw['spawns'] = [
    _rbD('a_window', 17, 8, layer='back'), _rbD('a_backdrop', 1, 1, w=24, h=14, scene='archives'),
    _rbS('bench', 16, 8, id='bench', view=[17, 5], lore='rb_4', zoom=0.9),
    _rbS('lore', 6, 9, page='rb_7', look='book'),
    _rbD('a_shelf', 2, 9, layer='back', h=6), _rbD('a_books', 11, 9), _rbD('a_candles', 13, 8), _rbD('a_candles', 20, 8),
    _rbD('a_rain', 13, 1, w=9, h=8),
]

# ---------------------------------------------------------------- A16 The Forbidden Annex (secret, Root Hook)
r = Room('A16', 'The Forbidden Annex', 'archives', 324, -212, 16, 14, indoor=True, x3=True, secret=True,
         needs=['talon', 'hook'], items=['emberstone'])
r.walls()
r.fill(0, 0, 15, 1)
r.open('W', 6, 8).fill(0, 9, 3, 13)                 # behind the Copy Room's false bookcase
r.fill(4, 11, 11, 12, '9').fill(4, 13, 11, 13)      # an ink well across the floor
r.fill(12, 9, 15, 13)                               # the far ledge
_rbput(r, [(7, 3, '@'), (14, 8, 'i'), (2, 8, 'k'), (10, 2, 'l')])
r.kw['spawns'] = [
    _rbS('lore', 13, 8, page='rb_8', look='corpse', face=-1),
    _rbD('a_shelf', 1, 8, layer='back', h=5), _rbD('a_candles', 12, 8), _rbD('a_chain', 4, 2, len=4),
    _rbD('a_pages', 4, 3, w=8, h=7),
]

# ---------------------------------------------------------------- A15 Hookline Trial (trial, Root Hook)
# Hook to hook over the ink abyss. Hanging stacks force you under and over; blades sweep the middle. Past the last ring,
# the goal waits at the foot of a narrow chimney: wall-jump up it into the Copy Room (the only way on).
r = Room('A15', 'Hookline Trial', 'archives', 276, -196, 48, 32, indoor=True, x3=True, trial=True, needs=['talon', 'hook'])
r.walls()
r.fill(0, 0, 47, 1)
r.open('W', 25, 28).fill(0, 29, 5, 31)              # start ledge
r.fill(6, 29, 46, 30, '9')                          # the ink abyss
r.fill(12, 2, 14, 15)                               # hanging stack 1
r.fill(26, 2, 28, 10)                               # hanging stack 2
r.fill(29, 25, 30, 28)                              # a stub of shelving standing in the ink
r.fill(37, 21, 39, 28)                              # standing stack 3
r.fill(43, 19, 47, 20)                              # the goal ledge, past the last ring
r.fill(44, 2, 44, 16).fill(45, 0, 46, 1, '.')       # the chimney up to the Copy Room
_rbput(r, [(9, 18, '@'), (17, 18, '@'), (22, 13, '@'), (31, 15, '@'), (37, 12, '@'),
           (3, 2, 'l'), (20, 2, 'l'), (33, 2, 'l'), (2, 28, 'k')])
r.kw['spawns'] = [
    _rbS('trial', 3, 28, id='hookline', par=5.2, reward='c_x3_ink', region='Ashen Archives', name='The Hookline'),
    _rbS('trial_goal', 46, 18, trial='hookline'),
    _rbK('pendulum', 20, 2, len=7, period=2.4, amp=40, phase=0.0),
    _rbK('pendulum', 33, 2, len=6, period=2.0, amp=45, phase=0.5),
    _rbD('a_stack', 12, 16, w=3, r0=2, r1=15), _rbD('a_stack', 26, 11, w=3, r0=2, r1=10),
    _rbD('a_stack', 29, 24, w=2, r0=25, r1=28), _rbD('a_stack', 37, 20, w=3, r0=21, r1=28),
    _rbD('a_pages', 6, 4, w=37, h=22), _rbD('a_shelf', 1, 28, layer='back', h=4),
]


# ---------------------------------------------------------------- W5 The Ink Stair (K3 -> A1): dressed, not moved
def _rbW5():
    r = ROOM('W5')
    r.kw['spawns'] = r.kw.get('spawns', []) + [
        _rbD('a_pages', 1, 2, w=r.w - 2, h=r.h - 4, k=0.6),
        *[_rbD('a_chain', x, 1, len=8 + (i * 5) % 14) for i, x in enumerate((1, r.w - 2))],
        *[_rbD('a_shelf', 1 if i % 2 else r.w - 3, y, layer='back', h=5) for i, y in enumerate(range(12, r.h - 4, 14))],
    ]
POST_LINKS.append(_rbW5)


# ======================================================================================================== HOARFROST AQUEDUCT
# zone (§8.1) x 150..249, y -200..-39, above HF5-HF7. The wing is the first layout moved down 8 rows; its foot, the Rime
# Stair, climbs out of the Frozen Aqueduct's open sky (HF6) into the Conduit.
#   HF15 Rimebreaker Trial (150,-152) 56x22    HF14 Frostbitten Overlook (206,-152) 44x22 (open sky)
#   HF11 The Long Slide (170,-130) 80x16
#   HF12 Icicle Gallery (154,-114) 48x18       HF8 The Frozen Falls (202,-114) 48x56
#   HF9 Pump Station (154,-96) 48x16
#   HF13 Brazier Locks (162,-80) 40x22
#   HF10 Frozen Conduit (154,-58) 56x14
#   HF16 The Rime Stair (166,-44) 8x10  -> its open foot hangs over HF6's sky
def _rbH(x, y): return x, y + 8

# HF6 (the Frozen Aqueduct, open sky): ice ledges up its west end to the Rime Stair; the stair's two posts rest on HF6's
# top edge (the only cells of its sky that change).
_rb = ROOM('HF6')
_rb.fill(10, 11, 12, 11, '=').fill(3, 6, 6, 6, '=').fill(6, 3, 8, 3, '=').fill(3, 0, 8, 0, '=').put(2, 0, '#').put(9, 0, '#')

# ---------------------------------------------------------------- HF16 The Rime Stair (a short climb out of HF6's sky)
r = Room('HF16', 'The Rime Stair', 'hoarfrost', 166, -44, 8, 10, indoor=True, x3=True, needs=['talon', 'hook'])
r.fill(0, 0, 0, 9).fill(7, 0, 7, 9).fill(0, 0, 7, 0).fill(1, 0, 1, 0).fill(6, 0, 6, 0)
r.fill(2, 0, 5, 0, '.')                             # up into the Conduit
r.fill(1, 7, 3, 7, '=').fill(4, 4, 6, 4, '=').fill(2, 1, 5, 1, '=')
r.kw['spawns'] = [_rbD('f_snow', 1, 1, w=6, h=8, k=0.5), _rbD('f_frostpipe', 1, 1, w=6, h=8, v=1)]

# ---------------------------------------------------------------- HF10 Frozen Conduit (path)
r = Room('HF10', 'Frozen Conduit', 'hoarfrost', *_rbH(154, -66), 56, 14, indoor=True, x3=True, needs=['talon', 'hook'],
         shrine='Shrine of the Frozen Main')
r.walls()
r.fill(0, 0, 55, 3).fill(0, 10, 55, 13)             # the pipe's shell (inside: rows 4..9)
r.fill(12, 10, 21, 10, '_').fill(42, 10, 48, 10, '_')   # glazed floor
r.fill(33, 10, 40, 11, ':').fill(33, 12, 40, 12)    # a frozen sump
r.fill(52, 0, 54, 3, '.')                           # riser up into the Frozen Falls
r.fill(52, 7, 54, 7, '=').fill(52, 4, 54, 4, '=').fill(52, 2, 54, 2, '=')
r.fill(26, 0, 28, 3, '.')                           # riser up into the Brazier Locks
r.fill(26, 7, 28, 7, '=').fill(26, 4, 28, 4, '=').fill(26, 2, 28, 2, '=')
r.fill(8, 4, 9, 4).fill(40, 4, 41, 4)               # pipe collars
r.fill(14, 10, 17, 12, '.').fill(14, 13, 17, 13, '=')   # down the Rime Stair to HF6
_rbput(r, [(14, 4, ','), (18, 4, ','), (35, 4, ','), (43, 4, ','), (47, 4, ','), (2, 9, 'k'), (50, 9, 'b'), (11, 9, 'b'), (5, 9, 'S')])
r.kw['spawns'] = [
    _rbE('hf_wraith', 20, 6), _rbE('hf_golem', 45, 9), _rbE('hf_lurker', 36, 9, air=True),
    *[_rbD('f_rib', x, 5) for x in (6, 15, 24, 34, 45)], _rbD('f_frostpipe', 1, 4, w=54, h=6),
    _rbD('f_valve', 49, 9), _rbD('f_crystal', 23, 9), _rbD('f_crystal', 50, 9), _rbD('f_drift', 13, 9), _rbD('f_drift', 30, 9),
]

# ---------------------------------------------------------------- HF8 The Frozen Falls (grand)
# Up the frozen waterfall on its ice ledges (icicles, sliding ice), or up the west cliff's old stair (a cave behind it),
# or ring to ring up the east wall with the Root Hook. The great aqueduct arch crowns the falls.
r = Room('HF8', 'The Frozen Falls', 'hoarfrost', *_rbH(202, -122), 48, 56, indoor=True, x3=True, grand=True,
         needs=['talon', 'hook'], chests=['shard'])
r.walls()
r.fill(0, 0, 47, 1)
r.fill(42, 0, 44, 1, '.').fill(41, 2, 45, 2, '=')   # up to the Long Slide
r.fill(30, 5, 47, 6)                                # the top landing (under the arch)
r.fill(0, 53, 47, 55)
r.fill(4, 53, 6, 54, '.').fill(4, 55, 6, 55, '=')   # down to the Frozen Conduit
r.fill(15, 53, 33, 54, ':')                         # the plunge pool
# the waterfall's ice ledges
for i, y in enumerate([50, 47, 44, 41, 38, 35, 32, 29, 26, 23, 20, 17, 14, 11]):
    if y in (38, 26): continue                      # sliding ice there (movers)
    x0 = 13 if i % 2 == 0 else 26
    r.fill(x0, y, x0 + 5, y, '_')
r.fill(21, 8, 27, 8, '_')
# west cliff: the old stair and the cave behind the falls
r.fill(0, 27, 6, 35)
r.fill(1, 29, 5, 32, '.').fill(6, 29, 6, 32, 'B')   # the frost-sealed cave
for y, x0 in [(50, 1), (47, 5), (44, 1), (41, 5), (26, 5), (23, 1), (20, 5), (17, 1), (14, 5), (11, 1)]:
    r.fill(x0, y, x0 + 3, y, '=')
r.fill(8, 38, 11, 38, '=').fill(7, 35, 10, 35, '=').fill(8, 32, 11, 32, '=').fill(7, 29, 10, 29, '=')   # up past the cave's rock
r.open('W', 22, 25).fill(0, 26, 8, 26, '=')         # from the Pump Station, onto the old stair
r.fill(6, 8, 12, 8).fill(1, 8, 5, 8, '=')          # the west top ledge (its west end thin boards: the stair comes up through)
r.fill(13, 8, 20, 8, '=')                           # ... and the rime bridge to the falls' crown
# east: perches and rings (Root Hook)
for y in (49, 41, 33, 25, 17, 10):
    r.fill(41, y, 46, y, '=')
_rbput(r, [(38, 45, '@'), (44, 37, '@'), (38, 29, '@'), (44, 21, '@'), (38, 14, '@'),
           (2, 32, 'C'), (15, 51, ','), (28, 48, ','), (16, 42, ','), (29, 36, ','), (16, 30, ','), (29, 24, ','), (17, 18, ','),
           (3, 51, ','), (6, 39, ','), (43, 50, ','), (43, 34, ','),
           (8, 2, ','), (20, 2, ','), (34, 2, ','), (36, 4, 'k'), (46, 4, 'k'), (2, 52, 'k'), (45, 52, 'b'), (3, 7, 'b')])
r.kw['spawns'] = [
    _rbK('mover', 15, 38, w=3, path=[[13, 38], [26, 38]], speed=1.5, wait=0.7),
    _rbK('mover', 25, 26, w=3, path=[[26, 26], [13, 26]], speed=1.6, wait=0.6),
    _rbD('f_bigfall', 23, 52, top=2, layer='back'), _rbD('f_arch', 38, 4, layer='back'), _rbD('f_statue', 12, 7, layer='back'),
    *[_rbD('f_crystal', x, y) for x, y in [(2, 49), (44, 48), (8, 7), (32, 4), (44, 24), (12, 52), (35, 52)]],
    *[_rbD('f_drift', x, y) for x, y in [(9, 52), (38, 52), (35, 4), (5, 7)]],
    _rbD('f_mist', 19, 45, w=16, h=8), _rbD('f_snow', 1, 2, w=46, h=50),
    _rbE('hf_wraith', 10, 22), _rbE('hf_wraith', 36, 40), _rbE('hf_golem', 40, 52), _rbE('hf_wraith', 22, 12),
]

# ---------------------------------------------------------------- HF11 The Long Slide (parkour)
# West along the aqueduct's glazed channel: build speed on the ice and clear the breaks. Low arches keep the jumps flat.
r = Room('HF11', 'The Long Slide', 'hoarfrost', *_rbH(170, -138), 80, 16, indoor=True, x3=True, parkour=True,
         needs=['talon', 'hook'], shrine='Shrine of the Long Channel')
r.walls()
r.fill(0, 0, 79, 1)
r.fill(0, 12, 79, 15).fill(0, 12, 79, 12, '_')      # the glazed channel
r.fill(74, 12, 76, 14, '.').fill(74, 15, 76, 15, '=')   # up from the Frozen Falls
r.fill(2, 12, 4, 14, '.').fill(2, 15, 4, 15, '=')   # down to the Icicle Gallery
for x0, x1 in [(60, 64), (48, 53), (36, 40), (24, 29), (12, 16)]:
    r.fill(x0, 12, x1, 13, '.').fill(x0, 14, x1, 14, '^')   # breaks in the channel (ice shards below)
for x0, x1 in [(54, 58), (42, 46), (30, 34)]:
    r.fill(x0, 2, x1, 7)                            # low arches
r.fill(70, 0, 72, 1, '.')                           # up to the Overlook
for x0, x1, y in [(69, 72, 10), (65, 68, 7), (69, 72, 4), (69, 73, 2)]:
    r.fill(x0, y, x1, y, '=')
r.fill(10, 0, 12, 1, '.')                           # up to the Rimebreaker Trial
for x0, x1, y in [(6, 9, 10), (10, 13, 7), (6, 9, 4), (9, 13, 2)]:
    r.fill(x0, y, x1, y, '=')
_rbput(r, [(56, 8, ','), (44, 8, ','), (32, 8, ','), (19, 2, ','), (66, 2, ','), (78, 11, 'k'), (1, 11, 'k'), (20, 11, 'b'), (77, 11, 'S')])
r.kw['spawns'] = [
    *[_rbD('f_arch2', x, 11, layer='back') for x in (56, 44, 32)], _rbD('f_snow', 1, 2, w=78, h=10),
    *[_rbD('f_crystal', x, 11) for x in (68, 45, 21, 7)], _rbD('f_drift', 58, 11), _rbD('f_drift', 34, 11),
    _rbD('f_sign', 77, 11), _rbE('hf_wraith', 38, 5), _rbE('hf_wraith', 18, 6),
]

# ---------------------------------------------------------------- HF14 Frostbitten Overlook (vista, open sky)
# The Rimebreaker's goal ledge steps out over its west end (a one-way drop onto the crag).
r = Room('HF14', 'Frostbitten Overlook', 'hoarfrost', 206, -152, 44, 22, x3=True, vista=True, needs=['talon', 'hook'])
r.walls(top=False).open('W', 2, 5)
_X, _Y = 8, 4                                       # the first layout sat 8 columns east and 4 rows lower
r.fill(0, 15 + _Y, 43, 17 + _Y)
r.fill(26 + _X, 15 + _Y, 28 + _X, 16 + _Y, '.').fill(26 + _X, 17 + _Y, 28 + _X, 17 + _Y, '=')   # down to the Long Slide
r.fill(0, 11 + _Y, 8 + _X, 14 + _Y).fill(9 + _X, 13 + _Y, 12 + _X, 14 + _Y)            # the crag the bench looks out from
_rbput(r, [(3 + _X, 10 + _Y, 'k'), (33 + _X, 14 + _Y, 'k')])
r.kw['spawns'] = [
    _rbD('f_aurora', 1, 1, w=44, h=22), _rbD('f_reservoir', 14 + _X, 13 + _Y, w=36),
    _rbS('bench', 6 + _X, 10 + _Y, id='bench', view=[22 + _X, 4 + _Y], lore='rb_9'),
    _rbS('lore', 31 + _X, 14 + _Y, page='rb_10', look='stone'),
    _rbD('f_crystal', 1 + _X, 10 + _Y), _rbD('f_crystal', 12 + _X, 12 + _Y), _rbD('f_drift', 16 + _X, 14 + _Y), _rbD('f_drift', 23 + _X, 14 + _Y),
    _rbD('f_crystal', 3, 10 + _Y), _rbD('f_drift', 5, 10 + _Y),
    _rbD('f_railing', 13 + _X, 14 + _Y, w=12), _rbD('f_snow', 1, 1, w=42, h=18, k=0.6),
]

# ---------------------------------------------------------------- HF15 Rimebreaker Trial (trial, Ember Dash)
# Ember-dash through the ash veils in mid-air: low and west, up the frost wall, then high and east under the icicles.
r = Room('HF15', 'Rimebreaker Trial', 'hoarfrost', *_rbH(150, -160), 56, 22, indoor=True, x3=True, trial=True,
         needs=['talon', 'hook', 'emberdash'])
r.walls()
r.fill(0, 0, 55, 1)
r.fill(1, 20, 54, 20, '^')                          # ice shards the whole way
r.fill(26, 19, 36, 21)                              # the start ledge
r.fill(30, 19, 32, 20, '.').fill(30, 21, 32, 21, '=')   # (up from the Long Slide)
r.fill(21, 17, 23, 17, '_').fill(14, 17, 16, 17, '_').fill(6, 16, 9, 16, '_')   # low leg
r.fill(12, 2, 12, 19, '%').fill(12, 10, 12, 12, '^')   # veils split by a band of ice shards, so no one climbs them
r.fill(19, 2, 19, 19, '%').fill(19, 9, 19, 12, '^')
for x0, x1, y in [(2, 4, 13), (7, 9, 10)]:
    r.fill(x0, y, x1, y, '_')                       # the frost wall
r.fill(14, 7, 16, 7, '_').fill(21, 6, 24, 6, '_')   # high leg
r.fill(26, 6, 36, 6, '=')                           # the icicle bridge
r.fill(38, 2, 38, 12, '%')
r.fill(40, 6, 43, 6, '_')
r.fill(45, 2, 45, 9, '%').fill(45, 10, 45, 19, '^') # the last veil, over a column of ice shards
r.fill(47, 6, 54, 7)                                # the goal ledge ...
r.open('E', 2, 5)                                   # ... and out over the Overlook
_rbput(r, [(27, 2, ','), (30, 2, ','), (33, 2, ','), (36, 2, ','), (15, 2, ','), (7, 2, ','), (41, 2, ','), (2, 2, ','),
           (27, 18, 'k'), (35, 18, 'k'), (53, 5, 'k')])
r.kw['spawns'] = [
    _rbS('trial', 28, 18, id='rimebreaker', par=9.4, reward='c_x3_rime', region='Hoarfrost Aqueduct', name='The Rimebreaker'),
    _rbS('trial_goal', 50, 5, trial='rimebreaker'),
    _rbD('f_snow', 1, 2, w=54, h=17), *[_rbD('f_crystal', x, y) for x, y in [(34, 18), (48, 5)]],
]

# ---------------------------------------------------------------- HF12 Icicle Gallery (parkour)
# The icicles drop as you pass under; the ones that land in the frozen channel freeze into footholds for a while.
r = Room('HF12', 'Icicle Gallery', 'hoarfrost', *_rbH(154, -122), 48, 18, indoor=True, x3=True, parkour=True,
         needs=['talon', 'hook'], items=['emberstone'])
r.walls()
r.fill(0, 0, 47, 1)
r.fill(18, 0, 20, 1, '.').fill(17, 2, 21, 2, '=')   # down from the Long Slide
r.fill(0, 15, 47, 17)
r.fill(40, 15, 42, 16, '.').fill(40, 17, 42, 17, '=')   # down to the Pump Station
r.fill(23, 15, 35, 16, ':')                         # the frozen channel
r.fill(15, 7, 16, 13).fill(1, 6, 5, 6)              # a pillar; the high niche on the west wall
r.fill(20, 11, 22, 14).fill(36, 11, 38, 14)         # channel banks
r.fill(26, 8, 32, 8, '=')                           # the old gallery walk
r.fill(22, 2, 38, 4).fill(6, 2, 14, 2)             # the vault hangs low over the channel and the west hall
r.fill(8, 10, 11, 10, '_')
_rbput(r, [(3, 5, 'i'), (2, 14, 'k'), (45, 14, 'k'), (13, 14, 'b'), (9, 3, ','), (44, 2, ',')])
r.kw['spawns'] = [
    *[dict(t='xrb_icicle', x=x, y=5, foot=1) for x in (24, 26, 28, 30, 32, 34)],
    *[dict(t='xrb_icicle', x=x, y=3) for x in (7, 11)], dict(t='xrb_icicle', x=39, y=2),
    *[_rbD('f_rib', x, 5) for x in (18, 43)], _rbD('f_snow', 1, 2, w=46, h=12), _rbD('f_mist', 23, 12, w=13, h=3),
    _rbD('f_crystal', 37, 10), _rbD('f_crystal', 17, 14), _rbD('f_drift', 6, 14), _rbD('f_drift', 44, 14),
    _rbE('hf_wraith', 30, 5),
]

# ---------------------------------------------------------------- HF9 Pump Station (path) -> east into the Frozen Falls
r = Room('HF9', 'Pump Station', 'hoarfrost', *_rbH(154, -104), 48, 16, indoor=True, x3=True, needs=['talon', 'hook'])
r.walls()
r.fill(0, 0, 47, 1)
r.fill(40, 0, 42, 1, '.').fill(39, 2, 43, 2, '=')   # down from the Icicle Gallery
r.fill(35, 5, 39, 5, '=').fill(40, 8, 47, 8, '=')
r.open('E', 4, 7)                                   # the pumps' catwalk runs on into the Falls
r.fill(0, 13, 47, 15)
r.fill(9, 13, 18, 13, '_').fill(26, 13, 36, 13, '_')    # glazed floors
r.fill(20, 13, 22, 14, '.').fill(20, 15, 22, 15, '=')   # down to the Brazier Locks
r.fill(12, 8, 18, 8, '=').fill(25, 8, 31, 8, '=')   # pump gantries
_rbput(r, [(10, 2, 'x'), (28, 2, 'x'), (46, 12, 'k'), (8, 12, 'b'), (33, 7, 'k'), (24, 2, ','), (35, 2, ',')])
r.kw['spawns'] = [
    _rbD('f_pump', 23, 12, layer='back'), _rbD('f_pump', 43, 12, layer='back', v=1), _rbD('f_pipes', 6, 3, w=38, layer='back'),
    _rbD('f_valve', 15, 7), _rbD('f_valve', 28, 7), _rbD('f_gauge', 11, 12), _rbD('f_drift', 25, 12), _rbD('f_crystal', 38, 12),
    _rbD('f_sign', 21, 12, v=1), _rbD('f_snow', 6, 2, w=41, h=10, k=0.6),
    _rbE('hf_golem', 14, 12), _rbE('hf_golem', 32, 12), _rbE('hf_wraith', 27, 5),
]

# ---------------------------------------------------------------- HF13 Brazier Locks (puzzle)
# Three ice locks stacked in a shaft; a lit brazier thaws the lock its pipe runs to, a doused one lets it freeze again.
# From the top lock you can reach two fires (the top lock's and the bottom lock's), from the middle lock one more (the
# middle lock's) and the reliquary. Thaw the bottom lock first, or you land on it with no fire left to reach, and swim.
r = Room('HF13', 'Brazier Locks', 'hoarfrost', *_rbH(162, -88), 40, 22, indoor=True, x3=True, puzzle=True,
         needs=['talon', 'hook'], chests=['emberstone'])
r.walls()
r.fill(0, 0, 39, 1)
r.fill(12, 0, 14, 1, '.').fill(11, 2, 15, 2, '=')   # down from the Pump Station
r.fill(0, 2, 8, 20).fill(18, 2, 39, 20)             # the rock around the lock shaft (x 9..17)
r.fill(0, 21, 39, 21)
r.fill(9, 19, 30, 20, '.')                          # the outflow at the bottom
r.fill(18, 21, 20, 21, '=')                         # down to the Frozen Conduit
r.fill(9, 7, 17, 8, ':').fill(9, 12, 17, 13, ':').fill(9, 17, 17, 18, ':')   # the three locks (melted in the map)
r.fill(5, 5, 8, 6, '.').fill(18, 5, 21, 6, '.').fill(4, 10, 8, 11, '.').fill(18, 10, 21, 11, '.')    # niches
r.fill(22, 16, 30, 18, '.')                         # the outflow chamber
_rbput(r, [(20, 11, 'C'), (29, 20, 'k'), (10, 20, 'b'), (9, 3, 'k')])
r.kw['spawns'] = [
    _rbK('brazier', 6, 6, id='b1', skin='crystal'), _rbK('brazier', 20, 6, id='b2', skin='crystal'),
    _rbK('brazier', 6, 11, id='b3', skin='crystal'),
    dict(t='xrb_freeze', x=9, y=7, w=9, h=2, src='b1', id='L1'),
    dict(t='xrb_freeze', x=9, y=12, w=9, h=2, src='b3', id='L2'),
    dict(t='xrb_freeze', x=9, y=17, w=9, h=2, src='b2', id='L3'),
    dict(t='xrb_hint', x=13, y=5, freeze=['L1', 'L2', 'L3'],
         text='Follow the pipes: each fire thaws the lock its pipe runs to. Thaw the deepest lock while the ice above still holds you.'),
    _rbS('lore', 27, 20, page='rb_11', look='tablet'),
    _rbD('f_pipes', 23, 16, w=7, layer='back', v=1), _rbD('f_crystal', 24, 20), _rbD('f_drift', 13, 20),
    _rbD('f_frostpipe', 9, 3, w=9, h=17, v=1),
]
