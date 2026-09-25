#!/usr/bin/env python3
"""Story panels -- docs/ART_SPEC2.md section G.

    python3 art/gen_story.py              build all six panels (Aseprite) + preview
    python3 art/gen_story.py --preview    preview only (no Aseprite)
    python3 art/gen_story.py --only story_4[,story_1] [--preview]

Panels (384x216 opaque, 1 frame, tag `p`), composed like key art:
    story_1           the Pale Root standing golden over a kingdom
    story_2           the Root falling, ash raining
    story_3           hollowed knights in the ruins, a lone shrine flame
    story_4           the Ashbound knight waking on the cliff (from behind), the fallen Root on the horizon
    story_end_kindle  the knight seated on the root throne, the tree glowing anew
    story_end_ash     the knight walking away at dawn; the last gold fades, green shoots in the ash
Each is built in depth layers (Sky, Far, Mid, Near, FX) so the .aseprite source stays editable.
Preview: art/previews/story.png (all panels 2x) + art/previews/story_<name>.png (3x).

Method: value fields -> hand-picked ramps via 4x4 ordered dither (pixel-clean, limited palette);
shapes are polygons / tapered branch segments / blob clusters; light = radial glows, god-rays,
1-2px rim light on silhouettes facing the key light; particles for ash, embers and petals.
Palette is shared with the ramparts backgrounds (dusky sky ramp, gold ramp, violet-black silhouettes)
and the player sprite (blackened steel + crimson).
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402

W, H = 384, 216
BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))


def C(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def ramp(*hs):
    return np.array([C(h) for h in hs], dtype=np.uint8)


# =========================================================================== palettes
# dusk sky (same ramp as bg_ramparts_far)
SKY = ramp("0c0a17", "120e22", "19122b", "221733", "2c1c3a", "38213f", "462742", "552d44", "663445",
           "7a3d46", "8e4a47", "a25a4a", "b46c4e", "c48054", "d29760", "deb070", "e9ca88", "f3e2ac")
GOLD = ramp("3a2616", "6a4630", "8e6038", "b4843e", "d4a44a", "ecc466", "f8e098", "fff6d0")
HOT = ramp("b4843e", "ecc466", "f8e098", "fff6d0", "ffffff")
MT = ramp("1a1428", "221a32", "2c223c", "362a46", "423250", "4e3a58")
SIL = ramp("0a0810", "0f0d17", "15121e", "1c1826", "241f30", "2e2839", "3a3143")
STEEL = ramp("08070c", "14131e", "212030", "34354a", "545a76", "969fc4")
CRIM = ramp("0a0307", "1c0810", "340c1a", "521224", "76182e", "a02438", "d8404a")
ASH = ramp("16151a", "24222a", "35323a", "4a464c", "625d60", "7e7876", "a09892", "c4bcb2")
COLD = ramp("07080d", "0c0f18", "121724", "1a2030", "232b3e", "2e384e", "3b4760", "4d5b76", "65758f")
FLAME = ramp("7a2a10", "c0501a", "f08a2a", "ffc14a", "ffe890", "fffbe8")
BLOOD = ramp("100306", "250710", "3e0a17", "5c0e1d", "7e1a22", "a8322a", "d2582e", "f08a3a")
DAWN = ramp("1b2233", "25304a", "334263", "475a7e", "62779a", "8095b3", "a3b3c8", "c7cfd8", "e4dcd4",
            "f2d8c4", "f8e4c8", "fff4e0")
GREEN = ramp("1d2e1a", "2f4a24", "477030", "6a9a3a", "9cc452", "d2eb8a")
WARM = ramp("0c0f18", "1a1a24", "2a2228", "3f2c26", "5c3a26", "87522a", "b87430", "e0a040", "f8d070")
SKYP = ramp("2a3350", "36426a", "4a5a86", "6478a2", "8298bc", "a4b6d2", "c6d2e2", "e2e8ee", "f6f2e6")
PALE = ramp("5d5a70", "7b7890", "9c9aae", "c0bfcc", "e2e0e4", "fbf8ee")

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
TH = (np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W] + 0.5) / 16.0
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def pick(r, v):
    """ordered-dither a value field v (0..1) into ramp r -> (H,W,3)."""
    n = len(r)
    f = np.clip(v, 0, 1) * (n - 1)
    i = np.floor(f)
    i = i + ((f - i) > TH)
    return r[np.clip(i, 0, n - 1).astype(np.int32)]


def pick_flat(r, v):
    n = len(r)
    return r[np.clip(np.round(np.clip(v, 0, 1) * (n - 1)), 0, n - 1).astype(np.int32)]


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- noise (used sparingly)
def _hash(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(sx, sy, seed):
    gx, gy = W // sx + 3, H // sy + 3
    ix, iy = np.meshgrid(np.arange(gx, dtype=np.int64), np.arange(gy, dtype=np.int64))
    g = _hash(ix, iy, seed).astype(np.float32)
    fx, fy = XX / sx, YY / sy
    x0, y0 = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
    tx, ty = fx - x0, fy - y0
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = g[y0, x0] + (g[y0, x0 + 1] - g[y0, x0]) * tx
    b = g[y0 + 1, x0] + (g[y0 + 1, x0 + 1] - g[y0 + 1, x0]) * tx
    return a + (b - a) * ty


def fbm(sx, sy, seed, oct=3):
    v, amp, tot = 0, 1.0, 0
    for o in range(oct):
        v = v + vnoise(max(1, sx >> o), max(1, int(sy / (2 ** o)) or 1), seed + o * 31) * amp
        tot += amp
        amp *= 0.5
    return v / tot


def noise1(x, scale, seed):
    """1-D smooth noise for ridgelines (x array)."""
    fx = np.asarray(x, dtype=np.float64) / scale
    i = np.floor(fx).astype(np.int64)
    t = fx - i
    t = t * t * (3 - 2 * t)
    a, b = _hash(i, 7, seed), _hash(i + 1, 7, seed)
    return a + (b - a) * t


def ridge(base, amp, scale, seed, oct=3):
    x = np.arange(W)
    v, a, tot = 0, 1.0, 0
    for o in range(oct):
        v = v + noise1(x, scale / 2 ** o, seed + o) * a
        tot += a
        a *= 0.5
    return base + amp * (v / tot - 0.5) * 2


# ---------------------------------------------------------------- canvas / layers
class Layer:
    def __init__(self, name):
        self.name = name
        self.rgb = np.zeros((H, W, 3), np.uint8)
        self.a = np.zeros((H, W), bool)

    def put(self, mask, col):
        """col: (3,) colour or (H,W,3) array."""
        mask = mask & np.ones((H, W), bool)
        if isinstance(col, np.ndarray) and col.ndim == 3:
            self.rgb[mask] = col[mask]
        else:
            self.rgb[mask] = col
        self.a |= mask

    def dot(self, x, y, col):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.rgb[y, x] = col
            self.a[y, x] = True

    def image(self):
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = self.rgb
        out[..., 3] = np.where(self.a, 255, 0)
        return Image.fromarray(out)


def polymask(pts):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=255)
    return np.array(im) > 0


def ellmask(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return ((XX + .5 - cx) / rx) ** 2 + ((YY + .5 - cy) / ry) ** 2 <= 1.0


def below(yline):
    """mask of pixels on/below a per-column line (array of len W)."""
    return YY >= np.asarray(yline)[None, :]


def shift(m, dx, dy):
    out = np.zeros_like(m)
    H_, W_ = m.shape
    ys = slice(max(0, dy), H_ + min(0, dy))
    yd = slice(max(0, -dy), H_ + min(0, -dy))
    xs = slice(max(0, dx), W_ + min(0, dx))
    xd = slice(max(0, -dx), W_ + min(0, -dx))
    out[ys, xs] = m[yd, xd]
    return out


def edge_toward(m, dx, dy, width=1):
    """pixels of m whose neighbour toward (dx,dy) is outside m (rim facing the light)."""
    sx = int(np.sign(dx)) if abs(dx) > 0.35 else 0
    sy = int(np.sign(dy)) if abs(dy) > 0.35 else 0
    e = np.zeros_like(m)
    cur = m.copy()
    for k in range(1, width + 1):
        e |= m & ~shift(m, -sx * k, -sy * k)
    return e


def outline(m):
    return (shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)) & ~m


def segs_mask(segs):
    """segs: (x0,y0,x1,y1,w) tapered capsules -> (mask, width field, axis-param field)."""
    m = np.zeros((H, W), bool)
    wf = np.zeros((H, W), np.float32)
    side = np.zeros((H, W), np.float32)     # signed perpendicular offset / radius (-1..1)
    for (x0, y0, x1, y1, w0, *rest) in segs:
        w1 = rest[0] if rest else w0
        r = max(w0, w1) / 2 + 1
        xa, xb = int(max(0, min(x0, x1) - r)), int(min(W - 1, max(x0, x1) + r))
        ya, yb = int(max(0, min(y0, y1) - r)), int(min(H - 1, max(y0, y1) + r))
        if xa > xb or ya > yb:
            continue
        px = XX[ya:yb + 1, xa:xb + 1] + .5
        py = YY[ya:yb + 1, xa:xb + 1] + .5
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy or 1e-6
        t = np.clip(((px - x0) * vx + (py - y0) * vy) / L2, 0, 1)
        cx, cy = x0 + vx * t, y0 + vy * t
        rr = (w0 + (w1 - w0) * t) / 2
        d = np.hypot(px - cx, py - cy)
        hit = d <= np.maximum(rr, 0.5)
        ln = math.sqrt(L2)
        nx, ny = -vy / ln, vx / ln
        sd = ((px - cx) * nx + (py - cy) * ny) / np.maximum(rr, 0.5)
        sub_m = m[ya:yb + 1, xa:xb + 1]
        sub_w = wf[ya:yb + 1, xa:xb + 1]
        sub_s = side[ya:yb + 1, xa:xb + 1]
        upd = hit & (rr * 2 >= sub_w)
        sub_s[upd] = sd[upd]
        sub_w[upd] = (rr * 2)[upd]
        sub_m |= hit
    return m, wf, side


def branch_tree(rnd, x, y, ang, length, width, depth, curl, segs, spread=(0.3, 0.6), shrink=(0.55, 0.72),
                step=4.0, grav=0.0, twig=True, wmin=1.0):
    """recursive branching; ang radians (pi/2 = up). Appends tapered segments."""
    n = max(2, int(length / step))
    for i in range(n):
        ang += curl + rnd.uniform(-0.06, 0.06)
        x2 = x + math.cos(ang) * step
        y2 = y - math.sin(ang) * step + grav * i
        w0 = width * (1 - 0.35 * i / n)
        w1 = width * (1 - 0.35 * (i + 1) / n)
        segs.append((x, y, x2, y2, max(wmin, w0), max(wmin, w1)))
        x, y = x2, y2
        if twig and depth >= 1 and i > 1 and i % 3 == 1:
            sd = rnd.choice((-1, 1))
            branch_tree(rnd, x, y, ang + sd * rnd.uniform(0.5, 0.9), length * 0.3, max(wmin, width * 0.35), 0,
                        -sd * 0.03, segs, step=step * 0.8, twig=False, grav=grav, wmin=wmin)
    if depth > 0:
        k = 2 if depth > 1 or rnd.random() < 0.7 else 3
        for j in range(k):
            sd = -1 if j == 0 else 1
            branch_tree(rnd, x, y, ang + sd * rnd.uniform(*spread) + (0 if k == 2 else (j - 1) * 0.2),
                        length * rnd.uniform(*shrink), width * 0.64, depth - 1, sd * 0.015, segs, spread, shrink,
                        step, grav, twig, wmin)
    return segs


def tips(segs, wmax=2.2):
    return [(s[2], s[3]) for s in segs if s[5] <= wmax]


def radial(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
    return np.clip(1 - d, 0, 1)


def blur(f, r):
    """box blur (twice = tent) of a float/bool field, radius r."""
    f = f.astype(np.float32)
    for _ in range(2):
        c = np.cumsum(np.pad(f, ((0, 0), (r + 1, r)), mode="edge"), axis=1)
        f = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
        c = np.cumsum(np.pad(f, ((r + 1, r), (0, 0)), mode="edge"), axis=0)
        f = (c[2 * r + 1:, :] - c[:-2 * r - 1, :]) / (2 * r + 1)
    return f


def rays(cx, cy, freq, phase=0.0, sharp=3.0):
    ang = np.arctan2(YY - cy, XX - cx)
    return (0.5 + 0.5 * np.sin(ang * freq + phase + np.sin(ang * 3.1) * 0.8)) ** sharp


def compose(layers):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for L in layers:
        out.alpha_composite(L.image())
    return out


def particles(L, rnd, n, box, cols, size=(1, 1), streak=0, dirv=(0.0, 1.0), avoid=None, weights=None):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if avoid is not None and avoid[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))]:
            continue
        c = cols[rnd.randrange(len(cols))] if weights is None else rnd.choices(cols, weights)[0]
        s = rnd.randint(*size)
        for k in range(s):
            L.dot(x + (k if s > 1 and rnd.random() < 0.5 else 0), y + (k if s > 1 else 0) * 0, c)
        for k in range(1, streak + 1):
            L.dot(x - dirv[0] * k, y - dirv[1] * k, c)


def rim(L, m, dx, dy, col, width=1, only=None):
    e = edge_toward(m, dx, dy, width)
    if only is not None:
        e &= only
    L.put(e, col)
    return e


# =========================================================================== shared pieces
def bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def draw_knight_back(L, ox, oy, s, light, rim_warm, rim_cape, wind=1.0, sky_rim=None, sword=True, seed=3):
    """The Ashbound knight seen from behind (facing into the picture). (ox, oy) = feet centre,
    s = px per unit (figure is ~115 units tall). light = (dx, dy) toward the key light."""
    rnd = random.Random(seed)

    def P(pts):
        return [(ox + x * s, oy + y * s) for x, y in pts]
    dx, dy = light
    sky_rim = STEEL[3] if sky_rim is None else sky_rim
    # legs: armoured, slightly apart
    legL = polymask(P([(-10, 0), (-11, -4), (-9, -24), (-8, -50), (-1, -50), (-2, -24), (-3, -4), (-2, 0)]))
    legR = polymask(P([(3, 0), (3, -4), (2, -24), (1, -50), (8, -50), (9, -24), (11, -4), (12, 0)]))
    legs = legL | legR
    L.put(legs, STEEL[1])
    L.put(legs & ~shift(legs, 0, -1), STEEL[2])
    for k in (-24, -23):                                   # knee cops
        L.put(polymask(P([(-10, k - 3), (-2, k - 3), (-2, k + 1), (-10, k + 1)])) & legL, STEEL[2])
        L.put(polymask(P([(2, k - 3), (10, k - 3), (10, k + 1), (2, k + 1)])) & legR, STEEL[2])
    rim(L, legs, dx, dy, STEEL[4], 1)
    # left arm hanging, gauntlet just clear of the cape
    armL = polymask(P([(-19, -80), (-24, -66), (-25, -52), (-22, -46), (-18, -48), (-17, -64)]))
    L.put(armL, STEEL[1])
    rim(L, armL, 0, -1, STEEL[3], 1)
    # sword arm (right) reaching down to the hilt
    hand = (18, -50)
    armR = polymask(P([(17, -80), (23, -66), (21, -50), (15, -48), (13, -64)]))
    L.put(armR, STEEL[1])
    if sword:
        tip = (40, 0)
        hx, hy = ox + hand[0] * s, oy + hand[1] * s
        tx, ty = ox + tip[0] * s, oy + tip[1] * s
        sm, _, sd = segs_mask([(hx, hy, tx, ty, 3.0 * s, 1.2)])
        L.put(sm, STEEL[2])
        L.put(sm & (sd > 0.15), STEEL[4])
        L.put(sm & (sd > 0.55), rim_warm)
        g0 = (hx - 4 * s, hy - 2.8 * s)
        g1 = (hx + 4.2 * s, hy + 2.6 * s)
        gm, _, _ = segs_mask([(g0[0], g0[1], g1[0], g1[1], 1.8 * s)])
        L.put(gm, GOLD[3])
        L.put(edge_toward(gm, 0, -1), GOLD[5])
        pm = ellmask(hx - 2.2 * s, hy - 4.6 * s, 1.6 * s)
        L.put(pm, GOLD[4])
    # pauldrons (big, layered) - under the cape's collar
    pl = ellmask(ox - 15 * s, oy - 80 * s, 10 * s, 7.5 * s)
    pr = ellmask(ox + 15 * s, oy - 80 * s, 10 * s, 7.5 * s)
    for pm_, sgn in ((pl, -1), (pr, 1)):
        L.put(pm_, STEEL[2])
        for k in (3, 6):
            L.put(pm_ & (np.abs(YY - (oy - (80 - k) * s)) < 0.6 * max(1, s)), STEEL[1])
        rim(L, pm_, 0, -1, STEEL[4], 1)
        if sgn * dx > 0:
            rim(L, pm_, dx, dy, rim_warm, 1)
    L.put(ellmask(ox + 15 * s, oy - 84 * s, 3 * s, 1.2 * s) & pr, STEEL[3])
    # cape: gathered at the shoulders, sweeping right on the wind, tattered hem
    w = wind
    left = bez((-12, -86), (-20, -70), (-20, -40), (-18, -14), 12)
    right = bez((12, -86), (22, -70), (26 + 10 * w, -40), (30 + 16 * w, -12 - 6 * w), 12)
    hem = []
    x0, y0 = -18, -14
    x1, y1 = 30 + 16 * w, -12 - 6 * w
    n = 16
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + 5 * math.sin(t * math.pi) * (1 - 0.5 * w)
        if i % 2 == 1:
            y -= rnd.uniform(2.0, 5.0)
        elif 0 < i < n:
            y += rnd.uniform(0.0, 2.5)
        hem.append((x, y))
    cape_pts = left + hem + right[::-1]
    cape = polymask(P(cape_pts))
    nx, ny = ox, oy - 92 * s
    angf = np.arctan2(XX - nx, YY - ny)
    distf = np.hypot(XX - nx, YY - ny) / s
    fold = 0.5 + 0.5 * np.sin(angf * 11 + np.sin(distf * 0.07) * 0.9)
    band = np.floor(fold * 3.2) / 3.0
    lit = smooth(ox - 6 * s, ox + 34 * s, XX) * (1 if dx > 0 else 0) + smooth(ox + 6 * s, ox - 30 * s, XX) * (1 if dx < 0 else 0)
    v = 0.2 + 0.28 * band + 0.22 * lit - 0.1 * smooth(-30, -6, (YY - oy) / s)
    L.put(cape, pick(CRIM, v))
    L.put(cape & (fold < 0.1), CRIM[1])
    side = (XX - ox) * np.sign(dx) > 6 * s
    rim(L, cape, dx, dy, rim_cape, max(1, int(round(s * 1.2))), only=side)
    rim(L, cape, dx, dy, rim_warm, 1, only=side & (YY < oy - 16 * s))
    # collar / hood of the cape bunched around the neck
    col = ellmask(ox, oy - 87 * s, 12.5 * s, 5.5 * s)
    L.put(col, pick(CRIM, 0.45 + 0.25 * smooth(ox - 12 * s, ox + 12 * s, XX)))
    rim(L, col, 0, -1, CRIM[5], 1)
    # helm (back view): rounded, centre ridge, gold neck band, crest fin
    helm = ellmask(ox + 0.5 * s, oy - 99 * s, 9 * s, 10.5 * s) & (YY < oy - 88 * s)
    fin = polymask(P([(-1.6, -106), (-0.4, -116), (1.6, -118), (2.6, -113), (2.2, -106)]))
    hv = 0.18 + 0.28 * smooth(ox + 9 * s, ox - 6 * s, XX) * smooth(oy - 86 * s, oy - 106 * s, YY)
    L.put(helm | fin, pick(STEEL, hv))
    L.put(helm & (np.abs(XX - (ox + 1.2 * s)) < 0.55 * max(1, s)), STEEL[3])
    L.put(helm & (np.abs(YY - (oy - 90 * s)) < 0.8 * max(1, s)), GOLD[2])
    rim(L, helm | fin, dx, dy, rim_warm, 1)
    rim(L, helm | fin, 0, -1, sky_rim, 1)
    return {"cape": cape, "helm": helm, "all": cape | helm | legs | pl | pr | armL | armR | col}


def export(name, layers, keep):
    img = compose(layers)
    arr = np.array(img)
    assert (arr[..., 3] == 255).all(), name
    keep[name] = img
    if BUILD:
        asebuild.build(name, W, H, [L.name for L in layers],
                       [{"ms": 1000, "cels": {L.name: L.image() for L in layers}}], [("p", 0, 0)])
    img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(ART, "previews", f"story_{name}.png"
                                                                  if not name.startswith("story") else f"{name}.png"))


# =========================================================================== STORY 4
def story_4():
    """The Ashbound knight wakes on the cliff: from behind, cape in the wind, the fallen Root on the horizon."""
    rnd = random.Random(4)
    Sky, Far, Mid, Near, FX = (Layer(n) for n in ("Sky", "Far", "Mid", "Near", "FX"))
    HZ = 132                      # horizon
    RX, RY = 238, 118             # the Root's glow centre (root plate)
    # ---- sky: indigo top -> rose -> amber at the horizon glow, clouds lit from below
    t = np.clip(YY / HZ, 0, 1)
    v = 0.03 + 0.55 * t ** 2.1 + 0.34 * radial(RX + 30, HZ - 6, 200, 90) ** 1.6
    v += 0.07 * rays(RX + 10, RY, 13, 0.4, 5) * smooth(0, 110, YY) * (YY < RY + 4)
    cl = fbm(96, 6, 11) * 0.75 + fbm(24, 3, 12) * 0.25
    band = np.sin(YY * 0.19 + fbm(192, 64, 13) * 5)
    cloud = (cl + 0.2 * band - 0.6) > 0
    cloud &= YY < HZ - 6
    v = np.where(cloud, v + 0.07 + 0.1 * radial(RX, HZ, 240, 120), v)
    under = cloud & ~shift(cloud, 0, -1)           # the lower lip of every cloud glows
    v = np.where(under & (YY > 30), v + 0.12, v)
    Sky.put(np.ones((H, W), bool), pick(SKY, v))
    for _ in range(50):                            # stars
        x, y = rnd.uniform(0, W), rnd.uniform(0, 50)
        if v[int(y), int(x)] < 0.12 and not cloud[int(y), int(x)]:
            Sky.dot(x, y, SKY[7] if rnd.random() < 0.8 else SKY[12])
    # ---- the fallen Root on the horizon: upturned root plate + trunk lying right + broken crown
    segs = []
    for i in range(13):
        deg = -10 + i * 16 + rnd.uniform(-5, 5)
        branch_tree(rnd, RX + math.cos(math.radians(deg)) * 9, RY - math.sin(math.radians(deg)) * 9,
                    math.radians(deg), rnd.uniform(26, 40) * (1.0 if 15 < deg < 165 else 0.7), rnd.uniform(3.0, 4.2), 2,
                    rnd.uniform(-0.02, 0.02), segs, spread=(0.25, 0.5), shrink=(0.45, 0.62), step=2.5, twig=False)
    rm, rw, rside = segs_mask(segs)
    halo = np.zeros((H, W), np.float32)
    for k in range(1, 6):
        halo = np.maximum(halo, (shift(rm, k, 0) | shift(rm, -k, 0) | shift(rm, 0, k) | shift(rm, 0, -k)) * (1 - k / 6))
    Sky.put(halo > 0, pick(SKY, v + 0.16 * halo))
    # trunk
    tx0, tx1 = RX + 8, 350
    trunk = np.zeros((H, W), bool)
    tv = np.zeros((H, W), np.float32)
    for x in range(tx0, tx1):
        tt = (x - tx0) / (tx1 - tx0)
        cy, hw = RY + 2 + 14 * tt, 11 * (1 - tt) + 6 * tt
        col = (YY[:, x] >= cy - hw) & (YY[:, x] <= cy + hw)
        trunk[:, x] = col
        dyn = (YY[:, x] - cy) / hw
        groove = np.sin(dyn * 7 + math.sin(x * 0.07) * 1.3)
        tv[:, x] = 0.85 - 0.35 * np.abs(dyn + 0.4) - 0.3 * (dyn > 0.45) - 0.18 * (groove > 0.6)
    Far.put(trunk, pick(GOLD, tv))
    Far.put(trunk & ~shift(trunk, 0, 1), GOLD[6])
    # broken crown: slumped golden foliage beyond the trunk end
    cr = []
    for (x0, y0, deg, ln, w) in ((350, 132, 80, 30, 3.4), (354, 134, 40, 34, 3.2), (356, 136, 120, 24, 2.6),
                                 (360, 138, 15, 30, 2.6)):
        branch_tree(rnd, x0, y0, math.radians(deg), ln, w, 2, -0.03, cr, spread=(0.4, 0.8), grav=0.25, step=2.5,
                    twig=False)
    cm, _, _ = segs_mask(cr)
    leaf = (fbm(8, 5, 71) * 0.7 + fbm(4, 3, 72) * 0.3)
    fol = (radial(372, 124, 42, 20) * 0.9 + leaf * 0.5 - 0.55) > 0.03
    Far.put(fol, pick(GOLD[1:6], 0.3 + 0.5 * radial(372, 118, 42, 22) + 0.3 * (leaf - 0.5)))
    Far.put(cm, GOLD[3])
    # root plate + roots
    plate = ellmask(RX, RY - 10, 13, 15)
    pn = fbm(6, 6, 81)
    ang = np.arctan2(YY - (RY - 10), XX - RX)
    fib = np.sin(ang * 11 + pn * 5)
    pv = 0.75 - 0.4 * (((XX - RX) / 13) ** 2 + ((YY - RY + 10) / 15) ** 2) - 0.25 * (fib > 0.45)
    Far.put(plate, pick(GOLD, pv))
    Far.put(rm & ~plate, pick(GOLD, 0.45 + 0.35 * (rw > 2.2) + 0.2 * (rside < -0.2)))
    core = ellmask(RX + 10, RY + 2, 9, 5) & (trunk | plate)
    Far.put(core, pick(HOT, 0.4 + 0.6 * radial(RX + 10, RY + 2, 9, 5)))
    # ---- far hills/ramparts under the horizon (hazy, glowing toward the Root)
    for (base, amp, sc, seed, vv, towers) in ((HZ + 2, 5, 90, 3, 0.55, True), (HZ + 18, 12, 110, 5, 0.40, False),
                                              (HZ + 40, 16, 90, 8, 0.24, False)):
        rl = ridge(base, amp, sc, seed)
        m = below(rl)
        glow = radial(RX + 20, HZ, 220, 60)
        Mid.put(m, pick(MT, vv - 0.25 * smooth(base, base + 60, YY) + 0.35 * glow * (vv > 0.4)))
        Mid.put(m & ~shift(m, 0, 1), pick(MT, vv + 0.25 + 0.2 * glow))
        if towers:
            for (cx, w, hgt) in ((40, 5, 16), (58, 8, 10), (118, 4, 12), (150, 6, 18), (372, 5, 12)):
                tm = (XX >= cx) & (XX < cx + w) & (YY >= rl[cx] - hgt) & (YY <= rl[cx] + 2)
                tm |= polymask([(cx - 1, rl[cx] - hgt), (cx + w / 2, rl[cx] - hgt - w * 1.6), (cx + w + 1, rl[cx] - hgt)])
                Mid.put(tm, MT[2])
    # valley fog glowing gold near the Root
    fog = (fbm(64, 4, 91) - 0.5 + 0.25 * np.sin(YY * 0.35)) > 0.02
    fog &= (YY > HZ + 6) & (YY < HZ + 60)
    fv = 0.30 + 0.35 * radial(RX + 20, HZ + 10, 200, 50)
    Mid.put(fog & ((fbm(64, 4, 91) - 0.45) * 3 > TH), pick(SKY[3:14], fv))
    # ---- cliff (near): dark faceted rock mass bottom-left, rim-lit
    top = [(0, 184), (30, 186), (60, 189), (92, 192), (120, 194), (146, 195), (160, 197), (170, 201), (174, 206),
           (171, 211), (176, 216), (0, 216)]
    cliff = polymask(top)
    Near.put(cliff, SIL[1])
    # strata: slanted ledges catching a little light
    for k, (y0, x1) in enumerate(((200, 150), (207, 120), (212, 165))):
        Near.put(cliff & (np.abs(YY - (y0 + (XX - 60) * 0.06)) < 0.6) & (XX < x1) & (XX > 10 + k * 20), SIL[3])
    ctop = cliff & ~shift(cliff, 0, 1)
    Near.put(ctop, SIL[5])
    Near.put(shift(ctop, 0, -1) & cliff & (XX % 5 != 0), SIL[3])
    Near.put(edge_toward(cliff, 1, -0.3, 1) & (XX > 150), SKY[11])
    for x in range(2, 168, 2):
        colm = cliff[:, x]
        if colm.any() and rnd.random() < 0.55:
            t0 = int(np.argmax(colm))
            for k in range(rnd.randint(1, 3)):
                Near.dot(x + (k == 2), t0 - 1 - k, SIL[4] if k < 2 else SKY[8])
    # ---- the knight, standing at the lip, cape streaming toward the Root
    Lk = Layer("Knight")
    draw_knight_back(Lk, 118, 195, 1.0, (1, -0.15), SKY[16], CRIM[6], wind=1.0, sky_rim=SKY[9])
    # ---- FX: embers drifting toward the Root on the wind, a little ash
    for _ in range(46):
        x, y = rnd.uniform(0, W), rnd.uniform(40, 190)
        near = math.exp(-((x - RX) ** 2 / 9000 + (y - RY) ** 2 / 2500))
        if rnd.random() > 0.25 + 0.75 * near:
            continue
        c = [GOLD[5], GOLD[6], SKY[15]][rnd.randrange(3)]
        FX.dot(x, y, c)
        if rnd.random() < 0.4:
            FX.dot(x - 1, y + 1, GOLD[3])
    particles(FX, rnd, 26, (0, 60, W, 216), [ASH[3], ASH[4]], avoid=Lk.a)
    return [Sky, Far, Mid, Near, Lk, FX]


# =========================================================================== STORY 1
def great_tree(rnd, TX, top_y, base_y, spread=1.0, seed=0, strands=4, base_w=15, crown_w=9, grav=0.06):
    """Erdtree-like: twisted strand trunk + wide branching crown. Returns (trunk segs, crown segs)."""
    tsegs = []
    for k in range(strands):
        ph = k * 2 * math.pi / strands
        pts = []
        n = 24
        for i in range(n + 1):
            t = i / n
            y = base_y - (base_y - top_y) * t
            r = (base_w - (base_w - crown_w) * t) * 0.55
            x = TX + math.sin(ph + t * 4.2) * r
            pts.append((x, y))
        for i, (a_, b_) in enumerate(zip(pts, pts[1:])):
            w0 = (base_w - (base_w - crown_w) * i / n) * 0.62
            w1 = (base_w - (base_w - crown_w) * (i + 1) / n) * 0.62
            tsegs.append((a_[0], a_[1], b_[0], b_[1], w0, w1))
    csegs = []
    for (deg, ln, w) in ((90, 50, 8), (122, 78, 7), (150, 86, 6), (170, 60, 4.5), (58, 78, 7), (30, 86, 6),
                         (10, 60, 4.5), (104, 64, 6), (76, 64, 6)):
        dd = 90 + (deg - 90) * spread
        branch_tree(rnd, TX + (dd - 90) * 0.06, top_y + 4, math.radians(dd), ln * spread ** 0.5, w, 3,
                    (90 - dd) * 0.0009, csegs, spread=(0.3, 0.55), shrink=(0.58, 0.72), step=3.5, grav=grav)
    return tsegs, csegs


def story_1():
    """The Pale Root, golden and whole, over the kingdom that grew in its light."""
    rnd = random.Random(11)
    Sky, Far, Tree, City, Near, FX = (Layer(n) for n in ("Sky", "Far", "Tree", "City", "Near", "FX"))
    TX = 192
    TOP = 84
    tsegs, csegs = great_tree(rnd, TX, TOP, 188, spread=1.5, strands=5, base_w=34, crown_w=17)
    tm, tw, tside = segs_mask(tsegs)
    cm, cw, cside = segs_mask(csegs)
    leaves = np.zeros((H, W), bool)
    for (x, y) in tips(csegs, 1.6):
        leaves |= ellmask(x, y, rnd.uniform(2.5, 5.5), rnd.uniform(2.0, 4.0))
    leaves &= (fbm(4, 4, 51) > 0.42)
    treeall = tm | cm | leaves
    glow = blur(treeall, 6) * 1.6 + blur(treeall, 16) * 1.2
    CG = (TX, 54)
    # ---- sky: dusk, lit by the tree's own light
    v = 0.05 + 0.2 * (YY / H) + 0.30 * radial(CG[0], CG[1] + 20, 260, 180) ** 1.4 + 0.5 * np.clip(glow, 0, 1)
    v += 0.04 * rays(CG[0], CG[1], 21, 0.0, 5) * smooth(0, 200, YY)
    cl = fbm(128, 8, 21) * 0.7 + fbm(32, 3, 22) * 0.3
    cloud = ((cl + 0.15 * np.sin(YY * 0.15 + fbm(256, 64, 23) * 4) - 0.62) > 0) & (YY > 70)
    v = np.where(cloud, v + 0.05, v)
    Sky.put(np.ones((H, W), bool), pick(SKY, v))
    for _ in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 70)
        if v[int(y), int(x)] < 0.13:
            Sky.dot(x, y, SKY[8])
    # ---- far land
    for (base, amp, sc, seed, vv) in ((160, 6, 120, 31, 0.5), (172, 8, 90, 32, 0.32)):
        rl = ridge(base, amp, sc, seed)
        mm = below(rl)
        Far.put(mm, pick(MT, vv - 0.2 * smooth(base, base + 40, YY) + 0.3 * radial(TX, base, 170, 40)))
        Far.put(mm & ~shift(mm, 0, 1), pick(SKY, 0.5 + 0.4 * radial(TX, base, 170, 40)))
    # ---- the tree
    Tree.put(cm, pick(GOLD, 0.42 + 0.32 * (cside < -0.1) + 0.12 * (cw > 3) + 0.2 * radial(TX, TOP, 90, 70)))
    Tree.put(cm & (cside > 0.5) & (cw > 2.5), GOLD[2])
    Tree.put(leaves & ~cm, pick(GOLD, 0.55 + 0.3 * fbm(3, 3, 52) + 0.25 * radial(TX, 50, 120, 70)))
    Tree.put(tm, pick(GOLD, 0.5 + 0.34 * (tside < -0.15) - 0.25 * (tside > 0.55) - 0.1 * smooth(TOP, 186, YY)))
    Tree.put(tm & (np.abs(tside) < 0.12) & (TH > 0.5), GOLD[6])
    # ---- roots gripping the hill
    rs = []
    for (deg, ln) in ((188, 70), (200, 52), (-8, 70), (-20, 52), (215, 34), (-35, 34)):
        branch_tree(rnd, TX + (-8 if deg > 90 else 8), 184, math.radians(deg), ln, 7, 1, 0.01 * (1 if deg > 90 else -1),
                    rs, spread=(0.3, 0.5), step=3.0, grav=0.3, twig=False)
    rmask, _, rside = segs_mask(rs)
    # ---- the kingdom: two terraces of towers on the hill around the tree's foot
    hill = polymask([(60, 216), (96, 198), (140, 190), (TX, 188), (244, 190), (288, 198), (324, 216)])
    rnd2 = random.Random(7)
    City.put(hill, SIL[2])
    City.put(rmask & hill, pick(GOLD, 0.35 + 0.2 * (rside < 0)))
    windows = []
    for row, (base0, hmin, hmax, body, lit_c, n, x0, x1) in enumerate((
            (188, 12, 30, SIL[4], GOLD[3], 18, 96, 290), (198, 6, 15, SIL[2], GOLD[2], 26, 80, 306))):
        rowm = np.zeros((H, W), bool)
        lit = np.zeros((H, W), bool)
        xs = sorted(rnd2.uniform(x0, x1) for _ in range(n))
        for x in xs:
            dx_ = x - TX
            if abs(dx_) < (22 if row == 0 else 14):
                continue
            base = base0 + abs(dx_) * 0.1
            w = rnd2.choice((4, 5, 6, 7, 9))
            hgt = rnd2.uniform(hmin, hmax) * (1.25 - abs(dx_) / 200)
            b_ = (XX >= x) & (XX < x + w) & (YY >= base - hgt) & (YY <= base + 8)
            kind = rnd2.random()
            if kind < 0.45:
                top_ = polymask([(x - 0.5, base - hgt), (x + w / 2, base - hgt - w * 1.6), (x + w + 0.5, base - hgt)])
            elif kind < 0.65:
                top_ = ellmask(x + w / 2, base - hgt, w / 2 + 0.3, w / 2.2)
            else:
                top_ = ((XX - int(x)) % 2 == 0) & (XX >= x) & (XX < x + w) & (YY >= base - hgt - 2) & (YY < base - hgt)
            rowm |= b_ | top_
            lit |= (b_ | top_) & (np.abs(XX - ((x + w - 1) if dx_ < 0 else x)) < 0.6)
            for k in range(int(hgt // 6)):
                if rnd2.random() < 0.5:
                    windows.append((int(x + w / 2), int(base - hgt + 3 + k * 6), row))
        if row == 0:
            for sx_ in (TX - 42, TX + 34):
                sp = ((XX >= sx_) & (XX < sx_ + 8) & (YY >= 128) & (YY <= 196)) | polymask([(sx_ - 1, 128), (sx_ + 4, 100), (sx_ + 9, 128)])
                rowm |= sp
                lit |= sp & (np.abs(XX - ((sx_ + 7) if sx_ < TX else sx_)) < 0.6)
        City.put(rowm, body)
        City.put(rowm & (YY > 150), pick(SIL, 0.55 - 0.4 * smooth(150, 200, YY)) if row == 0 else body)
        City.put(lit & rowm, lit_c)
        City.put(edge_toward(rowm, 0, -1), GOLD[4] if row == 0 else GOLD[3])
    wall = (YY >= 204) & (XX > 76) & (XX < 308)
    wall |= ((XX - 78) % 6 < 3) & (YY >= 201) & (YY < 204) & (XX > 76) & (XX < 308)
    for tx_ in (80, 134, 250, 304):
        wall |= (XX >= tx_ - 6) & (XX <= tx_ + 6) & (YY >= 192)
        wall |= ((XX - tx_) % 4 < 2) & (np.abs(XX - tx_) <= 6) & (YY >= 189) & (YY < 192)
    City.put(wall, SIL[1])
    City.put(edge_toward(wall, 0, -1), GOLD[2])
    for (x, y, row) in windows:
        City.dot(x, y, GOLD[6] if row == 1 else GOLD[5])
    for x in range(84, 304, 7):
        if rnd2.random() < 0.5:
            City.dot(x, 209, GOLD[5])
    City.put(rmask & ~hill & (YY > 150) & ~City.a, pick(GOLD, 0.5 + 0.25 * (rside < 0)))
    # ---- near framing
    nl = polymask([(0, 180), (24, 184), (52, 196), (74, 208), (86, 216), (0, 216)])
    nr = polymask([(384, 174), (360, 180), (334, 196), (318, 208), (306, 216), (384, 216)])
    Near.put(nl | nr, SIL[1])
    for (x, y, hgt) in ((12, 184, 28), (30, 188, 18), (372, 178, 32), (352, 184, 22), (338, 194, 14)):
        tr = np.zeros((H, W), bool)
        for k in range(5):
            yy = y - hgt + k * hgt / 5
            wdt = 2 + k * 1.5 * hgt / 26
            tr |= polymask([(x, yy - 2), (x + wdt, yy + hgt / 4), (x - wdt, yy + hgt / 4)])
        tr |= (np.abs(XX - x) < 1) & (YY > y - 2) & (YY < y + 4)
        Near.put(tr, SIL[1])
        Near.put(edge_toward(tr, np.sign(TX - x), -0.5), SIL[4])
    Near.put(edge_toward(nl | nr, 0, -1), SIL[4])
    # ---- FX: drifting golden leaves + motes
    for _ in range(80):
        x = rnd.gauss(TX, 100)
        y = rnd.uniform(10, 200)
        if 0 <= x < W:
            c = [GOLD[4], GOLD[5], GOLD[6], GOLD[7]][rnd.randrange(4)]
            FX.dot(x, y, c)
            if rnd.random() < 0.35:
                FX.dot(x + 1, y + 1, GOLD[3])
    return [Sky, Far, Tree, City, Near, FX]


def rot_segs(segs, piv, deg, off=(0, 0)):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def R(x, y):
        x, y = x - piv[0], y - piv[1]
        return piv[0] + x * c - y * s_ + off[0], piv[1] + x * s_ + y * c + off[1]
    out = []
    for sg in segs:
        a_ = R(sg[0], sg[1])
        b_ = R(sg[2], sg[3])
        out.append((a_[0], a_[1], b_[0], b_[1]) + tuple(sg[4:]))
    return out


# =========================================================================== STORY 2
def story_2():
    """The Root falls. Its light tears loose as ash."""
    rnd = random.Random(22)
    Sky, Far, Tree, City, FX, Ash = (Layer(n) for n in ("Sky", "Far", "Tree", "City", "FX", "Ash"))
    TX, BRK = 262, 170                       # trunk axis, break height
    ANG = -36                                # the fall (degrees, top toward the left)
    tsegs, csegs = great_tree(rnd, TX, 70, 200, spread=1.3, strands=5, base_w=30, crown_w=16, grav=0.25)
    upper = [sg for sg in tsegs if max(sg[1], sg[3]) <= BRK + 2]
    stump = [sg for sg in tsegs if min(sg[1], sg[3]) >= BRK - 4]
    upper = rot_segs(upper, (TX, BRK), ANG, (-6, -4))
    crown = rot_segs(csegs, (TX, BRK), ANG, (-6, -4))
    um, uw, uside = segs_mask(upper)
    cm, cw, cside = segs_mask(crown)
    sm, sw_, sside = segs_mask(stump)
    # leaves tearing away as ash: only some tips still hold gold
    leaves = np.zeros((H, W), bool)
    ashl = np.zeros((H, W), bool)
    trails = []
    for (x, y) in tips(crown, 1.6):
        if rnd.random() < 0.4:
            leaves |= ellmask(x, y, rnd.uniform(2.0, 4.0), rnd.uniform(1.8, 3.0))
        elif rnd.random() < 0.5:
            trails.append((x, y))
    leaves &= fbm(4, 4, 61) > 0.45
    ashl &= fbm(3, 3, 62) > 0.5
    treeall = um | cm | sm | leaves
    glow = blur(treeall, 5) * 1.2 + blur(treeall, 14) * 0.9
    BX, BY = TX - 4, BRK - 2                 # the rupture
    # ---- sky: blood-red smoke, the rupture blazing
    v = 0.08 + 0.18 * (YY / H) + 0.55 * radial(BX, BY, 220, 150) ** 1.6 + 0.35 * np.clip(glow, 0, 1)
    v += 0.10 * rays(BX, BY, 15, 0.7, 6) * radial(BX, BY, 300, 220)
    smoke = fbm(64, 24, 71) * 0.7 + fbm(16, 8, 72) * 0.3
    sm_m = (smoke + 0.3 * smooth(140, 20, YY) - 0.66) > 0
    v = np.where(sm_m, v * 0.55 + 0.02, v)
    lip = sm_m & ~shift(sm_m, 0, -1)
    v = np.where(lip, v + 0.12, v)
    Sky.put(np.ones((H, W), bool), pick(BLOOD, v))
    # ---- far burning land
    rl = ridge(176, 6, 100, 81)
    mm = below(rl)
    Far.put(mm, pick(BLOOD, 0.12 + 0.3 * radial(BX, 176, 220, 40) - 0.1 * smooth(176, 216, YY)))
    Far.put(mm & ~shift(mm, 0, 1), BLOOD[5])
    # ---- the tree, falling
    near_r = radial(BX, BY, 260, 200)
    Tree.put(cm, pick(GOLD, 0.18 + 0.22 * (cside < -0.1) + 0.1 * (cw > 3) + 0.35 * near_r))
    Tree.put(cm & (cside > 0.4), GOLD[0])
    for (x, y) in trails:              # leaves tearing loose as ash, streaming on the wind
        n = rnd.randint(4, 12)
        for k in range(n):
            px_ = x + k * 1.6 + rnd.uniform(-0.6, 0.6)
            py_ = y + k * 0.9 + 0.04 * k * k
            if rnd.random() < 0.8:
                Tree.dot(px_, py_, GOLD[3] if k < 2 else ASH[6] if k < 5 else ASH[5] if k < 8 else ASH[4])
    Tree.put(leaves & ~cm, pick(GOLD, 0.3 + 0.25 * fbm(3, 3, 64) + 0.3 * near_r))
    Tree.put(edge_toward(cm | leaves, 1, 1) & (radial(BX, BY, 200, 160) > 0.2), GOLD[5])
    Tree.put(um, pick(GOLD, 0.45 + 0.34 * (uside < -0.15) - 0.25 * (uside > 0.55)))
    Tree.put(sm, pick(GOLD, 0.35 + 0.3 * (sside < -0.15) - 0.25 * (sside > 0.55) - 0.2 * smooth(BRK, 210, YY)))
    # cracks of light running up the falling trunk
    for k in range(5):
        t0 = rnd.uniform(0.05, 0.6)
        pts = []
        x, y = BX + rnd.uniform(-6, 6), BY - 4
        for i in range(12):
            a_ = math.radians(90 - ANG * -1 + 180 * 0) + rnd.uniform(-0.5, 0.5)
            x += math.cos(math.radians(90 + ANG)) * -3.0 * -1 + rnd.uniform(-1.5, 1.5)
            y -= math.sin(math.radians(90 + ANG)) * 3.0
            pts.append((x, y))
        for (x, y) in pts:
            if um[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))]:
                Tree.dot(x, y, HOT[3])
    # the rupture: white-hot core, splinters, rays
    core = ellmask(BX, BY, 14, 8)
    Tree.put(core & (um | sm | ellmask(BX, BY, 9, 5)), pick(HOT, 0.3 + 0.8 * radial(BX, BY, 14, 8)))
    for k in range(22):
        a_ = rnd.uniform(0, 2 * math.pi)
        r0, r1 = rnd.uniform(6, 12), rnd.uniform(16, 44)
        x0, y0 = BX + math.cos(a_) * r0, BY + math.sin(a_) * r0 * 0.7
        x1, y1 = BX + math.cos(a_) * r1, BY + math.sin(a_) * r1 * 0.7
        segm, _, _ = segs_mask([(x0, y0, x1, y1, rnd.uniform(1.0, 2.4), 0.6)])
        FX.put(segm, HOT[rnd.randrange(1, 4)])
    # ---- the kingdom below, burning
    city = np.zeros((H, W), bool)
    rnd2 = random.Random(9)
    fires = []
    for k in range(40):
        x = rnd2.uniform(0, W)
        base = 200 + rnd2.uniform(-4, 4)
        w = rnd2.choice((4, 5, 6, 8))
        hgt = rnd2.uniform(6, 20)
        city |= (XX >= x) & (XX < x + w) & (YY >= base - hgt)
        if rnd2.random() < 0.5:
            city |= polymask([(x - 0.5, base - hgt), (x + w / 2, base - hgt - w * 1.4), (x + w + 0.5, base - hgt)])
        if rnd2.random() < 0.35:
            fires.append((x + w / 2, base - hgt))
    for sx_ in (70, 150, 330):
        city |= (XX >= sx_) & (XX < sx_ + 7) & (YY >= 150)
        city |= polymask([(sx_ - 1, 150), (sx_ + 3.5, 126), (sx_ + 8, 150)])
    # one spire already broken, toppling
    city &= ~(((XX > 149) & (XX < 160)) & (YY < 160 + (XX - 149) * 0.8))
    back = np.zeros((H, W), bool)
    for k in range(30):
        x = rnd2.uniform(0, W)
        w = rnd2.choice((5, 7, 9))
        hgt = rnd2.uniform(14, 32)
        back |= (XX >= x) & (XX < x + w) & (YY >= 196 - hgt)
        if rnd2.random() < 0.5:
            back |= polymask([(x - 0.5, 196 - hgt), (x + w / 2, 196 - hgt - w * 1.5), (x + w + 0.5, 196 - hgt)])
    City.put(back & ~city, BLOOD[2])
    City.put(edge_toward(back, 0, -1) & ~city, BLOOD[4])
    City.put(city, SIL[1])
    near_b = radial(BX, BY, 150, 110) > 0.05
    City.put(edge_toward(city, 1, -0.6) & (XX < BX) & near_b, BLOOD[5])
    City.put(edge_toward(city, -1, -0.6) & (XX > BX) & near_b, BLOOD[5])
    City.put(edge_toward(city, 0, -1), BLOOD[3])
    for (x, y) in fires:
        for k in range(rnd2.randint(3, 7)):
            City.dot(x + rnd2.uniform(-2, 2), y - k * rnd2.uniform(0.8, 1.4), FLAME[min(5, 1 + k // 2 + rnd2.randint(0, 1))])
        City.dot(x, y, FLAME[2])
    # ---- ash rain (wind to the right): far fine flakes, near big dark flakes; embers round the rupture
    for _ in range(220):
        x, y = rnd.uniform(-20, W), rnd.uniform(-10, H)
        c = ASH[rnd.choice((4, 5, 5, 6))]
        Ash.dot(x, y, c)
        if rnd.random() < 0.5:
            Ash.dot(x - 1, y - 2, ASH[3])
    for _ in range(26):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        for (a_, b_) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            Ash.dot(x + a_, y + b_, ASH[2] if (a_ + b_) else ASH[4])
    for _ in range(80):
        x, y = rnd.gauss(BX, 60), rnd.gauss(BY - 30, 45)
        Ash.dot(x, y, [FLAME[3], FLAME[4], GOLD[6]][rnd.randrange(3)])
    return [Sky, Far, Tree, City, FX, Ash]


# =========================================================================== figures (side view)
def figure(pose, ox, oy, s=1.0, face=1, seed=0, horn=False, cloak=True):
    """Hollowed knight silhouette from capsules. Returns (body mask, cloak mask, helm centre, sword segs).
    pose: stand | slump | kneel | fallen. face=+1 looks right, -1 left. oy = floor."""
    f = face

    def P(x, y):
        return (ox + x * s * f, oy + y * s)
    rnd = random.Random(seed)
    J = {}
    if pose == "stand":        # hunched, head hanging, broken blade trailing
        J = dict(hd=(5, -50), nk=(3, -44), hip=(-1, -26), kn1=(2, -13), ft1=(3, 0), kn2=(-3, -13), ft2=(-5, 0),
                 sh=(2, -42), el=(6, -31), hd_=(8, -22), sw=((8, -22), (17, 2)))
    elif pose == "slump":      # seated against a wall, legs out, head on chest
        J = dict(hd=(4, -26), nk=(1, -24), hip=(-2, -6), kn1=(9, -10), ft1=(17, 0), kn2=(10, -6), ft2=(19, 0),
                 sh=(0, -22), el=(5, -12), hd_=(9, -4), sw=((-6, -30), (4, 0)))
    elif pose == "kneel":      # one knee down, sword planted, head bowed
        J = dict(hd=(6, -36), nk=(3, -31), hip=(-1, -16), kn1=(9, -12), ft1=(10, 0), kn2=(-2, -1), ft2=(-10, 0),
                 sh=(3, -29), el=(9, -22), hd_=(13, -20), sw=((13, -22), (14, 0)))
    elif pose == "fallen":     # lying face down
        J = dict(hd=(22, -4), nk=(17, -5), hip=(0, -4), kn1=(-10, -4), ft1=(-20, -2), kn2=(-9, -2), ft2=(-19, 0),
                 sh=(14, -6), el=(20, -2), hd_=(26, -1), sw=((28, -1), (44, -2)))
    segs = []

    def cap(a, b, w0, w1=None):
        A, B = P(*J[a]) if isinstance(a, str) else P(*a), P(*J[b]) if isinstance(b, str) else P(*b)
        segs.append((A[0], A[1], B[0], B[1], w0 * s, (w1 or w0) * s))
    cap("hip", "kn2", 5.0, 4.4)
    cap("kn2", "ft2", 4.2, 3.6)
    cap("nk", "hip", 10.0, 8.0)
    cap("hip", "kn1", 5.0, 4.4)
    cap("kn1", "ft1", 4.2, 3.6)
    cap("sh", "el", 4.0, 3.6)
    cap("el", "hd_", 3.6, 3.2)
    body, _, _ = segs_mask(segs)
    armm, _, _ = segs_mask(segs[-2:])
    hx, hy = P(*J["hd"])
    hdx, hdy = J["hd"]
    helm = polymask([P(hdx - 4.5, hdy - 3.5), P(hdx - 3, hdy - 6), P(hdx + 3.5, hdy - 6), P(hdx + 5, hdy - 3.5),
                     P(hdx + 5.2, hdy + 4.5), P(hdx - 4.5, hdy + 5)])
    body |= helm
    if horn:     # a broken crest, swept back
        body |= polymask([P(hdx - 1, hdy - 5), P(hdx - 7, hdy - 10), P(hdx - 9, hdy - 8), P(hdx - 3, hdy - 4)])
    J["visor"] = (P(hdx + 1, hdy - 0.5), P(hdx + 5.2, hdy - 0.5))
    # pauldron
    px_, py_ = P(*J["sh"])
    paul = ellmask(px_, py_ - 1 * s, 5.0 * s, 3.6 * s)
    body |= paul
    armm |= paul
    # sword (broken on standing ones)
    (a0, a1) = J["sw"]
    A, B = P(*a0), P(*a1)
    if pose == "stand":
        B = (A[0] + (B[0] - A[0]) * 0.7, A[1] + (B[1] - A[1]) * 0.7)
    sw, _, _ = segs_mask([(A[0], A[1], B[0], B[1], 2.4 * s, 1.6 * s)])
    gA = (A[0] - 2.5 * s, A[1] + 1.5 * s * f)
    # tattered cloak hanging from the shoulders on the back side
    cl = np.zeros((H, W), bool)
    if cloak and pose != "fallen":
        nx, ny = P(*J["nk"])
        hx2, hy2 = P(*J["hip"])
        back = -f
        pts = [(nx + back * 1 * s, ny), (nx + back * 7 * s, ny + 3 * s)]
        low = max(hy2 + 10 * s, oy - 3 * s) if pose != "slump" else oy
        n = 6
        for i in range(n + 1):
            t = i / n
            x = nx + back * (8 + 2 * t) * s - back * t * 12 * s
            y = low - (rnd.uniform(0, 5) if i % 2 else 0) * s
            pts.append((x, y))
        pts.append((hx2 + f * 2 * s, hy2))
        cl = polymask(pts)
    return body, cl, (hx, hy, J["visor"], armm, helm), sw


def paint_figure(L, body, cl, sw, light, warm_rim, cold_rim, base=None, cloak_c=None):
    base = COLD[1] if base is None else base
    L.put(cl & ~body, COLD[2] if cloak_c is None else cloak_c)
    L.put(body, base)
    L.put(sw, COLD[4])
    allm = body | cl | sw
    lx, ly = light
    rim(L, allm, lx, ly, warm_rim, 1)
    rim(L, allm, 0, -1, cold_rim, 1)
    return allm


# =========================================================================== STORY 3
def story_3():
    """The hollowed keep their vigil in the ruins; one shrine flame still burns."""
    rnd = random.Random(33)
    Sky, Ruin, Floor, Figs, FX = (Layer(n) for n in ("Sky", "Ruin", "Floor", "Figures", "FX"))
    FXX, FXY = 176, 150                       # flame
    light = radial(FXX, FXY, 150, 90)
    # ---- night sky through the ruin; the fallen Root a thin dim gold line on the far horizon
    v = 0.16 + 0.42 * smooth(10, 140, YY) + 0.14 * radial(96, 128, 120, 50)
    Sky.put(np.ones((H, W), bool), pick(COLD, v))
    cl = (fbm(96, 10, 101) - 0.55 + 0.2 * np.sin(YY * 0.12)) > 0
    Sky.put(cl & (YY < 116), pick(COLD, v + 0.12))
    Sky.put(cl & ~shift(cl, 0, 1) & (YY < 116), COLD[6])
    for _ in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 90)
        Sky.dot(x, y, COLD[6] if rnd.random() < 0.8 else PALE[3])
    hz = ridge(132, 3, 80, 102)
    far = below(hz)
    Sky.put(far, pick(COLD, 0.35 - 0.2 * smooth(132, 170, YY)))
    # (framed by the broken arch)
    rootl = (np.abs(YY - (129 + (XX - 72) * 0.05)) < 0.5 + 1.0 * smooth(130, 74, XX)) & (XX > 72) & (XX < 130)
    Sky.put(blur(rootl, 4) > 0.05, COLD[5])
    Sky.put(rootl, GOLD[2])
    Sky.put(rootl & (YY < 129 + (XX - 72) * 0.05), GOLD[3])
    for k in range(7):
        a_ = math.radians(50 + k * 14)
        seg, _, _ = segs_mask([(73, 128, 73 + math.cos(a_) * rnd.uniform(4, 8), 128 - math.sin(a_) * rnd.uniform(4, 8), 1.0)])
        Sky.put(seg, GOLD[2])
    # ---- ruins: great broken arch (left), a gothic window wall (right), columns
    ruin = np.zeros((H, W), bool)
    ruin |= (XX >= 16) & (XX <= 44) & (YY >= 30)                      # left pier
    ruin |= polymask([(16, 30), (20, 22), (26, 26), (34, 18), (44, 24), (44, 30)])
    # arch ring from the pier, broken off mid-span
    ring = (np.hypot(XX - 118, YY - 110) < 84) & (np.hypot(XX - 118, YY - 110) > 70) & (YY < 110) & (XX > 30) & (XX < 150)
    ring &= ~((XX > 128) & (YY > 30 + (XX - 128) * 1.1))
    ruin |= ring
    # right: wall with a tall lancet window, tracery
    wall = (XX >= 300) & (YY >= 40)
    wall |= polymask([(300, 40), (312, 32), (322, 38), (336, 28), (350, 36), (366, 24), (384, 30), (384, 40)])
    win = ((XX >= 326) & (XX <= 350) & (YY >= 70) & (YY <= 150)) | ellmask(338, 70, 12, 22) & (YY < 70)
    wall &= ~win
    wall |= (np.abs(XX - 338) < 1) & win
    wall |= (np.abs(YY - 96) < 1) & win
    ruin |= wall
    # a toppled column drum + standing column stumps
    ruin |= (XX >= 268) & (XX <= 282) & (YY >= 108)
    ruin |= polymask([(268, 108), (272, 102), (278, 106), (282, 100), (282, 108)])
    ruin |= (XX >= 86) & (XX <= 96) & (YY >= 140)
    ruv = 0.3 + 0.1 * np.sin(XX * 0.9) * 0 + 0.25 * light
    Ruin.put(ruin, pick(COLD, 0.14 - 0.06 * smooth(40, 200, YY)))
    # masonry courses (subtle)
    course = ruin & ((YY % 9 == 0) | (((XX + (YY // 9) * 7) % 16 == 0) & (YY % 9 != 0)))
    Ruin.put(course & ~ring, COLD[0])
    Ruin.put(edge_toward(ruin, 0, -1), COLD[5])
    Ruin.put(edge_toward(ruin, -1, 0) & (XX < 150), COLD[3])
    Ruin.put(edge_toward(ruin, 1, 0) & (light > 0.2) & (XX < FXX), WARM[4])
    Ruin.put(edge_toward(ruin, -1, 0) & (light > 0.2) & (XX > FXX), WARM[4])
    Ruin.put(ruin & (light > 0.35 + 0.3 * TH), WARM[2])
    # moonlight through the window: pale shaft on the floor
    shaft = polymask([(326, 150), (350, 150), (318, 216), (270, 216)])
    # ---- floor: flagstones in perspective, warm pool around the shrine
    fl = YY >= 168
    fv = 0.18 + 0.1 * smooth(168, 216, YY)
    rows = np.floor(np.log(np.maximum(YY - 160, 1)) * 5)
    joint = fl & ((np.abs(YY - np.round(160 + np.exp(rows / 5))) < 0.6) |
                  ((np.round((XX - 192) / np.maximum(YY - 150, 1) * 8) % 3 == 0) & (np.abs(((XX - 192) / np.maximum(YY - 150, 1) * 8) % 3) < 0.25)))
    cold = pick(COLD, fv)
    warm = pick(WARM, 0.15 + 0.85 * light)
    usew = light > 0.08 + 0.12 * TH
    Floor.put(fl, np.where(usew[..., None], warm, cold))
    Floor.put(fl & joint, np.where(usew[..., None], pick(WARM, 0.1 + 0.6 * light), COLD[1]))
    Floor.put(shaft & fl & (TH < 0.3) & ~usew, COLD[4])
    # rubble
    for k in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(172, 214)
        r = rnd.uniform(1.5, 4.5) * (y - 150) / 60
        m = ellmask(x, y, r * 1.3, r)
        Floor.put(m, WARM[2] if light[int(min(y, H - 1)), int(min(x, W - 1))] > 0.15 else COLD[2])
        Floor.put(edge_toward(m, 0, -1), WARM[6] if light[int(min(y, H - 1)), int(min(x, W - 1))] > 0.2 else COLD[5])
    # ---- the shrine: stone plinth, iron bowl, the flame
    plinth = (XX >= FXX - 9) & (XX <= FXX + 9) & (YY >= FXY + 10) & (YY <= 176)
    plinth |= (XX >= FXX - 11) & (XX <= FXX + 11) & (YY >= 172) & (YY <= 178)
    plinth |= (XX >= FXX - 4) & (XX <= FXX + 4) & (YY >= FXY + 4) & (YY < FXY + 10)
    bowl = ellmask(FXX, FXY + 3, 8, 3.2) & (YY >= FXY + 2)
    Floor.put(plinth, pick(WARM, 0.35 + 0.3 * smooth(FXX + 10, FXX - 10, XX) * 0 + 0.25 * smooth(178, FXY, YY)))
    Floor.put(edge_toward(plinth, 0, -1), WARM[7])
    Floor.put(bowl, WARM[2])
    Floor.put(edge_toward(bowl, 0, -1), WARM[8])
    flame_m = np.zeros((H, W), bool)
    fvv = np.zeros((H, W), np.float32)
    for y in range(FXY - 16, FXY + 3):
        t = (FXY + 2 - y) / 18
        hw = 5.2 * (1 - t) ** 0.8 * (1 + 0.25 * (t < 0.25))
        cx = FXX + math.sin(t * 5) * 1.4 * t
        row = np.abs(XX[y] + .5 - cx) <= hw
        flame_m[y] = row
        fvv[y] = 1 - np.abs(XX[y] + .5 - cx) / max(hw, 0.5) * 0.6 - t * 0.5
    FX.put(flame_m, pick(FLAME, fvv))
    for k in range(18):                       # embers rising
        FX.dot(FXX + rnd.gauss(0, 5), FXY - 18 - rnd.uniform(0, 50), FLAME[rnd.choice((2, 3, 3, 4))])
    # ---- the hollowed
    figs = [
        ("slump", 56, 196, 1.15, 1, 1, False),      # against the left pier
        ("kneel", 214, 184, 1.05, -1, 2, False),    # before the flame
        ("stand", 256, 190, 1.2, -1, 3, True),      # hunched, broken blade
        ("fallen", 110, 206, 1.1, 1, 4, False),     # face down in the foreground
        ("stand", 312, 176, 0.62, -1, 5, False),    # far, in the moon shaft
        ("stand", 336, 172, 0.52, -1, 6, True),
    ]
    for (pose, x, y, sc, fc, seed, horn) in figs:
        body, clk, hd, sw = figure(pose, x, y, sc, fc, seed, horn)
        dl = 1 if x < FXX else -1
        far = sc < 0.8
        paint_figure(Figs, body, clk, sw, (dl, -0.3), COLD[4] if far else WARM[7], COLD[5],
                     base=COLD[3] if far else COLD[1], cloak_c=COLD[3] if far else COLD[2])
        (v0, v1) = hd[2]
        if not far:
            inner = hd[3] & ~edge_toward(hd[3], -dl, 0)
            Figs.put(inner & ~edge_toward(body, dl, -0.3), COLD[2])
            Figs.put(edge_toward(hd[3], 0, -1) & ~edge_toward(body, dl, -0.3), COLD[4])
            Figs.put(hd[4] & ~edge_toward(body, dl, -0.3) & ~edge_toward(body, 0, -1), COLD[2])
        vs, _, _ = segs_mask([(v0[0], v0[1], v1[0], v1[1], 1.0)])
        Figs.put(vs & body, COLD[0])
        if not far and pose in ("stand", "kneel"):
            Figs.dot(v1[0] - fc * 1.5, v1[1], WARM[8])       # a last ember behind the visor
            Figs.dot(v1[0] - fc * 2.5, v1[1], WARM[6])
    # ---- low fog + slow ash
    fog = ((fbm(96, 6, 111) - 0.5 + 0.3 * np.sin(YY * 0.4)) * 2.5 > TH) & (YY > 150) & (YY < 190)
    FX.put(fog & ~Figs.a & ((XX + YY) % 2 == 0), COLD[4])
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        FX.dot(x, y, ASH[rnd.choice((3, 4, 5))])
    return [Sky, Ruin, Floor, Figs, FX]


# =========================================================================== ENDING: KINDLE
def story_end_kindle():
    """The knight takes the root throne. The tree drinks his cinders and burns gold again."""
    rnd = random.Random(55)
    Sky, Tree, Throne, Knight, Roots, FX = (Layer(n) for n in ("Sky", "Tree", "Throne", "Knight", "Roots", "FX"))
    CX = 192
    # ---- the tree: colossal trunk behind the throne, crown spreading over the whole sky
    tsegs, csegs = great_tree(rnd, CX, 30, 200, spread=1.9, strands=6, base_w=64, crown_w=40, grav=0.1)
    tm, tw, tside = segs_mask(tsegs)
    cm, cw, cside = segs_mask(csegs)
    leaves = np.zeros((H, W), bool)
    for (x, y) in tips(csegs, 1.8):
        leaves |= ellmask(x, y, rnd.uniform(2.5, 5.0), rnd.uniform(2.0, 3.5))
    leaves &= fbm(4, 4, 151) > 0.4
    glow = blur(tm | cm | leaves, 8) * 1.2 + blur(tm, 24) * 1.4
    # ---- sky: the pale sky above the clouds, washed with gold near the tree
    v = 0.22 + 0.55 * smooth(0, 170, YY) + 0.3 * np.clip(glow, 0, 1)
    v += 0.08 * rays(CX, 90, 23, 0.3, 6)
    Sky.put(np.ones((H, W), bool), pick_flat(SKYP, v + (TH - 0.5) * 0.06))
    goldwash = np.clip(glow, 0, 1) > 0.45 + 0.3 * TH
    Sky.put(goldwash, pick(GOLD, 0.55 + 0.4 * np.clip(glow - 0.45, 0, 1)))
    # sea of cloud far below
    cs = (fbm(48, 6, 152) * 0.7 + fbm(12, 3, 153) * 0.3 + smooth(150, 200, YY) * 0.6 - 0.72) > 0
    cs &= YY > 140
    Sky.put(cs, pick(SKYP, 0.55 + 0.35 * smooth(216, 150, YY) + 0.2 * radial(CX, 180, 200, 50)))
    Sky.put(cs & ~shift(cs, 0, 1), SKYP[8])
    # ---- tree paint (luminous white-gold)
    Tree.put(cm, pick(GOLD, 0.5 + 0.3 * (cside < -0.1) + 0.15 * (cw > 3)))
    Tree.put(leaves & ~cm, pick(GOLD, 0.7 + 0.3 * fbm(3, 3, 154)))
    Tree.put(tm, pick(GOLD, 0.62 + 0.3 * (tside < -0.15) - 0.28 * (tside > 0.5) - 0.2 * smooth(60, 200, YY) * (np.abs(XX - CX) > 20)))
    # sap veins climbing the trunk, blazing
    for k in range(7):
        x = CX + rnd.uniform(-26, 26)
        pts = []
        for y in range(196, 20, -3):
            x += rnd.uniform(-1.4, 1.4)
            pts.append((x, y))
        for i, (a_, b_) in enumerate(zip(pts, pts[1:])):
            sg, _, _ = segs_mask([(a_[0], a_[1], b_[0], b_[1], 1.0)])
            Tree.put(sg & tm, HOT[3] if i % 3 else HOT[2])
    # ---- the throne: a high pointed back of woven roots, darker than the blazing trunk behind it
    back = polymask(bez((CX - 40, 186), (CX - 42, 120), (CX - 26, 70), (CX, 50), 20) +
                    bez((CX, 50), (CX + 26, 70), (CX + 42, 120), (CX + 40, 186), 20))
    s1 = np.sin((XX - CX) * 0.42 + YY * 0.30 + np.sin(YY * 0.1) * 0.8)
    s2 = np.sin((XX - CX) * -0.42 + YY * 0.30 + np.sin(YY * 0.1 + 1) * 0.8)
    strand = np.maximum(s1, s2)
    Throne.put(back, pick(GOLD, 0.12 + 0.22 * (strand > 0.3) + 0.12 * (strand > 0.8) + 0.12 * smooth(186, 60, YY)))
    Throne.put(back & (strand > 0.3) & ~shift(back & (strand > 0.3), 0, 1), GOLD[1])
    Throne.put(edge_toward(back, 0, -1) | edge_toward(back, -1, 0) & (XX < CX) | edge_toward(back, 1, 0) & (XX > CX), GOLD[7])
    # arm-rests + seat
    arms = ((np.abs(XX - (CX - 40)) <= 8) | (np.abs(XX - (CX + 40)) <= 8)) & (YY >= 150) & (YY <= 196)
    arms |= ellmask(CX - 40, 150, 9, 5) | ellmask(CX + 40, 150, 9, 5)
    Throne.put(arms, pick(GOLD, 0.28 + 0.22 * smooth(196, 146, YY)))
    Throne.put(edge_toward(arms, 0, -1), GOLD[6])
    seat = (np.abs(XX - CX) <= 32) & (YY >= 160) & (YY <= 196)
    Throne.put(seat, pick(GOLD, 0.2 + 0.1 * smooth(196, 160, YY)))
    Throne.put(seat & (YY == 160), GOLD[5])
    # root-floor of the summit: a lens of roots with the cloud-sea beyond
    gr = ellmask(CX, 222, 180, 30)
    gv = 0.2 + 0.25 * radial(CX, 200, 140, 16) + 0.15 * (np.sin(XX * 0.3 + np.sin(YY * 0.9) * 2) > 0.6)
    Throne.put(gr, pick(GOLD, gv))
    Throne.put(gr & ~shift(gr, 0, 1), GOLD[6])
    fr = []
    for k in range(10):
        deg = 180 + 8 + k * (164 / 9)
        branch_tree(rnd, CX + math.cos(math.radians(deg)) * 30, 196, math.radians(deg), rnd.uniform(40, 120), 3.2, 1,
                    0.0, fr, spread=(0.2, 0.4), step=3.0, twig=False, grav=0.0)
    fm_, _, fside = segs_mask([(a_, b_ * 0.35 + 196 * 0.65, c_, d_ * 0.35 + 196 * 0.65, *r_) for (a_, b_, c_, d_, *r_) in fr])
    Throne.put(fm_ & gr, pick(GOLD, 0.45 + 0.3 * (fside < 0)))
    # ---- the knight, seated (front view), backlit: dark with a gold rim; the visor ember fading
    SY = 6                                   # seated offset
    cape = polymask([(CX - 16, 116 + SY), (CX - 28, 136 + SY), (CX - 31, 190), (CX - 22, 196), (CX + 22, 196),
                     (CX + 31, 190), (CX + 28, 136 + SY), (CX + 16, 116 + SY)])
    Knight.put(cape, pick(CRIM, 0.32 + 0.2 * np.abs(np.sin((XX - CX) * 0.35))))
    Knight.put(edge_toward(cape, -1, 0) & (XX < CX), CRIM[6])
    Knight.put(edge_toward(cape, 1, 0) & (XX > CX), CRIM[6])
    torso = polymask([(CX - 11, 116 + SY), (CX + 11, 116 + SY), (CX + 9, 142 + SY), (CX - 9, 142 + SY)])
    pl = ellmask(CX - 13, 118 + SY, 9, 6.5)
    pr = ellmask(CX + 13, 118 + SY, 9, 6.5)
    armL, _, _ = segs_mask([(CX - 17, 122 + SY, CX - 17, 138 + SY, 6, 5), (CX - 17, 138 + SY, CX - 3, 146 + SY, 5, 4.5)])
    armR, _, _ = segs_mask([(CX + 17, 122 + SY, CX + 17, 138 + SY, 6, 5), (CX + 17, 138 + SY, CX + 3, 146 + SY, 5, 4.5)])
    knees = ellmask(CX - 12, 160, 7.5, 6) | ellmask(CX + 12, 160, 7.5, 6)
    lap = polymask([(CX - 10, 146 + SY), (CX + 10, 146 + SY), (CX + 19, 158), (CX - 19, 158)])
    shins, _, _ = segs_mask([(CX - 13, 162, CX - 15, 190, 7.5, 6), (CX + 13, 162, CX + 15, 190, 7.5, 6)])
    feet = ellmask(CX - 16, 192, 5.5, 3) | ellmask(CX + 16, 192, 5.5, 3)
    helm = ellmask(CX, 103 + SY, 8.5, 10)
    fin = polymask([(CX - 1.5, 95 + SY), (CX, 84 + SY), (CX + 1.5, 95 + SY)])
    body = torso | pl | pr | armL | armR | knees | lap | shins | feet | helm | fin
    Knight.put(body, STEEL[1])
    Knight.put(pl | pr | helm, STEEL[2])
    Knight.put(knees & (YY < 158), STEEL[3])
    Knight.put(edge_toward(body, 0, -1), GOLD[6])
    Knight.put(edge_toward(body, -1, 0) & (XX < CX), GOLD[5])
    Knight.put(edge_toward(body, 1, 0) & (XX > CX), GOLD[5])
    # sword planted between the knees, hands resting on the pommel
    sw, _, sd = segs_mask([(CX, 150 + SY, CX, 195, 3.4, 1.4)])
    Knight.put(sw, STEEL[2])
    Knight.put(sw & (sd < -0.2), GOLD[5])
    Knight.put((np.abs(YY - (154 + SY)) < 1.2) & (np.abs(XX - CX) <= 7), GOLD[3])
    hands = ellmask(CX, 147 + SY, 5.5, 3.2)
    Knight.put(hands, STEEL[2])
    Knight.put(edge_toward(hands, 0, -1), GOLD[5])
    # the visor: its crimson ember turning gold as he gives his light to the tree
    for x in range(CX - 5, CX + 6):
        Knight.dot(x, 103 + SY, CRIM[5] if abs(x - CX) > 2 else GOLD[6])
    Knight.dot(CX, 103 + SY, HOT[3])
    # ---- roots rising over him: he is becoming part of the tree
    vr = []
    for (x0, deg, ln, w) in ((CX - 22, 80, 40, 2.4), (CX + 22, 100, 40, 2.4), (CX - 12, 92, 22, 1.8), (CX + 12, 88, 22, 1.8),
                             (CX - 44, 70, 50, 2.2), (CX + 44, 110, 50, 2.2)):
        branch_tree(rnd, x0, 196, math.radians(deg), ln, w, 1, (90 - deg) * 0.004, vr, spread=(0.4, 0.7), step=2.5,
                    twig=True, wmin=1.0)
    vm, vw, vside = segs_mask(vr)
    Roots.put(vm, pick(GOLD, 0.55 + 0.3 * (vside < 0)))
    Roots.put(vm & (vside < -0.4), GOLD[7])
    # ---- petals + motes drifting down, rising sparks off the trunk
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        c = [PALE[4], PALE[5], GOLD[6], GOLD[7]][rnd.randrange(4)]
        FX.dot(x, y, c)
        if rnd.random() < 0.3:
            FX.dot(x + 1, y, PALE[3])
    return [Sky, Tree, Throne, Knight, Roots, FX]


# =========================================================================== ENDING: ASH
def walker_back(L, ox, oy, s, stride, light, warm, cape_c=CRIM):
    """small knight walking away (back view, 3/4 toward the right), mid-stride."""
    def P(pts):
        return [(ox + x * s, oy + y * s) for x, y in pts]
    legA = polymask(P([(-7, -40), (-1, -40), (-2 + stride, -20), (-2 + stride * 1.4, 0), (-8 + stride * 1.4, 0),
                       (-7 + stride, -20)]))
    legB = polymask(P([(1, -40), (7, -40), (7 - stride * 0.6, -20), (8 - stride, -4), (2 - stride, -5),
                       (2 - stride * 0.6, -20)]))
    body = polymask(P([(-9, -40), (-10, -62), (-7, -70), (7, -70), (10, -62), (9, -40)]))
    pl = ellmask(ox - 10 * s, oy - 66 * s, 6 * s, 4.5 * s)
    pr = ellmask(ox + 10 * s, oy - 66 * s, 6 * s, 4.5 * s)
    helm = ellmask(ox, oy - 76 * s, 6.5 * s, 7.5 * s)
    fin = polymask(P([(-1, -82), (0.5, -90), (2, -82)]))
    cape = polymask(P([(-7, -71), (-11, -56), (-14, -30), (-16, -18), (-10, -21), (-5, -15), (1, -20), (6, -13), (11, -19),
                       (17, -14), (15, -34), (11, -58), (7, -71)]))
    sw, _, _ = segs_mask([(ox + 12 * s, oy - 44 * s, ox + 22 * s, oy - 18 * s, 2.0 * s, 1.0)])
    allm = legA | legB | body | pl | pr | helm | fin | cape | sw
    L.put(legA | legB, STEEL[2])
    L.put(legB & ~legA, STEEL[1])
    L.put(body | pl | pr | helm | fin, STEEL[1])
    L.put(sw, STEEL[2])
    L.put(cape, pick(cape_c, 0.3 + 0.18 * (np.sin((XX - ox) * 0.9 / max(s, 0.5)) > 0.3)))
    rim(L, allm, light[0], light[1], warm, 1)
    rim(L, allm, 0, -1, STEEL[4], 1)
    return allm


def story_end_ash():
    """Dawn. The last gold of the Root fades; the knight walks on, and green breaks through the ash."""
    rnd = random.Random(66)
    Sky, Far, Plain, Walker, Near, FX = (Layer(n) for n in ("Sky", "Far", "Plain", "Walker", "Near", "FX"))
    HZ = 128
    SX_, SY_ = 300, HZ + 2                    # the sun, just clearing the horizon
    # ---- dawn sky: slate -> rose -> pale gold at the sun
    v = 0.12 + 0.62 * smooth(-10, HZ, YY) ** 1.3 + 0.3 * radial(SX_, SY_, 200, 70) ** 1.5
    v += 0.04 * rays(SX_, SY_, 15, 1.0, 5) * (YY < HZ)
    cl = (fbm(128, 6, 201) * 0.7 + fbm(32, 3, 202) * 0.3 + 0.15 * np.sin(YY * 0.2) - 0.64) > 0
    cl &= (YY > 30) & (YY < HZ - 10)
    v = np.where(cl, v - 0.08, v)
    lip = cl & ~shift(cl, 0, -1)
    v = np.where(lip, v + 0.18 * (1 + radial(SX_, SY_, 220, 90)), v)
    Sky.put(np.ones((H, W), bool), pick(DAWN, v))
    sun = ellmask(SX_, SY_, 9, 9) & (YY < HZ + 1)
    Sky.put(sun, DAWN[11])
    Sky.put(edge_toward(sun, 0, -1), DAWN[10])
    # ---- the dead Root on the far left horizon: grey now, its last gold rising away as motes
    RX, RY = 70, HZ - 6
    segs = []
    for i in range(10):
        deg = 10 + i * 17 + rnd.uniform(-5, 5)
        branch_tree(rnd, RX + math.cos(math.radians(deg)) * 5, RY - math.sin(math.radians(deg)) * 5,
                    math.radians(deg), rnd.uniform(14, 24), rnd.uniform(1.8, 2.6), 2, 0.0, segs, spread=(0.3, 0.5),
                    shrink=(0.45, 0.6), step=2.0, twig=False)
    rm, _, rside = segs_mask(segs)
    trunk = polymask([(RX, RY - 5), (RX + 4, RY - 6), (190, HZ - 1), (190, HZ + 2), (RX, RY + 5)])
    dead = rm | trunk | ellmask(RX, RY - 1, 7, 8)
    Far.put(dead, pick(ASH, 0.36 + 0.18 * (rside < 0)))
    Far.put(edge_toward(dead, 1, 0), ASH[6])
    for k in range(5):             # a few last glints of gold in the grey
        x, y = rnd.uniform(RX - 4, RX + 30), rnd.uniform(RY - 14, RY + 2)
        if dead[int(y), int(x)]:
            Far.dot(x, y, GOLD[5])
    for k in range(34):            # the last light rising off it, fading as it climbs
        t = rnd.random()
        x = RX + rnd.gauss(10, 18) + t * 30
        y = RY - 6 - t * 90
        c = GOLD[6] if t < 0.25 else GOLD[5] if t < 0.5 else GOLD[3] if t < 0.75 else DAWN[8]
        FX.dot(x, y, c)
    # ---- far ridges + the ash plain (soft dunes, lit from the sun)
    rl = ridge(HZ, 2, 60, 203)
    fr = below(rl)
    Plain.put(fr, pick(DAWN, 0.45 - 0.25 * smooth(HZ, HZ + 12, YY) + 0.2 * radial(SX_, HZ, 160, 12)))
    dunes = np.zeros((H, W), np.float32)
    for (base, amp, sc, seed) in ((HZ + 12, 3, 90, 204), (HZ + 30, 5, 110, 205), (HZ + 56, 7, 120, 206)):
        r_ = ridge(base, amp, sc, seed)
        dunes += below(r_)
    pv = 0.25 + 0.12 * dunes + 0.25 * smooth(HZ + 70, HZ, YY) + 0.25 * radial(SX_, HZ + 10, 220, 50)
    plain = YY >= HZ + 5
    Plain.put(plain, pick(ASH, pv))
    for (base, amp, sc, seed) in ((HZ + 12, 3, 90, 204), (HZ + 30, 5, 110, 205), (HZ + 56, 7, 120, 206)):
        r_ = ridge(base, amp, sc, seed)
        crest = below(r_) & ~shift(below(r_), 0, 1)
        Plain.put(crest & plain, pick(ASH, 0.62 + 0.3 * radial(SX_, HZ, 260, 60)))
    # sun path glinting across the ash toward the viewer
    path = polymask([(SX_ - 4, HZ + 5), (SX_ + 4, HZ + 5), (262, 216), (206, 216)])
    # ---- the knight walking toward the sun; a long shadow falls back toward us
    WX, WY = 266, 166
    shadow = polymask([(WX - 3, WY), (WX + 4, WY), (WX - 44, 216), (WX - 66, 216)])
    Plain.put(shadow & plain, pick(ASH, pv - 0.18))
    # footprints leading from the foreground
    for k in range(9):
        t = k / 9
        x = 196 + (WX - 196) * t + (4 if k % 2 else -4) * (1 - t)
        y = 216 - (216 - WY) * t
        Plain.put(ellmask(x, y, 2.2 * (1 - t * 0.6), 1.0), ASH[2])
    walker_back(Walker, WX, WY, 0.62, 3.0, (1, -0.3), DAWN[10])
    # ---- foreground: ash dune, green shoots breaking through
    fg = below(ridge(196, 8, 140, 207))
    Near.put(fg, pick(ASH, 0.3 + 0.2 * smooth(230, 190, YY) + 0.15 * radial(SX_, 190, 300, 40)))
    Near.put(fg & ~shift(fg, 0, 1), ASH[6])
    for k in range(26):
        x = rnd.uniform(4, W - 4)
        col = fg[:, int(x)]
        if not col.any():
            continue
        top = int(np.argmax(col)) + rnd.randint(1, 10)
        hgt = rnd.randint(2, 7) if rnd.random() < 0.8 else rnd.randint(8, 12)
        for i in range(hgt):
            Near.dot(x + (i > hgt // 2) * (1 if k % 2 else 0), top - i, GREEN[1 + min(3, i * 4 // hgt)])
        if hgt >= 4:             # a pair of leaves
            Near.dot(x - 1, top - hgt + 2, GREEN[3])
            Near.dot(x - 2, top - hgt + 1, GREEN[4])
            Near.dot(x + 1, top - hgt + 3, GREEN[3])
            Near.dot(x + 2, top - hgt + 2, GREEN[5])
        Near.dot(x, top - hgt, GREEN[5])
    # a larger sapling at the lower left, catching the dawn
    sp = []
    branch_tree(rnd, 48, 212, math.radians(84), 22, 2.2, 1, 0.01, sp, spread=(0.5, 0.8), step=2.5, twig=False)
    spm, _, sps = segs_mask(sp)
    Near.put(spm, pick(GREEN, 0.3 + 0.3 * (sps < 0)))
    for (x, y) in tips(sp, 2.0):
        lf = ellmask(x + 1.5, y, 3.2, 1.6)
        Near.put(lf, GREEN[3])
        Near.put(edge_toward(lf, 1, -1), GREEN[5])
    # ---- drifting ash, lit pale by the dawn
    for _ in range(60):
        FX.dot(rnd.uniform(0, W), rnd.uniform(0, H), ASH[rnd.choice((5, 6, 7))])
    return [Sky, Far, Plain, Walker, Near, FX]


PANELS = {"story_1": story_1, "story_2": story_2, "story_3": story_3, "story_4": story_4,
          "story_end_kindle": story_end_kindle, "story_end_ash": story_end_ash}


def preview(imgs):
    sc = 2
    names = list(imgs)
    cols = 2
    rows = (len(names) + 1) // 2
    sheet = Image.new("RGBA", (cols * (W * sc + 8) + 8, rows * (H * sc + 22) + 8), (30, 30, 36, 255))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x = 8 + (i % cols) * (W * sc + 8)
        y = 8 + (i // cols) * (H * sc + 22)
        d.text((x, y), n, fill=(230, 230, 235, 255))
        sheet.alpha_composite(imgs[n].resize((W * sc, H * sc), Image.NEAREST), (x, y + 14))
    sheet.save(os.path.join(ART, "previews", "story.png"))


def main():
    keep = {}
    for n, fn in PANELS.items():
        if ONLY and n not in ONLY:
            continue
        export(n, fn(), keep)
    if not ONLY:
        preview(keep)


if __name__ == "__main__":
    main()
