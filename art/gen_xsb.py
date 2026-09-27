"""Agent SB (Expansion 3): decor, backdrops, sky and icons for the new Necropolis and Dunes rooms.

  xsb_nv     48x64   Necropolis decor (bottom-anchored; `cage` hangs from its top)
  xsb_du     48x64   Dunes decor (bottom-anchored)
  xsb_tall   64x112  palms, obelisk, broken columns (bottom-anchored)
  xsb_big    192x128 backdrop paintings, painted once into a room's back layer (bottom-centre anchored)
  xsb_sky    512x216 the Last Oasis sunset: far (sky, sun, clouds) + mid (dunes, palms)
  xsb_icons  16x16   c_x3_hood, c_x3_scarab
  xsb_bug    16x12   the golden scarab (walk 4, dig 3)

python3 art/gen_xsb.py [--preview]   (preview writes contact sheets to the scratch dir given by $SBPREV)
"""
import math, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envlib import pick, clamp, h01, bt
from xsb_draw import *   # noqa

PREVIEW = "--preview" in sys.argv


def cv(w=48, h=64):
    return Canvas(w, h)


# ============================================================================ NECROPOLIS
def nv_lamppost(f, w=48, h=64):
    c = cv(w, h); cx = 24
    c.paint(m_rect(c, cx - 5, 58, cx + 4, 63), NST, box(cx - 5, 58, cx + 4, 63, 0.75, 0.55, 0.3, 1, 2))           # plinth
    c.paint(m_rect(c, cx - 3, 55, cx + 2, 57), NST, box(cx - 3, 55, cx + 2, 57, 0.8, 0.6, 0.35, 1, 1))
    c.paint(m_rect(c, cx - 1, 16, cx + 1, 55), IRON, cyl(cx - 1, cx + 1, 0.2, 0.8, 0.2))                          # post
    for y in (24, 40, 50):
        c.paint(m_rect(c, cx - 2, y, cx + 2, y + 1), IRON, 0.55)
    c.paint(m_line(c, [(cx, 16), (cx + 6, 12), (cx + 9, 14)], 1), IRON, 0.6)                                     # scrolled arm
    c.paint(m_line(c, [(cx, 16), (cx - 6, 12), (cx - 9, 14)], 1), IRON, 0.6)
    for lx in (cx + 9, cx - 9):                                                                                  # twin lanterns
        c.paint(m_rect(c, lx - 3, 15, lx + 3, 25), IRON, 0.3)
        c.paint(m_rect(c, lx - 2, 16, lx + 2, 24), GHOST, lambda x, y: 0.25 + 0.4 * (1 - abs(y - 21) / 5))
        c.paint(m_poly(c, [(lx - 4, 15), (lx + 4, 15), (lx, 11)]), IRON, 0.5)
        c.set(lx, 10, IRON[5])
        flame(c, lx, 23, 2.2 + 0.4 * math.sin(f * 2.1 + lx), f, GHOST, seed=lx)
        for yy in range(16, 25):
            c.set(lx - 1, yy, IRON[2]); c.set(lx + 1, yy, IRON[2])
    c.outline()
    return c.im


def nv_headstone(v):
    def fn(f, w=48, h=64):
        c = cv(w, h); cx = 24
        if v == 0:   # a cross-topped slab, cracked
            m = m_or(m_rect(c, cx - 7, 44, cx + 6, 63), m_ell(c, cx - 7, 38, cx + 6, 52))
            c.paint(m, NST, noise_mod(lambda x, y: clamp(0.72 - 0.35 * (x - cx + 7) / 14 - 0.15 * (y - 38) / 25), 0.1, 3))
            c.paint(m_rect(c, cx - 1, 26, cx + 1, 40), NST, cyl(cx - 1, cx + 1, 0.35, 0.8, 0.2))
            c.paint(m_rect(c, cx - 5, 30, cx + 4, 32), NST, 0.7)
            for y in range(46, 58, 3):
                for x in range(cx - 4, cx + 4):
                    if h01(x, y, 5) < 0.55: c.set(x, y, BONE[2])
            c.paint(m_line(c, [(cx + 2, 44), (cx + 4, 50), (cx + 2, 55)], 1), NST, 0.05)
        else:        # rounded slab with a skull relief and a ghost-candle
            m = m_or(m_rect(c, cx - 8, 46, cx + 7, 63), m_ell(c, cx - 8, 36, cx + 7, 56))
            c.paint(m, NST, noise_mod(lambda x, y: clamp(0.7 - 0.3 * (x - cx + 8) / 16 - 0.12 * (y - 36) / 27), 0.1, 4))
            skull(c, cx - 4, 42, BONE, 0.9)
            c.paint(m_rect(c, cx - 6, 54, cx + 5, 55), NST, 0.2)
            c.paint(m_rect(c, cx + 9, 57, cx + 10, 63), BONE, 0.8)
            flame(c, cx + 9.5, 56, 1.5, f, GHOST, seed=3)
        c.outline()
        return c.im
    return fn


def nv_tombchest(v):
    def fn(f, w=48, h=64):
        c = cv(w, h); x0, x1 = 5, 42
        c.paint(m_rect(c, x0, 50, x1, 63), NST, box(x0, 50, x1, 63, 0.75, 0.55, 0.28, 1, 3))
        for x in range(x0 + 3, x1 - 3, 6):     # carved arcading
            c.paint(m_rect(c, x, 54, x + 3, 61), NST, 0.12)
            c.set(x + 1, 53, NST[2]); c.set(x + 2, 53, NST[2])
        c.paint(m_rect(c, x0 - 2, 46, x1 + 2, 49), NST, box(x0 - 2, 46, x1 + 2, 49, 0.9, 0.62, 0.3, 1, 2))   # lid
        if v == 0:   # a bone effigy lying on the lid
            c.paint(m_ell(c, x0 + 2, 39, x0 + 9, 46), BONE, cyl(x0 + 2, x0 + 9, 0.3, 0.85))
            c.paint(m_poly(c, [(x0 + 9, 41), (x1 - 4, 42), (x1 - 2, 46), (x0 + 9, 46)]), BONE, lambda x, y: clamp(0.75 - (y - 41) * 0.08))
            c.paint(m_line(c, [(x0 + 12, 43), (x1 - 8, 43)], 1), IRON, 0.7)                                   # the sword on its chest
            c.paint(m_rect(c, x0 + 14, 41, x0 + 15, 45), GOLD, 0.6)
            for i, cc in enumerate([3, 5, 3]):
                c.set(x0 + 4 + i * 2, 38, GOLD[cc])
        else:        # a purple pall and two ghost candles
            c.paint(m_poly(c, [(x0 - 1, 45), (x1 + 1, 45), (x1 - 2, 58), (x1 - 8, 55), (x0 + 12, 59), (x0 + 1, 56)]), PURP,
                    lambda x, y: clamp(0.55 - (y - 45) * 0.03 + 0.15 * math.sin(x * 0.6)))
            c.paint(m_rect(c, x0 + 14, 46, x0 + 22, 47), GOLD, 0.5)
            for cx_ in (x0 + 3, x1 - 3):
                c.paint(m_rect(c, cx_, 38, cx_ + 1, 45), BONE, 0.8)
                flame(c, cx_ + 1, 37, 1.6, f, GHOST, seed=cx_)
        c.outline()
        return c.im
    return fn


def nv_mourner(f, w=48, h=64):
    c = cv(w, h); cx = 24
    c.paint(m_rect(c, cx - 9, 58, cx + 8, 63), NST, box(cx - 9, 58, cx + 8, 63, 0.7, 0.5, 0.25, 1, 2))
    robe = m_poly(c, [(cx - 4, 22), (cx + 5, 22), (cx + 9, 40), (cx + 10, 58), (cx - 10, 58), (cx - 8, 38)])
    c.paint(robe, NST, noise_mod(lambda x, y: clamp(0.78 - 0.5 * (x - cx + 10) / 20 + 0.1 * math.sin(x * 0.9 + y * 0.12)), 0.08, 7))
    for x0 in (cx - 5, cx - 1, cx + 3):   # robe folds
        c.paint(m_line(c, [(x0, 30), (x0 + (x0 - cx) * 0.3, 57)], 1), NST, 0.12)
    hood = m_ell(c, cx - 6, 12, cx + 6, 27)
    c.paint(hood, NST, lambda x, y: clamp(0.85 - 0.45 * (x - cx + 6) / 12))
    c.paint(m_ell(c, cx - 2, 18, cx + 5, 27), NST, 0.02)                                               # the bowed face in shadow
    c.paint(m_ell(c, cx - 4, 30, cx + 3, 36), NST, 0.7)                                                # clasped hands
    c.set(cx + 1, 22, GHOST[3]); c.set(cx + 3, 22, GHOST[3])                                           # a glint of tears
    for y in (24, 27, 30):
        c.set(cx + 2 + (y % 2), y, GHOST[2])
    c.outline()
    return c.im


def nv_cage(f, w=48, h=64):
    c = cv(w, h); cx = 24
    for y in range(0, 14, 3):                           # chain
        c.paint(m_ell(c, cx - 1, y, cx + 1, y + 3), IRON, 0.6)
    c.paint(m_poly(c, [(cx - 8, 18), (cx + 8, 18), (cx, 12)]), IRON, 0.45)
    body = m_ell(c, cx - 9, 16, cx + 9, 46)
    inner = m_ell(c, cx - 7, 18, cx + 7, 44)
    skel = cv(w, h)
    skull(skel, cx - 4, 22, BONE, 0.8)
    skel.paint(m_rect(skel, cx - 1, 30, cx, 40), BONE, 0.5)
    for y in (32, 35, 38):
        skel.paint(m_line(skel, [(cx - 4, y), (cx + 3, y)], 1), BONE, 0.45)
    skel.paint(m_line(skel, [(cx - 4, 32), (cx - 6, 42)], 1), BONE, 0.5)
    c.paste(skel, 0, 0)
    for x in range(cx - 8, cx + 9, 3):                   # bars
        for y in range(16, 47):
            mm = body.load()
            if mm[x, y]:
                c.set(x, y, IRON[4 if x < cx else 2])
    for y in (18, 31, 44):
        for x in range(cx - 9, cx + 10):
            if body.load()[x, y]:
                c.set(x, y, IRON[3])
    c.paint(m_rect(c, cx - 2, 46, cx + 1, 48), IRON, 0.4)
    c.outline()
    return c.im


def nv_rack(f, w=48, h=64):
    """a headsman's weapon rack: three great axes stood upright, a chain-flail hung from the end"""
    c = cv(w, h); cx = 24
    for x in (cx - 15, cx + 14):
        c.paint(m_rect(c, x - 1, 30, x + 1, 63), WOOD, cyl(x - 1, x + 1, 0.3, 0.8))
        c.paint(m_rect(c, x - 2, 29, x + 2, 30), IRON, 0.5)
    c.paint(m_rect(c, cx - 16, 33, cx + 15, 34), WOOD, 0.6)
    c.paint(m_rect(c, cx - 16, 56, cx + 15, 58), WOOD, 0.45)
    for i, ax in enumerate((cx - 8, cx, cx + 8)):
        c.paint(m_rect(c, ax, 20, ax + 1, 60), WOOD, cyl(ax, ax + 1, 0.35, 0.75))                      # haft
        blade = m_poly(c, [(ax + 2, 20), (ax + 7, 17), (ax + 10, 22), (ax + 10, 30), (ax + 7, 34), (ax + 2, 31)])
        c.paint(blade, IRON, lambda x, y, ax=ax: clamp(0.85 - 0.06 * (x - ax) - 0.01 * (y - 17)))
        c.paint(m_line(c, [(ax + 10, 22), (ax + 10, 30)], 1), IRON, 0.95)                               # the honed edge
        c.set(ax + 6, 27, RUST[3]); c.set(ax + 5, 29, RUST[2])
        c.set(ax, 19, IRON[5])
    for y in range(35, 55, 2):                           # a chain-flail hanging off the end
        c.paint(m_ell(c, cx + 13, y, cx + 15, y + 2), IRON, 0.55)
    c.paint(m_ell(c, cx + 11, 54, cx + 17, 60), IRON, 0.5)
    skull(c, cx - 19, 22, BONE, 0.85)
    c.outline()
    return c.im


def nv_dummy(f, w=48, h=64):
    c = cv(w, h); cx = 24
    c.paint(m_rect(c, cx - 1, 20, cx + 1, 63), WOOD, cyl(cx - 1, cx + 1, 0.3, 0.8))
    c.paint(m_rect(c, cx - 11, 30, cx + 10, 32), WOOD, 0.55)
    c.paint(m_poly(c, [(cx - 7, 28), (cx + 7, 28), (cx + 6, 50), (cx - 6, 50)]), HIDE, noise_mod(cyl(cx - 7, cx + 7, 0.2, 0.75), 0.15, 9))
    for y in (33, 38, 43):
        c.paint(m_line(c, [(cx - 6, y), (cx + 6, y)], 1), HIDE, 0.12)
    c.paint(m_ell(c, cx - 6, 14, cx + 6, 27), IRON, lambda x, y: clamp(0.75 - 0.5 * (x - cx + 6) / 12 - 0.2 * (y - 14) / 13))   # a rusted helm
    c.paint(m_rect(c, cx - 5, 20, cx + 4, 21), IRON, 0.02)
    for x, y in [(cx - 3, 17), (cx + 2, 24), (cx - 5, 23), (cx + 4, 16)]:
        c.set(x, y, RUST[3])
    c.paint(m_line(c, [(cx + 8, 31), (cx + 16, 44)], 1), IRON, 0.6)   # a notched blade stuck in its shoulder
    c.outline()
    return c.im


def nv_bunk(f, w=48, h=64):
    c = cv(w, h)
    c.paint(m_rect(c, 2, 54, 45, 58), BONE, box(2, 54, 45, 58, 0.8, 0.55, 0.3, 1, 2))
    for x in (2, 44):
        c.paint(m_rect(c, x, 46, x + 1, 63), BONE, 0.6)
    c.paint(m_rect(c, 4, 51, 43, 53), LINEN, lambda x, y: clamp(0.35 + 0.1 * math.sin(x * 0.7)))
    skull(c, 34, 44, BONE, 0.8)
    c.outline()
    return c.im


def nv_drum(f, w=48, h=64):
    c = cv(w, h); cx = 24
    body = m_rect(c, cx - 12, 44, cx + 11, 61)
    c.paint(body, HIDE, noise_mod(cyl(cx - 12, cx + 11, 0.2, 0.85), 0.1, 11))
    c.paint(m_ell(c, cx - 12, 40, cx + 11, 48), HIDE, lambda x, y: clamp(0.9 - 0.25 * (x - cx + 12) / 24))
    for i, x in enumerate(range(cx - 11, cx + 12, 4)):   # lacing
        c.paint(m_line(c, [(x, 46), (x + 2, 60)], 1), BONE, 0.7)
    for y in (46, 60):
        c.paint(m_rect(c, cx - 12, y, cx + 11, y + 1), BONE, lambda x, y: 0.8 - 0.4 * (x - cx + 12) / 24)
    c.paint(m_rect(c, cx - 10, 62, cx - 8, 63), BONE, 0.5); c.paint(m_rect(c, cx + 7, 62, cx + 9, 63), BONE, 0.5)
    for sx in (-6, 7):                                    # two femur mallets
        c.paint(m_line(c, [(cx + sx, 39), (cx + sx * 2, 26)], 2), BONE, 0.75)
        c.paint(m_ell(c, cx + sx * 2 - 2, 23, cx + sx * 2 + 2, 27), BONE, 0.85)
    c.outline()
    return c.im


def nv_axestump(f, w=48, h=64):
    """the headsman's block: a scarred oak stump, his axe sunk in it, a basket at its foot"""
    c = cv(w, h); cx = 22
    c.paint(m_poly(c, [(cx - 10, 63), (cx - 8, 48), (cx + 8, 48), (cx + 10, 63)]), WOOD, noise_mod(cyl(cx - 10, cx + 10, 0.2, 0.8), 0.1, 13))
    c.paint(m_ell(c, cx - 8, 45, cx + 8, 51), WOOD, lambda x, y: clamp(0.85 - 0.04 * abs(x - cx)))
    for r_ in (2, 4, 6):
        for a in range(0, 360, 18):
            c.set(cx + r_ * math.cos(math.radians(a)), 48 + r_ * 0.35 * math.sin(math.radians(a)), WOOD[3])
    for y in range(52, 62, 3):
        c.paint(m_line(c, [(cx - 6, y), (cx - 2, y + 1)], 1), WOOD, 0.2)
    c.paint(m_line(c, [(cx + 1, 47), (cx + 15, 24)], 2), WOOD, 0.6)                                     # the haft, leaning out
    blade = m_poly(c, [(cx - 5, 49), (cx - 7, 42), (cx - 2, 38), (cx + 6, 39), (cx + 4, 48)])
    c.paint(blade, IRON, lambda x, y: clamp(0.9 - (x - cx + 7) * 0.035 - (y - 38) * 0.02))
    c.paint(m_line(c, [(cx - 7, 42), (cx - 5, 49)], 1), RUST, 0.55)
    c.paint(m_poly(c, [(cx + 12, 63), (cx + 13, 55), (cx + 22, 55), (cx + 23, 63)]), WOOD, noise_mod(cyl(cx + 12, cx + 23, 0.2, 0.6), 0.2, 14))   # the basket
    for x in range(cx + 13, cx + 23, 2):
        c.paint(m_line(c, [(x, 56), (x, 62)], 1), WOOD, 0.15)
    for x, y in [(cx - 7, 50), (cx - 9, 53), (cx + 7, 52)]:
        c.set(x, y, RUST[2])
    c.outline()
    return c.im


def nv_kingskull(v):
    def fn(f, w=48, h=64):
        c = cv(w, h); cx = 24
        c.paint(m_rect(c, cx - 8, 52, cx + 7, 63), NST, box(cx - 8, 52, cx + 7, 63, 0.8, 0.55, 0.28, 1, 2))
        c.paint(m_rect(c, cx - 10, 50, cx + 9, 52), NST, 0.85)
        skull(c, cx - 4, 41, BONE, 1.0, crown=GOLD if v == 0 else BONE)
        if v == 1:
            c.paint(m_line(c, [(cx - 7, 49), (cx + 7, 44)], 1), IRON, 0.7)                             # a broken sceptre
        for yy in range(54, 62, 2):
            c.set(cx - 5 + (yy % 4), yy, GHOST[2])
        c.outline()
        return c.im
    return fn


# ============================================================================ DUNES (48x64)
def du_jars(v):
    def fn(f, w=48, h=64):
        c = cv(w, h)
        specs = [(16, 63, 9, 18), (30, 63, 7, 13), (24, 63, 5, 9)] if v == 0 else [(20, 63, 10, 20), (33, 63, 6, 11)]
        for cx, base, rw, hh in specs:
            m = m_or(m_ell(c, cx - rw, base - hh, cx + rw, base), m_rect(c, cx - rw // 3, base - hh - 4, cx + rw // 3, base - hh + 2))
            c.paint(m, CLAY, noise_mod(cyl(cx - rw, cx + rw, 0.18, 0.9), 0.08, cx))
            c.paint(m_rect(c, cx - rw // 3 - 1, base - hh - 5, cx + rw // 3 + 1, base - hh - 4), CLAY, 0.85)
            yb = base - hh // 2
            for x in range(cx - rw + 1, cx + rw):
                if m.load()[x, yb]:
                    c.set(x, yb, LAPIS[3] if x % 3 else GOLD[4])
                if m.load()[x, yb - 2]:
                    c.set(x, yb - 2, CLAY[1])
        c.outline()
        return c.im
    return fn


def du_crates(f, w=48, h=64):
    c = cv(w, h)
    for x0, y0, s in [(4, 46, 17), (21, 50, 13), (10, 32, 13)]:
        c.paint(m_rect(c, x0, y0, x0 + s, y0 + s), WOOD, box(x0, y0, x0 + s, y0 + s, 0.85, 0.6, 0.3, 2, 2))
        c.paint(m_line(c, [(x0, y0), (x0 + s, y0 + s)], 1), WOOD, 0.3)
        for yy in (y0 + 2, y0 + s - 2):
            c.paint(m_rect(c, x0, yy, x0 + s, yy), WOOD, 0.35)
    c.paint(m_ell(c, 34, 44, 46, 63), LINEN, noise_mod(cyl(34, 46, 0.2, 0.85), 0.12, 21))   # a bundle, roped
    c.paint(m_line(c, [(35, 50), (45, 52)], 1), TRUNK, 0.5); c.paint(m_line(c, [(35, 57), (45, 58)], 1), TRUNK, 0.5)
    c.outline()
    return c.im


def du_banner(f, w=48, h=64):
    c = cv(w, h); px_ = 14
    c.paint(m_rect(c, px_ - 1, 4, px_ + 1, 63), TRUNK, cyl(px_ - 1, px_ + 1, 0.3, 0.85))
    c.paint(m_ell(c, px_ - 3, 1, px_ + 3, 6), GOLD, 0.8)
    pts = []
    for i in range(0, 13):
        y = 8 + i * 3
        pts.append((px_ + 2 + 22 + math.sin(f * 1.4 + i * 0.5) * 2 - (i > 9) * (i - 9) * 2, y))
    cloth = m_poly(c, [(px_ + 2, 8)] + pts + [(px_ + 2, 46)])
    c.paint(cloth, LAPIS, lambda x, y: clamp(0.55 - (x - px_) * 0.012 + 0.2 * math.sin(f * 1.4 + y * 0.18)))
    for x in range(px_ + 2, px_ + 25):
        c.set(x, 9, GOLD[3]); c.set(x, 11, GOLD[2])
    glow_dot(c, px_ + 12 + math.sin(f * 1.4 + 3) * 1, 24, 5, GOLD, 1.0)                  # the sun disc
    for a in range(0, 360, 45):
        c.set(px_ + 12 + 8 * math.cos(math.radians(a)), 24 + 8 * math.sin(math.radians(a)), GOLD[3])
    for i in range(3):   # torn fringe
        c.set(px_ + 5 + i * 7, 47, LAPIS[1])
    c.outline()
    return c.im


def du_reeds(v):
    def fn(f, w=48, h=64):
        c = cv(w, h)
        n = [9, 7, 11][v]
        for i in range(n):
            x0 = 8 + i * (32 / n) + h01(i, v, 3) * 3
            hh = 18 + h01(i, v, 5) * 22
            sw = math.sin(f * 1.3 + i * 0.9) * (1.5 + hh * 0.04)
            pts = [(x0, 63), (x0 + sw * 0.5, 63 - hh * 0.5), (x0 + sw, 63 - hh)]
            c.paint(m_line(c, pts, 1), PALM, 0.35 + 0.4 * h01(i, v, 7))
            if h01(i, v, 9) < 0.45:   # papyrus heads
                hx, hy = x0 + sw, 63 - hh
                c.paint(m_poly(c, [(hx, hy), (hx - 4, hy - 5), (hx + 4, hy - 5)]), PALM, 0.7)
            elif h01(i, v, 9) < 0.7:
                c.paint(m_ell(c, x0 + sw - 1, 63 - hh - 5, x0 + sw + 1, 63 - hh + 1), TRUNK, 0.55)   # a reed mace
        c.outline()
        return c.im
    return fn


def du_scarabidol(f, w=48, h=64):
    c = cv(w, h); cx = 24
    c.paint(m_rect(c, cx - 9, 52, cx + 8, 63), SSTONE, box(cx - 9, 52, cx + 8, 63, 0.85, 0.6, 0.3, 1, 2))
    body = m_ell(c, cx - 9, 34, cx + 8, 52)
    c.paint(body, GOLD, lambda x, y: clamp(0.95 - 0.55 * math.hypot(x - cx + 4, y - 38) / 14))
    c.paint(m_line(c, [(cx, 36), (cx, 51)], 1), GOLD, 0.15)
    c.paint(m_ell(c, cx - 4, 29, cx + 3, 36), GOLD, 0.7)
    glow_dot(c, cx, 25, 4, AMBER, 1.0)                    # the sun it pushes
    for s in (-1, 1):
        for k in range(3):
            c.paint(m_line(c, [(cx + s * 7, 40 + k * 4), (cx + s * 12, 42 + k * 5)], 1), GOLD, 0.4)
    c.outline()
    return c.im


def du_hoard(f, w=48, h=64):
    c = cv(w, h)
    c.paint(m_ell(c, 2, 50, 45, 70), GOLD, lambda x, y: clamp(0.85 - (y - 50) * 0.02 + 0.15 * h01(x, y, 4)))
    for i in range(40):
        x, y = 4 + h01(i, 1, 2) * 40, 52 + h01(i, 2, 2) * 11
        c.set(x, y, GOLD[5] if i % 3 else GOLD[1])
    c.paint(m_poly(c, [(28, 38), (36, 38), (34, 45), (33, 50), (35, 52), (29, 52), (31, 50), (30, 45)]), GOLD, cyl(28, 36, 0.3, 0.95))
    c.paint(m_rect(c, 6, 44, 16, 52), WOOD, box(6, 44, 16, 52, 0.8, 0.55, 0.3, 1, 1))   # a little casket
    c.paint(m_rect(c, 6, 44, 16, 45), GOLD, 0.7)
    for x, y in [(12, 40), (38, 36), (22, 48)]:
        c.set(x, y, AMBER[5]); c.set(x - 1, y, AMBER[3]); c.set(x + 1, y, AMBER[3]); c.set(x, y - 1, AMBER[3]); c.set(x, y + 1, AMBER[3])
    c.outline()
    return c.im


def du_sarcophagus(v):
    def fn(f, w=48, h=64):
        c = cv(w, h); cx = 24
        body = m_or(m_ell(c, cx - 8, 14, cx + 7, 32), m_poly(c, [(cx - 8, 24), (cx + 7, 24), (cx + 6, 63), (cx - 7, 63)]))
        ramp_ = GOLD if v == 0 else LINEN
        c.paint(body, ramp_, noise_mod(lambda x, y: clamp(0.85 - 0.5 * (x - cx + 8) / 16), 0.06, 22))
        c.paint(m_ell(c, cx - 5, 17, cx + 4, 28), GOLD if v else SSTONE, 0.75)                     # the face
        c.set(cx - 2, 22, K); c.set(cx + 2, 22, K); c.set(cx - 2, 21, LAPIS[2]); c.set(cx + 2, 21, LAPIS[2])
        for y in range(14, 34, 2):                                                                  # the striped headdress
            for x in range(cx - 8, cx + 8):
                if body.load()[x, y] and not (cx - 5 <= x <= cx + 4 and 17 <= y <= 28):
                    c.set(x, y, LAPIS[3] if (y // 2) % 2 else GOLD[4])
        c.paint(m_poly(c, [(cx - 6, 36), (cx + 5, 36), (cx + 4, 40), (cx - 5, 40)]), LAPIS, 0.5)  # crossed arms / collar
        c.paint(m_line(c, [(cx - 5, 38), (cx + 4, 44)], 1), GOLD, 0.8); c.paint(m_line(c, [(cx + 4, 38), (cx - 5, 44)], 1), GOLD, 0.6)
        for y in range(46, 62, 3):
            for x in range(cx - 4, cx + 4):
                if h01(x, y, 23) < 0.6: c.set(x, y, LAPIS[1] if v == 0 else LINEN[2])
        c.outline()
        return c.im
    return fn


def du_brazier(f, w=48, h=64):
    c = cv(w, h); cx = 24
    for s in (-1, 1):
        c.paint(m_line(c, [(cx + s * 2, 44), (cx + s * 8, 63)], 2), GOLD, 0.5)
    c.paint(m_poly(c, [(cx - 11, 38), (cx + 10, 38), (cx + 6, 46), (cx - 7, 46)]), GOLD, cyl(cx - 11, cx + 10, 0.25, 0.9))
    c.paint(m_rect(c, cx - 11, 37, cx + 10, 38), GOLD, 0.95)
    for i in range(3):
        flame(c, cx - 4 + i * 4, 37, 3.2 + math.sin(f * 2 + i) * 0.7, f + i, AMBER, seed=i * 3)
    c.outline()
    return c.im


def du_jackal(f, w=48, h=64):
    c = cv(w, h); cx = 24
    J = ramp("08080c", "121119", "1d1b27", "2c2838", "3f3a50", "5a5470")
    c.paint(m_rect(c, cx - 11, 54, cx + 10, 63), SSTONE, box(cx - 11, 54, cx + 10, 63, 0.85, 0.6, 0.3, 1, 2))
    body = m_poly(c, [(cx - 8, 54), (cx - 9, 40), (cx - 3, 34), (cx + 5, 34), (cx + 9, 42), (cx + 9, 54)])
    c.paint(body, J, lambda x, y: clamp(0.8 - 0.55 * (x - cx + 9) / 18))
    head = m_poly(c, [(cx - 3, 34), (cx - 2, 22), (cx + 2, 20), (cx + 11, 25), (cx + 3, 30), (cx + 4, 34)])
    c.paint(head, J, lambda x, y: clamp(0.85 - 0.45 * (x - cx + 3) / 14))
    c.paint(m_poly(c, [(cx - 3, 23), (cx - 5, 10), (cx, 21)]), J, 0.7); c.paint(m_poly(c, [(cx + 1, 21), (cx + 1, 9), (cx + 4, 22)]), J, 0.5)
    c.set(cx + 4, 24, AMBER[3]); c.set(cx + 5, 24, AMBER[2])
    for y in (41, 44, 47):
        c.paint(m_line(c, [(cx - 7, y), (cx + 8, y)], 1), GOLD, 0.7)
    c.outline()
    return c.im


def du_goldbug():
    """xsb_bug 16x12: the golden scarab (walk 4, dig 3)"""
    fr = []
    for i in range(7):
        c = Canvas(16, 12); cx = 8
        dig = i >= 4
        y0 = 3 + (i - 4) * 2 if dig else 3
        body = m_ell(c, cx - 5, y0, cx + 4, y0 + 7)
        c.paint(body, GOLD, lambda x, y: clamp(0.95 - 0.6 * math.hypot(x - cx + 2, y - y0 - 2) / 7))
        c.paint(m_line(c, [(cx, y0 + 1), (cx, y0 + 6)], 1), GOLD, 0.2)
        c.paint(m_ell(c, cx + 3, y0 + 2, cx + 7, y0 + 5), GOLD, 0.55)
        if not dig:
            for k in range(3):
                lx = cx - 3 + k * 3
                off = (1 if (i + k) % 2 else -1)
                c.set(lx + off, y0 + 8, GOLD[2]); c.set(lx, y0 + 7, GOLD[1])
        else:
            for k in range(4):
                c.set(cx - 5 + k * 3 + (i % 2), 11 - (k % 2), SAND[6])
        c.outline()
        fr.append(c.im)
    return fr


# ============================================================================ TALL (64x112)
def tall_palm(v):
    def fn(f, w=64, h=112):
        c = cv(w, h)
        base = 32 + [0, -4, 5][v]
        lean = [7, -9, 3][v]
        top = (base + lean, [30, 38, 26][v])
        segs = 16
        for i in range(segs):
            t0, t1 = i / segs, (i + 1) / segs
            x0 = base + lean * t0 ** 1.6; y0 = 111 - (111 - top[1]) * t0
            x1 = base + lean * t1 ** 1.6; y1 = 111 - (111 - top[1]) * t1
            rw = 3.4 - t0 * 1.3
            m = m_poly(c, [(x0 - rw, y0), (x0 + rw, y0), (x1 + rw, y1), (x1 - rw, y1)])
            c.paint(m, TRUNK, lambda x, y, xm=(x0 + x1) / 2, r=rw: clamp(0.8 - 0.55 * (x - xm + r) / (2 * r) - (0.2 if int(y) % 5 == 0 else 0)))
        tx, ty = top
        fronds = [(-160, 30), (-130, 34), (-100, 26), (-60, 28), (-25, 33), (5, 30), (35, 26), (-80, 20), (-200, 22)]
        for k, (ang, L) in enumerate(fronds):
            a0 = math.radians(ang + math.sin(f * 1.1 + k) * 4)
            pts = []
            for s in range(9):
                t = s / 8
                ax = tx + math.cos(a0) * L * t
                ay = ty + math.sin(a0) * L * t + (t ** 2) * L * 0.55
                pts.append((ax, ay))
            for s in range(8):   # leaflets hang off the rib
                (ax, ay), (bx, by) = pts[s], pts[s + 1]
                for side in (-1, 1):
                    ll = 7 * (1 - s / 9)
                    c.paint(m_line(c, [(ax, ay), (ax + side * 1.5, ay + ll)], 1), PALM, 0.3 + 0.45 * (1 - s / 8) + 0.1 * side)
            c.paint(m_line(c, pts, 1), PALM, 0.65)
        c.paint(m_ell(c, tx - 3, ty - 2, tx + 3, ty + 3), TRUNK, 0.4)
        for i in range(3):   # dates
            c.set(tx - 2 + i * 2, ty + 4, CLAY[4]); c.set(tx - 1 + i * 2, ty + 5, CLAY[2])
        c.outline()
        return c.im
    return fn


def tall_palmdead(f, w=64, h=112):
    c = cv(w, h); x = 30
    for i in range(12):
        y0, y1 = 111 - i * 5, 111 - (i + 1) * 5
        xm = x + i * 0.6
        m = m_rect(c, xm - 3, y1, xm + 3, y0)
        c.paint(m, TRUNK, lambda xx, yy, xm=xm: clamp(0.65 - 0.45 * (xx - xm + 3) / 6 - (0.18 if int(yy) % 5 == 0 else 0)))
    c.paint(m_poly(c, [(x + 3, 51), (x + 10, 46), (x + 8, 53)]), TRUNK, 0.35)          # the snapped crown
    for k, (a, L) in enumerate([(200, 16), (160, 12), (230, 14)]):
        aa = math.radians(a)
        c.paint(m_line(c, [(x + 7, 55), (x + 7 + math.cos(aa) * L, 55 + math.sin(aa) * L * -0.2 + L * 0.8)], 1), TRUNK, 0.3)
    c.outline()
    return c.im


def tall_obelisk(f, w=64, h=112):
    c = cv(w, h); cx = 32
    shaft = m_poly(c, [(cx - 7, 111), (cx + 6, 111), (cx + 4, 24), (cx - 5, 24)])
    c.paint(shaft, SSTONE, noise_mod(lambda x, y: clamp(0.85 - 0.55 * (x - cx + 7) / 13 - 0.1 * (y - 24) / 87), 0.08, 31))
    c.paint(m_poly(c, [(cx - 5, 24), (cx + 4, 24), (cx, 14)]), GOLD, lambda x, y: clamp(0.95 - 0.4 * (x - cx + 5) / 9))
    for y in range(30, 104, 6):   # hieroglyph columns
        for x in range(cx - 3, cx + 2, 2):
            if h01(x, y, 32) < 0.7:
                c.set(x, y, SSTONE[1]); c.set(x, y + 1, SSTONE[2] if h01(x, y, 33) < 0.5 else SSTONE[1])
    c.paint(m_rect(c, cx - 9, 106, cx + 8, 111), SSTONE, box(cx - 9, 106, cx + 8, 111, 0.85, 0.6, 0.3, 1, 2))
    c.outline()
    return c.im


def tall_ruincol(v):
    def fn(f, w=64, h=112):
        c = cv(w, h); cx = 32
        top = [44, 62][v]
        c.paint(m_rect(c, cx - 7, top, cx + 6, 105), SSTONE, noise_mod(cyl(cx - 7, cx + 6, 0.2, 0.9), 0.1, 40 + v))
        for x in range(cx - 5, cx + 5, 3):
            c.paint(m_line(c, [(x, top + 2), (x, 104)], 1), SSTONE, 0.22)
        c.paint(m_poly(c, [(cx - 7, top), (cx - 2, top - 5), (cx + 2, top - 1), (cx + 6, top - 4), (cx + 6, top)]), SSTONE, 0.75)   # snapped top
        c.paint(m_rect(c, cx - 10, 105, cx + 9, 111), SSTONE, box(cx - 10, 105, cx + 9, 111, 0.85, 0.6, 0.3, 1, 2))
        if v == 0:
            c.paint(m_poly(c, [(cx + 8, 111), (cx + 22, 104), (cx + 28, 108), (cx + 16, 111)]), SSTONE, 0.5)   # a fallen drum
        for y in range(top + 10, 100, 9):   # lapis-painted bands, flaking
            for x in range(cx - 6, cx + 6):
                if h01(x, y, 41) < 0.7: c.set(x, y, LAPIS[2])
        c.outline()
        return c.im
    return fn


# ============================================================================ BIG (192x128 backdrops, painted into the back layer)
def big_catafalque(f, w=192, h=128):
    c = cv(w, h); cx = 96
    # a pall of royal purple hung between the inner spires, behind the bier
    pall = m_poly(c, [(cx - 46, 30), (cx + 46, 30), (cx + 44, 70), (cx + 30, 82), (cx + 10, 76), (cx - 10, 84), (cx - 30, 76), (cx - 44, 84)])
    c.paint(pall, PURP, lambda x, y: clamp(0.42 - 0.2 * (y - 30) / 54 + 0.12 * math.sin(x * 0.45) - 0.1 * abs(x - cx) / 46))
    for x in range(cx - 46, cx + 47):
        c.set(x, 30, GOLD[3]); c.set(x, 31, GOLD[1])
    for k in range(-2, 3):   # the sigil of the bells, stitched in gold thread
        c.paint(m_poly(c, [(cx + k * 18 - 3, 40), (cx + k * 18 + 3, 40), (cx + k * 18 + 6, 52), (cx + k * 18 - 6, 52)]), GOLD, 0.35 + 0.1 * (k == 0))
    # stepped plinth
    for i, (hw, y0, y1) in enumerate([(74, 118, 127), (66, 110, 117), (58, 100, 109)]):
        c.paint(m_rect(c, cx - hw, y0, cx + hw, y1), NST, box(cx - hw, y0, cx + hw, y1, 0.8, 0.55, 0.3, 1, 3))
    for x in range(cx - 56, cx + 57, 14):   # a frieze of skulls
        skull(c, x - 4, 101, BONE, 0.7)
    # the bier and the king's effigy (carved stone, kept dark so the ghost-light models it)
    c.paint(m_rect(c, cx - 54, 88, cx + 54, 99), NST, box(cx - 54, 88, cx + 54, 99, 0.9, 0.62, 0.3, 2, 3))
    c.paint(m_rect(c, cx - 50, 91, cx + 50, 96), PURP, lambda x, y: clamp(0.45 + 0.15 * math.sin(x * 0.4)))
    STONE = ramp("15151f", "222232", "36354b", "4c4a62", "6a6782", "8c88a2", "b0acc4")
    body = m_poly(c, [(cx - 36, 88), (cx - 34, 80), (cx - 20, 76), (cx + 26, 77), (cx + 42, 80), (cx + 46, 88)])
    c.paint(body, STONE, noise_mod(lambda x, y: clamp(0.72 - 0.5 * (y - 76) / 12), 0.05, 51))
    for x in range(cx - 30, cx + 44, 6):   # folds of the carved shroud
        c.paint(m_line(c, [(x, 79), (x + 3, 87)], 1), STONE, 0.25)
    c.paint(m_ell(c, cx - 50, 75, cx - 35, 88), STONE, lambda x, y: clamp(0.85 - 0.5 * math.hypot(x - cx + 45, y - 78) / 10))   # the head
    c.set(cx - 46, 81, STONE[1]); c.set(cx - 43, 81, STONE[1]); c.paint(m_line(c, [(cx - 46, 84), (cx - 42, 84)], 1), STONE, 0.2)
    for i, hh in enumerate([4, 2, 6, 2, 6, 2, 4]):   # the crown
        c.paint(m_rect(c, cx - 50 + i * 2, 75 - hh, cx - 49 + i * 2, 76), GOLD, 0.55 + 0.05 * (hh > 3))
    c.paint(m_rect(c, cx - 16, 76, cx + 36, 77), IRON, 0.55)                                 # the greatsword laid on him
    c.set(cx + 37, 76, IRON[4])
    c.paint(m_rect(c, cx - 22, 72, cx - 20, 80), GOLD, 0.5)                                  # its crossguard
    c.paint(m_ell(c, cx - 28, 74, cx - 21, 80), STONE, 0.6)                                   # hands on the hilt
    c.paint(m_poly(c, [(cx + 44, 80), (cx + 50, 76), (cx + 50, 88), (cx + 46, 88)]), STONE, 0.45)   # feet
    # four tall candle-spires with ghost fire
    for sx in (-66, -46, 46, 66):
        x = cx + sx; top = 22 if abs(sx) > 50 else 30
        c.paint(m_rect(c, x - 2, top, x + 1, 99), IRON, cyl(x - 2, x + 1, 0.2, 0.75))
        c.paint(m_poly(c, [(x - 5, top), (x + 4, top), (x, top - 5)]), IRON, 0.55)
        for yy in range(top + 8, 96, 14):
            c.paint(m_rect(c, x - 3, yy, x + 2, yy + 1), IRON, 0.45)
        flame(c, x, top - 5, 3.2, f + sx, GHOST, seed=sx)
    for sx0, sx1, t0, t1 in ((-66, -46, 22, 30), (46, 66, 30, 22)):   # chains swagged between the spires
        for k in range(21):
            t = k / 20
            x = cx + sx0 + (sx1 - sx0) * t
            y = t0 + (t1 - t0) * t + math.sin(t * math.pi) * 9
            c.set(x, y, IRON[4]); c.set(x, y + 1, IRON[2])
    c.outline()
    return c.im


def big_tombwall(f, w=192, h=128):
    """a street of mausoleum fronts in deep shadow: pediments, columns, barred doors lit faintly blue"""
    c = cv(w, h)
    for i, (x0, ww, top) in enumerate([(4, 56, 34), (66, 60, 18), (132, 56, 40)]):
        x1 = x0 + ww
        c.paint(m_rect(c, x0, top + 10, x1, 127), NST, noise_mod(lambda x, y, x0=x0, x1=x1: clamp(0.5 - 0.3 * (x - x0) / (x1 - x0) - 0.12 * (y - top) / 90), 0.08, 60 + i))
        c.paint(m_poly(c, [(x0 - 3, top + 10), (x1 + 3, top + 10), ((x0 + x1) / 2, top)]), NST, lambda x, y: clamp(0.62 - 0.02 * abs(x - (x0 + x1) / 2)))
        c.paint(m_rect(c, x0 - 3, top + 10, x1 + 3, top + 12), NST, 0.7)
        for cx_ in (x0 + 5, x1 - 5):
            c.paint(m_rect(c, cx_ - 2, top + 13, cx_ + 2, 120), NST, cyl(cx_ - 2, cx_ + 2, 0.18, 0.7))
        dx0, dx1 = (x0 + x1) // 2 - 9, (x0 + x1) // 2 + 9
        c.paint(m_or(m_rect(c, dx0, top + 40, dx1, 120), m_ell(c, dx0, top + 31, dx1, top + 49)), GHOST,
                lambda x, y: clamp(0.08 + 0.3 * (y - top - 30) / 90))
        for x in range(dx0 + 2, dx1, 3):
            for y in range(top + 36, 121):
                if c.get(x, y)[3]: c.set(x, y, IRON[2])
        skull(c, (x0 + x1) // 2 - 4, top + 14, BONE, 0.6)
        c.paint(m_rect(c, x0 - 2, 120, x1 + 2, 127), NST, 0.6)
    c.outline(NST[0])
    return c.im


def big_dirgeslab(f, w=192, h=128):
    """the dirge: a carved stave, five lines for the five bells (lowest line = the lowest-hanging bell), six notes"""
    c = cv(w, h); x0, x1, y0, y1 = 60, 131, 44, 127
    c.paint(m_rect(c, x0, y0, x1, y1), NST, noise_mod(lambda x, y: clamp(0.7 - 0.25 * (x - x0) / (x1 - x0) - 0.15 * (y - y0) / (y1 - y0)), 0.06, 70))
    c.paint(m_poly(c, [(x0 - 3, y0), (x1 + 3, y0), ((x0 + x1) / 2, y0 - 12)]), NST, 0.75)
    c.paint(m_rect(c, x0 + 3, y0 + 3, x1 - 3, y0 + 3), NST, 0.2)
    # a bell carved in the pediment
    c.paint(m_poly(c, [(95, 35), (97, 35), (101, 43), (91, 43)]), BONE, 0.6)
    lines = [98, 91, 84, 77, 70]    # line 0 (lowest) .. line 4 (highest)
    for ly in lines:
        for x in range(x0 + 7, x1 - 6):
            c.set(x, ly, BONE[3] if x % 7 else BONE[2])
    notes = [0, 2, 1, 4, 3, 0]      # the dirge: b2 b1 b4 b3 b5 b2
    for i, n in enumerate(notes):
        nx, ny = x0 + 14 + i * 9, lines[n]
        c.paint(m_poly(c, [(nx - 1, ny - 4), (nx + 1, ny - 4), (nx + 3, ny + 1), (nx - 3, ny + 1)]), GHOST, 0.75)   # bell-shaped note
        c.set(nx, ny + 2, GHOST[5])
        glow_dot(c, nx, ny - 1, 2.2, GHOST, 0.5)
    for i in range(6):   # a procession of mourners under the stave
        mx = x0 + 10 + i * 10
        c.paint(m_poly(c, [(mx - 2, 108), (mx + 2, 108), (mx + 3, 118), (mx - 3, 118)]), NST, 0.2)
        c.paint(m_ell(c, mx - 2, 104, mx + 2, 108), NST, 0.25)
    c.outline()
    return c.im


def big_fence(f, w=192, h=128):
    """wrought-iron cemetery railings with stone posts (the Cemetery Gate)"""
    c = cv(w, h)
    for px_ in range(8, 192, 46):
        c.paint(m_rect(c, px_ - 4, 60, px_ + 4, 127), NST, cyl(px_ - 4, px_ + 4, 0.2, 0.75))
        c.paint(m_rect(c, px_ - 6, 56, px_ + 6, 60), NST, 0.8)
        skull(c, px_ - 4, 47, BONE, 0.75)
    for x in range(0, 192, 5):
        if any(abs(x - p) < 7 for p in range(8, 192, 46)):
            continue
        top = 74 + (3 if (x // 5) % 2 else 0)
        c.paint(m_rect(c, x, top, x, 124), IRON, 0.45)
        c.paint(m_poly(c, [(x - 1, top), (x + 1, top), (x, top - 4)]), IRON, 0.7)
    for y in (84, 118):
        c.paint(m_rect(c, 0, y, 191, y + 1), IRON, 0.4)
    c.outline(NST[0])
    return c.im


def big_wagon(f, w=192, h=128):
    """a caravan wagon, one wheel smashed, its hood torn, half sunk in the sand"""
    c = cv(w, h); cx = 96
    c.paint(m_rect(c, cx - 58, 84, cx + 50, 100), WOOD, box(cx - 58, 84, cx + 50, 100, 0.8, 0.55, 0.3, 2, 3))   # the bed
    for x in range(cx - 56, cx + 50, 9):
        c.paint(m_rect(c, x, 86, x, 99), WOOD, 0.3)
    hood = m_poly(c, [(cx - 52, 84), (cx - 48, 50), (cx - 20, 38), (cx + 18, 40), (cx + 44, 56), (cx + 46, 84)])
    rip = m_poly(c, [(cx - 6, 42), (cx + 16, 44), (cx + 8, 64), (cx - 2, 58)])
    c.paint(m_sub(hood, rip), LINEN, noise_mod(lambda x, y: clamp(0.8 - 0.35 * (x - cx + 52) / 98 - 0.2 * (y - 38) / 46 + 0.08 * math.sin(x * 0.35)), 0.08, 81))
    for x in range(cx - 48, cx + 46, 16):   # hoops showing through
        c.paint(m_line(c, [(x, 84), (x + 2, 46 + abs(x - cx) * 0.2)], 1), WOOD, 0.35)
    for x in range(cx - 50, cx + 44, 2):
        if hood.load()[x, 60] and not rip.load()[x, 60]:
            c.set(x, 60, LAPIS[2])
    for wx, broken in ((cx - 36, False), (cx + 30, True)):   # wheels
        m = m_sub(m_ell(c, wx - 15, 84, wx + 15, 114), m_ell(c, wx - 12, 87, wx + 12, 111))
        if broken:
            m = m_sub(m, m_poly(c, [(wx, 99), (wx + 20, 80), (wx + 20, 105)]))
        c.paint(m, WOOD, 0.45)
        for a in range(0, 360, 45):
            if broken and -60 < a - 360 * (a > 180) < 30:
                continue
            aa = math.radians(a)
            c.paint(m_line(c, [(wx, 99), (wx + math.cos(aa) * 12, 99 + math.sin(aa) * 12)], 1), WOOD, 0.4)
        c.paint(m_ell(c, wx - 2, 97, wx + 2, 101), IRON, 0.6)
    # the sand swallowing its lower half
    c.paint(m_poly(c, [(0, 127), (0, 112), (40, 104), (90, 108), (140, 101), (191, 110), (191, 127)]), SAND, lambda x, y: clamp(0.72 - (y - 100) * 0.012 + 0.08 * h01(x // 3, y // 2, 82)))
    for x in range(0, 192):
        for y in range(95, 115):
            if c.get(x, y) in (SAND[6], SAND[7]) and c.get(x, y - 1)[3] and c.get(x, y - 1) not in SAND:
                c.set(x, y, SAND[8]); break
    c.outline()
    return c.im


def big_wagon2(f, w=192, h=128):
    c = cv(w, h); cx = 96
    c.paint(m_poly(c, [(cx - 40, 120), (cx - 36, 92), (cx + 30, 86), (cx + 38, 114)]), WOOD, lambda x, y: clamp(0.7 - (y - 86) * 0.012 - 0.2 * (x - cx + 40) / 78))   # overturned cart
    for x in range(cx - 36, cx + 32, 8):
        c.paint(m_line(c, [(x, 118), (x + 3, 90)], 1), WOOD, 0.25)
    c.paint(m_sub(m_ell(c, cx + 18, 66, cx + 46, 94), m_ell(c, cx + 21, 69, cx + 43, 91)), WOOD, 0.5)   # a wheel still turned to the sky
    for a in range(0, 360, 60):
        aa = math.radians(a)
        c.paint(m_line(c, [(cx + 32, 80), (cx + 32 + math.cos(aa) * 11, 80 + math.sin(aa) * 11)], 1), WOOD, 0.45)
    for jx, jy in [(cx - 56, 116), (cx - 48, 121), (cx + 48, 119)]:   # spilled jars
        c.paint(m_ell(c, jx - 6, jy - 8, jx + 6, jy + 4), CLAY, cyl(jx - 6, jx + 6, 0.2, 0.85))
    c.paint(m_poly(c, [(0, 127), (0, 120), (50, 116), (110, 119), (191, 114), (191, 127)]), SAND, lambda x, y: clamp(0.7 - (y - 114) * 0.015))
    c.outline()
    return c.im


def big_camelbones(f, w=192, h=128):
    c = cv(w, h); cx = 96
    c.paint(m_line(c, [(cx - 44, 112), (cx - 10, 104), (cx + 24, 108)], 2), BONE, 0.7)   # spine
    for i in range(8):   # ribs
        x = cx - 34 + i * 7
        c.paint(m_line(c, [(x, 107), (x + 4, 96 - (4 - abs(i - 4)) * 2), (x + 9, 108)], 1), BONE, 0.75 - i * 0.03)
    c.paint(m_poly(c, [(cx + 22, 106), (cx + 38, 100), (cx + 48, 104), (cx + 36, 110)]), BONE, cyl(cx + 22, cx + 48, 0.3, 0.9))   # skull
    c.set(cx + 36, 104, K); c.set(cx + 37, 104, K)
    for lx in (cx - 40, cx - 30, cx + 12):
        c.paint(m_line(c, [(lx, 112), (lx - 6, 124)], 1), BONE, 0.55)
    c.paint(m_poly(c, [(0, 127), (0, 118), (60, 114), (130, 116), (191, 112), (191, 127)]), SAND, lambda x, y: clamp(0.72 - (y - 112) * 0.02))
    c.outline()
    return c.im


def big_sunspire(f, w=192, h=128):
    """the buried sun-spire: a pyramid's gilded tip jutting from the dunes, its disc still burning"""
    c = cv(w, h); cx = 96
    pyr = m_poly(c, [(cx - 84, 127), (cx, 20), (cx + 84, 127)])
    c.paint(pyr, SSTONE, noise_mod(lambda x, y: clamp((0.82 if x < cx else 0.42) - 0.25 * (y - 20) / 107 + (0.05 if int(y) % 9 == 0 else 0)), 0.06, 90))
    for y in range(28, 127, 9):   # courses
        for x in range(cx - 84, cx + 85):
            if pyr.load()[x, y]:
                c.set(x, y, SSTONE[2] if x < cx else SSTONE[1])
    cap = m_poly(c, [(cx - 22, 48), (cx, 20), (cx + 22, 48)])
    c.paint(cap, GOLD, lambda x, y: clamp((0.95 if x < cx else 0.6) - 0.25 * (y - 20) / 28))
    glow_dot(c, cx, 62, 11, AMBER, 1.0)   # the disc, inset in the face
    for a in range(0, 360, 30):
        aa = math.radians(a)
        c.paint(m_line(c, [(cx + math.cos(aa) * 13, 62 + math.sin(aa) * 13), (cx + math.cos(aa) * 18, 62 + math.sin(aa) * 18)], 1), GOLD, 0.8)
    for s in (-1, 1):   # wings of the sun
        c.paint(m_poly(c, [(cx + s * 16, 60), (cx + s * 42, 54), (cx + s * 38, 60), (cx + s * 44, 62), (cx + s * 16, 66)]), GOLD, 0.7 if s < 0 else 0.45)
    c.paint(m_poly(c, [(0, 127), (0, 110), (40, 100), (80, 108), (120, 98), (170, 104), (191, 100), (191, 127)]), SAND,
            lambda x, y: clamp(0.75 - (y - 98) * 0.012 + 0.06 * h01(x // 3, y // 2, 91)))
    c.outline()
    return c.im


def big_ruinarch(f, w=192, h=128):
    """the tomb mouth: two pylons and a lintel with the winged sun, sunk to the knees in sand"""
    c = cv(w, h); cx = 96
    for s in (-1, 1):
        x0 = cx + s * 30
        m = m_poly(c, [(x0 - 14, 127), (x0 - 11, 40), (x0 + 11, 40), (x0 + 14, 127)])
        c.paint(m, SSTONE, noise_mod(lambda x, y, x0=x0: clamp(0.8 - 0.5 * (x - x0 + 14) / 28 - 0.12 * (y - 40) / 87), 0.07, 92 + s))
        for y in range(48, 120, 8):
            for x in range(x0 - 8, x0 + 8, 2):
                if h01(x, y, 93) < 0.55: c.set(x, y, SSTONE[1])
    c.paint(m_rect(c, cx - 48, 30, cx + 48, 42), SSTONE, box(cx - 48, 30, cx + 48, 42, 0.9, 0.65, 0.3, 2, 3))
    glow_dot(c, cx, 36, 4, GOLD, 1.0)
    for s in (-1, 1):
        c.paint(m_poly(c, [(cx + s * 5, 34), (cx + s * 26, 32), (cx + s * 22, 36), (cx + s * 5, 38)]), LAPIS, 0.55)
    c.paint(m_poly(c, [(0, 127), (0, 116), (50, 108), (96, 114), (150, 106), (191, 114), (191, 127)]), SAND, lambda x, y: clamp(0.72 - (y - 106) * 0.015))
    c.outline()
    return c.im


def big_hand(f, w=192, h=128):
    """a colossal stone hand reaching out of the dune"""
    c = cv(w, h); cx = 96
    palm = m_poly(c, [(cx - 30, 127), (cx - 26, 84), (cx + 20, 80), (cx + 30, 127)])
    c.paint(palm, SSTONE, noise_mod(lambda x, y: clamp(0.8 - 0.5 * (x - cx + 30) / 60), 0.08, 95))
    for i, (fx_, top) in enumerate([(-22, 30), (-9, 22), (4, 26), (16, 38)]):
        m = m_or(m_rect(c, cx + fx_ - 5, top + 4, cx + fx_ + 5, 86), m_ell(c, cx + fx_ - 5, top, cx + fx_ + 5, top + 9))
        c.paint(m, SSTONE, lambda x, y, fx_=fx_: clamp(0.85 - 0.55 * (x - cx - fx_ + 5) / 10))
        for y in (top + 20, top + 36):
            c.paint(m_rect(c, cx + fx_ - 4, y, cx + fx_ + 4, y), SSTONE, 0.2)
    c.paint(m_poly(c, [(cx + 22, 96), (cx + 44, 70), (cx + 50, 76), (cx + 32, 104)]), SSTONE, 0.4)   # thumb
    c.paint(m_poly(c, [(0, 127), (0, 112), (60, 104), (130, 108), (191, 100), (191, 127)]), SAND, lambda x, y: clamp(0.74 - (y - 100) * 0.012))
    c.outline()
    return c.im


def big_titles(f, w=192, h=128):
    """four cartouches on a painted band (the Pharaoh's titles; 54_sb.js inks the glyphs into them)"""
    c = cv(w, h)
    c.paint(m_rect(c, 2, 20, 189, 104), SSTONE, noise_mod(lambda x, y: clamp(0.55 - 0.1 * (y - 20) / 84), 0.06, 100))
    for y in (22, 102):
        c.paint(m_rect(c, 2, y, 189, y + 1), LAPIS, 0.55)
    for x in range(4, 188, 6):
        c.set(x, 25, GOLD[3]); c.set(x + 3, 99, GOLD[3])
    for i in range(4):
        cx = 26 + i * 46
        c.paint(m_ell(c, cx - 15, 32, cx + 15, 94), GOLD, lambda x, y: clamp(0.8 - 0.3 * (y - 32) / 62))
        c.paint(m_ell(c, cx - 12, 35, cx + 12, 91), LINEN, 0.8)
        c.paint(m_rect(c, cx - 14, 92, cx + 14, 95), GOLD, 0.75)
        for k in range(i + 1):   # tally marks: the order they were painted in
            c.paint(m_rect(c, cx - (i * 3) + k * 6 - 1, 98, cx - (i * 3) + k * 6, 100), LAPIS, 0.8)
    # the painted king leading the procession, facing the titles
    c.paint(m_poly(c, [(178, 104), (180, 60), (186, 56), (188, 104)]), LAPIS, 0.5)
    c.outline(SSTONE[0])
    return c.im


def big_sealdoor(f, w=192, h=128):
    """a hieroglyph door-frame (pylon jambs + lintel with the eye) around a gate column"""
    c = cv(w, h); cx = 96
    for s in (-1, 1):
        x0 = cx + s * 14
        c.paint(m_rect(c, x0 - 6, 40, x0 + 6, 127), SSTONE, noise_mod(cyl(x0 - 6, x0 + 6, 0.2, 0.85), 0.07, 110 + s))
        for y in range(46, 124, 7):
            for x in range(x0 - 4, x0 + 4, 2):
                if h01(x, y, 111) < 0.6: c.set(x, y, LAPIS[2] if h01(x, y, 112) < 0.3 else SSTONE[1])
    c.paint(m_rect(c, cx - 26, 26, cx + 26, 40), SSTONE, box(cx - 26, 26, cx + 26, 40, 0.9, 0.65, 0.3, 2, 3))
    c.paint(m_ell(c, cx - 9, 29, cx + 9, 37), LINEN, 0.85)                            # the eye
    c.paint(m_ell(c, cx - 3, 30, cx + 3, 36), LAPIS, 0.3)
    c.paint(m_line(c, [(cx - 9, 37), (cx - 12, 40)], 1), LAPIS, 0.3)
    c.outline()
    return c.im


def big_sundial(f, w=192, h=128):
    """a sun-dial mosaic: a great disc with hour rays and the path of noon picked out in gold"""
    c = cv(w, h); cx, cy = 96, 70
    c.paint(m_ell(c, cx - 54, cy - 54, cx + 54, cy + 54), SSTONE, lambda x, y: clamp(0.55 - 0.2 * math.hypot(x - cx, y - cy) / 54))
    c.paint(m_sub(m_ell(c, cx - 54, cy - 54, cx + 54, cy + 54), m_ell(c, cx - 50, cy - 50, cx + 50, cy + 50)), GOLD, 0.6)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        c.paint(m_line(c, [(cx + math.cos(a) * 20, cy + math.sin(a) * 20), (cx + math.cos(a) * 48, cy + math.sin(a) * 48)], 1),
                LAPIS if k % 3 else GOLD, 0.6)
    glow_dot(c, cx, cy, 14, GOLD, 0.9)
    c.set(cx - 4, cy - 2, SSTONE[1]); c.set(cx + 4, cy - 2, SSTONE[1])
    c.outline(SSTONE[0])
    return c.im


def big_gateleaves(f, w=192, h=128):
    """the Cemetery Gate's iron leaves, thrown open against the gatehouse walls"""
    c = cv(w, h); cx = 96
    for s in (-1, 1):
        x0 = cx + s * 92
        for k in range(8):
            x = x0 - s * (4 + k * 5)
            c.paint(m_rect(c, x, 64, x, 127), IRON, 0.5 - 0.03 * k)
            c.paint(m_poly(c, [(x - 1, 64), (x + 1, 64), (x, 58)]), IRON, 0.7)
        for y in (70, 96, 122):
            c.paint(m_line(c, [(x0 - s * 2, y), (x0 - s * 40, y + 3)], 1), IRON, 0.45)
    c.outline(NST[0])
    return c.im


# ============================================================================ SKY (512x216, the Last Oasis)
def sky_far(f=0, w=512, h=216):
    c = cv(w, h)
    SK = ramp("1a0e2a", "2c1238", "46163e", "6a1c3c", "922a36", "b8402e", "d86a2a", "ee9a34", "f8c858", "fff0a8")
    for y in range(h):
        for x in range(w):
            v = clamp(0.1 + 0.9 * (y / 150) ** 1.25)
            c.set(x, y, pick(SK, v, x, y))
    sx, sy, R = 300, 150, 30
    for y in range(sy - R - 40, sy + 30):
        for x in range(sx - R - 60, sx + R + 60):
            d = math.hypot(x - sx, (y - sy) * 1.2)
            if d < R:
                c.set(x, y, pick(ramp("f8c858", "ffe890", "fff6d0", "fffff0"), clamp(1 - d / R * 0.7 + (sy - y) * 0.004), x, y))
            elif d < R + 50:
                v = clamp((1 - (d - R) / 50) * 0.55)
                if v > bt(x, y) * 0.8:
                    old = c.get(x, y)
                    c.set(x, y, pick(SK, clamp(0.72 + v * 0.3), x, y))
    for sy_ in range(sy + 4, sy + 30, 4):   # the sun's lower half sinking into haze bands
        for x in range(sx - R - 6, sx + R + 6):
            c.set(x, sy_, SK[6])
    import random
    rnd = random.Random(7)
    for k in range(14):   # long lit clouds
        cy = 30 + k * 9 + rnd.randint(-4, 4); cx = rnd.randint(0, w); L = rnd.randint(60, 180); th = rnd.randint(2, 4)
        for i in range(L):
            x = (cx + i) % w
            thick = th * math.sin(math.pi * i / L)
            for j in range(int(thick) + 1):
                y = cy + j
                under = clamp(0.4 + (y / 150) * 0.6)
                col = pick(SK, clamp(under + (0.25 if j >= thick - 1 else -0.2)), x, y)
                c.set(x, y, col)
    # far dunes, violet
    FD = ramp("1e0e22", "2c1430", "3c1c3a", "4e2440")
    for x in range(w):
        top = 172 + 8 * math.sin(x * 0.012 + 1) + 5 * math.sin(x * 0.031 + 2)
        for y in range(int(top), h):
            c.set(x, y, pick(FD, clamp(0.85 - (y - top) * 0.03 + (0.3 if y - top < 1.5 else 0)), x, y))
    # a far pyramid against the sun
    for y in range(140, 176):
        for x in range(360, 440):
            if abs(x - 400) < (y - 140) * 1.1:
                c.set(x, y, pick(FD, 0.35 + (0.25 if x < 400 else 0), x, y))
    return c.im


def sky_mid(f=0, w=512, h=216):
    c = cv(w, h)
    MD = ramp("100812", "1a0c1c", "281226", "361a2e")
    for x in range(w):
        top = 180 + 10 * math.sin(x * 0.02) + 6 * math.sin(x * 0.047 + 1.3)
        for y in range(int(top), h):
            v = clamp(0.8 - (y - top) * 0.04)
            c.set(x, y, pick(MD, v, x, y))
        c.set(x, int(top), ramp("f0a040")[0] if (x % 3) else ramp("d06030")[0])   # the sunset rim on the crest
    for px_, ph in [(60, 70), (84, 56), (420, 64), (452, 76), (240, 40)]:   # palm silhouettes on the far bank
        for y in range(0, ph):
            x = px_ + (y / ph) ** 2 * 8
            c.set(x, 200 - y, MD[1]); c.set(x + 1, 200 - y, MD[1])
        tx, ty = px_ + 8, 200 - ph
        for a in (-150, -120, -60, -30, -170, -10):
            aa = math.radians(a)
            for s in range(16):
                c.set(tx + math.cos(aa) * s, ty + math.sin(aa) * s + (s / 16) ** 2 * 7, MD[1])
    return c.im


# ============================================================================ ICONS 16x16
def icon_hood():
    c = Canvas(16, 16)
    hood = m_poly(c, [(8, 1), (13, 5), (14, 13), (11, 15), (5, 15), (2, 13), (3, 5)])
    c.paint(hood, ramp("08080c", "121119", "1d1b27", "2c2838", "3f3a50"), lambda x, y: clamp(0.8 - 0.5 * (x - 2) / 12))
    c.paint(m_rect(c, 4, 7, 11, 9), ramp("020203"), 0)
    for x in (5, 10):
        c.set(x, 8, GHOST[5]); c.set(x + (1 if x == 5 else -1), 8, GHOST[3])
    c.paint(m_line(c, [(3, 14), (12, 14)], 1), IRON, 0.6)
    c.outline()
    return c.im


def icon_scarab():
    c = Canvas(16, 16)
    for s in (-1, 1):   # lapis wings
        c.paint(m_poly(c, [(8, 6), (8 + s * 7, 3), (8 + s * 7, 9), (8, 10)]), LAPIS, 0.55 if s < 0 else 0.35)
    c.paint(m_ell(c, 5, 5, 10, 13), GOLD, lambda x, y: clamp(0.95 - 0.5 * math.hypot(x - 6, y - 7) / 6))
    c.paint(m_ell(c, 6, 2, 9, 5), GOLD, 0.7)
    glow_dot(c, 7.5, 1.5, 1.4, AMBER, 1)
    c.set(7, 9, GOLD[1]); c.set(8, 9, GOLD[1])
    c.outline()
    return c.im


# ============================================================================ assembly
NV = [('lamppost', nv_lamppost, 4), ('headstone', nv_headstone(0), 4), ('headstone1', nv_headstone(1), 4), ('tombchest', nv_tombchest(0), 1),
      ('tombchest1', nv_tombchest(1), 4), ('mourner', nv_mourner, 1), ('cage', nv_cage, 1), ('rack', nv_rack, 1), ('dummy', nv_dummy, 1),
      ('bunk', nv_bunk, 1), ('drum', nv_drum, 1), ('axestump', nv_axestump, 1), ('kingskull', nv_kingskull(0), 1), ('kingskull1', nv_kingskull(1), 1)]
DUN = [('jars', du_jars(0), 1), ('jars1', du_jars(1), 1), ('crates', du_crates, 1), ('banner_du', du_banner, 4), ('reeds', du_reeds(0), 4),
       ('reeds1', du_reeds(1), 4), ('reeds2', du_reeds(2), 4), ('scarabidol', du_scarabidol, 1), ('hoard', du_hoard, 1),
       ('sarcophagus', du_sarcophagus(0), 1), ('sarcophagus1', du_sarcophagus(1), 1), ('brazier_du', du_brazier, 4), ('statue_du', du_jackal, 1)]
TALL = [('palm', tall_palm(0), 4), ('palm1', tall_palm(1), 4), ('palm2', tall_palm(2), 4), ('palmdead', tall_palmdead, 1), ('obelisk', tall_obelisk, 1),
        ('ruincol', tall_ruincol(0), 1), ('ruincol1', tall_ruincol(1), 1)]
BIG = [('catafalque', big_catafalque), ('tombwall', big_tombwall), ('dirgeslab', big_dirgeslab), ('fence', big_fence), ('gateleaves', big_gateleaves),
       ('wagon', big_wagon), ('wagon2', big_wagon2), ('camelbones', big_camelbones), ('sunspire', big_sunspire), ('ruinarch', big_ruinarch),
       ('colossushand', big_hand), ('titles', big_titles), ('sealdoor', big_sealdoor), ('sundial', big_sundial)]


def sheet(name, w, h, specs, ms=140):
    frames, tags = [], []
    for spec in specs:
        tag, fn = spec[0], spec[1]
        n = spec[2] if len(spec) > 2 else 1
        a = len(frames)
        for i in range(n):
            frames.append({"ms": ms, "cels": {"art": fn(i, w, h)}})
        tags.append((tag, a, len(frames) - 1))
    return name, w, h, ["art"], frames, tags


def all_sheets():
    out = [sheet('xsb_nv', 48, 64, NV), sheet('xsb_du', 48, 64, DUN), sheet('xsb_tall', 64, 112, TALL, 160), sheet('xsb_big', 192, 128, BIG)]
    sky = [{"ms": 100, "cels": {"art": sky_far()}}, {"ms": 100, "cels": {"art": sky_mid()}}]
    out.append(('xsb_sky', 512, 216, ["art"], sky, [('far', 0, 0), ('mid', 1, 1)]))
    ic = [{"ms": 100, "cels": {"art": icon_hood()}}, {"ms": 100, "cels": {"art": icon_scarab()}}]
    out.append(('xsb_icons', 16, 16, ["art"], ic, [('c_x3_hood', 0, 0), ('c_x3_scarab', 1, 1)]))
    bug = [{"ms": 90, "cels": {"art": im}} for im in du_goldbug()]
    out.append(('xsb_bug', 16, 12, ["art"], bug, [('walk', 0, 3), ('dig', 4, 6)]))
    return out


if __name__ == '__main__':
    sheets = all_sheets()
    if PREVIEW:
        dst = os.environ.get('SBPREV', '/tmp')
        for name, w, h, layers, frames, tags in sheets:
            sc = 3 if w <= 64 else 2 if w <= 192 else 1
            cols = min(len(frames), max(1, 2400 // (w * sc)))
            rows = (len(frames) + cols - 1) // cols
            out = Image.new('RGBA', (cols * w * sc, rows * h * sc), (46, 44, 58, 255))
            for i, fr in enumerate(frames):
                im = fr['cels']['art'].resize((w * sc, h * sc), Image.NEAREST)
                out.alpha_composite(im, ((i % cols) * w * sc, (i // cols) * h * sc))
            out.save(os.path.join(dst, name + '.png'))
        print('preview ->', dst)
    else:
        from asebuild import build
        for name, w, h, layers, frames, tags in sheets:
            build(name, w, h, layers, frames, tags)
            print('built', name, len(frames), 'frames')
