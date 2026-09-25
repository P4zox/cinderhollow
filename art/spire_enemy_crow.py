"""sp_crow -- storm crow (40x32, floats: anchor = body centre [20,16]). See gen_spire_enemies.py."""
import math
import enemy_kit as K
from enemy_kit import Layer, FXLayer, Rig, ip, line, hash01, n_dome, n_plate, poly_mask, dirv
import spire_enemy_kit as S
from spire_enemy_kit import n_tube, curve, madd, mk

SPEC = dict(fly=6, perch=4, takeoff=4, dive=6, hurt=2, death=6)
LAYERS = ["WingFar", "Tail", "Body", "Head", "WingNear", "FX"]
NEU = dict(O=(20.0, 16.0), tilt=0.0, wing=-120.0, bend=0.0, chord=0.85, wlen=16.0, far=-16.0, tail=1.0,
           legs=None, head=(0.0, 0.0), hrot=0.0, gape=0.0, eye=2, streak=None, feathers=0.0, flash=False,
           wind=0.0, tuck=True)
CP = mk(NEU)
PERCH_FEET = 24


def wing_poly(sh, ang, L, chord, bend, splay=1.0):
    """Long slender crow wing from shoulder `sh` (model coords): leading edge + fingered primaries.
    ang = direction the wing points (deg, screen), bend = extra rotation accumulated towards the tip."""
    # integrate a bent spine
    spine, p = [], sh
    n = 16
    for i in range(n + 1):
        u = L * i / n
        a = ang + bend * (u / L) ** 1.5
        spine.append((u, p, dirv(a)))
        p = madd(p, (dirv(a), L / n))

    def at(u, v):
        i = min(n, max(0, int(round(u / L * n))))
        _, q, d = spine[i]
        nv = (-d[1], d[0])                        # +v = leading edge side (rot +90)
        return madd(q, (nv, v))
    c = chord
    lead = [at(0, 1.1), at(2.5, 1.3), at(5.0, 1.1), at(8.5, 0.7), at(L - 1.2, 0.3), at(L, -0.2)]
    # primaries: fingered trailing edge near the tip (splay spreads the fingers)
    f = splay
    trail = [at(L - 0.4, -0.8 * c), at(L - 2.0, -0.1 * c), at(L - 2.3, -2.0 * c * f), at(L - 3.9, -0.8 * c),
             at(L - 4.3, -2.9 * c * f), at(L - 6.0, -1.8 * c), at(L - 6.5, -3.4 * c * f), at(L - 8.2, -3.0 * c),
             at(5.0, -3.3 * c), at(2.4, -2.9 * c), at(0.2, -2.0 * c)]
    return lead + trail, at


def draw_wing(R, L, sh, ang, Ln, chord, bend, bias, fi, seed, splay=1.0):
    pts, at = wing_poly(sh, ang, Ln, chord, bend, splay)
    m = R.mask(pts)
    L.paint(n_plate(m, 1.1, (-0.1, -0.25), 1.0), "S", bias)
    # lighter covert band along the leading edge (the "arm"), darker feather partings towards the tip
    cov = set()
    for u in (0.8, 2.0, 3.2, 4.4, 5.6, 6.8):
        cov.add(R.pt(at(u, 0.5)))
    L.decal([q for q in cov if q in m], ("S", 4 if bias >= 0 else 3))
    for k, u in enumerate((Ln - 2.2, Ln - 4.2, Ln - 6.4)):
        seg = line(R.T(at(u, -0.4 * chord)), R.T(at(u - 1.6, -2.4 * chord)))
        L.decal([q for q in seg if q in m], ("S", 1))
    return m


def draw_crow(p, fi, sw):
    Ls = {n: Layer(n) for n in LAYERS if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    O = p["O"]
    R = Rig(p["tilt"], O)
    M = lambda x, y: (O[0] + x, O[1] + y)
    info = {"hit": set()}
    sh = M(0.4, -1.8)
    # ---- far wing (behind body, darker, slightly offset)
    if p["wing"] is not None:
        draw_wing(R, Ls["WingFar"], M(-0.4, -2.2), p["wing"] + p["far"], p["wlen"] * 0.92, p["chord"] * 0.9,
                  p["bend"], -2, fi, 5, splay=0.9)
    # ---- forked tail
    ts = p["tail"]
    tl = [M(-4.6, -1.0), M(-10.4, -1.6 - 0.8 * ts + sw * 0.2), M(-8.8, 0.3), M(-10.6, 2.0 + 1.2 * ts + sw * 0.2),
          M(-4.6, 1.4)]
    tm = R.mask(tl)
    Ls["Tail"].paint(n_plate(tm, 0.9, (-0.1, -0.2), 1.0), "S", -1)
    Ls["Tail"].decal([q for q in line(R.T(M(-5.0, 0.2)), R.T(M(-8.6, 0.3))) if q in tm], ("S", 1))
    # ---- body: sleek teardrop, deep chest, narrowing to the tail
    Bd = Ls["Body"]
    cp = curve([M(-6.0, 0.4), M(-2.4, 0.4), M(1.2, -0.2), M(3.6, -1.4)], 5)
    rr = [1.4 + (3.0 - 1.4) * min(1.0, i / (len(cp) * 0.55)) if i < len(cp) * 0.55 else
          3.0 - 0.9 * (i - len(cp) * 0.55) / (len(cp) * 0.45) for i in range(len(cp))]
    bm = Bd.paint(n_tube([R.T(q) for q in cp], rr, flat=0.9), "S", 0)
    # legs / feet
    if p["legs"]:
        for k, (hip, foot) in enumerate(p["legs"]):
            h_, f_ = R.T(M(*hip)), foot
            seg = line(h_, (f_[0], f_[1] - 1))
            Bd.fill(seg, "S3" if k else "S4", noout=True)
            fx_, fy_ = ip(f_)
            Bd.fill([(fx_ - 1, fy_), (fx_ + 1, fy_), (fx_ + 2, fy_)], "S3" if k else "S4", noout=True)
    elif p["tuck"]:
        q = R.pt(M(-1.0, 2.9))
        Bd.fill([q, (q[0] + 1, q[1])], "S2")
    info["hit"] |= set(bm)
    # ---- head: small, flat-crowned, heavy bone beak, shaggy throat
    Hd = Ls["Head"]
    hx, hy = p["head"]
    hr = p["hrot"]
    HC = M(5.4 + hx, -2.8 + hy)
    Hh = lambda x, y: madd(HC, (dirv(hr), x), (dirv(hr + 90), y))
    Hd.paint(n_tube([R.T(Hh(-2.6, 1.4)), R.T(Hh(-0.6, 0.2)), R.T(Hh(0.4, -0.2))], [2.2, 2.1, 2.0], flat=0.9), "S", 0)
    Hd.paint(n_dome(R.T(Hh(0.2, -0.2)), 2.3, 1.9, tilt=(-0.1, -0.2)), "S", 0, ao=0)
    throat = [Hh(-1.4, 1.2), Hh(1.2, 1.2), Hh(-0.4, 2.8), Hh(-1.2, 2.2), Hh(-2.0, 3.0)]
    Hd.paint(n_plate(R.mask(throat), 0.8, (0, 0.2)), "S", -1, ao=0)
    g = p["gape"]
    up = [Hh(1.4, -1.4), Hh(3.0, -1.2), Hh(6.4, 0.2), Hh(6.4, 0.8), Hh(2.8, 0.1 - g * 0.3), Hh(1.6, 0.2)]
    lo = [Hh(1.6, 0.3), Hh(2.8, 0.5 + g * 0.4), Hh(5.2, 1.0 + g * 1.2), Hh(2.6, 1.4 + g * 0.4), Hh(1.4, 1.2)]
    um = R.mask(up)
    lm = R.mask(lo)
    Hd.paint(n_plate(lm, 0.7, (0, 0.3)), "B", -1, ao=0)
    Hd.paint(n_plate(um, 0.8, (-0.2, -0.5)), "B", 0, ao=0)
    Hd.decal([q for q in um if hash01(*q, 3) < 0.25], ("B", 2))
    e = R.pt(Hh(0.8, -0.8))
    if p["eye"] > 0:
        Hd.fixed({e: "U4" if p["eye"] >= 2 else "U3"})
        if p["eye"] >= 3:
            FX.put([(e[0] + 1, e[1] - 1)], "U3")
    else:
        Hd.fixed({e: "S1"})
    info["hit"] |= set(Hd.px)
    info["beak"] = R.T(Hh(6.4, 0.5))
    info["eye"] = e
    # ---- near wing
    if p["wing"] is not None:
        draw_wing(R, Ls["WingNear"], sh, p["wing"], p["wlen"], p["chord"], p["bend"], 0, fi, 3)
    # ---- storm sheen along the top line (cold rim so the black bird separates from a night sky)
    for L_ in (Bd, Hd, Ls["WingNear"]):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "S"
                  and not isinstance(e_[3], str) and hash01(*q, 9) < 0.7], ("S", 4))
    # ---- fx
    if p["streak"]:
        ang, n = p["streak"]
        d = dirv(ang)
        nv = (-d[1], d[0])
        c = R.T(M(0, 0))
        for k in range(n):
            o = (k - (n - 1) / 2) * 2.6
            a0 = madd(c, (d, -6 - (k % 2) * 3), (nv, o))
            a1 = madd(a0, (d, -6 - (k * 5) % 4))
            seg = line(a0, a1)
            for j, q in enumerate(seg):
                if q not in Bd.px and q not in Hd.px:
                    FX.put([q], "U3" if j < 2 else "S5" if j < len(seg) * 0.6 else "S4")
    if p["feathers"]:
        f = p["feathers"]
        for k in range(9):
            a = 2 * math.pi * hash01(k, 1, 31)
            r = 3 + 12 * f * (0.5 + 0.5 * hash01(k, 2, 31))
            c = (O[0] + math.cos(a) * r, O[1] + math.sin(a) * r * 0.8 + f * f * 6)
            fa = 360 * hash01(k, 4, 31) + f * 200
            dd = dirv(fa)
            q0 = ip(c)
            q1 = ip(madd(c, (dd, 1.6)))
            q2 = ip(madd(c, (dd, 2.8)))
            col = ("S4", "S3", "S2")[k % 3] if f < 0.8 else ("S3", "S2", "S2")[k % 3]
            FX.put([q0, q1], col)
            if k % 2 == 0:
                FX.put([q2], "S5" if f < 0.6 else "S3")
    if p["flash"]:
        c = R.T(M(0.5, -0.5))
        S.star(FX, c, 3, cols=("U4", "U3", "U1"))
    return Ls, info


# =========================================================================== animation
FLAP = [(-116, -30, 1.0), (-140, -18, 1.0), (-176, 6, 0.9), (124, 24, 0.9), (100, 30, 0.85), (-160, -10, 0.85)]


def a_fly():
    fr = []
    for i, (w, b, c) in enumerate(FLAP):
        bob = (0.6, 0.2, -0.4, -0.8, -0.4, 0.4)[i]
        fr.append((70, CP(O=(20.0, 16.0 + bob), wing=w, bend=b, chord=c, tilt=-4 + bob * 2,
                          tail=0.9 + 0.2 * math.sin(i), wind=-1.0)))
    return fr


def perch_legs(dx=0.0):
    return [((-1.0 + dx, 2.4), (18.0 + dx, PERCH_FEET)), ((1.0 + dx, 2.2), (21.0 + dx, PERCH_FEET))]


PERCH = dict(O=(20.0, 17.2), tilt=-27.0, wing=176.0, bend=-8, chord=0.55, wlen=12.0, far=-4, tail=0.35,
             tuck=False)


def a_perch():
    fr = []
    for i in range(4):
        hd = [(0.0, 0.0, 0.0, 0.0), (1.0, 1.6, 28.0, 0.0), (0.4, 0.4, 10.0, 0.25), (-0.2, -0.3, -12.0, 0.0)][i]
        fr.append(((180, 150, 180, 220)[i], CP(**PERCH, legs=perch_legs(), head=(hd[0], hd[1]), hrot=hd[2], gape=hd[3])))
    return fr


def a_takeoff():
    return [
        (70, CP(O=(20.0, 19.4), tilt=-14, wing=-150, bend=-10, chord=0.8, wlen=12.5, tail=0.6, tuck=False,
                legs=[((-0.6, 2.4), (18.6, PERCH_FEET)), ((0.8, 2.2), (20.6, PERCH_FEET))], head=(-0.4, 0.6))),
        (60, CP(O=(20.0, 17.6), tilt=-20, wing=-96, bend=-24, chord=1.0, tail=1.0, tuck=False,
                legs=[((-0.6, 2.4), (17.6, PERCH_FEET - 1)), ((0.8, 2.2), (19.2, PERCH_FEET - 2))])),
        (60, CP(O=(20.0, 16.6), tilt=-10, wing=132, bend=25, chord=0.85, tail=1.1, wind=2)),
        (70, CP(O=(20.0, 16.0), tilt=-5, wing=-170, bend=5, chord=0.9, tail=1.0)),
    ]


def a_dive():
    fold = dict(wing=182.0, bend=-4, chord=0.45, wlen=11.5, far=-3, tail=0.2)
    return [
        (90, CP(O=(20.0, 15.2), tilt=-22, wing=-86, bend=-30, chord=1.0, tail=1.2, eye=3)),
        (150, CP(O=(19.4, 14.6), tilt=-30, wing=-70, bend=-42, chord=1.0, tail=1.3, eye=3, head=(0.3, -0.3))),
        (80, CP(O=(20.0, 16.0), tilt=40, **fold, eye=3, gape=0.3, streak=(40, 3), wind=3)),
        (80, CP(O=(20.6, 16.6), tilt=42, **fold, eye=3, gape=0.3, streak=(42, 4), wind=3)),
        (80, CP(O=(21.0, 17.0), tilt=38, **fold, eye=3, gape=0.2, streak=(38, 3), wind=2)),
        (110, CP(O=(20.4, 16.4), tilt=6, wing=-104, bend=-26, chord=1.0, tail=1.3, eye=2)),
    ]


def a_hurt():
    return [(80, CP(O=(18.6, 14.8), tilt=-30, wing=-60, bend=-40, chord=0.9, tail=1.4, eye=3, gape=0.6,
                    feathers=0.25, flash=True)),
            (120, CP(O=(19.4, 15.6), tilt=-12, wing=-140, bend=-10, chord=0.95, tail=1.1, eye=2, gape=0.2,
                     feathers=0.5))]


def a_death():
    sn = ["WingFar", "Tail", "Body", "Head", "WingNear"]
    pal = ("U3", "S5", "S4", "S3", "S2")

    def burn(f):
        return lambda imgs: K.ember_dissolve(imgs, f, sn, seed=4, rise=-8, pal=pal)
    return [
        (80, CP(O=(19.0, 14.6), tilt=-40, wing=-58, bend=-40, chord=1.0, tail=1.5, eye=3, gape=0.8,
                feathers=0.2, flash=True)),
        (90, CP(O=(18.6, 15.6), tilt=70, wing=150, bend=40, chord=0.9, tail=1.2, eye=1, gape=0.5, feathers=0.45)),
        (90, CP(O=(19.2, 18.0), tilt=160, wing=-120, bend=30, chord=0.7, tail=1.0, eye=0, gape=0.4, feathers=0.65,
                post=burn(0.15))),
        (100, CP(O=(20.0, 21.0), tilt=250, wing=100, bend=30, chord=0.6, tail=0.8, eye=0, gape=0.4, feathers=0.8,
                 post=burn(0.4))),
        (110, CP(O=(20.6, 24.0), tilt=320, wing=180, bend=20, chord=0.5, tail=0.6, eye=0, feathers=0.95,
                 post=burn(0.72))),
        (260, CP(O=(21.0, 26.0), tilt=350, wing=180, bend=20, chord=0.5, tail=0.6, eye=0, feathers=1.1,
                 post=burn(1.2))),
    ]


def build(build_ase):
    K.setup(40, 32)
    anims, infos = S.render_anims(SPEC, LAYERS, draw_crow,
                                  [("fly", a_fly), ("perch", a_perch), ("takeoff", a_takeoff), ("dive", a_dive),
                                   ("hurt", a_hurt), ("death", a_death)], sway_key="O", loops=("fly", "perch"))
    # hurtbox: body + head only (no wings), on fly frame 0
    hb = [12, 10, 16, 12]          # body + head (no wings / beak tip), centred on the anchor
    hit = S.hit_rect(infos, "dive", [2, 3, 4], floor=False)
    meta = {"native": 1, "frame": [40, 32], "anchor": [20, 16], "flying": True,
            "hurtbox": hb,
            "attacks": {"dive": {"active": [2, 4], "hit": hit}},
            "telegraph": {"dive": {"frame": 1, "at": S.spawn_pt(infos["dive"][1]["eye"])}},
            "notes": "faces right; floats (anchor = body centre). fly: 6-frame wingbeat loop. perch: standing on a "
                     "ledge, feet on frame row 24 (8px below the anchor), head bob/peck loop. takeoff: perch -> fly. "
                     "dive: 0-1 wings flare up/back (1 = held windup, eye glints), 2-4 wings folded, beak-first plunge "
                     "~40 deg down-right (engine moves it along that line), 5 wings snap open. death: tumbles, "
                     "feathers burst, falls and scatters into feathers (engine may let it fall further)."}
    S.export("sp_crow", LAYERS, anims, meta, build_ase)
    return meta
