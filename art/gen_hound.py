#!/usr/bin/env python3
"""Mid-boss generator -- "Gravetusk, the Rootbound Hound" (huge ash-grey wolf-boar, Pale-Root grafted).

    python3 art/gen_hound.py              full build: hound + hound_p2 + fx_root_spike + fx_bite (+ meta, previews)
    python3 art/gen_hound.py --preview    previews only (no Aseprite)
    python3 art/gen_hound.py --only idle,bite --preview   quick iteration on some tags

Outputs
    art/hound.aseprite, assets/hound.png/.json            phase 1
    art/hound_p2.aseprite, assets/hound_p2.png/.json      phase 2 (same frames/tags: burning roots + embers)
    assets/hound_meta.json                                  meta (shared by both sheets)
    art/fx_root_spike.aseprite, assets/fx_root_spike.*     24x64, 8 frames, pivot bottom (tag root_spike)
    art/fx_bite.aseprite, assets/fx_bite.*                 48x32, 4 frames (tag bite)
    art/previews/hound.png, hound_p2.png (3x, one row per tag), hound_hitbox.png, hound_closeup.png,
    fx_hound.png

Method (same family as gen_boss.py): every body part is a mask with a per-pixel surface normal
(domes, capsules, bevelled plates).  Fur is shaded from the lit normal plus a *clump field* aligned
to the fur flow direction, so shading bands break into shingled fur clumps instead of noise;
silhouette edges get tapered tufts pointing along the flow.  Roots are tapered gold tubes with a
glowing core, partly buried under fur clumps so they read as grafted *through* the hide.  Poses are
hand-keyed joints (rump R, withers S, head Hd + angle, four feet) with 2-bone IK legs.  Faces RIGHT.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

W, H = 160, 96
GROUND = 95
AX = 78  # anchor x (body centre)

# =========================================================================== palette
HEX = {
    "OUT": "#08070c",
    # ash fur: violet-black shadow -> warm pale ash
    "F0": "#131118", "F1": "#231f28", "F2": "#37313a", "F3": "#514a4d", "F4": "#766d69", "F5": "#a49a8b",
    # bone / tusk / claw
    "B0": "#2a211d", "B1": "#54463b", "B2": "#8a7863", "B3": "#c2b294", "B4": "#ebe1c6",
    # Pale-Root gold (bark shadow -> gilded)
    "G0": "#2e1a0c", "G1": "#5a3713", "G2": "#8e5f1a", "G3": "#c48b28", "G4": "#eabb4a", "G5": "#fce9a0",
    # phase-2 burning root
    "R0": "#3a120a", "R1": "#7a260c", "R2": "#b8440f", "R3": "#e8741c", "R4": "#ffaf3c", "R5": "#ffe391",
    # dead root (dull husk)
    "D0": "#1b1614", "D1": "#2c2420", "D2": "#40362f", "D3": "#554a3f", "D4": "#6a5d4f", "D5": "#807160",
    # dark skin: nose, lips, paw pads, ear inside
    "K0": "#120d11", "K1": "#241a20", "K2": "#3c2c32", "K3": "#5a4248",
    # mouth / gums
    "M0": "#1c0910", "M1": "#3e121d", "M2": "#6c2231", "M3": "#98404c",
    # glow
    "Y0": "#ff9a24", "Y1": "#ffc54e", "Y2": "#ffe98f", "Y3": "#fffbe6",
    # embers
    "E0": "#c2340e", "E1": "#e8541a",
    # dust
    "U0": "#2d2932", "U1": "#443e46", "U2": "#5f5760", "U3": "#80777c",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {
    "F": ["F0", "F1", "F2", "F3", "F4", "F5"],
    "B": ["B0", "B1", "B2", "B3", "B4"],
    "G": ["G0", "G1", "G2", "G3", "G4", "G5"],
    "R": ["R0", "R1", "R2", "R3", "R4", "R5"],
    "D": ["D0", "D1", "D2", "D3", "D4", "D5"],
    "K": ["K0", "K1", "K2", "K3"],
    "M": ["M0", "M1", "M2", "M3"],
}
SHINY = {"B": 0.93, "G": 0.9, "R": 0.9, "K": 0.97}
LIGHT = (-0.55, -0.68, 0.48)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)

BASE_LAYERS = ["FXBack", "FarLegs", "Tail", "Body", "Roots", "Head", "TailFront", "Glow", "FX"]
P2_LAYERS = ["Embers"]
P2_ORDER = ["FXBack", "FarLegs", "Tail", "Body", "Roots", "Head", "TailFront", "Glow", "Embers", "FX"]
SHADED = {"FarLegs", "Tail", "Body", "Roots", "Head", "TailFront"}


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


def tube(pts, r0, r1):
    """Tapered tube along a polyline.  Returns (normals, param) where param[p] = t along the tube."""
    n = len(pts) - 1
    nm, par = {}, {}
    best = {}
    for i, c in enumerate(pts):
        r = max(0.5, r0 + (r1 - r0) * i / n)
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


# =========================================================================== fur
def fur_clump(x, y, ang):
    """Shingled clump field aligned to the fur flow.  +: clump root (lit), -: clump tip (shadowed)."""
    dx, dy = math.cos(ang), math.sin(ang)
    u = x * dx + y * dy
    v = -x * dy + y * dx
    col = math.floor(v / 2.0)
    st = hash01(col, 0, 7) * 5.0
    uu = u + st
    row = math.floor(uu / 5.0)
    cu = (uu / 5.0) - row
    j = (hash01(col, row, 8) - 0.5) * 0.25
    return (0.5 - cu) * 0.8 + j


def tufts(mask, ang, spacing=3.2, lmin=2, lmax=4, seed=0, only=None):
    """Tapered fur tufts along the silhouette where the flow exits the mask.  Returns new pixels."""
    dx, dy = math.cos(ang), math.sin(ang)
    groups = {}
    for (x, y) in mask:
        if (x + int(round(dx * 1.4)), y + int(round(dy * 1.4))) in mask:
            continue
        if only and not only(x, y):
            continue
        v = -(x + .5) * dy + (y + .5) * dx
        u = (x + .5) * dx + (y + .5) * dy
        g = math.floor(v / spacing)
        if g not in groups or u > groups[g][0]:
            groups[g] = (u, (x, y))
    out = set()
    for g, (u, (x, y)) in groups.items():
        L = lmin + hash01(g, seed, 17) * (lmax - lmin + 0.99)
        wdt = 1.6 if L > 2.5 else 1.0
        for i in range(int(L) + 1):
            t = i / max(1.0, L)
            w = wdt * (1 - t)
            cx, cy = x + .5 + dx * i, y + .5 + dy * i
            for k in (-1, 0, 1):
                if abs(k) <= w + 0.2:
                    px, py = cx - dy * k, cy + dx * k
                    out.add((int(math.floor(px)), int(math.floor(py))))
    return out - mask


def spike_mask(base, tip, w0, bend=(0, 0)):
    """Curved tapered triangle (fur hackle / spur)."""
    mid = add(lerp(base, tip, 0.5), bend)
    pts = qbez(base, mid, tip, 10)
    m = set()
    for i, c in enumerate(pts):
        r = w0 * (1 - i / 10) + 0.3
        m |= mask_disc(c, max(0.55, r))
    return m


def fur_strokes(layer, seed, spacing=5, only=None):
    """Hand-drawn strand strokes: a short dark groove along the flow with a lit lip on its upper side."""
    cand = {}
    for p, e in layer.px.items():
        if e[0] != "F" or not isinstance(e[5], float) or e[3] is not None:
            continue
        if only is not None and p not in only:
            continue
        x, y = p
        if not all((x + a, y + b) in layer.px for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        ox = (y // spacing) * 2 % spacing
        key = ((x + ox) // spacing, y // spacing)
        h = hash01(x, y, seed)
        if key not in cand or h < cand[key][0]:
            cand[key] = (h, p)
    for h, p in cand.values():
        e = layer.px[p]
        ang = e[5] + (hash01(p[0], p[1], seed + 1) - 0.5) * 0.5
        d = (math.cos(ang), math.sin(ang))
        n = 3 + int(hash01(p[0], p[1], seed + 2) * 2.5)
        st = [(int(round(p[0] + d[0] * i)), int(round(p[1] + d[1] * i))) for i in range(n)]
        if not all(q in layer.px and layer.px[q][0] == "F" for q in st):
            continue
        layer.shift(st, -1)
        nrm = (d[1], -d[0]) if d[1] * 1 - d[0] * 0 >= 0 else (-d[1], d[0])
        nrm = (-abs(nrm[0]) if nrm[0] else 0, -abs(nrm[1]))  # towards upper-left (the light)
        lip = [(int(round(q[0] + nrm[0])), int(round(q[1] + nrm[1] - (1 if nrm[1] == 0 else 0)))) for q in st[:n - 1]]
        layer.shift([q for q in lip if q in layer.px and q not in st], 1)


# =========================================================================== layer buffer
class Layer:
    def __init__(self, name):
        self.name = name
        self.px = {}      # (x,y) -> [mat, n, bias, fixed, pid, extra]
        self.part_n = 0

    def paint(self, normals, mat, bias=0, ao=1, clip=None, extra=None):
        """extra: fur flow angle (radians, float) for fur, or dict p->t for roots."""
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
            ex = extra.get(p, 0.0) if isinstance(extra, dict) else extra
            self.px[p] = [mat, normals[p], bias, None, pid, ex]
        return new

    def fill(self, mask, color):
        self.part_n += 1
        for p in mask:
            if inb(*p):
                self.px[p] = [None, (0, 0, 1), 0, color, self.part_n, None]

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
    mat, n, bias, fixed, _, extra = e
    ramp = RAMP[mat]
    top = len(ramp) - 1
    if isinstance(fixed, tuple):
        return max(0, min(top, fixed[1] + (bias if bias < 0 else 0)))
    ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    v = 0.14 + 0.86 * max(0.0, ndl)
    f = v * (top - (1 if mat in SHINY else 0)) + 0.3
    if mat == "F" and isinstance(extra, float):
        f += fur_clump(x, y, extra) * 0.85
    if mat == "F":
        f += (58 - y) * 0.013  # sky-lit back, ground-shadowed belly and legs
    i = int(math.floor(f)) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - LIGHT[2]
        if rz > SHINY[mat] and bias >= 0:
            i = top
        else:
            i = min(i, top - 1)
    if mat == "F":
        i = min(i, top - (0 if bias >= 0 else 1))
    return max(0, min(top, i))


def render_layer(layer, root_ramp="G", dead=0.0, outline=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pix = img.load()
    col, lvl = {}, {}
    for (x, y), e in layer.px.items():
        if e[0] is None or isinstance(e[3], str):
            col[(x, y)] = e[3]
            continue
        i = level_of(e, x, y)
        mat = e[0]
        if mat == "G":
            mat = root_ramp
            if dead > 0 and isinstance(e[5], float) and e[5] > 1.0 - dead * 1.25:
                mat = "D"
        lvl[(x, y)] = i
        col[(x, y)] = RAMP[mat][min(i, len(RAMP[mat]) - 1)]
    if outline:
        for (x, y) in layer.px:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if not inb(*q) or q in layer.px:
                    continue
                e = layer.px[(x, y)]
                c = "OUT"
                if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 2:
                    c = RAMP[e[0]][1] if e[0] != "G" else RAMP[root_ramp][1]
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


# =========================================================================== rig
NEUTRAL = dict(
    R=(45, 50), S=(96, 45), Hd=(122, 59), ha=14, jaw=0,
    fn=(107, 95), ff=(95, 95), hn=(38, 95), hf=(50, 95),
    tail=((-8, -12), (-19, -16), (-24, -5)), tail_front=False,
    glow=1.0, eyes=1.0, ears=0, dead=0.0,
)


def P_(**kw):
    d = dict(NEUTRAL)
    d.update(kw)
    return d


def mv(p, dx, dy):
    for k in ("R", "S", "Hd"):
        p[k] = add(p[k], (dx, dy))
    return p


def joints(p):
    j = dict(p)
    R, S = p["R"], p["S"]
    d = sub(S, R)
    j["L"] = math.hypot(*d)
    j["ax"] = unit(d)
    j["pp"] = (-j["ax"][1], j["ax"][0])
    j["tilt"] = math.degrees(math.atan2(d[1], d[0]))
    return j


def T(j, base, ox, oy):
    ax, pp = j["ax"], j["pp"]
    return (base[0] + ax[0] * ox + pp[0] * oy, base[1] + ax[1] * ox + pp[1] * oy)


def back_v(s):
    """Local (perpendicular) offset of the back line at s in [0,1] along rump->withers."""
    return -(14.5 + 1.0 * s + 8.0 * s ** 2.2)


FLOW_BODY = math.radians(158)   # fur lies back and slightly down


# =========================================================================== parts
def draw_leg_front(Lr, j, side, bias):
    near = side == "n"
    sh = T(j, j["S"], 1 if near else -6, 10 if near else 8)
    foot = j["f" + side]
    wrist = j.get("wrist_" + side) or (foot[0] - 1, foot[1] - 8)
    el = j.get("elbow_" + side) or ik(sh, wrist, 18, 16, (-1, 0.15))
    fl = math.radians(112)
    Lr.paint(n_capsule(sh, el, 10.5 if near else 9.5, 7.0), "F", bias=bias, extra=fl)
    # forearm: feathered fur at the back
    fa = n_capsule(el, wrist, 7.0, 5.0)
    Lr.paint(fa, "F", bias=bias, extra=math.radians(100))
    feather = tufts(set(fa), math.radians(165), spacing=3.0, lmin=2, lmax=4, seed=3 + near,
                    only=lambda x, y: y < wrist[1] - 1)
    Lr.paint({q: (-0.6, 0.2, 0.75) for q in feather}, "F", bias=bias - 1, ao=0, extra=math.radians(165))
    # pastern + paw
    pc = (foot[0] + 2.5, foot[1] - 2.8)
    Lr.paint(n_capsule(wrist, pc, 5.0, 4.4), "F", bias=bias - 1, extra=math.radians(95))
    Lr.paint(n_dome(pc, 6.8, 3.6, tilt=(0, -0.2)), "F", bias=bias - 1, extra=math.radians(20))
    fwd = unit(sub(pc, wrist)) if near else unit(sub(pc, wrist))
    fwd = (1.0, 0.25) if abs(pc[1] - wrist[1]) > 3 else fwd
    claws = []
    for k in range(3):
        b = (pc[0] + 4.4 + k * 0.5, pc[1] - 1.6 + k * 1.7)
        claws += line(b, add(b, (2.5, 1.4)))
    Lr.fill([c for c in claws if c[1] <= GROUND], "B3" if near else "B2")
    Lr.decal([c for c in claws if c[1] <= GROUND][::3], "B4" if near else "B3")
    j["elbow_pt_" + side] = el
    j["paw_" + side] = pc
    return claws


def draw_leg_hind(Lr, j, side, bias):
    near = side == "n"
    hip = T(j, j["R"], 2 if near else -3, 6)
    foot = j["h" + side]
    hock = j.get("hock_" + side) or (foot[0] - 7, foot[1] - 13)
    kn = j.get("knee_" + side) or ik(hip, hock, 19, 17, (1, 0.25))
    Lr.paint(n_dome(add(hip, (1, 1)), 12 if near else 10.5, 12 if near else 10.5), "F", bias=bias,
             extra=math.radians(125))
    Lr.paint(n_capsule(hip, kn, 10.5 if near else 9, 6.0), "F", bias=bias, ao=0, extra=math.radians(120))
    shin = n_capsule(kn, hock, 6.2, 4.4)
    Lr.paint(shin, "F", bias=bias, extra=math.radians(125))
    feather = tufts(set(shin), math.radians(160), spacing=3.0, lmin=2, lmax=3, seed=7 + near,
                    only=lambda x, y: True)
    Lr.paint({q: (-0.6, 0.2, 0.75) for q in feather}, "F", bias=bias - 1, ao=0, extra=math.radians(160))
    pc = (foot[0] + 2.0, foot[1] - 2.8)
    Lr.paint(n_capsule(hock, pc, 4.6, 4.2), "F", bias=bias - 1, extra=math.radians(95))
    # bony hock spur
    Lr.paint(n_capsule(hock, add(hock, (-4, 1.5)), 1.6, 0.6), "B", bias=bias - (0 if near else 1), ao=0)
    Lr.paint(n_dome(pc, 6.2, 3.4, tilt=(0, -0.2)), "F", bias=bias - 1, extra=math.radians(20))
    claws = []
    for k in range(3):
        b = (pc[0] + 3.8 + k * 0.4, pc[1] - 1.2 + k * 1.6)
        claws += line(b, add(b, (2.0, 1.0)))
    Lr.fill([c for c in claws if c[1] <= GROUND], "B3" if near else "B2")
    j["knee_pt_" + side] = kn
    return claws


def draw_tail(Lr, j, sw):
    base = T(j, j["R"], -12, -6)
    c1, c2, tip = j["tail"]
    sw = sw or 0.0
    # keep the whip + its spur inside the frame: squash the x reach when it would cross the left edge
    minx = min(c1[0], c2[0], tip[0])
    if base[0] + minx < 11:
        k = (base[0] - 11) / -minx
        c1, c2, tip = [(c[0] * k, c[1] - (1 - k) * 8 * (i + 1) / 3) for i, c in enumerate((c1, c2, tip))]
    pts = bezier(base, add(base, c1), add(base, add(c2, (0, sw * 0.4))), add(base, add(tip, (sw * 0.3, sw))), 30)
    j["tail_pts"] = pts
    # fur sleeve at the root
    sleeve = n_capsule(pts[0], pts[8], 6.5, 4.0) if not j.get("tail_front") else {}
    # vertebrae beads
    beads = []
    for i in range(4, 29, 2):
        r = 4.4 - 2.8 * i / 30
        beads.append((i, r))
    for i, r in beads:
        c = pts[i]
        Lr.paint(n_dome(c, r + 0.3, r + 0.3), "B", bias=-1 if i % 4 else 0)
    # dorsal processes along the top (outer curve side)
    for i in range(6, 28, 4):
        a, b = pts[i], pts[i + 1]
        d = unit(sub(b, a))
        nrm = (d[1], -d[0])  # left normal (screen-up-ish on a left-going tail)
        if nrm[1] > 0:
            nrm = (-nrm[0], -nrm[1])
        r = 4.4 - 2.8 * i / 30
        sp = spike_mask(add(a, mul(nrm, r * 0.6)), add(a, add(mul(nrm, r + 3.2), mul(d, 1.8))), 1.3)
        Lr.paint({q: norm3(nrm[0], nrm[1], 0.8) for q in sp}, "B", bias=-1, ao=0)
    # root wrap spiralling down the tail
    wrap = []
    for i in range(6, 30):
        a, b = pts[i], pts[min(30, i + 1)]
        d = unit(sub(b, a))
        nrm = (-d[1], d[0])
        r = 3.9 - 2.6 * i / 30
        wrap.append(add(a, mul(nrm, math.sin(i * 0.75) * (r + 0.2))))
    wn, wp = tube(wrap, 1.4, 0.9)
    Lr.paint(wn, "G", ao=0, extra={q: 0.55 + 0.45 * t for q, t in wp.items()})
    # barbed root spur at the tip
    tp = pts[-1]
    d = unit(sub(pts[-1], pts[-4]))
    nrm = (-d[1], d[0])
    spurs = []
    for k, (ang, ln) in enumerate(((0, 7), (-40, 5), (40, 5))):
        dd = rot(d, ang)
        tipp = add(tp, mul(dd, ln))
        m = spike_mask(tp, tipp, 1.7 if k == 0 else 1.2, bend=mul(nrm, 0.8 if k else 0))
        Lr.paint({q: norm3(-0.3, -0.5, 1) for q in m}, "G", bias=0 if k == 0 else -1, ao=0,
                 extra={q: 0.9 for q in m})
        spurs.append(tipp)
    Lr.paint(sleeve, "F", bias=-1, extra=FLOW_BODY + math.radians(20))
    ts = tufts(set(sleeve), math.atan2(*reversed(unit(sub(pts[10], pts[0])))), spacing=2.6, lmin=2, lmax=4, seed=21)
    Lr.paint({q: (-0.4, -0.2, 0.8) for q in ts}, "F", bias=-1, ao=0, extra=FLOW_BODY)
    j["tail_tip"] = tp
    j["tail_spurs"] = spurs
    return pts


def draw_body(L, j, sec):
    Bd = L["Body"]
    R, S, Lb = j["R"], j["S"], j["L"]
    tilt = math.radians(j["tilt"])
    flow = FLOW_BODY + tilt
    # --- torso hull
    top = [T(j, R, s * Lb, back_v(s)) for s in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    hull = [T(j, R, -9, -9)] + top + [T(j, S, 10, -14), T(j, S, 16, 0), T(j, S, 12, 14), T(j, S, 2, 20),
                                       T(j, R, Lb * 0.62, 14.5), T(j, R, Lb * 0.38, 12), T(j, R, 10, 13),
                                       T(j, R, -6, 11)]
    torso = poly_mask(hull)
    Bd.paint(n_plate(torso, bevel=9, tilt=(0.0, -0.1), strength=1.4,
                     fold=lambda x, y: (0.0, 0.25 * math.sin((x - R[0]) * 0.18))), "F", extra=flow)
    # belly fringe
    fr = tufts(torso, math.radians(112) + tilt, spacing=3.0, lmin=2, lmax=5, seed=1,
               only=lambda x, y: (x, y + 3) not in torso and x < S[0] + 6)
    Bd.paint({q: (0.1, 0.6, 0.7) for q in fr}, "F", bias=-1, ao=0, extra=math.radians(112) + tilt)
    # --- rump
    Bd.paint(n_dome(add(R, (-1, -1)), 16.5, 15.5, tilt=(0.0, -0.05)), "F", extra=flow + 0.2)
    # --- near haunch/hind leg (in front of body)
    draw_leg_hind(Bd, j, "n", 0)
    # --- shoulder hump
    sc = T(j, S, -1, -3)
    Bd.paint(n_dome(sc, 19, 20, flat=0.95, tilt=(0.05, 0.0)), "F", extra=math.radians(128) + tilt)
    # --- neck ruff / mane: shaggy mass joining shoulder and head
    hb = add(j["Hd"], rot((-7, 2), j["ha"]))
    mane_pts = qbez(T(j, S, 4, -8), lerp(T(j, S, 4, -8), hb, 0.5), hb, 8)
    mane = set()
    for i, c in enumerate(mane_pts):
        mane |= mask_disc(add(c, (0, 2)), 13 - i * 0.35, 13.5 - i * 0.3)
    chest = mask_disc(T(j, S, 9, 9), 11.5, 11.5)
    mane |= chest
    mflow = math.radians(118) + tilt * 0.5
    Bd.paint(n_plate(mane, bevel=8, tilt=(0.1, -0.05), strength=1.5), "F", bias=-1, extra=mflow)
    mt = tufts(mane, mflow, spacing=3.0, lmin=3, lmax=7, seed=2 + int(sec.get("mane", 0) > 0.5),
               only=lambda x, y: y > S[1] - 6)
    Bd.paint({q: (0.2, 0.6, 0.7) for q in mt}, "F", bias=-1, ao=0, extra=mflow)
    # --- hackle crest: ragged dark spikes raking back off the withers and up the neck
    c0 = T(j, R, 0.78 * Lb, back_v(0.78) + 3)
    c1 = T(j, S, 2, back_v(1.0) - 1)
    c2 = add(hb, rot((2, -10), j["ha"] * 0.5))
    crest = qbez(c0, c1, c2, 16)
    for k in range(8):
        t = k / 7
        base = crest[int(t * 16)]
        ln = (6 + 8 * math.sin(math.pi * min(1.0, t * 1.15))) * (1 + j.get("flare", 0) * 0.25)
        ln += (hash01(k, 2, 19) - 0.5) * 3
        d = unit(rot((-0.75 - t * 0.5, -1.0), j["tilt"] * (1 - t * 0.5) + sec.get("mane", 0) * 3 +
                     (hash01(k, 1, 19) - 0.5) * 14))
        tip = add(base, mul(d, ln))
        m = spike_mask(add(base, (0, 2)), tip, 2.7, bend=rot((-1.4, 1.4), j["tilt"]))
        Bd.paint({q: norm3(-0.4, -0.75, 0.6) for q in m}, "F", bias=-1 if k % 2 else 0, ao=1,
                 extra=math.atan2(d[1], d[0]) + math.pi)
    # --- near front leg (in front of chest)
    claws = draw_leg_front(Bd, j, "n", 0)
    fur_strokes(Bd, 101)
    j["body_mask"] = set(Bd.px)
    j["torso_mask"] = torso | mask_disc(sc, 19, 21)
    return claws


def draw_roots(L, j, glow_fx, phase):
    """Pale-Root grafts: dorsal root spikes, a root 'spine', ribs of root diving through the flank."""
    Rt, Bd = L["Roots"], L["Body"]
    R, Lb = j["R"], j["L"]
    flare = j.get("flare", 0.0)
    cores, tips = [], []

    def wound(c, r):
        ring = [q for q in mask_disc(c, r + 1.1) if q not in mask_disc(c, r - 0.4)]
        Bd.decal(ring, ("K", 0), only_on=("F",))
        Bd.decal([q for q in ring if hash01(q[0], q[1], 5) > 0.75], ("M", 1), only_on=("F",))

    def gnarl(rp, length, seed):
        """Bark grooves: skewed dark rings every few px along the root."""
        g = [q for q, t in rp.items() if q in Rt.px and ((t * length + q[0] * 0.35) % 3.6) < 0.9
             and hash01(q[0], q[1], seed) > 0.25]
        Rt.shift(g, -1)

    def veins(pts, t0, t1, on=3, off=2):
        """Glowing bark cracks along the centreline (drawn into the Glow layer)."""
        n = len(pts) - 1
        cl = polyline(pts)
        m = len(cl)
        for i, q in enumerate(cl):
            if (i + int(hash01(int(pts[0][0]), 0, 3) * 5)) % (on + off) < on:
                cores.append((q, t0 + (t1 - t0) * i / max(1, m - 1)))

    def seg_paint(pts, r0, r1, t0, t1, keep, bias=0):
        rn, rp = tube(pts, r0, r1)
        m = {q: n for q, n in rn.items() if any(a <= rp[q] <= b for a, b in keep)}
        Rt.paint(m, "G", bias=bias, extra={q: t0 + (t1 - t0) * rp[q] for q in m})
        n = len(pts) - 1
        gnarl({q: rp[q] for q in m}, math.hypot(*sub(pts[-1], pts[0])) * 1.1, 41)
        for a, b in keep:
            veins(pts[int(a * n):int(b * n) + 1], t0 + (t1 - t0) * a, t0 + (t1 - t0) * b)
        for a, b in keep:  # wounds where the root enters / leaves the hide
            for t in (a, b):
                if 0.02 < t < 0.98:
                    wound(pts[int(round(t * n))], r0 + (r1 - r0) * t)
        return m
    # spine root: runs along the backbone, sinking in and out of the hide
    sp = [T(j, R, s * Lb, back_v(s) + 3.4) for s in [0.04 + 0.96 * i / 24 for i in range(25)]]
    seg_paint(sp, 2.6, 2.2, 0.0, 0.3, ((0.0, 0.3), (0.4, 0.66), (0.76, 1.0)))
    # rib roots
    for k, s_ in enumerate((0.36, 0.53, 0.7)):
        a = T(j, R, s_ * Lb, back_v(s_) + 5)
        b = T(j, R, s_ * Lb - 5, back_v(s_) * 0.2 + 2)
        c = T(j, R, s_ * Lb - 12 + k * 2, 13.5 - k)
        pts = qbez(a, b, c, 16)
        seg_paint(pts, 2.0, 1.3, 0.3, 0.8, ((0.0, 0.42), (0.62, 0.92)))
    # dorsal root spikes (tallest over the withers), curling back
    for k, s_ in enumerate((0.16, 0.33, 0.5, 0.65, 0.79)):
        base = T(j, R, s_ * Lb, back_v(s_) + 3.0)
        ln = (9 + 12 * s_ ** 1.1) * (1 + flare * 0.5) + (hash01(k, 3, 5) - 0.5) * 3
        d = unit(rot((-0.6, -1.0), j["tilt"] + (hash01(k, 1, 9) - 0.5) * 20 - flare * 8))
        tip = add(base, mul(d, ln))
        mid = add(lerp(base, tip, 0.5), rot((-ln * 0.28, ln * 0.05), j["tilt"]))
        pts = qbez(base, mid, tip, 14)
        rn, rp = tube(pts, 1.6 + s_ * 0.9, 0.4)
        Rt.paint(rn, "G", ao=1, extra={q: 0.45 + 0.55 * t for q, t in rp.items()})
        gnarl(rp, ln, 42 + k)
        if k in (1, 3):  # a thorn off some of them
            tb = pts[6]
            tt = add(tb, mul(unit(rot(d, 60)), 3.5 + s_ * 2))
            tn, tp_ = tube(qbez(tb, lerp(tb, tt, 0.5), tt, 5), 1.1, 0.45)
            Rt.paint(tn, "G", bias=-1, ao=0, extra={q: 0.8 for q in tn})
        wound(base, 1.6 + s_ * 0.9)
        tips.append(tip)
        veins(pts[2:12], 0.5, 0.95, on=2, off=2)
    j["root_tips"] = tips
    j["root_mask"] = set(Rt.px)
    return cores, tips


def draw_head(L, j):
    Hl = L["Head"]
    Hc, ha, jaw = j["Hd"], j["ha"], j["jaw"]
    HINGE = (-1.0, 4.0)
    HS = 1.26

    def hp(ox, oy):
        return add(Hc, rot((ox * HS, oy * HS), ha))

    def jp(ox, oy):
        return hp(*add(HINGE, rot(sub((ox, oy), HINGE), jaw)))
    fflow = math.radians(ha + 185)
    # far tusk (behind everything on the head)
    tusk_pts_far = bezier(jp(12, 5), jp(16, 2), jp(17.5, -3), jp(14.5, -5.5), 12)
    tn, tp = tube(tusk_pts_far, 1.8, 0.5)
    Hl.paint(tn, "B", bias=-1)
    # far ear
    fe = poly_mask([hp(-6, -8), hp(-14, -14.5), hp(-9, -6)])
    Hl.paint({q: norm3(-0.2, -0.4, 1) for q in fe}, "F", bias=-2, ao=0, extra=fflow)
    # lower jaw
    jm = poly_mask([jp(-5, 2.5), jp(8, 4.5), jp(19, 4.5), jp(20, 7), jp(11, 9.5), jp(-2, 9.5)])
    if jaw > 6:
        mouth = poly_mask([hp(2, 3), hp(21, 3), jp(20, 5.5), jp(4, 6)])
        Hl.fill(mouth, "M1")
        Hl.decal([q for q in mouth if hash01(q[0], q[1], 3) > 0.7], "M2")
        tongue = poly_mask([jp(4, 5.5), jp(15, 5.5), jp(13, 7.5), jp(4, 8)])
        Hl.paint(n_plate(tongue, bevel=1.5, tilt=(0, -0.3)), "M", ao=0)
    jn = n_plate(jm, bevel=2.5, tilt=(0.0, 0.35), strength=1.2)
    Hl.paint(jn, "F", bias=-1, extra=fflow)
    jt = tufts(jm, math.radians(ha + jaw + 150), spacing=2.6, lmin=2, lmax=4, seed=31)
    Hl.paint({q: (0, 0.6, 0.7) for q in jt}, "F", bias=-1, ao=0, extra=math.radians(ha + jaw + 150))
    # skull with cheek ruff
    sk = mask_disc(Hc, 11, 9.5)
    Hl.paint(n_dome(Hc, 11, 9.5, tilt=(0.05, 0.0)), "F", extra=fflow)
    ruff = tufts(sk, math.radians(ha + 150), spacing=2.8, lmin=3, lmax=5, seed=33,
                 only=lambda x, y: (sub((x, y), Hc)[0] * math.cos(math.radians(ha)) +
                                    sub((x, y), Hc)[1] * math.sin(math.radians(ha))) < 2)
    Hl.paint({q: (-0.3, 0.3, 0.8) for q in ruff}, "F", bias=0, ao=0, extra=math.radians(ha + 150))
    # snout (heavy boar-like muzzle)
    sn = poly_mask([hp(2, -7.5), hp(13, -6.5), hp(21, -4.5), hp(24.5, -1), hp(24.5, 3), hp(21, 4.5),
                    hp(8, 4.5), hp(1, 3)])
    Hl.paint(n_plate(sn, bevel=3.5, tilt=(-0.15, -0.3), strength=1.3), "F", extra=fflow)
    # upper lip line and fangs
    lip = [hp(x, 3.6) for x in range(6, 22)]
    Hl.decal([(int(q[0]), int(q[1])) for q in lip], ("K", 1))
    Hl.fill(line(hp(18.3, 3.8), hp(18.6, 5.6)), "B3")  # snarling canine, always bared
    if jaw > 6:
        for fx_ in (18.5, 12):
            a = hp(fx_, 4.0)
            Hl.fill(line(a, hp(fx_ + 0.6, 6.3)), "B3")
        for fx_ in (16, 10):
            a = jp(fx_, 5.2)
            Hl.fill(line(a, jp(fx_ + 0.4, 3.5)), "B2")
    # nose pad
    nz = mask_disc(hp(23.3, -0.8), 2.3, 2.4)
    Hl.paint(n_dome(hp(23.3, -0.8), 2.3, 2.4), "K", ao=0)
    Hl.decal([(int(hp(24.2, 0.3)[0]), int(hp(24.2, 0.3)[1]))], "K0")
    # heavy brow ridge
    br = poly_mask([hp(-2, -9.8), hp(6, -9.5), hp(12, -6.8), hp(11.5, -4.8), hp(4, -5.8), hp(-1, -6)])
    Hl.paint(n_plate(br, bevel=2, tilt=(-0.1, -0.55), strength=1.0), "F", ao=1, extra=fflow)
    # eye socket (shadow under the brow)
    sock = [hp(5, -4.2), hp(6, -4.2), hp(7, -4.2), hp(8, -4.2), hp(9, -4.2), hp(5, -3.2), hp(9.5, -3.4),
            hp(6, -2.5), hp(8, -2.4)]
    Hl.decal([(int(q[0]), int(q[1])) for q in sock], ("F", 0))
    eyes = [hp(6.8, -3.6), hp(5.8, -3.6), hp(7.8, -3.4)]
    eyes = [(int(q[0]), int(q[1])) for q in eyes]
    j["eye"] = eyes[0]
    # scar across the muzzle
    Hl.decal([(int(q[0]), int(q[1])) for q in polyline([hp(10, -6.5), hp(13, -3), hp(15, 0)])], ("F", 1))
    # near ear, laid back (pinned flatter when snarling)
    e = j.get("ears", 0)
    ear = poly_mask([hp(-3, -8), hp(-11 - e * 3, -17 + e * 4), hp(-10, -9.5), hp(-7.5, -4.5)])
    Hl.paint(n_plate(ear, bevel=1.5, tilt=(-0.2, -0.4)), "F", bias=0, ao=1, extra=fflow)
    Hl.decal(poly_mask([hp(-4.5, -7.5), hp(-9.5 - e * 2.5, -14.5 + e * 3.5), hp(-8.5, -8.5)]), ("K", 2))
    Hl.decal([(int(hp(-9.5 - e * 2, -14 + e * 3)[0]), int(hp(-9.5 - e * 2, -14 + e * 3)[1]))], ("F", 1))  # notch
    # near tusk (big, from the lower jaw, curling up past the muzzle)
    tusk_pts = bezier(jp(13.5, 6.5), jp(19.5, 4), jp(21.5, -3), jp(17, -6.5), 14)
    tn, tp = tube(tusk_pts, 2.5, 0.5)
    Hl.paint(tn, "B", ao=1)
    for i in (4, 7):
        q = tusk_pts[i]
        Hl.decal([(int(q[0]), int(q[1])), (int(q[0]) + 1, int(q[1]))], ("B", 1))
    j["tusk_tip"] = tusk_pts[-1]
    j["snout_tip"] = hp(25, 0)
    j["jaw_tip"] = jp(20, 8)
    fur_strokes(Hl, 202, spacing=6)
    j["head_mask"] = set(Hl.px)
    return eyes


def draw_whips(Lr, j, whips, cores, tips):
    """Root whips torn out of the back for the sweep: (s along the spine, c1, c2, tip) in frame coords."""
    for k, (s_, c1, c2, tip) in enumerate(whips):
        base = T(j, j["R"], s_ * j["L"], back_v(s_) + 3)
        pts = bezier(base, c1, c2, tip, 36)
        pts = [q for q in pts]
        rn, rp = tube(pts, 2.8 - k * 0.4, 0.7)
        rn = {q: n for q, n in rn.items() if q[1] <= GROUND}
        Lr.paint(rn, "G", bias=-k, extra={q: 0.4 + 0.6 * rp[q] for q in rn})
        for i in range(8, 34, 7):  # thorns
            a, b = pts[i], pts[i + 1]
            d = unit(sub(b, a))
            nrm = (d[1], -d[0])
            tt = add(a, add(mul(nrm, 3.5), mul(d, 2)))
            tn, _ = tube(qbez(a, lerp(a, tt, 0.5), tt, 4), 1.1, 0.4)
            Lr.paint({q: n for q, n in tn.items() if q[1] <= GROUND}, "G", bias=-1, ao=0, extra={q: 0.9 for q in tn})
        for i, q in enumerate(polyline(pts)):
            if i % 4 < 2 and q[1] <= GROUND:
                cores.append((q, 0.5 + 0.5 * i / 60))
        tips.append(pts[-1])
    j["root_mask"] = j["root_mask"] | set(Lr.px)
    j["whip_mask"] = set(Lr.px)
    j["whip_low"] = {q for q in Lr.px if q[1] >= GROUND - 24}


# =========================================================================== FX
def smear_color(age, edge_d):
    if age < 0.2:
        return "Y3" if edge_d < 2.5 else "Y2"
    if age < 0.45:
        return "Y2" if edge_d < 2 else "Y1"
    if age < 0.7:
        return "Y1" if edge_d < 2 else "Y0"
    return "G4" if edge_d < 2 else "G3"


def fx_bite(FX, info, j, fi, strength):
    """Twin jaw crescents snapping shut in front of the muzzle + speed streaks."""
    tx, ty = j["snout_tip"]
    cx, cy = tx - 9, ty + 3
    pts = set()
    for y in range(int(cy - 16), int(cy + 17)):
        for x in range(int(cx - 6), int(cx + 18)):
            dx, dy = x + .5 - cx, y + .5 - cy
            r = math.hypot(dx * 0.85, dy)
            th = math.degrees(math.atan2(dy, dx))
            for sgn in (-1, 1):
                t0, t1 = (-105, -8) if sgn < 0 else (8, 105)
                if not (t0 <= th <= t1):
                    continue
                R = 9 * strength + 5
                if R - 3.2 <= r <= R:
                    age = (abs(th) - 8) / 97
                    FX["FX"].put([(x, y)], smear_color(age, R - r))
                    pts.add((x, y))
    # speed streaks behind the head
    for k, oy in enumerate((-15, -12, 12, 15)):
        a = (tx - 34 - (k * 5) % 9, ty + oy)
        b = (tx - 16 - (k * 3) % 5, ty + oy)
        FX["FX"].put(line(a, b), "Y1" if k % 2 else "Y0")
        FX["FX"].put(line(b, add(b, (-3, 0))), "Y2")
    # glint on the tusk
    q = j["tusk_tip"]
    FX["FX"].put([(int(q[0]), int(q[1]))], "Y3")
    info["smear"] |= pts


def fx_glint(FX, info, j, fi, where, size=4):
    x, y = j[where] if isinstance(where, str) else where
    x, y = int(x), int(y)
    FX["FX"].put([(x, y)], "Y3")
    for k in range(1, size + 1):
        c = "Y3" if k == 1 else "Y2" if k < size else "Y1"
        FX["FX"].put([(x + k, y), (x - k, y)], c)
        if k <= size - 1:
            FX["FX"].put([(x, y + k), (x, y - k)], c)
    FX["FX"].put([(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)], "Y1")


def fx_dust(FX, info, j, fi, cx, spread, stage, front=True):
    gy = GROUND
    lay = FX["FX"] if front else FX["FXBack"]
    for k in range(7):
        dx = (k - 3) * spread * (1 + stage * 0.5)
        r = 3 + (k % 3) + stage * 1.5
        c = (cx + dx, gy - r * 0.6 - stage * 2)
        for q in mask_disc(c, r, r * 0.7):
            if q[1] > gy:
                continue
            if stage > 0 and hash01(q[0] // 2, q[1] // 2, 40 + stage) < 0.2 * stage:
                continue
            lit = (q[0] - c[0]) + (q[1] - c[1]) < -1
            lay.put([q], "U3" if lit else "U2" if (q[0] + q[1]) % 3 else "U1")
    for k in range(8):
        hx_ = hash01(k, 1, 44 + stage)
        FX["FX"].put([(int(cx + (hx_ - 0.5) * spread * 12), int(gy - 4 - hash01(k, 2, 44) * 10 - stage * 5))],
                     "U3" if k % 2 else "U2")


def fx_hsweep(FX, info, j, fi, c, rin, rout, k, th0, th1, bright=1.0):
    """Low elliptical root-lash band (seen from the side).  sin(th)>0 = in front of the body."""
    cx, cy = c
    lo, hi = min(th0, th1), max(th0, th1)
    pts = set()
    for y in range(int(cy - rout * k) - 3, int(cy + rout * k) + 4):
        for x in range(int(cx - rout) - 2, int(cx + rout) + 3):
            if y > GROUND:
                continue
            dx, dy = x + .5 - cx, (y + .5 - cy) / k
            r = math.hypot(dx, dy)
            if not (rin <= r <= rout):
                continue
            th = math.degrees(math.atan2(dy, dx))
            while th < lo:
                th += 360
            if th > hi:
                continue
            t = (th - th0) / (th1 - th0)
            age = 1 - t
            edge_d = rout - r
            if age > 0.55 and edge_d > 2 and int(edge_d / 3) % 2 == 1:
                continue
            if age > 0.85 and edge_d > 2:
                continue
            if bright < 1 and int(edge_d / 2) % 3 != 0:
                continue
            col = smear_color(age, edge_d)
            if r < rin + 3 and age > 0.3:
                col = "G3" if age > 0.6 else "Y0"
            front = math.sin(math.radians(th)) > 0
            (FX["FX"] if front else FX["FXBack"]).put([(x, y)], col)
            if age < 0.6 and bright >= 1:
                pts.add((x, y))
    info["smear"] |= pts


def fx_lash(FX, info, j, fi, x0, x1, y, amp, bright):
    """Root tendrils whipping along the ground (drawn as FX so they overlap everything)."""
    pts = set()
    for k in range(3):
        yy = y - k * 3
        prev = None
        for x in range(int(min(x0, x1)), int(max(x0, x1)) + 1):
            t = (x - x0) / (x1 - x0)
            yy2 = yy + math.sin(t * 9 + k * 2 + fi) * amp * (0.4 + t)
            q = (x, int(round(yy2)))
            seg = line(prev, q) if prev else [q]
            prev = q
            for s in seg:
                if s[1] <= GROUND:
                    c = "G2" if k else "G3"
                    if bright and (s[0] + k * 3) % 5 < 2:
                        c = "Y1" if t > 0.6 else "Y0"
                    FX["FX"].put([s], c)
                    FX["FX"].put([(s[0], s[1] + 1)], "G1") if s[1] + 1 <= GROUND else None
                    pts.add(s)
    info["smear"] |= pts


def fx_howl(FX, info, j, fi, r, strength):
    """Sound rings from the maw + root-light rays behind the back."""
    tx, ty = j["snout_tip"]
    cx, cy = tx + 1, ty - 1
    for rr in (r, r * 0.62):
        for a in range(-110, 10, 2):
            q = (int(cx + math.cos(math.radians(a)) * rr), int(cy + math.sin(math.radians(a)) * rr * 0.9))
            if hash01(q[0] // 2, q[1] // 2, 71) < 0.3 + 0.7 * strength:
                FX["FX"].put([q, (q[0] + 1, q[1])], "Y2" if rr == r else "Y1")
    bx, by = T(j, j["R"], j["L"] * 0.7, -26)
    for k in range(14):
        a = math.radians(200 + k * 11 + fi * 5)
        r0 = 12 + (k % 3) * 3
        r1 = r0 + 8 + (k % 2) * 8 * strength
        FX["FXBack"].put(line((bx + math.cos(a) * r0, by + math.sin(a) * r0),
                              (bx + math.cos(a) * r1, by + math.sin(a) * r1)), "Y1" if k % 2 else "Y0")
    for k in range(10):
        FX["FX"].put([(int(bx + (hash01(k, fi, 72) - 0.5) * 60), int(by - hash01(k, fi, 73) * 20 + 10))],
                     "Y2" if k % 3 == 0 else "Y1")


def fx_impact(FX, info, j, fi, cx, stage):
    gy = GROUND
    if stage == 0:
        for y in range(gy - 6, gy + 1):
            for x in range(int(cx) - 22, int(cx) + 23):
                d = ((x + .5 - cx) / 21) ** 2 + ((y + .5 - gy) / 5.5) ** 2
                if 0.72 <= d <= 1.0:
                    FX["FX"].put([(x, y)], "Y2" if d > 0.86 else "Y1")
        for k in range(9):
            a = math.radians(200 + k * 17)
            r0, r1 = 4 + k % 3, 10 + (k * 7) % 8
            FX["FX"].put(line((cx + math.cos(a) * r0, gy - 1 + math.sin(a) * r0),
                              (cx + math.cos(a) * r1, gy - 1 + math.sin(a) * r1)), "Y2" if k % 2 else "Y1")
    fx_dust(FX, info, j, fi, cx, 7, stage)


def fx_speed(FX, info, j, fi, x0, x1, ys):
    for i, y in enumerate(ys):
        a = x0 + (i * 7) % 11
        b = x1 - (i * 5) % 9
        FX["FXBack"].put(line((a, y), (b, y)), "U3" if i % 2 else "U2")


FX_FUNCS = {"bite": fx_bite, "glint": fx_glint, "dust": fx_dust, "hsweep": fx_hsweep, "lash": fx_lash,
            "howl": fx_howl, "impact": fx_impact, "speed": fx_speed}


# =========================================================================== render
def render(p, frame_i, sec, phase=1):
    j = joints(p)
    L = {n: Layer(n) for n in SHADED}
    FX = {n: FXLayer(n) for n in ("FXBack", "Glow", "FX")}
    info = {"smear": set()}
    # far legs (darker, behind)
    far_claws = draw_leg_hind(L["FarLegs"], j, "f", -2)
    far_claws += draw_leg_front(L["FarLegs"], j, "f", -2)
    fur_strokes(L["FarLegs"], 303)
    draw_tail(L["TailFront" if p.get("tail_front") else "Tail"], j, sec.get("tail", 0))
    draw_body(L, j, sec)
    cores, tips = draw_roots(L, j, FX["Glow"], phase)
    eyes = draw_head(L, j)
    if p.get("whips"):
        draw_whips(L["TailFront"], j, p["whips"], cores, tips)
    g = p.get("glow", 1.0)
    dead = p.get("dead", 0.0)
    # root core glow (veins of light inside the gold), killed as the roots die
    for k, (c, t) in enumerate(cores):
        if dead > 0 and t > 1.0 - dead * 1.25:
            continue
        q = (int(c[0]), int(c[1]))
        if not (q in j["root_mask"]):
            continue
        if hash01(q[0], q[1], 11) < 0.45 * (2 - g):
            continue
        hot = g > 1.15 or phase == 2
        FX["Glow"].put([q], ("Y2" if hot else "Y1") if hash01(q[0], q[1], 12) > 0.3 else ("Y3" if hot else "Y2"))
        if g > 1.3:
            FX["Glow"].put([(q[0], q[1] - 1)], "Y1")
    for k, tp in enumerate(tips):
        if dead > 0.2:
            continue
        q = (int(round(tp[0])), int(round(tp[1])))
        FX["Glow"].put([q], "Y3" if g >= 1.0 else "Y2")
        if g > 1.25 or phase == 2:
            FX["Glow"].put([(q[0], q[1] - 1)], "Y2")
    for tp in j.get("tail_spurs", [])[:1]:
        if dead < 0.3:
            FX["Glow"].put([(int(round(tp[0])), int(round(tp[1])))], "Y2")
    # eyes
    e = p.get("eyes", 1.0) * (1.25 if phase == 2 else 1.0)
    if e > 0.05:
        ex, ey = eyes[0]
        if e < 0.6:
            FX["Glow"].put(eyes[:1], "G3")
        else:
            FX["Glow"].put(eyes[1:], "Y2" if e > 0.9 else "Y0")
            FX["Glow"].put(eyes[:1], "Y3" if e > 0.9 else "Y1")
            FX["Glow"].put([(ex, ey + 1)], "Y0")
        if e > 1.1:
            FX["Glow"].put([(ex + 2, ey), (ex - 1, ey)], "Y1")
            FX["Glow"].put([(ex, ey - 1), (ex + 1, ey - 1)], "Y1")
            # trailing wisp
            for i in range(int(3 * e)):
                FX["Glow"].put([(ex - 2 - i, ey - (i // 2))], "Y1" if i < 2 else "Y0")
    for f in p.get("fx", []):
        FX_FUNCS[f[0]](FX, info, j, frame_i, *f[1:])
    info["j"] = j
    info["eyes"] = eyes
    info["cores"] = cores
    return L, FX, info


def root_rim(imgs, j, phase):
    """Warm the fur right next to the roots (the gold light spilling onto the hide)."""
    body = imgs["Body"].load()
    rm = j["root_mask"]
    warm = {}
    for (x, y) in rm:
        for a in (-2, 2):
            for b in (-2, 0, 2):
                q = (x + a, y + b)
                if inb(*q) and q not in rm and body[q][3]:
                    warm[q] = 1
    for q in warm:
        c = body[q]
        lum = c[0] + c[1] + c[2]
        if lum > 3 * 0x50 and hash01(q[0], q[1], 13) > 0.35:
            body[q] = RGBA["G3" if phase == 1 else "R3"]
        elif lum > 3 * 0x38 and hash01(q[0], q[1], 14) > 0.6:
            body[q] = RGBA["G2" if phase == 1 else "R2"]


def compose(L, FX, info, phase, dead):
    imgs = {}
    for n in BASE_LAYERS:
        if n in L:
            imgs[n] = render_layer(L[n], root_ramp="R" if phase == 2 else "G", dead=dead)
        else:
            imgs[n] = FX[n].image()
    if dead < 0.5:
        root_rim(imgs, info["j"], phase)
    return imgs


def p2_embers(info, fi, imgs, k, dead):
    """Phase-2: ember pixels streaming up from the burning roots + glowing fur tips."""
    out = FXLayer("Embers")
    if k <= 0.01:
        return out.image()
    j = info["j"]
    srcs = list(j["root_tips"]) + [c for c, _ in info["cores"][::2]]
    for t in range(int(26 * k)):
        s = srcs[int(hash01(t, 5, 87) * len(srcs))]
        age = ((fi * 0.29 + hash01(t, 6, 88)) % 1.0)
        x = s[0] - age * 10 + math.sin(age * 7 + t) * 2.5
        y = s[1] - 2 - age * 30
        c = "Y2" if age < 0.2 else "Y1" if age < 0.45 else "Y0" if age < 0.7 else "E1" if age < 0.85 else "E0"
        out.put([(int(x), int(y))], c)
        if age < 0.3:
            out.put([(int(x) + 1, int(y) + 1)], "Y0")
    # glowing fur tips: topmost pixels of hackles/mane columns near the roots
    body = imgs["Body"].load()
    tops = {}
    for x in range(W):
        for y in range(H):
            if body[x, y][3] and body[x, y] != RGBA["OUT"]:
                tops[x] = y
                break
    for x, y in tops.items():
        if hash01(x, fi // 3, 89) < 0.22 * k and y < j["S"][1]:
            out.put([(x, y)], "Y0" if hash01(x, 1, 90) > 0.5 else "E1")
    return out.image()


# =========================================================================== secondary motion
def secondary(frames, loop):
    state = {"tail": 0.0, "mane": 0.0}
    vel = {"tail": 0.0, "mane": 0.0}
    res = []
    for ps in range(2 if loop else 1):
        prev = frames[-1][1] if loop else frames[0][1]
        res = []
        for ms, p in frames:
            dr = (p["R"][1] - prev["R"][1]) + 0.5 * (p["R"][0] - prev["R"][0])
            ds = p["S"][0] - prev["S"][0]
            for k, drive, gain, stiff in (("tail", dr, 1.3, 0.45), ("mane", ds, 0.4, 0.5)):
                target = -gain * drive
                vel[k] = vel[k] * 0.45 + (target - state[k]) * stiff
                state[k] = max(-6.0, min(6.0, state[k] + vel[k]))
            res.append(dict(state))
            prev = p
    return res


# =========================================================================== animation keyframes
# Keys were authored against a rig 3px longer in the body; Q_ maps those absolute joints onto the current rig.
_SHIFT = {"R": (3, 0), "S": (-2, 0), "Hd": (-4, -1), "hn": (3, 0), "hf": (3, 0), "hock_n": (3, 0), "hock_f": (3, 0),
          "knee_n": (3, 0), "knee_f": (3, 0), "fn": (-2, 0), "ff": (-2, 0), "wrist_n": (-2, 0), "wrist_f": (-2, 0),
          "elbow_n": (-2, 0), "elbow_f": (-2, 0)}


def Q_(**kw):
    for k, d in _SHIFT.items():
        if k in kw and kw[k] is not None:
            kw[k] = add(kw[k], d)
    return P_(**kw)

def anim_idle():
    fr = []
    for i in range(6):
        b = (0, 0, 1, 1, 1, 0)[i]
        h = (0, 1, 1, 2, 1, 1)[i]
        fr.append((170, Q_(S=(98, 45 + b), Hd=(126, 60 + h), R=(42, 50 + (i in (3,))),
                           glow=(1.0, 1.1, 1.2, 1.3, 1.2, 1.1)[i],
                           tail=((-8, -12), (-19, -16 + (0, 1, 2, 2, 1, 0)[i]), (-24, -5 + (0, 1, 2, 3, 2, 1)[i])))))
    return fr


def anim_prowl():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        st = 10
        lift_a = max(0.0, s) * 6
        lift_b = max(0.0, -s) * 6
        fn = (107 + st * c, GROUND - lift_a)
        hf = (50 + st * c, GROUND - lift_a)
        ff = (95 - st * c, GROUND - lift_b)
        hn = (38 - st * c, GROUND - lift_b)
        bob = 1.0 * abs(c)
        p = Q_(R=(42, 51 + bob), S=(98, 47 + bob), Hd=(127 - c, 64 + bob + (i % 4 == 1)), ha=18,
               fn=fn, ff=ff, hn=hn, hf=hf, ears=1,
               tail=((-8, -11), (-19, -14 + c), (-24, -3 + 2 * s)))
        # flexed wrists on lifted forepaws
        if lift_a > 1:
            p["wrist_n"] = (fn[0] + lift_a * 0.4, fn[1] - 8)
            p["fn"] = (fn[0] - 1.5, fn[1] + 1)
        if lift_b > 1:
            p["wrist_f"] = (ff[0] + lift_b * 0.4, ff[1] - 8)
            p["ff"] = (ff[0] - 1.5, ff[1] + 1)
        fr.append((115, p))
    return fr


def anim_bite():
    snap = dict(R=(48, 52), S=(104, 50), Hd=(129, 71), ha=22, fn=(118, 95), ff=(104, 95), hn=(40, 95), hf=(54, 95),
                ears=1, tail=((-9, -11), (-20, -2), (-28, -10)))
    return [
        (110, Q_(R=(41, 51), S=(96, 48), Hd=(123, 63), ha=18, jaw=4, ears=1)),
        (140, Q_(R=(37, 52), S=(91, 45), Hd=(113, 50), ha=-8, jaw=18, fn=(105, 95), hn=(36, 95), ears=1,
                 tail=((-8, -12), (-18, -4), (-24, -14)))),
        (260, Q_(R=(36, 53), S=(89, 44), Hd=(110, 47), ha=-14, jaw=26, fn=(105, 95), hn=(36, 95), ears=1,
                 eyes=1.6, tail=((-8, -13), (-18, -6), (-23, -17)),
                 fx=[("glint", "tusk_tip", 4)])),
        (60, Q_(**snap, jaw=30, eyes=1.6, fx=[("bite", 0.7)])),
        (90, Q_(**snap, jaw=0, eyes=1.4, fx=[("bite", 1.0)])),
        (160, Q_(**dict(snap, Hd=(134, 71)), jaw=0)),
        (140, Q_(R=(45, 51), S=(102, 47), Hd=(130, 64), ha=18, fn=(112, 95), ff=(100, 95), hn=(39, 95))),
        (140, Q_(R=(43, 50), S=(99, 45), Hd=(127, 61), ha=15)),
    ]


def anim_pounce():
    crouch = dict(R=(40, 58), S=(96, 55), Hd=(124, 68), ha=16, ears=1, fn=(110, 95), ff=(98, 95), hn=(34, 95),
                  hf=(46, 95), tail=((-9, -6), (-19, 4), (-27, -2)))
    return [
        (120, Q_(**crouch)),
        (300, Q_(**dict(crouch, R=(38, 60), S=(94, 58), Hd=(121, 71), hn=(32, 95), hf=(44, 95)), jaw=8, eyes=1.6,
                 fx=[("glint", "tusk_tip", 4)])),
        # launch: hind legs extend, body pitches up
        (80, Q_(R=(44, 52), S=(99, 34), Hd=(126, 40), ha=-5, jaw=16, fn=(118, 74), ff=(110, 78),
                hn=(22, 95), hf=(32, 95), hock_n=(26, 84), hock_f=(36, 84),
                wrist_n=(118, 66), wrist_f=(110, 70), tail=((-10, 2), (-22, 12), (-30, 16)),
                fx=[("dust", 30, 5, 0, False)])),
        # airborne: full stretch
        (90, Q_(R=(40, 40), S=(98, 32), Hd=(128, 36), ha=2, jaw=22, fn=(138, 70), ff=(131, 74),
                hn=(10, 62), hf=(18, 66), hock_n=(18, 56), hock_f=(26, 58),
                wrist_n=(133, 62), wrist_f=(126, 66), ears=1, tail=((-10, 0), (-22, 6), (-32, 4)),
                fx=[("speed", 2, 40, (30, 44, 58))])),
        # descending: forepaws reaching down, claws out
        (90, Q_(R=(40, 38), S=(100, 44), Hd=(130, 54), ha=22, jaw=26, fn=(130, 88), ff=(122, 88),
                hn=(22, 68), hf=(30, 72), hock_n=(26, 60), hock_f=(34, 62),
                wrist_n=(126, 78), wrist_f=(118, 78), ears=1, eyes=1.4, tail=((-10, -8), (-22, -10), (-30, -18)))),
        # land impact
        (70, Q_(R=(46, 50), S=(104, 58), Hd=(133, 71), ha=26, jaw=4, fn=(126, 95), ff=(116, 95),
                hn=(40, 95), hf=(52, 95), ears=1, eyes=1.2, tail=((-9, -14), (-20, -12), (-26, -22)),
                fx=[("impact", 128, 0)])),
        (160, Q_(R=(44, 55), S=(102, 57), Hd=(131, 69), ha=22, fn=(126, 95), ff=(116, 95),
                 hn=(40, 95), hf=(52, 95), ears=1, tail=((-9, -10), (-20, -4), (-27, -10)),
                 fx=[("dust", 124, 7, 1)])),
        (140, Q_(R=(43, 53), S=(100, 50), Hd=(129, 64), ha=18, fn=(118, 95), ff=(106, 95),
                 hn=(40, 95), hf=(52, 95))),
        (120, Q_(R=(42, 51), S=(99, 46), Hd=(127, 61), ha=15, fn=(110, 95), ff=(98, 95))),
        (120, Q_()),
    ]


SWEEP_C = (80, 86)


def anim_sweep():
    coil = dict(R=(46, 44), S=(98, 52), Hd=(122, 70), ha=30, ears=1, fn=(106, 95), ff=(96, 95),
                hn=(44, 95), hf=(56, 95), tail=((-4, -12), (-8, -24), (2, -30)))
    low = dict(R=(40, 56), S=(98, 55), Hd=(128, 71), ha=24, ears=1, fn=(114, 95), ff=(100, 95),
               hn=(32, 95), hf=(46, 95))
    return [
        (130, Q_(**coil, glow=1.2, flare=0.4)),
        (280, Q_(**dict(coil, R=(47, 42), tail=((-2, -13), (-4, -26), (6, -32))), glow=1.5, eyes=1.6, flare=0.8,
                 fx=[("glint", "eye", 3)])),
        # tail cracks down behind; two roots tear free of the back
        (70, Q_(**low, glow=1.5, tail=((-12, 8), (-24, 26), (-30, 38)),
                whips=[(0.65, (84, 6), (120, 4), (140, 22)), (0.5, (70, 4), (98, 0), (112, 12))],
                fx=[("hsweep", SWEEP_C, 30, 78, 0.16, 110, 185, 0.5)])),
        # the lash: roots whip forward and down along the ground, tail scythes behind
        (60, Q_(**dict(low, R=(38, 58)), glow=1.6, tail=((-12, 12), (-22, 34), (-34, 40)),
                whips=[(0.65, (100, 10), (150, 40), (156, 92)), (0.5, (84, 6), (132, 50), (140, 93))],
                fx=[("hsweep", SWEEP_C, 30, 78, 0.16, 110, 215), ("lash", 3, 44, 92, 1.5, True)])),
        (70, Q_(**dict(low, R=(38, 58)), glow=1.4, tail=((-12, 14), (-22, 36), (-34, 42)),
                whips=[(0.65, (104, 30), (126, 92), (158, 91)), (0.5, (90, 34), (108, 93), (146, 93))],
                fx=[("hsweep", SWEEP_C, 30, 78, 0.16, -10, 90), ("hsweep", SWEEP_C, 30, 78, 0.16, 185, 260, 0.5),
                    ("lash", 104, 157, 92, 1.5, True), ("dust", 130, 6, 0)])),
        (120, Q_(**low, glow=1.2, tail=((-10, 10), (-22, 20), (-32, 26)),
                 whips=[(0.65, (96, 20), (112, 60), (124, 80)), (0.5, (82, 20), (96, 50), (104, 66))],
                 fx=[("hsweep", SWEEP_C, 34, 76, 0.16, 20, 110, 0.4), ("dust", 120, 9, 1)])),
        (140, Q_(R=(41, 53), S=(98, 51), Hd=(127, 66), ha=20, tail=((-10, -4), (-20, 10), (-28, 6)),
                 whips=[(0.65, (86, 16), (96, 18), (102, 24))])),
        (140, Q_(R=(42, 51), S=(98, 47), Hd=(126, 62), ha=16, tail=((-9, -8), (-20, 7), (-27, 0)))),
        (140, Q_()),
    ]


def anim_howl():
    rear = dict(R=(40, 60), S=(88, 37), Hd=(107, 29), ha=-40, jaw=30, ears=1, fn=(110, 70), ff=(102, 73),
                wrist_n=(107, 62), wrist_f=(99, 65), hn=(40, 95), hf=(54, 95), hock_n=(32, 84), hock_f=(46, 84),
                tail=((-10, 6), (-20, 16), (-30, 20)))
    fr = [
        (140, Q_(R=(42, 51), S=(97, 50), Hd=(124, 68), ha=28, ears=1, glow=1.1)),
        (140, Q_(R=(40, 54), S=(94, 44), Hd=(118, 50), ha=-10, jaw=8, fn=(104, 88), ff=(96, 90),
                 wrist_n=(104, 80), wrist_f=(96, 82), glow=1.2, tail=((-10, 2), (-20, 12), (-28, 14)))),
        (120, Q_(**dict(rear, S=(90, 40), Hd=(110, 33), ha=-32, jaw=18), glow=1.4)),
    ]
    for k in range(5):
        fr.append((200, Q_(**rear, glow=1.6, flare=1.0 if k % 2 == 0 else 0.8, eyes=2.0,
                           shake=(1 if k % 2 == 0 else -1),
                           fx=[("howl", 9 + k * 5, 1.0 - k * 0.15)])))
    fr.append((160, Q_(R=(41, 54), S=(95, 42), Hd=(120, 46), ha=-5, jaw=6, fn=(108, 86), ff=(100, 88),
                       wrist_n=(108, 78), wrist_f=(100, 80), glow=1.2)))
    fr.append((180, Q_(R=(42, 52), S=(99, 49), Hd=(127, 64), ha=18, fn=(110, 95), ff=(98, 95), glow=1.1,
                       fx=[("dust", 104, 6, 0)])))
    return fr


def anim_charge():
    """Rotary gallop, head low, tusks forward."""
    base = dict(ha=30, ears=1, jaw=6, eyes=1.3)
    return [
        # gathered: all four feet under the body
        (75, Q_(**base, R=(46, 52), S=(100, 52), Hd=(130, 70), fn=(96, 92), ff=(88, 95), hn=(60, 95), hf=(68, 91),
                hock_n=(52, 84), hock_f=(60, 80), wrist_n=(98, 84), wrist_f=(90, 86),
                tail=((-10, -2), (-22, 2), (-32, -2)), fx=[("dust", 64, 4, 0, False)])),
        # hind push-off, fronts reaching
        (75, Q_(**base, R=(44, 46), S=(100, 44), Hd=(132, 63), fn=(134, 84), ff=(126, 88), hn=(24, 95), hf=(32, 93),
                hock_n=(30, 86), hock_f=(38, 84), wrist_n=(128, 76), wrist_f=(120, 80),
                tail=((-10, 0), (-24, 0), (-34, -4)), fx=[("speed", 4, 50, (40, 56, 72))])),
        # full extension (suspension)
        (75, Q_(**base, R=(42, 44), S=(100, 45), Hd=(134, 62), fn=(140, 90), ff=(132, 93), hn=(14, 86), hf=(22, 88),
                hock_n=(22, 80), hock_f=(30, 80), wrist_n=(136, 82), wrist_f=(128, 85),
                tail=((-10, 2), (-24, 4), (-34, 2)), fx=[("speed", 2, 46, (44, 60, 76))])),
        # front landing, hinds swinging forward
        (75, Q_(**base, R=(44, 48), S=(102, 50), Hd=(134, 68), fn=(118, 95), ff=(126, 93), hn=(40, 86), hf=(48, 88),
                hock_n=(38, 76), hock_f=(46, 78), wrist_n=(118, 87), wrist_f=(126, 85),
                tail=((-10, -4), (-22, -2), (-32, -8)), fx=[("dust", 120, 4, 0)])),
    ]


def anim_stagger():
    kneel = dict(R=(42, 50), S=(98, 62), Hd=(124, 78), ha=24, ears=1, jaw=12, eyes=0.8,
                 fn=(120, 95), ff=(110, 95), wrist_n=(108, 93), wrist_f=(98, 93), elbow_n=(94, 82), elbow_f=(86, 84),
                 hn=(38, 95), hf=(50, 95), tail=((-9, -2), (-18, 12), (-26, 10)))
    return [
        (120, Q_(R=(40, 49), S=(94, 40), Hd=(116, 46), ha=-14, jaw=22, ears=1, eyes=1.3, fn=(104, 92),
                 wrist_n=(104, 84), tail=((-9, -12), (-20, -4), (-28, -12)))),
        (140, Q_(R=(41, 50), S=(96, 54), Hd=(121, 68), ha=18, jaw=14, ears=1, fn=(114, 95), ff=(104, 95),
                 wrist_n=(106, 90), wrist_f=(98, 90), elbow_n=(96, 76), elbow_f=(88, 78),
                 tail=((-9, -6), (-19, 8), (-27, 4)))),
        (320, Q_(**kneel)),
        (220, Q_(**dict(kneel, S=(98, 60), Hd=(124, 75), ha=20, jaw=6))),
    ]


def anim_death():
    kneel = dict(R=(42, 51), S=(98, 62), Hd=(124, 78), ha=24, ears=1, jaw=12,
                 fn=(120, 95), ff=(110, 95), wrist_n=(108, 93), wrist_f=(98, 93), elbow_n=(94, 82), elbow_f=(86, 84),
                 hn=(38, 95), hf=(50, 95), tail=((-9, -2), (-18, 12), (-26, 10)))
    lie = dict(R=(40, 70), S=(96, 66), Hd=(126, 82), ha=12, ears=1, jaw=8,
               fn=(122, 95), ff=(112, 95), wrist_n=(110, 94), wrist_f=(100, 94), elbow_n=(92, 86), elbow_f=(84, 88),
               hn=(62, 95), hf=(70, 95), hock_n=(42, 93), hock_f=(50, 93), knee_n=(56, 82), knee_f=(62, 84),
               tail=((-10, 8), (-20, 18), (-30, 22)))
    fr = [
        (150, Q_(R=(40, 49), S=(93, 38), Hd=(114, 40), ha=-30, jaw=26, ears=1, eyes=1.5, fn=(104, 90),
                 wrist_n=(104, 82), glow=1.4, tail=((-9, -12), (-20, -6), (-28, -14)))),
        (160, Q_(R=(41, 50), S=(96, 54), Hd=(121, 68), ha=18, jaw=14, ears=1, fn=(114, 95), ff=(104, 95),
                 wrist_n=(106, 90), wrist_f=(98, 90), elbow_n=(96, 76), elbow_f=(88, 78), glow=1.2,
                 tail=((-9, -6), (-19, 8), (-27, 4)))),
        (180, Q_(**kneel, glow=1.1)),
        (200, Q_(**dict(lie, R=(40, 62), S=(97, 65), Hd=(125, 80)), eyes=0.9, glow=1.0,
                 fx=[("dust", 50, 7, 0)])),
        (240, Q_(**lie, eyes=0.8, glow=0.9, fx=[("dust", 90, 9, 1)])),
    ]
    for k, dd in enumerate((0.15, 0.35, 0.55, 0.8, 1.0)):
        fr.append(((240, 260, 280, 320, 800)[k],
                   Q_(**dict(lie, Hd=(126, 83), jaw=4), eyes=max(0.0, 0.7 - dd), glow=max(0.3, 0.9 - dd), dead=dd)))
    return fr


TAGDEFS = [("idle", anim_idle), ("prowl", anim_prowl), ("bite", anim_bite), ("pounce", anim_pounce),
           ("sweep", anim_sweep), ("howl", anim_howl), ("charge", anim_charge), ("stagger", anim_stagger),
           ("death", anim_death)]
COUNTS = {"idle": 6, "prowl": 8, "bite": 8, "pounce": 10, "sweep": 9, "howl": 10, "charge": 4, "stagger": 4,
          "death": 10}
LOOPS = ("idle", "prowl", "charge")


# =========================================================================== output helpers
def flatten(imgs, order):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
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


def preview_rows(rows, path, w=W, h=H, scale=3, bg=(92, 92, 98, 255), label=True):
    """rows: list of (tag, [images]).  One row per tag, mid-grey background."""
    maxn = max(len(r[1]) for r in rows)
    pad = 2
    lab = 12 if label else 0
    sheet = Image.new("RGBA", ((maxn * (w + pad)) * scale, len(rows) * (h + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    for r, (tag, ims) in enumerate(rows):
        y0 = r * (h + pad + lab) * scale
        if label:
            d.text((4, y0 + 4), f"{tag} ({len(ims)})", fill=(230, 230, 230, 255))
        for i, im in enumerate(ims):
            fr = Image.new("RGBA", (w, h), bg)
            fr.alpha_composite(im)
            sheet.alpha_composite(fr.resize((w * scale, h * scale), Image.NEAREST),
                                  (i * (w + pad) * scale, y0 + lab * scale))
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
    s = 3
    items = []
    for t, d in meta["attacks"].items():
        a, b = d["active"]
        for k in range(a, b + 1):
            items.append((t, k, d["rects"][str(k)], d["hit"]))
    cols = 4
    rows_n = (len(items) + cols) // cols + 1
    sheet = Image.new("RGBA", (cols * (W + 2) * s, rows_n * (H + 14) * s), (30, 30, 36, 255))
    for i, (t, k, r, hr) in enumerate(items + [("idle", 0, None, None)]):
        fr = Image.new("RGBA", (W, H), (92, 92, 98, 255))
        fr.alpha_composite(flats[start[t] + k])
        d = ImageDraw.Draw(fr)
        hb = meta["hurtbox"]
        if t == "idle":
            d.rectangle([hb[0], hb[1], hb[0] + hb[2] - 1, hb[1] + hb[3] - 1], outline=(80, 255, 120, 255))
            ax, ay = meta["anchor"]
            d.line([ax - 3, ay - 1, ax + 3, ay - 1], fill=(255, 255, 255, 255))
            d.line([ax, ay - 5, ax, ay - 1], fill=(255, 255, 255, 255))
        else:
            d.rectangle([hr[0], hr[1], hr[0] + hr[2] - 1, hr[1] + hr[3] - 1], outline=(255, 170, 60, 255))
            d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 50, 50, 255))
            # a 10x26 player standing inside the rect's far edge
            px = min(W - PLAYER[0], max(0, r[0] + r[2] - PLAYER[0] - 2)) if t != "sweep" else r[0] + 2
            py = H - PLAYER[1]
            hit = not (r[0] + r[2] <= px or px + PLAYER[0] <= r[0] or r[1] + r[3] <= py or H <= r[1])
            d.rectangle([px, py, px + PLAYER[0] - 1, H - 1], outline=(80, 200, 255, 255))
        tg = meta.get("telegraph", {}).get(t)
        if tg and False:
            pass
        col = Image.new("RGBA", (W, H + 14), (30, 30, 36, 255))
        ImageDraw.Draw(col).text((2, 1), f"{t} f{k}" if t != "idle" else "hurtbox + anchor",
                                 fill=(230, 230, 230, 255))
        col.paste(fr, (0, 14))
        sheet.alpha_composite(col.resize((W * s, (H + 14) * s), Image.NEAREST),
                              ((i % cols) * (W + 2) * s, (i // cols) * (H + 14) * s))
    # telegraph frames with their glint point
    j = len(items) + 1
    for t, tg in meta["telegraph"].items():
        fr = Image.new("RGBA", (W, H), (92, 92, 98, 255))
        fr.alpha_composite(flats[start[t] + tg["frame"]])
        d = ImageDraw.Draw(fr)
        x, y = tg["at"]
        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(0, 255, 255, 255))
        col = Image.new("RGBA", (W, H + 14), (30, 30, 36, 255))
        ImageDraw.Draw(col).text((2, 1), f"telegraph {t} f{tg['frame']}", fill=(230, 230, 230, 255))
        col.paste(fr, (0, 14))
        if (j // cols) < rows_n:
            sheet.alpha_composite(col.resize((W * s, (H + 14) * s), Image.NEAREST),
                                  ((j % cols) * (W + 2) * s, (j // cols) * (H + 14) * s))
        j += 1
    sheet.save(path)


# =========================================================================== FX sheets
def fx_root_spike_frames():
    """24x64, 8 frames, pivot bottom: glow crack -> spike erupts -> retracts."""
    w, h = 24, 64
    gy = h - 1
    cx = 12
    heights = (0, 0, 22, 58, 60, 44, 24, 8)
    frames = []
    for i in range(8):
        back = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        spike = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bp, sp, gp = back.load(), spike.load(), glow.load()

        def put(pp, x, y, c):
            if 0 <= x < w and 0 <= y < h:
                pp[x, y] = RGBA[c]
        # ground crack glow (telegraph) frames 0-2, fading after
        crack_w = (4, 9, 10, 10, 9, 7, 5, 3)[i]
        cb = (1.0, 1.3, 1.2, 0.9, 0.7, 0.6, 0.4, 0.2)[i]
        for dx in range(-crack_w, crack_w + 1):
            x = cx + dx
            yy = gy - (1 if abs(dx) < crack_w * 0.5 else 0) - (1 if hash01(dx, 0, 3) > 0.7 else 0)
            c = "Y3" if abs(dx) < 2 and cb > 1 else "Y2" if abs(dx) < crack_w * 0.5 else "Y1" if cb > 0.5 else "Y0"
            put(gp, x, gy, c)
            if abs(dx) < crack_w * 0.6 and cb > 0.6:
                put(gp, x, yy, "Y0" if (x + i) % 2 else "Y1")
        if i <= 2:  # dark fissure under the glow + heat haze column (the telegraph)
            for dx in range(-crack_w - 1, crack_w + 2):
                if abs(dx) > crack_w - 1:
                    put(bp, cx + dx, gy, "OUT")
            for k in range(6 + i * 6):
                x = cx + int((hash01(k, i, 15) - 0.5) * crack_w * 1.6)
                y = gy - 1 - int(hash01(k, i, 16) ** 1.6 * (8 + i * 10))
                put(gp, x, y, "Y0" if k % 3 else "Y1")
        if i <= 1:  # pre-rise glow wisps
            for k in range(4 + i * 3):
                put(gp, cx + int((hash01(k, i, 5) - 0.5) * 12), gy - 2 - int(hash01(k, i, 6) * (6 + i * 8)),
                    "Y1" if k % 2 else "Y2")
        hgt = heights[i]
        if hgt > 0:
            # twisted root spike: two intertwined strands + a thorn
            top = gy - hgt
            m = {}
            for y in range(top, gy + 1):
                t = (y - top) / max(1, hgt)  # 0 tip .. 1 base
                half = 0.6 + t * 4.2 + (1.2 if t > 0.85 else 0)
                sway = math.sin(t * 3.2 + 0.4) * 1.3 * (1 - t)
                for x in range(int(cx - half + sway - 1), int(cx + half + sway + 2)):
                    dx = (x + .5 - (cx + sway)) / max(0.6, half)
                    if abs(dx) <= 1.0:
                        m[(x, y)] = (dx, t)
            for (x, y), (dx, t) in m.items():
                # strand twist: diagonal groove
                tw = ((y * 0.55 + dx * 3.0) % 4.0)
                lv = 3 if dx < -0.35 else 2 if dx < 0.35 else 1
                if tw < 0.9:
                    lv -= 1
                if dx < -0.55 and tw > 2.5:
                    lv = 4
                if t < 0.12:
                    lv = min(5, lv + 1)
                put(sp, x, y, "G%d" % max(0, lv))
            # thorns
            for k, (ty, sd) in enumerate(((0.35, -1), (0.6, 1), (0.78, -1))):
                y = int(top + ty * hgt)
                if hgt < 30 and k == 0:
                    continue
                half = 0.6 + ty * 4.2
                x0 = int(cx + sd * half)
                for s in range(5):
                    put(sp, x0 + sd * s, y - s, "G3" if s < 3 else "G4")
                    if s < 3:
                        put(sp, x0 + sd * s, y - s + 1, "G1")
            # outline
            for (x, y) in list(m.keys()) + []:
                pass
            src = spike.copy().load()
            for y in range(h):
                for x in range(w):
                    if src[x, y][3]:
                        continue
                    if any(0 <= x + a < w and 0 <= y + b < h and src[x + a, y + b][3]
                           for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        sp[x, y] = RGBA["OUT"]
            # glowing core veins + hot tip
            for y in range(top + 2, gy, 3):
                t = (y - top) / max(1, hgt)
                sway = math.sin(t * 3.2 + 0.4) * 1.3 * (1 - t)
                put(gp, int(cx + sway + 0.5), y, "Y1" if (y // 3) % 2 else "Y2")
            put(gp, cx + int(math.sin(0.4) * 1.3), top, "Y3")
            put(gp, cx + int(math.sin(0.4) * 1.3), top + 1, "Y2")
            # debris kicked up on eruption
            if i in (2, 3):
                for k in range(10):
                    dx = (hash01(k, i, 7) - 0.5) * 22
                    dy = hash01(k, i, 8) * (10 if i == 2 else 22)
                    c = "U2" if k % 3 else "U3"
                    put(bp, int(cx + dx), int(gy - 3 - dy), c)
                    put(bp, int(cx + dx) + 1, int(gy - 3 - dy), "U1")
            if i >= 5:  # crumbling as it retracts
                for k in range(6 + (i - 5) * 4):
                    x = int(cx + (hash01(k, i, 9) - 0.5) * 12)
                    y = int(top + hash01(k, i, 10) * hgt)
                    if src[min(w - 1, max(0, x)), y][3]:
                        sp[min(w - 1, max(0, x)), y] = (0, 0, 0, 0)
                    put(bp, x + (1 if k % 2 else -1) * 2, min(gy, y + 3), "G2" if k % 2 else "U2")
        frames.append({"ms": (110, 130, 50, 60, 140, 90, 80, 90)[i],
                       "cels": {"Back": back, "Spike": spike, "Glow": glow}})
    return frames


def fx_bite_frames():
    """48x32, 4 frames: jaw-snap crescents closing on a point (travelling right)."""
    w, h = 48, 32
    frames = []
    cx, cy = 30, 16
    for i in range(4):
        main = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        mp, cp = main.load(), core.load()
        R = (14, 11, 8, 10)[i]
        spread = (95, 60, 25, 10)[i]  # half-angle of each jaw arc
        thick = (3.5, 4, 3.5, 2)[i]
        for y in range(h):
            for x in range(w):
                dx, dy = x + .5 - cx, y + .5 - cy
                r = math.hypot(dx * 0.8, dy)
                th = math.degrees(math.atan2(dy, dx))
                for sg in (-1, 1):
                    a0 = sg * 12
                    a1 = sg * (12 + spread + 60)
                    lo, hi = min(a0, a1), max(a0, a1)
                    if not (lo <= th <= hi):
                        continue
                    if R - thick <= r <= R:
                        age = abs(th - a0) / abs(a1 - a0)
                        ed = R - r
                        if i == 3 and int(ed + x) % 2:
                            continue
                        c = smear_color(age * (1.3 if i > 1 else 1.0), ed)
                        mp[x, y] = RGBA[c]
        # teeth tips converging
        for sg in (-1, 1):
            for k in range(3):
                a = math.radians(sg * (20 + k * 22 + spread * 0.4))
                tx, ty = cx + math.cos(a) * (R - thick) / 0.8, cy + math.sin(a) * (R - thick)
                for s in range(3 if i < 3 else 1):
                    x, y = int(tx - math.cos(a) * s), int(ty - math.sin(a) * s)
                    if 0 <= x < w and 0 <= y < h:
                        cp[x, y] = RGBA["Y3" if s == 0 else "Y2"]
        if i == 2:  # snap flash
            for k in range(8):
                a = math.radians(k * 45)
                ln = 7 if k % 2 == 0 else 4
                for s in range(ln):
                    x, y = int(cx + 4 + math.cos(a) * s), int(cy + math.sin(a) * s)
                    if 0 <= x < w and 0 <= y < h:
                        cp[x, y] = RGBA["Y3" if s < 2 else "Y2"]
        # speed streaks trailing left
        for k, oy in enumerate((-5, 0, 5)):
            x1 = cx - 10 - k * 2 + i * 2
            x0 = x1 - (14 - i * 3)
            for x in range(max(0, x0), max(0, x1)):
                if (x + k) % 7 == 0:
                    continue
                if 0 <= cy + oy < h:
                    mp[x, cy + oy] = RGBA["Y1" if x > x1 - 4 else "Y0"]
        frames.append({"ms": (50, 50, 60, 80)[i], "cels": {"Arc": main, "Core": core}})
    return frames


# =========================================================================== main
def main():
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
            dead = p.get("dead", 0.0)
            L, FX, info = render(p, a + k, sec[k], phase=1)
            imgs = compose(L, FX, info, 1, dead)
            L2, FX2, info2 = render(p, a + k, sec[k], phase=2)
            imgs2 = compose(L2, FX2, info2, 2, dead)
            imgs2["Embers"] = p2_embers(info2, a + k, imgs2, max(0.0, 1.0 - dead * 1.5), dead)
            if p.get("shake"):
                imgs = shift_imgs(imgs, p["shake"])
                imgs2 = shift_imgs(imgs2, p["shake"])
            frames.append({"ms": ms, "cels": imgs})
            frames_p2.append({"ms": ms, "cels": imgs2})
            f1, f2 = flatten(imgs, BASE_LAYERS), flatten(imgs2, P2_ORDER)
            flats.append(f1); flats_p2.append(f2)
            r1.append(f1); r2.append(f2)
            infos[name].append(info)
        tags.append((name, a, len(frames) - 1))
        rows.append((name, r1)); rows2.append((name, r2))
        print("rendered", name, len(fr))
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    suffix = "" if not only else "_wip"
    preview_rows(rows, os.path.join(pv, f"hound{suffix}.png"))
    preview_rows(rows2, os.path.join(pv, f"hound_p2{suffix}.png"))
    c = Image.new("RGBA", (W * 2, H), (92, 92, 98, 255))
    c.alpha_composite(flats[0]); c.alpha_composite(flats_p2[0], (W, 0))
    c.resize((W * 2 * 5, H * 5), Image.NEAREST).save(os.path.join(pv, f"hound_closeup{suffix}.png"))
    if only:
        return

    # ---------------- meta
    def rect(tag, k, parts):
        inf = infos[tag][k]
        j = inf["j"]
        pts = set(inf["smear"])
        for pk in parts:
            pts |= j.get(pk, set())
        return bbox(pts, pad=1)

    def pt(q):
        return [int(round(q[0])), int(round(q[1]))]

    def reach_floor(r, floor_y=GROUND - 20):
        """Guarantee the rect reaches down into a standing player's body (10x26 on the floor)."""
        x, y, w_, h_ = r
        if y + h_ < floor_y:
            h_ = floor_y - y
        return [x, y, w_, h_]

    def attack(tag, a, b, parts, floor=True, extend=None):
        rs = {}
        for k in range(a, b + 1):
            r = rect(tag, k, parts)
            if extend:
                r = extend(r, k)
            rs[str(k)] = reach_floor(r) if floor else r
        return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}

    body_core = set()
    for n in ("Body",):
        src = frames[0]["cels"][n].load()
        body_core |= {(x, y) for y in range(H) for x in range(W) if src[x, y][3]}
    tb = infos["idle"][0]["j"]["torso_mask"]
    hb = bbox(tb, pad=0)
    hurt = [hb[0] + 2, hb[1] + 3, hb[2] - 4, GROUND - 14 - (hb[1] + 3)]
    head_j = infos["idle"][0]["j"]
    hh = bbox(head_j["head_mask"], pad=0)
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "hurtbox_head": [hh[0] + 2, hh[1] + 2, hh[2] - 4, hh[3] - 3],
        "attacks": {
            "bite": attack("bite", 3, 4, ("head_mask",)),
            "pounce": attack("pounce", 4, 5, ("head_mask",),
                             extend=lambda r, k: union_rect([r, bbox({(int(x), int(y)) for x, y in (
                                 infos["pounce"][k]["j"]["paw_n"], infos["pounce"][k]["j"]["paw_f"])}, pad=4)])),
            "sweep": attack("sweep", 3, 4, ("whip_low",)),
            "charge": attack("charge", 0, 3, ("head_mask",),
                             extend=lambda r, k: union_rect([r, bbox({(x, y) for (x, y) in
                                                                     infos["charge"][k]["j"]["torso_mask"]
                                                                     if x > infos["charge"][k]["j"]["S"][0] - 4})])),
        },
        "telegraph": {
            "bite": {"frame": 2, "at": pt(infos["bite"][2]["j"]["tusk_tip"])},
            "pounce": {"frame": 1, "at": pt(infos["pounce"][1]["j"]["tusk_tip"])},
            "sweep": {"frame": 1, "at": list(infos["sweep"][1]["eyes"][0])},
        },
        "spawn": {
            "howl": {"frame": 4, "at": [int(round(infos["howl"][4]["j"]["S"][0])), GROUND]},
        },
        "notes": "faces right; 'hit' = union of per-frame 'rects' over the inclusive active range; "
                 "charge is active on every frame (loop); howl spawns fx_root_spike (engine positions them); "
                 "telegraph 'at' = where to flash the glint the frame before the strike.",
    }
    hit_preview(flats, tags, meta, os.path.join(pv, "hound_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "hound_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k != "attacks"}))
    for t, d in meta["attacks"].items():
        print("attack", t, d["active"], d["hit"])

    # ---------------- fx sheets
    rs = fx_root_spike_frames()
    fb = fx_bite_frames()
    rsl = [flatten(f["cels"], ["Back", "Spike", "Glow"]) for f in rs]
    fbl = [flatten(f["cels"], ["Arc", "Core"]) for f in fb]
    s = 4
    sheet = Image.new("RGBA", (8 * 26 * s, (64 + 2 + 34) * s), (40, 40, 46, 255))
    for i, im in enumerate(rsl):
        fr = Image.new("RGBA", (24, 64), (92, 92, 98, 255)); fr.alpha_composite(im)
        sheet.alpha_composite(fr.resize((24 * s, 64 * s), Image.NEAREST), (i * 26 * s, 0))
    for i, im in enumerate(fbl):
        fr = Image.new("RGBA", (48, 32), (92, 92, 98, 255)); fr.alpha_composite(im)
        sheet.alpha_composite(fr.resize((48 * s, 32 * s), Image.NEAREST), (i * 50 * s, 66 * s))
    sheet.save(os.path.join(pv, "fx_hound.png"))

    if "--preview" not in sys.argv:
        asebuild.build("hound", W, H, BASE_LAYERS, frames, tags)
        asebuild.build("hound_p2", W, H, P2_ORDER, frames_p2, tags)
        asebuild.build("fx_root_spike", 24, 64, ["Back", "Spike", "Glow"], rs, [("root_spike", 0, 7)])
        asebuild.build("fx_bite", 48, 32, ["Arc", "Core"], fb, [("bite", 0, 3)])


if __name__ == "__main__":
    main()
