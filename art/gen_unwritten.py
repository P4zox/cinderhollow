#!/usr/bin/env python3
"""The Unwritten -- main boss of the Ashen Archives (A6 "The Inkwell").

    python3 art/gen_unwritten.py                 build unwritten + unwritten_p2 (+ meta) and every fx_ink_* / ar2_* sheet
    python3 art/gen_unwritten.py --preview       previews + meta only (no Aseprite)
    python3 art/gen_unwritten.py --only reap,cast --preview

The Scribe's unfinished story of the Root, given hunger: a tall, gaunt reaper of ink with a razor-peaked hood,
long bone arms and a spine-hafted scythe whose blade is a giant quill nib.  Built from the approved concept
(art/concepts/unwritten.png, generator art/concepts/gen_unwritten.py -- its drawing code is reused through
art/unwritten_rig.py).  Faces RIGHT.  Frame 224x176, anchor (114, 176) = the floor under its lowest wisp; the
engine floats it at a variable height above the floor.

Tags (same frames in both sheets; unwritten_p2 = phase 2: torn hood, burning skull, crown of script, cloak on fire):
    idle(8 loop)  drift(6 loop)  reap(12: scythe chop, active 4-6)  cast(10: glyph ring, spawn 5, channel-hold 6)
    write(10: scythe stabbed into the floor, spawn 4)  sink(7)  rise(7)  transform(14: phase-2 change)
    stagger(4)  death(14)
"""
import json
import math
import os
import sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import unwritten_rig as R  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

C = R.C
BUILD = "--preview" not in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
ASSETS = os.path.join(os.path.dirname(ART), "assets")
PV = os.path.join(ART, "previews")

# =========================================================================== base pose
NEAR = dict(sh=(88, 51), wrist=(94.5, 76.5), pref=(-0.3, 1), hdir=-15, curl=55, spread=11, thumb=-80)
FAR = dict(sh=(54, 51), wrist=(40, 84), pref=(-1, 0.1), hdir=105, curl=12, spread=13, thumb=-70, drape=(-2, 13))
SC0 = dict(g=(94.5, 76.5), ang=-94.0, lh=66.65, lb=47.6, s=1, k=0.88)
BASE = dict(ph=0.0, bob=0.0, lean=0.0, wind=0.0, htilt=0.0, near=NEAR, far=FAR, sc=SC0, order=R.ORDER_IDLE,
            chain_swing=0.0, eyes=0.0, lift=0.0)


def P_(base=BASE, **kw):
    d = dict(base)
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict) and k in ("near", "far", "sc"):
            nd = dict(d[k]); nd.update(v); d[k] = nd
        else:
            d[k] = v
    return d


def rot_about(q, c, deg):
    v = C.rotv(C.sub(q, c), deg)
    return (c[0] + v[0], c[1] + v[1])


def leaned(q, lean):
    """a point authored for an upright body, carried along when the torso leans about the waist"""
    return rot_about(q, C.PIV, lean)


def sc_leaned(sc, lean):
    d = dict(sc); d["g"] = leaned(sc["g"], lean); d["ang"] = sc["ang"] + lean
    return d


# =========================================================================== animations  (ms, pose)
def anim_idle(phase):
    fr = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        bob = 1.0 - math.cos(a)
        fr.append((150, P_(ph=a, bob=round(bob, 2), htilt=-0.9 * bob, lift=-1.4 * math.sin(a), chain_swing=1.5 * math.sin(a - 0.8),
                           far=dict(wrist=(40 + 0.8 * math.sin(a), 84 + 0.8 * math.sin(a - 0.6)), curl=12 + 3 * bob),
                           phase=phase)))
    return fr


def anim_drift(phase):
    fr = []
    lean = 6
    for i in range(6):
        a = 2 * math.pi * i / 6
        bob = 0.8 * (1.0 - math.cos(a))
        fr.append((110, P_(ph=a, bob=round(bob, 2), lean=lean, wind=7 + math.sin(a), htilt=3, lift=-1.5 * math.sin(a),
                           chain_swing=-3 + math.sin(a),
                           near=dict(wrist=leaned(NEAR["wrist"], lean)), sc=sc_leaned(SC0, lean),
                           far=dict(wrist=(34 + math.sin(a), 86 + math.sin(a - 0.5)), hdir=150, curl=8),
                           phase=phase)))
    return fr


def anim_reap(phase):
    K = [  # ms, lean, bob, htilt, grip, ang, far wrist, eyes
        (110, -2, -1, -2, (94, 70), -104, (44, 78), 0.0),
        (110, -6, -2, -4, (92, 60), -132, (38, 70), 0.3),
        (120, -9, -3, -6, (90, 52), -164, (34, 64), 0.7),
        (200, -10, -3, -7, (89, 50), -172, (33, 62), 1.0),       # telegraph hold
        (60, 3, 0, 2, (100, 56), -62, (50, 74), 1.0),            # strike (active 4-6)
        (60, 10, 2, 6, (106, 66), -8, (64, 78), 1.0),
        (80, 13, 3, 8, (106, 74), 17, (72, 82), 0.8),
        (120, 13, 3, 8, (105, 75), 21, (72, 83), 0.5),
        (110, 9, 2, 5, (102, 76), 2, (62, 84), 0.3),
        (120, 5, 1, 3, (99, 77), -42, (52, 84), 0.0),
        (130, 2, 0, 1, (96, 77), -80, (44, 84), 0.0),
        (140, 0, 0, 0, (94.5, 76.5), -94, (40, 84), 0.0),
    ]
    fr = []
    prev = None
    for i, (ms, lean, bob, ht, gp, ang, fw, eyes) in enumerate(K):
        sc = dict(SC0, g=gp, ang=ang, lh=(64, 58, 52, 52, 56, 60, 60, 60, 62, 64, 66, 66.65)[i],
                  lb=(49, 54, 60, 60, 56, 50, 47.6, 47.6, 47.6, 47.6, 47.6, 47.6)[i])
        smear = prev if 4 <= i <= 7 else None
        fr.append((ms, P_(ph=0.4 * i, lean=lean, bob=bob, htilt=ht, wind=(0, 1, 2, 2, -4, -7, -8, -6, -4, -2, -1, 0)[i],
                           lift=(0, 1, 2, 2, -2, -3, -2, -1, 0, 0, 0, 0)[i], chain_swing=(0, 1, 2, 2, -3, -5, -5, -4, -2, -1, 0, 0)[i],
                           near=dict(wrist=gp), far=dict(wrist=fw, hdir=(105, 120, 140, 150, 60, 20, 10, 10, 40, 80, 100, 105)[i],
                                                         curl=(12, 20, 30, 34, 20, 10, 8, 10, 12, 12, 12, 12)[i]),
                           sc=sc, sc_prev=smear, eyes=eyes, phase=phase)))
        prev = sc
    return fr


def anim_cast(phase):
    far_sc = dict(g=(58, 36), ang=-106, lh=18, lb=92, s=-1, k=0.8)
    K = [  # ms, lean, bob, near wrist, near hand (hdir, curl, spread), far wrist, scythe, ring r, rot, flash, eyes
        (100, -1, 0, (94, 74), None, (60, 62), dict(SC0, g=(94, 74), ang=-96), 0, 0, 0, 0.0),
        (100, -2, -1, (100, 64), (-10, 30, 14), (78, 52), dict(g=(78, 52), ang=-102, lh=30, lb=82, s=1, k=0.6), 3, 0, 0, 0.3),
        (110, -3, -1, (103, 58), (-8, 5, 18), (60, 38), dict(far_sc, g=(60, 38)), 6, 0.0, 0, 0.6),
        (120, -4, -1, (104, 56), (-8, -6, 19), (58, 36), far_sc, 11, 0.15, 0, 1.0),     # telegraph
        (150, -4, -1, (104, 56), (-8, -6, 19), (57, 35), far_sc, 15, 0.3, 0, 1.0),
        (70, -5, -2, (106, 55), (-8, -10, 21), (57, 34), far_sc, 16, 0.45, 5, 1.0),      # spawn
        (130, -4, -1, (105, 56), (-8, -8, 20), (57, 35), far_sc, 15, 0.8, 0, 1.0),       # channel hold
        (110, -3, -1, (102, 60), (-10, 10, 16), (59, 38), far_sc, 11, 1.0, 0, 0.6),
        (120, -1, 0, (97, 70), None, (72, 56), dict(g=(94, 70), ang=-100, lh=60, lb=54, s=1, k=0.6), 0, 0, 0, 0.3),
        (140, 0, 0, (94.5, 76.5), None, (40, 84), SC0, 0, 0, 0, 0.0),
    ]
    fr = []
    for i, (ms, lean, bob, nw, nh, fw, sc, r, rot, fl, eyes) in enumerate(K):
        near = dict(wrist=nw)
        if nh:
            near.update(hdir=nh[0], curl=nh[1], spread=nh[2], thumb=-85)
        on_far = math.hypot(fw[0] - sc["g"][0], fw[1] - sc["g"][1]) < 5.5
        far = dict(wrist=fw, hdir=-30 if on_far else 60, curl=62 if on_far else 20, spread=10, pref=(-1, 0.2), drape=(-4, 12))
        order = R.ORDER_IDLE if sc.get("s", 1) == 1 and i in (0, 9) else \
            ["FXB", "Smear", "Scythe", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve", "Mantle",
             "Hood", "Head", "NearArm", "NearHand", "Chain", "Glow", "FX"]
        p = P_(ph=0.5 * i, lean=lean, bob=bob, htilt=(0, -1, -3, -4, -4, -5, -4, -3, -1, 0)[i], wind=(0, 1, 2, 2, 2, 4, 3, 2, 1, 0)[i],
               near=near, far=far, sc=sc, order=order, eyes=eyes, phase=phase, chain_swing=(0, 1, 2, 2, 2, 3, 2, 1, 0, 0)[i])
        if r:
            c = (nw[0] + 17, nw[1])
            p["ring"] = dict(c=c, r=r, rot=0.3 + rot, palm=(nw[0] + 6, nw[1]), flash=fl)
        fr.append((ms, p))
    return fr


def anim_write(phase):
    K = [  # ms, lean, bob, grip, far wrist, far hand(hdir, curl, spread), eyes, ring at far palm
        (110, -2, -1, (95, 70), (48, 62), (-60, 20, 16), 0.0, 0),
        (120, -3, -3, (96, 62), (46, 40), (-100, 8, 20), 0.5, 3),
        (150, -3, -4, (96, 58), (45, 36), (-104, 4, 22), 1.0, 5),       # telegraph (the ink gathers)
        (60, 3, 3, (97, 84), (50, 44), (-90, 10, 20), 1.0, 5),           # stab
        (140, 5, 5, (97, 88), (52, 48), (-80, 16, 18), 1.0, 0),          # spawn: the spike is in the floor
        (120, 5, 5, (97, 88), (52, 52), (-70, 20, 16), 0.7, 0),
        (120, 4, 5, (97, 88), (50, 60), (-40, 20, 14), 0.5, 0),
        (110, 2, 3, (96, 80), (46, 70), (40, 16, 14), 0.2, 0),
        (120, 1, 1, (95, 77), (42, 80), (90, 12, 13), 0.0, 0),
        (140, 0, 0, (94.5, 76.5), (40, 84), (105, 12, 13), 0.0, 0),
    ]
    fr = []
    prev = None
    for i, (ms, lean, bob, gp, fw, fh, eyes, rr) in enumerate(K):
        sc = dict(SC0, g=gp, ang=-94 + lean * 0.5)
        p = P_(ph=0.45 * i, lean=lean, bob=bob, htilt=(-1, -3, -4, 3, 5, 5, 4, 2, 1, 0)[i], near=dict(wrist=gp),
               far=dict(wrist=fw, hdir=fh[0], curl=fh[1], spread=fh[2], pref=(-1, -0.2)), sc=sc, eyes=eyes, phase=phase,
               wind=(0, 1, 1, -3, -2, -1, 0, 0, 0, 0)[i], lift=(0, 1, 2, -3, -2, 0, 0, 0, 0, 0)[i],
               sc_prev=prev if i == 3 else None, chain_swing=(0, 1, 2, -3, -4, -3, -2, -1, 0, 0)[i])
        if rr:
            p["ring"] = dict(c=(fw[0] - 2, fw[1] - 8), r=rr, rot=0, palm=(fw[0] - 1, fw[1] - 7), flash=0)
        p["stab"] = i
        fr.append((ms, p))
        prev = sc
    return fr


SINK_BOB = [3, 12, 30, 54, 82, 112, 150]
SINK_RX = [12, 22, 30, 32, 31, 26, 16]


def anim_sink(phase):
    fr = []
    for i, (bob, rx) in enumerate(zip(SINK_BOB, SINK_RX)):
        fr.append(((90, 80, 70, 70, 70, 80, 110)[i],
                   P_(ph=0.5 * i, bob=bob, lift=-2 - i, wind=-2, eyes=1.0 if i < 4 else 0.0, phase=phase,
                      puddle=(rx, 0.9 if i in (1, 2, 3) else 0.3), surface=140, far=dict(wrist=(44, 80), hdir=130, curl=20))))
    return fr


def anim_rise(phase):
    bobs = [150, 108, 72, 42, 18, 6, 0]
    rxs = [18, 30, 32, 30, 24, 14, 0]
    fr = []
    for i, (bob, rx) in enumerate(zip(bobs, rxs)):
        fr.append(((100, 70, 70, 70, 80, 100, 130)[i],
                   P_(ph=0.5 * i, bob=bob, lift=4 - i, wind=2 if i < 5 else 0, eyes=1.0 if i >= 3 else 0.0, phase=phase,
                      puddle=(rx, 0.8 if i in (2, 3, 4) else 0.2), surface=140 if rx else None,
                      far=dict(wrist=(42, 80), hdir=120, curl=16))))
    return fr


def anim_stagger(phase):
    K = [(80, -6, 3, -4, (92, 80), -84, 1.0), (120, -10, 7, -8, (90, 86), -76, 0.4), (160, -9, 9, -9, (90, 88), -74, 0.2),
         (200, -8, 10, -9, (90, 89), -74, 0.2)]
    fr = []
    for i, (ms, lean, bob, ht, gp, ang, eyes) in enumerate(K):
        fr.append((ms, P_(ph=0.6 * i, lean=lean, bob=bob, htilt=ht, near=dict(wrist=gp), sc=dict(SC0, g=gp, ang=ang), eyes=eyes,
                          far=dict(wrist=(44, 92 + i), hdir=110, curl=6), wind=4 - i, lift=3, phase=phase,
                          chain_swing=(4, 3, 2, 1)[i])))
    return fr


def anim_death(phase):
    fr = []
    ms = (120, 120, 130, 130, 120, 120, 120, 120, 120, 130, 130, 140, 160, 400)
    behind = ["FXB", "Smear", "Scythe", "TailsB", "FarSleeve", "FarArm", "FarHand", "Robe", "NearSleeve", "Mantle",
              "Hood", "Head", "NearArm", "NearHand", "Chain", "Glow", "FX"]
    for i in range(14):
        if i < 4:
            k = i / 3
            bob = 4 + 6 * k
            sc = dict(SC0, g=(96 - 4 * k, 78 + 44 * k * k - bob * k * k), ang=-94 - 80 * k * k, s=1)
            p = P_(ph=0.5 * i, lean=-10 - 2 * k, bob=bob, htilt=-8 - 6 * k, eyes=1.0 if i < 2 else 0.6, sc=sc,
                   near=dict(wrist=(98 + 4 * k, 72 + 6 * k) if i else sc["g"], hdir=20, curl=30),
                   far=dict(wrist=(40 - 4 * k, 80 + 4 * k), hdir=150, curl=40), wind=4, lift=2, phase=phase,
                   order=behind if i >= 2 else R.ORDER_IDLE)
        else:
            k = (i - 4) / 9
            bob = 10 - 4 * k
            sc = dict(SC0, g=(104, 141 - bob), ang=-178, s=1)
            p = P_(ph=0.5 * i, lean=-8 + 6 * k, bob=bob, htilt=-12 + 8 * k, eyes=max(0.0, 0.6 - k), sc=sc,
                   near=dict(wrist=(102, 80), hdir=40, curl=50), far=dict(wrist=(38, 86), hdir=160, curl=50),
                   wind=4 - 6 * k, lift=2, phase=phase, dissolve=0.08 + k * 0.98, no_wisps=True, order=behind)
        p["dissolve"] = p.get("dissolve", 0.0)
        fr.append((ms[i], p))
    return fr


def anim_transform(phase_unused):
    fr = []
    K = [  # ms, lean, bob, htilt, crack, phase, crown, far wrist, eyes, flash
        (120, 6, 3, 8, 0.25, 1, 0.0, (44, 88), 1.0, 0),
        (120, 9, 5, 10, 0.5, 1, 0.0, (46, 90), 1.0, 0),
        (110, 10, 6, 11, 0.75, 1, 0.0, (46, 91), 1.0, 0),
        (100, 11, 6, 12, 1.0, 1, 0.0, (47, 91), 1.0, 0),
        (70, -6, -1, -8, 0.0, 2, 0.35, (30, 64), 1.0, 14),         # the hood tears away
        (80, -8, -3, -10, 0.0, 2, 0.6, (26, 58), 1.0, 9),
        (100, -8, -3, -9, 0.0, 2, 0.85, (26, 58), 1.0, 5),
        (120, -7, -2, -8, 0.0, 2, 1.0, (28, 62), 1.0, 0),
        (120, -5, -1, -5, 0.0, 2, 1.0, (30, 68), 0.8, 0),
        (120, -3, 0, -3, 0.0, 2, 1.0, (34, 74), 0.6, 0),
        (120, -2, 0, -2, 0.0, 2, 1.0, (37, 78), 0.4, 0),
        (130, -1, 0, -1, 0.0, 2, 1.0, (39, 82), 0.2, 0),
        (140, 0, 0, 0, 0.0, 2, 1.0, (40, 84), 0.0, 0),
        (160, 0, 0, 0, 0.0, 2, 1.0, (40, 84), 0.0, 0),
    ]
    for i, (ms, lean, bob, ht, cr, ph_, crown, fw, eyes, flash) in enumerate(K):
        shake = (0, 1, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)[i]
        gp = leaned(NEAR["wrist"], lean)
        fr.append((ms, P_(ph=0.5 * i, lean=lean, bob=bob, htilt=ht, crack=cr, phase=ph_, crown=crown, eyes=eyes,
                          near=dict(wrist=gp), sc=sc_leaned(SC0, lean), far=dict(wrist=fw, hdir=150 if i >= 4 else 110, curl=10 if i >= 4 else 40, spread=18),
                          wind=(0, 1, 1, 1, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0)[i], lift=(1, 2, 2, 2, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0)[i],
                          flash=flash, shake=shake, burn=1.0 if i >= 4 else 0.0)))
    return fr


TAGDEFS = [("idle", anim_idle), ("drift", anim_drift), ("reap", anim_reap), ("cast", anim_cast), ("write", anim_write),
           ("sink", anim_sink), ("rise", anim_rise), ("transform", anim_transform), ("stagger", anim_stagger),
           ("death", anim_death)]
COUNTS = dict(idle=8, drift=6, reap=12, cast=10, write=10, sink=7, rise=7, transform=14, stagger=4, death=14)
LOOPS = ("idle", "drift")


# =========================================================================== per-frame extras
def head_burst(F, info, k, phase):
    """transformation flash: a ring of torn ink and crimson light bursting from the head"""
    e = info.get("eye") or (78, 32)
    c = (e[0] - 3, e[1] - 6)
    for kk in range(28):
        a = 2 * math.pi * kk / 28 + 0.1
        for d in range(k - 5, k + 1):
            if d <= 2:
                continue
            q = (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d * 0.9)
            F.put([q], "R5" if d > k - 2 else "R3", 255 if d > k - 3 else 190)
    for kk in range(10):
        a = C.hash01(kk, k, 5) * 6.28
        d = k * (0.5 + 0.8 * C.hash01(kk, k, 6))
        F.put([(c[0] + math.cos(a) * d, c[1] + math.sin(a) * d)], "K3")


def stab_fx(F, info, i, phase):
    """write: ink erupting from the stab point along the floor"""
    if i < 4:
        return
    b = info["sc"]["butt"]
    x0, y0 = b[0], 142
    k = (i - 3)
    hi = "V3" if phase == 1 else "R4"
    mid = "V1" if phase == 1 else "R2"
    for side in (-1, 1):
        for s in range(3):
            d = 6 + k * 9 + s * 5
            for t in range(4):
                x = x0 + side * (d + t)
                F.put([(x, y0 - (2 if t % 2 else 1))], hi if s == 0 else mid, 255 if s == 0 else 190)
    if i in (4, 5):
        for kk in range(12):
            a = math.pi * (0.08 + 0.84 * C.hash01(kk, i, 41))
            d = 4 + 20 * C.hash01(kk, i, 42) * (1 if i == 4 else 1.4)
            h = 4 + 22 * C.hash01(kk, i, 43) * (1 if i == 4 else 0.7)
            q = (x0 + math.cos(a) * d, y0 - h * math.sin(a))
            F.put([q, (q[0], q[1] + 1)], "K3")
            F.put([(q[0], q[1] - 1)], hi, 190)
    R.puddle(F, x0, y0 + 0.5, 6 + 3 * k, 1.8, phase)


def render_frame(p, fi, i, tag):
    imgs, info = R.render(p, fi)
    phase = p.get("phase", 1)
    if tag == "write":
        stab_fx(info["FX"], info, p["stab"], phase)
    if p.get("flash"):
        head_burst(info["FX"], info, p["flash"], phase)
    if p.get("puddle"):
        rx, spl = p["puddle"]
        if rx:
            R.puddle(info["FX"], 70, 140.5, rx * 1.15, 3.6, phase, fi, spl)
    if p.get("flash") or p.get("puddle") or tag == "write":
        imgs["FX"] = info["FX"].image()
    if p.get("surface") is not None:
        R.clip_below(imgs, p["surface"] + R.OY, [n for n in imgs if n not in ("FX",)], fi, phase)
    if p.get("dissolve"):
        R.dissolve(imgs, p["dissolve"], [n for n in imgs if n not in ("Scythe", "FXB", "Smear")], fi, phase)
        # ink motes lifting off the dissolve front
        F = C.FXLayer("motes")
        d = min(1.0, p["dissolve"])
        for kk in range(int(8 + 16 * (1 - abs(d - 0.5) * 2))):
            h = C.hash01(kk, fi, 90)
            x = 44 + 56 * C.hash01(kk, 3, 91)
            y = 132 - d * 120 - 34 * h
            ln = 2 + int(4 * C.hash01(kk, fi, 92))
            F.put([(x, y - t) for t in range(ln)], "K4", 190)
            F.put([(x, y - ln)], "V3" if phase == 1 else "R4", 190)
        imgs["FX"].alpha_composite(F.image())
    if p.get("shake"):
        for n in list(imgs):
            im = Image.new("RGBA", (R.FW, R.FH), (0, 0, 0, 0))
            im.alpha_composite(imgs[n], (p["shake"], 0))
            imgs[n] = im
    return imgs, info


GROUPS = {"FXB": "Back", "Smear": "Smear", "Glow": "FX", "FX": "FX", "Scythe": "Scythe"}
LAYERS = ["Back", "Body", "Smear", "Scythe", "Arm", "FX"]
ARMSET = {"NearArm", "NearHand", "Chain"}


def to_cels(imgs, order):
    """collapse the rig's many layers into a few Aseprite layers, keeping the pose's paint order"""
    cels = {n: Image.new("RGBA", (R.FW, R.FH), (0, 0, 0, 0)) for n in LAYERS}
    cur = 0
    for n in order:
        if n not in imgs:
            continue
        want = LAYERS.index(GROUPS.get(n, "Arm" if n in ARMSET else "Body"))
        cur = max(cur, want)
        cels[LAYERS[cur]].alpha_composite(imgs[n])
    flat = R.flatten(imgs, order)
    return cels, flat


# =========================================================================== build
def build_all():
    import asebuild
    tags, frames1, frames2, flats1, flats2 = [], [], [], [], []
    infos = {}
    rows1, rows2 = [], []
    fi = 0
    for name, fn in TAGDEFS:
        if ONLY and name not in ONLY:
            continue
        a = len(flats1)
        infos[name] = []
        r1, r2 = [], []
        f1s = fn(1)
        assert len(f1s) == COUNTS[name], (name, len(f1s))
        for k, (ms, p) in enumerate(f1s):
            outs = []
            for phase in (1, 2):
                pp = dict(p)
                if name != "transform":
                    pp["phase"] = phase
                imgs, info = render_frame(pp, fi if name not in LOOPS else k, k, name)
                cels, flat = to_cels(imgs, pp["order"])
                outs.append((cels, flat, info))
            (c1, fl1, i1), (c2, fl2, i2) = outs
            frames1.append({"ms": ms, "cels": c1}); frames2.append({"ms": ms, "cels": c2})
            flats1.append(fl1); flats2.append(fl2); r1.append(fl1); r2.append(fl2)
            infos[name].append(i1)
            fi += 1
        tags.append((name, a, len(flats1) - 1))
        rows1.append((name, r1)); rows2.append((name, r2))
        print("rendered", name, len(f1s), flush=True)
    os.makedirs(PV, exist_ok=True)
    sfx = "" if not ONLY else "_wip"
    preview(rows1, os.path.join(PV, f"unwritten{sfx}.png"))
    preview(rows2, os.path.join(PV, f"unwritten_p2{sfx}.png"))
    if ONLY:
        return
    meta = make_meta(infos, tags)
    hit_preview(flats1, tags, meta, os.path.join(PV, "unwritten_hitbox.png"))
    if BUILD:
        asebuild.build("unwritten", R.FW, R.FH, LAYERS, frames1, tags)
        asebuild.build("unwritten_p2", R.FW, R.FH, LAYERS, frames2, tags)
    json.dump(meta, open(os.path.join(ASSETS, "unwritten_meta.json"), "w"), indent=1)
    print("meta written")


def bbox(pts, pad=0):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return [min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 1 + 2 * pad, max(ys) - min(ys) + 1 + 2 * pad]


def union(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def frc(q):
    return [int(round(q[0] + R.OX)), int(round(q[1] + R.OY))]


def make_meta(infos, tags):
    idle0 = infos["idle"][0]
    body = {q for q in idle0["body_px"] if 44 <= q[0] <= 92 and q[1] <= 128}
    hb = bbox(body)
    hurt = [hb[0] + 4 + R.OX, hb[1] + R.OY, hb[2] - 8, hb[3]]
    # reap: blade + smear on the active frames, in front of the body, reaching the floor
    rects = {}
    for k in (4, 5, 6):
        inf = infos["reap"][k]
        pts = {q for q in (inf["blade_px"] | inf.get("smear", set())) if q[0] > 84}
        r = bbox(pts, 1)
        r = [r[0] + R.OX, r[1] + R.OY, r[2], r[3]]
        if r[1] + r[3] < R.FH:
            r[3] = R.FH - r[1]
        rects[str(k)] = r
    reap_hit = union(list(rects.values()))
    eye = infos["idle"][0]["eye"]
    cast5 = infos["cast"][5]["p"]["ring"]
    write4 = infos["write"][4]
    meta = {
        "native": 1,
        "frame": [R.FW, R.FH],
        "anchor": [R.AX, R.AY],
        "floating": True,
        "hurtbox": hurt,
        "attacks": {
            "reap": {"active": [4, 6], "hit": reap_hit, "rects": rects},
        },
        "telegraph": {
            "reap": {"frame": 3, "at": frc(infos["reap"][3]["blade_tip"])},
            "cast": {"frame": 3, "at": frc(infos["cast"][3]["p"]["ring"]["c"])},
            "write": {"frame": 2, "at": frc(infos["write"][2]["sc"]["butt"])},
        },
        "spawn": {
            "cast": {"frame": 5, "at": frc(cast5["c"]), "hold": 6},
            "write": {"frame": 4, "at": [int(round(write4["sc"]["butt"][0] + R.OX)), R.FH - 2]},
            "sink": {"frame": 6, "at": [R.AX, R.FH - 3]},
        },
        "points": {
            "eye": frc(eye),
            "chest": frc((72, 62)),
            "scythe_rest": frc((94.5, 76.5)),
        },
        "notes": "faces right; floating: anchor = floor point under the body (lowest wisp ~11px above it). hurtbox = hood, "
                 "robe and upper cloak tails. reap: overhead scythe chop in front, telegraph glint on frame 3 (held 200ms), "
                 "active 4-6, 'hit' = blade + smear union reaching the floor. cast: glyph ring grows 1-4, fire patterns "
                 "at spawn.cast (frame 5), hold frame 6 to channel. write: the scythe butt is stabbed into the floor on "
                 "frame 3, spawn.write on frame 4 (ink runs along the floor). sink/rise: the body sinks into / rises from "
                 "an ink pool at the anchor; frames 5-6 of sink (0-1 of rise) are fully submerged. transform: phase-2 "
                 "change (hood tears on frame 4). death: the scythe falls behind it and the body unravels into ink; the "
                 "last frame (scythe on the floor) is held.",
    }
    return meta


def preview(rows, path, scale=2, maxcols=7):
    blocks = []
    for name, ims in rows:
        for s in range(0, len(ims), maxcols):
            blocks.append((name if s == 0 else "", ims[s:s + maxcols]))
    Wd = maxcols * (R.FW * scale + 4) + 60
    Hd = len(blocks) * (R.FH * scale + 6)
    sh = Image.new("RGBA", (Wd, Hd), (40, 40, 46, 255))
    dr = ImageDraw.Draw(sh)
    for bi, (name, ims) in enumerate(blocks):
        y = bi * (R.FH * scale + 6)
        dr.text((4, y + 4), name, fill=(220, 210, 230))
        for i, im in enumerate(ims):
            fr_ = Image.new("RGBA", (R.FW, R.FH), (92, 92, 98, 255)); fr_.alpha_composite(im)
            sh.alpha_composite(fr_.resize((R.FW * scale, R.FH * scale), Image.NEAREST), (60 + i * (R.FW * scale + 4), y))
    sh.save(path)


def hit_preview(flats, tags, meta, path):
    rows = []
    start = {t: a for t, a, _ in tags}
    for tag in ("idle", "reap"):
        a = start[tag]
        n = 12 if tag == "reap" else 1
        ims = []
        for k in range(n):
            im = Image.new("RGBA", (R.FW, R.FH), (92, 92, 98, 255)); im.alpha_composite(flats[a + k])
            dr = ImageDraw.Draw(im)
            x, y, w, h = meta["hurtbox"]
            dr.rectangle([x, y, x + w - 1, y + h - 1], outline=(60, 230, 90))
            if tag == "reap" and str(k) in meta["attacks"]["reap"]["rects"]:
                x, y, w, h = meta["attacks"]["reap"]["rects"][str(k)]
                dr.rectangle([x, y, x + w - 1, y + h - 1], outline=(240, 60, 60))
            if tag == "reap" and k == meta["telegraph"]["reap"]["frame"]:
                x, y = meta["telegraph"]["reap"]["at"]
                dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(60, 220, 240))
            # player for scale, standing 30px in front at the floor
            px = R.AX + 48
            dr.rectangle([px - 5, R.FH - 26, px + 5, R.FH - 1], outline=(250, 250, 120))
            ims.append(im)
        rows.append((tag, ims))
    preview(rows, path)


if __name__ == "__main__":
    if "--fx-only" not in sys.argv:
        build_all()
    if not ONLY:
        import unwritten_fx
        unwritten_fx.build_all(BUILD)
