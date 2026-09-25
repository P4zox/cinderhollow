#!/usr/bin/env python3
"""CONCEPT pass -- "Cindervane, the Last Drake" (main boss, Tempest Spire).

    python3 art/concepts/gen_cindervane.py        -> art/concepts/cindervane.png (+ cindervane_<pose>.png at 1x)

Ash-grey storm wyvern-dragon, 256x160 frame, faces RIGHT.  Same method family as art/gen_hound.py:
every body part is a mask with a per-pixel surface normal (tapered tubes along Catmull-Rom spines,
bevelled plates for membranes / skull), shaded against a top-left light into short hand-picked ramps.
Scales are a staggered, arc-edged cell field in each part's own (u along spine, v across) space, so
shading bands break into clustered scale rows rather than noise; some scale gaps smoulder with embers.
Lightning veins are midpoint-displaced polylines riding the wing bones and dorsal line.

Posable parts (all driven by a pose dict of joints): torso / tail / neck spines, head (+jaw angle,
horn crown), 2x hind legs (hip/knee/ankle/foot), 2x wings (shoulder/elbow/wrist + finger knuckle/tip
list + membrane body attach).  Layer order per pose so it can be split into Aseprite layers later.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
W, H = 256, 160
GROUND = 152

# =========================================================================== palette
HEX = {
    "OUT": "#07070b",
    # ash scale: charcoal -> pale ash
    "S0": "#121218", "S1": "#202029", "S2": "#33333d", "S3": "#4c4b55", "S4": "#6d6a71", "S5": "#9b969a",
    # pale belly plates
    "P0": "#29252a", "P1": "#48413f", "P2": "#6c6259", "P3": "#968a78", "P4": "#c0b39b",
    # wing membrane (slate leather)
    "M0": "#0e0c12", "M1": "#1b1721", "M2": "#2b2331", "M3": "#3f3345", "M4": "#58495c",
    # horn / claw / teeth
    "H0": "#16141a", "H1": "#2d292d", "H2": "#4b4442", "H3": "#75695c", "H4": "#a69780", "H5": "#dccfb2",
    # storm lightning
    "L0": "#0f2146", "L1": "#1c4796", "L2": "#3a86ee", "L3": "#8fd0ff", "L4": "#d9f4ff", "L5": "#ffffff",
    # ember / fire
    "E0": "#3d0f06", "E1": "#8a2408", "E2": "#d24a10", "E3": "#f58a24", "E4": "#ffc35a", "E5": "#fff0b8",
    # mouth
    "K0": "#12060c", "K1": "#2a0d18", "K2": "#4a1a28",
    # storm cloud
    "C0": "#1a1d2a", "C1": "#262a3b", "C2": "#353a50", "C3": "#4a5169", "C4": "#666e8a",
    "BG": "#12141c",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {
    "S": ["S0", "S1", "S2", "S3", "S4", "S5"],
    "P": ["P0", "P1", "P2", "P3", "P4"],
    "M": ["M0", "M1", "M2", "M3", "M4"],
    "H": ["H0", "H1", "H2", "H3", "H4", "H5"],
    "C": ["C0", "C1", "C2", "C3", "C4"],
}
SHINY = {"H": 0.9}
LIGHT = (-0.55, -0.7, 0.46)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)


# =========================================================================== geometry helpers
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def norm3(x, y, z):
    l = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / l, y / l, z / l)


def hash01(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def poly_mask(pts):
    ys = [p[1] for p in pts]
    res = set()
    n = len(pts)
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1):
        cy = y + 0.5
        xi = []
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xi.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xi.sort()
        for a, b in zip(xi[::2], xi[1::2]):
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                res.add((x, y))
    return res


def line(a, b):
    x0, y0 = int(round(a[0])), int(round(a[1]))
    x1, y1 = int(round(b[0])), int(round(b[1]))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts


def polyline(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        out += line(a, b)
    return out


def qbez(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def catmull(pts, step=0.5):
    """Dense Catmull-Rom samples through the control points."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def mask_disc(c, rx, ry=None):
    ry = rx if ry is None else ry
    cx, cy = c
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0}


def dist_field(mask):
    import heapq
    INF = 1e9
    d = {p: INF for p in mask}
    heap = []
    for (x, y) in mask:
        if any((x + a, y + b) not in mask for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            d[(x, y)] = 1.0
            heap.append((1.0, (x, y)))
    heapq.heapify(heap)
    while heap:
        dv, (x, y) = heapq.heappop(heap)
        if dv > d[(x, y)]:
            continue
        for a, b, w in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.41), (1, -1, 1.41),
                        (-1, 1, 1.41), (-1, -1, 1.41)):
            q = (x + a, y + b)
            if q in d and d[q] > dv + w:
                d[q] = dv + w
                heapq.heappush(heap, (dv + w, q))
    return d


def n_plate(mask, bevel=2.5, tilt=(0.0, 0.0), strength=1.2):
    d = dist_field(mask)
    out = {}

    def h(p):
        v = d.get(p)
        if v is None:
            return 0.0
        t = min(v, bevel) / bevel
        return math.sqrt(1 - (1 - t) ** 2)
    for p in mask:
        x, y = p
        gx = (h((x + 1, y)) - h((x - 1, y))) * 0.5
        gy = (h((x, y + 1)) - h((x, y - 1))) * 0.5
        out[p] = norm3(tilt[0] - gx * strength, tilt[1] - gy * strength, 1.0)
    return out


def tube(path, rfn, sign=None):
    """Tapered tube along a dense path.  rfn(t)->radius.  Returns (normals, info) where
    info[p] = (u px along spine, v px across (+ = belly side), r, t, sample index)."""
    n = len(path) - 1
    arc = [0.0]
    for a, b in zip(path, path[1:]):
        arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tang = []
    for i in range(n + 1):
        a, b = path[max(0, i - 2)], path[min(n, i + 2)]
        tang.append(unit(sub(b, a)))
    if sign is None:
        s = sum(t[0] for t in tang)  # perp (-ty, tx) has y = tx: pointing down when moving right
        sign = 1 if s >= 0 else -1
    nm, info, best = {}, {}, {}
    for i, c in enumerate(path):
        t = i / max(1, n)
        r = max(0.6, rfn(t))
        tg = tang[i]
        pp = (-tg[1] * sign, tg[0] * sign)
        for q in mask_disc(c, r + 0.1):
            ox, oy = q[0] + .5 - c[0], q[1] + .5 - c[1]
            d = math.hypot(ox, oy) / r
            if q not in best or d < best[q]:
                best[q] = d
                k = min(0.93, d)
                l = math.hypot(ox, oy) or 1
                nm[q] = norm3(ox / l * k, oy / l * k, math.sqrt(1 - k * k) + 0.12)
                info[q] = (arc[i], ox * pp[0] + oy * pp[1], r, t, i)
    return nm, info, tang, sign


def jagged(a, b, amp, seed, minseg=3.0):
    """Midpoint-displaced lightning polyline a->b."""
    pts = [a, b]
    k = 0
    while True:
        longest = max(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))
        if longest < minseg:
            break
        new = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            m = lerp(p, q, 0.5)
            if L >= minseg:
                nv = unit((-(q[1] - p[1]), q[0] - p[0]))
                off = (hash01(m[0] * 7, m[1] * 13, seed + k) - 0.5) * amp * L / 10
                m = add(m, mul(nv, off))
                new.append(m)
            new.append(q)
            k += 1
        pts = new
    return pts


# =========================================================================== layer buffer
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}      # (x,y) -> [mat, n, bias, tex, fixed, part]

    def paint(self, normals, mat, bias=0.0, ao=1, tex=None, part="", clip=None):
        pts = [p for p in normals if inb(*p) and (clip is None or p in clip)]
        new = set(pts)
        if ao:
            done = set()
            for (x, y) in pts:
                for a, b in ((1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)):
                    q = (x + a, y + b)
                    if q not in new and q not in done and q in self.px:
                        self.px[q][2] -= ao
                        done.add(q)
        for p in pts:
            self.px[p] = [mat, normals[p], bias, (tex.get(p, 0.0) if tex else 0.0), None, part]
        return new

    def fix(self, pts, color):
        for p in pts:
            if p in self.px:
                self.px[p][4] = color


def level_of(e, x, y):
    mat, n, bias, tex, _, _ = e
    ramp = RAMP[mat]
    top = len(ramp) - 1
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = 0.1 + 0.9 * max(0.0, ndl)
    f = v * (top - (1 if mat in SHINY else 0.4)) + 0.35
    base = int(math.floor(f + bias))
    i = base
    if base >= 1 or tex > 0:
        i = int(math.floor(f + bias + tex))
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        i = top if (rz > SHINY[mat] and bias >= 0) else min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    col, lvl = {}, {}
    for (x, y), e in layer.px.items():
        if e[4] is not None:
            col[(x, y)] = e[4]
            continue
        i = level_of(e, x, y)
        lvl[(x, y)] = i
        col[(x, y)] = RAMP[e[0]][i]
    for (x, y) in layer.px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if not inb(*q) or q in layer.px:
                continue
            e = layer.px[(x, y)]
            c = "OUT"
            if (a, b) in ((-1, 0), (0, -1)) and e[4] is None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 2:
                c = RAMP[e[0]][1]
            cur = pix[q]
            if cur[3] == 0 or c == "OUT":
                pix[q] = RGBA[c]
    for p, c in col.items():
        pix[p] = RGBA[c]
    return img


class FX:
    def __init__(self):
        self.px = {}

    def put(self, pts, c, only=None, keep_brighter=True):
        for p in pts:
            if not inb(*p) or (only is not None and p not in only):
                continue
            cur = self.px.get(p)
            if keep_brighter and cur is not None and cur[0] == c[0] and cur > c:
                continue
            self.px[p] = c

    def image(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = RGBA[c]
        return img


# =========================================================================== textures
def scale_tex(info, cw, ch, seed, embers, ember_rate, glow=None, belly_thr=0.5, belly_mat=True,
              band=4.0, throat=None):
    """Staggered arc-edged scales on the back/flank, banded pale plates on the belly side.
    Returns (tex, mats, fixed) dicts."""
    tex, mats, fixed = {}, {}, {}
    for p, (u, v, r, t, _) in info.items():
        vn = v / r
        if belly_mat and vn > belly_thr + (hash01(int(u // 2), 0, seed) - 0.5) * 0.18:
            mats[p] = "P"
            fb = (u / band) % 1.0
            if fb < 1.0 / band + 0.01:
                tex[p] = -1.2
                if throat and throat(t):
                    fixed[p] = "L3" if hash01(p[0], p[1], seed) < 0.3 else "L2"
            elif throat and throat(t) and fb < 2.0 / band + 0.01:
                fixed[p] = "L1"
            elif fb > 1 - 1.5 / band:
                tex[p] = 0.6
            continue
        row = math.floor(v / ch)
        uu = u + (row % 2) * cw * 0.5
        col = math.floor(uu / cw)
        fu = uu / cw - col
        fv = v / ch - row
        edge = 0.2 + 0.28 * (2 * fv - 1) ** 2
        jit = (hash01(col, row, seed) - 0.5) * 0.5
        if fu < edge - 0.02 * 0 and fu < 1.0 / cw + 0.22 * (2 * fv - 1) ** 2 + 0.01:
            tex[p] = -1.25
            if embers and hash01(col, row, seed + 3) < ember_rate and 0.34 < fv < 0.66:
                fixed[p] = "E3" if hash01(p[0], p[1], 5) < 0.35 else ("E2" if hash01(p[0], p[1], 6) < 0.7 else "E1")
        elif fv > 1 - 1.0 / ch + 0.01 and fu > 0.55:
            tex[p] = -0.7 + jit
        elif fu < edge + 1.25 / cw and fv < 0.6:
            tex[p] = 0.85 + jit
            if glow and hash01(col, row, seed + 9) < glow:
                fixed[p] = "L2"
        else:
            tex[p] = jit
    return tex, mats, fixed


# =========================================================================== parts
def paint_tube_part(L, path, rfn, cw, ch, seed, pose, part, belly_thr=0.5, bias=0.0, sign=None,
                    ember_rate=0.08, band=4.0, throat=None, belly=True):
    nm, info, tang, sgn = tube(path, rfn, sign)
    tex, mats, fixed = scale_tex(info, cw, ch, seed, True, ember_rate,
                                 glow=0.18 if pose.get("p2") else None, belly_thr=belly_thr,
                                 band=band, throat=throat, belly_mat=belly)
    groups = {"S": {}, "P": {}}
    for p, n in nm.items():
        groups[mats.get(p, "S")][p] = n
    L.paint(groups["S"], "S", bias, tex=tex, part=part)
    L.paint(groups["P"], "P", bias, ao=0, tex=tex, part=part)
    L.fix([p for p in fixed if p in nm], None)
    for p, c in fixed.items():
        if p in L.px:
            L.px[p][4] = c
    return nm, info, tang, sgn


def dorsal_spikes(L, path, rfn, sgn, every, size, bias=0.0, t0=0.0, t1=1.0, lean=0.75):
    """Back-swept horn spikes along the dorsal (top) side of a tube path."""
    n = len(path) - 1
    i = int(t0 * n)
    k = 0
    while i <= int(t1 * n):
        c = path[i]
        t = i / n
        a, b = path[max(0, i - 2)], path[min(n, i + 2)]
        tg = unit(sub(b, a))
        up = (tg[1] * sgn, -tg[0] * sgn)
        r = rfn(t)
        ln = size(t) * (0.8 + 0.4 * hash01(k, 3, 11))
        base = add(c, mul(up, r * 0.7))
        tip = add(base, add(mul(up, ln), mul(tg, -ln * lean)))
        w = max(1.0, ln * 0.33)
        b1 = add(base, mul(tg, w)); b2 = add(base, mul(tg, -w))
        mid = add(lerp(base, tip, 0.55), mul(tg, -ln * 0.12))
        m = poly_mask([b1, mid, tip, b2])
        L.paint(n_plate(m, 1.5, tilt=(-tg[0] * 0.3, -0.3)), "H", bias + 0.2, ao=0, part="spike")
        i += max(1, int(every / 0.5))
        k += 1


def paint_leg(L, hip, knee, ankle, foot, bias, seed, pose, far=False):
    # thigh: big muscular dome
    tc = lerp(hip, knee, 0.4)
    ang = math.atan2(knee[1] - hip[1], knee[0] - hip[0])
    th_path = catmull([add(hip, (0, -3)), tc, lerp(hip, knee, 0.85)])
    paint_tube_part(L, th_path, lambda t: 13 - 6 * t ** 1.3, 4.5, 3.5, seed, pose, "thigh", belly=False,
                    bias=bias, ember_rate=0.06)
    shin = catmull([knee, lerp(knee, ankle, 0.5), ankle])
    paint_tube_part(L, shin, lambda t: 5.5 - 1.8 * t, 3.5, 3, seed + 1, pose, "shin", belly=False, bias=bias - 0.2,
                    ember_rate=0.0)
    met = catmull([ankle, foot])
    paint_tube_part(L, met, lambda t: 3.6 - 0.6 * t, 3, 3, seed + 2, pose, "met", belly=False, bias=bias - 0.3,
                    ember_rate=0.0)
    # heel spur
    back = unit(sub(ankle, foot))
    sp = poly_mask([add(ankle, (-1, -2)), add(ankle, add(mul(back, 5), (-2, 1))), add(ankle, (1, 2))])
    L.paint(n_plate(sp, 1.2), "H", bias - 0.5, ao=0)
    # toes + claws (pointing along the foot direction)
    fd = unit(sub(foot, ankle))
    fwd = (1.0, 0.0) if abs(fd[1]) > 0.6 else fd
    for j, (dx, dy, ln) in enumerate(((0, 0, 8), (-1, -1.5, 6.5), (-2, 0.8, 5.5))):
        b0 = add(foot, (dx, dy))
        tip = add(b0, mul(fwd, ln))
        toe = catmull([b0, lerp(b0, tip, 0.6), tip])
        nm, _, _, _ = tube(toe, lambda t: 2.4 - 1.0 * t)
        L.paint(nm, "S", bias - (0.6 if j else 0.0), part="toe")
        ct = add(tip, add(mul(fwd, 3), (0, 1.5 if abs(fwd[1]) < .5 else 0)))
        cm = poly_mask([add(tip, (0, -1.6)), add(tip, mul(fwd, 2.4)), ct, add(tip, (-0.5, 1.2))])
        L.paint(n_plate(cm, 1.0), "H", bias, ao=0, part="claw")


def paint_head(L, Lfar, hd, ang, jaw, mouth, pose, seed=40):
    """Head in local space (x forward, y down) around the skull joint hd, rotated by ang degrees."""
    HS = 1.32
    T = lambda p: add(hd, rot(mul(p, HS), ang))
    TJ = lambda p: T(add((-1, 3), rot(sub(p, (-1, 3)), jaw)))
    out = {}
    # far-side horn (behind everything on the head)
    horn_far = [(1, -6), (-10, -13), (-21, -17), (-30, -23)]
    nm, _, _, _ = tube(catmull([T(p) for p in horn_far]), lambda t: (2.8 - 2.3 * t) * HS)
    Lfar.paint(nm, "H", -1.0, part="horn")
    # lower jaw
    jaw_pts = [(-5, 2), (6, 4), (18, 4.5), (28, 4.5), (31, 5.5), (30, 7), (22, 8.5), (10, 9.5), (0, 9.5), (-5, 7)]
    jm = poly_mask([TJ(p) for p in jaw_pts])
    jn = n_plate(jm, 2.5, tilt=rot((0, 0.25), ang + jaw))
    L.paint(jn, "S", -0.3, part="jaw")
    # jaw underside plates (pale)
    jb = poly_mask([TJ(p) for p in [(-3, 7.2), (10, 8.0), (22, 7.2), (30, 6.2), (22, 9.5), (10, 10), (0, 10), (-4, 8.5)]])
    L.paint({p: jn.get(p, (0, 0.5, 0.8)) for p in jb & jm}, "P", -0.5, ao=0,
            tex={p: (-1.2 if (p[0] + p[1]) % 4 == 0 else 0) for p in jb})
    # mouth interior
    if jaw > 4:
        inner = [T((-2, 3))] + [T((x, 3.6)) for x in range(2, 31, 4)] + [TJ((29, 4.2))] + \
                [TJ((x, 4.2)) for x in range(26, -2, -4)]
        mm = poly_mask(inner)
        glowc = ("E5", "E4", "E3", "E2") if mouth == "fire" else ("L5", "L4", "L3", "L1")
        for p in mm:
            lp = mul(rot(sub((p[0] + .5, p[1] + .5), hd), -ang), 1 / HS)
            d = lp[0]
            if mouth == "fire":
                c = "E5" if d > 20 else ("E4" if d > 13 else ("E3" if d > 7 else "E2"))
            else:
                c = "K1" if d > 14 else ("K2" if d > 9 else (glowc[3] if d > 6 else (glowc[2] if d > 3 else glowc[1])))
            L.px[p] = [None, (0, 0, 1), 0, 0, c, "mouth"]
        # tongue
        for x in range(6, 22):
            q = TJ((x, 3.4 + 0.02 * (x - 6) ** 1.3))
            q = (int(q[0]), int(q[1]))
            if q in mm and mouth != "fire":
                L.px[q] = [None, (0, 0, 1), 0, 0, "K2", "mouth"]
    # skull / upper snout
    skull = [(-7, -3), (-4, -7), (3, -8.6), (8, -8.8), (12, -7.2), (16, -5.2), (21, -4.6), (26, -4.4), (30, -3.2),
             (33, -1.2), (34.5, 1), (33, 3.2), (24, 3.6), (12, 3.8), (2, 4.4), (-5, 4), (-8, 0.5)]
    sm = poly_mask([T(p) for p in skull])
    sn = n_plate(sm, 5.0, tilt=rot((0.0, -0.3), ang), strength=1.4)
    tex = {}
    for p in sm:
        lp = mul(rot(sub((p[0] + .5, p[1] + .5), hd), -ang), 1 / HS)
        # sculpted plates: nasal ridge line, cheek plate seam, lip line
        if 14 < lp[0] < 30 and abs(lp[1] - (-1.0 + (lp[0] - 14) * 0.05)) < 0.55:
            tex[p] = -1.0
        elif -2 < lp[0] < 14 and abs(lp[1] - 1.5) < 0.5:
            tex[p] = -0.9
        elif lp[1] > 2.6:
            tex[p] = -0.8
        elif lp[1] < -4 and lp[0] < 10 and (int(lp[0]) + int(lp[1])) % 3 == 0:
            tex[p] = -0.8
    up_l = unit(rot((0, -1), ang))
    for p in sm:
        lp = mul(rot(sub((p[0] + .5, p[1] + .5), hd), -ang), 1 / HS)
        above = (int(round(p[0] + up_l[0])), int(round(p[1] + up_l[1])))
        if above not in sm and 3 < lp[0] < 32:
            tex[p] = 1.6 if hash01(p[0], p[1], 2) < 0.85 else 0.6
        elif 5 < lp[0] < 15 and -5.5 < lp[1] < -1.5:
            tex[p] = tex.get(p, 0) - 1.1
        elif lp[1] > 1.2 and lp[0] > 2:
            tex[p] = tex.get(p, 0) - 0.6
    L.paint(sn, "S", 0.45, tex=tex, part="skull")
    # brow ridge over the eye
    brow = poly_mask([T(p) for p in [(4, -8.4), (12, -7.2), (17, -5.2), (12, -5.0), (6, -5.6)]])
    L.paint(n_plate(brow, 1.4, tilt=rot((0, -0.5), ang)), "S", 0.3, part="brow")
    # teeth: fangs over the lip when closed, full rows when open
    teeth = []
    for x in range(8, 31, 3):
        ln = 2 if x in (26, 29, 11) else 1
        for k in range(ln + (1 if jaw > 4 else 0)):
            teeth.append(T((x, 4.0 + k)))
    if jaw > 4:
        for x in range(10, 29, 3):
            for k in range(2):
                teeth.append(TJ((x + 1, 4.0 - k)))
    for q in teeth:
        q = (int(q[0]), int(q[1]))
        if inb(*q):
            L.px[q] = [None, (0, 0, 1), 0, 0, "H5" if hash01(*q, 3) < 0.5 else "H4", "tooth"]
    # nostril
    for q in (T((30, -0.4)), T((29, -0.4))):
        q = (int(q[0]), int(q[1]))
        if q in L.px:
            L.px[q][4] = "OUT"
    # horn crown (swept back)
    horns = [
        ([(-1, -5), (-12, -11), (-24, -14), (-35, -20)], 3.3, 0.0),
        ([(-3, -1), (-14, -3), (-25, -3), (-35, -7)], 2.6, -0.3),
        ([(4, -7), (-2, -13), (-6, -19), (-7, -25)], 2.0, 0.0),
        ([(11, -6.5), (10, -10), (7, -13)], 1.4, 0.2),
        ([(1, 7), (-6, 10), (-12, 11)], 1.8, -0.4),
        ([(27, -2.5), (28, -5), (26, -7)], 1.1, 0.2),
    ]
    for pts, r0, b in horns:
        path = catmull([T(p) for p in pts])
        nm, info, _, _ = tube(path, lambda t, r0=r0: (r0 - (r0 - 0.4) * t ** 0.9) * HS)
        # growth rings on the horns
        tx = {p: (-0.9 if (info[p][0] % 4.0) < 0.9 and info[p][3] < 0.8 else 0.0) for p in nm}
        L.paint(nm, "H", b, tex=tx, part="horn")
    out["eye"] = T((10, -3.4))
    out["mouth"] = T((29, 3.5 + jaw * 0.1))
    out["dir"] = ang + jaw * 0.45
    out["nostril"] = T((30, -0.5))
    return out


def paint_wing(Lm, Lb, wg, pose, seed, veins):
    sh, el, wr = wg["sh"], wg["el"], wg["wr"]
    fingers, attach = wg["fingers"], wg["attach"]
    far = wg.get("far", False)
    bias = -1.0 if far else 0.0
    tilt = wg.get("tilt", (0.1, -0.2))
    sag = wg.get("sag", 0.22)
    tears = wg.get("tears", 3)
    # membrane panels
    panels = []
    chain = [(fk, ft) for fk, ft in fingers]
    for i in range(len(chain)):
        kn, tp = chain[i]
        if i + 1 < len(chain):
            kn2, tp2 = chain[i + 1]
            end, back = tp2, [kn2]
        else:
            end, back = attach, ([sh] if wg.get("folded") else [sh, el])
        mid = lerp(tp, end, 0.5)
        ctrl = lerp(mid, wr, sag * (1.4 if i + 1 == len(chain) else 1.0))
        sc = qbez(tp, ctrl, end, 14)
        # ragged trailing edge
        sc = [add(p, ((hash01(j, i, seed) - .5) * 1.6, (hash01(j, i, seed + 1) - .5) * 1.6)) if 0 < j < len(sc) - 1 else p
              for j, p in enumerate(sc)]
        poly = [wr, kn] + sc + back
        panels.append((poly, sc, i, tp, end))
    if wg.get("prop", True):
        panels.append(([sh, el, lerp(el, wr, 0.9), lerp(sh, wr, 0.35)], [], -1, None, None))
    for poly, sc, i, ea, eb in panels:
        m = poly_mask(poly)
        # tears: V notches from the trailing edge + holes
        for k in range(tears if i >= 0 else 0):
            if len(sc) < 4:
                break
            j = 2 + int(hash01(i, k, seed + 5) * (len(sc) - 4))
            e = sc[j]
            inward = unit(sub(wr, e))
            depth = 3 + hash01(i, k, seed + 6) * 6
            side = (-inward[1], inward[0])
            wdt = 1.2 + hash01(i, k, seed + 7) * 1.8
            notch = poly_mask([add(e, mul(side, wdt)), add(e, mul(inward, depth)), add(e, mul(side, -wdt * 0.6)),
                               add(e, mul(inward, -2))])
            m -= notch
            if hash01(i, k, seed + 8) < 0.65:
                hc = add(e, mul(inward, depth + 4 + hash01(i, k, 9) * 5))
                m -= mask_disc(add(hc, mul(side, 3)), 1.3 + hash01(i, k, 10) * 1.2, 1.1 + hash01(i, k, 11))
        nm = n_plate(m, 3.0, tilt=tilt, strength=0.9)
        tx = {}
        if ea is not None:  # billow: convex sail between the two bounding fingers, darker toward the trailing edge
            A = math.atan2(ea[1] - wr[1], ea[0] - wr[0])
            B = math.atan2(eb[1] - wr[1], eb[0] - wr[0])
            dl = (B - A + math.pi) % (2 * math.pi) - math.pi
            span = max(math.hypot(ea[0] - wr[0], ea[1] - wr[1]), math.hypot(eb[0] - wr[0], eb[1] - wr[1]))
            for p, nv in nm.items():
                rx_, ry_ = p[0] + .5 - wr[0], p[1] + .5 - wr[1]
                a_ = math.atan2(ry_, rx_)
                s_ = max(0.0, min(1.0, ((a_ - A + math.pi) % (2 * math.pi) - math.pi) / (dl or 1e-6)))
                rl = math.hypot(rx_, ry_) or 1
                tg = (-ry_ / rl * (1 if dl > 0 else -1), rx_ / rl * (1 if dl > 0 else -1))
                k = -math.cos(math.pi * s_) * 0.7
                nm[p] = norm3(nv[0] + tg[0] * k, nv[1] + tg[1] * k, nv[2])
                tx[p] = 0.5 - 0.9 * (rl / span)
        for p in m:
            a = math.atan2(p[1] + .5 - wr[1], p[0] + .5 - wr[0])
            d = math.hypot(p[0] + .5 - wr[0], p[1] + .5 - wr[1])
            s = (math.degrees(a) / 5.0 + hash01(int(d // 6), i, seed) * 0.6) % 1.0
            if d > 10 and s < 0.16 and hash01(int(d // 4), int(math.degrees(a) // 5), seed) < 0.75:
                tx[p] = tx.get(p, 0) - 1.0
            elif d > 10 and s < 0.32:
                tx[p] = tx.get(p, 0) + 0.45
        Lm.paint(nm, "M", bias + (-0.35 if i % 2 else 0.0), ao=0, tex=tx, part="membrane")
    # bones
    def bone(a, b, r0, r1, part, mat="S", bb=0.0):
        path = catmull([a, lerp(a, b, 0.5), b])
        paint_tube_part(Lb, path, lambda t: r0 + (r1 - r0) * t, 3.5, 2.6, seed + len(part), pose, part,
                        belly=False, bias=bias + bb - 0.2, ember_rate=0.04)
        return path
    for kn, tp in fingers:
        path = catmull([wr, kn, lerp(kn, tp, 0.55), tp])
        nm, info, _, _ = tube(path, lambda t: 2.3 - 1.6 * t)
        Lb.paint(nm, "S", bias - 0.2, part="finger")
        ext = add(tp, mul(unit(sub(tp, kn)), 3.5))
        cm = poly_mask([add(tp, (-1, -1)), ext, add(tp, (1, 1))])
        Lb.paint(n_plate(cm, 1.0), "H", bias, ao=0, part="claw")
        if wg.get("folded"):
            ki = min(range(len(path)), key=lambda j: math.hypot(path[j][0] - kn[0], path[j][1] - kn[1]))
            veins.append(("finger_dim", path[ki:], far))
        else:
            veins.append(("finger", path, far))
    fk = 1.2 if wg.get("folded") else 1.0
    hum = bone(sh, el, 6.2, 4.4 * fk, "humerus")
    fore = bone(el, wr, 4.4 * fk, 3.0 * fk, "forearm")
    veins.append(("arm_dim" if wg.get("folded") else "arm", hum + fore, far))
    # elbow spur and knuckle
    eo = unit(add(unit(sub(el, sh)), unit(sub(el, wr))))
    sp = poly_mask([add(el, (eo[1] * 3, -eo[0] * 3)), add(el, mul(eo, 9)), add(el, (-eo[1] * 3, eo[0] * 3))])
    Lb.paint(n_plate(sp, 1.3), "H", bias, ao=0, part="spur")
    Lb.paint({p: (0, -0.3, 1) for p in mask_disc(wr, 3.6)}, "S", bias + 0.2, part="wrist",
             tex={p: -0.4 for p in mask_disc(wr, 3.6)})
    # thumb claw (hooked, pointing forward/down)
    td = wg.get("thumb", (1, 0.4))
    tb = add(wr, mul(unit(td), 2))
    tt = add(tb, mul(unit(td), 6))
    hook = add(tt, (0, 3))
    cm = poly_mask([add(tb, (0, -2)), lerp(tb, tt, 0.6), tt, hook, add(lerp(tb, tt, 0.5), (0, 1.8)), add(tb, (-1, 2))])
    Lb.paint(n_plate(cm, 1.0), "H", bias + 0.2, ao=0, part="thumb")


# =========================================================================== FX
def draw_veins(fx, veins, spine, masks, p2, seed=0):
    core, node, halo, halo2 = ("L4", "L5", "L2", "L1") if p2 else ("L3", "L4", "L1", None)
    k = 0
    for kind, path, far in veins:
        onbody = masks["far" if far else "near"]
        dim = kind.endswith("dim")
        if kind == "arm_dim":
            core_c, node_c, halo_c = ("L0", "L1", "L0") if far else ("L1", "L2", "L0")
        elif (far and not p2) or dim:
            core_c, node_c, halo_c = ("L1", "L2", "L0") if (far and dim) else ("L2", "L3", "L1")
        else:
            core_c, node_c, halo_c = core, node, halo
        n = len(path)
        a0 = 0.0 if kind.startswith("arm") else 0.08
        a1 = 0.75 if dim else 0.92
        pts = [path[int(a0 * (n - 1))]]
        for j in range(int(a0 * (n - 1)) + 6, int(a1 * (n - 1)), 6):
            pts.append(path[j])
        segs = []
        for a, b in zip(pts, pts[1:]):
            segs += jagged(a, b, 3.2 if p2 else 2.4, seed + k)
            k += 1
        pix = polyline(segs)
        # forks into the membrane
        forks = []
        for j in range((2 if p2 else 1) if not dim else 0):
            if len(segs) < 6:
                break
            s0 = segs[int(len(segs) * (0.3 + 0.25 * j + hash01(k, j, 4) * 0.15)) % len(segs)]
            sgn_ = 1 if hash01(k, j, 12) < 0.5 else -1
            dirn = rot(unit(sub(segs[-1], segs[0])), sgn_ * (25 + hash01(k, j, 5) * 45))
            s1 = add(s0, mul(dirn, 7 + hash01(k, j, 6) * (10 if p2 else 5)))
            forks += polyline(jagged(s0, s1, 3.0, seed + 50 + k * 7 + j))
        allp = pix + forks
        hal = set()
        for (x, y) in allp:
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    if (a == 0 or b == 0) and hash01(x + a, y + b, 17 + k) < (0.8 if p2 else (0.25 if dim else 0.55)):
                        hal.add((x + a, y + b))
        if halo2:
            h2 = set()
            for (x, y) in hal:
                for a, b in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1)):
                    if hash01(x + a, y + b, 23) < 0.35:
                        h2.add((x + a, y + b))
            fx.put(h2 - hal, halo2, only=onbody)
        fx.put(hal, halo_c, only=onbody)
        fx.put(forks, core_c if p2 else halo_c, only=onbody)
        fx.put(pix, core_c, only=onbody)
        fx.put([q for i, q in enumerate(pix) if hash01(q[0], q[1], 31) < (0.3 if p2 else 0.15)], node_c, only=onbody)
    # spine crackle: cracks along the dorsal line
    if spine:
        onbody = masks["body"]
        n = len(spine)
        step = 4 if p2 else 6
        for j in range(0, n - step, step):
            if hash01(j, 1, seed + 3) < (0.8 if p2 else 0.55):
                seg = polyline(jagged(spine[j], spine[min(n - 1, j + step)], 3.0, seed + j))
                fx.put(seg, "L3" if p2 else "L2", only=onbody)
                fx.put([q for q in seg if hash01(*q, 7) < 0.2], "L5" if p2 else "L3", only=onbody)


def draw_arc(fx, a, b, seed, core="L4", halo="L2", amp=4.5):
    segs = jagged(a, b, amp, seed, 2.5)
    pix = polyline(segs)
    hal = {(x + dx, y + dy) for (x, y) in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    fx.put(hal - set(pix), halo, keep_brighter=True)
    fx.put(pix, core)
    fx.put([q for q in pix if hash01(*q, 3) < 0.25], "L5")
    # small forks
    for j in range(2):
        s0 = segs[int(len(segs) * (0.35 + 0.3 * j))]
        dirn = rot(unit(sub(b, a)), (-1) ** j * (40 + 30 * hash01(j, seed, 2)))
        fx.put(polyline(jagged(s0, add(s0, mul(dirn, 6 + 6 * hash01(j, seed, 1))), 3, seed + 9 + j)), "L3")


def cloud_layer(centers, seed):
    """Storm-cloud banks: overlapping flattened puffs, lit crowns, dark bellies."""
    L = Layer("cloud")
    for ci, (c, rad) in enumerate(centers):
        m = set()
        for k in range(9):
            ox = (hash01(ci, k, seed) - .5) * rad * 2.2
            oy = (hash01(ci, k, seed + 1) - .5) * rad * 0.7 - abs(ox) * 0.15
            r = rad * (0.42 + 0.34 * hash01(ci, k, seed + 2)) * (1.0 - abs(ox) / (rad * 2.6))
            m |= mask_disc(add(c, (ox, oy)), r * 1.25, r * 0.95)
        bottom = max(p[1] for p in m) - rad * 0.25
        m = {p for p in m if p[1] < bottom + hash01(p[0] // 3, 0, seed + ci) * 2}
        nm = n_plate(m, 4.5, strength=1.5)
        tx = {p: (0.7 if hash01(p[0] // 3, p[1] // 2, seed + ci) < 0.18 else 0) - (p[1] - c[1]) * 0.03 for p in m}
        L.paint(nm, "C", 0.0, ao=1, tex=tx, part="cloud")
    return L


def draw_fire(fx, m0, ang, length, seed):
    d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    nv = (-d[1], d[0])
    for y in range(H):
        for x in range(W):
            o = (x + .5 - m0[0], y + .5 - m0[1])
            a = dot(o, d)
            if a < -1 or a > length:
                continue
            t = max(0.0, a) / length
            hw = 2.0 + a * 0.33 + math.sin(a * 0.45 + seed) * 1.6 * t + (hash01(int(a // 3), 0, seed) - .5) * 3 * t
            v = dot(o, nv)
            rr = abs(v) / max(1.0, hw)
            # licking tongues on the rim
            tongue = hash01(int(a // 2), 1 if v > 0 else 2, seed + 4)
            if rr > 1.0 + (0.35 * tongue if t > 0.25 else 0):
                continue
            # blob head: flame front billows
            if a > length - 6 and rr > 0.55 + 0.4 * hash01(int(v // 2), int(a // 2), seed + 7):
                continue
            q = rr + (hash01(x // 2, y // 2, seed + 2) - .5) * 0.35
            if t < 0.12:
                c = "L5" if q < 0.45 else ("L4" if q < 0.8 else "L3")
            elif t < 0.22:
                c = "E5" if q < 0.35 else ("L4" if q < 0.55 else ("E4" if q < 0.85 else "E3"))
            else:
                c = "E5" if q < 0.28 else ("E4" if q < 0.55 else ("E3" if q < 0.78 else ("E2" if q < 0.95 else "E1")))
            fx.px[(x, y)] = c
    # sparks
    for k in range(26):
        a = hash01(k, 1, seed) * length * 1.1
        v = (hash01(k, 2, seed) - .5) * (6 + a * 0.9)
        p = add(add(m0, mul(d, a)), mul(nv, v))
        q = (int(p[0]), int(p[1]))
        if inb(*q) and q not in fx.px:
            fx.px[q] = "E4" if k % 3 else "L4"


# =========================================================================== poses
POSES = {
    "idle": dict(
        label="1  GROUNDED IDLE - wings folded, head low, growling",
        torso=[(46, 102), (66, 95), (96, 88), (124, 90), (144, 99)], torso_r=[10, 16, 20, 20, 17],
        tail=[(54, 100), (34, 110), (20, 128), (10, 144), (2, 150)],
        neck=[(138, 97), (158, 92), (172, 97), (180, 106)], neck_r=(11, 8),
        head=((181, 108), 22, 5, "blue"),
        legs=[((88, 99), (104, 122), (95, 138), (104, 151), True), ((76, 102), (91, 125), (79, 140), (87, 151), False)],
        wings=[
            dict(sh=(138, 86), el=(128, 58), wr=(170, 148), far=True, folded=True, tilt=(0.2, -0.1), sag=0.1, tears=1,
                 thumb=(1, 0.1), prop=False,
                 fingers=[((150, 82), (118, 32)), ((149, 88), (104, 40)), ((148, 94), (92, 56))], attach=(90, 88)),
            dict(sh=(132, 90), el=(116, 62), wr=(154, 148), folded=True, tilt=(0.25, -0.15), sag=0.18, tears=2,
                 thumb=(1, 0.1),
                 fingers=[((134, 84), (98, 36)), ((133, 90), (80, 46)), ((132, 96), (64, 66))], attach=(60, 106)),
        ],
        order=["farwing_m", "farwing_b", "farleg", "spines", "body", "nearwing_m", "nearwing_b", "nearleg",
               "hornfar", "head"],
    ),
    "roar": dict(
        label="2  REARING ROAR - wings spread (intro cutscene)",
        torso=[(60, 132), (78, 122), (100, 106), (120, 90), (132, 80)], torso_r=[10, 16, 20, 19, 16],
        tail=[(66, 128), (44, 140), (22, 147), (6, 149)],
        neck=[(128, 84), (140, 64), (148, 48), (158, 38)], neck_r=(11, 7.5),
        head=((159, 37), -24, 28, "blue"),
        legs=[((90, 118), (108, 132), (100, 144), (110, 151), True), ((80, 124), (98, 137), (86, 146), (95, 151), False)],
        wings=[
            dict(sh=(130, 80), el=(154, 54), wr=(180, 26), far=True, tilt=(-0.1, -0.1), sag=0.2, tears=2, thumb=(0.4, -1),
                 fingers=[((196, 16), (250, 6)), ((198, 26), (252, 44)), ((194, 36), (232, 80))], attach=(128, 100)),
            dict(sh=(118, 92), el=(100, 56), wr=(84, 22), tilt=(0.15, -0.15), sag=0.22, tears=3, thumb=(0.5, -1),
                 fingers=[((68, 14), (8, 6)), ((68, 26), (4, 48)), ((70, 38), (22, 90))], attach=(96, 104)),
        ],
        order=["farwing_m", "farwing_b", "farleg", "spines", "body", "nearleg", "hornfar", "head",
               "nearwing_m", "nearwing_b"],
    ),
    "breath": dict(
        label="3  FIRE-BREATH SWEEP - head low, cone ignites",
        torso=[(36, 104), (56, 98), (84, 96), (110, 100), (126, 108)], torso_r=[10, 16, 19, 19, 16],
        tail=[(44, 102), (26, 94), (14, 88), (6, 94)],
        neck=[(122, 108), (142, 112), (158, 118), (166, 124)], neck_r=(11, 8),
        head=((167, 125), 9, 24, "fire"),
        legs=[((70, 100), (90, 122), (82, 138), (94, 151), True), ((58, 104), (78, 126), (64, 140), (72, 151), False)],
        wings=[
            dict(sh=(118, 96), el=(106, 58), wr=(146, 148), far=True, folded=True, tilt=(0.2, -0.1), sag=0.16, tears=1,
                 thumb=(1, 0.1), prop=False,
                 fingers=[((126, 84), (96, 22)), ((125, 90), (78, 30)), ((124, 96), (62, 48))], attach=(64, 92)),
            dict(sh=(112, 100), el=(96, 64), wr=(130, 148), folded=True, tilt=(0.25, -0.15), sag=0.2, tears=2,
                 thumb=(1, 0.1),
                 fingers=[((112, 86), (76, 30)), ((111, 92), (56, 42)), ((110, 98), (40, 64))], attach=(40, 104)),
        ],
        order=["farwing_m", "farwing_b", "farleg", "spines", "body", "nearwing_m", "nearwing_b", "nearleg",
               "hornfar", "head"],
        fire=True,
    ),
    "air": dict(
        label="4  AIRBORNE (PHASE 2) - storm-wreathed flight",
        torso=[(60, 92), (80, 88), (108, 86), (134, 86), (148, 90)], torso_r=[9, 15, 18, 17, 14],
        tail=[(66, 91), (42, 97), (24, 92), (10, 99)],
        neck=[(144, 88), (160, 82), (174, 78), (186, 78)], neck_r=(10, 7),
        head=((187, 78), 6, 10, "blue"),
        legs=[((98, 92), (112, 104), (98, 112), (86, 117), True), ((86, 94), (100, 108), (84, 116), (72, 121), False)],
        wings=[
            dict(sh=(138, 80), el=(160, 48), wr=(178, 16), far=True, tilt=(-0.1, -0.1), sag=0.2, tears=2, thumb=(0.5, -1),
                 fingers=[((194, 10), (248, 6)), ((196, 18), (252, 34)), ((192, 26), (230, 60))], attach=(146, 84)),
            dict(sh=(128, 84), el=(106, 52), wr=(94, 16), tilt=(0.15, -0.2), sag=0.22, tears=3, thumb=(0.5, -1),
                 fingers=[((78, 10), (18, 5)), ((78, 18), (12, 40)), ((80, 26), (28, 70))], attach=(82, 90)),
        ],
        order=["farwing_m", "farwing_b", "farleg", "spines", "body", "nearleg", "hornfar", "head",
               "nearwing_m", "nearwing_b"],
        p2=True, shift=(0, 12),
        clouds_back=[((232, 10), 26), ((252, 38), 20), ((16, 6), 26), ((4, 40), 22), ((26, 72), 14), ((222, 62), 14),
                     ((128, -6), 16)],
        clouds_front=[((252, -4), 14), ((2, -6), 15), ((-4, 52), 12), ((258, 52), 12), ((40, 90), 8)],
    ),
}


def radii(lst):
    def f(t):
        x = t * (len(lst) - 1)
        i = min(len(lst) - 2, int(x))
        return lst[i] + (lst[i + 1] - lst[i]) * (x - i)
    return f


def render_pose(P):
    layers = {n: Layer(n) for n in ("farwing_m", "farwing_b", "farleg", "spines", "body", "nearleg",
                                    "nearwing_m", "nearwing_b", "hornfar", "head")}
    p2 = P.get("p2", False)
    veins = []
    body = layers["body"]
    # tail (+ barb), torso, neck share one layer so their junctions read as one hide
    tp = catmull(P["tail"])
    tr = lambda t: 12.5 * (1 - t) ** 0.85 + 1.4
    _, _, ttang, tsgn = paint_tube_part(body, tp, tr, 4.5, 3.5, 11, P, "tail", belly_thr=0.45, ember_rate=0.07)
    # barbed tail tip: arrowhead blade + side barbs
    end = tp[-1]
    d = ttang[-1]
    nv = (-d[1], d[0])
    blade = [add(end, mul(nv, 1.5)), add(end, add(mul(d, -4), mul(nv, 7))), add(end, mul(d, 3)),
             add(end, mul(d, 12)), add(end, mul(d, 3)), add(end, add(mul(d, -4), mul(nv, -7))), add(end, mul(nv, -1.5))]
    bm = poly_mask([blade[0], blade[1], blade[3], blade[5], blade[6]])
    body.paint(n_plate(bm, 1.6, tilt=(0, -0.2)), "H", 0.0, part="barb")
    n = len(tp) - 1
    for k, tt in enumerate((0.62, 0.74, 0.84)):
        i = int(tt * n)
        c, g = tp[i], ttang[i]
        pn = (-g[1], g[0])
        for s in (1, -1):
            b0 = add(c, mul(pn, s * tr(tt) * 0.8))
            tip = add(b0, add(mul(pn, s * 4.5), mul(g, -3)))
            body.paint(n_plate(poly_mask([add(b0, mul(g, 1.5)), tip, add(b0, mul(g, -1.5))]), 1.0), "H",
                       -0.3 if s * tsgn > 0 else 0.0, ao=0, part="barb")
    torso_p = catmull(P["torso"])
    trf = radii(P["torso_r"])
    _, _, tot, tosgn = paint_tube_part(body, torso_p, trf, 6.5, 5.0, 21, P, "torso", belly_thr=0.42, band=5.0,
                                       ember_rate=0.09)
    npth = catmull(P["neck"])
    nr = lambda t: P["neck_r"][0] + (P["neck_r"][1] - P["neck_r"][0]) * t
    _, _, nt, nsgn = paint_tube_part(body, npth, nr, 4.0, 3.2, 31, P, "neck", belly_thr=0.3, band=3.5,
                                     throat=lambda t: t > 0.35, ember_rate=0.06)
    # dorsal spikes
    sp = layers["spines"]
    dorsal_spikes(sp, tp, tr, tsgn, 5, lambda t: 5 * (1 - t) + 1.5, t1=0.8)
    dorsal_spikes(sp, torso_p, trf, tosgn, 6, lambda t: 6.5 + 2 * math.sin(t * 3.1), t0=0.1, t1=0.95)
    dorsal_spikes(sp, npth, nr, nsgn, 5, lambda t: 5 - 2 * t, t1=0.9)
    # legs
    for hip, knee, ankle, foot, far in P["legs"]:
        L = layers["farleg" if far else "nearleg"]
        paint_leg(L, hip, knee, ankle, foot, -1.0 if far else 0.0, 60 if far else 70, P, far)
    # wings
    for wi, wg in enumerate(P["wings"]):
        pre = "farwing" if wg.get("far") else "nearwing"
        paint_wing(layers[pre + "_m"], layers[pre + "_b"], wg, P, 80 + wi * 10, veins)
    hd, ang, jaw, mouth = P["head"]
    hinfo = paint_head(layers["head"], layers["hornfar"], hd, ang, jaw, mouth, P)

    # ---- composite
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if P.get("clouds_back"):
        img.alpha_composite(render_layer(cloud_layer(P["clouds_back"], 5)))
    arcs_back = FX()
    if p2:
        for wg in P["wings"]:
            for k, (kn, tip) in enumerate(wg["fingers"][:2]):
                for cc, rad in P["clouds_back"]:
                    if math.hypot(cc[0] - tip[0], cc[1] - tip[1]) < 24:
                        draw_arc(arcs_back, tip, add(cc, (math.cos(k * 2.1) * rad * 0.6, math.sin(k * 1.3) * rad * 0.4)),
                                 100 + k + int(cc[0]), amp=5)
        for ci, (cc, rad) in enumerate(P["clouds_back"]):
            if rad >= 20:
                a0 = add(cc, (-rad * 0.7, rad * 0.1 * (ci % 2)))
                draw_arc(arcs_back, a0, add(cc, (rad * 0.6, -rad * 0.2 + ci)), 300 + ci, amp=4)
        # clouds lit from inside by the arcs
        cl = img.load()
        arcpx = [p for p, c in arcs_back.px.items() if c in ("L4", "L5", "L3")]
        lit = {}
        for (x, y) in arcpx:
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    q = (x + dx, y + dy)
                    d2 = dx * dx + dy * dy
                    if inb(*q) and cl[q][3] > 0 and d2 <= 36:
                        lit[q] = min(lit.get(q, 99), d2)
        for q, d2 in lit.items():
            if cl[q] != RGBA["OUT"] or d2 <= 4:
                cl[q] = RGBA["L2" if d2 <= 4 else ("L1" if d2 <= 14 else "C4")] if hash01(*q, 41) < 0.85 else cl[q]
        img.alpha_composite(arcs_back.image())
    onbody = set()
    owner = {}
    for name in P["order"]:
        li = render_layer(layers[name])
        img.alpha_composite(li)
        al = li.split()[3].load()
        for y in range(H):
            for x in range(W):
                if al[x, y] > 0:
                    owner[(x, y)] = name
    a = img.split()[3].load()
    onbody = {(x, y) for y in range(H) for x in range(W) if a[x, y] > 0}
    # restrict glow to dragon (not clouds): mask of dragon layers only
    dragon = set()
    for name in P["order"]:
        dragon |= set(p for p in layers[name].px)
    fx = FX()
    spine = []
    # dorsal line for the spine crackle: tail -> torso -> neck, just under the ridge
    for path, rf, sg, t0, t1 in ((tp[::-1], None, tsgn, 0, 0.8), (torso_p, trf, tosgn, 0.05, 1), (npth, nr, nsgn, 0, 0.9)):
        m = len(path) - 1
        for i in range(int(t0 * m), int(t1 * m)):
            c = path[i]
            a0, b0 = path[max(0, i - 2)], path[min(m, i + 2)]
            g = unit(sub(b0, a0))
            s = sg if path is not tp[::-1] else -sg
            up = (g[1] * s, -g[0] * s)
            if rf is None:
                r = tr(1 - i / m)
            else:
                r = rf(i / m)
            spine.append(add(c, mul(up, r * 0.55)))
    vis = lambda *names: {p for p, o in owner.items() if o in names and p in dragon}
    draw_veins(fx, veins, spine, {"far": vis("farwing_m", "farwing_b"), "near": vis("nearwing_m", "nearwing_b"),
                                  "body": vis("body", "spines")}, p2, seed=3)
    # eye
    ex, ey = int(hinfo["eye"][0]), int(hinfo["eye"][1])
    ea = hinfo["dir"] - P["head"][2] * 0.45
    ed = (math.cos(math.radians(ea)), math.sin(math.radians(ea)))
    eye = [(ex, ey), (int(ex + ed[0] * 1.5), int(ey + ed[1] * 1.5)), (int(ex - ed[0] * 1.2), int(ey - ed[1] * 1.2) + 1)]
    fx.put([(ex + a_, ey + b_) for a_ in (-2, -1, 0, 1, 2) for b_ in (-1, 0, 1)], "L1", only=dragon)
    fx.put([(ex + a_, ey - 2) for a_ in (-2, -1, 0, 1)], "OUT", only=dragon)
    fx.put(eye + [(ex + 1, ey), (ex - 1, ey), (ex + 2, ey), (ex - 2, ey + 1)], "L3")
    fx.put([(ex, ey), (ex + 1, ey)], "L5")
    fx.put([(ex - 1, ey + 1), (ex, ey + 1)], "L2")
    if p2:  # trailing eye-light
        for k in range(1, 7):
            q = (int(ex - ed[0] * (k + 2) - 0.3 * k), int(ey - ed[1] * (k + 2) - 0.2 * k))
            fx.put([q], "L3" if k < 3 else "L2")
    # smoulder: embers drifting off the back / from the nostril
    for k in range(18 if not p2 else 26):
        src = spine[int(hash01(k, 1, 77) * (len(spine) - 1))]
        q = (int(src[0] + (hash01(k, 2, 77) - .5) * 8), int(src[1] - 3 - hash01(k, 3, 77) * 14))
        if inb(*q) and q not in dragon:
            fx.put([q], "E3" if k % 3 else "E4")
            if k % 4 == 0 and inb(q[0], q[1] + 1):
                fx.put([(q[0], q[1] + 1)], "E1")
    if P["head"][3] == "blue" and not P.get("fire"):
        nx_, ny_ = hinfo["nostril"]
        for k in range(5):
            q = (int(nx_ + 2 + k * 1.5 + hash01(k, 9, 3) * 2), int(ny_ - 1 - k * 1.2 - hash01(k, 8, 3) * 2))
            fx.put([q], "E2" if k > 2 else "E3")
    if P.get("fire"):
        draw_fire(fx, hinfo["mouth"], hinfo["dir"] + 4, 62, 13)
    img.alpha_composite(fx.image())
    if P.get("clouds_front"):
        img.alpha_composite(render_layer(cloud_layer(P["clouds_front"], 9)))
    if P.get("shift"):
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(img, P["shift"])
        img = out
    return img


# =========================================================================== sheet
def knight():
    p = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40)).convert("RGBA")
    w = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40)).convert("RGBA")
    p.alpha_composite(w)
    return p.transpose(Image.FLIP_LEFT_RIGHT)  # face the dragon


def backdrop(w, h, seed, ground):
    bg = Image.new("RGBA", (w, h), RGBA["BG"])
    px = bg.load()
    # faint storm banks
    for y in range(h):
        for x in range(w):
            v = math.sin(x * 0.045 + seed) * 6 + math.sin(x * 0.11 + y * 0.03 + seed * 2) * 4
            if y < 44 + v and hash01(x // 3, y // 2, seed) < 0.55 + (44 + v - y) * 0.02:
                px[x, y] = (22, 25, 36, 255)
    if ground:
        for x in range(w):
            px[x, GROUND] = (34, 36, 46, 255)
            for y in range(GROUND + 1, h):
                px[x, y] = (20, 21, 29, 255) if (x + y) % 5 else (26, 27, 36, 255)
    return bg


def main():
    out_dir = HERE
    S = 2
    pad = 12
    lab_h = 16
    extra = 52  # knight room beside the idle
    panels = {}
    for k, P in POSES.items():
        im = render_pose(P)
        im.save(os.path.join(out_dir, "cindervane_%s.png" % k))
        wid = W + (extra if k == "idle" else 0)
        bg = backdrop(wid, H, 3 + len(k), ground=(k != "air"))
        bg.alpha_composite(im)
        if k == "idle":
            kn = knight()
            bg.alpha_composite(kn, (W - 18, GROUND - 39))
        panels[k] = bg
    colw = [max(panels["idle"].width, panels["breath"].width), max(panels["roar"].width, panels["air"].width)]
    title_h = 30
    SW = pad * 3 + (colw[0] + colw[1]) * S
    SH = title_h + pad * 2 + 2 * (H * S + lab_h) + pad
    sheet = Image.new("RGBA", (SW, SH), (10, 11, 16, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f1 = ImageFont.load_default(size=16)
        f2 = ImageFont.load_default(size=11)
    except TypeError:
        f1 = f2 = ImageFont.load_default()
    d.text((pad, 8), "CINDERVANE, THE LAST DRAKE  -  Tempest Spire main boss  -  concept pass (256x160 frames, shown 2x)",
           fill=(210, 222, 240), font=f1)
    grid = [["idle", "roar"], ["breath", "air"]]
    y = title_h + pad
    for row in grid:
        x = pad
        for ci, k in enumerate(row):
            d.text((x, y), POSES[k]["label"] + ("   (knight for scale)" if k == "idle" else ""),
                   fill=(143, 208, 255) if k == "air" else (190, 184, 172), font=f2)
            im = panels[k].resize((panels[k].width * S, H * S), Image.NEAREST)
            sheet.alpha_composite(im, (x, y + lab_h))
            x += colw[ci] * S + pad
        y += H * S + lab_h + pad
    sheet.convert("RGB").save(os.path.join(out_dir, "cindervane.png"))
    print("wrote", os.path.join(out_dir, "cindervane.png"), sheet.size)


if __name__ == "__main__":
    main()
