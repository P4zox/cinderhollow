#!/usr/bin/env python3
"""The Enforcer Mech (agent NH) -- NEO-HALLOW's riot-control walker, mini-boss of the Enforcer's Plaza.

    python3 art/gen_neo_enforcer.py [--preview]

enforcer / enforcer_p2   128x96, faces right, feet on the bottom row, ~84 px tall.
A tall, narrow-waisted walker on reverse-jointed legs: a gunmetal carapace with chrome armour, a low sensor head with
a magenta visor slit, a tower RIOT SHIELD on the near arm (chrome rim, cyan light strip, stencilled glyphs), a shock
baton in the far hand, a MISSILE POD on the far shoulder.  Phase 2: the shield is gone, the visor runs red, vents smoke.
Tags: idle(6) walk(8) bash(10, active 4-7) sweep(10, active 5-6) stomp(11, active 6-7) missiles(12, spawn f6)
      guard(2) stagger(4) death(12)
"""
import math, sys
import neo_kit  # noqa: F401
from neo_kit import K, E3, Layer, FXLayer, lerp, ip, line, poly_mask, n_plate, n_dome, n_capsule, n_tube, mk, madd, disc_glow, halo_dots, spawn_pt, circuit
from enemy_kit import hash01, ik

BUILD = "--preview" not in sys.argv
E3.BUILD = BUILD
TAGS = dict(idle=6, walk=8, bash=10, sweep=10, stomp=11, missiles=12, guard=2, stagger=4, death=12)
E3.SPEC_FRAMES["enforcer"] = dict(TAGS)
E3.SPEC_FRAMES["enforcer_p2"] = dict(TAGS)
LAYERS = ["Pod", "FarArm", "FarLeg", "Body", "NearLeg", "NearArm", "Head", "Shield", "FX"]
FL = 95.0
NEU = dict(C=(54.0, 30.0), P=(52.0, 52.0), Hd=(66.0, 32.0), nf=(62.0, FL), ff=(42.0, FL), lift_n=0.0, lift_f=0.0,
           sh=(78.0, 52.0), sa=0.0, bh=(40.0, 56.0), ba=70.0, pod=0.0, flash=0, visor=1.0, shield=True, smear=None,
           dead=0.0, spark=0, smoke=0, red=False, fi=0, dust=0)
EP = mk(NEU)


def off(q, dx, dy):
    return (q[0] + dx, q[1] + dy)


def draw(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX"); Ls["FX"] = FX
    info = {"hit": set()}
    C_, P_, Hd = p["C"], p["P"], p["Hd"]
    up = (C_[0] - P_[0], C_[1] - P_[1]); ul = math.hypot(*up) or 1
    un = (up[0] / ul, up[1] / ul); nr = (-un[1], un[0])   # nr points toward the front-ish (right when upright)
    nr = (-nr[0], -nr[1]) if nr[0] < 0 else nr
    vis = "R" if p["red"] else "T"
    # ---------------- missile pod (far shoulder, behind)
    Pd = Ls["Pod"]
    pc = madd(C_, (un, 10.0), (nr, -7.0))
    lid = p["pod"]
    pod = [madd(pc, (nr, -12), (un, -5)), madd(pc, (nr, 8), (un, -6)), madd(pc, (nr, 11), (un, 3 + lid * 2)), madd(pc, (nr, -10), (un, 6))]
    Pd.paint(n_plate(poly_mask(pod), 1.8, (-0.3, -0.4), 1.2), "U", 0)
    cover = [madd(pc, (nr, -11), (un, 5 + lid * 5)), madd(pc, (nr, 9), (un, 4 + lid * 7)), madd(pc, (nr, 11), (un, 8 + lid * 7)), madd(pc, (nr, -10), (un, 9 + lid * 5))]
    Pd.paint(n_plate(poly_mask(cover), 1.0, (-0.3, -0.6), 1.2), "S", 0, ao=0)
    info["pod"] = madd(pc, (un, 8 + lid * 6))
    if lid > 0.4:
        for k in range(4):
            q = ip(madd(pc, (nr, -7 + k * 4.5), (un, 5.5)))
            Pd.fixed({q: "R2", (q[0], q[1] - 1): "S4"})
    if p["flash"]:
        disc_glow(FX, info["pod"], 3.0 + p["flash"], ["T4", "T3", "T2", "T1"])
    # ---------------- far arm + shock baton
    shF = madd(C_, (un, 2.0), (nr, -4.0))
    el = ik(shF, p["bh"], 13.0, 12.0, (-0.3, 1))
    A = Ls["FarArm"]
    A.paint(n_tube([shF, el, p["bh"]], [3.4, 2.8, 2.6]), "U", -1)
    A.paint(n_capsule(el, lerp(el, p["bh"], 0.8), 3.0, 2.8), "S", -1, ao=0)
    ba = math.radians(p["ba"]); bd = (math.cos(ba), math.sin(ba))
    b0 = madd(p["bh"], (bd, -4)); b1 = madd(p["bh"], (bd, 26))
    A.paint(n_capsule(b0, b1, 1.3, 1.1), "U", 0, ao=0)
    for k in range(6):
        q = ip(madd(p["bh"], (bd, 14 + k * 2.2)))
        A.fixed({q: "X2" if k % 2 else "X3"})
    FX.put([ip(b1), ip(madd(b1, (bd, 1)))], "X4")
    info["baton"] = b1
    # ---------------- legs: reverse-jointed, chrome shin plates
    for name, foot, lift, b in (("FarLeg", p["ff"], p["lift_f"], -1), ("NearLeg", p["nf"], p["lift_n"], 0)):
        L = Ls[name]
        hip = madd(P_, (nr, 3.0 if name == "NearLeg" else -3.0))
        f = (foot[0], foot[1] - lift)
        hock = (f[0] - 7.0, f[1] - 13.0)
        kn = ik(hip, hock, 17.0, 16.0, (1, 0.2))
        L.paint(n_tube([hip, kn], [5.0, 4.0]), "U", b)
        L.paint(n_tube([kn, hock], [3.4, 2.6]), "U", b)
        L.paint(n_plate(poly_mask([off(kn, 0, -3), off(kn, 4, 0), off(hock, 2.5, 0), off(hock, -2, 0)]), 1.2, (-0.3, -0.3)), "S", b, ao=0)
        L.paint(n_dome(kn, 3.6, 3.4), "S", b, ao=0)
        L.paint(n_capsule(hock, (f[0], f[1] - 2.0), 2.4, 2.0), "U", b)
        toe = poly_mask([(f[0] - 6, f[1] + 1), (f[0] - 5, f[1] - 3), (f[0] + 3, f[1] - 3.5), (f[0] + 9, f[1] - 0.5), (f[0] + 9, f[1] + 1)])
        L.paint(n_plate(toe, 1.2, (-0.1, -0.5)), "S", b)
        L.decal([(int(f[0] + 8), int(f[1] - 1))], "X2")
    # ---------------- body: waist spine, carapace, chest light bar, sensor head
    B = Ls["Body"]
    B.paint(n_tube([P_, lerp(P_, C_, 0.5)], [5.0, 4.0]), "U", 0)
    for k in range(3):
        B.paint(n_capsule(madd(lerp(P_, C_, 0.1 + k * 0.14), (nr, -4)), madd(lerp(P_, C_, 0.1 + k * 0.14), (nr, 4)), 1.4), "S", -1, ao=0)
    cara = [madd(C_, (nr, -12), (un, 8)), madd(C_, (nr, 0), (un, 12)), madd(C_, (nr, 11), (un, 7)), madd(C_, (nr, 14), (un, -4)),
            madd(C_, (nr, 8), (un, -12)), madd(C_, (nr, -6), (un, -13)), madd(C_, (nr, -13), (un, -4))]
    B.paint(n_plate(poly_mask(cara), 3.0, (-0.25, -0.2), 1.1), "U", 0)
    plate = [madd(C_, (nr, -8), (un, 9)), madd(C_, (nr, 2), (un, 11.5)), madd(C_, (nr, 10), (un, 6)), madd(C_, (nr, 7), (un, 0)), madd(C_, (nr, -6), (un, 2))]
    B.paint(n_plate(poly_mask(plate), 2.0, (-0.3, -0.5), 1.2), "S", 0, ao=0)
    bar = [ip(madd(C_, (nr, x), (un, -3))) for x in range(-4, 10, 2)]
    B.fixed({q: ("X3" if i % 2 else "X2") for i, q in enumerate(bar)})
    circuit(B, [madd(C_, (nr, -10), (un, -8)), madd(C_, (nr, 0), (un, -9)), madd(C_, (nr, 6), (un, -11))], "X1")
    # sensor head: a narrow helm on a short neck, jutting forward above the near shoulder
    Hd = madd(C_, (un, 11.0), (nr, 8.0))
    B.paint(n_capsule(madd(C_, (un, 8.0), (nr, 2.0)), Hd, 2.6, 2.2), "U", -1)
    head = [off(Hd, -6, -4), off(Hd, 2, -6), off(Hd, 9, -3), off(Hd, 10, 1), off(Hd, 6, 4), off(Hd, -5, 4)]
    Ls["Head"].paint(n_plate(poly_mask(head), 1.4, (-0.2, -0.5), 1.3), "S", 0, ao=0)
    Ls["Head"].paint(n_plate(poly_mask([off(Hd, -6, 1), off(Hd, 8, 1), off(Hd, 6, 4), off(Hd, -5, 4)]), 1.0, (0, 0.3)), "U", 0, ao=0)
    vx = [ip(off(Hd, x, 0.0)) for x in range(0, 8)]
    Ls["Head"].fixed({q: vis + ("3" if i % 3 else "2") for i, q in enumerate(vx)})
    if p["visor"] > 0.5: FX.put(vx[2:7:2], vis + ("3" if vis == "R" else "4"))
    info["visor"] = off(Hd, 5, 0)
    if p["red"]:   # overheated vents on the carapace
        for k in range(3):
            q = ip(madd(C_, (nr, -10 + k * 3), (un, 3)))
            B.fixed({q: "R2", (q[0], q[1] + 1): "R1"})
    # ---------------- near arm + riot shield
    shN = madd(C_, (un, 1.0), (nr, 4.0))
    eln = ik(shN, p["sh"], 13.0, 12.0, (-0.2, 1))
    NA = Ls["NearArm"]
    NA.paint(n_tube([shN, eln, p["sh"]], [3.8, 3.0, 2.8]), "U", 0)
    NA.paint(n_dome(shN, 5.2, 4.4), "S", 0, ao=0)
    NA.paint(n_capsule(eln, lerp(eln, p["sh"], 0.8), 3.3, 3.0), "S", 0, ao=0)
    if p["shield"]:
        S_ = Ls["Shield"]
        a = math.radians(p["sa"]); d = (math.sin(a), -math.cos(a)); nn = (math.cos(a), math.sin(a))
        c = madd(p["sh"], (nn, 4.0))
        shp = [madd(c, (d, 26), (nn, -6)), madd(c, (d, 27), (nn, 5)), madd(c, (d, 22), (nn, 8)), madd(c, (d, -20), (nn, 8)),
               madd(c, (d, -24), (nn, 4)), madd(c, (d, -24), (nn, -6)), madd(c, (d, -20), (nn, -8)), madd(c, (d, 22), (nn, -8))]
        m_ = poly_mask(shp)
        S_.paint(n_plate(m_, 2.2, (-0.15, -0.1), 1.0), "U", 0)
        edge = {q for q in m_ if any((q[0] + a2, q[1] + b2) not in m_ for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        S_.decal(list(edge), "S4")
        S_.decal([q for q in edge if q[0] < c[0] - 2 or q[1] < c[1] - 10], "S5")
        # vision slot + light strip + stencil glyphs
        for k in range(-6, 7):
            q = ip(madd(c, (d, 15), (nn, k * 0.8)))
            if q in S_.px: S_.decal([q], "X1" if k % 3 else "X2")
        for k in range(-18, 12, 1):
            q = ip(madd(c, (d, k), (nn, 5.5)))
            if q in S_.px: S_.decal([q], "X3" if (k + fi) % 5 else "X4")
        for g_ in range(3):
            gy = -6 - g_ * 7
            for k in range(-3, 4):
                if (hash01(g_, k, 5) > 0.45):
                    q = ip(madd(c, (d, gy + (k % 2) * 2), (nn, k * 1.1)))
                    if q in S_.px: S_.decal([q], "T2")
        info["shield"] = m_
        info["hit"] |= set(m_)
    else:
        # phase 2: a torn stump of the shield mount, sparking
        NA.paint(n_capsule(p["sh"], off(p["sh"], 6, 0), 2.4, 1.6), "S", 0, ao=0)
        if fi % 2 == 0: FX.put([ip(off(p["sh"], 7, 1)), ip(off(p["sh"], 8, -1))], "X4")
    # ---------------- smears, dust, sparks, smoke, death
    if p["smear"]:
        g0, a0, g1, a1 = p["smear"]
        info["hit"] |= K.swept(FX, g0, a0, g1, a1, 12.0, 30.0, hw=1.0, pal="cyan", start=0.1)
    if p["dust"]:
        for k in range(10):
            FX.put([(int(p["nf"][0] - 20 + k * 6 + hash01(k, fi, 1) * 3), int(FL - hash01(fi, k, 2) * 5))], "S3" if k % 2 else "S2")
    if p["spark"]:
        for k in range(8):
            FX.put([(int(C_[0] + (hash01(k, fi, 3) - 0.5) * 30), int(C_[1] + (hash01(fi, k, 4) - 0.5) * 36))], ["X4", "T3", "S6", "X3"][k % 4])
    if p["smoke"]:
        for k in range(6):
            t = (k / 6 + fi * 0.13) % 1
            FX.put([(int(C_[0] - 8 - t * 6 + math.sin(k + t * 5) * 2), int(C_[1] - 12 - t * 16))], "S2" if t < 0.5 else "S1")
    if p["dead"]:
        for L in Ls.values():
            if isinstance(L, Layer):
                for q in list(L.px):
                    if hash01(q[0], q[1], 7) < p["dead"] * 0.45: L.erase([q])
    return Ls, info


def poses(shield=True):
    red = not shield
    B = dict(shield=shield, red=red, smoke=1 if red else 0)

    def pp(ms, **kw):
        d = dict(B); d.update(kw); return (ms, EP(**d))
    idle = [pp(170, C=(54.0, 30.0 + b), P=(52.0, 52.0 + b * 0.6), Hd=(66.0, 32.0 + b), sh=(78.0, 52.0 + b), bh=(40.0, 56.0 + b)) for b in (0, 0.5, 1, 1.5, 1, 0.5)]
    walk = []
    for k in range(8):
        t = k / 8 * 2 * math.pi
        nf = (52.0 + math.sin(t) * 10, FL); ff = (48.0 - math.sin(t) * 10, FL)
        ln, lf = max(0, math.cos(t)) * 4, max(0, -math.cos(t)) * 4
        b = abs(math.sin(t)) * 1.5
        walk.append(pp(120, nf=(nf[0] + 8, FL), ff=(ff[0] - 4, FL), lift_n=ln, lift_f=lf, C=(55.0, 30.0 + b), P=(53.0, 52.0 + b), Hd=(67.0, 32.0 + b), sh=(79.0, 52.0 + b), bh=(41.0 + math.sin(t) * 2, 56.0 + b)))
    # bash: brace behind the shield, then drive forward (shield in p1, shoulder in p2)
    bash = [pp(130, C=(52.0, 32.0), P=(51.0, 54.0), Hd=(63.0, 34.0), sh=(74.0, 52.0), sa=-4),
            pp(130, C=(50.0, 34.0), P=(50.0, 55.0), Hd=(61.0, 36.0), sh=(72.0, 54.0), sa=-8, nf=(60.0, FL), ff=(38.0, FL)),
            pp(130, C=(49.0, 35.0), P=(49.0, 56.0), Hd=(60.0, 37.0), sh=(71.0, 55.0), sa=-10, nf=(60.0, FL), ff=(36.0, FL)),
            pp(200, C=(49.0, 35.0), P=(49.0, 56.0), Hd=(60.0, 37.0), sh=(71.0, 55.0), sa=-10, nf=(60.0, FL), ff=(36.0, FL), visor=1),
            pp(70, C=(60.0, 32.0), P=(55.0, 54.0), Hd=(71.0, 35.0), sh=(86.0, 52.0), sa=6, nf=(70.0, FL), ff=(40.0, FL), dust=1),
            pp(70, C=(62.0, 32.0), P=(56.0, 54.0), Hd=(73.0, 35.0), sh=(88.0, 52.0), sa=8, nf=(72.0, FL), ff=(42.0, FL), dust=1),
            pp(80, C=(62.0, 32.0), P=(56.0, 54.0), Hd=(73.0, 35.0), sh=(88.0, 53.0), sa=8, nf=(72.0, FL), ff=(46.0, FL), dust=1),
            pp(90, C=(60.0, 31.0), P=(55.0, 53.0), Hd=(71.0, 34.0), sh=(85.0, 53.0), sa=4, nf=(70.0, FL), ff=(50.0, FL)),
            pp(140, C=(57.0, 30.0), P=(54.0, 52.0), Hd=(69.0, 32.0), sh=(81.0, 52.0), sa=1, nf=(66.0, FL), ff=(46.0, FL)),
            pp(140)]
    # sweep: baton raised behind, arcs over and down in front
    sweep = [pp(120, bh=(38.0, 44.0), ba=-120), pp(120, bh=(36.0, 32.0), ba=-150, C=(52.0, 31.0), Hd=(64.0, 33.0)),
             pp(130, bh=(38.0, 26.0), ba=-160, C=(51.0, 31.0), Hd=(63.0, 33.0)), pp(190, bh=(38.0, 25.0), ba=-165, C=(51.0, 31.0), Hd=(63.0, 33.0)),
             pp(60, bh=(56.0, 26.0), ba=-60, C=(55.0, 31.0), Hd=(67.0, 33.0), sh=(72.0, 58.0), smear=((40.0, 26.0), -160, (56.0, 26.0), -60)),
             pp(60, bh=(66.0, 40.0), ba=10, C=(58.0, 32.0), Hd=(70.0, 34.0), sh=(72.0, 60.0), nf=(68.0, FL), smear=((52.0, 26.0), -80, (66.0, 40.0), 10)),
             pp(70, bh=(66.0, 50.0), ba=45, C=(58.0, 32.0), Hd=(70.0, 34.0), sh=(72.0, 60.0), nf=(68.0, FL), smear=((64.0, 36.0), 0, (66.0, 50.0), 45)),
             pp(120, bh=(62.0, 56.0), ba=70, C=(57.0, 31.0), Hd=(69.0, 33.0), sh=(74.0, 58.0), nf=(66.0, FL)),
             pp(130, bh=(50.0, 58.0), ba=75, nf=(64.0, FL)), pp(130)]
    # stomp: rear up, near foot high, crash down
    stomp = [pp(120, C=(53.0, 28.0), P=(51.0, 50.0), Hd=(65.0, 30.0)), pp(120, C=(52.0, 27.0), P=(50.0, 48.0), Hd=(64.0, 27.0), lift_n=6, nf=(66.0, FL)),
             pp(120, C=(51.0, 25.0), P=(49.0, 46.0), Hd=(63.0, 24.0), lift_n=14, nf=(68.0, FL), sh=(76.0, 44.0)),
             pp(120, C=(50.0, 24.0), P=(48.0, 44.0), Hd=(62.0, 22.0), lift_n=20, nf=(70.0, FL), sh=(76.0, 42.0)),
             pp(220, C=(50.0, 24.0), P=(48.0, 44.0), Hd=(62.0, 22.0), lift_n=21, nf=(70.0, FL), sh=(76.0, 41.0), visor=1),
             pp(60, C=(54.0, 29.0), P=(52.0, 51.0), Hd=(66.0, 31.0), lift_n=6, nf=(72.0, FL), sh=(78.0, 50.0)),
             pp(70, C=(56.0, 34.0), P=(54.0, 56.0), Hd=(68.0, 37.0), nf=(72.0, FL), sh=(80.0, 56.0), dust=1),
             pp(80, C=(56.0, 35.0), P=(54.0, 57.0), Hd=(68.0, 38.0), nf=(72.0, FL), sh=(80.0, 57.0), dust=1),
             pp(130, C=(55.0, 33.0), P=(53.0, 55.0), Hd=(67.0, 35.0), nf=(70.0, FL), sh=(79.0, 55.0)),
             pp(130, C=(54.0, 31.0), P=(52.0, 53.0), Hd=(66.0, 33.0), nf=(66.0, FL)), pp(130)]
    # missiles: brace, pod lid opens, two salvos
    mis = [pp(120, pod=0.2), pp(120, pod=0.5, C=(53.0, 31.0)), pp(120, pod=0.8, C=(52.0, 32.0), Hd=(64.0, 34.0)), pp(130, pod=1.0, C=(52.0, 32.0), Hd=(64.0, 34.0)),
           pp(130, pod=1.0, C=(52.0, 32.0), Hd=(64.0, 34.0), visor=1), pp(120, pod=1.0, C=(52.0, 32.0), Hd=(64.0, 34.0)),
           pp(90, pod=1.0, flash=2, C=(50.0, 33.0), Hd=(62.0, 35.0), P=(51.0, 53.0)), pp(100, pod=1.0, flash=1, C=(51.0, 32.0), Hd=(63.0, 34.0)),
           pp(90, pod=1.0, flash=2, C=(50.0, 33.0), Hd=(62.0, 35.0), P=(51.0, 53.0)), pp(120, pod=0.8, C=(52.0, 31.0), Hd=(64.0, 33.0)),
           pp(130, pod=0.4), pp(130, pod=0.0)]
    guard = [pp(200, C=(51.0, 33.0), P=(50.0, 55.0), Hd=(61.0, 36.0), sh=(72.0, 50.0), sa=-2, nf=(60.0, FL), ff=(38.0, FL)),
             pp(200, C=(51.0, 33.5), P=(50.0, 55.5), Hd=(61.0, 36.5), sh=(72.0, 50.5), sa=-2, nf=(60.0, FL), ff=(38.0, FL))]
    stag = [pp(100, C=(48.0, 36.0), P=(49.0, 56.0), Hd=(58.0, 42.0), sh=(68.0, 64.0), sa=20, bh=(34.0, 64.0), ba=100, spark=1, visor=0),
            pp(120, C=(47.0, 38.0), P=(48.0, 58.0), Hd=(57.0, 45.0), sh=(66.0, 68.0), sa=26, bh=(33.0, 66.0), ba=105, spark=1, visor=0),
            pp(200, C=(47.0, 39.0), P=(48.0, 58.0), Hd=(57.0, 46.0), sh=(66.0, 69.0), sa=28, bh=(33.0, 67.0), ba=105, visor=0),
            pp(200, C=(48.0, 37.0), P=(48.5, 57.0), Hd=(58.0, 44.0), sh=(67.0, 66.0), sa=22, bh=(34.0, 65.0), ba=100, visor=1)]
    death = []
    for k in range(12):
        t = min(1, k / 8)
        death.append(pp(110 if k < 11 else 500, C=(52.0 - t * 12, 30.0 + t * 40), P=(51.0 - t * 4, 52.0 + t * 28), Hd=(62.0 - t * 4, 34.0 + t * 44),
                        sh=(74.0, 54.0 + t * 30), sa=10 + t * 60, bh=(38.0 - t * 6, 58.0 + t * 26), ba=90 + t * 60, nf=(60.0 + t * 6, FL), ff=(42.0 - t * 4, FL),
                        spark=1 if k % 2 == 0 and k < 10 else 0, visor=1 if k < 3 else 0, dead=max(0, (k - 8) / 5), smoke=1))
    return [("idle", lambda: idle), ("walk", lambda: walk), ("bash", lambda: bash), ("sweep", lambda: sweep), ("stomp", lambda: stomp),
            ("missiles", lambda: mis), ("guard", lambda: guard), ("stagger", lambda: stag), ("death", lambda: death)]


def fix_floor(anims):
    """Nothing may hang below the floor row (sinking) -- the feet are planted on row FL by construction."""
    return anims


def build():
    K.setup(128, 96)
    anims, infos = E3.render_anims("enforcer", LAYERS, draw, poses(True), sway_key="C", loops=("idle", "walk"))
    bash = E3.hit_rect(infos, "bash", (4, 5, 6, 7), floor=True, x_min=60)
    sweep = E3.hit_rect(infos, "sweep", (5, 6), floor=True, x_min=46)
    st = [64, 70, 44, 26]
    meta = {"native": 1, "anchor": [54, 96], "hurtbox": [36, 18, 40, 78],
            "attacks": {"bash": {"active": [4, 7], "hit": bash}, "sweep": {"active": [5, 6], "hit": sweep}, "stomp": {"active": [6, 7], "hit": st}},
            "spawn": {"missiles": {"frame": 6, "at": spawn_pt(infos["missiles"][6]["pod"])}},
            "telegraph": {"bash": {"frame": 3, "at": spawn_pt(infos["bash"][3]["visor"])}, "sweep": {"frame": 3, "at": spawn_pt(infos["sweep"][3]["baton"])},
                          "stomp": {"frame": 4, "at": spawn_pt(infos["stomp"][4]["visor"])}, "missiles": {"frame": 4, "at": spawn_pt(infos["missiles"][4]["pod"])}},
            "visor": spawn_pt(infos["idle"][0]["visor"])}
    E3.export("enforcer", LAYERS, anims, meta)
    anims2, _ = E3.render_anims("enforcer_p2", LAYERS, draw, poses(False), sway_key="C", loops=("idle", "walk"))
    E3.export("enforcer_p2", LAYERS, anims2, None)


if __name__ == "__main__":
    build()
