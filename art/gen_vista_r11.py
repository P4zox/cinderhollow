#!/usr/bin/env python3
"""R11 Watcher's Perch vista (agent V1, docs/v17/vista_v1.md): the Hallow at last light from the highest tower.

  python3 art/gen_vista_r11.py                 build assets/vista_r11_{far,mid} from the saved renders in art/bg_src/vista_r11/
  python3 art/gen_vista_r11.py --guide         only (re)paint the guides
  python3 art/gen_vista_r11.py --sweep far 1,2,3 [--dn 0.7 --cn 0.5 --pix 0.5]   pass-1 renders (ComfyUI :8188) + sheet
  python3 art/gen_vista_r11.py --render        guides + render the picked seeds (PICK), then build

Lore (ra_1): "A pale light rose over the Hallow where the Root stands, and did not set." The regular ramparts backdrop is an
ember sunset over the walls; this view looks the other way, over a valley drowned in mist, to the Pale Root on the horizon:
a colossal pale tree lit from within, the Hallow's spires at its foot, the wall and its signal fires winding toward it.
"""
import os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import hexc, lerp, smooth

ROOM = 'R11'
SRC = os.path.join(HERE, 'bg_src', 'vista_r11')
TINT = '#120f20'
FAR = dict(sheet='vista_r11_far', w=432, h=240, fac=0.02, vfac=0.3, x=-4, dy=12)
MID = dict(sheet='vista_r11_mid', w=432, h=240, fac=0.12, vfac=0.3, x=-4, dy=12)
HOR = 134            # horizon row (screen y ~122 at the bench)
ROOT = (300, 134)    # the Pale Root's foot on the horizon

PROMPT_FAR = ('pixel art, dark fantasy landscape at dusk seen from a high castle tower, a colossal pale glowing world tree on the far '
              'horizon rising into the clouds, its slender trunk of furrowed ashen ivory bark softly lit, a vast bare branching crown, a pale '
              'halo of light around it, a ruined gothic city of spires at its feet, '
              'a sea of mist filling the valley below, long thin clouds lit rose and gold from beneath, first stars in a deep indigo '
              'violet sky, distant mountain ridges in haze, mythic, serene, atmospheric perspective, highly detailed, '
              'muted violet, rose and pale gold palette')
PROMPT_MID = ('pixel art, dark fantasy, dark rocky crags rising out of a sea of mist at dusk, a ruined castle wall with crenellations '
              'running along the ridge, a slender stone watchtower with a small signal fire burning on top, rim light of rose and gold '
              'on the edges, a vast glowing pale world tree far away on the horizon, deep violet sky, atmospheric, highly detailed')

RENDER = {'far': dict(seed=1, dn=0.66, cn=0.5, cn_end=0.65, pix=0.5, tag='c'),
          'mid': dict(seed=1, dn=0.6, cn=0.55, cn_end=0.7, pix=0.55)}


def sky(G):
    img = G.vgrad([(0, (16, 13, 32)), (30, (26, 19, 50)), (62, (46, 28, 70)), (92, (88, 44, 86)), (112, (142, 64, 92)),
                   (126, (196, 104, 92)), (HOR, (232, 160, 116)), (HOR + 1, (190, 130, 128))])
    G.rgb = img
    # the light that did not set: a broad pale-gold bloom around the Root's crown and foot
    G.glow(ROOT[0], HOR - 30, 190, 120, (60, 44, 30), 1.0, 1.6)
    G.glow(ROOT[0], HOR - 6, 120, 40, (70, 58, 40), 1.0, 1.4)
    G.glow(ROOT[0] - 4, HOR - 70, 70, 70, (40, 36, 34), 1.0, 1.5)
    # stars in the deep sky
    rng = np.random.default_rng(5)
    for _ in range(90):
        x, y = rng.uniform(0, G.w), rng.uniform(0, 70) ** 1.0
        b = rng.uniform(0.4, 1.0) * (1 - y / 80)
        G.fill(G.ellipse(x, y, 0.5, 0.5, 2), (220, 214, 236), b)
    # long thin clouds: dark plum bodies, rose/gold underlit edges, brighter toward the Root
    nz = G.noise(64, 6, 31, 3)
    for (y0, x0, x1, th, k) in [(48, -10, 210, 2.2, 0.7), (58, 150, 440, 2.6, 0.8), (74, -10, 160, 3.0, 0.8), (84, 210, 440, 3.4, 0.9),
                                (98, 40, 260, 3.6, 0.9), (104, 270, 440, 3.0, 0.9), (116, -10, 140, 2.6, 0.9), (118, 330, 440, 2.4, 0.9)]:
        xs = np.clip((G.X - x0) / (x1 - x0), 0, 1); env = np.sin(xs * math.pi) ** 0.6 * ((G.X > x0) & (G.X < x1))
        yy = y0 + 2.0 * np.sin(G.X / 37 + y0) + 1.5 * (nz - 0.5) * 4
        body = np.clip(1 - np.abs(G.Y - yy) / (th * env + 0.01), 0, 1) * env
        under = np.clip(1 - np.abs(G.Y - (yy + th * 0.8)) / (1.2 * env + 0.01), 0, 1) * env
        near = np.clip(1 - np.abs(G.X - ROOT[0]) / 220, 0, 1)
        G.fill(body, lerp(np.array((70, 40, 72)), np.array((120, 70, 90)), near[..., None] * 0.6 + (y0 / 140)), 0.85 * k)
        G.add(under, (200, 120, 90), 0.55 * k * (0.4 + 0.6 * near))


def root(G):
    """The Pale Root: a slender colossal trunk flaring into roots at the horizon, a vast bare crown fading into cloud."""
    rng = np.random.default_rng(12)
    cx, base = ROOT
    # trunk: tapered column, slight lean, buttress roots
    pts_l, pts_r = [], []
    for i in range(0, 101):
        t = i / 100; y = base - t * 78
        half = 6.0 - 3.2 * t ** 0.7 + 9 * (1 - t) ** 8
        lean = 3.0 * t ** 1.5
        pts_l.append((cx - half + lean, y)); pts_r.append((cx + half + lean, y))
    trunk = G.poly(pts_l + pts_r[::-1])
    side = np.clip((G.X - cx) / 11, -1, 1)
    fur = np.sin((G.X - cx) * 2.1 + G.noise(4, 40, 3, 2) * 6)
    img = lerp(np.array((128, 104, 122)), np.array((236, 218, 196)), np.clip(0.6 + 0.35 * side + 0.2 * fur, 0, 1)[..., None])
    G.fill_img(trunk, img)
    # buttress roots sprawling over the horizon
    segs = []
    for ang, ln, w in [(math.pi * 0.97, 34, 3.4), (math.pi * 0.88, 22, 2.6), (math.pi * 0.06, 30, 3.2), (math.pi * 0.14, 18, 2.4)]:
        segs += L.V.root_segs(rng, cx + (-7 if ang > 1.5 else 7), base - 4, ang, ln, w, 1, step=2.0, droop=0.05)
    G.fill(G.lines(segs), (214, 196, 186))
    # the crown: limbs climbing and spreading, thinning into twigs, fading into the high cloud
    import bgroll_a_lib as A
    crown = []
    for ang, ln, w in [(-math.pi / 2 - 1.05, 96, 3.2), (-math.pi / 2 - 0.55, 92, 3.0), (-math.pi / 2 - 0.15, 84, 3.0), (-math.pi / 2 + 0.2, 86, 3.0),
                       (-math.pi / 2 + 0.62, 96, 3.2), (-math.pi / 2 + 1.12, 90, 2.8)]:
        crown += A.tree_segs(rng, cx + 3.0, base - 76, ang, ln, w, 3, step=2.2, target=-math.pi / 2, trop=0.014, jitter=0.13,
                             spread=(0.35, 0.8), shrink=(0.5, 0.72), p_branch=0.09, min_w=0.6, taper=0.85)
    m = G.lines(crown)
    fade = np.clip((G.Y - 2) / 50, 0.25, 1)
    img = lerp(np.array((200, 186, 196)), np.array((250, 240, 214)), np.clip(0.5 + 0.25 * np.sin(G.X / 9), 0, 1)[..., None])
    G.fill_img(m * fade, img)
    # inner light: the trunk glows from its heart
    G.glow(cx + 2, base - 40, 10, 50, (40, 34, 20), 1.0, 1.2)


def far_land(G):
    rng = np.random.default_rng(7)
    # distant ranges left and right of the Root, in rose-violet haze
    for k, (base, amp, seed, col) in enumerate([(HOR - 4, 26, 3, (108, 62, 92)), (HOR - 1, 16, 4, (86, 50, 80))]):
        prof = L.profile(G.w, seed, base, amp, cells=((60, 1.0), (17, 0.5), (6, 0.2)))
        shape = np.clip(np.abs(np.arange(G.w + 1) - ROOT[0]) / 120, 0, 1) ** 0.8   # low near the Root, so it stands clear
        prof = HOR - (HOR - prof) * shape
        pts = [(x, prof[x]) for x in range(G.w + 1)] + [(G.w, HOR + 1), (0, HOR + 1)]
        G.fill(G.poly(pts), col)
    # the Hallow: spires and domes at the Root's foot, dark against the light
    city = []
    for i in range(34):
        x = ROOT[0] + rng.uniform(-78, 78)
        if abs(x - ROOT[0]) < 12: continue
        h = rng.uniform(4, 15) * (1.3 - abs(x - ROOT[0]) / 90); w = rng.uniform(2, 5)
        kind = rng.random()
        if kind < 0.45: city.append([(x - w / 2, HOR), (x - w / 2, HOR - h), (x, HOR - h - w * 1.8), (x + w / 2, HOR - h), (x + w / 2, HOR)])
        elif kind < 0.7: city.append([(x - w, HOR), (x - w, HOR - h * 0.6)] + [(x - w * math.cos(a), HOR - h * 0.6 - w * 0.9 * math.sin(a)) for a in np.linspace(0, math.pi, 8)] + [(x + w, HOR)])
        else: city.append([(x - w / 2, HOR), (x - w / 2, HOR - h), (x + w / 2, HOR - h), (x + w / 2, HOR)])
    m = np.zeros_like(G.X)
    for p in city: m = np.maximum(m, G.poly(p))
    G.fill(m, (78, 50, 74))
    for i in range(16):   # a few warm windows
        x = ROOT[0] + rng.uniform(-60, 60); y = HOR - rng.uniform(1, 9)
        G.fill(G.ellipse(x, y, 0.6, 0.6, 2) * m, (255, 196, 120), 0.9)
    # the valley: a sea of mist, lit under the Root, darkening toward the viewer, hill tops breaking through
    mist = G.vgrad([(HOR, (168, 110, 120)), (HOR + 14, (122, 78, 104)), (HOR + 50, (74, 46, 78)), (240, (38, 26, 50))])
    below = np.clip((G.Y - HOR) * 3, 0, 1)
    G.fill_img(below, mist)
    G.add(below * G.radial(ROOT[0], HOR + 6, 130, 34, 1.4), (90, 74, 50), 1.0)
    nz = G.noise(48, 5, 9, 3)
    G.add(below * np.clip(np.sin(G.Y / 2.6 + nz * 5) * 0.5 + 0.5, 0, 1) * np.clip(1 - (G.Y - HOR) / 70, 0, 1), (30, 20, 26), 0.6)
    for (hx, hy, rw, rh) in [(40, 172, 60, 16), (150, 160, 46, 9), (205, 150, 30, 5), (380, 168, 70, 14), (110, 196, 80, 18)]:
        hill = G.poly([(hx - rw, hy + rh)] + [(hx + rw * math.cos(a), hy + rh - rh * 1.6 * math.sin(a) ** 0.8) for a in np.linspace(math.pi, 0, 24)] + [(hx + rw, hy + rh)], blur=0.6)
        G.fill(hill * (G.Y < hy + rh * 0.5), (46, 30, 54))
        G.add(hill * np.clip(1 - (G.Y - (hy - rh * 0.4)) / 4, 0, 1) * (G.Y < hy + rh * 0.3), (110, 60, 60), 0.6)
    # the far wall winding over the hills toward the Hallow, with beacons
    wall = [(0, 188), (40, 160), (80, 168), (120, 156), (150, 151), (182, 146), (205, 142), (232, 139)]
    segs = [(a[0], a[1], b[0], b[1], 1.6) for a, b in zip(wall, wall[1:])]
    G.fill(G.lines(segs), (52, 34, 58))
    for (x, y) in wall[1:]:
        G.fill(G.poly([(x - 1.6, y), (x - 1.6, y - 5), (x + 1.6, y - 5), (x + 1.6, y)]), (52, 34, 58))
        G.fill(G.ellipse(x, y - 6, 1.0, 1.0, 2), (255, 170, 90))
        G.glow(x, y - 6, 6, 5, (90, 50, 20), 1.0, 2)


def guide_far():
    G = L.VG(FAR['w'], FAR['h'])
    sky(G); root(G); far_land(G)
    return G


def guide_mid():
    """Near crags with the wall and a beacon tower (left), a lower crag (right): over the far guide, so the render lights them in place."""
    G = guide_far(); G.a = np.zeros_like(G.X)
    rng = np.random.default_rng(4)
    # left crag
    prof = L.profile(G.w, 21, 0, 1, cells=((30, 1.0), (9, 0.4), (3, 0.15)))
    def crag(x0, x1, top, peak_x, bot=240):
        xs = np.arange(int(x0), int(x1) + 1)
        ys = [top + (bot - top) * (abs(x - peak_x) / max(1, (x1 - x0))) ** 1.3 * 1.8 + 6 * prof[int(x) % G.w] for x in xs]
        return [(x0, bot)] + list(zip(xs, ys)) + [(x1, bot)]
    def ridge(x0, x1, top_x, top_y, k, jag, seed, bot=241):
        pr = L.profile(G.w + 40, seed, 0, 1, cells=((11, 1.0), (4, 0.5), (2, 0.25)))
        xs = np.arange(x0, x1 + 1)
        ys = [top_y + k * (abs(x - top_x) / 40) ** 1.6 * 40 + jag * pr[int(x - x0)] - (6 if abs(x - top_x) < 3 else 0) for x in xs]
        return [(x0, bot)] + list(zip(xs, ys)) + [(x1, bot)]
    mL = G.poly(ridge(-4, 168, 58, 150, 0.55, 7, 21)); mR = G.poly(ridge(318, 436, 418, 172, 0.45, 6, 22))
    m = np.maximum(mL, mR)
    rock = lerp(np.array((30, 20, 40)), np.array((58, 36, 62)), np.clip(G.noise(6, 4, 8, 3), 0, 1)[..., None])
    G.fill_img(m, rock)
    # rim light from the Root side (right / up)
    up = np.roll(m, 3 * L.S, axis=0) < 0.5
    G.add(m * up, (150, 90, 80), 0.8)
    # the wall on the left crag, crenellated, and the watchtower with its fire
    wl = [(-4, 162), (30, 152), (64, 150), (96, 156), (128, 168)]
    for a, b in zip(wl, wl[1:]):
        G.fill(G.poly([(a[0], a[1] + 4), (a[0], a[1] - 6), (b[0], b[1] - 6), (b[0], b[1] + 4)]), (44, 28, 50))
        for x in np.arange(a[0], b[0], 5):
            y = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
            G.fill(G.poly([(x, y - 6), (x, y - 9), (x + 2.5, y - 9), (x + 2.5, y - 6)]), (44, 28, 50))
    tx, ty = 66, 150
    G.fill(G.poly([(tx - 7, ty), (tx - 5.5, ty - 38), (tx + 5.5, ty - 38), (tx + 7, ty)]), (40, 26, 48))
    G.fill(G.poly([(tx - 8, ty - 38), (tx - 8, ty - 43), (tx + 8, ty - 43), (tx + 8, ty - 38)]), (40, 26, 48))
    for x in (-8, -3, 2, 6.5):
        G.fill(G.poly([(tx + x, ty - 43), (tx + x, ty - 47), (tx + x + 2, ty - 47), (tx + x + 2, ty - 43)]), (40, 26, 48))
    G.add(G.poly([(tx + 2, ty), (tx + 5.5, ty - 38), (tx + 7, ty)]), (60, 34, 34), 1.0)
    G.fill(G.ellipse(tx, ty - 50, 2.2, 3.2, 2), (255, 190, 100)); G.glow(tx, ty - 50, 16, 14, (110, 60, 20), 1.0, 2)
    G.fill(G.poly([(tx - 2, ty - 26), (tx - 2, ty - 31), (tx + 2, ty - 31), (tx + 2, ty - 26)]), (255, 170, 90), 0.9)
    # mist curling over the crags' feet (kept out of the alpha)
    nz = G.noise(40, 4, 17, 3)
    G.fill(np.clip((G.Y - 200) / 30, 0, 1) * (0.5 + 0.5 * nz), (80, 52, 84), 0.5, cover=False)
    return G


def build(no_ase=False):
    os.makedirs(SRC, exist_ok=True)
    far_hi = np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float)
    far_hi = far_post(far_hi)
    s = V.box_down(far_hi, FAR['w'], FAR['h'])
    pal = L.kpal(s, 40)
    far = L.pixelize(far_hi, FAR['w'], FAR['h'], pal, dk=0.35)
    far = paint_trunk(far, pal + [(226, 212, 194), (240, 230, 210), (200, 180, 176)])
    mid_hi = np.asarray(Image.open(f'{SRC}/mid_render.png').convert('RGB'), float)
    mid_hi = V.grade(mid_hi, black=8, white=300, gamma=0.9, sat=0.9)
    al = np.asarray(Image.open(f'{SRC}/alpha_mid.png').convert('L').resize((MID['w'], MID['h']), Image.BOX), float) / 255 >= 0.5
    sm = V.box_down(mid_hi, MID['w'], MID['h'])
    mpal = L.kpal(sm, 16, mask=al)
    mid = L.pixelize(mid_hi, MID['w'], MID['h'], mpal, dk=0, alpha=al)
    mid = np.where(al[..., None], mid, 0)
    mid = mid_post(mid, al)
    far = far_patch(far)
    far_im, mid_im = L.to_rgba(far), L.to_rgba(mid, al)
    far_im.save(f'{SRC}/out_far.png'); mid_im.save(f'{SRC}/out_mid.png')
    L.comp_preview(ROOM, [(FAR, far_im), (MID, mid_im)], TINT, f'{SRC}/preview.png')
    print('far colours', len(pal), 'mid colours', len(mpal))
    if not no_ase:
        L.ase('vista_r11_far', [far_im]); L.ase('vista_r11_mid', [mid_im])


TRUNK_X = 301.5   # the render's trunk centre (1x)


def far_post(a):
    """Every seed rendered the trunk as a straight white beam with a vertical glow band around it. Remove the band (each row is
    re-filled by interpolating the sky between columns well clear of it) and lay a round halo in its place; the trunk itself is
    repainted at 1x (`paint_trunk`), as a tapered pale tree lit from within."""
    a = a.copy(); hh, ww = a.shape[:2]; S = L.S
    xl, xr = int((TRUNK_X - 22) * S), int((TRUNK_X + 22) * S)
    ys = np.arange(hh) / S
    t = np.clip((np.arange(xl, xr) - xl) / (xr - xl), 0, 1)
    interp = a[:, xl:xl + 1] * (1 - t)[None, :, None] + a[:, xr:xr + 1] * t[None, :, None]
    il, ir = int((TRUNK_X - 10) * S), int((TRUNK_X + 10) * S); t2 = np.clip((np.arange(xl, xr) - il) / (ir - il), 0, 1)
    low = a[:, il:il + 1] * (1 - t2)[None, :, None] + a[:, ir:ir + 1] * t2[None, :, None]
    interp = np.where((ys >= 116)[:, None, None], low, interp)
    dx = np.abs((np.arange(xl, xr) + 0.5) / S - TRUNK_X)
    bw = np.where(ys < 116, 22, 10)[:, None]                     # narrower over the city, so its spires stay
    wx = np.clip((bw - dx[None, :]) / 4, 0, 1)
    wy = np.clip((ys - 57) / 5, 0, 1) * np.clip((ROOT[1] + 1.5 - ys) * 2, 0, 1)
    w = (wy[:, None] * wx)[..., None]
    a[:, xl:xr] = a[:, xl:xr] * (1 - w) + interp * w
    X = (np.arange(ww)[None, :] + 0.5) / S; Y = (np.arange(hh)[:, None] + 0.5) / S
    d = np.sqrt(((X - TRUNK_X) / 46) ** 2 + ((Y - 112) / 64) ** 2)
    a = a + (np.clip(1 - d, 0, 1) ** 1.8)[..., None] * np.array([70, 58, 44])
    d2 = np.sqrt(((X - TRUNK_X) / 90) ** 2 + ((Y - ROOT[1]) / 14) ** 2)                      # the light pooling on the mist at its foot
    a = a + (np.clip(1 - d2, 0, 1) ** 1.5)[..., None] * np.array([50, 40, 30])
    return np.clip(a, 0, 255)


def far_patch(q):
    """A thin dark post on the right hill (x 324..334, y 168..186) read as a standing figure: refilled from the hill row by row."""
    q = q.copy(); x0, y0, x1, y1 = 323, 166, 336, 188
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = (x - x0) / (x1 - x0); q[y, x] = q[y, x0 - 1] if t < 0.5 else q[y, x1]
    return q


def mid_post(q, al):
    """The watchtower's lit window rendered as a round red blob (an eye) and its fire as a brown dot: the window becomes a dark
    stone face with a narrow amber slit, the fire a small flame; the crags get a 1 px rose rim on the edges facing the Root."""
    q = q.copy(); h, w = al.shape
    stone = np.array((40, 26, 48), float)
    for y in range(96, 130):
        for x in range(58, 76):
            if al[y, x] and (q[y, x, 0] - q[y, x, 2]) > 20: q[y, x] = stone
    for y in range(117, 122): q[y, 66] = (236, 168, 96)
    q[121, 66] = (176, 104, 70)
    for (x, y, c) in [(66, 97, (255, 226, 150)), (66, 98, (255, 200, 110)), (65, 99, (232, 128, 64)), (66, 99, (255, 200, 110)), (67, 99, (232, 128, 64)), (66, 96, (232, 128, 64))]:
        q[y, x] = c
    rim = al & ~np.roll(al, -1, axis=1) | al & ~np.roll(al, 1, axis=0)
    rim[:, -1] = False; rim[0, :] = False
    q[rim & (np.arange(h)[:, None] > 104)] = (112, 66, 84)
    return q


def paint_trunk(q, pal):
    """The Pale Root's trunk at 1x: a tapered column flaring into buttress roots, brightest at its heart."""
    P = np.array(pal, float)
    near = lambda c: P[np.argmin(((P - np.array(c, float)) ** 2).sum(1))]
    tones = [near(c) for c in [(118, 92, 118), (160, 132, 146), (200, 180, 176), (226, 212, 194), (240, 230, 210)]]
    q = q.copy(); top, base = 53, ROOT[1]
    for y in range(top, base + 1):
        t = (base - y) / (base - top)
        half = 3.6 + 1.6 * (1 - t) + 9 * (1 - t) ** 12; cx = TRUNK_X + 1.2 * t
        for x in range(int(cx - half - 1), int(cx + half + 2)):
            u = (x + 0.5 - cx) / half
            if abs(u) > 1: continue
            fur = math.sin(x * 2.3 + math.sin(y / 6.0) * 1.6) > 0.72 and abs(u) < 0.8
            k = 4 if abs(u + 0.05) < 0.28 else 3 if abs(u) < 0.62 else 2 if u > 0 or abs(u) < 0.85 else 1
            if u < -0.82: k = 0 if t > 0.1 else 1
            if fur: k = max(1, k - 1)
            if y > base - 3 and abs(u) > 0.7: k = min(k, 1)
            q[y, x] = tones[k]
    # buttress roots creeping over the horizon
    for sgn, ln in ((-1, 16), (1, 13), (-1, 9), (1, 8)):
        for i in range(ln):
            x = int(TRUNK_X + sgn * (9 + i * 1.3)); y = base - 1 + (i > ln * 0.5)
            q[y, x] = tones[1 if i < ln * 0.6 else 0]
    return q


if __name__ == '__main__':
    args = sys.argv[1:]
    os.makedirs(SRC, exist_ok=True)
    if '--guide' in args or '--sweep' in args or '--render' in args:
        guide_far().save(SRC, 'far'); guide_mid().save(SRC, 'mid')
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
