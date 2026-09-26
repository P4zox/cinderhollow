#!/usr/bin/env python3
"""FX for The Crimson Manor (agent C).

    fx_cm_lance   24x72  6 frames, pivot bottom: a spike of solidified blood erupts from the floor, shines, bursts back to liquid
    fx_cm_bat     12x8   4 frames loop, centred: a small bat (swarms / teleports)
    fx_cm_thrust  32x16  4 frames, centred, travels right: rapier thrust spark
    fx_cm_slash   64x48  4 frames, centred, faces right: the Butler's silver crescent cut, crimson edged
Previews: art/previews/fx_crimson.png
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

BUILD = "--preview" not in sys.argv
C = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
K = C("#08070c")
Z = [C(h) for h in ("#2e040c", "#5c0816", "#920f22", "#c82032", "#f0505a", "#ffb0a8", "#fff0e6")]
U = [C(h) for h in ("#2c2b36", "#7c7b8c", "#b0afc0", "#e8e8f2", "#ffffff")]
X = [C(h) for h in ("#070508", "#1c141e", "#3e3042")]


def h01(x, y, k=0):
    n = (x * 374761393 + y * 668265263 + k * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def outline(img):
    w, h = img.size
    src = img.load()
    out = img.copy()
    o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X_, Y_ = x + dx, y + dy
                if 0 <= X_ < w and 0 <= Y_ < h and src[X_, Y_][3] == 255 and src[X_, Y_] != K:
                    o[x, y] = K
                    break
    return out


def lance(fi):
    w, h = 24, 72
    img = Image.new("RGBA", (w, h))
    p = img.load()
    cx = 12
    hgt = [22, 60, 62, 60, 40, 0][fi]
    crack = fi >= 3
    for y in range(h - hgt, h):
        t = (h - 1 - y) / max(1, hgt)          # 0 base .. 1 tip
        half = 5.5 * (1 - t) ** 0.85 + 0.4
        for x in range(w):
            dx = x + 0.5 - cx
            if abs(dx) > half:
                continue
            u = dx / max(half, 0.6)
            lvl = 2 if u < -0.2 else 1 if u > 0.35 else 3
            if u < -0.55:
                lvl = 4 if t > 0.3 else 3
            if t > 0.88:
                lvl = 4
            if crack and h01(x, y, fi) < (0.12 if fi == 3 else 0.35):
                continue
            if fi == 2 and abs(y - (h - hgt + 18)) < 2 and u < 0.2:
                lvl = 6
            p[x, y] = Z[lvl]
    # facet line
    for y in range(h - hgt, h - 2):
        t = (h - 1 - y) / max(1, hgt)
        x = int(cx - 1 - 2.5 * (1 - t))
        if 0 <= x < w and p[x, y][3] and fi < 4:
            p[x, y] = Z[4]
    img = outline(img)
    p = img.load()
    # splash / droplets at the base
    n = [6, 10, 6, 8, 14, 10][fi]
    for i in range(n):
        a = h01(i, fi, 3) * math.pi
        r = 3 + 8 * h01(i, fi, 4) * (1 + fi * 0.2)
        x = int(cx + math.cos(a) * r * (1 if i % 2 else -1))
        y = int(h - 2 - abs(math.sin(a)) * r * (0.7 if fi < 4 else 1.2))
        if 0 <= x < w and 0 <= y < h:
            p[x, y] = Z[3 if i % 3 else 4]
    for x in range(max(0, cx - 7 - fi), min(w, cx + 8 + fi)):
        p[x, h - 1] = Z[1] if abs(x - cx) > 4 else Z[2]
    return img


def bat(fi):
    img = Image.new("RGBA", (12, 8))
    p = img.load()
    up = [0, 1, 2, 1][fi]
    body = [(6, 4), (5, 4), (6, 5), (5, 3)]
    wing_l = [(4, 4 - up), (3, 4 - up), (2, 5 - up), (1, 5 - up * 2 if up < 2 else 2), (3, 5 - up), (2, 4 - up)]
    wing_r = [(7, 4 - up), (8, 4 - up), (9, 5 - up), (10, 5 - up * 2 if up < 2 else 2), (8, 5 - up), (9, 4 - up)]
    for q in wing_l + wing_r:
        if 0 <= q[0] < 12 and 0 <= q[1] < 8:
            p[q] = X[1]
    for q in body:
        p[q] = X[0]
    p[6, 3] = X[2]
    p[7, 3] = Z[4]
    return img


def thrust(fi):
    img = Image.new("RGBA", (32, 16))
    p = img.load()
    L = [10, 22, 26, 18][fi]
    x0 = [10, 6, 8, 14][fi]
    for i in range(L):
        x = x0 + i
        if x >= 32:
            break
        t = i / L
        p[x, 8] = U[3] if t > 0.6 else Z[4]
        if t > 0.3 and i % 2 == 0:
            p[x, 7] = Z[3]
            p[x, 9] = Z[2]
    tip = min(31, x0 + L)
    if fi < 3:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0, 2), (0, -2)):
            if 0 <= tip - 1 + dx < 32:
                p[tip - 1 + dx, 8 + dy] = U[4] if (dx, dy) == (0, 0) else U[3]
    return img


def slash(fi):
    w, h = 64, 48
    img = Image.new("RGBA", (w, h))
    p = img.load()
    cx, cy = 18, 24
    a0, a1 = [(-80, -20), (-70, 50), (-40, 80), (10, 85)][fi]
    R = 26
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.15
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx))
            if a < a0 or a > a1:
                continue
            k = (a - a0) / max(1, a1 - a0)          # 0 old end .. 1 leading edge
            th = 1.5 + 5.5 * math.sin(k * math.pi) ** 0.8 * (1 - fi * 0.18)
            if R - th <= r <= R + 0.8:
                d = (R - r) / th
                col = U[3] if d < 0.2 else U[2] if d < 0.45 else Z[3] if d < 0.75 else Z[2]
                if fi == 3 and h01(x, y, 7) < 0.4:
                    continue
                p[x, y] = col
    return img


def build(name, w, h, frames, ms, tag):
    fr = [{"ms": m, "cels": {"fx": im}} for im, m in zip(frames, ms)]
    if BUILD:
        asebuild.build(name, w, h, ["fx"], fr, [(tag, 0, len(frames) - 1)])
    return frames


def main():
    rows = []
    rows.append(build("fx_cm_lance", 24, 72, [lance(i) for i in range(6)], [50, 60, 60, 60, 60, 70], "cm_lance"))
    rows.append(build("fx_cm_bat", 12, 8, [bat(i) for i in range(4)], [60] * 4, "cm_bat"))
    rows.append(build("fx_cm_thrust", 32, 16, [thrust(i) for i in range(4)], [40, 50, 50, 60], "cm_thrust"))
    rows.append(build("fx_cm_slash", 64, 48, [slash(i) for i in range(4)], [40, 50, 50, 70], "cm_slash"))
    sc = 4
    Wm = max(sum(im.size[0] + 2 for im in r) for r in rows)
    Hm = sum(max(im.size[1] for im in r) + 2 for r in rows)
    sheet = Image.new("RGBA", (Wm * sc, Hm * sc), (60, 58, 66, 255))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            sheet.alpha_composite(im.resize((im.size[0] * sc, im.size[1] * sc), Image.NEAREST), (x * sc, y * sc))
            x += im.size[0] + 2
        y += max(im.size[1] for im in r) + 2
    sheet.save(os.path.join(ART, "previews", "fx_crimson.png"))


if __name__ == "__main__":
    main()
