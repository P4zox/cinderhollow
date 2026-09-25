#!/usr/bin/env python3
"""CONCEPT v2 -- "The Unwritten", reaper of forgotten names (boss of the Ashen Archives).

    python3 art/concepts/gen_unwritten.py      -> art/concepts/unwritten.png (+ unwritten_closeup.png)

Fresh redesign (v1 rejected).  Tall, gaunt, floating reaper: a narrow razor-peaked hood over a void with two
glyph-eyes, long skeletal arms, a black ink-cloth cloak that splits into ragged ribbons trailing down and back,
and a spine-hafted scythe whose blade is a giant quill nib with gold script along the edge.

Same method as art/gen_boss.py / gen_sovereign.py: every part is a mask with a per-pixel surface normal; a
material ramp is picked from the lit normal (top-left key), contact AO, per-layer sel-out outline, a selective
cold rim light on the back-lit edges, then hand-placed decals (script, seams, cracks) and stepped-alpha glow.
Parts read joints from a pose dict, so these five concept poses can be keyed into animations later.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
W, H = 144, 144

# =========================================================================== palette
HEX = {
    "OUT": "#050409",
    # ink cloth: blue-black -> deep desaturated indigo (wet sheen at the top)
    "K0": "#09070f", "K1": "#110e1c", "K2": "#1a162b", "K3": "#26203d", "K4": "#372f55", "K5": "#51477a",
    # bone: violet-grey shadow -> cold bone-white
    "B0": "#26222c", "B1": "#433e4b", "B2": "#686270", "B3": "#948d98", "B4": "#bfb8bd", "B5": "#e6e0da",
    # dark spine haft (smoked bone)
    "D0": "#0e0c12", "D1": "#1c1822", "D2": "#2c2733", "D3": "#433c4b", "D4": "#625869", "D5": "#8a7f8e",
    # black blade steel
    "S0": "#08070d", "S1": "#131120", "S2": "#1e1b2f", "S3": "#2e2a45", "S4": "#4d4870", "S5": "#b9b3dc",
    # tarnished gold (script, rings)
    "G0": "#24160c", "G1": "#4d3214", "G2": "#7f5a1f", "G3": "#b3852e", "G4": "#e0b653", "G5": "#fbe7a4",
    # grey old metal (chain, lockets)
    "M0": "#15131a", "M1": "#2b2833", "M2": "#48444f", "M3": "#6f6a75", "M4": "#9d97a0",
    # old paper (desaturated, ink-stained)
    "P0": "#2a2527", "P1": "#4c4442", "P2": "#756a61", "P3": "#a19482", "P4": "#c9bda5",
    # wax seal
    "X0": "#2a0a0e", "X1": "#521419", "X2": "#7c2226", "X3": "#a53a36",
    # void + skull hint inside the hood
    "VD": "#030207", "SK1": "#130e22", "SK2": "#201936", "SK3": "#31274f",
    # cold violet glow
    "V0": "#2b1c50", "V1": "#523799", "V2": "#8a69d8", "V3": "#c4b1ff", "V4": "#f2ecff",
    # crimson (phase 2)
    "R0": "#33070c", "R1": "#6e1119", "R2": "#ab1f24", "R3": "#e2472f", "R4": "#ff8a4f", "R5": "#ffd9a8",
    "RIM": "#5f538f", "RIMR": "#8a2a30",
    "L": "#ffffff",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {m: [m + str(i) for i in range(6)] for m in "KBDSG"}
RAMP["M"] = ["M0", "M1", "M2", "M3", "M4"]
RAMP["P"] = ["P0", "P1", "P2", "P3", "P4"]
RAMP["X"] = ["X0", "X1", "X2", "X3"]
RAMP["R"] = ["R0", "R1", "R2", "R3", "R4", "R5"]
SHINY = {"S": 0.93, "G": 0.88, "M": 0.9, "K": 0.975}
GAIN = {"K": 0.98, "B": 1.0, "D": 0.95, "S": 0.95, "G": 1.0, "M": 1.0, "P": 1.0, "X": 1.0, "R": 1.0}
OFFS = {"K": 0.3, "B": 0.55, "D": 0.35, "S": 0.3, "G": 0.4, "M": 0.4, "P": 0.5, "X": 0.4, "R": 0.5}
LIGHT = (-0.55, -0.72, 0.42)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# =========================================================================== math
def inb(x, y): return 0 <= x < W and 0 <= y < H
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def ipt(p): return (int(math.floor(p[0])), int(math.floor(p[1])))
def perp(v): return (-v[1], v[0])


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def dirv(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def rotv(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def norm3(x, y, z):
    l = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / l, y / l, z / l)


def hash01(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, k=0):
    i = math.floor(x)
    f = x - i
    f = f * f * (3 - 2 * f)
    return hash01(i, 0, k) * (1 - f) + hash01(i + 1, 0, k) * f


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


def curve_px(pts):
    """Pixel-perfect 1px curve through float points (no doubled corners)."""
    raw = []
    for a, b in zip(pts, pts[1:]):
        for q in line(a, b):
            if not raw or raw[-1] != q:
                raw.append(q)
    out = []
    for i, q in enumerate(raw):
        if 0 < i < len(raw) - 1 and out:
            p, r = out[-1], raw[i + 1]
            if abs(p[0] - r[0]) == 1 and abs(p[1] - r[1]) == 1 and (q[0] == p[0] or q[1] == p[1]):
                continue          # drop L-corner pixel
        out.append(q)
    return out


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def qbez(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def ik(s, h, l1, l2, pref):
    dx, dy = h[0] - s[0], h[1] - s[1]
    d = math.hypot(dx, dy) or 1e-6
    if d >= l1 + l2 - 0.01:
        return lerp(s, h, l1 / (l1 + l2))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    mx, my = s[0] + ux * a, s[1] + uy * a
    c1 = (mx - uy * hh, my + ux * hh)
    c2 = (mx + uy * hh, my - ux * hh)
    sc = lambda c: (c[0] - mx) * pref[0] + (c[1] - my) * pref[1]
    return c1 if sc(c1) >= sc(c2) else c2


def mask_disc(c, rx, ry=None):
    ry = rx if ry is None else ry
    cx, cy = c
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0}


def clean(m, passes=2):
    """Kill 1px spurs and fill 1px notches so contours stay smooth (no lumps, no stair noise)."""
    m = set(m)
    for _ in range(passes):
        m -= {p for p in m if sum((p[0] + a, p[1] + b) in m for a, b in N4) <= 1}
        cand = {(p[0] + a, p[1] + b) for p in m for a, b in N4} - m
        m |= {q for q in cand if sum((q[0] + a, q[1] + b) in m for a, b in N4) >= 3}
    return m


def dist_field(mask):
    import heapq
    INF = 1e9
    d = {p: INF for p in mask}
    heap = []
    for (x, y) in mask:
        if any((x + a, y + b) not in mask for a, b in N4):
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


def n_plate(mask, bevel=2.5, tilt=(0.0, 0.0), strength=1.2, fold=None):
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
        nx, ny = tilt[0] - gx * strength, tilt[1] - gy * strength
        if fold:
            fx, fy = fold(x, y)
            nx += fx; ny += fy
        out[p] = norm3(nx, ny, 1.0)
    return out


def n_dome(c, rx, ry, flat=1.0, tilt=(0, 0)):
    cx, cy = c
    out = {}
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            ex, ey = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            e = ex * ex + ey * ey
            if e <= 1.0:
                nx, ny = ex * flat + tilt[0], ey * flat + tilt[1]
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.08, 1 - min(0.92, e) * flat * flat)))
    return out


def tube(pts, r0, r1, ex=1.0):
    n = max(1, len(pts) - 1)
    nm, par, best = {}, {}, {}
    for i, c in enumerate(pts):
        r = max(0.5, r1 + (r0 - r1) * (1 - i / n) ** ex)
        for q in mask_disc(c, r + 0.15):
            ox, oy = q[0] + .5 - c[0], q[1] + .5 - c[1]
            d = math.hypot(ox, oy) / max(r, 0.6)
            if q not in best or d < best[q]:
                best[q] = d
                k = min(0.95, d)
                l = math.hypot(ox, oy) or 1
                nm[q] = norm3(ox / l * k, oy / l * k, math.sqrt(1 - k * k) + 0.15)
                par[q] = i / n
    return nm, par


def ribbon(pts, w0, w1, bulge=0.25, tip_ext=2.0, skew=0.0, ex=1.0):
    """Tapered cloth strip along a centre polyline -> (mask, param t per pixel, polygon)."""
    n = len(pts) - 1
    L, R = [], []
    for i, p in enumerate(pts):
        t = i / n
        a, b = pts[max(0, i - 1)], pts[min(n, i + 1)]
        tg = unit(sub(b, a))
        nr = perp(tg)
        w = (w1 + (w0 - w1) * (1 - t) ** ex) * (1 + bulge * math.sin(math.pi * t)) * 0.5
        L.append(add(p, mul(nr, w * (1 + skew))))
        R.append(add(p, mul(nr, -w * (1 - skew))))
    tip = add(pts[-1], mul(unit(sub(pts[-1], pts[-2])), tip_ext))
    poly = L + [tip] + list(reversed(R))
    m = clean(poly_mask(poly))
    par = {}
    for q in m:
        best, bi = 1e9, 0
        for i in range(0, n + 1):
            d = (q[0] + .5 - pts[i][0]) ** 2 + (q[1] + .5 - pts[i][1]) ** 2
            if d < best:
                best, bi = d, i
        par[q] = bi / n
    return m, par, poly


# =========================================================================== layers
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}          # (x,y) -> [mat, n, bias, fixed, pid, rim]
        self.part_n = 0

    def paint(self, normals, mat, bias=0, ao=1, clip=None, rim=False):
        self.part_n += 1
        pid = self.part_n
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
            self.px[p] = [mat, normals[p], bias, None, pid, rim]
        return new

    def fill(self, mask, color, rim=False):
        self.part_n += 1
        for p in mask:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color, self.part_n, rim]

    def decal(self, pts, color, only_on=None):
        for p in pts:
            e = self.px.get(p)
            if e is None or (only_on is not None and e[0] not in only_on):
                continue
            if isinstance(color, tuple):
                e[0] = color[0]; e[3] = ("LVL", color[1])
            else:
                e[3] = color

    def erase(self, pts):
        for p in pts:
            self.px.pop(p, None)


def level_of(e, x, y):
    mat, n, bias, fixed = e[0], e[1], e[2], e[3]
    ramp = RAMP[mat]
    top = len(ramp) - 1
    if isinstance(fixed, tuple):
        return max(0, min(top, fixed[1] + (bias if bias < 0 else 0)))
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = 0.1 + 0.9 * max(0.0, ndl)
    f = v * (top - (1 if mat in SHINY else 0)) * GAIN[mat] + OFFS[mat]
    if mat == "K":
        f += (60 - y) * 0.010        # ink cloth sinks into darkness toward the wisps
    i = int(math.floor(f)) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        if rz > SHINY[mat] and bias >= 0:
            i = top
        else:
            i = min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, rimcol="RIM", sil=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    col, lvl = {}, {}
    for (x, y), e in layer.px.items():
        if e[0] is None or isinstance(e[3], str):
            col[(x, y)] = e[3]
            continue
        i = level_of(e, x, y)
        lvl[(x, y)] = i
        col[(x, y)] = RAMP[e[0]][i]
    # selective cold rim: back-lit right / lower-right edges of flagged parts
    for (x, y), e in layer.px.items():
        if not e[5] or isinstance(e[3], str):
            continue
        S_ = sil if sil is not None else layer.px
        if (x + 1, y) not in S_ and (x + 1, y) not in layer.px:
            if lvl.get((x, y), 0) <= 3 and y < 118:
                col[(x, y)] = rimcol
    for (x, y) in layer.px:
        for a, b in N4:
            q = (x + a, y + b)
            if not inb(*q) or q in layer.px:
                continue
            e = layer.px[(x, y)]
            c = "OUT"
            if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 2:
                c = RAMP[e[0]][1]
            cur = pix[q]
            if cur[3] == 0 or c == "OUT":
                pix[q] = RGBA[c]
    for p, c in col.items():
        pix[p] = RGBA[c]
    return img


ALPHA_STEPS = (0, 70, 130, 190, 255)


class FXLayer:
    def __init__(self, name):
        self.name = name
        self.px = {}

    def put(self, pts, c, a=255):
        a = min(ALPHA_STEPS, key=lambda s: abs(s - a)) if a < 255 else 255
        rgba = RGBA[c][:3] + (a,)
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if inb(*p):
                self.px[p] = rgba

    def under(self, pts, c, a=255):
        a = min(ALPHA_STEPS, key=lambda s: abs(s - a)) if a < 255 else 255
        rgba = RGBA[c][:3] + (a,)
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if inb(*p) and p not in self.px:
                self.px[p] = rgba

    def image(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = c
        return img


# =========================================================================== rig
PIV = (66, 98)     # lean pivot (waist): above it the torso tips, below it the cloak streams


def joints(p):
    bob = p.get("bob", 0.0)
    lean = p.get("lean", 0.0)

    def X(q):
        v = sub(q, PIV)
        v = rotv(v, lean)
        return (PIV[0] + v[0], PIV[1] + v[1] + bob)
    return dict(X=X, ph=p.get("ph", 0.0), wind=p.get("wind", 0.0), bob=bob, lean=lean)


# =========================================================================== cloak
# rest-pose tails: (start, width, end point, layer, twist seed).  "b" tails hang off the cape (behind),
# "f" tails flare out of the narrow waist of the front robe.
TAILS = [
    ((40, 82), 7.0, (9, 98), "b", 0.0),
    ((44, 88), 8.0, (15, 112), "b", 1.3),
    ((52, 91), 8.5, (28, 125), "b", 2.1),
    ((64, 92), 8.0, (43, 129), "f", 2.9),
    ((70, 92), 7.5, (58, 128), "f", 3.7),
    ((76, 90), 6.5, (70, 121), "f", 4.4),
]


def tail_pts(j, k, spec):
    X, ph, wind = j["X"], j["ph"], j["wind"]
    (sx, sy), w0, (ex, ey), lay, sd = spec
    s = X((sx, sy))
    back = (5 - k) / 5.0
    e = (ex - wind * (0.6 + back * 1.4) + 2.4 * math.sin(ph + sd),
         ey - wind * back * 0.9 + 1.5 * math.cos(ph * 1.1 + sd) + j["bob"] * 0.5)
    c1 = (s[0] - 1.0 - back * 2, s[1] + (e[1] - s[1]) * 0.6)
    c2 = (e[0] + (s[0] - e[0]) * 0.5 + 1.5 * math.sin(ph + sd + 1), e[1] - 3 - back * 6)
    return bezier(s, c1, c2, e, 30), w0


def cloth_fold(par, ph, sd, amp=0.5):
    def f(x, y):
        t = par[(x, y)]
        return (amp * math.sin(t * 4.5 + ph + sd), -0.12)
    return f


def ink_script(layer, pts, t0, t1, seed, off=0.0, cols=("V0", "V1")):
    """Faint lines of forgotten names written down the cloth: dashes + ticks, following the flow."""
    n = len(pts) - 1
    for i in range(int(t0 * n), int(t1 * n)):
        a, b = pts[max(0, i - 1)], pts[min(n, i + 1)]
        nr = perp(unit(sub(b, a)))
        c = add(pts[i], mul(nr, off))
        q = ipt(c)
        h = hash01(i, seed, 31)
        if q not in layer.px or layer.px[q][0] != "K":
            continue
        if h < 0.62:
            layer.decal([q], cols[1] if h < 0.18 else cols[0])
        if h < 0.16:
            layer.decal([ipt(add(c, mul(nr, 1)))], cols[0])


def draw_cloak(L, j, p, info):
    X, ph, wind = j["X"], j["ph"], j["wind"]
    info["tails"] = []
    # ---- cape: hangs from the shoulders behind the body and streams back
    Cp = L["TailsB"]
    sw = 1.5 * math.sin(ph) - wind * 0.8
    left = bezier(X((49, 47)), X((42, 60)), (X((37, 76))[0] + sw, X((37, 76))[1]), (X((36, 88))[0] + sw * 1.4,
                  X((36, 88))[1]), 16)
    poly = left + [X((56, 94)), X((66, 88)), X((78, 64)), X((84, 48)), X((68, 43))]
    cape = clean(poly_mask(poly))

    def cfold(x, y):
        u = x + (y - 50) * 0.55
        t = max(0.0, min(1.0, (y - 48) / 40))
        return (0.7 * math.sin(u * 0.33 + ph * 0.5) * (0.3 + 0.7 * t), -0.1)
    Cp.paint(n_plate(cape, bevel=6, tilt=(0.05, -0.05), strength=1.2, fold=cfold), "K", bias=-1, rim=True)
    for k, spec in enumerate(TAILS):
        if spec[3] != "b":
            continue
        pts, w0 = tail_pts(j, k, spec)
        m, par, _ = ribbon(pts, w0, 0.5, bulge=0.15, ex=0.8)
        Cp.paint(n_plate(m, bevel=2.2, tilt=(0.05, -0.1), strength=1.0, fold=cloth_fold(par, ph, spec[4])),
                 "K", bias=-1 if k == 0 else 0, rim=True)
        if k == 2:
            ink_script(Cp, pts, 0.2, 0.65, k, 0.5)
        info["tails"].append((Cp, m, par))
    # ---- front robe: gaunt torso tapering to a narrow waist, then flaring into the front tails
    R = L["Robe"]
    back = bezier(X((57, 49)), X((58, 64)), X((61, 80)), X((63, 93)), 14)
    front = bezier(X((78, 93)), X((82, 80)), X((86, 66)), X((88, 50)), 14)
    robe = clean(poly_mask(back + [X((70, 95))] + front + [X((74, 45))]))

    apex = X((73, 30))

    def rfold(x, y):
        # folds hang from the shoulders and gather toward the narrow waist
        a = math.atan2(x + .5 - apex[0], y + .5 - apex[1])
        w = 0.6 * math.sin(a * 13 + 0.8 + 0.3 * math.sin(ph)) + 0.25 * math.sin(a * 29 + 2.0)
        return (w, -0.1)
    R.paint(n_plate(robe, bevel=7, tilt=(0.02, -0.12), strength=1.5, fold=rfold), "K", rim=True)
    ink_script(R, bezier(X((80, 60)), X((79, 70)), X((76, 80)), X((72, 94)), 30), 0.0, 1.0, 11, 0.0)
    info["robe"] = robe
    for k, spec in enumerate(TAILS):
        if spec[3] != "f":
            continue
        pts, w0 = tail_pts(j, k, spec)
        m, par, _ = ribbon(pts, w0, 0.5, bulge=0.2, ex=0.8)
        R.paint(n_plate(m, bevel=2.2, tilt=(0.1, -0.1), strength=1.0, fold=cloth_fold(par, ph, spec[4])),
                "K", rim=True)
        if k == 4:
            ink_script(R, pts, 0.12, 0.66, k, -0.5)
        info["tails"].append((R, m, par))
    # ---- wisps: thin ink threads curling off some tail tips
    if p.get("phase", 1) == 1:
        for k in (0, 1, 3, 5):
            pts, _ = tail_pts(j, k, TAILS[k])
            e = pts[-1]
            d = unit(sub(pts[-1], pts[-4]))
            wp = qbez(add(e, mul(d, -1.0)), add(e, add(mul(d, 4), (-1, 0.5))),
                      add(e, (-6 - k * 0.5, 1.0 + 1.2 * math.sin(ph + k))), 10)
            px = curve_px(wp)[:-1]
            lay = Cp if TAILS[k][3] == "b" else R
            lay.paint({q: (-0.4, -0.6, 0.7) for q in px if q not in lay.px}, "K", bias=0, ao=0)


def draw_mantle(L, j, p, info):
    """Shoulder shawl: sharp raised shoulder points (inverted-triangle silhouette), a few knife shreds."""
    X, ph = j["X"], j["ph"]
    M = L["Mantle"]
    top = bezier(X((43, 52)), X((51, 45)), X((60, 40)), X((69, 39)), 10) + \
        bezier(X((79, 39)), X((88, 41)), X((94, 46)), X((98, 54)), 10)
    bot = bezier(X((98, 54)), X((92, 55)), X((86, 58)), X((77, 59)), 8) + \
        bezier(X((66, 59)), X((57, 58)), X((50, 56)), X((43, 52)), 8)
    m = clean(poly_mask(top + bot))
    for k, (s, e, w) in enumerate((((50, 50), (40, 66), 5.0), ((57, 55), (50, 72), 5.5),
                                   ((88, 54), (87, 66), 4.5))):
        s2 = X(s)
        e2 = add(X(e), (1.2 * math.sin(ph + k * 1.7) - j["wind"] * 0.5, 1.0 * math.cos(ph + k)))
        pts = bezier(s2, add(s2, (-1, 5)), add(e2, (3, -4)), e2, 14)
        sm, par, _ = ribbon(pts, w, 0.4, bulge=0.1, ex=0.9)
        M.paint(n_plate(sm, bevel=2, tilt=(0.1, -0.15), strength=1.0, fold=cloth_fold(par, ph, k, 0.35)),
                "K", rim=True)
    M.paint(n_plate(m, bevel=3.0, tilt=(0.05, -0.35), strength=1.35,
                    fold=lambda x, y: (0.35 * math.sin(x * 0.5 + 1.0), 0.0)), "K", rim=True)
    info["mantle"] = m


# =========================================================================== hood / head
NK = (74, 44)


def head_x(j, p):
    X = j["X"]
    t = p.get("htilt", 0.0)
    return lambda q: X(add(NK, rotv(sub(q, NK), t)))


def draw_hood(L, G, j, p, info):
    Hx = head_x(j, p)
    ph2 = p.get("phase", 1) == 2
    Hd = L["Hood"]
    peak = Hx((52, 11))
    crown = bezier(peak, Hx((64, 11)), Hx((78, 15)), Hx((85, 26)), 20)
    lip = [Hx((83, 27))]
    side = bezier(Hx((82.5, 28)), Hx((83, 33)), Hx((85, 38)), Hx((87, 44)), 10)
    bottom = [Hx((80, 46)), Hx((70, 45))]
    back = bezier(Hx((66, 44)), Hx((64, 34)), Hx((63, 22)), peak, 20)
    hood = clean(poly_mask(crown + lip + side + bottom + back[:-1]))
    op = bezier(Hx((82.5, 27.5)), Hx((75, 26)), Hx((70.5, 32)), Hx((72, 38)), 12) + \
        bezier(Hx((72, 38)), Hx((74, 42.5)), Hx((80, 42.5)), Hx((83.5, 38)), 8) + [Hx((83.5, 30))]
    void = clean(poly_mask(op)) & hood

    def fold(x, y):
        a = math.atan2(x + .5 - peak[0], y + .5 - peak[1])
        return (0.3 * math.sin(a * 9 + 0.4), 0.0)
    Hd.paint(n_plate(hood, bevel=4, tilt=(0.0, -0.1), strength=1.4, fold=fold), "K", rim=True)
    seam = curve_px(bezier(add(peak, (3, 1)), Hx((62, 14)), Hx((67, 19)), Hx((69, 28)), 14))
    Hd.decal(seam, ("K", 1))
    Hd.decal([(q[0], q[1] - 1) for q in seam[:10]], ("K", 4))
    rim_in = {q for q in hood - void if any((q[0] + a, q[1] + b) in void for a, b in N4)}
    Hd.decal([q for q in rim_in if q[1] > Hx((0, 30))[1]], ("K", 3))
    if not ph2:
        Hd.decal([q for q in rim_in if Hx((0, 35))[1] < q[1] < Hx((0, 41))[1] and q[0] < Hx((77, 0))[0]], "V0")
    Hd.decal([q for q in rim_in if q[1] <= Hx((0, 30))[1]], ("K", 0))
    Hd.fill(void, "VD")
    info["void"] = void
    info["Hx"] = Hx
    Hd.decal(curve_px([Hx((74, 30.5)), Hx((78, 30)), Hx((82.5, 30.5))]), "SK3")
    Hd.decal(curve_px([Hx((75.5, 35.5)), Hx((79, 35)), Hx((82, 36.5))]), "SK2")
    Hd.decal(curve_px([Hx((76, 40)), Hx((79.5, 40.8)), Hx((82.5, 40))]), "SK1")
    Hd.decal([ipt(Hx((82.8, 34)))], "SK2")
    ec = ("R2", "R3", "R4", "R5") if ph2 else ("V1", "V2", "V3", "V4")
    ne = [ipt(Hx((76.5, 32.5))), ipt(Hx((77.5, 32.5))), ipt(Hx((78.5, 33.5)))]
    fe = [ipt(Hx((81.2, 33.5))), ipt(Hx((82.2, 32.5)))]
    Hd.decal(ne, ec[3]); Hd.decal([ne[0]], ec[2])
    Hd.decal([ipt(Hx((76.5, 31.5)))], ec[1])
    Hd.decal(fe, ec[2]); Hd.decal([fe[1]], ec[3])
    for q in ne + fe:
        G.under([(q[0] + a, q[1] + b) for a, b in ((0, -1), (0, 1), (-1, 0), (1, 0))], ec[0], 130)
    G.under([(ne[1][0], ne[1][1] + 2), (ne[1][0], ne[1][1] + 3)], ec[1], 130)
    info["eye"] = ne[1]


def draw_torn_hood(L, j, p, info):
    """Phase 2: the hood ripped back -- its broken peak drooping behind the skull, shredded at the edge."""
    Hx = head_x(j, p)
    ph = j["ph"]
    Hd = L["Hood"]
    pts = [Hx((86, 44)), Hx((80, 43)), Hx((74, 38)), Hx((69, 30)), Hx((64, 24))]
    tip = Hx((47 + 1.5 * math.sin(ph), 30))
    pts += [Hx((58, 25)), tip, Hx((55, 30)), Hx((50, 36)), Hx((57, 35)), Hx((54, 42)), Hx((61, 40)), Hx((62, 46))]
    m = clean(poly_mask(pts), 1)
    Hd.paint(n_plate(m, bevel=3, tilt=(0.0, -0.2), strength=1.3,
                     fold=lambda x, y: (0.45 * math.sin((x + y) * 0.5 + ph), 0)), "K", rim=True)
    info["Hx"] = Hx


def draw_skull(L, G, j, p, info):
    """Phase 2 head: a long, gaunt, cracked skull (turned right), bone kept mid-grey so it isn't a white blob."""
    Hx = head_x(j, p)
    Sk = L["Head"]
    cran = dict(n_dome(Hx((75, 26.8)), 6.6, 7.4))
    for q, n in n_dome(Hx((70.2, 23.6)), 5.0, 5.2).items():
        cran.setdefault(q, n)
    face = [Hx(q) for q in ((80.5, 24.5), (83.6, 28.2), (82.9, 29.4), (84.3, 31), (85.1, 33.4), (84.3, 34.8),
                            (84.1, 36.6), (80, 37.2), (77, 35.6), (74.5, 33), (73.5, 29))]
    fm = poly_mask(face)
    jaw = [Hx(q) for q in ((76, 35.8), (79, 37.6), (83.2, 37.9), (82.8, 39.6), (79.5, 40.4), (77, 39.4), (75.3, 37))]
    jm = clean(poly_mask(jaw), 1)
    head = clean(set(cran) | fm)
    c = Hx((75, 28))
    nm = {q: cran.get(q) or norm3((q[0] - c[0]) * 0.07, (q[1] - c[1]) * 0.06, 0.9) for q in head}
    Sk.paint(nm, "B", bias=-1)
    Sk.paint(n_plate(jm, bevel=1.5, tilt=(0.1, 0.1), strength=0.8), "B", bias=-1)
    sock = mask_disc(Hx((80.2, 30.9)), 2.7, 2.5)
    Sk.fill(sock & head, "VD")
    Sk.decal(curve_px([Hx((77.5, 27.6)), Hx((82.8, 27.9))]), ("B", 4))                # brow ridge lit
    Sk.fill({ipt(Hx((83.9, 30.5))), ipt(Hx((83.9, 31.5)))} & head, "VD")               # far socket sliver
    Sk.fill({ipt(Hx((84.2, 33.0))), ipt(Hx((84.2, 34.0))), ipt(Hx((83.2, 34.0)))} & head, "VD")   # nasal
    Sk.decal(curve_px([Hx((78, 33.4)), Hx((81.6, 33.3))]), ("B", 4))                   # cheekbone lit
    Sk.decal(curve_px([Hx((77, 34.8)), Hx((80.5, 35.6))]), ("B", 0))                   # cheek hollow
    Sk.decal(curve_px([Hx((74.8, 29.5)), Hx((75.4, 33.2))]), ("B", 1))                 # temple
    for i in range(5):
        Sk.decal([ipt(Hx((79.2 + i, 36.4))), ipt(Hx((79.2 + i, 38.4)))], ("B", 4) if i % 2 == 0 else ("B", 0))
    Sk.decal(curve_px([Hx((77.8, 37.4)), Hx((83.4, 37.4))]), "VD")
    for cr, main in (([(75.5, 19.6), (76.8, 22.4), (75.6, 24.8), (77.6, 27.2)], True),
                     ([(69, 20.5), (70.6, 23.2), (69.8, 25.2)], False)):
        px = curve_px([Hx(q) for q in cr])
        Sk.decal(px, "R2" if main else "R1")
        Sk.decal(px[1:-1:2] if main else px[1:2], "R4" if main else "R3")
        if main:
            G.under([(q[0] + 1, q[1]) for q in px] + [(q[0] - 1, q[1]) for q in px], "R1", 70)
    e = ipt(Hx((80.2, 30.8)))
    Sk.decal([e], "R5"); Sk.decal([(e[0] - 1, e[1])], "R3"); Sk.decal([(e[0], e[1] + 1)], "R2")
    Sk.decal([ipt(Hx((83.9, 30.6)))], "R3")
    G.under([(e[0] + a, e[1] + b) for a in range(-3, 4) for b in range(-3, 3) if abs(a) + abs(b) <= 3], "R2", 70)
    info["eye"] = e
    info["skull"] = head
    info["Hx"] = Hx


RUNES = [
    ["#.#", "###", "#..", "#..", "#.."],
    [".#.", "#.#", ".#.", ".#.", "#.#"],
    ["##.", "#.#", "##.", "#..", "#.."],
    ["#..", "##.", "#.#", "#..", "#.."],
    ["###", ".#.", ".#.", "#.#", ".#."],
    ["#.#", ".#.", "###", ".#.", ".#."],
    [".#", "##", ".#", "#.", "#."],
    ["#.#", "#.#", ".#.", "#.#", "#.#"],
]


def crown_of_script(F, j, info, fi):
    """Phase 2: a circlet of burning crimson letters hovering on the cracked brow, flames licking up."""
    Hx = info["Hx"]
    c = Hx((75, 20.8))
    rx, ry = 8.6, 2.5
    skull = info["skull"]
    for i in range(90):
        a = 2 * math.pi * i / 90
        q = ipt((c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry))
        if math.sin(a) >= 0:
            F.put([q], "R3")
        elif q not in skull:
            F.put([q], "R1", 190)
    for k in range(5):
        a = math.radians(155 - k * 32.5)
        bx, by = c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry
        rune = [["#.", "##", "#.", "#.", "#."], [".#", "##", ".#", "#.", ".#"], ["#", "#", "#", "#", "#"],
                ["#.", "#.", "##", "#.", "#."], [".#", "#.", "##", ".#", ".#"]][k]
        if k == 2:
            rune = [".#.", "###", ".#.", ".#.", "#.#", ".#."]
        hw = len(rune[0])
        x0, y0 = int(bx) - hw // 2, int(by) - len(rune)
        for yy, row in enumerate(rune):
            for xx, ch in enumerate(row):
                if ch == "#":
                    F.put([(x0 + xx, y0 + yy)], "R4" if yy < 2 else "R3")
        fl = 1 + int(3 * hash01(k, fi, 7))
        for s_ in range(fl):
            F.put([(x0 + hw // 2, y0 - 1 - s_)], "R5" if s_ == 0 else "R4", 255 if s_ < 2 else 190)
        F.under([(x0 + xx, y0 + yy) for xx in range(-1, hw + 1) for yy in range(-1, 6)
                 if (x0 + xx, y0 + yy) not in skull], "R0", 130)
    for k in range(7):
        age = (fi * 0.3 + hash01(k, 3, 9)) % 1.0
        F.put([(c[0] - 8 + 16 * hash01(k, 4, 9) - age * 3, c[1] - 7 - age * 12)],
              "R5" if age < 0.3 else "R4" if age < 0.6 else "R2")


# =========================================================================== arms
def draw_arm(Ls, La, Lh, j, arm, info, key, far=False):
    """Short tattered bell sleeve; below it the arm is bare bone: long humerus, elbow knob, radius + ulna."""
    X = j["X"]
    A = X(arm["sh"])
    Wr = arm["wrist"]
    E = ik(A, Wr, 16.5, 17.5, arm["pref"])
    info[key + "_E"] = E
    bias = -1 if far else 0
    d = unit(sub(E, A)); f = unit(sub(Wr, E))
    nA = perp(d); nA = nA if nA[1] < 0 else mul(nA, -1)
    S = add(A, mul(d, arm.get("slen", 8.0)))
    dr = arm.get("drape", (-3, 12))
    cw = arm.get("cuff", 4.6)
    T1 = add(lerp(S, A, 0.1), (dr[0] * 0.5, dr[1]))
    T2 = add(lerp(S, A, 0.55), (dr[0] * 0.7 - 2, dr[1] * 0.7))
    poly = [add(A, mul(nA, 3.4)), add(add(S, mul(nA, cw)), mul(d, 1.2)), add(add(S, mul(nA, -cw)), mul(d, 0.6)),
            T1, add(lerp(S, A, 0.35), add(mul(nA, -4.2), (0, dr[1] * 0.35))), T2, add(A, mul(nA, -3.6))]
    sl = clean(poly_mask(poly), 1)
    Ls.paint(n_plate(sl, bevel=2.5, tilt=(0.05, -0.25), strength=1.2,
                     fold=lambda x, y: (0.45 * math.sin((x - y) * 0.55), 0.0)), "K", bias=bias if far else 1,
             rim=not far)
    Ls.decal({ipt(add(add(S, mul(d, 0.3)), mul(nA, s_))) for s_ in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)}, ("K", 0))
    # humerus
    h0 = add(S, mul(d, -0.5))
    nm, _ = tube([lerp(h0, E, i / 10) for i in range(11)], 1.25, 1.05)
    La.paint(nm, "B", bias=bias - 1, ao=0)
    # forearm: radius + ulna, a dark gap between
    pf = perp(f)
    for o, r0, r1, bb in ((1.2, 0.95, 0.85, -1), (-1.1, 1.15, 1.0, 0)):
        a0 = add(E, mul(pf, o * 0.8))
        a1 = add(Wr, mul(pf, o * 0.35))
        nm, _ = tube([lerp(a0, a1, i / 10) for i in range(11)], r0, r1)
        La.paint(nm, "B", bias=bias + bb, ao=1)
    La.paint(n_dome(E, 1.9, 1.9), "B", bias=bias, ao=0)
    La.paint(n_dome(Wr, 1.8, 1.8), "B", bias=bias, ao=0)
    draw_hand(Lh, Wr, arm, bias)


def draw_hand(Lh, Wr, arm, bias=0):
    hd = arm["hdir"]
    curl = arm.get("curl", 30)
    spread = arm.get("spread", 16)
    segs = arm.get("segs", (5.0, 4.5, 4.0))
    fingers = []
    for i in range(4):
        a = hd + (i - 1.5) * spread
        k0 = add(Wr, mul(dirv(hd + (i - 1.5) * spread * 0.45), 4.5))   # knuckle
        pts = [k0]
        ang = a
        for s, ln in enumerate(segs):
            ang += curl * (0.6 + 0.4 * s) * (1 if i % 2 == 0 else 0.9)
            pts.append(add(pts[-1], mul(dirv(ang), ln * (0.85 + 0.1 * (i in (1, 2))))))
        fingers.append(pts)
    # thumb
    ta = hd + arm.get("thumb", -70)
    tp = [add(Wr, mul(dirv(ta), 1.5))]
    tp.append(add(tp[-1], mul(dirv(ta + 20), 3.5)))
    tp.append(add(tp[-1], mul(dirv(ta + 20 + curl * 0.8), 3.0)))
    fingers.append(tp)
    # palm (metacarpal fan)
    palm = set()
    for fp in fingers[:4]:
        palm |= set(curve_px([Wr, fp[0]]))
    Lh.paint({q: (-0.2, -0.5, 0.85) for q in palm}, "B", bias=bias - 1, ao=0)
    for fp in fingers:
        px = curve_px(fp)
        nmap = {q: (-0.3, -0.6, 0.75) for q in px}
        Lh.paint(nmap, "B", bias=bias, ao=0)
        joints_ = [ipt(q) for q in fp[1:-1]]
        Lh.decal(joints_, ("B", 2 + bias))
        Lh.decal([px[-1]], ("B", 5 + bias))


# =========================================================================== scythe
BLADE_SPINE = bezier((-2, -2), (14, -13.5), (44, -11.5), (58, 15), 28)
BLADE_EDGE = bezier((58, 15), (45, 1.0), (22, -2.5), (0, 6.0), 28)


def scythe_frame(sc):
    Hd, Bt = sc["head"], sc["butt"]
    u = unit(sub(Hd, Bt))
    v = mul(perp(u), sc.get("s", 1))
    k = sc.get("k", 0.88)

    def Wd(q):
        return (Hd[0] + (v[0] * q[0] - u[0] * q[1]) * k, Hd[1] + (v[1] * q[0] - u[1] * q[1]) * k)
    return Hd, Bt, u, v, k, Wd


def draw_scythe(Ls, G, j, sc, info, phase=1):
    Hd, Bt, u, v, k, Wd = scythe_frame(sc)
    # ---- haft: dark vertebral column
    top = add(Hd, mul(u, 2))
    n = int(math.hypot(*sub(top, Bt)))
    pts = [lerp(Bt, top, i / n) for i in range(n + 1)]
    nm, _ = tube(pts, 1.5, 1.5)
    Ls.paint(nm, "D")
    grips = sc.get("grips", [])
    # vertebrae: small knuckled bulges with a back-pointing process, dense near the blade, sparse below
    s = 4.0
    while s < n - 4:
        c = lerp(top, Bt, s / n)
        near_head = s < n * 0.32
        if all(math.hypot(*sub(c, g)) > 3.5 for g in grips):
            if near_head:
                Ls.paint(n_dome(c, 2.0, 2.0), "D", ao=1)
                sp = add(c, mul(v, -2.3))
                Ls.paint({ipt(sp): (-0.4, -0.6, 0.7), ipt(add(sp, add(mul(v, -1), mul(u, -1)))): (-0.4, -0.6, 0.7)},
                         "D", ao=0)
            else:
                Ls.decal(curve_px([add(c, mul(perp(u), -1.4)), add(c, mul(perp(u), 1.4))]), ("D", 1))
        s += 5.5 if near_head else 11.0
    # grip wraps (dark leather strips)
    for g in grips:
        for o in range(-3, 4):
            c = add(g, mul(u, o))
            if o % 2 == 0:
                Ls.decal(curve_px([add(c, mul(perp(u), -1.5)), add(c, mul(perp(u), 1.5))]), ("K", 2))
    # butt spike
    tip = add(Bt, mul(u, -7))
    sp = [lerp(Bt, tip, i / 8) for i in range(9)]
    nm, _ = tube(sp, 1.8, 0.4)
    Ls.paint(nm, "M")
    # ---- blade (quill-nib page-knife)
    poly = [Wd(q) for q in BLADE_SPINE] + [Wd(q) for q in BLADE_EDGE[1:]]
    bl = clean(poly_mask(poly))
    edge_w = [Wd(q) for q in BLADE_EDGE]
    spine_w = [Wd(q) for q in BLADE_SPINE]

    def dmin(q, curve):
        return min(math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) for c in curve)
    nb = n_plate(bl, bevel=3.0, tilt=(0.0, 0.0), strength=0.9)
    Ls.paint(nb, "S", rim=True)
    de = {q: dmin(q, edge_w) for q in bl}
    ds = {q: dmin(q, spine_w) for q in bl}
    ep = {}
    for q in bl:
        best, bi = 1e9, 0
        for i, c in enumerate(edge_w):
            d = (q[0] + .5 - c[0]) ** 2 + (q[1] + .5 - c[1]) ** 2
            if d < best:
                best, bi = d, i
        ep[q] = 1 - bi / (len(edge_w) - 1)       # 0 at the base, 1 at the tip
    for q in bl:
        if de[q] <= 1.0:
            Ls.decal([q], ("S", 4))
        elif de[q] <= 2.4:
            Ls.decal([q], ("S", 3))
        elif ds[q] <= 1.0:
            Ls.decal([q], ("S", 2))
        else:
            Ls.decal([q], ("S", 1 if ep[q] > 0.25 else 2))
    # glints along the edge
    for q in bl:
        if de[q] <= 1.0 and (0.42 < ep[q] < 0.52 or 0.86 < ep[q]):
            Ls.decal([q], ("S", 5))
    # nib slit + breather hole
    mid = [Wd(lerp(BLADE_SPINE[i], BLADE_EDGE[len(BLADE_EDGE) - 1 - i], 0.5)) for i in range(6, 19)]
    slit = curve_px(mid)
    Ls.decal(slit, "OUT")
    hole = mask_disc(Wd((9.5, 0.2)), 1.7, 1.7)
    Ls.fill(hole & bl, "VD")
    Ls.decal([ipt(Wd((10.3, -0.6)))], "V1" if phase == 1 else "R1")
    # gold script etched two px inside the edge
    gc = "G" if phase == 1 else "R"
    for i in range(3, len(BLADE_EDGE) - 3):
        t = i / (len(BLADE_EDGE) - 1)
        a, b = BLADE_EDGE[i - 1], BLADE_EDGE[i + 1]
        nrm = unit(perp(sub(b, a)))
        c = (BLADE_EDGE[i][0] + nrm[0] * 3.0, BLADE_EDGE[i][1] + nrm[1] * 3.0)
        q = ipt(Wd(c))
        if q not in bl or de[q] < 1.5:
            continue
        pat = int(hash01(i, 7, 3) * 4)
        if pat == 0:
            Ls.decal([q], (gc, 3))
        elif pat == 1:
            Ls.decal([q], (gc, 2))
        elif pat == 2:
            Ls.decal([q], (gc, 4 if i % 3 == 0 else 3))
    # ---- collar: dark metal knot, gold band, back spur, finial
    Ls.paint(n_dome(Wd((0.5, 1.5)), 2.8, 2.8), "M", ao=1)
    band = curve_px([Wd((-2.5, 4.5)), Wd((2.5, 4.5))])
    Ls.decal(band, ("G", 3))
    spur = [Wd(q) for q in qbez((-1, 0), (-7, -2), (-10, 4), 8)]
    nm, _ = tube(spur, 1.5, 0.4)
    Ls.paint(nm, "M", ao=0)
    fin = [lerp(add(Hd, mul(u, 2)), add(Hd, mul(u, 8)), i / 6) for i in range(7)]
    nm, _ = tube(fin, 1.3, 0.3)
    Ls.paint(nm, "M", ao=0)
    info["blade"] = bl
    info["blade_tip"] = Wd(BLADE_SPINE[-1])
    info["scythe"] = (Hd, Bt, u, v, k, Wd)


# =========================================================================== trinkets
def draw_pages(Lb, Lf, j, p, info, burn=False, G=None):
    """A slow orbit of torn pages: pale parchment scraps, a dog-eared corner, two lines of faded script,
    a faint violet wake behind each.  Far-side pages are smaller and dimmer."""
    ph = j["ph"]
    orb = p.get("orbit", 0.0)
    C = j["X"]((68, 60))
    n = 4
    for k in range(n):
        th = math.radians(orb + k * 360 / n + 30)
        x = C[0] + math.cos(th) * 52
        y = C[1] + math.sin(th) * 7 - math.cos(th) * 11 + 6 * math.sin(k * 2.1) + 1.5 * math.sin(ph + k)
        front = math.sin(th) > 0
        ang = 24 * math.sin(th * 1.7 + k * 1.3) - 6
        ax, ay = dirv(ang), dirv(ang + 90)
        squash = 0.45 + 0.55 * abs(math.sin(th))
        sc = 1.0 if front else 0.8
        # torn bottom edge, dog-ear top-right
        cu = 1.2 * math.sin(th * 2 + k)                  # page curl
        loc = [(-4.6, -2.6 + cu), (-1.0, -3.0), (2.4, -3.0), (4.4, -1.4 - cu * 0.6), (4.6, 2.6 - cu * 0.4),
               (1.0, 3.0), (-0.4, 2.2), (-1.6, 3.0), (-4.4, 2.8 + cu * 0.5)]
        tf = lambda u, v: (x + (ax[0] * u * squash + ay[0] * v) * sc, y + (ax[1] * u * squash + ay[1] * v) * sc)
        m = clean(poly_mask([tf(u, v) for u, v in loc]), 1)
        if len(m) < 4:
            continue
        L = Lf if front else Lb
        L.paint({q: norm3(-0.5, -0.6, 0.6) for q in m}, "P", bias=0 if front else -1, ao=0)
        ear = poly_mask([tf(2.4, -3.0), tf(4.4, -1.4 - cu * 0.6), tf(2.4, -1.2)]) & m
        L.decal(m, ("P", 3))
        L.decal([q for q in m if (q[0] + 1, q[1]) not in m or (q[0], q[1] + 1) not in m], ("P", 2))
        L.decal(ear, ("P", 2))
        L.decal([q for q in m if ((q[0], q[1] - 1) not in m or (q[0] - 1, q[1]) not in m) and q not in ear], ("P", 4))
        for r, u0, u1 in ((-1.0, -3.2, 1.8), (0.9, -3.2, 3.0)):
            for q in curve_px([tf(u0, r), tf(u1, r)]):
                if q in m and hash01(q[0], q[1], k) > 0.3 and all((q[0] + a_, q[1] + b_) in m for a_, b_ in N4):
                    L.decal([q], ("P", 2))
        if G is not None and not burn:
            for t in range(1, 4):
                th2 = th - math.radians(7 * t)
                wx = C[0] + math.cos(th2) * 52
                wy = C[1] + math.sin(th2) * 7 - math.cos(th2) * 11 + 6 * math.sin(k * 2.1) + 1.5 * math.sin(ph + k)
                G.under([(wx, wy)], "V1" if t == 1 else "V0", 130 if t == 1 else 70)
        if burn:
            edge = [q for q in m if any((q[0] + a_, q[1] + b_) not in m for a_, b_ in N4)]
            L.decal([q for q in edge if hash01(*q, k) > 0.35], ("R", 3))
            L.decal([q for q in edge if hash01(*q, k + 9) > 0.8], ("R", 5))


def draw_chain(L, G, j, p, info, phase=1):
    """Chain of lockets and seals wound round the near wrist: the names it has taken, dangling."""
    ph = j["ph"]
    Wr = p["near"]["wrist"]
    E = info["near_E"]
    f = unit(sub(Wr, E))
    n = perp(f)
    # two wraps around the wrist bones
    for o in (-2.0, -3.6):
        c = add(Wr, mul(f, o))
        for q in curve_px([add(c, mul(n, -2.2)), add(c, mul(n, 2.2))]):
            L.paint({q: (0, -0.5, 0.8)}, "M", ao=0)
    base = add(Wr, mul(f, -2.8))
    swing = p.get("chain_swing", 0.0)
    for k, (ln, kind, dx) in enumerate(((8, "loc", -1.5), (13, "seal", 1.0), (18, "locg", -0.5))):
        e = (base[0] + dx + swing * (0.4 + k * 0.3) + 0.8 * math.sin(ph + k), base[1] + ln)
        mid = add(lerp(base, e, 0.5), (dx * 0.8, 0))
        px = curve_px(qbez(base, mid, e, 10))
        for i, q in enumerate(px[1:]):
            L.paint({q: (0, -0.6 if i % 2 else 0.4, 0.8)}, "M", bias=0 if i % 2 else -1, ao=0)
        c = add(e, (0, 2.4))
        if kind == "seal":
            L.paint(n_dome(c, 2.3, 2.3), "X", ao=0)
            L.decal([ipt(c)], ("X", 0))
            L.decal([ipt(add(c, (1, 0)))], ("X", 1))
        else:
            L.paint(n_dome(c, 1.7, 2.4), "G" if kind == "locg" else "M", ao=0)
            L.decal([ipt(add(c, (0, 0.5)))], ("G", 1) if kind == "locg" else ("M", 0))


# =========================================================================== FX
def fx_smear(Fb, Ff, sm):
    """Ink smear of a horizontal reap: crescent swept around the body, thick + bright at the blade end,
    thinning and fraying into droplets at the trailing end.  Upper (far) half goes behind the body."""
    cx, cy = sm["c"]
    rx, ry = sm["rx"], sm["ry"]
    a0, a1 = sm["a0"], sm["a1"]
    th = sm.get("th", 10.0)
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            ex, ey = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            e = math.hypot(ex, ey)
            if e > 1.0 or e < 0.4:
                continue
            ad = math.degrees(math.atan2(ey, ex)) % 360
            if not (a1 <= ad <= a0):
                continue
            t = (a0 - ad) / (a0 - a1)
            R = math.hypot(rx * ex / e, ry * ey / e)
            depth = (1 - e) * R
            thick = 0.8 + th * t ** 1.5 * (0.55 + 0.45 * max(0.0, ey / e))
            if depth > thick:
                continue
            f = depth / thick
            if t < 0.35 and hash01(x, y, 9) > t * 2.6:
                continue
            L = Ff if ey > -0.05 else Fb
            if f < 0.14:
                col, al = ("V4" if t > 0.75 else "V3" if t > 0.45 else "V2"), 255
            elif f < 0.34:
                col, al = ("V2" if t > 0.55 else "V1"), 255 if t > 0.4 else 190
            elif f < 0.8:
                col, al = "K4", 190 if t > 0.35 else 130
            else:
                col, al = "K3", 130
            L.put([(x, y)], col, al)
    for k in range(10):
        t = 0.04 + 0.06 * k
        a = math.radians(a0 - (a0 - a1) * t)
        x = cx + math.cos(a) * (rx + 1 + 3 * hash01(k, 1, 4))
        y = cy + math.sin(a) * (ry + 1) + 2 * hash01(k, 2, 4)
        L = Ff if math.sin(a) > 0 else Fb
        L.put([(x, y)], "K4" if k % 2 else "V1", 190)
        if k % 3 == 0:
            L.put([(x + 1, y)], "K3", 130)


def fx_glyph_ring(Fb, Ff, rg, fi=0):
    c, r = rg["c"], rg["r"]
    rot = rg.get("rot", 0)
    # outer ring
    for i in range(200):
        a = 2 * math.pi * i / 200
        Ff.put([(c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)], "V2", 190)
    for i in range(0, 120):
        a = 2 * math.pi * i / 120 + rot
        if i % 4 < 2:
            Ff.put([(c[0] + math.cos(a) * (r - 4), c[1] + math.sin(a) * (r - 4))], "V1", 190)
    # inner sigil: a thin 5-point star
    pts = [(c[0] + math.cos(rot + math.pi * 2 * k * 2 / 5 - math.pi / 2) * (r - 5),
            c[1] + math.sin(rot + math.pi * 2 * k * 2 / 5 - math.pi / 2) * (r - 5)) for k in range(6)]
    for q in curve_px(pts):
        Ff.under([q], "V1", 130)
    # runes riding the ring
    for k in range(8):
        a = rot + 2 * math.pi * k / 8
        gx, gy = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r
        rune = RUNES[k % len(RUNES)]
        hw = len(rune[0])
        for yy, row in enumerate(rune):
            for xx, ch in enumerate(row):
                q = (int(gx) - hw // 2 + xx, int(gy) - 2 + yy)
                if ch == "#":
                    Ff.put([q], "V4" if yy == 2 and xx == hw // 2 else "V3")
                else:
                    Ff.put([q], "V0", 190)
        Ff.under([(int(gx) - hw // 2 - 1 + xx, int(gy) - 3 + yy) for xx in range(hw + 2) for yy in range(7)],
                 "V0", 130)
    # core spark at the palm
    h = rg["palm"]
    Ff.put([h], "V4")
    Ff.put([(h[0] + a, h[1] + b) for a, b in N4], "V3", 190)
    Ff.under([(h[0] + a, h[1] + b) for a in range(-2, 3) for b in range(-2, 3)], "V1", 130)
    for k in range(10):
        a = hash01(k, fi, 3) * 6.28
        d = 3 + hash01(k, fi, 4) * (r - 2)
        Ff.put([(c[0] + math.cos(a) * d, c[1] + math.sin(a) * d)], "V3" if k % 3 else "V4", 190)


def burn_tails(L, info, F, fi):
    """Phase 2: cloak tails burning away from the ends -- crimson char creeping up, thin flame tongues, embers."""
    for lay, m, par in info["tails"]:
        for q in m:
            t = par[q]
            if q not in lay.px:
                continue
            h = hash01(*q, 3)
            if t > 0.93:
                lay.decal([q], ("R", 4 if h > 0.6 else 3))
            elif t > 0.85:
                lay.decal([q], ("R", 3 if h > 0.55 else 2))
            elif t > 0.76:
                if h > 0.3:
                    lay.decal([q], ("R", 2 if h > 0.75 else 1))
            elif t > 0.68 and h > 0.8:
                lay.decal([q], ("R", 1))
        tops = {}
        for q in m:
            if par[q] > 0.8 and (q[0] not in tops or q[1] < tops[q[0]]):
                tops[q[0]] = q[1]
        for x, yt in tops.items():
            if hash01(x, fi, 21) < 0.45:
                continue
            h = 1 + vnoise(x / 1.7 + fi * 0.9, 21) * 5
            for s_ in range(1, int(h) + 1):
                f = s_ / h
                F.put([(x, yt - s_)], "R4" if f < 0.35 else "R3" if f < 0.7 else "R2", 255 if f < 0.7 else 190)
    for t in range(22):
        lay, m, par = info["tails"][t % len(info["tails"])]
        hot = sorted(q for q in m if par[q] > 0.8)
        if not hot:
            continue
        s_ = hot[int(hash01(t, 5, 87) * len(hot))]
        age = (fi * 0.23 + hash01(t, 6, 88)) % 1.0
        x = s_[0] - age * 6 + math.sin(age * 7 + t) * 2
        y = s_[1] - 3 - age * 28
        F.put([(x, y)], "R5" if age < 0.15 else "R4" if age < 0.4 else "R3" if age < 0.7 else "R2")


# =========================================================================== poses
IDLE = dict(
    ph=0.0, bob=0.0, lean=0.0, wind=0.0, orbit=-20.0, htilt=0.0,
    near=dict(sh=(88, 51), wrist=(92, 76), pref=(-0.3, 1), hdir=-15, curl=55, spread=11, thumb=-80),
    far=dict(sh=(54, 51), wrist=(40, 84), pref=(-1, 0.1), hdir=105, curl=12, spread=13, thumb=-70,
             drape=(-2, 13)),
    scythe=dict(head=(90, 10), butt=(98, 124), s=1, k=0.88, grips=[(94.5, 76.5)]),
    order=["FXB", "PagesB", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve",
           "Mantle", "Hood", "Head", "Scythe", "NearArm", "NearHand", "Chain", "PagesF", "Glow", "FX"],
)


def P_(base, **kw):
    d = dict(base)
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            nd = dict(d[k]); nd.update(v); d[k] = nd
        else:
            d[k] = v
    return d


POSES = [
    ("IDLE", P_(IDLE)),
    ("IDLE 2 (bob / cloak flow)", P_(IDLE, ph=1.9, bob=2.0, orbit=-4, htilt=-1.5, chain_swing=1.5,
                                     near=dict(wrist=(92, 78)), far=dict(wrist=(40, 87), curl=18),
                                     scythe=dict(head=(90, 12), butt=(98, 126), grips=[(94.5, 78.5)]))),
    ("SCYTHE REAP", P_(IDLE, ph=0.9, bob=1.0, lean=11, wind=7, orbit=5, htilt=6, chain_swing=-4,
                       near=dict(wrist=(103, 70), hdir=-5, curl=62, spread=10, pref=(0.2, 1)),
                       far=dict(wrist=(88, 73), hdir=5, curl=60, spread=10, pref=(0, 1), drape=(-6, 11)),
                       scythe=dict(head=(131, 66), butt=(49, 79), s=1, k=0.88, grips=[(104, 70.5), (89, 72.8)]),
                       smear=dict(rx=57, ry=20, a0=212, a1=35, th=10),
                       order=["FXB", "PagesB", "TailsB", "FarSleeve", "Robe", "NearSleeve", "Mantle",
                              "Hood", "Head", "FarArm", "Scythe", "FarHand", "NearArm", "NearHand", "Chain",
                              "PagesF", "Glow", "FX"])),
    ("GLYPH CAST", P_(IDLE, ph=2.8, bob=-1.0, lean=-4, wind=2, orbit=100, htilt=-4, chain_swing=2,
                      near=dict(wrist=(104, 56), hdir=-8, curl=-6, spread=19, pref=(-0.2, 1), thumb=-85),
                      far=dict(wrist=(52, 30), hdir=-30, curl=62, spread=10, pref=(-1, 0.2), drape=(-4, 12)),
                      scythe=dict(head=(47.8, 16.6), butt=(80, 120), s=-1, k=0.88, grips=[(52, 30)]),
                      ring=dict(c=(121, 56), r=15, rot=0.3, palm=(110, 56)),
                      order=["FXB", "PagesB", "Scythe", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe",
                             "NearSleeve", "Mantle", "Hood", "Head", "NearArm", "NearHand", "Chain", "PagesF",
                             "Glow", "FX"])),
    ("PHASE 2", P_(IDLE, ph=3.6, bob=1.0, lean=3, wind=3, orbit=210, htilt=0, phase=2,
                   near=dict(wrist=(99, 72), curl=60), far=dict(wrist=(42, 82), curl=30, spread=17),
                   scythe=dict(head=(99, 13), butt=(104, 126), s=1, k=0.76, grips=[(101.6, 72)]))),
]


# =========================================================================== render
def render(p, fi=0):
    j = joints(p)
    info = {"j": j}
    names = ["PagesB", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve", "Mantle",
             "Hood", "Head", "Scythe", "NearArm", "NearHand", "Chain", "PagesF"]
    L = {n: Layer(n) for n in names}
    G = FXLayer("Glow")
    F = FXLayer("FX")
    Fb = FXLayer("FXB")
    phase = p.get("phase", 1)
    draw_pages(L["PagesB"], L["PagesF"], j, p, info, burn=phase == 2, G=Fb)
    draw_cloak(L, j, p, info)
    draw_arm(L["FarSleeve"], L["FarArm"], L["FarHand"], j, p["far"], info, "far", far=True)
    draw_arm(L["NearSleeve"], L["NearArm"], L["NearHand"], j, p["near"], info, "near")
    draw_chain(L["Chain"], G, j, p, info, phase)
    draw_mantle(L, j, p, info)
    if phase == 1:
        draw_hood(L, G, j, p, info)
    else:
        draw_torn_hood(L, j, p, info)
        draw_skull(L, G, j, p, info)
        crown_of_script(F, j, info, fi)
    draw_scythe(L["Scythe"], G, j, p["scythe"], info, phase)
    if phase == 2:
        burn_tails(L, info, F, fi)
    if "smear" in p:
        sm = dict(p["smear"])
        tip = info["blade_tip"]
        a1 = math.radians(sm["a1"])
        sm["c"] = (tip[0] - math.cos(a1) * sm["rx"], tip[1] - math.sin(a1) * sm["ry"])   # smear ends at the tip
        fx_smear(Fb, F, sm)
    if "ring" in p:
        fx_glyph_ring(Fb, F, p["ring"], fi)
    sil = set()
    for n in names:
        if not n.startswith("Pages"):
            sil |= set(L[n].px)
    imgs = {n: render_layer(L[n], "RIMR" if phase == 2 else "RIM", sil) for n in names}
    imgs["Glow"], imgs["FX"], imgs["FXB"] = G.image(), F.image(), Fb.image()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in p["order"]:
        out.alpha_composite(imgs[n])
    return out


# =========================================================================== sheet
BG = (0x12, 0x10, 0x16, 255)


def player_frame():
    try:
        pl = Image.open(os.path.join(ROOT, "assets", "player.png")).convert("RGBA").crop((0, 0, 64, 40))
        wp = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).convert("RGBA").crop((0, 0, 64, 40))
        out = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
        out.alpha_composite(pl)
        out.alpha_composite(wp)
        return out
    except Exception:
        return None


def main():
    S = 3
    frames = [(n, render(p, i)) for i, (n, p) in enumerate(POSES)]
    pl = player_frame()
    gap, mar, top = 10, 16, 30
    pbb = pl.getbbox() if pl else (0, 0, 1, 1)
    pw = (pbb[2] - pbb[0] + 6) * S
    Wd = mar * 2 + pw + len(frames) * W * S + (len(frames) - 1) * gap
    Hd = top + H * S + 26
    sheet = Image.new("RGBA", (Wd, Hd), BG)
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=14)
        small = ImageFont.load_default(size=11)
    except Exception:
        font = small = ImageFont.load_default()
    floor = top + H * S                       # frame bottom row == arena floor line
    x = mar
    if pl is not None:
        crop = pl.crop(pbb)
        sheet.alpha_composite(crop.resize((crop.width * S, crop.height * S), Image.NEAREST),
                              (x, floor - (crop.height) * S))
        dr.text((x, top - 20), "KNIGHT", fill=(140, 130, 155), font=font)
    x += pw
    for i, (name, im) in enumerate(frames):
        sheet.alpha_composite(im.resize((W * S, H * S), Image.NEAREST), (x, top))
        dr.text((x + 4, top - 20), name, fill=(205, 196, 225) if i != 4 else (230, 96, 80), font=font)
        x += W * S + gap
    dr.line([mar, floor, Wd - mar, floor], fill=(46, 40, 56), width=1)
    dr.text((mar, floor + 7), "The Unwritten -- reaper of forgotten names.  concept v2, 144x144 frames @3x, "
            "floor = frame bottom, lowest wisp ~10px above.", fill=(110, 100, 125), font=small)
    out = os.path.join(HERE, "unwritten.png")
    sheet.convert("RGB").save(out)
    Z = 4
    sel = (0, 2, 3, 4)
    cl = Image.new("RGBA", (W * Z * len(sel) + 12 * (len(sel) - 1), H * Z), BG)
    for i, fi in enumerate(sel):
        cl.alpha_composite(frames[fi][1].resize((W * Z, H * Z), Image.NEAREST), (i * (W * Z + 12), 0))
    cl.convert("RGB").save(os.path.join(HERE, "unwritten_closeup.png"))
    for i, (n, im) in enumerate(frames):
        bb = im.getbbox()
        print(n, "bbox", bb)
    print("wrote", out)


if __name__ == "__main__":
    main()
