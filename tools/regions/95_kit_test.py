# ============================================================ KIT WORKSHOP (agent KM) — test room T1 for the kit mechanics
# Runs inside tools/rooms.py's namespace. A sealed test room (reach it with __game.tp('T1', x, y)): five floors stacked
# vertically, a labelled demo of every `t:'kit'` part (web/src/42_kit.js, docs/KIT_API.md ## Mechanics).
# Also: kit_lint() checks every kit spawn in the rooms built so far (all region modules numbered below 95).
KIT_KINDS_PY = {'mover', 'lift', 'crumble', 'sinker', 'phase', 'swing', 'pendulum', 'rising', 'wind', 'spring', 'crate',
                'lever', 'switch', 'plate', 'gate', 'seq', 'bell', 'lantern', 'glyph', 'stop', 'frame', 'brazier',
                'beam', 'mirror', 'socket', 'level', 'label'}


def K(kind, x, y, **kw):
    return dict(t='kit', kind=kind, x=x, y=y, **kw)


r = Room('T1', 'Kit Workshop', 'catacombs', -400, 0, 100, 100, indoor=True, test=True)
r.walls()
sp = []
for F in (0, 20, 40, 60, 80):             # floor slabs (each is the next floor's ceiling)
    r.fill(0, F + 17, 99, F + 19)
FL = lambda F: F + 17                     # floor surface row of a storey


def pit(x0, x1, F, spikes=True):
    r.fill(x0, FL(F), x1, FL(F) + 1, '.')
    if spikes: r.fill(x0, FL(F) + 1, x1, FL(F) + 1, '^')


def lintel(x, F, top, bot):              # the wall block a gate hangs from (gates reach the ceiling)
    r.fill(x - 1, top, x + 1, bot)


# ---------------------------------------------------------------- floor 0: movers, lifts, crumbles, sinkers
F = 0
sp += [K('label', 2, 14, text='MOVERS'), K('label', 13, 13, text='oneway, pingpong'), K('label', 25, 13, text='solid, vertical'),
       K('label', 12, 4, text='loop'), K('label', 35, 5, text='stand to ride, returns')]
pit(8, 22, F)
sp += [K('mover', 8, 15, w=3, path=[[8, 15], [20, 15]], speed=2, wait=0.6, skin='stone', id='mA'),
       K('mover', 24, 15, w=3, path=[[24, 15], [24, 7]], speed=1.5, wait=1, solid=True, skin='iron', id='mB'),
       K('mover', 10, 11, w=2, path=[[10, 11], [16, 11], [16, 6], [10, 6]], loop=True, speed=1.5, wait=0, skin='wood', id='mC'),
       K('mover', 32, 7, w=3, path=[[32, 7], [40, 7]], trigger='stand', speed=2.5, skin='bone', id='mD', **{'return': 2})]
r.fill(27, 7, 31, 8).fill(43, 7, 47, 8)
# lift in a pit (bottom stop flush with the floor), top landing on the right; an auto lift beside it
sp += [K('label', 48, 14, text='LIFT (call it)'), K('label', 60, 13, text='auto lift')]
r.fill(49, 17, 51, 18, '.')
sp += [K('lift', 49, 17, to=5, skin='stone', id='lift1'), K('lift', 60, 15, to=5, auto=True, skin='iron', id='lift2')]
r.fill(52, 5, 58, 6)
# crumbles over spikes (the last never comes back)
sp += [K('label', 64, 12, text='CRUMBLE'), K('label', 73, 11, text='respawn 0')]
pit(64, 78, F)
sp += [K('crumble', 65, 14, w=2, skin='stone'), K('crumble', 69, 14, w=2, skin='wood'), K('crumble', 73, 14, w=2, respawn=0, skin='bone')]
# sinkers on a poison pool
sp += [K('label', 82, 14, text='SINKERS')]
r.fill(80, 17, 97, 18, '~')
sp += [K('sinker', 81, 17, w=2, skin='wood'), K('sinker', 85, 17, w=2, skin='wood'), K('sinker', 89, 17, w=2, skin='bone', delay=0.5), K('sinker', 93, 17, w=2, skin='stone')]

# ---------------------------------------------------------------- floor 1: phase platforms, swings, pendulums
F = 20
sp += [K('label', 2, 33, text='PHASE (beat 2.4 s)')]
pit(4, 22, F)
for i, (x, on) in enumerate([(5, [0, 0.5]), (9, [0.25, 0.75]), (13, [0.5, 1]), (17, [0.75, 0.25])]):
    sp.append(K('phase', x, 35, w=2, period=2.4, on=on, skin=['crystal', 'neon', 'bone', 'stone'][i], group='p1'))
sp += [K('label', 27, 31, text='SWINGS: rope chain vine cable(auto)')]
pit(28, 56, F)
r.fill(26, 33, 27, 36).fill(57, 33, 58, 36)
sp += [K('swing', 32, 20, len=9, skin='stone'), K('swing', 38, 20, len=9, skin='iron'), K('swing', 44, 20, len=9, skin='wood'),
       K('swing', 50, 20, len=9, skin='neon', drive='auto', amp=35, period=2.6)]
sp += [K('label', 63, 32, text='PENDULUMS')]
r.fill(62, 28, 84, 29)
sp += [K('pendulum', 66, 30, len=6, period=2.2, amp=55, phase=0, skin='iron'),
       K('pendulum', 72, 30, len=6, period=2.2, amp=55, phase=0.33, skin='bone'),
       K('pendulum', 78, 30, len=6, period=2.2, amp=55, phase=0.66, skin='neon')]

# ---------------------------------------------------------------- floor 2: wind, spring, crate/plate/gate, levers
F = 40
sp += [K('label', 3, 49, text='WIND gusts'), K('label', 17, 41, text='updraft')]
sp += [K('wind', 4, 50, w=13, h=7, vx=-150, period=3, on=[0, 0.55], skin='stone'), K('wind', 18, 42, w=3, h=15, vy=-200, skin='crystal')]
r.fill(21, 44, 25, 45)
sp += [K('label', 28, 52, text='SPRING'), K('spring', 29, 56, skin='iron')]
r.fill(32, 45, 36, 46)
sp += [K('label', 39, 50, text='CRATE > PLATE > GATE')]
lintel(51, F, 40, 51)
sp += [K('crate', 40, 56, skin='wood'), K('plate', 45, 56, w=2, skin='stone', id='pl1', targets=['g1']),
       K('gate', 51, 56, id='g1', logic='any', skin='iron')]
sp += [K('label', 56, 50, text='lever'), K('label', 64, 50, text='timer 4s'), K('label', 72, 50, text='switch persist'), K('label', 80, 48, text='WINCH: both timers')]
lintel(61, F, 40, 51); lintel(69, F, 40, 51); lintel(76, F, 40, 51); lintel(94, F, 40, 51)
sp += [K('lever', 57, 56, id='L1', targets=['g2'], skin='stone'), K('gate', 61, 56, id='g2', skin='stone'),
       K('lever', 65, 56, id='L2', targets=['g3'], timer=4, skin='iron'), K('gate', 69, 56, id='g3', skin='iron'),
       K('switch', 73, 56, id='S1', targets=['g4'], skin='bone'), K('gate', 76, 56, id='g4', skin='bone', persist=True),
       K('lever', 80, 56, id='W1', targets=['g5'], timer=6, skin='wood'), K('lever', 90, 56, id='W2', targets=['g5'], timer=6, skin='wood'),
       K('gate', 94, 56, id='g5', logic='all', skin='wood')]

# ---------------------------------------------------------------- floor 3: sequences (bells, glyphs, braziers), light beam
F = 60
sp += [K('label', 3, 68, text='SEQ bells: 3 1 4 2')]
r.fill(3, 70, 19, 71)
lintel(22, F, 60, 71)
for i, x in enumerate([5, 9, 13, 17]):
    sp.append(K('bell', x, 72, id=f'b{i + 1}', group='bells', note=[0, 2, 4, 5][i]))
sp += [K('seq', 20, 76, id='sq1', group='bells', order=['b3', 'b1', 'b4', 'b2'], targets=['g6']), K('gate', 22, 76, id='g6', skin='bone')]
sp += [K('label', 26, 69, text='SEQ glyphs: C A D B')]
lintel(44, F, 60, 71)
for i, x in enumerate([28, 32, 36, 40]):
    sp.append(K('glyph', x, 74, id='gA gB gC gD'.split()[i], group='glyphs', sym=i, note=i + 3))
sp += [K('seq', 42, 76, id='sq2', group='glyphs', order=['gC', 'gA', 'gD', 'gB'], targets=['g7']), K('gate', 44, 76, id='g7', skin='stone')]
sp += [K('label', 48, 68, text='SEQ braziers: 2 3 1')]
lintel(62, F, 60, 71)
for i, x in enumerate([50, 54, 58]):
    sp.append(K('brazier', x, 76, id=f'f{i + 1}', group='fire', skin=['stone', 'iron', 'bone'][i]))
sp += [K('seq', 60, 76, id='sq3', group='fire', order=['f2', 'f3', 'f1'], targets=['g8']), K('gate', 62, 76, id='g8', skin='stone')]
sp += [K('label', 65, 68, text='members'), K('lantern', 66, 76, id='ln1'), K('stop', 69, 74, id='st1', note=3), K('frame', 72, 74, id='fr1')]
sp += [K('label', 76, 69, text='BEAM: turn both mirrors')]
lintel(96, F, 60, 71)
sp += [K('beam', 77, 75, dir='right', skin='stone'), K('mirror', 84, 75, id='M1', rot=0, skin='stone'), K('mirror', 84, 72, id='M2', rot=1, skin='stone'),
       K('socket', 92, 72, id='so1', targets=['g9'], skin='stone'), K('gate', 96, 76, id='g9', skin='stone')]

# ---------------------------------------------------------------- floor 4: fluid levels, rising lava, skin gallery
F = 80
sp += [K('label', 2, 85, text='LEVEL water: 2 levers')]
r.fill(5, 88, 5, 96).fill(19, 88, 19, 96).fill(6, 97, 18, 98, '.')
sp += [K('level', 6, 88, w=13, h=11, states=[98, 93, 89], fluid='water', id='lvl'), K('lever', 3, 96, targets=['lvl'], skin='stone'), K('lever', 21, 96, targets=['lvl'], skin='stone')]
sp += [K('label', 24, 87, text='LEVEL poison')]
r.fill(24, 90, 24, 96).fill(36, 90, 36, 96).fill(25, 97, 35, 98, '.')
sp += [K('level', 25, 90, w=11, h=9, states=[98, 94], fluid='poison', id='lvl2'), K('lever', 38, 96, targets=['lvl2'], skin='wood')]
sp += [K('label', 43, 91, text='RISING lava: climb!')]
r.fill(42, 81, 42, 92).fill(60, 81, 60, 96)
for row, x0, x1 in [(94, 52, 58), (91, 44, 50), (88, 52, 58), (85, 44, 50), (82, 50, 58)]:
    r.fill(x0, row, x1, row, '=')
sp += [K('rising', 43, 96, w=17, stopY=83, speed=0.9, fluid='lava', zone=[43, 93, 8, 4], respawn=[40, 96], goal=[50, 80, 9, 2], id='rise1')]
sp += [K('label', 63, 83, text='SKINS: stone bone wood iron crystal neon')]
for i, sk in enumerate(['stone', 'bone', 'wood', 'iron', 'crystal', 'neon']):
    x0 = 62 + 6 * i
    lintel(x0 + 4, F, 80, 91)
    sp += [K('mover', x0, 89, w=2, skin=sk), K('lever', x0, 96, skin=sk, id=f'gl{i}', targets=[f'gg{i}']), K('brazier', x0 + 1, 96, skin=sk, lit=True),
           K('crate', x0 + 2, 96, skin=sk), K('plate', x0 + 3, 96, skin=sk), K('gate', x0 + 4, 96, skin=sk, id=f'gg{i}'),
           K('pendulum', x0 + 2, 80, len=3, amp=35, period=2.6, phase=i * 0.15, skin=sk)]
r.kw['spawns'] = sp


# ============================================================ kit lint: every t:'kit' spawn in the rooms built so far
def kit_lint():
    errs = []
    for R in ROOMS:
        ks = [s for s in R.kw.get('spawns', []) if s.get('t') == 'kit']
        if not ks: continue
        ids = {}
        for s in ks:
            if s.get('id'):
                if s['id'] in ids: errs.append(f'{R.id}: kit duplicate id {s["id"]}')
                ids[s['id']] = s
        groups = {s.get('group') for s in ks if s.get('group')}
        for s in ks:
            k, x, y = s.get('kind'), s.get('x', -1), s.get('y', -1)
            tag = f'{R.id}: kit {k} at ({x},{y})'
            if k not in KIT_KINDS_PY: errs.append(f'{tag}: unknown kind'); continue
            for t in s.get('targets', []) + ([s['trigger']] if s.get('trigger') not in (None, 'stand', 'enter', 'zone') else []):
                if t not in ids: errs.append(f'{tag}: wired to unknown id {t}')
            if k == 'mover' and s.get('path') and any(not (0 <= px < R.w and 0 <= py < R.h) for px, py in s['path']): errs.append(f'{tag}: path leaves the room')
            if k == 'seq':
                if not s.get('group') or not s.get('order'): errs.append(f'{tag}: needs group and order')
                for m in s.get('order', []):
                    if m not in ids or ids[m].get('group') != s.get('group'): errs.append(f'{tag}: order id {m} is not a member of group {s.get("group")}')
            if k == 'level' and not s.get('states'): errs.append(f'{tag}: needs states')
            if k in ('bell', 'lantern', 'glyph', 'stop', 'frame', 'brazier') and s.get('group') and not s.get('id'): errs.append(f'{tag}: seq members need an id')
            if k in ('gate', 'level', 'seq', 'socket') and not s.get('id'): errs.append(f'{tag}: needs an id')
            if k == 'gate':
                h = s.get('h')
                yy = y
                n = 0
                while yy - n - 1 >= 0 and R.g[yy - n - 1][x] not in SOLID: n += 1
                if yy - n - 1 < 0: errs.append(f'{tag}: no ceiling above the gate (it could be jumped)')
                elif h and h < n + 1: errs.append(f'{tag}: h={h} stops short of the ceiling ({n + 1} rows) — it could be jumped')
    return errs


for _e in kit_lint():
    print('ERR', _e)
