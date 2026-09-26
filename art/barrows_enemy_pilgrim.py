"""db_pilgrim (48x48, anchor [24,48], faces right). See gen_barrows_enemies.py.

A drowned pilgrim: slender and hunched in a sodden black-teal hooded robe, face lost in the hood's shadow with two
faint teal eye-points, long thin grey-green arms with long fingers, a small verdigris censer on a chain whose
embers burn bioluminescent teal, barnacles crusted on the near shoulder, black water dripping from hood, sleeves,
hem and censer. Tags: idle(4) walk(6) swing(10) lunge(8) rise(6) hurt(2) death(6).
"""
import math
import enemy_kit as K
from enemy_kit import Layer, FXLayer, Rig, ip, line, lerp, add, sub, ik, hash01, n_dome, n_plate, n_capsule, \
    poly_mask, dirv, mask_disc
import spire_enemy_kit as S
from spire_enemy_kit import n_tube, madd, mk
import barrows_enemy_kit as B

SPEC = dict(idle=4, walk=6, swing=10, lunge=8, rise=6, hurt=2, death=6)
LAYERS = ["CenserB", "BackArm", "Legs", "Robe", "Head", "FrontArm", "Censer", "FX"]
FLOOR = 47
CH = 5.5            # idle chain length (hand -> censer lid)

NEU = dict(P=(21.8, 32.6), C=(24.8, 22.4), Hd=(29.0, 19.2), hup=(0.38, -0.93),
           hipn=(22.8, 33.4), hipf=(20.8, 33.0), fn=(26.0, FLOOR), ff=(18.6, FLOOR), kpref=(1.0, -0.2),
           hf=(31.0, 33.2), hb=(26.6, 36.4), cen=None, cback=False, chain=CH, glow=1.0, flare=0.0, eyes=2,
           smear=None, claw=None, rot=0.0, piv=(24.0, 47.0), sink=0.0, hem=0, wind=0.0, glint=False,
           splash=None, heap=None, drip=True, fingers=0.0, fingersb=0.0, cfloor=None, eyestar=False,
           attack_hand=False, lift=1.5)
PP = mk(NEU)


# =========================================================================== censer
def censer(L, FX, top, down, glow, fi, flare=0.0):
    """Small verdigris censer hanging from `top` (the lid ring) along unit vector `down`.
    Returns (centre, pixel set, bottom point)."""
    dx, dy = down
    rx, ry = dy, -dx
    T = lambda a, b: (top[0] + rx * a + dx * b, top[1] + ry * a + dy * b)
    c = T(0, 3.5)
    body = L.paint(n_dome(c, 2.45, 2.45, tilt=(-0.05, -0.05)), "dV", 0)
    lid = L.paint(n_dome(T(0, 1.3), 1.35, 1.2, tilt=(-0.1, -0.3)), "dV", 1, ao=0)
    L.fixed({ip(T(0, -0.1)): "dV4"})                               # ring
    band = [q for q in line(T(-2.6, 2.4), T(2.6, 2.4)) if q in body]
    L.decal(band, ("dV", 1))
    # pierced holes: the teal embers inside show through
    g = glow + 0.35 * math.sin(fi * 2.1) + flare
    holes = [T(-1.1, 3.6), T(1.0, 3.6), T(0.0, 4.6), T(-0.1, 3.2)]
    for k, h in enumerate(holes):
        if glow <= 0.05:
            col = "dV0"
        elif k == 3 and g > 1.6:
            col = "dG4"
        elif g > 1.1 or k == 2:
            col = "dG3" if k < 3 else "dG2"
        else:
            col = "dG2"
        L.fixed({ip(h): col})
    foot = ip(T(0, 6.1))
    L.fixed({foot: "dV2"})
    pix = body | lid | {foot}
    if glow > 0.4:
        # teal ember-smoke curling up out of the lid
        for k in range(3):
            t = ((fi * 0.37 + k / 3.0) % 1.0)
            q = ip((top[0] + math.sin(k * 2.1 + fi * 1.3) * 1.2 - t * 1.0, top[1] - 1.0 - t * 5.5))
            if q not in pix:
                FX.put([q], "dG2" if t < 0.35 else "dG1" if t < 0.7 else "dG0")
        if glow + flare > 1.6:
            B.halo_dots(FX, c, 4.2 + flare * 0.8, 10, fi, ("dG1", "dG0"), skip=pix)
    return c, pix, T(0, 6.2)


def chain_px(a, b, sag=0.0):
    pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t))
           for t in [i / 12 for i in range(13)]]
    return {q: ("dV4" if i % 2 == 0 else "dV1") for i, q in enumerate(dict.fromkeys(K.polyline(pts)))}


# =========================================================================== body parts
def robe_pts(F, P, ln, hemy, seed, sw):
    pts = [F(-4.1, -ln + 2.2), F(-3.5, -ln - 0.2), F(-1.3, -ln - 1.5), F(1.4, -ln - 1.1), F(3.0, -ln + 0.8),
           F(3.4, -ln + 4.6), F(2.9, -3.2), F(3.2, 0.6)]
    fr = P[0] + 4.3 - sw * 0.3
    bk = P[0] - 4.6 - sw * 0.5
    pts.append((fr + 0.4, hemy - 2.2))
    n = 8
    for i in range(n + 1):
        t = i / n
        x = fr - (fr - bk) * t
        long_ = (i + seed) % 3 == 0
        d = (1.2 + 1.0 * hash01(i, seed, 5)) if long_ else (-0.3 + 0.7 * hash01(i, 2, 7))
        pts.append((x, hemy + d + t * 0.8))
    pts += [(bk - 1.4 - sw * 0.6, hemy + 1.2), (bk - 0.1, hemy - 3.2), F(-4.4, -0.4), F(-4.7, -ln + 5.0)]
    return pts


def hand_fingers(L, hand, d, spread, bias, n=3, length=2.6):
    """Long thin grey-green fingers (claws) fanning out from `hand` along unit vector d."""
    a0 = math.degrees(math.atan2(d[1], d[0]))
    pix = {}
    for k in range(n):
        a = a0 + (k - (n - 1) / 2) * (12 + 22 * spread)
        ln_ = length * (1.0 if k != n - 1 else 0.85)
        seg = line(madd(hand, (dirv(a), 0.9)), madd(hand, (dirv(a), 0.9 + ln_)))
        for j, q in enumerate(seg):
            pix[q] = "dF2" if j == len(seg) - 1 else ("dF4" if bias >= 0 and k == 0 else "dF3" if bias >= 0 else "dF2")
    L.fixed(pix)
    return set(pix)


def arm(L, sh, hand, pref, bias, spread, R, l1=7.0, l2=7.4, claws=True):
    B.check_reach("arm", sh, hand, l1 + l2)
    el = ik(sh, hand, l1, l2, pref)
    cuff = lerp(el, hand, 0.35)
    # sodden sleeve (upper arm + elbow), ragged cuff
    L.paint(n_tube([sh, el, cuff], [1.45, 1.2, 1.5]), "dC", bias)
    # bare wasted forearm
    L.paint(n_tube([cuff, hand], [0.7, 0.7]), "dF", bias, ao=0)
    L.paint(n_dome(hand, 0.9, 0.9), "dF", bias + 1, ao=0)
    d = sub(hand, el)
    ln = math.hypot(*d) or 1
    d = (d[0] / ln, d[1] / ln)
    pix = set()
    if claws:
        pix = hand_fingers(L, hand, d, spread, bias)
    # hanging rag strip off the cuff
    rag = ip(madd(cuff, ((0, 1), 1.8)))
    L.fixed({rag: "dC2", (rag[0], rag[1] + 1): "dC1"})
    return el, cuff, pix


def leg(L, hip, foot, pref, bias):
    ank = (foot[0], foot[1] - 1.3)
    B.check_reach("leg", hip, ank, 15.6)
    kn = ik(hip, ank, 7.8, 7.8, pref)
    L.paint(n_tube([hip, kn, ank], [1.35, 1.05, 0.85]), "dC", bias - 1)
    # rag wraps on the shin, bare bony foot
    L.decal([q for q in line(lerp(kn, ank, 0.35), lerp(kn, ank, 0.4)) if q in L.px], ("dC", 3))
    toe = (ank[0] + 2.6, foot[1] - 0.4)
    L.paint(n_capsule(ank, toe, 0.95, 0.7), "dF", bias - 1, ao=0)
    return kn


def draw_head(Hl, FX, R, Hd, hup, eyes, fi, info, star=False):
    G0 = K.basis(Hd, hup)
    G = lambda a, b: R.T(G0(a, b))
    hood = [G(-3.0, 3.0), G(-3.8, 1.4), G(-6.8, 2.2), G(-5.0, -1.0), G(-3.6, -3.4), G(-1.2, -5.0), G(1.4, -4.9),
            G(3.3, -3.4), G(4.5, -1.2), G(4.0, -0.5), G(3.6, 1.4), G(3.8, 2.8), G(2.4, 3.7), G(-1.0, 3.9)]
    hm = poly_mask(hood)
    Hl.paint(n_plate(hm, 1.7, (-0.12, -0.25), 1.15), "dC", 1)
    # the face: a deep shadow under the hood lip
    cav = poly_mask([G(1.2, -2.3), G(4.0, -0.9), G(3.7, 1.3), G(3.5, 2.8), G(1.7, 3.0), G(0.7, 0.6)]) & hm
    Hl.fixed({q: "dC0" for q in cav})
    # hood lip / wet sheen along the top fold
    Hl.decal([q for q in line(G(-4.4, -1.4), G(-1.2, -4.0)) if q in hm and q not in cav], ("dC", 4))
    Hl.decal([q for q in line(G(-5.6, 1.6), G(-3.4, 0.8)) if q in hm], ("dC", 1))
    Hl.decal([q for q in line(G(1.0, -2.8), G(4.2, -1.2)) if q in hm and q not in cav], ("dC", 3))
    # chin: a sliver of drowned grey flesh catching light at the bottom of the cavity
    ch = [ip(G(2.8, 2.6)), ip(G(3.3, 2.4))]
    Hl.fixed({q: "dF2" for q in ch if q in cav})
    # the two eye-points
    e1, e2 = ip(G(1.9, 0.3)), ip(G(3.6, 0.4))
    if e2 == e1:
        e2 = (e1[0] + 2, e1[1])
    if eyes > 0:
        cols = {1: ("dG1", "dG1"), 2: ("dG3", "dG2"), 3: ("dG4", "dG3")}[eyes]
        Hl.fixed({e2: cols[0], e1: cols[1]})
        if eyes >= 3:
            FX.put([(e2[0] + 1, e2[1])], "dG2")
    info["eye"] = e2
    info["head"] = G(0.5, -1.0)
    info["hoodlip"] = G(4.2, -0.8)
    if star:
        B.star(FX, e2, 2, diag=False)
    return hm


# =========================================================================== main draw
def draw_pilgrim(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    R = Rig(p["rot"], p["piv"], off=(0, p["sink"]))
    if p["heap"] is not None:
        return draw_heap(p, fi, Ls, FX, info)
    if p["lift"]:                   # global leg-length tune: raise everything above the feet
        p = dict(p)
        for k in ("P", "C", "Hd", "hipn", "hipf", "hf", "hb", "cen"):
            if p[k] is not None:
                p[k] = (p[k][0], p[k][1] - p["lift"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F0 = K.basis(P, up)
    F = lambda a, b: R.T(F0(a, b))
    shF, shB = F(1.2, -ln + 1.6), F(-2.0, -ln + 2.0)
    hemy = min(FLOOR - 0.2, P[1] + 7.2)
    drops = []
    # ---- censer (on its chain from the near hand, or lying on the floor)
    hand = R.T(p["hf"])
    lc = None
    if p["cfloor"] is not None:
        top, down = p["cfloor"]
        CL = Ls["Censer"]
        lc, lpix, bot = censer(CL, FX, top, down, p["glow"], fi, p["flare"])
        CL.fixed(chain_px(hand, top, 0.6))
    else:
        if p["cen"] is not None:
            top = R.T(p["cen"])
        else:
            top = (hand[0] + 0.4 - sw * 0.45, hand[1] + p["chain"])
        dv = sub(top, hand)
        dl = math.hypot(*dv) or 1
        down = (dv[0] / dl, dv[1] / dl)
        if down[1] < 0.25:                      # whirled high: the censer trails its chain but still hangs
            down = (down[0] * 0.6, max(down[1], 0.2) + 0.55)
            l2 = math.hypot(*down)
            down = (down[0] / l2, down[1] / l2)
        CL = Ls["CenserB"] if p["cback"] else Ls["Censer"]
        lc, lpix, bot = censer(CL, FX, top, down, p["glow"], fi, p["flare"])
        CL.fixed(chain_px(hand, top, 0.5 if dl < 7 else 0.0))
        drops.append(bot)
    info["censer"] = lc
    info["hit"] |= lpix
    if p["glint"]:
        B.star(FX, (lc[0] - 1.5, lc[1] - 2.0), 3)
    # ---- legs
    Lg = Ls["Legs"]
    for k, (hip, foot) in enumerate(((p["hipf"], p["ff"]), (p["hipn"], p["fn"]))):
        leg(Lg, R.T(hip), R.T(foot), p["kpref"], -2 if k == 0 else 0)
    # ---- far arm
    Ba = Ls["BackArm"]
    hb = R.T(p["hb"])
    _, cuffb, _ = arm(Ba, shB, hb, (-1, 0.45), -2, p["fingersb"], R)
    drops.append(add(cuffb, (0, 2)))
    # ---- robe
    Rb = Ls["Robe"]
    m = poly_mask([R.T(q) for q in robe_pts(F0, P, ln, hemy, p["hem"], sw)])
    Rb.paint(n_plate(m, 2.6, (-0.05, 0.0), 1.0,
                     fold=lambda x, y: (0.3 * math.sin((x - P[0] - sw * 0.3) * 0.9) *
                                        min(1.0, max(0.0, (y - P[1] + 4) / 9)), 0)), "dC", 0)
    ys = [q[1] for q in m]
    yb = max(ys)
    Rb.decal([q for q in m if q[1] >= yb - 1], ("dC", 1))
    # soaked darker band above the hem (the tide line) and a pale salt line
    Rb.decal([q for q in m if q[1] == yb - 4 and (q[0] + 1, q[1]) in m and (q[0] - 1, q[1]) in m], ("dC", 2))
    # cord belt + a small bone scallop badge (pilgrim token) on the chest
    Rb.decal([q for q in line(F(-5.0, -2.6), F(3.8, -2.9)) if q in m], ("dV", 1))
    kq = ip(F(3.4, -2.4))
    Rb.fixed({kq: "dV3", (kq[0], kq[1] + 1): "dV2", (kq[0], kq[1] + 2): "dV1"})
    bq = ip(F(2.2, -ln + 4.2))
    Rb.fixed({bq: "dB4", (bq[0] + 1, bq[1]): "dB3", (bq[0], bq[1] + 1): "dB2", (bq[0] + 1, bq[1] + 1): "dB2"})
    # a strand of dead kelp caught on the belt
    kx, ky = ip(F(-2.4, -2.4))
    for j in range(5):
        Rb.fixed({(kx - (1 if j > 2 else 0) + (1 if sw > 1 and j > 3 else 0), ky + j): "dV1" if j % 2 else "dV2"})
    # hem drips: the robe is sodden
    for i in range(4):
        drops.append(((m and min(q[0] for q in m)) + 2 + i * 3.1, yb + 0.2))
    info["hit"] |= set()
    # ---- head / hood
    Hl = Ls["Head"]
    draw_head(Hl, FX, R, Hd, p["hup"], p["eyes"], fi, info, p["eyestar"])
    drops.append(info["hoodlip"])
    # ---- near arm + barnacles on the shoulder
    Fa = Ls["FrontArm"]
    _, cuff, fpix = arm(Fa, shF, hand, (-1, 0.55), 0, p["fingers"], R, claws=True)
    drops.append(add(cuff, (0, 2)))
    info["claw"] = fpix | {ip(hand)}
    so = shF
    B.barnacles(Fa, [(add(so, (-1.2, -1.7)), 1.3), (add(so, (1.1, -1.6)), 1.0), (add(so, (-3.3, -0.6)), 0.9)],
                seed=1)
    # ---- teal under-light from the censer on nearby cloth (restrained)
    if lc is not None and p["glow"] > 0.3:
        rad = 3.0 + p["glow"] * 1.6 + p["flare"] * 1.6
        for L_ in (Rb, Fa, Hl):
            B.glow_rim(L_, lc, rad)
    # ---- fx
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= K.swept(FX, R.T(g0), a0, R.T(g1), a1, u0, u1, hw=1.0, pal="tide2", taper=0.3,
                                   exclude=lpix, clip_y=FLOOR)
    if p["claw"]:
        for (a, b_) in p["claw"]:
            d = sub(b_, a)
            dl = math.hypot(*d) or 1
            nx, ny = -d[1] / dl, d[0] / dl
            for k, o in enumerate((-1.3, 1.3)):
                seg = line((a[0] + nx * o, a[1] + ny * o), (b_[0] + nx * o, b_[1] + ny * o))
                for j, q in enumerate(seg):
                    if j > len(seg) * (0.35 + 0.15 * k) and q not in info["claw"]:
                        FX.put([q], "dF5" if j > len(seg) * 0.8 else "dF3" if j > len(seg) * 0.6 else "dF2")
                info["hit"] |= set(seg)
    if p["attack_hand"]:
        info["hit"] |= info["claw"]
    if p["splash"]:
        c, f = p["splash"]
        for k in range(9):
            a = -math.pi * (0.12 + 0.76 * hash01(k, 1, 31))
            r = 1.5 + 6.5 * f * (0.45 + 0.55 * hash01(k, 2, 31))
            q = ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.8 + f * f * 3))
            if q[1] <= FLOOR:
                FX.put([q], ("dG3", "dW6", "dW4")[k % 3])
    if p["drip"]:
        B.drips(FX, drops, fi, floor=FLOOR, period=5, seed=3,
                skip=set().union(*[set(L.px) for L in Ls.values() if isinstance(L, Layer)]))
    if p["sink"] > 0.5:
        emerge(Ls, FX, fi, p["sink"])
    return Ls, info


def emerge(Ls, FX, fi, sink):
    """Black water surface where the body breaks the floor line: a band over the cut + a splash crown."""
    xs = [x for L in Ls.values() if isinstance(L, Layer) for (x, y) in L.px if y >= FLOOR - 1]
    if not xs:
        return
    x0, x1 = min(xs) - 2, max(xs) + 2
    for x in range(x0, x1 + 1):
        FX.put([(x, FLOOR)], "dW2" if (x + fi) % 3 else "dW4")
        if x0 + 1 <= x <= x1 - 1 and (x * 7 + fi) % 4 != 0:
            FX.put([(x, FLOOR - 1)], "dW3" if (x + fi) % 2 else "dW4")
    FX.put([(x0, FLOOR - 1), (x1, FLOOR - 1)], "dW6")
    FX.put([(x0 - 1, FLOOR - 2), (x1 + 1, FLOOR - 2)], "dW5")
    for k in range(5):                                   # droplets thrown up
        if sink < 4 and k > 2:
            continue
        x = x0 + (x1 - x0) * hash01(k, fi, 11)
        y = FLOOR - 3 - 5 * hash01(k, fi, 12)
        FX.put([ip((x, y))], "dW6" if k % 2 else "dW5")


def draw_heap(p, fi, Ls, FX, info):
    """Death: a sodden heap of robe on the floor, a thin hand reaching out, the censer guttering beside it."""
    f = p["heap"]                     # 0 = fresh (taller) .. 1 = settled
    Rb = Ls["Robe"]
    top = 37.2 + 3.0 * f
    x0, x1 = 12.5 - 1.5 * f, 38.0 + 1.0 * f
    pts = [(x0, FLOOR + 1), (x0 + 1.5, FLOOR - 2.2), (x0 + 5.0, top + 3.6), (x0 + 9.0, top + 1.0), (x0 + 13.0, top),
           (x0 + 17.0, top + 1.8), (x1 - 4.5, top + 0.6 + f), (x1 - 1.5, top + 3.0), (x1, FLOOR - 1.5), (x1 + 1.0, FLOOR + 1)]
    m = poly_mask(pts)
    Rb.paint(n_plate(m, 2.4, (-0.1, -0.1), 1.0, fold=lambda x, y: (0.5 * math.sin(x * 1.1), 0)), "dC", 0)
    Rb.decal([q for q in m if q[1] >= FLOOR], ("dC", 1))
    kx = int(x0 + 7)
    for j in range(4):
        Rb.fixed({(kx + (j > 1), int(top + 4 + j)): "dV1" if j % 2 else "dV2"})
    # the hood lump at the front, eye-points dark
    Hl = Ls["Head"]
    hc = (x1 - 5.0, top + 2.6 + f * 0.8)
    Hl.paint(n_dome(hc, 4.0, 3.2 - f * 0.6, tilt=(0.1, -0.2)), "dC", 1)
    Hl.fixed({q: "dC0" for q in mask_disc((hc[0] + 2.2, hc[1] + 1.4), 1.6, 1.2) if q in Hl.px})
    # barnacled shoulder still showing
    B.barnacles(Rb, [((x0 + 13.0, top + 1.2), 1.1), ((x0 + 15.0, top + 1.6), 0.9), ((x0 + 11.4, top + 2.0), 0.8)],
                seed=2)
    # a thin hand reaching out on the floor
    Fa = Ls["FrontArm"]
    a, b_ = (x1 - 2.0, FLOOR - 1.2), (x1 + 3.4, FLOOR - 0.8)
    Fa.paint(n_tube([a, b_], [0.8, 0.75]), "dF", -1)
    Fa.fixed({(int(b_[0]) + 1, FLOOR - 1): "dF2", (int(b_[0]) + 2, FLOOR): "dF1", (int(b_[0]) + 1, FLOOR): "dF2"})
    # censer lying on its side, embers going out
    CL = Ls["Censer"]
    lc, lpix, _ = censer(CL, FX, (x1 + 7.0, FLOOR - 3.6), (0.2, 0.98), p["glow"], fi)
    info["censer"] = lc
    # black water seeping out
    B.puddle(FX, x0 - 2 - 3 * f, x1 + 3 + 3 * f, FLOOR, fi, 5)
    if p["drip"]:
        B.drips(FX, [(x0 + 5, top + 3.6), (x1 - 2, top + 3.0)], fi, floor=FLOOR, seed=9, skip=set(Rb.px))
    return Ls, info


# =========================================================================== animation
def a_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        sway = (0.0, 0.6, 0.0, -0.6)[i]
        fr.append((230, PP(C=(24.8 - b * 0.15, 22.4 + b * 0.45), Hd=(29.0 - b * 0.2, 19.2 + b * 0.7),
                           hf=(31.0, 33.2 + b * 0.4), hb=(26.6 - b * 0.2, 36.4 + b * 0.4),
                           cen=(31.4 + sway, 33.2 + b * 0.4 + CH), hem=i, glow=(1.0, 1.2, 0.9, 1.1)[i],
                           fingers=0.1 * b, eyes=2)))
    return fr


def a_walk():
    fr = []
    # feet: planted 3 frames moving back 3 px/frame (no sliding), then a 3-frame swing forward
    plant = [27.0, 24.0, 21.0]
    swing = [(22.4, 1.6), (25.2, 2.3), (27.6, 0.9)]

    def foot(k):
        k %= 6
        if k < 3:
            return (plant[k], FLOOR), 0.0
        x, h = swing[k - 3]
        return (x, FLOOR - h), h
    for i in range(6):
        fnear, hn = foot(i)
        ffar, hf_ = foot(i + 3)
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.9 * abs(math.sin(ph * 1.0 + 0.4))          # dip on each plant
        lurch = 0.5 * c
        hand = (31.0 + lurch * 0.6, 33.4 + b * 0.5)
        fr.append((170, PP(P=(21.8 + lurch * 0.3, 32.6 + b * 0.6), C=(25.0 + lurch, 22.6 + b),
                           Hd=(29.3 + lurch * 1.2, 19.4 + b * 1.2), hipn=(22.8 + lurch * 0.3, 33.4 + b * 0.6),
                           hipf=(20.8 + lurch * 0.3, 33.0 + b * 0.6), fn=fnear, ff=ffar,
                           hf=hand, hb=(26.0 - c * 1.6, 36.4 + b * 0.5), cen=(hand[0] - 0.8 * s_, hand[1] + CH),
                           hem=i, glow=1.0 + 0.15 * s_, wind=-1.0, eyes=2)))
    return fr


LEAN_B = dict(P=(21.0, 33.0), C=(23.6, 23.2), Hd=(27.8, 19.0), hup=(0.2, -0.98))
STRIKE = dict(P=(22.4, 33.4), C=(27.4, 24.4), Hd=(32.8, 22.0), hup=(0.6, -0.8), hipn=(23.4, 34.2),
              hipf=(21.4, 33.8), fn=(28.4, FLOOR), ff=(17.6, FLOOR))


def a_swing():
    return [
        (130, PP(**LEAN_B, hf=(27.0, 33.0), hb=(28.0, 36.0), cen=(24.5, 39.0), cback=True, glow=1.1, fingersb=0.3)),
        (120, PP(**LEAN_B, hf=(22.6, 30.4), hb=(28.4, 34.6), cen=(13.8, 32.0), cback=True, glow=1.3, chain=10)),
        (120, PP(**dict(LEAN_B, C=(23.2, 23.0), Hd=(27.2, 18.6)), hf=(20.4, 24.6), hb=(28.6, 33.6), cen=(12.4, 18.0),
                 cback=True, glow=1.5, hem=1)),
        (130, PP(**dict(LEAN_B, C=(23.0, 22.8), Hd=(26.8, 18.4), hup=(0.1, -1)), hf=(21.4, 19.4), hb=(29.0, 33.0),
                 cen=(15.6, 10.0), glow=1.8, flare=0.4, eyes=3, hem=2)),
        (340, PP(**dict(LEAN_B, C=(22.8, 22.6), Hd=(26.6, 18.2), hup=(0.08, -1)), hf=(21.8, 18.4),
                 hb=(29.2, 32.8), cen=(15.8, 8.6), glow=2.2, flare=0.9, eyes=3, glint=True, hem=0)),
        (70, PP(**STRIKE, hf=(32.0, 25.4), hb=(23.0, 34.0), cen=(42.4, 25.4), glow=2.0, eyes=3, wind=3,
                smear=[((21.8, 18.4), -118, (32.0, 25.4), 0, 8.0, 14.5)])),
        (80, PP(**dict(STRIKE, C=(27.8, 25.0), Hd=(33.2, 22.8)), hf=(33.0, 30.6), hb=(22.6, 34.4),
                cen=(43.2, 37.2), glow=1.9, eyes=3, wind=3, hem=1,
                smear=[((32.0, 25.4), 0, (33.0, 30.6), 38, 8.0, 15.0)])),
        (150, PP(**dict(STRIKE, C=(27.6, 25.4), Hd=(33.0, 23.4)), hf=(32.6, 33.0), hb=(22.8, 35.0),
                 cen=(41.0, 39.4), glow=1.5, eyes=2, hem=2, splash=((42.0, FLOOR), 0.6))),
        (160, PP(P=(21.6, 33.2), C=(26.0, 23.8), Hd=(30.8, 20.4), hup=(0.45, -0.9), hf=(31.8, 33.4),
                 hb=(25.0, 36.0), cen=(36.0, 40.0), glow=1.2, hem=0, splash=((42.0, FLOOR), 1.0))),
        (170, PP(hf=(31.0, 33.2), cen=(32.6, 38.8), glow=1.0, hem=1)),
    ]


CROUCH = dict(P=(19.8, 36.0), C=(22.4, 27.8), Hd=(27.2, 25.2), hup=(0.55, -0.84), hipn=(20.8, 36.8),
              hipf=(18.8, 36.4), fn=(25.4, FLOOR), ff=(15.6, FLOOR), kpref=(1, -0.6))
REACH = dict(P=(24.6, 34.8), C=(32.0, 28.6), Hd=(37.6, 27.4), hup=(0.88, -0.48), hipn=(25.6, 35.6),
             hipf=(23.6, 35.2), fn=(31.4, FLOOR), ff=(14.8, FLOOR), kpref=(1, -0.3))


def a_lunge():
    return [
        (150, PP(P=(20.6, 34.6), C=(23.6, 25.8), Hd=(28.4, 23.0), hup=(0.5, -0.86), hipn=(21.6, 35.4),
                 hipf=(19.6, 35.0), fn=(25.8, FLOOR), ff=(16.8, FLOOR), kpref=(1, -0.5),
                 hf=(28.4, 32.6), hb=(22.6, 33.0), eyes=2, fingers=0.4)),
        (140, PP(**CROUCH, hf=(25.6, 28.6), hb=(19.6, 32.6), eyes=3, fingers=0.9, glow=1.2, hem=1)),
        (260, PP(**dict(CROUCH, C=(22.2, 28.0), Hd=(27.0, 25.6)), hf=(25.2, 28.4), hb=(19.4, 32.8), eyes=3,
                 eyestar=True, fingers=1.0, glow=1.4, hem=2)),
        (70, PP(**REACH, hf=(43.6, 31.6), hb=(21.0, 30.0), eyes=3, fingers=1.0, wind=3, hem=0, glow=1.3,
                claw=[((30.0, 32.6), (46.0, 31.8))], attack_hand=True)),
        (80, PP(**dict(REACH, C=(32.2, 29.4), Hd=(37.8, 28.6)), hf=(44.6, 38.0), hb=(21.6, 31.0), eyes=3,
                fingers=0.7, wind=3, hem=1, glow=1.2, claw=[((42.0, 29.6), (46.4, 42.6))], attack_hand=True)),
        (150, PP(**dict(REACH, P=(24.0, 35.4), C=(30.6, 30.4), Hd=(36.0, 30.2)), hf=(40.4, 42.2), hb=(22.4, 33.0),
                 eyes=2, fingers=0.4, hem=2, splash=((43.0, FLOOR), 0.5))),
        (160, PP(P=(22.4, 34.0), C=(27.4, 25.4), Hd=(32.4, 22.8), hup=(0.55, -0.84), hipn=(23.4, 34.8),
                 hipf=(21.4, 34.4), fn=(28.0, FLOOR), ff=(17.6, FLOOR), hf=(35.0, 36.0), hb=(26.0, 36.0),
                 eyes=2, fingers=0.2, splash=((43.0, FLOOR), 0.9))),
        (170, PP(hf=(31.0, 33.2), eyes=2, hem=1)),
    ]


def a_rise():
    # sink = how far the whole body is pushed below the floor line (the part below is simply not drawn)
    return [
        (260, PP(hup=(0.2, -0.98), hf=(28.8, 10.4), hb=(24.0, 34.0), sink=32.0, eyes=1, fingers=1.0, glow=0.6)),
        (170, PP(**dict(CROUCH), hf=(37.0, FLOOR - 19.6), hb=(22.0, 29.5), sink=21.0, eyes=2, fingers=0.9,
                 glow=0.7)),
        (160, PP(**dict(CROUCH), hf=(36.0, FLOOR - 10.6), hb=(32.0, FLOOR - 10.6), sink=12.0, eyes=2,
                 fingers=0.8, fingersb=0.8, glow=0.8)),
        (150, PP(**dict(CROUCH), hf=(28.2, FLOOR - 4.4), hb=(25.6, FLOOR - 4.6), sink=5.4, eyes=3, fingers=0.6,
                 fingersb=0.6, glow=0.9, hem=1)),
        (150, PP(P=(20.8, 34.4), C=(24.0, 25.2), Hd=(28.8, 22.2), hup=(0.48, -0.88), hipn=(21.8, 35.2),
                 hipf=(19.8, 34.8), fn=(25.8, FLOOR), ff=(17.4, FLOOR), kpref=(1, -0.5), hf=(31.0, 36.4),
                 hb=(25.4, 38.0), sink=1.2, eyes=2, glow=1.0, hem=2)),
        (190, PP(eyes=2, hem=0)),
    ]


def a_hurt():
    return [(90, PP(P=(20.8, 33.0), C=(22.8, 23.4), Hd=(26.4, 19.0), hup=(-0.2, -0.98), hipn=(21.8, 33.8),
                    hipf=(19.8, 33.4), hf=(29.0, 31.6), hb=(22.0, 34.0), cen=(33.6, 36.2), eyes=3, eyestar=True,
                    fingers=1.0, fingersb=1.0, glow=1.6)),
            (150, PP(P=(21.2, 33.0), C=(24.2, 23.2), Hd=(28.6, 19.2), hup=(0.2, -0.98), hf=(30.2, 32.6),
                     hb=(24.6, 35.4), cen=(33.8, 37.6), eyes=2, fingers=0.5, hem=1))]


def a_death():
    KNEEL = dict(P=(21.4, 39.6), C=(25.4, 30.6), Hd=(30.4, 28.6), hup=(0.7, -0.7), hipn=(22.4, 40.2),
                 hipf=(20.4, 39.8), fn=(16.6, FLOOR), ff=(13.6, FLOOR), kpref=(1.0, 0.9))
    return [
        (100, PP(P=(20.6, 33.0), C=(22.4, 23.6), Hd=(25.6, 19.6), hup=(-0.35, -0.94), hipn=(21.6, 33.8),
                 hipf=(19.6, 33.4), hf=(28.4, 31.0), hb=(21.6, 33.0), cen=(32.8, 35.2), eyes=3, eyestar=True,
                 fingers=1.0, fingersb=1.0, glow=1.6)),
        (150, PP(P=(21.0, 37.0), C=(24.0, 27.6), Hd=(28.4, 24.6), hup=(0.3, -0.95), hipn=(22.0, 37.6),
                 hipf=(20.0, 37.2), fn=(24.0, FLOOR), ff=(15.8, FLOOR), kpref=(1, 0.3), hf=(30.0, 38.0),
                 hb=(25.0, 40.0), cfloor=((33.4, 40.8), (0.25, 0.97)), eyes=2, glow=1.1, fingers=0.6)),
        (180, PP(**KNEEL, hf=(31.4, 44.6), hb=(27.0, 45.0), cfloor=((35.4, 40.6), (0.3, 0.95)), eyes=1, glow=0.9,
                 fingers=0.8, hem=1)),
        (150, PP(**KNEEL, hf=(32.6, 43.8), hb=(28.2, 44.4), rot=38.0, piv=(20.0, 47.0),
                 cfloor=((37.4, 40.8), (0.3, 0.95)), eyes=0, glow=0.7, hem=2)),
        (200, PP(heap=0.0, glow=0.45, eyes=0)),
        (900, PP(heap=1.0, glow=0.0, eyes=0, drip=False)),
    ]


def build(build_ase):
    K.setup(48, 48)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_pilgrim,
                                  [("idle", a_idle), ("walk", a_walk), ("swing", a_swing), ("lunge", a_lunge),
                                   ("rise", a_rise), ("hurt", a_hurt), ("death", a_death)],
                                  sway_key="C", loops=("idle", "walk"))
    hb = S.hurtbox(anims, ["Robe", "Head"], inset=(1, 1, 1, 0), tag=0)
    for k in (5, 6):          # the part of the arc in front of the body, from chest height down to the floor
        infos["swing"][k]["hit"] = {q for q in infos["swing"][k]["hit"] if q[1] >= 20}
    swing = S.hit_rect(infos, "swing", [5, 6], x_min=30)
    lunge = S.hit_rect(infos, "lunge", [3, 4], x_min=29)
    meta = {"native": 1, "frame": [48, 48], "anchor": [24, 48],
            "hurtbox": hb,
            "attacks": {"swing": {"active": [5, 6], "hit": swing},
                        "lunge": {"active": [3, 4], "hit": lunge}},
            "telegraph": {"swing": {"frame": 4, "at": S.spawn_pt(infos["swing"][4]["censer"])},
                          "lunge": {"frame": 2, "at": S.spawn_pt(infos["lunge"][2]["eye"])}},
            "light": {"censer_idle": S.spawn_pt(infos["idle"][0]["censer"]), "color": "#2fbfb0"},
            "notes": "faces right, feet on the bottom row. walk: feet planted 3 frames moving back 3px/frame at "
                     "170ms -> engine walk speed ~17.6 px/s keeps feet from sliding. swing: 0-3 wind the censer "
                     "back and up behind the head (chain lets out), 4 = held windup with a teal glint on the censer "
                     "(telegraph), 5-6 ACTIVE: the censer whips over and down in front (mid -> low, reaching ~22px "
                     "ahead), 7 it slaps the wet floor (teal splash), 8-9 recover. lunge: 0-2 crouch (2 = eye flare "
                     "telegraph), 3-4 ACTIVE claw rake (drawn in place, engine moves him forward on 3-4), 5 claws "
                     "hit the floor, 6-7 recover. rise: ambush out of black water; frame 0 only the hand + hood tip "
                     "are above the floor line, standing by 5 (= idle 0). death ends as a heap of wet robe with the "
                     "censer guttering out beside it (hold last frame). The censer is a small teal light source "
                     "(optional point light at `light.censer_idle`)."}
    S.export("db_pilgrim", LAYERS, anims, meta, build_ase)
    return meta
