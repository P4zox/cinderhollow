#!/usr/bin/env python3
"""THE ANTLERED WARDEN (agent T) -- main boss of Thornveil Wood, built from the user's reference
art/concepts/ref_antlered_warden.png: a towering, gaunt god of dark twisted wood; huge branching antlers hung with moss
and pale ribbons; a small deer-skull face with glowing green eyes; long thin arms; a living-wood staff wrapped in
thorned vines with green-lit leaves at its crook; a cloak of roots trailing over the ground; a green crack at the heart.

    python3 art/gen_thornveil_warden.py [--preview] [--only tag,tag] [--p1only]

Outputs: warden (phase 1) + warden_p2 (the forest wakes: veins of spirit-light, brighter eyes, glowing leaves),
224x176, faces RIGHT, feet on the bottom row, anchor [112,176]; assets/warden_meta.json (per-frame hit shapes for the
staff/antlers are summarised into the attack windows); previews art/previews/warden*.png.

Every pose is built from ONE skeleton with fixed bone lengths (thigh/shin 30, upper/fore arm 26, torso 38, neck 17,
staff 118), so proportions never drift between animations. Hands and feet are IK targets clamped to reach.
"""
import math, os, sys, json
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import thornveil_ckit as C  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome, n_capsule, dirv  # noqa: E402
from thornveil_ckit import mk, rot, madd, curve, chain, taper, deer_skull, antler, ribbon_px, glow_dots, render_anims, hit_rect, hurtbox, collapse, spawn_pt, contact  # noqa: E402
from PIL import Image  # noqa: E402

W_, H_ = 224, 176
FL = 175
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
LAYERS = ["AntlerFar", "CloakBack", "ArmBack", "LegBack", "Body", "LegFront", "CloakFront", "Head", "AntlerNear", "Staff",
          "ArmFront", "Ribbons", "Mound", "FX"]
FXL = {"Ribbons", "FX"}
THIGH, SHIN, UARM, FARM, TORSO, NECK = 30.0, 31.0, 26.0, 27.0, 38.0, 8.0
ST_BUTT, ST_HEAD = 70.0, 48.0        # staff: butt / head distance from the main grip

NEU = dict(hip=(108.0, 117.0), lean=10.0, na=22.0, ha=28.0, at=0.0, bf=(97.0, FL), ff=(122.0, FL), bl=0.0, fl=0.0,
           fh=(140.0, 105.0), sa=-93.0, bh=(96.0, 118.0), bs=None, glow=1, eye=1, smear=None, wind=0.0, sink=0.0, mound=0.0,
           jaw=0.0, burst=0, spark=0, flare=0.0, knee=None, hand_open=0.0, orb=0, bare=False)
PP = mk(NEU)


def clamp_reach(s, t, L):
    d = sub(t, s)
    ln = math.hypot(*d)
    if ln <= L - 0.4:
        return t
    return madd(s, ((d[0] / ln, d[1] / ln), L - 0.4))


def limb(L, s, t, l1, l2, pref, r, mat, bias, grain_seed=0):
    t = clamp_reach(s, t, l1 + l2)
    j = ik(s, t, l1, l2, pref)
    pts = curve([s, madd(lerp(s, j, 0.5), ((1, 0), 0.6)), j, madd(lerp(j, t, 0.5), ((-1, 0), 0.5)), t], 2)
    rr = [r[0] + (r[1] - r[0]) * min(1, i / (len(pts) * 0.45)) if i < len(pts) * 0.45 else
          r[1] + (r[2] - r[1]) * (i - len(pts) * 0.45) / (len(pts) * 0.55) for i in range(len(pts))]
    m = chain(L, pts, rr, mat, bias)
    # bark grain: dark streaks along the limb, and knotted rings at the joints
    for q in m:
        if hash01(q[0] // 2, q[1] // 3, grain_seed) < 0.16:
            L.decal([q], (mat, max(0, 1 + bias // 2)))
    for q in K.mask_disc(j, r[1] * 1.15):
        if q in L.px:
            L.decal([q], (mat, 2 if hash01(*q, 5) < 0.5 else 3))
    return j, t, m


def draw(p, fi, sw, p2):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX = FXLayer("FX")
    RB = FXLayer("Ribbons")
    Ls["FX"] = FX
    Ls["Ribbons"] = RB
    info = {"hit": set(), "ant": set()}
    dy = p["sink"] * 150.0
    D = lambda q: (q[0], q[1] + dy)
    s = sw * 0.8 + p["wind"]
    hip = D(p["hip"])
    tdir = dirv(-90 + p["lean"])
    chest = madd(hip, (tdir, TORSO))
    ndir = dirv(-90 + p["na"])
    headc = madd(chest, (tdir, 4.0), (ndir, NECK + 5.0))
    ha = p["ha"]
    # -------------------------------------------------------------- legs (long, gnarled; roots wind around them)
    for L, foot, lift, bias, seed in ((Ls["LegBack"], p["bf"], p["bl"], -2, 1), (Ls["LegFront"], p["ff"], p["fl"], 0, 2)):
        f = D((foot[0], foot[1] - lift))
        h0 = madd(hip, ((1, 0), 2.5 if bias == 0 else -2.5))
        kn, ft, m = limb(L, h0, (f[0], f[1] - 3.0), THIGH, SHIN, (1, -0.15), (5.2, 3.2, 2.6), "E", bias, seed)
        # root-toes gripping the floor
        for k, (a, ln) in enumerate(((-12, 9.0), (8, 11.0), (30, 7.0), (170, 6.0))):
            tip = madd(ft, (dirv(a), ln))
            tip = (tip[0], min(FL, tip[1] + 2.5))
            chain(L, curve([ft, madd(lerp(ft, tip, 0.5), ((0, -1), 1.2)), tip], 2), [2.2, 1.8, 1.4, 1.0, 0.7], "E", bias, ao=0)
        info["hit"] |= m
    # -------------------------------------------------------------- torso: narrow waist, ribbed barrel of twisted wood
    Bd = Ls["Body"]
    waist = madd(hip, (tdir, 12.0))
    spine = curve([hip, madd(waist, (dirv(p["lean"]), -1.2)), madd(chest, (tdir, -8.0)), chest, madd(chest, (tdir, 6.0))], 3)
    radii = []
    for i in range(len(spine)):
        t = i / (len(spine) - 1)
        radii.append(6.2 - 2.2 * math.sin(min(1, t * 2.2) * math.pi) if t < 0.45 else 4.2 + 3.8 * math.sin((t - 0.45) / 0.55 * math.pi * 0.62))
    bm = chain(Bd, spine, radii, "E", 0)
    # twisted wood: diagonal fibres
    for q in bm:
        if (q[0] * 2 + q[1] + int(hash01(q[0] // 4, q[1] // 4, 3) * 3)) % 7 == 0:
            Bd.decal([q], ("E", 1))
    # the heart-crack: a vertical seam of spirit-light down the chest
    crack = []
    for i in range(22):
        c = madd(chest, (tdir, 4.0 - i * 1.3), (dirv(p["lean"]), 3.4 + math.sin(i * 1.1) * 1.0))
        crack.append(ip(c))
    lv = 3 + (1 if p2 else 0) + (1 if p["glow"] >= 3 else 0)
    Bd.fixed({q: f"S{min(5, lv - (1 if i % 4 == 3 else 0))}" for i, q in enumerate(crack) if q in Bd.px})
    info["heart"] = crack[4]
    info["hit"] |= bm
    # -------------------------------------------------------------- cloak of roots: strands from the back of the torso to the ground, trailing
    backv = dirv(180 + p["lean"])
    for k in range(13):
        t = k / 12
        a0 = madd(lerp(hip, chest, 0.15 + 0.85 * t), (backv, 5.0 + 3.5 * t))
        spread = 10 + 34 * (1 - t) ** 0.5 + p["flare"] * 16
        endx = hip[0] - spread - k * 1.4 + s * (1.5 + t * 2)
        end = (endx, FL + (1 if k % 3 else 0))
        midp = (lerp(a0, end, 0.55)[0] - 6 * (1 - t) + s * 2.5 * (0.5 + t), lerp(a0, end, 0.55)[1] - 3)
        pts = curve([a0, midp, (end[0] + 6, FL - 2), end], 3)
        pts = [(x, min(FL, y)) for x, y in pts]
        L = Ls["CloakBack"]
        chain(L, pts, taper(len(pts), 2.4 + t * 0.8, 1.0), "E", -1 if k % 2 else -2, ao=0)
        for i in range(0, len(pts), 5):
            if hash01(k, i, 8) < 0.35:
                L.decal([ip(pts[i])], ("H", 3))
    # a few roots draped over the hips in front of the legs, with moss
    for k in range(4):
        a0 = madd(hip, (dirv(p["lean"]), -3.0 + k * 3.0), (tdir, 4.0))
        end = (hip[0] - 8 + k * 7 + s * 1.5, hip[1] + 34 + k % 2 * 6)
        pts = curve([a0, (lerp(a0, end, 0.5)[0] + 2, lerp(a0, end, 0.5)[1]), end], 3)
        pts = [(x, min(FL, y)) for x, y in pts]
        chain(Ls["CloakFront"], pts, taper(len(pts), 2.0, 0.6), "E", 0, ao=0)
        C.moss_drape(Ls["CloakFront"], [pts[len(pts) // 2]], fi, k + 20, n=1, maxlen=5)
    # -------------------------------------------------------------- arms (long, thin, clawed)
    shF = madd(chest, (dirv(p["lean"]), 3.0), (tdir, 1.0))
    shB = madd(chest, (dirv(p["lean"]), -5.0), (tdir, 2.0))
    g = D(p["fh"])
    sd = dirv(p["sa"])
    if p["bs"] is not None:
        bht = madd(g, (sd, p["bs"]))
    else:
        bht = D(p["bh"])
    for L, sh, hand, bias, pref, seed in ((Ls["ArmBack"], shB, bht, -2, (-0.6, 1), 11), (Ls["ArmFront"], shF, g, 0, (-0.5, 1), 12)):
        el, hnd, m = limb(L, sh, hand, UARM, FARM, pref, (4.2, 2.7, 2.2), "E", bias, seed)
        L.paint(n_dome(hnd, 3.0, 2.8), "E", bias, ao=0)
        # long claw fingers curling round the staff (or splayed when open)
        fdir = sub(hnd, el)
        fl_ = math.hypot(*fdir) or 1
        fdir = (fdir[0] / fl_, fdir[1] / fl_)
        for k in (-1, 0, 1, 2):
            a = math.degrees(math.atan2(fdir[1], fdir[0])) + k * (18 + 22 * p["hand_open"])
            tip = madd(hnd, (dirv(a), 5.5 + p["hand_open"] * 3))
            chain(L, [hnd, madd(lerp(hnd, tip, 0.6), (dirv(a + 90), 0.8 * (1 - p["hand_open"]))), tip], [1.1, 0.8, 0.5], "E", bias, ao=0)
            L.fixed({ip(tip): "J3" if bias == 0 else "J2"})
        if bias == 0:
            info["hand"] = hnd
        else:
            info["bhand"] = hnd
        info["hit"] |= m
        if p2:   # veins of spirit-light up the forearms
            for i, q in enumerate(polyline([el, madd(lerp(el, hnd, 0.5), ((0, 1), 1.0)), hnd])):
                if i % 2 == 0 and q in L.px:
                    L.fixed({q: "S3" if i % 4 else "S4"})
    # -------------------------------------------------------------- staff: living wood, a thorned vine spiralling it, green-lit leaves in its crook
    St = Ls["Staff"]
    butt = madd(g, (sd, -ST_BUTT))
    head = madd(g, (sd, ST_HEAD))
    pv = (-sd[1], sd[0])
    sp = curve([butt, madd(lerp(butt, head, 0.3), (pv, 1.4)), madd(lerp(butt, head, 0.62), (pv, -1.4)), head], 6)
    chain(St, sp, taper(len(sp), 1.6, 2.4), "E", 0, ao=0)
    vine = {}
    for i in range(len(sp)):
        q = madd(sp[i], (pv, 2.4 * math.sin(i * 0.55)))
        c = "U3" if math.sin(i * 0.55) > 0 else "U1"
        vine[ip(q)] = c
        if i % 6 == 3:
            vine[ip(madd(q, (pv, 1.6 * (1 if math.sin(i * 0.55) > 0 else -1))))] = "U5"
    St.fixed(vine)
    # the crook: three twisting prongs curling forward, knotted, cradling a green light
    tips = []
    for k, (off, curl) in enumerate(((-1, 1.0), (0.4, -0.6), (1.2, 0.4))):
        b = madd(head, (sd, -2.0 + k * 2.0))
        pts = [b]
        for i in range(1, 6):
            a = math.degrees(math.atan2(sd[1], sd[0])) + curl * 28 * i + off * 20
            pts.append(madd(pts[-1], (dirv(a), 3.4 - i * 0.3)))
        cp = curve(pts, 2)
        chain(St, cp, taper(len(cp), 1.5, 0.6), "E", 0, ao=0)
        tips.append(cp[-1])
    knot = madd(head, (sd, 5.0))
    info["tip"] = knot
    info["butt"] = butt
    gl = p["glow"] + (1 if p2 else 0)
    # leaves along the crook
    for k, tp in enumerate([] if p["bare"] else tips + [madd(head, (sd, -6), (pv, 3.0)), madd(head, (sd, -10), (pv, -3.0))]):
        lv_ = "S3" if gl >= 2 else "H5"
        FX.put([ip(tp), ip(madd(tp, (pv, 1.0)))], lv_)
        FX.put([ip(madd(tp, (sd, 1.0)))], "S4" if gl >= 2 else "H4")
    for q in K.mask_disc(knot, 1.8 + 0.6 * max(0, gl)):
        d = math.hypot(q[0] + .5 - knot[0], q[1] + .5 - knot[1])
        FX.put([q], "S5" if d < 1.0 else "S4" if d < 2.0 else "S3")
    if gl >= 2:
        glow_dots(FX, knot, 4.0 + gl * 1.5, 6 + gl * 2, fi, cols=("S3", "S4", "S2"), seed=1)
    stm = set(St.px)
    info["staff"] = stm
    # -------------------------------------------------------------- neck + head (a small deer skull), antlers
    Hd = Ls["Head"]
    nape = madd(headc, (dirv(ha + 180), 4.5), (dirv(ha + 90), 2.0))
    chain(Hd, curve([madd(chest, (tdir, 3.0)), madd(lerp(chest, nape, 0.5), (dirv(p["lean"]), 1.4)), nape], 3), [3.0, 2.6, 2.3, 2.1, 2.0, 1.9, 1.9], "E", 0)
    # a mane of moss and root fibres at the neck
    C.moss_drape(Hd, [madd(chest, (tdir, 5.0 - i * 2.0), (dirv(p["lean"] + 180), 3.0)) for i in range(4)], fi, 31, n=4, maxlen=7)
    hk = deer_skull(Hd, headc, ha, 1.6, eye=p["eye"] + (1 if p2 else 0), jaw=p["jaw"])
    info["eye"] = hk["eye"]
    info["snout"] = hk["snout"]
    e = hk["eye"]
    if p["eye"] >= 2 or p2:
        FX.put([(e[0] + 2, e[1]), (e[0] + 3, e[1])], "S3")
        if p["eye"] >= 2 and p2:
            FX.put([(e[0] + 4, e[1]), (e[0] + 5, e[1] - 1)], "S2")
    # ears (small, leaf-like) behind the skull
    ear = [madd(hk["crown"], (dirv(ha + 200), 1.0)), madd(hk["crown"], (dirv(ha + 160), 7.5)), madd(hk["crown"], (dirv(ha + 180), 2.0), (dirv(ha + 90), 2.5))]
    Hd.paint(n_plate(poly_mask(ear), 1.0, (-0.2, -0.2)), "E", -1, ao=0)
    at = p["at"]
    tipsF, bF = antler(Ls["AntlerFar"], hk["ab2"], -134 + ha * 0.45 + at, 3.7, "J", -1, tines=5, spread=1.1, w=0.5)
    tipsN, bN = antler(Ls["AntlerNear"], hk["ab"], -96 + ha * 0.45 + at, 4.1, "J", 0, tines=6, spread=1.2, w=0.5)
    info["ant"] |= set(Ls["AntlerNear"].px) | set(Ls["AntlerFar"].px)
    # moss draped over the antlers and pale ribbons knotted to the tines, fluttering
    for L, beam, tipl, sd_ in ((Ls["AntlerFar"], bF, tipsF, 3), (Ls["AntlerNear"], bN, tipsN, 7)):
        anchors = [beam[int(len(beam) * f)] for f in (0.35, 0.55, 0.8)]
        C.moss_drape(L, anchors, fi, sd_, n=3, maxlen=10)
        for k, t in enumerate(tipl[1:3] if not p["bare"] else []):
            for q, c in ribbon_px((t[0], t[1] + 1), fi, sd_ + k * 1.7, L=16 + k * 9 + (sd_ % 4) * 2, sway=-0.35 + s * 0.12).items():
                RB.put([q], c)
        # small wooden charms hanging on cords
        a = anchors[1]
        for i in range(5 if not p["bare"] else 0):
            RB.put([ip((a[0] + 0.3 * i * math.sin(fi * 0.7), a[1] + 2 + i))], "N2")
        if not p["bare"]: RB.put([ip((a[0], a[1] + 8)), ip((a[0] + 1, a[1] + 8)), ip((a[0], a[1] + 9))], "U4")
    if p2:   # blossoms on the antlers: the forest is waking
        for k, t in enumerate(tipsN[1:] + tipsF[1:3]):
            FX.put([ip(t), (ip(t)[0] + 1, ip(t)[1])], "N5" if k % 2 else "S4")
    # -------------------------------------------------------------- shading rims
    for L in (Bd, Hd, Ls["ArmFront"], Ls["LegFront"], St):
        C.rim(L, {"E"}, 4)
    for L in (Ls["AntlerNear"],):
        C.rim(L, {"J"}, 5)
    # -------------------------------------------------------------- fx: smears, sparks, root bursts, the thorn-light in the palm
    if p["smear"]:
        g0, a0, u0, u1 = p["smear"]
        hot = K.swept(FX, D(g0), a0, g, p["sa"], u0, u1, hw=1.4, pal="spirit", start=0.2, clip_y=FL)
        info["hit_staff"] = hot | stm
    if p["spark"]:
        glow_dots(FX, knot, 6 + p["spark"] * 3, 12, fi, cols=("S4", "S5", "S3"), seed=3)
    if p["orb"]:
        hb = info.get("bhand", bht)
        for q in K.mask_disc(hb, 1.5 + p["orb"]):
            d = math.hypot(q[0] + .5 - hb[0], q[1] + .5 - hb[1])
            FX.put([q], "S5" if d < 1.2 else "S4" if d < 2.4 else "S3")
        glow_dots(FX, hb, 4 + p["orb"] * 2, 8, fi, cols=("S3", "S4"), seed=5)
    if p["burst"]:
        b = (butt[0], min(FL, butt[1]))
        for k in range(22):
            a = -math.pi * (0.05 + 0.9 * hash01(k, p["burst"], 5))
            r = 3 + p["burst"] * 4.5 * hash01(k, 3, 7)
            FX.put([ip((b[0] + math.cos(a) * r * 1.6, b[1] + math.sin(a) * r))], "S4" if k % 3 == 0 else "S3" if k % 3 == 1 else "U4")
    # -------------------------------------------------------------- the root mound he sinks into / rises from
    if p["mound"] > 0:
        Mn = Ls["Mound"]
        mw = 34 * p["mound"]
        for k in range(26):
            t = k / 25
            x0 = hip[0] - mw + 2 * mw * t + 4
            hgt = (14 + 16 * math.sin(t * math.pi)) * p["mound"] * (0.6 + 0.4 * hash01(k, 1, 9))
            tip = (x0 + (hash01(k, 2, 9) - 0.5) * 10, FL - hgt)
            cp2 = curve([(x0, FL), (lerp((x0, FL), tip, 0.55)[0] + 3 * (1 if k % 2 else -1), lerp((x0, FL), tip, 0.55)[1]), tip], 3)
            chain(Mn, cp2, taper(len(cp2), 2.6, 0.7), "E", 0 if k % 2 else -1, ao=0)
            if k % 3 == 0:
                Mn.fixed({ip(tip): "S3"})
    # clip below the floor
    for n_, L in Ls.items():
        for q in [q for q in L.px if q[1] > FL]:
            L.px.pop(q, None)
            if isinstance(L, Layer):
                L.noout.discard(q)
    return Ls, info


# =========================================================================== animations
def idle():
    fr = []
    for i in range(8):
        b = math.sin(i / 8 * 2 * math.pi)
        fr.append((150, PP(hip=(108.0, 117.0 + b * 0.8), lean=10 + b * 0.8, na=22 + b * 1.5, ha=28 + b * 2, fh=(140.0, 105.0 + b * 0.6),
                           bh=(97.0 + b * 0.5, 119.0 + b), wind=b * 0.8, at=b * 1.2, glow=1 + (i in (3, 4)))))
    return fr


def walk():
    fr = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        bob = abs(math.sin(ph)) * 1.6
        fx_ = 110 + 14 * math.cos(ph)
        bx_ = 110 - 14 * math.cos(ph)
        fr.append((140, PP(hip=(110.0, 117.0 - bob), lean=13, na=24, ha=30, ff=(fx_ + 4, FL), bf=(bx_ - 4, FL),
                           fl=max(0, 4.0 * math.sin(ph)), bl=max(0, -4.0 * math.sin(ph)),
                           fh=(140.0 + 6 * math.cos(ph + 0.6), 106.0 - bob), sa=-93 + 4 * math.cos(ph + 0.6),
                           bh=(96.0 - 5 * math.cos(ph), 118.0 - bob), wind=-1.2, at=math.sin(ph) * 1.5)))
    return fr


def sweep():
    # two-handed low sweep: staff drawn back behind the hip, then swept in a wide arc along the ground in front
    back = dict(hip=(104.0, 120.0), lean=-4.0, na=10.0, ha=18.0, fh=(96.0, 130.0), sa=196.0, bs=-24.0, ff=(126.0, FL), bf=(90.0, FL))
    return [
        (110, PP(hip=(106.0, 118.0), lean=4.0, na=16.0, ha=24.0, fh=(128.0, 118.0), sa=-150.0, bs=-24.0)),
        (120, PP(hip=(105.0, 119.0), lean=0.0, na=12.0, ha=20.0, fh=(112.0, 126.0), sa=175.0, bs=-24.0, ff=(124.0, FL))),
        (140, PP(**back)),
        (150, PP(**dict(back, glow=2))),
        (200, PP(**dict(back, glow=2, eye=2, spark=1, wind=1.0))),                                  # hold: telegraph
        (70, PP(hip=(112.0, 121.0), lean=16.0, na=26.0, ha=34.0, fh=(136.0, 138.0), sa=-2.0, bs=-24.0, ff=(132.0, FL), bf=(96.0, FL),
                smear=((96.0, 130.0), 196.0, 20.0, 64.0), glow=2, eye=2, wind=-2.5, flare=0.4)),
        (70, PP(hip=(114.0, 121.0), lean=20.0, na=28.0, ha=36.0, fh=(144.0, 134.0), sa=-22.0, bs=-24.0, ff=(134.0, FL), bf=(98.0, FL),
                smear=((136.0, 138.0), -2.0, 20.0, 64.0), glow=2, eye=2, wind=-2.5, flare=0.4)),
        (110, PP(hip=(114.0, 120.0), lean=20.0, na=28.0, ha=34.0, fh=(146.0, 124.0), sa=-48.0, bs=-24.0, ff=(134.0, FL), bf=(98.0, FL), wind=-1.5)),
        (140, PP(hip=(113.0, 119.0), lean=17.0, na=26.0, ha=32.0, fh=(144.0, 116.0), sa=-66.0, bs=-24.0, ff=(132.0, FL), bf=(98.0, FL))),
        (150, PP(hip=(111.0, 118.0), lean=14.0, na=24.0, ha=30.0, fh=(142.0, 110.0), sa=-82.0, ff=(128.0, FL), bf=(98.0, FL))),
        (150, PP(hip=(109.0, 117.5), lean=11.0, na=22.0, ha=28.0, fh=(141.0, 106.0), sa=-90.0, ff=(124.0, FL))),
        (150, PP()),
    ]


def thrust():
    pull = dict(hip=(102.0, 121.0), lean=4.0, na=18.0, ha=26.0, fh=(104.0, 118.0), sa=10.0, bs=-22.0, ff=(118.0, FL), bf=(88.0, FL))
    return [
        (110, PP(hip=(106.0, 118.0), lean=6.0, fh=(130.0, 106.0), sa=-40.0, bs=-22.0)),
        (120, PP(hip=(104.0, 118.5), lean=2.0, na=16.0, ha=24.0, fh=(116.0, 105.0), sa=-6.0, bs=-22.0, ff=(120.0, FL))),
        (140, PP(**pull)),
        (150, PP(**dict(pull, glow=2))),
        (210, PP(**dict(pull, glow=2, eye=2, spark=1))),                                               # telegraph
        (70, PP(hip=(122.0, 124.0), lean=34.0, na=36.0, ha=42.0, fh=(152.0, 128.0), sa=16.0, bs=-22.0, ff=(146.0, FL), bf=(100.0, FL), bl=0.0,
                smear=((104.0, 118.0), 10.0, 30.0, 50.0), glow=2, eye=2, wind=-3.0)),
        (90, PP(hip=(124.0, 124.0), lean=36.0, na=37.0, ha=43.0, fh=(156.0, 130.0), sa=17.0, bs=-22.0, ff=(148.0, FL), bf=(102.0, FL),
                smear=((152.0, 128.0), 16.0, 42.0, 50.0), glow=2, eye=2, wind=-3.0)),
        (140, PP(hip=(122.0, 122.0), lean=28.0, na=30.0, ha=36.0, fh=(154.0, 124.0), sa=14.0, bs=-22.0, ff=(146.0, FL), bf=(102.0, FL), wind=-1.5)),
        (140, PP(hip=(118.0, 119.0), lean=18.0, na=26.0, ha=32.0, fh=(150.0, 110.0), sa=-30.0, bs=-22.0, ff=(140.0, FL), bf=(102.0, FL))),
        (150, PP(hip=(113.0, 118.0), lean=13.0, na=24.0, ha=30.0, fh=(144.0, 107.0), sa=-75.0, ff=(130.0, FL), bf=(100.0, FL))),
        (150, PP()),
    ]


def erupt():
    hi = dict(hip=(106.0, 115.0), lean=2.0, na=0.0, ha=6.0, fh=(118.0, 62.0), sa=-84.0, bs=-18.0, ff=(124.0, FL), bf=(92.0, FL), at=-6.0)
    slam = dict(hip=(110.0, 124.0), lean=22.0, na=32.0, ha=42.0, fh=(138.0, 112.0), sa=-86.0, bs=-18.0, ff=(128.0, FL), bf=(94.0, FL), at=4.0, flare=0.8)
    return [
        (110, PP(fh=(136.0, 96.0), sa=-90.0, bs=-18.0)),
        (120, PP(hip=(107.0, 116.0), lean=6.0, na=12.0, ha=18.0, fh=(128.0, 80.0), sa=-88.0, bs=-18.0, ff=(123.0, FL))),
        (130, PP(**dict(hi, glow=2))),
        (140, PP(**dict(hi, glow=2, spark=1))),
        (160, PP(**dict(hi, glow=3, spark=2, eye=2))),
        (180, PP(**dict(hi, glow=3, spark=2, eye=2, jaw=0.4))),                                      # telegraph
        (60, PP(**dict(slam, glow=3, eye=2, burst=1, smear=((118.0, 62.0), -84.0, 30.0, 48.0)))),    # spawn: roots erupt
        (110, PP(**dict(slam, glow=3, eye=2, burst=2))),
        (140, PP(**dict(slam, glow=2, eye=2, burst=3))),
        (160, PP(**dict(slam, glow=2, burst=0, flare=0.6))),
        (150, PP(hip=(109.0, 119.0), lean=14.0, na=24.0, ha=30.0, fh=(140.0, 106.0), sa=-90.0, bs=-18.0, ff=(126.0, FL), flare=0.3)),
        (150, PP()),
    ]


def volley():
    wind_ = dict(bh=(128.0, 88.0), hand_open=0.0, lean=4.0, na=18.0, ha=22.0, hip=(106.0, 118.0))
    return [
        (110, PP(bh=(112.0, 100.0), lean=8.0)),
        (120, PP(**dict(wind_, orb=1))),
        (130, PP(**dict(wind_, bh=(122.0, 80.0), orb=2))),
        (140, PP(**dict(wind_, bh=(118.0, 76.0), orb=3, glow=2, eye=2))),
        (180, PP(**dict(wind_, bh=(116.0, 74.0), orb=3, glow=2, eye=2, spark=0))),                    # telegraph
        (70, PP(hip=(112.0, 118.0), lean=18.0, na=26.0, ha=30.0, bh=(160.0, 96.0), hand_open=1.0, orb=1, glow=2, eye=2, wind=-2.5)),
        (80, PP(hip=(113.0, 118.0), lean=20.0, na=27.0, ha=32.0, bh=(164.0, 100.0), hand_open=1.0, glow=2, eye=2, wind=-2.0)),     # spawn
        (140, PP(hip=(112.0, 118.0), lean=17.0, na=25.0, ha=30.0, bh=(150.0, 106.0), hand_open=0.6)),
        (150, PP(hip=(110.0, 117.5), lean=13.0, bh=(120.0, 114.0), hand_open=0.2)),
        (150, PP()),
    ]


def charge_prep():
    low = dict(hip=(104.0, 124.0), lean=38.0, na=62.0, ha=84.0, at=38.0, fh=(118.0, 130.0), sa=8.0, bs=-24.0, bh=(112.0, 136.0), ff=(126.0, FL), bf=(84.0, FL))
    return [
        (110, PP(hip=(106.0, 119.0), lean=18.0, na=34.0, ha=48.0, at=14.0, fh=(130.0, 118.0), sa=-40.0)),
        (130, PP(**dict(low, ha=72.0, at=28.0))),
        (140, PP(**low)),
        (150, PP(**dict(low, bl=4.0, wind=1.0))),
        (150, PP(**dict(low, bl=0.0, eye=2, glow=2))),
        (220, PP(**dict(low, eye=2, glow=2, spark=1, bl=3.0))),                                      # telegraph (pawing)
        (90, PP(**dict(low, eye=2, glow=2))),
    ]


def charge():
    fr = []
    for i in range(4):
        ph = i / 4 * 2 * math.pi
        fr.append((85, PP(hip=(110.0, 122.0 - abs(math.sin(ph)) * 2), lean=42.0, na=64.0, ha=86.0, at=40.0, fh=(124.0, 132.0), sa=6.0, bs=-24.0,
                          bh=(116.0, 136.0), ff=(118 + 18 * math.cos(ph), FL), bf=(100 - 18 * math.cos(ph), FL),
                          fl=max(0, 6 * math.sin(ph)), bl=max(0, -6 * math.sin(ph)), eye=2, glow=2, wind=-3.5, flare=0.6)))
    return fr


def charge_end():
    return [
        (90, PP(hip=(108.0, 122.0), lean=30.0, na=50.0, ha=70.0, at=30.0, fh=(130.0, 124.0), sa=-20.0, ff=(136.0, FL), bf=(96.0, FL), eye=2, wind=-2.0, flare=0.5)),
        (100, PP(hip=(104.0, 120.0), lean=10.0, na=30.0, ha=44.0, at=12.0, fh=(136.0, 108.0), sa=-70.0, ff=(132.0, FL), bf=(94.0, FL), wind=1.0)),
        (130, PP(hip=(103.0, 116.0), lean=-6.0, na=6.0, ha=10.0, at=-8.0, fh=(134.0, 98.0), sa=-96.0, ff=(128.0, FL), bf=(92.0, FL), jaw=0.5, wind=1.5)),
        (160, PP(hip=(104.0, 116.0), lean=-4.0, na=8.0, ha=12.0, at=-6.0, fh=(136.0, 100.0), sa=-94.0, ff=(126.0, FL), jaw=0.4)),
        (150, PP(hip=(106.0, 117.0), lean=6.0, na=18.0, ha=24.0, fh=(138.0, 104.0), sa=-93.0)),
        (150, PP()),
    ]


def sink():
    fr = []
    sk = [0.0, 0.0, 0.05, 0.15, 0.3, 0.5, 0.7, 0.88, 1.0]
    mo = [0.0, 0.3, 0.6, 0.9, 1.0, 1.0, 1.0, 0.9, 0.6]
    for i in range(9):
        fr.append((110 if i < 7 else 90, PP(sink=sk[i], mound=mo[i], fh=(134.0, 100.0), sa=-90.0 + (i * 25 if i < 3 else 0), bs=-18.0 if i < 3 else None,
                                            ha=28 + 20 * sk[i], at=6 * sk[i], glow=2, eye=2 if i >= 2 else 1, flare=0.8, wind=0.5)))
    return fr


def rise():
    fr = []
    sk = [1.0, 0.8, 0.5, 0.25, 0.08, 0.0, 0.0, 0.0, 0.0]
    mo = [0.6, 0.9, 1.0, 1.0, 0.8, 0.6, 0.35, 0.1, 0.0]
    for i in range(9):
        kw = dict(sink=sk[i], mound=mo[i], glow=2, eye=2, flare=0.6)
        if i < 4:
            kw.update(fh=(128.0, 128.0), sa=-30.0, bs=-20.0, lean=20.0, na=40.0, ha=56.0, at=16.0)
        elif i == 4:
            kw.update(fh=(128.0, 126.0), sa=-20.0, bs=-20.0, lean=22.0, na=40.0, ha=56.0, at=16.0, spark=1)            # telegraph
        elif i == 5:
            kw.update(fh=(140.0, 88.0), sa=-62.0, bs=-20.0, lean=4.0, na=6.0, ha=4.0, at=-12.0, smear=((128.0, 126.0), -20.0, 24.0, 48.0), wind=-2)
        elif i == 6:
            kw.update(fh=(134.0, 70.0), sa=-100.0, bs=-20.0, lean=-2.0, na=0.0, ha=0.0, at=-14.0, smear=((140.0, 88.0), -62.0, 24.0, 48.0), wind=-2)
        elif i == 7:
            kw.update(fh=(136.0, 88.0), sa=-96.0, lean=4.0, na=12.0, ha=16.0, at=-4.0)
        else:
            kw.update(fh=(140.0, 104.0), sa=-93.0)
        fr.append((110 if i not in (4, 5, 6) else (170 if i == 4 else 70), PP(**kw)))
    return fr


def summon():
    up = dict(hip=(106.0, 116.0), lean=0.0, na=-4.0, ha=-8.0, at=-10.0, fh=(132.0, 60.0), sa=-92.0, bh=(78.0, 96.0), hand_open=1.0)
    return [
        (110, PP(fh=(136.0, 94.0), bh=(92.0, 112.0))),
        (120, PP(hip=(107.0, 116.5), lean=6.0, na=10.0, ha=12.0, fh=(134.0, 78.0), bh=(86.0, 104.0), hand_open=0.5)),
        (130, PP(**dict(up, glow=2))),
        (140, PP(**dict(up, glow=3, spark=1, eye=2))),
        (160, PP(**dict(up, glow=3, spark=2, eye=2, jaw=0.3))),
        (180, PP(**dict(up, glow=3, spark=3, eye=2, jaw=0.5))),                                        # telegraph
        (100, PP(**dict(up, glow=3, spark=2, eye=2, jaw=0.6, burst=2, fh=(132.0, 64.0)))),              # spawn: thorn walls
        (140, PP(**dict(up, glow=2, eye=2, jaw=0.3, fh=(133.0, 70.0)))),
        (150, PP(hip=(107.0, 116.5), lean=6.0, na=12.0, ha=16.0, fh=(136.0, 90.0), bh=(90.0, 110.0))),
        (150, PP()),
    ]


def roar():
    wide = dict(hip=(104.0, 116.0), lean=-8.0, na=-18.0, ha=-34.0, at=-18.0, fh=(150.0, 98.0), sa=-80.0, bh=(70.0, 92.0), hand_open=1.0, jaw=1.0, eye=2, glow=3, flare=0.8)
    return [
        (120, PP(hip=(107.0, 118.0), lean=16.0, na=30.0, ha=44.0, at=10.0)),
        (140, PP(hip=(106.0, 120.0), lean=24.0, na=40.0, ha=56.0, at=18.0, bh=(104.0, 126.0))),
        (140, PP(hip=(105.0, 118.0), lean=4.0, na=6.0, ha=0.0, at=-6.0, bh=(86.0, 104.0), hand_open=0.6, jaw=0.4, eye=2)),
        (130, PP(**wide)),
        (160, PP(**dict(wide, spark=1, wind=1.5))),
        (160, PP(**dict(wide, spark=2, wind=2.0, at=-20.0))),
        (160, PP(**dict(wide, spark=1, wind=2.0, at=-19.0))),
        (150, PP(**dict(wide, jaw=0.6, spark=0, wind=1.0))),
        (150, PP(hip=(106.0, 117.0), lean=6.0, na=14.0, ha=18.0, at=0.0, bh=(92.0, 110.0), hand_open=0.3, eye=2)),
        (150, PP()),
    ]


def stagger():
    low = dict(hip=(100.0, 128.0), lean=30.0, na=58.0, ha=78.0, at=26.0, fh=(128.0, 132.0), sa=-70.0, bh=(92.0, 150.0), ff=(122.0, FL), bf=(80.0, FL),
               eye=1, glow=0, flare=0.7, knee=True)
    return [(100, PP(hip=(102.0, 118.0), lean=-12.0, na=-10.0, ha=-20.0, at=-14.0, fh=(132.0, 100.0), sa=-70.0, bh=(84.0, 106.0), eye=0, wind=2.5)),
            (130, PP(hip=(100.0, 124.0), lean=12.0, na=36.0, ha=56.0, at=12.0, fh=(128.0, 118.0), sa=-72.0, bh=(88.0, 136.0), ff=(122.0, FL), bf=(82.0, FL))),
            (160, PP(**low)), (400, PP(**dict(low, ha=80.0, wind=-0.5))), (400, PP(**dict(low, ha=79.0)))]


def death():
    kneel = dict(hip=(102.0, 146.0), lean=24.0, na=52.0, ha=74.0, at=24.0, fh=(130.0, 150.0), sa=-60.0, bh=(94.0, 164.0), ff=(128.0, FL), bf=(76.0, FL),
                 eye=1, glow=0, flare=1.0)
    names = [n for n in LAYERS if n not in ("FX", "Ribbons")]
    fr = [(120, PP(hip=(103.0, 118.0), lean=-14.0, na=-16.0, ha=-30.0, at=-16.0, fh=(134.0, 98.0), sa=-70.0, bh=(80.0, 100.0), jaw=0.8, eye=2, glow=2, wind=3.0)),
          (150, PP(hip=(102.0, 128.0), lean=10.0, na=30.0, ha=46.0, at=10.0, fh=(130.0, 124.0), sa=-66.0, bh=(88.0, 136.0), ff=(124.0, FL), bf=(80.0, FL), eye=2, glow=1)),
          (180, PP(**kneel)),
          (220, PP(**dict(kneel, eye=1, glow=1, mound=0.3))),
          (200, PP(**dict(kneel, eye=0, glow=0, mound=0.6)))]
    for k, (sq, burn) in enumerate(((0.92, 0.06), (0.82, 0.12), (0.7, 0.2), (0.58, 0.28), (0.46, 0.36), (0.36, 0.44), (0.28, 0.5), (0.22, 0.54), (0.2, 0.56))):
        fr.append((170 if k < 8 else 700, PP(**dict(kneel, eye=0, glow=-1, bare=k >= 3, mound=0.8 + 0.02 * k), post=collapse(names, sq, burn, seed=9, spread=0.35))))
    return fr


ANIMS = [("idle", idle), ("walk", walk), ("sweep", sweep), ("thrust", thrust), ("erupt", erupt), ("volley", volley),
         ("charge_prep", charge_prep), ("charge", charge), ("charge_end", charge_end), ("sink", sink), ("rise", rise),
         ("summon", summon), ("roar", roar), ("stagger", stagger), ("death", death)]


def build():
    K.setup(W_, H_)
    anims_used = [a for a in ANIMS if ONLY is None or a[0] in ONLY]
    meta = None
    for p2, name in ((False, "warden"), (True, "warden_p2")):
        if p2 and "--p1only" in sys.argv:
            break
        anims, infos = render_anims(LAYERS, lambda p, k, s, p2=p2: draw(p, k, s, p2), anims_used, sway_key="hip", loops=("idle", "walk", "charge"))
        if not p2 and ONLY is None:
            def hs(tag, ks, key="hit_staff", x_min=None, floor=False, pad=1):
                pts = set()
                for k in ks:
                    pts |= infos[tag][k].get(key, set())
                r = K.bbox(pts, pad)
                if x_min is not None and r[0] < x_min:
                    r[2] -= x_min - r[0]; r[0] = x_min
                if floor:
                    r[3] = H_ - r[1]
                return r
            antr = lambda tag, ks: hs(tag, ks, key="ant", x_min=118)
            meta = {"native": 1, "frame": [W_, H_], "anchor": [112, 176],
                    "hurtbox": [94, 60, 36, 116],
                    "attacks": {"sweep": {"active": [5, 6], "hit": hs("sweep", [5, 6], x_min=112, floor=True)},
                                "thrust": {"active": [5, 6], "hit": hs("thrust", [5, 6], x_min=120, floor=True)},
                                "erupt": {"active": [6, 6], "hit": hs("erupt", [6], x_min=112, floor=True)},
                                "charge": {"active": [0, 3], "hit": (lambda r: [r[0], r[1], r[2], H_ - r[1]])(antr("charge", [0, 1, 2, 3]))},
                                "rise": {"active": [5, 6], "hit": hs("rise", [5, 6], x_min=100)}},
                    "spawn": {"erupt": {"frame": 6, "at": spawn_pt(infos["erupt"][6]["butt"])},
                              "volley": {"frame": 6, "at": spawn_pt(infos["volley"][6]["bhand"])},
                              "summon": {"frame": 6, "at": spawn_pt(infos["summon"][6]["tip"])}},
                    "telegraph": {"sweep": {"frame": 4, "at": spawn_pt(infos["sweep"][4]["tip"])},
                                  "thrust": {"frame": 4, "at": spawn_pt(infos["thrust"][4]["tip"])},
                                  "erupt": {"frame": 5, "at": spawn_pt(infos["erupt"][5]["tip"])},
                                  "volley": {"frame": 4, "at": spawn_pt(infos["volley"][4]["bhand"])},
                                  "charge_prep": {"frame": 5, "at": spawn_pt(infos["charge_prep"][5]["eye"])},
                                  "rise": {"frame": 4, "at": spawn_pt(infos["rise"][4]["tip"])},
                                  "summon": {"frame": 5, "at": spawn_pt(infos["summon"][5]["tip"])}},
                    "points": {tag: [{"eye": spawn_pt(i["eye"]), "tip": spawn_pt(i["tip"]), "heart": spawn_pt(i["heart"])} for i in infos[tag]] for tag, _ in ANIMS}}
        tags, flats = K.export(name, LAYERS, anims, meta if not p2 else None, build=BUILD)
        contact(name, tags, flats, per_row=14, scale=2)
        print("built", name)


if __name__ == "__main__":
    build()
