#!/usr/bin/env python3
"""NEO-HALLOW tiles v2 (docs/v17/neohallow_upgrade.md): wet rooftop metal and concrete for the play layer.

  python3 art/gen_tiles_neohallow_v2.py [--no-ase]     -> assets/tiles_neohallow.png/.json, art/tiles_neohallow.aseprite

The 48-tile contract of 03_world.js is kept (same as art/gen_neo_env.py, which still builds tiles_neohallow_cyber):
  0-15  solid by exposed sides (bit 1 N, 2 E, 4 S, 8 W)      16-31 the same with a detail (28 % of solids, by hash)
  32-35 one-way platform L / M / R / single                   36-37 spikes up / down (the Glitch Run's data spikes)
  38-41 back walls (indoor rooms; random per cell)            42-45 decor (x r k b; unused in NH rooms)
  46    breakable                                             47    drawn on top of 30 % of exposed tops
Look: dark gunmetal cladding in big 16 x 8 panels (bevelled seams, rivets, rain streaks running down from the seams),
darkening into the mass away from the open sides so big blocks read as silhouettes; every roof edge is a wet steel lip
(a broken specular line) over a segmented cyan LED trim; the west face catches a cold rim, the east falls into shadow,
undersides carry dim magenta service lights. Details: vent grates, a lit slit window, a conduit, hazard chevrons, and
a vein of the fossil Pale Root the city is built on. Platforms are steel catwalk grating with an LED edge.
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import hexc  # noqa: E402

B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float)
MET = ['06060c', '09090f', '0c0c15', '10101b', '141522', '191b2a', '1f2233', '262a3e', '2f344b', '3b415b', '4a516e', '5e6684', '7a83a0', 'a2abc4', 'cdd4e4']
CY = ['0a2a3a', '0b4d66', '13a3c9', '3fe0ff', 'b8f6ff']
MG = ['2a0624', '4a0a3e', '6e0f5c', 'c21d97', 'ff3fc0']
AMB = ['3a2414', '6a4418', 'a86a24', 'e0a050']
FOS = ['2e2b30', '46424a', '6a6470', '908a94', 'b8b2bc']
N_, E_, S_, W_ = 1, 2, 4, 8


def h01(*a):
    v = 0
    for x in a: v = (v * 1103515245 + int(x) * 2654435761 + 12345) & 0xffffffff
    v ^= v >> 13; v = (v * 1274126177) & 0xffffffff; v ^= v >> 16
    return (v & 0xffff) / 65535


def M(v):
    return MET[int(np.clip(v, 0, 0.999) * len(MET))]


class T:
    def __init__(self):
        self.a = np.zeros((16, 16, 4), np.uint8)

    def put(self, x, y, c, k=1.0):
        if 0 <= x < 16 and 0 <= y < 16 and c is not None:
            col = hexc(c)
            if k >= 1 or self.a[y, x, 3] == 0: self.a[y, x] = [*col.astype(int), 255]
            else: self.a[y, x, :3] = (self.a[y, x, :3] * (1 - k) + col * k).astype(int); self.a[y, x, 3] = 255

    def rect(self, x, y, w, h, c, k=1.0):
        for yy in range(y, y + h):
            for xx in range(x, x + w): self.put(xx, yy, c, k)

    def img(self):
        return Image.fromarray(self.a)


def panel_v(x, y, seed):
    """Cladding value (0..1) at a 16 x 16 torus point: 16 x 8 panels, staggered joints, bevelled seams, rivets."""
    course = y // 8; oy = y % 8
    jx = 0 if course == 0 else 8
    ox = (x - jx) % 16
    v = 0.43 + 0.05 * (h01(x // 4, y // 3, 7) - 0.5)
    if oy == 7: v = 0.2                      # the seam (shadowed under the panel above)
    elif oy == 0: v = 0.55                   # its bevel catches the light
    if ox == 0 and oy != 7: v = 0.24         # vertical joint
    elif ox == 1 and oy not in (0, 7): v += 0.05
    if oy == 2 and ox in (3, 13): v = 0.62   # rivets
    if oy == 3 and ox in (3, 13): v = 0.26
    return v


def depth(mask, x, y):
    d = 9
    if mask & N_: d = min(d, y)
    if mask & S_: d = min(d, 15 - y)
    if mask & W_: d = min(d, x)
    if mask & E_: d = min(d, 15 - x)
    return d


def solid(mask, var=False, seed=0):
    t = T()
    streak = [(x, h01(seed, x, 3)) for x in range(16) if h01(seed, x, 5) < 0.14]      # rain streaks below the seams
    for y in range(16):
        for x in range(16):
            d = depth(mask, x, y)
            v = panel_v(x, y, seed)
            for sx, r in streak:
                if x == sx and (y % 8) in range(0, 3 + int(r * 4)) and (y % 8) != 7: v += 0.06
            v -= 0.045 * min(d, 7) - 0.05           # the mass falls into dark away from the open sides
            t.put(x, y, M(v * 0.92))
    if var: detail(t, mask, seed)
    if var or True:   # re-darken the details that sit deep in the mass
        for y in range(16):
            for x in range(16):
                d = depth(mask, x, y)
                if d >= 5: t.a[y, x, :3] = (t.a[y, x, :3] * (0.82 if d >= 7 else 0.9)).astype(np.uint8)
    # ---- the open sides
    if mask & N_:
        for x in range(16):
            r = h01(x, seed, 11)
            t.put(x, 0, MET[13] if r > 0.82 else MET[12] if r > 0.3 else MET[11])          # the wet steel lip: a broken specular line
            t.put(x, 1, MET[10] if r > 0.5 else MET[9])
            t.put(x, 2, MET[6])
            on = (x + seed) % 8 != 7 and h01(x // 4, seed, 13) > 0.1
            t.put(x, 3, (CY[3] if (x + seed) % 8 == 3 else CY[2]) if on else CY[0])       # the LED trim, segmented
            t.put(x, 4, MET[1])
            t.put(x, 5, MET[8] if x % 2 else MET[7])                                         # the cladding face under it: wet,
            t.put(x, 6, MET[7], 0.6)                                                          # a little lighter near the top
            if h01(x, seed, 17) > 0.9: t.put(x, 7, MET[8])                                   # a drip
    if mask & W_:
        for y in range(16):
            if mask & N_ and y < 5: continue
            t.put(0, y, MET[9] if y % 6 else MET[11]); t.put(1, y, MET[6], 0.5)
    if mask & E_:
        for y in range(16):
            if mask & N_ and y < 5: continue
            t.put(15, y, MET[1]); t.put(14, y, MET[3], 0.6)
    if mask & S_:
        for x in range(16):
            t.put(x, 15, MET[0]); t.put(x, 14, MET[2])
            t.put(x, 13, MET[4], 0.6)
            if x % 6 == 2: t.put(x, 14, MG[3] if (x // 6 + seed) % 3 else MG[2])                 # service lights underneath
    if mask & N_ and mask & W_:
        t.put(0, 0, MET[14]); t.put(0, 1, MET[11]); t.put(0, 2, MET[9]); t.put(0, 3, CY[3]); t.put(0, 4, MET[8])
    if mask & N_ and mask & E_:
        t.put(15, 0, MET[11]); t.put(15, 1, MET[8]); t.put(15, 2, MET[4]); t.put(15, 3, CY[1]); t.put(15, 4, MET[1])
    if mask & S_ and mask & W_: t.put(0, 15, MET[5])
    return t.img()


DETAIL = {0: 5, 1: 0, 2: 2, 3: 1, 4: 3, 5: 4, 6: 0, 7: 2, 8: 1, 9: 4, 10: 3, 11: 0, 12: 2, 13: 1, 14: 3, 15: 0}


def detail(t, mask, seed):
    k = DETAIL[mask]
    if k == 5:      # deep in the mass: a bolted access hatch, barely there
        t.rect(4, 3, 8, 9, MET[2]); t.rect(4, 3, 8, 1, MET[5]); t.rect(4, 3, 1, 9, MET[4])
        for (xx, yy) in ((5, 4), (10, 4), (5, 10), (10, 10)): t.put(xx, yy, MET[6])
        return
    top = 6 if mask & N_ else 2
    if k == 0:      # a vent grate: dark slots, lit edges
        y0 = top + 1 if top + 6 <= 14 else 8
        t.rect(3, y0, 10, 5, MET[1])
        for yy in range(y0, y0 + 5, 2): t.rect(4, yy, 8, 1, MET[5])
        t.rect(3, y0 - 1, 10, 1, MET[9]); t.rect(3, y0 + 5, 10, 1, MET[3])
    elif k == 1:    # a lit slit window (somebody is still in there)
        y0 = top + 3
        t.rect(4, y0, 7, 2, MET[0]); t.rect(5, y0, 5, 1, AMB[2] if seed % 3 else CY[1]); t.rect(5, y0 + 1, 5, 1, AMB[0] if seed % 3 else CY[0])
        t.rect(4, y0 - 1, 7, 1, MET[9])
    elif k == 2:    # a conduit across the face, a clamp
        y0 = top + 4
        t.rect(0, y0, 16, 1, MET[10]); t.rect(0, y0 + 1, 16, 1, MET[7]); t.rect(0, y0 + 2, 16, 1, MET[3])
        cx = 4 + seed % 8; t.rect(cx, y0 - 1, 2, 4, MET[11]); t.put(cx + 1, y0 + 2, MET[5])
    elif k == 3:    # a vein of the fossil Pale Root through the concrete
        y0 = top + 2 + seed % 3
        for x in range(16):
            y = y0 + math.sin(x * 0.5 + seed) * 1.6
            t.put(x, int(round(y)), FOS[1]); t.put(x, int(round(y)) + 1, FOS[0])
            if h01(x, seed, 2) > 0.8: t.put(x, int(round(y)) - 1, FOS[2])
    else:           # hazard chevrons, worn
        y0 = top + 5
        for x in range(16):
            for yy in range(3):
                if ((x + yy) // 2) % 2 == 0 and h01(x, yy, seed) > 0.2: t.put(x, y0 + yy, AMB[1] if yy else AMB[2], 0.8)


def platform(kind):
    t = T()
    for x in range(16):
        r = h01(x, 3, 21)
        t.put(x, 0, MET[13] if r > 0.8 else MET[12])
        t.put(x, 1, MET[10])
        for y in (2, 3):
            t.put(x, y, MET[1] if (x + y) % 3 == 0 else MET[6])     # grating
        t.put(x, 4, MET[8])
        t.put(x, 5, CY[2] if x % 4 == 1 else MET[2])                # LED dots under the edge
    if kind in ('L', 'single'):
        t.rect(0, 0, 1, 6, MET[12]); t.put(0, 6, MET[8]); t.put(1, 7, MET[7]); t.put(2, 8, MET[6]); t.put(3, 9, MET[5])
    if kind in ('R', 'single'):
        t.rect(15, 0, 1, 6, MET[7]); t.put(15, 6, MET[5]); t.put(14, 7, MET[5]); t.put(13, 8, MET[4]); t.put(12, 9, MET[4])
    return t.img()


def spikes(up=True):
    t = T()
    for i in range(4):
        cx = 2 + i * 4
        for h in range(10):
            w = 1 if h < 6 else 0
            y = 15 - h if up else h
            for xx in range(cx - w, cx + w + 1):
                c = CY[3] if h == 9 else CY[2] if h == 8 else (MET[11] if xx < cx else MET[7] if xx > cx else MET[9])
                t.put(xx, y, c)
        t.put(cx - 2, 15 if up else 0, MET[5]); t.put(cx + 2, 15 if up else 0, MET[4])
    t.rect(0, 15 if up else 0, 16, 1, MET[5])
    return t.img()


def bg_wall(k):
    t = T()
    for y in range(16):
        for x in range(16):
            joint = x % 8 == 0 or y == 15
            bev = y == 0
            v = 0.2 + 0.04 * h01(x // 2, y // 4, k)
            v = 0.13 if joint else 0.27 if bev else v
            if x % 8 == 4 and not joint: v += 0.02                     # a faint rib
            t.put(x, y, M(v))
    if k == 1:      # server LEDs
        for yy in range(3, 14, 3):
            for xx in range(2, 7, 2):
                if h01(xx, yy, 5) > 0.4: t.put(xx, yy, [CY[1], CY[2], MG[2], AMB[1]][int(h01(xx, yy, 9) * 4)])
            for xx in range(10, 15, 2):
                if h01(xx, yy, 6) > 0.55: t.put(xx, yy, [CY[1], MG[1], AMB[1], CY[1]][int(h01(xx, yy, 8) * 4)])
    elif k == 2:    # a cable conduit
        t.rect(6, 0, 4, 16, MET[3]); t.rect(6, 0, 1, 16, MET[6]); t.rect(9, 0, 1, 16, MET[1])
        for yy in (4, 12): t.rect(5, yy, 6, 1, MET[7])
    elif k == 3:    # a dead glyph panel
        t.rect(3, 3, 10, 10, MET[1])
        for yy in range(4, 12, 2):
            for xx in range(4, 12):
                if h01(xx, yy, 5) > 0.55: t.put(xx, yy, CY[0])
    return t.img()


def deco(kind):
    t = T()
    if kind == 0:
        for y in range(16): t.put(7 + int(math.sin(y * 0.4) * 1.2), y, MET[7]); t.put(8 + int(math.sin(y * 0.4) * 1.2), y, MET[3])
    elif kind == 1:
        for i, off in enumerate((4, 7, 10)):
            for y in range(12 - i * 2): t.put(off + int(math.sin(y * 0.5 + i)), y, [MET[7], MET[6], MG[1]][i])
        t.put(7, 6, CY[3])
    elif kind == 2:
        t.rect(3, 12, 10, 2, MET[5]); t.rect(4, 11, 8, 1, MG[3]); t.put(4, 11, MG[4]); t.put(11, 11, MG[4])
    else:
        t.rect(3, 13, 3, 3, MET[9]); t.put(3, 13, MET[12]); t.rect(8, 12, 5, 4, MET[6]); t.put(9, 13, 'e0223f'); t.rect(13, 14, 2, 2, AMB[1])
    return t.img()


def breakable():
    im = solid(0, False, 5); t = T(); t.a = np.asarray(im).copy()
    pts = [(2, 3), (5, 6), (7, 5), (9, 9), (12, 10), (14, 14)]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        n = max(abs(c - a), abs(d - b))
        for i in range(n + 1):
            x, y = round(a + (c - a) * i / n), round(b + (d - b) * i / n); t.put(x, y, MET[0]); t.put(x, y + 1, MET[9])
    t.put(8, 7, CY[2]); t.put(11, 10, CY[1]); t.put(5, 7, CY[1])
    return t.img()


def tuft():
    t = T()   # a little standing clutter on the roof: a drain stub, a cable loop, a puddle catching the neon
    t.rect(3, 12, 2, 4, MET[7]); t.put(3, 12, MET[11]); t.put(4, 15, MET[2])
    for x in range(7, 12): t.put(x, 15, MET[4])
    t.put(6, 14, MET[5]); t.put(12, 14, MET[5]); t.put(9, 13, MET[5])
    t.put(13, 15, CY[1]); t.put(14, 15, CY[2]); t.put(10, 15, MG[2])
    return t.img()


def build_tiles():
    ts = [solid(m, False, m) for m in range(16)] + [solid(m, True, m * 7 + 3) for m in range(16)]
    ts += [platform(k) for k in ('L', 'M', 'R', 'single')]
    ts += [spikes(True), spikes(False)] + [bg_wall(k) for k in range(4)]
    ts += [deco(k) for k in range(4)] + [breakable(), tuft()]
    assert len(ts) == 48
    return ts


def preview(ts, out):
    S = Image.new('RGBA', (12 * 18 * 4, 4 * 18 * 4), (70, 70, 80, 255))
    for i, t in enumerate(ts): S.alpha_composite(t.resize((64, 64), Image.NEAREST), ((i % 12) * 72, (i // 12) * 72))
    S.save(out)
    # a test wall: a slab, a step, a floating block, a catwalk (4x)
    grid = ['................', '..####..........', '..####.....=====', '..####..........', '.........#######', '######...#######',
            '################', '################']
    H_, W_ = len(grid), len(grid[0]); C = Image.new('RGBA', (W_ * 16, H_ * 16), (12, 10, 26, 255))
    sol = lambda x, y: 0 <= y < H_ and 0 <= x < W_ and grid[y][x] == '#' or y >= H_ or x < 0 or x >= W_
    for y in range(H_):
        for x in range(W_):
            if grid[y][x] == '#':
                m = (0 if sol(x, y - 1) else 1) | (0 if sol(x + 1, y) else 2) | (0 if sol(x, y + 1) else 4) | (0 if sol(x - 1, y) else 8)
                C.alpha_composite(ts[m + (16 if h01(x + 7, y * 3, 1) < 0.28 else 0)], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y, 2) < 0.3: C.alpha_composite(ts[47], (x * 16, y * 16 - 16))
            elif grid[y][x] == '=':
                L = x > 0 and grid[y][x - 1] == '='; R = x + 1 < W_ and grid[y][x + 1] == '='
                C.alpha_composite(ts[33 if L and R else 32 if R else 34 if L else 35], (x * 16, y * 16))
    C.resize((C.width * 3, C.height * 3), Image.NEAREST).save(out.replace('.png', '_wall.png'))


if __name__ == '__main__':
    ts = build_tiles()
    os.makedirs(os.path.join(HERE, 'bg_src', 'neohallow'), exist_ok=True)
    preview(ts, os.path.join(HERE, 'bg_src', 'neohallow', 'tiles_preview.png'))
    if '--no-ase' not in sys.argv:
        import asebuild
        asebuild.build('tiles_neohallow', 16, 16, ['art'], [{'ms': 100, 'cels': {'art': t}} for t in ts], [('all', 0, 47)])
    print('ok')
