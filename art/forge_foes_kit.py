"""Cold Forge foes -- the shared pixel kit (agent FOES, v17).  Used by art/gen_forge_foes.py.

Part 1 is a copy of the approved concept rig (art/concepts/forge/forge_rig.py: normal-mapped parts, material ramps,
sel-out outline, cool rim, warm point lights) so the build never depends on a concept file.  Part 2 adds what the
in-game sheets need: muscled limbs (real forearms and hands, not sticks), blade plates, motion smears, a small pose
/ tween system (keyframes -> eased in-betweens, cloth lag) and the sheet export (Aseprite + meta + previews).
"""
import math
from PIL import Image

# ---------------------------------------------------------------- palette
HEX = {
    "OUT": "#050609",
    # black iron (plate, greaves, hammer, tongs) -- cold blue-black
    "I0": "#090a0f", "I1": "#151820", "I2": "#232835", "I3": "#363d4d", "I4": "#535c70", "I5": "#8a96ab",
    # soot veil / mantle -- near-black, faintly warm grey so it is not the iron
    "S0": "#060607", "S1": "#0c0c10", "S2": "#15151b", "S3": "#202028", "S4": "#2e2e39", "S5": "#454554",
    # smith's leather apron -- oxblood-brown, scorched
    "L0": "#0e0807", "L1": "#1a0f0c", "L2": "#2a1813", "L3": "#3c231a", "L4": "#543224", "L5": "#714631",
    # tarnished bronze ritual trim (restrained: thin lines only)
    "B0": "#17120c", "B1": "#2a2115", "B2": "#43341f", "B3": "#5f4a2d", "B4": "#82673e", "B5": "#a98a56",
    # ash-grey dead skin (gaunt wrists, the face under the mask on the alt heads)
    "K0": "#141317", "K1": "#232126", "K2": "#353236", "K3": "#4a4549", "K4": "#625b5d", "K5": "#7e7676",
    # slate (enemies, props)
    "T0": "#0a0c10", "T1": "#121620", "T2": "#1c222e", "T3": "#29313f", "T4": "#3a4455", "T5": "#56627a",
    # emissive heat: dull red -> orange -> white-hot
    "E0": "#2a0a06", "E1": "#5a1409", "E2": "#962a0c", "E3": "#cf4c14", "E4": "#f07f24", "E5": "#ffb453",
    "E6": "#ffe2a0", "E7": "#fff8e8",
    # steam / quench (cold emissive)
    "Q0": "#1d2630", "Q1": "#34424f", "Q2": "#56687a", "Q3": "#8496a8", "Q4": "#b8c6d2", "Q5": "#e2ebf2",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
MATS = "ISLBKT"
RAMP = {m: [RGBA[f"{m}{i}"] for i in range(6)] for m in MATS}


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


# warm-lit copies of each ramp: what the coals do to cold iron (orange on the facing planes)
WARM_TONE = (214, 92, 34)
WARM = {}
for _m in MATS:
    WARM[_m] = [_mix(RAMP[_m][i], WARM_TONE, 0.22 + 0.11 * i) for i in range(6)]
    WARM[_m] = [_mix(c, (255, 214, 150), max(0, i - 3) * 0.12) for i, c in enumerate(WARM[_m])]

SHINY = {"B": 0.86, "I": 0.93}
CONTRAST = {"I": 1.5, "B": 1.2}
MAT_LIFT = {"I": 1.35, "L": 0.55, "B": 0.9, "S": 0.45, "K": 0.4, "T": 0.6}
RIM = {"S": (4, 3), "I": (4, 3), "L": (3, 2), "T": (4, 3)}    # (top/left rim level, right rim level)
LIGHT = (-0.45, -0.78, 0.45)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)


# ---------------------------------------------------------------- geometry
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def dirv(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
def perp(v): return (-v[1], v[0])


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


def ribbon(spine, widths, offset=0.0):
    """Polygon around a polyline with per-point half widths (smooth tapering cloth / blades)."""
    L, R = [], []
    n = len(spine)
    for i, c in enumerate(spine):
        a = spine[max(0, i - 1)]; b = spine[min(n - 1, i + 1)]
        nv = perp(unit(sub(b, a)))
        w = widths[i] if isinstance(widths, (list, tuple)) else widths
        L.append(add(c, mul(nv, w + offset)))
        R.append(add(c, mul(nv, -w + offset)))
    return L + list(reversed(R))


def edge_of(mask):
    return {q for q in mask if any((q[0] + a, q[1] + b) not in mask for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


# ---------------------------------------------------------------- layers / render
class Canvas:
    """One shaded figure: painter's-order parts, then shade + outline, then emissive FX on top."""

    def __init__(self, w, h):
        self.W, self.H = w, h
        self.px = {}            # (x,y) -> [mat, n, bias, fixed]
        self.fx = {}            # (x,y) -> rgba   (emissive, over everything)
        self.fxb = {}           # (x,y) -> rgba   (emissive, behind the figure)
        self.lights = []        # (pos, radius, strength)
        self.noout = set()

    def inb(self, p):
        return 0 <= p[0] < self.W and 0 <= p[1] < self.H

    def paint(self, normals, mat, bias=0, ao=1, iline=False):
        pts = [p for p in normals if self.inb(p)]
        new = set(pts)
        edge = set()
        if iline:
            for (x, y) in pts:
                if any((x + a, y + b) not in new and (x + a, y + b) in self.px for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.add((x, y))
        if ao:
            done = set()
            for (x, y) in pts:
                for a, b in ((1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)):
                    q = (x + a, y + b)
                    if q not in new and q in self.px and q not in done:
                        self.px[q][2] -= ao
                        done.add(q)
        for p in pts:
            self.px[p] = [mat, normals[p], bias, None, p in edge]
        return new

    def flat(self, pts, mat, level):
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if self.inb(p):
                self.px[p] = [mat, (0, 0, 1), 0, level, False]

    def decal(self, pts, mat_level, only=None):
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            e = self.px.get(p)
            if e is None or (only and e[0] not in only):
                continue
            e[0], e[3] = mat_level
            e[4] = False

    def erase(self, pts):
        for p in pts:
            self.px.pop(p, None)

    def glow(self, pts, c, a=255, behind=False):
        tgt = self.fxb if behind else self.fx
        rgba = (RGBA[c][:3] if isinstance(c, str) else c[:3]) + (a,)
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if self.inb(p):
                tgt[p] = rgba

    def glow_under(self, pts, c, a=255, behind=False):
        tgt = self.fxb if behind else self.fx
        rgba = (RGBA[c][:3] if isinstance(c, str) else c[:3]) + (a,)
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if self.inb(p) and p not in tgt:
                tgt[p] = rgba

    # -- shading
    def level(self, e, x, y):
        mat, n, bias, fixed = e[0], e[1], e[2], e[3]
        top = 5
        if fixed is not None:
            return max(0, min(top, fixed + (bias if bias < 0 else 0))), 0.0
        ndl = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
        v = 0.1 + 0.9 * max(0.0, ndl) ** CONTRAST.get(mat, 1.0)
        f = v * (top - (1 if mat in SHINY else 0)) + 0.25
        f += (self.ref_y - y) * self.ydark
        f += MAT_LIFT.get(mat, 0.0)
        i = int(math.floor(f)) + bias
        if mat in SHINY:
            rz = 2 * ndl * n[2] - LIGHT[2]
            i = top if (rz > SHINY[mat] and bias >= 0 and f > 2.2) else min(i, top - 1)
        warm = 0.0
        for (lp, rad, st) in self.lights:
            dx, dy = lp[0] - (x + .5), lp[1] - (y + .5)
            d = math.hypot(dx, dy)
            if d > rad:
                continue
            ld = norm3(dx, dy, 5.0)
            fac = max(0.0, n[0] * ld[0] + n[1] * ld[1] + n[2] * ld[2] * 0.4) * (1 - d / rad) ** 1.2 * st
            warm = max(warm, fac)
        if warm > 0.16:
            i = max(i, int(1 + warm * 4.2) + min(0, bias))
        return max(0, min(top, i)), warm

    def render(self, ref_y=60, ydark=0.012, outline=True, rim=True):
        self.ref_y, self.ydark = ref_y, ydark
        img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        pix = img.load()
        for p, c in self.fxb.items():
            pix[p] = c
        col, lvl = {}, {}
        for (x, y), e in self.px.items():
            i, warm = self.level(e, x, y)
            r = RIM.get(e[0]) if rim else None
            if r and e[3] is None and e[2] > -2:
                if (x - 1, y) not in self.px or (x, y - 1) not in self.px:
                    i = max(i, r[0] + min(0, e[2]))
                elif (x + 1, y) not in self.px and warm <= 0.16:
                    i = max(i, r[1] + min(0, e[2]))
            if e[4]:
                i = max(0, min(i - 2, 2))
            lvl[(x, y)] = i
            col[(x, y)] = (WARM if warm > 0.16 else RAMP)[e[0]][i]
        if outline:
            for (x, y) in self.px:
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + a, y + b)
                    if not self.inb(q) or q in self.px or q in self.noout:
                        continue
                    c = RGBA["OUT"]
                    if (a, b) in ((-1, 0), (0, -1)) and lvl[(x, y)] >= 4:
                        c = RAMP[self.px[(x, y)][0]][1]
                    if q not in self.fxb or c == RGBA["OUT"]:
                        pix[q] = c
        for p, c in col.items():
            pix[p] = c
        top = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        tp = top.load()
        for p, c in self.fx.items():
            tp[p] = c
        img.alpha_composite(top)
        return img


# ---------------------------------------------------------------- emissive helpers
HEAT = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]


def heat_col(t):
    """t 0..1 -> dull red .. white-hot"""
    t = max(0.0, min(1.0, t))
    return HEAT[min(len(HEAT) - 1, int(t * (len(HEAT) - 0.01)))]


def halo(cv, mask, c="E3", a=130, r=1, behind=True):
    """A thin stepped-alpha glow around an emissive mask."""
    ring = set()
    for (x, y) in mask:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                q = (x + dx, y + dy)
                if q not in mask:
                    ring.add(q)
    cv.glow_under(ring, c, a, behind=behind)


def flame_tongues(cv, edge_pts, up, fi, seed, length=3.0, cols=("E3", "E4", "E5"), density=0.55, a=255, lean=(0, 0),
                  behind=False):
    for (x, y) in edge_pts:
        if hash01(x, y, seed) > density:
            continue
        ln = length * (0.35 + 0.9 * hash01(x + fi * 7, y, seed + 1))
        n = max(1, int(round(ln)))
        wob = (hash01(x, fi, seed + 2) - 0.5) * 1.2
        for k in range(n):
            t = k / max(1, n - 1) if n > 1 else 0
            q = (x + up[0] * (k + 1) + lean[0] * k * k * 0.15 + wob * t, y + up[1] * (k + 1) + lean[1] * k * k * 0.15)
            c = cols[min(len(cols) - 1, int((1 - t) * (len(cols) - 1) + 0.5))]
            if behind:
                cv.glow_under([q], c, a, behind=True)
            else:
                cv.glow([q], c, a)


def bbox_alpha(img):
    return img.getbbox()


# =====================================================================================================================
# Part 2 -- in-game kit (FOES)
# =====================================================================================================================
import os, json
from PIL import ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
PREVIEWS = os.path.join(ART, "previews")


def limb(cv, pts, radii, mat="I", bias=0, ao=1, iline=False, flat=1.0):
    """One continuous tapered tube through joints (no seams between segments)."""
    path, rr = [], []
    for (a, ra), (b, rb) in zip(zip(pts, radii), zip(pts[1:], radii[1:])):
        n = max(2, int(math.hypot(*sub(b, a)) / 0.7))
        for i in range(n):
            t = i / n
            path.append(lerp(a, b, t)); rr.append(ra + (rb - ra) * t)
    path.append(pts[-1]); rr.append(radii[-1])
    nm, best = {}, {}
    for c, r in zip(path, rr):
        for q in mask_disc(c, r + 0.15):
            ox, oy = q[0] + .5 - c[0], q[1] + .5 - c[1]
            d = math.hypot(ox, oy) / max(r, 0.6)
            if q not in best or d < best[q]:
                best[q] = d
                k = min(0.95, d) * flat
                l = math.hypot(ox, oy) or 1
                nm[q] = norm3(ox / l * k, oy / l * k, math.sqrt(max(0.02, 1 - k * k)) + 0.15)
    cv.paint(nm, mat, bias=bias, ao=ao, iline=iline)
    return nm


def arm(cv, sh, wrist, l1, l2, pref, R=(3.0, 2.8, 2.1, 2.7, 1.6), mat="S", bias=0, iline=True):
    """Shoulder -> elbow -> wrist with a real profile: deltoid, biceps, a narrower elbow, a forearm that swells
    below the elbow and tapers to the wrist.  Returns (elbow, wrist)."""
    el = ik(sh, wrist, l1, l2, pref)
    pts = [sh, lerp(sh, el, 0.38), el, lerp(el, wrist, 0.3), wrist]
    limb(cv, pts, list(R), mat, bias, iline=iline)
    return el


def fist(cv, wrist, d, r=1.9, mat="I", bias=0, open_=0.0):
    """A gauntleted hand past the wrist along d: a slightly long dome; open_ > 0 spreads two claw fingers."""
    c = add(wrist, mul(d, r * 0.9))
    v = perp(d)
    m = {}
    for q in mask_disc(c, r * 1.15, r * 1.15):
        lx = (q[0] + .5 - c[0]) * d[0] + (q[1] + .5 - c[1]) * d[1]
        ly = (q[0] + .5 - c[0]) * v[0] + (q[1] + .5 - c[1]) * v[1]
        if (lx / (r * 1.15)) ** 2 + (ly / r) ** 2 <= 1.0:
            m[q] = norm3(lx / r * 0.6 * d[0] + ly / r * 0.8 * v[0], lx / r * 0.6 * d[1] + ly / r * 0.8 * v[1], 0.75)
    cv.paint(m, mat, bias=bias, iline=True)
    if open_ > 0:
        for s in (-1, 1):
            a = add(c, mul(v, s * r * 0.6))
            b = add(a, add(mul(d, r * 1.4 + open_), mul(v, s * open_ * 0.7)))
            e = add(b, mul(d, 1.3))
            cv.paint({q: (0.2, -0.4, 0.88) for q in line(a, b) + line(b, e)}, mat, bias=bias, ao=0)
    return c


def leg(cv, hip, foot, l1, l2, R=(4.0, 3.6, 2.5, 2.9, 1.7), pref=(1, -0.12), mat="S", bias=0, iline=True, toe=6.0):
    ank = add(foot, (0, -1.6))
    kn = ik(hip, ank, l1, l2, pref)
    limb(cv, [hip, lerp(hip, kn, 0.4), kn, lerp(kn, ank, 0.3), ank], list(R), mat, bias, iline=iline)
    fx, fy = foot
    poly = [(fx - 2.4, fy - 3.0), (fx + 1.2, fy - 2.8), (fx + toe * 0.7, fy - 0.9), (fx + toe, fy + 0.6), (fx - 2.6, fy + 0.6)]
    cv.paint(n_plate(poly_mask(poly), bevel=1.3, tilt=(0.1, -0.5)), "I", bias=bias, iline=True)
    return kn


def blade(cv, a, b, w0, w1=0.25, mat="I", bias=0, edge=1, tip="point", seed=0, bevel=0.9, lit=5, fuller=True,
          tilt=None):
    """A tapered blade ribbon from a (base) to b (tip): bright edge on one side (edge=+1/-1, 0 none), a dark fuller,
    a pointed or broken (jagged) tip.  Returns its mask."""
    d = unit(sub(b, a)); v = perp(d)
    L = math.hypot(*sub(b, a))
    n = max(4, int(L / 1.5))
    sp = [lerp(a, b, j / n) for j in range(n + 1)]
    ws = []
    for j in range(n + 1):
        t = j / n
        w = w0 + (w1 - w0) * t
        if tip == "point":
            w *= min(1.0, (1 - t) * 4.5 + 0.12)
        ws.append(max(0.35, w))
    poly = ribbon(sp, ws)
    m = poly_mask(poly)
    if tip == "broken":
        # bite a jagged notch out of the end
        for q in list(m):
            lx = (q[0] + .5 - a[0]) * d[0] + (q[1] + .5 - a[1]) * d[1]
            ly = (q[0] + .5 - a[0]) * v[0] + (q[1] + .5 - a[1]) * v[1]
            cut = L - 1.6 - 2.2 * hash01(int(ly * 2 + 7), seed, 3) - (1.4 if ly * (1 if seed % 2 else -1) > 0 else 0)
            if lx > cut:
                m.discard(q)
    if not m:
        return m
    tl = tilt if tilt is not None else (-0.35 * v[0] - 0.1, -0.35 * v[1] - 0.3)
    cv.paint(n_plate(m, bevel=bevel, tilt=tl, strength=0.8), mat, bias=bias, iline=False)
    if edge:
        es = [ipt(add(p, mul(v, edge * (w - 0.6)))) for p, w in zip(sp, ws)]
        cv.decal([q for q in es if q in m], (mat, lit if bias >= 0 else lit - 1), only=mat)
        ds = [ipt(add(p, mul(v, -edge * (w - 0.5)))) for p, w in zip(sp, ws)]
        cv.decal([q for q in ds if q in m and q not in es], (mat, 1), only=mat)
    if fuller and w0 > 1.4:
        fs = [ipt(add(p, mul(v, -edge * 0.3))) for p in sp[1:int(n * 0.7)]]
        cv.decal([q for q in fs if q in m], (mat, 2), only=mat)
    return m


def smear(cv, c, r_in, r_out, a0, a1, cols=("Q2", "Q3", "Q4", "Q5"), behind=False, alpha=255, dith=True):
    """A motion smear: an arc band swept from angle a0 (trailing) to a1 (leading), degrees, around c.  The band is
    thin at its tail and full at its head; the leading rim is the brightest.  Returns the pixel set."""
    if abs(a1 - a0) < 3:
        return set()
    lo, hi = min(a0, a1), max(a0, a1)
    out = set()
    R = int(r_out) + 2
    for y in range(int(c[1]) - R, int(c[1]) + R + 1):
        for x in range(int(c[0]) - R, int(c[0]) + R + 1):
            dx, dy = x + .5 - c[0], y + .5 - c[1]
            rho = math.hypot(dx, dy)
            if rho > r_out or rho < r_in * 0.6:
                continue
            ph = math.degrees(math.atan2(dy, dx))
            # bring phi into [lo-360, hi+360] closest window
            while ph < lo - 180: ph += 360
            while ph > hi + 180: ph -= 360
            if not (lo <= ph <= hi):
                continue
            t = (ph - a0) / (a1 - a0)          # 0 tail .. 1 head
            rin = r_out - (r_out - r_in) * (0.25 + 0.75 * t ** 0.6)
            if rho < rin:
                continue
            k = (rho - rin) / max(0.5, r_out - rin)   # 0 inner .. 1 outer rim
            if t > 0.9:
                col, a = cols[3], alpha
            elif t > 0.7:
                col, a = (cols[3] if k > 0.6 else cols[2]), alpha
            elif t > 0.4:
                col, a = (cols[2] if k > 0.5 else cols[1]), int(alpha * 0.85)
            else:
                col, a = cols[1] if k > 0.6 else cols[0], int(alpha * 0.6)
                if dith and hash01(x, y, 11) > t * 2.2 + 0.15:
                    continue
            out.add((x, y))
            cv.glow([(x, y)], col, a, behind=behind)
    return out


def streak(cv, a, b, w=1.0, cols=("Q2", "Q3", "Q4"), alpha=255, behind=False):
    """A straight speed streak a -> b (thin at a, bright at b)."""
    out = set()
    pts = line(a, b)
    n = max(1, len(pts) - 1)
    for i, q in enumerate(pts):
        t = i / n
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        for o in range(-int(w * t), int(w * t) + 1):
            p = (q[0], q[1] + o) if abs(b[0] - a[0]) >= abs(b[1] - a[1]) else (q[0] + o, q[1])
            cv.glow([p], col, int(alpha * (0.5 + 0.5 * t)), behind=behind)
            out.add(p)
    return out


# ---------------------------------------------------------------- poses / tweening
def _ease(name, t):
    t = max(0.0, min(1.0, t))
    if name == "lin": return t
    if name == "in": return t * t
    if name == "out": return 1 - (1 - t) ** 2
    if name == "snap": return 1 - (1 - t) ** 3
    if name == "slam": return t ** 3
    return t * t * (3 - 2 * t)   # io


def mix(a, b, t):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return tuple(mix(x, y, t) for x, y in zip(a, b))
    return b if t >= 0.5 else a


def mixpose(p, q, t):
    out = dict(p)
    for k, v in q.items():
        out[k] = mix(p[k], v, t) if k in p else v
    return out


def seq(keys, loop=False):
    """ARRIVAL semantics.  keys: [{p: pose, n: frames, ms: per-frame ms, e: ease, + flags}].  The first key shows its
    pose for n frames.  Every later key takes n frames to ARRIVE at its pose from the previous one (the last of them is
    the pose itself); its flags (a=window, sm=smear, hold ...) belong to those arrival frames.  loop=True also tweens the
    last key back into the first (the first key's frames are then the arrival ones).  Returns [(ms, pose, flags)]."""
    out = []
    N = len(keys)
    order = list(range(N))
    for idx, i in enumerate(order):
        k = keys[i]
        n = k.get("n", 1)
        flags = {kk: vv for kk, vv in k.items() if kk not in ("p", "n", "ms", "e")}
        flags["_key"] = i
        prev = keys[i - 1] if (i > 0 or loop) else None
        for j in range(n):
            if prev is None:
                pose = dict(k["p"])
            else:
                pose = mixpose(prev["p"], k["p"], _ease(k.get("e", "io"), (j + 1) / n))
            out.append((k.get("ms", 80), pose, dict(flags)))
    return out


def add_sway(frames, keys=("hip",), k=0.35, decay=0.55, loop=False, field="sway", cap=6.0):
    """Cloth lag: sway = a decaying memory of how fast the body moved (px/frame), opposite to the motion."""
    def pos(p):
        v = p[keys[0]]
        return v if isinstance(v, tuple) else (v, 0)
    sw = (0.0, 0.0)
    passes = 2 if loop else 1
    for _ in range(passes):
        for i in range(len(frames)):
            prev = frames[i - 1][1] if i > 0 else (frames[-1][1] if loop else frames[0][1])
            a, b = pos(prev), pos(frames[i][1])
            vx, vy = b[0] - a[0], b[1] - a[1]
            sw = (sw[0] * decay - vx * k, sw[1] * decay - vy * k)
            sw = (max(-cap, min(cap, sw[0])), max(-cap, min(cap, sw[1])))
            frames[i][1][field] = sw
    return frames


# ---------------------------------------------------------------- export
def bbox_of(pts, pad=0):
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return [min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 1 + 2 * pad, max(ys) - min(ys) + 1 + 2 * pad]


def union(r, q):
    if r is None: return q
    if q is None: return r
    x0, y0 = min(r[0], q[0]), min(r[1], q[1])
    x1, y1 = max(r[0] + r[2], q[0] + q[2]), max(r[1] + r[3], q[1] + q[3])
    return [x0, y0, x1 - x0, y1 - y0]


BG = (52, 54, 62, 255)
CELL = (40, 42, 50, 255)


def preview(name, W, H, tags, flats, meta=None, scale=3, suffix=""):
    os.makedirs(PREVIEWS, exist_ok=True)
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 9
    sh = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), BG)
    d = ImageDraw.Draw(sh)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        att = (meta or {}).get("attacks", {}).get(t)
        wins = (att.get("windows") or [att]) if att else []
        d.text((4, y0 + 2), f"{t} ({b - a + 1})" + ("   " + "  ".join(f"{w['active']}" for w in wins) if wins else ""), fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), CELL)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            if meta:
                dd = ImageDraw.Draw(big)
                def rc(r_, col):
                    x, y, w, h = r_
                    dd.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=1)
                for w in wins:
                    if w["active"][0] <= i - a <= w["active"][1] and w.get("hit"):
                        rc(w["hit"], (255, 60, 60, 255))
            sh.alpha_composite(big, ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sh.save(os.path.join(PREVIEWS, f"{name}{suffix}.png"))


def export_sheet(name, W, H, anims, meta, build=True):
    """anims: [(tag, [(ms, img), ...])].  Writes assets/<name>.png/.json via Aseprite, <name>_meta.json, previews."""
    import asebuild
    frames, tags, flats = [], [], []
    for tag, frs in anims:
        a = len(frames)
        for ms, img in frs:
            assert img.size == (W, H), (name, tag, img.size)
            frames.append({"ms": int(ms), "cels": {"Body": img}})
            flats.append(img)
        tags.append((tag, a, len(frames) - 1))
    preview(name, W, H, tags, flats, meta)
    if meta is not None:
        with open(os.path.join(asebuild.ASSETS, f"{name}_meta.json"), "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
    if build:
        asebuild.build(name, W, H, ["Body"], frames, tags)
    return tags, flats
