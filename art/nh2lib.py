"""NEO-HALLOW art upgrade (docs/v17/neohallow_upgrade.md): shared 1x pixel painter, palette and city pieces.

Everything here draws crisp at 1x on float RGB numpy arrays (H x W x 3) with a bool alpha. `Px` wraps horizontally
when `wrap=True` (tileable parallax layers): every shape is drawn at x - W, x and x + W.

  Px(w, h, wrap)          canvas: rect, px, hline, vline, poly, blend, glowrect, line
  tower(px, T, rng, ...)  a skyscraper with floors of lit windows that cluster in offices, a lit edge, crown, mast,
                          optional neon band / vertical glyph sign / holo board; returns the points the fx light up
  glyph_panel(...)        an abstract neon sign (no letters, no brands): stacked glyph strokes in a frame
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bgv2lib import hexc, lerp, smooth  # noqa: E402

B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float)


def colr(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, float)


# ---------------------------------------------------------------- the NEO-HALLOW palette (World 2 "Neon Megacity" family)
NIGHT = ['04040c', '06071a', '0a0a20', '0e0c28', '130f30', '191238', '211540', '2a1848', '351c50', '421f58', '52245e', '622a64',
         '74306a', '88386f', '9e4274']                      # sky, top to the rose-magenta city glow at the horizon
TEAL = ['0a1424', '0e2032', '132c42', '1a3a52', '234a62', '2e5c72']   # the cyan district's haze (left)
CLOUD = ['0d0b20', '14112a', '1c1634', '241b3e', '2e2148', '3a2752', '4a2d5c', '5e3466', '763c70', '8e4678']
GHOST = ['1a1434', '20183c', '271c44', '2f214c', '382654', '432b5c']   # the farthest towers, dissolved in rain-haze
DARK = ['06060f', '090914', '0c0b1a', '100e21', '141128', '19152f', '1e1a37', '25203f']   # near facades
STEEL = ['1c2030', '262c40', '323a52', '404a66', '56627e', '74809c', '9aa6c0']
AMBER = ['3a2414', '5a3818', '7a4e20', '9c6428', 'c0803a', 'e0a050', 'ffc878', 'ffe6b8']
CYAN = ['06202e', '0b4d66', '13a3c9', '3fe0ff', 'b8f6ff', 'f2feff']
MAG = ['2a0624', '6e0f5c', 'c21d97', 'ff3fc0', 'ff9fe2', 'fff0fb']
RED = ['3a0610', '8a0f22', 'e0223f', 'ff6a7e']
NEONS = {'c': CYAN, 'm': MAG, 'a': AMBER[3:], 'r': RED}


class Px:
    def __init__(self, w, h, wrap=True, base=None, alpha=False):
        self.w, self.h, self.wrap = w, h, wrap
        self.rgb = np.zeros((h, w, 3)) if base is None else np.array(base, float).copy()
        self.a = np.zeros((h, w), bool) if alpha else None

    def _xs(self, x):
        return (x - self.w, x, x + self.w) if self.wrap else (x,)

    def px(self, x, y, c, k=1.0):
        x, y = int(round(x)), int(round(y))
        if not 0 <= y < self.h: return
        if self.wrap: x %= self.w
        if not 0 <= x < self.w: return
        self.rgb[y, x] = self.rgb[y, x] * (1 - k) + colr(c) * k
        if self.a is not None and k >= 0.5: self.a[y, x] = True

    def rect(self, x, y, w, h, c, k=1.0, solid=True):
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        y0, y1 = max(0, y), min(self.h, y + h)
        if y1 <= y0 or w <= 0: return
        col = colr(c)
        for ox in self._xs(x):
            x0, x1 = max(0, ox), min(self.w, ox + w)
            if x1 <= x0: continue
            self.rgb[y0:y1, x0:x1] = self.rgb[y0:y1, x0:x1] * (1 - k) + col * k
            if self.a is not None and solid and k >= 0.5: self.a[y0:y1, x0:x1] = True

    def hline(self, x, y, w, c, k=1.0): self.rect(x, y, w, 1, c, k)
    def vline(self, x, y, h, c, k=1.0): self.rect(x, y, 1, h, c, k)

    def mask_poly(self, pts):
        m = Image.new('L', (self.w, self.h), 0); d = ImageDraw.Draw(m)
        for dx in ((-self.w, 0, self.w) if self.wrap else (0,)):
            d.polygon([(x + dx, y) for x, y in pts], fill=255)
        return np.asarray(m) > 127

    def fill_mask(self, m, c, k=1.0, solid=True):
        col = colr(c) if not (isinstance(c, np.ndarray) and c.ndim == 3) else c
        mm = m[..., None] * k
        self.rgb = self.rgb * (1 - mm) + col * mm
        if self.a is not None and solid: self.a |= m

    def line(self, x0, y0, x1, y1, c, k=1.0):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for i in range(n + 1):
            self.px(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c, k)

    def glow(self, cx, cy, rx, ry, c, k=0.3, p=2.0, mask=None):
        """additive soft glow (pre-palette only: it makes gradients)"""
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        dx = xx - cx
        if self.wrap: dx = (dx + self.w / 2) % self.w - self.w / 2
        d = np.sqrt((dx / rx) ** 2 + ((yy - cy) / ry) ** 2)
        g = np.clip(1 - d, 0, 1) ** p * k
        if mask is not None: g = g * mask
        self.rgb = np.clip(self.rgb + g[..., None] * colr(c), 0, 255)

    def dither_k(self, x, y, k):
        return (B4[int(y) & 3, int(x) & 3] + 0.5) / 16 < k


def ramp(r, v):
    """colour from a ramp (list of hex) at v in 0..1"""
    return r[int(np.clip(v, 0, 0.999) * len(r))]


def glyph_panel(px, x, y, w, h, neon, seed, frame=None, lit=1.0, vertical=True, back='0c0a1a'):
    """An abstract neon sign: a 1 px frame and stacked glyph strokes (made-up script, no letters). Returns centre."""
    c1, c2, c3 = neon[2], neon[3], neon[4]
    rng = np.random.default_rng(seed)
    px.rect(x, y, w, h, back)
    if lit <= 0:
        px.rect(x, y, w, 1, neon[1]); px.rect(x, y + h - 1, w, 1, neon[1]); px.rect(x, y, 1, h, neon[1]); px.rect(x + w - 1, y, 1, h, neon[1])
        return x + w / 2, y + h / 2
    px.rect(x, y, w, 1, c2); px.rect(x, y + h - 1, w, 1, c2); px.rect(x, y, 1, h, c1); px.rect(x + w - 1, y, 1, h, c1)
    if vertical:
        gy = y + 2
        while gy < y + h - 3:
            gh = int(rng.integers(2, 5))
            if gy + gh > y + h - 2: break
            pat = rng.integers(0, 6)
            for yy in range(gh):
                for xx in range(1, w - 1):
                    on = {0: xx in (1, w - 2) or yy == 0, 1: yy in (0, gh - 1), 2: xx == w // 2 or yy == gh // 2,
                          3: (xx + yy) % 2 == 0, 4: xx < w - 2 and yy != 1, 5: xx == 1 or yy == gh - 1}[int(pat)]
                    if on and x + xx < x + w - 1: px.px(x + xx, gy + yy, c3 if (xx + yy + seed) % 5 == 0 else c2)
            gy += gh + 1
    else:
        gx = x + 2
        while gx < x + w - 3:
            gw = int(rng.integers(2, 5))
            if gx + gw > x + w - 2: break
            pat = rng.integers(0, 5)
            for xx in range(gw):
                for yy in range(1, h - 1):
                    on = {0: yy in (1, h - 2) or xx == 0, 1: xx in (0, gw - 1), 2: yy == h // 2 or xx == gw // 2, 3: (xx + yy) % 2 == 0,
                          4: yy == 1 or xx == gw - 1}[int(pat)]
                    if on: px.px(gx + xx, y + yy, c3 if (xx + yy + seed) % 5 == 0 else c2)
            gx += gw + 1
    return x + w / 2, y + h / 2


def tower(px, T, rng, wincols, body, edge=None, floor_h=3, win_w=1, win_gap=1, lit=0.35, haze=None, haze_top=None,
          crown=True, mast=True, scale=1.0, dim=1.0):
    """A skyscraper (crisp 1x). T: dict(x, w, top, kind, bot=px.h, setbacks=[(dy, inset)], band=neon key, sign=...)
    body: ramp (dark, top..bottom shading); wincols: [(hex, weight)]; edge: (neon ramp, side -1/1) lit edge.
    Returns dict(blink=[(x, y)], signs=[(x, y, w, h)])."""
    x, w, top, kind = T['x'], T['w'], T['top'], T.get('kind', 0)
    bot = T.get('bot', px.h)
    out = dict(blink=[], signs=[])
    # silhouette: a stack of setbacks
    segs = [(top, x, w)]
    for dy, ins in T.get('setbacks', []):
        segs.append((top + dy, x - ins, w + 2 * ins))
    segs.sort()
    tm = np.zeros((px.h, px.w), bool)
    for i, (yy, xx, ww) in enumerate(segs):
        y1 = segs[i + 1][0] if i + 1 < len(segs) else bot
        px.rect(xx, yy, ww, y1 - yy, body[2])
        for ox in px._xs(int(round(xx))):
            tm[max(0, int(yy)):max(0, int(y1)), max(0, ox):max(0, min(px.w, ox + int(round(ww))))] = True
        # vertical shading: darker at the bottom (no street light reaches far up into the fog)
        for r in range(int(yy), int(y1)):
            t = (r - top) / max(1, bot - top)
            c = ramp(body, 0.85 - 0.7 * t)
            px.rect(xx, r, ww, 1, c)
        # the shadow side (right third) a step darker
        px.rect(xx + ww - max(1, ww // 4), yy, max(1, ww // 4), y1 - yy, body[0], 0.45)
        # a 1 px rim on the roof edge of each setback (sky light)
        px.rect(xx, yy, ww, 1, body[-1], 0.8)
        # panel seams: faint vertical lines
        for sx in range(int(xx) + 3, int(xx + ww) - 1, max(4, int(6 * scale))):
            px.rect(sx, yy + 1, 1, y1 - yy - 1, body[0], 0.25)
    # crown
    if crown:
        if kind == 1:      # gabled / stepped crown
            for i in range(3):
                px.rect(x + 1 + i * 2, top - 2 - i * 2, w - 2 - i * 4, 2, body[-2])
        elif kind == 2:    # a spire
            for i in range(int(w * 0.8)):
                ww = max(1, int(w * 0.35 * (1 - i / (w * 0.8))))
                px.rect(x + w / 2 - ww / 2, top - i, ww, 1, body[-2] if i % 7 else body[-1])
        elif kind == 3:    # a crown ring (a neon halo deck)
            px.rect(x - 2, top - 3, w + 4, 2, body[-1]); px.rect(x - 2, top - 1, w + 4, 1, body[1])
    # windows: floors; offices cluster (noise over floor x column-group); a few floors fully dark or fully lit
    nfl = int((bot - top - 6) / floor_h)
    cw = win_w + win_gap
    gx0 = x + 2 if w > 6 else x + 1
    for f in range(nfl):
        fy = top + 4 + f * floor_h
        if fy >= bot - 2: break
        depth = (fy - top) / max(1, bot - top)
        mode = rng.random()
        fl_lit = lit * (0.35 if mode < 0.25 else 1.8 if mode > 0.93 else 1.0)
        # the edge of each setback this floor belongs to
        xx, ww = x, w
        for yy, sx, sw in segs:
            if fy >= yy: xx, ww = sx, sw
        ncol = int((ww - 3) / cw)
        grp = rng.random(max(1, ncol // 3 + 1))
        for c in range(ncol):
            wx = xx + 2 + c * cw
            if wx + win_w > xx + ww - 1: break
            p = fl_lit * (0.4 + 1.2 * grp[c // 3])
            if rng.random() < p:
                cols, wts = zip(*wincols); col = cols[rng.choice(len(cols), p=np.array(wts) / sum(wts))]
                k = dim * (0.95 - 0.55 * depth)
                px.rect(wx, fy, win_w, 1, col, k)
            elif rng.random() < 0.15:
                px.rect(wx, fy, win_w, 1, body[-2], 0.6)
    # the lit edge (neon reflection up the corner)
    if edge:
        ram, side = edge
        ex = x if side < 0 else x + w - 1
        for r in range(int(top), int(bot)):
            t = (r - top) / max(1, bot - top)
            if t < 0.95: px.px(ex, r, ram[2] if t > 0.55 else ram[1], 0.35 + 0.5 * t)
    # a neon band around the crown
    if T.get('band'):
        ram = NEONS[T['band']]; yb = top + T.get('band_y', 2)
        px.rect(x, yb, w, 1, ram[3]); px.rect(x, yb + 1, w, 1, ram[2], 0.6)
    # mast + aviation light
    if mast and T.get('mast', True):
        mx = int(round(x + w * T.get('mast_at', 0.5))); mh = T.get('mast_h', int(6 + w * 0.3))
        mt = top - (int(w * 0.8) if kind == 2 else 4 if kind == 1 else 3 if kind == 3 else 0)
        px.rect(mx, mt - mh, 1, mh, body[-1])
        if mh > 8: px.rect(mx - 1, mt - mh + 4, 3, 1, body[-2])
        out['blink'].append((mx, mt - mh - 1))
    # haze toward the street fog: ordered dither toward `haze` colour, strongest at the bottom
    if haze is not None:
        y0 = haze_top if haze_top is not None else bot - 40
        yy, xx = np.mgrid[0:px.h, 0:px.w]
        k = np.clip((yy - y0) / max(1, bot - y0), 0, 1) * 0.7
        m = tm & ((B4[yy & 3, xx & 3] + 0.5) / 16 < k)
        px.rgb[m] = px.rgb[m] * 0.5 + colr(haze) * 0.5
    out['mask'] = tm
    return out
