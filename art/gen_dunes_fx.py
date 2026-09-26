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
from dunes_tiles import SD, GD, LP, ST, outline_k
import math  # noqa: E402

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


def skull(phase, k):
    """A floating golden jackal death-mask (the Pharaoh's sun-skulls), in profile facing right, 56x40, centred on its head.
    phase: appear (k 0-3: gathering out of sand motes), charge (k 0-3: jaw opening, eyes and mouth kindling),
    fire (k 0-1: jaw wide, light pouring out), vanish (k 0-2: breaking back into sand)."""
    import enemy_kit as EK
    import dunes_kit  # noqa: F401  (palette)
    from enemy_kit import Layer, FXLayer, poly_mask, n_plate, n_dome
    EK.setup(56, 40)
    L, Fx = Layer("S"), FXLayer("FX")
    cx, cy = 20.0, 23.0
    jaw = {"appear": 0.0, "charge": 0.2 + 0.25 * k, "fire": 1.0 + 0.1 * k, "vanish": 0.6}[phase]
    skull_pts = [(cx - 10, cy + 2), (cx - 11, cy - 4), (cx - 7, cy - 9), (cx - 1, cy - 10), (cx + 4, cy - 7), (cx + 17, cy - 3.5),
                 (cx + 22, cy - 2), (cx + 22.5, cy + 0.5), (cx + 15, cy + 1.5), (cx + 4, cy + 3), (cx - 4, cy + 6)]
    m = poly_mask(skull_pts)
    L.paint(n_plate(m, 2.4, (-0.1, -0.2), 1.2), "g", -1, ao=0)
    for (ex, top) in ((cx - 6.5, -22.0), (cx - 0.5, -21.0)):                     # tall ears
        em = poly_mask([(ex - 3.6, cy - 6), (ex + 0.4, cy + top + 1), (ex + 3.8, cy - 8)])
        L.paint(n_plate(em, 1.0, (-0.3, -0.3), 1.3), "g", -1 if ex < cx - 3 else 0, ao=1)
        L.decal([q for q in em if abs(q[0] + .5 - (ex + 0.4)) < 0.7 and q[1] > cy + top + 10], ("u", 2))
    # lower jaw, hinged under the ear, swinging open
    a = math.radians(8 + jaw * 26)
    hx, hy = cx + 2, cy + 3
    jp = [(hx - 2, hy - 1)] + [(hx + math.cos(a) * r - math.sin(a) * o, hy + math.sin(a) * r + math.cos(a) * o) for r, o in ((18, -1.2), (18.5, 1.2), (6, 3.4))]
    jm = poly_mask(jp)
    L.paint(n_plate(jm, 1.2, (-0.2, 0.2), 1.2), "g", -1, ao=1)
    # lapis nemes-stripes along the skull, kohl eye socket
    L.decal([q for q in m if q[0] < cx + 3 and int(q[1] - q[0] * 0.3) % 4 == 0], ("u", 1))
    L.decal([q for q in m if (q[0], q[1] - 1) not in m], ("g", 5))
    L.decal(polyline_pts([(cx + 4, cy - 4.5), (cx + 9, cy - 3.5)]), ("n", 0))
    img = EK.render_layer(L)
    fx = Fx.image()
    px, fp = img.load(), None
    # glow: eye and mouth light (stronger as it charges)
    glow = {"appear": 0, "charge": 1 + k // 2, "fire": 3, "vanish": 0}[phase]
    if glow:
        for (x, y) in polyline_pts([(cx + 5, cy - 4), (cx + 8, cy - 3.6)]):
            px[x, y] = C("fff0b0") if glow > 1 else C("ffc04a")
        mouth = (cx + 14, cy + 3 + jaw * 3)
        for q in mask_pts(mouth, 1.5 + glow * 1.4):
            d = math.hypot(q[0] + .5 - mouth[0], q[1] + .5 - mouth[1]) / (1.5 + glow * 1.4)
            if 0 <= q[0] < 56 and 0 <= q[1] < 40 and px[q][3] == 0:
                px[q] = AMB[5] if d < 0.35 else AMB[4] if d < 0.6 else AMB[3] if d < 0.85 else AMB[2]
    if phase in ("appear", "vanish"):
        frac = (k + 1) / 5.0 if phase == "appear" else 1 - (k + 1) / 4.0
        for y in range(40):
            for x in range(56):
                if px[x, y][3] and h01(x, y, 5) > frac + 0.1:
                    px[x, y] = (0, 0, 0, 0)
        for j in range(26):
            x, y = int(h01(j, k, 3) * 56), int(h01(j, k, 4) * 40)
            if px[x, y][3] == 0:
                px[x, y] = SD[8] if j % 2 else SD[6]
    return img


def polyline_pts(pts):
    from enemy_kit import polyline, ip
    return polyline([ip(p) for p in pts])


def mask_pts(c, r):
    from enemy_kit import mask_disc
    return mask_disc(c, r)


def main():
    ase = "--preview" not in sys.argv
    specs = {
        "fx_du_coffin": (40, 64, [coffin(f) for f in range(10)], [100, 90, 80, 80, 90, 160, 60, 50, 60, 260], "du_coffin"),
        "fx_du_disc": (32, 32, [disc(f) for f in range(6)], [70] * 6, "du_disc"),
    }
    sk = [skull("appear", k) for k in range(4)] + [skull("charge", k) for k in range(4)] + [skull("fire", k) for k in range(2)] + \
         [skull("vanish", k) for k in range(3)]
    rows = [("fx_du_skull", 56, 40, sk)]
    if ase:
        asebuild.build("fx_du_skull", 56, 40, ["Layer"], [{"ms": 80, "cels": {"Layer": im}} for im in sk],
                       [("appear", 0, 3), ("charge", 4, 7), ("fire", 8, 9), ("vanish", 10, 12)])
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
