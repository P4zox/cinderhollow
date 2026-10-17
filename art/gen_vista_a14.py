#!/usr/bin/env python3
"""A14 The Reading Nook vista (agent V1, docs/v17/vista_v1.md): rain on the glass, the Root through the east wing.

  python3 art/gen_vista_a14.py [--guide | --sweep far 1,2,3 [--dn x --cn x --pix x --tag t] | --render] [--no-ase]
  (vista_v1_lib.cli; builds assets/vista_a14_{far,flash} from the saved renders in art/bg_src/vista_a14/)

Lore (rb_7, Rain on the Glass): "The rain has not stopped since the Root broke through the east wing. The windows are the only
clean thing left ... the candles in the stacks have started to burn violet." The nook is a room: the vista is only what the
tall arched window shows (the room's wall stays; 85v_v1.js opens the window), so the painting is composed for that 80 x 104 px
opening: the rain-dark sky, the Archives' east wing broken open, the Pale Root rising pale through it, violet candle windows in
the far stacks. The painting is room-locked (A14 is exactly one screen wide; fac 0, vfac 1).
"""
import os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import lerp

ROOM = 'A14'
SRC = os.path.join(HERE, 'bg_src', 'vista_a14')
TINT = '#0c0a12'
FAR = dict(sheet='vista_a14_far', w=384, h=224, fac=0.0, vfac=1.0, x=0, dy=8)
WIN = (240, 31, 320, 134)      # the window's glass in room px (xrb_awin interior: x 8..87, y 13..116 of the sprite at (232, 18))
ROOT_X = 280   # the centre pane (the mullions sit at x 263 and 295)

PROMPTS = {
    'far': ('pixel art, dark fantasy, view through a tall window at night in heavy rain, a ruined gothic library wing with broken '
            'tall lancet windows glowing faint violet candlelight, a colossal pale luminous tree root bursting up through its '
            'collapsed roof and rising into the storm clouds, thin pale rootlets, distant gothic spires and towers with small '
            'violet lit windows, slanting rain, dark indigo violet sky, melancholic, highly detailed, indigo, violet and pale '
            'ivory palette'),
}
RENDER = {'far': dict(seed=1, dn=0.58, cn=0.55, cn_end=0.65, pix=0.5, tag='c')}


# the painting is rendered for the window's neighbourhood only (CROP, room px), at 2x the guide's usual scale (6 render px per
# game px), so the model composes for the opening and spends its detail there; the rest of the layer is hidden by the wall
CROP = (224, 10, 352, 162)
K = 2


def guide_far():
    cx0, cy0, cx1, cy1 = CROP; G = L.VG((cx1 - cx0) * K, (cy1 - cy0) * K)
    X = lambda x: (x - cx0) * K; Y = lambda y: (y - cy0) * K
    G.rgb = G.vgrad([(0, (18, 14, 32)), (Y(60), (34, 28, 56)), (Y(100), (60, 50, 82)), (Y(112), (50, 42, 70)), (G.h, (22, 18, 32))])
    nz = G.noise(26, 9, 3, 4)
    G.fill(np.clip((nz - 0.42) * 3, 0, 1) * (G.Y < Y(96)), (26, 22, 44), 0.85)
    rng = np.random.default_rng(6)
    import bgroll_a_lib as A
    # far: the Pale Root, slender and distant, its limbs lost in the cloud, a cold glow around it
    rx = X(300)
    G.glow(rx, Y(70), 40 * K, 46 * K, (40, 36, 48), 1.0, 1.4)
    pts_l, pts_r = [], []
    for i in range(41):
        t = i / 40; y = Y(108) - t * (Y(108) - Y(50)); half = (2.6 - 1.4 * t + 2.5 * (1 - t) ** 10) * K; xc = rx + 2 * K * math.sin(t * 2.2)
        pts_l.append((xc - half, y)); pts_r.append((xc + half, y))
    G.fill_img(G.poly(pts_l + pts_r[::-1]), lerp(np.array((120, 110, 132), float), np.array((214, 206, 200), float), np.clip(0.5 + 0.5 * np.clip((G.X - rx) / (2.5 * K), -1, 1), 0, 1)[..., None]))
    segs = []
    for (ang, ln, w) in [(-0.75, 40, 1.4), (-2.35, 36, 1.3), (-1.3, 30, 1.1), (-1.85, 28, 1.0)]:
        segs += A.tree_segs(rng, rx + 2 * K * math.sin(2.2), Y(52), -math.pi / 2 + (ang + math.pi / 2), ln * K, w * K, 2, step=1.6 * K, target=-math.pi / 2, trop=0.01, jitter=0.15, min_w=0.6 * K)
    G.fill(G.lines(segs) * np.clip((G.Y - Y(16)) / (20 * K), 0.3, 1), (170, 160, 170))
    # rain haze between the root and the city
    G.fill(np.clip((G.Y - Y(80)) / (30 * K), 0, 1) * (G.Y < Y(112)), (56, 48, 78), 0.5, cover=False)
    # the far stacks of the Archives: a skyline of spires with tiny violet windows
    m = np.zeros_like(G.X)
    for i in range(18):
        x = X(rng.uniform(226, 352)); w = rng.uniform(4, 9) * K; top = Y(rng.uniform(96, 112)); sp = rng.uniform(4, 12) * K
        m = np.maximum(m, G.poly([(x - w / 2, G.h), (x - w / 2, top), (x, top - sp), (x + w / 2, top), (x + w / 2, G.h)]))
    G.fill(m, (40, 32, 58))
    for i in range(50):
        x, y = rng.uniform(0, G.w), rng.uniform(Y(100), Y(140))
        G.fill(G.ellipse(x, y, 0.5 * K, 0.8 * K, 2) * m, (150, 110, 230), 0.8)
    # near: the east wing's tall tower (left pane) with pointed windows, its top broken, and a gabled roof line
    tw0, tw1 = X(246), X(266)
    tower = G.poly([(tw0, G.h), (tw0, Y(62)), (tw0 + 3 * K, Y(58)), (tw0 + 6 * K, Y(46)), (tw0 + 9 * K, Y(52)), (tw0 + 13 * K, Y(40)), (tw1 - 3 * K, Y(54)), (tw1, Y(60)), (tw1, G.h)])
    G.fill(tower, (26, 20, 38))
    for (wx, wy) in [(250, 72), (258, 72), (250, 90), (258, 90), (254, 108)]:
        lan = G.poly([(X(wx), Y(wy + 6)), (X(wx), Y(wy + 1.5)), (X(wx + 1), Y(wy)), (X(wx + 2), Y(wy + 1.5)), (X(wx + 2), Y(wy + 6))])
        G.fill(lan, (170, 120, 240) if (wx + wy) % 3 else (60, 46, 86))
    roof = G.poly([(X(266), G.h), (X(266), Y(118)), (X(286), Y(104)), (X(306), Y(118)), (X(314), Y(112)), (X(330), Y(124)), (X(352), Y(120)), (X(352), G.h)])
    G.fill(roof, (22, 18, 32))
    G.add(G.lines([(X(266), Y(118), X(286), Y(104), 0.8 * K), (X(286), Y(104), X(306), Y(118), 0.8 * K)]), (60, 52, 80), 1.0)   # wet ridge
    for (wx, wy) in [(280, 122), (290, 122), (318, 128)]:
        G.fill(G.poly([(X(wx), Y(wy + 5)), (X(wx), Y(wy + 1.5)), (X(wx + 1), Y(wy)), (X(wx + 2), Y(wy + 1.5)), (X(wx + 2), Y(wy + 5))]), (190, 140, 250))
    # rain
    st = np.clip(np.sin((G.X * 1.0 + G.Y * 0.28) * 1.1 + G.noise(2, 26, 9, 2) * 9) * 0.5 + 0.5, 0, 1) ** 8
    G.add(st, (40, 40, 60), 0.4)
    return G


def guides():
    return {'far': guide_far()}


def flash_frame(a):
    """Lightning: the sky and the cloud undersides go pale violet-white, the silhouettes stay dark."""
    lum = a @ np.array([0.299, 0.587, 0.114]); hh, ww = lum.shape
    Y = (np.arange(hh)[:, None] + 0.5) / L.S
    Y2R = lambda y: CROP[1] + y / K
    sky = np.clip((Y2R(Y) - 100) / -40, 0, 1) * np.clip((lum - 18) / 50, 0, 1)
    return np.clip(a * (1 + 1.8 * sky)[..., None] + (sky * 40)[..., None] * np.array([0.9, 0.9, 1.2]), 0, 255)


def build(no_ase=False):
    cx0, cy0, cx1, cy1 = CROP; cw, ch = cx1 - cx0, cy1 - cy0
    # graded up: the archives' ambient halves whatever the parallax shows, and the window must out-shine the dim nook
    far_hi = V.grade(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float), black=4, white=150, gamma=1.25, sat=1.1)
    fl_hi = flash_frame(far_hi)
    pal = L.kpal(V.box_down(far_hi, cw, ch), 36) + L.kpal(V.box_down(fl_hi, cw, ch), 8)
    far = np.zeros((FAR['h'], FAR['w'], 3)); fl = np.zeros_like(far); far[:] = (12, 10, 18); fl[:] = (12, 10, 18)
    far[cy0:cy1, cx0:cx1] = L.pixelize(far_hi, cw, ch, pal, dk=0.3)
    fl[cy0:cy1, cx0:cx1] = L.pixelize(fl_hi, cw, ch, pal, dk=0.3)
    diff = np.abs(fl - far).sum(2) > 0
    far_im, fl_im = L.to_rgba(far), L.to_rgba(fl, diff)
    far_im.save(f'{SRC}/out_far.png'); fl_im.save(f'{SRC}/out_flash.png')
    x0, y0, x1, y1 = WIN
    win = far_im.crop((x0 - 8, y0 - 18, x1 + 9, y1 + 13)); awin = Image.open(os.path.join(L.ROOT, 'assets', 'xrb_awin.png')).convert('RGBA')
    win.alpha_composite(awin, (0, 0)); win.resize((win.width * 3, win.height * 3), Image.NEAREST).save(f'{SRC}/preview.png')
    print('far colours', len(pal))
    if not no_ase:
        L.ase('vista_a14_far', [far_im]); L.ase('vista_a14_flash', [fl_im])


if __name__ == '__main__':
    L.cli(sys.modules[__name__])
