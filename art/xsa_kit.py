"""Tiny pixel-art toolkit for the SA (Expansion 3) props: a canvas with shape fills, an auto-bevel (lit from the upper
left like the rest of the house style), texture speckle and a 1px near-black outline. Used by art/gen_xsa*.py."""
import math, random
from PIL import Image, ImageDraw

OUT = (14, 10, 14, 255)


def C(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (a[3] if len(a) > 3 else 255,)


def lit(c, k):   # k>0 lighter, k<0 darker
    if k >= 0: return mix(c, (255, 255, 255, 255), k)
    return mix(c, (0, 0, 0, 255), -k)


class Cv:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.im)

    def p(s, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.w and 0 <= y < s.h: s.im.putpixel((x, y), c)

    def g(s, x, y):
        if 0 <= x < s.w and 0 <= y < s.h: return s.im.getpixel((x, y))
        return (0, 0, 0, 0)

    def rect(s, x0, y0, x1, y1, c):
        s.d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], fill=c)

    def ell(s, cx, cy, rx, ry, c):
        s.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=c)

    def poly(s, pts, c):
        s.d.polygon([(round(x), round(y)) for x, y in pts], fill=c)

    def line(s, x0, y0, x1, y1, c, w=1):
        s.d.line([(x0, y0), (x1, y1)], fill=c, width=w)

    def thick(s, pts, c, w):   # a polyline of round-ish thickness
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for i in range(n + 1):
                t = i / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                s.ell(x, y, w / 2, w / 2, c)

    def speckle(s, cols, n, box=None, seed=1):
        r = random.Random(seed)
        x0, y0, x1, y1 = box or (0, 0, s.w - 1, s.h - 1)
        for _ in range(n):
            x, y = r.randint(x0, x1), r.randint(y0, y1)
            if s.g(x, y)[3] > 0: s.p(x, y, r.choice(cols))

    def bevel(s, hi=0.22, lo=0.32):
        """lighten pixels whose upper/left neighbour is empty, darken those whose lower/right neighbour is empty"""
        src = s.im.copy(); P = src.load()
        for y in range(s.h):
            for x in range(s.w):
                c = P[x, y]
                if c[3] == 0 or c == OUT: continue
                up = P[x, y - 1][3] if y > 0 else 0
                lf = P[x - 1, y][3] if x > 0 else 0
                dn = P[x, y + 1][3] if y < s.h - 1 else 0
                rt = P[x + 1, y][3] if x < s.w - 1 else 0
                if up == 0 or lf == 0: s.im.putpixel((x, y), lit(c, hi))
                elif dn == 0 or rt == 0: s.im.putpixel((x, y), lit(c, -lo))
        return s

    def outline(s, c=OUT):
        src = s.im.copy(); P = src.load()
        for y in range(s.h):
            for x in range(s.w):
                if P[x, y][3] != 0: continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < s.w and 0 <= yy < s.h and P[xx, yy][3] > 60 and P[xx, yy] != c:
                        s.im.putpixel((x, y), c); break
        return s

    def glow(s, cx, cy, r, col, a=0.5):
        """soft additive-looking halo painted as translucent pixels (only where empty)"""
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy) / r
                if d >= 1: continue
                cur = s.g(x, y)
                if cur[3] == 0: s.p(x, y, (col[0], col[1], col[2], int(255 * a * (1 - d) ** 2)))

    def paste(s, other, x, y):
        s.im.alpha_composite(other.im, (int(x), int(y)))

    def flip(s):
        s.im = s.im.transpose(Image.FLIP_LEFT_RIGHT); s.d = ImageDraw.Draw(s.im); return s


def frame(img):
    return {'ms': 120, 'cels': {'main': img}}


def sheet(name, w, h, items, ms=None):
    """items: [(tag, [PIL images])] -> asebuild"""
    import asebuild
    frames, tags, i = [], [], 0
    for tag, imgs in items:
        for im in imgs:
            f = frame(im)
            if ms and tag in ms: f['ms'] = ms[tag]
            frames.append(f)
        tags.append((tag, i, i + len(imgs) - 1)); i += len(imgs)
    asebuild.build(name, w, h, ['main'], frames, tags)
    return name


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def cyl_shade(c, ramp, box=None, key=None, lightu=0.3):
    """shade every opaque pixel (or those equal to `key`) as a lit cylinder across each row's span: ramp = dark..light
    (5 colours); the light falls from the left (u = lightu), Bayer-dithered band edges"""
    x0b, y0b, x1b, y1b = box or (0, 0, c.w - 1, c.h - 1)
    px = c.im.load()
    for y in range(y0b, y1b + 1):
        x = x0b
        while x <= x1b:
            ok = lambda xx: px[xx, y][3] > 0 and (key is None or px[xx, y][:3] == key[:3])
            if not ok(x): x += 1; continue
            a = x
            while x <= x1b and ok(x): x += 1
            b = x - 1; w = max(1, b - a)
            for xx in range(a, b + 1):
                u = (xx - a) / w
                v = 1 - min(1, abs(u - lightu) / (1 - lightu if u > lightu else max(lightu, 0.01)))   # 1 at the light line
                t = 0.15 + 0.85 * v ** 0.8
                if u > 0.85: t *= 0.6
                idx = t * (len(ramp) - 1) + (BAYER[y % 4][xx % 4] / 16 - 0.5) * 0.9
                px[xx, y] = ramp[max(0, min(len(ramp) - 1, int(round(idx))))]


def bark_lines(c, box, ramp, seed, spacing=6, key=None):
    """wavy vertical fissures with a lit ridge beside each, following the row spans (so they wrap round the trunk)"""
    r = random.Random(seed); px = c.im.load()
    x0b, y0b, x1b, y1b = box
    phases = [r.random() * 6.28 for _ in range(64)]
    for y in range(y0b, y1b + 1):
        xs = [x for x in range(x0b, x1b + 1) if px[x, y][3] > 0 and (key is None or px[x, y] in key)]
        if len(xs) < 4: continue
        a, b = xs[0], xs[-1]; w = b - a
        n = max(2, w // spacing)
        for i in range(1, n):
            u = i / n + math.sin(y / 11 + phases[i % 64]) * 0.35 / n
            x = int(a + u * w)
            if a < x < b and r.random() < 0.9:
                c.p(x, y, ramp[0])
                if x - 1 > a and r.random() < 0.7: c.p(x - 1, y, ramp[-1] if u < 0.4 else ramp[-2])


def leaf_clump(c, cx, cy, rx, ry, ramp, seed):
    """a leaf mass lit from the upper left: dark body, mid, light cap, a ragged edge of single leaves"""
    r = random.Random(seed)
    c.ell(cx, cy, rx, ry, ramp[1])
    c.ell(cx - rx * 0.15, cy - ry * 0.15, rx * 0.8, ry * 0.75, ramp[2])
    c.ell(cx - rx * 0.35, cy - ry * 0.35, rx * 0.45, ry * 0.4, ramp[3])
    for _ in range(int(rx * ry * 0.5)):
        a = r.random() * 6.28; d = r.random() ** 0.5
        x, y = cx + math.cos(a) * rx * d * 1.08, cy + math.sin(a) * ry * d * 1.08
        up = math.cos(a) * -0.7 + math.sin(a) * -0.7   # facing the light
        col = ramp[min(len(ramp) - 1, max(0, int(1 + (up + d * 0.2) * 1.6 + r.random())))]
        c.p(x, y, col); 
        if r.random() < 0.4: c.p(x + 1, y, col)
    for _ in range(int(rx * 2)):   # ragged edge
        a = r.random() * 6.28
        c.p(cx + math.cos(a) * (rx + 1), cy + math.sin(a) * (ry + 1), ramp[1 if math.sin(a) > 0 else 2])
