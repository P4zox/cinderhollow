#!/usr/bin/env python3
"""FX for the Starfall Crater (agent SF).  python3 art/gen_starfall_fx.py [--no-ase]

fx_sf_moonstep 32x16  6   starlit ring under the feet (pivot bottom)          -- the Moonstep jump
fx_sf_shard     8x8   4   spinning glass shard (golem shatter)                 (center)
fx_sf_star     16x40  4   a falling star, head at the bottom, trail up         (drawn by the engine, bottom pivot)
fx_sf_burst    48x48  7   star impact burst                                    (pivot bottom)
fx_sf_well     64x64  8   gravity well: a slow spiral of starlight (loop)      (center)
fx_sf_arrow    32x8   2   star arrow travelling right                          (center, rotated by the engine)
fx_sf_pillar   24x120 8   crown pillar: thin line -> pillar of light -> fade   (pivot bottom)
fx_sf_wave     24x16  4   starlight ground wave travelling right               (pivot bottom)
fx_sf_planet   16x16  4   the Orrery's planets, one per frame (tag planet)     (center)
fx_sf_eye      32x32  6   the Orrery's eye beam charge flare                   (center)
Preview: art/previews/fx_starfall.png
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import C, blank, scale, h01, outline, K  # noqa: E402

S0, S1, S2, S3, S4 = C("1c2c66"), C("3e5cc0"), C("7c9cf0"), C("c4d6ff"), C("ffffff")
V1, V2 = C("4c2a8c"), C("a67ee0")
GLASS = [C("142050"), C("2e4a9c"), C("7a9ae6"), C("eef4ff")]
BRASS = [C("3a2614"), C("8a6024"), C("d8aa4c"), C("f4d27e")]


def put(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((x, y), c)


def disc(img, cx, cy, r, c):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                put(img, x, y, c)


def ring(img, cx, cy, r, c, w=1.0, ry=None, step=1):
    ry = ry or r
    n = int(2 * math.pi * max(r, ry) * 1.5) + 8
    for i in range(0, n, step):
        a = i / n * 2 * math.pi
        for k in range(int(w)):
            put(img, cx + math.cos(a) * (r - k), cy + math.sin(a) * (ry - k * ry / max(r, 1)), c)


def moonstep():
    out = []
    for f in range(6):
        img = blank(32, 16)
        r = 3 + f * 2.6
        ring(img, 16, 12, r, S3 if f < 3 else S2, 1, ry=r * 0.32)
        if f < 4:
            ring(img, 16, 12, r * 0.6, S4 if f < 2 else S3, 1, ry=r * 0.2)
        for k in range(6):
            a = k / 6 * 2 * math.pi + f * 0.3
            put(img, 16 + math.cos(a) * (r + 1), 12 + math.sin(a) * r * 0.32 - f, S4 if k % 2 else S2)
        if f < 2:
            for dy in range(3):
                put(img, 16, 12 - dy, S4)
        out.append((50 if f < 3 else 70, img))
    return [("sf_moonstep", out)], (32, 16)


def shard():
    out = []
    for f in range(4):
        img = blank(8, 8)
        a = f * math.pi / 4
        for t in range(-3, 4):
            w = 1 if abs(t) < 3 else 0
            for v in range(-w, w + 1):
                put(img, 4 + math.cos(a) * t - math.sin(a) * v, 4 + math.sin(a) * t + math.cos(a) * v, GLASS[2] if v <= 0 else GLASS[1])
        put(img, 4 + math.cos(a) * 3, 4 + math.sin(a) * 3, GLASS[3])
        out.append((60, outline(img)))
    return [("sf_shard", out)], (8, 8)


def star():
    out = []
    for f in range(4):
        img = blank(16, 40)
        for y in range(0, 34):
            t = y / 33
            w = 0.4 + 2.6 * t ** 2
            for x in range(16):
                dx = abs(x + 0.5 - 8 - math.sin(y * 0.5 + f) * 0.4 * (1 - t))
                if dx <= w and h01(x, y, f) < 0.3 + 0.7 * t:
                    put(img, x, y, S4 if dx < w * 0.35 and t > 0.6 else S3 if dx < w * 0.7 else S1 if t < 0.5 else S2)
        disc(img, 8, 34, 4.2, S2)
        disc(img, 8, 34, 3.0, S3)
        disc(img, 8, 34, 1.8, S4)
        for dx, dy in ((5, 0), (-5, 0), (0, 5)):
            put(img, 8 + dx, 34 + dy, S3)
        out.append((60, img))
    return [("sf_star", out)], (16, 40)


def burst():
    out = []
    for f in range(7):
        img = blank(48, 48)
        r = 3 + f * 3.4
        if f < 6:
            ring(img, 24, 40, r, S3 if f < 3 else S2, 2 if f < 3 else 1, ry=r * 0.55)
        if f < 3:
            disc(img, 24, 40, 6 - f * 1.5, S4)
        for k in range(10):                               # rays
            a = -math.pi * (k + 0.5) / 10
            L = (8 + f * 4) * (0.6 + 0.4 * h01(k, 1, 5))
            if f < 5:
                for i in range(int(L * 0.4), int(L)):
                    put(img, 24 + math.cos(a) * i, 40 + math.sin(a) * i * 0.9, S3 if i < L * 0.7 else S2)
        for k in range(8 if f > 1 else 0):                # falling motes
            put(img, 24 + (h01(k, f, 9) - 0.5) * 40, 40 - h01(k, 3, 9) * 30 + f * 2, S3 if k % 2 else S2)
        out.append((50 if f < 3 else 70, img))
    return [("sf_burst", out)], (48, 48)


def well():
    out = []
    for f in range(8):
        img = blank(64, 64)
        for arm in range(4):
            for i in range(90):
                t = i / 89
                a = arm * math.pi / 2 + t * 4.2 + f * (math.pi / 16)
                r = 30 * (1 - t) + 2
                c = S1 if t < 0.35 else S2 if t < 0.7 else S3
                if i % 2 == 0:
                    put(img, 32 + math.cos(a) * r, 32 + math.sin(a) * r * 0.9, c)
        ring(img, 32, 32, 5, V2, 1)
        disc(img, 32, 32, 3.2, C("05040c"))
        ring(img, 32, 32, 3.6, S4, 1)
        for k in range(5):
            a = f * 0.6 + k * 1.3
            put(img, 32 + math.cos(a) * (12 + k * 3), 32 + math.sin(a) * (12 + k * 3) * 0.9, V2)
        out.append((80, img))
    return [("sf_well", out)], (64, 64)


def arrow():
    out = []
    for f in range(2):
        img = blank(32, 8)
        for x in range(0, 30):
            t = x / 29
            if h01(x, f, 3) < 0.4 + 0.6 * t:
                put(img, x, 4, S3 if t > 0.5 else S1)
            if t > 0.6:
                put(img, x, 3, S2); put(img, x, 5, S2)
        for dx, dy, c in ((29, 4, S4), (30, 4, S4), (28, 3, S3), (28, 5, S3), (27, 2, S2), (27, 6, S2)):
            put(img, dx, dy, c)
        out.append((60, img))
    return [("sf_arrow", out)], (32, 8)


def pillar():
    out = []
    for f in range(8):
        img = blank(24, 120)
        if f < 2:                                         # the thin warning line
            for y in range(0, 120, 2 if f == 0 else 1):
                put(img, 12, y, S2 if f == 0 else S3)
            disc(img, 12, 118, 2 + f, S3)
        elif f < 6:
            w = [5, 9, 8, 6][f - 2]
            for y in range(120):
                for x in range(24):
                    dx = abs(x + 0.5 - 12)
                    if dx <= w:
                        put(img, x, y, S4 if dx < w * 0.35 else S3 if dx < w * 0.7 else S2)
            for k in range(6):
                put(img, 12 + (h01(k, f, 2) - 0.5) * 20, h01(k, f, 3) * 110, S4)
        else:
            w = 3 - (f - 6) * 1.5
            for y in range(0, 120, 2):
                for x in range(24):
                    if abs(x + 0.5 - 12) <= w:
                        put(img, x, y, S2)
        out.append(([110, 110, 40, 50, 60, 70, 70, 70][f], img))
    return [("sf_pillar", out)], (24, 120)


def wave():
    out = []
    for f in range(4):
        img = blank(24, 16)
        for x in range(24):
            t = x / 23
            hgt = int(3 + 9 * math.sin(t * math.pi) ** 1.5 * (0.8 + 0.2 * math.sin(f + x * 0.8)))
            for y in range(16 - hgt, 16):
                put(img, x, y, S4 if y > 16 - hgt + hgt * 0.6 and t > 0.4 else S3 if t > 0.3 else S2)
        out.append((60, img))
    return [("sf_wave", out)], (24, 16)


def planets():
    out = []
    specs = [((C("1c1030"), C("4a2a7a"), C("8a5ac0"), C("d0b0f0")), 6, "ring"),     # violet ringed giant
             ((C("20140a"), C("6a3a14"), C("c07a2a"), C("f4c070")), 5, "band"),     # amber banded
             ((C("0a1a2a"), C("1e4a6a"), C("3a8ab0"), C("a8e0f0")), 4, "ice"),      # ice world
             ((C("2a0a0a"), C("7a1a14"), C("d0402a"), C("ffb080")), 3, "ember")]     # red ember
    for pal, r, kind in specs:
        img = blank(16, 16)
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - 8, y + 0.5 - 8
                d = math.hypot(dx, dy)
                if d <= r:
                    l = -(dx * 0.6 + dy * 0.7) / r
                    v = 1.4 + 1.2 * l
                    if kind == "band" and int((y - 8 + dx * 0.2) * 0.9) % 2 == 0:
                        v -= 0.6
                    put(img, x, y, pal[max(0, min(3, int(v + 0.5)))])
        if kind == "ring":
            for i in range(60):
                a = i / 60 * 2 * math.pi
                x, y = 8 + math.cos(a) * 7.5, 8 + math.sin(a) * 2.2
                if not (math.sin(a) < 0 and abs(math.cos(a)) < 0.8):
                    put(img, x, y, pal[3] if math.cos(a) < 0 else pal[2])
        out.append((100, outline(img)))
    return [("planet", out)], (16, 16)


def eye():
    out = []
    for f in range(6):
        img = blank(32, 32)
        r = 2 + f * 2.2
        ring(img, 16, 16, r, S3 if f < 4 else S2, 1)
        disc(img, 16, 16, max(1, 4 - f * 0.4), S4)
        for k in range(8):
            a = k / 8 * 2 * math.pi + f * 0.4
            for i in range(int(r), int(r + 3)):
                put(img, 16 + math.cos(a) * i, 16 + math.sin(a) * i, S2)
        out.append((60, img))
    return [("sf_eye", out)], (32, 32)


def crescent():
    out = []
    for f in range(4):
        img = blank(40, 48)
        for i in range(120):
            t = i / 119
            a = -1.25 + t * 2.5
            for w in range(6):
                r = 20 - w * 0.9 * (1 - abs(t - 0.5) * 1.6)
                x, y = 10 + math.cos(a) * r, 24 + math.sin(a) * r * 1.05
                c = S4 if w < 2 else S3 if w < 4 else S2
                if abs(t - 0.5) > 0.42 and w > 2:
                    continue
                put(img, x + f * 0.5, y, c)
        for k in range(6):
            put(img, 6 + h01(k, f, 3) * 10, 8 + h01(k, f, 4) * 32, S2)
        out.append((60, img))
    return [("sf_crescent", out)], (40, 48)


def meteor():
    out = []
    for f in range(4):
        img = blank(32, 32)
        for y in range(32):
            for x in range(32):
                d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
                if d < 11 + math.sin(f * 1.7 + math.atan2(y - 16, x - 16) * 5) * 1.2:
                    put(img, x, y, S1 if d > 9 else S2)
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - 16, y + 0.5 - 16
                d = math.hypot(dx, dy)
                if d < 7:
                    l = -(dx * 0.6 + dy * 0.7) / 7
                    rock = [C("2a2f4a"), C("4a5070"), C("6e7494"), C("a8b0d0")]
                    put(img, x, y, rock[max(0, min(3, int(1.5 + l * 1.6)))])
                    if 6 <= d:
                        put(img, x, y, S3)
        disc(img, 19, 19, 3, S4)
        disc(img, 19, 19, 1.5, C("ffffff"))
        out.append((60, img))
    return [("sf_meteor", out)], (32, 32)


def impact():
    out = []
    for f in range(7):
        img = blank(96, 64)
        r = 6 + f * 7
        if f < 6:
            ring(img, 48, 58, r, S3 if f < 3 else S2, 2 if f < 4 else 1, ry=r * 0.4)
        if f < 4:
            disc(img, 48, 56, 10 - f * 2, S4)
            for k in range(14):
                a = -math.pi * (k + 0.5) / 14
                L = (14 + f * 8) * (0.6 + 0.4 * h01(k, 1, 7))
                for i in range(int(L * 0.3), int(L)):
                    put(img, 48 + math.cos(a) * i, 58 + math.sin(a) * i * 0.8, S4 if i < L * 0.5 else S3)
        for k in range(16 if f > 1 else 0):
            put(img, 48 + (h01(k, f, 9) - 0.5) * 80, 58 - h01(k, 3, 9) * 44 + f * 3, S3 if k % 2 else V2)
        if f >= 3:
            for x in range(20, 76):
                if h01(x, f, 2) < 0.5:
                    put(img, x, 63, C("7a9cf2") if f < 6 else C("3e5cc0"))
        out.append((50 if f < 3 else 70, img))
    return [("sf_impact", out)], (96, 64)


FX = {"fx_sf_crescent": crescent, "fx_sf_meteor": meteor, "fx_sf_impact": impact, "fx_sf_moonstep": moonstep, "fx_sf_shard": shard, "fx_sf_star": star, "fx_sf_burst": burst, "fx_sf_well": well,
      "fx_sf_arrow": arrow, "fx_sf_pillar": pillar, "fx_sf_wave": wave, "fx_sf_planet": planets, "fx_sf_eye": eye}


def main():
    ase = "--no-ase" not in sys.argv
    rows = []
    for name, fn in FX.items():
        anims, (w, h) = fn()
        frames, tags = [], []
        for tag, frs in anims:
            a = len(frames)
            for ms, img in frs:
                frames.append({"ms": ms, "cels": {"Layer": img}})
            tags.append((tag, a, len(frames) - 1))
        if ase:
            asebuild.build(name, w, h, ["Layer"], frames, tags)
        row = Image.new("RGBA", (len(frames) * (w + 2), h + 2), (40, 40, 50, 255))
        for i, f in enumerate(frames):
            row.alpha_composite(f["cels"]["Layer"], (i * (w + 2) + 1, 1))
        rows.append(row)
    Wd = max(r.size[0] for r in rows); Hd = sum(r.size[1] for r in rows)
    pv = Image.new("RGBA", (Wd, Hd), (30, 30, 36, 255)); y = 0
    for r in rows:
        pv.paste(r, (0, y)); y += r.size[1]
    scale(pv, 3).save(os.path.join(HERE, "previews", "fx_starfall.png"))
    print("fx built" if ase else "fx previewed")


if __name__ == "__main__":
    main()
