#!/usr/bin/env python3
"""Thornveil Wood enemies (agent T): tv_husk, tv_hound, tv_wisp  (+ meta, previews, hitbox previews).

    python3 art/gen_thornveil_enemies.py                 build all (Aseprite)
    python3 art/gen_thornveil_enemies.py --preview       previews + meta only
    python3 art/gen_thornveil_enemies.py --only husk     one creature

    tv_husk   48x48  antlered husk: a gaunt hollow with a small deer skull for a head, bark-cloth rags, a bone sickle
    tv_hound  56x32  thorn-hound: a lean wolf woven of bramble vines around a pale canine skull, green eye-light
    tv_wisp   40x40  spore-wisp: a floating fawn skull wreathed in moss and spore sacs, green light in its sockets
All face RIGHT, feet on the bottom row (the wisp floats: anchor = body centre). Method: enemy_kit.py + thornveil_ckit.py.
"""
import math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import thornveil_ckit as C  # noqa: E402  (registers the ramps)
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, poly_mask, n_plate, n_dome, n_capsule, dirv  # noqa: E402
from thornveil_ckit import mk, rot, madd, curve, chain, taper, deer_skull, antler, ribbon_px, moss_drape, glow_dots, render_anims, hit_rect, hurtbox, collapse, export, spawn_pt, contact  # noqa: E402

ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None


# =========================================================================== 1. ANTLERED HUSK  (48x48)
HUSK_L = ["BackArm", "BackLeg", "Cloak", "FrontLeg", "Body", "Antlers", "Head", "FrontArm", "Weapon", "FX"]
FL = 47
H_NEU = dict(hip=(23.0, 30.0), ch=(26.0, 20.5), hd=(31.0, 15.0), ha=14.0, bf=(19.0, FL), ff=(28.5, FL), bl=0.0, fl=0.0,
             fh=(30.5, 30.5), bh=(20.5, 30.5), sk=95.0, eye=1, smear=None, ant=0.0, wind=0.0, lean=0.0, dead=False)
HP = mk(H_NEU)


def sickle_px(grip, ang):
    """A crooked bone sickle: short wooden haft + a curved antler blade. Returns ({px: col}, blade set, tip)."""
    out, blade = {}, set()
    d = dirv(ang)
    pv = (-d[1], d[0])
    for i in range(7):
        q = ip(madd(grip, (d, i - 1.5)))
        out[q] = "E3" if i % 3 else "E2"
    base = madd(grip, (d, 5.0))
    pts = []
    for i in range(11):
        t = i / 10
        a = ang - 90 * 0.0 + 160 * t
        p = madd(base, (dirv(ang - 70 + 150 * t), 4.2 + 1.4 * math.sin(t * math.pi)))
        pts.append(p)
    for i, q in enumerate(dict.fromkeys(polyline(pts))):
        out[q] = "J4" if i < 6 else "J3"
        blade.add(q)
    inner = [madd(p, (sub(base, p), 0.18)) for p in pts[2:9]]
    for q in polyline(inner):
        out.setdefault(q, "J2")
        blade.add(q)
    tip = ip(pts[-1])
    out[tip] = "J5"
    return out, blade, pts[-1]


def draw_husk(p, fi, sw):
    Ls = {n: Layer(n) for n in HUSK_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    hip, ch, hd = p["hip"], p["ch"], p["hd"]
    # ---- legs (thin, bark-wrapped, backward-knee'd like a deer's hind leg)
    for L, foot, lift, bias in ((Ls["BackLeg"], p["bf"], p["bl"], -2), (Ls["FrontLeg"], p["ff"], p["fl"], 0)):
        f = (foot[0], foot[1] - lift)
        h0 = madd(hip, ((1, 0), 1.0 if bias == 0 else -1.0))
        kn = ik(h0, (f[0] - 1.0, f[1] - 4.5), 8.5, 6.5, (1, 0.2))
        hock = (f[0] - 1.0, f[1] - 4.5)
        chain(L, [h0, kn, hock, (f[0], f[1] - 0.8)], [1.9, 1.15, 0.9, 0.8], "E", bias)
        L.paint(n_dome((f[0] + 0.8, f[1] - 0.6), 1.7, 0.9, tilt=(0, -0.3)), "E", bias, ao=0)   # split hoof
        L.fixed({ip((f[0] + 2.2, f[1] - 0.2)): "J2" if bias == 0 else "J1"})
    # ---- torso: bent spine, ribcage under the rags
    Bd = Ls["Body"]
    mid = madd(lerp(hip, ch, 0.5), ((-1, 0), 1.4 + p["lean"]))
    sp = curve([hip, mid, ch], 3)
    chain(Bd, sp, taper(len(sp), 2.6, 3.3), "E", 0)
    for i in range(3):   # ribs
        c = lerp(mid, ch, 0.2 + i * 0.3)
        Bd.decal([q for q in line(madd(c, ((1, 0), -2.0)), madd(c, ((1, 0), 2.2), ((0, 1), 1.0))) if q in Bd.px], ("E", 1))
    # neck
    nape = madd(hd, ((-1, 0), 2.2), ((0, 1), 0.8))
    chain(Bd, curve([ch, madd(lerp(ch, nape, 0.5), ((0, -1), 1.0)), nape], 2), [1.7, 1.5, 1.4, 1.3, 1.2], "E", 0)
    # ---- the cloak of bark-cloth rags over the back, ragged hem, moss clots
    Cl = Ls["Cloak"]
    s = sw * 0.6 + p["wind"]
    back = madd(ch, ((-1, 0), 3.0))
    hem_y = hip[1] + 9.5
    poly = [madd(ch, ((0, -1), 2.2)), madd(ch, ((1, 0), 2.0)), (hip[0] + 3.0 + s * 0.3, hip[1] + 3),
            (hip[0] + 2.0 + s, hem_y), (hip[0] - 0.5 + s, hem_y - 2.2), (hip[0] - 2.5 + s * 1.2, hem_y + 1.0),
            (hip[0] - 4.8 + s * 1.3, hem_y - 1.6), (hip[0] - 6.5 + s * 1.5, hem_y + 0.5), (back[0] - 3.0 + s, hip[1] - 2),
            (back[0] - 1.0, ch[1] + 1.0)]
    cm = poly_mask(poly)
    Cl.paint(n_plate(cm, 2.2, (-0.15, -0.1), 1.0, fold=lambda x, y: (0.35 * math.sin(x * 1.3 + y * 0.2), 0)), "X", 0)
    for q in cm:
        if hash01(q[0] // 2, q[1] // 2, 7) < 0.12:
            Cl.decal([q], ("H", 3 if hash01(*q, 3) < 0.5 else 2))
    # ---- head + antlers
    hk = deer_skull(Ls["Head"], hd, p["ha"], 0.78, eye=p["eye"])
    info["eye"] = hk["eye"]
    aa = p["ant"]
    antler(Ls["Antlers"], hk["ab2"], -118 + p["ha"] * 0.6 + aa, 0.6, "J", -1, tines=1, spread=0.8, w=0.7)
    antler(Ls["Antlers"], hk["ab"], -86 + p["ha"] * 0.6 + aa, 0.7, "J", 0, tines=2, spread=0.9, w=0.75)
    info["hit"] |= set(Ls["Antlers"].px) | set(Ls["Head"].px) if p.get("ramhit") else set()
    # ---- arms
    sh = madd(ch, ((1, 0), 0.4), ((0, 1), 0.8))
    for L, hand, bias, pref in ((Ls["BackArm"], p["bh"], -2, (-1, 0.6)), (Ls["FrontArm"], p["fh"], 0, (-1, 0.4))):
        s0 = madd(sh, ((-1, 0), 1.2 if bias else 0))
        el = ik(s0, hand, 7.8, 8.2, pref)
        chain(L, [s0, el, hand], [1.25, 0.95, 0.8], "E", bias)
        L.paint(n_dome(hand, 1.2, 1.2), "E", bias, ao=0)
    # rags hanging from the front forearm
    Ls["FrontArm"].fixed({q: "X3" if i % 2 else "X2" for i, q in enumerate(polyline([madd(p["fh"], ((-1, 0), 3), ((0, -1), 2)), madd(p["fh"], ((-1, 0), 3.5 + s * 0.4), ((0, 1), 3))]))})
    # ---- sickle
    px, blade, tip = sickle_px(p["fh"], p["sk"])
    Ls["Weapon"].fixed(px)
    info["blade"] = blade
    info["tip"] = tip
    if p["smear"]:
        g0, a0 = p["smear"]
        hot = K.swept(FX, g0, a0, p["fh"], p["sk"], 4.0, 10.5, hw=1.0, pal="bone", start=0.1)
        info["hit"] |= hot | blade
    # pale ribbon tied to an antler
    FX.put([], "N4")
    ab = hk["ab"]
    for q, c in ribbon_px((ab[0] - 2.0, ab[1] - 4.0), fi, 1.3, L=7, sway=-0.3 + s * 0.2).items():
        FX.put([q], c)
    # moss clots on the shoulders
    moss_drape(Cl, [madd(ch, ((-1, 0), 2.0)), madd(ch, ((-1, 0), 4.0), ((0, 1), 2)), (hip[0] - 3.0, hip[1] + 1)], fi, 5, n=3, maxlen=3)
    for L in (Bd, Ls["Head"], Cl):
        C.rim(L, {"E", "X", "J"}, 4)
    return Ls, info


def h_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 0.8, 0.4)[i]
        fr.append((200, HP(ch=(26.0, 20.5 + b * 0.6), hd=(31.0, 15.0 + b * 0.8), fh=(30.5, 30.5 + b * 0.5), bh=(20.5, 30.8 + b * 0.4),
                           sk=95 + b * 3, wind=b * 0.4)))
    return fr


def h_walk():
    fr = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        bob = abs(math.sin(ph)) * 0.8
        fx = 24 + 5.0 * math.cos(ph)
        bx = 24 - 5.0 * math.cos(ph)
        fr.append((130, HP(hip=(23.5, 30.0 - bob), ch=(26.8, 20.8 - bob), hd=(31.8, 15.4 - bob), bf=(bx, FL), ff=(fx, FL),
                           bl=max(0, 2.0 * math.sin(ph)), fl=max(0, -2.0 * math.sin(ph)),
                           fh=(29.5 + 2.5 * math.cos(ph + math.pi), 30.5 - bob), bh=(21.0 + 2.5 * math.cos(ph), 30.5 - bob),
                           sk=100 + 8 * math.cos(ph), wind=-0.6)))
    return fr


def h_slash():
    up = dict(fh=(20.5, 10.5), sk=-120.0, bh=(29.0, 26.0), ch=(24.8, 20.0), hd=(29.6, 14.4), ha=4.0, hip=(22.5, 30.2), ff=(29.5, FL))
    return [
        (120, HP(fh=(26.0, 24.0), sk=-20.0, ch=(25.5, 20.5), hd=(30.5, 15.0), ha=8.0)),
        (130, HP(fh=(22.0, 15.0), sk=-90.0, bh=(27.0, 28.0), ch=(25.0, 20.2), hd=(29.8, 14.6), ha=4.0)),
        (140, HP(**up)),
        (220, HP(**dict(up, eye=2))),                                            # hold: telegraph glint
        (70, HP(fh=(36.5, 24.0), sk=40.0, bh=(19.0, 29.0), ch=(28.0, 21.5), hd=(33.2, 16.8), ha=24.0, hip=(24.5, 30.5),
                ff=(32.0, FL), smear=((20.5, 10.5), -120.0), eye=2, wind=-1.5)),
        (80, HP(fh=(35.5, 31.0), sk=80.0, bh=(19.0, 29.5), ch=(28.2, 22.0), hd=(33.4, 17.5), ha=28.0, hip=(24.6, 30.8),
                ff=(32.0, FL), smear=((36.5, 24.0), 40.0), eye=2, wind=-1.0)),
        (160, HP(fh=(33.5, 32.0), sk=95.0, ch=(27.5, 21.5), hd=(32.5, 16.5), ha=24.0, hip=(24.0, 30.4), ff=(31.0, FL))),
        (160, HP(fh=(31.5, 31.0), sk=95.0, ch=(26.5, 21.0), hd=(31.5, 15.5), ha=16.0, hip=(23.4, 30.2), ff=(29.5, FL))),
    ]


def h_ram():
    low = dict(hip=(21.5, 31.0), ch=(26.5, 24.5), hd=(32.5, 24.0), ha=62.0, ant=18.0, fh=(28.5, 33.0), bh=(22.0, 33.0),
               sk=110.0, bf=(16.5, FL), ff=(29.0, FL))
    run = dict(hip=(23.0, 30.5), ch=(29.0, 25.0), hd=(35.5, 24.5), ha=60.0, ant=18.0, fh=(30.0, 33.0), bh=(21.0, 30.0), sk=140.0)
    return [
        (120, HP(ch=(26.0, 22.0), hd=(31.8, 18.0), ha=34.0, ant=8.0)),
        (140, HP(**low)),
        (150, HP(**dict(low, bl=2.0))),
        (240, HP(**dict(low, eye=2, bf=(16.5, FL), bl=0.0))),                    # paws the ground: telegraph
        (80, HP(**dict(run, bf=(14.0, FL), ff=(33.0, FL), fl=2.0, eye=2, wind=-2))),
        (70, HP(**dict(run, bf=(18.0, FL), ff=(34.5, FL), bl=2.5, eye=2, ramhit=True, wind=-2.5))),
        (70, HP(**dict(run, hip=(24.0, 30.0), ch=(30.0, 24.5), hd=(36.5, 24.0), bf=(20.0, FL), ff=(34.0, FL), eye=2, ramhit=True, wind=-2.5))),
        (80, HP(**dict(run, hip=(24.0, 30.0), ch=(30.0, 24.5), hd=(36.5, 24.0), bf=(16.0, FL), ff=(35.0, FL), fl=1.5, eye=2, ramhit=True, wind=-2))),
        (160, HP(ch=(27.5, 22.5), hd=(32.8, 19.0), ha=36.0, ant=8.0, ff=(31.0, FL), hip=(23.5, 30.5))),
        (160, HP(ch=(26.5, 21.0), hd=(31.5, 16.0), ha=20.0, ant=2.0)),
    ]


def h_hurt():
    return [(90, HP(ch=(24.0, 21.0), hd=(28.0, 14.5), ha=-12.0, fh=(27.0, 28.0), sk=70.0, hip=(22.0, 30.2), eye=0, wind=1.5)),
            (140, HP(ch=(25.0, 20.8), hd=(29.8, 14.8), ha=2.0, fh=(29.0, 30.0), hip=(22.6, 30.0), wind=0.8))]


def h_death():
    lie = dict(hip=(21.0, 41.0), ch=(29.0, 41.5), hd=(35.0, 42.0), ha=10.0, bf=(12.0, FL), ff=(15.0, FL), fh=(34.0, 45.0),
               bh=(26.0, 45.0), sk=10.0, eye=0)
    names = ["BackArm", "BackLeg", "Cloak", "FrontLeg", "Body", "Antlers", "Head", "FrontArm", "Weapon"]
    return [
        (110, HP(ch=(23.5, 21.5), hd=(27.0, 15.5), ha=-20.0, fh=(26.0, 28.0), sk=40.0, eye=0, wind=2)),
        (130, HP(hip=(22.0, 34.0), ch=(25.0, 27.0), hd=(29.0, 22.0), ha=30.0, fh=(28.5, 36.0), bh=(21.0, 38.0), sk=80.0,
                 bf=(18.0, FL), ff=(28.0, FL), eye=0)),
        (140, HP(**lie)),
        (150, HP(**lie, post=collapse(names, 0.75, 0.12, seed=2))),
        (160, HP(**lie, post=collapse(names, 0.45, 0.28, seed=2))),
        (500, HP(**lie, post=collapse(names, 0.18, 0.42, seed=2))),
    ]


def build_husk():
    K.setup(48, 48)
    anims, infos = render_anims(HUSK_L, draw_husk, [("idle", h_idle), ("walk", h_walk), ("slash", h_slash), ("ram", h_ram),
                                                    ("hurt", h_hurt), ("death", h_death)], sway_key="ch")
    meta = {"native": 1, "frame": [48, 48], "anchor": [24, 48],
            "hurtbox": hurtbox(anims, ["Body", "Cloak", "Head"], inset=(1, 1, 1)),
            "attacks": {"slash": {"active": [4, 5], "hit": hit_rect(infos, "slash", [4, 5], x_min=24)},
                        "ram": {"active": [5, 7], "hit": hit_rect(infos, "ram", [5, 6, 7], x_min=26, pad=1)}},
            "telegraph": {"slash": {"frame": 3, "at": spawn_pt(infos["slash"][3]["tip"])},
                          "ram": {"frame": 3, "at": spawn_pt(infos["ram"][3]["eye"])}}}
    tags, flats = export("tv_husk", HUSK_L, anims, meta)
    contact("tv_husk", tags, flats)


# =========================================================================== 2. THORN-HOUND  (56x32)
HOUND_L = ["FarLegs", "Tail", "Body", "NearHind", "NearFront", "Head", "FX"]
FLh = 31
D_NEU = dict(P=(17.5, 15.2), S=(35.3, 15.6), Hh=(44.7, 11.4), ha=16.0, arch=0.0, hn=(15.5, FLh, -2.4, -5.2), hf=(18.5, FLh, -2.4, -5.2),
             fn=(36.2, FLh, -0.3, -3.0), ff=(33.2, FLh, -0.3, -3.0), ta=0.0, wave=0.0, jaw=0.0, eye=1, lines=None, wind=0.0, bite=False)
DP = mk(D_NEU)


def vine_leg(L, hip, paw, front, bias):
    px, py, ox, oy = paw
    foot = (px, py - 0.9)
    mid = (px + ox, py + oy)
    kn = ik(hip, mid, 5.6 if front else 6.2, 5.4 if front else 6.0, (-1, 0.15) if front else (1, 0.25))
    chain(L, [hip, kn, mid, foot], [1.9 if not front else 1.7, 1.0, 0.8, 0.75], "U", bias)
    L.paint(n_dome((foot[0] + 1.0, foot[1] + 0.3), 1.7, 0.8, tilt=(0, -0.2)), "U", bias, ao=0)
    t = ip((foot[0] + 2.3, foot[1] + 0.5))
    L.fixed({t: "J3" if bias >= 0 else "J2"})
    # thorns on the shin
    q = ip(lerp(kn, mid, 0.5))
    L.fixed({(q[0] - 1, q[1]): "U5" if bias >= 0 else "U3"})
    return kn, mid


def draw_hound(p, fi, sw):
    Ls = {n: Layer(n) for n in HOUND_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    P, S, Hh, ha = p["P"], p["S"], p["Hh"], p["ha"]
    ax_ = sub(S, P)
    ln = math.hypot(*ax_)
    fwd = (ax_[0] / ln, ax_[1] / ln)
    up = (fwd[1], -fwd[0])
    dn = (-up[0], -up[1])
    vine_leg(Ls["FarLegs"], madd(P, (fwd, 1.4), (dn, 1.2)), p["hf"], False, -2)
    vine_leg(Ls["FarLegs"], madd(S, (fwd, -0.8), (dn, 2.6)), p["ff"], True, -2)
    # tail: a trailing whip of bramble, thorn-tipped
    ta, wv = p["ta"], p["wave"]
    t0 = madd(P, (fwd, -2.6), (up, 1.2))
    t1 = add(t0, rot((-4.5, 1.2 + 0.3 * sw), ta))
    t2 = add(t1, rot((-4.2, 1.2 + wv), ta))
    t3 = add(t2, rot((-3.4, -0.2 + wv * 1.5), ta))
    tp = curve([t0, t1, t2, t3], 3)
    chain(Ls["Tail"], tp, taper(len(tp), 1.4, 0.5), "U", -1)
    for i in range(2, len(tp), 3):
        q = ip(tp[i])
        Ls["Tail"].fixed({(q[0], q[1] - 2): "U5", (q[0] - 1, q[1] - 1): "U4"})
    # body: woven vines around a hollow ribcage
    Bd = Ls["Body"]
    c0 = madd(P, (fwd, -1.6), (up, 0.2))
    c1 = madd(lerp(P, S, 0.32), (up, 0.8 + p["arch"]))
    c2 = madd(lerp(P, S, 0.66), (dn, 0.6), (up, p["arch"] * 0.4))
    c3 = madd(S, (dn, 1.4))
    c4 = madd(S, (fwd, 2.4), (dn, 0.4))
    cp = curve([c0, c1, c2, c3, c4], 4)
    keys = [(0, 2.8), (0.25, 1.9), (0.52, 3.2), (0.76, 3.7), (1.0, 2.5)]
    rr = []
    for i in range(len(cp)):
        t = i / (len(cp) - 1)
        for (ta_, ra), (tb, rb) in zip(keys, keys[1:]):
            if ta_ <= t <= tb:
                u = (t - ta_) / (tb - ta_)
                rr.append(ra + (rb - ra) * u * u * (3 - 2 * u))
                break
    bm = chain(Bd, cp, rr, "U", 0)
    # woven strands: diagonal dark grooves + a few pale thorn barbs along the spine
    for q in list(bm):
        if (q[0] + q[1] * 2 + fi) % 6 == 0:
            Bd.decal([q], ("U", 1))
    for i in range(8):
        t = 0.08 + i * 0.11
        c = lerp(P, S, t)
        topc = madd(c, (up, 3.0 + p["arch"] * (1 - abs(t - 0.4))))
        q = ip(topc)
        while q in bm:
            q = (q[0], q[1] - 1)
        Bd.fixed({q: "U5" if i % 2 else "U4", (q[0] - 1, q[1] - 1): "J3" if i % 2 else "U5"})
    # the hollow ribs glow faintly (a spirit ember caught in the vines)
    cc = ip(madd(lerp(P, S, 0.62), (dn, 0.2)))
    Bd.fixed({cc: "S3", (cc[0] + 1, cc[1]): "S2", (cc[0], cc[1] + 1): "S1"})
    info["hit"] |= set(bm)
    Nh = Ls["NearHind"]
    hip = madd(P, (fwd, 0.4), (dn, 1.0))
    Nh.paint(n_dome(madd(hip, (fwd, -0.3), (up, 0.8)), 2.6, 3.2, tilt=(-0.1, -0.1)), "U", 0)
    vine_leg(Nh, hip, p["hn"], False, 0)
    Nf = Ls["NearFront"]
    sho = madd(S, (fwd, -0.4), (dn, 2.4))
    Nf.paint(n_dome(madd(sho, (up, 1.6), (fwd, -0.4)), 2.0, 2.9, tilt=(-0.1, -0.2)), "U", 0)
    vine_leg(Nf, sho, p["fn"], True, 0)
    info["hit"] |= set(Nf.px)
    # neck + pale canine skull
    Hd = Ls["Head"]
    G = lambda x, y: add(Hh, rot((x, y), ha))
    hb = G(-3.2, 0.6)
    n0 = madd(S, (fwd, 1.2), (up, 1.2))
    n1 = madd(lerp(n0, hb, 0.5), (up, 1.0))
    chain(Hd, curve([n0, n1, hb], 2), [2.6, 2.3, 2.0, 1.8, 1.7], "U", 0)
    hinge = (-0.6, 1.4)
    ja = p["jaw"] * 40.0
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), ja)))
    jaw = [J(-1.2, 1.1), J(8.8, 1.3), J(8.4, 2.1), J(2.0, 2.9), J(-1.6, 2.6)]
    if p["jaw"] > 0.15:
        Hd.fixed({q: "U0" for q in poly_mask([G(-1.0, 1.2), G(9.6, 1.2), J(8.8, 1.3)])})
    Hd.paint(n_plate(poly_mask(jaw), 0.8, (0.0, 0.3)), "J", -1)
    skull = [G(-3.4, -1.4), G(-1.0, -2.5), G(2.0, -2.2), G(3.4, -1.1), G(9.6, 0.0), G(10.6, 0.6), G(10.0, 1.3), G(2.4, 1.3),
             G(-1.4, 2.3), G(-3.5, 1.1)]
    sm = poly_mask(skull)
    Hd.paint(n_plate(sm, 1.2, (-0.15, -0.3), 1.1), "J", 0)
    Hd.decal([q for q in line(G(-1.0, 1.8), G(2.2, 1.1)) if q in sm], ("J", 1))
    teeth = {ip(G(7.2, 1.6)): "J5"} if p["jaw"] <= 0.15 else {ip(G(x, 1.7)): "J5" for x in (3.4, 5.8, 8.0)}
    Hd.fixed(teeth)
    # thorn crown over the skull (bramble ears)
    for (bx, L_, a) in ((-2.4, 5.0, -150), (-0.4, 4.0, -125)):
        b = G(bx, -1.8)
        tip = madd(b, (dirv(a + ha), L_))
        Hd.fixed({q: "U4" if i < 3 else "U5" for i, q in enumerate(line(b, tip))})
    e = ip(G(1.2, -0.6))
    Hd.fixed({e: "S4" if p["eye"] >= 2 else "S3", (e[0] + 1, e[1]): "S2", (e[0], e[1] - 1): "U0"})
    for L in (Bd, Hd, Nh, Nf):
        C.rim(L, {"U"}, 4)
    info["hit"] |= set(Hd.px)
    info["eye"] = e
    if p["lines"]:
        x0, x1, ys = p["lines"]
        for i, y in enumerate(ys):
            a = x0 + (i * 3) % 4
            b = x1 - (i * 5) % 6
            for x in range(a, b):
                FX.put([(x, y)], "S2" if x > (a + b) / 2 else "S1")
    if p["bite"]:
        jt = ip(G(10.5, 1.8))
        for d in ((0, 0), (1, 0), (-1, 1), (1, -1)):
            FX.put([(jt[0] + d[0], jt[1] + d[1])], "J5" if d == (0, 0) else "J4")
    return Ls, info


def d_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.4, 0.7, 0.3)[i]
        fr.append((190, DP(S=(35.0, 15.5 + b * 0.5), P=(17.0, 15.0 + b * 0.2), Hh=(44.5 + b * 0.2, 11.0 + b * 0.8),
                           ha=16 + b * 3, ta=-4 + 8 * math.sin(i * math.pi / 2), wave=math.sin(i * math.pi / 2 + 1))))
    return fr


def d_run():
    L = [((15.0, 13.5), (37.0, 14.0), -0.8, (47.5, 10.5), 8, (4.5, 25.0, 4.5, -1.8), (6.5, 26.5, 4.2, -2.2), (50.0, 24.5, -3.6, 0.2), (47.5, 26.5, -3.4, -0.6)),
         ((16.0, 14.5), (37.0, 15.5), 0.0, (46.5, 11.5), 12, (10.0, 24.0, 3.6, -3.0), (12.0, 25.5, 3.2, -3.2), (43.5, FLh, -1.5, -3.0), (47.0, 27.0, -3.0, -1.5)),
         ((18.0, 15.0), (36.0, 16.0), 1.2, (45.0, 12.5), 16, (20.0, 25.0, -1.0, -4.2), (22.0, 26.5, -1.2, -4.0), (35.0, FLh, 1.2, -3.0), (39.5, FLh, -0.5, -3.0)),
         ((19.0, 13.5), (35.0, 14.5), 2.6, (44.5, 11.5), 14, (29.0, 26.0, -3.0, -3.5), (31.0, 27.0, -3.0, -3.2), (27.0, 25.5, 3.0, -2.2), (29.0, 26.5, 2.8, -2.0)),
         ((19.0, 15.0), (36.0, 15.0), 1.5, (46.0, 11.5), 10, (26.0, FLh, -2.6, -4.6), (29.0, FLh, -2.6, -4.6), (41.0, 26.0, -2.2, -2.6), (38.0, 27.0, -1.5, -3.0)),
         ((17.0, 14.5), (37.0, 14.5), 0.0, (47.0, 11.0), 8, (11.0, FLh, -1.0, -5.0), (15.0, FLh, -1.8, -5.0), (47.0, 25.5, -3.4, -0.8), (44.0, 27.0, -3.0, -1.6))]
    return [(70, DP(P=P, S=S, arch=ar, Hh=Hh, ha=ha, hn=hn, hf=hf, fn=fn, ff=ff, ta=-14 + 10 * math.sin(i * 1.05),
                    wave=1.2 * math.sin(i * 1.05 + 1.5), wind=-2.0)) for i, (P, S, ar, Hh, ha, hn, hf, fn, ff) in enumerate(L)]


def d_pounce():
    return [
        (150, DP(P=(16.0, 16.5), S=(33.0, 18.0), arch=0.5, Hh=(40.5, 16.0), ha=10, eye=2, hn=(14.0, FLh, -2.2, -4.8), hf=(17.0, FLh, -2.2, -4.8),
                 fn=(36.0, FLh, 1.2, -2.8), ff=(33.5, FLh, 1.0, -2.8), ta=-6)),
        (300, DP(P=(14.5, 15.5), S=(31.0, 20.0), arch=1.5, Hh=(38.5, 19.0), ha=4, eye=2, jaw=0.25, hn=(12.5, FLh, -2.0, -5.0), hf=(16.0, FLh, -2.0, -5.0),
                 fn=(35.0, FLh, 2.2, -2.2), ff=(32.5, FLh, 2.0, -2.2), ta=-24, wave=1.5)),
        (160, DP(P=(14.0, 17.5), S=(30.5, 19.5), arch=2.0, Hh=(38.0, 17.5), ha=0, eye=2, jaw=0.3, hn=(13.5, FLh, -2.8, -3.6), hf=(16.5, FLh, -2.8, -3.6),
                 fn=(34.5, FLh, 1.8, -2.4), ff=(32.0, FLh, 1.8, -2.4), ta=-30, wave=-1.0)),
        (80, DP(P=(18.0, 15.0), S=(35.5, 10.5), arch=-1.0, Hh=(44.5, 7.0), ha=-8, eye=2, jaw=0.6, hn=(9.0, FLh, 3.0, -4.0), hf=(11.5, FLh, 2.6, -4.2),
                fn=(43.0, 17.0, -3.0, -0.5), ff=(41.0, 19.0, -3.0, -1.0), ta=10, wave=1.0, wind=3)),
        (90, DP(P=(20.0, 12.0), S=(39.0, 12.5), arch=-1.2, Hh=(48.5, 13.5), ha=18, eye=2, jaw=1.0, bite=True, hn=(7.0, 17.5, 4.6, -1.2), hf=(9.0, 19.5, 4.4, -1.6),
                fn=(52.0, 26.5, -3.2, -1.8), ff=(49.5, 28.5, -3.0, -2.2), ta=18, wave=0.5, wind=4, lines=(0, 16, (8, 11, 14, 17)))),
        (100, DP(P=(21.0, 15.0), S=(38.5, 17.0), arch=0.4, Hh=(47.5, 18.5), ha=26, eye=2, jaw=0.05, hn=(21.0, 26.0, -1.2, -4.0), hf=(23.5, 27.0, -1.2, -4.0),
                 fn=(46.5, FLh, -1.5, -3.0), ff=(44.0, FLh, -1.2, -3.0), ta=8, wave=-1.0)),
        (150, DP(P=(19.5, 16.0), S=(36.5, 17.5), arch=1.0, Hh=(45.5, 15.5), ha=20, hn=(19.0, FLh, -2.4, -5.0), hf=(22.0, FLh, -2.4, -5.0),
                 fn=(41.0, FLh, -0.2, -3.0), ff=(38.5, FLh, 0.0, -3.0), ta=0, wave=0.5)),
        (190, DP(P=(17.5, 15.2), S=(35.3, 15.6), Hh=(44.7, 11.4), ha=17, hn=(15.5, FLh, -2.4, -5.2), hf=(18.5, FLh, -2.4, -5.2),
                 fn=(36.2, FLh, -0.3, -3.0), ff=(33.2, FLh, -0.3, -3.0))),
    ]


def d_hurt():
    return [(90, DP(P=(15.0, 15.0), S=(32.0, 14.0), arch=1.0, Hh=(40.0, 8.0), ha=-26, jaw=0.6, eye=2, hn=(13.0, FLh, -2.2, -5.2), hf=(16.5, FLh, -2.2, -5.2),
                    fn=(34.0, 28.5, -1.0, -2.8), ff=(31.0, FLh, -0.3, -3.0), ta=-20)),
            (140, DP(P=(16.0, 15.0), S=(33.8, 15.0), arch=0.5, Hh=(42.5, 9.8), ha=2, jaw=0.2, hn=(14.0, FLh, -2.4, -5.2), hf=(17.5, FLh, -2.4, -5.2),
                     fn=(35.0, FLh, -0.3, -3.0), ff=(32.0, FLh, -0.3, -3.0), ta=-8))]


def d_death():
    lie = dict(P=(17.0, 25.0), S=(34.0, 26.0), arch=0.5, Hh=(43.0, 27.0), ha=12, eye=0, hn=(22.0, FLh, -3.5, -1.5), hf=(24.5, FLh, -3.5, -1.5),
               fn=(40.5, FLh, -3.2, -0.5), ff=(38.0, FLh, -3.0, -0.8), ta=20, wave=0.0)
    names = ["FarLegs", "Tail", "Body", "NearHind", "NearFront", "Head"]
    return [(100, DP(P=(15.0, 16.0), S=(31.0, 12.0), arch=0.5, Hh=(38.0, 6.5), ha=-36, jaw=0.8, eye=2, hn=(13.0, FLh, -2.2, -5.2), hf=(16.0, FLh, -2.2, -5.2),
                     fn=(35.0, 24.0, -1.5, -2.5), ff=(33.0, 26.0, -1.5, -2.5), ta=-30)),
            (130, DP(P=(16.0, 20.0), S=(33.0, 21.5), arch=1.0, Hh=(41.5, 22.0), ha=30, jaw=0.4, eye=1, hn=(12.0, FLh, -3.0, -3.5), hf=(19.0, FLh, -3.0, -3.5),
                     fn=(38.0, FLh, -1.5, -2.5), ff=(34.5, FLh, -1.0, -2.5), ta=0)),
            (140, DP(**lie)),
            (140, DP(**lie, post=collapse(names, 0.6, 0.12, seed=4))),
            (160, DP(**lie, post=collapse(names, 0.3, 0.25, seed=4))),
            (500, DP(**lie, post=collapse(names, 0.12, 0.35, seed=4)))]


def build_hound():
    K.setup(56, 32)
    anims, infos = render_anims(HOUND_L, draw_hound, [("idle", d_idle), ("run", d_run), ("pounce", d_pounce), ("hurt", d_hurt), ("death", d_death)],
                                sway_key="S", loops=("idle", "run"))
    meta = {"native": 1, "frame": [56, 32], "anchor": [26, 32],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(2, 2, 5)),
            "attacks": {"pounce": {"active": [3, 5], "hit": hit_rect(infos, "pounce", [4, 5], x_min=34)}},
            "telegraph": {"pounce": {"frame": 1, "at": spawn_pt(infos["pounce"][1]["eye"])}}}
    tags, flats = export("tv_hound", HOUND_L, anims, meta)
    contact("tv_hound", tags, flats)


# =========================================================================== 3. SPORE-WISP  (40x40, floats; anchor = centre)
WISP_L = ["Tendrils", "Moss", "Skull", "Sacs", "FX"]
W_NEU = dict(c=(20.0, 17.0), tilt=12.0, glow=1, open=0.0, puff=0, dip=0.0, wind=0.0, scatter=0.0)
WP = mk(W_NEU)


def draw_wisp(p, fi, sw):
    Ls = {n: Layer(n) for n in WISP_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {}
    c = p["c"]
    # hanging root tendrils (drift behind the motion)
    for k in range(4):
        x0 = c[0] - 3.5 + k * 2.4
        pts = [(x0, c[1] + 3), (x0 + math.sin(fi * 0.9 + k) * 1.5 - sw * 0.5, c[1] + 8), (x0 + math.sin(fi * 0.9 + k + 1) * 2.5 - sw, c[1] + 13 + k % 2 * 2)]
        cp = curve(pts, 3)
        chain(Ls["Tendrils"], cp, taper(len(cp), 0.9, 0.5), "E", -1, ao=0)
        tip = ip(cp[-1])
        FX.put([tip], "S2" if (k + fi) % 3 else "S3")
    # moss wreath around the skull
    for k in range(11):
        a = -0.35 + k / 10 * (math.pi + 0.7)          # a crescent of moss under and behind the skull
        q = (c[0] - 1.5 + math.cos(a) * 7.0, c[1] + 1.5 + math.sin(a) * 4.2)
        Ls["Moss"].paint(n_dome(q, 2.1, 1.8), "H", 0 if math.sin(a) > 0.3 else -1)
    # the fawn skull
    hk = deer_skull(Ls["Skull"], (c[0] - 3.0, c[1] - 1.5), p["tilt"], 1.05, eye=2 if p["glow"] >= 2 else 1, jaw=p["open"])
    info["eye"] = hk["eye"]
    # small nubs of first antlers
    for bx in (-4.0, -1.8):
        b = add(c, rot((bx, -4.2), p["tilt"]))
        Ls["Skull"].fixed({ip(b): "J3", ip((b[0] - 0.6, b[1] - 1.2)): "J4"})
    # spore sacs clustered under the wreath, pulsing
    for k, (dx, dy, r) in enumerate(((-5.0, 6.0, 1.8), (-1.0, 7.0, 2.3), (3.4, 6.2, 1.8))):
        pr = r * (1 + 0.12 * math.sin(fi * 1.6 + k) + 0.25 * p["puff"])
        Ls["Sacs"].paint(n_dome((c[0] + dx, c[1] + dy), pr, pr * 1.1), "H", 1)
        Ls["Sacs"].fixed({ip((c[0] + dx, c[1] + dy + pr * 0.4)): "S3" if (fi + k) % 2 else "S2"})
    # eye-light flare + spore halo
    e = hk["eye"]
    if p["glow"] >= 2:
        for d in ((1, 0), (-1, 0), (0, -1), (0, 1)):
            FX.put([(e[0] + d[0] * 2, e[1] + d[1] * 2)], "S3")
    glow_dots(FX, (c[0], c[1] + 2), 8 + p["puff"] * 3, 8 + p["puff"] * 4, fi, cols=("S3", "S2", "S4"))
    for L in (Ls["Skull"], Ls["Moss"]):
        C.rim(L, {"J", "H"}, 4)
    info["mouth"] = hk["snout"]
    return Ls, info


def w_fly():
    return [(110, WP(c=(20.0, 17.0 + 1.2 * math.sin(i / 6 * 2 * math.pi)), tilt=12 + 4 * math.sin(i / 6 * 2 * math.pi + 1))) for i in range(6)]


def w_cast():
    return [(120, WP(tilt=10, glow=1)), (120, WP(tilt=2, glow=2, puff=1, c=(19.0, 16.0))), (140, WP(tilt=-6, glow=2, puff=2, c=(18.5, 15.0))),
            (160, WP(tilt=-10, glow=2, puff=3, c=(18.0, 14.5), open=0.3)), (120, WP(tilt=-10, glow=2, puff=3, c=(18.0, 14.5), open=0.6)),
            (90, WP(tilt=22, glow=2, puff=1, c=(21.5, 17.5), open=1.0)), (140, WP(tilt=18, glow=1, c=(21.0, 17.5), open=0.4)),
            (140, WP(tilt=12, glow=1))]


def w_hurt():
    return [(90, WP(tilt=-20, c=(17.0, 15.0), glow=0)), (140, WP(tilt=0, c=(18.5, 16.0)))]


def w_death():
    names = ["Tendrils", "Moss", "Skull", "Sacs"]
    return [(100, WP(tilt=-30, c=(19.0, 16.0), glow=2, puff=3)), (120, WP(tilt=40, c=(20.0, 20.0), glow=0, puff=2)),
            (130, WP(tilt=70, c=(20.0, 25.0), glow=0, post=lambda im: K.ember_dissolve(im, 0.2, names, seed=5, rise=10, pal=("S4", "S3", "S2", "H3", "H2")))),
            (130, WP(tilt=90, c=(20.0, 29.0), glow=0, post=lambda im: K.ember_dissolve(im, 0.45, names, seed=5, rise=12, pal=("S4", "S3", "S2", "H3", "H2")))),
            (140, WP(tilt=100, c=(20.0, 31.0), glow=0, post=lambda im: K.ember_dissolve(im, 0.7, names, seed=5, rise=14, pal=("S4", "S3", "S2", "H3", "H2")))),
            (400, WP(tilt=100, c=(20.0, 32.0), glow=0, post=lambda im: K.ember_dissolve(im, 0.95, names, seed=5, rise=16, pal=("S4", "S3", "S2", "H3", "H2"))))]


def build_wisp():
    K.setup(40, 40)
    anims, infos = render_anims(WISP_L, draw_wisp, [("fly", w_fly), ("cast", w_cast), ("hurt", w_hurt), ("death", w_death)], sway_key="c", loops=("fly",))
    meta = {"native": 1, "frame": [40, 40], "anchor": [20, 20],
            "hurtbox": hurtbox(anims, ["Moss", "Skull"], inset=(0, 0, 0), floor=False),
            "attacks": {},
            "spawn": {"cast": {"frame": 5, "at": spawn_pt(infos["cast"][5]["mouth"])}},
            "telegraph": {"cast": {"frame": 2, "at": spawn_pt(infos["cast"][2]["eye"])}}}
    tags, flats = export("tv_wisp", WISP_L, anims, meta)
    contact("tv_wisp", tags, flats)


if __name__ == "__main__":
    for nm, fn in (("husk", build_husk), ("hound", build_hound), ("wisp", build_wisp)):
        if ONLY is None or nm in ONLY:
            fn()
            print("built", nm)
