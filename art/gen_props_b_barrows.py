#!/usr/bin/env python3
"""Batch B: Drowned Barrows props, xsa_db (48x48, bottom-centre) and xsa_bell (64x80, hung top-centre), docs/v17/props_b.md.

Reworked tags (the old ones were flat teal fills): pew, pearlclam (4f), coral, tomb, tomb_leak, tidemark, sluice, gravestone,
gravecross, cairn, wellcover, and the Drowned Bell. Kept pixel-exact from v1: weeds, chainlamp, candles_db (acceptable).

Relief models lit by the cold light that comes down through the water (from above, a little left), palette-locked to the
barrows ramps (stone and verdigris sampled from tiles_barrows / db_statue / db_lamp), 08070c outline. Wet stone gets
algae in its hollows and on its ledges, barnacles near the floor; the pearl and the leak glow (unlit emissive).

Run: python3 art/gen_props_b_barrows.py [--only tag,tag] [--nobuild]
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props_b_lib import *   # noqa

STONEB = ramp('04090b', '070d10', '0a1215', '0e181b', '132024', '18282c', '1e2f33', '26393c', '2f4345', '3a5052', '4b6464', '63807c', '86a49c')
VERD = ramp('0d3431', '145a54', '1f8f85', '2fbfb0', '8ff0e0', 'd8fff4')
ALGAE = ramp('0a1412', '10201a', '18301f', '22402a', '2e5434', '46703f')
BONE = ramp('151e1b', '2c363a', '5c594b', '848070', 'a8a290', 'cfc8b2')
WOODB = ramp('0a0c0c', '121614', '1c201c', '262b24', '323829', '434a36', '586048')
BRONZE = ramp('0d1c16', '13271e', '1b3428', '264634', '2f5f55', '447c6d', '5f9a86', '86c6b6', 'c8eee0')
IRONB = ramp('060a0c', '0e1418', '161e24', '222c34', '323e48', '4a5864', '6a7a86')
SHELL = ramp('0e1218', '161c24', '222a36', '323c4c', '465264', '5e6c80', '7c8aa0', 'a0aec0')
PEARL = ramp('3a4650', '6a7c88', 'a8bcc8', 'dff0f8', 'ffffff')
CORAL = ramp('140c10', '24141a', '3a2028', '542e36', '6e4044', '8a5a58', 'a87a70')
CORAL2 = ramp('0c1416', '122226', '1a3436', '244a4a', '336460', '4a8278')
RUST = ramp('140c0a', '2a1610', '442418', '603424', '7a4a30')

MATS = [('stone', STONEB), ('verd', VERD, False), ('algae', ALGAE), ('bone', BONE), ('wood', WOODB), ('bronze', BRONZE), ('iron', IRONB),
        ('shell', SHELL), ('pearl', PEARL, False), ('coral', CORAL), ('coral2', CORAL2), ('rust', RUST)]
OL = C('0e181b')


def new(w=48, h=48, S=4):
    return Rel(w, h, S, mats=MATS)


def lit(R, **kw):
    a = dict(L=(-0.35, -0.85, 0.45), amb=0.64, key=1.12, ao=0.55, shadow=0.5, shadow_len=6, rim=((0.9, -0.3), 0.06))
    a.update(kw); return R.light(**a)


def px(R, lv=None, **kw):
    a = dict(outline_lit=OL, dither=0.3); a.update(kw)
    return R.pixels(lv, **a)


def drown(R, seed, amount=0.5, floor=48, barn=6, y_top=None):
    """algae in hollows and on ledges, a darker wet band near the floor, a few barnacles."""
    S = R.S; X, Y = R.X, R.Y
    cav = np.clip((blur(R.hgt, 2.0 * S) - R.hgt) / 1.5, 0, 1)
    ledge = np.clip(-np.gradient(blur(R.hgt, S), axis=0) * S * 0.6, 0, 1)
    clump = vnoise(R.W, R.H, 4 * S, seed, 3, 0.8, 1.6)
    y0 = y_top if y_top is not None else floor - 30
    grow = cav * 0.8 + ledge * 0.6 + smoothstep(y0, floor, Y) * 0.4 * amount
    sel = (grow + (clump - 0.5) * 1.2 > 0.75 - 0.25 * amount) & (R.a > 0.5) & (R.mat == R.mat_ix['stone'])
    R.mat = np.where(sel, R.mat_ix['algae'], R.mat); R.val = np.where(sel, 0.35 + 0.5 * clump, R.val)
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero((R.a > 0.5) & (R.mat != R.mat_ix['verd']) & (R.mat != R.mat_ix['pearl']) & (Y > floor - 14))
    for _ in range(barn):
        if not len(xs): break
        i = rng.integers(len(xs)); x = xs[i] / S - R.ox; y = ys[i] / S - R.oy
        r = rng.uniform(0.8, 1.3)
        hz = float(R.hgt[ys[i], xs[i]])
        R.put(R.ell(x, y, r, r * 0.9) * (R.a > 0.5), 'bone', 0.55, z=hz + 0.8, prof='dome', r=r, cover=0.6)
        R.carve(R.ell(x, y, r * 0.35, r * 0.3), 0.6, -0.35)


# ----------------------------------------------------------------------------------------------- graves
def gravestone():
    R = new(); st = R.stone(401, 0.05, 3)
    # a round-headed stone, leaning a little, an inscription worn to shadows, a carved hourglass
    pts = [(17, 47.6), (17.2, 32)] + [(24 + 7 * math.cos(a), 32 - 7 * math.sin(a) * 1.05) for a in np.linspace(math.pi, 0, 18)] + [(31, 47.6)]
    Q = R.poly(pts)
    R.put(Q, 'stone', 0.65, z=3, prof='round', r=1.6, tex=st)
    R.carve(np.clip(R.poly([(18.6, 46), (18.6, 32.4)] + [(24 + 5.4 * math.cos(a), 32.4 - 5.4 * math.sin(a)) for a in np.linspace(math.pi, 0, 14)] + [(29.4, 46)]) -
                    R.poly([(19.2, 45.4), (19.2, 32.6)] + [(24 + 4.8 * math.cos(a), 32.6 - 4.8 * math.sin(a)) for a in np.linspace(math.pi, 0, 14)] + [(28.8, 45.4)]), 0, 1), 0.5, -0.1)
    for k, w in enumerate((7, 6, 7, 5, 6)):
        R.carve(R.rect(24 - w / 2, 34.4 + k * 2.0, 24 + w / 2, 34.9 + k * 2.0), 0.4, -0.1)
    R.carve(R.poly([(22.4, 27.2), (25.6, 27.2), (24.4, 29.0), (25.6, 30.8), (22.4, 30.8), (23.6, 29.0)]), 0.6, -0.12)
    R.put(R.poly([(15, 48), (33, 48), (32, 45.8), (16, 45.8)]), 'stone', 0.55, z=4, prof='round', r=0.8, tex=st)
    drown(R, 402, 0.7)
    R2 = rotate_rel(R, -4, (24, 47))
    return R2, lit(R2)


def gravecross():
    R = new(); st = R.stone(411, 0.05, 3)
    R.put(R.poly([(17, 48), (31, 48), (30, 43.6), (18, 43.6)]), 'stone', 0.60, z=2, prof='round', r=1.0, tex=st)
    R.put(R.poly([(19.6, 44), (28.4, 44), (27.4, 41.6), (20.6, 41.6)]), 'stone', 0.65, z=3, prof='round', r=0.8, tex=st)
    shaft = R.poly([(21.6, 42), (26.4, 42), (26.0, 18.6), (22.0, 18.6)]); R.put(shaft, 'stone', 0.68, z=5, prof='round', r=1.4, tex=st)
    arm = R.rect(14.6, 23.2, 33.4, 27.6); R.put(arm, 'stone', 0.68, z=5, prof='round', r=1.4, tex=st)
    R.put(R.rect(22.0, 16.2, 26.0, 19.0), 'stone', 0.70, z=5, prof='round', r=1.2, tex=st)
    ring = np.clip(R.ell(24, 25.4, 7.4, 7.4) - R.ell(24, 25.4, 5.4, 5.4), 0, 1)
    R.put(np.clip(ring - shaft - arm, 0, 1), 'stone', 0.62, z=4, prof='round', r=0.9, tex=st)
    R.put(R.ell(24, 25.4, 1.8, 1.8), 'stone', 0.75, z=7, prof='dome', r=1.5)
    for y in (30, 33, 36, 39): R.carve(R.line([(22.6, y), (24, y - 1), (25.4, y)], 0.45), 0.4, -0.1)   # knotwork
    drown(R, 412, 0.6)
    return R, lit(R)


def cairn():
    R = new(); rng = np.random.default_rng(421)
    stones = [(24, 45.2, 11.5, 3.4, 0.5), (17.5, 46.4, 5, 2.2, 0.45), (31, 46.2, 5.6, 2.4, 0.48), (24.5, 40.6, 8.4, 2.8, 0.55),
              (23.6, 36.6, 6.2, 2.4, 0.6), (25, 33.2, 4.4, 2.0, 0.62), (24.2, 30.4, 3.0, 1.6, 0.66)]
    for i, (x, y, rx, ry, v) in enumerate(stones):
        m = R.ell(x, y, rx, ry); R.put(m, 'stone', v, z=2 + i * 1.6, prof='dome', r=min(rx, ry) * 1.2, tex=R.stone(422 + i, 0.06, 2))
    # a driftwood marker with a bone tied across it
    R.put(R.tube([(24.6, 31), (24.2, 22.6), (24.8, 19.8)], 1.3, 1.0), 'wood', 0.55, z=14, prof='round', r=0.6)
    R.put(R.tube([(20.8, 24.6), (28.4, 23.4)], 1.1), 'bone', 0.62, z=15, prof='round', r=0.5)
    for x in (20.8, 28.4): R.put(R.ell(x, 24.2 - (x > 24) * 1.2, 1.0, 0.9), 'bone', 0.66, z=15.2, prof='dome', r=0.8)
    drown(R, 429, 0.7, barn=5)
    return R, lit(R)


# ----------------------------------------------------------------------------------------------- tombs
def tomb(leak):
    R = new(); st = R.stone(431, 0.05, 3)
    # a chest tomb: plinth, a panelled chest with quatrefoils, a coped (gabled) lid overhanging it
    R.put(R.rect(5.4, 44.6, 42.6, 48), 'stone', 0.45, z=2, prof='round', r=0.8, tex=st)
    R.put(R.rect(7, 22.4, 41, 45), 'stone', 0.5, z=3, prof='round', r=1.2, tex=st)
    for x0 in (9, 20.4, 31.8):
        panel(R, x0, 25.4, x0 + 8.6, 42.6, 'stone', 0.52, z=3.2, inset=1.2, tex=st)
        qx, qy = x0 + 4.3, 34
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            R.carve(R.ell(qx + math.cos(a) * 1.6, qy + math.sin(a) * 1.6, 1.4, 1.4), 0.6, -0.12)
    R.put(R.rect(5.6, 19.6, 42.4, 23.0), 'stone', 0.58, z=6, prof='cyly', amp=0.7, tex=st)
    lid = R.poly([(5, 20), (24, 10.6), (43, 20)]); R.put(lid, 'stone', 0.6, z=6.5, prof='round', r=1.4, tex=st)
    R.put(R.tube([(6, 19.6), (24, 11), (42, 19.6)], 0.6), 'stone', 0.66, z=7.5, prof='flat')
    R.put(R.ell(24, 15.6, 1.6, 1.6), 'stone', 0.66, z=8, prof='dome', r=1.4)       # a boss on the gable
    if leak:   # a crack down the middle panel: water leaks out, glowing, into a small pool
        crack = R.tube([(24.6, 23), (23.4, 27.4), (25.2, 31.6), (23.8, 36.4), (24.8, 40.8)], 0.9)
        R.put(crack, 'verd', 0.0, z=5, prof='flat', lit=0.0, tex=0.55 + 0.25 * np.sin(R.Y * 1.3))
        stream = R.tube([(24.8, 41), (24.6, 44.6), (24.8, 46.6)], 1.3, 1.0); R.put(stream, 'verd', 0.0, z=6, prof='flat', lit=0.0, tex=0.62)
        R.put(R.ell(24.4, 47.4, 6.0, 0.9), 'verd', 0.0, z=6, prof='flat', lit=0.0, tex=0.45 - np.abs(R.X - 24.4) * 0.04)
    drown(R, 432 + leak, 0.7, barn=8)
    return R, lit(R, point=(24.4, 40, 5, 12, 0.35) if leak else None)


def pew():
    R = new(); wd = R.grain(441, 0.07, 'x', 5, 9)
    # the back: three long boards, a capping rail, one board sprung loose; the seat; carved poppyhead ends
    for k, y in enumerate((28.4, 31.6, 34.8)):
        if k == 1:
            R.put(R.poly([(9.5, y), (27, y), (29, y + 2.6), (9.5, y + 2.8)]), 'wood', 0.48, z=2, prof='round', r=0.8, tex=wd)
            R.put(R.poly([(28.6, y + 0.2), (38.6, y - 1.4), (38.8, y + 1.4), (29, y + 2.8)]), 'wood', 0.44, z=2.4, prof='round', r=0.8, tex=wd)
        else:
            R.put(R.rect(9.5, y, 38.5, y + 2.9), 'wood', 0.48, z=2, prof='round', r=0.8, tex=wd)
    R.put(R.rect(8.6, 26.6, 39.4, 28.8), 'wood', 0.56, z=3, prof='cyly', amp=0.7, tex=wd)
    R.put(R.rect(8.6, 38.0, 39.4, 40.6), 'wood', 0.58, z=4, prof='cyly', amp=0.7, tex=wd)
    R.put(R.rect(9.5, 40.6, 38.5, 41.8), 'wood', 0.3, z=3.5, prof='flat')
    for x in (16, 32): R.put(R.rect(x - 0.9, 40.6, x + 0.9, 48), 'wood', 0.42, z=2, prof='cylx', amp=0.6)
    for x0 in (5.6, 38.4):
        end = R.poly([(x0, 48), (x0, 30), (x0 + 0.6, 27.6), (x0 + 2.0, 26.0), (x0 + 2.0, 24.4), (x0 + 1.0, 23.4), (x0 + 2.0, 22.4), (x0 + 3.0, 23.4), (x0 + 2.0, 24.4),
                       (x0 + 2.0, 26.0), (x0 + 3.4, 27.6), (x0 + 4.0, 30), (x0 + 4.0, 48)])
        R.put(end, 'wood', 0.52, z=6, prof='round', r=1.2, tex=R.grain(442, 0.06, 'y', 5, 9))
        R.carve(R.rect(x0 + 1.4, 32, x0 + 2.6, 45), 0.6, -0.1)
    # weed and silt along the seat and the feet
    alg = (vnoise(R.W, R.H, 2 * R.S, 443, 2) > 0.55) & (R.a > 0.5) & (((R.Y > 37.4) & (R.Y < 39.2)) | (R.Y > 45.4))
    R.mat = np.where(alg, R.mat_ix['algae'], R.mat); R.val = np.where(alg, 0.5, R.val)
    return R, lit(R)


# ----------------------------------------------------------------------------------------------- the lagoon's floor
def clam(f):
    R = new(); sh = R.speck(451, 0.03, 0.8)
    cx, base = 24.5, 47.6
    # the lower valve: a deep fluted bowl with a wavy lip
    nfl = 7
    lip_y = lambda x: base - 5.2 - 1.3 * np.cos((x - cx) / 13.0 * nfl * math.pi)
    xs = np.linspace(cx - 13, cx + 13, 40)
    low = R.poly([(cx - 13, base - 4.4)] + [(x, float(lip_y(x))) for x in xs] + [(cx + 13, base - 4.4), (cx + 10, base), (cx - 10, base)])
    flute = 0.8 * np.cos((R.X - cx) / 13.0 * nfl * math.pi)
    R.put(low, 'shell', 0.5, z=3, h=R.prof(low, 'dome', r=3) + flute, tex=sh)
    if f == 0:   # shut: the upper valve meets the lower along the wavy lip
        up = R.poly([(cx - 13, base - 4.4)] + [(x, float(lip_y(x))) for x in xs] + [(cx + 13, base - 4.4), (cx + 11.6, base - 8.4), (cx + 5, base - 10.6), (cx - 5, base - 10.6), (cx - 11.6, base - 8.4)])
        R.put(up, 'shell', 0.58, z=5, h=R.prof(up, 'dome', r=3) + flute * smoothstep(base - 10, base - 6, R.Y), tex=sh)
        R.put(R.ell(cx, float(lip_y(cx)) + 0.2, 1.2, 0.4), 'pearl', 0.35, z=6, prof='flat', lit=0.0)       # a sliver of light
    else:        # open: the upper valve thrown back, the mantle, the pearl
        up = R.poly([(cx - 12.6, base - 6.4), (cx - 10, base - 13.6), (cx - 4, base - 16.8), (cx + 4, base - 16.8), (cx + 10, base - 13.6), (cx + 12.6, base - 6.4),
                     (cx + 6, base - 8.6), (cx, base - 9.0), (cx - 6, base - 8.6)])
        u = np.arctan2(R.X - cx, (base - 7) - R.Y)
        R.put(up, 'shell', 0.62, z=2, h=R.prof(up, 'dome', r=3) + 0.8 * np.cos(u * 9), tex=sh)
        mant = R.poly([(cx - 11.6, base - 5.6)] + [(x, float(lip_y(x)) - 0.6) for x in np.linspace(cx - 11, cx + 11, 20)] + [(cx + 11.6, base - 5.6), (cx + 8, base - 7.8), (cx - 8, base - 7.8)])
        R.put(mant, 'coral2', 0.62, z=4, prof='round', r=1.0, tex=0.1 * np.sin(R.X * 2.6))
        k = (0.6, 0.85, 0.7)[f - 1]
        pr = R.ell(cx, base - 8.8, 3.0, 2.9)
        R.put(pr, 'pearl', 0.0, z=6, prof='flat', lit=0.0, tex=np.clip(k + 0.15 - np.hypot(R.X - cx + 0.9, R.Y - base + 9.8) * 0.13, 0.25, 1))
    R.put(R.ell(cx, base + 0.2, 12, 0.8), 'stone', 0.25, z=1, prof='flat')
    return R, lit(R, point=(cx, base - 9, 6, 12, (0, 0.3, 0.45, 0.35)[f]))


def coral():
    R = new(); rng = np.random.default_rng(461)
    R.put(R.ell(24, 46.6, 11, 2.4), 'stone', 0.45, z=1, prof='dome', r=2, tex=R.stone(462, 0.06, 2))
    # a fan coral behind (a lattice of fine branches), branching coral in front
    fan = np.zeros((R.H, R.W))
    def branch(x, y, a, L, w, d, acc):
        x2, y2 = x + math.cos(a) * L, y - math.sin(a) * L
        acc.append(R.tube([(x, y), ((x + x2) / 2 + rng.uniform(-1, 1), (y + y2) / 2), (x2, y2)], w, w * 0.7))
        if d > 0:
            for s in (-1, 1):
                branch(x2, y2, a + s * rng.uniform(0.25, 0.6), L * rng.uniform(0.6, 0.8), w * 0.72, d - 1, acc)
    acc = []; branch(30, 45, math.pi / 2 + 0.2, 7, 1.2, 4, acc)
    for m in acc: fan = np.maximum(fan, m)
    R.put(fan, 'coral2', 0.5, z=2, prof='round', r=0.4)
    for i, (x, a, L, w) in enumerate(((17, 1.75, 6.5, 2.6), (22, 1.5, 8.5, 2.8), (26.5, 1.3, 6, 2.4))):
        acc = []; branch(x, 45.6, a, L, w, 3, acc)
        m = np.zeros((R.H, R.W))
        for mm in acc: m = np.maximum(m, mm)
        R.put(m, 'coral', 0.5 + i * 0.05, z=4 + i, prof='round', r=1.0, tex=R.speck(463 + i, 0.06, 0.6))
    # polyps: pale dots on the tips
    ys, xs = np.nonzero((R.mat == R.mat_ix['coral']) & (R.a > 0.5))
    for _ in range(14):
        i = rng.integers(len(xs)); R.put(R.ell(xs[i] / 4, ys[i] / 4, 0.5, 0.5), 'coral', 0.85, z=9, prof='flat')
    return R, lit(R)


# ----------------------------------------------------------------------------------------------- waterworks
def tidemark():
    R = new(); st = R.stone(471, 0.05, 2)
    R.put(R.poly([(19.6, 48), (28.4, 48), (27.6, 45.4), (20.4, 45.4)]), 'stone', 0.60, z=2, prof='round', r=0.8, tex=st)
    R.put(R.rect(21.6, 21.6, 26.4, 45.6), 'stone', 0.65, z=3, prof='cylx', amp=0.8, tex=st)
    R.put(R.poly([(20.6, 22), (27.4, 22), (26.4, 19.6), (21.6, 19.6)]), 'stone', 0.70, z=4, prof='round', r=0.8, tex=st)
    R.put(R.ell(24, 19.4, 1.4, 1.0), 'bronze', 0.6, z=5, prof='dome', r=1)
    for k, y in enumerate(np.arange(24, 45, 2.4)):     # the graduations: deep notches; every other one a bronze plate
        if k % 2 == 0:
            R.put(R.rect(21.2, y, 27.2, y + 0.9), 'bronze', 0.55, z=5, prof='cyly', amp=0.4, spec=0.3)
            R.put(R.rect(27.2, y - 0.3, 28.4, y + 1.2), 'bronze', 0.5, z=5.2, prof='round', r=0.4)
        else:
            R.carve(R.rect(21.8, y + 0.2, 25.2, y + 0.6), 0.5, -0.12)
    # the high-water line: a ring of white salt and a weed fringe below it
    R.put(R.rect(21.4, 33.6, 26.6, 34.4), 'bone', 0.6, z=5.4, prof='flat')
    drown(R, 472, 0.9, y_top=34, barn=4)
    return R, lit(R)


def sluice():
    R = new(); st = R.stone(481, 0.05, 3)
    # stone housing with a channel; the iron gate raised on a threaded spindle; the wheel on top
    R.put(R.rect(9.4, 33, 38.6, 48), 'stone', 0.5, z=2, prof='round', r=1.2, tex=st)
    R.put(R.rect(8.6, 31.4, 39.4, 34.0), 'stone', 0.58, z=3, prof='cyly', amp=0.7, tex=st)
    R.put(R.rect(13, 36.2, 35, 46), 'stone', 0.12, z=1, prof='flat')                                 # the culvert mouth
    R.put(R.rect(13, 42.6, 35, 46), 'verd', 0.0, z=1.5, prof='flat', lit=0.0, tex=0.32 + 0.12 * np.sin(R.X * 1.4))   # water through it
    gate = R.rect(14, 35.4, 34, 41.4); R.put(gate, 'iron', 0.45, z=4, prof='round', r=0.8)
    for x in np.arange(15.5, 33.5, 3.4): R.put(R.rect(x, 35.6, x + 0.9, 41.2), 'iron', 0.55, z=4.6, prof='cylx', amp=0.5)
    R.put(R.rect(14, 38.0, 34, 38.9), 'rust', 0.5, z=4.4, prof='flat')
    for x in (11.6, 36.4): R.put(R.rect(x - 1.4, 22, x + 1.4, 33), 'stone', 0.55, z=3, prof='cylx', amp=0.7, tex=st)
    R.put(R.rect(9.6, 20.6, 38.4, 23.6), 'stone', 0.6, z=4, prof='cyly', amp=0.7, tex=st)
    R.put(R.rect(23.2, 23.6, 24.8, 35.4), 'iron', 0.5, z=5, prof='cylx', amp=0.6)
    for y in np.arange(24.4, 35, 1.2): R.carve(R.rect(23.2, y, 24.8, y + 0.35), 0.3, -0.12)
    wheel = np.clip(R.ell(24, 16.2, 6.2, 6.2) - R.ell(24, 16.2, 4.8, 4.8), 0, 1)
    for k in range(6):
        a = k * math.pi / 3 + 0.3; wheel = np.maximum(wheel, R.tube([(24, 16.2), (24 + math.cos(a) * 5.2, 16.2 + math.sin(a) * 5.2)], 0.9))
    R.put(wheel, 'rust', 0.55, z=8, prof='round', r=0.5, spec=0.2)
    R.put(R.ell(24, 16.2, 1.4, 1.4), 'iron', 0.6, z=9, prof='dome', r=1.2)
    R.put(R.rect(23.3, 16.2, 24.7, 21), 'iron', 0.5, z=6, prof='cylx', amp=0.5)
    drown(R, 482, 0.6, barn=6)
    return R, lit(R, point=(24, 44, 4, 12, 0.25))


def wellcover():
    R = new(); st = R.stone(491, 0.05, 2)
    R.put(R.poly([(11, 48), (37, 48), (36.4, 41.6), (11.6, 41.6)]), 'stone', 0.60, z=2, prof='round', r=1.0, tex=st)
    for x in np.arange(12, 36, 4.2): R.carve(R.rect(x, 41.8, x + 0.4, 48), 0.5, -0.1)
    R.put(R.rect(10.6, 39.8, 37.4, 42.0), 'stone', 0.70, z=3, prof='cyly', amp=0.6, tex=st)
    lid = R.poly([(12.6, 40.2), (35.4, 40.2), (34.4, 37.4), (13.6, 37.4)]); R.put(lid, 'iron', 0.45, z=4, prof='round', r=0.8, spec=0.2)
    for x in np.arange(15, 34, 3.0): R.put(R.rect(x, 37.6, x + 0.8, 40.0), 'iron', 0.58, z=4.6, prof='cylx', amp=0.4)
    R.put(R.rect(13.6, 38.4, 34.4, 39.0), 'rust', 0.45, z=4.8, prof='flat')
    ring = np.clip(R.ell(24, 34.6, 3.0, 2.6) - R.ell(24, 34.6, 2.0, 1.7), 0, 1); R.put(ring, 'iron', 0.55, z=6, prof='round', r=0.5, spec=0.3)
    R.put(R.rect(23, 36.6, 25, 38), 'iron', 0.5, z=6, prof='round', r=0.4)
    drown(R, 492, 0.6, barn=4)
    return R, lit(R)


# ----------------------------------------------------------------------------------------------- the Drowned Bell (64x80, hung)
def bigbell():
    R = Rel(64, 80, 4, mats=MATS); cx = 32; br = R.speck(501, 0.04, 0.8)
    # chain from the beam
    for i, y in enumerate(np.arange(0, 12, 2.4)):
        link = np.clip(R.ell(cx, y + 1.2, 1.2 if i % 2 else 0.6, 1.6) - (R.ell(cx, y + 1.2, 0.4, 0.8) if i % 2 else 0), 0, 1)
        R.put(link, 'iron', 0.5, z=2, prof='round', r=0.5)
    # the crown (canons) and headstock
    R.put(R.rect(cx - 6, 11.6, cx + 6, 14.6), 'wood', 0.45, z=3, prof='cyly', amp=0.6)
    for dx in (-3, 0, 3):
        R.put(np.clip(R.ell(cx + dx, 17.2, 1.6, 3.0) - R.ell(cx + dx, 17.0, 0.6, 1.8), 0, 1), 'bronze', 0.5, z=4, prof='round', r=0.6)
    # the bell: shoulder, waist, the flare of the sound bow, the lip
    prof = [(18.6, 5.0), (19.4, 8.6), (20.6, 10.8), (22.4, 12.2), (26, 12.8), (32, 13.2), (38, 14.0), (44, 15.8), (50, 18.6), (56, 22.2), (61, 25.6), (65, 27.9), (68, 29.0), (69.6, 29.2), (71.0, 28.4)]
    body = turned(R, cx, prof, 'bronze', 0.4, z=6, tex=br, spec=0.45, gloss=8)
    # mouldings: shoulder lines, an inscription band, the sound-bow ridges
    for (y, d) in ((22.6, 0.6), (24.0, -0.5), (60.8, 0.7), (62.6, -0.5), (66.2, 0.8)):
        band = (np.abs(R.Y - y) < 0.55) & (body > 0.5)
        R.hgt = np.where(band, R.hgt + d, R.hgt)
    insc = (R.Y > 26.4) & (R.Y < 29.6) & (body > 0.5)
    glyph = (np.abs(((R.X - cx) / 2.2) % 1 - 0.5) < 0.18) & ((((R.Y - 26.4) / 1.6) % 1) < 0.6)
    R.hgt = np.where(insc & glyph, R.hgt + 0.5, R.hgt); R.val = np.where(insc & glyph, R.val + 0.08, R.val)
    # the mouth: the dark inside under the lip
    R.put(R.ell(cx, 71.4, 27.6, 3.0), 'iron', 0.1, z=4, prof='flat')
    R.put(np.clip(R.ell(cx, 70.8, 29.2, 3.6) - R.ell(cx, 71.4, 27.6, 3.0), 0, 1) * (R.Y > 70.8), 'bronze', 0.55, z=12, prof='round', r=0.6, spec=0.4)
    # verdigris streaks and crust, barnacles on the sound bow
    st = vnoise(R.W, R.H, 3 * R.S, 502, 3, 0.35, 5.0)
    crust = (st > 0.6) & (body > 0.5)
    R.val = np.where(crust, R.val + 0.1, R.val); R.spec = np.where(crust, 0.1, R.spec)
    R.val = np.where(body > 0.5, R.val - 0.12 * smoothstep(40, 20, R.Y), R.val)      # the crown in its own shadow
    return R, lit(R, L=(-0.45, -0.75, 0.5))


ITEMS = {
    'gravecross': lambda: [px(*gravecross())], 'gravestone': lambda: [px(*gravestone())], 'cairn': lambda: [px(*cairn())],
    'tomb': lambda: [px(*tomb(False))], 'tomb_leak': lambda: [px(*tomb(True))], 'pew': lambda: [px(*pew())],
    'pearlclam': lambda: [px(*clam(f)) for f in range(4)], 'tidemark': lambda: [px(*tidemark())], 'wellcover': lambda: [px(*wellcover())],
    'sluice': lambda: [px(*sluice())], 'coral': lambda: [px(*coral())],
}


def main():
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    frames = {}
    for tag, f in ITEMS.items():
        if only and tag not in only: continue
        frames[tag] = f()
        for i, im in enumerate(frames[tag]): im.save(os.path.join(SRC, f'db_{tag}_{i}.png'))
    if not only or 'bigbell' in only:
        bell = px(*bigbell()); bell.save(os.path.join(SRC, 'xsa_bell_bigbell_0.png'))
        if '--nobuild' not in sys.argv: build_sheet('xsa_bell', {'bigbell': [bell]})
    if '--nobuild' not in sys.argv and not only:
        build_sheet('xsa_db', frames, keep_v1=('weeds', 'chainlamp', 'candles_db'))


if __name__ == '__main__':
    main()
