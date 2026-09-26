"""Sister Venn, the Last Kindling -- procedural rig (agent V).  Used by art/gen_venn.py.

Same family as gen_sovereign.py (read-only reference): every part is a mask with a per-pixel surface normal
(capsules, domes, bevelled cloth plates with animated fold fields, tapered tubes); a hue-shifted material ramp
is picked from the lit normal; sel-out outline; emissive parts (pale flame: blade, veil, halo, wing fire) are
flat colour on FX layers with stepped alpha.  One skeleton with fixed bone lengths drives every frame of every
phase, so proportions never drift.  Faces RIGHT.  Frame 192x128, anchor = (96, 122) = the hem on the floor.
"""
import math
from PIL import Image

W, H = 192, 128
AX, AY = 96, 122
FLOOR = 121          # last pixel row above the floor line

HEX = {
    "OUT": "#0a090e",
    # skin: young, pale, warm
    "P0": "#2c2230", "P1": "#55434e", "P2": "#8e7479", "P3": "#c6aba2", "P4": "#ecd9cb", "P5": "#fff6ec",
    # ivory robe
    "W0": "#1d1a26", "W1": "#3b3748", "W2": "#686375", "W3": "#a39daa", "W4": "#d7d1cf", "W5": "#f6f0e3",
    # ash grey (scapular, lining, sash)
    "A0": "#111016", "A1": "#211f27", "A2": "#35323c", "A3": "#4f4b56", "A4": "#6e6a75", "A5": "#928d98",
    # pale wood (the scythe)
    "B0": "#211b19", "B1": "#433731", "B2": "#6d5d4f", "B3": "#9c8a74", "B4": "#c9b89c", "B5": "#ece1c8",
    # ash-silver hair
    "H0": "#28262e", "H1": "#4a4752", "H2": "#78747f", "H3": "#a8a3ac", "H4": "#d3ced3", "H5": "#f2eef0",
    # charred root (phase-2 wings, root wraps)
    "C0": "#0c0909", "C1": "#1d1513", "C2": "#33231e", "C3": "#4d3328", "C4": "#6b4633", "C5": "#8c5d40",
    # pale gold thread
    "G0": "#3a2410", "G1": "#6a4518", "G2": "#9c6c24", "G3": "#cf9d3a", "G4": "#f0cd6a", "G5": "#fff0b8",
    # pale flame (emissive): white-gold
    "F0": "#a8501c", "F1": "#e08a2c", "F2": "#ffc158", "F3": "#ffe4a0", "F4": "#fff5d8", "L": "#ffffff",
    # embers
    "E0": "#6e1a0a", "E1": "#b83a10", "E2": "#ee7424",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
RAMP = {m: [f"{m}{i}" for i in range(6)] for m in "PWABHCG"}
SHINY = {"G": 0.9}
LIGHT = (-0.5, -0.72, 0.48)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)
LIGHT_P = (0.2, -0.55, 0.8)
_l = math.sqrt(sum(c * c for c in LIGHT_P)); LIGHT_P = tuple(c / _l for c in LIGHT_P)


# =========================================================================== geometry
def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def flerp(a, b, t): return a + (b - a) * t


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def dirv(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def norm3(x, y, z):
    l = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / l, y / l, z / l)


def hash01(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def ipt(p): return (int(math.floor(p[0])), int(math.floor(p[1])))


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
        for a, b, w in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.41), (1, -1, 1.41), (-1, 1, 1.41), (-1, -1, 1.41)):
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


def bbox(pts, pad=0):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    return [int(x0), int(y0), int(x1 - x0 + 1), int(y1 - y0 + 1)]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


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

    def erase(self, pts):
        for p in pts:
            self.px.pop(p, None)


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
    if mat in ("W", "A"):
        f += (70 - y) * 0.008        # light from above: the hem sinks into cool shadow
    if mat == "W":
        f += 0.7
    if mat == "P":
        f += 0.6
    if mat == "H":
        f += 0.4
    i = int(math.floor(f)) + bias
    if mat in SHINY:
        rz = 2 * ndl * n[2] - Lv[2]
        i = top if (rz > SHINY[mat] and bias >= 0) else min(i, top - 1)
    return max(0, min(top, i))


def render_layer(layer, outline="OUT"):
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
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if not inb(*q) or q in layer.px:
                    continue
                e = layer.px[(x, y)]
                c = outline
                if (a, b) in ((-1, 0), (0, -1)) and e[0] is not None and lvl.get((x, y), 0) >= len(RAMP[e[0]]) - 2:
                    c = RAMP[e[0]][1]   # sel-out: lit edges get a softer outline
                cur = pix[q]
                if cur[3] == 0 or c == outline:
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

    def drop(self, pts):
        for p in pts:
            self.px.pop(p, None)

    def image(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.px.items():
            pix[p] = c
        return img


def flame_tongues(F, edge_pts, up, fi, seed, length=3.0, cols=("F2", "F3", "F4"), density=0.55, a=255, lean=(0, 0)):
    """Little flickering tongues rising from a set of edge pixels (direction `up`, a unit vector)."""
    for (x, y) in edge_pts:
        if hash01(x, y, seed) > density:
            continue
        ln = length * (0.35 + 0.9 * hash01(x + fi * 7, y, seed + 1))
        n = max(1, int(round(ln)))
        wob = (hash01(x, fi, seed + 2) - 0.5) * 1.2
        for k in range(n):
            t = k / max(1, n - 1) if n > 1 else 0
            q = (x + up[0] * (k + 1) + lean[0] * k * k * 0.15 + wob * t, y + up[1] * (k + 1) + lean[1] * k * k * 0.15)
            c = cols[min(len(cols) - 1, int((1 - t) * (len(cols) - 1) + 0.5))] if k > 0 else cols[-1]
            F.put([q], c, a)


def edge_of(mask):
    return {q for q in mask if any((q[0] + a, q[1] + b) not in mask for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


# =========================================================================== rig
PIV = (96, 96)
REST = dict(Hd=(99.5, 65.0), Nk=(98.2, 70.6), Sn=(100.8, 73.4), Sf=(94.2, 73.0), Ch=(97.6, 78.0), Wa=(96.6, 89.0),
            Wr=(92.5, 76.5), Hc=(96.2, 62.4))
SL, BL = 60.0, 24.0            # scythe shaft length, blade length
L1N, L2N, L1F, L2F = 9.6, 9.2, 9.2, 8.8

NEUTRAL = dict(
    bob=0.0, lean=0.0, dx=0.0, crouch=0.0, stride=0.0, head=(0, 0), htilt=0.0,
    hn=(106, 92), hf=(92, 92), hn_dir=80, hf_dir=95, eln=(0.3, 1), elf=(-0.4, 1),
    scy=None, wind=0.0, lift=0.0,
    veil=1.0, eyes=0.0, halo=1.0, halo_broken=0.0, fire=0.0,
    wl=(264, 1.0, 0.9), wr=(-84, 1.0, 0.75), wsway=4.0, wings=None, lances=0.0,
    flask=None, flask_k=1.0, fx=(), dissolve=0.0, hood=0.0, keepveil=False,
)


def P_(**kw):
    d = dict(NEUTRAL)
    d.update(kw)
    return d


def joints(p, sec):
    lean, bob, ox = p["lean"], p["bob"], p["dx"]
    drop = 16.0 * p["crouch"]

    def X(q, k=1.0):
        r = rot((q[0] - PIV[0], q[1] - PIV[1]), lean * k)
        return (PIV[0] + r[0] + ox, PIV[1] + r[1] + bob + drop)
    j = {k: X(v) for k, v in REST.items()}
    j["X"] = X
    j["Hd"] = add(j["Hd"], p["head"])
    j["Hc"] = add(j["Hc"], mul(p["head"], 0.6))
    j["Hm"] = (96 + ox * 0.6, AY)
    j["ph"] = sec["ph"]
    j["wind"] = p["wind"] + sec.get("wind", 0.0)
    j["lift"] = p["lift"] + sec.get("lift", 0.0)
    return j


def scythe_geo(sc, phase):
    """sc: dict(g=(x,y) near-hand grip, ang=shaft direction butt->head (deg), s=grip distance from the butt,
    fo=far-hand offset along the shaft from g (None: far hand free), bs=+1/-1 blade side)."""
    d = dirv(sc["ang"])
    g = sc["g"]
    butt = sub(g, mul(d, sc["s"]))
    head = add(butt, mul(d, SL))
    bs = sc.get("bs", 1)
    v = rot(d, 90 * bs)
    bl = BL * (1.12 if phase >= 2 else 1.0) * sc.get("bl", 1.0)
    tip = add(head, add(mul(v, bl * 0.93), mul(d, -bl * 0.42)))
    ctrl = add(head, add(mul(v, bl * 0.62), mul(d, bl * 0.16)))
    curve = qbez(head, ctrl, tip, 18)
    fh = add(g, mul(d, sc["fo"])) if sc.get("fo") is not None else None
    return dict(d=d, v=v, g=g, butt=butt, head=head, tip=tip, curve=curve, fh=fh, bs=bs)


def blade_mask(geo, widen=1.0):
    """Blade polygon: spine on the outer (+d) side, the keen edge on the concave side facing the shaft."""
    cv = geo["curve"]
    n = len(cv) - 1
    spine, edge = [], []
    for i, c in enumerate(cv):
        t = i / n
        a = cv[max(0, i - 1)]; b = cv[min(n, i + 1)]
        tg = unit(sub(b, a))
        nrm = (-tg[1], tg[0])
        # orient the normal toward the shaft head direction (+d): the spine
        if nrm[0] * geo["d"][0] + nrm[1] * geo["d"][1] < 0:
            nrm = (-nrm[0], -nrm[1])
        w = (3.3 * (1 - t) ** 0.75 + 0.35) * widen
        spine.append(add(c, mul(nrm, w * 0.72)))
        edge.append(add(c, mul(nrm, -w * 0.28 - (0.6 if t < 0.15 else 0))))
    poly = spine + list(reversed(edge))
    m = poly_mask(poly)
    return m, spine, edge


# =========================================================================== parts
ORDER = ["FXBack", "Wings", "Halo", "Hair", "VeilBack", "Sash", "ScyBack", "ArmFar", "Body", "Head", "Veil",
         "ArmNear", "ScyFront", "Glow", "FX"]
SHADED = ["Wings", "Hair", "Sash", "ScyBack", "ArmFar", "Body", "Head", "ArmNear", "ScyFront"]
FXL = ["FXBack", "Halo", "VeilBack", "Veil", "Glow", "FX"]


def draw_halo(F, j, p, fi, phase):
    k = p["halo"]
    if k <= 0.02:
        return
    c = j["Hc"]
    R = 8.2 if phase == 1 else 9.2
    brk = p["halo_broken"]
    for y in range(int(c[1] - R - 8), int(c[1] + R + 8)):
        for x in range(int(c[0] - R - 8), int(c[0] + R + 8)):
            dx, dy = x + .5 - c[0], (y + .5 - c[1]) * 1.06
            d = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx))
            if brk > 0:
                gap = (hash01(int((a + 180) // 24), 3, 71) < brk * 0.85) or (-20 < a < 20 + 50 * brk)
                if gap:
                    if abs(d - R) < 0.8 and hash01(x, y + fi, 72) > 0.93:
                        F.put([(x, y)], "F1", 190)
                    continue
            e = abs(d - R)
            if e < 0.75:
                F.put([(x, y)], ("F4" if hash01(x, y + fi, 73) > 0.25 else "L") if brk < 0.5 else "F3")
            elif e < 1.55:
                F.put([(x, y)], "F3" if brk < 0.5 else "F2", 190)
            elif e < 1.55 + 1.6 * k and d > R:
                if (x + y + fi) % 2 == 0 or d < R + 2.3:
                    F.under([(x, y)], "F2", 70)
            elif d < R - 1.55 and d > R - 3.2 and brk < 0.5:
                F.under([(x, y)], "F3", 70)
    # tongues of soft white fire leaning outward
    n = 16
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3 * math.sin(fi * 0.7 + i)
        if brk > 0 and (hash01(int((math.degrees(a) + 180) // 24), 3, 71) < brk * 0.85):
            continue
        ln = (1.5 + 3.2 * hash01(i, fi, 74)) * k * (0.6 if brk > 0.5 else 1.0)
        base = add(c, (math.cos(a) * (R + 1.2), math.sin(a) * (R + 1.2) / 1.06))
        out = (math.cos(a) * 0.7, math.sin(a) * 0.7 - 0.7)
        out = unit(out)
        for s in range(int(ln) + 1):
            q = add(base, mul(out, s))
            F.put([q], "F4" if s == 0 else "F3" if s < ln * 0.6 else "F2", 255 if s < 2 else 190)


def grow(start, ang, length, curv, sway, ph, up):
    n = max(3, int(length / 1.3))
    step = length / n
    pts, a, pos = [start], ang, start
    for i in range(1, n + 1):
        t = i / n
        c = curv * (1.0 if t < 0.8 else 2.6)
        a += c * step * up + math.sin(ph - t * 3.2) * sway * 0.05 * t
        pos = add(pos, mul(dirv(a), step))
        pts.append(pos)
    return pts


# a wing = an "arm" root rising from the back + primaries hanging from it like pinions, longest at the wrist
WING_ARM = (30.0, 3.0)                     # length, root radius
WING_PRIM = [(0.30, 17, 1.7), (0.50, 24, 1.9), (0.68, 31, 2.0), (0.84, 37, 2.1), (1.00, 40, 2.2)]


def wing_geometry(root, s, ang, spread, scale, sway, ph):
    """s=-1: the wing behind her (screen left), s=+1: the far wing over her shoulder.  ang = arm direction."""
    up = 1 if s < 0 else -1
    arm = grow(add(root, mul(dirv(ang), 1.5)), ang, WING_ARM[0] * scale, 1.3, sway * 0.3, ph, -up)
    geo = [dict(k=-1, pts=arm, r0=WING_ARM[1] * min(1.2, scale))]
    n = len(arm) - 1
    for k, (t, ln, r0) in enumerate(WING_PRIM):
        i = min(n, int(round(t * n)))
        base = arm[i]
        ad = unit(sub(arm[min(n, i + 1)], arm[max(0, i - 1)]))
        aa = math.degrees(math.atan2(ad[1], ad[0]))
        # pinions fan out from the arm, sweeping back and down; spread opens the fan
        pa = aa - up * (122 - k * 19) * spread
        pts = grow(base, pa, ln * scale, 0.1 + 0.05 * k, sway, ph + k * 0.7, up)
        geo.append(dict(k=k, pts=pts, r0=r0))
    return geo


def draw_wings(Lw, FXb, FXg, j, p, fi, info, phase):
    root = j["X"](REST["Wr"])
    ph = j["ph"]
    allpx = set()
    tips = []
    for key, s in (("wl", -1), ("wr", 1)):
        ang, spread, scale = p[key]
        geo = wing_geometry(root, s, ang, spread, scale, p["wsway"], ph + (0 if s < 0 else 1.3))
        # web of faint fire between the primaries
        for a_, b_ in zip(geo, geo[1:]):
            A = a_["pts"]; B = b_["pts"]
            na, nb = len(A) - 1, len(B) - 1
            if a_["k"] < 0:
                continue
            poly = [A[int(na * t)] for t in (0.1, 0.45, 0.8)] + [B[int(nb * t)] for t in (0.8, 0.45, 0.1)]
            web = poly_mask(poly)
            for q in web:
                if hash01(q[0] // 2, q[1] // 2 + fi, 81) > 0.45:
                    FXb.under([q], "F1" if hash01(*q, 82) > 0.5 else "F2", 70)
        for b in geo:
            pts = b["pts"]
            nm, par = tube(pts, b["r0"] * min(1.25, 0.8 + 0.2 * scale), 0.5 if b["k"] >= 0 else 1.3, ex=1.2)
            bias = 0 if s > 0 else -1
            Lw.paint(nm, "C", bias=bias, ao=0)
            allpx |= set(nm)
            n = len(pts)
            # ember seams in the bark
            for i in range(2, n - 2, 2):
                q = ipt(pts[i])
                if hash01(q[0], q[1], 83 + b["k"]) > 0.72:
                    Lw.decal([q], "E2" if hash01(*q, 84) > 0.5 else "E1")
            # a twig or two
            for tw in ((0.55,) if b["k"] in (1, 3) else ()):
                i = int(n * tw)
                if i < 2 or i >= n - 1:
                    continue
                d = unit(sub(pts[i + 1], pts[i - 1]))
                side = 1 if (b["k"] + int(tw * 10)) % 2 else -1
                td = rot(d, 38 * side * (-1 if s > 0 else 1))
                tp = add(pts[i], mul(td, 5 + 3 * hash01(b["k"], i, 85)))
                tl = line(pts[i], tp)
                Lw.paint({q: (0.0, -0.4, 0.9) for q in tl}, "C", bias=bias, ao=0)
                FXg.put([ipt(tp)], "F3")
                tips.append(tp)
            # burning tips: tongues along the outer third
            outer = {q for q in nm if par[q] > (0.6 if b["k"] >= 0 else 0.85)}
            top = {q for q in outer if (q[0], q[1] - 1) not in nm}
            flame_tongues(FXg, top, (0, -1), fi, 86 + b["k"] * 3 + (0 if s < 0 else 20), length=2.4 + 1.6 * p["fire"],
                          cols=("F1", "F2", "F3", "F4"), density=0.4)
            tp = pts[-1]
            FXg.put([ipt(tp)], "L")
            FXg.put([ipt(add(tp, (0, -1)))], "F4")
            tips.append(tp)
    # knot of roots where the wings leave the back
    Lw.paint(n_dome(root, 3.2, 3.8), "C", bias=-1)
    info["wing_px"] = allpx
    info["wing_tips"] = tips


def draw_lances(Lw, FXg, j, p, fi, info):
    k = p["lances"]
    if k <= 0:
        return
    root = j["X"](REST["Wr"])
    px = set()
    for i, (dy, r0) in enumerate(((-7, 2.6), (4, 2.9), (15, 2.4))):
        ln = 12 + 76 * k - i * 6
        over = add(root, (6, -14 + i * 4))
        end = (root[0] + ln, j["Ch"][1] + dy)
        pts = bezier(root, over, (root[0] + ln * 0.35, end[1] - 2), end, 90)
        nm, par = tube(pts, r0, 0.5, ex=0.8)
        Lw.paint(nm, "C", bias=0, ao=0)
        px |= set(nm)
        for q in pts[6::7]:
            if hash01(*ipt(q), 90 + i) > 0.5:
                Lw.decal([ipt(q)], "E2")
        # burning spear tip
        tip = pts[-1]
        for s in range(4):
            FXg.put([ipt(add(tip, (s, 0)))], "L" if s < 2 else "F4")
        FXg.put([ipt(add(tip, (1, -1))), ipt(add(tip, (1, 1)))], "F3")
        top = {q for q in nm if par[q] > 0.5 and (q[0], q[1] - 1) not in nm}
        flame_tongues(FXg, top, (0, -1), fi, 95 + i, length=2.5, cols=("F1", "F2", "F3"), density=0.6)
    info["lance_px"] = px


def draw_hair(Lh, j, p, fi, phase):
    """Long ash-silver hair (visible once the veil has burned away)."""
    Hd = j["Hd"]
    ph = j["ph"]
    wind = j["wind"]
    root = add(Hd, (-2.5, -2.5))
    n, ln = 18, 30 + 4 * (phase >= 2)
    lp, rp = [], []
    for i in range(n + 1):
        t = i / n
        wv = math.sin(ph - t * 3.2) * (0.4 + 2.6 * t)
        cx = root[0] - 3 * t - 7 * t * t + wind * 0.8 * t * t + wv
        cy = root[1] + ln * t - abs(wind) * 0.35 * t * t * 8
        hw = 2.4 + 3.2 * t - 2.6 * max(0, t - 0.8) * 3
        lp.append((cx - hw, cy))
        rp.append((cx + hw * 0.7, cy))
    poly = lp + list(reversed(rp))
    m = poly_mask(poly)
    Lh.paint(n_plate(m, bevel=2.2, tilt=(0.0, -0.1), strength=0.9,
                     fold=lambda x, y: (0.55 * math.sin((x - root[0]) * 1.3 + (y - root[1]) * 0.15 - ph), 0.0)), "H")
    for s in range(3):
        st = [lerp(lp[i], rp[i], 0.25 + 0.25 * s) for i in range(2, n - 2)]
        Lh.decal([ipt(q) for q in st if hash01(*ipt(q), 101 + s) > 0.35], ("H", 1 + s % 2))


def veil_burn_keep(q, top_y, bot_y, veil, seed=0):
    """Veil burning away from the hem upward: returns 0 (gone), 1 (burning front), 2 (intact)."""
    if veil >= 0.999:
        return 2
    t = (q[1] - top_y) / max(1.0, bot_y - top_y)
    v = 0.55 * t + 0.45 * hash01(q[0] // 2, q[1] // 2, 111 + seed)
    thr = veil * 1.15 - 0.05
    if v > thr:
        return 0
    if v > thr - 0.1:
        return 1
    return 2


def draw_veil_back(F, j, p, fi):
    if p["veil"] <= 0.01:
        return
    Hd = j["Hd"]
    ph = j["ph"]
    wind = j["wind"]
    root = add(Hd, (-3.6, -2.2))
    n, ln = 20, 33
    lp, rp = [], []
    for i in range(n + 1):
        t = i / n
        wv = math.sin(ph * 1.0 - t * 3.6) * (0.5 + 3.0 * t)
        cx = root[0] - 5 * t - 9 * t * t + wind * 1.0 * t * t + wv
        cy = root[1] + ln * t - abs(wind) * 0.4 * t * t * 8
        hw = 2.4 + 3.6 * t - 3.5 * max(0.0, t - 0.75) ** 1.2
        lp.append((cx - hw, cy + t * 2))
        rp.append((cx + hw * 0.6, cy - t * 2))
    tail = [(lp[-1][0] + 2, lp[-1][1] + 2 + math.sin(ph) * 1.2), lerp(lp[-1], rp[-1], 0.55)]
    m = poly_mask(lp + tail + list(reversed(rp)))
    e = edge_of(m)
    top_y, bot_y = root[1], root[1] + ln + 4
    for q in m:
        st = veil_burn_keep(q, top_y, bot_y, p["veil"], 1)
        if st == 0:
            continue
        if st == 1:
            F.put([q], "E2" if hash01(*q, fi) > 0.5 else "F2")
            continue
        if q in e:
            F.put([q], "F3", 190)
        elif hash01(q[0] // 2, q[1] // 3 + fi, 112) > 0.6:
            F.put([q], "F4", 190)
        else:
            F.put([q], "F4", 130)
    outer = {q for q in e if (q[0] - 1, q[1]) not in m or (q[0], q[1] + 1) not in m}
    if p["veil"] > 0.3:
        flame_tongues(F, [q for q in outer if veil_burn_keep(q, top_y, bot_y, p["veil"], 1) == 2], (0, -1), fi, 113,
                      length=2.2, cols=("F2", "F3", "F4"), density=0.45, a=190)


def draw_veil_front(F, j, p, fi, info):
    if p["veil"] <= 0.01:
        return
    Hd = j["Hd"]
    ph = j["ph"]
    wv = math.sin(ph) * 0.7
    cap = mask_disc(add(Hd, (-0.6, -0.7)), 4.4, 4.9)
    drape = poly_mask([(Hd[0] + 3.2, Hd[1] - 3.6), (Hd[0] + 4.6, Hd[1] - 1.0), (Hd[0] + 5.0, Hd[1] + 3.0),
                       (Hd[0] + 4.4 + wv * 0.5, Hd[1] + 10.5 + wv), (Hd[0] + 1.5, Hd[1] + 11.5 + wv * 0.6),
                       (Hd[0] - 2.2, Hd[1] + 9.5), (Hd[0] - 4.6, Hd[1] + 3.5), (Hd[0] - 4.8, Hd[1] - 1)])
    m = cap | drape
    e = edge_of(m)
    top_y, bot_y = Hd[1] - 6, Hd[1] + 12
    for q in m:
        st = veil_burn_keep(q, top_y, bot_y, p["veil"], 2)
        if st == 0:
            continue
        if st == 1:
            F.put([q], "E2" if hash01(*q, fi + 3) > 0.45 else "F2")
            continue
        if q in e:
            F.put([q], "F3", 255 if q[1] < Hd[1] - 1 else 190)
        else:
            F.put([q], "F4", 190 if q[1] < Hd[1] - 1.5 or q[0] < Hd[0] - 1 else 130)
    # the hem of the veil smoulders: a fringe of flame-drips along its bottom edge
    bottom = {q for q in e if (q[0], q[1] + 1) not in m}
    for q in bottom:
        if veil_burn_keep(q, top_y, bot_y, p["veil"], 2) == 2 and (q[0] + fi) % 2 == 0:
            F.put([q], "F2")
    crown = {q for q in e if (q[0], q[1] - 1) not in m and q[1] < Hd[1]}
    if p["veil"] > 0.5:
        flame_tongues(F, crown, (0, -1), fi, 114, length=2.0, cols=("F3", "F4"), density=0.5, a=190)
    info["veil_px"] = m


def draw_head(L, FX, j, p, fi, phase, info):
    Hd = j["Hd"]
    Hl = L["Head"]
    Hl.paint(n_capsule(j["Nk"], add(Hd, (-0.6, 2.6)), 1.5, 1.4), "P", bias=-1)
    head = n_dome(Hd, 3.5, 4.2, tilt=(0.05, 0))
    Hl.paint(head, "P")
    Hl.paint(n_dome(add(Hd, (1.9, 3.0)), 1.8, 1.4), "P", ao=0)
    face = set(head)
    # hair cap over the back and top of the skull
    cap = n_dome(add(Hd, (-1.1, -0.9)), 4.0, 4.4, tilt=(-0.1, -0.05))
    cm = {q: v for q, v in cap.items() if (q[0] + .5 - Hd[0]) < -0.2 - (q[1] + .5 - Hd[1]) * 0.55 or (q[1] + .5 - Hd[1]) < -2.6}
    cm = {q: v for q, v in cm.items() if q[1] < Hd[1] + 3.5}
    Hl.paint(cm, "H", ao=0)
    ex, ey = ipt(add(Hd, (2.1, -0.4)))
    Hl.decal([(ex - 1, ey - 1), (ex, ey - 1)], ("P", 3))
    glow_eyes = p["eyes"] if phase == 1 else max(0.85, p["eyes"])
    if glow_eyes < 0.4:
        Hl.decal([(ex - 1, ey), (ex, ey)], "P1")                 # closed, calm
    else:
        Hl.decal([(ex - 1, ey), (ex, ey)], "P0")
        FX.put([(ex, ey)], "L")
        FX.put([(ex + 1, ey)], "F4" if phase < 3 else "F3")
        if glow_eyes > 0.8:
            FX.put([(ex - 1, ey)], "F3")
            for i in range(1, 5):                               # the light streams back from the eye
                FX.put([(ex - 1 - i, ey - (i // 3))], "F3" if i < 2 else "F2", 190 if i < 3 else 130)
            if phase >= 3:                                        # a tear of light
                for i in range(1, 4):
                    FX.put([(ex, ey + i)], "F3" if i < 2 else "F2", 190)
    nb = ipt(add(Hd, (3.5, 0.3)))
    Hl.fill([nb], "P4")
    Hl.decal([(nb[0] - 1, nb[1] + 1)], ("P", 2))
    lp_ = ipt(add(Hd, (2.6, 2.4)))
    Hl.decal([lp_], ("P", 2))
    info["eye"] = (ex, ey)
    info["face_px"] = face
    # the hood of the pilgrim she wore (only for the unmasking in the intro)
    if p["hood"] > 0:
        hood = n_dome(add(Hd, (-0.8, -0.6)), 4.6, 5.2, tilt=(-0.1, -0.1))
        hm = {q: v for q, v in hood.items() if (q[0] + .5 - Hd[0]) < 2.2 - (q[1] + .5 - Hd[1]) * 0.2}
        drop = int(round((1 - p["hood"]) * 6))
        hm = {(q[0] - drop // 2, q[1] + drop): v for q, v in hm.items()}
        Hl.paint(hm, "A", ao=0)


def robe_geometry(j, p):
    X = j["X"]
    Hm = j["Hm"]
    wind = j["wind"]
    ph = j["ph"]
    c = p["crouch"]
    st = p["stride"]
    wl = X((91.6, 88.6)); wr = X((101.4, 88.6))
    hy = FLOOR + 0.5
    hl = (Hm[0] - 15 - 8 * c + wind * 0.7, hy)
    hr = (Hm[0] + 11.5 + 9 * c + wind * 0.25 + max(0.0, st) * 2.5, hy)
    knee = X((103.5 + st * 2.6 + c * 9, 104 - c * 10))
    left = bezier(wl, X((88.4, 100)), (hl[0] + 5 - c * 2, hy - 13 + c * 5), hl, 16)
    right = bezier(wr, knee, (hr[0] - 1.5, hy - 10 + c * 4), hr, 16)
    hem = []
    n = 40
    for i in range(n + 1):
        t = i / n
        x = hr[0] + (hl[0] - hr[0]) * t
        rip = max(0.0, math.sin(ph + t * 9.0) * 0.9 + math.sin(ph * 2 - t * 17) * 0.4)
        hem.append((x, hy - rip * (0.4 + 0.6 * t)))
    poly = left + list(reversed(hem))[1:-1] + list(reversed(right))
    return poly, (wl, wr, hl, hr, hy)


def draw_body(L, FX, j, p, info, phase, fi):
    Bd = L["Body"]
    X = j["X"]
    ph = j["ph"]
    poly, (wl, wr, hl, hr, hy) = robe_geometry(j, p)
    robe = poly_mask(poly)
    robe = {q for q in robe if q[1] <= FLOOR}
    Wa = j["Wa"]
    top_y = Wa[1]

    def fold(x, y):
        t = max(0.0, min(1.0, (y - top_y) / max(1.0, hy - top_y)))
        cx = lerp(Wa, ((hl[0] + hr[0]) / 2, hy), t)[0]
        hw = 5 + (hr[0] - hl[0]) / 2 * t
        u = (x + .5 - cx) / hw
        sw = 0.8 * math.sin(ph - t * 2.4)
        return (0.6 * math.sin(u * 2.6 * math.pi + sw) * (0.2 + t), 0.0)
    Bd.paint(n_plate(robe, bevel=6, tilt=(0.05, -0.05), strength=1.3, fold=fold), "W")
    # scapular: an ash-grey panel down the front of the robe
    top = X((99.8, 73.5))
    bot = ((hl[0] + hr[0]) / 2 + 5 + p["stride"] * 1.5 + p["crouch"] * 6, hy)
    sc = poly_mask([add(top, (-1.2, 0)), add(top, (1.4, 0)), (bot[0] + 3.6, bot[1] + 1), (bot[0] - 2.4, bot[1] + 1)])
    # the hem band
    rows = {}
    for (x, y) in robe:
        rows[x] = max(rows.get(x, -1), y)
    band = {(x, y) for (x, y) in robe if y >= rows[x] - 1}
    Bd.decal(band, ("A", 3))
    Bd.decal({(x, y) for (x, y) in robe if y == rows[x] - 2}, ("A", 4))
    info["robe_px"] = set(robe)
    info["robe_bottom"] = rows
    # bodice
    bod = [X(q) for q in ((92.4, 72.6), (95.4, 71.0), (100.6, 71.0), (102.6, 73.6), (102.4, 78.2), (101.0, 83.2),
                          (101.6, 89.0), (91.6, 89.0), (92.2, 83.2), (91.3, 78.0))]
    bm = poly_mask(bod)
    Bd.paint(n_plate(bm, bevel=3.2, tilt=(0.1, -0.05), strength=1.3), "W")
    Bd.paint(n_dome(X((100.6, 77.0)), 2.3, 2.0, tilt=(0.1, 0.1)), "W", ao=0, clip=bm)
    sc_m = {q for q in sc if q in robe or q in bm}
    Bd.paint(n_plate(sc_m, bevel=1.5, tilt=(0.1, -0.1), strength=0.8,
                     fold=lambda x, y: (0.25 * math.sin(y * 0.5 + ph), 0.0)), "A", ao=0)
    sce = {q for q in sc_m if (q[0] - 1, q[1]) not in sc_m or (q[0] + 1, q[1]) not in sc_m}
    # collar
    col = poly_mask([X((95.0, 70.6)), X((100.8, 70.6)), X((100.4, 72.4)), X((95.2, 72.6))])
    Bd.paint({q: (0.0, -0.4, 0.9) for q in col}, "A", ao=0)
    # the kindling: a seed of white flame at her breast
    kc = X((100.4, 78.0))
    heart = [ipt(kc)]
    FX.put(heart, "L")
    FX.put([ipt(add(kc, (0, -1))), ipt(add(kc, (1, 0))), ipt(add(kc, (-1, 0))), ipt(add(kc, (0, 1)))],
           "F4" if phase == 1 else "F3", 255 if phase > 1 else 190)
    if phase >= 2:
        for a in range(0, 360, 60):
            q = add(kc, mul(dirv(a + fi * 13), 2.2))
            FX.put([q], "F2", 190)
    info["heart"] = kc
    # waist cord + knot
    belt = set(line(X((91.6, 88.4)), X((101.6, 88.8)))) | set(line(X((91.6, 89.4)), X((101.6, 89.8))))
    Bd.paint({q: (0.0, -0.4, 0.9) if q[1] < X((96, 89))[1] + 0.3 else (0, 0.4, 0.9) for q in belt}, "A", ao=0)
    # kneeling: a knee bulge where the thigh folds under the robe
    return robe


def draw_sash(L, j, p, info):
    Ls = L["Sash"]
    X = j["X"]
    ph = j["ph"]
    wind = j["wind"]
    base = X((91.0, 89.4))
    for k, (ln, off) in enumerate(((25, 0.0), (19, 1.2))):
        n = 18
        pts = []
        for i in range(n + 1):
            t = i / n
            wv = math.sin(ph * 1.0 - t * 4.2 + k * 1.3) * (0.4 + 2.8 * t)
            x = base[0] - 1 - ln * 0.45 * t + wind * 0.9 * t * t - k * 1.5 + wv * 0.5
            y = base[1] + ln * 0.88 * t - abs(wind) * 0.45 * t * t * 3
            pts.append((x, min(FLOOR - 1, y)))
        nm, _ = tube(pts, 1.25, 0.8)
        Ls.paint(nm, "W", bias=-1 - k, ao=0)
    Ls.paint(n_dome(base, 1.8, 1.6), "A", bias=0)


def draw_arm(Lr, FX, j, p, side, info, hand_pt):
    near = side == "n"
    sh = j["Sn"] if near else j["Sf"]
    pref = p["eln"] if near else p["elf"]
    l1, l2 = (L1N, L2N) if near else (L1F, L2F)
    d = math.hypot(*sub(hand_pt, sh))
    if d > l1 + l2 + 0.6:
        info.setdefault("warn", []).append(f"{side} arm overreach {d:.1f}>{l1 + l2:.1f}")
        hand_pt = add(sh, mul(unit(sub(hand_pt, sh)), l1 + l2))
    el = ik(sh, hand_pt, l1, l2, pref)
    bias = 0 if near else -1
    ph = j["ph"]
    wind = j["wind"]
    fa = unit(sub(hand_pt, el))
    wr = sub(hand_pt, mul(fa, 1.2))
    fl = math.hypot(*sub(wr, el))
    raise_ = max(0.0, min(1.0, -fa[1] * 1.3))
    M = add(el, mul(fa, max(2.0, (fl - 1.8) * (1 - 0.65 * raise_))))
    p1 = (-fa[1], fa[0])
    pd = p1 if (p1[1] > 0.05 or (abs(p1[1]) <= 0.05 and p1[0] < 0)) else (-p1[0], -p1[1])
    pu = (-pd[0], -pd[1])
    mw = 3.6 if near else 3.2
    drop = (8.5 if near else 7.5) - abs(fa[1]) * 2
    sway = math.sin(ph - (0.6 if near else 1.4)) * 1.2
    lipd = add(M, mul(pd, mw))
    T = (lipd[0] - 1 + wind * 0.4 + sway, max(lipd[1], M[1]) + drop - abs(wind) * 0.15)
    T2 = lerp(add(el, mul(pd, 2.0)), T, 0.55)
    T2 = (T2[0] - 1 + wind * 0.2 + sway * 0.5, T2[1] + 1)
    cone = [add(el, mul(pu, 2.0)), add(M, mul(pu, mw - 0.8)), add(lipd, mul(fa, 0.4)), add(T, (1.5, -1.2)), T, T2,
            add(el, mul(pd, 2.1))]
    drape = poly_mask(cone)
    Lr.paint(n_plate(drape, bevel=2.2, tilt=(0.1, -0.1), strength=1.0,
                     fold=lambda x, y: (0.35 * math.sin((x - el[0]) * 1.1 + (y - el[1]) * 0.3 + ph * 0.5), 0.0)),
             "W", bias=bias)
    Lr.paint(n_capsule(sh, el, 2.1, 1.9), "W", bias=bias)
    mouth = {q for q in drape if abs((q[0] + .5 - M[0]) * fa[0] + (q[1] + .5 - M[1]) * fa[1]) < 1.0 and
             abs((q[0] + .5 - M[0]) * p1[0] + (q[1] + .5 - M[1]) * p1[1]) < mw - 0.8}
    Lr.paint({q: (0.2, 0.3, 0.9) for q in mouth}, "A", bias=bias, ao=0)
    bottom = {q for q in drape if (q[0], q[1] + 1) not in drape and q not in mouth and q[1] > T[1] - 4}
    Lr.decal(bottom, ("A", 3 if near else 2))
    Lr.paint(n_capsule(M, wr, 1.0, 0.95), "P", bias=bias)
    hd = p["hn_dir"] if near else p["hf_dir"]
    palm = add(wr, mul(dirv(hd), 0.6))
    Lr.paint(n_dome(palm, 1.35, 1.35), "P", bias=bias, ao=0)
    fp = line(add(palm, mul(dirv(hd), 0.8)), add(palm, mul(dirv(hd), 2.4)))
    Lr.paint({q: (0.0, -0.5, 0.8) for q in fp}, "P", bias=bias, ao=0)
    info["hand_" + side] = add(palm, mul(dirv(hd), 1.4))
    info["elbow_" + side] = el
    info["sleeve_" + side] = drape


def draw_scythe(Ls, FX, geo, p, fi, phase, info, vis=1.0):
    d = geo["d"]
    keep = lambda q: vis >= 1 or hash01(q[0], q[1], 121) < vis * 1.1 - 0.05
    nrm = (-d[1], d[0])
    if nrm[1] > 0 or (abs(nrm[1]) < 0.2 and nrm[0] > 0):
        nrm = (-nrm[0], -nrm[1])                     # the lit side faces up/left
    lit = [q for q in line(add(geo["butt"], mul(nrm, 0.5)), add(geo["head"], mul(nrm, 0.5))) if keep(q)]
    dark = [q for q in line(add(geo["butt"], mul(nrm, -0.5)), add(geo["head"], mul(nrm, -0.5))) if keep(q)]
    nm = {}
    for q in dark:
        nm[q] = (-nrm[0] * 0.8, -nrm[1] * 0.8, 0.5)
    for q in lit:
        nm[q] = (nrm[0] * 0.3 + LIGHT[0] * 0.5, nrm[1] * 0.3 + LIGHT[1] * 0.5, 0.8)
    nm = {q: norm3(*v) for q, v in nm.items()}
    Ls.paint(nm, "B", bias=0, ao=0)
    Ls.decal([ipt(geo["butt"]), ipt(add(geo["butt"], d))], ("B", 1))
    knot = n_dome(geo["head"], 2.0, 2.0)
    Ls.paint({q: v for q, v in knot.items() if keep(q)}, "C" if phase >= 2 else "B", bias=-1, ao=0)
    if phase >= 2:        # burning roots wound about the upper shaft
        for i in range(24):
            t = 0.55 + 0.45 * i / 24
            c = lerp(geo["butt"], geo["head"], t)
            o = mul((-d[1], d[0]), 1.4 * math.sin(i * 0.9 + t * 4))
            q = ipt(add(c, o))
            if keep(q):
                Ls.fill([q], "C1" if i % 3 else "E1")
                if i % 4 == 0:
                    FX.put([q], "E2")
    bm, spine, edge = blade_mask(geo, widen=1.12 if phase >= 2 else 1.0)
    bm = {q for q in bm if keep(q)}
    em = set()
    for q in edge:
        em.add(ipt(q))
    for q in bm:
        # distance to the edge polyline (cheap: nearest sample)
        ds = min(math.hypot(q[0] + .5 - e[0], q[1] + .5 - e[1]) for e in edge[::2])
        dsp = min(math.hypot(q[0] + .5 - s[0], q[1] + .5 - s[1]) for s in spine[::2])
        if ds < 0.9:
            c = "L"
        elif dsp < 0.9:
            c = "F2" if phase >= 2 else "F3"
        else:
            c = "F4"
        Ls.fill([q], c)
    info["blade_px"] = bm
    info["blade_tip"] = geo["tip"]
    # flame licking from the spine, streaming away from the edge
    sp_edge = {q for q in bm if min(math.hypot(q[0] + .5 - s[0], q[1] + .5 - s[1]) for s in spine[::2]) < 1.3}
    up = unit(add(mul(d, 0.6), (0, -1.0)))
    flame_tongues(FX, sp_edge, up, fi, 123, length=2.2 + (1.6 if phase >= 2 else 0) + p["fire"],
                  cols=("F1", "F2", "F3", "F4") if phase >= 2 else ("F2", "F3", "F4"), density=0.55)
    info["shaft_px"] = set(nm)


def draw_flask(F, at, fi, k=1.0):
    x, y = ipt(at)
    glass = [(x, y - 4), (x - 1, y - 3), (x + 1, y - 3), (x - 1, y - 2), (x + 1, y - 2), (x - 1, y - 1), (x + 1, y - 1), (x, y)]
    F.put(glass, "W5")
    F.put([(x, y - 3), (x, y - 2), (x, y - 1)], "F3" if k < 0.5 else "F4")
    F.put([(x, y - 5)], "B3")
    if k > 0.3:
        F.under([(x + a, y - 2 + b) for a in (-2, 2) for b in (-2, 0, 2)], "F2", 70)


def smear_color(age, edge_d):
    if age < 0.2:
        return "L" if edge_d < 1.2 else "F4"
    if age < 0.42:
        return "F4" if edge_d < 1.2 else "F3"
    if age < 0.66:
        return "F3"
    return "F2"


def interp_sc(a, b, u):
    da = ((b["ang"] - a["ang"] + 180) % 360) - 180
    return dict(g=lerp(a["g"], b["g"], u), ang=a["ang"] + da * u, s=a["s"] + (b["s"] - a["s"]) * u,
                fo=None, bs=b.get("bs", 1), bl=b.get("bl", 1.0))


def fx_smear(F, info, prev_sc, cur_sc, phase, reach=1.0, both=False):
    """Crescent of pale flame traced by the outer blade between the previous pose and this one."""
    if prev_sc is None or cur_sc is None:
        return set()
    N = 12
    tracks = []
    for st in range(N + 1):
        u = st / N
        geo = scythe_geo(interp_sc(prev_sc, cur_sc, u), phase)
        cv = geo["curve"]
        n = len(cv) - 1
        row = [cv[int(n * t)] for t in (0.1, 0.3, 0.5, 0.7, 0.85, 1.0)]
        row.append(add(geo["tip"], mul(unit(sub(geo["tip"], geo["head"])), 1.5)))
        # the shaft's upper end too (the whole scythe sweeps)
        row = [lerp(geo["butt"], geo["head"], 0.75), geo["head"]] + row
        tracks.append((row, 1 - u))
    best = {}
    for st in range(N):
        A, age = tracks[st][0], tracks[st + 1][1]
        B = tracks[st + 1][0]
        for i in range(len(A) - 1):
            quad = [A[i], A[i + 1], B[i + 1], B[i]]
            t = i / (len(A) - 2)
            for q in poly_mask(quad) | set(line(A[i + 1], B[i + 1])):
                if inb(*q) and (q not in best or best[q][0] > age):
                    best[q] = (age, t)
    out = set()
    for q, (age, t) in best.items():
        if q[1] > FLOOR:
            continue
        v = age
        if t < 0.45 and age > 0.15:
            continue
        if v > 0.8 and (q[0] + q[1]) % 2:
            continue
        F.under([q], smear_color(v, 0.5 if t > 0.85 else 2.0), 255 if v < 0.55 else 190)
        out.add(q)
    return out


def dissolve(imgs, d, fi, names, ash=True):
    """Body comes apart into ash and embers, hem first."""
    if d <= 0:
        return
    F = FXLayer("motes")
    for n in names:
        im = imgs[n]
        px = im.load()
        for y in range(H):
            for x in range(W):
                if px[x, y][3] == 0:
                    continue
                v = 0.6 * (y - 40) / 90.0 + 0.4 * hash01(x // 2, y // 2, 131)
                if v < d * 1.3 - 0.15:
                    px[x, y] = (0, 0, 0, 0)
                    if hash01(x, y, 132 + fi) > 0.975:
                        age = hash01(x, y, 133)
                        q = (x + 4 + age * 10 + d * 10, y - 4 - age * 22 - d * 26)
                        F.put([q], "A4" if ash and hash01(x, y, 134) > 0.5 else "F2")
                elif v < d * 1.3 - 0.06:
                    px[x, y] = RGBA["F4" if hash01(x, y, 135) > 0.5 else "F2"]
    imgs["FX"].alpha_composite(F.image())


# =========================================================================== one frame
def render(p, fi, sec, phase, prev=None):
    j = joints(p, sec)
    L = {n: Layer(n) for n in SHADED}
    FX = {n: FXLayer(n) for n in FXL}
    info = {"j": j, "smear": set(), "wing_px": set(), "lance_px": set(), "blade_px": set()}
    if phase >= 2 and p["wings"] is not False and p["wl"][2] > 0.05:
        draw_wings(L["Wings"], FX["FXBack"], FX["Glow"], j, p, fi, info, phase)
    draw_lances(L["Wings"], FX["Glow"], j, p, fi, info)
    draw_halo(FX["Halo"], j, p, fi, phase)
    if p["veil"] < 0.999:
        draw_hair(L["Hair"], j, p, fi, phase)
    draw_veil_back(FX["VeilBack"], j, p, fi)
    draw_sash(L, j, p, info)
    sc = p["scy"]
    geo = scythe_geo(sc, phase) if sc else None
    if geo and sc.get("hand") == "f":           # the far hand holds the scythe (near hand busy: flask, spell)
        hf, hn = geo["g"], p["hn"]
    else:
        hn = geo["g"] if geo else p["hn"]
        hf = geo["fh"] if (geo and geo["fh"] is not None) else p["hf"]
    draw_arm(L["ArmFar"], FX["Glow"], j, p, "f", info, hf)
    draw_body(L, FX["Glow"], j, p, info, phase, fi)
    draw_head(L, FX["Glow"], j, p, fi, phase, info)
    draw_veil_front(FX["Veil"], j, p, fi, info)
    draw_arm(L["ArmNear"], FX["Glow"], j, p, "n", info, hn)
    if geo:
        layer = L["ScyFront"] if sc.get("front", True) else L["ScyBack"]
        draw_scythe(layer, FX["FX"], geo, p, fi, phase, info, vis=sc.get("vis", 1.0))
        info["geo"] = geo
        if geo["tip"][1] > FLOOR + 0.5 or geo["butt"][1] > FLOOR + 1.5:
            info.setdefault("warn", []).append(f"scythe below floor tip={geo['tip'][1]:.1f} butt={geo['butt'][1]:.1f}")
    if p["flask"] is not None:
        draw_flask(FX["FX"], info["hand_n"] if p["flask"] == "hand" else p["flask"], fi, p.get("flask_k", 1.0))
    return L, FX, info


def compose(L, FX, info, p, phase):
    imgs = {}
    for n in ORDER:
        if n in L:
            imgs[n] = render_layer(L[n])
        else:
            imgs[n] = FX[n].image()
    return imgs


def flatten(imgs, order=ORDER, w=W, h=H):
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for n in order:
        if n in imgs:
            out.alpha_composite(imgs[n])
    return out
