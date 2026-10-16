"""Painting kit for the Cold Forge environment art (gen_forge_env.py). Grown from the approved concept kit
(art/concepts/forge/moodlib.py): paint in float RGB with a coverage mask, light additively, then reduce to the forge
palette with a light ordered dither and a hard alpha, so every sheet is real pixel art in one palette.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

FORGE = [
    "#030405", "#06080b", "#0a0d12", "#0e1219", "#131822", "#18202b", "#1e2734", "#252f3e", "#2d3849", "#364356",
    "#415066", "#4f6079", "#62748f", "#7c8ea8",                    # slate / iron, cold blue-grey
    "#0b0a0b", "#141213", "#1d1a1b", "#272324",                    # soot (warm black)
    "#2a1a14", "#3d2419", "#5a311c", "#7c401d", "#a3531f", "#c96a22", "#e88a30", "#f7ad4c", "#ffd27e", "#fff0c4",
    "#3a3328", "#5c5040", "#857560",                               # warm-lit stone / dust
    "#8f9aa8", "#b7c0cb", "#dfe4ea",                               # pale ash light (threshold)
    "#141c22", "#1d2a31", "#2b3c45",                               # still black water / steam
    "#1c1718", "#2a2121", "#3a2b26", "#4e3829", "#664530",         # warm-lit slate/iron (where the coals reach)
    "#a5afbc", "#c9d0d9", "#eef1f4", "#6b7686", "#566273",         # threshold stone, lighter steps
]
PAL = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in FORGE], dtype=np.float32)
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0 - 0.47


def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


def hh(x, y, k=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + k * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


class Cv:
    """A paint canvas: float RGB + coverage (0/1). Everything painted becomes opaque unless cover=False."""

    def __init__(self, w, h, base=None):
        self.w, self.h = w, h
        self.c = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), bool)
        if base:
            self.c += hexc(base); self.a[:] = True
        yy, xx = np.mgrid[0:h, 0:w]
        self.yy, self.xx = yy.astype(np.float32), xx.astype(np.float32)

    # masks
    def poly(self, pts):
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        return np.array(m) > 127

    def rectm(self, x0, y0, x1, y1):
        m = np.zeros((self.h, self.w), bool)
        m[max(0, int(round(y0))):max(0, int(round(y1))), max(0, int(round(x0))):max(0, int(round(x1)))] = True
        return m

    def ellm(self, cx, cy, rx, ry):
        return ((self.xx + .5 - cx) / rx) ** 2 + ((self.yy + .5 - cy) / ry) ** 2 <= 1.0

    # fills
    def fill(self, mask, col, a=1.0, cover=True):
        c = hexc(col) if isinstance(col, str) else np.asarray(col, np.float32)
        self.c[mask] = self.c[mask] * (1 - a) + c * a
        if cover:
            self.a |= mask

    def vgrad(self, mask, top, bot, y0=0, y1=None, gamma=1.0):
        y1 = self.h if y1 is None else y1
        t = np.clip((self.yy - y0) / max(1, (y1 - y0)), 0, 1) ** gamma
        c = hexc(top)[None, None, :] * (1 - t[..., None]) + hexc(bot)[None, None, :] * t[..., None]
        self.c[mask] = c[mask]; self.a |= mask

    def add_light(self, field, col, strength=1.0, mask=None):
        f = field * strength
        if mask is not None:
            f = f * mask
        self.c += f[..., None] * hexc(col)[None, None, :]

    def mul(self, field, mask=None):
        if mask is not None:
            field = np.where(mask, field, 1.0)
        self.c *= np.asarray(field, np.float32)[..., None] if np.ndim(field) else field

    def glow(self, cx, cy, r, col, strength=1.0, power=2.0, mask=None):
        d = np.sqrt((self.xx + .5 - cx) ** 2 + (self.yy + .5 - cy) ** 2) / r
        self.add_light(np.clip(1 - d, 0, 1) ** power, col, strength, mask)

    def eglow(self, cx, cy, rx, ry, col, strength=1.0, power=2.0, mask=None):
        d = np.sqrt(((self.xx + .5 - cx) / rx) ** 2 + ((self.yy + .5 - cy) / ry) ** 2)
        self.add_light(np.clip(1 - d, 0, 1) ** power, col, strength, mask)

    def shaft(self, top0, top1, bot0, bot1, y0, y1, col, strength=1.0, soft=6.0, fade=1.0, mask=None):
        t = np.clip((self.yy - y0) / max(1, y1 - y0), 0, 1)
        l = top0 + (bot0 - top0) * t
        r = top1 + (bot1 - top1) * t
        d = np.abs(self.xx + .5 - (l + r) / 2) - (r - l) / 2
        f = np.clip(1 - d / soft, 0, 1) * (1 - t * fade) * ((self.yy >= y0) & (self.yy <= y1))
        self.add_light(f, col, strength, mask)
        return f

    def noise2(self, sx, sy, seed=0, octaves=3, wrap=False):
        """Value noise with cell sizes sx, sy; wrap=True tiles horizontally across the canvas width."""
        rng = np.random.default_rng(seed)
        out = np.zeros((self.h, self.w), np.float32)
        amp, tot = 1.0, 0.0
        for o in range(octaves):
            ax, ay = sx / (2 ** o), sy / (2 ** o)
            gw = max(1, int(round(self.w / ax))) if wrap else int(self.w / ax) + 3
            gh = int(self.h / ay) + 3
            ax = self.w / gw if wrap else ax
            g = rng.random((gh, gw + 1)).astype(np.float32)
            if wrap:
                g[:, gw] = g[:, 0]
            gy = self.yy / ay; gx = self.xx / ax
            y0 = np.floor(gy).astype(int); x0 = np.floor(gx).astype(int)
            fy = gy - y0; fx = gx - x0
            fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
            x1 = x0 + 1
            if wrap:
                x0 = x0 % gw; x1 = x1 % (gw + 1)
            v = (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy + g[y0 + 1, x1] * fx * fy)
            out += v * amp; tot += amp; amp *= 0.5
        return out / tot

    def px(self, x, y, col, a=1.0, cover=True):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y, x] = self.c[y, x] * (1 - a) + hexc(col) * a
            if cover:
                self.a[y, x] = True

    def line(self, a, b, col, a_=1.0):
        x0, y0 = int(round(a[0])), int(round(a[1])); x1, y1 = int(round(b[0])), int(round(b[1]))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, col, a_)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def rect(self, x0, y0, x1, y1, col, a=1.0):
        self.fill(self.rectm(x0, y0, x1, y1), col, a)

    def edge_dark(self, mask, col="#06080b"):
        """1px dark rim on the outer edge of mask (the game's sel-out outline)."""
        m = mask
        e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        self.fill(e, col)

    def to_image(self, dither=0.35, alpha=True):
        c = np.clip(self.c, 0, 255)
        if dither:
            th = np.tile(BAYER4, (self.h // 4 + 1, self.w // 4 + 1))[:self.h, :self.w]
            c = c + th[..., None] * dither * 18.0
        flat = c.reshape(-1, 3)
        wv = np.array([0.9, 1.2, 0.8], np.float32)
        out = np.zeros((flat.shape[0], 3), np.float32)
        for i in range(0, flat.shape[0], 65536):
            ch = flat[i:i + 65536]
            d = (((ch[:, None, :] - PAL[None, :, :]) * wv) ** 2).sum(-1)
            out[i:i + 65536] = PAL[d.argmin(1)]
        rgb = out.reshape(self.h, self.w, 3).astype(np.uint8)
        a = (self.a if alpha else np.ones_like(self.a)).astype(np.uint8) * 255
        return Image.fromarray(np.dstack([rgb, a]), "RGBA")


# ------------------------------------------------------------------ shared painters
def bricks(p, mask, bw=16, bh=8, cols=("#18202b", "#1e2734", "#252f3e"), mortar="#0a0d12", seed=0, ox=0, oy=0,
           soot=0.0, lip=1.18, wrap=False):
    yy, xx = p.yy + oy, p.xx + ox
    row = np.floor(yy / bh).astype(int)
    shift = (row % 2) * (bw // 2)
    col = np.floor((xx + shift) / bw).astype(int)
    if wrap:
        col = col % max(1, p.w // bw)
    lx = (xx + shift) % bw
    ly = yy % bh
    ids = (row * 7919 + col * 104729 + seed * 31) % 9973
    tone = (ids * 2654435761 % 1000) / 1000.0
    pal = [hexc(c) for c in cols]
    out = np.zeros(p.c.shape, np.float32)
    for i, c in enumerate(pal):
        sel = (tone >= i / len(pal)) & (tone < (i + 1) / len(pal))
        out[sel] = c
    mort = (ly < 1) | (lx < 1)
    out[mort] = hexc(mortar)
    lp = (ly == 1) & ~(lx < 1)
    out[lp] = out[lp] * lip + 4
    chip = ((lx < 2) & (ly < 2)) & ((ids % 3) == 0)
    out[chip] = hexc(mortar)
    if soot:
        n = p.noise2(10, 70, seed + 5, 3, wrap=wrap)
        streak = np.clip((n - 0.42) * 2.6, 0, 1) * soot
        out = out * (1 - streak[..., None] * 0.7)
    p.c[mask] = out[mask]; p.a |= mask


def plates(p, mask, pw=22, ph=16, cols=("#0e1219", "#131822", "#10151d"), seam="#05070a", lit="#252f3e", seed=0, ox=0, oy=0):
    yy, xx = p.yy + oy, p.xx + ox
    row = np.floor(yy / ph).astype(int)
    shift = (row % 2) * (pw // 2)
    col = np.floor((xx + shift) / pw).astype(int)
    lx = (xx + shift) % pw; ly = yy % ph
    ids = (row * 7919 + col * 104729 + seed * 31) % 9973
    tone = (ids * 2654435761 % 1000) / 1000.0
    out = np.zeros(p.c.shape, np.float32)
    for i, c in enumerate(cols):
        sel = (tone >= i / len(cols)) & (tone < (i + 1) / len(cols))
        out[sel] = hexc(c)
    out[(ly < 1) | (lx < 1)] = hexc(seam)
    out[(ly == 1) & (lx >= 1)] = hexc(lit)
    out[(ly == 3) & ((lx % 5) == 3)] = hexc(lit)
    p.c[mask] = out[mask]; p.a |= mask


def chain(p, top, bot, col="#1e2734", hi="#364356", sway=0.0):
    n = int(abs(bot[1] - top[1]))
    for i in range(n):
        t = i / max(1, n)
        x = top[0] + (bot[0] - top[0]) * t + math.sin(t * math.pi) * sway
        y = top[1] + i
        if i % 3 == 0:
            p.px(x - 1, y, col); p.px(x + 1, y, col); p.px(x, y, hi)
        else:
            p.px(x, y, col)


def hung_blade(p, x, y, ln, w, tilt, cols, glint=None, broken=False):
    post_c, rail_c, blade_c, edge_c, dark_c = cols
    d = (math.sin(math.radians(tilt)), math.cos(math.radians(tilt)))
    tang = (x + d[0] * 2, y + d[1] * 2)
    p.line((x, y), tang, post_c)
    gx = tang
    p.line((gx[0] - w - 1, gx[1]), (gx[0] + w + 1, gx[1]), rail_c)
    L = ln * (0.55 if broken else 1.0)
    n = max(3, int(L))
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        ww = w * (1 if t < 0.72 or broken else (1 - (t - 0.72) / 0.28))
        c = (gx[0] + d[0] * (1 + L * t), gx[1] + d[1] * (1 + L * t))
        left.append((c[0] - ww, c[1])); right.append((c[0] + ww + 0.99, c[1]))
    m = p.poly(left + list(reversed(right)))
    p.fill(m, blade_c)
    for a in left[:-1]:
        p.px(a[0], a[1], edge_c)
    for b in right[1:]:
        p.px(b[0] - 1, b[1], dark_c)
    if broken:
        e = left[-1]
        p.px(e[0] + 1, e[1], dark_c); p.px(e[0] + 2, e[1] + 1, edge_c)
    if glint:
        q = left[int(len(left) * 0.3)]
        p.px(q[0], q[1], glint)


def blade_rack(p, x0, x1, y_top, y_bot, scale=1.0, cols=("#131822", "#252f3e", "#2d3849", "#415066", "#0e1219"),
               glint="#7c8ea8", seed=0, fill=0.85, posts=True, rows=2):
    hgt = (y_bot - y_top) / rows
    step = max(3, int(3.2 * scale))
    for r in range(rows):
        r0, r1 = y_top + hgt * r, y_top + hgt * (r + 1)
        p.fill(p.rectm(x0, r0, x1, r0 + max(1, int(scale))), cols[1])
        p.fill(p.rectm(x0, r0, x1, r0 + 1), cols[3])
        x = x0 + 3
        while x < x1 - 3:
            if hh(x, r0, seed) < fill:
                ln = (r1 - r0 - 5 * scale) * (0.6 + 0.4 * hh(x, r0, seed + 1))
                w = 0 if scale < 1.3 else (1 if scale < 2.2 else 1.5)
                hung_blade(p, x, r0 + 1, ln, w, (hh(x, r0, seed + 4) - 0.5) * 6, cols,
                           glint if hh(x, r0, seed + 2) > 0.75 else None, broken=hh(x, r0, seed + 5) > 0.82)
            x += step + (1 if hh(x, r1, seed + 3) > 0.6 else 0)
    if posts:
        pw = max(2, int(2 * scale))
        for x in (x0, x1 - pw):
            p.fill(p.rectm(x, y_top - 4 * scale, x + pw, y_bot + 2), cols[0])
            p.fill(p.rectm(x, y_top - 4 * scale, x + 1, y_bot + 2), cols[1])


def iron_band(p, x0, x1, y, h=5):
    p.fill(p.rectm(x0, y, x1, y + h), "#0e1219")
    p.fill(p.rectm(x0, y, x1, y + 1), "#252f3e")
    p.fill(p.rectm(x0, y + h - 1, x1, y + h), "#06080b")
    for x in range(int(x0) + 3, int(x1), 10):
        p.px(x, y + 2, "#364356"); p.px(x, y + 3, "#06080b")
