"""King Vael, rebuilt on Morvain's rig (agent N).

Imports art/gen_boss.py read-only as a library (per-pixel-normal shapes, material ramps, decals, contact AO,
sel-out outlines, secondary motion, swept smears, render/compose) and swaps in Vael's own parts:
    corroded gold-and-bone plate (ramp A + verdigris N decals + bone B trim), a skull fused into a spiked crown with
    pale-blue ghost-fire eyes, a tattered royal-purple cape (V) with gold trim, a massive bone greatsword, spectral
    wrist chains.  All glows are pale ghost-fire blue (Morvain's molten-gold Y ramp is re-coloured in this process).
Authored facing LEFT on Morvain's joints (so his proven poses/secondary motion apply); frames are mirrored to face
RIGHT at export (art/gen_necro_vael2.py).
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import gen_boss as GB  # noqa: E402  (read-only reuse)
from gen_boss import (add, lerp, norm3, hash01, poly_mask, line, polyline, bezier, ik, n_capsule, n_dome, n_plate,  # noqa: E402
                      mask_disc, mask_capsule, tapered, inb, W, H, GROUND)

# ---------------------------------------------------------------- palette (process-local additions / recolours)
NEW = {
    # antique gold plate, corroded (warm brown shadows -> pale gold highlight)
    "A0": "#180f08", "A1": "#2e1f0e", "A2": "#4b3314", "A3": "#6e4e1e", "A4": "#9a7430", "A5": "#c9a458",
    # bone (grey-brown -> ivory)
    "B0": "#231d18", "B1": "#3f362c", "B2": "#62574a", "B3": "#8d8069", "B4": "#bcae8e", "B5": "#e6dcc0",
    # royal purple cloth
    "V0": "#0c0613", "V1": "#190b25", "V2": "#2a1340", "V3": "#3e1f5c", "V4": "#57307c", "V5": "#77509e",
    # verdigris corrosion
    "N0": "#0c1714", "N1": "#172c27", "N2": "#27463c", "N3": "#3b6556", "N4": "#578873",
    # ghost fire (fixed), replaces Morvain's molten gold everywhere in this process
    "Y0": "#3a70c0", "Y1": "#63a0e6", "Y2": "#a2cdf8", "Y3": "#eef8ff",
    "U0": "#142c58", "U1": "#22498a",
    # old blood wraps
    "R0": "#2a0a0e", "R1": "#4a1016", "R2": "#6e1a1e",
}
for k, v in NEW.items():
    GB.HEX[k] = v
    GB.RGBA[k] = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
GB.RAMP.update({"A": ["A0", "A1", "A2", "A3", "A4", "A5"], "B": ["B0", "B1", "B2", "B3", "B4", "B5"],
                "V": ["V0", "V1", "V2", "V3", "V4", "V5"], "N": ["N0", "N1", "N2", "N3", "N4"]})
GB.SHINY["A"] = 0.9


def smear_color(age, x, y, edge_d):
    if age < 0.2:
        return "Y3" if edge_d < 2.5 else "Y2"
    if age < 0.45:
        return "Y2" if edge_d < 2 else "Y1"
    if age < 0.7:
        return "Y1" if edge_d < 2 else "Y0"
    return "U1" if edge_d < 2 else "U0"


GB.smear_color = smear_color


# =========================================================================== weapon: the bone greatsword
BLADE = dict(pommel=-13, grip_end=3, guard=(3, 8), end=60, curve=0.0)
GB.BLADE.update(BLADE)


def weapon_geom(grip, ang, flip=1):
    """A massive greatsword of fused bone: vertebra ridge down the middle, notched serrated edges, old red wraps
    on the ricasso, a guard of curved gold ribs, a small skull pommel.  Returns (pixels, edge-glow pixels)."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    gx, gy = grip
    vdir = (-sa * flip, ca * flip)
    lit = -(vdir[0] * GB.LIGHT[0] + vdir[1] * GB.LIGHT[1])
    out, edge = {}, []
    E = BLADE["end"]
    b0 = BLADE["guard"][1] - 1
    Rr = E + 5
    for y in range(int(gy - Rr), int(gy + Rr) + 1):
        for x in range(int(gx - Rr), int(gx + Rr) + 1):
            dx, dy = x + .5 - gx, y + .5 - gy
            u = dx * ca + dy * sa
            if u < BLADE["pommel"] - 4 or u > E + 1:
                continue
            v = (-dx * sa + dy * ca) * flip
            c = None
            # grip: dark leather with bone rings
            if BLADE["pommel"] + 2 <= u <= BLADE["grip_end"] and abs(v) <= 1.7:
                c = "B1" if int(u) % 4 == 0 else ("S2" if v < 0 else "S1")
                if int(u) % 4 == 0 and v < 0:
                    c = "B3"
            # skull pommel
            pu = u - (BLADE["pommel"] + 0.2)
            if pu * pu / 7.5 + v * v / 8.0 <= 1.0:
                c = "B5" if v < -0.8 else "B4" if v < 0.8 else "B2"
                if abs(v) > 0.4 and abs(v) < 1.6 and -0.5 < pu < 1.2:
                    c = "OUT"                                    # sockets
                if abs(v) < 0.6 and abs(pu - 1.8) < 0.6:
                    c = "B1"
            # guard: curved gold ribs sweeping toward the blade
            g0, g1 = BLADE["guard"]
            if g0 - 1 <= u <= g1:
                t = (u - (g0 - 1)) / (g1 - g0 + 1)
                half = 8.0 - t * 2.0
                if abs(v) <= half and (abs(v) < 2.4 or (u - (g0 - 1)) > (abs(v) - 2.4) * 0.5):
                    rib = int(abs(v) * 0.9) % 2 == 0
                    c = ("A5" if v < -2 else "A4" if v < 1 else "A3") if rib else ("A2" if v < 0 else "A1")
                    if abs(v) > half - 1.2:
                        c = "A2" if v > 0 else "A4"
                    if abs(v) < 1.3 and g0 <= u <= g1 - 1:
                        c = "Y2"                                  # a ghost-fire gem
            # blade of fused bone
            if b0 <= u <= E:
                s = u - b0
                t = s / (E - b0)
                we = 4.6 + 1.2 * math.sin(min(t, 1.0) * math.pi * 0.8)
                wb = 4.2 + 1.0 * math.sin(min(t, 1.0) * math.pi * 0.8)
                if t > 0.8:
                    k = (1 - t) / 0.2
                    we *= k ** 0.8
                    wb *= k ** 0.8
                # serrations: notches bitten out of both edges
                notch = (int(s) % 7 in (3, 4)) and 0.12 < t < 0.8
                if notch:
                    we -= 1.3
                    wb -= 1.0
                lo, hi = -wb, we
                if lo <= v <= hi:
                    de, ds = hi - v, v - lo
                    if de < 1.0:
                        c = "B5"; edge.append((x, y))
                    elif ds < 1.0:
                        c = "B2" if lit > 0 else "B3"
                    elif abs(v) < 1.2 and 0.05 < t < 0.86:
                        # vertebra ridge: knobbly segments
                        seg = int(s) % 5
                        c = "B5" if seg == 0 else "B4" if (seg in (1, 4) and v < 0) else "B3" if v < 0 else "B2"
                        if seg == 2 and abs(v) < 0.5:
                            c = "B1"
                    elif v > 0:
                        c = "B4" if lit > 0.15 else "B3"
                    else:
                        c = "B3" if lit < -0.15 else "B2"
                    if 0.0 <= t < 0.14 and abs(v) > 1.4 and (int(u + v * 0.6) % 3 == 0):
                        c = "R2" if v < 0 else "R1"             # old blood-red wraps on the ricasso
                    if c in ("B3", "B2") and hash01(x // 2, y // 2, 17) < 0.05:
                        c = "B1"                                  # pits in the bone
            if c:
                out[(x, y)] = c
    return out, edge


def weapon_point(grip, ang, u, v=0.0, flip=1):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return (grip[0] + ca * u - sa * v * flip, grip[1] + sa * u + ca * v * flip)


GB.weapon_geom = weapon_geom
GB.weapon_point = weapon_point


# =========================================================================== cape: tattered royal purple
def draw_cape(L, j, t_sw, frame_i, p2fx):
    Ns, Fs, C, P = j["Ns"], j["Fs"], j["C"], j["P"]
    sw = t_sw
    fl = j.get("cape_flare", 0)
    top = min(Ns[1], Fs[1]) - 5
    bot = min(GROUND - 1 + fl * 0.2, GROUND)
    pts = [(Ns[0] + 3, top + 2), (Fs[0] + 5, top - 2), (Fs[0] + 15 + sw * 0.3, top + 12),
           (Fs[0] + 24 + sw * 0.7 + fl * 0.6, top + 40), (Fs[0] + 33 + sw + fl, bot),
           (P[0] - 14 + sw * 0.2, bot + 1), (Ns[0] - 5 + sw * 0.1, P[1] + 12), (Ns[0] - 2, top + 20)]
    m = poly_mask(pts)
    # long tattered strips at the hem
    xa, xb = int(P[0] - 14 + sw * 0.2), int(Fs[0] + 33 + sw + fl)
    x, k = xa, 0
    while x <= xb:
        wdt = 2 + int(hash01(k, 3, 11) * 3)
        dep = int(hash01(k, frame_i // 2, 12) * 6) + (5 if k % 3 == 1 else 0)
        for i in range(wdt):
            dd = dep - abs(i - (wdt - 1) / 2) * 1.2
            for yy in range(int(bot), int(bot + dd) + 1):
                if yy <= GROUND:
                    m.add((x + i, yy))
        if k % 4 == 2:     # deep tears cut upward into the cloth
            for yy in range(int(bot - 6 - hash01(k, 1, 4) * 10), int(bot) + 1):
                m.discard((x + wdt // 2, yy))
                m.discard((x + wdt // 2 + 1, yy))
        x += wdt
        k += 1
    for hx_, hy_, rr in ((0.62, 0.5, 2.4), (0.84, 0.72, 2.0), (0.4, 0.8, 1.7), (0.7, 0.88, 1.4), (0.55, 0.3, 1.3)):
        cx = Fs[0] + 4 + (26 + sw * 0.6) * hx_ + 4
        cy = top + (bot - top) * hy_
        hole = mask_disc((cx, cy), rr * 1.3, rr)
        m -= hole

    def fold(x, y):
        tt = max(0.0, (y - top) / max(1, bot - top))
        ph = (x - Fs[0] - sw * tt * 0.8) / (6.0 + tt * 3.0) * 2 * math.pi
        return (0.8 * math.sin(ph) * (0.3 + tt), 0.0)
    L["Cape"].paint(n_plate(m, bevel=3, tilt=(0.25, 0.1), strength=0.8, fold=fold), "V", bias=-1, ao=0)
    rim = []
    for (x, y) in m:
        if (x + 1, y) not in m and (x + 2, y) not in m and top + 6 < y < bot - 8:
            rim += [(x - 1, y), (x - 2, y)]
    L["Cape"].decal(rim, ("A", 3))
    L["Cape"].decal([p for p in rim if p[1] % 6 == 0], ("A", 5))
    return m


# =========================================================================== legs: gold plate over dark mail
def draw_legs(L, j):
    Lg = L["Legs"]
    for side in ("far", "near"):
        hip = j["hip_" + side]
        ft = j["foot_" + side]
        ank = (ft[0] + 1, ft[1] - 6)
        kn = j.get("kneel_" + side) or ik(hip, ank, 20, 20, (-1, -0.15))
        bias = -1 if side == "far" else 0
        Lg.paint(n_capsule(hip, kn, 6.6, 5.2), "A", bias=bias)
        Lg.paint(n_capsule(kn, ank, 5.0, 3.8), "A", bias=bias)
        d = (ank[0] - kn[0], ank[1] - kn[1]); dl = math.hypot(*d) or 1
        perp = (-d[1] / dl, d[0] / dl)
        if perp[0] > 0:
            perp = (-perp[0], -perp[1])
        a = add(kn, (perp[0] * 3.0 + d[0] / dl * 4, perp[1] * 3.0 + d[1] / dl * 4))
        b = add(ank, (perp[0] * 2.2, perp[1] * 2.2))
        Lg.decal(line(a, b), ("A", 5 + bias))
        Lg.decal(line(add(a, (-perp[0] * 1.2, -perp[1] * 1.2)), add(b, (-perp[0], -perp[1]))), ("A", 2))
        # verdigris creeping up from the ankle
        for q in mask_capsule(lerp(kn, ank, 0.82), ank, 3.6):     # a thin verdigris tide-line above the sabaton
            if hash01(q[0], q[1] // 2, 5) < 0.35:
                Lg.decal([q], ("N", 3 + bias), only_on=("A",))
        fx, fy = ft
        sab = poly_mask([(fx - 12, fy + 0.5), (fx - 10, fy - 3), (fx - 3, fy - 6.5), (fx + 4, fy - 7.5),
                         (fx + 6, fy - 3), (fx + 6, fy + 0.5)])
        Lg.paint(n_plate(sab, bevel=2.2, tilt=(-0.1, -0.3)), "A", bias=bias)
        for k in range(3):
            Lg.decal(line((fx - 8 + k * 3.5, fy - 5 + k * 0.4), (fx - 6 + k * 3.5, fy)), ("A", 1))
        Lg.decal([(fx - 11, fy), (fx - 10, fy)], ("B", 5 + bias))
        # knee: a small bone skull set into the poleyn, with a gold fan wing
        wing = poly_mask([add(kn, (1, -2)), add(kn, (8, -2)), add(kn, (6, 3)), add(kn, (1, 3))])
        Lg.paint(n_plate(wing, bevel=1.5, tilt=(0.3, -0.2)), "A", bias=bias - 1)
        Lg.paint(n_dome(add(kn, (-1, 0)), 4.8, 4.4, flat=0.9), "B", bias=bias)
        Lg.decal([(int(kn[0] - 3), int(kn[1] - 1)), (int(kn[0] - 1), int(kn[1] - 1))], "OUT")
        Lg.decal([(int(kn[0] - 2), int(kn[1] + 2)), (int(kn[0] - 1), int(kn[1] + 2))], ("B", 1))
        j["knee_" + side] = kn


# =========================================================================== body: gold cuirass, bone ribs, skull belt
def draw_body(L, j, sw):
    Bd = L["Body"]
    C, P, tw = j["C"], j["P"], j["tw"]
    Fs, Ns = j["Fs"], j["Ns"]
    # dark mail skirt
    wl, wr = (P[0] - 12, P[1] - 6), (P[0] + 13, P[1] - 6)
    hem = P[1] + 17
    kf, kn_ = j["knee_near"], j["knee_far"]
    lx, rx = min(kf[0] - 6, P[0] - 16), max(kn_[0] + 6, P[0] + 17)
    mail = poly_mask([wl, wr, (P[0] + 16, P[1] + 2), (rx, hem), (lx, hem), (P[0] - 15, P[1] + 2)])
    for x in range(int(lx), int(rx) + 1):
        if x % 4 in (1, 2):
            mail.add((x, int(hem)))
    Bd.paint(n_plate(mail, bevel=4, tilt=(0.05, 0.2), strength=1.0), "S", bias=-1)
    Bd.decal([p for p in mail if (p[0] + 2 * (p[1] % 2)) % 3 == 0 and p[1] % 2 == 0], ("S", 1))
    # royal tabard: purple with a gold crown over a skull
    ts = j.get("tab_sw", 0)
    tx = P[0] - 5 + tw * 2
    tab_bot = min(GROUND - 5, P[1] + 36)
    tab = poly_mask([(tx - 7, P[1] - 5), (tx + 7, P[1] - 5), (tx + 8 + ts * 0.5, tab_bot - 3),
                     (tx + 4 + ts, tab_bot + 3), (tx + ts, tab_bot - 2), (tx - 4 + ts, tab_bot + 4),
                     (tx - 9 + ts * 0.6, tab_bot - 2)])
    Bd.paint(n_plate(tab, bevel=2.5, tilt=(-0.15, 0.1), strength=0.9,
                     fold=lambda x, y: (0.5 * math.sin((x - tx - ts * (y - P[1]) / 34) * 0.9), 0)), "V")
    edge = [p for p in tab if (p[0] - 1, p[1]) not in tab or (p[0] + 1, p[1]) not in tab]
    Bd.decal(edge, ("A", 4))
    ex, ey = int(tx + ts * 0.3), int(P[1] + 13)
    crown = [(ex - 3, ey - 3), (ex - 3, ey - 4), (ex - 1, ey - 3), (ex - 1, ey - 5), (ex + 1, ey - 3), (ex + 1, ey - 4),
             (ex + 3, ey - 3), (ex + 3, ey - 4)] + [(ex + k, ey - 2) for k in range(-3, 4)]
    Bd.decal(crown, ("A", 5))
    sk = [(ex + a, ey + b) for a in range(-2, 3) for b in range(0, 4) if not (abs(a) == 2 and b == 3)]
    Bd.decal(sk, ("B", 4))
    Bd.decal([(ex - 1, ey + 1), (ex + 1, ey + 1)], "OUT")
    # tassets
    for side, off, bias in (("far", 9, -1), ("near", -9, 0)):
        kx = j["knee_" + side][0]
        top_c = (P[0] + off + tw * 2, P[1] - 5)
        bot_c = ((top_c[0] + kx) / 2 + (2 if side == "far" else -2), P[1] + 13)
        tas = poly_mask([(top_c[0] - 7, top_c[1]), (top_c[0] + 7, top_c[1]), (bot_c[0] + 7, bot_c[1]),
                         (bot_c[0] + 1, bot_c[1] + 3), (bot_c[0] - 6, bot_c[1])])
        Bd.paint(n_plate(tas, bevel=2, tilt=(0.15 if side == "far" else -0.2, 0.25)), "A", bias=bias)
        for yy in (top_c[1] + 6, top_c[1] + 12):
            seam = [p for p in tas if p[1] == int(yy)]
            Bd.decal(seam, ("A", 0))
            Bd.decal([(x, y + 1) for (x, y) in seam if (x, y + 1) in tas], ("A", 4 + bias))
        Bd.decal([p for p in tas if p[1] > bot_c[1] - 2 and hash01(p[0], 0, 9) < 0.5], ("N", 3 + bias), only_on=("A",))
    # cuirass: faceted gold plate
    ridge_top = (C[0] - 6 - tw * 3, C[1] - 13)
    ridge_bot = (P[0] - 3 - tw * 2, P[1] - 7)
    outline = [add(Ns, (-1, -3)), (C[0] - 8, C[1] - 15), (C[0] + 6, C[1] - 16), add(Fs, (4, -3)),
               (C[0] + 20 + tw * 2, C[1] + 4), (P[0] + 13, P[1] - 7), (P[0] - 12, P[1] - 7),
               (C[0] - 19 - tw * 2, C[1] + 3)]
    torso = poly_mask(outline)

    def side_of(p):
        (x1, y1), (x2, y2) = ridge_top, ridge_bot
        return (x2 - x1) * (p[1] + .5 - y1) - (y2 - y1) * (p[0] + .5 - x1)
    front = {p for p in torso if side_of(p) > 0}
    side = torso - front
    Bd.paint(n_plate(front, bevel=4, tilt=(-0.62, -0.32), strength=1.1,
                     fold=lambda x, y: ((x - (C[0] - 12)) * 0.015, (y - (C[1] - 2)) * 0.02)), "A")
    Bd.paint(n_plate(side, bevel=3.5, tilt=(-0.12, -0.3), strength=1.1,
                     fold=lambda x, y: ((x - (C[0] + 2)) * 0.045, (y - (C[1] - 6)) * 0.04)), "A", ao=0)
    # bone ribcage mounted over the breastplate
    for k in range(4):
        y0 = C[1] - 8 + k * 4.2
        rib = bezier((C[0] - 3 - tw * 2, y0), (C[0] - 10 - tw * 2, y0 - 1), (C[0] - 16 - tw * 2, y0 + 2),
                     (C[0] - 16 - tw * 2 + k * 0.8, y0 + 5), 10)
        pts = polyline(rib)
        Bd.decal([q for q in pts if q in torso], ("B", 4 if k < 2 else 3))
        Bd.decal([(x, y + 1) for (x, y) in pts if (x, y + 1) in torso], ("B", 1))
    Bd.decal(line((C[0] - 3 - tw * 2, C[1] - 12), (C[0] - 3 - tw * 2, C[1] + 7)), ("B", 5))   # sternum
    Bd.decal(line((C[0] - 2 - tw * 2, C[1] - 12), (C[0] - 2 - tw * 2, C[1] + 7)), ("B", 2))
    arc = [(int(C[0] + 2 + k - tw * 2), int(C[1] - 12 + 0.05 * (k - 3) ** 2)) for k in range(14)]
    Bd.decal([q for q in arc if q in side], ("A", 5))
    # corrosion blooms
    for k in range(2):     # two verdigris runs weeping down from the seams
        c0 = (C[0] + 4 + k * 7 - tw * 2, C[1] + 1 + k * 3)
        run = [(int(c0[0] + (i % 2)), int(c0[1] + i)) for i in range(5)]
        Bd.decal([q for q in run if q in torso], ("N", 3), only_on=("A",))
    ridge = line(ridge_top, ridge_bot)
    Bd.decal(ridge, ("A", 5))
    Bd.decal([(x + 1, y) for (x, y) in ridge], ("A", 1))
    for k in range(2):
        yy = int(C[1] + 11 + k * 4)
        seam = [p for p in torso if p[1] == yy]
        Bd.decal(seam, ("A", 0))
        Bd.decal([(x, y + 1) for (x, y) in seam if (x, y + 1) in torso], ("A", 4))
    neck_edge = [p for p in torso if (p[0], p[1] - 1) not in torso]
    Bd.decal([p for p in neck_edge if p[1] < C[1] - 8], ("B", 4))
    # belt with a skull buckle
    belt = [p for p in (torso | mail) if P[1] - 8 <= p[1] <= P[1] - 5]
    Bd.decal([p for p in belt if p[1] == P[1] - 8], ("A", 4))
    Bd.decal([p for p in belt if P[1] - 7 <= p[1] <= P[1] - 6], ("S", 1))
    Bd.decal([p for p in belt if p[1] == P[1] - 5], ("A", 1))
    bx, by = int(P[0] - 5 - tw * 2), int(P[1] - 6)
    Bd.paint(n_dome((bx + .5, by + .5), 4.2, 3.8), "B", ao=1)
    Bd.decal([(bx - 1, by), (bx + 2, by)], "OUT")
    Bd.decal([(bx, by - 1), (bx + 1, by - 1)], ("B", 5))
    Bd.decal([(bx, by + 2), (bx + 1, by + 2)], ("B", 1))
    Bd.decal([(bx - 1, by + 3), (bx + 1, by + 3)], ("B", 2))
    return torso


def draw_mantle(L, j, sw):
    """A high gorget of gold with bone spines rising behind the skull (the royal collar)."""
    Bd = L["Body"]
    Fs, Ns, C = j["Fs"], j["Ns"], j["C"]
    hx, hy = j["Hd"]
    gor = poly_mask([add(Ns, (3, -4)), (hx - 9, hy + 10), (hx - 3, hy + 6), (hx + 8, hy + 6), (hx + 13, hy + 10),
                     add(Fs, (-2, -4)), (C[0] + 6, C[1] - 12), (C[0] - 8, C[1] - 12)])
    Bd.paint(n_plate(gor, bevel=3, tilt=(-0.1, -0.35), strength=1.2), "A")
    Bd.decal([p for p in gor if (p[0], p[1] - 1) not in gor], ("A", 5))
    Bd.decal([p for p in gor if (p[0], p[1] + 1) not in gor], ("B", 3))
    # bone spines fanning up behind the head
    for k, (bx, by, tx, ty, w) in enumerate(((8, 6, 16, -10, 2.0), (12, 8, 24, -3, 1.8), (4, 6, 7, -14, 1.8))):
        base = (hx + bx, hy + by)
        tip = (hx + tx, hy + ty - j.get("look", 0))
        Bd.paint(n_plate(poly_mask([(base[0] - w, base[1]), (base[0] + w, base[1]), tip]), bevel=1.2, tilt=(0.3, -0.2),
                         strength=1.3), "B", bias=-1 if k == 1 else 0)
    return gor


# =========================================================================== head: the skull fused into the crown
def draw_head(L, j, frame_i, head_sw):
    Hl = L["Head"]
    hx, hy = j["Hd"]
    look = j.get("look", 0)
    jaw = j.get("jaw", 0)
    # cranium (faces left): a pale bone dome, the face in 3/4 view on the left
    cr = (hx + 1.5, hy - 2 - look * 0.4)
    Hl.paint(n_dome(cr, 7.6, 7.4, flat=0.95, tilt=(-0.2, -0.15)), "B", bias=1)
    face = poly_mask([(hx - 8.5, hy - 4), (hx - 1, hy - 5), (hx + 2.5, hy + 1), (hx + 1, hy + 6), (hx - 7.5, hy + 6.5),
                      (hx - 9.5, hy + 2)])
    Hl.paint(n_plate(face, bevel=1.4, tilt=(-0.45, -0.05), strength=1.0), "B", bias=1, ao=0)
    jawm = poly_mask([(hx - 8, hy + 7 + jaw), (hx + 1.5, hy + 6.5), (hx + 3, hy + 9), (hx - 0.5, hy + 11.5 + jaw),
                      (hx - 7, hy + 10.5 + jaw)])
    Hl.paint(n_plate(jawm, bevel=1.2, tilt=(-0.3, 0.25)), "B", bias=0)
    Hl.decal([(int(hx - 8 + k), int(hy + 6.5 + jaw * 0.5)) for k in range(9)], "OUT")          # mouth line
    for k in range(5):                                                                         # teeth
        x = int(hx - 7.5 + k * 1.8)
        Hl.decal([(x, int(hy + 5.5))], ("B", 5)); Hl.decal([(x + 1, int(hy + 5.5))], ("B", 2))
        Hl.decal([(x, int(hy + 7.5 + jaw))], ("B", 4))
    # sockets: two deep almond hollows (the far one foreshortened), ghost fire burning in both
    s1 = [(int(hx - 8 + a_), int(hy - 2 + b_)) for a_ in range(0, 2) for b_ in range(0, 3)]
    s2 = [(int(hx - 5 + a_), int(hy - 2 + b_)) for a_ in range(0, 4) for b_ in range(0, 3)] + [(int(hx - 4), int(hy + 1)), (int(hx - 3), int(hy + 1))]
    Hl.decal(s1 + s2, "OUT")
    Hl.decal(line((hx - 9, hy - 3), (hx - 1, hy - 3.5)), ("B", 5))                             # brow ridge
    Hl.decal(line((hx - 8, hy + 2), (hx - 2, hy + 3)), ("B", 5))                               # cheekbone
    Hl.decal(line((hx - 1, hy + 2), (hx + 2, hy + 4)), ("B", 2))                               # zygomatic shadow
    Hl.decal([(int(hx - 6), int(hy + 3)), (int(hx - 5), int(hy + 3)), (int(hx - 6), int(hy + 4))], "OUT")   # nasal
    Hl.decal(line((hx + 1, hy - 3), (hx + 4, hy + 2)), ("B", 2))                               # temple hollow
    # crown: a band of corroded gold fused into the skull, five tall spikes
    band = []
    for t in range(0, 23):
        q = lerp((hx - 9, hy - 5 - look * 0.3), (hx + 9, hy - 7 - look * 0.3), t / 22)
        band += [(int(q[0]), int(q[1])), (int(q[0]), int(q[1]) + 1), (int(q[0]), int(q[1]) + 2)]
    spikes = [(0.02, 7, 1.8), (0.24, 11, 2.0), (0.46, 15, 2.2), (0.68, 11, 2.0), (0.9, 7, 1.8)]
    crown_c = j.get("crown", 1.0)
    for k, (t, ht, w) in enumerate(spikes):
        q = lerp((hx - 9, hy - 5 - look * 0.3), (hx + 9, hy - 7 - look * 0.3), t)
        ht *= crown_c
        spk = poly_mask([(q[0] - w, q[1] + 1), (q[0] + w, q[1] + 1), (q[0] + (t - 0.5) * 3, q[1] - ht)])
        Hl.paint(n_plate(spk, bevel=1.2, tilt=(-0.35, -0.25), strength=1.3), "A", bias=-1 if k in (3, 4) else 0)
        Hl.decal(line((q[0] - w + 1, q[1]), (q[0] + (t - 0.5) * 3, q[1] - ht + 1)), ("A", 5))
    Hl.paint({p: (0, -0.3, 1) for p in band}, "A", ao=1)
    Hl.decal([p for i, p in enumerate(band) if i % 3 == 0], ("A", 5))
    Hl.decal([p for i, p in enumerate(band) if i % 3 == 2], ("A", 1))
    Hl.decal([p for p in band if hash01(p[0] // 2, p[1], 31) < 0.15], ("N", 3), only_on=("A",))
    gem = lerp((hx - 9, hy - 5), (hx + 9, hy - 7), 0.46)
    Hl.decal([(int(gem[0]), int(gem[1]) + 1)], "Y2")
    eyes = [(int(hx - 8), int(hy - 1)), (int(hx - 4), int(hy - 1)), (int(hx - 3), int(hy - 1))]
    return eyes, int(hy)


# =========================================================================== arms + pauldrons
def draw_arm(Lr, j, side, bias):
    sh = j["Ns"] if side == "near" else j["Fs"]
    hand = j["hand_" + side]
    pref = j.get("elbow_" + side, (1, 0.3) if side == "near" else (0.3, 1))
    el = ik(sh, hand, 17, 17, pref)
    Lr.paint(n_capsule(sh, el, 5.6, 4.6), "S", bias=bias)                        # dark mail sleeve
    Lr.paint(n_capsule(el, hand, 4.6, 4.0), "A", bias=bias)                      # gold vambrace
    d = (hand[0] - el[0], hand[1] - el[1]); dl = math.hypot(*d) or 1
    u = (d[0] / dl, d[1] / dl)
    for tt, lv in ((0.4, 4), (0.7, 3)):
        c = lerp(el, hand, tt)
        band = [p for p in mask_capsule(c, c, 4.8) if abs((p[0] + .5 - c[0]) * u[0] + (p[1] + .5 - c[1]) * u[1]) < 0.9]
        Lr.decal(band, ("B", lv + bias))
    Lr.paint(n_dome(el, 5.0, 5.0), "A", bias=bias)
    ring = [p for p in mask_disc(el, 5.0) if p not in mask_disc(el, 3.8)]
    Lr.decal([p for p in ring if p[1] >= el[1]], ("A", 5 + bias))
    Lr.paint(n_dome(add(hand, (u[0] * 1.5, u[1] * 1.5)), 4.4, 4.4), "A", bias=bias)
    for k in range(3):   # bone knuckles
        q = (int(hand[0] + u[0] * 2 + (k - 1) * -u[1] * 1.8), int(hand[1] + u[1] * 2 + (k - 1) * u[0] * 1.8))
        Lr.decal([q], ("B", 5 + bias))
    j["cuff_" + side] = lerp(el, hand, 0.8)
    return el


def draw_pauldron_near(L, j):
    Fa = L["FrontArm"]
    Ns = j["Ns"]
    c = add(Ns, (-5, 2))
    lames = [(add(c, (-3, 7)), 9, 4.5), (add(c, (-2, 2)), 10.5, 5.5), (add(c, (0, -3)), 12, 7.5)]
    for i, (lc, rx, ry) in enumerate(lames):
        m = mask_disc(lc, rx, ry)
        m = {p for p in m if p[1] >= lc[1] - ry * (0.2 if i < 2 else 1.0)}
        Fa.paint({p: v for p, v in n_dome(lc, rx, ry, flat=0.95, tilt=(0.05, 0.1)).items() if p in m}, "A")
        rim = [p for p in m if (p[0], p[1] + 1) not in m or (p[0], p[1] + 2) not in m]
        Fa.decal(rim, ("A", 1))
        Fa.decal([p for p in rim if (p[0], p[1] + 1) not in m and p[0] % 4 == 0], ("A", 5))

    tc = lames[2][0]
    # a skull mounted on the pauldron (as in the reference)
    sc = add(tc, (-3, -1))
    Fa.paint(n_dome(sc, 4.6, 4.2, flat=0.9), "B")
    Fa.decal([(int(sc[0] - 3), int(sc[1])), (int(sc[0] - 2), int(sc[1])), (int(sc[0]), int(sc[1])), (int(sc[0] + 1), int(sc[1]))], "OUT")
    Fa.decal([(int(sc[0] - 2), int(sc[1] + 3)), (int(sc[0]), int(sc[1] + 3))], ("B", 1))
    # bone spikes raking up and back
    for k, (bx, by, tx, ty, w) in enumerate(((-7, -5, -10, -15, 2.0), (1, -7, 3, -18, 2.3), (6, -5, 11, -13, 2.0))):
        base = add(tc, (bx, by))
        tip = add(tc, (tx, ty))
        Fa.paint(n_plate(poly_mask([(base[0] - w, base[1] + 1), (base[0] + w, base[1] + 1), tip]), bevel=1.4, tilt=(0.2, -0.1),
                         strength=1.4), "B", bias=-1 if k == 2 else 0)
        Fa.decal(line((base[0] - w + 1, base[1]), tip), ("B", 5))


def draw_pauldron_far(L, j):
    Ba = L["BackArm"]
    Fs = j["Fs"]
    c = add(Fs, (1, -2))
    Ba.paint(n_dome(c, 8.5, 7, flat=0.95), "A", bias=-1)
    Ba.paint(n_dome(add(c, (1, 5)), 7.5, 4, flat=0.9), "A", bias=-1)
    rim = [p for p in mask_disc(add(c, (1, 5)), 7.5, 4) if (p[0], p[1] + 1) not in mask_disc(add(c, (1, 5)), 7.5, 4)]
    Ba.decal(rim, ("B", 2))
    Ba.paint(n_plate(poly_mask([add(c, (-1, -5)), add(c, (4, -4)), add(c, (8, -13))]), bevel=1.2), "B", bias=-1)


GB.draw_cape = draw_cape
GB.draw_legs = draw_legs
GB.draw_body = draw_body
GB.draw_mantle = draw_mantle
GB.draw_head = draw_head
GB.draw_arm = draw_arm
GB.draw_pauldron_near = draw_pauldron_near
GB.draw_pauldron_far = draw_pauldron_far


# =========================================================================== spectral chains + ghost fire (FX layers)
def chain_pts(pts):
    return polyline(pts)


def draw_chains(FX, j, p, fi):
    """Spectral chains shackled to both wrists: dangling loops, or a lash along p['chain'] from the near hand."""
    for side in ("near", "far"):
        cuff = j.get("cuff_" + side)
        if not cuff:
            continue
        layer = FX["FX"] if side == "near" else FX["FXBack"]
        ring = [q for q in mask_disc(cuff, 4.2, 3.0) if q not in mask_disc(cuff, 3.0, 1.9)]
        layer.put(ring, "Y1")
        layer.put([q for q in ring if q[1] < cuff[1]], "Y2")
        lash = p.get("chain") if side == p.get("chain_hand", "near") else None
        if lash:
            pts = [cuff] + list(lash)
        else:
            sw = math.sin(fi * 0.9 + (0 if side == "near" else 2)) * 2
            pts = [cuff, (cuff[0] + 3 + sw, cuff[1] + 9), (cuff[0] - 2 + sw * 1.5, cuff[1] + 17),
                   (cuff[0] + 5 + sw * 2, cuff[1] + 23)]
            pts = bezier(pts[0], pts[1], pts[2], pts[3], 16)
        q = chain_pts(pts)
        for i, c in enumerate(q):
            if not inb(*c):
                continue
            k = i % 4
            layer.put([c], "Y2" if k == 0 else "Y1" if k == 1 else "Y0" if k == 2 else "Y1")
            if k == 1:
                layer.put([(c[0], c[1] - 1)], "Y0")
            if k == 3 and lash:
                layer.put([(c[0] + 1, c[1])], "Y2")


def ghost_flame(FX, base, size, fi, seed=0, layer="FX"):
    bx, by = base
    hgt = size * 1.9
    for y in range(int(by - hgt) - 1, int(by) + 2):
        t = (by - (y + .5)) / hgt
        if t < -0.1 or t > 1:
            continue
        wob = math.sin(fi * 1.9 + t * 5 + seed) * 0.9 * t
        half = size * 0.55 * max(0.0, 1 - t) ** 0.7 + 0.3
        for x in range(int(bx - half - 2), int(bx + half + 2)):
            dx = x + .5 - (bx + wob)
            if abs(dx) <= half:
                r = abs(dx) / max(half, 0.5) * 0.6 + t * 0.7
                if hash01(x, y, fi * 7 + seed) < 0.14 * t:
                    continue
                FX[layer].put([(x, y)], "Y3" if r < 0.35 else "Y2" if r < 0.6 else "Y1" if r < 0.85 else "Y0" if r < 1.05 else "U1")
