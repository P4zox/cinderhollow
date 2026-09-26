#!/usr/bin/env python3
"""Countess Sanguine, the Vampire Queen-Knight (agent C, The Crimson Manor) -- main boss, redesign v2.

    python3 art/gen_crimson_sanguine.py [--preview] [--only idle,slash1]

A commanding vampire queen-knight: broad layered black-steel pauldrons with silver rims, a high structured crimson
collar, a black cuirass with a blood-gem heart, armoured faulds over a heavy crimson gown that falls to the floor, a long
tattered cape, long black hair, a thorned iron crown, a pale sharp face with glowing red eyes; she wields a long
blade of solidified blood (a hand-and-a-half greatsword with a swept silver guard).  Phase 2 (`sanguine_p2`): the gown
becomes a torrent of blood, blood wings, the crown burns, the blade blazes.

One rig for every frame: fixed segment lengths (upper arm 15, forearm 14), head/cuirass/pauldrons are rigid and only
rotated about the waist (lean) and moved (bob / dx); the skirt always reaches the floor row, so there are no feet to slide.
Faces RIGHT.  Frame 224x160, anchor [104, 160].

Outputs: art/sanguine(.aseprite), assets/sanguine.png/.json, art/sanguine_p2(.aseprite), assets/sanguine_p2.png/.json,
assets/sanguine_meta.json, previews art/previews/sanguine*.png.
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, n_capsule, n_dome, n_plate, poly_mask, line, polyline, bezier, ik,  # noqa: E402
                       mask_disc, ip, hash01, add, sub, lerp, dirv, rot_pt, render_layer, flatten, inb)
from PIL import Image, ImageDraw  # noqa: E402

W, H = 224, 160
K.setup(W, H)
AX, AY = 104, 160
FLOOR = 159
BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

NEW = {
    "S": ["#2a1f2b", "#4d3b4c", "#7e6875", "#b3a0a6", "#dccfcc", "#f6efe8"],       # porcelain skin
    "N": ["#140409", "#2a0812", "#450d1c", "#661326", "#8c1c32", "#b02c3e"],       # crimson velvet
    "H": ["#060509", "#0f0c15", "#1a1623", "#282336", "#3b3550", "#57507a"],       # black hair, violet sheen
    "Z": ["#2e040c", "#5c0816", "#920f22", "#c82032", "#f0505a", "#ffb0a8"],       # blood crystal
    "U": ["#17161d", "#302f3a", "#55546a", "#86859a", "#bab9cc", "#eeeef8"],       # silver
    "E": ["#5a0008", "#b0101a", "#ff2e2e", "#ff8a78", "#fff0e6"],                  # glows
}
for r, cols in NEW.items():
    keys = []
    for i, c in enumerate(cols):
        k = f"{r}{i}"
        K.HEX[k] = c
        K.RGBA[k] = tuple(int(c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        keys.append(k)
    K.RAMP[r] = keys
K.SHINY.update({"Z": 0.88, "U": 0.9, "K": 0.9})
RGBA = K.RGBA
_lvl0 = K.level_of


def _level(e, x, y):   # porcelain stays pale; armour keeps a readable mid-tone
    i = _lvl0(e, x, y)
    if e[0] == "S" and not isinstance(e[3], tuple):
        i = min(5, i + 1 + (1 if i <= 1 else 0))
    if e[0] == "K" and not isinstance(e[3], tuple) and i == 0:
        i = 1
    return i


K.level_of = _level

LAYERS1 = ["FXBack", "Cape", "Hair", "Gown", "ArmFar", "Collar", "Body", "Head", "ArmNear", "Sword", "Glow", "FX"]
LAYERS2 = ["FXBack", "WingFar", "WingNear", "Cape", "Hair", "Gown", "ArmFar", "Collar", "Body", "Head", "ArmNear", "Sword", "Glow", "FX"]

# ------------------------------------------------------------------ rig (upright model coords, facing right)
WA = (104.0, 98.0)
REST = dict(Hd=(108.5, 60.0), Nk=(106.5, 68.5), Sn=(115.5, 75.0), Sf=(97.0, 74.5), Ch=(106.0, 83.0), Hip=(104.0, 106.0))
L1, L2 = 15.0, 14.0
BLADE = 58.0
GRIP = 7.0

BASE = dict(lean=0.0, bob=0.0, dx=0.0, head=(0.0, 0.0),
            hn=(128.0, 104.0), sa=20.0, hf=(96.0, 104.0), pref_n=(0.2, 1.0), pref_f=(-0.7, 0.8),
            two=False, blade=1.0, flare=0.0, wind=0.0, ph=0.0, eyes=1.0, spread=0.0, flap=0.0, fly=0.0,
            fx=(), mirror=False, offglow=0.0, claw=False, crownfire=0.0, aura=0.0, hair=0.0)


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
    return h if d <= l else lerp(s, h, l / d)


def rim(L, m, col, sides=((1, 0), (-1, 0), (0, 1), (0, -1))):
    e = {q for q in m if any((q[0] + a, q[1] + b) not in m for a, b in sides)}
    L.decal(e, col)
    return e


# ------------------------------------------------------------------ parts
def draw_head(L, G, F, j, p, phase):
    Hd = j["Hd"]
    Hl = L["Head"]
    Hl.paint(n_capsule(j["Nk"], add(Hd, (-0.5, 4.5)), 2.8, 2.6), "S", bias=-1)
    head = n_dome(Hd, 5.6, 6.8, tilt=(0.3, -0.1))
    Hl.paint(head, "S")
    Hl.paint(n_dome(add(Hd, (3.0, 4.4)), 2.9, 2.5), "S", ao=0)                      # strong jaw
    Hl.paint(n_capsule(add(Hd, (5.0, -1.2)), add(Hd, (6.6, 1.2)), 0.9, 1.0), "S", ao=0)   # nose
    # hair: swept back from a widow's peak; the face stays bare; the long fall is on the Hair layer
    cap = n_dome(add(Hd, (-1.6, -2.0)), 6.2, 6.3, tilt=(-0.1, -0.1))
    capm = {q: v for q, v in cap.items() if (q[0] + .5 - Hd[0]) < -0.6 - (q[1] + .5 - Hd[1]) * 0.75 or (q[1] + .5 - Hd[1]) < -4.8}
    capm = {q: v for q, v in capm.items() if q[1] < Hd[1] + 3.0}
    Hl.paint(capm, "H", ao=0)
    Hl.decal(line(add(Hd, (-3.0, -4.6)), add(Hd, (3.5, -5.2))), ("H", 3))
    # crown of thorned black iron with a blood gem; it burns in phase 2
    ca, cb = add(Hd, (-5.8, -5.2)), add(Hd, (4.0, -6.8))
    band = set(line(ca, cb)) | set(line(add(ca, (0, 1)), add(cb, (0, 1))))
    Hl.paint({q: (-0.2, -0.5, 0.8) for q in band}, "K", ao=0)
    Hl.decal(set(line(ca, cb)), ("U", 3))
    for k, (t, ang, ln) in enumerate([(0.05, -122, 5), (0.3, -106, 8), (0.55, -92, 12), (0.78, -80, 8), (0.98, -64, 5)]):
        base = lerp(ca, cb, t)
        tip = add(base, (dirv(ang)[0] * ln, dirv(ang)[1] * ln))
        for i, q in enumerate(line(base, tip)):
            Hl.paint({q: (-0.4, -0.5, 0.75)}, "K", ao=0)
            if i < 2:
                Hl.paint({(q[0] + 1, q[1]): (-0.4, -0.5, 0.75)}, "K", ao=0)
        G.put([ip(tip)], "U5" if phase == 1 and k != 2 else "E3")
        if phase == 2 or p["crownfire"] > 0:
            for i in range(3):
                F.put([ip((tip[0] + math.sin(p["ph"] * 3 + k + i) * 1.2, tip[1] - 1 - i * 1.5))], "E2" if i < 2 else "Z4")
    gem = ip(lerp(ca, cb, 0.55))
    G.put([gem, (gem[0], gem[1] - 1)], "E2")
    # face: a stern brow, a burning eye, dark lips, the shadow under the cheekbone
    ex, ey = ip(add(Hd, (3.0, -0.9)))
    Hl.decal([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey - 2)], "H2")
    e = p["eyes"]
    if e > 0.2:
        G.put([(ex, ey), (ex + 1, ey)], "E3" if phase == 1 else "E4")
        if phase == 2 and e > 0.6:
            F.put([(ex - 1, ey + 1), (ex - 2, ey + 1), (ex - 3, ey + 2)], "E1")
    else:
        Hl.decal([(ex, ey), (ex + 1, ey)], "H1")
    lp = ip(add(Hd, (5.0, 3.4)))
    Hl.decal([lp, (lp[0] - 1, lp[1])], "Z1")
    Hl.decal([ip(add(Hd, (1.0, 2.2))), ip(add(Hd, (1.4, 3.2)))], ("S", 3))
    Hl.decal([ip(add(Hd, (0.4, 1.4))), ip(add(Hd, (0.8, 2.6)))], ("S", 2))


def draw_hair(L, j, p, phase):
    """Long black hair falling down her back over the cape (streams wild in phase 2)."""
    Hd = j["Hd"]
    Hr = L["Hair"]
    ph, wind = p["ph"], p["wind"]
    k2 = 1.0 if phase == 2 else p["hair"]
    root = add(Hd, (-4.5, -2.0))
    lp, rp = [], []
    n = 16
    ln = 46
    for i in range(n + 1):
        t = i / n
        wv = math.sin(ph - t * 3.2) * (0.6 + 2.6 * t)
        cx = root[0] - 4 * t - 3 * t * t + wind * 0.55 * t * t + wv - k2 * 16 * t * t
        cy = root[1] + ln * t * (1 - 0.45 * k2) - k2 * 6 * t
        hw = 3.2 + 3.0 * t * (1 - t) * 2
        lp.append((cx - hw, cy))
        rp.append((cx + hw * 0.7, cy - t))
    tip = (lp[-1][0] + 1 - k2 * 3, lp[-1][1] + 3)
    m = poly_mask(lp + [tip] + list(reversed(rp)))
    Hr.paint(n_plate(m, bevel=2.5, strength=0.9, fold=lambda x, y: (0.6 * math.sin((x - root[0]) * 1.1 + y * 0.2 - ph), 0)), "H")
    for s in range(3):
        pts = [lerp(lp[i], rp[i], 0.3 + s * 0.2) for i in range(2, n)]
        Hr.decal(polyline(pts)[::2], ("H", 3 + (s == 1)))


def draw_collar(L, j, p, phase):
    """High structured collar: black steel gorget and two stiff crimson wings rising behind the head."""
    X = j["X"]
    Cl = L["Collar"]
    poly = [X(q) for q in ((98.0, 72.0), (93.0, 64.0), (90.5, 50.0), (95.5, 55.5), (99.0, 46.0), (102.0, 55.0), (106.0, 52.5),
                           (105.0, 62.0), (111.0, 69.5))]
    m = poly_mask(poly)
    Cl.paint(n_plate(m, bevel=2.2, tilt=(-0.2, -0.15), strength=1.1, fold=lambda x, y: (0.25 * math.sin(x * 1.1), 0)), "N", bias=0)
    rim(Cl, m, ("K", 2), ((-1, 0), (0, -1), (1, 0)))
    for q in ((90.5, 50.0), (99.0, 46.0)):
        Cl.fill([ip(X(q))], "U4")
    # gorget: a steel ring around the throat
    Cl.paint(n_capsule(X((101.0, 70.5)), X((111.0, 69.0)), 2.6, 2.6), "K", ao=0)
    Cl.decal(line(X((101.0, 69.0)), X((111.0, 67.5))), ("U", 3))


def draw_body(L, G, j, p, phase):
    X = j["X"]
    B = L["Body"]
    cu = [X(q) for q in ((96.0, 70.0), (114.0, 69.0), (119.0, 74.0), (120.0, 81.0), (116.5, 88.0), (111.5, 95.5), (112.5, 99.5),
                         (96.5, 99.5), (97.0, 94.0), (94.0, 87.0), (92.5, 80.0), (94.0, 73.5))]
    cm = poly_mask(cu)
    B.paint(n_plate(cm, bevel=5.0, tilt=(0.15, -0.05), strength=1.5), "K")
    B.paint(n_dome(X((114.0, 80.5)), 5.0, 5.0, tilt=(0.2, 0.0)), "K", ao=0, clip=cm)     # breastplate swell
    # crimson tabard panel down the front, under the silver V
    tb = poly_mask([X((103.0, 86.0)), X((110.0, 86.0)), X((108.5, 99.5)), X((104.0, 99.5))]) & cm
    B.paint(n_plate(tb, bevel=1.5, strength=0.6), "N", ao=0)
    # silver filigree: a centre ridge and a V down to the waist
    B.decal(line(X((108.0, 71.0)), X((106.5, 98.0))), ("U", 3))
    B.decal(line(X((97.0, 73.0)), X((106.0, 92.0))), ("U", 2))
    B.decal(line(X((118.0, 76.0)), X((107.5, 92.0))), ("U", 2))
    rim(B, cm, ("U", 2), ((0, 1),))
    # the blood-gem heart, set in silver
    gm = X((111.5, 81.0))
    B.paint(n_dome(gm, 2.4, 2.6), "U", ao=0)
    G.put([ip(gm), ip(add(gm, (0, 1))), ip(add(gm, (-1, 0)))], "E2" if phase == 1 else "E3")
    G.put([ip(add(gm, (0.6, -0.8)))], "E4")
    # belt
    B.paint({q: (0, -0.4, 0.9) for q in set(line(X((95.0, 98.0)), X((113.0, 98.0)))) | set(line(X((95.0, 99.0)), X((113.0, 99.0))))}, "N", ao=0)
    B.fill([ip(X((104.0, 98.5)))], "U4")
    return cm


def gown_poly(j, p):
    X = j["X"]
    ph, wind, fl = p["ph"], p["wind"], p["flare"]
    tl, tr = X((94.5, 100.0)), X((114.0, 100.0))
    fr = (148.0 + fl + wind * 0.3 + p["dx"] * 0.6, FLOOR)
    bk = (62.0 - fl * 0.7 + wind * 0.5 + p["dx"] * 0.6, FLOOR)
    right = bezier(tr, (122.0 + p["dx"] * 0.4, 118.0), (fr[0] - 6 + wind * 0.2, 142.0), fr, 14)
    left = bezier(tl, (86.0 + p["dx"] * 0.3, 120.0), (bk[0] + 5, 142.0), bk, 14)
    hem = []
    for i in range(33):
        t = i / 32
        x = fr[0] + (bk[0] - fr[0]) * t
        y = FLOOR - 0.6 - 1.1 * abs(math.sin(ph + t * 10.0)) * (0.5 + t)
        hem.append((x, y))
    return right + hem[1:-1] + list(reversed(left)), (tl, tr, fr, bk)


def draw_gown(L, F, j, p, phase, info):
    poly, (tl, tr, fr, bk) = gown_poly(j, p)
    m = {q for q in poly_mask(poly) if q[1] <= FLOOR}
    Gw = L["Gown"]
    ph = p["ph"]
    Wa = j["Wa"]
    if phase == 1:
        def fold(x, y):
            t = max(0.0, min(1.0, (y - Wa[1]) / max(1.0, FLOOR - Wa[1])))
            cx = lerp(Wa, ((fr[0] + bk[0]) / 2, FLOOR), t)[0]
            hw = 8 + (fr[0] - bk[0]) / 2 * t
            u = (x + .5 - cx) / hw
            return (0.55 * math.sin(u * 2.6 * math.pi + math.sin(ph - t * 2.0) * 0.7) * (0.25 + t), 0.0)
        Gw.paint(n_plate(m, bevel=8, tilt=(0.05, -0.05), strength=1.2, fold=fold), "N")
        # front slit: black underskirt
        o0, o1 = j["X"]((110.0, 104.0)), j["X"]((113.0, 104.0))
        wedge = poly_mask([o0, o1, (fr[0] - 6, FLOOR + 1), (fr[0] - 20, FLOOR + 1)]) & m
        Gw.paint(n_plate(wedge, bevel=2, strength=0.7), "K", bias=-1, ao=0)
        rim(Gw, wedge, ("U", 2), ((1, 0), (-1, 0)))
        rows = {}
        for (x, y) in m:
            rows[x] = max(rows.get(x, -1), y)
        for x, y in rows.items():
            if y >= FLOOR - 2:
                Gw.decal([(x, y), (x, y - 1)], ("K", 1))
                if (x + int(ph * 2)) % 4 == 0:
                    Gw.decal([(x, y - 2)], ("U", 2))
    else:
        draw_torrent(Gw, F, m, j, p, fr, bk)
    # armoured tassets: a side plate and a front plate hanging from the belt, pointed, silver-rimmed
    X = j["X"]
    Fl = L["Gown"]
    short = phase == 2 and p["fly"] > 0.5
    ln = 0.7 if short else 1.0
    side = [X((93.5, 99.5)), X((110.0, 99.5)), X((111.5, 99.5 + 25 * ln)), X((101.0, 99.5 + 29 * ln)), X((92.0, 99.5 + 22 * ln))]
    front = [X((106.0, 99.5)), X((115.5, 99.5)), X((125.5, 99.5 + 24 * ln)), X((118.5, 99.5 + 30 * ln)), X((110.0, 99.5 + 25 * ln))]
    for poly2, tl in ((side, (-0.1, 0.1)), (front, (0.25, 0.05))):
        fm = poly_mask(poly2)
        Fl.paint(n_plate(fm, bevel=2.5, tilt=tl, strength=1.3), "K", ao=1)
        rim(Fl, fm, ("U", 2))
        for yk in (8, 16):
            a_ = lerp(poly2[0], poly2[4], yk / 26.0)
            b_ = lerp(poly2[1], poly2[2], yk / 26.0)
            Fl.decal(line(a_, b_)[1:-1], ("K", 1))
        c0 = lerp(poly2[0], poly2[1], 0.5)
        Fl.decal(line(c0, lerp(c0, poly2[3], 0.85))[2:], ("N", 3))
    info["gown"] = m


def draw_torrent(Gw, F, m, j, p, fr, bk):
    ph = p["ph"]
    fly = p["fly"]
    Wa = j["Wa"]
    if fly > 0:
        tip = (Wa[0] - 22 - p["wind"] * 1.2 + math.sin(ph) * 4, FLOOR - 6 - 8 * fly)
        l = [j["X"]((92.0, 100.0)), (Wa[0] - 14, Wa[1] + 30), (tip[0] + 2, tip[1] - 12), tip]
        r = [tip, (tip[0] + 14, tip[1] - 16), (Wa[0] + 16, Wa[1] + 30), j["X"]((116.0, 100.0))]
        m = poly_mask(bezier(*l, 14) + bezier(*r, 14)) | {q for q in m if q[1] < Wa[1] + 8}
    nm = {}
    for q in m:
        x, y = q
        s = math.sin(x * 0.45 + math.sin(y * 0.1 + ph) * 1.3)
        nm[q] = K.norm3(0.5 * s, -0.15, 1.0)
    Gw.paint(nm, "Z", bias=-2)
    for (x, y) in m:
        v = x * 0.8 + math.sin(y * 0.18 + x) * 0.8
        band = math.sin(v * 1.2 + math.sin(y * 0.08 + ph) * 1.5) > 0.9
        flow = (y * 0.45 - ph * 6.0 + hash01(x, 0, 7) * 9.0) % 9.0
        if band and flow < 2.5:
            Gw.decal([(x, y)], ("Z", 4 if flow < 0.8 else 3))
        elif band and flow < 5:
            Gw.decal([(x, y)], ("Z", 2))
    rim(Gw, m, ("Z", 1), ((1, 0), (-1, 0)))
    if fly < 0.5:
        for k in range(12):
            a = hash01(k, int(ph * 3), 3)
            x = bk[0] + (fr[0] - bk[0]) * a
            h = 2 + 4 * hash01(k, int(ph * 5), 9)
            F.put([ip((x + math.sin(ph + k) * 2, FLOOR - h))], "Z4" if k % 3 == 0 else "Z3")
        for x in range(int(bk[0]) - 8, int(fr[0]) + 9):
            if inb(x, FLOOR):
                F.put([(x, FLOOR)], "Z2" if (x + int(ph * 4)) % 5 else "Z3")
    else:
        for k in range(5):
            t = (ph * 0.6 + k * 0.2) % 1.0
            F.put([ip((Wa[0] - 8 + k * 3 - p["wind"] * 0.4, Wa[1] + 34 + t * 30 + i)) for i in range(2)], "Z3")


def draw_cape(L, j, p, phase):
    """A long tattered cape from the shoulders to the floor behind her; crimson lining shows at the edges."""
    X = j["X"]
    Cp = L["Cape"]
    ph, wind = p["ph"], p["wind"]
    a0, a1 = X((96.0, 70.0)), X((104.0, 69.0))
    drop = FLOOR if not (phase == 2 and p["fly"] > 0.5) else FLOOR - 24
    back = (50.0 + wind * 1.6 - p["flare"] * 0.4 + p["dx"] * 0.4, drop - 2 - abs(wind) * 0.6)
    left = bezier(a0, (a0[0] - 14 + wind * 0.3, a0[1] + 22), (back[0] + 10, drop - 26), back, 14)
    hem = []
    for i in range(1, 16):
        t = i / 15
        x = back[0] + (88.0 + p["dx"] * 0.6 - back[0]) * t
        tear = (hash01(i, 0, 17) * 6 + 2 * math.sin(ph + i)) if i % 3 else 0.0
        hem.append((x, min(FLOOR, drop - tear * (1 - t * 0.5))))
    right = [(90.0 + p["dx"] * 0.5, drop - 30), X((100.0, 90.0)), a1]
    m = poly_mask(left + hem + right)
    m = {q for q in m if q[1] <= FLOOR}
    Cp.paint(n_plate(m, bevel=4, tilt=(0.1, -0.2), strength=1.0,
                     fold=lambda x, y: (0.5 * math.sin((x + y * 0.5) * 0.35 + ph), 0.0)), "K", bias=-1)
    edge = {q for q in m if (q[0] - 1, q[1]) not in m or (q[0], q[1] + 1) not in m}
    Cp.decal(edge, ("N", 3))
    Cp.decal({(q[0] + 1, q[1]) for q in edge if (q[0] + 1, q[1]) in m and (q[0] + 1, q[1]) not in edge}, ("N", 2))


def draw_arm(L, G, F, j, p, side, phase, info):
    near = side == "n"
    sh = j["Sn"] if near else j["Sf"]
    Lr = L["ArmNear"] if near else L["ArmFar"]
    bias = 0 if near else -1
    target = p["hn"] if near else p["hf"]
    hand = reach(sh, target, L1 + L2 - 0.4)
    el = ik(sh, hand, L1, L2, p["pref_n"] if near else p["pref_f"])
    Lr.paint(n_capsule(sh, el, 3.4, 3.0), "K", bias=bias)                   # rerebrace
    Lr.paint(n_dome(el, 3.2, 3.2), "K", bias=bias, ao=0)                     # couter
    Lr.paint(n_capsule(el, hand, 3.0, 2.6), "K", bias=bias)                  # vambrace
    fa = K.norm3(hand[0] - el[0], hand[1] - el[1], 0)
    Lr.decal(line(el, lerp(el, hand, 0.8)), ("U", 2 if near else 1))
    # a flared silver-rimmed gauntlet cuff and the gauntlet
    cuff = sub(hand, (fa[0] * 3.0, fa[1] * 3.0))
    Lr.paint(n_dome(cuff, 3.3, 3.3), "K", bias=bias, ao=0)
    rim(Lr, mask_disc(cuff, 3.3), ("U", 3 if near else 2))
    Lr.paint(n_dome(hand, 2.8, 2.8), "K", bias=bias, ao=0)
    if p["claw"] and not near:
        for off in (-35, 0, 35):
            dd = dirv(math.degrees(math.atan2(fa[1], fa[0])) + off)
            Lr.paint({q: (0, -0.5, 0.8) for q in line(add(hand, (dd[0] * 2, dd[1] * 2)), add(hand, (dd[0] * 6, dd[1] * 6)))}, "U", bias=bias, ao=0)
    # the pauldron: three curved steel lames stacked over the shoulder, silver-rimmed, an upswept flange and a thorn
    lames = []
    for k in range(3):
        c = add(sh, (0.8 + 0.9 * k, -2.5 + 3.8 * k))
        R = 8.6 - 1.3 * k
        up, lo = [], []
        for i in range(15):
            a = math.radians(196 + i * (148 / 14))
            up.append((c[0] + math.cos(a) * R * 1.02, c[1] + math.sin(a) * R * 0.66))
            lo.append((c[0] + math.cos(a) * R * 1.08, c[1] + math.sin(a) * R * 0.66 + 4.4 - 0.4 * k))
        lames.append(poly_mask(up + list(reversed(lo))))
    for k in (2, 1, 0):
        m = lames[k]
        Lr.paint(n_plate(m, bevel=2.0, tilt=(-0.05, -0.35 + 0.2 * k), strength=1.3), "K", bias=bias, ao=1)
        rim(Lr, m, ("U", 3 if near else 2), ((0, 1),))
        rim(Lr, m, ("U", 2 if near else 1), ((1, 0),))
    top = add(sh, (-3.0, -8.0))
    fl = poly_mask([add(sh, (-6.0, -5.0)), add(sh, (-5.0, -8.5)), add(sh, (-10.0, -12.5)), add(sh, (-1.0, -7.8)), add(sh, (4.0, -7.4))])
    Lr.paint(n_plate(fl, bevel=1.2, tilt=(-0.3, -0.5), strength=1.0), "K", bias=bias, ao=0)
    Lr.fill([ip(add(sh, (-10.0, -12.5)))], "U4" if near else "U3")
    info["hand_" + side] = hand
    return hand


def draw_sword(L, G, F, j, p, info, phase):
    """The blood blade: long crystalline blade, swept silver guard, a heavy grip for two hands."""
    Sw = L["Sword"]
    hand = info["hand_n"]
    d = dirv(p["sa"])
    perp = (-d[1], d[0])
    pom = sub(hand, (d[0] * (GRIP - 2), d[1] * (GRIP - 2)))
    Sw.paint(n_dome(pom, 1.8, 1.8), "U", ao=0)
    Sw.paint(n_capsule(pom, hand, 1.1, 1.1), "N", ao=0)
    gd = add(hand, (d[0] * 3.0, d[1] * 3.0))
    q0 = add(gd, (perp[0] * 6.5 - d[0] * 2.5, perp[1] * 6.5 - d[1] * 2.5))
    q1 = add(gd, (-perp[0] * 6.5 - d[0] * 2.5, -perp[1] * 6.5 - d[1] * 2.5))
    for a, b in ((gd, q0), (gd, q1)):
        Sw.paint({q: (-0.3, -0.5, 0.8) for q in line(a, b)}, "U", ao=0)
    Sw.paint(n_dome(gd, 2.0, 2.0), "U", ao=0)
    G.put([ip(gd)], "E2")
    ln = BLADE * p["blade"]
    b0 = add(gd, (d[0] * 1.5, d[1] * 1.5))
    tip = add(b0, (d[0] * ln, d[1] * ln))
    blade = set()
    if ln > 2:
        n = int(ln)
        for i in range(n + 1):
            t = i / n
            c = add(b0, (d[0] * ln * t, d[1] * ln * t))
            hw = 1.8 * (1 - t) ** 0.6 + 0.35
            for q in mask_disc(c, max(0.55, hw)):
                blade.add(q)
        core = line(add(b0, (perp[0] * -0.3, perp[1] * -0.3)), lerp(b0, tip, 0.93))
        Sw.paint({q: (perp[0] * 0.3 - 0.2, perp[1] * 0.3 - 0.6, 0.75) for q in blade}, "Z", ao=0)
        Sw.decal(core, ("Z", 4 if phase == 1 else 5))
        edge = [q for q in blade if (q[0] + round(perp[0]), q[1] + round(perp[1])) not in blade]
        Sw.decal(edge, ("Z", 2))
        G.put([ip(tip)], "Z5")
        if phase == 2 or p["aura"] > 0:
            for i in range(0, n, 3):
                t = i / n
                c = add(b0, (d[0] * ln * t, d[1] * ln * t))
                if hash01(i, int(p["ph"] * 4), 5) < 0.55:
                    F.put([ip(add(c, (perp[0] * 3, perp[1] * 3 - 1)))], "Z4" if i % 2 else "E2")
    info["blade_px"] = blade
    info["tip"] = tip
    info["b0"] = b0


def draw_smear(F, Fb, info, prev, p):
    """A crescent band of blood light swept by the blade tip between the previous frame and this one."""
    if not prev or "tip" not in prev:
        return
    pv = info["b0"]
    a0 = math.atan2(prev["tip"][1] - prev["b0"][1], prev["tip"][0] - prev["b0"][0])
    a1 = math.atan2(info["tip"][1] - pv[1], info["tip"][0] - pv[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    if abs(da) < 0.12:
        return
    R = math.hypot(info["tip"][0] - pv[0], info["tip"][1] - pv[1]) + 1.5
    for y in range(int(pv[1] - R) - 1, int(pv[1] + R) + 2):
        for x in range(int(pv[0] - R) - 1, int(pv[0] + R) + 2):
            dx, dy = x + .5 - pv[0], y + .5 - pv[1]
            r = math.hypot(dx, dy) / R
            if r > 1.0 or r < 0.7:
                continue
            ang = math.atan2(dy, dx)
            t = ((ang - a0 + math.pi) % (2 * math.pi) - math.pi) / da
            if t < 0 or t > 1:
                continue
            if hash01(x, y, 9) < (1 - t) * 0.75 * (1.2 - r):
                continue
            c = "Z5" if r > 0.955 and t > 0.55 else "Z4" if r > 0.9 else "Z3" if r > 0.8 else "Z2"
            if c == "Z2" and t < 0.6:
                continue
            F.put([(x, y)], c)


# ------------------------------------------------------------------ phase 2 wings
def draw_wings(L, F, j, p, info):
    sp = p["spread"]
    if sp <= 0.02:
        return
    ph, flap = p["ph"], p["flap"]
    X = j["X"]
    root = X((98.0, 80.0))
    body_end = X((97.0, 98.0))
    for side, name in ((0, "WingFar"), (1, "WingNear")):
        Lw = L[name]
        bias = -1 if side == 0 else 0
        sc = (0.88 if side == 0 else 1.0) * (0.45 + 0.55 * sp) * 1.25
        rotd = -flap * (26 if side else 20) - (1 - sp) * 95 + (-12 if side == 0 else 0) + p["lean"] * 0.5

        def A(a):
            return a + rotd
        elbow = add(root, tuple(v * 18 * sc for v in dirv(A(-118))))
        wrist = add(elbow, tuple(v * 22 * sc for v in dirv(A(-158))))
        fingers = [add(wrist, tuple(v * ln * sc for v in dirv(A(ang)))) for ang, ln in ((-138, 22), (-178, 30), (150, 29), (122, 24))]
        poly = [root, elbow, wrist, fingers[0]]
        scal = []
        for a_, b_ in zip(fingers, fingers[1:]):
            s_ = lerp(lerp(a_, b_, 0.5), wrist, 0.26)
            poly += [s_, b_]
            scal.append(s_)
        s_ = lerp(lerp(fingers[-1], body_end, 0.5), wrist, 0.22)
        poly += [s_, body_end]
        scal.append(s_)
        m = poly_mask(poly)
        Lw.paint(n_plate(m, bevel=3, tilt=(-0.15, -0.25), strength=0.8,
                         fold=lambda x, y: (0.35 * math.sin(math.atan2(y - wrist[1], x - wrist[0]) * 7.0 + ph * 0.5), 0.0)), "N", bias=bias - 1)
        for fi, tipp in enumerate(fingers):
            for t in (0.45, 0.75):
                q = lerp(wrist, tipp, t)
                Lw.decal(line(q, lerp(q, scal[min(fi, len(scal) - 1)], 0.5)), ("N", 4))
        Lw.paint(n_capsule(root, elbow, 2.0, 1.5), "Z", bias=bias, ao=0)
        Lw.paint(n_capsule(elbow, wrist, 1.5, 1.2), "Z", bias=bias, ao=0)
        Lw.paint(n_dome(wrist, 1.7, 1.7), "Z", bias=bias, ao=0)
        for tipp in fingers:
            Lw.paint({q: (0.0, -0.5, 0.85) for q in line(wrist, tipp)}, "Z", bias=bias, ao=0)
        claw = add(wrist, tuple(v * 4 for v in dirv(A(-100))))
        Lw.paint({q: (0.0, -0.6, 0.8) for q in line(wrist, claw)}, "Z", bias=bias, ao=0)
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
    for k, off in enumerate((-2.5, 0.0, 2.5)):
        a = add(tip, (perp[0] * off - d[0] * (18 + 5 * k), perp[1] * off - d[1] * (18 + 5 * k)))
        b = add(tip, (perp[0] * off * 0.3 + d[0] * 6, perp[1] * off * 0.3 + d[1] * 6))
        F.put(line(a, b)[::1 if k == 1 else 2], "Z5" if k == 1 else "Z4")
    t = ip(add(tip, (d[0] * 4, d[1] * 4)))
    F.put([t, (t[0] + 1, t[1]), (t[0] - 1, t[1]), (t[0], t[1] + 1), (t[0], t[1] - 1), (t[0] + 2, t[1]), (t[0] - 2, t[1])], "E4")


def fx_trail(F, j, p):
    for k in range(7):
        y = 80 + k * 11 + p["bob"] * 0.6
        x0 = j["Wa"][0] - 40 - k * 4
        pts = line((x0, y), (x0 + 16 + (k % 2) * 8, y))
        F.put([q for i, q in enumerate(pts) if i % 5 != 4], "Z3" if k % 2 else "Z2")


def fx_aura(F, Fb, j, p, info):
    k = p["aura"]
    if k <= 0:
        return
    for i in range(int(18 * k)):
        a = hash01(i, int(p["ph"] * 7), 3) * 6.28
        r = 18 + 22 * hash01(i, 2, int(p["ph"] * 7))
        x = j["Wa"][0] + math.cos(a) * r * 0.8
        y = j["Wa"][1] - 10 + math.sin(a) * r
        (F if i % 2 else Fb).put([ip((x, y)), ip((x, y - 1))], "Z3" if i % 3 else "E2")


def fx_off_glow(F, info, p):
    k = p["offglow"]
    if k <= 0:
        return
    h = info["hand_f"]
    r = 2 + 4 * k
    for q in mask_disc(h, r):
        dd = math.hypot(q[0] + .5 - h[0], q[1] + .5 - h[1]) / r
        if dd < 0.35:
            F.put([q], "E4")
        elif dd < 0.7:
            F.put([q], "E2")
        elif hash01(q[0], q[1], int(k * 9)) < 0.5:
            F.put([q], "Z3")
    for i in range(int(8 * k)):
        a = hash01(i, int(k * 10), 5) * 6.28
        rr = r + 3 + 6 * hash01(i, 1, int(k * 10))
        F.put([ip((h[0] + math.cos(a) * rr, h[1] + math.sin(a) * rr))], "Z3")


# ------------------------------------------------------------------ frame assembly
def render(p, phase, prev=None):
    names = LAYERS2 if phase == 2 else LAYERS1
    L = {n: Layer(n) for n in names if n not in ("FXBack", "Glow", "FX")}
    F, Fb, G = FXLayer("FX"), FXLayer("FXBack"), FXLayer("Glow")
    j = joints(p)
    info = {}
    if phase == 2:
        draw_wings(L, F, j, p, info)
    draw_cape(L, j, p, phase)
    draw_hair(L, j, p, phase)
    draw_gown(L, F, j, p, phase, info)
    draw_arm(L, G, F, j, p, "f", phase, info)
    draw_collar(L, j, p, phase)
    draw_body(L, G, j, p, phase)
    draw_head(L, G, F, j, p, phase)
    draw_arm(L, G, F, j, p, "n", phase, info)
    draw_sword(L, G, F, j, p, info, phase)
    fx_off_glow(F, info, p)
    fx_aura(F, Fb, j, p, info)
    for f in p["fx"]:
        if f == "thrust":
            fx_thrust(F, info, p)
        elif f == "trail":
            fx_trail(F, j, p)
        elif f == "smear":
            draw_smear(F, Fb, info, prev, p)
    imgs = {n: render_layer(l) for n, l in L.items()}
    imgs["FX"], imgs["FXBack"], imgs["Glow"] = F.image(), Fb.image(), G.image()
    info["hurt_px"] = set(L["Body"].px) | set(L["Head"].px) | {q for q in L["Gown"].px if q[1] < 136}
    info["off_px"] = mask_disc(info["hand_f"], 5)
    return imgs, info


def mirror_imgs(imgs):
    out = {}
    for n, im in imgs.items():
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        o.paste(im.transpose(Image.FLIP_LEFT_RIGHT), (2 * AX - W, 0))
        out[n] = o
    return out


def mirror_pt(q):
    return (2 * AX - q[0], q[1])


def dissolve(imgs, frac, seed=0, bats=False, blood=False):
    out, motes = {}, {}
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
                    if t < frac + 0.05 and n != "Glow":
                        dst[x, y] = RGBA["Z3" if blood else "K1"]
                elif blood and hash01(x, y, 5 + seed) < 0.05:
                    fy = int(y + (frac - t) * 60)
                    if fy < FLOOR:
                        motes[(x, fy)] = "Z2" if hash01(x, y, 6) < 0.5 else "Z3"
        out[n] = new
    fx = out["FX"].copy()
    fp = fx.load()
    if bats:
        n = int(14 + 30 * min(1.0, frac * 1.5))
        for i in range(n):
            a = hash01(i, 3, seed) * 6.28
            r = 8 + frac * 56 * hash01(i, 4, seed)
            cx = AX + math.cos(a) * r * 1.2
            cy = 96 + math.sin(a) * r * 0.7 - frac * 30 * hash01(i, 5, seed)
            up = (i + int(frac * 7)) % 2
            for q, c in (((0, 0), "K1"), ((-1, -up), "K2"), ((1, -up), "K2"), ((-2, -1 + up), "K1"), ((2, -1 + up), "K1"), ((-3, up), "K1"), ((3, up), "K1")):
                x, y = int(cx + q[0]), int(cy + q[1])
                if inb(x, y):
                    fp[x, y] = RGBA[c]
            if inb(int(cx), int(cy)) and i % 3 == 0:
                fp[int(cx), int(cy)] = RGBA["E2"]
    for (x, y), c in motes.items():
        if inb(x, y):
            fp[x, y] = RGBA[c]
    if blood:
        hw = int(8 + 34 * min(1.0, frac))
        for x in range(AX - hw, AX + hw + 1):
            if inb(x, FLOOR):
                fp[x, FLOOR] = RGBA["Z1" if abs(x - AX) > hw - 3 else "Z2"]
                if abs(x - AX) < hw - 6:
                    fp[x, FLOOR - 1] = RGBA["Z1" if x % 5 else "Z3"]
    out["FX"] = fx
    return out


# ------------------------------------------------------------------ animations: (ms, pose)
TAU = math.pi * 2
GUARD = dict(hn=(128.0, 104.0), sa=20.0, hf=(96.0, 104.0))


def wings(phase, s=0.42):
    return dict(spread=s) if phase == 2 else {}


def seq(phase, keys, **common):
    out = []
    for i, k in enumerate(keys):
        ms = k.pop("ms")
        d = dict(common)
        d.update(wings(phase))
        d.update(k)
        d.setdefault("ph", i * 0.55)
        out.append((ms, P(**d)))
    return out


def anim_idle(phase):
    n = 6
    return [(160, P(ph=TAU * i / n, bob=0.6 * math.sin(TAU * i / n), hn=(128.0, 104.0 + 0.6 * math.sin(TAU * i / n)), sa=20 + 1.5 * math.sin(TAU * i / n),
                    hf=(96.0, 104.0), wind=-1.0 + math.sin(TAU * i / n) * 0.7, flap=0.15 * math.sin(TAU * i / n), **wings(phase))) for i in range(n)]


def anim_walk(phase):
    n = 8
    return [(110, P(ph=TAU * i / n * 2, bob=1.0 * abs(math.sin(TAU * i / n)), wind=-4.5 + math.sin(TAU * i / n) * 1.5, flare=1.2 * math.sin(TAU * i / n),
                    hn=(129.0, 104.0 + math.sin(TAU * i / n)), sa=18, lean=3.0, hf=(94.0, 103.0), flap=0.2 * math.sin(TAU * i / n), **wings(phase))) for i in range(n)]


def anim_slash1(phase):   # a heavy diagonal cut from high to low
    return seq(phase, [
        dict(ms=110, lean=-3, hn=(120.0, 84.0), sa=-70),
        dict(ms=120, lean=-7, bob=-1, hn=(114.0, 74.0), sa=-128, two=True),
        dict(ms=60, lean=10, bob=3, hn=(138.0, 104.0), sa=35, fx=("smear",)),
        dict(ms=70, lean=12, bob=4, hn=(134.0, 118.0), sa=72, fx=("smear",)),
        dict(ms=120, lean=8, bob=3, hn=(132.0, 116.0), sa=70),
        dict(ms=120, lean=3, bob=1, hn=(130.0, 108.0), sa=40),
        dict(ms=120, lean=0, **GUARD),
    ], wind=-2.0)


def anim_slash2(phase):   # rising cut
    return seq(phase, [
        dict(ms=100, lean=4, bob=3, hn=(126.0, 116.0), sa=120),
        dict(ms=120, lean=6, bob=4, hn=(122.0, 120.0), sa=150),
        dict(ms=60, lean=-2, bob=1, hn=(136.0, 96.0), sa=-15, fx=("smear",)),
        dict(ms=70, lean=-6, bob=0, hn=(130.0, 80.0), sa=-72, fx=("smear",)),
        dict(ms=120, lean=-6, bob=0, hn=(128.0, 80.0), sa=-80),
        dict(ms=120, lean=-2, hn=(128.0, 92.0), sa=-20),
        dict(ms=120, lean=0, **GUARD),
    ], wind=-2.0)


def anim_thrust(phase):   # a long driving thrust
    return seq(phase, [
        dict(ms=110, lean=-4, hn=(116.0, 96.0), sa=12),
        dict(ms=130, lean=-9, bob=1, hn=(108.0, 96.0), sa=10, aura=0.4),
        dict(ms=60, lean=14, bob=5, hn=(146.0, 108.0), sa=16, fx=("thrust", "trail"), wind=-7, flare=4),
        dict(ms=90, lean=15, bob=5, hn=(147.0, 109.0), sa=17, fx=("thrust",), wind=-7, flare=4),
        dict(ms=120, lean=9, bob=3, hn=(138.0, 108.0), sa=20, wind=-4, flare=2),
        dict(ms=120, lean=4, bob=1, hn=(132.0, 106.0), sa=20),
        dict(ms=120, lean=0, **GUARD),
    ], wind=-2.0)


def anim_spin(phase):     # a whirling cut that strikes behind and before her
    return seq(phase, [
        dict(ms=110, lean=-4, hn=(118.0, 96.0), sa=170, hf=(94.0, 92.0)),
        dict(ms=60, lean=6, bob=2, hn=(138.0, 102.0), sa=15, flare=6, fx=("smear",)),
        dict(ms=60, lean=6, bob=2, hn=(140.0, 100.0), sa=-10, flare=8, mirror=True),
        dict(ms=60, lean=6, bob=2, hn=(138.0, 104.0), sa=20, flare=8, mirror=True, fx=("thrust",)),
        dict(ms=70, lean=6, bob=2, hn=(138.0, 104.0), sa=20, flare=6, fx=("smear",)),
        dict(ms=120, lean=3, bob=1, hn=(134.0, 106.0), sa=24, flare=3),
        dict(ms=120, lean=0, **GUARD),
        dict(ms=100, lean=0, **GUARD),
    ], wind=3.0)


def anim_overhead(phase):  # both hands, a cleaving blow that splits the floor
    two = dict(two=True, pref_n=(0.0, 1.0))
    return seq(phase, [
        dict(ms=110, lean=-2, hn=(118.0, 88.0), sa=-60, **two),
        dict(ms=110, lean=-6, bob=-1, hn=(112.0, 72.0), sa=-105, **two),
        dict(ms=120, lean=-9, bob=-2, hn=(108.0, 66.0), sa=-125, aura=0.5, **two),
        dict(ms=140, lean=-10, bob=-2, hn=(107.0, 66.0), sa=-132, aura=1.0, **two),
        dict(ms=80, lean=-10, bob=-2, hn=(107.0, 66.0), sa=-132, aura=1.0, **two),
        dict(ms=60, lean=14, bob=5, hn=(138.0, 108.0), sa=40, fx=("smear",), **two),
        dict(ms=90, lean=18, bob=7, hn=(140.0, 122.0), sa=72, fx=("smear",), **two),
        dict(ms=160, lean=16, bob=7, hn=(140.0, 122.0), sa=74, **two),
        dict(ms=140, lean=6, bob=2, hn=(132.0, 110.0), sa=40),
    ], wind=-1.0, hf=(112.0, 80.0))


def anim_charge(phase):   # crouch, then the blood-charge dash pose (frames 2..4 loop in the engine)
    return seq(phase, [
        dict(ms=110, lean=-8, bob=4, hn=(118.0, 108.0), sa=12, aura=0.6),
        dict(ms=120, lean=8, bob=6, hn=(132.0, 118.0), sa=14, aura=1.0),
        dict(ms=70, lean=24, bob=8, hn=(148.0, 116.0), sa=10, wind=-10, flare=6, fx=("trail", "thrust"), aura=1.0, hf=(86.0, 100.0)),
        dict(ms=70, lean=25, bob=9, hn=(149.0, 117.0), sa=11, wind=-12, flare=7, fx=("trail",), aura=1.0, hf=(86.0, 102.0)),
        dict(ms=70, lean=24, bob=8, hn=(148.0, 116.0), sa=10, wind=-10, flare=6, fx=("trail", "thrust"), aura=1.0, hf=(86.0, 100.0)),
    ])


def anim_chargeend(phase):  # braking, and a rising cut out of the charge
    return seq(phase, [
        dict(ms=80, lean=-6, bob=5, hn=(132.0, 120.0), sa=110, wind=6, flare=6),
        dict(ms=60, lean=-4, bob=3, hn=(138.0, 96.0), sa=-20, fx=("smear",), wind=4),
        dict(ms=70, lean=-6, bob=1, hn=(130.0, 80.0), sa=-75, fx=("smear",), wind=2),
        dict(ms=130, lean=-5, hn=(128.0, 82.0), sa=-78),
        dict(ms=120, lean=-2, hn=(128.0, 94.0), sa=-20),
        dict(ms=120, lean=0, **GUARD),
    ])


def anim_grab(phase):     # the off hand reaches back, burns, and lunges for your throat
    return seq(phase, [
        dict(ms=120, lean=-3, hf=(92.0, 90.0), offglow=0.3, claw=True),
        dict(ms=120, lean=-7, hf=(86.0, 82.0), offglow=0.6, claw=True),
        dict(ms=140, lean=-9, bob=1, hf=(84.0, 78.0), offglow=0.9, claw=True, aura=0.5),
        dict(ms=100, lean=-9, bob=1, hf=(84.0, 78.0), offglow=1.0, claw=True, aura=0.8),
        dict(ms=70, lean=16, bob=5, hf=(146.0, 102.0), offglow=1.0, claw=True, wind=-6, fx=("trail",), pref_f=(0.0, 1.0)),
        dict(ms=110, lean=18, bob=6, hf=(148.0, 104.0), offglow=0.8, claw=True, wind=-6, pref_f=(0.0, 1.0)),
        dict(ms=150, lean=8, bob=3, hf=(130.0, 100.0), offglow=0.3, claw=True),
        dict(ms=150, lean=0, hf=(96.0, 104.0)),
    ], hn=(116.0, 110.0), sa=60)


def anim_drain(phase):    # holding her prey up by the throat (the engine hangs you from her off hand)
    return [(130, P(lean=4 + math.sin(i * 1.6), bob=1, hf=(136.0, 92.0 + math.sin(i * 1.6)), claw=True, offglow=0.6 + 0.3 * (i % 2),
                    pref_f=(0.0, 1.0), hn=(116.0, 112.0), sa=62, head=(1.0, 1.0), aura=0.6, ph=i * 1.2, **wings(phase))) for i in range(4)]


def anim_cast(phase):     # blood gathers in her off hand, she drives it into the floor
    return seq(phase, [
        dict(ms=110, hf=(96.0, 100.0)),
        dict(ms=110, lean=-2, hf=(102.0, 84.0), offglow=0.3),
        dict(ms=120, lean=-4, bob=-1, hf=(106.0, 66.0), offglow=0.6, pref_f=(-1.0, 0.0)),
        dict(ms=130, lean=-5, bob=-1, hf=(107.0, 60.0), offglow=1.0, pref_f=(-1.0, 0.0)),
        dict(ms=70, lean=10, bob=5, hf=(120.0, 120.0), offglow=1.0),
        dict(ms=100, lean=14, bob=8, hf=(122.0, 132.0), offglow=0.7),
        dict(ms=150, lean=10, bob=6, hf=(118.0, 128.0), offglow=0.3),
        dict(ms=140, lean=2, bob=1, hf=(98.0, 104.0)),
    ], hn=(128.0, 104.0), sa=22, wind=-1.0)


def anim_stagger(phase):
    return seq(phase, [
        dict(ms=90, lean=-11, bob=2, hn=(122.0, 114.0), sa=60, head=(-1.0, 0.5), hf=(90.0, 108.0), eyes=0.6),
        dict(ms=110, lean=-14, bob=3, hn=(120.0, 118.0), sa=70, head=(-1.2, 0.8), hf=(88.0, 110.0), eyes=0.6),
        dict(ms=240, lean=-13, bob=3, hn=(120.0, 118.0), sa=72, head=(-1.2, 0.8), hf=(88.0, 110.0), eyes=0.6),
        dict(ms=240, lean=-10, bob=2, hn=(122.0, 116.0), sa=66, head=(-1.0, 0.5), hf=(90.0, 108.0), eyes=0.6),
    ], wind=2.0)


def anim_bow(phase):      # intro: a knight's salute, blade raised before her face, then lowered to guard
    keys = []
    for i, k in enumerate((0.0, 0.3, 0.7, 1.0, 1.0, 1.0, 0.6, 0.2)):
        keys.append(dict(ms=200 if 3 <= i <= 5 else 130, hn=lerp((128.0, 104.0), (116.0, 78.0), k), sa=20 - 112 * k, hf=(96.0, 104.0),
                         head=(0.0, 0.0), eyes=1.0 if i > 1 else 0.3, aura=0.4 * k))
    return seq(phase, keys)


def anim_death(phase):    # she sinks onto one knee, leaning on her planted blade, and bleeds away
    out = []
    for i in range(12):
        k = min(1.0, i / 6)
        out.append((140 if i < 8 else 160, P(lean=-8 + 16 * k, bob=2 + 16 * k, hn=(124.0 + 6 * k, 110.0 + 10 * k), sa=85, hf=(94.0, 110.0 + 10 * k),
                                         head=(1.0 * k, 2.0 * k), eyes=1.0 - k, flare=10 * k, ph=i * 0.4, wind=1.0, **(wings(phase, 0.3 * (1 - k)) if phase == 2 else {}))))
    return out


def anim_fly():
    n = 6
    return [(110, P(ph=TAU * i / n * 2, fly=1.0, spread=1.0, flap=math.sin(TAU * i / n), bob=-2 + 2 * math.sin(TAU * i / n + 1),
                    lean=5, hn=(128.0, 102.0), sa=40, hf=(92.0, 96.0), wind=-3.5)) for i in range(n)]


def anim_dive():
    ks = [(110, 8, -3, 1.0, 0.9, (126.0, 96.0), 30, ()), (110, 16, -3, 1.0, 1.0, (128.0, 96.0), 36, ()),
          (110, 26, -2, 0.8, 0.8, (132.0, 100.0), 44, ()), (80, 38, 0, 0.55, -0.4, (140.0, 110.0), 52, ("thrust", "trail")),
          (80, 40, 0, 0.5, -0.6, (141.0, 112.0), 54, ("thrust", "trail")), (80, 40, 0, 0.5, -0.6, (141.0, 112.0), 54, ("thrust", "trail")),
          (80, 40, 0, 0.5, -0.6, (141.0, 112.0), 54, ("thrust",)), (120, 20, 4, 0.8, 0.2, (134.0, 114.0), 50, ())]
    return [(ms, P(lean=l, bob=b, spread=s, flap=f, hn=h, sa=sa, fx=fx, fly=1.0, wind=-6.0, ph=i * 0.7, hf=(92.0, 94.0), aura=0.5))
            for i, (ms, l, b, s, f, h, sa, fx) in enumerate(ks)]


def anim_land():
    ks = [(90, 12, 9, 0.7), (110, 8, 6, 0.6), (130, 4, 3, 0.55), (140, 2, 1, 0.5), (150, 0, 0, 0.45), (160, 0, 0, 0.42)]
    return [(ms, P(lean=l, bob=b, spread=s, hn=(132.0, 116.0 - 2 * i), sa=50 - 6 * i, ph=i * 0.6, wind=-1.0, hf=(94.0, 104.0)))
            for i, (ms, l, b, s) in enumerate(ks)]


def anim_volley():         # wings flare wide and loose a fan of blood spikes
    out = []
    for i in range(8):
        k = min(1.0, i / 3) if i < 6 else 1.0 - (i - 5) / 3
        out.append((110 if i != 4 else 80, P(fly=1.0, spread=1.0, flap=-0.6 * k + 0.2 * math.sin(i), lean=-5 * k, bob=-2,
                                             hn=lerp((128.0, 102.0), (118.0, 72.0), k), sa=40 + (-110) * k, hf=(92.0, 96.0),
                                             ph=i * 0.6, wind=-2.5, aura=k)))
    return out


def anim_transform():
    out = []
    for i in range(10):
        k = i / 9
        out.append((120 if i < 9 else 220, P(spread=min(1.0, max(0.0, (k - 0.2) / 0.7)), flap=0.3 * math.sin(i), lean=-7 * math.sin(k * math.pi),
                                           bob=-1, hf=lerp((96.0, 104.0), (92.0, 80.0), math.sin(k * math.pi)), hn=(126.0, 96.0), sa=-30 * math.sin(k * math.pi) + 20,
                                           ph=i * 0.8, wind=-2.0, hair=k, crownfire=k, aura=k, eyes=1.0)))
    return out


TAGS1 = [("idle", anim_idle), ("walk", anim_walk), ("slash1", anim_slash1), ("slash2", anim_slash2), ("thrust", anim_thrust),
         ("spin", anim_spin), ("overhead", anim_overhead), ("charge", anim_charge), ("chargeend", anim_chargeend), ("grab", anim_grab),
         ("drain", anim_drain), ("cast", anim_cast), ("vanish", None), ("appear", None), ("stagger", anim_stagger),
         ("death", anim_death), ("bow", anim_bow)]
TAGS2 = [("fly", anim_fly), ("dive", anim_dive), ("land", anim_land), ("volley", anim_volley), ("transform", anim_transform)]


def build_frames(phase):
    out = []
    tags = TAGS1 + (TAGS2 if phase == 2 else [])
    idle_pose = anim_idle(phase)[0][1]
    for tag, fn in tags:
        if ONLY and tag not in ONLY:
            continue
        frs = []
        if tag in ("vanish", "appear"):
            imgs0, info0 = render(dict(idle_pose, ph=0.0), phase)
            seq_ = []
            for i in range(6):
                frac = (i + 1) / 6 * 1.05
                seq_.append((80, dissolve(imgs0, frac, seed=3, bats=True), dict(info0, hidden=frac > 0.8)))
            if tag == "appear":
                seq_ = list(reversed(seq_))[1:] + [(110, imgs0, info0)]
            frs = seq_
        else:
            poses = fn(phase) if (tag, fn) in TAGS1 else fn()
            prev = None
            for i, (ms, p) in enumerate(poses):
                imgs, info = render(p, phase, prev)
                prev = info
                if p["mirror"]:
                    imgs = mirror_imgs(imgs)
                    info = dict(info)
                    for k in ("hand_n", "hand_f", "tip", "b0"):
                        if k in info:
                            info[k] = mirror_pt(info[k])
                    for k in ("hurt_px", "blade_px", "off_px"):
                        info[k] = {mirror_pt(q) for q in info.get(k, set())}
                    prev = None
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


def union(rs):
    rs = [r for r in rs if r]
    if not rs:
        return None
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs); x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def blade_hit(frs, idx, down=10, minx=None):
    """The swept area of the blade over the given frames (previous frame included), reaching down for a 26px knight."""
    rs = []
    for i in idx:
        rs.append(rect_of(frs[i][2].get("blade_px", set()), pad=2))
        if i > 0 and not frs[i][1].get("_mir"):
            rs.append(rect_of(frs[i - 1][2].get("blade_px", set()), pad=1))
    r = union(rs)
    if not r:
        return None
    x, y, w, h = r
    y1 = min(FLOOR + 1, y + h + down)
    if minx is not None:
        x1 = x + w
        x = max(x, minx)
        w = x1 - x
    return [x, y, w, y1 - y]


def make_meta(frames_by_tag):
    fm = {}
    for tag, frs in frames_by_tag:
        lst = []
        for ms, imgs, info in frs:
            hb = rect_of(info["hurt_px"]) if not info.get("hidden") else None
            if hb:
                hb = [max(hb[0], AX - 22), hb[1], min(hb[2], 44), hb[3]]
            e = {"hb": hb or [AX - 14, 50, 28, 110]}
            for k, name in (("hand_n", "hand"), ("hand_f", "off"), ("tip", "tip")):
                if k in info:
                    e[name] = [round(info[k][0], 1), round(info[k][1], 1)]
            lst.append(e)
        fm[tag] = lst
    meta = {"native": 1, "anchor": [AX, AY], "hurtbox": [AX - 16, 50, 34, 110], "frames": fm, "attacks": {}, "spawn": {}, "telegraph": {}}
    by = {t: f for t, f in frames_by_tag}

    def tel(tag, i, at=None):
        if tag in by:
            meta["telegraph"][tag] = {"frame": i, "at": list(map(round, at or by[tag][i][2]["tip"]))}
    if "slash1" in by:
        meta["attacks"]["slash1"] = {"active": [2, 3], "hit": blade_hit(by["slash1"], [2, 3], minx=AX - 6)}
        tel("slash1", 1)
    if "slash2" in by:
        meta["attacks"]["slash2"] = {"active": [2, 3], "hit": blade_hit(by["slash2"], [2, 3], minx=AX - 6)}
        tel("slash2", 1)
    if "thrust" in by:
        meta["attacks"]["thrust"] = {"active": [2, 3], "hit": blade_hit(by["thrust"], [2, 3], down=14, minx=AX)}
        tel("thrust", 1)
    if "spin" in by:
        f = by["spin"]
        meta["attacks"]["spin"] = {"windows": [{"active": [1, 1], "hit": blade_hit(f, [1], minx=AX - 6)},
                                               {"active": [2, 3], "hit": union([rect_of(f[2][2]["blade_px"], 2), rect_of(f[3][2]["blade_px"], 2), [AX - 70, 100, 64, 60]])},
                                               {"active": [4, 4], "hit": blade_hit(f, [4], minx=AX - 6)}]}
        tel("spin", 0, [AX + 10, 80])
    if "overhead" in by:
        meta["attacks"]["overhead"] = {"active": [5, 6], "hit": blade_hit(by["overhead"], [5, 6], minx=AX - 4)}
        tel("overhead", 3)
        meta["spawn"]["overhead"] = {"frame": 6, "at": list(map(round, by["overhead"][6][2]["tip"]))}
    if "charge" in by:
        meta["attacks"]["charge"] = {"active": [2, 4], "hit": blade_hit(by["charge"], [2, 3, 4], down=18, minx=AX - 10)}
    if "chargeend" in by:
        meta["attacks"]["chargeend"] = {"active": [1, 2], "hit": blade_hit(by["chargeend"], [1, 2], minx=AX - 6)}
    if "grab" in by:
        g = by["grab"]
        r = union([rect_of(g[4][2]["off_px"], 3), rect_of(g[5][2]["off_px"], 3)])
        meta["attacks"]["grab"] = {"active": [4, 5], "hit": [r[0], r[1], r[2], min(FLOOR + 1, r[1] + r[3] + 16) - r[1]]}
        tel("grab", 2, list(map(round, g[2][2]["hand_f"])))
    if "cast" in by:
        meta["spawn"]["cast"] = {"frame": 4, "at": list(map(round, by["cast"][4][2]["hand_f"]))}
    if "dive" in by:
        meta["attacks"]["dive"] = {"active": [3, 6], "hit": blade_hit(by["dive"], [3, 4, 5, 6], down=6)}
    if "volley" in by:
        meta["spawn"]["volley"] = {"frame": 4, "at": list(map(round, by["volley"][4][2]["tip"]))}
    return meta


def preview(name, frames_by_tag, meta, scale=2):
    rows = frames_by_tag
    cols = max(len(f) for _, f in rows)
    pad, lab = 2, 10
    sheet = Image.new("RGBA", ((cols * (W + pad)) * scale, len(rows) * (H + pad + lab) * scale), (86, 86, 94, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, frs) in enumerate(rows):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 2), f"{t} ({len(frs)})", fill=(235, 235, 240, 255))
        a = meta["attacks"].get(t)
        wins = (a.get("windows") or [a]) if a else []
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
            sheet.alpha_composite(big, (i * (W + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", name))


def export(name, frames_by_tag, layers):
    frames, tags = [], []
    for tag, frs in frames_by_tag:
        a = len(frames)
        for ms, imgs, info in frs:
            frames.append({"ms": ms, "cels": {n: imgs[n] for n in layers if n in imgs}})
        tags.append((tag, a, len(frames) - 1))
    if BUILD:
        import asebuild
        asebuild.build(name, W, H, layers, frames, tags)


def closeup(frames_by_tag, name, picks, scale=3, crop=(20, 20, 204, 160)):
    by = {t: f for t, f in frames_by_tag}
    ims = []
    for t, i in picks:
        if t in by and i < len(by[t]):
            ims.append(flatten(by[t][i][1], LAYERS2 if "WingFar" in by[t][i][1] else LAYERS1).crop(crop))
    if not ims:
        return
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    sheet = Image.new("RGBA", (len(ims) * cw * scale, ch * scale), (86, 86, 94, 255))
    for k, im in enumerate(ims):
        fr = Image.new("RGBA", (cw, ch), (86, 86, 94, 255))
        fr.alpha_composite(im)
        sheet.alpha_composite(fr.resize((cw * scale, ch * scale), Image.NEAREST), (k * cw * scale, 0))
    sheet.save(os.path.join(ART, "previews", name))


def main():
    f1 = build_frames(1)
    meta = make_meta(f1)
    preview("sanguine.png", f1, meta)
    closeup(f1, "sanguine_closeup.png", [("idle", 0), ("slash1", 2), ("thrust", 3), ("overhead", 3), ("charge", 3), ("grab", 5)])
    f2 = build_frames(2)
    meta2 = make_meta(f2)
    for t in ("fly", "dive", "land", "volley", "transform"):
        if t in meta2["frames"]:
            meta["frames"][t] = meta2["frames"][t]
    for k in ("attacks", "spawn", "telegraph"):
        for t in ("dive", "volley"):
            if t in meta2[k]:
                meta[k][t] = meta2[k][t]
    preview("sanguine_p2.png", f2, meta)
    closeup(f2, "sanguine_p2_closeup.png", [("idle", 0), ("fly", 1), ("dive", 4), ("volley", 4), ("slash1", 2), ("transform", 9)],
            crop=(0, 0, 224, 160))
    if ONLY is None:
        with open(os.path.join(ART, "..", "assets", "sanguine_meta.json"), "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
        export("sanguine", f1, LAYERS1)
        export("sanguine_p2", f2, LAYERS2)


if __name__ == "__main__":
    main()
