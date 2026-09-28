"""Training Grounds art (agent TR, asset prefix trn_ + the `training` biome's tiles/parallax).

A clean white dev test chamber: light grey wall panels with thin graphite outlines on every exposed face, a 16 px panel
grid on the back wall, safety-striped platform caps and graphite spikes with orange warning tips. Plus the training dummy
(a sleek graphite mannequin on a weighted base with a bullseye plate), which reads well against the white.

  tiles_training      48 x 16x16, the standard tile index layout (docs/ART_SPEC.md section 6, see art/deep_tiles.py)
  bg_training_far     512x216 opaque: off-white with a faint 32 px grid and registration crosses (slow parallax)
  trn_dummy           32x44: idle (2), hurt (4) -- + assets/trn_dummy_meta.json

Run: python3 art/gen_training.py
"""
import json, os
from PIL import Image
import asebuild

ART = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(ART), "assets")
N, E, S, W = 1, 2, 4, 8
T = (0, 0, 0, 0)


def C(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# palette: cool neutral greys + one warning accent
G0, G1, G2, G3, G4, G5 = C("f7f8fa"), C("e6e9ed"), C("d9dde2"), C("c6cbd2"), C("a7adb6"), C("7d848f")
INK, INK2, INK3 = C("22252b"), C("33373f"), C("4a505a")
OR, OR2 = C("f08a24"), C("ffb85a")
YEL = C("f2c230")
WALL, WALL_LN, WALL_MK = C("eceef1"), C("d5d9de"), C("c3c8cf")


def img(w, h, fill=T):
    return Image.new("RGBA", (w, h), fill)


def px(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), c)


def rect(im, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(im, x, y, c)


# ---------------------------------------------------------------- tiles
def solid(mask, variant):
    t = img(16, 16, G2)
    # panel seams: every tile is one 16 px panel (the grid reads across big floors and walls)
    for i in range(16):
        px(t, 15, i, G3); px(t, i, 15, G3)
    for i in range(1, 15):
        px(t, 0, i, G1); px(t, i, 0, G1)
    if variant:   # bolted panel: four countersunk screws and a faint inset plate
        for x, y in ((3, 3), (12, 3), (3, 12), (12, 12)):
            px(t, x, y, G4); px(t, x + 1, y, G3)
        for i in range(5, 11):
            px(t, i, 6, G3); px(t, i, 9, G1)
    # exposed faces: a crisp graphite outline, a bright lip on top faces, a soft shade under bottom faces
    if mask & N:
        for i in range(16): px(t, i, 0, INK); px(t, i, 1, G0); px(t, i, 2, G1)
    if mask & S:
        for i in range(16): px(t, i, 15, INK); px(t, i, 14, G4); px(t, i, 13, G3)
    if mask & W:
        for i in range(16): px(t, 0, i, INK); px(t, 1, i, G1)
    if mask & E:
        for i in range(16): px(t, 15, i, INK); px(t, 14, i, G3)
    # rounded outer corners: the corner pixel goes, its neighbours become outline
    for cx, cy, a, b in ((0, 0, N, W), (15, 0, N, E), (0, 15, S, W), (15, 15, S, E)):
        if mask & a and mask & b:
            px(t, cx, cy, T)
            px(t, cx + (1 if cx == 0 else -1), cy, INK); px(t, cx, cy + (1 if cy == 0 else -1), INK)
            px(t, cx + (1 if cx == 0 else -1), cy + (1 if cy == 0 else -1), INK)
    return t


def platform(kind):   # 0 L, 1 M, 2 R, 3 single
    t = img(16, 16)
    rect(t, 0, 0, 15, 0, INK); rect(t, 0, 1, 15, 1, G0); rect(t, 0, 2, 15, 3, G2); rect(t, 0, 4, 15, 4, INK)
    for i in range(0, 16, 4): px(t, i, 3, G3)
    left, right = kind in (0, 3), kind in (2, 3)
    if left:   # safety-striped cap + a bracket under the end
        rect(t, 0, 0, 0, 4, INK)
        for x in range(1, 5):
            for y in range(1, 4):
                px(t, x, y, YEL if (x + y) % 4 < 2 else INK2)
        rect(t, 2, 5, 3, 7, INK3); px(t, 3, 8, INK3)
    if right:
        rect(t, 15, 0, 15, 4, INK)
        for x in range(11, 15):
            for y in range(1, 4):
                px(t, x, y, YEL if (x - y) % 4 < 2 else INK2)
        rect(t, 12, 5, 13, 7, INK3); px(t, 12, 8, INK3)
    return t


def spikes(up=True):
    t = img(16, 16)
    rect(t, 0, 14, 15, 15, INK); rect(t, 0, 13, 15, 13, G4)
    for k in range(4):
        x0 = k * 4
        for h in range(8):   # a slim spike: 3 px wide at the base, 1 px at the tip
            y = 12 - h
            w = 1 if h > 4 else 2 if h > 1 else 3
            for dx in range(w):
                c = OR if h >= 6 else INK2 if dx == 0 else INK3
                px(t, x0 + 1 + (3 - w) // 2 + dx, y, c)
        px(t, x0 + 2, 4, OR2)
    return t if up else t.transpose(Image.FLIP_TOP_BOTTOM)


def backwall(v):
    t = img(16, 16, WALL)
    for i in range(16):
        px(t, 15, i, WALL_LN); px(t, i, 15, WALL_LN)
    if v == 1:   # a registration plus at the panel centre
        for i in range(6, 10): px(t, i, 7, WALL_MK); px(t, 7, i, WALL_MK)
    return t


def deco(k):
    t = img(16, 16)
    if k == 0:   # hanging cable
        for y in range(16): px(t, 7 + (1 if 5 < y < 11 else 0), y, INK3)
    elif k == 1:   # cable bundle
        for y in range(16): px(t, 6, y, INK3); px(t, 9, y, INK2)
    elif k == 2:   # traffic cone
        for h in range(9):
            w = 1 + h // 2
            for dx in range(-w, w + 1): px(t, 8 + dx, 6 + h, OR if 2 < h < 5 else G0 if h == 5 else OR)
        rect(t, 3, 15, 13, 15, INK2)
    elif k == 3:   # crate
        rect(t, 3, 8, 12, 15, G3); rect(t, 3, 8, 12, 8, INK); rect(t, 3, 15, 12, 15, INK)
        rect(t, 3, 8, 3, 15, INK); rect(t, 12, 8, 12, 15, INK); rect(t, 5, 11, 10, 11, G4)
    return t


def tileset():
    tiles = [solid(m, False) for m in range(16)] + [solid(m, True) for m in range(16)]
    tiles += [platform(k) for k in range(4)]
    tiles += [spikes(True), spikes(False)]
    tiles += [backwall(v) for v in range(4)]
    tiles += [deco(k) for k in range(4)]
    brk = solid(0, False)
    for x, y in ((4, 3), (5, 4), (6, 5), (6, 6), (7, 7), (9, 8), (10, 9), (10, 10), (8, 8), (11, 11)): px(brk, x, y, INK3)
    tiles += [brk, img(16, 16)]
    assert len(tiles) == 48
    return tiles


# ---------------------------------------------------------------- parallax
def far():
    b = img(512, 216, C("f1f2f4"))
    for x in range(512):
        for y in range(216):
            if x % 128 == 0 or y % 128 == 40: b.putpixel((x, y), C("dde1e6"))
            elif x % 32 == 0 or y % 32 == 8: b.putpixel((x, y), C("e7e9ed"))
    for gx in range(0, 512, 128):   # registration crosses on the major grid
        for gy in (40, 168):
            for d in range(-4, 5):
                px(b, gx + d, gy, C("c7ccd3")); px(b, gx, gy + d, C("c7ccd3"))
    return b


# ---------------------------------------------------------------- the dummy
DW, DH = 32, 44
AX, AY = 16, 44


def dummy(lean=0.0, flash=False):
    """lean: top shift in px (shear about the base). The body is drawn upright, then each row is shifted."""
    up = img(DW, DH)
    # weighted base: a low flattened dome
    for x in range(8, 24):
        for y in range(40, 44):
            dx = (x - 15.5) / 8.0
            if dx * dx + ((y - 43.5) / 4.0) ** 2 <= 1.0:
                px(up, x, y, INK3 if y == 40 or abs(dx) > 0.85 else INK2)
    rect(up, 10, 43, 21, 43, INK)
    for x in range(11, 21): px(up, x, 40, G5)
    # pole
    rect(up, 15, 30, 16, 39, INK2); px(up, 16, 33, INK3); px(up, 16, 36, INK3)
    # torso: tapered, shoulders wider than the waist (heroic, not bulky)
    for y in range(12, 31):
        k = (y - 12) / 18.0
        half = round(6.5 - 2.5 * k) if y > 14 else (5 if y == 12 else 6)
        for x in range(16 - half, 16 + half):
            edge = x == 16 - half or x == 16 + half - 1
            px(up, x, y, INK if edge else (INK3 if x < 16 else INK2))
    # shoulder caps and a collar
    for x, y in ((10, 13), (21, 13), (10, 14), (21, 14)): px(up, x, y, G5)
    rect(up, 14, 10, 17, 11, INK2)
    # head: a small smooth ovoid
    for x in range(12, 20):
        for y in range(2, 10):
            if ((x - 15.5) / 3.6) ** 2 + ((y - 6) / 4.2) ** 2 <= 1.0:
                px(up, x, y, INK2 if x > 15 else INK3)
    px(up, 13, 4, G5); px(up, 14, 3, G5)
    # bullseye plate on the chest
    for x in range(11, 21):
        for y in range(14, 26):
            d = ((x - 15.5) ** 2 + (y - 19.5) ** 2) ** 0.5
            if d <= 4.6:
                px(up, x, y, OR if d > 3.4 else G0 if d > 2.2 else OR if d > 1.0 else INK)
    # a tape stripe at the waist
    rect(up, 12, 28, 19, 28, YEL)
    out = img(DW, DH)
    for y in range(DH):
        sh = round(lean * max(0, (40 - y)) / 38.0) if y < 40 else 0
        for x in range(DW):
            c = up.getpixel((x, y))
            if c[3]:
                if flash: c = G0
                px(out, x + sh, y, c)
    return out


def main():
    tiles = tileset()
    frames = [{"ms": 100, "cels": {"tiles": t}} for t in tiles]
    asebuild.build("tiles_training", 16, 16, ["tiles"], frames, [("all", 0, 47)])
    asebuild.build("bg_training_far", 512, 216, ["bg"], [{"ms": 100, "cels": {"bg": far()}}], [("loop", 0, 0)])
    idle = [dummy(0), dummy(0.6)]
    hurt = [dummy(3.2), dummy(-2.0), dummy(1.2), dummy(0)]
    fr = [{"ms": 700, "cels": {"body": f}} for f in idle] + [{"ms": ms, "cels": {"body": f}} for f, ms in zip(hurt, (70, 90, 110, 120))]
    asebuild.build("trn_dummy", DW, DH, ["body"], fr, [("idle", 0, 1), ("hurt", 2, 5)])
    meta = {"native": 1, "frame": [DW, DH], "anchor": [AX, AY], "hurtbox": [9, 2, 14, 40], "attacks": {}}
    json.dump(meta, open(os.path.join(ASSETS, "trn_dummy_meta.json"), "w"), indent=1)
    print("built tiles_training, bg_training_far, trn_dummy")


if __name__ == "__main__":
    main()
