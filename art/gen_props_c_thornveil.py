#!/usr/bin/env python3
"""Props batch C, Thornveil (docs/v17/props_c.md). Rebuilds, with the v1 contract (frame size, tags, frames, durations, anchors):

  tv_fern    32x20  idle          a fern: a crown of arching fronds with real pinnae, one fiddlehead
  tv_shroom  24x20  idle          a cluster of slender glowing mycena (code light at y-10 stays under the caps)
  tv_vine    16x64  loop 4f       a hanging liana with leaves (pivot top-centre); the 4 frames are a sway derived from frame 0
  xsa_tv     48x48  fungus 4f, mossrock, mossbank, stones, stone_l, stone_s, nest, herbs, snare 2f, shelves, cauldron 3f, hide
                    (rootcurtain, skullpost, antlers, thornbed keep their v1 pixels)
  xsa_tvbig  96x128 rootarch      a root arch of twisted bark (art/treelib.py, the tv_tree bark and moss)

Palettes: the trees pass ramps (art/gen_trees.py TV_BARK / TV_MOSS / TV_RIM / TV_FUNG / TV_IVY) plus a few prop ramps sampled from
tiles_thornveil and bg_thornveil_mid. Light from the upper left, the forest's cold-green ambient, bioluminescence where the
code adds a light.

  python3 art/gen_props_c_thornveil.py [fern shroom vine tv tvbig ...] [--no-ase] [--render]
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import props_c_lib as P
from props_c_lib import Pc, ramp, selout, to_img, T

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
NO_ASE = '--no-ase' in sys.argv
RENDER = '--render' in sys.argv

# ----------------------------------------------------------------------------------------------- palettes
TV_BARK = ramp('#0a0b0a', '#0f110f', '#151814', '#1c201a', '#242a21', '#2e3529', '#394133', '#475040', '#58614e', '#6c7660')
TV_MOSS = ramp('#0b1712', '#0f2119', '#152d1f', '#1c3a26', '#24492d', '#2f5935', '#3d6b3f', '#4a7745')
TV_RIM = ramp('#4e6058', '#6b8078', '#93a89c')
TV_FUNG = ramp('#1e1a15', '#332c22', '#4e4535', '#6d6249', '#8e8262', '#ada17c')
FERN = ramp('#08130d', '#0c1c13', '#11271a', '#173321', '#1f4128', '#294f2e', '#355e35', '#456f3c', '#5a8246', '#759856')
FERNB = ramp('#070f0c', '#0a1712', '#0f2018', '#152a1e', '#1b3524', '#22402a')
CAP = ramp('#141d1c', '#1d2a28', '#273a36', '#344c45', '#436256', '#557a68', '#6c957e', '#8cb79a', '#b4dcbd', '#ddf8e2')
GILL = ramp('#1a3e30', '#256449', '#338f63', '#4fbf85', '#8be8b1', '#d4fde4')
STEM = ramp('#151c18', '#1f2822', '#2c3730', '#3c4940', '#526153', '#6d7d6b', '#8fa08b')
SOIL = ramp('#0b0d0b', '#121612', '#1a1f18', '#242a20', '#2f3628')
STONE = ramp('#0d0f0f', '#151817', '#1d2120', '#262b29', '#323835', '#414843', '#535a53', '#6a7268', '#858d80')
OUT = (7, 10, 9)


def save_prev(name, imgs, **kw):
    kw.setdefault("scale", 6 if max(i.height for i in imgs) <= 64 else 3); P.preview(name, imgs, bg=(22, 34, 28), **kw)


# =============================================================================================== tv_fern
def fern_model(seed=4):
    w, h = 32, 20
    c = Pc(w, h); rng = np.random.default_rng(seed)
    cx, cy = 16.0, 19.4
    # (angle from vertical in degrees, -left; length; depth 0 back .. 2 front; droop)
    fronds = [(-30, 19.0, 0, 1.1), (28, 18.5, 0, 1.1), (-6, 17.0, 0, 0.9), (10, 16.0, 0, 0.95),
              (-50, 17.0, 1, 1.0), (50, 16.5, 1, 1.0), (-18, 18.0, 1, 1.05), (16, 17.5, 1, 1.05),
              (-40, 12.0, 2, 0.9), (38, 11.5, 2, 0.9), (-2, 10.5, 2, 0.6)]
    for (a0, L, dep, droop) in fronds:
        mat = 'fernb' if dep == 0 else 'fern'
        a0r = math.radians(a0) + rng.normal(0, 0.04); side = 1 if a0 >= 0 else -1
        # spine: direction leaves the crown upward, gravity bends it out and down
        pts = [(cx + side * 0.4, cy)]; x, y = cx + side * 0.4, cy; n = 24
        for i in range(1, n + 1):
            t = i / n
            ang = a0r + side * droop * 1.25 * t ** 1.4
            x += math.sin(ang) * L / n; y -= math.cos(ang) * L / n
            pts.append((x, y))
        pts = np.array(pts)
        base_v = (0.32, 0.5, 0.62)[dep]
        ms, U, TT, AX, AY = c.stroke(pts[::3].tolist() + [tuple(pts[-1])], 0.42, 0.16)
        c.put(ms, mat, base_v - 0.12 + 0.1 * TT)
        # pinnae: alternating, longest a third of the way out, angled forward and drooping
        seg = np.hypot(*np.diff(pts, axis=0).T); d = np.r_[0, np.cumsum(seg)]; Ltot = d[-1]
        sp = 1.0; k = 0
        s = 1.8
        while s < Ltot - 0.4:
            t = s / Ltot
            px = np.interp(s, d, pts[:, 0]); py = np.interp(s, d, pts[:, 1])
            j = min(len(pts) - 2, int(np.searchsorted(d, s)))
            tx, ty = pts[j + 1] - pts[j]; tn = math.hypot(tx, ty); tx, ty = tx / tn, ty / tn
            for sd in (-1, 1):
                if (k + (sd > 0)) % 2: continue
                pl = 3.4 * (L / 15) * math.sin(math.pi * min(1.0, (t + 0.08) / 1.02)) ** 0.7 * (1 - 0.5 * t)
                if pl < 0.6: continue
                ang = math.atan2(ty, tx) + sd * math.radians(58 - 18 * t)
                dx, dy = math.cos(ang), math.sin(ang)
                dy += 0.25                          # gravity
                dn = math.hypot(dx, dy); dx, dy = dx / dn, dy / dn
                off = sp * 0.5 * (sd > 0)
                bx = px + tx * off; by = py + ty * off
                q = [(bx, by), (bx + dx * pl * 0.55, by + dy * pl * 0.55 + 0.15), (bx + dx * pl, by + dy * pl + 0.45)]
                mp, Up, Tp, _, _ = c.stroke(q, 0.42, 0.1)
                face = -(dx * -0.6 + dy * -0.8)         # pinnae pointing up/left catch the light
                v = base_v + 0.16 * (-face) + 0.12 * t + 0.1 * Tp - 0.08 * (Up * sd > 0.3)
                c.put(mp, mat, np.asarray(v, float) if np.ndim(v) else np.full(mp.shape, v))
            k += 1; s += sp
    # a fiddlehead uncurling at the front of the crown
    sp_pts = [(cx + 1.2, cy)] + [(cx + 1.6 + 2.2 * (1 - i / 14) * math.cos(i * 0.62) * 0.9, cy - 7.5 + 2.2 * (1 - i / 14) * math.sin(i * 0.62))
                                 for i in range(15)]
    sp_pts = [(cx + 1.2, cy), (cx + 1.6, cy - 3.5), (cx + 2.0, cy - 6)] + sp_pts[4:]
    ms, U, TT, AX, AY = c.stroke(sp_pts, 0.5, 0.35)
    c.put(ms, 'fern', 0.62 + 0.25 * TT)
    # the crown: a dark tuft of old stalks and soil
    c.put(c.ell(cx, cy + 0.6, 4.2, 1.6), 'soil', 0.4)
    return c


def fern(seed=4):
    """Drawn straight at 1x: at this size a frond reads as a 1 px arching rachis with 1-2 px pinnae ticks on alternate sides,
    light on the upper side and towards the young tips, the back fronds sunk into the forest's shadow."""
    w, h = 32, 20
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w, 4)); z = np.full((h, w), -1.0)
    def px(x, y, ci, R, zz):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < w and 0 <= y < h and zz >= z[y, x]:
            out[y, x, :3] = R[int(np.clip(ci, 0, len(R) - 1))]; out[y, x, 3] = 255; z[y, x] = zz
    cx, cy = 15.5, 19.0
    # (angle from vertical, deg; length; depth 0 back .. 2 front; droop rad)
    fronds = [(-30, 19.0, 0, 1.0), (26, 18.5, 0, 1.0), (-2, 16.5, 0, 0.7),
              (-56, 15.5, 1, 0.95), (54, 16.0, 1, 0.95), (-14, 18.5, 1, 1.05), (12, 18.0, 1, 1.05),
              (-38, 12.0, 2, 0.9), (40, 11.5, 2, 0.9), (6, 10.5, 2, 0.7)]
    for fi, (a0, L, dep, droop) in enumerate(fronds):
        R = FERNB if dep == 0 else FERN
        base = (2.0, 4.0, 5.2)[dep]
        side = 1 if a0 >= 0 else -1
        a0r = math.radians(a0) + rng.normal(0, 0.03)
        pts = []; x, y = cx + side * 0.6, cy; n = int(L * 4)
        for i in range(n + 1):
            t = i / n
            pts.append((x, y, t))
            ang = a0r + side * droop * t ** 1.5
            x += math.sin(ang) * L / n; y -= math.cos(ang) * L / n
        # unique rachis pixels
        seen = []; 
        for (x, y, t) in pts:
            q = (int(round(x)), int(round(y)))
            if not seen or seen[-1][0] != q: seen.append((q, t, x, y))
        zz = dep * 10 + fi * 0.01
        for k, ((qx, qy), t, x, y) in enumerate(seen):
            # tangent
            j = min(len(seen) - 1, k + 2); i0 = max(0, k - 2)
            tx = seen[j][2] - seen[i0][2]; ty = seen[j][3] - seen[i0][3]; tn = math.hypot(tx, ty) or 1; tx, ty = tx / tn, ty / tn
            # pinnae on alternate sides every pixel step, longest a third of the way out
            if 0.1 < t < 0.97:
                sd = 1 if k % 2 else -1
                pl = (2.6 if dep else 2.2) * (L / 16) * math.sin(math.pi * min(1.0, (t + 0.05))) ** 0.8 * (1.1 - 0.6 * t)
                ang = math.atan2(ty, tx) + sd * math.radians(62)
                dx, dy = math.cos(ang), math.sin(ang) + 0.35
                dn = math.hypot(dx, dy); dx, dy = dx / dn, dy / dn
                upper = dy < 0.1                       # pinnae on the upper side face the light
                for st in range(1, int(round(pl)) + 1):
                    ci = base + (1.2 if upper else -0.6) + 1.6 * t - 0.5 * (st - 1)
                    px(qx + dx * st, qy + dy * st, ci, R, zz - 0.001)
            ci = base + 0.8 + 1.8 * t
            px(qx, qy, ci, R, zz)
    # a fiddlehead uncurling at the front of the crown
    for (x, y, ci) in [(16, 18, 5), (16, 17, 6), (17, 16, 6), (17, 15, 7), (17, 14, 7), (18, 13, 8), (19, 13, 8), (19, 14, 7), (18, 14, 6)]:
        px(x, y, ci, FERN, 40)
    # the crown: old stalks and soil
    for x in range(12, 20):
        px(x, 19, 1 + (x % 2), SOIL, 41)
    for x in range(13, 19, 2):
        px(x, 18, 2, FERN, 39)
    return to_img(out)


# =============================================================================================== tv_shroom
def mushroom(c, base, top, rx, ry, glow=1.0, lean=0.0, stem_r=(0.9, 0.6), umbo=0.25):
    bx, by = base; tx, ty = top
    mid = ((bx + tx) / 2 + lean, (by + ty) / 2)
    ms, U, TT, AX, AY = c.stroke([(bx, by), mid, (tx, ty + ry * 0.3)], stem_r[0], stem_r[1])
    v = c.cyl(U, AX, AY, amb=0.3, key=0.5) + 0.3 * TT ** 2 * glow       # the gills light the stem's top
    c.put(ms, 'stem', v)
    # the cap: a bell, seen a hair from below so the glowing gills show as a band under the rim
    pts = []
    for i in range(33):
        a = math.pi * i / 32
        u = math.cos(a)
        k = (1 - abs(u) ** 1.5) ** 0.85                       # a bell: steep sides, a rounded crown
        pts.append((tx + rx * u, ty - ry * k - umbo * ry * max(0.0, 1 - abs(u) * 3)))
    pts += [(tx - rx * 0.96, ty + ry * 0.18), (tx, ty + ry * 0.32), (tx + rx * 0.96, ty + ry * 0.18)]
    pts = [(tx + rx, ty)] + pts[1:]
    m = c.poly(pts)
    gill = c.ell(tx, ty + ry * 0.12, rx * 0.8, max(0.55, ry * 0.22)) & ~c.poly(pts[:33])
    lit = c.dome(m, sigma=max(0.8, ry * 0.4), amb=0.32, key=0.55)
    below = np.clip((c.Y - (ty - ry * 0.45)) / (ry * 0.75), 0, 1)       # translucent: the glow shows through the lower cap
    c.put(m, 'cap', lit + 0.6 * below ** 1.1 * glow)
    gv = 0.55 + 0.45 * (1 - np.clip(np.abs(c.X - tx) / (rx * 0.9), 0, 1)) * glow
    c.put(gill, 'gill', gv)
    return m


def shroom_model():
    w, h = 24, 20
    c = Pc(w, h)
    c.put(c.ell(12.5, 19.6, 8.5, 2.0), 'soil', 0.35)
    c.put(c.ell(9, 19.2, 3.5, 1.3), 'moss', 0.55)
    mushroom(c, (6.2, 19.6), (4.6, 13.4), 2.7, 2.0, glow=0.8, lean=-0.6, stem_r=(0.6, 0.45))
    mushroom(c, (16.6, 19.6), (18.4, 10.2), 3.9, 2.7, glow=0.95, lean=0.9, stem_r=(0.75, 0.55))
    mushroom(c, (11.4, 19.6), (10.6, 4.8), 5.4, 3.6, glow=1.0, lean=-0.9, stem_r=(0.95, 0.65))
    mushroom(c, (21.6, 19.6), (21.9, 17.0), 1.7, 1.3, glow=0.7, stem_r=(0.45, 0.4))
    return c


def shroom():
    c = shroom_model()
    s = c.resolve(0.45)
    R = {'cap': CAP, 'gill': GILL, 'stem': STEM, 'soil': SOIL, 'moss': TV_MOSS}
    s.index(R, dk=0.25).rim(R, mats={'cap'}, wts=(1.0, 0.5, 0.0, 0.0), steps=1)
    out = s.rgba(R)
    # a few glowing spores in the air above the caps
    for (x, y) in [(16, 4), (5, 8)]:
        out[y, x] = (*P.C('#bff7d4'), 200)
    out = selout(out, OUT, lit_k=0.3, near=s.m('cap') | s.m('gill') | s.m('soil'))
    return to_img(out)


# =============================================================================================== tv_vine
IVY = ramp('#0a160f', '#10221a', '#173020', '#1f3f27', '#2a4f2e', '#386136', '#4b743f', '#62894b')


def vine_frame0():
    """A liana hanging from its top-centre pivot: a woody twisted stem, a thinner strand winding round it, ivy leaves in pairs
    that thin out towards the tip, a frayed root-tip at the bottom."""
    w, h = 16, 64
    c = Pc(w, h)
    nz = T.Noise(31)
    cx = lambda y: 8.0 + 1.3 * math.sin(y * 0.105 + 0.6) + 0.5 * math.sin(y * 0.31)
    ys = np.arange(-1, 59, 1.0)
    ms, U, TT, AX, AY = c.stroke([(cx(y), y) for y in ys[::4]], 1.25, 0.55)
    v = c.cyl(U, AX, AY, amb=0.14, key=0.7) + 0.12 * (nz(c.X * 9, c.Y * 3) - 0.5)
    v -= 0.22 * (np.sin(c.Y * 1.35 + U * 2.2) > 0.6)            # the twist of the woody stem
    c.put(ms, 'bark', v)
    # the second, thinner strand wrapping round: in front where cos > 0
    for k in range(2):
        pts = [(cx(y) + 1.6 * math.sin(y * 0.42 + k * 3.1), y) for y in np.arange(2 + k * 6, 52 - k * 10, 1.5)]
        m2, U2, T2, A2x, A2y = c.stroke(pts, 0.45, 0.3)
        front = np.cos(c.Y * 0.42 + k * 3.1) > 0
        c.put(m2 & (front | ~ms), 'bark', c.cyl(U2, A2x, A2y, amb=0.25, key=0.7))
    # a frayed tip of rootlets
    for dx, L in ((-1.4, 4.0), (0.3, 5.5), (1.6, 3.5)):
        y0 = 57.0; x0 = cx(y0)
        m3, U3, _, a3x, a3y = c.stroke([(x0, y0), (x0 + dx * 0.6, y0 + L * 0.6), (x0 + dx, y0 + L)], 0.45, 0.2)
        c.put(m3, 'bark', c.cyl(U3, a3x, a3y, amb=0.2, key=0.6))
    # leaves: heart-ish, on short petioles, alternating sides, smaller towards the tip
    rng = np.random.default_rng(5)
    y = 3.0; k = 0
    while y < 52:
        side = 1 if k % 2 else -1
        size = 2.3 - 1.2 * (y / 52) + rng.uniform(-0.2, 0.2)
        x0 = cx(y); lx = x0 + side * (1.6 + size * 0.9); ly = y + size * 0.6
        ang = side * 0.5 + rng.normal(0, 0.15)
        m = c.ell(lx, ly, size * 1.05, size * 0.72, rot=ang) | c.poly([(lx - side * size * 0.9, ly - size * 0.2), (lx + side * size * 1.6, ly + size * 0.65),
                                                                   (lx + side * size * 0.2, ly + size * 0.7)])
        nx, ny, nzv = c.normals(m, sigma=0.6)
        L = P.unit(P.LIGHT); d = np.clip(nx * L[0] + ny * L[1] + nzv * L[2], 0, 1)
        vv = 0.18 + 0.62 * d + 0.12 * (1 - y / 52)
        vv -= 0.18 * (np.abs((c.X - lx) * math.cos(ang) + (c.Y - ly) * math.sin(ang) - 0) < 0.25)   # the midrib
        c.put(m, 'leaf', vv)
        y += 3.3 + rng.uniform(-0.5, 0.8); k += 1
    return c


def vine():
    c = vine_frame0()
    s = c.resolve(0.45)
    R = {'bark': TV_BARK, 'leaf': IVY}
    s.index(R, dk=0.25).rim(R, wts=(0.6, 1.0, 0.0, 0.0), steps=1, minv=0.3)
    base = selout(s.rgba(R), OUT, lit_k=0.3)
    # the sway: rows shift sideways, more towards the tip (frames: rest, right, rest, left; the pivot row never moves)
    frames = []
    for ph in (0.0, 1.0, 0.0, -1.0):
        out = np.zeros_like(base)
        for y in range(base.shape[0]):
            dx = int(round(ph * 1.8 * (y / 63) ** 1.6 + (0.5 if ph == 0 and y > 40 and False else 0)))
            out[y] = np.roll(base[y], dx, axis=0)
            if dx > 0: out[y, :dx] = 0
            elif dx < 0: out[y, dx:] = 0
        frames.append(to_img(out))
    return frames


# =============================================================================================== xsa_tv/fungus
def stump(c, cx, base, rw, top, seed, jag=None):
    """A rotten stump (treelib bark) with a broken jagged top and a soft, rotted heart."""
    Wd = T.Wood(c.w, c.h); nz = T.Noise(seed)
    Wd.branch([(cx, base + 4), (cx + 0.5, (base + top) / 2), (cx + 1, top - 6)], rw, rw * 0.9, wob=0.6, seed=seed,
              rprof=lambda t, s: rw * 0.9 + rw * 0.45 * np.exp(-s / 3.5), twist=0.1)
    jag = jag or [(-1.0, 1.5), (-0.6, -1.0), (-0.25, 2.5), (0.1, -2.5), (0.45, 0.8), (0.8, -0.5), (1.0, 2.0)]
    pts = [(cx + u * rw * 1.4, top + d) for u, d in jag] + [(cx + rw * 1.6, base + 2), (cx - rw * 1.6, base + 2)]
    keep = c.poly(pts)
    c.wood(Wd, nz, mask=keep, moss_amt=0.62, ambient=0.24)
    return keep


def fungus_model(glow=1.0, seed=7):
    w, h = 48, 48
    c = Pc(w, h)
    cx, base = 23.0, 47.6
    # ground: leaf litter and moss
    c.put(c.ell(24, base + 0.2, 19, 2.6), 'soil', 0.35)
    top = 31.0
    keep = stump(c, cx, base, 7.5, top, seed)
    # the rotted heart, open at the top
    c.put(c.ell(cx + 0.6, top + 0.6, 5.2, 1.4) & keep, 'rot', 0.3)
    # a fallen limb lying against it, mossy
    Wd = T.Wood(w, h); nz = T.Noise(seed + 1)
    Wd.branch([(3, 46.2), (12, 44.8), (19, 44.0)], 2.8, 2.3, seed=seed + 2, twist=0.05)
    c.wood(Wd, nz, moss_amt=0.75)
    # bracket shelves on the stump's flank
    for (x0, y0, L, sd) in [(cx + 7.5, 41.0, 5.5, 1), (cx + 7.0, 37.0, 4.0, 1), (cx - 7.2, 39.0, 4.0, -1)]:
        pts = [(x0 - sd * 1.0, y0 + 0.6), (x0 + sd * L * 0.5, y0 - 1.3), (x0 + sd * L, y0 - 0.4), (x0 + sd * L * 0.95, y0 + 0.7),
               (x0 + sd * L * 0.4, y0 + 1.2), (x0 - sd * 1.0, y0 + 1.7)]
        m = c.poly(pts)
        v = c.dome(m, sigma=0.8, amb=0.3, key=0.65)
        v += 0.15 * (np.sin(np.hypot(c.X - x0, (c.Y - y0) * 2) * 2.4) > 0.5)   # growth rings
        c.put(m, 'shelf', v)
        c.put(c.poly([(x0, y0 + 1.2), (x0 + sd * L * 0.9, y0 + 0.8), (x0 + sd * L * 0.4, y0 + 1.8)]), 'shelfu', 0.35 * glow + 0.3)
    # the glowing mycena: a crowded colony on the stump top, more on the ground round its foot
    t0 = top + 0.4
    caps = [((cx - 4.0, t0), (cx - 7.0, 22.0), 3.6, 3.0, 0.9, -0.7), ((cx + 0.8, t0), (cx + 1.4, 16.5), 5.0, 4.0, 1.0, 0.6),
            ((cx + 4.2, t0), (cx + 8.0, 22.6), 3.2, 2.7, 0.85, 0.8), ((cx - 1.6, t0), (cx - 2.4, 26.0), 2.2, 1.9, 0.8, -0.2),
            ((cx + 2.8, t0), (cx + 3.6, 27.6), 1.6, 1.4, 0.75, 0.0), ((cx - 5.5, t0 + 0.5), (cx - 4.6, 28.6), 1.5, 1.3, 0.75, 0.2),
            ((cx + 6.4, t0 + 0.6), (cx + 5.6, 29.0), 1.4, 1.2, 0.7, -0.2),
            ((cx + 10.5, base), (cx + 11.8, 40.0), 2.6, 1.8, 0.85, 0.5), ((cx + 14.0, base), (cx + 14.4, 43.6), 1.6, 1.2, 0.75, 0.0),
            ((cx - 11.0, base - 1.4), (cx - 12.4, 39.4), 2.6, 1.8, 0.85, -0.5), ((cx - 14.4, base - 0.6), (cx - 14.8, 43.6), 1.4, 1.0, 0.7, 0.0)]
    for (b_, t_, rx, ry, gk, lean) in caps:
        mushroom(c, b_, t_, rx, ry, glow=gk * glow, lean=lean, stem_r=(max(0.45, rx * 0.2), max(0.35, rx * 0.14)))
    return c


ROT = ramp('#0b0907', '#14100c', '#1e1812', '#2a2219')
SHELF = TV_FUNG


def fungus_frames():
    out = []
    for k, g in enumerate((1.3, 1.17, 1.04, 1.17)):
        c = fungus_model(glow=g)
        s = c.resolve(0.45)
        R = {'cap': CAP, 'gill': GILL, 'stem': STEM, 'soil': SOIL, 'moss': TV_MOSS, 'bark': TV_BARK, 'rot': ROT, 'shelf': SHELF,
             'shelfu': GILL}
        s.index(R, dk=0.3).rim(R, mats={'cap', 'shelf'}, wts=(1.0, 0.5, 0.0, 0.0), steps=1)
        o = s.rgba(R)
        rng = np.random.default_rng(11)
        for i in range(5):                                  # spores drifting up out of the cluster
            x = int(12 + rng.integers(0, 24)); y = int(20 - ((k * 3 + i * 7) % 18))
            if o[y, x, 3] == 0: o[y, x] = (*P.C('#bff7d4'), 150 + 25 * ((i + k) % 3))
        o = selout(o, OUT, lit_k=0.3, near=s.m('cap') | s.m('gill') | s.m('bark') | s.m('moss') | s.m('shelf') | s.m('soil'))
        out.append(to_img(o))
    return out


# =============================================================================================== xsa_tvbig/rootarch
def rootarch_model(seed=3):
    """A trunk coming down out of the canopy that splits into two great buttress roots: an arch to walk under. Bark, moss and
    rim light are the tv_tree ones (treelib.Wood + the same shade parameters), so it sits with the new trunks."""
    w, h = 96, 128
    c = Pc(w, h); nz = T.Noise(80 + seed)
    Wd = T.Wood(w, h)
    # thin aerial roots hanging in the opening (behind)
    for i, (x0, L) in enumerate([(38, 30), (49, 44), (58, 26), (44, 18)]):
        Wd.branch([(x0, 44), (x0 + 1.5 * math.sin(i), 44 + L * 0.5), (x0 - 1 + i % 2 * 2, 44 + L)], 1.4, 0.5, wob=0.6, wobf=0.3, seed=60 + i, mossk=0.3)
    # the two legs: each a buttress root flaring onto the floor
    leg = lambda r0, r1: (lambda t, s: r1 + (r0 - r1) * (1 - t) ** 0.8 + 4.5 * np.exp(-(1 - t) * 40 / 6.0))
    Wd.branch([(44, 34), (32, 48), (21, 70), (14, 98), (9, 131)], 10.5, 7.0, wob=1.4, wobf=0.06, seed=seed + 1, rprof=leg(10.5, 6.5), twist=0.14, under=10)
    Wd.branch([(52, 34), (64, 49), (75, 72), (82, 100), (87, 131)], 10.0, 6.5, wob=1.4, wobf=0.06, seed=seed + 2, rprof=leg(10.0, 6.0), twist=0.14, under=10)
    # the trunk out of the canopy, swelling where it splits
    Wd.branch([(48, -8), (47, 12), (48, 28), (48, 40)], 15, 14, wob=1.0, wobf=0.06, seed=seed,
              rprof=lambda t, s: 13.5 + 5.0 * T.smooth(0.55, 1.0, t), twist=0.12)
    # smaller roots twisting round the legs, and fingers of root over the floor
    Wd.branch([(22, 66), (14, 88), (12, 110), (18, 131)], 3.2, 2.0, wob=1.2, wobf=0.2, seed=seed + 5, twist=0.3)
    Wd.branch([(75, 70), (84, 92), (85, 114), (79, 131)], 3.0, 1.8, wob=1.2, wobf=0.2, seed=seed + 6, twist=0.3)
    for i, (pts, r) in enumerate([([(8, 120), (0, 128), (-4, 131)], 3.2), ([(18, 122), (24, 128), (30, 131)], 2.6),
                                  ([(86, 120), (96, 127), (100, 131)], 3.2), ([(78, 122), (70, 128), (64, 131)], 2.4)]):
        Wd.branch(pts, r, 1.4, wob=0.6, wobf=0.3, seed=seed + 10 + i, mossk=1.4)
    c.wood(Wd, nz, moss_amt=0.55)
    # the arch's underside sinks into shadow (the opening is lit only from behind)
    hollow = c.poly([(20, 128), (30, 92), (40, 66), (48, 56), (56, 66), (66, 92), (76, 128)])
    sh = np.clip(1 - np.abs(c.X - 48) / 34, 0, 1) * (c.Y > 50)
    c.shift(c.cov & ~hollow, -0.0)
    c.shift(c.cov & (c.Y > 44) & (np.abs(c.X - 48) < 26), -0.12 * sh)
    return c


def rootarch():
    c = rootarch_model()
    s = c.resolve(0.5)
    R = {'bark': TV_BARK, 'moss': TV_MOSS}
    s.index(R, dk=0.35)
    o = s.rgba(R)
    al = s.alpha
    rng = np.random.default_rng(9)
    # moss beards hanging from the crotch of the arch
    anchors = [(x, y, 0.8) for y in range(44, 70) for x in range(30, 66) if al[y, x] and not al[min(127, y + 1), x] and rng.random() < 0.18]
    T.strands(o, rng, anchors, [P.C(hh) for hh in ('#1f2a1f', '#2f3d2c', '#44553d', '#5f7352')], length=(3, 12), per=(1, 3), sway=0.4)
    # floor mist: the lowest rows sink into the ground shadow
    yy = np.arange(128)[:, None]
    dim = np.clip((yy - 100) / 28.0, 0, 1) * 0.35
    o[..., :3] *= (1 - dim[..., None])
    o = selout(o, OUT, lit_k=0.35)
    return to_img(o)


# =============================================================================================== xsa_tv: the small set
IRON = ramp('#08090a', '#111315', '#1b1e21', '#272b2f', '#363b40', '#4a5056', '#646b70')
RUST = ramp('#1a0f0a', '#2c1910', '#432516', '#5c341d', '#7a4826')
WOOD = ramp('#0e0b08', '#17120d', '#221a13', '#2e241a', '#3c3022', '#4d3e2c', '#615038', '#776448')
HIDE = ramp('#120d09', '#1d150f', '#2a1f16', '#3a2b1e', '#4c3a28', '#614b34', '#7a6045', '#957a5a')
BONE = ramp('#2a2822', '#47433a', '#6a6556', '#8f8a77', '#b3ad98', '#d2ccb6')
EGG = ramp('#3a4038', '#5d665b', '#87917f', '#b0b9a6', '#d6dccd')
BREW = ramp('#0e2412', '#17401c', '#236326', '#3a8a32', '#68b04a', '#a8dc78', '#e0ffc0')
FIRE = ramp('#3a1206', '#7a2a0a', '#c04a12', '#f07a22', '#ffb050', '#ffe6a0')
GLASS = {'g': ramp('#0d1a14', '#173326', '#24503a', '#3b7656', '#6aa784'), 'r': ramp('#1a0c0c', '#33171a', '#552629', '#7a3a38', '#a8645a'),
         'a': ramp('#1a140a', '#33270f', '#554118', '#7d6226', '#a98a44'), 'p': ramp('#120d18', '#221a2e', '#382a48', '#544066', '#7a6292')}
HERB = {'g': ramp('#0e1a0f', '#172a17', '#223d20', '#30522a', '#466a37', '#5f8448'), 's': ramp('#141a10', '#222c18', '#344022', '#4a5730', '#677343', '#848f5a'),
        'r': ramp('#170d10', '#2a171a', '#3e2226', '#573137', '#73454a', '#8f5f60'), 'y': ramp('#1a170c', '#2c2713', '#433b1c', '#5e5329', '#7c6f3b', '#9a8c52')}
ROPE = ramp('#1c160e', '#30271a', '#4a3e2a', '#6b5c40')
RUNE = ramp('#123c2c', '#1d6644', '#2f9a5e', '#5fe08e', '#b4ffd0')


def rock(c, pts, seed, sigma=3.0, moss_amt=0.5, mat='stone', crack=5.0, amb=0.16, key=0.8, moss=True):
    m = c.poly(pts) if isinstance(pts, list) else pts
    nx, ny, nzv = c.normals(m, sigma=sigma)
    L = P.unit(P.LIGHT); d = np.clip(nx * L[0] + ny * L[1] + nzv * L[2], 0, 1)
    v = amb + key * d
    cr, cid = c.cracks(seed, cell=crack, aspect=0.7, width=0.1)
    v = v - 0.22 * cr + 0.08 * (cid - 0.5) + 0.08 * (c.noise(seed, 1.5) - 0.5)
    c.put(m, mat, v)
    if moss:
        n = c.noise(seed + 9, 1.2)
        mm = m & ((np.clip(-ny, 0, 1) * 1.1 + n * 0.7 - (1 - moss_amt) * 1.1) > 0.62)
        c.put(mm, 'moss', 0.3 + 0.55 * d + 0.15 * (n - 0.5))
    return m, d


def tuft(c, x, y, n, h, seed, mat='fern', spread=2.5, lean=0.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = rng.uniform(-0.6, 0.6) + lean; L = h * rng.uniform(0.6, 1.0); x0 = x + rng.uniform(-spread, spread)
        m, U, TT, ax, ay = c.stroke([(x0, y), (x0 + math.sin(a) * L * 0.5, y - L * 0.55), (x0 + math.sin(a) * L * 1.1, y - L)], 0.45, 0.15)
        c.put(m, mat, 0.3 + 0.5 * TT + 0.15 * (a < 0))


def tv_small(tag, seed=0):
    w, h = 48, 48; c = Pc(w, h); y = 47.8
    if tag == 'mossrock':
        rock(c, [(9, y), (10, y - 7), (14, y - 13), (21, y - 17), (29, y - 17.5), (35, y - 14), (39, y - 8), (41, y)], 21, sigma=3.5, moss_amt=0.7)
        rock(c, [(33, y), (35, y - 5), (40, y - 7), (45, y - 4), (46, y)], 22, sigma=1.6, moss_amt=0.5)
        tuft(c, 12, y, 4, 4, 1); tuft(c, 37, y, 3, 3.5, 2)
    elif tag == 'mossbank':
        m = c.poly([(1, y), (4, y - 5), (10, y - 8.5), (20, y - 10.5), (30, y - 10), (39, y - 8), (45, y - 4.5), (47.5, y)])
        nx, ny, nzv = c.normals(m, sigma=3.5)
        L = P.unit(P.LIGHT); d = np.clip(nx * L[0] + ny * L[1] + nzv * L[2], 0, 1)
        n = c.noise(41, 0.8)
        c.put(m, 'moss', 0.28 + 0.72 * d + 0.3 * (n - 0.5) - 0.2 * T.smooth(0.6, 0.85, c.noise(43, 0.5)) + 0.1 * np.sin(c.X * 2.1 + c.Y * 1.3) * (c.noise(44, 0.3) > 0.5))
        c.put(m & (c.Y > y - 2.5), 'soil', 0.35)
        for i, x in enumerate((7, 15, 24, 33, 41)): tuft(c, x, y - 7 - 2 * math.sin(x * 0.2), 4, 4.5, 5 + i)
        c.put(c.ell(18, y - 9.5, 0.6, 0.6) | c.ell(29, y - 9.8, 0.6, 0.6) | c.ell(38, y - 7.6, 0.6, 0.6), 'gill', 0.9)   # tiny glowing caps
    elif tag == 'stones':   # a cairn of flat stones
        yy = y
        for i, (rw, rh, dx) in enumerate([(12.5, 5.0, 0.0), (10.5, 4.4, -1.0), (8.5, 4.0, 0.8), (6.5, 3.4, -0.4), (4.4, 3.0, 0.5), (2.6, 2.4, 0.0)]):
            pts = [(24 + dx + rw * math.cos(a), yy - rh / 2 - (rh / 2) * math.sin(a) * (1.0 if math.sin(a) > 0 else 0.85)) for a in np.linspace(0, 2 * math.pi, 28)]
            rock(c, pts, 30 + i, sigma=1.4, moss_amt=0.35 if i < 2 else 0.2, crack=3.5, amb=0.24)
            yy -= rh - 0.4
        tuft(c, 15, y, 3, 3.5, 7); tuft(c, 33, y, 3, 3, 8)
    elif tag in ('stone_l', 'stone_s'):
        big = tag == 'stone_l'
        pts = ([(15.5, y), (15, y - 22), (16.5, y - 34), (20, y - 40), (26, y - 41.5), (30.5, y - 37), (32.5, y - 26), (33, y)] if big else
               [(18, y), (17.5, y - 12), (19.5, y - 19.5), (24, y - 22.5), (28.5, y - 20.5), (30.5, y - 12), (31, y)])
        m, d = rock(c, pts, 50 + big, sigma=3.2 if big else 2.4, moss_amt=0.45, crack=6.0 if big else 4.5)
        # carved spiral rune, faintly lit by the forest-spirit
        cxr, cyr = (24.0, y - 24) if big else (24.0, y - 11)
        c.rune = (cxr, cyr, big)
        tuft(c, 16, y, 4, 4.5, 3); tuft(c, 32, y, 3, 4, 4)
    elif tag == 'nest':       # a deep bowl of woven twigs, three pale speckled eggs showing over the rim
        rng = np.random.default_rng(3)
        bowl = (c.ell(24, y - 4.6, 10.5, 4.8) & (c.Y > y - 7.6)) | c.ell(24, y - 7.6, 10.6, 1.9)
        c.put(bowl, 'twig', 0.15 + 0.3 * c.dome(bowl, sigma=2.0, amb=0.0, key=1.0))
        c.put(c.ell(24, y - 7.9, 8.2, 1.2), 'rot', 0.15)                         # the cup
        for (ex, ey, r) in [(20.6, y - 9.0, 1.8), (24.4, y - 9.9, 1.9), (28.1, y - 8.9, 1.7)]:
            em = c.ell(ex, ey, r * 0.95, r * 1.2)
            c.put(em, 'egg', c.dome(em, sigma=0.7, amb=0.35, key=0.7))
        c.put(c.ell(23.8, y - 9.9, 0.35, 0.35) | c.ell(20.2, y - 8.8, 0.3, 0.3) | c.ell(28.3, y - 8.0, 0.3, 0.3), 'egg', 0.12)
        for i in range(70):                                          # woven twigs: lit on the rim, stray ends poking out
            a0 = rng.uniform(0, math.pi); x0 = 24 + 10.5 * math.cos(a0) * rng.uniform(0.5, 1.05); y0 = y - 5.0 + rng.uniform(-2.8, 4.6)
            L = rng.uniform(4, 9); ang = rng.uniform(-0.45, 0.45) + (rng.choice([-0.9, 0.9]) if rng.random() < 0.12 else 0)
            mm = c.stroke([(x0, y0), (x0 + math.cos(ang) * L, y0 + math.sin(ang) * L * 0.45)], 0.45, 0.3)[0]
            c.put(mm & ~c.ell(24, y - 8.4, 8.0, 1.6) & ~c.ell(24, y - 10, 6.5, 2.6), 'twig', 0.25 + 0.5 * (y0 < y - 6.5) + 0.15 * rng.random())
        c.put(c.ell(24, y - 0.3, 9, 0.8), 'soil', 0.3)
    elif tag == 'herbs':      # hanging from the top of the cell (SA_HANG): bundles of drying herbs on a cord
        m, U, TT, ax, ay = c.stroke([(1, 1.2), (24, 2.6), (47, 1.2)], 0.55, 0.55)
        c.put(m, 'rope', c.cyl(U, ax, ay, amb=0.2, key=0.7))
        rng = np.random.default_rng(14)
        for i, x in enumerate((6, 13, 20.5, 28, 35, 42)):
            y0 = 1.6 + 1.4 * math.sin(math.pi * x / 48); L = rng.uniform(10, 17); kind = 'gsrygs'[i]
            tie = c.rect(x - 1.2, y0, x + 1.2, y0 + 2.2)
            for k in range(14):                                       # stems fanning down from the tie, leaves along them
                a = rng.uniform(-0.28, 0.28); ll = L * rng.uniform(0.7, 1.0)
                mm, U, TT, ax, ay = c.stroke([(x + a * 1.5, y0 + 1.5), (x + math.sin(a) * ll * 0.6, y0 + ll * 0.6), (x + math.sin(a) * ll, y0 + ll)], 0.5, 0.3)
                c.put(mm, 'herb' + kind, c.cyl(U, ax, ay, amb=0.15, key=0.75) + 0.2 * (a < 0) - 0.15 * TT)
            c.put(tie, 'rope', 0.7)
    elif tag == 'shelves':
        frame = c.rect(9, y - 37, 39, y)
        c.put(frame, 'wood', 0.3 + 0.05 * c.noise(5, 0.6))
        c.put(c.rect(11, y - 35, 37, y - 1), 'rot', 0.12)               # the dark back
        for x0 in (9, 37): c.put(c.rect(x0, y - 37, x0 + 2, y), 'wood', 0.5 - 0.2 * (x0 > 20) + 0.1 * (c.X < x0 + 0.8))
        c.put(c.rect(8, y - 38.5, 40, y - 36.5), 'wood', 0.65)
        rng = np.random.default_rng(12)
        for sy in (y - 25, y - 13, y - 1.5):
            c.put(c.rect(10, sy, 38, sy + 1.6), 'wood', 0.62); c.put(c.rect(10, sy + 1.6, 38, sy + 2.2), 'wood', 0.18)
            x = 12.0
            while x < 34:
                kind = rng.choice(list('graap')); bw = rng.uniform(2.4, 4.2); bh = rng.uniform(4.5, 8.5); cx_ = x + bw / 2
                shape = rng.integers(0, 3)
                if shape == 0:   # round flask
                    mm = c.ell(cx_, sy - bw * 0.55, bw * 0.55, bw * 0.55) | c.rect(cx_ - 0.6, sy - bw * 1.1 - 2.2, cx_ + 0.6, sy - bw * 0.6)
                elif shape == 1: # tall bottle
                    mm = c.rect(cx_ - bw / 2, sy - bh + 2.4, cx_ + bw / 2, sy) | c.rect(cx_ - 0.6, sy - bh, cx_ + 0.6, sy - bh + 2.4)
                else:            # squat jar with a lid
                    mm = c.rect(cx_ - bw / 2, sy - bh * 0.55, cx_ + bw / 2, sy)
                    c.put(c.rect(cx_ - bw / 2 - 0.4, sy - bh * 0.55 - 1.0, cx_ + bw / 2 + 0.4, sy - bh * 0.55), 'wood', 0.55)
                v = c.dome(mm, sigma=0.7, amb=0.2, key=0.75)
                c.put(mm, 'glass' + kind, v)
                hl = mm & (np.abs(c.X - (cx_ - bw * 0.22)) < 0.35) & (c.Y < sy - 1)
                c.put(hl, 'glass' + kind, 1.0)
                x += bw + rng.uniform(0.8, 2.2)
        c.put(c.poly([(30, y - 37), (37.5, y - 37), (37.5, y - 30)]), 'web', 0.6)                        # cobweb in the corner
    elif tag == 'hide':       # a pelt laced into a frame of lashed poles, propped on its feet
        def pole(p0, p1, r=1.0):
            m, U, TT, ax, ay = c.stroke([p0, p1], r, r * 0.85); c.put(m, 'wood', c.cyl(U, ax, ay, amb=0.15, key=0.75) + 0.08 * (c.noise(3, 0.4) - 0.5))
        fl, fr_, ft, fb = 10.0, 38.0, y - 33.0, y - 3.0
        pole((fl + 2, y + 0.5), (fl - 1, ft - 3)); pole((fr_ - 2, y + 0.5), (fr_ + 1, ft - 3))
        pole((fl - 3, ft + 1), (fr_ + 3, ft - 0.5), 0.9)
        # the pelt: a stretched body with four limbs pulled to the corners, the head and tail
        cx_, cy_ = 24.0, (ft + fb) / 2 + 0.5
        body = c.ell(cx_, cy_, 8.5, 10.5)
        for (lx, ly) in [(fl + 2.5, ft + 4), (fr_ - 2.5, ft + 4), (fl + 2.5, fb - 4), (fr_ - 2.5, fb - 4)]:
            m, U, TT, ax, ay = c.stroke([(cx_ + (lx - cx_) * 0.3, cy_ + (ly - cy_) * 0.3), (lx, ly)], 3.2, 1.3); body |= m
        body |= c.ell(cx_, ft + 2.6, 2.6, 2.4) | c.stroke([(cx_, cy_ + 9), (cx_ + 0.5, fb + 0.5)], 1.5, 0.6)[0]
        n = c.noise(77, 0.6)
        fur = 0.12 * np.sin(c.X * 0.9 + n * 6 + np.abs(c.X - cx_) * 0.8)                                  # hair lying outward from the spine
        spine = np.exp(-((c.X - cx_) / 2.2) ** 2)
        c.put(body, 'hide', 0.42 + 0.2 * spine - 0.18 * np.clip(np.abs(c.X - cx_) / 10, 0, 1) + fur + 0.18 * (n - 0.5) - 0.1 * (c.Y > cy_ + 6))
        c.put(body & (c.noise(78, 0.45) > 0.7), 'hide', 0.22)
        for (px, py, qx, qy) in [(fl + 2.5, ft + 4, fl - 0.5, ft + 1), (fr_ - 2.5, ft + 4, fr_ + 0.5, ft + 1), (fl + 2.5, fb - 4, fl + 1, fb - 1),
                                 (fr_ - 2.5, fb - 4, fr_ - 1, fb - 1), (cx_, ft + 1, cx_, ft - 0.5), (cx_ - 7, cy_, fl - 0.3, cy_), (cx_ + 7, cy_, fr_ + 0.3, cy_)]:
            m, U, TT, ax, ay = c.stroke([(px, py), (qx, qy)], 0.35, 0.35); c.put(m, 'rope', 0.65)   # the lacing
        pole((fl - 3, fb + 1), (fr_ + 3, fb + 0.5), 0.9)
    return c


def snare(shut):
    """A leghold trap staked to the ground: rusted iron jaws with teeth, open flat (f0) or sprung shut (f1). Must read as a trap."""
    w, h = 48, 48; c = Pc(w, h); y = 47.8
    c.put(c.ell(24, y - 0.4, 12, 1.6), 'soil', 0.3)
    # the chain to its stake
    for i in range(6):
        x = 33.5 + i * 1.8; yy = y - 1.2 + 0.25 * math.sin(i)
        c.put(c.ell(x, yy, 1.0, 0.65 if i % 2 else 0.4), 'iron', 0.55 if i % 2 else 0.35)
    st, U, TT, ax, ay = c.stroke([(44.5, y - 7), (44.5, y + 0.5)], 0.9, 0.7)
    c.put(st, 'wood', c.cyl(U, ax, ay, amb=0.2, key=0.7)); c.put(c.rect(43.2, y - 7.8, 45.8, y - 6.4), 'wood', 0.75)
    # base plate and springs
    c.put(c.ell(24, y - 1.2, 9.5, 1.5), 'iron', 0.35)
    for sx in (13.5, 34.5):
        m = c.ell(sx, y - 1.4, 2.4, 1.3); c.put(m, 'iron', c.dome(m, sigma=0.6, amb=0.2, key=0.7))
    if not shut:   # the jaws lie open as an oval ring round the pan, teeth standing up all round
        ring = c.ell(24, y - 2.6, 10.2, 2.8) & ~c.ell(24, y - 2.6, 8.4, 1.7)
        c.put(ring, 'iron', 0.4 + 0.3 * (c.Y < y - 2.6))
        for k in range(14):
            a_ = math.pi * (k + 0.5) / 14
            for sd in (-1, 1):
                tx = 24 + 9.3 * math.cos(a_); ty = y - 2.6 - sd * 2.2 * math.sin(a_)
                c.put(c.poly([(tx - 0.7, ty), (tx, ty - 2.2 - 0.3 * (sd > 0)), (tx + 0.7, ty)]), 'iron', 0.8 if sd > 0 else 0.55)
        pan = c.ell(24, y - 2.6, 3.2, 1.1); c.put(pan, 'rust', 0.55)
        c.put(c.ell(24, y - 2.9, 1.0, 0.5), 'iron', 0.85)
    else:
        for sd in (-1, 1):   # jaws snapped up together into a tooth-lined arch
            pts = [(24 + sd * 10.5, y - 1.5), (24 + sd * 9.0, y - 6.5), (24 + sd * 5.0, y - 10.5), (24 + sd * 0.4, y - 12.0)]
            m, U, TT, ax, ay = c.stroke(pts, 1.3, 1.1)
            c.put(m, 'iron', c.cyl(U, ax, ay, amb=0.25, key=0.75))
            for k in range(4):
                t = 0.25 + k * 0.2; px = 24 + sd * (10.0 - 9.5 * t); py = y - 2 - 10 * math.sin(t * math.pi / 2)
                c.put(c.poly([(px, py - 1.0), (px - sd * 2.8, py + 0.2), (px, py + 1.1)]), 'iron', 0.75)
        c.put(c.rect(23.5, y - 11.5, 24.5, y - 1.5), 'iron', 0.2)
    # rust blooms on the iron
    r = c.noise(19, 0.5) > 0.62
    c.remat(r, 'iron', 'rust')
    return c


def cauldron(k):
    """An iron cauldron on three legs over a fire, a green brew bubbling (code light at y-18 = the brew)."""
    w, h = 48, 48; c = Pc(w, h); y = 47.8
    c.put(c.ell(24, y - 0.6, 12, 1.6), 'soil', 0.25)
    # firewood and flames under the pot
    for (x0, x1, yy) in [(13, 33, y - 1.6), (16, 35, y - 2.4), (31, 14, y - 2.0)]:
        m, U, TT, ax, ay = c.stroke([(x0, yy), (x1, yy - 0.6)], 0.9, 0.8); c.put(m, 'wood', c.cyl(U, ax, ay, amb=0.1, key=0.5) + 0.25 * (np.abs(c.X - 24) < 5))
    rng = np.random.default_rng(40 + k)
    for i in range(7):
        fx = 17.5 + i * 2.2 + rng.uniform(-0.5, 0.5); fh = 4.0 + 2.6 * math.sin(i * 1.7 + k * 2.1) ** 2
        m = c.poly([(fx - 1.3, y - 2.2), (fx + rng.uniform(-0.8, 0.8), y - 2.2 - fh), (fx + 1.3, y - 2.2)])
        c.put(m, 'fire', 0.35 + 0.65 * np.clip((c.Y - (y - 2.2 - fh)) / fh, 0, 1) * (1 - 0.3 * (i % 2)))
    for sd in (-1, 0, 1):   # legs
        m, U, TT, ax, ay = c.stroke([(24 + sd * 9.5, y - 9), (24 + sd * 11.5, y - 0.5)], 0.9, 0.7)
        c.put(m, 'iron', c.cyl(U, ax, ay, amb=0.12, key=0.6) - 0.1 * (sd == 0))
    body = c.ell(24, y - 12.5, 11.5, 8.5) & (c.Y > y - 18.5)
    nx, ny, nzv = c.normals(body, sigma=3.5); L = P.unit(P.LIGHT); d = np.clip(nx * L[0] + ny * L[1] + nzv * L[2], 0, 1)
    under = np.clip((c.Y - (y - 12)) / 6, 0, 1) * np.clip(-ny + 0.3, 0, 1)
    c.put(body, 'iron', 0.12 + 0.6 * d + 0.35 * under)        # the fire lights its belly
    c.remat(body & (c.Y > y - 9) & (c.noise(7, 0.5) > 0.6), 'iron', 'rust')
    lip = c.ell(24, y - 18.5, 12.6, 2.3)
    c.put(lip, 'iron', 0.55 + 0.25 * (c.Y < y - 19))
    brew = c.ell(24, y - 18.7, 10.6, 1.5)
    c.put(brew, 'brew', 0.5 + 0.25 * np.cos((c.X - 24) * 0.5 + k * 2.0) * 0.5)
    for i in range(3):   # bubbles rising and bursting
        bx = 18.5 + i * 5.5 + (k % 2); by = y - 19.3 - ((i + k) % 3) * 0.7; br = 0.8 + 0.4 * ((i + k) % 2)
        c.put(c.ell(bx, by, br, br * 0.8), 'brew', 0.92)
    for sd in (-1, 1):   # lug handles
        c.put(c.ell(24 + sd * 12.0, y - 16.5, 1.4, 1.4) & ~c.ell(24 + sd * 12.0, y - 16.5, 0.6, 0.6), 'iron', 0.55)
    # steam above the brew
    for i in range(3):
        sx = 20 + i * 4 + (k + i) % 2; sy = y - 23 - ((k + i) % 3) * 2.2
        c.put(c.ell(sx, sy, 1.2, 0.7), 'steam', 0.6)
    return c


TV_R = {'stone': STONE, 'moss': TV_MOSS, 'fern': FERN, 'soil': SOIL, 'gill': GILL, 'rune': RUNE, 'bark': TV_BARK, 'twig': WOOD, 'rot': ROT,
        'egg': EGG, 'rope': ROPE, 'wood': WOOD, 'hide': HIDE, 'iron': IRON, 'rust': RUST, 'brew': BREW, 'fire': FIRE,
        'steam': ramp('#3a4a40', '#58695d', '#7a8b7e'), 'web': ramp('#3c4440', '#5c6560', '#7c8680'),
        **{'glass' + k: v for k, v in GLASS.items()}, **{'herb' + k: v for k, v in HERB.items()}}


def weave(s, rng):
    """1x woven-twig texture on the nest: short diagonal strands alternating light and dark, row by row."""
    m = s.m('twig'); n = len(WOOD)
    for y in range(s.h):
        off = int(rng.integers(0, 4)); d = 1 if y % 2 else -1
        for x in range(s.w):
            if m[y, x]: s.idx[y, x] = int(np.clip(s.idx[y, x] + (2 if ((x * d + off) % 4) < 2 else -1), 0, n - 1))


def finish_small(c, rim_mats=None, alpha_mats=None, near_skip=None, post=None):
    s = c.resolve(0.45)
    s.index(TV_R, dk=0.3).rim(TV_R, mats=rim_mats, wts=(1.0, 0.6, 0.0, 0.0), steps=1, minv=0.2)
    if post: post(s)
    o = s.rgba(TV_R)
    if alpha_mats:
        for nm, a in alpha_mats.items(): o[s.m(nm), 3] = a
    near = None
    if near_skip: near = s.alpha & ~np.logical_or.reduce([s.m(n) for n in near_skip])
    return to_img(selout(o, OUT, lit_k=0.35, near=near))


def xsa_tv_set():
    rep = {}
    for tag in ('mossrock', 'mossbank', 'stones', 'stone_l', 'stone_s', 'nest', 'herbs', 'shelves', 'hide'):
        c = tv_small(tag)
        post = (lambda s_: weave(s_, np.random.default_rng(8))) if tag == 'nest' else None
        rep[tag] = finish_small(c, rim_mats={'stone', 'moss', 'wood', 'hide', 'twig', 'egg', 'herbg', 'herbs', 'herbr', 'herby'},
                                near_skip=('fern', 'web', 'steam'), post=post)
        if tag == 'mossbank':   # a few small pale wood-sorrel flowers in the moss
            a = np.asarray(rep[tag]).copy(); rng = np.random.default_rng(12)
            for i in range(14):
                x = int(rng.integers(5, 43)); col = a[:, x, 3] > 0
                if not col.any(): continue
                yy = int(np.argmax(col)) + int(rng.integers(1, 4))
                a[yy, x, :3] = P.C('#c9d2bd') if i % 3 else P.C('#d8cf9a'); a[yy, x, 3] = 255
            rep[tag] = Image.fromarray(a)
        if getattr(c, 'rune', None):    # a carved spiral, cut dark and faintly lit by the forest-spirit
            a = np.asarray(rep[tag]).copy(); cxr, cyr, big = c.rune; seen = set()
            for k in range(105 if big else 70):
                t = k * 0.12; r = 0.4 + t * (0.42 if big else 0.3)
                q = (int(round(cxr + r * math.cos(t))), int(round(cyr + r * math.sin(t) * 1.2)))
                if q in seen or a[q[1], q[0], 3] == 0: continue
                seen.add(q); a[q[1], q[0], :3] = RUNE[1 if k > 80 else 2]
            rep[tag] = Image.fromarray(a)
    rep['snare'] = [finish_small(snare(False), rim_mats={'iron'}), finish_small(snare(True), rim_mats={'iron'})]
    rep['cauldron'] = [finish_small(cauldron(k), rim_mats={'iron'}, alpha_mats={'steam': 120}, near_skip=('steam', 'fire')) for k in range(3)]
    return rep


# =============================================================================================== main
def main():
    todo = ARGS or ['fern', 'shroom']
    if 'fern' in todo:
        im = fern(); save_prev('tv_fern', [im, im.transpose(Image.FLIP_LEFT_RIGHT), P.v1_frames('tv_fern')[0]])
        if not NO_ASE: P.build_sheet('tv_fern', {'idle': im})
    if 'shroom' in todo:
        im = shroom(); save_prev('tv_shroom', [im, P.v1_frames('tv_shroom')[0]])
        if not NO_ASE: P.build_sheet('tv_shroom', {'idle': im})
    if 'vine' in todo:
        fr = vine(); save_prev('tv_vine', fr + P.v1_frames('tv_vine'))
        if not NO_ASE: P.build_sheet('tv_vine', {'loop': fr})
    if 'tvbig' in todo:
        im = rootarch(); save_prev('xsa_tvbig', [im, P.v1_frames('xsa_tvbig')[0]], scale=3)
        if not NO_ASE: P.build_sheet('xsa_tvbig', {'rootarch': im})
    if 'tv' in todo or 'fungus' in todo:
        rep = xsa_tv_set() if 'tv' in todo else {}
        rep['fungus'] = fungus_frames()
        v1 = P.v1_frames('xsa_tv'); _, _, _, tags = P.read_contract('xsa_tv'); td = {t: (a, b) for t, a, b in tags}
        for tag, fr in rep.items():
            fr = fr if isinstance(fr, list) else [fr]
            save_prev('xsa_tv_' + tag, fr + v1[td[tag][0]:td[tag][1] + 1])
        if not NO_ASE and 'tv' in todo: P.build_sheet('xsa_tv', rep)


if __name__ == '__main__':
    main()
