#!/usr/bin/env python3
"""Thornveil Wood FX (agent T). Tag = name without the fx_ prefix.

  fx_tv_rootspike  32x72  9  bottom pivot: green crack -> a gnarled thorned root erupts -> holds -> crumbles (active 3..5)
  fx_tv_thorn      16x8   2  loop, travelling RIGHT: a dark thorn dart with a spirit-lit tip
  fx_tv_spore      12x12  4  loop: a drifting spore puff
  fx_tv_cloud      48x40  8  bottom pivot: a spore cloud bursting open and thinning
  fx_tv_wall       32x64  12 bottom pivot: summoned thorn wall -- rise(0..4) idle(5..6) wither(7..11) as separate tags
  fx_tv_orb        16x16  4  loop: a falling mote of spirit-light (the phase-2 storm)
  fx_tv_burst      64x48  7  centred: a flare of spirit-light and leaves (teleports, phase change)
"""
import math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
from thornveil_kit import (BARK, MOSS, SPIRIT, THORN, RIBBON, K, C, Pix, h01, curve_pts, stroke, outline, strip, save_prev)  # noqa: E402
from PIL import Image  # noqa: E402

BUILD = "--preview" not in sys.argv


def rootspike(f):
    P = Pix(32, 72)
    FLr = 71
    h = [0, 0, 12, 50, 64, 64, 60, 36, 12][f]
    if f <= 2:   # glowing crack in the ground
        w = 6 + f * 4
        for x in range(16 - w, 16 + w):
            if h01(x, f, 3) < 0.7:
                P.set(x, FLr, SPIRIT[2 + (1 if abs(x - 16) < w / 2 else 0)])
        P.set(16, FLr - 1, SPIRIT[4]); P.set(15, FLr - 1, SPIRIT[3])
    if h > 0:
        base_w = 5.5 if f < 7 else 4.0
        pts = [(16, FLr + 2), (14.5, FLr - h * 0.35), (17.5, FLr - h * 0.7), (16, FLr - h)]
        stroke(P, pts, base_w, 0.6, lambda t, lit: BARK[5] if lit > 0.35 else BARK[4] if lit > 0 else BARK[3] if lit > -0.4 else BARK[2])
        cp = curve_pts(pts, 10)
        for i in range(4, len(cp) - 3, 5):         # thorn barbs
            x, y = cp[i]
            t = i / len(cp)
            s = 1 if (i // 5) % 2 else -1
            r = base_w * (1 - t) + 0.6
            P.set(x + s * (r + 1), y - 1, THORN[4]); P.set(x + s * (r + 2), y - 2, THORN[5])
        for i in range(2, len(cp), 9):             # green-lit veins
            x, y = cp[i]
            P.set(x, y, SPIRIT[3] if f in (3, 4) else SPIRIT[2])
        x, y = cp[-1]
        P.set(x, y - 1, THORN[5])
        # clods of soil thrown up at the eruption
        if f in (3, 4):
            for k in range(8):
                a = -math.pi * (0.1 + 0.8 * h01(k, f, 5))
                r = 6 + 6 * h01(k, f, 6) + (f - 3) * 4
                P.set(16 + math.cos(a) * r * 1.4, FLr - 2 + math.sin(a) * r, BARK[1] if k % 2 else MOSS[3])
    img = outline(P.img, K)
    return img


def thorn(f):
    P = Pix(16, 8)
    for x in range(2, 13):
        w = 1 if x > 9 else 2 if x > 4 else 1
        for y in range(4 - w // 2 - (1 if w == 2 else 0), 4 + w // 2 + 1):
            P.set(x, y, BARK[4] if y < 4 else BARK[2])
    P.set(13, 4, SPIRIT[4]); P.set(14, 4, SPIRIT[5 if f else 4]); P.set(12, 3, SPIRIT[3])
    P.set(0 + f, 3, SPIRIT[2]); P.set(1, 5 - f, SPIRIT[1])
    return outline(P.img, K)


def spore(f):
    P = Pix(12, 12)
    r = 3.2 + 0.5 * math.sin(f * 1.57)
    P.disc(6, 6, r, SPIRIT[2]); P.disc(5.5, 5.5, r * 0.6, SPIRIT[3]); P.set(5, 5, SPIRIT[5])
    for k in range(4):
        a = k * 1.57 + f * 0.6
        P.set(6 + math.cos(a) * (r + 1.5), 6 + math.sin(a) * (r + 1.5), SPIRIT[3] if k % 2 else MOSS[5])
    return P.img


def cloud(f):
    img = Image.new("RGBA", (48, 40), (0, 0, 0, 0))
    px = img.load()
    k = f / 7
    R = 8 + 14 * min(1, k * 2.2)
    fade = max(0, 1 - max(0, k - 0.35) * 1.5)
    for y in range(40):
        for x in range(48):
            dx, dy = (x + .5 - 24) / R, (y + .5 - (39 - R * 0.7)) / (R * 0.75)
            q = dx * dx + dy * dy
            n = h01(x // 2, y // 2, f) * 0.35
            if q + n < 1.0 and (q + n > 0.25 * (1 - fade) or f < 3):
                c = SPIRIT[3] if q < 0.3 and f < 3 else SPIRIT[2] if q < 0.55 else MOSS[4] if q < 0.8 else MOSS[3]
                if fade < 1 and h01(x, y, f + 9) > fade:
                    continue
                px[x, y] = c
    return img


def wall(state, f):
    P = Pix(32, 64)
    FLw = 63
    hmax = 58
    if state == "rise":
        h = hmax * [0.15, 0.45, 0.8, 1.05, 1.0][f]
    elif state == "idle":
        h = hmax
    else:
        h = hmax * [0.95, 0.8, 0.6, 0.35, 0.12][f]
    for k, (x0, lean, hk) in enumerate(((10, -0.12, 0.85), (16, 0.04, 1.0), (22, 0.14, 0.9), (13, 0.25, 0.7), (19, -0.25, 0.75))):
        hh = h * hk
        if hh < 3:
            continue
        pts = [(x0, FLw + 2), (x0 + lean * hh * 0.4 + (1 if k % 2 else -1), FLw - hh * 0.5), (x0 + lean * hh, FLw - hh)]
        col = (lambda t, lit: THORN[4] if lit > 0.3 else THORN[3] if lit > -0.2 else THORN[2]) if state != "wither" else \
              (lambda t, lit: BARK[3] if lit > 0 else BARK[2])
        stroke(P, pts, 2.2 if k < 3 else 1.6, 0.5, col)
        cp = curve_pts(pts, 8)
        for i in range(3, len(cp) - 1, 4):
            x, y = cp[i]
            s = 1 if (i // 4 + k) % 2 else -1
            P.set(x + s * 3, y - 1, THORN[4]); P.set(x + s * 4, y - 2, THORN[5] if state != "wither" else BARK[4])
        if state == "idle":
            x, y = cp[len(cp) // 2]
            P.set(x, y, SPIRIT[3] if (f + k) % 2 else SPIRIT[2])
    if state == "rise" and f < 3:
        for x in range(6, 26):
            if h01(x, f, 2) < 0.6:
                P.set(x, FLw, SPIRIT[3])
    img = outline(P.img, K)
    if state == "wither" and f >= 2:
        px = img.load()
        for y in range(64):
            for x in range(32):
                if px[x, y][3] and h01(x, y, f) < 0.15 * f:
                    px[x, y] = (0, 0, 0, 0)
    return img


def orb(f):
    P = Pix(16, 16)
    P.disc(8, 8, 3.2, SPIRIT[3]); P.disc(7.6, 7.6, 2.0, SPIRIT[4]); P.set(7, 7, SPIRIT[5])
    for k in range(3):
        P.set(8 + math.cos(f * 1.57 + k * 2.1) * 5.2, 8 + math.sin(f * 1.57 + k * 2.1) * 5.2, SPIRIT[3])
    for y in range(0, 4):
        P.set(8, y, SPIRIT[2] if y % 2 else SPIRIT[1])
    return P.img


def burst(f):
    P = Pix(64, 48)
    k = f / 6
    r = 4 + 20 * k
    for i in range(28):
        a = i / 28 * 2 * math.pi + h01(i, 1, 2) * 0.3
        rr = r * (0.7 + 0.3 * h01(i, f, 3))
        x, y = 32 + math.cos(a) * rr * 1.2, 24 + math.sin(a) * rr * 0.8
        c = SPIRIT[5] if k < 0.3 else SPIRIT[4] if k < 0.55 else SPIRIT[3] if k < 0.8 else SPIRIT[2]
        P.set(x, y, c)
        if i % 4 == 0:
            P.set(x + 1, y, MOSS[5] if f > 2 else c)
    if f < 3:
        P.disc(32, 24, 5 - f * 1.5, SPIRIT[4]); P.disc(32, 24, 2.5 - f, SPIRIT[5])
    return P.img


def pillar(part, v=0):
    """A segment of a great root pillar (vertical, tileable top-to-bottom), or its thorned tip. 24x32."""
    P = Pix(24, 32)
    for y in range(32):
        taper = 1.0 if part == "seg" else max(0.0, (y - 2) / 30)
        w = (7.5 + 1.2 * math.sin(y / 32 * 2 * math.pi * 2 + v)) * taper
        cx = 12 + 1.5 * math.sin(y / 32 * 2 * math.pi + v * 1.3)
        for x in range(24):
            d = (x + 0.5 - cx) / max(w, 0.1)
            if abs(d) <= 1:
                twist = math.sin((y * 0.55 + x * 0.9) + v)
                lv = 0.72 - 0.55 * (d + 1) / 2 + 0.12 * twist
                c = BARK[max(1, min(5, int(lv * 6)))]
                if abs(d) > 0.86:
                    c = BARK[1]
                P.set(x, y, c)
        if (y + v * 5) % 8 == 3 and w > 2:                 # thorn barbs
            sd = 1 if (y // 8) % 2 else -1
            P.set(cx + sd * (w + 1), y - 1, THORN[4]); P.set(cx + sd * (w + 2), y - 2, THORN[5])
        if (y + v * 3) % 11 == 5 and w > 2:                # veins of spirit-light
            P.set(cx - 1, y, SPIRIT[3]); P.set(cx, y, SPIRIT[2])
    if part == "tip":
        P.set(12, 1, THORN[5]); P.set(12, 2, THORN[4])
    return outline(P.img, K)


def main():
    items = {
        "fx_tv_rootspike": (32, 72, [rootspike(f) for f in range(9)], [("tv_rootspike", 0, 8)], [90, 90, 110, 60, 70, 110, 110, 80, 80]),
        "fx_tv_thorn": (16, 8, [thorn(f) for f in range(2)], [("tv_thorn", 0, 1)], [80, 80]),
        "fx_tv_spore": (12, 12, [spore(f) for f in range(4)], [("tv_spore", 0, 3)], [110] * 4),
        "fx_tv_cloud": (48, 40, [cloud(f) for f in range(8)], [("tv_cloud", 0, 7)], [70, 80, 110, 150, 200, 260, 300, 300]),
        "fx_tv_wall": (32, 64, [wall("rise", f) for f in range(5)] + [wall("idle", f) for f in range(2)] + [wall("wither", f) for f in range(5)],
                       [("rise", 0, 4), ("idle", 5, 6), ("wither", 7, 11)], [60, 60, 70, 90, 100, 200, 200, 110, 110, 110, 120, 140]),
        "fx_tv_orb": (16, 16, [orb(f) for f in range(4)], [("tv_orb", 0, 3)], [90] * 4),
        "fx_tv_burst": (64, 48, [burst(f) for f in range(7)], [("tv_burst", 0, 6)], [50, 60, 70, 80, 90, 100, 110]),
        "fx_tv_pillar": (24, 32, [pillar("seg", 0), pillar("seg", 1), pillar("tip", 0)], [("seg", 0, 1), ("tip", 2, 2)], [100, 100, 100]),
    }
    rows = []
    for nm, (w, h, frames, tags, ms) in items.items():
        if BUILD:
            asebuild.build(nm, w, h, ["FX"], [{"ms": m, "cels": {"FX": f}} for m, f in zip(ms, frames)], tags)
        rows.append(strip(frames))
    Wd = max(r.size[0] for r in rows); Hd = sum(r.size[1] + 4 for r in rows)
    sh = Image.new("RGBA", (Wd, Hd), (70, 70, 76, 255))
    y = 0
    for r in rows:
        sh.alpha_composite(r, (0, y)); y += r.size[1] + 4
    save_prev(sh, "fx_thornveil.png", k=3)
    print("fx ok")


if __name__ == "__main__":
    main()
