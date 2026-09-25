#!/usr/bin/env python3
"""CONCEPT pass -- "The Frostbound Twins", main boss of the Hoarfrost Aqueduct.

    python3 art/concepts/gen_twins.py

Outputs (concept only, nothing in assets/ is touched)
    art/concepts/twins.png         3x presentation sheet: one row per twin (player for scale, idle, block,
                                   signature attack, enraged survivor), then the back-to-back key art
    art/concepts/twins_frames.png  the same frames at 1x (96x72 cells; key art 128x80)

Method: same family as gen_kalden.py -- enemy_kit normal-field shading, per-layer sel-out outline, a Rig
that maps upright model joints to the frame.  Everything is keyed by joints (P hip, C chest, Hd head, feet,
hands, weapon angle, shield pose) and drawn into named layers, so a pose is just a dict and the rig can be
animated later exactly like Kalden's.  Model space is a 96x72 frame, faces RIGHT, feet on row 71, AX = 40.
A mirrored Rig (sx=-1) draws a twin facing LEFT while the light stays top-left (used for the key art).
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, n_plate, leg, arm, blade_px, blade_line, flame, dirv)

W, H = 96, 72
K.setup(W, H)
FLOOR = H - 1
AX = 40

# ---------------------------------------------------------------- palette additions (runtime only)
EXTRA = {
    # Hael: soot-blackened crimson plate (warm, hue-shifted to ember orange in the light)
    "H0": "#140709", "H1": "#2c0d12", "H2": "#4d1519", "H3": "#78211d", "H4": "#a63a24", "H5": "#d8683a",
    # bronze trim
    "Z0": "#1f1209", "Z1": "#402612", "Z2": "#6a421b", "Z3": "#9a6526", "Z4": "#cc933c", "Z5": "#f3d488",
    # soot / blackened iron
    "J0": "#0c0a0c", "J1": "#1a1617", "J2": "#2a2324", "J3": "#3f3533", "J4": "#5e4f49",
    # Rime: pale blue-white enamel (cool, violet shadows)
    "E0": "#1d1f38", "E1": "#343d64", "E2": "#5a6d98", "E3": "#8ea6c9", "E4": "#c4d6e8", "E5": "#f3f9fc",
    # ice crystal
    "N0": "#10263a", "N1": "#1f5470", "N2": "#3a8fae", "N3": "#6cc6de", "N4": "#b4ecf6", "N5": "#f2feff",
    # silver trim
    "S0": "#141925", "S1": "#262f44", "S2": "#414e66", "S3": "#687a92", "S4": "#a1b1c2", "S5": "#dfe8ee",
    # deep frost-navy cloth
    "X0": "#0a0e1d", "X1": "#131b37", "X2": "#1d2a52", "X3": "#2b3f74", "X4": "#46609c",
    # ice glow (fixed colours)
    "U0": "#173a73", "U1": "#2f73c2", "U2": "#6fbaf2", "U3": "#c4ecff", "U4": "#ffffff",
}
for k, v in EXTRA.items():
    K.HEX[k] = v
    K.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k[0], []).append(k)
K.SHINY.update({"Z": 0.9, "E": 0.93, "N": 0.88, "S": 0.92})
RGBA = K.RGBA

FIRE = ("Y3", "Y2", "Y1", "O4", "O3", "O2")
FIRE_BACK = ("O4", "O3", "O3", "O2", "O1", "O0")
COLDFIRE = ("U4", "U3", "U2", "U2", "U1", "U0")

# weapons (u along the blade from the grip; see enemy_kit.blade_px)
HBLADE = dict(pommel=-6.4, grip_end=0.8, grip="L1", grip_w=0.9, pommel_c="Z3", guard=(0.6, 2.6, 5.4),
              guard_c="Z2", guard_hi="Z4", b0=2.6, end=30.0, w_edge=2.0, w_spine=1.7, taper=0.22, fuller="O2",
              edge_hi="O4", edge="I3", spine="I2")
RBLADE = dict(pommel=-5.6, grip_end=0.8, grip="X2", grip_w=0.7, pommel_c="N4", guard=(0.6, 2.0, 4.2),
              guard_c="S2", guard_hi="S4", b0=2.0, end=29.0, w_edge=1.3, w_spine=1.1, taper=0.42, fuller="N3",
              edge_hi="N5", edge="N4", spine="N2")


class MRig(Rig):
    """Rig that may mirror (sx=-1): weapon angles and shading tilts are mirrored so light stays top-left."""
    def A(self, ang):
        return (180.0 - ang if self.sx < 0 else ang) + self.rot

    def tl(self, t):
        return (t[0] * (1 if self.sx > 0 else -1), t[1])

    def dome(self, L, c, rx, ry=None, mat="I", bias=0, ao=1, flat=1.0, tilt=(0, 0), clip=None):
        return Rig.dome(self, L, c, rx, ry, mat, bias, ao, flat, self.tl(tilt), clip)

    def plate(self, L, pts, mat, bevel=1.5, tilt=(0, 0), strength=1.1, fold=None, bias=0, ao=1, minus=None):
        return Rig.plate(self, L, pts, mat, bevel, self.tl(tilt), strength, fold, bias, ao, minus)


def P_(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


# =========================================================================== shared helpers
def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def remat(L, pts, frm, to, chance=1.0, seed=0):
    """Swap the material of shaded pixels (keeps the normal-field shading) -- soot, frost crust..."""
    for q in pts:
        e = L.px.get(q)
        if e is not None and e[0] == frm and e[3] is None and hash01(q[0], q[1], seed) < chance:
            e[0] = to


def blot(x, y, seed):
    """Low-frequency value noise (0..1) for coherent grime / frost patches instead of pixel salt."""
    return (hash01(x // 3, y // 3, seed) * 0.5 + hash01((x + 1) // 2, (y + 1) // 2, seed + 1) * 0.3 +
            hash01(x // 5, y // 4, seed + 2) * 0.2)


def soot(L, mat, y0, span, seed=17):
    """Soot creeping up from below: darker ramp steps, then blackened iron in the lowest blotches."""
    for q, e in L.px.items():
        if e[0] != mat or e[3] is not None:
            continue
        t = max(0.0, min(1.0, (q[1] - y0) / span))
        n = blot(q[0], q[1], seed)
        if n < 0.08 + 0.38 * t * t:
            e[0] = "J"
        elif n < 0.2 + 0.45 * t:
            e[2] -= 1


def rag_hem(x0, x1, y, seed, depth=2.5):
    pts = []
    n = max(2, int(abs(x1 - x0) / 1.6))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.3 + hash01(i, 3, seed)) if i % 2 == 0 else depth * 0.15
        pts.append((x, y + d))
    return pts


def crystal(R, L, base, ang, length, w, mat="N", bias=0):
    """Faceted ice shard: two triangles with opposite tilts give a crisp lit/shadow facet split."""
    d = dirv(ang)
    pv = (-d[1], d[0])
    tip = add(base, (d[0] * length, d[1] * length))
    lft, rgt = add(base, (pv[0] * w, pv[1] * w)), add(base, (-pv[0] * w, -pv[1] * w))
    back = add(base, (-d[0] * 0.8, -d[1] * 0.8))
    m1 = R.plate(L, [lft, tip, back], mat, bevel=0.7, tilt=(-0.3, -0.35), strength=0.4, bias=bias, ao=0)
    m2 = R.plate(L, [back, tip, rgt], mat, bevel=0.7, tilt=(0.55, 0.35), strength=0.4, bias=bias - 1, ao=0)
    return m1 | m2


def crack(L, start, ang, length, seed, core, glow=None, branch=True, only=None):
    """Jagged glowing crack decal in frame coords (random walk)."""
    pts = [start]
    a = ang
    x, y = start
    step = 1.6
    n = int(length / step)
    for i in range(n):
        a += (hash01(i, seed, 71) - 0.5) * 70
        x += math.cos(math.radians(a)) * step
        y += math.sin(math.radians(a)) * step
        pts.append((x, y))
    px = polyline(pts)
    px = [q for q in px if q in L.px and (only is None or L.px[q][0] in only)]
    if glow:
        L.decal([(q[0] + 1, q[1]) for q in px if (q[0] + 1, q[1]) in L.px], glow)
    L.decal(px, core)
    if branch and n > 3:
        mid = pts[n // 2]
        crack(L, mid, ang + (50 if hash01(seed, 1, 5) > 0.5 else -50), length * 0.4, seed + 7, core, glow, False, only)
    return px


def sparkle(FX, c, big=False, pal=("U4", "U2")):
    x, y = ip(c)
    FX.put([(x, y)], pal[0])
    FX.put([(x + 1, y), (x - 1, y), (x, y - 1), (x, y + 1)], pal[1])
    if big:
        FX.put([(x + 2, y), (x - 2, y), (x, y - 2), (x, y + 2)], pal[1])


def embers(FX, box, n, seed, pal=("O4", "O3", "Y1", "O2")):
    x0, y0, x1, y1 = box
    for k in range(n):
        x = int(x0 + (x1 - x0) * hash01(k, seed, 1))
        y = int(y0 + (y1 - y0) * hash01(k, seed, 2))
        FX.put([(x, y)], pal[k % len(pal)])
        if hash01(k, seed, 3) < 0.3:
            FX.put([(x, y - 1)], pal[(k + 1) % len(pal)])


def snow(FX, box, n, seed, pal=("U3", "U2", "N5", "U1")):
    x0, y0, x1, y1 = box
    for k in range(n):
        x = int(x0 + (x1 - x0) * hash01(k, seed, 11))
        y = int(y0 + (y1 - y0) * hash01(k, seed, 12))
        if hash01(k, seed, 13) < 0.18:
            sparkle(FX, (x, y))
        else:
            FX.put([(x, y)], pal[k % len(pal)])


def arc_smear(FX, c, a0, a1, r_out, width, pal, exclude=(), clip_y=None):
    """Crescent smear around c from angle a0 -> a1 (screen degrees, clockwise); thick & hot at a1."""
    hot = set()
    R_ = int(r_out + 2)
    for y in range(int(c[1]) - R_, int(c[1]) + R_ + 1):
        for x in range(int(c[0]) - R_, int(c[0]) + R_ + 1):
            if (x, y) in exclude or not K.inb(x, y) or (clip_y is not None and y > clip_y):
                continue
            dx, dy = x + .5 - c[0], y + .5 - c[1]
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx))
            while a < a0:
                a += 360
            if a > a1:
                continue
            t = (a - a0) / (a1 - a0)
            th = 1.0 + width * t ** 1.4
            if r_out - th <= r <= r_out:
                k = (r_out - r) / max(th, 1e-3)
                if t < 0.35 and hash01(x, y, 91) > t * 2.6:
                    continue
                i = 0 if k < 0.2 else 1 if k < 0.45 else 2 if k < 0.75 else 3
                if t < 0.5:
                    i = min(3, i + 1)
                FX.put([(x, y)], pal[i])
                hot.add((x, y))
    return hot


def rim_light(img, side, cols, strength=0.55):
    """Tint the pixels just inside the silhouette outline on one side (+1 right, -1 left) toward a glow."""
    src = img.copy()
    s = src.load()
    d = img.load()
    w, h = img.size
    op = lambda x, y: 0 <= x < w and 0 <= y < h and s[x, y][3] > 0

    def tint(x, y, c, st):
        if op(x, y):
            p = s[x, y]
            d[x, y] = tuple(int(p[i] + (c[i] - p[i]) * st) for i in range(3)) + (255,)
    for y in range(h):
        for x in range(w):
            if op(x, y) and not op(x + side, y) and op(x - side, y) and op(x - 2 * side, y):
                tint(x - side, y, RGBA[cols[0]], strength)
                if op(x - 3 * side, y):
                    tint(x - 2 * side, y, RGBA[cols[1]], strength * 0.5)
    return img


def up_facing(e, k=-0.15):
    return e[1][1] < k


def split_hilt(Ls, p, pix, g0, ca, sa):
    """Blade on the weapon layer; with p['hilt'] the hilt+hand come forward while the blade stays behind."""
    if not p.get("hilt"):
        Ls[p["wl"]].fixed(pix)
        return
    front = {q: c for q, c in pix.items() if (q[0] + .5 - g0[0]) * ca + (q[1] + .5 - g0[1]) * sa < 3.0}
    Ls["Weapon"].fixed(front)
    Ls["WeaponBack"].fixed({q: c for q, c in pix.items() if q not in front})


# =========================================================================== SER HAEL (flame)
HL = ["FXBack", "Cape", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "HornBack", "Head", "Horn",
      "ArmUp", "Weapon", "FrontArm", "Shield", "FX"]
FXL = {"FXBack", "FX"}

HAEL0 = dict(P=(39.0, 47.0), C=(40.6, 34.4), Hd=(42.4, 22.8), hup=(0.12, -1), fb=(30.0, 71), ff=(50.5, 71),
             kb=None, kf=None, hs=(52.0, 45.0), wang=-52, wl="Weapon", hsh=(45.0, 47.5),
             sh=dict(c=(43.5, 47.0), rx=6.4, ry=8.6, tilt=(0.25, 0.0)), cape=1.0, sway=0.0, enr=False,
             slam=False, flames=1.0, eye=1, fi=0)


def draw_hael(p, R):
    Ls = {n: Layer(n) for n in HL if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    P, C, Hd = p["P"], p["C"], p["Hd"]
    fi = p["fi"]
    enr = p["enr"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(1.8, -ln + 2.6), F(-3.4, -ln + 3.0)
    hB, hF = F(-3.6, 1.2), F(3.6, 1.2)
    floor = R.T((0, FLOOR))[1]
    info = {}

    # ---------------- sword (far hand): dark iron, molten edge and glowing fuller runes, wreathed in fire
    grip, wang = p["hs"], p["wang"]
    pix, blade, tip = blade_px(R, grip, wang, HBLADE)
    g0, a0 = R.T(grip), R.A(wang)
    ca, sa = dirv(a0)
    for q in list(pix):
        u = (q[0] + .5 - g0[0]) * ca + (q[1] + .5 - g0[1]) * sa
        if pix[q] == "O2":
            pix[q] = ("O3", "O2", "O1", "O2")[int(u) % 4]
        if enr and pix[q] == "I2" and hash01(q[0], q[1], 3) < 0.45:
            pix[q] = "N3" if hash01(q[0], q[1], 4) < 0.6 else "U3"         # hoarfrost on the spine
    pix = {q: c for q, c in pix.items() if q[1] <= floor}
    split_hilt(Ls, p, pix, g0, ca, sa)
    info["tip"] = tip
    if p["flames"]:
        # flames rise from the upper edge of the blade: big dim tongues behind, small hot licks in front
        nrm = (sa, -ca) if -ca < 0 or abs(ca) < 0.2 else (-sa, ca)
        if nrm[1] > 0:
            nrm = (-nrm[0], -nrm[1])
        for k, u in enumerate(range(7, 31, 3)):
            b = blade_line(g0, a0, u + hash01(k, fi, 1) * 1.2)
            if b[1] > floor - 1:
                continue
            s = (1.2 + 1.9 * (u / 30.0) + hash01(k, fi, 2) * 0.8) * p["flames"]
            flame(FXB, (b[0] + nrm[0] * 0.5, b[1] + nrm[1] * 0.5), s * 1.3, fi + k, seed=k * 3, pal=FIRE_BACK)
            if k % 3 == 1 or u > 26:
                cold = enr and k % 2 == 1
                flame(FX, (b[0] + nrm[0] * 1.6, b[1] + nrm[1] * 1.6), s * 0.55, fi + k, seed=k * 5 + 1,
                      pal=COLDFIRE if cold else FIRE)
        embers(FX, (min(g0[0], tip[0]) - 3, min(g0[1], tip[1]) - 9, max(g0[0], tip[0]) + 3,
                    min(g0[1], tip[1]) - 2), int(5 * p["flames"]), 30 + fi)

    # ---------------- cape: soot-black, tattered, hem smouldering
    if p["cape"]:
        Cl = Ls["Cape"]
        ctop = F(-4.2, -ln - 0.6)
        hem_y = min(FLOOR - 3.0, P[1] + 16.5)
        back = P[0] - 7.5 - 8.5 * p["cape"] + p["sway"]
        fx0 = P[0] - 2.5
        pts = [add(ctop, (3.4, -1.0)), F(0.4, -ln + 2.0), F(-2.8, 0.6), (fx0, hem_y - 2.0)] + \
            rag_hem(back, fx0, hem_y, 41, 4.2) + \
            [(back - 1.0, P[1] - 1.0), (P[0] - 10.5 + p["sway"] * 0.5, P[1] - 11.0), add(ctop, (-5.4, 2.6))]
        cm = R.mask(pts)
        Cl.paint(n_plate(cm, 2.6, (0.2, 0.05), 1.0,
                         fold=lambda x, y: (0.75 * math.sin((x - P[0]) * 0.7 + y * 0.1), 0)), "J", bias=-1, ao=0)
        cols = {}
        for q in cm:
            cols[q[0]] = max(cols.get(q[0], -1), q[1])
        for x, yb in cols.items():
            h = hash01(x, 0, 42)
            Cl.decal([(x, yb)], "O3" if h < 0.35 else "O2" if h < 0.75 else "O1")
            if h < 0.5:
                Cl.decal([(x, yb - 1)], "O1" if h < 0.3 else ("R", 2))
            if h < 0.2:
                Cl.decal([(x, yb - 2)], ("R", 1))
        Cl.decal([q for q in cm if hash01(q[0] // 2, q[1] // 2, 43) < 0.05 and q[1] > hem_y - 8], ("J", 0))
        Cl.decal([q for q in cm if abs(q[0] - R.T((P[0] - 3.4, 0))[0]) < 0.8 and q[1] > R.T(P)[1]], ("H", 1))
        embers(FX, (R.T((back, 0))[0], R.T((0, hem_y - 5))[1], R.T((fx0, 0))[0], R.T((0, hem_y))[1]), 3, 60 + fi)

    # ---------------- far (sword) arm
    ba = Ls["ArmUp" if p.get("armup") else "BackArm"]
    el = arm(R, ba, shB, grip, 8.8, 8.8, 3.1, 2.7, "H", bias=-1, fist="J", fist_r=2.4, pref=(-1, 0.6))
    R.cap(ba, lerp(el, grip, 0.5), grip, 2.8, 2.4, "J", -1, ao=0)
    R.dome(ba, add(shB, (0.2, -0.8)), 4.2, 3.8, "H", bias=-1)

    # ---------------- legs: crimson cuisses, bronze poleyns, soot-black sabatons
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        L = Ls[nm]
        k = leg(R, L, hip, ft, 12.6, 12.6, 4.0, 3.1, "H", bias=bias, flen=5.8, heel=2.6, boot_h=4.4,
                knee=kn, boot="J")
        R.dome(L, add(k, (0.8, 0.0)), 3.2, 2.9, "Z", bias=bias)
        R.decal(L, [add(k, (1.4, -0.6))], ("Z", 5 + bias))
        R.dline(L, add(k, (-2.2, 3.0)), add(k, (2.6, 2.7)), ("Z", 2 + bias))
        soot(L, "H", floor - 20, 22)
        info["knee_" + nm] = k

    # ---------------- torso: broad crimson cuirass, bronze flame filigree, soot creeping up from below
    Bd = Ls["Body"]
    faulds = [F(-7.8, -2.0), F(7.0, -2.0), F(8.2, 5.8), F(-8.4, 5.8)]
    fm = R.plate(Bd, faulds, "H", bevel=1.8, tilt=(0.0, 0.2), bias=-1)
    for k in range(2):
        R.dline(Bd, F(-8.0, 0.8 + k * 2.4), F(7.4, 0.8 + k * 2.4), ("H", 1))
    R.dline(Bd, F(-8.2, 5.4), F(8.0, 5.4), ("Z", 2))
    torso = [F(-7.6, -1.0), F(-8.8, -ln + 3.6), F(-6.4, -ln - 2.2), F(3.8, -ln - 3.0), F(8.6, -ln + 1.0),
             F(9.0, -ln + 7.0), F(7.0, -1.0)]
    tm = R.plate(Bd, torso, "H", bevel=3.6, tilt=(-0.35, -0.15), strength=1.35)
    R.dline(Bd, F(2.6, -ln - 2.4), F(3.2, -2.4), ("H", 5))                      # keel ridge
    R.dline(Bd, F(3.4, -ln - 2.2), F(4.0, -2.4), ("H", 2))
    R.dline(Bd, F(-6.0, -ln - 1.8), F(3.8, -ln - 2.6), ("Z", 3))                # neck trim
    # bronze flame filigree on the breast
    fl = bezier(F(-3.0, -2.6), F(-3.6, -ln + 4.0), F(1.0, -ln + 6.0), F(-0.6, -ln + 1.2), n=14)
    Bd.decal(polyline([R.T(q) for q in fl]), ("Z", 3))
    fl2 = bezier(F(0.8, -2.6), F(0.2, -5.0), F(4.4, -ln + 7.0), F(3.4, -ln + 3.6), n=12)
    Bd.decal(polyline([R.T(q) for q in fl2]), ("Z", 4))
    # heavy belt, bronze buckle
    R.cap(Bd, F(-8.0, -1.4), F(7.6, -1.4), 1.2, 1.2, "L", 0, ao=0)
    R.dome(Bd, F(5.4, -1.4), 1.6, 1.4, "Z", 0)
    soot(Bd, "H", R.T(F(0, -ln))[1], 24)
    R.cap(Bd, F(0.6, -ln - 1.0), add(Hd, (-0.8, 5.8)), 3.6, 3.3, "J", bias=-1)   # gorget

    # ---------------- horns + horned great-helm with an ember visor slit
    G = basis(Hd, p["hup"])
    horn = lambda o: [add(q, o) for q in bezier(G(-2.4, -5.0), G(-8.8, -6.0), G(-10.6, -12.6), G(-5.4, -17.2), n=12)]
    tube(R, Ls["HornBack"], horn((3.4, -0.8)), 2.3, 0.5, "B", bias=-1)
    hp = horn((0, 0))
    hm = tube(R, Ls["Horn"], hp, 2.7, 0.5, "B", bias=0)
    for i in range(2):
        R.dome(Ls["Horn"], hp[i], 2.6, 2.4, "J", bias=0, ao=0)                       # sooted roots
    R.dline(Ls["Horn"], add(hp[0], (0.4, -2.4)), add(hp[0], (0.4, 2.4)), ("Z", 3))   # bronze collar
    for i in (5, 7, 9):
        R.dline(Ls["Horn"], add(hp[i], (-1.2, -1.0)), add(hp[i], (1.0, 0.9)), ("B", 2))   # ridges
    Hl = Ls["Head"]
    helm = [G(-5.2, 5.4), G(-5.8, -1.0), G(-5.4, -6.0), G(-1.2, -7.0), G(3.8, -6.8), G(5.9, -5.2), G(6.2, 1.2),
            G(5.8, 5.6), G(-4.6, 5.8)]
    R.plate(Hl, helm, "H", bevel=2.4, tilt=(-0.3, -0.25), strength=1.3)
    R.dline(Hl, G(-5.6, -3.6), G(6.0, -3.6), ("Z", 3))                          # brow band
    R.dline(Hl, G(-5.6, -2.9), G(6.0, -2.9), ("Z", 2))
    R.dline(Hl, G(-5.0, -6.2), G(5.4, -5.8), ("Z", 4))                          # crown rim
    R.dline(Hl, G(5.5, -2.4), G(5.5, 5.2), ("Z", 3))                            # face cross
    for k in range(3):
        R.decal(Hl, [G(3.2 + 0.1 * k, 1.6 + k * 1.3)], "OUT")                   # breaths
        R.decal(Hl, [G(4.2, 1.6 + k * 1.3)], "O1")
    soot(Hl, "H", R.T(G(0, 0))[1], 12, seed=19)
    # visor slit: the ember glow
    slit = R.dline(Hl, G(1.0, -1.0), G(6.4, -1.0), "O3")
    R.dline(Hl, G(1.0, -0.2), G(6.2, -0.2), "OUT")
    R.dline(Hl, G(1.0, -1.8), G(6.2, -1.8), ("J", 1))
    FX.put(slit[:2], "O2")
    FX.put(slit[2:], "O4")
    if enr:
        # the back half of the slit burns ice-blue now
        FX.put(slit[:len(slit) // 2], "U2")
        FX.put(slit[:1], "U1")
    e1 = R.pt(G(5.0, -1.0))
    FX.put([e1], "Y2")
    sp_ = R.pt(G(7.4, -1.0))
    FX.put([sp_], "O2")                                                         # light spilling out
    FX.put([(sp_[0] + R.sx, sp_[1])], "O1")
    if p["eye"] == 2:
        FX.put([(e1[0] + 1, e1[1]), (e1[0] + 2, e1[1]), (e1[0], e1[1] - 1), (e1[0], e1[1] + 1)], "O4")
        FX.put([(e1[0] + 3, e1[1])], "O2")

    # ---------------- near (shield) arm + great pauldron
    Fa = Ls["FrontArm"]
    hsh = p["hsh"]
    el2 = arm(R, Fa, shF, hsh, 8.6, 8.6, 3.2, 2.8, "H", bias=0, fist="J", fist_r=2.4, pref=(-1, 0.7))
    R.cap(Fa, lerp(el2, hsh, 0.45), hsh, 2.8, 2.5, "J", 0, ao=0)
    R.dome(Fa, add(el2, (0.3, 0.2)), 2.5, 2.3, "Z", 0)                            # couter
    pm = set()
    lames = ((1.0, 4.6, 4.8, 2.8), (0.5, 1.6, 5.8, 3.4), (0.0, -1.4, 6.6, 4.4))
    for k, (dx, dy, rx, ry) in enumerate(lames):
        m = R.dome(Fa, add(shF, (dx, dy)), rx, ry, "H", tilt=(0.05, 0.1))
        Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], ("Z", 3 if k < 2 else 4))
        pm |= m
    R.dline(Fa, add(shF, (-4.4, -2.6)), add(shF, (2.0, -5.4)), ("H", 5))          # haute-piece ridge
    soot(Fa, "H", R.T(shF)[1] - 2, 26, seed=21)

    # ---------------- heavy round shield, rim of embers
    Sh = Ls["Shield"]
    sp = p["sh"]
    if sp:
        c, rx, ry, tl = sp["c"], sp["rx"], sp["ry"], sp["tilt"]
        m = R.dome(Sh, c, rx, ry, "H", flat=0.45, tilt=tl, ao=0)
        cc = R.T(c)
        erx, ery = rx * abs(R.sx), ry
        ring = {q for q in m if ((q[0] + .5 - cc[0]) / erx) ** 2 + ((q[1] + .5 - cc[1]) / ery) ** 2 > 0.62}
        outer = {q for q in m if ((q[0] + .5 - cc[0]) / erx) ** 2 + ((q[1] + .5 - cc[1]) / ery) ** 2 > 0.8}
        for q in ring:
            Sh.px[q][0] = "Z"
        soot(Sh, "H", cc[1] - ery * 0.5, ery * 1.6, seed=23)
        # radial bronze bands + boss
        for ang in (-60, 60, 180):
            d = dirv(ang)
            R.dline(Sh, c, add(c, (d[0] * rx * 0.78, d[1] * ry * 0.78)), ("Z", 2))
        R.dome(Sh, add(c, (0.4, -0.2)), 2.6, 3.0, "Z", 0, tilt=tl)
        # rivets round the rim
        for k in range(10):
            a = math.radians(k * 36 + 10)
            R.decal(Sh, [add(c, (math.cos(a) * rx * 0.72, math.sin(a) * ry * 0.72))], ("Z", 5))
        # the ember rim: hot coals set in the bronze, glowing outward
        for q in outer:
            a = math.atan2(q[1] + .5 - cc[1], q[0] + .5 - cc[0])
            f = (a + math.pi) / (2 * math.pi) * 12
            cold = enr and math.cos(a) * R.sx < -0.1
            if int(f) % 2 == 0:
                hot_ = abs(f - int(f) - 0.5) < 0.22
                Sh.decal([q], ("U3" if hot_ else "U1") if cold else ("O4" if hot_ else "O2"))
        for k in range(7):
            a = hash01(k, 1, 26) * 6.283
            r = 1.0 + 0.25 + hash01(k, 2, 26) * 0.35
            q = (cc[0] + math.cos(a) * erx * r, cc[1] + math.sin(a) * ery * r)
            cold = enr and math.cos(a) * R.sx < -0.1
            (FXB if k % 3 else FX).put([ip(q)], ("U2", "U1", "N4")[k % 3] if cold else ("O3", "O2", "O4")[k % 3])
        if enr:
            for k in range(3):
                crack(Sh, add(cc, (-1 * R.sx, -1 + k)), 180 + (k - 1) * 40 if R.sx > 0 else (k - 1) * 40, 6 + k,
                      500 + k, "U3", ("N", 3))

    # ---------------- enraged survivor: frost from the fallen sister has taken him
    if enr:
        # frost cracks through the plate
        for k, (L_, s, ang, ln_) in enumerate(((Bd, F(-6.0, -ln + 3.0), 40, 12), (Bd, F(-7.0, -3.0), -30, 8),
                                               (Fa, add(shF, (-3.0, -2.0)), 60, 8), (Hl, G(-4.4, -4.8), 60, 7),
                                               (Ls["FrontLeg"], add(hF, (-1.0, 2.0)), 80, 9))):
            crack(L_, R.T(s), R.A(ang) if R.sx > 0 else 180 - ang, ln_, 300 + k * 13, "U3", ("N", 3),
                  only=("H", "J", "Z"))
        # hoarfrost crust on the back side of the plate
        for L_ in (Bd, Fa, Ls["BackArm"], Ls["BackLeg"], Hl):
            for q in list(L_.px):
                e = L_.px[q]
                if e[0] in ("H", "J") and e[3] is None and up_facing(e, -0.3) and blot(q[0], q[1], 31) < 0.42:
                    e[0] = "E"
        # ice shards growing from pauldron, horn and helm
        for k, (b, a, l_, w_) in enumerate(((add(shF, (-3.6, -3.2)), -125, 5.5, 1.3), (add(shF, (-1.0, -4.4)), -100, 4.2, 1.1),
                                            (add(shF, (-5.4, -1.4)), -150, 3.6, 1.0))):
            crystal(R, Fa, b, a, l_, w_, "N")
        for i, (a, l_) in ((5, (-150, 3.4)), (7, (-60, 3.0))):
            crystal(R, Ls["Horn"], hp[i], a, l_, 0.9, "N")
        crystal(R, Hl, G(-4.6, -6.0), -130, 3.8, 1.0, "N")
        snow(FX, (R.T(P)[0] - 20, R.T(Hd)[1] - 12, R.T(P)[0] + 4, R.T(P)[1] + 18), 10, 90 + fi)

    # ---------------- signature: overhead flame slam (impact frame)
    if p["slam"]:
        excl = {q for q in pix}
        rr = math.hypot(*sub(tip, R.T(shB)))
        arc_smear(FX, R.T(shB), -48, R.A(wang) - 3, rr + 0.5, 5.0, ["Y3", "Y2", "O4", "O3"], exclude=excl,
                  clip_y=floor)
        arc_smear(FXB, R.T(shB), -60, R.A(wang) - 6, rr - 4.5, 4.0, ["O3", "O2", "O1", "O0"], exclude=excl,
                  clip_y=floor)
        ix = tip[0]
        for k, (dx, s) in enumerate(((-9, 3.2), (-5, 5.0), (-1, 7.4), (3, 6.2), (7, 4.4), (11, 2.8), (-13, 2.0))):
            flame(FXB, (ix + dx - 0.5, floor + 0.5), s * 1.3, fi + k, seed=k * 7, pal=FIRE_BACK)
            flame(FX, (ix + dx, floor + 0.5), s * 0.85, fi + k, seed=k * 11 + 2, pal=FIRE)
        # ground rupture
        for k in range(-16, 17):
            x = int(ix + k)
            if hash01(k, 3, 33) < 0.8:
                FX.put([(x, int(floor))], "O4" if abs(k) < 5 else "O3" if abs(k) < 11 else "O2")
        # thrown rubble + embers
        for k in range(10):
            a = math.radians(-160 + 140 * hash01(k, 1, 34))
            r = 8 + 10 * hash01(k, 2, 34)
            q = (ix + math.cos(a) * r, floor - 2 + math.sin(a) * r * 0.9)
            FX.put([ip(q)], "J3" if k % 2 else "J2")
            FX.put([ip(add(q, (0, 1)))], "OUT")
        embers(FX, (ix - 16, floor - 30, ix + 16, floor - 8), 22, 80 + fi, pal=("O4", "Y2", "O3", "Y1", "O2"))
    return Ls, info


# =========================================================================== DAME RIME (frost)
RL = ["FXBack", "Cape", "Plume", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "ArmUp", "Weapon",
      "FrontArm", "Shield", "FX"]

RIME0 = dict(P=(40.0, 45.8), C=(41.2, 34.6), Hd=(42.4, 24.0), hup=(0.1, -1), fb=(33.0, 71), ff=(49.0, 71),
             kb=None, kf=None, hs=(53.0, 42.0), wang=-62, wl="WeaponBack", hsh=(48.5, 44.5),
             sh=dict(c=(50.0, 49.5), w=6.0, h=19.0, ang=-10.0, face=0.25), cape=1.0, sway=0.0, enr=False,
             thrust=False, eye=1, fi=0, plume=0.0)


def kite(R, L, c, w, h, ang, face):
    """Kite shield of ice: rounded top, long point. `face` tilts the facets (turned toward the viewer +)."""
    G = basis(c, (math.sin(math.radians(ang)), -math.cos(math.radians(ang))))
    top = -h * 0.42
    pts = [G(-w, top + 1.6), G(-w * 0.82, top), G(0, top - 1.0), G(w * 0.82, top), G(w, top + 1.6),
           G(w * 0.92, top + h * 0.38), G(w * 0.45, top + h * 0.75), G(0, top + h)]
    pts += [G(-w * 0.45, top + h * 0.75), G(-w * 0.92, top + h * 0.38)]
    m = R.mask(pts)
    cx = R.T(c)[0]
    left = {q for q in m if (q[0] + .5 - cx) * R.sx < 0}
    L.paint(n_plate(left, 1.6, R.tl((-0.4 + face, -0.45)), 0.8), "N", 0, ao=0)
    L.paint(n_plate(m - left, 1.6, R.tl((0.2 + face, -0.2)), 0.8), "N", 0, ao=0)
    # silver rim
    edge = [q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        L.px[q][0] = "S"
    R.dline(L, G(0, top - 0.6), G(0, top + h - 1.0), ("N", 5))                  # the ridge
    # frozen star sigil
    s0 = G(0, top + h * 0.33)
    for a in (0, 60, 120):
        d = dirv(a)
        R.dline(L, add(s0, (d[0] * 2.6, d[1] * 2.6)), add(s0, (-d[0] * 2.6, -d[1] * 2.6)), ("N", 4))
    R.decal(L, [s0], ("N", 5))
    # internal fractures (lighter) & deep ice (darker)
    L.decal(polyline([R.T(q) for q in (G(-w * 0.7, top + 2.5), G(-w * 0.35, top + 4.2), G(-w * 0.5, top + 6.8))]),
            ("N", 4), only_on=("N",))
    L.decal(polyline([R.T(q) for q in (G(w * 0.6, top + 5.0), G(w * 0.25, top + 7.5), G(w * 0.42, top + 10.0))]),
            ("N", 3), only_on=("N",))
    L.decal([q for q in m if hash01(q[0] // 2, q[1] // 3, 51) < 0.12], ("N", 1), only_on=("N",))
    return m, G, top


def draw_rime(p, R):
    Ls = {n: Layer(n) for n in RL if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    P, C, Hd = p["P"], p["C"], p["Hd"]
    fi = p["fi"]
    enr = p["enr"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(1.4, -ln + 2.2), F(-2.8, -ln + 2.5)
    hB, hF = F(-2.6, 1.0), F(2.6, 1.0)
    floor = R.T((0, FLOOR))[1]
    info = {}

    # ---------------- icicle sword
    grip, wang = p["hs"], p["wang"]
    pix, blade, tip = blade_px(R, grip, wang, RBLADE)
    g0, a0 = R.T(grip), R.A(wang)
    ca, sa = dirv(a0)
    for q in list(pix):
        u = (q[0] + .5 - g0[0]) * ca + (q[1] + .5 - g0[1]) * sa
        if pix[q] == "N3":
            pix[q] = "O3" if enr and int(u) % 3 != 2 else ("N3" if int(u) % 5 else "N5")
        if pix[q] == "N2" and hash01(q[0], q[1], 7) < 0.25:
            pix[q] = "N1"
    pix = {q: c for q, c in pix.items() if q[1] <= floor}
    split_hilt(Ls, p, pix, g0, ca, sa)
    wl = Ls[p["wl"]]
    # ice nubs along the spine + crystal quillons
    for k, u in enumerate((8, 14, 20)):
        b = blade_line(grip, wang, u)
        crystal(R, wl, b, wang - 150, 2.6 - k * 0.5, 0.7, "N")
    crystal(R, wl, blade_line(grip, wang, 1.6), wang - 95, 3.2, 0.9, "N")
    crystal(R, wl, blade_line(grip, wang, 1.6), wang + 95, 3.0, 0.9, "N")
    info["tip"] = tip
    for k in range(3):
        sparkle(FX, blade_line(g0, a0, 10 + k * 8 + hash01(k, fi, 1) * 3), big=k == 1)
    if enr:
        for k, u in enumerate((20, 25, 29)):
            b = blade_line(g0, a0, u)
            flame(FX, (b[0], b[1] - 0.5), 1.4 + k * 0.4, fi + k, seed=k * 9, pal=FIRE)
        embers(FX, (min(g0[0], tip[0]), min(g0[1], tip[1]) - 8, max(g0[0], tip[0]) + 2, max(g0[1], tip[1])),
               7, 140 + fi)

    # ---------------- plume: long pale horsehair from the crown
    G0 = basis(Hd, p["hup"])
    G = lambda a, b: G0(a * 1.14, b * 1.14)
    root = G(-1.6, -5.4)
    ps = p["sway"] * 1.2 - p["plume"]
    pl = bezier(root, add(root, (-5.0, -2.6)), add(root, (-11.0 + ps, 1.5)), add(root, (-15.0 + ps * 1.6, 13.0)), n=14)
    side_a, side_b = [], []
    for i, q in enumerate(pl):
        j = min(i + 1, len(pl) - 1); k0 = max(i - 1, 0)
        dx, dy = pl[j][0] - pl[k0][0], pl[j][1] - pl[k0][1]
        l_ = math.hypot(dx, dy) or 1
        w_ = 3.2 * (1 - i / len(pl)) ** 0.7 + 0.5
        side_a.append((q[0] - dy / l_ * w_, q[1] + dx / l_ * w_))
        side_b.append((q[0] + dy / l_ * w_, q[1] - dx / l_ * w_))
    Pm = R.plate(Ls["Plume"], side_a + side_b[::-1], "E", bevel=1.6, tilt=(-0.1, -0.2), strength=1.0,
                 fold=lambda x, y: (0.4 * math.sin(x * 0.9 + y * 0.6), 0))
    for k in range(3):
        Ls["Plume"].decal(polyline([R.T(add(q, (0, -0.9 + k * 0.9))) for q in pl[2:11 - k]]), ("E", (2, 4, 3)[k]))

    # ---------------- short cape, frost-navy, hem rimed with ice
    if p["cape"]:
        Cl = Ls["Cape"]
        ctop = F(-3.4, -ln - 0.4)
        hem_y = min(FLOOR - 4.0, P[1] + 13.0 + p["cape_drop"] if "cape_drop" in p else P[1] + 13.0)
        back = P[0] - 6.0 - 8.0 * p["cape"] + p["sway"]
        fx0 = P[0] - 2.0
        pts = [add(ctop, (3.0, -1.0)), F(0.2, -ln + 2.0), F(-2.2, 0.0), (fx0, hem_y - 2.0)] + \
            rag_hem(back, fx0, hem_y, 61, 2.4) + [(back - 1.0, P[1] - 2.0), (P[0] - 8.5 + p["sway"] * 0.5, P[1] - 10.5),
                                                  add(ctop, (-4.2, 2.2))]
        cm = R.mask(pts)
        Cl.paint(n_plate(cm, 2.4, (0.2, 0.05), 1.0,
                         fold=lambda x, y: (0.7 * math.sin((x - P[0]) * 0.8 + y * 0.1), 0)), "X", bias=-1, ao=0)
        cols = {}
        for q in cm:
            cols[q[0]] = max(cols.get(q[0], -1), q[1])
        for x, yb in cols.items():
            h = hash01(x, 0, 62)
            if enr and h < 0.4:
                Cl.decal([(x, yb)], "O3" if h < 0.15 else "O2")
                Cl.decal([(x, yb - 1)], ("J", 1))
            else:
                Cl.decal([(x, yb)], ("N", 4 if h < 0.5 else 3))
                if h < 0.55:
                    Cl.decal([(x, yb - 1)], ("N", 3 if h < 0.3 else 2))
        Cl.decal([q for q in cm if abs(q[0] - R.T((P[0] - 3.0, 0))[0]) < 0.8 and q[1] > R.T(P)[1] - 2], ("S", 2))

    # ---------------- far (sword) arm
    ba = Ls["ArmUp" if p.get("armup") else "BackArm"]
    el = arm(R, ba, shB, grip, 8.4, 8.2, 2.3, 2.0, "E", bias=-1, fist="S", fist_r=1.9, pref=(-1, 0.6))
    R.cap(ba, lerp(el, grip, 0.5), grip, 2.1, 1.9, "S", -1, ao=0)
    R.dome(ba, add(shB, (0.2, -0.6)), 3.2, 2.8, "E", bias=-1)

    # ---------------- legs: long, slim, silver greaves
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        L = Ls[nm]
        k = leg(R, L, hip, ft, 13.2, 13.0, 2.9, 2.2, "E", bias=bias, flen=5.0, heel=2.0, boot_h=3.4,
                knee=kn, boot="S")
        R.dome(L, add(k, (0.6, 0.0)), 2.4, 2.3, "S", bias=bias)
        R.decal(L, [add(k, (0.9, 0.1))], "N4" if not enr else "O3")
        R.dline(L, add(hip, (1.6, 1.0)), lerp(hip, k, 0.85), ("E", 5 + bias))      # thigh highlight seam
        info["knee_" + nm] = k

    # ---------------- torso: slim enamel cuirass, pinched waist, long tassets, frost-navy tabard
    Bd = Ls["Body"]
    tass = [F(-5.4, -2.0), F(4.6, -2.0), F(6.6, 8.2), F(0.8, 9.2), F(-6.2, 8.0)]
    R.plate(Bd, tass, "E", bevel=1.6, tilt=(0.0, 0.25), bias=-1)
    R.dline(Bd, F(-5.8, 3.4), F(5.6, 3.4), ("E", 1))
    R.dline(Bd, F(-6.0, 7.6), F(6.4, 7.6), ("S", 3))
    R.dline(Bd, F(0.9, -1.8), F(1.0, 9.0), ("E", 1))                              # tasset split
    torso = [F(-4.4, -1.0), F(-6.4, -ln + 3.4), F(-5.0, -ln - 2.0), F(3.0, -ln - 2.6), F(6.8, -ln + 1.6),
             F(6.6, -ln + 6.4), F(3.6, -1.4)]
    R.plate(Bd, torso, "E", bevel=3.0, tilt=(-0.35, -0.15), strength=1.35)
    R.dline(Bd, F(2.2, -ln - 2.0), F(2.6, -2.2), ("E", 5))
    R.dline(Bd, F(-4.6, -ln - 1.5), F(2.6, -ln - 2.2), ("S", 4))                  # neck trim
    R.dline(Bd, F(-4.4, -1.4), F(4.0, -1.4), ("S", 3))                            # waist
    # silver frost filigree
    fl = bezier(F(-1.0, -2.4), F(-3.2, -ln + 5.0), F(1.6, -ln + 4.4), F(0.4, -ln + 1.0), n=12)
    Bd.decal(polyline([R.T(q) for q in fl]), ("S", 4), only_on=("E",))
    # tabard
    tx = F(2.0, -2.0)
    tsw = -p["sway"] * 0.5
    tb = [add(tx, (-2.4, 0)), add(tx, (2.6, 0)), add(tx, (3.0 + tsw * 0.5, 11.0)), add(tx, (0.2 + tsw, 14.4)),
          add(tx, (-2.6 + tsw * 0.5, 11.0))]
    tbm = R.plate(Bd, tb, "X", bevel=1.4, tilt=(-0.2, 0.0), fold=lambda x, y: (0.45 * math.sin(x * 1.3), 0))
    Bd.decal([q for q in tbm if any((q[0] + a, q[1]) not in tbm for a in (1, -1))], ("S", 3))
    sg = R.T(add(tx, (0.2, 6.0)))
    for a in (0, 60, 120):
        d = dirv(a)
        Bd.decal(line((sg[0] - d[0] * 1.6, sg[1] - d[1] * 1.6), (sg[0] + d[0] * 1.6, sg[1] + d[1] * 1.6)), ("N", 4))
    Bd.decal([ip(sg)], ("N", 5))
    R.cap(Bd, F(0.4, -ln - 0.6), add(Hd, (-0.4, 4.2)), 2.3, 2.1, "S", bias=0)   # gorget
    # frost-star on the breast
    st = F(1.8, -ln + 4.4)
    for a in (0, 60, 120):
        d = dirv(a)
        R.dline(Bd, add(st, (d[0] * 1.8, d[1] * 1.8)), add(st, (-d[0] * 1.8, -d[1] * 1.8)), ("S", 4))
    R.decal(Bd, [st], "U3")

    # ---------------- crowned helm, ice-blue visor
    Hl = Ls["Head"]
    helm = [G(-4.0, 4.4), G(-4.6, -1.0), G(-3.8, -4.6), G(-0.6, -5.8), G(2.6, -5.4), G(4.4, -3.2), G(5.0, 0.6),
            G(4.6, 2.8), G(1.8, 4.8), G(-2.8, 4.8)]
    R.plate(Hl, helm, "E", bevel=2.2, tilt=(-0.3, -0.2), strength=1.3)
    R.dline(Hl, G(-0.2, -5.6), G(3.8, -3.6), ("E", 5))
    # pointed silver visor (sparrow-beak), hinged at a rosette on the cheek
    vis = [G(0.6, -2.2), G(4.6, -2.4), G(5.6, 0.4), G(5.0, 2.8), G(1.8, 4.6), G(0.2, 1.2)]
    R.plate(Hl, vis, "S", bevel=1.2, tilt=(-0.15, 0.0), strength=1.0)
    R.dline(Hl, G(1.2, 1.4), G(5.4, 1.2), ("S", 4))                              # visor ridge
    R.dome(Hl, G(0.2, 0.2), 1.0, 1.0, "S", 0, ao=0)                              # hinge rosette
    for k in range(3):
        R.decal(Hl, [G(2.8 + k * 0.9, 2.8)], "OUT")                              # breaths
    slit = R.dline(Hl, G(0.8, -1.6), G(5.0, -1.6), "U1")
    FX.put(slit[1:], "U2")
    e1 = R.pt(G(4.0, -1.6))
    FX.put([e1], "U4")
    sp_ = R.pt(G(6.0, -1.8))
    FX.put([sp_], "U1")
    if enr:
        FX.put(slit[:len(slit) // 2], "O3")
        FX.put([R.pt(G(1.6, -1.6))], "O4")
    if p["eye"] == 2:
        FX.put([(e1[0] + R.sx, e1[1]), (e1[0] + 2 * R.sx, e1[1]), (e1[0], e1[1] - 1), (e1[0], e1[1] + 1)], "U3")
    # silver circlet and a crown of ice
    circ = R.dline(Hl, G(-4.4, -3.2), G(4.4, -3.8), ("S", 4))
    Hl.decal([(q[0], q[1] + 1) for q in circ if (q[0], q[1] + 1) in Hl.px], ("S", 2))
    for k, (a, l_, w_, tilt_) in enumerate(((-3.2, 3.0, 1.2, -24), (-0.8, 5.4, 1.5, -4),
                                             (1.8, 3.2, 1.2, 18))):
        b = G(a, -4.0 - 0.2 * k)
        crystal(R, Hl, b, -90 + tilt_ + math.degrees(math.atan2(p["hup"][0], 1)), l_, w_, "N")
    R.decal(Hl, [G(-1.6, -3.5)], "U3")                                           # crown gem

    # ---------------- near (shield) arm + pauldron with frost crystals
    Fa = Ls["FrontArm"]
    hsh = p["hsh"]
    el2 = arm(R, Fa, shF, hsh, 8.2, 8.0, 2.4, 2.1, "E", bias=0, fist="S", fist_r=1.9, pref=(-1, 0.7))
    R.cap(Fa, lerp(el2, hsh, 0.5), hsh, 2.2, 2.0, "S", 0, ao=0)
    lames = ((0.8, 3.4, 3.8, 2.2), (0.4, 1.2, 4.6, 2.8), (0.0, -1.0, 5.2, 3.4))
    for k, (dx, dy, rx, ry) in enumerate(lames):
        m = R.dome(Fa, add(shF, (dx, dy)), rx, ry, "E", tilt=(0.05, 0.1))
        Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], ("S", 3 if k < 2 else 4))
    for k, (dx, dy, a, l_, w_) in enumerate(((-3.8, -2.2, -128, 7.6, 2.0), (-1.0, -3.4, -104, 5.2, 1.6))):
        crystal(R, Fa, add(shF, (dx, dy)), a, l_, w_, "N")
    crystal(R, ba, add(shB, (-1.6, -2.2)), -118, 4.6, 1.4, "N", bias=-1)

    # ---------------- kite shield of ice
    sp = p["sh"]
    if sp:
        m, SG, top = kite(R, Ls["Shield"], sp["c"], sp["w"], sp["h"], sp["ang"], sp["face"])
        for k in range(2):
            sparkle(FX, R.T(SG(-sp["w"] * 0.4 + k * sp["w"] * 0.9, top + 2 + k * 5)), big=False)
        if enr:
            for k in range(3):
                crack(Ls["Shield"], R.T(SG(0, top + 3 + k * 3)), 30 + k * 60, 7, 700 + k * 5, "O4", "O2")

    # ---------------- enraged survivor: her brother's fire has taken her
    if enr:
        for k, (L_, s, ang, ln_) in enumerate(((Bd, F(-4.0, -ln + 3.0), 60, 12), (Bd, F(3.0, -3.0), -110, 7),
                                               (Fa, add(shF, (-3.0, 0.0)), 40, 7), (Hl, G(-3.4, -3.0), 50, 7),
                                               (Ls["FrontLeg"], add(hF, (0.0, 2.0)), 85, 10),
                                               (Ls["BackArm"], shB, 70, 6))):
            crack(L_, R.T(s), ang if R.sx > 0 else 180 - ang, ln_, 400 + k * 17, "O4", "O2", only=("E", "S", "X"))
        for L_ in (Bd, Fa, Hl, Ls["BackLeg"], Ls["FrontLeg"]):              # scorch
            for q in list(L_.px):
                e = L_.px[q]
                if e[0] == "E" and e[3] is None and not up_facing(e, 0.2) and blot(q[0], q[1], 41) < 0.2:
                    e[0] = "J"
        # crystals burn from within
        for L_ in (Fa, Hl):
            L_.decal([q for q, e in L_.px.items() if e[0] == "N" and hash01(q[0], q[1], 43) < 0.2], "O3")
        embers(FX, (R.T(P)[0] - 18, R.T(Hd)[1] - 10, R.T(P)[0] + 6, R.T(P)[1] + 14), 12, 150 + fi)

    # ---------------- signature: lunging ice thrust
    if p["thrust"]:
        excl = set(pix)
        for k, (off, u0, u1) in enumerate(((-2, 2, 24), (0, -2, 30), (2, 4, 26), (-4, 8, 21), (4, 10, 23))):
            a = blade_line(g0, a0, u0)
            b = blade_line(g0, a0, u1)
            pts = line((a[0] - sa * off, a[1] + ca * off), (b[0] - sa * off, b[1] + ca * off))
            n = len(pts)
            for i, q in enumerate(pts):
                if q in excl:
                    continue
                t = i / max(1, n - 1)
                if (t < 0.4 and hash01(q[0], q[1], k) > t * 2.5) or (q[0] - g0[0]) * R.sx < 4:
                    continue
                FX.put([q], "U4" if t > 0.85 and k == 1 else "U3" if t > 0.6 else "U2" if t > 0.3 else "U1")
        # frost burst at the point
        tx_, ty_ = tip
        for k in range(9):
            a = -70 + 140 * hash01(k, 1, 55)
            r = 2.5 + 5 * hash01(k, 2, 55)
            d = dirv(a if R.sx > 0 else 180 - a)
            q = (tx_ + d[0] * r, ty_ + d[1] * r)
            FX.put(line(ip(add(q, (-d[0] * 1.5, -d[1] * 1.5))), ip(q)), "N4")
            FX.put([ip(q)], "U4")
        sparkle(FX, tip, big=True)
        # rime left on the ground under the lunge
        fb0 = R.T(p["fb"])[0]
        for k in range(24):
            x = int(fb0 - 8 + k * 1.7 * R.sx)
            FX.put([(x, int(floor))], ("N4", "U3", "N3")[k % 3])
            if hash01(k, 7, 57) < 0.4:
                FX.put([(x, int(floor) - 1)], "N5")
        snow(FX, (min(fb0, tx_) - 6, ty_ - 10, max(fb0, tx_) + 6, floor - 2), 12, 170 + fi)
    return Ls, info


# =========================================================================== render
def render(draw_fn, order, p, R, rim=None):
    Ls, info = draw_fn(p, R)
    imgs = {n: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for n, v in Ls.items()}
    body = K.flatten(imgs, [n for n in order if n not in FXL])
    if rim:
        for side, cols, st in rim:
            rim_light(body, side * (1 if R.sx > 0 else -1), cols, st)
    out = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
    out.alpha_composite(imgs["FXBack"])
    out.alpha_composite(body)
    out.alpha_composite(imgs["FX"])
    return out, info


def hael_poses():
    idle = P_(HAEL0)
    block = P_(HAEL0, P=(37.6, 48.6), C=(40.0, 36.8), Hd=(42.6, 25.8), hup=(0.3, -1), fb=(27.0, 71), ff=(50.0, 71),
               hs=(45.0, 45.5), wang=-34, wl="WeaponBack", hsh=(51.0, 38.5),
               sh=dict(c=(52.0, 37.0), rx=4.4, ry=9.6, tilt=(0.55, -0.05)), eye=2, flames=0.8, sway=-1.0)
    slam = P_(HAEL0, P=(44.0, 51.0), C=(49.2, 40.4), Hd=(53.6, 30.4), hup=(0.5, -1), fb=(27.5, 71), ff=(60.0, 71),
              hs=(60.0, 52.5), wang=38, hsh=(40.0, 46.0), sh=dict(c=(38.5, 45.5), rx=5.6, ry=8.4, tilt=(-0.1, 0.1)),
              eye=2, slam=True, sway=3.0, cape=1.15)
    enr = P_(HAEL0, P=(41.0, 48.4), C=(44.0, 36.6), Hd=(47.2, 26.0), hup=(0.35, -1), fb=(28.0, 71), ff=(54.0, 71),
             hs=(56.0, 41.0), wang=-22, hsh=(44.0, 46.0), sh=dict(c=(42.4, 46.8), rx=6.0, ry=8.6, tilt=(0.1, 0.0)),
             enr=True, eye=2, flames=1.25, sway=2.0)
    return [("idle", idle), ("block", block), ("flame slam", slam), ("enraged", enr)]


def rime_poses():
    idle = P_(RIME0)
    block = P_(RIME0, P=(38.6, 47.4), C=(40.2, 36.4), Hd=(42.4, 26.2), hup=(0.25, -1), fb=(29.0, 71), ff=(49.5, 71),
               hs=(47.5, 31.0), wang=-10, hsh=(50.0, 40.0), sh=dict(c=(52.5, 42.5), w=5.8, h=19.0, ang=-6.0, face=0.45),
               eye=2, sway=-1.0)
    thrust = P_(RIME0, P=(43.0, 51.0), C=(50.4, 42.0), Hd=(56.6, 33.8), hup=(0.55, -1), fb=(22.0, 71), ff=(64.0, 71),
                hs=(60.0, 41.0), wang=-3, hsh=(40.0, 44.0), sh=dict(c=(37.0, 45.5), w=4.8, h=14.0, ang=28.0, face=-0.1),
                eye=2, thrust=True, wl="Weapon", sway=4.0, cape=1.2, plume=4.0)
    enr = P_(RIME0, P=(40.4, 47.0), C=(43.0, 35.6), Hd=(45.6, 25.4), hup=(0.3, -1), fb=(30.0, 71), ff=(52.0, 71),
             hs=(49.0, 27.0), wang=12, hsh=(46.0, 44.0), sh=dict(c=(46.0, 47.0), w=5.0, h=15.0, ang=-2.0, face=0.2),
             enr=True, eye=2, sway=2.0, plume=2.0)
    return [("idle", idle), ("block", block), ("ice thrust", thrust), ("enraged", enr)]


HAEL_RIM = [(1, ("O3", "O2"), 0.55), (-1, ("U2", "U1"), 0.6)]
RIME_RIM = [(1, ("U2", "U1"), 0.55), (-1, ("O3", "O2"), 0.6)]


def key_art():
    """Back to back, blades crossed behind their heads. 144x88 canvas; Rime mirrored to face left."""
    K.setup(144, 96)
    oy = 24
    h = P_(HAEL0, P=(41.0, 47.4), C=(41.0, 34.8), Hd=(42.0, 23.2), hup=(0.02, -1), fb=(33.0, 71), ff=(53.0, 71),
           hs=(34.5, 20.5), wang=-117, wl="WeaponBack", hsh=(49.0, 45.0),
           sh=dict(c=(50.0, 46.0), rx=5.0, ry=8.8, tilt=(0.45, 0.0)), eye=2, cape=0.0, flames=0.9)
    r = P_(RIME0, P=(41.0, 46.0), C=(41.0, 34.8), Hd=(42.0, 24.2), hup=(0.02, -1), fb=(35.0, 71), ff=(51.0, 71),
           hs=(36.0, 21.0), wang=-117, wl="WeaponBack", hsh=(48.0, 43.5),
           sh=dict(c=(50.0, 47.0), w=5.2, h=17.0, ang=-6.0, face=0.4), eye=2, cape=0.0, plume=-6.0)
    Rh = MRig(off=(44.0, oy))
    Rr = MRig(piv=(AX, 0), sx=-1.0, off=(22.0, oy))
    img = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
    gl = FXLayer("g")                                    # split glow on the floor: frost left, fire right
    cxm = 72
    for x in range(K.W):
        d = (x - cxm) / 60.0
        if abs(d) < 1 and hash01(x, 0, 3) < 0.8 - 0.5 * abs(d):
            gl.put([(x, K.H - 1)], ("O3" if abs(d) < 0.3 else "O2" if abs(d) < 0.6 else "O1") if d > 0 else
                   ("U2" if abs(d) < 0.3 else "U1" if abs(d) < 0.6 else "U0"))
    ri, rinfo = render(draw_rime, RL, r, Rr, rim=[(-1, ("O2", "O1"), 0.4)])
    hi, hinfo = render(draw_hael, HL, h, Rh, rim=[(-1, ("U1", "U0"), 0.4)])
    img.alpha_composite(gl.image())
    img.alpha_composite(ri)
    img.alpha_composite(hi)
    # clash flare where the blades cross
    g1, t1 = Rh.T(h["hs"]), hinfo["tip"]
    g2, t2 = Rr.T(r["hs"]), rinfo["tip"]
    d1, d2 = sub(t1, g1), sub(t2, g2)
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) > 1e-6:
        u = ((g2[0] - g1[0]) * d2[1] - (g2[1] - g1[1]) * d2[0]) / den
        x = add(g1, (d1[0] * u, d1[1] * u))
        fx = FXLayer("c")
        sparkle(fx, x, big=True, pal=("Y3", "O4"))
        fx.put([ip(add(x, (-3, 0))), ip(add(x, (-2, -1)))], "U3")
        fx.put([ip(add(x, (3, 0))), ip(add(x, (2, 1)))], "O4")
        img.alpha_composite(fx.image())
    K.setup(W, H)
    return img


# =========================================================================== sheet
BG = (20, 24, 32, 255)


def player_scale():
    pl = Image.open(os.path.join(ROOT, "assets", "player.png")).crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ROOT, "assets", "wpn_longsword.png")).crop((0, 0, 64, 40))
    pl = pl.convert("RGBA")
    pl.alpha_composite(wp.convert("RGBA"))
    bb = pl.getbbox()
    return pl.crop((bb[0], 0, bb[2], bb[3]))


def main():
    rows = []
    frames_1x = []
    for name, fn, order, poses, rim in (("SER HAEL  -  flame", draw_hael, HL, hael_poses(), HAEL_RIM),
                                        ("DAME RIME  -  frost", draw_rime, RL, rime_poses(), RIME_RIM)):
        imgs = []
        for lab, p in poses:
            im, _ = render(fn, order, p, MRig(), rim=rim if p["enr"] else None)
            imgs.append((lab, im))
        rows.append((name, imgs))
        frames_1x.append([im for _, im in imgs])
    ka = key_art()

    S = 3
    pad = 10
    pl = player_scale()
    font = ImageFont.load_default()
    cell_w, cell_h = W * S, H * S
    pw = pl.width * S + 16
    sheet_w = pad + pw + 4 * (cell_w + pad) + pad
    lab_h = 16
    row_h = lab_h + cell_h + 18
    ka_w, ka_h = ka.width * S, ka.height * S
    sheet_h = pad + 2 * row_h + lab_h + ka_h + 24 + pad
    sheet = Image.new("RGBA", (sheet_w, sheet_h), BG)
    d = ImageDraw.Draw(sheet)
    floor_col = (34, 40, 52, 255)
    y = pad
    for name, imgs in rows:
        d.text((pad, y), name, fill=(205, 212, 226, 255), font=font)
        y0 = y + lab_h
        d.rectangle([pad, y0 + cell_h, sheet_w - pad, y0 + cell_h + 2], fill=floor_col)
        # player for scale, feet on the same floor row
        ps = pl.resize((pl.width * S, pl.height * S), Image.NEAREST)
        sheet.alpha_composite(ps, (pad + 4, y0 + cell_h - ps.height))
        d.text((pad + 4, y0 + cell_h + 5), "player", fill=(120, 128, 146, 255), font=font)
        x = pad + pw
        for lab, im in imgs:
            sheet.alpha_composite(im.resize((cell_w, cell_h), Image.NEAREST), (x, y0))
            d.text((x + 4, y0 + cell_h + 5), lab, fill=(140, 150, 170, 255), font=font)
            x += cell_w + pad
        y += row_h
    d.text((pad, y), "THE FROSTBOUND TWINS  -  key art: back to back, blades crossed", fill=(205, 212, 226, 255),
           font=font)
    y0 = y + lab_h
    kx = (sheet_w - ka_w) // 2
    d.rectangle([pad, y0 + ka_h, sheet_w - pad, y0 + ka_h + 2], fill=floor_col)
    sheet.alpha_composite(ka.resize((ka_w, ka_h), Image.NEAREST), (kx, y0))
    # player next to the key art too
    ps = pl.resize((pl.width * S, pl.height * S), Image.NEAREST)
    sheet.alpha_composite(ps, (kx - ps.width - 30, y0 + ka_h - ps.height))
    sheet.convert("RGB").save(os.path.join(HERE, "twins.png"))

    # raw 1x frames
    fw = 4 * W + ka.width
    raw = Image.new("RGBA", (fw, 2 * H + ka.height), BG)
    for r_, fr in enumerate(frames_1x):
        for c_, im in enumerate(fr):
            raw.alpha_composite(im, (c_ * W, r_ * H))
    raw.alpha_composite(ka, (0, 2 * H))
    raw.save(os.path.join(HERE, "twins_frames.png"))
    print("wrote", os.path.join(HERE, "twins.png"))


if __name__ == "__main__":
    main()
