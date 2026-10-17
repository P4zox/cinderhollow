#!/usr/bin/env python3
"""NH15 Neon Skyline: the vista (docs/v17/vista_v3.md). "From the roof the city goes on until the rain hides it."

Night rain over NEO-HALLOW. Low cloud lit magenta from below by the city, darker above. The city in three depths: far
towers dissolving into rain-haze (thousands of lit windows, no one behind them), mid towers with neon bands and signs, and
far out where the towers thin, the Pale Root: a colossal petrified trunk, grey as bone, rising out of the city into the
cloud, its flared roots draped over the towers and lit from below by the neon. Rivers of light cross the sky (fx).

  python3 art/gen_vista_nh15.py [--guide | --sweep <sky|far|mid> 1,2,3 [tag] | --pick <name> <seed> [tag] | --no-ase]
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from vista_v3lib import *  # noqa
import bgv2lib as V
import vista_v3lib as L

ROOM = 'NH15'; SRC = src_dir(ROOM)
LW, LH = 512, 240
TINT = '#08081a'
ROOT_X = 262          # the Pale Root's trunk (far layer)


def sky(C):
    nz = C.noise(70, 22, 3); nz2 = C.noise(20, 8, 4)
    C.rgb = C.vgrad([(0, '06061a'), (50, '0e0c26'), (110, '1e1438'), (150, '3a1e4c'), (180, '5a2a5a'), (240, '2a1a3a')])
    # the cloud deck, lit from below by the city: magenta under-glow, violet bodies, darker high
    for (y0, y1, cx, cy, sd, lo, hi, k) in ((10, 70, 120, 18, 31, '12102a', '2a2048', 0.8), (50, 120, 100, 14, 32, '1e1838', '5a3068', 0.85),
                                          (100, 160, 90, 10, 33, '3a2050', 'a04a8a', 0.75)):
        d = C.noise(cx, cy, sd, 3)
        band = smooth(y0, y0 + 14, C.Y) * (1 - smooth(y1 - 14, y1, C.Y))
        m = smooth(0.46, 0.6, d) * band
        C.fill_img(m, lerp(hexc(lo), hexc(hi), np.clip(smooth(y0, y1 + 30, C.Y) * (0.7 + 0.6 * (d - 0.5)), 0, 1)[..., None]), k)
        under = np.clip(m - np.roll(m, int(-3 * S), axis=0), 0, 1)
        C.fill(under, hexc('c060a0'), 0.35 * k)
    C.add(np.exp(-((C.Y - 175) / 30) ** 2) * (0.7 + 0.5 * nz), hexc('6a2a6a'), 0.4)     # the city's glow in the rain-haze
    C.add(np.exp(-((C.Y - 185) / 14) ** 2) * np.exp(-((C.X - 90) / 90) ** 2), hexc('206a8a'), 0.3)   # a cyan district far left
    return C


def root_chains(long=False):
    """The Pale Root: a colossal leaning petrified trunk, two great limbs (long=True: carried on up into the cloud), and
    buttress roots flaring into the city at its foot."""
    trunk = []; x, y = ROOT_X + 10, 214.0
    for i in range(62):          # the trunk, leaning a little left as it rises, tapering
        t = i / 62; nx = x - 0.3 + 0.5 * math.sin(i / 10); ny = y - 3.6
        trunk.append((x, y, nx, ny, (62 if long else 50) * (1 - 0.42 * t) + 3 + (22 * (1 - smooth(0, 0.12, t)) if long else 0))); x, y = nx, ny
    if long: trunk = [(ROOT_X + 10, 256.0, ROOT_X + 10, 214.0, trunk[0][4])] + trunk     # the foot runs on below the frame
    chains = [trunk]
    rng = np.random.default_rng(7)
    limbs = ((0.42, -2.8, 44, 15), (0.7, -0.45, 40, 12))
    if long: limbs = ((0.42, -2.75, 90, 19), (0.62, -0.5, 84, 16), (0.8, -2.1, 60, 11))
    for frac, ang, ln, w in limbs:
        ch = []; px, py = trunk[int(frac * 61)][0], trunk[int(frac * 61)][1]; a = ang
        for j in range(int(ln / 3)):
            a += rng.normal(0, 0.05) + (-math.pi / 2 - a) * 0.02
            nx, ny = px + math.cos(a) * 3, py + math.sin(a) * 3
            ch.append((px, py, nx, ny, max(3.0, w * (1 - 0.6 * j / (ln / 3))))); px, py = nx, ny
        chains.append(ch)
    if long:
        for sx, sy, ex, ey, w in ((-26, 192, -66, 232, 16), (-14, 202, -40, 236, 12), (26, 194, 64, 232, 15), (12, 204, 38, 236, 11)):
            ch = []; p0 = (ROOT_X + 10 + sx, sy); p2 = (ROOT_X + 10 + ex, ey); p1 = (p0[0] + (p2[0] - p0[0]) * 0.45, p0[1] + (p2[1] - p0[1]) * 0.35); prev = p0
            for j in range(1, 13):
                t = j / 12; q = ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
                ch.append((prev[0], prev[1], q[0], q[1], w * (1 - 0.35 * t))); prev = q
            chains.append(ch)
    return chains


def root_mask(C):
    return C.mask_lines([q for ch in root_chains() for q in ch]), None


B = ['0e0a18', '141022', '1a162c', '221c38', '2a2444', '342c50', '3e365c', '4a4068']     # bark: dark violet-grey, never glowing
RIM_C = ['22506a', '2a7090', '3a98b8']                                          # cyan, from the district on the left
RIM_M = ['5a2a5a', '84387a', 'b04a90']                                          # magenta, from the city on the right and below


def draw_root(q, al, sky, near_row):
    """The Pale Root drawn crisp at 1x over the far layer (lead review: it read as a flat pale smear). Dark furrowed bark
    following the trunk, neon rim light on both edges (cyan left, magenta right, stronger toward the city below), a magenta
    up-light at the foot, buttress roots into the city, rain haze at its foot and the crown lost in the cloud."""
    chains = root_chains(long=True)
    inside, u, along, hw, ch = seg_field(chains, LW, LH)
    P = lambda k: hexc(k)
    yy = np.arange(LH)[:, None] * np.ones((1, LW)); xx = np.ones((LH, 1)) * np.arange(LW)[None, :]
    nz = noise(LW, LH, 5, 22, 91, 2); nzb = noise(LW, LH, 3, 9, 92, 2)
    low = np.clip((yy - 60) / 150, 0, 1)                                          # 0 high in the sky .. 1 at the city
    # bark: lit a little from the left (the cyan district), furrows every ~3.5 px following the limb, ridge highlights
    v = 0.36 - 0.3 * u - 0.12 * u * u + 0.16 * (nz - 0.5) + 0.12 * low
    fpos = (u * hw / 3.6 + 0.5 * np.sin(along / 15 + ch * 1.9) + 0.3 * (nzb - 0.5)) % 1
    furrow = (fpos < 0.2) & (np.abs(u) < 0.88); ridge = (fpos > 0.2) & (fpos < 0.38) & (u < 0.45)
    v = np.where(furrow, v - 0.2, np.where(ridge, v + 0.16, v))
    bark = np.array([P(k) for k in B])[np.clip((v * 7.99).astype(int), 0, 7)]
    # the up-light: magenta from the street below on the lower trunk and buttresses
    up = np.clip((yy - 150) / 60, 0, 1) * (0.35 + 0.65 * (u > -0.2))
    bark = np.where((up > 0.5)[..., None] & furrow[..., None] == False, bark * 0.7 + P('5a2a5a') * 0.3 * (up[..., None] + 0.5), bark)
    out = np.where(inside[..., None], bark, q)
    # rims: outer px and a second one, cyan on the left edge and magenta on the right; they fade up into the dark sky
    e1 = inside & (np.abs(u) * hw > hw - 1.05); e2 = inside & ~e1 & (np.abs(u) * hw > hw - 2.05) & (hw > 4)
    lvl = np.clip((0.6 + low * 3.4 + 0.6 * (nz - 0.5)).astype(int), 0, 3)        # 0: no rim, 1..3 ramp steps
    for e, d in ((e1, 0), (e2, 1)):
        k = np.clip(lvl - 1 - d, -1, 2)
        for side, ramp in ((-1, RIM_C), (1, RIM_M)):
            m = e & (np.sign(u) == side) & (k >= 0)
            out = np.where(m[..., None], np.array([P(c) for c in ramp])[np.clip(k, 0, 2)], out)
    # rain haze at the foot: toward the sky/haze colour behind, ordered dither (house style)
    yy_i, xx_i = yy.astype(int), xx.astype(int)
    th = (V.B4[yy_i & 3, xx_i & 3] + 0.5) / 16
    hz = np.clip((yy - 186) / 40, 0, 0.6)
    out = np.where((inside & (hz > th))[..., None], P('3a2858') * 0.6 + out * 0.4, out)
    # the crown and the limbs lost in the cloud: cut away above a ragged cloud line, a cloud band across the trunk
    # cloud strata cross it more and more thickly with height: a pixel is cloud where the streaky cloud field beats a
    # threshold that falls as the trunk rises; just under each cut a dithered fringe veils it
    cl = noise(LW, LH, 46, 5, 93, 3)
    lim = np.clip((yy - 18) / 110, 0, 1) * 0.55 + 0.45
    cut = cl > lim
    thin = (cl > lim - 0.07) & ~cut
    out = np.where((inside & thin & (th < 0.6))[..., None], sky * 0.55 + out * 0.45, out)
    draw = inside & ~cut & ~near_row
    old = np.asarray(Image.fromarray((root_mask(Canvas(LW, LH))[0] * 255).astype(np.uint8)).resize((LW, LH), Image.BOX), float) > 60
    q[:] = np.where(draw[..., None], out, q)
    al[:] = (al & ~((inside | old) & ~draw & ~near_row)) | draw          # the render's own (old) trunk never shows through
    return q


def towers(rng, y_lo, y_hi, w_lo, w_hi, x_lo=-10, x_hi=LW + 10):
    out = []; x = x_lo
    while x < x_hi:
        w = rng.uniform(w_lo, w_hi); top = rng.uniform(y_lo, y_hi)
        out.append((x, w, top, int(rng.integers(0, 4)))); x += w + rng.uniform(-w * 0.3, w * 0.5)
    return out


def tower_shape(x, w, top, kind, base=LH + 2):
    if kind == 0: return [(x, base), (x, top), (x + w, top), (x + w, base)]
    if kind == 1: return [(x, base), (x, top + 6), (x + w * 0.5, top), (x + w, top + 6), (x + w, base)]           # gable crown
    if kind == 2: return [(x, base), (x, top + 8), (x + w * 0.2, top + 8), (x + w * 0.2, top), (x + w * 0.8, top), (x + w * 0.8, top + 8), (x + w, top + 8), (x + w, base)]
    return [(x, base), (x + w * 0.1, top + 3), (x + w * 0.5, top - 6), (x + w * 0.9, top + 3), (x + w, base)]  # spire


def far(C):
    """The far city dissolving into rain-haze, and the Pale Root (cover = far layer)."""
    cov = np.zeros_like(C.X); nz = C.noise(30, 30, 41)
    for (x, w, top, k) in towers(np.random.default_rng(31), 158, 186, 5, 13):        # the farthest towers: pale, hazy
        m = C.mask_poly(tower_shape(x, w, top, k))
        C.fill_img(m, lerp(hexc('4a3470'), hexc('7a4a8a'), smooth(150, 210, C.Y)[..., None])); cov = np.maximum(cov, m)
    rm, top = root_mask(C)
    lit = np.clip(0.3 + 0.7 * smooth(ROOT_X + 26, ROOT_X - 16, C.X + 0.25 * (210 - C.Y)), 0, 1)       # lit on its left (the cyan district)
    bark = 0.86 + 0.2 * np.sin((C.X - ROOT_X) * 0.8 + 5 * C.noise(4, 30, 43, 2)) * (C.noise(3, 20, 44, 2) > 0.45)
    rc = lerp(hexc('6a6284'), hexc('c4bcd6'), lit[..., None]) * bark[..., None]
    rc = lerp(rc, hexc('5a4078'), (0.75 * smooth(140, 205, C.Y))[..., None])                    # its foot sunk in the haze
    C.fill_img(rm, rc); cov = np.maximum(cov, rm)
    cl = C.noise(40, 10, 45, 3)
    C.fill(rm * np.clip(smooth(60, 0, C.Y) * (0.5 + 0.9 * cl), 0, 1), hexc('1e1838'), 0.95, cover=False)    # its crown lost in the cloud
    C.fill(rm * np.exp(-((C.Y - 92) / 6) ** 2) * smooth(0.4, 0.6, cl), hexc('3a2858'), 0.8, cover=False)
    for (x, w, top, k) in towers(np.random.default_rng(32), 176, 200, 8, 18):          # a nearer far row in front of its foot
        m = C.mask_poly(tower_shape(x, w, top, k))
        C.fill_img(m, lerp(hexc('2e2050'), hexc('4a2c60'), smooth(170, 240, C.Y)[..., None])); cov = np.maximum(cov, m)
    C.add(np.clip(cov, 0, 1) * np.exp(-((C.Y - 200) / 18) ** 2), hexc('a04a8a'), 0.35)       # the neon haze at street level
    return cov


# the mid towers (crisp, drawn at 1x): x, width, top, crown kind, district (0 cyan / 1 magenta / 2 amber)
MID = [(-6, 30, 118, 0, 0), (26, 18, 148, 3, 0), (46, 26, 104, 2, 0), (80, 15, 152, 1, 2), (98, 32, 130, 0, 0), (142, 20, 162, 3, 1),
       (164, 24, 142, 2, 1), (192, 14, 170, 0, 2), (334, 18, 166, 1, 1), (350, 26, 138, 0, 1), (380, 20, 156, 1, 2), (400, 32, 114, 2, 1),
       (438, 22, 148, 0, 0), (464, 34, 124, 3, 1), (502, 20, 152, 1, 0)]
NEON = {0: ('40d0e8', '80e8f8'), 1: ('e050b0', 'f090d0'), 2: ('f0a040', 'f8d080')}
SIGNS = [(2, 0.66, 22, 30, 1), (4, 0.2, 18, 40, 1), (9, 0.6, 20, 26, 0), (11, 0.14, 26, 34, 0), (13, 0.7, 16, 28, 2)]   # tower, x frac, y off, h, colour
BLINK = []     # antenna tips (x, y): the red lights the fx blinks


def draw_mid(rng):
    """The mid towers as crisp pixel art: dark glass, one neon-lit edge, window grids lit floor by floor, crowns with neon
    bands, vertical signs, antenna masts. Returns rgb, alpha (1x)."""
    rgb = np.zeros((LH, LW, 3)); al = np.zeros((LH, LW), bool)
    im = Image.new('RGBA', (LW, LH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    BLINK.clear()
    for i, (x, w, top, k, dist) in enumerate(MID):
        pts = tower_shape(x, w, top, k, LH + 2)
        d.polygon([(round(px), round(py)) for px, py in pts], fill=(16, 12, 32, 255))
    rgb[:] = np.asarray(im, float)[..., :3]; al[:] = np.asarray(im)[..., 3] > 0
    for i, (x, w, top, k, dist) in enumerate(MID):
        x0, x1 = int(round(x)), int(round(x + w)); n1, n2 = NEON[dist]
        for y in range(int(top), LH):          # body: a slow vertical gradient, the lit left edge
            for xx in range(max(0, x0), min(LW, x1)):
                if al[y, xx]: rgb[y, xx] = lerp(hexc('1a1434'), hexc('0c0a1c'), min(1, (y - top) / 120))
            if 0 <= x0 < LW and al[y, x0]: rgb[y, x0] = lerp(hexc(n1), hexc('1a1434'), 0.55 + 0.35 * min(1, (y - top) / 90))
        y0 = int(top) + (10 if k else 4)
        for fy in range(y0, LH, 3):            # floors: some dark, some lit, a few fully lit
            p = rng.choice([0.0, 0.08, 0.25, 0.5, 0.85], p=[0.18, 0.3, 0.27, 0.17, 0.08])
            for wx in range(x0 + 2, x1 - 1, 2):
                if 0 <= wx < LW and al[fy, wx] and al[fy, wx - 1] and al[fy, min(LW - 1, wx + 1)] and rng.random() < p:
                    c = rng.choice(['f0a040', 'f8d080', 'd8d0e0', n2], p=[0.45, 0.2, 0.2, 0.15])
                    rgb[fy, wx] = lerp(hexc(c), hexc('1a1434'), 0.15 + 0.4 * min(1, (fy - top) / 140))
        if i % 3 == 0 and k in (0, 2):         # a neon band around the crown
            yb = int(top) + (9 if k == 2 else 3)
            for xx in range(max(0, x0), min(LW, x1)):
                if al[yb, xx]: rgb[yb, xx] = hexc(n1); rgb[yb + 1, xx] = lerp(hexc(n1), hexc('1a1434'), 0.5)
        if k != 3:                             # an antenna mast with a red light on top
            ax = int(round(x + w * (0.3 if i % 2 else 0.7))); ah = 8 + (i * 5) % 12; ay = int(top) - (0 if k != 1 else -2)
            for yy in range(ay - ah, ay):
                if 0 <= ax < LW: rgb[yy, ax] = hexc('241c3c'); al[yy, ax] = True
            BLINK.append((ax, ay - ah))
    for (ti, fx_, yo, h, ci) in SIGNS:        # vertical neon signs: abstract glyph columns, no letters
        x, w, top, k, dist = MID[ti]; sx = int(round(x + w * fx_)); sy = int(top) + yo
        c1, c2 = NEON[ci]
        for yy in range(sy, sy + h):
            for xx in range(sx, sx + 4):
                edge = xx in (sx, sx + 3) or yy in (sy, sy + h - 1)
                glyph = ((yy - sy) % 5 in (1, 2, 3)) and xx in (sx + 1, sx + 2) and ((yy - sy) // 5 + xx) % 3 != 0
                rgb[yy, xx] = hexc(c2) if glyph else (hexc(c1) if edge else lerp(hexc(c1), hexc('100c22'), 0.6)); al[yy, xx] = True
    return rgb, al


def mid(C):
    """The guide's mid cover (for the far render's context only)."""
    rgb, al = draw_mid(np.random.default_rng(9))
    m = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((C.WS, C.HS), Image.NEAREST), float) / 255
    C.fill(m, hexc('120e24'))
    return m


def guides():
    gs = sky(Canvas(LW, LH)); gs.save(f'{SRC}/guide_sky.png')
    gf = sky(Canvas(LW, LH)); cf = far(gf); gf.save(f'{SRC}/guide_far.png'); Image.fromarray((np.clip(cf, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/cover_far.png')
    edges(gf.image()).save(f'{SRC}/edge_far.png')
    gm = sky(Canvas(LW, LH)); far(gm); mid(gm); gm.image().save(f'{SRC}/guide_preview.png')


PROMPT = ('pixel art, cyberpunk megacity skyline at night in heavy rain, endless skyscrapers with thousands of lit windows fading '
          'into rain haze, magenta and cyan neon glow on low clouds, far away a colossal petrified pale grey ancient tree trunk '
          'rising out of the city into the clouds, bone white stone bark, lit from below by neon, melancholy, atmospheric, dark '
          'fantasy, highly detailed, deep violet and navy palette with magenta and cyan accents')
RENDER = {
    'far': (PROMPT, dict(denoise=0.6, pix=0.5, edge=True, cn=0.45, cn_end=0.65)),
    'fard': (PROMPT.replace('far away a colossal petrified pale grey ancient tree trunk', 'far away the colossal petrified trunk of a dead world tree, smooth bone white stone with long vertical fissures,'),
             dict(guide='far', denoise=0.45, pix=0.35, edge=True, cn=0.5, cn_end=0.7)),
}

PAL = ['06061a', '0a0a20', '0e0c26', '141030', '1a1438', '201840', '2a1e48', '342454', '3e2a5e', '4a3268', '5a3a74', '6a4280',
       '7a4a8a', '8a5294', 'a05a9a', 'c060a0', 'e070b0', '3a3a5a', '4a4a6a', '5a5470', '7a7488', '9a94a8', 'b8b0c4', 'd8d0e0',
       '206a8a', '2a8aa8', '40c0e0', '80e8f8', 'f0a040', 'f8d080', 'ff4060']


def windows(q, al, rng, n, cols, region=None, grid=True):
    """Crisp lit windows on the towers: 1 px lights in loose columns (the model smears them)."""
    h, w = al.shape; ys, xs = np.nonzero(al)
    if region is not None: k = region[ys, xs]; ys, xs = ys[k], xs[k]
    idx = rng.choice(len(ys), size=min(n, len(ys)), replace=False)
    for i in idx:
        y, x = ys[i], xs[i]
        if grid and (x % 2 or y % 3): continue
        if 0 < y < h - 1 and al[y - 1, x] and al[y + 1, x]: q[y, x] = hexc(rng.choice(cols))


def build(ase=True):
    rng = np.random.default_rng(15)
    a = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    a = knee(grade(a, black=2, white=255, gamma=1.0, sat=1.1), 190, 0.5)
    s = down(a, LW, LH)
    cov = cover_alpha(f'{SRC}/cover_far.png', LW, LH, 0.02)
    sk = fill_under(s, np.asarray(Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), float) > 0)
    q, _ = pixelize(sk, PAL, n_acc=4, dk=0.3); sky_im = to_rgba(q)
    al = cover_alpha(f'{SRC}/cover_far.png', LW, LH)
    rootk, _, _, _, _ = seg_field(root_chains(long=True), LW, LH)
    q, _ = pixelize(s, PAL, n_acc=4, dk=0.25, mask=al)
    windows(q, al & ~rootk, rng, 5000, ('f0a040', 'f8d080', '9a94a8', '80e8f8', 'e070b0'))
    # the nearer far row of towers stands in front of the Root's foot (as in the guide)
    nr = Canvas(LW, LH); m = np.zeros_like(nr.X)
    for (x, w, top, k) in towers(np.random.default_rng(32), 176, 200, 8, 18): m = np.maximum(m, nr.mask_poly(tower_shape(x, w, top, k)))
    near_row = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((LW, LH), Image.BOX), float) > 127
    al = al.copy(); skyq = np.asarray(sky_im.convert('RGB'), float)
    draw_root(q, al, skyq, near_row & (np.arange(LH)[:, None] > 400))   # (the root now stands in front of that row: the city grew around it)
    far_im = to_rgba(np.where(al[..., None], q, 0), al)
    rgb, al = draw_mid(np.random.default_rng(9))
    mid_im = to_rgba(np.where(al[..., None], rgb, 0), al)
    json.dump(BLINK, open(f'{SRC}/blink.json', 'w'))
    ims = {'sky': sky_im, 'far': far_im, 'mid': mid_im}
    for k, im in ims.items(): im.save(f'{SRC}/out_{k}.png')
    preview([(sky_im, 0.02, 0.03, {}), (far_im, 0.05, 0.04, {}), (mid_im, 0.12, 0.08, {})], TINT, f'{SRC}/preview.png', [(0, 100), (256, 100), (0, -60)])
    if ase:
        for k, im in ims.items(): L.build(f'vista_nh15_{k}', [im])


if __name__ == '__main__':
    cli(ROOM, SRC, guides, RENDER, build)
