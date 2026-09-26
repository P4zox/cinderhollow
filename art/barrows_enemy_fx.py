"""fx_db_splash (48x32, 6 frames, tag fx_db_splash, pivot bottom-centre [24,32]). See gen_barrows_enemies.py.

A splash crown of the Barrows' black tide: dark teal-black water spikes with pale foam tips rising out of a
pool, droplets thrown up, then everything falls back into spreading ripples. Crisp colour bands; only the fine
spray uses a couple of alpha steps. Two layers: Water (body) under Foam (tips, droplets, spray).
"""
import math, os
from PIL import Image, ImageDraw
import enemy_kit as K
from enemy_kit import hash01
import barrows_enemy_kit as B

W, H = 48, 32
CX = 24.0
FL = 31                       # floor row (pool surface)
C = {k: K.RGBA[k] for k in K.RGBA if k.startswith("dW") or k == "OUT"}


def col(k, a=255):
    c = K.RGBA[k]
    return (c[0], c[1], c[2], a)


def put(img, x, y, c, over=True):
    x, y = int(math.floor(x)), int(math.floor(y))
    if 0 <= x < W and 0 <= y < H and (over or img.getpixel((x, y))[3] == 0):
        img.putpixel((x, y), c)


# per-spike: (x offset, relative height, lean)
SPIKES = [(-13.0, 0.45, -0.55), (-9.0, 0.75, -0.35), (-5.0, 1.0, -0.15), (-1.5, 0.7, -0.05), (1.5, 0.72, 0.05),
          (5.0, 0.95, 0.15), (9.0, 0.8, 0.35), (13.0, 0.5, 0.55)]
# per-frame: crown height, crown spread, pool half-width, droplet time, ripple radius
FR = [(6.0, 0.7, 9.0, 0.10, 0.0), (13.0, 0.9, 12.0, 0.30, 0.0), (18.0, 1.0, 14.0, 0.50, 0.0),
      (14.0, 1.12, 15.0, 0.68, 4.0), (7.0, 1.22, 16.0, 0.84, 9.0), (2.0, 1.3, 17.0, 1.0, 14.0)]
MS = [50, 60, 70, 80, 90, 120]


def spike(water, foam, x0, h, lean, w0, fall):
    """Tapered water tongue from the pool at x0 up to height h, leaning outward; foam cap at the tip.
    fall 0..1 = the tongue is collapsing (tip breaks into a bead that drops)."""
    if h < 1:
        return
    tip = (x0 + lean * h, FL - h)
    n = int(h) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        y = FL - t * h
        x = x0 + lean * t * h + math.sin(t * 3.0) * lean * 0.8
        half = w0 * (1 - t) ** 0.8 + 0.25
        for xx in range(int(math.floor(x - half)), int(math.ceil(x + half))):
            if abs(xx + .5 - x) <= half:
                edge = (xx + .5 - x) / max(half, 0.5)
                k = "dW4" if edge < -0.35 else "dW2" if edge > 0.45 else "dW3"
                if t > 0.72:
                    k = "dW5" if edge < 0.2 else "dW4"
                put(water, xx, y, col(k))
    # foam cap + a pale lit edge on the upper-left of the tongue
    tx, ty = tip
    if fall < 0.5:
        put(foam, tx, ty, col("dW7"))
        put(foam, tx - (1 if lean <= 0 else 0), ty + 1, col("dW6"))
        put(foam, tx + (1 if lean > 0 else 0), ty + 1, col("dW6"))
    else:
        by = ty - 1 + fall * 3
        put(foam, tx + lean * 2, by, col("dW7"))
        put(foam, tx + lean * 2, by + 1, col("dW5"))


def frame(i):
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    foam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hgt, spread, pool, dt, rip = FR[i]
    fall = 0.0 if i < 3 else (i - 2) / 3.0
    # pool: a low dark lens on the floor with a foam lip
    for x in range(int(CX - pool), int(CX + pool) + 1):
        d = abs(x + .5 - CX) / pool
        top = FL - (2.2 * (1 - d * d) if i < 5 else 0.6 * (1 - d * d))
        for y in range(int(math.floor(top)), FL + 1):
            put(water, x, y, col("dW2" if y > top + 1 else "dW3"))
        if d > 0.25 and (x + i) % 3 != 0:
            put(foam, x, math.floor(top), col("dW6" if d > 0.6 else "dW5"))
    # the crown: two flaring water walls rising from the pool, a darker back sheet between them,
    # tongues breaking off the rim with pale foam tips
    if hgt > 1.5:
        hb = hgt * 0.42
        for x in range(int(CX - 7 * spread), int(CX + 7 * spread) + 1):
            d = abs(x + .5 - CX) / (7 * spread)
            top = FL - hb * (0.55 + 0.45 * d * d)
            for y in range(int(math.floor(top)), FL):
                put(water, x, y, col("dW2" if y > top + 0.8 else "dW4"))
        for side in (-1, 1):
            xb, xt = CX + side * 4.2 * spread, CX + side * 9.0 * spread
            n = int(hgt * 2) + 2
            rim = None
            for i2 in range(n + 1):
                t = i2 / n
                x = xb + (xt - xb) * (t ** 1.4)
                y = FL - t * hgt
                half = 2.0 * (1 - t) + 0.9
                for xx in range(int(math.floor(x - half)), int(math.ceil(x + half))):
                    if abs(xx + .5 - x) <= half:
                        e = (xx + .5 - x) * side / max(half, 0.5)       # + = outer face
                        k = "dW5" if (e < -0.3 and side < 0) or (e > 0.3 and side < 0) and t > 0.5 else \
                            "dW3" if e > 0.3 else "dW4"
                        put(water, xx, y, col(k))
                rim = (x, y)
            # tongues off the rim
            for j, (ang, ln) in enumerate(((-100 + side * 25, 3.2), (-100 + side * 60, 2.6), (-95 + side * 5, 2.0))):
                if hgt < 6 and j > 0:
                    continue
                L = ln * (0.6 + 0.4 * min(1.0, hgt / 14)) * (1 - 0.5 * fall)
                a = math.radians(ang + side * fall * 30)
                p0 = rim
                for m in range(int(L * 2) + 1):
                    q = (p0[0] + math.cos(a) * m * 0.5, p0[1] + math.sin(a) * m * 0.5 + fall * m * 0.3)
                    put(water, q[0], q[1], col("dW5"))
                tip = (p0[0] + math.cos(a) * L, p0[1] + math.sin(a) * L + fall * L * 0.6)
                put(foam, tip[0], tip[1], col("dW7"))
                put(foam, tip[0], tip[1] + 1, col("dW6"))
            # foam along the rim top
            put(foam, rim[0], rim[1], col("dW7"))
            put(foam, rim[0] - side, rim[1] + 1, col("dW6"))
    # central jet rising out of the collapsing crown
    jet = (0, 0, 5, 11, 7, 0)[i]
    if jet:
        for y in range(FL - jet, FL - 2):
            t = (FL - y) / jet
            w = 1 if t > 0.6 else 2
            for xx in range(int(CX) - (w - 1), int(CX) + 1):
                put(water, xx, y, col("dW4" if xx < CX - 0.5 else "dW3"))
        bead = FL - jet - (2 if i == 4 else 0)
        put(foam, CX - 0.5, bead - 1, col("dW7"))
        put(foam, CX - 0.5, bead, col("dW6"))
    # droplets on ballistic arcs (rise then fall)
    for k in range(12):
        a = math.radians(-90 + (hash01(k, 1, 9) * 2 - 1) * 62)
        v = 17 + 12 * hash01(k, 2, 9)
        t = dt * (0.75 + 0.5 * hash01(k, 3, 9))
        x = CX + math.cos(a) * v * t * 1.1
        y = FL - 3 + math.sin(a) * v * t + 34 * t * t
        if y < FL - 1:
            put(foam, x, y, col("dW7" if k % 3 == 0 else "dW6"))
            if k % 2 == 0 and i < 4:
                put(foam, x, y + 1, col("dW4"))
    # fine spray (alpha steps) around the crown at its peak
    if 1 <= i <= 3:
        for k in range(16):
            x = CX + (hash01(k, i, 21) * 2 - 1) * 12 * spread
            y = FL - hgt * (0.6 + 0.5 * hash01(k, i, 22))
            put(foam, x, y, col("dW6", 150 if k % 2 else 90), over=False)
    # ripples spreading after the fall
    if rip > 0:
        for sgn in (-1, 1):
            for j in range(3):
                x = CX + sgn * (rip + j * 1.0 + 4)
                put(foam, x, FL, col("dW5" if j == 0 else "dW4"))
            put(foam, CX + sgn * (rip + 2), FL - 1, col("dW6", 200 if i < 5 else 120))
    return {"Water": water, "Foam": foam}


def build_splash(build_ase):
    frames = [{"ms": MS[i], "cels": frame(i)} for i in range(6)]
    if build_ase:
        B.K.asebuild.build("fx_db_splash", W, H, ["Water", "Foam"], frames, [("fx_db_splash", 0, 5)])
    preview(frames)
    return None


def preview(frames, scale=4):
    rows = [((86, 86, 94, 255), (74, 74, 82, 255)), ((86, 86, 94, 255), (14, 14, 20, 255))]
    sheet = Image.new("RGBA", ((len(frames) * (W + 2) + 2) * scale, (len(rows) * (H + 2) + 12) * scale),
                      (86, 86, 94, 255))
    d = ImageDraw.Draw(sheet)
    d.text((4, 4), f"fx_db_splash  6f  ms {MS}  pivot bottom-centre  (grey cell / dark cell)",
           fill=(240, 240, 245, 255))
    for r, (_, cellc) in enumerate(rows):
        for i, f in enumerate(frames):
            cell = Image.new("RGBA", (W, H), cellc)
            cell.alpha_composite(f["cels"]["Water"])
            cell.alpha_composite(f["cels"]["Foam"])
            dd = ImageDraw.Draw(cell)
            sheet.alpha_composite(cell.resize((W * scale, H * scale), Image.NEAREST),
                                  ((2 + i * (W + 2)) * scale, (12 + r * (H + 2)) * scale))
    os.makedirs(os.path.join(K.ART, "previews"), exist_ok=True)
    sheet.save(os.path.join(K.ART, "previews", "fx_db_splash.png"))
