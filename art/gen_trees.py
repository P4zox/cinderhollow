#!/usr/bin/env python3
"""Trees pass (docs/v17/trees.md): the Thornveil's trees, rebuilt.

  xsa_oak   256x224  tag motheroak   The Mother Oak (TV14 Mossbed Glade, a back prop standing on the floor, foot = bottom row)
  tv_tree   96x240   tags v0 v1 v2   the giant back trunks of the Thornveil rooms (drawn 12 px below the floor line)
  xsa_elder 240x440  tag elder       the Elder of TV9 (behind the elder-skinned trunk; the hollow and the fork stay where they were)

Procedural (art/treelib.py): a skeleton of tapering branches shaded as bark cylinders + clumped foliage masses, resolved to 1x
on hand-picked Thornveil ramps. The 1x results are also written to art/bg_src/trees/<name>.png (tracked) so the older
generators (gen_xsa.py, thornveil_props.py) reuse them instead of drawing their old versions.

  python3 art/gen_trees.py [oak|trees|elder ...] [--no-ase] [--render] [--procedural]
    --render      repaint the texture pass with ComfyUI (:8188, prefix trees/) -> art/bg_src/trees/<name>_render.png (gitignored)
    --procedural  build without a painted pass (the oak and the trunks otherwise refuse, so a checkout without the renders
                  can't silently replace the shipped art)
  Previews (3x, over flat and backdrop) -> art/previews/trees/ (gitignored).
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import treelib as T
from treelib import S, C

ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, 'bg_src', 'trees'); os.makedirs(SRC, exist_ok=True)
PREV = os.path.join(HERE, 'previews', 'trees'); os.makedirs(PREV, exist_ok=True)   # gitignored

OUTL = (9, 12, 11)


def ramp(*hs):
    return np.array([C(h) for h in hs], float)


# ----------------------------------------------------------------------------------------------- shared resolve
def resolve(layers, w, h):
    """layers: list (back->front) of (cov4x bool, val4x float, extra dict of 4x float maps). -> per-1x: layer index (-1 none),
    value, extras averaged over that layer's subpixels, coverage."""
    H, W = h * S, w * S
    top = np.full((H, W), -1, int)
    for i, (cov, val, ex) in enumerate(layers): top = np.where(cov, i, top)
    covd = T.down((top >= 0).astype(float), w, h)
    cnt = np.stack([T.down((top == i).astype(float), w, h) for i in range(len(layers))], -1)
    lay = np.where(covd >= 0.5, cnt.argmax(-1), -1)
    val = np.zeros((h, w)); extras = {}
    for i, (cov, v, ex) in enumerate(layers):
        m = (top == i).astype(float); c = np.maximum(T.down(m, w, h), 1e-6); sel = lay == i
        val = np.where(sel, T.down(v * m, w, h) / c, val)
        for k, a in ex.items():
            extras.setdefault(k, np.zeros((h, w)))
            extras[k] = np.where(sel, T.down(a * m, w, h) / c, extras[k])
    return lay, val, extras


def edge_light(alpha, wts=(1.0, 0.75, 0.55, 0.12)):
    """per-pixel rim weight from transparent neighbours: (up, left, right, down) weights; 2nd ring at half."""
    up, dn, lf, rt = T.neighbours(alpha)
    w1 = np.maximum.reduce([~up * wts[0], ~lf * wts[1], ~rt * wts[2], ~dn * wts[3]]) * alpha
    a2 = alpha & (w1 == 0)
    # second ring: pixels whose up/left neighbour is a first-ring pixel
    r1 = w1 > 0
    p = np.pad(r1, 1); pw = np.pad(w1, 1)
    w2 = np.maximum.reduce([p[:-2, 1:-1] * pw[:-2, 1:-1] * 0.5, p[1:-1, :-2] * pw[1:-1, :-2] * 0.45, p[1:-1, 2:] * pw[1:-1, 2:] * 0.3]) * a2
    return w1, w2


def save_rgba(arr, path):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


def preview(img, name, bgs):
    """img RGBA PIL -> 3x previews over each background (PIL RGBA same size or None = flat)."""
    outs = []
    for bg in bgs:
        b = bg.copy() if bg is not None else Image.new('RGBA', img.size, (52, 54, 60, 255))
        b.alpha_composite(img); outs.append(b)
    W = sum(o.width for o in outs) + 4 * (len(outs) - 1)
    sheet = Image.new('RGBA', (W, img.height), (0, 0, 0, 255)); x = 0
    for o in outs: sheet.alpha_composite(o, (x, 0)); x += o.width + 4
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(PREV, name + '.png'))


# =============================================================================================== THE MOTHER OAK
OAK_BARK = ramp('#0a0b0a', '#121411', '#1a1c17', '#23251e', '#2d2e25', '#38382c', '#454434', '#55523e', '#68634a')
OAK_MOSS = ramp('#0c1710', '#112016', '#172b1b', '#1f3821', '#294829', '#365a32', '#4a703e')
OAK_LEAF = ramp('#06100c', '#0a1812', '#0f2118', '#152b1d', '#1c3622', '#244228', '#2e4f2d', '#3b5e31', '#4c6f37', '#62833f', '#7d9a4b')
OAK_RIM = ramp('#4f6a3a', '#6f8c4c', '#97b263', '#c4d886')
OAK_HAZE = ramp('#0c1915', '#11221c', '#172c23', '#1e372b', '#264233', '#2f4e3b', '#3a5b44')   # the back dome, in the glade's haze
OAK_BEARD = ramp('#1f2a1f', '#2f3d2c', '#44553d', '#5f7352', '#839770')
SPORE = (226, 255, 196)
STONE = ramp('#121516', '#1a1f20', '#242a2b', '#303738', '#3e4645', '#4f5855', '#636d67')


def oak_wood(w, h):
    Wd = T.Wood(w, h); nz = T.Noise(11)
    taper = lambda r0, r1, k=1.35: (lambda t, s: r1 + (r0 - r1) * (1 - t) ** k * (1 + 0.06 * np.sin(s * 0.33)))
    # ---- twigs and boughs (behind everything)
    sub = [
        ([(82, 118), (76, 100), (68, 84), (62, 68)], 5.8, 1.5), ([(44, 116), (34, 104), (28, 90)], 4.4, 1.3),
        ([(22, 114), (12, 122), (6, 131)], 3.2, 1.0), ([(60, 114), (56, 126), (52, 135)], 2.8, 0.9),
        ([(174, 110), (178, 94), (186, 78), (190, 62)], 5.8, 1.5), ([(214, 99), (222, 86), (228, 72)], 4.2, 1.2),
        ([(236, 91), (244, 100), (249, 109)], 3.0, 1.0), ([(196, 102), (200, 114), (203, 125)], 2.8, 0.9),
        ([(100, 88), (82, 72), (64, 60), (48, 54)], 6.0, 1.5), ([(92, 58), (78, 42), (70, 26)], 4.2, 1.2),
        ([(89, 40), (98, 24), (106, 12)], 3.4, 1.0), ([(156, 86), (174, 74), (196, 64), (214, 60)], 5.6, 1.5),
        ([(164, 58), (156, 40), (152, 22)], 4.0, 1.2), ([(168, 40), (182, 28), (194, 20)], 3.2, 1.0),
    ]
    for i, (pts, r0, r1) in enumerate(sub):
        Wd.branch(pts, r0, r1, wob=1.2, wobf=0.2, seed=7 + i, rprof=taper(r0, r1, 1.1), mossk=1.0, twist=0.1)
    # ---- the two great limbs, reaching out from behind the trunk (the west one sags, the east one climbs)
    Wd.branch([(124, 142), (104, 129), (82, 119), (60, 115), (40, 118), (22, 114), (8, 104)], 15.5, 2.4, wob=2.0, wobf=0.1, seed=21,
              rprof=taper(15.5, 2.4), twist=0.1)
    Wd.branch([(132, 138), (152, 123), (174, 111), (196, 103), (218, 98), (236, 90), (246, 80)], 14.5, 2.4, wob=2.0, wobf=0.1, seed=22,
              rprof=taper(14.5, 2.4), twist=0.1)
    # ---- the trunk: a twisting, flaring column
    Wd.branch([(128, 240), (127, 214), (123, 190), (120, 166), (122, 146), (127, 130)], 30, 21, wob=2.5, wobf=0.05, seed=31,
              rprof=lambda t, s: 21 + 7 * (1 - t) + 30 * np.exp(-s / 13) + 2.0 * np.sin(s * 0.11 + 1), twist=0.12, mossk=0.8)
    # ---- the leaders grow out of it (seamless inside the trunk)
    Wd.branch([(121, 152), (114, 126), (105, 101), (96, 77), (90, 53), (88, 30)], 17, 3.5, wob=1.8, wobf=0.1, seed=23,
              rprof=taper(17, 3.5, 1.2), twist=0.12, under=34)
    Wd.branch([(133, 150), (141, 124), (151, 99), (160, 75), (166, 51), (171, 28)], 15, 3.2, wob=1.8, wobf=0.1, seed=24,
              rprof=taper(15, 3.2, 1.2), twist=0.12, under=34)
    # ---- a broken stub low on the trunk (the limb that fell), burls
    stub = None
    for (bx, by, br, sd) in [(108, 186, 7.0, 40), (143, 198, 6.0, 41), (137, 154, 5.0, 42)]:
        Wd.branch([(bx - 0.5, by + br * 0.3), (bx + 0.5, by - br * 0.3)], br, br * 0.9, seed=sd, twist=0.6, mossk=0.6)
    # ---- buttress roots gripping the ground (the front ones over the trunk's foot)
    roots = [
        ([(104, 192), (84, 202), (64, 210), (46, 214), (36, 220), (32, 229)], 7.0, 2.4),
        ([(152, 190), (172, 200), (194, 208), (214, 212), (222, 220), (224, 229)], 6.5, 2.4),
        ([(110, 204), (92, 212), (72, 218), (50, 221), (28, 224), (14, 229)], 11.0, 2.0),
        ([(146, 202), (164, 210), (186, 216), (210, 220), (234, 224), (250, 230)], 11.5, 2.0),
        ([(118, 210), (106, 219), (100, 229)], 9.0, 4.0), ([(140, 210), (152, 219), (158, 229)], 9.0, 4.0),
    ]
    for i, (pts, r0, r1) in enumerate(roots):
        Wd.branch(pts, r0, r1, wob=1.5, wobf=0.12, seed=50 + i, rprof=taper(r0, r1, 1.6), twist=0.04, mossk=1.3)
    # ---- stones half sunk in the moss among the roots, thin roots gripping over them
    for i, (sx, sy, srx, sry) in enumerate([(84, 219, 9, 6), (176, 218, 9, 6), (22, 221, 6, 4), (236, 220, 7, 5), (128, 223, 6, 3)]):
        Wd.blob(sx, sy, srx, sry, seed=70 + i)
    for i, pts in enumerate([[(96, 210), (86, 213), (78, 218), (72, 226)], [(164, 209), (174, 212), (182, 217), (188, 226)]]):
        Wd.branch(pts, 2.6, 1.2, wob=0.8, wobf=0.3, seed=80 + i, twist=0.02, mossk=1.0)
    return Wd, nz, stub


STYLE = os.environ.get('OAK_STYLE', 'cumulus')


def oak_leaves(w, h):
    return oak_leaves_tiers(w, h) if STYLE == 'tiers' else oak_leaves_cumulus(w, h)


def oak_leaves_tiers(w, h):
    """Long, tapering leaf shelves along the limbs (lit upper surface, a fine leafy edge, ends drooping), staggered in depth over
    a dark back dome; sky between the tiers."""
    back = T.Leaves(w, h); front = T.Leaves(w, h)
    BACK = [(128, 38, 102, 30, 0.0), (40, 82, 30, 12, 0.12), (216, 78, 30, 12, -0.12), (128, 70, 34, 11, 0.0)]
    FRONT = [  # cx, cy, rx, ry, tilt, droop
        (50, 95, 44, 10, 0.10, 5), (78, 66, 38, 12, 0.06, 4), (128, 30, 62, 20, 0.0, 6), (180, 62, 40, 12, -0.06, 4),
        (208, 90, 44, 10, -0.12, 5), (96, 46, 26, 10, 0.1, 2), (160, 44, 28, 10, -0.08, 2), (124, 76, 18, 7, 0.0, 1),
        (16, 108, 13, 5, 0.25, 2), (242, 102, 11, 5, -0.3, 2)]
    kw = dict(clump=(1.6, 3.0), wts=(0.62, 0.22, 0.3), sub_r=(0.45, 0.7), ragged=0.5, drip=0.6)
    for i, (cx, cy, rx, ry, tl) in enumerate(BACK):
        back.lobe(cx, cy, rx, ry, 100 + i, subs=4, zbase=0, lift=-0.08, holes=0.3, tilt=tl, **kw)
    for i, (cx, cy, rx, ry, tl, dr) in enumerate(FRONT):
        front.lobe(cx, cy, rx, ry, 200 + i, subs=5, zbase=20 + cy * 0.6, lift=0.02, holes=0.6, tilt=tl, droop=dr, **kw)
    back.holes += [(104, 82, 5), (154, 80, 5.5), (128, 60, 3), (30, 62, 3.5), (228, 60, 3.5), (78, 84, 3.5), (180, 82, 3.5)]
    return back, front


def oak_leaves_cumulus(w, h):
    """One broad crown of rounded leaf masses stacked like cumulus (the lower ones in front), heavier to the east; the long west
    limb carries only two small clusters so the bough shows over the bench. A hazier back dome behind the wood gives depth;
    gaps where the limbs show. Each clump keeps its own lit crescent, so the masses read as leaves, not balloons."""
    back = T.Leaves(w, h); front = T.Leaves(w, h)
    BACK = [(132, 34, 96, 28), (120, 66, 22, 10), (44, 74, 22, 13), (214, 72, 26, 15)]
    FRONT = [(24, 100, 14, 8), (49, 95, 10, 6), (70, 63, 30, 19), (44, 43, 18, 12), (100, 37, 30, 18), (156, 33, 34, 19),
             (226, 42, 16, 11), (196, 59, 32, 20), (215, 88, 24, 12), (240, 101, 9, 6), (128, 73, 12, 7), (128, 12, 50, 14),
             (142, 58, 14, 9), (98, 62, 10, 7)]
    for i, (cx, cy, rx, ry) in enumerate(BACK):
        back.lobe(cx, cy, rx, ry, 100 + i, zbase=0, lift=0.0, holes=0.3, clump=(3.0, 5.4))
    for i, (cx, cy, rx, ry) in enumerate(FRONT):
        front.lobe(cx, cy, rx, ry, 200 + i, zbase=20 + cy * 0.6, lift=0.05, holes=1.1, clump=(2.6, 5.0), drip=0.35, ragged=0.3)
    back.holes += [(104, 82, 5), (156, 82, 5), (30, 60, 3.5), (232, 60, 3.5), (80, 86, 3.5), (184, 84, 3.5), (130, 50, 3)]
    return back, front


def ragged_holes(holes, seed=5):
    """Big gaps become irregular: each is replaced by a cluster of smaller bites around it."""
    rng = np.random.default_rng(seed); out = []
    for hx, hy, hr in holes:
        if hr < 3: out.append((hx, hy, hr)); continue
        for _ in range(int(hr * 1.5)):
            a = rng.uniform(0, 2 * math.pi); d = rng.uniform(0, hr * 0.6)
            out.append((hx + math.cos(a) * d, hy + math.sin(a) * d * 0.8, hr * rng.uniform(0.35, 0.6)))
    return out


def oak_model():
    w, h = 256, 224
    Wd, nz, stub = oak_wood(w, h)
    val, rim, moss, furrow = Wd.shade(nz, light=(-0.65, -0.55, 0.52), rim_dir=[(-0.3, -0.95, 1.0), (1.0, -0.2, 0.75)], ridges=0.55,
                                      furrow_depth=0.85, plate_len=12, ambient=0.17, key=0.78, moss_amt=0.62, pattern='fissure', gaps=0.26, fw=0.15)
    val, moss, st = Wd.stone_shade(nz, val, moss)
    back, front = oak_leaves(w, h)
    T.carve(ragged_holes(back.holes + front.holes), back.cov, front.cov)
    bv, _ = back.shade(ambient=0.12); fv, _ = front.shade(ambient=0.1)
    lay, v1, ex = resolve([(back.cov, bv, {}), (Wd.cov, val, {'rim': rim * ~st, 'moss': moss, 'fur': furrow, 'stone': st.astype(float)}),
                           (front.cov, fv, {})], w, h)
    M = dict(w=w, h=h, lay=lay, v=v1, ex=ex, alpha=lay >= 0, wood=lay == 1, leaf=(lay == 0) | (lay == 2), back=lay == 0,
             bark=OAK_BARK, moss=OAK_MOSS, leafr=OAK_LEAF, rimr=OAK_RIM, haze=OAK_HAZE, stone=(lay == 1) & (ex['stone'] > 0.5))
    M['rgb'] = colourize(M, v1, ex['moss'] > 0.5)
    return M


def colourize(M, v, mossy, leaf_off=-0.08):
    wd, lv = M['wood'], M['leaf']
    bi = T.ramp_index(v, len(M['bark']), dk=0.35)
    mi = T.ramp_index(v * 1.15 + 0.05, len(M['moss']), dk=0.35)
    col = np.where((wd & mossy)[..., None], M['moss'][mi], M['bark'][bi])
    if 'stone' in M:
        si = T.ramp_index(v, len(STONE), dk=0.3)
        col = np.where((M['stone'] & ~mossy)[..., None], STONE[si], col)
    fr = lv & ~M['back']
    li = T.orphans(T.ramp_index(v, len(M['leafr']), dk=0.3), fr)
    col = np.where(fr[..., None], M['leafr'][li], col)
    if 'haze' in M:
        hi = T.orphans(T.ramp_index(v + leaf_off, len(M['haze']), dk=0.3), M['back'])
        col = np.where(M['back'][..., None], M['haze'][hi], col)
    else:
        bi2 = T.orphans(T.ramp_index(v + leaf_off, len(M['leafr']), dk=0.3), M['back'])
        col = np.where(M['back'][..., None], M['leafr'][bi2], col)
    return col


def hist_match(src, ref):
    """Values of src remapped so their distribution matches ref's (both 1-D)."""
    if len(src) == 0: return src
    o = np.argsort(src); r = np.sort(ref); out = np.empty_like(src, float)
    out[o] = np.interp(np.linspace(0, 1, len(src)), np.linspace(0, 1, len(r)), r)
    return out


def apply_ai(M, ai_rgb, k_wood=0.75, k_leaf=0.6, green=14.0):
    """Keep the model's values (their distribution per class) but take the texture from the painted pass: the AI luminance is
    histogram-matched to the model's values and blended in; green in the AI wood becomes moss."""
    lum = ai_rgb @ np.array([0.299, 0.587, 0.114])
    v = M['v'].copy()
    for m, k in ((M['wood'], k_wood), (M['leaf'] & ~M['back'], k_leaf), (M['back'], k_leaf)):
        if m.sum() < 4: continue
        v[m] = (1 - k) * M['v'][m] + k * hist_match(lum[m], M['v'][m])
    g = ai_rgb[..., 1] - (ai_rgb[..., 0] + ai_rgb[..., 2]) / 2
    mossy = ((M['ex']['moss'] > 0.5) & (g > green * 0.4)) | (g > green)
    return v, mossy


def finish(M, rgb, rim_w=(1.0, 0.8, 0.6, 0.0), rim_mix=0.7, rim_min=0.25):
    """Backlight rim on the crown's edges + the wood's grazing rim, then the 1 px outline on the open silhouette."""
    h, w = M['h'], M['w']; alpha = M['alpha']; v1 = M['v']; lv = M['leaf']; wd = M['wood']
    w1, w2 = edge_light(~T.exterior(alpha, min_hole=40), rim_w)      # tiny dapples don't rim
    w1 *= alpha; w2 *= alpha
    rk = np.where(lv, np.maximum(w1 * (v1 > rim_min), w2 * 0.75 * (v1 > rim_min + 0.15)), 0)
    rk = np.where(wd, M['ex']['rim'] * 0.9, rk)
    ri = np.clip(np.floor(rk * 3.0 + (T.bayer(h, w) - 0.5) * 0.3) - 1, -1, 3).astype(int)
    R = M['rimr']
    mix = np.where(lv & (w1 > 0), min(1.0, rim_mix + 0.15), rim_mix)[..., None]
    col = np.where((ri >= 0)[..., None] & alpha[..., None], R[np.clip(ri, 0, len(R) - 1)] * mix + rgb * (1 - mix), rgb)
    out = np.zeros((h, w, 4)); out[..., :3] = col; out[..., 3] = alpha * 255
    return T.outline(out, OUTL, ext=T.exterior(alpha, min_hole=10 ** 6))


def oak_dress(out, lay):
    """Hanging moss from the boughs and the crown's underside, vines, glowing spores."""
    rng = np.random.default_rng(77); h, w = lay.shape
    op = out[..., 3] > 0
    anchors = []
    for y in range(76, 132):
        for x in range(4, w - 4):
            if not op[y, x] or op[y + 1, x]: continue
            if 92 < x < 166 and y > 116: continue          # not on the trunk
            wood = lay[max(0, y - 1), x] == 1
            if rng.random() < ((0.13 if x < 110 else 0.07) if wood else 0.025): anchors.append((x, y, (1.25 if x < 110 else 1.0) if wood else 0.6))
    T.strands(out, rng, anchors, OAK_BEARD, length=(4, 24), per=(2, 5), sway=0.45)
    for p0, p1, sag in [((40, 118), (66, 116), 7), ((178, 112), (204, 104), 8), ((222, 100), (238, 94), 5)]:
        T.vine(out, p0, p1, sag, (22, 40, 24), (52, 84, 44), rng)
    for x, y, a in [(70, 128, 1.0), (96, 112, 0.8), (150, 120, 0.9), (186, 128, 1.0), (40, 134, 0.7), (214, 118, 0.8), (124, 104, 0.7),
                    (60, 152, 0.6), (204, 150, 0.6), (232, 134, 0.6)]:
        T.spore(out, x, y, SPORE, (150, 235, 140), a)


# ----------------------------------------------------------------------------------------------- painted texture pass (ComfyUI)
AI_NEG = ('text, watermark, signature, person, character, people, cartoon, chibi, blurry, jpeg artifacts, frame, border, '
          'flat colors, vector, smooth gradient')


def ai_pass(name, guide_rgba, bg, prompt, seed, denoise=0.5, cn=0.65, cn_end=0.8, pix=0.5, render=False):
    """The model's colours over a backdrop, 4x, softened -> img2img (SDXL + pixel-art LoRA + Lightning, tile ControlNet from the
    guide itself, so the forms stay put) -> back to 1x (BOX). Renders are cached in art/bg_src/trees/<name>_render.png
    (gitignored); without one (and without render=True) the pass is skipped."""
    from PIL import ImageFilter
    out = os.path.join(SRC, f'{name}_render.png'); gp = os.path.join(SRC, f'guide_{name}.png')
    w, h = guide_rgba.size
    g = (bg.copy() if bg is not None else Image.new('RGBA', (w, h), (40, 50, 44, 255))); g.alpha_composite(guide_rgba)
    g = g.convert('RGB').resize((w * S, h * S), Image.NEAREST).filter(ImageFilter.GaussianBlur(1.5))
    same = os.path.exists(gp) and np.array_equal(np.asarray(Image.open(gp).convert('RGB')), np.asarray(g))
    if not render:
        if not (same and os.path.exists(out)):
            print(f'  [{name}] no painted pass for this guide (run with --render): procedural colours only'); return None
    else:
        import bgv2lib as V
        c = V._comfy(); g.save(gp)
        up = c.upload(gp)
        wf = c.workflow(prompt, seed, init_image=up, denoise=denoise, negative=AI_NEG, pose=up, pose_type='tile', pose_strength=cn,
                        loras=V.lora_set(pix))
        wf['43']['inputs']['end_percent'] = cn_end
        wf['9']['inputs']['filename_prefix'] = f'trees/{name}'
        c.run(wf, out)
    return np.asarray(Image.open(out).convert('RGB').resize((w, h), Image.BOX), float)


OAK_PROMPT = ('pixel art, a colossal ancient oak tree, massive gnarled trunk with deep furrowed bark and moss, buttress roots, '
              'twisting limbs, broad canopy of dense layered leaf clusters, dappled light, backlit by a glowing green forest glade, '
              'rim light, dark fantasy, mythic, highly detailed, game background')


def oak(render=False, seed=3, denoise=0.6):
    M = oak_model()
    guide = Image.fromarray(np.dstack([np.clip(M['rgb'], 0, 255), M['alpha'] * 255]).astype(np.uint8))
    ai = ai_pass('oak', guide, vista_bg(M['w'], M['h']), OAK_PROMPT, seed, denoise=denoise, render=render)
    if ai is not None:
        v, mossy = apply_ai(M, ai)
        rgb = colourize(M, v, mossy)
    else:
        rgb = M['rgb']
    out = finish(M, rgb)
    oak_dress(out, M['lay'])
    return out, M, ai


# =============================================================================================== THORNVEIL TRUNKS (tv_tree)
TV_BARK = ramp('#0a0b0a', '#0f110f', '#151814', '#1c201a', '#242a21', '#2e3529', '#394133', '#475040', '#58614e', '#6c7660')
TV_MOSS = ramp('#0b1712', '#0f2119', '#152d1f', '#1c3a26', '#24492d', '#2f5935', '#3d6b3f')
TV_RIM = ramp('#4e6058', '#6b8078', '#93a89c')
TV_FUNG = ramp('#1e1a15', '#332c22', '#4e4535', '#6d6249', '#8e8262', '#ada17c')
TV_IVY = ramp('#0d1a10', '#15291a', '#1f3b23', '#2d522d', '#40693a')
SPIRIT = [C(h) for h in ('#123c2c', '#1d6644', '#2f9a5e', '#5fe08e', '#b4ffd0', '#f0fff6')]
RIBBON = [C(h) for h in ('#3f3c37', '#5d5a52', '#8f8a7c', '#bcb6a4', '#e2dccb')]
GROUND = 228          # the floor line inside the 96x240 frame (the engine draws the frame 12 px below the floor)


def tv_skeleton(v):
    w, h = 96, 240; Wd = T.Wood(w, h); nz = T.Noise(60 + v)
    trunk_r = lambda base, top, flare: (lambda t, s: top + (base - top) * (1 - t) + flare * np.exp(-s / 9.0) + 0.8 * np.sin(s * 0.09 + v))
    extra = {}
    if v == 0:      # tall and straight-ish, leaning a little east; a broken limb on the west side
        Wd.branch([(30, 82), (19, 73), (12, 69)], 6.2, 5.0, seed=5, twist=0.05)                        # behind: the stub's far half
        Wd.branch([(47, 252), (48, 228), (50, 190), (52, 140), (53, 90), (52, 40), (50, -12)], 16, 13.5, wob=1.6, wobf=0.05, seed=1,
                  rprof=trunk_r(17, 13.5, 24), twist=0.1)
        extra['stub'] = Wd.branch([(42, 86), (30, 77), (19, 71)], 6.6, 5.4, seed=6, twist=0.05, under=6)
    elif v == 1:    # leaning west, splitting into two leaders near the top; the hollow with its ribbon
        Wd.branch([(48, 252), (47, 228), (45, 180), (43, 120), (43, 74), (45, 52)], 17, 13, wob=1.4, wobf=0.05, seed=2,
                  rprof=trunk_r(17.5, 13, 26), twist=0.12)
        Wd.branch([(42, 70), (37, 40), (31, 12), (27, -12)], 10.5, 8, wob=1.0, wobf=0.08, seed=3, twist=0.12, under=14)
        Wd.branch([(49, 68), (56, 40), (62, 14), (66, -12)], 9.5, 7, wob=1.0, wobf=0.08, seed=4, twist=0.12, under=14)
    else:           # an S-curve sway, burls, a bough leaving the frame; the spirit-lit runes
        Wd.branch([(52, 44), (66, 30), (82, 20), (98, 13)], 5.6, 3.2, wob=0.8, wobf=0.15, seed=7, twist=0.08)
        Wd.branch([(48, 252), (49, 228), (53, 190), (56, 150), (52, 110), (45, 70), (44, 30), (47, -12)], 15, 13, wob=1.2, wobf=0.05,
                  seed=8, rprof=trunk_r(16, 13, 24), twist=0.14)
        for (bx, by, br, sd) in [(62, 176, 6.0, 9), (37, 96, 5.0, 10)]:
            Wd.branch([(bx - 0.5, by + br * 0.3), (bx + 0.5, by - br * 0.3)], br, br * 0.9, seed=sd, twist=0.6)
    # roots: the flare fingers out over the floor line and dives under it
    rr = {0: [((40, 210), (28, 220), (14, 226), (4, 236), 8.0), ((58, 212), (72, 221), (86, 227), (95, 236), 7.5),
              ((45, 222), (40, 232), (37, 242), None, 6.0), ((54, 222), (60, 232), (63, 242), None, 5.5)],
          1: [((38, 208), (24, 219), (10, 226), (0, 234), 8.5), ((57, 210), (70, 220), (82, 228), (90, 238), 7.0),
              ((44, 222), (36, 233), (32, 242), None, 6.0)],
          2: [((42, 210), (30, 220), (18, 227), (8, 236), 7.5), ((60, 210), (74, 219), (88, 226), (96, 234), 8.0),
              ((50, 222), (47, 232), (46, 242), None, 6.0), ((57, 224), (64, 233), (68, 242), None, 4.5)]}[v]
    for i, q in enumerate(rr):
        pts = [p for p in q[:4] if p]; r0 = q[4]
        Wd.branch(pts, r0, 2.0, wob=1.0, wobf=0.15, seed=20 + i, rprof=lambda t, s, r0=r0: 2.0 + (r0 - 2.0) * (1 - t) ** 1.5, twist=0.04, mossk=1.3)
    return Wd, nz, extra


def tv_tree(v, render=False):
    w, h = 96, 240
    Wd, nz, extra = tv_skeleton(v)
    val, rim, moss, furrow = Wd.shade(nz, light=(-0.7, -0.45, 0.55), rim_dir=[(-1.0, -0.25, 1.0), (1.0, -0.1, 0.35)], ridges=0.6,
                                      furrow_depth=0.85, plate_len=14, ambient=0.15, key=0.74, pattern='fissure', gaps=0.28, fw=0.15, moss_amt=0.32 + 0.05 * v, moss_side=(-1.0, 0.0), side_k=1.0)
    lay, v1, ex = resolve([(Wd.cov, val, {'rim': rim, 'moss': moss, 'fur': furrow})], w, h)
    M = dict(w=w, h=h, lay=lay, v=v1, ex=ex, alpha=lay >= 0, wood=lay == 0, leaf=np.zeros_like(lay, bool), back=np.zeros_like(lay, bool),
             bark=TV_BARK, moss=TV_MOSS, leafr=TV_MOSS, rimr=TV_RIM)
    M['rgb'] = colourize(M, v1, ex['moss'] > 0.5)
    return M, Wd, extra


def tv_dress(out, v, M, rng):
    """Per variant: fungus shelves, ivy, the hollow + ribbon, the spirit runes; moss beards from the knots."""
    h, w = out.shape[:2]; al = out[..., 3] > 0
    def edge_x(y, side):   # the trunk's outer x on a row (side -1 west, 1 east), ignoring roots
        xs = np.nonzero(al[y])[0]
        if not len(xs): return None
        return xs.min() if side < 0 else xs.max()
    def shelf(y0, side, n, L):   # bracket fungus: lens-shaped shelves stacked up the bark, lit tops, dark gills, a shadow below
        for k in range(n):
            y = y0 + k * 6 + int(rng.integers(0, 2)); x0 = edge_x(y, side)
            if x0 is None: continue
            ln = max(4, L - 2 * k + int(rng.integers(-1, 2))); H = 2.2 + 0.25 * ln
            x0 -= side * 3                                   # rooted a little inside the silhouette
            cx_, cy_ = x0 + side * ln * 0.5, y - H * 0.35
            for yy in range(int(y), int(y + 3 + ln * 0.25)):   # the cast shadow on the bark beneath
                for xx in range(min(x0, x0 - side * 4), max(x0, x0 - side * 4) + 1):
                    if 0 <= xx < w and 0 <= yy < h and al[yy, xx]: out[yy, xx, :3] = out[yy, xx, :3] * 0.6
            for yy in range(int(cy_ - H - 1), int(cy_ + H + 2)):
                for xx in range(min(x0, x0 + side * (ln + 1)), max(x0, x0 + side * (ln + 1)) + 1):
                    if not (0 <= xx < w and 0 <= yy < h): continue
                    ex_ = ((xx - cx_) / (ln * 0.55)) ** 2 + ((yy - cy_) / H) ** 2
                    if ex_ > 1 or (yy - cy_) > H * 0.45: continue      # flat underneath
                    t = abs(xx - x0) / ln
                    up_ = (yy - cy_) / H
                    if (yy - cy_) > H * 0.2: c = TV_FUNG[0]                   # the gills in shadow
                    elif up_ < -0.55: c = TV_FUNG[5] if t > 0.45 else TV_FUNG[4]   # the rim of the cap catching light
                    elif up_ < -0.1: c = TV_FUNG[3]
                    else: c = TV_FUNG[2]
                    if ex_ > 0.72 and up_ > -0.55 and up_ <= 0.2: c = TV_FUNG[1]   # the outer lip, darker
                    out[yy, xx, :3] = c; out[yy, xx, 3] = 255
    def ivy(x0, y0, y1, side, seed):   # a stem climbing the trunk's side, small three-pixel leaves
        r = np.random.default_rng(seed); x = float(x0)
        for y in range(y0, y1, -1):
            ex_ = edge_x(y, side)
            if ex_ is None: continue
            x = ex_ - side * (2 + 1.5 * math.sin(y * 0.11 + seed))
            xi = int(round(x)); out[y, xi, :3] = TV_IVY[1]; out[y, xi, 3] = 255
            if r.random() < 0.34:
                lx = xi + int(r.choice([-1, 1])) * int(r.integers(1, 3))
                for dx, dy, ci in ((0, 0, 3), (1, 0, 2), (0, -1, 4), (-1, 0, 2), (0, 1, 1)):
                    xx, yy = lx + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and (al[yy, xx] or ci >= 3):
                        out[yy, xx, :3] = TV_IVY[ci]; out[yy, xx, 3] = 255
    def knot(x, y, rx, ry):      # an eye-shaped knot: a dark core in a lit swollen ring
        for yy in range(int(y - ry - 2), int(y + ry + 3)):
            for xx in range(int(x - rx - 2), int(x + rx + 3)):
                if not (0 <= xx < w and 0 <= yy < h and al[yy, xx]): continue
                e = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2
                if e <= 0.45: out[yy, xx, :3] = TV_BARK[0] if e < 0.2 else TV_BARK[1]
                elif e <= 1.0: out[yy, xx, :3] = TV_BARK[6] if (xx < x and yy < y + 1) else TV_BARK[2]
                elif e <= 1.9 and yy > y + ry * 0.6: out[yy, xx, :3] = out[yy, xx, :3] * 0.7
    for (kx, ky, krx, kry) in {0: [(52, 108, 2.2, 3.6), (44, 196, 2.6, 4.0)], 1: [(52, 96, 2.0, 3.4), (40, 184, 2.4, 3.8)],
                               2: [(45, 62, 2.0, 3.2), (55, 166, 2.4, 3.6)]}[v]:
        knot(kx, ky, krx, kry)
    # the trunk sinks into shadow and ground mist towards the floor line
    yy = np.arange(h)[:, None]
    dim = np.clip((yy - (GROUND - 40)) / 40.0, 0, 1) * 0.35
    out[..., :3] = out[..., :3] * (1 - dim[..., None] * (out[..., 3:] > 0))
    if v == 0:
        shelf(126, 1, 3, 12); shelf(174, -1, 2, 9)
        ivy(40, 226, 92, -1, 3)
        # the broken end of the stub: a jagged, splintered tip
        for (x, y, c) in [(12, 66, 1), (11, 68, 0), (12, 70, 0), (13, 72, 1), (14, 65, 2), (15, 63, 3), (13, 74, 2)]:
            if 0 <= x < w: out[y, x, :3] = TV_BARK[c]; out[y, x, 3] = 255
        for (x, y) in [(15, 62), (16, 61), (14, 62)]:
            out[y, x, :3] = TV_BARK[6]; out[y, x, 3] = 255
    if v == 1:
        cx, hy = 46, 150
        yy, xx = np.mgrid[0:h, 0:w]
        e = ((xx - cx) / 6.5) ** 2 + ((yy - hy) / 12.5) ** 2
        lip = (e > 1) & (e <= 1.55) & al
        out[lip & (yy > hy), :3] = TV_BARK[7]; out[lip & (yy <= hy) & (xx < cx), :3] = TV_BARK[5]
        out[lip & (yy <= hy) & (xx >= cx), :3] = TV_BARK[2]
        inner = e <= 1
        depth = np.clip((yy - (hy - 12)) / 24.0, 0, 1)
        out[inner, :3] = np.array([3, 4, 4]) + (np.array([16, 20, 17]) * depth[..., None])[inner] * (xx[inner] > cx - 2)[..., None] * 0.6
        out[inner, 3] = 255
        rim_lo = lip & (yy > hy + 6)
        out[rim_lo & (xx < cx + 3), :3] = TV_MOSS[4]; out[rim_lo & (xx >= cx + 3), :3] = TV_MOSS[2]
        for x in range(cx - 15, cx + 16):    # the pale ribbon tied round the trunk above the hollow
            if al[118, x]:
                out[118, x, :3] = RIBBON[3] if (x - cx) < 4 else RIBBON[2]; out[119, x, :3] = RIBBON[1]
        for yy_ in range(22):
            x = int(round(cx + 10 + math.sin(yy_ * 0.3) * 2))
            out[120 + yy_, x, :3] = RIBBON[3] if yy_ < 6 else RIBBON[2] if yy_ < 14 else RIBBON[1]; out[120 + yy_, x, 3] = 255
            if yy_ < 18: out[120 + yy_, x + 1, :3] = RIBBON[1]; out[120 + yy_, x + 1, 3] = 255
        shelf(186, 1, 2, 10)
    if v == 2:
        # an ogham line cut by the first wardens down the bark: a stem with groups of strokes, lit from within by the spirit-light
        def glow_px(x, y, core=True):
            if not (0 <= x < w and 0 <= y < h) or not al[y, x]: return
            out[y, x, :3] = SPIRIT[3] if core else SPIRIT[2]
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = out[y + oy, x + ox]
                if q[3] and tuple(q[:3]) not in (tuple(SPIRIT[3]), tuple(SPIRIT[2])): q[:3] = q[:3] * 0.5 + np.array(SPIRIT[1]) * 0.5
        sx = lambda y: int(round(51 + math.sin(y * 0.09) * 1.2))
        for y in range(108, 166): glow_px(sx(y), y, (y % 7) != 3)
        y = 112
        for grp, kind in [(3, 'r'), (1, 'l'), (4, 'x'), (2, 'r'), (5, 'l'), (2, 'x')]:
            for k in range(grp):
                yy = y + k * 2; x = sx(yy)
                rng_ = {'r': range(1, 4), 'l': range(-3, 0), 'x': range(-2, 3)}[kind]
                for dx in rng_: glow_px(x + dx, yy - (1 if kind == 'x' and dx > 0 else 0))
            y += grp * 2 + 4
        for (x, y, a) in [(60, 132, 1.0), (63, 138, 0.8), (58, 144, 0.7), (64, 126, 0.6), (40, 152, 0.5)]:
            T.spore(out, x, y, SPIRIT[4], SPIRIT[3], a)
        shelf(180, -1, 2, 10)
        ivy(60, 226, 168, 1, 7)
    # moss beards from a few knots / the stub
    anchors = []
    for y in range(40, 200):
        for x in range(1, w - 1):
            if al[y, x] and not al[y + 1, x] and y + 1 < GROUND - 14 and rng.random() < 0.18: anchors.append((x, y, 0.8))
    T.strands(out, rng, anchors, [TV_MOSS[2], TV_MOSS[3], TV_MOSS[4], TV_MOSS[5]], length=(4, 16), per=(1, 3), sway=0.4)


TV_PROMPT = ('pixel art, a giant ancient gnarled tree trunk in a dark misty primeval forest, deep furrowed bark, moss, ivy, bracket '
             'fungus, knots and burls, cold moonlight from the left, dark fantasy, highly detailed, game background')


def tv_trees(render=False):
    frames = []
    for v in range(3):
        M, Wd, extra = tv_skeleton_model(v)
        guide = Image.fromarray(np.dstack([np.clip(M['rgb'], 0, 255), M['alpha'] * 255]).astype(np.uint8))
        bg = Image.new('RGBA', (96, 240), (14, 22, 20, 255))
        ai = ai_pass(f'tv{v}', guide, bg, TV_PROMPT, 11 + v, denoise=0.5, render=render)
        if ai is None and not PROCEDURAL: raise NoPaint(f'tv{v}')
        if ai is not None:
            vv, mossy = apply_ai(M, ai, k_wood=0.55)
            rgb = colourize(M, vv, mossy)
        else:
            rgb = M['rgb']
        out = finish(M, rgb, rim_w=(0.6, 1.0, 0.4, 0.0), rim_mix=0.55)
        tv_dress(out, v, M, np.random.default_rng(90 + v))
        # the crown is far above: the top fades into the dark
        fade = np.clip((np.arange(240) - 2) / 34.0, 0, 1)[:, None]
        out[..., 3] = np.where(out[..., 3] > 0, np.round(out[..., 3] * fade / 32) * 32, 0)
        frames.append(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)))
    return frames


def tv_skeleton_model(v):
    M, Wd, extra = tv_tree(v)
    return M, Wd, extra


def build_trees(ase=True, render=False):
    frames = tv_trees(render)
    for v, im in enumerate(frames): im.save(os.path.join(SRC, f'tv_tree_v{v}.png'))
    strip = Image.new('RGBA', (96 * 3 + 8, 240), (0, 0, 0, 0))
    for v, im in enumerate(frames): strip.alpha_composite(im, (v * 100, 0))
    bg = Image.new('RGBA', strip.size, (14, 20, 18, 255))
    preview(strip, 'tv_trees', [None, bg])
    if ase:
        import asebuild
        asebuild.build('tv_tree', 96, 240, ['Art'], [{'ms': 110, 'cels': {'Art': f}} for f in frames], [('v0', 0, 0), ('v1', 1, 1), ('v2', 2, 2)])
    return frames


# =============================================================================================== THE ELDER (xsa_elder, TV9)
# Frame 240x440, foot = bottom row, placed at room x 904 (frame x 112 = the centre of the elder-skinned trunk column, room cols
# 52..59 = frame x 48..175). The column (front layer) hides the frame's middle from y 24 to 359 except the cleft the high walk
# passes through (y 120..168); the hollow at the foot is open (y 360..440, x 64..159, thorn curtains at 48..63 / 160..175).
ELD_BARK = ramp('#0b0807', '#120d0a', '#1a130e', '#221912', '#2a1f16', '#33261b', '#3b2b1d', '#47362a', '#503b27', '#614a33', '#735a40')
ELD_RIM = ramp('#5a5a44', '#7a7a5a', '#9a9c74')
ELD_CX = 112


def elder_model():
    w, h = 240, 440; Wd = T.Wood(w, h); nz = T.Noise(91)
    cx = ELD_CX
    Wd.branch([(cx, 470), (cx, 440), (cx + 1, 380), (cx - 1, 300), (cx, 200), (cx + 1, 100), (cx, 0), (cx, -30)], 68, 67, wob=1.0, wobf=0.03,
              seed=1, rprof=lambda t, s: 67 + 34 * np.exp(-np.maximum(0, s - 20) / 60) + 1.5 * np.sin(s * 0.05), twist=0.08, mossk=0.9)
    # buttresses: ridges that rise out of the trunk's skin (nothing at their top end), swell as they reach the ground, then root
    roots = [((cx - 50, 250), (cx - 70, 330), (cx - 96, 400), (cx - 122, 452), 17.0), ((cx + 50, 254), (cx + 72, 334), (cx + 100, 400), (cx + 126, 452), 17.0),
             ((cx - 22, 330), (cx - 30, 380), (cx - 52, 420), (cx - 64, 452), 11.0), ((cx + 26, 334), (cx + 34, 384), (cx + 56, 420), (cx + 68, 452), 11.0)]
    for i, q in enumerate(roots):
        pts = [p for p in q[:4] if p]; r0 = q[4]
        Wd.branch(pts, r0, 4.0, wob=2.0, wobf=0.06, seed=10 + i, twist=0.05, mossk=1.4,
                  rprof=lambda t, s, r0=r0: 1.0 + (r0 - 1.0) * np.clip(t / 0.45, 0, 1) ** 0.8 * (1 - 0.65 * np.clip((t - 0.45) / 0.55, 0, 1)))
    val, rim, moss, furrow = Wd.shade(nz, light=(-0.7, -0.4, 0.6), rim_dir=[(-1.0, -0.3, 1.0), (1.0, -0.2, 0.4)], ridges=0.5,
                                      furrow_depth=0.85, plate_len=14, ambient=0.14, key=0.7, moss_amt=0.42, moss_side=(-1.0, 0.0), side_k=0.8,
                                      pattern='fissure', gaps=0.26, fw=0.14)
    lay, v1, ex = resolve([(Wd.cov, val, {'rim': rim, 'moss': moss, 'fur': furrow})], w, h)
    M = dict(w=w, h=h, lay=lay, v=v1, ex=ex, alpha=lay >= 0, wood=lay == 0, leaf=np.zeros_like(lay, bool), back=np.zeros_like(lay, bool),
             bark=ELD_BARK, moss=TV_MOSS, leafr=TV_MOSS, rimr=ELD_RIM)
    M['rgb'] = colourize(M, v1, ex['moss'] > 0.5)
    return M


def elder_dress(out, rng):
    h, w = out.shape[:2]; cx = ELD_CX
    yy, xx = np.mgrid[0:h, 0:w]
    # ---- the cleft the high walk passes through: a split in the trunk, dark, its splintered lips catching a little light
    top = 116 + 3 * np.sin(xx * 0.31) + 2 * np.sin(xx * 0.83 + 1); bot = 172 + 2 * np.sin(xx * 0.47 + 2)
    half = np.clip(1 - np.abs(xx - cx) / 78.0, 0, 1)
    cl = (yy > top) & (yy < bot) & (half > 0)
    depth = np.clip(1 - np.abs(yy - 144) / 30.0, 0, 1) * half
    out[cl, :3] = (np.array([22, 16, 12]) * (1 - depth[..., None]) + np.array([5, 3, 3]) * depth[..., None])[cl]
    fib = cl & ((xx % 5) == 0) & (np.sin(yy * 0.4 + xx) > -0.3) & (depth < 0.8)      # the heartwood's fibres, dim
    out[fib, :3] = out[fib, :3] * 1.6 + 4
    glow = np.exp(-(((xx - cx) / 26.0) ** 2 + ((yy - 146) / 10.0) ** 2)) * cl          # the heart of the Elder, still faintly alive
    out[..., :3] = out[..., :3] * (1 - glow[..., None] * 0.5) + np.array(SPIRIT[1]) * glow[..., None] * 0.5
    lipt = (yy > top - 2) & (yy <= top) & (half > 0); out[lipt, :3] = ELD_BARK[2]
    lipt2 = (yy > top) & (yy <= top + 1) & (half > 0.05); out[lipt2, :3] = ELD_BARK[6]
    for x in range(cx - 70, cx + 71, 7):    # splinters hanging into the cleft
        L = int(rng.integers(2, 7)); y0 = int(top[0, x]) + 1
        for k in range(L): out[y0 + k, x + (k // 3), :3] = ELD_BARK[4 if k < L - 1 else 7]
    # ---- the hollow at the foot: a tall pointed opening, the dark going deep, roots framing it
    hb = 440; ht = 357
    prof = lambda y: 58 * np.sqrt(np.clip((y - ht) / (hb - ht), 0, 1)) ** 0.9 + 2
    hw = prof(yy)
    ho = (yy > ht) & (np.abs(xx - cx) < hw)
    hdepth = np.clip((np.abs(xx - cx) / np.maximum(hw, 1)), 0, 1)
    shade = (1 - hdepth) * np.clip((yy - ht) / 60.0, 0, 1)
    out[ho, :3] = (np.array([18, 13, 10]) * (1 - shade[..., None]) + np.array([3, 2, 2]) * shade[..., None])[ho]
    out[ho, 3] = 255
    rimh = (~ho) & (yy > ht - 3) & (np.abs(xx - cx) < prof(yy + 3) + 3) & (out[..., 3] > 0)
    out[rimh & (xx < cx), :3] = ELD_BARK[7]; out[rimh & (xx >= cx), :3] = ELD_BARK[3]
    for i in range(9):    # grey ribbons the wardens tied over the hollow
        x = cx - 30 + i * 7 + int(rng.integers(-2, 3)); y0 = int(ht + 18 + abs(x - cx) * -0.0)
        y0 = int(ht + 4 + (abs(x - cx) / 58) ** 2 * 60)
        col = [RIBBON[3], C('7a2028'), C('6a6a8a')][int(rng.integers(0, 3))]
        L = int(rng.integers(10, 22))
        for k in range(L):
            xk = int(round(x + math.sin(k * 0.3 + i) * 1.2))
            out[y0 + k, xk, :3] = col if k < L * 0.7 else np.array(col) * 0.7; out[y0 + k, xk, 3] = 255
    # ---- ogham lines cut by the first wardens on the flanks, faintly lit
    for (sx0, sy0, n) in [(30, 300, 5), (196, 310, 4), (40, 386, 3), (186, 392, 4), (cx, 134, 0)]:
        y = sy0
        for g in range(n):
            grp = int(rng.integers(1, 5)); kind = rng.choice(['l', 'r', 'x'])
            for k in range(grp):
                for dx in {'r': range(1, 4), 'l': range(-3, 0), 'x': range(-2, 3)}[kind]:
                    if out[y + k * 2, sx0 + dx, 3]: out[y + k * 2, sx0 + dx, :3] = SPIRIT[2]
            y += grp * 2 + 4
        for yk in range(sy0 - 2, y):
            if n and out[yk, sx0, 3]: out[yk, sx0, :3] = SPIRIT[2] if yk % 6 else SPIRIT[3]
    for (x, y, a) in [(cx - 10, 150, 0.7), (cx + 14, 140, 0.6), (cx + 2, 420, 0.8), (cx - 20, 404, 0.5), (cx + 24, 396, 0.5)]:
        T.spore(out, x, y, SPIRIT[4], SPIRIT[3], a)
    # moss beards from the buttresses
    al = out[..., 3] > 0; anchors = []
    for y in range(200, 420):
        for x in range(1, w - 1):
            if al[y, x] and not al[y + 1, x] and rng.random() < 0.12: anchors.append((x, y, 0.8))
    T.strands(out, rng, anchors, [TV_MOSS[2], TV_MOSS[3], TV_MOSS[4], TV_MOSS[5]], length=(4, 14), per=(1, 3), sway=0.4)


ELD_PROMPT = ('pixel art, the colossal trunk of a primeval elder tree in a dark misty forest, deep furrowed bark, huge buttress roots, '
              'moss, dark fantasy, highly detailed, game background')


def elder(render=False, lift=0.0, edges=False):
    M = elder_model()
    guide = Image.fromarray(np.dstack([np.clip(M['rgb'], 0, 255), M['alpha'] * 255]).astype(np.uint8))
    ai = ai_pass('elder', guide, Image.new('RGBA', (240, 440), (14, 20, 18, 255)), ELD_PROMPT, 21, denoise=0.45, render=render)
    if ai is not None:
        v, mossy = apply_ai(M, ai, k_wood=0.6)
    else:
        v, mossy = M['v'], M['ex']['moss'] > 0.5
    rgb = colourize(M, v + lift, mossy)
    out = finish(M, rgb, rim_w=(0.5, 1.0, 0.5, 0.0), rim_mix=0.5)
    elder_dress(out, np.random.default_rng(33))
    if edges:   # the solid column's own edges (room cols 52 and 59): a dark seam, then a lit / shaded edge
        out[:, 47, :3] = OUTL; out[:, 48, :3] = ELD_BARK[9]; out[:, 49, :3] = ELD_BARK[7]
        out[:, 176, :3] = OUTL; out[:, 175, :3] = ELD_BARK[1]; out[:, 174, :3] = ELD_BARK[2]
        out[:, [47, 48, 49, 174, 175, 176], 3] = 255
    return out


def build_elder(ase=True, render=False):
    """'elder' = the back painting (a shade darker: it stands behind the play space); 'front' = the same tree lit as the solid
    column, which 53_sa.js draws into the elder-skinned cells instead of tiled bark, so the column IS the Elder."""
    im = Image.fromarray(np.clip(elder(render, lift=0.0), 0, 255).astype(np.uint8))
    fr = Image.fromarray(np.clip(elder(render, lift=0.0, edges=True), 0, 255).astype(np.uint8))
    im.save(os.path.join(SRC, 'elder.png')); fr.save(os.path.join(SRC, 'elder_front.png'))
    sim = im.copy(); sim.alpha_composite(fr.crop((47, 24, 177, 360)), (47, 24))
    cut = Image.new('RGBA', (130, 48), (0, 0, 0, 0)); sim.paste(im.crop((47, 120, 177, 168)), (47, 120))
    preview(im, 'elder', [None, Image.new('RGBA', im.size, (14, 20, 18, 255))])
    preview(sim, 'elder_ingame', [Image.new('RGBA', im.size, (14, 20, 18, 255))])
    if ase:
        import xsa_kit
        xsa_kit.sheet('xsa_elder', 240, 440, [('elder', [im]), ('front', [fr])])
    return im


# =============================================================================================== main
def vista_bg(w, h):
    try:
        v = Image.open(os.path.join(ROOT, 'assets', 'vista_tv14_far.png')).convert('RGBA')
        x0 = (v.width - w) // 2 + 10
        return v.crop((x0, v.height - h, x0 + w, v.height))
    except Exception:
        return None


class NoPaint(Exception):
    pass


def build_oak(ase=True, render=False):
    arr, M, ai = oak(render)
    if ai is None and not PROCEDURAL: raise NoPaint('oak')
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.save(os.path.join(SRC, 'motheroak.png'))
    preview(im, 'oak', [None, vista_bg(256, 224)])
    if ase:
        import xsa_kit
        xsa_kit.sheet('xsa_oak', 256, 224, [('motheroak', [im])])
    return im


PROCEDURAL = '--procedural' in sys.argv

if __name__ == '__main__':
    a = sys.argv[1:]; ase = '--no-ase' not in a; render = '--render' in a
    what = [x for x in a if not x.startswith('--')] or ['oak', 'trees', 'elder']
    for name, fn in (('oak', build_oak), ('trees', build_trees), ('elder', build_elder)):
        if name not in what: continue
        try: fn(ase, render)
        except NoPaint as e:
            print(f'  {name}: skipped, the painted pass for {e} is missing (art/bg_src/trees/*_render.png is gitignored): run with '
                  f'--render (ComfyUI on :8188) to repaint it, or --procedural to build without it')
    print('ok')
