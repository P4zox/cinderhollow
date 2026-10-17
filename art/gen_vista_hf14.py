#!/usr/bin/env python3
"""HF14 Frostbitten Overlook vista (agent V1, docs/v17/vista_v1.md): the aurora over the frozen reservoir.

  python3 art/gen_vista_hf14.py                build assets/vista_hf14_{far,mid,aur} from the saved renders in art/bg_src/vista_hf14/
  python3 art/gen_vista_hf14.py --guide        only (re)paint the guides
  python3 art/gen_vista_hf14.py --sweep far 1,2,3 [--dn x --cn x --pix x --tag t]   pass-1 renders (ComfyUI :8188) + sheet
  python3 art/gen_vista_hf14.py --render       guides + render the picked seeds (RENDER), then build

Lore (rb_9): "The reservoir froze in one night, all the way down ... The sky does this every winter now, green and slow, as if
something above the clouds is breathing on a cold glass." The regular hoarfrost backdrop is a full moon over snow ranges and
the aqueduct; this view has no moon: the aurora is the only light, a great folded curtain over a basin of black ice that
mirrors it, the dam's arches crossing the ice toward the far shore.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import lerp

ROOM = 'HF14'
SRC = os.path.join(HERE, 'bg_src', 'vista_hf14')
TINT = '#070a16'
FAR = dict(sheet='vista_hf14_far', w=424, h=232, fac=0.03, vfac=0.05, x=-4, dy=12)
MID = dict(sheet='vista_hf14_mid', w=424, h=232, fac=0.1, vfac=0.05, x=-4, dy=12)
HOR = 150

PROMPT_FAR = ('pixel art, dark fantasy winter night landscape, a vast frozen lake in a deep mountain basin seen from a high cliff, '
              'black mirror ice reflecting a huge aurora borealis, folded green and violet aurora curtains with fine vertical rays '
              'arching across a dense starry sky, jagged snowy mountain peaks on the far shore lit faintly green, an old stone '
              'aqueduct of tall arches crossing the ice, serene and silent, no moon, highly detailed, deep navy blue, teal and pale '
              'green palette')
PROMPT_MID = ('pixel art, dark fantasy winter night, snow covered pine trees and frosted rocks on a cliff edge in the foreground, '
              'dark silhouettes rim lit by green aurora light, a vast frozen lake and aurora behind, highly detailed, deep navy blue '
              'and teal palette')
RENDER = {'far': dict(seed=2, dn=0.62, cn=0.5, cn_end=0.65, pix=0.5),
          'mid': dict(seed=2, dn=0.58, cn=0.55, cn_end=0.7, pix=0.55)}

# the aurora: ribbons as (lower-edge polyline control points (x, y), curtain height, colour bias); a fold over the lake
RIBBONS = [
    dict(pts=[(-30, 14), (40, 34), (110, 58), (170, 80), (215, 98), (240, 104), (262, 100), (290, 80), (330, 50), (380, 30), (450, 16)], hgt=52, k=1.0, seed=1),
    dict(pts=[(60, 64), (140, 70), (220, 66), (300, 74), (360, 84), (450, 80)], hgt=26, k=0.5, seed=2),
    dict(pts=[(-30, 112), (40, 118), (110, 124), (170, 128)], hgt=18, k=0.4, seed=3),
]


def ribbon_field(G, rb, t=0.0):
    """Intensity field of one aurora curtain: bright lower edge, rays rising and fading, a violet fringe on top."""
    xs = np.array([p[0] for p in rb['pts']], float); ys = np.array([p[1] for p in rb['pts']], float)
    xx = G.X[0]
    yb = L.smooth_curve(xs, ys, xx) + 3 * np.sin(xx / 23 + rb['seed'] + t) + 1.5 * np.sin(xx / 7.3 + t * 1.7)
    hgt = rb['hgt'] * (0.75 + 0.25 * np.sin(xx / 41 + rb['seed'] * 2 + t * 0.6))
    d = (yb[None, :] - G.Y)                                     # height above the lower edge
    up = np.clip(d / hgt[None, :], 0, 1); edge = np.clip(1 + d / 1.6, 0, 1) * (d < 0) + (d >= 0)
    rays = 0.55 + 0.45 * np.clip(G.noise(2.2, 60, rb['seed'] * 7 + int(t * 10), 2) * 1.6 - 0.3, 0, 1)
    body = (1 - up) ** 1.4 * edge * rays * (d > -1.6)
    fringe = np.exp(-((up - 0.9) / 0.1) ** 2) * (d > 0) * rays
    return body * rb['k'], fringe * rb['k']


def sky(G):
    G.rgb = G.vgrad([(0, (6, 8, 22)), (50, (10, 15, 36)), (100, (16, 26, 52)), (135, (22, 42, 64)), (HOR, (30, 58, 74)), (HOR + 1, (12, 22, 36))])
    rng = np.random.default_rng(9)
    for _ in range(170):
        x, y = rng.uniform(0, G.w), rng.uniform(0, HOR - 10); b = rng.uniform(0.3, 1.0) * (1 - y / (HOR + 20))
        G.fill(G.ellipse(x, y, 0.5, 0.5, 2), (210, 226, 255), b)
    for _ in range(14):
        x, y = rng.uniform(0, G.w), rng.uniform(0, 100)
        G.fill(G.ellipse(x, y, 0.8, 0.8, 2), (235, 244, 255)); G.glow(x, y, 3, 3, (60, 70, 90), 1, 2)


def aurora(G, t=0.0, k=1.0):
    for rb in RIBBONS:
        body, fringe = ribbon_field(G, rb, t)
        G.add(body, (70, 230, 160), 0.95 * k); G.add(body ** 3, (120, 255, 210), 0.5 * k)
        G.add(fringe, (110, 60, 170), 0.28 * k)


def land(G):
    rng = np.random.default_rng(4)
    # far shore: jagged peaks, snow faces lit green on the left flanks
    prof = L.profile(G.w, 13, HOR - 2, 22, cells=((46, 1.0), (15, 0.6), (5, 0.25)))
    xx = np.arange(G.w + 1, dtype=float)
    prof = np.minimum(prof, HOR - 2 - 44 * np.clip(1 - np.abs(xx - 300) / 46, 0, 1) ** 1.25 - 6 * np.abs(np.sin(xx / 3.1)) * np.clip(1 - np.abs(xx - 300) / 46, 0, 1))
    prof = np.minimum(prof, HOR - 2 - 30 * np.clip(1 - np.abs(xx - 352) / 34, 0, 1) ** 1.2)
    prof = np.minimum(prof, HOR - 2 - 24 * np.clip(1 - np.abs(xx - 92) / 50, 0, 1) ** 1.3)
    prof2 = L.profile(G.w, 14, HOR, 16, cells=((30, 1.0), (9, 0.5), (3, 0.2)))
    for pr, col, lit in [(prof, (26, 36, 58), (88, 130, 140)), (prof2, (16, 24, 42), (60, 96, 110))]:
        pts = [(x, pr[x]) for x in range(G.w + 1)] + [(G.w, HOR + 1), (0, HOR + 1)]
        m = G.poly(pts)
        xi = np.clip(G.X.astype(int), 0, G.w); slope = np.gradient(pr)[xi]
        depth = G.Y - pr[xi]
        litm = np.clip(-slope * 0.6, 0, 1) * np.clip(1 - depth / 24, 0, 1)
        snow = np.clip(1 - (depth - 3 * G.noise(4, 3, 5, 2)) / 7, 0, 1)
        img = lerp(np.array(col, float), np.array(lit, float), (litm * 0.6 + snow * 0.5).clip(0, 1)[..., None])
        G.fill_img(m, img)
    # the ice: black mirror with the sky and aurora reflected, cracks and snow drifts
    below = np.clip((G.Y - HOR) * 3, 0, 1)
    ice = G.vgrad([(HOR, (24, 46, 62)), (HOR + 20, (12, 24, 40)), (232, (6, 12, 24))])
    G.fill_img(below, ice)
    R = L.VG(G.w, G.h); R.rgb[:] = 0
    for rb in RIBBONS:
        body, fringe = ribbon_field(R, rb, 0.0)
        R.add(body, (60, 200, 150), 0.7); R.add(fringe, (90, 50, 140), 0.35)
    refl = R.rgb[::-1]                                              # mirror about the horizon
    sh = int((2 * HOR - G.h) * L.S)
    m = np.zeros_like(G.rgb)
    if sh >= 0: m[sh:] = refl[:G.HS - sh]
    else: m[:sh] = refl[-sh:]
    m = np.asarray(Image.fromarray(np.clip(m, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((2.5 * L.S, 0.8 * L.S))) if False else
                   Image.fromarray(np.clip(m, 0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2)), float)
    fade = np.clip(1 - (G.Y - HOR) / 110, 0, 1) * below * (0.75 + 0.25 * np.sin(G.Y * 2.1 + G.noise(40, 2, 3, 2) * 4))
    G.rgb = G.rgb + m * (1.0 * fade)[..., None]
    # mountain reflection
    for x in range(0, G.w, 1): pass
    # cracks: long thin pale lines radiating across the ice
    segs = []
    for i in range(16):
        x, y = rng.uniform(0, G.w), rng.uniform(HOR + 8, 228); ang = rng.uniform(-0.25, 0.25) + (math.pi if rng.random() < 0.5 else 0)
        for j in range(int(rng.uniform(8, 24))):
            nx, ny = x + math.cos(ang) * 3, y + math.sin(ang) * 0.8; segs.append((x, y, nx, ny, 0.45)); x, y = nx, ny; ang += rng.normal(0, 0.3)
    G.fill(G.lines(segs) * below, (120, 170, 190), 0.6)
    # snow drifts on the ice near the viewer
    nz = G.noise(30, 4, 6, 3)
    G.fill(np.clip((nz - 0.58) * 6, 0, 1) * np.clip((G.Y - 185) / 20, 0, 1), (70, 96, 116), 0.8)
    # the dam: a long aqueduct of arches crossing the ice from the left to the far shore, receding
    x0 = -14.0; G.aq = np.zeros_like(G.X)
    for i in range(40):
        f = min(1, (x0 + 14) / 214); y0 = 206 - f * 54; s = 1 - 0.78 * f
        aw, ah, pw = 16 * s, 30 * s, 4 * s
        if x0 > 200: break
        deck = y0 - ah - 4 * s
        box = G.poly([(x0, deck - 3 * s), (x0 + aw + pw, deck - 3 * s), (x0 + aw + pw, y0), (x0, y0)]); G.aq = np.maximum(G.aq, box)
        G.fill(box, (30, 40, 62))
        arch = [(x0 + pw, y0)] + [(x0 + pw + aw / 2 - aw / 2 * math.cos(a), deck + 4 * s + (ah - 4 * s) * 0.35 - (ah * 0.55) * math.sin(a)) for a in np.linspace(0, math.pi, 12)] + [(x0 + pw + aw, y0)]
        G.fill(G.poly(arch), (12, 22, 38))
        G.fill(G.poly([(x0, deck - 3 * s), (x0 + aw + pw, deck - 3 * s), (x0 + aw + pw, deck - 1.8 * s), (x0, deck - 1.8 * s)]), (120, 160, 170))   # snow on the deck
        x0 += aw + pw


def guide_far():
    G = L.VG(FAR['w'], FAR['h'])
    sky(G); aurora(G); land(G)
    return G


def guide_mid():
    G = guide_far(); G.a = np.zeros_like(G.X)
    rng = np.random.default_rng(21)
    def pine(cx, base, h, w):
        pts = [(cx, base - h)]
        n = 7
        for i in range(1, n + 1):
            y = base - h + h * i / n; ww = w * (i / n) ** 0.9
            pts.append((cx + ww, y)); pts.append((cx + ww * 0.45, y - h / n * 0.25))
        pts = [pts[0]] + pts[1:][::2][:n]
        L_ = [(cx - (x - cx), y) for x, y in pts[1:]][::-1]
        return pts + [(cx + w * 0.15, base + 2), (cx - w * 0.15, base + 2)] + L_
    m = np.zeros_like(G.X)
    # rocks + pines on the near cliff edges (corners), dark with green rim
    rockL = G.poly([(-4, 232), (-4, 186), (20, 180), (46, 188), (70, 196), (96, 206), (130, 214), (150, 232)])
    rockR = G.poly([(330, 232), (350, 210), (380, 200), (404, 194), (428, 190), (428, 232)])
    m = np.maximum(rockL, rockR)
    for cx, base, h, w in [(14, 184, 44, 8), (32, 186, 30, 6), (52, 191, 22, 5), (78, 200, 16, 4), (392, 197, 38, 7), (410, 194, 26, 5), (370, 204, 18, 4)]:
        m = np.maximum(m, G.poly(pine(cx, base, h, w)))
    G.fill_img(m, lerp(np.array((10, 16, 28), float), np.array((24, 34, 52), float), G.noise(5, 5, 3, 2)[..., None]))
    up = np.roll(m, 2 * L.S, axis=0) < 0.5
    G.add(m * up, (60, 150, 130), 0.9)
    snow = np.clip(G.noise(3, 2, 8, 2) * 2 - 0.9, 0, 1) * m
    G.add(snow, (60, 80, 96), 0.8)
    return G


def aur_frames():
    """The animated aurora overlay: two shimmer states of the curtains (drawn additively, crossfading, by 85v_v1.js fx)."""
    out = []
    for t in (0.0, 1.7):
        G = L.VG(FAR['w'], FAR['h']); G.rgb[:] = 0
        aurora(G, t=t, k=0.8)
        a = V.box_down(G.rgb, FAR['w'], FAR['h'])
        out.append(a)
    return out


SHORE = 168   # the render put the far shore lower than the guide's horizon


def far_post(a):
    """Every seed broke the ice into land patches; the ice is rebuilt as black mirror ice (as the pilot built the cathedral's
    water): the sky, peaks and aurora mirrored about the shore, darkened and blue-shifted, smeared along the rows with a faint
    ripple, over 30 % of the render's own frost patches. The dam's arches (the guide's mask) keep the render's pixels."""
    S = L.S; hh, ww = a.shape[:2]; y0 = SHORE * S
    out = a.copy(); rng = np.random.default_rng(3)
    for y in range(y0, hh):
        sy = int(y0 - (y - y0) * 2.4)                    # seen from high above: the near ice mirrors the high sky
        if sy < 0: break
        row = a[sy].copy()
        shift = int(round(2.0 * S * math.sin(y / (1.3 * S)) + rng.normal(0, 0.6) * S * (y - y0) / (hh - y0)))
        row = np.roll(row, shift, axis=0)
        k = 3 + int((y - y0) / (hh - y0) * 6); ker = np.ones(k) / k
        row = np.stack([np.convolve(np.pad(row[:, c], k, mode='edge'), ker, mode='same')[k:-k] for c in range(3)], -1)
        f = (y - y0) / (hh - y0)
        refl = row * (0.8 - 0.3 * f) * np.array([0.8, 0.95, 1.1])
        wv = min(1, (y - y0) / (2.5 * S))
        out[y] = a[y] * (1 - 0.7 * wv) + refl * 0.7 * wv
    aq = np.asarray(Image.open(f'{SRC}/aq_mask.png').resize((ww, hh), Image.BILINEAR).filter(ImageFilter.MaxFilter(9)), float)[..., None] / 255
    out = out * (1 - aq) + a * aq
    return out


def add_stars(q, pal):
    """1 px stars (and a few 2 px ones with a dim cross) on the dark sky, away from the aurora light."""
    rng = np.random.default_rng(17); q = q.copy(); h, w = q.shape[:2]
    lum = q @ np.array([0.299, 0.587, 0.114]); green = q[..., 1] - q[..., 0]
    for _ in range(150):
        x, y = int(rng.uniform(1, w - 1)), int(rng.uniform(1, 96))
        if lum[y, x] > 60 or green[y, x] > 40: continue
        b = rng.random()
        q[y, x] = (238, 246, 255) if b > 0.85 else (196, 214, 240) if b > 0.45 else (150, 170, 210)
        if b > 0.97:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): q[y + dy, x + dx] = (150, 170, 210)
    return q


def aur_overlay(q):
    """The aurora's shimmer, taken from the painting itself: its green light (sky and mirror), modulated by drifting vertical
    rays; two frames that the fx crossfades and draws additively."""
    h, w = q.shape[:2]; a = q.astype(float)
    A = np.clip((a[..., 1] - np.maximum(a[..., 0], a[..., 2] * 0.85) - 8) / 90, 0, 1)
    out = []
    for seed in (1, 2):
        rng = np.random.default_rng(seed); n = rng.random(w // 3 + 3); xi = np.arange(w) / 3; i0 = xi.astype(int); t = xi - i0
        rays = n[i0] * (1 - t) + n[i0 + 1] * t
        m = A * np.clip(rays * 1.6 - 0.4, 0, 1)[None, :]
        col = np.zeros((h, w, 3)); col[:] = (120, 255, 200); col[m > 0.6] = (190, 255, 228)
        alpha = (np.round(m * 4) / 4 * 200).astype(np.uint8)
        out.append(Image.fromarray(np.dstack([col.astype(np.uint8), alpha]), 'RGBA'))
    return out


def build(no_ase=False):
    far_hi = far_post(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float))
    s = V.box_down(far_hi, FAR['w'], FAR['h'])
    pal = L.kpal(s, 40) + [(196, 214, 240), (150, 170, 210), (238, 246, 255)]   # + star whites (k-means drops 1 px stars)
    far = L.pixelize(far_hi, FAR['w'], FAR['h'], pal, dk=0.35)
    mid_hi = V.grade(np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float), black=4, white=280, gamma=0.95)
    al = np.asarray(Image.open(f'{SRC}/alpha_mid.png').convert('L').resize((MID['w'], MID['h']), Image.BOX), float) / 255 >= 0.5
    mpal = L.kpal(V.box_down(mid_hi, MID['w'], MID['h']), 14, mask=al)
    mid = np.where(al[..., None], L.pixelize(mid_hi, MID['w'], MID['h'], mpal, dk=0, alpha=al), 0)
    far = add_stars(far, pal)
    frames = aur_overlay(far)
    far_im, mid_im = L.to_rgba(far), L.to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png'); frames[0].save(f'{SRC}/out_aur0.png')
    L.comp_preview(ROOM, [(FAR, far_im), (MID, mid_im)], TINT, f'{SRC}/preview.png')
    print('far colours', len(pal), 'mid colours', len(mpal))
    if not no_ase:
        L.ase('vista_hf14_far', [far_im]); L.ase('vista_hf14_mid', [mid_im]); L.ase('vista_hf14_aur', frames)


if __name__ == '__main__':
    args = sys.argv[1:]
    os.makedirs(SRC, exist_ok=True)
    if '--guide' in args or '--sweep' in args or '--render' in args:
        G = guide_far(); G.save(SRC, 'far'); guide_mid().save(SRC, 'mid')
        Image.fromarray((G.aq * 255).astype(np.uint8)).resize((FAR['w'], FAR['h']), Image.BOX).save(f'{SRC}/aq_mask.png')
    if '--sweep' in args:
        i = args.index('--sweep'); layer = args[i + 1]; seeds = [int(s) for s in args[i + 2].split(',')]
        R = dict(RENDER[layer])
        for k in ('dn', 'cn', 'pix'):
            if f'--{k}' in args: R[k] = float(args[args.index(f'--{k}') + 1])
        tag = args[args.index('--tag') + 1] if '--tag' in args else ''
        L.sweep(ROOM, SRC, layer, PROMPT_FAR if layer == 'far' else PROMPT_MID, seeds, R['dn'], R['cn'], R['cn_end'], R['pix'], tag=tag)
    elif '--render' in args:
        for layer in ('far', 'mid'):
            R = RENDER[layer]
            L.sweep(ROOM, SRC, layer, PROMPT_FAR if layer == 'far' else PROMPT_MID, [R['seed']], R['dn'], R['cn'], R['cn_end'], R['pix'], tag=R.get('tag', ''))
            L.pick(SRC, layer, R['seed'], tag=R.get('tag', ''))
        build('--no-ase' in args)
    elif '--guide' not in args:
        build('--no-ase' in args)
