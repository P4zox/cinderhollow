"""Kit mechanics art (agent KM): palettes + pixel drawers for every kit part in six skins.

Skins: stone (masonry, gold trim), bone (ivory ossuary, ghost-blue), wood (planks, iron bands, moss), iron (riveted
steel, ember), crystal (star-glass), neon (dark alloy, cyan/magenta light strips). Every drawer takes a Canvas (envlib)
and paints in place; outlines are added by the caller with envlib.outline where noted.
"""
import math
from envlib import C, Canvas, K, T, outline, bt

PAL = {
    'stone': dict(k=C('0e0c12'), r=[C('26232c'), C('3a3642'), C('56515e'), C('7a7482'), C('a49eab')], a=C('b8862e'), A=C('f4d890')),
    'bone': dict(k=C('120e0a'), r=[C('3a3226'), C('5e5240'), C('8a7c62'), C('b8aa8a'), C('e4d9bc')], a=C('4a86c8'), A=C('c8e4ff')),
    'wood': dict(k=C('0e0906'), r=[C('2a1c12'), C('3f2b1b'), C('5c4028'), C('7d5a38'), C('a07a4e')], a=C('4e6e2c'), A=C('92b456'),
                 m=[C('26262c'), C('3e3e46'), C('6a6a74')]),
    'iron': dict(k=C('09090c'), r=[C('1c1c22'), C('2c2c34'), C('43434d'), C('62626e'), C('8c8c9a')], a=C('d0501e'), A=C('ffb060')),
    'crystal': dict(k=C('070914'), r=[C('151c36'), C('22305a'), C('34508a'), C('5a86c4'), C('a8d4ff')], a=C('9a7ae0'), A=C('ffffff')),
    'neon': dict(k=C('06060e'), r=[C('12121e'), C('1c1c2c'), C('2a2a40'), C('3c3c58'), C('5c5c80')], a=C('30e8ff'), A=C('c0ffff'),
                 m2=C('ff3ca8')),
}
SKINS = ['stone', 'bone', 'wood', 'iron', 'crystal', 'neon']
BRONZE = [C('2a1a0c'), C('5a3a14'), C('8a5e22'), C('c08e3a'), C('f0cc78')]
GLASS_OFF = [C('1a1620'), C('2a2432')]
FLAME = [C('7a1a08'), C('d04a14'), C('ff8a2a'), C('ffc860'), C('fff0c0')]
BLUEFLAME = [C('102050'), C('2a5ad0'), C('5a9aff'), C('a8d4ff'), C('f0f8ff')]
CYANFLAME = [C('083040'), C('1090b0'), C('30e8ff'), C('a0ffff'), C('ffffff')]


def ramp_pick(r, v, x, y):
    v = max(0.0, min(1.0, v))
    f = v * (len(r) - 1)
    i = int(f)
    if f - i > bt(x, y):
        i += 1
    return r[min(i, len(r) - 1)]


# ------------------------------------------------------------------ platform slabs (16x16, surface at y=0, 8 px thick)
def slab(skin, part, seed=0):
    """part: 'l' 'm' 'r' 's'. Body rows 0..7 (row 7 = dark underside), decoration hangs below to ~row 13."""
    p = PAL[skin]; r = p['r']; k = p['k']
    c = Canvas(16, 16)
    L = part in ('l', 's'); R = part in ('r', 's')
    for y in range(0, 8):
        for x in range(16):
            v = 0.62 - y * 0.07
            if skin == 'stone':
                seam = (x == (7 if (y // 4) % 2 == 0 else 15)) and 1 <= y <= 6 or y == 4
                col = r[1] if seam else ramp_pick(r[1:4], v + 0.12 * math.sin(x * 1.7 + seed), x, y)
            elif skin == 'bone':
                seg = (x + seed * 3) % 8
                col = r[1] if seg == 0 and 1 <= y <= 6 else ramp_pick(r[2:5], v + 0.25 - abs(y - 3) * 0.08 - (0.15 if seg in (1, 7) else 0), x, y)
            elif skin == 'wood':
                grain = (y in (2, 5))
                col = r[1] if grain else ramp_pick(r[2:5], v + 0.08 * math.sin(x * 0.9 + y * 2 + seed), x, y)
            elif skin == 'iron':
                col = ramp_pick(r[1:5], v + (0.12 if y == 1 else 0) - (0.1 if x in (0, 15) else 0), x, y)
            elif skin == 'crystal':
                facet = ((x + y * 2 + seed * 5) % 11) / 11
                col = ramp_pick(r[1:5], v - 0.1 + facet * 0.35, x, y)
            else:  # neon
                col = ramp_pick(r[1:4], v - 0.15, x, y)
            c.set(x, y, col)
    # top lip + underside edge
    for x in range(16):
        c.set(x, 0, r[4] if skin != 'neon' else r[3]); c.set(x, 1, r[3] if skin != 'crystal' else r[4] if x % 5 == 1 else r[3])
        c.set(x, 7, r[0])
    if skin == 'wood':
        for x in range(16):   # moss tufts on the lip
            if (x * 7 + seed * 3) % 9 < 2: c.set(x, 0, p['A']); c.set(x, 1, p['a'])
        for bx in ([1] if L else []) + ([13] if R else []):
            for y in range(1, 7):
                c.set(bx, y, p['m'][1]); c.set(bx + 1, y, p['m'][2] if y < 3 else p['m'][1])
        c.set(4, 3, p['m'][2]); c.set(11, 3, p['m'][2])     # nails
    if skin == 'iron':
        for rx in (3, 12):
            c.set(rx, 3, r[4]); c.set(rx, 4, r[1])
        c.set(8, 5, p['a'])
    if skin == 'neon':
        for x in range(16):
            c.set(x, 2, p['a'] if (x + seed) % 8 else p['A']); c.set(x, 5, r[0])
        if L: c.set(2, 4, p['m2'])
        if R: c.set(13, 4, p['m2'])
    if skin == 'stone':
        for x in range(1, 15, 5): c.set(x + seed % 3, 2, r[4])
        if L or R:
            gx = 3 if L else 12
            c.set(gx, 3, p['a']); c.set(gx, 4, p['A'])
    if skin == 'bone':
        for x in range(2, 16, 8): c.set((x + seed * 3) % 16, 3, r[0])
    # underside decoration
    if L or R:
        xs = [2] if L and not R else [13] if R and not L else [3, 12]
        for bx in xs:
            for y in range(8, 13):
                w = max(0, 3 - (y - 8) // 2)
                for x in range(bx - w // 2 - 1, bx + w // 2 + 1):
                    c.set(x, y, ramp_pick(r[0:3], 0.7 - (y - 8) * 0.12, x, y) if skin != 'crystal' else r[2 + (x + y) % 2])
    else:
        if skin == 'bone':
            for bx in (3, 11):
                for y in range(8, 11): c.set(bx, y, r[3])
        elif skin == 'crystal':
            for bx, n in ((4, 4), (10, 3)):
                for y in range(8, 8 + n): c.set(bx, y, r[3] if y < 8 + n - 1 else r[4])
        elif skin == 'neon':
            c.set(8, 8, p['a']); c.set(8, 9, r[2])
        elif skin == 'wood':
            c.set(6, 8, r[1]); c.set(6, 9, r[1])
        elif skin == 'iron':
            for x in range(2, 14): c.set(x, 8, r[1] if (x % 4) else r[2])
    # side outline for caps
    for y in range(0, 8):
        if L: c.set(0, y, k)
        if R: c.set(15, y, k)
    img = outline(c.img, k)
    # keep the top row flush (the rider's feet sit exactly on y=0): no outline above
    return img


def cracks(level):
    c = Canvas(16, 16)
    K2 = C('08060a', 230)
    pts = [(3, 1), (4, 3), (6, 4), (7, 6)] + ([(10, 1), (11, 2), (11, 3), (13, 5), (12, 6)] if level > 1 else [])
    for x, y in pts: c.set(x, y, K2)
    if level > 1:
        for x, y in [(5, 2), (8, 5), (2, 5), (14, 3)]: c.set(x, y, K2)
    return c.img


# ------------------------------------------------------------------ gate parts + lift yoke + rope anchor (16x16)
def gate_bar(skin):
    p = PAL[skin]; r = p['r']; c = Canvas(16, 16)
    for bx in (3, 7, 11):
        for y in range(16):
            c.set(bx - 1, y, r[1]); c.set(bx, y, r[3] if skin != 'crystal' else r[4]); c.set(bx + 1, y, r[2])
    for x in range(1, 15):   # crossbar
        c.set(x, 7, r[2]); c.set(x, 8, r[1])
    for bx in (3, 7, 11): c.set(bx, 7, r[4]); c.set(bx, 8, r[2])
    if skin == 'bone':
        for bx in (3, 7, 11): c.set(bx, 3, r[4]); c.set(bx, 12, r[4])
    if skin == 'wood':
        for bx in (3, 7, 11):
            for y in range(16): c.set(bx - 1, y, r[1]); c.set(bx, y, r[3]); c.set(bx + 1, y, r[2])
        for x in range(1, 15): c.set(x, 7, p['m'][1]); c.set(x, 8, p['m'][0])
    return outline(c.img, p['k'])


def gate_foot(skin):
    img = gate_bar(skin)
    p = PAL[skin]; r = p['r']
    c = Canvas(16, 16); c.paste(img, 0, 0)
    for y in range(11, 16):
        for x in range(16): c.set(x, y, T)
    for bx in (3, 7, 11):   # spiked bar ends
        for y in range(9, 14):
            w = 1 if y < 12 else 0
            for x in range(bx - w, bx + w + 1): c.set(x, y, r[3] if x == bx else r[2])
        c.set(bx, 14, r[4] if skin != 'wood' else r[3])
    return outline(c.img, p['k'])


def gate_cap(skin):
    p = PAL[skin]; r = p['r']; c = Canvas(16, 16)
    for y in range(0, 7):
        for x in range(0, 16):
            c.set(x, y, ramp_pick(r[1:4], 0.7 - y * 0.08, x, y))
    for x in range(16): c.set(x, 0, r[4]); c.set(x, 6, r[0])
    if skin == 'neon':
        for x in range(2, 14): c.set(x, 4, p['a'])
        for bx in (4, 8, 11): c.set(bx, 6, p['A'])
    else:
        c.set(7, 3, p['a']); c.set(8, 3, p['A']); c.set(8, 2, p['a'])
    for bx in (3, 7, 11):   # slots the bars slide into
        c.set(bx, 5, p['k'])
    return outline(c.img, p['k'])


def gate_foot_neon():
    p = PAL['neon']; r = p['r']; c = Canvas(16, 16)
    for y in range(12, 16):
        for x in range(1, 15): c.set(x, y, ramp_pick(r[1:4], 0.6 - (y - 12) * 0.1, x, y))
    for x in range(1, 15): c.set(x, 12, r[4])
    for bx in (4, 8, 11): c.set(bx, 12, p['A']); c.set(bx, 13, p['a'])
    return outline(c.img, p['k'])


def yoke(skin):
    p = PAL[skin]; r = p['r']; c = Canvas(16, 16)
    # a clamp shackle: the chain end hooks into it; sits on the platform lip (bottom row 15 = platform surface + 1)
    for y in range(9, 16):
        for x in range(6, 10): c.set(x, y, r[2] if x in (6, 9) else r[3])
    for x in range(5, 11): c.set(x, 15, r[1])
    c.set(7, 10, p['k']); c.set(8, 10, p['k']); c.set(7, 11, r[0]); c.set(8, 11, r[0])
    c.set(8, 13, p['a'] if skin != 'wood' else r[4])
    return outline(c.img, p['k'])


def anchor(skin):
    p = PAL[skin]; r = p['r']; c = Canvas(16, 16)
    # a ring bolted under the ceiling; its bottom sits at y=15 (drawn with bottom at anchor+4)
    for x in range(4, 12): c.set(x, 8, r[3]); c.set(x, 9, r[1])
    for a in range(0, 360, 20):
        x = 8 + round(math.cos(math.radians(a)) * 2.6); y = 12 + round(math.sin(math.radians(a)) * 2.4)
        c.set(x, y, r[4] if a < 180 else r[2])
    c.set(8, 10, r[2])
    if skin == 'neon': c.set(8, 12, p['a'])
    return outline(c.img, p['k'])


# ------------------------------------------------------------------ 32x32 parts (bottom-centred unless noted)
def lever(skin, on):
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    for y in range(26, 32):   # base plinth
        for x in range(10, 22): c.set(x, y, ramp_pick(r[1:4], 0.8 - (y - 26) * 0.12, x, y))
    for x in range(10, 22): c.set(x, 26, r[4])
    c.set(15, 28, p['a']); c.set(16, 28, p['A'])
    ang = math.radians(35 if on else -35)
    for i in range(14):
        x = 16 + math.sin(ang) * i; y = 27 - math.cos(ang) * i
        c.set(round(x), round(y), r[3]); c.set(round(x) + 1, round(y), r[1])
    kx = 16 + math.sin(ang) * 14; ky = 27 - math.cos(ang) * 14
    for dx in range(-2, 2):
        for dy in range(-2, 1): c.set(round(kx) + dx, round(ky) + dy, p['a'] if dy > -2 else p['A'])
    if skin == 'neon':
        c.set(round(kx), round(ky) - 1, p['A'])
    return outline(c.img, p['k'])


def switch(skin, down):
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    for y in range(22, 32):
        for x in range(10, 22): c.set(x, y, ramp_pick(r[1:4], 0.75 - (y - 22) * 0.06, x, y))
    for x in range(10, 22): c.set(x, 22, r[4])
    for y in range(24, 31): c.set(10, y, r[3])
    top = 22 if down else 19
    for y in range(top, 23):
        for x in range(13, 19): c.set(x, y, (p['A'] if y == top else p['a']) if down else (r[4] if y == top else r[3]))
    return outline(c.img, p['k'])


def plate(skin, down):
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    y0 = 30 if down else 29
    for y in range(y0, 32):
        for x in range(9, 23): c.set(x, y, ramp_pick(r[2:5], 0.9 - (y - y0) * 0.3, x, y))
    for x in range(10, 22): c.set(x, y0, (p['A'] if down else r[4]))
    if down:
        for x in range(11, 21, 3): c.set(x, y0 + 1, p['a'])
    return outline(c.img, p['k'])


def crate(skin):
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    x0, y0 = 8, 16
    for y in range(y0, 32):
        for x in range(x0, x0 + 16):
            c.set(x, y, ramp_pick(r[1:4], 0.75 - (y - y0) * 0.025 - (x - x0) * 0.01, x, y))
    for x in range(x0, x0 + 16): c.set(x, y0, r[4]); c.set(x, 31, r[0])
    for y in range(y0, 32): c.set(x0, y, r[3]); c.set(x0 + 15, y, r[1])
    if skin == 'wood':
        for i in range(14):
            c.set(x0 + 1 + i, y0 + 1 + i, r[4]); c.set(x0 + 14 - i, y0 + 1 + i, r[4])
        for y in (y0 + 1, 30):
            for x in range(x0 + 1, x0 + 15): c.set(x, y, p['m'][1])
    elif skin == 'stone':
        for x in range(x0 + 1, x0 + 15): c.set(x, y0 + 8, r[1])
        c.set(x0 + 7, y0 + 4, p['a']); c.set(x0 + 8, y0 + 4, p['A']); c.set(x0 + 7, y0 + 12, p['a'])
    elif skin == 'iron':
        for rx, ry in [(2, 2), (13, 2), (2, 13), (13, 13)]: c.set(x0 + rx, y0 + ry, r[4])
        for x in range(x0 + 4, x0 + 12): c.set(x, y0 + 7, r[0]); c.set(x, y0 + 8, r[2])
        c.set(x0 + 7, y0 + 10, p['a'])
    elif skin == 'bone':
        for bx in (3, 7, 11):
            for y in range(y0 + 1, 31): c.set(x0 + bx, y, r[4] if (y % 5) else r[2])
        for x in range(x0 + 1, x0 + 15): c.set(x, y0 + 8, r[3])
    elif skin == 'crystal':
        for i in range(10): c.set(x0 + 3 + i, y0 + 12 - i, r[4])
        c.set(x0 + 5, y0 + 4, p['A']); c.set(x0 + 11, y0 + 11, p['a'])
    else:
        for x in range(x0 + 2, x0 + 14): c.set(x, y0 + 5, p['a']); c.set(x, y0 + 11, p['m2'] if x % 3 == 0 else r[1])
        c.set(x0 + 3, y0 + 8, p['A'])
    return outline(c.img, p['k'])


def spring(skin, comp):
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    for y in range(29, 32):
        for x in range(9, 23): c.set(x, y, r[2] if y == 29 else r[1])
    top = 26 if comp else 22
    n = 31 - top - 3
    for i in range(n):
        y = 28 - i
        for x in range(11, 21):
            if (i % 2 == 0 and x in range(11, 21)) or x in (11, 20): c.set(x, y, p['a'] if (i % 2 == 0) else r[2])
    for y in range(top, top + 3):
        for x in range(8, 24): c.set(x, y, r[4] if y == top else r[3] if y == top + 1 else r[1])
    c.set(15, top + 1, p['A']); c.set(16, top + 1, p['A'])
    return outline(c.img, p['k'])


def brazier(skin, frame):
    """frame 0 = cold, 1..3 = burning."""
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    for y in range(28, 32):        # foot
        for x in range(11, 21): c.set(x, y, r[2] if y > 28 else r[3])
    for y in range(22, 28):        # stem
        for x in range(14, 18): c.set(x, y, r[1] if x == 14 else r[3] if x == 15 else r[2])
    for y in range(16, 22):        # bowl
        w = 8 - (y - 16) // 2
        for x in range(16 - w, 16 + w): c.set(x, y, ramp_pick(r[1:5], 0.8 - (y - 16) * 0.08 - abs(x - 15.5) * 0.02, x, y))
    for x in range(8, 24): c.set(x, 16, r[4])
    if skin == 'stone': c.set(15, 19, p['a']); c.set(16, 19, p['A'])
    if skin == 'bone':
        for x in (11, 15, 19): c.set(x, 18, r[0]); c.set(x, 19, r[0])
    if skin == 'iron':
        for x in range(9, 23, 3): c.set(x, 17, r[1])
    if skin == 'neon':
        for x in range(9, 23): c.set(x, 18, p['a'] if x % 2 else r[2])
    if skin == 'wood':
        for x in range(9, 23): c.set(x, 17, p['m'][1])
    # embers in the bowl
    for x in range(10, 22): c.set(x, 15, C('3a1a10') if frame == 0 else C('ff8a2a') if x % 3 else C('ffd070'))
    img = outline(c.img, p['k'])
    if frame:
        fl = CYANFLAME if skin == 'neon' else BLUEFLAME if skin in ('crystal', 'bone') else FLAME
        f = Canvas(32, 32)
        ph = frame * 2.1
        for y in range(2, 16):
            t = (15 - y) / 13.0
            w = (1 - t) * 5.5 * (0.8 + 0.2 * math.sin(ph + y))
            cx = 16 + math.sin(ph + y * 0.6) * (t * 2.2)
            for x in range(int(cx - w) - 1, int(cx + w) + 2):
                d = abs(x - cx) / max(w, 0.5)
                if d > 1: continue
                v = (1 - d) * 0.9 + (1 - t) * 0.4 - 0.2
                f.set(x, y, fl[max(0, min(4, int(v * 5)))])
        img.alpha_composite(f.img)
    return img


def blade(skin):
    """a crescent axe head centred on (16,17); the chain meets its socket at (16,8)."""
    p = PAL[skin]; r = p['r']; c = Canvas(32, 32)
    for y in range(6, 12):   # socket + haft stub
        for x in range(14, 18): c.set(x, y, r[2] if x in (14, 17) else r[3])
    c.set(15, 7, r[4])
    # a sleek crescent, horns up: a thin band between two offset ellipses, honed edge on the outer rim
    for y in range(9, 27):
        for x in range(1, 31):
            o = (x - 16) ** 2 / 14.5 ** 2 + (y - 10) ** 2 / 14.0 ** 2
            i = (x - 16) ** 2 / 13.0 ** 2 + (y - 6) ** 2 / 14.0 ** 2
            if o <= 1 and i > 1 and y >= 10:
                edge = o > 0.84
                if skin == 'neon':
                    col = p['A'] if edge else p['a'] if (x + y) % 3 else r[3]
                elif skin == 'crystal':
                    col = r[4] if edge else r[3] if (x - y) % 4 else r[2]
                elif skin == 'bone':
                    col = r[4] if edge else r[3] if y > 16 else r[2]
                else:
                    col = C('e4e4ec') if edge else ramp_pick(r[1:4], 0.95 - (y - 10) * 0.035, x, y)
                c.set(x, y, col)
    for y in range(11, 22):   # the haft down into the blade's spine
        c.set(15, y, r[3] if skin != 'neon' else r[2]); c.set(16, y, r[1])
    if skin in ('stone', 'iron'): c.set(15, 15, p['a'])
    if skin == 'wood':
        for y in range(6, 12): c.set(15, y, p['m'][1] if y % 2 else p['m'][2])
    return outline(c.img, p['k'])


def bell(lit):
    c = Canvas(32, 32)
    B = BRONZE
    for y in range(2, 5):
        for x in range(14, 18): c.set(x, y, B[1] if x in (14, 17) else B[2])   # crown loop
    for y in range(5, 22):
        t = (y - 5) / 16.0
        w = 3.5 + t * t * 5.5 + (1.5 if y >= 20 else 0)
        for x in range(int(16 - w), int(16 + w) + 1):
            v = 0.7 - abs(x - 15) / (w + 1) * 0.6 + (0.2 if lit else 0)
            c.set(x, y, ramp_pick(B[1:], v, x, y))
    for x in range(8, 25): c.set(x, 21, B[0]); c.set(x, 20, B[3] if not lit else B[4])
    c.set(16, 23, B[2]); c.set(16, 22, B[1])
    for y in range(8, 16): c.set(13, y, B[4] if lit else B[3])
    return outline(c.img, K)


def lantern(lit):
    c = Canvas(32, 32); r = PAL['stone']['r']
    for y in range(26, 32):
        for x in range(13, 19): c.set(x, y, r[2] if x > 13 else r[3])
    for x in range(11, 21): c.set(x, 31, r[1]); c.set(x, 26, r[3])
    for y in range(13, 26):   # cage
        for x in range(11, 21):
            if x in (11, 20) or y in (13, 25): c.set(x, y, C('2a2a30') if x != 11 else C('4a4a54'))
            elif x in (14, 17): c.set(x, y, C('1c1c22'))
            else: c.set(x, y, (FLAME[3] if abs(x - 15.5) < 2 and 16 < y < 23 else FLAME[2]) if lit else GLASS_OFF[(x + y) % 2])
    for x in range(10, 22): c.set(x, 12, C('3a3a44'))
    for x in range(13, 19): c.set(x, 11, C('3a3a44'))
    c.set(15, 10, C('5a5a64')); c.set(16, 10, C('5a5a64'))
    if lit: c.set(15, 19, FLAME[4]); c.set(16, 19, FLAME[4])
    return outline(c.img, K)


RUNES = [  # 8 glyph strokes on a 7x9 grid (x, y pairs of line segments)
    [((3, 0), (3, 8)), ((0, 2), (6, 2)), ((1, 6), (5, 6))],
    [((0, 0), (6, 8)), ((6, 0), (0, 8))],
    [((3, 0), (0, 4)), ((0, 4), (3, 8)), ((3, 8), (6, 4)), ((6, 4), (3, 0))],
    [((1, 0), (1, 8)), ((1, 0), (5, 3)), ((5, 3), (1, 5))],
    [((0, 8), (3, 0)), ((3, 0), (6, 8)), ((1, 5), (5, 5))],
    [((3, 0), (3, 8)), ((3, 3), (0, 0)), ((3, 3), (6, 0)), ((3, 6), (0, 8)), ((3, 6), (6, 8))],
    [((0, 1), (6, 1)), ((6, 1), (0, 7)), ((0, 7), (6, 7))],
    [((0, 4), (6, 4)), ((3, 0), (3, 8)), ((1, 1), (5, 7))],
]


def glyph(sym, lit):
    c = Canvas(32, 32); r = PAL['stone']['r']
    if not lit:
        for y in range(8, 25):
            for x in range(9, 23): c.set(x, y, ramp_pick(r[1:4], 0.65 - (y - 8) * 0.015, x, y))
        for x in range(9, 23): c.set(x, 8, r[4])
    for (a, b) in RUNES[sym]:
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2 + 1
        for i in range(n + 1):
            t = i / n
            x = 13 + round(a[0] + (b[0] - a[0]) * t); y = 12 + round(a[1] + (b[1] - a[1]) * t)
            if lit:
                c.set(x, y, C('d8f0ff'))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if c.get(x + dx, y + dy)[3] == 0: c.set(x + dx, y + dy, C('5aa0ff', 150))
            else:
                c.set(x, y, r[0])
    return outline(c.img, K) if not lit else c.img


def organ_stop(out):
    c = Canvas(32, 32); B = BRONZE
    for y in range(10, 22):
        for x in range(10, 22): c.set(x, y, C('2a1e18') if (x + y) % 7 else C('3a2a20'))
    for x in range(10, 22): c.set(x, 10, C('4a3628'))
    ln = 5 if out else 2
    for y in range(13, 19):
        for x in range(14, 18 + ln - 2): c.set(x, y, B[2] if y in (13, 18) else B[3])
    for y in range(12, 20):
        for x in range(16 + ln, 19 + ln): c.set(x, y, B[4] if out and x == 16 + ln else B[3] if y not in (12, 19) else B[1])
    if out:
        c.set(17 + ln, 15, C('fff0c0'))
    return outline(c.img, K)


def portrait(lit):
    c = Canvas(32, 32); G = BRONZE
    for y in range(4, 28):
        for x in range(6, 26):
            edge = x in (6, 7, 24, 25) or y in (4, 5, 26, 27)
            if edge: c.set(x, y, G[3] if (x + y) % 3 else G[2])
    for y in range(6, 26):
        for x in range(8, 24): c.set(x, y, C('1a0e14') if y < 20 else C('241018'))
    for y in range(9, 19):   # a pale face in shadow
        w = 4 - abs(y - 13) * 0.4
        for x in range(int(16 - w), int(16 + w) + 1): c.set(x, y, C('3a2c34'))
    for y in range(18, 26):
        for x in range(10, 22): c.set(x, y, C('2e1420'))
    eye = C('ff3030') if lit else C('14080c')
    c.set(14, 13, eye); c.set(18, 13, eye)
    if lit: c.set(14, 12, C('ffa0a0')); c.set(18, 12, C('ffa0a0'))
    return outline(c.img, K)


BEAMCOL = {'sun': (BRONZE, C('fff0c0'), C('ffd070')), 'star': (PAL['crystal']['r'], C('ffffff'), C('a8d4ff')),
           'neon': (PAL['neon']['r'], C('c0ffff'), C('30e8ff'))}


def emitter(style):
    ramp, hot, glow = BEAMCOL[style]; c = Canvas(32, 32)
    for y in range(10, 22):
        for x in range(8, 20): c.set(x, y, ramp_pick(ramp[0:4], 0.75 - (y - 10) * 0.04, x, y))
    for y in range(12, 20):
        for x in range(20, 23): c.set(x, y, ramp[2] if y in (12, 19) else ramp[1])
    for y in range(13, 19): c.set(23, y, glow)
    for y in range(14, 18): c.set(24, y, hot)
    for x in range(8, 20): c.set(x, 10, ramp[3])
    c.set(12, 15, glow); c.set(13, 15, hot)
    return outline(c.img, K)


def mirror(style, rot):
    ramp, hot, glow = BEAMCOL[style]; c = Canvas(32, 32)
    # a pivot mount (behind), then a polished plate along the line at rot*45° (0 = —, 1 = \\, 2 = |, 3 = /)
    for y in range(14, 19):
        for x in range(14, 19): c.set(x, y, ramp[1] if (x + y) % 2 else ramp[2])
    a = math.radians(rot * 45)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    for i in range(-9, 10):
        x = 16 + dx * i; y = 16 + dy * i
        c.set(round(x + nx), round(y + ny), ramp[1])      # dark back
        c.set(round(x), round(y), glow if abs(i) < 8 else ramp[3])
        c.set(round(x - nx), round(y - ny), hot if abs(i) % 4 != 1 else glow)
    return outline(c.img, K, diag=False)


def socket(style, lit):
    ramp, hot, glow = BEAMCOL[style]; c = Canvas(32, 32)
    if not lit:
        for y in range(9, 24):
            for x in range(9, 24):
                d = math.hypot(x - 16, y - 16)
                if d <= 7.3: c.set(x, y, ramp[2] if d > 5.5 else ramp[1] if d > 3 else C('0a080c'))
        for a in range(0, 360, 90):
            c.set(16 + round(math.cos(math.radians(a)) * 6.5), 16 + round(math.sin(math.radians(a)) * 6.5), ramp[3])
        return outline(c.img, K)
    for y in range(4, 29):
        for x in range(4, 29):
            d = math.hypot(x - 16, y - 16)
            if d <= 3: c.set(x, y, hot)
            elif d <= 5: c.set(x, y, glow)
            elif (x == 16 or y == 16) and d <= 11 and int(d) % 2 == 0: c.set(x, y, (glow[0], glow[1], glow[2], 170))
    return c.img
