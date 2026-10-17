#!/usr/bin/env python3
"""Batch B: Crimson Manor furniture and fittings, xsa_cm (64x64, bottom-centre, laundry hangs top-centre), docs/v17/props_b.md.

Reworked tags (the old ones were flat rectangles): bookcase, bookcase_fallen, books, bed, wardrobe, hearth (3f), bellboard,
desk, globe, cot, stove (2f), lamp_cm (4f), laundry, roses, pipes, piano, chimney, weathervane, gutterspout, bust, rug,
canvasback, spyhole. Kept pixel-exact from v1: grandclock, crows, trellis, chalk (scored acceptable, not in the batch).

Every prop is a relief model (art/props_b_lib.py) lit by the manor's candle key from the upper left, palette-locked to the
crimson ramps (art/props_b_crimson_pal.py), with the region's 08070c outline. Fire and glass glow are unlit emissive parts;
animated tags rebuild only the flames/glow per frame on the same model.

Run: python3 art/gen_props_b_crimson.py [--only tag,tag] [--nobuild]
"""
import math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props_b_lib import *   # noqa
from props_b_crimson_pal import *   # noqa

MARBLE = ramp('0e0a0e', '1a1218', '2a1c24', '3c2a32', '523a42', '6c4e56', '8a6a70', 'a88c90')   # the red-black mantel marble
PALE = ramp('1a161c', '2a2430', '3e3846', '585266', '767088', '9690a6', 'b8b2c4', 'd8d4e0')   # white marble (busts)
MATS = [('wood', WOOD), ('oak', OAK), ('red', RED), ('gilt', GILT), ('iron', IRON), ('stone', STONE), ('marble', MARBLE), ('brick', BRICK), ('linen', LINEN),
        ('paper', PAPER), ('black', BLACK), ('green', GREEN), ('sky', SKY), ('glassg', GLASSG), ('fire', FIRE, False), ('ember', EMBER, False),
        ('flesh', FLESH), ('pale', PALE)]
OL = C(OUTLIT)


def new(w=64, h=64, S=4):
    return Rel(w, h, S, mats=MATS)


def lit(R, **kw):
    a = dict(L=(-0.6, -0.65, 0.5), amb=0.44, key=1.05, ao=0.55, shadow=0.5, shadow_len=6, rim=((1.0, 0.0), 0.06))
    a.update(kw); return R.light(**a)


def px(R, lv=None, **kw):
    a = dict(outline_lit=OL, dither=0.3); a.update(kw)
    return R.pixels(lv, **a)


# =============================================================================================== library
BOOKC = [('red', 0.52), ('red', 0.4), ('oak', 0.55), ('oak', 0.42), ('black', 0.7), ('green', 0.58), ('sky', 0.62), ('linen', 0.5), ('wood', 0.62)]


def shelf_books(R, x0, x1, base, hmax, seed, gap_p=0.08, lean_end=True, z=4):
    rng = np.random.default_rng(seed); x = x0
    while x < x1 - 1.2:
        w = rng.uniform(1.6, 3.2)
        if x + w > x1: w = x1 - x
        if rng.random() < gap_p: x += w; continue
        hh = rng.uniform(hmax * 0.68, hmax); mat, v = BOOKC[rng.integers(len(BOOKC))]
        v += rng.uniform(-0.06, 0.06)
        if lean_end and x + w > x1 - 4 and rng.random() < 0.6 and w > 2:   # the last one leans on its neighbour
            L = hh; ang = 0.32
            pts = [(x, base), (x + w * math.cos(ang), base - w * math.sin(ang) * 0.2), (x + w * math.cos(ang) - L * math.sin(ang), base - L * math.cos(ang)),
                   (x - L * math.sin(ang), base - L * math.cos(ang) + 0.6)]
            m = R.poly([(px_ + 2.6, py) for px_, py in pts])
            R.put(m, mat, v, z=z, prof='round', r=0.8); break
        m = R.rect(x, base - hh, x + w - 0.25, base)
        R.put(m, mat, v, z=z, prof='cylx', amp=0.7)
        for by in (base - hh + 1.2, base - 1.6):                                # gilt bands on the spine
            if rng.random() < 0.75:
                R.put(R.rect(x + 0.2, by, x + w - 0.45, by + 0.5) * (m > 0.5), 'gilt', 0.6, z=z + 0.6, prof='flat', add_h=False)
        if rng.random() < 0.4:
            R.put(R.rect(x + 0.4, base - hh * 0.62, x + w - 0.65, base - hh * 0.62 + 1.4) * (m > 0.5), 'black', 0.4, z=z + 0.3, prof='flat')
        x += w


def bookcase(fallen=False):
    R = Rel(128, 128, 4, mats=MATS, ox=32, oy=40) if fallen else new()
    wd = R.grain(5, 0.07, 'y', 6, 10)
    box(R, 14, 18, 50, 64, 'wood', 0.42, z=2, r=1.0, tex=wd)
    back = R.rect(17.5, 20, 46.5, 58); R.put(back, 'wood', 0.2, z=0.5, prof='flat', tex=R.grain(6, 0.04, 'y', 3, 12))
    rng = np.random.default_rng(9 + fallen)
    for i, sb in enumerate((31, 43, 55)):
        shelf_books(R, 18, 46.5, sb, 10.2, 30 + i * 7 + 50 * fallen, gap_p=0.35 if fallen else 0.08)
        box(R, 17, sb, 47, sb + 1.6, 'wood', 0.5, z=5, r=0.6, tex=wd)
    # pilasters with flutes, the cornice, the crest
    for x0 in (14, 46.5):
        box(R, x0, 19, x0 + 3.5, 58, 'wood', 0.5, z=6, r=1.0, tex=wd)
        R.carve(R.rect(x0 + 1.5, 23, x0 + 2.0, 54), 0.5, -0.12)
    corn = R.poly([(12, 17), (52, 17), (51, 20.5), (13, 20.5)]); R.put(corn, 'wood', 0.55, z=8, prof='cyly', amp=0.8, tex=wd)
    R.put(R.rect(11.5, 14.5, 52.5, 17.2), 'wood', 0.6, z=9, prof='cyly', amp=0.8, tex=wd)
    crest = R.poly([(26, 14.6), (28, 11.2), (32, 9.4), (36, 11.2), (38, 14.6)]); R.put(crest, 'wood', 0.55, z=9, prof='dome', r=2.0, tex=wd)
    R.put(R.ell(32, 12.2, 1.4, 1.4), 'gilt', 0.7, z=10, prof='dome', r=1.2)
    box(R, 13.5, 58, 50.5, 64, 'wood', 0.38, z=6, r=0.9, tex=wd)
    R.carve(R.rect(16, 60.5, 48, 61.0), 0.5, -0.12)
    R.put(R.ell(32, 60.8, 1.2, 0.7), 'gilt', 0.65, z=7, prof='dome', r=0.8)
    if not fallen:
        return R, lit(R)
    Q = rotate_rel(R, -80, (32, 40))
    ys, xs = np.nonzero(Q.a > 0.5); S = Q.S
    x0 = max(0, int(xs.max() // S) - 62); y0 = int(ys.max() // S) - 63
    Q = crop_rel(Q, x0, y0, 64, 64); R = new()
    # spilled books on the floor in front
    rng = np.random.default_rng(14)
    for i in range(7):
        x = rng.uniform(4, 30); w = rng.uniform(5, 8); hh = rng.uniform(1.6, 2.6); mat, v = BOOKC[rng.integers(len(BOOKC))]
        y1 = 64 - (i % 2) * 2.2 if x < 26 else 64
        m = R.poly([(x, y1), (x + w, y1 - rng.uniform(-0.8, 0.8)), (x + w, y1 - hh), (x, y1 - hh)])
        Q.put(m, mat, v, z=6 + i * 0.4, prof='round', r=0.7)
        Q.put(R.rect(x + 0.6, y1 - hh * 0.65, x + w - 0.3, y1 - hh * 0.35) * (m > 0.5), 'paper', 0.5, z=6.5 + i * 0.4, prof='flat')
    return Q, lit(Q)


def books():
    R = new(); rng = np.random.default_rng(8)
    # a toppled stack (left), a fanned open book (centre), loose leaves and two more books (right)
    y = 64
    for i, (x, w, hh) in enumerate(((10, 13, 2.6), (11, 12, 2.2), (10.5, 11, 2.4), (12, 10, 2.0))):
        mat, v = BOOKC[(i * 3 + 1) % len(BOOKC)]
        sk = (i - 1.5) * 0.6
        m = R.poly([(x + sk, y), (x + w + sk, y), (x + w + sk, y - hh), (x + sk, y - hh)])
        R.put(m, mat, v, z=2 + i * 2.5, prof='round', r=0.7)
        R.put(R.rect(x + sk + w - 1.4, y - hh + 0.5, x + sk + w - 0.3, y - 0.4) * (m > 0.5), 'paper', 0.5, z=2.4 + i * 2.5, prof='flat')
        y -= hh
    # the open book: two page blocks, the cover under them
    cov = R.poly([(25, 64), (43, 64), (42, 61.6), (26, 61.6)]); R.put(cov, 'red', 0.4, z=1, prof='round', r=0.6)
    for sx in (-1, 1):
        pg = R.poly([(34, 62.2), (34 + sx * 8.5, 62.6), (34 + sx * 8, 58.6), (34 + sx * 3, 57.6), (34, 59.4)])
        R.put(pg, 'paper', 0.58, z=3, prof='dome', r=2.0)
        for k in range(3):
            R.carve(R.line([(34 + sx * 2.0, 59.8 + k * 0.9), (34 + sx * 7.0, 59.6 + k * 0.9)], 0.35), 0.3, -0.1)
    # loose leaves
    for (x, yy, a) in ((45, 63.5, -0.15), (49, 62.8, 0.25), (20, 63.6, 0.1)):
        m = R.poly([(x, yy), (x + 5 * math.cos(a), yy - 5 * math.sin(a)), (x + 5 * math.cos(a) - 0.5, yy - 5 * math.sin(a) - 1.1), (x - 0.5, yy - 1.1)])
        R.put(m, 'paper', 0.5, z=1.5, prof='flat')
    for i, (x, w) in enumerate(((44, 9), (46, 7))):
        m = R.rect(x, 64 - 2.4 * (i + 1), x + w, 64 - 2.4 * i); R.put(m, ('black', 'green')[i], 0.5, z=2 + i * 2.4, prof='round', r=0.7)
    return R, lit(R)


# =============================================================================================== bedroom
def bed():
    R = new(); wd = R.grain(11, 0.07, 'x', 6, 10)
    # headboard (left), carved, with a gilt crest; posts with finials
    hb = R.poly([(5, 62), (5, 33), (7, 30), (9.5, 28.5), (12, 30), (14, 33), (14, 62)])
    R.put(hb, 'wood', 0.55, z=2, prof='round', r=1.2, tex=R.grain(12, 0.07, 'y', 6, 10))
    panel(R, 6.6, 34, 12.4, 46, 'wood', 0.55, z=2.5, inset=1.0, arch=True)
    turned(R, 5.2, [(26.5, 1.0), (27.5, 1.6), (29, 1.0), (31, 1.6), (64, 1.6)], 'wood', 0.5, z=5, tex=wd)
    turned(R, 13.8, [(28.5, 0.9), (29.5, 1.4), (31, 1.0), (32.5, 1.4), (64, 1.4)], 'wood', 0.48, z=4.5, tex=wd)
    R.put(R.ell(9.5, 31.5, 1.4, 1.4), 'gilt', 0.7, z=6, prof='dome', r=1.2)
    # footboard (right), lower
    fb = R.poly([(53.5, 62), (53.5, 43), (56, 41.2), (58.5, 43), (58.5, 62)]); R.put(fb, 'wood', 0.42, z=3, prof='round', r=1.2, tex=wd)
    turned(R, 59, [(38.5, 1.0), (39.5, 1.5), (41, 1.0), (42.5, 1.5), (64, 1.5)], 'wood', 0.5, z=5, tex=wd)
    # mattress, the white sheet, two pillows, the crimson velvet coverlet over the side with a gilt fringe
    box(R, 13, 45, 55, 52, 'pale', 0.62, z=6, r=2.0)
    for (x, w) in ((15, 10), (21, 9)):
        R.put(R.ell(x + w / 2, 43.2, w / 2, 3.0), 'pale', 0.78, z=8 + (x == 15), prof='dome', r=3)
    cov = R.poly([(23, 44.6), (36, 43.6), (54, 44.2), (55.5, 46), (55.5, 57.5), (50, 58.5), (44, 57.6), (38, 58.6), (31, 57.8), (25, 58.4), (22, 57.4), (21, 47)])
    u = (R.X - 22) / 4.6 + 0.3 * np.sin(R.Y / 3.0)
    folds = (0.5 - 0.5 * np.cos(2 * math.pi * u)) ** 1.5 * 1.6 * smoothstep(46, 52, R.Y)
    R.put(cov, 'red', 0.5, z=10, h=R.prof(cov, 'round', r=2.4) + folds, tex=R.speck(13, 0.03, 0.8) + 0.05 * np.sin(R.X * 2.4) * smoothstep(48, 58, R.Y))
    turn = R.poly([(22, 46.4), (36, 45.2), (54.5, 45.8), (54.5, 47.4), (36, 46.9), (22, 48.2)]); R.put(turn, 'pale', 0.75, z=11, prof='round', r=0.8)
    fr = (np.abs(R.Y - (58.4 + 0.5 * np.sin(R.X * 1.2))) < 0.75) & (R.X > 21.5) & (R.X < 55.4)
    R.put(fr.astype(float), 'gilt', 0.55, z=11, prof='flat')
    for x in np.arange(22.5, 55, 1.5):
        R.put(R.rect(x, 58.4, x + 0.5, 60.0 + (int(x * 3) % 2) * 0.6), 'gilt', 0.45, z=11, prof='flat')
    # side rail and the shadow under the bed
    box(R, 13, 57, 54, 60, 'wood', 0.35, z=4, r=0.7, tex=wd)
    return R, lit(R)


def wardrobe():
    R = new(); wd = R.grain(17, 0.06, 'y', 6, 10)
    box(R, 16, 15, 48, 60, 'wood', 0.38, z=2, r=1.0, tex=wd)
    for x0 in (18.2, 32.6):
        panel(R, x0, 18.5, x0 + 13.2, 37, 'wood', 0.44, z=3, inset=2.0, arch=True, tex=wd)
        panel(R, x0, 38.5, x0 + 13.2, 56.5, 'wood', 0.44, z=3, inset=2.0, tex=wd)
    R.carve(R.rect(31.7, 18, 32.3, 57), 0.8, -0.2)                         # the meeting of the doors
    for sx in (-1, 1):                                                       # escutcheons
        R.put(R.ell(32 + sx * 1.6, 38, 0.9, 1.3), 'gilt', 0.62, z=6, prof='dome', r=1)
    # cornice with a broken pediment and a gilt urn
    R.put(R.poly([(14, 15.5), (50, 15.5), (49, 12.6), (15, 12.6)]), 'wood', 0.52, z=6, prof='cyly', amp=0.8, tex=wd)
    for sx in (-1, 1):
        R.put(R.poly([(32 + sx * 2.2, 12.8), (32 + sx * 15.5, 12.8), (32 + sx * 15.5, 11.4), (32 + sx * 3.4, 8.6), (32 + sx * 2.2, 9.6)]), 'wood', 0.5, z=6.5, prof='round', r=1.0, tex=wd)
    turned(R, 32, [(6.0, 0.6), (6.6, 1.2), (7.6, 1.8), (9.0, 1.4), (10.6, 0.7), (12.8, 1.6)], 'gilt', 0.55, z=8)
    box(R, 15, 59.5, 49, 61.5, 'wood', 0.42, z=5, r=0.6, tex=wd)
    for x in (18.5, 45.5):
        R.put(R.ell(x, 62.6, 2.2, 1.6), 'wood', 0.45, z=4, prof='dome', r=1.6)
    return R, lit(R)


# =============================================================================================== hearth (3 frames)
def hearth_model():
    R = new(); st = R.stone(21, 0.05, 4) + 0.06 * np.sin((R.X * 0.7 + R.Y * 0.4) + 3 * vnoise(R.W, R.H, 6 * R.S, 25, 3))
    # firebox: soot-black brick behind, an iron fire-back with a crest
    fb = R.rect(17, 33, 47, 63); R.put(fb, 'brick', 0.2, z=0, prof='flat', tex=R.stone(22, 0.05, 2) - smoothstep(48, 34, R.Y) * 0.1)
    for yy in np.arange(35, 63, 2.6):
        R.carve(R.rect(17, yy, 47, yy + 0.35), 0.3, -0.06)
    back = R.poly([(24, 61), (24, 44), (27, 40.5), (32, 39.5), (37, 40.5), (40, 44), (40, 61)]); R.put(back, 'iron', 0.28, z=1, prof='round', r=1.0)
    R.put(R.ell(32, 46, 3.0, 3.4), 'iron', 0.34, z=1.6, prof='dome', r=2.5)
    # stone surround: jambs (pilasters with capitals), a segmental arch, the frieze and the mantel shelf
    for x0 in (8.5, 46.5):
        box(R, x0, 31, x0 + 9, 62, 'marble', 0.5, z=4, r=1.0, tex=st)
        box(R, x0 + 1.5, 34, x0 + 7.5, 59, 'marble', 0.55, z=5, r=0.8, tex=st)
        R.carve(R.rect(x0 + 4.2, 36, x0 + 4.8, 57), 0.6, -0.1)
        box(R, x0 - 0.5, 30.5, x0 + 9.5, 33.5, 'marble', 0.6, z=6, r=0.8, tex=st)
    arch = np.clip(R.rect(17, 30, 47, 37) - R.ell(32, 46, 17.5, 12.5), 0, 1)
    R.put(arch, 'marble', 0.52, z=4, prof='round', r=1.0, tex=st)
    for k in range(-3, 4):    # voussoir joints
        a = math.pi / 2 + k * 0.17
        R.carve(R.line([(32 + math.cos(a) * 12.6, 46 - math.sin(a) * 12.6 * 0.72), (32 + math.cos(a) * 16, 46 - math.sin(a) * 16 * 0.72)], 0.4), 0.4, -0.08)
    R.put(R.poly([(29.5, 33.4), (34.5, 33.4), (33.6, 37.2), (30.4, 37.2)]), 'marble', 0.62, z=6, prof='round', r=1.0, tex=st)   # keystone
    fri = R.rect(8, 27.6, 56, 31); R.put(fri, 'marble', 0.5, z=5, prof='cyly', amp=0.6, tex=st)
    for x in np.arange(10, 55, 4):
        R.put(R.ell(x + 1, 29.3, 1.0, 1.0), 'marble', 0.55, z=6, prof='dome', r=1)
    R.put(R.poly([(6, 27.8), (58, 27.8), (57.4, 25), (6.6, 25)]), 'marble', 0.62, z=7, prof='cyly', amp=0.8, tex=st)
    R.put(R.rect(5.5, 24.0, 58.5, 25.4), 'marble', 0.66, z=8, prof='cyly', amp=0.6, tex=st)
    # on the shelf: two candlesticks and a skull
    for x in (12, 52):
        turned(R, x, [(19.5, 0.5), (20, 0.9), (22, 0.6), (23.6, 1.6), (24.2, 1.8)], 'gilt', 0.55, z=9)
        R.put(R.rect(x - 0.5, 16.5, x + 0.5, 19.6), 'linen', 0.62, z=9.5, prof='cylx', amp=0.5)
    R.put(R.ell(22, 22.2, 2.6, 2.2), 'linen', 0.5, z=9, prof='dome', r=2.2)
    R.put(R.rect(20.6, 22.5, 23.4, 24.2), 'linen', 0.45, z=9, prof='round', r=0.6)
    for sx in (-1, 1): R.carve(R.ell(22 + sx * 0.9, 22.3, 0.55, 0.6), 0.8, -0.35)
    # andirons, logs, embers bed, the hearth slab
    for x in (21, 43):
        turned(R, x, [(52.5, 0.8), (53.5, 1.2), (55, 0.8), (60, 0.8), (62, 1.6)], 'iron', 0.42, z=6)
    for (x0, y0, x1, y1, w) in ((21, 59.5, 42, 58.3, 3.0), (23, 61.2, 44, 61.4, 2.8)):
        lg = R.tube([(x0, y0), (x1, y1)], w); R.put(lg, 'oak', 0.3, z=5, prof='cyly', amp=0.8, tex=R.grain(24, 0.06, 'x'))
    hs = R.rect(7, 62.2, 57, 64); R.put(hs, 'marble', 0.55, z=3, prof='round', r=0.6, tex=st)
    return R


def hearth_frames():
    out = []
    for f in range(3):
        R = hearth_model()
        bed_m = R.ell(32, 61.8, 10.5, 1.6); R.put(bed_m * (R.mat != R.mat_ix['marble']), 'ember', 0.0, z=5.5, prof='flat', lit=0.0,
                                                 tex=0.65 + 0.35 * np.sin(R.X * 2.3 + f * 2.1))
        rng = np.random.default_rng(3 + f)
        for i, x in enumerate((24.5, 27.5, 30.5, 33.5, 36.5, 39.5)):
            hh = 8 + 6 * math.sin(i * 1.7 + f * 2.0) ** 2 + (3 if i in (2, 3) else 0)
            flame(R, x + rng.uniform(-0.5, 0.5), 60, hh, 1.9 + 0.5 * (i in (2, 3)), seed=i, phase=f * 2.2 + i, z=12)
        lv = lit(R, point=(32, 54, 8, 26, 0.55))
        R.lv = lv
        out.append(px(R, lv))
    return out


# =============================================================================================== servants' hall
def bellboard():
    R = new(); wd = R.grain(31, 0.06, 'x', 6, 10)
    box(R, 30, 50, 34, 62, 'wood', 0.42, z=2, r=1.0, tex=wd)            # the post
    R.put(R.poly([(23, 64), (41, 64), (39, 61.6), (25, 61.6)]), 'wood', 0.4, z=3, prof='round', r=0.8, tex=wd)
    bd = R.poly([(10, 52), (10, 36), (13, 33.5), (28, 33.5), (32, 31.2), (36, 33.5), (51, 33.5), (54, 36), (54, 52)])
    R.put(bd, 'wood', 0.52, z=4, prof='round', r=1.2, tex=wd)
    R.carve(np.clip(R.rect(12, 36, 52, 50.5) - R.rect(12.8, 36.8, 51.2, 49.7), 0, 1), 0.6, -0.12)
    R.put(R.ell(32, 33.5, 1.4, 1.4), 'gilt', 0.65, z=6, prof='dome', r=1.2)
    for i in range(6):
        x = 17 + (i % 3) * 15; y = 39.5 + (i // 3) * 6.5
        R.put(R.tube([(x - 3.5, y - 2), (x - 2.0, y - 2.8), (x - 0.8, y - 1.6)], 0.6), 'iron', 0.5, z=6, prof='round', r=0.3)   # spring arm
        turned(R, x, [(y - 2.8, 0.6), (y - 2.2, 1.6), (y - 1.0, 2.0), (y + 0.4, 2.2), (y + 1.4, 3.0), (y + 2.0, 3.3)], 'gilt', 0.72 - (i == 3) * 0.14, z=7, spec=0.5, gloss=10)
        R.put(R.ell(x, y + 2.2, 0.6, 0.5), 'gilt', 0.35, z=7.2, prof='dome', r=0.5)
        R.put(R.rect(x - 3.0, y + 3.0, x + 3.0, y + 4.4), 'paper', 0.66, z=6, prof='round', r=0.4)
    return R, lit(R)


def desk():
    R = new(); wd = R.grain(41, 0.06, 'x', 6, 10)
    for x0 in (9, 41):
        box(R, x0, 41, x0 + 14, 63, 'wood', 0.38, z=2, r=0.9, tex=wd)
        for k in range(3):
            panel(R, x0 + 1.2, 42.5 + k * 6.6, x0 + 12.8, 48.4 + k * 6.6, 'wood', 0.44, z=2.5, inset=1.0, tex=wd)
            R.put(R.ell(x0 + 7, 45.5 + k * 6.6, 1.1, 0.7), 'gilt', 0.6, z=5, prof='dome', r=0.8)
        box(R, x0 - 0.5, 62, x0 + 14.5, 64, 'wood', 0.32, z=3, r=0.5)
    R.put(R.rect(23, 41, 41, 45), 'wood', 0.34, z=1.5, prof='round', r=0.6, tex=wd)          # the apron over the kneehole
    R.put(R.poly([(7, 41.4), (57, 41.4), (57.6, 39.2), (6.4, 39.2)]), 'wood', 0.55, z=5, prof='cyly', amp=0.8, tex=wd)
    R.put(R.rect(7.6, 37.8, 56.4, 39.4), 'red', 0.4, z=5.5, prof='cyly', amp=0.4)               # the leather writing surface edge
    # papers, an open ledger, the inkwell and quill, the candle (the light: x+8, y-30)
    R.put(R.poly([(20, 38), (35, 38), (36, 36.6), (21, 36.0)]), 'paper', 0.6, z=7, prof='flat')
    for sx in (-1, 1):
        R.put(R.poly([(28, 37.8), (28 + sx * 7, 37.4), (28 + sx * 6.6, 35.2), (28, 35.8)]), 'paper', 0.66, z=8, prof='dome', r=1.2)
    R.carve(R.rect(27.8, 35.6, 28.2, 37.8), 0.3, -0.15)
    R.put(R.ell(14.5, 36.6, 2.0, 1.6), 'black', 0.5, z=7, prof='dome', r=1.6, spec=0.5, gloss=20)
    R.put(R.rect(13.8, 34.4, 15.2, 35.4), 'black', 0.5, z=7, prof='flat')
    q = R.tube([(15, 35), (18.4, 28.5), (19.6, 26.2)], 1.2, 0.4); R.put(q, 'linen', 0.62, z=9, prof='round', r=0.6)
    turned(R, 40, [(35.6, 0.5), (36.4, 1.2), (37.4, 0.6), (38.2, 1.8), (38.8, 2.2)], 'gilt', 0.55, z=8, spec=0.3)
    R.put(R.rect(39.3, 30.8, 40.7, 35.8), 'linen', 0.62, z=8.5, prof='cylx', amp=0.5)
    R.put(R.poly([(40.7, 31), (41.4, 33.5), (40.7, 33)]), 'linen', 0.58, z=8.6, prof='flat')       # wax run
    return R


def desk_px():
    R = desk(); flame(R, 40, 30.9, 3.6, 0.9, seed=2, phase=0.4, z=12)
    lv = lit(R, point=(40, 29, 6, 22, 0.5)); R.lv = lv; return px(R, lv)


def globe():
    R = new(); wd = R.grain(51, 0.06, 'y', 5, 8)
    # tripod stand and turned column
    for (x0, x1) in ((24, 30), (40, 34)):
        R.put(R.tube([(x0, 63.5), ((x0 + x1) / 2, 61.5), (x1, 58)], 1.6, 1.4), 'wood', 0.42, z=3, prof='round', r=0.8, tex=wd)
    turned(R, 32, [(49.5, 1.2), (51, 1.8), (53, 1.2), (55.5, 2.2), (57, 1.4), (59.5, 2.4), (60.5, 1.6)], 'wood', 0.48, z=5, tex=wd)
    R.put(R.tube([(32, 60), (32, 64)], 1.6), 'wood', 0.4, z=4, prof='round', r=0.8)
    # the horizon ring (behind) and the meridian (in front), brass
    hz_b = np.clip(R.ell(32, 41, 12.6, 3.0) - R.ell(32, 41, 11.4, 2.2), 0, 1) * (R.Y < 41)
    R.put(hz_b, 'gilt', 0.45, z=2, prof='round', r=0.6, spec=0.3)
    # the sphere: ocean, old-parchment lands mapped onto it, a terminator from the candle light
    cx, cy, r = 32, 39.5, 9.2
    sp = R.ell(cx, cy, r, r)
    u = np.clip((R.X - cx) / r, -0.999, 0.999); v = np.clip((R.Y - cy) / r, -0.999, 0.999)
    lon = np.arcsin(np.clip(u / np.sqrt(np.maximum(1 - v * v, 1e-3)), -1, 1) * 0.999) + 0.4; lat = np.arcsin(v)
    land = vnoise(400, 200, 22, 55, 3)
    li = np.clip(((lon / math.pi + 0.5) * 399).astype(int) % 400, 0, 399); lj = np.clip(((lat / math.pi + 0.5) * 199).astype(int), 0, 199)
    ld = land[lj, li] > 0.55
    R.put(sp, 'sky', 0.45, z=6, prof='sphere', amp=1.0, spec=0.25, gloss=16, tex=R.speck(56, 0.04, 0.8))
    R.mat = np.where((sp > 0.5) & ld, R.mat_ix['linen'], R.mat); R.val = np.where((sp > 0.5) & ld, 0.48, R.val)
    gr = ((np.abs(((lon * 6 / math.pi) % 1) - 0.5) > 0.47) | (np.abs(((lat * 6 / math.pi) % 1) - 0.5) > 0.47)) & (sp > 0.5)
    R.val = np.where(gr, R.val - 0.08, R.val)
    mer = np.clip(R.ell(cx, cy, 11.2, 11.2) - R.ell(cx, cy, 10.0, 10.0), 0, 1) * (R.X < cx + 1)
    R.put(mer, 'gilt', 0.58, z=14, prof='round', r=0.6, spec=0.4, gloss=10)
    hz_f = np.clip(R.ell(32, 41, 12.6, 3.0) - R.ell(32, 41, 11.4, 2.2), 0, 1) * (R.Y >= 41)
    R.put(hz_f, 'gilt', 0.6, z=15, prof='round', r=0.6, spec=0.3)
    R.put(R.rect(31.4, 27.4, 32.6, 29.6), 'gilt', 0.6, z=15, prof='cylx', amp=0.5)
    R.put(R.tube([(32, 49.5), (32, 51)], 1.4), 'gilt', 0.5, z=6, prof='round', r=0.6)
    return R, lit(R)


# =============================================================================================== servants' wing
def cot():
    R = new()
    box(R, 11.5, 51, 52.5, 55.5, 'linen', 0.62, z=4, r=1.6)                           # thin straw mattress
    bl = R.poly([(22, 50.4), (52.6, 50.6), (53.2, 52), (53, 56.4), (49, 57.2), (41, 56.6), (33, 57.3), (24, 56.8), (21.6, 52)])
    R.put(bl, 'stone', 0.72, z=6, h=R.prof(bl, 'round', r=2) + 0.6 * np.sin(R.X / 1.6) * smoothstep(52, 55, R.Y), tex=R.speck(61, 0.04))
    R.put(R.poly([(43, 50.2), (52.8, 50.3), (52.8, 52.2), (43, 52.6)]), 'stone', 0.78, z=7.5, prof='round', r=1.0)    # the fold at the foot
    R.put(R.ell(16.5, 50.2, 5.0, 1.9), 'pale', 0.78, z=7, prof='dome', r=2)
    # iron frame: rails, legs, a bent head rail
    for y in (55.6,):
        R.put(R.tube([(10.5, y), (53.5, y)], 1.2), 'iron', 0.6, z=8, prof='cyly', amp=0.8)
    for x in (11, 53):
        R.put(R.tube([(x, 55), (x, 63.6)], 1.2), 'iron', 0.58, z=8, prof='cylx', amp=0.8)
    R.put(R.tube([(10.5, 55.5), (10.5, 48.5), (11.5, 47.4), (14, 47.4), (15, 48.5), (15, 52)], 1.0), 'iron', 0.62, z=9, prof='round', r=0.5)
    R.put(R.tube([(53.5, 55.5), (53.5, 51.2)], 1.0), 'iron', 0.62, z=9, prof='round', r=0.5)
    return R, lit(R)


def stove_model():
    R = new(); ir = R.speck(71, 0.03, 0.8)
    for x in (19, 44): R.put(R.tube([(x, 58), (x - (x < 30) * 0.8 + (x > 30) * 0.8, 63.6)], 1.6, 2.0), 'iron', 0.38, z=2, prof='round', r=0.8)
    box(R, 16, 37.5, 47, 59, 'iron', 0.36, z=3, r=1.6, tex=ir)
    R.put(R.rect(14.5, 35.2, 48.5, 38.2), 'iron', 0.5, z=5, prof='cyly', amp=0.7, tex=ir)
    R.put(R.rect(15, 56.8, 48, 58.6), 'iron', 0.45, z=4, prof='cyly', amp=0.6)
    panel(R, 33, 41, 45, 55.5, 'iron', 0.4, z=4, inset=1.4)                          # oven door
    R.put(R.tube([(35, 43.4), (43, 43.4)], 1.0), 'gilt', 0.6, z=7, prof='cyly', amp=0.6, spec=0.4)
    fd = R.rect(19, 42, 30.5, 53.5); R.put(fd, 'iron', 0.42, z=4, prof='round', r=1.0)
    R.put(R.ell(24.7, 41.6, 1.2, 0.8), 'gilt', 0.55, z=6, prof='dome', r=0.8)
    # the flue: up from the back, an elbow, a damper
    R.put(R.tube([(39.5, 35.6), (39.5, 22.5)], 4.0), 'iron', 0.38, z=1, prof='cylx', amp=0.8, tex=ir)
    R.put(R.tube([(39.5, 18.6), (39.5, 22.8)], 4.6), 'iron', 0.42, z=1.5, prof='cylx', amp=0.8)
    R.put(R.ell(39.5, 29, 2.6, 0.7), 'iron', 0.5, z=2, prof='dome', r=0.6)
    # the kettle
    turned(R, 24.5, [(30.0, 0.6), (30.6, 1.2), (31.4, 3.2), (33.0, 4.4), (35.0, 4.2)], 'iron', 0.5, z=8, spec=0.35, gloss=12)
    R.put(R.tube([(28.6, 33.2), (31.6, 31.0), (32.4, 30.2)], 1.0, 0.7), 'iron', 0.5, z=8, prof='round', r=0.5)
    R.put(R.tube([(21.6, 31.4), (22.4, 28.6), (26.6, 28.6), (27.4, 31.4)], 0.6), 'iron', 0.45, z=7.6, prof='round', r=0.3)
    return R


def stove_frames():
    out = []
    for f in range(2):
        R = stove_model()
        gl = R.rect(20.5, 46.5, 29, 52)                      # the grate in the firebox door: embers glow through
        bars = (np.abs(((R.X - 20.5) / 1.7) % 1 - 0.5) > 0.33) & (gl > 0.5)
        R.put(gl, 'ember', 0.0, z=4.5, prof='flat', lit=0.0, tex=(0.85 if f else 0.65) - 0.4 * smoothstep(52, 46.5, R.Y) + 0.12 * np.sin(R.X * 3 + f * 2))
        R.mat = np.where(bars, R.mat_ix['iron'], R.mat); R.val = np.where(bars, 0.35, R.val); R.lit_k = np.where(bars, 1.0, R.lit_k)
        lv = lit(R, point=(25, 50, 6, 18, 0.35 + 0.1 * f)); R.lv = lv; out.append(px(R, lv))
    return out


def lamp_model():
    R = new()
    R.put(R.poly([(27, 64), (37, 64), (35.6, 61.6), (28.4, 61.6)]), 'iron', 0.4, z=2, prof='round', r=0.8)
    turned(R, 32, [(39.5, 0.6), (40.2, 1.1), (41.4, 0.7), (56, 0.7), (58, 1.2), (60.5, 1.6), (61.8, 2.2)], 'iron', 0.45, z=3)
    # the lantern: a hipped cap with a finial, four glass panes in an iron cage, a drip-pan
    R.put(R.poly([(26.8, 31.6), (37.2, 31.6), (34.4, 28.8), (29.6, 28.8)]), 'iron', 0.45, z=6, prof='round', r=1.0)
    turned(R, 32, [(25.6, 0.5), (26.3, 0.9), (27.2, 0.5), (28.9, 1.0)], 'iron', 0.5, z=7)
    R.put(R.rect(27.6, 31.6, 36.4, 38.6), 'fire', 0.0, z=4, prof='flat', lit=0.0)
    for x in (27.6, 31.6, 35.6):
        R.put(R.rect(x, 31.6, x + 0.8, 38.6), 'iron', 0.42, z=6, prof='cylx', amp=0.5)
    R.put(R.poly([(26.6, 38.4), (37.4, 38.4), (35.6, 40.4), (28.4, 40.4)]), 'iron', 0.4, z=6, prof='round', r=0.8)
    return R


def lamp_frames():
    out = []
    for f in (0, 1, 2, 1):
        R = lamp_model()
        pane = (R.mat == R.mat_ix['fire'])
        g = np.clip(0.42 + 0.12 * f - np.hypot(R.X - 32, (R.Y - 36) * 1.2) * 0.05, 0.1, 1)
        R.val = np.where(pane, g, R.val)
        flame(R, 32, 37.6, 3.0 + 0.6 * f, 0.9, phase=f, z=5)
        R.mat = np.where(pane & (R.val < 0.2), R.mat_ix['ember'], R.mat)
        for x in (27.6, 31.6, 35.6):   # bars over the flame
            m = R.rect(x, 31.6, x + 0.8, 38.6) > 0.5
            R.mat = np.where(m, R.mat_ix['iron'], R.mat); R.val = np.where(m, 0.42, R.val); R.lit_k = np.where(m, 1.0, R.lit_k)
        lv = lit(R, point=(32, 35, 4, 14, 0.5)); R.lv = lv; out.append(px(R, lv))
    return out


def laundry():
    R = new()
    line = [(0, 2.0), (16, 3.2), (32, 3.8), (48, 3.4), (63.9, 2.4)]
    sag = lambda x: np.interp(x, [p[0] for p in line], [p[1] for p in line])
    R.put(R.tube(line, 0.7), 'linen', 0.32, z=2, prof='round', r=0.3)
    X, Y = R.X, R.Y
    items = [(2.5, 15.5, 'linen', 0.58, 15, 'shirt'), (18, 27.5, 'red', 0.42, 12, 'skirt'), (30.5, 44.5, 'linen', 0.52, 21, 'sheet'), (47, 58, 'black', 0.5, 13, 'cloth')]
    for x0, x1, mat, v, ln, kind in items:
        top0 = float(sag(x0)) + 0.4; top1 = float(sag(x1)) + 0.4
        hem = lambda x: top0 + (top1 - top0) * (x - x0) / (x1 - x0) + ln + 0.9 * math.sin(x * 1.3)
        xs = np.linspace(x0, x1, 12)
        pts = [(x0, top0), (x1, top1)] + [(x, hem(x)) for x in xs[::-1]]
        if kind == 'shirt':   # sleeves out to the sides, a collar
            pts = [(x0 + 2, top0), (x1 - 2, top1), (x1 + 0.6, top1 + 5.5), (x1 - 1.6, top1 + 6.4), (x1 - 2, top1 + ln)] + \
                  [(x, hem(x)) for x in np.linspace(x1 - 2.2, x0 + 2.2, 8)] + [(x0 + 2, top0 + ln), (x0 + 1.6, top0 + 6.4), (x0 - 0.6, top0 + 5.5)]
        if kind == 'skirt':
            pts = [(x0 + 1.5, top0), (x1 - 1.5, top1), (x1 + 0.6, top1 + ln)] + [(x, hem(x)) for x in np.linspace(x1, x0, 9)] + [(x0 - 0.6, top0 + ln)]
        m = R.poly(pts)
        u = (X - x0) / 2.6 + 0.2 * np.sin(Y / 2)
        fold = (0.5 - 0.5 * np.cos(2 * math.pi * u)) ** 1.4 * 1.2 * smoothstep(top0 + 2, top0 + 8, Y)
        R.put(m, mat, v, z=4, h=R.prof(m, 'round', r=1.6) + fold, tex=R.speck(int(x0) + 80, 0.03))
        for xp in (x0 + 1.4, x1 - 1.4):           # pegs
            R.put(R.rect(xp - 0.5, float(sag(xp)) - 0.8, xp + 0.5, float(sag(xp)) + 1.6), 'oak', 0.55, z=6, prof='round', r=0.3)
    if True:   # a lace edge on the shirt cuffs and a darned patch on the sheet
        R.put(R.ell(38, 15, 2.2, 1.8), 'linen', 0.42, z=5, prof='round', r=0.6)
    return R, lit(R, L=(-0.5, -0.75, 0.45))


def roses():
    R = new(); st = R.stone(91, 0.05, 3)
    turned(R, 32, [(48.0, 7.4), (49.0, 8.0), (50.2, 7.6), (52.0, 6.4), (55.0, 4.8), (57.0, 3.2), (58.5, 2.6), (60.5, 3.0), (61.4, 5.4), (64, 5.6)], 'marble', 0.52, z=4, tex=st)
    R.carve(R.rect(24.6, 51.6, 39.4, 52.2), 0.5, -0.1)
    R.put(R.ell(32, 48.3, 7.2, 1.0), 'brick', 0.18, z=5, prof='flat')                 # soil
    rng = np.random.default_rng(12)
    stems = []
    for i in range(9):
        x0 = 26.5 + i * 1.4 + rng.uniform(-0.5, 0.5); h = rng.uniform(12, 21); lean = rng.uniform(-6, 6)
        pts = [(x0, 48.4), (x0 + lean * 0.3, 48.4 - h * 0.45), (x0 + lean * 0.75, 48.4 - h * 0.8), (x0 + lean, 48.4 - h)]
        stems.append(pts)
        R.put(R.tube(pts, 0.7, 0.5), 'green', 0.32, z=6 + i * 0.2, prof='round', r=0.3)
        for t in (0.35, 0.6):     # thorns and leaves
            px_ = pts[1][0] + (pts[2][0] - pts[1][0]) * t; py = pts[1][1] + (pts[2][1] - pts[1][1]) * t
            if rng.random() < 0.6:
                s_ = 1 if rng.random() < 0.5 else -1
                R.put(R.poly([(px_, py), (px_ + s_ * 2.8, py - 1.4), (px_ + s_ * 1.6, py + 0.6)]), 'green', 0.45, z=7 + i * 0.2, prof='round', r=0.6)
    for i, pts in enumerate(stems):
        bx, by = pts[-1]; r = rng.uniform(1.6, 2.3) if i % 3 else 1.3
        if i == 4: by += 1   # one hangs its head
        R.put(R.ell(bx, by, r, r * 0.9), 'red', 0.36 + rng.uniform(-0.04, 0.06), z=10 + i * 0.3, prof='dome', r=r)
        R.carve(R.line([(bx - r * 0.5, by - r * 0.1), (bx + r * 0.3, by + r * 0.35)], 0.4), 0.4, -0.12)
        R.carve(R.line([(bx - r * 0.1, by - r * 0.55), (bx + r * 0.5, by - r * 0.1)], 0.4), 0.4, -0.1)
    for (x, y) in ((22, 63.4), (41, 63.5), (44.5, 63.2), (20, 63.6)):              # fallen petals
        R.put(R.ell(x, y, 0.9, 0.5), 'red', 0.35, z=2, prof='dome', r=0.5)
    return R, lit(R)


def pipes():
    R = new(); ir = R.speck(101, 0.03, 0.8); rust = vnoise(R.W, R.H, 3 * R.S, 102, 2, 0.6, 4.0)
    for x in (22, 29.2):
        R.put(R.rect(x - 1.9, 0, x + 1.9, 64), 'iron', 0.4, z=4, prof='cylx', amp=0.9, tex=ir + (rust > 0.62) * -0.12)
        for y in (13, 33, 53):
            R.put(R.rect(x - 2.5, y, x + 2.5, y + 1.6), 'iron', 0.46, z=5.5, prof='cylx', amp=0.9)
    for y in (9, 29, 49):     # wall brackets bolted across both
        R.put(R.rect(18, y, 33.2, y + 2.2), 'iron', 0.34, z=7, prof='cyly', amp=0.7)
        for x in (19.2, 32.0): R.put(R.ell(x, y + 1.1, 0.7, 0.7), 'iron', 0.55, z=8, prof='dome', r=0.6)
    # a branch to the right: tee, run, elbow down to a valve with a rusted wheel
    R.put(R.tube([(31, 38.5), (42.5, 38.5)], 3.2), 'iron', 0.42, z=3, prof='cyly', amp=0.9, tex=ir)
    R.put(R.tube([(42.5, 38.5), (42.5, 47)], 3.2), 'iron', 0.42, z=3, prof='cylx', amp=0.9)
    R.put(R.ell(42.5, 38.5, 2.6, 2.6), 'iron', 0.48, z=4, prof='dome', r=2)
    R.put(R.rect(39.8, 46, 45.2, 48.2), 'iron', 0.46, z=4.5, prof='cyly', amp=0.6)
    wheel = np.clip(R.ell(42.5, 43.5, 4.4, 4.4) - R.ell(42.5, 43.5, 3.2, 3.2), 0, 1)
    for k in range(4):
        a = k * math.pi / 2 + 0.4; wheel = np.maximum(wheel, R.tube([(42.5, 43.5), (42.5 + math.cos(a) * 3.6, 43.5 + math.sin(a) * 3.6)], 0.7))
    R.put(wheel, 'brick', 0.55, z=9, prof='round', r=0.5, spec=0.15)
    R.put(R.ell(42.5, 43.5, 1.0, 1.0), 'iron', 0.6, z=10, prof='dome', r=0.8)
    # a drip of rust water under the joint
    R.shade((np.abs(R.X - 42.8) < 0.5) & (R.Y > 48.2) & (R.Y < 50.5) & (R.a > 0.5), -0.1)
    return R, lit(R)


def piano():
    R = new(); lac = R.speck(111, 0.025, 1.0)
    # legs with casters, the lyre and pedals
    for x in (9.5, 33, 53):
        turned(R, x, [(45.5, 1.6), (47, 2.1), (49, 1.6), (56, 1.2), (59.5, 1.6), (61, 1.1), (62.4, 1.0)], 'black', 0.5, z=2, spec=0.4, gloss=18)
        R.put(R.ell(x, 63.0, 1.2, 1.0), 'gilt', 0.5, z=3, prof='dome', r=0.8)
    R.put(R.poly([(14.5, 46), (18.5, 46), (18, 58), (15, 58)]), 'black', 0.45, z=2.5, prof='round', r=0.8)
    for x in (15.2, 16.5, 17.8): R.put(R.rect(x - 0.3, 58, x + 0.4, 60.4), 'gilt', 0.55, z=3, prof='flat')
    # the case: straight at the keyboard, the bentside sweeping to the tail
    case = R.poly([(4, 45.4), (4, 37.6), (40, 37.6), (50, 38.0), (57, 39.4), (60.5, 41.6), (60.5, 44.0), (56, 46.4), (14, 46.4)])
    R.put(case, 'black', 0.55, z=4, prof='round', r=1.6, spec=0.9, gloss=18, tex=lac)
    R.put(R.tube([(5, 44.2), (40, 44.2), (52, 43.2), (59.5, 42.2)], 0.5), 'gilt', 0.5, z=6, prof='flat')       # an inlay line
    # the keyboard and its cheek blocks
    R.put(R.rect(2.4, 39.2, 14, 42.6), 'black', 0.5, z=6, prof='round', r=0.6)            # the keybed
    R.put(R.rect(2.8, 39.6, 13.6, 41.6), 'linen', 0.72, z=7, prof='flat')
    for x in np.arange(3.4, 13.4, 1.4):
        if int((x - 3.4) / 1.4) % 7 not in (2, 6): R.put(R.rect(x, 39.6, x + 0.7, 40.6), 'black', 0.3, z=8, prof='flat')
    R.put(R.rect(2.0, 36.6, 3.4, 41.6), 'black', 0.5, z=8, prof='round', r=0.6)
    # the music desk with a sheet, the raised lid on its prop stick
    R.put(R.poly([(13, 37.8), (19.8, 37.8), (19, 30.4), (14.4, 31.0)]), 'black', 0.48, z=3, prof='round', r=0.6)
    R.put(R.poly([(14.6, 36.4), (18.6, 36.4), (18.1, 31.4), (15.2, 31.8)]), 'paper', 0.55, z=3.6, prof='flat')
    for k in range(3): R.carve(R.rect(15.4, 32.6 + k * 1.2, 17.8, 32.9 + k * 1.2), 0.3, -0.12)
    R.put(R.tube([(42, 37.6), (45.6, 22.8)], 0.7), 'black', 0.5, z=1.2, prof='round', r=0.3)
    lid = R.poly([(20, 37.4), (21.2, 35.6), (57.6, 20.6), (60.6, 21.6), (58.4, 23.6), (23.6, 37.6)])
    R.put(lid, 'black', 0.6, z=1.6, prof='round', r=1.0, spec=0.9, gloss=18, tex=lac)
    # inside the lid: the gilt plate glimpsed under it
    R.put(R.poly([(24, 37.4), (56, 24.6), (57, 25.6), (27, 37.6)]), 'gilt', 0.4, z=1.0, prof='flat')
    return R, lit(R)


def chimney():
    R = new()
    stack = R.rect(20, 30, 44, 64)
    br = R.stone(121, 0.05, 2)
    R.put(stack, 'brick', 0.6, z=3, prof='round', r=1.0, tex=br)
    rows = np.floor((R.Y - 30) / 3.0); off = (rows % 2) * 3.0
    mort = ((((R.Y - 30) / 3.0) % 1) < 0.3) | ((((R.X - 20 + off) / 6.0) % 1) < 0.15)
    R.hgt = np.where(mort & (stack > 0.5), R.hgt - 0.8, R.hgt); R.val = np.where(mort & (stack > 0.5), R.val - 0.3, R.val)
    R.val = np.where(stack > 0.5, R.val - 0.18 * smoothstep(40, 30, R.Y), R.val)     # soot under the cap
    R.put(R.rect(18.5, 27.4, 45.5, 30.6), 'stone', 0.62, z=5, prof='cyly', amp=0.7)
    R.put(R.rect(19.5, 25.6, 44.5, 27.6), 'stone', 0.68, z=5.5, prof='cyly', amp=0.6)
    for x in (25, 32, 39):
        turned(R, x, [(16.6, 2.0), (17.4, 2.4), (18.6, 1.8), (21.6, 2.0), (24.5, 2.6), (25.8, 2.6)], 'brick', 0.55, z=7, tex=br)
        R.put(R.ell(x, 16.9, 1.5, 0.45), 'black', 0.1, z=8, prof='flat')
    return R, lit(R)


def weathervane():
    R = new()
    R.put(R.poly([(27, 64), (37, 64), (33.2, 57.4), (30.8, 57.4)]), 'iron', 0.4, z=2, prof='round', r=1.0)     # the roof mount
    R.put(R.rect(31.4, 22, 32.6, 58), 'iron', 0.45, z=3, prof='cylx', amp=0.6)
    R.put(R.tube([(23.5, 42), (40.5, 42)], 0.8), 'iron', 0.45, z=4, prof='cyly', amp=0.5)
    for x in (23.2, 40.8): R.put(R.ell(x, 42, 1.1, 1.1), 'gilt', 0.55, z=5, prof='dome', r=0.8)
    R.put(R.ell(32, 42, 1.4, 1.4), 'iron', 0.5, z=5, prof='dome', r=1.0)
    # the crow on its arrow
    R.put(R.tube([(22.5, 25.8), (42.5, 25.8)], 0.8), 'iron', 0.45, z=4, prof='cyly', amp=0.5)
    R.put(R.poly([(42, 24.2), (45.6, 25.8), (42, 27.4)]), 'iron', 0.5, z=4.5, prof='round', r=0.5)
    R.put(R.poly([(21.4, 23.6), (24.6, 25.8), (21.4, 28.0), (22.6, 25.8)]), 'iron', 0.45, z=4.5, prof='round', r=0.4)
    body = R.poly([(26, 25.4), (28, 22.2), (32, 20.8), (35.6, 21.6), (37.4, 20.4), (39.2, 20.8), (40.4, 21.8), (38.2, 22.6), (36.4, 24.4), (33, 25.6)])
    R.put(body, 'black', 0.5, z=6, prof='dome', r=1.6, spec=0.3)
    R.put(R.poly([(29, 22.4), (25.4, 19.6), (23.6, 20.4), (27, 23.6)]), 'black', 0.45, z=6.5, prof='round', r=0.6)    # tail
    R.put(R.ell(38.6, 21.2, 0.35, 0.35), 'red', 0.8, z=8, prof='flat', lit=0.0)
    R.put(R.rect(30.6, 25.4, 31.4, 26.6), 'black', 0.4, z=6, prof='flat'); R.put(R.rect(33.2, 25.4, 34.0, 26.6), 'black', 0.4, z=6, prof='flat')
    return R, lit(R)


def gutterspout():
    R = new(); st = R.stone(131, 0.06, 3)
    R.put(R.rect(11, 29, 18, 50.5), 'stone', 0.55, z=2, prof='round', r=1.0, tex=st)          # the corbel in the wall
    R.put(R.rect(10.5, 28, 18.6, 30.2), 'stone', 0.62, z=2.5, prof='cyly', amp=0.6)
    # the beast: crouched along the spout, wings folded, the head thrust out with open jaws
    body = R.poly([(15, 41), (17, 35.4), (24, 33.6), (34, 34), (40, 34.6), (42.6, 37.2), (40, 40.6), (30, 41.6), (22, 43.6), (17, 45)])
    R.put(body, 'stone', 0.62, z=5, prof='dome', r=3.0, tex=st)
    wing = R.poly([(19, 35.6), (22, 29.6), (27, 28.4), (31, 30.4), (33, 34.4), (26, 36.6)])
    R.put(wing, 'stone', 0.58, z=7, prof='dome', r=2.0, tex=st)
    for k in range(3): R.carve(R.line([(22 + k * 3, 30.4 + k * 0.4), (24 + k * 3, 35.4)], 0.4), 0.5, -0.12)
    for (x, y) in ((22, 44), (34, 41)):   # forelegs / claws gripping the corbel edge
        R.put(R.tube([(x, y - 2), (x + 1.4, y + 2.4), (x + 3.4, y + 3.0)], 2.0, 1.2), 'stone', 0.58, z=6, prof='round', r=1.0)
    head = R.poly([(39.6, 33.6), (43, 31.4), (47.6, 31.8), (52.4, 33.4), (55, 35.4), (52.4, 36.0), (47, 35.6), (43, 37.8)])
    R.put(head, 'stone', 0.66, z=8, prof='dome', r=2.0, tex=st)
    jaw = R.poly([(43.4, 37.6), (47.2, 37.6), (52.8, 38.2), (53.6, 39.6), (47, 40.2), (42.6, 39.6)])
    R.put(jaw, 'stone', 0.58, z=7.5, prof='round', r=1.0, tex=st)
    R.put(R.poly([(46, 35.6), (53.6, 36.2), (53, 37.8), (46, 37.6)]), 'black', 0.12, z=7.6, prof='flat')        # the throat
    for x in (48, 50, 52): R.put(R.poly([(x, 35.8), (x + 0.6, 37.2), (x + 1.0, 35.8)]), 'linen', 0.5, z=8, prof='flat')
    R.put(R.poly([(42.4, 31.8), (40.0, 27.6), (41.2, 27.8), (44.4, 31.2)]), 'stone', 0.52, z=9, prof='round', r=0.5)   # horn
    R.put(R.ell(46.4, 33.0, 0.6, 0.5), 'red', 0.85, z=10, prof='flat', lit=0.0)
    return R, lit(R)


def bust():
    R = new(); st = R.stone(141, 0.035, 3)
    turned(R, 32, [(40.0, 6.0), (41.4, 5.2), (42.4, 4.0), (44, 3.6), (57, 3.6), (58.6, 4.4), (60, 5.2), (61.6, 5.6), (64, 6.0)], 'stone', 0.55, z=2, tex=st)
    for x in (29.2, 32.0, 34.8): R.carve(R.rect(x - 0.25, 45.5, x + 0.25, 56), 0.4, -0.1)
    # the bust: shoulders and chest cut in a curve, a draped cloak, a cravat; the head turned a little left
    sh = R.poly([(20.6, 40.2), (21.0, 35.2), (23.4, 31.4), (27.6, 29.2), (32, 28.6), (36.6, 29.2), (40.6, 31.4), (43.0, 35.2), (43.4, 40.2), (38, 41.4), (32, 40.0), (26, 41.4)])
    u = np.arctan2(R.X - 32, np.maximum(R.Y - 26, 0.5))
    R.put(sh, 'pale', 0.62, z=4, h=R.prof(sh, 'dome', r=4.0) + 0.7 * np.sin(u * 8) * smoothstep(32, 37, R.Y), tex=st)
    R.put(R.poly([(23.0, 34.0), (27.6, 30.0), (30.0, 31.6), (27.0, 40.6), (22.0, 40.0)]), 'pale', 0.58, z=5, prof='dome', r=2.2, tex=st)   # cloak over the left shoulder
    R.put(R.poly([(29.4, 29.4), (34.6, 29.4), (33.6, 33.6), (32, 35.0), (30.4, 33.6)]), 'pale', 0.7, z=6, prof='round', r=1.0)
    R.put(R.rect(29.6, 24.6, 34.2, 29.8), 'pale', 0.58, z=5, prof='cylx', amp=0.6)
    X, Y = R.X, R.Y; cx, cy, rx, ry = 31.6, 19.6, 5.0, 6.2
    hm = R.ell(cx, cy, rx, ry); u = (X - cx) / rx; w = (Y - cy) / ry
    hh = R.prof(hm, 'sphere', amp=0.9)
    nose = np.exp(-((u + 0.15) / 0.15) ** 2) * smoothstep(-0.3, 0.05, w) * (1 - smoothstep(0.25, 0.42, w)) * rx * 0.45
    sock = -np.exp(-(((np.abs(u + 0.1) - 0.36) / 0.18) ** 2 + ((w + 0.08) / 0.13) ** 2)) * rx * 0.5
    mouth = -np.exp(-(((u + 0.1) / 0.25) ** 2 + ((w - 0.5) / 0.06) ** 2)) * rx * 0.25
    chin = np.exp(-(((u + 0.1) / 0.3) ** 2 + ((w - 0.78) / 0.12) ** 2)) * rx * 0.2
    R.put(hm, 'pale', 0.72, z=8, h=hh + nose + sock + mouth + chin, tex=st * 0.4)
    hair = R.poly([(26.4, 19.4), (26.6, 15.6), (28.6, 13.4), (32.0, 12.6), (35.4, 13.6), (37.2, 16.4), (37.0, 22.4), (35.6, 18.0), (32.6, 16.0), (28.8, 17.4), (27.6, 21.0)])
    R.put(hair, 'pale', 0.6, z=9, h=R.prof(hair, 'dome', r=1.8) + 0.6 * np.sin(X * 2.4 + Y * 1.6), tex=st)
    return R, lit(R, L=(-0.7, -0.6, 0.5), amb=0.42)


def rug():
    R = new()
    top = R.poly([(4.6, 63.2), (59.4, 63.2), (57.8, 60.2), (6.2, 60.2)])
    X, Y = R.X, R.Y
    border = (np.abs(Y - 60.9) < 0.45) | (np.abs(Y - 62.5) < 0.45)
    motif = (np.abs(((X - 4) / 6.0) % 1 - 0.5) < 0.16) & (np.abs(Y - 61.7) < 0.6)
    tex = 0.18 * border + 0.0 * motif + R.speck(151, 0.04, 0.8)
    R.put(top, 'red', 0.42, z=1, prof='round', r=0.6, tex=tex)
    R.mat = np.where(motif & (top > 0.5), R.mat_ix['gilt'], R.mat); R.val = np.where(motif & (top > 0.5), 0.5, R.val)
    R.put(R.rect(4.6, 63.2, 59.4, 64), 'red', 0.22, z=0.5, prof='flat')
    for x0, x1 in ((2.6, 4.8), (59.2, 61.4)):
        for yy in (60.6, 61.8, 63.0): R.put(R.rect(x0, yy, x1, yy + 0.6), 'linen', 0.45, z=1.2, prof='flat')
    R.hgt = np.where(top > 0.5, R.hgt + 1.0 * np.exp(-((X - 40) / 3.0) ** 2), R.hgt)        # a ruck in it
    return R, lit(R, L=(-0.5, -0.8, 0.4))


def canvasback():
    R = new(); wd = R.grain(161, 0.06, 'y', 5, 8)
    # the easel behind: two splayed legs and a back leg, the ledge
    for (a, b) in (((31.5, 17.5), (16, 64)), ((32.5, 17.5), (48, 64))):
        R.put(R.tube([a, b], 1.8), 'oak', 0.4, z=1, prof='round', r=0.8, tex=wd)
    R.put(R.rect(13, 53.4, 51, 55.6), 'oak', 0.45, z=5, prof='cyly', amp=0.6)
    # the canvas back between the stretcher bars, two eyeholes cut through it
    R.put(R.rect(13.4, 21.4, 50.6, 53.4), 'linen', 0.4, z=2, prof='flat', tex=R.speck(162, 0.03, 0.6) + 0.04 * np.sin(R.Y * 1.7))
    for (x0, y0, x1, y1) in ((12, 20.4, 52, 22.8), (12, 52, 52, 54.2), (12, 20.4, 14.4, 54.2), (49.6, 20.4, 52, 54.2)):
        R.put(R.rect(x0, y0, x1, y1), 'oak', 0.5, z=4, prof='round', r=0.8, tex=wd)
    for (a, b) in (((14, 22.4), (50, 52.6)), ((50, 22.4), (14, 52.6))):
        R.put(R.tube([a, b], 1.8), 'oak', 0.44, z=3.4, prof='round', r=0.8, tex=wd)
    R.put(R.rect(31, 21.6, 33, 53.6), 'oak', 0.46, z=3.8, prof='cylx', amp=0.6)
    for (x, y) in ((26.6, 34.6), (37.4, 34.6)):
        R.put(R.ell(x, y, 1.3, 1.0), 'black', 0.05, z=5, prof='flat', lit=0.0)
        R.put(R.ell(x + 0.3, y - 0.2, 0.35, 0.3), 'linen', 0.6, z=5.2, prof='flat', lit=0.0)
    R.put(R.rect(13.4, 21.4, 50.6, 23.0) * 0, 'linen', 0, z=0)
    return R, lit(R)


def spyhole():
    R = new(); wd = R.grain(171, 0.06, 'y', 5, 8)
    panel(R, 23, 24, 41, 45, 'wood', 0.42, z=2, inset=2.2, tex=wd)
    R.put(R.rect(26.6, 32.0, 37.4, 35.4), 'black', 0.2, z=3, prof='round', r=0.6)
    sl = R.rect(27.8, 32.8, 36.2, 34.6)
    R.put(sl, 'fire', 0.0, z=3.5, prof='flat', lit=0.0, tex=0.75 - np.abs(R.X - 32) * 0.08)
    R.put(R.ell(31.2, 33.7, 0.9, 0.6), 'black', 0.3, z=4, prof='flat', lit=0.0)                     # an eye, close behind it
    R.put(R.ell(31.4, 33.6, 0.35, 0.3), 'linen', 0.9, z=4.2, prof='flat', lit=0.0)
    R.put(R.rect(36.6, 31.4, 40.0, 36.0), 'gilt', 0.55, z=5, prof='round', r=0.6, spec=0.3)            # the slid-back cover
    R.put(R.ell(38.3, 33.7, 0.5, 0.5), 'gilt', 0.4, z=6, prof='dome', r=0.4)
    return R, lit(R, point=(32, 34, 3, 10, 0.4))


# =============================================================================================== xsa_chand: the fallen chandelier (112x64)
def fallen_chandelier():
    R = Rel(112, 64, 4, mats=MATS); rng = np.random.default_rng(201)
    cx, cy = 56, 52.5
    # chains from the ceiling (out of frame), slack, to the crown of the wreck
    for (x0, x1) in ((53, 54.6), (57, 57.2), (61, 59.4)):
        pts = [(x0 + 0.4 * math.sin(t * 9), t * (cy - 20)) for t in np.linspace(0, 1, 10)]
        pts[-1] = (x1, cy - 20)
        for i in range(len(pts) - 1):
            R.put(R.tube([pts[i], pts[i + 1]], 1.1), 'iron', 0.42 + 0.1 * (i % 2), z=2, prof='round', r=0.5)
    # the ring: a tilted gilt hoop crushed on its near side, arms snapped, candles scattered
    ring_o = R.ell(cx, cy, 47, 9.0); ring_i = R.ell(cx, cy - 1.4, 37, 3.6)
    ring = np.clip(ring_o - ring_i, 0, 1)
    back = ring * (R.Y < cy - 0.6); front = ring * (R.Y >= cy - 0.6)
    R.put(back, 'gilt', 0.75, z=4, prof='round', r=1.2, spec=0.4, gloss=10, tex=R.speck(202, 0.05))
    # the hub and its broken stem, toppled onto the ring
    turned(R, cx, [(cy - 20, 0.8), (cy - 19, 1.6), (cy - 17, 1.0), (cy - 13, 2.6), (cy - 10, 3.6), (cy - 7.5, 4.0), (cy - 5, 2.4), (cy - 3.4, 1.2)], 'gilt', 0.75, z=8, spec=0.5, gloss=10)
    for k, (dx, ln, up) in enumerate(((-30, 12, 1), (-17, 9, 1), (17, 11, 1), (31, 8, 1), (-24, 7, -1), (24, 9, -1))):
        x0 = cx + dx; y0 = cy - (2 if up > 0 else -3)
        x1 = x0 + (6 if dx < 0 else -6) * (0.4 + 0.4 * (k % 2)); y1 = y0 - ln * 0.7 * up
        R.put(R.tube([(x0, y0), ((x0 + x1) / 2, y0 - ln * 0.4 * up), (x1, y1)], 1.4, 1.0), 'gilt', 0.7, z=6 + k * 0.2, prof='round', r=0.6, spec=0.3)
        R.put(R.ell(x1, y1, 1.8, 0.9), 'gilt', 0.55, z=7 + k * 0.2, prof='dome', r=0.8)
        if up > 0:
            R.put(R.rect(x1 - 0.7, y1 - 4.5, x1 + 0.7, y1), 'linen', 0.68, z=7.5 + k * 0.2, prof='cylx', amp=0.5)
    # a crushed inner tier
    tier = np.clip(R.ell(cx + 3, cy - 4, 20, 4.2) - R.ell(cx + 3, cy - 4.6, 15.5, 2.2), 0, 1)
    R.put(tier, 'gilt', 0.75, z=9, prof='round', r=1.0, spec=0.4)
    for t in np.linspace(0.12, 0.88, 9):          # the candle cups still on the ring, a few candles left in them
        x = cx - math.cos(t * math.pi) * 43; y = cy + math.sin(t * math.pi) * 6.0
        R.put(R.ell(x, y - 0.4, 1.6, 0.9), 'gilt', 0.8, z=12, prof='dome', r=0.8)
        if int(t * 100) % 3 != 1: R.put(R.rect(x - 0.6, y - 4.6, x + 0.6, y - 0.6), 'linen', 0.7, z=12.5, prof='cylx', amp=0.5)
    R.put(front, 'gilt', 0.85, z=10, prof='round', r=1.4, spec=0.45, gloss=10, tex=R.speck(203, 0.05))
    beads = (np.abs(R.Y - (cy + 6.4 - 0.004 * (R.X - cx) ** 2)) < 0.6) & (np.cos(R.X * 2.2) > 0.3) & (front > 0.5)
    R.hgt = np.where(beads, R.hgt + 0.6, R.hgt)
    # crystal drops: hanging from the ring and scattered across the floor; snapped candles rolled away
    for i in range(30):
        t = rng.uniform(0.05, 0.95) * math.pi; x = cx - math.cos(t) * 44; y = cy + math.sin(t) * 7.2
        if rng.random() < 0.8: R.put(R.poly([(x - 0.8, y + 1), (x + 0.8, y + 1), (x, y + 3.6)]), 'pale', 0.85, z=11, prof='flat', spec=0.6)
    for i in range(46):
        x = rng.uniform(4, 108); y = rng.uniform(61.6, 63.8)
        if abs(x - cx) < 44 and y < 62.2: continue
        R.put(R.ell(x, y, rng.uniform(0.5, 1.1), 0.5), 'pale', rng.uniform(0.6, 0.9), z=3, prof='flat')
    for (x, a) in ((9, 0.1), (100, -0.12), (86, 0.2)):
        R.put(R.tube([(x, 63.2), (x + 4.5 * math.cos(a), 63.2 - 4.5 * math.sin(a))], 1.2), 'linen', 0.55, z=3, prof='round', r=0.5)
    return R, lit(R, point=(56, 46, 10, 40, 0.15))


# =============================================================================================== cm_table / cm_coffin / cm_winerack / cm_barrel
def table():
    R = Rel(64, 32, 4, mats=MATS)
    for x in (6, 58):
        turned(R, x, [(24, 1.4), (26, 1.8), (28, 1.2), (30.5, 1.6), (32, 1.8)], 'wood', 0.45, z=2)
    cloth = R.poly([(1.4, 15.4), (62.6, 15.4), (63.0, 25.6), (58, 26.6), (52, 25.8), (46, 26.8), (40, 25.9), (34, 26.9), (28, 25.8), (22, 26.8), (16, 25.9), (10, 26.7), (4, 25.8), (1.0, 26.6)])
    u = R.X / 5.2 + 0.2 * np.sin(R.Y)
    folds = (0.5 - 0.5 * np.cos(2 * math.pi * u)) ** 1.5 * 1.4 * smoothstep(17, 22, R.Y)
    dam = 0.07 * ((np.sin(R.X * 1.6) * np.sin(R.Y * 1.6)) > 0.45) * (R.Y > 17)
    R.put(cloth, 'black', 0.55, z=4, h=R.prof(cloth, 'round', r=1.6) + folds, tex=dam * 0.6 + R.speck(301, 0.03))
    R.put(R.rect(1.4, 14.2, 62.6, 16.4), 'black', 0.7, z=5, prof='cyly', amp=0.6)
    run = R.poly([(22, 14.4), (42, 14.4), (42, 24.6), (38, 25.6), (32, 24.8), (26, 25.6), (22, 24.6)])
    R.put(run, 'red', 0.4, z=4.6, h=R.prof(run, 'round', r=1.0) + folds, tex=dam)
    lace = (np.abs(R.Y - (25.8 + 0.5 * np.sin(R.X * 1.2))) < 0.6) & (cloth > 0.5)
    R.mat = np.where(lace, R.mat_ix['linen'], R.mat); R.val = np.where(lace, 0.42, R.val)
    # a spill of wine run down the cloth from a toppled goblet
    spill = R.poly([(40, 15.4), (44, 15.4), (43.2, 21), (42.6, 24.4), (41.8, 21)]); R.put(spill, 'red', 0.62, z=5.5, prof='round', r=0.6, spec=0.5)
    R.put(R.tube([(38.4, 14.2), (42.8, 13.4)], 1.6, 1.0), 'iron', 0.62, z=8, prof='round', r=0.6, spec=0.6)
    # the silver candelabrum at the centre (light: y-26), plates, goblets, a decanter
    turned(R, 32, [(6.0, 0.4), (7.0, 0.8), (9, 0.6), (10.5, 1.2), (12.4, 1.6), (13.6, 2.6), (14.4, 3.0)], 'iron', 0.6, z=9, spec=0.6)
    R.put(R.tube([(26, 7.4), (27, 9.6), (32, 10.6), (37, 9.6), (38, 7.4)], 0.8), 'iron', 0.6, z=9, prof='round', r=0.4, spec=0.5)
    for x in (26, 32, 38):
        R.put(R.rect(x - 0.6, 3.2 - (x == 32) * 1.2, x + 0.6, 7.4 - (x == 32) * 0.4), 'linen', 0.65, z=10, prof='cylx', amp=0.5)
    for x in (12, 20, 46, 54):
        turned(R, x, [(10.8, 1.1), (12.2, 0.9), (13, 0.3), (14.0, 0.3), (14.6, 1.0)], 'iron', 0.62, z=8, spec=0.6)
        R.put(R.ell(x + (4 if x < 32 else -4), 14.7, 2.6, 0.6), 'pale', 0.55, z=7, prof='round', r=0.4)
    turned(R, 50, [(7.4, 0.5), (8.4, 0.6), (10.4, 1.4), (12.4, 2.2), (14.4, 2.0)], 'glassg', 0.55, z=8.5, spec=0.8, gloss=20)
    R.put(R.rect(48.4, 11.6, 51.6, 14.2), 'red', 0.45, z=8.6, prof='cylx', amp=0.5)
    return R


def table_px():
    R = table()
    for i, x in enumerate((26, 32, 38)):
        flame(R, x, 3.4 - (x == 32) * 1.2, 2.6, 0.7, seed=i, phase=i * 1.3, z=12)
    lv = lit(R, point=(32, 3, 6, 26, 0.35)); R.lv = lv; return px(R, lv)


def coffin(open_):
    R = Rel(32, 24, 6, mats=MATS); lac = R.speck(311, 0.03)
    base = 22.0
    # a six-sided coffin seen from the side and a little above: the lid face, the side, the gilt handles
    side = R.poly([(2, base - 5.2), (6.5, base - 7.6), (30, base - 6.8), (30, base - 1.0), (6.5, base), (2, base - 1.6)])
    R.put(side, 'black', 0.66, z=2, prof='round', r=1.0, spec=0.6, gloss=16, tex=lac)
    for x in (9, 17, 25):
        R.put(R.tube([(x - 1.6, base - 3.3), (x + 1.6, base - 3.3)], 0.8), 'gilt', 0.7, z=4, prof='cyly', amp=0.5, spec=0.4)
    R.put(R.tube([(2.4, base - 4.2), (6.6, base - 6.2), (29.6, base - 5.6)], 0.5), 'gilt', 0.62, z=3.5, prof='flat')
    if not open_:
        lid = R.poly([(2, base - 5.2), (3.4, base - 9.6), (8, base - 12.2), (30.4, base - 11.0), (31, base - 7.0), (30, base - 6.8), (6.5, base - 7.6)])
        R.put(lid, 'black', 0.74, z=5, h=R.prof(lid, 'dome', r=2.6) * 0.8, spec=0.7, gloss=18, tex=lac)
        R.put(R.tube([(2.6, base - 6.4), (4.2, base - 9.8), (8.2, base - 11.4), (29.8, base - 10.2)], 0.5), 'gilt', 0.66, z=7, prof='flat')
        cr = np.maximum(R.tube([(12.4, base - 9.2), (22.4, base - 8.9)], 0.9), R.tube([(15.6, base - 11.0), (15.4, base - 7.6)], 0.9))
        R.put(cr, 'gilt', 0.78, z=8, prof='round', r=0.4, spec=0.5)
    else:
        well = R.poly([(3.2, base - 5.8), (5.6, base - 10.2), (9, base - 11.4), (29.2, base - 10.6), (29.6, base - 7.0), (6.5, base - 7.6)])
        R.put(R.poly([(2, base - 5.2), (4.6, base - 11.0), (8.6, base - 12.6), (30.4, base - 11.8), (31, base - 7.0), (30, base - 6.8), (6.5, base - 7.6)]), 'black', 0.66, z=4, prof='round', r=0.8, tex=lac)
        R.put(well, 'red', 0.58, z=5, h=-R.prof(well, 'dome', r=2) * 0.6 + 1.0, tex=0.06 * np.sin(R.X * 2.2 + R.Y))
        R.put(R.ell(7.6, base - 8.4, 2.2, 1.0), 'red', 0.5, z=6, prof='dome', r=1)               # the pillow
        lid = R.poly([(15, base - 13.6), (31.6, base - 19.4), (32, base - 17.2), (31.4, base - 16.0), (16.4, base - 11.8)])
        R.put(lid, 'black', 0.74, z=7, prof='round', r=0.8, spec=0.7, gloss=18, tex=lac)
        R.put(R.tube([(16, base - 12.8), (31.2, base - 18.2)], 0.4), 'gilt', 0.62, z=8, prof='flat')
    return R, lit(R)


def winerack():
    R = Rel(48, 48, 4, mats=MATS); wd = R.grain(321, 0.06, 'y', 5, 8); rng = np.random.default_rng(322)
    box(R, 0.6, 1.4, 47.4, 48, 'wood', 0.42, z=2, r=1.0, tex=wd)
    R.put(R.poly([(0, 4.2), (48, 4.2), (48, 0.6), (0, 0.6)]), 'wood', 0.55, z=6, prof='cyly', amp=0.6, tex=wd)
    # 4 x 5 cubbies, each with a bottle end: a green glass punt, its rim lit from the upper left; some foil-sealed
    k = 0
    for j in range(5):
        for i in range(4):
            x0 = 3.4 + i * 10.6; y0 = 5.6 + j * 8.4; cx, cy = x0 + 5.0, y0 + 4.0; k += 1
            R.put(R.rect(x0, y0, x0 + 9.4, y0 + 7.6), 'wood', 0.08, z=0.5, prof='flat')
            R.carve(R.rect(x0, y0, x0 + 9.4, y0 + 7.6), 1.2, 0.0)
            if k in (7, 18): continue                    # empty slots
            R.put(R.ell(cx, cy, 3.4, 3.4), 'glassg', 0.42, z=3, prof='dome', r=2.6, spec=0.9, gloss=14)
            R.put(R.ell(cx + 0.3, cy + 0.3, 1.4, 1.4), 'glassg', 0.15, z=2.4, prof='flat')
            if k % 5 == 2: R.put(R.ell(cx, cy, 2.0, 2.0), 'red', 0.48, z=3.6, prof='dome', r=1.4, spec=0.3)
            if k in (10, 15):                            # broken: jagged glass, wine run down the front
                R.put(R.ell(cx, cy, 3.4, 3.4), 'black', 0.06, z=3.2, prof='flat')
                R.put(R.poly([(cx - 2.6, cy + 1.2), (cx + 2.2, cy + 2.0), (cx + 0.4, cy - 2.4), (cx - 0.6, cy + 0.2)]), 'glassg', 0.6, z=3.4, prof='flat')
                R.put(R.tube([(cx + 0.6, cy + 3.2), (cx + 0.9, cy + 8.2)], 0.9, 0.5), 'red', 0.52, z=7, prof='round', r=0.3, spec=0.5)
    # the shelves and uprights in front of the cubbies
    for j in range(6):
        R.put(R.rect(2.0, 4.6 + j * 8.4, 46.0, 5.8 + j * 8.4), 'wood', 0.5, z=5, prof='cyly', amp=0.6, tex=wd)
    for i in range(5):
        R.put(R.rect(2.2 + i * 10.6, 4.6, 3.6 + i * 10.6, 47), 'wood', 0.48, z=5.5, prof='cylx', amp=0.6, tex=wd)
    return R, lit(R)


def barrel():
    R = Rel(32, 32, 4, mats=MATS); wd = R.grain(331, 0.07, 'x', 4, 8)
    # a cradle of two chocks; the cask on its side, its head toward us at the right
    for x in (8, 22):
        R.put(R.poly([(x - 3.5, 32), (x + 3.5, 32), (x + 3.0, 27.6), (x - 3.0, 27.6)]), 'oak', 0.4, z=2, prof='round', r=0.8)
    body = R.poly([(3, 18.5), (4.4, 10.6), (8, 7.6), (24, 7.6), (24, 29.4), (8, 29.4), (4.4, 26.4)])
    yy = (R.Y - 18.5) / 11
    R.put(body, 'wood', 0.48, z=4, h=np.sqrt(np.clip(1 - yy ** 2, 0, 1)) * 9, tex=wd)
    for k in range(6): R.carve(R.rect(4, 9.6 + k * 3.4, 24, 9.9 + k * 3.4), 0.4, -0.08)   # staves
    for x in (7.4, 13, 21.4):
        hoop = R.rect(x - 0.9, 7.2, x + 0.9, 29.8) * (body > 0.2)
        R.put(hoop, 'iron', 0.42, z=5, h=np.sqrt(np.clip(1 - yy ** 2, 0, 1)) * 9 + 0.6, spec=0.3)
    head = R.ell(24.4, 18.5, 3.2, 11.0); R.put(head, 'oak', 0.55, z=6, prof='dome', r=1.6, tex=R.grain(332, 0.05, 'y', 3, 8))
    R.put(np.clip(head - R.ell(24.6, 18.5, 2.3, 9.9), 0, 1), 'iron', 0.45, z=7, prof='round', r=0.4)
    R.carve(R.rect(24.2, 8.6, 24.6, 28.4), 0.3, -0.08)
    R.put(R.rect(26.0, 21, 29.4, 23), 'gilt', 0.55, z=8, prof='cyly', amp=0.5, spec=0.4)          # the brass tap
    R.put(R.rect(28.2, 23, 29.4, 25.2), 'gilt', 0.5, z=8, prof='cylx', amp=0.5)
    R.put(R.ell(28.8, 26.2, 0.5, 0.6), 'red', 0.6, z=8, prof='flat', spec=0.5)                     # a drop
    R.put(R.ell(26, 31.4, 4.0, 0.6), 'red', 0.3, z=1, prof='flat')                                 # the stain under it
    return R, lit(R)


ITEMS = {}


def reg(tag):
    def d(f): ITEMS[tag] = f; return f
    return d


@reg('bookcase')
def _bc(): R, lv = bookcase(); return [px(R, lv)]
@reg('bookcase_fallen')
def _bcf(): R, lv = bookcase(True); return [px(R, lv)]
@reg('books')
def _bk(): R, lv = books(); return [px(R, lv)]
@reg('bed')
def _bed(): R, lv = bed(); return [px(R, lv)]
@reg('wardrobe')
def _wd(): R, lv = wardrobe(); return [px(R, lv)]
@reg('hearth')
def _hearth(): return hearth_frames()
@reg('bellboard')
def _bb(): R, lv = bellboard(); return [px(R, lv)]
@reg('desk')
def _desk(): return [desk_px()]
@reg('globe')
def _globe(): R, lv = globe(); return [px(R, lv)]
@reg('cot')
def _cot(): R, lv = cot(); return [px(R, lv)]
@reg('stove')
def _stove(): return stove_frames()
@reg('lamp_cm')
def _lamp(): return lamp_frames()
@reg('laundry')
def _laundry(): R, lv = laundry(); return [px(R, lv)]
@reg('roses')
def _roses(): R, lv = roses(); return [px(R, lv)]
@reg('pipes')
def _pipes(): R, lv = pipes(); return [px(R, lv)]
@reg('piano')
def _piano(): R, lv = piano(); return [px(R, lv)]
@reg('chimney')
def _chimney(): R, lv = chimney(); return [px(R, lv)]
@reg('weathervane')
def _wv(): R, lv = weathervane(); return [px(R, lv)]
@reg('gutterspout')
def _gs(): R, lv = gutterspout(); return [px(R, lv)]
@reg('bust')
def _bust(): R, lv = bust(); return [px(R, lv)]
@reg('rug')
def _rug(): R, lv = rug(); return [px(R, lv)]
@reg('canvasback')
def _cb(): R, lv = canvasback(); return [px(R, lv)]
@reg('spyhole')
def _spy(): R, lv = spyhole(); return [px(R, lv)]


EXTRA = {
    'xsa_chand': lambda: {'fallenchandelier': [px(*fallen_chandelier())]},
    'cm_table': lambda: {'idle': [table_px()]},
    'cm_coffin': lambda: {'closed': [px(*coffin(False))], 'open': [px(*coffin(True))]},
    'cm_winerack': lambda: {'idle': [px(*winerack())]},
    'cm_barrel': lambda: {'idle': [px(*barrel())]},
}


def main():
    only = None
    if '--only' in sys.argv: only = sys.argv[sys.argv.index('--only') + 1].split(',')
    frames = {}
    for tag, f in ITEMS.items():
        if only and tag not in only: continue
        frames[tag] = f()
        for i, im in enumerate(frames[tag]): im.save(os.path.join(SRC, f'cm_{tag}_{i}.png'))
        print(' ', tag, len(frames[tag]))
    for name, f in EXTRA.items():
        if only and name not in only: continue
        fr = f()
        for tag, ims in fr.items():
            for i, im in enumerate(ims): im.save(os.path.join(SRC, f'{name}_{tag}_{i}.png'))
        if '--nobuild' not in sys.argv: build_sheet(name, fr)
    if '--nobuild' not in sys.argv and not only:
        build_sheet('xsa_cm', frames, keep_v1=('grandclock', 'crows', 'trellis', 'chalk'))
    return frames


if __name__ == '__main__':
    main()
