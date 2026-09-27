"""Drawing kit for agent SB's Expansion 3 art (art/gen_xsb.py): masks + ordered-dither shading + a 1px dark outline.

Every shape is a boolean mask painted with a ramp; the value per pixel comes from a light function (key light from the
upper left, like the rest of the game's props), picked through the 4x4 Bayer matrix so gradients read as hand-dithered.
"""
import math
from PIL import Image, ImageDraw
from envlib import ramp, pick, clamp, h01, bt

K = (8, 7, 12, 255)
T = (0, 0, 0, 0)

# ---- palettes (matched to the region tilesets: necropolis bone/ghost-blue on blue-black stone; dunes sand/gold/lapis)
NST = ramp("07070b", "0d0d14", "13131d", "1a1a27", "222232", "2b2b3e", "36354b", "44425c", "56536f", "6e6a86")   # necropolis stone
BONE = ramp("1c1915", "2e2922", "4a4236", "6f6550", "978a6c", "bcae8c", "ddd2b2", "f1ead4")
GHOST = ramp("0b1732", "142c58", "22498a", "3a70c0", "63a0e6", "a2cdf8", "e4f3ff")
IRON = ramp("0a0a0e", "15151c", "22222c", "33333f", "4b4b58", "6c6c7a", "9898a4")
RUST = ramp("140c0a", "281612", "3e2218", "5a3220", "7a4a2c")
PURP = ramp("0e0714", "1c0d27", "2d1640", "43225c", "5e347a", "7a4c98")
WOOD = ramp("100c0a", "1d1612", "2d231b", "3f3226", "564433", "6e5a44")
HIDE = ramp("2a1c14", "4a3222", "6e4c34", "94704c", "b8966a")
SAND = ramp("2a1809", "3f250e", "573413", "704518", "8a581f", "a86f2a", "c68c3c", "dcaa58", "f0c878")
SSTONE = ramp("1e140c", "33230f", "4d3517", "6a4a20", "8a642c", "a88040", "c8a060", "e0c088")   # sun-baked sandstone
GOLD = ramp("3a2208", "6a4210", "a06818", "d09a2a", "f2c84a", "fff0a0")
LAPIS = ramp("0a1024", "142450", "203e80", "3462aa", "6292d0")
LINEN = ramp("241c14", "3e3224", "5c4c36", "7c6a4c", "a08c68", "c6b28a", "e2d4b0")
PALM = ramp("0c1408", "16240e", "243a14", "34521c", "4a6e26", "668c34", "86a848")
TRUNK = ramp("1a1008", "2e1e10", "46301a", "604428", "7c5a36", "98744a")
CLAY = ramp("241008", "3e1c0e", "5e2c14", "82401e", "a4582a", "c4763c", "dc9656")
AMBER = ramp("6a2a04", "b25a0c", "f0901c", "ffc04a", "fff0b0", "fffcf0")


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), T)
        self.px = self.im.load()

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return T

    # ---- masks
    def mask(self):
        return Image.new("L", (self.w, self.h), 0)

    def paint(self, m, rmp, val, over=True, alpha=255):
        """paint mask m with ramp rmp; val(x, y, info) -> 0..1 (None = skip)"""
        mp = m.load()
        bb = m.getbbox()
        if not bb:
            return
        for y in range(bb[1], bb[3]):
            for x in range(bb[0], bb[2]):
                if mp[x, y]:
                    v = val(x, y) if callable(val) else val
                    if v is None:
                        continue
                    c = pick(rmp, v, x, y)
                    if alpha < 255:
                        c = (c[0], c[1], c[2], alpha)
                    if over or self.px[x, y][3] == 0:
                        self.px[x, y] = c

    def outline(self, col=K, inner=False):
        """1px dark outline around the opaque silhouette (outside), and optionally an inner rim darken"""
        src = self.im.copy().load()
        for y in range(self.h):
            for x in range(self.w):
                if src[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h and src[xx, yy][3] > 200:
                        self.px[x, y] = col
                        break
        return self

    def paste(self, other, ox, oy):
        self.im.alpha_composite(other.im if isinstance(other, Canvas) else other, (int(ox), int(oy)))
        self.px = self.im.load()


# ---- mask builders (ImageDraw on an L mask)
def m_rect(cv, x0, y0, x1, y1):
    m = cv.mask(); ImageDraw.Draw(m).rectangle([x0, y0, x1, y1], fill=255); return m


def m_poly(cv, pts):
    m = cv.mask(); ImageDraw.Draw(m).polygon([(float(a), float(b)) for a, b in pts], fill=255); return m


def m_ell(cv, x0, y0, x1, y1):
    m = cv.mask(); ImageDraw.Draw(m).ellipse([x0, y0, x1, y1], fill=255); return m


def m_line(cv, pts, w=1):
    m = cv.mask(); ImageDraw.Draw(m).line([(float(a), float(b)) for a, b in pts], fill=255, width=w); return m


def m_or(*ms):
    out = ms[0].copy()
    for m in ms[1:]:
        out.paste(255, (0, 0), m)
    return out


def m_sub(a, b):
    out = a.copy(); out.paste(0, (0, 0), b); return out


# ---- light functions
def cyl(x0, x1, lo=0.15, hi=0.95, peak=0.32):
    """a vertical cylinder lit from the left: brightest at `peak` of its width"""
    def f(x, y):
        t = (x + 0.5 - x0) / max(1, (x1 - x0 + 1))
        d = abs(t - peak)
        return clamp(hi - (hi - lo) * (d / max(peak, 1 - peak)) ** 1.2)
    return f


def box(x0, y0, x1, y1, top=0.9, face=0.6, side=0.35, topH=2, sideW=0):
    """a block: lit top rows, mid front, dark right edge; soft vertical falloff down the face"""
    def f(x, y):
        if y < y0 + topH:
            return top
        if sideW and x > x1 - sideW:
            return side
        return clamp(face - 0.25 * (y - y0) / max(1, y1 - y0) + 0.08 * (x < x0 + 1))
    return f


def grad_v(y0, y1, a, b):
    return lambda x, y: clamp(a + (b - a) * (y - y0) / max(1, y1 - y0))


def noise_mod(f, amt=0.12, seed=0, sc=1):
    return lambda x, y: None if f(x, y) is None else clamp(f(x, y) + (h01(int(x // sc), int(y // sc), seed) - 0.5) * amt)


def glow_dot(cv, cx, cy, r, rmp, k=1.0):
    """a soft dithered glow (for FX-ish bits: flames, eyes); brightest at the centre"""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / max(0.5, r)
            if d <= 1:
                v = clamp((1 - d) * k * 1.1)
                if v > bt(x, y) * 0.35:
                    cv.set(x, y, pick(rmp, v, x, y))


def flame(cv, cx, base, size, f, rmp=GHOST, seed=0):
    """a small flickering flame (ghost-blue by default), frame f"""
    hh = size * 1.9
    for y in range(int(base - hh) - 1, int(base) + 1):
        t = (base - (y + .5)) / hh
        if t < 0 or t > 1:
            continue
        wob = math.sin(f * 1.7 + t * 5 + seed) * 0.8 * t
        half = size * 0.55 * (1 - t) ** 0.7 + 0.3
        for x in range(int(cx - half - 2), int(cx + half + 2)):
            d = abs(x + .5 - (cx + wob)) / half
            if d > 1:
                continue
            v = clamp((1 - d) * 0.6 + (1 - t) * 0.5)
            cv.set(x, y, pick(rmp, v, x, y))


def skull(cv, ox, oy, rmp=BONE, lit=1.0, crown=None):
    S = ["  ....  ", " ...... ", "........", ".xx..xx.", ".xx..xx.", "...xx...", " .t.t.t ", "  ....  "]
    for j, row in enumerate(S):
        for i, ch in enumerate(row):
            if ch == ".":
                lv = 5 if j < 2 else 4 if j < 5 else 3
                if i <= 1: lv += 1
                if i >= 6: lv -= 1
                cv.set(ox + i, oy + j, rmp[int(clamp(lv * lit, 1, len(rmp) - 1))])
            elif ch in "x":
                cv.set(ox + i, oy + j, rmp[0])
            elif ch == "t":
                cv.set(ox + i, oy + j, rmp[2])
    if crown:
        for i, h in enumerate([2, 1, 3, 1, 2, 1, 3, 1, 2][:8]):
            for k in range(h):
                cv.set(ox + i, oy - 1 - k, crown[4 - min(3, k + (i > 5))])
        for i in range(8):
            cv.set(ox + i, oy - 1, crown[3])


def frames_of(fn, n, w, h):
    return [fn(i, w, h) for i in range(n)]
