"""Shared toolkit for the enemy generators (gen_enemies.py).

Same method as gen_boss.py, scaled down for 14-50px creatures:
  * every body part is a mask with a per-pixel surface normal (capsules, domes, bevelled plates);
  * a hue-shifted material ramp is picked from N.L (light from the upper-left);
  * decals (seams, rust, trim, runes) recolour pixels on top; contact AO between parts;
  * each Aseprite layer gets its own 1px sel-out outline.
A `Rig` maps upright "model" coordinates through an optional rotation (used for falls/tilts),
so poses can be keyed as joints and whole bodies can topple over convincingly.
"""
import json, math, os, sys, heapq
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

W = H = 0


def setup(w, h):
    global W, H
    W, H = w, h


# =========================================================================== palette
HEX = {
    "OUT": "#0b080c",
    # rusty dark iron (warm grey)
    "I0": "#141118", "I1": "#26212a", "I2": "#3d363d", "I3": "#5b5253", "I4": "#857a73", "I5": "#bdb2a4",
    # black plate (cool violet-black)
    "K0": "#0d0b11", "K1": "#1a1720", "K2": "#2a2533", "K3": "#3e3749", "K4": "#5d556a", "K5": "#968ea6",
    # tarnished gold
    "G0": "#2b1a0e", "G1": "#4f3314", "G2": "#7d5519", "G3": "#b2822a", "G4": "#dfb24a", "G5": "#fbe7a0",
    # crimson cloth
    "C0": "#1a0712", "C1": "#320d1c", "C2": "#541424", "C3": "#7c1f2a", "C4": "#a1342f", "C5": "#c45a3a",
    # rust
    "R0": "#24100c", "R1": "#461c11", "R2": "#6e2d16", "R3": "#98441c", "R4": "#c0652a",
    # bone
    "B0": "#2a231f", "B1": "#4a3f35", "B2": "#75664f", "B3": "#a39274", "B4": "#cdbf9d", "B5": "#eee4c6",
    # ash (desiccated skin)
    "A0": "#1e1a1e", "A1": "#37302f", "A2": "#564c49", "A3": "#7a6d66", "A4": "#a39485",
    # faded olive tabard
    "T0": "#16140e", "T1": "#2a2617", "T2": "#423b22", "T3": "#5d532e", "T4": "#7c703c",
    # leather
    "L0": "#170f0c", "L1": "#2b1d17", "L2": "#433026", "L3": "#604535", "L4": "#7f5f48",
    # rot-green chitin
    "V0": "#0f150e", "V1": "#1b2715", "V2": "#2c3d1c", "V3": "#435725", "V4": "#62762d", "V5": "#8c9a3e",
    # rot-orange glow (fixed colours)
    "O0": "#4a1a08", "O1": "#8a330d", "O2": "#cc5a14", "O3": "#f58a24", "O4": "#ffc04f", "O5": "#fff0b0",
    # molten gold glow
    "Y0": "#ff8a1f", "Y1": "#ffc14a", "Y2": "#ffe890", "Y3": "#fffbe8",
    # moth / gloom violet-grey
    "M0": "#120f1a", "M1": "#211b2e", "M2": "#342c45", "M3": "#4e4561", "M4": "#736985", "M5": "#a198ad",
    # ghost teal glow (fixed)
    "Q0": "#10403f", "Q1": "#1f7a70", "Q2": "#4fbfa8", "Q3": "#a2f0dc", "Q4": "#eafff8",
    # moss-grey hood
    "D0": "#121410", "D1": "#1f231b", "D2": "#2f3527", "D3": "#444c36", "D4": "#5f6947",
    # wood
    "W0": "#1a110c", "W1": "#2e1f16", "W2": "#4a3222", "W3": "#694830", "W4": "#8d6641",
    # pale ash cloth
    "P0": "#1f1c1f", "P1": "#353035", "P2": "#524b4d", "P3": "#756c69", "P4": "#9d948a", "P5": "#c7bfb0",
    # dead flesh
    "F0": "#1c1214", "F1": "#33201f", "F2": "#523430", "F3": "#764c41", "F4": "#9c6c58",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {}
for _k in HEX:
    if _k != "OUT":
        RAMP.setdefault(_k[0], []).append(_k)
SHINY = {"I": 0.95, "K": 0.95, "G": 0.9}
LIGHT = (-0.55, -0.68, 0.48)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)


# =========================================================================== geometry
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ip(p):
    return (int(math.floor(p[0])), int(math.floor(p[1])))


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
    x0, y0 = int(math.floor(a[0])), int(math.floor(a[1]))
    x1, y1 = int(math.floor(b[0])), int(math.floor(b[1]))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
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


def ik(s, h, l1, l2, pref):
    """Two-bone IK: joint position; pref = direction the joint should bulge towards."""
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


def basis(o, up):
    """Local frame: f(dx, dy) with +dx = 'forward' (right when upright), +dy = 'down' along the part."""
    l = math.hypot(*up) or 1.0
    dx_, dy_ = -up[0] / l, -up[1] / l
    rx, ry = dy_, -dx_
    return lambda a, b: (o[0] + rx * a + dx_ * b, o[1] + ry * a + dy_ * b)


def rot_pt(p, piv, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y = p[0] - piv[0], p[1] - piv[1]
    return (piv[0] + x * c - y * s, piv[1] + x * s + y * c)


def dirv(ang):
    return (math.cos(math.radians(ang)), math.sin(math.radians(ang)))


# ---------------------------------------------------------------- normal fields
def n_capsule(a, b, r0, r1=None, flat=1.0):
    r1 = r0 if r1 is None else r1
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-6
    R = max(r0, r1) + 1
    out = {}
    for y in range(int(math.floor(min(ay, by) - R)), int(max(ay, by) + R) + 2):
        for x in range(int(math.floor(min(ax, bx) - R)), int(max(ax, bx) + R) + 2):
            px, py = x + .5, y + .5
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
            qx, qy = ax + dx * t, ay + dy * t
            r = r0 + (r1 - r0) * t
            ox, oy = px - qx, py - qy
            d2 = ox * ox + oy * oy
            if d2 <= r * r:
                k = 1.0 / max(r, 0.3)
                nx, ny = ox * k * flat, oy * k * flat
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
    return out


def n_dome(c, rx, ry=None, flat=1.0, tilt=(0, 0)):
    ry = rx if ry is None else ry
    cx, cy = c
    out = {}
    for y in range(int(math.floor(cy - ry)) - 1, int(cy + ry) + 2):
        for x in range(int(math.floor(cx - rx)) - 1, int(cx + rx) + 2):
            ex, ey = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            e = ex * ex + ey * ey
            if e <= 1.0:
                nx, ny = ex * flat + tilt[0], ey * flat + tilt[1]
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.08, 1 - min(0.92, e) * flat * flat)))
    return out


def dist_field(mask):
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


def n_plate(mask, bevel=2.0, tilt=(0.0, 0.0), strength=1.2, fold=None):
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


def mask_disc(c, rx, ry=None):
    ry = rx if ry is None else ry
    cx, cy = c
    return {(x, y) for y in range(int(math.floor(cy - ry)) - 1, int(cy + ry) + 2)
            for x in range(int(math.floor(cx - rx)) - 1, int(cx + rx) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0}


# =========================================================================== layers
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}        # (x,y) -> [mat, n, bias, fixed, part]
        self.noout = set()  # pixels that never receive an outline (strings, wisps)
        self.part_n = 0

    def paint(self, normals, mat, bias=0, ao=1, clip=None):
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
            self.px[p] = [mat, normals[p], bias, None, pid]
        return new

    def fill(self, pts, color, noout=False):
        self.part_n += 1
        for p in pts:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color, self.part_n]
                if noout:
                    self.noout.add(p)

    def fixed(self, pixdict):
        self.part_n += 1
        for p, c in pixdict.items():
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, c, self.part_n]

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

    def erase(self, pts):
        for p in pts:
            self.px.pop(p, None)
            self.noout.discard(p)


def level_of(e, x, y):
    mat, n, bias, fixed = e[0], e[1], e[2], e[3]
    ramp = RAMP[mat]
    top = len(ramp) - 1
    if isinstance(fixed, tuple):
        return max(0, min(top, fixed[1] + (bias if bias < 0 else 0)))
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = min(1.0, 0.14 + 0.95 * max(0.0, ndl))
    f = v * (top - (1 if mat in SHINY else 0)) + 0.45
    i = int(f) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        if rz > SHINY[mat] and bias >= 0:
            i = top
        else:
            i = min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, outline=True):
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
    if outline:
        for (x, y) in layer.px:
            if (x, y) in layer.noout:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if not inb(*q) or q in layer.px:
                    continue
                e = layer.px[(x, y)]
                c = "OUT"
                if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 2:
                    c = RAMP[e[0]][1]   # sel-out: lit rim gets a dark coloured outline
                if pix[q][3] == 0 or c == "OUT":
                    pix[q] = RGBA[c]
    for p, c in col.items():
        pix[p] = RGBA[c]
    return img


class FXLayer:
    """Flat, un-outlined colour pixels (glows, smears, embers)."""
    def __init__(self, name):
        self.name = name
        self.px = {}

    def put(self, pts, c):
        for p in pts:
            if inb(*p):
                self.px[p] = c

    def image(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = RGBA[c]
        return img


# =========================================================================== rig
class Rig:
    """Maps upright model coordinates to the frame: rotate about piv by rot degrees, then offset."""
    def __init__(self, rot=0.0, piv=(0, 0), off=(0, 0), sx=1.0, sy=1.0):
        self.rot, self.piv, self.off, self.sx, self.sy = rot, piv, off, sx, sy
        self.c, self.s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def T(self, p):
        x, y = (p[0] - self.piv[0]) * self.sx, (p[1] - self.piv[1]) * self.sy
        return (self.piv[0] + x * self.c - y * self.s + self.off[0],
                self.piv[1] + x * self.s + y * self.c + self.off[1])

    def A(self, ang):
        if self.sy < 0:
            ang = -ang
        return ang + self.rot

    def pt(self, p):
        return ip(self.T(p))

    def cap(self, L, a, b, r0, r1=None, mat="I", bias=0, ao=1, flat=1.0, clip=None):
        return L.paint(n_capsule(self.T(a), self.T(b), r0, r1, flat), mat, bias, ao, clip)

    def dome(self, L, c, rx, ry=None, mat="I", bias=0, ao=1, flat=1.0, tilt=(0, 0), clip=None):
        ry = rx if ry is None else ry
        return L.paint(n_dome(self.T(c), rx * abs(self.sx), max(0.6, ry * abs(self.sy)), flat, tilt), mat, bias, ao, clip)

    def mask(self, pts):
        return poly_mask([self.T(p) for p in pts])

    def plate(self, L, pts, mat, bevel=1.5, tilt=(0, 0), strength=1.1, fold=None, bias=0, ao=1, minus=None):
        m = self.mask(pts)
        if minus:
            m -= minus
        L.paint(n_plate(m, bevel, tilt, strength, fold), mat, bias, ao)
        return m

    def decal(self, L, pts, color, only_on=None):
        L.decal([self.pt(p) for p in pts], color, only_on)

    def dline(self, L, a, b, color, only_on=None):
        pts = line(self.T(a), self.T(b))
        L.decal(pts, color, only_on)
        return pts


ID = Rig()


# ---------------------------------------------------------------- limbs
def leg(R, L, hip, foot, l1, l2, r_th, r_sh, mat, bias=0, pref=(1, -0.1), boot=None, flen=3.0,
        knee=None, toe=1, heel=1.6, boot_h=2.6):
    """Upright leg; foot = sole point (x at the ankle, y = floor row)."""
    fx, fy = foot
    ank = (fx, fy - 1.4)
    kn = knee or ik(hip, ank, l1, l2, pref)
    R.cap(L, hip, kn, r_th, r_sh * 1.05, mat, bias)
    R.cap(L, kn, ank, r_sh, r_sh * 0.9, mat, bias)
    if boot:
        R.cap(L, lerp(kn, ank, 0.5), ank, r_sh * 1.02, r_sh * 0.95, boot, bias, ao=0)
    sole = [(fx - heel * toe, fy + 1), (fx - heel * toe, fy - boot_h), (fx + 0.6 * toe, fy - boot_h - 0.3),
            (fx + flen * toe, fy - 1.0), (fx + flen * toe, fy + 1)]
    if toe < 0:
        sole = sole[::-1]
    R.plate(L, sole, boot or mat, bevel=1.0, tilt=(0, -0.35), bias=bias)
    return kn


def arm(R, L, sh, hand, l1, l2, r1, r2, mat, bias=0, pref=(-1, 0.5), fist=None, fist_r=1.2, fore=None, elbow=None):
    el = elbow or ik(sh, hand, l1, l2, pref)
    R.cap(L, sh, el, r1, r2, mat, bias)
    R.cap(L, el, hand, r2, r2 * 0.9, fore or mat, bias)
    if fist_r:
        R.dome(L, hand, fist_r, fist_r, fist or fore or mat, bias)
    return el


# ---------------------------------------------------------------- blades
def blade_px(R, grip, ang, spec):
    """Rasterise a straight bladed weapon in frame coords.
    spec: pommel, grip_end, guard (u0,u1,half), b0, end, w_edge, w_spine, taper, broken,
          colours: edge_hi, edge, spine, grip, guard, pommel.
    Returns (pix dict, blade set, tip point)."""
    g = R.T(grip)
    ang = R.A(ang)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    # which side of the blade faces the light
    vdir = (-sa, ca)
    lit_edge = -(vdir[0] * LIGHT[0] + vdir[1] * LIGHT[1])
    sp = spec
    out, blade = {}, set()
    Rr = sp["end"] + 3
    for y in range(int(g[1] - Rr), int(g[1] + Rr) + 1):
        for x in range(int(g[0] - Rr), int(g[0] + Rr) + 1):
            dx, dy = x + .5 - g[0], y + .5 - g[1]
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            c = None
            if sp["pommel"] - 1.2 <= u <= sp["grip_end"] and abs(v) <= sp.get("grip_w", 0.75):
                c = sp["grip"]
            if abs(u - sp["pommel"]) <= 0.9 and abs(v) <= 1.1:
                c = sp["pommel_c"]
            gu0, gu1, gh = sp["guard"]
            if gu0 <= u <= gu1 and abs(v) <= gh:
                c = sp["guard_hi"] if v * (1 if lit_edge > 0 else -1) > 0.5 else sp["guard_c"]
            if sp["b0"] <= u <= sp["end"] + 0.5:
                t = (u - sp["b0"]) / (sp["end"] - sp["b0"])
                we, ws = sp["w_edge"], sp["w_spine"]
                tp = sp.get("taper", 0.25)
                if t > 1 - tp and not sp.get("broken"):
                    k = max(0.0, (1 - t) / tp)
                    we *= k ** 0.8; ws *= k ** 0.8
                end_ok = True
                if sp.get("broken"):
                    # jagged diagonal break
                    cut = sp["end"] - 1.6 * (v + ws) / (we + ws) + (0.8 if int(v * 2) % 2 else 0)
                    end_ok = u <= cut
                if -ws <= v <= we and end_ok:
                    sgn = v if lit_edge > 0 else -v
                    if sgn > we * 0.35 if lit_edge > 0 else sgn > ws * 0.35:
                        c = sp["edge_hi"]
                    elif abs(v) < 0.45 and sp.get("fuller"):
                        c = sp["fuller"]
                    else:
                        c = sp["spine"] if sgn < -0.2 else sp["edge"]
                    blade.add((x, y))
            if c:
                out[(x, y)] = c
    tip = (g[0] + ca * sp["end"], g[1] + sa * sp["end"])
    return out, blade, tip


def blade_line(grip, ang, u):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return (grip[0] + ca * u, grip[1] + sa * u)


# ---------------------------------------------------------------- smears
SMEAR = {
    "bone": ["B5", "B4", "B3", "B2"],
    "steel": ["B5", "I5", "I4", "I3"],
    "gold": ["Y3", "Y2", "G4", "G3"],
    "ember": ["O5", "O4", "O3", "O2"],
    "teal": ["Q4", "Q3", "Q2", "Q1"],
}


def swept(fx, grip0, ang0, grip1, ang1, u0, u1, hw=0.9, mid=None, start=0.0, pal="bone", taper=0.7,
          exclude=(), hot=0.6, streak=True, clip_y=None):
    """Arc smear: union of blade placements between two (grip, angle) poses (frame coords).
    age 0 = newest (just behind the weapon). Returns the 'hot' pixel set (for hit rects)."""
    arc = abs(ang1 - ang0) * math.pi / 180 * u1 + math.hypot(grip1[0] - grip0[0], grip1[1] - grip0[1])
    n = max(8, int(arc * (1 - start) / 0.7))
    best = {}
    for i in range(n + 1):
        t = start + (1 - start) * i / n
        gp = lerp(lerp(grip0, mid, t), lerp(mid, grip1, t), t) if mid else lerp(grip0, grip1, t)
        a = ang0 + (ang1 - ang0) * t
        age = 1 - (t - start) / max(1e-6, 1 - start)
        umin = u0 + age * taper * (u1 - u0)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        u = umin
        while u <= u1:
            for vv in (-hw, 0, hw):
                q = ip((gp[0] + ca * u - sa * vv, gp[1] + sa * u + ca * vv))
                ed = u1 - u
                if q not in best or best[q][0] > age:
                    best[q] = (age, ed)
            u += 0.5
    cols = SMEAR[pal]
    hotset = set()
    for q, (age, ed) in best.items():
        if q in exclude or not inb(*q) or (clip_y is not None and q[1] > clip_y):
            continue
        if streak and age > 0.55 and ed > 2 and int(ed / 2) % 2 == 1:
            continue
        if age > 0.85 and ed > 1.5:
            continue
        if age < 0.2:
            c = cols[0] if ed < 2.5 else cols[1]
        elif age < 0.45:
            c = cols[1] if ed < 2 else cols[2]
        elif age < 0.7:
            c = cols[2]
        else:
            c = cols[3]
        fx.put([q], c)
        if age < hot:
            hotset.add(q)
    return hotset


def thrust_lines(fx, grip, ang, u0, u1, offs, pal="steel", flash=None):
    """Speed streaks parallel to a thrusting weapon (frame coords), optional star flash at u=flash."""
    cols = SMEAR[pal]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = set()
    for i, o in enumerate(offs):
        a = u0 + (i * 3) % 5
        b = u1 - (i * 2) % 4
        seg = line((grip[0] + ca * a - sa * o, grip[1] + sa * a + ca * o),
                   (grip[0] + ca * b - sa * o, grip[1] + sa * b + ca * o))
        for k, q in enumerate(seg):
            fx.put([q], cols[1] if k > len(seg) * 0.6 else cols[2] if k > len(seg) * 0.3 else cols[3])
        pts |= set(seg)
    if flash is not None:
        c = ip((grip[0] + ca * flash, grip[1] + sa * flash))
        for d in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            fx.put([(c[0] + d[0], c[1] + d[1])], cols[0] if d == (0, 0) else cols[1])
        for d in ((2, 0), (0, 2), (0, -2), (-2, 0)):
            fx.put([(c[0] + d[0], c[1] + d[1])], cols[2])
    return pts


def speed_lines(fx, x0, x1, ys, pal="bone", seed=0):
    cols = SMEAR[pal]
    pts = set()
    for i, y in enumerate(ys):
        a = x0 + int(hash01(i, y, seed) * 4)
        b = x1 - int(hash01(y, i, seed + 1) * 4)
        for x in range(min(a, b), max(a, b) + 1):
            fx.put([(x, y)], cols[2] if (x - a) < (b - a) * 0.5 else cols[1])
            pts.add((x, y))
    return pts


def flame(fx, base, size, fi, seed=0, pal=("Y3", "Y2", "Y1", "O4", "O3", "O2")):
    """Flickering teardrop flame standing on `base` (frame coords), height ~ 1.7*size."""
    bx, by = base
    pts = []
    hgt = size * 1.8
    for y in range(int(by - hgt) - 1, int(by) + 2):
        t = (by - (y + .5)) / hgt              # 0 at base .. 1 at tip
        if t < -0.15 or t > 1:
            continue
        wob = math.sin(fi * 1.9 + t * 5 + seed) * 0.7 * t
        half = size * 0.55 * (1 - t) ** 0.7 * (1 + 0.3 * (t < 0.2)) + 0.3
        for x in range(int(bx - half - 2), int(bx + half + 2)):
            dx = x + .5 - (bx + wob)
            if abs(dx) <= half:
                r = abs(dx) / max(half, 0.5) * 0.6 + t * 0.7
                if hash01(x, y, fi + seed) < 0.15 * t:
                    continue
                c = pal[0] if r < 0.3 else pal[1] if r < 0.5 else pal[2] if r < 0.7 else pal[3] if r < 0.9 else pal[4] \
                    if r < 1.1 else pal[5]
                fx.put([(x, y)], c)
                pts.append((x, y))
    return pts


def ember_dissolve(imgs, frac, names, fx_name="FX", seed=0, rise=30, pal=("O5", "O4", "O3", "O2", "O1")):
    """Burn layers away from the bottom up; burning edge glows; lost pixels rise as embers into fx."""
    motes = {}
    out = dict(imgs)
    for n in names:
        if n not in imgs:
            continue
        src = imgs[n].load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                if src[x, y][3] == 0:
                    continue
                t = 0.5 * hash01(x, y, 91 + seed) + 0.5 * (1 - y / H)
                if t >= frac:
                    if t < frac + 0.07:
                        dst[x, y] = RGBA[pal[1] if hash01(x, y, 92) > 0.5 else pal[2]]
                    else:
                        dst[x, y] = src[x, y]
                elif hash01(x, y, 93 + seed) < 0.06:
                    age = frac - t
                    mx = int(x + math.sin(y * 0.4 + age * 9) * 2 + age * 6)
                    my = int(y - age * rise - hash01(x, y, 94) * 3)
                    if inb(mx, my) and age < 0.45:
                        motes[(mx, my)] = pal[0] if age < 0.1 else pal[1] if age < 0.2 else pal[2] if age < 0.32 else pal[4]
        out[n] = new
    fx = imgs[fx_name].copy() if fx_name in imgs else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fp = fx.load()
    for (x, y), c in motes.items():
        fp[x, y] = RGBA[c]
    out[fx_name] = fx
    return out


# =========================================================================== secondary motion
def spring(values, loop, gain=1.0, stiff=0.45, damp=0.45, lo=-6, hi=6, extra=None):
    """values: list of driver positions (e.g. chest x) -> lagged sway per frame (+ = trailing right)."""
    st, vel = 0.0, 0.0
    res = []
    n = len(values)
    for ps in range(2 if loop else 1):
        res = []
        prev = values[-1] if loop else values[0]
        for i, v in enumerate(values):
            target = -gain * (v - prev) + (extra[i] if extra else 0.0)
            vel = vel * damp + (target - st) * stiff
            st = max(lo, min(hi, st + vel))
            res.append(st)
            prev = v
    return res


# =========================================================================== output
BG = (86, 86, 94, 255)
BG_CELL = (74, 74, 82, 255)


def flatten(imgs, order):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in order:
        if n in imgs:
            out.alpha_composite(imgs[n])
    return out


def shift_imgs(imgs, dx, dy, names=None):
    out = {}
    for n, im in imgs.items():
        if names is None or n in names:
            o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            o.paste(im, (dx, dy))
            out[n] = o
        else:
            out[n] = im
    return out


def opaque_bbox(imgs, names):
    box = None
    for n in names:
        if n in imgs:
            b = imgs[n].getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def bbox(pts, pad=0):
    pts = [p for p in pts if inb(*p)]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def preview_rows(name, tags, flats, scale=4, labels=True):
    """One row per tag, mid-grey background, each frame on a slightly darker cell."""
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 10
    sheet = Image.new("RGBA", ((cols * (W + pad) + 40) * scale, len(tags) * (H + pad + lab) * scale), BG)
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 2), f"{t} ({b - a + 1})", fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), BG_CELL)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                                  (((i - a) * (W + pad)) * scale, y0 + lab * scale))
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    sheet.save(os.path.join(ART, "previews", f"{name}.png"))


def hitbox_preview(name, tags, flats, meta, scale=4):
    """Rows for every damaging tag: hurtbox green, hit rects red on active frames, anchor cross,
    and a 10x26 player box (blue) standing just inside the far edge of the hit rect."""
    start = {t: (a, b) for t, a, b in tags}
    rows = []
    for t, d in meta.get("attacks", {}).items():
        wins = d["windows"] if "windows" in d else [d]
        rows.append((t, wins))
    rows.append((tags[0][0], []))
    pad, lab = 2, 10
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", ((cols * (W + pad)) * scale, len(rows) * (H + pad + lab) * scale), BG)
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        dd.text((4, y0 + 2), t + "  " + "  ".join(f"active {w['active']} hit {w['hit']}" for w in wins),
                fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), BG_CELL)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rect(w["hit"], (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = w["hit"]
                    px = min(W - 10, max(0, hx + hw - 6))
                    rect([px, H - 26, 10, 26], (90, 150, 255, 255))
            d.line([(ax * scale - 4, min(ay * scale, H * scale - 1)), (ax * scale + 4, min(ay * scale, H * scale - 1))],
                   fill=(255, 255, 0, 255))
            d.line([(ax * scale, ay * scale - 5), (ax * scale, ay * scale + 3)], fill=(255, 255, 0, 255))
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", f"{name}_hitbox.png"))


def export(name, layers, anims, meta, build=True, flat_order=None):
    """anims: list of (tag, [(ms, imgs_dict), ...]). Writes sheet+json (Aseprite), meta, previews."""
    frames, tags, flats = [], [], []
    for tag, frs in anims:
        a = len(frames)
        for ms, imgs in frs:
            frames.append({"ms": ms, "cels": {n: imgs[n] for n in layers if n in imgs}})
            flats.append(flatten(imgs, flat_order or layers))
        tags.append((tag, a, len(frames) - 1))
    preview_rows(name, tags, flats)
    zoom = os.environ.get("ENEMY_ZOOM")      # debug close-up: "tag:i,j;tag2:k" -> $ENEMY_ZOOM_DIR/<name>_zoom.png
    if zoom:
        start = {t: a for t, a, _ in tags}
        idx = []
        for part in zoom.split(";"):
            t, ks = part.split(":")
            if t in start:
                idx += [start[t] + int(k) for k in ks.split(",")]
        if idx:
            sc = int(os.environ.get("ENEMY_ZOOM_SCALE", "8"))
            sheet = Image.new("RGBA", (len(idx) * (W + 1) * sc, H * sc), BG)
            for i, j in enumerate(idx):
                fr = Image.new("RGBA", (W, H), BG_CELL)
                fr.alpha_composite(flats[j])
                sheet.alpha_composite(fr.resize((W * sc, H * sc), Image.NEAREST), (i * (W + 1) * sc, 0))
            sheet.save(os.path.join(os.environ.get("ENEMY_ZOOM_DIR", "/tmp"), f"{name}_zoom.png"))
    if meta is not None:
        hitbox_preview(name, tags, flats, meta)
        with open(os.path.join(asebuild.ASSETS, f"{name}_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
    if build:
        asebuild.build(name, W, H, layers, frames, tags)
    return tags, flats
