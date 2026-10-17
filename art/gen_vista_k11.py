#!/usr/bin/env python3
"""K11 The Rose Window vista (agent V1, docs/v17/vista_v1.md): the great rose window at dawn, the Root's branches behind the glass.

  python3 art/gen_vista_k11.py [--guide | --sweep far 1,2,3 [--dn x --cn x --pix x --tag t] | --render] [--no-ase]
  (vista_v1_lib.cli; builds assets/vista_k11_far from the saved render in art/bg_src/vista_k11/)

Lore (ra_10): "They raised the nave around the trunk and set the great window toward the dawn, so that the light would pass
through the Root before it reached them." The regular cathedral backdrop is the flooded nave at night in cold moonlight; this is
the upper nave at dawn: the east wall in shadow, ribbed vaults, a row of clerestory lancets, and the great rose window lit from
behind, its tracery holding muted jewel glass with the dark lace of the Root's branches pressed against it. The room's old
rose prop (xra_rose, 50_ra.js) is hidden while this painting is loaded (85v_v1.js keeps its lights and draws the shafts from the
painted window instead).
"""
import os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vista_v1_lib as L
import bgv2lib as V
from bgv2lib import lerp

ROOM = 'K11'
SRC = os.path.join(HERE, 'bg_src', 'vista_k11')
TINT = '#0e0c14'
FAR = dict(sheet='vista_k11_far', w=416, h=232, fac=0.08, vfac=0.15, x=-4, dy=16)
ROSE = (296, 84, 64)     # centre x, y, radius (painting px)

PROMPTS = {
    'far': ('pixel art, dark fantasy, interior of a vast gothic cathedral at dawn, a colossal round rose window with intricate stone '
            'tracery and glowing stained glass in muted deep blue, wine red and amber, the dark silhouette of great tree branches '
            'behind the glass, warm golden dawn light streaming through in long diagonal shafts with floating dust, ribbed stone '
            'vaults and clustered pillars in deep violet shadow, a row of tall narrow lancet windows below, solemn and sacred, '
            'highly detailed, muted violet grey stone with rose gold light'),
}
RENDER = {'far': dict(seed=3, dn=0.74, cn=0.42, cn_end=0.7, pix=0.45, tag='b')}


def rose(G):
    cx, cy, R = ROSE
    d = np.sqrt((G.X - cx) ** 2 + (G.Y - cy) ** 2); ang = np.arctan2(G.Y - cy, G.X - cx)
    # moulded frame rings
    G.fill(np.clip((R + 6 - d) * 3, 0, 1) * np.clip((d - R) * 3 + 1, 0, 1), (84, 76, 96))
    G.fill(np.clip((R + 3 - d) * 3, 0, 1) * np.clip((d - R + 1) * 3, 0, 1), (120, 110, 128))
    inside = np.clip((R - d) * 3, 0, 1)
    # glass: muted jewel tones by sector and ring, brightest at the centre and toward the dawn (lower left)
    n = 12; sec = ((ang + math.pi) / (2 * math.pi) * n) % n; si = np.floor(sec).astype(int)
    rr = d / R
    cols = np.array([(60, 76, 128), (112, 54, 70), (150, 116, 70), (66, 88, 134), (104, 60, 86), (72, 98, 116)], float)
    ring = np.where(rr < 0.3, 2, np.where(rr < 0.62, (si + 1) % 6, si % 6))
    cell = G.noise(3, 3, 17, 1)                                              # leaded glass: small pieces of slightly different tone
    glass = cols[ring] * (0.8 + 0.4 * cell)[..., None]
    lead = np.clip(1 - np.abs(np.sin(G.X * 1.3) * np.sin(G.Y * 1.1)) * 6, 0, 1) * 0
    glow = np.clip(1.25 - rr * 0.7, 0, 1.3)[..., None] * (1 + 0.25 * np.clip(-(G.X - cx) / R - (G.Y - cy) / R, -1, 1))[..., None]
    G.fill_img(inside, np.clip(glass * glow + 30, 0, 255))
    # tracery: 12 spokes, a ring of 12 petal arcs, an inner ring of 6 trefoil circles, the oculus
    stone = (70, 62, 80); m = np.zeros_like(G.X)
    for k in range(n):
        a = k / n * 2 * math.pi
        m = np.maximum(m, G.lines([(cx + math.cos(a) * R * 0.3, cy + math.sin(a) * R * 0.3, cx + math.cos(a) * R, cy + math.sin(a) * R, 2.6)]))
        pa = (k + 0.5) / n * 2 * math.pi
        px, py = cx + math.cos(pa) * R * 0.8, cy + math.sin(pa) * R * 0.8
        dd = np.sqrt((G.X - px) ** 2 + (G.Y - py) ** 2); m = np.maximum(m, np.clip(1 - np.abs(dd - R * 0.17) / 1.2, 0, 1))
    for k in range(6):
        a = k / 6 * 2 * math.pi + math.pi / 6; px, py = cx + math.cos(a) * R * 0.46, cy + math.sin(a) * R * 0.46
        dd = np.sqrt((G.X - px) ** 2 + (G.Y - py) ** 2); m = np.maximum(m, np.clip(1 - np.abs(dd - R * 0.15) / 1.2, 0, 1))
    for r0 in (0.3, 0.62):
        m = np.maximum(m, np.clip(1 - np.abs(d - R * r0) / 1.4, 0, 1))
    G.fill(m * inside, (96, 86, 104))
    G.fill(G.ellipse(cx, cy, R * 0.12, R * 0.12), (250, 214, 140))
    # the Root's branches pressed against the glass from behind (dark lace, strongest low and right)
    import bgroll_a_lib as A
    rng = np.random.default_rng(3)
    segs = A.tree_segs(rng, cx + R * 0.35, cy + R * 1.05, -math.pi / 2 - 0.25, R * 1.5, 4.2, 4, step=2.0, target=-math.pi / 2 - 0.5, trop=0.01,
                       jitter=0.16, spread=(0.4, 0.9), p_branch=0.1, min_w=0.6)
    G.fill(G.lines(segs) * inside, (36, 26, 40), 0.85)


def guide_far():
    G = L.VG(FAR['w'], FAR['h'])
    G.rgb = G.vgrad([(0, (16, 14, 24)), (120, (30, 26, 40)), (232, (22, 20, 30))])
    cx, cy, R = ROSE
    # the east wall around the window: ashlar courses in shadow, lit warm near the glass
    nz = G.noise(8, 4, 2, 2)
    course = (np.sin(G.Y * math.pi / 4) > 0.86).astype(float)
    G.add(course, (-6, -6, -6), 1.0); G.add(nz - 0.5, (14, 12, 16), 1.0)
    # the great arch framing the window (a pointed head), clustered shafts either side
    for off, col in [(0, (40, 34, 52)), (-6, (52, 46, 64))]:
        hw = R + 22 + off
        pts = [(cx - hw, 232), (cx - hw, cy)]
        for i in range(25):
            t = i / 24; a = t * math.pi / 2.6
            pts.append((cx - hw + hw * (1 - math.cos(a)) * 1.05, cy - (hw * 1.25) * math.sin(a)))
        pts += [(cx, cy - hw * 1.32)] + [(2 * cx - x, y) for x, y in reversed(pts[2:])] + [(cx + hw, 232)]
        G.fill(G.poly(pts), col)
    for sx in (cx - R - 30, cx - R - 22, cx + R + 22, cx + R + 30):
        G.fill(G.poly([(sx - 2.5, 232), (sx - 2.5, 0), (sx + 2.5, 0), (sx + 2.5, 232)]), (58, 50, 70))
        G.add(G.poly([(sx - 2.5, 232), (sx - 2.5, 0), (sx - 1, 0), (sx - 1, 232)]), (30, 22, 16), 1.0)
    rose(G)
    # the clerestory lancets under the rose, lit dimmer
    for k in range(5):
        lx = cx - 48 + k * 24
        pts = [(lx - 6, 216), (lx - 6, 176), (lx - 3.5, 168), (lx, 163), (lx + 3.5, 168), (lx + 6, 176), (lx + 6, 216)]
        G.fill(G.poly(pts), (44, 38, 54))
        G.fill(G.poly([(lx - 2.2, 214), (lx - 2.2, 177), (lx, 171), (lx + 2.2, 177), (lx + 2.2, 214)]), (112, 84, 82))
        G.fill(G.poly([(lx - 0.4, 214), (lx - 0.4, 174), (lx + 0.4, 174), (lx + 0.4, 214)]), (44, 38, 54))
    G.fill(G.poly([(cx - 66, 216), (cx + 66, 216), (cx + 70, 222), (cx - 70, 222)]), (70, 62, 80))
    # the nave receding to the left: piers, arcade arches, vault ribs, a far lancet with dawn in it
    for k, px in enumerate([30, 92, 150, 196]):
        w = 9 - k * 1.2
        G.fill(G.poly([(px - w, 232), (px - w, 40 + k * 8), (px + w, 40 + k * 8), (px + w, 232)]), (34 - k * 2, 30 - k * 2, 44 - k * 2))
        G.add(G.poly([(px + w * 0.3, 232), (px + w * 0.3, 40 + k * 8), (px + w, 40 + k * 8), (px + w, 232)]), (24, 16, 14), 1.0)
    for a, b in [(30, 92), (92, 150), (150, 196)]:
        m = (a + b) / 2; h = (b - a) * 0.75
        arc = [(a + (b - a) * t, 120 - math.sin(t * math.pi) * h) for t in np.linspace(0, 1, 30)]
        G.fill(G.lines([(p[0], p[1], q[0], q[1], 2.2) for p, q in zip(arc, arc[1:])]), (44, 38, 56))
    G.fill(G.poly([(58, 112), (58, 66), (61, 58), (64, 54), (67, 58), (70, 66), (70, 112)]), (200, 150, 110))
    for i in range(5):   # the vault's pointed web over the nave bays
        x0 = 8 + i * 46
        arc = [(x0 + 46 * t, 34 - math.sin(t * math.pi) ** 0.8 * 30) for t in np.linspace(0, 1, 24)]
        G.fill(G.lines([(p[0], p[1], q[0], q[1], 1.8) for p, q in zip(arc, arc[1:])]), (50, 44, 62))
    # dawn shafts from the rose, falling down-left, and the far lancet's shaft
    for k, (dx, w) in enumerate([(-30, 14), (-6, 18), (20, 14)]):
        sh = G.poly([(cx + dx - w / 2, cy + 20), (cx + dx + w / 2, cy + 20), (cx + dx + w / 2 - 150, 232), (cx + dx - w / 2 - 170, 232)], blur=4)
        G.add(sh, (60, 40, 30), 0.55)
    G.add(G.poly([(58, 112), (70, 112), (40, 232), (10, 232)], blur=4), (50, 34, 26), 0.6)
    G.glow(cx, cy, R * 1.8, R * 1.6, (40, 26, 20), 1.0, 1.6)
    return G


def guides():
    return {'far': guide_far()}


# the picked seed painted a small robed figure under the lancets (hi-res boxes in PATCH): it reads as an enemy,
# so the box is refilled row by row from the wall on either side (as the dunes far layer's PATCH)
PATCH = [(899, 612, 941, 696), (878, 654, 946, 696)]


def patch(a):
    a = a.copy()
    for x0, y0, x1, y1 in PATCH:
        t = np.linspace(0, 1, x1 - x0)[None, :, None]
        a[y0:y1, x0:x1] = a[y0:y1, x0 - 1:x0] * (1 - t) + a[y0:y1, x1:x1 + 1] * t
    return a


def build(no_ase=False):
    far_hi = patch(np.asarray(Image.open(f'{SRC}/far_render.png').convert('RGB'), float))
    far_hi = V.grade(far_hi, black=2, white=200, gamma=1.15, sat=1.0)
    pal = L.kpal(V.box_down(far_hi, FAR['w'], FAR['h']), 48)
    far = L.pixelize(far_hi, FAR['w'], FAR['h'], pal, dk=0.3)
    far_im = L.to_rgba(far); far_im.save(f'{SRC}/out_far.png')
    L.comp_preview(ROOM, [(FAR, far_im)], TINT, f'{SRC}/preview.png')
    print('far colours', len(pal))
    if not no_ase:
        L.ase('vista_k11_far', [far_im])


if __name__ == '__main__':
    L.cli(sys.modules[__name__])
