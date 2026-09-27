# ============================================================ EXPANSION 3 — agent RC: Stormward Spire (+ The Last Field), The Deep, The Crown
# Runs inside tools/rooms.py's namespace (Room, ROOM, SOLID, GROUNDED, FLYING, HAZARD, free_spot).
# Engine: web/src/52_rc.js (xrc_* spawns, the lastfield biome, Ember Hatchling, trial charms, lore rc_*). Art: art/gen_xrc*.py.
#
# Every room sits in its region's zone (EXPANSION3 §7.2) and joins its old rooms through KS `door`s (the zones don't touch them):
#   SPIRE  SP3 ⇄ SP9 Fishers' Row → SP10 Sea-Wall Tunnels → SP11 Lower Harbor ⇄ SP1 (shortcut, lever on the Harbor side)
#          SP11 → SP12 Updraft Chimney → SP8 Storm Causeway (grand) → SP14 Kite Lines → SP13 Crumbling Stair ⇄ SP6
#          (the Stair's gate is worked from the SP6 side: the wing can't skip the Bell-Ringer). Off the spine: SP15 Lighthouse
#          Balcony (vista), SP16 Gale Trial (door from the Causeway's high route), SP17 The Crow's Nest (secret, glide).
#          LF1 The Last Field: a hidden passage + crack door in SP7's west wall (after Cindervane, a rest or 5 minutes).
#   DEEP   D4 ⇄ D9 Workers' Lift → D10 Ore Rail Tunnels → D11 The Great Forge (grand) → D12 Belt Runner ⇄ D7 (gate worked
#          from the D7 side: the wing can't skip the Overseer). Off it: D13 Slag Sluices (puzzle), D14 The Slag Pits and
#          D15 The Overseer's Floor (gauntlets), D16 Crucible Trial, D17 The Slam-cracked Vault (secret under the Forge).
#   CROWN  X3 ⇄ X6 Root Passage → X7 The Great Boughs (grand) → X8 Petal Stair → X9 Petal Drift ⇄ X4 (lever on the Drift
#          side). Off it: X11 The Crown Overlook (vista), X10 Thorned Gallery (gauntlet), X12 Sovereign's Trial.


def _rcpaint(r, rows):
    assert len(rows) == r.h, (r.id, len(rows), r.h)
    for y, row in enumerate(rows):
        assert len(row) == r.w, (r.id, y, len(row), r.w)
        for x, ch in enumerate(row):
            r.g[y][x] = ch
    return r


def _en(tp, x, y, **kw):
    return dict(t='enemy', type=tp, x=x, y=y, **kw)


def _spp(kind, x, y, **kw):          # 22_spire.js decor (lamp windmill cottage fence wheat window)
    return dict(t='sp_prop', kind=kind, x=x, y=y, **kw)


def _xp(kind, x, y, **kw):           # 52_rc.js decor / set pieces
    return dict(t='xrc', kind=kind, x=x, y=y, **kw)


def _door(x, y, id, to, toId=None, look='arch', **kw):
    return dict(t='sys', kind='door', x=x, y=y, id=id, to=to, toId=toId or id, look=look, **kw)


def _kit(kind, x, y, **kw):
    return dict(t='kit', kind=kind, x=x, y=y, **kw)


def _sys(kind, x, y, **kw):
    return dict(t='sys', kind=kind, x=x, y=y, **kw)


def _put(r, pts):
    for x, y, ch in pts:
        r.put(x, y, ch)


def _hollow(r, x0, y0, x1, y1):
    """clear a rectangle to open air"""
    return r.fill(x0, y0, x1, y1, '.')


# ============================================================================================ STORMWARD SPIRE
HAZARD.add("'")                    # the storm sea hurts and throws you back to firm ground: for reachability it's a hazard, not a floor
_SPW = dict(dir=-1, every=[5.0, 8.0], dur=2.2, push=74)

# ---- anchors in the old rooms (spawns only: doors and the Last Field passage)
ROOM('SP3').kw.setdefault('spawns', []).append(_door(17, 25, 'rc_sp', 'SP9', look='arch'))
ROOM('SP1').kw.setdefault('spawns', []).append(_door(10, 11, 'rc_sp', 'SP11', look='arch'))
ROOM('SP6').kw.setdefault('spawns', []).append(_door(16, 5, 'rc_sp', 'SP13', look='arch'))
ROOM('SP7').kw.setdefault('spawns', []).extend([
    # the wall where she fell splits once she is dead and you've rested (or five minutes have passed): a crack door behind it
    _sys('passage', 1, 15, w=1, h=3, id='lastfield', cond={'flag': 'boss:cindervane', 'restAfter': True, 'minTime': 300},
         drift='seed', wind=1, light='255,196,120'),
    _door(1, 15, 'lf', 'LF1', look='crack', auto=True, face=1),
])

# ---------------------------------------------------------------- SP9 Fishers' Row (huts on the sea wall; the wind rattles them)
r = Room('SP9', 'Fishers\' Row', 'spire', 70, -106, 48, 14, needs=['talon'], x3=True, wind=dict(dir=1, every=[4.5, 7.5], dur=2.2, push=70),
         spawns=[_door(43, 10, 'rc_sp', 'SP3', look='arch'), _sys('lore', 5, 10, page='rc_1', look='corpse'),
                 _en('sp_scarecrow', 15, 10, hidden=True), _en('sp_acolyte', 30, 7), dict(t='sp_perch', x=37, y=10, n=3),
                 dict(t='sp_puddle', x=26, y=10, w=3), dict(t='sp_puddle', x=8, y=10, w=2),
                 _xp('hut', 10, 10), _xp('hut', 31, 10, flip=1), _xp('nets', 38, 10), _xp('boat', 20, 11),
                 _spp('lamp', 6, 10), _spp('lamp', 25, 10), _spp('lamp', 41, 10), _spp('fence', 16, 10), _spp('fence', 26, 10)])
_rcpaint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "#............................................###",  # 0
    "#............................................###",  # 1
    "#............................................###",  # 2
    "#............................................###",  # 3
    "#.............................................##",  # 4
    "#.............................................##",  # 5
    "#.............................................##",  # 6
    "#.......======..........................======##",  # 7   hut roofs / the gatehouse loft
    "..........................======...............#",  # 8
    "...............................................#",  # 9
    "...............................................#",  # 10
    "#################......##########.......########",  # 11
    "#################''''''##########'''''''########",  # 12
    "################################################",  # 13
])
_put(r, [(3, 10, 'u'), (35, 10, 'b'), (46, 10, 'u'), (13, 6, 'b')])

# ---------------------------------------------------------------- SP10 Sea-Wall Tunnels (storm drains; waves burst through the grates)
r = Room('SP10', 'Sea-Wall Tunnels', 'spire', 22, -106, 48, 14, indoor=True, needs=['talon'], x3=True,
         spawns=[_en('sp_acolyte', 21, 4), _en('sp_acolyte', 40, 10), _en('sp_crow', 9, 5, air=True),
                 dict(t='sp_puddle', x=17, y=10, w=3), dict(t='sp_puddle', x=36, y=10, w=3), dict(t='sp_puddle', x=4, y=10, w=2),
                 _xp('grate', 13, 3, period=5.2, off=0.0, push=-150, area=[8, 2, 12, 9]),
                 _xp('grate', 31, 3, period=5.2, off=2.6, push=150, area=[27, 2, 12, 9]),
                 _xp('pipe', 44, 2), _xp('pipe', 3, 2), _spp('lamp', 25, 10), _spp('lamp', 45, 10), _spp('lamp', 13, 10)])
_rcpaint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "################################################",  # 0
    "################################################",  # 1
    "#...........###...............###..............#",  # 2
    "#.............................................##",  # 3
    "#..............................................#",  # 4
    "#.................######.......................#",  # 5
    "#..........======.######...........=====.......#",  # 6
    "#..............................................#",  # 7
    "................................................",  # 8
    "................................................",  # 9
    "................................................",  # 10
    "#######.....#######....####......##########.####",  # 11
    "#######'''''#######''''####''''''##########'####",  # 12
    "################################################",  # 13
])
_put(r, [(8, 2, 'l'), (24, 2, 'l'), (40, 2, 'l'), (2, 10, 'b'), (38, 10, 'k'), (20, 4, 'x')])

# ---------------------------------------------------------------- SP11 The Lower Harbor (docks, nets, a lift up the sea wall to SP1)
r = Room('SP11', 'The Lower Harbor', 'spire', -26, -106, 48, 14, needs=['talon'], x3=True, chests=['seed'], wind=dict(dir=-1, every=[5.5, 8.5], dur=2.0, push=66),
         spawns=[_door(45, 3, 'rc_sp', 'SP1', look='arch'),
                 _kit('lift', 33, 11, to=4, w=3),
                 _kit('gate', 40, 3, id='sg', persist=True),
                 _kit('lever', 37, 3, id='sl', targets=['sg'], once=True, msg='The sea-wall gate grinds open. A way back to the Sea-Wall Stair.'),
                 _en('sp_scarecrow', 7, 10, hidden=True), _en('sp_acolyte', 29, 10), _en('sp_crow', 12, 4, air=True), dict(t='sp_perch', x=4, y=10, n=3),
                 dict(t='sp_puddle', x=28, y=10, w=3),
                 _xp('nets', 9, 10), _xp('nets', 30, 10, flip=1), _xp('boat', 11, 11), _xp('boat', 19, 11, flip=1), _xp('crates', 17, 10),
                 _spp('lamp', 2, 10), _spp('lamp', 21, 10), _spp('lamp', 38, 3)])
_rcpaint(r, [
    #0         1         2         3         4
    #012345678901234567890123456789012345678901234567
    "##..............................################",  # 0   the gatehouse roof over the lift
    "#...............................################",  # 1
    "#..............................................#",  # 2
    "#..............................................#",  # 3   door ledge: lever 37, gate 40, door 45
    "#...................................############",  # 4
    "#...................................############",  # 5
    "#...................................############",  # 6
    "................=====..............#############",  # 7
    "...................................#############",  # 8
    "...................................#############",  # 9
    "...................................#############",  # 10  <- Sea-Wall Tunnels (rows 7-10)
    "#########.....###.....#####...###.....##########",  # 11
    "#########'''''###'''''#####...###'''''##########",  # 12
    "################################################",  # 13
])
r.fill(47, 7, 47, 10, '.').fill(36, 7, 46, 10, '.')     # the tunnel mouth runs under the sea wall
r.fill(36, 7, 47, 7)                                     # its lintel
r.fill(33, 11, 35, 11, '.')                              # the lift's pit (floor-level stop)
r.fill(28, 11, 30, 11, '#').fill(28, 12, 30, 12, '#')    # a stone quay
_put(r, [(25, 10, 'C'), (6, 10, 'b'), (44, 10, 'k')])

# ---------------------------------------------------------------- SP12 Updraft Chimney (ride the draughts up between crumbling blocks)
r = Room('SP12', 'Updraft Chimney', 'spire', -50, -152, 24, 60, indoor=True, needs=['talon'], x3=True, parkour=True,
         spawns=[_kit('wind', 2, 36, w=3, h=21, vy=-220),
                 _kit('crumble', 11, 33, w=2), _kit('crumble', 14, 30, w=2), _kit('crumble', 17, 27, w=2),
                 _kit('wind', 11, 11, w=3, h=13, vy=-230, period=3.2, on=[0, 0.62]),
                 _kit('crumble', 16, 45, w=2, respawn=2.5), _kit('crumble', 12, 49, w=2, respawn=2.5),
                 _en('sp_crow', 8, 22, air=True), _en('sp_crow', 15, 44, air=True),
                 _xp('pipe', 20, 30), _xp('grate', 6, 50, period=6.5, off=1.0, push=0, area=[0, 0, 0, 0]),
                 _spp('lamp', 8, 35), _spp('lamp', 20, 23), _spp('lamp', 5, 8), _spp('lamp', 19, 56)])
r.fill(0, 0, 23, 59)
_hollow(r, 2, 2, 21, 56)
_hollow(r, 10, 0, 13, 1)                                 # top: the flue opens onto the Storm Causeway
_hollow(r, 22, 53, 23, 56)                               # east: from the Lower Harbor
r.fill(5, 36, 9, 37)                                     # A: the first landing (off the west draught)
r.fill(18, 24, 21, 25)                                   # C: over the crumbling steps
r.fill(4, 9, 9, 10)                                      # D: under the flue
r.fill(2, 2, 9, 5).fill(14, 2, 21, 5)                    # the flue's cheeks: wall-jump up between them
r.fill(18, 38, 21, 41)                                   # a buttress on the east (the crumbling detour)
r.fill(2, 16, 5, 17)                                     # a west shelf (breather)
for y, x0, x1 in [(52, 5, 8), (46, 3, 6)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(7, 38, 'l'), (19, 26, 'l'), (6, 11, 'l'), (3, 56, 'b'), (19, 56, 'k'), (4, 15, 'b'), (20, 37, 'u'), (12, 6, 'x')])

# ---------------------------------------------------------------- SP8 The Storm Causeway (grand: the high towers, the deck, the drowned piers)
# Three ways east: the deck (lightning marks where it will fall, the wind shoves), the broken tower-tops (one-way beams, the
# Gale Trial door on the third tower) and the low road through the breached piers at sea level (a chest in the dark).
# Landmark: the Stormwarden, a drowned colossus holding up a dead lantern mid-causeway, seen from both headlands.
r = Room('SP8', 'The Storm Causeway', 'spire', -56, -180, 128, 28, needs=['talon'], x3=True, grand=True, chests=['gold'],
         storm=dict(every=[2.8, 4.6]), wind=dict(dir=-1, every=[5.0, 8.0], dur=2.4, push=78),
         spawns=[_door(81, 6, 'gale', 'SP16', look='arch'),
                 _en('sp_acolyte', 57, 14), _en('sp_acolyte', 88, 14), _en('sp_scarecrow', 34, 14, hidden=True), _en('sp_acolyte', 65, 7), _door(104, 7, 'gale2', 'SP16', look='arch'),
                 _en('sp_crow', 70, 10, air=True), _en('sp_crow', 47, 20, air=True), dict(t='sp_perch', x=12, y=17, n=3), dict(t='sp_perch', x=120, y=14, n=3),
                 dict(t='sp_puddle', x=61, y=14, w=3), dict(t='sp_puddle', x=84, y=14, w=2), dict(t='sp_puddle', x=107, y=14, w=3), dict(t='sp_puddle', x=31, y=21, w=2),
                 _xp('colossus', 61, 25), _xp('beam', 4, 3),
                 _spp('lamp', 30, 14), _spp('lamp', 55, 14), _spp('lamp', 77, 14), _spp('lamp', 100, 14), _spp('lamp', 122, 14), _spp('lamp', 9, 17),
                 _spp('fence', 118, 14), _xp('pennant', 37, 7), _xp('pennant', 104, 7),
                 _spp('lamp', 39, 22), _spp('lamp', 58, 22), _spp('lamp', 81, 22), _spp('lamp', 103, 22), _spp('lamp', 30, 21)])
r.fill(0, 27, 127, 27).fill(0, 26, 127, 26, "'")
r.fill(0, 18, 27, 26)                                    # the west headland (you climb out of the Chimney's flue into it)
_hollow(r, 16, 18, 19, 27)                               # the flue: wall-jump up out of the Updraft Chimney
r.fill(0, 0, 3, 12)                                      # the Lighthouse's footing; its door is the gap in rows 13-17
r.fill(24, 16, 27, 17)                                   # steps up onto the deck
r.fill(28, 15, 112, 16)                                  # the deck
r.fill(45, 15, 50, 16, '.').fill(45, 15, 50, 15, ';')    # a plank span that gives way
r.fill(67, 15, 72, 16, '.').fill(68, 18, 71, 19)         # a fallen span: drop to the stub and climb out
r.fill(91, 15, 96, 16, '.').fill(91, 15, 96, 15, ';')
r.fill(110, 15, 112, 25)                                 # the last pier
r.fill(116, 15, 127, 26)                                 # the east headland (the kite gorge beyond)
r.fill(124, 0, 127, 10)                                  # the gorge wall; the way on is rows 11-14
# the tower tops and the beams of the lost upper gallery (the high road)
r.fill(36, 8, 38, 14).fill(58, 7, 60, 14).fill(80, 7, 83, 14).fill(103, 8, 105, 14)
for y, x0, x1 in [(12, 30, 32), (9, 33, 34), (8, 42, 45), (8, 48, 51), (7, 54, 55), (8, 64, 67), (7, 71, 74), (7, 76, 77),
                  (8, 88, 91), (8, 95, 98), (11, 107, 109), (12, 40, 42), (12, 84, 86)]:
    r.fill(x0, y, x1, y, '=')
# the low road: rubble mounds in the surf, the piers' breached feet
for x0, x1, top in [(28, 33, 22), (37, 41, 23), (44, 49, 24), (56, 60, 23), (63, 67, 24), (70, 73, 22), (79, 83, 23), (86, 90, 24),
                    (93, 95, 23), (101, 105, 23), (107, 109, 24)]:
    r.fill(x0, top, x1, 25)
for x0 in (52, 74, 97):                                  # piers under the deck, each with a breach at the waterline
    r.fill(x0, 17, x0 + 2, 25).fill(x0, 20, x0 + 2, 23, '.')
    r.fill(x0 - 1, 24, x0 + 3, 25)
_put(r, [(89, 23, 'C'), (6, 17, 'b'), (40, 22, 'b'), (65, 14, 'b'), (119, 14, 'u'), (21, 17, 'u')])

# ---------------------------------------------------------------- SP15 Lighthouse Balcony (vista: the storm over the open sea)
r = Room('SP15', 'Lighthouse Balcony', 'spire', -88, -180, 32, 20, needs=['talon'], x3=True, vista=True,
         spawns=[_sys('bench', 11, 6, id='bench', view=[4, 9], lore='rc_2', face=-1),
                 _xp('lantern_room', 25, 6), _xp('railing', 8, 6), _xp('railing', 15, 6),
                 _spp('lamp', 21, 17), _spp('lamp', 29, 17)])
r.fill(0, 19, 31, 19).fill(1, 18, 31, 18, "'")
r.fill(0, 0, 0, 19)                                      # the sea-stack on the west (the frame of the view)
r.fill(1, 10, 3, 18).fill(1, 14, 5, 18)                  # its skirt of rocks in the surf
r.fill(18, 7, 31, 19)                                    # the lighthouse tower
_hollow(r, 20, 8, 30, 17)                                # its stair hall
_hollow(r, 31, 13, 31, 17)                               # door onto the Causeway's headland
r.fill(18, 0, 18, 6).fill(31, 0, 31, 12)                 # the lantern room's frame
_hollow(r, 21, 7, 23, 7)                                 # the hatch up to the lantern gallery
r.fill(4, 7, 17, 7)                                      # the balcony, cantilevered over the sea
for y, x0, x1 in [(15, 27, 29), (12, 22, 25), (9, 26, 29)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(28, 17, 'b'), (24, 6, 'k'), (20, 6, 'k'), (25, 8, 'l')])

# ---------------------------------------------------------------- SP14 Kite Lines (cross the gorge on the storm kites' lines)
r = Room('SP14', 'Kite Lines', 'spire', 72, -180, 48, 20, needs=['talon'], x3=True, parkour=True, items=['emberstone'],
         wind=dict(dir=-1, every=[6.0, 9.0], dur=1.8, push=60),
         spawns=[_kit('swing', 12, 3, len=7, amp=26, period=3.0, phase=0.0, drive='auto', rope='cable'),
                 _kit('swing', 20, 3, len=8, amp=26, period=3.0, phase=0.5, drive='auto', rope='cable'),
                 _kit('swing', 29, 3, len=7, amp=26, period=3.0, phase=0.0, drive='auto', rope='cable'),
                 _xp('kite', 12, 3), _xp('kite', 20, 3, c=1), _xp('kite', 29, 3, c=2),
                 _xp('winch', 5, 14), _en('sp_acolyte', 43, 13), _door(45, 13, 'nest', 'SP17', look='crack'), dict(t='sp_perch', x=38, y=13, n=4), _en('sp_crow', 24, 8, air=True),
                 _spp('lamp', 2, 14), _spp('lamp', 36, 13), _spp('fence', 45, 13)])
r.fill(0, 19, 47, 19).fill(8, 18, 35, 18, "'")
r.fill(0, 0, 3, 10).fill(0, 15, 7, 19)                   # the west headland (from the Causeway, rows 11-14)
r.fill(36, 14, 47, 19)                                   # the far landing
r.fill(44, 0, 47, 10).fill(47, 11, 47, 13)              # the foot of the great stack (the Crow's Nest is on its crown)
_hollow(r, 40, 14, 42, 19)                               # the drop into the Crumbling Stair
r.fill(24, 4, 25, 4, '=')                                # a kite-winch perch at the top of the gorge
_put(r, [(24, 3, 'i'), (37, 13, 'b'), (46, 13, 'u')])

# ---------------------------------------------------------------- SP17 The Crow's Nest (secret: a crack in the stack; the nest is a glide away)
# The nest shelf hangs off the stack's crown, far from any wall you could claw up: only the warm draught boiling out of the
# stack's heart carries you to it (Gale Cloak). Everything clingable is too far to jump from.
r = Room('SP17', 'The Crow\'s Nest', 'spire', 120, -194, 20, 14, needs=['talon', 'gale'], x3=True, secret=True, items=['shard'],
         spawns=[_door(2, 11, 'nest', 'SP14', look='crack', face=1),
                 _en('sp_crow', 9, 2, air=True), _en('sp_crow', 13, 6, air=True), _xp('bignest', 17, 2), _sys('lore', 18, 2, page='rc_3', look='corpse', face=-1)])
_rcpaint(r, [
    #01234567890123456789
    "####.|||||||||.....#",  # 0
    "####.|||||||||.....#",  # 1
    "####.|||||||||.....#",  # 2
    "####.|||||||||..####",  # 3
    "####.|||||||||..####",  # 4
    "####.|||||||||.....#",  # 5
    "####.|||||||||.....#",  # 6
    "####.|||||||||.....#",  # 7
    "####.|||||||||.....#",  # 8
    "#....|||||||||.....#",  # 9
    "#....|||||||||.....#",  # 10
    "#....|||||||||.....#",  # 11
    "####'''''''''''''''#",  # 12
    "####################",  # 13
])
_put(r, [(16, 2, 'i'), (1, 11, 'b')])

# ---------------------------------------------------------------- SP13 The Crumbling Stair (a stair falling apart as you climb; SP6 at its foot)
r = Room('SP13', 'The Crumbling Stair', 'spire', 104, -160, 32, 48, indoor=True, needs=['talon'], x3=True, parkour=True, items=['emberstone'],
         spawns=[_door(4, 45, 'rc_sp', 'SP6', look='arch'),
                 _kit('lever', 8, 45, id='stl', targets=['stg'], once=True, msg='The stair gate grinds up. The Stormward Cliffs are a door away now.'),
                 _kit('gate', 11, 45, id='stg', persist=True),
                 _en('sp_crow', 20, 30, air=True), _en('sp_crow', 9, 12, air=True), _en('sp_acolyte', 28, 32),
                 _xp('pipe', 29, 3), _spp('lamp', 28, 32), _spp('lamp', 7, 21), _spp('lamp', 25, 6), _spp('lamp', 14, 43)] +
                [_kit('crumble', x, y, w=2, delay=0.45, respawn=3) for x, y in
                 [(15, 42), (18, 40), (21, 38), (24, 36),                 # flight 1 (rising east)
                  (19, 31), (16, 29), (13, 27), (10, 25),                 # flight 2 (rising west)
                  (8, 18), (11, 16), (14, 14), (17, 12), (20, 10)]])      # flight 3 (rising east)
r.fill(0, 0, 31, 47)
_hollow(r, 1, 2, 30, 45)
_hollow(r, 8, 0, 10, 1)                                  # up into Kite Lines' landing
r.fill(1, 40, 12, 40)                                    # the lobby ceiling (the gate reaches it)
r.fill(12, 44, 30, 45)                                   # the stair foot
r.fill(26, 33, 30, 34)                                   # landing 1 (east)
r.fill(1, 22, 8, 23)                                     # landing 2 (west)
r.fill(3, 20, 5, 21)
r.fill(22, 7, 30, 8)                                     # landing 3 (east), under the hatch's ledge
r.fill(12, 4, 20, 5)                                     # the top floor; the hatch is over it
r.fill(26, 26, 30, 27)                                   # an alcove ledge (the stone)
for y, x0, x1 in [(30, 27, 29), (37, 2, 4)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(28, 25, 'i'), (3, 39, 'l'), (27, 32, 'l'), (4, 19, 'l'), (25, 6, 'l'), (2, 45, 'k'), (29, 43, 'b'), (6, 21, 'b')])

# ---------------------------------------------------------------- SP16 Gale Trial (glide the storm's own updrafts between its bolts)
# Door from the Causeway's third tower. Start bottom-left; three draughts lift you (U1 → L1 → U2 → L3), then one long glide
# back west along the roof of the storm, through the high draught, to the reliquary. Bolt columns (xrc 'bolts') fall on a beat.
r = Room('SP16', 'Gale Trial', 'spire', 8, -220, 48, 39, needs=['talon', 'gale'], x3=True, trial=True,
         spawns=[_door(2, 33, 'gale', 'SP8', look='arch'), _door(3, 4, 'gale2', 'SP8', look='arch'),
                 _sys('trial', 5, 33, id='gale', par=13, reward='c_x3_storm', region='Stormward Spire', name='The Gale Trial'),
                 _sys('trial_goal', 5, 4, trial='gale'),
                 _xp('bolts', 1, 1, cols=[[16, 2.2, 0.0], [32, 2.2, 1.1], [27, 1.8, 0.4], [12, 1.8, 1.3]], warn=0.8),
                 _xp('pennant', 20, 20)])
q = "'"
r.fill(0, 0, 0, 38).fill(47, 0, 47, 38).fill(0, 38, 47, 38).fill(1, 37, 46, 37, q)
r.fill(1, 34, 7, 37)                                     # the start ledge (sigil, door back down)
r.fill(9, 18, 16, 36, '|')                               # U1
r.fill(18, 21, 22, 22)                                   # L1
r.fill(24, 5, 31, 24, '|')                               # U2
r.fill(33, 8, 37, 9)                                     # L3
r.fill(15, 2, 22, 12, '|')                               # U3: the high draught
r.fill(1, 5, 7, 6)                                       # the reliquary ledge
r.fill(38, 10, 46, 36)                                   # the storm-wall of the east (nothing to cling to but rock)
_put(r, [(6, 33, 'k'), (20, 20, 'b'), (35, 7, 'u')])

# ---------------------------------------------------------------- LF1 The Last Field (secret vista, biome `lastfield`)
# Through the crack where Cindervane fell: a golden wheat field at sunset, the one warm place she kept. The ground rolls a
# tile at a time; wheat (drawn live in 52_rc.js) sways and parts around you; her nest lies in a hollow at the far end, the
# last egg still warm in it (Ember Hatchling). A lore stone tells the drakes' story; the bench looks back over the field.
r = Room('LF1', 'The Long Evening', 'lastfield', -110, -220, 112, 20, needs=['talon'], x3=True, vista=True,
         spawns=[_xp('wheat', 6, 0), _door(7, 16, 'lf', 'SP7', look='crack', face=1),
                 _sys('bench', 45, 15, id='bench', view=[62, 12], lore='rc_4', face=1),
                 _sys('lore', 74, 15, page='rc_5', look='none'), _xp('lorestone', 74, 15),
                 _xp('nest', 102, 17), _xp('egg', 102, 17),
                 _xp('deadtree', 108, 16), _xp('stones', 24, 15), _xp('fence', 34, 16), _xp('fence', 88, 16), _xp('plough', 58, 16)])
r.fill(0, 0, 5, 19)                                      # the storm-cliff you came through (the crack is its foot)
r.fill(110, 0, 111, 19)                                  # the old ash tree's roots and bole at the field's end
for x0, x1, top in [(6, 12, 17), (13, 24, 16), (25, 40, 17), (41, 52, 16), (53, 70, 17), (71, 84, 16), (85, 98, 17),
                    (99, 105, 18), (106, 109, 17)]:
    r.fill(x0, top, x1, 19)
                                                          # the nest lies in a shallow hollow (x 99-105) pressed into the earth


# ============================================================================================ THE DEEP
ROOM('D4').kw.setdefault('spawns', []).append(_door(6, 30, 'rc_dp', 'D9', look='arch'))
ROOM('D7').kw.setdefault('spawns', []).append(_door(4, 14, 'rc_dp', 'D12', look='arch'))

# ---------------------------------------------------------------- D9 Workers' Lift (a freight shaft; cages on chains)
r = Room('D9', 'Workers\' Lift', 'deep', 376, 136, 24, 40, indoor=True, needs=['talon'], x3=True,
         spawns=[_door(3, 5, 'rc_dp', 'D4', look='arch'),
                 _kit('lift', 9, 38, to=6, w=3),
                 _kit('mover', 15, 30, w=3, path=[[15, 30], [15, 16]], speed=1.6, wait=1.0, solid=True),
                 _kit('mover', 19, 24, w=3, path=[[19, 24], [19, 10]], speed=1.6, wait=1.0, solid=True, offset=0.5),
                 _en('dp_slag_imp', 20, 31), _en('dp_slag_imp', 20, 9), _en('dp_forge_sentry', 17, 37),
                 _xp('gear', 20, 5), _xp('pipes', 2, 30), _xp('cage', 5, 37)])
r.fill(0, 0, 23, 39)
_hollow(r, 1, 2, 22, 37)
_hollow(r, 0, 34, 0, 37)                                 # west: the ore tunnels
r.fill(1, 6, 8, 7)                                       # the landing from the Slag Chute
_hollow(r, 9, 38, 11, 38)                                # the lift's pit
r.fill(19, 32, 22, 33).fill(19, 10, 22, 11).fill(13, 20, 14, 21).fill(1, 22, 5, 23).fill(1, 14, 4, 15)
_put(r, [(4, 2, 'x'), (13, 2, 'x'), (21, 2, 'x'), (2, 37, 'k'), (22, 37, 'b'), (2, 21, 'b'), (7, 5, 'k'), (21, 31, 'k')])

# ---------------------------------------------------------------- D10 Ore Rail Tunnels (runaway ore carts thunder down the rails)
r = Room('D10', 'Ore Rail Tunnels', 'deep', 320, 162, 56, 14, indoor=True, needs=['talon'], x3=True,
         spawns=[_door(12, 11, 'pits', 'D14', look='arch'),
                 _xp('cart', 54, 11, dir=-1, period=7.5, off=2.0, speed=230),
                 _xp('rails', 1, 11, w=54), _xp('timbers', 16, 11), _xp('timbers', 36, 11), _xp('ore', 26, 11), _xp('ore', 49, 11),
                 _en('dp_slag_imp', 24, 11), _en('dp_slag_imp', 42, 8), _en('dp_forge_sentry', 31, 11)])
r.fill(0, 0, 55, 13)
_hollow(r, 1, 2, 54, 11)
_hollow(r, 0, 8, 0, 11).fill(55, 8, 55, 11, '.')         # the Forge (west) and the Workers' Lift (east)
for x0 in (5, 17, 29, 41):
    r.fill(x0, 9, x0 + 3, 9, '=')                        # timber cross-beams: step up out of a cart's way
r.fill(44, 12, 46, 12, '=').fill(44, 13, 46, 13, '.')     # a grate over the sluice-house below (↓ + jump)
r.fill(22, 2, 25, 4).fill(47, 2, 50, 3)                  # roof falls
_put(r, [(3, 2, 'l'), (19, 5, 'l'), (33, 2, 'l'), (52, 2, 'l'), (8, 11, 'k'), (38, 11, 'b'), (53, 11, 'b')])

# ---------------------------------------------------------------- D11 The Great Forge (grand: gantry, cranes, the foundry floor, the Heart-Furnace)
# High road: the crane hooks ride the ceiling rail west. Low road: down the gantry stair to the belts, the lava and the geysers.
# Secret: the cracked plug in the floor (Cinder Slam) over the Vault. Landmark: the Heart-Furnace, lit from far across the hall.
r = Room('D11', 'The Great Forge', 'deep', 228, 158, 92, 40, indoor=True, needs=['talon'], x3=True, grand=True, chests=['gold'],
         spawns=[_door(86, 35, 'floor', 'D15', look='arch'),
                 _kit('mover', 64, 10, w=3, path=[[64, 10], [15, 10]], speed=2.4, wait=1.4, solid=True),
                 _kit('mover', 22, 22, w=3, path=[[22, 22], [60, 22]], speed=2.0, wait=1.0, solid=True, offset=0.5),
                 _xp('furnace', 46, 28), _xp('crane_rail', 12, 3, w=58), _sys('lore', 73, 15, page='rc_7', look='book'),
                 _xp('geyser', 33, 35, period=4.2, off=0.0, h=7), _xp('geyser', 58, 35, period=4.2, off=2.1, h=7), _xp('geyser', 23, 35, period=3.6, off=1.2, h=6),
                 _xp('anvil_big', 76, 35), _xp('pipes', 88, 30), _xp('gear', 8, 30), _xp('gear', 70, 7),
                 _en('dp_slag_imp', 80, 15), _en('dp_slag_imp', 10, 10), _en('dp_forge_sentry', 66, 35), _en('dp_forge_sentry', 14, 35),
                 _en('dp_slag_imp', 50, 28), _en('dp_magma_crawler', 34, 36, air=True)])
r.fill(0, 0, 91, 39)
_hollow(r, 1, 2, 90, 35)
_hollow(r, 91, 12, 91, 15)                               # east: from the Ore Rail Tunnels
r.fill(70, 16, 90, 17)                                   # the gantry
r.fill(64, 13, 69, 13, '=')                              # the crane dock
for y, x0, x1 in [(20, 80, 84), (24, 72, 76), (28, 80, 84), (32, 72, 76)]:
    r.fill(x0, y, x1, y + 1)                             # the gantry stair down to the floor
r.fill(4, 11, 13, 12)                                    # the west crane dock
r.fill(42, 29, 51, 35)                                   # the Heart-Furnace's dais
r.fill(30, 36, 39, 37, '*').fill(54, 36, 63, 37, '*').fill(20, 36, 25, 37, '*')   # slag pools in the floor
r.fill(8, 36, 19, 36, '>').fill(64, 36, 71, 36, '<')       # belts feeding them
_hollow(r, 3, 36, 6, 39)                                 # the drop to the Belt Runner
r.fill(70, 36, 73, 39, 'Y')                              # a cracked plug in the floor (the Vault beneath)
for y, x0, x1 in [(32, 26, 28), (32, 40, 40), (32, 53, 53), (30, 58, 61), (27, 33, 36), (16, 30, 33), (16, 50, 53)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(47, 28, 'C'), (12, 2, 'x'), (30, 2, 'x'), (50, 2, 'x'), (68, 2, 'x'), (84, 2, 'x'), (88, 15, 'k'), (75, 15, 'b'),
         (2, 35, 'b'), (79, 35, 'k'), (8, 10, 'k')])

# ---------------------------------------------------------------- D12 Belt Runner (belts over the lava reverse on a beat)
r = Room('D12', 'Belt Runner', 'deep', 228, 198, 64, 16, indoor=True, needs=['talon'], x3=True, parkour=True,
         spawns=[_door(60, 7, 'rc_dp', 'D7', look='arch'),
                 _kit('lever', 58, 7, id='bl', targets=['bg'], once=True, msg='The runner gate winds up. The Crucible Gate is a door away.'),
                 _kit('gate', 55, 7, id='bg', persist=True),
                 _xp('beltflip', 20, 4, period=3.2, warn=0.9),
                 _en('dp_magma_crawler', 20, 11, air=True), _en('dp_magma_crawler', 40, 11, air=True), _en('dp_slag_imp', 5, 7),
                 _xp('pipes', 30, 3), _xp('gear', 62, 4)])
r.fill(0, 0, 63, 15)
_hollow(r, 1, 2, 62, 12)
_hollow(r, 3, 0, 6, 1)                                   # up into the Forge
r.fill(1, 2, 2, 7).fill(7, 2, 9, 7)                      # the chimney's cheeks (wall-jump back up)
r.fill(1, 8, 10, 12)                                     # west landing
r.fill(11, 11, 51, 12, '*')                              # the lava channel
for x0, x1, ch in [(12, 18, '>'), (22, 28, '<'), (32, 38, '>'), (42, 48, '<')]:
    r.fill(x0, 9, x1, 9, ch).fill(x0, 10, x1, 10)
r.fill(52, 8, 62, 12)                                    # east landing (the gate, the door to the Crucible Gate)
_put(r, [(8, 7, 'k'), (54, 7, 'b'), (20, 2, 'x'), (40, 2, 'x')])

# ---------------------------------------------------------------- D13 Slag Sluices (puzzle: pour the Smiths' Stair)
# Four valves on the sluice-master's gallery; pipes you can trace in the wall run from the hanging crucible to four moulds.
# Three moulds cast the stair up to the reliquary; the fourth (the Grave) only wastes a measure. The crucible holds three.
r = Room('D13', 'Slag Sluices', 'deep', 336, 176, 40, 24, indoor=True, needs=['talon'], x3=True, puzzle=True,
         spawns=[_door(34, 19, 'trial', 'D16', look='arch'),
                 _xp('sluice', 1, 1, molds=[[11, 17, 12, 19], [8, 14, 9, 19], [5, 11, 6, 19], [15, 14, 16, 19]],
                     valves=[[27, 4, 2], [29, 4, 3], [31, 4, 0], [33, 4, 1]], reset=[36, 4], crucible=[19, 3], reward=[2, 7]),
                 _sys('lore', 25, 4, page='rc_9', look='tablet'),
                 _en('dp_magma_crawler', 23, 20, air=True)])
r.fill(0, 0, 39, 23)
_hollow(r, 1, 1, 38, 19)
_hollow(r, 28, 0, 30, 0)                                 # the grate from the Ore Rail Tunnels
r.fill(27, 0, 27, 2).fill(31, 0, 31, 2)                  # the grate's chute (wall-jump back up)
r.fill(24, 5, 38, 6)                                     # the sluice-master's gallery
r.fill(1, 8, 4, 9)                                       # the reliquary ledge
r.fill(22, 20, 25, 21, '*')                              # the cooling gutter
_put(r, [(37, 19, 'k'), (13, 19, 'b'), (2, 1, 'x'), (37, 1, 'x')])

# ---------------------------------------------------------------- D14 The Slag Pits (gauntlet: the shift whistle)
r = Room('D14', 'The Slag Pits', 'deep', 336, 200, 40, 14, indoor=True, needs=['talon'], x3=True, gauntlet=True,
         spawns=[_door(3, 10, 'pits', 'D10', look='arch'),
                 _kit('gate', 6, 10, id='gL', open=True),
                 _sys('gauntlet', 22, 10, id='g1', look='whistle', name='The Slag Pits', gates=['gL'],
                      waves=[[dict(type='dp_slag_imp', x=11, y=10), dict(type='dp_slag_imp', x=21, y=10), dict(type='dp_slag_imp', x=34, y=10)],
                             [dict(type='dp_slag_imp', x=10, y=10), dict(type='ember_acolyte', x=25, y=10), dict(type='ember_acolyte', x=36, y=10), dict(type='dp_slag_imp', x=15, y=6)],
                             [dict(type='xrc_slag_foreman', x=22, y=10), dict(type='dp_slag_imp', x=9, y=10), dict(type='dp_slag_imp', x=35, y=10)]],
                      reward=['emberstone']),
                 _xp('beltflip', 20, 4, period=4.0, warn=0.9), _xp('pipes', 30, 3), _xp('ore', 37, 10)])
r.fill(0, 0, 39, 13)
_hollow(r, 1, 2, 38, 10)
r.fill(14, 11, 16, 12, '*').fill(28, 11, 30, 12, '*')
r.fill(8, 11, 13, 11, '>').fill(31, 11, 37, 11, '<')
r.fill(13, 7, 17, 7, '=').fill(27, 7, 31, 7, '=')
_put(r, [(2, 10, 'k'), (5, 2, 'x'), (20, 2, 'x'), (35, 2, 'x')])

# ---------------------------------------------------------------- D15 The Overseer's Floor (gauntlet: the foundry horn)
r = Room('D15', 'The Overseer\'s Floor', 'deep', 292, 214, 48, 16, indoor=True, needs=['talon'], x3=True, gauntlet=True,
         spawns=[_door(3, 12, 'floor', 'D11', look='arch'),
                 _kit('gate', 6, 12, id='gL', open=True),
                 _sys('gauntlet', 19, 12, id='g1', look='horn', name='The Overseer\'s Floor', gates=['gL'],
                      waves=[[dict(type='dp_forge_sentry', x=13, y=12), dict(type='dp_forge_sentry', x=38, y=12)],
                             [dict(type='dp_forge_sentry', x=19, y=8), dict(type='dp_slag_imp', x=11, y=12), dict(type='dp_slag_imp', x=42, y=12), dict(type='dp_magma_crawler', x=23, y=13)],
                             [dict(type='xrc_slag_golem', x=30, y=12), dict(type='dp_slag_imp', x=12, y=12), dict(type='dp_slag_imp', x=40, y=12)]],
                      reward=['emberstone', 600]),
                 _xp('beltflip', 20, 4, period=5.0, warn=1.0), _xp('overseer_seat', 40, 12), _xp('pipes', 16, 3), _xp('gear', 44, 4)])
r.fill(0, 0, 47, 15)
_hollow(r, 1, 2, 46, 12)
r.fill(22, 13, 25, 14, '*')
r.fill(8, 13, 15, 13, '>').fill(32, 13, 39, 13, '<')
r.fill(17, 9, 21, 9, '=').fill(27, 9, 31, 9, '=')
_put(r, [(2, 12, 'k'), (46, 12, 'b'), (10, 2, 'x'), (24, 2, 'x'), (36, 2, 'x')])

# ---------------------------------------------------------------- D16 Crucible Trial (climb while the lava rises behind you)
# Slag falls down both walls (no clawing up the sides). Ledges, a wall-jump chimney, crumbling steps, a switchback of
# catwalks, then the reliquary under the crucible's lip. The lava starts rising when you leave the floor.
r = Room('D16', 'Crucible Trial', 'deep', 376, 176, 24, 64, indoor=True, needs=['talon'], x3=True, trial=True,
         spawns=[_door(3, 61, 'trial', 'D13', look='arch'),
                 _sys('trial', 7, 61, id='crucible', par=24, reward='c_x3_slag', region='The Deep', name='The Crucible Trial'),
                 _sys('trial_goal', 13, 4, trial='crucible'),
                 _kit('rising', 2, 61, w=20, stopY=5, speed=2.5, delay=1.0, fluid='lava', trigger='zone', zone=[2, 50, 20, 9], respawn=[7, 61]),
                 _xp('gear', 5, 44), _xp('gear', 18, 30), _xp('cage', 8, 1), _xp('pipes', 19, 61), _xp('cage', 16, 1)] +
                [_kit('crumble', x, y, w=2, delay=0.45, respawn=2.5) for x, y in [(9, 32), (5, 29)]])
r.fill(0, 0, 23, 63)
_hollow(r, 1, 1, 22, 61)
r.fill(1, 3, 1, 57, '*').fill(22, 3, 22, 57, '*')            # slag falls down both walls: no clawing up the sides
for y, x0, x1 in [(59, 5, 8), (56, 11, 14), (53, 16, 19)]:
    r.fill(x0, y, x1, y, '=')                            # 1. up to the chimney
r.fill(15, 36, 15, 50).fill(20, 36, 20, 50)              # 2. the chimney (wall-jump)
r.put(16, 49, '=').put(19, 44, '=').put(16, 39, '=')   # iron rungs in it: somewhere to catch your breath
r.fill(11, 35, 14, 35)                                   # out over its lip, west
r.fill(2, 26, 5, 26)                                     # 3. after the crumbling steps
for y, x0, x1 in [(23, 8, 11), (20, 14, 17), (17, 9, 12), (14, 3, 6), (11, 9, 12), (8, 14, 17)]:
    r.fill(x0, y, x1, y, '=')                            # 4. the switchback catwalks
r.fill(7, 5, 13, 5)                                      # the reliquary ledge
_put(r, [(2, 61, 'k'), (21, 61, 'b'), (5, 1, 'x'), (18, 1, 'x')])

# ---------------------------------------------------------------- D17 The Slam-cracked Vault (secret: under the Forge's cracked plug)
r = Room('D17', 'The Slam-cracked Vault', 'deep', 296, 198, 16, 14, indoor=True, needs=['talon', 'slam'], x3=True, secret=True, chests=['seed'],
         spawns=[_sys('lore', 8, 11, page='rc_8', look='corpse', face=-1), _xp('hoard', 12, 11), _xp('hoard', 4, 11, flip=1)])
r.fill(0, 0, 15, 13)
_hollow(r, 1, 7, 14, 11)
_hollow(r, 2, 0, 5, 6)                                   # the broken plug's shaft (wall-jump back up)
_put(r, [(11, 11, 'C'), (1, 11, 'k'), (14, 11, 'k'), (8, 7, 'l')])


# ============================================================================================ THE CROWN
ROOM('X3').kw.setdefault('spawns', []).append(_door(45, 10, 'rc_cr', 'X6', look='arch'))
ROOM('X4').kw.setdefault('spawns', []).append(_door(21, 10, 'rc_cr', 'X9', look='arch'))

# ---------------------------------------------------------------- X6 The Root Passage (a tunnel through the living wood)
r = Room('X6', 'The Root Passage', 'crown', 565, 25, 48, 14, indoor=True, needs=['talon'], x3=True,
         spawns=[_door(4, 11, 'rc_cr', 'X3', look='arch'), _sys('lore', 43, 11, page='rc_12', look='stone'),
                 _en('root_spawn', 14, 11), _en('root_spawn', 34, 11), _en('root_spawn', 40, 11), _en('sun_seraph', 27, 5, air=True),
                 _xp('sapvein', 5, 2), _xp('sapvein', 31, 2), _xp('sapvein', 44, 2), _xp('rootknot', 16, 11), _xp('rootknot', 38, 11, flip=1)])
r.fill(0, 0, 47, 13)
_hollow(r, 1, 2, 46, 11)
_hollow(r, 47, 8, 47, 11)                                # east: into the Great Boughs
_hollow(r, 20, 0, 22, 1)                                 # up into the Thorned Gallery
for y, x0, x1 in [(9, 17, 19), (6, 22, 24), (3, 18, 21)]:
    r.fill(x0, y, x1, y, '=')                            # root rungs up to the gallery
r.fill(27, 12, 31, 12, '^')                              # a thorn-choked stretch of the floor
r.fill(29, 8, 30, 8, '=')
r.fill(8, 2, 11, 3).fill(40, 2, 43, 4)                   # knotted ceiling
_put(r, [(2, 11, 'k'), (45, 11, 'k'), (24, 11, 'b'), (6, 2, 'r'), (14, 2, 'r'), (26, 2, 'r'), (36, 2, 'r')])

# ---------------------------------------------------------------- X10 The Thorned Gallery (gauntlet: the thorned idol calls the sentinels' echoes)
r = Room('X10', 'Thorned Gallery', 'crown', 565, 11, 48, 14, indoor=True, needs=['talon'], x3=True, gauntlet=True,
         spawns=[_kit('gate', 24, 11, id='gA', open=True), _kit('gate', 44, 11, id='gB', open=True),
                 _sys('gauntlet', 34, 11, id='g1', look='idol', name='The Thorned Gallery', gates=['gA', 'gB'],
                      waves=[[dict(type='root_spawn', x=28, y=11), dict(type='root_spawn', x=40, y=11), dict(type='sun_seraph', x=34, y=5)],
                             [dict(type='gilded_sentinel', x=38, y=11), dict(type='root_spawn', x=27, y=11), dict(type='root_spawn', x=41, y=11)],
                             [dict(type='xrc_sentinel_echo', x=30, y=11), dict(type='sun_seraph', x=36, y=4), dict(type='sun_seraph', x=27, y=5)]],
                      reward=['emberstone', 'shard']),
                 _xp('portrait', 30, 7), _xp('portrait', 38, 7), _xp('thornbrazier', 26, 11), _xp('thornbrazier', 42, 11)])
r.fill(0, 0, 47, 13)
_hollow(r, 1, 2, 46, 11)
_hollow(r, 20, 12, 22, 13)                               # the hole down into the Root Passage
_hollow(r, 47, 7, 47, 10)                                # east: out onto a bough of the Great Boughs
r.fill(1, 2, 19, 4)                                      # the antechamber's low ceiling
r.fill(30, 7, 38, 7, '=')                                # the gallery's balcony
_put(r, [(3, 11, 'k'), (46, 10, 'b'), (10, 11, 'b'), (28, 2, 'r'), (40, 2, 'r')])

# ---------------------------------------------------------------- X11 The Crown Overlook (vista: the whole Hallow below)
r = Room('X11', 'The Crown Overlook', 'crown', 565, -13, 48, 24, needs=['talon'], x3=True, vista=True,
         spawns=[_sys('bench', 20, 19, id='bench', view=[14, 12], lore='rc_10', face=-1),
                 _xp('panorama', 1, 1), _xp('blossom', 12, 19), _xp('blossom', 34, 19, flip=1)])
r.fill(0, 0, 0, 23)                                      # a rising limb frames the west
r.fill(1, 20, 47, 23)                                    # the bough's crown, pale bark
r.fill(47, 0, 47, 15)                                    # the Boughs' outer bark (the way in is rows 16-19)
r.fill(1, 17, 3, 19).fill(1, 12, 1, 16)
r.fill(38, 17, 41, 19)
_put(r, [(8, 19, 'k'), (28, 19, 'k'), (44, 19, 'b')])

# ---------------------------------------------------------------- X7 The Great Boughs (grand: climb the Pale Root's crown)
# Low road: along the great root to the Petal Stair (east, bottom). High road: up the trunk's boughs to Petal Drift (east, top).
# Side ways: the Thorned Gallery (west, middle) and the Crown Overlook (west, top). Secret: a knot of dead bark hides a seed.
# Landmark: the Heartbloom, a vast lantern-flower on the crown, shedding petals over everything.
r = Room('X7', 'The Great Boughs', 'crown', 613, -8, 72, 48, needs=['talon'], x3=True, grand=True, items=['seed'],
         spawns=[_xp('heartbloom', 36, 8), _xp('petals', 1, 1), _sys('lore', 63, 11, page='rc_11', look='tablet'),
                 _en('root_spawn', 24, 38), _en('root_spawn', 52, 32), _en('sun_seraph', 50, 20, air=True), _en('sun_seraph', 18, 12, air=True),
                 _en('gilded_sentinel', 52, 26), _en('root_spawn', 22, 23),
                 _xp('blossom', 10, 44), _xp('blossom', 60, 44, flip=1), _xp('blossom', 24, 23)])
r.fill(0, 45, 71, 47)                                    # the great root
r.fill(0, 0, 0, 44).fill(71, 0, 71, 44)                  # the outer bark
_hollow(r, 0, 41, 0, 44)                                 # west: the Root Passage
_hollow(r, 71, 41, 71, 44)                               # east: the Petal Stair
_hollow(r, 0, 26, 0, 29)                                 # west: the Thorned Gallery
_hollow(r, 0, 11, 0, 14)                                 # west: the Crown Overlook
_hollow(r, 71, 8, 71, 11)                                # east: Petal Drift (the high road)
r.fill(32, 12, 39, 44)                                   # the trunk
# boughs (two courses of pale bark) and twigs, every rise three rows: west of the trunk, then east
for x0, x1, y in [(14, 31, 39), (10, 20, 33), (1, 8, 30), (18, 31, 24), (12, 24, 18), (1, 10, 15), (20, 47, 9),
                  (44, 56, 39), (48, 63, 33), (46, 60, 27), (44, 58, 21), (48, 62, 15), (60, 70, 12)]:
    r.fill(x0, y, x1, y + 1)
for y, x0, x1 in [(42, 8, 11), (36, 4, 7), (27, 12, 15), (21, 7, 10), (12, 14, 17),
                  (42, 58, 61), (36, 64, 67), (30, 42, 45), (24, 64, 67), (18, 60, 63), (6, 50, 53)]:
    r.fill(x0, y, x1, y, '=')
r.fill(1, 18, 4, 18).fill(1, 22, 6, 23).fill(4, 19, 4, 21, 'B')   # a knot of dead bark (strike it): the seed within
_put(r, [(2, 21, 'i'), (30, 44, 'k'), (44, 44, 'k'), (2, 44, 'b'), (69, 44, 'b'), (28, 37, 'k')])

# ---------------------------------------------------------------- X8 The Petal Stair (bark ledges under falling petals)
r = Room('X8', 'Petal Stair', 'crown', 685, 8, 24, 32, indoor=True, needs=['talon'], x3=True,
         spawns=[_en('root_spawn', 16, 22), _en('sun_seraph', 12, 12, air=True), _en('root_spawn', 5, 10), _xp('petals', 1, 1),
                 _xp('sapvein', 20, 14), _xp('blossom', 19, 28)])
r.fill(0, 0, 23, 31)
_hollow(r, 1, 1, 22, 28)
_hollow(r, 0, 25, 0, 28)                                 # west: the Great Boughs' root
_hollow(r, 23, 25, 23, 28)                               # east: the Sovereign's Trial
_hollow(r, 10, 0, 13, 0)                                 # up into Petal Drift
for x0, x1, y in [(15, 20, 23), (3, 8, 19), (13, 19, 15), (2, 7, 11), (15, 21, 7), (5, 9, 4)]:
    r.fill(x0, y, x1, y + 1)
for y, x0, x1 in [(26, 9, 11), (21, 10, 12), (13, 9, 10), (9, 9, 11), (2, 10, 13)]:
    r.fill(x0, y, x1, y, '=')
_put(r, [(2, 28, 'k'), (21, 28, 'b'), (4, 1, 'r'), (18, 1, 'r')])

# ---------------------------------------------------------------- X9 Petal Drift (great petals ride the wind; X4 at the far end)
r = Room('X9', 'Petal Drift', 'crown', 685, -13, 56, 21, needs=['talon'], x3=True, parkour=True, items=['emberstone'],
         spawns=[_door(54, 11, 'rc_cr', 'X4', look='arch'),
                 _kit('lever', 50, 11, id='pl', targets=['pg'], once=True, msg='The bark gate draws back. The Crown Shrine lies beyond.'),
                 _kit('gate', 52, 11, id='pg', persist=True),
                 _kit('mover', 16, 15, w=3, path=[[16, 15], [20, 12], [24, 15], [20, 17]], loop=True, speed=1.5, wait=0, petal=True),
                 _kit('mover', 27, 11, w=3, path=[[27, 11], [31, 8], [35, 11], [31, 13]], loop=True, speed=1.5, wait=0, offset=0.5, petal=True),
                 _kit('mover', 38, 12, w=3, path=[[38, 12], [44, 9]], speed=1.3, wait=0.6, petal=True),
                 _kit('mover', 28, 5, w=2, path=[[28, 5], [33, 5]], speed=1.0, wait=0.8, petal=True),
                 _kit('wind', 15, 2, w=34, h=16, vx=-40, period=6, on=[0, 0.35]),
                 _xp('petals', 1, 1), _en('sun_seraph', 30, 3, air=True), _en('sun_seraph', 42, 14, air=True),
                 _xp('blossom', 3, 16)])
r.fill(0, 20, 55, 20)
r.fill(0, 0, 0, 12).fill(55, 0, 55, 20)
r.fill(0, 17, 9, 19).fill(14, 17, 15, 19)                # the west landing (the Stair's hatch in between)
_hollow(r, 10, 17, 13, 20)
r.fill(16, 19, 48, 19, '^')                              # thorns under the drift
r.fill(49, 12, 54, 19)                                   # the east ledge
r.fill(49, 0, 55, 7)                                     # the bark arch over the gate
r.fill(31, 5, 32, 5, '=')
_put(r, [(31, 4, 'i'), (2, 16, 'k'), (53, 11, 'k')])

# ---------------------------------------------------------------- X12 Sovereign's Trial (hook, dash, glide and slam in one run)
r = Room('X12', 'Sovereign\'s Trial', 'crown', 709, 8, 52, 32, indoor=True, needs=['talon', 'hook', 'emberdash', 'gale', 'slam'], x3=True, trial=True,
         spawns=[_sys('trial', 4, 28, id='sovereign', par=18, reward='c_x3_crown', region='The Crown', name='The Sovereign\'s Trial'),
                 _sys('trial_goal', 5, 6, trial='sovereign'), _xp('pennant', 9, 6),
                 _xp('thornbrazier', 6, 28), _xp('thornbrazier', 2, 6), _xp('blossom', 25, 22), _xp('portrait', 32, 20), _xp('sapvein', 20, 15),
                 _xp('sapvein', 13, 15), _xp('blossom', 48, 3), _xp('rootknot', 40, 27), _xp('thornbrazier', 30, 22)])
r.fill(0, 0, 51, 31)
_hollow(r, 1, 1, 50, 28)
_hollow(r, 0, 25, 0, 28)                                 # west: from the Petal Stair
r.fill(7, 28, 22, 28, '^')                               # 1. the thorn pit under the hook rings (Root Hook)
r.put(13, 19, '@').put(19, 18, '@')
r.fill(23, 23, 27, 28)                                   # landing
r.fill(28, 12, 28, 28).fill(28, 19, 28, 22, '%')         # 2. an ash veil in a bark wall (Ember Dash)
r.fill(29, 4, 36, 18).fill(36, 19, 36, 24)               # the cell beyond the veil
r.fill(29, 23, 35, 24).fill(31, 23, 34, 24, 'Y')         # 3. its cracked floor (Cinder Slam) over the root-way
r.fill(29, 28, 50, 28)                                   # the root-way's floor
r.fill(37, 1, 44, 27, '|')                               # 4. the updraft shaft (Gale Cloak): ride it up the east wall
r.fill(45, 4, 50, 27)                                    # the east ledge at the top of the shaft
r.fill(11, 12, 27, 12, '^').fill(11, 13, 27, 14)         # 5. the long glide west over the thorns...
r.fill(18, 1, 21, 11, '|')                               # ...with one thermal to carry you
r.fill(1, 7, 10, 22)                                     # the reliquary ledge and the wall under it
_hollow(r, 8, 20, 10, 22).fill(8, 20, 8, 20)               # a chamfered corner: the first ring is in sight from the start
_put(r, [(2, 28, 'k'), (24, 22, 'b'), (48, 3, 'b')])
