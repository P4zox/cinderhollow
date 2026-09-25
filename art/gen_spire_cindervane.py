#!/usr/bin/env python3
"""CINDERVANE, THE LAST DRAKE — Tempest Spire main boss sprite sheets (from the approved concept v3).

    python3 art/gen_spire_cindervane.py                 full build: cindervane + cindervane_p2 (+ meta, previews)
    python3 art/gen_spire_cindervane.py --preview       previews only (no Aseprite)
    python3 art/gen_spire_cindervane.py --only bite,claw --preview   quick iteration on some tags

Drawing = the approved concept generator (art/concepts/gen_cindervane.py) driven through the rig in
art/spire_drake_rig.py; poses are keyframed rig controls interpolated with easing.  Frame 288x176, faces RIGHT,
anchor [144, 168] (ground line).  Airborne tags keep the same anchor: the engine's y is the ground-equivalent
reference and the body flies ~80px above it inside the frame.

Sheets (grid, 14 columns): cindervane (phase 1, storm in the seams) and cindervane_p2 (phase 2: the storm breaks
loose — brighter seams, arcs off spikes and wing tips).  Meta: assets/cindervane_meta.json with per-frame hurtboxes,
mouth / hand / club points, attack windows, telegraphs.
"""
import copy, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spire_drake_rig as RG  # noqa: E402
from spire_drake_rig import base, mix, ease, shifted, wing_xform, build, render  # noqa: E402

ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREV = os.path.join(HERE, "previews")
W, H = RG.W, RG.H
AX, AY = 144, RG.GROUND
COLS = 14
ARGS = sys.argv[1:]
PREVIEW_ONLY = "--preview" in ARGS
ONLY = None
if "--only" in ARGS:
    ONLY = ARGS[ARGS.index("--only") + 1].split(",")


# =========================================================================== wing library (relative to shoulder)
def W2(far, near):
    return [far, near]


FAR_FIX = dict(seed=31, nholes=4, tears=4, bolts=1, fore_r=(2.8, 2.0), hum_r=(4.4, 2.6), lead_spikes=3, bias=-1.8)
NEAR_FIX = dict(seed=33, nholes=6, tears=5, bolts=2, bias=0.0)


def wf(**k):
    d = dict(FAR_FIX); d.update(k); return d


def wn(**k):
    d = dict(NEAR_FIX); d.update(k); return d


SAG_F = [0.26, 0.28, 0.28, 0.32]
SAG_N = [0.3, 0.32, 0.32, 0.36]
WING_IDLE = W2(
    wf(shoulder=(3, -10), elbow=(-5, -42), wrist=(13, -76), thumb=(3, -4), tips=[(-35, -98), (-53, -80), (-51, -56), (-29, -36)],
       root=(-3, -16), bends=[3, 3, 3, 2.5], sag=SAG_F),
    wn(shoulder=(-13, -8), elbow=(-33, -38), wrist=(-15, -74), thumb=(3, -4), tips=[(-67, -88), (-85, -66), (-81, -40), (-59, -20)],
       root=(-31, -6), bends=[3, 3, 3, 2.5], sag=SAG_N))
WING_FOLD = W2(     # tucked tight along the back
    wf(shoulder=(3, -10), elbow=(-10, -30), wrist=(8, -50), thumb=(3, -4), tips=[(-30, -62), (-44, -50), (-46, -36), (-30, -24)],
       root=(-3, -14), bends=[2, 2, 2, 2], sag=SAG_F),
    wn(shoulder=(-13, -8), elbow=(-34, -26), wrist=(-18, -48), thumb=(3, -4), tips=[(-62, -58), (-78, -44), (-76, -26), (-58, -12)],
       root=(-31, -4), bends=[2, 2, 2, 2], sag=SAG_N))
WING_ROAR = W2(
    wf(shoulder=(9, -15), elbow=(9, -53), wrist=(19, -95), thumb=(2, -4), tips=[(53, -107), (69, -99), (65, -81), (45, -67)],
       root=(25, -21), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-5, -13), elbow=(-27, -51), wrist=(-47, -87), thumb=(-3, -4), tips=[(-139, -103), (-155, -67), (-139, -37), (-99, -23)],
       root=(-15, -11), bends=[3, 3, 3, 2.5], sag=[0.36, 0.38, 0.38, 0.4]))
WING_UP = W2(       # flight upstroke (concept "air")
    wf(shoulder=(0, -11), elbow=(16, -43), wrist=(28, -77), thumb=(2, -4), tips=[(78, -88), (104, -77), (102, -55), (76, -39)],
       root=(18, -5), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-14, -9), elbow=(-36, -43), wrist=(-58, -77), thumb=(-3, -4), tips=[(-148, -86), (-164, -49), (-148, -17), (-106, 1)],
       root=(-32, 5), bends=[3, 3, 3, 2.5], sag=[0.36, 0.38, 0.38, 0.4]))
WING_RAISE = W2(    # both wings high, before a downbeat / breath rear
    wf(shoulder=(3, -12), elbow=(4, -48), wrist=(20, -86), thumb=(2, -4), tips=[(-6, -108), (-20, -96), (-22, -76), (-8, -58)],
       root=(6, -18), bends=[2, 2, 2, 2], sag=SAG_F),
    wn(shoulder=(-13, -9), elbow=(-30, -46), wrist=(-22, -86), thumb=(3, -4), tips=[(-78, -104), (-100, -80), (-98, -52), (-72, -30)],
       root=(-30, -6), bends=[3, 3, 3, 2.5], sag=SAG_N))


WING_DOWN = W2(     # flight downstroke: wings driven below the body line
    wf(shoulder=(0, -11), elbow=(22, 2), wrist=(42, 16), thumb=(3, -3), tips=[(92, 52), (110, 38), (110, 18), (86, 4)],
       root=(18, -4), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-14, -9), elbow=(-38, 4), wrist=(-60, 20), thumb=(-3, -3), tips=[(-112, 64), (-140, 48), (-146, 24), (-116, 6)],
       root=(-32, 5), bends=[-3, -3, -3, -2.5], sag=[0.36, 0.38, 0.38, 0.4]))
WING_MID = W2(      # wings level, sweeping through
    wf(shoulder=(0, -11), elbow=(24, -26), wrist=(50, -36), thumb=(3, -4), tips=[(108, -38), (122, -20), (114, -2), (84, 2)],
       root=(18, -5), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-14, -9), elbow=(-40, -24), wrist=(-68, -36), thumb=(-3, -4), tips=[(-152, -40), (-164, -14), (-146, 6), (-106, 6)],
       root=(-32, 5), bends=[3, 3, 3, 2.5], sag=[0.36, 0.38, 0.38, 0.4]))
WING_REC = W2(      # recovery upstroke: half folded, rising
    wf(shoulder=(0, -11), elbow=(10, -36), wrist=(22, -56), thumb=(2, -4), tips=[(56, -70), (72, -56), (68, -38), (48, -26)],
       root=(16, -6), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-14, -9), elbow=(-34, -34), wrist=(-44, -60), thumb=(-3, -4), tips=[(-104, -72), (-120, -46), (-110, -22), (-80, -8)],
       root=(-32, 5), bends=[3, 3, 3, 2.5], sag=[0.36, 0.38, 0.38, 0.4]))


def flap_wings(t):
    """0 up -> 0.25 level -> 0.45 down -> 0.75 recovery -> 1 up."""
    keys = [(0.0, WING_UP), (0.22, WING_MID), (0.45, WING_DOWN), (0.72, WING_REC), (1.0, WING_UP)]
    t %= 1.0
    for (t0, A), (t1, B) in zip(keys[:-1], keys[1:]):
        if t0 <= t <= t1:
            k = ease((t - t0) / (t1 - t0))
            return [RG.lerp_any(A[i], B[i], k) for i in range(2)]
    return copy.deepcopy(WING_UP)


WING_SLUMP = W2(    # stagger / death: dropped, spread low
    wf(shoulder=(3, -8), elbow=(14, -30), wrist=(34, -40), thumb=(2, -4), tips=[(60, -34), (68, -18), (62, -2), (46, 8)],
       root=(16, -4), bends=[-2, -2, -2, -2], sag=SAG_F),
    wn(shoulder=(-13, -6), elbow=(-38, -22), wrist=(-62, -30), thumb=(-3, -4), tips=[(-104, -22), (-118, -6), (-110, 12), (-86, 24)],
       root=(-34, 4), bends=[3, 3, 3, 2.5], sag=SAG_N))


def wings(R, Wset):
    R = copy.deepcopy(R); R["wings"] = copy.deepcopy(Wset); return R


# =========================================================================== key poses
IDLE = base()
IDLE["wings"] = copy.deepcopy(WING_IDLE)
IDLE["seam_bolts"] = (7, 1); IDLE["wing_bolts"] = 2

AIR = copy.deepcopy(IDLE)
AIR.update(hip=(127, 92), sh=(168, 91), sag=1.5, head=(236, 80), head_ang=12, neck_a0=-4, jaw=6,
           tail=[168.1, 166.0, 172.2, 187.8, 201.8, 234.5, 263.3],
           feet=[(99, 128), (113, 132)], ankle_off=[(12, -8), (12, -8)],
           hands=[(193, 128), (181, 134)], wrist_off=[(-7, -6), (-7, -6)], claw_dir=[(0.6, 0.8), (0.6, 0.8)])
AIR["wings"] = copy.deepcopy(WING_UP)

ROAR = copy.deepcopy(IDLE)
ROAR.update(hip=(120, 129), sh=(161, 107), sag=0.0, head=(229, 58), head_ang=-24, neck_a0=-34, jaw=38, mouth_glow=2,
            throat=1, tail=[150.9, 160.7, 169.7, 190.3, 213.7, 253.6, 273.0],
            feet=[(116, 163), (133, 164)], ankle_off=[(-8, -7), (-9, -6)],
            hands=[(208, 156), (190, 162)], wrist_off=[(-6, -10), (-6, -10)], claw_dir=[(1, 0.5), (1, 0.5)])
ROAR["wings"] = copy.deepcopy(WING_ROAR)

CROUCH = shifted(IDLE, -2, 7)
CROUCH.update(head=(230, 152), head_ang=10, neck_a0=10)
CROUCH = wings(CROUCH, WING_FOLD)


def sway(R, t, amp=1.0, wing_amp=4.0, head_amp=2.0):
    """Idle breathing / tail sway at phase t in [0,1)."""
    R = copy.deepcopy(R)
    s = math.sin(2 * math.pi * t)
    c = math.cos(2 * math.pi * t)
    R["hip"] = (R["hip"][0], R["hip"][1] + 1.0 * s * amp)
    R["sh"] = (R["sh"][0], R["sh"][1] + 1.5 * s * amp)
    R["head"] = (R["head"][0] + 1.0 * c * amp, R["head"][1] + head_amp * math.sin(2 * math.pi * t - 0.9) * amp)
    R["head_ang"] += 2.0 * math.sin(2 * math.pi * t - 0.9) * amp
    R["tail"] = [a + 5.0 * amp * (i / 6) * math.sin(2 * math.pi * t - i * 0.6) for i, a in enumerate(R["tail"])]
    R["wings"] = [wing_xform(R["wings"][0], deg=wing_amp * s * amp), wing_xform(R["wings"][1], deg=-wing_amp * s * amp)]
    return R


# =========================================================================== tags
TAGS = []            # (name, [(R, ms, dict(storm=, jitter=))...])


def seq(keys, ns, kinds=None):
    """Chain of key poses -> list of poses; ns[i] = frames from keys[i] to keys[i+1] (endpoint of the last included)."""
    out = []
    for i, n in enumerate(ns):
        k = kinds[i] if kinds else "io"
        for j in range(n):
            t = (j + 1) / n
            out.append(mix(keys[i], keys[i + 1], ease(t, k)))
    return out


def tag_idle():
    return [(sway(IDLE, i / 8), 120, {}) for i in range(8)]


def walk_pose(t):
    R = copy.deepcopy(IDLE)
    base_h = [113, 129]; base_f = [199, 185]
    ph_h = [0.5, 0.0]; ph_f = [0.75, 0.25]
    step, duty, lift = 30.0, 0.62, 8.0

    def foot(bx, p, ground):
        p %= 1.0
        if p < duty:
            return (bx + step / 2 - step * p / duty, ground)
        q = (p - duty) / (1 - duty)
        return (bx - step / 2 + step * ease(q), ground - lift * math.sin(math.pi * q))
    R["feet"] = [foot(base_h[k], t + ph_h[k], [164, 165][k]) for k in range(2)]
    R["hands"] = [foot(base_f[k], t + ph_f[k], [163, 165][k]) for k in range(2)]
    bob = -1.6 * abs(math.sin(2 * math.pi * t))
    R = shifted(R, 0, bob + 1.0)
    R["head"] = (R["head"][0] + 1.5 * math.sin(2 * math.pi * t), R["head"][1] + 1.8 * math.sin(4 * math.pi * t + 1.0))
    R["tail"] = [a + 6.0 * (i / 6) * math.sin(2 * math.pi * t - i * 0.7) for i, a in enumerate(R["tail"])]
    R["wings"] = [wing_xform(WING_IDLE[0], deg=3 * math.sin(4 * math.pi * t)), wing_xform(WING_IDLE[1], deg=-3 * math.sin(4 * math.pi * t))]
    return R


def tag_walk():
    return [(walk_pose(i / 8), 100, {}) for i in range(8)]


def tag_bite():
    coil = shifted(IDLE, -8, 4)
    coil.update(head=(194, 100), head_ang=-24, neck_a0=-50, jaw=4)
    coil = wings(coil, [wing_xform(WING_IDLE[0], -8), wing_xform(WING_IDLE[1], 8)])
    hold = copy.deepcopy(coil); hold.update(head=(190, 96), head_ang=-28, jaw=18, mouth_glow=1)
    strike = shifted(IDLE, 10, 2)
    strike.update(head=(246, 150), head_ang=14, neck_a0=8, jaw=36, mouth_glow=1)
    strike["hands"] = [(205, 163), (193, 165)]
    strike = wings(strike, [wing_xform(WING_IDLE[0], 6), wing_xform(WING_IDLE[1], -6)])
    snap = copy.deepcopy(strike); snap.update(head=(249, 152), head_ang=16, jaw=1, mouth_glow=0)
    fr = seq([IDLE, coil], [3], ["out"])
    ms = [90, 90, 100]
    fr += [hold]; ms += [300]
    fr += [mix(hold, strike, 0.6)]; ms += [50]
    fr += [strike, snap]; ms += [70, 90]
    fr += seq([snap, IDLE], [3]); ms += [110, 120, 130]
    return [(r, m, {}) for r, m in zip(fr, ms)]


def tag_claw():
    raise_ = shifted(IDLE, -4, -4)
    raise_.update(head=(212, 112), head_ang=-18, neck_a0=-30, jaw=10)
    raise_["hands"] = [(199, 163), (222, 100)]
    raise_["wrist_off"] = [(-7, -5), (-4, -9)]
    raise_["claw_dir"] = [(1, 0.45), (0.55, 0.9)]
    raise_ = wings(raise_, [wing_xform(WING_IDLE[0], -12), wing_xform(WING_IDLE[1], 10)])
    hold = copy.deepcopy(raise_); hold["hands"] = [(199, 163), (220, 92)]; hold["head"] = (208, 108)
    swipe = shifted(IDLE, 12, 3)
    swipe.update(head=(238, 146), head_ang=12, neck_a0=6, jaw=18)
    swipe["hands"] = [(203, 163), (244, 164)]
    swipe["wrist_off"] = [(-7, -5), (-9, -4)]
    swipe["claw_dir"] = [(1, 0.45), (1, 0.25)]
    swipe = wings(swipe, [wing_xform(WING_IDLE[0], 10), wing_xform(WING_IDLE[1], -8)])
    mid = mix(hold, swipe, 0.5); mid["hands"] = [(201, 163), (236, 132)]
    fr = seq([IDLE, raise_], [3], ["out"]); ms = [90, 90, 100]
    fr += [hold]; ms += [280]
    fr += [mid, swipe]; ms += [55, 90]
    fr += seq([swipe, IDLE], [4]); ms += [110, 110, 120, 130]
    return [(r, m, {}) for r, m in zip(fr, ms)]


def tag_tail():
    lift = shifted(IDLE, 6, 3)
    lift.update(head=(242, 152), head_ang=16, neck_a0=10, jaw=8, sag=4)
    lift["tail"] = [138, 124, 108, 92, 78, 60, 30]
    lift = wings(lift, [wing_xform(WING_IDLE[0], -10), wing_xform(WING_IDLE[1], 12)])
    hold = copy.deepcopy(lift); hold["tail"] = [136, 120, 102, 84, 68, 48, 20]
    lash = shifted(IDLE, 18, 2)
    lash.update(head=(250, 146), head_ang=10, neck_a0=6, jaw=14)
    lash["tail"] = [166, 172, 176, 178, 179, 180, 184]
    lash["feet"] = [(126, 164), (142, 165)]
    lash["hands"] = [(210, 163), (198, 165)]
    lash = wings(lash, [wing_xform(WING_IDLE[0], 8), wing_xform(WING_IDLE[1], -14)])
    follow = copy.deepcopy(lash); follow["tail"] = [170, 184, 196, 206, 220, 240, 262]
    fr = seq([IDLE, lift], [4], ["out"]); ms = [90, 90, 100, 110]
    fr += [hold]; ms += [300]
    fr += [mix(hold, lash, 0.55), lash]; ms += [50, 80]
    fr += [follow]; ms += [90]
    fr += seq([follow, IDLE], [3]); ms += [120, 130, 140]
    return [(r, m, {}) for r, m in zip(fr, ms)]


def tag_breath():
    rear = copy.deepcopy(IDLE)
    rear.update(hip=(118, 129), sh=(158, 110), sag=1, head=(206, 84), head_ang=-32, neck_a0=-42, jaw=8, throat=2)
    rear["hands"] = [(197, 161), (184, 164)]
    rear = wings(rear, WING_RAISE)
    inhale = copy.deepcopy(rear); inhale.update(head=(203, 80), head_ang=-36, jaw=18, mouth_glow=1, throat=2)
    fire0 = shifted(IDLE, 8, 2)
    fire0.update(head=(238, 136), head_ang=34, neck_a0=6, jaw=34, mouth_glow=2, throat=2)
    fire0 = wings(fire0, [wing_xform(WING_RAISE[0], 20), wing_xform(WING_RAISE[1], -18)])
    fire1 = copy.deepcopy(fire0); fire1.update(head=(248, 124), head_ang=6, neck_a0=0)
    close = copy.deepcopy(fire1); close.update(jaw=10, mouth_glow=0, throat=1)
    fr = seq([IDLE, rear], [3], ["out"]); ms = [100, 100, 110]
    fr += [inhale, inhale]; ms += [180, 260]
    fr += [fire0]; ms += [90]
    fr += seq([fire0, fire1], [5], ["lin"]); ms += [110] * 5
    fr += [close, mix(close, IDLE, 0.6)]; ms += [120, 140]
    ex = [{}] * 6 + [dict(storm=1.6)] * 6 + [{}] * 2
    ex[4] = ex[5] = dict(storm=1.3)
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]


def tag_roar():
    rear = copy.deepcopy(ROAR); rear.update(jaw=16, mouth_glow=1)
    fr = seq([IDLE, CROUCH], [2], ["out"]); ms = [100, 110]
    fr += [CROUCH]; ms += [160]
    fr += seq([CROUCH, rear], [2]); ms += [90, 90]
    for k in range(4):
        r = copy.deepcopy(ROAR)
        j = [(0, 0), (1, -1), (-1, 1), (1, 0)][k]
        r["head"] = (r["head"][0] + j[0], r["head"][1] + j[1])
        r["jaw"] = 38 + (k % 2) * 3
        fr.append(r); ms.append(120)
    fr += [mix(ROAR, IDLE, 0.6)]; ms += [160]
    ex = [{}] * 5 + [dict(storm=1.8)] * 4 + [{}]
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]


def fly_pose(t, R0=None):
    """Flap cycle phase t: 0 = wings up, 0.5 = wings down."""
    R0 = R0 or AIR
    R = copy.deepcopy(R0)
    R["wings"] = flap_wings(t)
    bob = 4.0 * math.cos(2 * math.pi * (t - 0.1))    # body rises on the downstroke
    R = shifted(R, 0, bob, feet=True)
    lag = math.cos(2 * math.pi * t - 1.2)
    R["feet"] = [(x, y + 2 * lag) for x, y in R["feet"]]
    R["tail"] = [a + 5.0 * (i / 6) * math.sin(2 * math.pi * t - i * 0.7) for i, a in enumerate(R["tail"])]
    R["head"] = (R["head"][0], R["head"][1] + 1.5 * math.cos(2 * math.pi * t - 0.8))
    return R


def tag_fly():
    return [(fly_pose(i / 6), 95, {}) for i in range(6)]


FLYB = copy.deepcopy(AIR)
FLYB.update(head=(240, 102), head_ang=42, neck_a0=14, jaw=32, mouth_glow=2, throat=2)


def tag_flybreath():
    return [(fly_pose(i / 6, FLYB), 90, dict(storm=1.4)) for i in range(6)]


def tag_takeoff():
    crouch = shifted(IDLE, -2, 8)
    crouch.update(head=(228, 146), head_ang=6, neck_a0=0)
    crouch = wings(crouch, WING_RAISE)
    beat = shifted(IDLE, 0, -10)
    beat.update(head=(234, 118), head_ang=0, neck_a0=-8)
    beat["feet"] = [(108, 160), (124, 162)]
    beat["hands"] = [(196, 156), (184, 158)]
    beat = wings(beat, WING_DOWN)
    lift = fly_pose(0.0)
    fr = seq([IDLE, crouch], [2], ["out"]); ms = [100, 120]
    fr += [crouch]; ms += [220]
    fr += [mix(crouch, beat, 0.6), beat]; ms += [70, 90]
    fr += [mix(beat, lift, 0.5), lift, fly_pose(0.2)]; ms += [100, 100, 100]
    return [(r, m, {}) for r, m in zip(fr, ms)]


DIVE = copy.deepcopy(AIR)
DIVE.update(hip=(112, 72), sh=(160, 98), sag=0, head=(222, 138), head_ang=44, neck_a0=34, jaw=26, mouth_glow=2, throat=2,
            tail=[150, 146, 148, 152, 160, 170, 190],
            feet=[(118, 116), (132, 120)], ankle_off=[(10, -10), (10, -10)],
            hands=[(206, 136), (196, 142)], wrist_off=[(-8, -6), (-8, -6)], claw_dir=[(0.7, 0.7), (0.7, 0.7)])
DIVE["wings"] = [wing_xform(WING_FOLD[0], 18, sx=1.05), wing_xform(WING_FOLD[1], 22, sx=1.1)]


def tag_dive():
    pre = fly_pose(0.0)
    pre["wings"] = copy.deepcopy(WING_RAISE)
    pre.update(head=(232, 92), head_ang=20, jaw=20, mouth_glow=1)
    fr = [mix(fly_pose(0.0), pre, 0.6), pre]; ms = [90, 220]
    fr += [mix(pre, DIVE, 0.6), DIVE]; ms += [70, 80]
    d2 = copy.deepcopy(DIVE); d2["tail"] = [a + 4 for a in DIVE["tail"]]
    fr += [d2, DIVE]; ms += [80, 80]
    ex = [{}, dict(storm=1.4), dict(storm=2.0), dict(storm=2.0), dict(storm=2.0), dict(storm=2.0)]
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]


def tag_land():
    flare = copy.deepcopy(AIR)
    flare.update(hip=(120, 104), sh=(160, 96), head=(226, 92), head_ang=-6, neck_a0=-20, jaw=12)
    flare["feet"] = [(112, 150), (128, 152)]; flare["ankle_off"] = [(-6, -8), (-6, -8)]
    flare["hands"] = [(196, 146), (184, 150)]; flare["wrist_off"] = [(-7, -6), (-7, -6)]
    flare = wings(flare, WING_RAISE)
    impact = shifted(IDLE, 0, 6)
    impact.update(head=(236, 154), head_ang=12, neck_a0=6, jaw=10)
    impact = wings(impact, WING_SLUMP)
    fr = [flare, mix(flare, impact, 0.55), impact]; ms = [110, 60, 140]
    fr += seq([impact, IDLE], [4]); ms += [110, 110, 120, 130]
    return [(r, m, {}) for r, m in zip(fr, ms)]


def tag_stagger():
    reel = copy.deepcopy(IDLE)
    reel.update(hip=(116, 128), sh=(154, 112), head=(206, 90), head_ang=-40, neck_a0=-40, jaw=30, mouth_glow=1)
    reel = wings(reel, [wing_xform(WING_ROAR[0], 10), wing_xform(WING_ROAR[1], -10)])
    slump = shifted(IDLE, 2, 8)
    slump.update(head=(236, 158), head_ang=26, neck_a0=16, jaw=6, sag=5)
    slump = wings(slump, WING_SLUMP)
    fr = [mix(IDLE, reel, 0.7), reel, mix(reel, slump, 0.5), slump]; ms = [70, 150, 110, 120]
    s2 = copy.deepcopy(slump); s2["head"] = (236, 159)
    fr += [s2, slump]; ms += [160, 400]
    ex = [{}, {}, dict(storm=0.6), dict(storm=0.4), dict(storm=0.4), dict(storm=0.4)]
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]


def tag_death():
    agony = copy.deepcopy(ROAR); agony.update(jaw=34, head=(222, 62))
    agony["wings"] = [wing_xform(WING_ROAR[0], -8), wing_xform(WING_ROAR[1], 10)]
    drop = shifted(IDLE, 0, 11)
    drop.update(head=(230, 156), head_ang=30, neck_a0=18, jaw=14, sag=6)
    drop["feet"] = [(106, 165), (126, 166)]; drop["hands"] = [(204, 165), (194, 166)]
    drop = wings(drop, WING_SLUMP)
    dead = shifted(drop, 0, 5)
    dead.update(head=(240, 161), head_ang=6, jaw=18, neck_a0=6)
    dead["tail"] = [170, 172, 176, 180, 186, 200, 220]
    dead = wings(dead, [wing_xform(WING_SLUMP[0], 20, sy=0.8), wing_xform(WING_SLUMP[1], -14, sy=0.8)])
    fr = seq([IDLE, agony], [3]); ms = [80, 90, 140]
    fr += [agony]; ms += [260]
    fr += seq([agony, drop], [4], ["in"]); ms += [80, 70, 60, 120]
    fr += seq([drop, dead], [5]); ms += [130, 140, 150, 170, 900]
    ex = [dict(storm=1.8)] * 4 + [dict(storm=1.2)] * 4 + [dict(storm=s) for s in (0.8, 0.5, 0.3, 0.1, 0.0)]
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]



# ---- physical move set (rework): rush wind-up / gallop / skid, wing buffet, rearing slam
RUSHPOSE = shifted(IDLE, 4, 7)
RUSHPOSE.update(head=(244, 154), head_ang=20, neck_a0=16, jaw=10, sag=3)
RUSHPOSE["tail"] = [160, 164, 170, 178, 186, 196, 214]
RUSHPOSE = wings(RUSHPOSE, WING_FOLD)


def tag_rushprep():
    crouch = shifted(IDLE, -8, 9)
    crouch.update(head=(232, 158), head_ang=24, neck_a0=18, jaw=6, sag=4)
    crouch["tail"] = [140, 130, 122, 116, 112, 100, 80]
    crouch = wings(crouch, WING_FOLD)
    out = seq([IDLE, crouch], [2], ["out"]); ms = [100, 110]
    for k in range(4):   # pawing: the near hind foot scrapes back, head sways low, tail lashes
        r = copy.deepcopy(crouch)
        fx, fy = r["feet"][1]
        r["feet"] = [r["feet"][0], (fx - (8 if k % 2 == 0 else 0), fy - (4 if k % 2 == 0 else 0))]
        r["head"] = (r["head"][0] + (1 if k % 2 else -1), r["head"][1] + (1 if k % 2 else 0))
        r["tail"] = [a + (8 if k % 2 else -8) * (i / 6) for i, a in enumerate(r["tail"])]
        r["jaw"] = 10 + 4 * (k % 2)
        out.append(r); ms.append(150 if k < 3 else 220)
    return [(r, m, {}) for r, m in zip(out, ms)]


def rush_pose(t):
    R = copy.deepcopy(RUSHPOSE)
    base_h = [118, 134]; base_f = [206, 192]
    ph_h = [0.1, 0.0]; ph_f = [0.55, 0.45]            # bounding gallop: hind pair, then fore pair
    step, duty, lift = 46.0, 0.42, 12.0

    def foot(bx, p, ground):
        p %= 1.0
        if p < duty:
            return (bx + step / 2 - step * p / duty, ground)
        q = (p - duty) / (1 - duty)
        return (bx - step / 2 + step * ease(q), ground - lift * math.sin(math.pi * q))
    R["feet"] = [foot(base_h[k], t + ph_h[k], [164, 165][k]) for k in range(2)]
    R["hands"] = [foot(base_f[k], t + ph_f[k], [163, 165][k]) for k in range(2)]
    bob = -4.0 * math.sin(2 * math.pi * t)
    R = shifted(R, 0, bob)
    R["head"] = (R["head"][0] + 2 * math.sin(2 * math.pi * t), R["head"][1] + 2 * math.sin(2 * math.pi * t + 0.8))
    R["tail"] = [a + 7.0 * (i / 6) * math.sin(2 * math.pi * t - i * 0.8) for i, a in enumerate(R["tail"])]
    R["wings"] = [wing_xform(WING_FOLD[0], deg=5 * math.sin(2 * math.pi * t)), wing_xform(WING_FOLD[1], deg=-5 * math.sin(2 * math.pi * t))]
    return R


def tag_rush():
    return [(rush_pose(i / 6), 70, {}) for i in range(6)]


def tag_rushstop():
    skid = shifted(IDLE, -12, 5)
    skid.update(head=(222, 128), head_ang=-10, neck_a0=-18, jaw=18)
    skid["hands"] = [(224, 164), (212, 165)]; skid["wrist_off"] = [(-9, -3), (-9, -3)]
    skid["feet"] = [(110, 164), (126, 165)]
    skid = wings(skid, [wing_xform(WING_IDLE[0], -16), wing_xform(WING_IDLE[1], 14)])
    fr = [mix(rush_pose(0), skid, 0.6), skid, skid]; ms = [70, 150, 160]
    fr += seq([skid, IDLE], [2]); ms += [140, 150]
    return [(r, m, {}) for r, m in zip(fr, ms)]


WING_BUFFET = W2(   # both wings driven forward and down in front of the drake
    wf(shoulder=(3, -10), elbow=(28, -18), wrist=(58, -10), thumb=(3, -3), tips=[(112, 26), (118, 44), (104, 56), (78, 50)],
       root=(16, -2), bends=[-3, -3, -3, -2.5], sag=[0.3, 0.32, 0.3, 0.36]),
    wn(shoulder=(-13, -8), elbow=(14, -22), wrist=(44, -18), thumb=(3, -3), tips=[(100, 18), (110, 40), (92, 56), (60, 46)],
       root=(-10, 2), bends=[-3, -3, -3, -2.5], sag=[0.34, 0.36, 0.36, 0.4]))


def tag_buffet():
    rear = copy.deepcopy(IDLE)
    rear.update(hip=(116, 130), sh=(154, 112), head=(212, 102), head_ang=-18, neck_a0=-30, jaw=10, sag=1)
    rear["hands"] = [(196, 160), (184, 162)]
    rear = wings(rear, [wing_xform(WING_ROAR[0], -6), wing_xform(WING_ROAR[1], 6)])
    hold = copy.deepcopy(rear); hold["head"] = (208, 98); hold["jaw"] = 16
    beat = shifted(IDLE, 6, 3)
    beat.update(head=(236, 142), head_ang=10, neck_a0=6, jaw=24)
    beat = wings(beat, WING_BUFFET)
    fr = seq([IDLE, rear], [3], ["out"]); ms = [100, 100, 110]
    fr += [hold]; ms += [300]
    fr += [mix(hold, beat, 0.5), beat]; ms += [60, 110]
    fr += seq([beat, IDLE], [4]); ms += [120, 120, 130, 140]
    return [(r, m, {}) for r, m in zip(fr, ms)]


def tag_slam():
    crouch = shifted(IDLE, -4, 7)
    crouch.update(head=(228, 150), head_ang=10, neck_a0=6)
    crouch = wings(crouch, WING_FOLD)
    rear = copy.deepcopy(ROAR)
    rear.update(jaw=12, mouth_glow=1, hip=(116, 131), sh=(152, 102), head=(214, 60), head_ang=-30, neck_a0=-44)
    rear["hands"] = [(204, 112), (192, 118)]; rear["wrist_off"] = [(-4, -9), (-4, -9)]; rear["claw_dir"] = [(0.6, 0.9), (0.6, 0.9)]
    hold = copy.deepcopy(rear); hold["head"] = (212, 56); hold["jaw"] = 20
    crash = shifted(IDLE, 10, 8)
    crash.update(head=(240, 150), head_ang=16, neck_a0=10, jaw=30, mouth_glow=2)
    crash["hands"] = [(226, 165), (214, 166)]; crash["wrist_off"] = [(-9, -4), (-9, -4)]
    crash = wings(crash, WING_SLUMP)
    fr = seq([IDLE, crouch], [2], ["out"]); ms = [90, 110]
    fr += seq([crouch, rear], [2]); ms += [100, 110]
    fr += [hold]; ms += [320]
    fr += [crash]; ms += [60]
    fr += [crash]; ms += [140]
    fr += seq([crash, IDLE], [3]); ms += [130, 140, 150]
    ex = [{}] * 5 + [dict(storm=1.6)] + [dict(storm=2.0)] * 2 + [{}] * 2
    return [(r, m, e) for r, m, e in zip(fr, ms, ex)]


# ---- phase 3: the wings break (applied to every pose of the p3 sheet)
def broken_wing(wg, near):
    """The arm still lifts, but the finger bones are snapped: the outer wing hangs limp in shreds."""
    wg = copy.deepcopy(wg)
    o = RG.v(wg["shoulder"]); el0 = RG.v(wg["elbow"]); wr0 = RG.v(wg["wrist"])
    el = el0 + RG.v((0, 5)); wr = el + (wr0 - el0) * 0.85 + RG.v((0, 9))
    tips = []
    for k, t in enumerate(wg["tips"]):
        d = RG.v(t) - wr0
        tips.append(tuple(wr + RG.v((d[0] * (0.62 + 0.06 * k), 30 + 10 * k + max(0.0, d[1]) * 0.3))))
    wg["elbow"], wg["wrist"], wg["tips"] = tuple(el), tuple(wr), tips
    wg["root"] = tuple(RG.v(wg["root"]) + RG.v((0, 6)))
    wg["nholes"] = wg.get("nholes", 5) * 2 + 3; wg["tears"] = wg.get("tears", 4) + 6; wg["hole_k"] = 1.45
    wg["sag"] = [0.42, 0.45, 0.48, 0.5]; wg["bends"] = [2.0 if near else -2.0] * 4
    return wg


def break_wings(R):
    R = copy.deepcopy(R)
    R["wings"] = [broken_wing(R["wings"][0], False), broken_wing(R["wings"][1], True)]
    return R


TAG_FUNCS = [("idle", tag_idle), ("walk", tag_walk), ("bite", tag_bite), ("claw", tag_claw), ("tail", tag_tail),
             ("breath", tag_breath), ("roar", tag_roar), ("takeoff", tag_takeoff), ("fly", tag_fly),
             ("flybreath", tag_flybreath), ("dive", tag_dive), ("land", tag_land), ("stagger", tag_stagger),
             ("death", tag_death), ("rushprep", tag_rushprep), ("rush", tag_rush), ("rushstop", tag_rushstop),
             ("buffet", tag_buffet), ("slam", tag_slam)]


# =========================================================================== per-frame geometry for the meta
def frame_geom(P, info, img):
    a = np.array(img)[..., 3] > 0
    tb = info["tb"]
    s_hip = P["s_hip"]
    body = tb.mask & (tb.arc > s_hip - 22)
    ys, xs = np.nonzero(body)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    else:
        x0, x1, y0, y1 = 100, 200, 100, 168
    # legs / feet reach the floor
    feet_y = max([f["foot"][1] for f in P["legs"]] + [h["hand"][1] for h in P["arms"]])
    y1 = max(y1, int(feet_y))
    hb = [int(x0), int(y0), int(x1 - x0 + 1), int(y1 - y0 + 1)]
    m = info["mouth"]
    mouth = [round(float(m[0][0]), 1), round(float(m[0][1]), 1), round(float(m[1]), 1)] if m else None
    club = tb.at(2.0)[0]
    hand = P["arms"][1]["hand"]
    head = P["head"]
    return dict(hb=hb, mouth=mouth, club=[round(float(club[0]), 1), round(float(club[1]), 1)],
                hand=[round(float(hand[0]), 1), round(float(hand[1]), 1)], head=[round(float(head[0]), 1), round(float(head[1]), 1)])


def rect_around(pts, pad, floor=None):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    if floor is not None:
        y1 = max(y1, floor)
    return [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]


# =========================================================================== build
def render_all(phase):
    frames, tags, geoms = [], [], {}
    for name, fn in TAG_FUNCS:
        if ONLY and name not in ONLY:
            continue
        seqf = fn()
        a = len(frames)
        geoms[name] = []
        for i, (R, ms, ex) in enumerate(seqf):
            P = build(break_wings(R) if phase == 3 else R)
            seed = 1000 * phase + 37 * len(frames) + 11
            storm = ex.get("storm", 1.0) * {1: 1.0, 2: 1.25, 3: 1.7}[phase]
            img, info = render(P, phase=min(phase, 2), seed=seed, storm=storm)
            frames.append(dict(ms=ms, img=img))
            geoms[name].append(frame_geom(P, info, img))
        tags.append((name, a, len(frames) - 1))
        print(f"  {name}: {len(seqf)} frames", flush=True)
    return frames, tags, geoms


def attacks_from(geoms):
    G = geoms
    atk, tel, spawn = {}, {}, {}
    if "bite" in G:
        g = G["bite"]
        heads = [g[i]["mouth"][:2] for i in (6, 7)]
        atk["bite"] = dict(active=[6, 7], hit=rect_around(heads, 22, floor=AY))
        tel["bite"] = dict(frame=4, at=g[4]["mouth"][:2])
    if "claw" in G:
        g = G["claw"]
        pts = [g[i]["hand"] for i in (5, 6)]
        atk["claw"] = dict(active=[5, 6], hit=rect_around(pts, 20, floor=AY))
        tel["claw"] = dict(frame=4, at=g[4]["hand"])
    if "tail" in G:
        g = G["tail"]
        pts = [g[i]["club"] for i in (6, 7)] + [[70, 150], [40, 160]]
        r = rect_around(pts, 14, floor=AY)
        r[0] = max(0, r[0] - 10); r[2] = 150 - r[0]
        atk["tail"] = dict(active=[6, 7], hit=r)
        tel["tail"] = dict(frame=5, at=g[5]["club"])
    if "land" in G:
        atk["land"] = dict(active=[2, 2], hit=[40, 120, 230, 48])
    if "dive" in G:
        g = G["dive"]
        hb = g[3]["hb"]
        atk["dive"] = dict(active=[2, 5], hit=[hb[0] + 20, hb[1], hb[2] - 10, hb[3]])
        tel["dive"] = dict(frame=1, at=g[1]["mouth"][:2])
    if "breath" in G:
        tel["breath"] = dict(frame=5, at=G["breath"][5]["mouth"][:2])
        spawn["breath"] = dict(frame=6, at=G["breath"][6]["mouth"][:2])
    if "roar" in G:
        spawn["roar"] = dict(frame=5, at=G["roar"][5]["mouth"][:2])
    return atk, tel, spawn


def write_meta(geoms):
    atk, tel, spawn = attacks_from(geoms)
    meta = dict(native=1, frame=[W, H], anchor=[AX, AY], hurtbox=geoms["idle"][0]["hb"] if "idle" in geoms else [100, 100, 100, 68],
                attacks=atk, telegraph=tel, spawn=spawn,
                frames={k: [dict(hb=g["hb"], mouth=g["mouth"], hand=g["hand"], club=g["club"]) for g in v] for k, v in geoms.items()},
                notes="faces right; ground line y=168 (anchor). Airborne tags (takeoff 3+, fly, flybreath, dive, land 0-1) keep "
                      "the anchor as the ground-equivalent reference; the body is drawn ~80px above it. Per-frame hurtboxes in "
                      "frames[tag][i].hb (torso + neck + head + legs, no wings / tail). mouth = [x, y, angle deg] for the breath "
                      "beam (frames 6-11 of breath, all of flybreath). tail hits BEHIND the drake (low sweep).")
    json.dump(meta, open(os.path.join(ASSETS, "cindervane_meta.json"), "w"), indent=1)
    return meta


def preview(frames, tags, name, geoms=None, scale=2):
    rows = []
    for t, a, b in tags:
        rows.append((t, frames[a:b + 1]))
    maxn = max(len(r[1]) for r in rows)
    pw, ph = W // 2 * scale, H // 2 * scale      # half-size cells at `scale` -> keeps the sheet readable
    cw, ch = W, H
    S = Image.new("RGBA", (maxn * cw + 60, len(rows) * ch), (58, 60, 68, 255))
    d = ImageDraw.Draw(S)
    for r, (t, fr) in enumerate(rows):
        d.text((4, r * ch + 4), t, fill=(230, 230, 230, 255))
        for i, f in enumerate(fr):
            S.alpha_composite(f["img"], (60 + i * cw, r * ch))
            d.line([(60 + i * cw, r * ch + AY), (60 + i * cw + cw - 1, r * ch + AY)], fill=(90, 96, 110, 255))
            if geoms:
                hb = geoms[t][i]["hb"]
                d.rectangle([60 + i * cw + hb[0], r * ch + hb[1], 60 + i * cw + hb[0] + hb[2], r * ch + hb[1] + hb[3]], outline=(60, 220, 90, 255))
    S.save(os.path.join(PREV, name))
    return S


def main():
    os.makedirs(PREV, exist_ok=True)
    print("phase 1")
    f1, tags, geoms = render_all(1)
    preview(f1, tags, "cindervane.png")
    preview(f1, tags, "cindervane_hb.png", geoms)
    if not ONLY:
        write_meta(geoms)
    if PREVIEW_ONLY:
        return
    print("phase 2")
    f2, tags2, _ = render_all(2)
    preview(f2, tags2, "cindervane_p2.png")
    print("phase 3 (broken wings)")
    f3, tags3, _ = render_all(3)
    preview(f3, tags3, "cindervane_p3.png")
    import spire_ase
    for name, fr in (("cindervane", f1), ("cindervane_p2", f2), ("cindervane_p3", f3)):
        spire_ase.build_grid(name, W, H, ["Drake"], [dict(ms=f["ms"], cels={"Drake": f["img"]}) for f in fr], tags, COLS)
    print("built", len(f1), "frames x3")


if __name__ == "__main__":
    main()
