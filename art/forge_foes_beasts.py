"""The Cold Forge's regular foes (cf_smith, cf_wraith, cf_hulk, cf_mite).  Driven by art/gen_forge_foes.py.  Face RIGHT.

cf_smith   96x72   floor 68, anchor x 40.  The Hollow Smith: an empty smith's coat and leather apron walking on its
                   own, a deep hood with one dim cinder, heavy iron gloves where hands should be; a forge hammer in the
                   near hand, long tongs in the far one (they glow when they grab).
                   idle(6) walk(8) hammer grab hold(4, loop) throw toss hurt(2) death(8)
cf_wraith  96x72   floor 68, anchor x 44.  The Quench Wraith: cold steam risen from still water; a long faceless skull
                   with a hissing mouth, a ribbed vapour body narrowing to the pool, two long arms ending in claws.
                   rise(8) idle(6) hiss(6) lunge(9) claw(9) sink(6) hurt(2) death(8)
cf_hulk    128x96  floor 92, anchor x 52.  The Bellows Hulk: a hunched heroic carrier; the great bellows is its back
                   (iron boards, pleated leather) and breathes into the grate in its chest (the core).
                   idle(6) walk(8) slam sweep blast vent(6, loop) hurt(4 = the stagger, kneeling) death(10)
cf_mite    24x16   floor 15, anchor x 12.  The Cinder Mite: a sleek iron tick with ember seams.
                   crawl(4) leap(6) cling(4, loop) hurt(2) death(5)
"""
import math
from forge_foes_kit import *  # noqa


def P_(base, **kw):
    p = dict(base); p.update(kw); return p


def at(p, **kw):
    q = dict(p); q.update(kw); return q


def Kf(p, n=1, ms=80, e="io", **fl):
    d = dict(p=p, n=n, ms=ms, e=e); d.update(fl); return d


def spine(hip, lean, L):
    up = dirv(-90 + lean)
    fwd = (-up[1], up[0])
    if fwd[0] < 0: fwd = (-fwd[0], -fwd[1])
    return up, fwd


def Tq(hip, lean, L, t, off):
    up, fwd = spine(hip, lean, L)
    return add(add(hip, mul(up, L * t)), mul(fwd, off))


# =====================================================================================================================
# HOLLOW SMITH
# =====================================================================================================================
SM = dict(W=96, H=72, FLOOR=68, AX=40, TOR=17.0, UA=9.5, FA=9.0, TH=11.5, SH=11.0)
SM_BASE = dict(hip=(40.0, 46.0), lean=14.0, head=0.0, nf=(46.0, 68.0), ff=(35.0, 68.0),
               na=-40.0, nr=0.5, npref=(-0.6, 1.0), wh=-150.0, fa=40.0, fr=0.85, fpref=(-0.3, 1.0), wt=24.0, op=2.0,
               heat=0.0, sway=(0.0, 0.0), eye=1.0, slump=0.0, sparks=0.0, hs="hammer")


def sm_shoulders(p):
    L = SM["TOR"]
    return Tq(p["hip"], p["lean"], L, 0.95, 1.5), Tq(p["hip"], p["lean"], L, 0.97, -2.4)


def sm_wrist(p, near):
    sn, sf = sm_shoulders(p)
    if near:
        return add(sn, mul(dirv(p["na"]), (SM["UA"] + SM["FA"]) * p["nr"]))
    return add(sf, mul(dirv(p["fa"]), (SM["UA"] + SM["FA"]) * p["fr"]))


def sleeve(cv, sh, wr, pref, bias, wind=(0, 0)):
    """A smith's sleeve: a soft cloth tube that widens at the cuff and hangs a little; a heavy iron glove at its end."""
    el = ik(sh, wr, SM["UA"], SM["FA"], pref)
    limb(cv, [sh, lerp(sh, el, 0.5), el, lerp(el, wr, 0.6), wr], [2.8, 2.7, 2.5, 2.6, 2.9], "S", bias=bias, iline=True)
    # the cuff opening (a dark ring) and the cloth hanging under the forearm
    d = unit(sub(wr, el)); v = perp(d)
    if v[1] < 0: v = (-v[0], -v[1])
    hang = [add(lerp(el, wr, 0.2), mul(v, 2.0)), add(lerp(el, wr, 0.95), mul(v, 2.6)), add(add(lerp(el, wr, 0.8), mul(v, 4.6)), (wind[0] * 0.4, 0)),
            add(add(lerp(el, wr, 0.45), mul(v, 3.6)), (wind[0] * 0.3, 0))]
    cv.paint(n_plate(poly_mask(hang), bevel=1.2, tilt=(0, 0.2)), "S", bias=bias - 1)
    return el, d


def glove(cv, wr, d, bias, r=2.4, open_=0.0):
    return fist(cv, wr, d, r, "I", bias=bias, open_=open_)


def hammer(cv, grip, ang, heat=0.0, bias=0):
    d = dirv(ang); v = perp(d)
    butt = sub(grip, mul(d, 3.0)); hd = add(grip, mul(d, 17.0))
    limb(cv, [butt, hd], [1.0, 0.9], "L", bias=bias, ao=0)
    hp = [add(hd, add(mul(v, 4.2), mul(d, 2.6))), add(hd, add(mul(v, 4.4), mul(d, -2.4))), add(hd, add(mul(v, -6.5), mul(d, -1.4))),
          add(hd, add(mul(v, -6.8), mul(d, 0.4))), add(hd, add(mul(v, -1.0), mul(d, 2.6)))]
    m = poly_mask(hp)
    cv.paint(n_plate(m, bevel=1.4, tilt=(-0.1, -0.25), strength=1.5), "I", bias=bias, iline=True)
    face = [q for q in m if (q[0] + .5 - hd[0]) * v[0] + (q[1] + .5 - hd[1]) * v[1] > 3.0]
    if heat > 0:
        cv.glow(face, heat_col(0.3 + 0.5 * heat), int(150 + 100 * heat))
    else:
        cv.decal(face, ("I", 4), only="I")
    return m, add(hd, mul(v, 4.4))


def tongs(cv, hand, ang, ln=24.0, op=4.0, heat=0.0, bias=0):
    d = dirv(ang); v = perp(d)
    piv = add(hand, mul(d, ln * 0.6))
    allp = set(); tips = []
    for s in (-1, 1):
        r0 = add(hand, mul(v, s * 0.9)); r1 = add(piv, mul(v, s * 0.3))
        jm = add(add(piv, mul(d, ln * 0.2)), mul(v, s * op * 0.55))
        jt = add(add(piv, mul(d, ln * 0.4)), mul(v, s * op * 0.15))
        nm = {q: norm3(v[0] * s * 0.3, -0.5, 0.8) for q in line(r0, r1)}
        nm2, _ = tube(qbez(r1, jm, jt, 10), 0.9, 0.6)
        nm.update(nm2)
        cv.paint(nm, "I", bias=bias, ao=0)
        allp |= set(nm2); tips.append(jt)
    cv.paint(n_dome(piv, 1.1, 1.1), "B", bias=bias)
    if heat > 0:
        cv.glow(list(allp), heat_col(0.25 + 0.6 * heat), int(140 + 110 * heat))
        halo(cv, allp, "E2", int(60 + 70 * heat))
    return allp, lerp(tips[0], tips[1], 0.5)


def smith(p, fi=0):
    cv = Canvas(SM["W"], SM["H"])
    info = {"hit": set()}
    hip, lean, sw = p["hip"], p["lean"], p["sway"]
    L = SM["TOR"]
    Tt = lambda t, o: Tq(hip, lean, L, t, o)
    if p["heat"] > 0.1:
        cv.lights.append((sm_wrist(p, False), 20.0, 0.6 * p["heat"]))
    sn, sf = sm_shoulders(p)
    # far arm + tongs (behind the coat; the tongs reach out in front)
    wr_f = sm_wrist(p, False)
    el_f, df = sleeve(cv, sf, wr_f, p["fpref"], -2, sw)
    tp, tmid = tongs(cv, add(wr_f, mul(df, 1.5)), p["wt"], 24.0, p["op"], p["heat"], bias=-1)
    glove(cv, wr_f, df, -2)
    info["tongs"] = tmid; info["tongpix"] = tp
    # boots under the coat
    for foot, b in ((p["ff"], -2), (p["nf"], 0)):
        hp_ = Tt(0.0, 1.0 if b == 0 else -1.5)
        kn = ik(hp_, add(foot, (0, -1.5)), SM["TH"], SM["SH"], (1, -0.1))
        limb(cv, [lerp(hp_, kn, 0.6), kn, add(foot, (0, -1.5))], [2.2, 2.0, 1.6], "S", bias=b, iline=True)
        fx, fy = foot
        cv.paint(n_plate(poly_mask([(fx - 2.2, fy - 3.4), (fx + 1.6, fy - 3.0), (fx + 5.0, fy - 0.6), (fx + 5.2, fy + 0.6), (fx - 2.6, fy + 0.6)]), bevel=1.0, tilt=(0.1, -0.5)), "L", bias=b, iline=True)
    # the coat: a long empty smith's coat; the hem trails the motion, split at the back
    kn_n = ik(Tt(0.0, 1.0), add(p["nf"], (0, -1.5)), SM["TH"], SM["SH"], (1, -0.1))
    kn_f = ik(Tt(0.0, -1.5), add(p["ff"], (0, -1.5)), SM["TH"], SM["SH"], (1, -0.1))
    hem = max(kn_n[1], kn_f[1]) + 4.0 - p["slump"] * 2
    sx = sw[0]
    coat = [Tt(1.02, -4.6), Tt(1.04, 2.6), Tt(0.7, 5.6), Tt(0.25, 5.2), Tt(0.0, 5.4),
            (kn_n[0] + 4.0 + sx * 0.3, hem - 1.0), (kn_n[0] - 1.0 + sx * 0.6, hem + 1.0), ((kn_n[0] + kn_f[0]) / 2 + sx, hem - 1.5),
            (kn_f[0] - 2.0 + sx * 1.2, hem + 1.5), (kn_f[0] - 6.5 + sx * 1.6, hem), Tt(0.1, -6.8), Tt(0.55, -6.6)]
    m = poly_mask(coat)
    cv.paint(n_plate(m, bevel=2.2, tilt=(0.05, -0.1), strength=1.0, fold=lambda x, y: (0.45 * math.sin(x * 0.85 + y * 0.12), 0.0)), "S", iline=True)
    # apron (bib + skirt), the strap and a scorch
    apron = [Tt(0.8, 1.6), Tt(0.82, 5.0), Tt(0.3, 6.2), Tt(0.0, 6.6), (kn_n[0] + 5.0 + sx * 0.3, hem - 3.0), (kn_n[0] - 0.5 + sx * 0.4, hem - 2.0), Tt(0.0, 0.8)]
    cv.paint(n_plate(poly_mask(apron), bevel=1.4, tilt=(0.15, -0.05), fold=lambda x, y: (0.35 * math.sin(x * 1.3), 0.0)), "L", iline=True)
    cv.decal(line(Tt(0.98, -1.0), Tt(0.82, 4.6)), ("L", 1), only="L")
    cv.decal(line(Tt(0.12, -4.6), Tt(0.12, 6.4)), ("B", 2), only=("S", "L"))
    # hood: deep, sloping forward; empty inside but for one dim cinder
    neck = Tt(1.0, 1.0)
    hd = add(neck, rot((2.4, -4.4), lean * 0.5 + p["head"]))
    R_ = lambda q: add(hd, rot(q, lean * 0.5 + p["head"]))
    hood = [R_(q) for q in ((-5.2, 4.2), (-5.0, -1.4), (-2.6, -4.6), (1.0, -5.0), (4.2, -2.8), (5.6, 0.6), (5.0, 4.0), (2.0, 5.2), (-2.0, 5.4))]
    cv.paint(n_plate(poly_mask(hood), bevel=1.8, tilt=(0.05, -0.25), strength=1.2), "S", iline=True)
    cv.paint(n_plate(poly_mask([R_((-4.6, 3.4)), R_((-6.6, 6.8)), R_((-2.0, 6.0))]), bevel=0.8), "S", bias=-1)   # the hood's tail
    void = [R_(q) for q in ((1.0, -2.6), (5.2, -0.6), (5.0, 3.6), (1.4, 4.0))]
    cv.flat(poly_mask(void), "S", 0)
    if p["eye"] > 0:
        e = ipt(R_((3.0, 0.6)))
        cv.glow([e], "E4" if p["eye"] > 0.6 else "E2")
        cv.glow([(e[0] - 1, e[1])], "E2", 160)
    info["head"] = hd
    # near arm + the hammer
    wr_n = sm_wrist(p, True)
    el_n, dn = sleeve(cv, sn, wr_n, p["npref"], 0, sw)
    hm, hface = hammer(cv, wr_n, p["wh"], p["heat"] * 0.0, bias=0)
    glove(cv, wr_n, dn, 0)
    info["hit"] = set(hm) if p["hs"] == "hammer" else set(tp); info["tip"] = hface if p["hs"] == "hammer" else tmid
    if p["sparks"] > 0:
        for i in range(int(10 * p["sparks"])):
            a = -180 + 180 * hash01(i, fi, 3); r = 3 + 9 * hash01(i, fi, 4)
            q = add(hface, (math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r * 0.7))
            cv.glow([q], "E5" if i % 3 else "E6")
    return cv, info


def smith_anims():
    b = SM_BASE
    idle = []
    for i in range(6):
        s = math.sin(i / 6 * 2 * math.pi)
        idle.append((140, at(b, hip=(40.0, 46.0 + 0.5 * s), lean=14 + 1.2 * s, na=-40 + 3 * s, wh=-150 + 3 * s, fa=40 + 3 * s, sway=(0.5 * s, 0)), {}))
    walk = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        def foot(phase):
            u = (phase % (2 * math.pi)) / (2 * math.pi)
            if u < 0.5: return (40.0 + 6.0 - 12.0 * (u / 0.5), 68.0)
            k = (u - 0.5) / 0.5
            return (40.0 - 6.0 + 12.0 * (k * k * (3 - 2 * k)), 68.0 - 2.5 * math.sin(k * math.pi))
        walk.append((110, at(b, hip=(40.0, 46.5 + 0.8 * math.cos(2 * ph)), nf=foot(ph), ff=foot(ph + math.pi), lean=17, na=-40 - 4 * math.sin(ph),
                             fa=40 + 6 * math.sin(ph), wt=24 + 4 * math.sin(ph), sway=(-1.5 + 0.6 * math.sin(2 * ph), 0)), {}))
    raise_ = at(b, na=-115, nr=0.85, wh=-165, lean=2, hip=(38.0, 46.5), head=-6, fa=70, wt=60)
    strike = at(b, na=50, nr=0.95, wh=78, lean=30, hip=(46.0, 49.0), nf=(54.0, 68.0), head=10, fa=60, wt=50)
    hammer_ = [Kf(b, 1, 80), Kf(raise_, 2, 80, "out"), Kf(at(raise_, na=-118, wh=-170), 1, 320, hold=1),
               Kf(at(b, na=-40, nr=0.95, wh=-40, lean=14), 1, 45, "lin", a=1, sm=1), Kf(strike, 1, 55, "slam", a=1, sm=1),
               Kf(at(strike, sparks=1.0), 1, 90, a=1), Kf(at(strike, sparks=0.4, na=52, wh=80), 2, 140), Kf(b, 2, 120)]
    reach_w = at(b, hs="tongs", fa=150, fr=0.5, wt=160, op=7.0, lean=6, hip=(38.0, 47.0), na=-60, wh=-160)
    reach = at(b, hs="tongs", fa=4, fr=1.0, wt=6, op=6.0, lean=32, hip=(48.0, 50.0), nf=(58.0, 68.0), ff=(34.0, 68.0), na=-30, wh=-150)
    grab = [Kf(b, 1, 80), Kf(reach_w, 2, 90, "out"), Kf(at(reach_w, op=8.0, heat=0.3), 1, 300, hold=1),
            Kf(reach, 2, 45, "snap", a=1), Kf(at(reach, op=1.0, heat=0.6), 1, 90, a=1), Kf(at(reach, op=5.0), 2, 130),
            Kf(at(b, hs="tongs"), 2, 140)]
    holdp = at(b, fa=-55, fr=0.95, wt=-50, op=1.5, heat=1.0, lean=-6, hip=(38.0, 46.5), head=-8, na=-110, nr=0.8, wh=-160)
    hold = [(110, at(holdp, fa=-55 + 3 * math.sin(k / 4 * 6.28), hip=(38.0, 46.5 + 0.5 * math.sin(k / 4 * 6.28)), sway=(0.6 * math.sin(k / 4 * 6.28), 0)), {}) for k in range(4)]
    throw = [Kf(holdp, 1, 80), Kf(at(holdp, na=-118, wh=-172), 1, 120),
             Kf(at(holdp, na=10, nr=0.95, wh=20, lean=10, fa=-40, wt=-30), 2, 45, "snap", sm=1, hit=1),
             Kf(at(b, fa=10, fr=1.0, wt=4, op=6.0, lean=20, hip=(44.0, 48.0), nf=(52.0, 68.0), na=40, wh=60), 2, 60, "snap", fling=1),
             Kf(at(b, fa=20, fr=0.9, wt=20, op=4.0, lean=18, hip=(44.0, 47.0), nf=(52.0, 68.0)), 2, 140), Kf(b, 2, 140)]
    tw = at(b, fa=150, fr=0.7, wt=170, op=1.5, heat=1.0, lean=4, hip=(38.0, 47.0))
    toss = [Kf(b, 1, 80), Kf(tw, 2, 90, "out"), Kf(at(tw, fa=155), 1, 260, hold=1),
            Kf(at(b, fa=-40, fr=0.95, wt=-50, op=5.0, heat=0.4, lean=18, hip=(42.0, 47.0)), 2, 50, "snap", sm=1, shot=1),
            Kf(at(b, fa=-30, fr=0.9, wt=-40, op=3.0, lean=16, hip=(42.0, 47.0)), 2, 130), Kf(b, 2, 120)]
    hurt = [(80, at(b, lean=2, head=-12, hip=(38.0, 46.0), na=-70, fa=10, sway=(2.5, 0), eye=0.5), {}), (130, at(b, lean=8, head=-6, hip=(39.0, 46.0), sway=(1.0, 0)), {})]
    dk = [Kf(b, 1, 80), Kf(at(b, lean=-4, head=-14, na=-80, fa=-10, hip=(38.0, 46.0)), 1, 120),
          Kf(at(b, lean=30, head=20, na=80, nr=0.9, wh=80, fa=80, wt=80, hip=(40.0, 54.0), slump=0.5, eye=0.4), 2, 120),
          Kf(at(b, lean=70, head=30, na=90, nr=0.95, wh=10, fa=100, wt=170, hip=(42.0, 62.0), nf=(50.0, 68.0), ff=(32.0, 68.0), slump=1.0, eye=0.0), 2, 150),
          Kf(at(b, lean=82, head=34, na=95, nr=0.95, wh=4, fa=110, wt=176, hip=(43.0, 64.0), nf=(50.0, 68.0), ff=(32.0, 68.0), slump=1.0, eye=0.0), 2, 300)]
    return [("idle", idle, True), ("walk", walk, True), ("hammer", seq(hammer_), False), ("grab", seq(grab), False),
            ("hold", hold, True), ("throw", seq(throw), False), ("toss", seq(toss), False), ("hurt", hurt, False), ("death", seq(dk), False)]


# =====================================================================================================================
# QUENCH WRAITH
# =====================================================================================================================
WR = dict(W=96, H=72, FLOOR=68, AX=44)
WR_BASE = dict(hip=(44.0, 68.0), rise=1.0, lean=18.0, head=0.0, mouth=0.15, na=10.0, nr=0.75, fa=30.0, fr=0.7, claw=0.4,
               fade=0.0, sway=(0.0, 0.0), coil=0.0, fi=0)


def steam_paint(cv, mask, base_lv=2.0, top=None, edge_a=165, seed=0, fi=0, fade=0.0, core=None):
    """Emissive cold steam: brighter inside and where the top light falls, a soft dithered edge, a slow churn."""
    if not mask:
        return
    d = dist_field(mask)
    ys = [q[1] for q in mask]; y0, y1 = min(ys), max(ys)
    for q in mask:
        x, y = q
        dd = d.get(q, 1.0)
        churn = hash01((x + fi) // 3, (y - fi) // 3, seed) * 0.9 - 0.3
        lv = base_lv + min(2.2, (dd - 1) * 0.7) + churn + (0.8 if (x, y - 1) not in mask else 0) - (0.6 if (x + 1, y) not in mask else 0)
        if core and math.hypot(x - core[0], y - core[1]) < core[2]:
            lv += 0.8
        lv = max(0, min(5, int(lv)))
        a = 255 if dd > 1.5 else edge_a
        if fade > 0:
            if hash01(x, y, 99 + fi) < fade: continue
            a = int(a * (1 - 0.6 * fade))
        cv.glow([q], f"Q{lv}", a)


def wraith(p, fi=0):
    cv = Canvas(WR["W"], WR["H"])
    info = {"hit": set()}
    bx, fy = p["hip"]
    rise, lean, sw = p["rise"], p["lean"], p["sway"]
    fi = int(round(p.get("fi", fi)))
    # the still water it rose from
    pool = {q for q in mask_disc((bx, fy + 0.4), 13.0 + 4 * (1 - rise), 1.6) if q[1] >= fy - 1}
    cv.glow(list(pool), "Q0", 200, behind=True)
    cv.glow([q for q in pool if q[1] == fy - 1 and (q[0] + fi) % 4 == 0], "Q2", 160, behind=True)
    if rise <= 0.02:
        info["head"] = (bx, fy - 4); info["tip"] = (bx, fy - 4)
        return cv, info
    H = 42.0 * rise
    la = math.radians(lean)
    neck = (bx + 4 + math.sin(la) * H * 0.55 + p["coil"] * -6, fy - H * (0.95 - 0.25 * math.sin(la) ** 2))
    c1 = (bx - 3 - sw[0] * 0.8, fy - H * 0.3)
    c2 = (bx + 1 + math.sin(la) * H * 0.2 - p["coil"] * 6, fy - H * 0.72)
    sp = bezier((bx, fy - 1), c1, c2, neck, 30)
    ws = []
    for i in range(31):
        t = i / 30
        w = 1.0 + 5.2 * math.sin(math.pi * min(1.0, 0.12 + t * 0.9)) ** 1.3 * (0.55 + 0.45 * t)
        if t > 0.9: w *= 0.6
        ws.append(w * (0.6 + 0.4 * rise))
    body = poly_mask(ribbon(sp, ws))
    # trailing wisps from the back (they stream behind the motion)
    wisps = set()
    for k in range(4):
        t0 = 0.35 + k * 0.17
        a0 = sp[int(t0 * 30)]
        tail = bezier(a0, add(a0, (-6 - sw[0] * 2, -2 + k)), add(a0, (-12 - sw[0] * 3, 1 + k * 2)), add(a0, (-18 - sw[0] * 4 - k * 2, 4 + k * 3)), 18)
        for i, q in enumerate(tail):
            if hash01(i, k, fi + 3) > 0.25:
                wisps.add(ipt(q))
    cv.glow(list(wisps - body), "Q2", 120)
    chest = sp[22]
    steam_paint(cv, body, 1.6, seed=3, fi=fi, fade=p["fade"], core=(chest[0], chest[1], 4.0))
    # ribs: an emaciated cage of darker vapour
    if rise > 0.6 and p["fade"] < 0.5:
        for k, t in enumerate((0.64, 0.74)):
            q = sp[int(t * 30)]
            dv = unit(sub(sp[int(t * 30) + 1], sp[int(t * 30) - 1])); nv = perp(dv)
            cv.glow([ipt(add(q, mul(nv, o))) for o in (-2.5, -1.5, -0.5, 0.5)], "Q1", 200)
    # arms: long, reaching, vapour sleeves over bone; three claws
    sh = sp[25]
    claws = set()
    for near, a_, r_, al in ((False, p["fa"], p["fr"], 190), (True, p["na"], p["nr"], 255)):
        wr = add(sh, mul(dirv(a_), 26.0 * r_))
        el = ik(sh, wr, 13.5, 13.5, (-0.3, 1.0))
        arm = poly_mask(ribbon(qbez(sh, el, wr, 14), [2.4 - 1.2 * (i / 14) for i in range(15)]))
        if near:
            steam_paint(cv, arm, 2.0, seed=5, fi=fi, fade=p["fade"])
        else:
            cv.glow(list(arm), "Q2", al)
        d = unit(sub(wr, el)); v = perp(d)
        for j in (-1, 0, 1):
            c0 = add(wr, mul(v, j * 0.8))
            spread = j * (0.5 + p["claw"] * 1.6)
            c1_ = add(c0, add(mul(d, 3.6), mul(v, spread)))
            c2_ = add(c1_, add(mul(d, 2.6 - p["claw"]), mul(v, spread * 0.3 + 1.4)))      # the hook of the claw
            pts = [ipt(q) for q in qbez(c0, c1_, c2_, 8)]
            cv.glow(pts[:-2], "Q4" if near else "Q3", 255 if near else 190)
            cv.glow(pts[-2:], "Q5" if near else "Q3", 255 if near else 190)
            claws |= set(pts)
        if near:
            info["tip"] = wr
    # head: a long faceless skull, the jaw drops open to hiss
    tilt = lean * 0.5 + p["head"]
    hd = add(neck, rot((3.0, -3.2), tilt))
    R_ = lambda q: add(hd, rot(q, tilt))
    skull = poly_mask([R_(q) for q in ((-4.0, 1.0), (-3.0, -2.8), (0.5, -3.8), (4.6, -2.6), (7.6, -0.6), (7.4, 1.0), (3.0, 1.6), (-1.4, 3.4))])
    jaw_a = 8 + 34 * p["mouth"]
    J_ = lambda q: add(R_((-1.0, 1.2)), rot(q, tilt + jaw_a))
    jaw = poly_mask([J_(q) for q in ((0.0, 0.0), (7.6, -0.4), (6.6, 1.6), (0.4, 2.0))])
    steam_paint(cv, skull | jaw, 2.6, seed=7, fi=fi, fade=p["fade"])
    mouth = poly_mask([R_((0.6, 1.4)), R_((7.4, 1.0)), J_((7.0, 0.2)), J_((0.6, 0.6))]) - jaw
    cv.glow(list(mouth), "Q0", 255)
    cv.glow([ipt(R_((2.0, -1.0))), ipt(R_((3.0, -1.0))), ipt(R_((4.6, -0.6)))], "Q0", 255)
    if p["mouth"] > 0.5:      # the hiss: a jet of steam from the mouth
        m0 = R_((7.6, 1.2))
        for i in range(10):
            q = add(m0, (2 + i * 1.6 + hash01(i, fi, 4) * 2, (hash01(i, fi, 5) - 0.5) * (1 + i * 0.6)))
            cv.glow([ipt(q)], "Q4" if i < 4 else "Q3", 220 - i * 14)
    info["head"] = hd
    info["hit"] = claws | {ipt(q) for q in mask_disc(info["tip"], 4.0)}
    return cv, info


def wraith_anims():
    b = WR_BASE
    rise = [(110, at(b, rise=0.0), {})] + [(90, at(b, rise=k / 6, lean=40 - k * 3, mouth=0.1 + 0.1 * k, na=70, fa=80, claw=0.2), {}) for k in range(1, 7)] + [(140, at(b, mouth=0.8), {})]
    idle = [(130, at(b, lean=18 + 3 * math.sin(k / 6 * 6.28), na=10 + 6 * math.sin(k / 6 * 6.28 + 1), fa=30 + 6 * math.sin(k / 6 * 6.28 + 2),
                     head=3 * math.sin(k / 6 * 6.28 + 0.5), sway=(1.2 * math.sin(k / 6 * 6.28), 0), fi=k), {}) for k in range(6)]
    hissp = at(b, lean=4, head=-14, mouth=1.0, na=-20, nr=0.6, fa=0, fr=0.55, claw=1.0, coil=1.0)
    hiss = [Kf(b, 1, 70), Kf(hissp, 2, 90, "out"), Kf(at(hissp, fi=1), 1, 120, hold=1), Kf(at(hissp, fi=2), 1, 120), Kf(at(hissp, fi=3, head=-12), 1, 120)]
    lun = at(b, hip=(64.0, 68.0), lean=76, rise=0.82, head=16, mouth=0.9, na=26, nr=1.0, fa=34, fr=1.0, claw=1.0, sway=(-5, 0))
    lunge = [Kf(at(hissp, mouth=0.7), 1, 60), Kf(lun, 2, 45, "snap", a=1, st=1), Kf(at(lun, hip=(70.0, 68.0), na=32, fa=40), 2, 60, a=1),
             Kf(at(lun, hip=(70.0, 68.0), lean=40, mouth=0.3, na=40, fa=50, claw=0.4), 2, 120), Kf(at(b, hip=(70.0, 68.0)), 2, 120)]
    c1 = at(b, na=-60, nr=0.8, lean=24, claw=1.0, mouth=0.4, fa=20)
    c2 = at(b, na=50, nr=1.0, lean=34, claw=0.8, mouth=0.6, hip=(50.0, 68.0), fa=-40, fr=0.8)
    c3 = at(b, na=40, nr=0.8, fa=50, fr=1.0, lean=36, claw=0.8, mouth=0.6, hip=(54.0, 68.0))
    claw = [Kf(b, 1, 70), Kf(c1, 2, 80, "out"), Kf(at(c1, na=-64), 1, 160, hold=1), Kf(c2, 2, 45, "snap", a=1, sm=1),
            Kf(at(c2, na=-30, nr=0.8, fa=-70, fr=0.9), 1, 80), Kf(c3, 2, 45, "snap", a=2), Kf(at(c3, lean=24), 2, 120), Kf(at(b, hip=(54.0, 68.0)), 2, 120)]
    sink = [(90, at(b, rise=1 - k / 5, lean=18 + k * 4, mouth=0.3, na=60, fa=70, fade=0.15 * k, fi=k), {}) for k in range(6)]
    hurt = [(80, at(b, lean=-6, head=-16, mouth=0.9, na=-50, fa=-30, sway=(3, 0)), {}), (120, at(b, lean=8, head=-6, mouth=0.4), {})]
    death = [(80, at(b, lean=-10, head=-20, mouth=1.0, na=-60, fa=-50, fi=0), {})] + \
            [(100, at(b, rise=max(0.0, 1 - k * 0.12), lean=-10 + k * 6, head=-20, mouth=1.0, na=-60 + k * 10, fa=-50 + k * 10, fade=min(1.0, k * 0.15), fi=k, sway=(2, -1)), {}) for k in range(1, 7)] + \
            [(400, at(b, rise=0.0), {})]
    return [("rise", rise, False), ("idle", idle, True), ("hiss", seq(hiss), False), ("lunge", seq(lunge), False), ("claw", seq(claw), False),
            ("sink", sink, False), ("hurt", hurt, False), ("death", death, False)]


# =====================================================================================================================
# BELLOWS HULK
# =====================================================================================================================
HK = dict(W=128, H=96, FLOOR=92, AX=52, TOR=29.0, UA=16.5, FA=16.5, TH=19.0, SH=19.0)
HK_BASE = dict(hip=(50.0, 57.0), lean=46.0, head=0.0, nf=(60.0, 92.0), ff=(41.0, 92.0), na=62.0, nr=0.92, npref=(-0.2, 1.0),
               fa=70.0, fr=0.9, fpref=(-0.2, 1.0), breath=0.4, core=0.35, nopen=0.0, fopen=0.0, sway=(0.0, 0.0), eye=1.0, kneel=0.0)


def hk_T(p, t, off):
    return Tq(p["hip"], p["lean"], HK["TOR"], t, off)


def hk_shoulders(p):
    return hk_T(p, 0.9, 3.0), hk_T(p, 0.93, -1.5)


def hk_wrist(p, near):
    sn, sf = hk_shoulders(p)
    if near:
        return add(sn, mul(dirv(p["na"]), (HK["UA"] + HK["FA"]) * p["nr"]))
    return add(sf, mul(dirv(p["fa"]), (HK["UA"] + HK["FA"]) * p["fr"]))


def hk_arm(cv, p, near):
    sn, sf = hk_shoulders(p)
    sh = sn if near else sf
    wr = hk_wrist(p, near)
    b = 0 if near else -2
    el = ik(sh, wr, HK["UA"], HK["FA"], p["npref" if near else "fpref"])
    limb(cv, [sh, lerp(sh, el, 0.35), el, lerp(el, wr, 0.3), wr], [3.8, 3.5, 2.5, 3.3, 2.2], "S", bias=b, iline=True)
    d = unit(sub(wr, el)); v = perp(d)
    if v[1] > 0: v = (-v[0], -v[1])     # the outer (upper) side of the forearm
    # iron vambrace: a broad banded plate over the forearm, flared at the elbow
    va = [add(sub(el, mul(d, 2.0)), mul(v, 1.2)), add(lerp(el, wr, 0.3), mul(v, 3.8)), add(lerp(el, wr, 0.98), mul(v, 2.6)),
          add(lerp(el, wr, 0.98), mul(v, -2.2)), add(lerp(el, wr, 0.35), mul(v, -3.0)), add(el, mul(v, -2.0))]
    cv.paint(n_plate(poly_mask(va), bevel=1.8, tilt=(0.1 + v[0] * 0.3, -0.25 + v[1] * 0.3), strength=1.3), "I", bias=b - 1)
    cv.decal(line(add(lerp(el, wr, 0.15), mul(v, 2.6)), add(lerp(el, wr, 0.92), mul(v, 2.0))), ("I", 5 if near else 4), only="I")
    cv.decal(line(add(lerp(el, wr, 0.55), mul(v, 3.2)), add(lerp(el, wr, 0.55), mul(v, -2.6))), ("I", 1), only="I")
    # upper-arm: a pauldron sweeping back off the shoulder
    du = unit(sub(el, sh)); pu = perp(du)
    if pu[1] > 0: pu = (-pu[0], -pu[1])
    pd = [add(sh, add(mul(pu, 4.2), mul(du, -2.0))), add(lerp(sh, el, 0.4), mul(pu, 4.2)), add(lerp(sh, el, 0.58), mul(pu, 0.6)),
          add(lerp(sh, el, 0.3), mul(pu, -3.2)), add(sub(sh, mul(du, 6.0)), mul(pu, 1.0))]
    cv.paint(n_plate(poly_mask(pd), bevel=2.4, tilt=(-0.1, -0.4), strength=1.3), "I", bias=b - 1)
    c = fist(cv, wr, d, 3.3, "I", bias=b, open_=p["nopen" if near else "fopen"] * 2.5)
    return wr, c, d


def hk_leg(cv, p, near):
    hip = hk_T(p, 0.0, 2.0 if near else -2.5)
    foot = p["nf" if near else "ff"]
    b = 0 if near else -2
    kn = leg(cv, hip, foot, HK["TH"], HK["SH"], R=(4.6, 4.0, 2.6, 3.2, 1.9), pref=(1, -0.2), mat="S", bias=b, toe=8.0)
    ank = add(foot, (0, -1.6))
    ds = unit(sub(ank, kn)); v = perp(ds)
    if v[0] < 0: v = (-v[0], -v[1])
    gv = [add(kn, mul(v, 3.4)), add(lerp(kn, ank, 0.5), mul(v, 3.2)), add(ank, mul(v, 2.4)), add(ank, mul(v, -1.6)), add(lerp(kn, ank, 0.3), mul(v, -2.2))]
    cv.paint(n_plate(poly_mask(gv), bevel=1.8, tilt=(0.3, -0.15), strength=1.2), "I", bias=b)
    cv.paint(n_dome(add(kn, mul(v, 1.0)), 2.8, 2.7), "I", bias=b)
    dt = unit(sub(kn, hip)); vt = perp(dt)
    if vt[0] < 0: vt = (-vt[0], -vt[1])
    cv.paint(n_plate(poly_mask([add(hip, mul(vt, 4.2)), add(lerp(hip, kn, 0.8), mul(vt, 3.6)), add(lerp(hip, kn, 0.95), mul(vt, 0.5)),
                                add(lerp(hip, kn, 0.3), mul(vt, -2.0))]), bevel=1.6, tilt=(0.2, -0.3)), "I", bias=b - 1)
    return kn


def bellows(cv, p, fi):
    """The great bellows is the hulk's back: an inner board along the spine, an outer board hinged at the shoulders
    that swings open with each breath, pleated leather between, a nozzle over the shoulder into the chest grate."""
    br = p["breath"]
    hinge = hk_T(p, 1.0, -2.0)
    inner_end = hk_T(p, -0.06, -6.0)
    di = unit(sub(inner_end, hinge))
    L = math.hypot(*sub(inner_end, hinge)) + 2.0
    ang_i = math.degrees(math.atan2(di[1], di[0]))
    ang_o = ang_i + 5 + 14 * br           # opens outward (away from the body); at rest it lies along the back
    do = dirv(ang_o)
    outer_end = add(hinge, mul(do, L * 1.02))
    # leather: the wedge between the boards, pleats radiating from the hinge
    mid_o = lerp(hinge, outer_end, 0.55)
    wedge = [hinge, add(outer_end, mul(perp(do), 0.0)), lerp(outer_end, inner_end, 0.5), inner_end]
    wm = poly_mask(wedge)
    npl = 6
    def fold(x, y):
        a = math.degrees(math.atan2(y + .5 - hinge[1], x + .5 - hinge[0]))
        k = (a - ang_i) / max(1.0, (ang_o - ang_i)) * npl
        return (0.0, 0.0) if False else (0.9 * math.sin(k * math.pi) * -do[1], 0.9 * math.sin(k * math.pi) * do[0])
    cv.paint(n_plate(wm, bevel=2.0, tilt=(-0.1, -0.2), strength=1.0, fold=fold), "L", bias=-1)
    # pleat ridges (lit) and creases (dark) along the open edge
    for k in range(1, npl):
        a = ang_i + (ang_o - ang_i) * k / npl
        e = add(hinge, mul(dirv(a), L * (0.98 + 0.04 * (k % 2))))
        cv.decal(line(lerp(hinge, e, 0.35), e), ("L", 4 if k % 2 else 0), only="L")
    # the outer board: a long sleek curved shell (an elytron, not a slab), widest a third of the way down, pointed at
    # both ends, a riveted spine and a lit rim
    nv = perp(do)
    if (nv[0] * (hinge[0] - hk_T(p, 0.5, 0)[0]) + nv[1] * (hinge[1] - hk_T(p, 0.5, 0)[1])) < 0 and False: pass
    awayv = unit(sub(lerp(hinge, outer_end, 0.5), hk_T(p, 0.55, 0.0)))
    sp = [add(lerp(hinge, outer_end, t), mul(awayv, 3.2 * math.sin(math.pi * t))) for t in (i / 16 for i in range(17))]
    ws = [0.8 + 3.6 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8 * (1 - 0.45 * t) for t in (i / 16 for i in range(17))]
    ob = ribbon(sp, ws)
    om = poly_mask(ob)
    cv.paint(n_plate(om, bevel=2.4, tilt=(-0.2 + awayv[0] * 0.3, -0.35 + awayv[1] * 0.3), strength=1.35), "I")
    cv.decal([ipt(add(q, mul(awayv, w_ * 0.55))) for q, w_ in zip(sp[2:15], ws[2:15])], ("I", 5), only="I")
    cv.decal([ipt(q) for q in sp[3:14:3]], ("B", 4), only="I")
    # the nozzle: a curved iron throat from the hinge over the shoulder into the grate
    g = hk_T(p, 0.68, 6.0)
    noz = qbez(hinge, add(hk_T(p, 1.12, 2.0), (0, -2)), add(g, (0, -3)), 14)
    limb(cv, noz, [2.6] + [2.2] * 12 + [1.8], "I", bias=-1, ao=0)
    cv.paint(n_dome(hinge, 3.4, 3.4), "I")
    cv.decal([ipt(hinge)], ("B", 4), only="I")
    return om | wm


def hk_tabard(cv, p, front):
    """Leather flaps hanging from the girdle: they break up the legs' dark mass and trail the motion."""
    sw = p["sway"]
    a0 = hk_T(p, 0.02, 4.0 if front else -4.0)
    a1 = hk_T(p, 0.02, 0.5 if front else -0.5)
    L = 22.0 if front else 18.0
    lo0 = add(a0, (sw[0] * 1.6 + (2.0 if front else -3.0), L))
    lo1 = add(a1, (sw[0] * 1.2 + (0.0 if front else -1.5), L - 2.0))
    m = poly_mask([a0, a1, lo1, add(lerp(lo0, lo1, 0.5), (0, 2.0)), lo0])
    cv.paint(n_plate(m, bevel=1.4, tilt=(0.1, 0.0), strength=1.0, fold=lambda x, y: (0.5 * math.sin(x * 1.1), 0.0)), "L", bias=0 if front else -2)
    cv.decal(line(add(a0, (0.5, 3.0)), add(lo0, (0.0, -2.0))), ("L", 1), only="L")


def hk_chest(cv, p, fi):
    Tt = lambda t, o: hk_T(p, t, o)
    core = [Tt(0.0, -3.8), Tt(0.0, 3.8), Tt(0.28, 4.8), Tt(0.55, 8.6), Tt(0.82, 9.2), Tt(1.02, 5.4), Tt(1.04, -2.0), Tt(0.6, -5.8), Tt(0.25, -4.6)]
    cv.paint(n_plate(poly_mask(core), bevel=3.4, tilt=(0.05, -0.15), strength=1.2), "S", iline=True)
    # breastplate: a deep keel of iron over the chest, cut open at the grate
    bp = [Tt(0.42, 3.4), Tt(0.52, 8.4), Tt(0.8, 9.6), Tt(1.0, 6.0), Tt(1.0, 1.0), Tt(0.7, 0.0)]
    m = poly_mask(bp)
    cv.paint(n_plate(m, bevel=3.0, tilt=(0.25, -0.3), strength=1.3), "I")
    cv.decal(line(Tt(0.97, 5.4), Tt(0.54, 8.2)), ("I", 5), only="I")
    # waist: a girdle of leather straps (narrow: the wedge stays heroic)
    cv.paint(n_plate(poly_mask([Tt(-0.04, -4.0), Tt(-0.04, 4.2), Tt(0.12, 4.6), Tt(0.12, -4.4)]), bevel=1.0), "L", bias=-1)
    cv.decal(line(Tt(0.04, -3.6), Tt(0.04, 4.0)), ("B", 3), only="L")
    # the grate (core): bars over a fire that breathes with the bellows
    gc = Tt(0.68, 6.0)
    k = max(0.0, min(1.0, p["core"]))
    rx, ry = 2.6, 3.6
    fire = mask_disc(gc, rx, ry)
    for q in fire:      # hotter at the heart of the grate, breathing with the bellows
        r = math.hypot((q[0] + .5 - gc[0]) / rx, (q[1] + .5 - gc[1]) / ry)
        cv.glow([q], heat_col(max(0.0, 0.15 + 0.7 * k - 0.45 * r + 0.1 * (hash01(q[0], q[1] + fi, 3) - 0.5))), 255)
    up = dirv(-90 + p["lean"]); fw = perp(up)
    for o in (-1.3, 0.2):
        cv.glow([q for q in line(add(gc, add(mul(up, ry - 0.5), mul(fw, o))), add(gc, add(mul(up, -ry + 0.5), mul(fw, o)))) if q in fire], "I1", 255)
    if k > 0.8:
        halo(cv, fire, "E2", int(60 + 90 * (k - 0.8) / 0.2), r=1, behind=False)
    cv.lights.append((gc, 9 + 7 * k, 0.22 + 0.28 * k))
    return gc


def hk_head(cv, p, fi):
    neck0 = hk_T(p, 1.0, 3.5)
    tilt = p["lean"] * 0.15 + p["head"]
    nk = add(neck0, rot((3.4, -2.8), tilt))
    limb(cv, [neck0, nk], [3.0, 2.4], "S", bias=-1, iline=True)
    hd = add(nk, rot((3.6, 0.4), tilt))
    R_ = lambda q: add(hd, rot(q, tilt))
    # a small hooded head with a long-jawed smith's mask, jutting forward from the hump
    hood = [R_(q) for q in ((-4.2, -0.2), (-2.8, -3.8), (0.4, -4.6), (3.2, -3.4), (3.8, 0.0), (1.6, 3.0), (-2.4, 2.8))]
    cv.paint(n_plate(poly_mask(hood), bevel=1.6, tilt=(0.05, -0.3), strength=1.2), "S", iline=True)
    mask = [R_(q) for q in ((0.6, -2.6), (3.8, -2.2), (6.4, -0.2), (8.4, 2.2), (5.4, 3.0), (2.2, 3.4), (0.4, 2.2))]
    cv.paint(n_plate(poly_mask(mask), bevel=1.1, tilt=(0.25, -0.2), strength=1.3), "I")
    cv.decal(line(R_((2.0, -0.4)), R_((5.0, 0.2))), ("I", 0), only="I")
    cv.decal(line(R_((1.2, -2.0)), R_((7.4, 1.8))), ("I", 5), only="I")
    if p["eye"] > 0:
        cv.glow([ipt(R_((3.0, -0.4))), ipt(R_((4.0, -0.2)))], "E4" if p["eye"] > 0.6 else "E2")
    return hd


def hulk(p, fi=0):
    cv = Canvas(HK["W"], HK["H"])
    info = {"hit": set()}
    fi = int(round(p.get("fi", fi)))
    wr_f, c_f, d_f = hk_arm(cv, p, False)
    hk_leg(cv, p, False)
    hk_tabard(cv, p, False)
    bellows(cv, p, fi)
    gc = hk_chest(cv, p, fi)
    hk_leg(cv, p, True)
    hk_tabard(cv, p, True)
    wr_n, c_n, d_n = hk_arm(cv, p, True)
    hd = hk_head(cv, p, fi)
    info["core"] = gc; info["head"] = hd; info["tip"] = c_n; info["tip2"] = c_f
    info["hit"] = {q for q in mask_disc(c_n, 6.0)} | ({q for q in mask_disc(c_f, 6.0)} if p.get("both_fists") else set())
    info["body"] = set()
    return cv, info


def hulk_anims():
    b = HK_BASE
    idle = []
    for i in range(6):
        s = math.sin(i / 6 * 2 * math.pi)
        idle.append((150, at(b, hip=(50.0, 58.5 + 0.6 * s), lean=46 - 1.5 * s, breath=0.45 + 0.35 * s, core=0.35 + 0.15 * s,
                             na=62 + 2 * s, fa=70 + 2 * s, sway=(0.4 * s, 0)), {}))
    walk = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        def foot(phase, cx):
            u = (phase % (2 * math.pi)) / (2 * math.pi)
            if u < 0.5: return (cx + 7.0 - 14.0 * (u / 0.5), 92.0)
            k = (u - 0.5) / 0.5
            return (cx - 7.0 + 14.0 * (k * k * (3 - 2 * k)), 92.0 - 3.0 * math.sin(k * math.pi))
        walk.append((120, at(b, hip=(50.0, 59.0 + 1.2 * math.cos(2 * ph)), nf=foot(ph, 56.0), ff=foot(ph + math.pi, 46.0), lean=48,
                             na=62 - 10 * math.sin(ph), fa=70 + 10 * math.sin(ph), breath=0.4 + 0.2 * math.cos(2 * ph), sway=(-1.0, 0)), {}))
    up = at(b, na=-105, nr=0.8, fa=-95, fr=0.8, lean=16, hip=(48.0, 60.0), head=-12, breath=1.2, core=0.6, npref=(-0.4, 1.0), fpref=(-0.4, 1.0), both_fists=1)
    down = at(b, na=62, nr=0.98, fa=66, fr=0.98, lean=62, hip=(56.0, 64.0), nf=(68.0, 92.0), ff=(42.0, 92.0), head=14, breath=0.1, core=0.5, both_fists=1)
    slam = [Kf(b, 1, 90), Kf(up, 3, 90, "out"), Kf(at(up, na=-110, fa=-100), 1, 360, hold=1),
            Kf(at(b, na=-20, nr=0.95, fa=-14, fr=0.95, lean=40, hip=(52.0, 61.0), breath=0.6, both_fists=1), 1, 45, "lin", a=1, sm=1),
            Kf(down, 1, 55, "slam", a=1, sm=1), Kf(at(down, na=64, fa=68), 4, 170), Kf(b, 3, 140)]
    back = at(b, na=165, nr=0.85, npref=(0.2, 1.0), lean=30, hip=(48.0, 59.0), head=-6, breath=0.8, fa=70)
    sweep = [Kf(b, 1, 90), Kf(back, 2, 90, "out"), Kf(at(back, na=168), 1, 300, hold=1),
             Kf(at(b, na=95, nr=1.0, lean=42, hip=(52.0, 60.0), breath=0.5), 1, 45, "lin", a=1, sm=1),
             Kf(at(b, na=20, nr=1.0, lean=48, hip=(56.0, 61.0), nf=(66.0, 92.0), breath=0.3), 1, 50, "lin", a=1, sm=1),
             Kf(at(b, na=-20, nr=0.95, lean=44, hip=(56.0, 60.0), nf=(66.0, 92.0), breath=0.3), 1, 60, "out", a=1, sm=1),
             Kf(at(b, na=-10, nr=0.9, lean=42, hip=(56.0, 60.0), nf=(66.0, 92.0)), 3, 150), Kf(at(b, hip=(56.0, 58.5), nf=(66.0, 92.0)), 3, 140)]
    inh = at(b, lean=22, hip=(48.0, 58.0), head=-14, breath=1.9, core=0.9, na=120, nr=0.8, fa=130, fr=0.8, npref=(-0.5, 1), fpref=(-0.5, 1))
    exh = at(b, lean=46, hip=(52.0, 61.0), head=6, breath=-0.05, core=1.0, na=60, nr=0.9, fa=70, fr=0.9)
    blast = [Kf(b, 1, 90), Kf(inh, 3, 110, "out"), Kf(at(inh, breath=2.1, core=1.0), 1, 420, hold=1),
             Kf(exh, 2, 50, "snap", wave=1), Kf(at(exh, breath=0.0), 3, 130), Kf(at(exh, breath=0.05, core=0.9, lean=50, hip=(52.0, 62.0)), 2, 150)]
    vent = []
    for i in range(6):
        s = math.sin(i / 6 * 2 * math.pi)
        vent.append((110, at(b, lean=54 + 2 * s, hip=(50.0, 63.0 + 0.6 * s), head=18, breath=0.08 + 0.08 * s, core=0.95 + 0.05 * s, na=88, nr=0.95, fa=92, fr=0.95, nopen=0.8, fopen=0.8, fi=i), {}))
    kneel = at(b, hip=(50.0, 72.0), lean=50, nf=(64.0, 92.0), ff=(36.0, 92.0), head=24, na=95, nr=0.98, fa=100, fr=0.98, breath=0.0, core=1.0, nopen=1.0, fopen=1.0)
    hurt = [(80, at(b, lean=24, head=-18, hip=(48.0, 60.0), breath=0.9, core=1.0, na=40, fa=50), {}),
            (100, at(kneel, hip=(50.0, 68.0), lean=44, core=1.0, breath=0.3), {}), (120, at(kneel, fi=1), {}), (200, at(kneel, fi=2, head=26), {})]
    dk = [Kf(b, 1, 90), Kf(at(b, lean=20, head=-20, hip=(48.0, 60.0), breath=1.0, core=1.0, na=30, fa=40), 1, 140),
          Kf(kneel, 2, 120), Kf(at(kneel, lean=72, hip=(54.0, 76.0), head=30, na=70, fa=76, breath=0.0, core=0.6), 2, 150),
          Kf(at(kneel, lean=86, hip=(56.0, 80.0), nf=(70.0, 92.0), ff=(36.0, 92.0), head=34, na=10, nr=0.9, fa=20, fr=0.9, breath=-0.1, core=0.2, eye=0.0), 2, 160),
          Kf(at(kneel, lean=92, hip=(58.0, 82.0), nf=(72.0, 92.0), ff=(36.0, 92.0), head=36, na=4, nr=0.9, fa=12, fr=0.9, breath=-0.1, core=0.05, eye=0.0), 2, 500)]
    return [("idle", idle, True), ("walk", walk, True), ("slam", seq(slam), False), ("sweep", seq(sweep), False), ("blast", seq(blast), False),
            ("vent", vent, True), ("hurt", hurt, False), ("death", seq(dk), False)]


# =====================================================================================================================
# CINDER MITE
# =====================================================================================================================
MT = dict(W=24, H=16, FLOOR=15, AX=12)
MT_BASE = dict(hip=(12.0, 15.0), body=(11.5, 10.0), tilt=0.0, legs=0.0, glow=0.6, curl=0.0, fold=0.0, fade=0.0, fi=0, dead=0.0)


def mite(p, fi=0):
    cv = Canvas(MT["W"], MT["H"])
    info = {"hit": set()}
    fi = int(round(p.get("fi", fi)))
    c = p["body"]; tl = p["tilt"]
    R_ = lambda q: add(c, rot(q, tl))
    # legs: three pairs, jointed, splayed; the far ones darker; fold tucks them under (the leap / the cling)
    for k, (ax, side) in enumerate(((-3.0, -1), (0.0, -1), (3.0, -1), (-2.0, 1), (1.0, 1), (4.0, 1))):
        ph = p["legs"] * 6.283 + k * 2.1
        lift = max(0.0, math.sin(ph)) * 1.6
        base = R_((ax * 0.8, 0.6))
        reach = (ax * 1.3 + math.cos(ph) * 1.2) * (1 - p["fold"]) + ax * 0.3 * p["fold"]
        foot = (base[0] + reach + (1.6 if ax > 0 else -1.6), 15.0 - lift - p["fold"] * 4.0 - p["curl"] * 3)
        knee = (lerp(base, foot, 0.5)[0] + (1.0 if ax > 0 else -1.0), min(base[1], foot[1]) - 2.6 + p["fold"] * 1.5)
        b = -1 if side < 0 else 0
        cv.paint({q: (0.0, -0.6, 0.8) for q in line(base, knee) + line(knee, foot)}, "I", bias=b - 1, ao=0)
    # carapace: a sleek iron teardrop of three plates, the seams glowing
    shell = poly_mask([R_(q) for q in ((-6.4, 0.8), (-4.4, -2.6), (-0.6, -4.0), (3.6, -3.4), (6.6, -1.0), (7.0, 1.0), (3.0, 2.4), (-3.0, 2.4))])
    cv.paint(n_plate(shell, bevel=2.0, tilt=(0.0, -0.35), strength=1.5), "I")
    for ox in (-2.6, 1.4):
        seam = [ipt(R_((ox + 0.3 * j, -3.6 + j))) for j in range(6)]
        cv.glow([q for q in seam if q in shell], heat_col(0.3 + 0.5 * p["glow"]), 255)
    cv.glow([ipt(R_((-4.8, 0.0))), ipt(R_((-5.4, 0.6)))], heat_col(0.25 + 0.4 * p["glow"]), 220)   # the burning abdomen tip
    # head + mandibles
    hd = poly_mask([R_(q) for q in ((5.2, -1.6), (8.4, -0.8), (8.8, 1.2), (6.2, 1.8))])
    cv.paint(n_plate(hd, bevel=1.0, tilt=(0.2, -0.3)), "I", bias=1)
    for s_ in (-1, 1):
        cv.paint({q: (0.3, -0.3, 0.9) for q in line(R_((8.4, 0.6 + s_ * 0.6)), R_((10.4, 1.4 + s_ * 1.0 * (1 - p["curl"]))))}, "I", ao=0)
    cv.glow([ipt(R_((7.6, -0.4)))], "E5" if p["glow"] > 0.5 else "E3")
    if p["glow"] > 0.85:
        halo(cv, shell, "E2", 90, behind=True)
    if p["dead"] > 0:
        for q in list(cv.px):
            if hash01(q[0], q[1], 7 + fi) < p["dead"] * 0.8:
                cv.px.pop(q, None)
        for i in range(int(6 * p["dead"])):
            cv.glow([(int(c[0] + (hash01(i, fi, 1) - 0.5) * 14), int(c[1] + (hash01(i, fi, 2) - 0.5) * 8))], "E4" if i % 2 else "E2")
    cv.lights.append((R_((0.0, -3.0)), 8.0, 0.3 * p["glow"]))
    info["tip"] = R_((10.0, 1.0)); info["head"] = R_((7.0, 0.0))
    info["hit"] = set(shell) | set(hd)
    return cv, info


def mite_anims():
    b = MT_BASE
    crawl = [(70, at(b, legs=k / 4, body=(11.5, 10.0 - 0.4 * (k % 2)), glow=0.55 + 0.1 * (k % 2), fi=k), {}) for k in range(4)]
    leap = [(70, at(b, body=(11.0, 11.0), tilt=8, fold=0.2, glow=0.9), {}), (60, at(b, body=(11.0, 11.5), tilt=10, fold=0.4, glow=1.0), {}),
            (50, at(b, body=(12.0, 9.0), tilt=-14, fold=0.9, glow=1.0), {"a": 1}), (50, at(b, body=(12.0, 9.0), tilt=-8, fold=1.0, glow=1.0), {"a": 1}),
            (60, at(b, body=(12.0, 9.5), tilt=6, fold=0.8, glow=1.0), {"a": 1}), (90, at(b, fold=0.3, glow=0.8), {})]
    cling = [(90, at(b, body=(12.0, 9.0), tilt=-70, curl=1.0, fold=0.6, glow=0.8 + 0.2 * (k % 2), legs=k / 4, fi=k), {}) for k in range(4)]
    hurt = [(70, at(b, tilt=-20, glow=1.0, fold=0.5), {}), (90, at(b, tilt=-8, glow=0.7), {})]
    death = [(80, at(b, tilt=-180 * k / 4, body=(12.0, 10.0 - 2 * math.sin(k / 4 * 3.14)), glow=1.0 - k * 0.2, curl=1.0, dead=k * 0.22, fi=k), {}) for k in range(5)]
    return [("crawl", crawl, True), ("leap", leap, False), ("cling", cling, True), ("hurt", hurt, False), ("death", death, False)]


# =====================================================================================================================
# builders
# =====================================================================================================================
def build_generic(name, W, H, AX, FLOOR, drawfn, anims, hurtbox, shoulder_fn, pts=("tip", "head"), cols=("Q1", "Q2", "Q4", "Q5"),
                  build=True, extra_meta=None, root=False):
    import gen_forge_foes as G
    tagged = []
    for tag, frs, loop in anims:
        add_sway(frs, loop=loop, k=0.3)
        if root:
            rt = G.root_motion(frs, AX, keys=("hip", "nf", "ff"))
            for (ms, p, fl), r in zip(frs, rt):
                fl["_root"] = r
        tagged.append((tag, G.run_frames(frs, drawfn, shoulder_fn, cols)))
    anims_, meta = G.build_meta((AX, FLOOR), hurtbox, tagged, pts_names=pts)
    if extra_meta:
        extra_meta(meta, tagged)
    export_sheet(name, W, H, anims_, meta, build=build)
    return f"{name}: {sum(len(f) for _, f in anims_)} frames, " + ", ".join(f"{t}:{len(f)}" for t, f in anims_)


def build(name, BUILD=True):
    if name == "cf_smith":
        return build_generic("cf_smith", SM["W"], SM["H"], SM["AX"], SM["FLOOR"], lambda p: smith(p), smith_anims(),
                             [SM["AX"] - 7, SM["FLOOR"] - 46, 14, 46], lambda p: sm_shoulders(p)[0], pts=("tip", "head", "tongs"),
                             build=BUILD, root=True)
    if name == "cf_wraith":
        def wr_sh(p):
            return (p["hip"][0] + 6, p["hip"][1] - 34)
        return build_generic("cf_wraith", WR["W"], WR["H"], WR["AX"], WR["FLOOR"], lambda p: wraith(p), wraith_anims(),
                             [WR["AX"] - 7, WR["FLOOR"] - 44, 16, 44], wr_sh, pts=("tip", "head"), build=BUILD, root=True)
    if name == "cf_hulk":
        return build_generic("cf_hulk", HK["W"], HK["H"], HK["AX"], HK["FLOOR"], lambda p: hulk(p), hulk_anims(),
                             [HK["AX"] - 12, HK["FLOOR"] - 60, 26, 60], lambda p: hk_shoulders(p)[0], pts=("tip", "head", "core"),
                             cols=("I2", "I3", "I4", "I5"), build=BUILD, root=True)
    if name == "cf_mite":
        return build_generic("cf_mite", MT["W"], MT["H"], MT["AX"], MT["FLOOR"], lambda p: mite(p), mite_anims(),
                             [MT["AX"] - 6, MT["FLOOR"] - 8, 13, 8], lambda p: p["body"], pts=("tip", "head"), build=BUILD)
    return f"{name}: not built yet"
