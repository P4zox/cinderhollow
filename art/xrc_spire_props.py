"""Small props for the Stormward Spire expansion (xrc_sp_*). Each builder returns (w, h, layers, frames, tags).

xrc_sp_hut      80x64   idle(1) rattle(4)   fisher's hut against the sea wall; flat roof edge on rows 0-4
xrc_sp_nets     48x48   sway(4)             net drying rack, cork floats, a storm lantern on the hook
xrc_sp_boat     48x20   bob(4)              moored clinker boat, furled patched sail, keel on the bottom rows
xrc_sp_crates   32x24   idle(1)             fish crates, a barrel, a coil of rope
xrc_sp_pipe     16x48   idle(1)             iron outflow pipe hung from the ceiling (top-anchored), dripping
xrc_sp_grate    48x48   idle(1) warn(2) burst(6)   round storm-drain grate; the burst gout blasts to the RIGHT
xrc_sp_pennant  16x32   loop(6)             tattered pennant on a leaning pole
xrc_sp_winch    32x32   idle(1)             kite-line winch drum on posts, crank, line leaving the top
xrc_sp_bignest  64x32   idle(1)             storm-crow nest of driftwood, bones, rope, trinkets
xrc_sp_railing  48x16   idle(1)             iron balustrade on a stone kerb, post on the left (tiles every 48 px)
"""
import math, random
from xrc_spire_kit import *                                          # noqa: F401,F403
from xrc_spire_kit import (Spr, K, T, h01, clamp, bt, ST, SHEEN, GLINT, SALT, SEA, AMBER, RUST, VERD, IRON, WOOD,
                           WHEAT, GRASS, BONE, CLOTH, LICHEN, CANVAS, FLAME, stone_level, TAR, GFLOAT, GBLUE, DRIFT,
                           OCHRE, FRED, flame, thick_line, fill_poly, rope, sag_pts, glass_float, cork_float, outline)


# =========================================================================== fisher's hut
HUT_WIN = (16, 19, 27, 28)          # warm window interior (x0, y0, x1, y1)


def _shutter(s, hinge_x, side, theta, top=18, bot=29, width=6):
    """Plank shutter hinged at hinge_x. side -1 = opens to the left of the hinge, +1 to the right.
    theta 0 = flat open against the wall, 180 = closed over the window. Returns the free-edge (x, y_mid)."""
    ct = math.cos(math.radians(theta))
    pw = max(1, int(round(abs(width * ct))))
    d = side if ct >= 0 else -side
    edge = 20 < theta < 160
    inner = ct >= 0                                   # we see the face that meets the glass
    h = bot - top
    xs = []
    for i in range(pw):
        x = hinge_x + d * (1 + i)
        xs.append(x)
        board = int(i * 2 / pw) if pw > 1 else 0
        for y in range(top, bot + 1):
            lv = 3.2 + (0.7 if board == 0 else 0) * (1 if d < 0 else -1) * -1
            if not inner:
                lv -= 0.6
            if 40 < theta < 140:
                lv -= 0.8                               # turned away from the light
            if (i == pw // 2 and pw >= 4) or (pw >= 2 and i == pw - 1 and edge):
                lv -= 1.2
            c = GBLUE[int(clamp(lv, 1, 5))]
            if (h01(i, y // 3, 5) < 0.12):
                c = WOOD[3]                              # paint flaked to bare wood
            s.set(x, y, c)
        # ledges + Z brace
        for y in (top + 1, bot - 1):
            s.set(x, y, WOOD[4] if y == top + 1 else WOOD[2])
        yb = top + 2 + (h - 4) * (i / max(1, pw - 1))
        s.set(x, round(yb), WOOD[4])
        s.set(x, round(yb) + 1, WOOD[2])
    fx = xs[-1]
    for y in range(top, bot + 1):
        s.set(fx + d, y, TAR[0])                        # thin dark gap / edge
    s.set(hinge_x, top + 2, IRON[5])
    s.set(hinge_x, bot - 2, IRON[4])
    return fx, (top + bot) // 2


def hut():
    Wd, Hd = 80, 64
    base = Spr(Wd, Hd)
    s = base
    # ---- stone course (fieldstone footing)
    for y in range(49, 64):
        for x in range(3, 73):
            sl = stone_level(x + 3, y - 50, 8, 5, 7)
            lv = 6.0 - (x - 3) / 70 * 2.2
            if y == 49:
                lv = 8.4 - (x - 3) / 70 * 2.0 if (x + 2) % 11 else 5.5    # capping ledge, a joint here and there
            elif sl is None:
                lv = 2
            else:
                lv += sl * 0.8
                if (y - 50) % 5 == 0:
                    lv += 0.8
            if y >= 62:
                lv -= 1.2
            s.set(x, y, ST[int(clamp(lv, 1, 10))])
    for x in range(3, 73):                                # salt crust + weed at the foot
        if h01(x, 0, 61) < 0.22:
            s.set(x, 62, SALT[0])
        if h01(x // 3, 1, 62) < 0.3:
            s.set(x, 63, GRASS[2])
            if x % 3 == 1:
                s.set(x, 62, GRASS[3])
    # ---- tarred plank walls
    for x in range(6, 70):
        pi_, px_ = (x - 6) // 5, (x - 6) % 5
        tone = (h01(pi_, 0, 31) - 0.5) * 1.4
        jy = 14 + int(h01(pi_, 1, 33) * 26)
        for y in range(5, 45):
            if px_ == 4:
                c = TAR[0]
            else:
                lv = 4.2 - (x - 6) / 64 * 1.6 + tone
                if px_ == 0:
                    lv += 0.8
                elif px_ == 3:
                    lv -= 0.8
                if y < 10:
                    lv -= 1.8 - (y - 5) * 0.3                # under the eave
                if y == jy:
                    lv = 0.4                              # butt joint
                elif y == jy + 1:
                    lv += 0.7
                c = TAR[int(clamp(lv, 0, 6))]
            s.set(x, y, c)
        # wet gloss running down some planks
        if px_ == 1 and h01(pi_, 3, 34) < 0.45:
            y0 = 11 + int(h01(pi_, 4, 35) * 14)
            for y in range(y0, y0 + 5 + int(h01(pi_, 5, 36) * 8)):
                if y != jy:
                    s.set(x, y, SHEEN[2])
            s.set(x, y0 + 1, SHEEN[1])
    # sole plate on the stone
    for x in range(4, 72):
        s.set(x, 45, WOOD[5] if x < 60 else WOOD[4])
        s.set(x, 46, WOOD[3])
        s.set(x, 47, WOOD[3] if (x % 13) else WOOD[1])
        s.set(x, 48, WOOD[1])
    # corner posts
    for y in range(5, 45):
        s.set(5, y, WOOD[4])
        s.set(6, y, WOOD[3])
        s.set(69, y, WOOD[2])
        s.set(70, y, WOOD[1])
    # ---- door
    for x in range(46, 59):
        s.set(x, 17, WOOD[5])
        s.set(x, 18, WOOD[3])
    for y in range(19, 45):
        s.set(46, y, WOOD[4])
        s.set(58, y, WOOD[2])
        for x in range(47, 58):
            b = (x - 47) % 4
            lv = 2.6 + (0.9 if b == 0 else 0) - (1.2 if b == 3 else 0)
            if y < 22:
                lv -= 1
            s.set(x, y, TAR[int(clamp(lv, 0, 6))])
    for yy in (23, 39):
        for x in range(47, 56):
            s.set(x, yy, RUST[3] if x < 50 else RUST[2])
            s.set(x, yy + 1, RUST[1])
        s.set(47, yy, IRON[5])
    for (x, y, c) in ((55, 31, IRON[5]), (56, 32, IRON[3]), (55, 34, IRON[2]), (54, 32, IRON[4]), (54, 33, IRON[4]),
                      (56, 33, IRON[2]), (55, 30, IRON[3])):
        s.set(x, y, c)                                    # ring pull
    # ---- window: frame, warm panes, sill
    x0, y0, x1, y1 = HUT_WIN
    for x in range(x0 - 1, x1 + 2):
        s.set(x, y0 - 1, WOOD[5])
        s.set(x, y1 + 1, WOOD[2])
    for y in range(y0 - 1, y1 + 2):
        s.set(x0 - 1, y, WOOD[4])
        s.set(x1 + 1, y, WOOD[2])
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u, v = (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
            lv = 3.6 - u * 0.9 - v * 0.9
            if (x - 18) ** 2 + (y - 25.5) ** 2 < 3:
                lv += 0.7                                 # the lamp inside, low on the left
            c = AMBER[int(clamp(lv, 1, 4))]
            if x == 21 or y == 23:
                c = WOOD[1]                               # mullion + transom
            s.set(x, y, c)
    for y in range(19, 23):
        s.set(25, y, WOOD[1] if y < 21 else TAR[2])       # a hanging line of drying fish, dark on the glow
    s.set(24, 22, TAR[2])
    s.set(26, 22, TAR[2])
    s.set(17, 20, AMBER[5])
    for x in range(x0 - 2, x1 + 3):
        s.set(x, y1 + 2, AMBER[1] if x0 <= x <= x1 else WOOD[5])     # sill, catching the warm spill
        s.set(x, y1 + 3, WOOD[2])
    # cleat for the left shutter's lashing
    s.set(8, 33, IRON[4])
    s.set(9, 33, IRON[3])
    s.set(8, 34, IRON[2])
    # ---- the wall net (draped between two nails right of the door)
    for y in range(9, 40):
        t = (y - 9) / 31
        l = 61 - int(1.5 * math.sin(t * math.pi))
        r = 67 + int(1.0 * math.sin(t * math.pi * 0.8))
        for x in range(l, r + 1):
            u, v = x - l, y - 9
            strand = (x - 60) % 3 == 0
            mesh = (u + v) % 6 == 0 or (u - v) % 6 == 0
            if strand:
                s.set(x, y, LICHEN[2] if x < 65 else LICHEN[1])
            elif mesh:
                s.set(x, y, LICHEN[1])
    for x in range(60, 69):
        s.set(x, 9, WHEAT[2])
    s.set(60, 9, IRON[5])
    s.set(68, 9, IRON[5])
    # ---- roof slab (flat, walkway lies on row 0)
    for x in range(1, 79):
        c0 = WOOD[5] if (x % 6) else WOOD[3]
        if h01(x, 0, 41) < 0.2:
            c0 = SHEEN[1]
        s.set(x, 0, c0)
        s.set(x, 1, WOOD[3] if (x % 6) else WOOD[2])
        s.set(x, 2, TAR[4] if x < 60 else TAR[3])
        s.set(x, 3, TAR[2])
        s.set(x, 4, TAR[1])
    for jx in range(8, 72, 9):                           # joist ends
        s.set(jx, 5, WOOD[4])
        s.set(jx + 1, 5, WOOD[3])
        s.set(jx, 6, WOOD[2])
        s.set(jx + 1, 6, WOOD[1])
    # ---- crooked stovepipe out of the right wall, cowl under the eave
    pipe = [(71, 27), (72, 27), (73, 27)]
    for y in range(27, 16, -1):
        pipe.append((73, y))
    for y in range(16, 11, -1):
        pipe.append((74, y))
    for y in range(11, 8, -1):
        pipe.append((73, y))
    for (px_, py_) in pipe:
        vertical = px_ >= 73 and py_ < 27
        if vertical:
            s.set(px_ - 1, py_, IRON[5])
            s.set(px_, py_, IRON[3])
            s.set(px_ + 1, py_, IRON[1])
        else:
            s.set(px_, py_ - 1, IRON[5])
            s.set(px_, py_, IRON[3])
            s.set(px_, py_ + 1, IRON[1])
        if h01(px_, py_, 44) < 0.18:
            s.set(px_, py_, RUST[3])
    for (x, y, c) in ((72, 16, IRON[4]), (73, 12, IRON[4]), (74, 11, IRON[2])):
        s.set(x, y, c)                                   # the kinks
    for (x, y, c) in ((72, 8, IRON[5]), (73, 8, IRON[4]), (74, 8, IRON[3]), (75, 8, IRON[3]), (76, 8, IRON[2]),
                      (73, 9, IRON[3]), (74, 9, IRON[2]), (75, 9, IRON[2]), (76, 9, RUST[2]),
                      (72, 7, IRON[4]), (73, 7, IRON[5]), (74, 7, IRON[5]), (75, 7, IRON[4]), (76, 7, IRON[4]),
                      (77, 7, IRON[3]), (77, 8, TAR[0]), (77, 9, TAR[0]), (77, 10, IRON[2]), (76, 10, IRON[1])):
        s.set(x, y, c)                                   # bent cowl, mouth to the right
    for yy in (22, 14):
        s.set(71, yy, IRON[2])                           # wire straps to the wall
    s.set(72, 20, RUST[3])
    s.set(73, 24, RUST[2])
    base_img = base.img

    def frame(theta_l, theta_r, ph, still=False):
        f = Spr(Wd, Hd)
        f.img = base_img.copy()
        f.px = f.img.load()
        # float string under the eave (sways in the gust)
        pts = sag_pts(8, 7, 42, 7, 3, 34)
        rope(f, pts, (WHEAT[2], WHEAT[1]), 3)
        f.set(8, 7, IRON[5])
        f.set(42, 7, IRON[5])
        for k, fx in enumerate((12, 17, 23, 29, 35, 39)):
            hx, hy = pts[fx - 8]
            sw = 0 if still else round(math.sin(ph + k * 1.3) * 1.0 + 0.4)
            L = 2 + (k % 2)
            f.set(hx, hy + 1, WHEAT[1])
            f.set(hx + sw * 0.5, hy + 2, WHEAT[1])
            if k % 2 == 0:
                glass_float(f, hx - 1 + sw, hy + L)
            else:
                cork_float(f, hx + sw, hy + L)
        # the net's foot floats
        for k, (nx, ny) in enumerate(((61, 39), (65, 40))):
            sw = 0 if still else round(math.sin(ph + 2 + k))
            cork_float(f, nx + sw, ny)
        # shutters; the left one lashed to its cleat, the right one's line snapped (it bangs in the wind)
        fxl, fyl = _shutter(f, x0 - 2, -1, theta_l)
        rope(f, [(fxl, fyl + 2), (fxl - 0.5, fyl + 5), (8, 33)], (WHEAT[3], WHEAT[2]), 2)
        fxr, fyr = _shutter(f, x1 + 2, 1, theta_r)
        dang = 0 if still else math.sin(ph) * 1.5
        rope(f, [(fxr, fyr + 1), (fxr + dang * 0.5, fyr + 4), (fxr + dang, fyr + 7)], (WHEAT[3], WHEAT[2]), 2)
        f.outline()
        return f.img

    frames = [{"ms": 1000, "cels": {"Hut": frame(0, 0, 0, still=True)}}]
    TL = [0, 10, 3, 16]
    TR = [2, 72, 158, 96]
    MS = [90, 80, 70, 110]
    for i in range(4):
        frames.append({"ms": MS[i], "cels": {"Hut": frame(TL[i], TR[i], i * math.pi / 2)}})
    return Wd, Hd, ["Hut"], frames, [("idle", 0, 0), ("rattle", 1, 4)]


# =========================================================================== net drying rack
NETS_LAMP = (43, 17)


def nets():
    Wd, Hd = 48, 48
    frames = []
    for f in range(4):
        ph = f * math.pi / 2
        s = Spr(Wd, Hd)
        # poles (driftwood), a little splayed, and the crossbar
        thick_line(s, 8, 47, 10, 5, [DRIFT[5], DRIFT[3]])
        thick_line(s, 37, 47, 35, 6, [DRIFT[4], DRIFT[2]])
        s.set(9, 4, DRIFT[6])
        s.set(11, 3, DRIFT[5])                           # forked tip
        s.set(36, 5, DRIFT[5])
        s.set(34, 4, DRIFT[4])
        for x in range(4, 44):
            y = 7 + (x - 4) / 40 * 1.0
            s.set(x, y, DRIFT[5] if x < 30 else DRIFT[4])
            s.set(x, y + 1, DRIFT[2])
        # lashings
        for (lx, ly) in ((10, 7), (35, 8)):
            for (dx, dy) in ((-1, -1), (1, 1), (-1, 1), (1, -1), (0, 2)):
                s.set(lx + dx, ly + dy, WHEAT[3] if dy < 1 else WHEAT[2])
        # iron lantern arm off the right pole
        for x in range(37, 45):
            s.set(x, 11, IRON[4] if x < 42 else IRON[3])
        s.set(38, 12, IRON[3])
        s.set(39, 13, IRON[2])                           # strut
        s.set(44, 12, IRON[4])
        # a stone foot for each pole
        for (bx, c) in ((8, 0), (37, 1)):
            for x in range(bx - 3, bx + 4):
                s.set(x, 47, ST[5 - c] if x < bx + 1 else ST[3])
                if abs(x - bx) < 3:
                    s.set(x, 46, ST[7 - c] if x < bx else ST[5])
        s.outline()
        # ---- nets over the bar (no outline: the mesh is see-through). Gathered vertical strands (the folds) with a
        # sparse diamond mesh between them; the foot sways downwind and carries the cork floats.
        for (nl, nr, drop, seed, pal) in ((12, 24, 32, 1, WHEAT), (24, 33, 24, 2, LICHEN), (4, 8, 18, 3, LICHEN)):
            sw_amp = (0.9 + 0.9 * math.sin(ph + seed)) * 2.6
            hem = []
            for y in range(10, 10 + drop):
                t = (y - 10) / drop
                sway = sw_amp * t ** 1.7
                belly = 1.6 * math.sin(math.pi * t)
                l = nl + sway - belly * 0.5 + 1.2 * t
                r = nr + sway + belly * 0.3 - 1.4 * t
                for x in range(int(round(l)), int(round(r)) + 1):
                    p = x - sway - nl
                    pi_ = int(math.floor(p + 0.5))
                    # uneven bottom: the middle strands hang lower
                    mid = (x - (l + r) / 2) / max(1.0, (r - l) / 2)
                    if y > 10 + drop - 1 + 0.5 * (1 - mid * mid) - 0.5:
                        continue
                    if pi_ % 4 == 0:
                        c = pal[3] if t < 0.15 else pal[2]
                    elif (pi_ + y) % 8 == 0 or (pi_ - y) % 8 == 0:
                        c = pal[1]
                    else:
                        c = None
                    if c is not None:
                        s.set(x, y, c)
                hem.append((l, r, y))
            # the hem line + floats
            l, r, yb = hem[-1]
            for x in range(int(round(l)), int(round(r)) + 1):
                mid = (x - (l + r) / 2) / max(1.0, (r - l) / 2)
                s.set(x, yb + 0.5 * (1 - mid * mid), pal[2])
            for x in range(int(round(l)) + 2, int(round(r)), 5):
                mid = (x - (l + r) / 2) / max(1.0, (r - l) / 2)
                yy = round(yb + 0.5 * (1 - mid * mid)) + 1
                s.set(x, yy, WHEAT[4])
                s.set(x + 1, yy, WHEAT[3])
                s.set(x, yy + 1, WHEAT[3])
                s.set(x + 1, yy + 1, WHEAT[2])
            # the gathered head of the net over the bar
            for x in range(nl, nr + 1):
                y = 7 + (x - 4) / 40
                s.set(x, y - 1, pal[3] if (x % 3) else pal[2])
                s.set(x, y + 2, pal[2])
        # ---- the storm lantern on the hook (swings a little)
        sw = round(math.sin(ph + 0.7) * 0.9)
        lx = 44 + sw
        s.set(44, 13, IRON[4])
        s.set(44 + sw * 0.5, 14, IRON[3])
        L = Spr(Wd, Hd)
        for x in range(lx - 2, lx + 3):
            L.set(x, 15, IRON[4] if x <= lx else IRON[2])
        for y in range(16, 21):
            for x in range(lx - 2, lx + 3):
                L.set(x, y, AMBER[2] if x <= lx else AMBER[1])
            L.set(lx - 2, y, IRON[4])
            L.set(lx + 2, y, IRON[2])
        flame(L, lx + 0.5, 20, 3 + (f % 2), 1.0, f / 4, pal=FLAME, seed=4)
        for x in range(lx - 2, lx + 3):
            L.set(x, 21, IRON[3])
        L.outline()
        L.set(lx - 1, 17, AMBER[5] if f % 2 == 0 else AMBER[4])
        s.img.alpha_composite(L.img)
        s.px = s.img.load()
        frames.append({"ms": 140, "cels": {"Nets": s.img}})
    return Wd, Hd, ["Nets"], frames, [("sway", 0, 3)]


# =========================================================================== moored boat
def _spline(u, pts):
    """Monotone-x Catmull-Rom through (u, y) knots."""
    u = clamp(u, pts[0][0], pts[-1][0])
    for i in range(len(pts) - 1):
        if pts[i][0] <= u <= pts[i + 1][0]:
            break
    p0 = pts[max(0, i - 1)][1]
    p1, p2 = pts[i][1], pts[i + 1][1]
    p3 = pts[min(len(pts) - 1, i + 2)][1]
    t = (u - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def boat():
    Wd, Hd = 48, 20
    frames = []
    for f in range(4):
        dy = [0, 0, 1, 1][f]
        pitch = [0.0, 0.6, 0.0, -0.6][f]               # bow up / down (px at the ends)
        s = Spr(Wd, Hd)

        def keel(x):                                    # bottom of the hull (y), stern x~4 .. bow x~46
            return _spline((x - 4) / 42, [(0, 14.0), (0.08, 17.4), (0.2, 18.8), (0.62, 18.8), (0.8, 16.8),
                                          (0.92, 12.0), (1.0, 5.0)])

        def sheer(x):                                   # the gunwale: low waist, a proud lifting bow
            return _spline((x - 4) / 42, [(0, 7.2), (0.3, 9.6), (0.55, 10.0), (0.8, 8.4), (0.93, 6.0), (1.0, 3.6)])

        def lift(x):
            return dy - pitch * (x - 24) / 21

        for x in range(4, 47):
            top, bot = sheer(x) + lift(x), keel(x) + lift(x)
            if bot <= top + 0.8:
                continue
            for y in range(int(math.floor(top)), int(math.ceil(bot)) + 1):
                if y < top - 0.5 or y > bot:
                    continue
                d = y - top
                if d < 1.0:
                    c = WOOD[6] if x < 32 else WOOD[5]         # gunwale capping
                elif d < 2.0:
                    c = CANVAS[2] if (x // 7) % 4 else TAR[4]      # a worn pale sheer stripe
                else:
                    band = (d - 2.0) / 2.6
                    k = int(band)
                    fr = band - k
                    lv = 3.0 - k * 0.7 - (x - 4) / 41 * 0.5
                    if fr < 0.35:
                        lv += 1.6                            # the clinker lap catches the light
                    c = TAR[int(clamp(lv, 0, 6))]
                s.set(x, y, c)
        # stem head (bow) curling up, and the transom
        for (x, y, c) in ((46, 3, WOOD[6]), (46, 2, WOOD[5]), (45, 2, WOOD[6])):
            s.set(x, y + lift(46), c)
        for y in range(9, 16):
            s.set(4, y + lift(4), WOOD[4] if y < 11 else TAR[3])
        # thole pins
        for tx in (14, 31):
            s.set(tx, sheer(tx) + lift(tx) - 1, WOOD[5])
        # mast stub (stepped at x=20) and a lateen yard slung aslant with the sail furled along it
        mx = 22
        top_m = 0 + dy
        for y in range(top_m, int(sheer(mx) + lift(mx))):
            s.set(mx, y, WOOD[5])
            s.set(mx + 1, y, WOOD[3])
        sway = [0, 1, 0, -1][f]
        ya, yb = (9.0, 8.5 + dy), (39.0, 2.0 + dy)   # yard ends (x, y): low aft, high forward
        n = 34
        for i in range(n + 1):
            t = i / n
            x = ya[0] + (yb[0] - ya[0]) * t
            y = ya[1] + (yb[1] - ya[1]) * t
            r = 1.9 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7
            for j in range(-int(r + 0.5), int(r + 0.5) + 1):
                lv = 4.2 - (j + r) / (2 * r + 0.01) * 2.8
                c = CANVAS[int(clamp(lv, 1, 5))]
                if 0.28 < t < 0.42:
                    c = FRED[int(clamp(lv, 1, 5))]          # a faded red patch
                s.set(x, y + j, c)
            if i % 7 == 4:                                  # gaskets
                s.set(x, y - r - 0.5, WHEAT[2])
                s.set(x, y + r + 0.5, WHEAT[1])
        for i in range(3):
            s.set(yb[0] + 1 + i, yb[1] - 0.5 + i * (0.6 + 0.4 * sway), WOOD[4])      # yard tip
        for i in range(5):                                  # a loose sail corner flogging off the yard's low end
            s.set(ya[0] - 1 - i * 0.6, ya[1] + 1 + i * 0.5 + (sway * i * 0.3), CANVAS[3 if i < 2 else 2])
        # mooring line off the stem, into the water
        rope(s, [(47, 4 + lift(46)), (47, 9 + dy), (47, 14 + dy)], (WHEAT[2], WHEAT[1]), 2)
        s.outline()
        s.set(9, sheer(9) + lift(9), SHEEN[0] if f % 2 == 0 else SHEEN[1])
        s.set(27, sheer(27) + lift(27), SHEEN[1])
        frames.append({"ms": 220, "cels": {"Boat": s.img}})
    return Wd, Hd, ["Boat"], frames, [("bob", 0, 3)]


# =========================================================================== crates, barrel, rope
def crates():
    Wd, Hd = 32, 24
    s = Spr(Wd, Hd)
    # barrel (left): bulging staves, cylinder lit from the left, three iron hoops
    bx, btop, bbot = 7, 8, 23
    for y in range(btop, bbot + 1):
        t = (y - btop) / (bbot - btop)
        hw = 4.0 + 1.1 * math.sin(math.pi * t)
        for x in range(int(round(bx - hw)), int(round(bx + hw)) + 1):
            nx = (x + 0.5 - bx) / (hw + 0.5)
            lv = 4.2 - nx * 2.0 - abs(nx) ** 3 * 1.0
            stave = int((nx + 1) * 3.5)
            if abs(((nx + 1) * 3.5) - round((nx + 1) * 3.5)) < 0.18 and abs(nx) < 0.8:
                lv -= 1.1                                   # stave seams, bending with the bulge
            c = WOOD[int(clamp(lv, 1, 7))]
            if y in (10, 15, 21):
                c = IRON[5] if nx < -0.3 else IRON[3] if nx < 0.4 else IRON[1]
            s.set(x, y, c)
    for x in range(bx - 3, bx + 4):
        s.set(x, btop - 1, WOOD[6] if x < bx + 1 else WOOD[4])   # the lid rim
    s.set(bx + 3, 16, RUST[3])
    s.set(bx + 4, 17, RUST[2])

    def crate(x0, y0, x1, y1, fish_gaps):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                ly = y - y0
                corner = x in (x0, x0 + 1, x1 - 1, x1)
                if corner:
                    c = WOOD[6] if x == x0 else WOOD[5] if x == x0 + 1 else WOOD[3] if x == x1 - 1 else WOOD[2]
                elif ly % 4 != 3:
                    lv = 4.6 - (1.2 if ly % 4 == 2 else 0) + (0.8 if ly % 4 == 0 else 0) - (x - x0) / (x1 - x0) * 1.4
                    c = WOOD[int(clamp(lv, 1, 7))]
                else:
                    c = TAR[0]
                s.set(x, y, c)
            if y == y1:
                for x in range(x0, x1 + 1):
                    s.set(x, y, WOOD[2])
        for (gx, gy) in fish_gaps:                       # a silver fish flank glinting through a gap
            s.set(gx, gy, SALT[0])
            s.set(gx + 1, gy, SALT[1])
            s.set(gx + 2, gy, SALT[0])
    crate(12, 14, 30, 23, [(16, 17), (24, 21)])
    crate(14, 6, 28, 13, [(20, 9)])
    # fish heaped over the top crate's rim: two silver bodies, a tail flipped up
    for (x, y, c) in ((16, 5, SALT[1]), (17, 5, SALT[2]), (18, 5, SALT[1]), (19, 5, SALT[0]), (20, 4, SALT[0]),
                      (20, 6, SALT[0]), (15, 5, SLATE[3]),
                      (22, 5, SALT[0]), (23, 5, SALT[1]), (24, 5, SALT[2]), (25, 5, SALT[1]), (26, 4, SALT[1]),
                      (27, 3, SALT[2]), (26, 3, SALT[0])):
        s.set(x, y, c)
    s.set(16, 4, SALT[0])
    # a coil of rope on the ground in front of the barrel, seen a little from above
    ccx, ccy = 10.5, 21.0
    for y in range(18, 24):
        for x in range(3, 19):
            e = ((x + 0.5 - ccx) / 6.6) ** 2 + ((y + 0.5 - ccy) / 2.6) ** 2
            if e > 1:
                continue
            r = math.sqrt(e)
            if r < 0.24:
                c = TAR[1]
            elif abs(r - 0.52) < 0.09 or abs(r - 0.8) < 0.07:
                c = WHEAT[1]                                # the grooves between turns
            else:
                c = WHEAT[3] if y + 0.5 < ccy else WHEAT[2]
                if r > 0.86 and y + 0.5 > ccy:
                    c = WHEAT[1]
            s.set(x, y, c)
    for x in range(6, 16):
        s.set(x, 23, WHEAT[1])
    for i in range(5):                                      # the loose end
        s.set(17 + i, 23, WHEAT[2] if i % 2 else WHEAT[3])
    s.outline()
    s.set(4, 12, SHEEN[1])
    s.set(4, 18, SHEEN[1])
    s.set(17, 5, GLINT)
    return Wd, Hd, ["Crates"], [{"ms": 1000, "cels": {"Crates": s.img}}], [("idle", 0, 0)]


# =========================================================================== outflow pipe (hung from the ceiling)
def pipe():
    Wd, Hd = 16, 48
    s = Spr(Wd, Hd)
    COLS = [IRON[4], IRON[5], IRON[4], IRON[3], IRON[2], IRON[1]]
    # ceiling flange + bolts
    for x in range(2, 14):
        s.set(x, 0, IRON[3])
        s.set(x, 1, IRON[4] if x < 9 else IRON[3])
        s.set(x, 2, IRON[2])
    s.set(3, 1, IRON[6])
    s.set(12, 1, IRON[5])
    for y in range(3, 35):
        for i, x in enumerate(range(5, 11)):
            c = COLS[i]
            # rust bleeding down from the joints
            if i in (2, 3) and (17 <= y <= 23 or 31 <= y) and h01(x, y // 2, 5) < 0.55:
                c = RUST[3] if i == 2 else RUST[2]
            if i == 1 and h01(x, y // 3, 6) < 0.12:
                c = RUST[4]
            s.set(x, y, c)
    for jy in (14, 28):                                     # collars
        for x in range(4, 12):
            s.set(x, jy, IRON[5] if x < 8 else IRON[3])
            s.set(x, jy + 1, IRON[3] if x < 8 else IRON[1])
        s.set(4, jy, IRON[6])
    # flared, rust-eaten mouth
    for x in range(3, 13):
        s.set(x, 35, IRON[4] if x < 8 else IRON[2])
        s.set(x, 36, RUST[2] if x < 7 else RUST[1])
    for x in range(5, 11):
        s.set(x, 37, ST[0])                                 # the dark bore
    s.set(4, 37, RUST[1])
    s.set(11, 37, RUST[1])
    # a strand of weed hanging off the lip
    for y in range(37, 42):
        s.set(4 - (y > 39), y, VERD[1] if y % 2 else VERD[2])
    s.outline()
    # the trickle + drips (no outline: pale water on the dark)
    for y in range(38, 42):
        s.set(8, y, SEA[9] if y < 40 else SEA[8])
    s.set(7, 38, SEA[7])
    s.set(8, 44, SEA[9])
    s.set(8, 45, SEA[8])
    s.set(8, 47, SEA[10])
    s.set(6, 12, SHEEN[0])
    s.set(6, 25, SHEEN[1])
    return Wd, Hd, ["Pipe"], [{"ms": 1000, "cels": {"Pipe": s.img}}], [("idle", 0, 0)]


# =========================================================================== storm-drain grate
GC = (24, 24)
WATER = [SEA[6], SEA[8], SEA[9], SEA[10], SEA[11], GLINT]


def _grate_stone():
    s = Spr(48, 48)
    cx, cy = GC
    for y in range(48):
        for x in range(48):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if 14.5 <= r <= 22.5:
                a = math.atan2(dy, dx)
                seg = int((a + math.pi) / (2 * math.pi) * 12 + 0.5) % 12
                aj = ((a + math.pi) / (2 * math.pi) * 12 + 0.5) % 1.0
                # bevel: the ring's face tilts inward; lit on the upper-left outer, lower-right inner
                nx, ny = dx / r, dy / r
                t = (r - 14.5) / 8
                face = (-nx * 0.7 - ny * 0.7) * (1 if t > 0.5 else -1)
                lv = 5.2 + face * 2.0 + (h01(seg, 0, 3) - 0.5) * 1.4
                if r > 21.6:
                    lv -= 1.2
                if r < 15.5:
                    lv = 2 + (1 if ny > 0 else 0)
                if aj < 0.06 or aj > 0.97:
                    lv = 1.5                                 # voussoir joint
                if seg == 3 and r > 15.5:                    # keystone at the top
                    lv += 1.0
                c = ST[int(clamp(lv, 1, 10))]
                s.set(x, y, c)
            elif r < 14.5:
                # the throat: darker at the top where the ring shades it
                lv = 1.2 + (dy / 14.5) * 0.9
                s.set(x, y, ST[int(clamp(lv, 0, 3))])
    return s


def _grate_iron(s, ox=0, oy=0):
    cx, cy = GC[0] + ox, GC[1] + oy
    for y in range(48):
        for x in range(48):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if 12.6 <= r <= 14.4:
                lit = -dx - dy
                s.set(x, y, IRON[5] if lit > 6 else IRON[3] if lit > -6 else IRON[2])
            elif r < 12.6:
                bx = (x - cx + 20) % 5
                if bx in (0, 1):
                    s.set(x, y, IRON[4] if bx == 0 else IRON[2])
                    if h01(x, y // 3, 9) < 0.15:
                        s.set(x, y, RUST[3])
                elif abs(y + 0.5 - cy) < 1.1:
                    s.set(x, y, IRON[4] if y < cy else IRON[2])
    for (dx, dy) in ((-10, 0), (10, 0), (0, -13), (0, 13)):
        s.set(cx + dx, cy + dy, IRON[6] if dx <= 0 and dy <= 0 else IRON[4])     # rivets on the ring


def _jet(s, f):
    """Seawater gout blasting to the right out of the grate. f 0..5 (burst). Drawn over everything."""
    cx, cy = GC
    reach = [36, 47, 47, 47, 44, 30][f]
    thick = [5.0, 8.5, 9.5, 8.5, 6.0, 3.0][f]
    rnd = random.Random(100 + f)
    for x in range(cx - 10, min(48, reach + 1)):
        u = max(0.0, x - cx)
        yc = cy + 0.012 * u * u + (1.0 if f >= 4 else 0)
        hw = thick * (0.75 + 0.35 * min(1, u / 14)) + 1.2 * math.sin(u * 0.55 - f * 1.9) + 0.8 * math.sin(u * 1.3 + f)
        if x < cx:
            hw = thick * 0.9 * math.sqrt(max(0, 1 - ((cx - x) / 11) ** 2)) + 0.5
        if f == 5:
            hw *= 0.8 if (x // 4) % 2 == 0 else 0.35          # breaking up
        for y in range(int(yc - hw) - 1, int(yc + hw) + 2):
            d = (y + 0.5 - yc) / max(hw, 0.5)
            if abs(d) > 1:
                continue
            stream = 0.5 + 0.5 * math.sin(y * 1.7 + u * 0.08 - f * 2.0)
            v = 3.6 - abs(d) * 2.4 + stream * 0.8 - (u / 30) * 0.8
            if d < -0.55:
                v += 0.6                                      # the lit top of the gout
            if abs(d) > 0.8:
                v = 0 if d > 0 else 1
            if abs(d) > 0.93:
                s.set(x, y, SEA[4] if d > 0 else SEA[5])
                continue
            s.set(x, y, WATER[int(clamp(v, 0, 5))])
    # the foam head + spray lumps at the leading edge and along the rims
    for i in range(22 if f < 5 else 12):
        a = rnd.uniform(-1, 1)
        u = rnd.uniform(4, reach - cx + 2)
        yc = cy + 0.012 * u * u
        x = cx + u
        y = yc + a * (thick + 1.5)
        if x < 48:
            s.set(x, y, SEA[10] if rnd.random() < 0.6 else SEA[11])
            if rnd.random() < 0.4:
                s.set(x + 1, y, SEA[9])
    if f in (1, 2, 3):
        for i in range(8):
            y = cy + rnd.uniform(-thick - 3, thick + 4)
            s.set(47 - rnd.randint(0, 3), y, SEA[11] if i % 2 else SEA[10])


def grate():
    frames = []
    stone = _grate_stone()

    def cel(ox=0, oy=0):
        s = Spr(48, 48)
        s.img = stone.img.copy()
        s.px = s.img.load()
        _grate_iron(s, ox, oy)
        s.outline()
        return s

    # idle: a damp stain below the grate
    s = cel()
    for y in range(39, 46):
        for x in (22, 23, 26):
            if s.get(x, y)[3] and s.get(x, y) != K:
                s.set(x, y, SHEEN[3] if y > 41 else ST[1])
    s.set(24, 40, SHEEN[2])
    frames.append({"ms": 1000, "cels": {"Grate": s.img}})
    # warn: water welling through the bars, the grate trembling
    for f in range(2):
        s = cel(ox=(0 if f == 0 else 1))
        rnd = random.Random(7 + f)
        for x in range(13, 37):
            dy_ = 24 + math.sqrt(max(0, 12.5 ** 2 - (x + 0.5 - 24) ** 2))
            if rnd.random() < 0.55:
                s.set(x + f, dy_ - rnd.randint(0, 2), SEA[8] if rnd.random() < 0.6 else SEA[9])
        for (x, L) in ((18, 7), (23, 11), (27, 9), (31, 5)):
            for y in range(36, 36 + L + f * 2):
                s.set(x + f, y, SEA[8] if y % 3 else SEA[9])
            s.set(x + f, 36 + L + f * 2 + 1, SEA[10])
        for i in range(5 + 4 * f):                           # spit of spray through the bars
            s.set(24 + rnd.randint(-10, 10), 24 + rnd.randint(-10, 10), SEA[10] if i % 2 else SEA[9])
        frames.append({"ms": 110, "cels": {"Grate": s.img}})
    # burst
    for f in range(6):
        s = cel(ox=(1 if f in (0, 1) else 0))
        _jet(s, f)
        frames.append({"ms": [60, 80, 80, 90, 100, 120][f], "cels": {"Grate": s.img}})
    return 48, 48, ["Grate"], frames, [("idle", 0, 0), ("warn", 1, 2), ("burst", 3, 8)]


# =========================================================================== storm pennant
def pennant():
    Wd, Hd = 16, 32
    frames = []
    for f in range(6):
        s = Spr(Wd, Hd)
        # pole: leaning a touch downwind, in a split rock
        for y in range(3, 31):
            x = 4 + (30 - y) * 0.07
            s.set(x, y, DRIFT[5] if y % 9 else DRIFT[3])
            s.set(x + 1, y, DRIFT[2])
        s.set(6, 2, IRON[5])
        s.set(6, 1, IRON[4])
        for x in range(1, 9):
            s.set(x, 31, ST[5] if x < 5 else ST[3])
            if 2 <= x <= 7:
                s.set(x, 30, ST[7] if x < 4 else ST[5])
        s.set(4, 29, WHEAT[2])
        s.set(6, 29, WHEAT[2])                                # wedges
        # the pennant: hoist at x=6, y 4..10, streaming right, travelling wave
        P = 2 * math.pi * f / 6
        L = 9.5 + 0.8 * math.sin(P * 2)
        for i in range(int(L) + 1):
            u = i / L
            x = 7 + i
            wave = 1.8 * u * math.sin(P - u * 5.0) + 0.6 * u
            slope = math.cos(P - u * 5.0)
            hw = 3.2 * (1 - u) + 0.8
            yc = 7 + wave
            for y in range(int(yc - hw), int(yc + hw) + 1):
                d = (y + 0.5 - yc) / hw
                if abs(d) > 1.05:
                    continue
                if u > 0.72 and abs(d) < 0.3:
                    continue                                   # swallowtail notch
                if h01(i, y - int(wave), 3) < 0.08 and u > 0.3:
                    continue                                   # holes
                lv = 3.6 + slope * 1.0 - d * 0.5
                c = CANVAS[int(clamp(lv, 1, 5))]
                if -0.25 < d < 0.3 and u < 0.7:
                    c = CLOTH[3] if slope > -0.2 else CLOTH[2]  # storm-blue stripe
                s.set(x, y, c)
        s.outline()
        frames.append({"ms": 90, "cels": {"Pennant": s.img}})
    return Wd, Hd, ["Pennant"], frames, [("loop", 0, 5)]


# =========================================================================== kite-line winch
WINCH_LINE = (18, 0)


def winch():
    Wd, Hd = 32, 32
    s = Spr(Wd, Hd)
    # stone footing
    for y in range(27, 32):
        for x in range(4, 28):
            lv = 7 - (x - 4) / 24 * 2 - (y - 27) * 0.6
            if y == 27:
                lv += 1.2
            if (x in (11, 20) and y > 27) or y == 29 and 0:
                lv = 2
            s.set(x, y, ST[int(clamp(lv, 1, 10))])
    # uprights with braces
    for (px_, lit) in ((6, 1), (24, 0)):
        for y in range(7, 27):
            s.set(px_, y, WOOD[5 + lit])
            s.set(px_ + 1, y, WOOD[4 + lit] if y % 6 else WOOD[2])
            s.set(px_ + 2, y, WOOD[2])
        for x in range(px_ - 1, px_ + 4):
            s.set(x, 6, WOOD[6] if x < px_ + 2 else WOOD[4])
    thick_line(s, 3, 26, 6, 19, [WOOD[4], WOOD[2]])
    thick_line(s, 29, 26, 26, 19, [WOOD[3], WOOD[1]])
    # drum: rope wound on a spool between flanges, cylinder lit from the top-left
    for y in range(10, 23):
        t = (y - 10) / 12
        for x in range(11, 22):
            lv = 4.0 - abs(t - 0.28) * 4.2 - (x - 11) / 10 * 0.5
            turn = (x - 11 + (1 if y > 16 else 0)) % 2              # each 2px column is one turn of line
            if turn == 1:
                lv -= 1.0
            c = WHEAT[int(clamp(lv, 0, 5))]
            s.set(x, y, c)
    for fx in (9, 10, 22, 23):
        for y in range(9, 24):
            t = (y - 9) / 14
            lv = 4.5 - abs(t - 0.35) * 5 - (0.8 if fx in (10, 23) else 0)
            s.set(fx, y, WOOD[int(clamp(lv, 1, 7))])
    # axle + crank (right)
    for x in range(8, 30):
        if s.get(x, 16)[3] == 0 or x > 26 or x < 9:
            s.set(x, 16, IRON[5] if x > 26 else IRON[4])
    s.set(29, 16, IRON[5])
    for y in range(16, 23):
        s.set(29, y, IRON[4])
        s.set(30, y, IRON[2])
    s.set(30, 23, WOOD[5])
    s.set(31, 23, WOOD[4])
    s.set(30, 24, WOOD[3])
    s.set(31, 24, WOOD[2])
    # pawl + ratchet teeth on the left flange
    s.set(8, 13, IRON[4])
    s.set(7, 12, IRON[5])
    # the line leaving the drum top, up and away
    for y in range(0, 10):
        s.set(WINCH_LINE[0] - (9 - y) * 0.12 + 1, y, WHEAT[2] if y % 2 else WHEAT[1])
    s.outline()
    s.set(12, 11, SHEEN[1])
    s.set(9, 11, SHEEN[1])
    return Wd, Hd, ["Winch"], [{"ms": 1000, "cels": {"Winch": s.img}}], [("idle", 0, 0)]


# =========================================================================== storm-crow nest
def bignest():
    Wd, Hd = 64, 32
    s = Spr(Wd, Hd)
    rnd = random.Random(11)
    cx, ry_top = 32, 11

    def bowl_hw(y):                                       # half-width of the bowl at row y
        t = (y - ry_top) / (31 - ry_top)
        return 28 - 12 * t ** 1.7

    # dark mass of the bowl
    for y in range(ry_top, 32):
        hw = bowl_hw(y)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            s.set(x, y, WOOD[1] if (x + y) % 5 else TAR[0])
    # back rim sticks (above the rim line, behind the hollow)
    for i in range(26):
        a = rnd.uniform(-1, 1)
        x0 = cx + a * 27
        y0 = ry_top - 1 + rnd.uniform(-2, 1.5)
        L = rnd.uniform(7, 16)
        ang = rnd.uniform(-0.25, 0.25)
        x1, y1 = x0 + L * math.cos(ang) * (1 if a < 0 else -1), y0 + L * math.sin(ang)
        cols = [DRIFT[5], DRIFT[3]] if rnd.random() < 0.6 else [WOOD[5], WOOD[3]]
        thick_line(s, x0, y0, x1, y1, cols, 2 if rnd.random() < 0.5 else 1)
    # the hollow
    for y in range(ry_top - 3, ry_top + 5):
        for x in range(cx - 24, cx + 25):
            e = ((x + 0.5 - cx) / 23) ** 2 + ((y + 0.5 - (ry_top + 1)) / 4) ** 2
            if e < 1:
                s.set(x, y, TAR[1] if e > 0.55 else TAR[0])
    # eggs (storm-crow: slate-blue, speckled)
    for (ex, ey) in ((27, 9), (31, 10)):
        for (dx, dy, c) in ((0, -1, SLATE[4]), (1, -1, SLATE[3]), (-1, 0, SLATE[4]), (0, 0, SLATE[4]),
                            (1, 0, SLATE[3]), (2, 0, SLATE[2]), (-1, 1, SLATE[3]), (0, 1, SLATE[3]),
                            (1, 1, SLATE[2]), (2, 1, SLATE[1]), (0, -2, SLATE[5])):
            s.set(ex + dx, ey + dy, c)
        s.set(ex + 1, ey, SLATE[1])
    # trinkets in the hollow: a silver chain, a coin, a gilt ring
    for i in range(7):
        s.set(36 + i, 10 + (1 if 1 < i < 5 else 0), SALT[1] if i % 2 else SALT[0])
    s.set(40, 9, SALT[2])
    s.set(41, 9, SALT[1])
    s.set(20, 11, AMBER[3])
    s.set(21, 11, AMBER[2])
    s.set(20, 10, AMBER[4])
    # front weave: straight sticks crossing at alternating slants, clipped to the bowl, lit on top
    for i in range(58):
        y0 = rnd.uniform(ry_top + 3, 30)
        x0 = cx + rnd.uniform(-1, 1) * bowl_hw(y0) * 0.9
        ang = (0.35 + rnd.uniform(0, 0.35)) * (1 if i % 2 else -1)
        L = rnd.uniform(8, 18)
        pal = DRIFT if rnd.random() < 0.6 else WOOD
        for k in range(int(L)):
            x = x0 + (k - L / 2) * math.cos(ang)
            y = y0 + (k - L / 2) * math.sin(ang)
            if y < ry_top + 2 or y > 31 or abs(x + 0.5 - cx) > bowl_hw(y):
                continue
            depth = (y - ry_top) / 20
            lit = 5.2 - depth * 2.4 - (0.9 if x > cx + 10 else 0)
            s.set(x, y, pal[int(clamp(lit, 1, len(pal) - 1))])
            s.set(x, y + 1, pal[int(clamp(lit - 2.6, 0, len(pal) - 1))])
    # a crown of sticks bristling out of the rim
    for i in range(16):
        side = -1 if i % 2 else 1
        u = 0.62 + 0.4 * rnd.random()                    # only toward the ends of the rim
        bx = cx + side * u * 25
        by = ry_top + 2 + rnd.uniform(-1, 3)
        L = rnd.uniform(3, 8)
        ang = rnd.uniform(0.2, 0.9)
        ex, ey = bx + side * math.cos(ang) * L, by - math.sin(ang) * L
        thick_line(s, bx, by, ex, ey, [DRIFT[5] if i % 3 else WOOD[5], DRIFT[2]], 1)
    # the rim: a band of lit sticks across the front lip
    for x in range(cx - 25, cx + 26):
        e = (x + 0.5 - cx) / 24
        y = ry_top + 1 + 4 * math.sqrt(max(0, 1 - e * e))
        c = DRIFT[6] if (x // 3) % 3 and x < cx + 10 else DRIFT[4]
        s.set(x, y, c)
        s.set(x, y + 1, DRIFT[3] if (x // 2) % 2 else WOOD[2])
    # sticks jutting out of the silhouette
    for (x0, y0, x1, y1) in ((6, 12, -1, 8), (9, 17, 1, 19), (57, 12, 63, 7), (55, 18, 63, 20), (14, 7, 10, 2),
                             (47, 8, 52, 2), (40, 7, 42, 1), (22, 27, 17, 31)):
        thick_line(s, x0, y0, x1, y1, [DRIFT[5], DRIFT[2]], 1)
    # bones: a rib sweeping out on the right, a gull skull on the left lip, a long bone across the front
    for i in range(14):
        a = i / 13
        s.set(46 + a * 12, 19 - math.sin(a * 2.4) * 7, BONE[2] if i < 9 else BONE[1])
        s.set(46 + a * 12, 20 - math.sin(a * 2.4) * 7, BONE[0])
    for (dx, dy, c) in ((0, 0, BONE[3]), (1, 0, BONE[3]), (2, 0, BONE[2]), (-1, 1, BONE[3]), (0, 1, BONE[2]),
                        (1, 1, K), (2, 1, BONE[2]), (3, 1, BONE[1]), (0, 2, BONE[2]), (1, 2, BONE[1]),
                        (2, 2, BONE[1]), (4, 2, BONE[2]), (5, 2, BONE[1]), (6, 3, BONE[1])):
        s.set(10 + dx, 10 + dy, c)
    thick_line(s, 18, 23, 35, 26, [BONE[2], BONE[0]], 2)
    s.set(17, 22, BONE[3])
    s.set(17, 24, BONE[2])
    s.set(36, 25, BONE[2])
    s.set(36, 27, BONE[1])
    # rope scraps trailing off the bottom and a side
    rope(s, [(24, 28), (22, 31)], (WHEAT[2], WHEAT[1]))
    rope(s, [(44, 26), (47, 28), (46, 31)], (WHEAT[3], WHEAT[2]))
    rope(s, [(8, 14), (5, 17), (6, 21)], (WHEAT[2], WHEAT[1]))
    # black feathers
    for (x, y, dx) in ((50, 9, 1), (13, 13, -1), (38, 21, 1)):
        for k in range(4):
            s.set(x + dx * k * 0.6, y - k, ST[3] if k < 3 else ST[5])
    s.outline()
    for (x, y, c) in ((20, 10, GLINT), (41, 9, GLINT), (37, 10, SALT[2]), (29, 8, SLATE[6]), (13, 10, BONE[4])):
        s.set(x, y, c)
    return Wd, Hd, ["Nest"], [{"ms": 1000, "cels": {"Nest": s.img}}], [("idle", 0, 0)]


# =========================================================================== iron balustrade on stone posts
def railing():
    Wd, Hd = 48, 16
    s = Spr(Wd, Hd)
    # stone kerb (runs the full width: tiles every 48 px)
    for x in range(48):
        s.set(x, 13, ST[8] if (x % 16) else ST[5])
        s.set(x, 14, ST[5] if (x % 16) else ST[2])
        s.set(x, 15, ST[3] if (x % 16) else ST[1])
    # the post (left)
    for y in range(2, 13):
        for x in range(1, 7):
            lv = 6.6 - (x - 1) * 0.7
            if y in (2, 3):
                lv += 1.5 - (y - 2)
            if y == 4:
                lv = 2.5                                     # under the cap
            if y == 12:
                lv -= 1.5
            s.set(x, y, ST[int(clamp(lv, 1, 10))])
    for x in range(0, 8):
        s.set(x, 1, ST[9] if x < 5 else ST[7])
        s.set(x, 2, ST[7] if x < 5 else ST[5])
        s.set(x, 3, ST[4])
    s.set(2, 8, ST[3])
    s.set(3, 9, ST[3])                                       # a crack
    # rails
    for x in range(7, 48):
        s.set(x, 4, IRON[5] if (x % 11) else IRON[6])
        s.set(x, 5, IRON[2])
        s.set(x, 11, IRON[4])
        s.set(x, 12, IRON[1])
    # plain square balusters, every fourth one with a collar; a rusted one here and there
    for i, x in enumerate(range(10, 48, 4)):
        for y in range(6, 11):
            s.set(x, y, IRON[4])
        if i % 2 == 0:
            s.set(x - 1, 8, IRON[3])
            s.set(x + 1, 8, IRON[2])
            s.set(x, 8, IRON[5])
        if h01(i, 0, 3) < 0.3:
            s.set(x, 9, RUST[3])
            s.set(x, 10, RUST[2])
    s.outline()
    for y in range(6, 11):                                   # open work between the rails: no outline fill
        for x in range(8, 48):
            if s.get(x, y) == K:
                s.set(x, y, T)
    s.set(1, 1, SHEEN[0])
    s.set(9, 4, SHEEN[1])
    return Wd, Hd, ["Railing"], [{"ms": 1000, "cels": {"Railing": s.img}}], [("idle", 0, 0)]


# =========================================================================== storm kites
KITES = [
    dict(ramp=OCHRE, spar=(BONE[2], BONE[0]),
         poly=[(24, 1), (35, 10), (24, 25), (13, 10)],
         spars=[((24, 1), (24, 25), 0), ((13, 10), (35, 10), -1.6)],
         patches=[([(15, 12), (22, 11), (22, 19)], CANVAS, 1), ([(26, 4), (31, 7), (28, 11), (25, 9)], OCHRE, -1.2)],
         tails=[((24, 25), 25, 0.0)], tow=(24, 25)),
    dict(ramp=FRED, spar=(DRIFT[5], DRIFT[2]),
         poly=[(24, 3), (26, 5), (30, 6), (36, 5), (42, 2), (46, 4), (44, 6), (42, 6), (41, 8), (38, 8), (37, 10),
               (34, 10), (32, 12), (28, 12), (28, 16), (31, 22), (26, 19), (24, 21), (22, 19), (17, 22), (20, 16),
               (20, 12), (16, 12), (14, 10), (11, 10), (10, 8), (7, 8), (6, 6), (4, 6), (2, 4), (6, 2), (12, 5),
               (18, 6), (22, 5)],
         spars=[((24, 3), (24, 20), 0), ((24, 5), (43, 3), 1.3), ((24, 5), (5, 3), 1.3)],
         patches=[([(9, 6), (15, 6), (16, 10), (11, 9)], GBLUE, 0.6), ([(26, 14), (28, 14), (28, 18), (26, 17)], CANVAS, 1)],
         tails=[((18, 22), 14, 0.8), ((30, 22), 18, 0.0)], tow=(24, 20), eye=True),
    dict(ramp=GBLUE, spar=(BONE[1], BONE[0]),
         poly=[(24, 2), (40, 20), (33, 19), (24, 23), (15, 19), (8, 20)],
         spars=[((24, 2), (24, 23), 0), ((24, 2), (9, 20), 0), ((24, 2), (39, 20), 0), ((13, 15), (35, 15), -1.0)],
         patches=[([(18, 12), (23, 10), (23, 17), (19, 17)], OCHRE, 0.8), ([(27, 15), (33, 16), (32, 18), (27, 18)], FRED, 0.6)],
         tails=[((24, 23), 25, 0.0), ((9, 20), 11, 1.5)], tow=(24, 23)),
]


def _kite_cel(v, f):
    D = KITES[v]
    R = D["ramp"]
    P = 2 * math.pi * f / 6
    ang = math.radians([0, 2.5, 4, 2, -1.5, -2.5][f])
    dy = [0, -1, -1, 0, 1, 0][f]
    ox, oy = 24.0, 13.0

    def tr(p):
        x, y = p[0] - ox, p[1] - oy
        return (ox + x * math.cos(ang) - y * math.sin(ang), oy + x * math.sin(ang) + y * math.cos(ang) + dy)

    s = Spr(48, 32)
    poly = [tr(p) for p in D["poly"]]
    spars = [(tr(a), tr(b), bow) for a, b, bow in D["spars"]]
    # tails (behind the sail): rag bows now (outlined with the sail), the thin cord after the outline
    cords = []
    for ti, (a, L, ph0) in enumerate(D["tails"]):
        ax, ay = tr(a)
        done = set()
        for i in range(int(L * 1.3)):
            sp = i / 1.3
            amp = 0.3 + sp * 0.09
            x = ax + sp * 0.97
            y = ay + 1 + sp * 0.12 + amp * math.sin(2 * math.pi * (sp / 10.0 - f / 6.0) + ph0)
            if x > 47.5 or y > 31:
                break
            cords.append((x, y, i))
            kb = int(sp) // 6
            if int(sp) % 6 == 4 and kb not in done:
                done.add(kb)
                rc = [R, CANVAS, R, GBLUE if R is not GBLUE else OCHRE][(kb + ti) % 4]
                flap = math.sin(2 * math.pi * (sp / 10.0 - f / 6.0) + ph0 + 1.2)
                for (ddx, ddy) in ((0, -1), (0, 0), (0, 1), (1, -1 - (flap > 0)), (1, 1 + (flap < 0)), (-1, -1), (-1, 1)):
                    s.set(x + ddx, y + ddy, rc[4] if ddy < 0 else rc[3] if ddy == 0 else rc[2])
    # the sail
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    top, bot = min(ys), max(ys)
    from spire_props import point_in_poly as pip

    def dseg(x, y, a, b):
        ax_, ay_ = a
        bx_, by_ = b
        vx, vy = bx_ - ax_, by_ - ay_
        t = clamp(((x - ax_) * vx + (y - ay_) * vy) / (vx * vx + vy * vy + 1e-9))
        return math.hypot(x - ax_ - vx * t, y - ay_ - vy * t)

    for y in range(int(top) - 1, int(bot) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            if not pip(x + 0.5, y + 0.5, poly):
                continue
            dsp = min(dseg(x + 0.5, y + 0.5, a, b) for a, b, _ in spars)
            billow = math.cos(dsp * 0.45 - P * 1.0 + 0.3 * x)
            lv = 3.4 + 0.7 * billow - (y - top) / (bot - top + 1) * 0.9 - (x - 24) * 0.025
            if dsp < 1.2:
                lv += 0.6
            c = R[int(clamp(lv, 1, 5))]
            for (pp, pr, off) in D["patches"]:
                if pip(x + 0.5, y + 0.5, [tr(q) for q in pp]):
                    c = pr[int(clamp(lv + off, 1, len(pr) - 1))]
                    break
            s.set(x, y, c)
    # stitching around the patches
    for (pp, pr, off) in D["patches"]:
        tp = [tr(q) for q in pp]
        for a, b in zip(tp, tp[1:] + tp[:1]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
            for i in range(0, n, 2):
                x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
                if s.get(round(x), round(y))[3]:
                    s.set(x, y, R[0] if pr is not R else R[1])
    if D.get("eye"):
        ex, ey = tr((24, 6))
        for (dx_, dy_, c) in ((-1, 0, BONE[2]), (0, 0, K), (1, 0, BONE[2]), (0, -1, BONE[1]), (0, 1, BONE[1])):
            s.set(ex + dx_, ey + dy_, c)
    # frayed trailing edge flutter (right-hand edges of the sail, per frame)
    for y in range(int(top), int(bot) + 1):
        for x in range(47, 0, -1):
            if s.get(x, y)[3]:
                if h01(x, y, 70 + f) < 0.28 and x > 26:
                    s.set(x + 1, y, R[2])
                break
    # spars (bone / driftwood), bowed
    for (a, b, bow) in spars:
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n + 1):
            t = i / n
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t + bow * math.sin(math.pi * t)
            s.set(x, y, D["spar"][0] if t < 0.5 else D["spar"][1])
    s.outline()
    for (x, y, i) in cords:
        if s.get(round(x), round(y))[3] == 0:
            s.set(x, y, WHEAT[2] if i % 3 else WHEAT[1])
    # bridle + the start of the kite line (drawn after the outline: thin)
    tx, ty = tr(D["tow"])
    mid = tr((24, 12))
    for (a, b) in ((mid, (26.5, 28)), ((tx, ty), (26.5, 28)), ((26.5, 28), (24, 31))):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
            if s.get(round(x), round(y))[3] == 0:
                s.set(x, y, WHEAT[1])
    s.set(24, 31, WHEAT[2])
    return s.img


def kite():
    frames, tags = [], []
    for v in range(3):
        for f in range(6):
            frames.append({"ms": 110, "cels": {"Kite": _kite_cel(v, f)}})
        tags.append((f"kite{v}", v * 6, v * 6 + 5))
    return 48, 32, ["Kite"], frames, tags
