#!/usr/bin/env python3
"""Boss generator -- "The Vessel of Rot" (ART_SPEC2 section D).

    python3 art/gen_vessel.py              full build: vessel (+ meta, previews)
    python3 art/gen_vessel.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_vessel.py --only slam,spew --preview   quick iteration on some tags

Outputs
    art/vessel.aseprite, assets/vessel.png/.json    160x128, faces right, base of the mass on the bottom row
    assets/vessel_meta.json                         meta: attacks (slam, sweep), telegraphs, spawn (spew, slam)
    art/previews/vessel.png (3x, one row per tag), vessel_hitbox.png, vessel_closeup.png

A mountainous grotesque of fused hollowed bodies and fungus: one huge vertical maw splitting its front
face, two great knuckle-walking arms of bundled corpse-limbs, a fringe of small grasping arms along its
base, fungal spires on its hump, glowing rot-orange pustules.  Deliberately limited palette: ash-grey
corpse flesh (A), rot green (V), bone (B), gum-flesh (F, maw only), rot-orange glow (O).
Method: enemy_kit.py normal-field shading + sel-out outlines; the mass is a union of lumpy domes on a
Rig (lean / squash about the base) with noise-perturbed normals (wrinkled flesh); arms are 2-bone IK
limbs in frame coordinates.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, n_plate, n_dome, n_capsule, dirv)

W, H = 160, 128
K.setup(W, H)
FLOOR = H - 1
AX = 80
BUILD = "--preview" not in sys.argv
RGBA = K.RGBA
K.SMEAR["rotdark"] = ["O4", "V5", "V3", "V2"]
K.SMEAR["limb"] = ["O5", "O3", "V4", "V2"]

LAYERS = ["FXBack", "FarArm", "BackGrowth", "Body", "Maw", "SmallArms", "NearArm", "Spew", "FX"]
FXL = {"FXBack", "Spew", "FX"}
PIV = (80.0, 127.0)

# ---------------------------------------------------------------- the mass (model coords, upright)
LUMPS = [  # cx, cy, rx, ry, bias
    (34, 100, 14, 17, -1), (46, 113, 25, 15, -1), (80, 111, 31, 17, 0), (110, 113, 22, 14, 0),
    (58, 88, 26, 24, 0), (88, 86, 25, 24, 0), (110, 92, 15, 17, 0),
    (62, 63, 21, 21, 0), (83, 66, 19, 18, 0),
    (57, 50, 11, 11, -1), (69, 43, 14, 15, 0),
    (110, 62, 17, 22, 0), (114, 88, 14, 14, 0),
]
MAW = (114.0, 61.0)
CORPSES = [  # torso centre, angle (deg, 0 = lying head-right), scale, eye glow
    ((49, 80), -30, 1.0, 1), ((92, 58), 25, 0.9, 0), ((40, 105), 10, 1.0, 1), ((76, 97), -12, 1.1, 0),
    ((70, 35), -80, 0.9, 1), ((100, 106), 35, 0.9, 1), ((64, 112), 170, 0.9, 0),
]
PUSTULES = [  # centre, radius
    ((58, 70), 2.0), ((62, 74), 1.3), ((54, 73), 1.0), ((94, 76), 1.8), ((98, 72), 1.1), ((79, 50), 1.6),
    ((83, 53), 1.0), ((45, 93), 1.7), ((41, 90), 1.1), ((86, 100), 1.5), ((90, 104), 1.0), ((102, 60), 1.3),
    ((69, 90), 1.2), ((30, 104), 1.2), ((115, 104), 1.4), ((73, 26), 1.1),
]
SPIRES = [  # base, tip, radius, cap
    ((66, 36), (58, 9), 3.4, 3.8), ((76, 34), (84, 17), 2.8, 2.8), ((57, 46), (41, 28), 2.8, 3.0),
    ((82, 44), (95, 33), 2.0, 2.0),
]
SHELVES = [((40, 71), 7, 3.2), ((37, 80), 6, 2.8), ((45, 63), 5, 2.4), ((95, 44), 5, 2.4)]
BONES = [((50, 58), (40, 44), 1.4), ((47, 66), (33, 58), 1.2), ((88, 48), (96, 36), 1.2)]
SMALL = [  # root (model), rest hand offset, front?
    ((36, 116), (-10, 0), 0), ((50, 120), (-5, 0), 1), ((63, 121), (-3, 0), 0), ((76, 122), (1, 0), 1),
    ((90, 121), (4, 0), 0), ((101, 120), (6, 0), 1), ((118, 117), (8, 0), 1), ((126, 110), (12, 0), 0),
]
SH_N = (103.0, 93.0)    # near shoulder (model): below the maw so the face stays clear
SH_F = (56.0, 76.0)     # far shoulder (model)

NEU = dict(rot=0.0, sy=1.0, off=(0.0, 0.0), open=0.25, nh=(146.0, 125.0), nhd=10.0, ncurl=0.3, nspread=1.0,
           fh=(28.0, 125.0), fhd=170.0, fcurl=0.3, fspread=1.0, glow=0.5, sph=0.0, twitch=0.0, smear=None,
           fsm=None, floor_streak=0, impact=0, spew=0, dust=0, burst=0, eye=1, drool=0,
           nel=None, fel=None, shake=0, tele=None, melt=0.0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


# =========================================================================== helpers
def vnoise(x, y, sc, seed):
    """Smooth value noise (bilinear over a hashed grid), 0..1."""
    gx, gy = x / sc, y / sc
    x0, y0 = math.floor(gx), math.floor(gy)
    tx, ty = gx - x0, gy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = hash01(x0, y0, seed); b = hash01(x0 + 1, y0, seed)
    c = hash01(x0, y0 + 1, seed); d = hash01(x0 + 1, y0 + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fleshify(L, mats=("A", "V"), sc=4.5, k=0.9, seed=7, R=None):
    """Perturb normals with a noise height-field: lumpy, wrinkled flesh instead of smooth plastic domes."""
    ox, oy = (R.off if R else (0, 0))
    for (x, y), e in L.px.items():
        if e[0] not in mats or e[3] is not None:
            continue
        X, Y = x - ox, y - oy
        gx = vnoise(X + 1, Y, sc, seed) - vnoise(X - 1, Y, sc, seed)
        gy = vnoise(X, Y + 1, sc, seed) - vnoise(X, Y - 1, sc, seed)
        g2 = vnoise(X + 1, Y, sc * 0.45, seed + 1) - vnoise(X - 1, Y, sc * 0.45, seed + 1)
        h2 = vnoise(X, Y + 1, sc * 0.45, seed + 1) - vnoise(X, Y - 1, sc * 0.45, seed + 1)
        n = e[1]
        e[1] = K.norm3(n[0] - (gx + g2 * 0.5) * k * 2.2, n[1] - (gy + h2 * 0.5) * k * 2.2, n[2])


def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def pustule(L, c, r, hot):
    """Glowing boil: fixed colours so it reads as light; outlined like everything else."""
    m = mask_disc(c, r + 0.45)
    L.fill(m, "O1" if not hot else "O2")
    L.fill(mask_disc(c, max(0.55, r - 0.2)), "O3" if hot else "O2")
    if r > 1.2:
        L.fill(mask_disc(c, r * 0.45), "O4")
    L.decal([ip((c[0] - 0.4, c[1] - 0.4))], "O5" if hot else "O4")
    return m


def glow_halo(FX, L, c, r, k):
    """Sparse dithered halo of light around a pustule (drawn only on empty pixels)."""
    for a in range(0, 360, 30):
        q = ip((c[0] + math.cos(math.radians(a + k * 13)) * (r + 1.8), c[1] + math.sin(math.radians(a + k * 13)) * (r + 1.8)))
        if q not in L.px and hash01(q[0], q[1], k) < 0.5:
            FX.put([q], "O2")


# =========================================================================== parts
def draw_mass(R, Bd, Bg, p, fi, info):
    glow = p["glow"]
    mass = set()
    for k, (cx, cy, rx, ry, bias) in enumerate(LUMPS):
        br = 1.0 + 0.03 * math.sin(fi * 0.9 + k)            # lumps breathe out of phase
        m = R.dome(Bd, (cx, cy), rx * br, ry * br, "A", bias=bias, flat=0.85,
                   tilt=(0.05 * math.sin(k * 1.7), 0.08))
        mass |= m
    info["mass"] = set(mass)
    fleshify(Bd, R=R)
    # rot-green blotches creeping up from the base (smooth noise, so they read as patches, not camo)
    ox, oy = R.off
    for q in list(Bd.px):
        e = Bd.px[q]
        if e[0] != "A":
            continue
        X, Y = q[0] - ox, q[1] - oy
        base_t = (Y - 70) / 55.0
        n = vnoise(X, Y, 9.0, 12) * 0.75 + vnoise(X, Y, 3.0, 13) * 0.25
        if n + base_t * 0.35 > 0.66:
            e[0] = "V"
            if n + base_t * 0.35 < 0.69:
                e[2] -= 1
    # veins
    for k in range(9):
        a = hash01(k, 1, 14) * 6.28
        p0 = (40 + hash01(k, 2, 14) * 70, 50 + hash01(k, 3, 14) * 60)
        pts = [p0]
        for j in range(5):
            a += (hash01(k, j, 15) - 0.5) * 1.4
            pts.append(add(pts[-1], (math.cos(a) * 4, math.sin(a) * 4)))
        Bd.decal(polyline([R.T(q) for q in pts]), ("A", 1), only_on=("A",))
    # embedded bodies: rib-cages, skulls, draped arms
    for k, (c, ang, s, eye) in enumerate(CORPSES):
        ca, sa = dirv(ang)
        f = lambda u, v: (c[0] + (ca * u - sa * v) * s, c[1] + (sa * u + ca * v) * s)
        R.cap(Bd, f(-6, 0), f(3, 0), 3.8 * s, 3.2 * s, "A", bias=0, ao=1)        # torso
        for j in range(4):                                                     # ribs
            u = -4.5 + j * 2.2
            Bd.decal(line(R.T(f(u, -3.0)), R.T(f(u + 0.8, 3.0))), ("B", 2 if j % 2 else 3))
        hd = f(6.6, 0)
        R.dome(Bd, hd, 3.2 * s, 3.0 * s, "B", bias=-1, ao=1)                  # skull
        e1, e2 = R.pt(f(7.4, -1.2)), R.pt(f(7.4, 1.2))
        Bd.decal([e1, e2], "OUT")
        Bd.decal([R.pt(f(8.8, 0))], ("B", 0))
        if eye and p["eye"]:
            Bd.decal([e1], "O4" if glow > 0.6 else "O3")
        R.cap(Bd, f(1.5, -3.0), f(-2.0, -9.5), 1.3 * s, 1.0 * s, "A", bias=1, ao=1)    # draped arms
        R.cap(Bd, f(1.0, 3.0), f(4.5, 9.0), 1.3 * s, 1.0 * s, "A", bias=0, ao=1)
        R.dome(Bd, f(-2.0, -9.5), 1.3 * s, 1.3 * s, "B", 0)
    # shelf fungus on the hump's back
    for k, (c, rx, ry) in enumerate(SHELVES):
        m = R.dome(Bd, c, rx, ry, "B", bias=-1, flat=0.7, tilt=(0.0, -0.3))
        under = [q for q in m if (q[0], q[1] + 1) not in m]
        Bd.decal(under, "O3" if glow > 0.3 else "O2")
        gills = [q for q in m if (q[0] + k) % 2 == 0 and (q[0], q[1] + 2) not in m and (q[0], q[1] + 1) in m]
        Bd.decal(gills, ("B", 1))
    # the maw's brow: a heavy overhang of fused skulls above the mouth
    for k, (dx, dy, r) in enumerate(((-6, -22, 3.2), (-1, -24, 3.6), (4, -21.5, 3.0), (-10, -18, 2.6))):
        cc = add(MAW, (dx, dy))
        R.dome(Bd, cc, r, r * 0.9, "B", bias=-1 if k == 3 else 0, ao=1)
        e = R.pt(add(cc, (1.0, 0.3)))
        Bd.decal([e, (e[0] - 1, e[1])], "OUT")
        if p["eye"] and k in (0, 1, 2):
            Bd.decal([e], "O5" if (p["eye"] == 2 or glow > 0.9) else "O4")
    info["brow"] = R.T(add(MAW, (-1, -24)))

    # back growths: fungal spires + bone spikes (behind the mass, spiky silhouette)
    sw = math.sin(fi * 0.7) * 0.8 + p["twitch"] * 0.6
    for k, (b0, tip, r, cap) in enumerate(SPIRES):
        t2 = add(tip, (sw * (1 + k * 0.3), 0))
        mid = add(lerp(b0, t2, 0.5), (2.5 if k % 2 else -2.5, 0))
        pts = bezier(b0, mid, lerp(mid, t2, 0.6), t2, n=8)
        tube(R, Bg, pts, r, r * 0.35, "A", bias=0)
        for q in list(Bg.px):
            if Bg.px[q][0] == "A" and vnoise(q[0], q[1], 3.0, 50 + k) > 0.55:
                Bg.px[q][0] = "V"
        # lopsided bracket caps up the stalk, gills glowing underneath
        for j, (t, sc_) in enumerate(((1.0, 1.0), (0.62, 0.7))):
            cc = add(pts[int(t * (len(pts) - 1))], (cap * 0.35 * (1 if (k + j) % 2 else -1), -0.4))
            m = R.dome(Bg, cc, cap * sc_, cap * 0.55 * sc_, "B", bias=0, flat=0.8, tilt=(0.0, -0.3))
            under = [q for q in m if (q[0], q[1] + 1) not in m]
            Bg.decal(under, "O4" if glow > 0.5 else "O3")
    for (b0, tip, r) in BONES:
        tube(R, Bg, [b0, lerp(b0, tip, 0.5), tip], r, 0.5, "B", bias=0)

    # pustules
    info["pustules"] = []
    for k, (c, r) in enumerate(PUSTULES):
        pulse = 0.85 + 0.25 * math.sin(fi * 1.3 + k * 1.9) * glow + 0.25 * glow
        rr = r * pulse * (1.0 + 0.5 * p["burst"] * (k % 2) / 4)
        q = R.T(c)
        pustule(Bd, q, rr, hot=glow > 0.55 or (k + fi) % 5 == 0)
        info["pustules"].append((q, rr))
    return mass


def draw_maw(R, Mw, p, fi, info):
    """One huge vertical maw on the front face: an almond slit splitting the face, fleshy lips,
    interleaved fangs from both jaws (left/right), rings of throat receding to a rot-orange glow."""
    o = max(0.0, min(1.2, p["open"]))
    c = R.T(MAW)
    rx, ry = 3.0 + 7.5 * o, 10.0 + 11.0 * o
    lean = math.radians(p["rot"])
    cl, sl = math.cos(-lean), math.sin(-lean)

    def local(x, y):
        ux, uy = (x + .5 - c[0]), (y + .5 - c[1])
        return ux * cl - uy * sl, ux * sl + uy * cl

    def half_w(uy, grow=0.0):
        t = min(1.0, abs(uy) / (ry + grow))
        return (rx + grow) * (1 - t * t) ** 0.75
    inner, lips = set(), {}
    for y in range(int(c[1] - ry - 6), int(c[1] + ry + 7)):
        for x in range(int(c[0] - rx - 6), int(c[0] + rx + 7)):
            ux, uy = local(x, y)
            if abs(uy) <= ry and abs(ux) <= half_w(uy):
                inner.add((x, y))
            elif abs(uy) <= ry + 3.5 and abs(ux) <= half_w(uy, 3.4):
                # lip: a rolled torus of flesh; normal points away from the slit
                hw = max(0.5, half_w(uy))
                t = (abs(ux) - hw) / 3.4
                k = (t - 0.45) * 2.2
                nx = (1 if ux > 0 else -1) * k
                ny = (uy / (ry + 3.5)) * 0.8
                lips[(x, y)] = K.norm3(nx * 0.8, ny, 0.7)
    Mw.paint(lips, "F", bias=0, ao=0)
    for (x, y) in lips:                       # lip wrinkles
        ux, uy = local(x, y)
        if int(uy + 40) % 4 == 0 and hash01(x, y, 22) < 0.7:
            Mw.decal([(x, y)], ("F", 1))
    # gullet: receding rings toward a glowing throat low in the mouth
    hot = p["spew"] in (1, 2, 3) or p["glow"] > 0.95
    for q in inner:
        ux, uy = local(*q)
        hw = max(0.6, half_w(uy))
        d = max(abs(ux) / hw, abs(uy) / ry) if o > 0.2 else abs(ux) / hw
        dd = math.hypot(ux / max(rx, 1), (uy - ry * 0.25) / ry)
        if o < 0.2:
            col = "F0"
        elif dd < 0.28:
            col = "O4" if hot else "O3"
        elif dd < 0.45:
            col = "O3" if hot else "O2"
        elif dd < 0.62:
            col = "O1" if int(dd * 30) % 3 else "O2"
        elif d > 0.82:
            col = "F0"
        else:
            col = "F1" if int(dd * 22) % 3 else "F0"
        Mw.fill([q], col)
    # fangs: from each jaw (left/right edge), interleaved, uneven, hooked slightly inward-down
    n = 6
    for side in (-1, 1):
        for k in range(n):
            v = -0.82 + 1.64 * (k + (0.5 if side > 0 else 0.0)) / n
            uy = v * ry
            hw = half_w(uy)
            ln = (2.2 + 3.2 * hash01(k, side + 2, 20)) * (0.6 + 0.5 * o) * (1 - abs(v) * 0.4)
            ln = min(ln, hw * 1.6 + 1.5)
            base_u = side * (hw + 0.8)
            tip_u = side * (hw + 0.8) - side * ln
            wv = 1.2 + 0.5 * hash01(k, side, 23)
            pts = [(base_u, uy - wv), (base_u, uy + wv), (tip_u, uy + 0.6 + ln * 0.18)]
            fr = [(c[0] + u * cl + w * sl, c[1] - u * sl + w * cl) for u, w in pts]
            m = K.poly_mask(fr) | set(line(fr[0], fr[2])) | set(line(fr[1], fr[2]))
            Mw.paint(n_plate(m, 1.0, (0.35 * side * -1, -0.25), 1.0), "B", bias=0, ao=0)
    for sgn in (-1, 1):   # a fang at each point of the almond
        tip0 = (c[0] - sl * sgn * (ry + 1.5), c[1] + cl * sgn * (ry + 1.5))
        tip1 = (c[0] - sl * sgn * (ry - 3.5 - 2 * o), c[1] + cl * sgn * (ry - 3.5 - 2 * o))
        m = set(line(tip0, tip1)) | set(line(add(tip0, (1, 0)), tip1))
        Mw.paint(n_plate(m, 1.0, (0.0, -0.3), 1.0), "B", bias=0, ao=0)
    # drool strands between the jaws
    if p["drool"] and o > 0.35:
        for k in range(3):
            x = c[0] - rx * 0.45 + k * rx * 0.45 + (hash01(k, fi, 21) - 0.5)
            y0 = c[1] - ry * 0.55 + k * 2
            ln = ry * (0.7 + 0.5 * hash01(k, 2, 21))
            for j in range(int(ln)):
                q = ip((x + math.sin(j * 0.5 + k) * 0.5, y0 + j))
                if q in inner:
                    Mw.fill([q], "V4" if j % 3 else "V5")
    info["maw"] = c
    info["maw_inner"] = inner
    info["maw_r"] = (rx, ry)


def draw_hand(R, L, hand, ang, curl, spread, bias, scale=1.0, planted=False):
    """Great claw: palm + four bundled-corpse fingers with bone talons."""
    m = set()
    m |= L.paint(n_dome(hand, 5.6 * scale, 5.0 * scale, 0.9), "A", bias, ao=1)
    for k in range(4):
        da = (-42 + k * 26) * spread
        a = ang + da
        base = add(hand, (math.cos(math.radians(a)) * 4.2 * scale, math.sin(math.radians(a)) * 4.2 * scale))
        a2 = a + curl * 70 * (1 if math.cos(math.radians(ang)) >= 0 else -1)
        kn = add(base, (math.cos(math.radians(a)) * 5.0 * scale, math.sin(math.radians(a)) * 5.0 * scale))
        tp = add(kn, (math.cos(math.radians(a2)) * 4.6 * scale, math.sin(math.radians(a2)) * 4.6 * scale))
        if planted:
            kn = (kn[0], min(kn[1], FLOOR - 1.5))
            tp = (tp[0], min(tp[1], FLOOR - 0.5))
        m |= L.paint(n_capsule(base, kn, 2.2 * scale, 1.9 * scale), "A", bias, ao=1)
        m |= L.paint(n_capsule(kn, tp, 1.8 * scale, 0.9 * scale), "A", bias, ao=1)
        L.paint(n_dome(kn, 1.5 * scale, 1.5 * scale), "B", bias - 1, ao=0)     # knuckle bone
        claw_tip = add(tp, (math.cos(math.radians(a2)) * 3.2 * scale, math.sin(math.radians(a2)) * 3.2 * scale))
        if planted:
            claw_tip = (claw_tip[0], min(claw_tip[1], FLOOR))
        m |= L.paint(n_capsule(tp, claw_tip, 1.0 * scale, 0.4), "B", bias + 1, ao=0)
    # thumb
    a = ang + 70 * spread * (1 if math.cos(math.radians(ang)) >= 0 else -1)
    tb = add(hand, (math.cos(math.radians(a)) * 5.5 * scale, math.sin(math.radians(a)) * 5.5 * scale))
    m |= L.paint(n_capsule(hand, tb, 2.0 * scale, 1.2 * scale), "A", bias, ao=1)
    return m


def draw_arm(R, L, sh_model, hand, hang, curl, spread, bias, info, key, elbow=None, planted=False, scale=1.0):
    """Arm of bundled corpse limbs (frame coords for the hand), bony elbow, fused-limb grooves."""
    sh = R.T(sh_model)
    l1, l2 = 31.0 * scale, 29.0 * scale
    el = elbow or ik(sh, hand, l1, l2, (0.7, -1) if hand[0] > sh[0] else (-0.7, -1))
    m = set()
    ab = bias + 1                          # desiccated limbs: paler than the mass so the arm reads
    m |= L.paint(n_capsule(sh, el, 8.0 * scale, 6.4 * scale), "A", ab, ao=1)
    m |= L.paint(n_capsule(el, hand, 6.2 * scale, 4.6 * scale), "A", ab, ao=1)
    fleshify(L, mats=("A",), sc=3.5, k=0.7, seed=31)
    # fused limbs: grooves running along the arm + a second, thinner arm twisted around it
    for seg, (a_, b_, r_) in enumerate(((sh, el, 6.0), (el, hand, 4.6))):
        d = sub(b_, a_)
        ln = math.hypot(*d) or 1
        nrm = (-d[1] / ln, d[0] / ln)
        for off in (-0.45, 0.2):
            o = off * r_ * scale
            L.decal(line(add(a_, (nrm[0] * o, nrm[1] * o)), add(b_, (nrm[0] * o * 0.8, nrm[1] * o * 0.8))), ("A", 1))
    tw = [lerp(sh, el, t) for t in (0.1, 0.45, 0.8)] + [lerp(el, hand, t) for t in (0.3, 0.7)]
    tw = [add(q, (math.sin(i * 2.1) * 3.5 * scale, math.cos(i * 2.1) * 3.0 * scale)) for i, q in enumerate(tw)]
    m |= tube(ID, L, tw, 2.2 * scale, 1.4 * scale, "A", ab + 1, ao=1)
    L.paint(n_dome(add(el, (0, -1.5)), 4.0 * scale, 3.4 * scale), "B", bias, ao=1)      # elbow skull-cap
    e = ip(add(el, (1.2, -1.2)))
    L.decal([e, (e[0] - 2, e[1])], "OUT")
    # rot and a boil or two
    for q in list(L.px):
        if vnoise(q[0], q[1], 4.0, 30 + len(key)) > 0.7 and L.px[q][0] == "A":
            L.px[q][0] = "V"
    pustule(L, lerp(sh, el, 0.45), 1.5 * scale, hot=True)
    pustule(L, add(lerp(el, hand, 0.4), (0, -2)), 1.1 * scale, hot=False)
    m |= draw_hand(R, L, hand, hang, curl, spread, bias, scale, planted)
    info[key] = {"sh": sh, "el": el, "hand": hand, "mask": m}
    return m


def draw_small_arms(R, Sm, Fa, p, fi, info):
    ph = p["sph"]
    for k, (root_m, rest, front) in enumerate(SMALL):
        root = R.T(root_m)
        t = ph * 6.283 + k * 1.7
        reach = 5 + 4 * math.sin(t)
        lift = max(0.0, math.cos(t)) * 4 * (1 if p["sph"] else 0.3) + p["twitch"] * hash01(k, fi, 40) * 3
        hand = (root[0] + rest[0] + reach * (1 if rest[0] >= 0 else -0.6), FLOOR - 1 - lift)
        L = Sm if front else Fa
        el = ik(root, hand, 7.0, 7.0, (0.3 if rest[0] >= 0 else -0.3, -1))
        L.paint(n_capsule(root, el, 1.9, 1.6), "A", 0 if front else -1, ao=1)
        L.paint(n_capsule(el, hand, 1.6, 1.2), "A", 0 if front else -1, ao=1)
        L.paint(n_dome(el, 1.3, 1.3), "B", -1, ao=0)
        for j in (-1, 0, 1):                       # bony fingers
            L.fill([ip(add(hand, (j * 1.0 + (1 if rest[0] >= 0 else -1), 1 if lift < 1 else 0.5)))], "B3")
        L.fill([ip(hand)], "B2")


# =========================================================================== fx
def limb_smear(FX, piv, hands, pal):
    """Heavy-limb smear: the fan swept by the forearm + claw about the shoulder, oldest hand first.
    Newest edge hot, older parts fall back to streaked rot-green."""
    cols = K.SMEAR[pal]
    hot = set()
    polar = []
    for h in hands:
        d = sub(h, piv)
        polar.append((math.atan2(d[1], d[0]), math.hypot(*d)))
    for i in range(1, len(polar)):          # unwrap angles
        a0, a1 = polar[i - 1][0], polar[i][0]
        while a1 - a0 > math.pi:
            a1 -= 2 * math.pi
        while a1 - a0 < -math.pi:
            a1 += 2 * math.pi
        polar[i] = (a1, polar[i][1])
    n = len(polar) - 1
    best = {}
    span = sum(abs(polar[i + 1][0] - polar[i][0]) for i in range(n)) * max(r for _, r in polar)
    span += sum(math.hypot(*sub(hands[i + 1], hands[i])) for i in range(n))
    steps = max(60, int(span * 2.2))
    for si in range(steps + 1):
        tg = si / steps
        seg = min(n - 1, int(tg * n))
        tl = tg * n - seg
        ang = polar[seg][0] + (polar[seg + 1][0] - polar[seg][0]) * tl
        rad = polar[seg][1] + (polar[seg + 1][1] - polar[seg][1]) * tl
        age = 1 - tg
        r0 = rad * (0.62 + 0.3 * age)
        r1 = rad + 9
        rr = r0
        while rr <= r1:
            q = ip((piv[0] + math.cos(ang) * rr, piv[1] + math.sin(ang) * rr))
            ed = r1 - rr
            if q not in best or best[q][0] > age:
                best[q] = (age, ed)
            rr += 0.5
    for q, (age, ed) in best.items():
        if not K.inb(*q) or q[1] > FLOOR:
            continue
        if age > 0.62 and ed > 3 and int(ed / 2.5) % 2 == 1:
            continue
        if age > 0.8 and ed > 2:
            continue
        if age < 0.18:
            c = cols[0] if ed < 3 else cols[1]
        elif age < 0.4:
            c = cols[1] if ed < 2.5 else cols[2]
        elif age < 0.7:
            c = cols[2] if (q[0] + q[1]) % 3 else cols[3]
        else:
            c = cols[3]
        FX.put([q], c)
        if age < 0.75:
            hot.add(q)
    return hot


def impact(FX, FXB, x, stage, info, width=1.0):
    pts = set()
    for k in range(34):
        a = -math.pi * (0.04 + 0.92 * hash01(k, 7, 50))
        r = (4 + 26 * hash01(k, 8, 51)) * (0.55 if stage == 1 else 1.0) * width
        q = ip((x + math.cos(a) * r * 1.3, FLOOR - 1 + math.sin(a) * r * (0.8 if stage == 1 else 0.6)
                + (0 if stage == 1 else 3 * (r / 12) ** 2)))
        c = ("O5", "O4", "V5", "V4", "A3")[k % 5] if stage == 1 else ("V4", "A3", "A2", "V3")[k % 4]
        if K.inb(*q):
            FX.put([q], c)
            if k % 3 == 0:
                FX.put([(q[0] + 1, q[1])], c)
            pts.add(q)
    for s in (-1, 1):   # dust clouds rolling along the floor
        for k in range(10):
            cx = x + s * (6 + k * 3.2 * (1.4 if stage == 2 else 1.0))
            cy = FLOOR - 2 - hash01(k, s, 53) * (4 if stage == 1 else 7)
            rr = 1.4 + hash01(k, s, 54) * 2.2 * (1.3 if stage == 2 else 1.0)
            for q in mask_disc((cx, cy), rr):
                if K.inb(*q) and q[1] <= FLOOR:
                    (FXB if stage == 2 else FX).put([q], "A2" if (q[0] + q[1]) % 3 else "A3")
                    pts.add(q)
    for dx in range(-24, 25):
        if hash01(dx, 3, 52) < 0.8 and K.inb(x + dx, FLOOR):
            FX.put([(int(x + dx), FLOOR)], "O4" if abs(dx) < 4 else "O2" if stage == 1 else "V3")
    if stage == 1:
        for ang in range(-170, -5, 17):
            FX.put([q for q in line((x, FLOOR - 1), (x + math.cos(math.radians(ang)) * 16, FLOOR - 1 + math.sin(math.radians(ang)) * 12))
                    if K.inb(*q)], "O5" if ang % 34 == 0 else "O3")
    info["hit"] |= pts
    info["impact_x"] = int(x)


def spew_stream(Sp, FX, maw, stage, fi, info):
    """Projectile vomit: a thick gush of rot jetting forward out of the maw and off-frame."""
    if stage == 0:
        return
    pts = set()
    reach = {1: 0.3, 2: 0.75, 3: 1.0, 4: 1.0, 5: 0.8, 6: 0.35}[stage]
    thick = {1: 4.0, 2: 5.2, 3: 5.6, 4: 4.8, 5: 3.2, 6: 1.8}[stage]
    start = (maw[0] + 1, maw[1] + 3)
    end = (start[0] + 30 * reach, start[1] + (FLOOR - 1 - start[1]) * reach)
    ctrl = (start[0] + 26 * reach, start[1] - 3 * reach)
    path = [((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * ctrl[0] + t * t * end[0],
             (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * ctrl[1] + t * t * end[1]) for t in [i / 22 for i in range(23)]]
    if stage >= 5:
        path = path[int(len(path) * (0.35 if stage == 5 else 0.65)):]
    body = {}
    for i, c in enumerate(path):
        t = i / max(1, len(path) - 1)
        r = thick * (1.2 - 0.4 * t) * (0.75 + 0.5 * hash01(i, fi, 66))
        if t > 0.7 and i % 2 == 1 and stage < 3:
            continue                                  # the far end breaks up into separate gobbets
        if t > 0.7:
            c = add(c, ((hash01(i, fi, 67) - 0.5) * 3, 0))
        j = min(len(path) - 1, i + 1)
        tg = sub(path[j], path[max(0, j - 1)])
        tl = math.hypot(*tg) or 1.0
        nrm = (-tg[1] / tl, tg[0] / tl)
        if nrm[0] + nrm[1] > 0:                 # normal pointing to the light (upper left)
            nrm = (-nrm[0], -nrm[1])
        for q in mask_disc(c, r):
            if not K.inb(*q) or q[1] > FLOOR:
                continue
            dy = -((q[0] + .5 - c[0]) * nrm[0] + (q[1] + .5 - c[1]) * nrm[1]) / max(r, 0.5)
            if q not in body or abs(dy) < abs(body[q][0]):
                body[q] = (dy, t)
    for q, (dy, t) in body.items():
        if dy < -0.45:
            col = "V5"
        elif dy < 0.1:
            col = "V4" if hash01(q[0] // 2, q[1], fi + 60) > 0.18 else ("O4" if t < 0.5 else "O3")
        elif dy < 0.6:
            col = "V3" if hash01(q[0], q[1] // 3 + fi, 69) > 0.2 else "V4"
        else:
            col = "V2"
        Sp.put([q], col)
        pts.add(q)
    for (x, y) in list(body):                # 1px outline around the whole gush
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and K.inb(*q) and q[1] <= FLOOR and hash01(q[0], q[1], 65) < 0.92:
                Sp.put([q], "OUT")
    for k in range(30):     # spatter flung off the stream (falls under gravity)
        t = hash01(k, fi, 61)
        c = path[min(len(path) - 1, int(t * len(path)))]
        q = ip(add(c, ((hash01(k, 2, 62) - 0.2) * 16, (hash01(k, 3, 62) - 0.25) * 10 + 8 * t * t)))
        if K.inb(*q) and q[1] <= FLOOR:
            FX.put([q, (q[0] + 1, q[1])], ("V5", "V4", "O3")[k % 3])
            if k % 3 == 0 and K.inb(q[0], q[1] + 1):
                FX.put([(q[0], q[1] + 1)], "V3")
            pts.add(q)
    ex = path[-1][0]
    if stage in (3, 4, 5) and path[-1][1] > FLOOR - 12:
        for k in range(16):
            a = -math.pi * hash01(k, stage, 63)
            r = 3 + hash01(k, 4, 63) * 12
            q = ip((min(ex, W - 4) + math.cos(a) * r * 1.3, FLOOR - 1 + math.sin(a) * r * 0.7))
            if K.inb(*q):
                FX.put([q], ("V5", "V4", "O4", "V3")[k % 4])
                pts.add(q)
    if stage >= 3:
        x0 = int(start[0] + 18)
        for x in range(x0, W):
            if hash01(x, 9, 64) < 0.85:
                Sp.put([(x, FLOOR)], "V3" if x % 4 else "V4")
                if hash01(x, 10, 64) < 0.5:
                    Sp.put([(x, FLOOR - 1)], "V2")
    info["spew"] = pts


def burst_fx(FX, pustules, stage, fi):
    """Death: pustules rupture in orange sprays."""
    for k, (c, r) in enumerate(pustules):
        if (k + stage) % 3 != 0:
            continue
        for j in range(8):
            a = hash01(k, j, 70) * 6.283
            d = (2 + hash01(k, j, 71) * 7) * (1 + stage * 0.3)
            q = ip((c[0] + math.cos(a) * d, c[1] + math.sin(a) * d * 0.8 + stage))
            if K.inb(*q):
                FX.put([q], ("O5", "O4", "O3", "V4")[j % 4])


def tele_star(FX, c):
    x, y = ip(c)
    FX.put([(x, y)], "O5")
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], "O5")
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0), (0, 3), (0, -3)):
        FX.put([(x + d[0], y + d[1])], "O4")
    for d in ((4, 0), (-4, 0), (5, 0), (-5, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)):
        FX.put([(x + d[0], y + d[1])], "O3")


# =========================================================================== frame
def draw(p, fi):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB, Sp = FXLayer("FX"), FXLayer("FXBack"), FXLayer("Spew")
    Ls["FX"], Ls["FXBack"], Ls["Spew"] = FX, FXB, Sp
    R = Rig(p["rot"], PIV, p["off"], 1.0 + (1 - p["sy"]) * 0.5, p["sy"])
    info = {"hit": set()}
    draw_mass(R, Ls["Body"], Ls["BackGrowth"], p, fi, info)
    draw_maw(R, Ls["Maw"], p, fi, info)
    draw_arm(R, Ls["NearArm"], SH_N, p["nh"], p["nhd"], p["ncurl"], p["nspread"], 0, info,
             "near", elbow=p["nel"], planted=p["nh"][1] > FLOOR - 6)
    draw_arm(R, Ls["FarArm"], SH_F, p["fh"], p["fhd"], p["fcurl"], p["fspread"], -1, info,
             "far", elbow=p["fel"], planted=p["fh"][1] > FLOOR - 6, scale=0.92)
    draw_small_arms(R, Ls["SmallArms"], Ls["FarArm"], p, fi, info)
    # the near arm casts a shadow down-right onto the mass (light from the upper left)
    arm = set(Ls["NearArm"].px)
    shadow = {(x + dx, y + dy) for (x, y) in arm for dx, dy in ((2, 2), (3, 3), (1, 3))} - arm
    Ls["Body"].shift(list(shadow), -1)
    Ls["Maw"].shift(list({(x + 2, y + 2) for (x, y) in arm} - arm), -1)
    for L in Ls.values():                 # nothing below the floor
        if isinstance(L, Layer):
            L.erase([q for q in list(L.px) if q[1] > FLOOR])
    if p["glow"] > 0.7:
        for k, (c, r) in enumerate(info["pustules"]):
            glow_halo(FXB, Ls["Body"], c, r, k)
    # fx
    if p["smear"]:
        info["hit"] |= limb_smear(FX, info["near"]["sh"], p["smear"], "limb" if not p["fsm"] else "rotdark")
    if p["fsm"]:
        info["hit"] |= limb_smear(FX, info["far"]["sh"], p["fsm"], "rotdark")
    if p["floor_streak"]:
        st = p["floor_streak"]
        for x0, x1 in ((96, 159), (64, 0)):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                t = abs(x - x0) / abs(x1 - x0)
                hgt = int(2 + 5 * t * (1.0 if st == 1 else 0.5))
                for y in range(FLOOR - hgt, FLOOR + 1):
                    if (x + y) % (2 if st == 1 else 3) == 0 or y == FLOOR:
                        col = "O4" if (t > 0.85 and st == 1) else "V4" if y > FLOOR - 2 else "V3" if st == 1 else "A2"
                        FX.put([(x, y)], col)
                        info["hit"].add((x, y))
    if p["impact"]:
        impact(FX, FXB, p["nh"][0] + 4, p["impact"], info, width=p.get("iw", 1.0))
    if p["spew"]:
        spew_stream(Sp, FX, info["maw"], p["spew"], fi, info)
    if p["burst"]:
        burst_fx(FX, info["pustules"], p["burst"], fi)
    if p["tele"]:
        tele_star(FX, p["tele"])
    if p["dust"]:
        for s in (-1, 1):
            for k in range(8):
                x = int(AX + s * (30 + k * 5 + hash01(k, fi, 80) * 4))
                y = FLOOR - int(hash01(k, fi, 81) * 3)
                if K.inb(x, y):
                    FX.put([(x, y)], ("A3", "A2")[k % 2])
    return Ls, info


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(6):
        b = math.sin(i / 6 * 6.283)
        fr.append((200, P_(sy=1.0 - 0.012 * (b + 1), open=0.22 + 0.08 * (b + 1), glow=0.45 + 0.2 * (b + 1),
                           twitch=0.5 * (i % 2))))
    return fr


def a_crawl():
    fr = []
    for i in range(8):
        t = i / 8
        s = math.sin(t * 6.283)
        c = math.cos(t * 6.283)
        # near hand reaches forward and plants, then drags the mass; far hand pushes from behind
        nx = 142 + 8 * c
        ny = FLOOR - 2 - max(0.0, s) * 14
        fx = 30 - 6 * c
        fy = FLOOR - 2 - max(0.0, -s) * 10
        lurch = 2.2 * math.sin(t * 6.283 - 1.2)
        fr.append((130, P_(rot=1.5 * math.sin(t * 6.283 - 0.8), sy=1.0 - 0.02 * abs(s), off=(lurch, -abs(s) * 1.2),
                           open=0.3 + 0.1 * c, glow=0.5 + 0.15 * s, nh=(nx, ny), nhd=10 - 30 * max(0, s),
                           ncurl=0.3 + 0.5 * max(0, s), fh=(fx, fy), fhd=170 + 25 * max(0, -s), sph=t,
                           dust=1 if i in (2, 6) else 0)))
    return fr


def a_slam():
    up_hand = (118.0, 14.0)
    return [
        (160, P_(rot=-2.0, sy=1.01, open=0.3, glow=0.6, nh=(134.0, 110.0), nhd=-20, ncurl=0.6, twitch=0.5)),
        (160, P_(rot=-5.0, sy=1.02, off=(-2, 0), open=0.45, glow=0.7, nh=(130.0, 60.0), nhd=-70, ncurl=0.5)),
        (160, P_(rot=-8.0, sy=1.03, off=(-3, 0), open=0.6, glow=0.85, nh=(122.0, 26.0), nhd=-100, ncurl=0.2,
                 nspread=1.3)),
        (360, P_(rot=-9.0, sy=1.03, off=(-3, 0), open=0.75, glow=1.0, nh=up_hand, nhd=-105, ncurl=0.1, nspread=1.4,
                 eye=2, drool=1, tele=(119, 6))),
        (70, P_(rot=4.0, sy=0.99, off=(2, 0), open=0.9, glow=1.0, nh=(148.0, 70.0), nhd=40, ncurl=0.5,
                smear=[up_hand, (134, 16), (144, 34), (148, 52), (148, 70)])),
        (90, P_(rot=7.0, sy=0.97, off=(3, 1), open=1.0, glow=1.0, nh=(142.0, 120.0), nhd=20, ncurl=0.2, nspread=1.3,
                impact=1, smear=[(148, 52), (148, 72), (146, 94), (142, 114)], shake=2)),
        (150, P_(rot=6.0, sy=0.97, off=(3, 1), open=0.8, glow=0.9, nh=(142.0, 121.0), nhd=15, ncurl=0.1, nspread=1.3,
                 impact=2, iw=1.1, shake=-1)),
        (180, P_(rot=4.0, sy=0.98, off=(2, 0), open=0.55, glow=0.75, nh=(141.0, 116.0), nhd=0, ncurl=0.3)),
        (200, P_(rot=1.5, sy=0.99, off=(1, 0), open=0.4, glow=0.6, nh=(144.0, 123.0), nhd=8, ncurl=0.3)),
        (220, P_(rot=0.0, open=0.3, glow=0.5)),
    ]


def a_sweep():
    return [
        (160, P_(sy=1.01, open=0.35, glow=0.6, nh=(130.0, 98.0), nhd=-30, ncurl=0.7, fh=(32.0, 100.0), fhd=210,
                 fcurl=0.7, twitch=0.5)),
        (160, P_(sy=1.03, off=(0, -1), open=0.5, glow=0.75, nh=(146.0, 70.0), nhd=-50, ncurl=0.2, nspread=1.3,
                 fh=(16.0, 74.0), fhd=225, fspread=1.3)),
        (160, P_(sy=1.04, off=(0, -2), open=0.6, glow=0.9, nh=(150.0, 56.0), nhd=-60, ncurl=0.0, nspread=1.4,
                 fh=(10.0, 60.0), fhd=238, fspread=1.4)),
        (340, P_(sy=1.04, off=(0, -2), open=0.7, glow=1.0, nh=(151.0, 54.0), nhd=-62, ncurl=0.0, nspread=1.5,
                 fh=(9.0, 58.0), fhd=240, fspread=1.5, eye=2, tele=(154, 48), drool=1)),
        (70, P_(sy=0.97, off=(0, 1), open=0.85, glow=1.0, nh=(150.0, 117.0), nhd=20, ncurl=0.2, nspread=1.3,
                fh=(10.0, 117.0), fhd=160, fcurl=0.2, fspread=1.3, shake=1, dust=1,
                smear=[(151, 54), (158, 80), (156, 102), (150, 117)],
                fsm=[(9, 58), (2, 84), (4, 104), (10, 117)])),
        (90, P_(sy=0.96, off=(0, 2), open=0.85, glow=1.0, nh=(152.0, 122.0), nhd=5, ncurl=0.3, nspread=1.3,
                fh=(8.0, 122.0), fhd=175, fcurl=0.3, fspread=1.3, dust=2, floor_streak=1,
                smear=[(156, 102), (152, 114), (152, 122)], fsm=[(4, 104), (8, 114), (8, 122)])),
        (130, P_(sy=0.97, off=(0, 1), open=0.6, glow=0.8, nh=(148.0, 124.0), nhd=0, ncurl=0.5, fh=(12.0, 124.0),
                 fhd=180, fcurl=0.5, dust=2, floor_streak=2)),
        (180, P_(sy=0.99, open=0.45, glow=0.65, nh=(144.0, 124.0), nhd=5, ncurl=0.4, fh=(18.0, 124.0), fhd=175)),
        (200, P_(open=0.35, glow=0.55, nh=(145.0, 125.0), nhd=8, fh=(24.0, 124.0), fhd=172)),
        (220, P_(open=0.3, glow=0.5)),
    ]


def a_spew():
    return [
        (150, P_(rot=-2.0, sy=1.01, open=0.15, glow=0.6, nh=(143.0, 124.0))),
        (160, P_(rot=-4.5, sy=1.03, off=(-2, 0), open=0.05, glow=0.75, nh=(141.0, 123.0), ncurl=0.6, twitch=1)),
        (160, P_(rot=-6.0, sy=1.05, off=(-3, -1), open=0.05, glow=0.9, nh=(140.0, 122.0), ncurl=0.7, twitch=1)),
        (200, P_(rot=-6.5, sy=1.06, off=(-3, -1), open=0.12, glow=1.0, nh=(140.0, 122.0), ncurl=0.7, shake=1, eye=2)),
        (260, P_(rot=-6.5, sy=1.06, off=(-3, -1), open=0.3, glow=1.1, nh=(140.0, 122.0), ncurl=0.7, shake=-1, eye=2,
                 tele=(118, 60))),
        (90, P_(rot=5.0, sy=0.98, off=(3, 0), open=1.05, glow=1.0, nh=(145.0, 124.0), ncurl=0.3, drool=1)),
        (90, P_(rot=6.0, sy=0.98, off=(3, 0), open=1.15, glow=1.0, nh=(146.0, 124.0), spew=1)),
        (100, P_(rot=6.0, sy=0.98, off=(3, 0), open=1.15, glow=0.95, nh=(146.0, 124.0), spew=2, shake=1)),
        (110, P_(rot=5.5, sy=0.98, off=(3, 0), open=1.1, glow=0.9, nh=(146.0, 124.0), spew=3, shake=-1)),
        (110, P_(rot=5.0, sy=0.98, off=(3, 0), open=1.0, glow=0.8, nh=(146.0, 124.0), spew=4)),
        (150, P_(rot=3.0, sy=0.99, off=(2, 0), open=0.7, glow=0.65, nh=(145.0, 124.0), spew=5, drool=1)),
        (200, P_(rot=0.5, open=0.35, glow=0.5, spew=6)),
    ]


def a_stagger():
    return [
        (100, P_(rot=-4.0, sy=1.02, off=(-3, 0), open=0.9, glow=0.3, nh=(132.0, 110.0), nhd=-40, ncurl=0.8,
                 fh=(22.0, 115.0), twitch=1, eye=0)),
        (160, P_(rot=3.0, sy=0.95, off=(1, 2), open=0.75, glow=0.2, nh=(138.0, 125.0), nhd=30, ncurl=0.9,
                 fh=(32.0, 125.0), eye=0, drool=1, nel=(133.0, 108.0))),
        (260, P_(rot=4.0, sy=0.93, off=(1, 3), open=0.7, glow=0.15, nh=(137.0, 125.0), nhd=35, ncurl=1.0,
                 fh=(33.0, 125.0), eye=0, drool=1, nel=(132.0, 110.0))),
        (260, P_(rot=3.5, sy=0.935, off=(1, 3), open=0.72, glow=0.25, nh=(137.0, 125.0), nhd=35, ncurl=1.0,
                 fh=(33.0, 125.0), eye=0, drool=1, twitch=1, nel=(132.0, 110.5))),
    ]


def a_death():
    fr = [
        (120, P_(rot=-5.0, sy=1.03, off=(-3, 0), open=1.1, glow=1.1, nh=(128.0, 60.0), nhd=-80, ncurl=0.0, nspread=1.5,
                 fh=(16.0, 90.0), fhd=220, twitch=1, eye=2, shake=2)),
        (120, P_(rot=-3.0, sy=1.02, off=(-2, 0), open=1.15, glow=1.1, nh=(132.0, 76.0), nhd=-60, ncurl=0.2, nspread=1.5,
                 fh=(20.0, 96.0), fhd=210, twitch=1, eye=2, shake=-2, burst=1)),
        (140, P_(rot=2.0, open=1.0, glow=1.0, nh=(138.0, 110.0), nhd=0, ncurl=0.6, fh=(26.0, 116.0), twitch=1, eye=2,
                 burst=2, shake=1)),
        (140, P_(rot=4.0, sy=0.97, off=(1, 1), open=0.95, glow=0.8, nh=(140.0, 124.0), nhd=20, ncurl=0.9,
                 fh=(28.0, 124.0), burst=3, eye=1)),
        (160, P_(rot=5.0, sy=0.94, off=(1, 2), open=0.9, glow=0.6, nh=(141.0, 125.0), nhd=25, ncurl=1.0,
                 fh=(29.0, 125.0), burst=4, eye=1, drool=1)),
        (200, P_(rot=5.0, sy=0.9, off=(1, 3), open=0.85, glow=0.4, nh=(142.0, 125.0), nhd=25, ncurl=1.0,
                 fh=(29.0, 125.0), eye=0, drool=1)),
    ]
    # the mass slumps and melts down into the floor as a spreading rot slick
    for k, (mf, ms) in enumerate(((0.12, 180), (0.26, 180), (0.42, 200), (0.6, 220), (0.8, 260), (1.0, 900))):
        fr.append((ms, P_(rot=5.0, sy=0.88, off=(1, 3), open=0.8, glow=max(0.0, 0.3 - k * 0.06),
                          nh=(142.0 + k * 1.5, 125.0), nhd=25, ncurl=1.0, fh=(28.0 - k, 125.0), eye=0, melt=mf)))
    return fr


TAGDEFS = [("idle", a_idle), ("crawl", a_crawl), ("slam", a_slam), ("sweep", a_sweep), ("spew", a_spew),
           ("stagger", a_stagger), ("death", a_death)]
COUNTS = dict(idle=6, crawl=8, slam=10, sweep=10, spew=12, stagger=4, death=12)


# =========================================================================== render
MELT_LAYERS = ["FarArm", "BackGrowth", "Body", "Maw", "SmallArms", "NearArm"]


def melt(imgs, frac, fi):
    """Death: the body sinks into the floor; the bottom rows smear into a rot slick; motes rise."""
    out = dict(imgs)
    drop = int(round(frac * 104))
    for n in MELT_LAYERS:
        if n not in imgs:
            continue
        src = imgs[n].load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                c = src[x, y]
                if c[3] == 0:
                    continue
                # columns sink at slightly different speeds -> a dripping, sagging top edge
                yy = y + drop + int(hash01(x // 3, 0, 5) * 6 * frac)
                if yy < FLOOR - 2:
                    dst[x, yy] = c
        out[n] = new
    # slick: spreads wider as the mass sinks, with bones left in it
    fx = out["FXBack"].copy()
    px = fx.load()
    half = 42 + 34 * frac
    for x in range(int(AX - half), int(AX + half) + 1):
        if not 0 <= x < W:
            continue
        t = abs(x - AX) / half
        hgt = int(round((1 - t ** 2) * (3 + 4 * frac)))
        top = FLOOR - hgt
        for y in range(top, H):
            px[x, y] = RGBA["V2" if y > top + 1 else "V4"]
        if top - 1 >= 0:
            px[x, top - 1] = RGBA["OUT"]
        if hash01(x, 3, 91) < 0.08 * frac and hgt > 1:
            px[x, top] = RGBA["O3"]
    for k in range(int(12 * frac)):
        x = int(AX - half * 0.7 + hash01(k, 1, 90) * half * 1.4)
        y = FLOOR - 1 - int(hash01(k, 2, 90) * 3)
        for j in range(3 + k % 3):
            if 0 <= x + j < W:
                px[x + j, y] = RGBA["B3" if j % 2 else "B4"]
    out["FXBack"] = fx
    f2 = out["FX"].copy()
    fp = f2.load()
    for k in range(int(26 * (1 - frac * 0.6))):       # rot motes rising off the melt
        x = int(AX - half * 0.8 + hash01(k, fi, 92) * half * 1.6)
        y = int(FLOOR - 6 - hash01(k, fi, 93) * (30 + 40 * (1 - frac)))
        if 0 <= x < W and 0 <= y < H:
            fp[x, y] = RGBA[("O4", "V5", "O3", "V4")[k % 4]]
    out["FX"] = f2
    return out


def render_frame(p, fi):
    Ls, info = draw(p, fi)
    imgs = {}
    for n in LAYERS:
        v = Ls.get(n)
        if v is None:
            continue
        imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
    if p["melt"] > 0:
        imgs = melt(imgs, p["melt"], fi)
    if p["shake"]:
        imgs = K.shift_imgs(imgs, p["shake"], 0)
    return imgs, info


def render_all(only=None):
    frames, infos, tags = [], {}, []
    for tag, fn in TAGDEFS:
        fr = fn()
        assert len(fr) == COUNTS[tag], (tag, len(fr))
        if only and tag not in only:
            continue
        a = len(frames)
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            imgs, info = render_frame(p, a + k)
            frames.append((ms, imgs))
            infos[tag].append(info)
        tags.append((tag, a, len(frames) - 1))
        print("rendered", tag, len(fr))
    return frames, infos, tags


# =========================================================================== previews / meta
BG = (92, 92, 98, 255)


def preview_rows(tags, flats, path, scale=3):
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 12
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(230, 230, 230, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                                  ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def hitbox_preview(tags, flats, meta, path, scale=3):
    start = {t: (a, b) for t, a, b in tags}
    rows = [(t, d["windows"] if "windows" in d else [d]) for t, d in meta["attacks"].items()]
    rows += [("spew", []), ("idle", [])]
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), (40, 40, 46, 255))
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        dd.text((4, y0 + 4), t + "   " + "   ".join(f"active {w['active']} hit {w['hit']}" for w in wins),
                fill=(230, 230, 230, 255))
        tg = meta.get("telegraph", {}).get(t)
        spn = meta.get("spawn", {}).get(t)
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            rect(meta["weakpoint"], (230, 230, 60, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rr = w.get("rects", {}).get(str(k), w["hit"])
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(rr, (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = rr
                    rect([min(W - 10, max(0, hx + hw - 6)), H - 26, 10, 26], (90, 150, 255, 255))
                    if t == "sweep":
                        rect([max(0, hx - 4), H - 26, 10, 26], (90, 150, 255, 255))
            if tg and tg["frame"] == k:
                x, y = tg["at"]
                d.ellipse([(x - 3) * scale, (y - 3) * scale, (x + 3) * scale, (y + 3) * scale], outline=(0, 255, 255, 255), width=2)
            if spn and spn["frame"] == k:
                x, y = spn["at"]
                d.line([((x - 3) * scale, y * scale), ((x + 3) * scale, y * scale)], fill=(255, 0, 255, 255), width=2)
                d.line([(x * scale, (y - 3) * scale), (x * scale, (y + 3) * scale)], fill=(255, 0, 255, 255), width=2)
            d.line([(ax * scale - 5, ay * scale - 2), (ax * scale + 5, ay * scale - 2)], fill=(255, 255, 0, 255), width=2)
            d.line([(ax * scale, ay * scale - 8), (ax * scale, ay * scale - 1)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def bbox(pts, pad=0):
    pts = [p for p in pts if K.inb(*p)]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def build_meta(infos):
    def rects(tag, a, b, parts, x_min=None):
        rs = {}
        for k in range(a, b + 1):
            inf = infos[tag][k]
            pts = set(inf["hit"])
            for pk in parts:
                pts |= inf[pk]["mask"]
            if x_min is not None:
                pts = {q for q in pts if q[0] >= x_min}
            r = bbox(pts)
            r[3] = H - r[1]                 # reach the floor: a 10x26 player standing there must be hit
            rs[str(k)] = r
        return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}

    idle = infos["idle"][0]
    mb = bbox(idle["mass"])
    hurt = [mb[0] + 6, mb[1] + 4, mb[2] - 12, H - (mb[1] + 4)]
    mx, my = idle["maw"]
    rx, ry = idle["maw_r"]
    weak = [int(mx - rx - 2), int(my - ry - 2), int(2 * rx + 5), int(2 * ry + 5)]

    def pt(q):
        return [int(round(q[0])), int(round(q[1]))]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "weakpoint": weak,
        "attacks": {
            "slam": rects("slam", 5, 6, ["near"], x_min=AX + 20),
            "sweep": rects("sweep", 4, 5, ["near", "far"]),
        },
        "telegraph": {
            "slam": {"frame": 3, "at": [119, 6]},
            "sweep": {"frame": 3, "at": [154, 48]},
            "spew": {"frame": 4, "at": [118, 60]},
        },
        "spawn": {
            "spew": {"frame": 6, "at": pt(add(infos["spew"][6]["maw"], (4, 3))), "dir": [1, 0.15]},
            "slam": {"frame": 5, "at": [infos["slam"][5]["impact_x"], H - 1]},
        },
        "notes": "faces right, anchor = centre of the base. hurtbox = the mass; weakpoint = the maw (optional "
                 "bonus-damage zone). slam: near arm raised overhead (frames 1-3, hold on 3) then brought down, "
                 "active 5-6; spawn.slam = impact point on the floor (shockwave / fx_rot_wave both ways). sweep: both "
                 "arms raised wide (hold on 3) then raked outward along the floor to BOTH sides, active 4-5, hit spans "
                 "the whole base. spew: rears back and swells (frames 1-4), vomits on 6; engine spawns proj_rotglob / "
                 "fx_rot_wave at spawn.spew (the drawn gush is visual only). crawl is a loop drawn in place.",
    }
    return meta


# =========================================================================== main
def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    frames, infos, tags = render_all(only)
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    flats = [K.flatten(imgs, LAYERS) for _, imgs in frames]
    sfx = "_wip" if only else ""
    preview_rows(tags, flats, os.path.join(pv, f"vessel{sfx}.png"))
    c = Image.new("RGBA", (W, H), BG)
    c.alpha_composite(flats[0])
    c.resize((W * 4, H * 4), Image.NEAREST).save(os.path.join(pv, f"vessel_closeup{sfx}.png"))
    if only:
        return
    meta = build_meta(infos)
    hitbox_preview(tags, flats, meta, os.path.join(pv, "vessel_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "vessel_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        print("attack", t, d["active"], d["hit"])
    print("hurtbox", meta["hurtbox"], "weak", meta["weakpoint"], "spawn", meta["spawn"])
    if BUILD:
        asebuild.build("vessel", W, H, LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in frames], tags)


if __name__ == "__main__":
    main()
