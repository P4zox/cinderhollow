"""sp_acolyte -- lightning acolyte (48x56, anchor [24,56]). See gen_spire_enemies.py.

Tall storm-priest in rain-soaked slate-blue robes, deep hood, verdigris copper face-mask with a single vertical
slit, copper chains, lightning-rod staff (dark wood, copper coil, forked prongs). The only glow is the cold
electric blue gathering at the coil / prongs.
"""
import math
import enemy_kit as K
from enemy_kit import Layer, FXLayer, ip, line, polyline, lerp, sub, ik, hash01, n_dome, n_plate, n_capsule, \
    poly_mask, dirv
import spire_enemy_kit as S
from spire_enemy_kit import n_tube, madd, mk

SPEC = dict(idle=4, walk=6, cast=12, hurt=2, death=6)
LAYERS = ["StaffB", "BackArm", "Robe", "Chains", "Head", "Staff", "FrontArm", "FX"]
FLOOR = 55
UB, UT = 22.0, 20.0           # staff: hand -> butt, hand -> top of the coil collar

NEU = dict(P=(22.0, 38.0), C=(23.0, 26.0), Hd=(25.6, 19.6), hup=(0.28, -1.0), hf=(32.0, 33.0), hb=(18.4, 36.0),
           st=dict(hand=(32.0, 33.0), a=-90.0), charge=0, sparks=1, flash=False, hem=0, heap=0.0, drip=True,
           bolt=None, smoke=0, lie=None, wind=0.0, glow=1.0, jolt=False)
AP = mk(NEU)


def chain_px(a, b, sag=0.0, c1="J4", c2="J2"):
    pts = []
    for i in range(13):
        t = i / 12
        pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)))
    out = {}
    for i, q in enumerate(dict.fromkeys(polyline(pts))):
        out[q] = c1 if i % 2 == 0 else c2
    return out


def robe_mask(F, P, ln, floor, fi, seed, sw, w=0.85, heap=0.0):
    hem = floor + 0.6
    fr = P[0] + (5.0 + heap * 3.0) * w - sw * 0.3
    bk = P[0] - (5.8 + heap * 3.4) * w - sw * 0.6
    pts = [F(-3.2 * w, -ln - 1.2), F(2.6 * w, -ln - 1.4), F(3.6 * w, -ln + 4.0), F(3.2 * w, -3.0), (fr, hem - 1.8)]
    n = 9
    for i in range(n + 1):
        t = i / n
        x = fr - (fr - bk) * t
        d = (1.0 + hash01(i, fi // 2, seed) * 1.4) if (i + fi) % 2 == 0 else -0.6
        pts.append((x, hem + d))
    pts += [(bk - 2.4 - sw * 0.5, hem - 0.4), (bk + 0.4, hem - 3.0), F(-4.6 * w, -2.0), F(-4.2 * w, -ln + 3.0)]
    return pts


# =========================================================================== staff
def staff_geom(st):
    d = dirv(st["a"])
    h = st["hand"]
    return madd(h, (d, -st.get("ub", UB))), madd(h, (d, st.get("ut", UT))), d


def draw_staff(L, FX, butt, top, d, charge, fi, sparks):
    """Dark wood shaft, copper coil below the top, forked copper prongs. Returns (tip point, prong tips, coil pts)."""
    nv = (-d[1], d[0])
    L.paint(n_capsule(butt, madd(top, (d, -9.0)), 0.8, 0.8), "W", -1)
    # copper ferrule at the butt
    L.paint(n_capsule(butt, madd(butt, (d, 1.4)), 0.9, 0.9), "J", -1, ao=0)
    # coil: a thicker copper band with bright windings
    c0, c1 = madd(top, (d, -8.6)), madd(top, (d, -2.2))
    cm = L.paint(n_capsule(c0, c1, 1.15, 1.15), "J", -1)
    for k in range(7):
        u = -8.2 + k * 1.0
        a_, b_ = madd(top, (d, u), (nv, -1.4)), madd(top, (d, u + 0.6), (nv, 1.4))
        L.decal([q for q in line(a_, b_) if q in cm], ("J", 4) if k % 2 == 0 else ("J", 1))
    L.decal([q for q in cm if hash01(*q, 21) < 0.2], ("N", 3))           # verdigris bloom on the coil
    # collar + prongs (centre spike, two curved outer tines)
    L.paint(n_capsule(madd(top, (d, -2.2)), top, 0.9, 1.1), "J", -1, ao=0)
    tips = []
    for side in (-1, 0, 1):
        if side == 0:
            pts = [top, madd(top, (d, 5.4))]
        else:
            pts = [madd(top, (nv, side * 0.8)), madd(top, (d, 1.6), (nv, side * 2.4)),
                   madd(top, (d, 4.0), (nv, side * 2.6)), madd(top, (d, 5.0), (nv, side * 2.0))]
        seg = polyline(pts)
        L.fixed({q: ("J4" if i < 1 else "J3") if side == 0 else ("J3" if side < 0 else "J2") for i, q in enumerate(seg)})
        tips.append(pts[-1])
    tip = madd(top, (d, 5.4))
    coil = [madd(top, (d, -8.0 + k * 1.1), (nv, (1.8 if k % 2 else -1.8))) for k in range(6)]
    # prong tips glow with the charge
    if charge > 0:
        for t in tips:
            q = ip(t)
            FX.put([q], "U4" if charge >= 2 else "U3")
            if charge >= 3:
                FX.put([(q[0], q[1] - 1)], "U3")
    # idle sparks crawling along the coil
    if sparks:
        for k in range(sparks):
            j = (fi * 2 + k * 3) % len(coil)
            q = ip(coil[j])
            FX.put([q], "U3" if (fi + k) % 2 else "U2")
            q2 = ip(madd(coil[j], (d, 0.9 if k % 2 else -0.9)))
            FX.put([q2], "U1")
    return tip, tips, coil


def charge_fx(FX, c, tips, level, fi, seed=0):
    """Arcs gathering around the prongs: more, longer, brighter per level (1..4)."""
    n = 2 + level * 2
    R = 3.4 + level * 1.2
    pts = set()
    for k in range(n):
        a = (k / n) * 2 * math.pi + fi * 0.9 + hash01(k, level, 5) * 0.8
        r = R * (0.75 + 0.35 * hash01(k, fi, 7))
        start = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.9)
        end = tips[k % 3] if level >= 2 else (c[0] + math.cos(a) * r * 0.45, c[1] + math.sin(a) * r * 0.4)
        core = "U4" if level >= 3 and k % 2 == 0 else "U3"
        pts |= S.arc_fx(FX, start, end, 3, 1.1, seed + k * 7 + fi, core=core, edge="U1" if level < 3 else "U2")
    if level >= 2:
        S.disc_glow(FX, c, 1.2 + level * 0.5, ("U4", "U3", "U2") if level >= 3 else ("U3", "U2", "U1"))
    if level >= 4:
        for k in range(10):
            a = k * 2 * math.pi / 10 + fi
            q = ip((c[0] + math.cos(a) * (R + 2.5), c[1] + math.sin(a) * (R + 2.0)))
            if k % 2 == fi % 2:
                FX.put([q], "U1")
    return pts


# =========================================================================== body
def draw_aco(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    P, C, Hd = p["P"], p["C"], p["Hd"]
    C, Hd = (C[0], C[1] - 1.4), (Hd[0], Hd[1] - 1.6)        # tall, gaunt proportions
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    shF, shB = F(1.2, -ln + 1.0), F(-2.2, -ln + 1.6)
    floor = FLOOR + 0.0
    # ---- staff
    if p["lie"]:
        butt, top = p["lie"]
        dd = sub(top, butt)
        l_ = math.hypot(*dd)
        d = (dd[0] / l_, dd[1] / l_)
    else:
        butt, top, d = staff_geom(p["st"])
    tip, tips, coil = draw_staff(Ls["Staff"], FX, butt, top, d, p["charge"], fi, p["sparks"])
    info["tip"] = tip
    # ---- back arm
    Ba = Ls["BackArm"]
    hb = p["hb"]
    el = ik(shB, hb, 5.6, 5.6, (-1, 0.5))
    Ba.paint(n_tube([shB, el, hb], [1.7, 1.9, 2.2]), "E", -2)
    Ba.paint(n_dome(hb, 1.0, 1.1), "A", -1, ao=0)
    # ---- robe + mantle
    Rb = Ls["Robe"]
    if p["heap"] < 1.0:
        m = poly_mask(robe_mask(F, P, ln, floor, p["hem"], 5, sw, heap=p["heap"]))
    else:
        m = poly_mask([F(-3.4, -ln - 1.2), F(2.8, -ln - 1.4), F(4.2, 2.0), F(5.0, 9.0), F(-1.0, 11.0), F(-6.0, 8.0),
                       F(-4.8, -2.0)])
    Rb.paint(n_plate(m, 2.0, (-0.05, 0.0), 1.0,
                     fold=lambda x, y: (0.65 * math.sin((x - P[0] - sw * 0.25) * 1.25) *
                                        min(1.0, max(0.0, (y - P[1] + 10) / 12)), 0)), "E", 0)
    ys = [q[1] for q in m]
    yb = max(ys)
    Rb.decal([q for q in m if q[1] >= yb - 4 and hash01(*q, 3) < 0.55 + 0.1 * (q[1] - yb + 4)], ("E", 1))  # soaked hem
    Rb.decal([q for q in m if q[1] >= yb - 1], ("E", 0))
    # wet sheen streaks running down the robe
    for k, xo in enumerate((-1.8, 1.6)):
        a_ = F(xo, -ln + 7 + k * 2)
        Rb.decal([q for q in line(a_, (a_[0] + 0.6, a_[1] + 8 + k * 3)) if q in m and hash01(*q, 9 + k) < 0.7],
                 ("E", 4))
    mantle = [F(-5.0, -ln - 0.2), F(3.4, -ln - 0.8), F(4.4, -ln + 3.6), F(2.6, -ln + 5.6), F(1.0, -ln + 4.8),
              F(-0.8, -ln + 6.8), F(-2.6, -ln + 5.4), F(-4.6, -ln + 7.2 - sw * 0.1), F(-5.6, -ln + 3.0)]
    Rb.paint(n_plate(poly_mask(mantle), 1.4, (-0.1, -0.2), 1.0), "E", 1)
    # ---- chains: copper, draped across the chest, a charm hanging at the hip
    Ch = Ls["Chains"]
    if p["heap"] < 0.5:
        Ch.fixed(chain_px(F(-3.0, -ln + 3.0), F(3.2, -4.0), 1.0))
        Ch.fixed(chain_px(F(-3.6, -3.2), F(3.0, -2.6), 0.5, "J3", "J1"))
        ch = ip(F(1.4, -1.0))
        Ch.fixed({(ch[0], ch[1] + j): ("J3" if j < 2 else "J4") for j in range(3)})
        Ch.fixed({(ch[0] - 1, ch[1] + 2): "J2", (ch[0] + 1, ch[1] + 2): "J2", (ch[0], ch[1] + 3): "J2"})
    # ---- head: deep hood, verdigris mask with a single vertical slit
    Hl = Ls["Head"]
    G = K.basis(Hd, p["hup"])
    hood = [G(-4.4, 4.0), G(-5.0, -0.5), G(-4.2, -4.0), G(-2.2, -6.2), G(0.4, -6.8), G(2.8, -6.0), G(4.6, -3.8),
            G(5.4, -0.8), G(5.2, 2.0), G(3.8, 3.2), G(2.4, 6.0), G(-2.4, 6.4)]
    Hl.paint(n_plate(poly_mask(hood), 1.6, (-0.15, -0.2), 1.1), "E", 0)
    cav = poly_mask([G(1.2, -3.8), G(4.4, -3.4), G(5.0, 0.0), G(4.4, 3.0), G(2.0, 3.8), G(0.8, 0.4)])
    Hl.paint(n_plate(cav, 0.8, (0.2, 0.2)), "E", -2, ao=0)
    mask = poly_mask([G(2.2, -2.8), G(4.4, -2.5), G(5.1, -0.4), G(5.0, 1.8), G(3.8, 3.2), G(2.6, 2.4), G(2.0, 0.0)])
    Hl.paint(n_plate(mask, 1.0, (-0.3, -0.2), 1.0), "N", 0, ao=0)
    Hl.decal([q for q in mask if hash01(*q, 17) < 0.2], ("N", 2))                     # pitted patina
    slit = line(G(4.0, -1.8), G(4.1, 1.8))
    Hl.fixed({q: "OUT" for q in slit})
    rv = ip(G(3.0, -2.0))
    Hl.fixed({rv: "J4"})
    # hood rim: the brim edge catches a little light
    Hl.decal([q for q in line(G(1.0, -4.6), G(4.8, -3.6))], ("E", 4))
    info["head"] = G(3.0, 0.0)
    # ---- front arm: wide wet sleeve, pale hand on the staff
    Fa = Ls["FrontArm"]
    hf = p["hf"]
    el = ik(shF, hf, 5.6, 5.8, (-1, 0.6))
    Fa.paint(n_tube([shF, el, lerp(el, hf, 0.78)], [1.8, 2.0, 2.4]), "E", 0)
    Fa.paint(n_dome(hf, 1.15, 1.2, tilt=(-0.1, -0.1)), "A", 1, ao=0)
    Fa.fixed({(int(hf[0]) + 1, int(hf[1]) + 1): "A3"})
    # ---- cold light from the charge on the near side
    if p["charge"] >= 2 or p["flash"]:
        for L_ in (Hl, Fa, Rb):
            S.rim_light(L_, tip, 6 + p["charge"] * 2.5, cols=("U1", "U0"))
    info["hit"] |= set(m) | set(Hl.px)
    # ---- fx
    if p["charge"] >= 1:
        charge_fx(FX, tip, tips, p["charge"], fi)
    if p["flash"]:
        c = ip(madd(tip, (d, 1.0)))
        S.disc_glow(FX, c, 3.4, ("U4", "U4", "U3", "U2"))
        for ang in range(0, 360, 45):
            L_ = 7 if ang % 90 == 0 else 4
            FX.put(line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_)),
                   "U4" if ang % 90 == 0 else "U3")
        info["flash"] = c
    if p["bolt"]:
        a, b = p["bolt"]
        pts = polyline(S.jag_pts(a, b, 7, 2.2, 13))
        for q in pts:
            FX.put([q], "U4")
            FX.put([(q[0] + 1, q[1])], "U2")
        br = polyline(S.jag_pts(pts[len(pts) // 2], (b[0] - 7, b[1] - 3), 3, 1.2, 5))
        FX.put(br, "U3")
        for k in range(6):
            FX.put([(int(b[0]) - 4 + k * 2, FLOOR - (k % 2))], "U3" if k % 2 else "U2")
    if p["jolt"]:
        for k in range(5):
            a = 2 * math.pi * hash01(k, 1, 44)
            r = 3 + 3 * hash01(k, 2, 44)
            q = ip((tip[0] + math.cos(a) * r, tip[1] + math.sin(a) * r))
            FX.put([q], "U3" if k % 2 else "U2")
    if p["smoke"]:
        for k in range(6):
            t = (k / 6 + fi * 0.17) % 1.0
            q = ip((tip[0] + math.sin(k * 1.7 + t * 5) * 1.5, tip[1] - 2 - t * 7 * p["smoke"]))
            FX.put([q], "E4" if t < 0.5 else "E3")
    if p["drip"] and p["heap"] < 0.5:
        for k, x in enumerate((P[0] + 3.4, P[0] - 3.0, hf[0] + 0.2)):
            ph = (fi * 0.37 + k * 0.41) % 1.0
            y0 = (yb + 1) if k < 2 else hf[1] + 2
            q = (int(x), int(y0 + ph * 4))
            if q[1] <= FLOOR:
                FX.put([q], "E5" if ph < 0.5 else "E4")
    return Ls, info


# =========================================================================== animation
def st(hand, a, **kw):
    d = dict(hand=hand, a=a)
    d.update(kw)
    return d


def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        hand = (32.0, 33.0 + b * 0.2)
        fr.append((200, AP(C=(23.0, 26.0 + b * 0.4), Hd=(25.6 + b * 0.1, 19.6 + b * 0.6), hf=hand,
                           hb=(18.4, 36.0 + b * 0.4), st=st(hand, -90.0), hem=i, sparks=1 + (i % 2))))
    return fr


def a_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.6 * abs(s_)
        hand = (32.4 + 0.8 * c, 33.0 + b)
        a = -90.0 + 4.0 * c
        # keep the butt on the floor: shift the grip so hand - dir*UB lands on FLOOR
        dd = dirv(a)
        ub = (FLOOR - hand[1]) / -dd[1] if dd[1] < 0 else UB
        fr.append((140, AP(P=(22.0 + 0.3 * c, 38.0 + b * 0.3), C=(23.4 + 0.4 * c, 26.0 + b),
                           Hd=(26.0 + 0.4 * c, 19.6 + b), hf=hand, hb=(18.2 - 0.8 * c, 36.0 + b),
                           st=st(hand, a, ub=ub, ut=UB + UT - ub), hem=i, sparks=1, wind=-1.5)))
    return fr


def a_cast():
    RAISE = dict(P=(21.6, 38.0), C=(22.2, 25.8), Hd=(24.2, 19.4), hup=(0.1, -1.0))
    PEAK = dict(P=(21.4, 38.0), C=(21.8, 25.6), Hd=(23.6, 19.0), hup=(0.05, -1.0))
    LUNGE = dict(P=(22.6, 38.0), C=(25.0, 26.2), Hd=(28.4, 20.2), hup=(0.55, -1.0))
    TOT = UB + UT

    def hi(hand, a, ut=13.0):
        return st(hand, a, ut=ut, ub=TOT - ut)
    s2 = hi((30.0, 29.0), -66.0)
    return [
        (140, AP(C=(23.2, 26.4), Hd=(25.8, 20.0), hf=(32.0, 31.0), hb=(19.0, 35.0), st=st((32.0, 31.0), -92.0),
                 sparks=2)),
        (120, AP(**RAISE, hf=(31.0, 30.0), hb=(26.0, 35.0), st=hi((31.0, 30.0), -78.0, 16.0), sparks=2, hem=1)),
        (140, AP(**RAISE, hf=s2["hand"], hb=(25.6, 35.6), st=s2, sparks=2, charge=0, hem=2)),
        (130, AP(**PEAK, hf=s2["hand"], hb=(25.6, 35.6), st=s2, sparks=0, charge=1, hem=0)),
        (130, AP(**PEAK, hf=(30.0, 28.8), hb=(25.6, 35.4), st=hi((30.0, 28.8), -66.0), sparks=0, charge=2, hem=1)),
        (130, AP(**PEAK, hf=(30.0, 28.6), hb=(25.6, 35.2), st=hi((30.0, 28.6), -67.0), sparks=0, charge=3, hem=2)),
        (320, AP(**PEAK, hf=(29.8, 28.4), hb=(25.4, 35.0), st=hi((29.8, 28.4), -68.0), sparks=0, charge=4, hem=0)),
        (80, AP(**LUNGE, hf=(33.0, 28.0), hb=(27.6, 34.4), st=hi((33.0, 28.0), -58.0), sparks=0, flash=True,
                hem=1, wind=3)),
        (120, AP(**LUNGE, hf=(32.0, 29.0), hb=(26.6, 35.0), st=hi((32.0, 29.0), -63.0), sparks=0, jolt=True,
                 smoke=1, hem=2)),
        (140, AP(P=(22.0, 38.0), C=(23.6, 26.0), Hd=(26.4, 19.8), hup=(0.35, -1.0), hf=(31.6, 30.4),
                 hb=(23.0, 35.0), st=hi((31.6, 30.4), -76.0, 17.0), sparks=1, smoke=1, hem=0)),
        (140, AP(hf=(32.0, 32.0), hb=(20.0, 35.4), st=st((32.0, 32.0), -86.0), sparks=1, hem=1)),
        (160, AP(hem=2)),
    ]


def a_hurt():
    return [(90, AP(P=(21.6, 38.0), C=(21.0, 26.4), Hd=(22.4, 20.4), hup=(-0.3, -1.0), hf=(30.4, 33.4),
                    hb=(16.4, 35.0), st=st((30.4, 33.4), -98.0), jolt=True, sparks=0)),
            (140, AP(P=(21.8, 38.0), C=(22.2, 26.2), Hd=(24.2, 19.9), hup=(0.05, -1.0), hf=(31.4, 33.2),
                     st=st((31.4, 33.2), -93.0), sparks=2))]


def a_death():
    sn = ["BackArm", "Robe", "Chains", "Head", "FrontArm"]
    pal = ("U3", "U2", "E4", "E3", "E2")
    lie = ((5.0, 54.0), (39.0, 53.2))
    KN = dict(P=(21.4, 44.0), C=(24.0, 33.0), Hd=(27.8, 27.4), hup=(0.8, -1.0), hf=(30.0, 44.0), hb=(18.0, 45.0),
              heap=0.9, drip=False)

    def col(sq, burn, spread):
        return S.collapse(sn, sq, burn, seed=6, spread=spread, pal=pal, cx=22.0, rise=14)
    return [
        (100, AP(P=(21.4, 38.0), C=(20.6, 26.6), Hd=(21.6, 20.8), hup=(-0.45, -1.0), hf=(30.0, 32.4),
                 hb=(16.0, 34.0), st=st((30.0, 32.4), -104.0), jolt=True, sparks=0, charge=1)),
        (110, AP(P=(21.6, 40.0), C=(22.8, 28.6), Hd=(25.6, 22.6), hup=(0.4, -1.0), hf=(31.4, 34.0),
                 hb=(18.0, 38.0), st=st((31.4, 34.0), -70.0), heap=0.4, charge=3, sparks=0, drip=False,
                 bolt=((0, 0), (0, 0)))),
        (150, AP(**KN, st=st((33.0, 40.0), -38.0), sparks=0, charge=1, smoke=1)),
        (140, AP(**KN, lie=lie, sparks=1, smoke=1, post=col(0.62, 0.1, 0.3))),
        (160, AP(**KN, lie=lie, sparks=1, post=col(0.32, 0.18, 0.5))),
        (700, AP(**KN, lie=lie, sparks=0, smoke=1, post=col(0.16, 0.22, 0.6))),
    ]


def build(build_ase):
    K.setup(48, 56)
    anims_spec = [("idle", a_idle), ("walk", a_walk), ("cast", a_cast), ("hurt", a_hurt), ("death", a_death)]
    # death frame 1: aim the last discharge from the actual prong tip down to the floor in front
    _orig = a_death

    def death_fixed():
        fr = _orig()
        ms, p = fr[1]
        butt, top, d = staff_geom(p["st"])
        tip = madd(top, (d, 5.4))
        p["bolt"] = (tip, (tip[0] + 4.0, FLOOR))
        return fr
    anims_spec[4] = ("death", death_fixed)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_aco, anims_spec, sway_key="C", loops=("idle", "walk"))
    hb = S.hurtbox(anims, ["Robe", "Head"], inset=(2, 2, 2, 0))
    meta = {"native": 1, "frame": [48, 56], "anchor": [24, 56],
            "hurtbox": hb,
            "attacks": {},
            "spawn": {"cast": {"frame": 7, "at": S.spawn_pt(infos["cast"][7]["flash"])}},
            "telegraph": {"cast": {"frame": 6, "at": S.spawn_pt(infos["cast"][6]["tip"])}},
            "notes": "faces right, feet on the bottom row; ranged only (no melee). cast: 0-2 plant and raise the "
                     "lightning-rod staff, 3-6 arcs gather at the prongs (brighter each frame), 6 = held peak "
                     "(telegraph at the staff tip), 7 = release flash: spawn the chain bolt at spawn.cast.at, 8-11 "
                     "recover. The coil/prongs are the only light source (a small cold-blue point light at the staff "
                     "tip suits idle/cast). death: recoils, a last discharge arcs from the staff into the floor "
                     "(frame 1), kneels and collapses into sodden robes, staff lying beside them."}
    S.export("sp_acolyte", LAYERS, anims, meta, build_ase)
    return meta
