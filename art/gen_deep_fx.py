#!/usr/bin/env python3
"""FX for the Burning Deep (agent D).  python3 art/gen_deep_fx.py [--preview]

fx_dp_slag    12x12  4 loop   molten slag glob (imp throw), travelling right
fx_dp_splash  32x16  6        lava splash (pivot bottom)
fx_dp_flame   64x24  4 loop   flame jet travelling right from x=0 (pivot left-centre)
fx_dp_burst   48x48  6        magma burst (centred)
fx_dp_wave    32x24  4 loop   magma shockwave rolling along the floor, travelling right (pivot bottom)
fx_dp_pour    32x96  4 loop   pouring stream of molten metal (pivot top-centre)
fx_dp_breath  160x48 4 loop   forge-breath cone travelling right from x=0 (pivot left-centre)
fx_dp_drip    8x16   2 loop   falling slag drop (centred)
fx_dp_marker  32x8   4 loop   floor telegraph: a glowing crack where slag will land (pivot bottom)
fx_dp_debris  16x16  4 loop   an armour plate shard tumbling (centred)
fx_dp_pillar  32x96  8        magma geyser column: crack -> eruption -> collapse (pivot bottom)
Preview: art/previews/fx_deep.png
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import C, h01, scale  # noqa: E402

BUILD = "--preview" not in sys.argv
MG = [C(h) for h in ("3a0906", "661107", "9c1f09", "cf3b0c", "f26414", "ff9a2e", "ffcf66", "fff3cc")]
IR = [C(h) for h in ("0b0809", "161112", "221a19", "342824", "4f3d32", "7a634c", "a08466")]
K = C("060304")


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def heat(v):
    v = max(0.0, min(1.0, v))
    return MG[min(7, int(v * 7.99))]


def field(w, h, fn):
    img = blank(w, h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            v = fn(x + .5, y + .5)
            if v is not None and v > 0.12:
                px[x, y] = heat(v)
    return img


def slag(f):
    def fn(x, y):
        d = math.hypot((x - 7) / 3.6, (y - 6) / 3.0)
        tail = math.hypot((x - 3.5 + f * 0.3) / 3.2, (y - 6.5) / 1.4)
        v = max(1.05 - d, 0.7 - tail * 0.8)
        if d < 0.35:
            return 1.0
        return v + 0.12 * (h01(int(x), int(y), f) - 0.5)
    return field(12, 12, fn)


def splash(f):
    t = f / 5
    def fn(x, y):
        best = None
        for k in range(9):
            a = math.pi * (0.1 + 0.8 * k / 8)
            r = 2 + 12 * t * (0.6 + 0.4 * h01(k, 1, 5))
            cx, cy = 16 + math.cos(a) * r * 1.2, 16 - math.sin(a) * r * 1.1 + 18 * t * t
            d = math.hypot(x - cx, y - cy)
            if d < 1.8 - t:
                best = max(best or 0, 1 - t * 0.7 - d * 0.2)
        base = 1 - abs(x - 16) / (8 + 8 * t) if y > 14 else 0
        return max(best or 0, base * (1 - t) if base > 0 else 0) or None
    return field(32, 16, fn)


def flame(f, w=64, h=24, spread=0.22):
    def fn(x, y):
        t = x / w
        c = h / 2 + 1.8 * math.sin(x * 0.25 - f * 1.6) * t
        hw = 1.5 + x * spread + 3 * max(0, t - 0.6)
        d = abs(y - c) / hw
        if d > 1:
            return None
        n = h01(int(x / 3 + f * 5), int(y / 2), 3)
        v = (1.15 - t * 0.75) * (1 - d ** 1.6) + 0.25 * (n - 0.5)
        if t > 0.8 and n < 0.4:
            return None
        return v
    return field(w, h, fn)


def burst(f):
    t = f / 5
    def fn(x, y):
        d = math.hypot(x - 24, y - 24)
        r = 4 + 18 * t
        ring = 1 - abs(d - r) / (3 + 4 * (1 - t))
        core = (1 - d / (10 * (1 - t) + 1)) if t < 0.6 else -1
        n = h01(int(x / 2), int(y / 2), f)
        v = max(ring * (1 - t * 0.6), core) + 0.2 * (n - 0.5)
        return v if v > 0.15 else None
    return field(48, 48, fn)


def wave(f):
    def fn(x, y):
        yy = 24 - y
        h = 14 * math.exp(-((x - 20 + f) / 7.0) ** 2) + 5 * math.exp(-((x - 8 + f * 0.5) / 5.0) ** 2)
        if yy > h + 1.5 * math.sin(x + f):
            return None
        v = 0.45 + 0.55 * (yy / (h + 1)) ** 0.6 if yy < h else 0.3
        return v + 0.15 * (h01(int(x), int(y) + f, 7) - 0.5)
    return field(32, 24, fn)


def pour(f):
    def fn(x, y):
        w = 5 + y * 0.06 + math.sin(y * 0.2 - f * 1.5) * 1.2
        d = abs(x - 16 - math.sin(y * 0.09 + f) * 1.2) / w
        if d > 1:
            return None
        return 1.05 - d * 0.7 - (0.2 if h01(int(x), int((y + f * 6) // 3), 9) < 0.2 else 0)
    return field(32, 96, fn)


def breath(f):
    return flame(f, 160, 48, 0.14)


def drip(f):
    img = blank(8, 16)
    px = img.load()
    for y in range(3 + f, 13):
        px[4, y] = MG[5] if y < 11 else MG[6]
        if y > 9:
            px[3, y] = MG[4]; px[5, y] = MG[4]
    px[4, 13] = MG[7]; px[4, 1 + f] = MG[3]
    return img


def marker(f):
    img = blank(32, 8)
    px = img.load()
    a = 0.5 + 0.5 * math.sin(f * math.pi / 2)
    for x in range(32):
        d = abs(x - 16) / 15
        if d > 1:
            continue
        for y in range(5, 8):
            v = (1 - d) * (0.55 + 0.35 * a) - (7 - y) * 0.12
            if (x + y + f) % 3 == 0 and v < 0.5:
                continue
            if v > 0.12:
                px[x, y] = heat(v)
    for (x, y) in ((10, 6), (14, 5), (19, 6), (22, 5)):
        px[x, y] = K
    return img


def debris(f):
    img = blank(16, 16)
    px = img.load()
    a = f * math.pi / 2
    pts = [(-5, -3), (5, -4), (6, 2), (-3, 5)]
    rp = [(8 + math.cos(a) * x - math.sin(a) * y, 8 + math.sin(a) * x + math.cos(a) * y) for x, y in pts]
    m = blank(16, 16)
    ImageDraw.Draw(m).polygon(rp, fill=(255, 255, 255, 255))
    mp = m.load()
    for y in range(16):
        for x in range(16):
            if mp[x, y][3]:
                edge = any(not (0 <= x + dx < 16 and 0 <= y + dy < 16 and mp[x + dx, y + dy][3]) for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)))
                px[x, y] = K if edge else (IR[4] if (x + y) % 5 == 0 else IR[2] if y > 8 else IR[3])
    px[8, 8] = MG[4]
    return img


def pillar(f):
    stages = [0.0, 0.15, 0.55, 1.0, 1.0, 0.8, 0.45, 0.15]
    s = stages[f]
    def fn(x, y):
        yy = 96 - y
        if f <= 1:
            if yy < 4 and abs(x - 16) < 6 + f * 4:
                return 0.5 + 0.3 * f if (x + y) % 2 else 0.3
            return None
        hgt = 90 * s
        if yy > hgt:
            return None
        w = 6 + 3 * math.sin(yy * 0.2 + f) + (4 if yy < 8 else 0)
        d = abs(x - 16) / w
        if d > 1:
            return None
        return 1.05 - d * 0.6 - (yy / 96) * 0.25 + 0.15 * (h01(int(x), int(y / 3) + f, 3) - 0.5)
    return field(32, 96, fn)


FX = [("fx_dp_slag", 12, 12, 4, slag, 70), ("fx_dp_splash", 32, 16, 6, splash, 60), ("fx_dp_flame", 64, 24, 4, flame, 70),
      ("fx_dp_burst", 48, 48, 6, burst, 60), ("fx_dp_wave", 32, 24, 4, wave, 70), ("fx_dp_pour", 32, 96, 4, pour, 80),
      ("fx_dp_breath", 160, 48, 4, breath, 70), ("fx_dp_drip", 8, 16, 2, drip, 90), ("fx_dp_marker", 32, 8, 4, marker, 90),
      ("fx_dp_debris", 16, 16, 4, debris, 60), ("fx_dp_pillar", 32, 96, 8, pillar, 80)]


def outline(img):
    w, h = img.size
    src = img.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and src[X, Y][3] and src[X, Y] in (MG[5], MG[6], MG[7]):
                    op[x, y] = MG[1]
                    break
    return out


def main():
    rows = []
    for name, w, h, n, fn, ms in FX:
        ims = [fn(f) for f in range(n)]
        if name not in ("fx_dp_debris", "fx_dp_drip", "fx_dp_marker"):
            ims = [outline(im) for im in ims]
        rows.append((name, w, h, ims))
        if BUILD:
            tag = name[3:]
            asebuild.build(name, w, h, ["FX"], [{"ms": ms, "cels": {"FX": im}} for im in ims], [(tag, 0, n - 1)])
    k = 3
    W_ = max(len(r[3]) * (r[1] + 4) for r in rows) * k + 160
    H_ = sum((r[2] + 6) * k for r in rows) + 10
    sheet = Image.new("RGBA", (W_, H_), (60, 60, 66, 255))
    d = ImageDraw.Draw(sheet)
    y = 5
    for name, w, h, ims in rows:
        d.text((4, y), name, fill=(230, 230, 230, 255))
        x = 160
        for im in ims:
            bg = Image.new("RGBA", im.size, (30, 26, 28, 255)); bg.alpha_composite(im)
            sheet.alpha_composite(scale(bg, k), (x, y))
            x += (w + 4) * k
        y += (h + 6) * k
    sheet.save(os.path.join(HERE, "previews", "fx_deep.png"))
    print("fx built", len(rows))


if __name__ == "__main__":
    main()
