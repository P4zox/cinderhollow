#!/usr/bin/env python3
"""Final boss generator -- "The Pale Sovereign" (Queen Ysolde, the corrupted heart of the Pale Root).

    python3 art/gen_sovereign.py              full build: sovereign + sovereign_p2 + fx (+ meta, previews)
    python3 art/gen_sovereign.py --preview    previews only (no Aseprite)
    python3 art/gen_sovereign.py --only idle,sweep --preview   quick iteration on some tags

Outputs
    art/sovereign.aseprite, assets/sovereign.png/.json          phase 1
    art/sovereign_p2.aseprite, assets/sovereign_p2.png/.json    phase 2 (same frames/tags: shattered crown,
                                                                burning cracks, robes ablaze, embers)
    assets/sovereign_meta.json                                   meta (shared by both sheets)
    art/fx_sov_nova.aseprite      assets/fx_sov_nova.*       160x120, 8 frames, centred     (tag sov_nova)
    art/fx_lightpillar.aseprite   assets/fx_lightpillar.*    24x120, 8 frames, pivot bottom (tag lightpillar)
    art/fx_sov_lance.aseprite     assets/fx_sov_lance.*      64x16, 4 frames loop, travels right (tag sov_lance)
    art/previews/sovereign.png, sovereign_p2.png (3x, one row per tag), sovereign_hitbox.png,
    sovereign_closeup.png, sovereign_bg.png (pale sky + dark backdrop check), fx_sovereign.png

Method (same family as gen_boss.py / gen_hound.py): every part is a mask with a per-pixel surface normal
(domes, capsules, bevelled cloth plates with animated fold fields, tapered root tubes).  A hue-shifted
material ramp is picked from the lit normal; sel-out outline; hand-placed decals (gold trim, kintsugi
cracks).  The root-wings are procedural branching roots grown from a fixed seed, so the same wing is
re-grown every frame from pose angles (spread / reach / travelling sway wave).  Robes, train, sleeves,
sash ribbons and hair are driven by a continuous cloth phase + wind so they flow between frames.
Faces RIGHT.  Floating: anchor = [96, 150] (the hem line); rows below 150 only carry light / roots / FX.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

W, H = 192, 160
AX, AY = 96, 150
FLOOR = 159         # lowest row; roots / hit rects reach it

# =========================================================================== palette
HEX = {
    "OUT": "#08070c",
    # porcelain skin: violet-rose shadow -> warm white glaze
    "P0": "#2a2231", "P1": "#4f4152", "P2": "#86737c", "P3": "#bba9a6", "P4": "#e4d8cc", "P5": "#fffaf0",
    # ivory robe: cool lavender shadows -> warm ivory
    "W0": "#221d31", "W1": "#413a55", "W2": "#6d6582", "W3": "#a29aae", "W4": "#d9d1d3", "W5": "#fbf5e8",
    # royal violet lining / underdress
    "V0": "#100b1c", "V1": "#1f1633", "V2": "#33254f", "V3": "#4b376e", "V4": "#6a5190",
    # gold
    "G0": "#2e1a0c", "G1": "#5a3713", "G2": "#8e5f1a", "G3": "#c48b28", "G4": "#eabb4a", "G5": "#fce9a0",
    # pale root bark (white-gold)
    "B0": "#231b20", "B1": "#45362f", "B2": "#715c47", "B3": "#a18a66", "B4": "#cfba8f", "B5": "#f1e6c2",
    # hair (pale gold)
    "H0": "#3b2a18", "H1": "#6d4f2a", "H2": "#a07c45", "H3": "#cfae6c", "H4": "#eed9a0", "H5": "#fff4d0",
    # phase-2 burn
    "R0": "#3a120a", "R1": "#7a260c", "R2": "#b8440f", "R3": "#e8741c", "R4": "#ffaf3c", "R5": "#ffe391",
    # light
    "Y0": "#e8a031", "Y1": "#ffcf5a", "Y2": "#ffeaa0", "Y3": "#fffbe8", "L": "#ffffff",
    # embers
    "E0": "#c2340e", "E1": "#e8541a",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {
    "P": ["P0", "P1", "P2", "P3", "P4", "P5"],
    "W": ["W0", "W1", "W2", "W3", "W4", "W5"],
    "V": ["V0", "V1", "V2", "V3", "V4"],
    "G": ["G0", "G1", "G2", "G3", "G4", "G5"],
    "B": ["B0", "B1", "B2", "B3", "B4", "B5"],
    "H": ["H0", "H1", "H2", "H3", "H4", "H5"],
    "R": ["R0", "R1", "R2", "R3", "R4", "R5"],
}
SHINY = {"G": 0.9, "P": 0.93}
LIGHT = (-0.55, -0.7, 0.46)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)
LIGHT_P = (0.15, -0.55, 0.82)   # porcelain: soft frontal key so the face (turned right) stays luminous
_l = math.sqrt(sum(c * c for c in LIGHT_P)); LIGHT_P = tuple(c / _l for c in LIGHT_P)

BASE_LAYERS = ["FXBack", "Wings", "Halo", "HairBack", "Train", "ArmFar", "Body", "Head", "ArmNear", "Glow", "FX"]
P2_ORDER = ["FXBack", "Wings", "Halo", "HairBack", "Train", "ArmFar", "Body", "Head", "ArmNear", "Fire", "Glow",
            "Embers", "FX"]
SHADED = ["Wings", "Halo", "HairBack", "Train", "ArmFar", "Body", "Head", "ArmNear"]


# =========================================================================== geometry helpers
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def dirv(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


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


def ipt(p):
    return (int(math.floor(p[0])), int(math.floor(p[1])))


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


def qbez(p0, p1, p2, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


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
            d2 = ox * ox + oy * oy
            if d2 <= r * r:
                k = 1.0 / max(r, 0.5)
                nx, ny = ox * k * flat, oy * k * flat
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
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
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0}


def tube(pts, r0, r1, ex=1.0):
    """Tapered tube along a polyline -> (normals, param t along the tube)."""
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


def spike_mask(base, tip, w0, bend=(0, 0), n=10):
    mid = add(lerp(base, tip, 0.5), bend)
    pts = qbez(base, mid, tip, n)
    m = set()
    for i, c in enumerate(pts):
        r = w0 * (1 - i / n) + 0.3
        m |= mask_disc(c, max(0.55, r))
    return m, pts


# =========================================================================== layer buffers
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}      # (x,y) -> [mat, n, bias, fixed, pid]
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

    def fill(self, mask, color):
        self.part_n += 1
        for p in mask:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color, self.part_n]

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
    Lv = LIGHT_P if mat == "P" else LIGHT
    ndl = n[0] * Lv[0] + n[1] * Lv[1] + n[2] * Lv[2]
    v = 0.16 + 0.84 * max(0.0, ndl)
    f = v * (top - (1 if mat in SHINY else 0)) + 0.35
    if mat in ("W", "V"):
        f += (95 - y) * 0.006        # light from above: the hem sinks into cool shadow
    if mat == "W":
        f += 0.75                     # luminous ivory: shadows stay light
    if mat == "P":
        f += 0.5                      # glazed porcelain glows from within
    i = int(math.floor(f)) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - Lv[2]
        if rz > SHINY[mat] and bias >= 0:
            i = top
        else:
            i = min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, burn=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    col, lvl = {}, {}
    for (x, y), e in layer.px.items():
        if e[0] is None or isinstance(e[3], str):
            col[(x, y)] = e[3]
            continue
        i = level_of(e, x, y)
        mat = e[0]
        if burn and mat == "G" and e[2] >= -1:
            mat = "R"
        lvl[(x, y)] = i
        col[(x, y)] = RAMP[mat][min(i, len(RAMP[mat]) - 1)]
    for (x, y) in layer.px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
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


ALPHA_STEPS = (0, 70, 130, 190, 255)   # the only alpha levels glow may use


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
        """Only where empty."""
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
PIV = (96, 92)   # lean pivot (hips): above it tips forward, the hem swings back
REST = dict(Hd=(101, 39), Nk=(98.5, 49), Sn=(104, 55), Sf=(90, 54), Ch=(98, 62), Wa=(96, 80), Wr=(90, 59),
            Hc=(95, 36), Hm=(95, 146))

NEUTRAL = dict(
    bob=0, lean=0.0, dx=0, head=(0, 0), htilt=0.0,
    hn=(119, 73), hf=(71, 69), hn_dir=55, hf_dir=150, eln=(0.5, 1), elf=(-0.6, 1), palm_n=0.0,
    wl=(198, 1.0, 1.0), wr=(-18, 1.0, 0.9), wsway=5.0,
    wind=0.0, lift=0.0, glow=1.0, eyes=0.0, halo=1.0, crack=0.0, dissolve=0.0, tendrils=0.0,
    shake=0, crown_break=0.0, fx=(),
)


def P_(**kw):
    d = dict(NEUTRAL)
    d.update(kw)
    return d


def joints(p, sec):
    lean, bob, ox = p["lean"], p["bob"], p["dx"]

    def X(q, k=1.0):
        r = rot((q[0] - PIV[0], q[1] - PIV[1]), lean * k)
        return (PIV[0] + r[0] + ox, PIV[1] + r[1] + bob)
    j = {k: X(v) for k, v in REST.items()}
    j["X"] = X
    j["Hd"] = add(j["Hd"], p["head"])
    j["Hc"] = add(j["Hc"], mul(p["head"], 0.5))
    j["ph"] = sec["ph"]
    j["wind"] = p["wind"] + sec.get("wind", 0.0)
    j["lift"] = p["lift"] + sec.get("lift", 0.0)
    j["hn"] = X(p["hn"])
    j["hf"] = X(p["hf"])
    return j


# =========================================================================== wings (procedural roots)
# (angle offset, length, r0, curvature deg/px): outer/low -> inner/high.  Roots leave the back, run
# outward, then sweep upward and hook at the tips -- a raised seraph fan rather than a tree.
WING_PRIM = [(-34, 72, 4.4, 0.78), (-13, 86, 4.2, 0.6), (8, 80, 3.9, 0.45), (28, 60, 3.3, 0.32)]


def grow(start, ang, length, curv, sway, ph, seed, up):
    """One root: returns (points, angles).  up = +1: angle increases to bend upward (left wing)."""
    n = max(3, int(length / 1.3))
    step = length / n
    pts, angs = [start], [ang]
    a = ang
    pos = start
    for i in range(1, n + 1):
        t = i / n
        c = curv * (1.0 if t < 0.82 else 3.4)          # the tip hooks into a curl
        a += up * c * step
        ae = a + sway * t * t * math.sin(ph - t * 2.6 + seed * 1.7)
        pos = add(pos, mul(dirv(ae), step))
        pts.append(pos)
        angs.append(ae)
    return pts, angs


def wing_geometry(root, s, ang, spread, scale, sway, ph):
    """s = -1 left wing (fan points left), +1 right wing.  Returns branches dict(pts, r0, r1, depth, k)."""
    out = []
    up = -s
    for k, (off, ln, r0, cv) in enumerate(WING_PRIM):
        a0 = ang - s * off * spread
        L = ln * scale
        st = add(root, mul(dirv(a0), 2))
        pts, angs = grow(st, a0, L, cv, sway, ph, k, up)
        for _ in range(10):      # keep the whole root inside the frame (shorten it rather than clip)
            if all(4 <= q[1] and 2 <= q[0] <= W - 3 for q in pts):
                break
            L *= 0.94
            pts, angs = grow(st, a0, L, cv, sway, ph, k, up)
        out.append(dict(pts=pts, r0=r0, r1=0.6, depth=0, k=k))
        n = len(pts) - 1
        # one barb on the outer (lower) side pointing tip-ward, and a forked tip
        i = int(0.46 * n)
        ca = angs[i] - up * (30 + hash01(k, 0, 3) * 10)
        cl = L * 0.3
        cp, _ = grow(pts[i], ca, cl, cv * 1.6, sway, ph - 0.7, k * 5, up)
        out.append(dict(pts=cp, r0=max(1.2, r0 * 0.5), r1=0.5, depth=1, k=k))
        i = int(0.8 * n)
        ca = angs[i] - up * 34
        cp, _ = grow(pts[i], ca, L * 0.16, cv * 2.5, sway, ph - 1.0, k * 7 + 1, up)
        out.append(dict(pts=cp, r0=1.0, r1=0.5, depth=1, k=k))
    return out


def wing_membrane(fxb, geo, root, phase, alpha=1.0):
    """Luminous sail of light spanned between neighbouring roots (a few alpha steps)."""
    prim = [b["pts"] for b in geo if b["depth"] == 0]
    for a, b in zip(prim, prim[1:]):
        na, nb = len(a) - 1, len(b) - 1
        ea, eb = a[int(na * 0.8)], b[int(nb * 0.8)]
        mid = lerp(lerp(ea, eb, 0.5), root, 0.3)
        poly = [a[int(na * t / 20)] for t in range(1, 17)] + [mid] + [b[int(nb * t / 20)] for t in range(16, 0, -1)]
        m = poly_mask(poly)
        L = math.hypot(*sub(ea, root)) or 1
        for q in m:
            d = math.hypot(q[0] + .5 - root[0], q[1] + .5 - root[1]) / L
            if phase == 1:
                c, al = ("Y3", 240) if d < 0.3 else ("Y2", 205) if d < 0.6 else ("Y1", 150)
            else:
                c, al = ("Y2", 240) if d < 0.3 else ("R5", 205) if d < 0.6 else ("R4", 150)
            fxb.under([q], c, int(al * alpha))


def draw_wing(Lw, glow, info, geo, bias, phase, fi):
    wing_px = set()
    for dep in (2, 1, 0):
        for b in geo:
            if b["depth"] != dep:
                continue
            nm, par = tube(b["pts"], b["r0"], b["r1"], ex=2.2 if dep == 0 else 1.4)
            wing_px |= Lw.paint(nm, "B", bias=bias - (1 if dep == 2 else 0), ao=1 if dep == 0 else 0)
    # sap vein: a continuous golden core seam with light pulses travelling out along it
    for b in geo:
        pts = b["pts"]
        n = len(pts)
        if b["depth"] == 0:
            for i in range(3, int(n * 0.84)):
                q = ipt(pts[i])
                if q not in wing_px:
                    continue
                pulse = (i - fi * 4 - b["k"] * 5) % 18 < 3
                if phase == 1:
                    glow.put([q], "Y3" if pulse else "Y1" if i % 5 else "Y2")
                else:
                    glow.put([q], "L" if pulse else "R4" if i % 4 else "Y2")
        tip = ipt(pts[-1])
        if b["depth"] < 2:
            glow.put([tip], "Y3" if phase == 1 else "L")
            if phase == 2 and b["depth"] == 0:
                glow.put([(tip[0], tip[1] - 1)], "R4")
    info["wing_px"] |= wing_px
    return wing_px


# =========================================================================== halo & crown
def draw_halo(L, glow, fxb, j, p, fi, phase):
    Hc = j["Hc"]
    R = 14.0
    br = p["halo"]
    broken = phase == 2 or p["crown_break"] > 0.4
    rotd = (fi * 3.75) % 360
    # sun disc (a few alpha steps, behind everything)
    if br > 0.05:
        for q in mask_disc(Hc, R + 7):
            d = math.hypot(q[0] + .5 - Hc[0], q[1] + .5 - Hc[1])
            if d < R - 2:
                fxb.put([q], "Y3" if phase == 1 else "Y2", int(min(235, 170 * br)))
            elif d < R + 3:
                fxb.put([q], "Y2" if phase == 1 else "R5", int(min(220, 120 * br)))
            else:
                fxb.put([q], "Y1" if phase == 1 else "R4", int(min(200, 60 * br)))
    gaps = []
    if broken:
        gaps = [(20, 52), (140, 175), (250, 262)]   # shattered ring: arcs missing (deg)

    def gapped(th):
        thd = math.degrees(th) % 360
        return any(a <= thd <= b for a, b in gaps)
    # twin twisted root strands
    for strand, sg in ((0, 1), (1, -1)):
        pts = []
        segs = []
        for i in range(0, 121):
            th = 2 * math.pi * i / 120
            if gapped(th):
                if len(pts) > 1:
                    segs.append(pts)
                pts = []
                continue
            rr = R + sg * 1.1 * math.sin(th * 7 + math.radians(rotd) * 2)
            pts.append((Hc[0] + math.cos(th) * rr, Hc[1] + math.sin(th) * rr * 1.02))
        if len(pts) > 1:
            segs.append(pts)
        for sgm in segs:
            nm, _ = tube(sgm, 1.25, 1.25)
            L.paint(nm, "G" if strand == 0 else "B", bias=-strand, ao=0)
    # tines: a slowly turning sunburst, length set by absolute angle (longest at the top)
    tips = []
    for k in range(12):
        thd = (k * 30 + rotd) % 360
        th = math.radians(thd)
        up = -math.sin(th)
        if up < -0.35 or gapped(th):
            continue
        ln = 3.0 + 10.0 * max(0.0, up) ** 1.6
        if broken:
            ln *= 0.35 + 0.45 * hash01(k, 1, 77)
        base = (Hc[0] + math.cos(th) * (R + 0.5), Hc[1] + math.sin(th) * (R + 0.5))
        tip = (Hc[0] + math.cos(th) * (R + 0.5 + ln), Hc[1] + math.sin(th) * (R + 0.5 + ln))
        m, sp = spike_mask(base, tip, 0.9 if ln > 7 else 0.6, bend=mul(dirv(thd + 90), 1.2))
        L.paint({q: norm3(math.cos(th) * 0.6, math.sin(th) * 0.6, 0.8) for q in m}, "B", bias=0, ao=0)
        tips.append(tip)
        if ln > 5:
            glow.put([ipt(tip)], "Y3" if phase == 1 else "R5")
    # glowing jewels on the ring at the cardinal points
    for thd in (270, 200, 340):
        th = math.radians(thd)
        if gapped(th):
            continue
        q = (Hc[0] + math.cos(th) * R, Hc[1] + math.sin(th) * R)
        glow.put([ipt(q)], "L" if phase == 1 else "R5")
        glow.put([add(ipt(q), (1, 0)), add(ipt(q), (0, 1))], "Y2" if phase == 1 else "R4")
    # phase 2 / death: shards of the ring hang in the air beside the gaps
    if broken:
        for gi, (a, b) in enumerate(gaps):
            for s in range(2):
                thd = a + (b - a) * (0.3 + 0.4 * s) + math.sin(fi * 0.8 + gi + s) * 4
                th = math.radians(thd)
                rr = R + 3 + 2 * s + math.sin(fi * 0.6 + gi * 2 + s) * 1.2
                c = (Hc[0] + math.cos(th) * rr, Hc[1] + math.sin(th) * rr)
                m, _ = spike_mask(c, add(c, mul(dirv(thd + 90 + 30 * s), 3)), 1.2, n=4)
                L.paint({q: (-0.4, -0.6, 0.7) for q in m}, "B", bias=-1, ao=0)
                glow.put([ipt(c)], "R4" if phase == 2 else "Y1")
    return tips


def draw_head(L, glow, j, p, fi, phase, info):
    Hd = j["Hd"]
    X = j["X"]
    Hl = L["Head"]
    # neck
    Hl.paint(n_capsule(j["Nk"], add(Hd, (-1, 3)), 2.3, 2.1), "P", bias=-1)
    # head (porcelain egg) + chin + nose
    head = n_dome(Hd, 6.0, 7.1, tilt=(0.05, 0))
    Hl.paint(head, "P")
    Hl.paint(n_dome(add(Hd, (3.3, 5.0)), 2.8, 2.2), "P", ao=0)
    Hl.paint(n_capsule(add(Hd, (5.1, -0.5)), add(Hd, (6.5, 1.5)), 0.8, 0.9), "P", ao=0)
    face = set(head)
    # veil hood over the back of the head; the face stays bare, framed by a gold hem
    hood = n_dome(add(Hd, (-1.9, -0.9)), 7.0, 7.7, tilt=(-0.1, -0.05))
    hm = {q: v for q, v in hood.items()
          if (q[0] + .5 - Hd[0]) < -0.8 - (q[1] + .5 - Hd[1]) * 0.35 or (q[1] + .5 - Hd[1]) < -4.3}
    hm = {q: v for q, v in hm.items() if q[1] < Hd[1] + 7.5}
    Hl.paint(hm, "W", ao=0)
    hedge = {q for q in hm if any((q[0] + a_, q[1] + b_) in face and (q[0] + a_, q[1] + b_) not in hm
                                  for a_, b_ in ((1, 0), (0, 1), (1, 1)))}
    Hl.decal(hedge, ("G", 4))
    shade = {q for q in face if q not in hm and any((q[0] + a_, q[1] + b_) in hm for a_, b_ in ((-1, 0), (0, -1), (-1, -1)))}
    Hl.decal(shade, ("P", 2))
    # circlet
    ca, cb = add(Hd, (-4.6, -5.6)), add(Hd, (3.6, -6.4))
    circ = set(line(ca, cb)) | set(line(add(ca, (0, 1)), add(cb, (0, 1))))
    Hl.paint({q: (-0.2, -0.5, 0.8) if q[1] < (ca[1] + cb[1]) / 2 + 0.5 else (0.1, 0.4, 0.9) for q in circ}, "G", ao=0)
    cj = ipt(lerp(ca, cb, 0.72))
    glow.put([cj], "L" if phase == 1 else "R5")
    # crown tines rising from the circlet (roots)
    brk = max(p["crown_break"], 1.0 if phase == 2 else 0.0)
    tines = [(0.0, -122, 3), (0.22, -104, 7), (0.52, -92, 11), (0.8, -79, 7), (1.0, -64, 3)]
    tip_pts = []
    for k, (t, ang, ln) in enumerate(tines):
        if brk > 0.4 and k in (1, 4):
            ln *= 0.25          # snapped stumps
        elif brk > 0.4:
            ln *= 0.55 + 0.2 * hash01(k, 3, 5)
        base = add(lerp(ca, cb, t), (0, -0.5))
        tip = add(base, mul(dirv(ang + p["htilt"]), ln))
        m, sp = spike_mask(base, tip, 0.75 if ln > 4 else 0.5, bend=mul(dirv(ang + 90), 0.8 * (1 if k < 2 else -1)))
        Hl.paint({q: norm3(-0.4, -0.4, 0.8) for q in m}, "G", ao=0)
        tip_pts.append(tip)
        if ln > 4:
            glow.put([ipt(tip)], "Y2" if phase == 1 else "R5")
        if brk > 0.4 and ln <= 4:
            glow.put([ipt(tip)], "R4" if phase == 2 else "Y1")
    info["crown_tips"] = tip_pts
    # face: closed serene eye / open glowing eye, brow, nose, lips, kintsugi tear
    e = p["eyes"] if phase == 1 else max(0.8, p["eyes"])
    ex, ey = ipt(add(Hd, (3.4, -0.6)))
    Hl.decal([(ex - 1, ey - 2), (ex, ey - 2), (ex + 1, ey - 2)], ("P", 3))          # brow ridge
    Hl.decal([(ex - 2, ey - 1)], ("P", 3))
    if e < 0.4:
        Hl.decal([(ex - 1, ey), (ex, ey), (ex + 1, ey)], "P0")                    # closed lids: calm dark lash line
        Hl.decal([(ex - 1, ey + 1), (ex, ey + 1)], ("P", 3))
    else:
        Hl.decal([(ex - 1, ey), (ex, ey), (ex + 1, ey), (ex, ey - 1)], "P0")
        glow.put([(ex, ey)], "L")
        glow.put([(ex + 1, ey)], "Y2" if phase == 1 else "R5")
        if e > 0.9:
            glow.put([(ex - 1, ey)], "Y1" if phase == 1 else "R4")
            for i in range(1, 4):
                glow.put([(ex - 1 - i, ey - (i // 2))], "Y1" if i < 2 else "Y0")
    nb = ipt(add(Hd, (6.0, 0.6)))                                                    # nose tip + nostril shade
    Hl.fill([nb, (nb[0], nb[1] - 1)], "P4")
    Hl.decal([(nb[0] - 1, nb[1] + 1)], ("P", 2))
    lp_ = ipt(add(Hd, (5.0, 3.2)))
    Hl.decal([lp_], "P1")                                                             # lips
    Hl.decal([(lp_[0] - 1, lp_[1])], ("P", 2))
    Hl.decal([(lp_[0], lp_[1] - 1)], ("P", 3))
    info["eye"] = (ex, ey)
    info["face_px"] = face


def draw_hair_back(L, j, p, sec):
    """The veil: a long panel of sheer ivory cloth falling from the hood down her back, flowing."""
    Hd = j["Hd"]
    ph = j["ph"]
    wind = j["wind"]
    Hb = L["HairBack"]
    root = add(Hd, (-4.5, -1))
    n = 22
    ln = 62
    lp, rp = [], []
    for i in range(n + 1):
        t = i / n
        wv = math.sin(ph - t * 3.0) * (0.5 + 3.5 * t)
        cx = root[0] - 8 * t - 9 * t * t + wind * 0.7 * t * t + wv
        cy = root[1] + ln * t - abs(wind) * 0.25 * t * t * 10
        hw = 4.0 + 8.0 * t
        lp.append((cx - hw, cy))
        rp.append((cx + hw * 0.8, cy - 2 * t))
    # pointed tails at the bottom
    bl, br = lp[-1], rp[-1]
    tail = [(bl[0] + 1, bl[1] + 3 + math.sin(ph) * 1.5), lerp(bl, br, 0.45),
            (lerp(bl, br, 0.7)[0] + 1, lerp(bl, br, 0.7)[1] + 4 + math.sin(ph - 1) * 1.5)]
    poly = lp + tail + list(reversed(rp))
    m = poly_mask(poly)
    Hb.paint(n_plate(m, bevel=3, tilt=(0.0, -0.1), strength=1.0,
                     fold=lambda x, y: (0.5 * math.sin((x - root[0]) * 0.8 + (y - root[1]) * 0.12 - ph), 0.0)),
             "W", bias=0)
    edge = {q for q in m if (q[0] - 1, q[1]) not in m or (q[0], q[1] + 1) not in m}
    Hb.decal(edge, ("G", 3))
    sec["veil_px"] = m


# =========================================================================== body, robe, sleeves
def robe_geometry(j, p):
    """Outer robe polygon: narrow at the hips, flaring into a bell, the hem trailing off into floating tails."""
    X = j["X"]
    Hm = j["Hm"]
    wind = j["wind"]
    ph = j["ph"]
    lift = j["lift"]
    wl = X((89, 80)); wr = X((103, 80))
    hy = Hm[1] - 7 - lift          # hem line above the tails
    hl = (Hm[0] - 27 + wind * 1.0, hy - 2)
    hr = (Hm[0] + 26 + wind * 0.6, hy)
    left = bezier(wl, X((84, 104)), (hl[0] + 12 + wind * 0.4, hy - 22), hl, 16)
    right = bezier(wr, X((109, 102)), (hr[0] - 11 + wind * 0.3, hy - 24), hr, 16)
    hem = []
    NT = 6
    n = 72
    for i in range(n + 1):
        t = i / n
        x = hl[0] + (hr[0] - hl[0]) * t
        k = min(NT - 1, int(t * NT))
        s = t * NT - k
        shape = (1 - abs(2 * s - 1)) ** 1.6
        depth = (6.5 + 4.5 * hash01(k, 0, 5) + 1.5 * math.sin(ph + k * 1.3)) * (0.85 if k in (0, NT - 1) else 1.0)
        shift = wind * 0.5 + 2.4 * math.sin(ph - k * 0.9) - 1.5
        y = hy + shape * depth + 1.2 * math.sin(ph * 2 + t * 7)
        hem.append((x + shape * shift, y))
    poly = left + hem[1:-1] + list(reversed(right))
    return poly, (wl, wr, hl, hr, hy)


def draw_body(L, glow, j, p, sec, info, phase):
    Bd = L["Body"]
    X = j["X"]
    ph = j["ph"]
    wind = j["wind"]
    poly, (wl, wr, hl, hr, hy) = robe_geometry(j, p)
    robe = poly_mask(poly)
    Wa = j["Wa"]
    top_y = Wa[1]

    def fold(x, y):
        t = max(0.0, min(1.0, (y - top_y) / max(1.0, hy - top_y)))
        cx = lerp(Wa, ((hl[0] + hr[0]) / 2, hy), t)[0]
        hw = 7 + (hr[0] - hl[0]) / 2 * t
        u = (x + .5 - cx) / hw
        sw = 0.7 * math.sin(ph - t * 2.2)
        return (0.62 * math.sin(u * 3.3 * math.pi + sw) * (0.25 + t), 0.0)
    Bd.paint(n_plate(robe, bevel=9, tilt=(0.05, -0.05), strength=1.35, fold=fold), "W")
    # front opening: violet underdress wedge with gold trim
    o0, o1 = X((97.5, 83)), X((101, 83))
    fr_l = (Hm_x := (hl[0] + hr[0]) / 2) + 1 + wind * 0.15
    wedge = poly_mask([o0, o1, (fr_l + 16, hy + 12), (fr_l - 1, hy + 13)])
    wedge &= robe
    Bd.paint(n_plate(wedge, bevel=3, tilt=(0.1, -0.1), strength=0.8,
                     fold=lambda x, y: (0.35 * math.sin((x - o0[0]) * 0.9 + ph), 0)), "V", ao=0)
    edge = {q for q in wedge if any((q[0] + a, q[1]) not in wedge for a in (-1, 1))}
    Bd.decal(edge, ("G", 3))
    Bd.decal([q for q in edge if (q[1] + int(ph * 2)) % 5 == 0], ("G", 5))
    # underdress filigree: a vertical chain of gold diamonds down the centre of the wedge
    for k in range(6):
        t = 0.18 + k * 0.14
        c = lerp(lerp(o0, o1, 0.5), (fr_l + 7.5, hy), t)
        Bd.decal([ipt(c)], ("G", 4))
        Bd.decal([ipt(add(c, (1, 0))), ipt(add(c, (-1, 0))), ipt(add(c, (0, 1)))], ("G", 2))
    # hem trim band (2px gold) following the hem
    rows = {}
    for (x, y) in robe:
        if y > rows.get(x, -1):
            rows[x] = y
    trim = set()
    for x, y in rows.items():
        if y > hy - 4:
            trim |= {(x, y), (x, y - 1)}
            if (x + int(ph * 3)) % 6 == 0:
                trim.add((x, y - 2))
    Bd.decal([q for q in trim if q in Bd.px and Bd.px[q][0] == "W"], ("G", 3))
    Bd.decal([q for q in trim if q in Bd.px and (q[0] // 2) % 3 == 0 and Bd.px[q][1][0] < 0.1], ("G", 4))
    info["robe_bottom"] = rows
    info["robe_px"] = set(robe)
    # bodice
    bod = [X(q) for q in ((95, 50), (90, 53), (87.5, 57), (88.5, 64), (90, 72), (90, 81), (102.5, 81),
                          (103.5, 73), (106.5, 66), (107.5, 60), (106.5, 55), (101.5, 50))]
    bm = poly_mask(bod)
    Bd.paint(n_plate(bm, bevel=4.5, tilt=(0.1, -0.05), strength=1.4,
                     fold=lambda x, y: (0.0, 0.0)), "W")
    # bust shading: a soft dome in front
    Bd.paint(n_dome(X((103, 62)), 4.2, 3.6, tilt=(0.1, 0.1)), "W", ao=0, clip=bm)
    # mantle: petal-scalloped capelet over the shoulders, gold-edged
    mp = [X((87, 55)), X((92, 50.5)), X((104, 50.5)), X((109.5, 55))]
    for k in range(7):
        t = k / 6
        x = 111 - 27 * t
        yb = 66 - 2.2 * math.sin(math.pi * t) + (1.2 if k % 2 else 0)
        mp.append(X((x + 1.8, yb - 2.5)))
        mp.append(X((x, yb)))
    mm = poly_mask(mp)
    Bd.paint(n_plate(mm, bevel=3.5, tilt=(0.05, -0.25), strength=1.3,
                     fold=lambda x, y: (0.3 * math.sin(x * 0.9), 0.0)), "W")
    medge = {q for q in mm if (q[0], q[1] + 1) not in mm}
    Bd.decal(medge, ("G", 3))
    Bd.decal({(q[0], q[1] - 1) for q in medge if q[0] % 3 == 0}, ("G", 4))
    info["mantle_px"] = mm
    # neckline: V of porcelain skin with gold trim
    nl = poly_mask([X((95.5, 50.5)), X((102, 50.5)), X((100, 60))])
    Bd.paint({q: (0.0, -0.3, 0.9) for q in nl}, "P", ao=0)
    nle = {q for q in nl if any((q[0] + a, q[1] + b) not in nl for a, b in ((1, 0), (-1, 0), (0, 1)))}
    Bd.decal([q for q in nle if q[1] > X((0, 51))[1]], ("G", 4))
    # brooch (the Root's heart-seed)
    bc = X((100.5, 61))
    Bd.paint(n_dome(bc, 2.2, 2.2), "G", ao=0)
    glow.put([ipt(bc)], "L" if phase == 1 else "R5")
    glow.put([ipt(add(bc, (0, 1)))], "Y2" if phase == 1 else "R4")
    info["heart"] = bc
    # belt: gold cord at the waist
    belt = set(line(X((89.5, 79.5)), X((102.5, 80.5)))) | set(line(X((89.5, 80.5)), X((102.5, 81.5))))
    Bd.paint({q: (0.0, -0.4, 0.9) if q[1] < X((96, 80))[1] + 0.5 else (0, 0.4, 0.9) for q in belt}, "G", ao=0)
    # bodice gold seam / filigree lines
    Bd.decal(line(X((93, 56)), X((91.5, 78))), ("W", 2))
    Bd.decal(line(X((104.5, 64)), X((101.5, 78))), ("W", 2))
    return robe


def draw_train(L, glow, j, p, info):
    """Trailing train (behind) and two sash ribbons flowing from the waist."""
    Tr = L["Train"]
    X = j["X"]
    ph = j["ph"]
    wind = j["wind"]
    poly, (wl, wr, hl, hr, hy) = robe_geometry(j, p)
    a = X((85, 108))
    tip1 = (hl[0] - 22 + wind * 1.3, hy - 9 + 4 * math.sin(ph - 1.0) - abs(wind) * 0.4)
    tip2 = (hl[0] - 12 + wind * 1.0, hy - 1 + 3 * math.sin(ph - 1.7))
    mid = (hl[0] - 9 + wind * 0.8, hy - 7 + 2 * math.sin(ph - 0.5))
    pts = bezier(a, (a[0] - 10 + wind * 0.4, a[1] + 8), (tip1[0] + 8, tip1[1] - 4), tip1, 10) + \
        [mid] + bezier(tip2, (tip2[0] + 4, tip2[1] + 1), (hl[0] - 2, hy + 1), (hl[0] + 6, hy), 6)
    m = poly_mask(pts)

    def fold(x, y):
        return (0.5 * math.sin((x + y * 0.6) * 0.45 + ph), 0.0)
    Tr.paint(n_plate(m, bevel=3, tilt=(0.1, -0.2), strength=0.9, fold=fold), "W", bias=0)
    # lining visible on the underside edge
    under = {q for q in m if (q[0], q[1] + 1) not in m and q[0] < hl[0] - 2}
    Tr.decal(under, ("V", 4))
    Tr.decal({q for q in m if (q[0], q[1] + 1) not in m and (q[0], q[1] + 2) in m}, ("G", 3))
    # sash ribbons
    base = X((90, 81))
    rib_pts = []
    for k in range(0):
        pts = []
        n = 22
        ln = 40
        for i in range(n + 1):
            t = i / n
            wv = math.sin(ph * 1.0 - t * 4.5 + k * 1.1) * (0.6 + 4.0 * t)
            x = base[0] - 2 - ln * 0.75 * t + wind * 0.8 * t * t - k * 2
            y = base[1] + ln * 0.62 * t - (abs(wind) * 0.5 * t * t) + wv * 0.35
            x += wv * 0.5
            pts.append((x, y))
        nm, _ = tube(pts, 1.2, 0.9)
        Tr.paint(nm, "G" if k == 0 else "W", bias=-1 if k else 0, ao=0)
        tail = pts[-1]
        m2, _ = spike_mask(pts[-3], add(tail, mul(unit(sub(tail, pts[-3])), 3)), 1.3, n=4)
        Tr.paint({q: (-0.3, -0.3, 0.9) for q in m2}, "G" if k == 0 else "W", bias=-1 if k else 0, ao=0)
        rib_pts.append(pts)
    info["train_px"] = set(m)


def draw_arm(Lr, glow, j, p, side, info, phase):
    near = side == "n"
    sh = j["Sn"] if near else j["Sf"]
    hand = j["hn"] if near else j["hf"]
    pref = p["eln"] if near else p["elf"]
    l1, l2 = (13.0, 12.5) if near else (12.0, 11.5)
    el = ik(sh, hand, l1, l2, pref)
    bias = 0 if near else -1
    wind = j["wind"]
    ph = j["ph"]
    fa = unit(sub(hand, el))
    wr = sub(hand, mul(fa, 2.2))
    # bell sleeve: a cone flaring from the elbow to a wide mouth near the wrist, its lower lip hanging in a tail
    fl = math.hypot(*sub(wr, el))
    raise_ = max(0.0, min(1.0, -fa[1] * 1.3))     # arm raised: the sleeve slides down to the elbow
    M = add(el, mul(fa, max(2.5, (fl - 1.5) * (1 - 0.72 * raise_))))
    p1 = (-fa[1], fa[0])
    pd = p1 if (p1[1] > 0.05 or (abs(p1[1]) <= 0.05 and p1[0] < 0)) else (-p1[0], -p1[1])
    pu = (-pd[0], -pd[1])
    mw = 8.0 if near else 7.0
    drop = (22 if near else 19) - abs(fa[1]) * 4
    sway = math.sin(ph - (0.6 if near else 1.4)) * 2.0
    lipd = add(M, mul(pd, mw))
    T = (lipd[0] - 2 + wind * 0.6 + sway, max(lipd[1], M[1]) + drop - abs(wind) * 0.2)
    T2 = lerp(add(el, mul(pd, 3.5)), T, 0.55)
    T2 = (T2[0] - 1.5 + wind * 0.3 + sway * 0.5, T2[1] + 2)
    cone = [add(el, mul(pu, 3.4)), add(M, mul(pu, mw - 1.0)), add(M, mul(pu, mw * 0.5)), add(lipd, mul(fa, 0.5)),
            add(T, (2.5, -2.0)), T, T2, add(el, mul(pd, 3.6))]
    drape = poly_mask(cone)
    Lr.paint(n_plate(drape, bevel=3.5, tilt=(0.1, -0.1), strength=1.1,
                     fold=lambda x, y: (0.4 * math.sin((x - el[0]) * 0.9 + (y - el[1]) * 0.3 + ph * 0.5), 0.0)),
             "W", bias=bias)
    Lr.paint(n_capsule(sh, el, 3.6, 3.4), "W", bias=bias)
    # sleeve mouth: violet lining ellipse + gold rim
    mouth = {q for q in drape if abs((q[0] + .5 - M[0]) * fa[0] + (q[1] + .5 - M[1]) * fa[1]) < 1.3 and
             abs((q[0] + .5 - M[0]) * p1[0] + (q[1] + .5 - M[1]) * p1[1]) < mw - 1.2}
    rim = {q for q in drape if abs((q[0] + .5 - M[0]) * fa[0] + (q[1] + .5 - M[1]) * fa[1]) < 2.0 and
           abs((q[0] + .5 - M[0]) * p1[0] + (q[1] + .5 - M[1]) * p1[1]) < mw + 0.5 and q not in mouth}
    Lr.paint({q: (0.2, 0.3, 0.9) for q in mouth}, "V", bias=bias, ao=0)
    Lr.decal(rim, ("G", 3 if near else 2))
    Lr.decal([q for q in rim if hash01(*q, 3) > 0.6], ("G", 4 if near else 3))
    # gold hem on the hanging edge
    bottom = {q for q in drape if (q[0], q[1] + 1) not in drape and q not in rim and q not in mouth
              and q[1] > T[1] - 7 and (q[0] - 1, q[1]) in drape and (q[0] + 1, q[1]) in drape}
    Lr.decal(bottom, ("G", 3 if near else 2))
    cuff = M
    # forearm + hand (porcelain)
    Lr.paint(n_capsule(M, wr, 1.5, 1.4), "P", bias=bias)
    hd = p["hn_dir"] if near else p["hf_dir"]
    d = dirv(hd)
    palm = add(wr, mul(d, 1.2))
    Lr.paint(n_dome(palm, 1.9, 1.9), "P", bias=bias, ao=0)
    for k, off in enumerate((-22, 0, 20)):
        dd = dirv(hd + off)
        ln = 3.4 if off == 0 else 2.8
        fp = line(add(palm, mul(dd, 1.0)), add(palm, mul(dd, 1.0 + ln)))
        Lr.paint({q: (dd[0] * 0.3, -0.5, 0.8) for q in fp}, "P", bias=bias, ao=0)
    thumb = line(add(palm, mul(dirv(hd - 70), 1.2)), add(palm, mul(dirv(hd - 50), 3.0)))
    Lr.paint({q: (-0.2, -0.5, 0.8) for q in thumb}, "P", bias=bias - 1, ao=0)
    info["hand_" + side] = add(palm, mul(d, 2.0))
    info["elbow_" + side] = el
    info["cuff_" + side] = cuff
    info["sleeve_" + side] = drape


# =========================================================================== cracks (kintsugi)
def _crack(seed, start, ang, n, step=1.7, jit=40):
    pts = [start]
    a = ang
    out = []
    for i in range(n):
        a += (hash01(seed, i, 61) - 0.5) * 2 * jit
        nxt = add(pts[-1], mul(dirv(a), step + hash01(seed, i, 62)))
        pts.append(nxt)
        if hash01(seed, i, 63) > 0.8 and i > 1:
            b = _crack(seed * 7 + i, nxt, a + (40 if hash01(seed, i, 64) > 0.5 else -40), max(2, n // 3), step, jit)
            out += b
    out.insert(0, pts)
    return out


CRACKS = []  # (threshold, layer, [polylines in rest coords])
for _i, (_s, _a, _n, _thr, _lay) in enumerate((
        ((104, 40), 95, 2, 0.0, "Head"),        # kintsugi tear under the eye
        ((99, 56), 95, 6, 0.15, "Body"), ((93, 60), 110, 7, 0.3, "Body"), ((104, 68), 120, 5, 0.45, "Body"),
        ((96, 146), -80, 9, 0.2, "Body"), ((110, 145), -100, 8, 0.35, "Body"), ((82, 143), -70, 7, 0.5, "Body"),
        ((91, 100), 80, 6, 0.55, "Body"), ((105, 96), 70, 6, 0.6, "Body"),
        ((98, 34), -60, 3, 0.4, "Head"), ((99, 44), 150, 3, 0.65, "Head"))):
    CRACKS.append((_thr, _lay, _crack(_i + 3, _s, _a, _n)))


def draw_cracks(imgs, j, p, phase, glow):
    amount = max(p["crack"], 1.0 if phase == 2 else 0.08)
    X = j["X"]
    hd_off = sub(j["Hd"], j["X"](REST["Hd"]))
    hot = phase == 2 or p["crack"] > 0.55
    for thr, lay, polys in CRACKS:
        if thr > amount:
            continue
        src = imgs[lay].load()
        for pl in polys:
            q = [X(c) for c in pl]
            if lay == "Head":
                q = [add(c, hd_off) for c in q]
            for pt in polyline(q):
                if not inb(*pt) or src[pt][3] == 0 or src[pt][:3] == RGBA["OUT"][:3]:
                    continue
                if hot:
                    glow.put([pt], "L" if hash01(*pt, 71) > 0.45 else "Y3")
                    for a, b in ((1, 0), (0, 1)):
                        qq = (pt[0] + a, pt[1] + b)
                        if inb(*qq) and src[qq][3] and qq not in glow.px and hash01(*qq, 73) > 0.45:
                            glow.put([qq], "R3" if phase == 2 else "Y1")
                else:
                    glow.put([pt], "G4" if hash01(*pt, 72) > 0.3 else "G5")


# =========================================================================== FX helpers
def smear_color(age, edge_d):
    if age < 0.18:
        return "L" if edge_d < 1.5 else "Y3"
    if age < 0.4:
        return "Y3" if edge_d < 1.5 else "Y2"
    if age < 0.65:
        return "Y2" if edge_d < 1.5 else "Y1"
    return "Y1" if edge_d < 1.5 else "Y0"


def fx_orb(F, Fb, c, r, fi=0, rays=0):
    cx, cy = c
    for q in mask_disc(c, r + 3):
        d = math.hypot(q[0] + .5 - cx, q[1] + .5 - cy)
        if d < r * 0.45:
            F.put([q], "L")
        elif d < r * 0.75:
            F.put([q], "Y3")
        elif d < r:
            F.put([q], "Y2")
        elif d < r + 1.5:
            Fb.put([q], "Y1", 170)
        else:
            Fb.put([q], "Y1", 70)
    for k in range(rays):
        a = k * (360 / rays) + fi * 11
        ln = r + 4 + (k % 2) * 4
        for s in range(int(r * 0.8), int(ln)):
            q = add(c, mul(dirv(a), s))
            F.put([q], "Y3" if s < ln - 2 else "Y1")


def fx_star(F, c, r):
    x, y = ipt(c)
    F.put([(x, y)], "L")
    for k in range(1, r + 1):
        cc = "Y3" if k <= max(1, r // 2) else "Y1"
        F.put([(x + k, y), (x - k, y), (x, y + k), (x, y - k)], cc)
    if r >= 3:
        F.put([(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)], "Y2")


def fx_converge(F, c, R, prog, n, fi, seed=0):
    """Light motes streaming into point c (prog 0..1)."""
    for k in range(n):
        a = hash01(k, seed, 81) * 360
        age = (prog + hash01(k, seed, 82) * 0.6) % 1.0
        d = R * (1 - age) + 2
        q = add(c, mul(dirv(a), d))
        q2 = add(c, mul(dirv(a), d + 2.5))
        F.put([q], "Y3" if age > 0.6 else "Y2")
        F.put([q2], "Y1")


def fx_ring(F, Fb, c, r, th, k=1.0, bright=1.0, fi=0, info=None, gaps=0.0):
    cx, cy = c
    pts = set()
    for y in range(int(cy - r * k) - 3, int(cy + r * k) + 4):
        for x in range(int(cx - r) - 3, int(cx + r) + 4):
            dx, dy = x + .5 - cx, (y + .5 - cy) / k
            d = math.hypot(dx, dy)
            e = r - d
            if -1 <= e <= th:
                ang = math.degrees(math.atan2(dy, dx))
                if gaps > 0 and vnoise(ang / 14 + fi * 0.7, 91) < gaps:
                    continue
                if e < 0:
                    c_ = "Y1"
                elif e < 1.2:
                    c_ = "Y3" if bright > 0.7 else "Y2"
                elif e < th * 0.45:
                    c_ = "L" if bright > 0.7 else "Y3"
                elif e < th * 0.8:
                    c_ = "Y2"
                else:
                    c_ = "Y1"
                F.put([(x, y)], c_)
                pts.add((x, y))
            elif th < e < th + 10 and bright > 0.8:
                Fb.put([(x, y)], "Y2", int(90 * bright * (1 - (e - th) / 10)))
    if info is not None:
        info["nova_px"] |= pts
    return pts


def fx_rays(F, c, r0, r1, n, rotd, col="Y2", thick=False):
    for k in range(n):
        a = k * 360 / n + rotd
        ln = r1 if k % 2 == 0 else r0 + (r1 - r0) * 0.6
        for s in range(int(r0), int(ln)):
            q = add(c, mul(dirv(a), s))
            F.put([q], col if s < ln - 3 else "Y1")
            if thick and s < ln * 0.7:
                F.put([add(q, mul(dirv(a + 90), 1))], "Y1")


def petal(F, c, ang, big=False, col="W5", edge="Y1"):
    x, y = ipt(c)
    d = dirv(ang)
    F.put([(x, y)], col)
    F.put([ipt(add(c, mul(d, 1)))], col)
    if big:
        F.put([ipt(add(c, mul(d, 2)))], "Y2")
        F.put([ipt(add(c, mul(dirv(ang + 90), 1)))], edge)
    else:
        F.put([ipt(add(c, mul(dirv(ang + 90), 1)))], edge)


def fx_wing_smear(F, info, geo_prev, geo_cur, front_only=None):
    """Fill between the previous and current positions of each primary root (motion smear)."""
    pts_all = set()
    for bp, bc in zip(geo_prev, geo_cur):
        if bp["depth"] != 0:
            continue
        A, B = bp["pts"], bc["pts"]
        n = min(len(A), len(B))
        for i in range(int(n * 0.35), n - 1, 1):
            quad = [A[i], A[i + 1], B[i + 1], B[i]]
            for q in poly_mask(quad):
                if not inb(*q):
                    continue
                pts_all.add(q)
        # store the current primary for colouring
    cur_lines = [b["pts"] for b in geo_cur if b["depth"] == 0]
    prev_lines = [b["pts"] for b in geo_prev if b["depth"] == 0]

    def dmin(q, lines):
        best = 1e9
        for pl in lines:
            for c in pl[::2]:
                d = abs(c[0] - q[0]) + abs(c[1] - q[1])
                if d < best:
                    best = d
        return best
    for q in pts_all:
        if front_only and not front_only(q):
            continue
        dc, dp = dmin(q, cur_lines), dmin(q, prev_lines)
        age = dc / (dc + dp + 1e-6)
        if age > 0.75 and (q[0] + q[1]) % 2:
            continue
        F.put([q], smear_color(age, 2.0 if age > 0.3 else 1.0))
    info["smear"] |= pts_all


# =========================================================================== render one frame
def render(p, fi, sec, phase, prev=None):
    j = joints(p, sec)
    L = {n: Layer(n) for n in SHADED}
    FX = {n: FXLayer(n) for n in ("FXBack", "Glow", "FX")}
    info = {"smear": set(), "wing_px": set(), "nova_px": set(), "j": j}
    ph = j["ph"]
    # wings
    geos = {}
    for key, s, bias in (("wr", 1, -1), ("wl", -1, 0)):
        ang, spread, scale = p[key]
        geo = wing_geometry(j["Wr"], s, ang, spread, scale, p["wsway"], ph + (0.0 if s < 0 else 1.1))
        geos[key] = geo
        draw_wing(L["Wings"], FX["Glow"], info, geo, bias, phase, fi)
        wing_membrane(FX["FXBack"], geo, j["Wr"], phase, p.get("membrane", 1.0) * max(0.0, 1 - p["dissolve"] * 1.6))
    # knot of roots where the wings leave the back
    L["Wings"].paint(n_dome(j["Wr"], 5.0, 6.0), "B", bias=-1)
    info["geos"] = geos
    draw_halo(L["Halo"], FX["Glow"], FX["FXBack"], j, p, fi, phase)
    sec_ = {}
    draw_hair_back(L, j, p, sec_)
    info["veil_px"] = sec_.get("veil_px", set())
    draw_train(L, FX["Glow"], j, p, info)
    draw_arm(L["ArmFar"], FX["Glow"], j, p, "f", info, phase)
    draw_body(L, FX["Glow"], j, p, sec, info, phase)
    draw_head(L, FX["Glow"], j, p, fi, phase, info)
    draw_arm(L["ArmNear"], FX["Glow"], j, p, "n", info, phase)
    # summon roots: tendrils from under the hem boring into the ground
    if p["tendrils"] > 0:
        draw_ground_roots(L["Train"], FX, j, p, info, phase, fi)
    for f in p["fx"]:
        FX_FUNCS[f[0]](FX, info, j, p, fi, prev, *f[1:])
    return L, FX, info


def draw_ground_roots(Lr, FX, j, p, info, phase, fi):
    k_ = p["tendrils"]
    rows = None
    hy = j["Hm"][1] - j["lift"]
    for k, (ox, ex) in enumerate(((-16, -40), (-6, -18), (4, 6), (13, 30), (21, 52))):
        base = (j["Hm"][0] + ox, hy - 4)
        end = (j["Hm"][0] + ex * (0.4 + 0.6 * k_), FLOOR + 2)
        mid = lerp(base, end, 0.5)
        mid = add(mid, (math.sin(k * 2.1 + fi * 0.5) * 4, -2))
        pts = qbez(base, mid, lerp(base, end, k_ if k_ < 1 else 1.0), 14)
        nm, _ = tube(pts, 3.4, 1.2, ex=1.5)
        Lr.paint(nm, "B", bias=0, ao=0)
        for q in pts[2::3]:
            FX["Glow"].put([q], "Y2" if phase == 1 else "R4")
        if k_ >= 0.8:
            e = ipt(pts[-1])
            for dx in range(-5, 6):
                FX["FX"].put([(e[0] + dx, FLOOR)], "Y2" if abs(dx) < 3 else "Y1")
                if abs(dx) < 2:
                    FX["FX"].put([(e[0] + dx, FLOOR - 1)], "Y3")


# ------------------------------------------------------------------ per-tag FX functions
def fx_hand_orb(FX, info, j, p, fi, prev, side, r, rays=0):
    c = info["hand_" + side]
    fx_orb(FX["FX"], FX["FXBack"], c, r, fi, rays)
    info["orb_" + side] = c


def fx_gather(FX, info, j, p, fi, prev, where, R, prog, n):
    c = info["hand_n"] if where == "hand" else info["heart"] if where == "heart" else info["hand_f"]
    fx_converge(FX["FX"], c, R, prog, n, fi, seed=len(where))


def fx_beam_up(FX, info, j, p, fi, prev, width, bright):
    c = info["hand_n"]
    x0 = c[0]
    for y in range(0, int(c[1])):
        wv = width * (0.7 + 0.3 * math.sin(y * 0.4 + fi * 2)) * (0.5 + 0.5 * min(1, (c[1] - y) / 12 + 0.4))
        for x in range(int(x0 - wv - 2), int(x0 + wv + 3)):
            d = abs(x + .5 - x0)
            if d < wv * 0.4:
                FX["FX"].put([(x, y)], "L" if bright > 0.6 else "Y3")
            elif d < wv * 0.75:
                FX["FX"].put([(x, y)], "Y3" if bright > 0.6 else "Y2")
            elif d < wv:
                FX["FX"].put([(x, y)], "Y2" if bright > 0.6 else "Y1")
            elif d < wv + 2 and (y + fi) % 3:
                FX["FXBack"].put([(x, y)], "Y1", 140)
    for k in range(10):
        y = hash01(k, fi, 5) * c[1]
        x = x0 + (hash01(k, fi, 6) - 0.5) * width * 5
        FX["FX"].put([(x, y), (x, y + 1)], "Y2")
    if bright > 0.6:
        fx_rays(FX["FX"], c, 4, 16, 10, fi * 9, "Y3")
        fx_star(FX["FX"], c, 6)


def fx_spear(FX, info, j, p, fi, prev, solid, length=40, thrown=False):
    """Spear of light held along the hand (horizontal, pointing right)."""
    c = info["hand_n"]
    y = int(round(c[1])) - 1
    x0 = c[0] + 3
    x1 = c[0] + 3 + length
    F = FX["FX"]
    pts = set()
    for x in range(int(x0), int(x1) + 1):
        t = (x - x0) / (x1 - x0)
        if solid < 1 and hash01(x, fi, 21) > solid:
            if hash01(x, fi, 22) > 0.6:
                F.put([(x, y + int((hash01(x, fi, 23) - 0.5) * 8))], "Y2")
            continue
        F.put([(x, y)], "L")
        F.put([(x, y - 1)], "Y2" if t < 0.85 else "Y3")
        F.put([(x, y + 1)], "Y1" if t < 0.85 else "Y3")
        pts |= {(x, y), (x, y - 1), (x, y + 1)}
    if solid >= 0.6:
        # leaf head
        hx = x1
        for s in range(9):
            w_ = int(3 * math.sin(math.pi * s / 9) + 0.5)
            for dy in range(-w_, w_ + 1):
                F.put([(int(hx + s), y + dy)], "L" if abs(dy) < max(1, w_ - 1) else "Y2")
        F.put([(int(hx) + 9, y)], "Y3")
        # root-guard flare at the butt
        for dy in (-2, -1, 1, 2):
            F.put([(int(x0) + 1 + abs(dy), y + dy)], "Y1")
    info["spear"] = (x0, x1, y)


def fx_release(FX, info, j, p, fi, prev, r):
    c = info["hand_n"]
    fx_star(FX["FX"], add(c, (2, -1)), r)
    for k in range(3):
        yy = int(c[1]) - 3 + k * 3
        for x in range(int(c[0]) + 4, W):
            if (x + k * 3) % 9 < 6:
                FX["FX"].put([(x, yy)], "Y2" if k == 1 else "Y1")


def fx_nova_ring(FX, info, j, p, fi, prev, r, th, bright):
    c = (info["heart"][0] - 1, info["heart"][1] + 6)
    fx_ring(FX["FX"], FX["FXBack"], c, r, th, k=0.92, bright=bright, fi=fi, info=info, gaps=0.0 if bright > 0.8 else 0.35)
    if bright > 0.8:
        fx_rays(FX["FX"], c, r * 0.3, r * 0.95, 16, fi * 7, "Y3")
    info["nova_c"] = c
    info["nova_r"] = r


def fx_flash(FX, info, j, p, fi, prev, r):
    c = info["heart"]
    fx_orb(FX["FX"], FX["FXBack"], c, r, fi, rays=12)


def fx_wsmear(FX, info, j, p, fi, prev, key):
    """Crescent smear traced by the outer parts of the primaries between the previous and current pose."""
    if prev is None:
        return
    s = 1 if key == "wr" else -1
    a0, s0, c0 = prev[0][key]
    a1, s1, c1 = p[key]
    N = 16
    F = FX["FX"]
    tracks = {}
    for st in range(N + 1):
        u = st / N
        ang, spread, scale = a0 + (a1 - a0) * u, s0 + (s1 - s0) * u, c0 + (c1 - c0) * u
        geo = wing_geometry(j["Wr"], s, ang, spread, scale, 0.0, j["ph"])
        for b in geo:
            if b["depth"] != 0 or b["k"] == 3:
                continue
            pl = b["pts"]
            n = len(pl)
            for ti in range(31, 51):
                tracks.setdefault((b["k"], ti, 50), []).append((pl[min(n - 1, int(ti / 50 * (n - 1)))], 1 - u))
    best = {}
    keys = sorted(tracks)
    for (k, i, n) in keys:
        nxt = (k, i + 1, n)
        if nxt not in tracks:
            continue
        A, B = tracks[(k, i, n)], tracks[nxt]
        t = i / n
        for st in range(len(A) - 1):
            quad = [A[st][0], B[st][0], B[st + 1][0], A[st + 1][0]]
            age = A[st + 1][1]
            for q in poly_mask(quad) | set(line(A[st][0], A[st + 1][0])):
                if inb(*q) and (q not in best or best[q][0] > age):
                    best[q] = (age, t)
    for q, (age, t) in best.items():
        v = age * 0.85 + (1.0 - t) * 1.1
        if v > 0.95:
            continue
        if v > 0.62 and (q[0] + q[1]) % 2:
            continue
        F.put([q], smear_color(v, 0.5 if t > 0.93 else 2.0))
    info["smear"] |= {q for q, (age, _) in best.items() if age < 0.7}


def fx_dust(FX, info, j, p, fi, prev, cx, spread, stage):
    for k in range(int(10 * spread)):
        x = cx + (hash01(k, 1, 31) - 0.5) * spread * 60
        y = FLOOR - hash01(k, 2, 32) * (4 + stage * 5)
        FX["FX"].put([(x, y)], "Y1" if k % 3 == 0 else "W3")
        if stage > 0 and k % 2:
            FX["FX"].put([(x + 1, y - 1)], "W4")


def fx_petals(FX, info, j, p, fi, prev, n, spread, rise):
    c = info["heart"]
    for k in range(n):
        x = c[0] + (hash01(k, 3, 51) - 0.5) * spread + rise * 0.4 * hash01(k, 4, 52) * 30
        y = c[1] + 40 - hash01(k, 5, 53) * 90 - rise * (10 + hash01(k, 6, 54) * 30)
        petal(FX["FX"], (x, y), hash01(k, fi, 55) * 360, big=k % 3 == 0)


def fx_crown_shatter(FX, info, j, p, fi, prev, prog):
    for k, tp in enumerate(info.get("crown_tips", [])):
        for s in range(2):
            a = -90 + (k - 2) * 28 + s * 15
            q = add(tp, mul(dirv(a), 3 + prog * (10 + s * 6)))
            q = add(q, (0, prog * prog * 6))
            FX["FX"].put([q, add(q, (1, 0))], "B4" if s else "B3")
            FX["FX"].put([add(q, (0, 1))], "B1")
    fx_star(FX["FX"], add(j["Hd"], (1, -9)), int(3 + prog * 3))


def fx_groundglow(FX, info, j, p, fi, prev, k):
    """Glowing fissure racing out along the floor from under her (spike telegraph)."""
    cx = j["Hm"][0]
    reach = 30 + 60 * k
    for x in range(int(cx - reach), int(cx + reach) + 1):
        d = abs(x - cx) / reach
        if hash01(x // 3, fi, 45) < 0.2 + d * 0.3:
            continue
        FX["FX"].put([(x, FLOOR)], "L" if d < 0.3 * k else "Y2" if d < 0.7 else "Y1")
        if d < 0.8 and (x + fi) % 3 == 0:
            FX["FX"].put([(x, FLOOR - 1)], "Y2")
        if hash01(x, fi, 46) > 0.9:
            FX["FX"].put([(x, FLOOR - 2 - int(hash01(x, fi, 47) * 8))], "Y2")


FX_FUNCS = {"orb": fx_hand_orb, "gather": fx_gather, "beam": fx_beam_up, "spear": fx_spear, "release": fx_release,
            "nova": fx_nova_ring, "flash": fx_flash, "wsmear": fx_wsmear, "dust": fx_dust, "petals": fx_petals,
            "crown": fx_crown_shatter, "groundglow": fx_groundglow}


# =========================================================================== compose, phase 2, dissolve
def compose(L, FX, info, p, phase):
    imgs = {}
    for n in BASE_LAYERS:
        if n in L:
            imgs[n] = render_layer(L[n], burn=(phase == 2 and n == "Wings"))
    draw_cracks(imgs, info["j"], p, phase, FX["Glow"])
    for n in ("FXBack", "Glow", "FX"):
        imgs[n] = FX[n].image()
    return imgs


def p2_fire(info, fi, k):
    """Robes ablaze: white-gold flame tongues licking up from the hem, sleeve ends and train."""
    out = FXLayer("Fire")
    if k <= 0.01:
        return out.image()
    rows = info["robe_bottom"]
    j = info["j"]
    for x, yb in rows.items():
        n = vnoise(x / 3.0 + fi * 0.9, 13) * 0.7 + vnoise(x / 7.0 - fi * 0.4, 14) * 0.5
        h = (3 + n * 19) * k
        for s in range(int(h)):
            y = yb - s
            f = s / max(1.0, h)
            c = "L" if f < 0.15 else "Y3" if f < 0.35 else "Y2" if f < 0.55 else "Y1" if f < 0.75 else "R4"
            out.put([(x, y)], c)
        if h > 8 and hash01(x, fi, 15) > 0.6:
            out.put([(x, int(yb - h - 2))], "R3")
    for key in ("train_px", "veil_px"):
        bot = {}
        for (x, y) in info.get(key, ()):
            if y > bot.get(x, -1):
                bot[x] = y
        for x, yb in bot.items():
            if x in rows and rows[x] >= yb - 2:
                continue
            h = (2 + vnoise(x / 2.8 + fi * 0.8, 19) * 10) * k
            for s in range(int(h)):
                f = s / max(1.0, h)
                out.put([(x, yb - s)], "Y3" if f < 0.25 else "Y2" if f < 0.5 else "Y1" if f < 0.75 else "R4")
    for side in ("n", "f"):
        dr = info.get("sleeve_" + side)
        if not dr:
            continue
        bot = {}
        for (x, y) in dr:
            if y > bot.get(x, -1):
                bot[x] = y
        for x, yb in bot.items():
            h = (1 + vnoise(x / 2.5 + fi, 17 + len(side)) * 6) * k
            for s in range(int(h)):
                f = s / max(1.0, h)
                out.put([(x, yb - s)], "Y3" if f < 0.3 else "Y2" if f < 0.6 else "R4")
    return out.image()


def p2_embers(info, fi, k):
    out = FXLayer("Embers")
    if k <= 0.01:
        return out.image()
    rows = list(info["robe_bottom"].items())
    j = info["j"]
    for t in range(int(34 * k)):
        if t % 3 == 0 and info["wing_px"]:
            wp = sorted(info["wing_px"])
            s = wp[int(hash01(t, 2, 86) * len(wp))]
        else:
            s = rows[int(hash01(t, 5, 87) * len(rows))]
        age = (fi * 0.23 + hash01(t, 6, 88)) % 1.0
        x = s[0] - age * 8 + math.sin(age * 7 + t) * 3
        y = s[1] - 3 - age * 44
        c = "Y3" if age < 0.15 else "Y2" if age < 0.35 else "Y1" if age < 0.55 else "R4" if age < 0.75 else "E1"
        out.put([(x, y)], c)
        if age < 0.3:
            out.put([(x + 1, y + 1)], "R4")
    return out.image()


def dissolve(imgs, d, fi, info):
    """Death: the body comes apart from the hem upward into petals and light."""
    if d <= 0:
        return
    F = FXLayer("petals")
    for n in SHADED + ["Glow", "FXBack"]:
        im = imgs[n]
        px = im.load()
        for y in range(H):
            for x in range(W):
                if px[x, y][3] == 0:
                    continue
                v = 0.62 * (y - 8) / 150.0 + 0.38 * hash01(x // 2, y // 2, 97)
                v = 1 - v  # hem (large y) dissolves first
                if v < d * 1.25 - 0.1:
                    px[x, y] = (0, 0, 0, 0)
                    if hash01(x, y, 98 + fi) > 0.985:
                        age = hash01(x, y, 99)
                        petal(F, (x + 6 + age * 14 + d * 20, y - 6 - age * 26 - d * 30), hash01(x, fi, 5) * 360,
                              big=age > 0.6)
                elif v < d * 1.25 - 0.02:
                    px[x, y] = RGBA["Y3" if hash01(x, y, 96) > 0.5 else "Y2"]
    fx = imgs["FX"]
    fx.alpha_composite(F.image())


# =========================================================================== secondary (cloth phase / lag)
def secondary(frames, loop, period_ms=1200):
    res = []
    n = len(frames)
    tacc = 0
    prev_bob = frames[-1][1]["bob"] if loop else frames[0][1]["bob"]
    lag = 0.0
    vel = 0.0
    for pas in range(2 if loop else 1):
        res = []
        tacc = 0
        for i, (ms, p) in enumerate(frames):
            ph = 2 * math.pi * i / n if loop else 2 * math.pi * tacc / period_ms
            tacc += ms
            db = p["bob"] - prev_bob
            target = db * 1.1           # rising -> hem lags below (negative lift)
            vel = vel * 0.4 + (target - lag) * 0.5
            lag = max(-4, min(4, lag + vel))
            res.append({"ph": ph, "lift": -lag})
            prev_bob = p["bob"]
    return res


# =========================================================================== animations
WL0, WR0 = 198, -18   # neutral wing fan angles (left / right)

def anim_idle():
    fr = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        fr.append((150, P_(bob=int(round(-1.6 * math.sin(a))), head=(0, 0),
                           wl=(WL0 + 2.5 * math.sin(a - 0.8), 1.0 + 0.05 * math.sin(a - 0.5), 1.0),
                           wr=(WR0 - 2.5 * math.sin(a - 0.8), 1.0 + 0.05 * math.sin(a - 0.5), 0.92),
                           hn=(119, 73 + round(math.sin(a - 0.6))), hf=(71, 69 + round(math.sin(a - 0.9))),
                           halo=1.0 + 0.15 * math.sin(a), wind=-1.0)))
    return fr


def anim_glide():
    fr = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        fr.append((110, P_(bob=int(round(-1.5 * math.sin(a))), lean=9, wind=-9 + 1.5 * math.sin(a),
                           wl=(WL0 - 6 + 3 * math.sin(a - 0.8), 0.8, 1.02), wr=(WR0 - 14 - 3 * math.sin(a - 0.8), 0.78, 0.8),
                           hn=(106, 84), hn_dir=150, hf=(80, 82), hf_dir=160, wsway=7.0, eyes=0.6)))
    return fr


def anim_sweep():
    K = [  # ms, bob, lean, wr(ang,spread,scale), wl, hn, fx
        (120, -2, -3, (-66, 1.05, 0.95), (212, 1.05, 1.0), (118, 64), ()),
        (120, -5, -6, (-92, 1.1, 1.0), (224, 1.1, 1.0), (120, 56), ()),
        (170, -6, -7, (-104, 1.15, 1.02), (230, 1.1, 1.0), (120, 52), ()),                     # telegraph hold
        (60, 2, 6, (44, 1.2, 1.3), (214, 1.0, 1.0), (126, 82), (("wsmear", "wr"),)),           # window 1
        (80, 4, 8, (66, 1.3, 1.36), (206, 1.0, 1.0), (126, 88), (("wsmear", "wr"), ("dust", 150, 1.0, 0))),
        (110, 3, 5, (62, 1.2, 1.3), (236, 1.1, 1.0), (122, 82), (("dust", 150, 1.0, 1),)),
        (140, -3, -2, (22, 1.1, 1.1), (254, 1.2, 1.04), (118, 70), ()),                        # back wing rises
        (60, 3, 5, (58, 1.2, 1.26), (146, 1.2, 1.28), (124, 84), (("wsmear", "wl"),)),          # window 2
        (80, 4, 6, (64, 1.25, 1.3), (114, 1.3, 1.36), (124, 88), (("wsmear", "wl"), ("dust", 96, 2.2, 0))),
        (120, 3, 3, (44, 1.1, 1.14), (130, 1.15, 1.2), (120, 82), (("dust", 96, 2.2, 1),)),
        (140, 0, 1, (6, 1.05, 0.98), (174, 1.05, 1.02), (119, 77), ()),
        (160, 0, 0, (WR0, 1.0, 0.92), (WL0, 1.0, 1.0), (119, 74), ()),
    ]
    fr = []
    for i, (ms, bob, lean, wr, wl, hn, fx) in enumerate(K):
        fr.append((ms, P_(bob=bob, lean=lean, wr=wr, wl=wl, hn=hn, hn_dir=-40 if hn[1] < 70 else 40,
                          eyes=1.0 if 2 <= i <= 8 else 0.5, wind=(-2, -2, -3, 6, 5, 2, -2, 5, 4, 1, 0, -1)[i],
                          wsway=2.0 if i in (3, 4, 7, 8) else 5.0, fx=fx)))
    return fr


def anim_rain():
    K = [  # ms, bob, hn, hn_dir, hf, head, wing spread, fx
        (120, 0, (120, 66), -20, (72, 72), (0, 0), 1.0, ()),
        (120, -2, (121, 48), -60, (70, 78), (0, -1), 1.08, ()),
        (130, -3, (119, 34), -75, (68, 82), (0, -1), 1.14, (("orb", "n", 2.0),)),
        (110, -4, (118, 30), -80, (67, 84), (1, -1), 1.18, (("orb", "n", 3.5), ("gather", "hand", 30, 0.2, 14))),
        (110, -4, (118, 29), -80, (67, 84), (1, -1), 1.2, (("orb", "n", 5.0, 8), ("gather", "hand", 30, 0.5, 16))),
        (150, -5, (118, 28), -80, (67, 84), (1, -2), 1.22, (("orb", "n", 6.5, 12), ("gather", "hand", 26, 0.8, 18))),
        (70, -6, (118, 27), -80, (66, 85), (1, -2), 1.3, (("beam", 6.0, 1.0), ("orb", "n", 5.0, 16))),   # spawn
        (120, -5, (118, 28), -80, (67, 84), (1, -1), 1.25, (("beam", 3.5, 0.5), ("orb", "n", 2.5))),
        (140, -2, (120, 46), -40, (70, 78), (0, 0), 1.1, ()),
        (160, 0, (119, 70), 40, (71, 70), (0, 0), 1.0, ()),
    ]
    fr = []
    for i, (ms, bob, hn, hd, hf, head, sp, fx) in enumerate(K):
        fr.append((ms, P_(bob=bob, hn=hn, hn_dir=hd, hf=hf, hf_dir=160, head=head, eln=(0.8, 0.2),
                          wl=(WL0 + 6 + (sp - 1) * 50, sp, 1.0), wr=(WR0 - 6 - (sp - 1) * 50, sp, 0.9),
                          eyes=1.0 if 2 <= i <= 7 else 0.3, halo=1.0 + (0.8 if 3 <= i <= 6 else 0),
                          lean=-2 if 2 <= i <= 7 else 0, wind=-1, fx=fx)))
    return fr


def anim_lance():
    K = [  # ms, bob, lean, hn, hn_dir, hf, fx
        (110, 0, -1, (121, 64), 20, (70, 70), ()),
        (120, -1, -4, (118, 58), 0, (66, 66), (("gather", "hand", 20, 0.3, 10),)),
        (130, -2, -6, (116, 56), 0, (64, 64), (("spear", 0.3, 30), ("gather", "hand", 20, 0.6, 12))),
        (120, -2, -7, (115, 55), 0, (63, 63), (("spear", 0.65, 34),)),
        (120, -2, -8, (114, 55), 0, (62, 62), (("spear", 1.0, 36),)),
        (150, -3, -9, (112, 54), 0, (61, 61), (("spear", 1.0, 36), ("orb", "n", 2.0))),              # telegraph
        (60, 1, 9, (135, 57), 0, (72, 76), (("release", 6),)),                                        # spawn
        (110, 1, 7, (133, 58), 10, (73, 76), (("release", 3),)),
        (130, 0, 3, (126, 64), 30, (72, 73), ()),
        (150, 0, 0, (120, 71), 50, (71, 70), ()),
    ]
    fr = []
    for i, (ms, bob, lean, hn, hd, hf, fx) in enumerate(K):
        fr.append((ms, P_(bob=bob, lean=lean, hn=hn, hn_dir=hd, hf=hf, hf_dir=190, eln=(0.3, 1), elf=(-0.3, 1),
                          eyes=1.0 if 2 <= i <= 7 else 0.3, wind=(-1, 0, 1, 1, 1, 2, -6, -5, -3, -1)[i],
                          wl=(WL0 + (6 if i < 6 else -8), 1.05 if i < 6 else 0.95, 1.0),
                          wr=(WR0 + (-6 if i < 6 else 10), 1.05 if i < 6 else 0.95, 0.9), fx=fx)))
    return fr


def anim_nova():
    fr = []
    for i in range(14):
        if i < 8:
            k = i / 7
            bob = -int(round(1 + k * 5))
            pose = dict(hn=(99, 64), hn_dir=190, hf=(97, 62), hf_dir=10, eln=(0.6, 1), elf=(-0.6, 1),
                        wl=(WL0 + 22 * k, 1.0 - 0.45 * k, 1.0 - 0.14 * k), wr=(WR0 - 22 * k, 1.0 - 0.45 * k, 0.9 - 0.12 * k),
                        halo=1.0 + k * 1.2, crack=0.2 + 0.5 * k, eyes=0.2 if i < 3 else 1.0, lean=-2,
                        shake=(0, 0, 0, 0, 0, 1, -1, 1)[i], head=(0, 1 if i > 3 else 0),
                        fx=(("gather", "heart", 40 - k * 12, k, int(8 + 14 * k)),) +
                           ((("flash", 2 + k * 4),) if i >= 4 else ()))
        elif i <= 10:
            r = (28, 56, 84)[i - 8]
            pose = dict(hn=(138, 60), hn_dir=-20, hf=(60, 58), hf_dir=200, eln=(0.3, 1), elf=(-0.3, 1),
                        wl=(WL0 + 4, 1.45, 1.08), wr=(WR0 - 4, 1.45, 1.0), halo=2.2, crack=0.9, eyes=1.0, lean=-4,
                        head=(-1, -1), fx=(("nova", r, (12, 10, 7)[i - 8], (1.0, 1.0, 0.7)[i - 8]),)
                        + ((("flash", 8),) if i == 8 else ()))
            bob = -6
        else:
            k = (i - 10) / 3
            bob = int(round(-6 + k * 6))
            pose = dict(hn=(lerp((138, 60), (113, 77), k)), hf=lerp((60, 58), (83, 79), k), hn_dir=40 + 60 * k,
                        wl=(WL0, 1.45 - 0.45 * k, 1.06 - 0.06 * k), wr=(WR0, 1.45 - 0.45 * k, 1.0 - 0.08 * k),
                        halo=2.0 - k, crack=0.8 - 0.7 * k, eyes=1.0 - 0.7 * k,
                        fx=((("nova", 96, 3, 0.4),) if i == 11 else ()) + (("petals", 10 - (i - 11) * 3, 70, k),))
        ms = (110, 110, 110, 110, 120, 120, 140, 160, 60, 80, 100, 140, 160, 180)[i]
        fr.append((ms, P_(bob=bob, **pose)))
    return fr


def anim_summon():
    K = [  # ms, bob, hn, hn_dir, hf, hf_dir, tendrils, fx
        (120, 0, (121, 66), -10, (70, 68), 190, 0, ()),
        (120, -3, (124, 50), -50, (66, 52), 230, 0, (("orb", "n", 1.5), ("orb", "f", 1.5))),
        (130, -5, (123, 40), -70, (66, 42), 250, 0, (("orb", "n", 3.0), ("orb", "f", 2.5))),
        (140, -6, (122, 37), -80, (67, 39), 260, 0, (("orb", "n", 4.5, 8), ("orb", "f", 3.5, 6))),   # telegraph
        (70, 1, (124, 98), 90, (68, 98), 90, 0.5, (("orb", "n", 3.0), ("orb", "f", 2.5))),
        (70, 4, (123, 102), 90, (69, 102), 90, 1.0, (("dust", 96, 2.6, 0), ("groundglow", 1.0))),      # spawn
        (130, 4, (122, 101), 90, (70, 101), 90, 1.0, (("dust", 96, 2.6, 1), ("groundglow", 0.8))),
        (130, 3, (121, 96), 90, (71, 96), 90, 0.8, (("groundglow", 0.5),)),
        (140, 1, (120, 84), 80, (71, 84), 100, 0.4, ()),
        (160, 0, (119, 72), 50, (71, 70), 150, 0.0, ()),
    ]
    fr = []
    for i, (ms, bob, hn, hd, hf, hfd, tn, fx) in enumerate(K):
        fr.append((ms, P_(bob=bob, hn=hn, hn_dir=hd, hf=hf, hf_dir=hfd, tendrils=tn, eln=(0.6, 0.6), elf=(-0.6, 0.6),
                          eyes=1.0 if 2 <= i <= 7 else 0.3, halo=1.0 + (0.6 if 2 <= i <= 6 else 0),
                          wl=(WL0 + (16 if i in (2, 3) else -16 if 4 <= i <= 7 else 0), 1.0 + (0.15 if i in (2, 3) else 0), 1.0),
                          wr=(WR0 - (16 if i in (2, 3) else -16 if 4 <= i <= 7 else 0), 1.0 + (0.15 if i in (2, 3) else 0), 0.9),
                          wind=(0, 0, 0, 0, 2, 3, 2, 1, 0, 0)[i], lean=(0, -2, -4, -5, 4, 6, 5, 3, 1, 0)[i], fx=fx)))
    return fr


def anim_stagger():
    K = [(80, 3, -10, (0, -1), 0.4, 1.0), (120, 5, -12, (-1, 0), 0.2, 0.8), (160, 5, -9, (-1, 1), 0.5, 0.5),
         (200, 3, -4, (0, 0), 0.8, 0.3)]
    fr = []
    for i, (ms, bob, lean, head, halo, cr) in enumerate(K):
        fr.append((ms, P_(bob=bob, lean=lean, head=head, halo=halo, crack=cr * 0.6, eyes=1.0 if i == 0 else 0.3,
                          hn=(118, 70 - i), hn_dir=40, hf=(76, 70), hf_dir=200, wind=6 - i * 2,
                          wl=(WL0 - 14 + i * 3, 0.85, 0.96), wr=(WR0 + 14 - i * 3, 0.85, 0.88), shake=(2, -1, 0, 0)[i],
                          fx=(("flash", 3),) if i == 0 else ())))
    return fr


def anim_death():
    fr = []
    for i in range(14):
        ms = (120, 120, 140, 160, 120, 120, 140, 110, 110, 120, 130, 140, 160, 300)[i]
        if i < 4:
            k = i / 3
            pose = dict(bob=3 + int(k * 4), lean=-10 + k * 16, head=(0, int(k * 2)), htilt=k * 8, eyes=1.0,
                        crack=0.3 + 0.3 * k, halo=0.8, crown_break=0.0 if i < 3 else 0.5,
                        hn=(116, 80 + k * 6), hf=(78, 82 + k * 6), wind=4 - k * 4,
                        wl=(WL0 - 10 - k * 14, 0.9 - 0.1 * k, 0.96), wr=(WR0 + 10 + k * 14, 0.9 - 0.1 * k, 0.88),
                        fx=((("crown", 0.3),) if i == 3 else ()) + ((("flash", 3),) if i == 0 else ()))
        elif i < 7:
            k = (i - 4) / 2
            pose = dict(bob=7 - int(k * 5), lean=4 - k * 8, head=(0, 1 - int(k * 2)), htilt=-k * 6, eyes=1.0,
                        crack=1.0, halo=1.2 + k, crown_break=1.0, hn=(122 + k * 10, 70 - k * 12), hf=(74 - k * 8, 70 - k * 10),
                        hn_dir=-30, hf_dir=210, wind=0,
                        wl=(WL0 - 24 + k * 30, 0.8 + 0.4 * k, 0.96), wr=(WR0 + 24 - k * 30, 0.8 + 0.4 * k, 0.88),
                        fx=(("crown", 0.6 + k * 0.4), ("flash", 3 + int(k * 4))))
        else:
            k = (i - 7) / 6
            pose = dict(bob=2 - int(k * 6), lean=-4, head=(0, -1), eyes=1.0, crack=1.0, halo=2.0 - 2 * k,
                        crown_break=1.0, hn=(132, 58), hf=(66, 60), hn_dir=-30, hf_dir=210, wind=-2 - k * 4,
                        wl=(WL0 + 6, 1.2, 0.96), wr=(WR0 - 6, 1.2, 0.88), dissolve=0.12 + k * 0.95,
                        fx=(("petals", int(14 + 24 * k), 90, k * 2),) + ((("flash", 6),) if i == 7 else ()))
        fr.append((ms, P_(**pose)))
    return fr


TAGDEFS = [("idle", anim_idle), ("glide", anim_glide), ("sweep", anim_sweep), ("rain", anim_rain),
           ("lance", anim_lance), ("nova", anim_nova), ("summon", anim_summon), ("stagger", anim_stagger),
           ("death", anim_death)]
COUNTS = {"idle": 8, "glide": 8, "sweep": 12, "rain": 10, "lance": 10, "nova": 14, "summon": 10, "stagger": 4,
          "death": 14}
LOOPS = ("idle", "glide")


# =========================================================================== output helpers
def flatten(imgs, order, w=W, h=H):
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for n in order:
        if n in imgs:
            out.alpha_composite(imgs[n])
    return out


def shift_imgs(imgs, dx):
    out = {}
    for n, im in imgs.items():
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        o.paste(im, (dx, 0))
        out[n] = o
    return out


def preview_rows(rows, path, w=W, h=H, scale=3, bg=(92, 92, 98, 255), label=True, maxcols=None):
    maxn = max(len(r[1]) for r in rows)
    if maxcols:
        maxn = min(maxn, maxcols)
    pad = 2
    lab = 10 if label else 0
    nrows = sum((len(r[1]) + maxn - 1) // maxn for r in rows)
    sheet = Image.new("RGBA", ((maxn * (w + pad)) * scale, nrows * (h + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    rr = 0
    for tag, ims in rows:
        for c0 in range(0, len(ims), maxn):
            y0 = rr * (h + pad + lab) * scale
            if label:
                d.text((4, y0 + 4), f"{tag} ({len(ims)})  frames {c0}..", fill=(230, 230, 230, 255))
            for i, im in enumerate(ims[c0:c0 + maxn]):
                fr = Image.new("RGBA", (w, h), bg)
                fr.alpha_composite(im)
                sheet.alpha_composite(fr.resize((w * scale, h * scale), Image.NEAREST),
                                      (i * (w + pad) * scale, y0 + lab * scale))
            rr += 1
    sheet.save(path)


def bbox(pts, pad=1):
    pts = [p for p in pts if inb(*p)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


PLAYER = (10, 26)


def hit_preview(flats, tags, meta, path):
    start = {t: a for t, a, _ in tags}
    s = 2
    items = []
    for t, d in meta["attacks"].items():
        for wi, w_ in enumerate(d.get("windows", [d])):
            a, b = w_["active"]
            for k in range(a, b + 1):
                items.append((t, k, d["rects"][str(k)], w_["hit"], wi))
    extra = [("idle", 0, None, None, 0)]
    for t, tg in meta["telegraph"].items():
        extra.append(("tele:" + t, tg["frame"], tg["at"], None, 0))
    for t, sp in meta["spawn"].items():
        extra.append(("spawn:" + t, sp["frame"], sp["at"], sp.get("points"), 0))
    allit = items + extra
    cols = 4
    rows_n = (len(allit) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (W + 2) * s, rows_n * (H + 12) * s), (30, 30, 36, 255))
    for i, (t, k, r, hr, wi) in enumerate(allit):
        fr = Image.new("RGBA", (W, H), (92, 92, 98, 255))
        base = t.split(":")[-1]
        fr.alpha_composite(flats[start[base] + k])
        d = ImageDraw.Draw(fr)
        hb = meta["hurtbox"]
        label = f"{t} f{k}"
        if t == "idle":
            d.rectangle([hb[0], hb[1], hb[0] + hb[2] - 1, hb[1] + hb[3] - 1], outline=(80, 255, 120, 255))
            ax, ay = meta["anchor"]
            d.line([ax - 4, ay, ax + 4, ay], fill=(255, 255, 255, 255))
            d.line([ax, ay - 5, ax, ay], fill=(255, 255, 255, 255))
            d.line([0, FLOOR, W, FLOOR], fill=(120, 200, 255, 255))
            label = "hurtbox + anchor (+ frame floor)"
        elif t.startswith("tele") or t.startswith("spawn"):
            x, y = r
            d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(0, 255, 255, 255))
            for q in (hr or []):
                d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], outline=(255, 0, 255, 255))
        else:
            d.rectangle([hr[0], hr[1], hr[0] + hr[2] - 1, hr[1] + hr[3] - 1], outline=(255, 170, 60, 255))
            d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 50, 50, 255))
            for fy, colr in ((AY, (80, 200, 255, 255)), (FLOOR + 1, (80, 120, 255, 255))):
                px_ = min(W - PLAYER[0], max(0, r[0] + r[2] - PLAYER[0] - 2))
                d.rectangle([px_, fy - PLAYER[1], px_ + PLAYER[0] - 1, fy - 1], outline=colr)
            label += f" (window {wi})"
        col = Image.new("RGBA", (W, H + 12), (30, 30, 36, 255))
        ImageDraw.Draw(col).text((2, 1), label, fill=(230, 230, 230, 255))
        col.paste(fr, (0, 12))
        sheet.alpha_composite(col.resize((W * s, (H + 12) * s), Image.NEAREST),
                              ((i % cols) * (W + 2) * s, (i // cols) * (H + 12) * s))
    sheet.save(path)


# =========================================================================== FX sheets
def _fxput(pp, w, h, x, y, c, a=255):
    a = min(ALPHA_STEPS, key=lambda s: abs(s - a)) if a < 255 else 255
    if a == 0:
        return
    x, y = int(x), int(y)
    if 0 <= x < w and 0 <= y < h:
        pp[x, y] = RGBA[c][:3] + (a,)


def fx_nova_frames():
    """160x120, 8 frames, centred: radiant ring (elliptical) with rays, shards and a gold rim."""
    w, h = 160, 120
    cx, cy = 80, 60
    frames = []
    radii = (8, 20, 32, 42, 50, 56, 60, 62)
    thick = (8, 10, 9, 8, 6, 4, 3, 2)
    for i in range(8):
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gp, rp, spp = glow.load(), ring.load(), sp.load()
        r, th = radii[i], thick[i]
        k = 0.78
        for y in range(h):
            for x in range(w):
                dx, dy = x + .5 - cx, (y + .5 - cy) / k
                d = math.hypot(dx, dy)
                e = r - d
                ang = math.degrees(math.atan2(dy, dx))
                if i >= 5 and vnoise(ang / 12 + i * 1.3, 91) < 0.25 + (i - 5) * 0.2:
                    continue
                if -1.5 <= e < 0:
                    _fxput(rp, w, h, x, y, "G3" if i < 6 else "Y0")
                elif 0 <= e <= th:
                    f = e / th
                    c = "Y2" if f < 0.15 else "L" if f < 0.45 else "Y3" if f < 0.7 else "Y2" if f < 0.9 else "Y1"
                    if i >= 6:
                        c = {"L": "Y3", "Y3": "Y2", "Y2": "Y1", "Y1": "Y0"}[c]
                    _fxput(rp, w, h, x, y, c)
                elif th < e < th + 14 and i < 6:
                    a = int((110 if i < 2 else 70) * (1 - (e - th) / 14))
                    _fxput(gp, w, h, x, y, "Y2", a)
        if i <= 1:  # blinding core
            for q in mask_disc((cx, cy), (16, 9)[i], (13, 7)[i]):
                d = math.hypot((q[0] + .5 - cx) / (16, 9)[i], (q[1] + .5 - cy) / (13, 7)[i])
                _fxput(rp, w, h, q[0], q[1], "L" if d < 0.6 else "Y3" if d < 0.85 else "Y2")
        # rays
        if i < 6:
            for n in range(16):
                a = n * 22.5 + i * 3
                ln = r * (1.25 if n % 2 == 0 else 1.08) + 6
                for s_ in range(int(r * 0.55), int(ln)):
                    x = cx + math.cos(math.radians(a)) * s_
                    y = cy + math.sin(math.radians(a)) * s_ * k
                    _fxput(spp, w, h, x, y, "Y3" if s_ < ln - 4 else "Y1")
        # shards / petals flung outward
        for n in range(22):
            a = hash01(n, 1, 7) * 360
            d = r + 4 + hash01(n, 2, 8) * 14 + i * 2
            x = cx + math.cos(math.radians(a)) * d
            y = cy + math.sin(math.radians(a)) * d * k
            if i >= 2:
                c = "Y3" if i < 5 else "Y1" if n % 2 else "W5"
                _fxput(spp, w, h, x, y, c)
                _fxput(spp, w, h, x + math.cos(math.radians(a)), y + math.sin(math.radians(a)), "Y1" if i < 6 else "Y0")
        frames.append({"ms": (50, 60, 70, 80, 80, 90, 100, 110)[i], "cels": {"Glow": glow, "Ring": ring, "Sparks": sp}})
    return frames


def fx_pillar_frames():
    """24x120, 8 frames, pivot bottom: thin warning line -> pillar of light -> fade."""
    w, h = 24, 120
    cx = 12
    frames = []
    widths = (0, 0, 5, 10, 11, 8, 4, 0)
    for i in range(8):
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gp, cp = glow.load(), core.load()
        if i <= 1:
            for y in range(h):
                if i == 0 and (y // 3) % 3 == 2:
                    continue
                _fxput(cp, w, h, cx, y, "Y1" if i == 0 else "Y2")
                if i == 1 and (y + 2) % 6 < 2:
                    _fxput(cp, w, h, cx - 1, y, "Y0")
            for dx in range(-6 - i * 2, 7 + i * 2):
                _fxput(cp, w, h, cx + dx, h - 1, "Y2" if abs(dx) < 3 else "Y1" if abs(dx) < 6 else "G3")
                if abs(dx) < 3 + i:
                    _fxput(cp, w, h, cx + dx, h - 2, "Y1")
            for k in range(3 + i * 4):
                _fxput(cp, w, h, cx + (hash01(k, i, 3) - 0.5) * 10, h - 3 - hash01(k, i, 4) * (10 + i * 12), "Y2")
        wd = widths[i]
        if wd:
            for y in range(h):
                wv = wd / 2 + (math.sin(y * 0.35 + i * 2) * 0.8 if i >= 3 else 0)
                if i == 2:
                    wv *= min(1.0, (y + 10) / 60 + 0.2)
                for x in range(w):
                    d = abs(x + .5 - cx)
                    if d <= wv:
                        f = d / max(0.5, wv)
                        c = "L" if f < 0.4 else "Y3" if f < 0.65 else "Y2" if f < 0.85 else "Y1"
                        if i == 6 and (y + x) % 3 == 0:
                            continue
                        _fxput(cp, w, h, x, y, c)
                    elif d <= wv + 1.2:
                        _fxput(cp, w, h, x, y, "G3" if i < 6 else "Y0")
                    elif d <= wv + 4 and i < 6:
                        _fxput(gp, w, h, x, y, "Y2", int(110 * (1 - (d - wv - 1.2) / 2.8)))
            # ground burst
            for dx in range(-11, 12):
                if abs(dx) <= wd / 2 + 5:
                    _fxput(cp, w, h, cx + dx, h - 1, "L" if abs(dx) < wd / 2 else "Y2")
                    if abs(dx) < wd / 2 + 2:
                        _fxput(cp, w, h, cx + dx, h - 2, "Y3")
        if i >= 5:
            for k in range(14):
                y = h - 5 - hash01(k, i, 9) * 100
                x = cx + (hash01(k, i, 10) - 0.5) * 12
                _fxput(cp, w, h, x, y - (i - 5) * 8, "Y2" if k % 2 else "W5")
        frames.append({"ms": (110, 110, 50, 70, 90, 80, 80, 90)[i], "cels": {"Glow": glow, "Core": core}})
    return frames


def fx_lance_frames():
    """64x16, 4 frames loop, travelling right: spear of light with a gold edge + trailing motes."""
    w, h = 64, 16
    y0 = 8
    frames = []
    for i in range(4):
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gp, cp = glow.load(), core.load()
        x0, x1 = 12, 50
        for x in range(x0, x1 + 1):
            t = (x - x0) / (x1 - x0)
            shimmer = ((x - i * 4) // 3) % 4 == 0
            _fxput(cp, w, h, x, y0, "L")
            _fxput(cp, w, h, x, y0 - 1, "Y3" if shimmer else "Y2")
            _fxput(cp, w, h, x, y0 + 1, "Y2" if t > 0.3 else "Y1")
            _fxput(cp, w, h, x, y0 - 2, "G3" if t > 0.15 else "Y0")
            _fxput(cp, w, h, x, y0 + 2, "G3" if t > 0.15 else "Y0")
            if t > 0.1:
                _fxput(gp, w, h, x, y0 - 3, "Y2", 90)
                _fxput(gp, w, h, x, y0 + 3, "Y2", 90)
        # leaf head
        for s in range(13):
            wv = 4.0 * min(1.0, (s + 1) / 4.0) * max(0.0, 1 - s / 13.0) ** 0.85
            for dy in range(-5, 6):
                ad = abs(dy)
                if ad <= wv:
                    c = "L" if ad < wv - 1.5 else "Y3" if ad < wv - 0.5 else "Y2"
                    _fxput(cp, w, h, x1 + s, y0 + dy, c)
                elif ad <= wv + 1:
                    _fxput(cp, w, h, x1 + s, y0 + dy, "G3")
        # root-guard flare at the base of the head
        for dy in (-4, -3, 3, 4):
            _fxput(cp, w, h, x1 - 1 - (abs(dy) - 3), y0 + dy, "Y1")
            _fxput(cp, w, h, x1 - 2 - (abs(dy) - 3), y0 + dy, "G3")
        # trailing motes and streaks
        for k in range(9):
            age = (hash01(k, 1, 3) + i * 0.25) % 1.0
            x = x0 - 1 - age * 12
            y = y0 + (hash01(k, 2, 4) - 0.5) * 8
            _fxput(cp, w, h, x, y, "Y3" if age < 0.3 else "Y2" if age < 0.6 else "Y1")
        for k, dy in enumerate((-1, 0, 1)):
            for x in range(1, x0):
                if (x + i * 3 + k * 4) % 7 < 3:
                    _fxput(cp, w, h, x, y0 + dy, "Y2" if dy == 0 else "Y1")
        frames.append({"ms": 70, "cels": {"Glow": glow, "Core": core}})
    return frames


# =========================================================================== main
def main():
    import sovereign_moves   # new phase 1-2 moves (lash, combo, petals, grab, orbs, beam, spears, blink, rings, crown)
    sovereign_moves.install(sys.modules[__name__])
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    frames, frames_p2, flats, flats_p2, tags, infos, rows, rows2 = [], [], [], [], [], {}, [], []
    for name, fn in TAGDEFS:
        if only and name not in only:
            continue
        fr = fn()
        assert len(fr) == COUNTS[name], (name, len(fr))
        sec = secondary(fr, loop=name in LOOPS)
        a = len(frames)
        infos[name] = []
        r1, r2 = [], []
        for k, (ms, p) in enumerate(fr):
            prev = (fr[k - 1][1], sec[k - 1]) if k > 0 else ((fr[-1][1], sec[-1]) if name in LOOPS else None)
            fi = a + k if name not in LOOPS else k
            outs = []
            for phase in (1, 2):
                L, FX, info = render(p, fi, sec[k], phase, prev)
                imgs = compose(L, FX, info, p, phase)
                if phase == 2:
                    kk = max(0.0, 1.0 - p["dissolve"] * 2.0)
                    imgs["Fire"] = p2_fire(info, fi, kk)
                    imgs["Embers"] = p2_embers(info, fi, kk)
                dissolve(imgs, p["dissolve"], fi, info)
                if p.get("shake"):
                    imgs = shift_imgs(imgs, p["shake"])
                outs.append((imgs, info))
            (imgs, info), (imgs2, info2) = outs
            frames.append({"ms": ms, "cels": imgs})
            frames_p2.append({"ms": ms, "cels": imgs2})
            f1, f2 = flatten(imgs, BASE_LAYERS), flatten(imgs2, P2_ORDER)
            flats.append(f1); flats_p2.append(f2)
            r1.append(f1); r2.append(f2)
            infos[name].append(info)
        tags.append((name, a, len(frames) - 1))
        rows.append((name, r1)); rows2.append((name, r2))
        print("rendered", name, len(fr), flush=True)
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    suffix = "" if not only else "_wip"
    preview_rows(rows, os.path.join(pv, f"sovereign{suffix}.png"))
    preview_rows(rows2, os.path.join(pv, f"sovereign_p2{suffix}.png"))
    # closeup: phase 1 / phase 2 first frame at 4x
    c = Image.new("RGBA", (W * 2, H), (92, 92, 98, 255))
    c.alpha_composite(flats[0]); c.alpha_composite(flats_p2[0], (W, 0))
    c.resize((W * 2 * 4, H * 4), Image.NEAREST).save(os.path.join(pv, f"sovereign_closeup{suffix}.png"))
    # readability: pale sky vs dark cavern
    bgc = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 255))
    sky = Image.new("RGBA", (W, H))
    skp = sky.load()
    for y in range(H):
        t = y / H
        cc = (int(214 + 30 * t), int(226 + 20 * t), int(240 + 10 * t), 255)
        for x in range(W):
            skp[x, y] = cc
    dark = Image.new("RGBA", (W, H), (18, 16, 24, 255))
    pick = [flats[0], flats[tags[0][1] + 4] if not only else flats[-1]]
    for ci, im in enumerate((flats[0], flats_p2[0])):
        for ri, bgi in enumerate((sky, dark)):
            t_ = bgi.copy(); t_.alpha_composite(im)
            bgc.paste(t_, (ci * W, ri * H))
    bgc.resize((W * 2 * 3, H * 2 * 3), Image.NEAREST).save(os.path.join(pv, f"sovereign_bg{suffix}.png"))
    wip = os.environ.get("SOV_WIP_DIR")
    if wip:
        for (tag, ims), (_, ims2) in zip(rows, rows2):
            for nm, lst in ((tag, ims), (tag + "_p2", ims2)):
                n = len(lst)
                cols = min(n, 7)
                rr = (n + cols - 1) // cols
                sh = Image.new("RGBA", (cols * (W + 2) * 2, rr * (H + 2) * 2), (40, 40, 46, 255))
                for i, im in enumerate(lst):
                    fr_ = Image.new("RGBA", (W, H), (92, 92, 98, 255)); fr_.alpha_composite(im)
                    sh.alpha_composite(fr_.resize((W * 2, H * 2), Image.NEAREST),
                                       ((i % cols) * (W + 2) * 2, (i // cols) * (H + 2) * 2))
                sh.save(os.path.join(wip, f"{nm}.png"))
    if only:
        return

    # ---------------- meta
    start = {t: a for t, a, _ in tags}

    def pt(q):
        return [int(round(q[0])), int(round(q[1]))]

    def reach_floor(r):
        x, y, w_, h_ = r
        if y + h_ < FLOOR + 1:
            h_ = FLOOR + 1 - y
        return [x, y, w_, h_]

    def sweep_rect(k, side):
        inf = infos["sweep"][k]
        cx = inf["j"]["Wr"][0]
        pts = {q for q in (inf["smear"] | inf["wing_px"]) if q[1] > 96 and
               ((q[0] > cx + 6) if side > 0 else (q[0] < cx - 6) if side < 0 else True)}
        return reach_floor(bbox(pts, 1))

    rects = {}
    w1 = {}
    for k in (3, 4):
        w1[str(k)] = sweep_rect(k, 1)
    w2 = {}
    for k in (7, 8):
        w2[str(k)] = sweep_rect(k, 0)
    rects.update(w1); rects.update(w2)
    nova_rects = {}
    for k in (8, 9, 10):
        inf = infos["nova"][k]
        nova_rects[str(k)] = bbox(inf["nova_px"], 0)
    idle0 = infos["idle"][0]
    body_pts = {q for q in idle0["robe_px"] if q[1] < 142}
    hb = bbox(body_pts | idle0["face_px"], 0)
    hurt = [hb[0] + 8, hb[1] - 2, hb[2] - 16, hb[3] + 2]
    head_box = bbox(idle0["face_px"], 1)
    rain6 = infos["rain"][6]
    lance6 = infos["lance"][6]
    sum5 = infos["summon"][5]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, AY],
        "floating": True,
        "floor_y": FLOOR + 1,
        "hurtbox": hurt,
        "hurtbox_head": head_box,
        "attacks": {
            "sweep": {
                "active": [3, 8],
                "hit": union_rect(list(rects.values())),
                "windows": [{"active": [3, 4], "hit": union_rect(list(w1.values())), "side": "front"},
                            {"active": [7, 8], "hit": union_rect(list(w2.values())), "side": "both"}],
                "rects": rects,
            },
            "nova": {"active": [8, 10], "hit": union_rect(list(nova_rects.values())), "rects": nova_rects,
                     "center": pt(infos["nova"][9]["nova_c"])},
        },
        "telegraph": {
            "sweep": {"frame": 2, "at": pt(next(q for q in reversed(infos["sweep"][2]["geos"]["wr"][1]["pts"])
                                                if 6 <= q[1] and 6 <= q[0] <= W - 6))},
            "rain": {"frame": 4, "at": pt(infos["rain"][4]["hand_n"])},
            "lance": {"frame": 5, "at": pt((infos["lance"][5]["spear"][1] + 8, infos["lance"][5]["spear"][2]))},
            "nova": {"frame": 6, "at": pt(infos["nova"][6]["heart"])},
            "summon": {"frame": 3, "at": pt(infos["summon"][3]["hand_n"])},
        },
        "spawn": {
            "rain": {"frame": 6, "at": pt(rain6["hand_n"])},
            "lance": {"frame": 6, "at": pt(lance6["hand_n"]), "dir": [1, 0]},
            "summon": {"frame": 5, "at": [AX, FLOOR],
                       "points": [[AX + dx, FLOOR] for dx in (-60, -30, 30, 60)]},
            "nova": {"frame": 8, "at": pt(infos["nova"][8]["nova_c"])},
        },
        "notes": "faces right; floating: anchor [96,150] is the hem line, rows 151-159 hold only light/roots/FX "
                 "(floor_y = frame bottom if the engine hovers her 10px). 'hit' = union of per-frame 'rects' over "
                 "the inclusive active range; sweep has two windows (engine: attacks.sweep.windows) -- window 0 the "
                 "near wing slams low in front, window 1 the back wing sweeps low under/behind her while the front "
                 "wing stays down (both sides). nova: in-sprite ring active 8-10; spawn fx_sov_nova at spawn.nova. "
                 "rain: spawn fx_lightpillar columns (engine positions) at frame 6; lance: fx_sov_lance from "
                 "spawn.lance.at travelling right at frame 6; summon: fx_root_spike (or fx_lightpillar) at frame 5; "
                 "telegraph 'at' = glint point the frame before the strike.",
    }
    # ---------------- new moves (sovereign_moves.py)
    def ub(pts, pad=1):
        return reach_floor(bbox(pts, pad)) if pts else [0, 0, 1, 1]

    def win(tag, a, b, pick, floor=False):
        rs = {}
        for k in range(a, b + 1):
            pts = pick(infos[tag][k])
            if pts:
                rs[str(k)] = reach_floor(bbox(pts, 1)) if floor else bbox(pts, 1)
        return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}

    blade = lambda inf: set(inf.get("blade_px", ())) | {q for q in inf["smear"]}
    wc = [win("combo", 3, 4, blade, True), win("combo", 6, 7, blade, True), win("combo", 11, 12, blade, True)]
    meta["attacks"]["combo"] = {"active": [3, 12], "hit": union_rect([w_["hit"] for w_ in wc]),
                                "windows": [{"active": w_["active"], "hit": w_["hit"]} for w_ in wc],
                                "rects": {k: v for w_ in wc for k, v in w_["rects"].items()}}
    front = lambda inf: {q for q in (inf["smear"] | inf["wing_px"]) if q[0] > inf["j"]["Wr"][0] + 4 and q[1] > 44}
    cw = win("cross", 4, 6, front, floor=True)
    meta["attacks"]["cross"] = {"active": [4, 6], "hit": cw["hit"], "rects": cw["rects"]}
    gw = lambda inf: {q for q in (inf["smear"] | inf["wing_px"]) if q[0] > inf["j"]["Wr"][0] + 24 and q[1] > 100}
    gr = win("grab", 3, 5, gw, floor=True)
    hr_ = gr["hit"]
    meta["grab"] = {"active": [3, 5], "hit": hr_, "rects": gr["rects"], "hold": [hr_[0] + hr_[2] // 2, FLOOR + 1]}
    I = lambda tag, k, key: pt(infos[tag][k][key])
    meta["telegraph"].update({
        "lash": {"frame": 2, "at": I("lash", 2, "hand_n")},
        "combo": {"frame": 2, "at": [pt(infos["combo"][2]["blade"][1])[0], max(4, pt(infos["combo"][2]["blade"][1])[1])]},
        "petals": {"frame": 2, "at": I("petals", 2, "heart")},
        "grab": {"frame": 2, "at": pt(max(infos["grab"][2]["geos"]["wr"][1]["pts"], key=lambda q: -q[1]))},
        "grabhold": {"frame": 3, "at": I("grabhold", 3, "hand_n")},
        "orbs": {"frame": 4, "at": I("orbs", 4, "hand_n")},
        "beam": {"frame": 4, "at": I("beam", 4, "hand_n")},
        "spears": {"frame": 3, "at": I("spears", 3, "hand_n")},
        "cross": {"frame": 3, "at": I("cross", 3, "heart")},
        "rings": {"frame": 5, "at": I("rings", 5, "heart")},
        "crown": {"frame": 4, "at": pt(add(infos["crown"][4]["j"]["Hc"], (0, -17)))},
    })
    meta["spawn"].update({
        "lash": {"frame": 4, "at": [AX + 30, FLOOR]},
        "orbs": {"frame": 6, "at": I("orbs", 6, "hand_n"), "halo": [pt(q) for q in infos["orbs"][4]["halo_orbs"]]},
        "petals": {"frame": 4, "at": I("petals", 4, "heart"), "second": 8},
        "spears": {"frame": 5, "at": [AX, FLOOR]},
        "rings": {"frame": 6, "at": [AX, FLOOR], "second": 10},
        "grabhold": {"frame": 4, "at": I("grabhold", 4, "hand_n")},
    })
    meta["frames"] = {
        "beam": [{"hand": pt(infos["beam"][k]["hand_n"]), "ang": sovereign_moves.BEAM_ANG[k]} for k in range(16)],
        "crown": [{"halo": pt(infos["crown"][k]["j"]["Hc"])} for k in range(14)],
    }
    # sheet split: <= 21 frames (4032 px) per strip; idle/glide/stagger stay together in the first sheet
    cnt = {t: b - a + 1 for t, a, b in tags}
    groups = [["idle", "glide", "stagger"]]
    rest = sorted([t for t in cnt if t not in groups[0]], key=lambda t: -cnt[t])
    bins = []
    for t in rest:
        for b_ in bins:
            if sum(cnt[x] for x in b_) + cnt[t] <= 21:
                b_.append(t)
                break
        else:
            bins.append([t])
    groups += bins
    names1 = ["sovereign"] + [f"sovereign_{i + 2}" for i in range(len(groups) - 1)]
    names2 = ["sovereign_p2"] + [f"sovereign_p2_{i + 2}" for i in range(len(groups) - 1)]
    meta["sheets"] = {"p1": {t: names1[gi] for gi, g in enumerate(groups) for t in g},
                      "p2": {t: names2[gi] for gi, g in enumerate(groups) for t in g}}
    hit_preview(flats, tags, meta, os.path.join(pv, "sovereign_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "sovereign_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k not in ("attacks", "notes")}))
    for t, d in meta["attacks"].items():
        print("attack", t, d["active"], d["hit"], [w_["hit"] for w_ in d.get("windows", [])])

    # ---------------- fx sheets
    nv, lp, ln = fx_nova_frames(), fx_pillar_frames(), fx_lance_frames()
    nvl = [flatten(f["cels"], ["Glow", "Ring", "Sparks"], 160, 120) for f in nv]
    lpl = [flatten(f["cels"], ["Glow", "Core"], 24, 120) for f in lp]
    lnl = [flatten(f["cels"], ["Glow", "Core"], 64, 16) for f in ln]
    s = 3
    sheet = Image.new("RGBA", (8 * 162 * s, (122 * 3 + 20) * s), (40, 40, 46, 255))
    for bi, bgc_ in enumerate(((92, 92, 98, 255), (225, 235, 246, 255))):
        for i, im in enumerate(nvl):
            fr = Image.new("RGBA", (160, 120), bgc_); fr.alpha_composite(im)
            sheet.alpha_composite(fr.resize((160 * s, 120 * s), Image.NEAREST), (i * 162 * s, bi * 122 * s))
    for bi, bgc_ in enumerate(((92, 92, 98, 255), (225, 235, 246, 255))):
        for i, im in enumerate(lpl):
            fr = Image.new("RGBA", (24, 120), bgc_); fr.alpha_composite(im)
            sheet.alpha_composite(fr.resize((24 * s, 120 * s), Image.NEAREST), ((i + bi * 8) * 26 * s, 244 * s))
        for i, im in enumerate(lnl):
            fr = Image.new("RGBA", (64, 16), bgc_); fr.alpha_composite(im)
            sheet.alpha_composite(fr.resize((64 * s, 16 * s), Image.NEAREST),
                                  ((16 * 26 + 4 + i * 66) * s, (244 + bi * 20) * s))
    sheet.save(os.path.join(pv, "fx_sovereign.png"))

    if "--preview" not in sys.argv:
        rng = {t: (a, b) for t, a, b in tags}
        for gi, grp in enumerate(groups):
            fr1, fr2, tg = [], [], []
            for t in grp:
                a, b = rng[t]
                tg.append((t, len(fr1), len(fr1) + b - a))
                fr1 += frames[a:b + 1]
                fr2 += frames_p2[a:b + 1]
            asebuild.build(names1[gi], W, H, BASE_LAYERS, fr1, tg)
            asebuild.build(names2[gi], W, H, P2_ORDER, fr2, tg)
            print("sheet", names1[gi], names2[gi], grp, len(fr1), flush=True)
        asebuild.build("fx_sov_nova", 160, 120, ["Glow", "Ring", "Sparks"], nv, [("sov_nova", 0, 7)])
        asebuild.build("fx_lightpillar", 24, 120, ["Glow", "Core"], lp, [("lightpillar", 0, 7)])
        asebuild.build("fx_sov_lance", 64, 16, ["Glow", "Core"], ln, [("sov_lance", 0, 3)])


if __name__ == "__main__":
    main()
