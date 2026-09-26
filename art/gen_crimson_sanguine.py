#!/usr/bin/env python3
"""Countess Sanguine (agent C, The Crimson Manor) -- main boss.

    python3 art/gen_crimson_sanguine.py [--preview] [--only idle,flurry]

A tall, slender vampiric noblewoman: dark crimson ball gown with a high fanned collar and a long train, porcelain skin,
a sharp aristocratic face, glowing red eyes, black hair in a high knot, a rapier of solidified blood; thin blood
ribbons rise from her gown.  Phase 2 (`sanguine_p2`, same frames/tags/body + extra tags): the gown dissolves into a
torrent of blood, blood wings, her hair loosens.

One rig for every frame: fixed segment lengths (upper arm 12, forearm 11), fixed head/torso/bodice geometry that is only
rotated about the waist (lean) and moved (bob / dx); the gown always reaches the floor row, so there are no feet to
slide.  Faces RIGHT.  Frame 176x128, anchor [80, 128] (the hem line).

Outputs: art/sanguine.aseprite + assets/sanguine.png/.json, art/sanguine_p2.aseprite + assets/sanguine_p2.*,
assets/sanguine_meta.json (per-frame hurtbox / hand / off-hand / tip / dive hit + attack windows + spawn + telegraph),
previews art/previews/sanguine*.png.
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, n_capsule, n_dome, n_plate, poly_mask, line, polyline, bezier, ik,  # noqa: E402
                       mask_disc, ip, hash01, add, sub, lerp, dirv, rot_pt, render_layer, flatten, inb)
from PIL import Image, ImageDraw  # noqa: E402

W, H = 176, 128
K.setup(W, H)
AX, AY = 80, 128
FLOOR = 127
BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

NEW = {
    # porcelain skin: cool violet shadow -> warm white
    "S": ["#241a26", "#463646", "#76616e", "#ab98a0", "#d6cac8", "#f4ede6"],
    # the gown: deep crimson velvet (no garish red; the light tops out at a dark rose)
    "N": ["#110309", "#240712", "#3d0b1a", "#5c1124", "#80192e", "#a42a38"],
    # black hair (blue-violet sheen)
    "H": ["#060509", "#100d16", "#1b1724", "#2a2538", "#3e3854", "#5c5678"],
    # black velvet / lace
    "X": ["#070508", "#110c12", "#1c141e", "#2a1f2c", "#3e3042", "#5a4a5e"],
    # blood-crystal (rapier, wings' ribs, the torrent's light)
    "Z": ["#2e040c", "#5c0816", "#920f22", "#c82032", "#f0505a", "#ffb0a8"],
    # tarnished silver
    "U": ["#15141b", "#2c2b36", "#4e4d5c", "#7c7b8c", "#b0afc0", "#e8e8f2"],
    # fixed glows
    "E": ["#5a0008", "#b0101a", "#ff2e2e", "#ff8a78", "#fff0e6"],
}
for r, cols in NEW.items():
    keys = []
    for i, c in enumerate(cols):
        k = f"{r}{i}"
        K.HEX[k] = c
        K.RGBA[k] = tuple(int(c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        keys.append(k)
    K.RAMP[r] = keys
K.SHINY.update({"Z": 0.9, "U": 0.9, "S": 0.97})
RGBA = K.RGBA
_lvl0 = K.level_of


def _level(e, x, y):   # porcelain glows from within: skin stays pale in shadow; velvet sinks darker toward the hem
    i = _lvl0(e, x, y)
    if e[0] == "S" and not isinstance(e[3], tuple):
        i = min(len(K.RAMP["S"]) - 1, i + 1 + (1 if i <= 1 else 0))
    return i


K.level_of = _level

LAYERS1 = ["FXBack", "Train", "Gown", "ArmFar", "Collar", "Body", "Head", "ArmNear", "Sword", "Glow", "FX"]
LAYERS2 = ["FXBack", "WingFar", "WingNear", "Train", "Gown", "ArmFar", "Collar", "Body", "Head", "ArmNear", "Sword", "Glow", "FX"]

# ------------------------------------------------------------------ rig (upright model coords, facing right)
WA = (80.0, 70.0)          # waist: lean pivot
REST = dict(Hd=(84.5, 39.5), Nk=(82.5, 47.5), Sn=(86.5, 52.0), Sf=(76.5, 51.5), Ch=(82.0, 58.0), Hip=(80.0, 78.0))
L1, L2 = 12.0, 11.0        # upper arm, forearm (both arms, every frame)
BLADE = 40.0

BASE = dict(lean=0.0, bob=0.0, dx=0.0, head=(0.0, 0.0), htilt=0.0,
            hn=(99.0, 76.0), sa=28.0, hf=(75.0, 70.0), pref_n=(0.2, 1.0), pref_f=(-0.6, 1.0),
            blade=1.0, whipgrip=False, flare=0.0, wind=0.0, ph=0.0, eyes=1.0, ribbons=1.0,
            spread=0.0, flap=0.0, fly=0.0, fx=(), smear=None, mirror=False, sink=0.0, hair=0.0, offglow=0.0)


def P(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


def joints(p):
    def X(q):
        r = rot_pt(q, WA, p["lean"])
        return (r[0] + p["dx"], r[1] + p["bob"])
    j = {k: X(v) for k, v in REST.items()}
    j["Hd"] = add(j["Hd"], p["head"])
    j["X"] = X
    j["Wa"] = (WA[0] + p["dx"], WA[1] + p["bob"])
    return j


def reach(s, h, l):
    d = math.hypot(h[0] - s[0], h[1] - s[1])
    if d <= l:
        return h
    return lerp(s, h, l / d)


# ------------------------------------------------------------------ parts
def draw_head(L, G, j, p, phase):
    Hd = j["Hd"]
    Hl = L["Head"]
    X = j["X"]
    Hl.paint(n_capsule(j["Nk"], add(Hd, (-0.5, 3.5)), 2.0, 1.8), "S", bias=-1)
    head = n_dome(Hd, 4.6, 5.5, tilt=(0.25, -0.1))
    Hl.paint(head, "S")
    Hl.paint(n_dome(add(Hd, (2.2, 3.4)), 2.1, 1.9), "S", ao=0)                 # the sharp jaw
    Hl.paint(n_capsule(add(Hd, (3.7, -0.4)), add(Hd, (4.7, 1.3)), 0.6, 0.7), "S", ao=0)   # nose
    face = set(head)
    # hair: a close black cap over the crown and the back of the head, a high knot, a loose strand
    cap = n_dome(add(Hd, (-1.4, -1.6)), 4.8, 5.0, tilt=(-0.1, -0.1))
    capm = {q: v for q, v in cap.items() if (q[0] + .5 - Hd[0]) < -1.4 - (q[1] + .5 - Hd[1]) * 0.45 or (q[1] + .5 - Hd[1]) < -3.8}
    capm = {q: v for q, v in capm.items() if q[1] < Hd[1] + 2.6}
    Hl.paint(capm, "H", ao=0)
    knot = add(Hd, (-3.6, -5.6))
    Hl.paint(n_dome(knot, 2.6, 2.3), "H", ao=0)
    Hl.paint(n_dome(add(knot, (-1.6, -1.8)), 1.5, 1.4), "H", ao=0)
    pin = ip(add(knot, (1.6, -1.5)))
    Hl.fill([pin, (pin[0] + 1, pin[1] - 1)], "U4")
    G.put([(pin[0] + 1, pin[1] - 1)], "E2")
    # parted fringe line across the brow
    Hl.decal(line(add(Hd, (-1.5, -4.0)), add(Hd, (3.2, -2.8))), ("H", 3))
    if phase == 2 or p["hair"] > 0:                   # loosened hair streaming back (phase 2)
        k = max(p["hair"], 1.0 if phase == 2 else 0.0)
        for s in range(4):
            base = add(Hd, (-3.5 - s * 0.4, -3 + s * 2.0))
            pts = []
            for i in range(12):
                t = i / 11
                wv = math.sin(p["ph"] * 2 + s * 1.3 - t * 4) * 2.0 * t
                pts.append((base[0] - 16 * t * k - p["wind"] * 0.5 * t, base[1] - 4 * t * k + 10 * t * (1 - k) + wv))
            Hl.fill(polyline(pts), "H1" if s % 2 else "H2")
    else:                                               # a single loose strand at the nape
        strand = bezier(add(Hd, (-3.5, 1.0)), add(Hd, (-5.0, 5.0)), add(Hd, (-4.0, 9.0)), add(Hd, (-5.5, 13.0 + math.sin(p["ph"]) * 0.8)), 10)
        Hl.fill(polyline(strand), "H1")
    # face: brow shadow, one glowing eye, lips
    ex, ey = ip(add(Hd, (2.1, -0.6)))
    Hl.decal([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1)], "H2")
    Hl.decal([(ex - 1, ey), (ex + 1, ey)], ("S", 2))
    e = p["eyes"]
    if e > 0.2:
        G.put([(ex, ey)], "E4" if phase == 2 else "E3")
        if e > 0.6:
            G.put([(ex + 1, ey)], "E2")
            if phase == 2:
                G.put([(ex - 1, ey), (ex - 2, ey)], "E1")
    else:
        Hl.decal([(ex, ey)], "H1")
    lp = ip(add(Hd, (3.3, 3.4)))
    Hl.decal([lp], "Z2")
    cheek = ip(add(Hd, (0.5, 1.5)))
    Hl.decal([cheek, (cheek[0], cheek[1] + 1)], ("S", 3))
    return face


def draw_collar(L, j, p, phase):
    """The high fanned collar: three stiff lace points rising behind the head, framed in black with silver tips."""
    X = j["X"]
    Cl = L["Collar"]
    base_l, base_r = X((77.0, 51.5)), X((84.5, 50.0))
    tips = [X((67.5, 34.0)), X((72.5, 26.5)), X((78.5, 28.5))]
    valleys = [X((72.0, 38.0)), X((76.5, 34.5))]
    poly = [base_l, X((71.0, 46.0)), tips[0], valleys[0], tips[1], valleys[1], tips[2], X((80.0, 40.0)), base_r]
    m = poly_mask(poly)
    Cl.paint(n_plate(m, bevel=2.5, tilt=(-0.15, -0.2), strength=1.0,
                     fold=lambda x, y: (0.35 * math.sin((x - base_l[0]) * 1.3), 0.0)), "N", bias=-1)
    edge = {q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in ((1, 0), (-1, 0), (0, -1)))}
    Cl.decal(edge, ("X", 2))
    Cl.decal({q for q in edge if (q[0] - 1, q[1]) not in m or (q[0], q[1] - 1) not in m}, ("U", 2))
    for t in tips:
        Cl.fill([ip(t)], "U4")
    # lace ribs radiating from the neck
    for t in tips:
        Cl.decal(line(lerp(base_l, base_r, 0.5), lerp(lerp(base_l, base_r, 0.5), t, 0.8)), ("N", 1))


def draw_body(L, G, j, p, phase):
    X = j["X"]
    B = L["Body"]
    bod = [X(q) for q in ((77.0, 50.0), (85.5, 49.5), (88.5, 53.5), (89.5, 58.5), (87.8, 63.5), (85.0, 69.5), (84.5, 71.5),
                          (76.0, 71.5), (75.5, 69.5), (74.5, 63.0), (74.2, 56.5), (75.0, 52.5))]
    bm = poly_mask(bod)
    B.paint(n_plate(bm, bevel=3.5, tilt=(0.12, -0.05), strength=1.35), "N")
    B.paint(n_dome(X((86.2, 58.0)), 3.0, 2.6, tilt=(0.1, 0.1)), "N", ao=0, clip=bm)
    # black lace stomacher: a pointed V down the front with silver lacing
    st = poly_mask([X((82.0, 51.0)), X((86.5, 51.0)), X((83.2, 71.5))])
    st &= bm
    B.paint(n_plate(st, bevel=1.5, strength=0.8), "X", ao=0)
    for k in range(5):
        c = X((83.8 - k * 0.2, 54.0 + k * 3.3))
        B.decal([ip(c)], ("U", 3))
    # sash at the waist + brooch (a drop of blood in silver)
    B.decal(line(X((75.8, 70.0)), X((85.0, 70.0))), ("X", 2))
    B.decal(line(X((75.8, 71.0)), X((85.0, 71.0))), ("X", 1))
    br = X((85.6, 52.5))
    B.paint(n_dome(br, 1.6, 1.6), "U", ao=0)
    G.put([ip(br)], "E2" if phase == 1 else "E3")
    # high neckline: black lace band up the throat
    B.paint(n_capsule(X((81.0, 50.5)), X((84.8, 49.8)), 1.3, 1.3), "X", ao=0)
    return bm


def gown_poly(j, p, phase):
    """Skirt: a slim fall over the hips that flares into a bell, the hem always on the floor row."""
    Wa = j["Wa"]
    X = j["X"]
    ph, wind, fl = p["ph"], p["wind"], p["flare"]
    top_l, top_r = X((75.5, 71.0)), X((85.0, 71.0))
    hy = FLOOR
    fr = (103.0 + fl + wind * 0.35 + p["dx"] * 0.6, hy)
    bk = (58.0 - fl * 0.6 + wind * 0.5 + p["dx"] * 0.6, hy)
    right = bezier(top_r, (87.0 + p["dx"] * 0.4, 92.0), (fr[0] - 4 + wind * 0.2, 114.0), fr, 14)
    left = bezier(top_l, (73.5 + p["dx"] * 0.3, 94.0), (bk[0] + 3, 114.0), bk, 14)
    hem = []
    n = 30
    for i in range(n + 1):
        t = i / n
        x = fr[0] + (bk[0] - fr[0]) * t
        y = hy - 0.6 - 0.9 * abs(math.sin(ph * 1.0 + t * 9.0)) * (0.5 + t)
        hem.append((x, y))
    return right + hem[1:-1] + list(reversed(left)), (top_l, top_r, fr, bk, hy)


def draw_gown(L, G, F, Fb, j, p, phase, info):
    poly, (tl, tr, fr, bk, hy) = gown_poly(j, p, phase)
    m = poly_mask(poly)
    m = {q for q in m if q[1] <= FLOOR}
    Gw = L["Gown"]
    ph = p["ph"]
    Wa = j["Wa"]

    def fold(x, y):
        t = max(0.0, min(1.0, (y - Wa[1]) / max(1.0, hy - Wa[1])))
        cx = lerp(Wa, ((fr[0] + bk[0]) / 2, hy), t)[0]
        hw = 5 + (fr[0] - bk[0]) / 2 * t
        u = (x + .5 - cx) / hw
        return (0.55 * math.sin(u * 3.0 * math.pi + math.sin(ph - t * 2.0) * 0.8) * (0.2 + t), 0.0)
    if phase == 1:
        Gw.paint(n_plate(m, bevel=7, tilt=(0.05, -0.05), strength=1.25, fold=fold), "N")
        # black underskirt panel down the front, silver-threaded edge
        o0, o1 = j["X"]((82.5, 72.0)), j["X"]((84.8, 72.0))
        wedge = poly_mask([o0, o1, (fr[0] - 5, hy + 1), (fr[0] - 14, hy + 1)]) & m
        Gw.paint(n_plate(wedge, bevel=2, strength=0.7, fold=lambda x, y: (0.3 * math.sin(x * 0.8 + ph), 0)), "X", bias=-1, ao=0)
        we = {q for q in wedge if any((q[0] + a, q[1]) not in wedge for a in (-1, 1))}
        Gw.decal(we, ("U", 2))
        # hem band: black velvet + a silver thread line
        rows = {}
        for (x, y) in m:
            rows[x] = max(rows.get(x, -1), y)
        for x, y in rows.items():
            if y >= hy - 2:
                Gw.decal([(x, y), (x, y - 1)], ("X", 2))
                if (x + int(ph * 2)) % 3 == 0:
                    Gw.decal([(x, y - 2)], ("U", 2))
    else:
        draw_torrent(Gw, F, m, j, p, info, fr, bk, hy)
    info["gown"] = m
    return m


def draw_torrent(Gw, F, m, j, p, info, fr, bk, hy):
    """Phase 2: the gown is a torrent of blood -- vertical streams pouring from the waist, splashing at the floor."""
    ph = p["ph"]
    fly = p["fly"]
    Wa = j["Wa"]
    if fly > 0:   # airborne: the torrent narrows into a whipping tail
        tail = []
        tip = (Wa[0] - 10 - p["wind"] * 0.8 + math.sin(ph) * 3, FLOOR - 4 - 22 * fly)
        l = [j["X"]((75.5, 71.0)), (Wa[0] - 6, Wa[1] + 22), (tip[0] + 3, tip[1] - 8), tip]
        r = [tip, (tip[0] + 8, tip[1] - 10), (Wa[0] + 8, Wa[1] + 24), j["X"]((85.0, 71.0))]
        m2 = poly_mask(bezier(*l, 12) + bezier(*r, 12))
        m = {q for q in m if q[1] < Wa[1] + 6} | m2 if fly >= 1 else (m if fly < 0.5 else m2 | {q for q in m if q[1] < Wa[1] + 6})
    nm = {}
    for q in m:
        x, y = q
        s = math.sin(x * 0.55 + math.sin(y * 0.12 + ph) * 1.2)
        nm[q] = K.norm3(0.55 * s, -0.15, 1.0)
    Gw.paint(nm, "Z", bias=-2)
    # bright liquid streams running down
    for (x, y) in m:
        v = (x * 0.9 + math.sin(y * 0.2 + x) * 0.8)
        band = math.sin(v * 1.3 + math.sin(y * 0.09 + ph) * 1.5) > 0.9
        flow = (y * 0.45 - ph * 6.0 + hash01(x, 0, 7) * 9.0) % 9.0
        if band and flow < 2.5:
            Gw.decal([(x, y)], ("Z", 4 if flow < 0.8 else 3))
        elif band and flow < 5:
            Gw.decal([(x, y)], ("Z", 2))
    edge = {q for q in m if (q[0] - 1, q[1]) not in m or (q[0] + 1, q[1]) not in m}
    Gw.decal(edge, ("Z", 1))
    info["gown"] = m
    if fly < 0.5:   # splashes and a spreading pool at the hem
        for k in range(10):
            a = hash01(k, int(ph * 3), 3)
            x = bk[0] + (fr[0] - bk[0]) * a
            h = 2 + 3 * hash01(k, int(ph * 5), 9)
            F.put([ip((x + math.sin(ph + k) * 2, FLOOR - h))], "Z4" if k % 3 == 0 else "Z3")
        for x in range(int(bk[0]) - 6, int(fr[0]) + 7):
            if inb(x, FLOOR):
                F.put([(x, FLOOR)], "Z2" if (x + int(ph * 4)) % 5 else "Z3")
    else:           # drips falling from the tail
        for k in range(4):
            t = (ph * 0.6 + k * 0.25) % 1.0
            x = Wa[0] - 6 + k * 3 - p["wind"] * 0.4
            y = Wa[1] + 28 + t * 30
            F.put([ip((x, y)), ip((x, y + 1))], "Z3")


def draw_train(L, j, p, phase):
    """Phase 1: the long train sweeping behind along the floor."""
    if phase == 2:
        return
    Tr = L["Train"]
    ph, wind = p["ph"], p["wind"]
    X = j["X"]
    a = X((75.0, 82.0))
    tip = (38.0 + wind * 1.4 - p["flare"] * 0.5 + p["dx"] * 0.4, FLOOR - 0.5 - 1.2 * abs(math.sin(ph - 1.2)))
    top = bezier(a, (68.0 + wind * 0.4, 100.0), (50.0 + wind, 118.0 + math.sin(ph) * 1.2), tip, 14)
    bot = [(tip[0] + 6, FLOOR), (62.0, FLOOR)]
    m = poly_mask(top + bot)
    m = {q for q in m if q[1] <= FLOOR}
    Tr.paint(n_plate(m, bevel=3, tilt=(0.1, -0.25), strength=0.9, fold=lambda x, y: (0.45 * math.sin((x + y * 0.8) * 0.4 + ph), 0)), "N", bias=-1)
    rim = {q for q in m if (q[0], q[1] + 1) not in m or q[1] == FLOOR}
    Tr.decal(rim, ("X", 2))


def draw_arm(L, G, F, j, p, side, phase, info):
    near = side == "n"
    sh = j["Sn"] if near else j["Sf"]
    Lr = L["ArmNear"] if near else L["ArmFar"]
    bias = 0 if near else -1
    target = p["hn"] if near else p["hf"]
    hand = reach(sh, target, L1 + L2 - 0.4)
    el = ik(sh, hand, L1, L2, p["pref_n"] if near else p["pref_f"])
    # tight black velvet sleeves, a little puff at the shoulder, lace flaring at the wrist
    Lr.paint(n_dome(sh, 2.8, 2.6), "X", bias=bias)
    Lr.paint(n_capsule(sh, el, 2.1, 1.8), "X", bias=bias)
    Lr.paint(n_capsule(el, hand, 1.7, 1.3), "X", bias=bias)
    fa = K.norm3(hand[0] - el[0], hand[1] - el[1], 0)
    cuff = sub(hand, (fa[0] * 2.2, fa[1] * 2.2))
    perp = (-fa[1], fa[0])
    lace = poly_mask([add(cuff, (perp[0] * 2.8, perp[1] * 2.8)), add(cuff, (-perp[0] * 2.8, -perp[1] * 2.8)),
                      add(hand, (-perp[0] * 1.2 - fa[0] * 0.5, -perp[1] * 1.2 - fa[1] * 0.5)), add(hand, (perp[0] * 1.2 - fa[0] * 0.5, perp[1] * 1.2 - fa[1] * 0.5))])
    Lr.paint({q: (0.0, -0.4, 0.9) for q in lace}, "N", bias=bias - 1, ao=0)
    Lr.paint(n_dome(hand, 1.5, 1.5), "S", bias=bias, ao=0)
    info["hand_" + side] = hand
    info["el_" + side] = el
    return hand


def draw_sword(L, G, F, j, p, info, phase):
    """Rapier of solidified blood: silver cup hilt, long crystalline blade."""
    Sw = L["Sword"]
    hand = info["hand_n"]
    d = dirv(p["sa"])
    perp = (-d[1], d[0])
    pom = sub(hand, (d[0] * 3.2, d[1] * 3.2))
    Sw.paint(n_dome(pom, 1.3, 1.3), "U", ao=0)
    Sw.paint(n_capsule(pom, hand, 0.8, 0.8), "X", ao=0)
    cup = add(hand, (d[0] * 1.6, d[1] * 1.6))
    Sw.paint(n_dome(cup, 2.3, 2.3, tilt=(d[0] * 0.3, d[1] * 0.3)), "U", ao=0)
    q0, q1 = add(cup, (perp[0] * 3.5 + d[0] * 0.8, perp[1] * 3.5 + d[1] * 0.8)), add(cup, (-perp[0] * 3.5 + d[0] * 0.8, -perp[1] * 3.5 + d[1] * 0.8))
    Sw.fill(line(q0, q1), "U3")
    Sw.fill([ip(q0), ip(q1)], "U5")
    ln = BLADE * p["blade"]
    tip = add(cup, (d[0] * (2 + ln), d[1] * (2 + ln)))
    if ln > 1:
        b0 = add(cup, (d[0] * 2, d[1] * 2))
        core = line(b0, tip)
        edge = line(add(b0, (perp[0] * 0.9, perp[1] * 0.9)), add(lerp(b0, tip, 0.65), (perp[0] * 0.6, perp[1] * 0.6)))
        Sw.fill(edge, "Z1")
        Sw.fill(core, "Z3")
        hi = core[: int(len(core) * 0.7)]
        Sw.fill(hi[1::3], "Z4")
        G.put([ip(tip)], "Z5")
        info["blade_px"] = set(core) | set(edge)
    else:
        info["blade_px"] = set()
    info["tip"] = tip
    info["cup"] = cup
    # a blood drip hanging from the guard (idle life)
    if p.get("drip") is not None:
        k = p["drip"]
        dp = add(cup, (0, 2 + 4 * k))
        F.put([ip(dp)], "Z3")


def draw_ribbons(F, Fb, j, p, info, phase):
    """Thin blood ribbons rising from the gown and fading upward (alpha stepped via lighter colours)."""
    if p["ribbons"] <= 0:
        return
    ph = p["ph"]
    for k in range(4 if phase == 1 else 6):
        bx = 62 + k * 11 + (4 if k % 2 else 0) + p["dx"] * 0.5
        by = 118 - (k % 3) * 9
        length = (34 + 10 * (k % 2)) * p["ribbons"]
        pts = []
        for i in range(16):
            t = i / 15
            y = by - length * t
            x = bx + math.sin(ph * 1.0 + k * 1.7 - t * 5.0) * (1.0 + 4.0 * t) - p["wind"] * 0.4 * t
            pts.append((x, y))
        px = polyline(pts)
        n = len(px)
        for i, q in enumerate(px):
            t = i / max(1, n - 1)
            if t > 0.9 and hash01(q[0], q[1], k) < 0.6:
                continue
            if t > 0.65 and (i % 2):
                continue
            c = "Z3" if t < 0.25 else "Z2" if t < 0.6 else "Z1"
            (F if k % 2 else Fb).put([q], c)


# ------------------------------------------------------------------ phase 2 wings
def draw_wings(L, F, j, p, info):
    """Blood wings: bat wings of clotted crimson membrane over blood-crystal bones, spread behind her (left) and up."""
    sp = p["spread"]
    if sp <= 0.02:
        return
    ph = p["ph"]
    flap = p["flap"]
    X = j["X"]
    root = X((77.0, 54.0))
    body_end = X((76.0, 70.0))
    for side, name in ((0, "WingFar"), (1, "WingNear")):
        Lw = L[name]
        bias = -1 if side == 0 else 0
        sc = (0.86 if side == 0 else 1.0) * (0.45 + 0.55 * sp)
        # folded (sp small): the wing hangs like a mantle behind her; open: up and back
        rotd = -flap * (26 if side else 20) - (1 - sp) * 95 + (-12 if side == 0 else 0) + p["lean"] * 0.5
        def A(a):
            return a + rotd
        elbow = add(root, tuple(v * 17 * sc for v in dirv(A(-118))))
        wrist = add(elbow, tuple(v * 21 * sc for v in dirv(A(-158))))
        fingers = [add(wrist, tuple(v * ln * sc for v in dirv(A(ang)))) for ang, ln in ((-138, 22), (-178, 30), (150, 29), (122, 24))]
        poly = [root, elbow, wrist, fingers[0]]
        scal = []
        for a_, b_ in zip(fingers, fingers[1:]):
            mid = lerp(a_, b_, 0.5)
            s_ = lerp(mid, wrist, 0.26)
            poly += [s_, b_]
            scal.append(s_)
        mid = lerp(fingers[-1], body_end, 0.5)
        s_ = lerp(mid, wrist, 0.22)
        poly += [s_, body_end]
        scal.append(s_)
        m = poly_mask(poly)
        nm = n_plate(m, bevel=3, tilt=(-0.15, -0.25), strength=0.8,
                     fold=lambda x, y: (0.35 * math.sin(math.atan2(y - wrist[1], x - wrist[0]) * 7.0 + ph * 0.5), 0.0))
        Lw.paint(nm, "N", bias=bias - 1)
        # veins of brighter blood running from the bones into the membrane
        for fi, tipp in enumerate(fingers):
            for t in (0.45, 0.75):
                q = lerp(wrist, tipp, t)
                Lw.decal(line(q, lerp(q, scal[min(fi, len(scal) - 1)], 0.5)), ("N", 4))
        # bones of blood-crystal
        Lw.paint(n_capsule(root, elbow, 1.7, 1.3), "Z", bias=bias, ao=0)
        Lw.paint(n_capsule(elbow, wrist, 1.3, 1.0), "Z", bias=bias, ao=0)
        Lw.paint(n_dome(wrist, 1.4, 1.4), "Z", bias=bias, ao=0)
        for tipp in fingers:
            Lw.paint({q: (0.0, -0.5, 0.85) for q in line(wrist, tipp)}, "Z", bias=bias, ao=0)
        claw = add(wrist, tuple(v * 3 for v in dirv(A(-100))))
        Lw.paint({q: (0.0, -0.6, 0.8) for q in line(wrist, claw)}, "Z", bias=bias, ao=0)
        # the trailing edge drips
        for k, s2 in enumerate(scal):
            dl = 2 + int(4 * hash01(k, int(ph * 2.5), side))
            F.put([ip((s2[0], s2[1] + i)) for i in range(1, dl)], "Z2")
            F.put([ip((s2[0], s2[1] + dl + 1))], "Z3")
        info.setdefault("wing_px", set()).update(m)


# ------------------------------------------------------------------ fx
def fx_thrust(F, info, p):
    tip = info["tip"]
    d = dirv(p["sa"])
    perp = (-d[1], d[0])
    for k, off in enumerate((-2.0, 0.0, 2.0)):
        a = add(tip, (perp[0] * off - d[0] * (14 + 4 * k), perp[1] * off - d[1] * (14 + 4 * k)))
        b = add(tip, (perp[0] * off * 0.3 + d[0] * 5, perp[1] * off * 0.3 + d[1] * 5))
        F.put(line(a, b)[::1 if k == 1 else 2], "Z5" if k == 1 else "Z4")
    t = ip(add(tip, (d[0] * 3, d[1] * 3)))
    F.put([t, (t[0] + 1, t[1]), (t[0] - 1, t[1]), (t[0], t[1] + 1), (t[0], t[1] - 1)], "E4")


def fx_lunge_trail(F, j, p):
    for k in range(6):
        y = 60 + k * 9 + p["bob"] * 0.6
        x0 = j["Wa"][0] - 30 - k * 3
        pts = line((x0, y), (x0 + 12 + (k % 2) * 6, y))
        F.put([q for i, q in enumerate(pts) if i % 4 != 3], "Z3" if k % 2 else "Z2")


def fx_off_glow(F, info, p):
    k = p["offglow"]
    if k <= 0:
        return
    h = info["hand_f"]
    r = 1.5 + 3.5 * k
    for q in mask_disc(h, r):
        dd = math.hypot(q[0] + .5 - h[0], q[1] + .5 - h[1]) / r
        if dd < 0.35:
            F.put([q], "E4")
        elif dd < 0.7:
            F.put([q], "E2")
        elif hash01(q[0], q[1], int(k * 9)) < 0.5:
            F.put([q], "Z3")
    for i in range(int(6 * k)):
        a = hash01(i, int(k * 10), 5) * 6.28
        rr = r + 3 + 5 * hash01(i, 1, int(k * 10))
        F.put([ip((h[0] + math.cos(a) * rr, h[1] + math.sin(a) * rr))], "Z3")


# ------------------------------------------------------------------ frame assembly
def render(p, phase, fi=0):
    L = {n: Layer(n) for n in (LAYERS2 if phase == 2 else LAYERS1) if n not in ("FXBack", "Glow", "FX")}
    F, Fb, G = FXLayer("FX"), FXLayer("FXBack"), FXLayer("Glow")
    j = joints(p)
    info = {}
    if phase == 2:
        draw_wings(L, F, j, p, info)
    draw_train(L, j, p, phase)
    draw_gown(L, G, F, Fb, j, p, phase, info)
    draw_arm(L, G, F, j, p, "f", phase, info)
    draw_collar(L, j, p, phase)
    draw_body(L, G, j, p, phase)
    draw_head(L, G, j, p, phase)
    draw_arm(L, G, F, j, p, "n", phase, info)
    draw_sword(L, G, F, j, p, info, phase)
    draw_ribbons(F, Fb, j, p, info, phase)
    fx_off_glow(F, info, p)
    for f in p["fx"]:
        if f == "thrust":
            fx_thrust(F, info, p)
        elif f == "trail":
            fx_lunge_trail(F, j, p)
    imgs = {n: render_layer(l) for n, l in L.items()}
    imgs["FX"] = F.image()
    imgs["FXBack"] = Fb.image()
    imgs["Glow"] = G.image()
    info["hurt_px"] = set(L["Body"].px) | set(L["Head"].px) | {q for q in L["Gown"].px if q[1] < 112}
    return imgs, info


def mirror_imgs(imgs):
    out = {}
    for n, im in imgs.items():
        f = im.transpose(Image.FLIP_LEFT_RIGHT)
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        o.paste(f, (2 * AX - W, 0))     # mirror about x = AX
        out[n] = o
    return out


def mirror_pt(q):
    return (2 * AX - q[0], q[1])


def dissolve(imgs, frac, seed=0, bats=False, blood=False, ph=0.0):
    """Remove pixels progressively (top-down bias); lost pixels become bats (vanish) or falling blood (death)."""
    out = {}
    motes = {}
    for n, im in imgs.items():
        if n in ("FX", "FXBack"):
            out[n] = im
            continue
        src = im.load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                c = src[x, y]
                if c[3] == 0:
                    continue
                t = 0.55 * hash01(x // 2, y // 2, 71 + seed) + 0.45 * (y / H if not blood else 1 - (y / H))
                if t >= frac:
                    dst[x, y] = c
                    if t < frac + 0.05 and n not in ("Glow",):
                        dst[x, y] = RGBA["Z3" if blood else "X1"]
                elif blood and hash01(x, y, 5 + seed) < 0.05:
                    fy = int(y + (frac - t) * 60)
                    if fy < FLOOR:
                        motes[(x, fy)] = "Z2" if hash01(x, y, 6) < 0.5 else "Z3"
        out[n] = new
    fx = out["FX"].copy()
    fp = fx.load()
    if bats:
        n = int(10 + 24 * min(1.0, frac * 1.5))
        for i in range(n):
            a = hash01(i, 3, seed) * 6.28
            r = 6 + frac * 46 * hash01(i, 4, seed)
            cx = AX + math.cos(a) * r * 1.2
            cy = 70 + math.sin(a) * r * 0.7 - frac * 26 * hash01(i, 5, seed)
            up = (i + int(frac * 7)) % 2
            for q, c in (((0, 0), "X1"), ((-1, -up), "X2"), ((1, -up), "X2"), ((-2, -1 + up), "X1"), ((2, -1 + up), "X1")):
                x, y = int(cx + q[0]), int(cy + q[1])
                if inb(x, y):
                    fp[x, y] = RGBA[c]
            if inb(int(cx), int(cy)) and i % 3 == 0:
                fp[int(cx), int(cy)] = RGBA["E2"]
    for (x, y), c in motes.items():
        if inb(x, y):
            fp[x, y] = RGBA[c]
    if blood:   # a spreading pool where she stood
        hw = int(6 + 26 * min(1.0, frac))
        for x in range(AX - hw, AX + hw + 1):
            if inb(x, FLOOR):
                fp[x, FLOOR] = RGBA["Z1" if abs(x - AX) > hw - 3 else "Z2"]
                if abs(x - AX) < hw - 6 and inb(x, FLOOR - 1):
                    fp[x, FLOOR - 1] = RGBA["Z1" if (x % 5) else "Z3"]
    out["FX"] = fx
    return out


# ------------------------------------------------------------------ animations (lists of (ms, pose, extra))
TAU = math.pi * 2


def loop_ph(i, n):
    return TAU * i / n


def anim_idle(phase):
    n = 6
    return [(150, P(ph=loop_ph(i, n), bob=0.5 * math.sin(loop_ph(i, n)), hn=(99.0, 76.0 + 0.5 * math.sin(loop_ph(i, n))),
                    sa=28 + 2 * math.sin(loop_ph(i, n)), drip=i / n, wind=-1.0 + math.sin(loop_ph(i, n)) * 0.6,
                    spread=0.45 if phase == 2 else 0, flap=0.15 * math.sin(loop_ph(i, n)))) for i in range(n)]


def anim_walk(phase):
    n = 8
    out = []
    for i in range(n):
        t = loop_ph(i, n)
        out.append((110, P(ph=t * 2, bob=0.8 * abs(math.sin(t)), wind=-3.5 + math.sin(t) * 1.5, flare=1.0 * math.sin(t),
                           hn=(100.0, 76.0 + math.sin(t)), sa=26, lean=2.0,
                           spread=0.45 if phase == 2 else 0, flap=0.2 * math.sin(t))))
    return out


def anim_flurry(phase):
    sp = 0.45 if phase == 2 else 0
    base = dict(spread=sp, wind=-2.0)
    key = [  # (ms, lean, bob, hand, sa, fx)
        (120, -4, 0, (90.0, 68.0), 12, ()),
        (120, -7, 1, (86.0, 66.0), 8, ()),
        (90, -6, 1, (88.0, 68.0), 14, ()),
        (60, 9, 3, (112.0, 80.0), 40, ("thrust",)),
        (80, 4, 2, (100.0, 74.0), 26, ()),
        (70, 0, 1, (96.0, 70.0), 14, ()),
        (60, 11, 4, (113.0, 83.0), 42, ("thrust",)),
        (80, 4, 2, (100.0, 76.0), 28, ()),
        (70, 0, 1, (95.0, 70.0), 16, ()),
        (60, 13, 5, (114.0, 82.0), 38, ("thrust",)),
        (130, 6, 3, (106.0, 80.0), 28, ()),
        (150, 1, 1, (100.0, 77.0), 28, ()),
    ]
    return [(ms, P(lean=l, bob=b, hn=h, sa=s, fx=f, ph=i * 0.5, **base)) for i, (ms, l, b, h, s, f) in enumerate(key)]


def anim_lunge(phase):
    sp = 0.45 if phase == 2 else 0
    key = [  # coil back, then the long fencing lunge low along the floor
        (120, -4, 1, (92.0, 70.0), 20, -2, 0, ()),
        (120, -9, 3, (84.0, 66.0), 10, -1, 0, ()),
        (140, -12, 4, (80.0, 66.0), 8, 0, 0, ()),
        (110, -12, 5, (80.0, 67.0), 6, 1, 0, ()),
        (70, 20, 10, (121.0, 95.0), 24, -7, 4, ("thrust", "trail")),
        (70, 24, 11, (123.0, 97.0), 26, -8, 5, ("thrust", "trail")),
        (90, 22, 11, (122.0, 97.0), 28, -8, 5, ("trail",)),
        (140, 14, 8, (114.0, 92.0), 30, -5, 3, ()),
        (140, 6, 4, (104.0, 84.0), 30, -3, 1, ()),
        (150, 1, 1, (100.0, 77.0), 28, -1.5, 0, ()),
    ]
    return [(ms, P(lean=l, bob=b, hn=h, sa=s, wind=w, flare=f, fx=fx, ph=i * 0.6, spread=sp)) for i, (ms, l, b, h, s, w, f, fx) in enumerate(key)]


def anim_whip(phase):
    sp = 0.45 if phase == 2 else 0
    key = [  # the blade liquefies (blade -> 0: the code draws the lash from the hand), raised overhead, lashed down
        (110, 0, 0, (99.0, 74.0), 20, 1.0, (75.0, 70.0)),
        (110, -3, 0, (96.0, 60.0), -40, 0.7, (74.0, 68.0)),
        (110, -6, 0, (90.0, 44.0), -95, 0.35, (74.0, 66.0)),
        (120, -9, -1, (84.0, 34.0), -130, 0.1, (72.0, 64.0)),
        (140, -10, -1, (82.0, 32.0), -140, 0.0, (72.0, 64.0)),
        (70, 2, 1, (98.0, 48.0), -60, 0.0, (74.0, 68.0)),
        (70, 10, 3, (110.0, 70.0), 10, 0.0, (76.0, 70.0)),
        (80, 12, 4, (112.0, 80.0), 40, 0.0, (76.0, 70.0)),
        (120, 8, 3, (108.0, 80.0), 40, 0.0, (76.0, 70.0)),
        (120, 4, 2, (104.0, 78.0), 32, 0.4, (75.0, 70.0)),
        (120, 2, 1, (101.0, 77.0), 30, 0.8, (75.0, 70.0)),
        (140, 0, 0, (99.0, 76.0), 28, 1.0, (75.0, 70.0)),
    ]
    return [(ms, P(lean=l, bob=b, hn=h, sa=s, blade=bl, hf=hf, wind=-1.5 - (2 if 5 <= i <= 8 else 0), ph=i * 0.5, spread=sp,
                   pref_n=(0.3, 1.0) if h[1] > 50 else (1.0, 0.2))) for i, (ms, l, b, h, s, bl, hf) in enumerate(key)]


def anim_cast(phase):
    sp = 0.45 if phase == 2 else 0
    key = [  # the off hand gathers blood at her breast, then presses down: lances answer from the floor
        (110, 0, 0, (75.0, 70.0), 0.0),
        (110, -2, 0, (80.0, 58.0), 0.3),
        (120, -4, -1, (84.0, 48.0), 0.6),
        (120, -5, -1, (86.0, 42.0), 0.9),
        (120, -5, -1, (87.0, 40.0), 1.0),
        (70, 6, 3, (92.0, 76.0), 1.0),
        (90, 9, 5, (94.0, 84.0), 0.7),
        (140, 8, 5, (94.0, 84.0), 0.4),
        (140, 4, 2, (84.0, 76.0), 0.1),
        (140, 0, 0, (75.0, 70.0), 0.0),
    ]
    return [(ms, P(lean=l, bob=b, hf=h, offglow=g, pref_f=(-0.3, 1.0), ph=i * 0.5, spread=sp, wind=-1.0)) for i, (ms, l, b, h, g) in enumerate(key)]


def anim_dance(phase):
    sp = 0.45 if phase == 2 else 0
    key = [  # a pirouette: arms open, the gown flares wide; frames flip facing mid-spin
        (110, 0, 0, (104.0, 64.0), -10, (66.0, 64.0), 2, False),
        (100, -2, -1, (108.0, 56.0), -30, (62.0, 58.0), 5, False),
        (80, 0, -1, (108.0, 56.0), -30, (62.0, 58.0), 8, True),
        (80, 0, -1, (108.0, 56.0), -30, (62.0, 58.0), 10, False),
        (80, 0, -1, (108.0, 56.0), -30, (62.0, 58.0), 10, True),
        (130, 0, -1, (110.0, 58.0), -20, (60.0, 60.0), 9, False),
        (120, -1, 0, (106.0, 64.0), 0, (64.0, 64.0), 6, False),
        (120, 0, 0, (102.0, 72.0), 20, (70.0, 68.0), 3, False),
        (140, 0, 0, (100.0, 76.0), 28, (75.0, 70.0), 1, False),
        (160, 0, 0, (99.0, 76.0), 28, (75.0, 70.0), 0, False),
    ]
    return [(ms, P(lean=l, bob=b, hn=h, sa=s, hf=hf, flare=fl, mirror=mi, wind=(-4 if i % 2 else 3) * (fl / 10), ph=i * 0.9,
                   pref_f=(-1.0, 0.3), pref_n=(1.0, 0.3), spread=sp)) for i, (ms, l, b, h, s, hf, fl, mi) in enumerate(key)]


def anim_stagger(phase):
    sp = 0.3 if phase == 2 else 0
    key = [(90, -10, 2, (94.0, 82.0), 50), (110, -13, 3, (92.0, 86.0), 60), (220, -12, 3, (92.0, 86.0), 62), (220, -10, 2, (93.0, 84.0), 58)]
    return [(ms, P(lean=l, bob=b, hn=h, sa=s, head=(-1.0, 0.5), hf=(70.0, 76.0), eyes=0.6, wind=2.0, ph=i, spread=sp)) for i, (ms, l, b, h, s) in enumerate(key)]


def anim_bow(phase):
    key = [(140, 0, 0, 0), (140, 3, 2, 0.2), (140, 6, 4, 0.45), (140, 9, 6, 0.7), (160, 11, 7, 0.9), (200, 12, 8, 1.0), (300, 12, 8, 1.0), (300, 12, 8, 1.0)]
    out = []
    for i, (ms, l, b, k) in enumerate(key):
        hn = lerp((99.0, 76.0), (104.0, 92.0), k)
        hf = lerp((75.0, 70.0), (64.0, 88.0), k)
        out.append((ms, P(lean=l, bob=b, hn=hn, sa=28 + 40 * k, hf=hf, flare=4 * k, head=(0.5 * k, 0.5 * k), eyes=1.0 - 0.7 * k, ph=i * 0.4,
                           pref_f=(-1.0, 0.2), spread=0.45 if phase == 2 else 0)))
    return out


def anim_death(phase):
    out = []
    for i in range(12):
        k = min(1.0, i / 6)
        out.append((140 if i < 8 else 160, P(lean=-8 + 14 * k, bob=2 + 16 * k, hn=(96.0 + 6 * k, 84.0 + 20 * k), sa=60 + 20 * k,
                                         hf=(72.0, 80.0 + 12 * k), head=(1.0 * k, 1.5 * k), eyes=1.0 - k, flare=10 * k, ph=i * 0.4,
                                         ribbons=max(0.0, 1 - k), spread=0.3 * (1 - k) if phase == 2 else 0, wind=1.0)))
    return out


# phase-2-only
def anim_fly():
    n = 6
    return [(110, P(ph=loop_ph(i, n) * 2, fly=1.0, spread=1.0, flap=math.sin(loop_ph(i, n)), bob=-2 + 2 * math.sin(loop_ph(i, n) + 1),
                    lean=4, hn=(100.0, 72.0), sa=40, hf=(72.0, 66.0), wind=-3.0, ribbons=0.5)) for i in range(n)]


def anim_dive():
    key = [  # wings rise, then fold: a straight diving thrust
        (110, 8, -3, 1.0, 0.9, (102.0, 66.0), 30, ()),
        (110, 16, -3, 1.0, 1.0, (104.0, 66.0), 36, ()),
        (110, 26, -2, 0.8, 0.8, (108.0, 70.0), 44, ()),
        (80, 38, 0, 0.55, -0.4, (114.0, 82.0), 52, ("thrust", "trail")),
        (80, 40, 0, 0.5, -0.6, (115.0, 84.0), 54, ("thrust", "trail")),
        (80, 40, 0, 0.5, -0.6, (115.0, 84.0), 54, ("thrust", "trail")),
        (80, 40, 0, 0.5, -0.6, (115.0, 84.0), 54, ("thrust",)),
        (120, 20, 4, 0.8, 0.2, (108.0, 86.0), 50, ()),
    ]
    return [(ms, P(lean=l, bob=b, spread=s, flap=f, hn=h, sa=sa, fx=fx, fly=1.0, wind=-5.0, ph=i * 0.7, ribbons=0.3, hf=(70.0, 66.0)))
            for i, (ms, l, b, s, f, h, sa, fx) in enumerate(key)]


def anim_land():
    key = [(90, 12, 8, 0.7, 0.4), (110, 8, 6, 0.6, 0.5), (130, 4, 3, 0.55, 0.6), (140, 2, 1, 0.5, 0.8), (150, 0, 0, 0.45, 1.0), (160, 0, 0, 0.45, 1.0)]
    return [(ms, P(lean=l, bob=b, spread=s, flap=0.0, hn=(104.0, 86.0 - 8 * k), sa=40 - 12 * k, fly=0.0, ph=i * 0.6, wind=-1.0, hf=(72.0, 74.0)))
            for i, (ms, l, b, s, k) in enumerate(key)]


def anim_rain():
    out = []
    for i in range(10):
        k = min(1.0, i / 4) if i < 7 else 1.0 - (i - 6) / 4
        out.append((120 if i != 5 else 90, P(fly=1.0, spread=1.0, flap=0.4 * math.sin(i * 1.3) - 0.3 * k, lean=-4 * k, bob=-2,
                                             hf=lerp((72.0, 66.0), (80.0, 30.0), k), pref_f=(-1.0, 0.0), offglow=k,
                                             hn=(100.0, 74.0), sa=45, ph=i * 0.6, wind=-2.0, ribbons=0.6 + 0.4 * k)))
    return out


def anim_transform():
    out = []
    for i in range(10):
        k = i / 9
        out.append((120 if i < 9 else 200, P(spread=min(1.0, max(0.0, (k - 0.2) / 0.7)), flap=0.3 * math.sin(i), lean=-6 * math.sin(k * math.pi),
                                           bob=-1, hf=lerp((75.0, 70.0), (70.0, 56.0), math.sin(k * math.pi)), hn=(100.0, 76.0), sa=30,
                                           ph=i * 0.8, wind=-2.0, hair=k, ribbons=1.5, eyes=1.0)))
    return out


TAGS1 = [("idle", anim_idle, True), ("walk", anim_walk, True), ("flurry", anim_flurry, False), ("lunge", anim_lunge, False),
         ("whip", anim_whip, False), ("cast", anim_cast, False), ("vanish", None, False), ("appear", None, False),
         ("dance", anim_dance, False), ("stagger", anim_stagger, False), ("death", anim_death, False), ("bow", anim_bow, False)]
TAGS2_EXTRA = [("fly", anim_fly), ("dive", anim_dive), ("land", anim_land), ("rain", anim_rain), ("transform", anim_transform)]


def build_frames(phase):
    """-> list of (tag, [(ms, imgs, info)])"""
    out = []
    tags = [(t, f) for t, f, _ in TAGS1]
    if phase == 2:
        tags += TAGS2_EXTRA
    idle_pose = anim_idle(phase)[0][1]
    for tag, fn in tags:
        if ONLY and tag not in ONLY:
            continue
        frs = []
        if tag in ("vanish", "appear"):
            imgs0, info0 = render(dict(idle_pose, ph=0.0, ribbons=0.0), phase)
            seq = []
            for i in range(6):
                frac = (i + 1) / 6 * 1.05
                seq.append((90, dissolve(imgs0, frac, seed=3, bats=True), dict(info0, hidden=frac > 0.8)))
            if tag == "appear":
                seq = list(reversed(seq))[1:] + [(120, imgs0, info0)]
            frs = seq
        else:
            for i, (ms, p) in enumerate(fn(phase) if fn not in [f for _, f in TAGS2_EXTRA] else fn()):
                imgs, info = render(p, phase, i)
                if p["mirror"]:
                    imgs = mirror_imgs(imgs)
                    for k in ("hand_n", "hand_f", "tip", "cup"):
                        if k in info:
                            info[k] = mirror_pt(info[k])
                    info["hurt_px"] = {mirror_pt(q) for q in info["hurt_px"]}
                    info["blade_px"] = {mirror_pt(q) for q in info.get("blade_px", set())}
                if tag == "death" and i >= 7:
                    imgs = dissolve(imgs, (i - 6) / 5 * 1.1, seed=11, blood=True)
                frs.append((ms, imgs, info))
        out.append((tag, frs))
    return out


def rect_of(pts, pad=0):
    pts = [q for q in pts if inb(*q)]
    if not pts:
        return None
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    x0, y0, x1, y1 = max(0, min(xs) - pad), max(0, min(ys) - pad), min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def hit_from_blade(info, down=12):
    r = rect_of(info.get("blade_px", set()) | {ip(info["tip"])}, pad=3)
    if r is None:
        return None
    x, y, w, h = r
    # reach low enough for a 10x26 knight standing on the floor in front of her
    y1 = min(FLOOR + 1, y + h + down)
    return [x, y, w, y1 - y]


def make_meta(frames_by_tag):
    fm = {}
    hb_all = []
    for tag, frs in frames_by_tag:
        lst = []
        for ms, imgs, info in frs:
            hb = rect_of(info["hurt_px"], pad=0) if not info.get("hidden") else None
            if hb:
                # the torso and skirt, not the train/wing tips
                hb = [max(hb[0], AX - 18), hb[1], min(hb[2], 36), hb[3]]
                hb_all.append(hb)
            e = {"hb": hb or [AX - 10, 40, 20, 88]}
            if "hand_n" in info:
                e["hand"] = [round(info["hand_n"][0], 1), round(info["hand_n"][1], 1)]
            if "hand_f" in info:
                e["off"] = [round(info["hand_f"][0], 1), round(info["hand_f"][1], 1)]
            if "tip" in info:
                e["tip"] = [round(info["tip"][0], 1), round(info["tip"][1], 1)]
            if tag == "dive":
                e["hit"] = hit_from_blade(info, down=8) or e["hb"]
            lst.append(e)
        fm[tag] = lst
    meta = {"native": 1, "anchor": [AX, AY], "hurtbox": [AX - 12, 40, 26, 88], "frames": fm, "attacks": {}, "spawn": {}, "telegraph": {}}
    by = {t: frs for t, frs in frames_by_tag}
    if "flurry" in by:
        meta["attacks"]["flurry"] = {"windows": [{"active": [i, i], "hit": hit_from_blade(by["flurry"][i][2])} for i in (3, 6, 9)]}
        meta["telegraph"]["flurry"] = {"frame": 1, "at": list(map(round, by["flurry"][1][2]["tip"]))}
    if "lunge" in by:
        rs = [hit_from_blade(by["lunge"][i][2]) for i in (4, 5, 6)]
        x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs); x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
        meta["attacks"]["lunge"] = {"active": [4, 6], "hit": [x0 - 6, y0, x1 - x0 + 6, y1 - y0]}
        meta["telegraph"]["lunge"] = {"frame": 2, "at": list(map(round, by["lunge"][2][2]["tip"]))}
    meta["attacks"]["whip"] = {"active": [6, 8]}
    meta["telegraph"]["whip"] = {"frame": 3, "at": [84, 30]}
    meta["spawn"]["cast"] = {"frame": 5, "at": [94, 84]}
    meta["spawn"]["dance"] = {"frame": 5, "at": [AX, 70]}
    meta["spawn"]["rain"] = {"frame": 4, "at": [80, 30]}
    meta["attacks"]["dive"] = {"active": [3, 6]}
    return meta


def preview(name, frames_by_tag, meta, scale=3):
    rows = frames_by_tag
    cols = max(len(f) for _, f in rows)
    pad, lab = 2, 10
    sheet = Image.new("RGBA", ((cols * (W + pad)) * scale, len(rows) * (H + pad + lab) * scale), (86, 86, 94, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, frs) in enumerate(rows):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 2), f"{t} ({len(frs)})", fill=(235, 235, 240, 255))
        wins = []
        a = meta["attacks"].get(t)
        if a:
            wins = a.get("windows") or [a]
        for i, (ms, imgs, info) in enumerate(frs):
            fr = Image.new("RGBA", (W, H), (74, 74, 82, 255))
            fr.alpha_composite(flatten(imgs, LAYERS2 if "WingFar" in imgs else LAYERS1))
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            dd = ImageDraw.Draw(big)
            if os.environ.get("SG_BOXES"):
                hb = meta["frames"][t][i]["hb"]
                dd.rectangle([hb[0] * scale, hb[1] * scale, (hb[0] + hb[2]) * scale - 1, (hb[1] + hb[3]) * scale - 1], outline=(60, 230, 90, 255))
                for w in wins:
                    if w.get("hit") and w["active"][0] <= i <= w["active"][1]:
                        x, y, ww, hh = w["hit"]
                        dd.rectangle([x * scale, y * scale, (x + ww) * scale - 1, (y + hh) * scale - 1], outline=(255, 50, 50, 255), width=2)
                        dd.rectangle([(x + ww - 6) * scale, (H - 26) * scale, (x + ww + 4) * scale - 1, H * scale - 1], outline=(90, 150, 255, 255))
                if t == "dive" and "hit" in meta["frames"][t][i]:
                    x, y, ww, hh = meta["frames"][t][i]["hit"]
                    dd.rectangle([x * scale, y * scale, (x + ww) * scale - 1, (y + hh) * scale - 1], outline=(255, 120, 50, 255))
            sheet.alpha_composite(big, (i * (W + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", name))


def export(name, frames_by_tag, layers, meta=None):
    frames, tags = [], []
    for tag, frs in frames_by_tag:
        a = len(frames)
        for ms, imgs, info in frs:
            frames.append({"ms": ms, "cels": {n: imgs[n] for n in layers if n in imgs}})
        tags.append((tag, a, len(frames) - 1))
    if BUILD:
        import asebuild
        asebuild.build(name, W, H, layers, frames, tags)


def closeup(frames_by_tag, name, picks, scale=6):
    by = {t: f for t, f in frames_by_tag}
    ims = []
    for t, i in picks:
        if t in by and i < len(by[t]):
            ims.append(flatten(by[t][i][1], LAYERS2 if "WingFar" in by[t][i][1] else LAYERS1))
    if not ims:
        return
    sheet = Image.new("RGBA", (len(ims) * W * scale, H * scale), (86, 86, 94, 255))
    for k, im in enumerate(ims):
        fr = Image.new("RGBA", (W, H), (86, 86, 94, 255))
        fr.alpha_composite(im)
        sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), (k * W * scale, 0))
    sheet.save(os.path.join(ART, "previews", name))


def main():
    f1 = build_frames(1)
    meta = make_meta(f1)
    preview("sanguine.png", f1, meta)
    closeup(f1, "sanguine_closeup.png", [("idle", 0), ("flurry", 6), ("lunge", 5), ("whip", 4), ("cast", 4), ("bow", 6)], scale=4)
    f2 = build_frames(2)
    meta2 = make_meta(f2)
    for t in ("fly", "dive", "land", "rain", "transform"):
        if t in meta2["frames"]:
            meta["frames"][t] = meta2["frames"][t]
    preview("sanguine_p2.png", f2, meta)
    closeup(f2, "sanguine_p2_closeup.png", [("idle", 0), ("fly", 1), ("dive", 4), ("rain", 5), ("lunge", 5)], scale=4)
    if ONLY is None:
        with open(os.path.join(ART, "..", "assets", "sanguine_meta.json"), "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
        export("sanguine", f1, LAYERS1)
        export("sanguine_p2", f2, LAYERS2)


if __name__ == "__main__":
    main()
