#!/usr/bin/env python3
"""Boss v2 generator -- "Morvain, the Ashen Omen" (colossal armoured demigod-knight).

    python3 art/gen_boss.py              full build: boss + boss_p2 (+ meta, previews)
    python3 art/gen_boss.py --preview    previews only (no Aseprite)
    python3 art/gen_boss.py --only idle,combo --preview   quick iteration on some tags

Outputs
    art/boss.aseprite, assets/boss.png, assets/boss.json
    art/boss_p2.aseprite, assets/boss_p2.png, assets/boss_p2.json   (same frames + phase-2 layers)
    assets/boss_meta.json
    art/previews/boss_preview.png, boss_p2_preview.png (3x), boss_closeup.png (6x idle)

The expanded move set (feint rising sweep grab impale dash drag / plunge throw counter ward flurry invoke) is
keyed on this same rig in art/omen_moves.py (sheets omen_a / omen_b); the phase-2 arena, the colossal echoes and
Morvain's projectile fx are in art/omen_bg.py.  Re-run those after changing the rig here.

Method: every body part is a shape with a per-pixel surface normal (analytic cylinders / domes,
bevelled faceted plates, folded cloth).  A material ramp (hue-shifted, 5-6 steps) is picked from the
lit normal; hand-placed decals (filigree, seams, rivets, runes) go on top; contact-shadow AO between
overlapping parts; sel-out outline; rim light from the glowing blade.  Poses are hand-keyed joints.
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

W, H = 176, 128
GROUND = 127
AX = 100  # body centre line (anchor x)

# =========================================================================== palette
HEX = {
    "OUT": "#0b080c",
    # blackened steel (cool violet shadows -> warm grey highlights)
    "S0": "#120e17", "S1": "#241c25", "S2": "#3a2e34", "S3": "#564641", "S4": "#836e5f", "S5": "#c8b39b",
    # tarnished gold
    "G0": "#2b1a0e", "G1": "#4f3314", "G2": "#7d5519", "G3": "#b2822a", "G4": "#dfb24a", "G5": "#fbe7a0",
    # crimson cloth (purple shadow -> orange-red highlight)
    "C0": "#1a0712", "C1": "#320d1c", "C2": "#541424", "C3": "#7c1f2a", "C4": "#a1342f", "C5": "#c45a3a",
    # ash fur / skin
    "F0": "#1f1b20", "F1": "#37302f", "F2": "#574c46", "F3": "#817363", "F4": "#b3a38a",
    # molten gold glow
    "Y0": "#ff8a1f", "Y1": "#ffc14a", "Y2": "#ffe890", "Y3": "#fffbe8",
    # phase-2 embers
    "R0": "#b8300e", "R1": "#e8541a",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {
    "S": ["S0", "S1", "S2", "S3", "S4", "S5"],
    "G": ["G0", "G1", "G2", "G3", "G4", "G5"],
    "C": ["C0", "C1", "C2", "C3", "C4", "C5"],
    "F": ["F0", "F1", "F2", "F3", "F4"],
}
SHINY = {"S": 0.955, "G": 0.9}          # specular threshold (R.z)
LIGHT = (-0.55, -0.68, 0.48)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)

BASE_LAYERS = ["FXBack", "Cape", "WeaponBack", "BackArm", "Legs", "Body", "Head", "Weapon",
               "FrontArm", "Glow", "FX"]
P2_LAYERS = ["Halo", "Cracks", "BladeFire", "Embers"]
P2_ORDER = ["Halo", "FXBack", "Cape", "WeaponBack", "BackArm", "Legs", "Body", "Head", "Weapon",
            "BladeFire", "FrontArm", "Cracks", "Glow", "Embers", "FX"]
SHADED = {"Cape", "WeaponBack", "BackArm", "Legs", "Body", "Head", "Weapon", "FrontArm"}


# =========================================================================== geometry helpers
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


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


# ---------------------------------------------------------------- normal-field generators
def n_capsule(a, b, r0, r1=None, flat=1.0):
    """Cylinder normals around segment a-b (radius r0->r1)."""
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
                k = 1.0 / r
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
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.08, 1 - min(0.92, ex * ex + ey * ey) * flat * flat)))
    return out


def dist_field(mask):
    """Chamfer distance (in px) to the outside of mask."""
    INF = 1e9
    d = {p: INF for p in mask}
    frontier = []
    for (x, y) in mask:
        if any((x + a, y + b) not in mask for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            d[(x, y)] = 1.0
            frontier.append((x, y))
    # simple Dijkstra-ish relaxation with 8-neighbourhood
    import heapq
    heap = [(1.0, p) for p in frontier]
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
    """Bevelled plate: flat interior with the given tilt, rounded rim.  fold(x,y)->(dx,dy) adds ripples."""
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


def mask_capsule(a, b, r0, r1=None):
    return set(n_capsule(a, b, r0, r1))


def tapered(pts, r0, r1):
    m = set()
    n = len(pts) - 1
    for i, p in enumerate(pts):
        m |= mask_disc(p, max(0.55, r0 + (r1 - r0) * i / n))
    return m


# =========================================================================== layer buffer
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}      # (x,y) -> [mat, n, bias, fixed, part]
        self.part_n = 0

    # -- painting ----------------------------------------------------------
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
        """Flat fixed colour (still part of the silhouette)."""
        self.part_n += 1
        for p in mask:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color, self.part_n]

    def decal(self, pts, color, only_on=None):
        """Recolour existing pixels. color: palette key, or (mat, level)."""
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

    def has(self, p):
        return p in self.px


def level_of(e, x, y):
    mat, n, bias, fixed = e[0], e[1], e[2], e[3]
    ramp = RAMP[mat]
    top = len(ramp) - 1
    if isinstance(fixed, tuple):
        return max(0, min(top, fixed[1] + (bias if bias < 0 else 0)))
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = 0.18 + 0.82 * max(0.0, ndl)  # 0.18 .. 1
    f = v * (top - (1 if mat in SHINY else 0)) + 0.25
    i = int(f)
    if mat in ("C", "F"):  # sparing ordered dither only right on band borders of cloth / fur
        fr = f - i
        if mat == "F" and 0.44 < fr < 0.56 and (x + y) % 2 == 0:
            i += 1
    i += bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        if rz > SHINY[mat] and bias >= 0:
            i = top
        else:
            i = min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, glow_pts=(), outline=True, rim=True):
    """Resolve a shaded layer to an RGBA image with sel-out outline and weapon rim light."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    col = {}
    lvl = {}
    for (x, y), e in layer.px.items():
        if e[0] is None:
            col[(x, y)] = e[3]
            continue
        if isinstance(e[3], str):
            col[(x, y)] = e[3]
            continue
        i = level_of(e, x, y)
        lvl[(x, y)] = i
        col[(x, y)] = RAMP[e[0]][i]
    # rim light from glowing blade
    if rim and glow_pts:
        gp = glow_pts[::3]
        for (x, y), e in layer.px.items():
            if e[0] not in ("S", "F", "C") or e[3] is not None:
                continue
            n = e[1]
            nl = math.hypot(n[0], n[1])
            if nl < 0.35:
                continue
            best = None
            for (gx, gy) in gp:
                dx, dy = gx - x, gy - y
                d = abs(dx) + abs(dy)
                if d < 26 and (best is None or d < best[0]):
                    best = (d, dx, dy)
            if not best:
                continue
            d, dx, dy = best
            dl = math.hypot(dx, dy) or 1
            face = (n[0] * dx + n[1] * dy) / (nl * dl)
            if face > 0.55:
                sx = 1 if dx > 0.4 * dl else -1 if dx < -0.4 * dl else 0
                sy = 1 if dy > 0.4 * dl else -1 if dy < -0.4 * dl else 0
                if (x + sx, y + sy) not in layer.px:
                    if e[0] == "S":
                        col[(x, y)] = "G4" if d < 12 else "G3"
                    elif e[0] == "F":
                        col[(x, y)] = "G3" if d < 12 else "F4"
                    else:
                        col[(x, y)] = "C5" if d < 14 else "C4"
    if outline:
        for (x, y) in layer.px:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if not inb(*q) or q in layer.px:
                    continue
                e = layer.px[(x, y)]
                c = "OUT"
                # sel-out: lit upper/left rims get a coloured dark outline instead of black
                if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 3:
                    c = RAMP[e[0]][1]
                cur = pix[q]
                if cur[3] == 0 or c == "OUT":
                    pix[q] = RGBA[c]
    for p, c in col.items():
        pix[p] = RGBA[c]
    return img


class FXLayer:
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


# =========================================================================== weapon
BLADE = dict(pommel=-12, grip_end=3, guard=(3, 7), end=57, curve=0.0045)


def weapon_geom(grip, ang, flip=1):
    """Analytic greatsword.  Returns dict p -> (colour, zone) and list of edge glow pixels."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    gx, gy = grip
    # light direction in blade-local frame for bevel shading
    vdir = (-sa * flip, ca * flip)  # +v axis in screen
    lit_edge = -(vdir[0] * LIGHT[0] + vdir[1] * LIGHT[1])  # >0 : edge bevel faces light
    out = {}
    edge = []
    E = BLADE["end"]
    b0 = BLADE["guard"][1] - 1
    Rr = E + 4
    for y in range(int(gy - Rr), int(gy + Rr) + 1):
        for x in range(int(gx - Rr), int(gx + Rr) + 1):
            dx, dy = x + .5 - gx, y + .5 - gy
            u = dx * ca + dy * sa
            if u < BLADE["pommel"] - 3 or u > E + 1:
                continue
            v = (-dx * sa + dy * ca) * flip
            c = None
            # grip (leather wrap)
            if BLADE["pommel"] + 2 <= u <= BLADE["grip_end"] and abs(v) <= 1.6:
                c = "C2" if (int(u * 1.0 + v * 1.4) % 3) else "C0"
                if v < -0.6:
                    c = "C3" if c == "C2" else "C1"
            # pommel
            pu = u - (BLADE["pommel"] + 0.5)
            if pu * pu / 6.0 + v * v / 7.0 <= 1.0:
                c = "G4" if v < -0.5 else "G3" if v < 0.8 else "G1"
                if abs(v) < 0.8 and abs(pu) < 0.9:
                    c = "C4"
            # guard: swept gold wings curving toward the blade
            g0, g1 = BLADE["guard"]
            if g0 - 1 <= u <= g1:
                t = (u - (g0 - 1)) / (g1 - g0 + 1)
                half = 7.2 - t * 1.5
                if abs(v) <= half and (abs(v) < 2.2 or (u - (g0 - 1)) > (abs(v) - 2.2) * 0.45):
                    c = "G4" if v < -2 else "G3" if v < 1 else "G2"
                    if abs(v) > half - 1.1:
                        c = "G1" if v > 0 else "G3"
                    if abs(v) < 1.2 and g0 <= u <= g1 - 1:
                        c = "Y1"  # ember gem
            # blade
            if b0 <= u <= E:
                s = u - b0
                t = s / (E - b0)
                cc = -BLADE["curve"] * s * s
                we = 4.3 + 1.5 * math.sin(min(t, 1.0) * math.pi * 0.85)
                wb = 2.4 + 0.7 * math.sin(min(t, 1.0) * math.pi * 0.85)
                if t > 0.78:
                    k = (1 - t) / 0.22
                    we *= k ** 0.7
                    wb *= k ** 1.3
                lo, hi = cc - wb, cc + we
                if lo <= v <= hi:
                    de, ds = hi - v, v - lo
                    if de < 1.0:
                        c = "Y3"; edge.append((x, y))
                    elif de < 2.0:
                        c = "Y2"; edge.append((x, y))
                    elif de < 2.9:
                        c = "Y0" if t > 0.1 else "G4"
                    elif ds < 1.0:
                        c = "S4" if lit_edge < 0 else "S2"   # spine top line
                    elif abs(v - (cc + 0.3)) < 0.75 and 0.06 < t < 0.72:
                        c = "S0"  # fuller
                        # runes: short glyph strokes inside the fuller
                        k = int(s) % 6
                        if k in (1, 2, 3) and hash01(int(s) // 6, 0, 5) > 0.2:
                            c = "Y1" if k == 2 else "Y0"
                    elif v > cc + 0.3:
                        c = "S4" if lit_edge > 0.15 else "S3"  # edge bevel
                    else:
                        c = "S3" if lit_edge < -0.15 else "S2"  # spine bevel
            if c:
                out[(x, y)] = c
    return out, edge


def weapon_point(grip, ang, u, v=0.0, flip=1):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    s = max(0.0, u - (BLADE["guard"][1] - 1))
    if u > BLADE["guard"][1] - 1:
        v = v - BLADE["curve"] * s * s
    return (grip[0] + ca * u - sa * v * flip, grip[1] + sa * u + ca * v * flip)


# =========================================================================== character parts
def draw_cape(L, j, t_sw, frame_i, p2fx):
    """Massive tattered crimson cape behind the body."""
    Ns, Fs, C, P = j["Ns"], j["Fs"], j["C"], j["P"]
    sw = t_sw  # secondary motion (+ = trailing to the right)
    fl = j.get("cape_flare", 0)
    top = min(Ns[1], Fs[1]) - 4
    bot = min(GROUND - 3 + fl * 0.3, GROUND - 1)
    pts = [(Ns[0] + 2, top + 2), (Fs[0] + 4, top - 1), (Fs[0] + 12 + sw * 0.25, top + 12),
           (Fs[0] + 20 + sw * 0.6 + fl * 0.5, top + 40), (Fs[0] + 28 + sw + fl, bot),
           (P[0] - 12 + sw * 0.2, bot + 1), (Ns[0] - 4 + sw * 0.1, P[1] + 10), (Ns[0] - 2, top + 20)]
    m = poly_mask(pts)
    # frayed hem: tattered teeth, varied per frame for flutter
    xa, xb = int(P[0] - 12 + sw * 0.2), int(Fs[0] + 28 + sw + fl)
    x = xa
    k = 0
    while x <= xb:
        wdt = 2 + int(hash01(k, 3, 11) * 3)
        dep = int(hash01(k, frame_i // 2, 12) * 5) + (3 if k % 4 == 1 else 0)
        for i in range(wdt):
            dd = dep - abs(i - (wdt - 1) / 2) * 1.4
            for yy in range(int(bot), int(bot + dd) + 1):
                if yy <= GROUND:
                    m.add((x + i, yy))
        # notches cut upward
        if k % 5 == 3:
            for yy in range(int(bot - 3 - hash01(k, 1, 4) * 4), int(bot) + 1):
                m.discard((x + wdt // 2, yy))
        x += wdt
        k += 1
    # torn holes
    for hx_, hy_, rr in ((0.62, 0.55, 2.2), (0.8, 0.78, 1.8), (0.45, 0.83, 1.5)):
        cx = Fs[0] + 4 + (22 + sw * 0.6) * hx_ + 4
        cy = top + (bot - top) * hy_
        hole = mask_disc((cx, cy), rr * 1.3, rr)
        hole |= {(int(cx + rr), int(cy + rr + 1))}
        m -= hole
    # fold ripples: vertical folds that fan out towards the hem
    def fold(x, y):
        tt = max(0.0, (y - top) / max(1, bot - top))
        ph = (x - Fs[0] - sw * tt * 0.8) / (6.5 + tt * 3.0) * 2 * math.pi
        return (0.75 * math.sin(ph) * (0.3 + tt), 0.0)
    L["Cape"].paint(n_plate(m, bevel=3, tilt=(0.25, 0.1), strength=0.8, fold=fold), "C", bias=-1, ao=0)
    # gold trim band along the outer (right) edge + inner shadow near the body
    rim = []
    for (x, y) in m:
        if (x + 1, y) not in m and (x + 2, y) not in m and top + 6 < y < bot - 5:
            rim += [(x - 1, y), (x - 2, y)]
    L["Cape"].decal(rim, ("G", 2))
    L["Cape"].decal([p for p in rim if p[1] % 7 == 0], ("G", 4))
    return m


def draw_legs(L, j):
    Lg = L["Legs"]
    for side in ("far", "near"):
        hip = j["hip_" + side]
        ft = j["foot_" + side]
        ank = (ft[0] + 1, ft[1] - 6)
        kn = j.get("kneel_" + side) or ik(hip, ank, 20, 20, (-1, -0.15))
        bias = -1 if side == "far" else 0
        # thigh (cuisse)
        Lg.paint(n_capsule(hip, kn, 7.0, 5.6), "S", bias=bias)
        # greave
        g = n_capsule(kn, ank, 5.4, 3.9)
        Lg.paint(g, "S", bias=bias)
        # front ridge highlight on the greave + gold trim line
        d = (ank[0] - kn[0], ank[1] - kn[1]); dl = math.hypot(*d) or 1
        perp = (-d[1] / dl, d[0] / dl)
        if perp[0] > 0:
            perp = (-perp[0], -perp[1])
        a = add(kn, (perp[0] * 3.2 + d[0] / dl * 4, perp[1] * 3.2 + d[1] / dl * 4))
        b = add(ank, (perp[0] * 2.4, perp[1] * 2.4))
        Lg.decal(line(a, b), ("G", 3 + bias))
        Lg.decal(line(add(a, (-perp[0], -perp[1])), add(b, (-perp[0], -perp[1]))), ("S", 4 + bias))
        # sabaton (pointed armoured foot)
        fx, fy = ft
        sab = poly_mask([(fx - 11, fy + 0.5), (fx - 9, fy - 3), (fx - 3, fy - 6.5), (fx + 4, fy - 7.5),
                         (fx + 6, fy - 3), (fx + 6, fy + 0.5)])
        Lg.paint(n_plate(sab, bevel=2.2, tilt=(-0.1, -0.3)), "S", bias=bias)
        for k in range(3):  # lames
            Lg.decal(line((fx - 7 + k * 3.5, fy - 5 + k * 0.4), (fx - 5 + k * 3.5, fy)), ("S", 1))
        Lg.decal([(fx - 10, fy), (fx - 9, fy)], ("G", 4 + bias))
        # knee cop (poleyn) with fan wing
        Lg.paint(n_dome(add(kn, (-1, 0)), 5.2, 4.6, flat=0.9), "S", bias=bias)
        wing = poly_mask([add(kn, (1, -2)), add(kn, (8, -1)), add(kn, (6, 3)), add(kn, (1, 3))])
        Lg.paint(n_plate(wing, bevel=1.5, tilt=(0.3, -0.2)), "S", bias=bias - 1)
        Lg.paint(n_dome(add(kn, (-1, 0)), 5.2, 4.6, flat=0.9), "S", bias=bias, ao=0)
        rimk = [p for p in mask_disc(add(kn, (-1, 0)), 5.2, 4.6) if p not in mask_disc(add(kn, (-1, -0.5)), 4.0, 3.5)]
        Lg.decal([p for p in rimk if p[1] > kn[1] - 1], ("G", 3 + bias))
        Lg.decal([(int(kn[0] - 1), int(kn[1]))], ("G", 5))
        j["knee_" + side] = kn


def draw_body(L, j, sw):
    Bd = L["Body"]
    C, P, tw = j["C"], j["P"], j["tw"]
    Fs, Ns = j["Fs"], j["Ns"]
    # ---- chainmail skirt
    wl, wr = (P[0] - 12, P[1] - 6), (P[0] + 13, P[1] - 6)
    hem = P[1] + 16
    kf, kn_ = j["knee_near"], j["knee_far"]
    lx = min(kf[0] - 6, P[0] - 16)
    rx = max(kn_[0] + 6, P[0] + 17)
    mail = poly_mask([wl, wr, (P[0] + 16, P[1] + 2), (rx, hem), (lx, hem), (P[0] - 15, P[1] + 2)])
    for x in range(int(lx), int(rx) + 1):  # scalloped hem
        if x % 4 in (1, 2):
            mail.add((x, int(hem))); mail.add((x, int(hem) + 1)) if x % 4 == 1 else None
    Bd.paint(n_plate(mail, bevel=4, tilt=(0.05, 0.2), strength=1.0), "S", bias=-1)
    Bd.decal([p for p in mail if (p[0] + 2 * (p[1] % 2)) % 3 == 0 and p[1] % 2 == 0], ("S", 1))
    Bd.decal([p for p in mail if (p[0] + 2 * (p[1] % 2)) % 3 == 1 and p[1] % 2 == 1 and p[0] < P[0] + 2], ("S", 3))
    # ---- tabard (crimson ceremonial cloth between the legs)
    ts = j.get("tab_sw", 0)
    tx = P[0] - 5 + tw * 2
    tab_bot = min(GROUND - 6, P[1] + 34)
    tab = poly_mask([(tx - 6, P[1] - 5), (tx + 6, P[1] - 5), (tx + 7 + ts * 0.5, tab_bot - 3),
                     (tx + 3 + ts, tab_bot + 2), (tx - 1 + ts, tab_bot - 1), (tx - 5 + ts, tab_bot + 3),
                     (tx - 8 + ts * 0.6, tab_bot - 2)])
    tabn = n_plate(tab, bevel=2.5, tilt=(-0.15, 0.1), strength=0.9,
                   fold=lambda x, y: (0.5 * math.sin((x - tx - ts * (y - P[1]) / 34) * 0.9), 0))
    Bd.paint(tabn, "C")
    edge = [p for p in tab if (p[0] - 1, p[1]) not in tab or (p[0] + 1, p[1]) not in tab]
    Bd.decal(edge, ("G", 3))
    # emblem on the tabard: an ember eye in a crescent
    ex, ey = int(tx + ts * 0.3), int(P[1] + 12)
    emb = [(ex - 2, ey - 2), (ex - 3, ey - 1), (ex - 3, ey), (ex - 3, ey + 1), (ex - 2, ey + 2), (ex - 1, ey + 3),
           (ex + 2, ey - 2), (ex + 3, ey - 1), (ex + 3, ey + 1), (ex + 2, ey + 2), (ex + 1, ey + 3), (ex, ey + 3)]
    Bd.decal(emb, ("G", 4))
    Bd.decal([(ex, ey), (ex - 1, ey), (ex, ey + 1)], ("G", 5))
    # ---- tassets (plates hanging from the belt over the thighs)
    for side, off, bias in (("far", 9, -1), ("near", -9, 0)):
        kx = j["knee_" + side][0]
        top_c = (P[0] + off + tw * 2, P[1] - 5)
        bot_c = ((top_c[0] + kx) / 2 + (2 if side == "far" else -2), P[1] + 13)
        tas = poly_mask([(top_c[0] - 7, top_c[1]), (top_c[0] + 7, top_c[1]), (bot_c[0] + 7, bot_c[1]),
                         (bot_c[0] + 1, bot_c[1] + 2), (bot_c[0] - 6, bot_c[1])])
        Bd.paint(n_plate(tas, bevel=2, tilt=(0.15 if side == "far" else -0.2, 0.25)), "S", bias=bias)
        for yy in (top_c[1] + 6, top_c[1] + 12):  # lame seams with lit lip
            seam = [p for p in tas if p[1] == int(yy)]
            Bd.decal(seam, ("S", 0))
            Bd.decal([(x, y + 1) for (x, y) in seam if (x, y + 1) in tas], ("S", 4 + bias))
        bot = [p for p in tas if (p[0], p[1] + 1) not in tas or (p[0], p[1] + 2) not in tas]
        Bd.decal(bot, ("G", 3 + bias))
    # ---- torso: faceted breastplate (front plane toward light, side plane in shade)
    ridge_top = (C[0] - 6 - tw * 3, C[1] - 13)
    ridge_bot = (P[0] - 3 - tw * 2, P[1] - 7)
    outline = [add(Ns, (-1, -3)), (C[0] - 8, C[1] - 15), (C[0] + 6, C[1] - 16), add(Fs, (4, -3)),
               (C[0] + 21 + tw * 2, C[1] + 4), (P[0] + 14, P[1] - 7), (P[0] - 13, P[1] - 7),
               (C[0] - 20 - tw * 2, C[1] + 3)]
    torso = poly_mask(outline)
    def side_of(p):
        # left of the ridge line = front plane
        (x1, y1), (x2, y2) = ridge_top, ridge_bot
        return (x2 - x1) * (p[1] + .5 - y1) - (y2 - y1) * (p[0] + .5 - x1)
    front = {p for p in torso if side_of(p) > 0}
    side = torso - front
    # chest swell: slight dome on each plane
    Bd.paint(n_plate(front, bevel=4, tilt=(-0.62, -0.32), strength=1.1,
                     fold=lambda x, y: ((x - (C[0] - 12)) * 0.015, (y - (C[1] - 2)) * 0.02)), "S")
    Bd.paint(n_plate(side, bevel=3.5, tilt=(-0.12, -0.3), strength=1.1,
                     fold=lambda x, y: ((x - (C[0] + 2)) * 0.045, (y - (C[1] - 6)) * 0.04)), "S", ao=0)
    # specular swell on the pectoral plate
    arc = [(int(C[0] - 4 + k - tw * 2), int(C[1] - 11 + 0.05 * (k - 3) ** 2)) for k in range(18)]
    Bd.decal([q for q in arc if q in torso], ("S", 5))
    Bd.decal([(x, y + 1) for (x, y) in arc if (x, y + 1) in torso], ("S", 4))
    Bd.decal([(x, y + 3) for (x, y) in arc if (x, y + 3) in torso], ("S", 1))
    # chest emblem: gold sun-ring with an ember eye (the Omen)
    ec = (C[0] + 5 - tw * 2, C[1] - 1)
    ring = [p for p in mask_disc(ec, 4.6) if p not in mask_disc(ec, 3.3)]
    Bd.decal(ring, ("G", 3))
    Bd.decal([p for p in ring if p[1] < ec[1] - 1 or p[0] < ec[0] - 2], ("G", 4))
    for a in range(8):
        ang = a * math.pi / 4 + 0.39
        Bd.decal([(int(ec[0] + math.cos(ang) * 6), int(ec[1] + math.sin(ang) * 6))], ("G", 3))
    Bd.decal([(int(ec[0]) - 1, int(ec[1])), (int(ec[0]), int(ec[1]))], "Y1")
    Bd.decal([(int(ec[0]) - 2, int(ec[1])), (int(ec[0]) + 1, int(ec[1]))], ("G", 2))
    ridge = line(ridge_top, ridge_bot)
    Bd.decal(ridge, ("S", 5))
    Bd.decal([(x + 1, y) for (x, y) in ridge], ("S", 1))
    # abdomen lames
    for k in range(3):
        yy = int(C[1] + 9 + k * 4)
        seam = [p for p in torso if p[1] == yy]
        Bd.decal(seam, ("S", 0))
        Bd.decal([(x, y + 1) for (x, y) in seam if (x, y + 1) in torso and side_of((x, y + 1)) > 0], ("S", 4))
    # gold filigree: neckline trim, plate edge trim, scroll work on the front plane
    neck_edge = [p for p in torso if (p[0], p[1] - 1) not in torso or (p[0], p[1] - 2) not in torso]
    Bd.decal([p for p in neck_edge if p[1] < C[1] - 8], ("G", 3))
    Bd.decal([p for p in neck_edge if p[1] < C[1] - 8 and (p[0], p[1] - 1) not in torso], ("G", 4))
    fx0, fy0 = int(C[0] - 12 - tw * 2), int(C[1] - 7)
    scroll = [(0, 0), (1, -1), (2, -1), (3, 0), (3, 1), (2, 2), (1, 1), (4, 2), (5, 3), (6, 3), (7, 2), (7, 1), (6, 0),
              (-1, 1), (-2, 2), (-2, 3), (-1, 4), (0, 4), (3, 5), (4, 6), (4, 7), (3, 8)]
    Bd.decal([(fx0 + a, fy0 + b) for a, b in scroll], ("G", 3), only_on=("S",))
    Bd.decal([(fx0 + 1, fy0 - 1), (fx0 + 6, fy0 + 3)], ("G", 5), only_on=("S",))
    # rivets along the side plane edge
    for k in range(4):
        q = (int(ridge_top[0] + 4 + k * 0.6), int(ridge_top[1] + 4 + k * 5))
        Bd.decal([q], ("G", 4)); Bd.decal([(q[0] + 1, q[1] + 1)], ("S", 0))
    # ---- belt with sun buckle
    belt = [p for p in (torso | mail) if P[1] - 8 <= p[1] <= P[1] - 5]
    Bd.decal([p for p in belt if p[1] == P[1] - 8], ("G", 4))
    Bd.decal([p for p in belt if P[1] - 7 <= p[1] <= P[1] - 6], ("G", 2))
    Bd.decal([p for p in belt if p[1] == P[1] - 5], ("G", 1))
    bx, by = int(P[0] - 5 - tw * 2), int(P[1] - 7)
    buckle = mask_disc((bx + .5, by + .5), 3.2, 2.8)
    Bd.paint(n_dome((bx + .5, by + .5), 3.2, 2.8), "G", ao=0)
    Bd.decal([(bx, by)], ("G", 5)); Bd.decal([(bx, by + 1)], "Y1")
    return torso


def draw_mantle(L, j, sw):
    """Ash-fur mantle draped over both shoulders and across the back."""
    Bd = L["Body"]
    Fs, Ns, C = j["Fs"], j["Ns"], j["C"]
    ctrl = bezier(add(Ns, (1, -2)), add(C, (-8, -20)), add(C, (10, -20)), add(Fs, (0, -1)), 14)
    m = set()
    for i, p in enumerate(ctrl):
        r = 6.5 + 2.2 * math.sin(i / 14 * math.pi)
        m |= mask_disc(p, r + 1.0, r)
    # tufts hanging from the bottom edge
    cols = {}
    for (x, y) in m:
        cols[x] = max(cols.get(x, -1), y)
    for x, yb in cols.items():
        ln = int(hash01(x, 1, 21) * 4) + (2 if x % 3 == 0 else 0)
        for k in range(ln):
            m.add((x + (1 if k > 2 and sw > 0 else 0), yb + k))
    nrm = n_plate(m, bevel=5, tilt=(0.0, -0.15), strength=1.3,
                  fold=lambda x, y: (0.35 * math.sin(x * 1.3 + y * 0.4), 0.2 * math.sin(y * 1.1)))
    Bd.paint(nrm, "F")
    # strands
    for (x, y) in list(m):
        hsh = hash01(x, y, 31)
        if hsh < 0.035 and (x, y + 2) in m:
            Bd.decal([(x, y), (x + 1, y + 1), (x + 1, y + 2)], ("F", 1))
    return m


def draw_head(L, j, frame_i, head_sw):
    Hl = L["Head"]
    hx, hy = j["Hd"]
    look = j.get("look", 0)  # -1 lowered, +1 raised (roar)
    hs = head_sw
    # ---- veil tails hanging behind the helm (overlapping action)
    veil = poly_mask([(hx + 4, hy - 8), (hx + 13, hy - 6), (hx + 17 + hs * 0.3, hy + 6),
                      (hx + 22 + hs * 0.9, hy + 21), (hx + 18 + hs * 0.8, hy + 18), (hx + 17 + hs, hy + 27),
                      (hx + 13 + hs * 0.6, hy + 17), (hx + 10 + hs * 0.5, hy + 22), (hx + 7, hy + 12)])
    L["Cape"].paint(n_plate(veil, bevel=3, tilt=(0.25, 0.0), strength=1.0,
                     fold=lambda x, y: (0.6 * math.sin((x - hx - hs * (y - hy) / 30) * 0.9), 0)), "C", bias=-1)
    # ---- gorget
    gor = poly_mask([(hx - 9, hy + 8), (hx + 8, hy + 7), (hx + 11, hy + 13), (hx - 11, hy + 14)])
    Hl.paint(n_plate(gor, bevel=2, tilt=(-0.1, -0.35)), "S")
    Hl.decal([p for p in gor if (p[0], p[1] - 1) not in gor], ("G", 3))
    # ---- great-helm: faceted front + side planes
    front = poly_mask([(hx - 3, hy - 11), (hx - 8, hy - 9), (hx - 10.5, hy - 3), (hx - 11, hy + 6),
                       (hx - 8, hy + 10), (hx - 2, hy + 10.5)])
    side = poly_mask([(hx - 3, hy - 11), (hx + 4, hy - 11), (hx + 9, hy - 6), (hx + 9.5, hy + 5),
                      (hx + 7, hy + 10), (hx - 2, hy + 10.5)]) - front
    Hl.paint(n_plate(front, bevel=2.2, tilt=(-0.32, -0.12), strength=1.0), "S")
    Hl.paint(n_plate(side, bevel=2.5, tilt=(0.55, 0.0), strength=1.0), "S", ao=0)
    Hl.decal(line((hx - 3, hy - 11), (hx - 2, hy + 10)), ("S", 5))
    Hl.decal(line((hx - 2, hy - 11), (hx - 1, hy + 10)), ("S", 1))
    # visor slit + breathing holes
    vy = int(hy - 2 - look)
    slit = [(x, vy) for x in range(int(hx - 11), int(hx + 7))] + \
           [(x, vy + 1) for x in range(int(hx - 11), int(hx - 2))]
    Hl.decal(slit, "OUT")
    Hl.decal([(x, vy - 1) for x in range(int(hx - 10), int(hx + 6))], ("S", 4))
    Hl.decal([(x, vy + 2) for x in range(int(hx - 10), int(hx - 2))], ("S", 1))
    for r in range(2):
        for c in range(3):
            Hl.decal([(int(hx - 9 + c * 2 + r), int(hy + 4 + r * 2))], "OUT")
    # jaw filigree
    Hl.decal(line((hx - 10, hy + 8), (hx - 3, hy + 9)), ("G", 3))
    # ---- cowl: hood drawn over the helm's crown and rear, framing the face
    outer = poly_mask([(hx - 10, hy - 9), (hx - 4, hy - 15), (hx + 6, hy - 16), (hx + 14, hy - 10),
                       (hx + 16, hy + 2), (hx + 15, hy + 9), (hx + 8, hy + 12), (hx + 4, hy + 12)])
    face = poly_mask([(hx - 14, hy - 8), (hx - 2, hy - 10.5), (hx + 4, hy - 9), (hx + 6, hy + 2),
                      (hx + 5, hy + 15), (hx - 14, hy + 15)])
    cowl = outer - face
    Hl.paint(n_plate(cowl, bevel=3.5, tilt=(0.1, -0.2), strength=1.2,
                     fold=lambda x, y: (0.45 * math.sin((x - hx) * 0.7 + (y - hy) * 0.5), 0)), "C")
    lip = [p for p in cowl if (p[0] - 1, p[1]) in face or (p[0], p[1] + 1) in face]
    Hl.decal(lip, ("C", 4))
    # ---- crown: gold band with jagged points, then three great swept-back horns
    band = []
    for t in range(0, 21):
        q = lerp((hx - 9, hy - 10), (hx + 9, hy - 14), t / 20)
        band += [(int(q[0]), int(q[1])), (int(q[0]), int(q[1]) + 1)]
    horns = [((-5, -11), (-7, -17), (-4, -21), (1, -23), 2.3, 0),
             ((1, -12), (0, -22), (10, -27), (21, -25), 3.7, 0),
             ((7, -11), (13, -18), (20, -18), (25, -11), 3.1, -1)]
    for k in (2, 1, 0):
        r0, c1, c2, tip, rad, bias = horns[k]
        pts = bezier((hx + r0[0], hy + r0[1]), (hx + c1[0], hy + c1[1] - look),
                     (hx + c2[0], hy + c2[1] - look * 2), (hx + tip[0], hy + tip[1] - look * 3), 26)
        m = tapered(pts, rad, 0.5)
        nm = {}
        for p in m:
            best = min(pts, key=lambda q: (q[0] - p[0] - .5) ** 2 + (q[1] - p[1] - .5) ** 2)
            ox, oy = p[0] + .5 - best[0], p[1] + .5 - best[1]
            nm[p] = norm3(ox * 0.9, oy * 0.9, 0.7)
        Hl.paint(nm, "S", bias=bias)
        # ridged growth rings
        for i in (6, 10, 14):
            q = pts[i]
            Hl.decal([(int(q[0]), int(q[1])), (int(q[0]) + 1, int(q[1]))], ("S", 1 + (bias < 0)))
    Hl.paint({p: (0, -0.3, 1) for p in band}, "G", ao=1)
    Hl.decal([p for i, p in enumerate(band) if i % 2 == 0], ("G", 4))
    for k, t in enumerate((0.1, 0.42, 0.72)):
        q = lerp((hx - 9, hy - 11), (hx + 9, hy - 15), t)
        ht = (5, 7, 4)[k]
        spike = poly_mask([(q[0] - 1.8, q[1] + 1), (q[0] + 1.8, q[1] + 1), (q[0] - 0.5 + k * 0.4, q[1] - ht)])
        Hl.paint({p: norm3(-0.3, -0.4, 1) for p in spike}, "G")
        Hl.decal([(int(q[0]) - 1, int(q[1]))], ("G", 5))
    Hl.decal([(int(hx - 1), int(hy - 12))], "Y1")  # ember gem in the crown
    eyes = [(int(hx - 9), vy), (int(hx - 8), vy), (int(hx - 5), vy), (int(hx - 4), vy)]
    return eyes, vy

def draw_arm(Lr, j, side, bias):
    sh = j["Ns"] if side == "near" else j["Fs"]
    hand = j["hand_" + side]
    pref = j.get("elbow_" + side, (1, 0.3) if side == "near" else (0.3, 1))
    el = ik(sh, hand, 17, 17, pref)
    # rerebrace (upper arm), couter (elbow), vambrace, gauntlet
    Lr.paint(n_capsule(sh, el, 6.0, 5.0), "S", bias=bias)
    Lr.paint(n_capsule(el, hand, 5.0, 4.2), "S", bias=bias)
    d = (hand[0] - el[0], hand[1] - el[1]); dl = math.hypot(*d) or 1
    u = (d[0] / dl, d[1] / dl)
    for tt, lv in ((0.55, 3), (0.8, 2)):
        c = lerp(el, hand, tt)
        band = [p for p in mask_capsule(c, c, 5.2)
                if abs((p[0] + .5 - c[0]) * u[0] + (p[1] + .5 - c[1]) * u[1]) < 0.9]
        Lr.decal(band, ("G", lv + bias + 1))
    # cuff flare of the gauntlet
    cuff = mask_capsule(lerp(el, hand, 0.78), lerp(el, hand, 0.9), 5.6)
    Lr.paint(n_capsule(lerp(el, hand, 0.78), lerp(el, hand, 0.9), 5.6), "S", bias=bias)
    Lr.decal([p for p in cuff if abs((p[0] + .5 - lerp(el, hand, 0.9)[0]) * u[0] +
                                   (p[1] + .5 - lerp(el, hand, 0.9)[1]) * u[1]) < 0.8], ("G", 3 + bias))
    # couter
    Lr.paint(n_dome(el, 5.2, 5.2), "S", bias=bias)
    ring = [p for p in mask_disc(el, 5.2) if p not in mask_disc(el, 4.0)]
    Lr.decal([p for p in ring if p[1] >= el[1]], ("G", 3 + bias))
    Lr.decal([(int(el[0]), int(el[1]))], ("G", 5 + bias))
    # gauntlet fist
    Lr.paint(n_dome(add(hand, (u[0] * 1.5, u[1] * 1.5)), 4.6, 4.6), "S", bias=bias)
    for k in range(3):
        q = (int(hand[0] + u[0] * 2 + (k - 1) * -u[1] * 1.8), int(hand[1] + u[1] * 2 + (k - 1) * u[0] * 1.8))
        Lr.decal([q], ("G", 4 + bias))
    return el


def draw_pauldron_near(L, j):
    Fa = L["FrontArm"]
    Ns = j["Ns"]
    c = add(Ns, (-5, 2))
    lames = [(add(c, (-3, 7)), 9, 4.5), (add(c, (-2, 2)), 10.5, 5.5), (add(c, (0, -3)), 12, 7.5)]
    for i, (lc, rx, ry) in enumerate(lames):
        m = mask_disc(lc, rx, ry)
        m = {p for p in m if p[1] >= lc[1] - ry * (0.2 if i < 2 else 1.0)}
        Fa.paint({p: v for p, v in n_dome(lc, rx, ry, flat=0.95, tilt=(0.05, 0.1)).items() if p in m}, "S")
        rim = [p for p in m if (p[0], p[1] + 1) not in m or (p[0], p[1] + 2) not in m]
        Fa.decal(rim, ("G", 3))
        Fa.decal([p for p in rim if (p[0], p[1] + 1) not in m and p[0] % 4 == 0], ("G", 5))
    top = lames[2]
    # engraved filigree swirl on the top lame
    tc = top[0]
    sw = [(int(tc[0] + 5 * math.cos(a) * (0.4 + a / 12)), int(tc[1] + 3.2 * math.sin(a) * (0.4 + a / 12)))
          for a in [i * 0.35 for i in range(22)]]
    Fa.decal(sw, ("G", 3), only_on=("S",))
    # spikes raking up and back
    for k, (bx, by, tx, ty, w) in enumerate(((-7, -5, -9, -15, 2.2), (-2, -7, 0, -18, 2.6), (4, -6, 9, -14, 2.2))):
        base = add(tc, (bx, by))
        tip = add(tc, (tx, ty))
        pts = [(base[0] - w, base[1] + 1), (base[0] + w, base[1] + 1), tip]
        m = poly_mask(pts)
        Fa.paint(n_plate(m, bevel=1.5, tilt=(0.2, -0.1), strength=1.4), "S", bias=-1 if k == 2 else 0)
        Fa.decal(line((base[0] - w + 1, base[1]), tip), ("S", 4))
        Fa.decal([(int(base[0] - w + 1), int(base[1])), (int(base[0] + w - 1), int(base[1]))], ("G", 4))


def draw_pauldron_far(L, j):
    Ba = L["BackArm"]
    Fs = j["Fs"]
    c = add(Fs, (1, -2))
    Ba.paint(n_dome(c, 8.5, 7, flat=0.95), "S", bias=-1)
    Ba.paint(n_dome(add(c, (1, 5)), 7.5, 4, flat=0.9), "S", bias=-1)
    rim = [p for p in mask_disc(add(c, (1, 5)), 7.5, 4) if (p[0], p[1] + 1) not in mask_disc(add(c, (1, 5)), 7.5, 4)]
    Ba.decal(rim, ("G", 2))
    Ba.paint(n_plate(poly_mask([add(c, (-1, -5)), add(c, (4, -4)), add(c, (7, -12))]), bevel=1.2), "S", bias=-1)


# =========================================================================== rig / pose
NEUTRAL = dict(
    P=(100, 85), C=(98, 61), Hd=(94, 40), tw=0.0,
    foot_near=(80, 127), foot_far=(120, 127),
    grip=(80, 84), wang=148, wflip=1, wlayer="Weapon", weapon=True, twohand=True,
    hand_far=None, hand_near=None, look=0,
    cape_wind=0.0, cape_flare=0, tab_wind=0.0, eyes=1.0,
)


def P_(**kw):
    d = dict(NEUTRAL)
    d.update(kw)
    return d


def joints(p):
    j = dict(p)
    C, P, tw = p["C"], p["P"], p["tw"]
    j["Ns"] = add(C, (-14 + 2 * tw, -8 - tw * 0.5))   # near (leading, left) shoulder
    j["Fs"] = add(C, (15 + 4 * tw, -9 + tw * 0.5))    # far (rear, right) shoulder
    j["hip_near"] = add(P, (-8 + tw, 3))
    j["hip_far"] = add(P, (8 + tw, 4))
    if p["weapon"] and p["twohand"]:
        j["hand_near"] = p["grip"]
        j["hand_far"] = weapon_point(p["grip"], p["wang"], -8, 0, p["wflip"])
    else:
        j["hand_near"] = p["hand_near"] or (p["grip"] if p["weapon"] else add(C, (-18, 22)))
        j["hand_far"] = p["hand_far"] or add(C, (20, 24))
    return j


def blade_mask(grip, ang, flip=1, umin=12):
    px, _ = weapon_geom(grip, ang, flip)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = set()
    for (x, y) in px:
        u = (x + .5 - grip[0]) * ca + (y + .5 - grip[1]) * sa
        if u >= umin:
            out.add((x, y))
    return out


def render(p, frame_i, sec):
    """sec = secondary motion state dict (cape, hood, tab)."""
    j = joints(p)
    L = {n: Layer(n) for n in SHADED}
    FX = {n: FXLayer(n) for n in ("FXBack", "Glow", "FX")}
    info = {"smear": set(), "blade": set(), "edge": [], "tip": None}
    if p["weapon"]:
        wpx, edge = weapon_geom(p["grip"], p["wang"], p["wflip"])
        clip = p.get("bury")
        if clip:
            wpx = {q: c for q, c in wpx.items() if q[1] < clip}
            edge = [q for q in edge if q[1] < clip]
        wl = L[p["wlayer"]]
        for q, c in wpx.items():
            if inb(*q):
                wl.px[q] = [None, (0, 0, 1), 0, c, 999]
        if p["wlayer"] == "Weapon":
            shimmer = frame_i % 3
            for k, q in enumerate(edge):
                if inb(*q) and wpx[q] in ("Y2", "Y3"):
                    FX["Glow"].put([q], "Y3" if (k + shimmer) % 5 else "Y2")
        info["blade"] = {q for q, c in wpx.items() if c[0] in "SYG" and inb(*q)}
        # blade-only (exclude hilt) for hit rects
        ca, sa = math.cos(math.radians(p["wang"])), math.sin(math.radians(p["wang"]))
        info["blade"] = {q for q in info["blade"]
                         if (q[0] + .5 - p["grip"][0]) * ca + (q[1] + .5 - p["grip"][1]) * sa > 6}
        info["tip"] = weapon_point(p["grip"], p["wang"], BLADE["end"] - 2, 0, p["wflip"])
        info["edge"] = edge
    draw_cape(L, j, sec["cape"], frame_i, None)
    draw_pauldron_far(L, j)
    draw_arm(L["BackArm"], j, "far", -1)
    draw_legs(L, j)
    j["tab_sw"] = sec["tab"]
    draw_body(L, j, sec["cape"])
    draw_mantle(L, j, sec["cape"])
    eyes, vy = draw_head(L, j, frame_i, sec["hood"])
    draw_arm(L["FrontArm"], j, "near", 0)
    draw_pauldron_near(L, j)
    e = p.get("eyes", 1.0)
    for k, q in enumerate(eyes):
        FX["Glow"].put([q], "Y3")
        FX["Glow"].put([(q[0], q[1] + 1)], "Y1" if k % 2 == 0 else "Y0")
    if e > 1.0:  # flaring eyes + trailing wisp
        for q in eyes:
            FX["Glow"].put([(q[0], q[1] - 1)], "Y1")
        ex, ey = eyes[-1]
        for i in range(int(4 * e)):
            FX["Glow"].put([(ex + 1 + i, ey - (i // 3))], "Y1" if i < 3 else "Y0")
    if p.get("smear"):
        fx_swept(FX, info, p, p["smear"])
    for f in p.get("fx", []):
        FX_FUNCS[f[0]](FX, info, j, frame_i, *f[1:])
    info["j"] = j
    info["eyes"] = eyes
    return L, FX, info


def compose(L, FX, info):
    glow = info["edge"]
    imgs = {}
    for n in BASE_LAYERS:
        if n in L:
            imgs[n] = render_layer(L[n], glow_pts=glow if n not in ("Weapon", "WeaponBack") else (),
                                   outline=True, rim=n not in ("Weapon", "WeaponBack", "Cape"))
        else:
            imgs[n] = FX[n].image()
    return imgs


# =========================================================================== FX
def smear_color(age, x, y, edge_d):
    """age 0 = newest (just behind the blade), 1 = oldest tail."""
    if age < 0.2:
        return "Y3" if edge_d < 2.5 else "Y2"
    if age < 0.45:
        return "Y2" if edge_d < 2 else "Y1"
    if age < 0.7:
        return "Y1" if edge_d < 2 else "Y0"
    return "G4" if edge_d < 2 else "G3"


def fx_swept(FX, info, p, sm):
    """Swept-blade smear: union of densely sampled blade placements between two poses."""
    g0, a0 = sm["frm"]
    g1, a1 = sm.get("to", (p["grip"], p["wang"]))
    mid = sm.get("mid")
    start = sm.get("start", 0.0)
    arc = abs(a1 - a0) * math.pi / 180 * BLADE["end"] + math.hypot(g1[0] - g0[0], g1[1] - g0[1])
    n = max(8, int(arc * (1 - start) / 1.6))
    layer = FX[sm.get("layer", "FX")]
    reach0 = sm.get("inner", 20)
    best = {}
    for i in range(n):
        t = start + (1 - start) * i / n
        gp = lerp(lerp(g0, mid, t), lerp(mid, g1, t), t) if mid else lerp(g0, g1, t)
        ang = a0 + (a1 - a0) * t
        age = 1 - (t - start) / (1 - start)
        umin = reach0 + age * sm.get("taper", 22)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for q in blade_mask(gp, ang, p["wflip"], umin=umin):
            u = (q[0] + .5 - gp[0]) * ca + (q[1] + .5 - gp[1]) * sa
            ed = BLADE["end"] - u
            if q not in best or best[q][0] > age:
                best[q] = (age, ed)
    blade = info["blade"]
    hot = set()
    for q, (age, ed) in best.items():
        if q in blade or not inb(*q) or q[1] >= p.get("bury", 999):
            continue
        if age > 0.6 and ed > 2.5 and int(ed / 2.5) % 2 == 1:
            continue  # tail breaks into clean streaks
        if age > 0.85 and ed > 2.5:
            continue
        layer.put([q], smear_color(age, q[0], q[1], ed))
        if age < sm.get("hot", 0.55):
            hot.add(q)
    info["smear"] |= hot


def fx_hsweep(FX, info, j, fi, c, rin, rout, k, th0, th1, bright=1.0):
    """Horizontal sweep seen from the side: an elliptical annulus band between radius rin..rout
    (vertical squash k).  th in degrees; sin(th)>0 = near half (in front of body), else behind."""
    cx, cy = c
    lo, hi = min(th0, th1), max(th0, th1)
    pts = set()
    for y in range(int(cy - rout * k) - 3, int(cy + rout * k) + 4):
        for x in range(int(cx - rout) - 2, int(cx + rout) + 3):
            dx, dy = x + .5 - cx, (y + .5 - cy) / k
            r = math.hypot(dx, dy)
            if not (rin <= r <= rout):
                continue
            th = math.degrees(math.atan2(dy, dx))
            # unwrap into [lo, hi]
            while th < lo:
                th += 360
            if th > hi:
                continue
            t = (th - th0) / (th1 - th0)  # 0 at start (old) .. 1 at blade
            age = 1 - t
            edge_d = rout - r
            if age > 0.55 and edge_d > 2 and int(edge_d / 3) % 2 == 1:
                continue  # clean streaks instead of noise
            if age > 0.85 and edge_d > 2:
                continue
            if bright < 1 and int(edge_d / 2) % 3 != 0:
                continue
            col = smear_color(age, x, y, edge_d)
            if r < rin + 3 and age > 0.3:
                col = "G3" if age > 0.6 else "Y0"
            front = math.sin(math.radians(th)) > 0
            (FX["FX"] if front else FX["FXBack"]).put([(x, y)], col)
            if age < 0.6 and bright >= 1:
                pts.add((x, y))
    for q in info["blade"]:
        FX["FX"].px.pop(q, None)
    info["smear"] |= pts


def fx_dlines(FX, info, j, fi, offs):
    """Speed streaks parallel to the blade, trailing behind the tip."""
    g, a, fl = j["grip"], j["wang"], j["wflip"]
    for i, o in enumerate(offs):
        u0 = 14 + (i * 5) % 9
        u1 = 44 - (i * 3) % 7
        p0 = weapon_point(g, a, u0, o, fl)
        p1 = weapon_point(g, a, u1, o, fl)
        pts = line(p1, p0)
        FX["FX"].put(pts, "Y1" if i % 2 == 0 else "Y0")
        FX["FX"].put(pts[:5], "Y3")


def fx_lines(FX, info, j, fi, x0, x1, ys):
    for i, y in enumerate(ys):
        a = x0 + (i * 7) % 13
        b = x1 - (i * 5) % 11
        FX["FX"].put(line((a, y), (b, y)), "Y1" if i % 2 == 0 else "Y0")
        FX["FX"].put(line((a, y), (a + 6, y)), "Y3")
        pass


def fx_tipflash(FX, info, j, fi, r):
    if not info["tip"]:
        return
    tx, ty = info["tip"]
    for ang in range(0, 360, 45):
        ln = r if ang % 90 == 0 else r * 0.5
        FX["FX"].put(line((tx, ty), (tx + math.cos(math.radians(ang)) * ln, ty + math.sin(math.radians(ang)) * ln)),
                     "Y2" if ang % 90 == 0 else "Y1")
    FX["FX"].put([(int(tx), int(ty))], "Y3")


def rock(FX, c, sz, seed):
    m = mask_disc(c, sz + 0.4, sz * 0.8 + 0.4)
    for q in m:
        lv = 3 if (q[0] - c[0]) + (q[1] - c[1]) < -0.5 else 2 if (q[0] - c[0]) + (q[1] - c[1]) < 1 else 1
        FX["FX"].put([q], "S%d" % lv)
    for q in list(m):
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nq = (q[0] + d[0], q[1] + d[1])
            if nq not in m and inb(*nq) and nq not in FX["FX"].px:
                FX["FX"].put([nq], "OUT")


def fx_impact(FX, info, j, fi, cx, stage):
    """Ground impact: shock ring, sparks, debris, dust.  stage 0 = hit, 1 = held."""
    gy = GROUND
    if stage == 0:
        for y in range(gy - 8, gy + 1):
            for x in range(int(cx) - 30, int(cx) + 31):
                d = ((x + .5 - cx) / 28) ** 2 + ((y + .5 - gy) / 7) ** 2
                if 0.7 <= d <= 1.0:
                    FX["FX"].put([(x, y)], "Y2" if d > 0.85 else "Y3")
                elif 0.45 <= d < 0.7 and (x + y) % 2 == 0:
                    FX["FX"].put([(x, y)], "Y0")
        for k in range(13):
            a = math.radians(190 + k * 12.5)
            r0, r1 = 5 + k % 3, 14 + (k * 7) % 11
            FX["FX"].put(line((cx + math.cos(a) * r0, gy - 2 + math.sin(a) * r0),
                              (cx + math.cos(a) * r1, gy - 2 + math.sin(a) * r1)), "Y2" if k % 2 else "Y3")
    # debris
    for k in range(10):
        hx_ = hash01(k, 1, 41); hy_ = hash01(k, 2, 41)
        rx = cx + (hx_ - 0.45) * 44 * (1 + stage * 0.5)
        ry = gy - 4 - hy_ * 16 - stage * (6 + k % 4 * 3) + (stage * stage * 2)
        rock(FX, (rx, ry), 1 + (k % 3 == 0) + (k % 5 == 0), k)
    # dust puffs
    for k in range(6):
        dx = (k - 2.5) * 9 * (1 + stage * 0.4)
        c = (cx + dx, gy - 3 - stage * 2)
        m = mask_disc(c, 4 + stage * 2, 3 + stage)
        for q in m:
            if q[1] <= gy and hash01(q[0], q[1], 42 + stage) > 0.25 * stage:
                FX["FXBack"].put([q], "F2" if (q[0] + q[1]) % 3 else "F1")
    if stage == 1:
        for k in range(14):
            FX["FX"].put([(int(cx + (hash01(k, 3, 43) - 0.5) * 50), int(gy - 6 - hash01(k, 4, 43) * 28))],
                         "Y1" if k % 3 else "Y2")
    info["smear"] |= {(x, y) for x in range(int(cx) - 20, int(cx) + 21) for y in range(gy - 12, gy + 1)}


def fx_cracks(FX, info, j, fi, cx, reach, bright):
    """Molten cracks racing along the ground from the buried blade."""
    gy = GROUND
    for side in (-1, 1):
        x, y = cx, gy - 1
        pts = []
        k = 0
        while abs(x - cx) < reach:
            nx = x + side * (2 + hash01(k, side, 51) * 3)
            ny = gy - 1 - int(hash01(k, side, 52) * 3)
            pts += line((x, y), (nx, ny))
            if hash01(k, side, 53) > 0.6:  # branch
                pts += line((nx, ny), (nx + side * 3, ny - 2 - int(hash01(k, 5, 54) * 3)))
            x, y = nx, ny
            k += 1
        for i, q in enumerate(pts):
            fade = abs(q[0] - cx) / max(1, reach)
            FX["FX"].put([q], "Y3" if fade < 0.3 * bright else "Y2" if fade < 0.6 else "Y1")
            if q[1] - 1 > gy - 6 and bright > 0.5:
                FX["FX"].put([(q[0], q[1] - 1)], "Y0" if (q[0] % 3) else "Y1")
    # rising sparks / heat
    for k in range(int(10 * bright)):
        sx = cx + (hash01(k, fi, 55) - 0.5) * reach * 1.6
        sy = gy - 4 - hash01(k, fi, 56) * 24 * bright
        FX["FX"].put([(int(sx), int(sy))], "Y1" if k % 2 else "Y2")
    # glowing pool at the blade
    for q in mask_disc((cx, gy), 7 * bright + 2, 2.5):
        if q[1] <= gy:
            FX["FX"].put([q], "Y2")


def fx_orb(FX, info, j, fi, r, rays):
    if not info["tip"]:
        return
    tx, ty = info["tip"]
    for q in mask_disc((tx, ty), r + 2.5):
        FX["FX"].put([q], "Y0" if (q[0] + q[1]) % 2 == 0 else "Y1") if r > 3 else None
    for q in mask_disc((tx, ty), r + 1):
        FX["FX"].put([q], "Y1")
    for q in mask_disc((tx, ty), r * 0.6 + 0.8):
        FX["FX"].put([q], "Y2")
    for q in mask_disc((tx, ty), r * 0.3 + 0.6):
        FX["FX"].put([q], "Y3")
    for k in range(rays):
        a = math.radians(k * 360 / rays + fi * 17)
        ln = r + 4 + (k % 2) * 5
        FX["FX"].put(line((tx + math.cos(a) * (r + 1), ty + math.sin(a) * (r + 1)),
                          (tx + math.cos(a) * ln, ty + math.sin(a) * ln)), "Y1" if k % 2 else "Y2")
    # motes being drawn in toward the tip
    for k in range(10):
        a = hash01(k, 1, 61) * 6.283
        d = 10 + hash01(k, fi, 62) * 22
        FX["FX"].put([(int(tx + math.cos(a) * d), int(ty + math.sin(a) * d))], "Y1" if k % 2 else "G4")


def fx_flash(FX, info, j, fi):
    tx, ty = info["tip"]
    for k in range(16):
        a = math.radians(k * 22.5)
        ln = 26 if k % 4 == 0 else 14 if k % 2 == 0 else 8
        FX["FX"].put(line((tx, ty), (tx + math.cos(a) * ln, ty + math.sin(a) * ln)), "Y3" if k % 4 == 0 else "Y2")
    for q in mask_disc((tx, ty), 6):
        FX["FX"].put([q], "Y3")
    ring = [q for q in mask_disc((tx, ty), 14) if q not in mask_disc((tx, ty), 12.5)]
    FX["FX"].put(ring, "Y1")


def fx_roar(FX, info, j, fi, r, strength):
    """Expanding power burst centred on the chest."""
    cx, cy = add(j["C"], (0, -8))
    ring = [q for q in mask_disc((cx, cy), r, r * 0.8) if q not in mask_disc((cx, cy), r - 3.2, r * 0.8 - 3)]
    inner = set(mask_disc((cx, cy), r - 1.2, r * 0.8 - 1.2))
    for q in ring:
        if hash01(q[0] // 2, q[1] // 2, 71) < 0.35 + 0.65 * strength:
            FX["FX"].put([q], "Y2" if q not in inner else ("Y3" if strength > 0.7 else "Y1"))
    for k in range(18):
        a = math.radians(k * 20 + fi * 7)
        r0 = r * 0.55 + (k % 3) * 3
        r1 = r0 + 6 + (k % 2) * 6
        FX["FXBack"].put(line((cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.8),
                              (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.8)), "Y2" if k % 2 else "Y0")
    # ground dust blown outward
    for k in range(8):
        dx = (k - 3.5) * (r * 0.3 + 6)
        for q in mask_disc((cx + dx, GROUND - 2), 3 + strength * 2, 2.2):
            if q[1] <= GROUND and hash01(q[0], q[1], 72) > 0.3:
                FX["FXBack"].put([q], "F2" if q[0] % 2 else "F1")


FX_FUNCS = {"hsweep": fx_hsweep, "lines": fx_lines, "dlines": fx_dlines, "tipflash": fx_tipflash, "impact": fx_impact,
            "cracks": fx_cracks, "orb": fx_orb, "flash": fx_flash, "roar": fx_roar}


# =========================================================================== animation keyframes
def anim_idle():
    fr = []
    for i in range(6):
        b = (0, 1, 2, 2, 1, 0)[i]
        fr.append((160, P_(C=(98, 61 + b), Hd=(94, 40 + b), P=(100, 85 + (b > 1)),
                           grip=(80, 84 + (b > 1)), wang=148 - (b > 1),
                           cape_wind=(0, 1, 2, 3, 2, 1)[i] * 0.6)))
    return fr


def anim_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        nf = (88 - 13 * c, GROUND - max(0.0, -s) * 7)
        ff = (112 + 13 * c, GROUND - max(0.0, s) * 7)
        bob = 2.5 * abs(c)  # lowest at contact
        fr.append((110, P_(P=(100, 84 + bob), C=(98 - c * 1.5, 60 + bob), Hd=(93 - c * 1.5, 39 + bob + 0.5),
                           tw=0.45 * c, foot_near=nf, foot_far=ff,
                           grip=(80 - c * 3, 84 + bob), wang=148 + c * 3, cape_wind=2.0)))
    return fr


def anim_backstep():
    return [
        (80, P_(P=(100, 90), C=(95, 67), Hd=(88, 47), foot_near=(82, 127), foot_far=(118, 127),
                grip=(80, 88), wang=152, look=-1)),
        (80, P_(P=(103, 82), C=(104, 58), Hd=(99, 37), foot_near=(88, 125), foot_far=(122, 123),
                grip=(84, 80), wang=160, cape_wind=-3, cape_flare=4)),
        (100, P_(P=(103, 79), C=(106, 56), Hd=(102, 35), foot_near=(90, 121), foot_far=(118, 120),
                 grip=(84, 76), wang=165, cape_wind=-5, cape_flare=8, tab_wind=-4)),
        (100, P_(P=(101, 93), C=(98, 71), Hd=(91, 51), foot_near=(80, 127), foot_far=(124, 127),
                 grip=(78, 90), wang=150, look=-1, cape_wind=2)),
        (120, P_(P=(100, 87), C=(98, 63), Hd=(93, 42), grip=(80, 85), wang=149, cape_wind=1)),
    ]


def anim_combo():
    WB = dict(wlayer="WeaponBack")
    f = []
    # -------- hit 1: diagonal downward slash
    f.append((110, P_(P=(101, 86), C=(103, 62), Hd=(99, 42), tw=0.7, grip=(98, 50), wang=316, **WB,
                      foot_near=(78, 127), foot_far=(122, 127))))
    f.append((260, P_(P=(103, 90), C=(108, 63), Hd=(104, 44), tw=1.1, grip=(108, 36), wang=328, **WB,
                      foot_near=(76, 127), foot_far=(124, 127), eyes=1.5)))
    f.append((60, P_(P=(95, 91), C=(83, 70), Hd=(73, 52), tw=-0.9, grip=(66, 88), wang=150,
                     foot_near=(66, 127), foot_far=(122, 127), cape_wind=2,
                     smear=dict(frm=((108, 36), 328), mid=(76, 40), start=0.3, inner=14, taper=22))))
    f.append((90, P_(P=(95, 92), C=(83, 72), Hd=(73, 54), tw=-0.9, grip=(68, 94), wang=153,
                     foot_near=(66, 127), foot_far=(122, 127), cape_wind=1,
                     smear=dict(frm=((68, 86), 178), start=0.0, inner=26, taper=16))))
    # -------- hit 2: twist then rising upswing
    f.append((120, P_(P=(97, 93), C=(88, 73), Hd=(79, 54), tw=-1.0, grip=(74, 98), wang=158,
                      foot_near=(68, 127), foot_far=(123, 127))))
    f.append((180, P_(P=(98, 97), C=(88, 78), Hd=(78, 60), tw=-1.2, grip=(82, 96), wang=165, look=-1,
                      foot_near=(68, 127), foot_far=(124, 127), eyes=1.3)))
    f.append((60, P_(P=(96, 84), C=(90, 57), Hd=(84, 36), tw=-0.3, grip=(74, 56), wang=242, look=1,
                     foot_near=(72, 127), foot_far=(120, 127), cape_wind=-2,
                     smear=dict(frm=((82, 96), 165), mid=(56, 100), start=0.0, inner=14, taper=22, hot=1.0))))
    f.append((90, P_(P=(97, 84), C=(93, 58), Hd=(87, 37), tw=0.1, grip=(80, 54), wang=256,
                     foot_near=(74, 127), foot_far=(120, 127),
                     smear=dict(frm=((72, 58), 230), inner=28, taper=12))))
    # -------- hit 3: big delayed hold, full horizontal sweep
    f.append((150, P_(P=(101, 87), C=(103, 62), Hd=(98, 42), tw=0.8, grip=(102, 58), wang=300, **WB,
                      foot_near=(76, 127), foot_far=(122, 127))))
    f.append((380, P_(P=(104, 92), C=(111, 67), Hd=(106, 49), tw=1.4, grip=(116, 74), wang=356, **WB,
                      foot_near=(70, 127), foot_far=(126, 127), look=-1, eyes=2.0, cape_wind=-1)))
    f.append((60, P_(P=(95, 97), C=(83, 75), Hd=(73, 56), tw=-1.2, grip=(64, 102), wang=181,
                     foot_near=(62, 127), foot_far=(125, 127), cape_wind=4, cape_flare=6, tab_wind=4,
                     fx=[("hsweep", (96, 110), 22, 88, 0.16, -12, 178)])))
    f.append((120, P_(P=(96, 96), C=(86, 74), Hd=(76, 55), tw=-1.0, grip=(66, 104), wang=170,
                      foot_near=(63, 127), foot_far=(124, 127), cape_wind=3,
                      fx=[("hsweep", (96, 110), 26, 86, 0.16, 110, 190, 0.45)])))
    f.append((180, P_(P=(99, 90), C=(93, 67), Hd=(86, 47), tw=-0.4, grip=(74, 94), wang=156,
                      foot_near=(70, 127), foot_far=(122, 127), cape_wind=1)))
    f.append((180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)))
    return f


def anim_thrust():
    lunge = dict(P=(92, 98), C=(84, 78), Hd=(74, 59), tw=-1.2, foot_near=(54, 127), foot_far=(126, 127), look=-1)
    return [
        (140, P_(P=(101, 87), C=(102, 63), Hd=(97, 43), tw=0.5, grip=(94, 80), wang=172)),
        (160, P_(P=(104, 91), C=(107, 68), Hd=(102, 49), tw=0.9, grip=(110, 82), wang=170,
                 foot_near=(78, 127), foot_far=(126, 127))),
        (380, P_(P=(107, 96), C=(113, 73), Hd=(107, 55), tw=1.4, grip=(124, 86), wang=168, look=-1,
                 foot_near=(78, 127), foot_far=(131, 127), eyes=2.0, cape_wind=-1)),
        (60, P_(**lunge, grip=(58, 88), wang=162, cape_wind=5, cape_flare=6, tab_wind=4,
                fx=[("dlines", (-6, -4, 8, 10)), ("tipflash", 7)])),
        (100, P_(**lunge, grip=(60, 88), wang=162, cape_wind=3)),
        (120, P_(P=(95, 94), C=(89, 73), Hd=(80, 54), tw=-0.7, grip=(68, 88), wang=160,
                 foot_near=(62, 127), foot_far=(123, 127), cape_wind=1)),
        (160, P_(P=(99, 89), C=(95, 66), Hd=(88, 46), tw=-0.2, grip=(76, 86), wang=153,
                 foot_near=(72, 127), foot_far=(121, 127))),
        (160, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]


def anim_leap():
    WB = dict(wlayer="WeaponBack")
    return [
        (140, P_(P=(100, 93), C=(94, 71), Hd=(86, 52), grip=(82, 92), wang=158, look=-1)),
        (140, P_(P=(101, 98), C=(95, 77), Hd=(87, 58), grip=(92, 100), wang=170, look=-1,
                 foot_near=(78, 127), foot_far=(122, 127), eyes=1.4)),
        (120, P_(P=(100, 78), C=(100, 53), Hd=(96, 32), grip=(100, 38), wang=322, **WB, look=1,
                 foot_near=(90, 121), foot_far=(112, 119), cape_wind=4, cape_flare=6)),
        (160, P_(P=(100, 79), C=(103, 55), Hd=(99, 35), tw=0.6, grip=(108, 30), wang=345, **WB,
                 foot_near=(86, 118), foot_far=(118, 117), cape_wind=-3, cape_flare=10, eyes=1.6)),
        (160, P_(P=(98, 81), C=(94, 58), Hd=(86, 39), tw=-0.3, grip=(88, 46), wang=300, **WB,
                 foot_near=(82, 120), foot_far=(116, 122), cape_wind=-5, cape_flare=10)),
        (60, P_(P=(93, 98), C=(80, 78), Hd=(70, 60), tw=-1.0, grip=(60, 92), wang=118, bury=126, look=-1,
                foot_near=(68, 127), foot_far=(122, 127), cape_wind=4, cape_flare=4,
                smear=dict(frm=((88, 46), 300), mid=(60, 50), start=0.3, inner=14, taper=22),
                fx=[("impact", 38, 0)])),
        (140, P_(P=(93, 97), C=(81, 77), Hd=(71, 59), tw=-1.0, grip=(60, 92), wang=118, bury=126, look=-1,
                 foot_near=(68, 127), foot_far=(122, 127), cape_wind=2,
                 fx=[("impact", 38, 1)])),
        (160, P_(P=(97, 93), C=(89, 72), Hd=(80, 52), tw=-0.5, grip=(72, 88), wang=135,
                 foot_near=(72, 127), foot_far=(121, 127))),
        (180, P_(P=(99, 88), C=(95, 65), Hd=(89, 44), tw=-0.2, grip=(78, 86), wang=146,
                 foot_near=(76, 127), foot_far=(120, 127))),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]


SPIN_C = (100, 108)


def anim_spin():
    WB = dict(wlayer="WeaponBack")
    low = dict(P=(99, 96), C=(92, 74), Hd=(83, 55), tw=-1.0, foot_near=(70, 127), foot_far=(126, 127),
               cape_wind=6, cape_flare=10, tab_wind=5)
    return [
        (150, P_(P=(101, 89), C=(102, 66), Hd=(97, 46), tw=0.6, grip=(94, 92), wang=160)),
        (150, P_(P=(103, 93), C=(107, 71), Hd=(101, 51), tw=1.0, grip=(106, 94), wang=80, **WB,
                 foot_near=(76, 127), foot_far=(125, 127))),
        (300, P_(P=(104, 97), C=(110, 76), Hd=(104, 57), tw=1.4, grip=(114, 104), wang=10, **WB, look=-1,
                 foot_near=(72, 127), foot_far=(129, 127), eyes=2.0)),
        (50, P_(**low, grip=(70, 100), wang=178,
                fx=[("hsweep", SPIN_C, 22, 86, 0.17, 20, 180)])),
        (50, P_(P=(101, 96), C=(106, 74), Hd=(100, 55), tw=1.4, grip=(116, 104), wang=357, wflip=-1, **WB,
                foot_near=(74, 127), foot_far=(124, 127), cape_wind=-6, cape_flare=12, tab_wind=-5,
                fx=[("hsweep", (SPIN_C[0], SPIN_C[1] + 9), 22, 86, 0.17, 180, 358),
                    ("hsweep", SPIN_C, 30, 86, 0.17, 110, 180, 0.4)])),
        (50, P_(**low, grip=(72, 101), wang=179,
                fx=[("hsweep", SPIN_C, 22, 86, 0.17, 2, 178), ("hsweep", SPIN_C, 30, 86, 0.17, 290, 360, 0.4)])),
        (120, P_(P=(99, 94), C=(93, 72), Hd=(85, 53), tw=-0.8, grip=(74, 100), wang=165,
                 foot_near=(71, 127), foot_far=(124, 127), cape_wind=4, cape_flare=4,
                 fx=[("hsweep", SPIN_C, 30, 84, 0.17, 90, 170, 0.35)])),
        (160, P_(P=(100, 90), C=(95, 67), Hd=(88, 47), tw=-0.4, grip=(77, 92), wang=156, cape_wind=2)),
        (180, P_(P=(100, 87), C=(97, 63), Hd=(92, 42), grip=(80, 87), wang=150, cape_wind=1)),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]


def anim_cast():
    up = dict(P=(100, 84), C=(99, 59), Hd=(95, 37), tw=0.2, grip=(76, 66), wang=268, look=1)
    return [
        (150, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(82, 78), wang=205)),
        (150, P_(P=(100, 85), C=(99, 60), Hd=(95, 38), tw=0.1, grip=(78, 70), wang=250, look=1)),
        (200, P_(**up, eyes=1.3, fx=[("orb", 2, 6)])),
        (200, P_(**up, eyes=1.6, fx=[("orb", 4, 8)])),
        (200, P_(**up, eyes=2.0, fx=[("orb", 6.5, 10)])),
        (80, P_(P=(100, 85), C=(98, 60), Hd=(94, 38), tw=0.2, grip=(76, 67), wang=266, look=1, eyes=2.0,
                fx=[("flash",)])),
        (150, P_(P=(100, 85), C=(98, 60), Hd=(94, 39), grip=(78, 70), wang=240, fx=[("orb", 2, 4)])),
        (150, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 76), wang=200)),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 82), wang=160)),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]


ERUPT_X = 74


def anim_eruption():
    hold = dict(P=(96, 97), C=(87, 76), Hd=(78, 57), tw=-0.7, grip=(76, 84), wang=92, bury=126, look=-1,
                foot_near=(68, 127), foot_far=(122, 127))
    return [
        (150, P_(P=(100, 86), C=(98, 61), Hd=(93, 41), grip=(86, 66), wang=210)),
        (150, P_(P=(100, 84), C=(98, 59), Hd=(94, 38), grip=(84, 40), wang=150, look=1)),
        (250, P_(P=(100, 82), C=(97, 57), Hd=(94, 36), tw=-0.2, grip=(80, 22), wang=91, look=1, eyes=1.8,
                 foot_near=(76, 127), foot_far=(122, 127), cape_wind=-1)),
        (60, P_(**hold, cape_wind=3, cape_flare=4,
                fx=[("lines", 0, 0, ()), ("impact", ERUPT_X, 0)],
                smear=dict(frm=((80, 22), 91), n=8, inner=10, taper=4))),
        (400, P_(**hold, eyes=1.5, fx=[("cracks", ERUPT_X, 40, 1.0)])),
        (300, P_(**hold, eyes=1.5, fx=[("cracks", ERUPT_X, 60, 1.0)])),
        (200, P_(**hold, fx=[("cracks", ERUPT_X, 66, 0.5)])),
        (150, P_(P=(98, 90), C=(93, 68), Hd=(86, 48), tw=-0.4, grip=(79, 72), wang=94, bury=126,
                 foot_near=(70, 127), foot_far=(122, 127))),
        (150, P_(P=(99, 87), C=(96, 63), Hd=(90, 43), grip=(82, 66), wang=130)),
        (180, P_(P=(100, 86), C=(97, 62), Hd=(92, 41), grip=(80, 80), wang=146)),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]


def anim_roar():
    spread = dict(twohand=False, grip=(62, 62), wang=198, hand_far=(138, 40), look=1, tw=0.4)
    fr = [
        (150, P_(P=(100, 90), C=(96, 68), Hd=(88, 49), grip=(82, 88), wang=152, look=-1)),
        (150, P_(P=(100, 93), C=(96, 72), Hd=(88, 53), grip=(84, 92), wang=156, look=-1, eyes=1.4)),
        (150, P_(P=(101, 87), C=(101, 62), Hd=(98, 40), twohand=False, grip=(68, 70), wang=175,
                 hand_far=(130, 48), look=1, eyes=1.8)),
    ]
    for k, (r, stg) in enumerate(((14, 1.0), (26, 0.9), (38, 0.8), (50, 0.6), (62, 0.4))):
        fr.append((200, P_(P=(102, 86), C=(107, 58), Hd=(107, 35), **spread, eyes=2.2, cape_wind=-3,
                           cape_flare=8, shake=(1 if k % 2 == 0 else -1), fx=[("roar", r, stg)])))
    fr.append((250, P_(P=(100, 86), C=(100, 60), Hd=(96, 39), twohand=False, grip=(70, 76), wang=160,
                       hand_far=(122, 70), eyes=1.5)))
    fr.append((300, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)))
    return fr


KNEEL_ONE = dict(P=(102, 99), C=(96, 78), Hd=(88, 60), look=-1, tw=-0.3,
                 foot_near=(80, 127), foot_far=(128, 127), kneel_far=(112, 123),
                 twohand=False, grip=(80, 88), wang=94, bury=126, hand_far=(112, 101))


def anim_stagger():
    return [
        (120, P_(P=(104, 84), C=(108, 60), Hd=(106, 39), look=1, twohand=False, grip=(84, 92), wang=128,
                 hand_far=(128, 56), foot_near=(84, 127), foot_far=(122, 127), cape_wind=-4, cape_flare=4)),
        (160, P_(P=(103, 93), C=(100, 72), Hd=(93, 53), look=-1, twohand=False, grip=(82, 90), wang=100,
                 bury=126, hand_far=(116, 90), foot_near=(81, 127), foot_far=(126, 127), kneel_far=(113, 118))),
        (300, P_(**KNEEL_ONE)),
        (200, P_(P=(102, 94), C=(97, 72), Hd=(90, 53), look=-1, twohand=False, grip=(80, 88), wang=96, bury=126,
                 hand_far=(114, 92), foot_near=(80, 127), foot_far=(124, 127), kneel_far=(113, 116))),
    ]


KNEEL_BOTH = dict(P=(100, 103), C=(93, 82), Hd=(85, 64), look=-1, tw=-0.2,
                  foot_near=(96, 127), foot_far=(126, 127), kneel_near=(82, 123), kneel_far=(110, 123),
                  grip=(76, 92), wang=93, bury=126)


def anim_death():
    fr = [
        (150, P_(P=(104, 84), C=(108, 60), Hd=(106, 39), look=1, twohand=False, grip=(84, 92), wang=128,
                 hand_far=(128, 58), foot_near=(84, 127), foot_far=(122, 127), cape_wind=-4)),
        (150, P_(P=(102, 90), C=(98, 67), Hd=(92, 47), grip=(78, 88), wang=95, bury=126,
                 foot_near=(80, 127), foot_far=(124, 127))),
        (200, P_(P=(101, 97), C=(95, 75), Hd=(88, 56), grip=(77, 90), wang=94, bury=126,
                 foot_near=(84, 127), foot_far=(126, 127), kneel_far=(112, 120))),
        (200, P_(**KNEEL_BOTH)),
        (200, P_(**dict(KNEEL_BOTH, Hd=(84, 67), C=(92, 84)), eyes=0.5)),
    ]
    for frac, ms in ((0.12, 200), (0.26, 200), (0.4, 200), (0.55, 250), (0.7, 300), (0.86, 350), (1.25, 700)):
        fr.append((ms, P_(**dict(KNEEL_BOTH, Hd=(84, 67), C=(92, 84)), eyes=0.5, dissolve=frac)))
    return fr


TAGDEFS = [("idle", anim_idle), ("walk", anim_walk), ("backstep", anim_backstep), ("combo", anim_combo),
           ("thrust", anim_thrust), ("leap", anim_leap), ("spin", anim_spin), ("cast", anim_cast),
           ("eruption", anim_eruption), ("roar", anim_roar), ("stagger", anim_stagger), ("death", anim_death)]
EXPECT = {"idle": [160] * 6, "walk": [110] * 8, "backstep": [80, 80, 100, 100, 120],
          "combo": [110, 260, 60, 90, 120, 180, 60, 90, 150, 380, 60, 120, 180, 180],
          "thrust": [140, 160, 380, 60, 100, 120, 160, 160],
          "leap": [140, 140, 120, 160, 160, 60, 140, 160, 180, 180],
          "spin": [150, 150, 300, 50, 50, 50, 120, 160, 180, 180],
          "cast": [150, 150, 200, 200, 200, 80, 150, 150, 180, 180],
          "eruption": [150, 150, 250, 60, 400, 300, 200, 150, 150, 180, 180],
          "roar": [150, 150, 150, 200, 200, 200, 200, 200, 250, 300],
          "stagger": [120, 160, 300, 200],
          "death": [150, 150, 200, 200, 200, 200, 200, 200, 250, 300, 350, 700]}


# =========================================================================== secondary motion
def secondary(frames, loop):
    """Spring-lagged cape / hood / tabard offsets driven by torso motion (+ explicit wind)."""
    state = {"cape": 0.0, "hood": 0.0, "tab": 0.0}
    vel = {"cape": 0.0, "hood": 0.0, "tab": 0.0}
    res = []
    for ps in range(2 if loop else 1):
        prev = frames[-1][1] if loop else frames[0][1]
        res = []
        for ms, p in frames:
            dxc = p["C"][0] - prev["C"][0]
            dxp = p["P"][0] - prev["P"][0]
            dxh = p["Hd"][0] - prev["Hd"][0]
            for k, drive, gain, stiff, wind in (("cape", dxc, 1.2, 0.4, 2.2), ("hood", dxh, 0.9, 0.55, 1.0),
                                                ("tab", dxp, 1.3, 0.5, 0.8)):
                target = -gain * drive * 1.8 + p.get("cape_wind", 0) * wind + (p.get("tab_wind", 0) if k == "tab" else 0)
                vel[k] = vel[k] * 0.4 + (target - state[k]) * stiff
                state[k] = max(-14.0, min(16.0, state[k] + vel[k]))
            res.append(dict(state))
            prev = p
    return res


# =========================================================================== phase-2 layers
def p2_layers(info, fi, k, layer_imgs):
    """Burning halo, blade fire, armour cracks, cape embers.  k = intensity 0..1."""
    out = {n: FXLayer(n) for n in P2_LAYERS}
    if k <= 0.01:
        return {n: out[n].image() for n in P2_LAYERS}
    j = info["j"]
    hx, hy = j["Hd"]
    # ---- halo: ring of gold fire behind the head
    hc = (hx + 5, hy - 11)
    R = 15 + 7 * k
    ring = [q for q in mask_disc(hc, R) if q not in mask_disc(hc, R - 2.2)]
    for q in ring:
        if hash01(q[0], q[1], 81) < 0.35 + 0.65 * k:
            out["Halo"].put([q], "Y2" if hash01(q[0], q[1], fi) > 0.4 else "Y1")
    inner = [q for q in mask_disc(hc, R - 2.2) if q not in mask_disc(hc, R - 3.4)]
    out["Halo"].put([q for q in inner if (q[0] + q[1]) % 2 == 0], "Y0")
    for t in range(int(22 * k)):
        a = t * 2 * math.pi / 22 + fi * 0.13
        base = (hc[0] + math.cos(a) * R, hc[1] + math.sin(a) * R)
        ln = (3 + hash01(t, fi, 82) * 6) * k
        tip = (base[0] + math.cos(a) * ln * 0.6, base[1] + math.sin(a) * ln * 0.6 - ln * 0.7)
        pts = line(base, tip)
        for i, q in enumerate(pts):
            out["Halo"].put([q], "Y2" if i < len(pts) * 0.4 else "Y0" if i < len(pts) * 0.8 else "R1")
    # ---- blade fire: tongues rising (screen-up) off the edge
    if info["tip"] and j["weapon"]:
        g, a_, fl = j["grip"], j["wang"], j["wflip"]
        for kk, u in enumerate(range(10, BLADE["end"] - 2, 3)):
            base = weapon_point(g, a_, u, 3.5, fl)
            if j.get("bury") and base[1] >= j["bury"]:
                continue
            hgt = (4 + hash01(kk, fi, 83) * 7) * k
            sway = (hash01(kk, fi, 84) - 0.5) * 3
            for i in range(int(hgt)):
                t = i / max(1, hgt)
                x = base[0] + sway * t * t
                y = base[1] - i
                wdt = 1.6 * (1 - t) + 0.3
                c = "Y3" if t < 0.25 else "Y2" if t < 0.5 else "Y0" if t < 0.8 else "R1"
                for dx in range(-int(wdt), int(wdt) + 1):
                    out["BladeFire"].put([(int(x + dx), int(y))], c)
    # ---- armour cracks (only where the owning layer is visible on top)
    C, P = j["C"], j["P"]
    cracks = {
        "Body": [[add(C, (2, -8)), add(C, (5, -3)), add(C, (3, 2)), add(C, (7, 7))],
                 [add(C, (5, -3)), add(C, (10, -2)), add(C, (13, 3))],
                 [add(P, (6, -12)), add(P, (9, -8)), add(P, (7, -4))]],
        "FrontArm": [[add(j["Ns"], (-8, -3)), add(j["Ns"], (-4, 0)), add(j["Ns"], (-6, 4))],
                     [add(j["Ns"], (-4, 0)), add(j["Ns"], (1, -2))]],
        "Legs": [[add(j.get("knee_near", P), (0, 4)), add(j.get("knee_near", P), (-1, 10)),
                  add(j.get("knee_near", P), (1, 15))]],
        "Head": [[add(j["Hd"], (-6, 3)), add(j["Hd"], (-4, 6)), add(j["Hd"], (-5, 9))]],
    }
    above = {n: BASE_LAYERS[BASE_LAYERS.index(n) + 1:] for n in cracks}
    for lname, polys in cracks.items():
        src = layer_imgs[lname].load()
        for pl in polys:
            for i, q in enumerate(polyline(pl)):
                if not inb(*q) or src[q][3] == 0:
                    continue
                if any(layer_imgs[a].load()[q][3] and a not in ("Glow", "FX", "FXBack") for a in above[lname]):
                    continue
                if hash01(i, 0, 85) > 0.25 + 0.75 * k:
                    continue
                out["Cracks"].put([q], "Y2" if i % 3 else "Y1")
                n2 = (q[0] + 1, q[1])
                if inb(*n2) and src[n2][3] and hash01(i, 1, 86) < 0.4 * k:
                    out["Cracks"].put([n2], "Y0")
    # ---- embers streaming off the cape
    cape = layer_imgs["Cape"].load()
    edge = [(x, y) for y in range(40, H, 2) for x in range(W - 1, 90, -1) if cape[x, y][3]][:0]
    cols = {}
    for y in range(30, H):
        for x in range(W - 1, 60, -1):
            if cape[x, y][3]:
                cols[y] = x
                break
    ys = sorted(cols)
    for t in range(int(18 * k)):
        if not ys:
            break
        y0 = ys[int(hash01(t, 5, 87) * len(ys))]
        age = ((fi * 0.37 + hash01(t, 6, 88)) % 1.0)
        x = cols[y0] + 1 + age * 14 + math.sin(age * 6 + t) * 2
        y = y0 - age * 26
        c = "Y2" if age < 0.25 else "Y1" if age < 0.5 else "Y0" if age < 0.75 else "R1"
        out["Embers"].put([(int(x), int(y))], c)
        if age < 0.4:
            out["Embers"].put([(int(x) - 1, int(y) + 1)], "Y0")
    return {n: out[n].image() for n in P2_LAYERS}


# =========================================================================== dissolve
def dissolve(imgs, frac, extra=()):
    motes = {}
    out = {}
    names = [n for n in imgs if n not in ("FX",)]
    for n in names:
        src = imgs[n].load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                if src[x, y][3] == 0:
                    continue
                t = 0.55 * hash01(x, y, 91) + 0.45 * (y / H)
                if t >= frac:
                    if t < frac + 0.05:
                        dst[x, y] = RGBA["Y1"] if hash01(x, y, 92) > 0.5 else RGBA["G4"]
                    else:
                        dst[x, y] = src[x, y]
                elif hash01(x, y, 93) < 0.03 and n not in P2_LAYERS:
                    age = frac - t
                    mx = int(x + age * 26 + math.sin(y * 0.3) * 3)
                    my = int(y - age * 70 - hash01(x, y, 94) * 4)
                    if inb(mx, my) and age < 0.42:
                        motes[(mx, my)] = "Y3" if age < 0.08 else "Y1" if age < 0.2 else "G4" if age < 0.32 else "G3"
        out[n] = new
    fx = imgs["FX"].copy()
    fp = fx.load()
    for (x, y), c in motes.items():
        fp[x, y] = RGBA[c]
    out["FX"] = fx
    return out


# =========================================================================== output
def preview(images, path, scale=3, cols=8):
    rows = (len(images) + cols - 1) // cols
    pad = 2
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, rows * (H + pad) * scale), (0x0e, 0x0d, 0x16, 255))
    for i, im in enumerate(images):
        cx, cy = (i % cols) * (W + pad) * scale, (i // cols) * (H + pad) * scale
        fr = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
        fr.alpha_composite(im)
        sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), (cx, cy))
    sheet.save(path)


def flatten(imgs, order):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in order:
        if n in imgs:
            out.alpha_composite(imgs[n])
    return out


def shift_imgs(imgs, dx):
    from PIL import ImageChops
    out = {}
    for n, im in imgs.items():
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        o.paste(im, (dx, 0))
        out[n] = o
    return out


def bbox(pts, pad=1):
    pts = [p for p in pts if inb(*p)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def p2_intensity(tag, k, n, pose):
    if tag == "roar":
        return (0, 0, 0.1, 0.3, 0.55, 0.8, 1.0, 1.0, 1.0, 1.0)[k]
    if pose.get("dissolve"):
        return max(0.0, 1.0 - pose["dissolve"] * 1.4)
    return 1.0


PLAYER_BOX = (20, 103, 21, 25)  # x, y, w, h of a standing player next to the boss


def hit_check(frames, tags, meta):
    """Composite of every active frame with a 25px player silhouette + the meta rects."""
    start = {t: a for t, a, _ in tags}
    act = [(t, int(k)) for t, d in meta["attacks"].items() for k in d["rects"]]
    s = 3
    sheet = Image.new("RGBA", (len(act) * (W + 2) * s, (H + 14) * s), (0x0e, 0x0d, 0x16, 255))
    pl = None
    try:
        pim = Image.open(os.path.join(asebuild.ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
        bb = pim.getbbox()
        pl = pim.crop(bb)
    except Exception:
        pass
    from PIL import ImageDraw
    for i, (t, k) in enumerate(act):
        fr = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
        fr.alpha_composite(flatten(frames[start[t] + k]["cels"], BASE_LAYERS))
        d = ImageDraw.Draw(fr)
        px, py, pw, ph = PLAYER_BOX
        if pl is not None:
            fr.alpha_composite(pl, (px + (pw - pl.width) // 2, H - pl.height))
        d.rectangle([px, py, px + pw - 1, py + ph - 1], outline=(80, 200, 255, 255))
        r = meta["attacks"][t]["rects"][str(k)]
        d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 60, 60, 255))
        hit = not (r[0] + r[2] <= px or px + pw <= r[0] or r[1] + r[3] <= py or py + ph <= r[1])
        lab = Image.new("RGBA", (W, 14), (0x0e, 0x0d, 0x16, 255))
        ImageDraw.Draw(lab).text((2, 1), f"{t} f{k} {'HIT' if hit else 'MISS'}",
                                 fill=(120, 255, 120, 255) if hit else (255, 90, 90, 255))
        col = Image.new("RGBA", (W, H + 14))
        col.paste(lab, (0, 0)); col.paste(fr, (0, 14))
        sheet.alpha_composite(col.resize((W * s, (H + 14) * s), Image.NEAREST), (i * (W + 2) * s, 0))
        print("hitcheck", t, k, r, "HIT" if hit else "MISS")
    sheet.save(os.path.join(ART, "previews", "boss_hitcheck.png"))


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    frames, frames_p2, flats, flats_p2, tags, infos = [], [], [], [], [], {}
    for name, fn in TAGDEFS:
        if only and name not in only:
            continue
        fr = fn()
        assert [ms for ms, _ in fr] == EXPECT[name], (name, [ms for ms, _ in fr])
        sec = secondary(fr, loop=name in ("idle", "walk"))
        a = len(frames)
        infos[name] = []
        for k, (ms, p) in enumerate(fr):
            L, FX, info = render(p, a + k, sec[k])
            imgs = compose(L, FX, info)
            if p.get("shake"):
                imgs = shift_imgs(imgs, p["shake"])
            p2 = p2_layers(info, a + k, p2_intensity(name, k, len(fr), p), imgs)
            if p.get("dissolve"):
                both = dissolve({**imgs, **p2}, p["dissolve"])
                imgs = {n: both[n] for n in imgs}
                p2 = {n: both[n] for n in p2}
            frames.append({"ms": ms, "cels": imgs})
            frames_p2.append({"ms": ms, "cels": {**imgs, **p2}})
            flats.append(flatten(imgs, BASE_LAYERS))
            flats_p2.append(flatten({**imgs, **p2}, P2_ORDER))
            infos[name].append(info)
        tags.append((name, a, len(frames) - 1))
        print("rendered", name, len(fr))
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    preview(flats, os.path.join(ART, "previews", "boss_preview.png"))
    preview(flats_p2, os.path.join(ART, "previews", "boss_p2_preview.png"))
    c = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
    c.alpha_composite(flats[0])
    c.resize((W * 6, H * 6), Image.NEAREST).save(os.path.join(ART, "previews", "boss_closeup.png"))
    c = Image.new("RGBA", (W, H), (0x1c, 0x1a, 0x2c, 255))
    c.alpha_composite(flats_p2[0])
    c.resize((W * 6, H * 6), Image.NEAREST).save(os.path.join(ART, "previews", "boss_p2_closeup.png"))
    if only:
        return
    # ---------------- meta
    def rect(tag, k):
        inf = infos[tag][k]
        return bbox(inf["blade"] | inf["smear"], pad=1)

    def glint(tag, k):
        j = infos[tag][k]["j"]
        q = weapon_point(j["grip"], j["wang"], BLADE["end"] - 8, 1.5, j["wflip"])
        return [int(round(q[0])), int(round(q[1]))]
    idle_core = set()
    im = frames[0]["cels"]
    for n in ("Legs", "Body", "FrontArm"):
        src = im[n].load()
        idle_core |= {(x, y) for y in range(H) for x in range(W) if src[x, y][3]}
    hb = bbox(idle_core, pad=0)
    top = int(NEUTRAL["Hd"][1] - 12)  # helm crown (horns excluded)
    hb = [hb[0] + 4, top, hb[2] - 8, H - top]
    cast_tip = infos["cast"][5]["tip"]
    meta = {
        "frame": [W, H], "anchor": [AX, H], "hurtbox": hb,
        "attacks": {
            "combo": {"active": [2, 6, 10], "rects": {str(k): rect("combo", k) for k in (2, 6, 10)}},
            "thrust": {"active": [3], "rects": {"3": rect("thrust", 3)}},
            "leap": {"active": [5], "rects": {"5": rect("leap", 5)}},
            "spin": {"active": [3, 4, 5], "rects": {str(k): rect("spin", k) for k in (3, 4, 5)}},
            "eruption": {"active": [3], "rects": {"3": rect("eruption", 3)}},
        },
        "cast_point": [int(round(cast_tip[0])), int(round(cast_tip[1]))],
        "eruption_point": [ERUPT_X, GROUND - 1],
        "telegraph": {"combo": {"9": glint("combo", 9), "1": glint("combo", 1)},
                      "thrust": {"2": glint("thrust", 2)}, "spin": {"2": glint("spin", 2)},
                      "leap": {"3": glint("leap", 3)}},
    }
    # VFX pivots (frame coords, facing left) for the game's effect sprites
    rw = meta["attacks"]["combo"]["rects"]["10"]
    tj = infos["thrust"][3]["j"]
    ttip = infos["thrust"][3]["tip"]
    meta["body"] = {
        "arc_down": [int(round(v)) for v in infos["combo"][2]["j"]["Ns"]],
        "arc_up": [int(round(v)) for v in infos["combo"][6]["j"]["Ns"]],
        "arc_wide": [rw[0] + 132, rw[1] + rw[3] // 2 - 2],
        "spin": list(SPIN_C),
        "thrust": [int(round(v)) for v in tj["grip"]],
    }
    meta["thrust_angle_deg"] = int(round(math.degrees(math.atan2(ttip[1] - tj["grip"][1], tj["grip"][0] - ttip[0]))))
    hit_check(frames, tags, meta)
    with open(os.path.join(asebuild.ASSETS, "boss_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps(meta))
    if "--preview" not in sys.argv:
        asebuild.build("boss", W, H, BASE_LAYERS, frames, tags)
        asebuild.build("boss_p2", W, H, P2_ORDER, frames_p2, tags)


if __name__ == "__main__":
    main()
