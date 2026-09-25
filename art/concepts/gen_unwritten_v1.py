#!/usr/bin/env python3
"""CONCEPT pass -- "The Unwritten" (ink wraith, boss of the Ashen Archives).

    python3 art/concepts/gen_unwritten.py            -> art/concepts/unwritten.png (+ unwritten_closeup.png)

Standalone concept generator (does not touch assets/ or the production pipeline).  Same method as
art/gen_boss.py / gen_sovereign.py: every part is a mask with a per-pixel surface normal, a hue-shifted
material ramp is picked from the lit normal (top-left key light), wet-ink specular pops, contact AO,
per-layer sel-out outline, then hand-placed decals (glyphs, page lines, nib slits) and glow FX.

Part functions take the joint dict `j` + pose dict `p`, so the poses below can later be keyed into
full animations (idle / barrage / slash / phase 2) without redrawing anything.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
W, H = 128, 128

# =========================================================================== palette
HEX = {
    "OUT": "#07060b",
    # wet ink: blue-black -> deep indigo, violet-white wet specular
    "K0": "#08060e", "K1": "#100c1d", "K2": "#1a1430", "K3": "#282046", "K4": "#3d3166", "K5": "#a397dc",
    # parchment: umber shadow -> warm cream
    "P0": "#2e1f1c", "P1": "#5b4336", "P2": "#937657", "P3": "#c4a97e", "P4": "#e6d3a7", "P5": "#faf0d2",
    # nib brass
    "G0": "#2b1a0e", "G1": "#5a3a14", "G2": "#8e6320", "G3": "#c4912e", "G4": "#ecc257", "G5": "#fff0b0",
    # violet glyph glow
    "V0": "#27163f", "V1": "#4a2880", "V2": "#8651c9", "V3": "#c29af0",
    # gold glyph glow
    "Y0": "#d0902c", "Y1": "#f6c64e", "Y2": "#ffe99c", "Y3": "#fffbe8",
    # phase-2 crimson / burning ink
    "C0": "#2a0710", "C1": "#5c0d1c", "C2": "#9c1626", "C3": "#dc2c2c", "C4": "#ff6a3d", "C5": "#ffc49a",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {
    "K": ["K0", "K1", "K2", "K3", "K4", "K5"],
    "P": ["P0", "P1", "P2", "P3", "P4", "P5"],
    "G": ["G0", "G1", "G2", "G3", "G4", "G5"],
}
SHINY = {"K": 0.93, "G": 0.9}
LIGHT = (-0.55, -0.7, 0.46)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)
# glyph colour schemes: (core, bright, mid, halo, deep halo)
GLYPH = {1: ("Y3", "Y2", "Y1", "V2", "V1"), 2: ("C5", "C4", "C3", "C2", "C1")}


# =========================================================================== geometry
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def dirv(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
def ipt(p): return (int(math.floor(p[0])), int(math.floor(p[1])))


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def rot_about(p, piv, deg):
    return add(rot(sub(p, piv), deg), piv)


def unit(v):
    l = math.hypot(*v) or 1e-6
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


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def ellipse_pts(c, rx, ry, rotd=0, n=40):
    return [add(c, rot((rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)), rotd))
            for i in range(n)]


# ---------------------------------------------------------------- normal fields
def n_capsule(a, b, r0, r1=None, flat=1.0):
    r1 = r0 if r1 is None else r1
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-6
    R = max(r0, r1) + 1
    out = {}
    for y in range(int(min(ay, by) - R), int(max(ay, by) + R) + 2):
        for x in range(int(min(ax, bx) - R), int(max(ax, bx) + R) + 2):
            px, py = x + .5, y + .5
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
            qx, qy = ax + dx * t, ay + dy * t
            r = r0 + (r1 - r0) * t
            ox, oy = px - qx, py - qy
            if ox * ox + oy * oy <= r * r:
                k = 1.0 / r
                nx, ny = ox * k * flat, oy * k * flat
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
    return out


def tube(pts, r0, r1):
    out = {}
    n = max(1, len(pts) - 1)
    for i in range(len(pts) - 1):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        for q, v in n_capsule(pts[i], pts[i + 1], ra, rb).items():
            if q not in out:
                out[q] = v
    return out


def n_dome(c, rx, ry=None, tilt=(0, 0)):
    ry = rx if ry is None else ry
    cx, cy = c
    out = {}
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            ex, ey = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            e = ex * ex + ey * ey
            if e <= 1.0:
                out[(x, y)] = norm3(ex + tilt[0], ey + tilt[1], math.sqrt(max(0.08, 1 - min(0.92, e))))
    return out


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


def n_plate(mask, bevel=2.5, tilt=(0.0, 0.0), strength=1.2, fold=None):
    d = dist_field(mask)

    def h(p):
        v = d.get(p)
        if v is None:
            return 0.0
        t = min(v, bevel) / bevel
        return math.sqrt(1 - (1 - t) ** 2)
    out = {}
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


def mask_disc(c, rx, ry=None):
    ry = rx if ry is None else ry
    cx, cy = c
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0}


def edge_of(mask, dirs=((1, 0), (-1, 0), (0, 1), (0, -1))):
    return {q for q in mask if any((q[0] + a, q[1] + b) not in mask for a, b in dirs)}


# =========================================================================== layers
class Layer:
    """Shaded layer: (x,y) -> [mat, normal, bias, fixed]; fixed = palette key or ("LVL", i)."""

    def __init__(self, name):
        self.name = name
        self.px = {}

    def paint(self, normals, mat, bias=0, ao=1, clip=None):
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
            self.px[p] = [mat, normals[p], bias, None]
        return new

    def fill(self, mask, color):
        for p in mask:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color]

    def decal(self, pts, color, only_on=None):
        for p in pts:
            e = self.px.get(p)
            if e is None or (only_on is not None and e[0] not in only_on):
                continue
            if isinstance(color, tuple):
                e[0] = color[0]; e[3] = ("LVL", color[1])
            else:
                e[3] = color

    def shift(self, pts, d):
        for p in pts:
            e = self.px.get(p)
            if e is not None:
                e[2] += d


def level_of(e, x, y):
    mat, n, bias, fixed = e[0], e[1], e[2], e[3]
    ramp = RAMP[mat]
    top = len(ramp) - 1
    if isinstance(fixed, tuple):
        return max(0, min(top, fixed[1] + (bias if bias < 0 else 0)))
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = 0.16 + 0.84 * max(0.0, ndl)
    f = v * (top - (1 if mat in SHINY else 0)) + 0.3
    if mat == "K":
        f -= 0.55 + max(0, y - 76) * 0.012      # ink stays black; sinks darker toward the wisps
    if mat == "P":
        f += 0.45
    i = int(math.floor(f)) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        if rz > SHINY[mat]:
            i = top if bias >= 0 else top - 1
        else:
            i = min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, glows=(), outline=True, remap=None):
    """Resolve to RGBA with sel-out outline; `glows` = [(pt, radius, key_near, key_far)] rim lights on ink."""
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
    # cool violet bounce on the shadow-side (right / lower-right) silhouette so black ink reads on dark bg
    for (x, y), e in layer.px.items():
        if e[0] == "K" and e[3] is None and (x + 1, y) not in layer.px and e[1][0] > 0.3 and y < 104:
            col[(x, y)] = "K4" if lvl.get((x, y), 0) >= 2 else "K3"
    # coloured rim light from glyph glows onto ink silhouettes
    for (x, y), e in layer.px.items():
        if e[0] != "K" or e[3] is not None or not glows:
            continue
        n = e[1]
        nl = math.hypot(n[0], n[1])
        if nl < 0.3:
            continue
        for (g, R, near, far) in glows:
            dx, dy = g[0] - x, g[1] - y
            d = math.hypot(dx, dy)
            if d > R or d < 1:
                continue
            face = (n[0] * dx + n[1] * dy) / (nl * d)
            if face < 0.45:
                continue
            sx = 1 if dx > 0.4 * d else -1 if dx < -0.4 * d else 0
            sy = 1 if dy > 0.4 * d else -1 if dy < -0.4 * d else 0
            if (x + sx, y + sy) not in layer.px:
                col[(x, y)] = near if d < R * 0.55 else far
                break
    if outline:
        for (x, y) in layer.px:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if not inb(*q) or q in layer.px:
                    continue
                e = layer.px[(x, y)]
                c = "OUT"
                if (a, b) in ((-1, 0), (0, -1)) and e[0] in ("P", "G") and lvl.get((x, y), 0) >= 3:
                    c = RAMP[e[0]][1]
                if pix[q][3] == 0 or c == "OUT":
                    pix[q] = RGBA[c]
    for p, c in col.items():
        pix[p] = RGBA[(remap or {}).get(c, c)]
    return img


class FX:
    def __init__(self):
        self.px = {}

    def put(self, pts, c, over=True):
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if inb(*p) and (over or p not in self.px):
                self.px[p] = c

    def image(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = RGBA[c]
        return img


# =========================================================================== glyphs
RUNE5 = ["#...#/.#.#./..#../..#../.###.", ".###./#...#/.###./..#../..#..", "#.#.#/#.#.#/.###./..#../..#..",
         "..#../.#.#./#.#.#/.#.#./..#..", "###../..#../.###./...#./..###", "#..#./#.#../##.../#.#../#..#."]
RUNE3 = ["#.#/.#./#.#", ".#./###/.#.", "##./.#./.##", "#../###/..#", ".##/#.#/##."]


def rune_pts(src, c):
    rows = src.split("/")
    h, w = len(rows), len(rows[0])
    ox, oy = int(round(c[0])) - w // 2, int(round(c[1])) - h // 2
    return [(ox + i, oy + j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch == "#"]


def glyph(F, src, c, phase, bright=True):
    """Glowing rune: core colour + 1px coloured halo (no soft alpha)."""
    core, hi, mid, halo, deep = GLYPH[phase]
    pts = rune_pts(src, c)
    s = set(pts)
    ring = {(x + a, y + b) for (x, y) in pts for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))} - s
    F.put(ring, halo, over=False)
    F.put(pts, hi if bright else mid)
    return s


# =========================================================================== poses
def P_(**kw):
    p = dict(o=(0, 0), lean=0.0, htilt=0.0, hoff=(0, 0), trail=0.0, ph=0.0, phase=1, cowl_lift=0.0, fx=())
    p.update(kw)
    return p


def pose_idle(k=0):
    b = 1 if k else 0
    return P_(o=(0, 1 - 2 * b), ph=0.0 if k == 0 else 1.6, htilt=-2 * b, trail=b,
              fa=dict(e=(84, 71 + b), w=(89, 87 + b), fing=[48, 68, 88, 108], thumb=150, curl=26, l=(8, 7)),
              ba=dict(e=(35, 71 + b), w=(30, 87 + b), fing=[132, 112, 92, 72], thumb=30, curl=-26, l=(7.5, 6.5)))


def pose_barrage():
    return P_(o=(1, 0), lean=-4, htilt=-8, hoff=(0, -1), trail=-1, ph=0.8, cowl_lift=2,
              fa=dict(e=(89, 53), w=(101, 46), fing=[-80, -54, -28, -2], thumb=40, curl=16, l=(7, 6), ring=13),
              ba=dict(e=(31, 53), w=(22, 46), fing=[-100, -122, -144, -166], thumb=140, curl=-16, l=(6.5, 5.5),
                      ring=12),
              fx=("barrage",))


def pose_slash():
    return P_(o=(-10, 1), lean=16, htilt=8, hoff=(1, 1), trail=10, ph=2.2, cowl_lift=-1,
              fa=dict(e=(95, 61), w=(112, 70), fing=[8, 26, 44, 62], thumb=140, curl=26, l=(8, 7)),
              ba=dict(e=(37, 69), w=(27, 60), fing=[195, 212, 229, 246], thumb=150, curl=-20, l=(6.5, 5.5)),
              fx=("smear",))


def pose_p2():
    return P_(o=(0, 2), lean=3, htilt=5, ph=0.9, phase=2, trail=2, cowl_lift=1.5,
              fa=dict(e=(88, 64), w=(99, 72), fing=[-14, 10, 34, 58], thumb=110, curl=28, l=(8, 7)),
              ba=dict(e=(33, 64), w=(24, 72), fing=[188, 164, 140, 116], thumb=70, curl=-28, l=(7.5, 6.5)),
              fx=("pages", "burn"))


def joints(p):
    ox, oy = p["o"]
    piv = (58, 82)

    def X(pt):
        return (pt[0] + ox, pt[1] + oy)

    def U(pt):
        q = rot_about(pt, piv, p["lean"])
        return (q[0] + ox, q[1] + oy)
    head = add(U((63, 25)), p["hoff"])
    return dict(X=X, U=U, head=head, hang=p["lean"] + p["htilt"],
                sf=U((74, 53)), sb=U((43, 53)), waist=U((58, 80)))


# =========================================================================== parts
def draw_tail(Ly, j, p, info):
    """Ink skirt below the waist fraying into trailing tendrils + falling drips.  Floats: lowest px ~ y117."""
    X, U, ph, tr = j["X"], j["U"], p["ph"], p["trail"]
    wl, wr = U((50.5, 79)), U((65.5, 79))
    bl, br = X((45 - tr * 0.6, 92)), X((68 - tr * 0.4, 91))
    left = bezier(wl, add(wl, (-3, 6)), X((42 - tr * 0.4, 87)), bl, 12)
    right = bezier(br, X((72 - tr * 0.3, 86)), add(wr, (4, 5)), wr, 12)
    poly = left + [lerp(bl, br, t) for t in (0.25, 0.5, 0.75)] + right
    skirt = poly_mask(poly)
    cx0 = (wl[0] + wr[0]) / 2

    def fold(x, y):
        t = max(0.0, min(1.0, (y - wl[1]) / 20))
        cx = cx0 + (((bl[0] + br[0]) / 2) - cx0) * t
        return (0.6 * math.sin((x + .5 - cx) * 0.7 + ph * 0.6) * (0.3 + t), -0.05)
    Ly.paint(n_plate(skirt, bevel=6, tilt=(0.0, -0.05), strength=1.3, fold=fold), "K")
    spec = [(0.1, 21, 3.4, -9), (0.45, 27, 4.8, -13), (0.82, 24, 3.8, -8), (0.28, 14, 1.8, -5), (0.64, 17, 2.1, -5)]
    tips = []
    for i, (t, L, r0, drift) in enumerate(spec):
        r = add(lerp(bl, br, t), (0, -4))
        L = L - (1 if (i + int(ph)) % 2 else 0)
        sw = 2.0 * math.sin(ph * 1.3 + i * 2.1)
        end = add(r, (drift - tr * (0.8 + 0.1 * i) + sw, L))
        c1 = add(r, (2.0 + 1.5 * math.sin(ph + i), L * 0.45))
        c2 = add(end, (4 + 2.0 * math.sin(ph * 1.1 + i * 1.7) + tr * 0.3, -L * 0.35))
        pts = bezier(r, c1, c2, end, 18)
        Ly.paint(tube(pts, r0, 0.5), "K", ao=0)
        tips.append(end)
    info["tips"] = tips
    for i in (1, 2):
        e = tips[i]
        dy = 3 + int(2 + 2 * math.sin(ph * 2 + i)) % 3
        c = add(e, (0.3 - tr * 0.1, dy))
        if c[1] < 114:
            Ly.paint(n_dome(c, 1.1, 1.5), "K", ao=0)
    for k, (c, a, sz) in enumerate(((U((51, 87)), -18, (6, 4.5)), (X((63 - tr * 0.3, 93)), 24, (5, 4)))):
        pts = page_quad(c, a, *sz)
        m = poly_mask(pts) & skirt
        Ly.paint(n_plate(m, bevel=1.2, tilt=(-0.1 + 0.2 * k, -0.2), strength=0.6), "P", bias=-1)
        low = {q for q in m if (q[0], q[1] + 1) not in m or (q[0] + q[1]) % 5 == 0 and (q[0], q[1] + 2) not in m}
        Ly.decal(low, ("K", 1))
        Ly.decal([ipt(add(c, rot((dx, -0.5), a))) for dx in (-1.5, 0, 1.5)], ("P", 2))
    return skirt


def draw_torso(Ly, j, p, info):
    """Chest (with a torn cavity of page-ribs around a glyph heart) + a dripping cowl-mantle over the shoulders."""
    U, ph, phase = j["U"], p["ph"], p["phase"]
    tor = poly_mask([U(q) for q in ((45, 49), (42, 57), (46, 68), (51, 81), (65, 81), (70, 68), (74.5, 57),
                                    (72, 49))])
    Ly.paint(n_plate(tor, bevel=5, tilt=(0.0, -0.05), strength=1.3), "K")
    cc = U((58.5, 67))
    RX, RY = 6.8, 10.0
    cav_pts = []
    for i in range(28):
        a = 2 * math.pi * i / 28
        jag = 0.8 * (hash01(i, 3, 11) - 0.5) + (0.9 if i % 3 == 0 else 0)
        cav_pts.append(add(cc, rot(((RX + jag) * math.cos(a), (RY + jag) * math.sin(a)), p["lean"])))
    cav = poly_mask(cav_pts) & tor
    core, hi, mid, halo, deep = GLYPH[phase]
    for q in cav:
        d = math.hypot((q[0] + .5 - cc[0]) / RX, (q[1] + .5 - cc[1]) / RY)
        Ly.fill([q], "K0" if d > 0.62 else ("V0" if phase == 1 else "C0") if d > 0.3 else
                ("V1" if phase == 1 else "C1"))
    lip = {(x, y) for (x, y) in tor - cav if any((x + a, y + b) in cav for a, b in ((-1, 0), (0, -1), (-1, -1)))}
    Ly.decal(lip, ("K", 3))
    F = FX()
    glyph(F, RUNE5[2], add(cc, (0, 1)), phase)
    for q, c in F.px.items():
        if q in cav:
            Ly.fill([q], c)
    info["heart"] = add(cc, (0, 1))
    s0, s1 = U((58.5, 57)), U((58.5, 77))
    spine = set(line(s0, s1)) | set(line(add(s0, (1, 0)), add(s1, (1, 0))))
    Ly.paint({q: (-0.5, 0, 0.85) if q[0] <= round(s0[0]) else (0.3, 0, 0.9) for q in spine}, "P", bias=-2, ao=0)
    Ly.decal([q for q in spine if q[1] % 4 == 0], ("G", 3))
    for k in range(4):
        y0 = 59 + k * 4.2
        for sgn in (-1, 1):
            w = 7.2 - abs(k - 1.2) * 0.6
            a = U((58.5 + sgn * 1.2, y0))
            pts = bezier(a, U((58.5 + sgn * 4, y0 - 1.8)), U((58.5 + sgn * (w + 0.8), y0 + 0.5)),
                         U((58.5 + sgn * (w - 0.3), y0 + 3.4)), 10)
            nm = tube(pts, 1.05, 0.65)
            Ly.paint(nm, "P", bias=0 if sgn < 0 else -1, ao=1)
            Ly.decal([ipt(q) for q in pts[3:8:2]], ("P", 2))
    # cowl-mantle: wide drape off the shoulders, ragged hanging tatters at the sides, drips along the hem
    lift = p["cowl_lift"]
    top = [U(q) for q in ((52, 38), (44, 42), (37.5, 47.5), (34.5, 54))]
    edge = []
    N = 16
    for i in range(N + 1):
        t = i / N
        x = 34 + 53 * t
        side = abs(2 * t - 1)                       # 1 at the flanks, 0 in the middle
        y = 57 + 9 * side ** 3 - lift * (1 - side) - 4.5 * (1 - side) ** 2
        y += (3.2 * hash01(i, 1, 31) if i % 2 else -0.5) * (0.4 + side) + 0.9 * math.sin(i * 1.9 + ph)
        edge.append(U((x, y)))
    rside = [U(q) for q in ((87.5, 60 - lift), (85, 50), (79, 43), (70, 39))]
    cowl = poly_mask(top + edge + rside)

    def cfold(x, y):
        return (0.45 * math.sin((x + .5 - j["head"][0]) * 0.5 + 0.6), -0.05)
    Ly.paint(n_plate(cowl, bevel=6, tilt=(0.0, -0.12), strength=1.4, fold=cfold), "K")
    for i, t in enumerate((0.06, 0.2, 0.38, 0.62, 0.78, 0.95)):
        base = edge[int(round(t * N))]
        ln = 2.5 + 4.5 * hash01(i, 7, 3) + 1.2 * math.sin(ph * 2 + i)
        end = add(base, (0, ln))
        Ly.paint(tube([add(base, (0, -1)), end], 1.1, 0.7), "K", ao=0)
        Ly.paint(n_dome(add(end, (0, 0.6)), 1.25, 1.4), "K", ao=0)
    info["cowl"] = cowl
    return tor | cowl


def hood_pts(j, p):
    c, a = j["head"], j["hang"]
    rel = ((-12, 17), (-15.5, 7), (-16, -3), (-12.5, -12), (-6, -18), (2, -20.5), (9, -19.5), (14.5, -16),
           (18.5, -10.5), (21.5, -4), (21, -1), (18.5, -1.5), (15.5, -4.5), (15.5, 1), (15.5, 9), (13, 15.5), (6, 19))
    return [add(c, rot(q, a)) for q in rel]


def face_frame(j, p):
    c, a = j["head"], j["hang"]
    return (lambda q: add(c, rot(add(q, (6, 3)), a))), a


def draw_hood(Ly, j, p, info):
    c = j["head"]
    hm = poly_mask(hood_pts(j, p))

    def fold(x, y):
        dx, dy = x + .5 - c[0], y + .5 - c[1]
        return (0.0, 0.0)
    Ly.paint(n_plate(hm, bevel=8, tilt=(-0.05, -0.05), strength=1.45, fold=fold), "K")
    F, a = face_frame(j, p)
    op = poly_mask(ellipse_pts(F((0, 0)), 8.2, 11.8, a - 6, 48)) & hm
    Ly.fill(op, "K0")
    lip = {q for q in hm - op if any((q[0] + dx, q[1]) in op for dx in (1, 2)) and q[0] < F((0, 0))[0]}
    Ly.decal(lip, ("K", 4))
    Ly.decal({q for q in lip if q[1] < F((0, -5))[1]}, "K5")
    # drape creases running from the crown to the back hem
    for off in (0, 4):
        cr = [add(c, rot((q[0] + off * 0.6, q[1] + off), j["hang"])) for q in ((-4, -13), (-8, -6), (-10, 3), (-9, 12))]
        Ly.decal([q for q in polyline(cr) if q in hm], ("K", 1))
    # wet specular streak along the crown of the hood
    crown = [add(c, rot(q, j["hang"])) for q in ((-12, -6), (-10, -11), (-6, -15), (-1, -17))]
    Ly.decal([q for q in polyline(crown) if q in hm], "K4")
    Ly.decal([ipt(add(c, rot((-9, -12), j["hang"]))), ipt(add(c, rot((-8, -13), j["hang"])))], "K5")
    info["hood"] = hm
    info["opening"] = op
    return hm


def draw_face(Ly, G, j, p, info):
    """The blank open book that is its face.  Phase 2: torn down the spine, a burning maw between halves."""
    F, a = face_frame(j, p)
    phase = p["phase"]
    torn = phase == 2
    gap = 1.6 if torn else 0.0
    # cover (ink-soaked leather) peeking out behind the pages
    cov = poly_mask([F(q) for q in ((-7.2 - gap, -7), (-0.5, -5.5), (0.5, -5.5), (6.8 + gap, -7.5),
                                    (6.8 + gap, 6.8), (0.5, 8.4), (-0.5, 8.4), (-7.2 - gap, 6.5))])
    Ly.paint(n_plate(cov, bevel=1.5, strength=0.8), "K", bias=1)
    Lp = [F(q) for q in ((-gap, -5.2), (-3, -7.6), (-6.5, -7.2), (-6.5, 5.8), (-3, 5.9), (-gap, 7.4))]
    Rp = [F(q) for q in ((gap, -5.2), (3, -7.8), (6, -7.6), (6, 5.5), (3, 5.8), (gap, 7.4))]
    if torn:  # ragged torn inner edges
        Lp = Lp[1:5] + [F((-gap - 0.6 * (k % 2), 5 - k * 2.3)) for k in range(6)]
        Rp = [F((gap + 0.7 * (k % 2), -5 + k * 2.3)) for k in range(6)] + Rp[1:5][::-1][::-1]
        Rp = [F((gap + 0.7 * (k % 2), -5 + k * 2.3)) for k in range(6)] + [F(q) for q in ((3, 5.8), (6, 5.5), (6, -7.6), (3, -7.8))]
    lm, rm = poly_mask(Lp), poly_mask(Rp)
    Ly.paint(n_plate(lm, bevel=2.2, tilt=(-0.25, -0.2), strength=0.9), "P", ao=0)
    Ly.paint(n_plate(rm, bevel=2.2, tilt=(0.2, -0.05), strength=0.9), "P", ao=0)
    # page-stack edges along the bottom + gutter shadow at the spine
    for m in (lm, rm):
        bot = {q for q in m if (q[0], q[1] + 1) not in m}
        Ly.decal(bot, ("P", 2))
        Ly.decal({(x, y - 1) for (x, y) in bot if x % 2 == 0}, ("P", 3))
    sp = F((0, 0))[0]
    Ly.decal({q for q in lm | rm if abs(q[0] + .5 - sp) < 1.6 + gap}, ("P", 2))
    Ly.decal({q for q in lm | rm if abs(q[0] + .5 - sp) < 0.8 + gap}, ("P", 1))
    # ghost ruling: the pages are blank, but the ruled lines remain
    for yy in (-4, -1.5, 3):
        Ly.decal([ipt(F((x, yy))) for x in (-5, -4, 2.5, 3.5, 4.5)], ("P", 3), only_on=("P",))
    eyes = [F((-3.2, -1.2)), F((3.2, -1.6))]
    core, hi, mid, halo, deep = GLYPH[phase]
    for k, e in enumerate(eyes):
        # ink tears bleeding down from each glyph-eye
        tear = [ipt(add(e, (0.2 * k, t))) for t in range(2, 6 - k)]
        Ly.decal(tear, ("K", 2))
        Ly.decal([tear[-1], add(tear[-1], (1, 0))], ("K", 1))
    if torn:
        # burning maw between the torn halves
        mid_c = F((0, 0.5))
        maw = poly_mask([F(q) for q in ((-gap - 0.3, -6), (gap + 0.3, -6), (gap + 0.6, 7.5), (-gap - 0.6, 7.5))])
        maw -= lm | rm
        for q in maw:
            dx = abs(q[0] + .5 - mid_c[0])
            G.put([q], "C5" if dx < 0.8 else "C4" if dx < 1.6 else "C3")
        # charred / burning torn edges
        for m in (lm, rm):
            te = {q for q in m if any((q[0] + dx, q[1]) in maw or (q[0] + dx, q[1]) not in m and
                                      abs(q[0] + dx + .5 - sp) < 2.5 for dx in (-1, 1))}
            Ly.decal(te, "C3")
            Ly.decal({(x - (1 if x < sp else -1), y) for (x, y) in te}, ("P", 1))
        # extra crimson script crawling over the pages
        for k in range(9):
            q = ipt(F((-6 + hash01(k, 1, 9) * 12, -6 + hash01(k, 2, 9) * 11)))
            if q in lm or q in rm:
                G.put([q], "C2" if k % 2 else "C3", over=False)
    for k, e in enumerate(eyes):
        glyph(G, RUNE3[1], e, phase)
        G.put([ipt(e)], core)
    info["eyes"] = eyes
    info["book"] = lm | rm | cov


def draw_arm(Ly, j, p, side, info):
    """Long ink arm: upper arm, forearm with a tattered dripping sleeve, palm, four quill-nib claws + thumb."""
    X = j["X"]
    a = p["fa" if side == "f" else "ba"]
    s = j["sf" if side == "f" else "sb"]
    e, w = X(a["e"]), X(a["w"])
    bias = 0 if side == "f" else -1
    # tattered sleeve: ragged ink fringe hanging off the forearm (gravity + a little outward)
    outward = 1 if w[0] > j["waist"][0] else -1
    fl = [lerp(e, w, 0.05 + 0.8 * i / 7) for i in range(8)]
    hang = []
    for i, q in enumerate(fl):
        ln = 4 + 5 * hash01(i, 5, 7 + (side == "f")) + (3 if i % 2 == 0 else 0) - i * 0.3
        sway = 1.3 * math.sin(p["ph"] + i) - p["trail"] * 0.15
        hang.append(add(q, (sway + outward * ln * 0.35, ln)))
    sl = poly_mask([add(fl[0], (0, -1))] + hang + [add(fl[-1], (0, -1))])
    if len(sl) > 3:
        Ly.paint(n_plate(sl, bevel=2, tilt=(0.05, 0.1), strength=1.1,
                         fold=lambda x, y: (0.5 * math.sin(x * 1.3 + p["ph"]), 0)), "K", bias=bias - 1)
    Ly.paint(n_capsule(s, e, 3.4, 2.3), "K", bias=bias)
    Ly.paint(n_dome(e, 2.4, 2.4), "K", bias=bias, ao=0)
    Ly.paint(n_capsule(e, w, 2.3, 1.6), "K", bias=bias)
    fwd = unit(sub(w, e))
    palm = add(w, mul(fwd, 1.6))
    Ly.paint(n_dome(palm, 2.5, 2.3), "K", bias=bias, ao=0)
    tips = []
    l1, l2 = a["l"]
    fingers = [(ang, 1.0) for ang in a["fing"]] + [(a["thumb"], 0.55)]
    for idx, (ang, sc) in enumerate(fingers):
        p0 = add(palm, mul(dirv(ang), 1.8))
        p1 = add(p0, mul(dirv(ang), l1 * sc))
        p2 = add(p1, mul(dirv(ang + a["curl"]), l2 * sc))
        Ly.paint(n_capsule(p0, p1, 0.95, 0.75), "K", bias=bias, ao=1)
        Ly.paint(n_dome(p1, 1.05), "K", bias=bias, ao=0)
        Ly.paint(n_capsule(p1, p2, 0.75, 0.6), "K", bias=bias, ao=1)
        # brass quill nib
        d = dirv(ang + a["curl"] * (1.5 if sc == 1 else 1.2))
        nl = 5.2 if sc == 1 else 3.2
        nx = (-d[1], d[0])
        base = add(p2, mul(d, -0.4))
        tip = add(p2, mul(d, nl))
        nib = poly_mask([add(base, mul(nx, 1.5)), add(lerp(base, tip, 0.4), mul(nx, 1.35)), tip,
                         add(lerp(base, tip, 0.4), mul(nx, -1.35)), add(base, mul(nx, -1.5))])
        Ly.paint(n_plate(nib, bevel=1.3, tilt=(-nx[0] * 0.35, -nx[1] * 0.35 - 0.2), strength=0.9), "G",
                 bias=bias, ao=1)
        Ly.decal([ipt(lerp(base, tip, t)) for t in (0.55, 0.75)], ("G", 1))
        Ly.decal([ipt(lerp(base, tip, 0.3))], ("G", 0))
        tips.append(tip)
    info["tips_" + side] = tips
    info["palm_" + side] = palm
    return palm


# =========================================================================== FX
def fx_glyph_ring(Fb, F, c, r, rotd, phase, n_runes=6):
    """Rotating glyph circle around a hand: outer gold ring, inner dashed ring, runes riding the band."""
    core, hi, mid, halo, deep = GLYPH[phase]
    ring, ring2 = set(), set()
    for i in range(int(2 * math.pi * r * 1.6)):
        t = 2 * math.pi * i / int(2 * math.pi * r * 1.6)
        ring.add(ipt(add(c, (r * math.cos(t) + .5, r * math.sin(t) + .5))))
        if (i // 3) % 2 == 0:
            ring2.add(ipt(add(c, ((r - 4.5) * math.cos(t) + .5, (r - 4.5) * math.sin(t) + .5))))
    outer = {ipt(add(c, ((r + 1) * math.cos(t) + .5, (r + 1) * math.sin(t) + .5)))
             for t in [2 * math.pi * i / 90 for i in range(90)]} - ring
    Fb.put(outer, halo)
    Fb.put(ring, mid)
    Fb.put([q for q in ring if hash01(q[0], q[1], 4) < 0.35], hi)
    Fb.put(ring2, halo)
    for k in range(n_runes):
        ang = rotd + k * 360 / n_runes
        q = add(c, mul(dirv(ang), r - 2.3))
        glyph(Fb, RUNE3[k % len(RUNE3)], q, phase, bright=k % 2 == 0)
    # a few runes already peeling off the ring (the barrage)
    for k in range(2):
        ang = rotd + 25 + k * 180
        q = add(c, mul(dirv(ang), r + 4 + k * 2))
        glyph(F, RUNE3[(k + 2) % len(RUNE3)], q, phase)


def fx_barrage(F, Fb, j, p, info):
    ph = p["phase"]
    fa, ba = info["palm_f"], info["palm_b"]
    X = j["X"]
    for side, rotd, nr in (("fa", 10, 7), ("ba", -20, 6)):
        a = p[side]
        cen = add(info["palm_" + side[0]], mul(unit(sub(X(a["w"]), X(a["e"]))), 3.5))
        fx_glyph_ring(Fb, F, cen, a["ring"], rotd, ph, nr)
    # a crown of large runes gathering over the hood, about to rain
    hc = j["head"]
    for k, ang in enumerate((-162, -132, -48, -18)):
        q = add(add(hc, (3, 12)), (math.cos(math.radians(ang)) * 34, math.sin(math.radians(ang)) * 24))
        glyph(F, RUNE5[k % len(RUNE5)], q, ph, bright=k % 2 == 0)
        tr = sub(q, mul(unit(sub(q, hc)), 4))
        F.put([ipt(tr)], "V1", over=False)


def fx_smear(Ly, F, j, p, info):
    """Quill slash: four nib-trails arcing down from overhead to the claws, fused by a wet ink smear."""
    c = j["sf"]
    tips = info["tips_f"][:4]
    palm = info["palm_f"]
    tang = [math.degrees(math.atan2(t[1] - c[1], t[0] - c[0])) for t in tips]
    rads = [math.hypot(*sub(t, c)) for t in tips]
    a1 = max(tang) - 4
    a0 = a1 - 100
    r_out = max(rads) + 1.5
    r_in = math.hypot(*sub(palm, c)) - 3
    body = {}
    for y in range(H):
        for x in range(W):
            dx, dy = x + .5 - c[0], y + .5 - c[1]
            r = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dy, dx))
            if ang < a0 - 180:
                ang += 360
            if not (a0 <= ang <= a1):
                continue
            t = (ang - a0) / (a1 - a0)                 # 0 = tail, 1 = leading edge
            lo = min(r_out - 3 - (r_out - 3 - r_in) * t ** 0.55, r_out - 15)
            hi = r_out - 1.2 * (1 - t) ** 2
            if lo <= r <= hi:
                body[(x, y)] = (t, (r - lo) / max(0.5, hi - lo), r)
    srad = [r_out - 1.5 - i * 3.6 for i in range(4)]
    rads = srad
    for q, (t, u, r) in list(body.items()):
        # the tail of the smear breaks into four separate claw streaks
        if t < 0.5 and min(abs(r - rr) for rr in srad) > 0.9 + 2.0 * (t / 0.5) ** 2:
            del body[q]
            continue
        Ly.fill([q], "K2" if u < 0.3 else "K3" if u < 0.75 or t < 0.6 else "K4")
    # glyph-ink nib trails at each claw's radius (brighter toward the hand)
    for i, rr in enumerate(sorted(rads)):
        n = 220
        for k in range(n):
            t = k / (n - 1)
            if t < 0.03 + i * 0.05:
                continue
            ang = math.radians(a0 + (a1 - a0) * t)
            q = ipt(add(c, (rr * math.cos(ang) + .5, rr * math.sin(ang) + .5)))
            if q in body:
                Ly.fill([q], "Y2" if t > 0.9 and i == 0 else "V3" if t > 0.62 else "V2" if t > 0.3 else "V1")
    # wet outer rim + leading-edge highlight
    for q, (t, u, r) in body.items():
        if r > r_out - 1.6 and t > 0.3:
            Ly.fill([q], "K4" if t < 0.75 else "K5")
    # flung ink droplets off the leading edge (tangential)
    for k in range(8):
        ang = math.radians(a1 - 4 - k * 11)
        rr = r_out + 2 + hash01(k, 1, 2) * 4
        q = add(c, (rr * math.cos(ang), rr * math.sin(ang)))
        if inb(*ipt(q)):
            Ly.fill(mask_disc(q, 0.8 + 0.6 * (k % 2)), "K2")
            Ly.fill([ipt(add(q, (-.4, -.4)))], "K5" if k % 2 else "V2")


def page_quad(c, ang, w, h):
    return [add(c, rot(v, ang)) for v in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


PAGE_SLOTS = [  # (x, y, rotation, size, front?) -- a hand-placed vortex around the body
    (16, 30, -30, 1.0, 1), (34, 14, 18, 0.85, 0), (90, 12, -12, 0.95, 1), (110, 30, 38, 1.1, 1),
    (116, 60, -22, 1.0, 1), (9, 58, 46, 1.05, 1), (14, 92, -8, 0.95, 1), (104, 90, 24, 1.1, 1),
    (84, 40, 5, 0.8, 0), (36, 44, -40, 0.8, 0), (62, 104, 60, 0.9, 1), (48, 8, -60, 0.75, 1)]


def fx_pages(Lb, Lf, F, j, p, info):
    """Phase 2: loose pages whirling around the body (counter-clockwise vortex), corners burning."""
    c = j["U"]((58, 62))
    rotd = p["ph"] * 12
    for k, (x, y, ang, sc, front) in enumerate(PAGE_SLOTS):
        q = add(rot_about(j["X"]((x, y)), c, rotd * (0.6 if front else 1)), (0, 0))
        quad = page_quad(q, ang + rotd * 3, 8 * sc, 6 * sc)
        m = poly_mask(quad)
        L = Lf if front else Lb
        tilt = (math.cos(math.radians(ang * 2 + k * 40)) * 0.45, -0.25 + 0.3 * math.sin(k * 2.3))
        L.paint(n_plate(m, bevel=1.6, tilt=tilt, strength=0.7), "P", bias=0 if front else -1, ao=0)
        for yy in (-1.2, 0.8):
            L.decal([ipt(add(q, rot((dx, yy), ang))) for dx in (-2, -1, 1, 2) if (dx + k + int(yy)) % 3],
                    ("P", 2))
        corner = quad[k % 4]
        dist = lambda r: math.hypot(r[0] + .5 - corner[0], r[1] + .5 - corner[1])
        burn = {r for r in m if dist(r) < 2.6 * sc}
        L.decal({r for r in m - burn if dist(r) < 3.6 * sc}, ("P", 1))
        L.decal(burn, "C3")
        L.decal({r for r in burn if dist(r) < 1.4 * sc}, "C5")
        # motion streak trailing behind (vortex turns counter-clockwise on screen)
        rv = sub(q, c)
        tang = unit((rv[1], -rv[0]))
        for s_ in range(1, 5):
            t2 = add(q, mul(tang, -(4 + 2.2 * s_) * sc))
            t2 = add(t2, mul(unit(rv), -0.25 * s_ * s_))
            F.put([ipt(t2)], "C3" if s_ == 1 else "C2" if s_ == 2 else "C1", over=False)


def flame_tongue(F, base, h, w, lean, body_mask, seed):
    """One teardrop flame: dark-crimson rim, hot core, curling tip."""
    tip = add(base, (lean * h, -h))
    side = []
    n = 10
    for i in range(n + 1):
        t = i / n
        c = lerp(base, tip, t)
        c = (c[0] + math.sin(t * 4.0 + seed) * 1.8 * t * t, c[1])
        ww = w * (math.sin(math.pi * min(1, t * 1.35 + 0.1)) ** 0.9) * (1 - t) ** 0.35 * 0.5 + 0.2
        side.append((c, ww))
    poly = [(c[0] - ww, c[1]) for c, ww in side] + [(c[0] + ww, c[1]) for c, ww in reversed(side)]
    m = poly_mask(poly)
    for q in m:
        t = max(0.0, min(1.0, (base[1] - (q[1] + .5)) / h))
        c, ww = side[min(n, int(t * n + .5))]
        e = abs(q[0] + .5 - c[0]) / max(0.6, ww)
        col = "C2" if e > 0.7 or t > 0.9 else "C3" if e > 0.35 or t > 0.7 else "C4" if t > 0.25 else "C5"
        if q not in body_mask or t < 0.2:
            F.put([q], col, over=True)
    for (x, y) in m:
        for a, b in ((1, 0), (-1, 0), (0, -1)):
            r = (x + a, y + b)
            if r not in m and r not in body_mask and r not in F.px:
                F.put([r], "C0")


def fx_burn(img, F, body_mask, j, p):
    """Phase 2: the ink is on fire -- crimson flame tongues licking up from hood & shoulders, embers."""
    tops = sorted((x, y) for (x, y) in body_mask if (x, y - 1) not in body_mask and (x, y - 2) not in body_mask)
    placed = []
    for (x, y) in tops:
        if y > 64 or hash01(x, y, 21) > 0.4:
            continue
        if any(abs(x - a) < 9 and abs(y - b) < 12 for a, b in placed):
            continue
        placed.append((x, y))
        big = y < 60
        h = (8 + 9 * hash01(x, 0, 22)) if y < 40 else (6 + 6 * hash01(x, 0, 22))
        w = 5.5 + 1.5 * hash01(x, 1, 22)
        h = min(h, y + 1)
        flame_tongue(F, (x + .5, y + 2.5), h + 1, w, -0.25 - 0.2 * hash01(x, y, 25), body_mask, x * 0.7)
    for (x, y) in tops:
        if y < 70 and hash01(x, y, 23) < 0.6:
            F.put([(x, y)], "C2", over=False)
    for k in range(24):
        x = int(14 + hash01(k, 1, 24) * 100)
        y = int(3 + hash01(k, 2, 24) * 70)
        if (x, y) not in body_mask and (x + 1, y) not in body_mask:
            F.put([(x, y)], "C4" if k % 3 else "C5", over=False)


def crack_veins(Ly, pts_mask, seed, n, start_region):
    """Burning veins in the ink (phase 2)."""
    for k in range(n):
        cand = sorted(start_region, key=lambda q: hash01(q[0], q[1], seed + k))
        if not cand:
            return
        x, y = cand[0]
        ang = hash01(k, 3, seed) * 360
        path = []
        for i in range(9):
            ang += (hash01(k, i, seed + 5) - 0.5) * 70
            x += math.cos(math.radians(ang)) * 1.4
            y += math.sin(math.radians(ang)) * 1.4 + 0.5
            path.append(ipt((x, y)))
        pl = polyline(path)
        Ly.decal([q for q in pl if q in pts_mask], "C2")
        Ly.decal([q for q in pl[len(pl) // 4: len(pl) // 2] if q in pts_mask], "C3")


# =========================================================================== render
ORDER = ["PagesBack", "BackArm", "Tail", "Torso", "Hood", "Face", "Smear", "FrontArm", "PagesFront"]


def render(p):
    L = {k: Layer(k) for k in ORDER}
    G, F, Fb = FX(), FX(), FX()
    j = joints(p)
    info = {}
    skirt = draw_tail(L["Tail"], j, p, info)
    body = draw_torso(L["Torso"], j, p, info)
    hood = draw_hood(L["Hood"], j, p, info)
    draw_face(L["Face"], G, j, p, info)
    draw_arm(L["BackArm"], j, p, "b", info)
    draw_arm(L["FrontArm"], j, p, "f", info)
    if p["phase"] == 2:
        for nm, seed, n in (("Hood", 30, 3), ("Torso", 40, 4), ("Tail", 50, 4)):
            m = set(L[nm].px)
            region = {q for q in m if L[nm].px[q][0] == "K" and L[nm].px[q][3] is None}
            crack_veins(L[nm], region, seed, max(1, n - 2), region)
    if "barrage" in p["fx"]:
        fx_barrage(F, Fb, j, p, info)
    if "smear" in p["fx"]:
        fx_smear(L["Smear"], F, j, p, info)
    if "pages" in p["fx"]:
        fx_pages(L["PagesBack"], L["PagesFront"], F, j, p, info)
        # inverted (crimson) glyphs drifting loose behind it
        for k, q in enumerate(((22, 30), (100, 22), (14, 62), (110, 50), (30, 96), (96, 100))):
            glyph(Fb, RUNE5[k % len(RUNE5)] if k < 2 else RUNE3[k % len(RUNE3)], j["X"](q), 2, bright=k % 2 == 0)
    gcol = GLYPH[p["phase"]]
    glows = [(e, 9, gcol[3], gcol[4]) for e in info["eyes"]] + [(info["heart"], 9, gcol[4], gcol[4])]
    if "barrage" in p["fx"]:
        glows += [(info["palm_f"], 16, gcol[2], gcol[3]), (info["palm_b"], 14, gcol[2], gcol[3])]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(Fb.image())
    body_mask = set()
    for k in ORDER:
        if not L[k].px:
            continue
        remap = {"K5": "C4", "K4": "C2"} if p["phase"] == 2 and k in ("Hood", "Torso", "Tail") else None
        li = render_layer(L[k], glows if k not in ("Face", "Smear") else (), remap=remap)
        img.alpha_composite(li)
        if k not in ("PagesBack", "PagesFront", "Smear"):
            body_mask |= set(L[k].px)
        if k == "Face":
            img.alpha_composite(G.image())
    if "burn" in p["fx"]:
        fx_burn(img, F, body_mask, j, p)
    img.alpha_composite(F.image())
    return img


# =========================================================================== sheet
BG = (0x1a, 0x16, 0x20, 255)


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
    poses = [("IDLE", pose_idle(0)), ("IDLE 2 (bob)", pose_idle(1)), ("GLYPH BARRAGE", pose_barrage()),
             ("QUILL SLASH", pose_slash()), ("PHASE 2", pose_p2())]
    frames = [(n, render(p)) for n, p in poses]
    pl = player_frame()
    gap, mar, top = 14, 20, 34
    pw = 44 * S
    Wd = mar * 2 + pw + len(frames) * W * S + (len(frames) - 1) * gap
    Hd = top + H * S + 30
    sheet = Image.new("RGBA", (Wd, Hd), BG)
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=15)
        small = ImageFont.load_default(size=11)
    except Exception:
        font = small = ImageFont.load_default()
    floor = top + H * S
    x = mar
    # player for scale (feet on the arena floor, facing the boss)
    if pl is not None:
        crop = pl.crop((8, 0, 52, 40))
        sheet.alpha_composite(crop.resize((44 * S, 40 * S), Image.NEAREST), (x, floor - 40 * S))
        dr.text((x + 4, top - 22), "KNIGHT (scale)", fill=(150, 140, 165), font=font)
    x += pw
    for i, (name, im) in enumerate(frames):
        dr.rectangle([x - 1, top - 1, x + W * S, top + H * S], outline=(40, 34, 50))
        sheet.alpha_composite(im.resize((W * S, H * S), Image.NEAREST), (x, top))
        dr.text((x + 6, top - 22), name, fill=(210, 196, 160) if i != 4 else (230, 110, 90), font=font)
        x += W * S + gap
    dr.line([mar, floor, Wd - mar, floor], fill=(58, 48, 70), width=2)
    dr.text((mar, floor + 8), "The Unwritten -- concept pass, 128x128 frames @3x.  Hem floats ~10px above the floor.",
            fill=(120, 110, 135), font=small)
    out = os.path.join(HERE, "unwritten.png")
    sheet.convert("RGB").save(out)
    # 4x close-up of the four key poses for detail review
    Z = 4
    cl = Image.new("RGBA", (W * Z * 4 + 36, H * Z), BG)
    for i, fi in enumerate((0, 2, 3, 4)):
        cl.alpha_composite(frames[fi][1].resize((W * Z, H * Z), Image.NEAREST), (i * (W * Z + 12), 0))
    cl.convert("RGB").save(os.path.join(HERE, "unwritten_closeup.png"))
    print("wrote", out)


if __name__ == "__main__":
    main()
