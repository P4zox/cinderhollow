#!/usr/bin/env python3
"""Mini-boss generator -- "the Ice Golem Warden" of the Hoarfrost Aqueduct (Sluice Gates).

    python3 art/gen_hoarfrost_warden.py              full build: ice_warden + ice_warden_p2 + fx_hf_icespike + fx_hf_shatter
    python3 art/gen_hoarfrost_warden.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_hoarfrost_warden.py --only slam,sweep --preview   quick iteration on some tags (_wip previews)

Outputs
    art/ice_warden.aseprite, assets/ice_warden.png/.json          phase 1: armoured guardian in a thick ice shell
    art/ice_warden_p2.aseprite, assets/ice_warden_p2.png/.json    phase 2 (same frames/tags/durations): shell gone,
                                                                  cracked plates leaking frost light, glowing core
    assets/ice_warden_meta.json                                   meta shared by both sheets
    art/fx_hf_icespike.aseprite, assets/fx_hf_icespike.*           24x64, 8 frames (tag hf_icespike), pivot bottom
    art/fx_hf_shatter.aseprite, assets/fx_hf_shatter.*             64x64, 6 frames (tag hf_shatter), centred
    art/previews/ice_warden.png, ice_warden_p2.png (3x, one row per tag), ice_warden_hitbox.png,
    ice_warden_closeup.png (p1 | p2 idle at 5x), ice_warden_scale.png (1x next to the player), fx_hf_warden.png

Method: enemy_kit.py (normal-field shading, sel-out outlines, Rig, spring sway, ember_dissolve) -- same family as
gen_kalden.py, scaled up to a ~90px guardian in a 144x112 frame.  Faces RIGHT, feet on the bottom row, anchor x = 60.
The ice shell lives on its own layers (ShellBack / Shell / ShellArm): faceted crystal plates whose shading is
nudged by the armour beneath (seams and trim read faintly through the ice), deep-blue cores, bright facet rims.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_capsule, norm3, leg, arm, dirv, dist_field)

W, H = 144, 112
K.setup(W, H)
FLOOR = H - 1
AX = 60
BUILD = "--preview" not in sys.argv
NAME = "ice_warden"

# ---------------------------------------------------------------- palette additions (runtime only, this process)
EXTRA = {
    # blue-black iron-bronze plate
    "E0": "#080a10", "E1": "#111623", "E2": "#1d2536", "E3": "#324059", "E4": "#566987", "E5": "#9fb2cb",
    # cold bronze trim
    "H0": "#150f0c", "H1": "#2c2119", "H2": "#4b3a2a", "H3": "#6f5a3f", "H4": "#9a8260", "H5": "#cdb994",
    # dark basalt
    "J0": "#08090c", "J1": "#121319", "J2": "#1c1e26", "J3": "#2a2d38", "J4": "#40434f", "J5": "#62667a",
    # ice crystal (edges, thin ice)
    "N0": "#10263a", "N1": "#1f5470", "N2": "#3a8fae", "N3": "#6cc6de", "N4": "#b4ecf6", "N5": "#f2feff",
    # deep glacier ice (thick cores)
    "Z0": "#0a1426", "Z1": "#112743", "Z2": "#1a3d63", "Z3": "#285c86", "Z4": "#3f83ab", "Z5": "#7cc0da",
    # haft leather wrap
    "X0": "#0d0b0d", "X1": "#1a1618", "X2": "#2a2427", "X3": "#3e3538",
    # frost glow (fixed colours)
    "U0": "#173a73", "U1": "#2f73c2", "U2": "#6fbaf2", "U3": "#c4ecff", "U4": "#ffffff",
}
for k, v in EXTRA.items():
    K.HEX[k] = v
    K.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k[0], []).append(k)
K.SHINY.update({"E": 0.93, "H": 0.9, "N": 0.86, "Z": 0.9})
K.SMEAR["ice"] = ["U4", "U3", "N3", "N1"]
K.SMEAR["ice2"] = ["U4", "U3", "U2", "U1"]
RGBA = K.RGBA
ICE_DISSOLVE = ("U4", "U3", "U2", "N2", "N1")

LAYERS = ["FXBack", "WeaponBack", "BackArm", "BackLeg", "ShellBack", "Body", "FrontLeg", "Head", "Shell", "Weapon",
          "FrontArm", "ShellArm", "Glow", "FX"]
FXL = {"FXBack", "Glow", "FX"}
SHELLS = ("ShellBack", "Shell", "ShellArm")
# which armour layers sit beneath each shell layer (for the see-through tint)
UNDER = {"ShellBack": ("BackArm", "BackLeg"), "Shell": ("BackArm", "BackLeg", "ShellBack", "Body", "FrontLeg", "Head"),
         "ShellArm": ("FrontArm",)}

# maul geometry, local (u along the haft from the front grip, v across)
M_POMMEL, M_HEAD0, M_HEAD1, M_HALF = -17.0, 25.5, 42.5, 12.5
M_BACK = -9.0          # back hand position along the haft

NEU = dict(P=(59.0, 72.0), C=(61.0, 47.0), Hd=(63.6, 30.0), hup=(0.12, -1), fb=(50.0, FLOOR), ff=(71.0, FLOOR),
           kb=None, kf=None, hf=(84.0, 62.0), hb=None, mang=90.0, maul="hand", wl="Weapon", onehand=False,
           smear=None, flat=None, impact=0, stuck=False, glint=None, eye=1, wind=0.0, dust=0, breath=0,
           shell=1, crack=0.0, burst=0, roar=0, dissolve=0.0, shake=0, rot=0.0, piv=(0, 0), flare=0, stomp=0,
           free=None, pl=None, gu=0.0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


PTS = ("P", "C", "Hd", "fb", "ff", "kb", "kf", "hf", "hb")


def shifted(p, dx=0.0, dy=0.0, keys=PTS):
    q = dict(p)
    for k in keys:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] + dy)
    return q


# =========================================================================== small helpers
def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def facet_poly(L, pts, ridge, mat, bias=0, k=0.78, ao=1, lift=0.0):
    """Faceted crystal plate: fan of triangles from an inner ridge point, each with one flat normal
    (a gem / cut-ice look with crisp lit/shadow facet splits).  pts & ridge in frame coords."""
    m_all = set()
    n = len(pts)
    first = True
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        tri = poly_mask([ridge, a, b])
        tri -= m_all
        if not tri:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        dx, dy = mid[0] - ridge[0], mid[1] - ridge[1]
        l = math.hypot(dx, dy) or 1.0
        nrm = norm3(dx / l * k, dy / l * k - lift, 1 - k * 0.45)
        L.paint({q: nrm for q in tri}, mat, bias, ao=ao if first else 0)
        first = False
        m_all |= tri
    # facet ridges (ridge -> vertex): lit ones get a bright edge in see_through, shadow ones a dark one
    if not hasattr(L, "edges"):
        L.edges = {}
    for i, v in enumerate(pts):
        dx, dy = v[0] - ridge[0], v[1] - ridge[1]
        l = math.hypot(dx, dy) or 1.0
        lit = (dx * K.LIGHT[0] + dy * K.LIGHT[1]) / l
        if abs(lit) < 0.25 or hash01(i, int(ridge[0]), 13) < 0.25:
            continue
        seg = line(ridge, v)[1:-1]
        for q in seg[: max(1, int(len(seg) * 0.8))]:
            L.edges[q] = 1 if lit > 0 else -1
    return m_all


def crystal(L, base, ang, length, w, mat="N", bias=0, ao=0):
    """Faceted ice shard (frame coords): two triangles with opposite tilts -> crisp lit/shadow split."""
    d = dirv(ang)
    pv = (-d[1], d[0])
    tip = add(base, (d[0] * length, d[1] * length))
    lft, rgt = add(base, (pv[0] * w, pv[1] * w)), add(base, (-pv[0] * w, -pv[1] * w))
    back = add(base, (-d[0] * 0.8, -d[1] * 0.8))
    m1 = poly_mask([lft, tip, back])
    m2 = poly_mask([back, tip, rgt]) - m1
    # the facet facing the light gets the bright tilt
    s = pv[0] * K.LIGHT[0] + pv[1] * K.LIGHT[1]
    t1, t2 = ((-0.45, -0.5), (0.6, 0.4)) if s < 0 else ((0.6, 0.4), (-0.45, -0.5))
    L.paint({q: norm3(t1[0], t1[1], 0.75) for q in m1}, mat, bias, ao=ao)
    L.paint({q: norm3(t2[0], t2[1], 0.75) for q in m2}, mat, bias, ao=0)
    return m1 | m2, tip


def icicle(L, base, length, w=1.2, mat="N"):
    """Hanging icicle (always points straight down in the frame)."""
    return crystal(L, base, 90 + (hash01(int(base[0]), int(base[1]), 3) - 0.5) * 10, length, w, mat, 0)[0]


def crack(L, start, ang, length, seed, core, glow=None, branch=True, only=None, step=1.5, jit=95):
    """Jagged crack decal in frame coords (random walk); returns the pixels."""
    pts = [start]
    a = ang
    x, y = start
    n = int(length / step)
    for i in range(n):
        a += (hash01(i, seed, 71) - 0.5) * jit
        x += math.cos(math.radians(a)) * step
        y += math.sin(math.radians(a)) * step
        pts.append((x, y))
    px = polyline(pts)
    px = [q for q in px if q in L.px and (only is None or L.px[q][0] in only)]
    if glow:
        L.decal([(q[0] + 1, q[1]) for q in px if (q[0] + 1, q[1]) in L.px and (only is None or L.px[(q[0] + 1, q[1])][0] in only)], glow)
    L.decal(px, core)
    out = list(px)
    if branch and n > 3:
        mid = pts[n // 2]
        out += crack(L, mid, ang + (50 if hash01(seed, 1, 5) > 0.5 else -50), length * 0.45, seed + 7, core, glow,
                     False, only, step, jit)
    return out


def star(FX, c, core="U4", arm_="U3", big=True):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], core)
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2)) + (((3, 0), (-3, 0), (0, -3), (0, 3), (4, 0), (-4, 0)) if big else ()):
        FX.put([(x + d[0], y + d[1])], arm_)
    if big:
        for d in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            FX.put([(x + d[0], y + d[1])], "U2")


# =========================================================================== the glacier maul
def maul_frame(grip, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def T(u, v):
        return (grip[0] + ca * u - sa * v, grip[1] + sa * u + ca * v)
    return T, ca, sa


def draw_maul(L, grip, ang, phase, fi, info, glint=False):
    """Long iron haft + a massive block of glacier ice bound in iron bands.  Returns the head mask."""
    T, ca, sa = maul_frame(grip, ang)

    def rot_n(nx, ny, nz):
        return norm3(nx * ca - ny * sa, nx * sa + ny * ca, nz)
    # haft
    L.paint(n_capsule(T(M_POMMEL + 1.5, 0), T(M_HEAD0 + 1.0, 0), 1.25, 1.25), "E", 0, ao=0)
    for u0, u1 in ((-2.5, 2.5), (M_BACK - 2.5, M_BACK + 2.5)):          # leather wraps under the hands
        L.paint(n_capsule(T(u0, 0), T(u1, 0), 1.35, 1.35), "X", 0, ao=0)
    for u in (-5.5, 6.0, 15.0):                                         # bronze rings
        L.paint(n_capsule(T(u - 0.5, 0), T(u + 0.5, 0), 1.7, 1.7), "H", 0, ao=0)
    # pommel spike
    pm = poly_mask([T(M_POMMEL + 2.0, -2.0), T(M_POMMEL - 2.4, 0), T(M_POMMEL + 2.0, 2.0)])
    L.paint({q: rot_n(-0.6, -0.2, 0.7) for q in pm}, "E", 0, ao=0)
    # socket / langets
    sk = poly_mask([T(M_HEAD0 - 4.5, -1.8), T(M_HEAD0 + 0.5, -3.4), T(M_HEAD0 + 0.5, 3.4), T(M_HEAD0 - 4.5, 1.8)])
    L.paint({q: rot_n(0, -0.4, 0.8) for q in sk}, "E", 0, ao=0)
    # the ice block: an elongated octagonal prism seen side-on -> three facet bands (top bevel, face, bottom bevel)
    u0, u1, hv = M_HEAD0, M_HEAD1, M_HALF
    ring = [(u0 + 3.0, -hv), (u0 + 8.0, -hv - 0.6), (u1 - 3.0, -hv + 0.2), (u1 + 0.6, -hv + 4.4), (u1 + 3.4, -hv + 7.4),
            (u1 + 1.0, -1.0), (u1 + 4.6, 3.2), (u1 + 0.4, hv - 4.0), (u1 - 3.4, hv), (u0 + 3.4, hv + 0.4), (u0, hv - 5.0),
            (u0 - 0.4, -hv + 5.0)]
    hm = poly_mask([T(*q) for q in ring])
    head = {}
    for q in hm:
        # local coords of the pixel
        dx, dy = q[0] + .5 - grip[0], q[1] + .5 - grip[1]
        u = dx * ca + dy * sa
        v = -dx * sa + dy * ca
        # hexagonal prism: two bevel planes toward each striking face, a ridge along the middle
        fu = (u - (u0 + u1) / 2) / ((u1 - u0) / 2)
        if abs(v) > hv - 4.6 + abs(fu) * 1.5:
            nl = (fu * 0.35, 0.75 if v > 0 else -0.75)
        else:
            nl = (0.62 if fu > 0.05 else -0.5, 0.0)
        head[q] = rot_n(nl[0], nl[1], 0.72)
    L.paint(head, "N", 0, ao=1)
    # thick-ice core: deep glacier colour away from the rims
    df = dist_field(hm)
    for q in hm:
        if df.get(q, 0) > 3.4 and q in L.px:
            L.px[q][0] = "Z"
    # iron face plates on both striking faces
    for sgn in (-1, 1):
        fp = poly_mask([T(u0 + 3.0, sgn * (hv + 0.6)), T(u1 - 3.0, sgn * (hv + 0.6)), T(u1 - 3.6, sgn * (hv - 1.4)),
                        T(u0 + 3.6, sgn * (hv - 1.4))])
        L.paint({q: rot_n(0, 0.8 * sgn, 0.6) for q in fp}, "E", 0, ao=1)
    # iron bands
    for ub in (u0 + 3.6, u1 - 3.2):
        band = poly_mask([T(ub - 1.1, -hv - 1.0), T(ub + 1.1, -hv - 1.0), T(ub + 1.1, hv + 1.0), T(ub - 1.1, hv + 1.0)])
        L.paint({q: head.get(q, rot_n(0, 0, 1)) for q in band}, "E", 0, ao=1)
        for vv in (-hv + 1.0, 0.0, hv - 1.0):                            # rivets
            L.decal([ip(T(ub, vv))], ("H", 4))
    # facet glints along the lit rim + a sliver of refraction
    L.decal(line(T(u0 + 5.4, -hv + 0.4), T(u1 - 5.0, -hv + 0.4)), ("N", 4), only_on=("N", "Z"))
    L.decal(line(T(u0 + 6.0, -2.0), T(u0 + 8.4, 3.0)), ("N", 3), only_on=("Z",))
    L.decal(line(T(u1 - 6.0, -4.0), T(u1 - 4.8, -1.0)), ("N", 3), only_on=("Z",))
    # jagged crystal points growing out of the block's ends
    tips = []
    for (uu, vv, aa, ll, ww) in ((u1 + 1.8, -hv + 7.2, -8, 5.0, 1.6), (u1 + 3.4, 3.0, 16, 3.4, 1.3),
                                 (u0 + 5.0, hv + 0.4, 100, 3.0, 1.2), (u0 + 9.0, -hv - 0.4, -96, 3.6, 1.3)):
        base = T(uu, vv)
        a2 = ang + aa
        m, tip = crystal(L, base, a2, ll, ww, "N", 0)
        tips.append(tip)
        hm |= m
    if phase == 2:
        # cracked with blue light
        c0 = T(u0 + 7.5, -1.0)
        crack(L, c0, ang + 70, 12, 11 + fi % 2, ("U", 3), ("U", 1), True, only=("N", "Z"))
        crack(L, T(u1 - 5.5, 3.0), ang - 100, 8, 23, ("U", 2), None, False, only=("N", "Z"))
    hm = {q for q in hm if q[1] <= FLOOR}
    info["head"] = hm
    info["head_c"] = T((u0 + u1) / 2, 0)
    info["face"] = T((u0 + u1) / 2, hv)
    info["head_top"] = T(u1 - 3.0, -hv)
    info["tips"] = tips
    return hm


# =========================================================================== ice shell pieces
def shell_torso(L, F, ln, fi, crack_amt, bang):
    pts = [F(-6.4, 0.6), F(-8.8, -ln * 0.45), F(-11.4, -ln + 3.0), F(-8.4, -ln - 2.6), F(-1.6, -ln - 4.4),
           F(5.4, -ln - 2.8), F(11.2, -ln + 4.0), F(9.4, -ln * 0.5), F(5.6, -ln * 0.3), F(5.8, 0.6)]
    m = facet_poly(L, pts, F(3.0, -ln * 0.66), "N", 0)
    # a second, lower plate (abdomen / hip ice), separated by a dark seam
    m |= facet_poly(L, [F(-7.0, 1.0), F(-7.0, -ln * 0.3), F(-0.4, -ln * 0.36), F(6.6, -ln * 0.26), F(7.6, 2.6),
                        F(3.4, 6.4), F(-5.0, 5.4)], F(1.0, -ln * 0.06), "N", 0)
    # ice mantle: two long blades swept back off the upper back
    for (a, b, ang, l, w) in ((-9.6, -ln + 2.4, -160, 13.0, 2.4),):
        mm, _ = crystal(L, F(a, b), ang + bang, l, w, "N", 0, ao=1)
        m |= mm
    return m


def shell_limb(L, a, b, ra, rb, ridge_t=0.45, spike=None, mat="N"):
    """Angular ice sleeve around a limb segment a->b (frame coords)."""
    d = sub(b, a)
    l = math.hypot(*d) or 1.0
    u = (d[0] / l, d[1] / l)
    v = (-u[1], u[0])
    pts = [add(a, (v[0] * ra * 0.7 - u[0] * 1.5, v[1] * ra * 0.7 - u[1] * 1.5)),
           add(a, (v[0] * ra, v[1] * ra)), add(lerp(a, b, 0.55), (v[0] * (ra + rb) * 0.55, v[1] * (ra + rb) * 0.55)),
           add(b, (v[0] * rb, v[1] * rb)), add(b, (u[0] * 1.2, u[1] * 1.2)),
           add(b, (-v[0] * rb, -v[1] * rb)), add(lerp(a, b, 0.5), (-v[0] * (ra + rb) * 0.52, -v[1] * (ra + rb) * 0.52)),
           add(a, (-v[0] * ra, -v[1] * ra))]
    ridge = add(lerp(a, b, ridge_t), (v[0] * 0.8, v[1] * 0.8))
    m = facet_poly(L, pts, ridge, mat, 0)
    return m


def shell_detail(L, mask_all):
    """Thick ice gets the deep glacier ramp away from the rims; faint internal fracture planes."""
    df = dist_field(mask_all)
    for q in mask_all:
        e = L.px.get(q)
        if e is None or e[0] != "N" or e[3] is not None:
            continue
        d = df.get(q, 0)
        if d > 2.2 + 1.2 * hash01(q[0] // 3, q[1] // 3, 5):
            e[0] = "Z"


def see_through(L, under_img):
    """Translucent ice: over armour the ice takes the deep glacier ramp and its value is a blend of the facet
    shading and the armour beneath (so the dark plates, seams and trim read faintly through it); the outer rim
    and ice over nothing stay thin and pale; lit facet ridges get a bright edge, shadow ridges a dark one."""
    up = under_img.load()
    df = dist_field(set(q for q, e in L.px.items() if e[0] is not None))
    edges = getattr(L, "edges", {})
    for q, e in L.px.items():
        if e[0] is None or isinstance(e[3], str) or e[0] == "U":
            continue
        fl = K.level_of(e, *q)
        r, g, b, a = up[q]
        d = df.get(q, 1.0)
        if a == 0:
            e[0] = "N"
            lvl = min(5, max(2, fl))
        else:
            lum = 0.3 * r + 0.55 * g + 0.15 * b
            al = max(0.0, min(5.0, (lum - 10) / 18.0))
            lvl = int(round(0.62 * fl + 0.45 * al - 0.2))
            e[0] = "Z"
            if d <= 1.2:
                lvl += 1
        ed = edges.get(q)
        if ed is not None:
            if ed > 0:
                e[0] = "N"
                lvl = min(5, max(lvl + 2, 4))
            else:
                lvl = max(0, lvl - 1)
        e[3] = ("LVL", max(0, min(5, lvl)))


# =========================================================================== the warden
def draw(p, fi, sw, phase):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, GL, FXB = FXLayer("FX"), FXLayer("Glow"), FXLayer("FXBack")
    Ls["FX"], Ls["Glow"], Ls["FXBack"] = FX, GL, FXB
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    shF, shB = F(3.0, -ln + 3.4), F(-5.2, -ln + 3.8)
    hB, hF = F(-4.2, 1.8), F(4.4, 1.8)
    info = {"hit": set(), "smear": set()}
    bare = phase == 2 or p["burst"] >= 1          # shell gone (p2, or p1 after it explodes)
    shell_on = phase == 1 and p["shell"] and not bare

    # ---------------- maul
    if p["maul"] == "hand":
        grip, mang = R.T(p["hf"]), R.A(p["mang"])
        if p["gu"]:                                   # the hand holds the haft at u = gu (e.g. near the pommel)
            ca_, sa_ = dirv(mang)
            grip = (grip[0] - ca_ * p["gu"], grip[1] - sa_ * p["gu"])
    else:
        grip, mang = p["maul"]
    hm = draw_maul(Ls[p["wl"]], grip, mang, 2 if bare else 1, fi, info, p["glint"])
    info["hit"] |= hm
    info["grip"] = grip
    T, ca, sa = maul_frame(grip, mang)
    hand2 = T(M_BACK, 0)
    info["hand2"] = hand2

    # ---------------- back arm (holds the haft lower down unless one-handed)
    hbk = p["hb"] or (hand2 if not p["onehand"] else F(-5.0, -3.0))
    Ba = Ls["BackArm"]
    elb = arm(R, Ba, shB, hbk, 15.0, 15.0, 3.6, 3.2, "E", bias=-1, fist="E", fist_r=2.9, pref=(-1, 0.55),
              fore="J")
    R.cap(Ba, lerp(elb, hbk, 0.5), hbk, 3.5, 3.2, "E", -1, ao=0)                      # gauntlet
    bp = R.plate(Ba, [add(shB, (-7.5, -1.0)), add(shB, (-4.0, -6.5)), add(shB, (4.0, -5.2)), add(shB, (5.5, 1.0)),
                      add(shB, (1.0, 5.5)), add(shB, (-6.0, 4.0))], "E", bevel=2.2, tilt=(-0.1, -0.2), bias=-1)
    info["elb"] = elb

    # ---------------- legs: basalt thighs, blue-black greaves, pointed sabatons
    knees = {}
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        Lg = Ls[nm]
        k = leg(R, Lg, hip, ft, 19.6, 19.6, 4.5, 3.4, "J", bias=bias, flen=8.0, heel=3.6, boot_h=5.0, knee=kn,
                boot="E", pref=(1, -0.1))
        ank = (ft[0], ft[1] - 1.4)
        # greave: angular plate on the shin front
        d = sub(ank, k)
        l = math.hypot(*d) or 1
        u = (d[0] / l, d[1] / l)
        v = (-u[1], u[0])
        if v[0] < 0:
            v = (-v[0], -v[1])
        gv = [add(k, (v[0] * 4.0, v[1] * 4.0)), add(lerp(k, ank, 0.9), (v[0] * 3.0, v[1] * 3.0)),
              add(lerp(k, ank, 0.9), (-v[0] * 2.6, -v[1] * 2.6)), add(lerp(k, ank, 0.2), (-v[0] * 3.4, -v[1] * 3.4))]
        Lg.paint(n_plate(poly_mask(gv), 1.8, (0.1, 0.0), 1.2), "E", bias, ao=1)
        # cuisse: a long angular plate down the front of the thigh
        dth = sub(k, hip)
        lt = math.hypot(*dth) or 1
        ut = (dth[0] / lt, dth[1] / lt)
        vt = (-ut[1], ut[0])
        if vt[0] < 0:
            vt = (-vt[0], -vt[1])
        cu = [add(lerp(hip, k, 0.08), (vt[0] * 4.4, vt[1] * 4.4)), add(lerp(hip, k, 0.82), (vt[0] * 3.8, vt[1] * 3.8)),
              add(lerp(hip, k, 0.9), (-vt[0] * 0.6, -vt[1] * 0.6)), add(lerp(hip, k, 0.1), (-vt[0] * 1.2, -vt[1] * 1.2))]
        Lg.paint(n_plate(poly_mask(cu), 1.6, (-0.15, -0.1), 1.2), "E", bias, ao=1)
        # knee cop: pointed, angular
        kc = [add(k, (-3.2, -3.6)), add(k, (3.0, -3.8)), add(k, (5.8, 0.4)), add(k, (2.4, 4.0)), add(k, (-3.0, 3.0))]
        Lg.paint(n_plate(poly_mask(kc), 1.6, (-0.1, -0.2), 1.3), "E", bias, ao=1)
        Lg.decal([ip(add(k, (1.4, -0.4)))], ("H", 4 + bias))
        Lg.decal(line(add(k, (-2.4, 3.4)), add(k, (4.0, 1.2))), ("H", 2 + bias))
        knees[nm] = k
        info["knee_" + nm] = k

    # ---------------- torso
    Bd = Ls["Body"]
    faulds = [F(-7.2, -2.4), F(6.4, -2.4), F(7.4, 5.4), F(-7.8, 5.8)]
    R.plate(Bd, faulds, "J", bevel=1.8, tilt=(0.0, 0.2), bias=-1)
    for kk in range(2):
        R.dline(Bd, F(-7.4, 0.2 + kk * 2.8), F(6.8, 0.2 + kk * 2.8), ("J", 1))
    # long front tasset (sleek, narrow)
    tsw = -sw * 0.5 + p["wind"] * 0.3
    R.plate(Bd, [F(0.8, 2.0), F(6.2, 2.0), F(5.4 - tsw * 0.4, 15.0), F(3.2 - tsw * 0.5, 17.6), F(1.2 - tsw * 0.4, 14.6)],
            "E", bevel=1.4, tilt=(-0.1, 0.05), bias=0)
    R.dline(Bd, F(1.4, 2.4), F(1.6 - tsw * 0.4, 14.2), ("H", 2))
    torso = [F(-4.8, -1.0), F(-6.6, -ln * 0.45), F(-10.0, -ln + 3.0), F(-7.6, -ln - 1.6), F(-1.0, -ln - 3.0),
             F(6.0, -ln - 1.8), F(10.2, -ln + 4.4), F(8.4, -ln * 0.52), F(4.8, -ln * 0.28), F(4.2, -1.0)]
    tm = R.plate(Bd, torso, "E", bevel=3.4, tilt=(-0.35, -0.15), strength=1.35)
    info["torso"] = tm
    # abdomen lames in basalt, narrow waist
    for kk in range(3):
        b = -ln * 0.3 + kk * 3.0
        lm = [F(-6.0, b - 1.2), F(5.2, b - 1.4), F(5.0 - kk * 0.2, b + 1.4), F(-5.8, b + 1.4)]
        R.plate(Bd, lm, "J", bevel=1.2, tilt=(-0.2, -0.1), bias=0)
    R.dline(Bd, F(3.0, -ln - 1.6), F(4.4, -ln * 0.45), ("E", 5))            # keel ridge
    R.dline(Bd, F(3.8, -ln - 1.2), F(5.0, -ln * 0.45), ("E", 2))
    R.dline(Bd, F(-6.6, -ln - 0.6), F(5.0, -ln - 1.4), ("H", 3))            # collar trim
    R.dline(Bd, F(-5.6, -1.4), F(4.8, -1.4), ("H", 2))                      # waist trim
    R.dline(Bd, F(-8.4, -ln + 4.0), F(-6.4, -ln * 0.45), ("E", 1))          # back plate seam
    # gorget + neck
    G = basis(Hd, p["hup"])
    R.cap(Bd, F(0.4, -ln - 1.0), G(-0.4, 5.0), 3.6, 3.0, "E", bias=-1)

    # ---------------- head: small narrow helm, single cold visor slit, swept crest
    Hl = Ls["Head"]
    helm = [G(-3.6, 4.4), G(-4.2, -0.6), G(-3.0, -4.6), G(0.0, -5.8), G(2.6, -4.6), G(4.6, -2.2), G(6.8, 0.2),
            G(4.2, 2.8), G(2.0, 5.2), G(-0.6, 5.6)]
    hmask = R.plate(Hl, helm, "E", bevel=2.2, tilt=(-0.3, -0.2), strength=1.3)
    info["headmask"] = hmask
    # crest fin sweeping back
    fin = [G(0.4, -5.4), G(-2.4, -6.8), G(-10.6, -6.6), G(-3.6, -4.6)]
    R.plate(Hl, fin, "E", bevel=0.8, tilt=(-0.2, -0.5), strength=0.8)
    R.dline(Hl, G(-0.4, -5.8), G(-9.0, -5.4), ("H", 3))
    R.dline(Hl, G(0.4, -5.6), G(4.6, -1.6), ("E", 5))                        # comb ridge
    R.dline(Hl, G(-3.0, 1.6), G(0.4, 5.0), ("E", 2))                         # cheek plate seam
    R.dline(Hl, G(4.0, 1.2), G(6.0, 0.6), ("E", 1))                          # snout underside
    slit = R.dline(Hl, G(0.8, -1.4), G(5.6, -0.4), "OUT")
    info["visor"] = R.T(G(4.6, -0.6))
    if p["eye"]:
        vis = [q for q in line(R.T(G(1.6, -1.2)), R.T(G(5.4, -0.4)))]
        hot = "U4" if (p["eye"] == 2 or bare) else "U3"
        FX.put(vis, "U3" if not bare else "U2")
        FX.put(vis[-2:], hot)
        if p["eye"] == 2:
            e = ip(info["visor"])
            FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1]), (e[0], e[1] - 1), (e[0], e[1] + 1)], "U3")
            FX.put([e], "U4")

    # ---------------- near arm + pauldron
    Fa = Ls["FrontArm"]
    hfr = (R.T(p["hf"]) if p["gu"] else grip) if p["maul"] == "hand" else (p["hf"] if p["hf"] else F(6.0, -3.0))
    if p["free"]:
        hfr = p["free"]
    el = arm(R, Fa, shF, hfr, 15.0, 15.0, 3.8, 3.4, "E", bias=0, fist="E", fist_r=3.0, pref=(-1, 0.7), fore="J")
    R.cap(Fa, lerp(el, hfr, 0.45), hfr, 3.7, 3.3, "E", 0, ao=0)             # gauntlet
    R.dline(Fa, lerp(el, hfr, 0.45), lerp(el, hfr, 0.47), ("H", 3))
    R.dome(Fa, el, 3.4, 3.2, "E", 0)                                         # couter
    info["elf"] = el
    info["handf"] = hfr
    paul = [add(shF, (-8.4, -2.4)), add(shF, (-4.6, -7.4)), add(shF, (2.6, -7.8)), add(shF, (7.4, -3.4)),
            add(shF, (7.0, 2.2)), add(shF, (2.4, 5.6)), add(shF, (-5.4, 4.6))]
    pm = R.plate(Fa, paul, "E", bevel=2.6, tilt=(-0.15, -0.25), strength=1.3)
    lame = [add(shF, (-5.8, 3.4)), add(shF, (5.6, 1.8)), add(shF, (6.2, 5.2)), add(shF, (0.6, 8.2)), add(shF, (-4.6, 6.8))]
    pm |= R.plate(Fa, lame, "E", bevel=1.6, tilt=(0.0, 0.1), strength=1.2)
    R.dline(Fa, add(shF, (-7.6, -2.2)), add(shF, (2.4, -7.2)), ("E", 5))       # ridge
    R.dline(Fa, add(shF, (-5.0, 4.4)), add(shF, (6.6, 2.0)), ("H", 3))         # bronze rim
    info["pauldron"] = pm

    # ---------------- ice shell (phase 1)
    info["shell_pts"] = []
    if shell_on:
        S, SB, SA = Ls["Shell"], Ls["ShellBack"], Ls["ShellArm"]
        bang = math.degrees(math.atan2(upv[1], upv[0])) + 90
        hang = math.degrees(math.atan2(p["hup"][1], p["hup"][0])) + 90
        # back leg & back arm sleeves
        mb = set()
        mb |= shell_limb(SB, hB, knees["BackLeg"], 5.6, 4.8)
        mb |= shell_limb(SB, knees["BackLeg"], lerp(knees["BackLeg"], p["fb"], 0.7), 4.6, 3.8)
        mb |= shell_limb(SB, lerp(elb, hbk, 0.15), lerp(elb, hbk, 0.74), 4.0, 3.5)
        mb |= facet_poly(SB, [add(shB, (-9.0, -1.0)), add(shB, (-5.0, -8.6)), add(shB, (3.6, -7.2)), add(shB, (6.0, 1.6)),
                              add(shB, (-6.0, 5.4))], add(shB, (-1.0, -2.0)), "N")
        # torso, front leg, helm cowl
        ms = shell_torso(S, F, ln, fi, p["crack"], bang)
        kf_ = knees["FrontLeg"]
        ms |= shell_limb(S, hF, kf_, 5.8, 5.0)
        ms |= shell_limb(S, kf_, lerp(kf_, p["ff"], 0.72), 4.8, 3.9)
        m, _ = crystal(S, add(kf_, (1.4, -1.4)), -28, 5.0, 1.7, "N", 0, ao=1)          # knee spike
        ms |= m
        cowl = [G(-5.6, 5.0), G(-6.2, -1.8), G(-4.6, -6.4), G(-0.6, -8.0), G(3.0, -6.4), G(4.6, -3.6), G(1.0, -3.4),
                G(-1.4, 0.2), G(-1.6, 5.4)]
        ms |= facet_poly(S, [R.T(q) for q in cowl], R.T(G(-2.4, -3.0)), "N")
        for (a_, b_, ang, l, w) in ((-3.0, -6.8, -166, 12.0, 1.8), (0.6, -7.2, -150, 5.0, 1.3)):   # crown shards
            m, _ = crystal(S, R.T(G(a_, b_)), R.A(ang + hang), l, w, "N", 0, ao=1)
            ms |= m
        # front upper arm + forearm bracer + pauldron crown (over the arm)
        ma = set()
        ma |= shell_limb(SA, lerp(el, hfr, 0.12), lerp(el, hfr, 0.74), 4.3, 3.7)
        ma |= shell_limb(SA, lerp(shF, el, 0.45), lerp(shF, el, 0.9), 4.2, 3.8)
        ma |= facet_poly(SA, [add(shF, (-10.4, -2.0)), add(shF, (-6.0, -9.8)), add(shF, (3.6, -10.2)), add(shF, (9.6, -4.0)),
                              add(shF, (8.8, 3.4)), add(shF, (1.6, 7.8)), add(shF, (-6.8, 6.0))], add(shF, (-0.4, -3.4)), "N")
        for (dx, dy, ang, l, w) in ((-4.4, -8.8, -142, 16.0, 2.8), (3.6, -8.6, -112, 7.0, 1.9)):
            m, _ = crystal(SA, add(shF, (dx, dy)), ang + bang, l, w, "N", 0, ao=1)
            ma |= m
        # icicles under the pauldron and the forearms
        ic = set()
        for k, dx in enumerate((-4.6, -0.6, 4.2)):
            ic |= icicle(SA, add(shF, (dx, 7.4 - abs(dx) * 0.3)), 3.0 + 3.5 * hash01(k, 1, 9), 1.1)
        q = lerp(el, hfr, 0.4)
        ic |= icicle(SA, (q[0], q[1] + 3.8), 4.0, 1.0)
        q = lerp(elb, hbk, 0.45)
        icicle(SB, (q[0], q[1] + 3.6), 3.5, 1.0)
        info["shell_mask"] = ms | ma | mb
        # glowing fracture lines (shatter build-up)
        if p["crack"] > 0:
            c = p["crack"]
            ln_ = 6 + 24 * c
            for L_, seeds in ((S, ((F(2.0, -ln * 0.6), -60), (F(2.0, -ln * 0.6), 130), (F(-3.0, -ln + 2), 200),
                                   (F(1.0, -ln * 0.2), 30))),
                              (SA, ((add(shF, (0, -3)), -20), (add(shF, (0, -3)), 150), (lerp(el, hfr, 0.4), 60))),
                              (SB, ((add(shB, (-1, -2)), 200), (lerp(hB, knees["BackLeg"], 0.5), 100)))):
                for k, (st, ang) in enumerate(seeds):
                    crack(L_, st, ang, ln_ * (0.6 if L_ is not S else 1.0), 40 + k * 13 + int(c * 3), ("U", 3 if c > 0.5 else 2),
                          ("U", 1) if c > 0.3 else None, True, only=("N", "Z"))
            if c >= 0.6:
                for k in range(int(4 + 10 * c)):
                    a = hash01(k, 3, 61) * 6.283
                    r = 14 + hash01(k, 4, 61) * 18
                    q = ip(add(lerp(P, C, 0.6), (math.cos(a) * r, math.sin(a) * r * 1.2)))
                    if q[1] < FLOOR:
                        FX.put([q], "U3" if k % 3 == 0 else "U2")

    # ---------------- phase 2 / bare: cracked plates, frost light from the seams, glowing core, ice stubs
    if bare:
        corec = F(-4.0, -ln + 10.0)
        info["core"] = corec
        glow = 1 + (1 if p["flare"] else 0)
        for L_, seeds in ((Bd, ((corec, -70), (corec, 150), (corec, 40), (F(-5.0, -ln + 4.0), 100))),
                          (Fa, ((add(shF, (-1.0, -2.0)), -10), (add(shF, (-3.0, 1.0)), 160))),
                          (Ls["FrontLeg"], ((lerp(hF, knees["FrontLeg"], 0.3), 80),)),
                          (Hl, ((R.T(G(-2.0, -4.0)), 60),))):
            for k, (st, ang) in enumerate(seeds):
                crack(L_, st, ang, 8 if L_ is Bd else 6, 70 + k * 7, ("U", 2 + (1 if p["flare"] else 0)),
                      ("U", 0), L_ is Bd, only=("E", "J"))
        # the core
        cc = ip(corec)
        core = mask_disc(corec, 3.0)
        Bd.fill(core, "U1")
        Bd.fill(mask_disc(corec, 2.2), "U2")
        Bd.fill(mask_disc(corec, 1.3), "U3")
        Bd.decal([cc], "U4")
        rr = 4 + 2 * glow
        for k in range(8):
            a = k * 0.785 + fi * 0.3
            q0 = add(corec, (math.cos(a) * 3.6, math.sin(a) * 3.6))
            q1 = add(corec, (math.cos(a) * rr, math.sin(a) * rr))
            if k % 2 == 0 or p["flare"]:
                GL.put(line(q0, q1), "U2" if k % 2 == 0 else "U1")
        # jagged ice stubs still clinging
        Sa = Ls["FrontArm"]
        for (dx, dy, ang, l, w) in ((-5.0, -5.6, -130, 5.0, 1.8), (-1.0, -7.0, -105, 6.0, 1.8), (3.8, -5.6, -70, 3.4, 1.4)):
            crystal(Sa, add(shF, (dx, dy)), ang, l, w, "N", 0, ao=1)
        crystal(Sa, lerp(el, hfr, 0.35), R.A(-100) if False else -120, 3.6, 1.4, "N", 0, ao=1)
        crystal(Ls["BackArm"], add(shB, (-3.0, -5.4)), -130, 5.0, 1.6, "N", -1, ao=1)
        crystal(Ls["FrontLeg"], add(knees["FrontLeg"], (1.0, -1.0)), -40, 4.0, 1.6, "N", 0, ao=1)
        icicle(Sa, (lerp(el, hfr, 0.5)[0], lerp(el, hfr, 0.5)[1] + 3.8), 3.0, 0.9)
        # frost light leaking from the seams (flat glow, no outline)
        if p["flare"]:
            fl = p["flare"]
            for k in range(10 + 6 * fl):
                a = hash01(k, 5, 62) * 6.283
                r = 10 + hash01(k, 6, 62) * (10 + 8 * fl)
                q = ip(add(corec, (math.cos(a) * r, math.sin(a) * r * 1.1)))
                if q[1] < FLOOR:
                    FX.put([q], "U3" if k % 3 == 0 else "U2")
            for k in range(12):
                a = k * 0.5236 + 0.2
                q0 = add(corec, (math.cos(a) * (8 + fl), math.sin(a) * (8 + fl)))
                q1 = add(corec, (math.cos(a) * (13 + 4 * fl), math.sin(a) * (13 + 4 * fl)))
                if k % 2 == 0:
                    FXB.put([q for q in line(q0, q1) if q[1] < FLOOR], "U2" if fl > 1 else "U1")

    # ---------------- shell explosion (p1 shatter frames)
    if phase == 1 and 1 <= p["burst"] <= 3:
        shatter_burst(FX, FXB, lerp(P, C, 0.55), p["burst"], fi)

    # ---------------- breath vapour from the visor slit
    if p["breath"]:
        v0 = info["visor"]
        for k in range(5):
            ph = ((fi * 0.23 + k * 0.2) % 1.0)
            if ph > 0.8:
                continue
            q = ip((v0[0] + 2 + ph * 9 + math.sin(k * 2.1 + ph * 5) * 1.2, v0[1] + 1 - ph * 7))
            FX.put([q], "N4" if ph < 0.3 else "N3" if ph < 0.55 else "N2")
            if ph < 0.4:
                FX.put([(q[0] + 1, q[1])], "N3")

    # ---------------- smears / impact / fx
    pal = "ice" if not bare else "ice2"
    if p["smear"]:
        sm = p["smear"]
        hot = maul_smear(FX, sm["g0"], sm["a0"], grip, mang, mid=sm.get("mid"), start=sm.get("start", 0.0), pal=pal,
                         exclude=hm, fade=sm.get("fade", 0.0))
        info["hit"] |= hot
        info["smear"] |= hot
    if p["flat"]:
        hot = flat_arc(FX, p["flat"], pal, exclude=hm, back=FXB)
        info["hit"] |= hot
        info["smear"] |= hot
    if p["impact"]:
        impact(FX, FXB, info, info["face"] if p["impact"] < 3 else info["head_c"], p["impact"], bare, fi)
    if p["stomp"]:
        stomp_fx(FX, FXB, info, p["ff"], p["stomp"], bare)
    if p["stuck"]:
        # frost crust around the maul head buried in the floor
        hx = int(info["head_c"][0])
        for dx in range(-14, 15):
            if hash01(dx, 4, 55) < 0.8:
                FX.put([(hx + dx, FLOOR)], "N3" if abs(dx) < 9 else "N2")
            if abs(dx) < 11 and hash01(dx, 5, 55) < 0.35:
                FX.put([(hx + dx, FLOOR - 1)], "N2")
    if p["dust"]:
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(7):
                x = int(fx_[0] + fx_[1] * (2 + k * 1.6) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (2 + k * 0.6))
                FX.put([(x, y)], ("N3", "N2", "Z4")[k % 3])
    if p["glint"]:
        g = p["glint"]
        c = info["head_top"] if g is True else (info["tips"][0] if g == "tip" else g)
        star(FX, c)
        info["glint_at"] = c
    return Ls, info


def maul_smear(fx, g0, a0, g1, a1, mid=None, start=0.0, pal="ice", exclude=(), fade=0.0):
    """Arc smear the width of the maul head: union of head placements between two (grip, angle) poses."""
    cols = K.SMEAR[pal]
    arc = abs(a1 - a0) * math.pi / 180 * M_HEAD1 + math.hypot(g1[0] - g0[0], g1[1] - g0[1])
    n = max(10, int(arc * (1 - start) / 0.8))
    best = {}
    for i in range(n + 1):
        t = start + (1 - start) * i / n
        gp = lerp(lerp(g0, mid, t), lerp(mid, g1, t), t) if mid else lerp(g0, g1, t)
        a = a0 + (a1 - a0) * t
        age = 1 - (t - start) / max(1e-6, 1 - start)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        u = M_HEAD0 - 4 + age * 6
        while u <= M_HEAD1 + 0.5:
            v = -M_HALF
            while v <= M_HALF:
                q = ip((gp[0] + ca * u - sa * v, gp[1] + sa * u + ca * v))
                ed = M_HEAD1 + 1.0 - u                  # distance from the outer rim of the arc
                if q not in best or best[q][0] > age:
                    best[q] = (age, ed, u)
                v += 1.0
            u += 1.0
    hot = set()
    for q, (age, ed, u) in best.items():
        if q in exclude or not K.inb(*q) or q[1] > FLOOR:
            continue
        thick = (M_HEAD1 - M_HEAD0 + 4) * (1 - age * 0.75) + 1.0
        if ed > thick or age > 0.9:
            continue
        if age > 0.45 and ed > 2 and int(ed / 2 + age * 7) % 3 == 0:
            continue                                     # streak gaps in the old part of the arc
        if fade and hash01(q[0], q[1], 78) < fade:
            continue
        if ed < 1.6:
            c = cols[0] if age < 0.5 else cols[1]
        elif ed < thick * 0.45:
            c = cols[1] if age < 0.35 else cols[2]
        else:
            c = cols[2] if age < 0.3 else cols[3]
        fx.put([q], c)
        if age < 0.7:
            hot.add(q)
    return hot


def flat_arc(FX, spec, pal, exclude=(), back=None):
    """Horizontal sweep seen side-on: a flattened crescent in front of the body (copied from gen_kalden).
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
            t = (th - th0) / (th1 - th0) if th1 != th0 else 0
            if not (0 <= t <= 1):
                continue
            thick = wd * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - fade * 0.6)
            grad = math.hypot(ux / rx, uy / ry) / d
            dd = (1 - d) / max(grad, 1e-6)
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


def ice_spikes(FX, x, n, spread, hmax, seed, cols=("U4", "N4", "N3", "N2")):
    """Short jagged ice shards jutting from the floor around x (flat colours, crisp facets)."""
    pts = set()
    for k in range(n):
        bx = x + (hash01(k, seed, 1) - 0.5) * 2 * spread
        h = hmax * (0.35 + 0.65 * hash01(k, seed, 2)) * (1 - abs(bx - x) / (spread * 1.4))
        if h < 2:
            continue
        lean = (hash01(k, seed, 3) - 0.5) * 0.8 + (0.35 if bx > x else -0.35)
        w = 1.0 + h * 0.18
        for yy in range(int(h) + 1):
            t = yy / max(1.0, h)
            half = w * (1 - t)
            cx = bx + lean * yy
            for xx in range(int(cx - half - 1), int(cx + half + 2)):
                if abs(xx + .5 - cx) <= half + 0.2:
                    q = (xx, FLOOR - yy)
                    lit = xx + .5 < cx
                    c = cols[0] if (t > 0.75 or (lit and abs(xx + .5 - cx) > half - 1)) else cols[1] if lit else cols[2] if t > 0.3 else cols[3]
                    FX.put([q], c)
                    pts.add(q)
    return pts


def impact(FX, FXB, info, face, stage, bare, fi):
    """Maul meets floor: white flash, ice burst (shards + spray), crack running along the floor."""
    ix = int(round(min(max(face[0], 8), W - 8)))
    pts = set()
    if stage == 1:
        pts |= ice_spikes(FX, ix + 4, 11, 16, 17, 7)
        for k in range(22):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 7, 50))
            r = 4 + 16 * hash01(k, 8, 51)
            q = ip((ix + math.cos(a) * r * 1.3, FLOOR - 2 + math.sin(a) * r * 0.9))
            FX.put([q], ("U4", "U3", "N4", "N3")[k % 4])
            if k % 3 == 0:
                FX.put([(q[0] + 1, q[1])], "N3")
            pts.add(q)
        for ang in range(-170, -5, 20):
            FXB.put(line((ix, FLOOR - 1), (ix + math.cos(math.radians(ang)) * 12, FLOOR - 1 + math.sin(math.radians(ang)) * 9)),
                    "U3" if ang % 40 == 0 else "U2")
        for d in ((0, 0), (1, 0), (-1, 0), (0, -1), (2, 0), (-2, 0), (0, -2)):
            FX.put([(ix + d[0], FLOOR - 3 + d[1])], "U4")
    else:
        pts |= ice_spikes(FX, ix + 4, 12, 20, 14, 8, cols=("N5", "N4", "N3", "Z3"))
        for k in range(26):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 9, 52))
            r = 10 + 22 * hash01(k, 10, 53)
            q = ip((ix + math.cos(a) * r * 1.4, FLOOR - 4 + math.sin(a) * r * 0.8 + (r / 12) ** 2 * 3))
            if q[1] <= FLOOR:
                FX.put([q], ("N4", "N3", "U2", "N2")[k % 4])
                pts.add(q)
    # floor crack: dark fissure with frost light, running both ways
    span = 20 if stage == 1 else 30
    for dx in range(-span, span + 1):
        if hash01(dx, 3, 54) < 0.82:
            c = "U4" if abs(dx) < 3 else "U3" if abs(dx) < span * 0.4 else "U2" if abs(dx) < span * 0.7 else "U1"
            FX.put([(ix + dx, FLOOR)], c)
        if abs(dx) < span * 0.6 and hash01(dx, 4, 54) < 0.3:
            FX.put([(ix + dx, FLOOR - 1)], "U1")
    info["hit"] |= {q for q in pts if abs(q[0] - ix) < 22}
    info["impact_x"] = ix


def stomp_fx(FX, FXB, info, foot, stage, bare):
    x = int(foot[0] + 3)
    pts = set()
    if stage == 1:
        pts |= ice_spikes(FX, x + 4, 7, 9, 8, 21)
        for d in range(-16, 17):
            if hash01(d, 1, 56) < 0.85:
                FX.put([(x + d, FLOOR)], "U4" if abs(d) < 3 else "U3" if abs(d) < 9 else "U2")
        for k in range(14):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 2, 56))
            r = 5 + 10 * hash01(k, 3, 56)
            q = ip((x + math.cos(a) * r * 1.3, FLOOR - 1 + math.sin(a) * r * 0.7))
            FX.put([q], ("U3", "N4", "N3")[k % 3])
            pts.add(q)
        # frost cracks radiating along the floor (drawn as low forked lines)
        for s in (-1, 1):
            FXB.put(polyline([(x, FLOOR - 1), (x + s * 6, FLOOR - 2), (x + s * 12, FLOOR - 1), (x + s * 18, FLOOR - 1)]), "U2")
    else:
        pts |= ice_spikes(FX, x + 5, 8, 12, 6, 22, cols=("N5", "N4", "N3", "Z3"))
        for d in range(-22, 23):
            if hash01(d, 5, 56) < 0.7:
                FX.put([(x + d, FLOOR)], "U3" if abs(d) < 6 else "U2" if abs(d) < 14 else "U1")
        for k in range(10):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 6, 56))
            r = 12 + 10 * hash01(k, 7, 56)
            q = ip((x + math.cos(a) * r * 1.3, FLOOR - 2 + math.sin(a) * r * 0.6 + 3))
            if q[1] <= FLOOR:
                FX.put([q], ("N3", "N2")[k % 2])
    # the foot itself + the area around it (the stomp hit is ONLY this, not the maul)
    fx0 = int(foot[0])
    pts |= {(xx, yy) for xx in range(fx0 - 6, fx0 + 13) for yy in range(FLOOR - 16, FLOOR + 1)}
    info["hit"] |= pts
    info["stomp_hit"] = pts
    info["stomp_x"] = x


def shatter_burst(FX, FXB, c, stage, fi):
    """The ice shell exploding off: shards fly outward (6-8), white flash on 6."""
    cx, cy = c
    if stage == 1:
        for r in (8, 13):
            for k in range(28):
                a = k / 28 * 6.283
                q = ip((cx + math.cos(a) * r * 1.2, cy + math.sin(a) * r * 1.3))
                if q[1] <= FLOOR:
                    (FX if r == 8 else FXB).put([q], "U4" if r == 8 else "U3")
        for k in range(10):
            a = k * 0.628 + 0.2
            FXB.put([q for q in line((cx, cy), (cx + math.cos(a) * 30, cy + math.sin(a) * 34)) if q[1] <= FLOOR],
                    "U3" if k % 2 else "U2")
    n = 34
    dist = {1: 18, 2: 30, 3: 42}[stage]
    for k in range(n):
        a = hash01(k, 1, 57) * 6.283
        r = dist * (0.55 + 0.6 * hash01(k, 2, 57))
        x = cx + math.cos(a) * r * 1.35
        y = cy + math.sin(a) * r * 1.1 + (stage - 1) ** 2 * 3.0 * hash01(k, 3, 57)
        if stage == 3:
            y = min(y + 8, FLOOR - 1 - hash01(k, 4, 57) * 3) if y > cy else y + 6
        sz = 1 + int(hash01(k, 5, 57) * 3) - (1 if stage == 3 else 0)
        ang = a + fi * 0.9 + k
        d = (math.cos(ang), math.sin(ang))
        pts = line((x - d[0] * sz, y - d[1] * sz), (x + d[0] * sz, y + d[1] * sz))
        pts = [q for q in pts if K.inb(*q) and q[1] <= FLOOR]
        FX.put(pts, "N4" if k % 3 == 0 else "N3" if k % 3 == 1 else "Z4")
        if pts and sz > 1:
            FX.put([pts[0]], "U4" if stage < 3 else "N5")
            if len(pts) > 2:
                FX.put([(pts[1][0], pts[1][1] + 1)], "N2")


# =========================================================================== animations
IDLE_BASE = dict(P=(59.0, 72.0), C=(61.2, 47.0), Hd=(63.6, 30.2), hup=(0.12, -1), fb=(49.0, FLOOR), ff=(70.0, FLOOR))


def idle_pose(b, i):
    """Leaning on the planted maul, both hands on the pommel; b = breath 0..1."""
    return P_(P=(59.0, 72.0 + b * 0.4), C=(61.2, 47.0 + b * 1.1), Hd=(63.6, 30.2 + b * 1.3), fb=(49.0, FLOOR),
              ff=(70.0, FLOOR), maul=((84.5, 67.5), 90.0), hf=None, free=(84.2, 56.0 + b * 0.6),
              hb=(83.4, 59.4 + b * 0.6), breath=1, wind=0.3 * math.sin(i * 1.05))


def a_idle():
    return [(190, idle_pose((0, 0.3, 0.75, 1.0, 0.75, 0.3)[i], i)) for i in range(6)]


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (60.5 + 11.0 * c, FLOOR - max(0.0, -s) * 6.0)
        fb = (58.5 - 11.0 * c, FLOOR - max(0.0, s) * 6.0)
        bob = 2.2 * abs(c)
        sway = 0.6 * s
        fr.append((165, P_(P=(59.5 + sway, 71.0 + bob), C=(62.0 + sway, 46.4 + bob), Hd=(65.0 + sway, 29.8 + bob),
                           ff=ff, fb=fb, hf=(69.0 + 1.5 * c, 74.0 + bob), mang=166 - 3.0 * c, gu=-12.0, hb=(52.0 - 4.0 * c, 72.0 + bob), onehand=True,
                           wl="WeaponBack", breath=1, wind=0.4 * c)))
    return fr


def a_slam():
    WB = dict(wl="WeaponBack")
    rise = dict(P=(58.0, 72.4), C=(58.4, 47.2), Hd=(59.6, 30.4), hup=(-0.05, -1), fb=(46.0, FLOOR), ff=(71.0, FLOOR))
    arch = dict(P=(57.0, 72.6), C=(54.6, 47.8), Hd=(53.8, 31.4), hup=(-0.28, -1), fb=(44.0, FLOOR), ff=(72.0, FLOOR))
    arch2 = dict(P=(56.6, 73.0), C=(53.6, 48.4), Hd=(52.6, 32.2), hup=(-0.34, -1), fb=(43.5, FLOOR), ff=(72.5, FLOOR))
    hit = dict(P=(63.0, 79.0), C=(71.0, 57.6), Hd=(77.6, 43.2), hup=(0.62, -1), fb=(42.0, FLOOR), ff=(80.0, FLOOR))
    return [
        (140, P_(P=(58.6, 72.6), C=(61.0, 47.6), Hd=(63.4, 30.8), fb=(48.0, FLOOR), ff=(70.0, FLOOR),
                 hf=(80.0, 62.0), mang=66)),
        (130, P_(**rise, hf=(74.0, 48.0), mang=-50)),
        (130, P_(**rise, hf=(63.0, 50.0), mang=-110, **WB)),
        (160, P_(**arch, hf=(57.0, 33.0), mang=-152, **WB)),
        (380, P_(**arch2, hf=(55.0, 26.4), mang=-166, eye=2, glint=True, **WB)),
        (220, P_(**dict(arch2, C=(53.2, 48.6)), hf=(54.6, 26.6), mang=-170, eye=2, glint=True, **WB)),
        (60, P_(P=(61.0, 75.0), C=(65.0, 51.0), Hd=(68.8, 35.0), hup=(0.35, -1), fb=(43.0, FLOOR), ff=(77.0, FLOOR),
                hf=(76.0, 42.0), mang=-36, wind=4,
                smear=dict(g0=(54.6, 26.6), a0=-170, mid=(64.0, 20.0), start=0.05))),
        (80, P_(**hit, hf=(79.0, 76.0), mang=36, impact=1, wind=4, shake=1,
                smear=dict(g0=(76.0, 42.0), a0=-36, start=0.1))),
        (130, P_(**hit, hf=(79.0, 76.2), mang=36, impact=2, wind=2)),
        (280, P_(**dict(hit, C=(70.4, 58.4), Hd=(76.8, 44.4)), hf=(78.6, 76.6), mang=36, stuck=True, eye=0)),
        (260, P_(P=(61.6, 78.0), C=(67.4, 55.6), Hd=(72.6, 40.8), hup=(0.5, -1), fb=(43.0, FLOOR), ff=(79.0, FLOOR),
                 hf=(78.0, 74.0), mang=38, stuck=True)),
        (230, P_(P=(60.0, 74.0), C=(63.6, 49.4), Hd=(67.0, 32.8), hup=(0.25, -1), fb=(46.0, FLOOR), ff=(74.0, FLOOR),
                 hf=(78.0, 62.0), mang=-10)),
    ]


def a_sweep():
    WB = dict(wl="WeaponBack")
    coil = dict(P=(58.0, 74.0), C=(54.4, 50.4), Hd=(53.0, 34.0), hup=(-0.3, -1), fb=(42.0, FLOOR), ff=(70.0, FLOOR))
    lung = dict(P=(64.0, 77.0), C=(70.0, 54.0), Hd=(75.0, 38.6), hup=(0.48, -1), fb=(44.0, FLOOR), ff=(84.0, FLOOR))
    return [
        (140, P_(P=(58.6, 73.0), C=(58.6, 48.4), Hd=(59.6, 31.6), hup=(-0.08, -1), fb=(46.0, FLOOR), ff=(71.0, FLOOR),
                 hf=(66.0, 66.0), mang=160, **WB)),
        (150, P_(**coil, hf=(52.0, 70.0), mang=178, **WB)),
        (380, P_(**dict(coil, C=(53.8, 50.8), Hd=(52.2, 34.6)), hf=(52.0, 70.0), mang=181, eye=2, glint=True, **WB)),
        (90, P_(P=(60.0, 75.0), C=(60.4, 51.0), Hd=(62.0, 35.0), hup=(0.1, -1), fb=(43.0, FLOOR), ff=(76.0, FLOOR),
                hf=(62.0, 76.0), mang=150, wind=3, **WB)),
        (60, P_(**dict(lung, P=(62.0, 76.0), C=(64.0, 52.0), Hd=(68.0, 36.0), hup=(0.3, -1)), hf=(68.0, 70.0), mang=118,
                wind=5, flat=dict(c=(64.0, 93.0), rx=50.0, ry=12.0, th0=178, th1=100, w=7.0))),
        (70, P_(**lung, hf=(84.0, 84.0), mang=8, wind=5,
                flat=dict(c=(64.0, 93.0), rx=52.0, ry=12.0, th0=160, th1=-4, w=10.0))),
        (90, P_(**dict(lung, C=(71.0, 54.6)), hf=(84.0, 80.0), mang=-24, wind=3,
                flat=dict(c=(64.0, 93.0), rx=52.0, ry=12.0, th0=70, th1=-34, w=6.0, fade=0.45))),
        (200, P_(P=(63.0, 76.0), C=(68.0, 53.0), Hd=(72.4, 37.6), hup=(0.4, -1), fb=(44.0, FLOOR), ff=(82.0, FLOOR),
                 hf=(80.0, 74.0), mang=-40)),
        (200, P_(P=(61.0, 74.0), C=(64.6, 50.0), Hd=(68.0, 33.4), hup=(0.25, -1), fb=(46.0, FLOOR), ff=(77.0, FLOOR),
                 hf=(78.0, 66.0), mang=-60)),
        (200, P_(P=(59.6, 72.8), C=(62.0, 48.0), Hd=(64.6, 31.0), hup=(0.14, -1), fb=(48.0, FLOOR), ff=(72.0, FLOOR),
                 hf=(76.0, 58.0), mang=-100)),
    ]


def a_stomp():
    def S(hf, ang, hb, **kw):
        return dict(hf=(hf[0] + 1.0, hf[1] + 5.0), mang=ang + 100, onehand=False, **kw)
    return [
        (140, P_(P=(58.0, 73.0), C=(59.0, 48.0), Hd=(61.0, 31.4), hup=(0.05, -1), fb=(50.0, FLOOR), ff=(69.0, FLOOR),
                 **S((72.0, 58.0), -152, (50.0, 70.0)))),
        (140, P_(P=(56.4, 72.0), C=(56.0, 47.0), Hd=(57.0, 30.4), hup=(-0.08, -1), fb=(52.0, FLOOR), ff=(70.0, 104.0),
                 kf=(73.0, 84.0), **S((69.0, 57.0), -150, (44.0, 64.0)))),
        (140, P_(P=(55.6, 70.6), C=(54.4, 45.8), Hd=(55.0, 29.4), hup=(-0.15, -1), fb=(52.5, FLOOR), ff=(71.0, 96.0),
                 kf=(75.0, 77.0), **S((67.0, 56.0), -148, (40.0, 58.0)))),
        (360, P_(P=(55.0, 70.0), C=(53.4, 45.4), Hd=(53.6, 29.2), hup=(-0.2, -1), fb=(52.5, FLOOR), ff=(72.0, 93.0),
                 kf=(76.0, 74.0), eye=2, glint=(80.0, 94.0), **S((66.0, 55.6), -147, (38.0, 56.0)))),
        (70, P_(P=(58.0, 72.6), C=(59.0, 48.0), Hd=(60.6, 31.6), hup=(0.05, -1), fb=(51.0, FLOOR), ff=(74.0, 100.0),
                kf=(77.0, 84.0), **S((70.0, 58.0), -150, (44.0, 62.0)))),
        (80, P_(P=(61.0, 77.0), C=(64.0, 52.6), Hd=(67.0, 36.4), hup=(0.28, -1), fb=(48.0, FLOOR), ff=(77.0, FLOOR),
                stomp=1, shake=1, **S((76.0, 63.0), -150, (50.0, 74.0)))),
        (130, P_(P=(61.0, 77.4), C=(64.2, 53.0), Hd=(67.2, 36.8), hup=(0.3, -1), fb=(48.0, FLOOR), ff=(77.0, FLOOR),
                 stomp=2, **S((76.0, 63.4), -150, (50.4, 74.4)))),
        (180, P_(P=(60.4, 75.6), C=(63.0, 51.0), Hd=(66.0, 34.4), hup=(0.24, -1), fb=(48.0, FLOOR), ff=(77.0, FLOOR),
                 dust=2, **S((75.0, 61.6), -152, (51.0, 72.6)))),
        (180, P_(P=(60.0, 73.6), C=(62.0, 48.8), Hd=(64.6, 32.0), hup=(0.16, -1), fb=(48.5, FLOOR), ff=(74.0, FLOOR),
                 **S((74.0, 59.4), -154, (50.4, 71.0)))),
        (180, P_(P=(59.4, 72.4), C=(61.4, 47.4), Hd=(64.0, 30.6), hup=(0.12, -1), fb=(49.0, FLOOR), ff=(71.0, FLOOR),
                 **S((73.0, 58.4), -155, (50.0, 70.0)))),
    ]


def a_shatter():
    plant = ((86.0, 67.5), 88.0)
    hunch = dict(P=(58.0, 75.0), C=(61.0, 51.0), Hd=(64.6, 35.4), hup=(0.45, -1), fb=(47.0, FLOOR), ff=(71.0, FLOOR))
    roar = dict(P=(57.0, 72.0), C=(56.4, 46.4), Hd=(56.8, 29.4), hup=(-0.5, -1), fb=(45.0, FLOOR), ff=(72.0, FLOOR))
    base = dict(maul=plant, hf=None)
    return [
        (150, P_(**hunch, **base, free=(84.0, 62.0), hb=(80.0, 64.0), crack=0.15)),
        (150, P_(**shifted(hunch, 0.6), **base, free=(84.2, 62.4), hb=(80.4, 64.4), crack=0.35, shake=1)),
        (150, P_(**shifted(hunch, -0.6), **base, free=(84.0, 62.2), hb=(80.0, 64.0), crack=0.55)),
        (150, P_(**shifted(hunch, 0.6), **base, free=(84.2, 62.6), hb=(80.4, 64.4), crack=0.75, eye=2, shake=1)),
        (160, P_(**hunch, **base, free=(84.0, 62.0), hb=(80.0, 64.0), crack=1.0, eye=2)),
        (200, P_(**roar, **base, free=(88.0, 63.0), hb=(29.0, 64.0), crack=1.0, eye=2, flare=1, wind=3)),
        (80, P_(**roar, **base, free=(89.0, 62.0), hb=(28.0, 63.0), burst=1, eye=2, flare=2, wind=5, shake=1)),
        (100, P_(**roar, **base, free=(89.0, 62.6), hb=(28.4, 63.6), burst=2, eye=2, flare=2, wind=4)),
        (140, P_(**roar, **base, free=(88.0, 63.0), hb=(29.4, 64.4), burst=3, eye=2, flare=1, wind=2)),
        (300, P_(P=(58.0, 73.0), C=(60.4, 48.4), Hd=(63.2, 31.8), hup=(0.2, -1), fb=(47.0, FLOOR), ff=(71.0, FLOOR),
                 **base, free=(84.0, 61.0), hb=(80.4, 63.0), burst=4, eye=2)),
    ]


def a_stagger():
    plant = ((77.0, 66.0), 80.0)
    return [
        (100, P_(P=(56.4, 72.4), C=(53.0, 48.4), Hd=(51.4, 32.0), hup=(-0.45, -1), fb=(46.0, FLOOR), ff=(70.0, FLOOR),
                 hf=(60.0, 64.0), mang=176, eye=0, wl="WeaponBack")),
        (140, P_(P=(58.0, 80.0), C=(60.0, 56.0), Hd=(63.0, 40.0), hup=(0.3, -1), fb=(46.0, FLOOR), ff=(70.0, FLOOR),
                 kb=(50.0, 104.0), maul=plant, hf=None, free=(79.0, 68.0), hb=(77.0, 71.0), eye=0, dust=1)),
        (260, P_(P=(58.0, 84.0), C=(61.0, 60.6), Hd=(65.0, 45.4), hup=(0.5, -1), fb=(38.0, FLOOR), ff=(70.0, FLOOR),
                 kb=(50.0, 109.0), maul=plant, hf=None, free=(79.0, 68.4), hb=(76.4, 72.0), eye=0, dust=2)),
        (300, P_(P=(58.0, 84.4), C=(61.0, 61.0), Hd=(65.2, 46.0), hup=(0.52, -1), fb=(38.0, FLOOR), ff=(70.0, FLOOR),
                 kb=(50.0, 109.0), maul=plant, hf=None, free=(79.0, 68.6), hb=(76.4, 72.2), eye=1)),
    ]


def a_death():
    plant = ((81.0, 66.5), 84.0)
    KN = dict(P=(56.0, 90.0), C=(59.0, 67.0), Hd=(63.0, 52.4), hup=(0.55, -1), kb=(52.0, 109.2), fb=(36.0, FLOOR),
              kf=(66.0, 109.0), ff=(52.0, FLOOR), maul=plant, hf=None, free=(82.0, 70.0), hb=(79.6, 73.0), eye=1)
    fr = [
        (120, P_(P=(56.4, 72.4), C=(52.4, 48.4), Hd=(50.6, 32.4), hup=(-0.5, -1), fb=(46.0, FLOOR), ff=(70.0, FLOOR),
                 hf=(60.0, 64.0), mang=176, eye=2, wl="WeaponBack")),
        (160, P_(P=(58.0, 80.0), C=(60.0, 56.0), Hd=(63.0, 40.0), hup=(0.3, -1), fb=(46.0, FLOOR), ff=(70.0, FLOOR),
                 kb=(50.0, 104.0), maul=plant, hf=None, free=(82.0, 68.0), hb=(80.0, 71.0), eye=1, dust=1)),
        (200, P_(**dict(KN, P=(57.0, 86.0), C=(59.6, 62.6), Hd=(63.2, 47.6), hup=(0.4, -1)), dust=2)),
        (260, P_(**KN)),
        (500, P_(**dict(KN, Hd=(63.6, 53.2), hup=(0.62, -1)))),
        (300, P_(**dict(KN, C=(59.6, 68.0), Hd=(64.4, 54.6), hup=(0.78, -1), eye=0))),
        (500, P_(**dict(KN, C=(59.6, 68.2), Hd=(64.6, 54.8), hup=(0.8, -1), eye=0))),
    ]
    for d, ms in ((0.14, 140), (0.3, 140), (0.48, 140), (0.68, 160), (0.95, 900)):
        fr.append((ms, P_(**dict(KN, C=(59.6, 68.2), Hd=(64.6, 54.8), hup=(0.8, -1), eye=0), dissolve=d)))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("slam", a_slam), ("sweep", a_sweep), ("stomp", a_stomp),
           ("shatter", a_shatter), ("stagger", a_stagger), ("death", a_death)]
COUNTS = dict(idle=6, walk=8, slam=12, sweep=10, stomp=10, shatter=10, stagger=4, death=12)
LOOPS = ("idle", "walk")


def p2_pose(tag, p, k):
    """Phase 2: the bare warden -- faster, lower, leaning forward in idle/walk; shatter = roar with frost flare."""
    q = dict(p)
    if tag == "idle":
        # no longer leaning on the maul: a low forward-leaning guard, maul held two-handed across the body
        b = (0, 0.3, 0.75, 1.0, 0.75, 0.3)[k]
        q.update(P=(58.4, 75.0 + b * 0.4), C=(63.6, 51.4 + b * 1.1), Hd=(68.2, 35.4 + b * 1.3), hup=(0.42, -1),
                 fb=(45.0, FLOOR), ff=(72.0, FLOOR), maul="hand", hf=(80.0, 73.0 + b * 0.7), mang=46 - b * 2,
                 free=None, hb=None, onehand=False, wl="Weapon")
    elif tag == "walk":
        q = shifted(q, 0, 2.5, ("P",))
        q = shifted(q, 2.8, 3.6, ("C",))
        q = shifted(q, 4.6, 4.4, ("Hd", "hf"))
        q["hup"] = (0.4, -1)
    elif tag == "shatter":
        q.update(burst=0, crack=0.0)
        q["flare"] = {0: 0, 1: 0, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 1, 9: 0}[k]
    return q


# =========================================================================== render
def render_frame(p, fi, sw, phase):
    Ls, info = draw(p, fi, sw, phase)
    imgs = {}
    for n in LAYERS:
        v = Ls.get(n)
        if v is None or n in SHELLS:
            continue
        imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
    for n in SHELLS:
        L = Ls[n]
        if not L.px:
            continue
        see_through(L, K.flatten(imgs, UNDER[n]))
        imgs[n] = K.render_layer(L)
        if n == "ShellBack":
            pass
    if p["dissolve"] > 0:
        imgs = K.ember_dissolve(imgs, p["dissolve"], [n for n in LAYERS if n not in ("Weapon", "WeaponBack", "FX", "Glow",
                                                                                      "FXBack")],
                                fx_name="FX", seed=5, rise=30, pal=ICE_DISSOLVE)
        # snow motes drifting down as well
        fx = imgs["FX"].load()
        for k in range(int(30 * p["dissolve"])):
            x = int(40 + hash01(k, 1, 97) * 50)
            y = int(40 + hash01(k, 2, 97) * 70 * p["dissolve"])
            if K.inb(x, y):
                fx[x, y] = RGBA["N4" if k % 2 else "U3"]
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
                pp = p if ph == 1 else p2_pose(tag, p, k)
                imgs, info = render_frame(pp, a + k, sway[k], ph)
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


def scale_preview(flats1, flats2, tags, path):
    """1x composite next to the player (frame 0 + longsword) on the dark aqueduct blue, then 3x."""
    bg = (11, 15, 24, 255)
    start = {t: a for t, a, _ in tags}
    if "idle" not in start:
        return
    pl = Image.open(os.path.join(asebuild.ASSETS, "player.png")).crop((0, 0, 64, 40))
    ws = Image.open(os.path.join(asebuild.ASSETS, "wpn_longsword.png")).crop((0, 0, 64, 40))
    picks = [("idle", 0, 1), ("idle", 0, 2)]
    for t, k in (("slam", 4), ("slam", 8), ("sweep", 5), ("stomp", 5), ("shatter", 7)):
        if t in start:
            picks.append((t, k, 1))
    cw = 64 + len(picks) * (W - 24) + 8
    img = Image.new("RGBA", (cw, H + 6), bg)
    img.alpha_composite(pl, (4, H - 40))
    img.alpha_composite(ws, (4, H - 40))
    x = 40
    for t, k, ph in picks:
        fl = (flats1 if ph == 1 else flats2)[start[t] + k]
        img.alpha_composite(fl, (x, 0))
        x += W - 24
    d = ImageDraw.Draw(img)
    d.line([(0, H), (cw, H)], fill=(40, 48, 66, 255))
    img.resize((cw * 3, (H + 6) * 3), Image.NEAREST).save(path)


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


def attack(infos, tag, a, b, x_min=AX + 4, key="hit"):
    rs = {}
    for k in range(a, b + 1):
        pts = set(infos[tag][k][key])
        if "p2" in infos[tag][k]:
            pts |= infos[tag][k]["p2"][key]
        pts = {q for q in pts if q[0] >= x_min}
        r = bbox(pts)
        r[3] = H - r[1]                 # reach the floor: a 10x26 player standing there must be hit
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def build_meta(infos, tags):
    idle = infos["idle"][0]
    tb = bbox(idle["torso"] | idle["headmask"] | idle.get("pauldron", set()))
    x0, x1 = min(tb[0] - 1, AX - 12), max(tb[0] + tb[2] + 1, AX + 14)
    hurt = [x0, tb[1], x1 - x0, H - tb[1]]

    def pt(q):
        return [int(round(q[0])), int(round(q[1]))]
    st = infos["stomp"][5]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {
            "slam": attack(infos, "slam", 7, 8),
            "sweep": attack(infos, "sweep", 5, 6),
            "stomp": attack(infos, "stomp", 5, 6, x_min=AX, key="stomp_hit"),
        },
        "telegraph": {
            "slam": {"frame": 4, "at": pt(infos["slam"][4]["glint_at"])},
            "sweep": {"frame": 2, "at": pt(infos["sweep"][2]["glint_at"])},
            "stomp": {"frame": 3, "at": pt(infos["stomp"][3]["glint_at"])},
        },
        "spawn": {
            "slam": {"frame": 7, "at": [infos["slam"][7]["impact_x"], H - 1]},
            "stomp": {"frame": 5, "at": [st["stomp_x"], H - 1]},
            "shatter": {"frame": 6, "at": pt(infos["shatter"][6]["p2"]["core"])},
        },
        "notes": "faces right, anchor = feet (x=60). ice_warden (phase 1, ice shell on layers ShellBack/Shell/ShellArm) and "
                 "ice_warden_p2 (bare, cracked armour, frost core) share this meta, frames, tags and durations. "
                 "'hit' = union of per-frame 'rects' over the inclusive active range (rects reach the floor). "
                 "Telegraph 'at' = glint point on the anticipation hold (slam: maul head overhead, sweep: maul head "
                 "behind, stomp: raised front foot). spawn.slam = maul impact on the floor (fx_hf_shatter + frost "
                 "crack); slam frames 9-11 = maul stuck in the floor (punish window). spawn.stomp = the stomping foot: "
                 "erupt a line of fx_hf_icespike forward from there. shatter (phase transition, play on the p1 sheet): "
                 "cracks 0-4, roar 5, shell explodes 6-8 (spawn fx_hf_shatter at spawn.shatter), revealed 9 -> swap "
                 "to the p2 sheet after the tag; on the p2 sheet the same tag is a frost-flare roar. stagger holds "
                 "its last frame; death leaves the maul planted.",
    }
    return meta


# =========================================================================== FX sheets
def fx_icespike():
    """24x64, 8 frames, pivot bottom-centre: frost crack glint -> jagged ice spike erupts -> shatters."""
    w, h = 24, 64
    gy = h - 1
    cx = 12
    heights = (0, 0, 0, 40, 56, 52, 0, 0)
    frames = []
    for i in range(8):
        back = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        spike = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bp, sp, gp = back.load(), spike.load(), glow.load()

        def put(pp, x, y, c):
            if 0 <= x < w and 0 <= y < h:
                pp[int(x), int(y)] = RGBA[c]
        # ground crack glow (telegraph 0-2, lingering afterwards)
        cw_ = (3, 7, 10, 10, 9, 8, 6, 3)[i]
        br = (1, 2, 3, 3, 2, 2, 1, 0)[i]
        for dx in range(-cw_, cw_ + 1):
            if hash01(dx, 0, 3) < 0.15 and abs(dx) > 1:
                continue
            c = ("U1", "U2", "U3", "U4")[max(0, min(3, br - (1 if abs(dx) > cw_ * 0.5 else 0)))]
            put(gp, cx + dx, gy, c)
            if abs(dx) < cw_ * 0.45 and br >= 2:
                put(gp, cx + dx, gy - 1, "U1" if (dx + i) % 2 else "U2")
        if i <= 2:
            for dx in (-cw_ - 1, cw_ + 1):
                put(bp, cx + dx, gy, "OUT")
            for k in range(3 + i * 4):                               # rising ice motes
                x = cx + int((hash01(k, i, 15) - 0.5) * cw_ * 1.5)
                y = gy - 2 - int(hash01(k, i, 16) ** 1.4 * (6 + i * 9))
                put(gp, x, y, "U3" if k % 3 == 0 else "N3")
            if i == 2:
                put(gp, cx, gy - 2, "U4"); put(gp, cx - 1, gy - 2, "U3"); put(gp, cx + 1, gy - 2, "U3")
                put(gp, cx, gy - 3, "U3")
        hgt = heights[i]
        if hgt > 0:
            top = gy - hgt
            # main spike + two side shards: each a two-facet crystal with a bright lit edge
            shards = [(cx - 0.5, hgt, 5.4, 0.08), (cx - 5.0, hgt * 0.42, 2.8, -0.25), (cx + 5.0, hgt * 0.55, 3.0, 0.22)]
            for sx, sh, sw_, lean in shards:
                for y in range(int(gy - sh), gy + 1):
                    t = min(1.0, (gy - y) / max(1.0, sh))  # 0 base .. 1 tip
                    half = sw_ * (1 - t) ** 0.9 + 0.3
                    ccx = sx + lean * (gy - y) + math.sin(t * 7 + sx) * 0.3
                    for x in range(int(ccx - half - 1), int(ccx + half + 2)):
                        dx = x + .5 - ccx
                        if abs(dx) > half:
                            continue
                        rel = dx / max(half, 0.5)
                        if rel < -0.55:
                            c = "N5" if t > 0.15 else "N4"
                        elif rel < 0.0:
                            c = "N4" if t > 0.6 else "N3"
                        elif rel < 0.5:
                            c = "Z4" if t > 0.3 else "Z3"
                        else:
                            c = "Z3" if t > 0.3 else "Z2"
                        if t > 0.9:
                            c = "U4"
                        put(sp, x, y, c)
            # internal fracture glints + the frost core line
            for y in range(top + 4, gy - 2, 5):
                put(sp, cx - 1 + (y % 3 == 0), y, "N5" if i != 5 else "U3")
            # outline
            for y in range(h):
                for x in range(w):
                    if sp[x, y][3]:
                        continue
                    if any(0 <= x + a < w and 0 <= y + b < h and sp[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, -1))):
                        bp[x, y] = RGBA["N0"]
            if i == 3:     # eruption burst: shards & spray at the base
                for k in range(12):
                    a = -math.pi * (0.1 + 0.8 * hash01(k, 3, 17))
                    r = 3 + hash01(k, 4, 17) * 9
                    put(gp, cx + math.cos(a) * r, gy - 1 + math.sin(a) * r * 0.8, ("U4", "N4", "N3")[k % 3])
            if i == 4:     # glint on the tip
                put(gp, cx - 1, top + 1, "U4"); put(gp, cx - 3, top + 2, "U3"); put(gp, cx + 1, top + 2, "U3")
        if i >= 6:
            # shattered: the spike breaks into falling shards, a stub remains then melts into the crack
            stub = 10 if i == 6 else 4
            for y in range(gy - stub, gy + 1):
                t = (gy - y) / stub
                half = 4.0 * (1 - t) + 0.5
                for x in range(int(cx - half), int(cx + half + 1)):
                    put(sp, x, y, "N3" if x < cx else "Z3")
            n = 16 if i == 6 else 10
            for k in range(n):
                x = cx + (hash01(k, i, 21) - 0.5) * 18
                y = gy - 8 - hash01(k, i, 22) * (44 if i == 6 else 30) + (0 if i == 6 else 10)
                sz = 1 + int(hash01(k, i, 23) * 2)
                c = ("N4", "N3", "Z4", "U3")[k % 4]
                for j in range(sz + 1):
                    put(sp, x + j * 0.5, y + j, c)
                put(bp, x - 1, y, "N0") if sz > 1 else None
        frames.append({"ms": (90, 90, 110, 50, 70, 90, 80, 80)[i], "cels": {"Back": back, "Spike": spike, "Glow": glow}})
    return frames


def fx_shatter():
    """64x64, 6 frames, centred: ice-shell shards flying outward around a white flash core."""
    w, h = 64, 64
    cx, cy = 32, 32
    frames = []
    for i in range(6):
        ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shards = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        rp, sp, cp = ring.load(), shards.load(), core.load()

        def put(pp, x, y, c):
            x, y = int(math.floor(x)), int(math.floor(y))
            if 0 <= x < w and 0 <= y < h:
                pp[x, y] = RGBA[c]
        # flash core
        cr = (7, 9, 6, 3, 0, 0)[i]
        for y in range(h):
            for x in range(w):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d < cr:
                    put(cp, x, y, "U4" if d < cr * 0.55 else "U3")
                elif d < cr + 2 and i < 3:
                    put(cp, x, y, "U2")
        # shock ring
        rr = (10, 16, 22, 26, 29, 0)[i]
        if rr:
            for k in range(int(rr * 6.3)):
                a = k / (rr * 6.3) * 6.283
                if i >= 3 and hash01(k, i, 3) < 0.4 + 0.15 * i:
                    continue
                put(rp, cx + math.cos(a) * rr, cy + math.sin(a) * rr, "U3" if i < 2 else "U2" if i < 4 else "U1")
        # rays
        if i < 3:
            for k in range(8):
                a = k * 0.785 + 0.3
                for s in range(cr + 2, cr + 6 + 4 * i):
                    put(rp, cx + math.cos(a) * s, cy + math.sin(a) * s, "U3" if s < cr + 5 else "U2")
        # shards: faceted triangles flying outward, spinning, falling slightly
        for k in range(18):
            a = hash01(k, 1, 7) * 6.283
            sp_ = 0.6 + 0.6 * hash01(k, 2, 7)
            r = (4 + i * 5.5) * sp_ + 2
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r * 0.9 + (i * i) * 0.35 * hash01(k, 3, 7)
            sz = 2.0 + 3.0 * hash01(k, 4, 7) - i * 0.25
            if sz < 0.8 or (i == 5 and k % 2):
                continue
            rot = a + i * (0.8 + hash01(k, 5, 7))
            d = (math.cos(rot), math.sin(rot))
            pv = (-d[1], d[0])
            tri = [(x + d[0] * sz * 1.6, y + d[1] * sz * 1.6), (x - d[0] * sz + pv[0] * sz * 0.8, y - d[1] * sz + pv[1] * sz * 0.8),
                   (x - d[0] * sz - pv[0] * sz * 0.8, y - d[1] * sz - pv[1] * sz * 0.8)]
            m = poly_mask(tri) or {ip((x, y))}
            lit = pv[0] * K.LIGHT[0] + pv[1] * K.LIGHT[1] < 0
            for q in m:
                side = (q[0] + .5 - x) * pv[0] + (q[1] + .5 - y) * pv[1]
                c = ("N5" if lit else "N3") if side > 0 else ("Z3" if lit else "N4")
                put(sp, q[0], q[1], c)
            put(sp, *tri[0], "U4" if i < 3 else "N4")
            # dark rim
            for q in m:
                for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    qq = (q[0] + a2, q[1] + b2)
                    if qq not in m and 0 <= qq[0] < w and 0 <= qq[1] < h and not sp[qq][3]:
                        sp[qq] = RGBA["N0"]
            # sparkle trail
            if i in (1, 2, 3):
                for j in (1, 2):
                    put(rp, x - math.cos(a) * j * 3, y - math.sin(a) * j * 3, "N3" if j == 1 else "N2")
        # snow motes
        for k in range(14):
            a = hash01(k, 8, 7) * 6.283
            r = 6 + i * 5 * (0.5 + hash01(k, 9, 7))
            if i >= 1:
                put(rp, cx + math.cos(a) * r, cy + math.sin(a) * r + i * 1.5, "N4" if k % 2 else "U3")
        frames.append({"ms": (50, 60, 70, 80, 90, 100)[i], "cels": {"Ring": ring, "Shards": shards, "Core": core}})
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
    preview_rows(tags, flats[1], os.path.join(pv, f"{NAME}{sfx}.png"))
    preview_rows(tags, flats[2], os.path.join(pv, f"{NAME}_p2{sfx}.png"))
    c = Image.new("RGBA", (W * 2, H), BG)
    c.alpha_composite(flats[1][0]); c.alpha_composite(flats[2][0], (W, 0))
    c.resize((W * 2 * 5, H * 5), Image.NEAREST).save(os.path.join(pv, f"{NAME}_closeup{sfx}.png"))
    scale_preview(flats[1], flats[2], tags, os.path.join(pv, f"{NAME}_scale{sfx}.png"))
    zoom = os.environ.get("WZOOM")          # debug: "tag:i,j;tag2:k" -> $WZOOM_DIR/warden_zoom.png (p1 row, p2 row)
    if zoom:
        st_ = {t: a for t, a, _ in tags}
        idx = []
        for part in zoom.split(";"):
            t, ks = part.split(":")
            if t in st_:
                idx += [st_[t] + int(k) for k in ks.split(",")]
        sc = int(os.environ.get("WZOOM_SCALE", "4"))
        sheet = Image.new("RGBA", (len(idx) * (W + 1) * sc, 2 * (H + 1) * sc), (40, 40, 46, 255))
        for r, ph in enumerate((1, 2)):
            for i, j in enumerate(idx):
                fr = Image.new("RGBA", (W, H), BG)
                fr.alpha_composite(flats[ph][j])
                sheet.alpha_composite(fr.resize((W * sc, H * sc), Image.NEAREST), (i * (W + 1) * sc, r * (H + 1) * sc))
        sheet.save(os.path.join(os.environ.get("WZOOM_DIR", "/tmp"), "warden_zoom.png"))
    if only:
        return
    meta = build_meta(infos, tags)
    hitbox_preview(tags, flats[1], meta, os.path.join(pv, f"{NAME}_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, f"{NAME}_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        print("attack", t, d["active"], d["hit"], d["rects"])
    print("hurtbox", meta["hurtbox"], "telegraph", meta["telegraph"], "spawn", meta["spawn"])

    isp, shp = fx_icespike(), fx_shatter()
    s = 4
    sheet = Image.new("RGBA", (max((8 * 26 + 2) * s, 6 * 66 * 3), (64 + 4) * s + 64 * 3), (40, 40, 46, 255))
    for i, f in enumerate(isp):
        fr = Image.new("RGBA", (24, 64), (11, 15, 24, 255))
        for n in ("Back", "Spike", "Glow"):
            fr.alpha_composite(f["cels"][n])
        sheet.alpha_composite(fr.resize((24 * s, 64 * s), Image.NEAREST), (i * 26 * s, 0))
    for i, f in enumerate(shp):
        fr = Image.new("RGBA", (64, 64), (11, 15, 24, 255))
        for n in ("Ring", "Shards", "Core"):
            fr.alpha_composite(f["cels"][n])
        sheet.alpha_composite(fr.resize((64 * s // 2 * 2 // 2, 64 * s // 2 * 2 // 2), Image.NEAREST) if False else
                              fr.resize((64 * 3, 64 * 3), Image.NEAREST), (i * 66 * 3, (64 + 4) * s))
    sheet.save(os.path.join(pv, "fx_hf_warden.png"))

    if BUILD:
        fr1 = [{"ms": ms, "cels": imgs} for ms, imgs in out[1]]
        fr2 = [{"ms": ms, "cels": imgs} for ms, imgs in out[2]]
        asebuild.build(NAME, W, H, LAYERS, fr1, tags)
        asebuild.build(f"{NAME}_p2", W, H, LAYERS, fr2, tags)
        asebuild.build("fx_hf_icespike", 24, 64, ["Back", "Spike", "Glow"], isp, [("hf_icespike", 0, 7)])
        asebuild.build("fx_hf_shatter", 64, 64, ["Ring", "Shards", "Core"], shp, [("hf_shatter", 0, 5)])


if __name__ == "__main__":
    main()
