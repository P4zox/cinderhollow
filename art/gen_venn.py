#!/usr/bin/env python3
"""Sister Venn, the Last Kindling -- secret final boss (agent V).

    python3 art/gen_venn.py                 full build (Aseprite): all sheets + fx + meta + previews
    python3 art/gen_venn.py --preview       previews only (no Aseprite)
    python3 art/gen_venn.py --only idle,sweep --preview   quick iteration on some tags

Outputs (per-tag sheets so every strip stays <= 4096 px):
    assets/venn_boss_<tag>.png/.json       phase 1 (veiled, halo, flame scythe)
    assets/venn_boss_p2_<tag>.png/.json    phase 2 (veil burned away, glowing eyes, wings of burning roots)
    assets/venn_boss_p3_<tag>.png/.json    phase 3 (the halo breaks; desperate)
    assets/venn_boss_meta.json             anchor / hurtbox / per-frame hit rects / spawn points / sheet map
    assets/fx_vn_*.png/.json               pillar, crescent wave, root lance, flare ring, impact
    art/previews/venn_*.png
Rig: art/venn_rig.py.  Faces RIGHT; anchor (96, 122) = hem on the floor line.
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import venn_rig as R  # noqa: E402
import asebuild  # noqa: E402
from venn_rig import P_, W, H, AX, AY, FLOOR  # noqa: E402

PREVIEW = "--preview" in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
PV = os.path.join(ART, "previews")
os.makedirs(PV, exist_ok=True)


def SC(g, ang, s, fo=None, bs=1, front=True, **kw):
    d = dict(g=g, ang=ang, s=s, fo=fo, bs=bs, front=front)
    d.update(kw)
    return d


# =========================================================================== secondary motion (cloth phase + hem lag)
def secondary(frames, loop, period_ms=1200):
    res = []
    n = len(frames)
    tacc = 0
    for i, (ms, p) in enumerate(frames):
        ph = 2 * math.pi * i / n if loop else 2 * math.pi * tacc / period_ms
        tacc += ms
        res.append({"ph": ph})
    return res


# =========================================================================== poses
IDLE_SC = lambda a=0.0: SC((108.5, 81.5 + a), -78, 34, bs=1)


def anim_idle():
    fr = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        b = -0.8 * math.sin(a)
        fr.append((150, P_(bob=round(b), head=(0, 0), hf=(93, 89.5 + round(b)), wind=-0.8,
                           scy=IDLE_SC(round(b * 0.6)), halo=1.0 + 0.1 * math.sin(a),
                           wl=(264 + 3 * math.sin(a - 0.8), 1.0, 0.9), wr=(-84 - 3 * math.sin(a - 0.8), 1.0, 0.75))))
    return fr


def anim_glide():
    fr = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        fr.append((105, P_(bob=round(-0.8 * math.sin(2 * a)), lean=6, wind=-6 + 1.2 * math.sin(a), stride=math.sin(a),
                           scy=SC((98.5, 91.0), 196, 22, bs=-1), hf=(90, 88), hf_dir=160,
                           wl=(250 + 4 * math.sin(a), 0.8, 0.9), wr=(-70 - 4 * math.sin(a), 0.8, 0.7))))
    return fr



def seq(K, base=None, **common):
    """K: list of (ms, dict) -> frames; each dict overrides NEUTRAL (+ common)."""
    out = []
    for ms, kw in K:
        d = dict(common); d.update(kw)
        out.append((ms, P_(**d)))
    return out


WIND_UP = dict(wl=(274, 0.9, 0.95), wr=(-94, 0.9, 0.8))
WIND_OUT = dict(wl=(236, 1.15, 1.0), wr=(-58, 1.1, 0.85))


def anim_sweep():
    # a wide overhead-to-low arc in front of her: the head of the scythe travels clockwise
    K = [
        (110, dict(lean=-3, bob=-1, scy=SC((104, 71), -128, 30), hf=(92, 86), wind=1, **WIND_UP)),
        (110, dict(lean=-6, bob=-2, scy=SC((101, 70), -158, 27), hf=(90, 84), wind=2, head=(-0.5, 0), **WIND_UP)),
        (190, dict(lean=-7, bob=-2, scy=SC((100, 70), -168, 26), hf=(90, 84), wind=2, head=(-0.5, 0), eyes=0.5, **WIND_UP)),
        (55, dict(lean=4, bob=0, scy=SC((110, 72), -62, 30), hf=(97, 80), wind=-4, fx=(("smear",),), **WIND_OUT)),
        (70, dict(lean=8, bob=1, scy=SC((114, 80), 14, 34), hf=(100, 83), wind=-6, stride=0.8, fx=(("smear",), ("dust", 150, 1.0)), **WIND_OUT)),
        (110, dict(lean=8, bob=1, scy=SC((112, 84), 44, 34), hf=(100, 86), wind=-5, stride=0.8, fx=(("smear",),), **WIND_OUT)),
        (130, dict(lean=5, bob=1, scy=SC((111, 84), 52, 32), hf=(98, 88), wind=-3, stride=0.5)),
        (140, dict(lean=2, bob=0, scy=SC((110, 82), 10, 30), hf=(95, 89), wind=-1)),
        (140, dict(lean=0, bob=0, scy=SC((109, 81), -50, 32), hf=(93, 89), wind=-1)),
        (150, dict(lean=0, bob=0, scy=IDLE_SC(), hf=(93, 89.5), wind=-0.8)),
    ]
    return seq(K)


def anim_reap():
    # forward cut, then the blade keeps travelling round and reaps low behind her
    K = [
        (100, dict(lean=-3, bob=-1, scy=SC((104, 71), -128, 30), hf=(92, 86), **WIND_UP)),
        (170, dict(lean=-6, bob=-2, scy=SC((100, 70), -165, 26), hf=(90, 84), head=(-0.5, 0), **WIND_UP)),
        (55, dict(lean=4, scy=SC((110, 72), -62, 30), hf=(97, 80), wind=-4, fx=(("smear",),), **WIND_OUT)),
        (70, dict(lean=8, bob=1, scy=SC((114, 80), 14, 34), hf=(100, 83), wind=-6, stride=0.8, fx=(("smear",),), **WIND_OUT)),
        (80, dict(lean=6, bob=1, scy=SC((110, 86), 62, 36), hf=(99, 88), wind=-4, stride=0.6, fx=(("smear",),), **WIND_OUT)),
        (120, dict(lean=2, bob=2, crouch=0.12, scy=SC((104, 88), 92, 38), hf=(96, 90), wind=-2, **WIND_OUT)),
        (55, dict(lean=-4, bob=2, crouch=0.15, scy=SC((96, 88), 150, 30), hf=(92, 89), wind=3, fx=(("smear",),), **WIND_UP)),
        (70, dict(lean=-7, bob=1, crouch=0.1, scy=SC((92, 86), 190, 26), hf=(90, 88), wind=5, fx=(("smear",), ("dust", 50, 1.0)), **WIND_UP)),
        (110, dict(lean=-6, bob=1, scy=SC((93, 82), 220, 24), hf=(90, 86), wind=4, fx=(("smear",),))),
        (140, dict(lean=-3, bob=0, scy=SC((98, 78), 250, 26), hf=(92, 88), wind=2)),
        (140, dict(lean=0, scy=SC((106, 80), -75, 32), hf=(93, 89), wind=0)),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5), wind=-0.8)),
    ]
    return seq(K)


def anim_rising():
    # low guard, then an upward arc that throws a crescent of flame along the floor
    K = [
        (110, dict(lean=6, crouch=0.2, scy=SC((110, 88), 22, 40, bs=-1), hf=(98, 86))),
        (120, dict(lean=10, crouch=0.35, scy=SC((112, 92), 34, 42, bs=-1), hf=(100, 90), eyes=0.5)),
        (200, dict(lean=11, crouch=0.38, scy=SC((112, 93), 38, 42, bs=-1), hf=(100, 91), eyes=0.6, fire=1)),
        (55, dict(lean=2, crouch=0.15, scy=SC((113, 82), -22, 36, bs=-1), hf=(100, 84), wind=-3, fx=(("smear",),))),
        (70, dict(lean=-6, crouch=0.0, bob=-2, scy=SC((108, 68), -88, 30, bs=-1), hf=(98, 72), wind=-2, fx=(("smear",),))),
        (110, dict(lean=-8, bob=-2, scy=SC((104, 64), -130, 26, bs=-1), hf=(96, 70), wind=0, fx=(("smear",),))),
        (140, dict(lean=-5, bob=-1, scy=SC((104, 68), -120, 28, bs=-1), hf=(94, 80))),
        (140, dict(lean=-2, scy=SC((106, 74), -95, 32), hf=(93, 86))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


PLANT = lambda y=84, x=91.5: SC((x, y), -86, 30 - max(0, y - 90.5), hand="f", front=False)


def anim_heal():
    # she kneels, props the scythe, and drinks from the flask of light she once gave you
    K = [
        (120, dict(crouch=0.15, scy=PLANT(86), hn=(104, 90))),
        (130, dict(crouch=0.35, scy=PLANT(90), hn=(104, 94))),
        (130, dict(crouch=0.5, scy=PLANT(94), hn=(105, 96), flask="hand", flask_k=0.4)),
        (140, dict(crouch=0.55, scy=PLANT(95), hn=(107, 90), hn_dir=-60, flask="hand", flask_k=0.6)),
        (140, dict(crouch=0.55, scy=PLANT(95), hn=(106, 84), hn_dir=-70, flask="hand", flask_k=0.8, head=(0, -0.5))),
        (160, dict(crouch=0.55, scy=PLANT(95), hn=(104.5, 80.5), hn_dir=-100, flask="hand", flask_k=1.0, head=(-0.5, -1), htilt=-8)),
        (160, dict(crouch=0.55, scy=PLANT(95), hn=(104.5, 80), hn_dir=-110, flask="hand", flask_k=1.0, head=(-0.5, -1), fx=(("glowheart", 0.5),))),
        (160, dict(crouch=0.55, scy=PLANT(95), hn=(104.5, 80), hn_dir=-110, flask="hand", flask_k=0.5, head=(-0.5, -1), fx=(("glowheart", 1.0),))),
        (120, dict(crouch=0.55, scy=PLANT(95), hn=(105, 86), hn_dir=-40, flask="hand", flask_k=0.1, fx=(("healburst", 0.5), ("glowheart", 1.0)))),
        (120, dict(crouch=0.5, scy=PLANT(94), hn=(106, 90), fx=(("healburst", 1.0),), halo=1.3)),
        (130, dict(crouch=0.35, scy=PLANT(90), hn=(105, 92), halo=1.2)),
        (130, dict(crouch=0.15, scy=PLANT(86), hn=(104, 91))),
        (140, dict(scy=SC((106, 80), -80, 33), hf=(93, 89))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


def anim_cast():
    # the scythe planted in her far hand, the near palm raised: shrine-light gathers and is released
    K = [
        (120, dict(scy=PLANT(84), hn=(106, 86))),
        (120, dict(scy=PLANT(83), hn=(110, 76), hn_dir=-70, bob=-1)),
        (120, dict(scy=PLANT(82), hn=(110, 67), hn_dir=-85, bob=-2, head=(0, -0.5), fx=(("orb", 1.5),))),
        (110, dict(scy=PLANT(82), hn=(110, 64), hn_dir=-88, bob=-2, head=(0, -1), fx=(("orb", 2.5), ("gather", 22, 0.3)), halo=1.2)),
        (110, dict(scy=PLANT(82), hn=(110, 64), hn_dir=-88, bob=-2, head=(0, -1), fx=(("orb", 3.5), ("gather", 20, 0.6)), halo=1.3)),
        (160, dict(scy=PLANT(82), hn=(110, 63), hn_dir=-88, bob=-2, head=(0, -1), fx=(("orb", 4.5), ("gather", 18, 0.9)), halo=1.4, eyes=0.6)),
        (70, dict(scy=PLANT(83), hn=(111, 62), hn_dir=-88, bob=-3, head=(0, -1), fx=(("orb", 6.0), ("flash", 8)), halo=1.5)),
        (120, dict(scy=PLANT(83), hn=(111, 66), hn_dir=-80, bob=-2, fx=(("orb", 2.5),), halo=1.2)),
        (130, dict(scy=PLANT(84), hn=(108, 78), hn_dir=-30, bob=-1)),
        (130, dict(scy=SC((106, 80), -80, 33), hf=(93, 89))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


def anim_stagger():
    K = [
        (90, dict(lean=-10, bob=1, head=(-1, 1), scy=SC((100, 86), 150, 30), hf=(88, 86), wind=4, eyes=0)),
        (110, dict(lean=-8, bob=3, crouch=0.15, head=(0, 1.5), scy=SC((101, 90), 160, 28), hf=(89, 90), wind=3)),
        (160, dict(lean=4, bob=3, crouch=0.28, head=(0.5, 2), scy=SC((103, 94), 170, 26), hf=(92, 94), wind=1)),
        (200, dict(lean=6, bob=3, crouch=0.3, head=(0.5, 2), scy=SC((103, 95), 172, 26), hf=(92, 95), wind=0)),
        (160, dict(lean=3, bob=2, crouch=0.2, head=(0, 1), scy=SC((104, 90), 190, 26), hf=(92, 92))),
        (150, dict(lean=0, bob=0, scy=SC((106, 82), -85, 32), hf=(93, 89))),
    ]
    return seq(K)


def anim_summon():
    # intro: the pilgrim's ash hood burns off, the halo lights, the scythe is drawn out of white fire
    K = []
    for i in range(12):
        t = i / 11
        vis = max(0.0, min(1.0, (i - 3) / 6))
        hood = max(0.0, 1 - i / 4)
        K.append((130 if i < 11 else 200, dict(
            hood=hood, halo=max(0.0, min(1.0, (i - 2) / 4)), veil=max(0.02, min(1.0, (i - 1) / 5)), keepveil=True,
            scy=SC((110 - 2 * (1 - vis), 84 - 2 * vis), -78 + 30 * (1 - vis), 34, vis=vis) if vis > 0 else None,
            hn=(111, 88), hn_dir=10, hf=(93, 89.5), head=(0, 1 - t), fx=(("gather", 16, t),) if 3 <= i <= 8 else ())))
    return seq(K)


def anim_lance():
    # the wings fold back, then three burning roots spear forward over her shoulder
    K = [
        (120, dict(lean=-3, scy=SC((106, 82), -70, 33), hf=(92, 86), wl=(262, 0.7, 0.95), wr=(-80, 0.7, 0.8))),
        (130, dict(lean=-6, bob=-1, scy=SC((104, 84), -60, 34), hf=(90, 84), wl=(282, 0.55, 0.9), wr=(-100, 0.55, 0.75), eyes=1)),
        (200, dict(lean=-7, bob=-1, scy=SC((104, 84), -60, 34), hf=(90, 84), wl=(288, 0.5, 0.9), wr=(-104, 0.5, 0.72), fire=1)),
        (50, dict(lean=5, scy=SC((108, 83), -40, 34), hf=(98, 82), wl=(250, 0.6, 0.9), wr=(-66, 0.6, 0.75), lances=0.35)),
        (60, dict(lean=8, scy=SC((109, 84), -30, 34), hf=(100, 82), wl=(236, 0.7, 0.9), wr=(-56, 0.7, 0.75), lances=0.8, stride=0.6)),
        (130, dict(lean=8, scy=SC((109, 84), -30, 34), hf=(100, 82), wl=(234, 0.7, 0.9), wr=(-54, 0.7, 0.75), lances=1.0, stride=0.6)),
        (110, dict(lean=6, scy=SC((109, 84), -34, 34), hf=(98, 84), wl=(236, 0.8, 0.9), wr=(-56, 0.8, 0.75), lances=0.6)),
        (100, dict(lean=3, scy=SC((108, 83), -50, 34), hf=(95, 86), lances=0.2)),
        (140, dict(lean=1, scy=SC((108, 82), -70, 33), hf=(93, 88))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


def anim_absorb():
    # she raises the scythe over her head and drinks the dying Root; frames 4-9 loop while she channels
    K = [
        (120, dict(scy=SC((106, 76), -90, 30), hf=(94, 82), head=(0, -0.5))),
        (120, dict(bob=-1, scy=SC((105, 66), -92, 26, fo=-7), head=(-0.5, -1), wl=(250, 1.2, 1.0), wr=(-70, 1.2, 0.85))),
        (130, dict(bob=-2, scy=SC((104, 58), -94, 22, fo=-8), head=(-1, -1.5), htilt=-10, wl=(240, 1.35, 1.05), wr=(-60, 1.3, 0.9))),
        (130, dict(bob=-2, scy=SC((104, 57), -94, 22, fo=-8), head=(-1, -1.5), wl=(236, 1.45, 1.08), wr=(-56, 1.4, 0.92), fire=1, fx=(("glowheart", 0.4),))),
    ]
    for i in range(6):
        a = 2 * math.pi * i / 6
        K.append((110, dict(bob=-2 + round(0.6 * math.sin(a)), scy=SC((104, 57 + round(0.6 * math.sin(a))), -94, 22, fo=-8), head=(-1, -1.5),
                            wl=(236 + 3 * math.sin(a), 1.45, 1.08), wr=(-56 - 3 * math.sin(a), 1.4, 0.92), fire=1.5,
                            fx=(("glowheart", 0.6 + 0.3 * math.sin(a)),), wind=math.sin(a))))
    K += [
        (120, dict(bob=-1, scy=SC((105, 66), -92, 26, fo=-7), head=(-0.5, -1), wl=(246, 1.2, 1.0), wr=(-66, 1.2, 0.85), fx=(("healburst", 0.6),))),
        (130, dict(scy=SC((106, 76), -88, 30), hf=(94, 84), fx=(("healburst", 1.0),))),
        (130, dict(scy=SC((107, 80), -80, 32), hf=(93, 88))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


def anim_dive():
    # crouch, one great wingbeat up (the engine lifts her), hover with the scythe overhead, plunge, land
    K = [
        (110, dict(crouch=0.2, lean=4, scy=SC((106, 84), -60, 34), hf=(94, 86), wl=(284, 0.8, 1.0), wr=(-104, 0.8, 0.85))),
        (130, dict(crouch=0.35, lean=6, scy=SC((106, 88), -50, 34), hf=(95, 90), wl=(294, 0.7, 1.05), wr=(-112, 0.7, 0.9), eyes=1)),
        (80, dict(crouch=0.0, bob=-2, lean=-2, scy=SC((104, 80), -80, 30), hf=(94, 82), wl=(214, 1.1, 1.05), wr=(-36, 1.1, 0.9), wind=4, lift=4)),
        (90, dict(bob=-2, lean=-4, scy=SC((104, 76), -90, 28), hf=(93, 80), wl=(196, 1.2, 1.0), wr=(-20, 1.2, 0.88), wind=5, lift=5)),
        (110, dict(bob=-2, lean=-6, scy=SC((102, 66), -150, 26), hf=(92, 72), wl=(250, 1.0, 1.0), wr=(-70, 1.0, 0.85), wind=3, lift=4)),
        (110, dict(bob=-3, lean=-8, scy=SC((101, 64), -165, 26), hf=(92, 70), wl=(276, 0.9, 1.0), wr=(-96, 0.9, 0.85), wind=2, lift=3, eyes=1)),
        (130, dict(bob=-3, lean=-8, scy=SC((101, 64), -168, 26), hf=(92, 70), wl=(262, 1.0, 1.0), wr=(-82, 1.0, 0.85), wind=2, lift=3, fire=1)),
        (50, dict(bob=-1, lean=6, scy=SC((110, 72), -70, 30), hf=(98, 76), wl=(230, 1.1, 1.0), wr=(-50, 1.1, 0.85), wind=-4, lift=-2, fx=(("smear",),))),
        (60, dict(bob=0, lean=12, scy=SC((114, 82), 30, 34), hf=(101, 84), wl=(216, 1.2, 1.0), wr=(-40, 1.2, 0.85), wind=-6, lift=-4, fx=(("smear",),))),
        (90, dict(crouch=0.4, lean=14, scy=SC((114, 92), 62, 32), hf=(102, 92), wl=(210, 1.25, 1.0), wr=(-34, 1.2, 0.85), wind=-4, fx=(("smear",), ("dust", 130, 2.0)))),
        (160, dict(crouch=0.42, lean=12, scy=SC((113, 93), 66, 30), hf=(102, 93), wl=(222, 1.1, 1.0), wr=(-44, 1.1, 0.85), fx=(("dust", 120, 2.5),))),
        (140, dict(crouch=0.25, lean=6, scy=SC((110, 88), 20, 32), hf=(98, 90))),
        (140, dict(crouch=0.05, lean=2, scy=SC((108, 82), -60, 33), hf=(94, 89))),
        (150, dict(scy=IDLE_SC(), hf=(93, 89.5))),
    ]
    return seq(K)


def anim_transform():
    # phase 2: the veil catches and burns away, her eyes open white-gold, burning roots tear out of her back
    K = []
    for i in range(14):
        t = i / 13
        veil = max(0.0, 1 - max(0, i - 2) / 6)
        ws = max(0.0, min(1.0, (i - 5) / 6))
        K.append((150 if i not in (9, 10) else 110, dict(
            keepveil=True, veil=veil, eyes=1.0 if i >= 4 else 0.0, head=(-0.4 * min(1, i / 5), -1.2 * min(1, i / 5)), htilt=-6,
            scy=SC((106, 80 - 2 * min(1, i / 5)), -84, 32), hf=(94 - 2 * ws, 86 - 4 * ws),
            wings=False if ws <= 0 else None, wl=(250 - 12 * ws, 0.5 + 0.7 * ws, 0.2 + 0.85 * ws), wr=(-70 + 12 * ws, 0.5 + 0.7 * ws, 0.2 + 0.7 * ws),
            fire=2 * ws, halo=1.0 + 0.4 * ws, wind=2 * math.sin(i))))
    return seq(K)


# ---------------------------------------------------------------- phase 3: fast, near silent
def anim_blink():
    # into white fire (0-4) and out again (5-9) -- the engine moves her while she is gone
    K = []
    for i in range(10):
        d = min(1.0, i / 4) if i < 5 else max(0.0, 1 - (i - 5) / 4)
        K.append((60, dict(dissolve=d * 1.05, lean=4, scy=SC((106, 84), -60, 34), hf=(94, 86), wl=(250, 0.9, 1.0), wr=(-70, 0.9, 0.85))))
    return seq(K)


def anim_flurry():
    # three desperate cuts: forward, back-hand, and a falling overhead
    K = [
        (70, dict(lean=-4, scy=SC((102, 70), -150, 27), hf=(91, 84), **WIND_UP)),
        (45, dict(lean=6, scy=SC((112, 76), -40, 32), hf=(98, 80), fx=(("smear",),), **WIND_OUT)),
        (55, dict(lean=9, bob=1, scy=SC((114, 82), 24, 34), hf=(100, 84), stride=0.8, fx=(("smear",),), **WIND_OUT)),
        (80, dict(lean=8, bob=1, scy=SC((113, 86), 50, 34), hf=(100, 88), stride=0.8)),
        (45, dict(lean=6, bob=1, scy=SC((112, 84), 40, 34, bs=-1), hf=(100, 86), stride=0.6)),
        (45, dict(lean=2, scy=SC((110, 74), -30, 32, bs=-1), hf=(99, 78), fx=(("smear",),), **WIND_OUT)),
        (55, dict(lean=-4, bob=-1, scy=SC((106, 66), -100, 28, bs=-1), hf=(97, 72), fx=(("smear",),), **WIND_UP)),
        (70, dict(lean=-8, bob=-2, scy=SC((102, 64), -150, 26, bs=-1), hf=(94, 70), **WIND_UP)),
        (90, dict(lean=-9, bob=-2, scy=SC((101, 64), -168, 26), hf=(92, 70), eyes=1, fire=1, **WIND_UP)),
        (45, dict(lean=6, scy=SC((110, 70), -70, 30), hf=(98, 74), fx=(("smear",),), **WIND_OUT)),
        (55, dict(lean=14, crouch=0.3, scy=SC((114, 86), 40, 34), hf=(102, 88), fx=(("smear",), ("dust", 140, 2.0)), **WIND_OUT)),
        (150, dict(lean=12, crouch=0.35, scy=SC((113, 92), 64, 30), hf=(102, 92), fx=(("dust", 130, 2.5),))),
        (120, dict(lean=5, crouch=0.15, scy=SC((110, 86), 10, 32), hf=(97, 88))),
        (120, dict(lean=1, scy=SC((108, 82), -60, 33), hf=(94, 89))),
    ]
    return seq(K)


def anim_slam():
    # a leap (the engine carries her) and a two-handed overhead slam that splits the floor both ways
    K = [
        (120, dict(crouch=0.25, lean=-4, scy=SC((102, 70), -150, 27, fo=-5), **WIND_UP)),
        (150, dict(crouch=0.35, lean=-6, scy=SC((101, 68), -160, 26, fo=-5), eyes=1, fire=1, **WIND_UP)),
        (90, dict(bob=-2, lean=-8, scy=SC((101, 62), -172, 25, fo=-5), wind=4, lift=4, wl=(210, 1.1, 1.0), wr=(-30, 1.1, 0.85))),
        (110, dict(bob=-3, lean=-9, scy=SC((101, 62), -176, 25, fo=-5), wind=3, lift=4, wl=(270, 0.9, 1.0), wr=(-90, 0.9, 0.85))),
        (110, dict(bob=-3, lean=-9, scy=SC((101, 62), -176, 25, fo=-5), wind=3, lift=3, wl=(262, 1.0, 1.0), wr=(-82, 1.0, 0.85))),
        (45, dict(bob=-1, lean=4, scy=SC((110, 68), -80, 30, fo=-6), wind=-4, fx=(("smear",),), **WIND_OUT)),
        (55, dict(crouch=0.45, lean=16, scy=SC((114, 88), 30, 32, fo=-6), wind=-6, fx=(("smear",), ("dust", 140, 3.0)), **WIND_OUT)),
        (200, dict(crouch=0.5, lean=16, scy=SC((114, 90), 40, 30, fo=-6), fx=(("dust", 130, 3.0),), **WIND_OUT)),
        (140, dict(crouch=0.3, lean=8, scy=SC((110, 88), 10, 32), hf=(98, 90))),
        (140, dict(crouch=0.1, lean=2, scy=SC((108, 82), -60, 33), hf=(94, 89))),
    ]
    return seq(K)


def anim_death():
    # she sinks to her knees; the scythe slips from her hands and goes out; the last flame leaves her; ash
    K = [
        (120, dict(lean=-10, bob=1, head=(-1, 1), scy=SC((100, 86), 150, 30), hf=(88, 86), wind=4, eyes=1)),
        (140, dict(lean=-6, bob=3, crouch=0.2, head=(0, 1.5), scy=SC((101, 90), 160, 28), hf=(89, 90), wind=3)),
        (160, dict(lean=4, crouch=0.45, head=(0.5, 2), scy=SC((103, 95), 172, 24), hf=(94, 96), wind=1, wl=(236, 0.9, 0.9), wr=(-56, 0.9, 0.75))),
        (200, dict(lean=6, crouch=0.6, head=(0.5, 2.5), scy=SC((104, 96), 176, 22, vis=0.8), hf=(96, 97), wl=(226, 0.8, 0.85), wr=(-46, 0.8, 0.7))),
        (220, dict(lean=6, crouch=0.62, head=(0.5, 2.5), scy=SC((104, 96), 178, 22, vis=0.5), hn=(106, 100), hf=(96, 98), wl=(216, 0.7, 0.75), wr=(-40, 0.7, 0.65), halo=0.6)),
        (240, dict(lean=7, crouch=0.62, head=(0.5, 3), hn=(106, 100), hf=(97, 99), wl=(206, 0.6, 0.6), wr=(-34, 0.6, 0.5), halo=0.35, fire=0, fx=(("glowheart", 1.0),))),
        (300, dict(lean=7, crouch=0.62, head=(0.5, 3), hn=(106, 100), hf=(97, 99), wl=(200, 0.5, 0.45), wr=(-30, 0.5, 0.4), halo=0.15, eyes=0.0, fx=(("glowheart", 0.6),))),
        (300, dict(lean=7, crouch=0.62, head=(0.5, 3), hn=(106, 100), hf=(97, 99), wings=False, halo=0.0, eyes=0.0)),
    ]
    for i in range(8):
        K.append((150, dict(lean=7, crouch=0.62, head=(0.5, 3), hn=(106, 100), hf=(97, 99), wings=False, halo=0.0, eyes=0.0,
                            dissolve=(i + 1) / 8 * 1.05)))
    return seq(K)

ANIMS = {"idle": (anim_idle, True), "glide": (anim_glide, True), "sweep": (anim_sweep, False), "reap": (anim_reap, False),
         "rising": (anim_rising, False), "heal": (anim_heal, False), "cast": (anim_cast, False),
         "stagger": (anim_stagger, False), "summon": (anim_summon, False),
         "lance": (anim_lance, False), "absorb": (anim_absorb, False), "dive": (anim_dive, False),
         "transform": (anim_transform, False), "blink": (anim_blink, False), "flurry": (anim_flurry, False),
         "slam": (anim_slam, False), "death": (anim_death, False)}
# which tags each phase's sheets carry
PHASE_TAGS = {1: ["idle", "glide", "sweep", "reap", "rising", "heal", "cast", "stagger", "summon"],
              2: ["idle", "glide", "sweep", "reap", "rising", "cast", "lance", "absorb", "dive", "stagger", "transform"],
              3: ["idle", "glide", "flurry", "blink", "slam", "stagger", "death"]}



# =========================================================================== per-frame fx
def fx_orb(F, c, r, fi):
    for y in range(int(c[1] - r - 3), int(c[1] + r + 4)):
        for x in range(int(c[0] - r - 3), int(c[0] + r + 4)):
            d = math.hypot(x + .5 - c[0], y + .5 - c[1])
            if d < r * 0.45:
                F.put([(x, y)], "L")
            elif d < r * 0.8:
                F.put([(x, y)], "F4")
            elif d < r:
                F.put([(x, y)], "F3", 190)
            elif d < r + 2 and (x + y + fi) % 2 == 0:
                F.under([(x, y)], "F2", 70)
    for k in range(6):
        a = k * 60 + fi * 17
        q = R.add(c, R.mul(R.dirv(a), r + 1.5 + 1.5 * R.hash01(k, fi, 5)))
        F.put([q], "F3")


def fx_gather(F, c, Rr, prog, fi):
    for k in range(14):
        a = k / 14 * 360 + 31 * k
        rr = Rr * (1 - prog) * (0.6 + 0.4 * R.hash01(k, fi, 7)) + 3
        q = R.add(c, R.mul(R.dirv(a), rr))
        q2 = R.add(c, R.mul(R.dirv(a), rr + 2))
        F.put([q], "F4"); F.put([q2], "F2", 190)


def apply_fx(FX, info, p, prev, fi, phase):
    F = FX["FX"]
    for f in p["fx"]:
        k = f[0]
        if k == "smear" and prev is not None and prev["scy"] and p["scy"]:
            info["smear"] |= R.fx_smear(F, info, prev["scy"], p["scy"], phase)
        elif k == "orb":
            fx_orb(F, info["hand_n"], f[1], fi); info["orb"] = info["hand_n"]
        elif k == "gather":
            fx_gather(F, info["hand_n"], f[1], f[2], fi)
        elif k == "flash":
            c = info["hand_n"]
            for a in range(0, 360, 30):
                for s in range(3, f[1] + 3):
                    if s % 2:
                        F.put([R.add(c, R.mul(R.dirv(a), s))], "F4" if s < f[1] else "F2")
        elif k == "dust":
            for i in range(int(10 * f[2])):
                x = f[1] + (R.hash01(i, 1, 31) - 0.5) * f[2] * 40
                y = FLOOR - R.hash01(i, 2, 32) * 5
                F.put([(x, y)], "W4" if i % 3 else "F3")
        elif k == "glowheart":
            c = info["heart"]
            fx_orb(F, c, 1.5 + 2.5 * f[1], fi)
        elif k == "healburst":
            j = info["j"]
            c = (j["Ch"][0], j["Ch"][1] + 4)
            rr = 10 + 16 * f[1]
            for a in range(0, 360, 6):
                q = R.add(c, (math.cos(math.radians(a)) * rr, math.sin(math.radians(a)) * rr * 0.8))
                if q[1] < FLOOR and (a // 6 + fi) % 2 == 0:
                    F.put([q], "F4" if f[1] < 0.7 else "F3", 255 if f[1] < 0.7 else 190)
            for i in range(14):
                q = (c[0] + (R.hash01(i, fi, 41) - 0.5) * 30, c[1] + 20 - R.hash01(i, 3, 42) * 40 * f[1])
                F.put([q], "F3")


# =========================================================================== build
def build_tag(tag, phase):
    fn, loop = ANIMS[tag]
    frames = fn()
    sec = secondary(frames, loop)
    out, infos = [], []
    prev = None
    for i, ((ms, p), s) in enumerate(zip(frames, sec)):
        p = dict(p)
        if phase >= 2 and not p.get("keepveil"):
            p["veil"] = 0.0
            p["eyes"] = max(p["eyes"], 1.0)
        if phase >= 3:
            p["halo_broken"] = max(p["halo_broken"], 0.8)
            p["halo"] = min(p["halo"], 0.7)
        L, FX, info = R.render(p, i, s, phase, prev)
        apply_fx(FX, info, p, prev, i, phase)
        imgs = R.compose(L, FX, info, p, phase)
        if p["dissolve"] > 0:
            R.dissolve(imgs, p["dissolve"], i, [n for n in R.ORDER if n not in ("FX",)])
        for w in info.get("warn", []):
            print(f"  WARN {tag}[{i}] p{phase}: {w}")
        out.append({"ms": ms, "cels": imgs})
        infos.append(info)
        prev = p
    return out, infos


def preview_strip(name, frames, scale=4, bg=(92, 92, 98, 255)):
    n = len(frames)
    sh = Image.new("RGBA", (n * W * scale, H * scale), (40, 40, 46, 255))
    for i, f in enumerate(frames):
        im = Image.new("RGBA", (W, H), bg)
        im.alpha_composite(R.flatten(f["cels"]))
        for x in range(W):
            im.putpixel((x, AY), (60, 50, 50, 255))
        sh.alpha_composite(im.resize((W * scale, H * scale), Image.NEAREST), (i * W * scale, 0))
    sh.save(os.path.join(PV, name))


ATTACKS = {  # tag -> active windows (frame index ranges, inclusive) whose hit rects come from the blade/smear/lances
    "sweep": [(3, 5)], "reap": [(2, 4), (6, 8)], "rising": [(3, 5)], "lance": [(3, 6)], "dive": [(7, 9)],
    "flurry": [(1, 2), (5, 6), (9, 10)], "slam": [(5, 6)],
}
TELEGRAPH = {"sweep": [2], "reap": [1], "rising": [2], "lance": [2], "dive": [6], "flurry": [0, 4, 8], "slam": [4]}
SPAWN = {"rising": 4, "cast": 6, "heal": 8, "dive": 9, "slam": 6, "absorb": 4, "lance": 4, "summon": 9, "transform": 9}


def hit_pts(inf):
    pts = set(inf.get("blade_px", ())) | set(inf.get("smear", ())) | set(inf.get("lance_px", ()))
    pts = {q for q in pts if q[1] <= FLOOR}
    if pts:    # the shaft sweeps the space between her hands and the blade too
        pts.add(R.ipt(inf["hand_n"]))
    return pts


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


def pack(tags, cnt, cap=21):
    bins = []
    for t in sorted(tags, key=lambda t: -cnt[t]):
        for b in bins:
            if sum(cnt[x] for x in b) + cnt[t] <= cap:
                b.append(t); break
        else:
            bins.append([t])
    return bins


def main():
    meta = {"native": 1, "frame": [W, H], "anchor": [AX, AY], "floor_y": AY, "attacks": {}, "telegraph": {}, "spawn": {},
            "sheets": {}, "frames": {}}
    all_infos = {}
    for ph in (1, 2, 3):
        built = {}
        for t in PHASE_TAGS[ph]:
            if ONLY is not None and t not in ONLY:
                continue
            fr, inf = build_tag(t, ph)
            built[t] = (fr, inf)
            all_infos[(ph, t)] = inf
            preview_strip(f"venn_wip_{t}_p{ph}.png", fr)
            print("built", t, ph, len(fr), flush=True)
            # per-phase hit rects (phase 2 blades are longer; lances only exist there)
            if t in ATTACKS:
                wins = []
                for a, b in ATTACKS[t]:
                    rects = {}
                    for k in range(a, b + 1):
                        pts = hit_pts(inf[k])
                        if pts:
                            rects[str(k)] = R.bbox(pts, 1)
                    if rects:
                        wins.append({"active": [a, b], "hit": R.union_rect(list(rects.values())), "rects": rects})
                meta["attacks"].setdefault(f"p{ph}", {})[t] = {"windows": wins}
            if t in TELEGRAPH:
                tl = []
                for k in TELEGRAPH[t]:
                    i = inf[k]
                    at = i.get("blade_tip") or i.get("heart")
                    if t == "lance":
                        at = i["heart"]
                    tl.append({"frame": k, "at": pt(at)})
                meta["telegraph"].setdefault(f"p{ph}", {})[t] = tl
            if t in SPAWN:
                k = SPAWN[t]
                i = inf[k]
                meta["spawn"].setdefault(f"p{ph}", {})[t] = {"frame": k, "at": pt(i.get("orb") or i.get("blade_tip") or i["heart"]),
                                                             "heart": pt(i["heart"])}
        if ONLY is not None:
            continue
        cnt = {t: len(built[t][0]) for t in built}
        groups = pack(list(built), cnt)
        names = [f"venn_boss_p{ph}_{gi + 1}" for gi in range(len(groups))]
        meta["sheets"][f"p{ph}"] = {t: names[gi] for gi, grp in enumerate(groups) for t in grp}
        if not PREVIEW:
            for gi, grp in enumerate(groups):
                frames, tg = [], []
                for t in grp:
                    tg.append((t, len(frames), len(frames) + cnt[t] - 1))
                    frames += built[t][0]
                asebuild.build(names[gi], W, H, R.ORDER, frames, tg)
                print("sheet", names[gi], grp, len(frames), flush=True)
    if ONLY is not None:
        return
    idle0 = all_infos[(1, "idle")][0]
    body = {q for q in idle0["robe_px"] if q[1] < 118} | idle0["face_px"]
    hb = R.bbox(body, 0)
    meta["hurtbox"] = [hb[0] + 4, hb[1] - 1, hb[2] - 8, hb[3] + 1]
    kneel = all_infos[(1, "heal")][6]
    kb = R.bbox({q for q in kneel["robe_px"] if q[1] < 118} | kneel["face_px"], 0)
    meta["hurtbox_kneel"] = [kb[0] + 4, kb[1] - 1, kb[2] - 8, kb[3] + 1]
    meta["notes"] = ("faces right; anchor [96,122] = hem on the floor line. attacks.p<phase>.<tag>.windows[].rects keyed by "
                     "frame index within the tag (blade + smear + lances). telegraph at = blade tip on the glint frame. "
                     "spawn at = orb / blade tip / heart on that frame. sheets.p<phase>.<tag> -> sheet name.")
    with open(os.path.join(ART, "..", "assets", "venn_boss_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print("hurtbox", meta["hurtbox"], "kneel", meta["hurtbox_kneel"])
    for ph in ("p1", "p2", "p3"):
        for t, d in meta["attacks"].get(ph, {}).items():
            print(ph, t, [w["hit"] for w in d["windows"]])
    hit_preview(all_infos, meta)


def hit_preview(all_infos, meta):
    """Every attack frame with its hit rect (red) and the hurtbox (green) over the sprite."""
    rows = []
    for ph in (1, 2, 3):
        for t, d in meta["attacks"].get(f"p{ph}", {}).items():
            strip = Image.open(os.path.join(PV, f"venn_wip_{t}_p{ph}.png"))
            row = []
            for w in d["windows"]:
                for k, r in w["rects"].items():
                    k = int(k)
                    im = strip.crop((k * W * 4, 0, (k + 1) * W * 4, H * 4)).resize((W * 2, H * 2), Image.NEAREST)
                    from PIL import ImageDraw
                    dr = ImageDraw.Draw(im)
                    dr.rectangle([r[0] * 2, r[1] * 2, (r[0] + r[2]) * 2, (r[1] + r[3]) * 2], outline=(255, 60, 60))
                    hb = meta["hurtbox"]
                    dr.rectangle([hb[0] * 2, hb[1] * 2, (hb[0] + hb[2]) * 2, (hb[1] + hb[3]) * 2], outline=(60, 255, 90))
                    row.append(im)
            rows.append(row)
    cols = max(len(r) for r in rows)
    sh = Image.new("RGBA", (cols * W * 2, len(rows) * H * 2), (30, 30, 34, 255))
    for y, r in enumerate(rows):
        for x, im in enumerate(r):
            sh.paste(im, (x * W * 2, y * H * 2))
    sh.save(os.path.join(PV, "venn_hitbox.png"))


if __name__ == "__main__":
    main()
