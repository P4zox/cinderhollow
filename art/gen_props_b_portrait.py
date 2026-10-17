#!/usr/bin/env python3
"""Batch B: the Countess's family portrait (xsa_portrait/familyportrait, 80x64, CM13 wall centrepiece).

A dark oil painting in a carved gilt frame, in the manner of the cm_portrait a-e paintings: the Count in black on the
left, his hand on the back of her chair; the Countess (Sanguine) in crimson at the centre, taller than life; the
child Rosalind in white lace on the right. A single candle key from the left, the ground near-black, the faces pale,
dim and a little wrong (dark eye hollows; hers hold two red points).

Run: python3 art/gen_props_b_portrait.py [--render] [--noai]
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props_b_lib import *   # noqa
from props_b_crimson_pal import *   # noqa

W, H = 80, 64
PRED = ramp('16040a', '22060c', '340a12', '4a101e', '5e1420', '74202a', '8a3034', 'a04440')   # a painted, varnished red
FX0, FY0, FX1, FY1 = 6, 6, 74, 58      # the canvas inside the frame


def face(R, cx, cy, rx, ry, v=0.62, eyes=0.0, red=False, z=8):
    """a painted face: oval dome, brow, nose, eye hollows, mouth, lit from the left."""
    X, Y = R.X, R.Y
    m = R.ell(cx, cy, rx, ry)
    u = (X - cx) / rx; w = (Y - cy) / ry
    h = R.prof(m, 'sphere', amp=0.9)
    nose = np.exp(-(u / 0.16) ** 2) * smoothstep(-0.35, 0.0, w) * (1 - smoothstep(0.25, 0.4, w)) * rx * 0.35
    sock = -np.exp(-(((np.abs(u) - 0.38) / 0.22) ** 2 + ((w + 0.08) / 0.16) ** 2)) * rx * 0.55
    mouth = -np.exp(-((u / 0.3) ** 2 + ((w - 0.5) / 0.07) ** 2)) * rx * 0.3
    R.put(m, 'flesh', v, z=z, h=h + nose + sock + mouth, tex=R.speck(int(cx * 7 + cy), 0.03, 0.6))
    # the hollows read darker than the light alone makes them
    hol = np.exp(-(((np.abs(u) - 0.38) / 0.2) ** 2 + ((w + 0.06) / 0.13) ** 2)) * (m > 0.5)
    R.val = R.val - hol * (0.22 + eyes)
    if red:
        for sx in (-1, 1):
            e = R.ell(cx + sx * rx * 0.38, cy - ry * 0.06, 0.55, 0.45)
            R.put(e, 'red', 0.9, z=z + 2, prof='flat', lit=0.0)
    return m


def portrait():
    R = Rel(W, H, S=6, mats=[('canvas', CANVAS), ('gilt', GILT), ('flesh', FLESH), ('red', PRED), ('black', BLACK), ('linen', LINEN),
                             ('hairb', HAIRB), ('wood', WOOD)])
    X, Y, S = R.X, R.Y, R.S
    brush = vnoise(R.W, R.H, 2.2 * S, 3, 3, 3.0, 0.6) - 0.5          # horizontal-ish brush drag
    brush2 = vnoise(R.W, R.H, 1.6 * S, 4, 2, 0.6, 2.5) - 0.5
    # ------------------------------------------------ the ground: a dim room, a curtain swag at left, a column at right
    can = R.rect(FX0, FY0, FX1, FY1)
    glowbg = np.exp(-(((X - 34) / 26) ** 2 + ((Y - 20) / 18) ** 2))
    R.put(can, 'canvas', 0.22, z=0, prof='flat', tex=glowbg * 0.35 + brush * 0.12 + brush2 * 0.06)
    swag = R.poly([(FX0, FY0), (30, FY0), (26, 10), (18, 14), (12, 22), (10, 36), (FX0, 44)])
    R.put(swag, 'red', 0.22, z=1, prof='round', r=2.5, tex=0.12 * np.sin((X + Y * 0.5) / 2.2) + brush * 0.1)
    col = R.rect(62, FY0, 70, FY1); R.put(col, 'canvas', 0.40, z=1, prof='cylx', amp=0.5, tex=brush * 0.1)
    R.put(R.rect(60, 12, 72, 14), 'canvas', 0.46, z=2, prof='cyly', amp=0.6)
    floor = R.rect(FX0, 50, FX1, FY1); R.put(floor, 'canvas', 0.30, z=0.5, prof='flat', tex=brush * 0.1 - smoothstep(50, 58, Y) * 0.1)
    # ------------------------------------------------ the Countess's chair back (behind her), the Count's hand on it
    chair = R.poly([(30, 22), (31, 17), (40, 13.5), (49, 17), (50, 22), (50, 40), (30, 40)])
    R.put(chair, 'wood', 0.45, z=2, prof='round', r=1.5, tex=brush * 0.1)
    R.put(R.ell(40, 14.2, 2.0, 1.4), 'gilt', 0.6, z=3, prof='dome', r=1.5)
    # ------------------------------------------------ the Count (left): black coat, white stock, slicked hair
    coat = R.poly([(12, FY1), (13, 36), (14, 29), (17, 26), (21, 25), (25, 26), (28, 29), (30, 36), (31, FY1)])
    R.put(coat, 'black', 0.5, z=4, prof='round', r=2.0, tex=brush * 0.08 + 0.12 * np.exp(-((X - 16) / 3) ** 2))
    lap = R.poly([(18, 26.5), (21, 30), (21, 40), (19, 34)]); R.shade(lap > 0.5, 0.18)
    stock = R.poly([(19.5, 25), (22.5, 25), (22, 29), (21, 31), (20, 29)]); R.put(stock, 'linen', 0.55, z=5, prof='round', r=0.8)
    face(R, 21, 19.5, 3.6, 4.6, v=0.55, eyes=0.12, z=6)
    hair = R.poly([(17.2, 19), (17.6, 15.5), (19.5, 14.2), (22.5, 14.0), (24.6, 15.5), (24.8, 18), (23.5, 16.4), (20, 16.2), (18.2, 17.5)])
    R.put(hair, 'black', 0.45, z=7, prof='round', r=1.0, tex=0.1 * np.sin(X * 3))
    hand = R.ell(30, 23.6, 1.8, 1.3); R.put(hand, 'flesh', 0.55, z=7, prof='dome', r=1.5)
    arm = R.tube([(26, 28), (29.5, 24.2)], 2.6); R.put(arm * (hand < 0.5), 'black', 0.5, z=6.5, prof='round', r=1.2)
    # ------------------------------------------------ the Countess (centre): crimson gown, pale shoulders, piled black hair
    skirt = R.poly([(25, FY1), (28, 46), (32, 36), (35, 31), (45, 31), (48, 36), (52, 46), (55, FY1)])
    sk_u = (X - 40) / np.maximum(4 + (Y - 31) * 0.45, 1)
    sk_f = (0.5 - 0.5 * np.cos(2 * math.pi * sk_u * 1.2)) * 1.6 * smoothstep(34, 44, Y)
    R.put(skirt, 'red', 0.38, z=8, h=R.prof(skirt, 'round', r=3) + sk_f, tex=brush * 0.08)
    bod = R.poly([(35.5, 31.5), (35.3, 25), (37, 22.8), (43, 22.8), (44.7, 25), (44.5, 31.5)])
    R.put(bod, 'red', 0.44, z=9, prof='cylx', amp=0.5, tex=brush * 0.06)
    dec = R.poly([(36.6, 23.2), (43.4, 23.2), (42, 26.5), (40, 27.2), (38, 26.5)]); R.put(dec, 'flesh', 0.68, z=9.5, prof='round', r=1.0)
    neck = R.rect(38.9, 19.8, 41.1, 23.4); R.put(neck, 'flesh', 0.6, z=9.2, prof='cylx', amp=0.5)
    R.put(R.ell(40, 25.0, 0.8, 0.9), 'red', 0.95, z=10, prof='dome', r=1, lit=0.6)           # the ruby
    for sx in (-1, 1):                                                                          # sleeves and gloved hands
        sl = R.tube([(40 + sx * 4.6, 24), (40 + sx * 5.8, 29), (40 + sx * 3, 33)], 2.8, 2.2)
        R.put(sl, 'red', 0.5, z=10, prof='round', r=1.2)
    R.put(R.ell(40, 33.2, 2.4, 1.3), 'flesh', 0.5, z=11, prof='dome', r=1.2)                  # folded hands
    face(R, 40, 15.6, 3.7, 4.8, v=0.72, eyes=0.05, red=True, z=12)
    up = R.poly([(35.6, 15.5), (36, 11.5), (38, 9.6), (40, 9.0), (42, 9.6), (44, 11.5), (44.4, 15.5), (43.3, 13), (40, 11.6), (36.7, 13)])
    R.put(up, 'black', 0.5, z=13, prof='dome', r=2.0, tex=0.08 * np.sin(X * 2.4 + Y))
    R.put(R.ell(40, 8.0, 2.3, 1.8), 'black', 0.52, z=13.5, prof='dome', r=2)
    for sx in (-1, 1):
        lock = R.tube([(40 + sx * 3.9, 15), (40 + sx * 4.4, 19), (40 + sx * 3.8, 22.5)], 1.2, 0.6)
        R.put(lock, 'black', 0.45, z=13, prof='round', r=0.6)
    # ------------------------------------------------ the child (right): white lace, pale hair, too still
    dress = R.poly([(52, FY1), (53, 47), (55, 40), (57, 37), (61, 37), (63, 40), (65, 47), (66, FY1)])
    lace = 0.04 * (np.sin(Y * 3.2 + X * 0.8) > 0.7) * smoothstep(48, 54, Y)
    R.put(dress, 'linen', 0.62, z=8, prof='round', r=2.2, tex=brush * 0.06 + lace)
    face(R, 59, 32.0, 2.7, 3.4, v=0.66, eyes=0.18, z=10)
    hb = R.poly([(56, 32.5), (56.2, 29.5), (57.6, 28.2), (60.4, 28.2), (61.8, 29.5), (62, 33.5), (61.5, 36.5), (60.8, 31), (58, 30), (56.8, 34)])
    R.put(hb, 'hairb', 0.5, z=11, prof='round', r=1.0)
    # varnish darkening toward the edges of the canvas (an old painting)
    vig = smoothstep(18, 40, np.hypot((X - 40) * 0.9, (Y - 30) * 1.3))
    # ------------------------------------------------ the gilt frame
    out = R.rect(0, 0, 80, 64); inn = R.rect(FX0, FY0, FX1, FY1)
    fr = np.clip(out - inn, 0, 1)
    d_out = np.minimum.reduce([X, Y, 80 - X, 64 - Y])                                  # distance from the outer edge
    along = np.where(np.minimum(X, 80 - X) < np.minimum(Y, 64 - Y), Y, X)               # position along the moulding
    roll = np.sqrt(np.clip(1 - ((d_out - 0.8) / 0.8) ** 2, 0, 1)) * 1.2
    chan = (np.abs(d_out - 1.9) < 0.35) * -0.6
    torus = np.sqrt(np.clip(1 - ((d_out - 3.3) / 1.1) ** 2, 0, 1)) * 1.6
    leaf = torus * 0.45 * (0.5 + 0.5 * np.sin(2 * math.pi * along / 3.0 + d_out * 1.2))
    bead = (np.abs(d_out - 4.85) < 0.5) * 0.7 * (np.cos(2 * math.pi * along / 1.6) > -0.2)
    sight = np.clip(1 - (d_out - 5.3) / 0.7, 0, 1) * 0.4 * (d_out > 5.3)
    R.put(fr, 'gilt', 0.7, z=10, h=roll + chan + torus + leaf + bead + sight, tex=R.speck(41, 0.025, 0.8))
    R.shade((fr > 0.5) & (np.abs(d_out - 1.9) < 0.4), -0.25)
    R.shade((fr > 0.5) & (d_out > 5.4), -0.2)
    # corner cartouches (acanthus bosses) and a crest at the top centre
    for (cx, cy) in ((3.2, 3.2), (76.8, 3.2), (3.2, 60.8), (76.8, 60.8)):
        R.put(R.ell(cx, cy, 3.6, 3.6), 'gilt', 0.62, z=12, prof='dome', r=3, tex=R.speck(43, 0.08, 0.5))
        R.carve(R.ell(cx, cy, 1.2, 1.2), 0.6, -0.15)
    crest = R.poly([(34, 0.2), (40, -0.5), (46, 0.2), (44, 3.4), (40, 4.6), (36, 3.4)])
    R.put(crest, 'gilt', 0.66, z=12, prof='dome', r=2.5, tex=R.speck(44, 0.08, 0.5))
    lip = np.clip(R.rect(FX0 - 1, FY0 - 1, FX1 + 1, FY1 + 1) - inn, 0, 1)
    R.put(lip, 'gilt', 0.4, z=8, prof='round', r=0.6)
    lv = R.light(L=(-0.75, -0.5, 0.45), amb=0.32, key=1.0, ao=0.5, shadow=0.6, shadow_len=5)
    inside = inn > 0.5
    lv = np.where(inside, lv * (1 - 0.35 * vig), lv)
    return R, lv


PROMPT = ('dark oil painting, old masters portrait of a vampire noble family in a gilded frame, a lord in black, a pale lady in a crimson gown, '
          'a pale child in white lace, candlelight, chiaroscuro, craquelure, dark gothic, muted palette, pixel art')


def main():
    R, lv = portrait(); save_dbg(R, 'portrait', lv)
    lv2 = ai_detail('portrait', R, PROMPT, seed=21, denoise=0.38, cn=0.8, cn_end=0.85, k_hp=0.45, k_lf=0.0, hp_sigma=0.8, pix=0.3)
    # keep the faces and the frame exactly as modelled
    keep = np.zeros_like(lv, bool)
    for (cx, cy, rx, ry) in ((21, 19.5, 4.4, 5.4), (40, 15.6, 4.5, 5.6), (59, 32.0, 3.4, 4.2)):
        keep |= R.ell(cx, cy, rx, ry) > 0.2
    keep |= R.mat == R.mat_ix['gilt']
    lv2 = np.where(keep, lv, lv2)
    save_dbg(R, 'portrait_ai', lv2)
    im = R.pixels(lv2, outline=False, rim_step=0, edge_dark=False, dither=0.0)
    im.save(os.path.join(SRC, 'portrait_px.png'))
    if '--nobuild' not in sys.argv:
        build_sheet('xsa_portrait', {'familyportrait': [im]})


if __name__ == '__main__':
    main()
