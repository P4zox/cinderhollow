"""Props for the `hoarfrost` biome. Each returns (w, h, layers, frames, tags).

hf_icicle   16x32  PIVOT = TOP-CENTRE (row 0 = ceiling contact; it hangs from a ceiling)
                   idle(1)   long sharp icicle under a small rime clump
                   shake(2)  looping wobble, hairline cracks at the root, ice crumbs dropping
                   fall(1)   the same icicle broken free (no clump), faint motion streaks
                   shatter(5) burst of ice shards drawn LOW in the frame: the engine puts the frame
                             bottom on the floor where the icicle lands (bottom row = floor)
hf_icefall  32x48  frozen-waterfall segments the engine stacks vertically (bottom-anchored)
                   top(1)    water pouring over a stone lip, frozen mid-flow
                   mid(4)    vertically tileable frozen column, a slow glint travelling down (loop)
                   bottom(1) splash frozen into a mound at the base (bottom row = floor)

1px K outline, light from upper-left, pale blue-white ice with darker blue edges.
"""
import math
from envlib import C, ramp, K, T, h01, clamp, blank
from env_props import Spr
from hoarfrost_tiles import ICE, SNOW, ST

# frozen-fall ice: same hue as ICE but greyer and a step darker so the column stays in the background
FALL = ramp("0c1824", "112434", "183247", "22425a", "305670", "446e88", "5f8aa2", "8cb3c8", "c6e2ee")

# =========================================================================== icicle
ROOT_Y = 3          # where the icicle body starts under the rime clump
LEN = 26            # body length (root -> tip)
RW = 3.2            # half-width at the root (~6-7 px wide)


def icicle_body(s, cx, top, shear=0.0, crack=False, hw0=RW, length=LEN):
    """Long tapering icicle: darker blue edges, pale core, bright specular streak left of centre,
    a couple of slight ring bulges (it grew in drips)."""
    for j in range(length):
        t = j / (length - 1)
        hw = hw0 * (1 - t) ** 0.9 + 0.35
        hw *= 1 + 0.10 * math.sin(t * 17)                         # growth rings
        c0 = cx + shear * t * t * length / 26
        y = top + j
        for x in range(int(c0 - hw) - 1, int(c0 + hw) + 2):
            dx = x + 0.5 - c0
            if abs(dx) > hw:
                continue
            u = (dx + hw) / (2 * hw)                               # 0 left edge .. 1 right edge
            if u < 0.16:
                c = ICE[5]
            elif u < 0.36:
                c = ICE[8] if t < 0.75 else ICE[7]                # specular streak
            elif u < 0.62:
                c = ICE[7] if t < 0.5 else ICE[6]
            elif u < 0.84:
                c = ICE[5]
            else:
                c = ICE[3]
            if hw < 0.9:
                c = ICE[6]
            s.set(x, y, c)
    if crack:
        for (x, y) in ((cx - 2, top + 1), (cx - 1, top + 2), (cx, top + 2), (cx + 1, top + 3), (cx + 2, top + 3)):
            s.set(x, y, ICE[1])


def rime_clump(s, cx):
    """The frozen anchor on the ceiling (row 0 = ceiling contact)."""
    for y in range(0, ROOT_Y + 1):
        hw = (5, 4.5, 3.8, 3.4)[y]
        for x in range(int(cx - hw), int(cx + hw) + 1):
            dx = x + 0.5 - cx
            if abs(dx) > hw:
                continue
            c = SNOW[3] if dx < -1 else SNOW[2] if dx < 2 else SNOW[1]
            if y == 0:
                c = SNOW[1]
            s.set(x, y, c)


def icicle():
    Wd, Hd = 16, 32
    cx = 8.0
    frames = []

    def fr(ms, s):
        frames.append({"ms": ms, "cels": {"Icicle": s.img}})

    # idle
    s = Spr(Wd, Hd)
    icicle_body(s, cx, ROOT_Y)
    rime_clump(s, cx)
    s.outline()
    fr(200, s)
    # shake: wobble (tip swings), cracks at the root, crumbs falling
    for k, sh in enumerate((1.4, -1.4)):
        s = Spr(Wd, Hd)
        icicle_body(s, cx, ROOT_Y, shear=sh, crack=True)
        rime_clump(s, cx)
        s.outline()
        for (x, y) in (((4, 8), (12, 14), (5, 19)), ((11, 6), (3, 13), (12, 21)))[k]:
            s.set(x, y, SNOW[3])
            s.set(x, y + 1, ICE[5])
        s.set(cx - 1 + k * 2, 1, ICE[1])                           # crack line through the clump
        fr(70, s)
    # fall: broken free, the clump stays on the ceiling -> only the body, with motion streaks
    s = Spr(Wd, Hd)
    icicle_body(s, cx, ROOT_Y + 1)
    for x in range(5, 12):                                         # jagged broken top
        if h01(x, 0, 3) < 0.5:
            s.set(x, ROOT_Y + 1, T)
    s.outline()
    for (x, y0, L) in ((3, 2, 9), (13, 4, 11), (2, 14, 6), (14, 16, 7), (5, 0, 4), (11, 0, 5)):
        for j in range(L):
            if s.get(x, y0 + j)[3] == 0:
                s.set(x, y0 + j, ICE[3] if j < L - 2 else ICE[2])
    fr(100, s)
    # shatter: impact at the bottom centre (row 31 = floor): the tip bursts, chunky shards fly out
    # radially under gravity, a soft puff of powder snow spreads and settles.
    SHARDS = [((0, 0, 8), (0, 1, 6), (1, 1, 3), (0, 2, 2)),            # little wedges (x, y, ICE lv)
              ((0, 0, 8), (1, 0, 6), (1, 1, 2)),                        # unoutlined: the dark lv-2/3
              ((1, 0, 8), (0, 1, 7), (1, 1, 5), (1, 2, 2)),             # pixel is their shaded edge
              ((0, 0, 7), (1, 0, 5), (1, 1, 2))]
    # (vx, vy, shard, spin) per shard, px per frame
    FLY = [(-3.4, -1.6, 0, 0), (-2.0, -3.6, 2, 1), (0.3, -4.6, 1, 1), (2.2, -3.4, 0, 0), (3.5, -1.8, 3, 0)]
    ix, iy = 8, 29
    for k in range(5):
        s = Spr(Wd, Hd)
        if k == 0:
            icicle_body(s, cx, 18, hw0=2.4, length=11)            # the tip jammed into the floor
            for (x, y, c) in ((5, 29, 7), (4, 30, 5), (11, 29, 7), (12, 30, 5), (6, 30, 8), (10, 30, 8)):
                s.set(x, y, ICE[c])                                # first chips spraying sideways
            s.outline()
            for (x, y) in ((8, 16), (3, 27), (13, 27), (8, 14)):
                s.set(x, y, ICE[8])                                # glints of the crack
            fr(50, s)
            continue
        t = (0, 1.0, 1.9, 2.7, 3.4)[k]
        if k == 1:                                                 # impact flash: short radial rays
            for ang in (200, 235, 270, 305, 340):
                for j in range(2, 5):
                    x = ix + 0.5 + j * math.cos(math.radians(ang)) * 1.3
                    y = iy + 1 + j * math.sin(math.radians(ang))
                    s.set(x, y, ICE[8] if j < 4 else ICE[6])
        for (vx, vy, sh, spin) in FLY:
            x = ix + vx * t
            y = iy + vy * t + 1.1 * t * t
            landed = y >= 29
            if landed:
                y = 29
            if not (0 <= x <= 14) or (k == 4 and not landed):
                continue
            pts = SHARDS[sh]
            if (spin and k % 2) or landed:                          # tumble / lie flat once landed
                pts = tuple((py, px_, c) for (px_, py, c) in pts)
            for (px_, py, c) in pts:
                s.set(x + px_, y + py - (1 if landed else 0), ICE[c])
        # powder-snow puff (soft): a low dome of motes that widens and thins out
        r = 2.0 + k * 2.0
        n = (0, 9, 11, 8, 4)[k]
        for i in range(n):
            a_ = math.pi * (i + 0.5) / n
            x = ix + r * math.cos(a_) * 1.3
            y = 31 - r * math.sin(a_) * 0.5 - (k - 2) * 0.7 * (k > 2)
            if s.get(x, y)[3] == 0:
                s.set(x, y, SNOW[3] if k < 3 else SNOW[2] if k < 4 else SNOW[1])
        if k >= 3:                                                 # crumbs on the floor
            for x in (3, 5, 10, 12):
                if s.get(x, 31)[3] == 0:
                    s.set(x, 31, ICE[5] if x % 2 else SNOW[2])
        if k == 4:
            s.set(6, 27, ICE[8])
            s.set(11, 25, ICE[7])
        fr((50, 60, 70, 90, 110)[k], s)
    tags = [("idle", 0, 0), ("shake", 1, 2), ("fall", 3, 3), ("shatter", 4, 8)]
    return Wd, Hd, ["Icicle"], frames, tags


# =========================================================================== frozen waterfall
FW = 32
FH = 48


def col_edges(y):
    """Left/right edge of the frozen column at frame row y (periodic over 48 -> tiles vertically)."""
    a = 2 * math.pi * y / FH
    xl = 6.5 + 1.2 * math.sin(a) + 0.8 * math.sin(2 * a + 1.3) + 0.5 * math.sin(3 * a + 0.4)
    xr = 25.5 + 1.0 * math.sin(a + 2.0) + 0.9 * math.sin(2 * a + 0.2) - 0.5 * math.sin(3 * a + 2.2)
    return xl, xr


def flow_px(x, y, xl, xr, glint=None):
    """Colour of the frozen column: semi-dark blue ice built of rounded vertical flutes (each lit on
    its left), outer flutes darker, lit left rim; periodic in y (tiles vertically)."""
    u = (x + 0.5 - xl) / (xr - xl)
    a = 2 * math.pi * y / FH
    NR = 4
    uu = u * NR
    ri = int(clamp(uu, 0, NR - 0.001))
    fu = uu - ri
    base = (4, 4, 3, 2)[ri]
    lv = base + (1 if fu < 0.22 else 0) - (1 if fu > 0.8 else 0)
    if u < 0.07:
        lv = 6
    elif u > 0.92:
        lv = 1
    if glint is not None and ri == 1:
        d = (y - glint) % FH
        if d > FH / 2:
            d -= FH
        if abs(d) < 3.5 and fu < 0.6:
            lv = 6 if abs(d) < 1.5 else 5
    return FALL[int(clamp(lv, 0, 8))]


def icefall():
    frames, tags = [], []

    def draw_column(s, y0, y1, glint=None):
        for y in range(y0, y1):
            xl, xr = col_edges(y)
            for x in range(int(xl), int(xr) + 1):
                if xl <= x + 0.5 <= xr:
                    s.set(x, y, flow_px(x, y, xl, xr, glint))

    def outline_sides(s):
        """Outline only left/right (keeps the column open at top/bottom so segments join)."""
        px = s.px
        adds = []
        for y in range(FH):
            for x in range(FW):
                if px[x, y][3]:
                    continue
                if (x + 1 < FW and px[x + 1, y][3] and px[x + 1, y] != K) or \
                   (x - 1 >= 0 and px[x - 1, y][3] and px[x - 1, y] != K):
                    adds.append((x, y))
        for (x, y) in adds:
            px[x, y] = K

    # ---------------------------------------------------------------- top: stone lip + frozen pour
    s = Spr(FW, FH)
    # the water arcs out over the lip, then drops into the column profile
    for y in range(6, FH):
        t = clamp((y - 6) / 20.0)
        xl1, xr1 = col_edges(y)
        xl = 3 + (xl1 - 3) * t ** 0.7 + 3 * (1 - t) * (1 - t)
        xr = 23 + (xr1 - 23) * t ** 0.6 + 6 * math.sin(math.pi * min(1, t * 1.4)) * (1 - t)
        for x in range(int(xl), int(xr) + 1):
            if xl <= x + 0.5 <= xr:
                c = flow_px(x, y, xl, xr)
                if y < 12:                                         # bright crest where it curls over
                    u = (x + 0.5 - xl) / (xr - xl)
                    c = FALL[7] if y == 6 else FALL[6] if u < 0.7 else FALL[4]
                s.set(x, y, c)
    # stone lip (channel spout) the water pours over
    for y in range(0, 8):
        for x in range(0, 27):
            if y > 5 and x > 22:
                continue
            c = ST[8] if y == 2 else ST[6] if x < 2 else ST[5] if y < 6 else ST[3]
            if y < 2:
                c = SNOW[3] if y == 0 else SNOW[2]
            if x in (9, 19) and 2 < y < 7:
                c = ST[2]
            if y == 7:
                c = ST[2]
            s.set(x, y, c)
    for x in range(3, 22):                                         # water sheet on the lip, frozen
        s.set(x, 5, FALL[5] if x % 4 else FALL[7])
        s.set(x, 6, FALL[4])
    for (x, L) in ((24, 5), (26, 3), (2, 4)):                      # icicles off the lip ends
        for j in range(L):
            s.set(x, 8 + j, FALL[6] if j < L - 1 else FALL[4])
    s.outline()
    frames.append({"ms": 200, "cels": {"Icefall": s.img}})
    tags.append(("top", 0, 0))
    # ---------------------------------------------------------------- mid: tileable column, glint
    for f in range(4):
        s = Spr(FW, FH)
        draw_column(s, 0, FH, glint=f * FH / 4 + 4)
        outline_sides(s)
        frames.append({"ms": 160, "cels": {"Icefall": s.img}})
    tags.append(("mid", 1, 4))
    # ---------------------------------------------------------------- bottom: frozen splash mound
    s = Spr(FW, FH)
    draw_column(s, 0, 30)
    for y in range(22, FH):
        t = (y - 22) / (FH - 23)
        xl0, xr0 = col_edges(min(y, 29))
        hw = 16 * math.sin(math.pi / 2 * t) ** 0.8
        xl = min(xl0, 16 - hw) - (1 if y > 44 else 0)
        xr = max(xr0, 16 + hw) + (1 if y > 44 else 0)
        for x in range(int(xl), int(xr) + 1):
            if not (xl <= x + 0.5 <= xr):
                continue
            u = (x + 0.5 - xl) / max(1, xr - xl)
            if y < 30 and xl0 <= x + 0.5 <= xr0:
                continue                                          # column already drawn
            lv = 5 if u < 0.25 else 4 if u < 0.5 else 3 if u < 0.8 else 2
            if y > 42:
                lv -= 1
            s.set(x, y, FALL[lv])
    # frozen splash spikes flaring out of the mound
    for (x0, y0, dx, L) in ((5, 38, -1, 7), (26, 37, 1, 7), (9, 33, -1, 5), (22, 32, 1, 5), (2, 43, -1, 3),
                            (29, 43, 1, 3)):
        for j in range(L):
            s.set(x0 + dx * (j // 2), y0 - j, FALL[7] if j == L - 1 else FALL[5])
    # rime crust + highlights on the mound
    for (x, y) in ((8, 36), (7, 37), (11, 34), (6, 40), (12, 38), (4, 42)):
        s.set(x, y, FALL[7])
    for x in range(0, FW):
        if s.get(x, FH - 1)[3]:
            s.set(x, FH - 1, FALL[1])
    s.outline()
    frames.append({"ms": 200, "cels": {"Icefall": s.img}})
    tags.append(("bottom", 5, 5))
    return FW, FH, ["Icefall"], frames, tags


PROPS = {"hf_icicle": icicle, "hf_icefall": icefall}
