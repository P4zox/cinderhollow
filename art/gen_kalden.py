#!/usr/bin/env python3
"""Boss generator -- "Ser Kalden the Oathless" (ART_SPEC2 section D).

    python3 art/gen_kalden.py              full build: kalden + kalden_p2 + fx_kalden_slash + fx_rot_wave (+meta)
    python3 art/gen_kalden.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_kalden.py --only combo,thrust --preview   quick iteration on some tags

Outputs
    art/kalden.aseprite, assets/kalden.png/.json          phase 1 (battered white-and-teal plate, blue cloak)
    art/kalden_p2.aseprite, assets/kalden_p2.png/.json    phase 2 (same frames/tags: rot growths, swollen sword arm)
    assets/kalden_meta.json                               meta shared by both sheets
    art/fx_kalden_slash.aseprite, assets/fx_kalden_slash.* 80x48, 4 frames (tag kalden_slash), teal-gold arc
    art/fx_rot_wave.aseprite, assets/fx_rot_wave.*         32x24, 4 frames loop (tag rot_wave), pivot bottom
    art/previews/kalden.png, kalden_p2.png (3x, one row per tag), kalden_hitbox.png, kalden_closeup.png,
    fx_kalden.png

Method: enemy_kit.py (normal-field shading, sel-out outlines, Rig) -- same family as grave_knight, scaled
up to a ~52px knight in a 96x72 frame.  Faces RIGHT, feet on the bottom row, anchor x = 40.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, leg, arm, blade_px, swept,
                       thrust_lines, dirv)

W, H = 96, 72
K.setup(W, H)
FLOOR = H - 1
AX = 40
BUILD = "--preview" not in sys.argv

# ---------------------------------------------------------------- palette additions (runtime only)
EXTRA = {
    # battered white plate (cool shadows)
    "S0": "#15161f", "S1": "#2b2e3d", "S2": "#4c5266", "S3": "#7a8497", "S4": "#aeb8c4", "S5": "#e6ecea",
    # teal enamel / tabard
    "N0": "#0a181c", "N1": "#123136", "N2": "#1b4b4e", "N3": "#2a716c", "N4": "#46a08f", "N5": "#86d2b8",
    # tattered blue cloak
    "U0": "#0c0e1c", "U1": "#161b35", "U2": "#212c55", "U3": "#304376", "U4": "#48609a", "U5": "#6f88b8",
    # black blade
    "X0": "#07070c", "X1": "#111119", "X2": "#1d1d29", "X3": "#303044", "X4": "#505068", "X5": "#9c9cc0",
}
for k, v in EXTRA.items():
    K.HEX[k] = v
    K.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k[0], []).append(k)
K.SHINY["S"] = 0.93
K.SHINY["X"] = 0.9
K.SMEAR["kalden"] = ["Y3", "Q2", "Q1", "N2"]        # white-gold edge -> teal
K.SMEAR["kalden2"] = ["O5", "O3", "V3", "V2"]       # phase 2: rot creeping into the arc
K.SMEAR["kthrust"] = ["Y3", "Q4", "Q3", "Q2"]
RGBA = K.RGBA

LAYERS = ["FXBack", "RotBack", "Cloak", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Plume", "Head", "Weapon",
          "FrontArm", "Rot", "Spores", "FX"]
FXL = {"FXBack", "Spores", "FX"}

KBLADE = dict(pommel=-7.0, grip_end=0.8, grip="L1", grip_w=0.8, pommel_c="G3", guard=(0.6, 2.4, 5.0),
              guard_c="G2", guard_hi="G4", b0=2.4, end=31.0, w_edge=1.8, w_spine=1.5, taper=0.2, fuller="N3",
              edge_hi="X5", edge="X3", spine="X2")

NEU = dict(P=(39.5, 51.5), C=(40.8, 40.4), Hd=(42.4, 30.2), hup=(0.1, -1), fb=(32.0, 71), ff=(47.0, 71),
           kb=None, kf=None, hf=(49.0, 49.0), wang=-58, wl="Weapon", hb=None, onehand=False, sword="hand",
           smear=None, flat=None, thrust=None, eye=1, wind=0.0, lift=0.0, impact=0, dust=0, burst=0.0,
           dissolve=0.0, shake=0, glint=None, rot=0.0, piv=(0, 0), fwd=0.0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


PTS = ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb")


def up(p, dy, dx=0.0):
    """Shift every joint of a pose (airborne frames)."""
    q = dict(p)
    for k in PTS:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] - dy)
    return q


# =========================================================================== small helpers
def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def rag_hem(x0, x1, y, fi, seed, depth=2.5, sway=0.0):
    pts = []
    n = max(2, int((x1 - x0) / 1.6))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.3 + hash01(i, fi // 2, seed)) if i % 2 == 0 else depth * 0.15
        pts.append((x + sway * (0.4 + 0.6 * t), y + d))
    return pts


def pustule(L, c, r=0.8, hot=False):
    """Glowing rot-orange boil (fixed colours so it reads as light, outlined)."""
    m = mask_disc(c, r + 0.4)
    L.fill(m, "O2")
    L.fill(mask_disc(c, max(0.6, r - 0.3)), "O3")
    L.decal([ip(c)], "O5" if hot else "O4")
    return m


def rot_blob(R, L, c, r, seed, n_pus=2, hot=False, mat="V"):
    """Cluster of rot growth: lumpy green mass + a couple of glowing boils."""
    R.dome(L, c, r, r * 0.85, mat, bias=0, ao=1)
    for k in range(2):
        a = hash01(seed, k, 3) * 6.28
        q = add(c, (math.cos(a) * r * 0.7, math.sin(a) * r * 0.6))
        R.dome(L, q, r * 0.55, r * 0.5, mat, bias=0, ao=1)
    for k in range(n_pus):
        a = hash01(seed, k, 5) * 6.28
        q = R.T(add(c, (math.cos(a) * r * 0.45, math.sin(a) * r * 0.45 - 0.3)))
        pustule(L, q, 0.55 + 0.3 * hash01(seed, k, 7), hot)


# =========================================================================== the knight
def draw(p, fi, sw, phase):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX = FXLayer("FX")
    SP = FXLayer("Spores")
    FXB = FXLayer("FXBack")
    Ls["FX"], Ls["Spores"], Ls["FXBack"] = FX, SP, FXB
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(2.0, -ln + 2.2), F(-3.4, -ln + 2.4)
    hB, hF = F(-2.8, 1.0), F(2.8, 1.0)
    info = {"hit": set(), "smear": set()}
    rot_on = phase == 2 or p["burst"] > 0
    burst = p["burst"]
    lift = p["lift"]

    # ---------------- weapon
    if p["sword"] == "hand":
        grip, wang = p["hf"], p["wang"]
    else:
        grip, wang = p["sword"]
    pix, blade, tip = blade_px(ID if p["sword"] != "hand" else R, grip, wang, KBLADE)
    g0 = R.T(grip) if p["sword"] == "hand" else grip
    a0 = R.A(wang) if p["sword"] == "hand" else wang
    ca, sa = dirv(a0)
    for q in list(pix):
        if pix[q] == KBLADE["fuller"]:                       # teal-gold filigree along the fuller
            u = (q[0] + .5 - g0[0]) * ca + (q[1] + .5 - g0[1]) * sa
            k = int(u) % 6
            if k == 0:
                pix[q] = "G4"
            elif k == 3:
                pix[q] = "N4"
            else:
                pix[q] = "N2"
            if u > KBLADE["end"] - 5:
                pix[q] = "X3"
        if phase == 2 and pix[q] == "X5" and hash01(q[0], q[1], 17) < 0.25:
            pix[q] = "V5"                                     # rot bloom on the edge
    pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
    blade = {q for q in blade if q[1] <= FLOOR}
    Ls[p["wl"]].fixed(pix)
    info["hit"] |= blade
    info["tip"] = tip
    info["grip"] = g0
    hand2 = (g0[0] - ca * 3.9, g0[1] - sa * 3.9) if p["sword"] == "hand" and not p["onehand"] else None

    # ---------------- cloak: tattered blue, long, from both shoulders
    Cl = Ls["Cloak"]
    sx = sw * 1.0 - p["wind"]
    ctop = F(-3.8, -ln - 0.6)
    hem_y = min(FLOOR - 2.0, P[1] + 17.0 + max(0.0, lift) * 0.5) + min(0.0, lift) * 1.3
    fly = abs(lift) * 0.55
    back = P[0] - 15.5 + sx * 1.3 - fly * 1.2
    fx0 = P[0] - 3.0 + sx * 0.4
    slant = 0.0
    pts = [add(ctop, (3.2, -1.2)), F(0.2, -ln + 2.2), F(-2.6, 0.5), (P[0] - 3.0 + sx * 0.3, hem_y - 2.0)] + \
        [(x, y - slant * (fx0 - x) / max(1.0, fx0 - back)) for x, y in rag_hem(back, fx0, hem_y, fi, 41, 3.8, sway=0)] + \
        [(back - 0.8 - fly * 0.3, P[1] - 1.0 - fly * 0.6), (P[0] - 11.0 + sx * 0.6, P[1] - 10.0), add(ctop, (-4.8, 2.6))]
    if p["dissolve"] < 0.99 or True:
        cm = R.mask(pts)
        Cl.paint(n_plate(cm, 2.4, (0.2, 0.05), 1.0,
                         fold=lambda x, y: (0.7 * math.sin((x - P[0] - sw * 0.4) * 0.75 + y * 0.08), 0)),
                 "U", bias=-1, ao=0)
        # tears & wear: a couple of holes near the hem, dark stripes
        for q in cm:
            if q[1] > hem_y - 7 and hash01(q[0] // 2, q[1] // 2, 43) < 0.05:
                Cl.decal([q], ("U", 0))
        if rot_on:
            stain = [q for q in cm if q[1] > hem_y - 6 - 3 * hash01(q[0], 0, 44)]
            Cl.decal(stain, ("V", 2), only_on=("U",))
            Cl.decal([q for q in stain if hash01(q[0], q[1], 45) < 0.18], ("V", 3))
        # inner lining shows where the cloak parts from the back
        Cl.decal([q for q in cm if abs(q[0] - (P[0] - 4.0 + sx * 0.3)) < 0.8 and q[1] > P[1]], ("N", 1))

    # ---------------- plume: long teal horsehair from the helm crest
    G = basis(Hd, p["hup"])
    Pl = Ls["Plume"]
    root = G(-0.6, -6.2)
    ps = sw * 1.2 - p["wind"] * 0.8
    pl_pts = bezier(root, add(root, (-4.5, -2.8 - lift * 0.1)), add(root, (-10.0 + ps, 0.5 + lift * 0.2)),
                    add(root, (-15.0 + ps * 1.6, 6.5 - lift * 0.6)), n=12)
    tube(R, Pl, pl_pts, 2.4, 0.7, "N", bias=0)
    for k in range(3):   # strands
        sp = [add(q, (0, -0.8 + k * 0.9)) for q in pl_pts[2:11 - k]]
        Pl.decal(polyline([R.T(q) for q in sp]), ("N", 2 if k != 1 else 4))

    # ---------------- back arm
    hbk = p["hb"] or hand2 or F(-3.8, -2.0)
    arm(R, Ls["BackArm"], shB, hbk, 7.8, 8.0, 2.5, 2.2, "S", bias=-1, fist="I", fist_r=2.0, pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (0.2, -0.8)), 3.6, 3.2, "S", bias=-1)

    # ---------------- legs: white plate, dark iron sabatons, gold poleyn studs
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(R, Ls[nm], hip, ft, 10.2, 10.2, 3.2, 2.6, "S", bias=bias, flen=4.6, heel=2.2, boot_h=3.4,
                knee=kn, boot=None)
        R.dome(Ls[nm], add(k, (0.7, 0.0)), 2.8, 2.5, "S", bias=bias)
        R.decal(Ls[nm], [add(k, (1.0, 0.2))], ("G", 4 + bias))
        R.dline(Ls[nm], add(k, (-1.6, 2.5)), add(k, (2.0, 2.3)), ("N", 3 + bias))
        info["knee_" + nm] = k

    # ---------------- torso
    Bd = Ls["Body"]
    faulds = [F(-6.4, -2.0), F(5.8, -2.0), F(6.6, 4.8), F(-7.0, 4.8)]
    R.plate(Bd, faulds, "S", bevel=1.6, tilt=(0.0, 0.2), bias=-1)
    for k in range(2):
        R.dline(Bd, F(-6.6, 0.5 + k * 2.2), F(6.2, 0.5 + k * 2.2), ("S", 1))
    torso = [F(-6.4, -1.0), F(-7.2, -ln + 3.4), F(-5.0, -ln - 1.8), F(3.2, -ln - 2.4), F(6.8, -ln + 1.0),
             F(7.2, -ln + 6.4), F(5.6, -1.0)]
    tm = R.plate(Bd, torso, "S", bevel=3.2, tilt=(-0.35, -0.15), strength=1.35)
    info["torso"] = tm
    R.dline(Bd, F(2.0, -ln - 2.0), F(2.6, -2.2), ("S", 5))            # keel ridge
    R.dline(Bd, F(2.8, -ln - 1.8), F(3.4, -2.2), ("S", 2))
    R.dline(Bd, F(-4.8, -ln - 1.5), F(3.2, -ln - 2.1), ("G", 3))       # neck trim
    R.dline(Bd, F(-6.0, -1.2), F(5.6, -1.2), ("G", 2))                 # waist trim
    # battle damage: dents & scratches
    for (a, b) in ((-2.6, -ln + 5.0), (4.6, -ln + 8.4)):
        R.decal(Bd, [F(a, b), F(a + 0.8, b + 0.6)], ("S", 1))
    R.dline(Bd, F(-3.6, -ln + 2.0), F(-1.0, -ln + 6.0), ("S", 2))
    # tabard: teal cloth, gold border, the oath-sigil scratched out
    tx = F(2.2, -2.2)
    if p["dissolve"] < 1.1:
        tsw = -sw * 0.6 + p["wind"] * 0.3
        tb = [add(tx, (-3.0, 0)), add(tx, (3.2, 0)), add(tx, (3.8 - tsw * 0.5, 10.5 - lift * 0.3)),
              add(tx, (1.8 - tsw, 13.6 - lift * 0.4)), add(tx, (0.4 - tsw, 11.6)), add(tx, (-1.2 - tsw, 14.0 - lift * 0.4)),
              add(tx, (-3.4 - tsw * 0.5, 10.5))]
        tbm = R.plate(Bd, tb, "N", bevel=1.4, tilt=(-0.2, 0.0), fold=lambda x, y: (0.45 * math.sin(x * 1.3), 0))
        edge = [q for q in tbm if any((q[0] + a, q[1] + b) not in tbm for a, b in ((1, 0), (-1, 0)))]
        Bd.decal(edge, ("G", 2))
        sig = R.T(add(tx, (0.2, 5.0)))
        ring = [q for q in mask_disc(sig, 2.0) if q not in mask_disc(sig, 1.0)]
        Bd.decal(ring, ("G", 3))
        Bd.decal([ip(sig)], ("G", 4))
        Bd.decal(line(add(sig, (-2.4, -2.2)), add(sig, (2.2, 2.4))), "OUT")      # the broken oath
        if rot_on:
            Bd.decal([q for q in tbm if q[1] > max(t[1] for t in tbm) - 3 + 2 * hash01(q[0], 0, 47)], ("V", 2))
    # gorget
    R.cap(Bd, F(0.4, -ln - 1.0), add(Hd, (-0.6, 4.6)), 2.8, 2.6, "S", bias=-1)

    # ---------------- head: rounded armet, visor slit, broken gold circlet
    Hl = Ls["Head"]
    helm = [G(-4.6, 4.4), G(-5.2, -1.4), G(-4.0, -5.0), G(-0.6, -6.6), G(2.8, -5.8), G(4.9, -3.2), G(5.6, 0.6),
            G(5.4, 3.0), G(2.2, 5.2), G(-3.0, 5.0)]
    hm = R.plate(Hl, helm, "S", bevel=2.2, tilt=(-0.3, -0.2), strength=1.3)
    info["head"] = hm
    R.dline(Hl, G(-0.4, -6.4), G(4.2, -3.8), ("S", 5))                  # comb ridge
    R.dline(Hl, G(1.0, -0.6), G(5.6, -0.8), "OUT")                     # visor slit
    R.dline(Hl, G(2.6, 0.4), G(5.4, 0.2), ("S", 2))
    for k in range(3):                                                  # breaths
        R.decal(Hl, [G(3.2 + k * 0.9, 2.2)], "OUT")
    circ = R.dline(Hl, G(-5.0, -2.4), G(4.4, -3.2), ("G", 3))            # circlet
    for k, q in enumerate(circ):
        if k % 3 == 0:
            Hl.decal([(q[0], q[1] - 1)], ("G", 4))
    R.decal(Hl, [G(-2.0, -2.9)], "OUT")                                 # the break in the circlet
    R.decal(Hl, [G(-4.0, 2.0), G(-3.2, 2.8)], ("N", 3))                 # teal cheek rivets
    # eye
    e1, e2 = R.pt(G(3.4, -0.7)), R.pt(G(4.6, -0.7))
    if phase == 2 or burst >= 2:
        FX.put([e1], "O4"); FX.put([e2], "O5" if p["eye"] == 2 else "O4")
    elif p["eye"]:
        FX.put([e2], "Q3" if p["eye"] == 1 else "Q4")
    if p["eye"] == 2:
        e = e2
        col = ("O5", "O4") if (phase == 2 or burst >= 2) else ("Y3", "Q3")
        FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1]), (e[0] - 1, e[1])], col[1])
        FX.put([(e[0], e[1] - 1), (e[0], e[1] + 1)], col[1])
        FX.put([e], col[0])

    # ---------------- near arm + great pauldron
    Fa = Ls["FrontArm"]
    swollen = phase == 2
    hfr = p["hf"] if p["sword"] == "hand" or p["hf"] else F(4.0, -2.0)
    if not swollen:
        el = arm(R, Fa, shF, hfr, 7.8, 8.0, 2.8, 2.3, "S", bias=0, fist="I", fist_r=2.1, pref=(-1, 0.7))
        R.cap(Fa, lerp(el, hfr, 0.45), hfr, 2.4, 2.1, "I", 0, ao=0)                 # gauntlet cuff
    else:
        # the sword arm is bloated with rot: the plate has burst, a lumpy green limb with boils
        el = ik(shF, hfr, 7.8, 8.0, (-1, 0.7))
        R.cap(Fa, shF, el, 4.4, 4.0, "V", 0)
        R.cap(Fa, el, hfr, 3.9, 2.6, "V", 0)
        R.dome(Fa, lerp(shF, el, 0.55), 4.4, 3.9, "V", 0)
        R.dome(Fa, lerp(el, hfr, 0.4), 3.8, 3.3, "V", 0)
        R.dome(Fa, add(lerp(shF, el, 0.8), (1.2, 1.4)), 2.4, 2.2, "V", 0)
        R.dome(Fa, add(el, (0.2, 0.4)), 2.2, 2.0, "S", bias=-1)                         # a torn couter
        R.cap(Fa, lerp(el, hfr, 0.72), hfr, 2.4, 2.1, "I", 0, ao=1)                    # gauntlet still holds
        R.dome(Fa, hfr, 2.1, 2.1, "I", 0)
        vein = polyline([R.T(shF), R.T(lerp(shF, el, 0.5)), R.T(add(el, (0.8, 0.6))), R.T(lerp(el, hfr, 0.6))])
        Fa.decal([q for i, q in enumerate(vein) if i % 4 < 2], ("V", 5))
        for k, (q, r) in enumerate(((lerp(shF, el, 0.7), 0.8), (lerp(el, hfr, 0.3), 0.7), (lerp(shF, el, 0.3), 0.55))):
            pustule(Fa, R.T(add(q, (0.6, -0.4))), r, hot=burst >= 2)
    pm = set()
    lames = ((0.9, 3.6, 4.2, 2.5), (0.5, 1.3, 4.9, 3.0), (0.0, -1.3, 5.4, 3.8))
    for k, (dx, dy, rx, ry) in enumerate(lames if not swollen else lames[:2]):
        c = add(shF, (dx, dy))
        m = R.dome(Fa, c, rx, ry, "S", tilt=(0.05, 0.1))
        rim = [q for q in m if (q[0], q[1] + 1) not in m]
        Fa.decal(rim, ("N", 3) if k < 2 else ("G", 3))
        pm |= m
    info["pauldron"] = pm
    if not swollen:
        R.decal(Fa, [add(shF, (-1.6, -3.8)), add(shF, (-0.6, -4.4))], ("S", 5))
        R.dline(Fa, add(shF, (-3.6, -2.2)), add(shF, (1.8, -4.6)), ("S", 5))  # haute-piece ridge

    # ---------------- rot growths (phase 2) on body/helm/pauldron
    if phase == 2:
        # a fungal crown bursting out where the top of the pauldron was
        sc = add(shF, (-2.2, -1.0))
        R.dome(Fa, sc, 4.0, 3.0, "V", 0)
        R.dome(Fa, add(sc, (-3.0, -0.8)), 2.6, 2.2, "V", 0)
        for k, (dx, dy, l, bend) in enumerate(((-3.8, -1.4, 5.0, -3.4), (-1.6, -2.4, 4.4, -2.6), (0.4, -2.4, 3.0, -1.2))):
            b0 = add(sc, (dx, dy))
            tube(R, Fa, [b0, add(b0, (bend * 0.5, -l * 0.6)), add(b0, (bend, -l))], 1.2, 0.5, "V", 0)
        pustule(Fa, R.T(add(sc, (1.0, -0.6))), 0.9, hot=burst >= 2)
        pustule(Fa, R.T(add(sc, (-2.6, -1.0))), 0.6, hot=burst >= 2)
        # growth splitting the back of the cuirass
        R.dome(Bd, F(-5.6, -ln + 6.0), 2.8, 3.4, "V", 0)
        R.dome(Bd, F(-6.4, -ln + 9.4), 1.8, 2.0, "V", 0)
        pustule(Bd, R.T(F(-5.2, -ln + 5.4)), 0.6)
        # helm: rot swelling out of the back, a glowing crack
        R.dome(Hl, G(-4.4, -2.0), 2.4, 2.8, "V", 0)
        R.dome(Hl, G(-5.0, 1.4), 1.6, 1.8, "V", 0)
        Hl.decal(line(R.T(G(-1.2, -6.2)), R.T(G(1.6, -1.8))), "OUT")
        Hl.decal(line(R.T(G(-0.8, -5.6)), R.T(G(1.3, -2.6))), "O3")
        # rot patina creeping up the plate
        for L_ in (Ls["FrontLeg"], Ls["BackLeg"]):
            L_.decal([q for q, e in L_.px.items() if e[0] == "S" and hash01(q[0] // 2, q[1] // 2, 48) < 0.06],
                     ("V", 2))
    # ---------------- rot burst (the eruption)
    if burst > 0:
        draw_burst(p, fi, R, F, Ls, FX, info, phase)
    if phase == 2:
        spores(SP, fi, P, C, shF, el)

    # ---------------- fx: smears
    pal = "kalden" if phase == 1 else "kalden2"
    if p["smear"]:
        sm = p["smear"]
        hot = swept(FX, R.T(sm["g0"]), sm["a0"], g0, a0, sm.get("u0", 14), KBLADE["end"] + 0.5, hw=1.3,
                    mid=sm.get("mid"), start=sm.get("start", 0.0), pal=pal, exclude=blade,
                    taper=sm.get("taper", 0.72), clip_y=FLOOR)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["flat"]:
        hot = flat_arc(FX, p["flat"], pal, exclude=blade, back=FXB)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["thrust"]:
        th = p["thrust"]
        pts = thrust_lines(FX, g0, a0, th.get("u0", -26), th.get("u1", 4), th.get("offs", (-3, -1, 2, 4)),
                           pal="kthrust" if phase == 1 else "kalden2", flash=th.get("flash"))
        info["hit"] |= {q for q in pts if q[0] > AX}
    if p["impact"]:
        impact(FX, info, tip, p["impact"], phase)
    if p["dust"]:
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(6):
                x = int(fx_[0] + fx_[1] * (1 + k * 1.3) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (2 + k * 0.5) * (1 if p["dust"] == 1 else 0.6))
                FX.put([(x, y)], ("A3", "A2", "I3")[k % 3] if p["dust"] == 1 else "A2")
    if p["glint"]:
        star(FX, p["glint"], "Y3", "Q3" if phase == 1 else "O4")
    return Ls, info


def star(FX, c, core, arm_):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], core)
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0)):
        FX.put([(x + d[0], y + d[1])], arm_)


def flat_arc(FX, spec, pal, exclude=(), back=None):
    """Horizontal cleave seen side-on: a flattened crescent in front of the body.
    spec: c, rx, ry, th0, th1 (deg, 0 = front), w (thickness in px), fade."""
    cols = K.SMEAR[pal]
    cx, cy = spec["c"]
    rx, ry, th0, th1, wd = spec["rx"], spec["ry"], spec["th0"], spec["th1"], spec.get("w", 5.0)
    fade = spec.get("fade", 0.0)
    hot = set()
    for y in range(int(cy - ry - wd - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            ux, uy = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = math.hypot(ux, uy)
            if d == 0:
                continue
            th = math.degrees(math.atan2(uy, ux))
            # angular position along the sweep (0 = oldest, 1 = newest/front)
            t = (th - th0) / (th1 - th0) if th1 != th0 else 0
            if not (0 <= t <= 1):
                continue
            thick = wd * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - fade * 0.6)
            grad = math.hypot(ux / rx, uy / ry) / d
            dd = (1 - d) / max(grad, 1e-6)           # true inward pixel distance from the outer rim
            if dd < -0.5 or dd > thick:
                continue
            if (x, y) in exclude or not K.inb(x, y) or y > FLOOR:
                continue
            age = 1 - t
            if fade and hash01(x, y, 77) < fade * 0.7:
                continue
            if age > 0.7 and int(dd) % 2 == 1:
                continue
            if dd < 1.2 and age < 0.5:
                c = cols[0]
            elif dd < thick * 0.45:
                c = cols[1] if age < 0.6 else cols[2]
            else:
                c = cols[2] if age < 0.5 else cols[3]
            (back if (back is not None and uy < -0.35 and ux < 0.55) else FX).put([(x, y)], c)
            if age < 0.8 and not fade:
                hot.add((x, y))
    return hot


def impact(FX, info, tip, stage, phase):
    ix = int(round(min(tip[0], W - 6)))
    pts = set()
    hotc = ("Y3", "Q4", "Q3") if phase == 1 else ("O5", "O4", "V5")
    for k in range(18):
        a = -math.pi * (0.06 + 0.88 * hash01(k, 7, 50))
        r = (3 + 15 * hash01(k, 8, 51)) * (0.6 if stage == 1 else 1.0)
        q = ip((ix + math.cos(a) * r * 1.3, FLOOR - 1 + math.sin(a) * r * (0.9 if stage == 1 else 0.7)
                + (0 if stage == 1 else 2.5 * (r / 10) ** 2)))
        c = (hotc[0], hotc[1], "I4")[k % 3] if stage == 1 else ("I4", "A3", "A2")[k % 3]
        FX.put([q], c)
        if k % 3 == 0 and stage == 1:
            FX.put([(q[0] + 1, q[1])], c)
        pts.add(q)
    for dx in range(-14, 15):
        if abs(dx) < (12 if stage == 1 else 15) and hash01(dx, 3, 52) < 0.75:
            FX.put([(ix + dx, FLOOR)], hotc[0] if abs(dx) < 3 else hotc[2] if stage == 1 else "I2")
    if stage == 1:
        for ang in range(-165, -10, 22):
            FX.put(line((ix, FLOOR - 1), (ix + math.cos(math.radians(ang)) * 9, FLOOR - 1 + math.sin(math.radians(ang)) * 7)),
                   hotc[0] if ang % 44 == 0 else hotc[2])
    info["hit"] |= pts
    info["impact_x"] = ix


def spores(SP, fi, P, C, shF, el):
    """Phase 2: rot motes drifting up off the body, drips from the swollen arm."""
    for k in range(7):
        ph = (fi * 0.37 + hash01(k, 1, 80)) % 1.0
        x = C[0] - 10 + hash01(k, 2, 81) * 20 + math.sin(ph * 6 + k) * 2
        y = C[1] + 6 - ph * 26
        if K.inb(int(x), int(y)):
            SP.put([ip((x, y))], ("O4", "V5", "O3", "V4")[k % 4] if ph < 0.7 else "V3")
    d = (fi * 3) % 9
    SP.put([ip(add(el, (0.5, 3 + d)))], "V4")
    if d > 2:
        SP.put([ip(add(el, (0.5, 1 + d)))], "V3")


def draw_burst(p, fi, R, F, Ls, FX, info, phase):
    """Rot erupting from the body. burst stage: 1-3 swelling, 4 erupt, 5 full, 6-8 retracting."""
    b = p["burst"]
    Rb, Rf = Ls["RotBack"], Ls["Rot"]
    P, C = p["P"], p["C"]
    O = lerp(P, C, 0.5)
    hit = set()
    if b < 4:
        # swelling: green growths bulge out of the armour seams, boils brighten, light leaks out
        n = int(1 + b * 1.5)
        for k in range(n):
            a = -0.4 - hash01(k, 1, 90) * 2.6 if k % 2 else 2.2 + hash01(k, 1, 90) * 1.6
            rr = 3.5 + hash01(k, 2, 90) * 4
            c = add(O, (math.cos(a) * rr * 0.9, math.sin(a) * rr * 1.3))
            r = 1.2 + 0.45 * b + hash01(k, 3, 90) * 0.6
            R.dome(Rf, c, r, r * 0.9, "V", 0)
            pustule(Rf, R.T(add(c, (0.3, -0.3))), 0.5 + 0.12 * b, hot=b >= 2)
        if b >= 2:
            for k in range(12):   # light leaking from the cracks
                a = k * 0.5236 + fi * 0.4
                r0 = 9 + b
                q0 = add(O, (math.cos(a) * r0, math.sin(a) * r0 * 1.2))
                q1 = add(O, (math.cos(a) * (r0 + 2 + b), math.sin(a) * (r0 + 2 + b) * 1.2))
                if k % 2 == 0:
                    FX.put([q for q in line(q0, q1) if q[1] <= FLOOR], "O4" if b >= 3 else "O3")
        return
    grow = {4: 0.6, 5: 1.0, 6: 0.8, 7: 0.42, 8: 0.18}.get(int(b), 0.1)
    droop = {4: 0.0, 5: 0.05, 6: 0.25, 7: 0.4, 8: 0.5}.get(int(b), 0.5)
    # (angle deg, length, front?, ground?)
    TEN = [(196, 38, 0, True), (156, 30, 0, True), (222, 30, 0, False), (246, 22, 0, False), (180, 26, 1, False),
           (-16, 38, 0, True), (24, 30, 0, True), (-42, 30, 0, False), (-68, 22, 0, False), (2, 24, 1, False),
           (268, 18, 0, False), (126, 18, 1, True), (58, 20, 1, True), (-100, 14, 1, False)]
    for k, (ang, L0, front, ground) in enumerate(TEN):
        L_ = L0 * grow * (0.88 + 0.24 * hash01(k, 4, 91))
        if L_ < 2.5:
            continue
        s = 1 if math.cos(math.radians(ang)) >= 0 else -1
        base = add(O, (math.cos(math.radians(ang)) * 3.0, math.sin(math.radians(ang)) * 4.0))
        if ground:
            reach = L_ * 1.05
            end = (O[0] + s * reach, FLOOR - 1.0)
            ctl1 = add(base, (s * reach * 0.3, -9 * grow))
            ctl2 = (end[0] - s * reach * 0.3, end[1] - 11 * grow)
            pts = bezier(base, ctl1, ctl2, end, n=14)
            pts.append((end[0] + s * 8 * grow, FLOOR - 0.5))
        else:
            a = math.radians(ang)
            end = add(base, (math.cos(a) * L_, math.sin(a) * L_ + droop * L_ * 0.5))
            curl = 4 * (1 if k % 2 else -1)
            ctl1 = add(base, (math.cos(a) * L_ * 0.4 - math.sin(a) * curl, math.sin(a) * L_ * 0.4 + math.cos(a) * curl))
            ctl2 = add(end, (-math.cos(a) * L_ * 0.3 + math.sin(a) * curl * 0.5, -math.sin(a) * L_ * 0.3 + droop * 3))
            pts = bezier(base, ctl1, ctl2, end, n=12)
        Lr = Rf if front else Rb
        r0 = 3.0 * (0.55 + 0.45 * grow) * (0.8 if front else 1.0)
        m = tube(ID, Lr, pts, r0, 0.5, "V", bias=0 if front else -1)
        m = {q for q in m if q[1] <= FLOOR}
        # glowing vein near the root only, a boil, and a burning thorn tip
        vein = polyline(pts[1:6])
        Lr.decal([q for i, q in enumerate(vein) if i % 3 != 2], "O3" if b <= 5 else "O2")
        if b <= 6 and len(pts) > 7:
            pustule(Lr, pts[5], 0.6 + 0.3 * hash01(k, 5, 92), hot=b == 5)
        if b <= 5:
            tp = ip(pts[-1])
            FX.put([tp], "O5")
            FX.put([(tp[0] - s, tp[1])], "O4")
        hit |= m
    # core flash + spray
    if b in (4, 5):
        rr = 7 if b == 4 else 11
        for k in range(28):
            a = k / 28 * 6.283
            q = ip(add(O, (math.cos(a) * rr, math.sin(a) * rr * 1.15)))
            if q[1] <= FLOOR:
                FX.put([q], "O5" if k % 3 == 0 else "O4")
        for k in range(30):
            a = hash01(k, 5, 93) * 6.283
            r = (12 + hash01(k, 6, 93) * 30) * (0.6 if b == 4 else 1.0)
            q = ip(add(O, (math.cos(a) * r * 1.3, math.sin(a) * r * 0.8)))
            if q[1] <= FLOOR:
                FX.put([q], ("O4", "O3", "V5", "V4")[k % 4])
                if k % 3 == 0:
                    FX.put([(q[0] + 1, q[1])], ("O3", "V4")[k % 2])
    elif b >= 6:
        for k in range(18):
            a = hash01(k, 5, 94) * 6.283
            r = 16 + hash01(k, 6, 94) * 26
            q = ip(add(O, (math.cos(a) * r * 1.3, min(FLOOR - O[1], math.sin(a) * r * 0.7 + (b - 5) * 8))))
            if q[1] <= FLOOR:
                FX.put([q], ("V4", "V3", "O3")[k % 3])
    if b in (5, 6):
        for dx in range(-44, 45):
            if hash01(dx, 1, 95) < 0.55 and abs(dx) > 4:
                FX.put([(int(O[0] + dx), FLOOR)], "V4" if abs(dx) % 5 else "O3")
    info["hit"] |= hit
    info["burst_mask"] = hit


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(6):
        b = (0, 0.4, 0.9, 1.2, 0.9, 0.4)[i]
        fr.append((170, P_(P=(39.5, 51.5 + b * 0.35), C=(40.8, 40.4 + b), Hd=(42.4, 30.2 + b * 1.05),
                           hf=(49.0, 49.0 + b * 0.6), wang=-58 + b * 1.5, wind=0.4 * math.sin(i * 1.05))))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (40.4 + 7.4 * c, 71 - max(0.0, -s) * 3.6)
        fb = (39.4 - 7.4 * c, 71 - max(0.0, s) * 3.6)
        bob = 1.5 * abs(c)
        fr.append((120, P_(P=(39.8, 50.8 + bob), C=(41.6, 39.8 + bob), Hd=(43.4, 29.6 + bob), ff=ff, fb=fb,
                           hf=(49.6 + 0.8 * c, 48.6 + bob), wang=-56 + 3 * c)))
    return fr


def a_combo():
    WB = dict(wl="WeaponBack")
    raise_ = dict(P=(38.4, 52.0), C=(37.4, 41.2), Hd=(37.8, 31.0), hup=(-0.22, -1), fb=(30.0, 71), ff=(46.5, 71))
    lunge = dict(P=(44.4, 53.6), C=(48.4, 43.2), Hd=(51.6, 33.8), hup=(0.42, -1), fb=(31.0, 71), ff=(56.0, 71))
    low = dict(P=(41.6, 54.2), C=(41.0, 43.4), Hd=(42.0, 33.2), hup=(-0.05, -1), fb=(30.5, 71), ff=(53.5, 71))
    rise = dict(P=(45.0, 52.2), C=(48.2, 41.6), Hd=(50.8, 31.6), hup=(0.3, -1), fb=(33.0, 71), ff=(57.0, 71))
    coil = dict(P=(40.0, 53.0), C=(37.6, 42.4), Hd=(37.4, 32.4), hup=(-0.2, -1), fb=(29.0, 71), ff=(49.0, 71))
    cleave = dict(P=(46.4, 54.4), C=(51.0, 44.2), Hd=(54.4, 34.8), hup=(0.38, -1), fb=(31.0, 71), ff=(59.0, 71))
    return [
        # slash 1: rising to an overhead, diagonal down cut
        (130, P_(**raise_, hf=(43.0, 34.0), wang=-100)),
        (300, P_(**dict(raise_, C=(36.8, 41.6), Hd=(37.0, 31.6)), hf=(37.0, 25.0), wang=-150, eye=2, **WB)),
        (60, P_(**lunge, hf=(59.0, 39.0), wang=-6, wind=4,
                smear=dict(g0=(37.0, 25.0), a0=-150, mid=(47.0, 18.0), start=0.1))),
        (100, P_(**lunge, hf=(56.0, 50.0), wang=40, wind=3, smear=dict(g0=(59.0, 39.0), a0=-6, taper=0.4, u0=18))),
        # slash 2: blade drops behind, rising backhand
        (110, P_(**low, hf=(40.0, 57.0), wang=162, **WB)),
        (170, P_(**dict(low, C=(40.4, 43.8), Hd=(41.2, 33.6)), hf=(39.0, 58.0), wang=168, eye=2, **WB)),
        (60, P_(**rise, hf=(60.0, 45.0), wang=-32, wind=4,
                smear=dict(g0=(39.0, 58.0), a0=168, mid=(50.0, 62.0), start=0.08))),
        (100, P_(**rise, hf=(55.0, 33.0), wang=-82, wind=3, smear=dict(g0=(60.0, 45.0), a0=-32, taper=0.2, u0=26,
                                                                         start=0.35))),
        # slash 3: coil the blade far back, then a flat, low, wide cleave
        (150, P_(**coil, hf=(33.0, 41.0), wang=-176, **WB)),
        (340, P_(**dict(coil, C=(37.0, 42.8), Hd=(36.6, 32.8)), hf=(32.0, 42.0), wang=-172, eye=2, **WB)),
        (60, P_(**cleave, hf=(62.0, 49.0), wang=6, wind=5,
                flat=dict(c=(50.0, 50.0), rx=44.0, ry=9.5, th0=-160, th1=10, w=7.0))),
        (110, P_(**cleave, hf=(53.0, 52.0), wang=158, wind=4,
                 flat=dict(c=(50.0, 50.0), rx=44.0, ry=9.5, th0=-30, th1=160, w=4.0, fade=0.5))),
        (200, P_(P=(43.0, 53.2), C=(44.6, 42.6), Hd=(46.6, 32.8), hup=(0.25, -1), fb=(31.5, 71), ff=(54.0, 71),
                 hf=(52.0, 55.0), wang=38)),
        (220, P_(P=(40.6, 52.0), C=(42.0, 41.0), Hd=(43.6, 30.8), fb=(32.0, 71), ff=(49.0, 71), hf=(50.0, 50.0),
                 wang=-30)),
    ]


def a_thrust():
    draw_ = dict(P=(37.6, 52.6), C=(35.8, 42.2), Hd=(36.2, 32.2), hup=(-0.12, -1), fb=(29.0, 71), ff=(47.0, 71))
    lunge = dict(P=(48.0, 55.2), C=(54.2, 46.2), Hd=(58.6, 37.4), hup=(0.55, -1), fb=(29.5, 71), ff=(62.5, 71))
    return [
        (130, P_(P=(39.0, 52.0), C=(39.6, 41.0), Hd=(41.0, 30.8), hf=(47.0, 50.0), wang=-30)),
        (150, P_(**draw_, hf=(34.0, 47.5), wang=-4)),
        (360, P_(**dict(draw_, C=(35.2, 42.6), Hd=(35.4, 32.6)), hf=(32.5, 48.0), wang=-3, eye=2,
                 glint=(63.5, 46.4))),
        (70, P_(**lunge, hf=(61.5, 49.5), wang=1, wind=5, thrust=dict(u0=-30, u1=6, offs=(-3, -1, 2, 4)))),
        (130, P_(**lunge, hf=(62.5, 50.0), wang=2, wind=3, thrust=dict(u0=-18, u1=4, offs=(-2, 3), flash=32))),
        (140, P_(P=(46.4, 54.4), C=(51.2, 44.8), Hd=(54.8, 35.4), hup=(0.4, -1), fb=(30.0, 71), ff=(60.0, 71),
                 hf=(58.0, 53.0), wang=22)),
        (150, P_(P=(43.2, 53.0), C=(45.6, 42.4), Hd=(47.8, 32.4), hup=(0.25, -1), fb=(31.0, 71), ff=(54.0, 71),
                 hf=(53.0, 51.0), wang=-6)),
        (150, P_(P=(41.0, 52.2), C=(42.4, 41.2), Hd=(44.2, 31.0), fb=(31.5, 71), ff=(50.0, 71), hf=(50.0, 50.0),
                 wang=-40)),
        (150, P_(hf=(49.0, 49.4), wang=-54)),
    ]


def a_leap():
    WB = dict(wl="WeaponBack")
    crouch = dict(P=(39.0, 56.0), C=(41.6, 45.6), Hd=(44.0, 35.8), hup=(0.25, -1), fb=(31.0, 71), ff=(48.0, 71))
    land = dict(P=(45.0, 57.0), C=(50.4, 47.4), Hd=(54.2, 38.6), hup=(0.5, -1), fb=(31.5, 71), ff=(58.0, 71))
    air = dict(P=(40.0, 52.0), C=(40.4, 41.0), Hd=(41.2, 31.0), hup=(-0.05, -1), fb=(33.0, 67), ff=(46.0, 66),
               kb=None, kf=None)
    return [
        (140, P_(**crouch, hf=(44.0, 58.0), wang=160, **WB)),
        (240, P_(**dict(crouch, P=(38.6, 58.0), C=(41.4, 47.8), Hd=(44.4, 38.2), hup=(0.3, -1)), hf=(43.0, 60.0),
                 wang=165, eye=2, dust=2, **WB)),
        (80, up(P_(P=(41.0, 50.0), C=(42.4, 39.0), Hd=(44.0, 29.0), hup=(0.1, -1), fb=(35.0, 70.5), ff=(46.0, 64.0),
                   hf=(46.0, 32.0), wang=-110, lift=4, dust=1), 2)),
        (100, up(P_(**dict(air, P=(40.0, 50.0), C=(40.6, 39.2), Hd=(41.6, 29.2), fb=(33.0, 64.0), ff=(47.0, 62.0)),
                    hf=(36.0, 29.0), wang=-138, lift=10, **WB), 5)),
        (110, up(P_(**dict(air, P=(40.0, 50.0), C=(40.0, 39.4), Hd=(40.4, 29.4), hup=(-0.1, -1), fb=(34.0, 63.0),
                           ff=(47.0, 61.0)), hf=(34.5, 28.0), wang=-150, lift=6, **WB), 6)),
        (220, up(P_(**dict(air, P=(40.0, 50.0), C=(39.0, 39.8), Hd=(38.8, 29.8), hup=(-0.25, -1), fb=(34.0, 63.0),
                           ff=(47.0, 61.0)), hf=(33.0, 28.5), wang=-160, lift=2, eye=2, **WB), 6)),
        (80, up(P_(P=(42.0, 51.0), C=(43.6, 40.4), Hd=(45.4, 30.6), hup=(0.2, -1), fb=(35.0, 66.0), ff=(49.0, 64.0),
                   hf=(35.0, 29.0), wang=-164, lift=-6, **WB), 4)),
        (60, up(P_(P=(44.0, 52.0), C=(47.0, 41.6), Hd=(49.6, 32.0), hup=(0.35, -1), fb=(36.0, 68.0), ff=(52.0, 67.0),
                   hf=(57.0, 33.0), wang=-60, lift=-8, wind=3,
                   smear=dict(g0=(35.0, 25.0), a0=-164, mid=(46.0, 14.0), start=0.15)), 2)),
        (70, P_(**land, hf=(62.0, 55.0), wang=36, impact=1, wind=3,
                smear=dict(g0=(57.0, 31.0), a0=-60, taper=0.5))),
        (140, P_(**land, hf=(62.0, 55.4), wang=36, impact=2)),
        (200, P_(P=(43.0, 54.2), C=(46.4, 43.6), Hd=(49.4, 33.8), hup=(0.3, -1), fb=(32.0, 71), ff=(55.0, 71),
                 hf=(56.0, 54.0), wang=40)),
        (200, P_(P=(40.6, 52.0), C=(42.0, 41.0), Hd=(43.8, 30.8), fb=(32.0, 71), ff=(49.0, 71), hf=(50.0, 50.0),
                 wang=-20)),
    ]


def a_guard():
    g = dict(P=(38.6, 53.0), C=(39.4, 42.0), Hd=(40.4, 32.0), hup=(0.02, -1), fb=(29.0, 71), ff=(47.0, 71))
    return [
        (200, P_(**g, hf=(48.0, 44.0), wang=-94, hb=(48.6, 30.0))),
        (200, P_(**dict(g, P=(38.6, 53.3), C=(39.4, 42.4), Hd=(40.4, 32.4)), hf=(48.0, 44.3), wang=-94,
                 hb=(48.6, 30.3), glint=(48.0, 22.0))),
    ]


def a_backstep():
    return [
        (90, P_(P=(40.0, 54.0), C=(41.8, 43.4), Hd=(43.6, 33.4), hup=(0.2, -1), fb=(32.0, 71), ff=(47.0, 71),
                hf=(48.0, 52.0), wang=-40)),
        (80, up(P_(P=(38.4, 51.0), C=(36.8, 40.4), Hd=(36.6, 30.4), hup=(-0.22, -1), fb=(30.0, 69.0), ff=(49.0, 71.0),
                   hf=(45.0, 47.0), wang=-52, dust=1, wind=-2, lift=3), 2)),
        (110, up(P_(P=(37.0, 50.0), C=(35.6, 39.4), Hd=(35.8, 29.4), hup=(-0.15, -1), fb=(30.0, 67.0), ff=(44.0, 66.0),
                    hf=(43.0, 44.0), wang=-48, wind=-5, lift=7), 6)),
        (100, up(P_(P=(37.4, 51.0), C=(37.0, 40.4), Hd=(37.8, 30.4), hup=(-0.05, -1), fb=(29.0, 69.0), ff=(45.0, 70.0),
                    hf=(44.0, 46.0), wang=-42, wind=-3, lift=2), 2)),
        (110, P_(P=(38.2, 55.4), C=(39.6, 45.0), Hd=(41.2, 35.0), hup=(0.1, -1), fb=(30.0, 71), ff=(46.0, 71),
                 hf=(46.0, 53.0), wang=-36, dust=1)),
        (160, P_(P=(39.2, 52.4), C=(40.4, 41.4), Hd=(42.0, 31.2), hf=(48.0, 50.0), wang=-52, dust=2)),
    ]


def a_rotburst():
    plant = ((51.0, 50.0), 88)
    base = dict(sword=plant, hf=(51.0, 50.0))
    hunch = dict(P=(40.0, 54.0), C=(43.0, 44.4), Hd=(46.4, 35.8), hup=(0.55, -1), fb=(31.0, 71), ff=(47.0, 71))
    arch = dict(P=(39.4, 52.4), C=(38.6, 41.4), Hd=(37.6, 31.6), hup=(-0.35, -1), fb=(29.5, 71), ff=(48.0, 71))
    return [
        (140, P_(P=(40.0, 52.6), C=(41.8, 42.0), Hd=(44.0, 32.4), hup=(0.3, -1), **base, hb=(45.0, 42.0))),
        (160, P_(**hunch, **base, hb=(46.0, 45.0), burst=1)),
        (120, P_(**up(hunch, 0, 1), **base, hb=(46.5, 45.5), burst=1.5)),
        (120, P_(**up(hunch, 0, -1), **base, hb=(46.0, 45.0), burst=2, eye=2)),
        (140, P_(**arch, **base, hb=(29.0, 36.0), burst=2.5)),
        (300, P_(**dict(arch, C=(38.2, 41.8), Hd=(37.0, 32.2)), **base, hb=(27.0, 34.0), burst=3, eye=2)),
        (80, P_(**arch, **base, hb=(26.0, 33.0), burst=4, eye=2, wind=4)),
        (140, P_(**arch, **base, hb=(26.0, 33.0), burst=5, eye=2, wind=3)),
        (140, P_(**arch, **base, hb=(27.0, 35.0), burst=6)),
        (180, P_(P=(40.0, 53.6), C=(42.6, 43.2), Hd=(45.4, 34.0), hup=(0.45, -1), **base, hb=(45.0, 44.0), burst=7)),
        (180, P_(P=(40.0, 52.8), C=(41.8, 42.2), Hd=(44.0, 32.4), hup=(0.25, -1), **base, hb=(49.0, 49.0), burst=8)),
        (200, P_(P=(39.6, 52.0), C=(41.0, 41.0), Hd=(42.6, 30.8), hf=(49.0, 50.0), wang=-40)),
    ]


def a_stagger():
    return [
        (90, P_(P=(37.6, 52.2), C=(35.4, 41.8), Hd=(34.6, 32.2), hup=(-0.45, -1), fb=(30.0, 71), ff=(47.0, 71),
                hf=(42.0, 36.0), wang=-128, eye=0, wl="WeaponBack")),
        (130, P_(P=(38.0, 56.0), C=(38.8, 45.8), Hd=(40.6, 36.2), hup=(0.2, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hf=(47.0, 56.0), wang=68, eye=0)),
        (260, P_(P=(38.4, 57.0), C=(40.6, 47.0), Hd=(43.8, 38.2), hup=(0.5, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hf=(48.0, 58.0), wang=74, eye=0)),
        (260, P_(P=(38.2, 57.4), C=(40.0, 47.4), Hd=(43.0, 38.8), hup=(0.46, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hf=(47.6, 58.4), wang=76, eye=0)),
    ]


def a_death():
    plant = ((50.0, 51.0), 91)
    KN = dict(P=(38.0, 60.0), C=(40.8, 49.4), Hd=(44.0, 40.0), hup=(0.45, -1), kb=(35.0, 69.2), fb=(25.5, 71),
              ff=(47.0, 71), sword=plant, hf=(50.0, 51.0), hb=(49.4, 53.0), eye=0)
    fr = [
        (100, P_(P=(37.6, 52.2), C=(35.4, 41.8), Hd=(34.6, 32.2), hup=(-0.5, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hf=(43.0, 38.0), wang=-120, eye=2, wl="WeaponBack")),
        (160, P_(P=(38.6, 55.0), C=(39.8, 44.6), Hd=(41.8, 35.0), hup=(0.25, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hf=(47.0, 56.0), wang=70, eye=1)),
        (180, P_(**KN)),
        (260, P_(**dict(KN, Hd=(45.0, 41.0), hup=(0.6, -1)))),
        (500, P_(**dict(KN, Hd=(45.0, 41.2), hup=(0.62, -1)))),
        (300, P_(**dict(KN, C=(41.6, 50.4), Hd=(46.2, 42.6), hup=(0.75, -1)))),
        (600, P_(**dict(KN, C=(41.6, 50.6), Hd=(46.4, 42.8), hup=(0.78, -1)))),
    ]
    for d, ms in ((0.14, 140), (0.32, 140), (0.5, 140), (0.7, 160), (0.95, 900)):
        fr.append((ms, P_(**dict(KN, C=(41.6, 50.6), Hd=(46.4, 42.8), hup=(0.78, -1)), dissolve=d)))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("combo", a_combo), ("thrust", a_thrust), ("leap", a_leap),
           ("guard", a_guard), ("backstep", a_backstep), ("rotburst", a_rotburst), ("stagger", a_stagger),
           ("death", a_death)]
COUNTS = dict(idle=6, walk=8, combo=14, thrust=9, leap=12, guard=2, backstep=6, rotburst=12, stagger=4, death=12)
LOOPS = ("idle", "walk", "guard")


# =========================================================================== render
def render_frame(p, fi, sw, phase):
    Ls, info = draw(p, fi, sw, phase)
    imgs = {}
    for n in LAYERS:
        v = Ls.get(n)
        if v is None:
            continue
        imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
    if p["dissolve"] > 0:
        pal = ("Q4", "Q3", "Y2", "G3", "N2") if phase == 1 else ("O5", "O4", "O3", "V4", "V3")
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in ("Weapon", "WeaponBack", "FX", "Spores")],
                                fx_name="FX", seed=3, rise=24, pal=pal)
    if p["shake"]:
        imgs = K.shift_imgs(imgs, p["shake"], 0)
    return imgs, info


def render_all(only=None):
    out = {1: [], 2: []}
    infos, tags = {}, []
    n = 0
    for tag, fn in TAGDEFS:
        fr = fn()
        assert len(fr) == COUNTS[tag], (tag, len(fr))
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in (1, 2):
                imgs, info = render_frame(p, a + k, sway[k], ph)
                out[ph].append((ms, imgs))
                if ph == 1:
                    infos[tag].append(info)
                else:
                    infos[tag][-1]["p2"] = info
            n += 1
        tags.append((tag, a, n - 1))
        print("rendered", tag, len(fr))
    return out, infos, tags


# =========================================================================== previews
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
    rows = []
    for t, d in meta["attacks"].items():
        wins = d["windows"] if "windows" in d else [d]
        rows.append((t, wins))
    rows.append(("idle", []))
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
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rr = w.get("rects", {}).get(str(k), w["hit"])
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(rr, (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = rr
                    rect([min(W - 10, max(0, hx + hw - 6)), H - 26, 10, 26], (90, 150, 255, 255))
                    if t == "rotburst":
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


# =========================================================================== meta
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


def attack(infos, tag, a, b, x_min=AX + 2, both=False):
    rs = {}
    for k in range(a, b + 1):
        pts = set(infos[tag][k]["hit"])
        if "p2" in infos[tag][k]:
            pts |= infos[tag][k]["p2"]["hit"]
        if not both:
            pts = {q for q in pts if q[0] >= x_min}
        r = bbox(pts)
        r[3] = H - r[1]                 # reach the floor: a 10x26 player standing there must be hit
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def build_meta(infos, tags, flats):
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["head"] | idle.get("pauldron", set()))
    hurt = [tb[0], tb[1], tb[2], H - tb[1]]

    def pt(q):
        return [int(round(q[0])), int(round(q[1]))]
    combo = [attack(infos, "combo", 2, 3), attack(infos, "combo", 6, 7), attack(infos, "combo", 10, 11)]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {
            "combo": {"windows": combo},
            "thrust": attack(infos, "thrust", 3, 4),
            "leap": attack(infos, "leap", 8, 9),
            "rotburst": attack(infos, "rotburst", 6, 8, both=True),
        },
        "telegraph": {
            "combo": {"frame": 1, "at": pt(infos["combo"][1]["tip"])},
            "thrust": {"frame": 2, "at": [63, 46]},
            "leap": {"frame": 5, "at": pt(infos["leap"][5]["tip"])},
            "rotburst": {"frame": 5, "at": pt(lerp(a_rotburst()[5][1]["P"], a_rotburst()[5][1]["C"], 0.55))},
        },
        "spawn": {
            "leap": {"frame": 8, "at": [infos["leap"][8]["impact_x"], H - 1]},
            "rotburst": {"frame": 6, "at": [AX, H - 1]},
        },
        "notes": "faces right, anchor = feet. combo = 3 windows (overhead cut, rising backhand, low flat cleave). "
                 "'hit' = union of per-frame 'rects' over the inclusive active range. Telegraph 'at' = glint point on "
                 "the anticipation hold. leap is drawn in place (engine moves him; airborne frames 2-7), spawn.leap = "
                 "blade impact on the floor (shockwave / fx_rot_wave in phase 2). rotburst: hit covers BOTH sides; "
                 "spawn.rotburst = floor under him (fx_rot_wave both directions). guard = parry/block stance loop; "
                 "backstep drawn in place (engine moves him back). kalden_p2 shares this meta.",
    }
    return meta


# =========================================================================== FX sheets
def fx_kalden_slash():
    """80x48, 4 frames: teal-gold crescent (Kalden's blade wave / slash overlay), faces right, centred."""
    w, h = 80, 48
    frames = []
    for i in range(4):
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cp, gp = core.load(), glow.load()
        # crescent = outer ellipse minus an inner ellipse shifted back; grows & thins as it flies
        ox = 40 + i * 4
        rx, ry = 20 + i * 1.5, 21.5
        th = [11.0, 9.5, 7.0, 4.5][i]
        for y in range(h):
            for x in range(w):
                ux, uy = (x + .5 - ox) / rx, (y + .5 - 24) / ry
                d_out = math.hypot(ux, uy)
                if d_out > 1:
                    continue
                ix, iy = (x + .5 - (ox - th)) / rx, (y + .5 - 24) / ry
                d_in = math.hypot(ix, iy)
                if d_in <= 1:
                    continue
                grad = math.hypot(ux / rx, uy / ry) / max(d_out, 1e-6)
                edge = (1 - d_out) / max(grad, 1e-6)          # px from the outer (leading) edge
                inner = (d_in - 1) * rx * 0.8                  # px from the inner (trailing) edge
                tot = edge + inner
                v = edge / max(tot, 0.1)
                if i == 3 and hash01(x, y, 5) < 0.3 + 0.4 * v:
                    continue
                if edge < 1.0:
                    c = "Y3"
                elif edge < 2.2 and i < 3:
                    c = "G4" if abs(uy) < 0.75 else "Y2"
                elif v < 0.5:
                    c = "Q3" if i < 2 else "Q2"
                elif v < 0.8:
                    c = "Q2" if (i < 2 or (x + y) % 2) else "Q1"
                else:
                    c = "Q1" if (x + y) % 2 == 0 else "N2"
                (cp if (edge < 2.2 or v < 0.5) else gp)[x, y] = RGBA[c]
        # trailing sparks
        for k in range(12):
            a = (hash01(k, i, 3) - 0.5) * 140
            r = 14 + hash01(k, i, 4) * 10
            x = int(ox - th - 3 + math.cos(math.radians(a)) * r * 0.7 - hash01(k, i, 6) * 8)
            y = int(24 + math.sin(math.radians(a)) * r)
            if 0 <= x < w and 0 <= y < h and not cp[x, y][3]:
                gp[x, y] = RGBA["G4" if k % 3 == 0 else "Q3" if k % 3 == 1 else "Q2"]
        frames.append({"ms": (50, 60, 70, 80)[i], "cels": {"Glow": glow, "Core": core}})
    return frames


def fx_rot_wave():
    """32x24, 4 frames loop: a creeping rot ground-wave travelling right (pivot bottom-centre)."""
    w, h = 32, 24
    frames = []
    for i in range(4):
        back = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bp, dp, gp = back.load(), body.load(), glow.load()
        crest = 21 + (i % 2)
        peak = 13 + (1 if i in (1, 2) else 0)
        tops = {}
        for x in range(w):
            if x <= crest:
                u = x / crest
                hgt = peak * (0.5 - 0.5 * math.cos(math.pi * u)) ** 1.2 + 1.5 + math.sin(x * 0.8 + i * 1.6) * 0.8 * u
            else:
                u = (x - crest) / (w - 1 - crest)
                hgt = peak * math.sqrt(max(0.0, 1 - u * u)) + 0.5
            if hgt < 1:
                continue
            top = h - hgt
            tops[x] = top
            for y in range(int(top), h):
                dep = y - top
                dx_front = crest - x
                if dep < 1.0:
                    c = "V5"
                elif dep < 2.5:
                    c = "V4"
                elif dep < 5:
                    c = "V3" if (x + 2 * y + i) % 6 else "V4"
                elif dep < 9:
                    c = "V2" if (x * 3 + y + i) % 7 else "V3"
                else:
                    c = "V1" if (x + y) % 3 else "V2"
                if x > crest and dep < 2:
                    c = "V4"
                dp[x, y] = RGBA[c]
        # curling lip over the front face
        lx0 = crest - 2
        for k in range(5):
            x, y = lx0 + k, int(tops.get(crest, h - peak)) - 1 + (k * k) // 5
            if 0 <= x < w and 0 <= y < h:
                dp[x, y] = RGBA["V5" if k < 3 else "V4"]
        # 1px outline around the mass
        for y in range(h):
            for x in range(w):
                if dp[x, y][3]:
                    continue
                if any(0 <= x + a < w and 0 <= y + b < h and dp[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    bp[x, y] = RGBA["OUT"]
        # glowing boils inside + hot lip
        for k in range(6):
            x = 6 + int(hash01(k, i // 2, 2) * (crest - 6))
            t = tops.get(x, h)
            y = int(min(h - 2, t + 3 + hash01(k, 1, 3) * (h - t - 4)))
            if dp[x, y][3]:
                gp[x, y] = RGBA["O4" if (k + i) % 2 else "O3"]
                if y + 1 < h and dp[x, y + 1][3]:
                    gp[x, y + 1] = RGBA["O2"]
        for k in range(3):
            x = crest - 1 + k
            y = int(tops.get(crest, h - peak))
            if 0 <= x < w and 0 <= y < h:
                gp[x, y] = RGBA["O4" if k == 1 else "O3"]
        for k in range(6):     # spray flicked off the crest
            x = crest - 2 + int(hash01(k, i, 6) * 9)
            y = h - peak - 2 - int(hash01(k, i, 7) * 6)
            if 0 <= x < w and 0 <= y < h and not dp[x, y][3] and not bp[x, y][3]:
                gp[x, y] = RGBA[("V5", "O4", "V4")[k % 3]]
        frames.append({"ms": 80, "cels": {"Back": back, "Body": body, "Glow": glow}})
    return frames


# =========================================================================== main
def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    out, infos, tags = render_all(only)
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    flats = {ph: [K.flatten(imgs, LAYERS) for _, imgs in out[ph]] for ph in (1, 2)}
    sfx = "_wip" if only else ""
    preview_rows(tags, flats[1], os.path.join(pv, f"kalden{sfx}.png"))
    preview_rows(tags, flats[2], os.path.join(pv, f"kalden_p2{sfx}.png"))
    c = Image.new("RGBA", (W * 2, H), BG)
    c.alpha_composite(flats[1][0]); c.alpha_composite(flats[2][0], (W, 0))
    c.resize((W * 2 * 5, H * 5), Image.NEAREST).save(os.path.join(pv, f"kalden_closeup{sfx}.png"))
    if only:
        return
    meta = build_meta(infos, tags, flats[1])
    hitbox_preview(tags, flats[1], meta, os.path.join(pv, "kalden_hitbox.png"))
    hitbox_preview(tags, flats[2], meta, os.path.join(pv, "kalden_p2_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "kalden_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        for w in d.get("windows", [d]):
            print("attack", t, w["active"], w["hit"])
    print("hurtbox", meta["hurtbox"], "telegraph", meta["telegraph"], "spawn", meta["spawn"])

    ks, rw = fx_kalden_slash(), fx_rot_wave()
    s = 4
    sheet = Image.new("RGBA", (4 * 82 * s, (48 + 2 + 24) * s), (40, 40, 46, 255))
    for i, f in enumerate(ks):
        fr = Image.new("RGBA", (80, 48), BG); fr.alpha_composite(K.flatten if False else f["cels"]["Glow"])
        fr.alpha_composite(f["cels"]["Core"])
        sheet.alpha_composite(fr.resize((80 * s, 48 * s), Image.NEAREST), (i * 82 * s, 0))
    for i, f in enumerate(rw):
        fr = Image.new("RGBA", (32, 24), BG)
        for n in ("Back", "Body", "Glow"):
            fr.alpha_composite(f["cels"][n])
        sheet.alpha_composite(fr.resize((32 * s, 24 * s), Image.NEAREST), (i * 34 * s, 50 * s))
    sheet.save(os.path.join(pv, "fx_kalden.png"))

    if BUILD:
        fr1 = [{"ms": ms, "cels": imgs} for ms, imgs in out[1]]
        fr2 = [{"ms": ms, "cels": imgs} for ms, imgs in out[2]]
        asebuild.build("kalden", W, H, LAYERS, fr1, tags)
        asebuild.build("kalden_p2", W, H, LAYERS, fr2, tags)
        asebuild.build("fx_kalden_slash", 80, 48, ["Glow", "Core"], ks, [("kalden_slash", 0, 3)])
        asebuild.build("fx_rot_wave", 32, 24, ["Back", "Body", "Glow"], rw, [("rot_wave", 0, 3)])


if __name__ == "__main__":
    main()
