#!/usr/bin/env python3
"""Batch B props: the Drowned Saint (xsa_saint 176x416) and the Sunken Nave rose window (xsa_rosewin 160x160), DB10.

The saint is painted twice in game: into the back layer and, clipped to DB10's solid cells (rect 36,13,11,25), over
the front layer. So her silhouette is built to cover those cells: the body (cols 38-44, rows 15-32 = sprite x 32..143,
y 48..335) and the plinth (cols 36-46, rows 33-37 = x 0..175, y 336..415). The halo she holds up is the one-way perch
at row 14 (sprite y 32). The waterline is row 18 (sprite y 96): below it the marble is drowned (algae, barnacles).

Run: python3 art/gen_props_b_saint.py [--render]   (--render re-runs ComfyUI; otherwise the cached renders are used)
"""
import math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props_b_lib import *   # noqa

MARBLE = ramp('08070c', '0e1513', '151e1b', '1d2824', '26332e', '31403a', '3e4f47', '4e6158', '63776c', '7e9488', 'a0b4a8', 'c8d6c8')
ALGAE = ramp('0a1412', '10201a', '18301f', '22402a', '2e5434', '46703f')
BRONZE = ramp('0d1c16', '13271e', '1b3428', '264634', '2f5f55', '447c6d', '5f9a86', '86c6b6', 'c8eee0')
BARN = ramp('151e1b', '2c363a', '5c594b', '848070', 'a8a290', 'cfc8b2')
GLOW = ramp('145a54', '1f8f85', '2fbfb0', '8ff0e0', 'e0fff8')
STONE = ramp('04090b', '070d10', '0e181b', '132024', '1e2f33', '26393c', '2f4345', '3a5052', '4b6464', '63807c')
GLASS = ramp('0a1e22', '0d3431', '145a54', '1f8f85', '2fbfb0', '6fd8c8', 'b8f4e8')
GLASS2 = ramp('101a2a', '182a40', '22405a', '2f6078', '4a8aa0', '86c0cc')     # a cold blue second glass
GLASS3 = ramp('161418', '262024', '3c3234', '5a4a44', '857058', 'b8a07a')     # amber (a few old panes)
LEAD = ramp('020506', '04090b', '0a1215', '132024', '1e2f33')

CX = 88


def robe_half(y):
    """half width of the robe at sprite row y."""
    pts = [(104, 30), (118, 40), (140, 52), (170, 56), (260, 57), (318, 60), (336, 66)]
    ys = [p[0] for p in pts]; ws = [p[1] for p in pts]
    return np.interp(y, ys, ws)


def saint():
    W, H = 176, 416
    R = Rel(W, H, S=3, mats=[('marble', MARBLE), ('algae', ALGAE), ('bronze', BRONZE), ('barn', BARN), ('glow', GLOW, False)])
    X, Y, S = R.X, R.Y, R.S
    stone = R.stone(3, 0.05, 6) + R.speck(4, 0.025, 0.8)

    # ---------------------------------------------------------------- plinth (full width, y 330..415)
    base = R.rect(0, 392, 176, 416); R.put(base, 'marble', 0.50, z=6, prof='round', r=2.0, tex=stone)
    torus = R.rect(1, 384, 175, 393); R.put(torus, 'marble', 0.58, z=8, prof='cyly', amp=0.8, tex=stone)
    die = R.rect(4, 346, 172, 385); R.put(die, 'marble', 0.50, z=6, prof='round', r=2.5, tex=stone)
    # carved panel with a relief of waves and a sealed scroll
    pan = R.rect(18, 352, 158, 379); R.carve(pan, 2.0, -0.08)
    for i in range(7):
        x0 = 24 + i * 19
        wave = R.line([(x0 + t * 1.6, 372 - 5 * math.sin(t / 10 * math.pi) - (t / 10) * 2) for t in range(0, 11)], 2.2)
        R.put(wave, 'marble', 0.52, z=5.5, prof='round', r=1.0, tex=stone)
        curl = R.ell(x0 + 13, 366, 3.0, 3.0); R.put(curl, 'marble', 0.55, z=5.6, prof='dome', r=2, tex=stone)
        R.carve(R.ell(x0 + 13.5, 366.5, 1.2, 1.2), 1.5, -0.1)
    corn = R.poly([(0, 336), (176, 336), (172, 346), (4, 346)]); R.put(corn, 'marble', 0.62, z=9, prof='cyly', amp=0.6, tex=stone)
    lip = R.rect(0, 333, 176, 338); R.put(lip, 'marble', 0.66, z=10, prof='cyly', amp=0.6, tex=stone)

    # ---------------------------------------------------------------- the veil, behind everything of the figure
    veil = R.poly([(CX - 26, 70), (CX - 22, 56), (CX - 12, 48), (CX, 46), (CX + 12, 48), (CX + 22, 56), (CX + 26, 70),
                   (CX + 34, 112), (CX + 44, 150), (CX - 44, 150), (CX - 34, 112)])
    vh = R.prof(veil, 'dome', r=10, amp=0.9)
    vf = 1.2 * (0.5 - 0.5 * np.cos(2 * math.pi * ((X - CX) / (8 + (Y - 46) * 0.12)))) * smoothstep(60, 110, Y)
    R.put(veil, 'marble', 0.42, z=10, h=vh + vf, tex=stone)

    # ---------------------------------------------------------------- the robe: a gathered bodice, a cord, a long skirt of folds
    hw = robe_half(Y)
    bod_hw = np.interp(Y, [100, 112, 140, 172], [26, 36, 38, 40])
    skirt_hw = np.interp(Y, [168, 200, 240, 300, 336], [42, 52, 57, 58, 66])
    robe = (((np.abs(X - CX) < bod_hw) & (Y > 100) & (Y <= 172)) | ((np.abs(X - CX) < skirt_hw) & (Y > 172) & (Y < 340))).astype(float)
    robe = blur(robe, 0.6 * S)
    # bodice: soft folds gathered toward the cord, a little chest volume
    ub = (X - CX) / np.maximum(bod_hw, 1) * 4.0 * (1 - 0.35 * smoothstep(110, 172, Y))
    bfold = (0.5 - 0.5 * np.cos(2 * math.pi * ub)) ** 1.3 * 2.2 * smoothstep(118, 150, Y)
    chest = np.exp(-(((X - CX) / 22) ** 2 + ((Y - 128) / 14) ** 2)) * 5
    # skirt: long straight folds that fan out from the cord and crumple where the hem pools on the plinth
    nfold = 9
    us = (X - CX) / np.maximum(skirt_hw, 1) * nfold / 2 + 0.10 * np.sin(Y / 41.0) + 0.06 * np.sin(Y / 17.0 + X / 23.0)
    ridge = (0.5 - 0.5 * np.cos(2 * math.pi * us)) ** 1.6
    folds = ridge * (2.0 + 6.0 * smoothstep(172, 240, Y)) * (Y > 172)
    breakf = 1.8 * np.sin((Y - 300) / 6.0 + us * 2.4) * smoothstep(306, 330, Y)
    col = np.sqrt(np.clip(1 - ((X - CX) / np.maximum(np.where(Y > 172, skirt_hw, bod_hw) + 4, 1)) ** 2, 0, 1)) * 18
    R.put(robe, 'marble', 0.55, z=12, h=col + folds + breakf + bfold + chest, tex=stone)
    # embroidered hem band
    for hy in (318.0, 322.5):
        band = (np.abs(Y - hy - 1.2 * np.sin(us * 2 * math.pi)) < 0.7) & (robe > 0.5)
        R.hgt = np.where(band, R.hgt + 0.8, R.hgt)
    # the waist cord, knotted, its ends hanging
    cord = R.tube([(CX - 42, 170), (CX - 20, 175), (CX, 176), (CX + 20, 175), (CX + 42, 170)], 4.0)
    R.put(cord, 'marble', 0.62, z=34, prof='cyly', amp=0.9, tex=stone)
    for sx in (-1, 1):
        end = R.tube([(CX + sx * 4, 176), (CX + sx * 6, 200), (CX + sx * 5, 226), (CX + sx * 7, 246)], 3.2, 2.4)
        R.put(end, 'marble', 0.6, z=33, prof='round', r=1.6, tex=stone)
    R.put(R.ell(CX, 177, 5.5, 4.5), 'marble', 0.66, z=36, prof='dome', r=4)
    R.put(R.ell(CX - 6, 248, 2.8, 4), 'marble', 0.6, z=34, prof='dome', r=3); R.put(R.ell(CX + 8, 248, 2.8, 4), 'marble', 0.6, z=34, prof='dome', r=3)

    # ---------------------------------------------------------------- arms raised to the halo, long sleeves hanging
    for sx in (-1, 1):
        sh = (CX + sx * 30, 118); el = (CX + sx * 47, 84); wr = (CX + sx * 41, 44)
        # sleeve: hangs from the forearm and pools against the side of the robe
        sl = R.poly([(wr[0] + sx * 1, wr[1] + 10), (el[0] + sx * 9, el[1] - 4), (CX + sx * 58, 124), (CX + sx * 58, 156),
                     (CX + sx * 55, 166), (CX + sx * 49, 170), (CX + sx * 42, 166), (CX + sx * 38, 150), (sh[0] + sx * 2, sh[1] + 4),
                     (CX + sx * 22, 92), (wr[0] - sx * 6, wr[1] + 12)])
        sh_h = R.prof(sl, 'dome', r=9, amp=0.9)
        sfold = 2.6 * (0.5 - 0.5 * np.cos(2 * math.pi * ((X - CX - sx * 46) / 5.5 + 0.08 * np.sin(Y / 9.0)))) ** 1.4 * smoothstep(92, 130, Y)
        R.put(sl, 'marble', 0.5, z=16, h=sh_h + sfold, tex=stone)
        # the bare forearm out of the sleeve, to the hand
        fa = R.tube([(el[0] - sx * 1, el[1] - 4), (wr[0], wr[1] + 2)], 8.5, 6.5)
        R.put(fa, 'marble', 0.62, z=30, prof='round', r=3.2, tex=stone * 0.6)
        # sleeve cuff at the elbow
        cuff = R.tube([(el[0] - sx * 6, el[1] + 0), (el[0] + sx * 5, el[1] - 5)], 7.0)
        R.put(cuff, 'marble', 0.58, z=32, prof='dome', r=4, tex=stone)
        for j in range(3):
            R.carve(R.line([(el[0] - sx * (5 - j * 2.5), el[1] + 2 - j * 1.5), (el[0] - sx * (2 - j * 2.5), el[1] + 9 - j)], 0.6), 0.8, -0.08)

    # ---------------------------------------------------------------- the head inside the veil
    hood_in = R.ell(CX, 80, 16, 22); R.carve(hood_in, 4.0, -0.18)
    face = R.ell(CX, 81, 11.5, 15.0)
    fh = R.prof(face, 'sphere', amp=0.8)
    # features: brow ridge, nose, cheekbones; carved lids, mouth, chin
    nose = np.exp(-((X - CX) / 1.7) ** 2) * smoothstep(73, 79, Y) * (1 - smoothstep(88, 90.5, Y)) * 2.6
    brow = np.exp(-((Y - 75.5) / 1.6) ** 2) * (np.abs(X - CX) < 9.5) * 1.3
    sock = np.exp(-(((np.abs(X - CX) - 4.8) / 2.6) ** 2 + ((Y - 79) / 2.0) ** 2)) * -2.2
    cheek = np.exp(-(((np.abs(X - CX) - 6.5) / 3.0) ** 2 + ((Y - 86) / 3.5) ** 2)) * 1.0
    mouth = np.exp(-(((X - CX) / 3.0) ** 2 + ((Y - 93.2) / 0.7) ** 2)) * -1.3
    lip = np.exp(-(((X - CX) / 2.6) ** 2 + ((Y - 94.6) / 0.9) ** 2)) * 0.6
    chin = np.exp(-(((X - CX) / 4.0) ** 2 + ((Y - 97.5) / 2.0) ** 2)) * 0.8
    R.put(face, 'marble', 0.72, z=22, h=fh + nose + brow + sock + cheek + mouth + lip + chin, tex=stone * 0.4)
    # closed lids (a dark crescent under each brow) and the tear streaks of algae
    for sx in (-1, 1):
        lid = R.line([(CX + sx * 2.5, 80.2), (CX + sx * 4.8, 81.0), (CX + sx * 7.2, 80.2)], 0.9)
        R.shade(lid > 0.4, -0.22)
    neck = R.poly([(CX - 6, 96), (CX + 6, 96), (CX + 7, 104), (CX - 7, 104)]); R.put(neck, 'marble', 0.45, z=18, prof='cylx', amp=0.6, tex=stone * 0.5)
    # the mantle: the veil falls over the shoulders and closes in a curved hem across the chest
    mant = R.poly([(CX - 9, 100), (CX - 24, 104), (CX - 37, 112), (CX - 42, 128), (CX - 40, 144), (CX - 31, 153), (CX - 16, 159), (CX, 161),
                   (CX + 16, 159), (CX + 31, 153), (CX + 40, 144), (CX + 42, 128), (CX + 37, 112), (CX + 24, 104), (CX + 9, 100)])
    phi = np.arctan2(X - CX, np.maximum(Y - 92, 1))
    mfold = (0.5 - 0.5 * np.cos(phi * 13 + 0.25 * np.sin(Y / 9))) ** 1.3 * 3.6 * smoothstep(104, 122, Y)
    mbody = np.exp(-(((X - CX) / 30) ** 2)) * 3 * smoothstep(100, 130, Y)
    R.put(mant, 'marble', 0.6, z=26, h=R.prof(mant, 'round', r=2.5, amp=1.0) + mfold + mbody, tex=stone)
    hem = (np.abs(Y - np.interp(np.abs(X - CX), [0, 16, 31, 40], [161, 159, 153, 144])) < 1.2) & (mant > 0.3)
    R.hgt = np.where(hem, R.hgt + 1.0, R.hgt)
    # the veil's front edge folded over the brow
    vfront = R.poly([(CX - 16, 70), (CX - 10, 62), (CX, 60), (CX + 10, 62), (CX + 16, 70), (CX + 13, 72), (CX, 66), (CX - 13, 72)])
    R.put(vfront, 'marble', 0.6, z=26, prof='round', r=2.2, tex=stone)
    for sx in (-1, 1):
        drape = R.poly([(CX + sx * 15, 70), (CX + sx * 19, 72), (CX + sx * 22, 98), (CX + sx * 20, 112), (CX + sx * 13, 108), (CX + sx * 11, 98), (CX + sx * 12, 86)])
        R.put(drape, 'marble', 0.56, z=29, prof='dome', r=4.0, tex=stone)

    # ---------------------------------------------------------------- the halo she holds up (the perch, top at y 32)
    ring_o = R.ell(CX, 33, 47, 10); ring_i = R.ell(CX, 33, 40, 6.2)
    ring = np.clip(ring_o - ring_i, 0, 1)
    back = ring * (Y < 33); front = ring * (Y >= 33)
    rh = R.prof(ring, 'round', r=2.5, amp=1.0)
    R.put(back, 'bronze', 0.42, z=4, h=rh, tex=R.speck(9, 0.06), spec=0.25, gloss=10)
    inner = ring_i * (Y < 40)
    gd = np.hypot((X - CX) / 40, (Y - 33) / 6.2)
    R.put(inner * (Y < 33), 'glow', 0.0, z=3, prof='flat', lit=0.0, emis=0.0, tex=np.clip(0.75 - gd * 0.75, 0, 1) ** 1.3)
    R.put(front, 'bronze', 0.55, z=44, h=rh, tex=R.speck(9, 0.06), spec=0.35, gloss=10)
    # rays of the halo (short bronze spikes on the back arc)
    for i in range(13):
        a = math.pi * (0.06 + 0.88 * i / 12)
        x0 = CX - math.cos(a) * 46; y0 = 33 - math.sin(a) * 9.5; x1 = CX - math.cos(a) * 52; y1 = 33 - math.sin(a) * 17
        sp = R.tube([(x0, y0), (x1, y1)], 2.6, 0.8); R.put(sp * (R.a < 0.5), 'bronze', 0.5, z=3, prof='round', r=1, spec=0.2)
    # hands gripping the front of the ring
    for sx in (-1, 1):
        hx = CX + sx * 41
        hand = R.ell(hx, 38.5, 4.6, 5.4); R.put(hand, 'marble', 0.66, z=48, prof='dome', r=4.5, tex=stone * 0.4)
        for f in range(3):
            fy = 35 + f * 2.4
            R.carve(R.line([(hx - 3.6, fy), (hx + 3.6, fy + 0.6)], 0.5), 0.6, -0.12)
        thumb = R.tube([(hx - sx * 3, 33), (hx - sx * 1, 30.5)], 2.6); R.put(thumb, 'marble', 0.68, z=47, prof='round', r=1.2)

    # ---------------------------------------------------------------- drowned: algae, tide stains, barnacles (below y 96)
    cav = np.clip((blur(R.hgt, 2.5 * S) - R.hgt) / 2.0, 0, 1)
    horiz = np.clip(-np.gradient(blur(R.hgt, S), axis=0) * S * 0.5, 0, 1)          # upward-facing ledges catch the growth
    grow = smoothstep(120, 400, Y) * 0.55 + cav * 0.7 + horiz * 0.5
    clump = vnoise(R.W, R.H, 7 * S, 21, 3, 0.7, 2.2)
    alg = (grow + (clump - 0.5) * 1.1 > 0.62) & (R.a > 0.5) & (Y > 100) & (R.mat == 0)
    R.mat = np.where(alg, 1, R.mat)
    R.val = np.where(alg, 0.30 + 0.5 * clump, R.val)
    # tide lines across the plinth and robe
    for ty in (150, 228, 300):
        band = np.abs(Y - ty - 2 * np.sin(X / 11.0)) < 0.9
        R.val = np.where(band & (R.a > 0.5), R.val - 0.10, R.val)
    rng = np.random.default_rng(5)
    for (gx, gy, n, sp) in ((24, 400, 9, 9), (150, 396, 8, 8), (40, 344, 5, 6), (132, 360, 6, 8), (70, 326, 5, 10), (112, 330, 4, 8), (160, 340, 3, 5)):
        for _ in range(n):
            x = gx + rng.normal(0, sp); y = gy + rng.normal(0, sp * 0.6)
            if not (2 < x < 174 and 250 < y < 414): continue
            if y < 334 and abs(x - CX) > robe_half(y) - 2: continue
            r = rng.uniform(1.3, 2.4)
            b = R.ell(x, y, r, r * 0.9)
            R.put(b * (R.a > 0.5), 'barn', 0.62, z=float(R.hgt[min(int(y * S), R.H - 1), min(int(x * S), R.W - 1)]) + 1.5, prof='dome', r=r, cover=0.6)
            R.carve(R.ell(x + 0.2, y + 0.2, r * 0.35, r * 0.3), 1.0, -0.4)

    lv = R.light(L=(-0.3, -0.85, 0.55), amb=0.44, key=0.98, ao=0.7, shadow=0.55, shadow_len=14,
                 rim=((0.9, -0.2), 0.10), point=(CX, 26, 30, 70, 0.35), fill=((0.6, 0.2, 0.6), 0.10))
    lv = lv * (1 - 0.14 * smoothstep(200, 416, Y)) * 1.08      # deeper = darker
    return R, lv


def rosewin():
    W = H = 160
    R = Rel(W, H, S=4, mats=[('stone', STONE), ('glass', GLASS, True), ('glass2', GLASS2, True), ('glass3', GLASS3, True), ('lead', LEAD)])
    X, Y = R.X, R.Y; cx = cy = 80
    rr = np.hypot(X - cx, Y - cy); th = np.arctan2(Y - cy, X - cx)
    st = R.stone(31, 0.06, 4)
    # outer moulded ring (three rolls)
    outer = R.ell(cx, cy, 79, 79)
    R.put(outer, 'stone', 0.55, z=6, h=1.8 * np.cos(np.clip((rr - 70) / 9, -1, 1) * math.pi * 1.5) ** 2 + 2, tex=st)
    # the glass field
    field = R.ell(cx, cy, 70, 70)
    n12 = 12
    a = (th / (2 * math.pi) * n12) % 1.0
    # petal (pointed trefoil) lancets between the spokes, each a different glass, a central rosette
    gtex = R.speck(33, 0.08, 2.2) + (vnoise(R.W, R.H, 14 * R.S, 34, 2) - 0.5) * 0.25
    # light falls through the glass from above-left: the pane value grades by angle
    glow = 0.55 + 0.25 * np.cos(th + math.pi * 0.7) - 0.25 * smoothstep(40, 70, rr)
    # glass families by tracery zone: amber heart, blue ring, pale-teal roundels, deep-teal outer lancets
    rd = np.full((R.H, R.W), 99.0)
    for k in range(n12):
        t = k / n12 * 2 * math.pi; rd = np.minimum(rd, np.hypot(X - cx - math.cos(t) * 47, Y - cy - math.sin(t) * 47))
    zone = np.where(rr < 23, 0, np.where(rd < 10.5, 2, np.where(rr < 36, 1, 3)))
    gsel = (field > 0.5)
    for z, mat, base in ((0, 'glass3', 0.55), (1, 'glass2', 0.5), (2, 'glass', 0.62), (3, 'glass', 0.38)):
        sel = gsel & (zone == z)
        R.put(sel.astype(float), mat, base, z=0, prof='flat', tex=gtex + glow - 0.55, lit=0.25)
    # tracery: 12 spokes, a ring of foiled roundels at r=48, an inner ring at r=24, cusps
    spokes = np.zeros((R.H, R.W))
    for k in range(n12):
        t = (k + 0.5) / n12 * 2 * math.pi
        spokes = np.maximum(spokes, R.tube([(cx + math.cos(t) * 22, cy + math.sin(t) * 22), (cx + math.cos(t) * 70, cy + math.sin(t) * 70)], 3.6, 4.4))
    rings = np.clip(R.ell(cx, cy, 72, 72) - R.ell(cx, cy, 68.5, 68.5), 0, 1)
    rings = np.maximum(rings, np.clip(R.ell(cx, cy, 25.5, 25.5) - R.ell(cx, cy, 22, 22), 0, 1))
    for k in range(n12):
        t = k / n12 * 2 * math.pi; px, py = cx + math.cos(t) * 47, cy + math.sin(t) * 47
        rings = np.maximum(rings, np.clip(R.ell(px, py, 12.5, 12.5) - R.ell(px, py, 10, 10), 0, 1))
        # quatrefoil cusps in each roundel
        for j in range(4):
            u = t + j * math.pi / 2
            rings = np.maximum(rings, R.ell(px + math.cos(u) * 7.5, py + math.sin(u) * 7.5, 2.6, 2.6) * (1 - R.ell(px + math.cos(u) * 4.5, py + math.sin(u) * 4.5, 3.6, 3.6)))
        # pointed arch heads between the spokes at r=60
        t2 = (k) / n12 * 2 * math.pi
        for s in (-1, 1):
            u0 = t2 + s * 0.2
            rings = np.maximum(rings, R.tube([(cx + math.cos(t2) * 62, cy + math.sin(t2) * 62), (cx + math.cos(u0) * 56, cy + math.sin(u0) * 56),
                                              (cx + math.cos(t2 + s * 0.26) * 36, cy + math.sin(t2 + s * 0.26) * 36)], 2.0))
    trac = np.clip(np.maximum(spokes, rings), 0, 1) * field
    R.put(trac, 'stone', 0.52, z=4, prof='round', r=1.6, tex=st)
    # leading inside the glass (thin dark cames: a radial + concentric grid)
    came = ((np.abs(((rr / 11.0) % 1) - 0.5) > 0.465) | (np.abs((((th / (2 * math.pi)) * 24) % 1) - 0.5) > 0.47)) & gsel & (R.mat != 0) & (zone != 2)
    for k in range(n12):      # a cross in each roundel
        t = k / n12 * 2 * math.pi; px, py = cx + math.cos(t) * 47, cy + math.sin(t) * 47
        came |= ((np.abs(X - px) < 0.35) | (np.abs(Y - py) < 0.35)) & (np.hypot(X - px, Y - py) < 10) & gsel
    R.mat = np.where(came, R.mat_ix['lead'], R.mat); R.val = np.where(came, 0.35, R.val); R.lit_k = np.where(came, 1.0, R.lit_k)
    # central boss: a bronze-dark stone flower
    boss = R.ell(cx, cy, 11, 11); R.put(boss, 'stone', 0.6, z=7, prof='dome', r=10, tex=st)
    for k in range(8):
        t = k / 8 * 2 * math.pi; R.carve(R.line([(cx + math.cos(t) * 3, cy + math.sin(t) * 3), (cx + math.cos(t) * 10, cy + math.sin(t) * 10)], 0.8), 1.0, -0.1)
    # broken panes: a few holes in the lower right (the sea came in this way)
    for (bx, by, br) in ((112, 116, 7), (100, 128, 5), (124, 100, 4)):
        hole = R.ell(bx, by, br, br * 0.8) * (R.mat > 0) * (R.mat != R.mat_ix['lead']) * (field > 0.5)
        R.val = np.where(hole > 0.5, 0.05, R.val)
    lv = R.light(L=(-0.4, -0.6, 0.7), amb=0.4, key=0.7, ao=0.55, shadow=0.4, shadow_len=6)
    return R, lv


PROMPT_SAINT = ('dark fantasy pixel art, a drowned marble statue of a veiled female saint holding a bronze halo above her head, '
                'serene carved face with closed eyes, heavy draped robe with deep folds, long hanging sleeves, carved stone plinth, '
                'weathered wet marble, algae stains, barnacles, cold teal light from above, soulslike, muted palette, sharp detail')
PROMPT_ROSE = ('dark fantasy pixel art, a gothic rose window of carved stone tracery, stained glass in muted teal, cold blue and pale amber, '
               'lead cames, drowned cathedral, weathered stone, soulslike, muted palette, front view, sharp detail')


def main():
    R, lv = saint(); save_dbg(R, 'saint', lv)
    # the AI pass mangles her face and flattens the folds at every denoise tried (0.3-0.5, see docs/v17/props_b.md):
    # the saint is the relief model alone
    lv2 = lv
    im = R.pixels(lv2, outline_lit=C('151e1b'), dither=0.25)
    im.save(os.path.join(SRC, 'saint_px.png'))
    W2, lvw = rosewin(); save_dbg(W2, 'rosewin', lvw)
    lvw2 = ai_detail('rosewin', W2, PROMPT_ROSE, seed=5, denoise=0.4, cn=0.7, cn_end=0.8, k_hp=0.35, k_lf=0.0, hp_sigma=1.0)
    save_dbg(W2, 'rosewin_ai', lvw2)
    imw = W2.pixels(lvw2, outline_lit=C('0a1215'), rim_step=0, dither=0.2)
    imw.save(os.path.join(SRC, 'rosewin_px.png'))
    if '--nobuild' not in sys.argv:
        build_sheet('xsa_saint', {'saint': [im]})
        build_sheet('xsa_rosewin', {'rosewin': [imw]})


if __name__ == '__main__':
    main()
