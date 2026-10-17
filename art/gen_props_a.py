#!/usr/bin/env python3
"""Props batch A (docs/v17/props_a.md, audit docs/v17/PROPS_AUDIT.md): the Dunes and Necropolis props, rebuilt.

Owns xsb_big (all tags), xsb_tall, xsb_du, xsb_nv, du_colossus, du_stele, nv_bell, nv_bell_big, nv_props. Each sheet keeps its
frame size, tags, frame counts, durations and anchors; only the reworked tags' pixels change (the rest is copied from the v1
backup in art/bg_src/props_a/v1/). Painted guides + ComfyUI img2img (cached renders) + palette-locked cleanup: props_a_lib.

  python3 art/gen_props_a.py                 build every sheet from the guides + cached renders (no server needed)
  python3 art/gen_props_a.py --render K,...  (re)render those targets with ComfyUI first (keys: see TARGETS), 'all' for all
  python3 art/gen_props_a.py --only K,...    build only the sheets those targets live in
  python3 art/gen_props_a.py --contact DIR  before/after contact sheets (v1 vs assets/) per sheet
  python3 art/gen_props_a.py --dry          no sheet build (with --preview: look only)
  python3 art/gen_props_a.py --preview DIR   also write guide / render / result previews per target to DIR
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import props_a_lib as L
from props_a_lib import Cv, ramp, hx, pal_of

ARGS = sys.argv[1:]


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


RENDER = set((arg('--render') or '').split(',')) - {''}
ONLY = set((arg('--only') or '').split(',')) - {''}
PREV = arg('--preview')
REF_DU = os.path.join(L.SRC, 'ref_dunes.png')
REF_NV = os.path.join(L.SRC, 'ref_necro.png')


def refs():
    """Style references for IP-Adapter: crops of the new painted backgrounds, upscaled."""
    if not os.path.exists(REF_DU):
        im = Image.open(os.path.join(L.ROOT, 'assets', 'bg_dunes_mid.png')).convert('RGBA').crop((290, 60, 420, 216))
        bg = Image.new('RGBA', im.size, (120, 96, 70, 255)); bg.alpha_composite(im); bg.convert('RGB').resize((im.width * 6, im.height * 6), Image.NEAREST).save(REF_DU)
    if not os.path.exists(REF_NV):
        im = Image.open(os.path.join(L.ROOT, 'assets', 'bg_necropolis_far.png')).convert('RGB').crop((120, 0, 300, 200))
        im.resize((im.width * 5, im.height * 5), Image.NEAREST).save(REF_NV)


# =============================================================================================== the build step per target
DU_PROMPT = ('pixel art game prop, dark fantasy, {obj}, weathered ancient sandstone, wind-eroded, chipped edges, carved relief, '
             'warm sunlight from the upper left, deep umber shadows, soulslike, muted dusty ochre and umber palette, desaturated, side view, '
             'single object, isolated on a plain flat grey background, detailed')
NV_PROMPT = ('pixel art game prop, dark fantasy, {obj}, gothic necropolis, cold moonlight from the upper left, blue-black night shadows, soulslike, '
             'muted desaturated palette, side view, single object, isolated on a plain flat grey background, detailed')


def make(key, cv, obj, region='du', seed=1, denoise=0.5, cn=0.55, cn_end=0.7, mix=0.6, pix=0.6, ref_w=0.25, prompt=None,
         pal=None, mat_pals=None, out_dark=None, out_lit=None, inner=False, rim_col=None, rim_k=0.45, rim_mask=None, thresh=0.5,
         post=None, fx=None, no_outline=None, neg='', sharp=0.5):
    """Guide (cv) -> [AI render] -> frame. mix = how much of the AI render is kept over the guide (0 = guide only)."""
    guide = cv.image()
    rp = os.path.join(L.SRC, f'{key}_render.png')
    if key in RENDER or 'all' in RENDER or (mix > 0 and not os.path.exists(rp)):
        refs()
        p = prompt or (DU_PROMPT if region == 'du' else NV_PROMPT).format(obj=obj)
        print('  render', key, flush=True)
        L.render(key, guide, L.edges(guide, cv.S), p, seed, denoise=denoise, cn=cn, cn_end=cn_end, ref=REF_DU if region == 'du' else REF_NV,
                 ref_w=ref_w, pix=pix, neg_extra=neg)
    hi = cv.rgb
    if mix > 0 and os.path.exists(rp):
        r = np.asarray(Image.open(rp).convert('RGB').resize((cv.W, cv.H), Image.BICUBIC), float)
        hi = cv.rgb * (1 - mix) + r * mix
    rgb, alpha, mats = L.down(cv, hi, thresh=thresh)
    if sharp:   # unsharp mask at 1x (inside the silhouette only): small forms keep their edges through the box filter
        from PIL import ImageFilter as _F
        bl = np.stack([np.asarray(Image.fromarray(np.clip(rgb[..., i], 0, 255).astype(np.uint8)).filter(_F.GaussianBlur(0.8)), float) for i in range(3)], -1)
        rgb = np.clip(rgb + sharp * (rgb - bl) * alpha[..., None], 0, 255)
    if post: rgb = post(rgb, alpha, mats)
    q = L.lock(rgb, alpha, pal, mats, mat_pals)
    q = L.majority(q, alpha)
    if fx: q, alpha = fx(q, alpha)
    if rim_col is not None: q = L.rim(q, alpha, pal, k=rim_k, col=hx(rim_col), mask=rim_mask)
    if out_dark is not None:
        q, alpha = L.outline(q, alpha, hx(out_dark), hx(out_lit) if out_lit else None, inner=inner, skip=no_outline)
    im = L.to_img(q, alpha)
    global LAST_MATS
    LAST_MATS = mats
    if PREV:
        os.makedirs(PREV, exist_ok=True)
        g = guide.resize((guide.width // 2, guide.height // 2))
        parts = [g]
        if os.path.exists(rp): parts.append(Image.open(rp).convert('RGB').resize(g.size))
        big = Image.new('RGBA', im.size, (90, 84, 78, 255)); big.alpha_composite(im); parts.append(big.convert('RGB').resize((im.width * 6, im.height * 6), Image.NEAREST))
        W = sum(p.width for p in parts) + 8 * len(parts); H = max(p.height for p in parts)
        o = Image.new('RGB', (W, H), (30, 30, 30)); x = 0
        for p in parts: o.paste(p, (x, 0)); x += p.width + 8
        o.save(os.path.join(PREV, key + '.png'))
    return im


# =============================================================================================== DUNES: tall pieces (64x112)
DU_PAL = pal_of(L.DU_STONE)
DU_PAL_G = pal_of(L.DU_STONE, L.DU_GOLD)


def stone_tex(c, seed, cell=3.0, k=0.16):
    """multiplicative mottling for weathered stone"""
    return 1 + (c.noise(cell, seed) - 0.5) * 2 * k


def incise(c, m_face, marks, depth=0.55):
    """Carved glyph marks: dark recess + a lit lower-right lip (sun from the upper left)."""
    for (x, y, w, h) in marks:
        r = c.rect(x, y, x + w, y + h)
        c.mulv(r * m_face, depth)
        lip = c.rect(x + 0.0, y + h, x + w + 0.5, y + h + 0.5) * m_face
        c.mulv(lip, 1.25)


def glyph_marks(rng, x0, x1, y0, y1, cell=3.2):
    out = []
    y = y0
    while y < y1 - 1.5:
        kind = rng.random()
        if kind < 0.35:
            out.append((x0 + rng.random() * 0.6, y, (x1 - x0) * rng.uniform(0.5, 0.9), 0.7))
        elif kind < 0.65:
            out.append((x0 + (x1 - x0) * 0.35, y - 0.3, 0.8, 1.8)); out.append((x0 + (x1 - x0) * 0.15, y + 1.0, (x1 - x0) * 0.6, 0.6))
        elif kind < 0.85:
            out.append((x0 + (x1 - x0) * 0.2, y, (x1 - x0) * 0.25, 1.4)); out.append((x0 + (x1 - x0) * 0.6, y + 0.4, (x1 - x0) * 0.22, 1.0))
        else:
            out.append((x0 + (x1 - x0) * 0.3, y, (x1 - x0) * 0.4, 1.6))
        y += cell * rng.uniform(0.8, 1.15)
    return out


def sand_mound(c, cx, w, h, base, seed, cols=None, lean=0.0):
    """A soft drift of sand around a foot."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(cx - w, cx + w, 24)
    top = [base - h * max(0, 1 - ((x - cx - lean) / w) ** 2) ** 0.8 - rng.uniform(0, 0.4) for x in xs]
    m = c.poly([(xs[0], base)] + list(zip(xs, top)) + [(xs[-1], base)])
    v = c.pillow(m, h * 0.9, depth=0.6, amb=0.3, k=0.75) * stone_tex(c, seed, 1.5, 0.05)
    c.shade(m, v * 0.92, cols or L.DU_SAND, mat=3)
    return m


GLYPHS = [["##.", "#..", "##."], ["###", ".#.", ".#."], [".#.", "###", ".#."], ["#.#", "###"], ["###"], ["##", "##"], [".#.", "#.#", ".#."],
          ["#..", "###"], ["###", "#.#"], ["..#", "###", "#.."], ["#", "#", "#"], ["##.", ".##"]]


def carve_glyphs(P, x0, x1, y0, y1, seed, gap=1, deep=-2, lip=1, frame=False):
    """Hieroglyph rows cut into a face (1x): marks step down the ramp, their lower-right lip steps up (sun upper-left)."""
    rng = np.random.default_rng(seed); y = y0
    if frame:
        for yy in range(y0 - 2, y1 + 2):
            P.step(x0 - 2, yy, -1); P.step(x1 + 1, yy, -1)
    while True:
        g = GLYPHS[rng.integers(len(GLYPHS))]; h = len(g); w = len(g[0])
        if y + h > y1: break
        gx = x0 + (x1 - x0 - w) // 2 + (rng.integers(-1, 2) if x1 - x0 - w > 2 else 0)
        cut = set()
        for j, row in enumerate(g):
            for i, ch in enumerate(row):
                if ch == '#': cut.add((gx + i, y + j))
        for (x, yy) in cut: P.step(x, yy, deep)
        for (x, yy) in cut:
            if (x + 1, yy + 1) not in cut and (x, yy + 1) not in cut: P.step(x, yy + 1, lip)
        y += h + gap + (1 if rng.random() < 0.25 else 0)


def tall_obelisk():
    c = Cv(64, 112, S=8)
    cx, foot = 31.5, 111
    S_ = L.DU_STONE
    # plinth (two worn steps): lit tops, shadowed fronts
    def block(x0, x1, y0, y1, seed):
        m = c.poly([(x0, y1), (x0, y0 + 0.8), (x0 + 0.8, y0), (x1 - 0.6, y0), (x1, y0 + 1.0), (x1, y1)])
        v = np.where(c.Y < y0 + 1.2, 0.78, 0.42 - (c.X - x0) / (x1 - x0) * 0.16) * stone_tex(c, seed, 2.0, 0.10)
        c.shade(m, v, S_, mat=1)
    block(cx - 11, cx + 11, 102.5, foot + 1, 4)
    block(cx - 8.5, cx + 8.5, 96.5, 102.5, 5)
    # shaft: a narrow lit left face + the broad front face, tapering
    top, bot = 28.5, 96.6
    def X(y, wb, wt): return wb + (wt - wb) * (bot - y) / (bot - top)
    ys = np.linspace(top, bot, 40)
    fl = [(cx - 3.0 - X(y, 3.0, 2.0) * 0 - 2.2, y) for y in ys]
    fl = [(cx - X(y, 5.0, 3.2), y) for y in ys]
    fr = [(cx + X(y, 6.6, 4.8), y) for y in ys]
    lf = [(cx - X(y, 5.0, 3.2) - X(y, 2.6, 1.8), y) for y in ys]
    front = c.poly(fl + fr[::-1]); left = c.poly(lf + fl[::-1])
    tex = stone_tex(c, 11, 3.5, 0.10) * stone_tex(c, 12, 1.2, 0.05)
    u = np.clip((c.X - (cx - 5)) / 11, 0, 1); t = (c.Y - top) / (bot - top)
    c.shade(front, (0.50 - 0.20 * u - 0.08 * t) * tex, S_, mat=1)
    c.shade(left, (0.80 - 0.10 * t) * tex, S_, mat=1)
    # pyramidion: tarnished electrum, lit face left
    tipy = 19.6
    xl, xm, xr = cx - X(top, 5.0, 3.2) - X(top, 2.6, 1.8), cx - X(top, 5.0, 3.2), cx + X(top, 6.6, 4.8)
    pyl = c.poly([(xl, top + 0.4), (cx - 0.5, tipy), (xm + 0.8, top + 0.4)])
    pyf = c.poly([(xm + 0.8, top + 0.4), (cx - 0.5, tipy), (cx + 0.5, tipy + 0.4), (xr, top + 0.4)])
    c.shade(pyl, 0.78 * np.ones_like(c.X), L.DU_GOLD, mat=2)
    c.shade(pyf, (0.55 - 0.3 * np.clip((c.X - cx) / 5, 0, 1)) * stone_tex(c, 9, 1.5, 0.12), L.DU_GOLD, mat=2)
    c.paint(c.rect(xl, top, xr, top + 1.0), ramp(0.3, S_), mat=1)
    # weathering: the right arris bitten away low down; a long crack
    c.erase(c.poly([(cx + 7.0, 70), (cx + 4.4, 73.5), (cx + 4.8, 78.5), (cx + 7.0, 80)]))
    c.mulv(c.path([(cx + 2.8, 50), (cx + 1.6, 56), (cx + 2.6, 61), (cx + 1.2, 66)], 0.55, 0.35) * front, 0.55)
    sand_mound(c, cx - 1, 16, 3.5, foot + 0.6, 21, lean=-3)

    def fx(q, a):
        P = L.Px(q, a, [S_, L.DU_GOLD])
        carve_glyphs(P, int(cx - 2), int(cx + 2) + 1, 33, 92, 3, frame=False)
        for y in range(31, 95): P.step(int(cx - 4), y, -1) if y % 9 else None     # the column's cut border
        return q, a
    return make('obelisk', c, 'a tall ancient egyptian obelisk with a tarnished gold pyramidion tip and carved hieroglyphs, on a stepped plinth',
                seed=5, denoise=0.42, cn=0.6, mix=0.3, pal=DU_PAL_G + pal_of(L.DU_SAND),
                mat_pals={1: pal_of(S_), 2: pal_of(L.DU_GOLD[:-1]), 3: pal_of(L.DU_SAND[:-1])}, fx=fx,
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#f4df9f', rim_k=0.55)


def fluted(c, cx, r, m, seed, base_v=0.0, flutes=5, dark=0.18):
    """A fluted (papyrus-bundle) column shaft: cylinder light + flute grooves."""
    v = c.cyl(cx, r, amb=0.16, k=0.78)
    u = np.clip((c.X - cx) / r, -1, 1); ang = np.arcsin(u)
    groove = 0.5 + 0.5 * np.cos(ang * flutes * 2)
    v = v * (1 - dark * (1 - groove) * (0.4 + 0.6 * np.cos(ang)))
    return (v + base_v) * stone_tex(c, seed, 2.5, 0.10)


def tall_ruincol(var):
    c = Cv(64, 112, S=8); S_ = L.DU_STONE
    cx, foot, r = 31.5, 111, 6.4
    top = [45.0, 63.0][var]
    rng = np.random.default_rng(40 + var)
    # snapped top (jagged, a lit break surface)
    brk = [(cx - r, top + 2.5), (cx - r + 2, top - 1.5), (cx - 1.5, top + 1.0), (cx + 0.5, top - 3.5), (cx + 3, top - 0.5), (cx + r, top - 2.0)]
    shaft = c.poly([(cx - r, 104)] + brk + [(cx + r, 104)])
    c.shade(shaft, fluted(c, cx, r, shaft, 41 + var) * (0.95 - 0.12 * (c.Y - top) / (104 - top)), S_, mat=1)
    # break surface (seen a little from above): a lit sliver
    bs = c.poly(brk + [(cx + r, top + 0.3), (cx - r, top + 3.6)])
    c.shade(bs, 0.82 * stone_tex(c, 3, 1.0, 0.1), S_, mat=1)
    # drum joints
    for y in np.arange(top + 9 - (top % 9), 104, 11.5):
        c.mulv(c.rect(cx - r, y, cx + r, y + 0.7) * shaft, 0.62)
    # flaking paint bands: faded lapis + ochre (a memory of colour)
    for y in (top + 7, 92):
        if y < 102:
            band = c.rect(cx - r, y, cx + r, y + 2.2) * shaft * (c.noise(1.6, 50 + int(y)) > 0.42)
            c.tint(band, L.DU_LAPIS[2], 0.55)
    # capital-less base: torus + square plinth
    tor = c.ell(cx, 104.5, r + 1.6, 1.8)
    c.shade(tor, c.cyl(104.0, 1.8, axis='h', amb=0.2, k=0.8) * 0.95, S_, mat=1)
    pl = c.poly([(cx - 10, foot + 1), (cx - 10, 106.4), (cx - 9.2, 105.8), (cx + 9.2, 105.8), (cx + 10, 106.6), (cx + 10, foot + 1)])
    c.shade(pl, np.where(c.Y < 106.8, 0.76, 0.42 - (c.X - cx + 10) / 20 * 0.15) * stone_tex(c, 6, 2, 0.1), S_, mat=1)
    if var == 0:   # a fallen drum lying at its foot, end-on to us (an ellipse face) and long side
        dr = c.poly([(cx + 9, foot + 1), (cx + 9.5, 103.5), (cx + 26, 101.5), (cx + 27, foot + 1)])
        c.shade(dr, c.cyl(106.5, 5.0, axis='h', amb=0.18, k=0.8) * stone_tex(c, 7, 2, 0.12), S_, mat=1)
        end = c.ell(cx + 26.5, 106.4, 2.6, 5.0)
        c.shade(end, 0.62 * stone_tex(c, 8, 1, 0.15), S_, mat=1)
        for k in range(3): c.mulv(c.rect(cx + 12 + k * 4.5, 102.5, cx + 12.6 + k * 4.5, foot) * dr, 0.75)
    sand_mound(c, cx + (3 if var == 0 else -1), 17 if var == 0 else 13, 3.2, foot + 0.6, 30 + var, lean=-2)

    return make(f'ruincol{var}', c, 'a broken ancient egyptian papyrus column, fluted sandstone shaft snapped off, faded painted bands, half buried in sand',
                seed=7 + var, denoise=0.42, cn=0.6, mix=0.3, pal=DU_PAL + pal_of(L.DU_SAND, L.DU_LAPIS),
                mat_pals={1: pal_of(S_, L.DU_LAPIS[1:3]), 3: pal_of(L.DU_SAND[:-1])},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#f4df9f', rim_k=0.55)


# =============================================================================================== DUNES: 48x64 props
def du_statue():
    """The jackal: a seated basalt Anubis on a carved plinth, gold-inlaid collar, a coal of an eye (light at x+4, y-40)."""
    c = Cv(48, 64, S=16)
    B = ['#0d0806', '#140c08', '#1d120c', '#2a1a10', '#3a2618', '#4e3420', '#6c4b2b', '#a17440', '#e3c68f']   # basalt, warm black
    foot = 64
    # plinth with a cavetto cornice
    pl = c.poly([(11.5, foot), (11.5, 52), (36.5, 52), (36.5, foot)])
    c.shade(pl, (0.42 - (c.X - 11.5) / 25 * 0.18) * stone_tex(c, 2, 2.0, 0.1), L.DU_STONE, mat=1)
    cor = c.poly([(10.5, 52.6), (10.8, 50.0), (37.2, 50.0), (37.5, 52.6)])
    c.shade(cor, np.where(c.Y < 50.8, 0.8, 0.55) * stone_tex(c, 3, 1.5, 0.08), L.DU_STONE, mat=1)
    # the jackal, seated, facing right
    haunch = c.ell(19.0, 43.5, 6.6, 6.8)
    body = c.poly([(13.5, 49.6), (14.0, 41), (16.5, 35), (20.5, 30.5), (24.5, 28.0), (28.0, 29.0), (30.0, 33), (30.4, 40), (29.6, 49.6)])
    legs = c.poly([(25.8, 38), (30.6, 37.5), (31.0, 49.6), (25.4, 49.6)])
    paw = c.ell(30.6, 48.8, 2.4, 1.2)
    neck = c.poly([(20.5, 31.0), (22.2, 24.0), (26.4, 22.2), (29.6, 25.5), (28.8, 30.5)])
    head = c.ell(25.6, 23.2, 4.1, 3.4)
    snout = c.poly([(26.5, 20.6), (35.4, 23.2), (35.8, 24.6), (34.6, 25.6), (27.0, 26.6)])
    jaw = c.poly([(27, 25.6), (33.5, 25.4), (32.4, 26.6), (27.4, 27.2)])
    earF = c.poly([(23.2, 21.0), (24.0, 9.4), (27.6, 20.2)])
    earB = c.poly([(21.0, 21.6), (20.4, 11.2), (23.4, 20.6)])
    tail = c.path([(14.0, 48.6), (11.6, 49.2), (10.4, 47.8)], 1.6, 0.9)
    whole = np.clip(haunch + body + legs + paw + neck + head + snout + jaw + earF + earB + tail, 0, 1)
    # volume: a soft dome over the whole silhouette + per-part domes for the haunch / head
    v = c.pillow(whole, 4.0, depth=0.9, amb=0.12, k=0.95) * 0.85
    v = np.maximum(v, c.pillow(haunch, 4.5, depth=1.0, amb=0.1, k=0.95) * haunch * 0.92)
    v = np.where(head + snout > 0.5, np.maximum(v * 0.9, c.pillow(np.clip(head + snout, 0, 1), 2.6, amb=0.12, k=0.95) * 0.95), v)
    v = np.where(earB > 0.5, v * 0.6, v)
    c.shade(whole, v * stone_tex(c, 9, 1.2, 0.06), B, mat=4)
    c.mulv(c.path([(25.4, 39.0), (25.6, 49.4)], 0.6) , 0.55)        # the gap between the legs and the chest
    c.mulv(c.path([(14.6, 45.0), (19.0, 49.4)], 0.5), 0.6)          # haunch over the hind paw
    # gold inlay: the wesekh collar, the ear lining, the plinth band
    col = c.poly([(21.2, 30.6), (28.9, 29.6), (29.6, 32.0), (21.0, 33.6)]) * whole
    c.shade(col, c.cyl(31.0, 2.0, axis='h', amb=0.25, k=0.8) * 0.85, L.DU_GOLD, mat=2)
    for k in range(2):
        c.mulv(c.path([(21.4, 31.6 + k * 1.1), (29.2, 30.6 + k * 1.1)], 0.35) * col, 0.65)
    lining = c.poly([(24.4, 19.6), (24.6, 12.0), (26.6, 19.4)])
    c.shade(lining, 0.55 * np.ones_like(c.X), L.DU_GOLD, mat=2)
    band = c.rect(12.5, 55.0, 35.5, 57.0)
    c.shade(band, 0.42 + 0.0 * c.X, L.DU_GOLD, mat=2)

    def fx(q, a):
        P = L.Px(q, a, [B, L.DU_GOLD, L.DU_STONE])
        P.set(28, 24, 1, 4); P.set(29, 24, 1, 3)          # the eye: a coal of amber (SB_LIGHT x+4, y-40)
        for x in range(14, 35, 4): P.step(x, 56, -2)      # cartouche ticks in the band
        return q, a
    return make('statue_du', c, 'a seated black basalt statue of the jackal god anubis on a carved stone plinth, gold inlaid collar, egyptian tomb guardian',
                seed=12, denoise=0.38, cn=0.65, mix=0.25, pal=pal_of(B, L.DU_GOLD, L.DU_STONE),
                mat_pals={4: pal_of(B), 2: pal_of(L.DU_GOLD[:-1]), 1: pal_of(L.DU_STONE)}, fx=fx,
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#e3c68f', rim_k=0.55)


# =============================================================================================== DUNES: xsb_big (192x128, painted into the back layer, bottom-centre)
def dune_front(c, pts, seed, v0=0.7):
    """A dune bank along the frame bottom: lit crest, wind ripples, darker lee."""
    m = c.poly([(0, 128)] + pts + [(192, 128)])
    crest = np.interp(c.X, [p[0] for p in pts], [p[1] for p in pts])
    d = np.clip((c.Y - crest) / 10, 0, 1)
    rip = 0.04 * np.sin((c.X * 0.9 + c.Y * 3.2 + 6 * c.noise(6, seed)) * 1.3)
    v = (v0 - 0.32 * d + rip) * stone_tex(c, seed + 1, 3, 0.05)
    c.shade(m, v, L.DU_SAND, mat=3)
    return m


def big_sunspire():
    """A buried pyramid seen corner-on: sunlit west face, umber east face, stripped casing showing the courses, a tarnished
    electrum capstone, and at its foot a small pylon shrine with the winged sun."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE
    ax, ay = 96.0, 21.0                       # apex
    bl, br, by = 6.0, 186.0, 124.0            # base corners
    mx = 104.0                                # the near corner's ridge meets the ground here (corner view, ridge a bit right)
    west = c.poly([(ax, ay), (mx, by), (bl, by)])
    east = c.poly([(ax, ay), (br, by), (mx, by)])
    t = (c.Y - ay) / (by - ay)
    tex = stone_tex(c, 61, 4.0, 0.08) * stone_tex(c, 62, 1.4, 0.05)
    c.shade(west, (0.74 - 0.12 * t) * tex, S_, mat=1)
    c.shade(east, (0.36 - 0.08 * t) * tex, S_, mat=1)
    # courses: every ~4.5 px a step; the lip catches light on the west face, a dark under-shadow on both
    ystep = 4.6
    lower = (c.Y > 52)
    for k in range(int((by - 52) / ystep) + 1):
        y = 52 + k * ystep
        line = c.rect(0, y, 192, y + 0.75) * lower
        c.mulv(line * west, 0.72); c.mulv(line * east, 0.7)
        lip = c.rect(0, y - 0.8, 192, y) * lower
        c.mulv(lip * west, 1.12)
        # vertical block joints, staggered
        rng = np.random.default_rng(100 + k)
        for xj in np.arange(rng.uniform(0, 9), 192, rng.uniform(7, 11)):
            j = c.rect(xj, y + 0.7, xj + 0.5, y + ystep) * lower
            c.mulv(j * (west + east), 0.85)
    # the casing still on the upper third: smooth, paler, with a ragged lower edge
    rag = 52 + 5 * c.noise(5, 63) - 2.5
    casing = (c.Y < rag) * (c.Y > ay + 9)
    c.shade(casing * west, (0.86 - 0.1 * t) * stone_tex(c, 64, 3, 0.05), S_, mat=1)
    c.shade(casing * east, (0.44 - 0.06 * t) * stone_tex(c, 65, 3, 0.05), S_, mat=1)
    c.mulv(np.clip(c.rect(0, 0, 192, 128) * (np.abs(c.Y - rag) < 0.7), 0, 1) * (west + east), 0.7)
    # capstone (pyramidion), tarnished electrum
    cy = ay + 10
    capw = c.poly([(ax, ay), (ax + (mx - ax) * 10 / (by - ay), cy), (ax + (bl - ax) * 10 / (by - ay), cy)])
    cape = c.poly([(ax, ay), (ax + (br - ax) * 10 / (by - ay), cy), (ax + (mx - ax) * 10 / (by - ay), cy)])
    c.shade(capw, 0.8 - 0.15 * (c.Y - ay) / 10, L.DU_GOLD, mat=2)
    c.shade(cape, 0.4 - 0.1 * (c.Y - ay) / 10 + 0 * c.X, L.DU_GOLD, mat=2)
    # erosion: bites out of the silhouette edges, a slumped scar on the west face
    for (x, y, rx, ry) in [(30, 96, 5, 3), (48, 76, 3.5, 2.4), (158, 92, 5, 3.2), (138, 72, 3.2, 2.2)]:
        c.erase(c.ell(x, y, rx, ry) * (np.abs(c.X - x) < rx))
    scar = c.poly([(60, 64), (74, 60), (80, 82), (70, 92), (58, 86)]) * west
    c.mulv(scar, 0.86)
    # the shrine at the foot: a small pylon gate with a winged sun disc, its door black
    gx, gy = 72.0, 125.0
    pyl = c.poly([(gx - 26, gy), (gx - 23, 88), (gx + 23, 88), (gx + 26, gy)])
    c.shade(pyl, (0.66 - 0.28 * np.clip((c.X - gx + 26) / 52, 0, 1)) * stone_tex(c, 66, 2.5, 0.1), S_, mat=1)
    cav = c.poly([(gx - 26, 88.5), (gx - 27.5, 84.2), (gx + 27.5, 84.2), (gx + 26, 88.5)])
    c.shade(cav, np.where(c.Y < 85.4, 0.9, 0.5) * stone_tex(c, 67, 2, 0.08), S_, mat=1)
    door = c.poly([(gx - 6.5, gy), (gx - 6.0, 101), (gx + 6.0, 101), (gx + 6.5, gy)])
    c.shade(door, 0.04 + 0.05 * (c.Y - 101) / 24, S_, mat=1)
    c.mulv(c.rect(gx - 7.5, 100, gx + 7.5, 101.2) * pyl, 0.6)
    # winged disc on the cornice
    disc = c.ell(gx, 93.6, 3.2, 3.2)
    c.shade(disc, c.pillow(disc, 2.0, amb=0.3, k=0.8), L.DU_GOLD, mat=2)
    for sgn in (-1, 1):
        wing = c.poly([(gx + sgn * 3.0, 92.0), (gx + sgn * 19, 90.6), (gx + sgn * 20.5, 92.4), (gx + sgn * 16, 95.6), (gx + sgn * 3.0, 95.8)])
        feathers = 0.5 + 0.5 * np.sin((c.X - gx) * 2.6)
        c.shade(wing, (0.38 + 0.12 * feathers) * (1.0 if sgn < 0 else 0.8), L.DU_LAPIS, mat=5)
        c.shade(wing * (c.Y < 92.6), 0.45 + 0 * c.X, L.DU_GOLD, mat=2)
    # dunes: a big drift banked against the east and the shrine, a lower one west
    dune_front(c, [(0, 113), (20, 110), (40, 114), (52, 121), (96, 120), (120, 112), (150, 104), (176, 106), (192, 110)], 70)
    return make('sunspire', c, 'a colossal ancient egyptian pyramid seen from a corner, sunlit face and shadowed face, stepped courses, eroded casing stones, '
                'a tarnished golden capstone, a small temple gate with a winged sun disc at its foot, half buried in desert dunes',
                seed=21, denoise=0.48, cn=0.6, mix=0.45, pix=0.55, pal=pal_of(S_, L.DU_GOLD, L.DU_SAND, L.DU_LAPIS),
                mat_pals={1: pal_of(S_), 2: pal_of(L.DU_GOLD[:-1]), 3: pal_of(L.DU_SAND), 5: pal_of(L.DU_LAPIS)},
                out_dark='#0d0806', out_lit='#2a1a10', inner=True, rim_col='#f4df9f', rim_k=0.5)


def big_ruinarch():
    """The tomb mouth: a battered gateway of two sloped jambs under a cavetto lintel with the winged sun disc, sunk in sand."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE
    cx = 96.0; top = 30.0; foot = 127.0
    tex = stone_tex(c, 81, 3.5, 0.09) * stone_tex(c, 82, 1.2, 0.05)
    for sgn in (-1, 1):
        x_in, x_out_t, x_out_b = cx + sgn * 17, cx + sgn * 40, cx + sgn * 47        # inner face vertical, outer face battered
        pts = [(x_in, foot), (x_in, top + 14), (x_out_t, top + 14), (x_out_b, foot)]
        jamb = c.poly(pts)
        if sgn < 0:   # west jamb: its outer (west) face catches the sun -> show a sliver of it
            v = 0.66 - 0.18 * np.clip((c.X - (cx - 47)) / 30, 0, 1)
        else:
            v = 0.5 - 0.2 * np.clip((c.X - (cx + 17)) / 30, 0, 1)
        c.shade(jamb, (v - 0.08 * (c.Y - top) / (foot - top)) * tex, S_, mat=1)
        # torus moulding down the outer corner
        tor = c.path([(x_out_t + sgn * -1.2, top + 14), (x_out_b + sgn * -1.2, foot)], 1.8)
        c.mulv(tor * jamb, 1.18 if sgn < 0 else 0.8)
        # block courses
        for y in np.arange(top + 22, foot, 9.5):
            c.mulv(c.rect(0, y, 192, y + 0.7) * jamb, 0.72)
            rng = np.random.default_rng(int(y) + (5 if sgn > 0 else 0))
            xj = cx + sgn * rng.uniform(24, 34)
            c.mulv(c.rect(xj, y + 0.7, xj + 0.6, y + 9.5) * jamb, 0.78)
        # reliefs: a standing figure carved on each jamb face (a sunk relief: dark cut, lit lower-right lip)
        fx_ = cx + sgn * 29
        fig = np.clip(c.ell(fx_, top + 31, 2.2, 2.6) + c.poly([(fx_ - 2.6, top + 34), (fx_ + 2.6, top + 34), (fx_ + 3.4, top + 50), (fx_ + 1.4, top + 64), (fx_ - 1.6, top + 64), (fx_ - 3.4, top + 50)]), 0, 1)
        c.mulv(fig * jamb, 0.78)
        edge_lit = np.clip(fig - c.blur(fig, 0.5) * 0 , 0, 1)
        c.mulv(np.clip(c.blur(fig, 0.6) - fig, 0, 1) * jamb * (c.X > fx_), 1.6)
    # the doorway: black, with a little reveal shadow
    door = c.rect(cx - 17, top + 14, cx + 17, foot)
    c.shade(door, 0.03 + 0.04 * np.clip((c.Y - top - 14) / 80, 0, 1) + 0 * c.X, S_, mat=1)
    # lintel + cavetto cornice spanning both jambs
    lin = c.rect(cx - 41, top + 6, cx + 41, top + 15)
    c.shade(lin, (0.56 - 0.2 * np.clip((c.X - cx + 41) / 82, 0, 1)) * tex, S_, mat=1)
    cav = c.poly([(cx - 41, top + 6.2), (cx - 45, top + 0.6), (cx - 44.5, top - 1.2), (cx + 44.5, top - 1.2), (cx + 45, top + 0.6), (cx + 41, top + 6.2)])
    cv_v = np.where(c.Y < top + 0.2, 0.92, 0.42 + 0.3 * np.clip((c.Y - top) / 6, 0, 1))
    c.shade(cav, cv_v * tex, S_, mat=1)
    torl = c.rect(cx - 41.5, top + 5.6, cx + 41.5, top + 7.2)
    c.shade(torl, 0.72 + 0 * c.X, S_, mat=1)
    # winged sun disc relief on the lintel
    disc = c.ell(cx, top + 10.4, 3.4, 3.4)
    c.shade(disc, c.pillow(disc, 2.2, amb=0.3, k=0.85), L.DU_GOLD, mat=2)
    for sgn in (-1, 1):
        c.shade(c.poly([(cx + sgn * 3.0, top + 9.4), (cx + sgn * 6.2, top + 7.6), (cx + sgn * 6.6, top + 9.6)]), 0.5 + 0 * c.X, L.DU_GOLD, mat=2)   # uraei
        wing = c.poly([(cx + sgn * 4.2, top + 8.8), (cx + sgn * 34, top + 8.0), (cx + sgn * 36, top + 9.6), (cx + sgn * 30, top + 12.6), (cx + sgn * 4.2, top + 13.2)])
        fe = 0.5 + 0.5 * np.sin((c.X - cx) * 2.2)
        c.shade(wing, (0.42 + 0.14 * fe) * (1.0 if sgn < 0 else 0.82) * (0.9 + 0.1 * np.clip((top + 13 - c.Y) / 4, 0, 1)), L.DU_LAPIS, mat=5)
        c.shade(wing * (c.Y < top + 9.6), 0.5 + 0 * c.X, L.DU_GOLD, mat=2)
        c.tint(wing * (c.noise(1.4, 90 + sgn) > 0.62), hx(L.DU_STONE[5]), 0.8)   # flaked to bare stone
    # damage: the east end of the cornice broken away, a crack through the lintel
    c.erase(c.poly([(cx + 46, top - 2), (cx + 33, top - 2), (cx + 36, top + 2.5), (cx + 41.5, top + 4.4), (cx + 46, top + 3)]))
    c.mulv(c.path([(cx + 11, top + 6), (cx + 13, top + 10), (cx + 12, top + 15)], 0.6) * lin, 0.5)
    # sand: a drift through the doorway and banked against both jambs
    dune_front(c, [(0, 112), (22, 106), (40, 110), (56, 117), (80, 118), (100, 114), (130, 111), (152, 114), (170, 109), (192, 112)], 88)
    return make('ruinarch', c, 'an ancient egyptian temple gateway, two massive battered stone jambs with carved reliefs and a dark doorway, a cavetto cornice lintel '
                'with a winged sun disc in faded lapis and tarnished gold, eroded, half buried in desert sand',
                seed=31, denoise=0.48, cn=0.6, mix=0.45, pix=0.55, pal=pal_of(S_, L.DU_GOLD, L.DU_SAND, L.DU_LAPIS),
                mat_pals={1: pal_of(S_), 2: pal_of(L.DU_GOLD[:-1]), 3: pal_of(L.DU_SAND), 5: pal_of(L.DU_LAPIS, ['#6c4b2b'])},
                out_dark='#0d0806', out_lit='#2a1a10', inner=True, rim_col='#f4df9f', rim_k=0.5)


# =============================================================================================== DUNES: the colossus (DU3)
def colossus():
    """A sun-king's head the size of a house, toppled and half sunk in the dune: nemes headcloth with worn stripes, serene
    heavy-lidded eyes, the nose broken away, a crack through the brow, the uraeus snapped off. Sculpted as a height field."""
    c = Cv(176, 128, S=6); S_ = L.DU_STONE
    cx = 88.0
    X, Y = c.X, c.Y
    # global head volume: everything sits on one big ellipsoid, so the far (east) side turns into shadow
    G = 58 * np.sqrt(np.clip(1 - ((X - cx + 8) / 62) ** 2 - ((Y - 62) / 78) ** 2, 0, 1))
    # ---- the nemes (headcloth): crown dome, flaring wings, lappets
    crown = [(cx + 50 * math.cos(a), 46 - 40 * math.sin(a)) for a in np.linspace(0, math.pi, 40)]
    nemes = c.poly([(cx + 58, 74), (cx + 56, 58)] + crown[1:-1] + [(cx - 56, 58), (cx - 58, 74), (cx - 30, 70), (cx + 30, 70)])
    lapL = c.poly([(cx - 33, 62), (cx - 50, 68), (cx - 50, 128), (cx - 30, 128), (cx - 28, 88)])
    lapR = c.poly([(cx + 33, 62), (cx + 50, 68), (cx + 50, 128), (cx + 30, 128), (cx + 28, 88)])
    backc = c.poly([(cx - 46, 60), (cx + 46, 60), (cx + 40, 96), (cx - 40, 96)])       # the cloth behind the jaw
    cloth = np.clip(nemes + lapL + lapR + backc, 0, 1)
    # stripes: broad bands following the crown's curve on the dome, horizontal on the lappets
    rr = np.sqrt(((X - cx) / 50) ** 2 + ((Y - 46) / 40) ** 2)
    yb = Y + 0.0065 * (X - cx) ** 2 * (Y < 66)                                       # bands bow over the dome
    ph = ((yb - 6) / 7.6) % 1.0
    st = np.clip(1 - np.abs(ph - 0.5) / 0.2, 0, 1) ** 0.7                            # narrow grooves between broad bands
    hN = G + 6 * c.blur(cloth, 4) - 2.2 * st
    # lappets lean forward at their tops (a fold where they turn over the shoulders)
    hN += np.where((lapL + lapR) > 0.5, -6 * np.clip((Y - 70) / 50, 0, 1), 0)
    hN = np.where((backc > 0.5) & (nemes < 0.5) & (lapL + lapR < 0.5), G - 8, hN)
    # ---- the neck and the top of the chest (in the chin's shadow)
    neck = c.poly([(cx - 26, 84), (cx + 26, 84), (cx + 29, 128), (cx - 29, 128)])
    hK = G - 10 + 4 * np.sqrt(np.clip(1 - ((X - cx) / 27) ** 2, 0, 1))
    # ---- the face: broad, strong-jawed, framed by the cloth
    fo = []
    for a in np.linspace(0, 2 * math.pi, 72):
        sa, ca = math.sin(a), math.cos(a)
        w = 29 * (1 - 0.30 * max(0, -ca) ** 1.6)            # jaw tapers toward the chin
        h = 30 if ca > 0 else 38                              # forehead (up) / chin (down)
        fo.append((cx + w * sa, 66 - h * ca))
    face = c.poly(fo)
    u = (X - cx) / 29.0; v = (Y - 66) / np.where(Y < 66, 30, 38)
    hF = G + 7 + 9 * np.sqrt(np.clip(1 - u ** 2 * 0.8 - v ** 2 * 0.7, 0, 1))
    for sg in (-1, 1):
        hF += 3.0 * c.g2(cx + sg * 13, 47.5, 10, 2.8)                     # brow
        hF -= 4.6 * c.g2(cx + sg * 12.5, 54.0, 7.4, 4.4)                  # socket
        hF += 3.0 * c.g2(cx + sg * 12.5, 55.0, 5.6, 2.1)                  # heavy lid / eyeball
        hF -= 1.6 * c.g2(cx + sg * 12.5, 53.4, 6.0, 0.5)                  # upper lid line
        hF -= 1.2 * c.g2(cx + sg * 20.5, 53.8, 3.4, 0.45, rot=-sg * 0.22) # cosmetic line drawn out to the temple
        hF += 3.2 * c.g2(cx + sg * 17, 69, 8.0, 8.0)                      # cheekbone
        hF += 1.2 * c.g2(cx + sg * 4.6, 72.5, 2.4, 2.0)                   # nostril wings (what is left of them)
        hF -= 1.6 * c.g2(cx + sg * 9.0, 78.5, 2.4, 3.0)                   # nasolabial
    nose = 7.5 * c.g2(cx, 60, 3.4, 10.5) * (Y < 69.0 + 1.6 * c.noise(0.7, 5))
    hF += nose
    hF += 2.0 * c.g2(cx, 70.0, 4.4, 2.4) + (c.noise(1.2, 7) - 0.5) * 1.2 * c.g2(cx, 70, 4.0, 2.2)   # the broken stump
    hF += 2.4 * c.g2(cx, 79.2, 8.5, 2.0) + 2.8 * c.g2(cx, 84.0, 7.0, 2.2)                         # lips
    hF -= 2.0 * c.g2(cx, 81.6, 9.0, 0.55)                                                         # mouth line
    hF -= 2.2 * c.g2(cx, 89.0, 7.0, 1.4)                                                          # under the lip
    hF += 3.0 * c.g2(cx, 96, 9, 5)                                                                # chin
    ears = np.clip(c.ell(cx - 31.5, 61, 3.8, 7.5) + c.ell(cx + 31.5, 61, 3.8, 7.5), 0, 1)
    hE = G + 3 + 3 * c.blur(ears, 2)
    band = c.poly([(cx - 31, 43.8), (cx - 18, 39.6), (cx, 38.2), (cx + 18, 39.6), (cx + 31, 43.8), (cx + 31, 47.6), (cx + 18, 44.0), (cx, 42.8), (cx - 18, 44.0), (cx - 31, 47.6)])
    urae = c.poly([(cx - 3.2, 43), (cx - 2.6, 35.0), (cx + 0.2, 33.0), (cx + 2.4, 34.6), (cx + 3.2, 43)])
    beard = c.poly([(cx - 6.5, 102), (cx + 6.5, 102), (cx + 5.6, 111), (cx + 2, 109.4), (cx - 1.4, 111.6), (cx - 5.8, 110)])
    H = np.where(neck > 0.5, hK, -50)
    H = np.where(cloth > 0.5, hN, H)
    H = np.where(ears > 0.5, hE, H)
    H = np.where(face > 0.5, hF, H)
    H = np.where(band > 0.5, G + 19 + 1.5 * c.blur(band, 1.2), H)
    H = np.where(urae > 0.5, G + 22 + 2 * c.blur(urae, 1.5), H)
    H = np.where(beard > 0.5, G + 6 + 2 * c.blur(beard, 2) - 0.8 * (np.sin((Y - 102) * 1.6) ** 2), H)
    crack = c.path([(cx + 9, 14), (cx + 6, 28), (cx + 10, 40), (cx + 6, 49), (cx + 9, 58), (cx + 17, 68), (cx + 19, 79)], 1.0, 0.5)
    H = H - 3.0 * c.blur(crack, 0.4)
    whole = np.clip(cloth + face + ears + band + urae + beard + neck, 0, 1)
    Hs = np.where(whole > 0.5, H, np.nan)
    Hf = np.where(np.isnan(Hs), np.nanmin(Hs), Hs)
    val = c.relief(Hf, k_h=1.25, amb=0.08, k=1.0)
    # cast shadow: chin over the neck, cloth over the ears' back; occlusion in the deep folds
    occl = np.clip((c.blur(np.clip(Hf, 0, 80) / 80, 3) - np.clip(Hf, 0, 80) / 80) * 6, 0, 0.6)
    val = val * (1 - occl)
    val = np.where((neck + backc * (nemes < 0.5)) * (face < 0.5) * (lapL + lapR < 0.5) > 0.5, val * (0.55 + 0.25 * np.clip((Y - 100) / 28, 0, 1)), val)
    val = val * (0.9 + 0.14 * c.noise(6, 13)) * (0.93 + 0.1 * c.noise(1.6, 16)) * 0.9
    val = val * (1 - 0.18 * np.clip(np.sin(X * 1.7 + 4 * c.noise(3, 17)) * 0.5 + 0.5 - 0.6, 0, 1) * (c.noise(8, 18) > 0.5))   # wind streaks
    c.shade(whole, val, S_, mat=1)
    c.tint(cloth * st * (c.noise(2.5, 14) > 0.52) * (face < 0.5), hx(L.DU_LAPIS[2]), 0.45)     # flecks of the old paint
    c.tint(band * (c.noise(1.5, 15) > 0.45), hx(L.DU_GOLD[3]), 0.4)
    c.erase(c.poly([(cx + 40, 14), (cx + 25, 10), (cx + 29, 18), (cx + 35, 25), (cx + 46, 27)]) * nemes)
    c.rotate(-5.0, cx, 120)
    drift = c.poly([(cx - 56, 40), (cx - 46, 24), (cx - 30, 14), (cx - 16, 12.5), (cx - 22, 18), (cx - 36, 28), (cx - 44, 42), (cx - 52, 50)])
    c.shade(drift * (c.cov > 0.5), 0.72 + 0.12 * c.noise(2, 19), L.DU_SAND, mat=3)          # sand lying on the crown
    dune_front_w(c, 176, [(0, 102), (14, 97), (34, 99), (52, 107), (70, 113), (100, 115), (122, 110), (144, 103), (164, 106), (176, 109)], 140)
    return make('colossus', c, 'a colossal weathered stone head of an ancient egyptian pharaoh, nemes headdress with worn stripes, serene heavy lidded carved eyes, '
                'nose broken off, cracked sandstone, toppled and half buried in a desert dune, monumental, mythic, majestic',
                seed=44, denoise=0.45, cn=0.65, cn_end=0.75, mix=0.4, pix=0.5, pal=pal_of(S_, L.DU_SAND, L.DU_LAPIS[1:3], L.DU_GOLD[1:4]),
                mat_pals={1: pal_of(S_, L.DU_LAPIS[1:3], L.DU_GOLD[2:4]), 3: pal_of(L.DU_SAND)},
                out_dark='#0d0806', out_lit='#2a1a10', inner=True, rim_col='#f4df9f', rim_k=0.5,
                neg='goggles, glasses, round eyes, open eyes with pupils, sunglasses, acne, pockmarks')


def dune_front_w(c, w, pts, seed, v0=0.7):
    m = c.poly([(0, c.fh)] + pts + [(w, c.fh)])
    crest = np.interp(c.X, [p[0] for p in pts], [p[1] for p in pts])
    d = np.clip((c.Y - crest) / 10, 0, 1)
    rip = 0.04 * np.sin((c.X * 0.9 + c.Y * 3.2 + 6 * c.noise(6, seed)) * 1.3)
    c.shade(m, (v0 - 0.32 * d + rip) * stone_tex(c, seed + 1, 3, 0.05), L.DU_SAND, mat=3)
    return m


LAST_MATS = None


def fire_layer(fw, fh, cx, yb, w, h, f, n=4, cols=None, seed=0, tongues=3):
    """A fire (frame f of n) as an RGBA layer: tongues licking up from (cx, yb), palette-locked to the fire ramp."""
    cols = cols or L.DU_FIRE
    c = Cv(fw, fh, S=8)
    ph = 2 * math.pi * f / n
    rng = np.random.default_rng(seed)
    acc = np.zeros((c.H, c.W))
    for i in range(tongues):
        ox = (i - (tongues - 1) / 2) * w / tongues * 1.1 + rng.uniform(-0.6, 0.6)
        hh = h * (0.7 + 0.3 * math.sin(ph * (1 + i % 2) + i * 2.1)) * (1.0 if i == tongues // 2 else 0.8)
        sway = 0.9 * math.sin(ph + i * 1.7)
        tip = (cx + ox + sway, yb - hh)
        pts = [(cx + ox - w / tongues * 0.75, yb), (cx + ox - w / tongues * 0.35 + sway * 0.4, yb - hh * 0.5), tip,
               (cx + ox + w / tongues * 0.35 + sway * 0.4, yb - hh * 0.45), (cx + ox + w / tongues * 0.75, yb)]
        acc = np.maximum(acc, c.poly(pts, blur=0.25))
    core = np.clip(1 - np.sqrt(((c.X - cx) / (w * 0.45)) ** 2 + ((c.Y - yb + h * 0.18) / (h * 0.45)) ** 2), 0, 1)
    v = np.clip(0.25 + 0.55 * core * 1.6 + 0.25 * (c.Y - (yb - h)) / h, 0, 1)
    c.shade(acc, v, cols, mat=9)
    rgb, al, _ = L.down(c, thresh=0.42)
    q = L.lock(rgb, al, pal_of(cols))
    return L.to_img(q, al)


JAR_FORMS = {
    'store': [(0, 0.42), (0.04, 0.5), (0.2, 0.84), (0.45, 1.0), (0.62, 0.96), (0.74, 0.72), (0.8, 0.44), (0.9, 0.38), (0.94, 0.48), (1.0, 0.5)],
    'amph': [(0, 0.16), (0.08, 0.3), (0.3, 0.78), (0.55, 1.0), (0.7, 0.9), (0.78, 0.5), (0.84, 0.3), (0.94, 0.3), (0.96, 0.4), (1.0, 0.4)],
    'oil': [(0, 0.5), (0.05, 0.62), (0.3, 1.0), (0.55, 0.92), (0.68, 0.5), (0.86, 0.36), (0.9, 0.52), (1.0, 0.5)],
}


def jar_profile(base, hh, rw, form='store'):
    P = JAR_FORMS[form]; ts = [p[0] for p in P]; rs = [p[1] for p in P]
    return base - hh, (lambda y: rw * float(np.interp((base - y) / hh, ts, rs)))


def clay_jar(c, cx, base, rw, hh, seed, band=True, broken=False, form='store'):
    top, r = jar_profile(base, hh, rw, form)
    m, v = c.revolve(cx, top, base, r, amb=0.14, k=0.9)
    tex = stone_tex(c, seed, 1.8, 0.07)
    c.shade(m, v * 0.92 * tex, L.DU_CLAY, mat=6)
    if form == 'amph':     # two loop handles from the neck to the shoulder
        for sg in (-1, 1):
            hnd = c.path([(cx + sg * r(top + hh * 0.1) * 0.9, top + hh * 0.12), (cx + sg * rw * 0.78, top + hh * 0.1), (cx + sg * rw * 0.82, top + hh * 0.28)], 0.9)
            c.shade(hnd, (0.55 if sg < 0 else 0.3) + 0 * c.X, L.DU_CLAY, mat=6)
    if band:   # a painted band (faded black-umber) with a zigzag
        yb = base - hh * 0.55
        bm = m * (np.abs(c.Y - yb) < 1.0)
        c.mulv(bm, 0.55)
        zz = m * (np.abs(c.Y - (yb - 2.4 + 0.9 * np.abs(((c.X - cx) / 1.4) % 2 - 1))) < 0.35)
        c.mulv(zz, 0.6)
    # rim mouth: a dark ellipse seen from slightly above
    c.shade(c.ell(cx, top + 0.6, r(top + 0.2) * 0.8, 0.7), 0.05 + 0 * c.X, L.DU_CLAY, mat=6)
    if broken:
        c.erase(c.poly([(cx + rw * 0.2, top - 1), (cx + rw * 1.2, top - 1), (cx + rw * 1.2, top + hh * 0.45), (cx + rw * 0.55, top + hh * 0.32), (cx + rw * 0.7, top + hh * 0.18), (cx + rw * 0.25, top + hh * 0.1)]))
    return m


def du_jars(var):
    c = Cv(48, 64, S=16)
    if var == 0:
        clay_jar(c, 17.0, 63.6, 8.6, 23, 1)                                 # the big storage jar
        clay_jar(c, 31.5, 63.6, 6.0, 17, 2, band=False, form='amph')        # an amphora
        clay_jar(c, 25.0, 63.8, 3.6, 9.0, 3, band=True, form='oil')         # a little oil jar in front
        shards = [c.poly([(36, 64), (37.5, 61.6), (40.5, 62.2), (41, 64)]), c.poly([(8, 64), (9, 62.4), (11.4, 63.0), (11.6, 64)])]
    else:
        clay_jar(c, 20.0, 63.6, 9.4, 25, 4, broken=True)                    # a cracked-open storage jar
        clay_jar(c, 34.5, 63.6, 5.2, 13, 5, band=True, form='oil')
        shards = [c.poly([(5, 64), (7, 61), (11, 62), (12, 64)]), c.poly([(39, 64), (40, 62.5), (43.5, 63), (44, 64)])]
    for sh in shards:
        c.shade(sh, 0.55 + 0 * c.X, L.DU_CLAY, mat=6)
    sand_mound(c, 24, 21, 2.2, 64.4, 50 + var)
    return make(f'jars{var}', c, 'ancient egyptian clay storage jars, terracotta amphorae with faded painted bands, dusty, cracked',
                seed=60 + var, denoise=0.38, cn=0.65, mix=0.25, pal=pal_of(L.DU_CLAY, L.DU_SAND),
                mat_pals={6: pal_of(L.DU_CLAY, ['#1d110a']), 3: pal_of(L.DU_SAND[:-1])},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#e3c68f', rim_k=0.45)


def du_crates():
    """Grave goods for the long road: cedar chests with bronze corners, a roped linen bundle, a reed basket."""
    c = Cv(48, 64, S=16); W_ = L.DU_STONE
    def chest(x0, y0, x1, y1, seed, lid=True):
        front = c.rect(x0, y0 + 2.0, x1, y1)
        topf = c.poly([(x0, y0 + 2.0), (x0 + 1.6, y0), (x1 + 1.6, y0), (x1, y0 + 2.0)])
        side = c.poly([(x1, y0 + 2.0), (x1 + 1.6, y0), (x1 + 1.6, y1 - 1.8), (x1, y1)])
        grain = 0.5 + 0.5 * np.sin(c.Y * 4.0 + 3 * c.noise(2.5, seed))
        c.shade(front, (0.3 + 0.06 * grain) * stone_tex(c, seed, 2, 0.08), W_, mat=1)
        c.shade(topf, 0.56 + 0.05 * grain, W_, mat=1)
        c.shade(side, 0.17 + 0.04 * grain, W_, mat=1)
        for xx in np.arange(x0 + 4, x1 - 2, 4.5):    # plank seams
            c.mulv(c.rect(xx, y0 + 3, xx + 0.45, y1) * front, 0.7)
        for xx in (x0 + 0.2, x1 - 1.4):          # bronze corner straps
            c.shade(c.rect(xx, y0 + 2, xx + 1.2, y1) , 0.42 + 0 * c.X, L.DU_GOLD, mat=2)
        c.shade(c.rect(x0, y0 + 2.0, x1, y0 + 3.0), 0.3 + 0 * c.X, L.DU_GOLD, mat=2)
        c.mulv(c.rect(x0 + 2, y0 + 3.8, x1 - 2, y0 + 4.3), 0.6)
    chest(4, 48, 22, 64, 1)
    chest(8.5, 39.5, 19, 48, 3)
    clay_jar(c, 28.0, 63.8, 4.6, 12, 6, band=True, form='amph')
    # a roped linen bundle leaning on the right
    b = c.ell(39.5, 55.5, 5.6, 8.4)
    c.shade(b, c.pillow(b, 4, amb=0.25, k=0.8) * stone_tex(c, 4, 1.2, 0.08), L.DU_BONE, mat=7)
    for yy in (51.5, 58.5):
        c.mulv(c.path([(34.2, yy), (44.8, yy + 0.6)], 0.7) * b, 0.55)
    sand_mound(c, 26, 22, 1.8, 64.4, 52)
    return make('crates', c, 'ancient egyptian cedar wood chests with bronze corner fittings stacked, a roped linen bundle, a reed basket, tomb grave goods',
                seed=70, denoise=0.36, cn=0.65, mix=0.22, pal=pal_of(W_, L.DU_GOLD[:-1], L.DU_BONE, L.DU_SAND, L.DU_CLAY),
                mat_pals={1: pal_of(W_[:9]), 2: pal_of(L.DU_GOLD[:-1]), 7: pal_of(L.DU_BONE, ['#2a1a10']), 3: pal_of(L.DU_SAND[:-1]), 6: pal_of(L.DU_CLAY)},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#e3c68f', rim_k=0.4)


def du_banner():
    """A sun-king's standard: a cedar pole with a gilded disc finial and a tattered faded-lapis linen banner. Frame 0 is
    painted; 1-3 sway the cloth by column displacement (the pole stays put)."""
    c = Cv(48, 64, S=16); px_ = 14.0
    pole, pv = c.revolve(px_, 3.5, 64, lambda y: 1.05, amb=0.18, k=0.85)
    c.shade(pole, pv * 0.7, L.DU_STONE, mat=1)
    ring = c.ell(px_, 3.4, 3.0, 3.0); c.shade(ring, c.pillow(ring, 2, amb=0.3, k=0.8), L.DU_GOLD, mat=2)     # the disc
    c.erase(c.ell(px_, 3.4, 1.3, 1.3))
    for sgn in (-1, 1):   # two little horns cradling the disc
        c.shade(c.path([(px_, 7.4), (px_ + sgn * 2.8, 6.6), (px_ + sgn * 3.6, 4.2)], 0.9, 0.5), 0.5 + 0 * c.X, L.DU_GOLD, mat=2)
    c.shade(c.rect(px_ - 1.6, 8.0, px_ + 1.6, 9.4), 0.55 + 0 * c.X, L.DU_GOLD, mat=2)
    # the cross-bar and the cloth
    c.shade(c.rect(px_ - 1, 9.6, px_ + 26, 10.8), 0.5 + 0 * c.X, L.DU_STONE, mat=1)
    rng = np.random.default_rng(3)
    bot = [(px_ + 1 + i * 2.6, 46 + (5 if i in (2, 3) else 0) - (3 if i == 6 else 0) + rng.uniform(-1.2, 1.2)) for i in range(10)]
    cloth = c.poly([(px_ + 1, 10.8), (px_ + 25.5, 10.8), (px_ + 25.0, 30), (px_ + 24.0, 41)] + bot[::-1])
    folds = 0.5 + 0.5 * np.sin((c.X - px_) * 0.55 + 0.6)
    vc = (0.42 + 0.26 * folds - 0.1 * (c.Y - 10) / 40) * stone_tex(c, 5, 2, 0.08)
    c.shade(cloth, vc, L.DU_LAPIS, mat=5)
    for y0 in (12.0, 41.5):    # ochre borders
        c.shade(cloth * (np.abs(c.Y - y0) < 0.9), 0.45 + 0.2 * folds, L.DU_GOLD, mat=2)
    sun = c.ell(px_ + 13, 25, 4.6, 4.6)
    c.shade(sun * cloth, 0.38 + 0.22 * folds, L.DU_GOLD, mat=2)
    c.shade(c.ell(px_ + 13, 25, 2.4, 2.4) * cloth, 0.25 + 0.15 * folds, L.DU_GOLD, mat=2)
    for k in range(8):   # rays, worn
        a = k * math.pi / 4
        c.shade(c.path([(px_ + 13 + 5.6 * math.cos(a), 25 + 5.6 * math.sin(a)), (px_ + 13 + 7.4 * math.cos(a), 25 + 7.4 * math.sin(a))], 0.8) * cloth,
                0.35 + 0.15 * folds, L.DU_GOLD, mat=2)
    c.erase(c.ell(px_ + 20, 34, 1.2, 1.8)); c.erase(c.ell(px_ + 8, 38, 0.9, 1.2))       # moth holes
    sand_mound(c, px_, 6, 1.5, 64.4, 53)
    f0 = make('banner_du', c, 'a tattered ancient egyptian royal standard banner of faded indigo linen with a worn golden sun disc, on a wooden pole with a gilded disc finial',
              seed=80, denoise=0.34, cn=0.7, mix=0.2, pal=pal_of(L.DU_STONE, L.DU_GOLD[:-1], L.DU_LAPIS, L.DU_SAND),
              mat_pals={1: pal_of(L.DU_STONE), 2: pal_of(L.DU_GOLD[:-1]), 5: pal_of(L.DU_LAPIS, ['#0d0806']), 3: pal_of(L.DU_SAND[:-1])},
              out_dark='#0d0806', out_lit='#2a1a10', rim_col='#e3c68f', rim_k=0.4)
    mats = LAST_MATS
    return [f0] + [sway(f0, mats, k, x_from=int(px_) + 2, y_from=11, amp=1.6) for k in (1, 2, 3)]


def sway(im, mats, k, x_from, y_from, amp=1.5, n=4):
    """Cloth sway by row displacement: rows further from the hanging edge (x_from) and lower (y_from) move more."""
    a = np.asarray(im).copy(); out = a.copy(); H, W = a.shape[:2]
    out[:, x_from:] = 0
    ph = 2 * math.pi * k / n
    for y in range(H):
        t = max(0, (y - y_from)) / max(1, H - y_from)
        for x in range(x_from, W):
            dx = amp * math.sin(ph + y * 0.22) * (x - x_from) / (W - x_from) * (0.4 + 0.6 * t)
            sx = int(round(x - dx))
            if x_from <= sx < W: out[y, x] = a[y, sx]
    out[:, :x_from] = a[:, :x_from]
    return Image.fromarray(out, 'RGBA')


def du_scarabidol():
    """Khepri: a tarnished gold scarab raising the sun disc in its forelegs, on a sandstone pedestal (light at y-38)."""
    c = Cv(48, 64, S=16); cx = 24.0
    ped = c.poly([(cx - 9, 64), (cx - 8, 51.6), (cx + 8, 51.6), (cx + 9, 64)])
    c.shade(ped, (0.48 - 0.22 * np.clip((c.X - cx + 9) / 18, 0, 1)) * stone_tex(c, 1, 2, 0.1), L.DU_STONE, mat=1)
    cap = c.poly([(cx - 10, 52.2), (cx - 10.4, 49.6), (cx + 10.4, 49.6), (cx + 10, 52.2)])
    c.shade(cap, np.where(c.Y < 50.6, 0.84, 0.5), L.DU_STONE, mat=1)
    c.mulv(c.rect(cx - 5.5, 55, cx + 5.5, 61), 0.72)
    # the beetle from above, stood on its tail: broad domed wing-cases split down the middle, pronotum, head
    body = c.ell(cx, 42.4, 11.0, 7.4)
    elL = body * (c.X < cx); elR = body * (c.X >= cx)
    v = np.maximum(c.pillow(elL, 3.6, depth=1.2, amb=0.12, k=0.98) * elL, c.pillow(elR, 3.6, depth=1.2, amb=0.12, k=0.98) * elR)
    c.shade(body, v, L.DU_GOLD, mat=2)
    c.mulv(c.path([(cx, 37.8), (cx, 49.8)], 0.9) * body, 0.35)
    for sg in (-1, 1):     # striae on the wing cases
        c.mulv(c.path([(cx + sg * 4.0, 39.0), (cx + sg * 4.6, 47.4)], 0.45) * body, 0.7)
    pro = c.ell(cx, 35.4, 8.6, 3.0); c.shade(pro, c.pillow(pro, 2.6, amb=0.14, k=0.95), L.DU_GOLD, mat=2)
    c.mulv(c.path([(cx - 8.4, 37.9), (cx + 8.4, 37.9)], 0.7), 0.45)
    hd = c.poly([(cx - 5.4, 33.4), (cx - 4.6, 31.6), (cx - 2.0, 31.0), (cx + 2.0, 31.0), (cx + 4.6, 31.6), (cx + 5.4, 33.4)])
    for k in range(5): c.mulv(c.path([(cx - 4.4 + k * 2.2, 31.2), (cx - 4.8 + k * 2.4, 30.2)], 0.7), 1.0)
    c.shade(hd, 0.6 + 0 * c.X, L.DU_GOLD, mat=2)
    for sg in (-1, 1):
        # forelegs raised to the disc, mid + hind legs gripping the pedestal edge
        c.shade(c.path([(cx + sg * 6.6, 33.6), (cx + sg * 10.4, 30.0), (cx + sg * 6.0, 26.4)], 1.6, 1.1), (0.55 if sg < 0 else 0.34) + 0 * c.X, L.DU_GOLD, mat=2)
        c.shade(c.path([(cx + sg * 10.4, 39.5), (cx + sg * 14.6, 41.2), (cx + sg * 14.4, 46.6)], 1.6, 1.1), (0.5 if sg < 0 else 0.3) + 0 * c.X, L.DU_GOLD, mat=2)
        c.shade(c.path([(cx + sg * 9.0, 46.8), (cx + sg * 12.6, 48.4), (cx + sg * 11.6, 50.2)], 1.5, 1.0), (0.46 if sg < 0 else 0.28) + 0 * c.X, L.DU_GOLD, mat=2)
    sun = c.ell(cx, 25.6, 4.4, 4.4)
    c.shade(sun, 0.5 + 0.5 * np.clip(1 - np.sqrt((c.X - cx + 1.2) ** 2 + (c.Y - 24.6) ** 2) / 4.4, 0, 1), L.DU_FIRE[1:], mat=8)
    return make('scarabidol', c, 'a tarnished golden scarab beetle idol khepri raising a glowing sun disc in its front legs, on a carved sandstone pedestal, egyptian',
                seed=90, denoise=0.36, cn=0.7, mix=0.2, pal=pal_of(L.DU_STONE, L.DU_GOLD, L.DU_FIRE[1:]),
                mat_pals={1: pal_of(L.DU_STONE), 2: pal_of(L.DU_GOLD[:-1], ['#1d110a']), 8: pal_of(L.DU_FIRE[1:])},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#f4df9f', rim_k=0.45)


def du_hoard():
    """A tomb robber's undoing: a slumped heap of tarnished gold, a gilded mask face-up, a canopic jar on its side, a casket."""
    c = Cv(48, 64, S=16)
    heap = c.poly([(1.5, 64), (5, 58.5), (12, 53.5), (20, 51), (28, 50.6), (36, 53), (42.5, 57.5), (46.5, 64)])
    v = c.pillow(heap, 6, depth=0.9, amb=0.16, k=0.9)
    coins = (c.noise(0.55, 3) > 0.56).astype(float)
    c.shade(heap, (v * 0.78 + 0.14 * coins - 0.12) * (0.9 + 0.1 * c.noise(1.5, 4)), L.DU_GOLD, mat=2)
    # the casket, left
    box_ = c.rect(5, 44.5, 16, 55.0); c.shade(box_, 0.36 * stone_tex(c, 5, 1.5, 0.1), L.DU_STONE, mat=1)
    lid = c.poly([(4.4, 44.8), (5.4, 42.2), (16.4, 42.2), (16.8, 44.8)]); c.shade(lid, 0.6 + 0 * c.X, L.DU_STONE, mat=1)
    c.shade(c.rect(4.6, 44.4, 16.6, 45.4), 0.5 + 0 * c.X, L.DU_GOLD, mat=2)
    # a tall goblet / ewer right
    ew, ev = c.revolve(36.5, 37.5, 52, lambda y: 1.4 + 2.2 * math.sin(min(1, (y - 37.5) / 10) * math.pi * 0.85) if y < 48 else 1.0 + 1.8 * (y - 48) / 4, amb=0.18, k=0.9)
    c.shade(ew, ev, L.DU_GOLD, mat=2)
    # the gilded mask lying on the heap
    mk = c.ell(24.5, 48.0, 4.2, 4.8); c.shade(mk, c.pillow(mk, 2.6, amb=0.2, k=0.9) * 0.95, L.DU_GOLD, mat=2)
    for sg in (-1, 1): c.mulv(c.ell(24.5 + sg * 1.6, 47.2, 0.9, 0.45), 0.35)
    c.mulv(c.path([(23.5, 50.5), (25.5, 50.5)], 0.45), 0.5)
    # a canopic jar on its side (stone) at the foot
    cj = c.ell(13.5, 60.2, 4.4, 2.6); c.shade(cj, c.pillow(cj, 2, amb=0.2, k=0.85) * 0.75, L.DU_BONE, mat=7)
    hd = c.ell(18.6, 60.0, 1.9, 2.1); c.shade(hd, 0.62 + 0 * c.X, L.DU_BONE, mat=7)

    def fx(q, a):
        P = L.Px(q, a, [L.DU_GOLD, L.DU_STONE])
        rng = np.random.default_rng(9)
        for _ in range(26):     # glints on coin edges
            x, y = rng.integers(4, 44), rng.integers(52, 63)
            if a[y, x] and P.get(x, y) and P.get(x, y)[0] == 0: P.step(x, y, 2)
        return q, a
    return make('hoard', c, 'a heap of tarnished ancient gold coins and treasure, a golden funerary mask, a gilded ewer, a small casket, egyptian tomb treasure',
                seed=100, denoise=0.38, cn=0.65, mix=0.25, pal=pal_of(L.DU_GOLD, L.DU_STONE, L.DU_BONE), fx=fx,
                mat_pals={2: pal_of(L.DU_GOLD, ['#1d110a']), 1: pal_of(L.DU_STONE), 7: pal_of(L.DU_BONE)},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#fff0c4', rim_k=0.35)


def du_sarcophagus(var):
    """An anthropoid coffin stood on end: nemes-striped head, a calm gilt face, crossed arms with crook and flail, a vulture
    spreading its wings across the breast. var 0: gilt, worn to the wood in places; var 1: stripped to the linen and gesso."""
    c = Cv(48, 64, S=16); cx = 24.0
    def r(y):
        if y < 15: return 0
        if y < 30: return 5.4 + 2.6 * math.sin((y - 15) / 15 * math.pi * 0.5)      # head + nemes
        if y < 40: return 8.0 - 0.6 * (y - 30) / 10                                  # shoulders/arms
        return 7.4 - 2.0 * (y - 40) / 21 + (1.2 if y > 60 else 0)                     # tapering to the feet
    body, v = c.revolve(cx, 13.0, 64, lambda y: r(y) if y >= 15 else 5.4 * math.sqrt(max(0, 1 - ((15 - y) / 2.2) ** 2)), amb=0.14, k=0.92)
    gold = L.DU_GOLD if var == 0 else L.DU_BONE
    base_ramp = gold
    c.shade(body, v * (0.9 + 0.1 * c.noise(1.5, 1 + var)), base_ramp, mat=2 if var == 0 else 7)
    # nemes stripes on the head-cloth (outside the face)
    face = c.ell(cx, 23.5, 4.0, 4.8)
    stripes = body * (c.Y < 33) * (face < 0.5) * (((c.Y - 14) % 3.2) < 1.5)
    c.tint(stripes, hx(L.DU_LAPIS[1 if var == 0 else 0]), 0.8)
    c.shade(face, c.pillow(face, 2.4, amb=0.3, k=0.85) * 1.0, L.DU_GOLD if var == 0 else L.DU_STONE[3:], mat=2 if var == 0 else 1)
    for sg in (-1, 1):
        c.mulv(c.ell(cx + sg * 1.5, 22.6, 1.0, 0.45), 0.35)                    # kohl-lined eyes (closed)
    c.mulv(c.path([(cx - 1.0, 26.6), (cx + 1.0, 26.6)], 0.4), 0.55)
    beard = c.poly([(cx - 0.9, 28.2), (cx + 0.9, 28.2), (cx + 0.7, 32.6), (cx - 0.7, 32.6)]); c.shade(beard, 0.4 + 0 * c.X, L.DU_LAPIS, mat=5)
    # broad collar
    col = body * (c.Y > 31.5) * (c.Y < 36)
    c.tint(col * (np.sin((c.Y - 31.5) * 4.5) > 0), hx(L.DU_LAPIS[2]), 0.6)
    # crossed arms + crook and flail
    for sg, ang in ((-1, 0.5), (1, -0.5)):
        c.shade(c.path([(cx + sg * 6.0, 37.0), (cx - sg * 2.6, 41.4)], 2.0, 1.6), 0.6 + 0.0 * c.X if sg < 0 else 0.42 + 0 * c.X, gold, mat=2 if var == 0 else 7)
    c.shade(c.path([(cx - 3.4, 33.8), (cx + 2.4, 45.0)], 0.7), 0.35 + 0 * c.X, L.DU_LAPIS, mat=5)
    c.shade(c.path([(cx + 3.4, 33.8), (cx - 2.4, 45.0)], 0.7), 0.6 + 0 * c.X, L.DU_GOLD, mat=2)
    # the vulture's wings across the legs + text column
    for y0 in (46.0, 49.0):
        c.tint(body * (np.abs(c.Y - y0 - 0.3 * np.abs(c.X - cx)) < 0.8), hx(L.DU_LAPIS[2]), 0.55)
    c.mulv(c.rect(cx - 1.0, 52, cx + 1.0, 61.5) * body, 0.7)
    # wear: gilding gone to dark wood / gesso
    wear = body * (c.noise(3.5, 7 + var) > (0.78 if var == 0 else 0.55)) * (face < 0.5) * (c.Y > 34)
    c.tint(wear, hx(L.DU_STONE[3] if var == 0 else L.DU_STONE[5]), 0.65)
    c.shade(c.rect(cx - 9.2, 61.4, cx + 9.2, 64), 0.4 + 0 * c.X, L.DU_STONE, mat=1)      # the stand
    return make(f'sarcophagus{var}', c, 'an ancient egyptian anthropoid coffin standing upright, ' + ('gilded and worn, faded lapis stripes' if var == 0 else
                'stripped of gold, cracked white gesso and linen') + ', calm carved face, crossed arms holding crook and flail',
                seed=110 + var, denoise=0.36, cn=0.7, mix=0.1, pal=pal_of(L.DU_GOLD[:-1], L.DU_LAPIS, L.DU_STONE, L.DU_BONE),
                mat_pals={2: pal_of(L.DU_GOLD[:-1], L.DU_LAPIS[1:3], L.DU_STONE[2:5]), 7: pal_of(L.DU_BONE, L.DU_LAPIS[1:3], L.DU_STONE[3:7]),
                          5: pal_of(L.DU_LAPIS), 1: pal_of(L.DU_STONE)},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#f4df9f', rim_k=0.4)


def du_brazier():
    """A bronze fire-bowl on lion-footed legs (fire at y-30). Frame 0 painted; the fire is drawn per frame."""
    c = Cv(48, 64, S=16); cx = 24.0
    for sg in (-1, 0, 1):
        leg = c.path([(cx + sg * 3.0, 41.5), (cx + sg * 6.5, 55), (cx + sg * 8.6, 62.6)], 1.5, 1.1)
        c.shade(leg, (0.5 if sg <= 0 else 0.3) + 0 * c.X, L.DU_GOLD[:5], mat=2)
        c.shade(c.ell(cx + sg * 9.0, 63.0, 1.8, 1.2), 0.42 + 0 * c.X, L.DU_GOLD[:5], mat=2)       # lion paws
    c.shade(c.rect(cx - 6.5, 51, cx + 6.5, 52.2), 0.35 + 0 * c.X, L.DU_GOLD[:5], mat=2)           # the stretcher ring
    bowl, bv = c.revolve(cx, 34.4, 43.2, lambda y: 10.6 - 7.0 * ((y - 34.4) / 8.8) ** 1.6, amb=0.12, k=0.95)
    c.shade(bowl, bv * 0.85, L.DU_GOLD[:5], mat=2)
    lip = c.ell(cx, 34.6, 10.8, 1.4); c.shade(lip, 0.72 + 0 * c.X, L.DU_GOLD[:5], mat=2)
    coals = c.ell(cx, 34.4, 9.4, 0.9); c.shade(coals, 0.3 + 0.2 * c.noise(0.6, 3), L.DU_FIRE, mat=8)
    for k in range(5):    # embossed band
        c.mulv(c.ell(cx - 8 + k * 4, 38.0, 0.9, 0.9) * bowl, 1.3)
    f0 = make('brazier_du', c, 'an ancient egyptian bronze fire bowl brazier on three lion footed legs, dark patinated bronze',
              seed=120, denoise=0.34, cn=0.7, mix=0.2, pal=pal_of(L.DU_GOLD[:5], L.DU_FIRE, ['#1d110a']),
              mat_pals={2: pal_of(L.DU_GOLD[:5], ['#1d110a', '#2a1a10']), 8: pal_of(L.DU_FIRE)},
              out_dark='#0d0806', out_lit='#2a1a10', rim_col='#f6d994', rim_k=0.4)
    out = []
    for f in range(4):
        im = f0.copy(); im.alpha_composite(fire_layer(48, 64, cx, 34.8, 15, 13, f, seed=4, tongues=4)); out.append(im)
    return out


# =============================================================================================== DUNES: palms (xsb_tall 64x112, 4f sway)
PALM_V = [dict(base=31, lean=8, top=30, seed=1), dict(base=27, lean=-10, top=38, seed=2), dict(base=36, lean=3, top=26, seed=3)]


def palm_trunk(c, base, lean, top, foot=111.5, w0=4.2, w1=2.8, dead=False, seed=0):
    def xc(t): return base + lean * t ** 1.6
    ys = np.linspace(foot, top, 60)
    ts = (foot - ys) / (foot - top)
    left = [(xc(t) - (w0 + (w1 - w0) * t), y) for t, y in zip(ts, ys)]
    right = [(xc(t) + (w0 + (w1 - w0) * t), y) for t, y in zip(ts, ys)]
    m = c.poly(left + right[::-1])
    tY = np.clip((foot - c.Y) / (foot - top), 0, 1)
    cxY = base + lean * tY ** 1.6; rY = w0 + (w1 - w0) * tY
    v = c.cyl(cxY, rY, amb=0.14, k=0.86)
    # the scaly rings of old frond bases: each ring a lip lit on top
    ring = ((foot - c.Y) % 3.1) / 3.1
    v = v * (0.72 + 0.34 * np.clip(ring * 1.6, 0, 1)) * stone_tex(c, seed + 5, 1.5, 0.08)
    c.shade(m, v * (0.85 if not dead else 0.75), L.DU_STONE, mat=1)
    return m


def frond(c, x0, y0, ang, length, droop, seed, val=0.6, cols=None, leaflet=6.0, dry=False):
    """One feathery frond: a curved rib with leaflets hanging off both sides, drawn as tapered strokes."""
    cols = cols or L.DU_LEAF
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(14):
        t = i / 13
        pts.append((x0 + math.cos(ang) * length * t, y0 + math.sin(ang) * length * t + droop * length * t * t))
    segs = []
    for i in range(1, 13):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / n, dx / n
        ll = leaflet * (1 - i / 15) * rng.uniform(0.8, 1.1)
        for sd in (-1, 1):
            ex = ax + (nx * sd * 0.45 + dx / n * 0.45) * ll
            ey = ay + (ny * sd * 0.45 + dy / n * 0.45) * ll + ll * 0.7
            segs.append((ax, ay, ex, ey, 0.75 * (1 - i / 16) + 0.25))
    leaves = c.lines(segs)
    rib = c.path(pts, 1.0, 0.45)
    m = np.clip(leaves + rib, 0, 1)
    vv = val * (0.88 + 0.2 * c.noise(1.2, seed))
    c.shade(m, vv + 0 * c.X, cols, mat=10)
    c.shade(rib, (val + 0.12) + 0 * c.X, cols, mat=10)
    return m


def tall_palm(var, f=0):
    P = PALM_V[var]
    c = Cv(64, 112, S=8)
    base, lean, top = P['base'], P['lean'], P['top']
    palm_trunk(c, base, lean, top, seed=P['seed'])
    tx, ty = base + lean, top
    # fronds: back ones dark, front/top ones sunlit
    # (angle deg, length, droop, value): fronds arc out and fall; back ones dark, the top/front ones sunlit
    spec = [(-178, 27, 1.5, 0.28), (-2, 27, 1.5, 0.3), (-160, 30, 1.0, 0.38), (-20, 30, 1.0, 0.4), (-195, 22, 2.2, 0.26),
            (15, 22, 2.2, 0.27), (-140, 28, 0.75, 0.55), (-40, 28, 0.75, 0.55), (-118, 22, 0.75, 0.68), (-62, 22, 0.75, 0.68),
            (-92, 15, 1.4, 0.74), (-168, 24, 1.3, 0.5), (-12, 24, 1.3, 0.52)]
    rng = np.random.default_rng(P['seed'])
    for k, (a, Ln, dr, val) in enumerate(spec):
        a = math.radians(a + rng.uniform(-6, 6))
        frond(c, tx, ty, a, Ln * rng.uniform(0.92, 1.08), dr * 0.55, P['seed'] * 31 + k, val=val, leaflet=7.5)
    # dates hanging under the crown + the boss of frond bases
    for k in range(5):
        d = c.ell(tx - 3.5 + k * 1.8, ty + 3.6 + (k % 2) * 1.2, 1.1, 1.4)
        c.shade(d, c.pillow(d, 0.8, amb=0.3, k=0.8) * 0.75, L.DU_CLAY, mat=6)
    boss = c.ell(tx, ty + 0.6, 3.0, 2.4); c.shade(boss, c.pillow(boss, 1.6, amb=0.2, k=0.8) * 0.5, L.DU_STONE, mat=1)
    sand_mound(c, base, 12, 2.4, 112.2, 140 + var)
    f0 = make(f'palm{var}', c, 'a tall desert date palm tree, scaly ringed trunk, drooping feathery fronds in dusty olive green, clusters of dates',
              seed=150 + var, denoise=0.36, cn=0.7, mix=0.15, prompt=('pixel art game prop, dark fantasy, a tall desert date palm tree, scaly ringed trunk, '
              'drooping feathery fronds in dusty olive green, clusters of dates, warm sunlight from the upper left, muted desaturated palette, side view, single object, '
              'isolated on a plain flat grey background'),
              pal=pal_of(L.DU_STONE, L.DU_LEAF, L.DU_CLAY, L.DU_SAND),
              mat_pals={1: pal_of(L.DU_STONE), 10: pal_of(L.DU_LEAF), 6: pal_of(L.DU_CLAY), 3: pal_of(L.DU_SAND[:-1])},
              out_dark='#0d0806', out_lit='#151408', rim_col='#c4b46a', rim_k=0.35, thresh=0.42)
    mats = LAST_MATS
    return [f0] + [frond_sway(f0, mats, k, tx, ty) for k in (1, 2, 3)]


def frond_sway(im, mats, k, tx, ty, n=4, amp=1.4):
    """Rotate the crown's fronds a little about the crown (k of n): the trunk and the outline around it stay put."""
    a = np.asarray(im).copy(); H, W = a.shape[:2]
    ph = 2 * math.pi * k / n; ang = math.radians(1.6) * math.sin(ph)
    out = a.copy()
    crown = np.zeros((H, W), bool)
    ys, xs = np.nonzero(a[..., 3] > 0)
    for y, x in zip(ys, xs):
        if y < ty + 16 and math.hypot(x - tx, y - ty) > 3.5: crown[y, x] = True
    out[crown] = 0
    for y in range(max(0, int(ty) - 40), min(H, int(ty) + 30)):
        for x in range(W):
            r = math.hypot(x - tx, y - ty)
            if r < 3.5: continue
            th = -ang * min(1.0, r / 20) ** 1.2
            sx = tx + (x - tx) * math.cos(th) - (y - ty) * math.sin(th)
            sy = ty + (x - tx) * math.sin(th) + (y - ty) * math.cos(th) - amp * 0.3 * math.sin(ph) * (r / 25)
            ix, iy = int(round(sx)), int(round(sy))
            if 0 <= ix < W and 0 <= iy < H and crown[iy, ix]:
                out[y, x] = a[iy, ix]
    return Image.fromarray(out, 'RGBA')


def tall_palmdead():
    """A dead palm: the crown snapped off in a jagged split, one dry frond hanging down the trunk, bark bleached."""
    c = Cv(64, 112, S=8)
    base, lean, top = 30, 5, 47
    palm_trunk(c, base, lean, top, dead=True, seed=9, w1=3.0)
    tx, ty = base + lean, top
    c.erase(c.poly([(tx - 4, ty - 2), (tx - 0.5, ty - 2), (tx - 1.0, ty + 3.5), (tx - 2.2, ty + 1.2), (tx - 4, ty + 4.5)]))
    spl = c.poly([(tx - 0.8, ty + 3.0), (tx + 0.2, ty - 6.5), (tx + 1.4, ty - 1.5), (tx + 2.0, ty - 4.0), (tx + 3.4, ty + 2.5)])
    c.shade(spl, 0.6 + 0.12 * c.noise(0.6, 3), L.DU_STONE, mat=1)
    c.mulv(c.path([(tx + 0.6, ty + 2), (tx - 0.6, ty + 16), (tx + 0.4, ty + 24)], 0.5), 0.45)      # the split running down
    DRY = ['#1d110a', '#2a1a10', '#3f2919', '#543a22', '#6c4b2b', '#8a5f2e']
    frond(c, tx + 2.6, ty + 3, math.radians(70), 22, 0.15, 71, val=0.5, cols=DRY, leaflet=3.2, dry=True)
    frond(c, tx - 2.6, ty + 6, math.radians(118), 12, 0.2, 72, val=0.35, cols=DRY, leaflet=2.6, dry=True)
    sand_mound(c, base, 10, 2.2, 112.2, 149)
    return make('palmdead', c, 'a dead desert palm trunk snapped off at the top in a jagged split, a dry brown frond hanging down, bleached bark',
                seed=160, denoise=0.36, cn=0.7, mix=0.15, pal=pal_of(L.DU_STONE, L.DU_SAND),
                mat_pals={1: pal_of(L.DU_STONE), 10: pal_of(L.DU_STONE[1:7]), 3: pal_of(L.DU_SAND[:-1])},
                out_dark='#0d0806', out_lit='#2a1a10', rim_col='#e3c68f', rim_k=0.4, thresh=0.42)


# =============================================================================================== DUNES: the other xsb_big paintings
BIGKW = dict(out_dark='#0d0806', out_lit='#2a1a10', inner=True, rim_col='#f4df9f', rim_k=0.45)
BIG_PAL = pal_of(L.DU_STONE, L.DU_GOLD[:-1], L.DU_SAND, L.DU_LAPIS)
BIG_MP = {1: pal_of(L.DU_STONE), 2: pal_of(L.DU_GOLD[:-1]), 3: pal_of(L.DU_SAND), 5: pal_of(L.DU_LAPIS, ['#6c4b2b'])}


def cavetto(c, x0, x1, y_top, depth, tex, mat=1):
    """An Egyptian cavetto cornice: a lit top fillet over a flaring hollow (dark at the top of the hollow)."""
    cav = c.poly([(x0 + 3, y_top + depth), (x0 - 1.5, y_top + 1.2), (x0 - 1.2, y_top - 1), (x1 + 1.2, y_top - 1), (x1 + 1.5, y_top + 1.2), (x1 - 3, y_top + depth)])
    v = np.where(c.Y < y_top + 0.4, 0.92, 0.32 + 0.4 * np.clip((c.Y - y_top) / depth, 0, 1))
    c.shade(cav, v * tex, L.DU_STONE, mat=mat)
    c.shade(c.rect(x0 + 2.5, y_top + depth - 0.2, x1 - 2.5, y_top + depth + 1.4), 0.7 * tex, L.DU_STONE, mat=mat)   # torus
    return cav


def big_sealdoor():
    """A sealed tomb door's frame: battered jambs carved with columns of glyphs, a cavetto lintel with the winged eye.
    The opening between the inner jamb faces (cx +- 8) stays clear: the kit gate draws there."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE; cx = 96.0
    tex = stone_tex(c, 201, 3, 0.09) * stone_tex(c, 202, 1, 0.05)
    for sg in (-1, 1):
        xi, xo_t, xo_b = cx + sg * 8, cx + sg * 20, cx + sg * 23
        jamb = c.poly([(xi, 128), (xi, 40), (xo_t, 40), (xo_b, 128)])
        u = np.clip((c.X - min(xi, xo_b)) / 15, 0, 1)
        v = (0.62 - 0.22 * u) if sg < 0 else (0.42 - 0.16 * u)
        c.shade(jamb, v * tex, S_, mat=1)
        c.shade(c.rect(xi - (1.6 if sg > 0 else 0), 40, xi + (1.6 if sg < 0 else 0), 128), (0.28 if sg < 0 else 0.6) + 0 * c.X, S_, mat=1)   # reveal
        for y in np.arange(48, 128, 10.5):
            c.mulv(c.rect(min(xi, xo_b), y, max(xi, xo_b), y + 0.6) * jamb, 0.72)
    lin = c.rect(cx - 25, 27, cx + 25, 40.5)
    c.shade(lin, (0.56 - 0.18 * np.clip((c.X - cx + 25) / 50, 0, 1)) * tex, S_, mat=1)
    cavetto(c, cx - 25, cx + 25, 20.5, 6.5, tex)
    eye = c.poly([(cx - 8, 33.5), (cx - 3, 30.4), (cx + 3, 30.4), (cx + 8, 33.5), (cx + 3, 36.0), (cx - 3, 36.0)])
    c.mulv(eye, 0.62)
    c.shade(c.ell(cx, 33.2, 2.2, 2.2), 0.55 + 0 * c.X, L.DU_LAPIS, mat=5)
    c.mulv(c.path([(cx - 6, 36), (cx - 7.5, 39.5), (cx - 5, 40)], 0.7), 0.55)
    c.mulv(c.path([(cx - 2, 36), (cx - 2.5, 39.6)], 0.6), 0.55)
    for sg in (-1, 1):
        wing = c.poly([(cx + sg * 9, 31), (cx + sg * 23, 29.6), (cx + sg * 23.5, 31.4), (cx + sg * 9, 34.4)])
        c.shade(wing, (0.42 + 0.12 * (0.5 + 0.5 * np.sin(c.X * 2.2))) * (1 if sg < 0 else 0.8), L.DU_LAPIS, mat=5)
        c.tint(wing * (c.noise(1.2, 210 + sg) > 0.6), hx(L.DU_STONE[5]), 0.8)

    def fx(q, a):
        P = L.Px(q, a, [S_, L.DU_LAPIS, L.DU_GOLD])
        for sg in (-1, 1):
            x0 = int(cx + sg * 14) - 2
            carve_glyphs(P, x0, x0 + 4, 46, 122, 205 + sg)
        return q, a
    return make('sealdoor', c, 'an ancient egyptian tomb door frame, battered sandstone jambs carved with columns of hieroglyphs, a cavetto cornice lintel with '
                'a winged eye of horus relief in faded lapis', seed=211, denoise=0.45, cn=0.65, mix=0.35, pix=0.55, fx=fx,
                pal=BIG_PAL, mat_pals=BIG_MP, **BIGKW)


def big_sundial():
    """The sun-wheel of DU13: a great stone disc relief sunk into the wall: rings of hours, rays in faded lapis, a tarnished
    gilt boss, cracked through and missing a wedge. Kept darker than v1 so it backs the mirror puzzle instead of shouting."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE; cx, cy, R = 96.0, 70.0, 54.5
    r = np.sqrt((c.X - cx) ** 2 + (c.Y - cy) ** 2); ang = np.arctan2(c.Y - cy, c.X - cx)
    disc = c.ell(cx, cy, R, R)
    # sculpted rings: a rim torus, a sunk band of hours, the ray field, a raised inner ring, the boss
    H = (2.0 * np.exp(-((r - (R - 2.4)) / 2.0) ** 2) - 1.4 * ((r > 38) & (r < 48)) + 1.6 * np.exp(-((r - 19) / 2.0) ** 2) + 4.0 * np.clip(1 - r / 11, 0, 1) ** 0.6)
    rays = (np.cos(ang * 12) > 0.55) & (r > 21) & (r < 37)
    H = H + 0.9 * rays
    val = c.relief(H, k_h=1.6, amb=0.18, k=0.82) * 0.78 * stone_tex(c, 221, 3, 0.1)
    val = val * (1 - 0.18 * np.clip(r / R, 0, 1))
    c.shade(disc, val, S_, mat=1)
    c.tint(disc * ((r > 21) & (r < 37) & ~rays) * (c.noise(2, 222) > 0.35), hx(L.DU_LAPIS[1]), 0.55)
    hours = disc * ((r > 39.5) & (r < 46.5)) * (np.abs(((ang / (2 * math.pi) * 24) % 1) - 0.5) < 0.07)
    c.mulv(hours, 0.55)
    boss = c.ell(cx, cy, 10.5, 10.5)
    c.shade(boss, c.relief(4.0 * np.clip(1 - r / 11, 0, 1) ** 0.6, k_h=1.6, amb=0.2, k=0.85) * 0.8, L.DU_GOLD, mat=2)
    c.mulv(c.ell(cx - 3.5, cy - 1.5, 1.4, 0.8) + c.ell(cx + 3.5, cy - 1.5, 1.4, 0.8), 0.45)     # the sun's calm face, worn
    c.mulv(c.path([(cx - 2.5, cy + 4), (cx + 2.5, cy + 4)], 0.5), 0.6)
    # damage: a missing wedge at the lower right, a crack across
    c.erase(c.poly([(cx + 30, cy + 46), (cx + 56, cy + 20), (cx + 60, cy + 60)]) * (r > 33))
    c.mulv(c.path([(cx - 50, cy - 20), (cx - 30, cy - 12), (cx - 22, cy - 18), (cx - 6, cy - 9)], 0.7), 0.5)
    return make('sundial', c, 'a huge carved stone sun disc relief set in an ancient tomb wall, concentric rings of hour marks, sun rays with faded lapis paint, '
                'a tarnished golden sun boss with a calm face, cracked, a missing wedge', seed=231, denoise=0.45, cn=0.65, mix=0.35, pix=0.55,
                pal=BIG_PAL, mat_pals=BIG_MP, **BIGKW)


def big_titles():
    """The Pharaoh's titles (DU11): a carved frieze with four upright cartouches (rope ovals on a base bar) under a cavetto
    cornice. The cartouche fields stay dark and plain: sbInkTitles inks the glyphs at x0+26+i*46, y0+63."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE
    tex = stone_tex(c, 241, 3, 0.08) * stone_tex(c, 242, 1, 0.05)
    panel = c.rect(3, 25, 189, 104)
    c.shade(panel, (0.46 - 0.1 * (c.Y - 25) / 79) * tex, S_, mat=1)
    cavetto(c, 3, 189, 19.5, 6.0, tex)
    c.shade(c.rect(3, 100.5, 189, 104.6), 0.62 * tex, S_, mat=1)
    for y in (28.5, 97.5):   # painted bands, flaking
        c.shade(c.rect(5, y, 187, y + 1.6) * (c.noise(1.4, 243 + int(y)) > 0.35), 0.4 + 0 * c.X, L.DU_LAPIS, mat=5)
    for i in range(4):
        cx = 26 + i * 46.0
        # the rope ring: a raised oval band, then the sunk field
        outer = c.ell(cx, 61.5, 16.0, 29.0); inner = c.ell(cx, 61.5, 12.6, 25.6)
        r = np.sqrt(((c.X - cx) / 14.3) ** 2 + ((c.Y - 61.5) / 27.3) ** 2)
        H = 1.6 * np.exp(-((r - 1.0) / 0.07) ** 2)
        val = c.relief(H, k_h=2.0, amb=0.2, k=0.85) * 0.7 * tex
        c.shade(np.clip(outer - inner, 0, 1), val, L.DU_GOLD, mat=2)
        c.mulv(np.clip(outer - inner, 0, 1) * (np.sin(np.arctan2(c.Y - 61.5, c.X - cx) * 40) > 0.5), 0.85)    # rope twist
        c.shade(inner, (0.24 + 0.06 * (c.Y - 36) / 50) * tex, S_, mat=1)
        c.shade(c.rect(cx - 14.5, 90.0, cx + 14.5, 93.6), 0.62 * tex, L.DU_GOLD, mat=2)                        # the base bar
        # the field's sunk edge: a shadow on the upper-left inside, a lit lip lower-right
        c.mulv(np.clip(inner - c.ell(cx + 0.8, 62.3, 12.6, 25.6), 0, 1), 0.6)
        for k in range(i + 1):                                                                                  # tally ticks under each
            c.mulv(c.rect(cx - i * 3 + k * 6 - 0.6, 95.2, cx - i * 3 + k * 6 + 0.6, 96.6), 0.5)
    # damage at the right end of the frieze
    c.erase(c.poly([(189.5, 18), (176, 18), (180, 26), (186, 32), (189.5, 40)]))
    return make('titles', c, 'a carved sandstone temple frieze with four royal cartouches, rope ovals on base bars, under a cavetto cornice, faded lapis bands, '
                'empty smooth cartouche fields', seed=251, denoise=0.42, cn=0.65, mix=0.3, pix=0.55, pal=BIG_PAL, mat_pals=BIG_MP, **BIGKW)


def big_hand():
    """A colossal stone hand rising from the dune, palm toward us, fingers half-curled, the little finger snapped, sand
    pouring off the knuckles. Sculpted as a height field."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE; X, Y = c.X, c.Y
    hx0 = 84.0
    palm = c.poly([(hx0 - 26, 128), (hx0 - 28, 96), (hx0 - 26, 74), (hx0 + 22, 70), (hx0 + 28, 92), (hx0 + 26, 128)])
    Hp = 10 * c.blur(palm, 8) + 3 * c.g2(hx0 - 14, 100, 10, 14) + 2.4 * c.g2(hx0 + 14, 102, 9, 12) - 2.0 * c.g2(hx0, 92, 8, 10)
    H = np.where(palm > 0.5, Hp, -9)
    fingers = [(-19, 76, 32, 6.4, -0.03), (-6, 72, 44, 6.8, -0.008), (7, 72, 41, 6.6, 0.012), (19, 75, 22, 5.8, 0.05)]   # x, base y, length, half-width, lean
    mask = palm.copy()
    for k, (fx_, by, Ln, hw, lean) in enumerate(fingers):
        tipx, tipy = hx0 + fx_ + lean * Ln * 10, by - Ln
        seg = []
        for j in range(3):          # three phalanges, each a rounded capsule, joints a little narrower
            t0, t1 = j / 3, (j + 1) / 3
            x0, y0 = hx0 + fx_ + (tipx - hx0 - fx_) * t0, by + (tipy - by) * t0
            x1, y1 = hx0 + fx_ + (tipx - hx0 - fx_) * t1, by + (tipy - by) * t1
            w = hw * (1 - 0.12 * j)
            cap = c.lines([(x0, y0, x1, y1, 2 * w)])
            hcap = 7 + 4 * c.blur(cap, w * 0.5) + 1.0 * c.g2(x1, y1, w, 1.2)
            H = np.where(cap > 0.5, np.maximum(H, hcap), H)
            mask = np.maximum(mask, cap)
            if k == 3 and j == 1: break  # the little finger: snapped at the second joint
        c.mulv(np.zeros_like(X), 1)
    thumb = c.lines([(hx0 + 24, 98, hx0 + 38, 86, 11), (hx0 + 38, 86, hx0 + 44, 74, 9)])
    H = np.where(thumb > 0.5, np.maximum(H, 8 + 4 * c.blur(thumb, 2.5)), H)
    mask = np.maximum(mask, thumb)
    # creases of the palm, a crack across the wrist
    H = H - 1.4 * c.blur(c.path([(hx0 - 22, 86), (hx0 - 4, 82), (hx0 + 18, 84)], 0.8), 0.4) - 1.2 * c.blur(c.path([(hx0 - 18, 98), (hx0 + 4, 92), (hx0 + 14, 80)], 0.8), 0.4)
    H = H - 2.0 * c.blur(c.path([(hx0 - 30, 112), (hx0 - 6, 108), (hx0 + 4, 114), (hx0 + 30, 110)], 0.9), 0.4)
    val = c.relief(H, k_h=1.4, amb=0.14, k=0.9) * stone_tex(c, 261, 3, 0.1) * 0.9
    val = val * (1 - 0.3 * np.clip((c.blur(np.clip(H, 0, 20) / 20, 3) - np.clip(H, 0, 20) / 20) * 5, 0, 1))
    c.shade(mask, val, S_, mat=1)
    # sand streaming between the fingers and off the knuckles
    for x0 in (hx0 - 13, hx0 + 1):
        st = c.path([(x0, 70), (x0 + 0.6, 90), (x0 + 0.2, 112)], 1.2, 2.2) * (c.noise(0.8, int(x0)) > 0.3)
        c.shade(st, 0.62 + 0 * X, L.DU_SAND, mat=3, a=0.85)
    dune_front(c, [(0, 108), (24, 104), (52, 110), (70, 114), (100, 112), (128, 106), (160, 110), (192, 104)], 270)
    return make('colossushand', c, 'a colossal weathered stone hand of a statue rising out of a desert dune, palm facing forward, fingers half curled, '
                'the little finger snapped off, cracked sandstone, sand pouring between the fingers', seed=271, denoise=0.45, cn=0.62, mix=0.4, pix=0.55,
                pal=BIG_PAL, mat_pals=BIG_MP, **BIGKW)


def wheel(c, wx, wy, R, spokes=6, broken=False, seed=0, tilt=1.0):
    r = np.sqrt(((c.X - wx) / tilt) ** 2 + (c.Y - wy) ** 2); a = np.arctan2(c.Y - wy, (c.X - wx) / tilt)
    rimm = c.ell(wx, wy, R * tilt, R) - c.ell(wx, wy, (R - 2.2) * tilt, R - 2.2)
    sp = (np.abs(((a / (2 * math.pi) * spokes) % 1) - 0.5) > 0.42) * (r < R - 1.5) * (r > 2.0)
    hub = c.ell(wx, wy, 2.6 * tilt, 2.6)
    m = np.clip(rimm + sp + hub, 0, 1)
    if broken:
        m = m * ~((a > 0.2) & (a < 1.6))
    v = 0.42 + 0.22 * np.cos(a + 2.4) * (rimm > 0.5)
    c.shade(m, v * stone_tex(c, seed, 1.5, 0.1), L.DU_STONE, mat=1)
    return m


def big_wagon():
    """A caravan wagon abandoned to the dune: a plank bed on two spoked wheels (one smashed), its linen hood torn to the hoops."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE; cx = 96.0
    bed = c.poly([(cx - 60, 84), (cx + 52, 82), (cx + 52, 96), (cx - 60, 99)])
    grain = 0.5 + 0.5 * np.sin(c.Y * 3 + 2 * c.noise(4, 281))
    c.shade(bed, (0.36 + 0.06 * grain) * stone_tex(c, 282, 2, 0.08), S_, mat=1)
    c.shade(c.poly([(cx - 60, 84), (cx + 52, 82), (cx + 52, 84.2), (cx - 60, 86.2)]), 0.62 + 0 * c.X, S_, mat=1)
    for x in np.arange(cx - 52, cx + 52, 10.5): c.mulv(c.rect(x, 85, x + 0.6, 98) * bed, 0.65)
    # hoops + hood
    hoops = []
    for k, x in enumerate(np.arange(cx - 52, cx + 50, 17)):
        h = 46 - 8 * math.cos((x - cx) / 60 * math.pi / 2)
        hoops.append((x, h))
    hood = c.poly([(cx - 56, 84), (cx - 55, 58), (cx - 46, 44), (cx - 20, 36), (cx + 16, 37), (cx + 40, 46), (cx + 48, 60), (cx + 48, 83)])
    rip = c.poly([(cx - 6, 36), (cx + 22, 38), (cx + 14, 56), (cx + 4, 66), (cx - 4, 52)])
    cloth = np.clip(hood - rip, 0, 1)
    sag = 0.5 + 0.5 * np.cos((c.X - cx + 52) / 17 * 2 * math.pi)
    vc = (0.4 + 0.16 * sag - 0.2 * np.clip((c.X - cx + 50) / 100, 0, 1) - 0.12 * np.clip((c.Y - 40) / 44, 0, 1)) * stone_tex(c, 283, 2, 0.06)
    c.shade(cloth, vc, L.DU_BONE, mat=7)
    c.tint(cloth * (np.abs(c.Y - 62) < 1.4), hx(L.DU_LAPIS[2]), 0.6)                          # a faded stripe
    c.tint(cloth * (c.noise(5, 284) > 0.7), hx(L.DU_STONE[5]), 0.3)                            # stains
    for x, h in hoops:
        hp = c.path([(x, 84), (x + 1, h + 8), (x + 4, h)], 1.2) * np.clip(rip + (c.X > cx + 46) + (c.X < cx - 54), 0, 1)
        c.shade(hp, 0.3 + 0 * c.X, S_, mat=1)
    c.shade(rip * c.rect(cx - 10, 30, cx + 26, 84), 0.08 + 0 * c.X, S_, mat=1)                # the dark inside through the rip
    for x, h in hoops:
        c.shade(c.path([(x, 66), (x + 2, h + 4), (x + 4, h + 1)], 1.0) * rip, 0.42 + 0 * c.X, S_, mat=1)
    wheel(c, cx - 38, 101, 18, seed=285)
    wheel(c, cx + 32, 102, 18, broken=True, seed=286)
    c.shade(c.path([(cx + 52, 92), (cx + 78, 108)], 2.2), 0.4 + 0 * c.X, S_, mat=1)          # the shaft, dropped
    dune_front(c, [(0, 110), (30, 103), (60, 106), (96, 109), (130, 102), (160, 105), (192, 112)], 287)
    return make('wagon', c, 'an abandoned old caravan wagon half buried in desert sand, plank bed, two big wooden spoked wheels one smashed, torn faded linen hood over wooden hoops',
                seed=291, denoise=0.45, cn=0.62, mix=0.35, pix=0.55, pal=BIG_PAL + pal_of(L.DU_BONE),
                mat_pals={**BIG_MP, 7: pal_of(L.DU_BONE, L.DU_LAPIS[1:3], L.DU_STONE[3:6])}, **BIGKW)


def big_wagon2():
    """An overturned cart half sunk in the sand, one wheel turned to the sky, spilled jars."""
    c = Cv(192, 128, S=6); S_ = L.DU_STONE; cx = 96.0
    box_ = c.poly([(cx - 42, 122), (cx - 38, 94), (cx + 30, 88), (cx + 38, 116)])
    grain = 0.5 + 0.5 * np.sin(c.X * 1.6 + 2 * c.noise(4, 301))
    c.shade(box_, (0.4 - 0.12 * np.clip((c.X - cx + 40) / 80, 0, 1) + 0.05 * grain) * stone_tex(c, 302, 2, 0.08), S_, mat=1)
    for x in np.arange(cx - 34, cx + 32, 9.5): c.mulv(c.path([(x, 120), (x + 3, 92)], 0.6) * box_, 0.65)
    c.shade(c.poly([(cx - 38, 94), (cx + 30, 88), (cx + 30.5, 90.5), (cx - 38, 96.4)]), 0.66 + 0 * c.X, S_, mat=1)
    c.shade(c.path([(cx + 30, 72), (cx + 30, 92)], 2.0), 0.3 + 0 * c.X, S_, mat=1)          # the axle
    wheel(c, cx + 30, 70, 18, seed=303, tilt=0.6)
    for (jx, jy, rw, hh) in [(cx - 60, 116, 6, 15), (cx - 49, 118, 4.4, 10), (cx + 52, 116, 5.2, 13)]:
        clay_jar(c, jx, jy, rw, hh, int(jx), band=True, form='store')
    dune_front(c, [(0, 119), (40, 117), (70, 114), (110, 113), (150, 116), (192, 120)], 305)
    return make('wagon2', c, 'an overturned wooden cart half buried in desert sand, one spoked wheel turned up to the sky, spilled clay jars',
                seed=311, denoise=0.42, cn=0.62, mix=0.3, pix=0.55, pal=BIG_PAL + pal_of(L.DU_CLAY),
                mat_pals={**BIG_MP, 6: pal_of(L.DU_CLAY)}, **BIGKW)


# =============================================================================================== DUNES: du_stele (24x32, 4f)
def du_stele():
    """A round-topped lore stele: the winged sun in the lunette (its disc breathes: 4 frames), rows of glyphs, a worn base."""
    c = Cv(24, 32, S=32); S_ = L.DU_STONE; cx = 12.0
    top = [(cx + 9.5 * math.cos(a), 8.5 - 7.0 * math.sin(a)) for a in np.linspace(0, math.pi, 30)]
    slab = c.poly([(cx + 9.5, 29)] + top + [(cx - 9.5, 29)])
    u = np.clip((c.X - cx + 9.5) / 19, 0, 1)
    c.shade(slab, (0.6 - 0.24 * u) * stone_tex(c, 3, 1.2, 0.08) * (1 - 0.1 * (c.Y - 2) / 27), S_, mat=1)
    c.shade(c.poly([(cx - 9.5, 29), (cx - 10.5, 32), (cx + 10.5, 32), (cx + 9.5, 29)]), 0.42 + 0 * c.X, S_, mat=1)
    c.shade(c.rect(cx - 10.5, 28.6, cx + 10.5, 29.4), 0.72 + 0 * c.X, S_, mat=1)

    def fx(q, a):
        P = L.Px(q, a, [S_, L.DU_FIRE, L.DU_GOLD])
        for k, x0 in enumerate((5, 10, 15)):
            carve_glyphs(P, x0, x0 + 4, 14, 27, 7 + k, gap=1)
        for x in range(4, 20): P.step(x, 12, -2); P.step(x, 13, 1)          # the register line under the lunette
        for sg in (-1, 1):                                                  # wing feathers
            for i in range(2, 8): P.step(12 + sg * i - (1 if sg < 0 else 0), 7, -2); P.step(12 + sg * i - (1 if sg < 0 else 0), 8, -1 if i < 6 else 0)
        return q, a
    f0 = make('du_stele', c, '', mix=0, pal=pal_of(S_, L.DU_FIRE, L.DU_GOLD), mat_pals={1: pal_of(S_)}, fx=fx,
              out_dark='#0d0806', out_lit='#2a1a10', inner=True, rim_col='#f4df9f', rim_k=0.5)
    out = []
    for k, lv in enumerate((0, 2, 3, 1)):          # the disc: dim, brighter, brightest, warm (durations 400/200/400/200)
        a = np.asarray(f0).copy()
        ring = [(11, 6), (12, 6), (11, 9), (12, 9), (10, 7), (10, 8), (13, 7), (13, 8)]
        core = [(11, 7), (12, 7), (11, 8), (12, 8)]
        fire = [hx(c_) for c_ in L.DU_FIRE]
        for (x, y) in ring: a[y, x, :3] = fire[min(4, 1 + lv // 2)]; a[y, x, 3] = 255
        for (x, y) in core: a[y, x, :3] = fire[min(4, 2 + (lv + 1) // 2)]; a[y, x, 3] = 255
        out.append(Image.fromarray(a, 'RGBA'))
    return out


# =============================================================================================== NECROPOLIS
NVKW = dict(out_dark='#06060a', out_lit='#14141e', rim_col='#a8a6bc', rim_k=0.45)
NV_PAL = pal_of(L.NV_STONE, L.NV_BONE, L.NV_GHOST)
NV_MP = {1: pal_of(L.NV_STONE), 7: pal_of(L.NV_BONE, L.NV_STONE[2:5]), 9: pal_of(L.NV_GHOST), 4: pal_of(L.NV_IRON), 11: pal_of(L.NV_WOOD),
         12: pal_of(L.NV_BRONZE), 13: pal_of(L.NV_CLOTH)}
SKULL6 = [".xxxx.", "xxxxxx", "xoxxox", "xxxxxx", ".x.x.x", ".xxxx."]


def nv_stone_tex(c, seed, cell=2.5, k=0.12):
    return stone_tex(c, seed, cell, k)


def skull_px(P, x0, y0, ri=1, base=4, eyes=None, flip=False):
    """A 6x6 skull at 1x (bone ramp index ri in P), lit from the upper left."""
    for j, row in enumerate(SKULL6):
        for i, ch in enumerate(row[::-1] if flip else row):
            x, y = x0 + i, y0 + j
            if ch == 'x':
                lv = base + (1 if (i < 2 and j < 3) else 0) - (1 if (i > 3 or j > 3) else 0)
                P.set(x, y, ri, lv)
            elif ch == 'o':
                if eyes is None: P.set(x, y, ri, 0)
                else: P.set(x, y, eyes[0], eyes[1])


def nv_bell_body(big):
    w, h = (48, 56) if big else (32, 40)
    c = Cv(w, h, S=24 if not big else 18); cx = w / 2
    yoke = 3.0
    # bone yoke + iron crown loops (the hang point is the top centre)
    c.shade(c.rect(cx - (8 if big else 6), 0, cx + (8 if big else 6), 2.4), c.cyl(1.2, 1.3, axis='h', amb=0.3, k=0.8), L.NV_BONE, mat=7)
    for sg in (-1, 1):
        lp = c.ell(cx + sg * 2.2, yoke + 1.6, 1.8, 2.0) - c.ell(cx + sg * 2.2, yoke + 1.6, 0.9, 1.1)
        c.shade(np.clip(lp, 0, 1), 0.5 + 0 * c.X, L.NV_IRON, mat=4)
    top, bot = 5.0, h - 4.5
    Hh = bot - top
    def r(y):
        t = (y - top) / Hh
        if t < 0.06: return w * (0.16 + 0.9 * t)                                     # the crown, rounded
        base = w * (0.21 + 0.03 * t + 0.09 * t ** 3)                                  # waist
        flare = w * 0.2 * max(0, (t - 0.68) / 0.32) ** 1.7                           # the sound bow flares
        return base + flare
    m, v = c.revolve(cx, top, bot, r, amb=0.1, k=0.95)
    # raised bands catch the light, the inscription band between
    t = (c.Y - top) / Hh
    bands = np.zeros_like(c.X)
    for tb in (0.1, 0.62, 0.9):
        bands += np.exp(-((t - tb) / 0.018) ** 2)
    v = v * (1 + 0.35 * bands) * nv_stone_tex(c, 3 + big, 2.5, 0.06)
    u = (c.X - cx) / np.maximum(1, np.interp(c.Y, [top, bot], [r(top), r(bot)]))
    spec = np.exp(-((u + 0.45) / 0.09) ** 2) * (t > 0.08)                      # a metal glint down the lit flank
    v = np.clip(v * 0.62 + 0.38 * spec, 0, 1)
    c.shade(m, v, L.NV_BRONZE, mat=12)
    insc = m * (np.abs(t - 0.36) < 0.05) * (np.sin(c.X * 3.1) > 0.3)
    c.mulv(insc, 0.62)
    # the mouth: a dark ellipse under the lip, cold light inside
    mouth = c.ell(cx, bot - 0.2, r(bot) * 0.92, 1.4)
    c.shade(mouth, 0.08 + 0 * c.X, L.NV_STONE, mat=1)
    # a crack up from the lip on the shadow side
    c.mulv(c.path([(cx + r(bot) * 0.5, bot - 0.5), (cx + r(bot) * 0.42, bot - Hh * 0.18), (cx + r(bot) * 0.48, bot - Hh * 0.3)], 0.5), 0.45)
    im = make('nv_bell_big' if big else 'nv_bell', c, '', mix=0, pal=pal_of(L.NV_BRONZE, L.NV_BONE, L.NV_IRON, L.NV_STONE),
              mat_pals={12: pal_of(L.NV_BRONZE), 7: pal_of(L.NV_BONE), 4: pal_of(L.NV_IRON), 1: pal_of(L.NV_STONE)},
              out_dark='#06060a', out_lit='#14141e', rim_col='#8a87a0', rim_k=0.5)
    return im, bot, r(bot)


def nv_bell_frames(big):
    """7 frames (idle + toll 6): the bell body, the clapper swinging under the lip, a ghost shimmer at the mouth on the strike."""
    body, bot, rb = nv_bell_body(big)
    w, h = body.size; cx = w / 2
    out = []
    swings = [0] + [k * 1.6 for k in (0.9, -0.7, 0.5, -0.3, 0.15, 0)]
    for f, sk in enumerate(swings):
        a = np.asarray(body).copy()
        q, al = a[..., :3].astype(float), a[..., 3] > 0
        P = L.Px(q, al, [L.NV_BONE, L.NV_IRON, L.NV_GHOST])
        clx = int(round(cx - 0.5 + math.sin(sk) * w * 0.18))
        yb = int(bot)
        for y in range(yb - 4, yb + 1): P.set(clx, y, 1, 4)
        if big:
            skull_px(P, clx - 3, yb, 0, 4)
        else:
            for (dx, dy, lv) in [(-1, 1, 5), (0, 1, 5), (1, 1, 4), (-1, 2, 4), (0, 2, 4), (1, 2, 3), (0, 3, 3)]:
                P.set(clx + dx, yb + dy, 0, lv)
        if f in (1, 2):   # the strike: cold sparks along the lip
            rng = np.random.default_rng(f * 7 + big)
            for k in range(3):
                y = yb + 2 - k
                for x in range(int(cx - rb * 0.95), int(cx + rb * 0.95)):
                    if 0 <= y < h and rng.random() < 0.38 - k * 0.1: P.set(x, y, 2, 5 - k)
        out.append(L.to_img(q, al))
    return out


def nv_statue():
    """A hooded mourner-knight in black stone, head bowed, both hands on the pommel of a sword stood point-down; under the
    hood two cold glints (the statue's light sits at y-38)."""
    c = Cv(48, 64, S=16); cx = 24.0
    pl = c.poly([(cx - 10, 64), (cx - 10, 56.5), (cx + 10, 56.5), (cx + 10, 64)])
    c.shade(pl, (0.5 - 0.2 * np.clip((c.X - cx + 10) / 20, 0, 1)) * nv_stone_tex(c, 1), L.NV_STONE, mat=1)
    c.shade(c.rect(cx - 11, 55.2, cx + 11, 57.2), 0.8 + 0 * c.X, L.NV_STONE, mat=1)
    robe = c.poly([(cx - 5.4, 24), (cx + 5.8, 24), (cx + 8.6, 38), (cx + 10.6, 55.4), (cx - 10.4, 55.4), (cx - 8.6, 38)])
    hood = c.poly([(cx - 6.6, 26), (cx - 6.0, 18), (cx - 3.0, 14.2), (cx + 1.0, 13.6), (cx + 4.6, 15.6), (cx + 6.6, 20), (cx + 7.0, 27)])
    fig = np.clip(robe + hood, 0, 1)
    v = c.pillow(fig, 4.5, depth=1.0, amb=0.1, k=0.95)
    folds = 0.5 + 0.5 * np.sin((c.X - cx) * 1.1 + (c.Y - 30) * 0.08)
    v = v * (0.82 + 0.22 * folds * (c.Y > 30))
    c.shade(fig, v * nv_stone_tex(c, 2, 1.6, 0.06), L.NV_STONE, mat=1)
    face = c.ell(cx + 1.0, 22.6, 3.6, 4.4)
    c.shade(face * hood, 0.04 + 0 * c.X, L.NV_STONE, mat=1)
    # the sword: blade down the front, crossguard at the hands, pommel under them
    blade = c.poly([(cx - 0.9, 33.5), (cx + 0.9, 33.5), (cx + 0.7, 53.5), (cx, 55.2), (cx - 0.7, 53.5)])
    c.shade(blade, np.where(c.X < cx, 0.75, 0.45), L.NV_STONE, mat=1)
    c.shade(c.rect(cx - 4.6, 32.0, cx + 4.6, 33.6), 0.62 + 0 * c.X, L.NV_STONE, mat=1)
    hands = c.ell(cx, 30.0, 3.6, 2.6); c.shade(hands, c.pillow(hands, 1.6, amb=0.2, k=0.9) * 0.9, L.NV_STONE, mat=1)
    c.shade(c.ell(cx, 27.2, 1.3, 1.3), 0.7 + 0 * c.X, L.NV_STONE, mat=1)
    # lichen of bone-pale on the lit shoulders
    c.tint(fig * (c.noise(1.2, 5) > 0.7) * (c.Y < 40) * (c.X < cx), hx(L.NV_BONE[2]), 0.4)

    def fx(q, a):
        P = L.Px(q, a, [L.NV_STONE, L.NV_GHOST])
        P.set(24, 22, 1, 5); P.set(27, 22, 1, 4)      # the glints under the hood
        P.set(24, 23, 1, 3)
        return q, a
    return make('nv_statue', c, 'a statue of a hooded mourning knight in black stone, head bowed, hands resting on the pommel of a sword stood point down, gothic tomb statue',
                region='nv', seed=401, denoise=0.38, cn=0.7, mix=0.2, fx=fx, pal=NV_PAL, mat_pals=NV_MP, **NVKW)


def nv_block():
    """The headsman's block (NV5): a scarred oak block with the neck notch, the axe bitten into it, a skull at its foot."""
    c = Cv(48, 64, S=16); cx = 25.0
    W_ = L.NV_WOOD
    front = c.poly([(cx - 13, 64), (cx - 12, 53.6), (cx + 12, 53.6), (cx + 13, 64)])
    grain = 0.5 + 0.5 * np.sin(c.X * 2.6 + 3 * c.noise(2, 3))
    c.shade(front, (0.42 + 0.08 * grain - 0.18 * np.clip((c.X - cx + 13) / 26, 0, 1)) * stone_tex(c, 4, 1.5, 0.08), W_, mat=11)
    topf = c.poly([(cx - 12, 53.8), (cx - 10.6, 51.2), (cx + 13.2, 51.2), (cx + 12, 53.8)])
    c.shade(topf, 0.8 + 0.1 * grain, W_, mat=11)
    notch = c.ell(cx - 1, 52.0, 3.6, 2.2); c.shade(notch * (c.Y < 54.5), 0.18 + 0 * c.X, W_, mat=11)
    for x in (cx - 8, cx + 6): c.mulv(c.path([(x, 54), (x + 1, 61)], 0.4), 0.6)    # cut scars
    # the axe: haft leaning right, broad bearded blade bitten into the top
    c.shade(c.path([(cx + 6.6, 42.6), (cx + 17, 23)], 1.7, 1.3), 0.5 + 0 * c.X, W_, mat=11)
    # a bearded axe head: the cheek against the haft, the long crescent edge sunk in the wood at its lower end
    blade = c.poly([(cx + 7.0, 40.6), (cx + 9.4, 39.0), (cx + 8.6, 44.6), (cx + 3.0, 50.4), (cx - 3.4, 52.4), (cx - 1.0, 47.6), (cx + 2.4, 43.0), (cx + 4.0, 38.4)])
    c.shade(blade, (0.74 - 0.03 * (c.X - cx)) * nv_stone_tex(c, 6, 1, 0.08), L.NV_IRON, mat=4)
    c.shade(c.path([(cx - 3.0, 51.8), (cx + 0.4, 46.6), (cx + 3.6, 42.4)], 0.7), 0.98 + 0 * c.X, L.NV_IRON, mat=4)
    c.shade(c.rect(cx - 13.6, 60.5, cx + 13.6, 64), 0.0 * c.X, L.NV_STONE, mat=1, a=0.0)
    sk = c.ell(cx + 17.5, 61.0, 3.4, 3.0)
    c.shade(sk, c.pillow(sk, 1.8, amb=0.25, k=0.85), L.NV_BONE, mat=7)

    def fx(q, a):
        P = L.Px(q, a, [L.NV_BONE, L.NV_STONE])
        for (x, y) in [(41, 60), (43, 60), (42, 62)]: P.set(x, y, 0, 0)
        return q, a
    return make('nv_block', c, "an executioner's chopping block of scarred black oak with a neck notch, a heavy bearded axe buried in it, a skull at its foot",
                region='nv', seed=411, denoise=0.38, cn=0.7, mix=0.2, fx=fx, pal=pal_of(L.NV_WOOD, L.NV_IRON, L.NV_BONE, L.NV_STONE), mat_pals=NV_MP, **NVKW)


def nv_gallows():
    """A gibbet: a weathered post and arm with a brace, a chain, an iron cage of bones turning on it."""
    c = Cv(48, 64, S=16); W_ = L.NV_WOOD
    post = c.rect(6.0, 2.0, 9.4, 64)
    c.shade(post, c.cyl(7.7, 1.7, amb=0.15, k=0.85) * 0.7 * stone_tex(c, 1, 1.5, 0.1), W_, mat=11)
    arm = c.rect(5.0, 1.6, 40.0, 4.6)
    c.shade(arm, c.cyl(3.1, 1.5, axis='h', amb=0.15, k=0.85) * 0.7 * stone_tex(c, 2, 1.5, 0.1), W_, mat=11)
    brace = c.path([(8.4, 15), (19.0, 4.2)], 1.8)
    c.shade(brace, 0.42 + 0 * c.X, W_, mat=11)
    c.shade(c.rect(4.4, 59, 11.0, 64), 0.45 + 0 * c.X, L.NV_STONE, mat=1)
    # chain (links alternate light/dark at 1x below), cage
    cx = 33.0
    c.shade(c.rect(cx - 0.6, 4.6, cx + 0.6, 18), 0.45 + 0 * c.X, L.NV_IRON, mat=4)
    cg, cv_ = c.revolve(cx, 18, 44, lambda y: 1.5 + 7.4 * math.sin(min(1.0, (y - 18) / 22) * math.pi * 0.62) if y < 40 else 7.6 - (y - 40) * 1.1, amb=0.2, k=0.85)
    bars = cg * ((np.abs(((c.X - cx) / 2.6) % 1 - 0.5) > 0.32) | (np.abs(c.Y - 30) < 0.6) | (c.Y > 41.8) | (c.Y < 19.6))
    inside = cg * (1 - bars)
    c.shade(inside * c.ell(cx - 0.5, 34, 4.2, 6.0), c.pillow(c.ell(cx - 0.5, 34, 4.2, 6.0), 1.6, amb=0.2, k=0.8) * 0.75, L.NV_BONE, mat=7)   # the bones
    c.shade(bars, cv_ * 0.62, L.NV_IRON, mat=4)

    def fx(q, a):
        P = L.Px(q, a, [L.NV_IRON, L.NV_BONE])
        for y in range(5, 18):
            P.set(33, y, 0, 4 if y % 2 else 2)
        skull_px(P, 30, 25, 1, 4)
        return q, a
    return make('nv_gallows', c, 'a weathered wooden gibbet post and arm with a brace, an iron chain, a hanging iron cage with bones and a skull',
                region='nv', seed=421, denoise=0.36, cn=0.7, mix=0.15, fx=fx, pal=pal_of(L.NV_WOOD, L.NV_IRON, L.NV_BONE, L.NV_STONE), mat_pals=NV_MP, **NVKW)


def nv_throne():
    """King Vael's throne (NV7): a tall gothic seat of black stone, its pointed back crowned with bone spires, a skull in the
    pediment, violet cushion, armrests ending in skulls (light at y-50)."""
    c = Cv(48, 64, S=16); cx = 24.0
    back = c.poly([(cx - 11, 42), (cx - 11, 14), (cx - 7, 8), (cx - 3.2, 3.6), (cx, 0.4), (cx + 3.2, 3.6), (cx + 7, 8), (cx + 11, 14), (cx + 11, 42)])
    c.shade(back, (0.46 - 0.2 * np.clip((c.X - cx + 11) / 22, 0, 1)) * nv_stone_tex(c, 1), L.NV_STONE, mat=1)
    panel = c.poly([(cx - 7, 40), (cx - 7, 17), (cx, 7.6), (cx + 7, 17), (cx + 7, 40)])
    c.shade(panel, (0.24 - 0.08 * np.clip((c.X - cx + 7) / 14, 0, 1)) * nv_stone_tex(c, 2), L.NV_STONE, mat=1)
    for sg in (-1, 1):   # spires
        sp = c.poly([(cx + sg * 11.8, 16), (cx + sg * 10.4, 4), (cx + sg * 9.0, 16)])
        c.shade(sp, (0.82 if sg < 0 else 0.55) + 0 * c.X, L.NV_BONE, mat=7)
        rib = c.path([(cx + sg * 9.5, 40), (cx + sg * 9.5, 15)], 1.2)
        c.shade(rib, (0.7 if sg < 0 else 0.42) + 0 * c.X, L.NV_BONE, mat=7)
    seat = c.poly([(cx - 13, 47), (cx - 12, 41.4), (cx + 12, 41.4), (cx + 13, 47)])
    c.shade(seat, np.where(c.Y < 43, 0.58, 0.36) * nv_stone_tex(c, 3), L.NV_CLOTH, mat=13)
    base = c.poly([(cx - 13.5, 64), (cx - 13, 47), (cx + 13, 47), (cx + 13.5, 64)])
    c.shade(base, (0.42 - 0.18 * np.clip((c.X - cx + 13) / 26, 0, 1)) * nv_stone_tex(c, 4), L.NV_STONE, mat=1)
    c.shade(c.rect(cx - 15, 60.5, cx + 15, 64), 0.55 + 0 * c.X, L.NV_STONE, mat=1)
    for sg in (-1, 1):
        armr = c.poly([(cx + sg * 11, 36), (cx + sg * 16.5, 35.4), (cx + sg * 16.5, 47.5), (cx + sg * 11, 47.5)])
        c.shade(armr, (0.55 if sg < 0 else 0.32) + 0 * c.X, L.NV_STONE, mat=1)
        sk = c.ell(cx + sg * 14.2, 33.2, 2.8, 2.6); c.shade(sk, c.pillow(sk, 1.6, amb=0.25, k=0.85) * 0.95, L.NV_BONE, mat=7)

    def fx(q, a):
        P = L.Px(q, a, [L.NV_BONE, L.NV_GHOST, L.NV_STONE])
        skull_px(P, 21, 15, 0, 4, eyes=(1, 4))
        for y in range(24, 40, 3):
            for x in (22, 25): P.step(x, y, -1) if False else None
        return q, a
    return make('nv_throne', c, 'a tall gothic throne of black stone with bone spires, a pointed back with a skull in the pediment, violet cushion, skull armrests',
                region='nv', seed=431, denoise=0.38, cn=0.7, mix=0.2, fx=fx, pal=pal_of(L.NV_STONE, L.NV_BONE, L.NV_CLOTH, L.NV_GHOST), mat_pals=NV_MP, **NVKW)


def nv_headstone(var, f):
    """var 0: a cracked cross-topped slab. var 1: a rounded slab with a skull relief and a ghost-candle (flame per frame,
    light at x+9, y-9)."""
    c = Cv(48, 64, S=16); cx = 24.0
    if var == 0:
        slab = c.poly([(cx - 7.5, 64), (cx - 7.5, 41), (cx - 6, 37.8), (cx, 36.6), (cx + 6, 37.8), (cx + 7.5, 41), (cx + 7.5, 64)])
        c.shade(slab, (0.5 - 0.24 * np.clip((c.X - cx + 7.5) / 15, 0, 1) - 0.08 * (c.Y - 37) / 27) * nv_stone_tex(c, 1), L.NV_STONE, mat=1)
        cross = np.clip(c.poly([(cx - 1.3, 37.5), (cx - 1.3, 29.6), (cx - 5.6, 30.4), (cx - 6.6, 29.0), (cx - 5.6, 27.6), (cx - 1.3, 28.2), (cx - 1.3, 23.6),
                                (cx - 2.0, 22.4), (cx, 20.8), (cx + 2.0, 22.4), (cx + 1.3, 23.6), (cx + 1.3, 28.2), (cx + 5.6, 27.6), (cx + 6.6, 29.0), (cx + 5.6, 30.4), (cx + 1.3, 29.6), (cx + 1.3, 37.5)]), 0, 1)
        c.shade(cross, np.where(c.X < cx - 0.2, 0.66, 0.4) * nv_stone_tex(c, 2), L.NV_STONE, mat=1)
        c.shade(cross * (c.Y < 29.1) * (np.abs(c.X - cx) > 1.4), 0.7 + 0 * c.X, L.NV_STONE, mat=1)
        c.mulv(c.path([(cx + 3.4, 40), (cx + 1.6, 46), (cx + 3.2, 51), (cx + 1.8, 56)], 0.5), 0.5)       # the crack
        c.tint(slab * (c.noise(1.0, 3) > 0.7) * (c.X < cx), hx(L.NV_BONE[2]), 0.35)                    # pale lichen
        c.shade(c.rect(cx - 9, 61.5, cx + 9, 64), 0.4 + 0 * c.X, L.NV_STONE, mat=1)
    else:
        top = [(cx + 8.5 * math.cos(a), 46 - 10 * math.sin(a)) for a in np.linspace(0, math.pi, 30)]
        slab = c.poly([(cx + 8.5, 64)] + top + [(cx - 8.5, 64)])
        c.shade(slab, (0.48 - 0.24 * np.clip((c.X - cx + 8.5) / 17, 0, 1) - 0.06 * (c.Y - 36) / 28) * nv_stone_tex(c, 4), L.NV_STONE, mat=1)
        c.mulv(c.rect(cx - 6, 53.6, cx + 6, 54.4), 0.55)
        c.shade(c.rect(cx - 10, 61.5, cx + 10, 64), 0.4 + 0 * c.X, L.NV_STONE, mat=1)
        cand = c.rect(cx + 8.8, 57.4, cx + 10.6, 64)
        c.shade(cand, np.where(c.X < cx + 9.6, 0.85, 0.55), L.NV_BONE, mat=7)
        c.shade(c.ell(cx + 9.7, 63.4, 2.6, 0.9), 0.5 + 0 * c.X, L.NV_BONE, mat=7)     # wax pooled

    def fx(q, a):
        P = L.Px(q, a, [L.NV_BONE, L.NV_GHOST, L.NV_STONE])
        if var == 0:
            for k, (x, y) in enumerate([(21, 45), (23, 45), (25, 45), (21, 48), (24, 48), (22, 51), (25, 51)]): P.step(x, y, -2)
        else:
            skull_px(P, 21, 42, 0, 3)
            for x in range(19, 29): P.step(x, 50, -2)
        return q, a
    im = make(f'headstone{var}', c, '', region='nv', mix=0, fx=fx, pal=pal_of(L.NV_STONE, L.NV_BONE, L.NV_GHOST), mat_pals=NV_MP, **NVKW)
    return im


def nv_headstones(var):
    base = nv_headstone(var, 0)
    out = []
    for f in range(4):
        a = np.asarray(base).copy(); q = a[..., :3].astype(float); al = a[..., 3] > 0
        P = L.Px(q, al, [L.NV_BONE, L.NV_GHOST, L.NV_STONE])
        if var == 1:    # the ghost flame: 3-5 px, licking
            fx_, fy = 33 + (1 if f == 2 else 0), 56
            hgt = [3, 4, 5, 4][f]
            for j in range(hgt):
                P.set(fx_ - (1 if (j == hgt - 1 and f % 2) else 0), fy - j, 1, 6 - min(3, j) - (0 if j else 0))
            P.set(fx_ + 1, fy - 1, 1, 3); P.set(fx_ - 1, fy, 1, 2)
        else:           # a mote of grave-light drifting up past the cross
            y = 34 - f * 3
            P.set(30, y, 1, 4 if f % 2 else 5); P.set(30, y + 1, 1, 2)
        out.append(L.to_img(q, al))
    return out


def nv_dummy():
    """A training pell for the dead watch: a post, a straw-stuffed sackcloth body roped tight, a dented iron helm, a crossbar,
    a notched blade still stuck in its shoulder."""
    c = Cv(48, 64, S=16); cx = 24.0; W_ = L.NV_WOOD
    c.shade(c.rect(cx - 1.4, 18, cx + 1.4, 64), c.cyl(cx, 1.4, amb=0.18, k=0.8) * 0.7, W_, mat=11)
    c.shade(c.rect(cx - 12, 29.6, cx + 12, 32.0), c.cyl(30.8, 1.2, axis='h', amb=0.2, k=0.8) * 0.65, W_, mat=11)
    body, bv = c.revolve(cx, 27.5, 51, lambda y: 7.2 - 1.4 * ((y - 39) / 12) ** 2, amb=0.15, k=0.85)
    c.shade(body, bv * 0.9 * stone_tex(c, 3, 1.0, 0.12), L.NV_BONE[:5], mat=7)
    for y in (33.0, 39.0, 45.5):
        c.mulv(c.rect(cx - 8, y, cx + 8, y + 1.0) * body, 0.55)
    helm, hv = c.revolve(cx, 14.0, 27.6, lambda y: 5.6 * math.sin(min(1, (y - 14) / 8) * math.pi / 2) + (0.6 if y > 25 else 0), amb=0.12, k=0.95)
    c.shade(helm, hv * 0.85, L.NV_IRON, mat=4)
    c.mulv(c.rect(cx - 4.8, 20.0, cx + 4.8, 21.0) * helm, 0.2)          # the eye slit
    c.mulv(c.ell(cx - 2.6, 17.0, 1.4, 1.0) * helm, 0.7)                 # a dent
    c.shade(c.path([(cx + 6.5, 31), (cx + 16, 42.5)], 1.4, 0.9), 0.72 + 0 * c.X, L.NV_IRON, mat=4)
    c.shade(c.rect(cx - 5, 60.5, cx + 5, 64), 0.4 + 0 * c.X, L.NV_STONE, mat=1)
    return make('nv_dummy', c, 'a training dummy pell, wooden post with a crossbar, straw stuffed sackcloth body bound with rope, dented iron great helm, a sword stuck in its shoulder',
                region='nv', seed=441, denoise=0.36, cn=0.7, mix=0.18, pal=pal_of(L.NV_WOOD, L.NV_BONE, L.NV_IRON, L.NV_STONE), mat_pals=NV_MP, **NVKW)


def nv_bunk():
    """A barracks cot of the dead watch: a plank bed on stubby legs, a grey blanket thrown back, a skull for a pillow."""
    c = Cv(48, 64, S=16); W_ = L.NV_WOOD
    frame = c.rect(2, 53.6, 46, 57.4)
    c.shade(frame, np.where(c.Y < 54.6, 0.62, 0.36) * stone_tex(c, 1, 1.5, 0.1), W_, mat=11)
    for x in (2.6, 43.6):
        c.shade(c.rect(x, 46.0, x + 1.8, 64), c.cyl(x + 0.9, 0.9, amb=0.2, k=0.8) * 0.6, W_, mat=11)
    for x in (12, 32): c.shade(c.rect(x, 57.4, x + 1.6, 64), 0.3 + 0 * c.X, W_, mat=11)
    blanket = c.poly([(4.5, 54), (5, 50.8), (14, 49.4), (24, 50.6), (30, 49.2), (34, 51.6), (34.6, 54)])
    folds = 0.5 + 0.5 * np.sin(c.X * 0.9)
    c.shade(blanket, (0.42 + 0.14 * folds) * stone_tex(c, 2, 1, 0.08), L.NV_STONE[2:9], mat=1)
    c.shade(c.poly([(4.5, 54), (4.0, 58.6), (8, 59.6), (9, 54)]), 0.3 + 0 * c.X, L.NV_STONE[2:9], mat=1)   # hanging over the edge

    def fx(q, a):
        P = L.Px(q, a, [L.NV_BONE])
        skull_px(P, 36, 46, 0, 4)
        return q, a
    return make('nv_bunk', c, '', region='nv', mix=0, fx=fx, pal=pal_of(L.NV_WOOD, L.NV_STONE, L.NV_BONE), mat_pals=NV_MP, **NVKW)


def nv_drum():
    """A funeral drum: a tall shell bound with zig-zag rope, a pale skin head, two femur sticks crossed on top."""
    c = Cv(48, 64, S=16); cx = 24.0; W_ = L.NV_WOOD
    shell, sv = c.revolve(cx, 42.0, 62.0, lambda y: 11.6 - 0.8 * abs(y - 52) / 10, amb=0.12, k=0.9)
    c.shade(shell, sv * 0.8 * stone_tex(c, 1, 1.2, 0.06), W_, mat=11)
    head = c.ell(cx, 42.0, 11.8, 2.4); c.shade(head, 0.62 + 0.15 * (c.X < cx), L.NV_BONE, mat=7)
    for y in (43.6, 60.6):
        c.shade(c.rect(cx - 12, y, cx + 12, y + 1.4) * shell, np.where(c.X < cx, 0.6, 0.3), L.NV_BONE[:5], mat=7)
    zz = shell * (np.abs(((c.Y - 45) / 15 * 1.6 + (c.X - cx) / 6.0) % 2 - 1) < 0.1) * (c.Y > 45) * (c.Y < 60.5)
    zz2 = shell * (np.abs(((c.Y - 45) / 15 * 1.6 - (c.X - cx) / 6.0) % 2 - 1) < 0.1) * (c.Y > 45) * (c.Y < 60.5)
    c.shade(np.clip(zz + zz2, 0, 1), sv * 0.75 + 0.1, L.NV_BONE[:5], mat=7)
    c.shade(c.rect(cx - 9, 62, cx - 6, 64) + c.rect(cx + 6, 62, cx + 9, 64), 0.3 + 0 * c.X, W_, mat=11)
    for sg in (-1, 1):   # two femurs crossed, leaning up out of the head
        a0 = (cx + sg * 3, 41.0); a1 = (cx - sg * 9, 24.0)
        c.shade(c.path([a0, a1], 1.8, 1.4), (0.75 if sg > 0 else 0.55) + 0 * c.X, L.NV_BONE, mat=7)
        for e in (a1,):
            c.shade(c.ell(e[0] - 0.9, e[1], 1.5, 1.4) + c.ell(e[0] + 0.9, e[1] + 0.4, 1.5, 1.4), 0.8 + 0 * c.X, L.NV_BONE, mat=7)
    return make('nv_drum', c, 'a tall funeral drum with a wooden shell bound in zig zag rope, a pale skin drumhead, two femur bones crossed as drumsticks',
                region='nv', seed=451, denoise=0.36, cn=0.7, mix=0.18, pal=pal_of(L.NV_WOOD, L.NV_BONE, L.NV_STONE), mat_pals=NV_MP, **NVKW)


def nv_kingskull(var):
    """A crowned skull on a small stone pedestal. var 0: the crown whole, tarnished gold (warm light); var 1: the crown
    broken, cold ghost-light in the sockets."""
    c = Cv(48, 64, S=16); cx = 24.0
    ped = c.poly([(cx - 7.5, 64), (cx - 6.5, 53.4), (cx + 6.5, 53.4), (cx + 7.5, 64)])
    c.shade(ped, (0.5 - 0.22 * np.clip((c.X - cx + 7.5) / 15, 0, 1)) * nv_stone_tex(c, 1), L.NV_STONE, mat=1)
    c.shade(c.rect(cx - 8.6, 51.6, cx + 8.6, 53.8), 0.78 + 0 * c.X, L.NV_STONE, mat=1)
    cush = c.ell(cx, 51.0, 7.6, 1.8); c.shade(cush, 0.5 + 0.15 * (c.X < cx), L.NV_CLOTH, mat=13)
    sk = c.ell(cx, 45.8, 4.6, 4.4)
    c.shade(sk, c.pillow(sk, 2.4, amb=0.14, k=0.85) * 0.78, L.NV_BONE, mat=7)
    jaw = c.poly([(cx - 3.0, 48.8), (cx + 3.0, 48.8), (cx + 2.4, 51.6), (cx - 2.4, 51.6)]); c.shade(jaw, 0.42 + 0 * c.X, L.NV_BONE, mat=7)
    crown = c.poly([(cx - 4.8, 42.6), (cx - 5.4, 37.0), (cx - 3.4, 39.6), (cx - 1.7, 36.0), (cx, 39.0), (cx + 1.7, 36.0), (cx + 3.4, 39.6), (cx + 5.4, 37.0), (cx + 4.8, 42.6)])
    if var == 1:
        crown = crown * ~((c.X > cx + 1.2) & (c.Y < 40.4))
    c.shade(crown, np.where(c.X < cx, 0.62, 0.38) * stone_tex(c, 3, 0.8, 0.08), L.DU_GOLD[:5], mat=2)

    def fx(q, a):
        P = L.Px(q, a, [L.NV_BONE, L.NV_GHOST, L.DU_GOLD])
        for (x, y) in [(21, 45), (22, 45), (21, 46), (22, 46), (25, 45), (26, 45), (25, 46), (26, 46)]:   # deep sockets
            if var: P.set(x, y, 1, 5 if (x, y) in ((21, 45), (25, 45)) else 2)
            else: P.set(x, y, 0, 0)
        P.set(23, 48, 0, 0); P.set(24, 48, 0, 0)                 # nasal cavity
        for x in range(21, 27): P.set(x, 50, 0, 1 if x % 2 else 3)   # teeth
        P.set(20, 41, 2, 4); P.set(27, 41, 2, 3)                # crown gems
        return q, a
    return make(f'kingskull{var}', c, '', region='nv', mix=0, fx=fx, pal=pal_of(L.NV_STONE, L.NV_BONE, L.NV_CLOTH, L.DU_GOLD[:5], L.NV_GHOST),
                mat_pals={**NV_MP, 2: pal_of(L.DU_GOLD[:5])}, **NVKW)


def big_dirgeslab():
    """The dirge (NV12): a tall pointed stela, five staff lines for the five bells (lowest line = the lowest-hanging bell) and
    the six bell-notes of the dirge in ghost-light (same lines and order as v1: 0 2 1 4 3 0), mourners filing under it."""
    c = Cv(192, 128, S=6); x0, x1, y0, y1 = 60, 131, 44, 128
    cx = (x0 + x1) / 2
    body = c.poly([(x0, y1), (x0, y0), (x0 - 2.5, y0 - 0.5), (cx, y0 - 13), (x1 + 2.5, y0 - 0.5), (x1, y0), (x1, y1)])
    u = np.clip((c.X - x0) / (x1 - x0), 0, 1)
    c.shade(body, (0.42 - 0.16 * u - 0.08 * (c.Y - y0) / (y1 - y0)) * nv_stone_tex(c, 501, 3, 0.1) * stone_tex(c, 502, 1, 0.05), L.NV_STONE, mat=1)
    c.shade(c.poly([(x0 - 2.5, y0 - 0.5), (cx, y0 - 13), (cx, y0 - 11.4), (x0 - 0.5, y0 + 0.8)]), 0.7 + 0 * c.X, L.NV_STONE, mat=1)   # lit raking edge
    c.mulv(c.rect(x0 + 3, y0 + 3, x1 - 3, y0 + 3.8), 0.55)
    c.mulv(c.rect(x0 + 3, 62, x1 - 3, 102), 0.82)                              # the sunk field of the stave
    # a bell carved in the pediment
    bell = c.poly([(cx - 1.2, 33.5), (cx + 1.2, 33.5), (cx + 5, 42.5), (cx - 5, 42.5)])
    c.shade(bell, np.where(c.X < cx, 0.62, 0.42), L.NV_BONE, mat=7)
    for i in range(6):   # mourners under the stave, in low relief
        mx = x0 + 10 + i * 10
        fig = np.clip(c.poly([(mx - 2.4, 108), (mx + 2.4, 108), (mx + 3.4, 119), (mx - 3.4, 119)]) + c.ell(mx, 106, 2.0, 2.4), 0, 1)
        c.mulv(fig, 0.72); c.mulv(np.clip(c.blur(fig, 0.4) - fig, 0, 1) * (c.X > mx), 1.5)
    lines = [98, 91, 84, 77, 70]
    notes = [0, 2, 1, 4, 3, 0]

    def fx(q, a):
        P = L.Px(q, a, [L.NV_STONE, L.NV_BONE, L.NV_GHOST])
        for ly in lines:
            for x in range(x0 + 7, x1 - 6):
                P.set(x, ly, 1, 3 if x % 7 else 2)
                P.step(x, ly + 1, -1)
        for i, n in enumerate(notes):
            nx, ny = x0 + 14 + i * 9, lines[n]
            for (dx, dy, lv) in [(0, -4, 5), (-1, -3, 5), (0, -3, 6), (1, -3, 4), (-1, -2, 4), (0, -2, 5), (1, -2, 4), (-2, -1, 3), (-1, -1, 4), (0, -1, 5),
                                 (1, -1, 4), (2, -1, 3), (-2, 0, 3), (-1, 0, 4), (0, 0, 4), (1, 0, 3), (2, 0, 2), (0, 1, 6)]:
                P.set(nx + dx, ny + dy, 2, lv)
        return q, a
    return make('dirgeslab', c, 'a tall gothic stone stela with a pointed top, a carved bell in the pediment, a sunk panel with musical staff lines, a procession of hooded mourners carved below',
                region='nv', seed=511, denoise=0.42, cn=0.65, mix=0.3, pix=0.55, fx=fx, pal=NV_PAL, mat_pals=NV_MP,
                out_dark='#06060a', out_lit='#14141e', inner=True, rim_col='#a8a6bc', rim_k=0.4)


def big_gateleaves():
    """The Cemetery Gate's leaves (NV8): two wrought-iron leaves thrown open against the gatehouse walls, spear-headed bars,
    scrolled crestings, one leaf sagging off a broken hinge."""
    c = Cv(192, 128, S=6); I_ = L.NV_IRON
    for sg in (-1, 1):
        xo = 96 + sg * 91            # the hinge stile at the wall
        xi = 96 + sg * 52            # the leaf's free edge
        sag = 0 if sg < 0 else 4.0
        def yt(x):                    # top rail, the free end sagging on the right leaf
            return 66 + sag * abs(x - xo) / abs(xi - xo)
        bars = np.zeros_like(c.X)
        xs = np.linspace(min(xo, xi), max(xo, xi), 9)
        for x in xs:
            bars = np.maximum(bars, c.rect(x - 0.7, yt(x), x + 0.7, 127))
            spear = c.poly([(x - 1.6, yt(x) + 0.5), (x, yt(x) - 5.5), (x + 1.6, yt(x) + 0.5)])
            bars = np.maximum(bars, spear)
        for y0 in (71, 96, 122):
            bars = np.maximum(bars, c.path([(xo, y0), (xi, y0 + sag * (y0 / 128))], 1.6))
        # a scroll cresting on the top rail of each leaf
        for k in range(len(xs) - 1):
            mx = (xs[k] + xs[k + 1]) / 2
            sc = np.clip(c.ell(mx, yt(mx) + 4.0, 2.4, 2.4) - c.ell(mx, yt(mx) + 4.0, 1.5, 1.5), 0, 1)
            bars = np.maximum(bars, sc)
        bars = np.maximum(bars, c.rect(xo - 1.4 * sg - 1.4, 60, xo - 1.4 * sg + 1.4, 128))     # the hinge stile
        v = (0.42 if sg < 0 else 0.3) + 0.25 * np.clip(-(c.X - xo) * sg / 40, 0, 1) * 0
        c.shade(bars, v * stone_tex(c, 520 + sg, 1.2, 0.15), I_, mat=4)
        c.tint(bars * (c.noise(1.0, 530 + sg) > 0.72), hx(L.NV_BRONZE[4]), 0.45)                 # rust blooms (tarnish)
    return make('gateleaves', c, 'two tall wrought iron cemetery gate leaves thrown open, spear headed bars, scroll crestings, rusted, one sagging off a broken hinge',
                region='nv', seed=541, denoise=0.36, cn=0.7, mix=0.15, pix=0.55, pal=pal_of(L.NV_IRON, L.NV_BRONZE[3:6]), mat_pals={4: pal_of(L.NV_IRON, L.NV_BRONZE[3:6])},
                out_dark='#06060a', out_lit='#10121a', thresh=0.4)


def du_reeds_recolour(tag):
    """The reeds were acceptable in form but neon green beside the new palms: same pixels, mapped by value onto DU_LEAF
    (papyrus heads) and DU_STONE (dry maces)."""
    old, j = L.old_frames('xsb_du'); a0, b0 = L.tag_range(j, tag)
    leaf = np.array([hx(c_) for c_ in L.DU_LEAF]); out = []
    for im in old[a0:b0 + 1]:
        a = np.asarray(im).astype(float).copy(); al = a[..., 3] > 0
        lum = (a[..., :3] * [0.299, 0.587, 0.114]).sum(-1)
        green = (a[..., 1] > a[..., 0] + 6) & al
        lo, hi = np.percentile(lum[al], 3), np.percentile(lum[al], 97)
        t = np.clip((lum - lo) / max(1, hi - lo), 0, 1)
        idx = np.clip(np.round(t * (len(leaf) - 1)), 0, len(leaf) - 1).astype(int)
        a[..., :3] = np.where(green[..., None], leaf[idx], a[..., :3])
        out.append(Image.fromarray(a.astype(np.uint8), 'RGBA'))
    return out


# =============================================================================================== registry
TARGETS = {
    'obelisk': ('xsb_tall', 'obelisk', lambda: [tall_obelisk()]),
    'ruincol': ('xsb_tall', 'ruincol', lambda: [tall_ruincol(0)]),
    'ruincol1': ('xsb_tall', 'ruincol1', lambda: [tall_ruincol(1)]),
    'statue_du': ('xsb_du', 'statue_du', lambda: [du_statue()]),
    'sunspire': ('xsb_big', 'sunspire', lambda: [big_sunspire()]),
    'ruinarch': ('xsb_big', 'ruinarch', lambda: [big_ruinarch()]),
    'colossus': ('du_colossus', 'idle', lambda: [colossus()]),
    'jars': ('xsb_du', 'jars', lambda: [du_jars(0)]),
    'reeds': ('xsb_du', 'reeds', lambda: du_reeds_recolour('reeds')),
    'reeds1': ('xsb_du', 'reeds1', lambda: du_reeds_recolour('reeds1')),
    'reeds2': ('xsb_du', 'reeds2', lambda: du_reeds_recolour('reeds2')),
    'jars1': ('xsb_du', 'jars1', lambda: [du_jars(1)]),
    'crates': ('xsb_du', 'crates', lambda: [du_crates()]),
    'banner_du': ('xsb_du', 'banner_du', du_banner),
    'scarabidol': ('xsb_du', 'scarabidol', lambda: [du_scarabidol()]),
    'hoard': ('xsb_du', 'hoard', lambda: [du_hoard()]),
    'sarcophagus': ('xsb_du', 'sarcophagus', lambda: [du_sarcophagus(0)]),
    'sarcophagus1': ('xsb_du', 'sarcophagus1', lambda: [du_sarcophagus(1)]),
    'brazier_du': ('xsb_du', 'brazier_du', du_brazier),
    'palm': ('xsb_tall', 'palm', lambda: tall_palm(0)),
    'palm1': ('xsb_tall', 'palm1', lambda: tall_palm(1)),
    'palm2': ('xsb_tall', 'palm2', lambda: tall_palm(2)),
    'palmdead': ('xsb_tall', 'palmdead', lambda: [tall_palmdead()]),
    'sealdoor': ('xsb_big', 'sealdoor', lambda: [big_sealdoor()]),
    'sundial': ('xsb_big', 'sundial', lambda: [big_sundial()]),
    'titles': ('xsb_big', 'titles', lambda: [big_titles()]),
    'colossushand': ('xsb_big', 'colossushand', lambda: [big_hand()]),
    'wagon': ('xsb_big', 'wagon', lambda: [big_wagon()]),
    'wagon2': ('xsb_big', 'wagon2', lambda: [big_wagon2()]),
    'du_stele': ('du_stele', 'idle', du_stele),
    'nv_bell': ('nv_bell', 'all', lambda: nv_bell_frames(False)),
    'nv_bell_big': ('nv_bell_big', 'all', lambda: nv_bell_frames(True)),
    'nv_statue': ('nv_props', 'statue', lambda: [nv_statue()]),
    'nv_block': ('nv_props', 'block', lambda: [nv_block()]),
    'nv_gallows': ('nv_props', 'gallows', lambda: [nv_gallows()]),
    'nv_throne': ('nv_props', 'throne', lambda: [nv_throne()]),
    'headstone': ('xsb_nv', 'headstone', lambda: nv_headstones(0)),
    'headstone1': ('xsb_nv', 'headstone1', lambda: nv_headstones(1)),
    'dummy': ('xsb_nv', 'dummy', lambda: [nv_dummy()]),
    'bunk': ('xsb_nv', 'bunk', lambda: [nv_bunk()]),
    'drum': ('xsb_nv', 'drum', lambda: [nv_drum()]),
    'kingskull': ('xsb_nv', 'kingskull', lambda: [nv_kingskull(0)]),
    'kingskull1': ('xsb_nv', 'kingskull1', lambda: [nv_kingskull(1)]),
    'dirgeslab': ('xsb_big', 'dirgeslab', lambda: [big_dirgeslab()]),
    'gateleaves': ('xsb_big', 'gateleaves', lambda: [big_gateleaves()]),
}


def contact_sheets(out_dir, sheets=None, scale=3):
    """Before/after contact sheets per sheet: v1 frames (left) next to the current assets/ frames, the player at the same scale."""
    import json as _j
    os.makedirs(out_dir, exist_ok=True)
    by = {}
    for k, (sh, tag, fn) in TARGETS.items():
        if sheets and sh not in sheets: continue
        by.setdefault(sh, []).append(tag)
    for sh, tags in by.items():
        old, j = L.old_frames(sh)
        nj = _j.load(open(os.path.join(L.ROOT, 'assets', sh + '.json'))); nim = Image.open(os.path.join(L.ROOT, 'assets', sh + '.png')).convert('RGBA')
        new = [nim.crop((f['frame']['x'], f['frame']['y'], f['frame']['x'] + f['frame']['w'], f['frame']['y'] + f['frame']['h'])) for f in nj['frames']]
        rows = []
        for t in tags:
            a, b = L.tag_range(j, t); n = min(4, b - a + 1)
            rows.append((f'{sh}/{t}  before | after  ({b - a + 1}f)', old[a:a + n] + [Image.new('RGBA', (6, old[0].height))] + new[a:a + n]))
        sc = 2 if old[0].width >= 150 else scale
        print('contact', sh, L.contact(rows, os.path.join(out_dir, f'contact_{sh}.png'), scale=sc))


def main():
    if '--contact' in ARGS:
        return contact_sheets(arg('--contact'), set(ONLY) or None)
    sheets = {}
    want = {TARGETS[k][0] if k in TARGETS else k for k in ONLY}      # a sheet is always rebuilt whole (all its targets)
    keys = [k for k in TARGETS if not want or TARGETS[k][0] in want]
    for k in keys:
        sh, tag, fn = TARGETS[k]
        print(k, flush=True)
        sheets.setdefault(sh, {})[tag] = fn()
    if '--dry' in ARGS: return
    for sh, rep in sheets.items():
        n = L.rebuild(sh, rep); print('built', sh, n, 'frames;', ', '.join(rep))


if __name__ == '__main__':
    main()
