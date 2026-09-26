#!/usr/bin/env python3
"""FX v5 (Expansion 2 spells + weapon arts, agent G) -> art/fx_g2_*.aseprite, assets/fx_g2_*.png/.json

House style as gen_fx*.py: crisp colour bands, Bayer-ordered falloff, Glow layer under a Core layer,
one tag per sprite named without the "fx_" prefix (multi-state sprites carry one tag per state).
Projectiles travel RIGHT; "bottom" sprites sit on their last row.
Families: thorn green (bramble), drowned teal (hymn, tidal surge), blood (lance, rite, thrust),
ghost blue (soul chains), sun gold (sunbeam, solar flare), sand (sandstorm), star violet (comet,
starfall, harvest moon), neon magenta/cyan (pulse, null field, overclock), pale flame (pale pyre).
Re-runnable: python3 art/gen_fx5.py [fx_g2_name ...]   (preview -> art/previews/fx5.png)
"""
import os, sys, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_fx import blank, put, disc, clean, bt  # noqa: E402
from gen_fx2 import A, CORE, ASH, ramp_at, radial, ring  # noqa: E402
from gen_fx4 import (mask_poly, fill_mask, pline, thick_pline, jag, ell_arc, dim, build, flame, ell_glow,  # noqa: E402
                     LAVA, STORM)

BLOOD = [A((40, 4, 10)), A((110, 10, 24)), A((190, 24, 40)), A((240, 90, 96)), A((255, 200, 196))]
MOSS = [A((20, 40, 20)), A((46, 88, 40)), A((96, 150, 60)), A((170, 214, 110)), A((230, 250, 190))]
TEAL = [A((10, 40, 48)), A((24, 100, 104)), A((70, 190, 180)), A((170, 245, 232)), A((240, 255, 252))]
SUN = [A((110, 60, 16)), A((200, 130, 30)), A((250, 200, 80)), A((255, 236, 160)), CORE]
SAND = [A((80, 58, 32)), A((140, 104, 58)), A((200, 162, 98)), A((238, 212, 150)), A((252, 240, 206))]
STAR = [A((40, 24, 80)), A((100, 70, 180)), A((170, 140, 240)), A((230, 220, 255)), CORE]
NEON = [A((70, 10, 70)), A((170, 30, 160)), A((240, 80, 220)), A((255, 180, 250)), CORE]
CYAN = [A((10, 50, 80)), A((20, 130, 190)), A((80, 220, 255)), A((190, 250, 255)), CORE]
GHOST = [A((24, 36, 90)), A((60, 100, 200)), A((130, 180, 255)), A((210, 236, 255)), CORE]
PALE = [A((110, 100, 88)), A((180, 170, 150)), A((230, 222, 204)), A((252, 248, 234)), CORE]
BONE = [A((70, 60, 52)), A((150, 136, 116)), A((214, 204, 184)), A((244, 238, 222))]
IRON = [A((34, 34, 46)), A((70, 72, 92)), A((130, 134, 160)), A((200, 204, 226))]


def L(*names):
    return {n: None for n in names}


def crescent_arc(img, cx, cy, rx, ry, a0, a1, thick, ramp, taper=True):
    """Sweep band along an ellipse from a0 to a1 (degrees, screen-up positive); thickness tapers to the tail."""
    n = int(abs(a1 - a0) / 360 * 2 * math.pi * max(rx, ry) * 2) + 8
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        th = thick * (math.sin(math.pi * t) ** 0.7 if taper else t ** 0.8)
        for k in range(int(th * 2) + 1):
            f = k / max(1, th * 2)
            r = 1 - k * 0.5 / max(rx, ry)
            x, y = cx + math.cos(a) * rx * r, cy - math.sin(a) * ry * r
            put(img, x, y, ramp[-1] if f < 0.2 else (ramp[-2] if f < 0.5 else (ramp[-3] if f < 0.8 else ramp[-4])))


def star4(img, cx, cy, L_, c0, c1):
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for i in range(int(L_) + 1):
            put(img, cx + dx * i, cy + dy * i, c0 if i < L_ * 0.4 else c1)


# ================================================================ bramble snare
def thorn_vine(img, pts, ramp, thorns=True, seed=0):
    rnd = random.Random(seed)
    thick_pline(img, pts, ramp[1], 1.0)
    pline(img, pts, ramp[2])
    if thorns:
        for i in range(1, len(pts) - 1):
            x, y = pts[i]
            s = rnd.choice((-1, 1))
            put(img, x + s, y - 1, ramp[3]); put(img, x + 2 * s, y - 2, BONE[3])


def fx_g2_bramble():
    """Bramble Snare: g2_bramble_idle (dormant coil on the floor, loop 4) and g2_bramble_snap (vines lash up and knot)."""
    W, H = 48, 48
    base = H - 1
    cels, ms = [], []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        ell_glow(glow, 24, base - 2, 18, 3.5, [MOSS[0], MOSS[1]])
        for j in range(3):
            pts = [(8 + j * 2 + i * 3.2, base - 2 - 2.2 * math.sin(i * 0.9 + j * 2 + k * 0.4)) for i in range(10)]
            thorn_vine(core, pts, MOSS, seed=j + k)
        for j in range(3):
            put(core, 12 + j * 11, base - 4 - (k + j) % 3, MOSS[4] if (j + k) % 2 else MOSS[3])
        cels.append({"Glow": glow, "Core": core}); ms.append(110)
    rnd = random.Random(4)
    vines = [(rnd.uniform(-16, 16), rnd.uniform(26, 40), rnd.uniform(-1, 1)) for _ in range(7)]
    for k in range(7):
        glow, core = blank(W, H), blank(W, H)
        grow = min(1.0, (k + 1) / 3)
        if k < 3:
            ell_glow(glow, 24, base - 12, 16, 12, [MOSS[0], MOSS[1], MOSS[2]])
        for (x0, h, lean) in vines:
            hh = h * grow * (1 if k < 5 else 0.8)
            pts = []
            for i in range(9):
                t = i / 8
                x = 24 + x0 * (1 - t) + lean * 8 * math.sin(t * 3) - x0 * 0.3 * t
                pts.append((x, base - hh * t))
            thorn_vine(core, pts, MOSS, seed=int(x0 * 7))
        if k >= 2:   # the knot
            ell_arc(core, 24, base - 18, 10, 12, 0, 360, MOSS[2], keep=lambda t, x, y: bt(int(x), int(y)) < 0.8)
            for j in range(6):
                a = j * 1.05 + k * 0.3
                put(core, 24 + math.cos(a) * 11, base - 18 + math.sin(a) * 13, BONE[3])
        if k >= 5:
            dim(core, 1 - (k - 4) * 0.3, k); dim(glow, 0.5, k)
        cels.append({"Glow": glow, "Core": core}); ms.append(50 if k < 4 else 80)
    return build("fx_g2_bramble", W, H, ["Glow", "Core"], cels, ms, [("g2_bramble_idle", 0, 3), ("g2_bramble_snap", 4, 10)])


# ================================================================ drowning hymn
def ghost_face(img, cx, cy, r, ramp, open_=1.0):
    for y in range(int(cy - r * 1.3), int(cy + r * 1.3) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / (r * 1.3)
            if nx * nx + ny * ny <= 1:
                put(img, x, y, ramp[3] if nx + ny < -0.3 else ramp[2])
    put(img, cx - r * 0.4, cy - r * 0.2, ramp[0]); put(img, cx + r * 0.4, cy - r * 0.2, ramp[0])
    for i in range(int(1 + 2 * open_)):
        put(img, cx, cy + r * 0.4 + i, ramp[0])


def fx_g2_hymn():
    """Drowning Hymn: a rolling wall of drowned water with pale singing faces in it, moving RIGHT, loop 4."""
    W, H = 52, 50
    base = H - 1
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        for x in range(W):
            t = x / (W - 1)
            h = 10 + 30 * math.sin(math.pi * min(1, t * 1.15)) ** 1.2 + 2 * math.sin(x * 0.5 + k * 1.6)
            for y in range(int(base - h), base + 1):
                q = (base - y) / max(1, h)
                if q > 0.85 and bt(x, y) > (1 - q) * 6:
                    continue
                if t < 0.25 and bt(x + k, y) > t * 4:
                    continue
                (glow if q < 0.7 else core).putpixel((x, y), TEAL[1] if q < 0.35 else (TEAL[2] if q < 0.7 else (TEAL[3] if q < 0.92 else TEAL[4])))
        # crest foam
        for x in range(10, W - 2):
            t = x / (W - 1)
            h = 10 + 30 * math.sin(math.pi * min(1, t * 1.15)) ** 1.2 + 2 * math.sin(x * 0.5 + k * 1.6)
            if (x + k) % 3:
                put(core, x, base - h, TEAL[4])
        for j, (fx, fy) in enumerate(((22, 20), (34, 16), (40, 30), (28, 34))):
            ghost_face(core, fx + (k % 2), base - fy + (1 if (k + j) % 2 else 0), 3, [TEAL[0], BONE[1], BONE[2], BONE[3]], open_=(k + j) % 2)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_hymn", W, H, ["Glow", "Core"], cels, 90, "g2_hymn")


# ================================================================ blood
def fx_g2_blood_lance():
    """Blood Lance projectile travelling RIGHT: a needle of blood with droplets trailing, loop 4."""
    W, H = 44, 12
    cy = 6
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        for x in range(4, W - 1):
            t = (x - 4) / (W - 5)
            hw = 2.6 * math.sin(math.pi * min(1, t * 1.25)) ** 0.6 if t < 0.8 else 2.6 * (1 - t) / 0.2
            for y in range(H):
                d = abs(y + 0.5 - cy)
                if d <= hw + 1.2 and d > hw:
                    if bt(x, y) < t:
                        glow.putpixel((x, y), BLOOD[1])
                elif d <= hw:
                    core.putpixel((x, y), BLOOD[4] if d < hw * 0.3 and t > 0.4 else (BLOOD[3] if y < cy else BLOOD[2]))
        put(core, W - 1, cy, CORE)
        for j in range(4):
            x = 6 - j * 1.5 + ((k + j) % 3); y = cy + (j - 1.5) * 2
            put(core, x, y, BLOOD[2] if j % 2 else BLOOD[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_blood_lance", W, H, ["Glow", "Core"], cels, 60, "g2_blood_lance")


def fx_g2_rite():
    """Crimson Rite: blood erupts from the caster into a spinning sigil ring, then rains back down."""
    W, H = 72, 72
    cx, cy = 36, 40
    rnd = random.Random(2)
    drops = [(rnd.uniform(0, 6.283), rnd.uniform(0.6, 1.0)) for _ in range(16)]
    cels = []
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        r = [6, 14, 22, 27, 29, 30, 30, 30][k]
        if k < 3:
            radial(glow, cx, cy, 10 + k * 4, [BLOOD[0], BLOOD[1], BLOOD[2], BLOOD[3]])
        keep = 1.0 if k < 5 else 1 - (k - 4) * 0.28
        ell_arc(core, cx, cy, r, r * 0.5, 0, 360, lambda t: BLOOD[3] if math.sin(t * 6.283 * 3) > 0 else BLOOD[2], keep=lambda t, x, y: bt(int(x), int(y)) < keep)
        if k >= 2:   # the sigil: a five-point star on the floor ellipse
            for j in range(5):
                a1, a2 = math.radians(90 + 144 * j + k * 10), math.radians(90 + 144 * (j + 1) + k * 10)
                p1 = (cx + math.cos(a1) * r * 0.85, cy - math.sin(a1) * r * 0.42)
                p2 = (cx + math.cos(a2) * r * 0.85, cy - math.sin(a2) * r * 0.42)
                if bt(j, k) < keep:
                    pline(core, [p1, p2], BLOOD[2])
        for (a, s) in drops:   # blood spray up, then raining
            t = k / 7
            x = cx + math.cos(a) * r * s
            y = cy - 26 * math.sin(math.pi * min(1, t * 1.6)) * s + (t * 20 if t > 0.6 else 0)
            if k < 7:
                put(core, x, y, BLOOD[3]); put(core, x, y + 1, BLOOD[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_rite", W, H, ["Glow", "Core"], cels, 55, "g2_rite")


def fx_g2_thrust():
    """Blood Frenzy thrust streak (RIGHT): a crimson line with a white-hot point, fading."""
    W, H = 52, 14
    cy = 7
    cels = []
    for k in range(5):
        glow, core = blank(W, H), blank(W, H)
        L_ = [30, 46, 48, 44, 36][k]
        x0 = W - 2 - L_
        for x in range(x0, W - 1):
            t = (x - x0) / max(1, L_)
            hw = 0.4 + 2.0 * t ** 1.5 if t < 0.9 else 2.4 * (1 - t) / 0.1
            if k >= 3 and bt(x, 0) > 1 - (k - 2) * 0.3:
                continue
            for y in range(H):
                d = abs(y + 0.5 - cy)
                if d <= hw + 1 and d > hw:
                    glow.putpixel((x, y), BLOOD[1])
                elif d <= hw:
                    core.putpixel((x, y), BLOOD[4] if t > 0.75 else (BLOOD[3] if d < hw * 0.5 else BLOOD[2]))
        if k < 3:
            star4(core, W - 3, cy, 3 + k, CORE, BLOOD[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_thrust", W, H, ["Glow", "Core"], cels, 35, "g2_thrust")


# ================================================================ soul chains
def chain_links(img, x0, y0, x1, y1, ramp, phase=0):
    L_ = math.hypot(x1 - x0, y1 - y0)
    n = int(L_ / 3)
    for i in range(n + 1):
        t = i / max(1, n)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if (i + phase) % 2 == 0:
            put(img, x, y, ramp[3]); put(img, x + 1, y, ramp[2]); put(img, x, y + 1, ramp[2])
        else:
            put(img, x, y, ramp[1]); put(img, x + 1, y + 1, ramp[2])


def fx_g2_chains():
    """Soul Chains: g2_chains_bind (chains lash up from the ground around a foe), g2_chains_hold (loop), g2_chains_break."""
    W, H = 48, 60
    base = H - 1
    anchors = [(4, base), (44, base), (10, base), (38, base)]
    target = (24, base - 24)
    cels, ms = [], []
    for k in range(5):   # bind
        glow, core = blank(W, H), blank(W, H)
        t = min(1.0, (k + 1) / 4)
        ell_glow(glow, 24, base - 1, 20, 3, [GHOST[0], GHOST[1]])
        for j, (ax, ay) in enumerate(anchors):
            ex, ey = ax + (target[0] + (j - 1.5) * 3 - ax) * t, ay + (target[1] + (j % 2) * 10 - 5 - ay) * t
            chain_links(core, ax, ay, ex, ey, GHOST, j)
            if k == 3:
                star4(core, ex, ey, 3, CORE, GHOST[3])
        cels.append({"Glow": glow, "Core": core}); ms.append(45)
    for k in range(4):   # hold
        glow, core = blank(W, H), blank(W, H)
        ell_glow(glow, 24, base - 1, 20, 3, [GHOST[0], GHOST[1]])
        ell_glow(glow, 24, base - 24, 12, 16, [GHOST[0], GHOST[1]])
        for j, (ax, ay) in enumerate(anchors):
            ex, ey = target[0] + (j - 1.5) * 3, target[1] + (j % 2) * 10 - 5
            chain_links(core, ax, ay, ex, ey, GHOST, j + k)
        for j in range(3):   # the binding bands
            y = base - 14 - j * 9
            ell_arc(core, 24, y, 9, 2.4, 0, 360, GHOST[3] if (j + k) % 2 else GHOST[2], keep=lambda tt, x, yy: (int(tt * 20) + k) % 3 != 0)
        cels.append({"Glow": glow, "Core": core}); ms.append(110)
    rnd = random.Random(6)
    bits = [(rnd.uniform(4, 44), rnd.uniform(10, 56), rnd.uniform(-60, 60), rnd.uniform(-90, -20)) for _ in range(22)]
    for k in range(5):   # break
        glow, core = blank(W, H), blank(W, H)
        t = k * 0.06
        if k < 2:
            radial(glow, 24, base - 24, 16 - k * 5, [GHOST[1], GHOST[2], GHOST[3]])
        for (x0, y0, vx, vy) in bits:
            x, y = x0 + vx * t, y0 + vy * t + 250 * t * t
            if k < 4 or bt(int(x), int(y)) < 0.5:
                put(core, x, y, GHOST[3] if k < 2 else GHOST[2]); put(core, x + 1, y, GHOST[1])
        cels.append({"Glow": glow, "Core": core}); ms.append(50)
    return build("fx_g2_chains", W, H, ["Glow", "Core"], cels, ms,
                 [("g2_chains_bind", 0, 4), ("g2_chains_hold", 5, 8), ("g2_chains_break", 9, 13)])


# ================================================================ sunbeam + solar flare
def beam(img_g, img_c, cx, top, base, hw, ramp, k, flicker=True):
    for y in range(top, base + 1):
        w = hw * (0.85 + 0.15 * math.sin(y * 0.3 + k * 2)) if flicker else hw
        for x in range(int(cx - w - 3), int(cx + w + 4)):
            d = abs(x + 0.5 - cx)
            if d <= w:
                q = d / max(0.5, w)
                img_c.putpixel((x, y), ramp[4] if q < 0.35 else (ramp[3] if q < 0.7 else ramp[2]))
            elif d <= w + 3 and bt(x, y) < (w + 3 - d) / 3:
                img_g.putpixel((x, y), ramp[1])


def fx_g2_sunbeam():
    """Sunbeam: g2_sunbeam_on (thin ray widens), g2_sunbeam_loop (full beam, motes), g2_sunbeam_off (narrows away)."""
    W, H = 40, 144
    cx, base = 20, H - 1
    cels, ms = [], []
    for k, hw in enumerate((1.0, 4.0, 8.0)):
        glow, core = blank(W, H), blank(W, H)
        beam(glow, core, cx, 0, base - 1, hw, SUN, k)
        ell_glow(glow, cx, base - 1, 8 + k * 4, 3, [SUN[0], SUN[1], SUN[2]])
        cels.append({"Glow": glow, "Core": core}); ms.append(40)
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        beam(glow, core, cx, 0, base - 1, 7.5, SUN, k)
        ell_glow(glow, cx, base - 1, 18, 4, [SUN[0], SUN[1], SUN[2], SUN[3]])
        for j in range(8):
            y = (j * 19 + k * 7) % (H - 10)
            x = cx + ((j * 5) % 11 - 5) * 1.6
            put(core, x, y, CORE)
        for j in range(5):
            put(core, cx - 14 + j * 7 + (k % 2), base - 1 - (j + k) % 3, SUN[3])
        cels.append({"Glow": glow, "Core": core}); ms.append(70)
    for k, hw in enumerate((5.0, 2.5, 0.8)):
        glow, core = blank(W, H), blank(W, H)
        beam(glow, core, cx, 0, base - 1, hw, SUN, k)
        dim(core, 1 - k * 0.25, k)
        cels.append({"Glow": glow, "Core": core}); ms.append(50)
    return build("fx_g2_sunbeam", W, H, ["Glow", "Core"], cels, ms,
                 [("g2_sunbeam_on", 0, 2), ("g2_sunbeam_loop", 3, 6), ("g2_sunbeam_off", 7, 9)])


def fx_g2_flare():
    """Solar Flare: a sun disc swells above the blade, then bursts into a ring of rays and heat."""
    W, H = 128, 112
    cx, cy = 64, 56
    cels = []
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        if k < 3:
            r = 5 + k * 5
            radial(glow, cx, cy, r + 8, [SUN[0], SUN[1], SUN[2]])
            radial(core, cx, cy, r, [SUN[2], SUN[3], SUN[4]])
        else:
            R = 18 + (k - 3) * 11
            keep = 1.0 if k < 5 else 1 - (k - 4) * 0.25
            ring(core, cx, cy, R, R, 2.2, SUN[3], keep=keep, seed=k, col_in=SUN[2])
            ring(glow, cx, cy, R - 3, R - 3, 3, SUN[1], keep=keep * 0.8, seed=k + 3)
            if k < 6:
                radial(glow, cx, cy, 16 - (k - 3) * 4, [SUN[1], SUN[2], SUN[3]])
            for j in range(16):   # rays
                a = j * math.pi / 8 + (0.2 if j % 2 else 0)
                L0, L1 = R * 0.55, R * (1.25 if j % 2 == 0 else 1.05)
                if bt(j, k) < keep:
                    pline(core, [(cx + math.cos(a) * L0, cy + math.sin(a) * L0), (cx + math.cos(a) * L1, cy + math.sin(a) * L1)], SUN[4] if j % 2 == 0 else SUN[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_flare", W, H, ["Glow", "Core"], cels, 50, "g2_flare")


# ================================================================ sandstorm
def fx_g2_sandstorm():
    """Sandstorm: a whirling funnel of sand moving along the ground, loop 6."""
    W, H = 52, 76
    cx, base = 26, H - 1
    rnd = random.Random(3)
    grains = [(rnd.uniform(0, 1), rnd.uniform(0, 6.283), rnd.uniform(0.7, 1.1)) for _ in range(160)]
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        for y in range(H):
            t = (base - y) / (H - 1)
            r = 5 + 19 * t ** 1.1
            sway = 3 * math.sin(t * 5 + k * 1.05)
            for x in range(W):
                d = abs(x + 0.5 - cx - sway)
                if d < r and bt(x + k, y) < 0.3 + 0.35 * (1 - d / r):
                    glow.putpixel((x, y), SAND[1] if d > r * 0.5 else SAND[0])
        for (h, a0, s) in grains:
            y = base - h * (H - 4)
            t = h
            r = (5 + 19 * t ** 1.1) * s
            a = a0 + k * 0.9 + t * 4
            x = cx + 3 * math.sin(t * 5 + k * 1.05) + math.cos(a) * r
            front = math.sin(a) > 0
            put(core if front else glow, x, y + math.sin(a) * 2, SAND[3] if front else SAND[2])
        for j in range(4):   # streak bands
            yy = base - 12 - j * 16
            t = (base - yy) / (H - 1)
            r = 5 + 19 * t ** 1.1
            a0 = k * 60 + j * 90
            ell_arc(core, cx + 3 * math.sin(t * 5 + k * 1.05), yy, r, 2.5, a0, a0 + 140, SAND[4] if j % 2 else SAND[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_sandstorm", W, H, ["Glow", "Core"], cels, 70, "g2_sandstorm")


# ================================================================ comet / starfall
def fx_g2_comet():
    """Comet in flight (falls DOWN-RIGHT): a white-violet head with a long fading tail to the upper-left, loop 4."""
    W, H = 44, 44
    hx, hy = 32, 32
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        for i in range(34):
            t = i / 33
            x, y = hx - t * 30 + math.sin(t * 9 + k) * 0.8, hy - t * 30 - math.sin(t * 9 + k) * 0.8
            r = 5.5 * (1 - t) ** 0.9
            if r < 0.5:
                continue
            for yy in range(int(y - r - 1), int(y + r + 2)):
                for xx in range(int(x - r - 1), int(x + r + 2)):
                    d = math.hypot(xx + 0.5 - x, yy + 0.5 - y) / r
                    if d <= 1 and bt(xx + k, yy) < 1.1 - t:
                        put(core if t < 0.35 else glow, xx, yy, STAR[3] if t < 0.15 else (STAR[2] if t < 0.5 else STAR[1]))
        radial(core, hx, hy, 5, [STAR[2], STAR[3], STAR[4]])
        disc(core, hx, hy, 2, CORE)
        star4(core, hx, hy, 6 + (k % 2) * 2, CORE, STAR[3])
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": core})
    return build("fx_g2_comet", W, H, ["Glow", "Core"], cels, 60, "g2_comet")


def fx_g2_comet_hit():
    """Comet impact: a white flash, a violet shock dome and a ring racing along the floor, star shards flung."""
    W, H = 104, 64
    cx, base = 52, H - 1
    rnd = random.Random(8)
    shards = [(rnd.uniform(-1, 1) * 170, -rnd.uniform(80, 220)) for _ in range(14)]
    cels = []
    for k in range(9):
        glow, core = blank(W, H), blank(W, H)
        t = k * 0.05
        if k < 4:
            r = [10, 22, 28, 30][k]
            ell_glow(glow, cx, base, r + 6, r * 0.9 + 4, [STAR[0], STAR[1], STAR[2]])
            ell_glow(core, cx, base, r * 0.6, r * 0.6, [STAR[2], STAR[3], STAR[4]])
            if k < 2:
                star4(core, cx, base - 14, 16 + k * 8, CORE, STAR[3])
        R = 8 + k * 6
        keep = 1.0 if k < 6 else 1 - (k - 5) * 0.3
        ell_arc(core, cx, base - 3, R, 4, 0, 360, STAR[3], keep=lambda tt, x, y: bt(int(x), int(y)) < keep)
        ell_arc(glow, cx, base - 3, R - 2, 3, 0, 360, STAR[1], keep=lambda tt, x, y: bt(int(x), int(y)) < keep * 0.7)
        for (vx, vy) in shards:
            x, y = cx + vx * t, base - 6 + vy * t + 420 * t * t
            if y < base and k < 8:
                put(core, x, y, STAR[4] if k < 4 else STAR[3]); put(core, x - math.copysign(1, vx), y + 1, STAR[2])
        if k >= 4:
            for j in range(5):
                disc(glow, cx - 20 + j * 10, base - 8 - (k - 4) * 4 - (j % 2) * 3, 3, ASH[1])
            dim(glow, 1 - (k - 4) * 0.18, k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_comet_hit", W, H, ["Glow", "Core"], cels, 50, "g2_comet_hit")


def fx_g2_star():
    """Starfall shard falling DOWN (head at the bottom), loop 3."""
    W, H = 16, 40
    cx, hy = 8, 33
    cels = []
    for k in range(3):
        glow, core = blank(W, H), blank(W, H)
        for y in range(0, hy):
            t = (hy - y) / hy
            w = 2.2 * (1 - t) ** 1.2
            for x in range(W):
                d = abs(x + 0.5 - cx)
                if d <= w and bt(x, y + k) < 1.15 - t:
                    (core if t < 0.3 else glow).putpixel((x, y), STAR[3] if t < 0.2 else STAR[2] if t < 0.5 else STAR[1])
        disc(core, cx, hy, 2.4, STAR[3]); put(core, cx, hy, CORE)
        star4(core, cx, hy, 4 + k, CORE, STAR[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_star", W, H, ["Glow", "Core"], cels, 60, "g2_star")


def fx_g2_star_hit():
    W, H = 44, 36
    cx, base = 22, H - 1
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        if k < 3:
            ell_glow(glow, cx, base, 10 + k * 5, 8 + k * 4, [STAR[0], STAR[1], STAR[2]])
            star4(core, cx, base - 6, 7 + k * 4, CORE, STAR[3])
        R = 5 + k * 3.5
        keep = 1 - k * 0.15
        ell_arc(core, cx, base - 2, R, 2.5, 0, 360, STAR[3], keep=lambda t, x, y: bt(int(x), int(y)) < keep)
        for j in range(6):
            a = j * 1.05
            put(core, cx + math.cos(a) * R * 0.9, base - 4 - abs(math.sin(a)) * R * 0.8, STAR[4] if k < 3 else STAR[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_star_hit", W, H, ["Glow", "Core"], cels, 45, "g2_star_hit")


def fx_g2_moon():
    """Harvest Moon: a spinning crescent (pale gold, violet rim), loop 4 (the crescent turns 90 deg / frame)."""
    W, H = 44, 44
    cx, cy = 22, 22
    MOON = [A((96, 70, 30)), A((190, 150, 70)), A((246, 214, 140)), A((255, 244, 208)), CORE]
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        a0 = -k * 90
        crescent_arc(core, cx, cy, 17, 17, a0 + 20, a0 + 250, 6.5, MOON)
        crescent_arc(glow, cx, cy, 19, 19, a0 - 40, a0 + 20, 2.5, [STAR[1], STAR[2], STAR[2], STAR[3]], taper=False)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_moon", W, H, ["Glow", "Core"], cels, 45, "g2_moon")


# ================================================================ neon: pulse / null field / glitch
def fx_g2_pulse():
    """Pulse Shot bolt travelling RIGHT: magenta core, cyan trail, loop 3."""
    W, H = 28, 8
    cy = 4
    cels = []
    for k in range(3):
        glow, core = blank(W, H), blank(W, H)
        for x in range(0, W - 5):
            if bt(x, k) < x / (W - 5):
                put(glow, x, cy + (1 if (x + k) % 5 == 0 else 0), CYAN[2] if x > 12 else CYAN[1])
        for x in range(W - 8, W - 1):
            put(core, x, cy, NEON[4] if x > W - 4 else NEON[3])
            put(core, x, cy - 1, NEON[2]); put(core, x, cy + 1, NEON[2])
        put(core, W - 1, cy, CORE)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_pulse", W, H, ["Glow", "Core"], cels, 40, "g2_pulse")


def fx_g2_pulse_hit():
    W, H = 24, 24
    cx, cy = 12, 12
    cels = []
    for k in range(5):
        glow, core = blank(W, H), blank(W, H)
        r = 2 + k * 2.5
        ring(core, cx, cy, r, r, 1.2, NEON[3] if k < 2 else NEON[2], keep=1 - k * 0.15, seed=k)
        if k < 2:
            star4(core, cx, cy, 5 + k * 3, CORE, CYAN[3])
        for j in range(4):   # square pixel shards (digital)
            a = j * 1.57 + 0.78
            x, y = cx + math.cos(a) * (r + 2), cy + math.sin(a) * (r + 2)
            put(glow, x, y, CYAN[2]); put(glow, x + 1, y, CYAN[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_pulse_hit", W, H, ["Glow", "Core"], cels, 40, "g2_pulse_hit")


def fx_g2_null():
    """Null Field: a hex-grid dome of cyan light with magenta scanlines, loop 6."""
    W, H = 120, 64
    cx, base = 60, H - 1
    rx, ry = 56, 58
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        for y in range(H):
            for x in range(W):
                nx, ny = (x + 0.5 - cx) / rx, (base - y) / ry
                d = nx * nx + ny * ny
                if d > 1 or y > base:
                    continue
                # hex-ish grid from three line families
                u = x * 0.5 + y * 0.866
                v = x * 0.5 - y * 0.866
                gline = (int(x) % 10 == 0) or (int(u) % 10 == 0) or (int(v) % 10 == 0)
                if d > 0.9:
                    core.putpixel((x, y), CYAN[3] if (x + k) % 7 else CORE)
                elif gline and bt(x, y) < 0.55 * (d ** 0.6):
                    glow.putpixel((x, y), CYAN[1] if d < 0.6 else CYAN[2])
        scan = (k * 11) % ry
        for x in range(W):
            nx = (x + 0.5 - cx) / rx
            if abs(nx) < math.sqrt(max(0, 1 - (scan / ry) ** 2)) and x % 2 == 0:
                put(core, x, base - scan, NEON[2])
        ell_arc(core, cx, base - 1, rx, 3, 0, 360, NEON[3], keep=lambda t, x, y: (int(t * 60) + k) % 4 != 0)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_null", W, H, ["Glow", "Core"], cels, 80, "g2_null")


def fx_g2_glitch():
    """Overclock burst: a square digital shockwave with RGB-split slices, 6 frames."""
    W, H = 56, 56
    cx, cy = 28, 28
    rnd = random.Random(11)
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        r = 4 + k * 4.5
        keep = 1 - k * 0.15
        for (dx, col) in ((-1, NEON[2]), (1, CYAN[2]), (0, CORE)):
            for t in range(int(r * 8)):
                s = t / (r * 8)
                side = int(s * 4)
                f = s * 4 - side
                x = cx + [(-r + 2 * r * f), r, (r - 2 * r * f), -r][side]
                y = cy + [-r, (-r + 2 * r * f), r, (r - 2 * r * f)][side]
                if bt(int(x), int(y)) < keep:
                    put(core if dx == 0 else glow, x + dx, y, col)
        for j in range(5):   # displaced scan slices
            y = rnd.randint(4, H - 5)
            x0 = rnd.randint(2, W - 20)
            for x in range(x0, x0 + rnd.randint(6, 16)):
                if k < 5:
                    put(glow, x + (k % 2) * 2, y, NEON[2] if j % 2 else CYAN[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_glitch", W, H, ["Glow", "Core"], cels, 45, "g2_glitch")


# ================================================================ scythe / whip / wave / pyre
def fx_g2_reap():
    """Reap: one full reaping circle around the wielder (wide ellipse), leading edge bright, 6 frames."""
    W, H = 104, 52
    cx, cy = 52, 28
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        head = 90 - k * 75
        span = [90, 200, 300, 330, 300, 240][k]
        fade = 1 if k < 4 else 1 - (k - 3) * 0.3
        crescent_arc(core, cx, cy, 48, 22, head + span, head, 5.5, [MOSS[1], MOSS[2], BONE[2], CORE], taper=False)
        crescent_arc(glow, cx, cy, 50, 23, head + span, head + 20, 3, [MOSS[0], MOSS[1], MOSS[1], MOSS[2]], taper=False)
        if fade < 1:
            dim(core, fade, k); dim(glow, fade * 0.8, k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_reap", W, H, ["Glow", "Core"], cels, 40, "g2_reap")


def fx_g2_crack():
    """Whip crack at the lash tip: a sharp 4-point spark with a sonic ring."""
    W, H = 28, 28
    cx, cy = 14, 14
    cels = []
    for k in range(5):
        glow, core = blank(W, H), blank(W, H)
        if k < 3:
            star4(core, cx, cy, [6, 11, 8][k], CORE, SUN[3])
            for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                for i in range(1, [3, 5, 4][k]):
                    put(glow, cx + dx * i, cy + dy * i, SUN[2])
        r = 3 + k * 2.4
        ring(glow if k > 2 else core, cx, cy, r, r * 0.8, 1, SUN[2] if k < 3 else SUN[1], keep=1 - k * 0.15, seed=k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_crack", W, H, ["Glow", "Core"], cels, 40, "g2_crack")


def fx_g2_wave():
    """Tidal Surge: a curling wave crest rushing RIGHT along the ground, loop 4."""
    W, H = 56, 48
    base = H - 1
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        crest_x = 40 + (k % 2)
        for x in range(W):
            t = x / (W - 1)
            h = 6 + 34 * t ** 1.6 if x <= crest_x else 40 * max(0, 1 - (x - crest_x) / 12) ** 0.5
            for y in range(int(base - h), base + 1):
                q = (base - y) / max(1, h)
                if x < 10 and bt(x + k, y) > x / 10:
                    continue
                c = TEAL[1] if q < 0.4 else (TEAL[2] if q < 0.8 else TEAL[3])
                (glow if q < 0.4 else core).putpixel((x, y), c)
        # the curl: an arc hooking over the front
        crescent_arc(core, crest_x - 2, base - 32, 10, 9, 20, 200, 3.5, [TEAL[1], TEAL[2], TEAL[3], TEAL[4]])
        for j in range(8):   # spray
            x = crest_x - 6 + j * 2 + (k * 3) % 5
            y = base - 42 - (j * 7 + k * 3) % 8
            put(core, x, y, TEAL[4] if j % 2 else TEAL[3])
        for x in range(0, W, 3):   # foam line
            put(core, x + k % 3, base - (6 + 34 * (x / (W - 1)) ** 1.6 if x <= crest_x else 0), TEAL[4])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_wave", W, H, ["Glow", "Core"], cels, 70, "g2_wave")


def fx_g2_pyre():
    """Pale Pyre: a column of white flame bursts from the ground, sways, and burns down to embers."""
    W, H = 36, 76
    cx, base = 18, H - 1
    hs = [8, 30, 56, 70, 64, 58, 44, 24, 8]
    cels = []
    for k, h in enumerate(hs):
        glow, core = blank(W, H), blank(W, H)
        ell_glow(glow, cx, base - h * 0.4, 12, h * 0.5 + 4, [PALE[0], PALE[1]])
        for i in range(h):
            t = i / max(1, h)
            hw = 7.5 * (1 - t) ** 0.6 + 0.5
            off = 1.8 * math.sin(t * 5 + k * 0.9)
            for x in range(W):
                d = abs(x + 0.5 - cx - off)
                if d > hw or (t > 0.75 and bt(x, base - i) > (1 - t) * 4):
                    continue
                v = (1 - t * 0.8) * (1 - 0.7 * d / hw)
                put(core, x, base - i, ramp_at([PALE[0], PALE[1], PALE[2], PALE[3], PALE[4]], v, x, base - i))
        for j in range(3):
            flame(core, cx - 9 + j * 9, base, h * 0.35, 2.2, j + k, [PALE[0], PALE[1], PALE[2], PALE[3]])
        for j in range(4):
            put(core, cx + ((j * 7 + k * 3) % 17) - 8, base - h - 2 - (j * 3 + k) % 6, PALE[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g2_pyre", W, H, ["Glow", "Core"], cels, 50, "g2_pyre")


# ================================================================ preview
BG = (92, 92, 100, 255)
CELL = (40, 38, 50, 255)


def preview(results, S=2):
    rows = []
    for name, frames, layers in results:
        cw, chh = frames[0]["cels"][layers[0]].size
        row = Image.new("RGBA", (len(frames) * (cw + 4) + 4, chh + 8), BG)
        for i, f in enumerate(frames):
            cell = Image.new("RGBA", (cw, chh), CELL)
            for Ly in layers:
                if f["cels"].get(Ly) is not None:
                    cell.alpha_composite(f["cels"][Ly])
            row.paste(cell, (4 + i * (cw + 4), 4))
        rows.append((name, row))
    LBL = 70
    Wt = LBL + max(r.width for _, r in rows)
    Ht = sum(r.height for _, r in rows)
    sheet = Image.new("RGBA", (Wt, Ht), BG)
    y = 0
    for name, r in rows:
        sheet.paste(r, (LBL, y)); y += r.height
    sheet = sheet.resize((Wt * S, Ht * S), Image.NEAREST)
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        d.text((4, y * S + 4), name.replace("fx_g2_", ""), fill=(255, 255, 255, 255)); y += r.height
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "fx5.png"))


ALL = [fx_g2_bramble, fx_g2_hymn, fx_g2_blood_lance, fx_g2_rite, fx_g2_thrust, fx_g2_chains, fx_g2_sunbeam, fx_g2_flare,
       fx_g2_sandstorm, fx_g2_comet, fx_g2_comet_hit, fx_g2_star, fx_g2_star_hit, fx_g2_moon, fx_g2_pulse, fx_g2_pulse_hit,
       fx_g2_null, fx_g2_glitch, fx_g2_reap, fx_g2_crack, fx_g2_wave, fx_g2_pyre]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    out = []
    for fn in ALL:
        if only and fn.__name__ not in only:
            continue
        frames = fn()
        out.append((fn.__name__, frames, list(frames[0]["cels"].keys())))
        print("built", fn.__name__, len(frames), "frames")
    if not only:
        preview(out)
