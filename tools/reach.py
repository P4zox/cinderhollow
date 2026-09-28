"""Build-time reachability checker (Expansion 3, agent KS).

For each room it flood-fills the player's reachable positions from every entrance with a frame-accurate port of the
player physics in web/src/04_player.js + 03_world.js (run, jump with hold/apex hang, gravity, the ledge assist and
ceiling corner nudge, coyote-free edges, air dash / Ember Dash, wall cling + wall jump, double jump, Moonstep's third
jump, Gale glide + updrafts, Root Hook swings, pogo off spikes, one-way platforms and drop-through). The numbers
MAXV / JUMP_V / GRAV_UP / GRAV_DN / FALL_MAX are read straight from 04_player.js, so tuning there flows through.

Search: nodes are standing cells, wall-cling spots and hook points. From each node a fixed set of maneuvers (input
programs) is simulated against the room grid; every landing / cling / hook in range becomes a new node. Maneuvers
whose free-flight envelope contains nothing new are skipped, so a room stops as soon as everything is found.

Checks (called from tools/rooms.py validation, results cached by room content in tools/.reach_cache.json):
  * every exit (edge opening into a neighbour, or a `door`), item `i`, chest `C`, trial goal, trial sigil,
    lore / bench / gauntlet marker must be reachable from some entrance
  * from every entrance there must be a way out again (no soft-locks)
Rooms with a `needs` kwarg (or x3=True) are checked with exactly those abilities -> ERR. Old rooms without `needs` are
checked leniently with every ability -> WARN only.

Kit objects (docs/KIT_API.md) count as their swept area: movers/lifts mark every cell their platform top passes
through as a one-way ledge; crumble/sinker/phase/spring/crate are ledges where they start; swings act as a hook point;
gates count as open (they are puzzle-gated, not movement-gated); hazards (pendulum, rising) are ignored.

CLI:  python3 tools/reach.py ROOMID [--needs talon,wings] [--show]   (ASCII map: S standing, * visited air, ! missed)
      python3 tools/reach.py --selftest                                (impossible / possible test layouts)
"""
import json, math, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TILE = 16
DT = 1 / 60
PW, PH = 10, 26
VERSION = 11          # bump to invalidate the cache when the model changes


def _consts():
    src = open(os.path.join(ROOT, 'web', 'src', '04_player.js')).read()
    m = re.search(r'const MAXV = ([\d.]+), JUMP_V = ([\d.]+), GRAV_UP = ([\d.]+), GRAV_DN = ([\d.]+), FALL_MAX = ([\d.]+)', src)
    if not m:
        return 122.0, 272.0, 640.0, 860.0, 430.0
    return tuple(float(v) for v in m.groups())


MAXV, JUMP_V, GRAV_UP, GRAV_DN, FALL_MAX = _consts()
WJ_VX, WJ_VY, WJ_LOCK = 175.0, 300.0, 0.15        # wallJump()
ROLL_V = 225.0                                   # doRoll(): air dash speed
ROLL_DASH, ROLL_TAIL, EMBER_DASH = 0.315, 0.115, 0.26   # roll anim: 7x45ms dashing + 55+60ms tail; ember_dash 260ms, all dashing
DJ_MUL, MOON_MUL = 0.9, 0.95                     # double jump / Moonstep
GLIDE_VX, GLIDE_VY, UPDRAFT_VY = 135.0, 42.0, -170.0
HOOK_RANGE = 130.0
POGO_V = 245.0
ALL_NEEDS = ['talon', 'wings', 'hook', 'emberdash', 'gale', 'slam', 'tidebreath', 'moonstep']

# cell codes
EMPTY, SOLID, PLAT, SPIKE_UP, SPIKE_DN, HAZ, WATER, UPDRAFT, VEIL, NOCLING, EXIT, SKY, STAR = range(13)
STAR_LOWG = 0.4   # 35_starfall.js SF_LOWG: starlight '+' cancels 40% of gravity, falls cap at 170 px/s
SOLIDISH = (SOLID, NOCLING)


def approach(v, t, d):
    return min(t, v + d) if v < t else max(t, v - d)


# ============================================================ grid
class Grid:
    """A room's cells as codes, plus what lies past each edge (exit into a neighbour, open sky, or wall)."""

    def __init__(self, R, cell_of, solid_chars, needs, hazard_chars='^v*(', kit=True):
        self.R, self.w, self.h = R, R.w, R.h
        self.pw, self.ph = R.w * TILE, R.h * TILE
        self.needs = set(needs)
        g = R.g
        T = bytearray(self.w * self.h)
        emberdash, slam = 'emberdash' in self.needs, 'slam' in self.needs
        for y in range(self.h):
            for x in range(self.w):
                ch = g[y][x]
                if ch == '=': c = PLAT
                elif ch == '^': c = SPIKE_UP
                elif ch == 'v': c = SPIKE_DN
                elif ch in 'B$': c = EMPTY                  # breakable by any strike
                elif ch == 'Y': c = EMPTY if slam else SOLID
                elif ch == '%': c = VEIL if not emberdash else EMPTY
                elif ch == '?': c = NOCLING
                elif ch == '+': c = STAR
                elif ch in hazard_chars: c = HAZ
                elif ch == '|': c = UPDRAFT
                elif ch == '"': c = WATER
                elif ch in solid_chars: c = SOLID
                else: c = EMPTY
                T[y * self.w + x] = c
        self.t = T
        # edges: per cell outside the room: EXIT (neighbour open), SKY (outdoor top), or SOLID
        E = cell_of if isinstance(cell_of, dict) else edge_codes(R, cell_of, solid_chars)
        self.left, self.right, self.top, self.bot = list(E['left']), list(E['right']), list(E['top']), list(E['bot'])
        for i in range(self.h):   # an edge cell that is itself solid can't be an exit
            if T[i * self.w] in SOLIDISH and self.left[i] == EXIT: self.left[i] = SOLID
            if T[i * self.w + self.w - 1] in SOLIDISH and self.right[i] == EXIT: self.right[i] = SOLID
        for i in range(self.w):
            if T[i] in SOLIDISH and self.top[i] == EXIT: self.top[i] = SOLID
            if T[(self.h - 1) * self.w + i] in SOLIDISH and self.bot[i] == EXIT: self.bot[i] = SOLID
        self.springs = []
        self.has_water = WATER in T
        self.has_star = STAR in T
        self.hooks = [(x * TILE + 8, y * TILE + 8) for y in range(self.h) for x in range(self.w) if g[y][x] == '@'] if 'hook' in self.needs else []
        if kit:
            self._kit(R)
        self._pad()

    def _pad(self):
        # a padded copy of every cell code (8 cells past each edge) so at() is one index; see at_slow for the rules
        pd = self.pad = 8; W2 = self.W2 = self.w + 2 * pd; H2 = self.h + 2 * pd
        self.PT = bytearray(W2 * H2)
        for ty in range(-pd, self.h + pd):
            for tx in range(-pd, self.w + pd):
                self.PT[(ty + pd) * W2 + tx + pd] = self.at_slow(tx, ty)

    def _kit(self, R):
        """KM kit objects (docs/KIT_API.md § Mechanics) as their swept area"""
        w = self.w
        self.springs = []
        def plat(x, y):
            if 0 <= x < w and 0 <= y < self.h and self.t[y * w + x] in (EMPTY, WATER, UPDRAFT, STAR):
                self.t[y * w + x] = PLAT
        DEFW = {'mover': 3, 'lift': 3, 'crumble': 2, 'sinker': 2, 'phase': 2}
        for s in R.kw.get('spawns', []):
            if s.get('t') != 'kit':
                continue
            k = s.get('kind'); sw = int(s.get('w', DEFW.get(k, 1)) or 1)
            if k in ('mover', 'lift'):
                if k == 'lift': pts = [(s['x'], s['y']), (s['x'], s.get('to', s['y'] - 6))]
                else: pts = [(int(p[0]), int(p[1])) for p in (s.get('path') or [])] or [(s['x'], s['y'])]
                segs = list(zip(pts, pts[1:] + ([pts[0]] if s.get('loop') and len(pts) > 2 else [])))
                for (x0, y0), (x1, y1) in segs or [(pts[0], pts[0])]:
                    n = max(abs(x1 - x0), abs(y1 - y0), 1)
                    for i in range(n + 1):
                        xx, yy = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
                        for dx in range(sw): plat(xx + dx, yy)
            elif k in ('crumble', 'sinker', 'phase'):
                for dx in range(sw): plat(s['x'] + dx, s['y'])
            elif k == 'crate':
                plat(s['x'], s['y'])
            elif k == 'spring':
                self.springs.append((s['x'], s['y'], float(s.get('power', 520))))
            elif k == 'swing':   # grabbed by touch, no Root Hook needed: a grab point at the rope's middle
                self.hooks.append((s['x'] * TILE + 8, s['y'] * TILE + int(s.get('len', 5)) * 8))
            elif k == 'wind' and s.get('vy', 0) <= -150:   # a strong updraft carries you: ride it like a lift
                for yy in range(s['y'], s['y'] + int(s.get('h', 4))):
                    for xx in range(s['x'], s['x'] + int(s.get('w', 4))): plat(xx, yy)
        for (x, y) in R.kw.get('reach_open', []):   # cells a region-specific mechanic opens (breakable walls, ink stairs…)
            if 0 <= x < w and 0 <= y < self.h: self.t[y * w + x] = EMPTY

    def at(self, tx, ty):
        pd = self.pad
        if -pd <= tx < self.w + pd and -pd <= ty < self.h + pd:
            return self.PT[(ty + pd) * self.W2 + tx + pd]
        return self.at_slow(tx, ty)

    def at_slow(self, tx, ty):
        if 0 <= tx < self.w and 0 <= ty < self.h:
            return self.t[ty * self.w + tx]
        if 0 <= ty < self.h: return self.left[ty] if tx < 0 else self.right[ty]
        if ty < 0:   # above the room: its own top edge, and for an outdoor room open sky beyond the corners too
            if 0 <= tx < self.w: return self.top[tx]
            return SKY if not self.R.kw.get('indoor') else SOLID
        if 0 <= tx < self.w: return self.bot[tx]
        return SOLID

    def solid(self, x, y, phasing=False):
        tx, ty, pd = int(x // TILE), int(y // TILE), self.pad
        c = self.PT[(ty + pd) * self.W2 + tx + pd] if -pd <= tx < self.w + pd and -pd <= ty < self.h + pd else self.at_slow(tx, ty)
        return c == SOLID or c == NOCLING or (c == VEIL and not phasing)


def edge_codes(R, cell_of, solid_chars):
    """what lies past each edge cell: EXIT (a neighbour's open cell), SKY (open sky over an outdoor room) or SOLID"""
    def outside(gx, gy):
        O, och = cell_of(gx, gy)
        if O is None:
            return SKY if gy < R.gy and not R.kw.get('indoor') else SOLID
        if och in solid_chars and och not in 'BY$':
            return SOLID
        return EXIT
    return {'left': [outside(R.gx - 1, R.gy + y) for y in range(R.h)], 'right': [outside(R.gx + R.w, R.gy + y) for y in range(R.h)],
            'top': [outside(R.gx + x, R.gy - 1) for x in range(R.w)], 'bot': [outside(R.gx + x, R.gy + R.h) for x in range(R.w)]}


# ============================================================ one simulated body (port of moveBody + the player's update)
class Body:
    __slots__ = ('x', 'y', 'vx', 'vy', 'ground', 'mode', 'aj', 'ms', 'adash', 'face', 'mt', 'lock', 'drop', 'dj', 'wall', 'jhold', 'phase')

    def __init__(self, x, y, vx=0.0, vy=0.0, ground=False, aj=0, ms=False, adash=True):
        self.x, self.y, self.vx, self.vy, self.ground = x, y, vx, vy, ground
        self.mode, self.aj, self.ms, self.adash, self.face = ('idle' if ground else 'air'), aj, ms, adash, 1
        self.mt = 0.0; self.lock = 0.0; self.drop = 0.0; self.dj = 0.0; self.wall = 0; self.jhold = True; self.phase = False


def move_body(b, G, dt):
    dx = b.vx * dt
    steps = int(math.ceil(abs(dx) / 6)) or 1
    ph = b.phase
    for _ in range(steps):
        nx = b.x + dx / steps
        side = nx + PW / 2 if dx > 0 else nx - PW / 2
        blocked = G.solid(side, b.y - 25, ph) or G.solid(side, b.y - 17, ph) or G.solid(side, b.y - 9, ph) or G.solid(side, b.y - 1, ph)
        if blocked and not b.ground and b.vy > -60:   # ledge assist
            low = not (G.solid(side, b.y - 25, ph) or G.solid(side, b.y - 21, ph) or G.solid(side, b.y - 17, ph) or G.solid(side, b.y - 13, ph) or G.solid(side, b.y - 9, ph))
            if low and not G.solid(side, b.y - 6, ph):
                top = math.floor((b.y - 1) / TILE) * TILE
                if b.y - top <= 6 and not G.solid(nx, top - PH + 1, ph):
                    b.y = top; b.vy = min(b.vy, 0); blocked = False
        if blocked:
            b.x = math.floor(side / TILE) * TILE - PW / 2 - 0.01 if dx > 0 else (math.floor(side / TILE) + 1) * TILE + PW / 2 + 0.01
            b.vx = 0
            break
        b.x = nx
    dy = b.vy * dt
    stepsY = int(math.ceil(abs(dy) / 6)) or 1
    b.ground = False
    for _ in range(stepsY):
        prevY, ny = b.y, b.y + dy / stepsY
        if dy >= 0:
            land = None
            for xx in (b.x - PW / 2 + 1, b.x, b.x + PW / 2 - 1):
                tx, ty = int(xx // TILE), int(ny // TILE)
                c = G.at(tx, ty); top = ty * TILE
                if c == SOLID or c == NOCLING or (c == VEIL and not ph): land = top if land is None else min(land, top)
                elif c == PLAT and not (b.drop > 0) and prevY <= top + 0.5: land = top if land is None else min(land, top)
            if land is not None:
                b.y = land; b.vy = 0; b.ground = True; break
            b.y = ny
        else:
            xs = (b.x - PW / 2 + 1, b.x, b.x + PW / 2 - 1)
            bonk = any(G.solid(xx, ny - PH, ph) for xx in xs)
            if bonk:   # corner correction
                for nudge in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5):
                    if not any(G.solid(xx + nudge, ny - PH, ph) or G.solid(xx + nudge, ny - PH / 2, ph) for xx in xs):
                        b.x += nudge; bonk = False; break
            if bonk:
                b.y = (math.floor((ny - PH) / TILE) + 1) * TILE + PH; b.vy = 0; break
            b.y = ny
    if not b.ground and b.vy >= 0 and dy == 0:
        for xx in (b.x - PW / 2 + 1, b.x + PW / 2 - 1):
            c = G.at(int(xx // TILE), int((b.y + 1) // TILE))
            if c in (SOLID, NOCLING) or (c == PLAT and abs(b.y - math.floor((b.y + 1) / TILE) * TILE) < 1):
                b.ground = True


def hazard_hit(b, G):
    x0, y0, x1, y1 = b.x - PW / 2 + 2, b.y - PH + 2, b.x + PW / 2 - 2, b.y - 1
    for ty in range(int(y0 // TILE), int(y1 // TILE) + 1):
        for tx in range(int(x0 // TILE), int(x1 // TILE) + 1):
            c = G.at(tx, ty)
            if c == SPIKE_UP and y1 > ty * TILE + 8: return True
            if c == SPIKE_DN and y0 < ty * TILE + 8: return True
            if c == HAZ: return True
    return False


def wall_at(b, G, d):
    x = b.x + PW / 2 + 1 if d > 0 else b.x - PW / 2 - 1
    y1, y2 = b.y - PH * 0.3, b.y - PH * 0.8
    c1, c2 = G.at(int(x // TILE), int(y1 // TILE)), G.at(int(x // TILE), int(y2 // TILE))
    return c1 == SOLID and c2 == SOLID          # star-glass (NOCLING) is too smooth to cling to


def in_updraft(b, G):
    tx = int(b.x // TILE)
    for ty in range(int((b.y - 10) // TILE), int((b.y + 30) // TILE) + 1):
        if G.at(tx, ty) == UPDRAFT: return True
    return False


def pogo_ready(b, G):
    y = b.y + 22
    for x in (b.x - 8, b.x - 2, b.x + 4, b.x + 8):
        if G.at(int(x // TILE), int(y // TILE)) == SPIKE_UP: return True
    return False


# ============================================================ maneuvers: tiny input programs
# program(frame, t, body, info) -> (ax, jump_held, jump_pressed, roll_pressed)
def prog(d, hold=True, dj=None, ms=None, dash=None, dash_d=None, glide=False, steer=None, walk=False):
    dash_d = d if dash_d is None else dash_d
    state = {'apex': None, 'dj_t': None, 'dash_done': False, 'ms_done': False}
    steers = steer if isinstance(steer, list) else ([steer] if steer else [])
    def f(i, t, b, info):
        ax = d
        for st in steers:
            if t >= st[0]: ax = st[1]
        jp = rp = False
        jh = hold if isinstance(hold, bool) else t < hold   # jump held (a body already rising keeps its height)
        if not walk and i == 0: jp = True
        if state['apex'] is None and b.vy >= 0 and t > 0.05: state['apex'] = t
        # double jump
        if dj is not None and b.aj > 0 and state['dj_t'] is None:
            fire = (dj == 'apex' and state['apex'] is not None) or (isinstance(dj, float) and t >= dj) or (dj == 'fall' and b.vy > 120)
            if fire: jp = True; jh = True; state['dj_t'] = t
        if ms and state['dj_t'] is not None and not state['ms_done'] and b.aj > 0 and b.vy >= 0 and t > state['dj_t'] + 0.1:
            jp = True; jh = True; state['ms_done'] = True
        if dash is not None and not state['dash_done'] and b.adash:
            fire = (dash == 'apex' and state['apex'] is not None) or (isinstance(dash, float) and t >= dash) or (dash == 'afterdj' and state['dj_t'] is not None and b.vy >= 0)
            if fire: rp = True; state['dash_done'] = True; ax = dash_d
        if glide and b.vy > 20: jh = True
        if dj is not None and state['dj_t'] is not None: jh = True
        return ax, jh, jp, rp
    f.long = bool(glide)
    return f


def maneuvers(needs, from_wall=False):
    """the input programs tried from a node. Each entry: (name, factory) with factory() -> fresh program."""
    wings, moon, gale, dash_ok = 'wings' in needs, 'moonstep' in needs, 'gale' in needs, True
    M = []
    for d in (1, -1):
        M.append(('jump', lambda d=d: prog(d)))
        M.append(('hop', lambda d=d: prog(d, hold=0.1)))
        M.append(('jump-stop', lambda d=d: prog(d, steer=(0.3, 0))))
        M.append(('jump-back', lambda d=d: prog(d, steer=(0.35, -d))))
        if dash_ok:
            M.append(('dash-apex', lambda d=d: prog(d, dash='apex')))
            M.append(('dash-early', lambda d=d: prog(d, dash=0.12)))
            M.append(('dash-late', lambda d=d: prog(d, dash=0.5)))
        if wings or moon:
            M.append(('dj-apex', lambda d=d: prog(d, dj='apex')))
            M.append(('dj-early', lambda d=d: prog(d, dj=0.2)))
            M.append(('dj-fall', lambda d=d: prog(d, dj='fall')))
            M.append(('dj-dash', lambda d=d: prog(d, dj='apex', dash='afterdj')))
            M.append(('dj-back', lambda d=d: prog(0, dj='apex', steer=(0.25, d))))
            if wings and moon:
                M.append(('triple', lambda d=d: prog(d, dj='apex', ms=True)))
                M.append(('triple-dash', lambda d=d: prog(d, dj='apex', ms=True, dash='afterdj')))
        if gale:
            M.append(('glide', lambda d=d: prog(d, glide=True)))
            M.append(('dash-glide', lambda d=d: prog(d, dash='apex', glide=True)))
            if wings or moon:
                M.append(('dj-glide', lambda d=d: prog(d, dj='apex', glide=True)))
    M.append(('up', lambda: prog(0)))
    if wings or moon:
        M.append(('up-dj', lambda: prog(0, dj='apex')))
        if wings and moon: M.append(('up-triple', lambda: prog(0, dj='apex', ms=True)))
    if gale:
        M.append(('up-glide', lambda: prog(0, glide=True)))
        for tt in (0.6, 1.2, 2.0, 3.0):   # ride an updraft, then drift out of it either way
            for d in (1, -1): M.append((f'up-glide-drift{tt}{d}', lambda tt=tt, d=d: prog(0, glide=True, steer=(tt, d))))
        for d in (1, -1): M.append(('glide-back', lambda d=d: prog(d, glide=True, steer=(0.8, -d))))
    return M


def walkoffs(needs):
    wings, moon, gale = 'wings' in needs, 'moonstep' in needs, 'gale' in needs
    M = []
    for d in (1, -1):
        M.append(('walkoff', lambda d=d: prog(d, walk=True)))
        M.append(('walkoff-stop', lambda d=d: prog(d, walk=True, steer=(0.12, 0))))
        M.append(('walkoff-back', lambda d=d: prog(d, walk=True, steer=(0.12, -d))))
        M.append(('walkoff-dash', lambda d=d: prog(d, walk=True, dash=0.1)))
        if wings or moon: M.append(('walkoff-dj', lambda d=d: prog(d, walk=True, dj=0.15)))
        if gale: M.append(('walkoff-glide', lambda d=d: prog(d, walk=True, glide=True)))
    return M


# ============================================================ simulate one maneuver from a body state
class Sim:
    def __init__(self, G, needs):
        self.G, self.needs = G, needs
        self.aj_max = (1 if 'wings' in needs else 0) + (1 if 'moonstep' in needs else 0)
        self.ember = 'emberdash' in needs

    def in_water(self, b):
        G = self.G
        return G.at(int(b.x // TILE), int((b.y - 3) // TILE)) == WATER or G.at(int(b.x // TILE), int((b.y - 20) // TILE)) == WATER

    def run(self, b, program, max_t=None, first_frame_ground_jump=True, from_wall=0):
        """returns dict(land=(x,y) or None, wall=(x,y,side,aj,dash) or None, exit=code, hooks=[...], pts=[(x,y)...], dead=bool)"""
        G, needs = self.G, self.needs
        out = {'land': None, 'wall': None, 'exit': None, 'hooks': [], 'pts': [], 'dead': False, 'water': None}
        if max_t is None: max_t = 8.0 if getattr(program, 'long', False) else 4.0   # glides can hang in the air a long time
        dry = not self.in_water(b)
        coy = 0.0
        t = 0.0; i = 0
        roll_t = -1.0; roll_dur = 0.0; roll_face = 1
        hooks_seen = set(); airborne = not b.ground
        while t < max_t:
            ax, jh, jp, rp = program(i, t, b, out)
            if b.lock > 0: ax_eff = 0
            else: ax_eff = ax
            # ---- action starts
            if b.mode in ('idle', 'air', 'wall', 'glide'):
                if rp and (b.ground or b.adash):
                    roll_face = ax_eff or b.face; b.face = roll_face; b.adash = b.ground and b.adash
                    if not b.ground: b.adash = False
                    b.mode = 'roll'; roll_t = 0.0; roll_dur = EMBER_DASH if self.ember else ROLL_DASH; b.vx = roll_face * ROLL_V
                elif jp:
                    if b.ground:
                        b.vy = -JUMP_V; b.ground = False; b.mode = 'air'
                    elif b.mode == 'wall':
                        d = b.wall or b.face
                        b.face = -d; b.vx = -d * WJ_VX; b.vy = -WJ_VY; b.lock = WJ_LOCK; b.wall = 0; b.adash = True; b.mode = 'air'
                    elif b.aj > 0:
                        b.aj -= 1
                        moon_jump = 'moonstep' in needs and b.aj == 0 and not b.ms
                        if moon_jump: b.ms = True
                        b.vy = -JUMP_V * (MOON_MUL if moon_jump else DJ_MUL); b.mode = 'air'; b.dj = 0.24
            # ---- per mode
            grav_apex = lambda: (not b.ground and b.mode == 'air' and abs(b.vy) < 55 and jh)
            if b.mode == 'roll':
                dashing = roll_t < roll_dur
                if dashing:
                    b.vx = roll_face * ROLL_V; b.vy = 0 if not b.ground or True else b.vy
                    b.phase = self.ember
                else:
                    b.phase = False
                    b.vx = approach(b.vx, ax_eff * MAXV, 900 * DT)
                    b.vy = min(b.vy + (GRAV_DN if b.vy > 0 else GRAV_UP) * DT, FALL_MAX)
                roll_t += DT
                if roll_t >= roll_dur + (0 if self.ember else ROLL_TAIL):
                    b.mode = 'air'; b.phase = False
            elif b.mode == 'wall':
                b.vy = min(b.vy + 600 * DT, 55); b.vx = b.wall * 10
                if not wall_at(b, G, b.wall) or (ax_eff and ax_eff != b.wall) or b.ground:
                    b.wall = 0; b.mode = 'air'
            elif b.mode == 'glide':
                up = in_updraft(b, G)
                b.vx = approach(b.vx, ax_eff * GLIDE_VX, 520 * DT)
                b.vy = approach(b.vy, UPDRAFT_VY if up else GLIDE_VY, (900 if up else 1100) * DT)
                if not jh or b.ground: b.mode = 'air'
                elif rp and b.adash:
                    pass
            else:   # air (and idle on the first frame)
                if b.lock <= 0:
                    b.vx = approach(b.vx, ax_eff * MAXV, (1400 if ax_eff and (ax_eff > 0) != (b.vx > 0) else 950) * DT)
                if not jh and b.vy < -90 and b.lock <= 0: b.vy = b.vy + (-90 - b.vy) * min(1, DT * 22)
                apex = grav_apex()
                b.vy = min(b.vy + (GRAV_DN if b.vy > 0 else GRAV_UP) * (0.55 if apex else 1) * DT, FALL_MAX)
                if 'talon' in needs and b.vy > 0 and ax_eff and wall_at(b, G, ax_eff):
                    b.wall = ax_eff; b.face = ax_eff; b.mode = 'wall'
                    out['wall'] = (b.x, b.y, ax_eff, b.aj, b.ms); return out
                if 'gale' in needs and jh and b.vy > 20 and b.dj <= 0 and b.mode == 'air':
                    b.mode = 'glide'
            if G.has_star and not b.ground and b.mode in ('air', 'idle') and G.at(int(b.x // TILE), int((b.y - 13) // TILE)) == STAR:
                b.vy -= (GRAV_UP if b.vy < 0 else GRAV_DN) * STAR_LOWG * DT   # starlight: gentler fall, higher leaps
                if b.vy > 170: b.vy = approach(b.vy, 170, 900 * DT)
            # pogo: a down-strike just before the spikes bounces you (refunds the air attack, restores dash/jump)
            if b.vy > 0 and b.mode in ('air', 'glide') and pogo_ready(b, G):
                b.vy = -POGO_V; b.adash = True; b.aj = max(b.aj, 1 if 'wings' in needs else 0); b.mode = 'air'
            b.lock -= DT; b.dj -= DT; b.drop -= DT
            move_body(b, G, DT)
            t += DT; i += 1
            # ---- where are we
            if b.x < 0 or b.x >= G.pw or b.y - 13 < 0 or b.y > G.ph + 4:
                tx, ty = int(b.x // TILE), int((b.y - 13) // TILE)
                if b.x < 0: code, key = G.left[min(max(ty, 0), G.h - 1)], ('W', min(max(ty, 0), G.h - 1))
                elif b.x >= G.pw: code, key = G.right[min(max(ty, 0), G.h - 1)], ('E', min(max(ty, 0), G.h - 1))
                elif b.y - 13 < 0: code, key = G.top[min(max(tx, 0), G.w - 1)], ('N', min(max(tx, 0), G.w - 1))
                else: code, key = G.bot[min(max(tx, 0), G.w - 1)], ('S', min(max(tx, 0), G.w - 1))
                if code == EXIT:
                    out['exit'] = key; return out
                if code == SOLID and b.y > G.ph + 4:
                    out['dead'] = True; return out
                if code == SOLID:   # the engine clamps you back in
                    b.x = min(max(b.x, 6), G.pw - 6)
                    if b.y - 13 < 0 and G.R.kw.get('indoor'): b.y = 30
            if hazard_hit(b, G):
                out['dead'] = True; return out
            if G.has_water:   # into deep water: the swim model takes over (a water node)
                wet = self.in_water(b)
                if wet and dry:
                    tx = int(b.x // TILE); ty = int((b.y - 20) // TILE)
                    if G.at(tx, ty) != WATER: ty = int((b.y - 3) // TILE)
                    out['water'] = (tx, ty); out['pts'].append((b.x, b.y)); return out
                if not wet: dry = True
            if i % 2 == 0: out['pts'].append((b.x, b.y))
            if G.hooks and b.mode != 'roll':
                for hi, (hx, hy) in enumerate(G.hooks):
                    if hi in hooks_seen: continue
                    dx, dy = hx - b.x, hy - (b.y - 20)
                    if dy > 30 or dx * dx + dy * dy > HOOK_RANGE * HOOK_RANGE: continue
                    if los(G, b.x, b.y - 22, hx, hy + 6):
                        hooks_seen.add(hi); out['hooks'].append((hi, b.x, b.y, b.aj, b.ms))
            if not b.ground: airborne = True
            elif airborne:
                out['land'] = (b.x, b.y, b.aj, b.ms); return out
        return out


def los(G, x0, y0, x1, y1):
    n = int(math.ceil(math.hypot(x1 - x0, y1 - y0) / 8))
    for k in range(1, n):
        if G.solid(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n): return False
    return True


# ============================================================ the search
def standable(G, tx, ty):
    """can the player stand with feet on the top of row ty+1, body in cells ty and ty-1?"""
    if not (0 <= tx < G.w and 0 <= ty < G.h): return False
    c, above, below = G.at(tx, ty), G.at(tx, ty - 1), G.at(tx, ty + 1)
    body_ok = c in (EMPTY, WATER, UPDRAFT, PLAT, STAR) and above in (EMPTY, WATER, UPDRAFT, PLAT, SKY, EXIT, STAR)
    return body_ok and below in (SOLID, NOCLING, PLAT)


def spans(G):
    """contiguous runs of standable cells per row: list of (row, x0, x1)"""
    out = []
    for ty in range(G.h):
        x = 0
        while x < G.w:
            if standable(G, x, ty):
                x0 = x
                while x + 1 < G.w and standable(G, x + 1, ty): x += 1
                out.append((ty, x0, x))
            x += 1
    return out


class Reach:
    def __init__(self, G, needs):
        self.G, self.needs = G, set(needs)
        self.sim = Sim(G, self.needs)
        self.span_of = {}
        self.spans = spans(G)
        for si, (ty, x0, x1) in enumerate(self.spans):
            for x in range(x0, x1 + 1): self.span_of[(x, ty)] = si
        self.aj_max = self.sim.aj_max
        self.man = maneuvers(self.needs); self.walk = walkoffs(self.needs)
        self.env = {}   # maneuver name -> relative bbox in free space (for pruning)
        # cells beside a clingable wall (open body cells, solid on one side): wall-jump shafts have no standing cells
        self.cling = set()
        if 'talon' in self.needs:
            for y in range(1, G.h):
                for x in range(G.w):
                    if G.at(x, y) in (SOLID, NOCLING, VEIL) or G.at(x, y - 1) in (SOLID, NOCLING): continue
                    if (G.at(x - 1, y) == SOLID and G.at(x - 1, y - 1) == SOLID) or (G.at(x + 1, y) == SOLID and G.at(x + 1, y - 1) == SOLID):
                        if (x, y) not in self.span_of: self.cling.add((x, y))
        self.has_updraft = UPDRAFT in G.t
        self.waters_all = [(x, y) for y in range(G.h) for x in range(G.w) if G.at(x, y) == WATER]

    def envelope(self, name, fac):
        if name in self.env: return self.env[name]
        E = Grid.__new__(Grid)   # an empty 200x200 box: free-flight extent of the maneuver
        E.w = E.h = 200; E.pw = E.ph = 200 * TILE; E.t = bytearray(200 * 200); E.hooks = []; E.needs = self.needs
        E.left = E.right = [SOLID] * 200; E.top = E.bot = [SOLID] * 200
        for x in range(200): E.t[150 * 200 + x] = SOLID
        E.R = type('R', (), {'kw': {'indoor': True}})(); E.has_water = False; E.has_star = False; E.springs = []
        E._pad()
        sim = Sim(E, self.needs)
        b = Body(100 * TILE + 8, 150 * TILE, MAXV * (1 if 'walk' not in name else 1), 0, True, self.aj_max, False, True)
        b.vx = 0
        o = sim.run(b, fac(), max_t=2.6)
        xs = [p[0] for p in o['pts']] or [b.x]; ys = [p[1] for p in o['pts']] or [b.y]
        r = ((min(xs) - 100 * TILE - 8) / TILE - 4, (max(xs) - 100 * TILE - 8) / TILE + 4, (min(ys) - 150 * TILE) / TILE - 2, 40)
        self.env[name] = r
        return r

    def search(self, seeds, targets_fn=None, stop_on_exit=False, budget=60000):
        """seeds: list of ('stand', tx, ty) | ('air', Body) | ('door', tx, ty). Returns the reach record."""
        G = self.G
        from collections import deque
        stand, walls, hooks, waters = {}, set(), set(), set()
        pts = set(); exits = set(); frontier = deque()   # FIFO: every seed is expanded before anything it leads to
        wallc = set()   # wall-cling cells visited (for pruning)
        def add_stand(tx, ty, aj=None):
            si = self.span_of.get((tx, ty))
            if si is None or si in stand: return
            stand[si] = True; frontier.append(('span', si))
            sty, a, b = self.spans[si]   # walking out along the floor counts at once (no budget can starve it)
            if a == 0 and G.left[sty] == EXIT: exits.add(('W', sty))
            if b == G.w - 1 and G.right[sty] == EXIT: exits.add(('E', sty))
        def add_water(tx, ty):
            rid = self.water_region(tx, ty)
            if rid is None or rid in waters: return
            waters.add(rid); frontier.append(('water', rid))
        def add_pts(P):
            for x, y in P: pts.add((int(x // 4), int(y // 4)))
        def land(o):
            if o['land']:
                x, y = o['land'][0], o['land'][1]
                tx, ty = int(x // TILE), int(round(y / TILE)) - 1
                if (tx, ty) not in self.span_of:   # standing past the edge on the next cell's support
                    for dx in (-1, 1):
                        if (int((x + dx * 4) // TILE), ty) in self.span_of: tx = int((x + dx * 4) // TILE); break
                add_stand(tx, ty)
            if o['wall']:
                x, y, side, aj, ms = o['wall']; k = (int(x // TILE), int(y // TILE), side, aj, ms)
                if k not in walls: walls.add(k); wallc.add((k[0], k[1])); frontier.append(('wall', k, x, y))
            for hk in o['hooks']:
                if hk[0] not in hooks: hooks.add(hk[0]); frontier.append(('hook', hk[0]))
            if o['exit']: exits.add(o['exit'])
            if o.get('water'): add_water(*o['water'])
            add_pts(o['pts'])
        self._tf = lambda x0, x1, y0, y1: targets_fn(x0, x1, y0, y1, stand, pts, exits, wallc) if targets_fn else True
        for s in seeds:
            if s[0] in ('stand', 'door'): add_stand(s[1], s[2])
            else:   # arriving in the air (a gap, a drop from above, a jump up through a floor): try the ways to steer it
                b = s[1]
                for f in self.air_progs(s[2]):
                    bb = Body(b.x, b.y, b.vx, b.vy, False, self.aj_max if b.aj < 0 else b.aj, b.ms, b.adash)
                    land(self.sim.run(bb, f))
        work = 0
        while frontier and work < budget:
            if stop_on_exit and exits: break
            if targets_fn is not None and not stop_on_exit and not targets_fn(-1e9, 1e9, -1e9, 1e9, stand, pts, exits, None): break
            node = frontier.popleft()
            if node[0] == 'water':
                for o in self.swim(node[1], exits, add_pts):
                    land(o); work += 1
            elif node[0] == 'span':
                ty, x0, x1 = self.spans[node[1]]
                add_pts([(x * TILE + 8, (ty + 1) * TILE) for x in range(x0, x1 + 1)])
                if G.hooks:
                    for x in range(x0, x1 + 1):
                        for hi, (hx, hy) in enumerate(G.hooks):
                            if hi in hooks: continue
                            bx, by = x * TILE + 8, (ty + 1) * TILE
                            if hy - (by - 20) <= 30 and math.hypot(hx - bx, hy - (by - 20)) <= HOOK_RANGE and los(G, bx, by - 22, hx, hy + 6):
                                hooks.add(hi); frontier.append(('hook', hi))
                starts = []
                for x in range(x0, x1 + 1):
                    starts.append((x * TILE + 8, 0))
                # run-ups toward each edge, and standing jumps
                for x in range(x0, x1 + 1):
                    for d in (1, -1):
                        room_behind = (x - x0 if d > 0 else x1 - x) >= 1
                        near_end = (x1 - x if d > 0 else x - x0) <= 1
                        if room_behind and near_end: starts.append((x * TILE + 8, d))
                starts.append((x1 * TILE + 8 + 3, 1)); starts.append((x0 * TILE + 8 - 3, -1))
                for (sx, sd) in starts:
                    for name, fac in self.man:
                        if sd and (('-' + str(sd)) and name.startswith('up')): continue
                        e = self.envelope(name, fac)
                        if not self._worth(sx, (ty + 1) * TILE, e, stand, name, fac, pts, exits, targets_fn): continue
                        f = fac()
                        dd = self._dir(f)
                        if sd and dd != sd: continue
                        b = Body(sx, (ty + 1) * TILE, sd * MAXV if sd else 0, 0, True, self.aj_max, False, True)
                        land(self.sim.run(b, f)); work += 1
                # walking off either end, and dropping through a one-way floor
                for (sx, d) in ((x1 * TILE + 8 + 3, 1), (x0 * TILE + 8 - 3, -1)):
                    for name, fac in self.walk:
                        if (d > 0) != ('-1' not in name and True): pass
                        f = fac()
                        if self._dir(f) != d: continue
                        b = Body(sx, (ty + 1) * TILE, d * MAXV, 0, True, self.aj_max, False, True)
                        land(self.sim.run(b, f)); work += 1
                for (sx_, sy_, pw_) in getattr(G, 'springs', []):
                    if sy_ == ty and x0 <= sx_ <= x1:
                        for d in (1, 0, -1):
                            for f in (prog(d, walk=True, hold=True), prog(d, walk=True, dj='apex'), prog(d, walk=True, dash='apex')):
                                b = Body(sx_ * TILE + 8, (ty + 1) * TILE - 1, 0, -pw_, False, self.aj_max, False, True)
                                land(self.sim.run(b, f)); work += 1
                if G.at(x0, ty + 1) == PLAT or any(G.at(x, ty + 1) == PLAT for x in range(x0, x1 + 1)):
                    for x in range(x0, x1 + 1):
                        if G.at(x, ty + 1) != PLAT: continue
                        for d in (0, 1, -1):
                            b = Body(x * TILE + 8, (ty + 1) * TILE + 2, 0, 0, False, self.aj_max, False, True); b.drop = 0.25
                            land(self.sim.run(b, prog(d, walk=True))); work += 1
            elif node[0] == 'wall':
                (cx, cy, side, aj, ms), x, y = node[1], node[2], node[3]
                progs = []
                for post in (side, -side, 0):
                    progs.append(prog(post))
                    if aj > 0: progs.append(prog(post, dj='apex'))
                    progs.append(prog(post, dash='apex', dash_d=-side))
                    if 'gale' in self.needs: progs.append(prog(post, glide=True))
                for tt in (0.2, 0.3, 0.4):   # leap off, then steer back in or hang in the middle
                    progs.append(prog(-side, steer=(tt, 0))); progs.append(prog(-side, steer=(tt, side)))
                for f in progs:
                    b = Body(x, y, 0, 30, False, aj, ms, True); b.mode = 'wall'; b.wall = side
                    land(self.sim.run(b, f)); work += 1
                # just let go / slide down
                b = Body(x, y, 0, 30, False, aj, ms, True); b.mode = 'wall'; b.wall = side
                land(self.sim.run(b, prog(side, walk=True, hold=False))); work += 1
            elif node[0] == 'hook':
                for o in self.swing(node[1]):
                    land(o); work += 1
        self.work = work
        return {'stand': stand, 'pts': pts, 'exits': exits, 'walls': walls, 'hooks': hooks, 'waters': waters}

    def air_progs(self, d):
        """steering programs for a body already in the air (no jump press; jump held so a rising body keeps its height)"""
        P_ = []
        for dd in ((d, 0, -d) if d else (1, 0, -1)):
            P_.append(prog(dd, walk=True, hold=True))
            if self.aj_max: P_.append(prog(dd, walk=True, hold=True, dj='apex'))
            P_.append(prog(dd, walk=True, hold=True, dash='apex'))
            if 'gale' in self.needs: P_.append(prog(dd, walk=True, glide=True))
            if 'talon' in self.needs: P_.append(prog(dd, walk=True, hold=True, steer=(0.25, -dd)))
        return P_

    # ---- deep water ('"', the Barrows): with tidebreath swim anywhere in the body; without, float and paddle on the surface
    def water_region(self, tx, ty):
        G = self.G
        if not hasattr(self, '_wreg'): self._wreg, self._wcells = {}, []
        if G.at(tx, ty) != WATER:
            for dy in (1, -1, 2):
                if G.at(tx, ty + dy) == WATER: ty += dy; break
            else: return None
        if (tx, ty) in self._wreg: return self._wreg[(tx, ty)]
        tb = 'tidebreath' in self.needs
        if not tb:   # rise to the surface of this column first
            while G.at(tx, ty - 1) == WATER: ty -= 1
            if (tx, ty) in self._wreg: return self._wreg[(tx, ty)]
        rid = len(self._wcells); cells = []; st = [(tx, ty)]; seen = {(tx, ty)}
        while st:
            x, y = st.pop(); cells.append((x, y)); self._wreg[(x, y)] = rid
            nb = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if tb else ((x + 1, y), (x - 1, y))
            for q in nb:
                if q not in seen and 0 <= q[0] < G.w and 0 <= q[1] < G.h and G.at(*q) == WATER:
                    seen.add(q); st.append(q)
        self._wcells.append(cells)
        return rid

    def swim(self, rid, exits, add_pts):
        G = self.G; outs = []
        cells = self._wcells[rid]
        add_pts([(x * TILE + 8, (y + 1) * TILE - 4) for x, y in cells] + [(x * TILE + 8, y * TILE + 12) for x, y in cells])
        for x, y in cells:   # swimming (or paddling) out through an edge
            if x == 0 and G.left[y] == EXIT: exits.add(('W', y))
            if x == G.w - 1 and G.right[y] == EXIT: exits.add(('E', y))
            if y == G.h - 1 and G.bot[x] == EXIT: exits.add(('S', x))
            if y == 0 and G.top[x] == EXIT: exits.add(('N', x))
        for x, y in cells:   # leap out of the surface: vy -300, as dbSwimUpdate does
            if G.at(x, y - 1) in (WATER, SOLID, NOCLING): continue
            for d in (1, 0, -1):
                for f in (prog(d, walk=True, hold=True), prog(d, walk=True, hold=True, dash='apex'), prog(d, walk=True, hold=True, dj='apex')):
                    b = Body(x * TILE + 8, y * TILE + 17, 0, -300, False, 0, False, True)
                    outs.append(self.sim.run(b, f))
        return outs

    @staticmethod
    def _dir(f):
        try: return f(0, 0, Body(0, 0, 0, 0, True), {})[0]
        except Exception: return 0

    def _worth(self, sx, sy, e, stand, name, fac, pts, exits, targets_fn):
        """prune: skip a maneuver whose free-flight box holds nothing unreached"""
        if targets_fn is None: return True
        if ('glide' in name and self.has_updraft) or self.G.has_star: return True   # updrafts/starlight carry you past the free-flight box   # an updraft carries a glide far past its free-flight box
        x0, x1, y0, y1 = sx / TILE + e[0], sx / TILE + e[1], sy / TILE + e[2], sy / TILE + e[3]
        if name.startswith('jump') or name.startswith('dash') or name.startswith('glide') or name.startswith('dj') or name.startswith('triple') or name.startswith('hop'):
            # direction-agnostic box (the program's d flips the x extent)
            w = max(abs(e[0]), abs(e[1])); x0, x1 = sx / TILE - w, sx / TILE + w
        return self._tf(x0, x1, y0, y1)

    def swing(self, hi):
        """Root Hook: zip to rope length, pump, release at many points of the arc (port of updateHook/releaseHook)."""
        G = self.G; hx, hy = G.hooks[hi]; outs = []
        for L in (46.0, 70.0, 94.0):
            for pump in (1, -1):
                ang, av = 0.0, 0.0
                for k in range(int(3.2 / DT)):
                    ax = pump if math.cos(ang) * av * pump >= -0.05 else -pump
                    av += (-(900 / L) * math.sin(ang) + ax * 3.2 * math.cos(ang)) * DT
                    av *= 0.8 ** DT; av = max(-4.2, min(4.2, av)); ang += av * DT
                    nx, ny = hx + math.sin(ang) * L, hy + math.cos(ang) * L + 34
                    if any(G.solid(xx, yy) for xx in (nx - 4, nx + 4) for yy in (ny - 2, ny - 13, ny - 24)):
                        av *= -0.3; ang -= av * DT * 2; continue
                    if k % 6 == 0:
                        tv = av * L
                        vx = max(-260, min(260, tv * math.cos(ang))); vy = min(-tv * math.sin(ang) * 0.9, 0) - 160
                        for d in (1, -1, 0):
                            b = Body(nx, ny, vx, vy, False, 1 if 'wings' in self.needs else 0, False, True)
                            f = prog(d, walk=True, hold=True)
                            outs.append(self.sim.run(b, lambda i, t, bb, o, f=f: (f(i, t, bb, o)[0], True, False, False)))
                        if 'wings' in self.needs or 'gale' in self.needs:
                            b = Body(nx, ny, vx, vy, False, 1 if 'wings' in self.needs else 0, False, True)
                            outs.append(self.sim.run(b, prog(1 if vx >= 0 else -1, walk=True, dj='apex' if 'wings' in self.needs else None, glide='gale' in self.needs)))
        return outs


# ============================================================ room-level checks
def room_targets(R, spawns_extra=()):
    """things that must be reachable: items/chests (map chars) and sys spawns. Each: (label, tx, ty, kind)"""
    T = []
    for y, row in enumerate(R.g):
        for x, ch in enumerate(row):
            if ch == 'i': T.append((f'item at ({x},{y})', x, y, 'touch'))
            elif ch == 'C': T.append((f'chest at ({x},{y})', x, y, 'stand'))
    for s in R.kw.get('spawns', []):
        if s.get('t') != 'sys': continue
        k = s.get('kind')
        if k == 'trial_goal': T.append((f'trial goal {s.get("trial")} at ({s["x"]},{s["y"]})', s['x'], s['y'], 'touch'))
        elif k in ('trial', 'bench', 'lore', 'gauntlet', 'door'):
            T.append((f'{k} {s.get("id") or s.get("page") or ""} at ({s["x"]},{s["y"]})'.replace('  ', ' '), s['x'], s['y'], 'stand' if not s.get('auto') else 'touch'))
    return T


def target_met(res, R_, tx, ty, kind, reach):
    if kind == 'stand':
        for si in res['stand']:
            sty, x0, x1 = reach.spans[si]
            if abs(sty - ty) <= 1 and x0 - 1 <= tx <= x1 + 1: return True
        return False
    # touch: item pickup box |dx| < 12, |dy| < 20 around (cx, fy - 4)
    cx, cy = tx * TILE + 8, (ty + 1) * TILE - 4
    for qx in range(int((cx - 12) // 4), int((cx + 12) // 4) + 1):
        for qy in range(int((cy - 20) // 4), int((cy + 20) // 4) + 1):
            if (qx, qy) in res['pts']: return True
    return False


def entrances(G, R):
    """entrance seeds: open edge runs (side/top/bottom) and doors. Returns list of (label, seeds)."""
    E = []
    def runs(arr):
        out, i = [], 0
        while i < len(arr):
            if arr[i] == EXIT:
                j = i
                while j + 1 < len(arr) and arr[j + 1] == EXIT: j += 1
                out.append((i, j)); i = j
            i += 1
        return out
    for side, arr in (('W', G.left), ('E', G.right)):
        for a, b in runs(arr):
            seeds = []
            x = 0 if side == 'W' else G.w - 1
            d = 1 if side == 'W' else -1
            for y in range(a, b + 1):
                if standable(G, x, y): seeds.append(('stand', x, y))
            if not seeds:   # arriving mid-air (a shaft or a ledge-less opening): fall in from the lowest open cell
                for y in range(b, a - 1, -1):
                    if G.at(x, y) not in SOLIDISH and G.at(x, y - 1) not in SOLIDISH:
                        seeds.append(('air', Body(x * TILE + 8 - d * 2, (y + 1) * TILE - 1, d * MAXV, 0, False, -1, False, True), d)); break
            if seeds: E.append((f'{side} edge rows {a}-{b}', seeds, (side, a, b)))
    for side, arr in (('N', G.top), ('S', G.bot)):
        for a, b in runs(arr):
            seeds = []
            for x in range(a, b + 1, 2):
                if side == 'N': seeds.append(('air', Body(x * TILE + 8, 28, 0, 40, False, -1, False, True), 0))
                else:   # coming up through a floor opening: at least 260 px/s upward (checkRoomExit), jump held, the air jump unspent
                    for vy in (-260, -JUMP_V) + ((-WJ_VY,) if 'talon' in G.needs else ()):   # a fresh jump at the boundary at best; a wall jump with the talon
                        seeds.append(('air', Body(x * TILE + 8, G.ph - 1, 0, vy, False, -1, False, True), 0))
            E.append((f'{side} edge cols {a}-{b}', seeds, (side, a, b)))
    for s in R.kw.get('spawns', []):
        if s.get('t') == 'sys' and s.get('kind') == 'door':
            E.append((f'door {s.get("id")}', [('door', s['x'], s['y'])], ('D', s.get('id'), s.get('id'))))
    return E


def exit_groups(G, R):
    """exits to reach: each open edge run (any cell of it), plus doors"""
    X = [e for e in entrances(G, R)]
    return X


def check_room(R, cell_of, solid_chars, hazard_chars='^v*(', cache=None):
    """returns list of (level, message). level 'ERR' for rooms with needs/x3, 'WARN' for old rooms.
    cell_of: tools/rooms.py cell(gx, gy), or a precomputed edge_codes() dict."""
    strict = 'needs' in R.kw or R.kw.get('x3')
    needs = [n for n in (R.kw.get('needs') or []) if n != 'start'] if strict else list(ALL_NEEDS)
    lvl = 'ERR' if strict else 'WARN'
    edges = cell_of if isinstance(cell_of, dict) else edge_codes(R, cell_of, solid_chars)
    h = room_hash(R, edges, needs, solid_chars, hazard_chars)
    if cache is not None and R.id in cache and cache[R.id].get('h') == h:
        return [tuple(m) for m in cache[R.id]['msgs']]
    G = Grid(R, edges, solid_chars, needs, hazard_chars)
    reach = Reach(G, needs)
    ents = entrances(G, R)
    msgs = []
    if R.kw.get('reach_ignore'):
        pass
    elif not ents:
        if not R.kw.get('test'): msgs.append((lvl, f'{R.id}: reach: no entrance found'))
    else:
        tg = room_targets(R)
        allseeds = [s for _, seeds, _ in ents for s in seeds]
        exit_keys = []
        for label, seeds, info in ents:
            side = info[0]
            if side == 'D': exit_keys.append((label, ('D', info[1])))
            else: exit_keys.append((label, (side, info[1], info[2])))
        def exit_hit(res, ek):
            if ek[0] == 'D': return None
            side, a, b = ek
            if any(e[0] == side and a <= e[1] <= b for e in res['exits']): return True
            return False
        # targets for pruning: unreached spans, targets, exits
        def make_targets(rc):
            done = set()
            def fn(x0, x1, y0, y1, stand, pts, exits, wallc):
                if wallc is not None and rc.cling:   # an unvisited wall-jump surface in reach: a shaft may lead on
                    for (cx, cy) in rc.cling:
                        if (cx, cy) not in wallc and x0 <= cx <= x1 and y0 <= cy <= y1: return True
                if wallc is not None and rc.waters_all and x0 <= max(c[0] for c in rc.waters_all) and min(c[0] for c in rc.waters_all) <= x1: return True
                for si, (ty, a, b) in enumerate(rc.spans):
                    if si in stand: continue
                    if b >= x0 and a <= x1 and y0 <= ty <= y1: return True
                for k, (label, tx, ty, kind) in enumerate(tg):
                    if k in done or not (x0 <= tx <= x1 and y0 <= ty <= y1): continue
                    if target_met({'stand': stand, 'pts': pts}, R, tx, ty, kind, rc): done.add(k); continue
                    return True
                for label, ek in exit_keys:
                    if ek[0] == 'D': continue
                    side, a, b = ek
                    if any(e[0] == side and a <= e[1] <= b for e in exits): continue
                    if side in 'WE':
                        ex = 0 if side == 'W' else G.w - 1
                        if x0 <= ex <= x1 and not (b < y0 or a > y1): return True
                    else:
                        ey = 0 if side == 'N' else G.h - 1
                        if y0 - 2 <= ey <= y1 + 2 and not (b < x0 or a > x1): return True
                return False
            return fn
        res = reach.search(allseeds, make_targets(reach))
        for label, tx, ty, kind in tg:
            if not target_met(res, R, tx, ty, kind, reach):
                msgs.append((lvl, f'{R.id}: reach: {label} is unreachable' + (f' with needs {needs}' if strict else ' even with every ability')))
        for label, ek in exit_keys:
            if ek[0] == 'D': continue
            if not exit_hit(res, ek):
                # doors-only rooms: an edge exit might be purely an entrance (a one-way drop in); only flag if it's a side exit
                msgs.append((lvl, f'{R.id}: reach: exit {label} can\'t be reached from any entrance'))
        # soft-lock: from each entrance, can you get out again (any exit, incl. walking back / a door)?
        doors = [s for s in R.kw.get('spawns', []) if s.get('t') == 'sys' and s.get('kind') == 'door']
        if R.kw.get('world_link') or R.kw.get('reach_both_ways'):   # a connector must work in both directions: every exit from every entrance
            for label, seeds, info in ents:
                r3 = Reach(G, needs); r3.env = reach.env
                res3 = r3.search(seeds, make_targets(r3))
                for l2, ek in exit_keys:
                    if ek[0] == 'D' or l2 == label: continue
                    if not exit_hit(res3, ek): msgs.append((lvl, f"{R.id}: reach: entering by {label}, exit {l2} can't be reached"))
        for label, seeds, info in ents:
            r2 = Reach(G, needs); r2.env = reach.env
            res2 = r2.search(seeds, make_targets(r2), stop_on_exit=True)
            ok = bool(res2['exits']) or any(target_met(res2, R, d['x'], d['y'], 'stand' if not d.get('auto') else 'touch', r2) for d in doors)
            if not ok:
                msgs.append((lvl, f'{R.id}: reach: entering by {label} there is no way out again'))
    if cache is not None:
        cache[R.id] = {'h': h, 'msgs': msgs}
    return msgs


def room_hash(R, edges, needs, solid_chars, hazard_chars):
    return hashlib.sha1(json.dumps([VERSION, R.rows(), sorted(needs), R.kw.get('spawns', []), bool(R.kw.get('indoor')), edges,
                                    sorted(solid_chars), sorted(hazard_chars)], sort_keys=True, default=str).encode()).hexdigest()


def _work(args):
    R, edges, solid, haz = args
    try:
        return R.id, check_room(R, edges, solid, haz)
    except Exception as e:   # a checker bug must never break the build
        return R.id, [('WARN', f'{R.id}: reach: checker failed ({e!r})')]


CACHE_PATH = os.path.join(HERE, '.reach_cache.json')


def check_all(rooms, cell_of, solid_chars, hazard_chars='^v*(', jobs=None):
    """every room, cached by content (+ what lies past its edges), uncached ones in parallel. Returns [(level, msg)]."""
    try: cache = json.load(open(CACHE_PATH))
    except Exception: cache = {}
    if cache.get('_v') != VERSION: cache = {'_v': VERSION}
    todo, out = [], {}
    for R in rooms:
        strict = 'needs' in R.kw or R.kw.get('x3')
        needs = [n for n in (R.kw.get('needs') or []) if n != 'start'] if strict else list(ALL_NEEDS)
        e = edge_codes(R, cell_of, solid_chars)
        h = room_hash(R, e, needs, solid_chars, hazard_chars)
        if R.id in cache and cache[R.id].get('h') == h: out[R.id] = [tuple(m) for m in cache[R.id]['msgs']]
        else: todo.append((R, e, set(solid_chars), hazard_chars, h))
    if todo:
        args = [(R, e, so, hz) for R, e, so, hz, _ in todo]
        res = None
        if len(todo) > 2 and (jobs or os.cpu_count() or 1) > 1:
            try:
                import multiprocessing as mp
                with mp.get_context('fork').Pool(min(len(todo), jobs or os.cpu_count() or 2)) as pool:
                    res = pool.map(_work, args, chunksize=1)
            except Exception:
                res = None
        if res is None: res = [_work(a) for a in args]
        hs = {R.id: h for R, _, _, _, h in todo}
        for rid, msgs in res:
            out[rid] = msgs; cache[rid] = {'h': hs[rid], 'msgs': msgs}
        try:   # merge with whatever other builds wrote meanwhile, then replace atomically
            try: disk = json.load(open(CACHE_PATH))
            except Exception: disk = {}
            if disk.get('_v') == VERSION:
                for k, v in disk.items():
                    if k not in hs: cache.setdefault(k, v)
            tmp = CACHE_PATH + f'.tmp{os.getpid()}'
            json.dump(cache, open(tmp, 'w')); os.replace(tmp, CACHE_PATH)
        except Exception:
            pass
    return [m for R in rooms for m in out.get(R.id, [])]


# ============================================================ placement helper
# Expansion 3 zones (docs/EXPANSION3_CONTRACT.md §7.2): (x0, x1, y0, y1), inclusive global tile bounds
ZONES = {
    'Ramparts': (-112, 15, -90, -1), 'Catacombs': (-330, -113, 43, 112), 'Cathedral': (372, 491, -160, -15), 'Mire': (150, 227, 99, 180),
    'Archives': (250, 371, -160, -61), 'Hoarfrost': (150, 249, -160, -39), 'Spire': (-112, 149, -220, -91), 'Deep': (228, 399, 135, 260),
    'Crown': (565, 760, -13, 39), 'Thornveil': (-330, -141, -120, 42), 'Barrows': (585, 760, 84, 220), 'Crimson': (453, 564, 41, 83),
    'Necropolis': (-112, 149, 113, 260), 'Dunes': (400, 584, 147, 260), 'Starfall': (492, 760, -220, -93), 'NeoHallow': (1000, 1400, -150, 150),
    'Ember': (565, 760, 40, 83), 'Hermit': (-140, -41, 0, 14),
}
TEST_ROOMS = {'T0': (-200, 0, 48, 20), 'T1': (-400, 0, 100, 100), 'T2': (-300, 0, 96, 30), 'T2b': (-520, 0, 28, 14)}   # kept clear even before they exist

def free_spot(rooms, near_gx, near_gy, w, h, zone, margin=0):
    """nearest free w x h rectangle (top-left global tile coords) inside zone=(x0, x1, y0, y1) (inclusive bounds) that
    overlaps no room (keeping `margin` tiles clear). Searches outward from (near_gx, near_gy). Returns (gx, gy) or None."""
    x0, x1, y0, y1 = ZONES[zone] if isinstance(zone, str) else zone
    occ = [(R.gx - margin, R.gy - margin, R.gx + R.w + margin, R.gy + R.h + margin) for R in rooms]
    have = {R.id for R in rooms}   # test rooms defined later in file order still count
    occ += [(gx - margin, gy - margin, gx + w_ + margin, gy + h_ + margin) for rid, (gx, gy, w_, h_) in TEST_ROOMS.items() if rid not in have]
    def free(gx, gy):
        if gx < x0 or gy < y0 or gx + w - 1 > x1 or gy + h - 1 > y1: return False
        for a, b, c, d in occ:
            if gx < c and gx + w > a and gy < d and gy + h > b: return False
        return True
    best = None
    for r in range(0, max(x1 - x0, y1 - y0) + 2):
        for gx in range(near_gx - r, near_gx + r + 1):
            for gy in (near_gy - r, near_gy + r) if r else (near_gy,):
                if free(gx, gy): return (gx, gy)
        for gy in range(near_gy - r + 1, near_gy + r):
            for gx in (near_gx - r, near_gx + r):
                if free(gx, gy): return (gx, gy)
    return best


def zones_report(rooms, zones):
    """free space per zone: coarse occupancy map (1 char = 4x4 tiles) + the largest free rectangles."""
    lines = []
    for name, (x0, x1, y0, y1) in zones.items():
        lines.append(f'== {name}: x {x0}..{x1}, y {y0}..{y1}')
        for gy in range(y0, y1 + 1, 4):
            row = ''
            for gx in range(x0, x1 + 1, 4):
                hit = any(R.gx < gx + 4 and R.gx + R.w > gx and R.gy < gy + 4 and R.gy + R.h > gy for R in rooms)
                row += '#' if hit else '.'
            lines.append('  ' + row)
        for (w, h) in ((48, 14), (24, 28), (64, 16), (96, 32)):
            p = free_spot(rooms, (x0 + x1) // 2, (y0 + y1) // 2, w, h, (x0, x1, y0, y1))
            lines.append(f'  free {w}x{h}: {p}')
    return '\n'.join(lines)


# ============================================================ CLI / self-test
def _load_rooms():
    sys.argv_backup = sys.argv
    import importlib.util
    spec = importlib.util.spec_from_file_location('rooms_mod', os.path.join(HERE, 'rooms.py'))
    mod = importlib.util.module_from_spec(spec)
    saved = sys.argv; sys.argv = ['rooms.py', '--noop']
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = saved
    return mod


def show(R, G, res, reach):
    rows = []
    for y in range(G.h):
        s = ''
        for x in range(G.w):
            ch = R.g[y][x]
            si = reach.span_of.get((x, y))
            if si is not None and si in res['stand']: s += 'S'
            elif si is not None: s += '!'
            elif ch == '.' and any((qx // 4 == x and qy // 4 == y + 0) for qx, qy in ()): s += '*'
            else: s += ch
        rows.append(s)
    vis = {(qx * 4 // TILE, (qy * 4 - 1) // TILE) for qx, qy in res['pts']}
    rows = [''.join('*' if (c == '.' and (x, y) in vis) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    return '\n'.join(rows)


class _Room:   # a minimal stand-in for tools/rooms.py Room (self-test layouts)
    def __init__(self, id, rows, **kw):
        self.id, self.g, self.kw = id, [list(r) for r in rows], kw
        self.w, self.h, self.gx, self.gy = len(rows[0]), len(rows), 0, 0
    def rows(self): return [''.join(r) for r in self.g]


def selftest():
    """layouts with a known answer. Each: (name, rows, needs, expect_ok)"""
    solid = set('#')
    L = []
    base = lambda mid: ['#' * 24] + ['#' + r + '#' for r in mid] + ['#' * 24]
    # 1. a 3-tile ledge: fine. 2. a 4-tile ledge: too high without wings. 3. the same with wings: fine.
    def ledge(hgt):
        rows = ['.' * 22 for _ in range(12)]
        rows = [list(r) for r in rows]
        for y in range(12 - hgt, 12):
            for x in range(14, 22): rows[y][x] = '#'
        rows[12 - hgt - 1][18] = 'i'
        rows[11][2] = '.'
        return base([''.join(r) for r in rows])
    L.append(('3-tile ledge', ledge(3), [], True))
    L.append(('5-tile ledge', ledge(5), [], False))
    L.append(('5-tile ledge + wings', ledge(5), ['wings'], True))
    # 4. a gap: 6 tiles is jumpable (~91 px of flight), 11 is not, 11 with an air dash... still no; with gale yes
    def gap(n):
        nonlocal_floor = None
        rows = [['.'] * 22 for _ in range(12)]
        for x in range(22):
            if not (4 <= x < 4 + n): rows[11][x] = '#'
            else: rows[11][x] = floor
        rows[10][20] = 'i'
        return base([''.join(r) for r in rows])
    floor = '*'
    L.append(('5-tile lava gap', gap(5), [], True))
    L.append(('8-tile lava gap (jump ~7 + the base air dash)', gap(8), [], True))
    L.append(('12-tile lava gap', gap(12), [], False))
    L.append(('12-tile lava gap + wings', gap(12), ['wings'], True))
    L.append(('13-tile lava gap', gap(13), [], False))
    L.append(('13-tile lava gap + gale + wings', gap(13), ['gale', 'wings'], True))
    floor = '^'
    L.append(('13-tile spike floor: pogo across', gap(13), [], True))
    # 5. a tall shaft: impossible without the talon, possible with it
    def shaft():
        rows = [['.'] * 22 for _ in range(12)]
        for y in range(12):
            for x in range(0, 9): rows[y][x] = '#'
            for x in range(12, 22): rows[y][x] = '#'
        for x in range(9, 12): rows[11][x] = '#'
        for x in range(0, 9): rows[9][x] = rows[10][x] = '.'   # the corridor in from the entrance
        rows[0][10] = 'i'
        return base([''.join(r) for r in rows])
    L.append(('11-tile shaft', shaft(), [], False))
    L.append(('11-tile shaft + talon', shaft(), ['talon'], True))
    # 6. a hook point over a wide spike pit
    def hookpit():
        rows = [['.'] * 22 for _ in range(12)]
        for x in range(22): rows[11][x] = '#' if x < 3 or x > 18 else '^'
        rows[3][11] = '@'; rows[10][20] = 'i'
        return base([''.join(r) for r in rows])
    L.append(('hook pit, no hook', hookpit(), [], False))
    L.append(('hook pit + hook', hookpit(), ['hook'], True))
    # 7. pogo: a wide spike floor under a high goal ledge — bouncing on spikes gets you there
    # ---- Expansion 3 §8 fixes (each: rows, needs, expect, options)
    W = lambda rows: [r.replace(' ', '.') for r in rows]
    def pool(extra=''):   # deep water with a page on the bottom; ledges both sides
        rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(6)] + ['#.......""......#'] * 5 + ['#......."i"......#'.replace('""i"', '"i""'.replace('i', 'i'))] + ['#' * 24]
        rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(6)]
        rows += ['#' + '.' * 7 + '"' * 8 + '.' * 7 + '#'] * 1
        rows += ['#' + '#' * 7 + '"' * 8 + '#' * 7 + '#'] * 4
        rows += ['#' + '#' * 7 + '"' * 3 + 'i' + '"' * 4 + '#' * 7 + '#']
        rows += ['#' * 24]
        return rows
    L2 = []
    L2.append(('pool floor, no tidebreath (floats)', pool(), [], False, {'entry': [(-1, 7), (-1, 6)]}))
    L2.append(('pool floor + tidebreath (swims down)', pool(), ['tidebreath'], True, {'entry': [(-1, 7), (-1, 6)]}))
    def moat():   # 12 tiles of deep water between two ledges, far side has the page: paddle across the surface
        rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(8)]
        rows += ['#...' + '"' * 16 + '..i#']
        rows += ['####' + '"' * 16 + '####'] * 3 + ['#' * 24]
        return rows
    L2.append(('moat: paddle across the surface', moat(), [], True, {'entry': [(-1, 9), (-1, 8)]}))
    def over_wall(indoor):   # steps up to a ledge by a wall that reaches the top edge: outdoors you hop over it through the sky
        rows = ['#' + '.' * 9 + '#' + '.' * 12 + '#' for _ in range(11)]
        rows[8] = '#===' + rows[8][4:]
        rows[5] = '#....===' + rows[5][8:]
        rows[2] = '#.......===' + rows[2][11:]
        rows[10] = '#' + '.' * 9 + '#' + '.' * 10 + 'i.#'
        rows = [('#' * 24) if indoor else ('..........#.............')] + rows[1:] + ['#' * 24]
        return rows
    L2.append(('outdoor: over a wall through the sky', over_wall(False), [], True, {'indoor': False, 'entry': [(-1, 10), (-1, 9)]}))
    L2.append(('indoor: the same wall is a wall', over_wall(True), [], False, {'entry': [(-1, 10), (-1, 9)]}))
    def up_hole(gap):   # arriving up through a floor opening: the first ledge `gap` px above the bottom edge
        rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(12)] + ['#.....' + '#' * 17 + '#']
        ly = 13 - gap // 16
        rows[ly] = '#' + '....' + '======' + '.' * 12 + '#'
        rows[ly - 1] = '#' + '.' * 6 + 'C' + '.' * 15 + '#'   # a chest: you must stand on the ledge
        return rows
    L2.append(('up through a floor hole: ledge 3 tiles up', up_hole(48), [], True, {'entry': [(1, 14), (2, 14), (3, 14), (4, 14), (5, 14)]}))
    L2.append(('up through a floor hole: ledge 4 tiles up', up_hole(64), [], False, {'entry': [(1, 14), (2, 14), (3, 14), (4, 14), (5, 14)]}))
    L2.append(('up through a floor hole: 4 up + wings', up_hole(64), ['wings'], True, {'entry': [(1, 14), (2, 14), (3, 14), (4, 14), (5, 14)]}))
    def perch():   # a long glide from a high perch over 30 tiles of lava (> 2.6 s in the air)
        rows = ['#' * 48] + ['#' + '.' * 46 + '#' for _ in range(22)]
        rows[4] = '#' + '#' * 4 + '.' * 42 + '#'
        rows[22] = '#' + '.' * 44 + 'C.#'
        rows += ['#' * 5 + '*' * 38 + '#' * 5]
        return rows
    L2.append(('long glide from a high perch', perch(), ['gale'], True, {'entry': [(-1, 3), (-1, 2)]}))
    L2.append(('the same, no gale', perch(), [], False, {'entry': [(-1, 3), (-1, 2)]}))
    def draft():   # an updraft column to a ledge offset 4 tiles to the side (ride up, then drift out)
        rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(20)] + ['#' * 24]
        for y in range(3, 21): rows[y] = rows[y][:6] + '|' + rows[y][7:]
        rows[5] = '#' + '.' * 9 + '=====' + '.' * 8 + '#'
        rows[4] = '#' + '.' * 11 + 'i' + '.' * 10 + '#'
        return rows
    L2.append(('updraft, then drift to a side ledge', draft(), ['gale'], True, {'entry': [(-1, 20), (-1, 19)]}))
    def tall_shaft():   # a 30-tile wall-jump shaft with nothing to stand on until the top (pruning must not skip it)
        rows = ['#' * 24] + ['#' * 9 + '...' + '#' * 12 for _ in range(30)] + ['#' * 24]
        rows[29] = '.' * 12 + '#' * 12; rows[30] = '.' * 12 + '#' * 12
        rows[1] = '#' * 9 + '.i.' + '#' * 12
        return rows
    L2.append(('30-tile wall-jump shaft + talon', tall_shaft(), ['talon'], True, {'entry': [(-1, 30), (-1, 29)]}))
    ok_all = True
    cell_of = lambda gx, gy: (None, None)
    runs = [(n, r, nd, e, None) for n, r, nd, e in L] + L2
    for name, rows, needs, expect, opt in runs:
        opt = opt or {}
        R = _Room('ST', rows, needs=needs or ['start'], indoor=opt.get('indoor', True))
        if 'entry' in opt:
            ent = set(opt['entry'])
            for (ex, ey) in ent:   # open the wall cell next to each entrance cell
                if ex == -1: R.g[ey][0] = '.'
                elif ey == R.h: R.g[R.h - 1][ex] = '.'
            cof = lambda gx, gy, ent=ent: ((object(), '.') if (gx, gy) in ent else (None, None))
        else:
            # the left end of row 11 is the entrance: open the wall there
            R.g[11][0] = '.'; R.g[10][0] = '.'
            cof = lambda gx, gy: ((object(), '.') if gx == -1 and gy in (10, 11) else (None, None))
        msgs = check_room(R, cof, solid)
        errs = [m for m in msgs if 'item' in m[1] or 'chest' in m[1]]
        got = not errs
        flag = 'ok ' if got == expect else 'BAD'
        if got != expect: ok_all = False
        print(f'{flag} {name:38s} expect {"reachable" if expect else "unreachable":12s} got {"reachable" if got else "unreachable"}   {msgs[:1]}')
    # seed starvation: two entrances, no search budget at all: both edge exits must still be recorded from the seeds
    rows = ['#' * 24] + ['#' + '.' * 22 + '#' for _ in range(10)] + ['#' * 24]
    R = _Room('ST', rows, needs=['start'], indoor=True)
    for y in (9, 10): R.g[y][0] = '.'; R.g[y][23] = '.'
    ent = {(-1, 9), (-1, 10), (24, 9), (24, 10)}
    G = Grid(R, lambda gx, gy: ((object(), '.') if (gx, gy) in ent else (None, None)), solid, [])
    res = Reach(G, []).search([('stand', 0, 10), ('stand', 23, 10)], budget=0)
    got = ('W', 10) in res['exits'] and ('E', 10) in res['exits']
    print(f'{"ok " if got else "BAD"} seed exits recorded with budget 0            {sorted(res["exits"])}')
    return ok_all and got


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    mod = _load_rooms()
    rid = next((a for a in sys.argv[1:] if not a.startswith('--')), None)
    needs_arg = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--needs=')), None)
    R = mod.ROOM(rid)
    if needs_arg is not None: R.kw['needs'] = [n for n in needs_arg.split(',') if n]
    msgs = check_room(R, mod.cell, mod.SOLID, ''.join(sorted(getattr(mod, 'HAZARD', set('^v*(')))))
    for m in msgs: print(*m)
    if not msgs: print(f'{rid}: everything reachable')
    if '--show' in sys.argv:
        strict = 'needs' in R.kw or R.kw.get('x3')
        needs = [n for n in (R.kw.get('needs') or []) if n != 'start'] if strict else list(ALL_NEEDS)
        G = Grid(R, mod.cell, mod.SOLID, needs); rc = Reach(G, needs)
        res = rc.search([s for _, seeds, _ in entrances(G, R) for s in seeds])
        print(show(R, G, res, rc))
