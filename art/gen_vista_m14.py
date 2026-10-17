#!/usr/bin/env python3
"""M14 Fisherman's Rest vista (agent V1, docs/v17/vista_v1.md): dusk on the still marsh, lanterns on the water.

  python3 art/gen_vista_m14.py [--guide | --sweep <layer> 1,2,3 [--dn x --cn x --pix x --tag t] | --render] [--no-ase]
  (vista_v1_lib.cli; builds assets/vista_m14_{far,mid} from the saved renders in art/bg_src/vista_m14/)

Lore (rb_2): "The old fisher of the Grove sat here every dusk and counted the lights on the water. Some nights there were more
than there were lanterns." The regular mire backdrop is a green moonlit night with the drowned chapel; this view is the last
of the dusk: an amber afterglow low under a deep teal sky, the drowned cypresses and a far stilt village in silhouette, the
marsh a black mirror, lanterns on poles across the water (and, if you count, a few pale lights that stand on nothing).
"""
import os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import lerp

ROOM = 'M14'
SRC = os.path.join(HERE, 'bg_src', 'vista_m14')
TINT = '#0a1210'
FAR = dict(sheet='vista_m14_far', w=400, h=224, fac=0.04, vfac=0.1, x=-4, dy=4)
MID = dict(sheet='vista_m14_mid', w=400, h=224, fac=0.12, vfac=0.1, x=-4, dy=4)
HOR = 112
GLOW = (300, HOR - 2)
# lanterns on poles standing in the water: (x, base row on the water, pole height); wisps: (x, y) pale lights on nothing
LANTERNS = [(70, 150, 16), (132, 128, 9), (186, 121, 6), (236, 118, 4), (262, 116, 3), (352, 132, 11), (384, 160, 20), (214, 140, 13)]
WISPS = [(160, 133), (282, 124), (110, 168), (330, 146)]

PROMPTS = {
    'far': ('pixel art, dark fantasy swamp at dusk, a still black marsh like a mirror, the last amber and rose light glowing low on the '
            'horizon under a deep teal sky with first stars, silhouettes of drowned dead cypress trees hung with long moss on small '
            'islets, a distant stilt village and a ruined chapel spire with a few warm lit windows, small lanterns on wooden poles '
            'standing in the water with long golden reflections, low mist banks, melancholic and serene, empty, highly detailed, '
            'muted teal green and amber palette'),
    'mid': ('pixel art, dark fantasy swamp at dusk, dark silhouettes of tall reeds, cattails and a gnarled dead tree hung with moss in '
            'the foreground, rim lit by amber afterglow, a still marsh mirror and glowing horizon behind, highly detailed, teal green '
            'and amber palette'),
}
RENDER = {'far': dict(seed=1, dn=0.6, cn=0.55, cn_end=0.65, pix=0.5)}
# (a mid layer of reeds and a dead tree was tried, mid_s1..3: the tree rendered mushy and the reeds sit behind the room's own
#  water and reed props, so the room keeps one painted layer; guide_mid stays for reference)


def sky(G):
    G.rgb = G.vgrad([(0, (10, 22, 26)), (36, (16, 34, 38)), (64, (36, 56, 54)), (84, (96, 86, 66)), (100, (170, 114, 74)),
                     (HOR, (222, 156, 96)), (HOR + 1, (120, 90, 64))])
    G.glow(GLOW[0], GLOW[1], 190, 50, (80, 52, 24), 1.0, 1.3)
    G.glow(GLOW[0], GLOW[1], 60, 14, (60, 50, 30), 1.0, 1.5)
    rng = np.random.default_rng(2)
    for _ in range(60):
        x, y = rng.uniform(0, G.w), rng.uniform(0, 64); G.fill(G.ellipse(x, y, 0.5, 0.5, 2), (200, 220, 210), rng.uniform(0.3, 0.9) * (1 - y / 70))
    # thin cloud bars lit from below
    nz = G.noise(60, 5, 7, 3)
    for y0, k in [(70, 0.6), (82, 0.8), (92, 0.7)]:
        band = np.clip(1 - np.abs(G.Y - y0 - (nz - 0.5) * 6) / 1.8, 0, 1) * np.clip((nz - 0.35) * 3, 0, 1)
        G.fill(band, (40, 50, 48), 0.8 * k); G.add(np.roll(band, L.S, axis=0) * 0.7, (90, 60, 30), k)


def land(G):
    rng = np.random.default_rng(5)
    # the far treeline and village on the horizon
    prof = L.profile(G.w, 3, HOR - 1, 7, cells=((30, 1.0), (9, 0.5), (3, 0.3)))
    G.fill(G.poly([(x, prof[x]) for x in range(G.w + 1)] + [(G.w, HOR + 1), (0, HOR + 1)]), (36, 44, 40))
    # the stilt village and the chapel spire, against the glow
    vx = GLOW[0]
    for i, (dx, w, h, roof) in enumerate([(-34, 10, 7, 4), (-20, 8, 5, 3), (-6, 12, 8, 5), (10, 9, 6, 4), (24, 11, 7, 4), (40, 7, 4, 3)]):
        x0 = vx + dx; y0 = HOR - 3
        G.fill(G.poly([(x0, y0), (x0, y0 - h), (x0 + w / 2, y0 - h - roof), (x0 + w, y0 - h), (x0 + w, y0)]), (34, 34, 34))
        for sx in range(int(x0) + 1, int(x0 + w), 3): G.fill(G.poly([(sx, y0), (sx + 0.6, y0), (sx + 0.6, HOR + 1), (sx, HOR + 1)]), (34, 34, 34))
        if i % 2 == 0: G.fill(G.ellipse(x0 + w * 0.5, y0 - h * 0.5, 0.8, 0.9, 2), (255, 190, 110))
    cx = vx - 52
    G.fill(G.poly([(cx - 6, HOR), (cx - 6, HOR - 14), (cx - 2, HOR - 16), (cx - 2, HOR - 30), (cx, HOR - 40), (cx + 2, HOR - 30), (cx + 2, HOR - 16), (cx + 6, HOR - 14), (cx + 6, HOR)]), (30, 32, 32))
    G.fill(G.ellipse(cx, HOR - 9, 1, 1.4, 2), (255, 180, 100), 0.9)
    # drowned cypresses on islets, moss hanging
    for (x, base, h, w) in [(28, HOR + 6, 62, 10), (54, HOR + 3, 40, 7), (120, HOR, 26, 5), (360, HOR + 4, 50, 8), (388, HOR + 8, 70, 11), (214, HOR, 18, 4)]:
        G.fill(G.poly([(x - w * 1.4, base + 1), (x - w * 0.4, base - 3), (x - w * 0.25, base - h * 0.9), (x, base - h), (x + w * 0.25, base - h * 0.85), (x + w * 0.4, base - 3), (x + w * 1.4, base + 1)]), (22, 30, 28))
        import bgroll_a_lib as A
        segs = []
        for k in range(5):
            yy = base - h * (0.35 + 0.12 * k); ang = -math.pi / 2 + (0.9 if k % 2 else -0.9) * rng.uniform(0.6, 1.0)
            segs += A.tree_segs(rng, x, yy, ang, h * 0.35, w * 0.22, 1, step=1.5, trop=0.01, jitter=0.15, min_w=0.5)
        G.fill(G.lines(segs), (22, 30, 28))
        moss = []
        for k in range(14):
            mx = x + rng.uniform(-w * 2.2, w * 2.2); my = base - h * rng.uniform(0.3, 0.9); ln = rng.uniform(4, 12)
            moss.append((mx, my, mx + rng.normal(0, 0.6), my + ln, 0.6))
        G.fill(G.lines(moss), (30, 40, 34), 0.9)
        G.fill(G.poly([(x - w * 2.2, base + 1), (x - w * 1.2, base - 2), (x + w * 1.2, base - 2), (x + w * 2.2, base + 1)]), (24, 32, 28))
    # mist banks over the water at the horizon
    nz = G.noise(50, 4, 9, 3)
    G.fill(np.clip(1 - np.abs(G.Y - HOR - 2) / 5, 0, 1) * np.clip(nz * 1.4 - 0.3, 0, 1), (110, 104, 88), 0.55, cover=False)


def water(G):
    """The still marsh: the sky mirrored, darker, with long lantern reflections and a few lily pads."""
    S = L.S; y0 = int(HOR * S); hh = G.HS
    src = G.rgb.copy()
    for y in range(y0 + 1, hh):
        sy = 2 * y0 - y
        if sy < 0: break
        f = (y - y0) / (hh - y0)
        G.rgb[y] = src[sy] * (0.62 - 0.3 * f) * np.array([0.85, 0.95, 1.0]) + np.array([2, 6, 6])
    # ripple lines
    nz = G.noise(40, 1.2, 13, 2)
    G.add(np.clip((nz - 0.62) * 4, 0, 1) * (G.Y > HOR + 2), (18, 16, 10), 1.0)
    # lily pads near the viewer
    rng = np.random.default_rng(8)
    for _ in range(26):
        x, y = rng.uniform(0, G.w), rng.uniform(HOR + 40, 220); r = 2 + (y - HOR) * 0.03
        G.fill(G.ellipse(x, y, r * 1.8, r * 0.6), (24, 40, 30))
    # lanterns on poles + their long reflections; wisps
    for (x, b, h) in LANTERNS:
        s = 0.5 + (b - HOR) / 60
        G.fill(G.poly([(x - 0.35 * s, b), (x - 0.35 * s, b - h), (x + 0.35 * s, b - h), (x + 0.35 * s, b)]), (28, 26, 22))
        G.fill(G.ellipse(x, b - h - 1.2 * s, 0.9 * s, 1.2 * s, 2), (255, 196, 110))
        G.glow(x, b - h - 1.2 * s, 6 * s, 6 * s, (90, 56, 20), 1.0, 2)
        refl = G.poly([(x - 0.7 * s, b + 1), (x + 0.7 * s, b + 1), (x + 0.4 * s, b + h * 1.6 + 6 * s), (x - 0.4 * s, b + h * 1.6 + 6 * s)])
        G.add(refl * (0.6 + 0.4 * np.sin(G.Y * 3.1)), (110, 70, 26), 0.9)
    for (x, y) in WISPS:
        G.fill(G.ellipse(x, y, 0.9, 0.9, 2), (200, 240, 210)); G.glow(x, y, 5, 5, (40, 70, 50), 1.0, 2)
        G.add(G.poly([(x - 0.5, y + 4), (x + 0.5, y + 4), (x + 0.3, y + 4 + (y - HOR) * 0.5), (x - 0.3, y + 4 + (y - HOR) * 0.5)]), (40, 70, 50), 0.7)


def guide_far():
    G = L.VG(FAR['w'], FAR['h']); sky(G); land(G); water(G); return G


def guide_mid():
    G = guide_far(); G.a = np.zeros_like(G.X)
    rng = np.random.default_rng(14)
    m = np.zeros_like(G.X)
    # reeds and cattails in the near water, left and right clumps (the room's hut is in the middle)
    segs = []
    for cx, n, spread, hmax in [(30, 40, 34, 46), (372, 34, 30, 40), (120, 14, 16, 24), (300, 12, 14, 22)]:
        for _ in range(n):
            x = cx + rng.normal(0, spread * 0.5); base = 222; h = rng.uniform(0.4, 1) * hmax; lean = rng.normal(0, 0.12)
            segs.append((x, base, x + lean * h, base - h, rng.uniform(0.6, 1.1)))
            if rng.random() < 0.25: segs.append((x + lean * h, base - h + 1, x + lean * h, base - h + 5, 1.6))   # a cattail head
    m = np.maximum(m, G.lines(segs))
    # a gnarled dead tree on the right bank, moss hanging
    import bgroll_a_lib as A
    tr = A.tree_segs(rng, 352, 224, -math.pi / 2 - 0.08, 120, 6.5, 3, step=2.0, trop=0.02, jitter=0.16, spread=(0.4, 0.9), p_branch=0.07, min_w=0.6)
    m = np.maximum(m, G.lines([s for s in tr if s[1] > 30]))
    moss = []
    for x0, y0, x1, y1, w in tr:
        if w < 2.5 and y1 > 40 and rng.random() < 0.35: moss.append((x1, y1, x1 + rng.normal(0, 0.5), y1 + rng.uniform(5, 14), 0.6))
    m = np.maximum(m, G.lines(moss))
    G.fill(m, (14, 20, 18))
    rim = m * (np.roll(m, 1 * L.S, axis=1) < 0.5)
    G.add(rim, (90, 60, 30), 0.8)
    return G


def guides():
    return {'far': guide_far()}


def build(no_ase=False):
    far_hi = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    pal = L.kpal(V.box_down(far_hi, FAR['w'], FAR['h']), 40) + [(255, 206, 128), (255, 170, 90), (206, 240, 214)]
    far = L.pixelize(far_hi, FAR['w'], FAR['h'], pal, dk=0.35)
    # the lights on the water (warm glints below the horizon): their positions feed the fx flicker in 85v_v1.js
    lum = far @ np.array([0.299, 0.587, 0.114]); warm = (far[..., 0] - far[..., 2]) > 40
    pts = []
    for y in range(HOR - 14, FAR['h'] - 1):
        for x in range(1, FAR['w'] - 1):
            if lum[y, x] > 150 and lum[y, x] >= lum[y - 1:y + 2, x - 1:x + 2].max() and not any(abs(x - a) < 4 and abs(y - b) < 6 for a, b in pts):
                pts.append((x, y))
    import json; json.dump(pts, open(f'{SRC}/lights.json', 'w'))
    far_im = L.to_rgba(far)
    far_im.save(f'{SRC}/out_far.png')
    L.comp_preview(ROOM, [(FAR, far_im)], TINT, f'{SRC}/preview.png')
    print('far colours', len(pal), 'lights', pts)
    if not no_ase:
        L.ase('vista_m14_far', [far_im])


if __name__ == '__main__':
    L.cli(sys.modules[__name__])
