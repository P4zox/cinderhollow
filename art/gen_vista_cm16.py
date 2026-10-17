#!/usr/bin/env python3
"""CM16 The Moonlit Conservatory: painted vista (agent V2, docs/v17/vista_v2.md).

Seen through the glasshouse's gothic mullions: a pale silver moon (a faint rose ring: the Manor's red moon gone quiet) over the
Countess's night garden. The east wing of the Manor on the left with one candle-lit window, a reflecting canal running to a
domed garden folly under the moon, cypress rows and an iron garden wall on the right, thin moonlit cloud bands and stars.

  python3 art/gen_vista_cm16.py               build assets/vista_cm16_{sky,far,mid} from the saved renders
  python3 art/gen_vista_cm16.py --guide       paint the guides only (art/bg_src/vista_cm16/)
  python3 art/gen_vista_cm16.py --sweep a 1,2,3   seed sweep of composition a (full / plate guides) into sweep/
  python3 art/gen_vista_cm16.py --render      re-render the picked seeds (ComfyUI on :8188), then build
"""
import math, os, sys, shutil
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import hexc, smooth, lerp

ROOM = 'cm16'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
W, H = 416, 224                     # every layer: wrap:false at x=0 (cam.x 0..192, fac <= 0.14 -> 27 px of travel)
MOON = (236, 64, 24)                # painting px (screen y = row - 8): x, y, radius
HZ = 170                            # far shore line
MOON_R = (238, 62, 24)              # where the picked render actually put the moon (1x)

PROMPT = ('pixel art, dark fantasy, gothic night garden of a vampire manor under a huge pale silver full moon with a faint rose halo, '
          'thin silver-edged clouds, stars, a long still reflecting canal mirroring the moon, a small domed marble garden folly on an islet, '
          'tall dark cypress trees, the gothic east wing of a manor with pointed spires and one warm candle-lit window, '
          'iron garden fence with spear finials, dead rose hedges, moonlight, deep indigo and violet night palette with silver highlights, '
          'side-scroller game background, atmospheric depth, mist over the water, highly detailed, serene, beautiful')
PROMPT_SKY = ('pixel art, night sky, a huge pale silver full moon with a faint rose halo, thin silver-edged clouds drifting across, '
              'scattered stars, deep indigo and violet, soft moonlight glow, serene, beautiful, highly detailed')
RENDER = dict(full=dict(seed=3, denoise=0.62, cn=0.5, cn_end=0.65, pix=0.45),
              sky=dict(seed=3, denoise=0.55, cn=0.4, cn_end=0.6, pix=0.45),
              plate=dict(seed=3, denoise=0.62, cn=0.5, cn_end=0.65, pix=0.45))


# ------------------------------------------------------------------------------------------------- guide
def paint():
    """-> dict of 3x canvases (full, sky, plate) and masks (far, mid)."""
    C = L.Canvas(W, H)
    X, Y = C.X, C.Y
    mx, my, mr = MOON
    # sky: indigo zenith, a pale lavender bloom around the moon, a cooler band near the horizon
    C.rgb = C.vgrad([(0, (16, 12, 34)), (70, (34, 28, 66)), (150, (58, 52, 96)), (HZ, (84, 80, 120))])
    dm = np.sqrt((X - mx) ** 2 + ((Y - my) * 1.15) ** 2)
    C.add(np.exp(-(dm / 70) ** 2), (110, 104, 150), 1.0)
    C.add(np.exp(-(dm / 34) ** 2), (120, 110, 140), 0.9)
    C.add(np.clip(1 - np.abs(dm - mr * 1.7) / 6, 0, 1), (70, 34, 50), 0.35)      # a faint rose ring
    nz = C.noise(60, 10, 7, 4)
    # cloud bands: long thin strata, lit silver on top where near the moon
    for (cy, th, x0, x1, k) in [(36, 5, 120, 400, 1.0), (52, 3, 0, 210, 0.8), (88, 6, 150, 416, 0.9), (104, 4, 20, 260, 0.7), (128, 7, 230, 416, 0.6), (140, 5, 0, 170, 0.5)]:
        wob = cy + 3 * np.sin(X / 37 + cy) + 4 * (nz - 0.5)
        band = np.clip(1 - np.abs(Y - wob) / th, 0, 1) * smooth(x0 - 30, x0 + 20, X) * (1 - smooth(x1 - 20, x1 + 30, X))
        lit = np.exp(-(np.sqrt((X - mx) ** 2 + (Y - my) ** 2) / 120) ** 2)
        C.fill(band, lerp(np.array((44, 38, 72.)), np.array((200, 196, 224.)), lit[..., None] * k), 0.85)
        C.add(band * (Y < wob - th * 0.3), (150, 150, 180), 0.5 * k * lit)
    # stars
    rng = np.random.default_rng(16)
    for _ in range(70):
        sx, sy = rng.uniform(0, W), rng.uniform(2, 120)
        if math.hypot(sx - mx, sy - my) < 48: continue
        C.fill(C.ellipse(sx, sy, 0.7, 0.7), (230, 228, 250), rng.uniform(0.5, 1))
    # the moon: ivory disc, soft maria
    md = C.ellipse(mx, my, mr, mr)
    face = 240 - 26 * np.clip(C.noise(9, 9, 3, 3) - 0.45, 0, 1) * 3 - 10 * ((X - mx) / mr) ** 2
    C.fill(md, np.stack([face, face - 4, face - 10], -1))
    sky = C.rgb.copy()

    # ---- far: hills in mist, the canal with the moon's road, the folly, the manor wing (left), cypress rows (right)
    far = np.zeros(C.rgb.shape[:2])
    hill = 150 + 6 * np.sin(X / 41) + 4 * np.sin(X / 17 + 1)
    m = (Y > hill).astype(float); C.fill(m, (52, 50, 84)); far = np.maximum(far, m)
    hill2 = 160 + 5 * np.sin(X / 29 + 2)
    m = (Y > hill2).astype(float); C.fill(m, (40, 36, 64)); far = np.maximum(far, m)
    # the water: from the shore down; moon road + reflections
    wm = (Y > HZ).astype(float)
    wat = C.vgrad([(HZ, (66, 64, 104)), (H, (20, 18, 40))])
    C.rgb = C.rgb * (1 - wm[..., None]) + wat * wm[..., None]
    road = np.exp(-((X - mx) / (5 + (Y - HZ) * 0.35)) ** 2) * wm
    rip = 0.6 + 0.4 * np.sin(Y * 2.1 + np.sin(X / 3))
    C.add(road * rip, (190, 190, 210), 0.95)
    # a little islet with a domed folly (rotunda) under the moon
    isl = C.mask_poly([(mx - 30, HZ + 4), (mx - 14, HZ - 2), (mx + 16, HZ - 2), (mx + 32, HZ + 4)])
    C.fill(isl, (30, 28, 48)); far = np.maximum(far, isl)
    fx0 = mx - 6
    for cxp in (fx0 - 9, fx0 - 3, fx0 + 3, fx0 + 9):
        col = C.mask_poly([(cxp - 1.2, HZ - 2), (cxp - 1.2, HZ - 20), (cxp + 1.2, HZ - 20), (cxp + 1.2, HZ - 2)])
        C.fill(col, (150, 150, 176)); far = np.maximum(far, col)
    ent = C.mask_poly([(fx0 - 12, HZ - 20), (fx0 + 12, HZ - 20), (fx0 + 11, HZ - 23), (fx0 - 11, HZ - 23)])
    C.fill(ent, (120, 118, 150)); far = np.maximum(far, ent)
    dome = C.ellipse(fx0, HZ - 23, 11, 9) * (Y < HZ - 23)
    C.fill(dome, (96, 94, 126)); C.add(dome * (X > fx0), (60, 60, 70), 0.8); far = np.maximum(far, dome)
    fin = C.mask_poly([(fx0 - 0.8, HZ - 32), (fx0 + 0.8, HZ - 32), (fx0, HZ - 38)]); C.fill(fin, (130, 130, 160)); far = np.maximum(far, fin)
    # reflection of the folly
    refl = (np.flipud(np.where((Y > HZ - 40) & (Y < HZ), 1, 0)) > 0)
    # cypress rows (right) and a few on the far bank (left of the folly)
    def cypress(cx, base, hgt, wid, col):
        pts = [(cx - wid, base), (cx - wid * 0.9, base - hgt * 0.45), (cx - wid * 0.5, base - hgt * 0.85), (cx, base - hgt),
               (cx + wid * 0.5, base - hgt * 0.85), (cx + wid * 0.9, base - hgt * 0.45), (cx + wid, base)]
        m = C.mask_poly(pts); C.fill(m, col)
        C.add(m * np.clip((X - cx) / wid, 0, 1) * (Y < base - 6), (40, 40, 60), 0.6)   # moonlit flank (moon is to the left of most)
        return m
    for cx, hgt in [(300, 64), (318, 78), (338, 70), (356, 86), (376, 74), (396, 90), (412, 80)]:
        far = np.maximum(far, cypress(cx, HZ + 2, hgt, 7, (22, 20, 38)))
    for cx, hgt in [(150, 38), (162, 46), (176, 34)]:
        far = np.maximum(far, cypress(cx, HZ, hgt, 5, (38, 36, 62)))
    # the manor's east wing (left): gables, pointed windows, two spires, one candle window
    wing = [(0, HZ + 8), (0, 96), (14, 96), (14, 80), (20, 64), (26, 80), (26, 96), (60, 96), (74, 76), (88, 96), (104, 96), (104, 70),
            (109, 40), (114, 70), (114, 110), (126, 110), (126, HZ + 8)]
    wm2 = C.mask_poly(wing); C.fill(wm2, (26, 20, 40)); far = np.maximum(far, wm2)
    C.add(C.mask_poly([(104, 70), (109, 40), (109, 70)]) + C.mask_poly([(20, 64), (26, 80), (20, 80)]), (60, 56, 90), 0.9)   # moonlit spire faces
    C.add(C.mask_poly([(114, 110), (126, 110), (126, HZ + 8), (114, HZ + 8)]), (34, 32, 56), 0.7)                           # lit end wall
    for wx in (36, 48, 66, 80):
        for wy in (106, 132):
            win = C.mask_poly([(wx - 2.5, wy + 12), (wx - 2.5, wy + 3), (wx, wy), (wx + 2.5, wy + 3), (wx + 2.5, wy + 12)])
            C.fill(win, (14, 12, 22))
    lit = C.mask_poly([(66 - 2.5, 132 + 12), (66 - 2.5, 132 + 3), (66, 132), (66 + 2.5, 132 + 3), (66 + 2.5, 132 + 12)])
    C.fill(lit, (255, 196, 120)); C.add(C.radial(66, 138, 12, 12, 2), (120, 70, 30), 0.6)
    plate_far = C.rgb.copy()

    # ---- mid: an iron garden fence with spear finials and urn piers along the bottom, two big cypresses framing left/right
    mid = np.zeros(far.shape)
    rail = C.mask_poly([(0, 196), (W, 196), (W, 198), (0, 198)]) + C.mask_poly([(0, 210), (W, 210), (W, 212), (0, 212)])
    bars = sum(C.mask_poly([(x - 0.6, 214), (x - 0.6, 190), (x, 187), (x + 0.6, 190), (x + 0.6, 214)]) for x in range(4, W, 7))
    fence = np.clip(rail + bars, 0, 1)
    for px in (60, 196, 332):
        pier = C.mask_poly([(px - 5, H), (px - 5, 182), (px + 5, 182), (px + 5, H)])
        urn = C.mask_poly([(px - 6, 182), (px + 6, 182), (px + 6, 180), (px, 168), (px - 6, 180)])     # a pyramidal cap (no round finials: they read as heads)
        fence = np.clip(fence + pier + urn, 0, 1)
    bottom = (Y > 212).astype(float)
    hedge = (Y > 200 + 5 * C.noise(8, 4, 4, 2)).astype(float)
    m = np.clip(fence + bottom + hedge, 0, 1)
    C.fill(m, (16, 12, 24)); C.add(fence * (Y < 199), (70, 70, 100), 0.5); mid = np.maximum(mid, m)
    big = cypress(-4, H, 150, 16, (12, 10, 22)); mid = np.maximum(mid, big)
    big2 = cypress(408, H, 170, 18, (12, 10, 22)); mid = np.maximum(mid, big2)
    full = C.rgb.copy()
    return dict(full=full, sky=sky, plate=plate_far, far=far, mid=mid)


def save_guides():
    P = paint()
    for k in ('full', 'sky', 'plate'):
        im = Image.fromarray(np.clip(P[k], 0, 255).astype(np.uint8)); im.save(f'{SRC}/guide_{k}.png')
        L.edges(im).save(f'{SRC}/edge_{k}.png')
    for k in ('far', 'mid'):
        Image.fromarray((np.clip(P[k], 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/mask_{k}.png')
    Image.fromarray(np.clip(P['full'], 0, 255).astype(np.uint8)).resize((W * 2, H * 2), Image.LANCZOS).save(f'{SRC}/guide_preview.png')
    return P


def prompt_for(k):
    return PROMPT_SKY if k == 'sky' else PROMPT


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' in a: save_guides(); sys.exit()
    if '--sweep' in a:
        k = a[a.index('--sweep') + 1]; seeds = [int(s) for s in a[a.index('--sweep') + 2].split(',')]
        save_guides(); L.use_prefix(ROOM)
        kw = {kk: v for kk, v in RENDER[k].items() if kk != 'seed'}
        for i in range(len(a)):
            if a[i].startswith('--') and a[i][2:] in ('denoise', 'cn', 'cn_end', 'pix'): kw[a[i][2:]] = float(a[i + 1])
        tag = a[a.index('--tag') + 1] if '--tag' in a else ''
        L.sweep(SRC, k, prompt_for(k), seeds, tag=tag, **kw); sys.exit()

# ------------------------------------------------------------------------------------------------- separation + build
# Two parallax planes: `far` (sky, moon, the Manor wing, the canal, the folly, the cypress rows: one opaque painting) and `mid`
# (the broken garden fence, the grass and the near cypress, keyed from the same render). The model invents towers and trees
# outside the guide's silhouettes, so the far plane is not split further; the far plate is the render with the mid plane's
# area repainted as water and shore (inpaint), so nothing doubles when the planes slide. `glint` (4 frames, same scroll as far)
# twinkles the stars and shimmers the moon's road on the water.
PICK = dict(full=3, far_inpaint=12)
PROMPT_WATER = ('pixel art, night, a still reflecting canal of dark water with the moon\'s silver reflection, misty far shore, '
                'deep indigo and violet, highly detailed')
FAC = dict(far=(0.04, 0.03), mid=(0.14, 0.05))


def masks(hero):
    P = L.Canvas(W, H); Y, X = P.Y, P.X
    mm = np.asarray(Image.open(f'{SRC}/mask_mid.png'), float) / 255
    prior = (Y > 184).astype(float)
    mid = L.seg_dark(hero, prior, grow=6, margin=14) * (Y > 150)
    return np.clip(mid + (Y > 214), 0, 1)


def plates(force=False):
    hero_p = f'{SRC}/full_render.png'
    if force or not os.path.exists(hero_p): shutil.copy(f'{SRC}/sweep/full_s{PICK["full"]}.png', hero_p)
    hero = np.asarray(Image.open(hero_p).convert('RGB'), float)
    mid = masks(hero)
    far_p = f'{SRC}/farplate_render.png'
    if force or not os.path.exists(far_p):
        L.use_prefix(ROOM); L.inpaint(hero_p, L.dilate(mid, 9), PROMPT_WATER, PICK['far_inpaint'], far_p, denoise=0.75)
    return hero, mid


def grade(a, layer):
    a = np.asarray(a, float)
    if layer == 'far':
        # lift the moon's bloom and the lit cloud edges toward the emissive knee (they then show as painted under the room light)
        l = L.lum(a); k = (np.clip((l - 90) / 50, 0, 1) * np.clip((185 - l) / 40, 0, 1))[..., None]
        a = a * (1 + 0.18 * k)
        # the moon: a crisp disc edge (the bloom around it is pulled down a step so the disc reads)
        P = L.Canvas(W, H); mx, my, mr = MOON_R
        d = np.hypot(P.X - mx, P.Y - my)
        ring = (np.clip((d - mr) / 2.0, 0, 1) * np.clip((mr + 26 - d) / 26, 0, 1))[..., None]
        a = a * (1 - 0.16 * ring)
    if layer == 'mid':
        a = a * 0.8
    return np.clip(a, 0, 255)


def glints(q, rng_seed=5):
    """4 frames over the far plane: stars (isolated bright pixels up in the sky) dim in turn; the moon's road on the water
    shimmers (its bright pixels brighten / dim with a moving ripple phase)."""
    h, w = q.shape[:2]; l = L.lum(q); rng = np.random.default_rng(rng_seed)
    pad = np.pad(l, 1, mode='edge'); nb = np.max([pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx], 0)
    mx, my, mr = MOON
    yy, xx = np.mgrid[0:h, 0:w]
    star = (l > nb + 25) & (l > 90) & (yy < 120) & (np.hypot(xx - mx, yy - my) > mr + 18)
    road = (yy > HZ) & (np.abs(xx - mx) < 24) & (l > 120)
    ph = rng.integers(0, 4, (h, w))
    frames = []
    for f in range(4):
        o = np.zeros((h, w, 4))
        dim = star & (ph == f)
        o[dim, :3] = q[dim] * 0.35; o[dim, 3] = 255
        rip = road & (((yy + f * 2) // 2 + xx // 5) % 4 == 0)
        o[rip, :3] = np.clip(q[rip] * 1.25 + 20, 0, 255); o[rip, 3] = 255
        frames.append(Image.fromarray(o.astype(np.uint8), 'RGBA'))
    return frames


def build(no_ase=False):
    hero, mid = plates()
    far_r = np.asarray(Image.open(f'{SRC}/farplate_render.png').convert('RGB'), float)
    out = {}
    f1 = L.down(grade(far_r, 'far'), W, H); qf, _ = L.to_pixels(f1, 36, dk=0.4, hi=10, hi_lum=175, lo=6, lo_lum=30); out['far'] = L.rgba(qf)
    am = L.key(mid, W, H); m1 = L.down(grade(hero, 'mid'), W, H); q, _ = L.to_pixels(m1, 8, mask=am, dither=False); out['mid'] = L.rgba(np.where(am[..., None], q, 0), am)
    gl = glints(qf)
    for k, im in out.items(): im.save(f'{SRC}/out_{k}.png')
    LAY = [(out['far'], *FAC['far'], 0, False), (gl[0], *FAC['far'], 0, False), (out['mid'], *FAC['mid'], 0, False)]
    L.composite_preview(LAY, f'{SRC}/preview.png', [(0, 72), (192, 72), (0, -36)])
    if not no_ase:
        for k, im in out.items(): L.build(f'vista_{ROOM}_{k}', [im])
        L.build(f'vista_{ROOM}_glint', gl, ms=250)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--render' in a: save_guides(); plates(force=True)
    build(no_ase='--no-ase' in a)
