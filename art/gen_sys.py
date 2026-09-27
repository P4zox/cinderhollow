"""Expansion 3 kit systems art (agent KS): doors, trial sigils + goals, gauntlet markers, vista benches, lore props, icons.

Run:  python3 art/gen_sys.py            (writes art/sys_*.aseprite + assets/sys_*.png/json via asebuild)
      python3 art/gen_sys.py --preview  (also writes a 3x contact sheet to $PREVIEW, default /tmp/sys_preview.png)

Sheets (all small; anchors are bottom-centre unless noted):
  sys_door   48x64  tags <look>_<skin>   look: arch crack hatch ladder portal(6f)        skin: stone wood metal crystal neon
  sys_trial  40x40  tags sigil_<skin> (dim, lit)  goal_<skin> (sealed, opening x2, open)
  sys_gaunt  32x48  tags <look> (unlit, lit)       banner bell stake whistle horn idol stones drum rack terminal
  sys_bench  48x24  tags bench_<skin>
  sys_lore   32x32  tags stone corpse book tablet scroll
  sys_icons  16x16  tags x3_lore x3_page x3_trial x3_gaunt x3_vista x3_secret x3_door x3_rooms
  sys_micons  9x9   tags mx_trial mx_trial_gold mx_gaunt mx_gaunt_done mx_puzzle mx_vista mx_secret mx_door mx_lock mx_passage mx_rooms mx_lore
"""
import math, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envlib import C, outline, bt, h01
from asebuild import build

T = (0, 0, 0, 0)
K = C('0a080e')
SKINS = ['stone', 'wood', 'metal', 'crystal', 'neon']
# k outline · d dark · m mid · l light · h highlight · a accent · g glow · x second accent
PAL = {
    'stone':   dict(k='0b0a10', d='2e2b36', m='4d4957', l='77727f', h='a39daa', a='d8a850', g='ffe0a0', x='8a6a3a'),
    'wood':    dict(k='0c0806', d='3a2618', m='5c3f27', l='86613e', h='b08a5a', a='c8a060', g='ffd08a', x='2a1a10'),
    'metal':   dict(k='08080a', d='25252b', m='42424c', l='696976', h='9898a6', a='ff8a3a', g='ffc080', x='5a3a24'),
    'crystal': dict(k='060812', d='1d2946', m='324e86', l='5886c6', h='a8d8ff', a='c8a8ff', g='e0f0ff', x='7a60c0'),
    'neon':    dict(k='05050d', d='141424', m='24243c', l='3a3a5a', h='66668e', a='30f0ff', g='c0ffff', x='ff3fc0'),
}
def P_(skin):
    return {k: C(v) for k, v in PAL[skin].items()}


class Cv:
    def __init__(s, w, h):
        s.w, s.h = w, h; s.im = Image.new('RGBA', (w, h), T); s.p = s.im.load()
    def px(s, x, y, c):
        x, y = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
        if 0 <= x < s.w and 0 <= y < s.h and c is not None:
            if len(c) == 4 and c[3] < 255:
                o = s.p[x, y]; a = c[3] / 255
                s.p[x, y] = (int(o[0] * (1 - a) + c[0] * a), int(o[1] * (1 - a) + c[1] * a), int(o[2] * (1 - a) + c[2] * a), max(o[3], c[3]))
            else:
                s.p[x, y] = c
    def get(s, x, y):
        return s.p[x, y] if 0 <= x < s.w and 0 <= y < s.h else T
    def rect(s, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                s.px(x, y, c)
    def box(s, x0, y0, x1, y1, P, body='m', lit=True):
        """a shaded block: highlight top row, light left column, dark right/bottom."""
        s.rect(x0, y0, x1, y1, P[body])
        if lit:
            s.rect(x0, y0, x1, y0, P['h']); s.rect(x0, y0 + 1, x0, y1, P['l'])
            s.rect(x1, y0 + 1, x1, y1, P['d']); s.rect(x0 + 1, y1, x1, y1, P['d'])
    def line(s, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            s.px(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c)
    def ell(s, cx, cy, rx, ry, c, fill=True):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                d = ((x - cx) / max(rx, 0.1)) ** 2 + ((y - cy) / max(ry, 0.1)) ** 2
                if (fill and d <= 1) or (not fill and 0.62 <= d <= 1.05):
                    s.px(x, y, c)
    def out(s, col=K, diag=False):
        s.im = outline(s.im, col, diag=diag); s.p = s.im.load(); return s
    def paste(s, o, x=0, y=0):
        s.im.alpha_composite(o.im if isinstance(o, Cv) else o, (int(x), int(y))); s.p = s.im.load()


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)
def alpha(c, a):
    return (c[0], c[1], c[2], int(a))


# ============================================================ doors (48x64)
def masonry(c, x0, y0, x1, y1, P, seed=0, bw=6, bh=4):
    """stone block wall with mortar seams and per-block tone."""
    for y in range(y0, y1 + 1):
        row = (y - y0) // bh
        for x in range(x0, x1 + 1):
            off = (row % 2) * (bw // 2)
            bx = (x - x0 + off) // bw
            seam = (y - y0) % bh == 0 or (x - x0 + off) % bw == 0
            v = h01(bx, row, seed)
            col = P['d'] if seam else (P['l'] if v > 0.72 else P['m'] if v > 0.2 else mix(P['m'], P['d'], 0.5))
            if not seam and (y - y0) % bh == 1 and v > 0.5: col = mix(col, P['h'], 0.35)
            c.px(x, y, col)


def material(c, x0, y0, x1, y1, P, skin, seed=0):
    if skin == 'stone':
        masonry(c, x0, y0, x1, y1, P, seed)
    elif skin == 'wood':
        for x in range(x0, x1 + 1):
            plank = (x - x0) // 4
            for y in range(y0, y1 + 1):
                edge = (x - x0) % 4 == 0
                grain = h01(x, y // 3, seed + plank) > 0.8
                c.px(x, y, P['d'] if edge else (mix(P['m'], P['l'], 0.4) if grain else P['m']))
        for y in (y0 + 2, y1 - 2):
            c.rect(x0, y, x1, y, P['x'])
    elif skin == 'metal':
        c.rect(x0, y0, x1, y1, P['m'])
        for y in range(y0, y1 + 1, 8):
            c.rect(x0, y, x1, y, P['d']); c.rect(x0, y + 1, x1, y + 1, P['l'])
            for x in range(x0 + 2, x1, 5): c.px(x, y + 3, P['h'])
    elif skin == 'crystal':
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                f = ((x * 3 + y * 2) // 7 + (x - y) // 5) % 4
                c.px(x, y, [P['d'], P['m'], P['l'], P['m']][f])
        for i in range(3):
            xx = x0 + 2 + int(h01(i, 3, seed) * (x1 - x0 - 4)); c.line(xx, y0 + 1, xx + 3, y0 + 5, P['h'])
    else:   # neon: dark panels with cyan seams
        c.rect(x0, y0, x1, y1, P['d'])
        for y in range(y0 + 3, y1, 7): c.rect(x0, y, x1, y, P['m'])
        c.rect(x0, y0, x0, y1, alpha(P['a'], 200))


def door_arch(skin):
    P = P_(skin); c = Cv(48, 64)
    x0, x1, top = 8, 39, 12            # outer frame
    ix0, ix1 = 15, 32                  # inner opening (18 wide, the player fits)
    arch_cy, rr = 26, 9
    # frame body
    for y in range(top, 64):
        for x in range(x0, x1 + 1):
            # outer rounded top
            if y < arch_cy and ((x - 23.5) / 16.5) ** 2 + ((y - arch_cy) / 14.5) ** 2 > 1: continue
            c.px(x, y, P['m'])
    tmp = Cv(48, 64); material(tmp, x0, top, x1, 63, P, skin, 3)
    for y in range(64):
        for x in range(48):
            if c.get(x, y)[3]: c.px(x, y, tmp.get(x, y))
    # carve the opening: rectangle + arch
    for y in range(arch_cy - rr, 64):
        for x in range(ix0, ix1 + 1):
            if y < arch_cy and ((x - 23.5) / 9) ** 2 + ((y - arch_cy) / rr) ** 2 > 1: continue
            depth = (y - (arch_cy - rr)) / (64 - arch_cy + rr)
            edge = min(x - ix0, ix1 - x)
            col = mix(C('000000'), P['d'], 0.25 + 0.2 * (1 - depth)) if edge > 1 else mix(P['k'], P['d'], 0.5)
            c.px(x, y, col)
    # inner reveal (depth) on the left side of the opening + threshold step
    for y in range(arch_cy - 2, 62): c.px(ix0, y, P['d']); c.px(ix0 + 1, y, mix(P['d'], C('000000'), 0.4))
    c.rect(ix0 - 2, 61, ix1 + 2, 63, P['l']); c.rect(ix0 - 2, 61, ix1 + 2, 61, P['h'])
    # voussoir ring + keystone
    for a in range(0, 181, 4):
        t = math.radians(a); x = 23.5 + math.cos(t) * 11.5; y = arch_cy - math.sin(t) * 11
        c.px(x, y, P['h'] if a % 20 < 8 else P['l'])
    c.rect(21, arch_cy - 14, 26, arch_cy - 10, P['l']); c.rect(22, arch_cy - 13, 25, arch_cy - 11, P['a'])
    c.px(23, arch_cy - 12, P['g']); c.px(24, arch_cy - 12, P['g'])
    # pillar capitals
    for px_ in (x0, x1 - 5):
        c.rect(px_, arch_cy + 1, px_ + 5, arch_cy + 2, P['h']); c.rect(px_, arch_cy + 3, px_ + 5, arch_cy + 3, P['d'])
    if skin == 'neon':
        for a in range(0, 181, 2):
            t = math.radians(a); c.px(23.5 + math.cos(t) * 10, arch_cy - math.sin(t) * 9.6, P['a'])
        c.rect(ix0 - 1, arch_cy, ix0 - 1, 60, P['a']); c.rect(ix1 + 1, arch_cy, ix1 + 1, 60, P['x'])
    if skin == 'crystal':
        for (x, y) in ((11, 20), (36, 22), (10, 44), (37, 50)): c.px(x, y, P['g'])
    return c.out(P['k'])


def door_crack(skin):
    P = P_(skin); c = Cv(48, 64)
    # jagged fissure through rock: a lit rim of broken stone around a black gap
    xs = []
    for y in range(18, 64):
        t = (y - 18) / 46
        cx = 24 + math.sin(y * 0.33) * 2.2 + (h01(y // 3, 1, 7) - 0.5) * 3
        half = 1.5 + 5.2 * math.sin(min(1, t * 1.25) * math.pi * 0.55) + (h01(y // 2, 5, 3) - 0.5) * 1.4
        xs.append((y, cx, half))
    for y, cx, half in xs:
        for x in range(int(cx - half - 4), int(cx + half + 5)):
            d = abs(x - cx) - half
            if d <= 0:
                c.px(x, y, mix(C('000000'), P['d'], 0.18 + 0.12 * math.sin(y * 0.2)))
            elif d < 1.5:
                c.px(x, y, P['h'] if x < cx else P['l'])
            elif d < 4 and h01(x, y, 11) > 0.35:
                c.px(x, y, P['m'] if h01(x // 2, y // 2, 4) > 0.5 else P['d'])
    # the thin light leaking from deep inside
    for y, cx, half in xs[6:-4]:
        if h01(y, 2, 9) > 0.4: c.px(cx, y, alpha(P['g'], 70))
    # rubble at the foot
    for i in range(9):
        x = 14 + int(h01(i, 1, 21) * 20); y = 60 + int(h01(i, 2, 21) * 3); r = 1 + int(h01(i, 3, 21) * 2)
        c.rect(x, y, x + r, y + r - 1, P['m']); c.px(x, y, P['h'])
    return c.out(P['k'])


def door_hatch(skin):
    P = P_(skin); c = Cv(48, 64)
    # a trapdoor set into the floor (lower 8 px of the frame sit in the floor surface)
    x0, x1, y0, y1 = 9, 38, 55, 62
    c.rect(x0 - 1, y0 - 1, x1 + 1, y1, P['k'])
    lid = Cv(48, 64); material(lid, x0, y0, x1, y1, P, 'wood' if skin in ('stone', 'wood') else skin, 5)
    c.paste(lid)
    for x in (x0 + 5, x1 - 5):   # iron straps
        c.rect(x, y0, x + 1, y1, P['k'] if skin != 'neon' else P['a']); c.px(x, y0 + 2, P['h']); c.px(x, y1 - 2, P['h'])
    c.rect(x0, y0, x1, y0, P['h'])
    # ring handle
    c.ell(24, y0 + 3, 2.5, 2, P['a'], fill=False); c.px(24, y0 + 1, P['g'])
    # the dark seam around the lid
    c.rect(x0 - 1, y1, x1 + 1, y1, C('000000'))
    return c


def door_ladder(skin):
    P = P_(skin); c = Cv(48, 64)
    mat = {'stone': P_('wood'), 'wood': P, 'metal': P, 'crystal': P, 'neon': P}[skin]
    for y in range(0, 64):
        fade = 255 if y > 14 else int(255 * (y / 14) ** 1.3)
        for x, side in ((17, 0), (30, 1)):
            c.px(x, y, alpha(mat['l'] if side == 0 else mat['m'], fade)); c.px(x + 1, y, alpha(mat['d'], fade))
        if y % 6 == 3:
            for x in range(18, 30): c.px(x, y, alpha(mat['h'] if x < 22 else mat['l'], fade))
            for x in range(18, 30): c.px(x, y + 1, alpha(mat['d'], fade))
    if skin == 'neon':
        for y in range(18, 64, 6): c.px(24, y + 3, P['a'])
    for x in (16, 29):   # feet
        c.rect(x, 62, x + 3, 63, mat['d'])
    return c


def door_portal(skin, f, n=6):
    P = P_(skin); c = Cv(48, 64)
    # two low plinths
    for x0 in (7, 34):
        c.box(x0, 56, x0 + 6, 63, P); c.rect(x0 + 1, 55, x0 + 5, 55, P['h'])
        c.px(x0 + 3, 59, P['a'])
    cx, cy, rx, ry = 23.5, 34, 10.5, 21
    ph = f / n * math.pi * 2
    glow, acc, acc2 = P['g'], P['a'], P['x'] if skin == 'neon' else P['h']
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            dx, dy = (x - cx) / rx, (y - cy) / ry; d = math.hypot(dx, dy)
            if d > 1.08: continue
            ang = math.atan2(dy, dx)
            if d > 0.9:   # the rim
                k = 0.5 + 0.5 * math.sin(ang * 3 + ph * 2)
                c.px(x, y, mix(acc, glow, k * 0.8))
            else:        # the swirl inside
                s = math.sin(ang * 2 - d * 7 + ph * 1.0)
                base = mix(C('05030a'), P['d'], 0.6)
                col = mix(base, acc, max(0, s) * 0.55 * (1 - d * 0.5)) if s > 0.2 else base
                if skin == 'neon' and ((y + f) % 5 == 0 and h01(y, f, 3) > 0.6): col = mix(col, acc2, 0.6)
                if d < 0.25: col = mix(col, glow, 0.35 * (1 - d / 0.25))
                c.px(x, y, col)
    # motes in the rim
    for i in range(3):
        a = ph + i * 2.1; c.px(cx + math.cos(a) * rx * 0.95, cy + math.sin(a) * ry * 0.95, glow)
    return c


# ============================================================ trial sigil + goal (40x40)
def rune_ring(c, cx, cy, rx, ry, col, n=10, seed=0):
    for i in range(n):
        a = i / n * math.pi * 2; x = cx + math.cos(a) * rx; y = cy + math.sin(a) * ry
        k = int(h01(i, seed, 5) * 3)
        c.px(x, y, col)
        if k == 0: c.px(x + 1, y, col)
        elif k == 1: c.px(x, y - 1, col)


def sigil(skin, lit):
    P = P_(skin); c = Cv(40, 40)
    # low slab set in the floor
    c.box(4, 34, 35, 39, P)
    material(c, 5, 35, 34, 38, P, skin, 2)
    c.rect(4, 34, 35, 34, P['h'])
    g = P['g'] if lit else mix(P['a'], P['d'], 0.45)
    a = P['a'] if lit else mix(P['a'], P['d'], 0.65)
    # engraved ring on the slab top, seen at an angle
    c.ell(19.5, 36.4, 13, 1.8, a, fill=False)
    for x in (9, 14, 25, 30): c.px(x, 36, g)
    # the floating sigil glyph: a diamond with a crossed stave
    cy = 20
    for i in range(-6, 7):
        w = 6 - abs(i)
        c.px(19.5 - w, cy + i, a); c.px(20.5 + w - 1, cy + i, a)
    c.line(19, cy - 9, 19, cy + 9, g); c.line(20, cy - 9, 20, cy + 9, a)
    c.line(14, cy, 25, cy, a)
    c.px(19, cy - 10, g); c.px(20, cy - 10, g)
    if lit:
        for (x, y) in ((12, 14), (27, 16), (10, 26), (29, 25)): c.px(x, y, alpha(g, 180))
    c = c.out(P['k'])
    if lit:   # soft inner glow around the glyph (after the outline so it isn't boxed in)
        for y in range(cy - 11, cy + 12):
            for x in range(9, 31):
                d = math.hypot(x - 19.5, (y - cy) * 0.9)
                if 5 < d < 11 and not c.get(x, y)[3]: c.px(x, y, alpha(g, int(40 * (1 - (d - 5) / 6))))
    return c


def goal(skin, frame):
    P = P_(skin); c = Cv(40, 40)
    # pedestal
    c.box(9, 30, 30, 39, P); material(c, 10, 31, 29, 38, P, skin, 8); c.rect(9, 30, 30, 30, P['h'])
    c.box(12, 26, 27, 29, P); c.rect(7, 38, 32, 39, P['d'])
    # reliquary box
    open_ = frame >= 1
    lidlift = [0, 2, 4, 5][frame]
    gold = C('d8a850') if skin != 'neon' else P['a']
    goldh = C('ffe08a') if skin != 'neon' else P['g']
    c.rect(13, 18, 26, 25, mix(gold, P['d'], 0.55)); c.rect(13, 18, 26, 18, gold); c.rect(13, 19, 13, 25, goldh)
    c.rect(15, 20, 24, 24, mix(gold, P['k'], 0.35))
    c.rect(18, 21, 21, 23, gold)   # the emblem
    if open_:
        # the lid swings back (it ends standing behind the box), the inside lights up
        if frame == 1: c.rect(12, 13, 27, 16, gold); c.rect(12, 13, 27, 13, goldh)
        elif frame == 2: c.rect(13, 11, 26, 15, mix(gold, P['d'], 0.3)); c.rect(13, 11, 26, 11, goldh)
        else: c.rect(14, 9, 25, 17, mix(gold, P['d'], 0.45)); c.rect(14, 9, 25, 9, gold); c.rect(15, 11, 24, 16, mix(gold, P['k'], 0.5))
        for y in range(19, 24):
            for x in range(14, 26): c.px(x, y, mix(goldh, C('ffffff'), 0.35 if frame == 3 else 0.1))
    else:
        c.rect(12, 14, 27, 17, gold); c.rect(12, 14, 27, 14, goldh); c.rect(19, 12, 20, 13, goldh)
        c.px(19, 16, P['k']); c.px(20, 16, P['k'])   # keyhole seal
    c = c.out(P['k'])
    if frame == 3:   # light rising out of it (after the outline, so no dark fringe)
        for i, x in enumerate(range(15, 25, 3)):
            for y in range(1, 9):
                if (y + i) % 2 == 0: c.px(x, y, alpha(goldh, 40 + y * 16))
    return c


# ============================================================ gauntlet markers (32x48): unlit, lit
def gaunt(look, lit):
    c = Cv(32, 48)
    S, W_, M_ = P_('stone'), P_('wood'), P_('metal')
    fire = C('ffb040'); fire2 = C('ff6a20'); gold = C('d8a850'); goldh = C('ffe08a')
    def flame(x, y, s=1.0):
        for i in range(int(7 * s)):
            w = max(0, int((3 - i * 0.45) * s))
            for dx in range(-w, w + 1): c.px(x + dx, y - i, fire if abs(dx) < w or i > 4 else fire2)
        c.px(x, y - int(7 * s), goldh)
    if look == 'banner':
        c.rect(15, 6, 16, 47, W_['m']); c.rect(15, 6, 15, 47, W_['l']); c.rect(13, 45, 18, 47, W_['d'])
        c.rect(12, 5, 19, 6, M_['l']); c.px(15, 3, gold); c.px(16, 3, gold); c.px(15, 4, gold)
        red, redd = C('7a1a22'), C('4a0e16')
        for y in range(8, 34):
            for x in range(17, 29):
                tatter = y > 28 and h01(x, 0, 3) * 6 < (y - 28)
                if not tatter: c.px(x, y, red if (x + y // 3) % 7 else redd)
        for y in range(8, 34): c.px(17, y, redd)
        em = goldh if lit else C('9a7a40')
        for (x, y) in ((22, 15), (23, 15), (21, 16), (24, 16), (22, 17), (23, 17), (22, 18), (23, 18), (22, 20), (23, 20), (22.5, 21)): c.px(x, y, em)
        if lit: flame(15.5, 4, 0.8)
    elif look == 'bell':
        for x in (6, 25): c.rect(x, 6, x + 1, 47, W_['m']); c.rect(x, 6, x, 47, W_['l'])
        c.rect(5, 5, 26, 7, W_['d']); c.rect(5, 5, 26, 5, W_['h'])
        c.rect(15, 8, 16, 11, M_['d'])
        for y in range(11, 28):   # bell profile: domed crown, narrow waist, flared lip
            t = (y - 11) / 16
            w = 2.5 + 3.2 * math.sin(min(1, t * 1.6) * 1.2) + (2.8 * ((t - 0.75) / 0.25) ** 2 if t > 0.75 else 0)
            for x in range(int(15.5 - w), int(16.5 + w) + 1):
                sh = (x - (15.5 - w)) / (2 * w + 1)
                c.px(x, y, goldh if sh < 0.22 else gold if sh < 0.62 else mix(gold, C('4a3010'), 0.45))
        c.rect(12, 27, 19, 27, mix(gold, C('000000'), 0.5)); c.px(15, 29, M_['h']); c.px(16, 29, M_['h'])
        if lit:
            for (x, y) in ((9, 14), (22, 13), (8, 22), (23, 24)): c.px(x, y, goldh)
    elif look == 'stake':
        c.rect(14, 10, 17, 47, W_['m']); c.rect(14, 10, 14, 47, W_['l']); c.rect(17, 10, 17, 47, W_['d'])
        for y in range(4, 10): c.rect(15 - (9 - y) // 3, y, 16 + (9 - y) // 3, y, W_['l'])
        for yy in (18, 30):   # bound skulls
            c.ell(15.5, yy, 3.5, 3, C('d8ccb0')); c.px(14, yy, K); c.px(17, yy, K); c.rect(14, yy + 2, 17, yy + 2, C('a89c80'))
        c.line(10, 24, 21, 27, M_['l']); c.line(10, 25, 21, 28, M_['d'])
        if lit: flame(15.5, 6, 1.1)
    elif look == 'whistle':
        c.rect(15, 16, 16, 47, S['m']); c.rect(12, 43, 19, 47, S['d']); c.rect(12, 43, 19, 43, S['l'])
        c.line(16, 16, 22, 10, W_['l'])
        for i in range(12):   # a long bone whistle hanging on a cord
            c.px(20 + i * 0.1, 18 + i, C('e0d6bc')); c.px(21 + i * 0.1, 18 + i, C('b0a68a'))
        c.px(20, 22, K); c.px(21, 25, K); c.line(22, 10, 21, 18, C('6a5a40'))
        if lit:
            for (x, y) in ((24, 16), (25, 20), (24, 25)): c.px(x, y, goldh)
    elif look == 'horn':
        c.rect(7, 30, 24, 32, W_['d']); c.rect(7, 30, 24, 30, W_['l'])
        for x in (9, 22): c.rect(x, 33, x + 1, 47, W_['m'])
        for i in range(20):   # a curved war horn resting on the stand
            t = i / 19; x = 6 + t * 20; y = 27 - math.sin(t * math.pi) * 10 - t * 2; r = 1 + t * 2.6
            for dy in range(-int(r), int(r) + 1): c.px(x, y + dy, C('d8cbb0') if dy < 0 else C('a8987a'))
        c.rect(24, 16, 27, 24, gold); c.rect(24, 16, 24, 24, goldh)
        if lit:
            for (x, y) in ((28, 12), (30, 17), (29, 23)): c.px(x, y, goldh)
    elif look == 'idol':
        c.box(9, 38, 22, 47, S); c.box(11, 16, 20, 37, S); c.rect(11, 16, 20, 16, S['h'])
        c.ell(15.5, 11, 4.5, 5, S['m']); c.ell(14.5, 10, 2.5, 3, S['l']); c.rect(12, 15, 19, 16, S['d'])
        c.rect(10, 4, 21, 5, S['d']); c.rect(12, 3, 19, 3, S['l'])
        eye = C('ff5a3a') if lit else S['d']
        c.px(13, 12, eye); c.px(18, 12, eye)
        for y in range(20, 36, 4): c.rect(13, y, 18, y, S['d'])
        if lit:
            c.px(13, 11, fire); c.px(18, 11, fire)
    elif look == 'stones':
        for (x0, y0, x1) in ((3, 26, 10), (12, 18, 20), (22, 28, 29)):
            c.box(x0, y0, x1, 47, S); c.rect(x0 + 1, y0, x1 - 1, y0, S['h'])
            rc = gold if lit else S['d']
            for y in range(y0 + 4, 44, 5): c.px((x0 + x1) // 2, y, rc); c.px((x0 + x1) // 2 + 1, y + 1, rc)
    elif look == 'drum':
        for x in (8, 23): c.line(x, 47, x + (3 if x < 16 else -3), 34, W_['d'])
        c.rect(7, 22, 24, 36, C('7a2a1a')); c.rect(7, 22, 7, 36, C('9a4a2a'))
        for y in (24, 34): c.rect(7, y, 24, y, gold)
        for x in range(8, 24, 4): c.line(x, 24, x + 2, 34, C('c8b48a'))
        c.ell(15.5, 21, 8.5, 2.2, C('d8c8a0')); c.ell(15.5, 21, 7, 1.2, C('efe2c0'))
        c.line(20, 10, 25, 19, W_['l']); c.ell(19.5, 9.5, 1.6, 1.6, W_['h'])
        if lit:
            for y in (24, 34): c.rect(7, y, 24, y, goldh)
            for (x, y) in ((5, 16), (27, 18), (15, 14)): c.px(x, y, goldh)
    elif look == 'rack':
        c.rect(5, 18, 26, 19, W_['m']); c.rect(5, 18, 26, 18, W_['l']); c.rect(5, 38, 26, 39, W_['m'])
        for x in (6, 25): c.rect(x, 16, x + 1, 47, W_['d'])
        for i, x in enumerate((9, 13, 17, 21)):
            if i == 1:   # a spear
                c.line(x, 6, x, 44, W_['l']); c.rect(x - 1, 3, x + 1, 6, M_['h'])
            else:
                c.rect(x, 10, x, 40, M_['h']); c.rect(x + 1, 10, x + 1, 40, M_['l']); c.rect(x - 2, 30, x + 3, 31, gold if lit else M_['d'])
        if lit:
            for (x, y) in ((9, 9), (17, 12), (21, 8)): c.px(x, y, C('ffffff'))
    elif look == 'terminal':
        N = P_('neon')
        c.box(8, 14, 23, 47, N); c.rect(8, 14, 23, 14, N['h'])
        c.rect(10, 17, 21, 28, C('000000'))
        scr = N['a'] if lit else C('1a3a44')
        for y in range(18, 28, 2): c.rect(11, y, 11 + int(h01(y, 1, 4) * 9), y, scr)
        c.rect(10, 31, 21, 33, N['m']); c.px(12, 32, N['x'] if lit else N['l']); c.px(15, 32, scr)
        c.rect(8, 44, 23, 44, N['a'] if lit else N['l'])
    return c.out(K)


# ============================================================ benches (48x24)
def bench(skin):
    P = P_(skin); c = Cv(48, 24)
    if skin == 'stone':
        c.box(6, 12, 41, 15, P); c.rect(6, 12, 41, 12, P['h'])
        for x0 in (9, 33): c.box(x0, 16, x0 + 5, 23, P)
        c.rect(8, 17, 39, 17, P['d'])
        c.px(23, 13, P['a']); c.px(24, 13, P['a'])
    elif skin == 'wood':
        for y in (12, 14): c.rect(5, y, 42, y + 1, P['l'] if y == 12 else P['m']); c.rect(5, y, 42, y, P['h'])
        for x in (7, 39): c.rect(x, 16, x + 1, 23, P['d']); c.rect(x, 4, x + 1, 11, P['m'])
        for y in (4, 7): c.rect(6, y, 41, y + 1, P['m']); c.rect(6, y, 41, y, P['l'])
        c.rect(8, 16, 38, 16, P['d'])
    elif skin == 'metal':
        c.rect(5, 12, 42, 14, P['m']); c.rect(5, 12, 42, 12, P['h'])
        for x in range(7, 41, 4): c.px(x, 13, P['d'])
        for x0 in (7, 38): c.line(x0, 15, x0 - 1, 23, P['l']); c.line(x0 + 1, 15, x0 + 2, 23, P['d'])
        for x in range(8, 40, 3): c.px(x, 6 + (x % 2), P['l'])
        c.rect(6, 5, 41, 5, P['m']); c.rect(6, 9, 41, 9, P['m']); c.rect(6, 5, 6, 11, P['l']); c.rect(41, 5, 41, 11, P['d'])
    elif skin == 'crystal':
        c.rect(6, 12, 41, 14, P['l']); c.rect(6, 12, 41, 12, P['h']); c.rect(6, 14, 41, 14, P['m'])
        for x0 in (9, 34):
            for y in range(15, 24): c.rect(x0 + (y - 15) // 4, y, x0 + 4 - (y - 15) // 4, y, P['m'] if y % 3 else P['l'])
        for x in (12, 20, 31): c.px(x, 13, P['g'])
    else:
        c.rect(5, 12, 42, 14, P['m']); c.rect(5, 12, 42, 12, P['h']); c.rect(5, 15, 42, 15, P['a'])
        for x0 in (9, 36): c.rect(x0, 16, x0 + 2, 23, P['d'])
        c.rect(5, 15, 42, 15, P['a']); c.px(5, 15, P['x']); c.px(42, 15, P['x'])
    return c.out(P['k'])


# ============================================================ lore props (32x32)
def lore(look):
    c = Cv(32, 32); S, W_ = P_('stone'), P_('wood')
    parch, parchd, ink = C('e6d8b0'), C('b8a67c'), C('4a3a2a')
    if look == 'stone':
        for y in range(8, 32):
            w = 7 if y > 12 else 7 - (12 - y) * 0.8
            for x in range(int(16 - w), int(16 + w) + 1):
                c.px(x, y, S['l'] if x < 13 else S['m'] if x < 20 else S['d'])
        for y in range(13, 27, 3): c.rect(12, y, 12 + int(h01(y, 1, 6) * 7) + 2, y, S['d'])
        c.px(10, 10, S['h']); c.px(11, 9, S['h'])
        for x in range(8, 25, 3): c.px(x, 31, C('4a5a30'))   # moss at the foot
    elif look == 'corpse':
        B, Bd = C('d4c8aa'), C('9a8e72')
        c.box(19, 16, 27, 31, S)   # a tombstone it leans on
        c.ell(15, 15, 3.4, 3.2, B); c.px(14, 15, K); c.px(16, 15, K); c.rect(14, 17, 16, 17, Bd)
        c.rect(12, 19, 18, 26, C('4a3a3a')); c.rect(12, 19, 12, 26, C('5a4a48'))
        for y in (21, 23, 25): c.rect(13, y, 17, y, Bd)
        c.line(11, 27, 5, 30, B); c.line(18, 27, 22, 31, B); c.line(12, 22, 8, 27, B)
        c.rect(5, 26, 9, 29, parch); c.rect(5, 26, 9, 26, C('fff2cc')); c.px(7, 28, ink)   # the page in its hand
    elif look == 'book':
        c.rect(14, 18, 17, 31, W_['m']); c.rect(14, 18, 14, 31, W_['l']); c.rect(10, 29, 21, 31, W_['d'])
        c.line(6, 17, 25, 13, W_['m']); c.line(6, 18, 25, 14, W_['d'])
        for i in range(10):
            c.line(7 + i, 16 - i * 0.2, 7 + i, 12 - i * 0.2, parch if i < 9 else parchd)
            c.line(16 + i, 14 - i * 0.2, 16 + i, 10 - i * 0.2, parch if i else parchd)
        for i in range(0, 9, 2): c.px(9 + i, 13 - i * 0.2, ink); c.px(18 + i, 11 - i * 0.2, ink)
        c.px(16, 9, C('7a1a22')); c.px(16, 10, C('7a1a22'))   # ribbon
    elif look == 'tablet':
        c.box(6, 6, 25, 27, S); c.rect(6, 6, 25, 6, S['h'])
        for y in range(10, 25, 3):
            for x in range(9, 23):
                if h01(x // 2, y, 3) > 0.3: c.px(x, y, S['d'])
        c.rect(4, 28, 27, 31, S['d']); c.rect(4, 28, 27, 28, S['l'])
        c.px(15, 8, C('d8a850')); c.px(16, 8, C('d8a850'))
    elif look == 'scroll':
        c.box(8, 24, 23, 31, S)
        c.rect(9, 17, 22, 22, parch); c.rect(9, 17, 22, 17, C('fff2cc'))
        for x in (8, 23): c.ell(x, 19.5, 1.6, 3, parchd)
        for y in (19, 21): c.rect(11, y, 20, y, ink)
    return c.out(K)


# ============================================================ icons (16x16) and map icons (9x9)
def icon16(name):
    c = Cv(16, 16); gold, goldh, goldd = C('d8a850'), C('ffe08a'), C('8a6a3a'); parch, parchd, ink = C('e6d8b0'), C('b8a67c'), C('4a3a2a')
    if name == 'x3_lore':   # the Chronicle: a dark tome with a gold clasp
        c.rect(3, 2, 12, 13, C('4a1a22')); c.rect(3, 2, 12, 2, C('7a2a32')); c.rect(3, 2, 3, 13, C('6a2430'))
        c.rect(13, 3, 13, 13, parch); c.rect(4, 13, 13, 13, parchd)
        c.rect(6, 5, 10, 9, gold); c.rect(7, 6, 9, 8, goldd); c.px(8, 7, goldh); c.rect(12, 7, 14, 8, gold)
    elif name == 'x3_page':
        c.rect(3, 1, 12, 14, parch); c.rect(3, 1, 12, 1, C('fff2cc')); c.rect(12, 2, 12, 14, parchd); c.rect(10, 12, 12, 14, parchd)
        for y in (4, 6, 8, 10): c.rect(5, y, 5 + (6 if y < 10 else 3), y, ink)
        c.px(5, 12, C('7a1a22'))
    elif name == 'x3_trial':
        for i in range(-5, 6):
            w = 5 - abs(i); c.px(7.5 - w, 7 + i, gold); c.px(8.5 + w, 7 + i, gold)
        c.line(8, 1, 8, 14, goldh); c.line(3, 7, 13, 7, gold); c.px(8, 7, C('ffffff'))
    elif name == 'x3_gaunt':
        c.rect(3, 1, 4, 15, C('86613e')); c.rect(5, 2, 12, 10, C('7a1a22')); c.rect(5, 2, 12, 2, C('9a2a32'))
        for x in (6, 8, 10): c.px(x, 11, C('7a1a22'))
        c.rect(7, 4, 9, 7, gold); c.px(8, 5, goldh)
    elif name == 'x3_vista':
        c.rect(1, 4, 14, 9, C('3a4a70')); c.rect(1, 4, 14, 5, C('6a7ab0')); c.ell(11, 7, 2, 1.5, goldh)
        c.rect(1, 8, 14, 9, C('2a2a40')); c.rect(3, 11, 12, 11, C('86613e')); c.rect(4, 12, 4, 14, C('5c3f27')); c.rect(11, 12, 11, 14, C('5c3f27'))
    elif name == 'x3_secret':
        c.ell(7.5, 7.5, 6, 3.4, C('d8ccb0')); c.ell(7.5, 7.5, 2.6, 2.6, C('4a8ab0')); c.ell(7.5, 7.5, 1.2, 1.2, K); c.px(6, 6, C('ffffff'))
    elif name == 'x3_door':
        c.rect(3, 4, 12, 15, C('77727f')); c.ell(7.5, 5, 4.5, 4, C('77727f')); c.rect(5, 6, 10, 15, C('0a0810')); c.ell(7.5, 6, 2.5, 2.5, C('0a0810'))
        c.px(7, 1, gold); c.px(8, 1, gold)
    elif name == 'x3_rooms':
        c.rect(1, 3, 14, 12, parch); c.rect(1, 3, 14, 3, C('fff2cc'))
        for (x0, y0, x1, y1) in ((3, 5, 6, 8), (7, 7, 12, 9), (9, 4, 11, 6)): c.rect(x0, y0, x1, y1, parchd)
        c.px(5, 6, C('c03a2a'))
    return c.out(K)


def micon(name):
    c = Cv(9, 9); gold, goldh, dim = C('d8a850'), C('ffe08a'), C('9a8a6a')
    red, parch = C('b83a2a'), C('e6d8b0')
    if name in ('mx_trial', 'mx_trial_gold'):
        col = goldh if name == 'mx_trial_gold' else C('c9bda2')
        for i in range(-3, 4):
            w = 3 - abs(i); c.px(4 - w, 4 + i, col); c.px(4 + w, 4 + i, col)
        c.px(4, 4, C('ffffff') if name == 'mx_trial_gold' else gold)
        if name == 'mx_trial_gold': c.px(4, 0, C('ffffff')); c.px(4, 8, C('ffffff'))
    elif name in ('mx_gaunt', 'mx_gaunt_done'):
        c.rect(1, 0, 1, 8, C('b08a5a')); c.rect(2, 1, 6, 5, red if name == 'mx_gaunt' else goldh); c.px(3, 6, red if name == 'mx_gaunt' else goldh); c.px(5, 6, red if name == 'mx_gaunt' else goldh)
    elif name == 'mx_puzzle':
        c.ell(4, 4, 3.3, 3.3, C('9ac0d8'), fill=False); c.px(4, 4, C('d8f0ff')); c.px(4, 1, C('d8f0ff')); c.px(7, 4, C('d8f0ff'))
    elif name == 'mx_vista':
        c.rect(0, 2, 8, 4, C('6a7ab0')); c.px(6, 3, goldh); c.rect(1, 6, 7, 6, C('b08a5a')); c.px(1, 7, C('86613e')); c.px(7, 7, C('86613e'))
    elif name == 'mx_secret':
        c.px(4, 0, goldh); c.px(4, 8, goldh); c.px(0, 4, goldh); c.px(8, 4, goldh)
        c.rect(3, 3, 5, 5, C('fff2cc')); c.px(4, 1, gold); c.px(4, 7, gold); c.px(1, 4, gold); c.px(7, 4, gold)
    elif name == 'mx_door':
        c.rect(1, 2, 7, 8, C('a39daa')); c.rect(3, 4, 5, 8, C('0a0810')); c.px(4, 3, C('0a0810')); c.px(4, 1, gold)
    elif name == 'mx_lock':
        c.ell(4, 3, 2.2, 2.2, C('b8b0c0'), fill=False); c.rect(1, 4, 7, 8, gold); c.rect(1, 4, 7, 4, goldh); c.px(4, 6, K)
    elif name == 'mx_passage':
        for y in range(0, 9): c.px(4 + (1 if y % 3 == 1 else -1 if y % 3 == 2 else 0), y, goldh)
        c.px(2, 7, dim); c.px(6, 2, dim)
    elif name == 'mx_rooms':
        c.rect(0, 1, 8, 7, parch); c.rect(2, 3, 4, 5, C('b8a67c')); c.rect(5, 4, 7, 5, C('b8a67c'))
    elif name == 'mx_lore':
        c.rect(1, 0, 7, 8, C('6a2430')); c.rect(1, 0, 7, 0, C('8a3a40')); c.rect(3, 2, 5, 4, gold)
    return c.out(K)


# ============================================================ build
def sheet(name, fw, fh, entries):
    """entries: list of (tag, [Cv frames], ms)"""
    frames, tags = [], []
    for tag, fl, ms in entries:
        a = len(frames)
        for f in fl:
            im = f.im if isinstance(f, Cv) else f
            frames.append({'ms': ms, 'cels': {'art': im}})
        tags.append((tag, a, len(frames) - 1))
    build(name, fw, fh, ['art'], frames, tags)
    print(name, len(frames), 'frames', fw * fh * len(frames), 'px')
    return frames, tags


def main():
    out = {}
    D = []
    for look in ('arch', 'crack', 'hatch', 'ladder'):
        for sk in SKINS:
            D.append((f'{look}_{sk}', [{'arch': door_arch, 'crack': door_crack, 'hatch': door_hatch, 'ladder': door_ladder}[look](sk)], 100))
    for sk in SKINS:
        D.append((f'portal_{sk}', [door_portal(sk, f) for f in range(6)], 90))
    out['sys_door'] = sheet('sys_door', 48, 64, D)
    Tt = []
    for sk in SKINS:
        Tt.append((f'sigil_{sk}', [sigil(sk, False), sigil(sk, True)], 200))
        Tt.append((f'goal_{sk}', [goal(sk, i) for i in range(4)], 90))
    out['sys_trial'] = sheet('sys_trial', 40, 40, Tt)
    G = [(lk, [gaunt(lk, False), gaunt(lk, True)], 200) for lk in ('banner', 'bell', 'stake', 'whistle', 'horn', 'idol', 'stones', 'drum', 'rack', 'terminal')]
    out['sys_gaunt'] = sheet('sys_gaunt', 32, 48, G)
    out['sys_bench'] = sheet('sys_bench', 48, 24, [(f'bench_{sk}', [bench(sk)], 100) for sk in SKINS])
    out['sys_lore'] = sheet('sys_lore', 32, 32, [(lk, [lore(lk)], 100) for lk in ('stone', 'corpse', 'book', 'tablet', 'scroll')])
    out['sys_icons'] = sheet('sys_icons', 16, 16, [(n, [icon16(n)], 100) for n in ('x3_lore', 'x3_page', 'x3_trial', 'x3_gaunt', 'x3_vista', 'x3_secret', 'x3_door', 'x3_rooms')])
    out['sys_micons'] = sheet('sys_micons', 9, 9, [(n, [micon(n)], 100) for n in ('mx_trial', 'mx_trial_gold', 'mx_gaunt', 'mx_gaunt_done', 'mx_puzzle', 'mx_vista', 'mx_secret', 'mx_door', 'mx_lock', 'mx_passage', 'mx_rooms', 'mx_lore')])
    if '--preview' in sys.argv:
        rows = []
        for name in out:
            im = Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', name + '.png')).convert('RGBA')
            rows.append(im)
        W_ = max(min(r.width, 1200) for r in rows); H_ = sum(r.height + 4 for r in rows)
        S = Image.new('RGBA', (W_, H_), (38, 34, 46, 255)); y = 0
        for r in rows: S.alpha_composite(r.crop((0, 0, min(r.width, W_), r.height)), (0, y)); y += r.height + 4
        S = S.resize((S.width * 3, S.height * 3), Image.NEAREST); pv = os.environ.get('PREVIEW', '/tmp/sys_preview.png'); S.save(pv); print('preview', pv, S.size)


if __name__ == '__main__':
    main()
