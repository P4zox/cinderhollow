"""cm_gargoyle -- a winged gargoyle-bat of the Crimson Manor (48x40, FLYING, anchor = body centre [24, 22]).

Black stone-skinned bat body, leathery dark-crimson wing membranes on stone finger bones, a small horned head,
red eyes, hooked talons.  Faces RIGHT.  Perched it squats on a ledge with its feet on the bottom row (the perch
point is [24, 39] = anchor + (0, 17)).  Built by gen_crimson_enemies.py.

Tags: perch(2 loop: folded, statue-still, stony) wake(4: unfolds and lifts off) fly(6 loop) dive(6: wings tucked,
talons forward, active [2,4]) hurt(2) death(6: cracks and crumbles like stone).
"""
import math

import crimson_kit as CK
import enemy_kit as K
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome,
                       n_capsule, mask_disc)
from gen_enemies3 import n_tube, curve, rot, madd
from PIL import Image

W, H = 48, 40
FLOOR = H - 1
AX, AY = 24, 22
PERCH = (24, 39)
LAYERS = ["FXBack", "WingBack", "Tail", "LegBack", "Body", "LegFront", "Head", "WingFront", "FX"]
FXL = {"FXBack", "FX"}
BODY = [n for n in LAYERS if n not in FXL]

# wing keypoints, local (u = back/outward, v = down), relative to the shoulder:
#   open = spread level behind the body;  fold = wrapped down along the body like a cloak
# Wings are drawn in a 3/4 view (the way classic bat sprites read): the open wing is a fan of four stone finger
# spars spread ABOVE the body; `flap` squashes/flips that fan vertically (1 = wings high, ~0 = edge-on mid-stroke,
# -0.6 = swept below the body), so the flap reads clearly at 1x.  local (u = back from the shoulder, v = down)
WOPEN = {"el": (4.0, -3.6), "wr": (8.0, -7.0), "t1": (7.0, -20.0), "s1": (9.6, -12.0), "t2": (16.0, -18.5),
         "s2": (12.6, -10.6), "t3": (22.0, -11.0), "s3": (14.6, -6.6), "t4": (21.0, -2.0), "s4": (13.0, -1.4),
         "at": (3.0, 1.2)}
# folded like a statue's cloak: wrist hooked up over the shoulder, fingers down its back
WFOLD = {"el": (1.8, -3.6), "wr": (0.8, -7.4), "t1": (2.4, -5.0), "s1": (2.6, -3.0), "t2": (4.2, 6.4),
         "s2": (2.8, 4.2), "t3": (3.0, 10.2), "s3": (1.6, 7.8), "t4": (1.0, 11.2), "s4": (0.2, 7.8),
         "at": (-1.2, 6.0)}


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def polar_lerp(a, b, t):
    r0, r1 = math.hypot(*a), math.hypot(*b)
    a0, a1 = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    r = r0 + (r1 - r0) * t
    an = a0 + da * t
    return (math.cos(an) * r, math.sin(an) * r)


def qarc(p0, mid, p1, n=8):
    c = (2 * mid[0] - (p0[0] + p1[0]) / 2, 2 * mid[1] - (p0[1] + p1[1]) / 2)
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]


NEU = dict(O=(24.0, 22.0), tilt=12.0, flapF=0.3, flapB=0.3, fold=0.0, head=(0.0, 0.0), ha=0.0, jaw=0,
           legs="hang", eye=1, stone=0.0, cracks=0, tailw=0.0, wind=0.0, lines=None, dust=0, scale=1.12)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def wing(L, sh, flap, fold, bias, mat_m, fi, scale=1.0):
    """One wing from shoulder sh (frame coords).  flap: 1 raised .. 0 edge-on .. -0.6 swept down;
    fold 0 open .. 1 folded like a cloak."""
    t = smooth(fold)
    fs = flap if abs(flap) >= 0.34 else (0.34 if flap >= 0 else -0.34)
    pts = {}
    for k in WOPEN:
        u, v = WOPEN[k]
        u = u * (0.82 + 0.18 * abs(fs))
        v = v * fs
        fu, fv = WFOLD[k]
        pts[k] = (sh[0] - (u + (fu - u) * t) * scale, sh[1] + (v + (fv - v) * t) * scale)
    # scallops: each trailing-edge arc dips a fixed fraction of the way from the tip-to-tip chord toward the wrist
    for sk, (ta_, tb_, f) in (("s1", ("t1", "t2", 0.3)), ("s2", ("t2", "t3", 0.3)), ("s3", ("t3", "t4", 0.28)),
                              ("s4", ("t4", "at", 0.2))):
        pts[sk] = lerp(lerp(pts[ta_], pts[tb_], 0.5), pts["wr"], f)
    edge = [sh, pts["el"], pts["wr"], pts["t1"]]
    edge += qarc(pts["t1"], pts["s1"], pts["t2"])[1:]
    edge += qarc(pts["t2"], pts["s2"], pts["t3"])[1:]
    edge += qarc(pts["t3"], pts["s3"], pts["t4"])[1:]
    edge += qarc(pts["t4"], pts["s4"], pts["at"], 6)[1:]
    m = poly_mask(edge)
    L.paint(n_plate(m, 1.6, (0.25 * (1 if flap >= 0 else -1), -0.35 * (1 if flap >= 0 else -1)), 0.7),
            mat_m, bias, ao=0)
    # membrane darkens toward the scalloped trailing edge
    L.decal([q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
             and q not in set(line(sh, pts["wr"]))], (mat_m, max(0, 1 + bias)))
    # stone arm + finger spars (lighter ridges) over the membrane
    L.paint(n_capsule(sh, pts["el"], 1.6, 1.25), "g", bias)
    L.paint(n_capsule(pts["el"], pts["wr"], 1.25, 0.95), "g", bias)
    if abs(fs) > 0.5 or t > 0.5:
        for k in ("t1", "t2", "t3", "t4"):
            seg = line(pts["wr"], pts[k])
            L.decal([q for q in seg[1:-1] if q in m], ("g", 3 + bias))
    w_ = ip(pts["wr"])
    L.fixed({(w_[0] + 1, w_[1] - 1): "g4", (w_[0] + 2, w_[1] - 2): "g5"})       # thumb hook
    return m, pts


def talon_leg(L, hip, foot, bias, grip=False):
    """Short stone leg ending in three hooked talons.  foot = where the talons meet."""
    kn = ik(hip, foot, 3.6, 3.6, (0.8, 0.3))
    L.paint(n_capsule(hip, kn, 1.7, 1.2), "g", bias)
    L.paint(n_capsule(kn, foot, 1.2, 0.9), "g", bias)
    d = sub(foot, kn)
    a = math.degrees(math.atan2(d[1], d[0]))
    pix = {}
    for k, da in enumerate((-30, 30) if not grip else (-20, 10, 40)):
        c = (math.cos(math.radians(a + da)), math.sin(math.radians(a + da)))
        p1 = add(foot, (c[0] * 1.6, c[1] * 1.6))
        p2 = add(p1, (c[0] * 0.8 + (0.9 if grip else 0.6), c[1] * 0.8 + 0.8))
        for q in line(foot, p1):
            pix[q] = "g3" if bias < 0 else "g4"
        pix[ip(p2)] = "w3" if bias >= 0 else "w1"
    L.fixed(pix)
    return kn


def draw(p, fi, sw, phase=1):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    info = {"hit": set()}
    O = p["O"]
    tl = p["tilt"]                      # degrees: + = nose down
    sc = p["scale"]
    F = lambda a, b: add(O, rot((a * sc, b * sc), tl))          # noqa: E731  (a forward, b down)

    # ---- body: sleek keel-chested torso, narrow waist, hips
    hip = F(-4.2, 1.2)
    chest = F(2.4, -0.8)
    Bd = Ls["Body"]
    Bd.paint(n_tube(curve([F(-5.4, 1.6), F(-2.6, 1.0), F(0.8, -0.2), F(3.4, -0.6)], 5),
                    [r * 1.18 * sc for r in (2.3, 2.2, 2.0, 1.8, 1.9, 2.4, 2.9, 3.1, 3.3, 3.2, 3.0, 2.8, 2.6, 2.4,
                                             2.3, 2.2)]), "g", 0)
    tm = set(Bd.px)
    info["torso"] = tm

    # ---- tail: short, pointed, segmented
    Tl = Ls["Tail"]
    t0 = F(-5.2, 1.6)
    t1 = add(t0, rot((-3.0, 2.0 + sw * 0.3), tl + p["tailw"]))
    t2 = add(t1, rot((-2.6, 2.6), tl + p["tailw"] * 1.5))
    tp = curve([t0, t1, t2], 4)
    Tl.paint(n_tube(tp, [1.3 - 1.0 * i / (len(tp) - 1) for i in range(len(tp))]), "g", -1)
    tip = ip(t2)
    Tl.fixed({tip: "g4", (tip[0] - 1, tip[1] + 1): "g3"})

    # ---- legs + talons
    legs = p["legs"]
    if legs == "perch":                    # squatting on the ledge: talons on the bottom row
        fb = (PERCH[0] - 3.0, FLOOR - 0.5)
        ff = (PERCH[0] + 1.5, FLOOR - 0.5)
    elif legs == "strike":                 # thrust forward-down for the dive
        fb, ff = F(3.2, 6.4), F(6.0, 5.6)
    elif legs == "tuck":
        fb, ff = F(-3.4, 4.2), F(-1.0, 4.6)
    else:                                  # trail back under the tail in flight
        fb, ff = F(-8.4, 4.0), F(-6.6, 5.0)
    kb = talon_leg(Ls["LegBack"], F(-3.8, 1.8), fb, -1, grip=legs == "perch")
    kf = talon_leg(Ls["LegFront"], F(-2.8, 2.4), ff, 0, grip=legs == "perch")
    info["feet"] = (fb, ff)
    if legs == "strike":
        info["hit"] |= set(Ls["LegFront"].px) | set(Ls["LegBack"].px)

    # ---- head: small, wedge-snouted, two swept-back horns, pointed ears
    Hl = Ls["Head"]
    hc = add(F(5.4, -2.6), p["head"])
    ha = tl + p["ha"]
    G = lambda a, b: add(hc, rot((a, b), ha))                   # noqa: E731
    Bd.paint(n_capsule(F(2.8, -1.4), G(-1.2, 0.6), 2.0, 1.6), "g", 0)       # neck
    skull = [G(-2.2, -1.4), G(-0.4, -2.3), G(1.6, -1.8), G(3.8, -0.4), G(4.4, 0.6), G(3.4, 1.2), G(1.2, 1.9),
             G(-1.4, 1.8), G(-2.6, 0.4)]
    hm = poly_mask(skull)
    Hl.paint(n_plate(hm, 1.2, (-0.2, -0.3), 1.2), "g", 0)
    info["head"] = hm
    if p["jaw"]:
        Hl.fixed({ip(G(2.4, 1.6)): "b1", ip(G(3.2, 1.5)): "b1", ip(G(3.0, 2.2)): "w3", ip(G(1.8, 2.4)): "g2",
                  ip(G(2.6, 2.6)): "g3"})
    else:
        Hl.decal(line(G(1.4, 1.2), G(3.6, 0.9)), "OUT")
        Hl.fixed({ip(G(2.6, 1.6)): "w3"})
    for k, (b0, b1, b2) in enumerate((((-0.6, -1.6), (-3.0, -3.6), (-6.4, -3.4)),
                                      ((0.6, -1.9), (-1.0, -4.8), (-4.2, -6.6)))):
        hp = curve([G(*b0), G(*b1), G(*b2)], 5)
        Hl.paint(n_tube(hp, [1.05 - 0.7 * i / (len(hp) - 1) for i in range(len(hp))]), "g", -1 if k == 0 else 0, ao=0)
        tipq = ip(G(*b2))
        Hl.fixed({tipq: "g5" if k else "g4"})
    e = ip(G(1.6, -0.6))
    info["eye"] = e
    if p["eye"] > 0:
        CK.eye_glow(FX, e, p["eye"], 1 if -90 < ha < 90 else -1, trail=1 if p["eye"] >= 3 else 0)
    elif p["stone"] > 0:
        Hl.fixed({e: "e0"})

    # ---- wings
    shB = F(-0.6, -1.9)
    shF = F(0.2, -1.4)
    mB = set()
    if p["flapB"] > 0.45 or p["fold"] > 0.5:           # the far wing only shows when raised (or folded)
        mB, _ = wing(Ls["WingBack"], add(shB, (3.2, -1.2)), p["flapB"], p["fold"], -1, "m", fi, 0.8 * sc)
    mF, wp = wing(Ls["WingFront"], shF, p["flapF"], p["fold"], 0, "m", fi, 0.9 * sc)
    info["wings"] = mB | mF
    info["wtip"] = wp["t2"]

    # ---- stone rim + stone state (perched statue: desaturated, lichen-grey highlights)
    for L_ in (Bd, Hl, Ls["WingFront"], Ls["LegFront"], Tl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "g"
                  and not isinstance(e_[3], str)], ("g", 4))
    if p["stone"] > 0:
        for nm in ("WingFront", "WingBack"):
            L_ = Ls[nm]
            L_.decal([q for q, e_ in L_.px.items() if e_[0] == "m" and hash01(q[0] // 2, q[1] // 2, 5) < p["stone"]],
                     ("g", 2 if nm == "WingFront" else 1))
        for L_ in (Bd, Hl, Ls["WingFront"]):
            L_.decal([q for q, e_ in L_.px.items() if hash01(q[0], q[1], 6) < 0.05 * p["stone"]], ("g", 5))
    if p["cracks"]:
        # glowing red fissures (death / hurt): short zig-zags across the body & wing
        for k in range(p["cracks"]):
            a0 = F(-3.0 + k * 2.6, -1.4 + (k % 2) * 2.0)
            pts = [a0]
            for j in range(3):
                pts.append(add(pts[-1], (1.4 + hash01(k, j, 8), (hash01(k, j, 9) - 0.4) * 2.4)))
            seg = polyline([ip(q) for q in pts])
            for L_ in (Bd, Ls["WingFront"], Hl):
                L_.decal([q for q in seg if q in L_.px], "e1" if k % 2 else "e2")

    # ---- fx
    if p["lines"]:
        ang, n = p["lines"]
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        for k in range(n):
            off = (k - (n - 1) / 2) * 3.0
            base = add(O, (-d[1] * off - d[0] * 6, d[0] * off - d[1] * 6))
            seg = line(base, add(base, (-d[0] * (8 + (k % 2) * 4), -d[1] * (8 + (k % 2) * 4))))
            for j, q in enumerate(seg):
                FX.put([q], "g4" if j < 2 else "g3" if j < len(seg) * 0.6 else "g2")
    if p["dust"]:
        for k in range(7):
            x = int(PERCH[0] + (k - 3) * 2.2 + (hash01(k, fi, 1) - 0.5) * 2)
            y = FLOOR - int(hash01(k, fi, 2) * 3) - (k % 2)
            FX.put([(x, y)], ("g3", "g2", "a2")[k % 3])
        for k in range(3):                                   # stone flakes falling off
            FX.put([(int(O[0] - 4 + k * 4), int(O[1] + 8 + hash01(k, fi, 4) * 6))], "g4")
    info["hit"] |= set(Ls["Head"].px) | {q for q in tm if q[0] > O[0]}
    return Ls, info


# =========================================================================== animations
def a_perch():
    """Squatting on the ledge, wings wrapped like a cloak, head forward: a statue (stony, eyes dark)."""
    base = dict(O=(23.0, 30.0), tilt=-42.0, fold=1.0, flapF=0.6, flapB=0.6, ha=48.0, legs="perch",
                stone=0.55, tailw=50.0)
    return [
        (600, P_(**base, eye=0)),
        (600, P_(**base, eye=0, head=(0.0, 0.3))),
    ]


def a_wake():
    return [
        (140, P_(O=(23.0, 29.6), tilt=-46.0, fold=1.0, flapF=0.6, flapB=0.6, head=(0.3, -0.3), ha=40.0, legs="perch",
                 stone=0.3, tailw=40.0, eye=2, dust=1)),
        (120, P_(O=(23.4, 27.0), tilt=-35.0, fold=0.55, flapF=1.0, flapB=0.9, ha=35.0, legs="perch", stone=0.1,
                 tailw=24.0, eye=2, jaw=1, dust=2)),
        (110, P_(O=(23.8, 24.6), tilt=-8.0, fold=0.05, flapF=1.0, flapB=0.95, ha=12.0, legs="tuck", eye=2, jaw=1,
                 tailw=10.0)),
        (110, P_(O=(24.0, 22.4), tilt=8.0, fold=0.0, flapF=-0.55, flapB=-0.45, ha=0.0, legs="hang", eye=1)),
    ]


FLAP = [1.0, 0.6, -0.4, -0.7, -0.45, 0.4]


def a_fly():
    fr = []
    for i, f in enumerate(FLAP):
        bob = (1.2, 0.4, -0.6, -1.0, -0.2, 0.8)[i]
        fr.append((80, P_(O=(24.0, 22.0 + bob), tilt=10.0 - f * 3.0, flapF=f, flapB=f * 0.9,
                          ha=-4.0, tailw=f * 8.0)))
    return fr


def a_dive():
    """Rise with the wings high (anticipation), tuck, then a steep talons-first dive (active 2-4), wings snap open."""
    return [
        (140, P_(O=(25.0, 21.4), tilt=-6.0, flapF=0.95, flapB=0.9, ha=6.0, eye=2, jaw=1, legs="tuck")),
        (100, P_(O=(24.0, 21.4), tilt=26.0, fold=0.75, flapF=0.8, flapB=0.7, ha=10.0, eye=3, jaw=1, legs="tuck")),
        (70, P_(O=(24.0, 22.0), tilt=38.0, fold=0.9, flapF=0.7, flapB=0.6, ha=-18.0, eye=3, jaw=1, legs="strike",
                lines=(38, 3))),
        (70, P_(O=(24.0, 22.4), tilt=40.0, fold=0.95, flapF=0.7, flapB=0.6, ha=-20.0, eye=3, jaw=1, legs="strike",
                lines=(40, 4))),
        (80, P_(O=(24.0, 22.4), tilt=36.0, fold=0.85, flapF=0.7, flapB=0.6, ha=-16.0, eye=3, jaw=1, legs="strike",
                lines=(36, 2))),
        (130, P_(O=(24.0, 21.4), tilt=4.0, fold=0.1, flapF=-0.6, flapB=-0.5, ha=-2.0, eye=2, legs="hang")),
    ]


def a_hurt():
    return [
        (90, P_(O=(25.0, 21.6), tilt=-18.0, flapF=0.9, flapB=0.8, ha=-26.0, eye=3, jaw=1, cracks=1, legs="tuck")),
        (130, P_(O=(23.6, 21.8), tilt=4.0, flapF=-0.3, flapB=-0.2, ha=-6.0, eye=2)),
    ]


def shatter(t, seed=0):
    """Break the body layers into 3x3 stone chunks that fall and tumble; chunks turn to grit as they go."""
    def f(imgs, ph):
        out = dict(imgs)
        grit = {}
        for n in BODY:
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
                    bx, by = (x + int(hash01(y // 3, 0, seed) * 3)) // 3, y // 3
                    r1, r2, r3 = hash01(bx, by, seed + 1), hash01(bx, by, seed + 2), hash01(bx, by, seed + 3)
                    if r3 < t * 0.55:                          # this chunk has already crumbled to grit
                        if hash01(x, y, seed + 4) < 0.12:
                            gx = int(x + (x - AX) * 0.2 * t + (r1 - 0.5) * 6 * t)
                            gy = int(y + (t * t) * (18 + 16 * r2) + 2)
                            if 0 <= gx < W and 0 <= gy < H:
                                grit[(gx, min(FLOOR, gy))] = "g3" if hash01(x, y, 5) < 0.5 else "a1"
                        continue
                    dx = (bx * 3 - AX) * 0.18 * t + (r1 - 0.5) * 4 * t
                    dy = (t * t) * (14 + 16 * r2)
                    nx, ny = int(round(x + dx)), int(round(y + dy))
                    if 0 <= nx < W and 0 <= ny <= FLOOR:
                        dst[nx, ny] = c
            out[n] = new
        fx = imgs["FX"].copy()
        fp = fx.load()
        for (x, y), c in grit.items():
            if fp[x, y][3] == 0:
                fp[x, y] = K.RGBA[c]
        out["FX"] = fx
        return out
    return f


def a_death():
    limp = dict(O=(24.0, 23.0), tilt=30.0, flapF=-0.6, flapB=-0.5, ha=30.0, legs="hang", jaw=1)
    return [
        (100, P_(O=(25.0, 21.6), tilt=-22.0, flapF=0.9, flapB=0.8, ha=-30.0, eye=3, jaw=1, cracks=2, legs="tuck")),
        (140, P_(**limp, eye=1, cracks=3)),
        (120, P_(**dict(limp, O=(24.0, 24.0), tilt=40.0), eye=0, cracks=4, stone=0.6, post=shatter(0.12, 5))),
        (110, P_(**dict(limp, O=(24.0, 24.0), tilt=40.0), eye=0, cracks=4, stone=0.8, post=shatter(0.4, 5))),
        (120, P_(**dict(limp, O=(24.0, 24.0), tilt=40.0), eye=0, cracks=4, stone=0.9, post=shatter(0.7, 5))),
        (400, P_(**dict(limp, O=(24.0, 24.0), tilt=40.0), eye=0, cracks=4, stone=1.0, post=shatter(1.0, 5))),
    ]


TAGDEFS = [("perch", a_perch), ("wake", a_wake), ("fly", a_fly), ("dive", a_dive), ("hurt", a_hurt),
           ("death", a_death)]
COUNTS = dict(perch=2, wake=4, fly=6, dive=6, hurt=2, death=6)
LOOPS = ("perch", "fly")
RUN_KW = dict(sway_key="O")


def setup():
    K.setup(W, H)


draw_fn = draw


def meta(infos, tags, frames):
    fl = infos["fly"][0]
    bb = CK.bbox(fl["torso"] | fl["head"])
    hurt = [bb[0], bb[1] - 1, bb[2], bb[3] + 2]
    dive = CK.attack_rect(infos, "dive", 2, 4, floor=False)
    pbb = CK.bbox(infos["perch"][0]["torso"] | infos["perch"][0]["head"] | infos["perch"][0]["wings"])
    perch_hb = [pbb[0] + 1, pbb[1] + 1, pbb[2] - 2, H - (pbb[1] + 1)]
    return {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, AY],
        "flying": True,
        "hurtbox": hurt,
        "perch": {"feet": list(PERCH), "offset_from_anchor": [PERCH[0] - AX, PERCH[1] - AY],
                  "hurtbox": perch_hb},
        "attacks": {"dive": dive},
        "telegraph": {"dive": {"frame": 0, "at": CK.pt(infos["dive"][0]["eye"])}},
        "notes": "FLYING: anchor = body centre [24,22] (the engine positions the body centre). perch.hurtbox is the body box while perched (use it for perch/wake f0-1). perch: feet (talons) "
                 "on the bottom row at [24,39] = anchor + (0,17): to sit it on a ledge whose top surface is at y, "
                 "put the anchor at y-17 (feet are the frame's bottom row). wake: f0 statue eyes light, f1 unfolds "
                 "(stone dust falls), f2 wings up, f3 lifts off into the fly pose (body centre back at the anchor). "
                 "dive: f0 wings raised (telegraph: eye flare), f1 tucks, f2-4 steep talons-first dive drawn in "
                 "place (the engine moves it along the dive), f5 wings snap open. The dive hit is not extended to "
                 "the floor (it is a flyer): it covers the talons, head and front of the body. death: glowing "
                 "cracks, then it shatters into stone chunks that fall to the bottom of the frame.",
    }
