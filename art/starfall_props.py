"""Starfall Crater props (agent SF): floating shards, observatory ruins, fallen-god bones, crystal spires, the fallen
star's cairn (X4) and its shard stair. Every function returns [(tag, [(ms, img), ...]), ...] for one sheet."""
import math
from PIL import Image
from envlib import C, ramp, K, T, h01, clamp, blank, outline, pick, bt

OB = ramp("05050b", "0a0b16", "11132a", "191d3c", "232a52", "303a6a", "44518a", "6476b4", "9aaee4")
GL = ramp("0a1030", "142050", "1f3274", "2e4a9c", "4a6cc4", "7a9ae6", "b8ccff", "eef4ff")
STONE = ramp("16171f", "23242f", "33353f", "484a55", "60636e", "7c808a", "9ca0a8", "c2c4c8")
BRASS = ramp("1e140c", "3a2614", "5e3e1a", "8a6024", "b48434", "d8aa4c", "f4d27e")
BONE = ramp("15141b", "24222c", "37343f", "4d4955", "67626c", "827c84", "a39ca2")
STAR = [C("1c2c66"), C("3e5cc0"), C("7c9cf0"), C("c4d6ff"), C("ffffff")]


def put(img, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((x, y), c)


def poly_pts(pts):
    ys = [p[1] for p in pts]
    res = set()
    n = len(pts)
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1):
        cy = y + 0.5
        xi = []
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xi.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xi.sort()
        for a, b in zip(xi[::2], xi[1::2]):
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                res.add((x, y))
    return res


def facet(img, pts, rp, lit, seed=0):
    """fill a flat facet with a dithered level from the ramp; lit in 0..1"""
    for (x, y) in poly_pts(pts):
        v = clamp(lit + 0.06 * (h01(x, y, seed) - 0.5), 0, 1)
        put(img, x, y, pick(rp, v, x, y))


def glint_line(img, a, b, c):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        t = i / n
        put(img, round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), c)


def star(img, x, y, big=False):
    put(img, x, y, STAR[4])
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(img, x + dx, y + dy, STAR[3] if big else STAR[2])
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            put(img, x + dx, y + dy, STAR[1])


def shard_body(img, cx, top, w, h, rp=OB, seed=0, glow=0.0):
    """a jagged obsidian shard pointing down: three facets (lit left, mid front, dark right)"""
    L, R = cx - w / 2, cx + w / 2
    tip = (cx + w * 0.08, top + h)
    crown = [(L, top + h * 0.12), (cx - w * 0.2, top), (cx + w * 0.15, top + h * 0.05), (R, top + h * 0.18)]
    mid = (cx - w * 0.05, top + h * 0.3)
    facet(img, [crown[0], crown[1], mid, tip], rp, 0.7, seed)
    facet(img, [crown[1], crown[2], crown[3], mid], rp, 0.85, seed + 1)
    facet(img, [mid, crown[3], tip], rp, 0.35, seed + 2)
    glint_line(img, crown[1], mid, rp[-1])
    glint_line(img, mid, tip, rp[-2])
    if glow:
        for i in range(int(h * 0.5)):
            t = i / max(1, h * 0.5)
            put(img, cx - w * 0.1 + math.sin(t * 5 + seed) * 1.2, top + h * 0.25 + i, STAR[2] if i % 3 else STAR[3])


def shard_prop():
    frames = []
    for f in range(6):
        img = blank(32, 32)
        shard_body(img, 16, 3, 16, 26, seed=3, glow=1)
        shard_body(img, 7, 12, 6, 11, seed=5)
        shard_body(img, 26, 14, 5, 9, seed=6)
        img = outline(img)
        gy = 5 + f * 4                                  # a glint sliding down the lit edge
        if gy < 26:
            put(img, 12 + (gy - 5) * 0.12, gy, STAR[4]); put(img, 13 + (gy - 5) * 0.12, gy, STAR[3])
        frames.append((140, img))
    return [("loop", frames)]


def arch_prop():
    img = blank(48, 80)
    # a pillar of pale observatory stone, fluted, cracked; an arch springing from it and breaking off
    for y in range(18, 80):
        for x in range(8, 20):
            fl = (x - 8) % 4
            v = 0.62 - 0.16 * (x - 8) / 12 + (0.08 if fl == 1 else -0.06 if fl == 3 else 0)
            put(img, x, y, pick(STONE, v, x, y))
    for x in range(5, 23):                                # capital + base
        for y in (16, 17, 18):
            put(img, x, y, STONE[6] if y == 16 else STONE[4])
        for y in (76, 77, 78, 79):
            put(img, x, y, STONE[5] if y == 76 else STONE[3])
    for i in range(60):                                   # the arch
        t = i / 59
        a = math.pi * (1 - t * 0.62)
        cx, cy, r = 34, 34, 21
        for w in range(6):
            x, y = cx + math.cos(a) * (r + w), cy - math.sin(a) * (r + w)
            put(img, x, y, STONE[6 - w // 2] if w < 3 else STONE[3])
    for (x, y) in ((12, 30), (13, 31), (13, 32), (14, 33), (12, 50), (11, 51), (12, 52)):
        put(img, x, y, STONE[1])
    for y in range(24, 70, 7):                            # starlight in the cracks
        put(img, 16, y, STAR[2])
    img = outline(img)
    return [("idle", [(1000, img)])]


def godbone_prop():
    img = blank(96, 56)
    # a colossal vertebra and two ribs of a dead god, half-sunk in the glass
    for r, (x0, h, lean) in enumerate(((20, 44, 0.35), (44, 50, 0.22), (70, 38, 0.1))):
        for i in range(h):
            t = i / h
            x = x0 + math.sin(t * math.pi * 0.9) * 14 * (1 if r < 2 else -1) * lean * 2
            y = 55 - i
            w = 6.5 - 5.0 * t
            for dx in range(int(-w), int(w) + 1):
                v = 0.7 - 0.3 * (dx + w) / (2 * w + 1) - 0.1 * t
                put(img, x + dx, y, pick(BONE, v, x + dx, y))
    for y in range(40, 56):                               # the vertebra
        for x in range(30, 62):
            if ((x - 46) / 16) ** 2 + ((y - 50) / 10) ** 2 <= 1:
                put(img, x, y, pick(BONE, 0.55 - (x - 30) / 64 + (0.15 if y < 44 else 0), x, y))
    for x in range(40, 52):
        for y in range(46, 50):
            put(img, x, y, BONE[0])
    for (x, y) in ((22, 20), (45, 12), (71, 24)):
        star(img, x, y)
    img = outline(img)
    for x in range(96):                                   # sunk in glass
        for y in (53, 54, 55):
            if img.getpixel((x, y))[3]:
                put(img, x, y, OB[3] if y > 53 else OB[6])
    return [("idle", [(1000, img)])]


def spire_prop():
    frames = []
    for f in range(4):
        img = blank(32, 40)
        for (cx, h, w, lean, s) in ((10, 26, 4, -0.18, 1), (17, 36, 5, 0.06, 2), (24, 20, 4, 0.22, 3), (6, 12, 3, -0.3, 4)):
            top = 40 - h
            L = [(cx - w, 40), (cx - w * 0.4 + lean * h, top + 2), (cx + lean * h, top), (cx + w * 0.4 + lean * h, top + 3), (cx + w, 40)]
            facet(img, [L[0], L[1], L[2], (cx + lean * h * 0.5, 40)], GL, 0.72, s)
            facet(img, [(cx + lean * h * 0.5, 40), L[2], L[3], L[4]], GL, 0.38, s + 7)
            glint_line(img, L[2], (cx + lean * h * 0.5, 38), GL[6])
            core = 0.5 + 0.5 * math.sin(f * math.pi / 2 + s)
            for i in range(int(h * 0.3), int(h * 0.7)):
                put(img, cx + lean * (h - i) * 0.9, 40 - i, STAR[1 + int(core * 2)])
        img = outline(img)
        frames.append((180, img))
    return [("loop", frames)]


def idol_prop():
    img = blank(48, 48)
    # the broken head of an old god: serene, eyes closed, its halo snapped, half-sunk
    cx, cy = 24, 26
    for y in range(6, 48):
        for x in range(6, 42):
            d = ((x - cx) / 15) ** 2 + ((y - cy) / 19) ** 2
            if d <= 1 and not (x > 30 and y < 14 + (x - 30)):      # a chunk broken off the crown
                nx = (x - cx) / 15
                v = 0.55 - 0.35 * nx - 0.12 * (y - cy) / 19
                put(img, x, y, pick(STONE, v, x, y))
    for x in range(16, 22):
        put(img, x, 24, STONE[1]); put(img, x + 11, 24, STONE[1])     # closed eyes
    for y in range(26, 33):
        put(img, 24, y, STONE[2])                                      # nose ridge
    for x in range(21, 28):
        put(img, x, 36, STONE[1])                                      # mouth
    for i in range(30):                                                # the snapped halo behind
        a = math.pi * (0.1 + i / 29 * 0.8)
        put(img, cx + math.cos(a) * 22, cy - 4 - math.sin(a) * 22, BRASS[4] if i % 5 else BRASS[6])
    for (x, y) in ((18, 12), (19, 13), (19, 14), (20, 15), (33, 30), (32, 31)):
        put(img, x, y, STAR[2])
    img = outline(img)
    for x in range(48):
        for y in range(43, 48):
            if img.getpixel((x, y))[3]:
                put(img, x, y, OB[3] if y > 44 else OB[6])
    return [("idle", [(1000, img)])]


def telescope_prop():
    img = blank(64, 64)
    # tripod mount
    for (x0, x1) in ((20, 10), (24, 26), (28, 42)):
        glint_line(img, (x0 + 4, 40), (x1, 63), BRASS[3])
        glint_line(img, (x0 + 5, 40), (x1 + 1, 63), BRASS[1])
    for y in range(36, 44):
        for x in range(22, 32):
            put(img, x, y, BRASS[5] if y < 38 else BRASS[3])
    # the great tube, tilted toward the sky, its lens cracked
    ang = math.radians(-32)
    ca, sa = math.cos(ang), math.sin(ang)
    for u in range(-14, 34):
        r = 4.5 if u > 26 else 3.6 if u > -6 else 3.0
        for v in range(int(-r), int(r) + 1):
            x, y = 27 + ca * u - sa * v, 38 + sa * u + ca * v
            lv = 0.75 - 0.5 * (v + r) / (2 * r + 1)
            if u % 9 == 0:
                lv += 0.15
            put(img, x, y, BRASS[int(clamp(lv, 0, 0.99) * len(BRASS))])
    lx, ly = 27 + ca * 34, 38 + sa * 34
    for v in range(-4, 5):
        put(img, lx - sa * v, ly + ca * v, GL[5] if v < 0 else GL[3])
    put(img, lx, ly - 1, STAR[4])
    img = outline(img)
    return [("idle", [(1000, img)])]


def lens_prop():
    frames = []
    for f in range(4):
        img = blank(24, 40)
        for y in range(18, 40):
            put(img, 11, y, BRASS[4]); put(img, 12, y, BRASS[2])
        for x in range(6, 18):
            put(img, x, 38, BRASS[3]); put(img, x, 39, BRASS[1])
        for a in range(40):                              # the ring
            t = a / 40 * 2 * math.pi
            put(img, 12 + math.cos(t) * 7, 11 + math.sin(t) * 7, BRASS[5] if math.sin(t) < 0 else BRASS[3])
        for y in range(5, 18):
            for x in range(6, 19):
                if (x - 12) ** 2 + (y - 11) ** 2 <= 30:
                    v = 0.4 + 0.3 * math.sin(f * math.pi / 2 + (x + y) * 0.3)
                    put(img, x, y, pick(GL, v, x, y))
        star(img, 12, 11, big=f % 2 == 0)
        img = outline(img)
        frames.append((160, img))
    return [("loop", frames)]


def orrering_prop():
    frames = []
    for f in range(8):
        img = blank(48, 48)
        cx, cy = 24, 26
        for (r, tilt, spin, col) in ((18, 0.35, 0, BRASS), (14, 0.9, f * math.pi / 8, BRASS)):
            for i in range(90):
                a = i / 90 * 2 * math.pi
                x, y, z = math.cos(a) * r, math.sin(a) * r, 0
                # rotate about x (tilt) then about y (spin)
                y2, z2 = y * math.cos(tilt), y * math.sin(tilt)
                x3, z3 = x * math.cos(spin) + z2 * math.sin(spin), -x * math.sin(spin) + z2 * math.cos(spin)
                put(img, cx + x3, cy + y2, col[5] if z3 < 0 else col[3])
        put(img, cx, cy, STAR[3]); put(img, cx + 1, cy, STAR[2])
        # broken: a chunk missing, one end sunk in the glass
        for y in range(40, 48):
            for x in range(10, 38):
                if img.getpixel((x, y))[3]:
                    put(img, x, y, OB[4])
        img = outline(img)
        frames.append((200, img))
    return [("loop", frames)]


def cairn_prop():
    def crust(img, openk=0.0, f=0):
        # a low dome of black glass with light leaking through cracks; openk 0..1 splits it apart
        cx, base = 24, 31
        for y in range(14, 32):
            for x in range(2, 46):
                d = ((x - cx) / 20) ** 2 + ((y - base) / 16) ** 2
                if d > 1:
                    continue
                if openk > 0 and abs(x - cx) < 2 + openk * 7 and y < base - 1:
                    continue
                v = 0.55 - 0.4 * (x - cx) / 20 - 0.25 * (y - 14) / 18
                put(img, x + (-openk * 6 if x < cx else openk * 6), y + openk * 2, pick(OB, v, x, y))
        return img

    def glow_cracks(img, k, f):
        pts = [(24, 18), (20, 22), (17, 27), (28, 21), (31, 26), (24, 25), (13, 29), (35, 29)]
        for i in range(len(pts) - 1):
            if i in (2, 4):
                continue
            glint_line(img, pts[i], pts[i + 1], STAR[1 + min(3, int(k * 3 + (f + i) % 2))])
    anims = []
    idle = []
    for f in range(4):
        img = crust(blank(48, 32))
        img = outline(img)
        glow_cracks(img, 0.3 + 0.25 * math.sin(f * math.pi / 2), f)
        idle.append((220, img))
    anims.append(("idle", idle))
    crack = []
    for f in range(6):
        k = f / 5
        img = blank(48, 32)
        if f >= 2:                                        # the star itself shows through
            for y in range(18, 31):
                for x in range(16, 33):
                    if (x - 24) ** 2 + ((y - 26) * 1.4) ** 2 <= 30 * k:
                        put(img, x, y, STAR[3] if (x - 24) ** 2 + ((y - 26) * 1.4) ** 2 < 10 else STAR[2])
        img2 = crust(blank(48, 32), openk=max(0, k - 0.2))
        img.alpha_composite(outline(img2))
        glow_cracks(img, 0.6 + k, f)
        for i in range(int(8 * k)):
            put(img, 24 + h01(i, f, 3) * 30 - 15, 18 - h01(i, f, 4) * 16 * k, STAR[3])
        crack.append((90 if f < 5 else 160, img))
    anims.append(("crack", crack))
    op = []
    for f in range(4):
        img = blank(48, 32)
        for y in range(16, 31):
            for x in range(14, 35):
                d = (x - 24) ** 2 + ((y - 25) * 1.3) ** 2
                if d <= 60:
                    put(img, x, y, STAR[4] if d < 8 + f % 2 * 4 else STAR[3] if d < 26 else STAR[2])
        img2 = crust(blank(48, 32), openk=0.8)
        img.alpha_composite(outline(img2))
        op.append((180, img))
    anims.append(("open", op))
    return anims


def stair_prop():
    frames = []
    for f in range(4):
        img = blank(48, 16)
        for x in range(1, 47):
            t = abs(x - 24) / 24
            keel = int(2 + (1 - t) * 9 * (0.6 + 0.4 * h01(x // 3, 1, 5)))
            for y in range(0, keel):
                put(img, x, y, GL[6] if y == 0 else OB[5] if y == 1 else OB[3] if y < keel - 2 else OB[2])
        img = outline(img)
        gx = 6 + f * 11
        put(img, gx, 1, STAR[4]); put(img, gx + 1, 1, STAR[3])
        for x in (12, 30):
            put(img, x, 4, STAR[1])
        frames.append((150, img))
    return [("loop", frames)]


PROPS = {
    "sf_shard": (32, 32, shard_prop), "sf_arch": (48, 80, arch_prop), "sf_godbone": (96, 56, godbone_prop),
    "sf_spire": (32, 40, spire_prop), "sf_idol": (48, 48, idol_prop), "sf_telescope": (64, 64, telescope_prop),
    "sf_lens": (24, 40, lens_prop), "sf_orrering": (48, 48, orrering_prop), "sf_cairn": (48, 32, cairn_prop),
    "sf_stair": (48, 16, stair_prop),
}
