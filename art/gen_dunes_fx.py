#!/usr/bin/env python3
"""FX for the Sunscorched Dunes (agent DU).

fx_du_coffin  40x64, 10 frames (pivot bottom): a gilt sarcophagus rises out of the sand (0-4), stands open (5), its lid slams
              shut (6-9) -- the engine hurts whoever stands inside while the lid comes down.
fx_du_disc    32x32, 6 frames loop (centred): the Pharaoh's hunting sun-disc, a spinning ring of fire around a white core.
Previews: art/previews/fx_dunes.png
"""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
from envlib import C, ramp, K, h01, clamp, blank, scale  # noqa: E402
from dunes_tiles import SD, GD, LP, ST, outline_k  # noqa: E402

AMB = ramp("6a2a04", "b25a0c", "f0901c", "ffc04a", "fff0b0", "fffcf0")


def coffin(f):
    """Frames 0-4 rise (clipped by the sand line), 5 open, 6-9 the lid closes from the right."""
    img = blank(40, 64)
    px = img.load()
    rise = min(1.0, (f + 1) / 5.0)
    close = 0.0 if f < 6 else min(1.0, (f - 5) / 3.0)
    top = int(64 - 58 * rise)
    cx = 20
    # the case: an anthropoid sarcophagus seen from the front (head, shoulders, tapering to the feet)
    def half(y):
        t = (y - top) / 58.0
        if t < 0.18:
            return 7 + t * 20
        if t < 0.3:
            return 10.6 + (t - 0.18) * 20
        return 13 - (t - 0.3) * 6
    for y in range(max(0, top), 64):
        hw = half(y)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if x < 0 or x >= 40:
                continue
            d = (x - cx) / max(1, hw)
            c = ST[6] if d < -0.4 else ST[5] if d < 0.4 else ST[4]
            px[x, y] = c
    # open interior (dark) with the lid swinging shut from the right
    for y in range(max(0, top + 4), 62):
        hw = half(y) - 2.5
        shut_x = cx + hw - close * 2 * hw
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if 0 <= x < 40 and x < shut_x:
                px[x, y] = (26, 14, 8, 255) if (x + y) % 5 else (40, 22, 10, 255)
    # the lid: gold, a painted face and crossed arms, slides over from the right
    if close > 0:
        for y in range(max(0, top + 2), 63):
            hw = half(y) - 1.5
            x0 = int(cx + hw - close * 2 * hw)
            for x in range(x0, int(cx + hw) + 1):
                if 0 <= x < 40:
                    px[x, y] = GD[4] if x < x0 + 2 else GD[3] if (y // 4) % 3 else LP[2]
        if close >= 1.0:
            fy = top + 8
            for (x, y, c) in ((cx - 2, fy, (20, 12, 8, 255)), (cx + 2, fy, (20, 12, 8, 255)), (cx, fy + 3, GD[2])):
                if 0 <= y < 64:
                    px[x, y] = c
    # gilt bands on the case
    for k in range(3):
        y = top + 16 + k * 12
        if 0 <= y < 64:
            for x in range(int(cx - half(y)), int(cx + half(y)) + 1):
                if 0 <= x < 40 and px[x, y][3]:
                    px[x, y] = GD[4] if x < cx else GD[3]
    img = outline_k(img)
    px = img.load()
    # sand spilling off and heaped at the base
    for x in range(0, 40):
        h = int(4 + 3 * math.sin(x * 0.5 + f) - abs(x - 20) * 0.12)
        for y in range(64 - max(1, h), 64):
            px[x, y] = SD[7] if y == 64 - h else SD[5]
    for k in range(12 if f < 6 else 18 if f in (7, 8) else 4):
        x = int(h01(k, f, 3) * 40)
        y = int(64 - 10 - h01(k, f, 4) * 40 * rise)
        if 0 <= y < 64 and px[x, y][3] == 0:
            px[x, y] = SD[8] if k % 2 else SD[6]
    return img


def disc(f):
    img = blank(32, 32)
    px = img.load()
    c = 15.5
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - c, y - c)
            a = math.atan2(y - c, x - c)
            if d < 5.2:
                px[x, y] = AMB[5] if d < 3 else AMB[4]
            elif d < 8.5:
                px[x, y] = AMB[3] if d < 7 else AMB[2]
            elif d < 12.5:
                flame = 0.5 + 0.5 * math.sin(a * 8 + f * math.pi / 3 * 2)
                if d < 9.5 + flame * 3.0:
                    px[x, y] = AMB[2] if d < 10.5 else AMB[1]
    for k in range(10):                                                           # sparks thrown off the rim
        a = k / 10 * 2 * math.pi + f * 0.5
        r = 13 + (k % 3)
        x, y = int(round(c + math.cos(a) * r)), int(round(c + math.sin(a) * r))
        if 0 <= x < 32 and 0 <= y < 32:
            px[x, y] = AMB[3] if k % 2 else AMB[1]
    return img


def main():
    ase = "--preview" not in sys.argv
    specs = {
        "fx_du_coffin": (40, 64, [coffin(f) for f in range(10)], [100, 90, 80, 80, 90, 160, 60, 50, 60, 260], "du_coffin"),
        "fx_du_disc": (32, 32, [disc(f) for f in range(6)], [70] * 6, "du_disc"),
    }
    rows = []
    for name, (w, h, ims, ms, tag) in specs.items():
        rows.append((name, w, h, ims))
        if ase:
            asebuild.build(name, w, h, ["Layer"], [{"ms": m, "cels": {"Layer": im}} for m, im in zip(ms, ims)], [(tag, 0, len(ims) - 1)])
    k = 4
    Wd = max(len(r[3]) * (r[1] * k + 6) for r in rows) + 10
    Hd = sum(r[2] * k + 20 for r in rows) + 10
    sheet = Image.new("RGBA", (Wd, Hd), (70, 70, 76, 255))
    d = ImageDraw.Draw(sheet)
    y = 6
    for name, w, h, ims in rows:
        d.text((6, y), name, fill=(235, 235, 235, 255))
        for i, im in enumerate(ims):
            sheet.alpha_composite(scale(im, k), (6 + i * (w * k + 6), y + 14))
        y += h * k + 20
    sheet.save(os.path.join(HERE, "previews", "fx_dunes.png"))
    print("built fx")


if __name__ == "__main__":
    main()
