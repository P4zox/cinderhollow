#!/usr/bin/env python3
"""Props batch C, Starfall (docs/v17/props_c.md). Cold crystalline relics on the black glass plains, rebuilt with the v1 contract:

  sf_spire      32x40   loop 4f    black-glass spires with a cold core (the 4 frames: the core breathing, a glint climbing)
  sf_godbone    96x56   idle       a dead god's vertebra and ribs, sunk in the glass
  sf_idol       48x48   idle       a god's broken head, eyes closed, a snapped halo
  sf_lens       24x40   loop 4f    a star-lens on a bronze stand (the frames: the caustic turning in the glass)
  sf_arch       48x80   idle       a fluted observatory pillar and the broken spring of its arch
  sf_orrering   48x48   loop 8f    a broken armillary: the inner ring turns (geometry per frame, no flicker)
  sf_telescope  64x64   idle       the great telescope on its iron tripod, lens cracked
  xsc_s         emberrock, wayshrine (32x32)        xsc_l   dome (128x128)       (all other xsc tags keep their v1 pixels)

Palettes: obsidian and starlight from tiles_starfall / bg_starfall_mid / vista_sf16 (indigo-black, cold blue-white), a cool
grey stone, cold ivory bone, tarnished bronze with verdigris. Key light from the upper left, a cold blue rim from the sky.

  python3 art/gen_props_c_starfall.py [spire godbone idol lens arch orrery telescope xsc ...] [--no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import props_c_lib as P
from props_c_lib import Pc, ramp, selout, to_img, T, S

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
NO_ASE = '--no-ase' in sys.argv

OBS = ramp('#05050b', '#0a0b16', '#11132a', '#191d3c', '#232a52', '#303a6a', '#44518a', '#6476b4', '#9aaee4')
ICE = ramp('#1a2450', '#2c3c78', '#45609e', '#6e8cc4', '#a4bce0', '#dce8fa', '#ffffff')
STONE = ramp('#0e0f16', '#171922', '#21242f', '#2d313e', '#3c414f', '#4e5462', '#636a78', '#7c8390', '#989eaa', '#b8bdc6')
BONE = ramp('#121117', '#1d1b22', '#2a2730', '#38343d', '#49444d', '#5d5760', '#746d75', '#8f878d', '#aca3a6', '#c9c1c0')
BRONZE = ramp('#0f0d0d', '#1a1614', '#26201c', '#352c25', '#463a30', '#5b4b3c', '#735f4b', '#8e775d', '#ab9474')
VERD = ramp('#16231f', '#22362f', '#304b42', '#426257', '#5a7c6e')
IRON = ramp('#07080b', '#0f1116', '#181b22', '#232730', '#30353f', '#424955', '#5a626e')
OUT = (4, 4, 10)
R = {'obs': OBS, 'ice': ICE, 'stone': STONE, 'bone': BONE, 'bronze': BRONZE, 'verd': VERD, 'iron': IRON, 'core': ICE,
     'glass': OBS, 'crack': ICE, 'void': ramp('#020206', '#06060e', '#0b0c18')}
L_KEY = (-0.6, -0.7, 0.4)


def prev(name, imgs, **kw):
    kw.setdefault('scale', 6 if max(i.height for i in imgs) <= 48 else 3)
    P.preview(name, imgs, bg=(14, 15, 30), **kw)


def finish(c, rim=('obs', 'stone', 'bone', 'bronze', 'iron'), dk=0.3, near_skip=(), steps=1, rimw=(1.0, 0.6, 0.35, 0.0)):
    s = c.resolve(0.45)
    s.index(R, dk=dk).rim(R, mats=set(rim), wts=rimw, steps=steps, minv=0.15)
    o = s.rgba(R)
    for (x, y, col) in getattr(c, 'stamps', []):
        if 0 <= x < o.shape[1] and 0 <= y < o.shape[0]: o[y, x, :3] = col; o[y, x, 3] = 255
    near = s.alpha & ~np.logical_or.reduce([s.m(n) for n in near_skip]) if near_skip else None
    return selout(o, OUT, lit_k=0.4, near=near), s


def lam(n, light=L_KEY):
    L = P.unit(light); n = P.unit(n); return max(0.0, float(n @ L))


# =============================================================================================== crystals
def crystal(c, base_x, base_y, h, w, lean=0.0, seed=0, core=0.6, glint=None, mat='obs'):
    """A prism of black glass: a lit left face and a dark right face meeting in a ridge, a pointed termination, a vein of cold
    light inside. Returns its mask."""
    tipx = base_x + lean * h; tipy = base_y - h
    sh = h * 0.22                                            # termination length
    lx0, rx0 = base_x - w, base_x + w
    lx1 = lx0 + lean * (h - sh); rx1 = rx0 + lean * (h - sh); my1 = base_y - (h - sh)
    ridge0 = base_x + w * 0.15; ridge1 = ridge0 + lean * (h - sh)
    left = [(lx0, base_y), (lx1, my1), (tipx, tipy), (ridge1, my1 + 0.5), (ridge0, base_y)]
    right = [(ridge0, base_y), (ridge1, my1 + 0.5), (tipx, tipy), (rx1, my1), (rx0, base_y)]
    ml, mr = c.poly(left), c.poly(right)
    tt = np.clip((base_y - c.Y) / h, 0, 1)                    # 0 base .. 1 tip
    n = c.noise(seed, 0.6)
    vl = 0.32 + 0.38 * tt + 0.08 * (n - 0.5)
    vr = 0.12 + 0.16 * tt + 0.06 * (n - 0.5)
    c.put(ml, mat, vl); c.put(mr, mat, vr)
    # the termination facets: the upper left plane catches the sky
    term = c.poly([(lx1, my1), (tipx, tipy), (ridge1, my1 + 0.5)])
    c.put(term, mat, 0.85)
    # inner light: a vein up the crystal, brighter towards the middle
    vein = c.stroke([(base_x + w * 0.05, base_y - 1), (base_x + w * 0.05 + lean * h * 0.55, base_y - h * 0.55), (tipx - lean * 1, tipy + sh * 1.2)],
                    max(0.5, w * 0.22), 0.3)[0] & (ml | mr)
    c.put(vein, 'core', np.clip(core * (0.55 + 0.6 * np.sin(np.pi * tt)), 0, 1))
    # a bright edge down the ridge
    edge = c.stroke([(ridge0, base_y), (ridge1, my1 + 0.5), (tipx, tipy)], 0.32, 0.25)[0]
    c.put(edge, mat, 0.95 if glint is None else 0.75)
    if glint is not None:   # a glint at a point along the ridge (0..1)
        gy = base_y - h * glint; gx = ridge0 + lean * (h * glint)
        c.put(c.ell(gx, gy, 0.6, 0.6), 'core', 1.0)
    return ml | mr


def glass_pool(c, cx, y, rx, ry=1.6):
    m = c.ell(cx, y, rx, ry) & (c.Y < y + 0.3) | (c.ell(cx, y, rx, ry) & (c.Y >= y))
    c.put(m, 'glass', 0.18 + 0.4 * np.exp(-((c.X - cx + rx * 0.3) / (rx * 0.35)) ** 2) * (c.Y < y))
    return m


# =============================================================================================== sf_spire
def spire_model(f):
    c = Pc(32, 40); y = 39.8
    ph = f * math.pi / 2
    specs = [(6.5, 13, 2.6, -0.28, 4), (24.0, 21, 3.3, 0.22, 3), (11.0, 27, 3.6, -0.12, 1), (17.5, 37, 4.4, 0.05, 2), (27.5, 10, 2.2, 0.35, 5)]
    for (x, h, w, lean, s) in specs:
        core = 0.55 + 0.35 * math.sin(ph + s * 1.3)
        g = ((f * 0.25 + s * 0.17) % 1.0) * 0.8 + 0.1 if s in (2, 3) else None
        crystal(c, x, y, h, w, lean, seed=s, core=core, glint=g)
    glass_pool(c, 16, y - 0.6, 14, 1.4)
    return c


def spire():
    out = []
    for f in range(4):
        o, s = finish(spire_model(f), rim=('obs',), rimw=(1.0, 0.8, 0.0, 0.0))
        out.append(to_img(o))
    return out


# =============================================================================================== sf_godbone
def bone_tex(c, m, seed, k=1.0):
    n1 = c.noise(seed, 0.5); n2 = c.noise(seed + 1, 1.6)
    pores = (n1 > 0.7) * 0.18
    return k * (0.08 * (n2 - 0.5) - pores)


def godbone_model():
    w, h = 96, 56; c = Pc(w, h); y = 55.8
    # ribs: long flattened curves rising from the glass, a groove along each
    ribs = [([(10, y + 1), (12, 40), (20, 22), (32, 10), (44, 6)], 4.4, 1.0, 11), ([(26, y + 1), (27, 42), (33, 28), (42, 19), (50, 17)], 3.6, 0.9, 12),
            ([(86, y + 1), (85, 44), (80, 32), (73, 25)], 3.8, 1.6, 13)]
    for pts, r0, r1, sd in ribs:
        m, U, TT, ax, ay = c.stroke(pts, r0, r1, rprof=lambda t, r0=r0, r1=r1: r1 + (r0 - r1) * (1 - t) ** 0.7)
        v = c.cyl(U, ax, ay, light=L_KEY, amb=0.16, key=0.72) + bone_tex(c, m, sd)
        v -= 0.18 * (np.abs(U - 0.25) < 0.12)                # the groove
        c.put(m, 'bone', v)
    # the broken end of the right rib: a jagged, darker break
    c.put(c.poly([(70.5, 26), (73, 22.5), (75.5, 25.5), (74, 27.5)]), 'bone', 0.12)
    # the vertebra: body, the neural arch, the spinous process raking back, transverse wings
    body = c.poly([(36, y), (36.5, 44), (40, 39), (50, 37.5), (60, 39), (64, 44), (64.5, y)])
    nx, ny, nzv = c.normals(body, sigma=4.0); d = np.clip(nx * -0.6 + ny * -0.7 + nzv * 0.4, 0, 1) / 0.95
    c.put(body, 'bone', 0.18 + 0.62 * d + bone_tex(c, body, 21))
    c.put(c.ell(50, 46.5, 9.0, 1.0), 'bone', 0.15)           # the growth plate seam
    arch = c.poly([(41, 39.5), (44, 31), (50, 28), (56, 31), (59, 39.5)])
    nx, ny, nzv = c.normals(arch, sigma=2.5); d = np.clip(nx * -0.6 + ny * -0.7 + nzv * 0.4, 0, 1) / 0.95
    c.put(arch, 'bone', 0.2 + 0.6 * d + bone_tex(c, arch, 22))
    c.put(c.ell(50, 35.2, 3.2, 2.4), 'void', 0.2)            # the spinal canal
    sp, U, TT, ax, ay = c.stroke([(50, 30), (54, 20), (60, 11), (66, 5)], 3.4, 1.2)
    c.put(sp, 'bone', c.cyl(U, ax, ay, light=L_KEY, amb=0.16, key=0.72) + bone_tex(c, sp, 23))
    for sd in (-1, 1):
        tp, U, TT, ax, ay = c.stroke([(50 + sd * 7, 34), (50 + sd * 13, 30), (50 + sd * 18, 31.5)], 2.6, 1.2)
        c.put(tp & ~arch, 'bone', c.cyl(U, ax, ay, light=L_KEY, amb=0.16, key=0.72) + bone_tex(c, tp, 24 + sd))
    # cracks with starlight in them
    for pts in ([(45, 41), (47, 45), (46, 50), (48, 54)], [(57, 9), (58, 13), (56.5, 16)], [(17, 32), (19, 35), (18, 39)]):
        m = c.stroke(pts, 0.35, 0.3)[0] & c.cov
        c.put(m, 'crack', 0.7)
    # crystals of black glass grown through the bones
    crystal(c, 30, y - 1, 12, 2.2, -0.25, seed=5, core=0.5)
    crystal(c, 68, y - 1, 9, 1.8, 0.3, seed=6, core=0.45)
    crystal(c, 72, y - 1, 15, 2.6, 0.12, seed=7, core=0.6)
    glass_pool(c, 48, y - 1.6, 44, 2.0)
    return c


def godbone():
    o, s = finish(godbone_model(), rim=('bone', 'obs'), rimw=(1.0, 0.7, 0.3, 0.0))
    return to_img(o)


# =============================================================================================== sf_idol
def idol_model():
    w, h = 48, 48; c = Pc(w, h); y = 47.8
    cx, cy = 24.0, 25.0
    X, Y = c.X - cx, c.Y - cy
    # a height field of a calm face, three-quarter to the left, carved out of pale stone
    head = ((X / 13.5) ** 2 + (Y / 18.0) ** 2) <= 1
    chip = c.poly([(29, 4), (40, 10), (38, 18), (33, 14), (30, 15), (27, 9)])            # a chunk broken off the crown
    head &= ~chip
    hgt = np.sqrt(np.clip(1 - (X / 13.5) ** 2 - (Y / 18.0) ** 2, 0, 1)) * 9
    g = lambda x0, y0, sx, sy, a: a * np.exp(-((X - x0) / sx) ** 2 - ((Y - y0) / sy) ** 2)
    hgt += g(-1.5, -9, 9, 3.0, 1.2)                          # forehead
    hgt += g(-5, -3.2, 3.6, 1.0, 1.0) + g(4, -3.2, 3.6, 1.0, 1.0)      # brow ridges
    hgt -= g(-5, -1.0, 3.0, 1.5, 1.6) + g(4.2, -1.0, 3.0, 1.5, 1.6)    # eye sockets
    hgt += g(-5, -0.6, 2.4, 0.8, 0.7) + g(4.2, -0.6, 2.4, 0.8, 0.7)    # closed lids
    hgt += g(-0.8, 3.5, 1.5, 4.8, 2.6) + g(-0.8, 7.8, 2.2, 1.2, 1.0)    # nose
    hgt += g(-0.6, 11.6, 3.6, 0.8, 0.7) - g(-0.6, 12.5, 3.2, 0.35, 0.8) + g(-0.6, 13.4, 3.0, 0.8, 0.5)   # lips
    hgt += g(-0.5, 17, 4.0, 2.2, 0.8) + g(-8, 6, 3.4, 4.0, 0.6) + g(7, 6, 3.4, 4.0, 0.6)    # chin, cheeks
    gy, gx = np.gradient(hgt * S)
    n = np.sqrt(gx * gx + gy * gy + 1); nx, ny, nz = -gx / n, -gy / n, 1 / n
    Lk = P.unit(L_KEY); d = np.clip(nx * Lk[0] + ny * Lk[1] + nz * Lk[2], 0, 1)
    rimr = np.clip(nx * 0.9 + ny * -0.3, 0, 1) ** 3                     # the cold sky rim on the right cheek
    v = 0.2 + 0.8 * d + 0.25 * rimr + 0.06 * (c.noise(41, 0.6) - 0.5)
    cr, cid = c.cracks(42, cell=7, aspect=1.3, width=0.06)
    v -= 0.15 * cr
    c.put(head, 'stone', v)
    # the lid lines and the parting of the lips
    for pts in ([(-7.4, -0.2), (-5, 0.6), (-2.6, -0.1)], [(1.8, -0.2), (4.2, 0.6), (6.6, -0.1)], [(-3.6, 12.4), (-0.6, 12.9), (2.4, 12.4)]):
        c.put(c.stroke([(cx + a, cy + b) for a, b in pts], 0.33, 0.33)[0] & head, 'stone', 0.06)
    # the broken face of the chip: rough and dark
    edge = c.stroke([(29, 4.5), (27.4, 9), (30, 15), (33, 14), (38, 18)], 0.9, 0.9)[0] & head
    c.put(edge, 'stone', 0.25 + 0.2 * c.noise(43, 0.3))
    # the snapped halo behind: a thin ring of tarnished bronze, broken at the upper right
    for i in range(70):
        a = math.pi * (0.06 + i / 69 * 0.66)
        x, yy = cx + math.cos(a) * 20.5, cy - 3 - math.sin(a) * 20.5
        m = c.ell(x, yy, 1.1, 1.1) & ~head
        c.put(m, 'bronze', 0.35 + 0.45 * max(0.0, -math.cos(a + 0.6)))
    for i in range(8):
        a = math.pi * (0.06 + i / 7 * 0.66); x, yy = cx + math.cos(a) * 20.5, cy - 3 - math.sin(a) * 20.5
        c.put(c.poly([(x - 1.6 * math.cos(a), yy + 1.6 * math.sin(a)), (x + 3.6 * math.cos(a) + 0.6, yy - 3.6 * math.sin(a)),
                      (x + 3.6 * math.cos(a) - 0.6, yy - 3.6 * math.sin(a))]) & ~head, 'bronze', 0.55)
    # starlight seeping from cracks across the brow and cheek
    for pts in ([(16, 13), (18, 16), (17.5, 19), (19, 21)], [(31, 27), (33, 30), (32, 33)]):
        c.put(c.stroke(pts, 0.4, 0.35)[0] & head, 'crack', 0.75)
    # sunk in the black glass to the jaw
    glass_pool(c, 24, y - 2.4, 21, 2.6)
    c.put(c.rect(4, y - 2.4, 44, y + 1) & c.ell(24, y, 20.5, 4), 'glass', 0.15)
    return c


def idol():
    o, s = finish(idol_model(), rim=('stone', 'bronze'), rimw=(1.0, 0.6, 0.5, 0.0))
    return to_img(o)


# =============================================================================================== sf_lens
def lens_model(f):
    w, h = 24, 40; c = Pc(w, h); y = 39.8
    cx, cy, r = 12.0, 11.0, 7.4
    # a slender bronze stand on a stepped foot
    st, U, TT, ax, ay = c.stroke([(cx, y - 2), (cx, 24), (cx, 18.5)], 1.15, 0.8)
    v = c.cyl(U, ax, ay, light=L_KEY, amb=0.18, key=0.7)
    v += 0.25 * ((np.abs(c.Y - 30) < 0.8) | (np.abs(c.Y - 24) < 0.6))     # collars
    c.put(st, 'bronze', v)
    for (hw, y0, y1, vv) in ((6.5, y - 2.4, y + 0.2, 0.35), (4.5, y - 4.2, y - 2.4, 0.55)):
        m = c.rect(cx - hw, y0, cx + hw, y1); c.put(m, 'bronze', vv + 0.25 * (c.X < cx - hw + 1.5) - 0.15 * (c.X > cx + hw - 1.5))
    c.remat(c.noise(9, 0.25, sy=1.5) > 0.72, 'bronze', 'verd')
    # the ring with its claws, and the lens disc
    ring = c.ell(cx, cy, r + 1.6, r + 1.6) & ~c.ell(cx, cy, r, r)
    ang = np.arctan2(c.Y - cy, c.X - cx)
    c.put(ring, 'bronze', 0.35 + 0.4 * np.clip(-np.sin(ang + 0.7), 0, 1))
    for a in (0.0, 2.1, 4.2):
        q = a + 0.3
        c.put(c.ell(cx + math.cos(q) * (r + 2.0), cy + math.sin(q) * (r + 2.0), 1.3, 1.3), 'bronze', 0.7)
    disc = c.ell(cx, cy, r, r)
    rr = np.hypot(c.X - cx, c.Y - cy) / r
    swirl = np.sin(ang * 2 + f * math.pi / 2 + rr * 4.5)
    c.put(disc, 'glass', 0.25 + 0.35 * (1 - rr) + 0.15 * swirl)
    c.put(disc & (swirl > 0.55) & (rr > 0.3), 'ice', 0.45 + 0.2 * (1 - rr))   # the caustic, turning
    c.put(c.ell(cx - 2.6, cy - 2.8, 1.8, 1.0, rot=-0.6), 'ice', 0.9)         # the sky's reflection
    # the star held in the lens
    star = c.ell(cx, cy, 1.1, 1.1) | (c.rect(cx - 0.35, cy - 3.2 - (f % 2), cx + 0.35, cy + 3.2 + (f % 2)) | c.rect(cx - 3.2 - (f % 2), cy - 0.35, cx + 3.2 + (f % 2), cy + 0.35))
    c.put(star & disc, 'ice', 1.0)
    return c


def lens():
    return [to_img(finish(lens_model(f), rim=('bronze',))[0]) for f in range(4)]


# =============================================================================================== sf_arch
def arch_model():
    w, h = 48, 80; c = Pc(w, h); y = 79.8
    px0, px1 = 8.0, 20.0; cxp = (px0 + px1) / 2; ctop = 30.0
    shaft = c.rect(px0, ctop + 3.5, px1, y - 4)
    U = np.clip((c.X - cxp) / ((px1 - px0) / 2), -1, 1)
    flute = np.cos((c.X - px0) / (px1 - px0) * 5 * 2 * math.pi)
    v = c.cyl(U, np.zeros_like(U), -np.ones_like(U), light=L_KEY, amb=0.18, key=0.75) + 0.08 * flute
    cr, cid = c.cracks(51, cell=6, aspect=2.0, width=0.06)
    v += 0.06 * (c.noise(52, 0.6) - 0.5) - 0.18 * cr
    c.put(shaft, 'stone', v)
    # base (plinth + torus) and the capital
    for (x0, x1, y0, y1, vv) in ((4, 24, y - 4, y + 0.2, 0.42), (6, 22, y - 6.5, y - 4, 0.55), (5, 23, ctop, ctop + 3.5, 0.6), (3.5, 24.5, ctop - 3, ctop, 0.72)):
        m = c.rect(x0, y0, x1, y1)
        c.put(m, 'stone', vv + 0.22 * (c.Y < y0 + 1) - 0.25 * (c.X > x1 - 2.5) + 0.05 * (c.noise(53, 0.5) - 0.5))
    # the arch springing from the capital, voussoir joints, breaking off ragged in the air
    acx, acy, ri, ro = 37.5, ctop - 3.0, 17.5, 23.5
    a = np.arctan2(-(c.Y - acy), c.X - acx); rr = np.hypot(c.X - acx, c.Y - acy)
    deg = np.degrees(a)
    band = (rr >= ri) & (rr <= ro) & (deg > 58) & (deg <= 180) & (c.Y <= acy + 0.01)
    rag = 66 + 7 * np.sin(rr * 1.7) + 4 * np.sin(rr * 4.1)          # the ragged break line
    band &= deg > rag
    tr = (rr - ri) / (ro - ri)
    vv = 0.3 + 0.35 * np.clip(np.sin(a + 0.6), 0, 1) + 0.22 * (tr > 0.84) - 0.18 * (tr < 0.12)
    joint = np.abs(((deg - 90) / 12.0) % 1 - 0.5) > 0.46
    vv -= 0.25 * joint
    vv -= 0.2 * (deg < rag + 2.5)                                    # the broken face
    c.put(band, 'stone', vv + 0.05 * (c.noise(54, 0.6) - 0.5))
    # fallen voussoir fragments at its foot, and a block hanging by a crack
    for (x0, y0, rw, rh, s) in ((34, y - 2, 4.0, 2.4, 1), (40, y - 1.8, 2.6, 1.8, 2), (29, y - 1.5, 2.0, 1.4, 3)):
        m = c.poly([(x0 - rw, y + 0.2), (x0 - rw * 0.8, y0 - rh * 0.6), (x0 + rw * 0.2, y0 - rh), (x0 + rw, y0 - rh * 0.3), (x0 + rw, y + 0.2)])
        c.put(m, 'stone', c.dome(m, sigma=1.0, light=L_KEY, amb=0.2, key=0.6))
    # starlight in the cracks of the shaft
    for pts in ([(15, 28), (16.5, 33), (15.5, 38), (17, 44)], [(11, 55), (12.5, 60), (11.8, 64)]):
        c.put(c.stroke(pts, 0.35, 0.3)[0] & shaft, 'crack', 0.7)
    return c


def arch():
    o, s = finish(arch_model(), rim=('stone',), rimw=(1.0, 0.7, 0.2, 0.0))
    return to_img(o)


# =============================================================================================== sf_orrering
def ring3d(c, cx, cy, r, tilt, spin, width, mat, vbase, front_only=None, gap=None):
    """A flat ribbon ring in 3D (radius r, `width` px wide) rotated by tilt (about x) then spin (about y). Painted back half
    first then the front half. Returns nothing; uses c.put in z order (call twice: front_only False then True)."""
    n = 220
    for i in range(n):
        a = i / n * 2 * math.pi
        if gap and gap[0] <= a <= gap[1]: continue
        x, y_, z = math.cos(a) * r, math.sin(a) * r, 0.0
        y2, z2 = y_ * math.cos(tilt) - z * math.sin(tilt), y_ * math.sin(tilt) + z * math.cos(tilt)
        x3, z3 = x * math.cos(spin) + z2 * math.sin(spin), -x * math.sin(spin) + z2 * math.cos(spin)
        front = z3 > 0
        if front_only is not None and front != front_only: continue
        # the ribbon's normal ~ the radial direction in 3D; light it
        nx, ny, nz = x3 / r, y2 / r, z3 / r
        v = vbase + 0.45 * max(0.0, -0.6 * nx - 0.7 * ny + 0.4 * nz) - (0.0 if front else 0.18)
        c.put(c.ell(cx + x3, cy + y2, width * 0.5 + 0.15, width * 0.5 + 0.15), mat, v)


def orrery_model(f):
    w, h = 48, 48; c = Pc(w, h); y = 47.8
    cx, cy = 24.0, 24.5
    spin = f * math.pi / 8 * 0.5
    rings = [(18.5, 1.25, 0.0, 2.2, 'bronze', 0.42, (2.5, 3.2)), (14.5, 0.35, spin * 2, 1.8, 'bronze', 0.48, None),
             (11.0, 1.0, -spin * 2 + 0.8, 1.6, 'verd', 0.5, (0.4, 1.0))]
    for (r, tilt, sp, wd, mat, vb, gap) in rings: ring3d(c, cx, cy, r, tilt, sp, wd, mat, vb, front_only=False, gap=gap)
    # the axis rod and the crystal heart
    rod = c.stroke([(cx - 2, cy + 20), (cx + 2, cy - 20)], 0.7, 0.6)[0]
    c.put(rod, 'bronze', 0.45)
    core = c.ell(cx, cy, 3.2, 3.2)
    c.put(core, 'ice', 0.35 + 0.55 * np.clip(1 - np.hypot(c.X - cx + 1, c.Y - cy + 1) / 3.2, 0, 1) + 0.08 * math.sin(f * math.pi / 4))
    for (r, tilt, sp, wd, mat, vb, gap) in rings: ring3d(c, cx, cy, r, tilt, sp, wd, mat, vb, front_only=True, gap=gap)
    # the broken mount: a fluted stone foot sunk in glass
    foot = c.poly([(cx - 6, y), (cx - 4, y - 5), (cx + 4, y - 5), (cx + 6, y)])
    c.put(foot, 'stone', 0.3 + 0.3 * (c.X < cx - 1) + 0.15 * (c.Y < y - 4))
    glass_pool(c, cx, y - 1.0, 15, 1.6)
    return c


def orrery():
    return [to_img(finish(orrery_model(f), rim=('bronze', 'verd', 'stone'), rimw=(1.0, 0.6, 0.0, 0.0))[0]) for f in range(8)]


# =============================================================================================== sf_telescope
def telescope_model():
    w, h = 64, 64; c = Pc(w, h); y = 63.8
    # iron tripod
    for (x0, x1) in ((27, 14), (31, 33), (34, 50)):
        m, U, TT, ax, ay = c.stroke([(x0, 41), (x1, y)], 1.4, 1.1)
        c.put(m, 'iron', c.cyl(U, ax, ay, light=L_KEY, amb=0.25, key=0.75))
        c.put(c.ell(x1, y - 0.6, 1.8, 0.9), 'iron', 0.4)
    # the mount: a fork and a drum
    drum = c.ell(31, 40, 4.6, 3.6); c.put(drum, 'bronze', c.dome(drum, sigma=1.2, light=L_KEY, amb=0.18, key=0.7))
    # the great tube, tilted to the sky, banded, the dew-shield at the far end, the eyepiece at the near end
    ang = math.radians(-32); ca, sa = math.cos(ang), math.sin(ang)
    ox, oy = 31.0, 37.5
    def along(u, v): return (ox + ca * u - sa * v, oy + sa * u + ca * v)
    segs = [(-16, -9, 2.2), (-9, 22, 3.6), (22, 33, 4.6)]
    for (u0, u1, r) in segs:
        pts = [along(u0, 0), along(u1, 0)]
        m, U, TT, ax, ay = c.stroke(pts, r, r, smooth_pts=False)
        v = c.cyl(U, ax, ay, light=L_KEY, amb=0.16, key=0.75)
        uu = (c.X - ox) * ca + (c.Y - oy) * sa
        v += 0.2 * (np.abs(((uu - u0) % 7.5) - 0.6) < 0.5) * (u1 - u0 > 10)
        c.put(m, 'bronze', v)
    for u in (-9, 22, 33):   # rims
        m = c.stroke([along(u - 0.6, 0), along(u + 0.6, 0)], [2.8, 4.2, 5.0][[-9, 22, 33].index(u)], smooth_pts=False)[0]
        c.put(m, 'bronze', 0.75)
    c.remat(c.noise(61, 0.25, sy=1.5) > 0.74, 'bronze', 'verd')
    ex, ey = along(-17, 0)
    c.put(c.ell(ex, ey, 1.4, 1.4), 'iron', 0.5)
    # the lens at the far end, cracked, catching starlight
    lx, ly = along(33.4, 0)
    lensm = c.ell(lx, ly, 1.6, 4.2, rot=ang)
    c.put(lensm, 'glass', 0.45 + 0.4 * (c.Y < ly))
    c.put(c.stroke([(lx - 0.6, ly - 3.2), (lx + 0.5, ly - 0.5), (lx - 0.3, ly + 2.6)], 0.3, 0.3)[0] & lensm, 'ice', 1.0)
    c.put(c.ell(lx - 0.4, ly - 2.2, 0.7, 0.7), 'ice', 1.0)
    return c


def telescope():
    o, s = finish(telescope_model(), rim=('bronze', 'iron', 'verd'), rimw=(1.0, 0.6, 0.3, 0.0))
    return to_img(o)


# =============================================================================================== xsc: emberrock, wayshrine, dome
def emberrock_model():
    c = Pc(32, 32); y = 31.8
    pts = [(4, y), (5, y - 5), (9, y - 9.5), (15, y - 11.5), (22, y - 9.5), (27, y - 5.5), (28.5, y)]
    m = c.poly(pts)
    nx, ny, nzv = c.normals(m, sigma=2.2); Lk = P.unit(L_KEY); d = np.clip(nx * Lk[0] + ny * Lk[1] + nzv * Lk[2], 0, 1)
    pits = (c.noise(71, 0.35) > 0.68)
    v = 0.18 + 0.7 * d - 0.15 * pits + 0.06 * (c.noise(72, 0.8) - 0.5)
    c.put(m, 'obs', v)
    for pts in ([(9, y - 2), (12, y - 4.5), (15, y - 4), (18, y - 6.5), (21, y - 6)], [(15, y - 4), (16, y - 1.5)], [(21, y - 6), (24, y - 3.5), (25, y - 1)]):
        c.put(c.stroke(pts, 0.75, 0.6)[0] & m, 'core', 0.72)
    c.put(c.stroke([(12, y - 4.5), (15, y - 4), (18, y - 6.5)], 0.55, 0.5)[0] & m, 'core', 0.95)
    glass_pool(c, 16, y - 0.6, 13, 1.2)
    return c


def wayshrine_model():
    c = Pc(32, 32); y = 31.8
    cx = 16.0
    post = c.rect(cx - 3.2, y - 18, cx + 3.2, y - 2)
    U = np.clip((c.X - cx) / 3.2, -1, 1)
    c.put(post, 'stone', c.cyl(U, np.zeros_like(U), -np.ones_like(U), light=L_KEY, amb=0.18, key=0.72) + 0.05 * (c.noise(81, 0.5) - 0.5))
    c.put(c.rect(cx - 5, y - 2.4, cx + 5, y + 0.2), 'stone', 0.45 + 0.2 * (c.Y < y - 1.8) - 0.2 * (c.X > cx + 3.5))
    roof = c.poly([(cx - 6.2, y - 17.5), (cx, y - 23.5), (cx + 6.2, y - 17.5), (cx + 5.2, y - 16.3), (cx - 5.2, y - 16.3)])
    c.put(roof, 'stone', 0.4 + 0.4 * (c.X < cx) - 0.1 * (c.Y > y - 17))
    c.put(c.ell(cx, y - 24.3, 1.0, 1.0), 'stone', 0.7)
    niche = c.poly([(cx - 2.2, y - 6.5), (cx - 2.2, y - 12), (cx, y - 14.2), (cx + 2.2, y - 12), (cx + 2.2, y - 6.5)])
    c.put(niche, 'void', 0.2)
    flame = c.poly([(cx - 1.2, y - 7), (cx - 0.2, y - 12.8), (cx + 1.2, y - 7)])
    c.put(flame, 'ice', 0.55 + 0.5 * np.clip((c.Y - (y - 12.8)) / 6, 0, 1) * (1 - np.abs(c.X - cx) / 1.4))
    c.put(c.rect(cx - 1.6, y - 7, cx + 1.6, y - 6.2), 'stone', 0.6)
    c.put(c.stroke([(cx + 1.6, y - 4), (cx + 2.4, y - 3), (cx + 1.8, y - 2.4)], 0.3, 0.3)[0], 'crack', 0.6)
    return c


def dome_model():
    """The observatory ruin: a drum of pale stone with pilasters, a ribbed iron dome half fallen in (the sky through it), the
    great telescope's slit and the barrel poking out."""
    w, h = 128, 128; c = Pc(w, h); y = 127.8
    cx = 64.0
    # the drum
    x0, x1, top = 22.0, 106.0, 84.0
    drum = c.rect(x0, top, x1, y - 4)
    U = np.clip((c.X - cx) / ((x1 - x0) / 2), -1, 1)
    v = c.cyl(U, np.zeros_like(U), -np.ones_like(U), light=L_KEY, amb=0.14, key=0.7)
    cr, cid = c.cracks(91, cell=5.5, aspect=0.55, width=0.08)   # ashlar courses
    v -= 0.2 * cr
    v += 0.06 * (c.noise(92, 0.8) - 0.5)
    c.put(drum, 'stone', v)
    for px in (30, 47, 64, 81, 98):                             # pilasters
        m = c.rect(px - 2.5, top - 1, px + 2.5, y - 4)
        uu = np.clip((px - cx) / ((x1 - x0) / 2), -1, 1)
        c.put(m, 'stone', 0.25 + 0.5 * max(0.0, -uu * 0.5 + 0.55) + 0.18 * (c.X < px - 1.4) - 0.15 * (c.X > px + 1.4))
    c.put(c.rect(x0 - 3, top - 4, x1 + 3, top), 'stone', 0.55 + 0.25 * (c.Y < top - 3) - 0.3 * np.clip((c.X - cx) / 50, 0, 1))   # cornice
    c.put(c.rect(x0 - 4, y - 4.5, x1 + 4, y + 0.2), 'stone', 0.4 + 0.2 * (c.Y < y - 3.8) - 0.25 * np.clip((c.X - cx) / 50, 0, 1))   # plinth
    # the door
    door = c.poly([(58, y - 4.5), (58, y - 22), (64, y - 28), (70, y - 22), (70, y - 4.5)])
    c.put(door, 'void', 0.25)
    c.put(c.stroke([(57, y - 4.5), (57, y - 22), (64, y - 29), (71, y - 22), (71, y - 4.5)], 0.8, 0.8)[0] & ~door, 'stone', 0.75)
    # the dome: iron ribs over a skin that has fallen in on the right
    dr = 40.0; dcy = top - 3.0
    dm = c.ell(cx, dcy, dr, 34) & (c.Y < dcy)
    hole = c.poly([(70, 52), (78, 60), (95, 66), (101, 80), (86, 80), (76, 70), (66, 64), (62, 56)])
    skin = dm & ~hole
    nx, ny, nzv = c.normals(dm, sigma=10); Lk = P.unit(L_KEY); d = np.clip(nx * Lk[0] + ny * Lk[1] + nzv * Lk[2], 0, 1)
    plates = (np.abs(np.sin(np.arctan2(c.X - cx, (dcy - c.Y) + 1e-6) * 9)) < 0.08)
    c.put(skin, 'iron', 0.2 + 0.68 * d - 0.15 * plates + 0.04 * (c.noise(93, 0.8) - 0.5))
    c.remat(skin & (c.noise(94, 0.3, sy=2.5) > 0.74), 'iron', 'verd')
    sky = 0.32 + 0.3 * np.clip((c.Y - 52) / 28, 0, 1)
    c.put(hole & dm, 'glass', sky)                                # the night sky seen through the hole
    rng = np.random.default_rng(5); c.stamps = []
    for i in range(14):
        sx, sy = int(rng.uniform(68, 99)), int(rng.uniform(56, 79))
        if c.poly([(70, 52), (78, 60), (95, 66), (101, 80), (86, 80), (76, 70), (66, 64), (62, 56)])[sy * S + 2, sx * S + 2]:
            c.stamps.append((sx, sy, ICE[4 + (i % 3)]))
    # the ribs still standing across the hole
    for k, a in enumerate((0.95, 1.25, 1.55)):
        pts = [(cx + dr * math.cos(t) * 0.999, dcy - 34 * math.sin(t)) for t in np.linspace(0.02, math.pi / 2 + 0.1, 14) if math.cos(t) * dr >= 0]
        pts = [(cx + (px - cx) * a / 1.55, py) for px, py in pts]
        if k == 0: pts = pts[:9]
        m = c.stroke(pts, 0.9, 0.8)[0] & (dm | (c.Y < dcy + 1))
        c.put(m, 'iron', 0.7)
    # the slit, and the telescope barrel through it
    slit = c.poly([(cx - 4, dcy - 33.5), (cx + 4, dcy - 33.5), (cx + 5, dcy - 18), (cx - 5, dcy - 18)])
    c.put(slit & dm, 'void', 0.3)
    ang = math.radians(-58)
    bx, by = cx + 1, dcy - 16
    tube, U2, TT, ax, ay = c.stroke([(bx, by), (bx + math.cos(ang) * 46, by + math.sin(ang) * 46)], 3.2, 3.8, smooth_pts=False)
    c.put(tube, 'bronze', c.cyl(U2, ax, ay, light=L_KEY, amb=0.15, key=0.75))
    c.put(c.ell(bx + math.cos(ang) * 46.5, by + math.sin(ang) * 46.5, 1.6, 3.8, rot=ang), 'glass', 0.8)
    # a crack of starlight up the drum
    c.put(c.stroke([(38, 86), (40, 94), (39, 100), (41, 110)], 0.45, 0.35)[0] & drum, 'crack', 0.7)
    glass_pool(c, cx, y - 1.0, 52, 1.8)
    return c


# =============================================================================================== main
def main():
    todo = ARGS or ['spire', 'godbone', 'idol', 'lens', 'arch', 'orrery', 'telescope', 'xsc']
    def go(name, tag, fn):
        fr = fn(); frs = fr if isinstance(fr, list) else [fr]
        prev(name, frs + P.v1_frames(name)[:len(frs)])
        if not NO_ASE: P.build_sheet(name, {tag: fr})
    if 'spire' in todo: go('sf_spire', 'loop', spire)
    if 'godbone' in todo: go('sf_godbone', 'idle', godbone)
    if 'idol' in todo: go('sf_idol', 'idle', idol)
    if 'lens' in todo: go('sf_lens', 'loop', lens)
    if 'arch' in todo: go('sf_arch', 'idle', arch)
    if 'orrery' in todo: go('sf_orrering', 'loop', orrery)
    if 'telescope' in todo: go('sf_telescope', 'idle', telescope)
    if 'xsc' in todo:
        er = to_img(finish(emberrock_model(), rim=('obs',))[0]); ws = to_img(finish(wayshrine_model(), rim=('stone',))[0])
        dm = to_img(finish(dome_model(), rim=('stone', 'iron', 'bronze'), rimw=(1.0, 0.6, 0.2, 0.0))[0])
        v1s, v1l = P.v1_frames('xsc_s'), P.v1_frames('xsc_l')
        prev('xsc_s_starfall', [er, v1s[7], ws, v1s[8]]); prev('xsc_l_dome', [dm, v1l[0]], scale=3)
        STARFALL_XSC.update(xsc_s={'emberrock': er, 'wayshrine': ws}, xsc_l={'dome': dm})


STARFALL_XSC = {}     # gen_props_c_ember.py builds the xsc_* sheets once, with these and the ember/hermit tags

if __name__ == '__main__':
    main()
