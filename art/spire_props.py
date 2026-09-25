"""Props for the `spire` biome (Tempest Spire). Each builder returns (w, h, layers, frames, tags).

sp_windmill  96x128  loop(8)          stone tower mill, conical slate cap, 4 tattered sails turning, amber window
sp_cottage   96x72   idle(1)          ruined farm cottage: sagging wet thatch, half-collapsed roof end, dim window
sp_fence     48x16   idle(1)          broken wooden field fence
sp_lamp      16x40   loop(4)          storm lantern hanging from a leaning iron pole, flame flicker
sp_wheat     48x24   loop(6)          clump of tall dead wheat bending in the gale
sp_bridge    16x16   l m r s crack    rickety rope-lashed plank bridge section, walkable top at y=0
sp_sea       16x16   surf(6) deep(4)  stormy sea surface tile (rolling foam crest) + the water below it
sp_debris    32x32   a b c d          falling roof debris: slates, split beam, gargoyle block, bent finial
sp_window    48x96   idle(1)          broken gothic lancet window (glass gone -> transparent), interior backdrop

Face right, bottom-anchored, horizontally centred (sp_debris: centred pivot). 1px K outline, light from the
upper-left, pixel-clean (alpha 0/255 only).
"""
import math, random
from envlib import C, ramp, K, T, bt, h01, clamp, blank, outline
from env_props import Spr, flame
from spire_tiles import (ST, SHEEN, GLINT, SALT, SEA, BOLT, AMBER, RUST, VERD, IRON, WOOD, WHEAT, GRASS, THRIFT,
                         BONE, CLOTH, LICHEN)

SLATE = ramp("0c0e14", "141822", "1c2230", "262e3e", "323c50", "445066", "5a687e")
CANVAS = ramp("1c1b1a", "282623", "35322d", "433e37", "524c43", "625a4f")
THATCH = ramp("171410", "221d16", "2e271d", "3b3224", "4a3f2c", "5a4d36", "6b5c40")
FLAME = [AMBER[1], AMBER[2], AMBER[3], AMBER[4], AMBER[5]]
GLASS = ramp("0e1624", "1a2a40", "2c4462", "4a6a8e")


def stone_level(x, y, cw=9, ch=5, seed=0):
    """Ashlar course pattern for props: returns -1 on a joint, else a small tone offset per block."""
    row = y // ch
    off = (cw // 2) * (row % 2)
    if y % ch == ch - 1 or (x + off) % cw == 0:
        return None
    return (h01((x + off) // cw, row, 40 + seed) - 0.5) * 2


# =========================================================================== windmill
def windmill():
    Wd, Hd = 96, 128
    cx = 48
    TOP, BOT = 52, 127                 # stone tower rows
    # ------------------------------------------------ tower (static)
    tw = Spr(Wd, Hd)
    for y in range(TOP, BOT + 1):
        t = (y - TOP) / (BOT - TOP)
        hw = 11 + 6 * t + (1 if y > BOT - 3 else 0)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            nx = (x + 0.5 - cx) / hw                          # -1..1 across the drum
            lit = 0.55 - 0.55 * nx - 0.1 * abs(nx) ** 3        # cylinder lit from the left
            lv = 3 + lit * 4
            sl = stone_level(int(x - cx + 64), y, 8, 5)
            if sl is None:
                lv -= 2
            else:
                lv += sl * 0.6
                if (y % 5) == 0:
                    lv += 0.6                                  # rain-wet top edge of each course
            if h01(x, y, 3) < 0.05:
                lv -= 1
            # rain streaking down from the cap: darker wet runs
            if h01(x, 0, 11) < 0.18 and y < TOP + 30 + 20 * h01(x, 1, 12):
                lv -= 0.8
            tw.set(x, y, ST[int(clamp(lv, 1, 10))])
    # arched door (weathered planks, iron strap) and a stone step
    for y in range(106, BOT + 1):
        for x in range(cx - 5, cx + 6):
            top = 106 + (0 if abs(x - cx) < 2 else 1 if abs(x - cx) < 4 else 3)
            if y < top:
                continue
            c = WOOD[3] if (x - cx + 5) % 3 else WOOD[1]
            if y in (112, 121):
                c = IRON[3]
            if x == cx - 5 or y == top:
                c = K
            tw.set(x, y, c)
    for x in range(cx - 7, cx + 8):
        tw.set(x, BOT, ST[7] if x < cx + 4 else ST[5])
    tw.set(cx + 3, 116, IRON[5])
    # the warm window (upper), and a dark shuttered one (lower left)
    for y in range(70, 77):
        for x in range(cx - 3, cx + 2):
            c = AMBER[3] if x < cx else AMBER[2]
            if x == cx - 1:
                c = WOOD[2]                                   # mullion
            if y == 73:
                c = WOOD[2]
            tw.set(x, y, c)
    tw.set(cx - 2, 71, AMBER[4])
    for x in range(cx - 4, cx + 3):
        tw.set(x, 69, K)
        tw.set(x, 77, ST[8])
    for y in range(69, 78):
        tw.set(cx - 4, y, K)
        tw.set(cx + 2, y, K)
    for y in range(90, 96):
        for x in range(cx - 12, cx - 8):
            tw.set(x, y, WOOD[1] if x % 2 else WOOD[2])
    # cap: conical slate hood with an eave band and a finial
    for y in range(26, 55):
        t = (y - 26) / 28
        hw = 1 + 15.5 * t ** 0.85
        for x in range(int(cx - hw), int(cx + hw) + 1):
            nx = (x + 0.5 - cx) / max(hw, 1)
            lv = 3.4 - 2.4 * nx
            row = (y - 26) // 3
            if (y - 26) % 3 == 2:
                lv -= 1.2                                     # slate course shadow
            elif (x + row * 2) % 5 == 0 and hw > 4:
                lv -= 0.8                                     # butt joints
            if h01(x, y, 21) < 0.06:
                lv += 1                                       # wet glint
            tw.set(x, y, SLATE[int(clamp(lv, 0, 6))])
    for x in range(cx - 17, cx + 18):
        tw.set(x, 54, WOOD[4] if x < cx + 6 else WOOD[2])
        tw.set(x, 55, WOOD[1])
    for y in range(18, 27):
        tw.set(cx, y, IRON[4])
    tw.set(cx - 1, 21, IRON[4])
    tw.set(cx + 1, 21, IRON[3])
    tw.set(cx, 17, BOLT[1])
    tw.outline()
    # wet specular on the cap's lit shoulder (after outline)
    for y in range(34, 50, 3):
        tw.set(cx - int(3 + (y - 30) * 0.35), y, SHEEN[0])
    # ------------------------------------------------ sails (rotating)
    hub = (cx + 1, 46)
    R = 45
    frames = []
    for f in range(8):
        sv = Spr(Wd, Hd)
        spx = sv.px
        ang0 = math.radians(22.5 * f + 30)      # 180 deg over 8 frames; opposite sails match
        sails = []
        for k in range(4):
            a = ang0 + k * math.pi / 2
            sails.append((k, math.cos(a), math.sin(a)))
        for y in range(Hd):
            for x in range(Wd):
                dx, dy = x + 0.5 - hub[0], y + 0.5 - hub[1]
                for (k, ca, sa) in sails:
                    r = dx * ca + dy * sa
                    w = -dx * sa + dy * ca
                    if r < 3 or r > R + 1:
                        continue
                    c = None
                    # the stock (whip): tapered 2px spar
                    if -1.0 <= w <= 0.6 + (0.4 if r < 20 else 0):
                        c = WOOD[5] if w < -0.2 else WOOD[3]
                    elif 7 < r <= R and 0.6 < w <= 10.5:
                        edge = w > 9.5
                        cross = (r % 5.0) < 1.0
                        torn = False
                        if k % 2 == 1:
                            has_canvas = r < 20 + 7 * h01(int(w), 2, 5) # canvas torn away: bare lattice tip
                        else:
                            has_canvas = True
                            torn = h01(int(r / 2), int(w / 2), 7) < 0.1 and r > 20
                        if edge or cross:
                            c = WOOD[3] if edge else WOOD[2]
                            if cross and not edge and has_canvas and not torn:
                                c = CANVAS[1]                           # batten seen through the cloth
                        elif has_canvas and not torn:
                            # weathered canvas: lit near the stock, a sag shadow mid-panel, stains
                            lv = 4 - (w / 10.5) * 2.2 + 0.6 * math.sin(r * 0.5 + k)
                            if h01(int(r), int(w), 30) < 0.06:
                                lv -= 1.5
                            c = CANVAS[int(clamp(lv, 0, 5))]
                    if c is not None:
                        spx[x, y] = c
                        break
        # a frayed strip of canvas flapping off sail 2's torn tip (animated with the rotation)
        for kk in (1, 3):
            k, ca, sa = sails[kk]
            for i in range(6):
                r = 21 + i
                w = 4 + math.sin(f * math.pi / 4 * 2 + i * 0.9) * 2 + i * 0.5
                sv.set(hub[0] + ca * r - sa * w, hub[1] + sa * r + ca * w, CANVAS[3])
        sv.outline()
        # iron hub boss over everything
        for (ox, oy, c) in ((-1, -1, IRON[5]), (0, -1, IRON[4]), (1, -1, IRON[3]), (-1, 0, IRON[4]),
                            (0, 0, IRON[6]), (1, 0, IRON[2]), (-1, 1, IRON[3]), (0, 1, IRON[2]), (1, 1, IRON[1])):
            sv.set(hub[0] + ox, hub[1] + oy, c)
        for (ox, oy) in ((-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1), (-1, -2), (0, -2), (1, -2),
                         (-1, 2), (0, 2), (1, 2)):
            if sv.get(hub[0] + ox, hub[1] + oy)[3] == 0 or True:
                sv.set(hub[0] + ox, hub[1] + oy, K)
        # the window's warm light breathes a little
        tw_f = tw.img.copy()
        if f % 4 == 2:
            tw_f.putpixel((cx - 3, 75), AMBER[4])
        frames.append({"ms": 140, "cels": {"Tower": tw_f, "Sails": sv.img}})
    return Wd, Hd, ["Tower", "Sails"], frames, [("loop", 0, 7)]


# =========================================================================== cottage
def cottage():
    Wd, Hd = 96, 72
    s = Spr(Wd, Hd)
    WL, WR, WT, WB = 12, 84, 44, 71        # walls
    # walls: rain-dark fieldstone, lit from the left, broken at the right end
    for y in range(WT, WB + 1):
        for x in range(WL, WR + 1):
            if x > 74 and y < WT + (x - 74) * 1.1 + (3 if x % 3 == 0 else 0):
                continue                                  # the collapsed corner
            sl = stone_level(x, y, 7, 4, 3)
            lv = 5.2 - (x - WL) / (WR - WL) * 1.8
            if sl is None:
                lv = 2
            else:
                lv += sl * 0.9
                if y % 4 == 0:
                    lv += 0.7
            if y < WT + 3:
                lv -= 1.5                                 # under the eaves
            s.set(x, y, ST[int(clamp(lv, 1, 9))])
    # door (dark gap with a broken plank door ajar)
    for y in range(54, WB + 1):
        for x in range(24, 33):
            s.set(x, y, ST[0] if x > 27 else WOOD[3] if (x % 2) else WOOD[2])
    for x in range(23, 34):
        s.set(x, 53, ST[8])                               # lintel
    # the dim window
    for y in range(52, 59):
        for x in range(46, 54):
            c = AMBER[2] if x < 50 else AMBER[1]
            if x == 49 or y == 55:
                c = WOOD[1]
            if y == 52:
                c = AMBER[3] if x < 49 else AMBER[2]
            s.set(x, y, c)
    for x in range(45, 55):
        s.set(x, 51, ST[8])
        s.set(x, 59, ST[7])
    # moss / sea-thrift at the wall foot
    for x in range(WL, WR - 8):
        if h01(x, 0, 71) < 0.3:
            s.set(x, WB, GRASS[3])
            if h01(x, 1, 72) < 0.3:
                s.set(x, WB - 1, GRASS[2])
    # chimney (left)
    for y in range(8, 30):
        for x in range(18, 25):
            sl = stone_level(x, y, 4, 3, 5)
            s.set(x, y, ST[2] if sl is None else ST[6 if x < 21 else 4])
    for x in range(17, 26):
        s.set(x, 8, ST[8])
    # roof: wet thatch, sagging ridge, overhanging eaves; the right end has collapsed to bare rafters
    RL, RR = 4, 92
    def ridge(x):
        return 16 + 5 * math.sin(math.pi * (x - RL) / (RR - RL)) ** 1.5      # sag in the middle
    for x in range(RL, RR + 1):
        top = ridge(x)
        if x < RL + 10:
            top += (RL + 10 - x) * 1.6                     # hipped end
        eave = WT + 2 - (0 if 8 < x < 88 else 2)
        for y in range(int(top), eave + 1):
            t = (y - top) / max(1, eave - top)
            if x > 64:
                continue                                  # collapsed section drawn below
            lv = 4.5 - t * 1.5 - (x - RL) / (RR - RL) * 1.2
            if (y + (x // 3) % 2) % 3 == 0:
                lv -= 1                                   # straw courses
            if (x * 3 + y) % 7 == 0:
                lv += 0.8                                 # stray lit straws
            if y == eave:
                lv = 1.4                                  # ragged eave shadow
            s.set(x, y, THATCH[int(clamp(lv, 0, 6))])
        if x <= 64 and h01(x, 3, 80) < 0.5:
            s.set(x, eave + 1, THATCH[1])                 # ragged straw ends hanging over
    # collapsed end: ridge beam snapped and sagging, rafters, a few thatch clumps
    for x in range(64, RR - 2):
        y = ridge(64) + (x - 64) ** 1.4 * 0.35
        s.set(x, y, WOOD[4])
        s.set(x, y + 1, WOOD[2])
    for rx in (68, 76, 84):
        top = ridge(64) + (rx - 64) ** 1.4 * 0.35
        for y in range(int(top), WT + 1):
            s.set(rx + (y - top) * 0.15, y, WOOD[3] if y % 5 else WOOD[4])
    for x in range(64, 72):
        for y in range(int(ridge(x)) + 4, WT + 2):
            if h01(x, y, 90) < 0.7 - (x - 64) * 0.07:
                s.set(x, y, THATCH[2 if y % 3 else 3])
    # wet sheen along the thatch ridge (a few cold glints)
    for x in range(RL + 12, 64, 5):
        s.set(x, ridge(x), SHEEN[1])
    s.outline()
    return Wd, Hd, ["Cottage"], [{"ms": 1000, "cels": {"Cottage": s.img}}], [("idle", 0, 0)]


# =========================================================================== fence
def fence():
    Wd, Hd = 48, 16
    s = Spr(Wd, Hd)

    def post(x, top, lean=0.0):
        for y in range(top, 16):
            xx = x + lean * (15 - y)
            s.set(xx, y, WOOD[5])
            s.set(xx + 1, y, WOOD[3])
        s.set(x + lean * (15 - top), top, WOOD[6])

    post(4, 2)
    post(22, 4, 0.12)
    post(41, 3)
    # rails: upper rail snapped between posts 2 and 3 (one half hanging down), lower rail whole
    for x in range(5, 23):
        s.set(x, 5, WOOD[5] if x % 7 else WOOD[4])
        s.set(x, 6, WOOD[3])
    for x in range(5, 42):
        y = 10 + (1 if 26 < x < 36 else 0)
        s.set(x, y, WOOD[4] if x % 9 else WOOD[3])
        s.set(x, y + 1, WOOD[2])
    for i in range(9):                                    # broken rail dangling from post 2
        s.set(24 + i, 6 + i * 0.45, WOOD[4])
        s.set(24 + i, 7 + i * 0.45, WOOD[2])
    for i in range(6):                                    # stub on post 3
        s.set(40 - i, 6 + (i > 3), WOOD[4])
        s.set(40 - i, 7 + (i > 3), WOOD[2])
    s.set(33, 11, WOOD[6])                                # splinter
    # a tuft of wet grass at two post feet
    for (gx, h) in ((3, 3), (7, 2), (21, 3), (43, 2), (39, 3)):
        for j in range(h):
            s.set(gx + (j > 1), 15 - j, GRASS[3] if j else GRASS[2])
    s.outline()
    return Wd, Hd, ["Fence"], [{"ms": 1000, "cels": {"Fence": s.img}}], [("idle", 0, 0)]


# =========================================================================== storm lamp
def lamp():
    Wd, Hd = 16, 40
    frames = []
    for f in range(4):
        s = Spr(Wd, Hd)
        # stone footing
        for x in range(3, 11):
            s.set(x, 39, ST[5] if x < 8 else ST[3])
            s.set(x, 38, ST[7] if x < 7 else ST[5])
        # leaning iron pole (leans right with the gale) + a hooked arm at the top
        for y in range(8, 38):
            x = 6 + (38 - y) * 0.06
            s.set(x, y, IRON[5] if y % 7 else RUST[3])
            s.set(x + 1, y, IRON[2])
        s.set(6, 30, VERD[2])
        topx = 6 + 30 * 0.06
        for i in range(5):
            s.set(topx + 1 + i, 8 - (1 if 0 < i < 4 else 0), IRON[5] if i < 3 else IRON[4])
        s.set(topx + 6, 9, IRON[4])
        # the lantern hanging from the arm tip
        lx = int(topx + 6)
        s.set(lx, 10, IRON[4])
        for x in range(lx - 2, lx + 3):
            s.set(x, 11, IRON[5] if x < lx + 1 else IRON[3])
        for x in range(lx - 3, lx + 4):
            s.set(x, 12, IRON[4] if x < lx + 1 else IRON[2])
        for y in range(13, 20):
            for x in range(lx - 2, lx + 3):
                s.set(x, y, AMBER[2] if x < lx + 1 else AMBER[1])
        flame(s, lx + 0.5, 18, 4 + (f % 2), 1.3, f / 4, pal=FLAME, seed=2)
        for y in range(13, 20):
            s.set(lx - 3, y, IRON[4])
            s.set(lx + 3, y, IRON[2])
        s.set(lx, 16, IRON[3])                            # cage bar across the glass
        for x in range(lx - 3, lx + 4):
            s.set(x, 20, IRON[3])
        s.set(lx, 21, IRON[2])
        s.outline()
        # rain glints on the glass (after outline)
        s.set(lx - 2, 14, AMBER[5] if f in (0, 2) else AMBER[4])
        frames.append({"ms": 120, "cels": {"Lamp": s.img}})
    return Wd, Hd, ["Lamp"], frames, [("loop", 0, 3)]


# =========================================================================== wheat in the wind
def wheat():
    Wd, Hd = 48, 24
    rnd = random.Random(4)
    stems = []
    for i in range(15):
        x0 = 6 + i * 2.5 + rnd.uniform(-1, 1)
        h = rnd.uniform(13, 22) * (1 - abs(i - 7) / 18)
        stems.append((x0, h, rnd.uniform(0, 1), rnd.random() < 0.8))
    frames = []
    for f in range(6):
        s = Spr(Wd, Hd)
        heads = []
        for n, (x0, h, ph, has_head) in enumerate(stems):
            gust = 0.5 + 0.5 * math.sin(2 * math.pi * (f / 6.0) - ph * 1.2)
            bend = 0.35 + 0.55 * gust                     # 0 upright .. 1 flattened to the right
            pts = []
            for j in range(int(h) + 1):
                t = j / h
                x = x0 + bend * h * 0.62 * t * t
                y = 23 - t * h * (1 - 0.28 * bend * t)
                pts.append((x, y))
            for j, (x, y) in enumerate(pts):
                c = WHEAT[2] if j < h * 0.5 else WHEAT[3]
                if n % 3 == 0:
                    c = WHEAT[1] if j < h * 0.6 else WHEAT[2]
                s.set(x, y, c)
            if has_head:
                heads.append((pts[-3:], n))
        for (tip, n) in heads:
            # an ear: 4px along the stem direction, a lighter kernel row and a bristle
            (xa, ya), (xb, yb) = tip[0], tip[-1]
            dx, dy = xb - xa, yb - ya
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            for k in range(5):
                x, y = xb - ux * k, yb - uy * k
                s.set(x, y, WHEAT[4] if k < 2 else WHEAT[3])
                s.set(x + uy * 0.9, y - ux * 0.9, WHEAT[2] if k % 2 else WHEAT[3])
            s.set(xb + ux * 2, yb + uy * 2, WHEAT[5] if n % 2 else WHEAT[4])       # awns
        # base: a dark clump of dead grass
        for x in range(4, 44):
            hh = 2 + int(2 * math.sin((x - 4) / 40 * math.pi))
            for j in range(hh):
                s.set(x, 23 - j, GRASS[2] if j < hh - 1 else GRASS[3])
        s.outline()
        frames.append({"ms": 110, "cels": {"Wheat": s.img}})
    return Wd, Hd, ["Wheat"], frames, [("loop", 0, 5)]


# =========================================================================== rickety bridge
def bridge_cel(kind):
    s = Spr(16, 16)
    left = kind in ("l", "s")
    right = kind in ("r", "s")
    crack = kind == "crack"
    # plank ends seen edge-on: 3px planks with 1px gaps (period 4 -> tiles), sagging 1px at the crack
    x0 = 1 if left else 0
    x1 = 14 if right else 15
    for x in range(x0, x1 + 1):
        gap = (x % 4) == 3
        sag = 0
        if crack:
            if 6 <= x <= 9:
                continue                                  # the split
            sag = 1 if x in (4, 5, 10, 11) else 0
        if gap:
            s.set(x, 0 + sag, WOOD[1])                    # dark gap between planks (still walkable)
            s.set(x, 1 + sag, WOOD[0])
            continue
        pi_ = x // 4
        tone = (0, 1, -1, 0)[(pi_ * 3 + (kind == "m")) % 4]
        for y in range(0, 4):
            c = [WOOD[6], WOOD[5], WOOD[4], WOOD[2]][y]
            if y == 0 and h01(x, 0, 5) < 0.25:
                c = SHEEN[1]                              # rain glint on the wet tread
            lv = WOOD.index(c) + tone if c in WOOD else None
            if lv is not None:
                c = WOOD[int(clamp(lv, 0, 7))]
            if x % 4 == 0 and y > 0:
                c = WOOD[min(7, WOOD.index(c) + 1)] if c in WOOD else c
            s.set(x, y + sag, c)
        if h01(pi_, 2, 7 + (kind == "m")) < 0.3:          # a rotten, shorter plank
            s.set(x, 3 + sag, T)
    # thin iron stringer under the planks
    for x in range(x0, x1 + 1):
        if crack and 5 <= x <= 10:
            continue
        s.set(x, 5, IRON[4] if x % 5 else RUST[3])
    if crack:
        # the rod bent down where it's failing, splinters and a fraying rope
        s.set(5, 6, IRON[4])
        s.set(10, 6, IRON[4])
        for (x, y, c) in ((6, 1, WOOD[5]), (5, 2, WOOD[6]), (9, 1, WOOD[5]), (10, 2, WOOD[6]),
                          (7, 3, WOOD[3]), (8, 5, WOOD[3]), (7, 7, WOOD[4]), (9, 9, WOOD[3])):
            s.set(x, y, c)
    # rope lashings wrapping plank + rod
    for lx in ((2, 10) if not crack else (2, 13)):
        if (left and lx < 2) or (right and lx > 13):
            continue
        for y in range(3, 7):
            s.set(lx, y, WHEAT[3] if y % 2 else WHEAT[2])
    # dangling rope ends
    for (rx, L) in ((6, 4), (13, 3)) if not crack else ((4, 5), (11, 6)):
        if (right and rx > 13) or (left and rx < 2):
            continue
        for y in range(6, 6 + L):
            s.set(rx + (1 if y > 7 + L // 2 else 0), y, WHEAT[2] if y % 3 else WHEAT[1])
    if left:
        # iron anchor post + ring at the left end
        for y in range(0, 12):
            s.set(0, y, IRON[5])
        s.set(1, 7, IRON[4])
        s.set(1, 8, IRON[3])
        s.set(1, 0, IRON[6])
    if right:
        for y in range(0, 12):
            s.set(15, y, IRON[3])
        s.set(14, 7, IRON[4])
        s.set(14, 8, IRON[3])
        s.set(15, 0, IRON[5])
    img = outline(s.img)
    # never outline above the walk surface: clear row -1 does not exist; but keep the top row clean
    return img


def bridge():
    frames, tags = [], []
    for i, k in enumerate(("l", "m", "r", "s", "crack")):
        frames.append({"ms": 1000, "cels": {"Bridge": bridge_cel(k)}})
        tags.append((k, i, i))
    return 16, 16, ["Bridge"], frames, tags


# =========================================================================== sea tiles
def sea_surf(f):
    """Top tile of the storm sea. Peaked travelling swells (harmonics of 16 -> tiles; phases loop in 6 frames),
    each crest capped by a rolling foam lip that spills forward (rightwards, with the wind), cold glints."""
    img = blank(16, 16)
    px = img.load()
    ph = f / 6.0

    def hgt(x):
        a = 0.5 + 0.5 * math.cos(2 * math.pi * (x / 16.0 - ph) + 0.6 * math.sin(2 * math.pi * (x / 16.0 - ph)))
        b = 0.5 + 0.5 * math.cos(2 * math.pi * (2 * x / 16.0 - 2 * ph) + 1.9)
        return 3.4 * a ** 1.4 + 0.8 * b ** 1.5          # 0 (trough) .. ~4 (crest)

    hs = [hgt(x + 0.5) for x in range(16)]
    hmax = max(hgt(x / 4.0) for x in range(64))
    for x in range(16):
        h = hs[x]
        top = int(round(8.0 - h))
        fwd = hs[(x + 1) % 16] - h                        # < 0: the front face (falling to the right)
        for y in range(top, 16):
            d = y - top
            c = SEA[2] if d > 6 else SEA[3]
            if d == 0:
                c = SEA[7] if h > 1.2 else SEA[6]
            elif d == 1:
                c = SEA[5]
            elif d in (2, 3) and bt(x, y) < 0.55 - (d - 2) * 0.3:
                c = SEA[4]
            elif d > 8 and bt(x, y) < 0.3:
                c = SEA[1]
            px[x, y] = c
        if h > hmax - 2.2:                                # foam cap on the crest
            px[x, top] = SEA[11] if h > hmax - 0.8 else SEA[10] if h > hmax - 1.5 else SEA[9]
            if top + 1 < 16:
                px[x, top + 1] = SEA[10] if (fwd < 0 and h > hmax - 1.2) else SEA[8]
            if fwd < -0.4:                                 # foam tumbling down the front face
                for j in (2, 3):
                    if top + j < 16 and bt(x, top + j) < 0.6 - j * 0.12:
                        px[x, top + j] = SEA[8]
        elif fwd > 0.35 and h > 0.6 and bt(x, top + 1) < 0.5 and top + 1 < 16:
            px[x, top + 1] = SEA[6]                        # glassy back of the swell catches the light
    # a single cold glint riding the back of the swell
    gx = int((16 * ph + 3) % 16)
    gy = int(round(8.0 - hs[gx])) + 2
    if gy < 16:
        px[gx, gy] = SEA[9]
    # wind-torn spray lifting off the highest crest point
    cx = max(range(16), key=lambda x: hs[x])
    top = int(round(8.0 - hs[cx]))
    for (ox, oy, fr) in ((1, -2, (0, 2, 4)), (2, -3, (1, 3, 5)), (3, -2, (1, 3, 5))):
        if f in fr:
            x, y = (cx + ox) % 16, top + oy
            if 0 <= y < 16 and px[x, y][3] == 0:
                px[x, y] = SEA[10]
    return img


def sea_deep(f):
    img = blank(16, 16)
    px = img.load()
    for y in range(16):
        for x in range(16):
            c = SEA[1]
            if (y % 8) in (2, 3) and bt(x + 2 * (y // 8), y) < 0.35:
                c = SEA[2]                                 # faint slow bands of current
            px[x, y] = c
    for (x0, y0, sp) in ((3, 4, 4), (11, 11, 4), (7, 14, -4)):
        x = (x0 + f * sp) % 16
        px[x, y0] = SEA[5]
        px[(x + 1) % 16, y0] = SEA[3]
    return img


def sea():
    frames = [{"ms": 110, "cels": {"Sea": sea_surf(f)}} for f in range(6)]
    frames += [{"ms": 160, "cels": {"Sea": sea_deep(f)}} for f in range(4)]
    return 16, 16, ["Sea"], frames, [("surf", 0, 5), ("deep", 6, 9)]


# =========================================================================== falling roof debris
def debris_slates():
    s = Spr(32, 32)
    for (cx, cy, ang, w, h, tone) in ((13, 13, -0.35, 12, 7, 0), (19, 18, 0.5, 11, 6, 1), (11, 21, 0.15, 9, 5, 2)):
        ca, sa = math.cos(ang), math.sin(ang)
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                u, v = dx * ca + dy * sa, -dx * sa + dy * ca
                if abs(u) <= w / 2 and abs(v) <= h / 2:
                    # chipped corner
                    if u > w / 2 - 2.5 and v < -h / 2 + 2.5 and (u - w / 2 + 2.5) + (-v - h / 2 + 2.5) > 2.2:
                        continue
                    lv = 5.2 - tone * 0.8 - (v + h / 2) / h * 2.4
                    if v < -h / 2 + 1:
                        lv = 6.5                           # lit top edge
                    elif v > h / 2 - 1:
                        lv = 1                             # the slate's thickness, in shadow
                    if abs(u + 1) < 0.6 and abs(v) < 0.8:
                        lv = 0                             # nail hole
                    s.set(x, y, SLATE[int(clamp(lv, 0, 6))])
    s.outline()
    s.set(9, 10, GLINT)
    return s.img


def debris_beam():
    s = Spr(32, 32)
    ang = -0.6
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca
            half = 12.5 + (2 * h01(int(v + 5), 1, 3) if u > 0 else 1.5 * h01(int(v + 5), 2, 4))   # splintered ends
            if abs(u) <= half and abs(v) <= 3.2:
                if u > 9 and abs(v) < 1.5 and u > half - 3:
                    continue                               # split
                lv = 5 - (v + 3.2) / 6.4 * 3
                if int(u) % 6 == 0:
                    lv -= 1                                # grain / checks
                s.set(x, y, WOOD[int(clamp(lv, 1, 7))])
    # iron strap with rust
    for k in range(-3, 4):
        x, y = 16 + ca * -4 - sa * k, 16 + sa * -4 + ca * k
        s.set(x, y, IRON[4] if k < 1 else RUST[3])
    s.outline()
    return s.img


def debris_gargoyle():
    s = Spr(32, 32)
    # masonry block (a chunk of cornice), lit top face + front, broken corner
    for y in range(13, 28):
        for x in range(3, 20):
            if x > 16 and y > 24 and x + y > 42:
                continue
            if y < 16:
                lv = 9 - (x - 3) / 17 * 2                 # top face
            else:
                lv = 7 - (x - 3) / 17 * 2.5 - (y - 16) / 12
                if y == 21 or (x == 11 and y > 21) or (x == 7 and y < 21):
                    lv = 2.5                              # joints
            if y == 16:
                lv = 3                                    # cornice edge shadow
            s.set(x, y, ST[int(clamp(lv, 1, 11))])
    # the gargoyle's head jutting right out of the block: swept horn, heavy brow, deep eye, open fanged jaw
    head = [
        "...hh.........",
        "....hh........",
        ".....hhh......",
        "...bbbbbb.....",
        "..bbbbbbbbb...",
        ".bbbbeebbbbbb.",
        ".bbbbbbbbbbbbb",
        ".sssssssssst.t",
        ".ssss.........",
        ".ssss.t.t.....",
        ".sssssssss....",
        "..sssssss.....",
    ]
    ox, oy = 17, 8
    for j, row in enumerate(head):
        for i, ch in enumerate(row):
            X, Y = ox + i, oy + j
            if ch == "h":
                s.set(X, Y, ST[10] if j < 2 else ST[8])
            elif ch == "b":
                s.set(X, Y, ST[9] if j == 3 else ST[7] if i < 7 else ST[6])     # brow and snout, lit above
            elif ch == "s":
                s.set(X, Y, ST[5] if j < 10 else ST[4])                         # lower jaw / neck, shaded
            elif ch == "e":
                s.set(X, Y, ST[1])
            elif ch == "t":
                s.set(X, Y, BONE[2])                                            # stone fangs
    s.outline()
    s.set(22, 13, BOLT[1])                                                      # a cold glint in the socket
    return s.img


def debris_finial():
    s = Spr(32, 32)
    # a bent iron rod: straight lower half, kinked upper half, a trefoil cross at the tip
    pts = [(9, 28), (11, 22), (13, 16), (14, 12), (18, 9), (23, 7)]
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 1
        for k in range(n + 1):
            x = a[0] + (b[0] - a[0]) * k / n
            y = a[1] + (b[1] - a[1]) * k / n
            s.set(x, y, IRON[5])
            s.set(x + 1, y, RUST[3] if (int(y) % 4 == 0) else IRON[3])
    tx, ty = 24, 6
    for (dx, dy, c) in ((0, 0, IRON[6]), (1, 0, IRON[5]), (2, -1, IRON[5]), (2, 1, IRON[4]), (3, -2, VERD[3]),
                        (3, 2, VERD[2]), (3, 0, IRON[4]), (4, 0, VERD[3]), (5, 0, VERD[2]), (-1, -1, IRON[5]),
                        (-1, 1, IRON[4]), (0, -2, VERD[2]), (0, 2, VERD[1])):
        s.set(tx + dx, ty + dy, c)
    # collar + a torn stub of the mounting socket
    for (x, y) in ((8, 27), (9, 27), (10, 27), (8, 28), (10, 29)):
        s.set(x, y, IRON[4])
    s.set(7, 29, RUST[2])
    s.set(9, 30, RUST[3])
    s.outline()
    s.set(14, 12, GLINT)
    return s.img


def debris():
    cels = [debris_slates(), debris_beam(), debris_gargoyle(), debris_finial()]
    frames = [{"ms": 1000, "cels": {"Debris": c}} for c in cels]
    return 32, 32, ["Debris"], frames, [("a", 0, 0), ("b", 1, 1), ("c", 2, 2), ("d", 3, 3)]


# =========================================================================== broken lancet window
def window():
    Wd, Hd = 48, 96
    s = Spr(Wd, Hd)
    cx = 24
    OUT, IN = 20, 15                 # outer / inner half-widths of the stone surround
    SPRING = 34                      # where the pointed arch springs

    def inside(x, y, hw, spring, top):
        """Lancet shape: rectangle below `spring`, pointed (two arcs) above, apex at `top`."""
        dx = abs(x + 0.5 - cx)
        if y >= spring:
            return dx <= hw
        # two-centred pointed arch: arc radius r centred on the opposite side
        r = ((spring - top) ** 2 + hw * hw) / (2 * hw)
        ccx = hw - r                                      # centre offset from the axis (negative)
        return (dx - ccx) ** 2 + (y + 0.5 - spring) ** 2 <= r * r and y >= top

    for y in range(Hd):
        for x in range(Wd):
            outer = inside(x, y, OUT, SPRING, 2)
            inner = inside(x, y, IN, SPRING, 9)
            if y >= 88:
                outer = abs(x + 0.5 - cx) <= OUT + 2       # the sill projects
                inner = False
            if outer and not inner:
                # voussoirs / jamb blocks: radial joints in the arch, courses in the jambs
                if y < SPRING:
                    ang = math.atan2(y - SPRING, x + 0.5 - cx)
                    joint = (int((ang + math.pi) * 9) % 2 == 0) and h01(int((ang + math.pi) * 9), 0, 3) < 0.25
                    jl = (int((ang + math.pi) * 9 * 4) % 4 == 0)
                else:
                    joint = False
                    jl = (y % 9 == 0)
                lv = 6 - (x - (cx - OUT)) / (2 * OUT) * 3
                if x < cx - IN - 2 or (y < SPRING and x < cx):
                    lv += 0.8
                if jl:
                    lv = 2.5
                if y >= 88:
                    lv = 8 if y == 88 else 6 if y < 91 else 4
                if h01(x, y, 9) < 0.06:
                    lv -= 1.5
                s.set(x, y, ST[int(clamp(lv, 1, 10))])
    # inner chamfer: the lit left reveal, the dark right reveal
    for y in range(9, 88):
        for x in range(Wd):
            if inside(x, y, IN, SPRING, 9) and not inside(x, y, IN - 2, SPRING, 11):
                s.set(x, y, ST[8] if x < cx else ST[3])
    # tracery: central mullion splitting into two sub-lancets with a quatrefoil in the head
    for y in range(24, 88):
        s.set(cx - 1, y, ST[8])
        s.set(cx, y, ST[5])
    for side in (-1, 1):
        scx = cx + side * 7
        for i in range(40):
            a = math.pi * i / 40
            x = scx - 7 * math.cos(a) * side * -1
            y = 32 - 8 * math.sin(a)
            s.set(x, y, ST[7] if side < 0 else ST[5])
            s.set(x, y + 1, ST[4])
    qx, qy = cx, 16
    for i in range(64):
        a = 2 * math.pi * i / 64
        r = 4.5 + 1.6 * math.cos(4 * a)
        s.set(qx + r * math.cos(a), qy + r * math.sin(a), ST[7] if math.cos(a) < 0.2 else ST[4])
    s.set(qx, qy, ST[6])
    # a break: the right sub-lancet's lower mullion stub is snapped off, stones chipped from the jamb
    for y in range(60, 70):
        s.set(cx, y, T)
        s.set(cx - 1, y, T)
    for (x, y) in ((cx + OUT - 1, 50), (cx + OUT - 1, 51), (cx + OUT - 2, 51), (cx + OUT, 52)):
        s.set(x, y, T)
    # glass shards still in the leading: dark storm-blue panes with lead cames, clinging to the frame edges
    shards = [
        [(cx - IN + 2, 70), (cx - 3, 76), (cx - 3, 87), (cx - IN + 2, 87)],
        [(cx + 2, 80), (cx + 9, 84), (cx + IN - 2, 81), (cx + IN - 2, 87), (cx + 2, 87)],
        [(cx - IN + 3, 38), (cx - 8, 44), (cx - IN + 3, 50)],
        [(cx + 2, 26), (cx + 7, 30), (cx + 2, 34)],
    ]
    for poly in shards:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                if point_in_poly(x + 0.5, y + 0.5, poly) and s.get(x, y)[3] == 0:
                    lv = 2 + (1 if (x + y) % 5 == 0 else 0) - (1 if x > cx else 0)
                    c = GLASS[int(clamp(lv, 0, 3))]
                    if (x - y) % 6 == 0:
                        c = IRON[2]                        # lead came
                    s.set(x, y, c)
        s.set(poly[0][0] + 1, poly[0][1] + 1, GLINT)      # a cold highlight on each shard
    s.outline()
    return Wd, Hd, ["Window"], [{"ms": 1000, "cels": {"Window": s.img}}], [("idle", 0, 0)]


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xc:
                inside = not inside
    return inside


PROPS = {"sp_windmill": windmill, "sp_cottage": cottage, "sp_fence": fence, "sp_lamp": lamp, "sp_wheat": wheat,
         "sp_bridge": bridge, "sp_sea": sea, "sp_debris": debris, "sp_window": window}
