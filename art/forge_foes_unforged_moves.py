"""The Unforged -- choreography for the 14 weapon types (art side).  Tags in every sheet cf_unforged_<type>:

  idle(6, loop) walk(8, loop) hurt(3) death(10) atk1 atk2 atk3
Keys use the pose of forge_foes_unforged (polar arms about the shoulders: na/nr near, fa/fr far, w = weapon angle,
two = two-handed grip distance).  Flags per key: a=<window #> (active, the hit rect is the union of the weapon pixels
over the window), sm=1 (a motion smear from the previous frame), st=1 (a thrust streak), body=1 (the body is the
weapon: shoulder tackle / shield), kick=1 (the near foot), hold=1 (the engine may hold this frame: charges, guards,
air time), both=1 (the window covers both sides: front and back).
What each atk means (engine side) is in web/src/83_forge_foes.js -> UF_KITS.
"""
import math
from forge_foes_unforged import Pz, BASE

READY = {
    "longsword": dict(na=48, nr=0.78, w=14),
    "katana": dict(na=104, nr=0.5, w=152, sheath=1.0, fa=78, fr=0.62, lean=8),
    "greatsword": dict(na=55, nr=0.58, w=-58, two=7.0, lean=6),
    "maul": dict(na=62, nr=0.7, w=72, two=9.0, lean=8),
    "sns": dict(na=58, nr=0.72, w=8, fa=12, fr=0.62, w2=-84),
    "dual": dict(na=58, nr=0.76, w=18, fa=64, fr=0.72, w2=34, lean=9),
    "spear": dict(na=40, nr=0.5, w=-6, two=11.0, lean=6),
    "staff": dict(na=46, nr=0.55, w=-34, two=10.0),
    "whip": dict(na=70, nr=0.72, w=95, ext=0.12, ext2=1.6),
    "saxe": dict(na=52, nr=0.72, w=8, two=6.0),
    "bow": dict(na=40, nr=0.45, fa=4, fr=0.86, w2=-92, ext=0.0, ext2=1.0),
    "fist": dict(na=-12, nr=0.5, fa=-2, fr=0.55, npref=(0.2, 1.0), fpref=(0.1, 1.0), lean=10),
    "scythe": dict(na=44, nr=0.6, w=-112, two=11.0),
    "bell": dict(na=62, nr=0.7, w=72, w2=88, two=6.0),
}


def R(wt, **kw):
    p = Pz(**READY[wt]); p.update(kw); return p


def K(p, n=1, ms=80, e="io", **fl):
    d = dict(p=p, n=n, ms=ms, e=e); d.update(fl); return d


def at(p, **kw):
    q = dict(p); q.update(kw); return q


# ---------------------------------------------------------------- shared loops
def idle(wt):
    out = []
    for i in range(6):
        s = math.sin(i / 6 * 2 * math.pi)
        r = R(wt)
        hx, hy = r["hip"]
        p = at(r, hip=(hx, hy + 0.7 * s), lean=r["lean"] + 0.8 * s, na=r["na"] + 2.0 * s,
               w=(r["w"] + 2.0 * s) if r["w"] is not None else None, fa=r["fa"] + 2.5 * s, glow=0.5 + 0.5 * s,
               sway=(0.6 * s, 0.0))
        out.append((130, p, {}))
    return out


def walk(wt):
    out = []
    r = R(wt)
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        def foot(phase):
            u = (phase % (2 * math.pi)) / (2 * math.pi)
            if u < 0.5:      # stance: slides back under the hip
                x = 10.0 - 20.0 * (u / 0.5); y = 106.0
            else:            # swing: lifts and comes forward
                k = (u - 0.5) / 0.5
                x = -10.0 + 20.0 * (k * k * (3 - 2 * k)); y = 106.0 - 4.0 * math.sin(k * math.pi)
            return (64.0 + x, y)
        nf, ff = foot(ph), foot(ph + math.pi)
        bob = 1.2 * math.cos(2 * ph)
        p = at(r, hip=(64.0, r["hip"][1] + 0.8 + bob), nf=nf, ff=ff, na=r["na"] - 5 * math.sin(ph),
               fa=r["fa"] + 8 * math.sin(ph), lean=r["lean"] + 2.5, w=(r["w"] - 3 * math.sin(ph)) if r["w"] is not None else None,
               sway=(-2.2 + 0.8 * math.sin(2 * ph), 0.0))
        out.append((95, p, {}))
    return out


def hurt(wt):
    """Elites never flinch: this is the stagger (stance broken / parried). It reels, then sinks to one knee, the heart
    flaring, the weapon arm hanging -- held on the last frame while it can be critted."""
    r = R(wt)
    knee = at(r, hip=(64.0, 84.0), nf=(76.0, 106.0), ff=(52.0, 106.0), lean=26, head=22, na=92, nr=0.95, fa=105, fr=0.85,
              glow=1.0, eye=0.5, sway=(1.0, 0.5))
    return [(70, at(r, hip=(62.0, 71.0), lean=-8, head=-12, na=r["na"] - 25, fa=r["fa"] - 30, sway=(3.0, 0), eye=0.4, glow=1.0), {}),
            (90, at(r, hip=(61.0, 74.0), lean=-4, head=-8, na=r["na"] - 10, fa=r["fa"] - 20, sway=(3.5, 0), eye=0.6, glow=1.0), {}),
            (100, at(knee, hip=(63.0, 80.0), lean=16, head=12), {}),
            (240, knee, {})]


def death(wt):
    r = R(wt)
    keys = [K(r, 1, 90), K(at(r, hip=(61.0, 73.0), lean=-12, head=-16, na=r["na"] - 40, eye=0.6), 2, 100),
            K(at(r, hip=(63.0, 82.0), nf=(72.0, 106.0), ff=(50.0, 106.0), lean=18, head=20, na=95, nr=0.9, fa=100, eye=0.3,
                 glow=-0.5), 2, 130),
            K(at(r, hip=(66.0, 88.0), nf=(74.0, 106.0), ff=(52.0, 106.0), lean=38, head=35, na=100, nr=0.95, fa=110, eye=0.0,
                 glow=-1.0), 1, 160)]
    fr = seq(keys)
    # the binding fails: the blades come apart and fall into a heap
    last = fr[-1][1]
    for k in range(5):
        fr.append((120 if k < 4 else 600, at(last, heap=(k + 1) / 5.0, eye=0.0), {}))
    return fr


# ---------------------------------------------------------------- the moves
# ARRIVAL semantics (forge_foes_kit.seq): K(pose, n, ms, ...) = take n frames to ARRIVE at pose; flags apply to them.
def step(p, dx, lean=None, ff=None):
    """The same pose stepped dx px forward (hip + near foot; far foot trails unless given)."""
    h = p["hip"]; nf = p["nf"]
    q = at(p, hip=(h[0] + dx, h[1]), nf=(nf[0] + dx, nf[1]))
    if ff is not None: q["ff"] = ff
    if lean is not None: q["lean"] = lean
    return q


def swing(r, wind, mid, end, settle=None, n_wind=2, ms_wind=70, hold=160, win=1, n_end=1, ms_strike=45, extra=None):
    """start -> wind-up (the tell, holdable) -> strike (mid, end: active + smear) -> settle -> ready."""
    ks = [K(r, 1, 70), K(wind, n_wind, ms_wind, "out"), K(at(wind, glow=1.0), 1, hold, hold=1),
          K(mid, 1, ms_strike, "lin", a=win, sm=1), K(end, n_end, 50, "out", a=win, sm=1)]
    if settle is not None:
        ks.append(K(settle, 2, 110, "out"))
    if extra:
        ks += extra
    ks.append(K(r, 2, 110))
    return ks


def moves(wt):
    r = R(wt)
    M = {}
    lunge = lambda p, dx, **kw: at(step(p, dx), **kw)
    if wt == "longsword":
        # chain: overhead cut, rising cut, lunging thrust
        w1 = at(r, na=-100, nr=0.82, w=-150, lean=0, hip=(62.0, 70.5), npref=(-0.3, 1))
        m1 = at(r, na=-30, nr=0.92, w=-40, lean=8)
        e1 = lunge(at(r, na=55, nr=0.9, w=75, lean=18, hip=(64.0, 72.5)), 6)
        w2 = lunge(at(r, na=75, nr=0.8, w=135, lean=14, hip=(64.0, 72.5)), 6)
        m2 = lunge(at(r, na=40, nr=0.96, w=45, lean=14, hip=(64.0, 73.5)), 8)
        e2 = lunge(at(r, na=-50, nr=0.92, w=-80, lean=6, hip=(64.0, 71.0)), 8)
        w3 = lunge(at(r, na=150, nr=0.45, w=4, lean=2, hip=(64.0, 71.0)), 6)
        e3 = lunge(at(r, na=30, nr=1.0, w=26, lean=26, hip=(64.0, 77.0), ff=(60.0, 106.0)), 16)
        M["atk1"] = [K(r, 1, 70), K(w1, 2, 70, "out"), K(at(w1, glow=1.0), 1, 150, hold=1),
                     K(m1, 1, 45, "lin", a=1, sm=1), K(e1, 1, 50, "out", a=1, sm=1), K(w2, 2, 70, "io"),
                     K(m2, 1, 45, "lin", a=2, sm=1), K(e2, 1, 50, "out", a=2, sm=1), K(w3, 2, 80, "io"), K(at(w3, glow=1.0), 1, 120, hold=1),
                     K(e3, 2, 45, "snap", a=3, st=1), K(e3, 2, 120), K(r, 2, 110)]
        # charged overhead (two-handed): long tell, the heat climbs, then one great cut
        wind = at(r, na=-100, nr=0.82, w=-125, two=6.0, lean=-4, hip=(62.0, 72.0), head=-6)
        M["atk2"] = swing(r, at(wind), at(r, na=-40, nr=0.92, w=-45, two=6.0, lean=8),
                          lunge(at(r, na=55, nr=0.94, w=80, two=6.0, lean=26, hip=(64.0, 76.0)), 8),
                          settle=lunge(at(r, na=60, nr=0.94, w=84, two=6.0, lean=24, hip=(64.0, 75.0)), 8), hold=300, n_end=2)
        M["atk2"][2]["p"] = at(wind, heat=0.7, glow=1.0, na=-104, w=-130)
        # parry stance -> riposte thrust
        guard = at(r, na=30, nr=0.6, w=-82, lean=0, hip=(62.0, 71.0), fa=40)
        e = lunge(at(r, na=30, nr=1.0, w=26, lean=26, hip=(64.0, 77.0), ff=(60.0, 106.0)), 14)
        M["atk3"] = [K(r, 1, 70), K(guard, 2, 60, "out"), K(at(guard, glow=1.0, lean=-2), 1, 400, hold=1),
                     K(at(r, na=150, nr=0.45, w=4, lean=4), 1, 50), K(e, 2, 45, "snap", a=1, st=1), K(e, 2, 130), K(r, 2, 110)]
    elif wt == "katana":
        crouch = at(r, hip=(62.0, 76.0), lean=24, nf=(76.0, 106.0), ff=(48.0, 106.0), head=6)
        drawn = dict(sheath=0.0)
        dash = at(r, sheath=0.0, na=26, nr=1.0, w=22, lean=32, hip=(82.0, 79.0), nf=(100.0, 106.0), ff=(62.0, 106.0))
        M["atk1"] = [K(r, 1, 70), K(crouch, 2, 70, "out"), K(at(crouch, glow=1.0), 1, 380, hold=1),
                     K(dash, 1, 40, "snap", a=1, st=1), K(at(dash, na=30, w=28, hip=(84.0, 79.0)), 2, 60, a=1),
                     K(at(dash, na=34, w=32, lean=28, hip=(84.0, 78.0)), 2, 140),
                     K(at(r, sheath=0.0, na=90, nr=0.6, w=176, lean=12, hip=(80.0, 72.0), nf=(92.0, 106.0), ff=(68.0, 106.0)), 2, 110),
                     K(at(r, hip=(80.0, 70.0), nf=(90.0, 106.0), ff=(70.0, 106.0)), 2, 120)]
        up_s = at(r, sheath=0.0, na=55, nr=0.95, w=55, lean=16, hip=(66.0, 75.0))
        up_e = lunge(at(r, sheath=0.0, na=-75, nr=0.95, w=-100, lean=2, hip=(64.0, 70.5)), 6)
        dn_e = lunge(at(r, sheath=0.0, na=55, nr=0.95, w=70, lean=22, hip=(64.0, 74.0)), 12)
        M["atk2"] = [K(r, 1, 70), K(at(r, hip=(63.0, 74.0), lean=18), 2, 60, "out"), K(at(r, hip=(63.0, 74.0), lean=18, glow=1.0), 1, 160, hold=1),
                     K(up_s, 1, 40, "lin", a=1), K(up_e, 2, 45, "out", a=1, sm=1), K(at(up_e, na=-80, w=-125), 1, 90),
                     K(dn_e, 2, 45, "snap", a=2, sm=1), K(at(dn_e, na=60, w=76), 2, 120),
                     K(at(dn_e, na=95, nr=0.6, w=176, lean=12), 2, 110), K(at(r, hip=(76.0, 70.0), nf=(88.0, 106.0)), 2, 120)]
        low = at(r, hip=(60.0, 78.0), lean=28, nf=(74.0, 106.0), ff=(44.0, 106.0), head=8)
        cut = lunge(at(r, sheath=0.0, na=-35, nr=1.0, w=-45, lean=14, hip=(66.0, 76.0), ff=(48.0, 106.0)), 4)
        M["atk3"] = [K(r, 1, 70), K(low, 2, 80, "out"), K(at(low, glow=1.0), 1, 600, hold=1),
                     K(at(r, sheath=0.0, na=60, nr=1.0, w=50, lean=24, hip=(64.0, 77.0), nf=(78.0, 106.0), ff=(46.0, 106.0)), 1, 40, "lin", a=1, sm=1),
                     K(cut, 1, 45, "out", a=1, sm=1), K(at(cut, na=-30, w=-38), 2, 140),
                     K(at(cut, na=95, nr=0.6, w=176, lean=10), 2, 120), K(r, 2, 130)]
    elif wt == "greatsword":
        wind = at(r, na=-120, nr=0.75, w=-170, lean=-8, hip=(61.0, 74.0), head=-6, nf=(76.0, 106.0))
        M["atk1"] = swing(r, wind, at(r, na=-50, nr=0.9, w=-60, lean=8, hip=(66.0, 74.0), nf=(80.0, 106.0)),
                          at(r, na=58, nr=0.95, w=88, lean=30, hip=(72.0, 78.0), nf=(88.0, 106.0), ff=(52.0, 106.0), heat=0.4),
                          settle=at(r, na=60, nr=0.95, w=90, lean=30, hip=(72.0, 78.0), nf=(88.0, 106.0), ff=(52.0, 106.0)), hold=500, n_end=2,
                          extra=[K(at(r, na=60, nr=0.95, w=90, lean=28, hip=(72.0, 77.0), nf=(88.0, 106.0), ff=(52.0, 106.0)), 2, 140)])
        M["atk1"][2]["p"] = at(wind, heat=0.8, glow=1.0, na=-124, w=-176)
        back = at(r, na=150, nr=0.8, w=176, lean=-6, hip=(60.0, 72.0), head=-4)
        M["atk2"] = [K(r, 1, 70), K(back, 2, 80, "out"), K(at(back, glow=1.0), 1, 240, hold=1),
                     K(at(r, na=80, nr=0.95, w=110, lean=8), 1, 45, "lin", a=1, sm=1),
                     K(lunge(at(r, na=8, nr=1.0, w=4, lean=18), 8), 1, 45, "lin", a=1, sm=1),
                     K(lunge(at(r, na=-40, nr=0.92, w=-70, lean=14), 8), 1, 55, "out", a=1, sm=1),
                     K(lunge(at(r, na=-30, nr=0.85, w=-60, lean=10, hip=(64.0, 72.0)), 8), 2, 140), K(r, 2, 120)]
        tk = at(r, na=120, nr=0.75, w=170, lean=24, hip=(60.0, 76.0), head=10, nf=(74.0, 106.0), ff=(46.0, 106.0))
        run = at(tk, lean=30, hip=(80.0, 77.0), nf=(94.0, 106.0), ff=(64.0, 106.0), na=130, w=172)
        M["atk3"] = [K(r, 1, 70), K(tk, 2, 80, "out"), K(at(tk, glow=1.0), 1, 280, hold=1),
                     K(run, 3, 55, "lin", a=1, body=1), K(at(run, hip=(84.0, 75.0), lean=20, nf=(96.0, 106.0), ff=(70.0, 106.0), na=110, w=160), 1, 70),
                     K(at(r, na=45, nr=0.95, w=50, lean=16, hip=(86.0, 75.0), nf=(98.0, 106.0), ff=(72.0, 106.0)), 1, 40, "lin", a=2, sm=1),
                     K(at(r, na=-75, nr=0.95, w=-86, lean=2, hip=(88.0, 71.0), nf=(100.0, 106.0), ff=(74.0, 106.0)), 1, 50, "out", a=2, sm=1),
                     K(at(r, na=-78, nr=0.95, w=-90, lean=0, hip=(88.0, 71.0), nf=(100.0, 106.0), ff=(74.0, 106.0)), 3, 140),
                     K(at(r, hip=(86.0, 70.0), nf=(96.0, 106.0), ff=(76.0, 106.0)), 2, 120)]
    elif wt == "maul":
        wind = at(r, na=-110, nr=0.75, w=-150, lean=-8, hip=(61.0, 73.0), head=-6)
        slam = at(r, na=50, nr=0.95, w=72, lean=30, hip=(70.0, 79.0), nf=(84.0, 106.0), ff=(50.0, 106.0))
        M["atk1"] = swing(r, wind, at(r, na=-30, nr=0.95, w=-30, lean=12, hip=(66.0, 75.0)), slam, settle=at(slam, na=54, w=76), hold=320,
                          extra=[K(at(slam, na=54, w=76), 2, 160)])
        sp = []
        for k in range(2):
            o = k * 8.0
            sp += [K(at(r, na=60, nr=0.95, w=90, lean=10, hip=(68.0 + o, 72.0), nf=(78.0 + o, 106.0), ff=(58.0 + o, 106.0)), 1, 45, "lin", sm=1, a=k + 1, both=1),
                   K(at(r, na=0, nr=1.0, w=0, lean=14, hip=(70.0 + o, 72.0), nf=(80.0 + o, 106.0), ff=(62.0 + o, 106.0)), 1, 45, "lin", sm=1, a=k + 1, both=1),
                   K(at(r, na=-70, nr=0.9, w=-90, lean=6, hip=(72.0 + o, 72.0), nf=(84.0 + o, 106.0), ff=(62.0 + o, 106.0)), 1, 50, "lin", sm=1, a=k + 1, both=1),
                   K(at(r, na=-160, nr=0.85, w=-178, lean=-4, hip=(74.0 + o, 72.0), nf=(84.0 + o, 106.0), ff=(66.0 + o, 106.0)), 1, 55, "lin", sm=1)]
        M["atk2"] = [K(r, 1, 70), K(at(r, na=170, nr=0.8, w=178, lean=-10, hip=(62.0, 73.0)), 2, 80, "out"),
                     K(at(r, na=172, nr=0.8, w=-178, lean=-12, hip=(61.0, 73.5), glow=1.0), 1, 240, hold=1)] + sp + \
                    [K(at(r, na=-70, nr=0.85, w=-100, lean=0, hip=(84.0, 71.0), nf=(94.0, 106.0), ff=(76.0, 106.0)), 2, 140),
                     K(at(r, hip=(84.0, 70.0), nf=(94.0, 106.0), ff=(76.0, 106.0)), 2, 130)]
        crouch = at(r, hip=(64.0, 80.0), lean=20, nf=(76.0, 106.0), ff=(50.0, 106.0), na=110, w=160)
        air = at(r, hip=(64.0, 62.0), lean=-6, nf=(70.0, 92.0), ff=(56.0, 96.0), na=-120, nr=0.8, w=-170, head=-6)
        land = at(r, hip=(68.0, 80.0), lean=32, nf=(80.0, 106.0), ff=(50.0, 106.0), na=55, nr=0.95, w=80)
        M["atk3"] = [K(r, 1, 70), K(crouch, 2, 90, "out"), K(at(crouch, glow=1.0), 1, 140), K(air, 2, 70, "out"), K(at(air, glow=1.0), 1, 200, hold=1),
                     K(at(r, hip=(66.0, 70.0), lean=6, nf=(76.0, 100.0), ff=(56.0, 102.0), na=-50, nr=0.95, w=-40), 1, 40, "lin", a=1, sm=1),
                     K(land, 1, 50, "slam", a=1, sm=1), K(at(land, na=58, w=82), 3, 160), K(r, 2, 130)]
    elif wt == "sns":
        wind = at(r, na=-90, nr=0.8, w=-140, lean=2, fa=20)
        e1 = lunge(at(r, na=55, nr=0.92, w=70, lean=16, fa=20), 6)
        w2 = lunge(at(r, na=80, nr=0.8, w=140, lean=12, fa=20), 6)
        e2 = lunge(at(r, na=-50, nr=0.95, w=-70, lean=6, fa=20), 10)
        M["atk1"] = [K(r, 1, 70), K(wind, 2, 70, "out"), K(at(wind, glow=1.0), 1, 150, hold=1),
                     K(at(r, na=-20, nr=0.92, w=-30, lean=8, fa=20), 1, 45, "lin", a=1, sm=1), K(e1, 1, 50, "out", a=1, sm=1),
                     K(w2, 2, 70), K(lunge(at(r, na=42, nr=0.96, w=40, lean=14, fa=20, hip=(64.0, 73.0)), 8), 1, 45, "lin", a=2, sm=1), K(e2, 1, 50, "out", a=2, sm=1),
                     K(e2, 2, 130), K(r, 2, 110)]
        brace = at(r, fa=-10, fr=0.45, w2=-80, lean=20, hip=(62.0, 75.0), nf=(74.0, 106.0), ff=(46.0, 106.0), na=110, w=150)
        bash = at(r, fa=0, fr=0.95, w2=-86, lean=26, hip=(80.0, 76.0), nf=(96.0, 106.0), ff=(64.0, 106.0), na=120, w=160)
        M["atk2"] = [K(r, 1, 70), K(brace, 2, 80, "out"), K(at(brace, glow=1.0), 1, 300, hold=1), K(bash, 3, 55, "lin", a=1, body=1),
                     K(at(bash, fa=4, fr=0.9, lean=18, hip=(84.0, 73.0), nf=(96.0, 106.0), ff=(70.0, 106.0), na=80, w=60), 2, 140),
                     K(at(r, hip=(84.0, 70.0), nf=(94.0, 106.0), ff=(74.0, 106.0)), 2, 120)]
        guard = at(r, fa=-6, fr=0.55, w2=-80, lean=4, hip=(63.0, 72.0), na=120, w=172)
        thr = lunge(at(r, fa=40, fr=0.6, w2=-60, na=30, nr=1.0, w=26, lean=26, hip=(64.0, 77.0), ff=(60.0, 106.0)), 14)
        M["atk3"] = [K(r, 1, 70), K(guard, 2, 60, "out"), K(at(guard, glow=1.0, lean=2), 1, 400, hold=1),
                     K(thr, 2, 45, "snap", a=1, st=1), K(thr, 2, 140), K(r, 2, 120)]
    elif wt == "dual":
        fl = [K(r, 1, 60), K(at(r, na=-40, w=-90, fa=-30, w2=-80, lean=4), 2, 60, "out"), K(at(r, na=-40, w=-90, fa=-30, w2=-80, lean=4, glow=1.0), 1, 140, hold=1)]
        for k in range(3):
            x = 66.0 + k * 4
            fl += [K(at(r, na=50, nr=0.95, w=60, fa=-50, fr=0.85, w2=-100, lean=16, hip=(x, 73.0), nf=(x + 12, 106.0)), 1, 45, "lin", sm=1, a=2 * k + 1),
                   K(at(r, na=-50, nr=0.9, w=-110, fa=60, fr=0.95, w2=70, lean=16, hip=(x + 2, 73.0), nf=(x + 12, 106.0)), 1, 45, "lin", sm=1, a=2 * k + 2)]
        M["atk1"] = fl + [K(at(r, na=-30, nr=0.85, w=-80, fa=20, w2=10, lean=10, hip=(80.0, 72.0), nf=(90.0, 106.0)), 2, 120),
                          K(at(r, hip=(78.0, 71.0), nf=(88.0, 106.0)), 2, 110)]
        coil = at(r, hip=(60.0, 78.0), lean=30, na=170, nr=0.8, w=178, fa=170, fr=0.8, w2=-178, nf=(74.0, 106.0), ff=(44.0, 106.0))
        thru = at(r, hip=(84.0, 76.0), lean=34, na=20, nr=1.0, w=10, fa=-10, fr=1.0, w2=-20, nf=(100.0, 106.0), ff=(68.0, 106.0))
        M["atk2"] = [K(r, 1, 60), K(coil, 2, 70, "out"), K(at(coil, glow=1.0), 1, 300, hold=1), K(thru, 2, 40, "snap", a=1, st=1),
                     K(at(thru, hip=(90.0, 75.0), lean=28, na=60, w=90, fa=40, w2=60, nf=(102.0, 106.0), ff=(76.0, 106.0)), 2, 50, sm=1, a=1),
                     K(at(thru, hip=(90.0, 74.0), lean=22, na=70, nr=0.9, w=100, fa=60, fr=0.9, w2=80, nf=(100.0, 106.0), ff=(78.0, 106.0)), 2, 140),
                     K(at(r, hip=(88.0, 71.0), nf=(98.0, 106.0), ff=(78.0, 106.0)), 2, 120)]
        cy = [K(r, 1, 60), K(at(r, na=150, w=170, fa=160, w2=-170, lean=-6, hip=(62.0, 73.0)), 2, 70, "out"),
              K(at(r, na=150, w=170, fa=160, w2=-170, lean=-6, hip=(62.0, 73.0), glow=1.0), 1, 200, hold=1)]
        for k in range(3):
            x = 64.0 + k * 6
            for j, (na, fa) in enumerate(((-90, 90), (0, 180), (90, -90), (180, 0))):
                cy.append(K(at(r, na=na, nr=1.0, w=na, fa=fa, fr=1.0, w2=fa, lean=4 + 4 * (j % 2), hip=(x + j * 1.5, 71.5),
                               nf=(x + 8 + j * 1.5, 106.0), ff=(x - 8 + j * 1.5, 106.0)), 1, 42, "lin", sm=1, a=k + 1, both=1))
        M["atk3"] = cy + [K(at(r, hip=(84.0, 72.0), nf=(94.0, 106.0), ff=(76.0, 106.0)), 2, 140), K(at(r, hip=(84.0, 71.0), nf=(94.0, 106.0), ff=(76.0, 106.0)), 2, 110)]
    elif wt == "spear":
        back = at(r, na=80, nr=0.35, w=-4, lean=-2, hip=(60.0, 72.0), two=12.0)
        p1 = lunge(at(r, na=28, nr=1.0, w=22, lean=22, two=6.0, hip=(64.0, 76.0)), 8)
        b2 = lunge(at(r, na=60, nr=0.4, w=-2, lean=6, two=12.0, hip=(64.0, 72.0)), 6)
        p2 = lunge(at(r, na=30, nr=1.0, w=24, lean=26, two=6.0, hip=(64.0, 77.0), ff=(60.0, 106.0)), 14)
        M["atk1"] = [K(r, 1, 70), K(back, 2, 70, "out"), K(at(back, glow=1.0), 1, 160, hold=1), K(p1, 2, 40, "snap", a=1, st=1),
                     K(b2, 2, 60), K(p2, 2, 40, "snap", a=2, st=1), K(p2, 2, 140), K(r, 2, 110)]
        crouch = at(r, na=60, nr=0.4, w=-2, lean=30, hip=(60.0, 78.0), nf=(72.0, 106.0), ff=(44.0, 106.0))
        run = []
        for k in range(4):
            ph = k / 4 * 2 * math.pi
            run.append(K(at(r, na=34, nr=0.85, w=20, two=8.0, lean=28, hip=(70.0, 74.0 + math.cos(2 * ph)),
                            nf=(70.0 + 12 * math.cos(ph), 106.0 - 3 * max(0, math.sin(ph))), ff=(70.0 - 12 * math.cos(ph), 106.0 - 3 * max(0, -math.sin(ph))), sway=(-4.0, 0)),
                         1, 70, "lin", a=1, hold=1 if k == 3 else 0))
        fin = lunge(at(r, na=30, nr=1.0, w=24, lean=28, two=6.0, hip=(66.0, 77.0), ff=(60.0, 106.0)), 10)
        M["atk2"] = [K(r, 1, 70), K(crouch, 2, 80, "out"), K(at(crouch, glow=1.0), 1, 380, hold=1)] + run + \
                    [K(fin, 2, 50, "snap", a=2, st=1), K(fin, 2, 130), K(at(r, hip=(74.0, 71.0), nf=(84.0, 106.0), ff=(64.0, 106.0)), 2, 130)]
        hop = at(r, hip=(58.0, 66.0), nf=(62.0, 98.0), ff=(50.0, 100.0), lean=-8, na=70, nr=0.4, w=-10)
        coil = at(r, hip=(62.0, 76.0), nf=(74.0, 106.0), ff=(46.0, 106.0), lean=20, na=80, nr=0.35, w=-4)
        fl = at(r, na=30, nr=1.0, w=24, lean=32, hip=(84.0, 79.0), nf=(100.0, 106.0), ff=(66.0, 106.0), two=5.0)
        M["atk3"] = [K(r, 1, 70), K(hop, 2, 80, "out", hold=1), K(coil, 2, 70, "slam"), K(at(coil, glow=1.0), 1, 200),
                     K(fl, 2, 40, "snap", a=1, st=1), K(at(fl, hip=(86.0, 76.0)), 3, 150), K(at(r, hip=(84.0, 71.0), nf=(94.0, 106.0), ff=(74.0, 106.0)), 2, 130)]
    elif wt == "staff":
        sp = [K(r, 1, 70), K(at(r, na=150, nr=0.7, w=-150, lean=-4), 2, 70, "out"), K(at(r, na=150, nr=0.7, w=-150, lean=-4, glow=1.0), 1, 160, hold=1)]
        for k, (na, w, a, both) in enumerate([(60, 80, 1, 0), (20, 30, 1, 0), (150, 160, 2, 1), (110, 125, 2, 1), (55, 65, 3, 0), (25, 30, 3, 0)]):
            sp.append(K(at(r, na=na, nr=0.85, w=w, lean=10, hip=(66.0 + k * 2, 72.0), nf=(78.0 + k * 2, 106.0)), 1, 50, "lin", sm=1, a=a, both=both))
        M["atk1"] = sp + [K(at(r, hip=(76.0, 71.0), nf=(86.0, 106.0), ff=(64.0, 106.0)), 2, 130), K(at(r, hip=(76.0, 70.0), nf=(86.0, 106.0), ff=(66.0, 106.0)), 2, 110)]
        plant = at(r, na=70, nr=0.8, w=88, lean=20, hip=(62.0, 76.0))
        vault = at(r, na=80, nr=0.9, w=95, lean=-10, hip=(64.0, 60.0), nf=(80.0, 86.0), ff=(56.0, 92.0))
        kick = at(r, na=120, nr=0.8, w=150, lean=-18, hip=(66.0, 60.0), nf=(92.0, 76.0), ff=(60.0, 88.0), sway=(3, 2))
        M["atk2"] = [K(r, 1, 70), K(plant, 2, 70, "out"), K(at(plant, glow=1.0), 1, 260, hold=1), K(vault, 2, 70, "out", hold=1),
                     K(kick, 2, 45, "snap", kick=1, a=1), K(at(kick, nf=(90.0, 80.0), lean=-12), 1, 80, kick=1, a=1, hold=1),
                     K(at(r, hip=(64.0, 74.0), nf=(74.0, 106.0), ff=(54.0, 106.0), lean=14), 2, 90), K(r, 2, 120)]
        low = at(r, na=110, nr=0.6, w=170, lean=24, hip=(60.0, 78.0), nf=(74.0, 106.0), ff=(44.0, 106.0))
        M["atk3"] = [K(r, 1, 70), K(low, 2, 80, "out"), K(at(low, glow=1.0), 1, 260, hold=1),
                     K(at(r, na=60, nr=0.95, w=10, two=8.0, lean=26, hip=(70.0, 78.0), nf=(84.0, 106.0), ff=(50.0, 106.0)), 2, 45, "snap", sm=1, a=1),
                     K(at(r, na=30, nr=0.95, w=35, two=8.0, lean=14, hip=(72.0, 74.0), nf=(84.0, 106.0), ff=(60.0, 106.0)), 1, 40, "lin", sm=1, a=2), K(at(r, na=-80, nr=0.95, w=-80, two=8.0, lean=0, hip=(74.0, 68.0), nf=(84.0, 106.0), ff=(62.0, 104.0)), 2, 50, "out", sm=1, a=2),
                     K(at(r, na=-86, nr=0.95, w=-86, two=8.0, lean=-2, hip=(74.0, 68.0), nf=(84.0, 106.0), ff=(62.0, 104.0)), 3, 140),
                     K(at(r, hip=(74.0, 70.0), nf=(84.0, 106.0), ff=(64.0, 106.0)), 2, 130)]
    elif wt == "whip":
        up = at(r, na=-120, nr=0.85, w=-150, ext=0.3, ext2=-1.2, lean=-4, hip=(62.0, 71.0))
        crack = at(r, na=10, nr=1.0, w=-4, ext=1.0, ext2=0.15, lean=16, hip=(68.0, 72.0), nf=(80.0, 106.0))
        M["atk1"] = [K(r, 1, 70), K(up, 2, 80, "out"), K(at(up, glow=1.0), 1, 240, hold=1),
                     K(at(r, na=-60, nr=0.95, w=-70, ext=0.6, ext2=-0.6, lean=6), 1, 45, "lin"),
                     K(crack, 2, 45, "out", a=1), K(at(crack, na=20, w=8, ext=0.9, ext2=0.6), 1, 80, a=1),
                     K(at(crack, na=50, nr=0.9, w=60, ext=0.4, ext2=1.6, lean=12), 2, 110), K(r, 2, 120)]
        wind = at(r, na=150, nr=0.8, w=170, ext=0.3, ext2=1.0, lean=4)
        lash = at(r, na=30, nr=1.0, w=14, ext=1.0, ext2=0.0, lean=14, hip=(68.0, 73.0), nf=(80.0, 106.0))
        M["atk2"] = [K(r, 1, 70), K(wind, 2, 80, "out"), K(at(wind, glow=1.0), 1, 200, hold=1), K(lash, 2, 45, "snap", a=1),
                     K(at(lash, na=34, w=16, ext=0.95, ext2=0.1), 1, 140, hold=1),
                     K(at(r, na=120, nr=0.8, w=160, ext=0.3, ext2=-1.0, lean=-8, hip=(64.0, 72.0), nf=(78.0, 106.0)), 2, 70),
                     K(at(r, na=30, nr=0.95, w=40, ext=0.45, ext2=0.3, lean=18, hip=(70.0, 75.0), nf=(82.0, 106.0)), 2, 45, "snap", a=2),
                     K(at(r, hip=(70.0, 71.0), nf=(80.0, 106.0)), 2, 130)]
        tc = [K(r, 1, 70)]
        for k in range(6):
            tc.append(K(at(r, na=-95, nr=0.95, w=-90 + k * 120, ext=0.55, ext2=1.6, lean=-2, glow=k / 5), 1, 60, "lin", hold=1 if k == 5 else 0))
        M["atk3"] = tc + [K(at(r, na=-80, nr=1.0, w=-70, ext=0.8, ext2=0.8, lean=4), 1, 45, "lin"),
                          K(at(r, na=20, nr=1.0, w=12, ext=1.0, ext2=0.4, lean=22, hip=(70.0, 75.0), nf=(84.0, 106.0)), 2, 50, "out", a=1),
                          K(at(r, na=30, nr=1.0, w=30, ext=0.8, ext2=1.0, lean=20, hip=(70.0, 75.0), nf=(84.0, 106.0)), 3, 130),
                          K(at(r, hip=(70.0, 71.0), nf=(80.0, 106.0)), 2, 120)]
    elif wt == "saxe":
        wind = at(r, na=-90, nr=0.8, w=-140, lean=0)
        M["atk1"] = [K(r, 1, 70), K(wind, 2, 70, "out"), K(at(wind, glow=1.0), 1, 150, hold=1),
                     K(at(r, na=-20, nr=0.92, w=-30, lean=8), 1, 45, "lin", a=1, sm=1), K(lunge(at(r, na=50, nr=0.95, w=70, lean=18, hip=(64.0, 73.0)), 6), 1, 50, "out", a=1, sm=1),
                     K(lunge(at(r, na=80, nr=0.8, w=140, lean=14, hip=(64.0, 73.0)), 6), 2, 70),
                     K(lunge(at(r, na=42, nr=0.96, w=42, lean=14, hip=(64.0, 74.0)), 10), 1, 45, "lin", a=2, sm=1),
                     K(lunge(at(r, na=-40, nr=0.92, w=-60, lean=6, hip=(64.0, 72.0)), 10), 1, 50, "out", a=2, sm=1),
                     K(lunge(at(r, na=-40, nr=0.92, w=-60, lean=6, hip=(64.0, 71.0)), 8), 2, 130), K(r, 2, 110)]
        low = at(r, na=120, nr=0.75, w=150, lean=22, hip=(60.0, 78.0), nf=(72.0, 106.0), ff=(46.0, 106.0), heat=0.5)
        M["atk2"] = [K(r, 1, 70), K(low, 2, 80, "out"), K(at(low, glow=1.0, heat=0.7), 1, 380, hold=1),
                     K(at(r, na=40, nr=0.95, w=30, lean=14, hip=(68.0, 75.0), nf=(82.0, 106.0), heat=0.8), 1, 45, "lin", a=1, sm=1),
                     K(at(r, na=-70, nr=0.95, w=-80, lean=0, hip=(72.0, 70.0), nf=(84.0, 106.0), axe=1.0, heat=1.0), 2, 50, "out", a=1, sm=1),
                     K(at(r, na=-80, nr=0.95, w=-92, lean=-2, hip=(72.0, 70.0), nf=(84.0, 106.0), axe=1.0, heat=0.8), 3, 130),
                     K(at(r, hip=(72.0, 70.0), nf=(82.0, 106.0), axe=1.0, heat=0.6), 2, 120)]
        wind = at(r, na=-110, nr=0.85, w=-150, lean=-8, hip=(62.0, 73.0), axe=1.0, heat=0.9)
        slam = at(r, na=55, nr=0.95, w=80, lean=30, hip=(70.0, 79.0), nf=(84.0, 106.0), ff=(50.0, 106.0), axe=1.0, heat=1.0)
        M["atk3"] = [K(at(r, axe=1.0, heat=0.6), 1, 70), K(wind, 2, 80, "out"), K(at(wind, glow=1.0), 1, 300, hold=1),
                     K(at(r, na=-30, nr=0.95, w=-30, lean=12, axe=1.0, heat=1.0), 1, 45, "lin", a=1, sm=1), K(slam, 1, 55, "slam", a=1, sm=1),
                     K(at(slam, na=58, w=82, heat=0.5), 4, 170), K(at(r, na=40, w=40, lean=14, hip=(68.0, 74.0), nf=(80.0, 106.0), axe=0.0), 2, 110),
                     K(r, 2, 130)]
    elif wt == "bow":
        nock = at(r, na=10, nr=0.6, fa=-2, fr=0.95, w2=-90, ext=0.3, ext2=1.0)
        drawn = at(r, na=170, nr=0.25, fa=-4, fr=0.95, w2=-92, ext=1.0, ext2=1.0, lean=2, heat=0.3)
        loose = at(r, na=160, nr=0.3, fa=-6, fr=0.95, w2=-94, ext=0.0, ext2=0.0, lean=-4, hip=(62.0, 70.0))
        M["atk1"] = [K(r, 1, 70), K(nock, 2, 60, "out"), K(drawn, 2, 70, "out"), K(at(drawn, glow=1.0), 1, 260, hold=1), K(loose, 2, 60, "snap", shot=1),
                     K(r, 2, 110)]
        deep = at(r, na=176, nr=0.35, fa=-6, fr=1.0, w2=-94, ext=1.0, ext2=1.0, lean=-6, hip=(60.0, 73.0), nf=(74.0, 106.0), ff=(46.0, 106.0), heat=1.0)
        M["atk2"] = [K(r, 1, 70), K(nock, 2, 60, "out"), K(at(drawn, lean=-2, hip=(62.0, 72.0), nf=(74.0, 106.0), ff=(48.0, 106.0)), 2, 80, "out"),
                     K(at(deep, glow=1.0), 1, 600, hold=1),
                     K(at(deep, ext=0.0, ext2=0.0, lean=-12, hip=(56.0, 72.0), nf=(70.0, 106.0), ff=(42.0, 106.0), heat=0.0), 2, 70, "snap", shot=1),
                     K(at(r, hip=(58.0, 70.0), nf=(68.0, 106.0), ff=(46.0, 106.0)), 2, 130), K(r, 2, 110)]
        stab_w = at(r, na=110, nr=0.5, fa=60, fr=0.6, w2=-60, ext=0.0, ext2=0.0, lean=10, hip=(62.0, 74.0))
        stab = lunge(at(r, na=34, nr=1.0, fa=70, fr=0.6, w2=-60, lean=28, hip=(64.0, 78.0), ff=(58.0, 106.0)), 10)
        hopb = at(drawn, lean=-8, hip=(66.0, 64.0), nf=(78.0, 96.0), ff=(56.0, 98.0))
        M["atk3"] = [K(r, 1, 70), K(stab_w, 2, 70, "out"), K(at(stab_w, glow=1.0), 1, 200, hold=1), K(stab, 2, 45, "snap", a=1, st=1),
                     K(at(stab, na=10, nr=0.95), 1, 110), K(hopb, 2, 70, "out", hold=1),
                     K(at(loose, lean=-10, hip=(62.0, 66.0), nf=(74.0, 98.0), ff=(52.0, 100.0)), 2, 60, "snap", shot=1),
                     K(at(r, hip=(60.0, 72.0), nf=(70.0, 106.0), ff=(48.0, 106.0)), 2, 110), K(r, 1, 100)]
    elif wt == "fist":
        set_ = at(r, na=10, nr=0.4, fa=20, fr=0.4, lean=22, hip=(64.0, 75.0))
        j1 = lunge(at(r, na=40, nr=1.0, fa=20, fr=0.45, lean=28, hip=(64.0, 77.0)), 4)
        j2 = lunge(at(r, na=10, nr=0.45, fa=38, fr=1.0, lean=30, hip=(64.0, 78.0)), 8)
        hook = lunge(at(r, na=34, nr=1.0, npref=(-0.5, 1.0), fa=20, fr=0.4, lean=30, hip=(64.0, 78.0), ff=(60.0, 106.0)), 12)
        M["atk1"] = [K(r, 1, 60), K(set_, 1, 60), K(at(set_, glow=1.0), 1, 130, hold=1), K(j1, 2, 40, "snap", a=1, st=1),
                     K(j2, 2, 40, "snap", a=2, st=1), K(at(j2, na=60, nr=0.5), 1, 60),
                     K(hook, 2, 45, "snap", a=3, sm=1), K(hook, 2, 120), K(at(r, hip=(76.0, 71.0), nf=(86.0, 106.0), ff=(66.0, 106.0)), 2, 110)]
        wind = at(r, na=160, nr=0.6, fa=10, fr=0.5, lean=-6, hip=(60.0, 76.0), nf=(74.0, 106.0), ff=(46.0, 106.0), heat=0.8)
        palm = at(r, na=34, nr=1.0, fa=150, fr=0.6, lean=30, hip=(76.0, 79.0), nf=(92.0, 106.0), ff=(58.0, 106.0), nopen=1.5, heat=1.0)
        M["atk2"] = [K(r, 1, 70), K(wind, 2, 90, "out"), K(at(wind, glow=1.0), 1, 520, hold=1), K(palm, 2, 50, "snap", a=1, st=1),
                     K(at(palm, heat=0.6), 3, 150), K(at(r, hip=(74.0, 71.0), nf=(86.0, 106.0), ff=(64.0, 106.0)), 2, 120)]
        crouch = at(r, hip=(62.0, 78.0), lean=18, nf=(72.0, 106.0), ff=(48.0, 106.0), na=110, fa=120)
        air = at(r, hip=(66.0, 56.0), lean=-14, nf=(86.0, 52.0), ff=(58.0, 86.0), na=-150, nr=0.8, fa=170, fr=0.8, sway=(2, 4))
        land = at(r, hip=(70.0, 78.0), lean=24, nf=(84.0, 106.0), ff=(54.0, 106.0), na=60, fa=120)
        M["atk3"] = [K(r, 1, 60), K(crouch, 2, 80, "out"), K(at(crouch, glow=1.0), 1, 140), K(air, 2, 70, "out"), K(at(air, glow=1.0), 1, 240, hold=1),
                     K(at(r, hip=(68.0, 64.0), lean=10, nf=(84.0, 98.0), ff=(58.0, 90.0), na=-120, fa=150), 1, 40, "lin", kick=1, a=1),
                     K(land, 1, 50, "slam", kick=1, a=1), K(at(land, na=40, fa=100, lean=22), 3, 150),
                     K(at(r, hip=(70.0, 71.0), nf=(80.0, 106.0), ff=(60.0, 106.0)), 2, 120)]
    elif wt == "scythe":
        back = at(r, na=160, nr=0.75, w=150, lean=-8, hip=(61.0, 72.0), head=-4)
        M["atk1"] = [K(r, 1, 70), K(back, 2, 80, "out"), K(at(back, glow=1.0), 1, 300, hold=1),
                     K(at(r, na=100, nr=0.9, w=-170, lean=0), 1, 45, "lin", sm=1, a=1, both=1),
                     K(lunge(at(r, na=40, nr=1.0, w=-110, lean=12, hip=(64.0, 73.0)), 4), 1, 45, "lin", sm=1, a=1, both=1),
                     K(lunge(at(r, na=-10, nr=1.0, w=-40, lean=16, hip=(64.0, 74.0)), 6), 1, 55, "out", sm=1, a=1, both=1),
                     K(lunge(at(r, na=-20, nr=0.95, w=-30, lean=14, hip=(64.0, 74.0)), 6), 3, 140), K(r, 2, 120)]
        hk = at(r, na=-60, nr=0.8, w=-70, lean=-2, hip=(62.0, 71.0), flip=1.0)
        pull = lunge(at(r, na=22, nr=1.0, w=4, lean=24, hip=(64.0, 77.0), flip=1.0), 8)
        M["atk2"] = [K(r, 1, 70), K(hk, 2, 70, "out"), K(at(hk, glow=1.0), 1, 260, hold=1), K(pull, 2, 45, "snap", sm=1, a=1),
                     K(at(pull, na=30, w=14), 1, 140, hold=1), K(at(r, na=-40, nr=0.8, w=-80, lean=-2, hip=(66.0, 72.0), nf=(80.0, 106.0), flip=1.0), 2, 70),
                     K(at(r, na=40, nr=1.0, w=10, lean=22, hip=(70.0, 78.0), nf=(84.0, 106.0), flip=1.0), 2, 50, "snap", sm=1, a=2),
                     K(at(r, hip=(70.0, 71.0), nf=(80.0, 106.0)), 2, 130)]
        lean_in = at(r, na=-40, nr=0.9, w=-40, lean=24, hip=(62.0, 76.0), nf=(76.0, 106.0), ff=(46.0, 106.0))
        gone = at(r, na=-30, nr=1.0, w=-30, lean=30, hip=(76.0, 66.0), nf=(92.0, 92.0), ff=(62.0, 96.0), sway=(-4, 2), dark=1.0)
        M["atk3"] = [K(r, 1, 70), K(lean_in, 2, 70, "out"), K(at(lean_in, glow=1.0), 1, 240, hold=1), K(gone, 2, 60, hold=1),
                     K(at(r, na=150, nr=0.8, w=150, lean=-4, hip=(64.0, 72.0)), 1, 90),
                     K(at(r, na=60, nr=1.0, w=-150, lean=10, hip=(68.0, 73.0), nf=(80.0, 106.0)), 1, 45, "lin", sm=1, a=1, both=1),
                     K(at(r, na=-10, nr=1.0, w=-40, lean=14, hip=(70.0, 74.0), nf=(82.0, 106.0)), 2, 50, "out", sm=1, a=1, both=1),
                     K(at(r, hip=(70.0, 71.0), nf=(80.0, 106.0)), 2, 140)]
    elif wt == "bell":
        wind = at(r, na=-110, nr=0.8, w=-130, w2=-150, lean=-6, hip=(62.0, 72.0))
        e1 = at(r, na=45, nr=0.95, w=60, w2=40, lean=24, hip=(70.0, 76.0), nf=(84.0, 106.0))
        M["atk1"] = [K(r, 1, 70), K(wind, 2, 80, "out"), K(at(wind, glow=1.0), 1, 240, hold=1),
                     K(at(r, na=-40, nr=0.95, w=-30, w2=-60, lean=8), 1, 45, "lin", sm=1, a=1), K(e1, 1, 55, "slam", sm=1, a=1),
                     K(at(r, na=110, nr=0.85, w=150, w2=150, lean=10, hip=(70.0, 74.0), nf=(84.0, 106.0)), 2, 90),
                     K(at(r, na=38, nr=1.0, w=30, w2=20, lean=22, hip=(74.0, 77.0), nf=(88.0, 106.0)), 2, 50, "snap", sm=1, a=2),
                     K(at(r, na=40, nr=1.0, w=34, w2=40, lean=20, hip=(74.0, 76.0), nf=(88.0, 106.0)), 3, 150),
                     K(at(r, hip=(74.0, 71.0), nf=(84.0, 106.0)), 2, 120)]
        wind = at(r, na=-140, nr=0.8, w=-160, w2=170, lean=-12, hip=(60.0, 74.0), head=-8)
        slam = at(r, na=50, nr=0.95, w=70, w2=80, lean=30, hip=(70.0, 80.0), nf=(84.0, 106.0), ff=(50.0, 106.0), heat=0.5)
        M["atk2"] = [K(r, 1, 70), K(wind, 2, 90, "out"), K(at(wind, heat=0.9, glow=1.0, na=-145, w=-166, w2=175), 1, 650, hold=1),
                     K(at(r, na=-50, nr=0.95, w=-50, w2=-70, lean=10), 1, 45, "lin", sm=1, a=1), K(slam, 2, 55, "slam", sm=1, a=1),
                     K(at(slam, na=54, w=74, w2=88, heat=0.0), 4, 170), K(r, 2, 130)]
        up = at(r, na=-90, nr=0.9, w=-90, w2=-100, lean=0, heat=0.6)
        M["atk3"] = [K(r, 1, 70), K(up, 2, 80, "out"), K(at(up, glow=1.0), 1, 320, hold=1),
                     K(at(r, na=0, nr=1.0, w=0, w2=10, lean=8, hip=(66.0, 72.0)), 1, 45, "lin", sm=1, a=1, both=1),
                     K(at(r, na=90, nr=1.0, w=90, w2=90, lean=10, hip=(66.0, 73.0)), 1, 45, "lin", sm=1, a=1, both=1),
                     K(at(r, na=170, nr=1.0, w=176, w2=176, lean=0, hip=(66.0, 73.0)), 2, 50, "out", sm=1, a=1, both=1),
                     K(at(r, na=175, nr=0.95, w=180, w2=178, lean=-2, hip=(66.0, 73.0)), 3, 150), K(r, 2, 130)]
    return M


def seq(keys):
    from forge_foes_kit import seq as _s
    return _s(keys)
