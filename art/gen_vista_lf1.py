#!/usr/bin/env python3
"""LF1 The Long Evening: painted vista (agent V2, docs/v17/vista_v2.md).

Kept from the old five layers (52_rc.js xrcLastFieldSky): the evening that never ends, a low sun over a golden field, the warm
wind. Raised (lore rc_4/rc_5): the field lies in the eye of the storm she called down around it. The sky over it is clear and
gold; on both horizons towering storm walls stand lit rose by the sun from inside; far off on a hill, the drake stones where the
farmers left the first sheaf; rolling fields with stooks and hedgerows in long light; the Stormspire dark in the eastern wall.

Planes (all single paintings, wrap:false): `sky` (fac 0.015), `far` hills + the drake stones (0.05), `mid` fields (0.12).
Each plane is cut from its own render with the guide's own silhouette (the shapes are simple ridges, so the guide holds).

  python3 art/gen_vista_lf1.py [--guide | --sweep sky|far|mid 1,2 | --no-ase]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import smooth, lerp, S

ROOM = 'lf1'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
SIZES = dict(sky=(424, 256), far=(472, 256), mid=(560, 256))   # cam.x 0..1408 x fac (+ margin)
SUN = (204, 150, 8)
FAR_TOP, MID_TOP = 163, 180

PROMPT_SKY = ('pixel art, breathtaking dramatic sunset cloudscape, a heavy storm cloud deck overhead with rippled mammatus pouches '
              'glowing crimson orange and gold on their undersides, lit from below by a small low setting sun near the horizon, a clear '
              'golden band of sky beneath, layers of detailed volumetric clouds catching the light, rays of light, epic, serene, '
              'side-scroller game background, highly detailed, beautiful')
PROMPT_FAR = ('pixel art, golden hour, rolling hills of ripe wheat fields far away in warm haze under a low sun, an ancient ring of '
              'standing stones on a hilltop silhouetted against the sun, hedgerows and lone trees, a distant dark storm-wrapped rocky '
              'spire on the right horizon, long shadows, amber rose and violet palette, side-scroller game background, highly detailed, beautiful')
PROMPT_MID = ('pixel art, golden hour, gently rolling golden wheat fields with rows of harvested sheaves and stooks, a dark hedgerow '
              'and an old oak, long warm sunlight from a low sun, violet shadows, side-scroller game background, highly detailed, beautiful')
PROMPTS = dict(sky=PROMPT_SKY, far=PROMPT_FAR, mid=PROMPT_MID)
RENDER = dict(sky=dict(denoise=0.62, cn=0.45, cn_end=0.6, pix=0.35), far=dict(denoise=0.6, cn=0.65, cn_end=0.75, pix=0.45),
              mid=dict(denoise=0.6, cn=0.65, cn_end=0.75, pix=0.45))
PICK = dict(sky=1, far=1, mid=1)


def sky_canvas(w, h):
    C = L.Canvas(w, h); X, Y = C.X, C.Y; sx, sy, sr = SUN
    C.rgb = C.vgrad([(0, (26, 18, 52)), (50, (64, 34, 84)), (100, (150, 66, 96)), (130, (226, 116, 86)), (150, (255, 178, 96)), (h, (255, 214, 140))])
    ds = np.sqrt(((X - sx) * 0.6) ** 2 + (Y - sy) ** 2)
    C.add(np.exp(-(ds / 70) ** 2), (60, 50, 20), 1.0); C.add(np.exp(-(ds / 26) ** 2), (50, 40, 30), 1.0)
    nz = C.noise(60, 9, 21, 4)
    for cy, th, x0, x1 in [(62, 3, 90, 330), (84, 4, 40, 300), (104, 3.5, 120, 380), (118, 4, 60, 260), (132, 3, 150, 330)]:   # lit strata
        wob = cy + 2.5 * (nz - 0.5) * 2
        band = np.clip(1 - np.abs(Y - wob) / th, 0, 1) ** 1.3 * smooth(x0 - 40, x0 + 40, X) * (1 - smooth(x1 - 40, x1 + 40, X))
        C.fill(band, lerp(np.array((200, 110, 120.)), np.array((255, 200, 140.)), np.clip((Y - 50) / 90, 0, 1)[..., None]), 0.75)
    # her storm overhead: a heavy cloud deck over the top of the sky, its rippled underside lit crimson and gold by the low sun
    # (the field sits in the clear band beneath it, the eye); it thins and breaks toward the sun
    xs = np.arange(w * S) / S; rng = np.random.default_rng(8)
    base = 60 - 14 * np.exp(-((xs - SUN[0]) / 120) ** 2) + 8 * np.sin(xs / 53 + 1) + 4 * np.sin(xs / 23)
    deck = (Y < base[None, :]).astype(float)
    for _ in range(140):   # mammatus: rounded pouches hanging from the deck's underside
        cx = rng.uniform(-10, w + 10); by = np.interp(cx, xs, base); r = rng.uniform(5, 13)
        deck = np.maximum(deck, C.ellipse(cx, by - r * 0.2, r * 1.2, r * 0.75))
    edge = (np.cumsum(deck[::-1] > 0.5, axis=0)[::-1] > 0)          # True at and above the lowest deck pixel of each column
    lowest = np.argmax(np.where(edge, np.arange(edge.shape[0])[:, None], -1), axis=0) / S
    d_up = np.clip((lowest[None, :] - Y) / 26, 0, 1)
    warm = np.exp(-((X - SUN[0]) / 230) ** 2)
    col = lerp(np.array((255, 150, 96.)), np.array((46, 28, 64.)), np.clip(d_up ** 0.7 - 0.12 * warm, 0, 1)[..., None])
    C.fill(deck, col)
    # each pouch's own underside catches light too
    C.add(deck * np.clip(1 - np.abs(np.roll(deck, -3 * S // 3, axis=0) - deck), 0, 1) * 0, (0, 0, 0))
    for k in range(3):   # ragged scraps hanging below the deck toward the sun
        cx = SUN[0] + (k - 1) * 70 + rng.uniform(-10, 10); cy = 92 + k * 6
        scrap = C.ellipse(cx, cy, 26, 3.5); C.fill(scrap, (230, 130, 100), 0.8)
    rng = np.random.default_rng(2)
    for _ in range(30):
        x, y = rng.uniform(0, w), rng.uniform(100, 120)
        C.fill(C.ellipse(x, y, 0.6, 0.6), (255, 230, 200), rng.uniform(0.2, 0.4))
    C.fill(C.ellipse(sx, sy, sr, sr), (255, 246, 214))
    return C


def hills(C, top, k, seed, base_col, lit_col):
    X, Y = C.X, C.Y; w = C.w
    xs = np.arange(w * S) / S; rng = np.random.default_rng(seed)
    prof = np.full_like(xs, float(top))
    for per, amp in [(220, 7), (97, 4), (41, 2)]:
        prof += amp * np.sin(xs / per * 2 * math.pi + rng.uniform(0, 6.3))
    m = (Y > prof[None, :]).astype(float)
    depth = np.clip((Y - prof[None, :]) / 30, 0, 1)
    sun = np.exp(-((X - SUN[0] * k) / 160) ** 2)
    col = lerp(np.array(lit_col, float), np.array(base_col, float), np.clip(depth * 0.8 + (1 - sun) * 0.3, 0, 1)[..., None])
    C.fill(m, col)
    return m, prof


def paint(layer):
    w, h = SIZES[layer]
    C = sky_canvas(w, h)
    if layer == 'sky': return C, None
    sk = f'{SRC}/sky_render.png'
    if os.path.exists(sk):   # the far / mid guides sit on the picked sky render (stretched to the wider plane), so light and colour agree
        C.rgb = np.asarray(Image.open(sk).convert('RGB').resize((w * S, h * S), Image.LANCZOS), float)
    X, Y = C.X, C.Y
    m0, prof0 = hills(C, FAR_TOP + 2, 1.0, 5, (120, 70, 90), (240, 170, 110))
    m1, prof1 = hills(C, FAR_TOP + 8, 1.0, 6, (110, 62, 84), (230, 150, 100))
    far = np.maximum(m0, m1)
    # the drake stones on the hill nearest the sun's left
    hx = 150; ht = prof0[int(hx * S)]
    for i, (dx, hh, ww) in enumerate([(-14, 7, 2.5), (-8, 9, 2.5), (-2, 10, 3), (5, 9, 2.5), (11, 8, 2.5), (16, 6, 2)]):
        st = C.mask_poly([(hx + dx - ww, ht + 2), (hx + dx - ww * 0.8, ht - hh), (hx + dx + ww * 0.8, ht - hh - 0.5), (hx + dx + ww, ht + 2)])
        C.fill(st, (70, 40, 66)); far = np.maximum(far, st)
    C.fill(C.mask_poly([(hx - 9, ht - 9), (hx + 7, ht - 10), (hx + 7, ht - 8), (hx - 9, ht - 7)]), (70, 40, 66))   # a lintel
    # lone trees on the far hills
    for tx in (60, 262, 330, 410):
        ty = prof0[min(len(prof0) - 1, int(tx * S))]
        tr = C.ellipse(tx, ty - 7, 6, 5) + C.mask_poly([(tx - 0.8, ty + 1), (tx - 0.8, ty - 4), (tx + 0.8, ty - 4), (tx + 0.8, ty + 1)])
        C.fill(np.clip(tr, 0, 1), (96, 54, 76)); far = np.maximum(far, np.clip(tr, 0, 1))
    # the Stormspire: a dark crag-spire inside the eastern storm wall
    sp = C.mask_poly([(w - 92, FAR_TOP + 6), (w - 84, 136), (w - 79, 116), (w - 76, 100), (w - 72, 100), (w - 70, 118), (w - 64, 138), (w - 56, FAR_TOP + 6)])
    sp = np.maximum(sp, C.mask_poly([(w - 76, 101), (w - 75.5, 84), (w - 74, 78), (w - 72.5, 84), (w - 72, 101)]))
    C.fill(sp, (46, 30, 60)); far = np.maximum(far, sp); C.fill(C.ellipse(w - 74, 82, 1.2, 1.2), (255, 220, 160))
    if layer == 'far': return C, far
    # mid: nearer fields with stooks and a hedgerow, an old oak
    m2, prof2 = hills(C, MID_TOP, 1.0, 9, (110, 56, 60), (250, 190, 100))
    mid = m2.copy()
    rng = np.random.default_rng(12)
    for row in range(3):
        y_off = 6 + row * 9
        for x in np.arange(rng.uniform(0, 20), w, 26 - row * 4):
            yb = prof2[min(len(prof2) - 1, int(x * S))] + y_off
            stk = C.mask_poly([(x - 3 - row, yb), (x, yb - 7 - row * 2), (x + 3 + row, yb)])
            C.fill(stk, (200, 140, 70)); C.add(stk * (X < x), (50, 40, 20), 1.0)
    nzh = C.noise(5, 3, 44, 2)
    hedge = ((Y > prof2[None, :] - 3 - 4 * nzh) & (Y < prof2[None, :] + 3)).astype(float) * (np.sin(X / 37) > -0.3)
    C.fill(hedge, (78, 44, 54)); C.add(hedge * (Y < prof2[None, :] - 1), (90, 50, 20), 0.6); mid = np.maximum(mid, hedge)
    ox = 380; oy = prof2[int(ox * S)]
    oak = np.clip(C.ellipse(ox, oy - 26, 22, 14) + C.ellipse(ox - 14, oy - 20, 12, 9) + C.ellipse(ox + 15, oy - 21, 12, 9) +
                  C.mask_poly([(ox - 3, oy + 2), (ox - 2, oy - 18), (ox + 2, oy - 18), (ox + 3, oy + 2)]), 0, 1)
    C.fill(oak, (80, 44, 54)); C.add(oak * np.clip((ox - X) / 20, 0, 1) * (Y < oy - 18), (120, 70, 30), 0.8); mid = np.maximum(mid, oak)
    return C, mid


def save_guides():
    for k in ('sky', 'far', 'mid'):
        C, m = paint(k); im = C.image(); im.save(f'{SRC}/guide_{k}.png'); L.edges(im).save(f'{SRC}/edge_{k}.png')
        if m is not None: Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).save(f'{SRC}/mask_{k}.png')
    C, _ = paint('mid'); C.image().resize((SIZES['mid'][0] * 2, SIZES['mid'][1] * 2), Image.LANCZOS).save(f'{SRC}/guide_preview.png')


def cli_sweep(a):
    k = a[a.index('--sweep') + 1]; seeds = [int(s) for s in a[a.index('--sweep') + 2].split(',')]
    save_guides(); L.use_prefix(ROOM)
    kw = dict(RENDER[k])
    for i in range(len(a)):
        if a[i].startswith('--') and a[i][2:] in ('denoise', 'cn', 'cn_end', 'pix'): kw[a[i][2:]] = float(a[i + 1])
    tag = a[a.index('--tag') + 1] if '--tag' in a else ''
    L.sweep(SRC, k, PROMPTS[k], seeds, tag=tag, **kw)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' in a: save_guides(); sys.exit()
    if '--sweep' in a: cli_sweep(a); sys.exit()


# ------------------------------------------------------------------------------------------------- the land, by hand at 1x
# The land is a thin band under the sky (standing, ~20 px of it shows over the field's own wheat; seated ~50 px), and every
# render of it came out as flat brown mush, so it is painted at the game's pixel scale: backlit ridges with a gold rim, the
# drake stones, the storm-spire, hedgerows, stooks in rows. Colours are taken from the sky render's horizon so they sit in it.
FAR_TOP, MID_TOP = 172, 188


def _ridge(w, top, seed, amps):
    rng = np.random.default_rng(seed); x = np.arange(w, dtype=float); y = np.full(w, float(top))
    for per, amp in amps: y += amp * np.sin(x / per * 2 * math.pi + rng.uniform(0, 6.3))
    return np.round(y).astype(int)


def _mix(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def land_far():
    w, h = SIZES['far']; a = np.zeros((h, w, 4), np.uint8); rng = np.random.default_rng(31)
    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h: a[y, x, :3] = c; a[y, x, 3] = 255
    hazeT, hazeB = (214, 120, 104), (150, 74, 92)     # ridge tops take the horizon's rose; lower down, violet
    for k, (top, amps, tint) in enumerate([(FAR_TOP - 4, [(160, 5), (61, 2.5)], 0.0), (FAR_TOP + 3, [(130, 4), (47, 2)], 0.35)]):
        r = _ridge(w, top, 40 + k, amps)
        for x in range(w):
            for y in range(r[x], h):
                t = min(1, (y - r[x]) / 22) * 0.8 + tint
                c = _mix(hazeT, hazeB, min(1, t)); c = _mix(c, (90, 46, 72), 0.25 * k)
                if (x * 7 + y * 3) % 11 == 0 and y > r[x] + 2: c = _mix(c, (120, 60, 84), 0.5)      # a little field texture
                put(x, y, c)
            put(x, r[x], _mix((255, 196, 120), hazeT, 0.25 * k))                               # the backlit rim
        if k == 0: r0 = r
    # the drake stones on the first ridge, left of the sun
    hx = 150; base = r0[hx]
    for dx, hh in [(-12, 6), (-7, 8), (-2, 9), (3, 8), (8, 7), (12, 5)]:
        for y in range(base - hh, base + 1):
            for xx in (hx + dx, hx + dx + 1): put(xx, y, (84, 40, 66))
        put(hx + dx, base - hh, (230, 150, 110))
    for xx in range(hx - 8, hx + 5): put(xx, base - 9, (84, 40, 66))                           # a lintel
    # lone trees on the ridges
    def clump(cx, b, blobs, dark, rimc):
        cov = set()
        for ox, oy, rx, ry in blobs:
            for yy in range(-int(ry) - 1, int(ry) + 2):
                for xx in range(-int(rx) - 1, int(rx) + 2):
                    if (xx / rx) ** 2 + (yy / ry) ** 2 < 1: cov.add((int(round(cx + ox + xx)), int(round(b + oy + yy))))
        for (x, y) in cov: put(x, y, dark)
        for (x, y) in cov:   # rim: the up-left facing edge catches the sun
            if (x, y - 1) not in cov or (x - 1, y) not in cov and (x, y - 1) not in cov: put(x, y, rimc)
    for tx in (58, 262, 318):
        b = r0[tx]
        for dy in range(0, 4): put(tx, b - dy, (92, 46, 70))
        clump(tx, b - 6, [(0, 0, 3.2, 2.4), (-2, 1, 2.2, 1.8), (2, -1, 2.5, 2), (1, 1.5, 2.6, 1.6)], (100, 50, 74), (200, 116, 100))
    # the Stormspire inside the east storm: a tall crag with the lighthouse on it
    sx0 = w - 74
    for y in range(96, FAR_TOP + 8):
        half = int(1.5 + (y - 96) * 0.05 + max(0, y - 158) * 0.3)
        for x in range(sx0 - half, sx0 + half + 1): put(x, y, (52, 30, 62))
        put(sx0 - half, y, (150, 84, 96))
    for y in range(82, 97): put(sx0, y, (52, 30, 62)); put(sx0 + 1, y, (52, 30, 62))
    put(sx0, 84, (255, 224, 160)); put(sx0 + 1, 84, (255, 224, 160)); put(sx0, 85, (255, 200, 140))
    return Image.fromarray(a)


def land_mid():
    w, h = SIZES['mid']; a = np.zeros((h, w, 4), np.uint8)
    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h: a[y, x, :3] = c; a[y, x, 3] = 255
    r = _ridge(w, MID_TOP, 52, [(210, 5), (77, 2.5)])
    lit, mid, sh = (246, 176, 92), (204, 120, 76), (120, 58, 66)
    for x in range(w):
        for y in range(r[x], h):
            d = y - r[x]; t = min(1, d / 26)
            c = _mix(lit, mid, min(1, t * 1.6)) if t < 0.6 else _mix(mid, sh, (t - 0.6) / 0.4)
            if (y + (x // 3)) % 4 == 0 and d > 1: c = _mix(c, sh, 0.25)              # furrows of stubble
            put(x, y, c)
        put(x, r[x], (255, 214, 140))
    # hedgerows (bushy runs along the crest, gaps between)
    for x0 in range(6, w, 74):
        n = 18 + (x0 * 13) % 22
        for x in range(x0, min(w, x0 + n)):
            hh = 3 + int(2 * abs(math.sin(x * 0.7)) + (x % 5 == 0))
            for y in range(r[x] - hh, r[x] + 2): put(x, y, (86, 44, 58))
            put(x, r[x] - hh, (220, 140, 100))
    # stooks in rows down the slope, lit on the sun side (the sun is up-left of most of them)
    for row, dy in enumerate((6, 13, 22)):
        for x0 in range(10 + row * 9, w, 23 + row * 3):
            yb = r[x0] + dy; hh = 4 + row
            for yy in range(hh):
                half = max(0, int((yy + 1) * (2 + row) / hh))
                for xx in range(-half, half + 1):
                    put(x0 + xx, yb - hh + yy, (255, 210, 120) if xx < 0 else (176, 96, 70))
            put(x0, yb - hh - 1, (255, 226, 150))
    # an old oak on the crest at the right: a lumpy crown of several masses, lit along its upper-left edges only
    ox = 420; b = r[ox]
    for y in range(b - 12, b + 1):
        for x in (ox - 1, ox, ox + 1): put(x, y, (70, 34, 50))
    for x, y in [(ox - 2, b - 10), (ox - 3, b - 11), (ox + 2, b - 9), (ox + 3, b - 10), (ox + 4, b - 11)]: put(x, y, (70, 34, 50))
    cov = set()
    for cx, cy, rx, ry in [(0, -20, 10, 6), (-9, -16, 7, 5), (9, -17, 8, 5), (-4, -24, 6, 4), (6, -23, 6, 4), (-14, -13, 4, 3), (14, -13, 5, 3)]:
        for yy in range(-ry - 1, ry + 2):
            for xx in range(-rx - 1, rx + 2):
                if (xx / rx) ** 2 + (yy / ry) ** 2 < 1: cov.add((ox + cx + xx, b + cy + yy))
    for (x, y) in cov: put(x, y, (88, 42, 58))
    for (x, y) in cov:
        if (x, y - 1) not in cov: put(x, y, (226, 140, 100))
        elif (x - 1, y) not in cov and (x, y - 2) not in cov: put(x, y, (170, 92, 82))
    return Image.fromarray(a)


FAC = dict(sky=(0.015, 0.03), far=(0.05, 0.05), mid=(0.12, 0.09))


def grade_sky(a):
    l = L.lum(a)[..., None]
    k = np.where(l > 150, (150 + (l - 150) * 0.55) / np.maximum(l, 1), 1.0)
    b = a * k * 0.95
    m = b.mean(-1, keepdims=True); return np.clip(m + (b - m) * 1.05, 0, 255)


def build(no_ase=False):
    w, h = SIZES['sky']
    sky = L.down(grade_sky(np.asarray(Image.open(f'{SRC}/sky_render.png').convert('RGB'), float)), w, h)
    q, _ = L.to_pixels(sky, 40, dk=0.35, hi=8, hi_lum=190, lo=6, lo_lum=50)
    out = {'sky': L.rgba(q), 'far': land_far(), 'mid': land_mid()}
    if os.path.exists(f'{SRC}/fartex_render.png'): out['sky'].save(f'{SRC}/out_sky.png'); out['far'] = textured('far')
    if os.path.exists(f'{SRC}/midtex_render.png'): out['mid'] = textured('mid')
    for k, im in out.items(): im.save(f'{SRC}/out_{k}.png')
    LAY = [(out[k], *FAC[k], 0, False) for k in ('sky', 'far', 'mid')]
    L.composite_preview(LAY, f'{SRC}/preview.png', [(600, 104), (1408, 104), (443, -73)])
    if not no_ase:
        for k, im in out.items(): L.build(f'vista_{ROOM}_{k}', [im])




# ------------------------------------------------------------------------------------------------- texture pass on the land
# The hand-painted land holds its shapes but reads flat next to the rendered sky, so it gets a light img2img pass (denoise 0.4,
# lineart ControlNet from its own edges): composite sky+far (and sky+far+mid) at 3x nearest -> render -> cut each plane back
# out with its own 1x alpha, so the silhouettes stay exactly as painted.
PROMPT_LAND = ('pixel art, golden hour, rolling hills of ripe wheat and harvested fields far away in warm haze, an ancient ring of '
               'standing stones on a hilltop, hedgerows and lone trees, stooks of wheat sheaves, long warm light from a low sun, rose '
               'and violet shadows, painterly, side-scroller game background, highly detailed, beautiful')
TEX = dict(seed=3, denoise=0.4, cn=0.6, cn_end=0.7, pix=0.4)


def land_comp(upto):
    sky = Image.open(f'{SRC}/out_sky.png').convert('RGBA')
    ims = {'far': land_far(), 'mid': land_mid()}
    w, h = SIZES[upto]
    c = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    c.alpha_composite(sky.resize((w, h), Image.NEAREST) if sky.size != (w, h) else sky)
    for k in ('far', 'mid'):
        im = ims[k]
        if im.size != (w, h): im = im.crop((0, 0, w, h)) if im.width >= w else im
        c.alpha_composite(im if im.size == (w, h) else im.resize((w, h), Image.NEAREST))
        if k == upto: break
    return c.convert('RGB')


def texture_pass(force=False):
    L.use_prefix(ROOM)
    for k in ('far', 'mid'):
        out = f'{SRC}/{k}tex_render.png'
        if os.path.exists(out) and not force: continue
        comp = land_comp(k); w, h = comp.size
        g = comp.resize((w * S, h * S), Image.NEAREST); gp = f'{SRC}/guide_{k}tex.png'; g.save(gp); L.edges(g).save(f'{SRC}/edge_{k}tex.png')
        L.render(gp, f'{SRC}/edge_{k}tex.png', PROMPT_LAND, TEX['seed'], out, denoise=TEX['denoise'], cn=TEX['cn'], cn_end=TEX['cn_end'], pix=TEX['pix'], blur=0.8)


def textured(k):
    a0 = land_far() if k == 'far' else land_mid(); al = np.asarray(a0)[..., 3] > 0
    w, h = a0.size
    r = L.down(Image.open(f'{SRC}/{k}tex_render.png'), w, h)
    q, _ = L.to_pixels(r, 28 if k == 'far' else 24, mask=al, dither=False, hi=4, hi_lum=190)
    return L.rgba(np.where(al[..., None], q, 0), al)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' not in a and '--sweep' not in a:
        build(no_ase=True)
        if '--texture' in a: texture_pass(force=True)
        build(no_ase='--no-ase' in a)
