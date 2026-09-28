#!/usr/bin/env python3
"""Sister Venn's dialogue portrait (portrait_venn, 64x64), redrawn from the user's reference: a young nun with long
silver hair and a fringe falling between half-lidded grey eyes, a black veil with a silver-embroidered band, a high
black collar, a chain with a silver cross, and a thin white halo ring behind her. Same frame, size and backdrop
treatment as the other portraits (helpers from gen_npcs.py); the figure is painted pixel by pixel.

    python3 art/gen_venn_portrait.py [--preview]     (--preview: art/previews/portrait_venn_*.png only, no Aseprite)
"""
import math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
_argv = sys.argv
sys.argv = [sys.argv[0], "--preview"]          # import gen_npcs for its helpers without building anything
import gen_npcs as N  # noqa: E402
sys.argv = _argv
import asebuild  # noqa: E402

BUILD = "--preview" not in sys.argv
PW = 64
C = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
# palettes (cool, desaturated, like the reference)
VEIL = [C("#070609"), C("#0f0d13"), C("#18151e"), C("#241f2c"), C("#352f40"), C("#4d4659")]
HAIR = [C("#34323d"), C("#4f4d5a"), C("#716f7d"), C("#9795a3"), C("#bcbac7"), C("#dddbe5"), C("#f4f3f8")]
SKIN = [C("#5d4b52"), C("#8c767d"), C("#b8a3a8"), C("#d9c8ca"), C("#eee3e2"), C("#faf4f2")]
SILV = [C("#4a4755"), C("#7a7788"), C("#aeabbb"), C("#dcdae6"), C("#ffffff")]
IRIS = [C("#2a2a36"), C("#5b5d6e"), C("#8d90a2"), C("#c3c5d2")]
LIP, BLUSH, OUT = C("#9c7780"), C("#d7b3b7"), C("#060508")
BAYER = N.BAYER


def bt(x, y):
    return (BAYER[y & 3][x & 3] + 0.5) / 16.0


def pick(ramp, v, x, y, dither=True):
    v = max(0.0, min(0.999, v))
    f = v * (len(ramp) - 1)
    i = int(f)
    if f - i > (bt(x, y) if dither else 0.5):
        i += 1
    return ramp[min(i, len(ramp) - 1)]


def poly(pts):
    m = Image.new("L", (PW, PW), 0)
    ImageDraw.Draw(m).polygon([(x, y) for x, y in pts], fill=255)
    px = m.load()
    return {(x, y) for y in range(PW) for x in range(PW) if px[x, y]}


def ell(cx, cy, rx, ry):
    return {(x, y) for y in range(PW) for x in range(PW) if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1}


def edge(mask):
    return {p for p in mask if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def draw_figure():
    img = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    px = img.load()

    def put(p, c):
        if 0 <= p[0] < PW and 0 <= p[1] < PW:
            px[p] = c

    def blend(p, c, a):
        if not (0 <= p[0] < PW and 0 <= p[1] < PW):
            return
        o = px[p]
        if o[3] == 0:
            px[p] = c[:3] + (int(255 * a),)
        else:
            px[p] = tuple(int(o[i] * (1 - a) + c[i] * a) for i in range(3)) + (max(o[3], int(255 * a)),)

    # ---- the halo: a thin white ring behind the head, soft glow either side
    hc, hr = (32.0, 24.5), 21.0
    for y in range(PW):
        for x in range(PW):
            d = abs(math.hypot(x + .5 - hc[0], y + .5 - hc[1]) - hr)
            if d < 0.55:
                put((x, y), C("#f6f6fb"))
            elif d < 1.6:
                blend((x, y), C("#c9cde0"), 0.55 * (1.6 - d))
            elif d < 3.4:
                blend((x, y), C("#8a90aa"), 0.16 * (3.4 - d) / 1.8)

    # ---- long hair behind the veil (falls over the shoulders, visible either side of the chest)
    back_hair = poly([(17, 30), (22, 22), (42, 22), (47, 30), (49, 44), (48, 58), (44, 62), (40, 56), (39, 44),
                      (25, 44), (24, 56), (20, 62), (16, 58), (15, 44)])
    # ---- veil: a heavy black hood falling to the shoulders, widening into the mantle
    veil = poly([(32, 6.5), (38.5, 7.5), (43.5, 10.5), (47, 15.5), (49, 22), (50, 30), (50.5, 38), (52.5, 46), (56, 52),
                 (60, 57), (61, 64), (3, 64), (4, 57), (8, 52), (11.5, 46), (13.5, 38), (14, 30), (15, 22), (17, 15.5),
                 (20.5, 10.5), (25.5, 7.5)])
    opening = poly([(24, 16.5), (32, 14.5), (40, 16.5), (43, 21), (44.5, 28), (44, 36), (42.5, 44), (41, 52), (40, 64),
                    (24, 64), (23, 52), (21.5, 44), (20, 36), (19.5, 28), (21, 21)])
    for p in veil - opening:
        x, y = p
        # backlit by the halo: brighter toward the outer edge and the crown; folds run down the drape
        dx = abs(x + .5 - 32) / 20
        rim = max(0.0, 1 - min(abs(x + .5 - 32) - 12, 99) * 0) if False else 0
        fold = 0.07 * math.sin(x * 0.9 + (y - 40) * 0.12) if y > 40 else 0
        v = 0.18 + 0.12 * (1 - y / 64) + 0.12 * dx + fold
        put(p, pick(VEIL, v, x, y))
    for p in edge(veil):
        if p not in opening and p[1] < 60:
            put(p, VEIL[4] if p[1] < 30 else VEIL[3])        # rim light from the halo
    # deep shadow just inside the veil around the face opening
    for p in edge(veil - opening) if False else ():
        pass
    near = {(x + dx, y + dy) for (x, y) in opening for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for p in (veil - opening) & near:
        put(p, VEIL[0])
    # embroidered trim running down the front edges of the veil and along the hood rim
    for y in range(45, 64):
        for side, x0 in ((-1, 22.5 - (y - 45) * 0.12), (1, 42.5 + (y - 45) * 0.12)):
            x = int(round(x0 - side * 1.5))
            put((x, y), SILV[1] if (y % 3) else SILV[2])
            if y % 3 == 0:
                put((x - side, y), SILV[0])

    # ---- body: black dress with a high collar between the veil edges
    body = poly([(23, 47), (41, 47), (42, 64), (22, 64)])
    for p in body:
        x, y = p
        put(p, pick(VEIL, 0.22 + 0.1 * math.sin(x * 0.7) * (y > 54), x, y))
    for p in back_hair - opening:
        pass
    # hair spilling over the shoulders in front of the dress, inside the veil opening
    locks = poly([(20, 36), (24, 40), (25.5, 50), (24.5, 60), (22, 63), (20.5, 56), (20.5, 46)]) | \
        poly([(44, 36), (40, 40), (38.5, 50), (39.5, 60), (42, 63), (43.5, 56), (43.5, 46)])
    collar = poly([(27, 43), (37, 43), (38, 49.5), (26, 49.5)])
    for p in collar:
        x, y = p
        put(p, pick(VEIL, 0.28 + 0.2 * (y < 45) - 0.1 * abs(x - 32) / 6, x, y))
    for x in range(27, 38):
        put((x, 43), VEIL[4] if 28 <= x <= 36 else VEIL[3])          # collar lip catches the light
    # neck
    neck = poly([(29, 38), (35, 38), (35, 44), (29, 44)])
    for p in neck:
        x, y = p
        put(p, pick(SKIN, 0.35 + 0.15 * (x - 29) / 6 - 0.2 * (y > 41), x, y))
    for x in range(29, 36):
        put((x, 42), SKIN[1])

    # ---- face: soft oval, slight downward tilt, lit from the front
    face = poly([(25, 24), (27, 20.5), (32, 19.5), (37, 20.5), (39, 24), (39.7, 30), (39, 35), (37, 39),
                 (34, 42), (30, 42), (27, 39), (25, 35), (24.3, 30)])
    for p in face:
        x, y = p
        cx = abs(x + .5 - 32) / 8
        v = 0.8 - 0.42 * cx ** 2 - 0.3 * max(0, (y - 36) / 6)
        put(p, pick(SKIN, v, x, y))
    for p in edge(face):                                          # jaw and cheek contour
        if p[1] > 32:
            put(p, SKIN[1] if p[1] > 37 or abs(p[0] - 32) > 6 else SKIN[2])
    for x in range(30, 35):
        put((x, 42), SKIN[0])                                     # under-chin shadow line
    # eyes: large, half-lidded (the lid cuts the top of the iris), grey, looking straight at you
    for (x0, x1, ix, far) in ((25, 30, 27, False), (34, 39, 35, True)):
        for x in range(x0, x1 + 1):
            put((x, 29), OUT)                                     # heavy upper lash line (2px)
            put((x, 30), OUT if x0 < x < x1 else SKIN[1])
        put((x1 + 1, 29) if not far else (x0 - 1, 29), OUT)        # outer flick (both toward the outside)
        put((x0 - 1, 29) if not far else (x1 + 1, 29), OUT)
        for x in range(x0 + 1, x1):
            put((x, 31), C("#dcd8e2")); put((x, 32), C("#c9c4d0"))  # sclera, shaded under the lid
        for dx in range(3):                                       # iris 3 wide, lid-cut top row darker
            put((ix + dx, 31), IRIS[1] if dx != 1 else IRIS[0])
            put((ix + dx, 32), IRIS[2] if dx != 1 else IRIS[1])
            put((ix + dx, 33), IRIS[2])
        put((ix + 2, 31), IRIS[3])                                # catchlight
        put((ix, 33), IRIS[3])
        for x in range(x0 + 1, x1):
            put((x, 34), SKIN[2])                                 # lower lid
        put((x0 + (1 if not far else 4), 34), SKIN[1])
        for x in range(x0 + 1, x1):
            put((x, 28), SKIN[2])                                 # lid crease
    # nose, mouth, faint blush
    put((32, 36), SKIN[2]); put((33, 37), SKIN[1])
    for x in (31, 32):
        put((x, 39), LIP)
    put((30, 39), SKIN[2]); put((33, 39), SKIN[2])
    for p in ((26, 36), (27, 36), (37, 36), (38, 36)):
        blend(p, BLUSH, 0.6)

    # ---- fringe and side locks: long silver strands; one lock falls between the eyes, one half over her right eye
    fringe = poly([(21, 18), (27, 15.5), (32, 15), (37, 15.5), (43, 18), (44, 24), (42.5, 27.5), (41, 25), (39.5, 28.5),
                   (37.5, 24.5), (35.5, 27.5), (34, 33.5), (32.6, 25.5), (31, 27.5), (29, 24.5), (27, 27.5), (25.5, 24.5),
                   (23.5, 28.5), (21.5, 25)])
    side_l = poly([(21, 20), (24.2, 24), (25, 30), (24.2, 36), (24.6, 42), (23.5, 48), (21.5, 53), (20, 47), (19.6, 38),
                   (19.8, 28)])
    side_r = poly([(43, 20), (39.8, 24), (39, 30), (39.8, 36), (39.4, 42), (40.5, 48), (42.5, 53), (44, 47), (44.4, 38),
                   (44.2, 28)])
    hair = fringe | side_l | side_r | (locks - face)
    def lock(x, y):                                               # wavy lock pattern: strands ~4px wide that sway
        off = 1.2 * math.sin(y * 0.35) + (x - 32) * 0.08 * (y - 16) / 10
        return math.cos(2 * math.pi * (x + .5 - off) / 5.0)
    for p in hair:
        x, y = p
        v = 0.56 + 0.13 * lock(x, y)
        v += 0.22 * math.exp(-((y - 21.5) / 2.2) ** 2)          # the sheen band across the crown
        v -= 0.28 * max(0, (y - 42) / 20)                        # tips darken as they fall into the veil
        v -= 0.22 * (y < 18)
        if p in side_l or p in side_r or (p in locks and p not in fringe):
            v -= 0.14 * max(0.0, 1 - abs(x + .5 - 32) / 12)       # inner sides of the locks sit in shadow
        put(p, pick(HAIR, v, x, y, dither=False))
    for p in edge(hair):
        x, y = p
        if (x, y + 1) in face and (x, y + 1) not in hair:
            put(p, HAIR[1])                                       # fringe underside
        elif (x + 1, y) in face or (x - 1, y) in face:
            put(p, HAIR[2])
    for p in face:                                               # the fringe casts a soft shadow on the forehead
        if (p[0], p[1] - 1) in fringe and p not in hair and px[p][:3] != OUT[:3]:
            put(p, SKIN[2])
    # bright strands catching the halo light
    for (a, b) in (((27, 17), (26, 25)), ((33.5, 16), (33.4, 31)), ((38, 17), (39.8, 26)), ((21.5, 22), (21, 46)),
                   ((42.5, 22), (43, 46))):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            q = (int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t)))
            if q in hair:
                put(q, HAIR[6] if (i % 4 == 1 and t < 0.6) else HAIR[5] if t < 0.7 else HAIR[4])

    # ---- the embroidered band across the brow (silver pattern on black)
    band_top = lambda x: 15.2 + ((x - 32) / 11.5) ** 2 * 2.6
    for x in range(20, 45):
        y0 = band_top(x)
        for k in range(3):
            p = (x, int(y0) + k)
            put(p, VEIL[1] if k != 1 else VEIL[2])
        if x % 2 == 0:
            put((x, int(y0) + 1), SILV[2] if x % 4 == 0 else SILV[1])
        put((x, int(y0)), SILV[0] if x % 4 == 2 else VEIL[3])
    # ---- chain and cross
    chain = [(27, 45), (28, 47), (29, 49), (30, 51), (31, 53), (32, 54), (33, 53), (34, 51), (35, 49), (36, 47), (37, 45)]
    for i, p in enumerate(chain):
        put(p, SILV[2] if i % 2 else SILV[1])
    for y in range(55, 61):
        put((32, y), SILV[3] if y < 58 else SILV[2])
    for x in (30, 31, 33, 34):
        put((x, 56), SILV[2])
    put((32, 56), SILV[4]); put((33, 57), SILV[0]); put((31, 57), SILV[0])
    return img


def build():
    fig = draw_figure()
    bg = N.backdrop([C("#09080d"), C("#110f17"), C("#1a1822"), C("#26232f"), C("#3a3747")], (32, 24), glow_r=30, glow_amt=0.55)
    layers = {"Backdrop": bg, "Figure": N.clip_arch(fig), "Frame": N.frame_img()}
    flat = Image.new("RGBA", (PW, PW), (0, 0, 0, 0))
    for n in ("Backdrop", "Figure", "Frame"):
        flat.alpha_composite(layers[n])
    prev = os.path.join(ART, "previews")
    flat.resize((PW * 8, PW * 8), Image.NEAREST).save(os.path.join(prev, "portrait_venn_8x.png"))
    # how it reads in the dialogue box (drawn at 48 low-res px, x3 screen scale)
    flat.resize((144, 144), Image.NEAREST).save(os.path.join(prev, "portrait_venn_ingame.png"))
    if BUILD:
        asebuild.build("portrait_venn", PW, PW, ["Backdrop", "Figure", "Frame"], [{"ms": 1000, "cels": layers}], [("p", 0, 0)])
    return flat


if __name__ == "__main__":
    build()
