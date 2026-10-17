#!/usr/bin/env python3
"""Props batch C, the Ember and the Hermit's Hollow (docs/v17/props_c.md), and the one build of the shared xsc_* sheets.

  xsc_m  deadshrine 4f (heat states n=0 lit .. 2 cold, 3 toppled), deadtree 2f (two variants), hearth 6f, pine, shelves
  xsc_l  hut (+ the Starfall dome from gen_props_c_starfall.py)
  xsc_s  lantern, jars, rug, embershelf, hangingpots, firewood, stonelantern, herbs (+ Starfall emberrock, wayshrine)
Every other xsc tag (the Neohallow ones: vending, watertower, devdesk, maglev, dumpster; and glassgrass, grass, meteor,
wellshard, ashpile, chimes, fallenstar, embertree, comet) keeps its v1 pixels.

Ember: scorched basalt and ash-grey stone, charred wood, ember light from inside. Hermit: weathered timber, thatch, clay and
a warm window in the dusk. Fire is drawn per frame from one geometry with phase-shifted tongues (no frame-to-frame noise).

  python3 art/gen_props_c_ember.py [shrine tree hearth pine shelves hut small] [--no-ase]   (builds the xsc sheets unless --no-ase)
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import props_c_lib as P
from props_c_lib import Pc, ramp, selout, to_img, T, S

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
NO_ASE = '--no-ase' in sys.argv

ASHST = ramp('#0c0909', '#151010', '#1e1716', '#29201e', '#352a27', '#443632', '#57463f', '#6d5a50', '#887264', '#a38d7c')
CHAR = ramp('#070505', '#0e0a09', '#16100e', '#1f1714', '#2a1f1a', '#382a22', '#4a382c', '#5e4a3a')
EMBER = ramp('#3a0e06', '#6e1a08', '#a83010', '#e05a1c', '#ff8a30', '#ffc060', '#ffe8b0')
ASH = ramp('#3e3734', '#57504b', '#746c66', '#958c85', '#b3aaa2')
WOOD = ramp('#120d0a', '#1d1510', '#2a1f17', '#3a2b1f', '#4c3a29', '#614b35', '#7a6044', '#957754')
THATCH = ramp('#17130c', '#241d12', '#33291a', '#463822', '#5b4a2d', '#73603a', '#8e7849', '#a8925c')
HSTONE = ramp('#100f12', '#1a181b', '#252226', '#322e31', '#423c3e', '#554e4e', '#6c6462', '#877d78', '#a19691')
CLAY = ramp('#1e120c', '#311d13', '#4a2c1c', '#653c26', '#824f33', '#9e6744', '#b88259')
PINE = ramp('#070d0c', '#0b1513', '#111e1b', '#172822', '#1e332a', '#273f33', '#324c3c', '#3f5a45')
IRON = ramp('#08080a', '#111114', '#1b1b1f', '#27272c', '#36363c', '#4a4a50', '#62626a')
GLOW = ramp('#5a2a10', '#9a5020', '#d08838', '#f0b458', '#ffd890', '#fff2d0')
CLOTH = ramp('#170c0c', '#2a1414', '#401e1c', '#5a2a26', '#743a32', '#8e4e40')
CLOTH2 = ramp('#14130f', '#25221a', '#3a3527', '#524b37', '#6d6449')
HERB = ramp('#0f170e', '#182515', '#22341d', '#2f4627', '#3f5a32', '#55723f')
FLOWER = ramp('#2a1a2a', '#463048', '#644a68', '#86688a')
PAPER = ramp('#4a3a28', '#7a6444', '#ad9668', '#d8c494', '#f4e6bc')
GLASS = ramp('#16201c', '#24342c', '#3a4e40', '#557060')
OUT = (6, 4, 4)
R = {'ashst': ASHST, 'char': CHAR, 'ember': EMBER, 'fire': EMBER, 'ash': ASH, 'wood': WOOD, 'thatch': THATCH, 'hstone': HSTONE, 'clay': CLAY,
     'pine': PINE, 'iron': IRON, 'glow': GLOW, 'cloth': CLOTH, 'cloth2': CLOTH2, 'herb': HERB, 'flower': FLOWER, 'paper': PAPER, 'glass': GLASS,
     'void': ramp('#030202', '#080505', '#0e0909'), 'soot': ramp('#0a0807', '#120e0c', '#1a1411')}
L_KEY = (-0.55, -0.72, 0.42)
NO_RIM = {'fire', 'ember', 'glow', 'void', 'soot', 'paper'}


def prev(name, imgs, **kw):
    kw.setdefault('scale', 5 if max(i.height for i in imgs) <= 64 else 3)
    P.preview(name, imgs, bg=(30, 20, 18), **kw)


def finish(c, dk=0.3, near_skip=(), rimw=(1.0, 0.6, 0.25, 0.0), lit_k=0.4):
    s = c.resolve(0.45)
    s.index(R, dk=dk).rim(R, mats=set(R) - NO_RIM, wts=rimw, steps=1, minv=0.15)
    o = s.rgba(R)
    for (x, y, col) in getattr(c, 'stamps', []):
        if 0 <= x < o.shape[1] and 0 <= y < o.shape[0]: o[y, x, :3] = col; o[y, x, 3] = 255
    near = s.alpha & ~np.logical_or.reduce([s.m(n) for n in near_skip]) if near_skip else None
    return to_img(selout(o, OUT, lit_k=lit_k, near=near))


def lit(c, m, sigma=2.0, amb=0.16, key=0.78, light=L_KEY):
    nx, ny, nz = c.normals(m, sigma=sigma); L = P.unit(light)
    return amb + key * np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1), ny


def block(c, x0, y0, x1, y1, mat, v=0.45, bevel=1.0, seed=0, tex=0.06):
    """A cut-stone block: lit top and left bevels, dark right and bottom edges, a little grain."""
    m = c.rect(x0, y0, x1, y1)
    vv = v + 0.22 * (c.Y < y0 + bevel) + 0.1 * (c.X < x0 + bevel) - 0.2 * (c.X > x1 - bevel) - 0.12 * (c.Y > y1 - bevel * 0.7)
    c.put(m, mat, vv + tex * (c.noise(seed, 0.5) - 0.5))
    return m


def ash_dust(c, m, ny, seed, k=0.62):
    """Ash settled on the up-facing surfaces."""
    n = c.noise(seed, 0.5)
    c.put(m & ((np.clip(-ny, 0, 1) * 1.2 + n * 0.6) > k + 0.45), 'ash', 0.35 + 0.4 * n)


def flame(c, cx, base, w, h, f, seed=0, n=5, mat='fire'):
    """Tongues of fire, each a curved tapering stroke with a phase per frame, hot at the root."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        ph = rng.uniform(0, 6.3); sp = rng.uniform(0.8, 1.3)
        hh = h * (0.55 + 0.45 * math.cos(u * 2.6)) * (0.75 + 0.25 * math.sin(f * 1.05 * sp + ph))
        x0 = cx + u * w; sway = 1.2 * math.sin(f * 1.3 + ph)
        pts = [(x0, base), (x0 + sway * 0.4, base - hh * 0.45), (x0 + sway, base - hh)]
        m, U, TT, ax, ay = c.stroke(pts, w / n * 0.95 + 0.4, 0.3)
        c.put(m, mat, 1.0 - 0.75 * TT - 0.15 * np.abs(U))


# =============================================================================================== xsc_m/deadshrine
def deadshrine(n):
    """A wayside shrine of ash-grey basalt: plinth, a squat body with a fire niche, a pitched cap stone. n: 0 the ember still
    burns, 1 a dull glow, 2 cold, 3 toppled (the cap fallen beside it)."""
    c = Pc(64, 64); y = 63.8; cx = 32.0
    c.put(c.ell(cx, y - 0.4, 14, 1.6), 'ash', 0.3)
    block(c, cx - 11, y - 4, cx + 11, y + 0.3, 'ashst', 0.36, seed=1)
    block(c, cx - 9, y - 6.5, cx + 9, y - 4, 'ashst', 0.46, seed=2)
    top = y - 24 if n < 3 else y - 19
    body = c.poly([(cx - 7.5, y - 6.5), (cx - 7, top), (cx + 7, top), (cx + 7.5, y - 6.5)]) if n < 3 else \
        c.poly([(cx - 7.5, y - 6.5), (cx - 7, top + 1), (cx - 3, top - 0.5), (cx + 1, top + 2), (cx + 4, top), (cx + 7, top + 2.5), (cx + 7.5, y - 6.5)])
    v, ny = lit(c, body, sigma=2.5)
    cr, cid = c.cracks(5, cell=4.0, aspect=0.6, width=0.09)
    c.put(body, 'ashst', v - 0.18 * cr + 0.05 * (c.noise(6, 0.6) - 0.5))
    # the niche (light at y-14 in code)
    ny0 = y - 9.5; nh = 9.0
    niche = c.poly([(cx - 3.6, ny0), (cx - 3.6, ny0 - nh + 2.5), (cx, ny0 - nh), (cx + 3.6, ny0 - nh + 2.5), (cx + 3.6, ny0)])
    c.put(niche, 'void', 0.3)
    c.put(c.stroke([(cx - 4.4, ny0 + 0.5), (cx - 4.4, ny0 - nh + 2.3), (cx, ny0 - nh - 1), (cx + 4.4, ny0 - nh + 2.3), (cx + 4.4, ny0 + 0.5)], 0.55, 0.55)[0] & ~niche,
          'ashst', 0.62)
    c.put(c.rect(cx - 4.5, ny0, cx + 4.5, ny0 + 1.4), 'ashst', 0.7)
    heat = [1.0, 0.45, 0.0, 0.0][n]
    if heat:
        glow = niche & (c.Y > ny0 - nh + 1)
        d = np.hypot((c.X - cx) / 3.6, (c.Y - (ny0 - 1)) / 6)
        c.put(glow, 'ember', 0.15 + heat * 0.8 * np.clip(1 - d, 0, 1))
        c.put(c.ell(cx, ny0 - 0.8, 2.6, 1.0), 'ember', 0.35 + 0.6 * heat)
        if n == 0: flame(c, cx, ny0 - 0.8, 3.4, 4.5, 0.0, seed=3, n=3)
        # the stone round the niche catches the light
        c.shift(body & ~niche & (np.hypot(c.X - cx, c.Y - (ny0 - 3)) < 7), 0.12 * heat)
    else:
        c.put(c.ell(cx, ny0 - 0.8, 2.6, 1.0), 'ash', 0.45)
    if n < 3:   # the pitched cap
        cap = c.poly([(cx - 11, top + 0.5), (cx - 9.5, top - 2.2), (cx, top - 7.5), (cx + 9.5, top - 2.2), (cx + 11, top + 0.5)])
        v, ny2 = lit(c, cap, sigma=1.6, key=0.85)
        c.put(cap, 'ashst', v + 0.1 * (c.X < cx))
        c.put(c.ell(cx, top - 8.2, 1.4, 1.4), 'ashst', 0.65)
        ash_dust(c, cap, ny2, 8, k=0.5)
    else:       # fallen beside it, cracked in two
        for (pts, sd) in (([(cx + 9, y - 0.2), (cx + 10, y - 5), (cx + 16, y - 8.5), (cx + 19, y - 6), (cx + 19.5, y - 0.2)], 9),
                          ([(cx + 20, y - 0.2), (cx + 21, y - 3.5), (cx + 25.5, y - 4.5), (cx + 27, y - 0.2)], 10)):
            m = c.poly(pts); v, ny2 = lit(c, m, sigma=1.4)
            c.put(m, 'ashst', v); ash_dust(c, m, ny2, sd, k=0.5)
        c.put(c.ell(cx - 12, y - 0.8, 2.2, 1.1) | c.ell(cx + 5, y - 7.0, 1.4, 0.8), 'ashst', 0.4)    # chips
    ash_dust(c, body, ny, 7)
    return finish(c, near_skip=('ember',))


# =============================================================================================== xsc_m/deadtree
def deadtree(v):
    c = Pc(64, 64); y = 63.8
    Wd = T.Wood(64, 64); nz = T.Noise(110 + v)
    if v == 0:
        Wd.branch([(32, y + 3), (31, 48), (30, 34), (32, 22)], 3.6, 2.2, wob=0.8, wobf=0.12, seed=1, rprof=lambda t, s: 2.2 + 1.6 * (1 - t) + 2.5 * np.exp(-s / 3), twist=0.2)
        for (pts, r0, sd) in [([(31, 36), (24, 29), (17, 24), (12, 16)], 1.6, 2), ([(32, 26), (38, 18), (43, 13), (47, 7)], 1.5, 3), ([(32, 24), (31, 14), (33, 6)], 1.4, 4),
                              ([(31, 46), (39, 41), (45, 39)], 1.2, 5), ([(18, 25), (13, 26), (9, 24)], 0.8, 6), ([(42, 14), (45, 17), (49, 16)], 0.8, 7),
                              ([(14, 19), (16, 13), (15, 9)], 0.7, 8), ([(44, 10), (41, 5)], 0.6, 9)]:
            Wd.branch(pts, r0, 0.45, wob=0.5, wobf=0.25, seed=sd, twist=0.2, under=2)
    else:
        Wd.branch([(30, y + 3), (31, 50), (34, 38), (33, 28), (29, 18)], 3.4, 2.0, wob=0.9, wobf=0.12, seed=11, rprof=lambda t, s: 2.0 + 1.6 * (1 - t) + 2.5 * np.exp(-s / 3), twist=0.25)
        for (pts, r0, sd) in [([(33, 40), (40, 34), (47, 30), (53, 24)], 1.5, 12), ([(33, 30), (24, 25), (18, 18), (15, 10)], 1.5, 13), ([(29, 20), (31, 11), (28, 4)], 1.1, 14),
                              ([(46, 31), (49, 36), (53, 37)], 0.8, 15), ([(19, 19), (13, 18), (9, 14)], 0.8, 16), ([(51, 26), (55, 20), (56, 15)], 0.7, 17),
                              ([(31, 52), (24, 49), (19, 50)], 1.0, 18)]:
            Wd.branch(pts, r0, 0.45, wob=0.5, wobf=0.25, seed=sd, twist=0.2, under=2)
    val, rim, mo, fur = Wd.shade(nz, light=(-0.7, -0.45, 0.55), rim_dir=[(1.0, -0.2, 1.0), (-1.0, -0.2, 0.5)], ridges=0.7, furrow_depth=0.9,
                                 plate_len=6, ambient=0.14, key=0.7, pattern='plates', gap=0.2, moss_amt=0.0)
    c.put(Wd.cov, 'char', val + 0.3 * rim)
    # ember-lit cracks deep in the char, and ash on the boughs' tops
    c.put(Wd.cov & (fur > 0.75) & (c.noise(120 + v, 0.6) > 0.68) & (c.Y > 30), 'ember', 0.45)
    c.put(Wd.cov & (np.clip(Wd.ay * 0 - 0, 0, 1) == 0) & (rim > 0.6) & (c.noise(121 + v, 0.4) > 0.55), 'ash', 0.45)
    c.put(c.ell(31, y - 0.3, 6.5, 1.3), 'ash', 0.3)
    return finish(c, near_skip=('ember',), rimw=(1.0, 0.4, 0.6, 0.0))


# =============================================================================================== xsc_m/hearth
def hearth(f):
    """A heavy hearth of fire-blackened stone: a lintel slab on two jambs, a soot-scorched back, iron firedogs, logs, flames."""
    c = Pc(64, 64); y = 63.8; cx = 32.0
    c.put(c.rect(cx - 21, y - 34, cx + 21, y), 'hstone', 0.3)
    cr, cid = c.cracks(31, cell=5.0, aspect=0.6, width=0.1)
    m = c.rect(cx - 21, y - 34, cx + 21, y)
    c.put(m, 'hstone', 0.32 + 0.12 * (cid - 0.5) - 0.25 * cr + 0.12 * (c.X < cx - 17) - 0.12 * (c.X > cx + 17))
    for (x0, x1) in ((cx - 18, cx - 11), (cx + 11, cx + 18)):          # jambs: bigger blocks
        for k in range(4):
            block(c, x0, y - 26 + k * 6.5, x1, y - 26 + (k + 1) * 6.5 - 0.6, 'hstone', 0.42 - 0.04 * k, seed=40 + k + int(x0))
    block(c, cx - 22, y - 32, cx + 22, y - 26, 'hstone', 0.5, bevel=1.4, seed=45)              # lintel
    block(c, cx - 23.5, y - 35, cx + 23.5, y - 32, 'wood', 0.5, bevel=1.0, seed=46)             # mantel beam
    for x in (cx - 15, cx + 13):
        c.put(c.rect(x, y - 37.5, x + 2.5, y - 35), 'clay', 0.55)                                # a pot, a jug on the mantel
    c.put(c.ell(cx + 6, y - 36.6, 1.6, 1.6), 'clay', 0.5)
    fire = c.poly([(cx - 11, y), (cx - 11, y - 22), (cx + 11, y - 22), (cx + 11, y)])
    d = np.hypot((c.X - cx) / 11, (c.Y - (y - 3)) / 20)
    c.put(fire, 'soot', 0.2 + 0.6 * np.clip(1 - d, 0, 1))
    # firedogs and logs
    for sd in (-1, 1):
        m, U, TT, ax, ay = c.stroke([(cx + sd * 7, y), (cx + sd * 7, y - 5.5), (cx + sd * 8.5, y - 7)], 0.7, 0.6)
        c.put(m, 'iron', 0.4)
    for (x0, x1, yy, r) in ((cx - 9, cx + 8, y - 3.0, 1.7), (cx - 6, cx + 9.5, y - 5.6, 1.5)):
        m, U, TT, ax, ay = c.stroke([(x0, yy), (x1, yy - 0.4)], r, r * 0.9)
        c.put(m, 'char', c.cyl(U, ax, ay, amb=0.1, key=0.4) + 0.25 * (U > 0.4))
        c.put(m & (np.abs(U) < 0.4) & (c.noise(50, 0.4) > 0.55), 'ember', 0.55)
    c.put(c.ell(cx, y - 1.0, 9.5, 1.1), 'ember', 0.5)                                          # the bed of coals
    flame(c, cx + 0.5, y - 5.5, 15, 14, f * 2 * math.pi / 6, seed=7, n=6)
    flame(c, cx - 1, y - 4.5, 8, 8, f * 2 * math.pi / 6 + 1.7, seed=8, n=4)
    # the fire lights the inner faces of the jambs and the lintel's underside
    c.shift(c.cov & ~fire & (np.abs(c.X - cx) < 14.5) & (c.Y > y - 26) & (c.mat == c.mid('hstone')), 0.2 * np.clip(1 - np.abs(np.abs(c.X - cx) - 11) / 3.5, 0, 1))
    # soot stains above the opening
    c.put(m & (c.Y < y - 25.5) & (c.Y > y - 32) & (np.abs(c.X - cx) < 9 + 3 * c.noise(51, 0.5)) & (c.noise(52, 0.5) > 0.35), 'soot', 0.4)
    return finish(c, near_skip=('fire', 'ember'))


# =============================================================================================== xsc_m/pine
def pine():
    """A dark fir: separate tiers of drooping, ragged needle sprays round a thin trunk (gaps between them show the trunk), the
    top of each tier lit from the upper left, its underside in shadow."""
    c = Pc(64, 64); y = 63.8; cx = 32.0
    tr, U, TT, ax, ay = c.stroke([(cx, y + 1), (cx + 0.4, y - 30), (cx - 0.2, y - 60)], 1.8, 0.5)
    c.put(tr, 'wood', c.cyl(U, ax, ay, amb=0.12, key=0.55))
    rng = np.random.default_rng(4)
    tiers = [(y - 58, 3.0), (y - 52, 5.5), (y - 45.5, 8.0), (y - 39, 10.5), (y - 32, 13.0), (y - 25, 15.5), (y - 17.5, 18.0), (y - 10, 20.0)]
    for k, (ty, span) in enumerate(tiers):
        for sd in (-1, 1):
            nsp = 3 + k // 2
            for j in range(nsp):
                L = span * rng.uniform(0.75, 1.05) * (1 - 0.35 * j / nsp)
                y0 = ty + j * 0.9 + rng.uniform(-0.4, 0.4); x0 = cx + sd * 0.8
                droop = rng.uniform(0.25, 0.45)
                pts = [(x0, y0), (x0 + sd * L * 0.5, y0 + L * droop * 0.25), (x0 + sd * L, y0 + L * droop + 1.0)]
                m, Us, T2, ax2, ay2 = c.stroke(pts, 1.0 + 0.12 * span * (1 - 0.4 * j / nsp), 0.45)
                top = np.clip(-(Us * (-ay2 * 0 + 1)) * sd * 0 + 0.5 - (c.Y - (y0 + (c.X - x0) * sd * droop * 0.6)) * 0.35, 0, 1)
                v = 0.14 + 0.5 * top + 0.12 * (sd < 0) - 0.06 * j + 0.12 * (c.noise(5 + k, 0.3) - 0.5)
                c.put(m, 'pine', v)
                for q in range(int(L / 1.6)):          # ragged needle tufts hanging off the spray
                    t = (q + 0.5) / (L / 1.6); px_ = x0 + sd * L * t; py_ = y0 + L * droop * t ** 1.6 + 0.6
                    tm = c.stroke([(px_, py_), (px_ + sd * 0.6, py_ + 1.6 + rng.uniform(0, 1.2))], 0.45, 0.25)[0]
                    c.put(tm, 'pine', 0.12 + 0.1 * rng.random(), under=True)
    c.put(c.ell(cx, y - 0.4, 7, 1.2), 'soot', 0.3)
    return finish(c, near_skip=())


# =============================================================================================== xsc_m/shelves
def shelves():
    c = Pc(64, 64); y = 63.8
    x0, x1, top = 18.0, 46.0, y - 40
    c.put(c.rect(x0, top, x1, y), 'void', 0.6)
    for xx in (x0, x1 - 2.4):
        m, U, TT, ax, ay = c.stroke([(xx + 1.2, y + 0.5), (xx + 1.2, top - 1)], 1.3, 1.3, smooth_pts=False)
        c.put(m, 'wood', c.cyl(U, ax, ay, amb=0.18, key=0.7))
    rng = np.random.default_rng(21)
    for k, sy in enumerate((top + 1.5, top + 14, top + 27, y - 1.5)):
        block(c, x0 - 1, sy - 1.5, x1 + 1, sy + 0.3, 'wood', 0.5, bevel=0.7, seed=60 + k)
        if k == 0: continue
        x = x0 + 3.0
        while x < x1 - 4:
            kind = rng.integers(0, 4)
            if kind <= 1:        # books, some leaning
                for b in range(rng.integers(2, 5)):
                    bw = rng.uniform(1.4, 2.2); bh = rng.uniform(7, 10.5); lean = 0.0 if rng.random() < 0.7 else 1.5
                    mat = ['cloth', 'cloth2', 'clay'][rng.integers(0, 3)]
                    m = c.poly([(x, sy - 1.5), (x + lean, sy - 1.5 - bh), (x + lean + bw, sy - 1.5 - bh), (x + bw, sy - 1.5)])
                    c.put(m, mat, 0.35 + 0.25 * (c.X < x + bw * 0.4) + 0.12 * (np.abs(c.Y - (sy - 1.5 - bh * 0.75)) < 0.5))
                    x += bw + 0.25
            elif kind == 2:      # a clay pot
                r = rng.uniform(2.4, 3.4); m = c.ell(x + r, sy - 1.5 - r * 0.9, r, r * 0.95) | c.rect(x + r * 0.5, sy - 1.5 - r * 2.1, x + r * 1.5, sy - 1.5 - r)
                c.put(m, 'clay', lit(c, m, sigma=0.9)[0]); x += 2 * r
            else:                # a bottle
                m = c.rect(x, sy - 6.5, x + 2.4, sy - 1.5) | c.rect(x + 0.7, sy - 9, x + 1.7, sy - 6.5)
                c.put(m, 'glass', lit(c, m, sigma=0.6)[0]); c.put(m & (np.abs(c.X - x - 0.6) < 0.3), 'glass', 1.0); x += 2.4
            x += rng.uniform(1.0, 2.5)
    c.put(c.ell(x1 - 6, top - 2.4, 3.6, 2.4) & (c.Y < top - 0.5), 'clay', 0.5)              # a basket on top
    return finish(c, near_skip=('void',))


# =============================================================================================== xsc_l/hut
def hut():
    """The hermit's hut: a dry-stone footing, dark timber walls, a steep shaggy thatch with moss, a stone chimney (smoke out at
    x+18, y-64 in code) and one warm window (light at x+2, y-22)."""
    c = Pc(128, 128); y = 127.8; cx = 64.0
    # footing
    for k, (yy0, yy1) in enumerate(((y - 5, y + 0.3), (y - 9.5, y - 5))):
        x = cx - 34 + (k * 3)
        while x < cx + 34:
            bw = 4.5 + 3 * ((int(x * 7) % 5) / 5)
            block(c, x, yy0, min(cx + 34, x + bw - 0.5), yy1 - 0.4, 'hstone', 0.4 + 0.08 * ((int(x) % 3) - 1), bevel=0.8, seed=int(x) + k * 50)
            x += bw
    # timber walls: vertical planks, a sill beam, corner posts
    wall = c.rect(cx - 31, y - 44, cx + 31, y - 9.5)
    plank = np.abs(((c.X - cx) / 4.2) % 1 - 0.5) > 0.44
    c.put(wall, 'wood', 0.32 - 0.12 * plank + 0.08 * (c.noise(70, 0.4, sy=3) - 0.5) - 0.12 * np.clip((c.X - cx) / 31, 0, 1) + 0.06 * (c.X < cx - 20))
    for xx in (cx - 32, cx + 29):
        m, U, TT, ax, ay = c.stroke([(xx + 1.5, y - 9), (xx + 1.5, y - 46)], 1.8, 1.8, smooth_pts=False)
        c.put(m, 'wood', c.cyl(U, ax, ay, amb=0.18, key=0.7))
    block(c, cx - 33, y - 12, cx + 33, y - 9.5, 'wood', 0.45, bevel=0.8, seed=71)
    c.shift(wall & (c.Y < y - 39), -0.14)                      # the eave's shadow on the wall
    # door with iron straps, lintel
    for (x0, x1) in ((cx - 16.5, cx - 15), (cx - 4, cx - 2.5)):
        block(c, x0, y - 37, x1, y - 9.5, 'wood', 0.6, bevel=0.5, seed=int(x0))
    door = c.rect(cx - 15, y - 36, cx - 4, y - 9.5)
    c.put(door, 'wood', 0.12 + 0.12 * (np.abs(((c.X - cx) / 2.75) % 1 - 0.5) < 0.4) + 0.1 * (c.X < cx - 13))
    for yy in (y - 31, y - 16):
        c.put(c.rect(cx - 15, yy, cx - 4, yy + 1.2), 'iron', 0.45)
    c.put(c.ell(cx - 6, y - 22, 0.8, 0.8), 'iron', 0.75)
    block(c, cx - 17, y - 38.5, cx - 2, y - 36, 'wood', 0.55, bevel=0.7, seed=72)
    # the window, warm (light at x+2, y-22)
    wx, wy = cx + 6, y - 32
    win = c.rect(wx, wy, wx + 11, wy + 9)
    d = np.hypot((c.X - wx - 5.5) / 5.5, (c.Y - wy - 5) / 4.5)
    c.put(win, 'glow', 0.95 - 0.55 * np.clip(d, 0, 1))
    c.put(win & ((np.abs(c.X - wx - 5.5) < 0.5) | (np.abs(c.Y - wy - 4.5) < 0.5)), 'wood', 0.25)     # mullions
    c.put(c.stroke([(wx - 1, wy - 0.6), (wx + 12, wy - 0.6)], 0.8, 0.8, smooth_pts=False)[0] | c.stroke([(wx - 1.5, wy + 9.7), (wx + 12.5, wy + 9.7)], 0.9, 0.9, smooth_pts=False)[0],
          'wood', 0.6)
    # the chimney (stone) on the right, the smoke rises from its top
    ch = c.rect(cx + 14, y - 67, cx + 23, y - 40)
    c.put(ch, 'hstone', 0.3)
    k = 0
    for yy in np.arange(y - 67, y - 40, 3.2):
        off = 2.2 * (k % 2); x = cx + 14 - off
        while x < cx + 23:
            block(c, max(cx + 14, x), yy, min(cx + 23, x + 4.4) - 0.4, yy + 2.8, 'hstone', 0.42 + 0.06 * (k % 3 - 1), bevel=0.6, seed=int(yy * 3 + x))
            x += 4.4
        k += 1
    block(c, cx + 13, y - 69, cx + 24, y - 66.5, 'hstone', 0.6, bevel=0.6, seed=80)
    c.put(c.rect(cx + 15.5, y - 69.5, cx + 21.5, y - 68.6), 'soot', 0.2)
    # the thatch: a steep shaggy roof, straw strokes along the slope, moss and darker wet patches
    roof = c.poly([(cx - 41, y - 40), (cx - 6, y - 82), (cx + 6, y - 82), (cx + 41, y - 40), (cx + 37, y - 37.5), (cx - 37, y - 37.5)])
    roof &= ~(ch & (c.Y < y - 45))
    nx, ny, nz = c.normals(roof, sigma=6)
    side = np.where(c.X < cx, 0.62, 0.3)
    sl = (c.X - cx) * np.sign(c.X - cx + 1e-6) * 0.85 - (c.Y - (y - 82))          # coordinate across the slope
    straw = 0.16 * np.sin(sl * 3.4 + 4 * c.noise(81, 0.25)) + 0.1 * (c.noise(82, 0.15, sy=0.5) - 0.5)
    crs = ((c.Y - (y - 82)) / 7.0 + 0.25 * np.sin(c.X * 0.9)) % 1
    rows = 0.28 * (crs > 0.84) - 0.08 * (crs < 0.2)                                          # the courses' shaggy lower edges
    c.put(roof, 'thatch', side + straw - rows - 0.12 * np.clip((c.Y - (y - 45)) / 6, 0, 1) * 0)
    eave = roof & (c.Y > y - 41.5)
    c.put(eave, 'thatch', 0.2 + 0.1 * np.sin(c.X * 2.3))
    notches = (c.Y > y - 39.5) & (np.sin(c.X * 1.9) + np.sin(c.X * 0.7) > 0.9)
    c.erase(roof & notches)
    c.put(roof & (c.noise(83, 0.3, sy=0.6) > 0.74) & (c.Y < y - 46), 'herb', 0.3 + 0.4 * (c.X < cx))   # moss on the thatch
    # the ridge pole
    c.put(c.stroke([(cx - 7, y - 82.5), (cx + 7, y - 82.5)], 1.3, 1.3, smooth_pts=False)[0], 'wood', 0.55)
    return finish(c, near_skip=('glow',))


# =============================================================================================== xsc_s small set
def small(tag):
    c = Pc(32, 32); y = 31.8; cx = 16.0
    if tag == 'lantern':      # a paper lantern on a crooked post (light y-10)
        m, U, TT, ax, ay = c.stroke([(cx - 1, y + 0.5), (cx - 1.4, y - 14), (cx - 1, y - 19)], 0.9, 0.7)
        c.put(m, 'wood', c.cyl(U, ax, ay, amb=0.2, key=0.7))
        c.put(c.stroke([(cx - 1, y - 18), (cx + 3.5, y - 18.5)], 0.55, 0.5)[0], 'wood', 0.55)
        c.put(c.stroke([(cx + 3.2, y - 18.4), (cx + 3.2, y - 16)], 0.25, 0.25)[0], 'iron', 0.4)
        body = c.ell(cx + 3.2, y - 11.5, 3.0, 4.6)
        d = np.hypot((c.X - cx - 3.2) / 3.0, (c.Y - y + 11.5) / 4.6)
        c.put(body, 'paper', 0.95 - 0.55 * d ** 1.5 - 0.12 * (np.abs(((c.Y - y + 11.5) / 1.6) % 1 - 0.5) > 0.42))
        c.put(c.rect(cx + 1.4, y - 16.5, cx + 5.0, y - 15.6) | c.rect(cx + 1.4, y - 7.4, cx + 5.0, y - 6.5), 'wood', 0.4)
    elif tag == 'jars':       # three clay jars, one stoppered, one cracked
        for (x, r, hh, s) in ((cx - 6, 3.6, 8.5, 1), (cx + 1, 4.6, 11.5, 2), (cx + 8, 3.0, 6.5, 3)):
            m = c.ell(x, y - hh * 0.45, r, hh * 0.45) | c.rect(x - r * 0.42, y - hh, x + r * 0.42, y - hh * 0.7)
            m |= c.rect(x - r * 0.62, y - hh - 0.8, x + r * 0.62, y - hh + 0.2)
            v, ny = lit(c, m, sigma=1.4)
            c.put(m, 'clay', v - 0.1 * (np.abs(c.Y - (y - hh * 0.62)) < 0.4) + 0.05 * (c.noise(s, 0.4) - 0.5))
            if s == 2: c.put(c.ell(x, y - hh - 1.2, r * 0.45, 0.9), 'wood', 0.55)
        c.put(c.stroke([(cx + 9, y - 6), (cx + 8, y - 3.5), (cx + 9, y - 1.5)], 0.3, 0.3)[0] & c.cov, 'void', 0.3)
    elif tag == 'rug':        # a worn woven rug on the floor, seen almost edge-on
        m = c.poly([(cx - 14.5, y + 0.2), (cx - 13, y - 2.8), (cx + 13, y - 2.8), (cx + 14.5, y + 0.2)])
        band = np.abs(((c.X - cx) / 4.5) % 1 - 0.5)
        c.put(m, 'cloth', 0.3 + 0.3 * (c.Y < y - 1.8) + 0.18 * (band > 0.36) - 0.15 * (np.abs(c.X - cx) > 10.5))
        c.put(m & (band < 0.12) & (c.Y < y - 1), 'cloth2', 0.55)
        for x in np.arange(cx - 14, cx + 15, 1.5):
            c.put(c.rect(x, y - 0.7, x + 0.6, y + 0.3) & ~m | c.rect(x, y - 0.6, x + 0.5, y + 0.3) & (np.abs(c.X - cx) > 13.5), 'cloth2', 0.4)
    elif tag == 'embershelf':   # a squat stone fire-plinth with an iron bowl of live embers on it
        block(c, cx - 7.5, y - 3, cx + 7.5, y + 0.3, 'hstone', 0.4, bevel=0.7, seed=5)
        body = c.poly([(cx - 6, y - 3), (cx - 5, y - 12), (cx + 5, y - 12), (cx + 6, y - 3)])
        v, ny = lit(c, body, sigma=1.6); c.put(body, 'hstone', v)
        block(c, cx - 7, y - 13.5, cx + 7, y - 12, 'hstone', 0.55, bevel=0.6, seed=6)
        c.put(c.rect(cx - 2.5, y - 10, cx + 2.5, y - 5) , 'void', 0.3)                    # an ash-hole in the plinth
        c.put(c.ell(cx, y - 5.6, 2.0, 0.6), 'ember', 0.4)
        bowl = c.ell(cx, y - 14.5, 5.6, 3.0) & (c.Y > y - 15.5)
        c.put(bowl, 'iron', 0.35 + 0.35 * (c.X < cx - 1))
        coals = c.ell(cx, y - 15.6, 4.6, 1.5)
        c.put(coals, 'ember', 0.4 + 0.5 * (c.noise(6, 0.25) > 0.5))
        c.put(c.ell(cx + 1, y - 16.6, 1.3, 0.8) | c.ell(cx - 2, y - 16.4, 1.0, 0.7), 'ember', 0.95)
    elif tag == 'hangingpots':  # a rail hung from the top of the cell: two copper pots and a ladle on hooks
        c.put(c.stroke([(1, 3), (31, 3)], 0.9, 0.9, smooth_pts=False)[0], 'wood', 0.55)
        for (x, L) in ((7, 9), (16, 13), (25, 8)):
            c.put(c.stroke([(x, 3.5), (x, 3.5 + L)], 0.55, 0.55, smooth_pts=False)[0], 'iron', 0.45)
        for (x, top, r, h) in ((7, 12.5, 3.4, 4.5), (25, 11.5, 3.0, 4.0)):
            m = c.ell(x, top + h * 0.45, r, h * 0.55) & (c.Y > top)
            c.put(m, 'clay', lit(c, m, sigma=1.0)[0])
            c.put(c.rect(x - r - 0.3, top - 0.4, x + r + 0.3, top + 0.6), 'clay', 0.75)
        lad = c.ell(16, 18.8, 2.4, 1.8) & (c.Y > 18.2)
        c.put(lad, 'iron', 0.5 + 0.3 * (c.X < 15.5))
    elif tag == 'firewood':     # a stack of split logs, end-grain out
        for i, row in enumerate((5, 4, 3)):
            for j in range(row):
                x = cx - (row - 1) * 2.4 + j * 4.8; yy = y - 2.6 - i * 4.4
                m = c.ell(x, yy, 2.5, 2.3)
                c.put(m, 'wood', 0.3 + 0.3 * (c.X < x - 0.6) - 0.1 * (c.Y > yy + 1))
                ring = np.abs(np.hypot(c.X - x, (c.Y - yy) * 1.05) - 1.2) < 0.32
                c.put(m & (np.hypot(c.X - x, c.Y - yy) < 1.8), 'paper', 0.25 + 0.15 * ring)
        c.put(c.stroke([(cx - 12, y - 0.4), (cx + 12, y - 0.4)], 0.5, 0.5, smooth_pts=False)[0], 'soot', 0.3)
    elif tag == 'stonelantern':  # a tōrō-style stone lantern: base, shaft, the lit fire-box, a curled roof (light y-12)
        block(c, cx - 5.5, y - 3, cx + 5.5, y + 0.3, 'hstone', 0.4, bevel=0.7, seed=1)
        sh = c.rect(cx - 2.2, y - 9, cx + 2.2, y - 3)
        c.put(sh, 'hstone', 0.3 + 0.3 * (c.X < cx - 0.6))
        block(c, cx - 4.5, y - 10.5, cx + 4.5, y - 9, 'hstone', 0.5, bevel=0.5, seed=2)
        box = c.rect(cx - 3.6, y - 16.5, cx + 3.6, y - 10.5)
        c.put(box, 'hstone', 0.35 + 0.3 * (c.X < cx - 2.4))
        win = c.rect(cx - 2.0, y - 15.5, cx + 2.0, y - 11.5)
        c.put(win, 'glow', 0.95 - 0.4 * np.hypot((c.X - cx) / 2, (c.Y - y + 13.5) / 2))
        roof = c.poly([(cx - 7, y - 16), (cx - 5.5, y - 18.2), (cx, y - 21), (cx + 5.5, y - 18.2), (cx + 7, y - 16), (cx + 5, y - 16.6), (cx - 5, y - 16.6)])
        c.put(roof, 'hstone', 0.45 + 0.3 * (c.X < cx) - 0.15 * (c.Y > y - 16.8))
        c.put(c.ell(cx, y - 21.6, 1.0, 1.0), 'hstone', 0.6)
        c.put(roof & (c.noise(3, 0.4) > 0.6), 'herb', 0.45)
    elif tag == 'herbs':         # a planter box of kitchen herbs, a few lavender spikes
        box = c.rect(cx - 12, y - 4.5, cx + 12, y + 0.3)
        c.put(box, 'wood', 0.35 + 0.1 * (np.abs(((c.X - cx) / 6) % 1 - 0.5) > 0.45) + 0.25 * (c.Y < y - 3.8))
        rng = np.random.default_rng(9)
        for i in range(26):
            x0 = cx - 11 + rng.uniform(0, 22); L = rng.uniform(3, 8); a = rng.uniform(-0.5, 0.5)
            m, U, TT, ax, ay = c.stroke([(x0, y - 4.4), (x0 + math.sin(a) * L * 0.5, y - 4.4 - L * 0.55), (x0 + math.sin(a) * L, y - 4.4 - L)], 0.55, 0.3)
            c.put(m, 'herb', 0.3 + 0.45 * TT + 0.15 * (a < 0))
        for i in range(5):
            x0 = cx - 9 + i * 4.5 + rng.uniform(-1, 1); L = rng.uniform(7, 10)
            c.put(c.stroke([(x0, y - 4.4), (x0 + 0.5, y - 4.4 - L)], 0.3, 0.3)[0], 'herb', 0.4)
            c.put(c.stroke([(x0 + 0.4, y - 4.4 - L * 0.6), (x0 + 0.5, y - 4.4 - L)], 0.55, 0.45)[0], 'flower', 0.55 + 0.2 * (i % 2))
    near = {'lantern': ('paper',), 'stonelantern': ('glow',), 'embershelf': ('ember', 'void')}.get(tag, ())
    return finish(c, near_skip=near)


# =============================================================================================== xsc_ruins (new sheet)
BASALT = ramp('#090606', '#100b0a', '#18100e', '#211613', '#2b1d19', '#38261f', '#4a3226', '#5e4030')


def ruins_frames():
    """Pieces of the basalt colonnades XS_KIND.ruins bakes into the Ember's back layer (55_sc.js): a 16 px shaft tile that repeats
    seamlessly, a base, a capital, two broken tops. 24x16 frames, column 10 px wide centred on x=12; the right edge is lit by
    the ember glow (the old bake's 1 px orange line)."""
    w, h = 24, 16
    def col(c, y0, y1, seed):
        m = c.rect(7, y0, 17, y1)
        U = np.clip((c.X - 12) / 5, -1, 1)
        flute = np.cos((c.X - 7) / 10 * 4 * 2 * math.pi)
        v = c.cyl(U, np.zeros_like(U), -np.ones_like(U), light=(-0.5, -0.5, 0.7), amb=0.22, key=0.55) + 0.1 * flute
        v += 0.06 * np.sin(c.Y * 2 * math.pi / 16 * 3 + c.X * 0.7 + seed)            # periodic in y (tiles)
        c.put(m, 'basalt', v)
        c.put(m & (c.X > 16), 'ember', 0.22)                                             # ember-lit edge
        return m
    frames = {}
    for i in range(2):
        c = Pc(w, h); col(c, -1, 17, i)
        c.put(c.rect(7, 4.6 + i * 6, 17, 5.4 + i * 6), 'basalt', 0.05)                   # a drum joint
        c.put(c.stroke([(11 + i * 2, 0), (12 + i * 2, 5), (11 + i * 2, 9)], 0.35, 0.3)[0], 'basalt', 0.08)   # a crack
        frames['shaft%d' % i] = c
    c = Pc(w, h); col(c, -1, 12, 3)
    c.put(c.rect(5.5, 9.5, 18.5, 12.2), 'basalt', 0.5); c.put(c.rect(4, 12, 20, 16.3), 'basalt', 0.4)
    c.shift(c.rect(4, 12, 20, 13), 0.15); c.shift(c.rect(18.5, 9.5, 20, 16.3), -0.2)
    c.put(c.rect(19, 12, 20, 16.3) | c.rect(18, 9.5, 18.5, 12.2), 'ember', 0.3)
    frames['base'] = c
    c = Pc(w, h); col(c, 12, 17, 4)
    c.put(c.rect(5, 8.5, 19, 12), 'basalt', 0.7); c.put(c.rect(6.5, 12, 17.5, 13.2), 'basalt', 0.5)
    c.shift(c.rect(5, 8.5, 19, 9.5), 0.25); c.shift(c.rect(17.5, 8.5, 19, 12), -0.3); c.put(c.rect(18.4, 9, 19, 12), 'ember', 0.3)
    frames['cap'] = c
    for i, jag in enumerate(([(7, 16), (7, 9), (9, 7.5), (11, 10), (13, 6.5), (15, 8.5), (17, 7.8), (17, 16)],
                             [(7, 16), (7, 11), (10, 8.5), (12, 11.5), (14.5, 9.5), (17, 12), (17, 16)])):
        c = Pc(w, h); m = col(c, 0, 17, 5 + i); c.erase(m & ~c.poly(jag))
        c.put(c.stroke(jag[1:-1], 0.5, 0.5)[0] & c.cov, 'basalt', 0.15)
        frames['broken%d' % i] = c
    out = {}
    for k, c in frames.items():
        s_ = c.resolve(0.5); s_.index({'basalt': BASALT, 'ember': EMBER}, dk=0.0)
        out[k] = to_img(s_.rgba({'basalt': BASALT, 'ember': EMBER}))
    return out


def build_ruins():
    import asebuild
    fr = ruins_frames(); order = ['shaft0', 'shaft1', 'base', 'cap', 'broken0', 'broken1']
    tags = [('shaft', 0, 1), ('base', 2, 2), ('cap', 3, 3), ('broken', 4, 5)]
    asebuild.build('xsc_ruins', 24, 16, ['Layer'], [{'ms': 100, 'cels': {'Layer': fr[k]}} for k in order], tags)
    # a preview: a column of 5 shaft tiles with base and cap, and one broken
    c = Image.new('RGBA', (60, 120), (30, 20, 18, 255))
    for x0, top in ((4, 'cap'), (32, 'broken0')):
        for i in range(6): c.alpha_composite(fr['shaft%d' % (i % 2)], (x0, 20 + i * 16))
        c.alpha_composite(fr['base'], (x0, 100)); c.alpha_composite(fr[top], (x0, 8))
    prev('xsc_ruins', [c], player=True, scale=4)


# =============================================================================================== build
def main():
    todo = ARGS or ['shrine', 'tree', 'hearth', 'pine', 'shelves', 'hut', 'small', 'ruins']
    if 'ruins' in todo and not NO_ASE: build_ruins()
    m_rep, l_rep, s_rep = {}, {}, {}
    v1m, v1s, v1l = P.v1_frames('xsc_m'), P.v1_frames('xsc_s'), P.v1_frames('xsc_l')
    if 'shrine' in todo:
        m_rep['deadshrine'] = [deadshrine(n) for n in range(4)]; prev('xsc_m_deadshrine', m_rep['deadshrine'] + v1m[3:7])
    if 'tree' in todo:
        m_rep['deadtree'] = [deadtree(v) for v in range(2)]; prev('xsc_m_deadtree', m_rep['deadtree'] + v1m[7:9])
    if 'hearth' in todo:
        m_rep['hearth'] = [hearth(f) for f in range(6)]; prev('xsc_m_hearth', m_rep['hearth'] + v1m[11:13])
    if 'pine' in todo:
        m_rep['pine'] = pine(); prev('xsc_m_pine', [m_rep['pine'], v1m[22]])
    if 'shelves' in todo:
        m_rep['shelves'] = shelves(); prev('xsc_m_shelves', [m_rep['shelves'], v1m[21]])
    if 'hut' in todo:
        l_rep['hut'] = hut(); prev('xsc_l_hut', [l_rep['hut'], v1l[11]])
    if 'small' in todo:
        tags = ['lantern', 'jars', 'rug', 'embershelf', 'hangingpots', 'firewood', 'stonelantern', 'herbs']
        for t in tags: s_rep[t] = small(t)
        prev('xsc_s_ember', [s_rep[t] for t in tags] + [v1s[16 + i] for i in range(8)])
    if not NO_ASE and not ARGS:
        import gen_props_c_starfall as SF
        SF.ARGS[:] = ['xsc']; SF.NO_ASE = True; SF.main()
        s_rep.update(SF.STARFALL_XSC['xsc_s']); l_rep.update(SF.STARFALL_XSC['xsc_l'])
        P.build_sheet('xsc_s', s_rep); P.build_sheet('xsc_m', m_rep); P.build_sheet('xsc_l', l_rep)
        print('built xsc_s', sorted(s_rep), 'xsc_m', sorted(m_rep), 'xsc_l', sorted(l_rep))


if __name__ == '__main__':
    main()
