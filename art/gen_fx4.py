#!/usr/bin/env python3
"""FX v4 (expansion spells + weapon arts, agent G) -> art/fx_g_*.aseprite, assets/fx_g_*.png/.json

Same house style as gen_fx.py / gen_fx2.py / gen_fx3.py: crisp colour bands, Bayer-ordered
falloff instead of blur, >= 2 layers per sprite (Glow under Core), one tag per sprite named
without the "fx_" prefix (multi-state sprites such as the ice wall carry one tag per state).
Projectiles travel RIGHT; "bottom" sprites sit on their last row.
Palette families: ink violet + gold (ink seal, glyph swarm), frost blue (glacial wall, frost
nova, frost aegis), ember/lava (magma orb, fissure, burning ground), storm cyan (bolt, spark),
wind mint (wind ward, whirl), bronze-gold (toll, aegis), silver-crimson (x-cut).
Re-runnable: python3 art/gen_fx4.py [fx_g_name ...]   (preview -> art/previews/fx4.png)
"""
import os, sys, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from gen_fx import blank, put, disc, clean, bt, crescent, EMBER  # noqa: E402
from gen_fx2 import A, CORE, G, CR, ASH, ramp_at, radial, ring  # noqa: E402

TR = (0, 0, 0, 0)
INK = [A((16, 8, 26)), A((42, 20, 68)), A((86, 44, 140)), A((156, 106, 226)), A((226, 204, 255))]
FROST = [A((22, 44, 104)), A((46, 110, 196)), A((120, 196, 244)), A((204, 240, 255)), A((250, 254, 255))]
LAVA = [A(EMBER[0][:3]), A(EMBER[1][:3]), A(EMBER[2][:3]), A(EMBER[3][:3]), A(EMBER[4][:3])]
CRUST = [A((22, 14, 16)), A((48, 30, 28)), A((80, 50, 40))]
STORM = [A((22, 40, 92)), A((40, 112, 204)), A((110, 204, 255)), A((206, 246, 255)), CORE]
WIND = [A((70, 96, 100)), A((118, 160, 150)), A((186, 226, 210)), A((236, 252, 244))]
SILVER = [A((52, 60, 96)), A((110, 128, 176)), A((190, 204, 236)), CORE]


# ---------------------------------------------------------------- helpers
def mask_poly(w, h, pts):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
    return m


def fill_mask(img, m, fn):
    w, h = img.size
    mp = m.load()
    for y in range(h):
        for x in range(w):
            if mp[x, y]:
                c = fn(x, y)
                if c:
                    img.putpixel((x, y), c)


def pline(img, pts, c):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            put(img, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)


def thick_pline(img, pts, c, r):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            disc(img, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, c)


def jag(x0, y0, x1, y1, n, amp, rnd):
    pts = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        nx, ny = -(y1 - y0), (x1 - x0)
        L = math.hypot(nx, ny) or 1
        o = rnd.uniform(-amp, amp)
        pts.append((x0 + (x1 - x0) * t + nx / L * o, y0 + (y1 - y0) * t + ny / L * o))
    pts.append((x1, y1))
    return pts


def ell_arc(img, cx, cy, rx, ry, a0, a1, c, step=None, keep=None):
    """Elliptical arc a0..a1 (degrees, screen-up positive)."""
    n = max(8, int(abs(a1 - a0) / 360 * 2 * math.pi * max(rx, ry) * 1.5))
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = cx + math.cos(a) * rx, cy - math.sin(a) * ry
        if keep and not keep(i / n, x, y):
            continue
        put(img, x, y, c(i / n) if callable(c) else c)


def dim(img, keep, seed=0):
    """Ordered fade: keep in 0..1."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and bt(x + seed, y + seed * 3) > keep:
                px[x, y] = TR
    return img


def build(name, W, H, layers, cels, ms, tags):
    """cels: list of {layer: img}; ms: int or list; tags: list of (tag, a, b) or a single tag name."""
    if isinstance(ms, int):
        ms = [ms] * len(cels)
    if isinstance(tags, str):
        tags = [(tags, 0, len(cels) - 1)]
    frames = [{"ms": m, "cels": {k: v for k, v in c.items()}} for m, c in zip(ms, cels)]
    asebuild.build(name, W, H, layers, frames, tags)
    return frames


def glow_disc(img, cx, cy, r, ramp, power=1.2):
    radial(img, cx, cy, r, ramp, power=power)


# ================================================================ ink seal glyph (floor trap)
def glyph_rim(W, H, cx, cy, rx, ry, k, bright):
    glow, core = blank(W, H), blank(W, H)
    # dark ink pool with ordered edge
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if d <= 1.0:
                if d > 0.8 and bt(x, y) < (d - 0.8) / 0.2:
                    continue
                glow.putpixel((x, y), INK[1] if d > 0.55 else INK[0])
    # outer and inner rings
    ell_arc(core, cx, cy, rx, ry, 0, 360, lambda t: INK[3] if (math.sin(t * 6.283) > 0.1) else INK[2])
    ell_arc(core, cx, cy, rx * 0.62, ry * 0.62, 0, 360, INK[3] if bright else INK[2])
    # runes: small gold ticks rotating around the ring gap
    for j in range(8):
        a = math.radians(j * 45 + k * 11)
        x, y = cx + math.cos(a) * rx * 0.81, cy - math.sin(a) * ry * 0.81
        c = G[4] if (j + k) % 4 == 0 and bright else (G[3] if j % 2 == 0 else G[2])
        put(core, x, y, c)
        put(core, x, y - 1, G[2] if j % 2 == 0 else INK[3])
    # the central star-sigil
    for j in range(5):
        a1, a2 = math.radians(90 + 144 * j + k * 4), math.radians(90 + 144 * (j + 1) + k * 4)
        pline(core, [(cx + math.cos(a1) * rx * 0.5, cy - math.sin(a1) * ry * 0.5),
                     (cx + math.cos(a2) * rx * 0.5, cy - math.sin(a2) * ry * 0.5)], G[3] if bright else G[2])
    put(core, cx, cy, CORE if bright else G[4])
    return glow, core


def fx_g_glyph():
    """Ink Seal floor glyph, perspective ellipse, loop of 6 (runes turn, the sigil pulses)."""
    W, H = 40, 14
    cels = []
    for k in range(6):
        glow, core = glyph_rim(W, H, 20, 8, 18, 5.2, k, k in (0, 1))
        # rising ink motes
        for j in range(3):
            x = 8 + j * 12 + (k * 3) % 5
            y = 6 - ((k * 2 + j * 3) % 6)
            put(core, x, y, INK[3] if j % 2 else G[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_glyph", W, H, ["Glow", "Core"], cels, 90, "g_glyph")


def fx_g_ink_burst():
    """Glyph detonation: violet-white flash, a splash of ink with gold rune shards, dispersing."""
    W, H = 64, 56
    cx, cy = 32, 32
    rnd = random.Random(7)
    shards = [(rnd.uniform(0, 6.283), rnd.uniform(0.7, 1.0)) for _ in range(10)]
    drops = [(rnd.uniform(0, 6.283), rnd.uniform(0.5, 1.0), rnd.uniform(1, 2.2)) for _ in range(14)]
    cels = []
    R = [6, 14, 20, 24, 26, 27, 28, 28]
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        r = R[k]
        if k == 0:
            radial(glow, cx, cy, 10, [INK[2], INK[3], INK[4], CORE])
            disc(core, cx, cy, 3, CORE)
        elif k <= 3:
            # ink splash body: lumpy blob that thins to a ring
            for y in range(H):
                for x in range(W):
                    dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.15
                    d = math.hypot(dx, dy)
                    a = math.atan2(dy, dx)
                    rr = r * (0.9 + 0.06 * math.sin(a * 3 + k) + 0.05 * math.sin(a * 7 + 2 * k))
                    if d > rr:
                        continue
                    inner = rr * (0.0 if k == 1 else (0.45 if k == 2 else 0.7))
                    if d < inner:
                        continue
                    q = (d - inner) / max(1, rr - inner)
                    if q > 0.8:
                        c = INK[3] if (x + y) % 3 else INK[4]
                        core.putpixel((x, y), c)
                    else:
                        glow.putpixel((x, y), INK[1] if q < 0.4 else INK[2])
            if k == 1:
                radial(core, cx, cy, 7, [INK[3], INK[4], CORE])
        else:
            ring(glow, cx, cy, r, r / 1.15, 1.3, INK[2], keep=1.0 - (k - 4) * 0.22, seed=k)
        # gold rune shards flying outward
        if k >= 1:
            for (a, s) in shards:
                d0 = r * s * 1.1
                x, y = cx + math.cos(a) * d0, cy + math.sin(a) * d0 / 1.15
                if k < 7:
                    put(core, x, y, G[4] if k < 4 else G[3])
                    put(core, x - math.cos(a) * 2, y - math.sin(a) * 2, G[2])
                    if k < 4:
                        put(core, x - math.cos(a) * 1, y - math.sin(a) * 1, G[3])
        # ink droplets
        if k >= 2:
            for (a, s, sz) in drops:
                d0 = r * s * 1.2 + (k - 2) * 1.5
                x, y = cx + math.cos(a) * d0, cy + math.sin(a) * d0 / 1.15 + (k - 2) ** 2 * 0.5
                if k < 7:
                    disc(glow, x, y, sz * (1 - (k - 2) * 0.12), INK[2] if k < 5 else INK[1])
        if k >= 5:
            dim(glow, 1.0 - (k - 4) * 0.25, k)
            dim(core, 1.0 - (k - 4) * 0.2, k + 1)
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": core})
    return build("fx_g_ink_burst", W, H, ["Glow", "Core"], cels, 50, "g_ink_burst")


def fx_g_rune():
    """Seeking rune (glyph swarm): a small violet diamond-glyph with a gold heart, loop of 4."""
    W, H = 14, 14
    cx, cy = 7, 7
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        radial(glow, cx, cy, 6.5, [INK[1], INK[2], INK[3]], power=0.8)
        rr = 3 + (1 if k % 2 == 0 else 0)
        pts = [(cx, cy - rr), (cx + rr, cy), (cx, cy + rr), (cx - rr, cy)]
        for (a, b) in zip(pts, pts[1:] + pts[:1]):
            pline(core, [a, b], INK[4] if k % 2 == 0 else INK[3])
        put(core, cx, cy, CORE)
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(core, cx + dx, cy + dy, G[3])
        # tick orbiting
        a = k * math.pi / 2
        put(core, cx + math.cos(a) * 5, cy + math.sin(a) * 5, G[4])
        # trail behind (left)
        put(glow, 1, cy, INK[2]); put(glow, 0, cy, INK[1])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_rune", W, H, ["Glow", "Core"], cels, 60, "g_rune")


# ================================================================ glacial wall
def ice_slab(W, H, height, seed, glint=None, crack=0):
    """Jagged glacier slab standing on the bottom row, x 6..22."""
    rnd = random.Random(seed)
    base, top = H - 1, H - 1 - height
    peaks = [(5, top + height * 0.28), (8, top + 2), (11, top + height * 0.18), (14, top),
             (17, top + height * 0.12), (20, top + 3), (23, top + height * 0.3)]
    pts = [(5, base + 1)] + peaks + [(23, base + 1)]
    m = mask_poly(W, H, pts)
    glow, core = blank(W, H), blank(W, H)

    def col(x, y):
        v = (x - 5) / 18
        yy = (y - top) / max(1, height)
        if x in (6, 7) or (y < top + 4 and x < 12):
            c = FROST[4] if (x + y) % 5 else FROST[3]
        elif v < 0.4:
            c = FROST[3] if yy < 0.5 else FROST[2]
        elif v < 0.75:
            c = FROST[2]
        else:
            c = FROST[1]
        return c
    fill_mask(core, m, col)
    # facet lines and cracks
    pline(core, [(14, top + 1), (12, top + height * 0.5), (13, base)], FROST[1])
    pline(core, [(8, top + 3), (9, top + height * 0.6), (8, base)], FROST[3])
    pline(core, [(20, top + 4), (18, top + height * 0.55), (19, base)], FROST[0])
    if crack:
        for j in range(crack):
            x0 = rnd.uniform(8, 20)
            y0 = rnd.uniform(top + 4, base - 4)
            pline(core, jag(x0, y0, x0 + rnd.uniform(-5, 5), y0 + rnd.uniform(6, 14), 3, 1.5, rnd), CORE)
    # outline in deep ice
    for y in range(H):
        for x in range(W):
            if core.getpixel((x, y))[3] == 0 and any(0 <= x + a < W and 0 <= y + b < H and core.getpixel((x + a, y + b))[3]
                                                    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                glow.putpixel((x, y), FROST[0])
    if glint is not None:
        gy = top + 2 + glint
        for i in range(-2, 3):
            if 0 <= gy + i < H:
                put(core, 7 + abs(i), gy + i, CORE)
        put(core, 6, gy, CORE); put(core, 8, gy - 2, CORE)
    return glow, core


def fx_g_icewall():
    """Glacial Wall: tags g_icewall_rise (5), g_icewall_idle (4, loop), g_icewall_shatter (6)."""
    W, H = 28, 52
    cels, ms, tags = [], [], []
    # rise
    for k, frac in enumerate((0.2, 0.5, 0.85, 1.08, 1.0)):
        glow, core = ice_slab(W, H, int(46 * frac), 1)
        rnd = random.Random(k)
        for j in range(8 - k):                                  # ground spray
            x = rnd.uniform(1, 27); y = H - 1 - rnd.uniform(0, 10) * (k + 1) / 3
            put(core, x, y, FROST[4] if j % 2 else FROST[3])
        cels.append({"Glow": glow, "Core": core}); ms.append(40)
    tags.append(("g_icewall_rise", 0, 4))
    for k in range(4):
        glow, core = ice_slab(W, H, 46, 1, glint=k * 11)
        cels.append({"Glow": glow, "Core": core}); ms.append(120)
    tags.append(("g_icewall_idle", 5, 8))
    # shatter: slab cracks, then breaks into shards that fly and fall
    rnd = random.Random(5)
    pieces = [(rnd.uniform(7, 21), rnd.uniform(8, 48), rnd.uniform(-60, 60), rnd.uniform(-70, -10), rnd.randint(2, 4)) for _ in range(16)]
    for k in range(6):
        if k == 0:
            glow, core = ice_slab(W, H, 46, 1, crack=6)
        else:
            glow, core = blank(W, H), blank(W, H)
            t = k * 0.05
            for (x0, y0, vx, vy, sz) in pieces:
                x = x0 + vx * t * 0.35
                y = y0 + vy * t * 0.35 + 300 * t * t * 0.5
                if y > H - 1:
                    y = H - 1
                pts = [(x, y - sz), (x + sz * 0.7, y), (x, y + sz * 0.6), (x - sz * 0.6, y)]
                m = mask_poly(W, H, pts)
                fill_mask(core, m, lambda xx, yy: FROST[4] if xx < x else (FROST[2] if yy < y else FROST[1]))
            if k >= 3:
                dim(core, 1.0 - (k - 2) * 0.22, k)
            radial(glow, 14, 30, 12 - k * 2, [FROST[1], FROST[2]]) if k < 3 else None
        cels.append({"Glow": glow, "Core": core}); ms.append(50)
    tags.append(("g_icewall_shatter", 9, 14))
    return build("fx_g_icewall", W, H, ["Glow", "Core"], cels, ms, tags)


# ================================================================ frost nova
def crystal(img, x, base, h, w, lit, mid, dark):
    pts = [(x - w, base + 1), (x - w * 0.4, base - h * 0.6), (x, base - h), (x + w * 0.5, base - h * 0.5), (x + w, base + 1)]
    m = mask_poly(img.width, img.height, pts)
    fill_mask(img, m, lambda xx, yy: lit if xx < x - 0.5 else (mid if xx < x + w * 0.4 else dark))


def fx_g_frost_nova():
    """Frost Nova: a white flash, then a ring of frost racing outward along the floor while
    ice crystals punch up out of the ground behind it, then crack and fade. Bottom-anchored."""
    W, H = 128, 56
    cx, base = 64, 55
    rnd = random.Random(11)
    spikes = sorted([(rnd.uniform(-1, 1), rnd.uniform(9, 22), rnd.uniform(2.2, 3.6)) for _ in range(14)], key=lambda s: -s[1])
    cels = []
    R = [6, 20, 34, 46, 54, 58, 60, 61]
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        r = R[k]
        # centre burst
        if k < 3:
            radial(glow, cx, base - 14, 16 - k * 3, [FROST[1], FROST[2], FROST[3], FROST[4]])
            if k == 0:
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    for i in range(14):
                        put(core, cx + dx * i, base - 14 + dy * i, FROST[4] if i < 6 else FROST[3])
        # floor ring (ellipse in perspective) + frost fog band
        keep = 1.0 if k < 5 else 1.0 - (k - 4) * 0.28
        ell_arc(core, cx, base - 5, r, 5, 0, 360, lambda t: FROST[4] if math.sin(t * 6.283) > 0 else FROST[3],
                keep=lambda t, x, y: bt(int(x), int(y)) < keep)
        ell_arc(glow, cx, base - 5, r * 0.92, 4.2, 0, 360, FROST[1], keep=lambda t, x, y: bt(int(x), int(y)) < keep * 0.8)
        # crystals behind the front
        for (u, h, w) in spikes:
            x = cx + u * min(r, 58)
            if abs(u) * 58 > r - 2:
                continue
            grow = min(1.0, (r - abs(u) * 58) / 16)
            hh = h * grow * (1 if k < 6 else 0.7)
            if k >= 6 and bt(int(x), 3) > 0.5:
                continue
            crystal(core, x, base - 4, hh, w, FROST[4], FROST[2], FROST[1])
        # drifting motes
        for j in range(12):
            a = j * 0.52 + k * 0.1
            x = cx + math.cos(a * 3) * r * 0.8
            y = base - 6 - (j % 5) * 4 - k * 2
            if 0 < y < H and k > 1:
                put(glow if j % 3 else core, x, y, FROST[3])
        if k >= 6:
            dim(core, 0.75 - (k - 6) * 0.3, k)
            dim(glow, 0.6 - (k - 6) * 0.3, k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_frost_nova", W, H, ["Glow", "Core"], cels, 45, "g_frost_nova")


# ================================================================ magma
def molten_ball(img, glow, cx, cy, r, k):
    radial(glow, cx, cy, r + 3, [LAVA[0], LAVA[1], LAVA[2]], power=0.7)
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            d = nx * nx + ny * ny
            if d > 1:
                continue
            v = -0.6 * nx - 0.8 * ny
            crust = (math.sin(nx * 5 + k * 1.3) + math.cos(ny * 6 - k * 0.9)) > 1.0 and v < 0.3
            if crust:
                c = CRUST[2] if v > -0.3 else CRUST[1]
            else:
                c = LAVA[4] if v > 0.55 else (LAVA[3] if v > 0.1 else (LAVA[2] if v > -0.45 else LAVA[1]))
            put(img, x, y, c)


def fx_g_magma_orb():
    W, H = 20, 20
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        molten_ball(core, glow, 11, 10, 5, k)
        put(core, 3, 10 + (k % 2), LAVA[3]); put(core, 1, 9, LAVA[2]); put(glow, 5, 12 - k % 2, LAVA[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_magma_orb", W, H, ["Glow", "Core"], cels, 70, "g_magma_orb")


def flame(img, bx, by, h, w, phase, ramp, dither=True):
    for i in range(int(h)):
        t = i / h
        hw = w * (1 - t) ** 0.75
        off = 1.2 * math.sin(t * 3.5 + phase)
        for x in range(int(bx - w - 3), int(bx + w + 4)):
            d = abs(x + 0.5 - bx - off)
            if d <= hw:
                q = d / max(0.5, hw)
                v = (1 - t) * (1 - 0.6 * q)
                if dither and t > 0.75 and bt(x, by - i) > (1 - t) * 4:
                    continue
                put(img, x, by - i, ramp_at(ramp, v, x, by - i))


def fx_g_magma_burst():
    """Magma orb burst: a dome of molten fire splashes up, globs arc out, smoke curls off."""
    W, H = 64, 48
    cx, base = 32, 47
    rnd = random.Random(3)
    globs = [(rnd.uniform(-1, 1) * 150, -rnd.uniform(120, 220), rnd.uniform(1.2, 2.2)) for _ in range(9)]
    cels = []
    for k in range(7):
        glow, core = blank(W, H), blank(W, H)
        t = k * 0.055
        if k < 4:
            rr = [8, 16, 20, 21][k]
            ell_glow(glow, cx, base - 2, rr + 6, rr * 0.8 + 4, [LAVA[0], LAVA[1], LAVA[2]])
            for j in range(7):
                u = (j - 3) / 3
                flame(core, cx + u * rr * 0.9, base, (rr * 1.3) * (1 - abs(u) * 0.55) * (1 if k < 3 else 0.7), 3.2 - abs(u), j + k,
                      [LAVA[0], LAVA[1], LAVA[2], LAVA[3], LAVA[4]])
        for (vx, vy, sz) in globs:
            x = cx + vx * t
            y = base - 6 + vy * t + 500 * t * t
            if y < base and k >= 1:
                disc(core, x, y, sz * (1 if k < 5 else 0.6), LAVA[3] if k < 4 else LAVA[2])
                put(core, x - 0.5, y - 0.5, LAVA[4])
        if k >= 3:
            for j in range(5):
                sx, sy = cx - 14 + j * 7, base - 10 - (k - 3) * 5 - (j % 2) * 4
                disc(glow, sx, sy, 3 + (k - 3) * 0.6, ASH[1] if j % 2 else ASH[2])
            dim(glow, 1.0 - (k - 3) * 0.2, k)
        if k >= 5:
            dim(core, 1.0 - (k - 4) * 0.3, k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_magma_burst", W, H, ["Glow", "Core"], cels, 55, "g_magma_burst")


def fx_g_fire_ground():
    """Burning ground: a molten seam on the floor with licking flames, loop of 6."""
    W, H = 56, 22
    base = H - 1
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        for x in range(2, W - 2):
            e = min(x - 2, W - 3 - x)
            if e < 3 and bt(x, 0) > e / 3:
                continue
            put(glow, x, base, LAVA[1]); put(glow, x, base - 1, LAVA[0])
            put(core, x, base, LAVA[3] if (x + k) % 4 else LAVA[4])
        for j in range(8):
            bx = 5 + j * 6.5 + (1 if (j + k) % 2 else 0)
            h = 6 + 7 * (0.5 + 0.5 * math.sin(k * 1.05 + j * 1.9))
            if 0 < j < 7:
                h += 3
            flame(core, bx, base - 1, h, 2.2, j * 1.3 + k * 1.05, [LAVA[0], LAVA[1], LAVA[2], LAVA[3], LAVA[4]])
        for j in range(4):
            x = (j * 14 + k * 5) % 52 + 2
            y = base - 8 - ((k + j * 2) % 6) * 2
            put(core, x, y, LAVA[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_fire_ground", W, H, ["Glow", "Core"], cels, 80, "g_fire_ground")


def ell_glow(img, cx, cy, rx, ry, ramp):
    """Elliptical ordered-dither glow (ramp dark -> light), never touching the frame edge."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if d > 1:
                continue
            v = 1 - d
            if v < 0.3 and bt(x, y) > v / 0.3:
                continue
            img.putpixel((x, y), ramp_at(ramp, v, x, y))


def fx_g_fissure():
    """Magma Quake fissure: the floor splits and glows, a tapering jet of lava erupts, then collapses."""
    W, H = 32, 64
    cx, base = 16, 63
    cels = []
    heights = [0, 0, 22, 48, 58, 50, 30, 12, 0]
    rnd = random.Random(9)
    for k in range(9):
        glow, core = blank(W, H), blank(W, H)
        crack = jag(4, base, 28, base, 6, 1.2, random.Random(4))
        pline(core, crack, LAVA[3] if k < 7 else LAVA[1])
        if k < 2:
            ell_glow(glow, cx, base, 7 + k * 3, 3 + k * 2, [LAVA[0], LAVA[1], LAVA[2]])
            for j in range(3 + k * 3):
                put(core, rnd.uniform(6, 26), base - rnd.uniform(1, 3 + k * 3), CRUST[2] if j % 2 else LAVA[3])
        h = heights[k]
        if h:
            ell_glow(glow, cx, base - h * 0.45, 9 if k < 6 else 7, h * 0.55 + 3, [LAVA[0], LAVA[1]])
            # main jet: a tapering tongue with a white-hot spine, wobbling
            for i in range(h):
                t = i / h
                hw = (4.6 if k < 6 else 3.4) * (1 - t) ** 0.55 + 0.6
                off = 1.3 * math.sin(t * 5 + k * 1.1)
                for x in range(W):
                    d = abs(x + 0.5 - cx - off)
                    if d > hw:
                        continue
                    if t > 0.8 and bt(x, base - i) > (1 - t) * 5:
                        continue
                    q = d / hw
                    v = (1 - t * 0.7) * (1 - 0.75 * q)
                    put(core, x, base - i, ramp_at([LAVA[0], LAVA[1], LAVA[2], LAVA[3], LAVA[4], CORE], v, x, base - i))
            for j in range(2):   # side tongues
                flame(core, cx + (-6 if j == 0 else 6), base, h * 0.3, 2.0, j + k, [LAVA[0], LAVA[1], LAVA[2], LAVA[3]])
            for j in range(4):   # flung droplets
                x = cx + rnd.uniform(-9, 9); y = base - rnd.uniform(0.5, 1.05) * h
                put(core, x, y, LAVA[3]); put(core, x, y + 1, LAVA[2])
        if k >= 6:
            for j in range(4):
                disc(glow, cx + (j - 1.5) * 5, base - 8 - (k - 5) * 7 - (j % 2) * 3, 2.2, ASH[1] if j % 2 else ASH[2])
            dim(glow, 1 - (k - 5) * 0.25, k)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_fissure", W, H, ["Glow", "Core"], cels, 45, "g_fissure")


# ================================================================ storm
def bolt_path(x0, y0, x1, y1, rnd, n=9, amp=5):
    return jag(x0, y0, x1, y1, n, amp, rnd)


def fx_g_bolt():
    """Stormcall strike: a jagged bolt from the sky with forks, ground flash, crackling afterglow."""
    W, H = 40, 128
    cx, base = 20, 127
    rnd = random.Random(21)
    main = bolt_path(cx + 3, 0, cx, base - 2, rnd, 12, 5)
    forks = []
    for i in (3, 6, 8):
        x, y = main[i]
        forks.append(bolt_path(x, y, x + rnd.choice((-1, 1)) * rnd.uniform(7, 13), y + rnd.uniform(12, 22), rnd, 4, 2.5))
    cels = []
    for k in range(7):
        glow, core = blank(W, H), blank(W, H)
        if k == 0:
            pline(glow, main[:5], STORM[1])
            radial(glow, cx, base - 2, 5, [STORM[1], STORM[2]])
        elif k <= 3:
            gw = 3 if k < 3 else 1.5
            thick_pline(glow, main, STORM[1] if k < 3 else STORM[0], gw)
            thick_pline(glow, main, STORM[2] if k < 3 else STORM[1], gw - 1 if gw > 1 else 0.5)
            thick_pline(core, main, CORE if k < 3 else STORM[3], 0.8 if k < 3 else 0.5)
            if k < 3:
                for f in forks:
                    pline(glow, f, STORM[2]); pline(core, f[:3], STORM[3])
            # ground flash
            rr = [0, 16, 19, 13][k]
            radial(glow, cx, base - 1, rr, [STORM[0], STORM[1], STORM[2], STORM[3]], power=0.9)
            if k == 1:
                for (dx, dy) in ((1, 0), (-1, 0), (0, -1)):
                    for i in range(16):
                        put(core, cx + dx * i, base - 2 + dy * i, CORE if i < 6 else STORM[3])
        else:
            # afterglow: flicker of the lower bolt + sparks skittering on the floor
            seg = main[-(8 - k):]
            if k < 5:
                pline(glow, seg, STORM[1])
            for j in range(6):
                x = cx + (j - 2.5) * (4 + (k - 3) * 3)
                y = base - 1 - ((j + k) % 3)
                put(core, x, y, STORM[3] if k < 5 else STORM[2])
                put(core, x - (1 if j < 3 else -1), y + 1, STORM[1])
            ell_arc(glow, cx, base - 1, 6 + k * 2, 1.5, 0, 180, STORM[1] if k < 5 else STORM[0])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_bolt", W, H, ["Glow", "Core"], cels, [30, 45, 45, 50, 60, 60, 60], "g_bolt")


def fx_g_spark():
    """Lightning impact: a crackling star of short zig-zag rays, cyan -> white core."""
    W, H = 28, 28
    cx, cy = 14, 14
    cels = []
    for k in range(5):
        glow, core = blank(W, H), blank(W, H)
        rnd = random.Random(30 + k)
        L = [6, 12, 11, 8, 4][k]
        if k < 3:
            radial(glow, cx, cy, L * 0.7, [STORM[0], STORM[1], STORM[2]])
        for j in range(6):
            a = j * math.pi / 3 + k * 0.4
            pts = jag(cx, cy, cx + math.cos(a) * L, cy + math.sin(a) * L, 3, 1.4, rnd)
            pline(glow if k >= 3 else core, pts, STORM[3] if k < 2 else STORM[2])
        if k < 3:
            disc(core, cx, cy, 2 - k * 0.5, CORE)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_spark", W, H, ["Glow", "Core"], cels, 40, "g_spark")


# ================================================================ wind
def fx_g_wind_ward():
    """Wind Ward: three wind streaks orbiting the body (tilted ellipse), loop of 6."""
    W, H = 56, 56
    cx, cy = 28, 28
    cels = []
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        for j in range(3):
            a0 = j * 120 + k * 20
            for i in range(40):
                t = i / 39
                a = math.radians(a0 + t * 95)
                r = 20 + 2 * math.sin(t * math.pi)
                x, y = cx + math.cos(a) * r, cy - math.sin(a) * r * 0.82
                c = WIND[3] if t > 0.8 else (WIND[2] if t > 0.45 else WIND[1])
                if t < 0.3 and bt(int(x), int(y)) > t / 0.3:
                    continue
                put(core, x, y, c)
                if t > 0.4:
                    put(glow, cx + math.cos(a) * (r - 1.3), cy - math.sin(a) * (r - 1.3) * 0.82, WIND[1])
        # inner faint ring
        ell_arc(glow, cx, cy, 16, 13, 0, 360, WIND[0], keep=lambda t, x, y: bt(int(x), int(y)) < 0.35)
        for j in range(4):
            a = math.radians(k * 25 + j * 90)
            put(core, cx + math.cos(a) * 23, cy - math.sin(a) * 19, WIND[3])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_wind_ward", W, H, ["Glow", "Core"], cels, 60, "g_wind_ward")


def fx_g_whirl():
    """Whirlwind: a flat spinning disc of wind and a blurred gold staff arc, loop of 4."""
    W, H = 76, 40
    cx, cy = 38, 22
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        for j in range(4):
            a0 = j * 90 + k * 22
            for i in range(50):
                t = i / 49
                a = math.radians(a0 + t * 70)
                rx, ry = 34 - j * 3, 12 - j
                x, y = cx + math.cos(a) * rx, cy - math.sin(a) * ry
                if t < 0.35 and bt(int(x), int(y)) > t / 0.35:
                    continue
                put(core, x, y, WIND[3] if t > 0.75 else WIND[2])
                put(glow, x, y + 1, WIND[1] if t > 0.4 else WIND[0])
        # staff blur: a bright arc sweeping the front
        a0 = k * 90
        ell_arc(core, cx, cy, 26, 8, a0, a0 + 60, lambda t: G[4] if t > 0.7 else (G[3] if t > 0.35 else G[2]))
        ell_arc(glow, cx, cy, 25, 7, a0, a0 + 60, G[1])
        for j in range(5):
            x = cx - 30 + j * 15 + (k * 4) % 15
            put(core, x, cy + 12, WIND[2])
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_whirl", W, H, ["Glow", "Core"], cels, 50, "g_whirl")


# ================================================================ toll + aegis + x-cut
def fx_g_toll():
    """Tolling Blow: bronze sound-rings bursting from the impact, dashed as they widen."""
    W, H = 120, 64
    cx, cy = 60, 40
    cels = []
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        if k < 2:
            radial(glow, cx, cy, 14 - k * 4, [G[1], G[2], G[3], G[4]])
            disc(core, cx, cy, 3 - k, CORE)
        for j in range(3):
            r = 8 + k * 7 - j * 11
            if r < 4:
                continue
            keep = 1.0 - max(0, (r - 30) / 40)
            dash = lambda t, x, y, j=j: (int(t * 40) + j) % 5 != 0 and bt(int(x), int(y)) < keep
            ell_arc(core, cx, cy, r, r * 0.55, 0, 360, G[3] if j == 0 else G[2], keep=dash)
            ell_arc(glow, cx, cy, r - 1.2, r * 0.55 - 0.8, 0, 360, G[1], keep=dash)
        cels.append({"Glow": glow, "Core": core})
    return build("fx_g_toll", W, H, ["Glow", "Core"], cels, 50, "g_toll")


def aegis_sheet(name, tag, ramp):
    """A curved guard barrier held in front (convex RIGHT), glyph ticks shimmering along it."""
    W, H = 28, 48
    cels = []
    for k in range(4):
        glow, core = blank(W, H), blank(W, H)
        cx, cy = 2, 24
        for y in range(H):
            for x in range(W):
                dx, dy = (x + 0.5 - cx) / 20, (y + 0.5 - cy) / 22
                d = math.hypot(dx, dy)
                if 0.86 <= d <= 1.0 and x > cx + 4:
                    q = (d - 0.86) / 0.14
                    core.putpixel((x, y), ramp[3] if q > 0.66 else (ramp[2] if q > 0.3 else ramp[1]))
                elif 0.6 <= d < 0.86 and x > cx + 4:
                    if bt(x, y + k) < (d - 0.6) / 0.26 * 0.7:
                        glow.putpixel((x, y), ramp[1] if d > 0.76 else ramp[0])
        # shimmering hex ticks travelling down the rim
        for j in range(4):
            a = math.radians(70 - ((k * 12 + j * 35) % 140))
            x, y = cx + math.cos(a) * 20.5, cy - math.sin(a) * 22
            put(core, x, y, ramp[4]); put(core, x - 1, y, ramp[3])
        cels.append({"Glow": glow, "Core": core})
    return build(name, W, H, ["Glow", "Core"], cels, 80, tag)


def fx_g_aegis():
    return aegis_sheet("fx_g_aegis", "g_aegis", [G[0], G[1], G[2], G[3], CORE])


def fx_g_frost_aegis():
    return aegis_sheet("fx_g_frost_aegis", "g_frost_aegis", [FROST[0], FROST[1], FROST[2], FROST[3], FROST[4]])


def fx_g_xcut():
    """Twin Tempest finisher: two crossing blade cuts drawn one after the other, then flaring."""
    W, H = 56, 56
    cels = []
    cuts = [((6, 10), (50, 46)), ((6, 46), (50, 10))]
    for k in range(6):
        glow, core = blank(W, H), blank(W, H)
        for ci, (a, b) in enumerate(cuts):
            prog = min(1.0, max(0.0, (k + 1 - ci * 1.2) / 2.0))
            if prog <= 0:
                continue
            fade = 1.0 if k < 4 else 1.0 - (k - 3) * 0.33
            ex, ey = a[0] + (b[0] - a[0]) * prog, a[1] + (b[1] - a[1]) * prog
            L = math.hypot(ex - a[0], ey - a[1])
            n = int(L)
            for i in range(n + 1):
                t = i / max(1, n)
                x, y = a[0] + (ex - a[0]) * t, a[1] + (ey - a[1]) * t
                w = 2.4 * math.sin(math.pi * min(1, t * prog)) if prog >= 1 else 2.4 * t
                if bt(int(x), int(y)) > fade:
                    continue
                disc(glow, x, y, w + 1, CR[1])
                disc(core, x, y, max(0.5, w * 0.6), SILVER[2])
                put(core, x, y, CORE)
        if k in (3, 4):
            radial(glow, 28, 28, 9 - (k - 3) * 3, [CR[1], CR[2], CR[3], CORE])
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": core})
    return build("fx_g_xcut", W, H, ["Glow", "Core"], cels, 40, "g_xcut")


# ================================================================ preview
BG = (92, 92, 100, 255)
CELL = (40, 38, 50, 255)


def preview(results, S=2):
    rows = []
    for name, frames, layers in results:
        cw = max(Image.new("RGBA", (1, 1)).width, frames[0]["cels"][layers[0]].width)
        chh = frames[0]["cels"][layers[0]].height
        row = Image.new("RGBA", (len(frames) * (cw + 4) + 4, chh + 8), BG)
        for i, f in enumerate(frames):
            cell = Image.new("RGBA", (cw, chh), CELL)
            for L in layers:
                if L in f["cels"]:
                    cell.alpha_composite(f["cels"][L])
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
        d.text((4, y * S + 4), name.replace("fx_g_", ""), fill=(255, 255, 255, 255)); y += r.height
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sheet.save(os.path.join(pdir, "fx4.png"))


ALL = [fx_g_glyph, fx_g_ink_burst, fx_g_rune, fx_g_icewall, fx_g_frost_nova, fx_g_magma_orb, fx_g_magma_burst,
       fx_g_fire_ground, fx_g_fissure, fx_g_bolt, fx_g_spark, fx_g_wind_ward, fx_g_whirl, fx_g_toll, fx_g_aegis,
       fx_g_frost_aegis, fx_g_xcut]

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
