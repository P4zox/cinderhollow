#!/usr/bin/env python3
"""CONCEPT pass -- "The Molten Colossus", main boss of the Burning Deep (Ashwright's failed masterwork).

    python3 art/concepts/gen_colossus.py      -> art/concepts/colossus.png (+ colossus_1x.png raw frames)

224x176 frames, faces right, sole on the bottom row, ~150px tall.  Read-only use of art/enemy_kit.py
(normal-field shading, sel-out outlines); extra ramps are registered at runtime, nothing shared is edited.

Part-based armour: every armoured part is a body SHAPE (domes/capsules/polys -> base normals) sliced by
CUT polylines into plate REGIONS.  Each region gets its own bevel on top of the body normal, cuts render as
glowing seams (the molten core showing through), and a region can be knocked off per damage state
(`broken` = jagged holes) -> the molten body beneath is exposed, slightly thinner, dripping lava.
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, add, sub, lerp, ip, line, polyline, bezier, ik, hash01,  # noqa: E402
                       n_capsule, n_dome, n_plate, dist_field, poly_mask, mask_disc, norm3)

W, H = 224, 176
K.setup(W, H)
FLOOR = H - 1

# ---------------------------------------------------------------- extra ramps (runtime only)
EXTRA = {
    # forge iron: warm near-black, slight violet in the darks, rust-grey highlights
    "N0": "#120d10", "N1": "#1f181b", "N2": "#30262a", "N3": "#473a3b", "N4": "#6a5954", "N5": "#a38c7b",
    # molten body (shaded, self-lit)
    "H0": "#3c0c07", "H1": "#6e1a08", "H2": "#a8300b", "H3": "#e05a12", "H4": "#ff9a2a", "H5": "#ffd86a",
    # iron lit by the forge glow (warm bounce)
    "E0": "#22100e", "E1": "#3e1812", "E2": "#642414", "E3": "#933714", "E4": "#c4561a",
    # smoke (fixed)
    "S0": "#241c1b", "S1": "#322827", "S2": "#473b39", "S3": "#5f514d", "S4": "#7a6a63",
}
for k, v in EXTRA.items():
    K.HEX[k] = v
    K.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
for k in EXTRA:
    K.RAMP.setdefault(k[0], [])
    if k not in K.RAMP[k[0]]:
        K.RAMP[k[0]].append(k)
K.SHINY["N"] = 0.975
RGBA = K.RGBA


def vnoise(x, y, sc, seed):
    gx, gy = x / sc, y / sc
    x0, y0 = math.floor(gx), math.floor(gy)
    tx, ty = gx - x0, gy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = hash01(x0, y0, seed); b = hash01(x0 + 1, y0, seed)
    c = hash01(x0, y0 + 1, seed); d = hash01(x0 + 1, y0 + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def unit(v):
    l = math.hypot(*v) or 1e-6
    return (v[0] / l, v[1] / l)


def components(pts):
    pts = set(pts)
    out = []
    while pts:
        s = pts.pop()
        comp, st = {s}, [s]
        while st:
            x, y = st.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in pts:
                    pts.remove(q); comp.add(q); st.append(q)
        out.append(comp)
    return out


N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def cellular(x, y, sc, seed):
    """Worley noise: (d2 - d1 in px, hash of the nearest cell) -> cooled crust plates with molten cracks."""
    gx, gy = x / sc, y / sc
    cx, cy = math.floor(gx), math.floor(gy)
    ds = []
    for j in range(-1, 2):
        for i in range(-1, 2):
            a, b = cx + i, cy + j
            px_ = (a + 0.15 + 0.7 * hash01(a, b, seed)) * sc
            py_ = (b + 0.15 + 0.7 * hash01(a, b, seed + 1)) * sc
            ds.append((math.hypot(x + .5 - px_, y + .5 - py_), hash01(a, b, seed + 2)))
    ds.sort()
    return ds[1][0] - ds[0][0], ds[0][1]


# =========================================================================== armour system
class Armour:
    """One armoured part: shapes -> base normals, cuts -> plate regions + glowing seams."""

    def __init__(self, L, heat=1.0, bias=0, erode=2):
        self.L, self.heat, self.bias, self.erode = L, heat, bias, erode
        self.base = {}
        self.cuts = []       # (pts, kind) kind: 'seam' (glows) | 'crease' (dark line, no glow)
        self.hot = []        # seeds of regions rendered as heated metal
        self.holes = set()
        self.mat = {}

    def shape(self, normals, mat="N"):
        for p, n in normals.items():
            if K.inb(*p):
                self.base[p] = n
                self.mat[p] = mat
        return set(normals)

    def dome(self, c, rx, ry=None, flat=0.8, tilt=(0, 0), mat="N"):
        return self.shape(n_dome(c, rx, ry, flat, tilt), mat)

    def cap(self, a, b, r0, r1=None, flat=0.9, mat="N"):
        return self.shape(n_capsule(a, b, r0, r1, flat), mat)

    def poly(self, pts, tilt=(0, 0), mat="N", bulge=0.0):
        m = poly_mask(pts)
        n = n_plate(m, bevel=3.0, tilt=tilt, strength=bulge) if bulge else {p: norm3(tilt[0], tilt[1], 1) for p in m}
        return self.shape(n, mat)

    def cut(self, pts, kind="seam"):
        self.cuts.append((polyline(pts), kind))

    def hole(self, c, r, seed=0, squash=1.0):
        """Jagged knocked-off patch (frame coords)."""
        for y in range(int(c[1] - r - 3), int(c[1] + r + 4)):
            for x in range(int(c[0] - r - 3), int(c[0] + r + 4)):
                d = math.hypot(x + .5 - c[0], (y + .5 - c[1]) / squash)
                j = (vnoise(x, y, 2.2, 90 + seed) - 0.5) * 4.2 + (vnoise(x, y, 5.0, 91 + seed) - 0.5) * 3.0
                if d + j < r:
                    self.holes.add((x, y))

    def build(self, bevel=2.2, strength=1.25, rivets=True, seam_heat=None):
        L = self.L
        S = set(self.base)
        C, crease = set(), set()
        for pts, kind in self.cuts:
            for p in pts:
                if p in S:
                    (C if kind == "seam" else crease).add(p)
        dS = dist_field(S)
        holes = self.holes & S
        rem = S - C - holes
        info = {"regions": [], "core": set(), "seams": set(), "plates": set()}
        # ---- exposed molten core (thinner than the armour: outer rim of a hole is simply gone)
        core = set()
        for p in holes | (C & set().union(*[self._grow(holes, 1)]) if holes else set()):
            if p in S and dS[p] > self.erode:
                core.add(p)
        if core:
            L.paint({p: self.base[p] for p in core}, "H", bias=1 + self.bias // 2, ao=0)
            for p in core:
                x, y = p
                edge, cell = cellular(x, y, 6.5, 31)
                e = L.px[p]
                if edge < 0.45:
                    e[3] = "H5"
                elif edge < 0.95:
                    e[3] = "H4"
                elif edge < 1.6:
                    e[3] = ("LVL", 3)
                else:
                    lit = -self.base[p][0] * 0.6 - self.base[p][1] * 0.8
                    e[3] = ("LVL", max(0, min(3, 1 + (cell > 0.55) + (lit > 0.35) - (lit < -0.3))))
                if (x, y - 1) not in core:
                    e[3] = ("LVL", 0)
                elif (x, y - 2) not in core and not isinstance(e[3], str):
                    e[3] = ("LVL", 1)
        info["core"] = core
        # ---- plates
        for reg in components(rem):
            if len(reg) < 3:
                C |= reg          # slivers become seam
                continue
            nb = n_plate(reg, bevel=bevel, strength=strength)
            nrm = {}
            for p in reg:
                b = self.base[p]
                g = nb[p]
                nrm[p] = norm3(b[0] + g[0] / g[2] * 0.9, b[1] + g[1] / g[2] * 0.9, b[2])
            mats = {}
            for p in reg:
                mats.setdefault(self.mat[p], {})[p] = nrm[p]
            hot = any(ip(s) in reg for s in self.hot)
            for m, nn in mats.items():
                L.paint(nn, "H" if hot else m, bias=self.bias + (1 if hot else 0), ao=0)
            info["regions"].append(reg)
            info["plates"] |= reg
            if rivets and len(reg) > 120 and not hot:
                self._rivets(reg, C)
        # ---- seams
        for p in C:
            if p in holes:
                continue
            if dS.get(p, 0) <= 1:
                L.px[p] = ["N", (0, 0, 1), 0, ("LVL", 0), 0]
                continue
            h = seam_heat(p) if seam_heat else self.heat
            c = "O1" if h < 0.62 else "O2" if h < 1.02 else "O3" if h < 1.42 else "O4" if h < 1.85 else "O5"
            L.px[p] = [None, (0, 0, 1), 0, c, 0]
            info["seams"].add(p)
        for p in crease:
            if p in L.px and p not in holes and L.px[p][0] == "N":
                L.px[p][3] = ("LVL", 0 if dS.get(p, 0) > 1 else 1)
        # ---- heated rims: plate pixels bordering exposed core glow
        for p in info["plates"]:
            if any((p[0] + a, p[1] + b) in core for a, b in N4):
                L.px[p] = [None, (0, 0, 1), 0, "O2" if hash01(*p, 5) < 0.6 else "O3", 0]
        # ---- warm bounce under seams (light leaks onto the plate below the seam)
        for p in info["seams"]:
            q = (p[0], p[1] + 1)
            e = L.px.get(q)
            if e is not None and e[0] == "N" and e[3] is None and q not in info["seams"]:
                e[0] = "E"
                e[3] = ("LVL", 1 if self.heat < 1.3 else 2)
        return info

    @staticmethod
    def _grow(s, k):
        out = set(s)
        for _ in range(k):
            out |= {(x + a, y + b) for (x, y) in out for a, b in N4}
        return out

    def _rivets(self, reg, C):
        d = dist_field(reg)
        near = lambda p: any((p[0] + a * 3, p[1] + b * 3) in C or (p[0] + a * 2, p[1] + b * 2) in C for a, b in N4)
        cand = sorted([p for p, v in d.items() if 1.9 < v < 3.1 and near(p)], key=lambda p: (p[1], p[0]))
        taken = []
        for p in cand:
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) >= 8 for q in taken):
                taken.append(p)
        for p in taken:
            e = self.L.px.get(p)
            if e is None:
                continue
            e[3] = ("LVL", 4 if self.bias >= 0 else 3)
            q = (p[0] + 1, p[1] + 1)
            if q in reg and q in self.L.px and self.L.px[q][0] == "N":
                self.L.px[q][3] = ("LVL", 1)


def warm_light(L, c, r, k=1.0, ramp="E", mats=("N",)):
    """Forge-light bounce: iron facing the light source `c` picks up a warm ramp."""
    for p, e in L.px.items():
        if e[0] not in mats or isinstance(e[3], str):
            continue
        dx, dy = c[0] - (p[0] + .5), c[1] - (p[1] + .5)
        d = math.hypot(dx, dy)
        if d > r or d < 0.5:
            continue
        n = e[1]
        ldir = norm3(dx / d, dy / d, 0.55)
        ndl = n[0] * ldir[0] + n[1] * ldir[1] + n[2] * ldir[2]
        v = ndl * (1 - d / r) ** 1.3 * k
        if v > 0.18:
            e[0] = ramp
            e[3] = ("LVL", min(4, int(v * 5.5)))


# =========================================================================== poses
NEU = dict(
    lean=0.0, crouch=0.0, breathe=0.0, head=(0.0, 0.0), head_rot=0.0,
    # near (hammer) arm, frame coords of elbow + wrist
    n_el=(54, 96), n_wr=(56, 118),
    # far (tongs) arm
    f_el=(158, 92), f_wr=(180, 100), tong_ang=24.0, tong_open=15.0,
    feet=((84, 175), (136, 175)),
    furnace="closed", heat=1.0, hammer_hot=0.0, broken=False, puff=0, blast=False, seed=0, lava=0,
)


def P(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


POSES = [
    ("IDLE", P()),
    ("IDLE b  vents", P(breathe=1.0, puff=1, heat=1.15, seed=3, f_wr=(180, 99), n_wr=(56, 119))),
    ("SLAM WINDUP", P(lean=-8.0, crouch=12.0, head=(-2, 2), n_el=(40, 70), n_wr=(34, 47), hammer_hot=1.0,
                      f_el=(168, 70), f_wr=(186, 76), tong_ang=20.0, tong_open=16.0, heat=1.35,
                      feet=((76, 175), (142, 175)), seed=5)),
    ("FURNACE BLAST", P(lean=-6.0, crouch=3.0, head=(-3, -1), head_rot=-6, n_el=(52, 84), n_wr=(40, 104),
                        f_el=(160, 58), f_wr=(174, 40), tong_ang=-40.0, tong_open=14.0, furnace="open",
                        heat=1.6, blast=True, feet=((78, 175), (138, 175)), seed=7)),
    ("PHASE 2", P(broken=True, heat=1.7, puff=2, lava=1, seed=9, f_wr=(180, 101), n_wr=(56, 119), tong_open=11.0)),
]


# =========================================================================== parts
def torso_rig(p):
    return Rig(rot=p["lean"], piv=(108, 124), off=(0, p["crouch"]))


def draw_torso(Ly, R, p):
    """Torso + fauld + furnace + maker's mark.  Returns key points (frame)."""
    L = Ly["Torso"]
    A = Armour(L, heat=p["heat"])
    T = R.T
    br = p["breathe"]
    A.dome(T((108, 110)), 25, 13, flat=0.7)                                   # waist
    A.dome(T((90, 62)), 27, 18 + br * 0.5, flat=0.75, tilt=(-0.1, -0.1))      # hunched back
    A.dome(T((108, 80)), 37, 31 + br * 0.5, flat=0.7)                         # barrel chest
    A.dome(T((121, 78)), 24, 24, flat=0.65, tilt=(0.15, 0.0))                 # chest front bulge
    A.poly([T(q) for q in [(84, 108), (133, 108), (136, 124), (80, 124)]], tilt=(0, 0.25), bulge=0.8)  # fauld band
    # plate cuts (model coords -> frame)
    cut = lambda pts, kind="seam": A.cut([T(q) for q in pts], kind)
    cut(bezier((66, 70), (90, 76), (120, 74), (148, 64), 30))       # pectoral line
    cut(bezier((70, 96), (92, 104), (122, 104), (146, 94), 30))     # lower ribs
    cut([(80, 108), (136, 108)])                                    # belt top
    for x in (96, 112, 127):
        cut([(x, 108), (x - 1, 124)])                               # fauld lames
    cut(bezier((92, 46), (96, 56), (98, 64), (100, 72), 12))        # near chest / back
    cut(bezier((82, 73), (80, 82), (80, 92), (84, 101), 12))        # near flank
    cut(bezier((137, 69), (140, 78), (140, 88), (137, 97), 12))     # far flank
    cut(bezier((72, 50), (78, 44), (90, 40), (104, 42), 16), "crease")
    # furnace heat: seams get hotter towards the heart
    fc = T((111, 88))

    def sh(q):
        d = math.hypot(q[0] - fc[0], q[1] - fc[1])
        return p["heat"] * (1.25 - min(0.7, d / 70.0)) + 0.1 * (hash01(q[0] // 4, q[1] // 4, p["seed"]) - 0.5)
    if p["broken"]:
        A.hole(T((87, 88)), 11, seed=1, squash=1.25)          # near flank plate gone
        A.hole(T((134, 102)), 8, seed=2)                   # far lower ribs
        A.hole(T((133, 64)), 6.5, seed=3)                     # back hump
        A.hole(T((113, 116)), 4.5, seed=4)                 # a fauld lame
    info = A.build(seam_heat=sh)
    # ---- tassets hanging over the thighs (separate plates, same layer)
    for k, (a, b, c, d) in enumerate([((82, 122), (98, 122), (100, 138), (84, 136)),
                                      ((120, 122), (136, 122), (137, 135), (122, 137))]):
        if p["broken"] and k == 1:
            continue
        t = Armour(L, heat=p["heat"] * 0.8, bias=-1 if k else 0)
        t.poly([T(q) for q in (a, b, c, d)], tilt=(0.1, 0.2), bulge=1.0)
        t.cut([T(lerp(a, d, 0.5)), T(lerp(b, c, 0.5))])
        t.build(rivets=False)
    furnace(L, Ly, R, p, info)
    mark(L, R, p)
    if info["core"]:
        warm_light(L, T((88, 88)), 16, 0.8)
    return info


def furnace(L, Ly, R, p, info):
    T = R.T
    open_ = p["furnace"] == "open"
    cx, cy, rr = 111, 86, 11.0
    hole = []
    for i in range(13):                                    # arched opening outline (model)
        a = math.pi + math.pi * i / 12
        hole.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    hole += [(cx + rr, cy + 12), (cx - rr, cy + 12)]
    ring = []
    for i in range(13):
        a = math.pi + math.pi * i / 12
        ring.append((cx + math.cos(a) * (rr + 5), cy + math.sin(a) * (rr + 5)))
    ring += [(cx + rr + 5, cy + 17), (cx - rr - 5, cy + 17)]
    if open_:                                              # chest splits wider when open
        ring = [(x + (x - cx) * 0.18, y + (y - cy) * 0.12) for x, y in ring]
        hole = [(x + (x - cx) * 0.22, y + (y - cy) * 0.12) for x, y in hole]
    ringm = R.mask(ring)
    holem = R.mask(hole)
    frame = ringm - holem
    fr = Armour(L, heat=p["heat"] * 1.4)
    fr.shape(n_plate(frame, bevel=2.5, tilt=(0.0, 0.05), strength=1.6))
    for a in (-50, 0, 50, 180 + 25, -25 - 180):
        pass
    fr.cut([T((cx - rr - 5, cy + 6)), T((cx - rr, cy + 6))])
    fr.cut([T((cx + rr, cy + 6)), T((cx + rr + 5, cy + 6))])
    fr.cut([T((cx, cy - rr - 5)), T((cx, cy - rr))])
    fr.build(bevel=2.0, strength=1.6, rivets=False)
    # rivets on the ring, evenly spaced along the arch
    for i in range(1, 12, 2):
        a = math.pi + math.pi * i / 12
        q = ip(T((cx + math.cos(a) * (rr + 2.6), cy + math.sin(a) * (rr + 2.6))))
        if q in L.px:
            L.px[q][3] = ("LVL", 5); L.px[q][0] = "N"
    # ---- the heart behind the grate
    hc = T((cx, cy + 2))
    pulse = 1.0 + (0.35 if p["broken"] else 0) + (0.5 if open_ else 0)
    glow = {}
    for q in holem:
        d = math.hypot(q[0] + .5 - hc[0], (q[1] + .5 - hc[1]) * 1.1) / pulse
        dy = q[1] - hc[1]
        c = "Y1" if d < 6.5 else "O4" if d < 8.5 else "O3" if d < 11 else "O2" if d < 14 else "O1"
        if dy > 8 and d > 6:                              # coal bed: clumps of embers
            n = vnoise(q[0], q[1], 2.0, 3 + p["seed"])
            c = "O0" if n < 0.35 else "O1" if n < 0.6 else "O2" if n < 0.8 else "O3"
        glow[q] = c
    L.fixed(glow)
    # heart: a faceted ingot-heart, white hot
    k = pulse ** 0.5
    heart = {}
    for q in holem:                                         # an inverted-teardrop ingot heart
        dx, dy = (q[0] + .5 - hc[0]) / k, (q[1] + .5 - hc[1]) / k
        lobe = min(math.hypot(dx + 2.4, dy + 1.5), math.hypot(dx - 2.4, dy + 1.5)) < 3.4
        tip = dy >= -1.5 and abs(dx) < (5.6 - (dy + 1.5) * 0.9)
        if lobe or tip:
            heart[q] = "Y3" if (dx - dy * 0.3) < 1.2 else "Y2"
    for q in list(heart):
        if any((q[0] + a, q[1] + b) not in heart for a, b in N4):
            heart[q] = "O4" if q[1] + .5 > hc[1] else "Y1"
    L.fixed(heart)
    if not open_:
        # grate bars (vertical) + one crossbar, bars catch the glow on their inner edges
        bars = set()
        for bx in (-8, -3.5, 1, 5.5):
            for yy in range(-14, 13):
                for w_ in (0, 1):
                    q = ip(T((cx + bx + w_ + 0.5, cy + yy + 0.5)))
                    if q in holem:
                        bars.add((q, w_))
        for yy in (3,):
            for xx in range(-12, 13):
                q = ip(T((cx + xx + .5, cy + yy + .5)))
                if q in holem:
                    bars.add((q, 2))
        for q, w_ in bars:
            L.px[q] = ["N", (0, 0, 1), 0, ("LVL", 3 if w_ == 0 else 1 if w_ == 1 else 2), 0]
        for q, w_ in bars:                                # glow rim on bar edge facing the heart
            if w_ == 1 and q[0] < hc[0] - 1:
                L.px[q] = ["E", (0, 0, 1), 0, ("LVL", 4), 0]
            if w_ == 0 and q[0] > hc[0] + 1:
                L.px[q] = ["E", (0, 0, 1), 0, ("LVL", 3), 0]
    else:
        # grate door swung open on its left hinge: foreshortened slab of bars
        dm = R.mask([(cx - rr * 1.22 - 7, cy - 9), (cx - rr * 1.22 - 1, cy - 12), (cx - rr * 1.22 - 1, cy + 14),
                     (cx - rr * 1.22 - 7, cy + 13)])
        dm -= set(L.px) - frame
        door = {q: norm3(0.5, -0.1, 0.8) for q in dm}
        L.paint(door, "N", bias=-1, ao=0)
        for q in dm:
            if (q[1] - int(T((0, cy))[1])) % 4 == 0:
                L.px[q][3] = ("LVL", 0)
    # forge light bounce on the plates around the furnace
    warm_light(L, T((cx, cy + 2)), 34 if open_ else 32 if p["broken"] else 26,
               1.25 if open_ else 1.2 if p["broken"] else 0.9)
    if p["broken"]:                                        # phase 2: heat cracks radiating from the ring
        for k, ang in enumerate((-120, -60, -15, 25, 150, 200)):
            q = (cx + math.cos(math.radians(ang)) * (rr + 4), cy + 2 + math.sin(math.radians(ang)) * (rr + 4))
            a_ = math.radians(ang)
            pts = [T(q)]
            for j in range(4):
                a_ += (hash01(k, j, 71) - 0.5) * 1.3
                q = (q[0] + math.cos(a_) * 3.2, q[1] + math.sin(a_) * 3.2)
                pts.append(T(q))
            for i, pp in enumerate(polyline(pts)):
                e = L.px.get(pp)
                if e is not None and e[0] in ("N", "E"):
                    L.px[pp] = [None, (0, 0, 1), 0, "O4" if i < 5 else "O3" if i < 10 else "O2", 0]
    return holem


def mark(L, R, p):
    """Ashwright's maker's mark: gold roundel with an embossed anvil, set as the furnace keystone."""
    c = R.T((111.5, 72.0))
    ring = mask_disc(c, 6.0)
    fld = mask_disc(c, 4.4)
    px = {}
    for q in ring:
        dx, dy = q[0] + .5 - c[0], q[1] + .5 - c[1]
        l = -dx * 0.6 - dy * 0.8
        px[q] = ("G", 4 if l > 1.5 else 3 if l > -1.5 else 1)
    for q in fld:
        px[q] = ("G", 1)
    glyph = [(x, -2) for x in range(-3, 3)] + [(3, -2)] + [(x, -1) for x in range(-2, 2)] + [(-1, 0), (0, 0)] + \
            [(-1, 1), (0, 1)] + [(x, 2) for x in range(-2, 2)]
    cx, cy = int(math.floor(c[0])), int(math.floor(c[1]))
    gs = {(cx + g[0], cy + g[1]) for g in glyph}
    for q in gs:
        up = (q[0], q[1] - 1) not in gs or (q[0] - 1, q[1]) not in gs
        px[q] = ("G", 5 if up else 3)
    for q, (m, l) in px.items():
        L.px[q] = [m, (0, 0, 1), 0, ("LVL", l), 0]


def draw_head(Ly, R, p):
    L = Ly["Head"]
    FX = Ly["FX"]
    hc = add(R.T((131, 42)), p["head"])
    A = Armour(L, heat=p["heat"])
    A.dome(hc, 11.5, 12.5, flat=0.8)                                      # kettle helm
    A.poly([add(hc, q) for q in [(2, -3), (11, -2), (12, 8), (5, 11), (1, 9)]], tilt=(0.35, 0.05), bulge=1.0)  # face plate
    A.cut([add(hc, (-3, -11)), add(hc, (-1, -4)), add(hc, (1, 3)), add(hc, (1, 10))], "crease")   # face-plate edge
    A.cut([add(hc, (-10, 2)), add(hc, (-2, 3))], "crease")
    A.build(bevel=1.8, strength=1.3, rivets=False)
    # crest ridge
    for i, q in enumerate(line(add(hc, (-8, -8)), add(hc, (0, -12)))):
        if q in L.px and L.px[q][0] == "N":
            L.px[q][3] = ("LVL", 5 if i % 2 == 0 else 4)
    # fire slit
    y = int(hc[1] + 1)
    for x in range(int(hc[0] + 1), int(hc[0] + 13)):
        for yy, c in ((y - 1, "OUT"), (y, "O4"), (y + 1, "O3"), (y + 2, "OUT")):
            if (x, yy) in L.px:
                cc = c
                if yy == y and hc[0] + 4 <= x <= hc[0] + 10:
                    cc = "Y3" if hc[0] + 6 <= x <= hc[0] + 8 else "Y2"
                if cc == "OUT" and (x < hc[0] + 3 or x > hc[0] + 11):
                    continue
                L.px[(x, yy)] = [None, (0, 0, 1), 0, cc, 0]
    for x in range(int(hc[0] + 12), int(hc[0] + 16)):                   # heat shimmer off the slit
        if hash01(x, y, p["seed"]) < 0.6:
            FX.put([(x, y - (x - int(hc[0] + 12)) // 2)], "O3" if x < hc[0] + 14 else "O2")
    # breathing holes
    for q in [(8, 5), (10, 5), (9, 7)]:
        qq = ip(add(hc, q))
        if qq in L.px:
            L.px[qq] = [None, (0, 0, 1), 0, "O2", 0]
    # gorget / high collar in front of the chin
    G = Armour(L, heat=p["heat"])
    gc = R.T((121, 58.5))
    G.dome(gc, 17, 7.5, flat=0.7, tilt=(0, -0.2))
    for dx in (-8, 1, 10):
        G.cut([add(gc, (dx, -8)), add(gc, (dx - 1, 8))])
    G.build(bevel=1.6, rivets=False)
    return hc


def chimney(L, FXB, FX, base, top, p, k):
    A = Armour(L, heat=0.5)
    A.cap(base, top, 5.2, 4.4, flat=0.9)
    d = unit(sub(top, base))
    nn = (-d[1], d[0])
    lip = add(top, (d[0] * 1.5, d[1] * 1.5))
    A.cap(add(lip, (nn[0] * 6.5, nn[1] * 6.5)), add(lip, (-nn[0] * 6.5, -nn[1] * 6.5)), 2.4, 2.4, flat=1.0)
    for t in (0.35, 0.7):
        q = lerp(base, top, t)
        A.cut([add(q, (nn[0] * 7, nn[1] * 7)), add(q, (-nn[0] * 7, -nn[1] * 7))], "crease")
    A.build(bevel=1.4, rivets=False)
    # mouth: dark opening with a glow deep inside
    mouth = add(lip, (d[0] * 1.2, d[1] * 1.2))
    for q in mask_disc(mouth, 5.0, 1.6):
        if q in L.px:
            L.px[q] = [None, (0, 0, 1), 0, "OUT", 0]
    for q in mask_disc(add(mouth, (0, 0.4)), 2.6, 0.9):
        if q in L.px:
            L.px[q] = [None, (0, 0, 1), 0, "O2" if p["puff"] == 0 else "O3", 0]
    smoke(FXB, FX, mouth, p, k)


def smoke(FXB, FX, mouth, p, k):
    """Chunky, top-left-lit smoke puffs drifting back (left) and up, embers rising through them."""
    n = 10 + p["puff"] * 3
    puffs = []
    for i in range(n):
        t = (i + 0.35 * p["puff"] + 0.3) / (n + 0.5)
        rise = 5 + t * (40 + 12 * p["puff"])
        drift = -t * t * (30 + 10 * p["puff"]) + (hash01(i, k, 61) - 0.5) * (4 + 8 * t)
        r = (3.4 + t * (9 + 3 * p["puff"])) * (0.8 + 0.4 * hash01(i, k, 62))
        puffs.append(((mouth[0] + drift, mouth[1] - rise), r, t))
    for (c, r, t) in puffs[::-1]:
        dens = 1 - t
        for q in mask_disc(c, r):
            if not K.inb(*q):
                continue
            ex = (q[0] + .5 - c[0]) / r
            ey = (q[1] + .5 - c[1]) / r
            e = ex * ex + ey * ey
            lit = -ex * 0.6 - ey * 0.8
            if t > 0.75 and e > 0.55 and hash01(*q, 7 + k) < 0.5:
                continue
            base = 3 if dens > 0.6 else 2 if dens > 0.3 else 1
            lvl = base + (1 if lit > 0.35 else 0) - (1 if lit < -0.35 else 0)
            if t < 0.2 and p["puff"]:
                lvl += 1
            FXB.put([q], "S%d" % max(0, min(4, lvl)))
        # underside glow near the vent
        if t < 0.3:
            for q in mask_disc((c[0], c[1] + r * 0.55), r * 0.6, r * 0.35):
                if q in FXB.px:
                    FXB.px[q] = "O1" if p["puff"] == 0 else "O2"
    if p["puff"]:                                                   # tongue of flame in the mouth
        K.flame(FX, (mouth[0], mouth[1] + 1), 3.2 + p["puff"], p["seed"] + k, seed=k)
    for i in range(4 + 5 * p["puff"]):
        q = (mouth[0] + (hash01(i, k, 11 + p["seed"]) - 0.6) * 22, mouth[1] - 4 - hash01(i, k, 12 + p["seed"]) * 44)
        FX.put([ip(q)], "O4" if hash01(i, k, 13) < 0.4 else "O3")
        if hash01(i, k, 14) < 0.3:
            FX.put([ip(add(q, (0, 1)))], "O2")


def draw_leg(L, hip, foot, p, bias, knee_pref, broken_sp=None):
    fx, fy = foot
    ank = (fx, fy - 9)
    kn = ik(hip, ank, 30, 27, knee_pref)
    A = Armour(L, heat=p["heat"] * (0.8 if bias < 0 else 1.0), bias=bias)
    A.cap(hip, kn, 13, 11, flat=0.85)                        # thigh
    A.cap(kn, ank, 10, 12, flat=0.85)                        # greave (flares)
    sab = [(fx - 13, fy + 1), (fx - 14, fy - 8), (fx - 8, fy - 13), (fx + 6, fy - 13), (fx + 13, fy - 8),
           (fx + 19, fy - 4), (fx + 20, fy + 1)]
    A.poly(sab, tilt=(0.0, -0.15), bulge=1.1)                # sabaton
    A.dome(kn, 8.5, 8, flat=0.8)                             # knee cop
    d = unit(sub(kn, hip))
    nn = (-d[1], d[0])
    for t in (0.45,):
        q = lerp(hip, kn, t)
        A.cut([add(q, (nn[0] * 15, nn[1] * 15)), add(q, (-nn[0] * 15, -nn[1] * 15))])
    d2 = unit(sub(ank, kn))
    n2 = (-d2[1], d2[0])
    for t in (0.5,):
        q = lerp(kn, ank, t)
        A.cut([add(q, (n2[0] * 14, n2[1] * 14)), add(q, (-n2[0] * 14, -n2[1] * 14))])
    A.cut([(fx - 14, fy - 7), (fx + 2, fy - 7), (fx + 14, fy - 3)])
    A.cut([(fx + 4, fy - 13), (fx + 7, fy - 7)])
    A.cut(bezier(add(kn, (-9, 3)), add(kn, (-5, 8)), add(kn, (5, 8)), add(kn, (9, 3)), 12))
    if broken_sp:
        A.hole(lerp(hip, kn, 0.55), broken_sp, seed=6)
    A.build()
    return kn


def hammer_fist(L, el, wr, p, broken=False):
    """Forearm ending in a massive forge-hammer fist (block along the arm, striking face at the end)."""
    d = unit(sub(wr, el))
    nn = (-d[1], d[0])
    loc = lambda u, v: (wr[0] + d[0] * u + nn[0] * v, wr[1] + d[1] * u + nn[1] * v)
    A = Armour(L, heat=p["heat"])
    A.cap(el, wr, 11, 11.5, flat=0.85)                                      # vambrace
    # block: side face (towards -nn / screen-left when hanging) + front face
    side_sgn = 1 if nn[0] < 0 else -1                                       # which side faces the light
    HW, HL, SW_ = 16, 33, 6
    A.poly([loc(-4, -HW + 5), loc(-4, HW - 5), loc(0, HW - 3), loc(HL, HW), loc(HL, -HW), loc(0, -HW + 3)], bulge=0.5)
    sd = [loc(0, (HW - 3) * side_sgn), loc(2, (HW + SW_ - 4) * side_sgn), loc(HL - 1, (HW + SW_) * side_sgn), loc(HL, HW * side_sgn)]
    A.shape({q: norm3(nn[0] * side_sgn * 0.9, nn[1] * side_sgn * 0.9 - 0.25, 0.45) for q in poly_mask(sd)})
    fw = HW + 2.5
    face = [loc(HL, -fw - (SW_ if side_sgn < 0 else 0)), loc(HL, fw + (SW_ if side_sgn > 0 else 0)),
            loc(HL + 6, fw + (SW_ if side_sgn > 0 else 0) - 1), loc(HL + 6, -fw - (SW_ if side_sgn < 0 else 0) + 1)]
    A.poly(face, tilt=(d[0] * 0.3, d[1] * 0.3), bulge=0.6)
    for u in (9, 22):                                                       # iron straps
        A.cut([loc(u, -26), loc(u, 26)])
    A.cut([loc(HL, -26), loc(HL, 26)])
    A.cut([loc(-4, -26), loc(-4, 26)])                                      # wrist socket
    A.cut([loc(-15, -14), loc(-15, 14)])                                    # vambrace lame
    A.cut([loc(0, (HW - 3) * side_sgn), loc(HL, HW * side_sgn)], "crease")        # block edge
    if p["hammer_hot"]:
        A.hot = [loc(HL + 3, 0), loc(HL + 3, 8), loc(HL + 3, -8)]
    if broken:
        A.hole(loc(-9, 2), 6, seed=8)
    info = A.build()
    # side-face bolts
    for u in (3, 15.5, 28):
        for v in (HW + 3,):
            q = ip(loc(u, v * side_sgn))
            if q in L.px and L.px[q][0] == "N":
                L.px[q][3] = ("LVL", 5)
    return loc


def draw_near_arm(Ly, R, p):
    L = Ly["NearArm"]
    sh = R.T((78, 60))
    el, wr = p["n_el"], p["n_wr"]
    A = Armour(L, heat=p["heat"])
    A.cap(sh, el, 12, 10.5, flat=0.85)                                      # upper arm
    A.dome(el, 8.5, 8.5, flat=0.8)                                          # elbow cop
    d = unit(sub(el, sh)); nn = (-d[1], d[0])
    q = lerp(sh, el, 0.62)
    A.cut([add(q, (nn[0] * 14, nn[1] * 14)), add(q, (-nn[0] * 14, -nn[1] * 14))])
    if p["broken"]:
        A.hole(lerp(sh, el, 0.75), 6.5, seed=10)
    A.build()
    hammer_fist(L, el, wr, p, broken=p["broken"])
    # pauldron: stacked lames over the shoulder
    P_ = Armour(L, heat=p["heat"])
    pc = R.T((76, 57))
    P_.dome(pc, 20, 18, flat=0.75, tilt=(-0.05, -0.1))
    for k in range(3):
        P_.cut(bezier(add(pc, (-21, -2 + k * 7)), add(pc, (-8, 3 + k * 7)), add(pc, (8, 3 + k * 7)),
                      add(pc, (21, -3 + k * 7)), 24))
    if p["broken"]:
        P_.hole(add(pc, (5, -7)), 10.5, seed=12, squash=0.8)
    P_.build(bevel=2.4)
    # rim trim on the top lame
    return sh


def draw_far_arm(Ly, R, p):
    L = Ly["FarArm"]
    sh = R.T((140, 58))
    el, wr = p["f_el"], p["f_wr"]
    A = Armour(L, heat=p["heat"] * 0.8, bias=-1)
    A.dome(R.T((140, 55)), 16, 15, flat=0.75)                            # far pauldron
    A.cap(sh, el, 11, 10, flat=0.85)
    A.dome(el, 8, 8, flat=0.8)
    A.cap(el, wr, 10, 9, flat=0.85)
    A.dome(wr, 7.5, 7.5, flat=0.8)
    A.cut(bezier(add(R.T((140, 55)), (-15, 3)), add(R.T((140, 55)), (-5, 8)), add(R.T((140, 55)), (6, 8)),
                 add(R.T((140, 55)), (15, 1)), 20))
    d = unit(sub(wr, el)); nn = (-d[1], d[0])
    q = lerp(el, wr, 0.5)
    A.cut([add(q, (nn[0] * 10, nn[1] * 10)), add(q, (-nn[0] * 10, -nn[1] * 10))])
    A.build()
    # tongs
    ang = p["tong_ang"]
    piv = add(wr, (math.cos(math.radians(ang)) * 8, math.sin(math.radians(ang)) * 8))
    T_ = Armour(L, heat=0.6, bias=-1)
    tips = []
    for s in (-1, 1):
        a = math.radians(ang + s * p["tong_open"])
        a2 = math.radians(ang - s * 38)
        mid = add(piv, (math.cos(a) * 27, math.sin(a) * 27))
        tip = add(mid, (math.cos(a2) * 10, math.sin(a2) * 10))
        T_.cap(piv, mid, 3.4, 2.8, flat=0.9)
        T_.cap(mid, tip, 2.8, 1.6, flat=0.9)
        tips.append((mid, tip))
    T_.dome(piv, 5.5, 5.5, flat=0.7)
    T_.build(rivets=False)
    for mid, tip in tips:                                                   # jaws heated at the tips
        for i, q in enumerate(line(lerp(mid, tip, 0.35), tip)):
            for qq in (q, (q[0], q[1] + 1)):
                if qq in L.px:
                    L.px[qq] = [None, (0, 0, 1), 0, "O4" if i > 3 else "O3", 0]
    pq = ip(piv)
    if pq in L.px:
        L.px[pq][3] = ("LVL", 4)
    return piv


def lava(FX, Ly, p):
    """Drips: from the bottom edge of exposed molten core, over plates and off the body; pool at the feet."""
    names = ["FarArm", "Back", "NearLeg", "FarLeg", "Torso", "Head", "NearArm"]
    occ = {}
    for n in names:
        for q, e in Ly[n].px.items():
            occ[q] = (n, e)
    starts = []
    for n in names:
        L = Ly[n]
        for q, e in L.px.items():
            if e[0] == "H" and (q[0], q[1] + 1) in L.px and L.px[(q[0], q[1] + 1)][0] != "H":
                if hash01(*q, 21) < 0.33:
                    starts.append(q)
    for i, s in enumerate(starts):
        ln = 2 + int(hash01(*s, 22) * 7)
        x, y = s
        for k in range(1, ln + 1):
            q = (x, y + k)
            if q in occ:
                FX.put([q], "O3" if k < ln - 1 else "O4")
            else:
                # left the body: a falling drop
                FX.put([q], "O4")
                if hash01(*s, 23) < 0.5:
                    FX.put([(x, min(FLOOR - 2, y + k + 4 + int(hash01(*s, 24) * 10)))], "O3")
                break
    # pool + splashes at the feet
    for x in range(58, 170):
        n = vnoise(x, 0, 6, 25)
        if n > 0.55:
            FX.put([(x, FLOOR)], "O3" if n > 0.65 else "O2")
            if n > 0.72:
                FX.put([(x, FLOOR - 1)], "O4")


def blast(FX, origin, p):
    """Fire belched from the open furnace: a widening, turbulent cone towards the right."""
    ox, oy = origin
    Lb = W - ox + 6
    for x in range(int(ox), W):
        t = (x - ox) / Lb
        half = 5 + t * 30 + math.sin(t * 9 + p["seed"]) * 2.0
        cy = oy - t * 10 + math.sin(t * 6.5) * 3
        for y in range(int(cy - half - 4), int(cy + half + 5)):
            if not K.inb(x, y):
                continue
            n = vnoise(x, y, 5.0, 40) - 0.5 + (vnoise(x - t * 30, y, 2.5, 41) - 0.5) * 0.6
            r = abs(y + .5 - cy) / max(half, 1) + n * 0.55
            if r > 1.0:
                continue
            v = r * 0.75 + t * 0.55
            c = "Y3" if v < 0.28 else "Y2" if v < 0.42 else "Y1" if v < 0.56 else "O4" if v < 0.7 else \
                "O3" if v < 0.86 else "O2" if v < 1.02 else "O1"
            if t > 0.72 and v > 0.95:
                c = "S2" if hash01(x, y, 42) < 0.6 else "S1"
            FX.put([(x, y)], c)
    # licks curling out around the furnace lip
    for k in range(4):                                     # licks curling up off the furnace lip
        b = (ox - 16 + k * 6, oy - 14 + abs(k - 1.5) * 2)
        K.flame(FX, b, 2.6 + (k % 2), k, seed=k)
    for i in range(26):
        q = (ox + 20 + hash01(i, 1, 44) * 90, oy - 30 + hash01(i, 2, 44) * 60)
        if ip(q) not in FX.px:
            FX.put([ip(q)], "O4" if hash01(i, 3, 44) < 0.5 else "O3")


# =========================================================================== frame assembly
ORDER = ["FXBack", "FarArm", "Back", "FarLeg", "NearLeg", "Torso", "Head", "NearArm", "FX"]


def frame(p):
    Ly = {n: (FXLayer(n) if n.startswith("FX") else Layer(n)) for n in ORDER}
    R = torso_rig(p)
    # chimneys (behind everything of the torso)
    chimney(Ly["Back"], Ly["FXBack"], Ly["FX"], R.T((70, 50)), R.T((62, 26)), p, 0)
    chimney(Ly["Back"], Ly["FXBack"], Ly["FX"], R.T((150, 46)), R.T((160, 25)), p, 1)
    draw_far_arm(Ly, R, p)
    hipN, hipF = R.T((96, 124)), R.T((124, 122))
    draw_leg(Ly["FarLeg"], hipF, p["feet"][1], p, -1, (0.9, -0.3), broken_sp=6 if p["broken"] else None)
    draw_leg(Ly["NearLeg"], hipN, p["feet"][0], p, 0, (0.8, -0.4))
    info = draw_torso(Ly, R, p)
    draw_head(Ly, R, p)
    draw_near_arm(Ly, R, p)
    if p["blast"]:
        blast(Ly["FX"], R.T((123, 88)), p)
    if p["lava"]:
        lava(Ly["FX"], Ly, p)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in ORDER:
        L = Ly[n]
        im = L.image() if isinstance(L, FXLayer) else K.render_layer(L)
        img.alpha_composite(im)
    return img


# =========================================================================== sheet
BGC = (26, 18, 16, 255)


def player_img():
    pl = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40))
    c = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
    c.alpha_composite(pl)
    c.alpha_composite(wp)
    return c.transpose(Image.FLIP_LEFT_RIGHT)          # faces the boss


def text(dr, xy, s, fill=(214, 170, 120, 255)):
    dr.text(xy, s, fill=fill)


def main():
    frames = [(name, frame(p)) for name, p in POSES]
    S = 2
    PAD = 16
    PL = 70                                              # extra room next to the idle for the knight
    widths = [W + (PL if i == 0 else 0) for i in range(len(frames))]
    rows = [[0, 1, 2], [3, 4]]
    rw = [sum(widths[i] * S + PAD for i in r) + PAD for r in rows]
    SW = max(rw)
    RH = H * S + 34
    sheet = Image.new("RGBA", (SW, RH * len(rows) + 28), BGC)
    dr = ImageDraw.Draw(sheet)
    text(dr, (PAD, 8), "THE MOLTEN COLOSSUS  -  concept  (224x176 frames @2x, knight for scale)", (240, 200, 150, 255))
    raw = Image.new("RGBA", (W * len(frames), H), (0, 0, 0, 0))
    for ri, r in enumerate(rows):
        x = PAD
        y = 28 + ri * RH
        for i in r:
            name, im = frames[i]
            raw.alpha_composite(im, (i * W, 0))
            w = widths[i]
            panel = Image.new("RGBA", (w, H), (0, 0, 0, 0))
            panel.alpha_composite(im, (0, 0))
            if i == 0:
                pim = player_img()
                panel.alpha_composite(pim, (W + PL - 64 - 2, H - 40))
            # floor strip
            fl = Image.new("RGBA", (w * S, 3 * S), (44, 30, 25, 255))
            sheet.alpha_composite(fl, (x, y + 14 + H * S))
            sheet.alpha_composite(panel.resize((w * S, H * S), Image.NEAREST), (x, y + 14))
            text(dr, (x + 2, y), name)
            x += w * S + PAD
    # 4x detail inset of the idle's furnace/head in the free slot
    x0 = PAD + sum(widths[i] * S + PAD for i in rows[1])
    y0 = 28 + RH + 14
    crop = frames[0][1].crop((78, 26, 196, 114))
    bgc = Image.new("RGBA", crop.size, BGC)
    bgc.alpha_composite(crop)
    Z = 4 if x0 + crop.size[0] * 4 < SW else 3
    sheet.alpha_composite(bgc.resize((crop.size[0] * Z, crop.size[1] * Z), Image.NEAREST), (x0, y0))
    text(dr, (x0 + 2, y0 - 14), "DETAIL x%d  helm slit / furnace heart / Ashwright's mark (keystone)" % Z)
    out = os.path.join(HERE, "colossus.png")
    sheet.save(out)
    raw.save(os.path.join(HERE, "colossus_1x.png"))
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
