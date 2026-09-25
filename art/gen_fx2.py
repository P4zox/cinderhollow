#!/usr/bin/env python3
"""FX additions (ART_SPEC section 2) -> art/fx_*.aseprite, assets/fx_*.png/.json

Same house style as gen_fx.py (and reuses its helpers): crisp colour bands, Bayer-ordered
falloff instead of blur, >= 2 layers per sprite, one tag per sprite named without "fx_".
Gold = sorcery / grace / cinders, crimson = blood / criticals, silver = the player's blade.
Re-runnable: python3 art/gen_fx2.py [fx_name ...]
"""
import os, sys, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from gen_fx import (blank, put, disc, line, clean, breakup, bt, crescent, silver_fn,  # noqa: E402
                    silver_tail_fn, flare, emit, comp_frame, DUST)

# ---------------------------------------------------------------- palette
def A(c, a=255):
    return (c[0], c[1], c[2], a)

CORE = A((255, 248, 230))                                   # white-hot core
G = [A((96, 54, 18)), A((170, 110, 40)), A((240, 170, 60)), A((255, 210, 120)), CORE]  # gold ramp
CR = [A((62, 6, 18)), A((150, 20, 40)), A((240, 36, 50)), A((255, 128, 118)), CORE]    # crimson ramp
ASH = [A((40, 37, 46)), A((66, 61, 72)), A((100, 94, 104)), A((142, 135, 142))]
TR = (0, 0, 0, 0)


def ramp_at(ramp, v, x, y):
    """v in 0..1 -> ramp colour with ordered dithering between steps."""
    v = max(0.0, min(1.0, v))
    f = v * (len(ramp) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return ramp[min(i, len(ramp) - 1)]


def radial(img, cx, cy, r, ramp, power=1.0, dither_edge=True):
    """Filled radial glow: ramp[-1] at the centre falling to ramp[0] at radius r."""
    w, h = img.size
    for y in range(max(0, int(cy - r - 1)), min(h, int(cy + r + 2))):
        for x in range(max(0, int(cx - r - 1)), min(w, int(cx + r + 2))):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
            if d > 1:
                continue
            v = (1 - d) ** power
            if dither_edge and v < 0.18 and bt(x, y) > v / 0.18:
                continue
            img.putpixel((x, y), ramp_at(ramp, v, x, y))


def ring(img, cx, cy, rx, ry, width, col, keep=1.0, seed=0, col_in=None):
    w, h = img.size
    rnd = random.Random(seed)
    for y in range(h):
        for x in range(w):
            ux, uy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(ux / rx, uy / ry)
            if d == 0:
                continue
            grad = math.hypot(ux / (rx * rx), uy / (ry * ry)) / d      # true pixel thickness
            dd = (d - 1) / max(grad, 1e-6)
            if -width <= dd <= 0.2:
                if keep < 1:
                    a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
                    if random.Random(seed * 131 + int((a + 4) * 5)).random() > keep:
                        continue
                img.putpixel((x, y), col_in if (col_in and dd < -width * 0.5) else col)
    return img


def iflare(core, glow, cx, cy, *a):
    """gen_fx.flare on an integer centre (a .5 centre rounds to every other pixel -> broken rays)."""
    flare(core, glow, int(math.floor(cx)), int(math.floor(cy)), *a)


def spark(img, x, y, vx, vy, head, tail, n=2):
    """1px spark with a short trail opposite its velocity."""
    L = math.hypot(vx, vy) or 1
    for j in range(n, 0, -1):
        put(img, x - vx / L * j, y - vy / L * j, tail)
    put(img, x, y, head)


# ================================================================ projectiles / sorcery
def fx_ashbolt():
    """Golden-ash sorcery bolt travelling RIGHT. Head at (25, 8). 4-frame loop."""
    W, H = 32, 16
    cx, cy = 25.0, 8.0
    rnd = random.Random(11)
    embers = [(rnd.uniform(0, 20), rnd.uniform(-3.5, 3.5), rnd.random()) for _ in range(9)]
    cels = []
    for k in range(4):
        trail, glow, core = blank(W, H), blank(W, H), blank(W, H)
        # tapered comet tail in crisp bands, with a slow wave (phase advances 90 deg / frame)
        for x in range(3, int(cx)):
            t = (cx - x) / (cx - 3)                     # 0 at head .. 1 at tail end
            hw = 2.8 * (1 - t) ** 0.8
            wob = math.sin(x * 0.5 + k * math.pi / 2) * 1.1 * t
            if t > 0.62 and (x + k * 2) % 4 == 0:        # the far tail breaks into dashes
                continue
            for y in range(H):
                d = abs(y + 0.5 - (cy + wob))
                if d > hw + 0.3:
                    continue
                if d <= 0.6:
                    c, lay = (CORE if t < 0.18 else (G[3] if t < 0.55 else G[2])), trail
                elif d <= hw * 0.6 + 0.3:
                    c, lay = (G[3] if t < 0.3 else G[2]), trail
                else:
                    c, lay = (G[2] if t < 0.3 else G[1]), glow
                lay.putpixel((x, y), c)
        # head: hot egg shape, pointed forward
        for y in range(H):
            for x in range(W):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                e = math.hypot(dx / (4.2 if dx > 0 else 3.4), dy / 2.9)
                if e <= 1:
                    c = CORE if e < 0.5 else (G[3] if e < 0.8 else G[2])
                    core.putpixel((x, y), c)
                elif e <= 1.45 and bt(x, y) < (1.45 - e) / 0.45 + 0.1 * (k % 2):
                    glow.putpixel((x, y), G[1])
        put(core, cx + 4, cy - 0.5, CORE)             # leading glint
        put(core, cx + 5, cy - 0.5, G[3])
        # glittering spark on the rim, alternating
        put(core, cx - 1 + (k % 2), cy - 3 + 5 * (k // 2 % 2), CORE)
        # trailing embers: drift left 5px/frame (20px period -> seamless 4-frame loop)
        for (x0, yo, ph) in embers:
            x = 4 + (x0 - k * 5) % 20
            y = cy + yo + math.sin(ph * 6 + k * 1.6) * 0.8
            hot = (x > 13)
            put(trail, x, y, CORE if hot else G[3])
            put(glow, x + 1, y, G[2] if hot else G[1])
        cels.append({"Trail": clean(trail, ref=(glow, core)), "Glow": clean(glow, ref=(trail, core)),
                     "Core": core})
    return emit("fx_ashbolt", W, H, ["Trail", "Glow", "Core"], cels, 70, "ashbolt")


def fx_ashbolt_hit():
    """Ash bolt impact burst, centred (16, 16)."""
    W, H = 32, 32
    cx = cy = 16.0
    rnd = random.Random(23)
    parts = [(rnd.uniform(0, 360), rnd.uniform(0.7, 1.3), rnd.random() < 0.35) for _ in range(16)]
    ms = [40, 50, 60, 70, 80, 90]
    cels = []
    for k in range(6):
        glow, core, sp = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            radial(glow, cx, cy, 7.5, G[:4], 0.7)
            disc(core, cx - 0.5, cy - 0.5, 3.2, CORE)
            iflare(core, glow, cx - 0.5, cy - 0.5, 9, 4, 1.6, CORE, G[3], G[2], G[2])
        elif k == 1:
            ring(glow, cx, cy, 8.5, 8.5, 2.2, G[2], col_in=G[3])
            radial(glow, cx, cy, 5.5, G[1:4], 0.8)
            disc(core, cx - 0.5, cy - 0.5, 2.6, CORE)
            iflare(core, glow, cx - 0.5, cy - 0.5, 13, 6, 1.6, CORE, G[3], G[2], G[3])
        elif k == 2:
            ring(glow, cx, cy, 11.5, 11.5, 1.6, G[2], keep=0.85, seed=2, col_in=G[1])
            disc(core, cx - 0.5, cy - 0.5, 1.6, G[3])
            iflare(core, glow, cx - 0.5, cy - 0.5, 6, 3, 1.0, G[3], G[2], G[1], G[1])
        elif k == 3:
            ring(glow, cx, cy, 13.5, 13.5, 1.0, G[1], keep=0.55, seed=3)
        # particles: fast gold sparks + slower grey ash that floats up
        if k >= 1:
            for (a_, spd, ash) in parts:
                a = math.radians(a_)
                t = k
                r = (3 + 3.2 * t - 0.18 * t * t) * spd * (0.65 if ash else 1)
                x = cx + math.cos(a) * r
                y = cy - math.sin(a) * r - (0.5 * t * t * 0.3 if ash else -0.12 * t * t)
                if ash:
                    c = ASH[3] if k < 4 else ASH[2]
                    put(sp, x, y, c)
                    if k < 3:
                        put(sp, x + 1, y, ASH[2])
                else:
                    if k >= 5 and spd < 1.0:
                        continue
                    head = [CORE, CORE, G[3], G[2], G[1]][k - 1]
                    tail = [G[3], G[2], G[2], G[1], G[0]][k - 1]
                    spark(sp, x, y, math.cos(a), -math.sin(a), head, tail, 2 if k < 4 else 1)
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Particles": sp})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_ashbolt_hit", W, H, ["Glow", "Core", "Particles"], frames, [("ashbolt_hit", 0, 5)])
    return frames


# ================================================================ Emberburst
def flame(img_back, img_front, bx, by, h, w, phase, dim, front):
    """Tapered fire tongue rising from (bx, by). dim shifts the whole ramp down."""
    img = img_front if front else img_back
    if h < 1:
        return
    ramp = [CR[1], G[1], G[2], G[3], CORE]
    for i in range(int(h) + 1):
        t = i / h
        y = by - i
        hw = w * (1 - t) ** 0.75 + 0.35
        sway = math.sin(t * 3.2 + phase) * 1.6 * t
        for x in range(int(bx - w - 3), int(bx + w + 4)):
            d = abs(x + 0.5 - (bx + sway))
            if d > hw:
                continue
            q = d / hw
            v = (1 - t) * 1.05 - q * 0.3 - dim - (0 if front else 0.15)
            # hard colour bands (no noise): white-hot base -> gold -> amber -> crimson tip
            if v > 0.8:
                c = CORE
            elif v > 0.6:
                c = G[3]
            elif v > 0.42:
                c = G[2]
            elif v > 0.26:
                c = G[1]
            elif v > 0.12:
                c = CR[2] if front else CR[1]
            elif v > -0.02 and t > 0.3:
                c = CR[1] if front else CR[0]
            else:
                continue
            put(img, x, y, c)


def fx_flame_ring():
    """'Emberburst': ring of fire erupting from the ground. 96x48, pivot bottom (48, 47)."""
    W, H = 96, 48
    cx, cy = 48.0, 42.5
    RX = [8, 17, 26, 33, 38, 41, 43, 44]
    FH = [3, 14, 24, 27, 22, 14, 7, 0]
    DIM = [0, 0, 0, 0.05, 0.15, 0.3, 0.45, 0]
    ms = [50, 50, 60, 70, 70, 70, 80, 90]
    N = 24
    rnd = random.Random(7)
    tongues = [(i * 360 / N + rnd.uniform(-5, 5), rnd.uniform(0.7, 1.15), rnd.uniform(0, 6)) for i in range(N)]
    motes = [(rnd.uniform(0, 360), rnd.uniform(0.3, 1.0), rnd.uniform(0.6, 1.4)) for _ in range(22)]
    cels = []
    for k in range(8):
        ground, back, front, emb = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        rx = RX[k]
        ry = rx * 0.11 + 1.2
        # scorched glowing ring on the ground (front half brighter than the far half)
        lv = 2 if k < 5 else (1 if k < 7 else 0)
        ring(ground, cx, cy, rx + 1, ry + 0.8, 1.6, G[lv], keep=1 if k < 5 else 0.6, seed=k,
             col_in=G[max(0, lv - 1)])
        gp = ground.load()
        for y in range(H):
            if y < cy:
                for x in range(W):
                    if gp[x, y][3]:
                        gp[x, y] = G[max(0, lv - 1)] if bt(x, y) < 0.75 else TR
        # fire tongues: back half behind (dimmer), front half in front
        for (ang, hm, ph) in sorted(tongues, key=lambda t: -math.sin(math.radians(t[0]))):
            a = math.radians(ang)
            s = math.sin(a)
            bx = cx + math.cos(a) * rx
            by = cy + s * ry
            h = FH[k] * hm * (0.8 + 0.2 * abs(math.cos(a)))
            flame(back, front, bx, by, h, 2.2 + 0.4 * hm, ph + k * 1.3, DIM[k], s >= 0)
        # embers kicked upward
        if k >= 2:
            t = k - 1
            for (ma, mr, spd) in motes:
                a = math.radians(ma)
                x = cx + math.cos(a) * rx * mr + math.sin(ma + t) * 1.5
                y = cy + math.sin(a) * ry * mr - FH[min(k, 4)] * 0.6 - t * 3.2 * spd
                if y < 1 or (k >= 6 and spd < 0.9):
                    continue
                c = [G[3], G[3], G[2], G[2], G[1], G[1]][min(5, k - 2)]
                put(emb, x, y, c)
                if k < 5:
                    put(emb, x, y + 1, CR[1])
        cels.append({"Ground": clean(ground), "Back": clean(back, ref=(front,)),
                     "Front": clean(front, ref=(back,)), "Embers": emb})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_flame_ring", W, H, ["Ground", "Back", "Front", "Embers"], frames,
                   [("flame_ring", 0, 7)])
    return frames


# ================================================================ pogo
def fx_pogo():
    """Down-strike spark burst, impact point centred (16, 12): flat shock + sparks fanning up."""
    W, H = 32, 24
    cx, cy = 16.0, 12.0
    rnd = random.Random(5)
    sparks = []
    for i in range(12):
        a = math.radians(8 + i * 14.5 + rnd.uniform(-4, 4))          # upper fan, 8..172 deg
        sparks.append((math.cos(a) * rnd.uniform(2.2, 3.0), -math.sin(a) * rnd.uniform(1.3, 2.2)))
    cels = []
    for k in range(4):
        glow, core, sp = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            radial(glow, cx, cy, 6, G[1:4], 0.8)
            disc(core, cx - 0.5, cy - 0.5, 2.4, CORE)
            # wide horizontal lens flare + short vertical
            for x in range(W):
                d = abs(x + 0.5 - cx)
                if d < 15:
                    put(core, x, cy - 0.5, CORE if d < 7 else G[3])
                    if d < 9:
                        put(glow, x, cy - 1.5, G[3] if d < 5 else G[2])
                        put(glow, x, cy + 0.5, G[3] if d < 5 else G[2])
            for j in range(3, 7):
                put(core, cx - 0.5, cy - 0.5 - j, G[3] if j < 5 else G[2])
                put(core, cx - 0.5, cy - 0.5 + j, G[2])
        elif k == 1:
            ring(glow, cx, cy, 10, 3.2, 1.4, G[3], col_in=G[2])
            disc(core, cx - 0.5, cy - 0.5, 1.6, CORE)
            for x in range(W):
                d = abs(x + 0.5 - cx)
                if d < 12:
                    put(core, x, cy - 0.5, G[3] if d < 6 else G[2])
        elif k == 2:
            ring(glow, cx, cy, 13.5, 4.2, 1.0, G[2], keep=0.8, seed=4)
        if k >= 1:
            for (vx, vy) in sparks:
                t = k * 1.5
                x = cx + vx * t
                y = cy - 1 + vy * t + 0.3 * t * t
                head = [CORE, G[3], G[2]][k - 1]
                spark(sp, x, y, vx, vy + 0.7 * t, head, G[2] if k < 3 else G[1], 2 if k < 3 else 1)
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Sparks": sp})
    return emit("fx_pogo", W, H, ["Glow", "Core", "Sparks"], cels, 40, "pogo")


# ================================================================ player slashes (silver, as fx_slash)
def fx_slash_up():
    """Upward crescent: front (right) -> over the top -> back (left). Pivot bottom-centre (24, 47)."""
    W, H = 48, 48
    keys = [(-6, 40, 5, 0), (-10, 150, 9, 0), (40, 188, 8, 0.15), (120, 192, 3.5, -1)]
    cels = []
    for (tail, head, th, dim) in keys:
        fn = silver_tail_fn if dim < 0 else silver_fn(dim)
        core, glow, _ = crescent(W, H, 24, 45, 22, 42, tail, head, th, fn)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_slash_up", W, H, ["Glow", "Core"], cels, 40, "slash_up")


def fx_slash_air():
    """Flat horizontal crescent sweeping forward (RIGHT). Hand/pivot at (3, 15)."""
    W, H = 48, 32
    keys = [(96, 66, 4, 0), (100, -10, 8, 0), (56, -38, 8, 0.15), (10, -44, 3.5, -1)]
    cels = []
    for (tail, head, th, dim) in keys:
        fn = silver_tail_fn if dim < 0 else silver_fn(dim)
        core, glow, _ = crescent(W, H, 3, 15, 42, 13, tail, head, th, fn)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_slash_air", W, H, ["Glow", "Core"], cels, 40, "slash_air")


# ================================================================ riposte
def fx_riposte():
    """Crimson critical burst with a white core; the thrust enters from the left.
    Impact point (30, 24)."""
    W, H = 64, 48
    cx, cy = 30.0, 24.0
    rnd = random.Random(31)
    drops = [(rnd.uniform(-70, 70) + (0 if i % 3 else 180), rnd.uniform(1.6, 3.2), rnd.uniform(0.8, 1.6))
             for i, _ in enumerate(range(18))]
    spikes = [(a, L) for a, L in ((0, 1.0), (180, 0.55), (90, 0.7), (270, 0.7), (35, 0.8), (-35, 0.8),
                                  (145, 0.5), (215, 0.5), (60, 0.55), (-60, 0.55))]
    ms = [40, 60, 60, 70, 80, 90]
    cels = []
    for k in range(6):
        glow, core, drp = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            # the thrust streak arriving + a hot pinprick
            for x in range(4, int(cx) + 3):
                t = (cx - x) / (cx - 4)
                put(core, x, cy - 0.5, CORE if t < 0.4 else CR[3])
                if t < 0.7:
                    put(glow, x, cy - 1.5, CR[2])
                    put(glow, x, cy + 0.5, CR[2] if t < 0.4 else CR[1])
            radial(glow, cx, cy, 5, CR[1:4], 0.8)
            disc(core, cx - 0.5, cy - 0.5, 1.8, CORE)
        elif k in (1, 2):
            # solid crimson bands around a white-hot core (read cleanly at 1x, like fx_hit)
            R = 7.5 if k == 1 else 6
            disc(glow, cx - 0.5, cy - 0.5, R, CR[1])
            disc(glow, cx - 0.5, cy - 0.5, R * 0.72, CR[2])
            disc(core, cx - 0.5, cy - 0.5, R * 0.48, CR[3])
            disc(core, cx - 0.5, cy - 0.5, R * 0.3, CORE)
            ring(glow, cx, cy, R + 4 + 3 * (k - 1), R + 4 + 3 * (k - 1), 1.3, CR[2] if k == 1 else CR[1],
                 keep=1 if k == 1 else 0.8, seed=k)
            # 4-point crimson star, long along the thrust axis
            iflare(core, glow, cx, cy, 20 if k == 1 else 14, 7 if k == 1 else 5, 2.6 if k == 1 else 1.8,
                   CORE, CR[3], CR[2], CR[2])
            # the blade's exit streak: white line punching out to the right
            for x in range(int(cx), W - (2 if k == 1 else 10)):
                t = (x - cx) / (W - cx)
                put(core, x, cy - 1, CORE if t < 0.55 else CR[3])
                if t < 0.4 and k == 1:
                    put(glow, x, cy - 2, CR[2])
                    put(glow, x, cy, CR[2])
        elif k == 3:
            ring(glow, cx, cy, 15, 15, 1.2, CR[1], keep=0.65, seed=3)
            disc(core, cx - 0.5, cy - 0.5, 1.5, CR[3])
            iflare(core, glow, cx, cy, 9, 3, 1.0, CR[3], CR[2], CR[1], CR[1])
        elif k == 4:
            ring(glow, cx, cy, 17, 17, 1.0, CR[0], keep=0.45, seed=4)
            put(core, cx - 0.5, cy - 0.5, CR[2])
        # blood droplets thrown out along the thrust direction (mostly right)
        if k >= 1:
            t = k
            for (a_, spd, sz) in drops:
                a = math.radians(a_)
                x = cx + math.cos(a) * (5 + spd * t * 2.4)
                y = cy - math.sin(a) * (4 + spd * t * 1.7) + 0.35 * t * t
                s = sz * (1.25 - 0.12 * k)
                if s < 0.45:
                    continue
                if k < 3:
                    line(drp, x - math.cos(a) * spd * 1.2, y + math.sin(a) * spd * 0.9, x, y, CR[1])
                disc(drp, x - 0.5, y - 0.5, s * 0.8, CR[2] if k < 4 else CR[1])
                put(drp, x - 0.5, y - 0.5, CR[3] if k < 3 else CR[2])
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Droplets": drp})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_riposte", W, H, ["Glow", "Core", "Droplets"], frames, [("riposte", 0, 5)])
    return frames


# ================================================================ level up
def fx_levelup():
    """Golden pillar around the player. 64x64, pivot bottom (32, 63)."""
    W, H = 64, 64
    cx = 32.0
    G_Y = 62.0                                   # ground ellipse centre
    rnd = random.Random(17)
    motes = [(rnd.uniform(-13, 13), rnd.uniform(0, 1), rnd.uniform(0.8, 1.6)) for _ in range(26)]
    # per frame: (column half-width, column top y, ring rx, flash)
    COL = [(0, 64, 6, 0), (2, 40, 11, 0), (4, 6, 15, 0), (11, 0, 18, 1), (10, 0, 20, 0),
           (8, 0, 22, 0), (5, 0, 23, 0), (2, 20, 24, 0), (0, 64, 0, 0), (0, 64, 0, 0)]
    ms = [60, 50, 50, 70, 80, 90, 90, 90, 100, 110]
    cels = []
    for k in range(10):
        ground, col, core, mo = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        hw, top, rx, fl = COL[k]
        if rx:
            ring(ground, cx, G_Y, rx, rx * 0.2 + 0.6, 1.6, G[3] if k < 5 else G[2], keep=1 if k < 6 else 0.65,
                 seed=k, col_in=G[2] if k < 5 else G[1])
        if hw:
            for y in range(int(top), H):
                # column fades toward the top; edges bright, interior sparse streaks (player stays visible)
                ft = (y - top) / max(1, H - top)
                for x in range(W):
                    d = abs(x + 0.5 - cx)
                    if d > hw + 1:
                        continue
                    e = hw - d                       # distance inside the edge
                    vfade = min(1.0, 0.2 + ft * 1.6)   # dissolves toward the top
                    if bt(x, y) > vfade:
                        continue
                    if e < 0:                        # outer haze (translucent)
                        col.putpixel((x, y), A(G[2], 90))
                    elif e < 1.0:
                        col.putpixel((x, y), G[3] if ft > 0.35 else G[2])
                    elif e < 2.0 and hw > 4:
                        col.putpixel((x, y), A(G[3], 150))
                    else:
                        # luminous translucent body + rising streaks (5px / frame)
                        if (x % 3 == 1) and ((y + k * 5 + x * 7) % 11) < 4:
                            col.putpixel((x, y), CORE if d < hw * 0.4 else G[3])
                        else:
                            col.putpixel((x, y), A(G[3], 70 if d < hw * 0.6 else 95))
            if hw <= 4:                              # thin phase: white-hot core line
                for y in range(int(top), H):
                    put(core, cx - 0.5, y, CORE)
                    put(core, cx + 0.5, y, G[3])
        if fl:
            # crown flare at the top of the pillar + a burst at the player's chest
            iflare(core, col, cx, 8, 12, 6, 2.4, CORE, G[3], G[2], G[3])
            iflare(core, col, cx, 44, 20, 9, 2.8, CORE, CORE, G[3], G[3])
            disc(core, cx - 0.5, 43.5, 3.5, CORE)
        if k == 4:
            iflare(core, col, cx, 44, 12, 5, 1.6, G[3], G[3], G[2], G[2])
        # rising motes (start low, float up, spiral slightly)
        if k >= 2:
            for (ox, ph, spd) in motes:
                t = (k - 2) + ph * 2
                x = cx + ox * (1 + 0.04 * t) + math.sin(t * 0.9 + ox) * 1.2
                y = G_Y - 3 - t * 6.5 * spd
                if y < 1:
                    continue
                lvl = 3 if k < 6 else (2 if k < 8 else 1)
                put(mo, x, y, CORE if (lvl == 3 and spd > 1.3) else G[lvl])
                if k < 7:
                    put(mo, x, y + 1, G[max(0, lvl - 2)])
        cels.append({"Ground": clean(ground), "Column": clean(col, ref=(core,)), "Core": core, "Motes": mo})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_levelup", W, H, ["Ground", "Column", "Core", "Motes"], frames, [("levelup", 0, 9)])
    return frames


# ================================================================ cinder pickup
def fx_cinder():
    """Small golden cinder mote (currency pickup). 8x8 loop: pulse + 1px bob."""
    W, H = 8, 8
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        oy = [0, -1, -1, 0][k]
        big = k in (1, 2)
        cx, cy = 3, 3 + oy
        # diamond body
        for (dx, dy, c) in ((0, 0, CORE), (1, 0, G[3]), (0, 1, G[3]), (1, 1, G[2]),
                            (0, -1, G[3]), (-1, 0, G[3]), (2, 1, G[2]) if big else (1, 2, G[1]),
                            (1, -1, G[3] if big else G[2]), (-1, 1, G[2]), (0, 2, G[2])):
            put(core, cx + dx, cy + dy, c)
        # soft rim, flickering
        for (dx, dy) in ((-2, 0), (0, -2), (2, 0), (1, 3), (-1, 2), (2, -1), (-1, -1), (3, 1) if big else (2, 2)):
            if big or (dx + dy + k) % 2 == 0:
                put(glow, cx + dx, cy + dy, G[1])
        if big:
            put(glow, cx + 3, cy - 2, G[2])       # twinkle
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_cinder", W, H, ["Glow", "Core"], cels, 120, "cinder")


# ================================================================ enemy death
def fx_death_ash():
    """Enemy dissolving into ash & gold motes: a generic ash silhouette crumbles from the head
    down, each pixel lifting away up-and-back. 48x48, pivot bottom (24, 47)."""
    W, H = 48, 48
    rnd = random.Random(41)

    def inside(x, y):
        return ((x - 25) ** 2 / 30 + (y - 15) ** 2 / 26 <= 1 or                      # head
                (abs(x - 24) <= 9 - abs(y - 25) * 0.18 and 19 <= y <= 35) or           # shoulders/torso
                (abs(x - 20.5) <= 2.6 and 35 < y <= 47) or (abs(x - 27.5) <= 2.6 and 35 < y <= 47))  # legs

    cells = [(x, y) for y in range(H) for x in range(W) if inside(x, y)]
    info = {c: (rnd.uniform(-0.4, 0.8), rnd.uniform(0.8, 2.0), rnd.random() < 0.13, rnd.random(),
                rnd.random() < 0.45) for c in cells}
    ms = [70, 70, 80, 80, 90, 90, 100, 110]
    cels = []
    for k in range(8):
        body, ash, gold = blank(W, H), blank(W, H), blank(W, H)
        front = 7 + k * 6.8               # dissolve line sweeps head -> feet
        for (x0, y0) in cells:
            vx, vy, isg, ph, keep = info[(x0, y0)]
            rel = front + ph * 4 - 2 - y0
            if rel < 0:
                # still-solid ash statue: lit left edge, glowing cracks at the dissolve front
                if -rel < 2.5:
                    c = G[3] if isg or ph > 0.8 else G[2]
                elif -rel < 5:
                    c = G[1] if isg else ASH[3]
                else:
                    lit = not inside(x0 - 1, y0) or not inside(x0, y0 - 1)
                    c = ASH[3] if lit else (ASH[1] if (x0 + y0 * 3) % 7 else ASH[2])
                    if isg and ph > 0.6:
                        c = G[1]                      # ember veins
                put(body, x0, y0, c)
                continue
            if not (keep or isg):
                continue
            t = rel / 6.8 + 0.25
            x = x0 + vx * t * 1.7 + math.sin(t * 1.3 + ph * 6) * 0.8 + t * 0.9
            y = y0 - vy * t * 2.6 - 0.15 * t * t
            if y < 0 or t > 5.5 or (t > 3.5 and ph > 0.55 and not isg):
                continue
            if isg:
                put(gold, x, y, CORE if t < 1.0 else (G[3] if t < 2.6 else (G[2] if t < 4 else G[1])))
            else:
                put(ash, x, y, ASH[3] if t < 1.2 else (ASH[2] if t < 3 else ASH[1]))
        # small ash heap left on the ground, growing as the body falls away
        heap = min(k, 5)
        for x in range(int(24 - 3 - heap), int(24 + 4 + heap)):
            d = abs(x + 0.5 - 24) / (4 + heap)
            hh = int(round((1 - d * d) * (1 + heap * 0.35)))
            for j in range(hh):
                if not body.getpixel((x, 47 - j))[3]:
                    put(body, x, 47 - j, ASH[3] if j == hh - 1 and d < 0.6 else ASH[2])
        cels.append({"Body": outline_img(body), "Ash": ash, "Gold": gold})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_death_ash", W, H, ["Body", "Ash", "Gold"], frames, [("death_ash", 0, 7)])
    return frames


def outline_img(img, col=A((8, 7, 12))):
    """1px dark outline around the opaque shape (house style for solid silhouettes)."""
    w, h = img.size
    px = img.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 and any(0 <= x + a < w and 0 <= y + b < h and px[x + a, y + b][3]
                                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = col
    return out


# ================================================================ wall dust
def fx_wall_dust():
    """Dust puff scraped off a wall on the RIGHT edge (x=15), billowing left/up. Centred."""
    W, H = 16, 16
    puffs = [(13.5, 9.0, 2.0, -1.2, -0.5), (13.0, 12.0, 2.4, -1.5, 0.2), (14.0, 5.5, 1.6, -0.9, -0.9)]
    cels = []
    for k in range(4):
        shade, light = blank(W, H), blank(W, H)
        for (x0, y0, r0, vx, vy) in puffs:
            r = r0 + 0.7 * k
            x = x0 + vx * k * 1.3
            y = y0 + vy * k * 1.1
            for yy in range(H):
                for xx in range(W):
                    d = math.hypot(xx + 0.5 - x, yy + 0.5 - y)
                    if d > r or xx > 15:
                        continue
                    lx, ly = (xx + 0.5 - x) / r, (yy + 0.5 - y) / r
                    lit = -0.6 * lx - 0.8 * ly
                    if lit > 0.35 and d < r - 0.5:
                        light.putpixel((xx, yy), DUST[3] if k < 2 else DUST[2])
                    elif lit > -0.2:
                        light.putpixel((xx, yy), DUST[2] if k < 2 else DUST[1])
                    else:
                        shade.putpixel((xx, yy), DUST[1] if k < 3 else DUST[0])
        # grit specks flicked off the wall
        for i, (sx, sy) in enumerate(((12, 3), (10, 14), (9, 7))):
            put(light, sx - k * 1.6 - i * 0.4, sy + (k * 0.8 if i == 1 else -k * 0.5), DUST[3] if k < 3 else DUST[1])
        if k == 3:
            breakup(shade, 0.55, 3)
            breakup(light, 0.6, 4)
        cels.append({"Shade": clean(shade, ref=(light,)), "Light": clean(light, ref=(shade,))})
    return emit("fx_wall_dust", W, H, ["Shade", "Light"], cels, 60, "wall_dust")


# ================================================================ bleed
def fx_bleed():
    """Bleed proc: crimson spray burst centred (24, 24)."""
    W, H = 48, 48
    cx, cy = 24.0, 24.0
    rnd = random.Random(13)
    drops = []
    for i in range(22):
        a = math.radians(i * 360 / 22 + rnd.uniform(-8, 8))
        drops.append((math.cos(a) * rnd.uniform(2.2, 3.6), -math.sin(a) * rnd.uniform(2.0, 3.4) - 0.8,
                      rnd.uniform(0.9, 1.9)))
    ms = [40, 50, 60, 70, 80, 90]
    cels = []
    for k in range(6):
        splash, dl, core = blank(W, H), blank(W, H), blank(W, H)
        rc = [5.0, 7.5, 5.5, 3.0, 0, 0][k]
        if rc:
            for y in range(H):
                for x in range(W):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    ang = math.atan2(dy, dx)
                    rr = rc * (1 + 0.32 * math.sin(ang * 7 + k) + 0.12 * math.sin(ang * 3))
                    d = math.hypot(dx, dy)
                    if d <= rr:
                        c = CR[3] if (d < rr * 0.45 and dy < 0) else (CR[2] if d < rr * 0.8 else CR[1])
                        splash.putpixel((x, y), c)
        if k == 0:
            disc(core, cx - 0.5, cy - 0.5, 2.2, CORE)
            iflare(core, splash, cx - 0.5, cy - 0.5, 10, 5, 1.6, CORE, CR[3], CR[2], CR[2])
        elif k == 1:
            ring(splash, cx, cy, 13, 13, 1.4, CR[2], keep=0.8, seed=1, col_in=CR[1])
        elif k == 2:
            ring(splash, cx, cy, 16, 16, 1.0, CR[1], keep=0.55, seed=2)
        t = k + 1
        for (vx, vy, sz) in drops:
            x = cx + vx * t
            y = cy + vy * t + 0.3 * t * t
            s = sz * (1.0 - 0.1 * k)
            if s < 0.42:
                continue
            if k < 4:
                line(dl, x - vx * 1.0, y - (vy + 0.6 * t) * 1.0, x, y, CR[1])
            disc(dl, x - 0.5, y - 0.5, s * 0.75, CR[2] if k < 4 else CR[1])
            put(dl, x - 0.5, y - 0.5, CR[3] if k < 3 else CR[2])
        cels.append({"Splash": clean(splash, ref=(dl, core)), "Droplets": clean(dl, ref=(splash,)), "Core": core})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_bleed", W, H, ["Splash", "Droplets", "Core"], frames, [("bleed", 0, 5)])
    return frames


# ================================================================ grace glow
def fx_grace_glow():
    """Soft golden guidance light (shrines, items). 6-frame breathing loop, centred.
    Soft falloff via a few alpha steps (allowed for FX glows) instead of noisy dither."""
    W, H = 32, 32
    cx = cy = 16.0
    cels = []
    for k in range(6):
        halo, glow, core, mo = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        p = 0.5 + 0.5 * math.cos(2 * math.pi * k / 6)          # 1 -> 0 -> 1
        R = 11.5 + 2.5 * p
        bands = [(1.00, A(G[1], 60)), (0.78, A(G[2], 95)), (0.58, A(G[3], 140))]
        for y in range(H):
            for x in range(W):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / R
                for (edge, c) in bands[::-1]:
                    if d <= edge:
                        halo.putpixel((x, y), c)
                        break
        rg = 4.2 + 1.2 * p
        disc(glow, cx - 0.5, cy - 0.5, rg, G[2])
        disc(glow, cx - 0.5, cy - 0.5, rg * 0.7, G[3])
        disc(core, cx - 0.5, cy - 0.5, 1.3 + 0.7 * p, CORE)
        # vertical + short horizontal glint, strongest at the peak of the breath
        L = int(round(4 + 4 * p))
        for j in range(2, L + 1):
            c = G[3] if j < L - 1 else G[2]
            put(core, 15, 15 - j, c)
            put(core, 15, 15 + j, c)
            if j <= L // 2 + 1:
                put(core, 15 - j, 15, c)
                put(core, 15 + j, 15, c)
        # three motes orbiting slowly (120 deg apart -> 6-frame seamless loop)
        for i in range(3):
            a = math.radians(i * 120 + k * 20)
            x, y = cx + math.cos(a) * 10, cy - math.sin(a) * 4.5 - 1
            put(mo, x, y, CORE if math.sin(a) < -0.5 else G[3])
        cels.append({"Halo": halo, "Glow": glow, "Core": core, "Motes": mo})
    return emit("fx_grace_glow", W, H, ["Halo", "Glow", "Core", "Motes"], cels, 110, "grace_glow")


# ================================================================ parry flash
def fx_parry_flash():
    """Successful-parry star flash, white-gold, centred (24, 24)."""
    W, H = 48, 48
    cx = cy = 23.5
    rnd = random.Random(19)
    fly = [(rnd.uniform(0, 360), rnd.uniform(0.8, 1.25)) for _ in range(14)]
    ms = [30, 50, 50, 60, 70]
    cels = []
    for k in range(5):
        glow, core, sp = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            radial(glow, cx + 0.5, cy + 0.5, 9, G[1:4], 0.6)
            disc(core, cx, cy, 5, CORE)
            iflare(core, glow, cx, cy, 16, 6, 3.0, CORE, CORE, G[3], G[3])
        elif k == 1:
            radial(glow, cx + 0.5, cy + 0.5, 6, G[2:], 0.7)
            disc(core, cx, cy, 2.6, CORE)
            iflare(core, glow, cx, cy, 23, 11, 2.4, CORE, CORE, G[3], G[3])
            ring(glow, cx + 0.5, cy + 0.5, 12, 12, 1.2, G[3])
        elif k == 2:
            disc(core, cx, cy, 1.6, CORE)
            iflare(core, glow, cx, cy, 17, 7, 1.6, CORE, G[3], G[2], G[2])
            ring(glow, cx + 0.5, cy + 0.5, 16, 16, 1.0, G[2], keep=0.85, seed=2)
        elif k == 3:
            put(core, cx, cy, G[3])
            iflare(core, glow, cx, cy, 8, 3, 1.0, G[3], G[2], G[1], G[1])
            ring(glow, cx + 0.5, cy + 0.5, 19, 19, 1.0, G[1], keep=0.5, seed=3)
        if k >= 1:
            for (a_, spd) in fly:
                a = math.radians(a_)
                r = (6 + 4.2 * k) * spd
                x, y = cx + math.cos(a) * r, cy - math.sin(a) * r
                head, tail = [(CORE, G[3]), (CORE, G[3]), (G[3], G[2]), (G[2], G[1])][k - 1]
                spark(sp, x, y, math.cos(a), -math.sin(a), head, tail, 2 if k < 3 else 1)
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Sparks": sp})
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    asebuild.build("fx_parry_flash", W, H, ["Glow", "Core", "Sparks"], frames, [("parry_flash", 0, 4)])
    return frames


# ================================================================ preview
BG = (92, 92, 100, 255)
CELL_BG = (44, 42, 54, 255)


def preview(all_fx, S=3):
    """All effects as rows (one row per sprite, frames left->right) on mid-grey, 3x."""
    rows = []
    for name, frames, layers in all_fx:
        w, h = frames[0]["cels"][layers[0]].size
        strip = Image.new("RGBA", (len(frames) * (w + 2) + 2, h + 4), BG)
        for i, fr in enumerate(frames):
            cell = Image.new("RGBA", (w, h), CELL_BG)
            cell.alpha_composite(comp_frame(fr, layers))
            strip.paste(cell, (2 + i * (w + 2), 2))
        rows.append((name, strip))
    LBL = 34
    Wt = max(r.width for _, r in rows) + LBL
    Ht = sum(r.height for _, r in rows)
    sheet = Image.new("RGBA", (Wt, Ht), BG)
    y = 0
    for name, r in rows:
        sheet.paste(r, (LBL, y))
        y += r.height
    sheet = sheet.resize((Wt * S, Ht * S), Image.NEAREST)
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        d.text((4, y * S + 4), name.replace("fx_", ""), fill=(255, 255, 255, 255))
        y += r.height
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "fx2.png"))


ALL = [fx_ashbolt, fx_ashbolt_hit, fx_flame_ring, fx_pogo, fx_slash_up, fx_slash_air, fx_riposte,
       fx_levelup, fx_cinder, fx_death_ash, fx_wall_dust, fx_bleed, fx_grace_glow, fx_parry_flash]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    out = []
    for fn in ALL:
        if only and fn.__name__ not in only:
            continue
        frames = fn()
        out.append((fn.__name__, frames, list(frames[0]["cels"].keys())))
        print("built", fn.__name__, len(frames), "frames")
    if not only:          # a partial run would overwrite fx2.png with a partial sheet
        preview(out)
