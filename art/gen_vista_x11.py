#!/usr/bin/env python3
"""X11 The Crown Overlook: painted vista (agent V2, docs/v17/vista_v2.md).

Kept from the old overlay (xrc_cr_panorama): the whole Hallow under a sea of cloud, its landmarks standing out of it (lore
rc_10: the Ramparts, the drowned Cathedral, the Spire in its storm, the red breath of the Deep). Raised: a golden-hour sky
from the top of the world, the low sun laying a road of light across the cloud sea, the landmarks in aerial perspective, the
Deep's glow breathing up through a rift in the clouds, and billows of near cloud below the bough.

Planes: `far` (sky, sun, cloud sea, landmarks: one opaque painting), `near` (cloud billows rendered on a flat ground, keyed).
fx (85v_v2.js): the Deep's red glow pulses, lightning in the Spire's storm, a drifting veil of cloud over the sea, the sun's bloom.

  python3 art/gen_vista_x11.py              build from the saved renders (art/bg_src/vista_x11/)
  python3 art/gen_vista_x11.py --guide
  python3 art/gen_vista_x11.py --sweep far|near 1,2,3 [--denoise x ...]
  python3 art/gen_vista_x11.py --render     re-render the picked seeds, then build
"""
import math, os, sys, shutil
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v2lib as L
from bgv2lib import smooth, lerp, S

ROOM = 'x11'
SRC = os.path.join(HERE, 'bg_src', 'vista_' + ROOM); os.makedirs(SRC, exist_ok=True)
FW, FH = 408, 240          # far: fac 0.03 over cam.x 0..384 -> 12 px of travel
NW, NH = 440, 240          # near: fac 0.12 -> 46 px
SUN = (150, 132, 10)       # painting px (low: the disc touches the cloud sea)
HZ = 140                   # the cloud sea's far edge
GROUND = (22, 26, 52)

PROMPT_FAR = ('pixel art, epic sky panorama at golden hour seen from above the clouds, a vast endless sea of clouds lit gold and rose, '
              'a low radiant setting sun touching the cloud sea and laying a road of golden light across the cloud tops, a towering '
              'cumulonimbus thunderhead on the horizon with a flat anvil top lit rose and gold and dark rain curtains below, high thin '
              'cirrus clouds streaked pink and gold, deep violet blue sky above with first stars, empty sky, no buildings, serene, majestic, '
              'aerial perspective, side-scroller game background, highly detailed, beautiful')
PROMPT_NEAR = ('pixel art, huge soft billowing cumulus cloud tops lit warm gold and rose by a low sun from the left, lavender shadows, '
               'isolated on a flat dark navy background, side-scroller game background layer, highly detailed')
RENDER = dict(far=dict(seed=1, denoise=0.66, cn=0.45, cn_end=0.6, pix=0.45),
              near=dict(seed=1, denoise=0.62, cn=0.5, cn_end=0.65, pix=0.45))


def paint_far():
    C = L.Canvas(FW, FH); X, Y = C.X, C.Y
    sx, sy, sr = SUN
    C.rgb = C.vgrad([(0, (28, 30, 74)), (40, (70, 62, 120)), (80, (176, 110, 130)), (112, (240, 170, 120)), (HZ, (255, 214, 150))])
    ds = np.sqrt(((X - sx) * 0.7) ** 2 + (Y - sy) ** 2)
    C.add(np.exp(-(ds / 60) ** 2), (70, 50, 20), 1.0)
    C.add(np.exp(-(ds / 22) ** 2), (60, 50, 30), 1.0)
    nz = C.noise(70, 8, 3, 4)
    # high cirrus streaks: long, thin, slightly slanted, lit on their lower edges
    for cy, th, x0, x1 in [(18, 2.5, 160, 408), (30, 3, 0, 260), (46, 3.5, 120, 408), (60, 2.5, 0, 200), (74, 4, 230, 408), (88, 3, 20, 300)]:
        wob = cy + (X - x0) * 0.04 + 3 * (nz - 0.5)
        band = np.clip(1 - np.abs(Y - wob) / th, 0, 1) ** 1.5 * smooth(x0 - 30, x0 + 30, X) * (1 - smooth(x1 - 30, x1 + 30, X))
        warm = np.clip(Y / 100, 0, 1)
        col = lerp(np.array((150, 120, 170.)), np.array((255, 190, 150.)), warm[..., None])
        C.fill(band, col, 0.7)
    # stars at the top
    rng = np.random.default_rng(3)
    for _ in range(40):
        x, y = rng.uniform(0, FW), rng.uniform(1, 34)
        C.fill(C.ellipse(x, y, 0.7, 0.7), (230, 225, 255), rng.uniform(0.4, 0.9))
    # the sun disc
    C.fill(C.ellipse(sx, sy, sr, sr), (255, 246, 220))
    # ---- landmarks (blue-violet haze silhouettes, rim-lit on the sun side)
    haze = (120, 104, 150)
    def sil(pts, col=haze, rim=True):
        m = C.mask_poly(pts); C.fill(m, col)
        if rim:   # the sun-facing (left) edges catch a thin warm light
            sh = np.roll(m, 4, axis=1); C.add(np.clip(m - sh, 0, 1), (120, 80, 40), 0.9)
        return m
    # the Spire's storm: a towering thunderhead (cumulonimbus) on the horizon, its crown and anvil lit rose and gold by the
    # low sun, its base dark and trailing rain; the tower stands in front of the dark base
    rng2 = np.random.default_rng(5); storm = np.zeros(C.rgb.shape[:2]); cx0 = 334
    for _ in range(60):
        t = rng2.uniform(0, 1); y = HZ - 6 - t * 92; half = 26 + 22 * t ** 3 + 10 * (1 - t)
        cx = cx0 + rng2.uniform(-half, half) * 0.8 + t * 10; r = rng2.uniform(7, 15) * (1 - 0.3 * t)
        storm = np.maximum(storm, C.ellipse(cx, y, r, r * 0.8))
    storm = np.maximum(storm, C.ellipse(cx0 + 14, HZ - 96, 58, 7))            # the anvil
    storm = np.maximum(storm, C.mask_poly([(cx0 - 30, HZ), (cx0 - 26, HZ - 30), (cx0 + 34, HZ - 30), (cx0 + 40, HZ)]))
    hgt = np.clip((HZ - Y) / 100, 0, 1)
    side = np.clip((cx0 + 10 - X) / 50, -1, 1)                                # +: the sun side
    base = lerp(np.array((70, 62, 96.)), np.array((150, 128, 160.)), hgt[..., None])
    C.fill(storm, base)
    C.add(storm * np.clip(side, 0, 1) * hgt, (120, 70, 20), 0.9)                # rose-gold light on the sunward flank
    C.add(storm * np.clip(-side, 0, 1), (-24, -22, -14), 1.0)
    for k, x0 in enumerate((cx0 - 22, cx0 - 4, cx0 + 16)):                   # rain curtains under the base
        xr = X - (x0 + (Y - (HZ - 30)) * 0.3)
        veil = np.clip(1 - np.abs(xr) / 7, 0, 1) * ((Y > HZ - 32) & (Y < HZ + 1)).astype(float)
        C.fill(veil, (60, 56, 88), 0.5)
    # far ridges peeking through the sea (very hazy)
    for cx, w, h in [(120, 26, 8), (270, 20, 6), (380, 30, 9)]:
        sil([(cx - w, HZ), (cx - w * 0.3, HZ - h), (cx + w * 0.2, HZ - h * 0.8), (cx + w, HZ)], (170, 130, 150), rim=False)
    # ---- the cloud sea: rows of billows, lit gold toward the sun, violet in shadow, getting bigger toward the viewer
    sea = (Y > HZ).astype(float)
    C.rgb = C.rgb * (1 - sea[..., None]) + C.vgrad([(HZ, (240, 196, 170)), (170, (200, 150, 170)), (FH, (120, 96, 150))]) * sea[..., None]
    rng = np.random.default_rng(11)
    bands = [HZ + 1 + 1.9 * k ** 1.55 for k in range(1, 14)]
    for k, y0 in enumerate(bands):   # back to front: each band a ragged billowing top edge (summed |sin| bumps of random sizes)
        amp = 1.2 + k * 0.9; xs = np.arange(FW * S) / S
        prof = np.zeros_like(xs)
        for per in (9 + k * 3, 17 + k * 5, 31 + k * 7):
            ph = rng.uniform(0, 6.3); prof += np.abs(np.sin(xs / per * math.pi + ph)) * rng.uniform(0.5, 1.0)
        top = y0 - prof / 2.2 * amp * 1.8
        m = (Y > top[None, :]).astype(float)
        depth = np.clip((Y - top[None, :]) / (amp * 2.2 + 2), 0, 1)
        toward = np.exp(-((X - sx) / (90 + k * 14)) ** 2)
        lit = np.clip(1 - depth, 0, 1) * (0.55 + 0.45 * toward)
        shade = lerp(np.array((150, 116, 168.)), np.array((205, 160, 180.)), (k / 13))
        col = lerp(shade, np.array((255, 224, 176.)), lit[..., None])
        C.fill(m, col)
    # the sun's road across the sea
    road = np.exp(-((X - sx) / (6 + (Y - HZ) * 0.9)) ** 2) * sea
    C.add(road, (60, 50, 20), 0.9)
    # the Deep's rift: only a soft warm hollow in the sea; its red glow is drawn live (85v_v2.js) so it can breathe
    C.add(C.radial(262, 160, 30, 7, 2), (40, -10, -20), 1.0)
    return C


def paint_near():
    C = L.Canvas(NW, NH, base=GROUND); X, Y = C.X, C.Y
    m = np.zeros(C.rgb.shape[:2]); rng = np.random.default_rng(7)
    for row, (y0, r) in enumerate([(206, 16), (222, 22), (238, 28)]):
        x = rng.uniform(-r, 0)
        while x < NW + r:
            rr = r * rng.uniform(0.7, 1.25)
            b = C.ellipse(x, y0, rr * 1.3, rr * 0.8)
            top = np.clip((y0 - Y) / (rr * 0.8), 0, 1); left = np.clip((x - X) / rr, 0, 1)
            col = lerp(np.array((150, 116, 160.)), np.array((255, 214, 176.)), np.clip(0.55 * top + 0.45 * left, 0, 1)[..., None])
            C.fill(b, col); m = np.maximum(m, b)
            x += rr * rng.uniform(1.4, 2.0)
    m = np.maximum(m, (Y > 236).astype(float)); C.fill((Y > 236).astype(float), (130, 100, 150))
    return C, m


def save_guides():
    F = paint_far(); im = F.image(); im.save(f'{SRC}/guide_far.png'); L.edges(im).save(f'{SRC}/edge_far.png')
    N, m = paint_near(); im = N.image(); im.save(f'{SRC}/guide_near.png'); L.edges(im).save(f'{SRC}/edge_near.png')
    Image.fromarray((m * 255).astype(np.uint8)).save(f'{SRC}/mask_near.png')
    F.image().resize((FW * 2, FH * 2), Image.LANCZOS).save(f'{SRC}/guide_preview.png')


PROMPTS = dict(far=PROMPT_FAR, near=PROMPT_NEAR)


def cli_sweep(a):
    k = a[a.index('--sweep') + 1]; seeds = [int(s) for s in a[a.index('--sweep') + 2].split(',')]
    save_guides(); L.use_prefix(ROOM)
    kw = {kk: v for kk, v in RENDER[k].items() if kk != 'seed'}
    for i in range(len(a)):
        if a[i].startswith('--') and a[i][2:] in ('denoise', 'cn', 'cn_end', 'pix'): kw[a[i][2:]] = float(a[i + 1])
    tag = a[a.index('--tag') + 1] if '--tag' in a else ''
    L.sweep(SRC, k, PROMPTS[k], seeds, tag=tag, **kw)




# ------------------------------------------------------------------------------------------------- the landmarks (1x, by hand)
# Painted at the game's pixel scale, not rendered: every render turned the storm into a castle and the castles into storms.
# Hazy aerial-perspective silhouettes, two tones (lit / shade), a 1 px warm rim on the sun-facing side, a few lit windows.
def landmarks():
    from PIL import ImageDraw
    im = Image.new('RGBA', (FW, FH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def poly(pts, col): d.polygon([(round(x), round(y)) for x, y in pts], fill=col + (255,))
    def rect(x0, y0, x1, y1, col): d.rectangle([x0, y0, x1, y1], fill=col + (255,))
    def px(x, y, col): d.point((x, y), fill=col + (255,))
    # --- the Ramparts on their crag (left of the sun: lit on the right)
    R0, R1, RR = (164, 112, 136), (134, 92, 126), (214, 150, 146)
    poly([(4, 141), (8, 128), (12, 122), (14, 114), (18, 110), (17, 104), (24, 100), (40, 99), (62, 100), (66, 104), (70, 103),
          (74, 110), (78, 116), (80, 124), (86, 130), (90, 141)], R1)
    poly([(62, 100), (66, 104), (70, 103), (74, 110), (78, 116), (80, 124), (86, 130), (90, 141), (72, 141), (70, 124), (66, 112)], R0)   # the crag's lit face
    for y0, x0, x1 in [(112, 20, 30), (122, 10, 22), (118, 40, 56)]: d.line([(x0, y0), (x1, y0 + 2)], fill=(118, 82, 116, 255))   # ledges
    for x0, x1, y in [(18, 74, 92)]:   # the curtain wall with crenels
        rect(x0, y, x1, 100, R1)
        for x in range(x0, x1 + 1, 3): rect(x, y - 2, x + 1, y - 1, R1)
    for cx, top, w in [(22, 80, 3), (66, 82, 3)]:   # round towers with conical roofs
        rect(cx - w, top, cx + w, 100, R1); poly([(cx - w - 1, top), (cx, top - 9), (cx + w + 1, top)], (110, 76, 112))
        d.line([(cx + w, top), (cx + w, 100)], fill=RR + (255,))
    rect(36, 70, 52, 100, R1)   # the keep
    for x in range(36, 53, 3): rect(x, 67, x + 1, 69, R1)
    rect(42, 58, 47, 70, R1); poly([(41, 58), (44, 50), (48, 58)], (110, 76, 112)); d.line([(44, 50), (44, 45)], fill=R1 + (255,))
    d.line([(52, 70), (52, 100)], fill=RR + (255,)); d.line([(47, 58), (47, 70)], fill=RR + (255,)); d.line([(74, 92), (74, 100)], fill=RR + (255,))
    for x, y in [(40, 78), (48, 78), (44, 62), (24, 88), (30, 95), (60, 95)]: px(x, y, (255, 214, 140))
    # --- the drowned Cathedral (right of the sun: lit on the left), its nave sunk in cloud
    C0, C1, CR = (176, 112, 132), (150, 96, 124), (226, 166, 150)
    poly([(198, 141), (198, 116), (215, 102), (232, 116), (232, 141)], C1)
    for cx in (203, 227):
        rect(cx - 5, 92, cx + 5, 141, C1)
        poly([(cx - 5, 92), (cx, 66 if cx < 215 else 70), (cx + 5, 92)], C1)
        for k in (-5, 5): poly([(cx + k - 1, 92), (cx + k, 84), (cx + k + 1, 92)], C1)   # pinnacles
        d.line([(cx - 5, 92), (cx - 5, 141)], fill=CR + (255,)); d.line([(cx - 4, 90), (cx, 68 if cx < 215 else 72)], fill=C0 + (255,))
        for y in (100, 110, 120): rect(cx - 1, y, cx, y + 5, (110, 70, 100))
    d.ellipse([211, 110, 219, 118], fill=(255, 196, 140, 255)); d.ellipse([213, 112, 217, 116], fill=(224, 140, 120, 255))   # the rose window, sunlit
    d.line([(198, 116), (215, 102)], fill=CR + (255,))
    # --- the Spire before the storm: a slender lighthouse tower, its lamp lit
    T0, T1, TR = (70, 58, 96), (56, 46, 82), (150, 120, 150)
    poly([(318, 141), (320, 96), (321, 86), (325, 86), (326, 96), (328, 141)], T1)
    poly([(318, 141), (320, 96), (321, 86), (322, 86), (322, 141)], T0)
    rect(319, 84, 327, 85, T1); rect(320, 79, 326, 83, (255, 226, 160)); rect(321, 80, 325, 82, (255, 248, 220))
    poly([(319, 79), (323, 72), (327, 79)], T1); d.line([(323, 72), (323, 68)], fill=T1 + (255,))
    d.line([(318, 141), (320, 96)], fill=TR + (255,))
    for y in (100, 114, 128): px(323, y, (255, 200, 130))
    # aerial haze: the lower parts sink into the glow over the cloud sea; then the sea laps their feet (a ragged cut)
    a = np.asarray(im).copy(); rng = np.random.default_rng(4)
    yy = np.arange(FH)[:, None]; t = (np.clip((yy - 112) / 28, 0, 1) * 0.45)[..., None]
    a[..., :3] = np.round(a[..., :3] * (1 - t) + np.array([214, 160, 168]) * t).astype(np.uint8)
    for x in range(FW):
        cut = 139 + int(round(1.5 * math.sin(x / 7.0) + rng.uniform(-0.6, 0.6)))
        a[cut:, x, 3] = 0
    return Image.fromarray(a, 'RGBA')


PICK = dict(far=2, near=1)
LAND_V2 = True   # False: the first, flat 1x landmarks (kept for comparison)
FAC = dict(far=(0.02, 0.03), land=(0.035, 0.03), near=(0.12, 0.12))


def grade(a):
    """Calmer than the render: the game's bloom spreads anything near white, so the sea and the sky's glow are pulled down
    (highlights compressed 2:1 above lum 150, the cloud sea a further step, a little more saturation in the shadows); the sun disc
    itself keeps its white."""
    P = L.Canvas(FW, FH, ); X, Y = P.X[::3, ::3], P.Y[::3, ::3]
    l = L.lum(a)[..., None]; sun = (np.hypot(X - 146, Y - 133) < 11)[..., None]
    k = np.where(l > 150, (150 + (l - 150) * 0.5) / np.maximum(l, 1), 1.0)
    sea = np.clip((Y - 140) / 20, 0, 1)[..., None]
    b = a * k * (1 - 0.12 * sea) * 0.94
    m = b.mean(-1, keepdims=True); b = m + (b - m) * 1.12
    # the room light treats pixels whose brightest channel passes ~214 as emissive: a halo fading slowly across that line
    # shows as a wide dithered ring in game, so the sky's glow crosses it in a narrow step (a painted halo ring instead)
    mx = b.max(-1, keepdims=True); sky = (Y < 139)[..., None]
    push = np.where(mx > 214, np.minimum(mx + 14, np.maximum(mx, 228)) / np.maximum(mx, 1), np.maximum(mx - 14, np.minimum(mx, 196)) / np.maximum(mx, 1))
    near = ((mx > 190) & (mx < 238)) & sky
    b = np.where(near, b * push, b)
    return np.clip(np.where(sun, a, b), 0, 255)


def build(no_ase=False):
    hero = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    f1 = grade(L.down(hero, FW, FH))
    qf, _ = L.to_pixels(f1, 40, dk=0.35, hi=10, hi_lum=200, lo=6, lo_lum=60)
    out = {'far': L.rgba(qf), 'land': land2() if LAND_V2 else landmarks()}
    for k, im in out.items(): im.save(f'{SRC}/out_{k}.png')
    LAY = [(out['far'], *FAC['far'], 0, False), (out['land'], *FAC['land'], 0, False)]
    if os.path.exists(f'{SRC}/out_near.png'): LAY.append((Image.open(f'{SRC}/out_near.png'), *FAC['near'], 0, False))
    L.composite_preview(LAY, f'{SRC}/preview.png', [(116, 168), (384, 168), (0, -9)])
    if not no_ase:
        for k, im in out.items(): L.build(f'vista_{ROOM}_{k}', [im])
    return out


# ------------------------------------------------------------------------------------------------- landmarks v2 (lead review)
# The 1x cut-outs read flat and pasted on. v2: each landmark is built at 3x from separate masses (crag strata, curtain wall,
# towers, keep, gatehouse; west towers, spires, nave; stack, tower, lantern), every mass lit by its own ramp from the shaded
# side to the sun side, a warm rim on its sunward edge, aerial perspective toward the sky render's own colour behind it
# (farther = more haze, more near the base where the cloud sea's mist rises), and billows of cloud wrapping the feet. Then a
# texture pass (img2img denoise ~0.42 over sky + landmarks) and a cut back out with the landmarks' own alpha.
PROMPT_LAND2 = ('pixel art, golden hour seen from above a sea of clouds, distant fortress castle with towers and conical roofs on a '
                'rocky crag, a gothic cathedral with twin spires and a rose window half sunk in clouds, a slender lighthouse on a sea '
                'stack before a thunderhead, rim lit by the low sun, aerial perspective, hazy violet and rose, cloud tops around their '
                'bases, painterly, side-scroller game background, highly detailed')
TEX2 = dict(seed=4, denoise=0.42, cn=0.6, cn_end=0.75, pix=0.4)


def land2_paint():
    C = L.Canvas(FW, FH); X, Y = C.X, C.Y
    sky = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB').resize((FW * S, FH * S), Image.LANCZOS), float)
    haze = np.stack([L.gblur(sky[..., i], 30) for i in range(3)], -1)
    haze = haze * 0.6 + np.array([128, 96, 150.]) * 0.4          # aerial colour: the sky behind, cooled toward violet
    sea_row = np.stack([L.gblur(sky[int((HZ + 10) * S):int((HZ + 10) * S) + 1, :, i], 6)[0] for i in range(3)], -1)   # the sea's colour per column
    rgb = np.zeros_like(sky); al = np.zeros(X.shape)
    sx = 146

    def part(pts, depth, shade=(78, 56, 96), lit=(206, 136, 120), rim=True, glow=None):
        nonlocal rgb, al
        m = C.mask_poly(pts)
        if m.max() < 0.5: return m
        xs = X[m > 0.5]; x0, x1 = xs.min(), xs.max()
        sunward = 1 if (x0 + x1) / 2 < sx else -1
        t = np.clip((X - x0) / max(1e-3, x1 - x0), 0, 1); t = t if sunward > 0 else 1 - t
        col = lerp(np.array(shade, float), np.array(lit, float), smooth(0.35, 1.0, t)[..., None])
        if rim:   # the sunward edge: a warm rim ~1 game px wide
            edge = np.clip(m - np.roll(m, -sunward * S, axis=1), 0, 1)
            col = col * (1 - edge[..., None]) + np.array((255, 196, 150.)) * edge[..., None]
        k = np.clip(depth + (1 - depth) * 0.55 * np.clip((Y - (HZ - 36)) / 36, 0, 1), 0, 0.85)[..., None]
        col = col * (1 - k) + haze * k
        rgb = rgb * (1 - m[..., None]) + col * m[..., None]; al = np.maximum(al, m)
        return m

    def lights(pts, col=(255, 210, 140)):
        nonlocal rgb
        for x, y in pts:
            m = C.ellipse(x, y, 0.6, 0.9); rgb = rgb * (1 - m[..., None]) + np.array(col, float) * m[..., None]

    # --- the Ramparts (mid distance, left of the sun: lit on their right)
    D = 0.32
    part([(2, 141), (6, 128), (10, 124), (12, 116), (18, 112), (20, 106), (30, 104), (44, 103), (60, 104), (68, 108), (74, 106),
          (80, 114), (86, 122), (90, 130), (96, 141)], D, shade=(52, 38, 70), lit=(150, 92, 104))                   # the crag
    for y0, x0, x1 in [(116, 14, 40), (124, 8, 30), (120, 46, 72), (130, 58, 88)]:                                   # strata ledges
        part([(x0, y0), (x1, y0 + 1), (x1, y0 + 2.2), (x0, y0 + 1.2)], D, shade=(74, 52, 86), lit=(190, 120, 116), rim=False)
    part([(16, 106), (16, 94), (80, 94), (80, 106)], D)                                                              # curtain wall
    for x in range(16, 81, 3): part([(x, 94), (x, 92), (x + 1.6, 92), (x + 1.6, 94)], D, rim=False)                   # crenels
    for cx, top, w in [(18, 82, 3.5), (74, 80, 3.5)]:                                                                # round towers
        part([(cx - w, 106), (cx - w, top), (cx + w, top), (cx + w, 106)], D)
        part([(cx - w - 1, top), (cx, top - 11), (cx + w + 1, top)], D, shade=(70, 44, 80), lit=(190, 104, 104))
    part([(28, 106), (28, 86), (34, 86), (34, 106)], D)                                                             # a square tower
    for x in (28, 31): part([(x, 86), (x, 84), (x + 1.5, 84), (x + 1.5, 86)], D, rim=False)
    part([(38, 106), (38, 68), (54, 68), (54, 106)], D - 0.04)                                                       # the keep
    for x in range(38, 55, 3): part([(x, 68), (x, 65.5), (x + 1.6, 65.5), (x + 1.6, 68)], D - 0.04, rim=False)
    part([(43, 68), (43, 54), (49, 54), (49, 68)], D - 0.04)                                                         # its turret
    part([(42, 54), (46, 41), (50, 54)], D - 0.04, shade=(70, 44, 80), lit=(190, 104, 104))
    part([(45.6, 41), (45.6, 35), (46.4, 35), (46.4, 41)], D - 0.04, rim=False)
    part([(58, 106), (58, 84), (68, 84), (68, 106)], D)                                                             # gatehouse
    for cx in (58.5, 67.5): part([(cx - 1.8, 84), (cx - 1.8, 78), (cx + 1.8, 78), (cx + 1.8, 84)], D); part([(cx - 2.4, 78), (cx, 72), (cx + 2.4, 78)], D, shade=(70, 44, 80), lit=(190, 104, 104))
    lights([(42, 76), (50, 76), (46, 60), (18, 92), (74, 90), (31, 96), (63, 96), (24, 100), (70, 100)])
    # --- the drowned Cathedral (nearest, right of the sun: lit on its left), sunk to its waist in cloud
    D = 0.22
    part([(204, 141), (204, 112), (215, 99), (226, 112), (226, 141)], D, shade=(84, 56, 96), lit=(214, 142, 126))    # the nave gable
    for cx, top in [(200, 64), (230, 68)]:
        part([(cx - 5.5, 141), (cx - 5.5, 92), (cx + 5.5, 92), (cx + 5.5, 141)], D)                                  # west towers
        part([(cx - 6.5, 92), (cx + 6.5, 92), (cx + 6.5, 89), (cx - 6.5, 89)], D)                                    # their cornice
        part([(cx - 4.5, 89), (cx, top), (cx + 4.5, 89)], D, shade=(76, 48, 88), lit=(214, 136, 122))                # spires
        for k in (-6, 6): part([(cx + k - 1, 89), (cx + k, 80), (cx + k + 1, 89)], D)                                # pinnacles
        for y in (98, 110, 122):                                                                                      # lancets
            part([(cx - 1.4, y + 7), (cx - 1.4, y + 2), (cx, y), (cx + 1.4, y + 2), (cx + 1.4, y + 7)], D, shade=(48, 30, 60), lit=(90, 56, 80), rim=False)
    part([(196, 141), (198, 130), (202, 128), (204, 141)], D + 0.1)                                                  # a buttress
    m = C.ellipse(215, 113, 4.6, 4.6); rgb = rgb * (1 - m[..., None]) + np.array((252, 190, 140.)) * m[..., None]; al = np.maximum(al, m)
    m = C.ellipse(215, 113, 2.0, 2.0); rgb = rgb * (1 - m[..., None]) + np.array((214, 120, 112.)) * m[..., None]   # the rose window, sunlit
    # --- the Spire's lighthouse on its sea stack (far, in the storm's shadow: dark, little rim)
    D = 0.42
    part([(310, 141), (312, 128), (316, 120), (322, 117), (330, 119), (334, 128), (337, 141)], D, shade=(54, 42, 74), lit=(120, 86, 110))
    part([(318, 119), (320, 90), (326, 90), (328, 119)], D - 0.12, shade=(46, 36, 66), lit=(130, 96, 120))
    part([(316.5, 90), (329.5, 90), (329.5, 87.5), (316.5, 87.5)], D - 0.12, shade=(46, 36, 66), lit=(130, 96, 120))
    m = C.mask_poly([(319.5, 87.5), (319.5, 80), (326.5, 80), (326.5, 87.5)]); rgb = rgb * (1 - m[..., None]) + np.array((255, 220, 150.)) * m[..., None]; al = np.maximum(al, m)
    part([(318.5, 80), (323, 72), (327.5, 80)], D - 0.12, shade=(46, 36, 66), lit=(130, 96, 120))
    part([(322.6, 72), (322.6, 67), (323.4, 67), (323.4, 72)], D - 0.12, rim=False)
    lights([(323, 100), (323, 110)], (255, 200, 130))
    # --- cloud billows wrapping their feet (the sea's own colours: lit tops, lavender undersides)
    rng = np.random.default_rng(17)
    for x0, x1, y0 in [(-10, 104, 136), (186, 244, 131), (300, 346, 137)]:
        x = x0
        while x < x1:
            edge = min(x - x0, x1 - x) / 14                                 # lower toward the ends: the sea rises around them, no plate
            r = rng.uniform(3, 7) * min(1, 0.5 + edge); cy = y0 + rng.uniform(-1, 4) + (1 - min(1, edge)) * 4
            m = C.ellipse(x, cy, r * 1.5, r * 0.75)
            top = np.clip((cy - Y) / (r * 0.75), 0, 1)
            col = sea_row[None, :, :] * (0.92 + 0.16 * top[..., None]) + np.array([14, 8, 0.]) * top[..., None]
            rgb = rgb * (1 - m[..., None]) + col * m[..., None]; al = np.maximum(al, m)
            x += r * rng.uniform(1.2, 1.9)
        m = ((Y > y0 + 4) & (X > x0) & (X < x1)).astype(float)
        rgb = rgb * (1 - m[..., None]) + sky * m[..., None]; al = np.maximum(al, m)            # under the billows: the sea itself
    al = al * (Y < HZ + 6)
    return rgb, al, sky


def land2(force=False):
    rgb, al, sky = land2_paint()
    comp = sky * (1 - al[..., None]) + rgb * al[..., None]
    gp = f'{SRC}/guide_land2.png'; Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(gp)
    L.edges(Image.open(gp)).save(f'{SRC}/edge_land2.png')
    np.save(f'{SRC}/_land2_alpha.npy', al.astype(np.float16))
    out = f'{SRC}/land2_render.png'
    if force or not os.path.exists(out):
        L.use_prefix(ROOM); L.render(gp, f'{SRC}/edge_land2.png', PROMPT_LAND2, TEX2['seed'], out, denoise=TEX2['denoise'], cn=TEX2['cn'],
                                     cn_end=TEX2['cn_end'], pix=TEX2['pix'], blur=0.8)
    a1 = L.key(al, FW, FH, thresh=0.5)
    r1 = grade(L.down(Image.open(out), FW, FH))
    q, _ = L.to_pixels(r1, 30, mask=a1, dither=False, hi=6, hi_lum=180)
    # the texture pass softens the rims: put a 1 px sun-side rim back on every edge above the cloud tops
    yy, xx = np.mgrid[0:FH, 0:FW]
    toward = np.where(xx < 146, np.roll(a1, -1, axis=1), np.roll(a1, 1, axis=1))
    edge = a1 & ~toward & (yy < HZ - 7)
    q = np.where(edge[..., None], q * 0.35 + np.array([255, 190, 146]) * 0.65, q)
    return L.rgba(np.where(a1[..., None], q, 0), a1)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--guide' in a: save_guides(); sys.exit()
    if '--sweep' in a: cli_sweep(a); sys.exit()
    build(no_ase='--no-ase' in a)
