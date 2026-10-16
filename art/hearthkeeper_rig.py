"""The Hearthkeeper -- production pixel rig (agent BOSS, v17 Cold Forge).  Used by art/gen_hearthkeeper.py.

Same family as art/venn_rig.py and the approved concept rig (art/concepts/forge/forge_rig.py): every part is a mask
with a per-pixel surface normal (capsules, domes, bevelled plates with fold fields, tubes); a material ramp is picked
from the lit normal; sel-out outline; a cool rim so the near-black keeper reads on dark rooms; warm point lights
(coals, a white-hot blade, the flame tongs) swap a pixel onto a warm-lit copy of its ramp, so he stays cold iron
except where his own fire reaches him.

Owner decisions built in: head A (veiled face, iron grate-bar crown) on B's tall flue cowl; the slim beaked hammer;
real forearms and gauntleted hands (no stick arms), soot sleeves that hang and trail with the motion.
Faces RIGHT.  Frame W x H, anchor (AX, AY) = the floor line under the feet.
"""
import math
from PIL import Image

W, H = 224, 144
AX, AY = 80, 139
FLOOR = AY - 1           # the last pixel row of the feet / hem
HIP_Y = AY - 45.0        # the idle hip height

# ---------------------------------------------------------------- palette
HEX = {
    "OUT": "#050609",
    "I0": "#08090d", "I1": "#11131b", "I2": "#1c1f2a", "I3": "#2b303d", "I4": "#434a5b", "I5": "#6f798d",
    "S0": "#060607", "S1": "#0c0c10", "S2": "#15151b", "S3": "#202028", "S4": "#2e2e39", "S5": "#454554",
    # the apron: one step darker than the concept (cold palette)
    "L0": "#0c0706", "L1": "#170d0b", "L2": "#251511", "L3": "#351f17", "L4": "#4a2c20", "L5": "#643e2c",
    "B0": "#17120c", "B1": "#2a2115", "B2": "#43341f", "B3": "#5f4a2d", "B4": "#82673e", "B5": "#a98a56",
    "K0": "#141317", "K1": "#232126", "K2": "#353236", "K3": "#4a4549", "K4": "#625b5d", "K5": "#7e7676",
    "E0": "#2a0a06", "E1": "#5a1409", "E2": "#962a0c", "E3": "#cf4c14", "E4": "#f07f24", "E5": "#ffb453",
    "E6": "#ffe2a0", "E7": "#fff8e8",
    "Q0": "#1d2630", "Q1": "#34424f", "Q2": "#56687a", "Q3": "#8496a8", "Q4": "#b8c6d2", "Q5": "#e2ebf2",
}
RGBA = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in HEX.items()}
MATS = "ISLBK"
RAMP = {m: [RGBA[f"{m}{i}"] for i in range(6)] for m in MATS}


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


WARM_TONE = (214, 92, 34)
WARM = {}
for _m in MATS:
    WARM[_m] = [_mix(RAMP[_m][i], WARM_TONE, 0.22 + 0.11 * i) for i in range(6)]
    WARM[_m] = [_mix(c, (255, 214, 150), max(0, i - 3) * 0.12) for i, c in enumerate(WARM[_m])]
SHINY = {"B": 0.86, "I": 0.93}
CONTRAST = {"I": 1.5, "B": 1.2}
MAT_LIFT = {"I": 1.1, "L": 0.55, "B": 0.9, "S": 0.25, "K": 0.4}
RIM = {"S": (4, 3), "I": (4, 3), "L": (3, 2)}
LIGHT = (-0.45, -0.78, 0.45)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)


# ---------------------------------------------------------------- geometry
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def unit(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def dirv(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
def perp(v): return (-v[1], v[0])
def ang(v): return math.degrees(math.atan2(v[1], v[0]))


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
    for _ in range(2000):
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


def tube_path(pts, radii):
    """Normals for one continuous tapered tube through a polyline (no seams between segments)."""
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
                k = min(0.95, d)
                l = math.hypot(ox, oy) or 1
                nm[q] = norm3(ox / l * k, oy / l * k, math.sqrt(1 - k * k) + 0.15)
    return nm


def ribbon(spine, widths, offset=0.0):
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


# ---------------------------------------------------------------- canvas
class Canvas:
    """One shaded figure: painter's-order parts, then shade + outline, then emissive FX on top."""

    def __init__(self, w=W, h=H):
        self.W, self.H = w, h
        self.px = {}
        self.fx = {}
        self.fxb = {}
        self.lights = []
        self.noout = set()
        self.tags = {}          # (x,y) -> set of part tags (for hit/hurt boxes)

    def inb(self, p):
        return 0 <= p[0] < self.W and 0 <= p[1] < self.H

    def paint(self, normals, mat, bias=0, ao=1, iline=False, tag=None):
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
            self.tags[p] = tag
        return new

    def flat(self, pts, mat, level, tag=None):
        for p in pts:
            p = ipt(p) if isinstance(p[0], float) else p
            if self.inb(p):
                self.px[p] = [mat, (0, 0, 1), 0, level, False]
                self.tags[p] = tag

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
            self.tags.pop(p, None)

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

    def render(self, ref_y=70, ydark=0.010, outline=True, rim=True):
        self.ref_y, self.ydark = ref_y, ydark
        for d_ in (self.px, self.fx, self.fxb):          # nothing below the floor line (a blade still in the coals)
            for q in [q for q in d_ if q[1] > FLOOR]:
                del d_[q]
        self.noout |= {(x, FLOOR + 1) for x in range(self.W)}
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


HEAT = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]


def heat_col(t):
    t = max(0.0, min(1.0, t))
    return HEAT[min(len(HEAT) - 1, int(t * (len(HEAT) - 0.01)))]


def halo(cv, mask, c="E3", a=130, r=1, behind=True):
    ring = set()
    for (x, y) in mask:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                q = (x + dx, y + dy)
                if q not in mask:
                    ring.add(q)
    cv.glow_under(ring, c, a, behind=behind)


def flame_tongues(cv, edge_pts, up, fi, seed, length=3.0, cols=("E3", "E4", "E5"), density=0.55, a=255, lean=(0, 0), behind=False):
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


# ================================================================ body proportions (identical in every frame)
L_TH, L_SH = 23.0, 22.0        # thigh, shin
L_UA, L_FA = 17.0, 16.5        # upper arm, forearm (long, gaunt -- but real forearms now)
SPINE = 32.0                   # hip -> neck
ARM_R = dict(ua0=3.6, ua1=3.0, fa0=3.1, fam=3.3, fa1=2.15)   # upper arm at the shoulder / elbow; forearm at the elbow / belly / wrist


def spine_frame(hip, neck):
    up = unit(sub(neck, hip))
    fwd = (-up[1], up[0])
    if fwd[0] < 0:
        fwd = (-fwd[0], -fwd[1])
    return up, fwd


def at(hip, neck, t, off):
    up, fwd = spine_frame(hip, neck)
    L = math.hypot(*sub(neck, hip))
    return add(add(hip, mul(up, L * t)), mul(fwd, off))


def limb(cv, pts, radii, mat="I", bias=0, ao=1, iline=False, tag=None):
    nm = tube_path(pts, radii)
    cv.paint(nm, mat, bias=bias, ao=ao, iline=iline, tag=tag)
    return nm


# ---------------------------------------------------------------- legs
def draw_leg(cv, hip, foot, bias=0, lift=0.0):
    knee = ik(hip, foot, L_TH, L_SH, (1, -0.15))
    ankle = add(foot, (0, -2.0))
    limb(cv, [hip, knee, ankle], [3.7, 2.7, 1.8], bias=bias, tag="body")
    d = unit(sub(ankle, knee))
    gv = [add(knee, mul(perp(d), -2.8)), add(knee, mul(perp(d), 2.6)), add(lerp(knee, ankle, 0.75), mul(perp(d), 1.9)),
          add(ankle, mul(perp(d), 1.3)), add(ankle, mul(perp(d), -1.6)), add(lerp(knee, ankle, 0.4), mul(perp(d), -2.6))]
    cv.paint(n_plate(poly_mask(gv), bevel=1.6, tilt=(0.25, -0.1), strength=1.3), "I", bias=bias, iline=True, tag="body")
    cv.paint(n_dome(add(knee, (0.8, -0.6)), 2.4, 2.6), "I", bias=bias, iline=True, tag="body")
    fx, fy = foot
    tip = -lift * 0.5     # a lifted foot points its toe down a little
    poly = [(fx - 2.6, fy - 3.4), (fx + 1.2, fy - 3.2), (fx + 5.6, fy - 1.0 + tip * 0.3), (fx + 8.2, fy + 0.4 + tip),
            (fx - 3.0, fy + 0.6)]
    cv.paint(n_plate(poly_mask(poly), bevel=1.4, tilt=(0.1, -0.5)), "I", bias=bias, iline=True, tag="body")
    cv.decal(line(add(knee, (-2.2, 3.4)), add(knee, (2.0, 2.8))), ("B", 3 if bias >= 0 else 2), only="I")
    return knee


# ---------------------------------------------------------------- arms: a sleeve, a real forearm, a gauntleted hand
def draw_hand(cv, wrist, hand, grip_dir, bias=0, mode="fist", spread=1.0):
    """mode 'fist': a gauntlet closed round a haft running along grip_dir through the hand centre (the haft is drawn
       first).  mode 'open': a reaching hand, fingers spread.  mode 'claw': half-closed (grabs, gestures)."""
    fd = unit(sub(hand, wrist))
    lv = 4 if bias >= 0 else 3
    if mode == "fist":
        g = unit(grip_dir)
        side = perp(g)
        if side[0] * fd[0] + side[1] * fd[1] < 0:
            side = (-side[0], -side[1])          # side: from the palm toward the knuckles (away from the wrist)
        # the back of the hand: a plate from the wrist to the knuckles
        bk = [add(wrist, mul(perp(fd), 1.9)), add(wrist, mul(perp(fd), -1.9)),
              add(add(hand, mul(side, 1.2)), mul(g, -2.3)), add(add(hand, mul(side, 1.2)), mul(g, 2.3))]
        cv.paint(n_plate(poly_mask(bk), bevel=1.2, tilt=(0, -0.2), strength=1.2), "I", bias=bias, ao=0, tag="hand")
        # the curled fingers: a thick rounded bar across the haft, split into knuckles
        a = add(hand, mul(g, -2.4)); b = add(hand, mul(g, 2.4))
        cv.paint(n_capsule(add(a, mul(side, 0.8)), add(b, mul(side, 0.8)), 2.25, 2.1), "I", bias=bias, iline=True, tag="hand")
        for k in (-1.2, 0.0, 1.2):
            q0 = add(add(hand, mul(g, k)), mul(side, -0.4)); q1 = add(q0, mul(side, 2.2))
            cv.decal(line(q0, q1), ("I", 1), only="I")
        cv.decal(line(add(add(hand, mul(side, 2.2)), mul(g, -1.9)), add(add(hand, mul(side, 2.2)), mul(g, 1.9))), ("I", lv), only="I")
        # the thumb wrapped over the haft on the near side
        th = add(add(hand, mul(side, -1.0)), mul(g, 2.0))
        cv.paint(n_capsule(add(hand, mul(side, -1.2)), th, 1.15, 1.0), "I", bias=bias, ao=0, tag="hand")
    else:
        pv = perp(fd)
        palm = [add(wrist, mul(pv, 1.9)), add(wrist, mul(pv, -1.9)), add(add(hand, mul(fd, 0.4)), mul(pv, -2.3)),
                add(add(hand, mul(fd, 0.6)), mul(pv, 2.3))]
        cv.paint(n_plate(poly_mask(palm), bevel=1.2, tilt=(0, -0.2), strength=1.2), "I", bias=bias, iline=True, tag="hand")
        base = add(hand, mul(fd, 0.5))
        for k in range(3):
            off = (k - 1) * 1.5 * spread
            a = add(base, mul(pv, off))
            curl = 0.0 if mode == "open" else 52.0
            d1 = unit(rot(fd, (k - 1) * 10 * spread))
            m1 = add(a, mul(d1, 2.6))
            d2 = unit(rot(d1, curl))
            m2 = add(m1, mul(d2, 2.0))
            d3 = unit(rot(d2, curl * 0.8))
            tip = add(m2, mul(d3, 1.4))
            cv.paint(tube_path([a, m1, m2, tip], [1.0, 0.9, 0.75, 0.5]), "I", bias=bias, ao=0, tag="hand")
        thd = unit(rot(fd, -60 if mode == "open" else -85))
        t0 = add(lerp(wrist, hand, 0.55), mul(pv, -1.8))
        cv.paint(tube_path([t0, add(t0, mul(thd, 2.2)), add(add(t0, mul(thd, 2.2)), mul(rot(thd, 30), 1.6))], [1.05, 0.85, 0.55]),
                 "I", bias=bias, ao=0, tag="hand")


def draw_sleeve(cv, sh, el, wrist, hang, bias=0, fire=0.0, fi=0, length=1.0):
    """A wide soot bell-sleeve: it wraps the upper arm loosely and opens past the elbow; its mouth and the long lower
    edge hang along `hang` (gravity + the lag of the arm's own motion), so the cloth swings and trails the limb."""
    du = unit(sub(el, sh))
    a1 = perp(du)
    if a1[1] < 0 or (abs(a1[1]) < 0.15 and a1[0] < 0):
        a1 = (-a1[0], -a1[1])                    # a1: the lower side of the upper arm (where cloth falls)
    hv = unit(hang)
    fdir = unit(sub(wrist, el))
    mouth = lerp(el, wrist, 0.30)                # the sleeve's mouth rings the forearm here
    fp = perp(fdir)
    if fp[0] * a1[0] + fp[1] * a1[1] < 0:
        fp = (-fp[0], -fp[1])                    # fp: the forearm's lower side
    drop = (12.0 if du[1] > -0.3 else 8.0) * length
    m_lo = add(mouth, mul(fp, 5.2))              # lower lip of the mouth, pulled down by gravity
    m_hi = add(mouth, mul(fp, -4.2))
    tail = add(add(lerp(el, m_lo, 0.5), mul(a1, 3.0)), mul(hv, drop))     # the hanging point of the bell
    poly = [add(sh, mul(a1, -4.3)), add(lerp(sh, el, 0.55), mul(a1, -4.4)), add(el, mul(a1, -4.1)), m_hi,
            add(m_lo, mul(hv, 2.0)), add(lerp(m_lo, tail, 0.5), mul(perp(hv), -0.8)), tail,
            add(lerp(el, sh, 0.35), add(mul(a1, 5.0), mul(hv, drop * 0.45))), add(lerp(sh, el, 0.15), mul(a1, 4.6))]
    m = poly_mask(poly)
    cv.paint(n_plate(m, bevel=2.0, tilt=(-0.1, -0.15), strength=1.0,
                     fold=lambda x, y: (0.28 * math.sin((x - sh[0]) * 0.55 + (y - sh[1]) * 0.35), 0.0)), "S", bias=bias, iline=True, tag="body")
    # folds: one crease down the hanging bell, the dark inside of the mouth
    cv.decal(line(lerp(el, sh, 0.2), lerp(tail, m_lo, 0.3)), ("S", 1), only="S")
    cv.decal(line(add(m_hi, mul(fdir, -0.6)), add(m_lo, mul(fdir, -0.6))), ("S", 0), only="S")
    if fire > 0:
        flame_tongues(cv, {q for q in edge_of(m) if dist(q, tail) < 6}, (0, -1), fi, 47, length=1.5 + 2 * fire,
                      cols=("E2", "E3", "E4"), density=0.3)
    return m


def draw_arm(cv, sh, hand, pref, bias=0, mode="fist", grip=(0, 1), hang=(0, 1), fire=0.0, fi=0, spread=1.0, sleeve=1.0):
    el = ik(sh, hand, L_UA, L_FA, pref)
    d = unit(sub(hand, el))
    wrist = sub(hand, mul(d, 2.6 if mode == "fist" else 2.0))
    R = ARM_R
    limb(cv, [sh, el], [R["ua0"], R["ua1"]], bias=bias, iline=True, tag="body")
    belly = lerp(el, wrist, 0.32)
    limb(cv, [el, belly, wrist], [R["fa0"], R["fam"], R["fa1"]], mat="K", bias=bias, iline=True, tag="arm")
    pv = perp(d)
    if pv[1] > 0 or (abs(pv[1]) < 0.15 and pv[0] < 0):
        pv = (-pv[0], -pv[1])     # the outer (upper) side of the forearm
    # vambrace: a long plate over the outer forearm, wide under the sleeve, narrowing to a flared cuff at the wrist
    c0 = lerp(el, wrist, 0.10); c1 = lerp(el, wrist, 0.92)
    vb = [add(c0, mul(pv, 3.8)), add(lerp(c0, c1, 0.45), mul(pv, 3.9)), add(c1, mul(pv, 2.8)), add(add(c1, mul(d, 1.3)), mul(pv, 3.2)),
          add(add(c1, mul(d, 1.3)), mul(pv, -2.5)), add(c1, mul(pv, -1.9)), add(lerp(c0, c1, 0.45), mul(pv, -2.6)), add(c0, mul(pv, -2.8))]
    cv.paint(n_plate(poly_mask(vb), bevel=1.5, tilt=(0.0, -0.25), strength=1.35), "I", bias=bias, iline=True, tag="arm")
    lv = 4 if bias >= 0 else 3
    cv.decal(line(add(lerp(c0, c1, 0.1), mul(pv, 3.0)), add(lerp(c0, c1, 0.95), mul(pv, 2.3))), ("I", lv), only="I")
    cv.decal(line(add(lerp(c0, c1, 0.62), mul(pv, 3.0)), add(lerp(c0, c1, 0.62), mul(pv, -1.8))), ("I", 1), only="I")
    cv.decal(line(add(c1, mul(pv, 2.4)), add(c1, mul(pv, -1.5))), ("B", 3 if bias >= 0 else 2), only="I")
    # the elbow: a cop with a short back spur (reads the bend in silhouette)
    back = unit(add(unit(sub(el, hand)), unit(sub(el, sh))))
    cv.paint(n_dome(add(el, mul(back, 0.6)), 2.5, 2.5), "I", bias=bias, iline=True, tag="arm")
    limb(cv, [add(el, mul(back, 1.5)), add(el, mul(back, 4.2))], [1.5, 0.4], bias=bias, ao=0, tag="arm")
    if sleeve:
        draw_sleeve(cv, sh, el, wrist, hang, bias=bias, fire=fire, fi=fi, length=sleeve)
    draw_hand(cv, wrist, hand, grip, bias=bias, mode=mode, spread=spread)
    return dict(el=el, wrist=wrist)


def draw_pauldron(cv, sh, bias=0, scale=1.0, lift=0.0):
    """Swept, layered shoulder plate (head A's): rides up with a raised arm (lift 0..1)."""
    s = scale
    raw = [(4.2, 2.2), (4.6, -0.8), (2.6, -3.4), (-1.0, -4.8), (-4.4, -6.2), (-7.4, -8.6), (-5.8, -4.6),
           (-4.6, -1.4), (-3.6, 2.4), (-0.6, 4.2), (2.6, 3.8)]
    pts = [rot((x * s, y * s), -lift * 14) for x, y in raw]
    sh = add(sh, (0, -lift * 1.5))
    poly = [add(sh, p) for p in pts]
    cv.paint(n_plate(poly_mask(poly), bevel=2.6, tilt=(-0.1, -0.35), strength=1.3), "I", bias=bias, iline=True, tag="body")
    pts2 = [rot(p, -lift * 14) for p in ((-3.8 * s, 3.0 * s), (3.4 * s, 3.0 * s), (2.6 * s, 5.4 * s), (-2.6 * s, 5.0 * s))]
    cv.paint(n_plate(poly_mask([add(sh, p) for p in pts2]), bevel=1.2, tilt=(0, -0.2)), "I", bias=bias - 1, tag="body")
    rim = [rot(p, -lift * 14) for p in ((-3.4 * s, 2.2 * s), (-0.6 * s, 3.8 * s), (2.4 * s, 3.4 * s), (4.0 * s, 1.8 * s))]
    cv.decal(polyline([add(sh, p) for p in rim]), ("B", 3 if bias >= 0 else 2), only="I")
    ridge = [rot(p, -lift * 14) for p in ((3.0 * s, -0.6 * s), (0.0, -2.6 * s), (-3.6 * s, -4.4 * s), (-6.0 * s, -6.8 * s))]
    cv.decal(polyline([add(sh, p) for p in ridge]), ("I", 5 if bias >= 0 else 4), only="I")


# ---------------------------------------------------------------- torso, apron, robe, ring of keys
def draw_torso(cv, hip, neck, glow=0.0):
    prof_f = [(0.0, 3.6), (0.22, 3.1), (0.45, 4.6), (0.62, 5.6), (0.8, 5.2), (0.92, 3.6), (1.0, 2.0)]
    prof_b = [(1.0, -2.2), (0.9, -5.2), (0.7, -5.4), (0.45, -4.0), (0.22, -3.4), (0.0, -4.2)]
    poly = [at(hip, neck, t, o) for t, o in prof_f + prof_b]
    m = poly_mask(poly)
    cv.paint(n_plate(m, bevel=5.0, tilt=(0.05, -0.1), strength=1.4), "I", iline=True, tag="body")
    for t in (0.14, 0.26, 0.38):
        cv.decal(line(at(hip, neck, t, -3.0), at(hip, neck, t + 0.02, 3.2)), ("I", 1), only="I")
    cv.decal(polyline([at(hip, neck, 0.9, -4.0), at(hip, neck, 0.86, 0.0), at(hip, neck, 0.9, 3.6)]), ("B", 3), only="I")
    if glow > 0:     # the hearth in his chest (P3): a grate of light between the plates
        for t in (0.62, 0.7):
            cv.glow(line(at(hip, neck, t, 1.5), at(hip, neck, t, 3.4)), heat_col(0.2 + 0.4 * glow), 190 if glow > 0.5 else 130)
    return m


def draw_apron(cv, hip, neck, knee_n, knee_f, hem_y, sway=0.0):
    top_l = at(hip, neck, 0.06, -2.4)
    top_r = at(hip, neck, 0.06, 4.4)
    bl = (min(knee_f[0], knee_n[0]) - 1.5 + sway * 0.5, hem_y + 1)
    br = (max(knee_n[0], knee_f[0]) + 5.0 + sway, hem_y - 1)
    mid_l = lerp(top_l, bl, 0.5); mid_l = (mid_l[0] - 1.0, mid_l[1])
    mid_r = lerp(top_r, br, 0.5); mid_r = (mid_r[0] + 1.0, mid_r[1])
    hem = []
    n = 9
    for i in range(n + 1):
        t = i / n
        p = lerp(br, bl, t)
        dip = (1.6 if i % 3 == 1 else 0.0) + (0.8 if i % 4 == 2 else 0.0)
        hem.append((p[0], p[1] + dip))
    poly = [top_l, top_r, mid_r] + hem + [mid_l]
    m = poly_mask(poly)
    cx = (top_l[0] + top_r[0]) / 2
    cv.paint(n_plate(m, bevel=2.0, tilt=(0.05, -0.05), strength=1.0,
                     fold=lambda x, y: (0.55 * math.sin((x - cx) * 0.95 + (y - hip[1]) * 0.08), 0.0)), "L", iline=True, tag="body")
    sp_top = at(hip, neck, 0.0, 1.2)
    sp_bot = ((bl[0] + br[0]) / 2 + 0.5, hem_y + 1.5)
    cv.decal(line(lerp(sp_top, sp_bot, 0.45), sp_bot), ("L", 0), only="L")
    cv.decal([p for i, p in enumerate(line(sp_top, lerp(sp_top, sp_bot, 0.45))) if i % 2 == 0], ("L", 1), only="L")
    for (x, y) in m:
        if y > hem_y - 3 and hash01(x, y, 7) > 0.55:
            cv.decal([(x, y)], ("L", 1), only="L")
    bt = [at(hip, neck, 0.05, -1.6), at(hip, neck, 0.05, 4.2), at(hip, neck, 0.62, 4.6), at(hip, neck, 0.66, 0.4)]
    cv.paint(n_plate(poly_mask(bt), bevel=1.6, tilt=(0.1, -0.15), strength=0.9), "L", iline=True, tag="body")
    cv.paint({q: (0.1, -0.5, 0.86) for q in line(at(hip, neck, 0.66, 0.6), at(hip, neck, 0.95, -1.2))}, "L", ao=0, tag="body")
    for q in (at(hip, neck, 0.6, 3.6), at(hip, neck, 0.63, 1.2)):
        cv.flat([ipt(q)], "B", 4)
    bl0 = at(hip, neck, 0.1, -4.4); br0 = at(hip, neck, 0.1, 4.6)
    belt = poly_mask([add(bl0, (0, -1.2)), add(br0, (0, -1.2)), add(br0, (0, 1.0)), add(bl0, (0, 1.0))])
    cv.paint(n_plate(belt, bevel=1.0, tilt=(0, -0.1)), "L", bias=-1, tag="body")
    cv.paint(n_dome(at(hip, neck, 0.1, 2.0), 1.3, 1.4), "B", tag="body")
    return m


def draw_ring(cv, c, bias=0, sway=0.0):
    ring = {q for q in mask_disc(c, 3.3) if q not in mask_disc(c, 2.0)}
    cv.paint({q: norm3((q[0] + .5 - c[0]) * 0.3, (q[1] + .5 - c[1]) * 0.3, 1) for q in ring}, "I", bias=bias)
    items = [(-2.6, 8, "key"), (-0.6, 10, "tong"), (1.2, 7, "key"), (2.8, 9, "key"), (-1.8, 6, "key")]
    for i, (ox, ln, kind) in enumerate(items):
        a = (c[0] + ox, c[1] + 2.6)
        an = 90 + ox * 7 + sway * 6 * (1 + 0.2 * i)
        d = dirv(an)
        b = add(a, mul(d, ln))
        if kind == "key":
            cv.paint({q: (0.2, -0.3, 0.9) for q in line(a, b)}, "B", bias=bias - 1, ao=0)
            cv.paint({q: (0.3, -0.2, 0.9) for q in line(add(b, mul(d, -1.5)), add(b, mul(perp(d), 1.2)))}, "B", bias=bias - 1, ao=0)
        else:
            pv = add(a, mul(d, ln * 0.45))
            for s in (-1, 1):
                end = add(pv, add(mul(d, ln * 0.55), mul(perp(d), s * 1.6)))
                cv.paint({q: (0.0, -0.3, 0.9) for q in line(a, pv) + line(pv, end)}, "I", bias=bias, ao=0)


def draw_robe(cv, hip, neck, front_x, back_x, hem_y=FLOOR, wind=0.0, fire=0.0, fi=0, flare=1.0, lift=0.0):
    wl = at(hip, neck, 0.12, -4.6)
    wr = at(hip, neck, 0.12, 3.8)
    hb = (back_x - wind, hem_y + 0.5 - lift)
    hf = (front_x, hem_y + 0.5 - lift * 0.6)
    back = bezier(wl, add(wl, (-4.0 * flare, 14)), (hb[0] + 3.0, hb[1] - 16), hb, 18)
    front = bezier(hf, (hf[0] - 1.0, hf[1] - 14), add(wr, (2.5, 12)), wr, 18)
    rag = []
    m = 9
    for k in range(m + 1):
        t = k / m
        p = lerp(hb, hf, t)
        rag.append((p[0] + (hash01(k, 1, 23) - 0.5) * 1.2, p[1] + (0.6 if k % 2 else -1.6 - 1.4 * hash01(k, 2, 23)) * (1 - t * 0.6)))
    poly = back + rag[1:-1] + front
    mk = poly_mask(poly)
    mk = {q for q in mk if q[1] <= FLOOR}
    cx = (wl[0] + wr[0]) / 2
    cv.paint(n_plate(mk, bevel=2.6, tilt=(-0.05, 0.05), strength=1.0,
                     fold=lambda x, y: (0.65 * math.sin((x - cx) * 0.7 + (y - hip[1]) * 0.06 + fi * 0.2) * min(1, max(0, (y - hip[1])) / 20), 0.0)),
             "S", bias=-1, tag="body")
    if fire > 0:
        edge = {q for q in edge_of(mk) if q[1] > hem_y - 6}
        flame_tongues(cv, edge, (0, -1), fi, 44, length=1.5 + 3.0 * fire, cols=("E2", "E3", "E4", "E5"), density=0.3)
    return mk


def draw_veil_back(cv, top, hem_y, wind=0.0, fire=0.0, fi=0, width=1.3):
    """The soot veil: falls from the cowl down the back to the waist, trailing with the wind."""
    n = 14
    sp = []
    for i in range(n + 1):
        t = i / n
        x = top[0] - 3.0 * t - (3.0 + wind * 0.8) * t * t
        y = top[1] + (hem_y - top[1]) * t - abs(wind) * 0.15 * t * t * 6
        sp.append((x, y))
    w = [width * (2.4 + 3.4 * (i / n) ** 0.7) for i in range(n + 1)]
    L, Rr = [], []
    for i, c in enumerate(sp):
        a = sp[max(0, i - 1)]; b = sp[min(n, i + 1)]
        nv = perp(unit(sub(b, a)))
        L.append(add(c, mul(nv, w[i] * 0.95)))
        Rr.append(add(c, mul(nv, -w[i] * 0.55)))
    rag = []
    for k in range(6):
        p = lerp(L[-1], Rr[-1], k / 5)
        rag.append((p[0], p[1] + (3.5 if k % 2 == 1 else 0.3)))
    mk = poly_mask(L + rag + list(reversed(Rr)))
    cv.paint(n_plate(mk, bevel=2.0, tilt=(-0.2, -0.05), strength=1.1,
                     fold=lambda x, y: (0.5 * math.sin((x - top[0]) * 1.1 + (y - top[1]) * 0.15), 0.0)), "S", tag="body")
    if fire > 0:
        edge = {q for q in edge_of(mk) if q[1] > top[1] + 10}
        flame_tongues(cv, edge, (0, -1), fi, 43, length=1.5 + 2.5 * fire, cols=("E2", "E3", "E4", "E5"), density=0.18)
    return mk


# ---------------------------------------------------------------- the head: B's flue cowl ringed by A's grate crown, veiled face
def draw_head(cv, hd, tilt=0.0, eyes=0.55, fire=0.0, fi=0, crown_hot=0.0):
    def R(p):
        return add(hd, rot(p, tilt))
    ring_c = R((-0.9, -4.4))
    RX, RY = 5.0, 1.4

    def ring_pt(a):
        return add(ring_c, rot((math.cos(math.radians(a)) * RX, math.sin(math.radians(a)) * RY), tilt))
    bars = ((200, 4.5), (235, 5.5), (305, 6.0), (340, 5.0), (25, 6.5), (70, 8.0), (115, 7.0), (155, 5.5))

    def draw_bars(front):
        for a, hgt in bars:
            is_front = 0 < a < 180
            if is_front != front:
                continue
            base = ring_pt(a)
            lean = math.cos(math.radians(a)) * 2.0
            tip = add(base, rot((lean, -hgt), tilt))
            pts = line(base, tip)
            cv.flat(pts, "I", (4 if math.cos(math.radians(a)) < 0.3 else 3) if front else 2, tag="crown")
            cv.flat(pts[-1:], "I", 5 if front else 3, tag="crown")
            if crown_hot > 0:
                cv.glow([ipt(tip)], "E6" if (crown_hot > 0.5 and front) else "E4")
                cv.glow([add(ipt(tip), (0, -1))], "E4" if front else "E3", 190)
                if front and crown_hot > 0.3:
                    cv.glow([add(ipt(tip), (0, -2))], "E3", 130)
    # back half of the ring and its bars, behind the cowl
    cv.flat([ipt(ring_pt(a)) for a in range(180, 360, 8)], "I", 2, tag="crown")
    draw_bars(False)
    # the flue cowl: a tall soot hood rising to a blunt chimney point, leaning back a little
    cowl = [R((-6.0, 6.6)), R((-5.6, 1.0)), R((-4.7, -4.0)), R((-3.9, -9.5)), R((-3.6, -15.0)), R((-3.7, -20.0)),
            R((-3.4, -23.2)), R((-2.0, -23.0)), R((-1.5, -19.0)), R((-0.6, -13.6)), R((0.9, -8.8)), R((2.8, -5.2)),
            R((3.8, -2.4)), R((4.2, 1.0)), R((3.8, 4.6)), R((2.2, 7.6)), R((-1.6, 8.4))]
    m = poly_mask(cowl)
    cv.paint(n_plate(m, bevel=2.4, tilt=(-0.1, -0.25), strength=1.2,
                     fold=lambda x, y: (0.32 * math.sin((x - hd[0]) * 1.3 + (y - hd[1]) * 0.2), 0.0)), "S", iline=True, tag="head")
    # the veiled face: cloth over a narrow helm -- brow and nose ridge press through it as lit folds
    cv.decal(line(R((0.6, -3.2)), R((3.4, -2.6))), ("S", 5), only="S")
    cv.decal(line(R((3.6, -0.6)), R((3.8, 2.8))), ("S", 4), only="S")
    cv.decal(line(R((1.4, 3.2)), R((2.0, 7.0))), ("S", 1), only="S")
    cv.decal(line(R((-2.4, -18.0)), R((-0.8, -6.0))), ("S", 1), only="S")     # the cowl's crease
    cv.decal(line(R((-3.0, -21.5)), R((-2.0, -21.8))), ("S", 4), only="S")    # the flue's lip
    # the eye-light burning through the veil: a hot slit with a dim bleed
    ecol = "E6" if eyes > 0.8 else ("E5" if eyes > 0.5 else ("E4" if eyes > 0.2 else "E2"))
    slit = line(R((1.4, -1.4)), R((3.6, -1.6)))
    if eyes > 0.05:
        cv.glow([add(q, (0, 1)) for q in slit[1:]], "E2", 190 if eyes > 0.3 else 120)
        cv.glow([add(q, (0, -1)) for q in slit[1:-1]], "E1", 190 if eyes > 0.3 else 120)
        cv.glow(slit, ecol)
        if eyes > 0.75:
            cv.glow([ipt(R((4.8, -1.7)))], "E4", 130)
    if fire > 0:      # P3: the flue vents a thin wisp of fire
        tipc = R((-2.8, -24.0))
        cv.glow([ipt(tipc)], "E5")
        cv.glow([ipt(add(tipc, (0, -1)))], "E4", 190)
        if fi % 2 == 0:
            cv.glow([ipt(add(tipc, (-1, -2)))], "E3", 130)
    # front half of the crown ring over the cowl, bronze on its lit side, then its bars
    front_half = [ring_pt(a) for a in range(0, 181, 8)]
    cv.flat([ipt(q) for q in front_half], "I", 4, tag="crown")
    cv.decal([ipt(q) for q in front_half if q[0] < ring_c[0]], ("B", 4))
    draw_bars(True)
    return m


# ---------------------------------------------------------------- weapons
def draw_hammer(cv, grip, an, below=6.0, above=34.0, bias=0, heat=0.0, flip=1, size=1.25, tag="weapon"):
    """The slim beaked forge hammer: smooth haft, a slim head with a flat striking face and a long curved beak.
    an = haft direction butt -> head (deg).  flip chooses which side the face is on (1: the face leads a forward swing)."""
    d = dirv(an)
    butt = sub(grip, mul(d, below))
    head = add(grip, mul(d, above))
    cv.paint(tube_path([butt, head], [1.3, 1.15]), "I", bias=bias, ao=0, tag=tag)
    cv.paint(n_dome(butt, 1.7, 1.7), "I", bias=bias, tag=tag)
    for t in (0.55,):
        q = lerp(butt, head, t)
        cv.paint(n_capsule(add(q, mul(d, -0.8)), add(q, mul(d, 0.8)), 1.6), "I", bias=bias, tag=tag)
    v = mul(perp(d), flip)
    sp = []
    for i in range(13):
        t = i / 12
        s = (5.0 - 15.5 * t) * size
        bend = -1.2 * max(0.0, -s - 3) ** 1.5 / 12.0
        sp.append(add(head, add(mul(v, s), mul(d, bend))))
    widths = [(2.9 if i < 4 else 2.9 - (i - 3) * 0.27) * size for i in range(13)]
    m = poly_mask(ribbon(sp, widths))
    cv.paint(n_plate(m, bevel=1.6, tilt=(-0.15, -0.25), strength=1.6), "I", bias=bias, iline=True, tag=tag)
    cv.decal(line(add(head, add(mul(v, -0.8), mul(d, 2.6))), add(head, add(mul(v, -0.8), mul(d, -2.6)))),
             ("B", 3 if bias >= 0 else 2), only="I")
    face = [q for q in m if (q[0] + .5 - head[0]) * v[0] + (q[1] + .5 - head[1]) * v[1] > 3.6 * size]
    if heat > 0:
        cv.glow(face, heat_col(heat * 0.7))
    else:
        cv.decal(face, ("I", 4), only="I")
    beak = sp[-1]
    return dict(butt=butt, head=head, m=m, face=set(face), tip=add(head, mul(v, 5.0 * size)), beak=beak, d=d)


def draw_tongs(cv, hand, an, ln=30.0, open_=5.0, bias=0, heat=0.0, coal=0.0, fi=0, tag="tongs"):
    """Long smith's tongs: two reins meeting at a rivet, beak jaws.  coal > 0: a white coal held in the jaws."""
    d = dirv(an)
    v = perp(d)
    piv = add(hand, mul(d, ln * 0.62))
    tips, allp = [], set()
    for s in (-1, 1):
        rein0 = add(hand, mul(v, s * 1.7))
        rein1 = add(piv, mul(v, s * 0.5))
        jaw_mid = add(add(piv, mul(d, ln * 0.20)), mul(v, s * (1.6 + open_ * 0.5)))
        jaw_tip = add(add(piv, mul(d, ln * 0.40)), mul(v, s * (0.4 + open_ * 0.42)))
        nm = tube_path([rein0, lerp(rein0, rein1, 0.5), rein1], [0.7, 0.6, 0.75])
        nm.update(tube_path(qbez(rein1, jaw_mid, jaw_tip, 10), [1.2] * 6 + [1.0] * 5))
        cv.paint(nm, "I", bias=bias, ao=0, tag=tag)
        allp |= set(nm)
        tips.append(jaw_tip)
    cv.paint(n_dome(piv, 1.3, 1.3), "B", bias=bias, tag=tag)
    if heat > 0:
        jaws = {q for q in allp if (q[0] + .5 - piv[0]) * d[0] + (q[1] + .5 - piv[1]) * d[1] > -ln * 0.15 * (1 - heat)}
        cv.glow(jaws, heat_col(heat), 255)
        halo(cv, jaws, "E3", 130)
    mid = lerp(*tips, 0.5)
    if coal > 0:
        c = add(mid, mul(d, -1.2))
        r = 2.4 + 0.6 * coal
        core = mask_disc(c, r)
        cv.glow(core, "E7")
        cv.glow(mask_disc(add(c, (-0.6, 0.6)), r * 0.55), "E6")
        halo(cv, core, "E5", 220, behind=False)
        halo(cv, core | {q for q in mask_disc(c, r + 1)}, "E3", 110, r=2, behind=False)
        for k in range(4):        # a few licks of flame off the coal
            a = -90 + (hash01(k, fi, 3) - 0.5) * 70
            ln2 = 2 + 3 * hash01(k, fi, 4) * coal
            p0 = add(c, mul(dirv(a), r))
            cv.glow(line(p0, add(p0, mul(dirv(a), ln2))), "E5" if k % 2 else "E4", 255)
        cv.lights.append((c, 46.0, 1.1))
    return dict(piv=piv, tips=tips, mid=mid, px=allp, d=d)


def draw_blade(cv, hilt, an, ln=46.0, curve=-3.5, heat=1.0, width=2.6, tag="weapon"):
    """A long blade pulled white-hot from the coals: dark hilt, the steel glowing, white along the edge."""
    d = dirv(an)
    v = perp(d)
    pom = sub(hilt, mul(d, 6.0))
    cv.paint(n_capsule(pom, add(hilt, mul(d, 1.0)), 1.15), "I", tag=tag)
    cv.paint(n_dome(pom, 1.5, 1.5), "B", tag=tag)
    g0 = add(add(hilt, mul(d, 1.5)), mul(v, 4.2)); g1 = add(add(hilt, mul(d, 1.5)), mul(v, -4.2))
    cv.paint(n_capsule(g0, g1, 1.2, 1.0), "I", tag=tag)
    base = add(hilt, mul(d, 2.5))
    tip = add(base, mul(d, ln))
    ctrl = add(lerp(base, tip, 0.55), mul(v, curve))
    sp = qbez(base, ctrl, tip, 30)
    widths = [width * (1.0 - 0.75 * (i / 30) ** 1.6) for i in range(31)]
    m = poly_mask(ribbon(sp, widths))
    for q in m:
        best, bi = 1e9, 0
        for i in range(0, 31, 2):
            dd = (sp[i][0] - q[0] - .5) ** 2 + (sp[i][1] - q[1] - .5) ** 2
            if dd < best:
                best, bi = dd, i
        t = bi / 30
        side = (q[0] + .5 - sp[bi][0]) * v[0] + (q[1] + .5 - sp[bi][1]) * v[1]
        e = 0.35 + 0.55 * t * heat + (0.25 if side > 0.6 else 0.0) - (0.15 if side < -0.8 else 0)
        if hash01(*q, 31) > 0.9:
            e -= 0.18
        cv.glow([q], heat_col(e * heat))
    halo(cv, m, "E3", 190)
    halo(cv, m, "E2", 70, r=2)
    cv.lights.append((lerp(base, tip, 0.6), 34.0, 0.9 * heat))
    return dict(m=m, sp=sp, tip=tip, base=base, head=tip)


def draw_spear(cv, grip, an, below=16.0, ln=58.0, heat=1.0, tag="weapon"):
    d = dirv(an)
    butt = sub(grip, mul(d, below))
    tipb = add(butt, mul(d, ln - 12))
    cv.paint(tube_path([butt, tipb], [1.05, 0.95]), "I", ao=0, tag=tag)
    cv.paint(n_dome(butt, 1.35, 1.35), "B", tag=tag)
    sp = [add(tipb, mul(d, i * 1.0)) for i in range(13)]
    w = [0.8 + 1.8 * math.sin(math.pi * min(1, (i / 12) * 1.15)) * (1 - i / 14) for i in range(13)]
    m = poly_mask(ribbon(sp, w))
    for q in m:
        t = ((q[0] + .5 - tipb[0]) * d[0] + (q[1] + .5 - tipb[1]) * d[1]) / 12
        cv.glow([q], heat_col(0.45 + 0.55 * t * heat))
    for i in range(22):
        cv.glow([add(tipb, mul(d, -i))], heat_col(0.5 - i * 0.022), 255 if i < 8 else 190)
    halo(cv, m, "E3", 190)
    halo(cv, m, "E2", 70, r=2)
    tip = add(tipb, mul(d, 12))
    cv.lights.append((tipb, 26.0, 0.8 * heat))
    return dict(m=m, tip=tip, head=tip, butt=butt)


def draw_chain(cv, hand, tip, bend=0.0, heat=1.0, fi=0, slack=0.0):
    """A chain pulled glowing from the coals, a hooked weight at the end.  The path is a smooth curve from the hand to
    the tip, bowed by `bend` (signed, px) and sagging by `slack`."""
    d = sub(tip, hand)
    L = math.hypot(*d) or 1
    nv = perp(unit(d))
    c1 = add(add(lerp(hand, tip, 0.33), mul(nv, bend * 0.9)), (0, slack))
    c2 = add(add(lerp(hand, tip, 0.70), mul(nv, bend * 0.7)), (0, slack * 0.6))
    path = bezier(hand, c1, c2, tip, max(24, int(L / 1.5)))
    pts = set()
    acc = 0.0
    k = 0
    for a, b in zip(path, path[1:]):
        seg = dist(a, b)
        acc += seg
        if acc >= 2.6:
            acc = 0.0
            k += 1
            c = b
            dd = unit(sub(b, a))
            t = k * 2.6 / L
            if k % 2 == 0:
                ring = set()
                for q in ((-1.6, 0), (1.6, 0), (-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (0, -1.2), (0, 1.2)):
                    rq = (q[0] * dd[0] - q[1] * dd[1], q[0] * dd[1] + q[1] * dd[0])
                    ring.add(ipt(add(c, rq)))
            else:
                ring = set(line(sub(c, mul(dd, 1.5)), add(c, mul(dd, 1.5))))
            cv.glow(ring, heat_col((0.42 + 0.48 * min(1, t)) * heat))
            pts |= ring
    # the hooked weight
    dd = unit(sub(path[-1], path[-4]))
    nv2 = perp(dd)
    hk = [add(tip, add(mul(dd, a), mul(nv2, b))) for a, b in ((-2, -2), (1.5, -2.6), (3.6, 0.5), (2.2, 3.6), (-0.8, 3.8), (-2.8, 1.0))]
    m = poly_mask(hk)
    cv.glow(m, "E6")
    barb = line(add(tip, add(mul(dd, 2.2), mul(nv2, 3.6))), add(tip, add(mul(dd, 5.0), mul(nv2, 1.2))))
    cv.glow(barb, "E5")
    halo(cv, m | set(barb), "E3", 190)
    halo(cv, pts, "E2", 90)
    cv.lights.append((tip, 26.0, 0.9 * heat))
    return dict(m=m | pts | set(barb), tip=tip, head=tip, path=path)


# ================================================================ the figure
def figure(p, phase, fi=0, nofx=False):
    """Render one frame.  p: a fully resolved pose (see gen_hearthkeeper.resolve).  Returns (image, info)."""
    cv = Canvas()
    hip = (p["hx"], p["hy"])
    neck = add(hip, rot((0, -SPINE), p["lean"]))
    hd = add(neck, rot((1.0, -7.4), p["lean"] + p["tilt"]))
    sh_n = add(at(hip, neck, 0.9, 1.4), (0.4, 0.6))
    sh_f = at(hip, neck, 0.93, -3.6)
    hip_n = add(hip, (1.6, 0.5)); hip_f = add(hip, (-2.0, -0.5))
    fire = p.get("fire", 0.0)
    wind = p.get("wind", 0.0)
    for L in p.get("lights", []):
        cv.lights.append(L)
    info = {"hip": hip, "neck": neck, "head": hd, "sh_n": sh_n, "sh_f": sh_f}
    W_ = p.get("weapon")           # 'hammer' | 'blade' | 'spear' | 'chain' | 'ftongs' | None
    hn, hf = p["hn"], p["hf"]
    # the weapon in the near hand (drawn behind the body when 'wb', else between the body and the near arm)
    wres = {}

    def near_weapon():
        if W_ == "hammer" and p.get("wfree"):          # let go: the hammer stays where it was driven in
            gx, gy, wa_ = p["wfree"]
            wres.update(draw_hammer(cv, (gx, gy), wa_, below=p.get("wbelow", 6.0), above=p.get("wabove", 34.0),
                                    heat=p.get("wheat", 0.0), flip=p.get("wflip", 1)))
        elif W_ == "hammer":
            wres.update(draw_hammer(cv, hn, p["wa"], below=p.get("wbelow", 6.0), above=p.get("wabove", 34.0),
                                    heat=p.get("wheat", 0.0), flip=p.get("wflip", 1), bias=-1 if p.get("wb") else 0))
        elif W_ == "blade":
            wres.update(draw_blade(cv, hn, p["wa"], ln=46.0, curve=p.get("wcurve", -3.5), heat=p.get("wheat", 1.0)))
        elif W_ == "spear":
            wres.update(draw_spear(cv, hn, p["wa"], below=p.get("wbelow", 16.0), heat=p.get("wheat", 1.0)))
        elif W_ == "chain":
            tip = add(hn, mul(dirv(p["ca"]), p["cl"]))
            wres.update(draw_chain(cv, hn, tip, bend=p.get("cb", 0.0), heat=p.get("wheat", 1.0), fi=fi, slack=p.get("cs", 0.0)))
        elif W_ == "ftongs":
            r = draw_tongs(cv, hn, p["wa"], ln=28, open_=p.get("topen", 4.0), heat=0.9, coal=p.get("coal", 1.0), fi=fi, tag="weapon")
            wres.update(r); wres["head"] = r["mid"]; wres["m"] = r["px"]
    # far hand's tongs (P1): drawn before the far arm so the hand closes over the reins
    tres = {}
    if p.get("tongs_far"):
        tres.update(draw_tongs(cv, hf, p["ta"], ln=30, open_=p.get("topen", 3.0), bias=0, heat=p.get("theat", 0.0)))
    # -- the far side
    if not p.get("two_front"):
        draw_arm(cv, sh_f, hf, p["pf"], bias=-1, mode=p.get("mf", "fist"), grip=p.get("gf", (0, 1)), hang=p["hang_f"], fire=fire, fi=fi,
                 spread=p.get("spread_f", 1.0))
    draw_pauldron(cv, add(sh_f, (-0.5, -0.5)), bias=-1, scale=1.2, lift=p.get("lift_f", 0.0))
    if p.get("wb"):
        near_weapon()
    kf = draw_leg(cv, hip_f, (p["ffx"], p["ffy"]), bias=-1, lift=FLOOR - p["ffy"])
    stride = p["fnx"] - p["ffx"] > 26
    kn = None
    if not stride:
        kn = draw_leg(cv, hip_n, (p["fnx"], p["fny"]), bias=0, lift=FLOOR - p["fny"])
    rf = p.get("robe_front", max(p["fnx"], hip[0] + 4) + (0 if stride else 2))
    rb = p.get("robe_back", min(p["ffx"] - 4, hip[0] - 10))
    draw_robe(cv, hip, neck, rf, rb, wind=wind, fire=fire, fi=fi, flare=p.get("flare", 1.0), lift=p.get("hemlift", 0.0))
    if stride:
        kn = draw_leg(cv, hip_n, (p["fnx"], p["fny"]), bias=0, lift=FLOOR - p["fny"])
    draw_veil_back(cv, add(hd, rot((-4.6, -3.0), p["lean"] + p["tilt"])), hip[1] + 6, wind=wind, fire=fire, fi=fi)
    draw_torso(cv, hip, neck, glow=p.get("chest", 0.0))
    draw_ring(cv, add(at(hip, neck, 0.02, -6.0), (0, 1.5)), bias=0, sway=p.get("ring_sway", 0.0))
    draw_apron(cv, hip, neck, kn, kf, p.get("hem", hip[1] + 28), sway=p.get("apron_sway", 0.0))
    col = [at(hip, neck, 0.86, -5.0), at(hip, neck, 1.2, -4.6), at(hip, neck, 1.06, -1.4), at(hip, neck, 0.9, 1.2)]
    cv.paint(n_plate(poly_mask(col), bevel=1.4, tilt=(-0.2, -0.3), strength=1.2), "I", bias=-1, iline=True, tag="body")
    cv.paint(n_capsule(at(hip, neck, 0.96, -0.6), hd, 1.6, 1.4), "I", bias=-1, tag="body")
    draw_head(cv, hd, p["lean"] + p["tilt"], eyes=p.get("eyes", 0.55), fire=fire, fi=fi, crown_hot=p.get("crown", 0.0))
    if p.get("two_front"):     # a two-handed grip where the far hand comes round in front of the chest
        draw_arm(cv, sh_f, hf, p["pf"], bias=-1, mode=p.get("mf", "fist"), grip=p.get("gf", (0, 1)), hang=p["hang_f"], fire=fire, fi=fi)
    if not p.get("wb") and not (W_ == "spear" and p.get("spear_front")):
        near_weapon()
    draw_pauldron(cv, add(sh_n, (-0.4, -1.2)), bias=0, scale=1.25, lift=p.get("lift_n", 0.0))
    arm = draw_arm(cv, sh_n, hn, p["pn"], bias=0, mode=p.get("mn", "fist"), grip=p.get("gn", (0, 1)), hang=p["hang_n"], fire=fire, fi=fi,
                   spread=p.get("spread_n", 1.0))
    if W_ == "spear" and p.get("spear_front"):
        near_weapon()
    info["el_n"] = arm["el"]
    if tres:
        info["tong_mid"] = tres["mid"]
    if "fx" in p and not nofx:
        for f in p["fx"]:
            f(cv, info, wres)
    img = cv.render(ref_y=72, ydark=0.010)
    info["weapon"] = wres
    info["tongs"] = tres
    info["mask"] = {q: t for q, t in cv.tags.items()}
    return img, info
