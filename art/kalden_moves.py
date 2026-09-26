#!/usr/bin/env python3
"""Ser Kalden rework (agent K): the new movesets, keyed on the same rig as art/gen_kalden.py.

    python3 art/kalden_moves.py              build kalden_b(+_p2), kalden_c, fx_kd_tendril, fx_kd_pool (+ metas)
    python3 art/kalden_moves.py --preview    previews + metas only (no Aseprite)
    python3 art/kalden_moves.py --only quick3,spin4 --preview

Sheets (128x72 frames, anchor (40, 72) -- same body placement as kalden.png, just more room in front for reach):
    kalden_b / kalden_b_p2   phase-1 sword strings, rendered in both looks (phase 2 re-uses them rot-grown):
                             quick3 spin4 rising3 stab5 charge kick plunge lunge feint
    kalden_c                 phase-2 only (rot arm): rotcombo tendrils grab grabhold berserk
    fx_kd_tendril            40x72, 8 frames: a rot whip erupting from the floor (pivot bottom-centre)
    fx_kd_pool               56x14, 4 frames loop: a bubbling rot pool (pivot bottom-centre)
Metas: assets/kalden_b_meta.json (shared by kalden_b_p2), assets/kalden_c_meta.json.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import gen_kalden as GK  # noqa: E402  (sets up the Kalden palette/rig; its main() does not run on import)
import enemy_kit as K  # noqa: E402
import asebuild  # noqa: E402
from enemy_kit import Layer, FXLayer, Rig, ID, add, sub, lerp, ip, line, bezier, hash01, mask_disc  # noqa: E402

W, H = 128, 72
AX = 40
FLOOR = H - 1
BUILD = "--preview" not in sys.argv
P_, up = GK.P_, GK.up
WB = dict(wl="WeaponBack")

# ---------------------------------------------------------------- stock body poses (from gen_kalden)
RAISE = dict(P=(38.4, 52.0), C=(37.4, 41.2), Hd=(37.8, 31.0), hup=(-0.22, -1), fb=(30.0, 71), ff=(46.5, 71))
LUNGE = dict(P=(44.4, 53.6), C=(48.4, 43.2), Hd=(51.6, 33.8), hup=(0.42, -1), fb=(31.0, 71), ff=(56.0, 71))
LOW = dict(P=(41.6, 54.2), C=(41.0, 43.4), Hd=(42.0, 33.2), hup=(-0.05, -1), fb=(30.5, 71), ff=(53.5, 71))
RISE = dict(P=(45.0, 52.2), C=(48.2, 41.6), Hd=(50.8, 31.6), hup=(0.3, -1), fb=(33.0, 71), ff=(57.0, 71))
COIL = dict(P=(40.0, 53.0), C=(37.6, 42.4), Hd=(37.4, 32.4), hup=(-0.2, -1), fb=(29.0, 71), ff=(49.0, 71))
CLEAVE = dict(P=(46.4, 54.4), C=(51.0, 44.2), Hd=(54.4, 34.8), hup=(0.38, -1), fb=(31.0, 71), ff=(59.0, 71))
REC1 = dict(P=(43.0, 53.2), C=(44.6, 42.6), Hd=(46.6, 32.8), hup=(0.25, -1), fb=(31.5, 71), ff=(54.0, 71))
REC2 = dict(P=(40.6, 52.0), C=(42.0, 41.0), Hd=(43.6, 30.8), fb=(32.0, 71), ff=(49.0, 71))
DRAW = dict(P=(37.6, 52.6), C=(35.8, 42.2), Hd=(36.2, 32.2), hup=(-0.12, -1), fb=(29.0, 71), ff=(47.0, 71))
TLUNGE = dict(P=(48.0, 55.2), C=(54.2, 46.2), Hd=(58.6, 37.4), hup=(0.55, -1), fb=(29.5, 71), ff=(62.5, 71))
CROUCH = dict(P=(39.0, 56.0), C=(41.6, 45.6), Hd=(44.0, 35.8), hup=(0.25, -1), fb=(31.0, 71), ff=(48.0, 71))
LAND = dict(P=(45.0, 57.0), C=(50.4, 47.4), Hd=(54.2, 38.6), hup=(0.5, -1), fb=(31.5, 71), ff=(58.0, 71))


def mv(d, dx=0.0, dy=0.0, **kw):
    """Shift a body pose (P, C, Hd, feet stay unless given) and override keys."""
    q = dict(d)
    for k in ("P", "C", "Hd"):
        q[k] = (q[k][0] + dx, q[k][1] + dy)
    q.update(kw)
    return q


# =========================================================================== phase-1 sword strings (kalden_b)
def a_quick3():
    """fast - fast - (hold) - heavy: two quick cuts, then a delayed overhead that craters the floor."""
    return [
        (110, P_(**RAISE, hf=(44.0, 38.0), wang=-80)),
        (170, P_(**mv(RAISE, -0.6, 0.4), hf=(38.0, 34.0), wang=-138, eye=2, **WB)),
        (50, P_(**LUNGE, hf=(59.0, 42.0), wang=8, wind=4, smear=dict(g0=(38.0, 34.0), a0=-138, mid=(50.0, 24.0), start=0.1))),
        (70, P_(**LUNGE, hf=(55.0, 51.0), wang=52, wind=3, smear=dict(g0=(59.0, 42.0), a0=8, taper=0.4, u0=18))),
        (50, P_(**RISE, hf=(58.0, 40.0), wang=-44, wind=4, smear=dict(g0=(55.0, 51.0), a0=52, mid=(62.0, 52.0), start=0.05))),
        (80, P_(**RISE, hf=(52.0, 31.0), wang=-100, wind=2, smear=dict(g0=(58.0, 40.0), a0=-44, taper=0.3, u0=22, start=0.3))),
        (150, P_(**mv(COIL, 0, -0.6), hf=(37.0, 25.0), wang=-158, eye=2, **WB)),
        (360, P_(**mv(COIL, -0.4, -0.2), hf=(36.0, 24.0), wang=-162, eye=2, glint=(22.0, 12.0), **WB)),
        (60, P_(**LAND, hf=(63.0, 52.0), wang=34, wind=5, smear=dict(g0=(36.0, 24.0), a0=-162, mid=(50.0, 10.0), start=0.1))),
        (110, P_(**LAND, hf=(63.0, 54.0), wang=40, impact=1, wind=3)),
        (200, P_(**LAND, hf=(62.0, 55.0), wang=40, impact=2)),
        (200, P_(**REC1, hf=(53.0, 52.0), wang=-10)),
    ]


def a_spin4():
    """forehand, backhand, diagonal, then a full turn into a spinning cleave that cuts on both sides."""
    turn = dict(P=(40.0, 53.0), C=(41.6, 42.4), Hd=(43.2, 32.4), hup=(0.15, -1), fb=(30.0, 71), ff=(50.0, 71))
    return [
        (110, P_(**REC2, hf=(45.0, 46.0), wang=-30)),
        (160, P_(**COIL, hf=(34.0, 44.0), wang=-172, eye=2, **WB)),
        (50, P_(**CLEAVE, hf=(62.0, 46.0), wang=4, wind=4, flat=dict(c=(52.0, 46.0), rx=40.0, ry=8.0, th0=-160, th1=8, w=6.0))),
        (80, P_(**LOW, hf=(42.0, 57.0), wang=158, wind=3, **WB)),
        (50, P_(**RISE, hf=(58.0, 40.0), wang=-48, wind=4, smear=dict(g0=(42.0, 57.0), a0=158, mid=(56.0, 66.0), start=0.08))),
        (80, P_(**mv(LOW, 0.4), hf=(44.0, 36.0), wang=-150, **WB)),
        (50, P_(**LUNGE, hf=(60.0, 44.0), wang=16, wind=4, smear=dict(g0=(44.0, 36.0), a0=-150, mid=(54.0, 24.0), start=0.1))),
        (90, P_(**mv(turn, 0.6), hf=(52.0, 52.0), wang=60, wind=2)),
        (110, P_(**turn, hf=(40.0, 50.0), wang=176, wind=-4, eye=2, mirror=True, **WB)),
        (60, P_(**CLEAVE, hf=(64.0, 47.0), wang=2, wind=6, flat=dict(c=(40.0, 46.0), rx=48.0, ry=9.0, th0=-190, th1=170, w=7.0))),
        (100, P_(**CLEAVE, hf=(60.0, 50.0), wang=30, wind=4, flat=dict(c=(40.0, 46.0), rx=48.0, ry=9.0, th0=-60, th1=190, w=4.0, fade=0.5))),
        (220, P_(**REC1, hf=(55.0, 54.0), wang=38)),
        (200, P_(**REC2, hf=(50.0, 50.0), wang=-30)),
    ]


def a_rising3():
    """a rising cut from the floor, up into an overhead that splits the ground, then a stab out of the crouch."""
    return [
        (140, P_(**CROUCH, hf=(40.0, 58.0), wang=164, **WB)),
        (240, P_(**mv(CROUCH, -0.4, 1.0), hf=(38.0, 59.0), wang=168, eye=2, dust=2, **WB)),
        (60, P_(**RISE, hf=(59.0, 36.0), wang=-68, wind=4, smear=dict(g0=(38.0, 59.0), a0=168, mid=(56.0, 68.0), start=0.06))),
        (90, up(P_(**mv(RISE, 0, -1.0), hf=(54.0, 30.0), wang=-100, wind=3, lift=4,
                   smear=dict(g0=(59.0, 36.0), a0=-68, taper=0.3, u0=24, start=0.3)), 2)),
        (130, up(P_(**mv(RAISE, 1.0, -1.0), hf=(40.0, 22.0), wang=-164, lift=6, eye=2, **WB), 4)),
        (60, P_(**LAND, hf=(63.0, 53.0), wang=38, wind=5, smear=dict(g0=(40.0, 18.0), a0=-164, mid=(56.0, 8.0), start=0.1))),
        (120, P_(**LAND, hf=(63.0, 54.0), wang=40, impact=1, wind=3)),
        (150, P_(**LAND, hf=(62.0, 55.0), wang=40, impact=2)),
        (170, P_(**mv(DRAW, 0, 1.5), hf=(34.0, 49.0), wang=-3, eye=2, glint=(64.0, 47.0))),
        (60, P_(**TLUNGE, hf=(61.5, 49.5), wang=1, wind=5, thrust=dict(u0=-30, u1=6, offs=(-3, -1, 2, 4)))),
        (130, P_(**TLUNGE, hf=(62.5, 50.0), wang=2, wind=3, thrust=dict(u0=-18, u1=4, offs=(-2, 3), flash=32))),
        (170, P_(**REC1, hf=(56.0, 52.0), wang=14)),
        (180, P_(**REC2, hf=(50.0, 50.0), wang=-36)),
    ]


def a_stab5():
    """three quick advancing stabs, a held breath, the long lunge -- and an upward flick off the end of it."""
    half = dict(P=(43.0, 54.0), C=(46.4, 44.2), Hd=(49.2, 34.4), hup=(0.35, -1), fb=(30.0, 71), ff=(56.0, 71))
    back = dict(P=(40.0, 53.2), C=(39.6, 42.8), Hd=(40.4, 32.6), hup=(0.0, -1), fb=(30.0, 71), ff=(50.0, 71))
    TH = lambda **kw: dict(u0=-24, u1=4, offs=(-2, 1, 3), **kw)
    return [
        (140, P_(**DRAW, hf=(34.0, 47.5), wang=-4)),
        (230, P_(**mv(DRAW, -0.4, 0.4), hf=(33.0, 48.0), wang=-3, eye=2, glint=(64.0, 46.5))),
        (50, P_(**half, hf=(57.0, 48.0), wang=0, wind=3, thrust=TH())),
        (70, P_(**back, hf=(42.0, 47.0), wang=-3)),
        (50, P_(**half, hf=(58.0, 45.5), wang=-5, wind=3, thrust=TH())),
        (70, P_(**back, hf=(42.0, 48.0), wang=2)),
        (50, P_(**half, hf=(58.0, 50.0), wang=4, wind=3, thrust=TH())),
        (110, P_(**mv(DRAW, -0.6, 0.6), hf=(33.0, 48.0), wang=-4, eye=2)),
        (230, P_(**mv(DRAW, -1.0, 0.8), hf=(32.0, 48.5), wang=-3, eye=2, glint=(63.0, 47.0))),
        (70, P_(**TLUNGE, hf=(61.5, 49.5), wang=1, wind=6, thrust=dict(u0=-34, u1=6, offs=(-3, -1, 2, 4)))),
        (100, P_(**TLUNGE, hf=(62.5, 50.0), wang=2, wind=3, thrust=dict(u0=-18, u1=4, offs=(-2, 3), flash=32))),
        (60, P_(**RISE, hf=(58.0, 36.0), wang=-70, wind=4, smear=dict(g0=(62.5, 50.0), a0=2, taper=0.5, u0=16))),
        (100, P_(**mv(RISE, 0, -0.6), hf=(51.0, 28.0), wang=-118, wind=2,
                 smear=dict(g0=(58.0, 36.0), a0=-70, taper=0.3, u0=24, start=0.35))),
        (200, P_(**REC1, hf=(52.0, 44.0), wang=-60)),
        (180, P_(**REC2, hf=(50.0, 50.0), wang=-40)),
    ]


def a_charge():
    """shoulder charge: the pauldron lowered like a ram, blade trailing; frames 2-5 are the run loop."""
    set_ = dict(P=(40.0, 56.0), C=(44.0, 46.4), Hd=(47.6, 37.8), hup=(0.55, -1), fb=(29.0, 71), ff=(49.0, 71))
    fr = [(160, P_(**set_, hf=(40.0, 57.0), wang=160, eye=1, **WB)),
          (300, P_(**mv(set_, -0.6, 0.8), hf=(38.0, 58.0), wang=163, eye=2, dust=2, **WB))]
    for i in range(4):
        ph = 2 * math.pi * i / 4
        c, s = math.cos(ph), math.sin(ph)
        bob = 1.2 * abs(s)
        fr.append((80, P_(P=(45.0, 55.0 + bob), C=(51.4, 46.8 + bob), Hd=(55.6, 38.8 + bob), hup=(0.7, -1),
                          ff=(47.0 + 10.0 * c, 71 - max(0.0, s) * 5.0), fb=(45.0 - 10.0 * c, 71 - max(0.0, -s) * 5.0),
                          hf=(42.0, 57.0 + bob * 0.5), wang=170, wind=6, dust=1 if i % 2 == 0 else 0, **WB)))
    fr += [(120, P_(**mv(set_, 3.0, 0.6, ff=(58.0, 71), fb=(34.0, 71)), hf=(44.0, 57.0), wang=165, dust=1, wind=4, **WB)),
           (220, P_(**REC1, hf=(52.0, 52.0), wang=-20))]
    return fr


def a_kick():
    """guard-break kick: a flat, heavy boot to the chest (unparryable, punishes a raised shield)."""
    lean = dict(P=(38.4, 52.4), C=(35.8, 41.8), Hd=(35.2, 31.6), hup=(-0.3, -1), fb=(30.0, 71))
    return [
        (110, P_(**mv(REC2, -1.0), hf=(47.0, 42.0), wang=-84)),
        (220, P_(**lean, ff=(49.0, 60.0), kf=(49.5, 50.5), hf=(45.0, 40.0), wang=-92, eye=2)),
        (60, P_(**mv(lean, -0.6, 0.2), ff=(63.0, 52.5), hf=(44.0, 40.0), wang=-100, wind=3)),
        (110, P_(**mv(lean, -0.8, 0.3), ff=(63.5, 53.0), hf=(44.0, 40.5), wang=-100, wind=2)),
        (130, P_(**lean, ff=(50.0, 62.0), kf=(49.0, 52.0), hf=(46.0, 42.0), wang=-90)),
        (160, P_(**REC2, hf=(49.0, 48.0), wang=-60)),
    ]


def a_plunge():
    """a high leap, the blade turned point-down, and a plunge onto where you stand (engine arcs him)."""
    air = dict(fb=(34.0, 63.0), ff=(46.0, 61.0))
    return [
        (150, P_(**CROUCH, hf=(44.0, 58.0), wang=160, **WB)),
        (260, P_(**mv(CROUCH, -0.4, 1.6), hf=(43.0, 60.0), wang=165, eye=2, dust=2, **WB)),
        (80, up(P_(P=(41.0, 50.0), C=(42.4, 39.0), Hd=(44.0, 29.0), hup=(0.1, -1), fb=(35.0, 70.5), ff=(46.0, 64.0),
                   hf=(50.0, 30.0), wang=-70, lift=4, dust=1), 3)),
        (120, up(P_(P=(40.0, 50.0), C=(40.8, 39.2), Hd=(42.0, 29.2), hup=(0.05, -1), **air,
                    hf=(55.0, 33.0), wang=93, lift=10), 8)),
        (220, up(P_(P=(40.0, 50.0), C=(40.8, 39.4), Hd=(41.8, 29.4), hup=(0.08, -1), **air,
                    hf=(56.0, 34.0), wang=92, lift=6, eye=2, glint=(57.0, 62.0)), 9)),
        (80, up(P_(P=(41.0, 51.0), C=(42.6, 40.4), Hd=(44.0, 30.6), hup=(0.12, -1), fb=(35.0, 66.0), ff=(47.0, 64.0),
                   hf=(57.0, 38.0), wang=91, lift=-8, wind=2), 5)),
        (70, P_(**mv(LAND, -2.0), hf=(59.0, 49.0), wang=89, impact=1, wind=3)),
        (160, P_(**mv(LAND, -2.0), hf=(59.0, 49.4), wang=89, impact=2)),
        (200, P_(**CROUCH, hf=(55.0, 44.0), wang=86)),
        (180, P_(**REC2, hf=(50.0, 50.0), wang=-30)),
    ]


def a_lunge():
    """the long lunge that follows a backstep: a low dash with the blade level (engine drives the distance)."""
    low = dict(P=(38.0, 56.0), C=(36.6, 45.8), Hd=(37.4, 35.8), hup=(0.0, -1), fb=(28.0, 71), ff=(47.0, 71))
    far = dict(P=(50.0, 56.4), C=(57.0, 48.4), Hd=(61.6, 40.0), hup=(0.7, -1), fb=(27.0, 71), ff=(66.0, 71))
    return [
        (100, P_(**low, hf=(33.0, 52.0), wang=-3, eye=2)),
        (200, P_(**mv(low, -0.4, 0.4), hf=(32.0, 52.4), wang=-2, eye=2, glint=(63.0, 51.0))),
        (60, P_(**far, hf=(65.0, 53.0), wang=2, wind=7, lift=-2, thrust=dict(u0=-40, u1=6, offs=(-3, -1, 2, 4)))),
        (60, P_(**far, hf=(66.0, 53.4), wang=2, wind=6, thrust=dict(u0=-34, u1=5, offs=(-2, 1, 3)))),
        (100, P_(**far, hf=(66.5, 53.5), wang=3, wind=3, thrust=dict(u0=-16, u1=4, offs=(-2, 3), flash=32))),
        (170, P_(**mv(TLUNGE, -2.0), hf=(58.0, 54.0), wang=18)),
        (170, P_(**REC1, hf=(52.0, 51.0), wang=-20)),
    ]


def a_feint():
    """the overhead that isn't: a raise, a twitch that stops short, a held breath (engine varies it), then the cut."""
    return [
        (130, P_(**RAISE, hf=(43.0, 34.0), wang=-100)),
        (230, P_(**mv(RAISE, -0.6, 0.4), hf=(37.0, 25.0), wang=-150, eye=2, **WB)),
        (90, P_(**mv(RAISE, 2.2, 0.4), hf=(47.0, 25.0), wang=-112, wind=2)),
        (320, P_(**mv(RAISE, -0.8, 0.6), hf=(36.0, 24.0), wang=-156, eye=2, glint=(20.0, 12.0), **WB)),
        (50, P_(**LUNGE, hf=(60.0, 40.0), wang=-2, wind=5, smear=dict(g0=(36.0, 24.0), a0=-156, mid=(48.0, 16.0), start=0.1))),
        (100, P_(**LUNGE, hf=(56.0, 51.0), wang=44, wind=3, smear=dict(g0=(60.0, 40.0), a0=-2, taper=0.4, u0=18))),
        (200, P_(**REC1, hf=(53.0, 52.0), wang=10)),
    ]


# =========================================================================== phase-2 rot moves (kalden_c)
PLANT = dict(sword=((45.0, 51.0), 92), hb=(45.0, 51.0))


def a_rotcombo():
    """cut, rising backhand, then the arm stretches: a long flat sweep and an overhead slam that leaves rot."""
    return [
        (110, P_(**RAISE, hf=(43.0, 34.0), wang=-100, rotglow=0.3)),
        (190, P_(**mv(RAISE, -0.6, 0.4), hf=(37.0, 25.0), wang=-150, eye=2, **WB)),
        (50, P_(**LUNGE, hf=(59.0, 40.0), wang=-4, wind=4, smear=dict(g0=(37.0, 25.0), a0=-150, mid=(48.0, 16.0), start=0.1))),
        (70, P_(**LUNGE, hf=(56.0, 50.0), wang=42, wind=3, smear=dict(g0=(59.0, 40.0), a0=-4, taper=0.4, u0=18))),
        (60, P_(**RISE, hf=(46.0, 32.0), wang=-146, wind=3, smear=dict(g0=(56.0, 50.0), a0=42, mid=(64.0, 40.0), start=0.05))),
        (100, P_(**COIL, hf=(35.0, 42.0), wang=-176, eye=2, rotglow=0.7, **WB)),
        (190, P_(**mv(COIL, -0.4, 0.3), hf=(33.0, 42.0), wang=-178, eye=2, rotglow=1.0, **WB)),
        (70, P_(**CLEAVE, hf=(76.0, 46.0), wang=4, armlen=2.1, wind=6, rotglow=1.0,
                flat=dict(c=(60.0, 47.0), rx=54.0, ry=9.5, th0=-165, th1=8, w=7.0))),
        (100, P_(**CLEAVE, hf=(70.0, 52.0), wang=32, armlen=1.9, wind=4,
                 flat=dict(c=(60.0, 47.0), rx=54.0, ry=9.5, th0=-40, th1=160, w=4.0, fade=0.5))),
        (140, P_(**mv(RAISE, 1.0), hf=(42.0, 20.0), wang=-160, armlen=1.3, eye=2, rotglow=1.0, **WB)),
        (220, P_(**mv(RAISE, 0.4, 0.3), hf=(41.0, 18.0), wang=-164, armlen=1.35, eye=2, rotglow=1.0, glint=(26.0, 8.0), **WB)),
        (60, P_(**LAND, hf=(74.0, 56.0), wang=42, armlen=1.9, wind=5, rotglow=1.0,
                smear=dict(g0=(41.0, 18.0), a0=-164, mid=(64.0, 6.0), start=0.1))),
        (120, P_(**LAND, hf=(75.0, 58.0), wang=46, armlen=1.95, impact=1, wind=3, rotglow=1.0)),
        (170, P_(**LAND, hf=(74.0, 58.0), wang=46, armlen=1.9, impact=2, rotglow=0.6)),
        (200, P_(**REC1, hf=(56.0, 53.0), wang=30, armlen=1.2)),
        (200, P_(**REC2, hf=(50.0, 50.0), wang=-30)),
    ]


def a_tendrils():
    """blade reversed and driven into the floor; the arm pumps rot into the ground (tendrils erupt, engine)."""
    kneel = dict(P=(40.0, 57.4), C=(43.0, 47.4), Hd=(46.2, 38.4), hup=(0.4, -1), fb=(29.0, 71), ff=(50.0, 71))
    return [
        (150, P_(**RAISE, hf=(50.0, 29.0), wang=-86, rotglow=0.4)),
        (320, P_(**mv(RAISE, -0.4, -0.6), hf=(48.0, 24.0), wang=-90, eye=2, rotglow=1.0, burst=1.5, glint=(48.0, 4.0))),
        (70, P_(**kneel, hf=(58.0, 45.0), wang=88, impact=1, rotglow=1.0, wind=3)),
        (380, P_(**kneel, hf=(58.0, 45.5), wang=88, rotglow=1.0, burst=2, eye=2)),
        (300, P_(**mv(kneel, 0.4, 0.3), hf=(58.0, 45.6), wang=88, rotglow=0.8, burst=2.5, eye=2)),
        (200, P_(**CROUCH, hf=(55.0, 40.0), wang=87)),
        (200, P_(**REC2, hf=(50.0, 50.0), wang=-30)),
    ]


def a_grab():
    """the sword is planted; the rot hand tears out of its gauntlet and shoots out to seize you."""
    lean = dict(P=(41.0, 53.0), C=(44.6, 42.6), Hd=(47.8, 32.8), hup=(0.35, -1), fb=(30.0, 71), ff=(52.0, 71))
    back = dict(P=(39.4, 53.0), C=(38.4, 42.4), Hd=(38.8, 32.2), hup=(-0.15, -1), fb=(30.0, 71), ff=(50.0, 71))
    return [
        (140, P_(**REC2, **PLANT, hf=(50.0, 44.0), claw="open", rotglow=0.3)),
        (300, P_(**back, **PLANT, hf=(35.0, 38.0), claw="open", rotglow=1.0, eye=2)),
        (60, P_(**lean, **PLANT, hf=(90.0, 44.0), armlen=3.0, claw="open", rotglow=1.0, wind=4)),
        (100, P_(**lean, **PLANT, hf=(95.0, 45.0), armlen=3.3, claw="open", rotglow=0.8, wind=3)),
        (160, P_(**lean, **PLANT, hf=(70.0, 49.0), armlen=2.1, claw="shut", rotglow=0.4)),
        (200, P_(**REC2, **PLANT, hf=(51.0, 47.0), claw="shut")),
        (200, P_(**REC2, hf=(49.0, 49.0), wang=-50)),
    ]


GRAB_HOLD = [(70.0, 43.0), (68.0, 38.0), (69.0, 39.0), (74.0, 64.0), (74.0, 64.0), (54.0, 48.0)]


def a_grabhold():
    """you, held up in the rot hand: squeezed twice (rot floods in), then smashed into the floor."""
    lift = dict(P=(39.0, 52.6), C=(38.8, 41.6), Hd=(39.6, 31.4), hup=(-0.05, -1), fb=(30.0, 71), ff=(50.0, 71))
    slam = dict(P=(42.0, 54.6), C=(46.0, 44.4), Hd=(49.4, 35.2), hup=(0.45, -1), fb=(30.0, 71), ff=(54.0, 71))
    h = GRAB_HOLD
    return [
        (120, P_(**lift, **PLANT, hf=h[0], armlen=2.1, claw="shut", rotglow=0.6)),
        (220, P_(**mv(lift, -0.4, -0.3), **PLANT, hf=h[1], armlen=2.0, claw="shut", rotglow=1.0, eye=2)),
        (220, P_(**mv(lift, -0.6, -0.4), **PLANT, hf=h[2], armlen=2.0, claw="shut", rotglow=1.0, eye=2, burst=2)),
        (70, P_(**slam, **PLANT, hf=h[3], armlen=2.2, claw="shut", rotglow=1.0, wind=4)),
        (220, P_(**slam, **PLANT, hf=h[4], armlen=2.2, claw="shut", rotglow=0.6, dust=2)),
        (220, P_(**REC2, **PLANT, hf=h[5], armlen=1.1, claw="shut")),
    ]


def a_berserk():
    """the last string, at the end of him: six wild cuts, the arm stretching further each time, then everything erupts."""
    return [
        (100, P_(**mv(COIL, 0, 0.6), hf=(40.0, 30.0), wang=-150, eye=2, rotglow=1.0, **WB)),
        (170, P_(**mv(COIL, -0.6, 1.0), hf=(38.0, 28.0), wang=-154, eye=2, rotglow=1.0, burst=1, **WB)),
        (50, P_(**LUNGE, hf=(62.0, 42.0), wang=10, armlen=1.35, wind=4, smear=dict(g0=(38.0, 28.0), a0=-154, mid=(52.0, 18.0), start=0.1))),
        (55, P_(**RISE, hf=(50.0, 29.0), wang=-138, armlen=1.2, wind=4, smear=dict(g0=(62.0, 42.0), a0=10, mid=(66.0, 30.0), start=0.05))),
        (55, P_(**CLEAVE, hf=(67.0, 45.0), wang=20, armlen=1.55, wind=5, smear=dict(g0=(50.0, 29.0), a0=-138, mid=(62.0, 20.0), start=0.1))),
        (80, P_(**mv(CROUCH, 0, -0.6), hf=(40.0, 57.0), wang=165, rotglow=1.0, eye=2, **WB)),
        (55, P_(**RISE, hf=(74.0, 34.0), wang=-58, armlen=1.95, wind=5, smear=dict(g0=(40.0, 57.0), a0=165, mid=(64.0, 68.0), start=0.05))),
        (60, P_(**mv(RISE, 0, -0.6), hf=(60.0, 24.0), wang=-128, armlen=1.45, wind=3)),
        (60, P_(**CLEAVE, hf=(80.0, 47.0), wang=2, armlen=2.3, wind=6,
                flat=dict(c=(62.0, 47.0), rx=58.0, ry=9.5, th0=-165, th1=8, w=7.0))),
        (90, P_(**CLEAVE, hf=(72.0, 53.0), wang=36, armlen=2.0, wind=4,
                flat=dict(c=(62.0, 47.0), rx=58.0, ry=9.5, th0=-40, th1=160, w=4.0, fade=0.5))),
        (140, P_(**mv(RAISE, 0.6), hf=(40.0, 19.0), wang=-164, armlen=1.3, eye=2, rotglow=1.0, burst=2, **WB)),
        (240, P_(**mv(RAISE, 0.2, 0.3), hf=(39.0, 18.0), wang=-166, armlen=1.3, eye=2, rotglow=1.0, burst=3, glint=(24.0, 8.0), **WB)),
        (60, P_(**LAND, hf=(74.0, 56.0), wang=42, armlen=2.0, wind=5, burst=4,
                smear=dict(g0=(39.0, 18.0), a0=-166, mid=(62.0, 6.0), start=0.1))),
        (130, P_(**LAND, hf=(75.0, 58.0), wang=46, armlen=2.0, impact=1, burst=5)),
        (170, P_(**LAND, hf=(74.0, 58.0), wang=46, armlen=1.9, impact=2, burst=6)),
        (200, P_(**REC1, hf=(56.0, 53.0), wang=30, armlen=1.2, burst=7)),
        (200, P_(**REC2, hf=(50.0, 50.0), wang=-30, burst=8)),
    ]


TAGS_B = [("quick3", a_quick3), ("spin4", a_spin4), ("rising3", a_rising3), ("stab5", a_stab5), ("charge", a_charge),
          ("kick", a_kick), ("plunge", a_plunge), ("lunge", a_lunge), ("feint", a_feint)]
TAGS_C = [("rotcombo", a_rotcombo), ("tendrils", a_tendrils), ("grab", a_grab), ("grabhold", a_grabhold),
          ("berserk", a_berserk)]
LAYERS = GK.LAYERS


# =========================================================================== render
def render(p, fi, sw, phase):
    mirror = p.pop("mirror", False) if isinstance(p, dict) else False
    Ls, info = GK.draw(p, fi, sw, phase)
    imgs = {n: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for n, v in Ls.items() if v is not None}
    if mirror:   # a frame seen from behind, mid-turn: mirror about the anchor column
        out = {}
        for n, im in imgs.items():
            o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            fl = im.transpose(Image.FLIP_LEFT_RIGHT)          # x -> W-1-x ; we want x -> 2*AX-1-x
            o.paste(fl, (2 * AX - W, 0))
            out[n] = o
        imgs = out
        info = dict(info)
        info["hit"] = {(2 * AX - 1 - x, y) for x, y in info["hit"]}
    return imgs, info


def render_set(tagdefs, phases, only=None):
    out = {ph: [] for ph in phases}
    infos, tags, n = {}, [], 0
    for tag, fn in tagdefs:
        fr = fn()
        if only and tag not in only:
            continue
        drv = [p["C"][0] for _, p in fr]
        sway = K.spring(drv, loop=False, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in phases:
                imgs, info = render(dict(p), a + k, sway[k], ph)
                out[ph].append((ms, imgs))
                info["pose"] = p
                if ph == phases[0]:
                    infos[tag].append(info)
                else:
                    infos[tag][-1]["p2"] = info
            n += 1
        tags.append((tag, a, n - 1))
        print("rendered", tag, len(fr))
    return out, infos, tags


# =========================================================================== meta
def bbox(pts, pad=0):
    pts = [p for p in pts if 0 <= p[0] < W and 0 <= p[1] < H]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def union(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def win(infos, tag, a, b, both=False, extra=None, floor=True, only_extra=False):
    rs = {}
    for k in range(a, b + 1):
        it = infos[tag][k]
        pts = set() if only_extra else set(it["hit"]) | (it["p2"]["hit"] if "p2" in it else set())
        if not both:
            pts = {q for q in pts if q[0] >= AX + 2}
        r = bbox(pts) if pts else None
        if extra:
            e = extra(k)
            if e:
                r = union([r, e]) if r else e
        if r is None:
            continue
        if floor:
            r[3] = H - r[1]
        rs[str(k)] = r
    return {"active": [a, b], "hit": union(list(rs.values())), "rects": rs}


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


def meta_b(infos):
    I = infos

    def kick_rect(k):
        f = I["kick"][k]["pose"]["ff"]
        return [int(f[0]) - 6, int(f[1]) - 7, 14, 12]

    def body_rect(k):
        p = I["charge"][k]["pose"]
        return [int(p["C"][0]) - 2, int(p["Hd"][1]) - 4, 16, 34]
    at = {
        "quick3": {"windows": [win(I, "quick3", 2, 3), win(I, "quick3", 4, 5), win(I, "quick3", 8, 9)]},
        "spin4": {"windows": [win(I, "spin4", 2, 3), win(I, "spin4", 4, 4), win(I, "spin4", 6, 6), win(I, "spin4", 9, 10, both=True)]},
        "rising3": {"windows": [win(I, "rising3", 2, 3), win(I, "rising3", 5, 6), win(I, "rising3", 9, 10)]},
        "stab5": {"windows": [win(I, "stab5", 2, 2), win(I, "stab5", 4, 4), win(I, "stab5", 6, 6), win(I, "stab5", 9, 10),
                              win(I, "stab5", 11, 12)]},
        "charge": {"windows": [win(I, "charge", 2, 6, extra=body_rect, only_extra=True)]},
        "kick": {"windows": [win(I, "kick", 2, 3, extra=kick_rect, floor=False, only_extra=True)]},
        "plunge": {"windows": [win(I, "plunge", 6, 7)]},
        "lunge": {"windows": [win(I, "lunge", 2, 4)]},
        "feint": {"windows": [win(I, "feint", 4, 5)]},
    }
    tel = {
        "quick3": {"frame": 7, "at": pt(I["quick3"][7]["tip"])},
        "spin4": {"frame": 8, "at": [40, 40]},
        "rising3": {"frame": 1, "at": pt(I["rising3"][1]["tip"])},
        "stab5": {"frame": 1, "at": [64, 46]},
        "charge": {"frame": 1, "at": [52, 36]},
        "kick": {"frame": 1, "at": [50, 58]},
        "plunge": {"frame": 1, "at": [46, 38]},
        "lunge": {"frame": 1, "at": [63, 51]},
        "feint": {"frame": 3, "at": pt(I["feint"][3]["tip"])},
    }
    return at, tel


def meta_c(infos):
    I = infos

    def claw_rect(k):
        h = I["grab"][k]["pose"]["hf"]
        return [int(h[0]) - 4, int(h[1]) - 9, 14, 18]
    at = {
        "rotcombo": {"windows": [win(I, "rotcombo", 2, 3), win(I, "rotcombo", 4, 4), win(I, "rotcombo", 7, 8), win(I, "rotcombo", 11, 12)]},
        "tendrils": {"windows": [win(I, "tendrils", 2, 2)]},
        "grab": {"windows": [win(I, "grab", 2, 3, extra=claw_rect, floor=False)]},
        "berserk": {"windows": [win(I, "berserk", 2, 2), win(I, "berserk", 3, 3), win(I, "berserk", 4, 4), win(I, "berserk", 6, 7),
                                win(I, "berserk", 8, 9), win(I, "berserk", 12, 14, both=True)]},
    }
    tel = {
        "rotcombo": {"frame": 1, "at": pt(I["rotcombo"][1]["tip"])},
        "tendrils": {"frame": 1, "at": [48, 6]},
        "grab": {"frame": 1, "at": [35, 38]},
        "berserk": {"frame": 1, "at": pt(I["berserk"][1]["tip"])},
    }
    pts = {"grabhold": {"hold": [pt(h) for h in GRAB_HOLD]},
           "rotcombo": {"slam": [pt(I["rotcombo"][12]["tip"])]},
           "tendrils": {"stab": [pt(I["tendrils"][2]["tip"])]}}
    return at, tel, pts


def base_meta(at, tel, extra=None):
    hb = json.load(open(os.path.join(asebuild.ASSETS, "kalden_meta.json")))["hurtbox"]
    m = {"native": 1, "frame": [W, H], "anchor": [AX, H], "hurtbox": hb, "attacks": at, "telegraph": tel,
         "notes": "agent K rework sheets (art/kalden_moves.py). Same body placement as kalden.png (anchor x 40), 128px "
                  "wide for reach. 'hit' = union of per-frame 'rects'. points: per-frame anchors (frame coords)."}
    if extra:
        m["points"] = extra
    return m


# =========================================================================== FX
def with_canvas(w, h, fn):
    K.setup(w, h)
    try:
        return fn()
    finally:
        K.setup(W, H)


def fx_tendril():
    """40x72, 8 frames: crack glow, bulge, emerge, lash (3 active), retract. Pivot bottom-centre, curls to the right."""
    w, h = 40, 72
    fl = h - 1
    specs = [(0, 0), (0.08, 0), (0.45, -0.3), (1.0, 1.0), (1.0, -0.5), (0.95, 0.35), (0.5, -0.4), (0.18, -0.2)]
    ms = [70, 60, 50, 50, 70, 90, 80, 80]

    def one(i):
        grow, curl = specs[i]
        Lb, Lf = Layer("Body"), Layer("Body")
        FX = FXLayer("Glow")
        cx = w // 2
        if i == 0 or grow < 0.1:
            for k in range(14):
                x = cx + int((hash01(k, i, 3) - 0.5) * 18)
                FX.put([(x, fl - (1 if k % 3 == 0 else 0))], ("O4", "O3", "V4", "V5")[k % 4])
            if grow > 0:
                K.ID.dome(Lb, (cx, fl), 4.5, 2.8, "V", bias=0)
        else:
            L_ = 60 * grow
            base = (cx, fl + 1)
            c1 = (cx - 2 + curl * 2, fl - L_ * 0.35)
            c2 = (cx + 9 * curl - 2, fl - L_ * 0.72)
            tip = (cx + 15 * curl, fl - L_ * (0.97 if abs(curl) > 0.7 else 1.0))
            pts = bezier(base, c1, c2, tip, n=18)
            if grow > 0.9:   # hooked end
                a = math.atan2(tip[1] - c2[1], tip[0] - c2[0]) + 1.4 * (1 if curl >= 0 else -1)
                pts.append((tip[0] + math.cos(a) * 5, tip[1] + math.sin(a) * 5))
            GK.tube(ID, Lb, pts, 4.2 * (0.6 + 0.4 * grow), 0.6, "V", bias=0)
            for k in range(3):   # thorns
                q = pts[4 + k * 4]
                s = 1 if k % 2 else -1
                GK.tube(ID, Lf, [q, (q[0] + s * 3.2, q[1] - 2.4)], 1.0, 0.4, "V", bias=0)
            vein = K.polyline([ip(q) for q in pts[1:12]])
            Lb.decal([q for j, q in enumerate(vein) if j % 3 != 2], "O3" if i in (3, 4, 5) else "O2")
            GK.pustule(Lb, pts[6], 0.8, hot=i in (3, 4))
            if i in (3, 4, 5):
                FX.put([ip(pts[-1])], "O5")
            for k in range(10):   # the floor splits around it
                x = cx + int((hash01(k, i, 7) - 0.5) * 22)
                FX.put([(x, fl)], ("V4", "O3", "V3")[k % 3])
            if i == 3:
                for k in range(12):
                    a = -math.pi * hash01(k, 1, 9)
                    r = 4 + hash01(k, 2, 9) * 10
                    FX.put([ip((cx + math.cos(a) * r, fl - 2 + math.sin(a) * r))], ("V5", "O4", "V4")[k % 3])
        body = K.render_layer(Lb)
        body.alpha_composite(K.render_layer(Lf))
        return {"ms": ms[i], "cels": {"Body": body, "Glow": FX.image()}}
    return with_canvas(w, h, lambda: [one(i) for i in range(8)])


def fx_pool():
    """56x14, 4 frames loop: a flat rot pool with slow boils (pivot bottom-centre)."""
    w, h = 56, 14

    def one(i):
        body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bp, gp = body.load(), glow.load()
        cx = w / 2
        for x in range(w):
            u = (x + 0.5 - cx) / (w / 2 - 1)
            if abs(u) >= 1:
                continue
            ht = 3.2 * math.sqrt(1 - u * u) + 0.6 * math.sin(x * 0.7 + i * 1.57)
            top = h - 1 - max(1.0, ht)
            for y in range(int(top), h):
                d = y - top
                c = "V5" if d < 0.9 else "V4" if d < 1.8 else ("V3" if (x + y + i) % 5 else "V4")
                if abs(u) > 0.85:
                    c = "V2" if d > 0.9 else "V3"
                bp[x, y] = K.RGBA[c]
            if hash01(x, 0, 21) < 0.08:
                gp[x, int(top) + 1 if int(top) + 1 < h else h - 1] = K.RGBA["O3"]
        for k in range(3):   # boils rising and popping
            x = int(8 + hash01(k, 0, 22) * (w - 16))
            ph = (i + k * 1.3) % 4
            y = h - 3 - int(ph)
            if 0 <= y < h:
                gp[x, y] = K.RGBA["O4" if ph < 2 else "V5"]
                if ph < 1.5:
                    gp[x + 1, y] = K.RGBA["O3"]
        # outline
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        op = out.load()
        for y in range(h):
            for x in range(w):
                if bp[x, y][3]:
                    continue
                if any(0 <= x + a < w and 0 <= y + b < h and bp[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, -1))):
                    op[x, y] = K.RGBA["OUT"]
        out.alpha_composite(body)
        return {"ms": 140, "cels": {"Body": out, "Glow": glow}}
    return [one(i) for i in range(4)]


# =========================================================================== previews
BG = (92, 92, 98, 255)


def preview(tags, flats, path, meta=None, scale=3):
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 12
    sh = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sh)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(230, 230, 230, 255))
        wins = []
        if meta and t in meta["attacks"]:
            wins = meta["attacks"][t]["windows"]
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            if meta:
                dd = ImageDraw.Draw(big)
                x, y, ww, hh = meta["hurtbox"]
                dd.rectangle([x * scale, y * scale, (x + ww) * scale - 1, (y + hh) * scale - 1], outline=(60, 230, 90, 255))
                for w_ in wins:
                    rr = w_["rects"].get(str(i - a))
                    if rr:
                        x, y, ww, hh = rr
                        dd.rectangle([x * scale, y * scale, (x + ww) * scale - 1, (y + hh) * scale - 1], outline=(255, 50, 50, 255), width=2)
                tg = meta["telegraph"].get(t)
                if tg and tg["frame"] == i - a:
                    x, y = tg["at"]
                    dd.ellipse([(x - 3) * scale, (y - 3) * scale, (x + 3) * scale, (y + 3) * scale], outline=(0, 255, 255, 255), width=2)
            sh.alpha_composite(big, ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sh.save(path)


# =========================================================================== main
def main():
    K.setup(W, H)
    GK.W = W   # (gen_kalden's own bbox helpers are not used here)
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    sfx = "_wip" if only else ""
    tb = [t for t in TAGS_B if not only or t[0] in only]
    tc = [t for t in TAGS_C if not only or t[0] in only]
    res = {}
    if tb:
        outb, infb, tagsb = render_set(tb, (1, 2))
        flb = {ph: [K.flatten(im, LAYERS) for _, im in outb[ph]] for ph in (1, 2)}
        mb = None
        if not only:
            at, tel = meta_b(infb)
            mb = base_meta(at, tel)
            json.dump(mb, open(os.path.join(asebuild.ASSETS, "kalden_b_meta.json"), "w"), indent=1)
        preview(tagsb, flb[1], os.path.join(pv, f"kalden_b{sfx}.png"), mb)
        preview(tagsb, flb[2], os.path.join(pv, f"kalden_b_p2{sfx}.png"), mb)
        res["b"] = (outb, tagsb)
    if tc:
        outc, infc, tagsc = render_set(tc, (2,))
        flc = [K.flatten(im, LAYERS) for _, im in outc[2]]
        mc = None
        if not only:
            at, tel, pts = meta_c(infc)
            mc = base_meta(at, tel, pts)
            json.dump(mc, open(os.path.join(asebuild.ASSETS, "kalden_c_meta.json"), "w"), indent=1)
        preview(tagsc, flc, os.path.join(pv, f"kalden_c{sfx}.png"), mc)
        res["c"] = (outc, tagsc)
    tdr, pool = fx_tendril(), fx_pool()
    s = 4
    sh = Image.new("RGBA", (8 * 42 * s, (72 + 2 + 14) * s), (40, 40, 46, 255))
    for i, f in enumerate(tdr):
        fr = Image.new("RGBA", (40, 72), BG)
        fr.alpha_composite(f["cels"]["Body"]); fr.alpha_composite(f["cels"]["Glow"])
        sh.alpha_composite(fr.resize((40 * s, 72 * s), Image.NEAREST), (i * 42 * s, 0))
    for i, f in enumerate(pool):
        fr = Image.new("RGBA", (56, 14), BG)
        fr.alpha_composite(f["cels"]["Body"]); fr.alpha_composite(f["cels"]["Glow"])
        sh.alpha_composite(fr.resize((56 * s, 14 * s), Image.NEAREST), (i * 58 * s, 74 * s))
    sh.save(os.path.join(pv, "fx_kd.png"))
    if BUILD and not only:
        outb, tagsb = res["b"]
        asebuild.build("kalden_b", W, H, LAYERS, [{"ms": ms, "cels": im} for ms, im in outb[1]], tagsb)
        asebuild.build("kalden_b_p2", W, H, LAYERS, [{"ms": ms, "cels": im} for ms, im in outb[2]], tagsb)
        outc, tagsc = res["c"]
        asebuild.build("kalden_c", W, H, LAYERS, [{"ms": ms, "cels": im} for ms, im in outc[2]], tagsc)
        asebuild.build("fx_kd_tendril", 40, 72, ["Body", "Glow"], tdr, [("kd_tendril", 0, 7)])
        asebuild.build("fx_kd_pool", 56, 14, ["Body", "Glow"], pool, [("kd_pool", 0, 3)])
        print("built")


if __name__ == "__main__":
    main()
