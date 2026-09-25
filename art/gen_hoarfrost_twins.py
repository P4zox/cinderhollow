#!/usr/bin/env python3
"""Boss generator -- THE FROSTBOUND TWINS (Hoarfrost Aqueduct main boss), built from the approved concept
art/concepts/twins.png (drawing code reused from art/concepts/gen_twins.py).

    python3 art/gen_hoarfrost_twins.py               full build (Aseprite) + meta + previews
    python3 art/gen_hoarfrost_twins.py --preview     previews + meta only
    python3 art/gen_hoarfrost_twins.py --only hael:slash,idle --preview

Outputs
    twins_hael / twins_hael_p2   96x72, Ser Hael (flame; p2 = enraged survivor wreathed in his sister's frost)
    twins_rime / twins_rime_p2   96x72, Dame Rime (frost; p2 = enraged survivor burning with her brother's fire)
    assets/twins_hael_meta.json, assets/twins_rime_meta.json  (shared by the p2 sheets)
    fx_hf_flamewave 32x24 (4 loop, pivot bottom)  fx_hf_lance 24x10 (4 loop)  fx_hf_firebolt 16x16 (4 loop)
    fx_hf_clash 48x48 (6)  fx_hf_nova 128x72 (8, pivot bottom)  fx_hf_pillar 24x72 (8, pivot bottom)
    art/previews/twins_hael*.png, twins_rime*.png (rows per tag), *_hitbox.png, twins_closeup.png, fx_hf_twins.png
Faces RIGHT, feet on row 71, anchor x = 40 (as in the concept).
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
sys.path.insert(0, os.path.join(ART, "concepts"))
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
import gen_twins as T  # noqa: E402   (approved concept: palettes, draw_hael, draw_rime, helpers)
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, hash01, swept, thrust_lines, dirv,  # noqa: E402
                       blade_px, blade_line, flame, mask_disc)

W, H = 96, 72
K.setup(W, H)
FLOOR = H - 1
AX = 40
BUILD = "--preview" not in sys.argv
RGBA = K.RGBA
K.SMEAR.update({
    "flame": ["Y3", "O4", "O3", "O1"],
    "flame2": ["U4", "U3", "O3", "O1"],       # enraged Hael: frost licks through the fire
    "frost": ["U4", "U2", "U1", "U0"],
    "frost2": ["Y3", "O4", "O2", "O1"],       # enraged Rime: fire in the frost
})
MR = T.MRig()
BODYL = ["FXBack", "Body", "FX"]


def star(FX, c, core, arm_):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], core)
    for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0), (0, -3)):
        FX.put([(x + d[0], y + d[1])], arm_)


def shoulder(p, back=True):
    P, C = p["P"], p["C"]
    upv = sub(C, P)
    ln = math.hypot(*upv)
    F = K.basis(P, upv)
    return F(-3.4, -ln + 3.0) if back else F(1.8, -ln + 2.6)


# =========================================================================== pose helpers
def HP(*bases, **kw):
    d = dict(T.HAEL0)
    d.update(dict(sm=None, glint=None, dust=0, impact=0, dissolve=0.0, wave=0, burn=0, kneel=False, shake=0, plant=0))
    for b in bases:
        d.update(b)
    d.update(kw)
    if "sh" not in kw and not any("sh" in b for b in bases) and d.get("sh") is not None:
        hx, hy = d["hsh"]
        d["sh"] = dict(c=(hx - 1.5, hy - 0.5), rx=6.4, ry=8.6, tilt=(0.25, 0.0))
    return d


def RP(*bases, **kw):
    d = dict(T.RIME0)
    d.update(dict(sm=None, glint=None, dust=0, impact=0, dissolve=0.0, burn=0, shake=0, cast=0, plant=0))
    for b in bases:
        d.update(b)
    d.update(kw)
    if "sh" not in kw and not any("sh" in b for b in bases) and d.get("sh") is not None:
        hx, hy = d["hsh"]
        d["sh"] = dict(c=(hx + 1.5, hy + 5.0), w=6.0, h=19.0, ang=-10.0, face=0.25)
    return d


def bob(p, dy, dx=0.0, keys=("P", "C", "Hd", "hs", "hsh")):
    q = dict(p)
    for k in keys:
        if q.get(k) is not None:
            q[k] = (q[k][0] + dx, q[k][1] + dy)
    if q.get("sh") and "c" in q["sh"]:
        s = dict(q["sh"]); s["c"] = (s["c"][0] + dx, s["c"][1] + dy); q["sh"] = s
    return q


def up(p, dy, dx=0.0):
    """airborne frames: shift the whole body incl. feet"""
    q = bob(p, -dy, dx, keys=("P", "C", "Hd", "hs", "hsh", "fb", "ff", "kb", "kf"))
    return q


# =========================================================================== SER HAEL  (flame, round shield)
HS = dict(P=(39.0, 47.0), C=(40.6, 34.4), Hd=(42.4, 22.8))


def h_idle():
    fr = []
    for i in range(6):
        b = (0, 0.4, 0.9, 1.2, 0.9, 0.4)[i]
        fr.append((170, HP(P=(39.0, 47.0 + b * 0.35), C=(40.6, 34.4 + b), Hd=(42.4, 22.8 + b * 1.05),
                           hs=(52.0, 45.0 + b * 0.8), hsh=(45.0, 47.5 + b * 0.7), wang=-52 + b, sway=0.6 * math.sin(i * 1.05))))
    return fr


def h_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (41.5 + 8.4 * c, 71 - max(0.0, -s) * 3.8)
        fb = (38.5 - 8.4 * c, 71 - max(0.0, s) * 3.8)
        bb = 1.4 * abs(c)
        fr.append((120, HP(P=(39.6, 47.4 + bb), C=(41.6, 35.0 + bb), Hd=(43.6, 23.6 + bb), ff=ff, fb=fb,
                           hs=(52.6 + 1.2 * c, 45.6 + bb), hsh=(46.0 - 0.8 * c, 47.6 + bb), wang=-50 + 3 * c,
                           sway=1.2 * s)))
    return fr


def h_slash():
    WB = dict(wl="WeaponBack", armup=True)
    rise = dict(P=(38.4, 48.0), C=(37.8, 35.6), Hd=(38.6, 24.2), hup=(-0.15, -1), fb=(29.0, 71), ff=(48.0, 71))
    lunge = dict(P=(45.0, 50.0), C=(49.4, 38.6), Hd=(52.8, 27.8), hup=(0.42, -1), fb=(29.5, 71), ff=(58.5, 71))
    low = dict(P=(41.0, 50.0), C=(40.6, 37.8), Hd=(41.6, 26.4), hup=(-0.05, -1), fb=(29.5, 71), ff=(53.0, 71))
    rise2 = dict(P=(45.0, 48.6), C=(48.4, 36.4), Hd=(51.0, 25.4), hup=(0.3, -1), fb=(31.5, 71), ff=(57.0, 71))
    return [
        (120, HP(rise, hs=(45.0, 30.0), wang=-100, hsh=(48.0, 45.0), **WB)),
        (150, HP(rise, hs=(40.0, 24.0), wang=-148, hsh=(49.0, 44.0), eye=2, **WB)),
        (260, HP(bob(rise, 0.6), hs=(39.4, 24.4), wang=-152, hsh=(49.0, 44.6), eye=2, glint="tip", flames=1.3, **WB)),
        (60, HP(lunge, hs=(59.0, 41.0), wang=-4, hsh=(44.0, 49.0), sway=3, flames=1.2,
                sm=dict(g0=(39.4, 24.4), a0=-152, mid=(50.0, 21.0), start=0.1))),
        (100, HP(lunge, hs=(57.0, 53.0), wang=44, hsh=(44.0, 49.0), sway=2,
                 sm=dict(g0=(59.0, 41.0), a0=-4, taper=0.45, u0=16))),
        (120, HP(low, hs=(42.0, 57.0), wang=164, hsh=(49.0, 46.0), wl="WeaponBack")),
        (190, HP(bob(low, 0.5), hs=(41.0, 58.0), wang=168, hsh=(49.0, 46.4), eye=2, wl="WeaponBack", glint="tip")),
        (60, HP(rise2, hs=(60.0, 40.0), wang=-34, hsh=(44.0, 48.0), sway=3, flames=1.2,
                sm=dict(g0=(41.0, 58.0), a0=168, mid=(52.0, 64.0), start=0.08))),
        (100, HP(rise2, hs=(56.0, 29.0), wang=-84, hsh=(44.0, 48.0), sway=2, armup=True,
                 sm=dict(g0=(60.0, 40.0), a0=-34, taper=0.25, u0=22, start=0.3))),
        (150, HP(P=(42.0, 48.0), C=(43.4, 35.4), Hd=(45.0, 24.0), hup=(0.2, -1), fb=(30.5, 71), ff=(53.5, 71),
                 hs=(53.0, 33.0), wang=-72, hsh=(46.0, 48.0))),
        (160, HP(P=(40.4, 47.4), C=(41.8, 34.8), Hd=(43.4, 23.2), fb=(30.0, 71), ff=(51.5, 71), hs=(52.6, 40.0),
                 wang=-60)),
        (160, HP()),
    ]


SLAM = dict(P=(44.0, 51.0), C=(49.2, 40.4), Hd=(53.6, 30.4), hup=(0.5, -1), fb=(27.5, 71), ff=(60.0, 71),
            hs=(60.0, 52.5), wang=38, hsh=(40.0, 46.0), sh=dict(c=(38.5, 45.5), rx=5.6, ry=8.4, tilt=(-0.1, 0.1)))


def h_slam():
    AU = dict(wl="WeaponBack", armup=True)
    crouch = dict(P=(38.6, 50.0), C=(40.4, 37.8), Hd=(42.4, 26.4), hup=(0.15, -1), fb=(29.0, 71), ff=(49.5, 71))
    high = dict(P=(38.2, 46.4), C=(37.4, 33.6), Hd=(37.6, 22.2), hup=(-0.25, -1), fb=(28.5, 71), ff=(50.0, 71))
    return [
        (120, HP(crouch, hs=(48.0, 42.0), wang=-70, hsh=(46.0, 47.0), dust=2)),
        (140, HP(high, hs=(42.0, 20.0), wang=-110, hsh=(47.0, 42.0), **AU)),
        (170, HP(bob(high, -1.0, -0.4), hs=(38.0, 16.0), wang=-132, hsh=(47.0, 41.0), eye=2, flames=1.4, **AU)),
        (300, HP(bob(high, -1.4, -0.8), hs=(36.6, 15.0), wang=-140, hsh=(47.0, 40.6), eye=2, flames=1.7,
                 glint="tip", **AU)),
        (60, HP(P=(42.0, 49.0), C=(45.0, 37.4), Hd=(48.0, 26.6), hup=(0.35, -1), fb=(28.0, 71), ff=(57.0, 71),
                hs=(56.0, 28.0), wang=-58, hsh=(42.0, 46.0), eye=2, flames=1.5, armup=True,
                sm=dict(g0=(36.6, 15.0), a0=-140, mid=(46.0, 12.0), start=0.4, taper=0.85, u0=18))),
        (70, HP(SLAM, eye=2, slam=True, sway=3.0, cape=1.15, flames=1.2, impact=1)),
        (130, HP(SLAM, eye=2, sway=2.0, cape=1.1, flames=1.0, impact=2, shake=1)),
        (170, HP(bob(SLAM, 0.6), eye=1, sway=1.0, flames=0.8, impact=3)),
        (170, HP(bob(SLAM, 0.8), eye=1, flames=0.7, impact=4)),
        (150, HP(P=(42.0, 50.0), C=(45.6, 38.4), Hd=(48.8, 27.6), hup=(0.35, -1), fb=(28.0, 71), ff=(57.0, 71),
                 hs=(57.0, 46.0), wang=-10, hsh=(42.0, 46.0))),
        (150, HP(P=(40.4, 48.0), C=(42.4, 35.6), Hd=(44.4, 24.0), hup=(0.18, -1), fb=(29.5, 71), ff=(53.0, 71),
                 hs=(54.0, 42.0), wang=-40)),
        (150, HP()),
    ]


BLOCKH = dict(P=(37.6, 48.6), C=(40.0, 36.8), Hd=(42.6, 25.8), hup=(0.3, -1), fb=(27.0, 71), ff=(50.0, 71),
              hs=(45.0, 45.5), wang=-34, wl="WeaponBack", hsh=(51.0, 38.5),
              sh=dict(c=(52.0, 37.0), rx=4.4, ry=9.6, tilt=(0.55, -0.05)), eye=2, flames=0.8, sway=-1.0)


def h_bash():
    rush = dict(P=(46.0, 51.0), C=(51.6, 41.4), Hd=(56.0, 31.6), hup=(0.6, -1), fb=(29.0, 71), ff=(61.0, 71),
                hs=(46.0, 50.0), wang=-20, wl="WeaponBack", hsh=(62.0, 40.0),
                sh=dict(c=(63.5, 39.0), rx=4.2, ry=9.8, tilt=(0.6, -0.05)), eye=2)
    return [
        (120, HP(BLOCKH)),
        (170, HP(bob(BLOCKH, 1.6, -1.0), glint=(56.0, 30.0), dust=2)),
        (160, HP(bob(BLOCKH, 2.0, -1.4))),
        (70, HP(rush, dust=1, sway=4, flames=1.1)),
        (70, HP(bob(rush, 0.4, 0.6), dust=1, sway=5, flames=1.1, burn=1)),
        (100, HP(bob(rush, 0.2, 1.0), sway=4, burn=2, flames=1.0)),
        (170, HP(BLOCKH, sway=2)),
        (170, HP(P=(38.6, 47.6), C=(40.6, 35.2), Hd=(42.6, 23.8), hs=(49.0, 45.0), wang=-45, hsh=(47.0, 46.0))),
    ]


def h_guard():
    return [(220, HP(BLOCKH)), (220, HP(bob(BLOCKH, 0.4), glint=(55.0, 29.0)))]


def h_stagger():
    return [
        (90, HP(P=(36.6, 48.0), C=(34.4, 36.0), Hd=(33.2, 25.0), hup=(-0.45, -1), fb=(28.0, 71), ff=(47.0, 71),
                hs=(40.0, 30.0), wang=-128, wl="WeaponBack", armup=True, hsh=(44.0, 44.0), eye=0, flames=0.5)),
        (130, HP(P=(37.4, 52.0), C=(38.8, 40.4), Hd=(40.8, 29.2), hup=(0.2, -1), fb=(28.0, 71), ff=(48.0, 71),
                 hs=(46.0, 58.0), wang=70, hsh=(47.0, 52.0), eye=0, flames=0.4)),
        (260, HP(P=(37.8, 53.4), C=(40.6, 42.0), Hd=(43.8, 31.4), hup=(0.5, -1), fb=(28.0, 71), ff=(48.0, 71),
                 hs=(48.0, 60.0), wang=76, hsh=(48.0, 54.0), eye=0, flames=0.35)),
        (260, HP(P=(37.6, 53.8), C=(40.2, 42.4), Hd=(43.2, 31.8), hup=(0.46, -1), fb=(28.0, 71), ff=(48.0, 71),
                 hs=(47.8, 60.4), wang=78, hsh=(47.6, 54.4), eye=0, flames=0.35)),
    ]


KNEELH = dict(P=(37.0, 57.0), C=(40.2, 45.2), Hd=(43.6, 34.4), hup=(0.45, -1), kb=(33.0, 69.6), fb=(24.5, 71),
              ff=(47.0, 71), hs=(52.0, 52.0), wang=86, hsh=(46.0, 54.0), eye=0, flames=0.3)


def h_death():
    fr = [
        (100, HP(P=(36.6, 48.0), C=(34.4, 36.0), Hd=(33.2, 25.0), hup=(-0.5, -1), fb=(28.0, 71), ff=(47.0, 71),
                 hs=(40.0, 30.0), wang=-120, wl="WeaponBack", armup=True, hsh=(44.0, 44.0), eye=2)),
        (160, HP(P=(37.6, 52.0), C=(39.0, 40.4), Hd=(41.0, 29.4), hup=(0.25, -1), fb=(28.0, 71), ff=(48.0, 71),
                 hs=(48.0, 57.0), wang=78, hsh=(47.0, 51.0), eye=1, flames=0.5)),
        (200, HP(KNEELH)),
        (260, HP(dict(KNEELH, Hd=(44.4, 35.4), hup=(0.6, -1)))),
        (500, HP(dict(KNEELH, Hd=(44.6, 35.6), hup=(0.62, -1), flames=0.2))),
        (300, HP(dict(KNEELH, C=(41.0, 46.2), Hd=(45.6, 36.8), hup=(0.75, -1), flames=0.15))),
        (500, HP(dict(KNEELH, C=(41.0, 46.4), Hd=(45.8, 37.0), hup=(0.78, -1), flames=0.1))),
    ]
    for d, ms in ((0.14, 140), (0.32, 140), (0.52, 150), (0.74, 180), (0.99, 900)):
        fr.append((ms, HP(dict(KNEELH, C=(41.0, 46.4), Hd=(45.8, 37.0), hup=(0.78, -1), flames=0.0), dissolve=d)))
    return fr


def h_absorb():
    """Kneels by the fallen twin (element flows in), then rises, weapon flaring -- the phase-2 turn."""
    k = dict(KNEELH, hs=(50.0, 56.0), wang=80, eye=0, flames=0.4)
    rise = dict(P=(39.6, 48.4), C=(41.6, 35.6), Hd=(43.6, 24.2), hup=(0.15, -1), fb=(28.5, 71), ff=(51.0, 71))
    return [
        (140, HP(k)),
        (220, HP(dict(k, Hd=(44.0, 35.0)), burn=1)),
        (220, HP(dict(k, Hd=(43.2, 34.2), hup=(0.3, -1)), burn=2, eye=1)),
        (220, HP(dict(k, C=(39.6, 44.4), Hd=(42.4, 33.4), hup=(0.2, -1)), burn=3, eye=2, flames=0.8)),
        (120, HP(P=(38.6, 52.0), C=(39.8, 39.8), Hd=(41.4, 28.4), hup=(0.05, -1), fb=(27.0, 71), ff=(49.0, 71),
                 hs=(49.0, 44.0), wang=-60, hsh=(46.0, 49.0), burn=3, eye=2, flames=1.2)),
        (120, HP(rise, hs=(48.0, 28.0), wang=-96, armup=True, hsh=(47.0, 46.0), burn=4, eye=2, flames=1.6)),
        (360, HP(bob(rise, -0.6), hs=(47.0, 22.0), wang=-100, armup=True, hsh=(47.0, 45.0), burn=5, eye=2,
                 flames=2.0, glint="tip")),
        (200, HP(rise, hs=(50.0, 30.0), wang=-80, armup=True, hsh=(47.0, 46.0), burn=4, eye=2, flames=1.6)),
        (180, HP(rise, hs=(53.0, 42.0), wang=-58, hsh=(46.0, 47.0), burn=2, eye=2, flames=1.3)),
        (160, HP(flames=1.2)),
    ]


def h_plant():
    """Enraged move: drives the sword into the ice -- fire and frost erupt along the floor."""
    AU = dict(wl="WeaponBack", armup=True)
    hi = dict(P=(39.0, 47.0), C=(40.4, 34.2), Hd=(41.8, 22.8), hup=(0.05, -1), fb=(30.0, 71), ff=(50.0, 71))
    dn = dict(P=(41.0, 55.0), C=(44.4, 43.2), Hd=(47.6, 32.6), hup=(0.45, -1), kb=(36.0, 69.4), fb=(27.0, 71), ff=(52.0, 71))
    return [
        (140, HP(hi, hs=(50.0, 30.0), wang=-150 + 60, hsh=(46.0, 46.0))),
        (160, HP(bob(hi, -1.2), hs=(49.0, 20.0), wang=90, hsh=(45.0, 46.0), eye=2, flames=1.4, **AU)),
        (320, HP(bob(hi, -1.6), hs=(49.4, 18.6), wang=90, hsh=(45.0, 45.6), eye=2, flames=1.8, glint=(49.4, 12.0), **AU)),
        (70, HP(dn, hs=(53.0, 44.0), wang=90, hsh=(44.0, 52.0), eye=2, flames=1.6, plant=1)),
        (120, HP(dn, hs=(53.0, 45.0), wang=90, hsh=(44.0, 52.0), eye=2, flames=1.4, plant=2, shake=1)),
        (160, HP(dn, hs=(53.0, 45.0), wang=90, hsh=(44.0, 52.0), eye=2, flames=1.2, plant=3)),
        (220, HP(dn, hs=(53.0, 45.0), wang=90, hsh=(44.0, 52.0), eye=1, flames=1.0, plant=4)),
        (160, HP(bob(dn, -1.0), hs=(53.0, 42.0), wang=90, hsh=(44.0, 51.0), flames=0.9)),
        (160, HP(P=(40.0, 49.0), C=(42.0, 36.6), Hd=(44.0, 25.2), hup=(0.2, -1), fb=(29.0, 71), ff=(52.0, 71),
                 hs=(52.0, 38.0), wang=-70, hsh=(46.0, 47.0))),
        (160, HP()),
    ]


def h_lunge():
    """Lunging fire thrust: sword drawn back level, then a long burning stab."""
    WB = dict(wl="WeaponBack")
    draw_ = dict(P=(37.0, 48.6), C=(35.4, 36.8), Hd=(35.8, 25.6), hup=(-0.12, -1), fb=(29.0, 71), ff=(47.0, 71))
    lunge = dict(P=(45.0, 51.0), C=(51.0, 40.6), Hd=(56.2, 30.6), hup=(0.55, -1), fb=(26.0, 71), ff=(63.0, 71))
    return [
        (120, HP(P=(38.4, 47.6), C=(39.4, 35.2), Hd=(40.8, 23.8), hs=(48.0, 44.0), wang=-20, hsh=(46.0, 46.0))),
        (150, HP(draw_, hs=(34.0, 43.0), wang=-2, hsh=(47.0, 44.0), **WB)),
        (300, HP(bob(draw_, 0.4, -0.4), hs=(33.0, 43.4), wang=-1, hsh=(47.0, 44.4), eye=2, glint="tip", flames=1.5, **WB)),
        (70, HP(lunge, hs=(60.0, 43.0), wang=0, hsh=(44.0, 48.0), eye=2, flames=1.7, sway=4, thrustfx=1, dust=1)),
        (110, HP(lunge, hs=(61.5, 43.4), wang=1, hsh=(44.0, 48.0), eye=2, flames=1.3, sway=3, thrustfx=2)),
        (150, HP(P=(43.4, 50.0), C=(48.0, 39.4), Hd=(52.0, 29.0), hup=(0.4, -1), fb=(27.0, 71), ff=(60.0, 71),
                 hs=(57.0, 47.0), wang=18, hsh=(44.0, 48.0))),
        (150, HP(P=(41.0, 48.6), C=(44.0, 36.4), Hd=(47.0, 25.2), hup=(0.25, -1), fb=(29.0, 71), ff=(55.0, 71),
                 hs=(55.0, 44.0), wang=-10)),
        (150, HP(P=(40.0, 47.6), C=(41.6, 35.0), Hd=(43.4, 23.6), fb=(30.0, 71), ff=(52.0, 71), hs=(53.0, 43.0), wang=-40)),
        (140, HP()),
    ]


def h_leap():
    """Leaping overhead: crouch, spring (engine carries him through the air), crash down in fire."""
    AU = dict(wl="WeaponBack", armup=True)
    crouch = dict(P=(38.6, 52.0), C=(40.8, 40.0), Hd=(43.0, 28.8), hup=(0.25, -1), fb=(29.0, 71), ff=(49.0, 71))
    air = dict(P=(40.0, 47.0), C=(40.6, 34.6), Hd=(41.6, 23.2), hup=(0.0, -1), fb=(33.0, 66.0), ff=(47.0, 64.0))
    return [
        (130, HP(crouch, hs=(46.0, 48.0), wang=-40, hsh=(47.0, 50.0), dust=2)),
        (260, HP(bob(crouch, 1.2), hs=(45.0, 50.0), wang=-32, hsh=(47.0, 51.0), eye=2, glint="tip", flames=1.4)),
        (80, up(HP(P=(40.0, 46.0), C=(41.4, 33.6), Hd=(43.0, 22.2), hup=(0.1, -1), fb=(35.0, 70.0), ff=(46.0, 64.0),
                   hs=(48.0, 30.0), wang=-100, dust=1, **AU), 2)),
        (110, up(HP(air, hs=(40.0, 22.0), wang=-135, flames=1.5, **AU), 4)),
        (120, up(HP(air, hs=(37.0, 20.0), wang=-150, flames=1.7, **AU), 5)),
        (220, up(HP(dict(air, C=(40.0, 35.0), Hd=(40.6, 23.6)), hs=(36.0, 19.0), wang=-155, eye=2, glint="tip",
                    flames=2.0, **AU), 5)),
        (80, up(HP(P=(43.0, 48.0), C=(46.0, 37.0), Hd=(49.0, 26.0), hup=(0.35, -1), fb=(36.0, 67.0), ff=(52.0, 66.0),
                   hs=(56.0, 30.0), wang=-60, eye=2, flames=1.6, armup=True,
                   sm=dict(g0=(36.0, 14.0), a0=-155, mid=(46.0, 8.0), start=0.35, taper=0.85, u0=18)), 3)),
        (70, HP(SLAM, eye=2, slam=True, sway=3.0, cape=1.15, flames=1.2, impact=1)),
        (130, HP(SLAM, eye=2, sway=2.0, flames=1.0, impact=2, shake=1)),
        (170, HP(bob(SLAM, 0.6), flames=0.8, impact=3)),
        (160, HP(P=(42.0, 50.0), C=(45.6, 38.4), Hd=(48.8, 27.6), hup=(0.35, -1), fb=(28.0, 71), ff=(57.0, 71),
                 hs=(57.0, 46.0), wang=-10, hsh=(42.0, 46.0))),
        (150, HP()),
    ]


def h_wave():
    """Scrapes the burning blade along the ice and flings a wave of fire along the floor."""
    WB = dict(wl="WeaponBack")
    low = dict(P=(40.6, 50.4), C=(39.8, 38.2), Hd=(40.4, 26.8), hup=(-0.1, -1), fb=(29.0, 71), ff=(52.0, 71))
    drive = dict(P=(44.0, 51.0), C=(47.4, 39.4), Hd=(50.4, 28.6), hup=(0.35, -1), fb=(29.0, 71), ff=(58.0, 71))
    return [
        (120, HP(low, hs=(41.0, 58.0), wang=165, hsh=(49.0, 46.0), **WB)),
        (260, HP(bob(low, 0.4), hs=(39.0, 59.0), wang=170, hsh=(49.0, 46.4), eye=2, glint="tip", flames=1.5, **WB)),
        (70, HP(drive, hs=(50.0, 61.0), wang=176, hsh=(45.0, 48.0), eye=2, flames=1.5, dust=1, **WB)),
        (60, HP(drive, hs=(58.0, 58.0), wang=8, hsh=(44.0, 48.0), eye=2, flames=1.6, sway=3,
                sm=dict(g0=(50.0, 61.0), a0=176, mid=(55.0, 66.0), start=0.1, u0=10))),
        (90, HP(drive, hs=(60.0, 42.0), wang=-35, hsh=(44.0, 48.0), eye=2, flames=1.4, sway=3, mark=1,
                sm=dict(g0=(58.0, 58.0), a0=8, taper=0.4, u0=16))),
        (140, HP(dict(drive, C=(46.6, 38.4), Hd=(49.4, 27.4)), hs=(56.0, 31.0), wang=-70, hsh=(44.0, 48.0), armup=True)),
        (150, HP(P=(42.0, 49.0), C=(43.6, 36.4), Hd=(45.4, 25.0), hup=(0.2, -1), fb=(29.5, 71), ff=(54.0, 71),
                 hs=(54.0, 36.0), wang=-62)),
        (150, HP(P=(40.6, 47.8), C=(42.0, 35.2), Hd=(43.8, 23.8), fb=(30.0, 71), ff=(52.0, 71), hs=(53.0, 42.0), wang=-55)),
        (140, HP(hs=(52.4, 44.0), wang=-53)),
        (130, HP()),
    ]


def h_launch():
    """Rising uppercut that throws the target into the air (duo launcher)."""
    low = dict(P=(40.0, 49.6), C=(41.6, 37.4), Hd=(43.2, 26.0), hup=(0.18, -1), fb=(29.0, 71), ff=(51.0, 71))
    rise = dict(P=(44.0, 48.0), C=(47.6, 35.4), Hd=(50.6, 24.2), hup=(0.35, -1), fb=(31.0, 71), ff=(57.0, 71))
    return [
        (120, HP(low, hs=(50.0, 57.0), wang=40, hsh=(47.0, 46.0))),
        (250, HP(bob(low, 1.0), hs=(49.0, 59.0), wang=52, hsh=(47.0, 47.0), eye=2, glint="tip", flames=1.4)),
        (60, HP(rise, hs=(60.0, 36.0), wang=-70, hsh=(45.0, 47.0), eye=2, armup=True, flames=1.5, sway=3,
                sm=dict(g0=(49.0, 59.0), a0=52, start=0.1, u0=10))),
        (90, HP(rise, hs=(55.0, 22.0), wang=-100, hsh=(45.0, 47.0), eye=2, armup=True, flames=1.3, sway=2,
                sm=dict(g0=(60.0, 36.0), a0=-70, taper=0.3, u0=18))),
        (150, HP(rise, hs=(53.0, 25.0), wang=-96, hsh=(45.0, 47.0), armup=True)),
        (150, HP(P=(42.0, 48.4), C=(44.0, 35.8), Hd=(46.0, 24.4), hup=(0.2, -1), fb=(30.0, 71), ff=(54.0, 71),
                 hs=(53.0, 32.0), wang=-75)),
        (150, HP(P=(40.6, 47.6), C=(42.0, 35.0), Hd=(43.6, 23.6), fb=(30.0, 71), ff=(52.0, 71), hs=(53.0, 40.0), wang=-60)),
        (140, HP(hs=(52.4, 43.6), wang=-54)),
        (130, HP()),
    ]


HAEL_TAGS = [("idle", h_idle), ("walk", h_walk), ("slash", h_slash), ("slam", h_slam), ("bash", h_bash),
             ("guard", h_guard), ("stagger", h_stagger), ("death", h_death), ("absorb", h_absorb), ("plant", h_plant),
             ("lunge", h_lunge), ("leap", h_leap), ("wave", h_wave), ("launch", h_launch)]


# =========================================================================== DAME RIME  (frost, kite shield)
def r_idle():
    fr = []
    for i in range(6):
        b = (0, 0.4, 0.8, 1.1, 0.8, 0.4)[i]
        fr.append((170, RP(P=(40.0, 45.8 + b * 0.3), C=(41.2, 34.6 + b), Hd=(42.4, 24.0 + b), hs=(53.0, 42.0 + b * 0.8),
                           hsh=(48.5, 44.5 + b * 0.7), wang=-62 + b, sway=0.7 * math.sin(i * 1.05), plume=0.8 * math.sin(i * 1.05 + 0.6))))
    return fr


def r_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s = math.cos(ph), math.sin(ph)
        ff = (42.0 + 8.0 * c, 71 - max(0.0, -s) * 3.4)
        fb = (39.0 - 8.0 * c, 71 - max(0.0, s) * 3.4)
        bb = 1.2 * abs(c)
        fr.append((110, RP(P=(40.4, 46.2 + bb), C=(42.0, 35.0 + bb), Hd=(43.4, 24.4 + bb), ff=ff, fb=fb,
                           hs=(53.4 + c, 42.6 + bb), hsh=(49.0 - c, 45.0 + bb), wang=-60 + 3 * c, sway=1.2 * s,
                           plume=1.4 * s + 1.0)))
    return fr


THRUST = dict(P=(43.0, 51.0), C=(50.4, 42.0), Hd=(56.6, 33.8), hup=(0.55, -1), fb=(22.0, 71), ff=(64.0, 71),
              hs=(60.0, 41.0), wang=-3, hsh=(40.0, 44.0), sh=dict(c=(37.0, 45.5), w=4.8, h=14.0, ang=28.0, face=-0.1),
              eye=2, wl="Weapon", sway=4.0, cape=1.2, plume=4.0)


def r_thrust():
    draw_ = dict(P=(37.6, 48.2), C=(36.2, 36.8), Hd=(36.4, 26.2), hup=(-0.12, -1), fb=(29.0, 71), ff=(47.0, 71))
    return [
        (120, RP(P=(39.4, 47.0), C=(40.2, 35.6), Hd=(41.4, 25.0), hs=(49.0, 44.0), wang=-30, hsh=(49.0, 45.0))),
        (150, RP(draw_, hs=(36.0, 41.0), wang=-4, hsh=(47.0, 44.0), plume=-2.0)),
        (330, RP(bob(draw_, 0.4, -0.4), hs=(34.6, 41.2), wang=-3, hsh=(47.0, 44.4), eye=2, glint="tip", plume=-2.5)),
        (70, RP(THRUST, thrust=True)),
        (120, RP(dict(THRUST, hs=(61.0, 41.4)), thrust=False, glint="tip")),
        (140, RP(P=(42.0, 49.4), C=(47.6, 39.4), Hd=(52.8, 30.2), hup=(0.45, -1), fb=(23.5, 71), ff=(62.0, 71),
                 hs=(57.0, 46.0), wang=18, hsh=(41.0, 45.0), sh=dict(c=(38.5, 47.0), w=5.0, h=15.0, ang=20.0, face=0.0), plume=3.0)),
        (150, RP(P=(41.2, 48.2), C=(44.6, 37.0), Hd=(48.0, 26.6), hup=(0.3, -1), fb=(27.0, 71), ff=(57.0, 71),
                 hs=(55.0, 44.0), wang=-10, hsh=(45.0, 45.0), plume=2.0)),
        (150, RP(P=(40.6, 46.8), C=(42.2, 35.4), Hd=(43.6, 24.8), fb=(30.0, 71), ff=(52.0, 71), hs=(53.0, 43.0),
                 wang=-40, plume=1.0)),
        (140, RP()),
    ]


def r_combo():
    AU = dict(armup=True)
    cock = dict(P=(39.0, 46.6), C=(38.6, 35.2), Hd=(39.2, 24.6), hup=(-0.12, -1), fb=(30.0, 71), ff=(49.0, 71))
    step1 = dict(P=(44.6, 48.0), C=(48.4, 37.2), Hd=(51.4, 27.0), hup=(0.4, -1), fb=(31.0, 71), ff=(58.0, 71))
    step2 = dict(P=(46.6, 48.6), C=(50.6, 37.8), Hd=(54.0, 27.8), hup=(0.45, -1), fb=(33.0, 71), ff=(60.0, 71))
    return [
        (110, RP(cock, hs=(44.0, 25.0), wang=-120, hsh=(49.0, 44.0), **AU)),
        (230, RP(bob(cock, 0.4), hs=(42.6, 24.0), wang=-128, hsh=(49.0, 44.4), eye=2, glint="tip", **AU)),
        (60, RP(step1, hs=(61.0, 44.0), wang=18, hsh=(46.0, 46.0), sway=2, plume=3,
                sm=dict(g0=(42.6, 24.0), a0=-128, mid=(56.0, 22.0), start=0.1))),
        (90, RP(step1, hs=(57.0, 53.0), wang=64, hsh=(46.0, 46.0), sway=2, plume=3,
                sm=dict(g0=(61.0, 44.0), a0=18, taper=0.45, u0=14))),
        (100, RP(P=(43.0, 47.8), C=(44.6, 36.2), Hd=(46.6, 25.6), hup=(0.15, -1), fb=(31.0, 71), ff=(56.0, 71),
                 hs=(46.0, 56.0), wang=158, hsh=(50.0, 45.0), wl="WeaponBack")),
        (170, RP(P=(43.0, 48.2), C=(44.0, 36.6), Hd=(45.6, 26.0), hup=(0.1, -1), fb=(31.0, 71), ff=(56.0, 71),
                 hs=(44.0, 57.0), wang=164, hsh=(50.0, 45.4), wl="WeaponBack", eye=2, glint="tip")),
        (60, RP(step2, hs=(62.0, 38.0), wang=-40, hsh=(47.0, 46.0), sway=3, plume=3.5,
                sm=dict(g0=(44.0, 57.0), a0=164, mid=(55.0, 64.0), start=0.08))),
        (90, RP(step2, hs=(58.0, 26.0), wang=-90, hsh=(47.0, 46.0), sway=2, plume=3.5, armup=True,
                sm=dict(g0=(62.0, 38.0), a0=-40, taper=0.25, u0=20, start=0.3))),
        (150, RP(P=(43.0, 47.2), C=(45.0, 35.8), Hd=(47.2, 25.2), hup=(0.2, -1), fb=(31.0, 71), ff=(56.0, 71),
                 hs=(55.0, 34.0), wang=-70, hsh=(48.0, 45.0), plume=2)),
        (150, RP()),
    ]


def r_cast():
    AU = dict(armup=True, wl="WeaponBack")
    st = dict(P=(39.4, 46.4), C=(40.0, 34.6), Hd=(40.8, 24.0), hup=(-0.05, -1), fb=(29.0, 71), ff=(50.0, 71))
    return [
        (130, RP(st, hs=(46.0, 34.0), wang=-80, hsh=(48.0, 45.0))),
        (150, RP(bob(st, -0.8), hs=(44.0, 20.0), wang=-92, hsh=(50.0, 44.0), eye=2, **AU)),
        (150, RP(bob(st, -1.2), hs=(43.6, 17.0), wang=-94, hsh=(51.0, 43.6), eye=2, cast=1, **AU)),
        (170, RP(bob(st, -1.4), hs=(43.4, 16.0), wang=-94, hsh=(51.0, 43.4), eye=2, cast=2, **AU)),
        (230, RP(bob(st, -1.6), hs=(43.2, 15.4), wang=-94, hsh=(51.0, 43.2), eye=2, cast=3, glint="tip", **AU)),
        (140, RP(bob(st, -1.6), hs=(43.2, 15.4), wang=-94, hsh=(51.0, 43.2), eye=2, cast=4, **AU)),
        (80, RP(bob(st, 0.6, 1.0), hs=(50.0, 30.0), wang=-60, hsh=(50.0, 45.0), eye=2, cast=5, plume=2.0)),
        (160, RP(bob(st, 0.4, 0.6), hs=(52.0, 36.0), wang=-52, hsh=(49.0, 45.0), cast=6, plume=1.5)),
        (160, RP(hs=(53.0, 40.0), wang=-58)),
        (140, RP()),
    ]


def r_backstep():
    return [
        (90, RP(P=(40.4, 48.6), C=(42.0, 37.4), Hd=(43.6, 26.8), hup=(0.2, -1), fb=(32.0, 71), ff=(48.0, 71),
                hs=(50.0, 46.0), wang=-40, hsh=(48.0, 46.0))),
        (80, up(RP(P=(38.8, 46.0), C=(37.4, 35.0), Hd=(37.4, 24.6), hup=(-0.22, -1), fb=(31.0, 69.0), ff=(49.0, 71.0),
                   hs=(48.0, 42.0), wang=-52, hsh=(46.0, 42.0), dust=1, plume=4, sway=-3), 2)),
        (110, up(RP(P=(37.4, 45.0), C=(36.2, 34.2), Hd=(36.4, 23.8), hup=(-0.15, -1), fb=(31.0, 65.0), ff=(45.0, 64.0),
                    hs=(46.0, 40.0), wang=-50, hsh=(45.0, 41.0), plume=5, sway=-5), 7)),
        (100, up(RP(P=(37.8, 46.0), C=(37.6, 35.0), Hd=(38.4, 24.4), hup=(-0.05, -1), fb=(30.0, 68.0), ff=(46.0, 69.0),
                    hs=(47.0, 42.0), wang=-46, hsh=(46.0, 43.0), plume=3, sway=-3), 2)),
        (110, RP(P=(38.6, 50.4), C=(40.0, 39.4), Hd=(41.6, 28.8), hup=(0.1, -1), fb=(30.0, 71), ff=(47.0, 71),
                 hs=(49.0, 48.0), wang=-36, hsh=(47.0, 47.0), dust=1)),
        (150, RP(P=(39.6, 47.0), C=(40.8, 35.6), Hd=(42.2, 25.0), hs=(52.0, 44.0), wang=-52, dust=2)),
    ]


BLOCKR = dict(P=(38.6, 47.4), C=(40.2, 36.4), Hd=(42.4, 26.2), hup=(0.25, -1), fb=(29.0, 71), ff=(49.5, 71),
              hs=(47.5, 31.0), wang=-10, hsh=(50.0, 40.0), sh=dict(c=(52.5, 42.5), w=5.8, h=19.0, ang=-6.0, face=0.45),
              eye=2, sway=-1.0)


def r_guard():
    return [(220, RP(BLOCKR)), (220, RP(bob(BLOCKR, 0.4), glint=(56.0, 36.0)))]


def r_stagger():
    return [
        (90, RP(P=(37.6, 46.6), C=(35.4, 35.4), Hd=(34.4, 25.2), hup=(-0.45, -1), fb=(29.0, 71), ff=(47.0, 71),
                hs=(40.0, 28.0), wang=-126, wl="WeaponBack", armup=True, hsh=(44.0, 42.0), eye=0, plume=5)),
        (130, RP(P=(38.4, 51.0), C=(39.6, 40.0), Hd=(41.4, 29.4), hup=(0.2, -1), fb=(29.0, 71), ff=(47.0, 71),
                 hs=(47.0, 57.0), wang=66, hsh=(47.0, 50.0), eye=0, plume=2)),
        (260, RP(P=(38.8, 52.6), C=(41.2, 41.6), Hd=(44.2, 31.4), hup=(0.5, -1), fb=(29.0, 71), ff=(47.0, 71),
                 hs=(48.0, 59.0), wang=74, hsh=(48.0, 52.0), eye=0, plume=1)),
        (260, RP(P=(38.6, 53.0), C=(40.8, 42.0), Hd=(43.6, 31.8), hup=(0.46, -1), fb=(29.0, 71), ff=(47.0, 71),
                 hs=(47.8, 59.4), wang=76, hsh=(47.8, 52.4), eye=0, plume=1)),
    ]


KNEELR = dict(P=(38.0, 56.0), C=(41.0, 44.8), Hd=(44.2, 34.4), hup=(0.45, -1), kb=(34.0, 69.6), fb=(25.5, 71),
              ff=(48.0, 71), hs=(52.0, 52.0), wang=86, hsh=(47.0, 53.0), eye=0, cape_drop=-2.0)


def r_death():
    fr = [
        (100, RP(P=(37.6, 46.6), C=(35.4, 35.4), Hd=(34.4, 25.2), hup=(-0.5, -1), fb=(29.0, 71), ff=(47.0, 71),
                 hs=(40.0, 28.0), wang=-120, wl="WeaponBack", armup=True, hsh=(44.0, 42.0), eye=2, plume=6)),
        (160, RP(P=(38.4, 51.0), C=(39.8, 40.0), Hd=(41.6, 29.4), hup=(0.25, -1), fb=(29.0, 71), ff=(47.0, 71),
                 hs=(48.0, 56.0), wang=78, hsh=(47.0, 50.0), eye=1, plume=2)),
        (200, RP(KNEELR)),
        (260, RP(dict(KNEELR, Hd=(45.0, 35.4), hup=(0.6, -1)))),
        (500, RP(dict(KNEELR, Hd=(45.2, 35.6), hup=(0.62, -1)))),
        (300, RP(dict(KNEELR, C=(41.8, 45.8), Hd=(46.2, 36.8), hup=(0.75, -1)))),
        (500, RP(dict(KNEELR, C=(41.8, 46.0), Hd=(46.4, 37.0), hup=(0.78, -1)))),
    ]
    for d, ms in ((0.14, 140), (0.3, 140), (0.48, 140), (0.66, 160), (0.99, 900)):
        fr.append((ms, RP(dict(KNEELR, C=(41.8, 46.0), Hd=(46.4, 37.0), hup=(0.78, -1)), dissolve=d)))
    return fr


def r_absorb():
    k = dict(KNEELR, hs=(50.0, 55.0), wang=80)
    rise = dict(P=(40.0, 46.6), C=(41.6, 35.2), Hd=(43.0, 24.6), hup=(0.1, -1), fb=(29.5, 71), ff=(51.0, 71))
    return [
        (140, RP(k)),
        (220, RP(dict(k, Hd=(45.0, 35.0)), burn=1)),
        (220, RP(dict(k, Hd=(44.2, 34.2), hup=(0.3, -1)), burn=2, eye=1)),
        (220, RP(dict(k, C=(40.4, 44.0), Hd=(43.0, 33.4), hup=(0.2, -1)), burn=3, eye=2)),
        (120, RP(P=(39.4, 50.6), C=(40.4, 39.0), Hd=(41.8, 28.4), hup=(0.05, -1), fb=(28.0, 71), ff=(49.0, 71),
                 hs=(50.0, 42.0), wang=-60, hsh=(48.0, 47.0), burn=3, eye=2)),
        (120, RP(rise, hs=(47.0, 24.0), wang=-94, armup=True, wl="WeaponBack", hsh=(49.0, 44.0), burn=4, eye=2, plume=3)),
        (360, RP(bob(rise, -0.6), hs=(46.4, 19.0), wang=-96, armup=True, wl="WeaponBack", hsh=(49.0, 43.4), burn=5,
                 eye=2, glint="tip", plume=4)),
        (200, RP(rise, hs=(49.0, 28.0), wang=-78, armup=True, hsh=(49.0, 44.0), burn=4, eye=2, plume=3)),
        (180, RP(rise, hs=(52.0, 38.0), wang=-62, hsh=(48.5, 44.5), burn=2, eye=2, plume=2)),
        (160, RP()),
    ]


def r_volley():
    """Frost gathers at her point, then three quick jabs each loose an ice lance."""
    st = dict(P=(38.8, 46.8), C=(38.6, 35.2), Hd=(39.2, 24.6), hup=(-0.05, -1), fb=(29.0, 71), ff=(50.0, 71))
    jab = lambda d, k: RP(bob(st, 0.4, 1.2 + d), hs=(56.0 + d, 38.0 + k * 2), wang=-14 + k * 6, cast=5, plume=2.0, eye=2)
    back = lambda k: RP(bob(st, 0.2, 0.4), hs=(50.0, 37.0 + k * 2), wang=-24 + k * 6, eye=2)
    return [
        (120, RP(st, hs=(46.0, 38.0), wang=-30, hsh=(48.0, 45.0))),
        (140, RP(st, hs=(44.0, 34.0), wang=-40, cast=1, eye=2)),
        (150, RP(st, hs=(44.0, 33.0), wang=-42, cast=2, eye=2)),
        (250, RP(st, hs=(43.6, 32.6), wang=-42, cast=3, eye=2, glint="tip")),
        (90, jab(0, 0)), (80, back(0)),
        (90, jab(0.6, 1)), (80, back(1)),
        (90, jab(1.2, 2)),
        (170, RP(hs=(53.0, 42.0), wang=-50)),
    ]


def r_spikes():
    """Drives her sword point-first into the ice: a line of frozen spikes races toward the target."""
    AU = dict(armup=True, wl="WeaponBack")
    hi = dict(P=(39.4, 46.6), C=(40.2, 35.0), Hd=(41.2, 24.4), hup=(0.05, -1), fb=(30.0, 71), ff=(50.0, 71))
    dn = dict(P=(42.0, 54.0), C=(45.4, 42.6), Hd=(48.4, 32.4), hup=(0.45, -1), kb=(37.0, 69.4), fb=(28.0, 71), ff=(53.0, 71))
    return [
        (130, RP(hi, hs=(50.0, 30.0), wang=-60, hsh=(48.0, 45.0))),
        (160, RP(bob(hi, -1.0), hs=(48.0, 18.0), wang=90, hsh=(47.0, 44.0), eye=2, **AU)),
        (300, RP(bob(hi, -1.4), hs=(48.4, 16.6), wang=90, hsh=(47.0, 43.6), eye=2, glint=(48.4, 10.0), **AU)),
        (70, RP(dn, hs=(55.0, 43.0), wang=90, hsh=(46.0, 51.0), eye=2, plant=1)),
        (120, RP(dn, hs=(55.0, 44.0), wang=90, hsh=(46.0, 51.0), eye=2, plant=2, shake=1)),
        (160, RP(dn, hs=(55.0, 44.0), wang=90, hsh=(46.0, 51.0), plant=3)),
        (200, RP(dn, hs=(55.0, 44.0), wang=90, hsh=(46.0, 51.0), plant=4)),
        (160, RP(bob(dn, -1.0), hs=(55.0, 41.0), wang=90, hsh=(46.0, 50.0))),
        (160, RP(P=(40.4, 48.0), C=(42.0, 36.6), Hd=(43.8, 26.0), hup=(0.2, -1), fb=(30.0, 71), ff=(52.0, 71),
                 hs=(52.0, 38.0), wang=-60)),
        (140, RP()),
    ]


def r_charge():
    rush = dict(P=(46.0, 49.5), C=(51.6, 40.0), Hd=(55.6, 30.4), hup=(0.6, -1), fb=(29.0, 71), ff=(61.0, 71),
                hs=(46.0, 46.0), wang=-20, wl="WeaponBack", hsh=(61.0, 39.0),
                sh=dict(c=(63.0, 42.0), w=5.6, h=18.0, ang=-4.0, face=0.5), eye=2, plume=5.0, sway=4)
    return [
        (120, RP(BLOCKR)),
        (170, RP(bob(BLOCKR, 1.4, -1.0), glint=(57.0, 34.0), dust=2)),
        (150, RP(bob(BLOCKR, 1.8, -1.2))),
        (70, RP(rush, dust=1)),
        (70, RP(bob(rush, 0.4, 0.6), dust=1, plume=6.0)),
        (100, RP(bob(rush, 0.2, 1.0), plume=5.0)),
        (170, RP(BLOCKR, sway=2)),
        (160, RP(P=(39.6, 47.0), C=(40.8, 35.6), Hd=(42.2, 25.0), hs=(51.0, 44.0), wang=-50)),
    ]


CNT = dict(P=(38.0, 49.0), C=(37.6, 37.4), Hd=(38.4, 26.8), hup=(-0.1, -1), fb=(28.0, 71), ff=(50.0, 71),
           hs=(35.0, 51.0), wang=160, wl="WeaponBack", hsh=(49.0, 42.0),
           sh=dict(c=(51.5, 45.0), w=5.8, h=19.0, ang=-4.0, face=0.45), eye=2, plume=-2.0)


def r_counter():
    return [(240, RP(CNT, aura=1)), (240, RP(bob(CNT, 0.4), aura=2, glint=(53.0, 37.0)))]


def r_riposte():
    lead = dict(P=(47.0, 49.0), C=(52.0, 38.6), Hd=(56.0, 28.8), hup=(0.5, -1), fb=(31.0, 71), ff=(62.0, 71))
    return [
        (50, RP(CNT, aura=2)),
        (60, RP(P=(44.0, 48.0), C=(47.0, 37.0), Hd=(50.0, 27.0), hup=(0.35, -1), fb=(30.0, 71), ff=(58.0, 71),
                hs=(40.0, 53.0), wang=170, wl="WeaponBack", eye=2, aura=1)),
        (60, RP(lead, hs=(64.0, 44.0), wang=-10, eye=2, plume=4, sway=3,
                sm=dict(g0=(40.0, 53.0), a0=170, mid=(54.0, 62.0), start=0.05))),
        (90, RP(lead, hs=(60.0, 32.0), wang=-72, eye=2, plume=4, sway=2, armup=True,
                sm=dict(g0=(64.0, 44.0), a0=-10, taper=0.3, u0=20))),
        (130, RP(lead, hs=(58.0, 31.0), wang=-78, armup=True, plume=3)),
        (150, RP(P=(43.0, 47.4), C=(45.6, 36.0), Hd=(48.0, 25.6), hup=(0.25, -1), fb=(30.0, 71), ff=(56.0, 71),
                 hs=(55.0, 36.0), wang=-65)),
        (150, RP(P=(40.6, 46.8), C=(42.2, 35.4), Hd=(43.6, 24.8), fb=(30.0, 71), ff=(52.0, 71), hs=(53.0, 42.0), wang=-55)),
        (140, RP()),
    ]


RIME_TAGS = [("idle", r_idle), ("walk", r_walk), ("thrust", r_thrust), ("combo", r_combo), ("cast", r_cast),
             ("backstep", r_backstep), ("guard", r_guard), ("stagger", r_stagger), ("death", r_death), ("absorb", r_absorb),
             ("volley", r_volley), ("spikes", r_spikes), ("charge", r_charge), ("counter", r_counter), ("riposte", r_riposte)]


# =========================================================================== extra FX drawn into the frames
def blade_info(p, spec):
    pix, blade, tip = blade_px(MR, p["hs"], p["wang"], spec)
    return {q for q in blade if q[1] <= FLOOR}, tip, MR.T(p["hs"]), MR.A(p["wang"])


def add_fx(who, p, Ls, info, enr, fi):
    FX, FXB = Ls["FX"], Ls["FXBack"]
    spec = T.HBLADE if who == "hael" else T.RBLADE
    blade, tip, g0, a0 = blade_info(p, spec)
    info["tip"] = tip
    info["blade"] = blade
    info["hit"] = set()
    if p.get("sm"):
        s = p["sm"]
        pal = ("flame2" if enr else "flame") if who == "hael" else ("frost2" if enr else "frost")
        hot = swept(FX, s["g0"], s["a0"], g0, a0, s.get("u0", 14), spec["end"], hw=1.1 if who == "hael" else 0.9,
                    mid=s.get("mid"), start=s.get("start", 0.0), pal=pal, taper=s.get("taper", 0.7),
                    exclude=blade, clip_y=FLOOR)
        info["hit"] |= hot | blade
    if p.get("glint"):
        g = tip if p["glint"] == "tip" else p["glint"]
        g = (min(W - 4, max(3, g[0])), min(FLOOR - 3, max(3, g[1])))
        core = "Y3"
        armc = ("O4" if not enr else "U3") if who == "hael" else ("U3" if not enr else "O4")
        star(FX, g, core, armc)
        info["glint"] = [int(round(g[0])), int(round(g[1]))]
    if p.get("thrust"):
        info["hit"] |= {q for q in line(ip(g0), ip(tip))} | blade
        for k in range(-2, 3):
            q = ip(add(tip, (2 + k, k * 0.6)))
            info["hit"].add(q)
    if p.get("impact"):
        st = p["impact"]
        ix = int(round(min(tip[0], W - 4)))
        info["impact_x"] = ix
        if st >= 2:
            fl_pal = T.COLDFIRE if enr and st % 2 else T.FIRE
            n = {2: 7, 3: 5, 4: 3}[st]
            for k in range(n):
                dx = (k - (n - 1) / 2) * 4.2 + hash01(k, st, 5) * 1.5
                sz = (5.5 - abs(dx) * 0.28) * {2: 1.0, 3: 0.7, 4: 0.45}[st]
                if sz > 0.8:
                    T.flame(FXB, (ix + dx - 0.5, FLOOR + 0.5), sz * 1.3, fi + k, seed=k * 7, pal=T.FIRE_BACK)
                    T.flame(FX, (ix + dx, FLOOR + 0.5), sz * 0.8, fi + k, seed=k * 11 + 2, pal=fl_pal)
            for dx in range(-18, 19):
                if hash01(dx, st, 33) < (0.7 if st == 2 else 0.4):
                    FX.put([(ix + dx, FLOOR)], "O3" if abs(dx) < 6 else "O2" if st < 4 else "O1")
            T.embers(FX, (ix - 18, FLOOR - 26 - st * 3, ix + 18, FLOOR - 4), 14 - st * 2, 90 + fi)
        if st <= 2:
            info["hit"] |= {(x, y) for x in range(ix - 16, ix + 17) for y in range(FLOOR - 16, FLOOR + 1)}
    if p.get("plant"):
        st = p["plant"]
        ix = int(round(tip[0]))
        info["impact_x"] = ix
        for k in range(10):
            a = math.radians(-170 + 160 * hash01(k, st, 71))
            r = (4 + 10 * hash01(k, st, 72)) * (0.6 + 0.2 * st)
            q = ip((ix + math.cos(a) * r * 1.4, FLOOR - 1 + math.sin(a) * r * 0.5))
            mixed = enr
            hot, dim = (("U4", "O4", "U3", "O3"), ("U2", "O2")) if mixed else ((("U4", "N4", "U3", "N3"), ("U2", "N2")) if who == "rime" else (("Y3", "O4", "Y2", "O3"), ("O3", "O2")))
            FX.put([q], hot[k % 4] if st < 4 else dim[k % 2])
        for dx in range(-8 - 4 * st, 9 + 4 * st):
            if hash01(dx, st, 73) < 0.6:
                near = ("U3", "O3") if mixed else (("U3", "N3") if who == "rime" else ("O4", "O3"))
                far = ("U1", "O1") if mixed else (("U1", "N2") if who == "rime" else ("O2", "O1"))
                FX.put([(ix + dx, FLOOR)], (near if abs(dx) < 10 else far)[0 if dx < 0 else 1])
        if st <= 2:
            info["hit"] |= {(x, y) for x in range(ix - 14, ix + 15) for y in range(FLOOR - 10, FLOOR + 1)}
    if p.get("cast"):
        st = p["cast"]
        c = tip
        pal = ("U4", "U3", "U2", "U1") if not enr else ("Y3", "O4", "U3", "O2")
        if st <= 4:
            n = 6 + st * 3
            for k in range(n):
                a = k * 2 * math.pi / n + st * 0.5
                rr = 9 - st * 1.5 + (k % 2)
                q = ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
                FX.put([q], pal[k % 3 + (1 if st < 2 else 0)])
            T.sparkle(FX, c, big=st >= 3, pal=(pal[0], pal[1]))
        else:
            for k in range(8):
                a = hash01(k, st, 3) * 6.28
                r = 4 + st * 2 + hash01(k, st, 4) * 4
                FX.put([ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))], pal[2 + (k % 2)])
    if p.get("burn"):
        # absorbing the fallen twin's element: wisps streaming in from behind, gathering around the body
        st = p["burn"]
        pal = ("U4", "U3", "U2", "U1") if who == "hael" else ("Y3", "O4", "O3", "O2")
        P_, C_ = p["P"], p["C"]
        for k in range(10 + st * 4):
            ph = (hash01(k, 1, 61) + st * 0.17) % 1.0
            a = hash01(k, 2, 61) * 6.28
            r = (1 - ph) * (22 - st * 2) + 4
            q = ip((C_[0] + math.cos(a) * r * 1.2 - 4, C_[1] + 4 + math.sin(a) * r))
            (FX if k % 3 else FXB).put([q], pal[min(3, int(ph * 4))])
    if p.get("thrustfx"):
        pal = ("flame2" if enr else "flame")
        pts = thrust_lines(FX, g0, a0, -28, 6, (-3, -1, 2, 4) if p["thrustfx"] == 1 else (-2, 3), pal=pal,
                           flash=spec["end"] + 1 if p["thrustfx"] == 2 else None)
        for k, u in enumerate(range(8, 30, 5)):
            b = blade_line(g0, a0, u)
            T.flame(FX, (b[0] - 2, b[1] + 0.5), 1.4 + k * 0.3, fi + k, seed=k * 3, pal=T.COLDFIRE if enr and k % 2 else T.FIRE)
        info["hit"] |= {q for q in pts if q[0] > AX} | blade
    if p.get("mark"):
        info["impact_x"] = int(min(W - 4, tip[0] + 6))
    if p.get("aura"):
        pal = ("U4", "U3", "U2", "U1") if not enr else ("Y3", "O4", "U3", "O2")
        C_ = p["C"]
        for dx in range(-14, 15):
            if (dx + fi) % 3:
                FXB.put([(int(p["P"][0] + dx), FLOOR)], pal[1] if abs(dx) < 8 else pal[3])
        for k in range(22):
            a = k / 22 * 6.283 + fi * 0.4
            r = 17 + (k % 3) + p["aura"]
            q = ip((C_[0] + math.cos(a) * r * 0.8, C_[1] + 4 + math.sin(a) * r))
            if q[1] <= FLOOR and (k + fi) % 2 == 0:
                (FX if math.sin(a) > -0.2 else FXB).put([q], pal[k % 4])
        T.sparkle(FX, add(C_, (8, -4)), big=p["aura"] == 2, pal=(pal[0], pal[1]))
    if p.get("dust"):
        for fx_ in ((p["fb"][0], -1), (p["ff"][0], 1)):
            for k in range(6):
                x = int(fx_[0] + fx_[1] * (1 + k * 1.3) + (hash01(k, fi, 9) - 0.5) * 2)
                y = FLOOR - int(hash01(k, fi, 10) * (2 + k * 0.5) * (1 if p["dust"] == 1 else 0.6))
                FX.put([(x, y)], ("N4", "E4", "N3")[k % 3] if p["dust"] == 1 else "E3")
    return info


def render_frame(who, p, fi, enr):
    p = dict(p)
    p["fi"] = fi
    p["enr"] = enr
    base_p = dict(p)
    if who == "hael":
        base_p["slam"] = bool(p.get("slam"))
        Ls, info = T.draw_hael(base_p, MR)
        order = T.HL
        rim = T.HAEL_RIM
    else:
        base_p["thrust"] = bool(p.get("thrust"))
        Ls, info = T.draw_rime(base_p, MR)
        order = T.RL
        rim = T.RIME_RIM
    info = add_fx(who, p, Ls, info, enr, fi)
    imgs = {n: (K.render_layer(v) if isinstance(v, Layer) else v.image()) for n, v in Ls.items()}
    body = K.flatten(imgs, [n for n in order if n not in T.FXL])
    if enr:
        for side, cols, st in rim:
            T.rim_light(body, side, cols, st)
    out = {"FXBack": imgs["FXBack"], "Body": body, "FX": imgs["FX"]}
    if p.get("dissolve", 0) > 0:
        pal = ("O5", "O4", "O3", "O2", "O1") if who == "hael" else ("U4", "U3", "U2", "U1", "U0")
        if enr:
            pal = ("U4", "O4", "U2", "O2", "U1")
        out = K.ember_dissolve(out, p["dissolve"], ["Body"], fx_name="FX", seed=5 if who == "hael" else 9, rise=26, pal=pal)
        out["FXBack"] = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if p.get("shake"):
        out = K.shift_imgs(out, p["shake"], 0)
    # body mask for the hurtbox
    info["bodybox"] = out["Body"].getbbox()
    return out, info


def render_twin(who, only=None):
    tags_def = HAEL_TAGS if who == "hael" else RIME_TAGS
    out = {1: [], 2: []}
    infos, tags = {}, []
    n = 0
    for tag, fn in tags_def:
        fr = fn()
        if only and tag not in only:
            continue
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in (1, 2):
                imgs, info = render_frame(who, p, a + k, ph == 2)
                out[ph].append((ms, imgs))
                if ph == 1:
                    infos[tag].append(info)
            n += 1
        tags.append((tag, a, n - 1))
        print(who, "rendered", tag, len(fr))
    return out, infos, tags


# =========================================================================== meta
def bbox(pts, pad=0):
    pts = [q for q in pts if K.inb(*q)]
    if not pts:
        return None
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def attack(infos, tag, a, b, x_min=AX + 4, extra=None):
    rs = {}
    for k in range(a, b + 1):
        pts = set(infos[tag][k]["hit"]) | set(infos[tag][k].get("blade", ()))
        pts = {q for q in pts if q[0] >= x_min}
        r = bbox(pts)
        if extra:
            r = union_rect([r, extra])
        r[3] = H - r[1]
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def build_meta(who, infos):
    bb = infos["idle"][0]["bodybox"]
    hurt = [AX - 9, bb[1] + 6, 20, H - (bb[1] + 6)]
    tel = lambda tag, k: {"frame": k, "at": infos[tag][k]["glint"]}
    if who == "hael":
        meta = {"native": 1, "frame": [W, H], "anchor": [AX, H], "hurtbox": hurt,
                "attacks": {
                    "slash": {"windows": [attack(infos, "slash", 3, 4), attack(infos, "slash", 7, 8)]},
                    "slam": attack(infos, "slam", 5, 6),
                    "bash": attack(infos, "bash", 3, 5, extra=[56, 26, 16, 46]),
                    "plant": attack(infos, "plant", 3, 4, x_min=0),
                    "lunge": attack(infos, "lunge", 3, 4),
                    "leap": attack(infos, "leap", 7, 8),
                    "wave": attack(infos, "wave", 3, 4),
                    "launch": attack(infos, "launch", 2, 3),
                },
                "telegraph": {"slash": tel("slash", 2), "slam": tel("slam", 3), "bash": tel("bash", 1),
                              "plant": tel("plant", 2), "absorb": tel("absorb", 6), "lunge": tel("lunge", 2),
                              "leap": tel("leap", 5), "wave": tel("wave", 1), "launch": tel("launch", 1)},
                "spawn": {"slam": {"frame": 5, "at": [infos["slam"][5]["impact_x"], H - 1]},
                          "plant": {"frame": 3, "at": [infos["plant"][3]["impact_x"], H - 1]},
                          "leap": {"frame": 7, "at": [infos["leap"][7]["impact_x"], H - 1]},
                          "wave": {"frame": 4, "at": [infos["wave"][4]["impact_x"], H - 1]}},
                "notes": "Ser Hael (flame). slash = 2 windows (overhead cut, rising backhand); slam = overhead flame slam, "
                         "spawn.slam = blade impact on the floor (flame wave); bash = shield charge drawn in place (engine moves "
                         "him on frames 3-5); plant = enraged move, sword driven into the floor (spawn.plant). "
                         "absorb = phase-2 turn (kneel, element flows in, rise). twins_hael_p2 shares this meta."}
    else:
        meta = {"native": 1, "frame": [W, H], "anchor": [AX, H], "hurtbox": hurt,
                "attacks": {
                    "thrust": attack(infos, "thrust", 3, 4),
                    "combo": {"windows": [attack(infos, "combo", 2, 3), attack(infos, "combo", 6, 7)]},
                    "spikes": attack(infos, "spikes", 3, 4, x_min=0),
                    "charge": attack(infos, "charge", 3, 5, extra=[56, 26, 16, 46]),
                    "riposte": attack(infos, "riposte", 2, 3),
                },
                "telegraph": {"thrust": tel("thrust", 2), "combo": tel("combo", 1), "cast": tel("cast", 4),
                              "absorb": tel("absorb", 6), "volley": tel("volley", 3), "spikes": tel("spikes", 2),
                              "charge": tel("charge", 1), "counter": tel("counter", 1)},
                "spawn": {"cast": {"frame": 6, "at": [int(infos["cast"][4]["tip"][0]), int(infos["cast"][4]["tip"][1])]},
                          "spikes": {"frame": 3, "at": [infos["spikes"][3]["impact_x"], H - 1]},
                          "volley": {"frame": 4, "at": [int(infos["volley"][4]["tip"][0]), int(infos["volley"][4]["tip"][1])]}},
                "spawn_multi": {"volley": {str(k): [int(infos["volley"][k]["tip"][0]), int(infos["volley"][k]["tip"][1])] for k in (4, 6, 8)}},
                "notes": "Dame Rime (frost). thrust = lunging ice thrust (engine moves her on frames 3-4); combo = 2 quick "
                         "windows; cast = sword raised, frost gathers at the tip (spawn frame 6: engine spawns ice spikes / "
                         "lances); backstep drawn in place. twins_rime_p2 shares this meta."}
    return meta


# =========================================================================== previews
BG = (92, 92, 98, 255)


def preview_rows(tags, flats, path, scale=3):
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 12
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(230, 230, 230, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST),
                                  ((i - a) * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


def hitbox_preview(tags, flats, meta, path, scale=3):
    start = {t: (a, b) for t, a, b in tags}
    rows = [(t, d["windows"] if "windows" in d else [d]) for t, d in meta["attacks"].items() if t in start]
    for t in meta.get("telegraph", {}):
        if t in start and t not in [r[0] for r in rows]:
            rows.append((t, []))
    rows.append(("idle", []))
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), (40, 40, 46, 255))
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        dd.text((4, y0 + 4), t + "   " + "   ".join(f"active {w['active']} hit {w['hit']}" for w in wins),
                fill=(230, 230, 230, 255))
        tg = meta.get("telegraph", {}).get(t)
        spn = meta.get("spawn", {}).get(t)
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), BG)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rr = w.get("rects", {}).get(str(k), w["hit"])
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(rr, (255, 50, 50, 255), 2)
            if tg and tg["frame"] == k:
                x, y = tg["at"]
                d.ellipse([(x - 3) * scale, (y - 3) * scale, (x + 3) * scale, (y + 3) * scale], outline=(0, 255, 255, 255), width=2)
            if spn and spn["frame"] == k:
                x, y = spn["at"]
                d.line([((x - 3) * scale, y * scale), ((x + 3) * scale, y * scale)], fill=(255, 0, 255, 255), width=2)
                d.line([(x * scale, (y - 3) * scale), (x * scale, (y + 3) * scale)], fill=(255, 0, 255, 255), width=2)
            d.line([(ax * scale - 5, ay * scale - 2), (ax * scale + 5, ay * scale - 2)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


# =========================================================================== FX sheets
def _canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def fx_flamewave():
    """32x24, 4 loop, pivot bottom: a rolling wall of flame travelling RIGHT along the floor."""
    w, h = 32, 24
    frames = []
    K.setup(w, h)
    for i in range(4):
        FXB, FX = FXLayer("B"), FXLayer("F")
        crest = 21 + (i % 2)
        for k in range(9):
            x = 3 + k * 2.6 + hash01(k, i, 3) * 1.2
            u = x / crest if x <= crest else max(0.0, 1 - (x - crest) / 8.0)
            sz = 1.2 + 6.4 * (u ** 1.3) + hash01(k, i, 4) * 0.8
            if sz < 1.0:
                continue
            T.flame(FXB, (x - 0.5, h - 0.5), sz * 1.25, i * 3 + k, seed=k * 7, pal=T.FIRE_BACK)
            T.flame(FX, (x, h - 0.5), sz * 0.75, i * 3 + k, seed=k * 5 + 1, pal=T.FIRE)
        for x in range(0, crest + 4):
            if hash01(x, i, 9) < 0.8:
                FX.put([(x, h - 1)], "O4" if abs(x - crest) < 4 else "O3" if x > 8 else "O2")
        T.embers(FX, (crest - 10, 2, crest + 6, h - 12), 6, 40 + i)
        img = FXB.image()
        img.alpha_composite(FX.image())
        frames.append({"ms": 80, "cels": {"FX": img}})
    K.setup(W, H)
    return frames


def fx_lance(fire=False):
    """24x10, 4 loop: an ice lance (or a fire bolt) travelling RIGHT."""
    w, h = 24, 10
    K.setup(w, h)
    frames = []
    for i in range(4):
        FX = FXLayer("F")
        cy = 5
        for x in range(2, 23):
            t = (x - 2) / 20.0
            hw = 0.4 + 2.2 * (1 - abs(t - 0.62) / 0.62) ** 0.8 if t < 0.62 else 0.4 + 2.2 * max(0.0, (1 - t) / 0.38)
            for y in range(h):
                dy = y + .5 - cy
                if abs(dy) <= hw:
                    if dy < -hw * 0.25:
                        c = "N5" if x > 12 else "N4"
                    elif dy > hw * 0.35:
                        c = "N2"
                    else:
                        c = "N4" if x % 4 != i % 4 else "U4"
                    FX.put([(x, y)], c)
        FX.put([(22, cy), (21, cy)], "U4")
        for k in range(5):
            x = int(1 + hash01(k, i, 2) * 10)
            y = int(cy + (hash01(k, i, 3) - 0.5) * 7)
            FX.put([(x, y)], ("U3", "U2", "N4")[k % 3])
        frames.append({"ms": 60, "cels": {"FX": FX.image()}})
    K.setup(W, H)
    return frames


def fx_firebolt():
    w, h = 16, 16
    K.setup(w, h)
    frames = []
    for i in range(4):
        FXB, FX = FXLayer("B"), FXLayer("F")
        for k in range(4):
            T.flame(FXB, (6 - k * 1.5, 9 + (k % 2)), 3.0 - k * 0.5, i + k, seed=k * 3, pal=T.FIRE_BACK)
        for q in mask_disc((9.5, 8.0), 3.4, 3.0):
            d = math.hypot(q[0] + .5 - 9.5, q[1] + .5 - 8.0)
            FX.put([q], "Y3" if d < 1.4 else "Y2" if d < 2.3 else "O4")
        T.embers(FX, (0, 3, 8, 13), 4, 10 + i)
        img = FXB.image(); img.alpha_composite(FX.image())
        frames.append({"ms": 60, "cels": {"FX": img}})
    K.setup(W, H)
    return frames


def fx_clash():
    """48x48, 6: blades of fire and frost meeting -- a split star burst (ice left, fire right)."""
    w, h = 48, 48
    K.setup(w, h)
    frames = []
    for i in range(6):
        FX = FXLayer("F")
        c = (24, 24)
        R_ = [6, 13, 18, 21, 23, 24][i]
        for k in range(16):
            a = k * math.pi / 8 + 0.2
            ln = R_ * (1.0 if k % 2 == 0 else 0.55)
            cold = math.cos(a) < 0
            pal = ("U4", "U3", "U2", "U1") if cold else ("Y3", "Y2", "O4", "O2")
            pts = line(c, (c[0] + math.cos(a) * ln, c[1] + math.sin(a) * ln))
            for j, q in enumerate(pts):
                t = j / max(1, len(pts) - 1)
                if i >= 3 and t < (i - 2) * 0.25:
                    continue
                FX.put([q], pal[min(3, int(t * 4))])
        if i < 3:
            for q in mask_disc(c, 4 - i, 4 - i):
                FX.put([q], "Y3" if i < 2 else "U4")
        for k in range(10):
            a = hash01(k, i, 5) * 6.28
            r = R_ * (0.6 + 0.5 * hash01(k, i, 6))
            q = ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
            FX.put([q], "U3" if math.cos(a) < 0 else "O4")
        frames.append({"ms": (40, 50, 60, 70, 80, 90)[i], "cels": {"FX": FX.image()}})
    K.setup(W, H)
    return frames


def fx_nova():
    """128x72, 8, pivot bottom: a ring of frost and fire bursting outward along the ice (enraged survivor)."""
    w, h = 128, 72
    K.setup(w, h)
    frames = []
    for i in range(8):
        FXB, FX = FXLayer("B"), FXLayer("F")
        cx, cy = 64, 56
        r = [8, 18, 30, 42, 52, 58, 62, 64][i]
        th = [4, 6, 7, 7, 6, 5, 3, 2][i]
        for y in range(h):
            for x in range(w):
                dx, dy = (x + .5 - cx) / 1.0, (y + .5 - cy) / 0.55
                d = math.hypot(dx, dy)
                if r - th <= d <= r and y < h:
                    k = (r - d) / th
                    ang = math.atan2(dy, dx)
                    cold = (int((ang + math.pi) / (math.pi / 6)) % 2 == 0)
                    if i >= 5 and hash01(x, y, i) < (i - 4) * 0.25:
                        continue
                    pal = ("U4", "U3", "U2", "U1") if cold else ("Y3", "Y2", "O4", "O2")
                    FX.put([(x, y)], pal[min(3, int(k * 4))])
        # rising shards/flames on the floor line
        for k in range(12):
            a = k / 12 * 2 * math.pi
            x = cx + math.cos(a) * r
            if 2 < x < w - 2 and math.sin(a) > -0.2:
                if k % 2:
                    T.flame(FXB, (x, h - 1.5), 2.8 * (1 - i / 9), i + k, seed=k, pal=T.FIRE)
                else:
                    for j in range(int(9 * (1 - i / 9))):
                        FXB.put([(int(x), h - 2 - j)], "N4" if j % 3 else "U4")
                        if j < 4:
                            FXB.put([(int(x) + 1, h - 2 - j)], "N2")
        if i < 3:
            for q in mask_disc((cx, cy), 5 - i, 3 - i * 0.6):
                FX.put([q], "Y3" if i == 0 else "U4")
        img = FXB.image(); img.alpha_composite(FX.image())
        frames.append({"ms": (50, 50, 60, 60, 70, 80, 90, 110)[i], "cels": {"FX": img}})
    K.setup(W, H)
    return frames


def MRk():
    return MR


def fx_pillar():
    """24x72, 8, pivot bottom: warning glow -> a column of fire erupts -> collapses to embers."""
    w, h = 24, 72
    K.setup(w, h)
    frames = []
    for i in range(8):
        FXB, FX = FXLayer("B"), FXLayer("F")
        if i < 3:
            for dx in range(-5 - i * 2, 6 + i * 2):
                if hash01(dx, i, 3) < 0.7:
                    FX.put([(12 + dx, h - 1)], "O3" if abs(dx) < 3 else "O2" if abs(dx) < 6 else "O1")
            for k in range(3 + i * 2):
                FX.put([(int(12 + (hash01(k, i, 4) - 0.5) * 10), int(h - 2 - hash01(k, i, 5) * (4 + i * 4)))], ("O4", "O3")[k % 2])
        elif i < 6:
            hh = [44, 66, 60][i - 3]
            for k in range(8):
                y = h - 0.5 - k * hh / 8
                s = (4.2 - k * 0.25) * (1.0 if i < 5 else 0.8)
                T.flame(FXB, (12 + math.sin(k + i) * 0.8, y), s * 1.3, i + k, seed=k * 3, pal=T.FIRE_BACK)
                T.flame(FX, (12 + math.sin(k + i) * 0.6, y), s * 0.8, i + k, seed=k * 5 + 1, pal=T.FIRE)
            for y in range(int(h - hh), h):
                FX.put([(12, y)], "Y3" if i == 4 else "Y2")
        else:
            T.embers(FX, (4, h - 50 + (i - 6) * 16, 20, h - 2), 14 - (i - 6) * 5, 70 + i)
            for dx in range(-4, 5):
                FX.put([(12 + dx, h - 1)], "O2")
        img = FXB.image(); img.alpha_composite(FX.image())
        frames.append({"ms": (90, 90, 110, 60, 80, 110, 120, 140)[i], "cels": {"FX": img}})
    K.setup(W, H)
    return frames


def fx_xslash():
    """64x64, 6: the twins' crossing cut -- a fire stroke (top-left to bottom-right) over a frost stroke, meeting in a flash."""
    w, h = 64, 64
    K.setup(w, h)
    frames = []
    for i in range(6):
        FXB, FX = FXLayer("B"), FXLayer("F")
        grow = [0.35, 0.8, 1.0, 1.0, 1.0, 1.0][i]
        fade = [0.0, 0.0, 0.0, 0.25, 0.5, 0.75][i]
        for sgn, pal in ((1, ("Y3", "Y2", "O4", "O2")), (-1, ("U4", "U3", "U2", "U1"))):
            for t in range(-30, 31):
                u = t / 30.0
                if abs(u) > grow:
                    continue
                cx = 32 + t * 0.95
                cy = 32 + sgn * t * 0.95 + (1 - u * u) * 3.0 * -sgn
                thick = 2.6 * (1 - abs(u)) ** 0.6 + 0.4
                for d in range(-3, 4):
                    if abs(d) > thick:
                        continue
                    if fade and hash01(t, d, i) < fade + abs(u) * 0.3:
                        continue
                    q = ip((cx + d * 0.7 * sgn, cy - d * 0.7))
                    k = 0 if abs(d) < 0.8 and abs(u) < 0.6 else 1 if abs(d) < 1.6 else 2
                    (FX if k < 2 else FXB).put([q], pal[k + (1 if i >= 4 else 0)])
        if i < 3:
            for q in mask_disc((32, 32), 5 - i, 5 - i):
                FX.put([q], "Y3" if i < 2 else "U4")
        for k in range(10):
            a = hash01(k, i, 8) * 6.283
            r = 6 + i * 4 + hash01(k, i, 9) * 6
            FX.put([ip((32 + math.cos(a) * r, 32 + math.sin(a) * r))], "U3" if math.cos(a) < 0 else "O4")
        img = FXB.image(); img.alpha_composite(FX.image())
        frames.append({"ms": (40, 50, 70, 80, 80, 90)[i], "cels": {"FX": img}})
    K.setup(W, H)
    return frames


FXDEFS = [("fx_hf_xslash", 64, 64, "hf_xslash", fx_xslash), ("fx_hf_flamewave", 32, 24, "hf_flamewave", fx_flamewave), ("fx_hf_lance", 24, 10, "hf_lance", fx_lance),
          ("fx_hf_firebolt", 16, 16, "hf_firebolt", fx_firebolt), ("fx_hf_clash", 48, 48, "hf_clash", fx_clash),
          ("fx_hf_nova", 128, 72, "hf_nova", fx_nova), ("fx_hf_pillar", 24, 72, "hf_pillar", fx_pillar)]


def fx_preview(built, path, s=3):
    rows = []
    for name, w, h, tag, frames in built:
        rows.append((name, w, h, frames))
    tw = max(len(f) * (w + 2) for _, w, h, f in rows) * s
    th = sum((h + 12) for _, w, h, f in rows) * s
    sheet = Image.new("RGBA", (tw, th), (40, 40, 46, 255))
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, w, h, frames in rows:
        d.text((4, y + 2), name, fill=(230, 230, 230, 255))
        for i, f in enumerate(frames):
            fr = Image.new("RGBA", (w, h), (24, 28, 40, 255))
            for c in f["cels"].values():
                fr.alpha_composite(c)
            sheet.alpha_composite(fr.resize((w * s, h * s), Image.NEAREST), (i * (w + 2) * s, y + 12 * s))
        y += (h + 12) * s
    sheet.save(path)


# =========================================================================== main
def main():
    only = {}
    if "--only" in sys.argv:
        for part in sys.argv[sys.argv.index("--only") + 1].split(";"):
            who, tags = part.split(":")
            only[who] = tags.split(",")
    pv = os.path.join(ART, "previews")
    os.makedirs(pv, exist_ok=True)
    results = {}
    for who in ("hael", "rime"):
        if only and who not in only:
            continue
        out, infos, tags = render_twin(who, only.get(who))
        order = BODYL
        flats = {ph: [K.flatten(imgs, order) for _, imgs in out[ph]] for ph in (1, 2)}
        sfx = "_wip" if only else ""
        preview_rows(tags, flats[1], os.path.join(pv, f"twins_{who}{sfx}.png"))
        preview_rows(tags, flats[2], os.path.join(pv, f"twins_{who}_p2{sfx}.png"))
        results[who] = (out, infos, tags, flats)
        if only:
            continue
        meta = build_meta(who, infos)
        hitbox_preview(tags, flats[1], meta, os.path.join(pv, f"twins_{who}_hitbox.png"))
        with open(os.path.join(asebuild.ASSETS, f"twins_{who}_meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
        for t, d in meta["attacks"].items():
            for w in d.get("windows", [d]):
                print(who, "attack", t, w["active"], w["hit"])
        print(who, "hurtbox", meta["hurtbox"], "telegraph", meta["telegraph"], "spawn", meta["spawn"])
        if BUILD:
            asebuild.build(f"twins_{who}", W, H, BODYL, [{"ms": ms, "cels": imgs} for ms, imgs in out[1]], tags)
            asebuild.build(f"twins_{who}_p2", W, H, BODYL, [{"ms": ms, "cels": imgs} for ms, imgs in out[2]], tags)
    if "hael" in results and "rime" in results:
        c = Image.new("RGBA", (W * 4, H), BG)
        c.alpha_composite(results["hael"][3][1][0]); c.alpha_composite(results["hael"][3][2][0], (W, 0))
        c.alpha_composite(results["rime"][3][1][0], (2 * W, 0)); c.alpha_composite(results["rime"][3][2][0], (3 * W, 0))
        c.resize((W * 4 * 4, H * 4), Image.NEAREST).save(os.path.join(pv, "twins_closeup.png"))
    if not only or "fx" in only:
        built = []
        for name, w, h, tag, fn in FXDEFS:
            frames = fn()
            built.append((name, w, h, tag, frames))
            if BUILD and not only:
                asebuild.build(name, w, h, ["FX"], frames, [(tag, 0, len(frames) - 1)])
        fx_preview(built, os.path.join(pv, "fx_hf_twins.png"))


if __name__ == "__main__":
    main()
