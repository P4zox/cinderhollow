#!/usr/bin/env python3
"""Morvain rework -- the expanded move set, hand-keyed on the same rig as art/gen_boss.py.

    python3 art/omen_moves.py                 build omen_a / omen_b (+ _p2) sheets + meta + previews
    python3 art/omen_moves.py --preview       previews only (no Aseprite, no meta)
    python3 art/omen_moves.py --only feint,sweep --preview

The original sheet (assets/boss*.png, tags idle..death) is untouched; these tags live in two extra
sheets with the same 176x128 frame and anchor so the game can swap sheets per move:
    omen_a: feint rising sweep grab impale dash drag
    omen_b: plunge throw counter ward flurry invoke
Outputs: art/omen_{a,b}{,_p2}.aseprite, assets/omen_{a,b}{,_p2}.png/.json, assets/omen_{a,b}_meta.json,
         art/previews/omen_{a,b}_preview.png (+ _p2), art/previews/omen_hitcheck.png
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import gen_boss as gb  # noqa: E402
from gen_boss import P_, GROUND, W, H, add, line, mask_disc, hash01, weapon_point, BLADE  # noqa: E402

WB = dict(wlayer="WeaponBack")
NEUTRAL_F = (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148))


# =========================================================================== extra FX
def fx_handglow(FX, info, j, fi, r, which="far", hot=True):
    """A gathering knot of gold light on an open gauntlet (the grab / ward / recall tells)."""
    hx, hy = j["hand_" + which]
    c = (hx - 2, hy)
    for q in mask_disc(c, r + 3):
        if (q[0] + q[1] + fi) % 3 == 0:
            FX["Glow"].put([q], "Y0")
    for q in mask_disc(c, r + 1):
        FX["Glow"].put([q], "Y1")
    for q in mask_disc(c, r * 0.6 + 0.6):
        FX["Glow"].put([q], "Y2" if hot else "Y1")
    FX["Glow"].put([(int(c[0]), int(c[1]))], "Y3")
    for k in range(6):
        a = math.radians(k * 60 + fi * 23)
        ln = r + 3 + (k % 2) * 3
        FX["FX"].put(line((c[0] + math.cos(a) * (r + 1), c[1] + math.sin(a) * (r + 1)),
                          (c[0] + math.cos(a) * ln, c[1] + math.sin(a) * ln)), "Y2" if k % 2 else "Y1")


def fx_sparks(FX, info, j, fi, n=10, trail=40):
    """Sparks spitting off a blade tip dragged along the stone + the glowing furrow it leaves."""
    if not info["tip"]:
        return
    tx, ty = info["tip"]
    ty = min(ty, GROUND - 1)
    for k in range(n):
        a = math.radians(200 + hash01(k, fi, 7) * 110)
        ln = 3 + hash01(k, fi, 8) * 9
        p0 = (tx + math.cos(a) * 2, ty + math.sin(a) * 2)
        p1 = (tx + math.cos(a) * ln, ty + math.sin(a) * ln)
        FX["FX"].put(line(p0, p1), "Y2" if k % 3 else "Y3")
    for x in range(int(tx), int(min(W - 1, tx + trail))):
        f = (x - tx) / trail
        FX["FXBack"].put([(x, GROUND)], "Y2" if f < 0.3 else "Y1" if f < 0.6 else "Y0")
        if f < 0.4 and (x + fi) % 3 == 0:
            FX["FXBack"].put([(x, GROUND - 1)], "Y0")
    for q in mask_disc((tx, ty), 2.2):
        FX["FX"].put([q], "Y3")


def fx_sigil(FX, info, j, fi, cx, cy, r, stage=0):
    """Shield of light: a vertical disc of runes held in front of the off-hand (seen edge-on-ish)."""
    k = 0.45  # horizontal squash: the disc faces the player
    for y in range(int(cy - r) - 2, int(cy + r) + 3):
        for x in range(int(cx - r * k) - 2, int(cx + r * k) + 3):
            dx, dy = (x + .5 - cx) / k, y + .5 - cy
            d = math.hypot(dx, dy)
            if r - 1.6 <= d <= r:
                FX["FX"].put([(x, y)], "Y3" if (y + fi) % 4 else "Y2")
            elif r - 4.5 <= d < r - 1.6:
                if int(math.degrees(math.atan2(dy, dx)) + fi * 20) % 30 < 12:
                    FX["FX"].put([(x, y)], "Y1")
            elif d < r - 4.5 and (x * 3 + y * 5 + fi) % 7 == 0:
                FX["FX"].put([(x, y)], "Y0")
            if stage and abs(d - (r + 4 + stage * 4)) < 1.2:
                FX["FX"].put([(x, y)], "Y2")
    # cross of light through the centre
    FX["FX"].put(line((cx, cy - r + 3), (cx, cy + r - 3)), "Y2")
    FX["FX"].put(line((cx - r * k + 2, cy), (cx + r * k - 2, cy)), "Y1")
    for q in mask_disc((cx, cy), 2.5):
        FX["FX"].put([q], "Y3")


def fx_bladeglint(FX, info, j, fi, u):
    """A bead of light running up the flat of the blade (the counter-stance shimmer)."""
    g, a, fl = j["grip"], j["wang"], j["wflip"]
    for du, c in ((0, "Y3"), (-2, "Y2"), (-4, "Y1"), (2, "Y2")):
        p = weapon_point(g, a, u + du, 1.0, fl)
        for q in mask_disc(p, 1.6 if du == 0 else 1.0):
            FX["FX"].put([q], c)
    p = weapon_point(g, a, u, 1.0, fl)
    for ang in (0, 90, 180, 270):
        FX["FX"].put(line(p, (p[0] + math.cos(math.radians(ang)) * 5, p[1] + math.sin(math.radians(ang)) * 5)), "Y2")


def fx_burst(FX, info, j, fi, cx, cy, r):
    """Point burst of light (impale / catch)."""
    for k in range(12):
        a = math.radians(k * 30 + fi * 11)
        ln = r if k % 3 == 0 else r * 0.55
        FX["FX"].put(line((cx, cy), (cx + math.cos(a) * ln, cy + math.sin(a) * ln)), "Y3" if k % 3 == 0 else "Y2")
    for q in mask_disc((cx, cy), 3.5):
        FX["FX"].put([q], "Y3")
    ring = [q for q in mask_disc((cx, cy), r * 0.7) if q not in mask_disc((cx, cy), r * 0.7 - 1.3)]
    FX["FX"].put(ring, "Y1")


gb.FX_FUNCS.update(handglow=fx_handglow, sparks=fx_sparks, sigil=fx_sigil, bladeglint=fx_bladeglint, burst=fx_burst)


# =========================================================================== keyframes
LUNGE = dict(P=(94, 93), C=(81, 72), Hd=(71, 54), tw=-1.0, foot_near=(62, 127), foot_far=(122, 127))
RECOVER1 = dict(P=(99, 90), C=(93, 67), Hd=(86, 47), tw=-0.4, foot_near=(70, 127), foot_far=(122, 127))
RECOVER2 = dict(P=(99, 90), C=(95, 67), Hd=(88, 47), tw=-0.3)


def anim_feint():
    """Elden-Ring delayed slash: rises, freezes far too long, twitches, re-cocks -- then drops."""
    held = dict(P=(105, 92), C=(112, 65), Hd=(109, 47), tw=1.4, foot_near=(72, 127), foot_far=(126, 127))
    return [
        (140, P_(P=(101, 87), C=(103, 63), Hd=(98, 43), tw=0.6, grip=(96, 52), wang=300, **WB,
                 foot_near=(78, 127), foot_far=(122, 127))),
        (160, P_(P=(103, 90), C=(108, 63), Hd=(104, 44), tw=1.1, grip=(108, 34), wang=322, **WB,
                 foot_near=(76, 127), foot_far=(124, 127), eyes=1.3)),
        (560, P_(**held, grip=(116, 31), wang=335, **WB, look=-1, eyes=2.0, cape_wind=-1)),
        (110, P_(P=(103, 91), C=(106, 65), Hd=(101, 46), tw=0.9, grip=(106, 34), wang=318, **WB,
                 foot_near=(72, 127), foot_far=(124, 127), eyes=1.6)),
        (160, P_(**held, grip=(114, 32), wang=332, **WB, look=-1, eyes=2.2, cape_wind=-2)),
        (50, P_(**LUNGE, grip=(64, 90), wang=155, cape_wind=3, cape_flare=4,
                smear=dict(frm=((114, 32), 332), mid=(68, 34), start=0.25, inner=14, taper=22))),
        (100, P_(**LUNGE, grip=(66, 94), wang=160, cape_wind=2,
                 smear=dict(frm=((64, 90), 176), start=0.0, inner=26, taper=16))),
        (180, P_(**RECOVER1, grip=(74, 94), wang=156, cape_wind=1)),
        NEUTRAL_F,
    ]


def anim_rising():
    """Rising uppercut out of a crouch that carries him into the air, then an aerial slam."""
    return [
        (130, P_(P=(101, 97), C=(97, 76), Hd=(89, 57), tw=-0.2, look=-1, grip=(96, 94), wang=30, **WB,
                 foot_near=(78, 127), foot_far=(124, 127))),
        (240, P_(P=(102, 100), C=(98, 80), Hd=(90, 61), tw=-0.2, look=-1, grip=(97, 98), wang=28, **WB,
                 foot_near=(76, 127), foot_far=(126, 127), eyes=1.8)),
        (60, P_(P=(98, 82), C=(93, 57), Hd=(87, 36), tw=-0.4, look=1, grip=(74, 52), wang=250,
                foot_near=(88, 124), foot_far=(114, 122), cape_wind=-3, cape_flare=6, tab_wind=-3,
                smear=dict(frm=((97, 98), 28), mid=(62, 100), start=0.25, inner=14, taper=22, hot=1.0))),
        (90, P_(P=(99, 78), C=(96, 53), Hd=(91, 32), tw=-0.1, look=1, grip=(84, 40), wang=268,
                foot_near=(90, 116), foot_far=(112, 114), cape_wind=-4, cape_flare=8,
                smear=dict(frm=((74, 52), 246), inner=28, taper=12))),
        (150, P_(P=(101, 79), C=(104, 55), Hd=(100, 35), tw=0.6, grip=(106, 30), wang=330, **WB,
                 foot_near=(86, 118), foot_far=(118, 117), cape_wind=-3, cape_flare=10, eyes=1.6)),
        (200, P_(P=(100, 80), C=(103, 56), Hd=(99, 36), tw=0.6, grip=(108, 29), wang=345, **WB,
                 foot_near=(86, 119), foot_far=(118, 118), cape_wind=-5, cape_flare=10, eyes=2.0)),
        (60, P_(P=(93, 98), C=(80, 78), Hd=(70, 60), tw=-1.0, grip=(60, 92), wang=118, bury=126, look=-1,
                foot_near=(68, 127), foot_far=(122, 127), cape_wind=4, cape_flare=4,
                smear=dict(frm=((108, 29), 345), mid=(60, 48), start=0.3, inner=14, taper=22),
                fx=[("impact", 38, 0)])),
        (140, P_(P=(93, 97), C=(81, 77), Hd=(71, 59), tw=-1.0, grip=(60, 92), wang=118, bury=126, look=-1,
                 foot_near=(68, 127), foot_far=(122, 127), cape_wind=2, fx=[("impact", 38, 1)])),
        (160, P_(P=(97, 93), C=(89, 72), Hd=(80, 52), tw=-0.5, grip=(72, 88), wang=135,
                 foot_near=(72, 127), foot_far=(121, 127))),
        NEUTRAL_F,
    ]


def anim_sweep():
    """Sweeping low cut at ankle height -- jump it."""
    low = dict(P=(95, 104), C=(84, 86), Hd=(73, 68), tw=-1.1, look=-1, foot_near=(56, 127), foot_far=(126, 127),
               twohand=False, hand_far=(118, 76))
    return [
        (140, P_(P=(102, 99), C=(104, 80), Hd=(97, 61), tw=1.0, grip=(106, 96), wang=25, **WB, look=-1,
                 foot_near=(74, 127), foot_far=(126, 127))),
        (280, P_(P=(103, 101), C=(106, 82), Hd=(99, 63), tw=1.1, grip=(108, 98), wang=22, **WB, look=-1,
                 foot_near=(72, 127), foot_far=(127, 127), eyes=2.0, cape_wind=-1)),
        (50, P_(**low, grip=(68, 112), wang=181, cape_wind=5, cape_flare=8, tab_wind=4,
                fx=[("hsweep", (98, 116), 22, 92, 0.1, -12, 178)])),
        (100, P_(**low, grip=(66, 111), wang=188, cape_wind=3, cape_flare=4,
                 fx=[("hsweep", (98, 116), 26, 90, 0.1, 110, 190, 0.45)])),
        (160, P_(P=(98, 98), C=(90, 78), Hd=(81, 59), tw=-0.6, grip=(74, 100), wang=165, look=-1,
                 foot_near=(64, 127), foot_far=(124, 127), cape_wind=1)),
        (180, P_(**RECOVER2, grip=(77, 92), wang=156)),
        NEUTRAL_F,
    ]


def anim_grab():
    """Unblockable off-hand grab: the far gauntlet gathers light, then lunges for the throat."""
    reach = dict(P=(90, 106), C=(74, 92), Hd=(63, 75), tw=-1.2, foot_near=(52, 127), foot_far=(124, 127),
                 twohand=False, grip=(66, 110), wang=172, look=-1)
    return [
        (150, P_(P=(103, 90), C=(106, 66), Hd=(101, 46), tw=0.8, twohand=False, grip=(84, 88), wang=150,
                 hand_far=(130, 68), foot_near=(78, 127), foot_far=(124, 127), fx=[("handglow", 2, "far")])),
        (320, P_(P=(104, 91), C=(108, 67), Hd=(103, 47), tw=0.9, twohand=False, grip=(85, 89), wang=150,
                 hand_far=(133, 66), foot_near=(76, 127), foot_far=(125, 127), eyes=1.8, look=-1,
                 fx=[("handglow", 4, "far")])),
        (70, P_(**reach, hand_far=(58, 104), cape_wind=4, cape_flare=6, tab_wind=3, eyes=1.6,
                fx=[("handglow", 3, "far"), ("lines", 70, 120, (96, 102, 108))])),
        (130, P_(**reach, hand_far=(57, 105), cape_wind=2, fx=[("handglow", 2, "far", False)])),
        (220, P_(P=(93, 100), C=(80, 83), Hd=(70, 65), tw=-1.0, twohand=False, grip=(70, 104), wang=166,
                 hand_far=(66, 96), foot_near=(56, 127), foot_far=(124, 127), look=-1)),
        (180, P_(**RECOVER2, grip=(77, 92), wang=156)),
        NEUTRAL_F,
    ]


HOLD_HAND = (74, 36)


def anim_impale():
    """Caught: held aloft by the throat, run through upward, flung away."""
    lift = dict(P=(98, 86), C=(90, 62), Hd=(84, 42), tw=-0.8, look=1, twohand=False, hand_far=HOLD_HAND,
                foot_near=(76, 127), foot_far=(120, 127))
    return [
        (220, P_(**lift, grip=(80, 86), wang=150, eyes=1.5)),
        (300, P_(**lift, grip=(84, 90), wang=140, eyes=2.0, cape_wind=-1)),
        (60, P_(**lift, grip=(70, 76), wang=262, eyes=2.2, cape_wind=2,
                smear=dict(frm=((84, 90), 140), mid=(60, 96), start=0.2, inner=16, taper=20, hot=1.0),
                fx=[("burst", 74, 52, 16)])),
        (420, P_(**dict(lift, hand_far=(80, 50)), grip=(71, 74), wang=263, eyes=2.2,
                 fx=[("burst", 74, 50, 10), ("tipflash", 5)])),
        (90, P_(P=(94, 92), C=(83, 70), Hd=(73, 52), tw=-1.0, twohand=False, hand_far=(112, 74),
                grip=(62, 88), wang=175, foot_near=(64, 127), foot_far=(122, 127), cape_wind=4, cape_flare=6,
                smear=dict(frm=((71, 74), 263), mid=(52, 60), start=0.2, inner=14, taper=22))),
        (200, P_(**RECOVER1, grip=(74, 94), wang=156)),
        NEUTRAL_F,
    ]


def anim_dash():
    """Golden dash-through: iaido crouch, a blur past the player, the cut completes behind them."""
    return [
        (140, P_(P=(102, 94), C=(104, 72), Hd=(97, 53), tw=1.0, twohand=False, grip=(104, 90), wang=350, **WB,
                 hand_far=(124, 84), look=-1, foot_near=(74, 127), foot_far=(126, 127))),
        (300, P_(P=(103, 96), C=(106, 75), Hd=(99, 56), tw=1.1, twohand=False, grip=(106, 92), wang=352, **WB,
                 hand_far=(122, 90), look=-1, foot_near=(72, 127), foot_far=(127, 127), eyes=2.2, cape_wind=-2)),
        (50, P_(P=(92, 96), C=(78, 78), Hd=(66, 62), tw=-1.2, twohand=False, grip=(88, 90), wang=5, **WB,
                hand_far=(96, 96), look=-1, foot_near=(60, 124), foot_far=(128, 120), cape_wind=8, cape_flare=14,
                tab_wind=6, fx=[("lines", 104, 172, (58, 66, 74, 84, 94, 104, 112))])),
        (60, P_(P=(94, 95), C=(82, 76), Hd=(72, 58), tw=-1.1, twohand=False, grip=(62, 86), wang=176,
                hand_far=(112, 80), foot_near=(58, 127), foot_far=(126, 127), cape_wind=6, cape_flare=10,
                smear=dict(frm=((88, 90), 365), mid=(82, 44), start=0.2, inner=14, taper=22, hot=1.0))),
        (90, P_(P=(95, 95), C=(84, 75), Hd=(74, 57), tw=-1.0, twohand=False, grip=(60, 90), wang=170,
                hand_far=(112, 82), foot_near=(60, 127), foot_far=(125, 127), cape_wind=4,
                smear=dict(frm=((62, 86), 200), inner=28, taper=12))),
        (180, P_(**RECOVER1, grip=(74, 94), wang=156, cape_wind=1)),
        NEUTRAL_F,
    ]


def anim_drag():
    """Blade dragged behind him through the stone (walk loop 1-4), flicked up into a rising cut."""
    fr = [(150, P_(P=(101, 93), C=(99, 70), Hd=(92, 50), tw=-0.3, twohand=False, grip=(98, 92), wang=34,
                   look=-1, foot_near=(80, 127), foot_far=(120, 127), fx=[("sparks", 6, 20)]))]
    for i in range(4):
        ph = 2 * math.pi * i / 4
        c, s = math.cos(ph), math.sin(ph)
        nf = (82 - 12 * c, GROUND - max(0.0, -s) * 6)
        ff = (114 + 12 * c, GROUND - max(0.0, s) * 6)
        bob = 2.0 * abs(c)
        fr.append((120, P_(P=(100, 93 + bob), C=(97 - c * 1.5, 70 + bob), Hd=(90 - c * 1.5, 50 + bob),
                           tw=-0.3 + 0.35 * c, look=-1, foot_near=nf, foot_far=ff, twohand=False,
                           grip=(98 - c * 2, 92 + bob * 0.5), wang=34 - c * 2, cape_wind=2.5,
                           fx=[("sparks", 12, 46)])))
    fr += [
        (70, P_(P=(96, 84), C=(90, 58), Hd=(84, 37), tw=-0.4, look=1, grip=(78, 50), wang=250,
                foot_near=(70, 127), foot_far=(120, 127), cape_wind=-3, cape_flare=6,
                smear=dict(frm=((98, 92), 34), mid=(58, 104), start=0.25, inner=14, taper=22, hot=1.0))),
        (220, P_(P=(97, 84), C=(92, 58), Hd=(86, 37), tw=-0.2, look=1, grip=(82, 46), wang=262, eyes=2.0,
                 foot_near=(72, 127), foot_far=(120, 127), fx=[("tipflash", 6)])),
        (180, P_(**RECOVER2, grip=(78, 80), wang=190)),
        NEUTRAL_F,
    ]
    return fr


def anim_plunge():
    """Leaps high, turns the blade point-down and drives it into the floor (shockwaves)."""
    apex = dict(P=(100, 78), C=(99, 53), Hd=(95, 32), tw=-0.2, foot_near=(90, 112), foot_far=(114, 110),
                grip=(80, 46), wang=95)
    return [
        (150, P_(P=(101, 98), C=(95, 77), Hd=(87, 58), grip=(88, 96), wang=160, look=-1,
                 foot_near=(78, 127), foot_far=(122, 127))),
        (200, P_(P=(101, 101), C=(96, 81), Hd=(88, 62), grip=(90, 98), wang=165, look=-1,
                 foot_near=(76, 127), foot_far=(124, 127), eyes=1.5)),
        (120, P_(P=(100, 76), C=(99, 51), Hd=(95, 30), look=1, grip=(92, 50), wang=272,
                 foot_near=(92, 116), foot_far=(112, 112), cape_wind=-4, cape_flare=8)),
        (140, P_(**apex, cape_wind=-2, cape_flare=10)),
        (260, P_(**dict(apex, P=(100, 76), C=(99, 51), Hd=(95, 30), grip=(80, 44)), cape_wind=-3,
                 cape_flare=12, eyes=2.2, fx=[("tipflash", 5)])),
        (50, P_(P=(97, 100), C=(88, 80), Hd=(79, 62), tw=-0.6, look=-1, grip=(74, 86), wang=92, bury=126,
                foot_near=(72, 127), foot_far=(122, 127), cape_wind=4, cape_flare=6,
                fx=[("impact", 76, 0), ("lines", 64, 84, (40, 50, 60))])),
        (160, P_(P=(97, 99), C=(88, 79), Hd=(79, 61), tw=-0.6, look=-1, grip=(74, 86), wang=92, bury=126,
                 foot_near=(72, 127), foot_far=(122, 127), cape_wind=2,
                 fx=[("impact", 76, 1), ("cracks", 76, 50, 0.8)])),
        (180, P_(P=(99, 92), C=(93, 70), Hd=(86, 50), tw=-0.3, grip=(78, 80), wang=110,
                 foot_near=(74, 127), foot_far=(121, 127))),
        NEUTRAL_F,
    ]


def anim_throw():
    """Hurls the greatsword (it boomerangs back); unarmed, he calls it home and catches it."""
    unarmed = dict(P=(100, 86), C=(99, 62), Hd=(94, 42), weapon=False, hand_far=(118, 84))
    return [
        (150, P_(P=(103, 88), C=(107, 64), Hd=(102, 44), tw=1.0, twohand=False, grip=(116, 44), wang=320,
                 **WB, hand_far=(100, 70), foot_near=(76, 127), foot_far=(124, 127))),
        (280, P_(P=(104, 89), C=(109, 65), Hd=(104, 45), tw=1.2, twohand=False, grip=(120, 40), wang=330,
                 **WB, hand_far=(100, 72), foot_near=(74, 127), foot_far=(126, 127), eyes=1.8, look=-1)),
        (60, P_(P=(96, 90), C=(86, 68), Hd=(76, 50), tw=-1.0, twohand=False, grip=(58, 60), wang=190,
                hand_far=(112, 76), foot_near=(62, 127), foot_far=(122, 127), cape_wind=4, cape_flare=6,
                smear=dict(frm=((120, 40), 330), mid=(84, 20), start=0.25, inner=14, taper=22))),
        (120, P_(P=(96, 90), C=(86, 68), Hd=(76, 50), tw=-1.0, weapon=False, hand_near=(54, 62),
                 hand_far=(112, 78), foot_near=(62, 127), foot_far=(122, 127), cape_wind=2)),
        (420, P_(**unarmed, hand_near=(70, 58), look=1, fx=[("handglow", 2, "near")])),
        (160, P_(**unarmed, hand_near=(66, 46), look=1, eyes=1.5, fx=[("handglow", 3, "near")])),
        (160, P_(**unarmed, hand_near=(66, 45), look=1, eyes=1.5, fx=[("handglow", 4, "near")])),
        (80, P_(P=(101, 87), C=(100, 63), Hd=(95, 43), grip=(66, 46), wang=250, twohand=False, hand_far=(118, 84),
                look=1, fx=[("tipflash", 6), ("burst", 64, 46, 10)])),
        (180, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(76, 74), wang=200)),
        NEUTRAL_F,
    ]


def anim_counter():
    """Counter stance: blade held upright, palm on the flat; any blow is answered by a sweeping cut."""
    st = dict(P=(101, 88), C=(100, 64), Hd=(95, 44), tw=-0.2, twohand=False, grip=(80, 74), wang=275,
              hand_far=(86, 54), foot_near=(72, 127), foot_far=(124, 127))
    return [
        (140, P_(P=(101, 87), C=(100, 63), Hd=(95, 43), tw=-0.2, twohand=False, grip=(80, 78), wang=250,
                 hand_far=(96, 62), foot_near=(76, 127), foot_far=(122, 127))),
        (200, P_(**st, eyes=1.6, fx=[("bladeglint", 16)])),
        (200, P_(**st, eyes=1.8, fx=[("bladeglint", 32)])),
        (200, P_(**st, eyes=1.6, fx=[("bladeglint", 48)])),
        (50, P_(P=(95, 97), C=(83, 75), Hd=(73, 56), tw=-1.2, grip=(64, 102), wang=181,
                foot_near=(62, 127), foot_far=(125, 127), cape_wind=4, cape_flare=6, tab_wind=4, eyes=2.2,
                fx=[("hsweep", (96, 106), 22, 92, 0.2, -40, 178)])),
        (90, P_(P=(96, 96), C=(86, 74), Hd=(76, 55), tw=-1.0, grip=(66, 104), wang=170,
                foot_near=(63, 127), foot_far=(124, 127), cape_wind=3,
                fx=[("hsweep", (96, 106), 26, 90, 0.2, 110, 190, 0.45)])),
        (180, P_(**RECOVER1, grip=(74, 94), wang=156, cape_wind=1)),
        NEUTRAL_F,
    ]


SIGIL = (54, 66, 26)


def anim_ward():
    """Shield of light: a rune disc raised in front on the off-hand; it soaks blows, then bursts."""
    st = dict(P=(101, 88), C=(94, 64), Hd=(88, 44), tw=-0.6, twohand=False, grip=(84, 90), wang=140,
              hand_far=(74, 58), foot_near=(72, 127), foot_far=(122, 127))
    return [
        (150, P_(P=(101, 87), C=(97, 63), Hd=(91, 43), tw=-0.4, twohand=False, grip=(82, 88), wang=145,
                 hand_far=(90, 66), foot_near=(76, 127), foot_far=(122, 127), fx=[("handglow", 3, "far")])),
        (200, P_(**st, eyes=1.5, fx=[("sigil", SIGIL[0], SIGIL[1], SIGIL[2] * 0.7), ("handglow", 2, "far")])),
        (200, P_(**st, eyes=1.6, fx=[("sigil", *SIGIL), ("handglow", 2, "far")])),
        (200, P_(**st, eyes=1.6, fx=[("sigil", *SIGIL), ("handglow", 2, "far")])),
        (80, P_(**dict(st, hand_far=(70, 56)), eyes=2.2, fx=[("sigil", SIGIL[0], SIGIL[1], SIGIL[2], 1),
                                                                ("burst", SIGIL[0], SIGIL[1], 24)])),
        (180, P_(**RECOVER2, grip=(77, 92), wang=156)),
        NEUTRAL_F,
    ]


def anim_flurry():
    """Crescent flurry: five fast alternating cuts stepping forward, then a great crescent finisher."""
    return [
        (120, P_(P=(101, 87), C=(103, 63), Hd=(98, 43), tw=0.7, grip=(98, 50), wang=316, **WB,
                 foot_near=(78, 127), foot_far=(122, 127))),
        (200, P_(P=(102, 88), C=(106, 63), Hd=(101, 43), tw=0.9, grip=(106, 40), wang=325, **WB,
                 foot_near=(76, 127), foot_far=(124, 127), eyes=1.4)),
        (50, P_(P=(95, 91), C=(83, 70), Hd=(73, 52), tw=-0.9, grip=(66, 88), wang=150,
                foot_near=(66, 127), foot_far=(122, 127), cape_wind=2,
                smear=dict(frm=((106, 40), 325), mid=(74, 38), start=0.3, inner=14, taper=22))),
        (70, P_(P=(96, 86), C=(88, 62), Hd=(80, 42), tw=-0.4, look=1, grip=(74, 56), wang=240,
                foot_near=(68, 127), foot_far=(120, 127), cape_wind=-2,
                smear=dict(frm=((66, 88), 150), mid=(54, 86), start=0.1, inner=14, taper=22))),
        (50, P_(P=(94, 92), C=(81, 71), Hd=(71, 53), tw=-1.0, grip=(64, 90), wang=152,
                foot_near=(64, 127), foot_far=(122, 127), cape_wind=3,
                smear=dict(frm=((74, 56), 240), mid=(52, 58), start=0.1, inner=14, taper=22))),
        (70, P_(P=(96, 86), C=(88, 62), Hd=(80, 42), tw=-0.4, look=1, grip=(72, 54), wang=245,
                foot_near=(66, 127), foot_far=(120, 127), cape_wind=-2,
                smear=dict(frm=((64, 90), 152), mid=(52, 88), start=0.1, inner=14, taper=22))),
        (50, P_(P=(97, 92), C=(88, 70), Hd=(78, 52), tw=-0.8, grip=(66, 84), wang=182,
                foot_near=(64, 127), foot_far=(124, 127), cape_wind=4, cape_flare=4,
                fx=[("hsweep", (96, 96), 22, 88, 0.22, -60, 178)])),
        (110, P_(P=(97, 92), C=(88, 70), Hd=(78, 52), tw=-0.8, grip=(68, 88), wang=175,
                 foot_near=(64, 127), foot_far=(124, 127), cape_wind=2,
                 fx=[("hsweep", (96, 96), 26, 86, 0.22, 110, 190, 0.45)])),
        (300, P_(P=(104, 90), C=(110, 64), Hd=(106, 46), tw=1.3, grip=(114, 32), wang=330, **WB, look=-1,
                 foot_near=(72, 127), foot_far=(126, 127), eyes=2.2, cape_wind=-2)),
        (50, P_(P=(93, 96), C=(80, 76), Hd=(70, 58), tw=-1.1, grip=(60, 94), wang=135,
                foot_near=(60, 127), foot_far=(124, 127), cape_wind=5, cape_flare=8, tab_wind=4,
                smear=dict(frm=((114, 32), 330), mid=(62, 28), start=0.2, inner=10, taper=26, hot=1.0),
                fx=[("tipflash", 8)])),
        (160, P_(P=(93, 96), C=(80, 76), Hd=(70, 58), tw=-1.1, grip=(62, 96), wang=132,
                 foot_near=(60, 127), foot_far=(124, 127), cape_wind=3,
                 smear=dict(frm=((60, 94), 150), inner=28, taper=10))),
        (180, P_(**RECOVER1, grip=(74, 94), wang=156, cape_wind=1)),
        NEUTRAL_F,
    ]


def anim_invoke():
    """Blade raised to the sky: light gathers at the point and the heavens answer (spear rain / eclipse)."""
    up = dict(P=(100, 86), C=(99, 61), Hd=(95, 40), tw=0.1, look=1, grip=(90, 52), wang=225)
    return [
        (150, P_(P=(100, 86), C=(98, 62), Hd=(93, 41), grip=(84, 70), wang=205)),
        (200, P_(**up, fx=[("orb", 3, 6)])),
        (250, P_(**up, eyes=1.8, fx=[("orb", 5, 8)])),
        (250, P_(**up, eyes=2.2, fx=[("orb", 7, 10)])),
        (80, P_(**up, eyes=2.2, fx=[("flash",)])),
        (300, P_(**up, eyes=1.5, fx=[("orb", 2, 4)])),
        (180, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 76), wang=190)),
        NEUTRAL_F,
    ]


SHEETS = {
    "omen_a": [("feint", anim_feint), ("rising", anim_rising), ("sweep", anim_sweep), ("grab", anim_grab),
               ("impale", anim_impale), ("dash", anim_dash), ("drag", anim_drag)],
    "omen_b": [("plunge", anim_plunge), ("throw", anim_throw), ("counter", anim_counter), ("ward", anim_ward),
               ("flurry", anim_flurry), ("invoke", anim_invoke)],
}
# active (hitting) frames per tag; the rects come from blade+smear bboxes unless listed in MANUAL
ACTIVE = {"feint": [5, 6], "rising": [2, 3, 6], "sweep": [2, 3], "grab": [2, 3], "impale": [], "dash": [2, 3],
          "drag": [5], "plunge": [5], "throw": [2], "counter": [4, 5], "ward": [], "flurry": [2, 3, 4, 5, 6, 9],
          "invoke": []}
GLINT = {"feint": [1], "rising": [1, 5], "sweep": [1], "dash": [1], "drag": [0], "plunge": [4], "throw": [1],
         "flurry": [1, 8], "counter": [1]}


# =========================================================================== reach check (keeps the rig honest)
def check_reach(name, fr):
    for k, (ms, p) in enumerate(fr):
        j = gb.joints(p)
        for side, sh in (("near", j["Ns"]), ("far", j["Fs"])):
            h = j["hand_" + side]
            d = math.hypot(h[0] - sh[0], h[1] - sh[1])
            if d > 42:
                print(f"  reach! {name} f{k} {side} {d:.1f}")


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    base_meta = json.load(open(os.path.join(asebuild.ASSETS, "boss_meta.json")))
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    hitcols = []
    for sname, tagdefs in SHEETS.items():
        frames, frames_p2, flats, flats_p2, tags, infos, poses = [], [], [], [], [], {}, {}
        for name, fn in tagdefs:
            if only and name not in only:
                continue
            fr = fn()
            check_reach(name, fr)
            sec = gb.secondary(fr, loop=False)
            a = len(frames)
            infos[name] = []
            poses[name] = [p for _, p in fr]
            for k, (ms, p) in enumerate(fr):
                L, FX, info = gb.render(p, a + k, sec[k])
                imgs = gb.compose(L, FX, info)
                p2 = gb.p2_layers(info, a + k, 1.0, imgs)
                frames.append({"ms": ms, "cels": imgs})
                frames_p2.append({"ms": ms, "cels": {**imgs, **p2}})
                flats.append(gb.flatten(imgs, gb.BASE_LAYERS))
                flats_p2.append(gb.flatten({**imgs, **p2}, gb.P2_ORDER))
                infos[name].append(info)
            tags.append((name, a, len(frames) - 1))
            print("rendered", sname, name, len(fr))
        if not frames:
            continue
        gb.preview(flats, os.path.join(ART, "previews", f"{sname}_preview.png"))
        gb.preview(flats_p2, os.path.join(ART, "previews", f"{sname}_p2_preview.png"))
        if only:
            continue
        meta = {"frame": [W, H], "anchor": base_meta["anchor"], "hurtbox": base_meta["hurtbox"], "native": -1,
                "attacks": {}, "telegraph": {}, "points": {}}
        for name, _ in tagdefs:
            inf = infos[name]
            rects = {}
            for k in ACTIVE[name]:
                pts = inf[k]["blade"] | inf[k]["smear"]
                if name == "grab":
                    hx, hy = inf[k]["j"]["hand_far"]
                    pts = {(int(hx + dx), int(hy + dy)) for dx in range(-12, 9) for dy in range(-12, 14)}
                if name == "dash" and k == 2:   # the blur itself hurts: body + trailing blade
                    pts |= {(x, y) for x in range(58, 120) for y in range(60, 127)}
                rects[str(k)] = gb.bbox(pts, pad=1) if pts else [0, 0, 1, 1]
            meta["attacks"][name] = {"active": ACTIVE[name], "rects": rects}
            tg = {}
            for k in GLINT.get(name, []):
                j = inf[k]["j"]
                if j["weapon"]:
                    q = weapon_point(j["grip"], j["wang"], BLADE["end"] - 8, 1.5, j["wflip"])
                    tg[str(k)] = [int(round(q[0])), int(round(q[1]))]
            if name == "grab":
                for k in (0, 1):
                    h = inf[k]["j"]["hand_far"]; tg[str(k)] = [int(h[0]), int(h[1])]
            if tg:
                meta["telegraph"][name] = tg
            meta["points"][name] = {
                "tip": [[int(round(v)) for v in i["tip"]] if i["tip"] else None for i in inf],
                "hand": [[int(round(v)) for v in i["j"]["hand_far"]] for i in inf],
                "handn": [[int(round(v)) for v in i["j"]["hand_near"]] for i in inf],
                "grip": [[int(round(v)) for v in i["j"]["grip"]] for i in inf],
            }
            for k in ACTIVE[name]:
                hitcols.append((name, k, frames[tags[[t[0] for t in tags].index(name)][1] + k]["cels"],
                                meta["attacks"][name]["rects"][str(k)]))
        meta["sigil"] = list(SIGIL)
        with open(os.path.join(asebuild.ASSETS, f"{sname}_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
        if "--preview" not in sys.argv:
            asebuild.build(sname, W, H, gb.BASE_LAYERS, frames, tags)
            asebuild.build(sname + "_p2", W, H, gb.P2_ORDER, frames_p2, tags)
    if hitcols:
        s = 2
        sheet = Image.new("RGBA", (8 * (W + 2) * s, ((len(hitcols) + 7) // 8) * (H + 14) * s), (14, 13, 22, 255))
        for i, (t, k, cels, r) in enumerate(hitcols):
            fr = Image.new("RGBA", (W, H), (28, 26, 44, 255))
            fr.alpha_composite(gb.flatten(cels, gb.BASE_LAYERS))
            d = ImageDraw.Draw(fr)
            px, py, pw, ph = gb.PLAYER_BOX
            d.rectangle([px, py, px + pw - 1, py + ph - 1], outline=(80, 200, 255, 255))
            d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 60, 60, 255))
            col = Image.new("RGBA", (W, H + 14), (14, 13, 22, 255))
            ImageDraw.Draw(col).text((2, 1), f"{t} f{k}", fill=(200, 255, 200, 255))
            col.paste(fr, (0, 14))
            sheet.alpha_composite(col.resize((W * s, (H + 14) * s), Image.NEAREST),
                                  ((i % 8) * (W + 2) * s, (i // 8) * (H + 14) * s))
        sheet.save(os.path.join(ART, "previews", "omen_hitcheck.png"))


if __name__ == "__main__":
    main()
