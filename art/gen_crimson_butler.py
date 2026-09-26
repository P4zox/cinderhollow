#!/usr/bin/env python3
"""Mini-boss "The Butler" of the Crimson Manor (agent C).

    python3 art/gen_crimson_butler.py              full build: butler + butler_p2 (Aseprite) + butler_meta.json
    python3 art/gen_crimson_butler.py --preview    previews + meta only (no Aseprite)
    python3 art/gen_crimson_butler.py --only slash,thrust --preview     quick iteration (writes *_wip previews)

Outputs
    art/butler.aseprite, assets/butler.png/.json         phase 1
    art/butler_p2.aseprite, assets/butler_p2.png/.json   phase 2: same frames/tags/durations/body; coat-wings held
                                                         half-open and torn, eyes blazing, fresh blood on blade+cuffs
    assets/butler_meta.json                              shared by both sheets
    art/previews/butler.png, butler_p2.png, butler_hitbox.png, butler_p2_hitbox.png, butler_closeup.png

128x80 frames, faces RIGHT, feet on the bottom row, anchor [56, 80].  Rig: art/crimson_kit_butler.py.
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import crimson_kit as CK  # noqa: E402
import enemy_kit as K  # noqa: E402
import crimson_kit_butler as B  # noqa: E402
from crimson_kit_butler import P_, up, W, H, AX, FLOOR, LAYERS  # noqa: E402
from PIL import Image  # noqa: E402

K.setup(W, H)
BUILD = "--preview" not in sys.argv
PV = os.path.join(ART, "previews")
F_ = FLOOR


# =========================================================================== poses
def a_idle():
    fr = []
    for i in range(6):
        b = (0.0, 0.35, 0.7, 0.9, 0.7, 0.35)[i]
        fr.append((190, P_(P=(55.5, 50.5 + b * 0.3), C=(56.4, 33.2 + b * 0.8), Hd=(58.4, 24.6 + b * 0.9),
                           hf=(64.0, 51.5 + b * 0.4), wang=52 + b * 1.2)))
    return fr


def a_walk():
    """Measured stride: planted foot travels back linearly (3.5 px/frame), the other swings through."""
    fr = []
    A = 7.0
    for i in range(8):
        ph = i / 8.0
        feet = []
        for off in (0.0, 0.5):
            q = (ph + off) % 1.0
            if q < 0.5:                                   # stance: +A -> -A linearly
                x = A - 4 * A * q
                lift = 0.0
            else:                                         # swing: -A -> +A eased, lifted
                s = (q - 0.5) / 0.5
                x = -A + 2 * A * (s * s * (3 - 2 * s))
                lift = 3.2 * math.sin(math.pi * s)
            feet.append((x, lift))
        (xf, lf), (xb, lb) = feet
        bob = 0.9 * abs(math.cos(2 * math.pi * ph))
        sway = math.sin(2 * math.pi * ph)
        fr.append((115, P_(P=(55.8, 51.1 + bob * 0.5), C=(57.0, 33.8 + bob * 0.5),
                           Hd=(59.0, 25.2 + bob * 0.5), ff=(56.0 + xf, F_ - lf), fb=(56.0 + xb, F_ - lb),
                           hf=(64.4 + 0.6 * sway, 51.4), wang=54 + 2 * sway)))
    return fr


STAND = dict(P=(55.5, 50.5), C=(56.4, 33.2), Hd=(58.4, 24.6))


def a_slash():
    """Two precise cuts: a diagonal descending cut (f3) and a rising horizontal cut (f6)."""
    wind = dict(P=(54.6, 51.0), C=(54.4, 33.8), Hd=(55.9, 25.2), hup=(-0.12, -1), fb=(50.5, F_), ff=(62.0, F_))
    step = dict(P=(58.0, 51.8), C=(61.0, 34.8), Hd=(64.0, 26.6), hup=(0.28, -1), fb=(50.5, F_), ff=(67.5, F_))
    coil = dict(P=(57.4, 52.2), C=(59.0, 35.2), Hd=(61.6, 27.0), hup=(0.12, -1), fb=(50.5, F_), ff=(67.5, F_))
    rise = dict(P=(58.6, 51.4), C=(62.0, 34.2), Hd=(65.0, 26.0), hup=(0.3, -1), fb=(50.5, F_), ff=(67.5, F_))
    return [
        (110, P_(P=(55.2, 51.0), C=(55.9, 33.6), Hd=(57.8, 25.0), hf=(63.0, 42.0), wang=-38)),
        (140, P_(**wind, hf=(54.5, 20.0), wang=-146, wl="WeaponBack")),
        (270, P_(**dict(wind, C=(54.0, 34.0), Hd=(55.4, 25.5)), hf=(53.8, 19.4), wang=-152, wl="WeaponBack", eye=2,
                 brow=1, glint=(26.4, 4.8))),
        (60, P_(**step, hf=(74.0, 46.0), wang=36, wind=4,
                smear=dict(g0=(53.8, 19.4), a0=-152, mid=(68.0, 24.0), start=0.1))),
        (100, P_(**step, hf=(70.0, 55.0), wang=92, wind=2, smear=dict(g0=(74.0, 46.0), a0=36, u0=24, taper=0.4))),
        (110, P_(**coil, hf=(61.0, 57.0), wang=168)),
        (60, P_(**rise, hf=(76.0, 41.0), wang=-14, wind=4,
                smear=dict(g0=(61.0, 57.0), a0=168, mid=(70.0, 58.0), start=0.12))),
        (100, P_(**rise, hf=(71.0, 31.0), wang=-68, wind=2, smear=dict(g0=(76.0, 41.0), a0=-14, u0=24, taper=0.3))),
        (150, P_(P=(56.8, 51.0), C=(58.4, 33.8), Hd=(60.6, 25.4), hup=(0.15, -1), fb=(50.5, F_), ff=(65.0, F_ - 2.5),
                 hf=(66.0, 44.0), wang=-12)),
        (170, P_(**STAND, hf=(64.0, 51.0), wang=48)),
    ]


def a_thrust():
    """Fencing lunge: draw back, hold (glint), the front foot shoots forward, arm and blade fully extended."""
    gar = dict(P=(54.8, 51.6), C=(55.6, 34.4), Hd=(57.6, 25.8), fb=(50.0, F_), ff=(63.5, F_))
    back = dict(P=(52.6, 52.2), C=(52.4, 35.2), Hd=(54.0, 26.6), hup=(-0.05, -1), fb=(50.0, F_), ff=(63.5, F_))
    lunge = dict(P=(61.0, 57.0), C=(67.2, 41.4), Hd=(71.4, 33.4), hup=(0.4, -1), fb=(50.0, F_), ff=(80.0, F_))
    return [
        (110, P_(**gar, hf=(66.0, 42.0), wang=-4)),
        (130, P_(**back, hf=(59.0, 42.0), wang=-3)),
        (140, P_(**dict(back, P=(52.0, 52.6), C=(51.4, 35.6), Hd=(52.9, 27.0)), hf=(56.0, 41.6), wang=-2)),
        (290, P_(**dict(back, P=(51.8, 52.8), C=(51.0, 35.9), Hd=(52.5, 27.3)), hf=(55.5, 41.6), wang=-2, eye=2,
                 brow=1, glint=(86.5, 40.6))),
        (60, P_(P=(56.8, 52.6), C=(59.8, 35.6), Hd=(62.8, 27.4), hup=(0.2, -1), fb=(50.0, F_), ff=(71.0, F_ - 3.5),
                hf=(73.0, 45.0), wang=10, wind=3, thrust=dict(u0=8, u1=30, offs=(-2, 2)))),
        (80, P_(**lunge, hf=(81.0, 48.0), wang=17, wind=4, thrust=dict(u0=6, u1=34, offs=(-3, 3)))),
        (150, P_(**lunge, hf=(81.5, 48.3), wang=17, wind=2, thrust=dict(u0=14, u1=30, offs=(-2, 2), flash=31))),
        (150, P_(P=(57.4, 53.2), C=(60.8, 36.4), Hd=(63.6, 28.0), hup=(0.2, -1), fb=(50.0, F_), ff=(70.0, F_ - 3.0),
                 hf=(73.0, 46.0), wang=12)),
        (170, P_(**STAND, hf=(64.0, 51.0), wang=46)),
    ]


def a_serve():
    """The off hand leaves the small of his back, fans three silver knives, winds back and flicks them (f6)."""
    tw = dict(P=(55.0, 50.9), C=(54.2, 33.8), Hd=(55.6, 25.4), hup=(-0.18, -1))
    fw = dict(P=(56.6, 51.0), C=(59.0, 34.2), Hd=(61.8, 25.9), hup=(0.3, -1))
    return [
        (120, P_(**STAND, hb=(61.0, 40.0), knives=3)),
        (130, P_(**STAND, hb=(64.0, 33.0), knives=3)),
        (140, P_(**tw, hb=(46.0, 33.0), knives=3, hf=(63.4, 51.8))),
        (270, P_(**dict(tw, C=(54.6, 33.8), Hd=(56.3, 25.4)), hb=(44.5, 32.5), knives=3, hf=(63.2, 52.0), eye=2,
                 brow=1)),
        (60, P_(**fw, hb=(59.0, 30.5), knives=3, wind=2)),
        (60, P_(**fw, hb=(70.0, 34.0), knives=3, wind=3)),
        (110, P_(**fw, hb=(73.0, 37.0), flick=((73.0, 37.0), 4), wind=2)),
        (110, P_(**dict(fw, C=(57.4, 33.6), Hd=(59.8, 25.2)), hb=(69.0, 42.0))),
        (140, P_(**STAND, hb=(62.0, 45.0))),
        (160, P_(**STAND)),
    ]


def a_flourish():
    """The tailcoat opens into bat wings; he spins twice with the blade flat (f6 front, f7 back, f8 full ring)."""
    low = dict(P=(55.0, 52.4), C=(55.4, 35.4), Hd=(57.2, 26.8), hup=(0.02, -1), fb=(49.5, F_), ff=(63.0, F_))
    spin = dict(P=(56.0, 54.6), C=(57.8, 37.8), Hd=(60.0, 29.2), hup=(0.14, -1), fb=(48.5, F_), ff=(64.0, F_))
    ring_n = dict(c=(56.0, 57.0), rx=46.0, ry=7.0, w=6.0)
    return [
        (110, P_(**STAND, hf=(61.0, 41.0), wang=-164, wingB=0.25, wingF=0.2)),
        (120, P_(**low, hf=(55.0, 42.0), wang=-176, wingB=0.6, wingF=0.55, wl="WeaponBack")),
        (140, P_(**low, hf=(48.0, 44.0), wang=180, wingB=1.0, wingF=1.0, wl="WeaponBack")),
        (270, P_(**dict(low, C=(55.0, 35.6), Hd=(56.6, 27.0)), hf=(47.0, 44.5), wang=180, wingB=1.0, wingF=1.0,
                 wl="WeaponBack", eye=2, brow=1, glint=(16.5, 44.5))),
        (70, P_(**spin, hf=(46.0, 52.0), wang=176, wingB=1.0, wingF=1.0, wl="WeaponBack", wind=3)),
        (60, P_(**spin, face=-1, hf=(47.0, 55.0), wang=178, wingB=1.0, wingF=1.0, wl="WeaponBack", wind=4,
                flat=[dict(ring_n, th0=10, th1=-150, w=3.0, fade=0.6)])),
        (60, P_(**spin, hf=(70.0, 56.0), wang=4, wingB=1.0, wingF=1.0, wind=5,
                flat=[dict(ring_n, th0=200, th1=12)])),
        (60, P_(**spin, face=-1, hf=(70.0, 56.0), wang=4, wingB=1.0, wingF=1.0, wind=5,
                flat=[dict(ring_n, th0=-10, th1=-172, w=5.0), dict(ring_n, th0=178, th1=100, w=6.0)])),
        (80, P_(**spin, hf=(71.0, 57.0), wang=10, wingB=0.95, wingF=0.95, wind=4,
                flat=[dict(ring_n, th0=182, th1=14, w=6.0), dict(ring_n, th0=0, th1=-178, w=3.5, fade=0.4)])),
        (120, P_(**low, hf=(68.0, 50.0), wang=38, wingB=0.6, wingF=0.55)),
        (140, P_(**STAND, hf=(65.0, 51.0), wang=46, wingB=0.25, wingF=0.2)),
        (170, P_(**STAND)),
    ]


def vanish_post(s, seed, fi, center, eye):
    def f(imgs, ph):
        return B.bat_dissolve(imgs, s, seed, fi, center, keep_eye=eye, phase=ph)
    return f


def a_vanish():
    """f0-3: the body breaks into a swarm of bats (f3 nearly empty); the engine teleports him; f4-7 he re-forms."""
    base = dict(P=(55.3, 51.4), C=(55.8, 34.2), Hd=(57.8, 25.6), hup=(0.05, -1), hf=(63.5, 52.0), wang=56)
    cen = (56.0, 44.0)
    eye = (60, 25)
    fr = []
    for i, (ms, s, seed, w) in enumerate(((110, 0.07, 1, 0.8), (100, 0.36, 1, 0.95), (100, 0.7, 1, 1.0),
                                          (130, 0.97, 1, 1.0), (130, 0.9, 2, 1.0), (100, 0.62, 2, 0.95),
                                          (100, 0.3, 2, 0.7), (140, 0.04, 2, 0.3))):
        fr.append((ms, P_(**base, wingB=w, wingF=w * 0.95, eye=2 if i in (0, 7) else 1,
                          post=vanish_post(s, seed, i, cen, eye if 1 <= i <= 6 else None))))
    return fr


def a_backstep():
    ls = dict(fb=(50.5, F_), ff=(61.5, F_))
    return [
        (90, P_(P=(55.0, 53.6), C=(56.6, 36.4), Hd=(59.0, 27.8), hup=(0.15, -1), **ls, hf=(63.0, 53.0), wang=52)),
        (80, up(P_(P=(54.2, 51.6), C=(53.8, 34.4), Hd=(55.4, 25.9), hup=(-0.12, -1), fb=(49.5, F_), ff=(61.0, F_ - 2.5),
                   hf=(61.5, 50.0), wang=48, wingB=0.2, wingF=0.2, dust=1, wind=-3), 1)),
        (110, up(P_(P=(54.0, 51.0), C=(53.2, 34.0), Hd=(54.6, 25.6), hup=(-0.15, -1), fb=(49.0, F_ - 2.0),
                    ff=(59.5, F_ - 3.5), hf=(61.0, 48.5), wang=44, wingB=0.35, wingF=0.3, wind=-5), 5)),
        (100, up(P_(P=(54.4, 51.0), C=(54.2, 33.8), Hd=(56.0, 25.2), hup=(-0.05, -1), fb=(49.5, F_ - 0.5),
                    ff=(60.5, F_ - 2.0), hf=(62.0, 49.5), wang=48, wingB=0.25, wingF=0.2, wind=-3), 2)),
        (110, P_(P=(55.0, 54.0), C=(56.4, 36.8), Hd=(58.8, 28.2), hup=(0.12, -1), **ls, hf=(63.0, 53.5), wang=54,
                 dust=1)),
        (160, P_(**STAND, hf=(64.0, 51.5), wang=52, dust=2)),
    ]


def a_stagger():
    return [
        (90, P_(P=(54.6, 51.2), C=(53.2, 34.2), Hd=(53.6, 25.6), hup=(-0.4, -1), hf=(62.0, 45.0), wang=-58,
                hb=(44.0, 40.0), eye=2)),
        (130, P_(P=(55.0, 54.0), C=(57.0, 37.2), Hd=(60.0, 29.4), hup=(0.45, -1), hf=(62.5, 57.0), wang=82)),
        (240, P_(P=(55.0, 55.0), C=(57.6, 38.4), Hd=(61.0, 30.8), hup=(0.55, -1), hf=(63.0, 58.0), wang=84, eye=0)),
        (240, P_(P=(55.0, 54.6), C=(57.4, 38.0), Hd=(60.6, 30.2), hup=(0.5, -1), hf=(62.8, 57.6), wang=83)),
    ]


def kneel(P, C, Hd, **kw):
    """One knee down: the back knee on the floor behind, the back foot's toe planted further back; the front leg
    (IK) folds up in front.  Knee and foot are placed so both leg segments keep their exact length."""
    up_ = (C[0] - P[0], C[1] - P[1])
    hB = K.basis(P, up_)(-1.5, 0.8)
    L = B.LEG
    ky = F_ - 2.2
    kx = hB[0] - math.sqrt(max(0.0, L * L - (ky - hB[1]) ** 2))
    ay = F_ - 1.6
    ax = kx - math.sqrt(max(0.0, L * L - (ay - ky) ** 2))
    return P_(P=P, C=C, Hd=Hd, kb=(kx, ky), fb=(ax, F_), ff=(66.0, F_), **kw)


def death_post(s, seed, fi, eye, ash):
    def f(imgs, ph):
        names = [n for n in B.BODY_LAYERS if n != "Weapon"]
        out = B.bat_dissolve(imgs, s, seed, fi, (56.0, 58.0), keep_eye=eye, n_bats=22, spread=30, phase=ph,
                             names=names)
        if ash:
            fx = out["FX"].copy()
            px = fx.load()
            for x in range(40, 72):
                t = abs(x + .5 - 56) / 16.0
                hgt = int(ash * (1 - t * t) * 3.2 + K.hash01(x, 1, 5) * ash)
                for yy in range(hgt):
                    y = F_ - yy
                    if 0 <= y < H and px[x, y][3] == 0:
                        px[x, y] = K.RGBA[("a1", "a2", "a0", "b1")[(x + yy) % 4] if yy < hgt - 1 else "a3"]
            out["FX"] = fx
        return out
    return f


def a_death():
    plant = ((67.0, 56.0), 86)
    k1 = dict(P=(54.0, 62.0), C=(56.2, 45.0), Hd=(58.8, 36.4), hup=(0.2, -1))
    bow = dict(P=(54.0, 62.2), C=(59.4, 46.0), Hd=(65.8, 40.0), hup=(1.0, -1))
    fr = [
        (100, P_(P=(54.6, 51.2), C=(53.2, 34.2), Hd=(53.6, 25.6), hup=(-0.4, -1), hf=(62.0, 45.0), wang=-58,
                 hb=(44.0, 40.0), eye=2)),
        (160, P_(P=(55.0, 55.0), C=(57.0, 38.2), Hd=(60.0, 30.2), hup=(0.4, -1), hf=(64.0, 56.0), wang=84)),
        (180, kneel(**k1, hf=plant[0], wang=plant[1])),
        (260, kneel(**dict(k1, Hd=(59.2, 36.8), hup=(0.3, -1)), hf=plant[0], wang=plant[1], eye=1)),
        (300, kneel(**dict(bow, C=(57.6, 45.4), Hd=(62.4, 37.8), hup=(0.6, -1)), blade=False, blade_floor=plant,
                    hold_chest=True, eye=1)),
        (560, kneel(**bow, blade=False, blade_floor=plant, hold_chest=True, eye=1)),
    ]
    for k, (ms, s, ash) in enumerate(((140, 0.3, 0.0), (140, 0.55, 0.5), (160, 0.82, 1.0), (800, 0.995, 1.3))):
        fr.append((ms, kneel(**bow, blade=False, blade_floor=plant, hold_chest=True, eye=1, wingB=0.3 * s,
                             wingF=0.3 * s, post=death_post(s, 30, k, (68, 40) if s < 0.99 else None, ash))))
    return fr


TAGDEFS = [("idle", a_idle), ("walk", a_walk), ("slash", a_slash), ("thrust", a_thrust), ("serve", a_serve),
           ("flourish", a_flourish), ("vanish", a_vanish), ("backstep", a_backstep), ("stagger", a_stagger),
           ("death", a_death)]
COUNTS = dict(idle=6, walk=8, slash=10, thrust=9, serve=10, flourish=12, vanish=8, backstep=6, stagger=4, death=10)
LOOPS = ("idle", "walk")


def check_proportions():
    """Torso/neck/leg lengths must stay within tolerance in every frame (no proportion drift)."""
    bad = []
    for tag, fn in TAGDEFS:
        for k, (_, p) in enumerate(fn()):
            t = math.dist(p["P"], p["C"])
            n = math.dist(p["C"], p["Hd"])
            if abs(t - 17.3) > 1.0 or abs(n - 8.9) > 1.0:
                bad.append((tag, k, round(t, 1), round(n, 1)))
            up_ = (p["C"][0] - p["P"][0], p["C"][1] - p["P"][1])
            for a, ft in ((-1.5, p["fb"]), (1.3, p["ff"])):
                hip = K.basis(p["P"], up_)(a * p["face"], 0.8)
                d = math.dist(hip, (ft[0], ft[1] - 1.6))
                if d > 2 * B.LEG + 0.3:
                    bad.append((tag, k, "leg overstretched", round(d, 1)))
    for b in bad:
        print("PROPORTION", b)
    return bad


def build_meta(infos):
    idle = infos["idle"][0]
    tb = CK.bbox(idle["torso"] | idle["head"])
    hurt = [tb[0] - 1, tb[1], tb[2] + 2, H - tb[1]]
    A = CK.attack_rect
    slash = [A(infos, "slash", 3, 3, x_min=AX + 2), A(infos, "slash", 6, 6, x_min=AX + 2)]
    thrust = A(infos, "thrust", 5, 6, x_min=AX + 4)
    for r in list(thrust["rects"].values()) + [thrust["hit"]]:       # the extended arm is part of the lunge
        r[2] += r[0] - (AX + 14)
        r[0] = AX + 14
    flourish = A(infos, "flourish", 6, 8)
    serve_at = CK.pt(infos["serve"][6]["hb"])
    return {
        "native": 1,
        "frame": [W, H],
        "anchor": [AX, H],
        "hurtbox": hurt,
        "attacks": {
            "slash": {"windows": slash},
            "thrust": thrust,
            "flourish": flourish,
        },
        "spawn": {
            "serve": {"frame": 6, "at": serve_at, "dirs_deg": [-5, 4, 13]},
        },
        "telegraph": {
            "slash": {"frame": 2, "at": CK.pt(infos["slash"][2]["tip"])},
            "thrust": {"frame": 3, "at": CK.pt(infos["thrust"][3]["tip"])},
            "flourish": {"frame": 3, "at": CK.pt(infos["flourish"][3]["tip"])},
            "serve": {"frame": 3, "at": CK.pt(infos["serve"][3]["hb"])},
        },
        "notes": "The Butler (mini-boss). Faces right, anchor = feet (x 56). 'hit' = union of the per-frame 'rects' over "
                 "the inclusive active range (each reaches the floor). slash: two windows (descending diagonal f3, "
                 "rising cut f6). thrust: fencing lunge drawn in place, the front foot lands ~24px ahead of the anchor "
                 "(the engine may slide him forward ~12-20px over f4-f5). flourish: coat-wings open (f1-3, hold f3), "
                 "he spins twice (mirrored frames 5 and 7): the hit covers BOTH sides of him on f6-f8. serve: three "
                 "silver knives released from the off hand on f6 at spawn.at, fanned at dirs_deg (0 = straight ahead, "
                 "+ = downward). vanish: f0-3 the body breaks into bats (f3 nearly empty) -> teleport between f3 and f4 "
                 "-> f4-7 re-forms; he should be intangible on f2-f5. backstep drawn in place (airborne f1-3; move him "
                 "back ~24px). walk: planted foot travels 3.5px per frame (115ms) = ~30 px/s; move him at that speed "
                 "so the feet do not slide. death: kneels (f2), last bow (f4-5), dissolves into bats and ash (f6-9); "
                 "the serving blade stays planted in the floor on the last frame. butler_p2 shares this meta "
                 "(identical frames/poses: coat-wings half-open and torn, eyes blazing, blood on blade and cuffs).",
    }


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    check_proportions()
    out, infos, tags = CK.run_anims(LAYERS, B.draw, TAGDEFS, COUNTS, loops=LOOPS, phases=(1, 2), only=only)
    flats = {ph: [K.flatten(imgs, LAYERS) for _, imgs in out[ph]] for ph in (1, 2)}
    sfx = "_wip" if only or len(TAGDEFS) < len(COUNTS) else ""
    CK.preview_rows(os.path.join(PV, f"butler{sfx}.png"), tags, flats[1])
    CK.preview_rows(os.path.join(PV, f"butler_p2{sfx}.png"), tags, flats[2])
    CK.closeup(os.path.join(PV, f"butler_closeup{sfx}.png"), flats[1][:1] + flats[2][:1], [0, 1], scale=5)
    if only:
        return
    meta = build_meta(infos)
    CK.hitbox_preview(os.path.join(PV, "butler_hitbox.png"), tags, flats[1], meta)
    CK.hitbox_preview(os.path.join(PV, "butler_p2_hitbox.png"), tags, flats[2], meta)
    CK.write_meta("butler", meta)
    for t, d in meta["attacks"].items():
        for w in d.get("windows", [d]):
            print("attack", t, w["active"], w["hit"])
    print("hurtbox", meta["hurtbox"], "spawn", meta["spawn"], "telegraph", meta["telegraph"])
    if BUILD:
        for ph, name in ((1, "butler"), (2, "butler_p2")):
            frames = [{"ms": ms, "cels": imgs} for ms, imgs in out[ph]]
            asebuild.build(name, W, H, LAYERS, frames, tags)
            print("built", name)


if __name__ == "__main__":
    main()
