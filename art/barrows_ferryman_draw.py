"""Drawing kit for THE FERRYMAN (Drowned Barrows mini-boss).  Used by art/gen_barrows_ferryman.py.

A tall, gaunt hooded ferryman of the dead who strides on the black water.  Everything is built with the
enemy_kit method (per-pixel normal fields -> material ramps lit from the upper-left, per-layer sel-out outlines).

Fixed rig (identical in every frame, so proportions never drift):
    waist P -> chest C along the lean vector, spine SP px; head centre NECK px above C; head scale HS
    arms: upper UA + fore FA px (two-bone IK); oar-staff length SL (blade BL at the bottom end, iron hook on top)
The robe has no legs: its hem liquefies into black water that always reaches the floor row (FLOOR).
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, norm3, dirv, basis)

W, H = 192, 128
K.setup(W, H)
FLOOR = H - 1
AX = 96

# ---------------------------------------------------------------- rig constants
SP = 21.0        # waist -> chest
NECK = 9.5       # chest -> head centre
HS = 0.86        # head scale (small, menacing)
UA, FA = 15.5, 15.5
SL = 104.0       # oar-staff length (hook socket -> blade tip), ~1.2x his height
BL = 22.0        # oar blade length
HEM_Y = 119.0    # where the cloth turns into water (standing)

# ---------------------------------------------------------------- palette (runtime additions)
NEW = {
    # near-black robes with a faint teal sheen on the lit folds
    "S": ["#06090b", "#0b1114", "#0f181b", "#152125", "#1e2e32", "#2c4543"],
    # pale bone (hands, jaw) -- cold
    "E": ["#1a1d20", "#33383a", "#5a5e5b", "#878a83", "#b5b5aa", "#dddbcd"],
    # rusted iron
    "X": ["#0c0b0d", "#1b1717", "#2d2522", "#46362c", "#6a4f3a", "#99785a"],
    # black oar wood
    "J": ["#070708", "#0f0d0e", "#181515", "#231e1d", "#312a27", "#4a3f38"],
    # black water (top step = pale foam)
    "N": ["#04080a", "#081317", "#0f2026", "#18343a", "#2c5d5a", "#9fd0c6"],
    # lantern light (fixed colours): deep teal .. #2fbfb0 .. #8ff0e0 .. core #e8fff8
    "Z": ["#0b2a2a", "#145652", "#1f8c83", "#2fbfb0", "#8ff0e0", "#e8fff8"],
    # dull obol bronze
    "U": ["#140f0b", "#241a12", "#3a2a1a", "#554028", "#735a38", "#94784e"],
}
for _r, _cols in NEW.items():
    K.RAMP[_r] = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        K.RAMP[_r].append(_k)
# translucent teal glow steps (FX only)
for _k, _a in (("GA1", 46), ("GA2", 80), ("GA3", 120)):
    K.RGBA[_k] = (47, 191, 176, _a)
K.RGBA["GB2"] = (143, 240, 224, 90)
K.SHINY.update({"X": 0.94})
K.SHINY.pop("S", None)
RGBA = K.RGBA
SMEAR = ["Z5", "Z4", "Z3", "N4"]

LAYERS = ["Glow", "StaffBack", "BackArm", "Robe", "Torso", "Mantle", "Cowl", "Face", "Staff", "FrontArm",
          "Lantern", "Smear", "FX"]
FXL = {"Glow", "Smear", "FX"}
BODY_LAYERS = ["BackArm", "Robe", "Torso", "Mantle", "Cowl", "Face", "FrontArm"]


# =========================================================================== small helpers
def curve(pts, n=10):
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def n_tube(pts, radii, flat=1.0, step=0.35):
    samp = []
    for (a, ra), (b, rb) in zip(zip(pts, radii), zip(pts[1:], radii[1:])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            samp.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ra + (rb - ra) * t))
    samp.append((pts[-1][0], pts[-1][1], radii[-1]))
    R = max(radii) + 1
    xs = [s[0] for s in samp]
    ys = [s[1] for s in samp]
    out = {}
    for y in range(int(min(ys) - R) - 1, int(max(ys) + R) + 2):
        for x in range(int(min(xs) - R) - 1, int(max(xs) + R) + 2):
            px, py = x + .5, y + .5
            best = None
            for sx, sy, r in samp:
                dx, dy = px - sx, py - sy
                if abs(dx) > r or abs(dy) > r:
                    continue
                q = (dx * dx + dy * dy) / (r * r)
                if q <= 1 and (best is None or q < best[0]):
                    best = (q, dx / r, dy / r)
            if best:
                nx, ny = best[1] * flat, best[2] * flat
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
    return out


def tube(L, pts, radii, mat, bias=0, ao=1, flat=1.0, floor=FLOOR):
    nm = {q: v for q, v in n_tube(pts, radii, flat).items() if q[1] <= floor}
    return L.paint(nm, mat, bias, ao)


def plate(L, pts, mat, bevel=1.6, tilt=(0, 0), strength=1.1, fold=None, bias=0, ao=1, floor=FLOOR, clip=None):
    m = {q for q in poly_mask(pts) if q[1] <= floor}
    if clip is not None:
        m &= clip
    if not m:
        return m
    L.paint(n_plate(m, bevel, tilt, strength, fold), mat, bias, ao)
    return m


def remat(L, pts, mat, dl=0):
    for q in pts:
        e = L.px.get(q)
        if e is not None and e[3] is None:
            e[0] = mat
            e[2] += dl


def madd(p, *vs):
    x, y = p
    for v, k in vs:
        x += v[0] * k
        y += v[1] * k
    return (x, y)


def unit(v):
    l = math.hypot(*v) or 1e-6
    return (v[0] / l, v[1] / l)


def star(FX, c, big=False):
    x, y = ip(c)
    FX.put([(x, y)], "Z5")
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], "Z5" if big else "Z4")
    arm = ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0), (0, -3), (0, 3))
    if big:
        arm += ((4, 0), (-4, 0), (0, -4), (0, 4), (1, 1), (-1, -1), (1, -1), (-1, 1))
    for d in arm:
        FX.put([(x + d[0], y + d[1])], "Z3" if abs(d[0]) + abs(d[1]) > 2 else "Z4")


# =========================================================================== the oar-staff
def staff_geom(st):
    """st = dict(g=front-hand grip, a=angle of the top->blade direction (deg, screen), u=grip distance from the
    top socket, sl=optional length). Returns (T top socket, d unit top->blade, n hook side, SLc)."""
    sl = st.get("sl", SL)
    d = dirv(st["a"])
    T = (st["g"][0] - d[0] * st["u"], st["g"][1] - d[1] * st["u"])
    n = (d[1], -d[0])                     # 'forward/up' side of the staff: the hook curls this way
    if st.get("flip"):
        n = (-n[0], -n[1])
    return T, d, n, sl


def staff_pt(st, u):
    T, d, n, sl = staff_geom(st)
    return (T[0] + d[0] * u, T[1] + d[1] * u)


def blade_w(s):
    """Half-width of the oar blade at s px from its neck."""
    if s < 0:
        return 0.0
    if s < 4.0:
        return 0.9 + 0.35 * s
    if s < 11.0:
        return 2.3 + (s - 4.0) / 7.0 * 1.9
    if s < 18.0:
        return 4.2
    k = (s - 18.0) / (BL - 18.0 + 0.6)
    return 4.2 * math.sqrt(max(0.0, 1 - k * k))


def draw_staff(L, st, info, hook=True, bands=True, floor=FLOOR):
    """Black-wood shaft, broad oar blade at the bottom end, iron socket (+ hook) at the top end."""
    T, d, n, sl = staff_geom(st)
    pv = (-d[1], d[0])                     # screen-perpendicular for the raster
    b0 = sl - BL
    ends = [T, (T[0] + d[0] * sl, T[1] + d[1] * sl)]
    xs = [e[0] for e in ends]
    ys = [e[1] for e in ends]
    shaft, blade = {}, {}
    for y in range(int(min(ys)) - 6, int(max(ys)) + 7):
        for x in range(int(min(xs)) - 6, int(max(xs)) + 7):
            if y > floor or not K.inb(x, y):
                continue
            ox, oy = x + .5 - T[0], y + .5 - T[1]
            u = ox * d[0] + oy * d[1]
            v = ox * pv[0] + oy * pv[1]
            if -0.5 <= u <= b0 + 0.5 and abs(v) <= 0.95:
                k = v / 1.0
                shaft[(x, y)] = norm3(k * pv[0], k * pv[1], math.sqrt(max(0.1, 1 - k * k)))
            elif b0 < u <= sl + 0.3:
                w = blade_w(u - b0)
                if abs(v) <= w:
                    k = v / max(w, 0.6)
                    rid = 0.5 * k                     # gently convex with a central ridge
                    blade[(x, y)] = norm3(rid * pv[0] - 0.15 * d[0], rid * pv[1] - 0.15 * d[1], 1.0)
    L.paint(shaft, "J", 0, ao=0)
    L.paint(blade, "J", 0, ao=0)
    bl = set(blade)
    # worn pale edge of the blade + dark ridge line
    for q in bl:
        ox, oy = q[0] + .5 - T[0], q[1] + .5 - T[1]
        u = ox * d[0] + oy * d[1]
        v = ox * pv[0] + oy * pv[1]
        w = blade_w(u - b0)
        if w - abs(v) < 1.0 and u - b0 > 3:
            L.decal([q], ("J", 4))
        elif abs(v) < 0.5 and 4 < u - b0 < BL - 3:
            L.decal([q], ("J", 1))
    # iron bands: blade neck + socket collar
    if bands:
        for u0, u1, r in ((b0 - 1.5, b0 + 1.2, 1.5), (0.0, 3.2, 1.45), (38.0, 39.4, 1.25)):
            band = {}
            for q in shaft:
                ox, oy = q[0] + .5 - T[0], q[1] + .5 - T[1]
                u = ox * d[0] + oy * d[1]
                if u0 <= u <= u1:
                    band[q] = shaft[q]
            nb = {}
            for q in list(band):
                for dd in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    qq = (q[0] + dd[0], q[1] + dd[1])
                    ox, oy = qq[0] + .5 - T[0], qq[1] + .5 - T[1]
                    u = ox * d[0] + oy * d[1]
                    v = ox * pv[0] + oy * pv[1]
                    if u0 <= u <= u1 and abs(v) <= r and qq[1] <= floor:
                        k = v / r
                        nb[qq] = norm3(k * pv[0], k * pv[1], math.sqrt(max(0.1, 1 - k * k)))
            L.paint(nb, "X", 0, ao=0)
    info.setdefault("blade", set()).update(bl)
    info.setdefault("staff_px", set()).update(bl | set(shaft))
    info["tip"] = ends[1]
    info["top"] = T
    info["blade_mid"] = (T[0] + d[0] * (sl - BL * 0.45), T[1] + d[1] * (sl - BL * 0.45))
    hang = None
    if hook:
        # iron boat-hook: a short spike past the socket + a curled barb towards n
        def H_(u, v):
            return (T[0] + d[0] * u + n[0] * v, T[1] + d[1] * u + n[1] * v)
        tube(L, [H_(0.5, 0), H_(-5.5, 0)], [1.25, 0.7], "X", 0, ao=0, floor=floor)
        crv = curve([H_(-0.5, 0.6), H_(-3.2, 3.0), H_(-2.6, 5.6), H_(0.2, 6.6), H_(2.4, 5.4)], n=6)
        tube(L, crv, [1.1] * (len(crv) - 3) + [0.95, 0.8, 0.65], "X", 0, ao=0,
             floor=floor)
        # the lantern hangs from the lowest point of the curl
        cand = [H_(-3.0, 3.6), H_(-2.6, 5.6), H_(0.2, 6.6), H_(-0.6, 0.6)]
        hang = max(cand, key=lambda q: q[1])
        info["hook_tip"] = H_(-5.5, 0)
    else:
        # bare socket with the chain's end ring
        tube(L, [(T[0] + d[0] * 0.5, T[1] + d[1] * 0.5), (T[0] - d[0] * 1.6, T[1] - d[1] * 1.6)], [1.35, 1.1], "X", 0,
             ao=0, floor=floor)
        info["hook_tip"] = (T[0] - d[0] * 2.0, T[1] - d[1] * 2.0)
    info["hang"] = hang
    return hang


# =========================================================================== the hook-lantern
def draw_lantern(L, G, FX, top, sway, level, fi, info, floor=FLOOR, chain=4.0):
    """Small iron cage lantern on a short chain from `top`, hanging at `sway` degrees from vertical.
    level: 0 dark, 1 normal, 2 bright (telegraph), 3 flare, 0.5 guttering."""
    s, c = math.sin(math.radians(sway)), math.cos(math.radians(sway))

    def Lp(x, y):          # local (x across, y down from the chain top) -> frame
        return (top[0] + x * c + y * s, top[1] - x * s + y * c)
    # chain links
    ch = {}
    k = 0
    y = 0.4
    while y < chain:
        q = ip(Lp(0, y))
        ch[q] = "X3" if k % 2 == 0 else "X1"
        y += 1.0
        k += 1
    L.fixed({q: v for q, v in ch.items() if q[1] <= floor})
    L.noout |= set(ch)
    y0 = chain
    # cap (trapezoid), glass, base
    cap = [Lp(-1.2, y0 + 0.0), Lp(1.2, y0 + 0.0), Lp(2.9, y0 + 2.2), Lp(-2.9, y0 + 2.2)]
    cm = {q for q in poly_mask(cap) if q[1] <= floor}
    L.paint(n_plate(cm, 1.0, (-0.1, -0.5), 1.0), "X", 0, ao=0)
    glass = [Lp(-2.4, y0 + 2.0), Lp(2.4, y0 + 2.0), Lp(2.4, y0 + 7.4), Lp(-2.4, y0 + 7.4)]
    gm = {q for q in poly_mask(glass) if q[1] <= floor}
    base = [Lp(-2.9, y0 + 7.2), Lp(2.9, y0 + 7.2), Lp(1.6, y0 + 9.0), Lp(-1.6, y0 + 9.0)]
    bm = {q for q in poly_mask(base) if q[1] <= floor} - gm
    L.paint(n_plate(bm, 1.0, (-0.1, 0.2), 1.0), "X", -1, ao=0)
    ctr = Lp(0, y0 + 4.8)
    pix = {}
    for q in gm:
        dx, dy = q[0] + .5 - ctr[0], q[1] + .5 - ctr[1]
        r = math.hypot(dx * 1.1, dy * 0.8)
        if level <= 0:
            col = "S2" if r > 1.6 else "S3"
        elif level < 1:
            col = ("Z1" if r > 1.4 else "Z3") if fi % 2 == 0 else ("Z1" if r > 1.0 else "Z2")
        elif level < 2:
            col = "Z5" if r < 0.9 else "Z4" if r < 1.9 else "Z3"
        else:
            col = "Z5" if r < 1.6 else "Z4" if r < 2.6 else "Z3"
        pix[q] = col
    # cage bars on the glass
    for q in line(Lp(-2.4, y0 + 2.2), Lp(-2.4, y0 + 7.2)) + line(Lp(2.3, y0 + 2.2), Lp(2.3, y0 + 7.2)):
        if q in pix:
            pix[q] = "X2" if level > 0 else "X1"
    L.fixed(pix)
    fin = ip(Lp(0, y0 + 9.6))
    if fin[1] <= floor:
        L.fixed({fin: "X2"})
    info["lantern"] = ctr
    info["lantern_px"] = cm | gm | bm
    # glow: translucent teal halo behind (restrained), a few motes
    if level > 0:
        R0 = {0.5: 3.0, 1: 4.5, 2: 7.0, 3: 10.0}.get(level, 5.5 + (level - 1) * 2.5)
        for q in mask_disc(ctr, R0 + 3, R0 + 3):
            if not K.inb(*q) or q[1] > floor:
                continue
            r = math.hypot(q[0] + .5 - ctr[0], q[1] + .5 - ctr[1])
            if r < R0 * 0.45:
                G.put([q], "GA2")
            elif r < R0:
                G.put([q], "GA1")
            elif r < R0 + 2.5 and (q[0] + q[1]) % 2 == 0:
                G.put([q], "GA1")
        if level >= 2:
            for k in range(3 + int(level) * 2):
                a = 2 * math.pi * hash01(k, fi, 81)
                r = R0 * (0.6 + 0.6 * hash01(k, fi, 82))
                q = ip((ctr[0] + math.cos(a) * r, ctr[1] + math.sin(a) * r - 2))
                FX.put([q], "Z4" if k % 3 else "Z5")
    return ctr


# =========================================================================== arms
def sleeve_arm(L, sh, hand, bias, fi, sw, pref=(0.2, 1.0), grip=None, drape=5.0, seed=0, show_hand=True, floor=FLOOR):
    """Long bell sleeve (robe cloth) ending before a gaunt pale bony hand. grip = staff direction for finger wrap."""
    d = math.hypot(hand[0] - sh[0], hand[1] - sh[1])
    info = {"reach": d - (UA + FA)}
    el = ik(sh, hand, UA, FA, pref)
    info["elbow"] = el
    fdir = unit(sub(hand, el))
    cuff = madd(el, (fdir, FA - 4.6))
    tube(L, [sh, lerp(sh, el, 0.5), el], [3.0, 2.6, 2.4], "S", bias, floor=floor)
    tube(L, [el, lerp(el, cuff, 0.5), cuff], [2.4, 2.7, 3.1], "S", bias, floor=floor)
    # the drape of the sleeve hangs under the forearm (gravity), ragged
    pts = [madd(el, (fdir, 0.5)), cuff]
    lo = []
    for i in range(6):
        t = i / 5
        c = lerp(cuff, el, t * 0.85)
        dep = drape * (1 - 0.75 * t) * (0.55 + 0.45 * abs(fdir[0]) + 0.3 * max(0.0, -fdir[1]))
        jag = (1.8 * hash01(i, seed, fi // 3) if i % 2 == 0 else -0.4)
        lo.append((c[0] - sw * 0.25 * (1 - t), c[1] + 1.8 + dep + jag))
    poly = pts + lo
    m = {q for q in poly_mask(poly) if q[1] <= floor}
    L.paint(n_plate(m, 2.0, (0.0, 0.25), 1.0), "S", bias - 1, ao=0)
    # pale bony wrist + hand
    if show_hand:
        wr = madd(cuff, (fdir, 0.6))
        tube(L, [wr, madd(hand, (fdir, -0.6))], [1.0, 1.0], "E", bias, ao=0, floor=floor)
        L.paint({q: v for q, v in n_dome(hand, 1.6, 1.6, tilt=(-0.1, -0.1)).items() if q[1] <= floor}, "E", bias - 1, ao=0)
        # long knuckled fingers curled round the staff (or hanging)
        if grip is not None:
            gd = unit(grip)
            gp = (-gd[1], gd[0])
            if gp[0] * fdir[0] + gp[1] * fdir[1] < 0:
                gp = (-gp[0], -gp[1])
            fing = {}
            for k in range(3):
                q = ip(madd(hand, (gd, -1.4 + k * 1.4), (gp, 1.6)))
                fing[q] = "E4" if k == 0 else "E3"
            L.fixed({q: c for q, c in fing.items() if q[1] <= floor})
        else:
            for k in range(3):
                q = ip(madd(hand, (fdir, 2.2 + k * 0.9), ((-fdir[1], fdir[0]), -0.8 + k * 0.8)))
                if q[1] <= floor:
                    L.fixed({q: "E3" if k else "E4"})
    return el, info


# =========================================================================== figure
NEU = dict(P=(94.0, 79.0), lean=5.0, htilt=0.0, trail=2.0, hemx=0.0, hemy=HEM_Y, air=False,
           st=dict(g=(114.0, 63.0), a=80.5, u=45.0), hb=(94.0, 90.0), hb_on=None, sback=False,
           lant="hook", lsw=0.0, lvl=1.0, eye=1, glint=None, sweep=None, splash=0, spray=0, wake=0.0,
           burst=0, melt=0.0, wind=0.0, ripple=1, hook_flare=0, jaw=0.0, staff=True, bflash=None, hood_back=0.0,
           drip=1.0, cool=0, hf=None, heap=0, puddle=0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    if "st" in kw:
        s = dict(NEU["st"])
        s.update(kw["st"])
        d["st"] = s
    return d


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    GL, SM, FX = FXLayer("Glow"), FXLayer("Smear"), FXLayer("FX")
    Ls["Glow"], Ls["Smear"], Ls["FX"] = GL, SM, FX
    info = {"hit": set(), "reach": []}
    if p.get("heap"):
        return draw_heap(p, fi, sw, Ls, GL, SM, FX, info)
    P = p["P"]
    lean = p["lean"]
    up = dirv(-90 + lean)
    F = basis(P, up)
    C = F(0, -SP)
    hup = dirv(-90 + lean + p["htilt"])
    Hd = add(add(C, (up[0] * NECK, up[1] * NECK)), (hup[0] * 0.5 + 2.2 * math.cos(math.radians(lean)), 0))
    G0 = basis(Hd, hup)
    G = lambda a, b: G0(a * HS, b * HS)
    shF, shB = F(3.4, -SP + 2.6), F(-4.2, -SP + 2.0)
    cs = sw * 0.7 + p["wind"] * 0.8           # cloth sway (+ = streaming back)
    hemy = p["hemy"]
    floor = FLOOR

    # ---------------- staff geometry (hands follow it)
    st = p["st"]
    T, d, n, slc = staff_geom(st)
    hf = p["hf"] if p.get("hf") else st["g"]
    if p["hb_on"] is not None:
        hb = staff_pt(st, p["hb_on"])
    else:
        hb = p["hb"]

    # ---------------- back arm (far side)
    el_b, ib = sleeve_arm(Ls["BackArm"], shB, hb, -1, fi, sw, pref=p.get("pref_b", (0.3, 1.0)),
                          grip=d if p["hb_on"] is not None else None, seed=5, show_hand=p["melt"] < 0.35)
    info["reach"].append(("back", ib["reach"]))

    # ---------------- lower robe: waist -> hem, liquefying into black water at the floor
    Rb = Ls["Robe"]
    tr = p["trail"] + cs * 0.9
    hx = P[0] + p["hemx"]
    wf, wb = F(5.0, 0.5), F(-5.6, 0.5)
    rl = max(8.0, hemy - P[1])
    midy = P[1] + rl * 0.55
    mw = 1.0 + 0.7 * p["melt"] + p.get("squash", 0.0)
    hwf, hwb = 11.5 * mw, 13.0 * mw
    front = curve([wf, (P[0] + 7.2 * mw + p["hemx"] * 0.4 - tr * 0.15, midy), (hx + hwf - tr * 0.35, hemy)], n=6)
    back = curve([(hx - hwb - tr, hemy - 1.0), (P[0] - 8.6 * mw - tr * 0.55 + p["hemx"] * 0.3, midy), wb], n=6)
    if p["puddle"]:
        puddle(Rb, FX, hx, p["puddle"], fi)
    hem = []
    x0, x1 = hx + hwf - tr * 0.35, hx - hwb - tr
    nh = 11
    for i in range(1, nh):
        t = i / nh
        x = x0 + (x1 - x0) * t
        long_ = (i % 2 == 0)
        dy = (2.2 + 2.6 * hash01(i, 17, fi // 2)) if long_ else -0.5
        hem.append((x, hemy + dy))
    tail = [(x1 - 3.5 - tr * 0.6, hemy + 0.5), (x1 + 0.5, hemy - 3.0)]
    poly = front + hem + tail + back
    fold_ph = cs * 0.35 + p.get("fphase", 0.0)

    def rfold(x, y):
        amp = 1.25 * min(1.0, max(0.0, (y - P[1] - 3) / 12.0))
        return (amp * math.sin((x - hx) * 0.62 + (y - P[1]) * 0.05 * (1 if tr >= 0 else -1) + fold_ph), 0.0)
    rm = plate(Rb, poly, "S", bevel=4.0, tilt=(-0.05, -0.05), strength=1.15, fold=rfold, floor=floor, bias=-1)
    info["robe"] = rm
    # the hem liquefies: bottom rows become black water with vertical run-off streaks
    wet = []
    for q in rm:
        cut = hemy - 7.0 + 3.0 * hash01(q[0], 3, 29)
        if q[1] >= cut:
            wet.append(q)
    remat(Rb, wet, "N", -1)
    for q in wet:
        if hash01(q[0], 5, 31) < 0.18 and (q[1] + fi) % 4 == 0:
            Rb.decal([q], ("N", 3))
    # dripping streams from the ragged hem down to the floor (the hem touches the bottom row)
    Wt = FX if p["air"] else None
    drip = {}
    if not p["air"]:
        lowest = {}
        for q in rm:
            if q[1] > lowest.get(q[0], -1):
                lowest[q[0]] = q[1]
        xs = sorted(lowest)
        for x in xs:
            y0 = lowest[x]
            hsh = hash01(x, 7, 41)
            if hsh < 0.62 or y0 >= floor - 2:
                for y in range(y0 + 1, floor + 1):
                    k = (y - y0)
                    col = "N1" if k > 2 else "N2"
                    if (y + fi * 2 + int(hsh * 9)) % 7 == 0 and hsh < 0.25:
                        col = "N3"
                    drip[(x, y)] = col
            else:
                ln_ = 1 + int(hash01(x, 9, fi // 2) * 3)
                for y in range(y0 + 1, min(floor, y0 + ln_) + 1):
                    drip[(x, y)] = "N1"
                dy_ = y0 + ln_ + 2 + (fi * 2 + int(hsh * 11)) % 5
                if dy_ <= floor:
                    drip[(x, dy_)] = "N3"
        # pool where the robe meets the water
        pl0, pl1 = int(min(xs)) - 2, int(max(xs)) + 2
        for x in range(pl0, pl1 + 1):
            drip[(x, floor)] = "N1"
            if pl0 + 1 <= x <= pl1 - 1:
                drip[(x, floor - 1)] = drip.get((x, floor - 1), "N1")
        Rb.fixed(drip)
        info["pool"] = (pl0, pl1)
        # ripple rings on the surface around him
        if p["ripple"]:
            for side in (-1, 1):
                for k in range(3):
                    ph = (fi * 1.3 + k * 2.2) % 6.6
                    r = 4 + ph * 2.4
                    xa = (pl1 if side > 0 else pl0) + side * r
                    ln2 = max(1, int(3 - ph * 0.3))
                    for j in range(ln2):
                        q = (int(xa + side * j), floor - (0 if ph > 3 else 1) * (j == 0))
                        FX.put([q], "N5" if ph < 2.2 else "N4" if ph < 4.5 else "N3")
    else:
        # airborne: water falls from the hem in drops
        lowest = {}
        for q in rm:
            if q[1] > lowest.get(q[0], -1):
                lowest[q[0]] = q[1]
        for x, y0 in lowest.items():
            h_ = hash01(x, 11, 43)
            if h_ < 0.45:
                ln_ = 2 + int(h_ * 8)
                for y in range(y0 + 1, min(floor, y0 + ln_) + 1):
                    drip[(x, y)] = "N1" if y - y0 > 1 else "N2"
                dy_ = y0 + ln_ + 3 + int(hash01(x, fi, 44) * 6)
                if dy_ <= floor:
                    FX.put([(x, dy_)], "N4")
        Rb.fixed(drip)
    info["drip"] = set(drip)

    # ---------------- torso (slender, high-waisted), cord belt with a string of obols
    To = Ls["Torso"]
    tor = [F(-5.6, -SP + 1.0), F(-2.2, -SP - 1.2), F(4.4, -SP - 0.4), F(6.2, -SP + 5.5), F(5.4, -9.0), F(5.2, 1.5),
           F(-5.8, 1.5), F(-6.8, -SP + 9.0)]
    tm = plate(To, tor, "S", bevel=3.5, tilt=(-0.1, -0.1), strength=1.2,
               fold=lambda x, y: (0.45 * math.sin((x - C[0]) * 0.9 + y * 0.25), 0), floor=floor)
    info["torso"] = tm
    belt = [F(-5.8, -1.6), F(0.0, -2.2), F(5.4, -1.8)]
    tube(To, belt, [0.8, 0.9, 0.8], "S", 0, ao=1, floor=floor)
    # obol string hanging from the belt front
    o0 = F(3.6, -1.4)
    cord = [o0, add(o0, (0.6 + cs * 0.15, 4.0)), add(o0, (0.9 + cs * 0.3, 8.0))]
    To.fixed({q: "S0" for q in polyline(cord) if q[1] <= floor})
    for k, t in enumerate((0.45, 0.9)):
        c = lerp(cord[0], cord[-1], t)
        cc = ip((c[0] + 0.8, c[1]))
        cp = {cc: "U3", (cc[0] + 1, cc[1]): "U2", (cc[0], cc[1] + 1): "U2", (cc[0] + 1, cc[1] + 1): "U1"}
        To.fixed({q: v for q, v in cp.items() if q[1] <= floor})

    # ---------------- mantle: short tattered capelet over the shoulders
    Mt = Ls["Mantle"]
    mant = [F(-6.6, -SP + 0.5), F(-4.4, -SP - 3.0), F(1.0, -SP - 3.8), F(5.4, -SP - 1.2), F(6.8, -SP + 3.4)]
    nm_ = 9
    for i in range(nm_ + 1):
        t = i / nm_
        a_ = 6.8 - 15.6 * t
        b_ = -SP + 6.0 + 5.5 * t + (3.0 * hash01(i, 23, fi // 3) if i % 2 == 0 else -0.3)
        q = F(a_, b_)
        mant.append((q[0] - cs * 0.55 * t, q[1]))
    mant.append(F(-9.0 - cs * 0.3, -SP + 5.0))
    mm = plate(Mt, mant, "S", bevel=3.5, tilt=(-0.2, -0.35), strength=1.25,
               fold=lambda x, y: (0.35 * math.sin((x - C[0]) * 0.8 - y * 0.3), 0), floor=floor)
    info["mantle"] = mm

    # ---------------- cowl: deep hood, small; face = void with two cold eye-points + a hint of pale jaw
    Cw, Fc = Ls["Cowl"], Ls["Face"]
    hb_ = p["hood_back"]
    hood = [G(-7.2, 9.6), G(-8.8, 3.0), G(-8.6, -2.6), G(-10.4 - hb_, -8.2), G(-5.8, -9.4 + hb_), G(-1.6, -11.2 + hb_),
            G(1.8, -11.3 + hb_),
            G(5.4, -9.2), G(8.4, -5.4), G(10.8, -1.6), G(9.6, -0.6), G(9.8, 3.6), G(9.0, 7.6), G(5.6, 10.4),
            G(-2.0, 10.9)]
    hm = plate(Cw, hood, "S", bevel=3.6, tilt=(-0.15, -0.3), strength=1.3, ao=0, floor=floor)
    info["head"] = hm
    # hood seam + lit rim of the peak (teal sheen)
    Cw.decal([q for q in polyline(curve([G(-5.6, -3.0), G(-3.8, 2.4), G(-2.0, 8.0)], n=5)) if q in hm], ("S", 1))
    Cw.decal([q for q in polyline(curve([G(-5.4, -7.6 + hb_), G(-1.4, -10.4 + hb_), G(3.4, -9.4), G(7.6, -5.2)], n=6))
              if q in hm], ("S", 5))
    # the deep opening sits back under the brow, a 1px cloth lip in front of it
    opening = [G(2.8, -1.6), G(8.8, -0.6), G(8.2, 3.6), G(7.0, 7.4), G(4.0, 8.4), G(2.2, 3.0)]
    om = {q for q in poly_mask(opening) if q[1] <= floor} & hm
    Fc.fixed({q: "S0" for q in om})
    br = {q for q in om if (q[0], q[1] - 1) not in om}
    Fc.fixed({q: "OUT" for q in br})                                   # brow shadow line
    info["face"] = om
    if p["melt"] < 0.5:
        # a hint of pale bony jaw low in the shadow
        jl = [q for q in line(G(6.0, 6.6 - p["jaw"]), G(8.0, 5.4 - p["jaw"])) if q in om]
        Fc.fixed({q: ("E2" if i < len(jl) - 1 else "E3") for i, q in enumerate(jl)})
        ch = ip(G(6.2, 7.4 - p["jaw"] * 0.5))
        if ch in om:
            Fc.fixed({ch: "E1"})
        # eyes: two small cold teal points (far one dimmer)
        e1, e2 = ip(G(5.0, 1.6)), ip(G(7.6, 1.2))
        if p["eye"] == 1:
            Fc.fixed({e1: "Z2", e2: "Z4"})
        elif p["eye"] == 2:
            Fc.fixed({e1: "Z3", e2: "Z5"})
            FX.put([(e2[0] + 1, e2[1]), (e2[0] + 2, e2[1])], "Z3")
            FX.put([(e2[0] + 3, e2[1])], "Z2")
        elif p["eye"] == 3:            # dimming
            Fc.fixed({e1: "Z1", e2: "Z2"})
        info["eye"] = e2

    # ---------------- staff + hook-lantern
    if p["staff"]:
        SL_ = Ls["StaffBack"] if p["sback"] else Ls["Staff"]
        hang = draw_staff(SL_, st, info, hook=p["lant"] in ("hook", "lying"), floor=floor)
        if p["lant"] == "hook" and hang is not None:
            draw_lantern(Ls["Lantern"], GL, FX, hang, p["lsw"], p["lvl"], fi, info, floor=floor)
        elif p["lant"] == "lying" and hang is not None:
            draw_lantern(Ls["Lantern"], GL, FX, (hang[0] + 2, FLOOR - 3.0), 84, 0, fi, info, floor=floor, chain=1.5)
        # back-hand fingers wrapped over the shaft
        if p["hb_on"] is not None and p["melt"] < 0.35:
            gp = (-d[1], d[0])
            if gp[1] > 0:
                gp = (-gp[0], -gp[1])
            SL_.fixed({ip(madd(hb, (d, k * 1.3 - 1.0), (gp, -0.2))): ("E3" if k else "E4") for k in range(2)})

    # ---------------- front arm (near side, over the staff)
    el_f, iff = sleeve_arm(Ls["FrontArm"], shF, hf, 0, fi, sw, pref=p.get("pref_f", (0.2, 1.0)),
                           grip=d if (p["staff"] and not p.get("hf")) else None, seed=9, show_hand=p["melt"] < 0.35)
    info["reach"].append(("front", iff["reach"]))
    # sleeve cap over the front shoulder
    Fa = Ls["FrontArm"]
    cap = [add(shF, (-4.4, -2.6)), add(shF, (1.8, -3.4)), add(shF, (3.6, 0.2)), add(shF, (2.6, 3.4)), add(shF, (-2.6, 3.6))]
    plate(Fa, cap, "S", bevel=1.8, tilt=(-0.2, -0.35), strength=1.2, ao=0, floor=floor)

    # ---------------- cold rim light on the upper-left silhouette edges (teal sheen, keeps him readable on black)
    for nm2, top_c, left_c in (("Cowl", ("S", 5), ("S", 4)), ("Mantle", ("S", 5), ("S", 4)), ("Torso", ("S", 4), ("S", 4)),
                               ("Robe", ("S", 4), ("S", 3)), ("BackArm", ("S", 3), None), ("FrontArm", ("S", 4), None)):
        L_ = Ls[nm2]
        rim = []
        for (x, y), e in L_.px.items():
            if e[3] is not None or e[0] != "S":
                continue
            if (x, y - 1) not in L_.px:
                rim.append(((x, y), top_c))
            elif left_c and (x - 1, y) not in L_.px and y < hemy - 8:
                rim.append(((x, y), left_c))
        for q, c in rim:
            L_.decal([q], c)

    # ---------------- lantern light: a cold teal rim on the edges of cloth that face the lantern
    lc = info.get("lantern")
    if lc is not None and p["lvl"] >= 1 and p["lant"] == "hook":
        rad = 16 + 6 * max(0, p["lvl"] - 1)
        for nm2 in ("Cowl", "Mantle", "Torso", "Robe", "FrontArm"):
            L_ = Ls[nm2]
            for (x, y), e in list(L_.px.items()):
                if e[3] is not None and not isinstance(e[3], tuple):
                    continue
                dx, dy = lc[0] - (x + .5), lc[1] - (y + .5)
                dist = math.hypot(dx, dy)
                if dist > rad or dist < 1:
                    continue
                sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
                facing = ((x + sx, y) not in L_.px and abs(dx) > abs(dy) * 0.5) or \
                         ((x, y + sy) not in L_.px and abs(dy) > abs(dx) * 0.5)
                if facing and e[0] in ("S", "N"):
                    L_.decal([(x, y)], "Z2" if dist < rad * 0.5 and p["lvl"] >= 2 else "Z1")

    # ---------------- fx
    if p["sweep"]:
        info["hit"] |= blade_sweep(SM, p["sweep"], exclude=info.get("blade", set()))
    if p["glint"] == "blade":
        tp = info["tip"]
        g = madd(tp, (d, -3.0), ((-d[1], d[0]), -2.0))
        g = (g[0], min(g[1], FLOOR - 4))
        star(FX, g)
        info["glint"] = g
    elif p["glint"] == "lantern" and lc is not None:
        star(FX, (lc[0], lc[1] - 1), big=True)
        info["glint"] = lc
    if p["splash"]:
        splash(FX, info, p["splash_at"], p["splash"], fi)
    if p["spray"]:
        spray(FX, info, p["spray"], fi)
    if p["wake"]:
        wake(FX, info, p["wake"], fi)
    if p["burst"] and lc is not None:
        burst(FX, GL, lc, p["burst"], fi)
    if p["hook_flare"] and "top" in info:
        tp = info["top"]
        fwd = (-d[0], -d[1])
        pv2 = (-fwd[1], fwd[0])
        for k, o in enumerate((-2.0, 0.0, 2.0)):
            a0, a1 = 5 + 3 * (k % 2), 16 - 4 * (k % 2)
            seg = line(madd(tp, (fwd, a0), (pv2, o)), madd(tp, (fwd, a1), (pv2, o)))
            for j, q in enumerate(seg):
                FX.put([q], "Z4" if j > len(seg) * 0.6 else "Z3" if j > len(seg) * 0.3 else "N4")
        star(FX, madd(tp, (fwd, 3.0)))
    if p["bflash"]:
        star(FX, p["bflash"], big=True)
    info["hit"] |= info.get("blade", set())
    info["C"], info["Hd"], info["P"] = C, Hd, P
    return Ls, info


# =========================================================================== fx pieces
def blade_sweep(FXL_, keys, exclude=(), pal=SMEAR):
    """keys: [st, ...] old -> new staff poses. Water-bright ghost trail of the oar blade."""
    samples = []
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        aa, ba = a["a"], b["a"]
        while ba - aa > 180:
            ba -= 360
        while ba - aa < -180:
            ba += 360
        for k in range(14):
            t = k / 14
            g = lerp(a["g"], b["g"], t)
            st = dict(g=g, a=aa + (ba - aa) * t, u=a["u"] + (b["u"] - a["u"]) * t, sl=a.get("sl", SL))
            samples.append(st)
    samples.append(keys[-1])
    m = len(samples) - 1
    best = {}
    for i, st in enumerate(samples):
        age = 1 - i / m
        T, d, n, sl = staff_geom(st)
        pv = (-d[1], d[0])
        umin = sl - BL * (0.75 - 0.45 * age)
        u = umin
        while u <= sl + 0.5:
            w = (blade_w(u - (sl - BL)) if u > sl - BL else 1.0) * (0.85 - 0.35 * age)
            v = -w
            while v <= w:
                q = ip((T[0] + d[0] * u + pv[0] * v, T[1] + d[1] * u + pv[1] * v))
                ed = sl - u
                if q not in best or best[q][0] > age:
                    best[q] = (age, ed)
                v += 0.8
            u += 0.6
    hot = set()
    for q, (age, ed) in best.items():
        if q in exclude or not K.inb(*q) or q[1] > FLOOR:
            continue
        if age > 0.25 and ed > 2.5 and int(ed / 2) % 2 == 1:
            continue
        if age > 0.55 and ed > 1.5 and int(ed) % 3 != 0:
            continue
        if age > 0.85 and ed > 1:
            continue
        if age < 0.16:
            c = pal[0] if ed < 3 else pal[1]
        elif age < 0.4:
            c = pal[1] if ed < 3 else pal[2]
        elif age < 0.66:
            c = pal[2]
        else:
            c = pal[3]
        FXL_.put([q], c)
        if age < 0.7:
            hot.add(q)
    return hot


def splash(FX, info, at, stage, fi):
    """Black water erupting where the blade strikes the surface (stage 1 = impact, 2 = falling, 3 = settling)."""
    ix = int(at[0])
    pts = set()
    # a sheet of water thrown up both sides, crests of foam
    for side in (-1, 1):
        for k in range(14):
            h_ = hash01(k, side + 3, 61)
            dx = side * (2 + k * 1.6)
            hmax = (14 - k) * (1.05 if side > 0 else 0.8)
            if stage == 1:
                hh = hmax * (0.7 + 0.3 * h_)
            elif stage == 2:
                hh = hmax * 0.45 * (0.6 + 0.4 * h_)
            else:
                hh = max(0.0, hmax * 0.15 * h_)
            x = ix + dx
            for y in range(int(FLOOR - hh), FLOOR + 1):
                if stage >= 2 and (y + k) % 3 == 0:
                    continue
                c = "N3" if y > FLOOR - hh + 2 else "N5" if stage == 1 else "N4"
                FX.put([(int(x), y)], c)
                FX.put([(int(x) + side, y)], "N2" if c == "N3" else c)
                pts.add((int(x), y))
    # droplets
    for k in range(22):
        side = -1 if k % 2 else 1
        a = -math.pi * (0.15 + 0.3 * hash01(k, 7, 62))
        r = (5 + 18 * hash01(k, 8, 63)) * (0.8 if stage == 1 else 1.3 if stage == 2 else 1.6)
        x = ix + side * math.cos(a) * r * 1.2
        y = FLOOR - 4 + math.sin(a) * r * (1.0 if stage == 1 else 0.7) + (0 if stage == 1 else 2.5 * stage ** 1.5)
        q = ip((x, min(FLOOR, y)))
        if stage == 3 and k % 2:
            continue
        FX.put([q], "N5" if k % 3 == 0 else "N4" if k % 3 == 1 else "Z3")
        pts.add(q)
    # surface ring
    for dx in range(-26, 27):
        if abs(dx) > 6 and hash01(dx, stage, 64) < 0.55:
            FX.put([(ix + dx, FLOOR)], "N4" if abs(dx) < 18 else "N3")
    info["hit"] |= pts
    info["impact"] = (ix, FLOOR)


def spray(FX, info, stage, fi):
    """Droplets flung ahead of a low sweep, skimming the surface."""
    tp = info.get("tip")
    if tp is None:
        return
    for k in range(16):
        r = 4 + 20 * hash01(k, stage, 71)
        x = tp[0] - r * 0.9 * (1 if stage == 1 else 1.6)
        y = min(FLOOR, tp[1] + (hash01(k, 3, 72) - 0.6) * 14)
        FX.put([ip((x, y))], "N5" if k % 3 == 0 else "N4" if k % 3 == 1 else "Z3")
    for dx in range(-30, 4):
        if hash01(dx, stage, 73) < 0.5:
            FX.put([(int(tp[0]) + dx, FLOOR)], "N4")


def wake(FX, info, amt, fi):
    """V-wake of ripples streaming back from the hem while he glides."""
    pl = info.get("pool")
    if not pl:
        return
    x0 = pl[0]
    for k in range(4):
        ph = (fi * 1.7 + k * 3.1) % 12
        x = x0 - 2 - ph * 2.2 * amt
        ln_ = 3 + int(ph * 0.4)
        col = "N5" if ph < 3 else "N4" if ph < 7 else "N3"
        FX.put([(int(x) - j, FLOOR - (1 if j < ln_ // 2 and ph < 5 else 0)) for j in range(ln_)], col)
    fr = pl[1]
    for j in range(3):
        FX.put([(fr + 1 + j, FLOOR - (1 if j == 0 else 0))], "N4" if (fi + j) % 2 else "N5")


def burst(FX, GL, c, stage, fi):
    """Lantern flare burst: a hard teal-white bloom + rays + soul motes spat outward."""
    R = (12.0, 16.0, 9.0)[min(stage, 3) - 1]
    for q in mask_disc(c, R, R):
        if not K.inb(*q):
            continue
        r = math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) / R
        GL.put([q], "GA3" if r < 0.5 else "GA2" if r < 0.8 else "GA1")
    if stage == 1:
        for q in mask_disc(c, 3.2, 3.2):
            FX.put([q], "Z5")
        for k in range(8):
            a = k * math.pi / 4 + 0.2
            ln_ = 12 if k % 2 == 0 else 8
            FX.put(line(add(c, (math.cos(a) * 4, math.sin(a) * 4)), add(c, (math.cos(a) * ln_, math.sin(a) * ln_))),
                   "Z4" if k % 2 == 0 else "Z3")
    elif stage == 2:
        for q in mask_disc(c, 1.8, 1.8):
            FX.put([q], "Z5")
        for k in range(10):
            a = 2 * math.pi * k / 10 + 0.3
            r0 = 9 + 3 * hash01(k, 1, 91)
            FX.put([ip(add(c, (math.cos(a) * r0, math.sin(a) * r0)))], "Z4")
            FX.put([ip(add(c, (math.cos(a) * (r0 + 1.5), math.sin(a) * (r0 + 1.5))))], "Z2")
    else:
        for k in range(8):
            a = 2 * math.pi * k / 8
            r0 = 13 + 2 * hash01(k, 2, 92)
            FX.put([ip(add(c, (math.cos(a) * r0, math.sin(a) * r0)))], "Z2")


# =========================================================================== death: the empty robe
def puddle(L, FX, cx, w, fi, floor=FLOOR):
    """Spreading black-water puddle on the surface (2-4 rows), foam-lit rim."""
    pix = {}
    for x in range(int(cx - w / 2), int(cx + w / 2) + 1):
        t = abs(x + .5 - cx) / (w / 2)
        if t > 1:
            continue
        h_ = int(round((1 - t * t) * 3.2)) + 1
        for k in range(h_):
            y = floor - k
            pix[(x, y)] = "N1" if k < h_ - 1 else "N3" if (x + fi) % 5 else "N4"
    L.fixed({q: c for q, c in pix.items() if K.inb(*q)})
    for side in (-1, 1):
        for j in range(3):
            x = int(cx + side * (w / 2 + 2 + j * 3 + (fi % 3)))
            FX.put([(x, floor)], "N4" if j == 0 else "N3")
    return set(pix)


def draw_heap(p, fi, sw, Ls, GL, SM, FX, info):
    """The robe collapsed empty into a spreading black puddle; cowl cloth lying on top; the oar fallen."""
    Rb, Cw = Ls["Robe"], Ls["Cowl"]
    cx = p["P"][0]
    hh = p["heap"]                          # mound height
    pw = p["puddle"]
    info["pool"] = (int(cx - pw / 2), int(cx + pw / 2))
    puddle(Rb, FX, cx + 2, pw, fi)
    # cloth mound: low, sleek drape with a couple of long folds, sinking into the water
    wl, wr = 17.0 + (8 - hh) * 0.8, 14.0 + (8 - hh) * 0.6
    pts = [(cx - wl, FLOOR - 0.5)]
    for i in range(9):
        t = i / 8
        x = cx - wl + (wl + wr) * t
        bump = math.sin(t * math.pi) ** 0.8 * hh + 1.4 * math.sin(t * 9.0) * (hh / 8)
        pts.append((x, FLOOR - 1 - bump))
    pts.append((cx + wr, FLOOR - 0.5))
    m = plate(Rb, pts, "S", bevel=3.0, tilt=(-0.1, -0.2), strength=1.2,
              fold=lambda x, y: (0.6 * math.sin((x - cx) * 0.5), 0.0), bias=-1)
    wet = [q for q in m if q[1] >= FLOOR - 1 - hash01(q[0], 2, 5) * 2]
    remat(Rb, wet, "N", -1)
    # the empty cowl, fallen forward on the front of the heap
    hc = (cx + 7.0, FLOOR - 2.2 - hh * 0.6)
    G0 = basis(hc, dirv(-90 + 72))
    G = lambda a, b: G0(a * HS, b * HS)
    hood = [G(-6.6, 8.0), G(-8.0, 2.0), G(-7.6, -2.6), G(-9.0, -7.2), G(-5.2, -8.4), G(-1.4, -9.6), G(2.0, -9.6),
            G(5.4, -7.6), G(7.8, -4.4), G(9.4, -1.4), G(8.4, 2.8), G(6.4, 6.6), G(3.0, 8.4), G(-2.0, 8.8)]
    hm = {q for q in poly_mask(hood) if q[1] <= FLOOR}
    Cw.paint(n_plate(hm, 3.0, (-0.15, -0.3), 1.3), "S", 0, ao=0)
    op = [G(3.0, -1.4), G(8.0, -0.6), G(7.0, 4.0), G(3.4, 5.4)]
    om = poly_mask(op) & hm
    Cw.fixed({q: "S0" for q in om})
    Cw.decal([q for q in polyline(curve([G(-5.0, -7.0), G(-1.0, -9.0), G(5.0, -6.6)], n=5)) if q in hm], ("S", 4))
    info["head"] = hm
    # fallen oar + dark lantern
    st = p["st"]
    SL_ = Ls["StaffBack"]
    hang = draw_staff(SL_, st, info, hook=True)
    if hang is not None and p["lant"] == "hook":
        draw_lantern(Ls["Lantern"], GL, FX, hang, p["lsw"], 0, fi, info)
    elif hang is not None:
        draw_lantern(Ls["Lantern"], GL, FX, (hang[0] + 2, FLOOR - 3.0), 84, 0, fi, info, chain=1.5)
    info["robe"] = m
    info["C"], info["Hd"], info["P"] = p["P"], hc, p["P"]
    return Ls, info
