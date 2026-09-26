#!/usr/bin/env python3
"""THE THORN COVEN (agent T): three gaunt forest witches in bark-and-bramble robes with thorn staffs.

    python3 art/gen_thornveil_coven.py [--preview]

Outputs: coven / coven_b / coven_c  (72x72, faces RIGHT, hem on the bottom row, anchor [36,72]) + coven_meta.json
(shared by all three), previews art/previews/coven*.png, coven_hitbox.png, coven_contact.png.
  coven    The Briar Mother  -- bark hood, a gaunt ash-pale face, a crown of thorns
  coven_b  The Moss Maiden   -- a veil of hanging moss hiding the face, small antler crown
  coven_c  The Ribbon Crone  -- a fawn-skull mask hung with pale ribbons
Tags: idle(6) walk(8) strike(9) cast(10) summon(10) blink(10) chant(6) hurt(2) stagger(4) death(8)
"""
import math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import thornveil_ckit as C  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome, n_capsule, dirv  # noqa: E402
from thornveil_ckit import mk, rot, madd, curve, chain, taper, deer_skull, antler, ribbon_px, moss_drape, glow_dots, render_anims, hit_rect, hurtbox, collapse, export, spawn_pt, contact  # noqa: E402
from PIL import Image  # noqa: E402

W_, H_ = 72, 72
FL = 71
LAYERS = ["StaffBack", "BackArm", "Robe", "Vines", "Head", "FrontArm", "Staff", "Mound", "FX"]
NEU = dict(ch=(35.0, 33.0), hd=(38.5, 24.0), ha=10.0, fh=(45.0, 43.0), sa=-84.0, bh=(29.0, 46.0), flare=0.0, sink=0.0, glow=1,
           smear=None, wind=0.0, bob=0.0, lean=0.0, spark=0, burst=0, mound=0.0, eye=1, dead=False)
PP = mk(NEU)
ROBE = {0: "X", 1: "E", 2: "X"}


def staff_geom(p):
    g = p["fh"]
    d = dirv(p["sa"])
    head = madd(g, (d, 27.0))
    butt = madd(g, (d, -25.0))
    return g, d, head, butt


def draw_witch(p, fi, sw, v):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    dy = p["sink"] * 64.0
    D = lambda q: (q[0], q[1] + dy)
    ch, hd = D(p["ch"]), D(p["hd"])
    s = sw * 0.7 + p["wind"]
    rmat = ROBE[v]
    # ---- robe: a long bark-cloth gown flaring to a ragged hem that pools on the ground
    Rb = Ls["Robe"]
    hem = FL + dy
    fl = p["flare"]
    left, right = ch[0] - 12.5 - fl * 2 + s * 0.8, ch[0] + 10.5 + fl * 2 + s * 0.3
    poly = [madd(ch, ((-1, 0), 4.2), ((0, -1), 2.5)), madd(ch, ((1, 0), 4.2), ((0, -1), 1.5)), (ch[0] + 6.0, ch[1] + 12)]
    n = 9
    for i in range(n + 1):
        t = i / n
        x = right + (left - right) * t
        y = hem - (1.8 if i % 2 else 0.0) - 1.2 * math.sin(fi * 0.9 + i)
        poly.append((x, y))
    poly += [(ch[0] - 8.5 + s * 0.4, ch[1] + 12)]
    rm = {q for q in poly_mask(poly) if q[1] <= FL}
    Rb.paint(n_plate(rm, 2.6, (-0.1, -0.05), 1.1, fold=lambda x, y: (0.45 * math.sin((x - ch[0]) * 0.9 + y * 0.08), 0)), rmat, 0)
    # hem darkening + moss clots
    for q in rm:
        if q[1] > hem - 5 and hash01(q[0], q[1], 3 + v) < 0.35:
            Rb.decal([q], ("H", 2 if q[1] > hem - 2 else 3))
    info["hit"] |= rm
    # ---- bramble vines wound around the gown, thorn barbs
    Vn = Ls["Vines"]
    vpx = {}
    for k in range(3):
        y0 = ch[1] + 5 + k * 11 + (v - 1) * 2
        pts = []
        for i in range(24):
            t = i / 23
            x = left + 2 + (right - left - 4) * t
            y = y0 + (5 - 3 * k) * t + 2.4 * math.sin(t * (5 + k) + k * 2 + v + fi * 0.2)
            pts.append((x, y))
        for i, q in enumerate(dict.fromkeys(polyline(pts))):
            if q in rm:
                if hash01(i, k, 4 + v) < 0.18:
                    continue
                vpx[q] = "U2" if i % 3 else "U1"
                if i % 9 == 4:
                    vpx[(q[0], q[1] - 1)] = "U4"
    Vn.fixed(vpx)
    # ---- back arm (thin, pale) and the far side of the staff when it passes behind
    g, d, head, butt = staff_geom(p)
    g, head, butt = D(g), D(head), D(butt)
    sh = madd(ch, ((0, -1), 1.0))
    for L, hand, bias, pref in ((Ls["BackArm"], D(p["bh"]), -2, (-1, 0.5)), (Ls["FrontArm"], g, 0, (-1, 0.6))):
        s0 = madd(sh, ((-1, 0), 1.5 if bias else -0.5))
        el = ik(s0, hand, 10.5, 10.0, pref)
        cuff = lerp(el, hand, 0.62)
        chain(L, [s0, el, cuff], [2.0, 1.5, 1.7], rmat, bias)   # long bell sleeve
        chain(L, [cuff, hand], [0.95, 0.85], "Z", bias - 1)     # gaunt wrist
        L.paint(n_dome(hand, 1.4, 1.3), "Z", bias, ao=0)
        # long fingers
        for k in (-1, 0, 1):
            L.fixed({ip(madd(hand, (dirv(p["sa"] + 90 + k * 20), 2.2))): "Z2" if bias else "Z3"})
    # ---- staff: gnarled wood wrapped in a thorned vine, glowing knot at the head
    St = Ls["Staff"]
    cp = curve([butt, madd(lerp(butt, head, 0.35), ((-d[1], d[0]), 0.8)), madd(lerp(butt, head, 0.7), ((d[1], -d[0]), 0.8)), head], 5)
    chain(St, cp, taper(len(cp), 1.0, 1.35), "E", 0, ao=0)
    for i, q in enumerate(cp):
        if i % 3 == 1:
            o = madd(q, ((-d[1], d[0]), 1.6 * (1 if (i // 3) % 2 else -1)))
            St.fixed({ip(o): "U4", ip(madd(o, ((-d[1], d[0]), 0.9 * (1 if (i // 3) % 2 else -1)))): "U5"})
    # gnarled crook at the head: two curling prongs cradling the spirit-knot
    for side in (-1, 1):
        pr = [head, madd(head, (d, 3.0), ((-d[1] * side, d[0] * side), 2.6)), madd(head, (d, 5.8), ((-d[1] * side, d[0] * side), 1.0))]
        chain(St, curve(pr, 2), [1.2, 1.0, 0.8, 0.7, 0.6], "E", 0, ao=0)
    knot = madd(head, (d, 3.2))
    gl = p["glow"]
    for q in (K.mask_disc(knot, 1.6 + 0.4 * gl) if gl >= 0 else []):
        FX.put([q], "S4" if math.hypot(q[0] + .5 - knot[0], q[1] + .5 - knot[1]) < 1.0 else "S3")
    if gl >= 2:
        glow_dots(FX, knot, 3.5 + gl, 6 + gl * 2, fi, cols=("S3", "S4", "S2"), seed=v)
    info["tip"] = knot
    info["butt"] = butt
    # ---- head (small, menacing)
    Hd = Ls["Head"]
    ha = p["ha"]
    G = lambda x, y: add(hd, rot((x, y), ha))
    # neck
    chain(Hd, [madd(ch, ((0, -1), 1.5)), G(-1.5, 2.5)], [1.8, 1.4], "Z", 0)
    if v == 2:   # the Ribbon Crone: a fawn-skull mask
        hk = deer_skull(Hd, G(0.0, -0.5), ha + 20, 0.62, eye=p["eye"] + (1 if gl >= 2 else 0))
        info["eye"] = hk["eye"]
        for k, a in enumerate((-2.0, 0.5)):
            for q, c in ribbon_px(G(a, -3.4), fi, k * 2.1, L=13 + k * 4, sway=-0.4 + s * 0.15).items():
                FX.put([q], c)
    else:
        face = [G(-1.8, -3.2), G(1.8, -3.0), G(3.4, -0.8), G(3.0, 2.4), G(1.2, 4.2), G(-1.6, 3.2)]
        Hd.paint(n_plate(poly_mask(face), 1.2, (-0.1, -0.2)), "Z", 0)
        e = ip(G(1.6, -0.3))
        Hd.fixed({e: "S4" if (p["eye"] >= 2 or gl >= 2) else "S3", (e[0] - 1, e[1]): "Z0", ip(G(1.9, 2.6)): "Z0", ip(G(1.2, 2.8)): "Z1"})
        info["eye"] = e
    # hood / headwear
    hood = [G(-4.2, -1.0), G(-3.6, -4.4), G(-0.8, -6.0), G(2.6, -5.2), G(4.2, -2.4), G(3.6, -1.8), G(1.6, -3.6), G(-1.8, -2.6),
            G(-2.4, 3.2), G(-4.8, 5.8), G(-6.0, 3.0)]
    Hd.paint(n_plate(poly_mask(hood), 1.6, (-0.2, -0.2), 1.2), rmat, 0)
    if v == 0:   # crown of thorns
        for k in range(5):
            b = G(-3.0 + k * 1.4, -5.2 + abs(k - 2) * 0.4)
            tp = madd(b, (dirv(-100 + (k - 2) * 16 + ha), 3.2 + (k % 2)))
            Hd.fixed({q: "U4" if j < 2 else "U5" for j, q in enumerate(line(b, tp))})
    if v == 1:   # moss veil over the face + small antler crown
        moss_drape(Hd, [G(x, -2.2) for x in (-0.5, 0.8, 2.0, 3.0)], fi, 11, n=4, maxlen=6)
        antler(Hd, G(-1.0, -5.4), -110 + ha, 0.38, "J", 0, tines=1, spread=0.7, w=0.7)
        antler(Hd, G(1.0, -5.4), -70 + ha, 0.38, "J", 0, tines=1, spread=0.7, w=0.7)
    for L in (Rb, Hd, Ls["FrontArm"]):
        C.rim(L, {rmat, "Z"}, 4)
    # ---- smears / sparks
    if p["smear"]:
        g0, a0 = p["smear"]
        hot = K.swept(FX, D(g0), a0, g, p["sa"], 14.0, 28.0, hw=1.0, pal="spirit", start=0.25)
        info["hit"] |= hot
    if p["spark"]:
        glow_dots(FX, knot, 5 + p["spark"] * 2, 10, fi, cols=("S4", "S5", "S3"), seed=3)
    if p["burst"]:   # summon: roots/light bursting from the staff's butt at the ground
        b = (butt[0], min(FL, butt[1]))
        for k in range(12):
            a = -math.pi * (0.05 + 0.9 * hash01(k, p["burst"], 5))
            r = 2 + p["burst"] * 2.5 * hash01(k, 3, 7)
            FX.put([ip((b[0] + math.cos(a) * r * 1.5, b[1] + math.sin(a) * r))], "S3" if k % 2 else "U4")
    # ---- blink: a bramble mound she sinks into / rises from
    if p["mound"] > 0:
        Mn = Ls["Mound"]
        mw = 12 * p["mound"]
        for k in range(16):
            t = k / 15
            x0 = ch[0] - mw + 2 * mw * t
            hgt = (6 + 5 * math.sin(t * math.pi)) * p["mound"] * (0.7 + 0.3 * hash01(k, 1, 9))
            tip = (x0 + (hash01(k, 2, 9) - 0.5) * 4, FL - hgt)
            pts = [(x0, FL), (lerp((x0, FL), tip, 0.6)[0] + 1, lerp((x0, FL), tip, 0.6)[1]), tip]
            cp2 = curve(pts, 2)
            chain(Mn, cp2, taper(len(cp2), 1.2, 0.5), "U", 0 if k % 2 else -1, ao=0)
            Mn.fixed({ip(tip): "U5"})
    # clip everything below the floor line (sinking)
    for n_, L in Ls.items():
        if isinstance(L, Layer):
            for q in [q for q in L.px if q[1] > FL]:
                L.px.pop(q, None)
        else:
            for q in [q for q in L.px if q[1] > FL]:
                L.px.pop(q, None)
    return Ls, info


# ---------------------------------------------------------------- animations
def a_idle():
    fr = []
    for i in range(6):
        b = math.sin(i / 6 * 2 * math.pi)
        fr.append((170, PP(ch=(35.0, 33.0 + b * 0.8), hd=(38.5 + b * 0.3, 24.0 + b * 1.0), fh=(45.0, 43.0 + b * 0.6), bh=(29.0, 46.0 + b * 0.5),
                           sa=-84 + b * 1.5, wind=b * 0.6, glow=1 + (i in (2, 3)))))
    return fr


def a_walk():
    fr = []
    for i in range(8):
        b = math.sin(i / 8 * 2 * math.pi)
        fr.append((120, PP(ch=(36.0, 32.5 + abs(b) * 0.8), hd=(40.0, 23.8 + abs(b)), fh=(46.5, 42.5 + b * 0.8), bh=(28.5, 46.0 - b * 0.6),
                           sa=-78 + b * 3, wind=-1.2, lean=1.0)))
    return fr


def a_strike():
    up = dict(fh=(32.0, 22.0), sa=-150.0, bh=(40.0, 36.0), ch=(33.0, 32.0), hd=(36.0, 23.0), ha=-4.0)
    return [
        (110, PP(fh=(42.0, 38.0), sa=-110.0, ch=(34.0, 32.8), hd=(37.5, 24.0))),
        (120, PP(fh=(37.0, 30.0), sa=-135.0, bh=(35.0, 40.0), ch=(33.5, 32.5), hd=(36.5, 23.5), ha=0.0)),
        (140, PP(**up)),
        (120, PP(**dict(up, glow=2))),
        (220, PP(**dict(up, glow=2, eye=2, spark=1))),                      # hold: telegraph
        (70, PP(fh=(49.0, 34.0), sa=-10.0, bh=(26.0, 44.0), ch=(37.5, 33.5), hd=(41.5, 25.5), ha=18.0, smear=((32.0, 22.0), -150.0), glow=2, wind=-2.0, flare=0.6)),
        (80, PP(fh=(50.0, 42.0), sa=30.0, bh=(26.0, 46.0), ch=(38.0, 34.0), hd=(42.0, 26.5), ha=22.0, smear=((49.0, 34.0), -10.0), glow=2, wind=-1.5, flare=0.6)),
        (170, PP(fh=(48.0, 43.0), sa=40.0, ch=(37.0, 33.8), hd=(41.0, 25.5), ha=16.0, flare=0.3)),
        (170, PP(fh=(46.0, 43.0), sa=-40.0, ch=(35.5, 33.2), hd=(39.0, 24.5), ha=12.0)),
    ]


def a_cast():
    aim = dict(fh=(44.0, 37.0), sa=-26.0, bh=(40.0, 38.0), ch=(36.5, 33.0), hd=(40.5, 24.5), ha=12.0, lean=1)
    return [
        (120, PP(fh=(46.0, 40.0), sa=-60.0, bh=(33.0, 40.0))),
        (120, PP(fh=(45.5, 38.5), sa=-40.0, bh=(37.0, 38.0), ch=(35.5, 33.0))),
        (130, PP(**dict(aim, glow=2))),
        (130, PP(**dict(aim, glow=2, spark=1))),
        (150, PP(**dict(aim, glow=3, spark=2, eye=2))),
        (120, PP(**dict(aim, glow=3, spark=3, eye=2))),
        (80, PP(**dict(aim, fh=(46.0, 36.5), glow=2, spark=1, wind=-1.5))),                   # spawn: the thorn bolt looses
        (140, PP(**dict(aim, fh=(45.0, 37.5), glow=1))),
        (150, PP(fh=(46.5, 40.0), sa=-50.0, bh=(32.0, 42.0))),
        (150, PP(fh=(45.0, 42.5), sa=-78.0)),
    ]


def a_summon():
    hi = dict(fh=(40.0, 31.0), sa=-88.0, bh=(40.0, 26.0), ch=(35.0, 32.0), hd=(38.0, 22.5), ha=-12.0, flare=0.4)
    return [
        (120, PP(fh=(43.0, 36.0), sa=-88.0, bh=(35.0, 36.0))),
        (120, PP(fh=(41.5, 34.0), sa=-88.0, bh=(38.0, 34.0), ha=-4.0)),
        (140, PP(**dict(hi, glow=2))),
        (180, PP(**dict(hi, glow=3, spark=1, eye=2))),
        (160, PP(**dict(hi, glow=3, spark=2, eye=2))),                       # telegraph
        (70, PP(fh=(42.0, 46.0), sa=-88.0, bh=(40.0, 44.0), ch=(35.5, 35.5), hd=(39.0, 27.0), ha=20.0, glow=2, burst=1, flare=0.9)),   # spawn
        (120, PP(fh=(42.0, 46.5), sa=-88.0, bh=(40.0, 44.5), ch=(35.5, 36.0), hd=(39.0, 27.5), ha=22.0, glow=2, burst=2, flare=0.9)),
        (160, PP(fh=(42.0, 46.5), sa=-88.0, bh=(39.0, 45.0), ch=(35.5, 35.5), hd=(39.0, 27.0), ha=20.0, glow=1, burst=3, flare=0.7)),
        (150, PP(fh=(43.5, 43.0), sa=-86.0, ch=(35.2, 34.0), hd=(38.8, 25.5), ha=14.0, flare=0.3)),
        (150, PP(fh=(45.0, 43.0), sa=-84.0)),
    ]


def a_blink():
    fr = []
    sinks = [0.0, 0.15, 0.4, 0.7, 0.95, 1.0, 0.9, 0.6, 0.3, 0.0]
    mounds = [0.5, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.4]
    for i, (sk, mo) in enumerate(zip(sinks, mounds)):
        ms = 90 if i != 5 else 60
        fr.append((ms, PP(sink=sk, mound=mo, fh=(44.0, 42.0), sa=-86.0, ha=10 + 10 * sk, glow=1 + (i > 5), flare=0.5 * sk)))
    return fr


def a_chant():
    fr = []
    for i in range(6):
        b = math.sin(i / 6 * 2 * math.pi)
        fr.append((140, PP(fh=(39.0, 30.0 + b * 0.8), sa=-92.0 + b * 3, bh=(27.0, 27.0 - b * 0.8), ch=(35.0, 32.5 + b * 0.4), hd=(37.0, 23.0 + b * 0.5), ha=-20.0,
                           glow=3, spark=1 + i % 2, eye=2, flare=0.4 + 0.2 * b, wind=b)))
    return fr


def a_hurt():
    return [(90, PP(ch=(33.0, 33.0), hd=(35.0, 25.0), ha=-24.0, fh=(41.0, 40.0), sa=-70.0, bh=(24.0, 42.0), eye=0, wind=1.8, flare=0.3)),
            (150, PP(ch=(34.0, 33.0), hd=(37.0, 24.5), ha=-6.0, fh=(43.0, 42.0), sa=-78.0, wind=0.8))]


def a_stagger():
    low = dict(ch=(33.0, 38.0), hd=(36.0, 31.0), ha=40.0, fh=(40.0, 50.0), sa=-60.0, bh=(27.0, 52.0), eye=1, flare=0.8, glow=0)
    return [(110, PP(ch=(32.5, 34.0), hd=(34.0, 26.0), ha=-30.0, fh=(40.0, 42.0), sa=-60.0, bh=(24.0, 44.0), eye=0, wind=2)),
            (140, PP(**low)), (300, PP(**dict(low, ha=44.0))), (300, PP(**dict(low, ha=42.0, wind=-0.5)))]


def a_death():
    names = [n for n in LAYERS if n != "FX"]
    kneel = dict(ch=(33.0, 44.0), hd=(36.5, 37.0), ha=46.0, fh=(41.0, 58.0), sa=-40.0, bh=(27.0, 60.0), eye=0, glow=-1, flare=1.0)
    return [(120, PP(ch=(32.5, 33.5), hd=(34.0, 25.5), ha=-34.0, fh=(40.0, 42.0), sa=-55.0, bh=(24.0, 42.0), eye=1, glow=0, wind=2)),
            (150, PP(**kneel)),
            (170, PP(**dict(kneel, mound=0.5))),
            (150, PP(**dict(kneel, mound=0.8), post=collapse(names, 0.85, 0.12, seed=7))),
            (150, PP(**dict(kneel, mound=1.0), post=collapse(names, 0.6, 0.25, seed=7))),
            (160, PP(**dict(kneel, mound=1.0), post=collapse(names, 0.4, 0.38, seed=7))),
            (170, PP(**dict(kneel, mound=1.0), post=collapse(names, 0.22, 0.5, seed=7))),
            (500, PP(**dict(kneel, mound=1.0), post=collapse(names, 0.1, 0.6, seed=7)))]


ANIMS = [("idle", a_idle), ("walk", a_walk), ("strike", a_strike), ("cast", a_cast), ("summon", a_summon), ("blink", a_blink),
         ("chant", a_chant), ("hurt", a_hurt), ("stagger", a_stagger), ("death", a_death)]


def build():
    K.setup(W_, H_)
    meta = None
    for v, name in enumerate(("coven", "coven_b", "coven_c")):
        anims, infos = render_anims(LAYERS, lambda p, k, s, v=v: draw_witch(p, k, s, v), ANIMS, sway_key="ch", loops=("idle", "walk", "chant"))
        if meta is None:
            meta = {"native": 1, "frame": [W_, H_], "anchor": [36, 72],
                    "hurtbox": hurtbox(anims, ["Robe", "Head"], inset=(4, 1, 4)),
                    "attacks": {"strike": {"active": [5, 6], "hit": hit_rect(infos, "strike", [5, 6], x_min=38)}},
                    "spawn": {"cast": {"frame": 6, "at": spawn_pt(infos["cast"][6]["tip"])},
                              "summon": {"frame": 5, "at": spawn_pt(infos["summon"][5]["butt"])}},
                    "telegraph": {"strike": {"frame": 4, "at": spawn_pt(infos["strike"][4]["tip"])},
                                  "cast": {"frame": 4, "at": spawn_pt(infos["cast"][4]["tip"])},
                                  "summon": {"frame": 3, "at": spawn_pt(infos["summon"][3]["tip"])}}}
        tags, flats = export(name, LAYERS, anims, meta if v == 0 else None)
        contact(name, tags, flats)
        print("built", name)


if __name__ == "__main__":
    build()
