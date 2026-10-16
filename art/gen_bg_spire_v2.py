#!/usr/bin/env python3
"""The Tempest Spire backdrop v2 (bg rollout agent A, docs/v17/bg_rollout_a.md; method: docs/v17/bg_pilot.md).

  python3 art/gen_bg_spire_v2.py               build bg_spire_{far,mid} from the saved renders in art/bg_src/spire/
  python3 art/gen_bg_spire_v2.py --guide       only (re)paint the layout guides
  python3 art/gen_bg_spire_v2.py --sweep far 1,2,3,4 [tag]   guides + pass-1 renders for those seeds (ComfyUI on :8188)
  python3 art/gen_bg_spire_v2.py --finish      seam pass for the picked sweep renders (PICK), then build
  --no-ase                                      write previews only, leave the assets alone

Same asset names, size, tags and frame counts as art/spire_bg.py, which 22_spire.js and 52_rc.js read:
  bg_spire_far  512x216, 10 frames: loop 0-3 (rain, whitecaps, the rod's spark), flash 4-6 (a forked bolt right of the spire),
                flash2 7-9 (sheet lightning over the left + a thin far bolt)
  bg_spire_mid  512x216, 4 frames: loop 0-3 (windmill sails turning, waves bursting on the bases)
How the animation survives the regeneration: the static base is rendered once (from the v1 composition: the median of the v1
loop frames, so no rain is baked in). Every v2 frame = the v2 base + what v1 frame f adds over its own median:
  * loop frames: the moving rain / whitecap / spark pixels of v1 frame f, added as a brightness delta;
  * flash frames: v1's light field (the delta, blurred so v1's cloud edges do not show) re-applied as a light pass that lifts
    the v2 clouds by their own luminance (lit undersides), plus the v1 bolt pixels exactly;
  * mid frames: the v2 static cliffs/causeway/stacks + the v1 pixels that move (sails, bursts), re-graded to the v2 ramp.
Rollback: restore art/bg_src/spire/v1/ (or python3 art/gen_spire_env.py, which also rebuilds the tiles).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import *  # noqa
import bgroll_a_lib as A
import spire_bg as SB
from spire_tiles import BOLT as BOLT_C, AMBER as AMBER_C

B = 'spire'
SRC = os.path.join(HERE, 'bg_src', B); os.makedirs(SRC, exist_ok=True)
TINT = '#0a0d16'
HZ = SB.HZ

FARR = ['04050a', '07080f', '0a0c14', '0e0f1a', '121320', '161726', '1b1b2d', '212035', '28263d', '2f2c46', '38344f', '423c59', '4d4663',
        '5a526f', '68627e', '7a7890', '8e92a8', 'a6b0c6', 'c2d0e2', 'dce8f4', 'f0f8ff']
SEA = ['0e1724', '132033', '1a2b43', '243a57', '32506f', '4a6d8c']
FOAM = ['4e6680', '7a94ae', 'a8c0d4', 'd6e6f0']
BOLT = ['2a4a8a', '5aa8ff', 'a4d6ff', 'eef9ff']
AMBER = ['6a3a14', 'a8621e', 'e09a3a', 'ffd27a']
FAR_PAL = [hexc(c) for c in FARR + SEA + FOAM + BOLT + AMBER]
MDR = ['06070c', '090b11', '0d1017', '12151e', '171b26', '1d2230', '252a3a', '2e3446', '3a4256', '4a546a']
RIMC = ['5a6a88', '7a8cac']
MID_PAL = [hexc(c) for c in MDR + RIMC + AMBER[:3] + FOAM]

PROMPT_FAR = ('pixel art, dark fantasy, a night storm over a black sea, heavy bruised storm clouds in layered strata with faintly lit '
              'undersides, far out a broken gothic stone spire tower on a rocky sea stack with a lightning rod and one small warm window, '
              'a rough sea with long rolling swells and whitecaps, a pale glow on the horizon, side-scroller game background, '
              'cold desaturated indigo, slate and storm blue palette, atmospheric depth, haze, highly detailed')
PROMPT_MID = ('pixel art, dark fantasy, wet black sea cliffs with a small stone windmill hamlet and a cottage on top, a ruined arched stone '
              'causeway bridge over the sea, jagged sea stacks, rain-wet rock with cold rim light, waves breaking at the bases, '
              'isolated on a flat grey background, side-scroller game background layer, dark slate and indigo stone, detailed')


def v1_frames(layer):
    a = np.asarray(Image.open(f'{SRC}/v1/bg_spire_{layer}.png').convert('RGBA'), float)
    n = a.shape[1] // W
    return [a[:, i * W:(i + 1) * W] for i in range(n)]


def v1_median():
    fr = v1_frames('far')[:4]
    return np.median(np.stack([f[..., :3] for f in fr]), 0)


def up3(a):
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((WS, HS), Image.BICUBIC), float)


def guide_far():
    med = v1_median()
    g = 255 * np.clip(med / 150, 0, 1) ** 0.72                      # lift the v1 storm 2-3 steps, keep its strata
    G = Guide(); G.rgb = up3(g)
    nz = tile_noise(WS, HS, 64, 6, 61, 2)
    # sea: long rolling swells with lit crests, spacing growing toward the viewer (perspective)
    sea = G.Y >= HZ + 1
    d = np.clip((G.Y - HZ) / (216 - HZ), 0, 1)
    phase = (1 / (d + 0.08)) * 9 + nz * 3 + 0.04 * G.X
    crest = (np.sin(phase) > 0.82).astype(float)
    base = lerp(hexc('1a2b43'), hexc('0a1019'), d[..., None] ** 0.6)
    G.rgb = np.where(sea[..., None], base, G.rgb)
    G.add(crest * sea * (0.3 + 0.7 * (1 - d)), hexc('2a3a50'), 1.0)
    G.fill(np.clip(1 - np.abs(G.Y - HZ - 0.5) / 1.0, 0, 1), hexc('5a6a88'), 0.6)    # horizon glint
    # the spire painted: stone with string courses, lit cold from the upper left, its window warm
    fs = SB.far_static()
    m1 = np.zeros((H, W))
    for (x, y) in fs.spire:
        if 0 <= y < H: m1[y, x % W] = 1
    m3 = np.asarray(Image.fromarray((m1 * 255).astype(np.uint8)).resize((WS, HS), Image.NEAREST), float) / 255
    dx = G.wdx(SB.SPX)
    stone = lerp(hexc('2a2c3e'), hexc('6a7088'), np.clip(0.45 - dx / 22, 0, 1)[..., None])
    course = ((G.Y - 70) % 12 < 1.6) & (G.Y > 70)
    stone = np.where(course[..., None], stone * 0.7, stone)
    G.fill_img(m3, stone)
    wx, wy = fs.window
    G.fill(G.mask_ellipse(wx + 0.5, wy + 0.5, 1.2, 1.6), hexc('e09a3a'))
    return G


def mid_static():
    """The v1 mid pixels that are the same in all four frames (rock, causeway, hamlet), and the moving rest."""
    fr = v1_frames('mid')
    al = [f[..., 3] > 0 for f in fr]
    same = np.ones(al[0].shape, bool)
    for f in fr[1:]:
        same &= (np.abs(f - fr[0]).sum(-1) == 0)
    static = same & al[0]
    return fr, static, ~same


def guide_mid():
    fr, static, moving = mid_static()
    rgb = fr[0][..., :3]
    lum = (rgb * [0.299, 0.587, 0.114]).sum(-1)
    yy, xx = np.mgrid[0:H, 0:W]
    # v1 is flat warm-black blobs: give the rock interior value (vertical strata, wet sheen near the top edges), the guide bright
    nz = tile_noise(W, H, 8, 24, 71, 2); nz2 = tile_noise(W, H, 4, 32, 72, 1); nz3 = tile_noise(W, H, 32, 6, 73, 2)
    dist = np.zeros((H, W)); left = np.zeros((H, W))
    for y in range(H):
        dist[y] = np.where(static[y], dist[y - 1] + 1 if y else 1, 0)
    for x in range(W):
        left[:, x] = np.where(static[:, x], left[:, x - 1] + 1 if x else 1, 0)
    # rock: vertical strata and dark crevices, horizontal ledges, a wet lit band on every sky-facing edge and left face
    v = 0.30 + 0.22 * nz + 0.10 * nz3
    v -= 0.28 * (nz2 > 0.68)                                       # crevices
    v -= 0.12 * ((yy + (nz3 * 12).astype(int)) % 11 == 0)          # ledges
    v += 0.40 * np.exp(-dist / 2.5) + 0.18 * np.exp(-left / 2.0)
    v = np.where(rgb.sum(-1) > 60, v + 0.1, v)                     # v1's lit details (railings, caps)
    g = lerp(hexc('1d2230'), hexc('8a9ab8'), np.clip(v, 0, 1)[..., None])
    warm = (rgb[..., 0] > rgb[..., 2] + 30) & static
    g = np.where(warm[..., None], hexc('e09a3a'), g)
    g = np.where(static[..., None], g, 128)
    G = np.asarray(Image.fromarray(g.astype(np.uint8)).resize((WS, HS), Image.NEAREST), float)
    A3 = np.asarray(Image.fromarray((static * 255).astype(np.uint8)).resize((WS, HS), Image.NEAREST), float)
    return Image.fromarray(G.astype(np.uint8)), Image.fromarray(A3.astype(np.uint8))


def paint_guides():
    f = guide_far(); f.image().save(f'{SRC}/guide_far.png'); edges_of(f.image(), lo=8).save(f'{SRC}/edge_far.png')
    m, ma = guide_mid(); m.save(f'{SRC}/guide_mid.png'); ma.save(f'{SRC}/guide_mid_alpha.png')
    edges_of(m, lo=10).save(f'{SRC}/edge_mid.png')
    far1 = box_down(f.image()); mid1 = box_down(m); al = key_mid(f'{SRC}/guide_mid_alpha.png')
    comp = np.where(al[..., None], mid1, far1); Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(f'{SRC}/guide_preview.png')


RENDER = {
    'far': dict(prompt=PROMPT_FAR, seed=1, denoise=0.72, cn=0.5, cn_end=0.65, pix=0.6, guide_blur=1.3),
    'mid': dict(prompt=PROMPT_MID, seed=1, denoise=0.45, cn=0.6, cn_end=0.8, pix=0.6, guide_blur=0.8, seam_band=96),
}
PICK = {'far': ('', 3), 'mid': ('b', 2)}   # (sweep tag, seed) picked by eye


def do_sweep(layer, seeds, tag=''):
    A.use_prefix(B); kw = dict(RENDER[layer]); kw.pop('seed'); kw.pop('seam_band', None)
    A.sweep(SRC, layer, seeds=seeds, tag=tag, **kw)


def do_finish():
    A.use_prefix(B)
    for layer in ('far', 'mid'):
        tag, seed = PICK[layer]
        A.finish(SRC, layer, seed, RENDER[layer]['prompt'], RENDER[layer]['pix'], seam_band=RENDER[layer].get('seam_band', 128), tag=tag)


# ------------------------------------------------------------------------------------------------ frames
FAR_GRADE = dict(black=12, white=300, gamma=0.8, sat=1.1, tint=(118, 104, 160), tint_k=0.3)   # pulled toward v1's bruised violet


def far_base():
    """The v2 static base at 1x (float, before the palette lock)."""
    a = grade(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float), **FAR_GRADE)
    b = box_down(a)
    # soft knee on the storm sky: the game's ray/bloom pass turned the render's lit horizon strata into a big pale halo
    # behind the player (SP4, SP11, SP15), so the sky's highlights are compressed; the flashes add the brightness back
    lum = (b * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    tgt = np.where(lum > 30, 30 + (lum - 30) * 0.5, lum)
    sky = (np.arange(H) < HZ)[:, None, None]
    return np.where(sky, b * tgt / np.maximum(lum, 1), b)


def spire_mask_1x(grow=1):
    fs = SB.far_static(); m = np.zeros((H, W), bool)
    for (x, y) in fs.spire:
        if 0 <= y < H: m[y, x % W] = True
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(1 + 2 * grow)), float) > 127


SPM = None


def draw_bolts(f):
    """The v1 bolts (same geometry: spire_bg.main_bolt / bolt_path), drawn as clean 1-2 px strokes in the BOLT ramp so they
    read on any v2 sky value: frame 4 full (2 px core, glow, all branches, strike splash + sea column), 5 fade, 6 ghost,
    7 thin far bolt + cloud crawlers, 8 thin fade."""
    rgb = np.zeros((H, W, 3)); m = np.zeros((H, W), bool); C = [hexc(c) for c in BOLT]
    def put(x, y, c):
        if 0 <= y < H: rgb[y, x % W] = c; m[y, x % W] = True
    def stroke(pts, core, glow=None, wide=False, skip=None):
        if glow is not None:
            for (x, y) in pts:
                if skip and skip(x, y): continue
                for dx in ((-1, 2) if wide else (-1, 1)): put(x + dx, y, glow)
        for (x, y) in pts:
            if skip and skip(x, y): continue
            put(x, y, core)
            if wide: put(x + 1, y, core)
    if f in (4, 5, 6):
        trunk, branches = SB.main_bolt()
        if f == 4:
            stroke(trunk, C[3], C[2], wide=True)
            for br in branches: stroke(br, C[3], C[1])
            bx, by = SB.BOLT_BOT
            for y in range(HZ + 1, H):
                if (y - HZ) % 3 != 2: put(bx, y, C[2]); put(bx + (1 if y % 2 else -1), y, C[1])
            for (dx, dy) in ((-2, 0), (2, 0), (-3, 1), (3, 1), (-1, -1), (1, -1), (0, -2)): put(bx + dx, by + dy, C[3] if abs(dx) < 2 else C[2])
        elif f == 5:
            stroke(trunk, C[2], C[1]); stroke(branches[1], C[1])
        else:
            stroke(trunk, C[0], skip=lambda x, y: y % 3 == 0 or y < SB.BOLT_TOP[1] + 20)
    if f in (7, 8):
        thin = SB.bolt_path(SB.THIN_TOP, SB.THIN_BOT, 41, 0.25, 5)
        stroke(thin, C[2] if f == 7 else C[0], C[1] if f == 7 else None)
        if f == 7:
            for (p0, p1, sd) in (((90, 52), (150, 62), 51), ((118, 56), (100, 80), 52)):
                stroke(SB.bolt_path(p0, p1, sd, 0.3, 4), C[1])
    return rgb, m


def far_frames():
    global SPM
    base = far_base()
    # the v2 tower is a little wider than the v1 one: its dark stone near the axis joins the mask
    lumb = (base * [0.299, 0.587, 0.114]).sum(-1); yy, xx = np.mgrid[0:H, 0:W]
    rowmed = np.median(lumb, axis=1, keepdims=True)
    near = (np.abs((xx - SB.SPX + W / 2) % W - W / 2) < 30) & (yy > 40) & (yy < HZ + 3) & (lumb < rowmed * 0.75)
    SPM = spire_mask_1x(1) | near
    acc = pick_accents(base, FAR_PAL, n=6)
    P = [tuple(c) for c in FAR_PAL] + acc
    fr = v1_frames('far'); med = v1_median()
    lum_b = (base * [0.299, 0.587, 0.114]).sum(-1)
    boltset = {tuple(hexc(c).astype(int)) for c in BOLT}
    out = []
    for f in range(10):
        v = fr[f][..., :3]; delta = v - med
        img = base.copy()
        if f < 4 or f == 9:
            # rain / whitecaps / spark: v1's small moving deltas, a touch stronger on the lifted base
            dl = (delta * [0.299, 0.587, 0.114]).sum(-1)
            mv = np.abs(dl) > 4
            img = np.where(mv[..., None], np.clip(img + delta * 1.25, 0, 255), img)
        if f >= 4:
            dl = np.clip((delta * [0.299, 0.587, 0.114]).sum(-1), 0, None)
            # normalised blur that ignores the v1 spire (it had no light delta, which would leave a dark halo round the v2 tower)
            def gb(a_): return np.asarray(Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), float)
            L = gb(dl * ~SPM) / np.maximum(gb(~SPM * 255.0), 1)
            L = np.where(SPM, L * 0.35, L)                              # the stone itself catches a little
            sky = (np.arange(H) < HZ)[:, None]
            under = np.clip(lum_b / 120, 0, 1)                          # brighter cloud parts catch more of the flash
            k = np.where(sky, L * (0.6 + 1.4 * under), L * 0.9)
            img = img + k[..., None] * np.array([215, 225, 245]) * 1.05 - k[..., None] * img * 0.2
            bolt_rgb, isbolt = draw_bolts(f)
        q = palette_lock(np.clip(img, 0, 255), P, dither_flat=True, dk=0.4)
        if f < 4: q = majority(q)
        q = np.where(isbolt[..., None], bolt_rgb, q) if f >= 4 else q
        out.append(q)
    return out, acc


FAR_MS = [130, 130, 130, 130, 60, 90, 150, 70, 100, 150]   # v1 frame timings (gen_spire_env.py)
MID_GRADE = dict(black=10, white=760, gamma=0.95, sat=0.8)


def mid_frames():
    fr, static, moving = mid_static()
    a = grade(np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float), **MID_GRADE)
    s = box_down(a)
    al_static = A.key_color(f'{SRC}/mid_render.png', f'{SRC}/guide_mid_alpha.png', env=1, union=0.5, close=True) & static | static
    acc = pick_accents(s, MID_PAL, n=0, mask=al_static)
    P = [tuple(c) for c in MID_PAL]
    q = palette_lock(s, P, dither_flat=False)
    q = majority(q, alpha=al_static)
    # wet rim light on sky-facing edges
    q = rim(q, al_static, hexc('5a6a88'))
    out = []
    for f in range(4):
        v = fr[f]; mv = moving & (v[..., 3] > 0)
        rgb = v[..., :3]
        # v1 moving pixels: sails (dark) re-graded onto the v2 stone ramp, foam bursts kept
        lum = (rgb * [0.299, 0.587, 0.114]).sum(-1)
        foam = (rgb[..., 2] > 90)
        sail = lerp(hexc('12151e'), hexc('3a4256'), np.clip(lum / 40, 0, 1)[..., None])
        mvcol = np.where(foam[..., None], rgb, sail)
        alf = al_static | mv
        fq = np.where(mv[..., None], mvcol, q)
        fq = np.where(alf[..., None], fq, 0)
        out.append((fq, alf))
    return out


def build(ase=True):
    import asebuild
    fars, acc_f = far_frames()
    mids = mid_frames()
    far_ims = [to_rgba(f) for f in fars]; mid_ims = [to_rgba(m, a) for m, a in mids]
    for i, im in enumerate(far_ims): im.save(f'{SRC}/out_far_{i}.png')
    for i, im in enumerate(mid_ims): im.save(f'{SRC}/out_mid_{i}.png')
    far_ims[0].save(f'{SRC}/out_far.png'); mid_ims[0].save(f'{SRC}/out_mid.png')
    preview(far_ims[0], mid_ims[0], TINT, f'{SRC}/preview.png')
    sheet = Image.new('RGBA', (W * 2 + 4, (H + 4) * 5), (17, 17, 17, 255))
    for i, im in enumerate(far_ims): sheet.paste(im, ((i % 2) * (W + 4), (i // 2) * (H + 4)))
    sheet.save(f'{SRC}/far_frames.png')
    st = {'far': stats(far_ims[0]), 'mid': stats(mid_ims[0]), 'accents_far': ['%02x%02x%02x' % c for c in acc_f],
          'far_colors_all': len({tuple(p) for im in far_ims for p in np.asarray(im).reshape(-1, 4)})}
    print(json.dumps(st)); json.dump(st, open(f'{SRC}/stats.json', 'w'), indent=1)
    if ase:
        asebuild.build(f'bg_{B}_far', W, H, ['Layer'], [{'ms': ms, 'cels': {'Layer': im}} for ms, im in zip(FAR_MS, far_ims)],
                       [('loop', 0, 3), ('flash', 4, 6), ('flash2', 7, 9)])
        asebuild.build(f'bg_{B}_mid', W, H, ['Layer'], [{'ms': 150, 'cels': {'Layer': im}} for im in mid_ims], [('loop', 0, 3)])
        for name, n, tags in ((f'bg_{B}_far', 10, [('loop', 0, 3), ('flash', 4, 6), ('flash2', 7, 9)]), (f'bg_{B}_mid', 4, [('loop', 0, 3)])):
            j = json.load(open(os.path.join(ROOT, 'assets', f'{name}.json')))
            assert len(j['frames']) == n and [(t['name'], t['from'], t['to']) for t in j['meta']['frameTags']] == tags, name


if __name__ == '__main__':
    a = sys.argv
    if '--guide' in a or '--sweep' in a: paint_guides()
    if '--sweep' in a:
        i = a.index('--sweep'); do_sweep(a[i + 1], [int(s) for s in a[i + 2].split(',')], tag=(a[i + 3] if len(a) > i + 3 and not a[i + 3].startswith('--') else ''))
    elif '--finish' in a: do_finish()
    if '--guide' not in a and '--sweep' not in a: build(ase='--no-ase' not in a)
