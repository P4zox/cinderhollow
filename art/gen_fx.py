#!/usr/bin/env python3
"""Combat effect sprites -> art/fx_*.aseprite, assets/fx_*.png/.json

Each effect is its own sprite with >= 2 layers and a single tag (name without "fx_").
Plain RGBA, bright "additive-looking" colours, no blend modes.
Re-runnable: python3 art/gen_fx.py
"""
import os, sys, math, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402


def C(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ---------------------------------------------------------------- palette
WHITE = C("ffffff")
SILVER = [C(c) for c in ("3c4c80", "6a86c0", "a8c0ec", "dce8ff")]          # dark edge -> near white
EMBER = [C(c) for c in ("7a2210", "c8461a", "f07c28", "ffb65a", "ffe2a0")]
GOLD = [C(c) for c in ("6e4012", "b8761c", "e8a830", "ffd466", "fff2b8")]
BLOOD = [C(c) for c in ("2c040a", "520812", "7e121c", "a8202a")]
DUST = [C(c) for c in ("3a3544", "58525f", "7a7280", "9e96a2")]
ROCK = [C(c) for c in ("1e1a22", "3a3440", "5e5462", "8a7e86")]
AMBER_DK = C("4a2408")
# molten ramp: dark amber falloff -> amber -> gold -> pale gold -> white-hot core
MOLTEN = [AMBER_DK, GOLD[0], GOLD[1], GOLD[2], GOLD[3], GOLD[4], WHITE]
TRANSPARENT = (0, 0, 0, 0)

B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bt(x, y):
    return (B4[y & 3][x & 3] + 0.5) / 16.0


def blank(w, h):
    return Image.new("RGBA", (w, h), TRANSPARENT)


def pick(ramp, v, x, y):
    v = 0.0 if v < 0 else (1.0 if v > 1 else v)
    f = v * (len(ramp) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return ramp[min(i, len(ramp) - 1)]


def clean(img, min_n=1, ref=()):
    """Remove stray pixels that have fewer than min_n opaque 8-neighbours.
    Pixels in the sibling layers given in ref count as neighbours too."""
    w, h = img.size
    px = img.load()
    refs = [r.load() for r in ref]
    kill = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h and (
                            px[x + dx, y + dy][3] or any(r[x + dx, y + dy][3] for r in refs)):
                        n += 1
            if n < min_n:
                kill.append((x, y))
    for p in kill:
        px[p] = TRANSPARENT
    return img


def put(img, x, y, c):
    w, h = img.size
    x, y = int(round(x)), int(round(y))
    if 0 <= x < w and 0 <= y < h:
        img.putpixel((x, y), c)


def disc(img, cx, cy, r, c):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                put(img, x, y, c)


def line(img, x0, y0, x1, y1, c):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        put(img, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)


def breakup(img, keep, seed, block=2):
    """Clean fade: drop whole block x block clusters (not single-pixel dither)."""
    w, h = img.size
    px = img.load()
    for by in range(0, h, block):
        for bx in range(0, w, block):
            if random.Random(seed * 7919 + bx * 131 + by * 17).random() >= keep:
                for y in range(by, min(h, by + block)):
                    for x in range(bx, min(w, bx + block)):
                        px[x, y] = TRANSPARENT
    return clean(img)


def merge(a, b):
    out = a.copy()
    out.alpha_composite(b)
    return out


def emit(name, w, h, layers, frame_cels, ms, tag):
    frames = [{"ms": ms, "cels": cels} for cels in frame_cels]
    asebuild.build(name, w, h, layers, frames, [(tag, 0, len(frames) - 1)])
    return frames


# ---------------------------------------------------------------- crescent arcs
def crescent(w, h, cx, cy, rx, ry, tail, head, thick, colour_fn, fade=1.0, mirror=False,
             halo=0.0, halo_fn=None, peak=0.75, tail_taper=True):
    """Draw a crescent sweep on an elliptical path.

    Angles in degrees, counter-clockwise from +x with screen-up positive; any range is
    allowed (wraps through 180/-180). The arc spans tail->head (head = leading tip).
    thick = max band thickness in pixels. The band lies between the outer ellipse and a
    shrunken inner ellipse (moon-crescent construction).
    colour_fn(s, u, x, y) -> (layer, colour) or None; s = 0 at the outer (cutting) edge
    .. 1 at the inner edge, u = 0 at tail .. 1 at head. layer 0 = core, 1 = glow.
    halo > 0 adds an outer falloff band (pixels) drawn by halo_fn(q, u, x, y) into the
    halo layer, q = 0 at the blade edge .. 1 at the halo's outer limit.
    Returns (core, glow, halo) images."""
    core, glow, hal = blank(w, h), blank(w, h), blank(w, h)
    lo = min(tail, head)
    span = abs(head - tail)
    for y in range(h):
        for x in range(w):
            dx = (x + 0.5 - cx) / rx
            dy = -(y + 0.5 - cy) / ry
            r = math.hypot(dx, dy)
            if r == 0:
                continue
            a = math.degrees(math.atan2(dy, dx))
            while a < lo:
                a += 360
            while a >= lo + 360:
                a -= 360
            if a > lo + span:
                continue
            u = (a - tail) / (head - tail)
            # crescent profile: sharp at both tips, fattest toward the head
            if tail_taper:
                prof = math.sin(math.pi * min(1.0, u ** peak)) ** 0.8
            else:
                prof = min(1.0, (1 - u) * 6) ** 0.8
            th = thick * prof
            if th <= 0.6:
                continue
            px_, py_ = dx * rx, dy * ry
            if r > 1.0:
                if halo > 0 and halo_fn:
                    grad = math.hypot(dx / rx, dy / ry) / r
                    dout = (r - 1.0) / grad
                    q = dout / (halo * min(1.0, prof * 1.6))
                    if q <= 1.0:
                        if fade < 1.0 and fade < bt(x, y):
                            continue
                        c = halo_fn(q, u, x, y)
                        if c:
                            hal.putpixel((x, y), c)
                continue
            r_in = math.hypot(px_ / max(1.0, rx - th), py_ / max(1.0, ry - th * 0.7))
            if r_in < 1.0:
                continue
            s = (1.0 - r) / max(1e-6, (1.0 - r) + (r_in - 1.0))
            if fade < 1.0 and fade < bt(x, y):
                continue
            res = colour_fn(s, u, x, y)
            if res is None:
                continue
            li, c = res
            (core if li == 0 else glow).putpixel((x, y), c)
    if mirror:
        core = core.transpose(Image.FLIP_LEFT_RIGHT)
        glow = glow.transpose(Image.FLIP_LEFT_RIGHT)
        hal = hal.transpose(Image.FLIP_LEFT_RIGHT)
    return clean(core, ref=(glow, hal)), clean(glow, ref=(core, hal)), clean(hal, ref=(core, glow))


def silver_fn(dim=0.0):
    def f(s, u, x, y):
        v = (1 - s) * (0.55 + 0.45 * u) - dim
        if s < 0.18 and u > 0.25:
            return (0, WHITE if dim < 0.2 else SILVER[3])
        if v > 0.55:
            return (0, SILVER[3])
        if v > 0.3:
            return (1, SILVER[2])
        if v > 0.12:
            return (1, SILVER[1])
        if v > 0.12 * bt(x, y) + 0.02:
            return (1, SILVER[0])
        return None
    return f


def silver_tail_fn(s, u, x, y):
    """Fading tail: a crisp thin crescent that cools from pale blue to deep blue."""
    if s < 0.4 and u > 0.45:
        return (0, SILVER[2])
    if s < 0.7:
        return (1, SILVER[1])
    return (1, SILVER[0])


def heavy_fn(dim=0.0):
    def f(s, u, x, y):
        v = (0.55 + 0.45 * u) - dim
        if s < 0.14:
            return (0, WHITE if v > 0.6 else SILVER[3])
        if s < 0.30:
            return (0, SILVER[3] if v > 0.5 else SILVER[2])
        if s < 0.50:
            return (1, EMBER[4] if v > 0.7 else EMBER[3])
        if s < 0.72:
            return (1, EMBER[2] if v > 0.45 else EMBER[1])
        if s < 0.9 or bt(x, y) < 0.5:
            return (1, EMBER[1] if v > 0.6 else EMBER[0])
        return None
    return f


def gold_fn(dim=0.0):
    def f(s, u, x, y):
        v = (0.5 + 0.5 * u) - dim          # brighter toward the leading tip
        if s < 0.16 and u > 0.2:
            return (0, WHITE if dim < 0.2 else GOLD[4])
        if s < 0.36:
            return (0, GOLD[4] if v > 0.5 else GOLD[3])
        if s < 0.62:
            return (1, GOLD[3] if v > 0.55 else GOLD[2])
        if s < 0.85:
            return (1, GOLD[2] if v > 0.55 else GOLD[1])
        return (1, GOLD[1] if v > 0.6 else GOLD[0])
    return f


def fx_slash():
    W, H = 48, 32
    # (tail, head, thickness, fade, dim)
    keys = [(96, 62, 5, 1.0, 0.0), (100, -24, 9, 1.0, 0.0),
            (66, -50, 8, 1.0, 0.15), (10, -54, 3.5, 1.0, -1)]
    cels = []
    for (tail, head, th, fade, dim) in keys:
        fn = silver_tail_fn if dim < 0 else silver_fn(dim)
        core, glow, _ = crescent(W, H, 6, 18, 36, 17, tail, head, th, fn, fade)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_slash", W, H, ["Glow", "Core"], cels, 40, "slash")


def fx_heavy():
    W, H = 64, 40
    keys = [(112, 90, 7, 1.0, 0.0), (114, 40, 11, 1.0, 0.0), (110, 0, 13, 1.0, 0.0),
            (64, -6, 11, 1.0, 0.15), (26, -6, 8, 0.55, 0.35)]
    cels = []
    rnd = random.Random(5)
    for i, (tail, head, th, fade, dim) in enumerate(keys):
        core, glow, _ = crescent(W, H, 18, 38, 41, 34, tail, head, th, heavy_fn(dim), fade)
        sparks = blank(W, H)
        if i >= 3:   # embers kicked up where the blade meets the ground
            for k in range(6):
                sx = 50 + rnd.uniform(-6, 8)
                sy = 36 - rnd.uniform(1, 10) * (i - 2)
                c = EMBER[3] if (k + i) % 2 else EMBER[2]
                put(sparks, sx, sy, c)
                put(sparks, sx - 1, sy + 1, EMBER[1])
        cels.append({"Glow": glow, "Core": core, "Sparks": sparks})
    return emit("fx_heavy", W, H, ["Glow", "Core", "Sparks"], cels, 50, "heavy")


def fx_boss_slash():
    W, H = 96, 48
    keys = [(90, 62, 7, 1.0, 0.0), (96, 12, 13, 1.0, 0.0),
            (72, -14, 11, 1.0, 0.15), (34, -22, 7, 0.5, 0.35)]
    cels = []
    for (tail, head, th, fade, dim) in keys:
        # drawn swinging right, then mirrored so it sweeps to the LEFT
        core, glow, _ = crescent(W, H, 14, 36, 66, 30, tail, head, th, gold_fn(dim), fade, mirror=True)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_boss_slash", W, H, ["Glow", "Core"], cels, 50, "boss_slash")


# ---------------------------------------------------------------- shockwave
ROCK_SHAPES = [
    ["LM", "MD"],
    ["LMM", "MMD"],
    [".LM", "LMD", "MD."],
    ["LL.", "MMD", ".DD"],
]


def rock(img, x, y, shape, flip, glow=False):
    rows = ROCK_SHAPES[shape]
    cmap = {"L": ROCK[3], "M": ROCK[2], "D": ROCK[1]}
    for j, row in enumerate(rows):
        if flip:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch in cmap:
                put(img, x + i, y + j, cmap[ch])
    # dark underside + faint gold under-light from the wave
    put(img, x + (0 if flip else len(rows[-1]) - 1), y + len(rows), ROCK[0])
    if glow:
        put(img, x + len(rows[-1]) // 2, y + len(rows), GOLD[1])


def fx_shockwave():
    """Rolling energy wave: a curling crest (lip overhangs the front) trailing a sloped
    body with flow lines; both directions from bottom-centre (48, 31)."""
    W, H = 96, 32
    G = H - 1
    CX = 48
    front = [6, 14, 23, 32, 40, 46]
    crest = [7, 12, 14, 12, 9, 5]
    tail = [5, 8, 11, 13, 14, 14]
    rnd = random.Random(21)
    rocks = [(sd * rnd.uniform(0.7, 2.0), rnd.uniform(3.0, 4.0), rnd.randrange(4))
             for sd in (-1, 1, -1, 1, 1, -1, 1)]
    cels = []
    for k in range(6):
        wave, glow, debris = blank(W, H), blank(W, H), blank(W, H)
        R_, Hh, L = front[k], crest[k], tail[k]
        dim = 0 if k < 3 else (1 if k < 5 else 2)
        FW = 5.0                                  # forward half-width of the dome
        for side in (-1, 1):
            for x in range(W):
                d = (x - CX) * side
                if d < 0:
                    continue
                b = R_ - d                       # distance behind the leading edge
                u = (FW - 1) - b                 # position relative to the dome centre (+ = ahead)
                if u > FW + 2.5 or u < -L - 1:
                    continue
                if u >= FW - 0.5:
                    # curling lip: a short tongue hanging ahead of the face, hollow beneath
                    ext = u - (FW - 0.5)
                    y0 = G - Hh + int(round(ext * 1.2))
                    y1 = y0 + max(0, int(round(2.4 - ext)))
                    for y in range(y0, y1 + 1):
                        wave.putpixel((x, y), MOLTEN[max(1, 6 - dim - (1 if ext > 1.5 else 0))])
                    continue
                if u >= 0:
                    hcol = Hh * math.sqrt(max(0.0, 1 - (u / FW) ** 2))
                else:
                    hcol = Hh * max(0.0, 1 - (-u / (L + 1)) ** 2) ** 0.8
                hcol = int(round(hcol))
                if hcol <= 0:
                    continue
                top = G - hcol + 1
                for y in range(G, top - 1, -1):
                    t = (G - y) / max(1.0, hcol)
                    rim = y <= top + (1 if u > -3 else 0)
                    if rim:
                        idx = 6 if u > -2 else (5 if u > -L * 0.5 else 4)
                        lay = wave
                    elif u > FW - 2.2:
                        idx = 5 if t > 0.25 else 6        # hot leading face
                        lay = wave
                    else:
                        depth = (y - top) / max(1.0, hcol)
                        idx = 4 if depth < 0.3 else (3 if depth < 0.7 else 2)
                        if (y + k + (x // 3)) % 4 == 0 and depth < 0.8:
                            idx += 1                      # flow lines rolling back
                        lay = wave if idx >= 5 else glow
                    idx -= dim
                    if idx <= 0:
                        continue
                    lay.putpixel((x, y), MOLTEN[idx])
                # 1px amber haze above the dome (ordered falloff)
                if top - 1 >= 0 and bt(x, top - 1) < 0.5 and dim < 2:
                    glow.putpixel((x, top - 1), MOLTEN[1])
            # glowing fissure along the ground behind the wave
            for dd in range(0, R_):
                x = CX + side * dd
                if 0 <= x < W and not wave.getpixel((x, G))[3]:
                    c = MOLTEN[max(1, (4 if dd > R_ - 8 else 3) - dim)]
                    glow.putpixel((x, G), c)
        if k >= 4:
            breakup(glow, 0.7 if k == 4 else 0.5, 60 + k)
        # debris: chunky rocks in parabolas, tumbling (mirror every other frame)
        t = (k + 1) * 0.9
        for i, (vx, vy, sh) in enumerate(rocks):
            x = CX + vx * t * 3.2
            y = G - 4 - (vy * t * 3.0 - t * t * 1.9)
            if y > G - 2:
                continue
            rock(debris, x, y, sh, (k + i) % 2 == 1, glow=k < 3)
        cels.append({"Glow": clean(glow, ref=(wave,)), "Wave": clean(wave, ref=(glow,)), "Debris": debris})
    return emit("fx_shockwave", W, H, ["Glow", "Wave", "Debris"], cels, 60, "shockwave")


# ---------------------------------------------------------------- hit spark
def star(img, cx, cy, arms, c_core, c_edge):
    """arms: list of (angle_deg, inner, outer). Rays tapered 2px -> 1px."""
    for (ang, r0, r1) in arms:
        a = math.radians(ang)
        n = int((r1 - r0) * 2) + 1
        for i in range(n + 1):
            r = r0 + (r1 - r0) * i / n
            x, y = cx + math.cos(a) * r, cy - math.sin(a) * r
            put(img, x, y, c_core if r < r0 + (r1 - r0) * 0.55 else c_edge)


def fx_hit():
    W, H = 24, 24
    cx = cy = 11.5
    cels = []
    for k in range(4):
        core, glow = blank(W, H), blank(W, H)
        if k == 0:
            disc(glow, cx, cy, 3.2, GOLD[3])
            disc(core, cx, cy, 1.8, WHITE)
            star(core, cx, cy, [(a, 2, 5) for a in (0, 90, 180, 270)], WHITE, GOLD[4])
        elif k == 1:
            disc(glow, cx, cy, 4.2, GOLD[3])
            disc(glow, cx, cy, 3.0, GOLD[4])
            disc(core, cx, cy, 2.2, WHITE)
            star(glow, cx, cy, [(a, 3, 8) for a in (45, 135, 225, 315)], GOLD[3], GOLD[2])
            star(core, cx, cy, [(a, 3, 11) for a in (0, 90, 180, 270)], WHITE, GOLD[4])
            # thicken cardinal rays near the centre
            for (dx, dy) in ((3, 1), (4, 1), (-3, 1), (-4, 1), (1, 3), (1, 4), (1, -3), (1, -4),
                             (3, -1), (-3, -1), (-1, 3), (-1, -3)):
                put(core, cx + dx, cy + dy, GOLD[4])
        elif k == 2:
            disc(glow, cx, cy, 2.2, GOLD[2])
            put(core, cx, cy, GOLD[4])
            star(core, cx, cy, [(a, 6, 11) for a in (0, 90, 180, 270)], GOLD[4], GOLD[3])
            star(glow, cx, cy, [(a, 6, 10) for a in (45, 135, 225, 315)], GOLD[3], GOLD[2])
        else:
            for a in (22, 112, 202, 292, 0, 90, 180, 270):
                r = 10 if a % 90 == 0 else 8
                x, y = cx + math.cos(math.radians(a)) * r, cy - math.sin(math.radians(a)) * r
                x2, y2 = cx + math.cos(math.radians(a)) * (r + 1.5), cy - math.sin(math.radians(a)) * (r + 1.5)
                line(glow if a % 90 else core, x, y, x2, y2, GOLD[2] if a % 90 else GOLD[3])
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,))})
    return emit("fx_hit", W, H, ["Glow", "Core"], cels, 40, "hit")


# ---------------------------------------------------------------- blood
def fx_blood():
    W, H = 24, 24
    cx, cy = 11.5, 11.5
    rnd = random.Random(3)
    drops = []
    for i in range(11):
        a = math.radians(i * (360 / 11) + rnd.uniform(-12, 12) + 10)
        drops.append((math.cos(a) * rnd.uniform(1.5, 2.2), -math.sin(a) * rnd.uniform(1.4, 2.0) - 0.5,
                      rnd.uniform(1.0, 1.9)))
    cels = []
    for k in range(5):
        splash, dl = blank(W, H), blank(W, H)
        # central burst clump
        rc = [3.2, 4.2, 3.0, 1.6, 0][k]
        if rc:
            for y in range(H):
                for x in range(W):
                    dx, dy = x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5
                    ang = math.atan2(dy, dx)
                    rr = rc * (1 + 0.28 * math.sin(ang * 5 + k))
                    d = math.hypot(dx, dy)
                    if d <= rr:
                        c = BLOOD[3] if (d < rr * 0.45 and dy < 0) else (BLOOD[2] if d < rr * 0.8 else BLOOD[1])
                        splash.putpixel((x, y), c)
        # droplets on ballistic paths, stretched along velocity early on
        t = k + 1
        for (vx, vy, sz) in drops:
            x = cx + vx * t
            y = cy + vy * t + 0.22 * t * t
            s = sz * (1.0 - 0.1 * k)
            if s < 0.5:
                continue
            # trail
            if k < 3:
                line(dl, x - vx * 0.8, y - (vy + 0.44 * t) * 0.8, x, y, BLOOD[1])
            disc(dl, x, y, s * 0.75, BLOOD[2])
            put(dl, x, y, BLOOD[3] if k < 3 else BLOOD[2])
        if k == 4:
            # last frame: drops only, thinning
            for yy in range(H):
                for xx in range(W):
                    if dl.getpixel((xx, yy))[3] and bt(xx, yy) > 0.6:
                        dl.putpixel((xx, yy), BLOOD[0])
        cels.append({"Droplets": clean(dl, ref=(splash,)), "Splash": clean(splash, ref=(dl,))})
    return emit("fx_blood", W, H, ["Droplets", "Splash"], cels, 50, "blood")


# ---------------------------------------------------------------- heal
def fx_heal():
    W, H = 32, 40
    cx = 15.5
    FEET = 37
    cels = []
    motes = [(-9, 0.0, 2), (-4, 0.35, 1), (1, 0.7, 2), (6, 0.15, 1), (10, 0.5, 2), (-11, 0.8, 1),
             (3, 0.95, 1), (-2, 0.55, 2), (8, 0.85, 1)]
    for k in range(6):
        ring, mo = blank(W, H), blank(W, H)
        # ground ring: expands and fades
        rx = [6, 9, 11.5, 13, 14, 14.5][k]
        ry = rx * 0.28
        dens = [1, 1, 1, 1, 1, 0.0][k]
        for y in range(H):
            for x in range(W):
                d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - FEET) / ry)
                if 0.78 <= d <= 1.12 and dens > 0:
                    if dens < 1 and dens < bt(x, y):
                        continue
                    front = y + 0.5 > FEET
                    c = GOLD[3] if front else GOLD[2]
                    if abs(d - 0.95) < 0.1 and front and k < 3:
                        c = GOLD[4]
                    ring.putpixel((x, y), c)
        if k == 4:
            breakup(ring, 0.5, 44)
        # rising light streaks (clean vertical dashes instead of a dithered column)
        for (ox, ph, ln) in ((-6, 0.1, 6), (-2, 0.55, 8), (3, 0.3, 7), (7, 0.8, 5)):
            p = (ph + k / 6.0) % 1.0
            if k == 0 or p > 0.85:
                continue
            ytop = FEET - 3 - p * 30
            for j in range(ln):
                put(ring, cx + ox, ytop + j, GOLD[2] if j < ln // 2 else GOLD[1])
        # motes rise with a gentle sway; bigger ones are 4-point sparkles
        for (ox, phase, sz) in motes:
            p = (phase + k / 6.0) % 1.0
            y = FEET - 2 - p * 32
            x = cx + ox + math.sin((p + ox) * 6.0) * 1.2
            if p > 0.92:
                continue
            bright = GOLD[4] if p < 0.6 else GOLD[3]
            if sz == 2:
                put(mo, x, y, WHITE if p < 0.5 else GOLD[4])
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(mo, x + dx, y + dy, GOLD[3] if p < 0.6 else GOLD[2])
            else:
                put(mo, x, y, bright)
                put(mo, x, y + 1, GOLD[2])   # tiny trail below
        cels.append({"Ring": ring, "Motes": mo})
    return emit("fx_heal", W, H, ["Ring", "Motes"], cels, 80, "heal")


# ---------------------------------------------------------------- dust
def fx_dust():
    W, H = 24, 16
    G = H - 1
    # puffs: (x, base radius, rise speed, growth)
    puffs = [(7.5, 2.4, 0.6, 1.0), (12.0, 3.2, 0.9, 1.2), (16.5, 2.2, 0.5, 0.9), (10.0, 2.0, 1.2, 0.8)]
    dens = [1.0, 1.0, 1.0, 1.0]
    spread = [0.6, 1.0, 1.4, 1.8]
    cels = []
    for k in range(4):
        shade, light = blank(W, H), blank(W, H)
        for (px_, r0, rise, grow) in puffs:
            r = r0 + grow * k * 0.9
            x = 12 + (px_ - 12) * spread[k]
            y = G - r + 1 - rise * k * 1.2
            for yy in range(H):
                for xx in range(W):
                    d = math.hypot(xx + 0.5 - x, yy + 0.5 - y)
                    if d > r or yy > G:
                        continue
                    if dens[k] < 1 and dens[k] < bt(xx, yy):
                        continue
                    # lit from above-left
                    lx = (xx + 0.5 - x) / r
                    ly = (yy + 0.5 - y) / r
                    lit = -0.6 * lx - 0.8 * ly
                    if lit > 0.35 and d < r - 0.5:
                        light.putpixel((xx, yy), DUST[3] if k < 2 else DUST[2])
                    elif lit > -0.2:
                        light.putpixel((xx, yy), DUST[2] if k < 2 else DUST[1])
                    else:
                        shade.putpixel((xx, yy), DUST[1] if k < 3 else DUST[0])
        # ground skid line on first frames
        if k < 2:
            for xx in range(4 - k * 2, 20 + k * 2):
                if (xx + k) % 3:
                    shade.putpixel((xx, G), DUST[0])
        if k == 3:
            breakup(shade, 0.55, 31)
            breakup(light, 0.55, 31)
        cels.append({"Shade": clean(shade, ref=(light,)), "Light": clean(light, ref=(shade,))})
    return emit("fx_dust", W, H, ["Shade", "Light"], cels, 60, "dust")


# ---------------------------------------------------------------- ember
def fx_embers():
    W, H = 8, 8
    # a single ember: 2px hot core + soft 1px glow; drifts/flickers within the cell
    frames = [((3, 4), 1.0), ((3, 3), 0.8), ((4, 3), 1.0), ((4, 4), 0.6)]
    cels = []
    for (x, y), b in frames:
        core, glow = blank(W, H), blank(W, H)
        for (dx, dy) in ((-1, 0), (2, 0), (0, -1), (1, -1), (0, 2), (1, 1), (-1, 1) if b > 0.7 else (0, 1)):
            put(glow, x + dx, y + dy, EMBER[1] if b > 0.7 else EMBER[0])
        put(glow, x + 1, y + 2, EMBER[0])
        put(core, x, y, EMBER[4] if b > 0.9 else EMBER[3])
        put(core, x + 1, y, EMBER[3])
        put(core, x, y + 1, EMBER[2])
        put(core, x + 1, y + 1, EMBER[2] if b > 0.7 else EMBER[1])
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_embers", W, H, ["Glow", "Core"], cels, 120, "ember")


# ================================================================ v2 effects
def molten_fn(dim=0.0, back_dim=None):
    """Premium boss blade light: white-hot cutting edge -> pale gold -> gold -> amber ->
    dark amber falloff (Bayer only at the inner falloff). Cooling toward the trailing end
    (and with dim) pushes the band thresholds toward the edge continuously, so the band
    thins and darkens smoothly with no seams."""
    def f(s, u, x, y):
        cool = (1 - min(1.0, u / 0.45)) ** 1.3 * 0.42 + dim * 0.55
        if back_dim and back_dim(x, y):
            cool += 0.3
        sp = s + cool
        if u > 0.93 and s < 0.3:
            sp = s                                    # the leading tip always burns white
        if sp < 0.12:
            idx = 6
        elif sp < 0.27:
            idx = 5
        elif sp < 0.46:
            idx = 4
        elif sp < 0.65:
            idx = 3
        elif sp < 0.84:
            idx = 2
        elif sp < 1.0:
            idx = 1
            q = (sp - 0.84) / 0.16
            if q > 0.4 and (q - 0.4) / 0.6 > bt(x, y):
                return None
        else:
            return None
        return (0 if idx >= 5 else 1, MOLTEN[idx])
    return f


def molten_halo(q, u, x, y):
    """Outer glow: amber hugging the edge, dark amber dithered to nothing."""
    if u < 0.15:
        return None
    if q < 0.34:
        return GOLD[1] if u > 0.5 else GOLD[0]
    if q < 0.67:
        return GOLD[0] if bt(x, y) < 0.75 else None
    return AMBER_DK if bt(x, y) < 0.4 else None


def boss_arc(name, tag, W, H, cx, cy, rx, ry, keys, halo=4, back_dim=None, ms=45):
    cels = []
    for (tail, head, th, dim) in keys:
        core, glow, hal = crescent(W, H, cx, cy, rx, ry, tail, head, th,
                                   molten_fn(dim, back_dim), halo=halo * (1 - dim),
                                   halo_fn=molten_halo, peak=0.6)
        if dim >= 0.3:
            breakup(hal, 0.6, len(cels) + 3)
        cels.append({"Halo": hal, "Glow": glow, "Core": core})
    return emit(name, W, H, ["Halo", "Glow", "Core"], cels, ms, tag)


# ---- player combo
def fx_slash2():
    """Combo hit 2: rising crescent, low-back -> up-forward (RIGHT). Pivot (8, 20)."""
    W, H = 48, 40
    keys = [(-100, -62, 5, 0), (-104, 24, 9, 0), (-56, 64, 8, 0.15), (18, 72, 3.5, -1)]
    cels = []
    for (tail, head, th, dim) in keys:
        fn = silver_tail_fn if dim < 0 else silver_fn(dim)
        core, glow, _ = crescent(W, H, 8, 20, 36, 18, tail, head, th, fn)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_slash2", W, H, ["Glow", "Core"], cels, 40, "slash2")


def lance(img_core, img_glow, W, H, x_tip, x_tail, cy, hw_max, ramp, dir_=1, tip_len=6, halo=True):
    """Tapered horizontal streak. dir_=1 points RIGHT (tip at x_tip > x_tail), -1 points LEFT.
    ramp: [edge, mid, bright, core] colours."""
    length = abs(x_tip - x_tail)
    if length < 1:
        return
    for i in range(int(length) + 1):
        x = x_tip - dir_ * i
        # sharp at the tip, long taper to the tail
        if i < tip_len:
            hw = hw_max * (i / tip_len) ** 0.8
        else:
            hw = hw_max * (1 - (i - tip_len) / max(1, length - tip_len)) ** 0.7
        for y in range(H):
            dy = abs(y + 0.5 - cy)
            if hw > 0.2 and dy <= hw + 0.35:
                q = dy / max(0.5, hw)
                c = ramp[3] if q < 0.3 else (ramp[2] if q < 0.6 else (ramp[1] if q < 0.85 else ramp[0]))
                (img_core if q < 0.6 else img_glow).putpixel((int(x), y), c) if 0 <= x < W else None
            elif halo and hw > 1.2 and dy <= hw + 1.1:
                if 0 <= x < W:
                    img_glow.putpixel((int(x), y), ramp[0])


def fx_slash3():
    """Combo finisher: thrust streak + wide flat arc to the RIGHT. Hand/pivot at (4, 16)."""
    W, H = 64, 32
    SIL = [SILVER[1], SILVER[2], SILVER[3], WHITE]
    keys = [  # (arc tail, arc head, arc thick, dim, streak tip x, streak tail x, streak hw)
        (70, 40, 4, 0, 30, 6, 1.2),
        (80, -30, 8, 0, 62, 8, 2.4),
        (40, -48, 7, 0.15, 63, 30, 1.8),
        (-10, -52, 4, 0.35, 63, 48, 1.0),
        (-30, -54, 3, -1, 0, 0, 0),
    ]
    cels = []
    for (tail, head, th, dim, tip, tl, hw) in keys:
        fn = silver_tail_fn if dim < 0 else silver_fn(dim)
        core, glow, _ = crescent(W, H, 2, 16, 60, 14, tail, head, th, fn)
        streak = blank(W, H)
        if hw:
            lance(streak, glow, W, H, tip, tl, 16, hw, SIL, dir_=1, tip_len=5, halo=False)
        cels.append({"Glow": clean(glow, ref=(core, streak)), "Core": core, "Streak": clean(streak, ref=(glow,))})
    return emit("fx_slash3", W, H, ["Glow", "Core", "Streak"], cels, 40, "slash3")


# ---- boss arcs (all face LEFT; boss body sits to the right of the pivot)
def fx_arc_down():
    """Diagonal down-cut: top-right -> bottom-left. Pivot (shoulder) at (68, 48)."""
    keys = [(52, 96, 8, 0), (56, 172, 16, 0), (64, 224, 22, 0), (122, 234, 15, 0.15),
            (176, 238, 8, 0.4)]
    return boss_arc("fx_arc_down", "arc_down", 112, 96, 68, 48, 60, 44, keys)


def fx_arc_up():
    """Rising cut: bottom-left -> top-right. Pivot (shoulder) at (60, 50)."""
    keys = [(228, 198, 8, 0), (230, 128, 16, 0), (226, 70, 22, 0), (168, 50, 15, 0.15),
            (112, 44, 8, 0.4)]
    return boss_arc("fx_arc_up", "arc_up", 112, 96, 60, 50, 54, 42, keys)


def fx_arc_wide():
    """Full horizontal sweep through the front (left). Pivot (waist) at (140, 30)."""
    keys = [(70, 116, 9, 0), (74, 168, 16, 0), (80, 204, 20, 0), (122, 212, 15, 0.15),
            (168, 216, 8, 0.4)]
    return boss_arc("fx_arc_wide", "arc_wide", 176, 64, 140, 30, 132, 26, keys)


def fx_spin():
    """360 spin: elliptical ring of blade light round the bottom-centre (104, 46).
    Upper half (behind the boss) is dimmer than the lower/front half."""
    cy = 46
    keys = [(120, 200, 6, 0), (90, 290, 10, 0), (110, 380, 12, 0), (160, 470, 12, 0),
            (260, 540, 9, 0.15), (400, 580, 6, 0.4)]
    return boss_arc("fx_spin", "spin", 208, 72, 104, cy, 96, 20, keys, halo=3,
                    back_dim=lambda x, y: y < cy - 2)


# ---- thrust + spears
GOLD_LANCE = [GOLD[1], GOLD[3], GOLD[4], WHITE]


def speed_lines(img, W, H, cy, x0, x1, n, seed, shift, colours):
    rnd = random.Random(seed)
    for i in range(n):
        y = int(cy + rnd.choice((-1, 1)) * rnd.uniform(4, H / 2 - 2))
        ln = rnd.randint(8, 22)
        xs = rnd.uniform(x0, x1) - shift
        for j in range(ln):
            x = int(xs + j)
            if 0 <= x < W and 0 <= y < H:
                img.putpixel((x, y), colours[0] if j < ln * 0.35 else colours[1])


def fx_thrust():
    """Gold lance streak toward the LEFT. Sword hand / origin at (124, 16)."""
    W, H = 128, 32
    keys = [(90, 124, 2.0, 0, 0), (4, 124, 4.0, 1, 0), (4, 70, 3.0, 2, 1), (6, 34, 1.5, 3, 2)]
    cels = []
    for (tip, tl, hw, k, dim) in keys:
        core, glow, lines = blank(W, H), blank(W, H), blank(W, H)
        ramp = GOLD_LANCE if dim == 0 else ([GOLD[0], GOLD[2], GOLD[3], GOLD[4]] if dim == 1
                                            else [AMBER_DK, GOLD[1], GOLD[2], GOLD[3]])
        lance(core, glow, W, H, tip, tl, 16, hw, ramp, dir_=-1, tip_len=10)
        if k == 1:   # tip flare
            for (dx, dy) in ((-1, 0), (-2, 0), (0, -1), (0, 1), (0, -2), (0, 2)):
                put(core, tip + dx, 16 + dy, WHITE if abs(dx) + abs(dy) < 2 else GOLD[4])
        if k >= 1:
            speed_lines(lines, W, H, 16, 20, 100, 7 - k, 11, k * 10,
                        (GOLD[3], GOLD[1]) if k < 3 else (GOLD[1], GOLD[0]))
        cels.append({"Lines": lines, "Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,))})
    return emit("fx_thrust", W, H, ["Lines", "Glow", "Core"], cels, 45, "thrust")


def fx_light_spear():
    """Projectile pointing LEFT (tip at x=1, y=6). Loops; the trail shimmers."""
    W, H = 40, 12
    cy = 6
    cels = []
    for k in range(4):
        glow, core, trail = blank(W, H), blank(W, H), blank(W, H)
        # spearhead: diamond from tip x=1 to x=12, widest at x=6
        for x in range(1, 13):
            hw = (x - 1) / 5 * 3.0 if x <= 6 else 3.0 * (1 - (x - 6) / 6) + 0.6
            for y in range(H):
                dy = abs(y + 0.5 - cy - 0.5)
                if dy <= hw:
                    q = dy / max(0.5, hw)
                    c = WHITE if q < 0.34 else (GOLD[4] if q < 0.7 else GOLD[3])
                    (core if q < 0.7 else glow).putpixel((x, y), c)
                elif dy <= hw + 1.2 and bt(x, y) < 0.5 + 0.25 * (k % 2):
                    glow.putpixel((x, y), GOLD[1])
        # shaft
        for x in range(12, 30):
            put(core, x, cy, WHITE if x < 22 else GOLD[4])
            put(glow, x, cy - 1, GOLD[3] if x < 24 else GOLD[2])
            put(glow, x, cy + 1, GOLD[2] if x < 24 else GOLD[1])
        # shimmering trail: dashes that march right each frame (4-frame loop)
        for row, off, col in ((cy, 0, GOLD[3]), (cy - 2, 2, GOLD[2]), (cy + 2, 1, GOLD[2]),
                              (cy - 3, 3, GOLD[1]), (cy + 3, 0, GOLD[1])):
            for x in range(28, 40):
                if ((x - k * 2 + off * 3) % 8) < (4 if row == cy else 2) and x + abs(row - cy) * 2 < 40:
                    put(trail, x, row, col)
        # glint on the head, alternating
        if k in (0, 2):
            put(core, 6, cy - 3, WHITE)
            put(core, 6, cy - 4, GOLD[4] if k == 0 else GOLD[3])
        cels.append({"Trail": trail, "Glow": glow, "Core": core})
    return emit("fx_light_spear", W, H, ["Trail", "Glow", "Core"], cels, 60, "light_spear")


def shard(img, cx, cy, ang, r0, r1, w0, colours):
    """Thin radial shard: base width w0 at r0 tapering to a point at r1."""
    a = math.radians(ang)
    ca, sa = math.cos(a), -math.sin(a)
    n = int((r1 - r0) * 2) + 2
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        hw = w0 * (1 - t)
        for j in range(-2, 3):
            off = j * 0.5
            if abs(off) <= hw:
                x, y = cx + ca * r - sa * off, cy + sa * r + ca * off
                c = colours[0] if t < 0.35 else (colours[1] if t < 0.7 else colours[2])
                put(img, x, y, c)


def fx_spear_impact():
    """Radial gold shard burst, centred at (24, 24)."""
    W, H = 48, 48
    cx = cy = 23.5
    rnd = random.Random(8)
    angs = [i * 36 + rnd.uniform(-10, 10) for i in range(10)]
    lens = [rnd.uniform(0.75, 1.0) for _ in angs]
    cels = []
    for k in range(5):
        glow, core, shards = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            disc(glow, cx, cy, 6.5, GOLD[2])
            disc(glow, cx, cy, 5.2, GOLD[3])
            disc(core, cx, cy, 3.8, GOLD[4])
            disc(core, cx, cy, 2.5, WHITE)
        elif k == 1:
            disc(glow, cx, cy, 3.6, GOLD[3])
            disc(core, cx, cy, 2.2, WHITE)
            for a, l in zip(angs, lens):
                shard(shards, cx, cy, a, 4, 4 + 15 * l, 1.2, (WHITE, GOLD[4], GOLD[3]))
        elif k == 2:
            disc(core, cx, cy, 1.2, GOLD[4])
            for a, l in zip(angs, lens):
                shard(shards, cx, cy, a, 8, 8 + 13 * l, 1.0, (GOLD[4], GOLD[3], GOLD[2]))
        elif k == 3:
            for a, l in zip(angs, lens):
                shard(shards, cx, cy, a, 13, 13 + 8 * l, 1.0, (GOLD[3], GOLD[2], GOLD[1]))
        else:
            for a, l in zip(angs, lens):
                shard(shards, cx, cy, a, 17, 17 + 4 * l, 0.8, (GOLD[2], GOLD[1], GOLD[1]))
        cels.append({"Glow": clean(glow, ref=(shards, core)), "Shards": clean(shards, ref=(glow, core)),
                     "Core": clean(core, ref=(glow, shards))})
    return emit("fx_spear_impact", W, H, ["Glow", "Shards", "Core"], cels, 50, "spear_impact")


def flare(img_core, img_glow, cx, cy, L, Ld, w, core_c, ray_c, tip_c, diag_c):
    """4-point star flare with tapered rays (width w at centre) + short diagonals."""
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for i in range(int(L) + 1):
            t = i / max(1, L)
            hw = w * (1 - t) ** 1.3
            for j in range(-2, 3):
                if abs(j) <= hw:
                    x = cx + dx * i + (j if dy else 0)
                    y = cy + dy * i + (j if dx else 0)
                    c = core_c if t < 0.25 else (ray_c if t < 0.7 else tip_c)
                    put(img_core, x, y, c)
    for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        for i in range(1, int(Ld) + 1):
            put(img_glow, cx + dx * i, cy + dy * i, diag_c)


def fx_telegraph():
    """Incoming-attack glint: 4-point flare pops then fades, white -> gold. Centre (16, 16)."""
    W, H = 32, 32
    cx = cy = 16
    spec = [  # (ray, diag, width, halo r, core, ray, tip, diag)
        (4, 0, 1.2, 0, WHITE, GOLD[4], GOLD[3], GOLD[3]),
        (13, 4, 2.2, 5.5, WHITE, WHITE, GOLD[4], GOLD[3]),
        (15, 6, 2.0, 6.5, WHITE, GOLD[4], GOLD[3], GOLD[3]),
        (10, 3, 1.6, 4.5, GOLD[4], GOLD[3], GOLD[2], GOLD[2]),
        (6, 0, 1.2, 0, GOLD[3], GOLD[2], GOLD[1], GOLD[1]),
        (2, 0, 0.8, 0, GOLD[2], GOLD[1], GOLD[1], GOLD[1]),
    ]
    cels = []
    for (L, Ld, w, hr, cc, rc, tc, dc) in spec:
        core, glow = blank(W, H), blank(W, H)
        if hr:
            for yy in range(H):
                for xx in range(W):
                    d = math.hypot(xx - cx, yy - cy)
                    if d <= hr:
                        q = d / hr
                        if q < 0.55:
                            glow.putpixel((xx, yy), GOLD[2])
                        elif bt(xx, yy) > (q - 0.55) / 0.45:
                            glow.putpixel((xx, yy), GOLD[0])
        flare(core, glow, cx, cy, L, Ld, w, cc, rc, tc, dc)
        cels.append({"Glow": glow, "Core": core})
    return emit("fx_telegraph", W, H, ["Glow", "Core"], cels, 40, "telegraph")


# ---- eruption pillar
def fx_pillar():
    """Eruption pillar, 32x128, ground row y=127, centred on x=16.
    0-2 warning glow + cracks, 3-6 eruption (hot core), 7-9 dissipate into sparks."""
    W, H = 32, 128
    G = H - 1
    cx = 15.5
    rnd = random.Random(12)
    sparks = [(rnd.uniform(-9, 9), rnd.uniform(0, 1), rnd.uniform(0.7, 1.3)) for _ in range(14)]
    cracks = [[(16, 127), (12, 126), (9, 127), (5, 126), (2, 127)],
              [(16, 127), (20, 126), (23, 127), (27, 126), (30, 127)],
              [(12, 126), (11, 124)], [(23, 127), (24, 125)]]
    cels = []
    for k in range(10):
        ground, glow, core, sp = blank(W, H), blank(W, H), blank(W, H), blank(W, H)
        # ---- ground warning: cracks + glow pool
        if k <= 7:
            heat = [0.4, 0.7, 1.0, 1.0, 1.0, 0.8, 0.6, 0.35][k]
            reach = [0.45, 0.8, 1.0, 1, 1, 1, 1, 1][k]
            for pts in cracks:
                segs = list(zip(pts, pts[1:]))
                for si, (a, b) in enumerate(segs):
                    if si / max(1, len(segs)) > reach:
                        break
                    line(ground, a[0], a[1], b[0], b[1],
                         GOLD[4] if heat > 0.9 else (GOLD[3] if heat > 0.5 else GOLD[2]))
            pr = 4 + 8 * heat
            for yy in range(G - 6, H):
                for xx in range(W):
                    q = math.hypot((xx + 0.5 - cx) / pr, (yy + 0.5 - G) / 3.2)
                    if q < 1 and not ground.getpixel((xx, yy))[3]:
                        if q < 0.45 * heat:
                            glow.putpixel((xx, yy), GOLD[2])
                        elif q < 0.75 or bt(xx, yy) > (q - 0.75) / 0.25:
                            glow.putpixel((xx, yy), GOLD[0] if q > 0.6 else GOLD[1])
            # warning: a few embers lifting off the pool
            if k <= 2:
                for i, (ox, ph) in enumerate(((-5, 0.0), (-1, 0.5), (3, 0.25), (6, 0.75))):
                    p = (ph + k * 0.33) % 1.0
                    y = G - 3 - p * (6 + 5 * k)
                    put(sp, cx + ox, y, GOLD[4] if k == 2 else GOLD[3])
                    put(sp, cx + ox, y + 1, GOLD[1])
        # ---- column
        if 3 <= k <= 7:
            top = [G - 58, 2, 1, 8, 24][k - 3]
            base_hw = [6.5, 10.5, 11.0, 8.0, 4.0][k - 3]
            for y in range(max(0, top - 2), G + 1):
                hgt = G - y
                span = G - top
                # tongue-shaped top, flared base, rippling edges
                ttop = min(1.0, (y - top) / 22.0) if y >= top else 0
                flare_ = 1 + 0.45 * max(0.0, 1 - hgt / 12.0)
                ripple = (1 + 0.09 * math.sin(y * 0.21 + k * 1.9) + 0.06 * math.sin(y * 0.53 - k * 2.7)
                          + 0.05 * math.sin(y * 1.31 + k * 0.8))
                hw = base_hw * (ttop ** 0.6) * flare_ * ripple
                if k == 7:
                    # detached remnant rising off the ground, tapering at both ends
                    hw = 3.6 * math.sin(math.pi * (y - 24) / 64.0) * ripple if 24 <= y <= 88 else 0
                for x in range(W):
                    dx = abs(x + 0.5 - cx)
                    if hw > 0.3 and dx <= hw:
                        q = dx / hw
                        if k <= 5:
                            idx = 6 if q < 0.28 else (5 if q < 0.48 else (4 if q < 0.68 else (3 if q < 0.86 else 2)))
                        else:
                            idx = 5 if q < 0.3 else (4 if q < 0.6 else (3 if q < 0.85 else 2))
                            idx -= (k - 6)
                        # rising internal streaks
                        if 0.3 < q < 0.7 and ((y + k * 7 + int(x) * 5) % 11) < 3:
                            idx = min(6, idx + 1)
                        if idx > 0:
                            (core if idx >= 5 else glow).putpixel((x, y), MOLTEN[idx])
                    elif hw > 1.5 and dx <= hw + 2.2 and k <= 6:
                        q = (dx - hw) / 2.2
                        if bt(x, y) > q:
                            glow.putpixel((x, y), GOLD[1] if q < 0.45 else AMBER_DK)
        # ---- sparks (rise during eruption and after)
        if k >= 4:
            for i, (ox, ph, spd) in enumerate(sparks):
                p = ph * 0.5 + (k - 4) * 0.14 * spd
                y = G - 10 - p * 150
                x = cx + ox * (0.6 + p) + math.sin(p * 9 + i) * 1.5
                if y < 1 or (k <= 6 and abs(ox * (0.6 + p)) < 9):
                    continue
                bright = GOLD[4] if k < 8 else (GOLD[3] if k < 9 else GOLD[2])
                put(sp, x, y, bright)
                put(sp, x, y + 1, GOLD[2] if k < 9 else GOLD[1])
                if i % 3 == 0 and k < 9:
                    put(sp, x, y + 2, GOLD[1])
        if k == 9:
            for pts in cracks[:2]:
                for (a, b) in zip(pts, pts[1:]):
                    line(ground, a[0], a[1], b[0], b[1], GOLD[1])
            breakup(ground, 0.6, 99)
        cels.append({"Ground": ground, "Glow": clean(glow, ref=(core, ground)), "Core": clean(core, ref=(glow,)),
                     "Sparks": sp})
    return emit("fx_pillar", W, H, ["Ground", "Glow", "Core", "Sparks"], cels, 60, "pillar")


def fx_ground_crack():
    """Glowing floor fissure spreading from centre (32, 15), bottom row = ground."""
    W, H = 64, 16
    G = H - 1
    left = [(32, 14), (28, 13), (25, 14), (21, 13), (17, 14), (13, 13), (9, 14), (5, 13), (1, 14)]
    right = [(32, 14), (36, 13), (39, 14), (43, 13), (47, 14), (51, 13), (55, 14), (59, 13), (62, 14)]
    branches = [[(21, 13), (19, 11)], [(43, 13), (45, 11)], [(13, 13), (11, 15)], [(51, 13), (53, 15)],
                [(28, 13), (27, 15)], [(39, 14), (40, 12)]]
    reach = [0.3, 0.6, 0.9, 1.0, 1.0, 1.0]
    heat = [2, 2, 2, 2, 1, 0]
    cels = []
    for k in range(6):
        rim, glow, core = blank(W, H), blank(W, H), blank(W, H)
        paths = []
        for path in (left, right):
            n = max(1, int(round((len(path) - 1) * reach[k])))
            paths.append(path[:n + 1])
        for br in branches:
            if abs(br[0][0] - 32) <= 30 * reach[k] - 4:
                paths.append(br)
        for pts in paths:
            for (a, b) in zip(pts, pts[1:]):
                n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
                for i in range(n + 1):
                    x = round(a[0] + (b[0] - a[0]) * i / n)
                    y = round(a[1] + (b[1] - a[1]) * i / n)
                    far = abs(x - 32) / 30.0
                    hot = heat[k] - (1 if far > 0.7 else 0)
                    c = [GOLD[1], GOLD[3], WHITE][max(0, hot)] if far < 0.25 and hot >= 2 else \
                        [GOLD[1], GOLD[2], GOLD[4]][max(0, hot)]
                    put(core, x, y, c)
                    put(rim, x, y + 1, ROCK[0])
                    put(rim, x + 1, y + 1, ROCK[0])
                    # light spilling upward from the fissure
                    if heat[k] >= 1:
                        for j in range(1, 4 if heat[k] == 2 else 2):
                            if bt(x, y - j) < (0.8 - j * 0.22) * (1 - far * 0.5):
                                put(glow, x, y - j, GOLD[1] if j == 1 else GOLD[0])
        if k == 5:
            breakup(core, 0.6, 5)
            breakup(rim, 0.6, 5)
        cels.append({"Rim": rim, "Glow": glow, "Core": core})
    return emit("fx_ground_crack", W, H, ["Rim", "Glow", "Core"], cels, 80, "ground_crack")


def fx_roar_ring():
    """Phase-2 roar: expanding shock ring from the centre (128, 64); gold edge, faint interior."""
    W, H = 256, 128
    cx, cy = 128, 64
    rxs = [16, 40, 66, 90, 110, 124]
    thick = [4, 5, 5, 4, 3, 2]
    cels = []
    for k in range(6):
        inner, ring, streaks = blank(W, H), blank(W, H), blank(W, H)
        rx = rxs[k]
        ry = rx * 0.5
        dim = 0 if k < 3 else (1 if k < 5 else 2)
        for y in range(H):
            for x in range(W):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx / rx, dy / ry)
                grad = math.hypot(dx / rx ** 2, dy / ry ** 2) / max(r, 1e-6)
                dpx = (1 - r) / max(grad, 1e-6)          # px inside the edge (neg = outside)
                if -0.5 <= dpx <= thick[k]:
                    q = (dpx + 0.5) / (thick[k] + 0.5)
                    idx = 6 if q < 0.25 else (5 if q < 0.5 else (4 if q < 0.75 else 3))
                    # lower half (front) slightly brighter than the upper half
                    if dy < 0:
                        idx -= 1
                    idx -= dim * 2
                    if idx > 0:
                        ring.putpixel((x, y), MOLTEN[idx])
                elif thick[k] < dpx <= thick[k] + 10 and k < 5:
                    q = (dpx - thick[k]) / 10
                    if bt(x, y) > 0.35 + q * 0.65:
                        inner.putpixel((x, y), GOLD[0] if q < 0.4 and dim == 0 else AMBER_DK)
        # radial speed streaks just outside the ring
        if 1 <= k <= 3:
            for i in range(16):
                a = math.radians(i * 22.5 + 11)
                for j in range(3, 3 + 5 + k):
                    x = cx + math.cos(a) * (rx + j)
                    y = cy - math.sin(a) * (ry + j * 0.5)
                    put(streaks, x, y, GOLD[3] if j < 6 else GOLD[2])
        if k == 5:
            breakup(ring, 0.65, 7)
        cels.append({"Inner": inner, "Ring": clean(ring), "Streaks": streaks})
    return emit("fx_roar_ring", W, H, ["Inner", "Ring", "Streaks"], cels, 60, "roar_ring")


def fx_cast_charge():
    """Gathering orb at (24, 24) with motes converging inward. Seamless 6-frame loop."""
    W, H = 48, 48
    cx = cy = 23.5
    rnd = random.Random(4)
    parts = [(i * 36 + rnd.uniform(-8, 8), i / 10.0 + rnd.uniform(0, 0.05)) for i in range(10)]
    cels = []
    for k in range(6):
        glow, orb, pts = blank(W, H), blank(W, H), blank(W, H)
        r = 5.5 + 0.9 * math.sin(2 * math.pi * k / 6)
        for yy in range(H):
            for xx in range(W):
                d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                if d <= r * 0.45:
                    orb.putpixel((xx, yy), WHITE)
                elif d <= r * 0.75:
                    orb.putpixel((xx, yy), GOLD[4])
                elif d <= r:
                    orb.putpixel((xx, yy), GOLD[3])
                elif d <= r + 1.5:
                    glow.putpixel((xx, yy), GOLD[2])
                elif d <= r + 5:
                    q = (d - r - 1.5) / 3.5
                    if bt(xx, yy) > q:
                        glow.putpixel((xx, yy), GOLD[1] if q < 0.45 else GOLD[0])
        # rotating dashed ring (4-fold symmetric, 15 deg/frame -> loops in 6)
        for i in range(4):
            base = i * 90 + k * 15
            for a_ in range(0, 40, 4):
                a = math.radians(base + a_)
                put(glow, cx + math.cos(a) * (r + 8), cy - math.sin(a) * (r + 8),
                    GOLD[3] if a_ > 20 else GOLD[2])
        # converging motes: streak points outward (trail), head toward the orb
        for (ang, ph) in parts:
            p = (ph + k / 6.0) % 1.0
            rho = r + 3 + (1 - p) * 17
            a = math.radians(ang + p * 70)
            x, y = cx + math.cos(a) * rho, cy - math.sin(a) * rho
            c = GOLD[4] if p > 0.6 else GOLD[3]
            put(pts, x, y, WHITE if p > 0.8 else c)
            for j in (1, 2):
                put(pts, x + math.cos(a) * j, y - math.sin(a) * j, GOLD[2] if j == 1 else GOLD[1])
        cels.append({"Glow": glow, "Orb": orb, "Particles": pts})
    return emit("fx_cast_charge", W, H, ["Glow", "Orb", "Particles"], cels, 70, "cast_charge")


def fx_parry_spark():
    """Big white-gold clash spark, centred at (16, 16)."""
    W, H = 32, 32
    cx = cy = 16
    rnd = random.Random(9)
    fly = [(rnd.uniform(0, 360), rnd.uniform(0.8, 1.2)) for _ in range(12)]
    cels = []
    for k in range(4):
        glow, core, sp = blank(W, H), blank(W, H), blank(W, H)
        if k == 0:
            disc(glow, cx, cy, 7.5, GOLD[3])
            disc(glow, cx, cy, 6, GOLD[4])
            disc(core, cx, cy, 4.5, WHITE)
            flare(core, glow, cx, cy, 13, 7, 2.6, WHITE, WHITE, GOLD[4], GOLD[4])
        elif k == 1:
            disc(glow, cx, cy, 4.5, GOLD[3])
            disc(core, cx, cy, 3, WHITE)
            flare(core, glow, cx, cy, 15, 9, 2.2, WHITE, GOLD[4], GOLD[3], GOLD[3])
        elif k == 2:
            disc(core, cx, cy, 1.5, GOLD[4])
            flare(core, glow, cx, cy, 9, 4, 1.4, GOLD[4], GOLD[3], GOLD[2], GOLD[2])
        else:
            for yy in range(H):
                for xx in range(W):
                    d = math.hypot(xx - cx, yy - cy)
                    if 9.4 <= d <= 10.4:
                        glow.putpixel((xx, yy), GOLD[2])
            breakup(glow, 0.55, 3)
        if k >= 1:
            for (a_, spd) in fly:
                a = math.radians(a_)
                rr = (5 + 4 * k) * spd
                x, y = cx + math.cos(a) * rr, cy - math.sin(a) * rr
                c1, c2 = [(WHITE, GOLD[4]), (GOLD[4], GOLD[3]), (GOLD[3], GOLD[1])][k - 1]
                put(sp, x, y, c1)
                put(sp, x - math.cos(a), y + math.sin(a), c2)
        cels.append({"Glow": clean(glow, ref=(core,)), "Core": clean(core, ref=(glow,)), "Sparks": sp})
    return emit("fx_parry_spark", W, H, ["Glow", "Core", "Sparks"], cels, 40, "parry_spark")


# ---------------------------------------------------------------- previews
BG = (0x1c, 0x1a, 0x2c, 255)


def comp_frame(fr, layers):
    w, h = fr["cels"][layers[0]].size
    c = blank(w, h)
    for ln in layers:
        c.alpha_composite(fr["cels"][ln])
    return c


def strip_img(frames, layers, S, bg=BG):
    w, h = frames[0]["cels"][layers[0]].size
    strip = Image.new("RGBA", ((w + 2) * len(frames) * S, (h + 2) * S), bg)
    for i, fr in enumerate(frames):
        cell = Image.new("RGBA", (w, h), bg)
        cell.alpha_composite(comp_frame(fr, layers))
        strip.paste(cell.resize((w * S, h * S), Image.NEAREST), (((w + 2) * i + 1) * S, S))
        for x in range(((w + 2) * i + 1) * S - 1, ((w + 2) * i + 1 + w) * S + 1):
            for yy in (S - 1, (h + 1) * S):
                strip.putpixel((x, yy), (0x30, 0x2c, 0x44, 255))
    return strip


def boss_silhouette():
    """~100px tall stand-in for the v2 boss (faces LEFT). Returns (img, pivots)."""
    W_, H_ = 70, 104
    img = blank(W_, H_)
    body, edge = C("0c0a12"), C("2e2640")
    def fill(pred):
        for y in range(H_):
            for x in range(W_):
                if pred(x, y):
                    img.putpixel((x, y), body)
    fill(lambda x, y: (x - 36) ** 2 / 64 + (y - 14) ** 2 / 81 <= 1)                 # head
    fill(lambda x, y: 20 <= y <= 60 and abs(x - 38) <= 16 + (y - 20) * 0.1)           # torso
    fill(lambda x, y: 56 <= y <= 103 and (abs(x - 30) <= 6 or abs(x - 46) <= 6))      # legs
    fill(lambda x, y: 26 <= y <= 96 and 44 <= x <= 62 - (96 - y) * 0.05)              # cape
    fill(lambda x, y: 24 <= y <= 50 and abs(x - 20) <= 4)                             # sword arm
    for i in range(12):                                                               # horns
        img.putpixel((28 - i // 2, 8 - i // 2), body)
        img.putpixel((44 + i // 2, 8 - i // 2), body)
    px = img.load()
    out = img.copy()
    for y in range(H_):
        for x in range(W_):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < W_ and 0 <= yy < H_) or px[xx, yy][3] == 0:
                    out.putpixel((x, y), edge)
                    break
    return out, {"shoulder": (26, 28), "waist": (36, 58), "hand": (18, 46), "feet": (38, 103)}


# effect -> (boss pivot key, pivot point inside the effect frame, frames to show)
SCALE_COMPS = {
    "fx_arc_down": ("shoulder", (68, 48), (1, 2, 3)),
    "fx_arc_up": ("shoulder", (60, 50), (1, 2, 3)),
    "fx_arc_wide": ("waist", (140, 30), (1, 2, 3)),
    "fx_spin": ("waist", (104, 46), (1, 2, 3)),
    "fx_thrust": ("hand", (124, 16), (1, 2)),
    "fx_pillar": (None, None, (1, 4, 6, 8)),
    "fx_roar_ring": ("waist", (128, 64), (1, 3)),
}


def preview(all_fx):
    pdir = os.path.join(HERE, "previews")
    os.makedirs(pdir, exist_ok=True)
    sil, piv = boss_silhouette()
    for name, frames, layers in all_fx:
        w, h = frames[0]["cels"][layers[0]].size
        S = 6 if max(w, h) <= 64 else (4 if max(w, h) <= 128 else 3)
        strip_img(frames, layers, S).save(os.path.join(pdir, f"{name}_{S}x.png"))
        for old in (2, 3, 4, 5, 6):
            if old != S and os.path.exists(os.path.join(pdir, f"{name}_{old}x.png")):
                os.remove(os.path.join(pdir, f"{name}_{old}x.png"))
        if name in SCALE_COMPS:
            key, fp, show = SCALE_COMPS[name]
            cells = []
            for fi in show:
                fx = comp_frame(frames[fi], layers)
                cw, ch = max(w, 60) + 80, max(h, 104) + 20
                cell = Image.new("RGBA", (cw, ch), BG)
                gy = ch - 6                                    # ground line
                for x in range(cw):
                    cell.putpixel((x, gy), C("3a3052"))
                if key:
                    sx = cw // 2 - 10
                    sy = gy - 103
                    cell.alpha_composite(sil, (sx, sy))
                    px_, py_ = piv[key]
                    # align the effect's pivot with the silhouette's pivot (clip what falls off)
                    ox, oy = sx + px_ - fp[0], sy + py_ - fp[1]
                    layer = Image.new("RGBA", (cw + 2 * w, ch + 2 * h), (0, 0, 0, 0))
                    layer.alpha_composite(fx, (ox + w, oy + h))
                    cell.alpha_composite(layer.crop((w, h, w + cw, h + ch)))
                else:
                    # grounded effect: bottom row on the ground line, beside the silhouette
                    sx = 6
                    cell.alpha_composite(sil, (sx, gy - 103))
                    cell.alpha_composite(fx, (sx + 76, gy - h + 1))
                cells.append(cell)
            S2 = 3
            sheet = Image.new("RGBA", (sum(c.width for c in cells) * S2, cells[0].height * S2), BG)
            x = 0
            for c in cells:
                sheet.paste(c.resize((c.width * S2, c.height * S2), Image.NEAREST), (x, 0))
                x += c.width * S2
            sheet.save(os.path.join(pdir, f"{name}_scale_3x.png"))


ALL = [fx_slash, fx_heavy, fx_boss_slash, fx_shockwave, fx_hit, fx_blood, fx_heal, fx_dust,
       fx_embers, fx_slash2, fx_slash3, fx_arc_down, fx_arc_up, fx_arc_wide, fx_spin, fx_thrust,
       fx_light_spear, fx_spear_impact, fx_telegraph, fx_pillar, fx_ground_crack, fx_roar_ring,
       fx_cast_charge, fx_parry_spark]

if __name__ == "__main__":
    only = set(sys.argv[1:])
    out = []
    for fn in ALL:
        if only and fn.__name__ not in only:
            continue
        frames = fn()
        out.append((fn.__name__, frames, list(frames[0]["cels"].keys())))
        print("built", fn.__name__)
    preview(out)
