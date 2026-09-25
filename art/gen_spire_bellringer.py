#!/usr/bin/env python3
"""Mini-boss generator -- THE BELL-RINGER of the Tempest Spire's Windmill Hamlet.

    python3 art/gen_spire_bellringer.py              full build (Aseprite): bellringer + fx_sp_toll + meta + previews
    python3 art/gen_spire_bellringer.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_spire_bellringer.py --only swing,slam --preview   quick iteration (writes *_wip previews)

Outputs
    art/bellringer.aseprite, assets/bellringer.png/.json     192x128, faces RIGHT, feet on the bottom row, anchor [96,128]
    assets/bellringer_meta.json                               hurtbox / attacks (windows) / spawn / telegraph
    art/fx_sp_toll.aseprite, assets/fx_sp_toll.png/.json      64x64, 8 frames, tag sp_toll, centred toll burst
    art/previews/bellringer.png (3x, one row per tag), bellringer_hitbox.png, bellringer_closeup.png (5x, with the
    player for scale), fx_sp_toll.png

A towering, gaunt hollow sexton (~84px, 3.3x the player): hunched, long-limbed, tattered sackcloth cowl over a small
pale hollow face, iron collar with broken links, bell-rope sash, a heavy chain wound round his forearm to a cracked
verdigris church bell.  Method: enemy_kit.py (normal-field shading, per-layer sel-out outlines), cold storm palette.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc,  # noqa: E402
                       poly_mask, n_plate, n_dome, norm3, dirv, basis)

W, H = 192, 128
K.setup(W, H)
FLOOR = H - 1
AX = 96
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None

# ---------------------------------------------------------------- palette (runtime additions, storm-cold)
NEW = {
    # sackcloth, storm-soaked (cold grey-brown)
    "S": ["#09090d", "#121318", "#1b1c23", "#272830", "#363740", "#4b4b52"],
    # hollow flesh: bloodless, cold pale
    "E": ["#17181e", "#2c2e36", "#484b55", "#6b6f79", "#9296a0", "#c1c4c4"],
    # cold wrought iron (top = wet glint)
    "X": ["#08090d", "#12141a", "#1e2129", "#2e323c", "#474c58", "#7d8595"],
    # bell bronze (top step = worn gold)
    "U": ["#120c0a", "#241811", "#3a2819", "#553b21", "#76552b", "#ae8a45"],
    # verdigris patina
    "N": ["#0a1413", "#11231f", "#1a352f", "#264c42", "#386a59", "#5a917a"],
    # hemp rope
    "H": ["#18150f", "#2c271c", "#433b2b", "#5f5540", "#7f7458", "#a49a7c"],
    # cold storm light (fixed)
    "Z": ["#16213a", "#2a4264", "#4f739e", "#8cb1d6", "#cfe4f5", "#f6fbff"],
}
for _r, _cols in NEW.items():
    K.RAMP[_r] = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        K.RAMP[_r].append(_k)
K.SHINY.update({"X": 0.93, "U": 0.9})
RGBA = K.RGBA
SMEAR = ["Z5", "Z4", "Z3", "Z1"]

LAYERS = ["SmearBack", "BellBack", "ChainBack", "Cloak", "BackArm", "BackLeg", "FrontLeg", "Body", "Cowl", "Head",
          "Collar", "FrontArm", "Smear", "Chain", "Bell", "FX"]
FXL = {"SmearBack", "Smear", "FX"}

# bell geometry (local: u along the axis from the crown top, v across)
LIP_U = 31.0
UC = 15.0            # 'bell centre' along the axis
LOOP_U = -2.4        # canon loop centre
LOOP_D = UC - LOOP_U  # centre -> loop distance
HEAD_DROP = 1.0      # head hangs below the hump
HS = 0.88            # head scale (small, menacing)
HUNCH = 2.5          # extra forward lean of chest + head on standing poses


# =========================================================================== helpers
def curve(pts, n=12):
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


def tube(L, pts, radii, mat, bias=0, ao=1, flat=1.0, clip_floor=True):
    nm = n_tube(pts, radii, flat)
    if clip_floor:
        nm = {q: v for q, v in nm.items() if q[1] <= FLOOR}
    return L.paint(nm, mat, bias, ao)


def plate(L, pts, mat, bevel=1.6, tilt=(0, 0), strength=1.1, fold=None, bias=0, ao=1):
    m = {q for q in poly_mask(pts) if q[1] <= FLOOR}
    L.paint(n_plate(m, bevel, tilt, strength, fold), mat, bias, ao)
    return m


def remat(L, pts, mat, dl=0):
    """Change material but keep the shading (patina, stains)."""
    for q in pts:
        e = L.px.get(q)
        if e is not None and e[3] is None:
            e[0] = mat
            e[2] += dl


def shade(L, pts, dl):
    for q in pts:
        e = L.px.get(q)
        if e is not None:
            e[2] += dl


def madd(p, *vs):
    x, y = p
    for v, k in vs:
        x += v[0] * k
        y += v[1] * k
    return (x, y)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rag(x0, x1, y, fi, seed, depth=3.0, n=None, sway=0.0):
    """Ragged hem points from x1 back to x0 (tatters alternate long/short)."""
    n = n or max(3, int(abs(x1 - x0) / 2.2))
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.35 + 0.9 * hash01(i, seed, 3)) if i % 2 == 0 else -0.6
        pts.append((x + sway * (0.3 + 0.7 * t), y + d))
    return pts


# =========================================================================== the bell
def hw(u):
    if u < 0:
        return 0.0
    if u < 3.0:
        return 7.7 * math.sqrt(max(0.0, 1 - (1 - u / 3.0) ** 2))
    return 7.7 + 0.9 * (u - 3) / 28 + 6.4 * smoothstep(12, 30.5, u) ** 1.8


def bell_frame(bc, ang):
    a = dirv(ang)
    vd = (a[1], -a[0])
    top = (bc[0] - a[0] * UC, bc[1] - a[1] * UC)
    return a, vd, top


def bell_local(q, a, vd, top):
    x, y = q[0] + .5 - top[0], q[1] + .5 - top[1]
    return x * a[0] + y * a[1], x * vd[0] + y * vd[1]


def bell_mask(bc, ang, mouth=True):
    a, vd, top = bell_frame(bc, ang)
    R = 22
    body, loop, mo = set(), set(), set()
    hl = hw(LIP_U)
    for y in range(int(bc[1] - R), int(bc[1] + R) + 1):
        for x in range(int(bc[0] - R), int(bc[0] + R) + 1):
            u, v = bell_local((x, y), a, vd, top)
            if 0 <= u <= LIP_U and abs(v) <= hw(u):
                body.add((x, y))
            elif mouth and u > LIP_U and ((u - LIP_U) / 2.3) ** 2 + (v / hl) ** 2 <= 1.0:
                mo.add((x, y))
            d = math.hypot(u - LOOP_U, v * 1.15)
            if u < 0.8 and 1.0 <= d <= 2.9:
                loop.add((x, y))
    return body, loop, mo


def draw_bell(L, FX, bc, ang, fi, mouth=True, clap=0.0, crack=True, ground=False):
    """Bronze church bell, crown -> lip along `ang` (90 = hanging mouth-down). Returns (all pixels, bc, loop pt)."""
    if ground:                                  # rest the lowest pixel on the floor
        body, loop, mo = bell_mask(bc, ang, mouth)
        my = max(q[1] for q in body | mo)
        bc = (bc[0], bc[1] + FLOOR - my)
    body, loop, mo = bell_mask(bc, ang, mouth)
    a, vd, top = bell_frame(bc, ang)
    nm = {}
    loc = {}
    for q in body:
        u, v = bell_local(q, a, vd, top)
        loc[q] = (u, v)
        h = max(hw(u), 0.5)
        dh = (hw(u + 0.5) - hw(u - 0.5))
        lat = max(-1.0, min(1.0, v / h))
        nz = math.sqrt(max(0.04, 1 - lat * lat))
        nu = -dh * nz * 0.9
        nx = lat * vd[0] + nu * a[0]
        ny = lat * vd[1] + nu * a[1]
        nm[q] = norm3(nx, ny, nz)
    L.paint(nm, "U", 0, ao=0)
    # ridges: crown shoulder band, inscription band, sound-bow ridges, lip
    for q, (u, v) in loc.items():
        side = v / max(hw(u), 1)
        if 5.0 <= u < 5.9 or 8.3 <= u < 9.2 or 26.2 <= u < 27.1 or 28.4 <= u < 29.2:
            shade(L, [q], +1)
        elif 5.9 <= u < 6.8 or 9.2 <= u < 10.1 or 27.1 <= u < 27.9 or 29.2 <= u < 29.9:
            shade(L, [q], -1)
        if 6.8 <= u < 8.3 and int(v + 20) % 2 == 0 and side < 0.2 and hash01(int(v), 1, 7) < 0.7:
            L.decal([q], ("G", 3 if side < -0.3 else 2))          # worn inscription
        if u >= 30.0 and side < 0.35:
            L.decal([q], ("U", 5 if side < -0.2 else 4))          # worn-gold lip
    # verdigris: crown cap + drips running down from the bands
    pat = []
    for q, (u, v) in loc.items():
        col = int(math.floor(v / 1.6))
        drip1 = 9.5 + 3 + 13 * hash01(col, 3, 11) ** 1.6
        drip2 = 29.5 + 1.5 * hash01(col, 4, 11)
        up2 = 27.0 - 5 * hash01(col, 5, 11) ** 2
        if u < 4.6 and hash01(q[0] // 2, q[1] // 2, 12) < 0.8:
            pat.append(q)
        elif 9.6 <= u < drip1 and hash01(col, 6, 11) < 0.62:
            pat.append(q)
        elif up2 <= u < 26.0 and hash01(col, 7, 11) < 0.35:
            pat.append(q)
        elif u > drip2 and v / max(hw(u), 1) > 0.25:
            pat.append(q)
    remat(L, pat, "N")
    # the crack in the rim
    if crack:
        pts = [(LIP_U + 0.4, 5.6), (27.5, 4.6), (25.0, 5.4), (22.4, 4.2), (19.6, 4.6)]
        fpts = [add(top, (a[0] * u + vd[0] * v, a[1] * u + vd[1] * v)) for u, v in pts]
        cr = [q for q in polyline(fpts) if q in body]
        L.decal(cr, "OUT")
        L.decal([(q[0] - 1, q[1]) for q in cr[:len(cr) // 2] if (q[0] - 1, q[1]) in body and (q[0] - 1, q[1]) not in cr],
                ("U", 4))
    # canon loop
    ln = {}
    for q in loop:
        u, v = bell_local(q, a, vd, top)
        ln[q] = norm3((v * vd[0] + (u - LOOP_U) * a[0]) * 0.4, (v * vd[1] + (u - LOOP_U) * a[1]) * 0.4, 0.8)
    L.paint(ln, "U", -1, ao=0)
    remat(L, [q for q in loop if hash01(q[0], q[1], 13) < 0.5], "N")
    # mouth: dark interior seen from a little below, bronze near rim, iron clapper
    allp = body | loop
    if mouth and mo:
        rim, inside = [], []
        for q in mo:
            u, v = bell_local(q, a, vd, top)
            e = ((u - LIP_U) / 2.3) ** 2 + (v / hw(LIP_U)) ** 2
            (rim if e > 0.55 else inside).append(q)
        L.fixed({q: "X0" for q in inside})
        L.fixed({q: ("U2" if bell_local(q, a, vd, top)[1] < 0 else "U1") for q in rim})
        cu = LIP_U + 1.2
        g = max(0.0, 1 - abs(a[1])) * (hw(LIP_U) - 3.5)
        cc = add(top, (a[0] * cu + vd[0] * clap, a[1] * cu + vd[1] * clap + g))
        cm = {q: v for q, v in n_dome(cc, 2.3, 2.3).items() if q[1] <= FLOOR}
        L.paint(cm, "X", 0, ao=0)
        allp |= mo | set(cm)
    loop_pt = add(top, (a[0] * (LOOP_U - 1.2), a[1] * (LOOP_U - 1.2)))
    return allp, bc, loop_pt, (a, vd, top)


# =========================================================================== chain
def chain_path(a, b, sag=0.0, n=16):
    pts = []
    for i in range(n + 1):
        t = i / n
        y = a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)
        pts.append((a[0] + (b[0] - a[0]) * t, min(FLOOR - 0.5, y)))
    return pts


def draw_chain(L, pts, phase=0.0):
    """Heavy forged chain along a polyline: alternating face links (rings) and edge links (bars)."""
    seg = []
    tot = 0.0
    for p0, p1 in zip(pts, pts[1:]):
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        seg.append((p0, p1, tot, d))
        tot += d
    pix = {}
    s = phase % 5.0
    k = 0
    while s < tot:
        for p0, p1, t0, d in seg:
            if t0 <= s <= t0 + d:
                t = (s - t0) / max(d, 1e-6)
                c = lerp(p0, p1, t)
                dx, dy = (p1[0] - p0[0]) / max(d, 1e-6), (p1[1] - p0[1]) / max(d, 1e-6)
                break
        if k % 2 == 0:       # face link: a ring 5 long, 3 wide
            for q in mask_disc(c, 2.3 * max(abs(dx), 0.55) + 0.6 * abs(dy), 2.3 * max(abs(dy), 0.55) + 0.6 * abs(dx)):
                ox, oy = q[0] + .5 - c[0], q[1] + .5 - c[1]
                u = ox * dx + oy * dy
                v = -ox * dy + oy * dx
                if abs(u) <= 2.4 and abs(v) <= 1.6 and not (abs(u) < 1.0 and abs(v) < 0.7):
                    lit = (u * -0.6 + v * -0.8) if False else (ox * -0.55 + oy * -0.7)
                    pix[q] = "X4" if lit > 0.6 else "X3" if lit > -0.4 else "X2"
        else:                # edge link: a bar seen edge-on
            for q in line((c[0] - dx * 2.0, c[1] - dy * 2.0), (c[0] + dx * 2.0, c[1] + dy * 2.0)):
                pix.setdefault(q, "X3" if (q[0] + q[1]) % 2 else "X2")
        s += 2.6
        k += 1
    pix = {q: c for q, c in pix.items() if q[1] <= FLOOR}
    L.fixed(pix)
    return set(pix)


# =========================================================================== bell sweep smear
def bell_sweep(FXL, keys, exclude=(), taper=0.62, pal=SMEAR, min_age=0.0):
    """keys: [(hand, ang, d), ...] old -> new (d = hand-to-loop distance). Ghost trail of the bell's far side."""
    keys = [list(k) for k in keys]
    for i in range(1, len(keys)):
        while keys[i][1] - keys[i - 1][1] > 180:
            keys[i][1] -= 360
        while keys[i][1] - keys[i - 1][1] < -180:
            keys[i][1] += 360
    hands = curve([k[0] for k in keys], n=10)
    m = len(hands) - 1
    best = {}
    for i in range(m + 1):
        t = i / m
        seg = t * (len(keys) - 1)
        j = min(len(keys) - 2, int(seg))
        f = seg - j
        ang = keys[j][1] + (keys[j + 1][1] - keys[j][1]) * f
        d = keys[j][2] + (keys[j + 1][2] - keys[j][2]) * f
        h = hands[i]
        age = 1 - t
        a = dirv(ang)
        vd = (a[1], -a[0])
        base = d + (-LOOP_U)
        umin = 13.0 + age * taper * 20
        u = umin
        while u <= 33.5:
            half = hw(min(u, LIP_U)) * 0.95
            v = -half
            while v <= half:
                q = ip((h[0] + a[0] * (base + u) + vd[0] * v, h[1] + a[1] * (base + u) + vd[1] * v))
                ed = 33.5 - u
                if q not in best or best[q][0] > age:
                    best[q] = (age, ed)
                v += 0.8
            u += 0.7
    hot = set()
    for q, (age, ed) in best.items():
        if q in exclude or not K.inb(*q) or q[1] > FLOOR or age < min_age:
            continue
        if age > 0.3 and ed > 2.5 and int(ed / 2) % 2 == 1:
            continue
        if age > 0.82 and ed > 2:
            continue
        if age < 0.18:
            c = pal[0] if ed < 3 else pal[1]
        elif age < 0.42:
            c = pal[1] if ed < 2.5 else pal[2]
        elif age < 0.68:
            c = pal[2]
        else:
            c = pal[3]
        FXL.put([q], c)
        if age < 0.6:
            hot.add(q)
    return hot


# =========================================================================== the giant
NEU = dict(P=(92.0, 78.0), C=(99.0, 56.0), Hd=(111.0, 52.5), hup=(0.45, -1), fb=(82.0, 127), ff=(104.0, 127),
           kb=None, kf=None, kneel=False, hf=(119.0, 80.0), hb=(84.0, 97.0), bc=None, ba=90.0, cd=7.0, sag=0.0,
           ground=False, mouth=True, clap=0.0, bl="Bell", sweep=None, eye=1, glint=None, wind=0.0, impact=0, vib=0,
           dust=0, scrape=0, fist=False, flash=None, grip2=False, shake=(0, 0), hood=0.0, fallen=0.0, toll=0)


def P_(**kw):
    d = dict(NEU)
    d.update(kw)
    return d


def hang(h, ang, d):
    a = dirv(ang)
    return (h[0] + a[0] * (d + LOOP_D), h[1] + a[1] * (d + LOOP_D))


def gleg(L, hip, foot, bias, knee=None, kneel=False, seed=0):
    ank = (foot[0], foot[1] - 2.4)
    kn = knee or ik(hip, ank, 24.0, 24.5, (1, -0.2))
    # gaunt thigh -> knobbed knee -> long bare shin
    tube(L, [hip, lerp(hip, kn, 0.45), kn], [4.0, 3.3, 2.5], "S", bias)
    th = sub(kn, hip)
    tl = math.hypot(*th) or 1
    tn = (th[0] / tl, th[1] / tl)
    tp = (-tn[1], tn[0])
    for t in (0.35, 0.55, 0.75):                   # spiral rag wraps
        c = lerp(hip, kn, t)
        L.decal(line(madd(c, (tp, -3.4), (tn, -1.2)), madd(c, (tp, 3.4), (tn, 1.2))), ("S", 1 + bias))
    tube(L, [kn, lerp(kn, ank, 0.25), lerp(kn, ank, 0.75), ank], [2.6, 2.5, 1.7, 1.4], "E", bias)
    L.paint({q: v for q, v in n_dome(add(kn, (0.6, 0.1)), 2.6, 2.4).items() if q[1] <= FLOOR}, "E", bias, ao=0)
    d = sub(ank, kn)
    l = math.hypot(*d) or 1
    dn = (d[0] / l, d[1] / l)
    pv = (-dn[1], dn[0])
    # dark rag bindings round the lower shin / ankle
    for t in (0.66, 0.75, 0.84):
        c = lerp(kn, ank, t)
        L.decal(line(madd(c, (pv, -2.2), (dn, 0.6)), madd(c, (pv, 2.2), (dn, -0.6))), ("S", 2 + bias))
    fx_, fy = foot
    if kneel:
        sole = [(fx_ - 7.0, fy + 1), (fx_ - 7.5, fy - 1.2), (fx_ - 1.0, fy - 2.8), (fx_ + 1.5, fy - 2.4), (fx_ + 1.8, fy + 1)]
    else:
        sole = [(fx_ - 2.4, fy + 1), (fx_ - 2.6, fy - 2.4), (fx_ - 0.8, fy - 3.8), (fx_ + 2.0, fy - 2.6), (fx_ + 6.4, fy - 1.0),
                (fx_ + 7.2, fy + 1)]
    fm = plate(L, sole, "E", bevel=1.0, tilt=(0, -0.3), bias=bias)
    L.decal([q for q in fm if q[0] < fx_ + 2.5], ("S", 2 + bias))                   # foot wraps
    if not kneel:
        L.decal([(int(fx_ + 4.2), int(fy))], ("E", 1 + bias))
    return kn


def garm(L, sh, hand, bias, chain=False, pref=(-1, 0.6), fist=False, sleeve_seed=0, fi=0, sw=0.0):
    if hand[1] < sh[1] - 8:                     # raised: elbow flares forward/out
        pref = (1.0, 0.1)
    elif hand[0] < sh[0] - 4:                   # reaching back: elbow hangs down
        pref = (0.35, 1.0)
    el = ik(sh, hand, 20.0, 21.0, pref)
    tube(L, [sh, lerp(sh, el, 0.4), el], [3.6, 3.0, 2.5], "S", bias)
    L.paint({q: v for q, v in n_dome(el, 2.0, 2.0).items() if q[1] <= FLOOR}, "E", bias, ao=0)
    wr = lerp(el, hand, 0.84)
    tube(L, [el, lerp(el, hand, 0.35), wr], [2.5, 2.4, 1.7], "E", bias)
    d = sub(wr, el)
    l = math.hypot(*d) or 1
    dn = (d[0] / l, d[1] / l)
    pv = (-dn[1], dn[0])
    # rag strip tied at the elbow
    rg = line(madd(el, (pv, -2.4), (dn, -0.6)), madd(el, (pv, 2.4), (dn, 0.8)))
    tat = [madd(el, (pv, -2.6), (dn, -1.0)), madd(el, (pv, 2.6), (dn, -1.0))]
    for k in range(4):
        tat.append(madd(el, (pv, 2.6 - k * 1.7), (dn, 1.0 + 2.6 * hash01(k, sleeve_seed, fi // 3) * (k % 2 == 0))))
    plate(L, tat, "S", bevel=0.8, bias=bias - 1, ao=0)
    if chain:     # heavy chain wound round the forearm: dark iron links on pale skin
        for k in range(4):
            t = 0.28 + k * 0.17
            c = lerp(el, wr, t)
            a0, a1 = madd(c, (pv, -2.8), (dn, -1.4)), madd(c, (pv, 2.8), (dn, 1.4))
            seg = line(a0, a1)
            pix = {}
            for j, q in enumerate(seg):
                pix[q] = "X1" if j % 3 == 1 else ("X4" if j < len(seg) // 2 else "X3")
                pix[(q[0] + (1 if abs(dn[1]) > abs(dn[0]) else 0), q[1] + (0 if abs(dn[1]) > abs(dn[0]) else 1))] = "X2"
            L.fixed(pix)
        cf = lerp(el, wr, 0.97)
        L.fixed({q: "X2" for q in line(madd(cf, (pv, -2.4)), madd(cf, (pv, 2.4)))})
    r = 3.0 if fist else 2.6
    L.paint({q: v for q, v in n_dome(hand, r, r * 0.95, tilt=(-0.1, -0.1)).items() if q[1] <= FLOOR}, "E", bias, ao=0)
    if fist:      # knuckles
        for k in range(3):
            L.decal([ip((hand[0] + 1.6, hand[1] - 1.4 + k * 1.4))], ("E", 5 + bias))
    return el


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, SM, SMB = FXLayer("FX"), FXLayer("Smear"), FXLayer("SmearBack")
    Ls["FX"], Ls["Smear"], Ls["SmearBack"] = FX, SM, SMB
    info = {"hit": set()}
    P, C, Hd = p["P"], p["C"], p["Hd"]
    hx = 0.0
    if not p["kneel"]:
        P, C = (P[0], P[1] - 1.5), (C[0] + HUNCH, C[1] - 0.8)
        hx = HUNCH * 1.5
    Hd = (Hd[0] - 0.5 + hx, Hd[1] + 3.5 + HEAD_DROP * (1 - abs(p["hup"][0]) * 0.4) + hx * 0.4)
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = basis(P, upv)
    G0 = basis(Hd, p["hup"])
    G = lambda a, b: G0(a * HS, b * HS)
    shF, shB = F(4.4, -ln + 2.8), F(-4.6, -ln + 3.4)
    hf, hb = p["hf"], p["hb"]
    cs = sw * 0.7 + p["wind"] * 0.8

    # ---------------- bell + chain
    bc = p["bc"] if p["bc"] is not None else hang(hf, p["ba"], p["cd"])
    BL = Ls["BellBack"] if p["bl"] == "BellBack" else Ls["Bell"]
    CL = Ls["ChainBack"] if p["bl"] == "BellBack" else Ls["Chain"]
    bpix, bc, loop_pt, bfr = draw_bell(BL, FX, bc, p["ba"], fi, mouth=p["mouth"], clap=p["clap"], ground=p["ground"])
    info["bell"] = bc
    info["bell_px"] = bpix
    info["hit"] |= bpix
    cpts = chain_path(hf, loop_pt, p["sag"])
    cpx = draw_chain(CL, cpts, phase=fi * 0.9)
    if p["sweep"] or p["impact"]:
        info["hit"] |= cpx
    # long fingers closed over the chain
    for L_, h_ in ((CL, hf),) + (((CL, hb),) if p["grip2"] else ()):
        L_.fixed({ip((h_[0] - 1.4, h_[1] + 1.2)): "E3", ip((h_[0], h_[1] + 1.8)): "E4", ip((h_[0] + 1.4, h_[1] + 1.2)): "E3",
                  ip((h_[0] + 1.8, h_[1] - 0.2)): "E4"})

    # ---------------- long tattered cloak down the back
    Ck = Ls["Cloak"]
    hem = 25.0 - max(0.0, P[1] + 25.0 - (FLOOR - 5.0)) if not p["kneel"] else 20.0
    bx = -14.0 - cs * 1.4
    cl = [F(-7.6, -ln - 1.6), F(-2.0, -ln - 4.4), F(2.4, -ln - 2.4), F(-1.0, -ln + 8.0), F(-4.0, -2.0),
          F(-5.0 - cs * 0.3, hem - 1.0)] + \
        [F(x, y) for x, y in rag(bx, -5.0 - cs * 0.3, hem, fi // 3, 71, depth=4.5, sway=0)] + \
        [F(bx - 3.0 - cs * 0.6, hem - 6.0), F(bx - 1.0 - cs * 0.4, -8.0), F(-11.6, -ln + 6.0)]
    cm = {q for q in poly_mask(cl) if q[1] <= FLOOR}
    Ck.paint(n_plate(cm, 4.5, (0.0, 0.0), 1.1,
                     fold=lambda x, y: (0.75 * math.sin((x - P[0] + cs) * 0.7 + y * 0.05) *
                                        min(1.0, max(0.0, (y - C[1]) / 18)), 0)), "S", -1, ao=0)

    # ---------------- back arm
    garm(Ls["BackArm"], shB, hb, -1, pref=(-1, 0.7), sleeve_seed=5, fi=fi, sw=sw)

    # ---------------- legs
    hB, hF = F(-2.4, 1.0), F(2.4, 1.0)
    info["knee_b"] = gleg(Ls["BackLeg"], hB, p["fb"], -1, p["kb"], p["kneel"])
    info["knee_f"] = gleg(Ls["FrontLeg"], hF, p["ff"], 0, p["kf"], p["kneel"])

    # ---------------- body: gaunt pale ribcage, rag loincloth, bell-rope sash
    Bd = Ls["Body"]
    rib = [F(-6.0, -ln + 1.0), F(4.0, -ln + 0.0), F(7.4, -ln + 6.0), F(6.8, -ln + 13.0), F(4.4, -5.0), F(1.4, -1.0),
           F(-4.0, -1.0), F(-6.6, -10.0)]
    rm = plate(Bd, rib, "S", bevel=4.0, tilt=(-0.1, -0.1), strength=1.25)
    # a torn gap in the tunic baring the hollow ribcage
    tear = [F(1.2, -ln + 3.0), F(6.6, -ln + 4.6), F(6.4, -ln + 12.0), F(4.6, -7.0), F(2.6, -ln + 13.0), F(0.4, -ln + 8.0)]
    tm = {q for q in poly_mask(tear) if q in rm}
    remat(Bd, tm, "E", 0)
    for k in range(4):
        y = -ln + 5.4 + k * 2.3
        Bd.decal([q for q in line(F(1.6, y + 0.8), F(7.0, y - 0.3 + k * 0.2)) if q in tm], ("E", 1))
    Bd.decal([q for q in line(F(4.4, -4.6), F(1.8, -2.0)) if q in rm], ("S", 1))
    sk_sw = sw * 0.5 + p["wind"] * 0.4
    skirt = [F(-6.4, -3.4), F(5.4, -3.6), F(6.8, 4.0)] + \
        [F(7.4 - 15.6 * t + sk_sw * t, 14.0 + (7.0 * hash01(i, 21, fi // 3) if i % 2 == 0 else 0.5))
         for i, t in enumerate([j / 8 for j in range(9)])] + [F(-7.4, 4.0)]
    skm = plate(Bd, skirt, "S", bevel=3.0, tilt=(-0.1, 0.0), strength=1.0,
                fold=lambda x, y: (0.6 * math.sin((x - P[0]) * 1.1 + y * 0.1), 0))
    info["torso"] = rm | skm
    tube(Bd, [F(-5.8, -3.6), F(0.0, -4.2), F(5.2, -3.8)], [1.1, 1.2, 1.1], "H", 0, ao=1)          # rope belt
    # bell-rope sash across the chest, frayed end with a faded sally
    rope = curve([F(-3.6, -ln + 1.6), F(1.0, -ln + 8.0), F(4.4, -ln + 14.0), F(5.2, -4.0)], n=6)
    tube(Bd, rope, [1.3] * len(rope), "H", 0)
    for j, q in enumerate(polyline(rope)):
        if j % 3 == 0:
            Bd.decal([q], ("H", 1))
    e0 = F(5.2, -4.0)
    end = [e0, add(F(6.0, 2.0), (sw * 0.3, 0)), add(F(6.4, 6.0), (sw * 0.6, 0))]
    tube(Bd, end, [1.1, 1.1, 1.0], "H", 0, ao=0)
    sal = [add(F(6.4, 6.0), (sw * 0.6, 0)), add(F(6.8, 11.0), (sw * 0.9, 0))]
    sm_ = tube(Bd, sal, [1.8, 1.5], "C", 0, ao=0)
    for q in sm_:
        if (q[1] // 2) % 2 == 0:
            remat(Bd, [q], "P", -1)
    tip = add(F(6.8, 12.0), (sw * 0.9, 0))
    for k in range(3):
        Bd.fixed({ip((tip[0] - 1 + k, tip[1] + (k % 2))): "H3"})

    # ---------------- cowl: short cape over the hunched shoulders
    Cw = Ls["Cowl"]
    mant = [F(-10.6, -ln + 3.0), F(-9.0, -ln - 3.0), F(-4.0, -ln - 5.8), F(3.0, -ln - 4.6), F(7.4, -ln + 1.2)] + \
        [add(F(7.4 - 20.0 * t, -ln + 6.5 + 4.5 * t + (3.2 * hash01(i, 31, fi // 3) if i % 2 == 0 else -0.4)),
             (cs * 0.5 * t, 0)) for i, t in enumerate([j / 9 for j in range(10)])] + [F(-12.6, -ln + 8.0)]
    mm = plate(Cw, mant, "S", bevel=4.5, tilt=(-0.2, -0.3), strength=1.3,
               fold=lambda x, y: (0.25 * math.sin((x - C[0]) * 0.7 - y * 0.35), 0))
    info["cowl"] = mm

    # ---------------- head: peaked sackcloth hood, small pale hollow face
    Hl = Ls["Head"]
    hs = p["hood"]
    G = lambda a_, b_: basis(Hd, (p["hup"][0] * 0.35, -1))(a_ * HS, b_ * HS)
    Cw = Ls["Cowl"]
    hood = [G(-10.0, 8.4), G(-13.4, 2.6), G(-13.6, -3.6), G(-9.6, -8.0), G(-4.6, -9.6 + hs), G(0.4, -10.2 + hs),
            G(2.8, -10.0 + hs),
            G(6.2, -6.8), G(9.4, -3.2), G(11.4, 0.2), G(8.4, -0.2), G(7.6, 5.8), G(5.0, 9.0), G(-2.4, 10.0)]
    hm = plate(Cw, hood, "S", bevel=4.0, tilt=(-0.15, -0.3), strength=1.3, ao=0)
    info["head"] = hm
    Cw.decal([q for q in polyline(curve([G(-7.6, -2.6), G(-5.2, 2.4), G(-3.0, 7.4)], n=5)) if q in hm], ("S", 1))
    Cw.decal([q for q in polyline(curve([G(-5.0, -6.6 + hs), G(-0.4, -8.8 + hs), G(5.2, -6.8), G(10.2, -0.8)], n=6))
              if q in hm], ("S", 5))                                                      # lit rim of the peak
    opening = [G(2.6, -1.8), G(9.2, -0.8), G(8.4, 5.8), G(5.6, 8.6), G(3.0, 6.2), G(1.8, 1.0)]
    om = poly_mask(opening)
    Hl.fixed({q: "S0" for q in om})
    face = [G(4.0, -0.4), G(7.4, -0.2), G(8.2, 1.4), G(9.6, 3.4), G(8.4, 4.0), G(8.6, 5.0), G(8.0, 7.0), G(6.2, 7.8),
            G(4.6, 5.6), G(3.8, 1.6)]
    fm = plate(Hl, face, "E", bevel=1.3, tilt=(0.1, 0.05), strength=1.0, bias=0, ao=0)
    info["face"] = fm
    sock = [ip(G(6.0, 2.0)), ip(G(7.1, 2.2))]
    Hl.decal(sock, "OUT")
    Hl.decal([q for q in [ip(G(5.8, 4.6)), ip(G(6.2, 5.2))] if q in fm], ("E", 1))            # hollow cheek
    Hl.decal([q for q in line(G(7.0, 5.8), G(8.4, 5.6)) if q in fm], "OUT")                   # mouth slit
    Hl.decal([q for q in line(G(3.8, -0.2), G(8.4, 0.6)) if q in fm], ("E", 1))               # hood shadow on brow
    e = sock[1]
    if p["eye"] == 1:
        Hl.fixed({e: "Z3"})
    elif p["eye"] == 2:
        Hl.fixed({e: "Z5"})
        FX.put([(e[0] + 1, e[1]), (e[0] - 1, e[1] - 0), (e[0], e[1] - 1)], "Z3")
        FX.put([(e[0] + 2, e[1]), (e[0] + 3, e[1])], "Z2")
    info["eye"] = e

    # ---------------- iron collar + broken links
    Co = Ls["Collar"]
    ccen = G(-0.6, 8.6)
    col = [add(ccen, (-6.0, -1.4)), add(ccen, (5.0, -0.2)), add(ccen, (5.2, 2.4)), add(ccen, (-5.8, 1.4))]
    cm_ = plate(Co, col, "X", bevel=1.2, tilt=(-0.1, -0.4), strength=1.3, ao=0)
    for q in cm_:
        if hash01(q[0], q[1], 51) < 0.05:
            Co.decal([q], ("R", 1))                                                  # rust pits
    Co.decal([ip(add(ccen, (-2.6, 0.2))), ip(add(ccen, (1.8, 0.8)))], ("X", 5))
    ctop = add(ccen, (3.6, 2.2))
    draw_chain(Co, chain_path(ctop, add(ctop, (0.6 + sw * 0.25, 7.0)), 0.0, n=4), phase=0.5)

    # ---------------- front arm (chain-wound forearm)
    Fa = Ls["FrontArm"]
    garm(Fa, shF, hf, 0, chain=True, pref=(-1, 0.55), fist=p["fist"], sleeve_seed=9, fi=fi, sw=sw)
    fl = [add(shF, (-4.4, -3.4)), add(shF, (2.2, -3.6)), add(shF, (4.0, 0.6)), add(shF, (2.8, 3.8)),
          add(shF, (0.6, 2.6)), add(shF, (-1.6, 4.6)), add(shF, (-4.0, 2.2))]
    plate(Fa, fl, "S", bevel=1.8, tilt=(-0.2, -0.3), strength=1.2, ao=0)

    # ---------------- storm rim light: a cold edge along the top of the cowl, hood and cloak
    for L_ in (Ls["Cowl"], Ls["Cloak"]):
        rim = {}
        for (x, y), e in L_.px.items():
            if (x, y - 1) not in L_.px and e[3] is None:
                rim[(x, y)] = "Z2" if (x - 1, y) not in L_.px else "Z1"
        L_.fixed(rim) if False else [L_.decal([q], c) for q, c in rim.items()]

    # ---------------- fx
    ex = set(bpix)
    if p["sweep"]:
        tgt = SMB if p["bl"] == "BellBack" else SM
        info["hit"] |= bell_sweep(tgt, p["sweep"], exclude=ex, min_age=0.22 if p["impact"] else 0.0)
    if p["impact"]:
        impact(FX, info, bc, p["impact"])
    if p["vib"]:
        vibrate(FX, bc, p["vib"], p["ba"], cold=not p["toll"])
    if p["dust"]:
        for k in range(10):
            side = -1 if k % 2 else 1
            x = int(bc[0] + side * (6 + hash01(k, fi, 3) * 12))
            y = FLOOR - int(hash01(k, fi, 4) * (3 + p["dust"] * 2))
            FX.put([(x, y)], ("A3", "A2", "S4")[k % 3])
    if p["scrape"]:
        lo = max(bpix, key=lambda q: (q[1], -q[0]))
        for k in range(9):
            x = int(lo[0] + 2 + hash01(k, fi, 5) * 14)
            y = FLOOR - int(hash01(k, fi, 6) ** 2 * 5)
            FX.put([(x, y)], ("A3", "A2", "S4")[k % 3])
        if fi % 2 == 0:
            FX.put([(lo[0] + 1, lo[1] - 1)], "U5")
            FX.put([(lo[0] + 2, lo[1] - 2)], "Z3")
    if p["glint"] == "bell":
        a_, vd_, top_ = bfr
        g = add(top_, (a_[0] * (LIP_U - 1) - vd_[0] * (hw(LIP_U) - 1.5), a_[1] * (LIP_U - 1) - vd_[1] * (hw(LIP_U) - 1.5)))
        star(FX, g)
        info["glint"] = g
    elif p["glint"] == "fist":
        star(FX, add(hf, (-1.0, -3.0)))
        info["glint"] = add(hf, (-1.0, -3.0))
    if p["flash"]:
        star(FX, p["flash"])
        for k in range(8):
            a = k * math.pi / 4
            FX.put(line(add(p["flash"], (math.cos(a) * 4, math.sin(a) * 4)), add(p["flash"], (math.cos(a) * 7, math.sin(a) * 7))),
                   "Z4" if k % 2 else "Z3")
    return Ls, info


def star(FX, c):
    x, y = ip(c)
    FX.put([(x, y)], "Z5")
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], "Z4")
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0), (0, -3), (0, 3)):
        FX.put([(x + d[0], y + d[1])], "Z3")


def impact(FX, info, bc, stage):
    ix = int(bc[0])
    pts = set()
    for k in range(26):
        side = -1 if k % 2 else 1
        a = -math.pi * (0.04 + 0.42 * hash01(k, 7, 50))
        r = (4 + 20 * hash01(k, 8, 51)) * (0.7 if stage == 1 else 1.1)
        x = ix + side * (12 + math.cos(a) * r * 1.2)
        y = FLOOR - 1 + math.sin(a) * r * (0.8 if stage == 1 else 0.55) + (0 if stage == 1 else 3 * (r / 12) ** 2)
        q = ip((x, min(FLOOR, y)))
        c = ("A4", "A3", "S5", "A2")[k % 4] if stage == 1 else ("A2", "S3", "A1")[k % 3]
        FX.put([q], c)
        if k % 3 == 0:
            FX.put([(q[0] + side, q[1]), (q[0], q[1] - 1), (q[0] + side, q[1] - 1)], c)
        pts.add(q)
    # billowing dust puffs either side of the bell
    for k in range(6):
        sgn = -1 if k % 2 else 1
        dx = (19 + (k // 2) * 7) * (1.0 if stage == 1 else 1.3)
        r = (4.6 - (k // 2) * 0.9) * (1.0 if stage == 1 else 1.25)
        c = (ix + sgn * dx, FLOOR - r * 0.6 - (0 if stage == 1 else 1.5))
        for q in mask_disc(c, r * 1.2, r):
            if q[1] > FLOOR or q in pts:
                continue
            ny = (q[1] + .5 - c[1]) / r
            nx = (q[0] + .5 - c[0]) / (r * 1.2)
            if stage == 1:
                FX.put([q], "A4" if ny < -0.4 and nx < 0.2 else "A3" if ny < 0.3 else "A2")
            else:
                FX.put([q], "A3" if ny < -0.4 and nx < 0.2 else "A2" if ny < 0.3 else "S3")
            pts.add(q)
    # floor cracks + shock sparks
    for sgn in (-1, 1):
        cx = ix + sgn * 14
        crk = polyline([(cx, FLOOR), (cx + sgn * 5, FLOOR - 1), (cx + sgn * 10, FLOOR), (cx + sgn * 16, FLOOR - 1)])
        FX.put(crk, "OUT")
        if stage == 1:
            FX.put([(q[0], q[1] - 1) for q in crk[::2] if q[1] > FLOOR - 2], "Z3")
    if stage == 1:
        for ang in range(-170, -5, 20):
            if -120 < ang < -60:
                continue
            a = math.radians(ang)
            p0 = (ix + math.cos(a) * 17, FLOOR - 1 + math.sin(a) * 5)
            p1 = (ix + math.cos(a) * 25, FLOOR - 1 + math.sin(a) * 9)
            FX.put(line(p0, p1), "Z4" if ang % 40 == -10 else "Z3")
        for dx in range(-26, 27):
            if abs(dx) > 14 and hash01(dx, 3, 52) < 0.7:
                FX.put([(ix + dx, FLOOR)], "Z4" if abs(dx) < 20 else "Z2")
    info["hit"] |= pts
    info["impact"] = (ix, FLOOR)


def vibrate(FX, bc, stage, ang, cold=True):
    """Subtle ring lines either side of the bell (stage 3 = strike, 2, 1 fading)."""
    cols = ("Z4", "Z3", "Z2") if cold else ("S5", "S4", "S3")
    for side in (-1, 1):
        for k in range(min(stage, 2) + (1 if stage >= 3 else 0)):
            r = 18 + k * 4 + (3 - stage)
            span = 0.55 - k * 0.1
            n = 9
            for i in range(n):
                t = -span + 2 * span * i / (n - 1)
                if (i + k + stage) % 4 == 3:
                    continue
                x = bc[0] + side * math.cos(t) * r
                y = bc[1] + 3 + math.sin(t) * r * 1.05
                if y <= FLOOR:
                    FX.put([ip((x, y))], cols[min(2, k + (3 - stage))])


# =========================================================================== animations
def a_idle():
    fr = []
    for i in range(6):
        b = 0.5 - 0.5 * math.cos(i * math.pi / 3)      # breath 0..1..0
        sway = 4.0 * math.sin(i * math.pi / 3 + 0.6)
        h = (119.0 - 0.3 * b, 80.0 + b * 0.8)
        fr.append((190, P_(P=(92.0, 78.0 + b * 0.4), C=(99.0, 56.0 + b * 1.0), Hd=(111.2, 52.5 + b * 1.3), hf=h,
                           hb=(84.0 + 0.4 * b, 97.0 + b * 0.7), ba=90 + sway, clap=-sway * 0.35, cd=7.0)))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        bob = 1.6 * abs(s)
        ff = (93.0 + 11.5 * c, 127 - max(0.0, -s) * 4.0)
        fb = (93.0 - 11.5 * c, 127 - max(0.0, s) * 4.0)
        P = (92.0, 78.0 + bob)
        hf = (86.0 - 1.5 * c, 95.0 + bob)
        tilt = 1.5 * math.sin(ph * 2)
        fr.append((140, P_(P=P, C=(99.5, 56.5 + bob), Hd=(112.0, 53.5 + bob), ff=ff, fb=fb,
                           hf=hf, hb=(96.0 + 6.0 * c, 95.0 + bob), bc=(44.0 - 1.5 * c, 110.0), ba=-167 + tilt,
                           ground=True, bl="BellBack", sag=2.0, scrape=1, wind=-1.0)))
    return fr


def a_swing():
    wind = dict(P=(89.0, 82.0), C=(89.0, 60.0), Hd=(99.0, 56.0), hup=(0.2, -1), fb=(74.0, 127), ff=(108.0, 127))
    deep = dict(P=(87.0, 86.0), C=(82.0, 64.4), Hd=(91.0, 59.0), hup=(-0.1, -1), fb=(70.0, 127), ff=(110.0, 127))
    lunge = dict(P=(98.0, 84.0), C=(110.0, 64.0), Hd=(123.0, 62.0), hup=(0.8, -1), fb=(76.0, 127), ff=(119.0, 127))
    tall = dict(P=(96.0, 79.0), C=(102.0, 57.0), Hd=(113.0, 52.0), hup=(0.35, -1), fb=(80.0, 127), ff=(112.0, 127))
    back = dict(P=(92.0, 81.0), C=(89.0, 59.0), Hd=(98.0, 54.0), hup=(-0.05, -1), fb=(76.0, 127), ff=(110.0, 127))
    K5 = [((72.0, 88.0), 148, 16.0), ((96.0, 94.0), 100, 18.0), ((117.0, 81.0), 50, 18.0)]
    K6 = [((96.0, 94.0), 100, 18.0), ((117.0, 81.0), 50, 18.0), ((132.0, 78.0), 12, 18.0)]
    K7 = [((117.0, 81.0), 50, 18.0), ((132.0, 78.0), 12, 18.0), ((130.0, 70.0), -32, 17.0)]
    K10 = [((116.0, 40.0), -118, 2.5), ((93.0, 46.0), -150, 12.0), ((74.0, 70.0), 168, 18.0)]
    K11 = [((93.0, 46.0), -150, 12.0), ((74.0, 70.0), 168, 18.0), ((76.0, 80.0), 128, 18.0)]
    return [
        (130, P_(P=(91.0, 79.0), C=(95.0, 57.0), Hd=(106.0, 53.0), hup=(0.35, -1), hf=(110.0, 84.0), hb=(90.0, 92.0),
                 ba=100, cd=8.0, clap=-2)),
        (130, P_(**wind, hf=(100.0, 90.0), hb=(98.0, 88.0), ba=114, cd=11.0, clap=-2)),
        (140, P_(**wind, hf=(86.0, 92.0), hb=(102.0, 90.0), ba=128, cd=14.0, bl="BellBack", clap=-1)),
        (150, P_(**deep, hf=(76.0, 90.0), hb=(104.0, 94.0), ba=140, cd=16.0, bl="BellBack", wind=-2)),
        (320, P_(**dict(deep, C=(81.0, 65.0), Hd=(90.0, 60.0)), hf=(72.0, 88.0), hb=(105.0, 95.0), ba=148, cd=16.0,
                 bl="BellBack", eye=2, glint="bell", wind=-3)),
        (70, P_(**lunge, hf=(117.0, 81.0), hb=(84.0, 92.0), ba=50, cd=18.0, sweep=K5, wind=5, clap=-3)),
        (60, P_(**lunge, hf=(132.0, 78.0), hb=(84.0, 90.0), ba=12, cd=18.0, sweep=K6, wind=6, clap=-3)),
        (70, P_(**dict(lunge, C=(109.0, 62.0), Hd=(122.0, 59.0)), hf=(130.0, 70.0), hb=(86.0, 88.0), ba=-32, cd=17.0,
                sweep=K7, wind=5, clap=-2)),
        (100, P_(**tall, hf=(116.0, 40.0), hb=(88.0, 88.0), ba=-118, cd=2.5, wind=3)),
        (120, P_(**back, hf=(93.0, 46.0), hb=(96.0, 86.0), ba=-150, cd=12.0, bl="BellBack", wind=1)),
        (70, P_(**back, hf=(74.0, 70.0), hb=(100.0, 88.0), ba=168, cd=18.0, bl="BellBack", sweep=K10, wind=-4)),
        (70, P_(**dict(back, P=(91.0, 82.0), C=(90.0, 60.0), Hd=(100.0, 55.0)), hf=(76.0, 80.0), hb=(100.0, 90.0),
                ba=128, cd=18.0, bl="BellBack", sweep=K11, wind=-4)),
        (160, P_(P=(91.0, 80.0), C=(95.0, 58.0), Hd=(106.0, 54.0), hup=(0.3, -1), hf=(92.0, 84.0), hb=(88.0, 94.0),
                 ba=96, cd=9.0, bl="BellBack", fb=(80.0, 127), ff=(106.0, 127))),
        (180, P_(P=(92.0, 79.0), C=(98.0, 57.0), Hd=(110.0, 53.0), hf=(114.0, 82.0), hb=(84.0, 96.0), ba=78, cd=7.0,
                 clap=2)),
    ]


def a_slam():
    tall = dict(P=(93.0, 78.0), C=(97.0, 55.0), Hd=(107.0, 48.0), hup=(0.2, -1), fb=(80.0, 127), ff=(106.0, 127))
    arch = dict(P=(91.0, 79.0), C=(90.0, 56.0), Hd=(98.0, 48.0), hup=(-0.1, -1), fb=(78.0, 127), ff=(108.0, 127))
    bend = dict(P=(98.0, 84.0), C=(114.0, 68.0), Hd=(127.0, 67.0), hup=(0.95, -1), fb=(80.0, 127), ff=(118.0, 127))
    K6 = [((93.0, 34.0), 150, 10.0), ((100.0, 32.0), -90, 6.0), ((118.0, 52.0), 10, 8.0)]
    K7 = [((110.0, 40.0), -40, 7.0), ((118.0, 52.0), 10, 8.0), ((132.0, 82.0), 78, 9.0)]
    return [
        (140, P_(P=(92.0, 80.0), C=(100.0, 58.0), Hd=(112.0, 55.0), hup=(0.5, -1), hf=(116.0, 80.0),
                 hb=(110.0, 82.0), grip2=True, ba=88, cd=5.0)),
        (130, P_(**tall, hf=(110.0, 62.0), hb=(106.0, 64.0), grip2=True, ba=72, cd=5.0, clap=3)),
        (130, P_(**tall, hf=(104.0, 46.0), hb=(100.0, 48.0), grip2=True, ba=-70, cd=4.0, wind=2)),
        (130, P_(**arch, hf=(96.0, 34.0), hb=(93.0, 36.0), grip2=True, ba=-165, cd=8.0, bl="BellBack")),
        (150, P_(**arch, hf=(94.0, 33.0), hb=(91.0, 35.0), grip2=True, ba=158, cd=10.0, bl="BellBack", wind=-2)),
        (340, P_(**dict(arch, C=(88.4, 56.6), Hd=(95.6, 49.0)), hf=(93.0, 34.0), hb=(90.0, 36.0), grip2=True,
                 ba=150, cd=10.0, bl="BellBack", eye=2, glint="bell", wind=-3)),
        (60, P_(**dict(bend, P=(96.0, 82.0), C=(108.0, 62.0), Hd=(121.0, 60.0), hup=(0.8, -1)), hf=(118.0, 52.0),
                hb=(114.0, 54.0), grip2=True, ba=10, cd=8.0, sweep=K6, wind=4)),
        (80, P_(**bend, hf=(132.0, 82.0), hb=(127.0, 84.0), grip2=True, ba=78, cd=9.0, bc=(148.0, 110.0),
                ground=True, sweep=K7, impact=1, mouth=False, wind=3)),
        (140, P_(**bend, hf=(132.0, 84.0), hb=(127.0, 86.0), grip2=True, ba=80, cd=9.0, bc=(148.0, 110.0),
                 ground=True, impact=2, mouth=False)),
        (150, P_(P=(94.0, 82.0), C=(104.0, 61.0), Hd=(116.0, 59.0), hup=(0.6, -1), fb=(80.0, 127), ff=(112.0, 127),
                 hf=(122.0, 78.0), hb=(116.0, 80.0), grip2=True, ba=102, bc=(146.0, 110.0), ground=True, sag=3,
                 dust=1, mouth=False)),
        (160, P_(P=(93.0, 80.0), C=(101.0, 58.0), Hd=(113.0, 55.0), hup=(0.5, -1), hf=(120.0, 78.0), hb=(112.0, 84.0),
                 ba=94, cd=6.0, clap=-2)),
        (180, P_(hf=(119.0, 80.0), ba=86, clap=1)),
    ]


RING_BC = (142.0, 110.0)


def a_ring():
    plant = dict(bc=RING_BC, ba=90, ground=True, mouth=False)
    rear = dict(P=(90.0, 80.0), C=(88.0, 58.0), Hd=(97.0, 52.0), hup=(-0.05, -1), fb=(78.0, 127), ff=(108.0, 127))
    hit = dict(P=(98.0, 82.0), C=(111.0, 64.0), Hd=(123.0, 62.0), hup=(0.8, -1), fb=(80.0, 127), ff=(116.0, 127))
    return [
        (140, P_(P=(93.0, 80.0), C=(102.0, 59.0), Hd=(114.0, 56.0), hup=(0.55, -1), hf=(122.0, 84.0), hb=(90.0, 92.0),
                 ba=74, cd=8.0, clap=2)),
        (130, P_(P=(95.0, 82.0), C=(106.0, 62.0), Hd=(118.0, 60.0), hup=(0.7, -1), ff=(112.0, 127), hf=(128.0, 88.0),
                 hb=(92.0, 92.0), sag=0, dust=1, **plant)),
        (140, P_(P=(94.0, 80.0), C=(102.0, 58.0), Hd=(114.0, 54.5), hup=(0.5, -1), ff=(110.0, 127),
                 hf=(118.0, 84.0), hb=(88.0, 94.0), sag=5, **plant)),
        (140, P_(P=(92.0, 80.0), C=(96.0, 58.0), Hd=(107.0, 53.0), hup=(0.3, -1), ff=(108.0, 127), fb=(79.0, 127),
                 hf=(102.0, 66.0), hb=(90.0, 88.0), sag=10, fist=True, **plant)),
        (320, P_(**rear, hf=(76.0, 52.0), hb=(102.0, 82.0), sag=14, fist=True, eye=2, glint="fist", wind=-3, **plant)),
        (70, P_(**hit, hf=(128.0, 97.0), hb=(94.0, 84.0), sag=7, fist=True, vib=3, wind=4, flash=(131.0, 97.0),
                **dict(plant, bc=(143.0, 110.0)))),
        (120, P_(**dict(hit, C=(109.0, 63.0), Hd=(121.0, 60.0)), hf=(124.0, 94.0), hb=(94.0, 86.0), sag=8, fist=True,
                 vib=3, **dict(plant, bc=(141.0, 110.0)))),
        (130, P_(P=(96.0, 81.0), C=(105.0, 60.0), Hd=(117.0, 57.0), hup=(0.6, -1), ff=(112.0, 127),
                 hf=(118.0, 88.0), hb=(92.0, 90.0), sag=8, vib=2, **dict(plant, bc=(143.0, 110.0)))),
        (150, P_(P=(94.0, 80.0), C=(102.0, 58.0), Hd=(114.0, 55.0), hup=(0.5, -1), ff=(110.0, 127),
                 hf=(124.0, 84.0), hb=(90.0, 92.0), sag=3, vib=1, **plant)),
        (180, P_(P=(93.0, 79.0), C=(100.0, 57.0), Hd=(112.0, 53.5), ff=(106.0, 127), hf=(121.0, 80.0), ba=76, cd=7.0,
                 clap=2)),
    ]


def a_stagger():
    reel = dict(P=(89.0, 80.0), C=(84.0, 59.0), Hd=(90.0, 51.0), hup=(-0.35, -1), fb=(76.0, 127), ff=(104.0, 127))
    sag = dict(P=(91.0, 83.0), C=(98.0, 62.0), Hd=(109.0, 61.0), hup=(0.75, -1), fb=(78.0, 127), ff=(106.0, 127))
    return [
        (100, P_(**reel, hf=(104.0, 70.0), hb=(78.0, 78.0), ba=60, cd=6.0, eye=2)),
        (130, P_(**reel, hf=(108.0, 86.0), hb=(76.0, 84.0), ba=82, bc=(124.0, 110.0), ground=True, sag=4,
                 mouth=False, dust=1)),
        (240, P_(**sag, hf=(112.0, 96.0), hb=(88.0, 100.0), ba=70, bc=(128.0, 110.0), ground=True, sag=3, eye=0)),
        (260, P_(**dict(sag, C=(98.4, 62.6), Hd=(109.4, 61.8)), hf=(112.0, 97.0), hb=(88.0, 101.0), ba=70,
                 bc=(128.0, 110.0), ground=True, sag=3, eye=0)),
    ]


def a_death():
    KN = dict(P=(91.0, 101.0), C=(97.0, 79.0), Hd=(108.0, 76.0), hup=(0.55, -1), kf=(104.0, 124.0), ff=(80.0, 127),
              kb=(94.0, 124.0), fb=(72.0, 127), kneel=True, eye=0)
    fr = [
        (120, P_(P=(89.0, 80.0), C=(83.0, 59.0), Hd=(89.0, 50.0), hup=(-0.45, -1), fb=(76.0, 127), ff=(104.0, 127),
                 hf=(102.0, 68.0), hb=(76.0, 76.0), ba=64, cd=6.0, eye=2)),
        (150, P_(P=(90.0, 86.0), C=(94.0, 64.0), Hd=(104.0, 60.0), hup=(0.4, -1), fb=(76.0, 127), ff=(104.0, 127),
                 hf=(110.0, 90.0), hb=(80.0, 94.0), ba=90, bc=(124.0, 110.0), ground=True, sag=4, mouth=False,
                 dust=1, eye=1)),
        (180, P_(**KN, hf=(110.0, 104.0), hb=(84.0, 110.0), ba=66, bc=(128.0, 110.0), ground=True, sag=5, dust=1)),
        (160, P_(**KN, hf=(111.0, 106.0), hb=(84.0, 111.0), ba=40, bc=(136.0, 110.0), ground=True, sag=7)),
        (160, P_(**KN, hf=(112.0, 107.0), hb=(84.0, 112.0), ba=14, bc=(143.0, 110.0), ground=True, sag=8, dust=1)),
        (170, P_(**KN, hf=(112.0, 107.0), hb=(84.0, 112.0), ba=-10, bc=(148.0, 110.0), ground=True, sag=8)),
        (320, P_(**dict(KN, Hd=(108.5, 77.0), hup=(0.65, -1)), hf=(112.0, 108.0), hb=(84.0, 112.0), ba=-8,
                 bc=(147.0, 110.0), ground=True, sag=8, vib=2, toll=1)),
        (180, P_(**dict(KN, C=(99.0, 81.0), Hd=(111.0, 80.0), hup=(0.75, -1)), hf=(113.0, 110.0), hb=(86.0, 113.0),
                 ba=-9, bc=(147.0, 110.0), ground=True, sag=8, vib=1, toll=1)),
        (160, P_(**dict(KN, P=(92.0, 103.0), C=(106.0, 90.0), Hd=(119.0, 92.0), hup=(0.95, -0.6)), hf=(118.0, 118.0),
                 hb=(92.0, 118.0), ba=-9, bc=(147.0, 110.0), ground=True, sag=8, hood=1.0)),
        (160, P_(**dict(KN, P=(93.0, 106.0), C=(112.0, 103.0), Hd=(126.0, 110.0), hup=(1.0, -0.2)),
                 hf=(126.0, 124.0), hb=(100.0, 124.0), ba=-9, bc=(147.0, 110.0), ground=True, sag=8, dust=2, hood=1.5)),
        (200, P_(**dict(KN, P=(93.0, 107.0), C=(113.0, 107.0), Hd=(127.0, 114.0), hup=(1.0, -0.05)),
                 hf=(127.0, 125.0), hb=(101.0, 125.0), ba=-9, bc=(147.0, 110.0), ground=True, sag=8, dust=1, hood=1.5)),
        (1000, P_(**dict(KN, P=(93.0, 107.0), C=(113.0, 107.4), Hd=(127.0, 114.4), hup=(1.0, -0.05)),
                  hf=(127.0, 125.0), hb=(101.0, 125.0), ba=-9, bc=(147.0, 110.0), ground=True, sag=8, hood=1.5)),
    ]
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("swing", a_swing), ("slam", a_slam), ("ring", a_ring),
           ("stagger", a_stagger), ("death", a_death)]
COUNTS = dict(idle=6, walk=8, swing=14, slam=12, ring=10, stagger=4, death=12)
LOOPS = ("idle", "walk")


# =========================================================================== render
def render_all(only=None):
    frames, infos, tags, flats = [], {}, [], []
    for tag, fn in TAGDEFS:
        fr = fn()
        assert len(fr) == COUNTS[tag], (tag, len(fr))
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=tag in LOOPS, extra=[p.get("wind", 0.0) for _, p in fr])
        a = len(frames)
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            Ls, info = draw(p, a + k, sway[k])
            imgs = {}
            for n in LAYERS:
                v = Ls.get(n)
                if v is None:
                    continue
                imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
            frames.append({"ms": ms, "cels": imgs})
            flats.append(K.flatten(imgs, LAYERS))
            infos[tag].append(info)
        tags.append((tag, a, len(frames) - 1))
        print("rendered", tag, len(fr))
    return frames, infos, tags, flats


# =========================================================================== meta
def bbox(pts):
    pts = [p for p in pts if K.inb(*p)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def window(infos, tag, a, b, xmin=None, xmax=None):
    rs = {}
    for k in range(a, b + 1):
        pts = infos[tag][k]["hit"]
        if xmin is not None:
            pts = {q for q in pts if q[0] >= xmin}
        if xmax is not None:
            pts = {q for q in pts if q[0] <= xmax}
        r = bbox(pts)
        r[3] = H - r[1]                        # reach the floor
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


def build_meta(infos, frames, tags):
    i0 = tags[[t for t, _, _ in tags].index("idle")][1]
    imgs = frames[i0]["cels"]
    box = K.opaque_bbox(imgs, ["Body", "Cowl", "Head", "FrontLeg", "BackLeg"])
    hurt = [box[0] + 3, box[1] + 2, box[2] - box[0] - 6, H - (box[1] + 2)]
    sw, sl, rg = infos["swing"], infos["slam"], infos["ring"]
    meta = {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {
            "swing": {"windows": [window(infos, "swing", 5, 7, xmin=AX + 6), window(infos, "swing", 10, 11, xmax=AX - 4)]},
            "slam": window(infos, "slam", 6, 7, xmin=AX + 10),
        },
        "spawn": {
            "slam": {"frame": 7, "at": [int(sl[7]["impact"][0]), H - 1]},
            "ring": {"frame": 5, "at": pt(rg[5]["bell"])},
        },
        "telegraph": {
            "swing": {"frame": 4, "at": pt(sw[4]["glint"])},
            "slam": {"frame": 5, "at": pt(sl[5]["glint"])},
            "ring": {"frame": 4, "at": pt(rg[4]["glint"])},
        },
        "notes": "faces right, anchor = feet (body centre x=96). swing = two windows: 0-4 winds the bell back low behind "
                 "him (4 = held windup), window 0 (5-7) the bell sweeps forward low-to-high in front (skims the floor, "
                 "reach ~88px), 8-9 whirls over his head, window 1 (10-11) the backswing sweeps low BEHIND him "
                 "(hit rect is behind the anchor), 12-13 recover. slam: 0-5 hauls the bell overhead behind his head "
                 "(5 held peak), active 6-7, bell lip strikes the floor on frame 7 -> spawn.slam = impact point on the "
                 "floor (shockwave ring). ring: 0-3 plants the bell mouth-down in front, 4 rears back the chain-wound "
                 "fist (held telegraph), 5 strikes -> spawn.ring = bell centre (toll shockwave + fx_sp_toll), 6-9 bell "
                 "shudders while he recovers; no hitbox. 'hit' = union of per-frame 'rects' over the inclusive active "
                 "range; each rect reaches the floor. telegraph 'at' = the glint on the bell lip (swing/slam) or on the raised fist (ring). "
                 "stagger holds its last frame; death final frame held (1000ms).",
    }
    return meta


# =========================================================================== FX: toll burst
def fx_sp_toll():
    """64x64, 8 frames, centred: concentric cold-white / pale-bronze sound rings + grit bursting from the bell."""
    w = h = 64
    cx, cy = 31.5, 31.5
    K.setup(w, h)
    frames = []

    def ring(L, r, cols, gapk, t, seed, thick=1, dotted=False):
        n = max(20, int(r * 7))
        for k in range(n):
            a = 2 * math.pi * k / n
            if hash01(int((a + 0.3) * 5 / math.pi), seed, 61) < gapk:
                continue
            if dotted and k % 2:
                continue
            for j in range(thick):
                rr = r - j
                q = ip((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.86))
                if K.inb(*q):
                    L.put([q], cols[min(j, len(cols) - 1)])

    for i in range(8):
        core, glow = FXLayer("Core"), FXLayer("Glow")
        t = i / 7
        r0 = 5.0 + i * 3.7
        if i < 5:
            ring(core, r0, ("Z5", "Z4", "Z3"), 0.08 + 0.06 * i, t, i // 2, thick=3 if i < 3 else 2)
        else:
            ring(core, r0, ("Z3", "Z2"), 0.25 + 0.1 * (i - 5), t, i // 2, thick=1 + (i == 5), dotted=i == 7)
        if r0 - 5 > 3:
            ring(glow, r0 - 5.0, ("U5", "U4") if i < 4 else ("U4", "U3") if i < 6 else ("U3",), 0.15 + 0.08 * i, t,
                 i // 2 + 7, thick=2 if i < 5 else 1, dotted=i >= 6)
        if r0 - 11 > 3 and i < 7:
            ring(glow, r0 - 11.0, ("Z3",) if i < 5 else ("Z2",), 0.35, t, i // 2 + 13, dotted=True)
        if i < 3:                                         # the strike flash
            rc = (4.2, 3.0, 1.6)[i]
            for q in mask_disc((cx, cy), rc):
                d = math.hypot(q[0] + .5 - cx, q[1] + .5 - cy) / rc
                core.put([q], "Z5" if d < 0.55 else "Z4" if i < 2 else "Z3")
            arm = (11, 7, 4)[i]
            for d in range(-arm, arm + 1):
                c = "Z5" if abs(d) < arm * 0.4 else "Z4" if abs(d) < arm * 0.75 else "Z3"
                core.put([ip((cx + d, cy))], c)
                if abs(d) < arm * 0.6:
                    core.put([ip((cx, cy + d * 0.8))], c)
        # grit + dust flung out, mostly sideways and along the ground, with a little gravity
        for k in range(26):
            a = math.pi * (hash01(k, 1, 70) * 1.3 - 0.15) if k % 3 else 2 * math.pi * hash01(k, 1, 71)
            if k % 2:
                a = math.pi - a
            sp = 0.55 + 0.7 * hash01(k, 2, 70)
            r = (4 + i * 3.9) * sp
            q = ip((cx + math.cos(a) * r * 1.15, cy + math.sin(a) * r * 0.55 + (i * i) * 0.1 * sp))
            if not K.inb(*q) or (i >= 6 and k % 3 == 0):
                continue
            c = ("A4", "A3", "U4", "S5")[k % 4] if i < 5 else ("A3", "A2", "S4")[k % 3]
            glow.put([q], c)
            if k % 4 == 0 and i < 6:
                glow.put([(q[0] + (1 if math.cos(a) > 0 else -1), q[1])], "A2")
        frames.append({"ms": (50, 60, 70, 70, 80, 90, 100, 110)[i], "cels": {"Glow": glow.image(), "Core": core.image()}})
    K.setup(W, H)
    return frames


# =========================================================================== previews
BG = (86, 88, 98, 255)
CELL = (70, 73, 84, 255)


def preview_rows(tags, flats, path, scale=3):
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 10
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), BG)
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), CELL)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                                  ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def hitbox_preview(tags, flats, meta, path, scale=3):
    start = {t: (a, b) for t, a, b in tags}
    rows = [("swing", meta["attacks"]["swing"]["windows"]), ("slam", [meta["attacks"]["slam"]]), ("ring", []),
            ("idle", [])]
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), BG)
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        sp, tg = meta["spawn"].get(t), meta["telegraph"].get(t)
        txt = t + "  " + "  ".join(f"active {w['active']} hit {w['hit']}" for w in wins)
        if sp:
            txt += f"  spawn f{sp['frame']} {sp['at']}"
        if tg:
            txt += f"  telegraph f{tg['frame']} {tg['at']}"
        dd.text((4, y0 + 4), txt, fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), CELL)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)

            def cross(q, col):
                x, y = q
                d.line([((x - 4) * scale, y * scale), ((x + 4) * scale, y * scale)], fill=col, width=2)
                d.line([(x * scale, (y - 4) * scale), (x * scale, (y + 4) * scale)], fill=col, width=2)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(w["rects"][str(k)], (255, 50, 50, 255), 2)
            if sp and sp["frame"] == k:
                cross(sp["at"], (255, 60, 255, 255))
            if tg and tg["frame"] == k:
                cross(tg["at"], (60, 240, 255, 255))
            d.line([(ax * scale - 5, ay * scale - 2), (ax * scale + 5, ay * scale - 2)], fill=(255, 255, 0, 255), width=2)
            d.line([(ax * scale, ay * scale - 8), (ax * scale, ay * scale - 1)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def closeup(tags, flats, path, scale=5):
    """Key frames at 5x, 3 per row; the player (assets/player.png frame 0) stands in front of him for scale."""
    start = {t: a for t, a, _ in tags}
    pl = Image.open(os.path.join(asebuild.ASSETS, "player.png")).crop((0, 0, 64, 40))
    picks = [(t, k) for t, k in (("idle", 0), ("swing", 4), ("swing", 6), ("slam", 5), ("slam", 7), ("ring", 5))
             if t in start]
    cols = 3
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (W + 2) * scale, rows * (H + 2) * scale), BG)
    for j, (t, k) in enumerate(picks):
        fr = Image.new("RGBA", (W, H), CELL)
        if j == 0:
            fr.alpha_composite(pl, (172 - 28, H - 40))
        fr.alpha_composite(flats[start[t] + k])
        sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                              ((j % cols) * (W + 2) * scale, (j // cols) * (H + 2) * scale))
    sheet.save(path)


def fx_preview(frames, path, s=5):
    sheet = Image.new("RGBA", (8 * 66 * s, 64 * s), BG)
    for i, f in enumerate(frames):
        fr = Image.new("RGBA", (64, 64), (40, 44, 56, 255))
        fr.alpha_composite(f["cels"]["Glow"])
        fr.alpha_composite(f["cels"]["Core"])
        sheet.alpha_composite(fr.resize((64 * s, 64 * s), Image.NEAREST), (i * 66 * s, 0))
    sheet.save(path)


# =========================================================================== main
def main():
    frames, infos, tags, flats = render_all(ONLY)
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    sfx = "_wip" if ONLY else ""
    preview_rows(tags, flats, os.path.join(pv, f"bellringer{sfx}.png"))
    closeup(tags, flats, os.path.join(pv, f"bellringer_closeup{sfx}.png"))
    if ONLY:
        return
    meta = build_meta(infos, frames, tags)
    hitbox_preview(tags, flats, meta, os.path.join(pv, "bellringer_hitbox.png"))
    with open(os.path.join(asebuild.ASSETS, "bellringer_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    for t, d in meta["attacks"].items():
        for w in d.get("windows", [d]):
            print("attack", t, w["active"], w["hit"])
    print("hurtbox", meta["hurtbox"], "telegraph", meta["telegraph"], "spawn", meta["spawn"])
    toll = fx_sp_toll()
    fx_preview(toll, os.path.join(pv, "fx_sp_toll.png"))
    if BUILD:
        asebuild.build("bellringer", W, H, LAYERS, frames, tags)
        asebuild.build("fx_sp_toll", 64, 64, ["Glow", "Core"], toll, [("sp_toll", 0, 7)])


if __name__ == "__main__":
    main()
