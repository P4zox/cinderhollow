"""Static reachability check for the Necropolis (agent N): approximate platformer moves on the global tile grid.

Moves from a standing cell (feet cell = the air cell above ground): walk 1 sideways, fall (straight or drifting up to 4
cells sideways), jump up to 3 rows / 4 columns (clear arc approximated), one-way '=' is passable from below.
Bell walkways: state = (cell, phase); waiting flips the phase (on a walkway that vanishes you fall).
Water '"': swimmable (move 1 in any direction) only with tidebreath; otherwise solid for this check.
Usage: python3 tools/shots/n/reach.py
"""
import os, sys, importlib.util
from collections import deque

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
spec = importlib.util.spec_from_file_location('rooms', os.path.join(ROOT, 'tools', 'rooms.py'))
rooms = importlib.util.module_from_spec(spec)
_argv = sys.argv; sys.argv = ['rooms.py']
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(rooms)
sys.argv = _argv
MINE = [R for R in rooms.ROOMS if R.id.startswith('NV') or R.id == 'C2']
GRID = {}
for R in MINE:
    for y in range(R.h):
        for x in range(R.w):
            GRID[(R.gx + x, R.gy + y)] = (R.id, R.g[y][x])
GATES = {}
for R in MINE:
    for y in range(R.h):
        for x in range(R.w):
            if R.g[y][x] == 'G':
                for k in range(4):
                    GATES[(R.gx + x, R.gy + y + k)] = R.id


def ch(c):
    return GRID.get(c, (None, '#'))[1]


def solid(c, phase, opt):
    k = ch(c)
    if c in GATES and not opt.get('open_' + GATES[c]):
        return True
    if k in '#BY':
        return True
    if k == '{':
        return phase == 0
    if k == '}':
        return phase == 1
    if k == '"':
        return not opt.get('swim')
    return False


def ground(c, phase, opt):   # something to stand on below c
    b = (c[0], c[1] + 1)
    return solid(b, phase, opt) or ch(b) == '='


def clear(c, phase, opt):     # body fits (2 cells tall)
    return not solid(c, phase, opt) and not solid((c[0], c[1] - 1), phase, opt)


def water(c, opt):
    return opt.get('swim') and ch(c) == '"'


def fall(c, phase, opt, dx):
    x, y = c
    for i in range(1, 80):
        n = (x + (dx if i <= 1 else 0), y + i - 1)
        if solid(n, phase, opt) or ch(n) == '^':
            return None
        if water(n, opt):
            return n
        if ground(n, phase, opt) and i > 0:
            return n
    return None


def moves(c, phase, opt):
    out = []
    x, y = c
    if water(c, opt) or water((x, y + 1), opt):   # swimming
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + d[0], y + d[1])
            if not solid(n, phase, opt) and not solid((n[0], n[1] - 1), phase, opt) or water(n, opt):
                if not solid(n, phase, opt):
                    out.append(n)
        # climb out onto a ledge
        for dx in (-1, 1):
            for dy in (0, -1, -2):
                n = (x + dx, y + dy)
                if clear(n, phase, opt) and ground(n, phase, opt):
                    out.append(n)
        return out
    for dx in (-1, 1):
        n = (x + dx, y)
        if clear(n, phase, opt):
            if ground(n, phase, opt):
                out.append(n)
            else:
                f = fall(n, phase, opt, 0)
                if f: out.append(f)
    # drop through one-way
    if ch((x, y + 1)) == '=':
        f = fall((x, y + 1), phase, opt, 0)
        if f: out.append(f)
    # jumps
    for dy in range(1, 4):
        # rise straight up: every cell above must be passable (one-way ok)
        ok = all(not solid((x, y - k), phase, opt) and not solid((x, y - k - 1), phase, opt) for k in range(1, dy + 1))
        if not ok:
            break
        for dx in range(-4, 5):
            n = (x + dx, y - dy)
            if not clear(n, phase, opt) or not ground(n, phase, opt):
                continue
            step = 1 if dx > 0 else -1
            if all(clear((x + k * step, y - dy), phase, opt) for k in range(1, abs(dx) + 1)):
                out.append(n)
    # jump sideways and fall (gaps)
    for dx in range(-5, 6):
        if abs(dx) < 2:
            continue
        step = 1 if dx > 0 else -1
        top = y - 1
        if not all(clear((x + k * step, top), phase, opt) for k in range(0, abs(dx) + 1)):
            continue
        f = fall((x + dx, top), phase, opt, 0)
        if f: out.append(f)
    return out


def standing(c, phase, opt):
    return ch(c) != '^' and clear(c, phase, opt) and (ground(c, phase, opt) or water(c, opt))


def reach(starts, opt):
    seen = set()
    q = deque()
    for s in starts:
        for ph in (0, 1):
            if standing(s, ph, opt):
                seen.add((s, ph)); q.append((s, ph))
    while q:
        c, ph = q.popleft()
        nxt = [(n, ph) for n in moves(c, ph, opt) if ch(n) != '^']
        if c in PLAT:   # the bell-hung platform over NV4's second pit
            nxt.append((PLAT[c], 1 - ph))
        # wait for the bell: stay if the ground below survives the flip, else fall
        np_ = 1 - ph
        if standing(c, np_, opt):
            nxt.append((c, np_))
        elif not solid(c, np_, opt):
            f = fall(c, np_, opt, 0)
            if f: nxt.append((f, np_))
        for s in nxt:
            if s not in seen:
                seen.add(s); q.append(s)
    return {c for c, _ in seen}


def G(rid, x, y):
    R = next(R for R in MINE if R.id == rid)
    return (R.gx + x, R.gy + y)


C2 = G('C2', 40, 10)
PLAT = {G('NV4', 35, 16): G('NV4', 46, 16), G('NV4', 46, 16): G('NV4', 35, 16)}
TARGETS = {'NV1 east': G('NV1', 22, 21), 'NV2 shrine': G('NV2', 7, 10), 'NV3 top alcove': G('NV3', 17, 5),
           'NV3 bottom': G('NV3', 5, 41), 'NV4 chest': G('NV4', 29, 8), 'NV4 east': G('NV4', 66, 16), 'NV4 west': G('NV4', 3, 16),
           'NV4 lever': G('NV4', 65, 4), 'NV5 mid': G('NV5', 18, 10), 'NV6 shrine': G('NV6', 29, 14), 'NV6 gallery': G('NV6', 14, 7),
           'NV7 throne': G('NV7', 20, 12), 'NV1 item': G('NV1', 10, 21), 'NV2 item': G('NV2', 14, 7), 'C2': C2}
fails = 0
for label, opt in [('no tidebreath, gates shut', {}), ('tidebreath', {'swim': 1}),
                   ('both levers pulled, no tidebreath', {'open_NV1': 1, 'open_NV4': 1})]:
    fwd = reach([C2], opt)
    print(f'== {label}: from C2 reaches', ', '.join(f"{k}{'' if v in fwd else ' (NO)'}" for k, v in TARGETS.items()))
# every standable cell in my rooms can get back to C2 (with swim), and the platform pit (NV4) is ignored (dyn)
opt = {'swim': 1}
allc = [c for c, (rid, k) in GRID.items() if rid != 'C2' and any(standing(c, ph, opt) for ph in (0, 1))]
back_ok, bad = 0, []
target = C2
for c in allc:
    r = reach([c], opt)
    if target in r:
        back_ok += 1
    else:
        bad.append((GRID[c][0], c))
print(f'== return to C2 (tidebreath): {back_ok}/{len(allc)} standing cells ok')
from collections import Counter
cnt = Counter(b[0] for b in bad)
print('   stuck cells by room:', dict(cnt))
for rid in cnt:
    R = next(R for R in MINE if R.id == rid)
    print('   ', rid, sorted([(c[0] - R.gx, c[1] - R.gy) for r_, c in bad if r_ == rid])[:40])
