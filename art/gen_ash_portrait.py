#!/usr/bin/env python3
"""Old Ashwright's dialogue portrait (portrait_ashwright, 64x64), redrawn from the user's reference: a huge old smith
with a wild grey mane under a red headband, a long flowing beard, a heavy weathered brow, bare muscled shoulders under
riveted leather straps and a red smithing apron, lit from below by the forge. His gold prosthetic arm (lore) stays, on
the near shoulder. Same frame, size and backdrop treatment as the other portraits.

    python3 art/gen_ash_portrait.py [--preview]
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
_argv = sys.argv
sys.argv = [sys.argv[0], "--preview"]
import gen_npcs as N  # noqa: E402
import gen_venn_portrait as V  # noqa: E402   (pixel helpers: poly, ell, edge, pick, C)
sys.argv = _argv
import asebuild  # noqa: E402

BUILD = "--preview" not in sys.argv
PW, C, poly, ell, edge, pick = 64, V.C, V.poly, V.ell, V.edge, V.pick
HAIR = [C("#231f20"), C("#3b3534"), C("#5a524f"), C("#7e7470"), C("#a39892"), C("#c9beb5"), C("#e6ddd2")]
SKIN = [C("#241410"), C("#40241b"), C("#633828"), C("#8a5139"), C("#b0704f"), C("#d09470"), C("#eab893")]
RED = [C("#1f0808"), C("#3e0f0e"), C("#651814"), C("#8e2519"), C("#b63a22"), C("#dc5a30")]
LEA = [C("#120c0a"), C("#241814"), C("#3a2820"), C("#553b2c"), C("#76553e")]
GOLD = [C("#2c1b06"), C("#5a3a0e"), C("#8d6116"), C("#bf8d26"), C("#e6b847"), C("#fbe39a")]
FORGE, FORGE2, OUT = C("#ff8a3a"), C("#ffc070"), C("#070405")


def draw_figure():
    img = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    px = img.load()

    def put(p, c):
        if 0 <= p[0] < PW and 0 <= p[1] < PW:
            px[p] = c

    def forge(x, y):   # warm light rising from the anvil, low on the left
        return max(0.0, 1 - math.hypot(x - 6, y - 70) / 58)

    # ---- mane behind the shoulders: wild, swept back and down both sides
    mane = poly([(14, 16), (20, 8), (32, 5), (44, 8), (51, 16), (54, 28), (55, 42), (52, 50), (46, 46), (44, 30), (40, 20),
                 (24, 20), (20, 30), (18, 46), (12, 50), (9, 40), (10, 28)])
    for p in mane:
        x, y = p
        wave = math.cos(2 * math.pi * (x + .5 - 2.2 * math.sin(y * 0.3)) / 6.5)
        v = 0.26 + 0.1 * wave - 0.14 * max(0, (y - 30) / 20) + 0.3 * forge(x, y) + 0.12 * max(0, (14 - y) / 8)
        put(p, pick(HAIR, v, x, y, dither=False))
    # ragged outline: bite into the mane's edge and flick strand tips outward
    h = lambda x, y: ((x * 73856093) ^ (y * 19349663)) % 7
    cx0 = 32
    for p in list(edge(mane)):
        x, y = p
        if y > 12 and h(x, y) < 3:
            px[p] = (0, 0, 0, 0)
        if y > 14 and h(x, y) == 6:
            d = -1 if x < cx0 else 1
            for k in (1, 2):
                put((x + d * k, y + k), HAIR[2] if k == 1 else HAIR[1])
    # ---- shoulders: huge bare traps and deltoids; the near (left) shoulder is the gold prosthetic
    torso = poly([(0, 64), (0, 52), (6, 45), (16, 41), (26, 42), (38, 42), (48, 41), (58, 45), (64, 52), (64, 64)])
    for p in torso:
        x, y = p
        dl = max(0.0, 1 - math.hypot((x - 55) / 9, (y - 50) / 7))         # far deltoid catches light
        tr = max(0.0, 1 - math.hypot((x - 44) / 6, (y - 45) / 4))          # trapezius
        v = 0.3 + 0.28 * dl + 0.12 * tr + 0.4 * forge(x, y) - 0.1 * (y > 58)
        put(p, pick(SKIN, v, x, y, dither=False))
    gold = ell(9, 55, 11, 10) & torso
    for p in gold:
        x, y = p
        n = (x + .5 - 9) / 11, (y + .5 - 55) / 10
        v = 0.55 - 0.3 * n[1] - 0.25 * n[0] + 0.2 * forge(x, y) - 0.25 * (n[0] ** 2 + n[1] ** 2)
        spec = max(0.0, 1 - math.hypot(n[0] + 0.35, n[1] + 0.45) / 0.3)
        put(p, pick(GOLD, v + 0.5 * spec, x, y, dither=False))
    for k in (-3, 2):                                                   # plate seams and rivets
        for x in range(0, 19):
            q = (x, 55 + k + (x - 9) // 6)
            if q in gold:
                put(q, GOLD[1])
    for q in ((5, 49), (11, 48), (16, 51), (3, 57)):
        put(q, GOLD[5]); put((q[0] + 1, q[1] + 1), GOLD[1])
    # ---- riveted leather straps over both shoulders, down into the apron bib
    for (a, b) in (((20, 42), (25, 64)), ((46, 42), (40, 64))):
        for i in range(24):
            t = i / 23
            cx, cy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for w in range(-2, 2):
                q = (int(round(cx + w)), int(round(cy)))
                put(q, LEA[3] if w == -2 else LEA[2] if w < 1 else LEA[1])
            if i % 6 == 3:
                put((int(round(cx)), int(round(cy))), C("#c9b89c"))            # rivet
    # ---- red apron bib at the chest (mostly under the beard)
    apron = poly([(24, 54), (40, 54), (41, 64), (23, 64)])
    for p in apron:
        x, y = p
        put(p, pick(RED, 0.45 + 0.3 * forge(x, y) + 0.05 * math.sin(x * 0.8), x, y))
    for x in range(24, 41):
        put((x, 54), RED[4])
    # ---- neck and face: heavy brow, deep-set glinting eyes, big nose, weathered
    neck = poly([(26, 36), (38, 36), (40, 44), (24, 44)])
    for p in neck:
        put(p, pick(SKIN, 0.3 + 0.2 * forge(*p), *p))
    face = poly([(24, 20), (28, 17), (36, 17), (40, 20), (41, 27), (40.5, 33), (38, 38), (32, 40), (26, 38), (23.5, 33), (23, 27)])
    for p in face:
        x, y = p
        cx = abs(x + .5 - 32) / 9
        cheek = max(0.0, 1 - math.hypot((abs(x + .5 - 32) - 5.5) / 2.5, (y - 29.5) / 1.8))
        v = 0.5 - 0.38 * cx ** 2 + 0.12 * cheek + 0.28 * forge(x, y) - 0.12 * (y < 21) - 0.1 * (x > 36)
        put(p, pick(SKIN, v, x, y, dither=False))
    for x in range(24, 41):                                             # the brow ridge casts deep shadow
        put((x, 25), SKIN[3] if 26 <= x <= 38 else SKIN[2])
        put((x, 26), SKIN[1] if x not in (32,) else SKIN[2])
    for (x0, x1, gx) in ((26, 30, 29), (34, 38, 35)):
        for x in range(x0, x1 + 1):
            put((x, 27), SKIN[0])
        put((gx, 27), C("#d8c7a8"))                                      # the eye glint under the brow
        put((x0, 28), SKIN[2]); put((x1, 28), SKIN[2])
    for y in range(26, 33):                                             # nose
        put((32, y), SKIN[5] if y < 31 else SKIN[4])
        put((33, y), SKIN[2])
    put((31, 32), SKIN[2]); put((33, 32), SKIN[1]); put((32, 33), SKIN[1])
    for (a, b) in (((27, 21), (30, 22)), ((34, 22), (37, 21)), ((25, 30), (26, 33)), ((39, 30), (38, 33))):   # wrinkles
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1])) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            put((int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t))), SKIN[2])
    # bushy grey brows
    for (x0, x1, d) in ((25, 31, 1), (33, 39, -1)):          # heavy brows, drawn down toward the nose (a scowl)
        for x in range(x0, x1 + 1):
            t = (x - x0) / (x1 - x0) if d > 0 else (x1 - x) / (x1 - x0)
            yb = 23 + round(t * 1.4)
            put((x, yb), HAIR[5] if t > 0.4 else HAIR[4])
            put((x, yb - 1), HAIR[3] if t > 0.3 else HAIR[2])
    # ---- red headband across the brow, knot trailing on his left
    for x in range(22, 43):
        y0 = 18 + (abs(x - 32) / 10) ** 2 * 1.5
        put((x, int(y0)), RED[4]); put((x, int(y0) + 1), RED[3]); put((x, int(y0) + 2), RED[2])
    for (x, y) in ((43, 19), (44, 20), (45, 22), (46, 24), (44, 21), (45, 25), (46, 27)):
        put((x, y), RED[3] if y < 23 else RED[2])
    # front hair: swept back over the crown above the band, strands falling at the temples
    crown = poly([(21, 18), (24, 11), (32, 8.5), (40, 11), (43, 18)])
    for p in crown:
        x, y = p
        v = 0.46 + 0.1 * math.cos(2 * math.pi * (x + .5 - (x - 32) * 0.4 * (18 - y) / 10) / 3.5) + 0.12 * max(0, (13 - y) / 4) - 0.1 * (x > 38)
        put(p, pick(HAIR, v, x, y, dither=False))
    for side in (-1, 1):
        for k in range(2):
            x0 = 32 + side * (9.5 + k)
            for y in range(21, 31 + 3 * k):
                put((int(x0 + side * 0.2 * (y - 21)), y), HAIR[3 - k] if side < 0 else HAIR[2 - k])
    # ---- the beard: long, grey, flowing to a point over the apron; moustache over the mouth; forge-lit edge
    beard = poly([(23, 30), (26, 34), (29, 35), (35, 35), (38, 34), (41, 30), (42, 38), (41, 46), (38, 54), (35, 60), (32, 63),
                  (29, 59), (26, 53), (23, 45), (22, 37)])
    for p in beard:
        x, y = p
        strand = math.cos(2 * math.pi * (x + .5 - 32 - 0.12 * (y - 34) * (1 if x < 32 else -1)) / 3.6)
        v = 0.5 + 0.1 * strand - 0.28 * max(0, (y - 42) / 20) + 0.22 * forge(x, y) - 0.12 * (x > 36) - 0.1 * max(0, 1 - abs(y - 37) / 2)
        put(p, pick(HAIR, v, x, y, dither=False))
    for p in edge(beard):
        if p[0] < 32 and p[1] > 38:
            put(p, C("#e8a068"))                                        # forge light on the beard's edge
    mous = poly([(26.5, 33), (31, 32), (32, 33), (33, 32), (37.5, 33), (36, 36), (32, 35), (28, 36)])
    for p in mous:
        put(p, pick(HAIR, 0.72 + 0.1 * ((p[0] + p[1]) % 2), *p, dither=False))
    for x in range(30, 35):
        put((x, 36), SKIN[0])                                            # the mouth in the beard's shadow
    # forge rim light on the left of the face and shoulders
    for p in edge(face | torso | mane):
        x, y = p
        if forge(x, y) > 0.35 and px[p][3] and (x - 1, y) not in (face | torso | mane):
            put(p, FORGE2 if forge(x, y) > 0.55 else FORGE)
    return img


def build():
    fig = draw_figure()
    bg = N.backdrop([C("#0b0605"), C("#170c08"), C("#26130b"), C("#3c1d0e"), C("#5c2c12"), C("#8a4418")], (8, 60), glow_r=44, glow_amt=0.75)
    layers = {"Backdrop": bg, "Figure": N.clip_arch(fig), "Frame": N.frame_img()}
    flat = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    for n in ("Backdrop", "Figure", "Frame"):
        flat.alpha_composite(layers[n])
    prev = os.path.join(ART, "previews")
    flat.resize((PW * 8, PW * 8), Image.NEAREST).save(os.path.join(prev, "portrait_ashwright_8x.png"))
    flat.resize((144, 144), Image.NEAREST).save(os.path.join(prev, "portrait_ashwright_ingame.png"))
    if BUILD:
        asebuild.build("portrait_ashwright", PW, PW, ["Backdrop", "Figure", "Frame"], [{"ms": 1000, "cels": layers}], [("p", 0, 0)])
    return flat


if __name__ == "__main__":
    build()
