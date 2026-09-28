"""Player: the dark knight, rigged for combat. 64x40 frames, faces RIGHT, feet on row 39.

Helmet, torso and pauldron are the hand-drawn v2 knight parts; legs, arm, sword and cape
are posed per frame. Every part is its own Aseprite layer.
"""
import math, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asebuild

W, H = 64, 40
OX, OY = 14, 8          # v2 32x32 knight coords -> frame coords

PAL = {
    'K': (8, 7, 12), '1': (20, 19, 30), '2': (33, 32, 48), '3': (52, 53, 74),
    '4': (84, 90, 118), '5': (150, 162, 196),
    'k': (10, 3, 7), 'm': (28, 8, 16), 'n': (52, 12, 26), 'o': (82, 18, 36), 'p': (118, 30, 46),
    'B': (38, 42, 58), 'S': (110, 120, 150), 's': (205, 214, 236),
    'g': (74, 50, 22), 'G': (170, 128, 52), 'l': (40, 26, 20),
    'r': (240, 36, 50), 'y': (255, 170, 140),
    'f': (255, 196, 90), 'F': (200, 120, 40),   # flask glow
    # sorcery glow (cast): white core -> gold ramp
    'W': (255, 248, 230), 'A': (255, 210, 120), 'a': (240, 170, 60), 'b': (170, 110, 40),
}

# ------------------------------------------------------------------ hand-drawn parts (v2 coords)
HELMET = {
    1: [(2, "K")],
    2: [(1, "K5K")],
    3: [(1, "K43KK"), (11, "KKKKKK")],
    4: [(2, "K4322KK"), (10, "K233445K")],
    5: [(4, "KK2211K"), (9, "K12233455K")],
    6: [(7, "KK"), (9, "K122334455K")],
    7: [(9, "K1122KrrryK")],
    8: [(9, "K11223KKKKK")],
    9: [(9, "K1122334K")],
    10: [(10, "K112233K")],
}
PAULDRON = {
    7: [(6, "K")],
    8: [(6, "K5K")],
    9: [(6, "K45K")],
    10: [(5, "KK3455KK")],
    11: [(4, "K12334455K")],
    12: [(4, "K112233445K")],
    13: [(4, "K11223344K")],
    14: [(5, "KK112233K")],
    15: [(7, "KKKK")],
}

def ramp_spans(edges, ramp="1122334"):
    rows = {}
    for y, (a, b) in edges.items():
        n = b - a - 1
        s = "K" + "".join(ramp[min(len(ramp) - 1, i * len(ramp) // max(n, 1))] for i in range(n)) + "K"
        rows[y] = [(a, s)]
    return rows

TORSO = ramp_spans({11: (12, 17), 12: (11, 18), 13: (11, 19), 14: (10, 19), 15: (9, 19),
                    16: (9, 18), 17: (9, 18), 18: (9, 17)})
TORSO[13].append((16, "45"))
TORSO[14].append((16, "455"))
TORSO[19] = [(9, "K11lGl111K")]
TORSO[20] = [(9, "K1223K2234K")]
TORSO[21] = [(9, "K1223K12334K")]
TORSO[22] = [(9, "KKKKK.KKKKK")]

# ------------------------------------------------------------------ grid helpers
def blank():
    return [[None] * W for _ in range(H)]

def stamp(g, rows, dx, dy):
    for y, segs in rows.items():
        for x, s in segs:
            for i, ch in enumerate(s):
                X, Y = x + i + dx, y + dy
                if ch != '.' and 0 <= X < W and 0 <= Y < H:
                    g[Y][X] = ch

def put(g, x, y, ch):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = ch

def outline(g, ch='K'):
    add = []
    for y in range(H):
        for x in range(W):
            if g[y][x] is None and any(0 <= x + a < W and 0 <= y + b < H and g[y + b][x + a] not in (None,)
                                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                add.append((x, y))
    for x, y in add:
        g[y][x] = ch
    return g

def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy or 1e-9
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    cx, cy = ax + t * vx, ay + t * vy
    # signed side: >0 = upper-left side of the segment (lit)
    nx, ny = vy, -vx
    if nx + ny > 0:
        nx, ny = -nx, -ny
    side = (px - cx) * nx + (py - cy) * ny
    return math.hypot(px - cx, py - cy), side

def limb(g, pts, width, lit, mid, dark):
    r = width / 2.0
    for y in range(H):
        for x in range(W):
            best = None
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                d, side = seg_dist(x, y, ax, ay, bx, by)
                if best is None or d < best[0]:
                    best = (d, side)
            if best and best[0] <= r:
                g[y][x] = lit if best[1] > 0.6 else (dark if best[1] < -0.6 else mid)

def ik(a, b, l1, l2, bend=1):
    """two-bone IK; returns joint point. bend=+1 knee forward (right), -1 back."""
    (ax, ay), (bx, by) = a, b
    d = min(math.hypot(bx - ax, by - ay), l1 + l2 - 0.01)
    base = math.atan2(by - ay, bx - ax)
    cosA = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = base - bend * math.acos(max(-1, min(1, cosA)))
    return ax + l1 * math.cos(ang), ay + l1 * math.sin(ang)

# ------------------------------------------------------------------ procedural parts
def draw_leg(hip, foot, front, bend=1):
    g = blank()
    knee = ik(hip, foot, 5.2, 5.2, bend)
    ramp = ('4', '3', '2') if front else ('3', '2', '1')
    limb(g, [hip, knee], 4.2, *ramp)
    limb(g, [knee, (foot[0], foot[1] - 1)], 3.4, *ramp)
    fx, fy = int(round(foot[0])), int(round(foot[1]))
    for x in range(fx - 1, fx + 3):
        put(g, x, fy - 1, ramp[1])
        put(g, x, fy, ramp[2])
    put(g, knee[0] + 0.5, knee[1], '5' if front else '4')     # knee cop glint
    return outline(g)

def draw_arm(shoulder, hand):
    g = blank()
    elbow = ik(shoulder, hand, 5.0, 5.0, bend=-1)
    limb(g, [shoulder, elbow, hand], 3.4, '4', '3', '2')
    hx, hy = int(round(hand[0])), int(round(hand[1]))
    for a, b in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)):
        put(g, hx + a, hy + b, '3')
    put(g, hx, hy - 1, '5')
    return outline(g)

def draw_sword(hand, ang_deg, length=18, planted=False):
    g = blank()
    a = math.radians(ang_deg)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx               # perpendicular
    hx, hy = hand
    # blade
    for i in range(2, length * 2):
        t = i / 2.0
        cx, cy = hx + dx * (t + 1), hy + dy * (t + 1)
        taper = t > length - 2.5
        put(g, cx, cy, 's' if taper else 'S')
        if not taper:
            ex, ey = cx + px * 0.9, cy + py * 0.9
            if 0 <= int(round(ex)) < W and 0 <= int(round(ey)) < H and g[int(round(ey))][int(round(ex))] is None:
                put(g, ex, ey, 's' if (py < 0 or (abs(py) < 0.3 and px < 0)) else 'B')
    # crossguard
    gx, gy = hx + dx * 1.6, hy + dy * 1.6
    for s in (-3, -2, -1, 0, 1, 2, 3):
        put(g, gx + px * s, gy + py * s, 'G' if abs(s) < 3 else 'g')
    # grip + pommel behind the hand
    put(g, hx - dx * 1.5, hy - dy * 1.5, 'l')
    put(g, hx - dx * 2.6, hy - dy * 2.6, 'G')
    outline(g)
    if planted:  # sink tip into floor: clip below ground
        for y in range(H):
            for x in range(W):
                if y > 39:
                    g[y][x] = None
    return g

# ------------------------------------------------------------------ weapons (overlay sheets wpn_<id>)
# Every weapon is authored in blade space: u = distance along the weapon from the grip point
# (the hand), v = offset across it (+v = the perpendicular (-dy, dx) draw_sword uses), and
# vl = v signed so that vl > 0 is the side facing the upper-left light. Colours are RGB tuples
# (to_img accepts both palette chars and tuples).
WPN_IDS = ["longsword", "dagger", "greatsword", "spear", "katana", "maul", "oathbrand", "kalden",
           "gravetusk", "omen", "rotmaw", "scepter"]   # v6: boss remembrance weapons appended

def _band(vl, hw, lit, mid, dark, k=0.35):
    return lit if vl > hw * k else (dark if vl < -hw * k else mid)

def _taper(u, end, full, n):
    """half-width: `full` until `n` px before `end`, then narrowing to a point."""
    return full if u < end - n else full * max(0.0, (end - u) / n) + 0.22

# ---- per-weapon shapes: f(u, v, vl, L) -> colour | None.  Blade tip sits at u = L + 1.5.
def shp_dagger(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    c = 0.5 - 0.02 * max(0.0, u - 2) ** 2           # curves back toward the spine
    if 1.8 <= u <= tip:
        hw = _taper(u, tip, 0.8, 4.0)
        if abs(v - c) <= hw:
            return _band((v - c) * s, hw, (214, 222, 240), (126, 136, 166), (46, 50, 70), 0.2)
    if 0.8 <= u < 1.8 and abs(v - 0.5) <= 1.75:        # small iron guard
        return (84, 90, 118) if vl > 0 else (40, 40, 56)
    if -3.0 <= u < 0.8 and abs(v - 0.5) <= 0.75:        # bone grip
        return (222, 212, 180) if vl > 0 else (170, 154, 120)
    if -4.2 <= u < -3.0 and abs(v - 0.5) <= 1.25:       # bone knob
        return (236, 228, 204) if vl > 0 else (170, 154, 120)
    return None

RUST = {4, 9, 10, 15, 19, 22}
def shp_greatsword(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    if 2.6 <= u <= tip:
        hw = min(1.45, 0.45 + (tip - u) * 0.55)          # blunt slab tip
        if abs(v) <= hw:
            iu = int(math.floor(u))
            if abs(v) < 0.5 and 4 <= u <= min(13, L - 4) and iu % 3 != 2:   # rune inscription by the hilt
                return (246, 192, 88) if iu % 3 == 0 else (150, 98, 36)
            col = _band(vl, 1.45, (170, 172, 182), (96, 98, 110), (50, 48, 60), 0.4)
            if iu in RUST and vl <= 0.4:                  # rust bloom on the shadowed edge
                col = (134, 76, 44) if vl > -0.6 else (92, 50, 34)
            return col
    if 0.8 <= u < 2.6 and abs(v) <= 4.4:                 # broad iron crossguard
        if abs(v) < 0.9:
            return (246, 192, 88)
        return (150, 150, 160) if u < 1.7 else (62, 58, 70)
    if -5.0 <= u < 0.8 and abs(v) <= 0.75:              # long two-hand grip
        return (84, 56, 38) if int(math.floor(u)) % 2 else (46, 30, 22)
    if -6.8 <= u < -5.0 and abs(v) <= 1.35:             # heavy pommel
        return (150, 150, 160) if vl > 0 else (62, 58, 70)
    return None

SPEAR_BACK = 8.0
def shp_spear(u, v, s, L, back=SPEAR_BACK):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 7.5                                      # leaf blade: 7.5 px long
    if h0 <= u <= tip:
        t = (u - h0) / 7.5
        hw = 1.75 * math.sin(math.pi * min(1.0, t * 1.25) ** 0.85) if t < 0.8 else 1.75 * (1 - t) / 0.2 * 0.75 + 0.2
        hw = max(0.3, hw)
        if abs(v) <= hw:
            if abs(v) < 0.45 and t < 0.75:
                return (150, 162, 196)                   # mid-rib
            return _band(vl, hw, (214, 222, 240), (126, 136, 166), (52, 53, 74), 0.1)
    if h0 - 1.6 <= u < h0 and abs(v) <= 0.9:            # bronze socket
        return (200, 150, 70) if vl > 0 else (120, 84, 34)
    if -back <= u < h0 - 1.6 and abs(v) <= 0.55:        # ash-wood shaft
        if int(math.floor(u)) in (-3, 4) :
            return (200, 150, 70)                        # grip bindings
        return (132, 96, 58) if vl >= 0 else (96, 66, 40)
    if -back - 1.4 <= u < -back and abs(v) <= 0.8:      # iron butt-cap
        return (84, 90, 118)
    return None

def shp_katana(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    c = 0.5 - 0.0062 * max(0.0, u - 2) ** 2              # gentle koshizori curve toward the spine
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 0.8, 3.0)
        if abs(v - c) <= hw:
            # convex side (+v) is the edge: moonlit; spine side dark steel
            if v - c > 0.05:
                return (208, 232, 255) if u > 3 else (160, 186, 222)
            return (92, 104, 140)
    if 1.0 <= u < 2.0 and abs(v - 0.5) <= 1.6:          # round tsuba
        return (170, 128, 52) if vl > 0 else (74, 50, 22)
    if -5.0 <= u < 1.0 and abs(v - 0.5) <= 0.75:        # ito-wrapped grip (diamond pattern)
        return (178, 170, 200) if (int(math.floor(u)) + (v > 0.5)) % 2 else (36, 34, 60)
    if -6.0 <= u < -5.0 and abs(v - 0.5) <= 0.8:        # kashira cap
        return (170, 128, 52)
    return None

def shp_maul(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 6.0                                       # sledge head: 6 along the haft x 10 across
    if h0 <= u <= tip and abs(v) <= 4.6:
        if abs(v) > 3.9 and (u < h0 + 0.8 or u > tip - 0.8):
            return None                                  # bevelled corners
        mid = (h0 + tip) / 2
        if abs(u - mid) < 0.5 and abs(v) < 3.9:          # molten seam across the head
            return (255, 222, 130) if abs(v) < 1.2 else (240, 120, 36)
        if abs(v) < 0.5 and abs(u - mid) < 1.6:          # short cracks off the seam
            return (200, 84, 30)
        if abs(v) > 3.9:                                 # banded iron end-caps
            return (138, 132, 144) if vl > 0 else (56, 50, 60)
        if u > tip - 0.9:
            return (48, 42, 52)                          # striking face in shadow
        return (104, 98, 112) if vl > 0 else (70, 64, 78)
    if -2.8 <= u < h0 and abs(v - 0.5) <= 0.75:         # stout 2px haft
        if u > h0 - 2.0:
            return (84, 90, 118)                         # iron langet under the head
        wood = (126, 90, 56) if (v - 0.5) * s > 0 else (86, 58, 36)
        return wood if int(math.floor(u)) % 6 else (52, 36, 26)
    if -4.0 <= u < -2.8 and abs(v - 0.5) <= 1.25:
        return (84, 90, 118)
    return None

def shp_oathbrand(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    if 2.2 <= u <= tip:
        hw = _taper(u, tip, 1.3, 3.5)
        if abs(v) <= hw:
            if abs(v) < 0.45 and u < tip - 2:
                return (255, 206, 104)                   # glowing fuller line
            return _band(vl, hw, (255, 250, 236), (232, 222, 196), (196, 166, 104), 0.2)
    if 1.0 <= u < 2.2 and abs(v) <= 3.2:                 # gold cross
        return (255, 196, 90) if u < 1.6 else (170, 128, 52)
    if 2.2 <= u < 3.6 and 2.4 <= abs(v) <= 3.4:          # upswept quillon tips
        return (255, 196, 90) if vl > 0 else (170, 128, 52)
    if -3.4 <= u < 1.0 and abs(v) <= 0.75:               # white-gold grip
        return (236, 226, 204) if int(math.floor(u)) % 2 else (170, 128, 52)
    if -4.8 <= u < -3.4 and abs(v) <= 1.25:              # sun pommel
        return (255, 248, 230) if abs(v) < 0.5 else (255, 196, 90)
    return None

def shp_kalden(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    if 2.4 <= u <= tip:
        hw = _taper(u, tip, 1.3, 3.5)
        if abs(v) <= hw:
            iu = int(math.floor(u))
            if abs(v) < 0.5 and 4 <= u <= L - 2 and iu % 3 != 2:      # teal-gold filigree
                return (86, 206, 190) if iu % 6 < 3 else (222, 180, 86)
            return _band(vl, hw, (112, 122, 146), (36, 38, 52), (22, 22, 32), 0.3)
    if 1.0 <= u < 2.4 and abs(v) <= 4.0:                  # guard: gold with teal ends
        if abs(v) > 3.0:
            return (86, 206, 190)
        return (222, 180, 86) if u < 1.7 else (130, 96, 40)
    if -4.6 <= u < 1.0 and abs(v) <= 0.75:               # blue-wrapped grip
        return (58, 92, 150) if int(math.floor(u)) % 2 else (30, 46, 84)
    if -6.0 <= u < -4.6 and abs(v) <= 1.2:               # teal pommel stone
        return (86, 206, 190) if vl > 0 else (40, 120, 116)
    return None

# ---- boss remembrance weapons (v6)
ROOTGOLD = ((255, 236, 160), (240, 186, 72), (150, 96, 36))      # glowing Pale-Root: core, body, deep
def shp_gravetusk(u, v, s, L):
    """Rootbound Hound: a curved ash-bone tusk bound in glowing golden roots."""
    tip = L + 1.5
    c = 0.4 - 0.0075 * max(0.0, u - 2.0) ** 2            # the tusk sweeps back toward -v
    dv = v - c
    vl = dv * s
    if 2.4 <= u <= tip:
        n = 7.0
        hw = 1.65 if u < tip - n else 1.65 * max(0.0, (tip - u) / n) ** 0.65 + 0.15
        ph = (u + 2.4 * dv) % 6.0                        # root helix winding round the tusk
        root = ph < 1.1 and u < tip - 5.5
        if abs(dv) <= hw:
            if root:
                return ROOTGOLD[0] if (vl > -0.3 and ph < 0.7) else ROOTGOLD[1]
            if u > tip - 5.5 and abs(dv) < 0.5 and vl > -0.2:
                return (244, 240, 228)                   # polished point
            iu = int(math.floor(u))
            col = _band(vl, hw, (214, 208, 194), (152, 146, 140), (92, 86, 88), 0.3)
            if iu % 5 == 1 and vl < 0.4:                 # growth rings of the tusk
                col = (118, 112, 110) if vl > -0.5 else (68, 62, 66)
            return col
        if root and abs(dv) <= hw + 1.0 and 3.0 <= u <= L - 6 and int(u) % 2:  # root knots spill off the edge
            return ROOTGOLD[2] if vl < 0 else ROOTGOLD[1]
    if 0.6 <= u < 2.4 and abs(v) <= 2.7:                  # knotted root guard, a seed of light in it
        if abs(v) < 0.9 and 1.0 <= u < 2.1:
            return ROOTGOLD[0]
        if abs(v) > 2.0 and u < 1.2:
            return None
        return (126, 92, 54) if vl > 0 else (70, 48, 32)
    if 2.4 <= u < 4.0 and 1.9 <= abs(v) <= 2.8 and abs(v) - 1.9 < (4.0 - u) * 0.8:   # tendrils hooked up the tusk
        return ROOTGOLD[1] if vl > 0 else ROOTGOLD[2]
    if -5.2 <= u < 0.6 and abs(v) <= 0.75:               # root-wrapped grip
        k = (int(math.floor(u)) + (1 if v > 0 else 0)) % 2
        if int(math.floor(u)) % 3 == 0 and k:
            return ROOTGOLD[1]
        return (116, 84, 50) if k else (60, 42, 28)
    if -6.6 <= u < -5.2 and abs(v) <= 1.3:               # bone knob with a gold seed
        if abs(v) < 0.5:
            return ROOTGOLD[0]
        return (214, 208, 194) if vl > 0 else (120, 114, 112)
    return None

def shp_omen(u, v, s, L):
    """Morvain's sword: curved black steel, serrated gold edge breathing embers, gilt swept guard."""
    tip = L + 1.5
    c = 0.5 - 0.0085 * max(0.0, u - 2.0) ** 2            # curves toward the spine (-v); +v = cutting edge
    dv = v - c
    vl = dv * s
    if 2.2 <= u <= tip:
        hw = _taper(u, tip, 1.55, 4.5)
        iu = int(math.floor(u))
        tooth = 4.0 <= u <= tip - 3.0 and iu % 3 == 0     # serrations along the edge
        hi = hw + (0.8 if tooth else 0.0)
        if -hw <= dv <= hi:
            de = hi - dv
            if de < 0.95:                                # gold cutting edge, the teeth white-hot
                return (255, 238, 170) if tooth else ((255, 214, 104) if u > tip - 3.5 else (223, 170, 64))
            if de < 1.9 and (tooth or iu % 3 == 1) and 3.0 < u < tip - 3.0:
                return (255, 138, 31)                    # ember glow seeping in behind the teeth
            if dv < -hw + 0.8:                           # spine: black steel, a thin gilt line near the guard
                if u < 7.0:
                    return (178, 130, 42)
                return (122, 102, 92) if vl > 0 else (36, 28, 37)
            return (72, 58, 58) if vl > 0 else (30, 23, 31)   # black steel
    if 0.8 <= u < 2.2 and abs(v) <= 3.3:                  # swept gold wings with an ember gem
        if abs(v) < 0.9 and u >= 1.1:
            return (255, 193, 74)
        return (223, 178, 74) if u < 1.5 else (125, 85, 25)
    if 2.2 <= u < 3.9 and 2.3 <= abs(v) <= 3.3 and abs(v) - 2.3 < (3.9 - u):
        return (223, 178, 74) if vl > 0 else (125, 85, 25)
    if -4.4 <= u < 0.8 and abs(v) <= 0.75:               # oxblood leather grip
        return (110, 34, 38) if (int(math.floor(u)) + (1 if v > 0 else 0)) % 2 else (46, 18, 26)
    if -5.8 <= u < -4.4 and abs(v) <= 1.25:              # gold pommel, ember eye
        return (255, 138, 31) if abs(v) < 0.5 else ((223, 178, 74) if vl > 0 else (125, 85, 25))
    return None

ROT_SLIME = (118, 166, 54)                               # drips run screen-down off these (see _raster)
def shp_rotmaw(u, v, s, L):
    """Vessel of Rot: a crude cleaver of rusted iron fused to bone, pustules aglow, weeping green."""
    tip = L + 1.5
    vl = v * s
    h0 = tip - 11.0                                      # the broad slab head
    if h0 <= u <= tip:
        du = u - h0
        e = min(4.6, 1.2 + du * 1.4)                      # edge flares out on +v
        if u > tip - 1.8:
            e = min(e, 4.6 - (u - (tip - 1.8)) * 1.5)     # leading corner hacked off
        iu = int(math.floor(u))
        if iu in (int(h0) + 5, int(h0) + 8) and du > 2:
            e -= 1.0                                     # chipped edge
        sp = -1.5
        if sp - 1.0 <= v < sp and iu % 3 != 2 and 0.5 < du < 10.0:
            return (214, 204, 172) if vl > 0 else (150, 136, 108)   # vertebra ridge along the spine
        if sp <= v <= e:
            for pu, pv, r in ((3.6, 1.2, 1.2), (7.4, 2.4, 0.95)):
                dd = math.hypot(du - pu, v - pv)
                if dd <= r:
                    return (255, 214, 120) if dd < r - 0.8 else (244, 124, 36)   # glowing pustule
                if dd <= r + 0.65:
                    return (120, 46, 30)
            if e - v < 0.9:                              # crude edge, weeping rot
                return ROT_SLIME if iu % 4 == 1 else ((176, 168, 160) if vl > 0 else (112, 104, 100))
            if v < sp + 0.9:
                return (132, 124, 132) if vl > 0 else (58, 52, 62)
            if (iu * 5 + int(math.floor(v * 1.5)) * 3) % 7 < 3:
                return (130, 76, 46) if vl > 0 else (88, 48, 32)      # rust bloom
            return (96, 90, 102) if vl > 0 else (66, 60, 72)          # pitted iron
    if 1.8 <= u < h0 and -1.2 <= v <= 0.6:               # thick fused-bone neck
        if int(math.floor(u)) % 4 == 0:
            return (116, 70, 46)                         # rusted iron band
        return (214, 204, 172) if vl > 0 else (150, 136, 108)
    if 0.8 <= u < 1.8 and abs(v) <= 1.5:                 # rusted collar
        return (160, 104, 64) if vl > 0 else (70, 42, 34)
    if -4.0 <= u < 0.8 and abs(v) <= 0.75:               # femur haft bound in rotting rag
        if int(math.floor(u)) % 3 == 0:
            return (78, 90, 44)
        return (200, 190, 158) if vl > 0 else (140, 126, 100)
    if -5.4 <= u < -4.0 and abs(v) <= 1.35:              # bone knuckle
        return (214, 204, 172) if vl > 0 else (150, 136, 108)
    return None

def shp_scepter(u, v, s, L, back=SPEAR_BACK):
    """Pale Sovereign: a pale branching rootspear, luminous gold leaf-blade, a small halo ring."""
    tip = L + 1.5
    vl = v * s
    BL = 8.0
    h0 = tip - BL
    if h0 <= u <= tip:                                   # luminous leaf-blade
        t = (u - h0) / BL
        hw = 1.9 * math.sin(math.pi * min(1.0, t * 1.3) ** 0.8) if t < 0.75 else 1.9 * (1 - t) / 0.25 * 0.7 + 0.2
        hw = max(0.35, hw)
        if abs(v) <= hw:
            if abs(v) < 0.45 and t < 0.8:
                return (255, 252, 236)
            return _band(vl, hw, (255, 236, 170), (240, 196, 96), (178, 128, 48), 0.15)
    uc = h0 - 4.6                                        # halo ring round the shaft below the head
    q = ((u - uc) / 1.7) ** 2 + (v / 3.4) ** 2
    if 0.42 <= q <= 1.12 and abs(v) > 0.8:
        return (255, 244, 196) if (vl > 0 and u < uc) else (236, 184, 78)
    if h0 - 1.6 <= u < h0 + 2.0:                         # root prongs cradling the blade
        w = 0.7 + (u - (h0 - 1.6)) * 0.55
        if abs(abs(v) - w) <= 0.55 and abs(v) > 0.6:
            return (238, 232, 214) if vl > 0 else (170, 160, 136)
    if -back <= u < h0 and abs(v) <= 0.55:               # pale root shaft
        iu = int(math.floor(u))
        if iu in (-3, 4):
            return (240, 190, 90)                        # gold bindings
        return (236, 228, 206) if vl >= 0 else (168, 156, 130)
    for ku, side in ((-5.5, 1), (1.5, -1)):              # gnarled knots / twig nubs
        if ku <= u < ku + 1.2 and 0.55 < v * side <= 1.4:
            return (212, 202, 176) if vl > 0 else (150, 138, 112)
    if -back - 1.8 <= u < -back:                          # root foot splaying into two tendrils
        w = 0.35 + (-back - u) * 0.75
        if abs(abs(v) - w) <= 0.5:
            return (206, 196, 170) if vl > 0 else (140, 128, 104)
    return None

# id -> (shape, nominal length, reach behind the hand, extent across, planted style)
WPN = {
    "dagger":     (shp_dagger, 10, 4.5, 2.5, "blade"),
    "greatsword": (shp_greatsword, 25, 7.0, 4.5, "blade"),
    "spear":      (shp_spear, 19, SPEAR_BACK + 1.5, 2.0, "blade"),
    "katana":     (shp_katana, 20, 6.2, 2.5, "blade"),
    "maul":       (shp_maul, 20, 4.2, 4.8, "maul"),
    "oathbrand":  (shp_oathbrand, 19, 5.0, 3.5, "blade"),
    "kalden":     (shp_kalden, 22, 6.2, 4.1, "blade"),
    "gravetusk":  (shp_gravetusk, 24, 7.0, 5.5, "blade"),
    "omen":       (shp_omen, 20, 6.0, 4.0, "blade"),
    "rotmaw":     (shp_rotmaw, 22, 5.8, 5.0, "blade"),
    "scepter":    (shp_scepter, 22, SPEAR_BACK + 2.0, 3.5, "blade"),
}
LONGHAFT = {"spear": shp_spear, "scepter": shp_scepter}   # shaft behind the hand shortens as they shrink

FIST = ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1))   # draw_arm's gauntlet pixels

def _raster(kind, hand, ang, L, back_scale=1.0):
    shape, _, back, across, _ = WPN[kind]
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    lit = 1 if (-0.5 * px - py) > 0 else -1              # +p faces the light?
    hx, hy = hand
    R = L + back + across + 3
    pix = {}
    for y in range(int(hy - R), int(hy + R) + 1):
        for x in range(int(hx - R), int(hx + R) + 1):
            u = (x - hx) * dx + (y - hy) * dy
            v = (x - hx) * px + (y - hy) * py
            if kind in LONGHAFT:
                c = LONGHAFT[kind](u, v, lit, L, SPEAR_BACK * back_scale)
            elif kind in STAFF_BACK:
                c = shape(u, v, lit, L, STAFF_BACK[kind] * back_scale)
            else:
                c = shape(u, v, lit, L)
            if c is not None:
                pix[(x, y)] = c
    if kind == "rotmaw":   # green rot weeps off the edge, straight down whatever the swing
        for (x, y), c in list(pix.items()):
            if c == ROT_SLIME:
                n = (x * 7 + y * 3) % 4
                for k in range(1, min(n, 3) + 1):
                    if (x, y + k) in pix:
                        break
                    pix[(x, y + k)] = (194, 226, 112) if k == min(n, 3) else ROT_SLIME
    if kind in RASTER_POST:   # screen-space extras (a hanging lantern, dangling beads...)
        RASTER_POST[kind](pix, (hx, hy), (dx, dy), L)
    for (x, y) in [(x + a2, y + b2) for (x, y) in pix for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1))]:
        if (x, y) not in pix:
            pix[(x, y)] = 'K'
    return pix

def draw_weapon(kind, hand, ang, length=18, planted=False, held=True, fit_bottom=False, info=None):
    """Weapon `kind` gripped at `hand`, pointing along `ang` (degrees, 0 = right, +90 = down).
    `length` is the pose's sword length (18 nominal): other weapons scale with it, then shrink
    further (never below ~half) until they fit the frame. Planted weapons point down into the
    floor (row 39); the maul instead rests its head on the floor."""
    if kind == "longsword":
        if info is not None:
            info.update(hand=hand, ang=ang, tip=length + 0.5, L=length)
        return draw_sword(hand, ang, length, planted)
    _, L0, _, _, style = WPN[kind]
    L = L0 * length / 18.0
    hx, hy = hand
    if planted:
        ang = 90
        if style == "maul":
            L = 37.8 - hy                                # head's last row sits on the floor
        elif held:
            L = max(L, 39.5 - hy)                        # tip reaches the floor
        else:
            hy = max(hy, 40.0 - L)                       # standing on its own: sink the tip
    must_fit_bottom = (fit_bottom or style == "maul") and not planted
    floor = H + (2 if style == "maul" and not fit_bottom else 0)   # a grounded maul may bury 2px
    Lmin = L * (0.3 if style == "maul" else 0.45)
    while True:
        s = max(0.0, (L - Lmin) / max(1e-6, L0 - Lmin)) if (kind in LONGHAFT or kind in STAFF_BACK) else 1.0
        pix = _raster(kind, (hx, hy), ang, L, back_scale=min(1.0, 0.55 + 0.45 * s))
        xs = [x for x, _ in pix]
        ys = [y for _, y in pix]
        inside = min(xs) >= 0 and max(xs) < W and min(ys) >= 0 and (max(ys) < floor or not must_fit_bottom)
        if inside or planted or L <= Lmin:
            break
        L -= 0.5
    if info is not None:
        info.update(hand=(hx, hy), ang=ang, tip=L + 1.5, L=L)
    g = blank()
    for (x, y), c in pix.items():
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c
    if held:   # the gauntlet closes over the grip: leave the fist pixels to the Arm layer
        fx, fy = int(round(hand[0])), int(round(hand[1]))
        for a2, b2 in FIST:
            if 0 <= fx + a2 < W and 0 <= fy + b2 < H:
                g[fy + b2][fx + a2] = None
    return g

class Wpn:
    """Deferred weapon cel: rendered once per weapon id."""
    def __init__(self, hand, ang, slen=18, planted=False, held=True, fitb=False):
        self.hand, self.ang, self.slen = hand, ang, slen
        self.planted, self.held, self.fitb = planted, held, fitb

    # moveset extras (all optional; unset = the plain weapon cel exactly as before)
    fx = ()            # smear / impact effects drawn under the weapon (see move_fx)
    clear = ()         # pixels to leave to the body (the off hand closing over a two-handed grip)
    mirror = False     # spin frame: the whole cel is mirrored about the anchor (x -> 56 - x)
    mask = None        # body alpha: weapon + fx hidden where the body is (weapon swung behind it)
    sheath = False     # iaido stance: blade drawn as a scabbard
    aura = 0           # weapon arts: halo of 1..3 px around the weapon (weapon's smear tones)
    aura_pal = None
    heat = None        # weapon arts: (u0, u1) blade span recoloured red-hot (cinder)
    fx_pal = None      # weapon arts: FX tones overriding the weapon's smear tones
    clear_fx = False   # weapon arts: `clear` also punches the FX (the off hand stays on top)

    shield = None      # v8 shield class: ((cx, cy), rot, sx) -- default: on the off hand / carried low
    offw = None        # v8 twin class: ((hx, hy), ang, slen, front) -- the off-hand blade
    offfx = ()         # v8: smear FX of the off-hand blade
    bxy = (0, 0)       # v8: body offset of the pose (defaults for the extras)
    offp = None        # v8: off hand position (absolute), if the pose draws the far arm
    cels = None        # v8: the frame's cels (body masks for the extras)

    lash = None        # v9 whip class: the lash's control points (absolute), None = hanging at rest
    lash_prev = None   # v9: previous frame's lash (motion smear)

    def render(self, kind, dust=True, extras=True):
        if kind in WHIP_KINDS:
            return render_whip(self, kind, dust)
        if extras and kind in EXTRA_KINDS:
            return render_extras(self, kind, dust)
        return self.render_core(kind, dust)

    def render_core(self, kind, dust=True):
        if not (self.fx or self.clear or self.mirror or self.sheath or self.mask is not None or self.aura or self.heat
                or self.clear_fx):
            return to_img(draw_weapon(kind, self.hand, self.ang, self.slen, self.planted, self.held, self.fitb))
        info = {}
        g = draw_weapon(kind, self.hand, self.ang, self.slen, self.planted, self.held, self.fitb, info=info)
        for x, y in self.clear:
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = None
        if self.sheath:   # blade housed in a black-lacquer scabbard with a gold chape
            a = math.radians(info["ang"])
            ddx, ddy = math.cos(a), math.sin(a)
            hx0, hy0 = info["hand"]
            for y in range(H):
                for x in range(W):
                    if g[y][x] is None:
                        continue
                    u = (x - hx0) * ddx + (y - hy0) * ddy
                    v = -(x - hx0) * ddy + (y - hy0) * ddx
                    if u > 2.4:
                        if g[y][x] == 'K':
                            continue
                        lit = (v * (1 if (0.5 * ddy - ddx) > 0 else -1)) > 0
                        if u > info["tip"] - 2.5:
                            g[y][x] = (200, 150, 70) if lit else (120, 84, 34)
                        else:
                            g[y][x] = (74, 48, 70) if lit else (38, 24, 40)
        if self.heat:
            heat_blade(g, info, self.heat)
        fxg = move_fx(kind, info, self.fx, dust, self.fx_pal)
        if self.aura:
            halo(fxg, g, self.aura, self.aura_pal or SMEAR[kind], info)
        if self.clear_fx:
            for x, y in self.clear:
                if 0 <= x < W and 0 <= y < H:
                    fxg[y][x] = None
        img = to_img(fxg)
        img.alpha_composite(to_img(g))
        self.info = info
        if self.mirror:
            m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            m.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT).crop((7, 0, W, H)), (0, 0))
            img = m
        if self.mask is not None:
            px, mk = img.load(), self.mask.load()
            for y in range(H):
                for x in range(W):
                    if mk[x, y][3]:
                        px[x, y] = (0, 0, 0, 0)
        return img

def heat_blade(g, info, span):
    """Recolour the blade between u0..u1 (px from the grip) along an ember ramp by brightness."""
    a = math.radians(info["ang"])
    ddx, ddy = math.cos(a), math.sin(a)
    hx0, hy0 = info["hand"]
    u0, u1 = span
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c is None or c == 'K':
                continue
            u = (x - hx0) * ddx + (y - hy0) * ddy
            if not (max(2.4, u0) < u <= u1):
                continue
            rgb = PAL[c] if isinstance(c, str) else c
            lum = 0.3 * rgb[0] + 0.55 * rgb[1] + 0.15 * rgb[2]
            hot = u > u1 - 2.5          # the hottest band right under the sliding hand
            g[y][x] = EMBER[0] if lum > 190 or (hot and lum > 110) else (
                EMBER[1] if lum > 110 or hot else (EMBER[2] if lum > 55 else EMBER[3]))

def halo(fxg, g, r, tones, info):
    """Glow ring around the weapon's blade (not the grip / fists), under it into fxg (empty cells only)."""
    c0, c1, c2 = tones
    a = math.radians(info["ang"])
    ddx, ddy = math.cos(a), math.sin(a)
    hx0, hy0 = info["hand"]
    solid = [(x, y) for y in range(H) for x in range(W)
             if g[y][x] is not None and (x - hx0) * ddx + (y - hy0) * ddy > 3.5]
    dist = {}
    for x, y in solid:
        for b in range(-r, r + 1):
            for a2 in range(-r, r + 1):
                X, Y = x + a2, y + b
                if 0 <= X < W and 0 <= Y < H and g[Y][X] is None:
                    dd = max(abs(a2), abs(b)) if abs(a2) + abs(b) <= r + 0.5 else r + 1
                    if dd <= r and dd < dist.get((X, Y), 99):
                        dist[(X, Y)] = dd
    for (X, Y), dd in dist.items():
        if fxg[Y][X] is not None:
            continue
        if dd == 1:
            fxg[Y][X] = c1
        elif dd == 2:
            fxg[Y][X] = c2 if (X + Y) % 2 == 0 or r == 2 else None
        elif (X + Y) % 2 == 0:
            fxg[Y][X] = c2

class RotWpn:
    """Weapon cel of a rotated (death fall) frame: same rotate/crop/offset as the body."""
    def __init__(self, inner, ang, box, off):
        self.inner, self.ang, self.box, self.off = inner, ang, box, off

    def render(self, kind, dust=True, extras=True):
        r = self.inner.render(kind, dust, extras).rotate(self.ang, resample=Image.NEAREST, expand=True).crop(self.box)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(r, self.off)
        return canvas

def draw_cape(shoulder_y, back_x, flow, bob, length=17, flutter=0):
    """Cape hangs from the back of the shoulders; flow>0 streams it backwards (left)."""
    g = blank()
    inside = set()
    top = shoulder_y
    tatters = [0, 2, 1, 3, 0, 2, 3, 1]
    for i in range(length):
        y = top + i
        spread = 2 + i * (0.35 + 0.25 * flow)
        left = back_x - spread - flow * i * 0.45
        right = back_x + 4 - flow * i * 0.15
        for x in range(int(math.floor(left)), int(math.ceil(right)) + 1):
            hem = length - tatters[(x + flutter) % len(tatters)] * (1 + (flow > 1))
            if i <= hem:
                inside.add((x, y))
    for (x, y) in inside:
        if not (0 <= x < W and 0 <= y < H):
            continue
        band = (x - (y - top) // 3) % 8
        ch = "mmnnoonn"[band]
        if y - top < 2:
            ch = 'm'
        if band == 5 and (y - top) % 5 == 2:
            ch = 'p'
        g[y][x] = ch
    return outline(g, 'k')

def draw_helmet(dx, dy):
    g = blank()
    stamp(g, HELMET, dx, dy)
    return g

def draw_torso(dx, dy):
    g = blank()
    stamp(g, TORSO, dx, dy)
    return g

def draw_pauldron(dx, dy):
    g = blank()
    stamp(g, PAULDRON, dx, dy)
    return g

def draw_offarm(shoulder, hand, ramp=('4', '3', '2'), palm=False):
    g = blank()
    elbow = ik(shoulder, hand, 5.0, 5.0, bend=-1)
    limb(g, [shoulder, elbow, hand], 3.2, *ramp)
    hx, hy = int(round(hand[0])), int(round(hand[1]))
    for a, b in ((0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (1, -1)):
        put(g, hx + a, hy + b, '3')
    put(g, hx + 1, hy - 1, '5')
    if palm:   # splayed gauntlet pressed flat against the wall
        for b in range(-2, 3):
            put(g, hx + 2, hy + b, '4' if b < 0 else '3')
        put(g, hx + 1, hy - 2, '4')
    return outline(g)

def draw_glow(hand, level):
    """Golden sorcery gathering in the off hand. level 1 (spark) .. 3 (full flare)."""
    g = blank()
    cx, cy = hand[0] + 1.5, hand[1] + 0.5
    R = [0, 2.2, 3.4, 4.6][level]
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= R * 0.35:
                g[y][x] = 'W'
            elif d <= R * 0.62:
                g[y][x] = 'A'
            elif d <= R * 0.85:
                g[y][x] = 'a'
            elif d <= R and (x + y) % 2 == 0:
                g[y][x] = 'b'
    if level >= 2:   # 4-point flare
        L = 3 + 2 * level
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(int(R), L):
                put(g, cx - 0.5 + dx * i, cy - 0.5 + dy * i, 'A' if i < L - 2 else 'a')
    return g

def draw_flask(hand):
    g = blank()
    hx, hy = int(round(hand[0])), int(round(hand[1]))
    for (a, b, c) in ((1, -2, 'f'), (2, -2, 'F'), (1, -3, 'f'), (2, -3, 'f'), (1, -4, 'G')):
        put(g, hx + a, hy + b, c)
    return outline(g)

# ------------------------------------------------------------------ pose -> layer cels
LAYERS = ["Cape", "BackLeg", "OffArm", "Torso", "FrontLeg", "Pauldron", "Head", "Arm", "Sword", "Item"]

def pose(p):
    """p: dict with body dx/dy, leg feet, hand, sword angle, cape flow."""
    bx, by = p.get("dx", 0), p.get("dy", 0)
    hx = p.get("head_dx", 0) + bx
    hy = p.get("head_dy", 0) + by
    hipB = (OX + 11 + bx, OY + 21 + by)
    hipF = (OX + 15 + bx, OY + 21 + by)
    shoulder = (OX + 13 + bx, OY + 14 + by)
    cels = {
        "Cape": draw_cape(OY + 10 + by, OX + 8 + bx, p.get("flow", 0.3), by, flutter=p.get("flutter", 0)),
        "BackLeg": draw_leg(hipB, p.get("footB", (OX + 9, 39)), False, p.get("bendB", 1)),
        "Torso": draw_torso(OX + bx, OY + by),
        "FrontLeg": draw_leg(hipF, p.get("footF", (OX + 17, 39)), True, p.get("bendF", 1)),
        "Pauldron": draw_pauldron(OX + bx, OY + by),
        "Head": draw_helmet(OX + hx, OY + hy),
    }
    if "hand" in p:
        hand = (p["hand"][0] + bx, p["hand"][1] + by)
        cels["Arm"] = draw_arm(shoulder, hand)
        if p.get("sword", True):
            cels["Sword"] = Wpn(hand, p["ang"], p.get("slen", 18), fitb=p.get("air", False))
    if "off" in p:          # far (off-hand) arm, drawn behind the torso
        off = (p["off"][0] + bx, p["off"][1] + by)
        if p.get("off_front"):   # palm flat on a wall ahead (wall cling): drawn over the body
            cels["Item"] = draw_offarm((OX + 12 + bx, OY + 14 + by), off, ramp=('4', '3', '2'), palm=True)
        else:
            cels["OffArm"] = draw_offarm((OX + 11 + bx, OY + 14 + by), off)
        if p.get("glow"):
            cels["Item"] = draw_glow(off, p["glow"])
    if "planted" in p:   # held when the hand rests on the hilt (rest/rise), free-standing in heal
        held = "hand" in p and abs(p["hand"][0] + bx - p["planted"][0]) < 3 and abs(p["hand"][1] + by - p["planted"][1]) < 4
        cels["Sword"] = Wpn(p["planted"], 90, planted=True, held=held)
    if p.get("flask"):
        cels["Item"] = draw_flask((p["hand"][0] + bx, p["hand"][1] + by))
    w = cels.get("Sword")
    if isinstance(w, Wpn):   # v8: what the class extras (shield / off-hand blade) need
        w.bxy, w.cels = (bx, by), cels
        if "off" in p and not p.get("off_front"):
            w.offp = (p["off"][0] + bx, p["off"][1] + by)
    return cels

def to_img(g):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c:
                px[x, y] = (PAL[c] if isinstance(c, str) else c) + (255,)
    return img

def compose(cels):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for name in LAYERS:
        if name in cels:
            img.alpha_composite(cels[name] if isinstance(cels[name], Image.Image) else to_img(cels[name]))
    return img

def imgs(cels, kind="longsword"):
    """Render a frame's cels; the deferred weapon cel is drawn as weapon `kind` (None = omit)."""
    out = {}
    for k, v in cels.items():
        if isinstance(v, (Wpn, RotWpn)):
            if kind:
                out[k] = v.render(kind)
        else:
            out[k] = v if isinstance(v, Image.Image) else to_img(v)
    return out

# ------------------------------------------------------------------ animations
FB, FF = (OX + 8, 39), (OX + 19, 39)

def seq(frames, base=None):
    """frames: list of (pose-dict, ms); base dict merged under each."""
    base = base or {}
    return [(pose({**dict(footB=FB, footF=FF), **base, **p}), ms) for p, ms in frames]

def idle():
    bob = [0, 0, 1, 1, 1, 0]
    return seq([(dict(dy=b, hand=(35, 27 + b), ang=-50 + 3 * b, flow=0.2 + 0.08 * i % 3, flutter=i // 2), 150)
                for i, b in enumerate(bob)])

def run():
    out = []
    for i in range(8):
        t = i / 8 * 2 * math.pi
        # contact at i=0/4 (low), passing at 2/6 (high)
        dy = [1, 0, -1, 0, 1, 0, -1, 0][i]
        fF = (OX + 14 + 7 * math.cos(t), 39 - max(0, math.sin(t)) * 4)
        fB = (OX + 14 + 7 * math.cos(t + math.pi), 39 - max(0, math.sin(t + math.pi)) * 4)
        swing = math.sin(t) * 1.5
        out.append((pose(dict(dx=1, dy=dy, head_dx=1, footF=fF, footB=fB,
                              hand=(31 + swing, 29), ang=160 - swing * 6,
                              flow=1.1 + 0.25 * math.sin(t * 2), flutter=i)), 80))
    return out

def jump_up():
    return seq([(dict(dy=-1, hand=(34, 25), ang=-70, footB=(OX + 9, 36), footF=(OX + 18, 37), flow=0.9, flutter=0), 90),
                (dict(dy=-1, hand=(34, 24), ang=-75, footB=(OX + 10, 35), footF=(OX + 18, 35), flow=1.1, flutter=1), 90)],
               dict(air=True))

def jump_fall():
    return seq([(dict(hand=(35, 24), ang=-60, footB=(OX + 8, 37), footF=(OX + 19, 38), flow=0.4, flutter=2), 90),
                (dict(hand=(35, 25), ang=-55, footB=(OX + 8, 38), footF=(OX + 19, 39), flow=0.3, flutter=3), 90)],
               dict(air=True))

def land():
    return seq([(dict(dy=3, head_dy=0, hand=(36, 31), ang=-20, footB=(OX + 6, 39), footF=(OX + 21, 39), flow=0.6), 70),
                (dict(dy=1, hand=(35, 28), ang=-40, flow=0.3), 80)])

def roll_ball(theta, cx=31.5, cy=31.0):
    """Tucked knight drawn procedurally at rotation theta (degrees, clockwise)."""
    g = blank()
    R = 7.4
    th = math.radians(theta)
    def rot(a_deg, r):
        a = math.radians(a_deg) + th
        return cx + r * math.cos(a), cy + r * math.sin(a)
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d > R:
                continue
            a = (math.degrees(math.atan2(y - cy, x - cx)) - theta) % 360
            if 170 <= a < 350:           # armoured back, curled outward
                band = int((a - 170) // 30)
                ch = "2334432"[band % 7] if d > 4.5 else ('2' if d > 2.5 else '1')
                if d > 6.4 and a < 260:
                    ch = '4'
            else:                        # cape wrapped over knees
                ch = "mnnom"[int(a // 36) % 5] if d > 2.5 else 'm'
            g[y][x] = ch
    # helmet: visor + red eye near the leading edge, horn swept back
    hx, hy = rot(335, 4.4)
    for dx, dy, c in ((0, 0, '3'), (1, 0, '4'), (0, 1, '2'), (1, 1, '2'), (-1, 0, '2'), (0, -1, '4'), (1, -1, '5')):
        put(g, hx + dx, hy + dy, c)
    put(g, *rot(345, 6.2), 'r'); put(g, *rot(352, 5.4), 'r')
    put(g, *rot(265, 8.3), '5'); put(g, *rot(262, 9.2), '4')
    # boots
    for a in (120, 138):
        put(g, *rot(a, 6.0), '3'); put(g, *rot(a, 5.0), '2')
    return outline(g)

def roll():
    out = seq([(dict(dy=3, head_dy=1, hand=(36, 33), ang=10, footB=(OX + 7, 39), footF=(OX + 19, 39), flow=1.2), 45)])
    for k in range(6):
        out.append(({"Cape": roll_ball(k * 60 + 30)}, 45))
    out += seq([(dict(dy=3, hand=(36, 32), ang=-10, footB=(OX + 6, 39), footF=(OX + 20, 39), flow=1.0), 55),
                (dict(dy=1, hand=(35, 29), ang=-35, flow=0.6), 60)])
    return out

def attack1():  # diagonal downward cut
    return mseq([(dict(dx=-1, hand=(29, 17), ang=-125, footB=(OX + 7, 39), flow=0.3), 50),
                 (dict(dx=1, hand=(32, 18), ang=-80, flow=0.5, flutter=1), 40),
                 (dict(dx=2, hand=(37, 22), ang=-10, footF=(FF[0] + 1, 39), flow=0.8, flutter=2, fx=[sw(w=0.45)]), 40),
                 (dict(dx=2, hand=(37, 28), ang=40, footF=(FF[0] + 1, 39), flow=0.8, flutter=3, fx=[sw(w=0.4)]), 60),
                 (dict(dx=2, dy=1, hand=(35, 31), ang=70, footF=(FF[0] + 1, 39), flow=0.5, flutter=4), 70),
                 (dict(dx=1, hand=(35, 29), ang=10, flow=0.3), 90)])

def attack2():  # rising reverse cut
    return mseq([(dict(dx=1, dy=1, hand=(32, 32), ang=125, footB=(OX + 7, 39), flow=0.4), 50),
                 (dict(dx=1, dy=1, hand=(35, 32), ang=60, flow=0.5, flutter=1, fx=[sw(w=0.3)]), 40),
                 (dict(dx=2, hand=(38, 27), ang=-10, footF=(FF[0] + 1, 39), flow=0.8, flutter=2, fx=[sw(w=0.45)]), 40),
                 (dict(dx=2, dy=-1, hand=(36, 20), ang=-70, footB=(OX + 9, 38), footF=(FF[0] + 1, 39), flow=0.9, flutter=3, fx=[sw(w=0.4)]), 60),
                 (dict(dx=1, hand=(34, 18), ang=-100, flow=0.5, flutter=4), 70),
                 (dict(dx=1, hand=(35, 25), ang=-60, flow=0.3), 90)])

def attack3():  # lunging thrust finisher
    return mseq([(dict(dx=-1, hand=(29, 26), ang=-5, footB=(OX + 6, 39), flow=0.3), 90),
                (dict(dx=-2, dy=1, head_dx=-1, hand=(27, 27), ang=0, footB=(OX + 5, 39), flow=0.2, fx=[("glint", "tip")]), 70),
                (dict(dx=3, dy=1, hand=(41, 27), ang=0, footB=(OX + 9, 39), footF=(OX + 24, 39), flow=1.3, flutter=2, fx=[("streak", 18)]), 50),
                (dict(dx=3, dy=1, hand=(42, 27), ang=2, footB=(OX + 9, 39), footF=(OX + 24, 39), flow=1.1, flutter=3, fx=[("streak", 8)]), 80),
                (dict(dx=2, hand=(38, 27), ang=-10, footF=(OX + 22, 39), flow=0.7), 100),
                (dict(dx=1, hand=(36, 27), ang=-35, flow=0.4), 120),
                (dict(hand=(35, 27), ang=-48, flow=0.3), 110)])

def heavy():
    return mseq([(dict(hand=(29, 17), ang=-100, flow=0.3), 110),
                (dict(dx=-1, hand=(27, 12), ang=-145, footB=(OX + 7, 39), flow=0.3), 130),
                (dict(dx=-1, dy=1, head_dx=-1, hand=(27, 11), ang=-162, footB=(OX + 6, 39), flow=0.2, flutter=1, fx=[("glint", "tip")]), 220),
                (dict(dx=1, hand=(34, 15), ang=-60, flow=0.6, flutter=2, fx=[sw(w=0.35)]), 50),
                (dict(dx=2, dy=1, hand=(38, 25), ang=20, footF=(FF[0] + 2, 39), flow=1.0, flutter=3, fx=[sw(w=0.5)]), 50),
                (dict(dx=2, dy=2, head_dy=1, hand=(37, 31), ang=58, footF=(FF[0] + 2, 39), flow=0.8, flutter=4, fx=[sw(w=0.4), ("dust", 47, 3)]), 110),
                (dict(dx=2, dy=1, hand=(36, 30), ang=50, footF=(FF[0] + 2, 39), flow=0.5), 150),
                (dict(dx=1, hand=(35, 27), ang=-25, flow=0.3), 160)])

def hurt():
    return seq([(dict(dx=-2, head_dx=-1, head_dy=1, hand=(31, 30), ang=40, flow=0.1), 60),
                (dict(dx=-2, dy=1, head_dx=-1, head_dy=1, hand=(31, 31), ang=50, flow=0.1), 100),
                (dict(dx=-1, dy=1, hand=(33, 29), ang=10, flow=0.2), 140)])

def heal():
    rows = [((33, 26), False, 0, 120), ((33, 22), True, 0, 120), ((32, 18), True, 1, 150),
            ((32, 16), True, 1, 300), ((32, 18), True, 1, 150), ((33, 24), False, 0, 150)]
    return seq([(dict(dy=dy, hand=h, sword=False, flask=f, planted=(40, 22), flow=0.2), ms) for h, f, dy, ms in rows])

def death():
    out = seq([(dict(dx=-2, head_dx=-1, head_dy=1, hand=(31, 31), ang=50, flow=0.1), 120),
               (dict(dx=-1, dy=2, head_dy=1, hand=(32, 33), ang=70, flow=0.0), 150),
               (dict(dy=5, head_dy=1, hand=(33, 35), ang=85, footB=(OX + 7, 39), footF=(OX + 20, 39), flow=0.0), 200)])
    kneel_p = dict(dy=7, head_dy=2, hand=(34, 37), ang=88, footB=(OX + 6, 39), footF=(OX + 21, 39), flow=0.0)
    kneel = pose({**dict(footB=FB, footF=FF), **kneel_p})
    out.append((kneel, 350))
    comp = compose(imgs(kneel))                   # body + longsword: fixes crop box and offset
    body = compose(imgs(kneel, None))
    for ang, ms in ((-25, 110), (-55, 110), (-80, 120), (-90, 900)):
        r = comp.rotate(ang, resample=Image.NEAREST, expand=True)
        box = r.getbbox()
        r = r.crop(box)
        off = (max(0, min(W - r.width, 22)), H - r.height)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(body.rotate(ang, resample=Image.NEAREST, expand=True).crop(box), off)
        out.append(({"Torso": canvas, "Sword": RotWpn(kneel["Sword"], ang, box, off)}, ms))
    return out

# ------------------------------------------------------------------ v3 moveset additions
AIR = dict(footB=(OX + 9, 36), footF=(OX + 18, 37), air=True)   # airborne legs (as jump_up)
TUCK = dict(footB=(OX + 9, 33), footF=(OX + 18, 33), air=True)  # knees pulled up
# (air=True: long weapons must also fit above the frame bottom -- there is no floor to bite)

def attack_up():  # rising overhead cut: low-front -> straight up -> trailing back
    return mseq([(dict(dy=2, hand=(33, 32), ang=45, footB=(OX + 7, 39), footF=(OX + 20, 39), flow=0.3), 70),
                 (dict(dy=1, hand=(36, 26), ang=-35, flow=0.5, fx=[sw(w=0.22)]), 40),
                 (dict(dy=-1, hand=(36, 16), ang=-68, slen=15, footB=(OX + 9, 38), flow=0.9, flutter=1, fx=[sw(w=0.4)]), 40),
                 (dict(dy=-1, hand=(35, 12), ang=-100, slen=14, footB=(OX + 9, 38), flow=0.8, flutter=2, fx=[sw(w=0.35)]), 60),
                 (dict(hand=(29, 15), ang=-135, slen=16, flow=0.5, flutter=3), 80),
                 (dict(hand=(34, 25), ang=-60, flow=0.3), 100)])

def attack_down():  # airborne plunge: sword reversed, tip below the feet
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-5, head_dy=0, hand=(31, 19), ang=90, slen=12, flow=0.9, flutter=0,
                     footB=(OX + 9, 34), footF=(OX + 17, 34)), 60),
               (dict(hand=(33, 27), ang=90, slen=14, flow=1.3, flutter=1, fx=[("streak", 10)] + DIVE(9)), 50),
               (dict(dy=-3, hand=(33, 27), ang=90, slen=14, flow=1.5, flutter=3, fx=DIVE(7, 1)), 50),
               (dict(hand=(33, 27), ang=89, slen=14, flow=1.3, flutter=5), 60),
               (dict(dy=-3, head_dy=0, hand=(34, 24), ang=20, flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [1, 2, 3])

def air_attack():  # horizontal cut in the air, legs tucked (active 2-3, as the engine)
    base = dict(dy=-3, **TUCK)
    return mseq([(dict(head_dx=-1, hand=(28, 19), ang=-150, flow=0.4), 45),
                 (dict(hand=(33, 19), ang=-65, flow=0.7, flutter=1), 25),
                 (dict(dx=1, hand=(40, 25), ang=-2, flow=1.1, flutter=2, fx=[sw(w=0.45)]), 50),
                 (dict(dx=1, hand=(38, 29), ang=38, flow=1.0, flutter=3, fx=[sw(w=0.4)]), 70),
                 (dict(hand=(35, 26), ang=-20, flow=0.6, flutter=4, **AIR), 120)], base)   # 310 ms in all, as before

def cast():  # off hand thrusts forward, gold sorcery flares at the palm (bolt spawns on frame 4)
    sw = dict(hand=(31, 31), ang=150)
    return seq([(dict(off=(29, 26), flow=0.2), 80),
                (dict(dx=-1, off=(25, 24), glow=1, flow=0.2), 90),
                (dict(dx=-1, dy=1, off=(24, 22), glow=2, flow=0.3, flutter=1), 110),
                (dict(dx=1, off=(36, 21), glow=2, footF=(FF[0] + 1, 39), flow=0.6, flutter=2), 50),
                (dict(dx=1, off=(38, 21), glow=3, footF=(FF[0] + 1, 39), flow=0.8, flutter=3), 70),
                (dict(dx=1, off=(37, 22), glow=1, footF=(FF[0] + 1, 39), flow=0.5, flutter=3), 90),
                (dict(off=(33, 25), flow=0.3), 100),
                (dict(off=(28, 27), hand=(34, 28), ang=-20, flow=0.2), 110)], sw)

def parry():  # quick flick of the blade upright across the body; frames 1-2 deflect
    return seq([(dict(dx=-1, hand=(32, 27), ang=-20, flow=0.2), 40),
                (dict(dx=-1, dy=1, head_dx=-1, hand=(36, 21), ang=-100, slen=17, flow=0.5), 60),
                (dict(dx=-1, dy=1, head_dx=-1, hand=(36, 22), ang=-92, slen=17, flow=0.4, flutter=1), 90),
                (dict(dx=-1, hand=(35, 24), ang=-70, flow=0.3), 80),
                (dict(hand=(35, 26), ang=-55, flow=0.2), 80),
                (dict(hand=(35, 27), ang=-50, flow=0.2), 90)])

def riposte():  # coil, lunging impale, twist, rip free
    return mseq([(dict(dx=-2, dy=1, hand=(27, 25), ang=-8, footB=(OX + 5, 39), flow=0.3), 90),
                (dict(dx=-3, dy=2, head_dx=-1, hand=(25, 26), ang=-4, footB=(OX + 4, 39), flow=0.2), 160),
                (dict(dx=3, dy=1, hand=(41, 26), ang=0, slen=17, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.4, flutter=2, fx=[("streak", 16)]), 40),
                (dict(dx=4, dy=2, hand=(42, 27), ang=3, slen=13, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.2, flutter=3), 90),
                (dict(dx=4, dy=3, head_dy=1, hand=(41, 29), ang=-12, slen=11, footB=(OX + 9, 39), footF=(OX + 26, 39), flow=0.9, flutter=4), 140),
                (dict(dx=3, dy=1, hand=(41, 21), ang=-35, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.0, flutter=5), 60),
                (dict(dx=2, hand=(38, 24), ang=-45, footF=(OX + 22, 39), flow=0.6), 110),
                (dict(dx=1, hand=(35, 27), ang=-48, flow=0.3), 130)])

def wall_slide():  # facing the wall on the right (x~35-36), off hand braced on it, sliding down
    out = []
    for i, dy in enumerate((0, 1)):
        out.append((pose(dict(dy=1 + dy, off=(35, 18 - dy), off_front=True, hand=(30, 31 - dy), ang=165, slen=16,
                              footB=(OX + 15, 39), footF=(OX + 20, 34 + dy),
                              flow=0.05, flutter=i * 3)), 110))
    return out

def cape_swirl(theta, cx, cy):
    """Crimson crescent of cape whipping around the tucked body (behind it)."""
    g = blank()
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            a = (math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx)) - theta) % 360
            # trail sweeps 150 deg behind the leading edge, thickest near the body
            if a > 150:
                continue
            q = a / 150.0
            r0, r1 = 6.5, 7.0 + 4.2 * (1 - q) ** 0.7
            if r0 <= d <= r1:
                g[y][x] = 'p' if d > r1 - 1.2 and q < 0.35 else ('o' if q < 0.5 else ('n' if q < 0.8 else 'm'))
    return outline(g, 'k')

def double_jump():  # tuck -> forward flip with the cape whirling -> open out
    out = seq([(dict(dy=-2, head_dy=1, hand=(35, 27), ang=30, slen=16, flow=1.3, flutter=1, **TUCK), 50)])
    for th in (100, 260):
        cy = 25.0
        out.append(({"Cape": cape_swirl(th + 180, 31.5, cy), "Torso": roll_ball(th, cy=cy)}, 55))
    out += seq([(dict(dy=-2, hand=(36, 25), ang=-40, flow=1.2, flutter=2, footB=(OX + 9, 35), footF=(OX + 18, 36)), 80)])
    return out

KNEEL = dict(dy=5, footB=(OX + 3, 39), footF=(OX + 20, 39), bendB=-1)

def rest():  # plant the sword and kneel (engine holds the last frame)
    return seq([(dict(dy=1, hand=(36, 27), ang=60, flow=0.2), 110),
                (dict(dy=3, hand=(37, 21), sword=False, planted=(37, 26), footB=(OX + 5, 39), footF=(OX + 20, 39), flow=0.1), 130),
                (dict(head_dy=1, hand=(37, 20), sword=False, planted=(37, 27), flow=0.0, **KNEEL), 160),
                (dict(head_dy=2, head_dx=1, hand=(37, 20), sword=False, planted=(37, 27), flow=0.0, **KNEEL), 600)])

def rise():  # reverse: lift the head, push up on the hilt, pull the blade free
    return seq([(dict(head_dy=0, hand=(37, 20), sword=False, planted=(37, 27), flow=0.0, **KNEEL), 140),
                (dict(dy=3, hand=(37, 20), sword=False, planted=(37, 25), footB=(OX + 5, 39), footF=(OX + 20, 39), flow=0.1), 120),
                (dict(dy=1, hand=(36, 25), ang=-70, flow=0.3), 100),
                (dict(hand=(35, 27), ang=-50, flow=0.2), 110)])

# ------------------------------------------------------------------ v4: per-class movesets
# Each weapon class gets its own attack tags (appended after the 125 v3 frames). The body is
# posed with the same helpers; the weapon overlay additionally carries the smear / impact FX of
# the swing (drawn under the blade, tinted per weapon), so body + any wpn_* still line up.
SMEAR = {   # weapon -> (rim, body, tail) smear tones
    "longsword":  ((240, 244, 255), (168, 180, 214), (90, 98, 130)),
    "dagger":     ((232, 238, 252), (156, 166, 198), (84, 90, 118)),
    "greatsword": ((255, 244, 222), (206, 184, 150), (116, 98, 80)),
    "spear":      ((238, 242, 252), (168, 178, 208), (92, 98, 128)),
    "katana":     ((226, 246, 255), (124, 186, 244), (54, 92, 166)),
    "maul":       ((255, 232, 140), (242, 132, 42), (150, 62, 26)),
    "oathbrand":  ((255, 252, 226), (255, 204, 100), (182, 122, 42)),
    "kalden":     ((206, 255, 244), (86, 206, 190), (38, 108, 110)),
    "gravetusk":  ((255, 244, 200), (236, 196, 104), (132, 112, 88)),
    "omen":       ((255, 244, 196), (255, 160, 48), (150, 52, 26)),
    "rotmaw":     ((255, 206, 120), (214, 116, 44), (80, 108, 40)),
    "scepter":    ((255, 252, 236), (255, 226, 150), (196, 156, 84)),
}
DUST = ((150, 138, 124), (104, 94, 86), (66, 60, 58))

def _unwrap(a, ref):
    while a - ref > 180:
        a -= 360
    while ref - a > 180:
        a += 360
    return a

def move_fx(kind, info, fx, dust=True, pal=None):
    """Rasterise a frame's swing FX for weapon `kind` into a grid (under the weapon).
    info: the weapon's final geometry (hand, ang, tip distance) from draw_weapon.
      ("arc", pivot, a0, a1, opt)  crescent swept by the tip: from angle a0 (trailing, degrees
                                   around pivot, in y-squashed space) to the blade tip (leading);
                                   a1 only picks the winding. opt: sq (y squash), rk (trailing
                                   radius factor), w (band depth as a fraction of the reach)
      ("streak", n)                thrust speed-lines trailing the tip, n px long
      ("flash", y, x0, x1)         iaido flash: a razor line across the frame
      ("dust", x, size)            floor impact debris at x
      ("glint", (x, y))            4-point glint (tension cue)
    """
    g = blank()
    c0, c1, c2 = pal or SMEAR[kind]
    hx, hy = info["hand"]
    a = math.radians(info["ang"])
    dx, dy = math.cos(a), math.sin(a)
    tx, ty = hx + dx * info["tip"], hy + dy * info["tip"]
    for f in fx:
        k = f[0]
        if k == "arc":
            (px, py), a0, a1 = f[1], f[2], f[3]
            opt = f[4] if len(f) > 4 else {}
            sq, rk, wf = opt.get("sq", 1.0), opt.get("rk", 1.0), opt.get("w", 0.55)
            rL = math.hypot(tx - px, (ty - py) / sq)
            aL = _unwrap(math.degrees(math.atan2((ty - py) / sq, tx - px)), a1)
            r0 = rL * rk
            depth = max(2.5, min(rL - 2.0, wf * info["tip"]))
            lo, hi = min(a0, aL), max(a0, aL)
            for y in range(H):
                for x in range(W):
                    ex, ey = x - px, (y - py) / sq
                    rho = math.hypot(ex, ey)
                    if rho < 1:
                        continue
                    th = _unwrap(math.degrees(math.atan2(ey, ex)), (lo + hi) / 2)
                    if not lo <= th <= hi:
                        continue
                    t = (th - a0) / (aL - a0) if aL != a0 else 1.0
                    rt = r0 + (rL - r0) * t
                    wt = depth * (0.2 + 0.8 * t ** 0.7)
                    d = rt - rho
                    if not -0.6 <= d <= wt:
                        continue
                    wv = wt
                    if t < 0.28:                        # dissolving tail
                        if (x + y) % 2 == 0:
                            g[y][x] = c2 if d > 1.0 else c1
                    elif d < 1.2:
                        g[y][x] = c0
                    elif d < wv * 0.5:
                        g[y][x] = c1
                    elif d < wv * 0.8 or (x + y) % 2 == 0:
                        g[y][x] = c2
        elif k == "sweep":
            # the band the blade's outer part swept since the previous frame (hand + angle lerp)
            (h0x, h0y), a0 = f[1], f[2]
            opt = f[3] if len(f) > 3 else {}
            wf = opt.get("w", 0.5)
            a1 = info["ang"]
            tip0 = info["tip"]
            if len(f) > 4 and f[4]:            # previous keyframe's (fitted) reach for this weapon
                pinfo = {}
                draw_weapon(kind, *f[4], info=pinfo)
                tip0 = pinfo["tip"]
            span = abs(a1 - a0) + math.hypot(hx - h0x, hy - h0y) * 3
            n = max(8, int(span * 1.5))
            best = {}
            tipL = info["tip"]
            depth = max(2.5, wf * tipL)
            for sidx in range(n + 1):
                t = sidx / n
                cx0, cy0 = h0x + (hx - h0x) * t, h0y + (hy - h0y) * t
                aa = math.radians(a0 + (a1 - a0) * t)
                ddx, ddy = math.cos(aa), math.sin(aa)
                Lt = tip0 + (tipL - tip0) * t
                for lim, comp, base in ((W - 2, ddx, cx0), (1, ddx, cx0), (39, ddy, cy0), (1, ddy, cy0)):
                    if comp > 1e-6 and lim > base:
                        Lt = min(Lt, (lim - base) / comp)
                    elif comp < -1e-6 and lim < base:
                        Lt = min(Lt, (lim - base) / comp)
                u = Lt
                while u >= max(2.0, Lt - depth):
                    X, Y = int(round(cx0 + ddx * u)), int(round(cy0 + ddy * u))
                    if 0 <= X < W and 0 <= Y < H:
                        d = Lt - u
                        o = best.get((X, Y))
                        if o is None or t > o[0] + 0.02 or (abs(t - o[0]) <= 0.02 and d < o[1]):
                            best[(X, Y)] = (t, d)
                    u -= 0.5
            for (X, Y), (t, d) in best.items():
                if t > 0.97:
                    continue
                if t < 0.3:
                    if (X + Y) % 2 == 0:
                        g[Y][X] = c1 if d < 1.5 else c2
                elif d < 1.5:
                    g[Y][X] = c0
                elif d < depth * 0.38:
                    g[Y][X] = c1
                elif d < depth * 0.66 or (X + Y) % 2 == 0:
                    g[Y][X] = c2
        elif k == "streak":
            n = f[1]
            ppx, ppy = -dy, dx
            for v, start, frac in ((0, 3, 1.0), (-2, 5, 0.65), (2, 6, 0.55)):
                end = start + n * frac
                i = start
                while i < end:
                    q = (i - start) / max(1, end - start)
                    col = (c0 if v == 0 else c1) if q < 0.45 else (c1 if q < 0.75 else c2)
                    if q < 0.85 or int(i) % 2 == 0:
                        put(g, tx - dx * i + ppx * v, ty - dy * i + ppy * v, col)
                    i += 0.5
        elif k == "flash":
            yy, x0, x1 = f[1], f[2], f[3]
            for x in range(x0, x1 + 1):
                q = (x - x0) / max(1, x1 - x0)
                put(g, x, yy, c0 if 0.12 < q < 0.97 else c1)
                if 0.3 < q < 0.9:
                    put(g, x, yy - 1, c1 if 0.45 < q < 0.8 else c2)
                if 0.55 < q < 0.85 and x % 2 == 0:
                    put(g, x, yy + 1, c2)
        elif k == "dust" and dust:
            x0, size = f[1], f[2]
            for i in range(-size, size + 1):
                hgt = max(0, int((size - abs(i)) * 0.55 + (1 if i % 3 == 0 else 0)))
                for j in range(hgt):
                    if (i + j) % 2 == 0 or j == 0:
                        put(g, x0 + i, 39 - j, DUST[min(2, j // 2)] if j else DUST[1])
            for i, (ox, oy) in enumerate(((-size - 2, -3), (size + 2, -4), (-size // 2 - 1, -size // 2 - 3),
                                          (size // 2 + 2, -size // 2 - 2))):
                put(g, x0 + ox, 39 + oy, DUST[0] if i % 2 else DUST[1])
            for i in range(-size - 3, size + 4):        # impact line on the floor
                if abs(i) > 1 and (abs(i) < size or i % 2 == 0):
                    put(g, x0 + i, 39, c1 if abs(i) < size * 0.6 else c2)
            put(g, x0, 39, c0); put(g, x0 - 1, 39, c0); put(g, x0 + 1, 39, c0)
        elif k == "glint":
            gx, gy = (tx - dx * 1.5, ty - dy * 1.5) if f[1] == "tip" else f[1]
            for i in range(-3, 4):
                col = c0 if abs(i) < 2 else c1
                put(g, gx + i, gy, col); put(g, gx, gy + i, col)
        else:
            art_fx(g, k, f, (c0, c1, c2), (tx, ty), (dx, dy))
    return g

# ---- weapon-art FX (v5). Palettes: the weapon's smear tones unless the art has its own colour.
EMBER = ((255, 240, 190), (255, 160, 60), (206, 74, 34), (120, 32, 26))
BLOOD = ((255, 150, 150), (214, 40, 58), (120, 16, 34))

def art_fx(g, k, f, tones, tip, d):
    c0, c1, c2 = tones
    tx, ty = tip
    if k == "flare":        # ("flare", (x, y) | "tip", size[, palette]): 8-point burst with a hot core
        gx, gy = (tx - d[0] * 1.0, ty - d[1] * 1.0) if f[1] == "tip" else f[1]
        n = f[2]
        pal = f[3] if len(f) > 3 else (c0, c1, c2)
        for y in range(H):
            for x in range(W):
                r = math.hypot(x - gx, y - gy)
                if r <= n * 0.3:
                    g[y][x] = pal[0]
                elif r <= n * 0.5:
                    g[y][x] = pal[1]
                elif r <= n * 0.62 and (x + y) % 2 == 0:
                    g[y][x] = pal[2]
        for i in range(1, n + 1):
            q = i / n
            col = pal[0] if q < 0.5 else (pal[1] if q < 0.8 else pal[2])
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(g, gx + sx * i, gy + sy * i, col)
            if i < n * 0.6:
                for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                    put(g, gx + sx * i * 0.72, gy + sy * i * 0.72, pal[1] if q < 0.35 else pal[2])
    elif k == "rings":      # ("rings", (x, y), radii): war-cry shock rings opening forward
        cx, cy = f[1]
        for j, R in enumerate(f[2]):
            for t in range(-70, 71, 2):
                a = math.radians(t)
                col = c0 if abs(t) < 30 else (c1 if abs(t) < 55 else c2)
                if abs(t) > 50 and (t // 2) % 2:
                    continue
                put(g, cx + math.cos(a) * R, cy + math.sin(a) * R * 1.15, col if j == 0 else (c1 if col == c0 else c2))
    elif k == "speed":      # ("speed", (x, y), n, length[, palette]): dash lines streaming back from x
        x0, y0 = f[1]
        pal = f[4] if len(f) > 4 else (c0, c1, c2)
        for j in range(f[2]):
            yy = y0 + j * 3 - (j % 2)
            ln = f[3] * (1.0 - 0.18 * ((j * 7) % 4))
            xs = x0 - (j * 5) % 7
            for i in range(int(ln)):
                q = i / max(1, ln)
                if q > 0.6 and i % 2:
                    continue
                put(g, xs - i, yy, pal[0] if q < 0.2 else (pal[1] if q < 0.55 else pal[2]))
    elif k == "wave":       # ("wave", (x, y), half_height, bulge): vertical moon crescent, bulging forward
        cx, cy = f[1]
        hh, b = f[2], f[3]
        for y in range(H):
            v = (y - cy) / hh
            if abs(v) > 1:
                continue
            front = cx + b * (1 - v * v)
            back = cx + b * 0.35 * (1 - v * v) - 1
            for x in range(max(0, int(back)), min(W, int(front) + 2)):
                dd = front - x
                if dd < -0.5:
                    continue
                if dd < 1.2:
                    g[y][x] = c0
                elif dd < 3:
                    g[y][x] = c1
                elif (x + y) % 2 == 0:
                    g[y][x] = c2
    elif k == "ring":       # ("ring", (cx, cy), R, a0, a1[, opt]): band swept round a pivot from a0 (tail) to a1 (head)
        cx, cy = f[1]
        R, a0, a1 = f[2], f[3], f[4]
        opt = f[5] if len(f) > 5 else {}
        sq, wd = opt.get("sq", 0.35), opt.get("w", 3.0)
        pal = opt.get("pal", (c0, c1, c2))
        span = max(-359.0, min(359.0, a1 - a0)) or 1.0
        lo, hi = min(a0, a0 + span), max(a0, a0 + span)
        for y in range(H):
            for x in range(W):
                ex, ey = x + 0.5 - cx, (y + 0.5 - cy) / sq
                rho = math.hypot(ex, ey)
                d = R - rho
                if not -0.6 <= d <= wd:
                    continue
                th = math.degrees(math.atan2(ey, ex))
                while th < lo:
                    th += 360
                while th > hi:
                    th -= 360
                if th < lo:
                    continue
                t = (th - a0) / span
                wt = wd * (0.25 + 0.75 * t ** 0.8)
                if d > wt:
                    continue
                if t < 0.3:
                    if (x + y) % 2 == 0:
                        g[y][x] = pal[2] if d > 1.0 else pal[1]
                elif d < 1.1:
                    g[y][x] = pal[0]
                elif d < wt * 0.55:
                    g[y][x] = pal[1]
                elif (x + y) % 2 == 0 or d < wt * 0.8:
                    g[y][x] = pal[2]
    elif k == "vspeed":     # ("vspeed", (x, y), n, length[, palette]): v10 dive lines streaming UP from y (behind a plunge)
        x0, y0 = f[1]
        pal = f[4] if len(f) > 4 else (c0, c1, c2)
        for j in range(f[2]):
            xx = x0 + j * 3 - (j % 2) - (f[2] - 1) * 1.5
            ln = f[3] * (1.0 - 0.2 * ((j * 5) % 3))
            ys = y0 - (j * 5) % 4
            for i in range(int(ln)):
                q = i / max(1, ln)
                if q > 0.6 and i % 2:
                    continue
                put(g, xx, ys - i, pal[0] if q < 0.2 else (pal[1] if q < 0.55 else pal[2]))
    elif k == "embers":     # ("embers", (x, y), spread, seed): scattered cinders
        cx, cy = f[1]
        sp, seed = f[2], f[3]
        for i in range(10):
            h = (seed * 131 + i * 977) % 1000
            ax = ((h % 37) / 36.0 - 0.5) * 2 * sp
            ay = (((h // 37) % 29) / 28.0 - 0.7) * 2 * sp
            col = EMBER[i % 3]
            put(g, cx + ax, cy + ay, col)
            if i % 3 == 0:
                put(g, cx + ax, cy + ay + 1, EMBER[2])

def mirror_grid(g):
    out = blank()
    for y in range(H):
        for x in range(W):
            if g[y][x] is not None and 0 <= 56 - x < W:
                out[y][56 - x] = g[y][x]
    return out

OFF_FIST = ((0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (1, -1))   # draw_offarm's gauntlet

_SETTLE = False   # v10 polish: while set (see settled()), mseq splits the last frame to ease the weapon back toward idle


def _lerp2(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _settle_frames(frames, base):
    """Split the recovery's last frame (same total time): hold it a little, then a pose halfway back to idle
    (hand (35, 27), blade at -50), so the swing doesn't pop when the idle loop takes over."""
    p, ms = frames[-1]
    q = {**dict(footB=FB, footF=FF), **base, **p}
    if "hand" not in q or q.get("air") or "planted" in q or ms < 60:
        return frames
    ang = q["ang"]
    tgt = _unwrap(-50, ang)
    hx, hy = q["hand"]
    if math.hypot(hx - 35, hy - 27) <= 3 and abs(tgt - ang) <= 25 and abs(q.get("dx", 0)) <= 1 and abs(q.get("dy", 0)) <= 1:
        return frames
    t = 0.55
    mid = {k: v for k, v in p.items() if k not in ("fx", "mirror", "behind", "sheath", "shield", "lash", "offsw", "aura", "heat")}
    mid.update(hand=_lerp2(q["hand"], (35, 27), t), ang=ang + (tgt - ang) * t,
               dx=int(round(q.get("dx", 0) * (1 - t))), dy=int(round(q.get("dy", 0) * (1 - t))), head_dx=0, head_dy=0,
               footB=_lerp2(q["footB"], FB, t), footF=_lerp2(q["footF"], FF, t), flow=0.3, flutter=q.get("flutter", 0) + 1)
    if "slen" in q:
        mid["slen"] = q["slen"] + (18 - q["slen"]) * t
    if "off" in q:
        mid["off"] = _lerp2(q["off"], (31, 26), t)
    if q.get("offw") is not None:
        ow = q["offw"]
        mid["offw"] = (_lerp2(ow[0], (25, 30), t), ow[1] + (_unwrap(152, ow[1]) - ow[1]) * t)
    keep = max(30, int(round(ms * 0.5 / 5)) * 5)
    return frames[:-1] + [(p, keep), (mid, ms - keep)]


def settled(fn):
    def run():
        global _SETTLE
        _SETTLE = True
        try:
            return fn()
        finally:
            _SETTLE = False
    run.__name__ = fn.__name__
    return run


def mseq(frames, base=None, grip=None, art=False):
    """Like seq, plus: two=True (off hand on the grip `grip` px behind the main hand),
    fx=[...] (swing FX, coords in pose space: +dx/+dy), mirror=True (spin frame),
    behind=True (weapon hidden behind the body)."""
    base = base or {}
    if _SETTLE and not art and len(frames) >= 3:
        frames = _settle_frames(frames, base)
    out = []
    prev, prevw = ((35, 27), -50), None
    prevoff = None
    prevlash = None
    for p, ms in frames:
        q = {**dict(footB=FB, footF=FF), **base, **p}
        bx, by = q.get("dx", 0), q.get("dy", 0)
        if q.get("offw") is not None:   # v8 twin blades: the far hand holds the second blade
            q["off"] = q["offw"][0]
        two = q.get("two", grip is not None and "off" not in q) and "hand" in q
        if two:
            g2 = q.get("grip", grip or 3.5)
            a = math.radians(q["ang"])
            q["off"] = (q["hand"][0] - math.cos(a) * g2, q["hand"][1] - math.sin(a) * g2)
        cels = pose(q)
        w = cels.get("Sword")
        if isinstance(w, Wpn):
            fxl = []
            for f in q.get("fx", ()):
                if f[0] == "arc":
                    fxl.append(("arc", (f[1][0] + bx, f[1][1] + by)) + tuple(f[2:]))
                elif f[0] == "dust":
                    fxl.append(("dust", f[1] + bx, f[2]))
                elif f[0] == "glint":
                    fxl.append(("glint", f[1] if f[1] == "tip" else (f[1][0] + bx, f[1][1] + by)))
                elif f[0] == "sweep":
                    opt = f[1] if len(f) > 1 else {}
                    h0 = opt.get("h0", prev[0])
                    a0 = opt.get("a0", prev[1])
                    if "a0" not in opt:
                        a0 = _unwrap(a0, q["ang"])
                    fxl.append(("sweep", h0, a0, opt, prevw))
                elif f[0] in ("flare", "rings", "speed", "wave", "embers", "ring", "vspeed"):
                    pt = f[1] if f[1] == "tip" else (f[1][0] + bx, f[1][1] + by)
                    fxl.append((f[0], pt) + tuple(f[2:]))
                elif f[0] == "flash":
                    fxl.append(f)
                else:
                    fxl.append(f)
            w.fx = tuple(fxl)
            if two:   # off-hand fist closes over the grip wherever it is not hidden by the body
                ox, oy = int(round(q["off"][0] + bx)), int(round(q["off"][1] + by))
                front = [cels[n] for n in ("Torso", "FrontLeg", "Pauldron", "Head", "Arm") if n in cels]
                w.clear = tuple((ox + a2, oy + b2) for a2, b2 in OFF_FIST
                                if 0 <= ox + a2 < W and 0 <= oy + b2 < H
                                and not any(c[oy + b2][ox + a2] for c in front))
        if isinstance(w, Wpn) and q.get("shield") is not None:   # v8: explicit shield pose rel. to the off hand
            o = q["shield"]
            if "abs" in o:   # a free shield pose (pose space): sliding round the hip / slung on the back
                c = (o["abs"][0] + bx, o["abs"][1] + by)
            else:
                c = (q["off"][0] + bx + o.get("ox", 1.5), q["off"][1] + by + o.get("oy", 0.5))
            w.shield = (c, o.get("rot", 0), o.get("sx", 0.62), o.get("layer", "front"))
        if isinstance(w, Wpn) and q.get("offw") is not None:
            (ohx, ohy), oang = q["offw"][0], q["offw"][1]
            oslen = q["offw"][2] if len(q["offw"]) > 2 else 18
            ofront = q["offw"][3] if len(q["offw"]) > 3 else False
            w.offw = ((ohx + bx, ohy + by), oang, oslen, ofront)
            if q.get("offsw") and prevoff is not None:
                w.offfx = (("sweep", prevoff[0], _unwrap(prevoff[1], oang), dict(w=q["offsw"])),)
            prevoff = (w.offw[0], oang)
        if isinstance(w, Wpn) and q.get("lash") is not None:   # v9 whip: lash control points (pose space)
            w.lash = [(x + bx, y + by) for x, y in q["lash"]]
            w.lash_prev = prevlash
            prevlash = w.lash
        elif isinstance(w, Wpn):
            prevlash = None
        if isinstance(w, Wpn) and q.get("sheath"):
            w.sheath = True
        if isinstance(w, Wpn) and q.get("aura"):
            w.aura, w.aura_pal = q["aura"], q.get("aura_pal")
        if isinstance(w, Wpn) and q.get("heat"):
            w.heat = q["heat"]
        if isinstance(w, Wpn) and q.get("fx_pal"):
            w.fx_pal = q["fx_pal"]
        if isinstance(w, Wpn) and art:
            w.clear_fx = True
        if "hand" in q:
            prev = ((q["hand"][0] + bx, q["hand"][1] + by), q["ang"])
            prevw = (prev[0], q["ang"], q.get("slen", 18), False, True, q.get("air", False)) if isinstance(w, Wpn) else None
        if q.get("mirror"):
            for n in list(cels):
                if not isinstance(cels[n], (Wpn, RotWpn, Image.Image)):
                    cels[n] = mirror_grid(cels[n])
            if isinstance(w, Wpn):
                w.mirror = True
        if q.get("behind") and isinstance(w, Wpn):
            w.mask = compose(imgs({n: c for n, c in cels.items() if n != "Sword"}, None))
        out.append((cels, ms))
    return out

SH = (27, 22)          # main shoulder in pose space (before dx/dy)
SW = ("sweep",)        # smear: the band swept since the previous frame

def sw(**k):
    return ("sweep", k)

# ---------------------------------------------------------------- dagger: short, fast, low
def dg_1():  # quick forward stab
    return mseq([(dict(dx=-1, dy=1, hand=(29, 26), ang=-12, off=(33, 24), footB=(OX + 6, 39), flow=0.3), 60),
                 (dict(dx=1, dy=1, hand=(36, 25), ang=-6, off=(27, 26), flow=0.6, flutter=1), 40),
                 (dict(dx=2, dy=1, hand=(40, 25), ang=-2, off=(22, 26), footF=(FF[0] + 2, 39), flow=0.9, flutter=2,
                       fx=[("streak", 14)]), 50),
                 (dict(dx=2, dy=1, hand=(39, 25), ang=-2, off=(23, 26), footF=(FF[0] + 2, 39), flow=0.7, flutter=3), 70),
                 (dict(hand=(34, 27), ang=-35, off=(31, 26), flow=0.3), 90)])

def dg_2():  # backhand horizontal slash
    return mseq([(dict(dx=-1, dy=1, head_dx=-1, hand=(26, 24), ang=174, off=(33, 26), flow=0.3), 60),
                 (dict(dy=1, hand=(31, 25), ang=128, slen=12, off=(31, 26), flow=0.5, flutter=1), 40),
                 (dict(dx=2, dy=1, hand=(38, 23), ang=-10, off=(24, 25), footF=(FF[0] + 2, 39), flow=0.9, flutter=2,
                       fx=[("arc", (30, 25), 176, -10, dict(sq=0.45, w=0.6))]), 50),
                 (dict(dx=2, dy=1, hand=(39, 21), ang=-38, off=(24, 26), footF=(FF[0] + 2, 39), flow=0.8, flutter=3,
                       fx=[sw(w=0.5)]), 60),
                 (dict(dx=1, hand=(35, 26), ang=-35, off=(29, 26), flow=0.4), 90)])

def dg_3():  # low lunging stab
    return mseq([(dict(dx=-1, dy=3, hand=(29, 29), ang=-5, off=(33, 27), footB=(OX + 5, 39), footF=(OX + 18, 39), flow=0.3), 70),
                 (dict(dx=2, dy=4, hand=(36, 31), ang=8, off=(24, 27), footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.0, flutter=1), 40),
                 (dict(dx=3, dy=5, head_dy=1, hand=(40, 32), ang=6, off=(20, 26), footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.4, flutter=2,
                       fx=[("streak", 16)]), 50),
                 (dict(dx=3, dy=5, head_dy=1, hand=(39, 32), ang=6, off=(21, 27), footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.0, flutter=3), 80),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=-25, off=(30, 27), footF=(OX + 21, 39), flow=0.5), 100)])

def dg_4():  # spinning double slash finisher
    return mseq([(dict(dx=-1, dy=1, head_dx=-1, hand=(28, 18), ang=-150, off=(33, 26), flow=0.3), 70),
                 (dict(dx=1, dy=1, hand=(33, 18), ang=-80, off=(30, 26), flow=0.6, flutter=1), 40),
                 (dict(dx=2, dy=2, hand=(38, 25), ang=12, off=(24, 25), footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                       fx=[sw(w=0.7)]), 50),
                 (dict(dx=1, dy=2, hand=(38, 26), ang=15, off=(26, 24), flow=1.4, flutter=4, mirror=True,
                       fx=[("arc", (28, 27), 190, 20, dict(sq=0.45, w=0.6))]), 50),
                 (dict(dx=2, dy=2, hand=(39, 24), ang=-20, off=(23, 24), footF=(FF[0] + 3, 39), flow=1.3, flutter=5,
                       fx=[("arc", (28, 27), 170, -20, dict(sq=0.45, w=0.6))]), 60),
                 (dict(dx=2, dy=2, hand=(38, 22), ang=-40, off=(24, 25), footF=(FF[0] + 3, 39), flow=0.9, flutter=6), 110),
                 (dict(dx=1, hand=(35, 27), ang=-35, off=(30, 26), flow=0.4), 110)])

def dg_heavy():  # crouch, then lunging double stab
    return mseq([(dict(dy=3, hand=(31, 28), ang=-10, off=(33, 26), footB=(OX + 6, 39), flow=0.3), 80),
                 (dict(dx=-2, dy=5, head_dy=1, hand=(27, 29), ang=-6, off=(32, 27), footB=(OX + 4, 39), footF=(OX + 18, 39), flow=0.2), 130),
                 (dict(dx=-2, dy=6, head_dy=1, hand=(27, 30), ang=-4, off=(32, 28), footB=(OX + 4, 39), footF=(OX + 18, 39), flow=0.2, flutter=1,
                       fx=[("glint", "tip")]), 160),
                 (dict(dx=2, dy=3, hand=(35, 26), ang=-4, off=(25, 26), footB=(OX + 6, 38), footF=(OX + 22, 39), flow=1.1, flutter=2), 40),
                 (dict(dx=4, dy=3, hand=(40, 24), ang=-6, off=(21, 25), footB=(OX + 9, 39), footF=(OX + 25, 39), flow=1.5, flutter=3,
                       fx=[("streak", 18)]), 50),
                 (dict(dx=4, dy=5, head_dy=1, hand=(40, 30), ang=10, off=(21, 26), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.3, flutter=4,
                       fx=[("streak", 16)]), 50),
                 (dict(dx=4, dy=5, head_dy=1, hand=(39, 30), ang=10, off=(22, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=0.9, flutter=5), 120),
                 (dict(dx=1, dy=1, hand=(35, 27), ang=-30, off=(30, 26), footF=(OX + 21, 39), flow=0.4), 130)])

# ---------------------------------------------------------------- great: slow, huge, two-handed
GRIP_GREAT = 3.5

def gs_1():  # overhead diagonal chop, behind the shoulder -> into the ground
    return mseq([(dict(dy=1, hand=(32, 22), ang=-95, flow=0.3), 100),
                 (dict(dx=-1, dy=1, hand=(29, 15), ang=-140, flow=0.3, flutter=1), 120),
                 (dict(dx=-2, dy=2, head_dx=-1, hand=(26, 14), ang=-168, footB=(OX + 6, 39), flow=0.2, flutter=1), 150),
                 (dict(dx=-2, dy=2, head_dx=-1, hand=(26, 15), ang=-176, footB=(OX + 6, 39), flow=0.2, flutter=2), 210),
                 (dict(dx=0, dy=1, hand=(30, 13), ang=-112, footF=(FF[0] + 2, 39), flow=0.5, flutter=2,
                       fx=[sw(w=0.35)]), 60),
                 (dict(dx=2, dy=2, hand=(37, 19), ang=-22, slen=15, footF=(FF[0] + 3, 39), flow=1.0, flutter=3,
                       fx=[sw(w=0.5)]), 50),
                 (dict(dx=3, dy=4, head_dy=1, hand=(37, 29), ang=40, slen=16, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.2, flutter=4,
                       fx=[sw(w=0.5), ("dust", 50, 5)]), 60),
                 (dict(dx=3, dy=5, head_dy=1, hand=(37, 30), ang=42, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=0.6, flutter=5,
                       fx=[("dust", 51, 3)]), 230),
                 (dict(dx=1, dy=3, hand=(35, 28), ang=30, footF=(FF[0] + 2, 39), flow=0.3), 190)], grip=GRIP_GREAT)

def gs_2():  # rising sweep: floor -> overhead
    return mseq([(dict(dy=2, hand=(33, 29), ang=115, flow=0.3), 110),
                 (dict(dx=-1, dy=4, head_dy=1, hand=(30, 31), ang=150, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.2), 140),
                 (dict(dx=-1, dy=5, head_dy=1, hand=(30, 31), ang=156, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.2, flutter=1,
                       fx=[("dust", 8, 2)]), 180),
                 (dict(dx=1, dy=3, hand=(35, 31), ang=100, footF=(FF[0] + 2, 39), flow=0.6, flutter=2,
                       fx=[sw(w=0.3), ("dust", 34, 2)]), 60),
                 (dict(dx=2, dy=0, hand=(39, 23), ang=-25, slen=15, footF=(FF[0] + 3, 39), flow=1.0, flutter=3,
                       fx=[sw(w=0.5)]), 50),
                 (dict(dx=2, dy=-2, hand=(35, 13), ang=-88, footB=(OX + 9, 37), footF=(FF[0] + 3, 39), flow=1.2, flutter=4,
                       fx=[sw(w=0.5)]), 60),
                 (dict(dx=1, dy=-1, hand=(30, 13), ang=-128, footF=(FF[0] + 2, 39), flow=0.8, flutter=5), 150),
                 (dict(dx=0, dy=1, hand=(30, 18), ang=-158, flow=0.4, flutter=6), 170),
                 (dict(dy=1, hand=(33, 25), ang=-70, flow=0.3), 170)], grip=GRIP_GREAT)

def gs_3():  # full horizontal spin sweep finisher
    ARC = dict(sq=0.38, w=0.5)
    return mseq([(dict(dx=-1, dy=2, hand=(30, 27), ang=168, footB=(OX + 6, 39), flow=0.3), 110),
                 (dict(dx=-2, dy=3, head_dx=-1, hand=(26, 27), ang=174, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2), 140),
                 (dict(dx=-2, dy=4, head_dx=-1, hand=(26, 28), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1), 190),
                 (dict(dx=0, dy=3, hand=(31, 27), ang=172, slen=14, footF=(FF[0] + 2, 39), flow=0.8, flutter=2), 60),
                 (dict(dx=1, dy=2, hand=(34, 28), ang=118, slen=8, footF=(FF[0] + 3, 39), flow=1.1, flutter=3,
                       fx=[("arc", (29, 28), 178, 118, ARC)]), 50),
                 (dict(dx=2, dy=2, hand=(38, 26), ang=0, footF=(FF[0] + 3, 39), flow=1.3, flutter=4,
                       fx=[("arc", (29, 28), 160, 0, ARC)]), 50),
                 (dict(dx=2, dy=2, hand=(38, 26), ang=-8, footF=(FF[0] + 3, 39), flow=1.5, flutter=5, mirror=True, behind=True,
                       fx=[("arc", (29, 28), 0, -170, ARC)]), 50),
                 (dict(dx=3, dy=3, hand=(38, 27), ang=12, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.4, flutter=6,
                       fx=[("arc", (29, 28), 170, 12, ARC)]), 60),
                 (dict(dx=3, dy=4, head_dy=1, hand=(37, 30), ang=38, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=0.8, flutter=7,
                       fx=[sw(w=0.4), ("dust", 52, 3)]), 220),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=25, footF=(FF[0] + 2, 39), flow=0.3), 190)], grip=GRIP_GREAT)

def gs_heavy():  # hop up, slam down
    return mseq([(dict(dy=3, hand=(33, 29), ang=125, flow=0.3), 110),
                 (dict(dx=-1, dy=5, head_dy=1, hand=(30, 31), ang=150, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.2), 150),
                 (dict(dx=-1, dy=6, head_dy=1, hand=(30, 31), ang=154, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1), 170),
                 (dict(dy=-4, hand=(30, 16), ang=-115, footB=(OX + 9, 37), footF=(OX + 18, 36), flow=1.0, flutter=2, air=True,
                       fx=[("dust", 28, 3)]), 70),
                 (dict(dy=-8, hand=(28, 13), ang=-160, footB=(OX + 9, 33), footF=(OX + 18, 32), flow=1.2, flutter=3, air=True), 100),
                 (dict(dy=-7, head_dx=-1, hand=(27, 14), ang=-172, footB=(OX + 9, 34), footF=(OX + 18, 33), flow=0.9, flutter=4, air=True), 130),
                 (dict(dy=-4, hand=(31, 12), ang=-100, footB=(OX + 9, 36), footF=(OX + 19, 36), flow=0.3, flutter=5, air=True,
                       fx=[sw(w=0.35)]), 50),
                 (dict(dx=1, dy=1, hand=(38, 21), ang=-12, slen=15, footF=(FF[0] + 2, 39), flow=0.0, flutter=6,
                       fx=[sw(w=0.5)]), 50),
                 (dict(dx=2, dy=5, head_dy=1, hand=(36, 30), ang=50, slen=16, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=0.9, flutter=7,
                       fx=[sw(w=0.5), ("dust", 46, 7)]), 70),
                 (dict(dx=2, dy=6, head_dy=1, hand=(36, 31), ang=52, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=0.6, flutter=8,
                       fx=[("dust", 46, 4)]), 280),
                 (dict(dx=1, dy=3, hand=(35, 29), ang=35, footF=(FF[0] + 2, 39), flow=0.3), 200)], grip=GRIP_GREAT)

# ---------------------------------------------------------------- spear: reach, both hands, held long
GRIP_SPEAR = 6.0

def sp_1():  # straight thrust
    return mseq([(dict(dx=-2, dy=1, hand=(29, 26), ang=-2, footB=(OX + 5, 39), flow=0.3), 90),
                 (dict(dx=-3, dy=1, head_dx=-1, hand=(26, 26), ang=-2, footB=(OX + 4, 39), flow=0.2, flutter=1), 80),
                 (dict(dx=2, dy=1, hand=(39, 26), ang=0, footB=(OX + 8, 39), footF=(OX + 23, 39), flow=1.2, flutter=2,
                       fx=[("streak", 22)]), 50),
                 (dict(dx=2, dy=1, hand=(39, 26), ang=0, footB=(OX + 8, 39), footF=(OX + 23, 39), flow=1.0, flutter=3,
                       fx=[("streak", 10)]), 60),
                 (dict(dx=1, hand=(34, 26), ang=-3, footF=(OX + 21, 39), flow=0.5), 100),
                 (dict(hand=(33, 27), ang=-8, flow=0.3), 110)], grip=GRIP_SPEAR)

def sp_2():  # rising thrust, ~20 deg up
    return mseq([(dict(dx=-1, dy=2, hand=(29, 29), ang=-12, footB=(OX + 6, 39), flow=0.3), 90),
                 (dict(dx=-2, dy=4, head_dy=1, hand=(27, 30), ang=-18, footB=(OX + 5, 39), flow=0.2, flutter=1), 90),
                 (dict(dx=2, dy=-1, hand=(37, 21), ang=-20, footB=(OX + 8, 37), footF=(OX + 22, 39), flow=1.2, flutter=2,
                       fx=[("streak", 20)]), 50),
                 (dict(dx=2, dy=-1, hand=(38, 20), ang=-21, footB=(OX + 8, 37), footF=(OX + 22, 39), flow=1.0, flutter=3,
                       fx=[("streak", 10)]), 60),
                 (dict(dx=1, hand=(34, 24), ang=-14, footF=(OX + 21, 39), flow=0.5), 100),
                 (dict(hand=(33, 27), ang=-8, flow=0.3), 110)], grip=GRIP_SPEAR)

def sp_3():  # overhead circular sweep
    return mseq([(dict(hand=(33, 22), ang=-60, flow=0.3), 90),
                 (dict(dx=-1, hand=(30, 15), ang=-145, flow=0.4, flutter=1), 100),
                 (dict(dx=-1, dy=1, head_dx=-1, hand=(29, 15), ang=-172, footB=(OX + 6, 39), flow=0.3, flutter=2), 120),
                 (dict(dx=0, dy=-1, hand=(32, 13), ang=-100, flow=0.9, flutter=3, fx=[sw(w=0.3)]), 50),
                 (dict(dx=1, dy=0, hand=(36, 16), ang=-35, footF=(FF[0] + 2, 39), flow=1.1, flutter=4, fx=[sw(w=0.3)]), 50),
                 (dict(dx=2, dy=2, hand=(38, 25), ang=22, footF=(FF[0] + 3, 39), flow=1.2, flutter=5, fx=[sw(w=0.3)]), 60),
                 (dict(dx=2, dy=2, hand=(36, 28), ang=30, footF=(FF[0] + 3, 39), flow=0.7, flutter=6), 110),
                 (dict(dx=1, hand=(33, 27), ang=-6, flow=0.3), 120)], grip=GRIP_SPEAR)

def sp_heavy():  # step-in charging lunge
    return mseq([(dict(dx=-1, dy=1, hand=(31, 26), ang=-2, flow=0.3), 100),
                 (dict(dx=-3, dy=2, head_dx=-1, hand=(26, 26), ang=-4, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2), 140),
                 (dict(dx=-3, dy=3, head_dx=-1, hand=(25, 27), ang=-5, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2, flutter=1,
                       fx=[("glint", "tip")]), 180),
                 (dict(dx=1, dy=1, hand=(31, 26), ang=-2, footB=(OX + 7, 38), footF=(OX + 22, 36), flow=1.2, flutter=2), 70),
                 (dict(dx=3, dy=2, hand=(39, 26), ang=0, footB=(OX + 9, 39), footF=(OX + 25, 39), flow=1.6, flutter=3,
                       fx=[("streak", 24)]), 50),
                 (dict(dx=4, dy=3, head_dy=1, hand=(39, 26), ang=1, footB=(OX + 10, 39), footF=(OX + 26, 39), flow=1.5, flutter=4,
                       fx=[("streak", 14)]), 60),
                 (dict(dx=4, dy=3, head_dy=1, hand=(39, 26), ang=1, footB=(OX + 10, 39), footF=(OX + 26, 39), flow=1.0, flutter=5), 70),
                 (dict(dx=2, dy=1, hand=(34, 26), ang=-3, footF=(OX + 22, 39), flow=0.5), 140),
                 (dict(hand=(33, 27), ang=-8, flow=0.3), 140)], grip=GRIP_SPEAR)

# ---------------------------------------------------------------- katana: fluid, elegant, fast
GRIP_KATANA = 3.5
KARC = dict(sq=0.42, w=0.35)

def kt_1():  # horizontal draw cut (one-handed out of the hip)
    return mseq([(dict(dx=-1, dy=1, hand=(30, 29), ang=166, off=(32, 28), footB=(OX + 6, 39), flow=0.3), 80),
                 (dict(dy=1, hand=(34, 27), ang=-172, off=(30, 28), flow=0.6, flutter=1), 40),
                 (dict(dx=2, dy=1, hand=(39, 24), ang=-6, off=(23, 26), footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                       fx=[("arc", (29, 26), 172, -6, KARC)]), 50),
                 (dict(dx=2, dy=1, hand=(39, 21), ang=-32, off=(23, 25), footF=(FF[0] + 2, 39), flow=1.0, flutter=3,
                       fx=[sw(w=0.35)]), 60),
                 (dict(dx=1, hand=(36, 17), ang=-70, off=(26, 25), footF=(FF[0] + 1, 39), flow=0.6, flutter=4), 90),
                 (dict(hand=(35, 26), ang=-42, off=(30, 26), flow=0.3), 110)])

def kt_2():  # reverse rising diagonal cut (two hands)
    return mseq([(dict(dx=-1, dy=2, hand=(30, 30), ang=140, flow=0.3), 80),
                 (dict(dy=2, hand=(33, 31), ang=105, flow=0.5, flutter=1), 40),
                 (dict(dx=2, dy=0, hand=(39, 24), ang=-25, footF=(FF[0] + 2, 39), flow=1.0, flutter=2, fx=[sw(w=0.35)]), 50),
                 (dict(dx=2, dy=-1, hand=(36, 15), ang=-72, footB=(OX + 9, 38), footF=(FF[0] + 2, 39), flow=1.1, flutter=3,
                       fx=[sw(w=0.35)]), 60),
                 (dict(dx=1, hand=(32, 14), ang=-112, flow=0.6, flutter=4), 90),
                 (dict(hand=(34, 25), ang=-50, flow=0.3), 110)], grip=GRIP_KATANA)

def kt_3():  # spinning cut finisher
    return mseq([(dict(dx=-1, dy=1, hand=(29, 21), ang=-158, flow=0.3), 80),
                 (dict(dx=-2, dy=2, head_dx=-1, hand=(27, 25), ang=176, footB=(OX + 6, 39), flow=0.2, flutter=1), 90),
                 (dict(dx=0, dy=2, hand=(33, 26), ang=-170, flow=1.0, flutter=2, mirror=True), 50),
                 (dict(dx=1, dy=2, hand=(37, 25), ang=-10, flow=1.4, flutter=3, mirror=True, behind=True,
                       fx=[("arc", (29, 27), -170, -10, KARC)]), 50),
                 (dict(dx=2, dy=2, hand=(39, 25), ang=-4, footF=(FF[0] + 3, 39), flow=1.4, flutter=4,
                       fx=[("arc", (29, 27), 175, -4, KARC)]), 50),
                 (dict(dx=2, dy=1, hand=(38, 17), ang=-60, footF=(FF[0] + 3, 39), flow=1.1, flutter=5, fx=[sw(w=0.35)]), 60),
                 (dict(dx=2, dy=1, hand=(34, 14), ang=-110, footF=(FF[0] + 2, 39), flow=0.7, flutter=6), 110),
                 (dict(dx=1, dy=1, hand=(37, 28), ang=40, flow=0.4, flutter=7), 150)], grip=GRIP_KATANA)

def kt_heavy():  # iaido: sheathed crouch held ~400ms, then a flash draw-cut
    stance = dict(hand=(30, 29), ang=168, off=(32, 28), footB=(OX + 4, 39), footF=(OX + 21, 39), sheath=True)
    return mseq([(dict(dy=2, flow=0.3, **stance), 90),
                 (dict(dx=-1, dy=4, head_dy=1, flow=0.2, **stance), 130),
                 (dict(dx=-1, dy=4, head_dy=1, flow=0.15, flutter=1, **stance), 140),
                 (dict(dx=-1, dy=5, head_dy=1, flow=0.1, flutter=2, **stance), 140),
                 (dict(dx=-1, dy=5, head_dy=2, flow=0.1, flutter=2, fx=[("glint", (31, 27))], **stance), 120),
                 (dict(dx=2, dy=4, hand=(35, 27), ang=-172, off=(31, 28), footB=(OX + 7, 38), footF=(OX + 24, 39), flow=1.3, flutter=3), 40),
                 (dict(dx=4, dy=4, hand=(40, 26), ang=-4, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.6, flutter=4,
                       fx=[("flash", 30, 2, 62), ("arc", (31, 28), 172, -4, dict(sq=0.35, w=0.3))]), 50),
                 (dict(dx=4, dy=4, hand=(40, 22), ang=-36, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.4, flutter=5,
                       fx=[("flash", 30, 12, 50), sw(w=0.35)]), 60),
                 (dict(dx=4, dy=4, hand=(40, 19), ang=-48, off=(24, 27), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=0.8, flutter=6), 220),
                 (dict(dx=2, dy=2, hand=(37, 28), ang=38, off=(28, 27), footF=(OX + 22, 39), flow=0.4, flutter=7), 160)])

# ---------------------------------------------------------------- v5: weapon arts (any weapon)
# Special techniques appended after frame 252. Bigger arcs, longer held anticipation, glow/flare FX.
def art_crescent():  # low wind-back, huge two-handed rising diagonal sweep that looses a crescent
    return mseq([(dict(dx=-1, dy=2, hand=(30, 30), ang=150, footB=(OX + 6, 39), flow=0.3), 100),
                 (dict(dx=-2, dy=4, head_dx=-1, hand=(27, 31), ang=168, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2), 140),
                 (dict(dx=-2, dy=5, head_dx=-1, head_dy=1, hand=(26, 31), ang=172, footB=(OX + 5, 39), footF=(FF[0] + 1, 39),
                       flow=0.2, flutter=1, aura=1, fx=[("glint", "tip")]), 180),
                 (dict(dx=0, dy=3, hand=(32, 32), ang=125, slen=16, footF=(FF[0] + 2, 39), flow=0.7, flutter=2, aura=1,
                       fx=[sw(w=0.4)]), 50),
                 (dict(dx=2, dy=0, hand=(39, 23), ang=-32, footB=(OX + 8, 38), footF=(FF[0] + 3, 39), flow=1.3, flutter=3,
                       fx=[("arc", (30, 25), 172, -32, dict(sq=0.55, w=0.95))]), 55),
                 (dict(dx=2, dy=-2, hand=(36, 13), ang=-88, footB=(OX + 9, 37), footF=(FF[0] + 3, 39), flow=1.4, flutter=4,
                       fx=[sw(w=0.55)]), 60),
                 (dict(dx=1, dy=-1, hand=(30, 12), ang=-128, footF=(FF[0] + 2, 39), flow=0.8, flutter=5), 170),
                 (dict(dy=1, hand=(33, 24), ang=-65, flow=0.3, flutter=6), 180)], grip=GRIP_GREAT, art=True)

def art_bloodstep():  # crouched sprint-dash, blade trailing low behind (engine moves the body on 2-4)
    dash = dict(dx=4, head_dx=2, off=(39, 25), flow=2.0, aura=1, aura_pal=BLOOD)
    return mseq([(dict(dx=-1, dy=3, hand=(30, 30), ang=162, off=(33, 27), footB=(OX + 5, 39), flow=0.3), 90),
                 (dict(dx=-2, dy=5, head_dy=1, hand=(27, 30), ang=170, off=(31, 28), footB=(OX + 4, 39), footF=(OX + 18, 39),
                       flow=0.2, flutter=1, fx=[("glint", "tip")]), 140),
                 (dict(dy=5, head_dy=1, hand=(26, 28), ang=172, footB=(OX + 3, 38), footF=(OX + 27, 39), flutter=2,
                       fx=[("speed", (16, 17), 6, 20, BLOOD)], **dash), 50),
                 (dict(dy=6, head_dy=1, hand=(25, 28), ang=174, footB=(OX + 14, 36), footF=(OX + 22, 39), flutter=4,
                       fx=[("speed", (15, 18), 6, 22, BLOOD)], **dash), 50),
                 (dict(dy=5, head_dy=1, hand=(26, 28), ang=172, footB=(OX + 4, 38), footF=(OX + 27, 39), flutter=6,
                       fx=[("speed", (16, 17), 5, 14, BLOOD)], **dash), 60),
                 (dict(dx=1, dy=2, hand=(33, 29), ang=30, off=(31, 27), footF=(OX + 21, 39), flow=0.5, flutter=7), 160)], art=True)

def art_stormleap():  # crouch, spring up spinning the weapon overhead, plunge, impact (shockwave on 9)
    SPIN = dict(sq=0.35, w=0.45)
    up = dict(footB=(OX + 9, 33), footF=(OX + 18, 32), air=True)
    return mseq([(dict(dy=3, hand=(33, 29), ang=125, flow=0.3), 90),
                 (dict(dx=-1, dy=6, head_dy=1, hand=(30, 31), ang=150, footB=(OX + 6, 39), footF=(FF[0] + 1, 39),
                       flow=0.2, flutter=1, fx=[("glint", "tip")]), 170),
                 (dict(dy=-4, hand=(31, 15), ang=-100, footB=(OX + 9, 37), footF=(OX + 18, 36), air=True, flow=1.1, flutter=2,
                       fx=[sw(w=0.2), ("dust", 28, 4)]), 60),
                 (dict(dy=-7, hand=(34, 14), ang=-166, flow=1.3, flutter=3, behind=True,
                       fx=[("arc", (30, 13), 10, 190, SPIN)], **up), 60),
                 (dict(dy=-8, hand=(34, 14), ang=-166, flow=1.2, flutter=4, mirror=True,
                       fx=[("arc", (30, 13), 10, 190, SPIN)], **up), 60),
                 (dict(dy=-8, hand=(35, 14), ang=-14, flow=1.3, flutter=5,
                       fx=[("arc", (30, 13), 190, 346, SPIN)], **up), 60),
                 (dict(dy=-5, hand=(35, 13), ang=-176, flow=0.9, flutter=6, aura=1, behind=True, fx=[("glint", "tip")], **up), 120),
                 (dict(dy=-5, hand=(35, 24), ang=72, flow=0.2, flutter=7, footB=(OX + 9, 37), footF=(OX + 18, 38), air=True,
                       fx=[sw(w=0.4)]), 50),
                 (dict(dy=-2, hand=(37, 28), ang=86, flow=0.1, flutter=8, footB=(OX + 9, 38), footF=(OX + 18, 39), air=True,
                       fx=[("streak", 14)]), 50),
                 (dict(dx=2, dy=6, head_dy=1, hand=(37, 27), ang=90, planted=(39, 33), footB=(OX + 5, 39), footF=(FF[0] + 3, 39),
                       flow=1.0, flutter=9, fx=[("dust", 38, 10), ("flare", (38, 30), 10)]), 110),
                 (dict(dx=2, dy=6, head_dy=1, hand=(37, 27), ang=90, planted=(39, 33), footB=(OX + 5, 39), footF=(FF[0] + 3, 39),
                       flow=0.6, flutter=10, fx=[("dust", 38, 5)]), 230),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=30, footF=(FF[0] + 2, 39), flow=0.3), 190)], grip=GRIP_GREAT, art=True)

def art_warcry():  # plant the weapon point-down, rear back, roar with the chest out and the free arm flung wide
    plant = dict(planted=(38, 27), ang=90)
    roar = dict(dx=1, head_dx=-1, head_dy=-1, hand=(37, 27), off=(14, 17), **plant)
    rings = lambda rr: ("rings", (32, 14), rr)
    return mseq([(dict(dy=1, hand=(36, 21), ang=88, off=(30, 26), flow=0.3), 100),
                 (dict(dy=2, hand=(38, 25), off=(31, 27), flow=0.3, flutter=1, fx=[("dust", 38, 3)], **plant), 110),
                 (dict(dx=-1, dy=3, head_dx=-1, head_dy=1, hand=(39, 24), off=(29, 29), footB=(OX + 7, 39), flow=0.1, flutter=1,
                       **plant), 180),
                 (dict(flow=1.3, flutter=2, fx=[rings((5, 9))], **roar), 110),
                 (dict(flow=1.5, flutter=3, fx=[rings((9, 13))], **roar), 140),
                 (dict(flow=1.4, flutter=4, fx=[rings((12, 17))], **roar), 150),
                 (dict(flow=1.5, flutter=5, fx=[rings((6, 16))], **roar), 150),
                 (dict(flow=1.2, flutter=6, fx=[rings((10, 20))], **roar), 120),
                 (dict(dy=1, hand=(37, 26), off=(26, 27), flow=0.5, flutter=7, **plant), 150),
                 (dict(hand=(35, 27), ang=-50, off=(30, 26), flow=0.3), 150)], art=True)

def art_moonwave():  # two-handed overhead charge (glowing), vertical cut releasing the wave on 5
    charge = dict(dx=-1, dy=1, hand=(34, 13), ang=-150, footB=(OX + 6, 39), behind=True)
    return mseq([(dict(dy=1, hand=(33, 20), ang=-95, flow=0.3), 100),
                 (dict(dx=-1, hand=(34, 14), ang=-128, footB=(OX + 7, 39), flow=0.3, aura=1, behind=True), 120),
                 (dict(flow=0.4, flutter=1, aura=2, **charge), 140),
                 (dict(flow=0.5, flutter=2, aura=3, fx=[("glint", "tip")], **charge), 140),
                 (dict(flow=0.4, flutter=3, aura=2, fx=[("glint", (22, 6))], **charge), 120),
                 (dict(dx=2, dy=3, hand=(39, 27), ang=58, footF=(FF[0] + 3, 39), flow=1.3, flutter=4, aura=1,
                       fx=[sw(w=0.45, a0=-95), ("wave", (47, 21), 17, 9)]), 50),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 31), ang=78, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=5,
                       fx=[("dust", 47, 5)]), 90),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 31), ang=80, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.6, flutter=6,
                       fx=[("dust", 47, 3)]), 200),
                 (dict(dx=2, dy=3, hand=(36, 29), ang=60, footF=(FF[0] + 2, 39), flow=0.4, flutter=7), 150),
                 (dict(dy=1, hand=(34, 26), ang=-40, flow=0.3), 170)], grip=GRIP_GREAT, art=True)

def art_cinderblade():  # blade upright before the face, the free hand draws fire along it hilt->tip, flare, flick
    up = dict(dx=1, hand=(35, 29), ang=-88, two=True)
    def slide(gp, ms, **k):   # the palm glows as it drags the fire up the blade
        k["fx"] = [("flare", (35.5, 29.5 - gp), 4, EMBER)] + k.get("fx", [])
        return (dict(grip=-gp, heat=(0, gp + 1), flow=0.2, **up, **k), ms)
    return mseq([(dict(dy=1, hand=(34, 28), ang=-60, off=(30, 27), flow=0.3), 100),
                 (dict(grip=-3, flow=0.2, **up), 150),
                 slide(5, 90, flutter=1, fx=[("embers", (36, 22), 2, 1)]),
                 slide(8, 90, flutter=1, fx=[("embers", (36, 19), 3, 2)]),
                 slide(11, 90, flutter=2, fx=[("embers", (36, 16), 3, 3)]),
                 slide(14, 100, flutter=2, fx=[("embers", (36, 13), 4, 4)]),
                 (dict(heat=(0, 40), off=(38, 11), flow=0.5, flutter=3, fx=[("flare", "tip", 9, EMBER), ("embers", (36, 12), 6, 5)],
                       **{k: v for k, v in up.items() if k != "two"}), 70),
                 (dict(dx=2, hand=(39, 25), ang=-12, off=(27, 26), heat=(0, 40), footF=(FF[0] + 2, 39), flow=1.0, flutter=4,
                       fx=[sw(w=0.5), ("embers", (44, 18), 6, 6)], aura=1, aura_pal=EMBER[1:], fx_pal=EMBER[:3]), 50),
                 (dict(dx=2, dy=1, hand=(39, 28), ang=32, off=(28, 27), heat=(0, 40), footF=(FF[0] + 2, 39), flow=0.8, flutter=5,
                       fx=[sw(w=0.4), ("embers", (50, 28), 5, 7)], fx_pal=EMBER[:3]), 70),
                 (dict(dx=1, hand=(36, 28), ang=40, off=(30, 27), heat=(0, 40), flow=0.4, flutter=6,
                       fx=[("embers", (48, 30), 4, 8)]), 170)], art=True)

ARTS = [("art_crescent", art_crescent), ("art_bloodstep", art_bloodstep), ("art_stormleap", art_stormleap),
        ("art_warcry", art_warcry), ("art_moonwave", art_moonwave), ("art_cinderblade", art_cinderblade)]

MOVES = [("dg_1", dg_1), ("dg_2", dg_2), ("dg_3", dg_3), ("dg_4", dg_4), ("dg_heavy", dg_heavy),
         ("gs_1", gs_1), ("gs_2", gs_2), ("gs_3", gs_3), ("gs_heavy", gs_heavy),
         ("sp_1", sp_1), ("sp_2", sp_2), ("sp_3", sp_3), ("sp_heavy", sp_heavy),
         ("kt_1", kt_1), ("kt_2", kt_2), ("kt_3", kt_3), ("kt_heavy", kt_heavy)]
MOVE_CLASS = {"dg": ("dagger",), "gs": ("greatsword", "maul"), "sp": ("spear",), "kt": ("katana",)}
# active windows (frame indices within the tag), incl. the v1/v3 sword tags for completeness
ACTIVE = {"attack1": (2, 3), "attack2": (2, 3), "attack3": (2, 3), "heavy": (4, 5), "attack_up": (2, 3),
          "attack_down": (1, 3), "air_attack": (2, 3),
          "dg_1": (2, 2), "dg_2": (2, 2), "dg_3": (2, 2), "dg_4": (2, 4), "dg_heavy": (4, 5),
          "gs_1": (5, 6), "gs_2": (4, 5), "gs_3": (5, 7), "gs_heavy": (7, 8),
          "sp_1": (2, 3), "sp_2": (2, 3), "sp_3": (3, 5), "sp_heavy": (4, 6),
          "kt_1": (2, 3), "kt_2": (2, 3), "kt_3": (3, 5), "kt_heavy": (6, 7),
          # v5 weapon arts: key frame(s) where the engine fires the technique
          "art_crescent": (4, 4), "art_bloodstep": (2, 4), "art_stormleap": (9, 9), "art_warcry": (3, 3),
          "art_moonwave": (5, 5), "art_cinderblade": (6, 6)}

BODY_HIT = {"art_bloodstep"}
FXAT_OVERRIDE = {"art_warcry": (5, -26)}   # roar FX from the visor, not the planted blade

# ---------------------------------------------------------------- v7: traversal techniques
# Appended after frame 308 (the v5 arts). Grappling hook, Gale Cloak glide, ember dash, slam.
# Extra helpers: a streaming / wing-spread cape, a straight reaching arm, a gold root-hook,
# ember specks, and a row-shear ("lean") applied to a whole posed frame (body + weapon cel).
import random as _random

HOOK = [".gGf.",     # gold root-hook pointing right (row 2 = the shank through the fist):
        "G...f",     # two barbed prongs curling back toward the hand
        "GGGGf",
        "g...G",
        ".gGg."]

def draw_hook(g, hand, orient):
    """Stamp the gold root-hook in the fist at `hand`: orient 'r' (thrown forward) / 'd' (dangling)."""
    hg = blank()
    hx, hy = int(round(hand[0])), int(round(hand[1]))
    for r, row in enumerate(HOOK):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            if orient == 'r':
                put(hg, hx + 2 + c, hy - 2 + r, ch)
            else:
                put(hg, hx - 1 + r, hy + 2 + c, ch)
    outline(hg)
    for y in range(H):
        for x in range(W):
            if hg[y][x] and (g[y][x] is None or hg[y][x] != 'K'):
                g[y][x] = hg[y][x]
    return g

def draw_reach(shoulder, hand, ramp=('4', '3', '2'), bend=1.0):
    """A (near-)straight arm of any length: hanging from / flinging the hook."""
    g = blank()
    (sx, sy), (hx, hy) = shoulder, hand
    L = math.hypot(hx - sx, hy - sy) or 1
    ex, ey = (sx + hx) / 2 + (hy - sy) / L * bend, (sy + hy) / 2 - (hx - sx) / L * bend
    limb(g, [shoulder, (ex, ey), hand], 3.2, *ramp)
    ix, iy = int(round(hx)), int(round(hy))
    for a, b in ((0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (1, -1)):
        put(g, ix + a, iy + b, '3')
    put(g, ix, iy - 1, '5')
    return outline(g)

def draw_streamer(root, ang, length, w0, w1, phase, amp=1.2, k=0.55):
    """Cape streaming from `root` along `ang` (deg): rippling band, tattered hem, lit upper-left edge."""
    g = blank()
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    lit_side = 1 if (px * -1 + py * -1) > 0 else -1       # +v faces the upper-left light?
    tat = [0, 2, 1, 3, 0, 1, 3, 2]
    for y in range(H):
        for x in range(W):
            rx, ry = x + 0.5 - root[0], y + 0.5 - root[1]
            u, v = rx * dx + ry * dy, rx * px + ry * py
            if u < -1.5 or u > length:
                continue
            c = amp * math.sin(u * k + phase) * min(1.0, max(0.0, u) / 6)
            hw = (w0 + (w1 - w0) * max(0.0, u) / length) / 2
            vv = v - c
            if abs(vv) > hw:
                continue
            if u > length - tat[(int(vv + hw) + int(phase * 2)) % len(tat)] * 1.3:
                continue
            slope = math.cos(u * k + phase)
            ch = 'o' if slope > 0.35 else ('n' if slope > -0.35 else 'm')
            if vv * lit_side > hw - 1.2:
                ch = 'p' if slope > 0 else 'o'
            elif vv * lit_side < -hw + 1.0:
                ch = 'm'
            if u < 2:
                ch = 'm'
            g[y][x] = ch
    return outline(g, 'k')

def draw_wing(root, a_lo, a_hi, rx, ry, phase, ribs=4, dark=False):
    """Gale Cloak: the cape spread as a scalloped wing fanning from the shoulders (a_lo = lower
    trailing edge, a_hi = upper leading edge; degrees, 180 = back, 270 = up)."""
    g = blank()
    for y in range(H):
        for x in range(W):
            ex, ey = x + 0.5 - root[0], y + 0.5 - root[1]
            ang = math.degrees(math.atan2(ey, ex)) % 360
            if not a_lo <= ang <= a_hi:
                continue
            t = (ang - a_lo) / (a_hi - a_lo)                # 0 lower edge .. 1 leading edge
            r = math.hypot(ex / rx, ey / ry)
            tr = t * ribs + phase * 0.25
            fr = tr - math.floor(tr)
            edge = (0.66 + 0.34 * t ** 0.7) * (1.0 - 0.13 * math.sin(math.pi * fr) ** 2)
            if r > edge:
                continue
            if t > 0.9 or (t > 0.84 and r > 0.5):
                ch = 'p' if r > 0.3 else 'o'                  # lit leading edge
            elif fr < 0.1 or fr > 0.93:
                ch = 'm'                                       # rib fold
            elif fr < 0.45:
                ch = 'o' if t > 0.45 else 'n'                  # upper side of each panel catches light
            else:
                ch = 'n' if (r < edge - 0.12 or t > 0.5) else 'm'
            if r < 0.22:
                ch = 'm'
            if dark:
                ch = {'p': 'o', 'o': 'n', 'n': 'm', 'm': 'm'}[ch]
            g[y][x] = ch
    # opening (erode then regrow inside the original): no 1px slivers at the tips
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    core = {(x, y) for y in range(H) for x in range(W) if g[y][x]
            and all(0 <= x + a < W and 0 <= y + b < H and g[y + b][x + a] for a, b in N4)}
    keep = core | {(x + a, y + b) for x, y in core for a, b in N4}
    for y in range(H):
        for x in range(W):
            if g[y][x] and (x, y) not in keep:
                g[y][x] = None
    return outline(g, 'k')

EMB_T = ((255, 240, 190), (255, 160, 60), (206, 74, 34), (120, 32, 26))

def draw_embers(g, box, n, seed, streak=2):
    """Scatter n embers peeling off inside box (x0, y0, x1, y1): hot heads, short trails to the left."""
    rnd = _random.Random(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        heat = (x - x0) / max(1, x1 - x0)                    # hotter near the body (right)
        head = EMB_T[0] if heat > 0.75 and i % 2 else (EMB_T[1] if heat > 0.35 else EMB_T[2])
        put(g, x, y, head)
        for j in range(1, streak + (i % 2) + 1):
            put(g, x - j, y + (j // 2) * (1 if i % 3 == 0 else 0), EMB_T[min(3, 1 + j)])
    return g

def item_merge(cels, grid, layer="Item"):
    base = cels.get(layer)
    if base is None:
        cels[layer] = grid
        return cels
    for y in range(H):
        for x in range(W):
            if grid[y][x] is not None and base[y][x] is None:
                base[y][x] = grid[y][x]
    return cels

def _shift(y, k, y0, above_only):
    if above_only and y > y0:
        return 0
    return int(round(k * (y0 - y)))

def shear_grid(g, k, y0, above_only=False):
    out = blank()
    for y in range(H):
        s = _shift(y, k, y0, above_only)
        for x in range(W):
            if g[y][x] is not None and 0 <= x + s < W:
                out[y][x + s] = g[y][x]
    return out

class ShearWpn(RotWpn):
    """Weapon cel of a leaning frame: same row shear as the body."""
    def __init__(self, inner, k, y0, above_only=False):
        self.inner, self.k, self.y0, self.above = inner, k, y0, above_only

    def render(self, kind, dust=True, extras=True):
        src = self.inner.render(kind, dust, extras)
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sp, op = src.load(), out.load()
        for y in range(H):
            s = _shift(y, self.k, self.y0, self.above)
            for x in range(W):
                if sp[x, y][3] and 0 <= x + s < W:
                    op[x + s, y] = sp[x, y]
        return out

def lean(frame, k, y0, above_only=False):
    """Row-shear every layer of a posed frame (k > 0 tips rows above y0 to the right)."""
    cels, ms = frame
    out = {}
    for n, c in cels.items():
        if isinstance(c, (Wpn, RotWpn)):
            out[n] = ShearWpn(c, k, y0, above_only)
        elif isinstance(c, Image.Image):
            out[n] = c
        else:
            out[n] = shear_grid(c, k, y0, above_only)
    return (out, ms)

def hook_throw():  # wind the hook back low, fling the free arm forward-up, release (engine draws the line)
    low = dict(ang=150, slen=16)
    fr = mseq([(dict(dx=-1, dy=1, off=(18, 21), hand=(32, 31), footB=(OX + 7, 39), flow=0.3, **low), 80),
               (dict(dx=1, hand=(33, 31), footF=(FF[0] + 1, 39), flow=0.8, flutter=1, **low), 50),
               (dict(dx=2, hand=(34, 31), footF=(FF[0] + 2, 39), flow=1.0, flutter=2, **low), 90),
               (dict(dx=1, hand=(33, 30), footF=(FF[0] + 1, 39), flow=0.6, flutter=3, **low), 120)])
    draw_hook(fr[0][0]["OffArm"], (17, 22), 'd')           # (off + dx/dy)
    for (cels, _), bx, reach in zip(fr[1:], (1, 2, 1), ((35, 15), (39, 13), (38, 16))):
        cels["Item"] = draw_reach((OX + 12 + bx, OY + 14), reach, bend=-1.0)   # flung arm, over the body
    draw_hook(fr[1][0]["Item"], (35, 15), 'r')
    return fr

HANG = (30, 6)   # hook_swing: the gripping fist (the engine attaches the line here)

def hook_swing():  # hanging from the raised free arm, body angled back, legs trailing together, cape streaming
    out = []
    for i, (fb, ff) in enumerate((((24, 38), (28, 39)), ((25, 39), (29, 39)))):
        bx, by = 3, 0
        p = dict(dx=bx, dy=by, hand=(35, 29), ang=62, slen=15, footB=fb, footF=ff, air=True)
        cels = pose({**dict(footB=FB, footF=FF), **p})
        cels["Cape"] = draw_streamer((OX + 9 + bx, OY + 11 + by), 150 + i * 6, 19, 5, 9, 1.2 + i * 1.6)
        # the far arm goes straight up behind the helmet: fist + forearm show above the head
        cels["OffArm"] = draw_reach((OX + 11 + bx, OY + 14 + by), (HANG[0] + 2, HANG[1]), bend=0.4)
        out.append(lean((cels, 150), 0.3, HANG[1]))
    return out

def glide():  # Gale Cloak: cape spread wide like wings, arms slightly out, legs trailing
    out = []
    for i, (alo, ahi, rx, ry, dy) in enumerate(((170, 240, 25, 17, 0), (172, 242, 25, 18, -1),
                                               (175, 243, 24, 18, -1), (172, 241, 25, 17, 0))):
        p = dict(dx=1, dy=-2 + dy, head_dx=1, hand=(37, 28), ang=165, slen=16, off=(19, 24),
                 footB=(OX + 3, 35 + dy), footF=(OX + 7, 37 + dy), air=True)
        cels = pose({**dict(footB=FB, footF=FF), **p})
        root = (OX + 10, OY + 10 + dy)
        far = draw_wing((root[0] + 3, root[1] - 1), alo + 30, ahi + 22, rx * 0.72, ry * 0.9, i + 2, ribs=2, dark=True)
        near = draw_wing(root, alo, ahi, rx, ry, i, ribs=3)
        cels["Cape"] = item_merge({"c": near}, far, "c")["c"]
        out.append((cels, 110))
    return out

def ember_dash():  # launch low -> body stretched forward, cape flat behind, embers peeling -> recover
    base = dict(hand=(28, 31), ang=172, slen=16, off=(40, 25))
    rows = [(dict(dx=0, dy=3, head_dx=1, footB=(OX + 5, 39), footF=(OX + 21, 39), flow=0.8), 50, 0.10, 0),
            (dict(dx=2, dy=5, head_dx=2, head_dy=1, footB=(OX + 1, 37), footF=(OX + 24, 39), air=True), 60, 0.28, 14),
            (dict(dx=2, dy=5, head_dx=2, head_dy=1, footB=(OX + 2, 38), footF=(OX + 24, 39), air=True), 60, 0.28, 12),
            (dict(dx=1, dy=3, head_dx=1, footB=(OX + 5, 39), footF=(OX + 22, 39), flow=0.6), 90, 0.12, 5)]
    out = []
    for i, (p, ms, k, ne) in enumerate(rows):
        cels = mseq([({**base, **p}, ms)])[0][0]
        bx, by = p["dx"], p["dy"]
        if i in (1, 2):
            cels["Cape"] = draw_streamer((OX + 9 + bx, OY + 11 + by), 182 - i, 22, 5, 7, i * 1.9, amp=0.8, k=0.7)
        if ne:
            eg = blank()
            draw_embers(eg, (2 + 3 * i, OY + 8 + by, OX + 8 + bx, OY + 24 + by), ne, 40 + i)
            item_merge(cels, eg)
        out.append(lean((cels, ms), k, OY + 22 + by, above_only=True))
    return out

def slam_dive():  # plunging straight down: tucked, blade two-handed point-down under the feet, cape up
    out = []
    for i in range(2):
        fr = mseq([(dict(dy=-4, head_dy=1, hand=(33, 27), ang=90, slen=14, two=True, grip=3.5,
                         footB=(OX + 9 + i, 33), footF=(OX + 17, 33 - i), air=True), 60)])[0]
        cels = fr[0]
        cels["Cape"] = draw_streamer((OX + 9, OY + 11 - 4), 250 + 5 * i, 19, 5, 10, 0.8 + i * 1.7, amp=1.2, k=0.7)
        out.append((cels, 60))
    return out

def slam_land():  # impact: crouched, blade driven into the floor two-handed -> hold -> pull free and rise
    def planted(dx, dy, hy, **k):
        return dict(dx=dx, dy=dy, hand=(39, hy), ang=90, two=True, grip=3.0, planted=(39 + dx, hy + dy), **k)
    fr = mseq([(planted(1, 5, 26, head_dy=1, footB=(OX + 1, 39), footF=(FF[0] + 4, 39), flow=1.6, flutter=2), 90),
                 (planted(1, 5, 26, head_dy=1, footB=(OX + 1, 39), footF=(FF[0] + 4, 39), flow=0.9, flutter=3), 170),
                 (planted(1, 4, 26, head_dy=1, footB=(OX + 2, 39), footF=(FF[0] + 4, 39), flow=0.4, flutter=4), 150),
                 (dict(dx=1, dy=3, hand=(36, 25), ang=-80, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.3), 110),
                 (dict(hand=(35, 27), ang=-50, flow=0.2), 120)])
    # the impact flings the cape up behind the shoulders, then it falls back
    fr[0][0]["Cape"] = draw_streamer((OX + 9 + 1, OY + 11 + 5), 232, 15, 5, 8, 0.5, amp=1.0, k=0.8)
    fr[1][0]["Cape"] = draw_streamer((OX + 9 + 1, OY + 11 + 5), 204, 15, 5, 9, 2.1, amp=1.0, k=0.7)
    return fr

TRAV = [("hook_throw", hook_throw), ("hook_swing", hook_swing), ("glide", glide), ("ember_dash", ember_dash),
        ("slam_dive", slam_dive), ("slam_land", slam_land)]

def techniques_preview(raw, tags, body_comp, wpn, prev_dir, scale=3):
    """art/previews/techniques.png: each traversal tag as a row (longsword composited), labelled."""
    from PIL import ImageDraw
    names = [n for n, _ in TRAV]
    rows, labels = [], []
    for t, a, b in tags:
        if t in names:
            rows.append([over(body_comp[i], wpn["longsword"][i]) for i in range(a, b + 1)])
            labels.append((t, [raw[i][1] for i in range(a, b + 1)]))
    sh = grid_sheet(rows)
    lw = 34
    out = Image.new("RGBA", (sh.width + lw, sh.height), (92, 92, 100, 255))
    out.alpha_composite(sh, (lw, 0))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    for ry, (name, mss) in enumerate(labels):
        y = ry * (H + 1) * scale
        d.text((4, y + 4), name, fill=(255, 255, 255, 255))
        d.text((4, y + 18), f"{sum(mss)}ms", fill=(200, 200, 210, 255))
        for i, ms in enumerate(mss):
            d.text(((lw + i * (W + 1)) * scale + 3, y + 3), f"{i}:{ms}", fill=(255, 220, 150, 255))
    out.save(os.path.join(prev_dir, "techniques.png"))

# ================================================================ v8: expansion weapons (17) + new classes
# Staff (held in the middle, both ends strike), sword & shield (shield rides the off arm), twin blades
# (the far hand holds a second blade) and the mirror weapon. Class extras (shield, off-hand blade) are
# drawn by render_extras() on the weapon overlay only for the kinds that carry them, so every older
# weapon sheet renders exactly as before.
STAFF_BACK = {}        # staff kind -> haft length behind the front hand
RASTER_POST = {}       # kind -> fn(pix, hand, dir, L): screen-space extras in _raster
SHIELD_KINDS = ("knight_shield", "twinborne", "overseer_bulwark")
TWIN_KINDS = ("twinfangs",)
EXTRA_KINDS = set(SHIELD_KINDS) | set(TWIN_KINDS)


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---- sword: Frostbrand (Hoarfrost) -- pale ice-steel, frozen fuller, rime crystals growing off the edge
def shp_frostbrand(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    iu = int(math.floor(u))
    if 2.2 <= u <= tip:
        hw = _taper(u, tip, 1.35, 4.0)
        if abs(v) <= hw:
            if abs(v) < 0.5 and 3.5 <= u <= tip - 3.0:
                return (236, 250, 255) if iu % 5 else (150, 206, 244)
            if abs(v) > hw - 0.7 and iu % 4 == 1 and u < tip - 2.5:
                return (250, 254, 255)
            return _band(vl, hw, (196, 228, 250), (112, 160, 212), (46, 72, 122), 0.25)
        if 3.0 <= u <= tip - 5 and hw < abs(v) <= hw + 1.0 and iu % 5 == 2 and vl > 0:
            return (170, 214, 246)
    if 0.9 <= u < 2.2 and abs(v) <= 3.4:
        if abs(v) > 2.5:
            return (236, 248, 255) if vl > 0 else (150, 206, 244)
        return (112, 160, 212) if u < 1.6 else (46, 72, 122)
    if -3.6 <= u < 0.9 and abs(v) <= 0.75:
        return (70, 96, 140) if iu % 2 else (32, 42, 70)
    if -5.0 <= u < -3.6 and abs(v) <= 1.25:
        return (214, 240, 255) if abs(v) < 0.5 else ((126, 180, 230) if vl > 0 else (52, 80, 130))
    return None


# ---- dagger: Pagecutter (Archives) -- a scribe's paper-knife, bone-pale blade dipped in violet ink
def shp_pagecutter(u, v, s, L):
    tip = L + 1.5
    dv = v - 0.4
    vl = dv * s
    if 1.8 <= u <= tip:
        hw = _taper(u, tip, 0.72, 3.5)
        if abs(dv) <= hw:
            if u > tip - 3.4:
                return (150, 104, 224) if vl > 0 else (62, 34, 108)
            if u > tip - 4.2 and vl < 0:
                return (96, 60, 150)            # ink wicking up the blade
            return _band(vl, hw, (238, 232, 216), (176, 166, 152), (84, 76, 84), 0.2)
    if 0.8 <= u < 1.8 and abs(dv) <= 1.6:
        return (214, 170, 86) if vl > 0 else (120, 84, 34)
    if -3.2 <= u < 0.8 and abs(dv) <= 0.72:
        if int(math.floor(u)) == -2:
            return (214, 170, 86)
        return (46, 36, 52) if vl > 0 else (20, 16, 26)
    if -4.4 <= u < -3.2 and abs(dv) <= 1.15:
        return (236, 196, 110) if vl > 0 else (120, 84, 34)
    return None


# ---- great: the Colossus's greathammer -- basalt head split by glowing magma veins
MAGMA = ((255, 240, 170), (255, 158, 48), (206, 70, 26), (110, 30, 20))
def shp_colossus_hammer(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 7.5
    if h0 <= u <= tip and abs(v) <= 5.4:
        if abs(v) > 4.5 and (u < h0 + 1.0 or u > tip - 1.0):
            return None
        du = u - h0
        ph = abs(((v * 0.8 + du * 1.6 + 0.4) % 4.8) - 2.4)
        if 0.9 < du < 6.8 and abs(v) < 4.6:
            if ph < 0.42:
                return MAGMA[0] if abs(v) < 2.2 else MAGMA[1]
            if ph < 0.95:
                return MAGMA[2] if (int(u * 2) + int(v * 2)) % 3 else MAGMA[1]
        if u > tip - 1.0:
            return (40, 30, 34)
        if abs(v) > 4.5:
            return (104, 86, 84) if vl > 0 else (48, 38, 42)
        return (84, 70, 72) if vl > 0.8 else ((60, 48, 52) if vl > -1.8 else (36, 28, 32))
    if -3.0 <= u < h0 and abs(v - 0.5) <= 0.8:
        if u > h0 - 2.2:
            return (112, 94, 88)
        if abs(v - 0.5) < 0.35 and int(math.floor(u)) % 3 == 0:
            return MAGMA[1]
        return (72, 60, 64) if (v - 0.5) * s > 0 else (38, 30, 36)
    if -4.4 <= u < -3.0 and abs(v - 0.5) <= 1.3:
        return MAGMA[1] if abs(v - 0.5) < 0.5 else ((112, 94, 88) if (v - 0.5) * s > 0 else (48, 38, 42))
    return None


# ---- great: Glacier Maul (Ice Golem Warden) -- a jagged block of blue glacier ice on a rimed haft
def shp_glacier_maul(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 7.0
    if h0 <= u <= tip:
        du = u - h0
        hw = 4.8 - 0.9 * abs(math.sin(du * 1.9 + (0.9 if v > 0 else 0.0)))
        if du < 0.8 or u > tip - 0.8:
            hw -= 1.0
        if abs(v) <= hw:
            f = (du * 1.3 - v * 0.8) % 3.4
            if abs(v) > hw - 0.8:
                return (236, 250, 255) if vl > 0 else (126, 184, 230)
            if f < 0.55:
                return (220, 244, 255)
            return (150, 204, 240) if vl > 0.8 else ((96, 156, 214) if vl > -1.2 else (52, 94, 160))
    if -2.8 <= u < h0 and abs(v - 0.5) <= 0.75:
        iu = int(math.floor(u))
        if u > h0 - 1.6 or iu % 5 == 0:
            return (214, 240, 255) if (v - 0.5) * s > 0 else (126, 180, 230)
        return (84, 100, 130) if (v - 0.5) * s > 0 else (40, 48, 70)
    if -4.0 <= u < -2.8 and abs(v - 0.5) <= 1.25:
        return (150, 204, 240) if (v - 0.5) * s > 0 else (52, 94, 160)
    return None


# ---- great: Bell-Ringer's hammer -- a cracked bronze bell for a head, mouth to the foe
BRONZE = ((240, 196, 104), (190, 136, 58), (120, 78, 34), (64, 40, 22))
def shp_bell_hammer(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    h0 = tip - 8.0
    if h0 <= u <= tip:
        t = (u - h0) / 8.0
        hw = 1.9 + 3.3 * t ** 1.7
        if u > tip - 1.2:
            hw += 0.5                           # flared lip
        if abs(v) <= hw:
            if u > tip - 0.9 and abs(v) < hw - 1.3:
                return (26, 16, 14)             # dark mouth
            if abs(v) > hw - 0.8 or u > tip - 1.2:
                return BRONZE[0] if vl > 0 else BRONZE[2]
            if ((int(u * 1.5) * 7 + int(v * 1.2) * 3) % 11) == 0 and vl < 1:
                return (92, 150, 120)           # verdigris
            if abs(u - (tip - 3.5)) < 0.45:
                return BRONZE[2]                # sound-bow ring
            return BRONZE[0] if vl > 1.2 else (BRONZE[1] if vl > -1.0 else BRONZE[2])
    if h0 - 1.8 <= u < h0 and 0.55 <= abs(v) <= 1.5:
        return BRONZE[1] if vl > 0 else BRONZE[3]  # crown loop
    if -3.0 <= u < h0 - 1.0 and abs(v - 0.5) <= 0.75:
        iu = int(math.floor(u))
        if iu % 5 == 1:
            return BRONZE[1]
        return (98, 70, 48) if (v - 0.5) * s > 0 else (54, 36, 26)
    if -4.2 <= u < -3.0 and abs(v - 0.5) <= 1.25:
        return BRONZE[0] if (v - 0.5) * s > 0 else BRONZE[2]
    return None


# ---- great: Forge Cleaver (Burning Deep) -- a riveted slab of forge iron, its edge still white-hot
def shp_forge_cleaver(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    sp, ed = -1.8, 2.9
    if 2.6 <= u <= tip:
        if u > tip - (v - sp) * 0.55:
            return None                          # slanted, hacked-off point
        if sp <= v <= ed:
            if math.hypot(u - (tip - 4.2), v - 0.4) < 0.95:
                return None                      # hanging hole
            e = ed - v
            if e < 0.95:
                t = min(1.0, (u - 2.6) / max(1.0, tip - 2.6))
                return _mix(MAGMA[2], MAGMA[0], t) if e < 0.5 else _mix((120, 40, 26), MAGMA[1], t)
            if v < sp + 0.8:
                return (112, 104, 108) if vl > 0 else (40, 34, 40)
            iu = int(math.floor(u))
            if iu % 6 == 3 and 0.0 <= v <= 0.9:
                return (156, 146, 146)           # rivets
            return (86, 78, 82) if vl > 0.6 else ((60, 52, 58) if vl > -1.0 else (38, 32, 38))
    if 0.8 <= u < 2.6 and abs(v) <= 3.6:
        return (112, 104, 108) if u < 1.7 else (48, 42, 48)
    if -5.0 <= u < 0.8 and abs(v) <= 0.75:
        return (104, 64, 40) if int(math.floor(u)) % 2 else (54, 32, 22)
    if -6.4 <= u < -5.0 and abs(v) <= 1.3:
        return (112, 104, 108) if vl > 0 else (40, 34, 40)
    return None


# ---- spear: Stormfang (Cindervane) -- the drake's fang on a blued haft, a lightning vein at its heart
STORM = ((244, 252, 255), (170, 214, 255), (90, 140, 230), (40, 60, 120))
def shp_stormfang(u, v, s, L, back=SPEAR_BACK):
    vl = v * s
    tip = L + 1.5
    BL = 9.0
    h0 = tip - BL
    if h0 <= u <= tip:
        t = (u - h0) / BL
        c = -0.5 * t * t                         # the fang hooks gently back
        hw = max(0.3, 2.0 * math.sin(math.pi * min(1.0, t * 1.2) ** 0.8) if t < 0.8 else 2.0 * (1 - t) / 0.2 * 0.8 + 0.2)
        dv = v - c
        if abs(dv) <= hw:
            if abs(dv - 0.35 * math.sin(u * 2.4)) < 0.42 and t < 0.85:
                return STORM[0] if int(u * 2) % 3 else STORM[1]
            if abs(dv) > hw - 0.7:
                return (186, 204, 236) if dv * s > 0 else (100, 110, 150)
            return (64, 72, 102) if dv * s > 0 else (32, 36, 56)
        if 0.05 < t < 0.3 and hw < -dv <= hw + 1.5 and -dv - hw < (0.3 - t) * 8:
            return (100, 110, 150) if vl > 0 else (32, 36, 56)   # back barb
    if h0 - 1.6 <= u < h0 and abs(v) <= 1.0:
        return STORM[1] if vl > 0 else STORM[2]
    if -back <= u < h0 - 1.6 and abs(v) <= 0.55:
        iu = int(math.floor(u))
        if iu in (-3, 4):
            return (190, 200, 220)
        return (70, 84, 120) if vl >= 0 else (36, 42, 70)
    if -back - 1.4 <= u < -back and abs(v) <= 0.85:
        return STORM[2]
    return None


# ---- katana: Stormvein (Spire) -- blued steel with a lightning vein forked down the blade
def shp_stormvein(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    c = 0.5 - 0.0062 * max(0.0, u - 2) ** 2
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 0.85, 3.0)
        dv = v - c
        if abs(dv) <= hw:
            zig = 0.35 * (1 if int(u * 0.9) % 2 else -1) * ((u * 0.9) % 1.0 - 0.5) * 2
            if abs(dv - zig * 0.5) < 0.3 and 3.0 < u < tip - 1.5:
                return STORM[0]
            if dv > 0.05:
                return (190, 224, 255) if u > 3 else (130, 170, 220)
            return (54, 62, 96)
    if 1.0 <= u < 2.0 and abs(v - 0.5) <= 1.6:
        return (200, 208, 224) if vl > 0 else (90, 96, 118)
    if -5.0 <= u < 1.0 and abs(v - 0.5) <= 0.75:
        return (210, 220, 240) if (int(math.floor(u)) + (v > 0.5)) % 2 else (30, 38, 70)
    if -6.0 <= u < -5.0 and abs(v - 0.5) <= 0.8:
        return (200, 208, 224)
    return None


# ---- staffs: gripped in the middle (front hand at u=0, far hand ~5 px behind), both ends strike
def shp_quarterstaff(u, v, s, L, back=13.0):
    vl = v * s
    tip = L + 1.5
    if -back <= u <= tip:
        if (tip - 1.7 <= u <= tip - 1.0 or -back + 1.0 <= u <= -back + 1.7) and abs(v) <= 1.05:
            return (126, 126, 140) if vl > 0 else (64, 64, 78)          # iron collars
        if abs(v) <= 0.75:
            if u > tip - 1.7 or u < -back + 1.7:
                return (150, 150, 164) if vl > 0 else (70, 70, 84)      # iron ferrules
            iu = int(math.floor(u))
            if -2 <= iu <= 1 or -8 <= iu <= -6:
                return (118, 76, 48) if (iu + (v > 0)) % 2 else (64, 40, 28)   # leather wraps
            if iu % 7 == 3:
                return (132, 96, 60) if vl > 0 else (92, 64, 40)
            return (176, 134, 88) if vl > 0 else (120, 86, 54)
    return None


PILGRIM = ((238, 230, 208), (196, 182, 152), (128, 116, 96))
def shp_windstaff(u, v, s, L, back=12.0):
    """Oswin's pilgrim staff: bleached wood, a crook curling back, a prayer-cloth and red beads."""
    vl = v * s
    tip = L + 1.5
    cu, cv, R = tip - 2.6, -1.5, 2.3              # the crook
    d = math.hypot(u - cu, v - cv)
    if abs(d - R) <= 0.72 and u > tip - 5.4:
        a = math.degrees(math.atan2(v - cv, u - cu))
        if not (-200 < a < -110 or 100 < a < 190):   # the curl stays open toward the haft
            return PILGRIM[0] if (v - cv) * s > 0 or u > cu + 1 else PILGRIM[2]
    if -back <= u <= tip - 2.6 and abs(v) <= 0.72:
        if tip - 8.2 <= u <= tip - 5.2:
            return (228, 236, 240) if (int(u * 2) % 2) else (160, 176, 186)   # wind-cloth wrap
        if u < -back + 1.3:
            return (84, 90, 118)
        iu = int(math.floor(u))
        if iu % 6 == 2:
            return PILGRIM[2]
        return PILGRIM[1] if vl > 0 else PILGRIM[2]
    for bu in (tip - 9.2, tip - 10.6, tip - 12.0):   # prayer beads strung down the haft
        if math.hypot(u - bu, v - 1.35) <= 0.72:
            return (196, 70, 58) if vl > 0 else (120, 38, 36)
    return None


def shp_inkquill(u, v, s, L, back=12.0):
    """The Unwritten's quill-staff: a gold nib weeping violet ink; a feather plume at the butt."""
    vl = v * s
    tip = L + 1.5
    h0 = tip - 6.5
    if h0 <= u <= tip:
        t = (tip - u) / 6.5
        hw = 2.1 * t ** 0.75
        if abs(v) <= hw + 0.1:
            if abs(math.hypot(u - (tip - 4.2), v)) < 0.62:
                return (206, 160, 255)           # breather hole, glowing
            if abs(v) < 0.34 and u > tip - 4.2:
                return (40, 18, 62)              # the slit
            return _band(vl, max(0.5, hw), (255, 222, 132), (214, 156, 62), (124, 82, 32), 0.2)
    if h0 - 1.3 <= u < h0 and abs(v) <= 1.35:
        return (196, 150, 250) if vl > 0 else (110, 60, 176)          # violet collar
    if -back + 6.5 <= u < h0 - 1.3 and abs(v) <= 0.72:
        iu = int(math.floor(u))
        if iu % 4 == 0 and abs(v) < 0.5:
            return (232, 184, 84)               # gold glyph ticks
        return (72, 48, 100) if vl > 0 else (32, 20, 50)
    if -back <= u < -back + 6.5:                # feather plume
        t = (u + back) / 6.5
        hw = 2.4 * math.sin(math.pi * min(1.0, 0.15 + t * 0.85))
        if abs(v) < 0.35:
            return (232, 220, 250)              # rachis
        if -0.4 <= v * 1.0 <= hw and v > 0 or (v < 0 and -v <= hw * 0.55):
            barb = (int((u + back) * 2 + abs(v) * 1.5) % 3 == 0)
            if abs(v) > hw - 0.7 or (v < 0 and -v > hw * 0.55 - 0.7):
                return (212, 196, 244)
            return (120, 90, 176) if barb else (78, 54, 124)
    return None


def shp_lantern_staff(u, v, s, L, back=12.0):
    """The Head Librarian's staff: dark oak, an iron hook-finial; the lantern hangs from it (RASTER_POST)."""
    vl = v * s
    tip = L + 1.5
    if tip - 3.0 <= u <= tip and abs(v) <= 0.72:
        return (130, 130, 146) if vl > 0 else (60, 60, 74)
    if tip - 3.0 <= u <= tip - 1.8 and abs(v) <= 1.6:
        return (130, 130, 146) if vl > 0 else (60, 60, 74)           # finial crossbar
    if -back <= u < tip - 3.0 and abs(v) <= 0.72:
        iu = int(math.floor(u))
        if u < -back + 1.3:
            return (60, 60, 74)
        if iu % 5 == 0:
            return (180, 140, 70)
        return (100, 70, 52) if vl > 0 else (56, 38, 30)
    return None


def _post_lantern(pix, hand, d, L):
    hx, hy = hand
    ex, ey = hx + d[0] * (L - 0.3), hy + d[1] * (L - 0.3)    # hook point near the finial
    x0, y0 = int(round(ex)), int(round(ey))
    pix[(x0, y0 + 1)] = (60, 60, 74)                       # chain
    pix[(x0, y0 + 2)] = (130, 130, 146)
    for yy in range(3, 8):                                 # 3x5 lantern, glass glowing amber
        for xx in (-1, 0, 1):
            if yy in (3, 7):
                c = (84, 70, 60) if xx else (130, 110, 80)
            elif xx == 0:
                c = (255, 246, 200) if yy in (4, 5) else (255, 196, 92)
            else:
                c = (255, 170, 70) if yy < 6 else (200, 110, 40)
            pix[(x0 + xx, y0 + yy)] = c


RASTER_POST["lantern_staff"] = _post_lantern


# ---- sword & shield: the blades (the shields are drawn by draw_shield)
def shp_knight_shield(u, v, s, L):
    """Knight's arming sword: plain steel, a gold guard, an oxblood grip."""
    vl = v * s
    tip = L + 1.5
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 1.1, 3.0)
        if abs(v) <= hw:
            if abs(v) < 0.35 and u < tip - 3:
                return (140, 150, 182)
            return _band(vl, hw, (226, 232, 246), (150, 160, 190), (60, 64, 88), 0.2)
    if 1.0 <= u < 2.0 and abs(v) <= 2.8:
        return (230, 186, 92) if u < 1.5 else (130, 90, 36)
    if -3.4 <= u < 1.0 and abs(v) <= 0.72:
        return (120, 36, 42) if int(math.floor(u)) % 2 else (60, 18, 26)
    if -4.6 <= u < -3.4 and abs(v) <= 1.2:
        return (170, 176, 196) if vl > 0 else (70, 72, 90)
    return None


def shp_twinborne(u, v, s, L):
    """The fire twin's sword: blackened steel whose edge never stopped burning."""
    vl = v * s
    tip = L + 1.5
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 1.25, 3.5)
        if -hw <= v <= hw:
            e = hw - v
            if e < 0.8:
                return MAGMA[0] if u > tip - 4 or int(u) % 3 == 0 else MAGMA[1]
            if e < 1.5 and int(u) % 3 != 1:
                return MAGMA[2]
            return (80, 66, 70) if vl > 0 else (36, 28, 34)
    if 1.0 <= u < 2.0 and abs(v) <= 3.0:
        return (206, 226, 246) if v * s > 0 else (90, 130, 190)     # frost-silver guard
    if -3.6 <= u < 1.0 and abs(v) <= 0.72:
        return (150, 40, 34) if int(math.floor(u)) % 2 else (70, 20, 20)
    if -4.8 <= u < -3.6 and abs(v) <= 1.2:
        return (170, 214, 246) if vl > 0 else (70, 110, 170)
    return None


def shp_overseer_bulwark(u, v, s, L):
    """The Forge Overseer's falchion: short, heavy, widening toward a glowing edge."""
    vl = v * s
    tip = L + 1.5
    if 2.0 <= u <= tip:
        t = (u - 2.0) / max(1.0, tip - 2.0)
        top = 1.0 + 1.4 * t ** 1.2
        if u > tip - 2.5:
            top = min(top, (tip - u) * 1.3 + 0.2)
        if -0.9 <= v <= top:
            if top - v < 0.8:
                return MAGMA[1] if t > 0.4 else MAGMA[2]
            if v < -0.2:
                return (110, 100, 104) if vl > 0 else (38, 32, 38)
            return (82, 74, 78) if vl > 0 else (50, 44, 50)
    if 1.0 <= u < 2.0 and abs(v) <= 2.6:
        return (112, 104, 108) if u < 1.5 else (48, 42, 48)
    if -3.4 <= u < 1.0 and abs(v) <= 0.75:
        return (104, 64, 40) if int(math.floor(u)) % 2 else (54, 32, 22)
    if -4.6 <= u < -3.4 and abs(v) <= 1.25:
        return MAGMA[1] if abs(v) < 0.5 else (70, 60, 64)
    return None


# ---- twin blades: Twinfangs (Hollow Champion) -- two curved bone fangs with bloodied steel edges
def shp_twinfangs(u, v, s, L):
    tip = L + 1.5
    c = 0.45 - 0.011 * max(0.0, u - 2) ** 2
    dv = v - c
    vl = dv * s
    if 1.9 <= u <= tip:
        hw = _taper(u, tip, 1.05, 4.5)
        if -hw <= dv <= hw:
            if dv > hw - 0.7:
                return (224, 232, 246) if u > 4 else (150, 60, 60)
            if int(u) % 4 == 2 and dv < -hw + 0.8:
                return (140, 36, 40)            # blood in the fuller
            return _band(vl, hw, (234, 226, 206), (172, 162, 142), (96, 88, 84), 0.25)
    if 0.8 <= u < 1.9 and abs(v - 0.3) <= 1.7:
        return (120, 110, 104) if vl > 0 else (56, 50, 50)
    if -3.4 <= u < 0.8 and abs(v - 0.3) <= 0.72:
        return (150, 36, 40) if (int(math.floor(u)) + (v > 0.3)) % 2 else (70, 18, 24)
    if -4.4 <= u < -3.4 and abs(v - 0.3) <= 1.1:
        return (234, 226, 206) if vl > 0 else (120, 110, 104)
    return None


# ---- mirror: The First Ember -- obsidian around a white-gold molten core, cracked with fire
def shp_first_ember(u, v, s, L):
    vl = v * s
    tip = L + 1.5
    iu = int(math.floor(u))
    if 2.2 <= u <= tip:
        hw = _taper(u, tip, 1.45, 4.2)
        if abs(v) <= hw:
            t = (u - 2.2) / max(1.0, tip - 2.2)
            if abs(v) < 0.48 and u < tip - 1.0:
                return _mix((255, 250, 226), (255, 186, 80), t)
            if abs(((u * 1.6 + v * 2.2) % 3.3) - 1.65) < 0.3 and abs(v) < hw - 0.4:
                return (255, 132, 40)
            if abs(v) > hw - 0.6 and vl > 0:
                return (126, 100, 104)
            return (44, 32, 38) if vl > 0 else (20, 14, 20)
    if 0.8 <= u < 2.2 and abs(v) <= 3.3:
        if abs(v) < 0.9:
            return (255, 236, 170)
        return (255, 170, 70) if u < 1.5 else (170, 60, 30)
    if 2.2 <= u < 4.6 and 2.2 <= abs(v) <= 3.4 and abs(v) - 2.2 < (4.6 - u) * 0.6:
        return (255, 170, 70) if vl > 0 else (170, 60, 30)                # flame-wing quillons
    if -3.8 <= u < 0.8 and abs(v) <= 0.72:
        return (60, 50, 56) if iu % 2 else (28, 22, 28)
    if -5.2 <= u < -3.8 and abs(v) <= 1.2:
        return (255, 190, 90) if abs(v) < 0.5 else (120, 40, 26)
    return None


for _k, _b in (("quarterstaff", 13.0), ("windstaff", 12.0), ("inkquill", 12.0), ("lantern_staff", 12.0)):
    STAFF_BACK[_k] = _b

WPN.update({
    "frostbrand":       (shp_frostbrand, 19, 5.0, 4.4, "blade"),
    "pagecutter":       (shp_pagecutter, 10, 4.6, 2.4, "blade"),
    "colossus_hammer":  (shp_colossus_hammer, 21, 4.4, 5.8, "maul"),
    "glacier_maul":     (shp_glacier_maul, 20, 4.0, 5.2, "maul"),
    "bell_hammer":      (shp_bell_hammer, 21, 4.2, 6.0, "maul"),
    "forge_cleaver":    (shp_forge_cleaver, 24, 6.4, 4.0, "blade"),
    "stormfang":        (shp_stormfang, 20, SPEAR_BACK + 1.5, 3.8, "blade"),
    "stormvein":        (shp_stormvein, 20, 6.2, 2.5, "blade"),
    "quarterstaff":     (shp_quarterstaff, 17, 13.0 + 0.5, 1.5, "blade"),
    "windstaff":        (shp_windstaff, 17, 12.0 + 0.5, 4.5, "blade"),
    "inkquill":         (shp_inkquill, 18, 12.0 + 0.5, 3.0, "blade"),
    "lantern_staff":    (shp_lantern_staff, 17, 12.0 + 0.5, 2.0, "blade"),
    "knight_shield":    (shp_knight_shield, 16, 4.8, 3.0, "blade"),
    "twinborne":        (shp_twinborne, 17, 5.0, 3.2, "blade"),
    "overseer_bulwark": (shp_overseer_bulwark, 15, 4.8, 3.2, "blade"),
    "twinfangs":        (shp_twinfangs, 13, 4.6, 2.2, "blade"),
    "first_ember":      (shp_first_ember, 19, 5.4, 3.6, "blade"),
})
LONGHAFT["stormfang"] = shp_stormfang
V8_IDS = ["frostbrand", "pagecutter", "colossus_hammer", "glacier_maul", "bell_hammer", "forge_cleaver", "stormfang",
          "stormvein", "quarterstaff", "windstaff", "inkquill", "lantern_staff", "knight_shield", "twinborne",
          "overseer_bulwark", "twinfangs", "first_ember"]
WPN_IDS += V8_IDS
SMEAR.update({
    "frostbrand":       ((236, 250, 255), (140, 200, 246), (60, 104, 170)),
    "pagecutter":       ((236, 226, 255), (160, 120, 230), (80, 50, 140)),
    "colossus_hammer":  MAGMA[:3],
    "glacier_maul":     ((236, 250, 255), (140, 200, 246), (60, 104, 170)),
    "bell_hammer":      ((255, 236, 170), (230, 170, 80), (130, 86, 40)),
    "forge_cleaver":    MAGMA[:3],
    "stormfang":        STORM[:3],
    "stormvein":        STORM[:3],
    "quarterstaff":     ((244, 232, 210), (190, 170, 140), (110, 96, 80)),
    "windstaff":        ((236, 252, 248), (170, 222, 214), (96, 140, 150)),
    "inkquill":         ((236, 214, 255), (170, 120, 240), (88, 50, 150)),
    "lantern_staff":    ((255, 240, 190), (255, 186, 90), (160, 90, 40)),
    "knight_shield":    ((240, 244, 255), (168, 180, 214), (90, 98, 130)),
    "twinborne":        MAGMA[:3],
    "overseer_bulwark": MAGMA[:3],
    "twinfangs":        ((246, 240, 230), (206, 150, 150), (130, 40, 50)),
    "first_ember":      ((255, 250, 226), (255, 186, 80), (190, 70, 30)),
})

# ---- shields
def _heater(lx, ly, w, h):
    t = (ly + h / 2) / h                          # 0 top .. 1 point
    if t < 0 or t > 1:
        return False
    hw = w / 2 if t < 0.45 else w / 2 * (1 - ((t - 0.45) / 0.55) ** 1.6) ** 0.8
    if t < 0.08:
        hw -= (0.08 - t) * 10                     # rounded top corners
    return abs(lx) <= hw


def _round(lx, ly, w, h):
    return (lx / (w / 2)) ** 2 + (ly / (h / 2)) ** 2 <= 1.0


def _tower(lx, ly, w, h):
    if abs(lx) > w / 2 or abs(ly) > h / 2:
        return False
    cx, cy = abs(lx) - (w / 2 - 1.3), abs(ly) - (h / 2 - 1.3)
    return not (cx > 0 and cy > 0 and cx * cx + cy * cy > 1.7)


def _em_knight(lx, ly, w, h):                     # a red ember-eye on a dark steel field, gold cross-bar
    r = math.hypot(lx * 0.9, ly + 1.2)
    if r < 1.0:
        return (255, 222, 140)
    if r < 2.0:
        return (230, 176, 80) if lx < 0 else (150, 104, 40)
    if abs(lx) < 0.5 and -h * 0.4 < ly < h * 0.36:
        return (200, 152, 64)
    return None


def _em_twin(lx, ly, w, h):                       # an ember heart frozen in the ice
    r = math.hypot(lx * 1.2, ly)
    if r < 1.0:
        return (255, 236, 170)
    if r < 1.9:
        return (255, 150, 60)
    if abs(abs(lx) - abs(ly) * 0.6) < 0.4 and r < 4.5:
        return (236, 250, 255)                    # frost star
    return None


def _em_overseer(lx, ly, w, h):                   # three furnace slits glowing through black iron
    for sy in (-3.2, 0.0, 3.2):
        if abs(ly - sy) < 0.6 and abs(lx) < w * 0.3:
            return MAGMA[0] if abs(lx) < w * 0.14 else MAGMA[1]
    if (abs(abs(lx) - (w / 2 - 1.6)) < 0.5 and int(ly + 20) % 3 == 0):
        return (150, 140, 140)                    # rivets
    return None


SHIELD = {
    "knight_shield":    dict(shape=_heater, w=10.0, h=13.0, rim=((190, 196, 216), (86, 90, 114)),
                             face=((150, 44, 52), (108, 28, 38), (64, 16, 26)), emblem=_em_knight),
    "twinborne":        dict(shape=_heater, w=10.0, h=14.0, rim=((236, 250, 255), (120, 176, 226)),
                             face=((150, 204, 240), (96, 150, 206), (52, 88, 150)), emblem=_em_twin),
    "overseer_bulwark": dict(shape=_tower, w=10.0, h=16.0, rim=((124, 114, 116), (56, 48, 52)),
                             face=((74, 64, 70), (52, 44, 50), (34, 28, 34)), emblem=_em_overseer),
}


def draw_shield(kind, c, rot=0.0, sx=0.55):
    """Shield of `kind` centred at c, tilted `rot` degrees (+ = top toward facing), its face
    foreshortened to sx of its width (side view). Returns a grid (outlined)."""
    sp = SHIELD[kind]
    w, h = sp["w"], sp["h"]
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = c
    inside = {}
    R = max(w, h) / 2 + 2
    for y in range(int(cy - R), int(cy + R) + 2):
        for x in range(int(cx - R), int(cx + R) + 2):
            if not (0 <= x < W and 0 <= y < H):
                continue
            rx, ry = x + 0.5 - cx, y + 0.5 - cy
            lx, ly = (rx * ca + ry * sa) / sx, -rx * sa + ry * ca
            if sp["shape"](lx, ly, w, h):
                inside[(x, y)] = (lx, ly)
    g = blank()
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for (x, y), (lx, ly) in inside.items():
        edge = any((x + a2, y + b2) not in inside for a2, b2 in N4)
        if edge:
            g[y][x] = sp["rim"][0] if (lx < 0 or ly < -h * 0.3) else sp["rim"][1]
            continue
        em = sp["emblem"](lx, ly, w, h)
        if em:
            g[y][x] = em
            continue
        lit, mid, dark = sp["face"]
        g[y][x] = lit if lx < -w * 0.2 else (dark if lx > w * 0.24 else mid)
    for (x, y), (lx, ly) in list(inside.items()):   # rim thickness on the far (facing) side
        if (x + 1, y) not in inside and 0 <= x + 1 < W and lx > 0:
            g[y][x + 1] = sp["rim"][1]
    return outline(g)


# ---- the extras renderer (shield / off-hand blade), for EXTRA_KINDS only
def _layers_img(cels, names):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in LAYERS:
        if n in names and n in cels and not isinstance(cels[n], (Wpn, RotWpn)):
            c = cels[n]
            img.alpha_composite(c if isinstance(c, Image.Image) else to_img(c))
    return img


def _masked(img, mask):
    if mask is None:
        return img
    px, mk = img.load(), mask.load()
    for y in range(H):
        for x in range(W):
            if mk[x, y][3]:
                px[x, y] = (0, 0, 0, 0)
    return img


def render_extras(w, kind, dust=True):
    base = w.render_core(kind, dust)
    bx, by = w.bxy
    behind, front, over = blank(), blank(), blank()
    if kind in SHIELD_KINDS:
        if w.shield is not None:
            (scx, scy), rot, sx, layer = w.shield
            dst = behind if layer == "behind" else (over if layer == "over" else front)
        elif w.offp is not None:
            scx, scy, rot, sx, dst = w.offp[0] + 1.5, w.offp[1] + 0.5, 0, 0.62, front
        else:                                     # slung on the back between fights (over the cape, under the body)
            scx, scy, rot, sx, dst = 21.5 + bx, 24.5 + by, -14, 0.78, behind
        sg = draw_shield(kind, (scx, scy), rot, sx)
        for y in range(H):
            for x in range(W):
                if sg[y][x] is not None:
                    dst[y][x] = sg[y][x]
    if kind in TWIN_KINDS:
        if w.offw is not None:
            (ohx, ohy), oang, oslen, ofront = w.offw
        elif w.offp is not None:
            (ohx, ohy), oang, oslen, ofront = w.offp, 128, 16, False
        else:
            (ohx, ohy), oang, oslen, ofront = (25.0 + bx, 30.0 + by), 152, 16, False
        info = {}
        og = draw_weapon(kind, (ohx, ohy), oang, oslen, held=False, info=info)
        fx, fy = int(round(ohx)), int(round(ohy))
        for a2, b2 in OFF_FIST:
            if 0 <= fx + a2 < W and 0 <= fy + b2 < H:
                og[fy + b2][fx + a2] = None
        if w.offfx:
            fxg = move_fx(kind, info, w.offfx, dust)
            for y in range(H):
                for x in range(W):
                    if fxg[y][x] is not None and og[y][x] is None:
                        og[y][x] = fxg[y][x]
        dst = front if ofront else behind
        for y in range(H):
            for x in range(W):
                if og[y][x] is not None:
                    dst[y][x] = og[y][x]
    bimg, fimg, oimg = to_img(behind), to_img(front), to_img(over)
    if w.mirror:
        def _mir(src):
            m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            m.alpha_composite(src.transpose(Image.FLIP_LEFT_RIGHT).crop((7, 0, W, H)), (0, 0))
            return m
        bimg, fimg, oimg = _mir(bimg), _mir(fimg), _mir(oimg)
    cels = w.cels or {}
    body_all = _layers_img(cels, [n for n in LAYERS if n not in ("Sword", "Cape")])   # far hand: in front of the cape
    near = _layers_img(cels, ["Arm", "FrontLeg"])
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(_masked(bimg, body_all))
    out.alpha_composite(_masked(fimg, near))
    out.alpha_composite(_masked(oimg, _layers_img(cels, ["Arm"])))   # swung out over the thigh, still under the sword arm
    out.alpha_composite(base)
    return out

# ---------------------------------------------------------------- v8 staff: quick, flowing, both ends
GRIP_STAFF = 5.0


def st_1():  # snapping jab with the leading end
    return mseq([(dict(dx=-1, dy=1, hand=(30, 26), ang=-4, footB=(OX + 6, 39), flow=0.3), 55),
                 (dict(dx=2, dy=1, hand=(37, 26), ang=-2, footF=(FF[0] + 2, 39), flow=0.9, flutter=1,
                       fx=[("streak", 12)]), 35),
                 (dict(dx=3, dy=1, hand=(39, 26), ang=-1, footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.1, flutter=2,
                       fx=[("streak", 18)]), 45),
                 (dict(dx=2, dy=1, hand=(37, 26), ang=-3, footF=(FF[0] + 2, 39), flow=0.7, flutter=3), 60),
                 (dict(hand=(33, 27), ang=-12, flow=0.3), 80)], grip=GRIP_STAFF)


def st_2():  # twirl: the staff wheels over in front of the body, both ends cutting
    P0 = (35, 24)
    def wheel(prev, ang):
        return [("ring", (P0[0] + 1, P0[1]), 15.5, prev, ang, dict(sq=1.0, w=3.4))]
    return mseq([(dict(dx=-1, dy=1, hand=(31, 24), ang=-150, footB=(OX + 6, 39), flow=0.3), 55),
                 (dict(dx=1, hand=P0, ang=-80, flow=0.7, flutter=1, fx=wheel(-150, -80)), 40),
                 (dict(dx=2, hand=P0, ang=-10, footF=(FF[0] + 2, 39), flow=1.0, flutter=2, fx=wheel(-80, -10)), 40),
                 (dict(dx=2, hand=P0, ang=60, footF=(FF[0] + 2, 39), flow=1.1, flutter=3, fx=wheel(-10, 60)), 40),
                 (dict(dx=2, hand=P0, ang=130, footF=(FF[0] + 2, 39), flow=1.0, flutter=4, fx=wheel(60, 130)), 45),
                 (dict(dx=1, hand=(34, 25), ang=196, flow=0.6, flutter=5, fx=wheel(130, 196)), 60),
                 (dict(hand=(33, 27), ang=-14, flow=0.3), 90)], grip=GRIP_STAFF)


def st_3():  # drop low and sweep the legs
    return mseq([(dict(dx=-1, dy=2, hand=(29, 27), ang=-172, footB=(OX + 6, 39), flow=0.3), 60),
                 (dict(dy=4, head_dy=1, hand=(31, 29), ang=160, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3, flutter=1), 45),
                 (dict(dx=2, dy=5, head_dy=1, hand=(35, 30), ang=10, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=1.0, flutter=2,
                       fx=[("arc", (30, 31), 166, 10, dict(sq=0.3, w=0.5)), ("dust", 44, 2)]), 45),
                 (dict(dx=2, dy=5, head_dy=1, hand=(36, 29), ang=-8, footB=(OX + 6, 39), footF=(FF[0] + 3, 39), flow=0.9, flutter=3,
                       fx=[sw(w=0.4)]), 55),
                 (dict(dx=1, dy=3, hand=(35, 28), ang=-14, footF=(FF[0] + 2, 39), flow=0.5, flutter=4), 90),
                 (dict(dy=1, hand=(33, 27), ang=-16, flow=0.3), 90)], grip=GRIP_STAFF)


def st_4():  # finisher: heave the staff overhead and bring it down like a falling bell-rope
    return mseq([(dict(dy=1, hand=(31, 20), ang=-110, flow=0.3), 70),
                 (dict(dx=-1, hand=(29, 15), ang=-150, footB=(OX + 6, 39), flow=0.3, flutter=1), 90),
                 (dict(dx=-1, dy=-1, head_dx=-1, hand=(29, 14), ang=-166, footB=(OX + 6, 39), flow=0.2, flutter=2), 110),
                 (dict(dx=1, dy=-1, hand=(33, 14), ang=-95, flow=0.7, flutter=3, fx=[sw(w=0.35)]), 40),
                 (dict(dx=3, dy=2, hand=(38, 20), ang=-18, footF=(FF[0] + 3, 39), flow=1.1, flutter=4, fx=[sw(w=0.5)]), 45),
                 (dict(dx=3, dy=4, head_dy=1, hand=(38, 27), ang=36, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.2, flutter=5,
                       fx=[sw(w=0.5), ("dust", 51, 4)]), 55),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=38, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=0.6, flutter=6,
                       fx=[("dust", 52, 2)]), 170),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=6, footF=(FF[0] + 2, 39), flow=0.3), 130)], grip=GRIP_STAFF)


def st_heavy():  # instant full-body spin: the staff sweeps all the way round at the waist, twice
    RG = dict(sq=0.3, w=11.0)
    ring = lambda a0, a1: ("ring", (30, 28), 24, a0, a1, RG)
    return mseq([(dict(dx=-1, dy=2, hand=(29, 28), ang=178, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3), 45),
                 (dict(dx=1, dy=2, hand=(33, 28), ang=2, footF=(FF[0] + 2, 39), flow=1.2, flutter=1, fx=[ring(180, 0)]), 45),
                 (dict(dx=1, dy=2, hand=(33, 28), ang=2, footF=(FF[0] + 2, 39), flow=1.4, flutter=2, mirror=True, behind=True,
                       fx=[ring(180, 0)]), 45),
                 (dict(dx=1, dy=2, hand=(33, 28), ang=-2, footF=(FF[0] + 2, 39), flow=1.5, flutter=3, fx=[ring(180, 0)]), 45),
                 (dict(dx=1, dy=2, hand=(33, 28), ang=2, footF=(FF[0] + 2, 39), flow=1.5, flutter=4, mirror=True, behind=True,
                       fx=[ring(180, 0)]), 45),
                 (dict(dx=2, dy=3, hand=(36, 29), ang=12, footF=(FF[0] + 3, 39), flow=1.2, flutter=5, fx=[ring(170, 12)]), 60),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=-6, footF=(FF[0] + 2, 39), flow=0.6, flutter=6), 110),
                 (dict(hand=(33, 27), ang=-14, flow=0.3), 100)], grip=GRIP_STAFF)


# ---------------------------------------------------------------- v8 sword & shield: short one-handed blows behind a raised shield
def sh_1():  # quick downward diagonal cut
    return mseq([(dict(dx=-1, dy=1, hand=(29, 18), ang=-135, off=(30, 27), flow=0.3, shield=HIP), 50),
                 (dict(hand=(32, 18), ang=-80, off=(32, 25), flow=0.5, flutter=1, fx=[sw(w=0.35)]), 35),
                 (dict(dx=2, hand=(38, 23), ang=-8, off=(30, 26), footF=(FF[0] + 2, 39), flow=0.9, flutter=2, fx=[sw(w=0.55)]), 40),
                 (dict(dx=2, hand=(38, 28), ang=38, off=(30, 26), footF=(FF[0] + 2, 39), flow=0.8, flutter=3, fx=[sw(w=0.5)]), 50),
                 (dict(dx=1, hand=(35, 27), ang=-25, off=(32, 25), flow=0.4), 80)])


def sh_2():  # rising backhand cut
    return mseq([(dict(dy=1, hand=(32, 31), ang=120, off=(30, 27), flow=0.3, shield=HIP), 50),
                 (dict(dy=1, hand=(35, 31), ang=70, off=(33, 25), flow=0.5, flutter=1, fx=[sw(w=0.35)]), 35),
                 (dict(dx=2, hand=(38, 26), ang=-15, off=(30, 26), footF=(FF[0] + 2, 39), flow=0.9, flutter=2, fx=[sw(w=0.55)]), 40),
                 (dict(dx=2, hand=(36, 19), ang=-75, off=(30, 26), footF=(FF[0] + 2, 39), flow=0.8, flutter=3, fx=[sw(w=0.5)]), 50),
                 (dict(dx=1, hand=(34, 22), ang=-60, off=(32, 25), flow=0.4), 80)])


def sh_3():  # finisher: step in and thrust past the shield rim
    return mseq([(dict(dx=-1, hand=(30, 24), ang=-5, off=(31, 26), footB=(OX + 6, 39), flow=0.3, shield=HIP), 70),
                 (dict(dx=-2, dy=1, head_dx=-1, hand=(27, 25), ang=-3, off=(33, 25), footB=(OX + 5, 39), flow=0.2, flutter=1), 70),
                 (dict(dx=3, dy=1, hand=(40, 25), ang=0, off=(30, 26), footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.2, flutter=2,
                       fx=[("streak", 16)]), 45),
                 (dict(dx=3, dy=1, hand=(41, 25), ang=1, off=(30, 26), footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.0, flutter=3,
                       fx=[("streak", 8)]), 70),
                 (dict(dx=2, hand=(38, 26), ang=-10, off=(31, 26), footF=(OX + 22, 39), flow=0.6), 90),
                 (dict(dx=1, hand=(35, 27), ang=-35, off=(32, 25), flow=0.3), 100)])


def sh_heavy():  # shield bash: coil behind the shield, then drive it forward with the whole body
    SB = dict(sx=0.42)
    return mseq([(dict(dx=-1, dy=1, hand=(30, 29), ang=160, off=(30, 26), flow=0.3, shield=HIP), 80),
                 (dict(dx=-2, dy=2, head_dx=-1, hand=(28, 30), ang=166, off=(30, 24), footB=(OX + 5, 39), flow=0.2, flutter=1), 120),
                 (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 30), ang=166, off=(30, 25), footB=(OX + 5, 39), flow=0.2, flutter=2,
                       fx=[("glint", (33, 20))]), 130),
                 (dict(dx=1, dy=2, hand=(29, 29), ang=160, off=(35, 24), footF=(FF[0] + 2, 39), flow=0.9, flutter=3, shield=SB), 40),
                 (dict(dx=4, dy=2, hand=(29, 29), ang=158, off=(39, 24), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.4, flutter=4,
                       shield=SB, fx=[("speed", (21, 19), 4, 12), ("flare", (44, 24), 6)]), 60),
                 (dict(dx=4, dy=2, hand=(29, 29), ang=158, off=(39, 24), footB=(OX + 9, 39), footF=(OX + 26, 39), flow=1.1, flutter=5,
                       shield=SB), 80),
                 (dict(dx=2, dy=1, hand=(31, 29), ang=150, off=(35, 25), footF=(OX + 22, 39), flow=0.6, flutter=6), 120),
                 (dict(hand=(34, 28), ang=-20, off=(32, 25), flow=0.3), 100)])


HIP = dict(abs=(31.5, 26.5), rot=30, sx=0.55, layer="over")   # the shield mid-swing from the back to the arm (first frame of a shield move)
GUARD = dict(dx=-1, dy=2, hand=(31, 21), ang=-12, off=(35, 23), footB=(OX + 6, 39), footF=(FF[0] + 1, 39), shield=dict(sx=0.66))


def sh_guard():  # held guard (loop): shield up, the blade laid over its rim
    return mseq([(dict(flow=0.3, flutter=0, **GUARD), 220),
                 (dict(flow=0.2, flutter=1, **{**GUARD, "dy": 3, "hand": (31, 21), "off": (35, 22)}), 220)])


def sh_block():  # a blow lands on the shield: jolted back, then settles into the guard
    return mseq([(dict(flow=0.9, flutter=2, fx=[("flare", (40, 21), 6)],
                       **{**GUARD, "dx": -4, "head_dx": -1, "off": (34, 22), "shield": dict(sx=0.6, rot=-12)}), 70),
                 (dict(flow=0.6, flutter=3, **{**GUARD, "dx": -2}), 90),
                 (dict(flow=0.3, flutter=0, **GUARD), 80)])


def sh_parry():  # shield parry: a sharp outward punch of the shield (frames 1-2 deflect)
    return mseq([(dict(dx=-1, dy=1, hand=(30, 26), ang=-30, off=(31, 26), flow=0.2, shield=HIP), 35),
                 (dict(dx=1, dy=1, hand=(30, 24), ang=-40, off=(38, 22), footF=(FF[0] + 2, 39), flow=0.8, flutter=1,
                       shield=dict(sx=0.45, rot=10), fx=[("flare", (43, 21), 5)]), 60),
                 (dict(dx=1, dy=1, hand=(30, 24), ang=-40, off=(38, 22), footF=(FF[0] + 2, 39), flow=0.6, flutter=2,
                       shield=dict(sx=0.45, rot=10)), 90),
                 (dict(dy=1, hand=(31, 23), ang=-25, off=(35, 23), flow=0.4, flutter=3), 80),
                 (dict(hand=(34, 27), ang=-30, off=(32, 25), flow=0.3), 80)])


def sh_break():  # guard broken: the shield is knocked wide and the knight reels
    return mseq([(dict(dx=-3, dy=1, head_dx=-1, hand=(31, 31), ang=120, off=(34, 15), flow=0.1,
                       shield=dict(rot=-35, sx=0.6), fx=[("flare", (37, 17), 6)]), 90),
                 (dict(dx=-3, dy=2, head_dx=-1, head_dy=1, hand=(31, 31), ang=110, off=(33, 17), flow=0.1, flutter=1,
                       shield=dict(rot=-28, sx=0.6)), 250),
                 (dict(dx=-2, dy=2, head_dx=-1, head_dy=1, hand=(32, 30), ang=90, off=(32, 21), flow=0.1, flutter=2,
                       shield=dict(rot=-12, sx=0.55)), 250),
                 (dict(dx=-1, dy=1, hand=(34, 28), ang=-10, off=(32, 25), flow=0.2), 180)])


def sh_counter():  # guard counter: a quick, heavy thrust over the rim straight out of the block
    return mseq([(dict(dx=-1, dy=1, hand=(30, 22), ang=-8, off=(35, 23), footB=(OX + 6, 39), flow=0.3), 40),
                 (dict(dx=3, dy=1, hand=(40, 22), ang=-3, off=(33, 24), footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.3, flutter=1,
                       fx=[("streak", 18), ("flare", "tip", 5)]), 40),
                 (dict(dx=3, dy=1, hand=(40, 21), ang=-12, off=(33, 24), footB=(OX + 8, 39), footF=(OX + 24, 39), flow=1.0, flutter=2,
                       fx=[sw(w=0.4)]), 60),
                 (dict(dx=2, hand=(37, 18), ang=-60, off=(32, 25), footF=(OX + 22, 39), flow=0.6, flutter=3, fx=[sw(w=0.4)]), 60),
                 (dict(dx=1, hand=(35, 25), ang=-40, off=(32, 25), flow=0.3), 110)])


# ---------------------------------------------------------------- v8 twin blades: a flurry, both hands
def tw_1():  # right blade: fast downward cut
    return mseq([(dict(dx=-1, hand=(30, 19), ang=-130, offw=((29, 28), 160), flow=0.3), 45),
                 (dict(dx=2, hand=(38, 24), ang=0, offw=((28, 28), 160), footF=(FF[0] + 2, 39), flow=0.9, flutter=1, fx=[sw(w=0.5)]), 35),
                 (dict(dx=2, hand=(37, 29), ang=45, offw=((28, 28), 160), footF=(FF[0] + 2, 39), flow=0.8, flutter=2, fx=[sw(w=0.45)]), 45),
                 (dict(dx=1, hand=(35, 27), ang=-20, offw=((29, 27), 150), flow=0.4), 60)])


def tw_2():  # left blade: backhand cut from the far side
    return mseq([(dict(hand=(31, 28), ang=150, offw=((28, 21), -140), flow=0.3), 45),
                 (dict(dx=2, hand=(30, 29), ang=150, offw=((38, 25), -5, 18, True), offsw=0.5, footF=(FF[0] + 2, 39),
                       flow=0.9, flutter=1), 35),
                 (dict(dx=2, hand=(30, 29), ang=150, offw=((37, 29), 40, 18, True), offsw=0.45, footF=(FF[0] + 2, 39),
                       flow=0.8, flutter=2), 45),
                 (dict(dx=1, hand=(33, 28), ang=-20, offw=((32, 27), -30), flow=0.4), 60)])


def tw_3():  # both blades rising together
    return mseq([(dict(dy=2, hand=(31, 31), ang=150, offw=((29, 31), 160), footB=(OX + 6, 39), flow=0.3), 50),
                 (dict(dx=2, hand=(38, 24), ang=-40, offw=((36, 26), -20, 18, True), offsw=0.45, footF=(FF[0] + 2, 39),
                       flow=1.0, flutter=1, fx=[sw(w=0.5)]), 40),
                 (dict(dx=2, dy=-1, hand=(36, 17), ang=-82, offw=((37, 20), -62, 18, True), offsw=0.45, footB=(OX + 9, 38),
                       footF=(FF[0] + 2, 39), flow=1.1, flutter=2, fx=[sw(w=0.5)]), 50),
                 (dict(dx=1, hand=(34, 24), ang=-40, offw=((31, 26), -20), flow=0.5), 80)])


def tw_4():  # spinning double slash
    AR = dict(sq=0.42, w=0.55)
    return mseq([(dict(dx=-1, hand=(29, 24), ang=170, offw=((28, 25), 176), flow=0.3), 50),
                 (dict(dx=1, dy=1, hand=(37, 26), ang=-5, offw=((35, 27), 5, 18, True), footF=(FF[0] + 2, 39), flow=1.1, flutter=1,
                       fx=[("arc", (29, 27), 172, -5, AR)]), 40),
                 (dict(dx=1, dy=1, hand=(37, 26), ang=5, offw=((35, 27), 10, 18, True), flow=1.4, flutter=2, mirror=True,
                       fx=[("arc", (29, 27), 185, 5, AR)]), 40),
                 (dict(dx=2, dy=1, hand=(38, 25), ang=-10, offw=((36, 27), 5, 18, True), footF=(FF[0] + 3, 39), flow=1.3, flutter=3,
                       fx=[("arc", (29, 27), 175, -10, AR)]), 40),
                 (dict(dx=1, hand=(35, 26), ang=-30, offw=((31, 27), -10), flow=0.5), 80)])


def tw_5():  # finisher: spring and bring both blades down together
    return mseq([(dict(dx=-1, dy=1, hand=(30, 16), ang=-120, offw=((29, 17), -110), flow=0.3), 70),
                 (dict(dy=-2, hand=(31, 13), ang=-150, offw=((29, 14), -160), footB=(OX + 9, 37), footF=(OX + 18, 38), flow=0.9,
                       flutter=1), 70),
                 (dict(dx=3, dy=2, hand=(39, 23), ang=-10, offw=((37, 24), -20, 18, True), offsw=0.45, footF=(FF[0] + 3, 39),
                       flow=1.2, flutter=2, fx=[sw(w=0.5)]), 40),
                 (dict(dx=3, dy=4, head_dy=1, hand=(39, 30), ang=50, offw=((37, 31), 55, 18, True), offsw=0.45, footB=(OX + 7, 39),
                       footF=(FF[0] + 4, 39), flow=1.0, flutter=3, fx=[sw(w=0.5), ("dust", 52, 3)]), 50),
                 (dict(dx=3, dy=4, head_dy=1, hand=(39, 30), ang=52, offw=((37, 31), 56, 18, True), footB=(OX + 7, 39),
                       footF=(FF[0] + 4, 39), flow=0.6, flutter=4), 150),
                 (dict(dx=1, dy=1, hand=(35, 27), ang=-20, offw=((31, 27), -10), flow=0.3), 110)])


def tw_heavy():  # cross slash: crouch with the blades crossed back, dash through, open them in an X
    return mseq([(dict(dx=-1, dy=2, hand=(29, 19), ang=-150, offw=((30, 19), -120), footB=(OX + 6, 39), flow=0.3), 80),
                 (dict(dx=-2, dy=3, head_dx=-1, hand=(28, 19), ang=-155, offw=((29, 19), -125), footB=(OX + 5, 39), flow=0.2,
                       flutter=1, fx=[("glint", "tip")]), 140),
                 (dict(dx=2, dy=2, hand=(34, 20), ang=-95, offw=((33, 22), -80), footB=(OX + 6, 38), footF=(OX + 23, 39), flow=1.4,
                       flutter=2, fx=[("speed", (22, 16), 5, 14)]), 40),
                 (dict(dx=4, dy=2, hand=(40, 27), ang=40, offw=((40, 20), -40, 18, True), offsw=0.5, footB=(OX + 9, 39),
                       footF=(OX + 26, 39), flow=1.6, flutter=3, fx=[sw(w=0.55)]), 50),
                 (dict(dx=4, dy=2, hand=(39, 31), ang=70, offw=((40, 16), -70, 18, True), offsw=0.5, footB=(OX + 9, 39),
                       footF=(OX + 26, 39), flow=1.3, flutter=4, fx=[sw(w=0.5)]), 60),
                 (dict(dx=4, dy=3, head_dy=1, hand=(39, 31), ang=72, offw=((39, 16), -72, 18, True), footB=(OX + 9, 39),
                       footF=(OX + 26, 39), flow=0.8, flutter=5), 160),
                 (dict(dx=2, dy=1, hand=(36, 28), ang=20, offw=((33, 26), -10), footF=(OX + 22, 39), flow=0.5), 120),
                 (dict(hand=(35, 27), ang=-25, offw=((30, 27), 150), flow=0.3), 100)])


# ---------------------------------------------------------------- v8 techniques (any weapon)
def counter():  # guard counter: two-handed rising cut out of the parry
    return mseq([(dict(dx=-1, dy=2, hand=(30, 30), ang=150, footB=(OX + 6, 39), flow=0.3), 45),
                 (dict(dx=2, hand=(39, 24), ang=-30, footF=(FF[0] + 3, 39), flow=1.2, flutter=1,
                       fx=[("arc", (30, 27), 160, -30, dict(sq=0.55, w=0.6))]), 40),
                 (dict(dx=2, dy=-1, hand=(36, 15), ang=-80, footB=(OX + 9, 38), footF=(FF[0] + 3, 39), flow=1.2, flutter=2,
                       fx=[sw(w=0.5)]), 50),
                 (dict(dx=1, hand=(32, 14), ang=-120, footF=(FF[0] + 2, 39), flow=0.7, flutter=3), 90),
                 (dict(dy=1, hand=(34, 24), ang=-60, flow=0.3), 110)], grip=GRIP_GREAT)


def backstep():  # backstep strike: out of a back-roll, turn and lunge with a wide rising cut
    return mseq([(dict(dx=-2, dy=3, hand=(28, 30), ang=165, footB=(OX + 4, 39), footF=(OX + 18, 39), flow=0.6), 50),
                 (dict(dx=1, dy=3, hand=(33, 31), ang=125, footB=(OX + 5, 39), footF=(OX + 22, 39), flow=1.0, flutter=1,
                       fx=[sw(w=0.35)]), 40),
                 (dict(dx=4, dy=2, hand=(41, 25), ang=-12, footB=(OX + 9, 39), footF=(OX + 27, 39), flow=1.6, flutter=2,
                       fx=[sw(w=0.55), ("speed", (24, 18), 4, 12)]), 45),
                 (dict(dx=4, dy=2, hand=(40, 20), ang=-48, footB=(OX + 9, 39), footF=(OX + 27, 39), flow=1.3, flutter=3,
                       fx=[sw(w=0.5)]), 55),
                 (dict(dx=3, dy=2, hand=(38, 18), ang=-64, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=0.8, flutter=4), 120),
                 (dict(dx=1, dy=1, hand=(35, 26), ang=-40, footF=(OX + 21, 39), flow=0.4), 110)])


def plunge():  # plunging attack, airborne: heave the weapon overhead (then plunge_fall loops)
    return mseq([(dict(dy=-4, hand=(31, 17), ang=-110, flow=0.8, **TUCK), 60),
                 (dict(dy=-5, head_dx=-1, hand=(29, 14), ang=-162, flow=1.0, flutter=1, fx=[("glint", "tip")], **TUCK), 80)],
                grip=GRIP_GREAT)


def plunge_fall():  # plunging: body stretched, blade driven down-forward, cape torn upward
    out = []
    for i in range(2):
        fr = mseq([(dict(dy=-3, hand=(35, 26), ang=62, footB=(OX + 7, 36 - i), footF=(OX + 17, 37), air=True,
                         fx=[("streak", 10 + 4 * i)]), 60)], grip=GRIP_GREAT)[0]
        cels = fr[0]
        cels["Cape"] = draw_streamer((OX + 9, OY + 11 - 3), 252 + 6 * i, 18, 5, 10, 0.6 + i * 1.8, amp=1.2, k=0.7)
        out.append((cels, 60))
    return out


def plunge_land():  # impact: blade driven into the floor ahead, a burst of dust, then rise
    return mseq([(dict(dx=2, dy=5, head_dy=1, hand=(38, 29), ang=60, footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=1.5, flutter=2,
                       fx=[("dust", 46, 10), ("flare", (47, 36), 8)]), 80),
                 (dict(dx=2, dy=5, head_dy=1, hand=(38, 29), ang=62, footB=(OX + 4, 39), footF=(FF[0] + 4, 39), flow=0.9, flutter=3,
                       fx=[("dust", 46, 5)]), 150),
                 (dict(dx=1, dy=3, hand=(36, 28), ang=30, footF=(FF[0] + 2, 39), flow=0.4, flutter=4), 110),
                 (dict(hand=(35, 27), ang=-30, flow=0.3), 100)], grip=GRIP_GREAT)


def sp_jump():  # spear jump thrust: cock the spear back at the top of the jump...
    return mseq([(dict(dy=-4, hand=(28, 20), ang=-15, flow=0.8, **TUCK), 60),
                 (dict(dy=-5, head_dx=-1, hand=(26, 19), ang=22, flow=1.0, flutter=1, fx=[("glint", "tip")], **TUCK), 70)],
                grip=GRIP_SPEAR)


def sp_dive():  # ...and dive down it at an angle (loop until landing)
    out = []
    for i in range(2):
        fr = mseq([(dict(dx=2, dy=-2, hand=(37, 28), ang=38, footB=(OX + 5, 35 - i), footF=(OX + 14, 36), air=True,
                         fx=[("streak", 14 + 4 * i)]), 60)], grip=GRIP_SPEAR)[0]
        cels = fr[0]
        cels["Cape"] = draw_streamer((OX + 11, OY + 11 - 2), 228 + 5 * i, 18, 5, 9, 0.9 + i * 1.7, amp=1.1, k=0.7)
        out.append((cels, 60))
    return out


V8_MOVES = [("st_1", st_1), ("st_2", st_2), ("st_3", st_3), ("st_4", st_4), ("st_heavy", st_heavy),
            ("sh_1", sh_1), ("sh_2", sh_2), ("sh_3", sh_3), ("sh_heavy", sh_heavy), ("sh_guard", sh_guard),
            ("sh_block", sh_block), ("sh_parry", sh_parry), ("sh_break", sh_break), ("sh_counter", sh_counter),
            ("tw_1", tw_1), ("tw_2", tw_2), ("tw_3", tw_3), ("tw_4", tw_4), ("tw_5", tw_5), ("tw_heavy", tw_heavy),
            ("counter", counter), ("backstep", backstep), ("plunge", plunge), ("plunge_fall", plunge_fall),
            ("plunge_land", plunge_land), ("sp_jump", sp_jump), ("sp_dive", sp_dive)]
MOVE_CLASS.update({"st": ("quarterstaff",), "sh": ("knight_shield",), "tw": ("twinfangs",)})
ACTIVE.update({"st_1": (1, 2), "st_2": (2, 4), "st_3": (2, 3), "st_4": (4, 5), "st_heavy": (1, 5),
               "sh_1": (2, 3), "sh_2": (2, 3), "sh_3": (2, 3), "sh_heavy": (4, 5), "sh_counter": (1, 2),
               "tw_1": (1, 2), "tw_2": (1, 2), "tw_3": (1, 2), "tw_4": (1, 3), "tw_5": (2, 3), "tw_heavy": (3, 4),
               "counter": (1, 2), "backstep": (2, 3), "plunge_land": (0, 0), "sp_dive": (0, 1)})
HIT_EXTRAS = {"sh_heavy"} | {t for t in ("tw_1", "tw_2", "tw_3", "tw_4", "tw_5", "tw_heavy")}   # hitbox incl. shield / off blade
HIT_X0 = {"tw_1": 0, "st_1": 0, "st_3": -4, "st_4": -2, "st_2": -6, "sh_heavy": 2, "tw_2": 0, "tw_3": 0, "tw_5": 0, "tw_heavy": 0,
          "counter": -2, "backstep": 0, "sh_counter": 0}      # clamp the back edge (staff butt / far blade behind the body)
HIT_OVERRIDE = {"st_heavy": [-36, -32, 38, 0], "plunge_land": [-26, -30, 40, 0]}
FXAT_OVERRIDE.update({"tw_2": (18, -14), "sh_heavy": (16, -14), "st_heavy": (20, -9), "tw_4": (20, -14)})


# ---------------------------------------------------------------- v8 weapon arts (agent G's ART_IMPL drives the logic; these are
# the bodies). Release frame = ACTIVE[tag][0] (G waits for it). Held/looping sections are synced by 04_player.js ART_SYNC.
P_GOLD = ((255, 244, 200), (255, 200, 100), (180, 120, 40))
P_FROST = ((236, 250, 255), (150, 206, 244), (70, 120, 190))
P_MAGMA = ((255, 240, 170), (255, 158, 48), (206, 70, 26))
P_STORM = ((244, 252, 255), (170, 214, 255), (90, 140, 230))
P_INK = ((236, 214, 255), (170, 120, 240), (88, 50, 150))
P_WIND = ((236, 252, 248), (170, 222, 214), (96, 140, 150))
P_BLOOD = ((255, 150, 150), (214, 40, 58), (120, 16, 34))


def art_whirlwind():  # coil, then a whirling spin at the waist (frames 1-8 loop while the art lasts)
    RG = dict(sq=0.3, w=11.0, pal=P_WIND)
    spin = []
    for k in range(8):
        m = k % 2 == 1
        fx = [("ring", (30, 28), 24, 180, 0, RG)]
        if k % 2 == 0:
            fx.append(("dust", 30 + (k % 4) * 4, 4))
        spin.append((dict(dx=1, dy=2 - (1 if k % 4 == 1 else 0), hand=(33, 27 + k % 2), ang=3, footF=(FF[0] + 2, 39),
                          footB=(OX + 7 - k % 2, 39), flow=1.3 + 0.2 * (k % 2), flutter=k, mirror=m, behind=m, fx=fx), 50))
    return mseq([(dict(dx=-2, dy=3, head_dx=-1, hand=(28, 28), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3,
                       aura=1, aura_pal=P_WIND, fx=[("glint", "tip")]), 90)] + spin, grip=GRIP_STAFF, art=True)


def art_gale_vault():  # plant the staff and vault over, flip at the apex, bring it down in a falling cut
    return mseq([(dict(dx=-1, dy=4, head_dy=1, hand=(32, 28), ang=40, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3,
                       aura=1, aura_pal=P_WIND, fx=[("glint", "tip")]), 110),
                 (dict(dy=-3, hand=(35, 24), ang=64, footB=(OX + 8, 37), footF=(OX + 16, 36), air=True, flow=1.2, flutter=1,
                       fx=[("dust", 44, 5), ("speed", (24, 30), 3, 10, P_WIND)]), 60),
                 (dict(dy=-7, hand=(33, 21), ang=104, footB=(OX + 13, 32), footF=(OX + 21, 31), air=True, flow=1.5, flutter=2,
                       fx=[sw(w=0.3)], fx_pal=P_WIND), 70),
                 (dict(dy=-8, head_dx=-1, hand=(31, 16), ang=-122, footB=(OX + 10, 32), footF=(OX + 18, 32), air=True, flow=1.2,
                       flutter=3, aura=1, aura_pal=P_WIND, fx=[sw(w=0.35)], fx_pal=P_WIND), 70),
                 (dict(dy=-8, head_dx=-1, hand=(30, 14), ang=-150, footB=(OX + 10, 33), footF=(OX + 18, 32), air=True, flow=1.0,
                       flutter=4, aura=1, aura_pal=P_WIND, fx=[("glint", "tip")]), 70),
                 (dict(dx=1, dy=-6, hand=(38, 24), ang=40, footB=(OX + 9, 36), footF=(OX + 18, 36), air=True, flow=0.6, flutter=5,
                       fx=[sw(w=0.55)], fx_pal=P_WIND), 50),
                 (dict(dx=1, dy=-4, hand=(38, 28), ang=62, footB=(OX + 9, 37), footF=(OX + 18, 38), air=True, flow=0.2, flutter=6,
                       fx=[("streak", 10)], fx_pal=P_WIND), 60),
                 (dict(dx=1, dy=5, head_dy=1, hand=(37, 30), ang=42, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=1.2, flutter=7,
                       fx=[("dust", 42, 7)]), 90),
                 (dict(dy=1, hand=(34, 27), ang=-18, flow=0.4), 110)], grip=GRIP_STAFF, art=True)


def art_ink_mark():  # the quill traces a glyph on the air, rises glowing, then stabs it into the ground
    RI = lambda a1: ("ring", (50, 15), 6.5, -90, a1, dict(sq=1.0, w=1.8, pal=P_INK))
    return mseq([(dict(dy=1, hand=(33, 22), ang=-40, flow=0.3), 90),
                 (dict(dx=1, hand=(36, 19), ang=-22, flow=0.4, flutter=1, fx=[RI(40), ("flare", "tip", 3, P_INK)]), 110),
                 (dict(dx=1, hand=(35, 21), ang=8, flow=0.4, flutter=2, fx=[RI(190), ("flare", "tip", 3, P_INK)]), 110),
                 (dict(dy=-1, hand=(33, 16), ang=-72, flow=0.3, flutter=3, aura=2, aura_pal=P_INK,
                       fx=[RI(269), ("flare", (50, 15), 4, P_INK), ("glint", "tip")]), 140),
                 (dict(dx=3, dy=3, head_dy=1, hand=(39, 27), ang=62, footF=(FF[0] + 3, 39), flow=1.2, flutter=4,
                       fx=[sw(w=0.5), ("flare", (48, 37), 9, P_INK), ("dust", 48, 4)], fx_pal=P_INK), 60),
                 (dict(dx=3, dy=3, head_dy=1, hand=(39, 27), ang=62, footF=(FF[0] + 3, 39), flow=0.7, flutter=5,
                       fx=[("rings", (48, 36), (6, 10))], fx_pal=P_INK), 160),
                 (dict(dx=1, dy=1, hand=(35, 26), ang=-20, flow=0.3), 140)], grip=GRIP_STAFF, art=True)


def _aegis(pal):  # brace behind the shield (hold frames 2-3 while the guard lasts), then shove it out
    return mseq([(dict(dx=-1, dy=1, hand=(30, 22), ang=-60, off=(33, 24), flow=0.3), 70),
                 (dict(dx=-2, dy=3, head_dx=-1, hand=(29, 21), ang=-20, off=(34, 23), footB=(OX + 5, 39), footF=(FF[0] + 2, 39),
                       flow=0.2, flutter=1, shield=dict(sx=0.66), aura=1, aura_pal=pal, fx=[("glint", (38, 16))]), 100),
                 (dict(dx=-1, dy=3, hand=(31, 20), ang=-8, off=(36, 23), footB=(OX + 4, 39), footF=(FF[0] + 3, 39), flow=0.5,
                       flutter=2, shield=dict(sx=0.72), aura=1, aura_pal=pal, fx=[("flare", (42, 24), 5, pal)]), 120),
                 (dict(dx=-1, dy=3, hand=(31, 20), ang=-6, off=(36, 22), footB=(OX + 4, 39), footF=(FF[0] + 3, 39), flow=0.4,
                       flutter=3, shield=dict(sx=0.72), aura=2, aura_pal=pal, fx=[("flare", (42, 23), 7, pal)]), 120),
                 (dict(dx=2, dy=2, hand=(31, 22), ang=-10, off=(40, 22), footB=(OX + 6, 39), footF=(OX + 24, 39), flow=1.3, flutter=4,
                       shield=dict(sx=0.45, rot=8), fx=[("flare", (46, 22), 9, pal), ("speed", (21, 17), 4, 12, pal)]), 60),
                 (dict(dx=1, dy=1, hand=(32, 24), ang=-30, off=(35, 24), flow=0.6, flutter=5), 140),
                 (dict(hand=(34, 27), ang=-40, off=(32, 25), flow=0.3), 110)], art=True)


def art_aegis():
    return _aegis(P_GOLD)


def art_frost_aegis():
    return _aegis(P_FROST)


def art_shield_charge():  # coil behind the shield, then a headlong rush (frames 2-3 alternate) and a skidding impact
    SH = dict(sx=0.42)
    return mseq([(dict(dx=-1, dy=2, hand=(29, 28), ang=160, off=(34, 24), footB=(OX + 6, 39), flow=0.3), 80),
                 (dict(dx=-3, dy=4, head_dx=-1, hand=(28, 29), ang=165, off=(33, 24), footB=(OX + 4, 39), footF=(FF[0] + 1, 39),
                       flow=0.2, flutter=1, shield=dict(sx=0.5), fx=[("glint", (37, 18))]), 130),
                 (dict(dx=3, dy=3, head_dx=1, hand=(30, 29), ang=158, off=(39, 23), footB=(OX + 4, 39), footF=(OX + 24, 38), flow=1.9,
                       flutter=2, shield=SH, fx=[("speed", (19, 17), 5, 16, P_MAGMA), ("dust", 24, 2)]), 60),
                 (dict(dx=3, dy=3, head_dx=1, hand=(30, 30), ang=160, off=(39, 24), footB=(OX + 11, 37), footF=(OX + 20, 39), flow=2.0,
                       flutter=5, shield=SH, fx=[("speed", (19, 18), 5, 14, P_MAGMA)]), 60),
                 (dict(dx=2, dy=2, hand=(30, 28), ang=150, off=(38, 21), footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.2, flutter=6,
                       shield=dict(sx=0.5, rot=-10), fx=[("flare", (44, 21), 8, P_MAGMA), ("dust", 40, 5)]), 70),
                 (dict(dy=1, hand=(31, 28), ang=150, off=(35, 24), flow=0.6, flutter=7), 130),
                 (dict(hand=(34, 28), ang=-20, off=(32, 25), flow=0.3), 100)], art=True)


def art_magma_quake():  # heave the weapon high, hop, and smash the ground open
    return mseq([(dict(dy=2, hand=(33, 29), ang=125, flow=0.3), 100),
                 (dict(dx=-1, dy=3, head_dx=-1, hand=(29, 16), ang=-150, footB=(OX + 5, 39), flow=0.3, flutter=1, aura=1, aura_pal=P_MAGMA,
                       fx=[("embers", (30, 10), 4, 1)]), 140),
                 (dict(dy=-5, hand=(30, 13), ang=-165, footB=(OX + 9, 35), footF=(OX + 18, 34), air=True, flow=1.1, flutter=2, aura=1,
                       aura_pal=P_MAGMA, fx=[("embers", (28, 8), 5, 2), ("dust", 28, 3)]), 80),
                 (dict(dy=-7, head_dx=-1, hand=(28, 12), ang=-174, air=True, flow=1.2, flutter=3, aura=1, aura_pal=P_MAGMA,
                       fx=[("glint", "tip")], **{k: v for k, v in TUCK.items() if k != "air"}), 90),
                 (dict(dx=2, dy=5, head_dy=1, hand=(37, 29), ang=55, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=1.4,
                       flutter=4, fx=[sw(w=0.5), ("dust", 48, 10), ("flare", (48, 36), 10, P_MAGMA), ("embers", (48, 30), 6, 3)],
                       fx_pal=P_MAGMA), 60),
                 (dict(dx=2, dy=5, head_dy=1, hand=(37, 29), ang=56, slen=16, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=1.0,
                       flutter=5, fx=[("dust", 48, 6), ("flare", (48, 36), 6, P_MAGMA), ("embers", (50, 28), 6, 4)]), 90),
                 (dict(dx=2, dy=5, head_dy=1, hand=(37, 30), ang=58, footB=(OX + 5, 39), footF=(FF[0] + 3, 39), flow=0.5, flutter=6,
                       fx=[("embers", (50, 32), 4, 5)]), 230),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=30, flow=0.3), 170)], grip=GRIP_GREAT, art=True)


def art_thunder_lunge():  # sink, crackle, then a flying lightning lunge (frames 2-3 alternate) and a skid
    return mseq([(dict(dx=-2, dy=2, hand=(29, 26), ang=-4, footB=(OX + 5, 39), flow=0.3), 80),
                 (dict(dx=-3, dy=4, head_dx=-1, hand=(26, 27), ang=-6, footB=(OX + 4, 39), footF=(OX + 17, 39), flow=0.2, flutter=1,
                       aura=1, aura_pal=P_STORM, fx=[("flare", "tip", 4, P_STORM)]), 140),
                 (dict(dx=4, dy=3, head_dx=2, hand=(42, 26), ang=0, footB=(OX + 1, 36), footF=(OX + 12, 35), air=True, flow=2.0,
                       flutter=2, aura=1, aura_pal=P_STORM, fx=[("streak", 20), ("speed", (16, 17), 6, 22, P_STORM)], fx_pal=P_STORM), 50),
                 (dict(dx=4, dy=3, head_dx=2, hand=(42, 27), ang=1, footB=(OX + 3, 35), footF=(OX + 11, 36), air=True, flow=2.0,
                       flutter=5, aura=1, aura_pal=P_STORM, fx=[("streak", 16), ("speed", (15, 18), 6, 20, P_STORM)], fx_pal=P_STORM), 50),
                 (dict(dx=3, dy=3, hand=(41, 26), ang=2, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.2, flutter=6,
                       fx=[("dust", 30, 4), ("flare", "tip", 5, P_STORM)]), 80),
                 (dict(dx=1, dy=1, hand=(34, 26), ang=-3, footF=(OX + 21, 39), flow=0.5, flutter=7), 140),
                 (dict(hand=(33, 27), ang=-8, flow=0.3), 120)], grip=GRIP_SPEAR, art=True)


def art_tolling_blow():  # the hammer swings up behind in a full circle and falls like a bell's clapper
    return mseq([(dict(dx=-1, dy=2, hand=(30, 31), ang=150, footB=(OX + 6, 39), flow=0.3), 100),
                 (dict(dx=-2, dy=1, head_dx=-1, hand=(25, 19), ang=-160, footB=(OX + 5, 39), flow=0.3, flutter=1, fx=[sw(w=0.3)],
                       fx_pal=P_GOLD), 130),
                 (dict(dx=-1, dy=-1, hand=(30, 12), ang=-110, footB=(OX + 6, 39), flow=0.2, flutter=2, aura=1, aura_pal=P_GOLD,
                       fx=[("glint", "tip")]), 170),
                 (dict(dx=2, dy=1, hand=(37, 19), ang=-20, footF=(FF[0] + 2, 39), flow=1.0, flutter=3, fx=[sw(w=0.5)], fx_pal=P_GOLD), 50),
                 (dict(dx=3, dy=4, head_dy=1, hand=(38, 29), ang=52, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.3, flutter=4,
                       fx=[("dust", 50, 8), ("flare", (50, 35), 8, P_GOLD), ("rings", (50, 32), (5, 9))], fx_pal=P_GOLD), 60),
                 (dict(dx=3, dy=4, head_dy=1, hand=(38, 29), ang=53, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.9, flutter=5,
                       fx=[("dust", 50, 4), ("rings", (50, 32), (10, 15))], fx_pal=P_GOLD), 120),
                 (dict(dx=3, dy=4, head_dy=1, hand=(38, 30), ang=54, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.5, flutter=6,
                       fx=[("rings", (50, 32), (15, 21))], fx_pal=P_GOLD), 220),
                 (dict(dx=1, dy=2, hand=(35, 28), ang=30, flow=0.3), 160)], grip=GRIP_GREAT, art=True)


def art_twin_tempest():  # blades crossed low, a whirl of alternating cuts (frames 1-4 loop), then an X that opens the foe
    return mseq([(dict(dx=-2, dy=3, head_dx=-1, hand=(29, 24), ang=170, offw=((30, 24), 176), footB=(OX + 4, 39),
                       footF=(FF[0] + 1, 39), flow=0.3, aura=1, aura_pal=P_BLOOD, fx=[("glint", "tip")]), 120),
                 (dict(dx=2, dy=2, hand=(39, 22), ang=-30, offw=((31, 28), 150), footF=(FF[0] + 2, 39), flow=1.2, flutter=1,
                       fx=[("arc", (30, 26), 160, -30, dict(sq=0.5, w=0.5))], fx_pal=P_BLOOD), 45),
                 (dict(dx=2, dy=2, hand=(33, 28), ang=150, offw=((39, 27), 30, 18, True), offsw=0.5, footF=(FF[0] + 2, 39), flow=1.3,
                       flutter=2), 45),
                 (dict(dx=2, dy=1, hand=(40, 26), ang=10, offw=((32, 22), -120), footF=(FF[0] + 2, 39), flow=1.2, flutter=3,
                       fx=[sw(w=0.5)], fx_pal=P_BLOOD), 45),
                 (dict(dx=2, dy=2, hand=(34, 20), ang=-110, offw=((40, 24), -10, 18, True), offsw=0.5, footF=(FF[0] + 2, 39),
                       flow=1.3, flutter=4), 45),
                 (dict(dx=4, dy=2, hand=(41, 30), ang=60, offw=((41, 17), -60, 18, True), offsw=0.6, footB=(OX + 9, 39),
                       footF=(OX + 26, 39), flow=1.7, flutter=5, fx=[sw(w=0.6, a0=-60), ("flare", (46, 23), 8, P_BLOOD)],
                       fx_pal=P_BLOOD), 70),
                 (dict(dx=4, dy=3, head_dy=1, hand=(40, 31), ang=64, offw=((40, 16), -64, 18, True), footB=(OX + 9, 39),
                       footF=(OX + 26, 39), flow=0.9, flutter=6), 200),
                 (dict(hand=(35, 27), ang=-25, offw=((30, 27), 150), flow=0.3), 120)], art=True)


def art_backstep_slash():  # a hop back (frames 1-2 while airborne), then a long lunging cut
    return mseq([(dict(dy=3, hand=(33, 28), ang=-20, footB=(OX + 6, 39), flow=0.3, aura=1, fx=[("glint", "tip")]), 70),
                 (dict(dx=-3, dy=-3, head_dx=-1, hand=(30, 27), ang=168, footB=(OX + 7, 36), footF=(OX + 19, 35), air=True, flow=0.1,
                       flutter=1, fx=[("speed", (44, 24), 4, 10)]), 60),
                 (dict(dx=-3, dy=-2, head_dx=-1, hand=(30, 28), ang=170, footB=(OX + 7, 37), footF=(OX + 19, 36), air=True, flow=0.0,
                       flutter=2), 60),
                 (dict(dx=3, dy=2, hand=(36, 29), ang=152, footB=(OX + 5, 39), footF=(OX + 22, 39), flow=1.6, flutter=3,
                       fx=[("speed", (20, 18), 5, 16)]), 40),
                 (dict(dx=5, dy=2, hand=(43, 24), ang=-20, footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.8, flutter=4,
                       fx=[("arc", (32, 26), 165, -20, dict(sq=0.5, w=0.7))]), 50),
                 (dict(dx=5, dy=2, hand=(41, 19), ang=-60, footB=(OX + 9, 39), footF=(OX + 28, 39), flow=1.4, flutter=5,
                       fx=[sw(w=0.5)]), 60),
                 (dict(dx=4, dy=2, hand=(39, 19), ang=-66, footB=(OX + 8, 39), footF=(OX + 26, 39), flow=0.8, flutter=6), 140),
                 (dict(dx=1, dy=1, hand=(35, 26), ang=-40, flow=0.4), 100)], art=True)


def sh_rest():  # sword & shield: after a fight the shield swings back round the hip onto the back (then idle)
    return mseq([(dict(hand=(35, 27), ang=-45, off=(33, 25), flow=0.3), 60),
                 (dict(hand=(35, 27), ang=-48, off=(29, 28), flow=0.3, flutter=1, shield=dict(abs=(30.5, 27), rot=30, sx=0.55, layer="over")), 70),
                 (dict(hand=(35, 27), ang=-50, flow=0.2, flutter=2, shield=dict(abs=(21.5, 24.5), rot=-14, sx=0.78, layer="behind")), 80)])


V8_ARTS = [("art_whirlwind", art_whirlwind), ("art_gale_vault", art_gale_vault), ("art_ink_mark", art_ink_mark),
           ("art_aegis", art_aegis), ("art_frost_aegis", art_frost_aegis), ("art_shield_charge", art_shield_charge),
           ("art_magma_quake", art_magma_quake), ("art_thunder_lunge", art_thunder_lunge), ("art_tolling_blow", art_tolling_blow),
           ("art_twin_tempest", art_twin_tempest), ("art_backstep_slash", art_backstep_slash), ("sh_rest", sh_rest)]
ACTIVE.update({"art_whirlwind": (1, 1), "art_gale_vault": (1, 1), "art_ink_mark": (4, 4), "art_aegis": (2, 2),
               "art_frost_aegis": (2, 2), "art_shield_charge": (2, 2), "art_magma_quake": (4, 4), "art_thunder_lunge": (2, 2),
               "art_tolling_blow": (4, 4), "art_twin_tempest": (1, 1), "art_backstep_slash": (1, 1)})


# ================================================================ v9 (Expansion 2): scythe + whip classes, 21 weapons
# Scythes are hafted two-handed; the blade juts from the head on the +v side (the clockwise side of the swing), its edge on
# the concave side facing the wielder. Whips are a short rigid handle (the Wpn cel) plus a lash drawn as a curve through
# per-frame control points (Wpn.lash) -- see render_whip. Like v8, only the new kinds use the new code paths.
SCYTHE_BACK = {}       # scythe kind -> haft length behind the front hand
WHIP_KINDS = ("headsman_chain", "gravechain", "orrery_whip")


def _scythe_blade(u, v, tip, reach=12.5, sweep=6.5, w0=2.6, root=1.2):
    """Blade of a scythe/antler: returns (edge_dist, spine_dist, t) if (u, v) is on the blade, else None.
    The blade leaves the head at u = tip - root along +v, bending back toward -u as it reaches out."""
    if v < -0.8 or v > reach:
        return None
    t = max(0.0, v) / reach
    uc = tip - root - sweep * t ** 1.7          # spine line
    w = w0 * (1 - t) ** 0.65 + 0.35              # blade depth toward the wielder
    if uc - w <= u <= uc + 0.6:
        return (u - (uc - w), uc + 0.6 - u, t)
    return None


def _haft(u, v, s, lo, hi, dark, lite, hw=0.72):
    if lo <= u <= hi and abs(v) <= hw:
        return lite if v * s > 0 else dark
    return None


def shp_antler_scythe(u, v, s, L, back=6.0):
    """The Warden's scythe: a living-wood haft wound with a green-glowing groove, the blade a branching antler."""
    tip = L + 1.5
    b = _scythe_blade(u, v, tip, reach=12.5, sweep=6.0, w0=2.2)
    if b:
        e, sp, t = b
        if e < 0.9:
            return (244, 238, 222)
        if int(v * 1.3) % 5 == 3 and sp < 1.2:
            return (96, 132, 60)                  # moss
        return (214, 204, 182) if sp > 1.2 else (150, 138, 118)
    for tv, tl in ((4.0, 3.2), (8.0, 2.4)):       # tines off the outer (spine) side
        uc = tip - 1.2 - 6.0 * (tv / 12.5) ** 1.7 + 0.6
        if uc <= u <= uc + tl and abs(v - tv - (u - uc) * 0.5) <= 0.6:
            return (214, 204, 182) if u < uc + tl - 0.8 else (244, 238, 222)
    if tip - 2.2 <= u <= tip and abs(v) <= 1.2:
        return (120, 230, 140) if abs(v) < 0.5 else (60, 44, 36)      # glowing knot where the antler grows
    if -back <= u < tip - 2.2 and abs(v - 0.25 * math.sin(u * 0.9)) <= 0.72:
        if abs(((u * 0.8 + v * 2.0) % 4.0) - 2.0) < 0.35:
            return (110, 220, 130)               # green-glowing spiral groove
        return (84, 62, 48) if v * s > 0 else (40, 28, 24)
    return None


def _post_ribbon(pix, hand, d, L):   # a pale ribbon hanging from the antler's root, whatever the angle
    x0, y0 = hand[0] + d[0] * (L - 0.5), hand[1] + d[1] * (L - 0.5)
    for k in range(1, 6):
        pix[(int(round(x0 - (k // 3))), int(round(y0 + k)))] = (232, 232, 222) if k < 4 else (180, 180, 172)


def shp_briar_scythe(u, v, s, L, back=6.0):
    """A field scythe grown through with bramble: rusted blade, a haft of thorned briar."""
    tip = L + 1.5
    b = _scythe_blade(u, v, tip, reach=11.5, sweep=6.5, w0=2.4)
    if b:
        e, sp, t = b
        if e < 0.9:
            return (206, 196, 180)
        return (150, 110, 80) if sp > 1.0 and int(v * 2) % 3 else (96, 70, 54)
    if tip - 1.6 <= u <= tip and abs(v) <= 1.1:
        return (110, 104, 110)
    if -back <= u < tip - 1.6:
        if abs(v) <= 0.72:
            return (116, 84, 50) if v * s > 0 else (64, 44, 28)
        iu = int(math.floor(u))
        if iu % 3 == 0 and 0.72 < abs(v) <= 1.6 and (iu // 3) % 2 == (1 if v > 0 else 0):
            return (170, 150, 110)                # thorns
    return None


def shp_crimson_scythe(u, v, s, L, back=6.0):
    """A duelling scythe of the Crimson court: black-lacquered haft ringed in gold, a blade the colour of old blood."""
    tip = L + 1.5
    b = _scythe_blade(u, v, tip, reach=12.0, sweep=7.0, w0=2.5)
    if b:
        e, sp, t = b
        if e < 0.9:
            return (255, 170, 170)
        if e < 1.6:
            return (214, 48, 64)
        return (130, 20, 40) if sp > 0.8 else (70, 10, 24)
    if tip - 2.0 <= u <= tip and abs(v) <= 1.3:
        return (230, 186, 92) if v * s > 0 else (130, 90, 36)
    r = _haft(u, v, s, -back, tip - 2.0, (22, 16, 22), (58, 44, 58))
    if r:
        return (230, 186, 92) if int(math.floor(u)) % 6 == 0 else r
    return None


def shp_last_kindling(u, v, s, L, back=6.0):
    """Venn's scythe: an ivory root haft, the blade a curved sheet of pale white flame."""
    tip = L + 1.5
    b = _scythe_blade(u, v, tip, reach=13.0, sweep=6.0, w0=2.9)
    if b:
        e, sp, t = b
        if e < 0.9:
            return (210, 230, 255)
        if sp < 0.9 and int(v * 1.7) % 3 == 0:
            return (255, 236, 190)                # flame licks on the spine
        return (255, 252, 240) if e < 2.0 else (255, 236, 190)
    uc = tip - 1.2
    if uc < u <= uc + 2.2 and -0.8 < v < 3 and (int(v * 2) + int(u * 2)) % 3 == 0:
        return (255, 236, 190)                    # sparks off the spine
    if tip - 2.0 <= u <= tip and abs(v) <= 1.3:
        return (255, 244, 214) if abs(v) < 0.6 else (190, 176, 150)
    if -back <= u < tip - 2.0:
        if abs(v) <= 0.72:
            if abs(((u * 0.7 - v * 2.2) % 5.0) - 2.5) < 0.4:
                return (160, 146, 120)            # root tendril wound round it
            return (236, 228, 206) if v * s > 0 else (176, 162, 136)
    return None


# ---- staffs
def shp_thornwood_staff(u, v, s, L, back=12.0):
    """A staff of thornwood, still budding: a green bud swells at its crown."""
    tip = L + 1.5
    if tip - 3.2 <= u <= tip + 0.4 and math.hypot(u - (tip - 1.4), v) <= 1.6:
        return (170, 236, 140) if v * s > 0 and u > tip - 1.8 else (70, 130, 60)
    if -back <= u < tip - 3.0:
        if abs(v) <= 0.72:
            iu = int(math.floor(u))
            if iu % 5 == 2:
                return (70, 50, 34)
            return (104, 80, 54) if v * s > 0 else (58, 42, 30)
        iu = int(math.floor(u))
        if iu % 3 == 1 and 0.72 < abs(v) <= 1.7 and (iu // 3) % 2 == (1 if v > 0 else 0):
            return (150, 170, 100)
    return None


def shp_sun_sceptre(u, v, s, L, back=12.0):
    """The Pharaoh's sun sceptre: gold ringed in lapis, crowned by a rayed disc of the sun."""
    tip = L + 1.5
    cu = tip - 2.4
    d = math.hypot(u - cu, v)
    if d <= 2.6:
        if d < 1.2:
            return (255, 250, 220)
        return (255, 214, 104) if d < 2.0 else (200, 140, 50)
    a = math.atan2(v, u - cu)
    if 2.6 < d <= 4.3 and (int((a + 3.2) / 0.5236) % 2 == 0) and abs(((a + 3.2) % 0.5236) - 0.26) < 0.14:
        return (255, 214, 104)                    # rays
    if -back <= u < cu - 2.6 and abs(v) <= 0.72:
        iu = int(math.floor(u))
        if iu % 4 == 0:
            return (60, 90, 200) if v * s > 0 else (30, 50, 130)
        return (240, 196, 90) if v * s > 0 else (160, 110, 40)
    return None


# ---- spears (LONGHAFT signature: back = haft behind the hand)
def shp_choir_harpoon(u, v, s, L, back=SPEAR_BACK):
    """The Choir's harpoon: a barbed bone head with a teal glow line, lashed to a black-water haft."""
    tip = L + 1.5
    h0 = tip - 8.0
    if h0 <= u <= tip:
        t = (u - h0) / 8.0
        hw = 1.3 * (1 - t) + 0.25
        if abs(v) <= hw:
            if abs(v) < 0.4 and t < 0.8:
                return (120, 240, 220)
            return (236, 230, 214) if v * s > 0 else (160, 150, 136)
        for bu in (h0 + 1.0, h0 + 3.6):           # barbs sweeping back on both sides
            if bu <= u <= bu + 2.4 and abs(abs(v) - (hw + (u - bu) * 0.0) - 0.2 - (bu + 2.4 - u) * 0.55) <= 0.5:
                return (214, 206, 190)
    if h0 - 2.4 <= u < h0:
        if abs(v) <= 1.0 and (int(u * 2) % 2 == 0):
            return (190, 180, 150)                # rope lashing
        if abs(v) <= 0.6:
            return (40, 70, 80)
    if -back <= u < h0 - 2.4 and abs(v) <= 0.55:
        iu = int(math.floor(u))
        if iu % 7 == 3:
            return (80, 200, 190)
        return (40, 70, 80) if v * s >= 0 else (20, 36, 44)
    if -back - 1.4 <= u < -back and abs(v) <= 0.8:
        return (160, 150, 136)
    return None


def shp_scarab_spear(u, v, s, L, back=SPEAR_BACK):
    """A Scarab Knight's spear: the blade a shard of beetle shell, iridescent green to gold."""
    tip = L + 1.5
    h0 = tip - 8.5
    if h0 <= u <= tip:
        t = (u - h0) / 8.5
        hw = max(0.3, 2.0 * math.sin(math.pi * min(1.0, t * 1.2) ** 0.8) if t < 0.8 else 2.0 * (1 - t) / 0.2 * 0.8 + 0.2)
        if abs(v) <= hw:
            if abs(v) < 0.4:
                return (40, 60, 40)
            k = (u * 0.8 + v * 1.5) % 3.0
            return (120, 220, 160) if k < 1 else ((220, 200, 90) if k < 2 else (40, 140, 110))
    if h0 - 1.6 <= u < h0 and abs(v) <= 1.0:
        return (220, 180, 80) if v * s > 0 else (130, 90, 30)
    if -back <= u < h0 - 1.6 and abs(v) <= 0.55:
        return (40, 64, 50) if v * s >= 0 else (20, 32, 26)
    if -back - 1.4 <= u < -back and abs(v) <= 0.8:
        return (220, 180, 80)
    return None


NEON = ((255, 255, 255), (120, 255, 250), (40, 170, 230), (255, 70, 200), (150, 30, 140))
def shp_saint_lance(u, v, s, L, back=SPEAR_BACK):
    """SAINT-0's lance: a chrome haft traced with circuit light, the head a blade of cyan energy rimmed in magenta."""
    tip = L + 1.5
    h0 = tip - 9.0
    if h0 <= u <= tip:
        t = (u - h0) / 9.0
        hw = 1.9 * (1 - t) ** 0.9 + 0.2
        if abs(v) <= hw:
            if abs(v) < 0.5:
                return NEON[0]
            if abs(v) > hw - 0.6:
                return NEON[3]
            return NEON[1] if abs(v) < hw * 0.6 else NEON[2]
    if h0 - 2.0 <= u < h0 and abs(v) <= 1.4:
        return (230, 236, 244) if v * s > 0 else (120, 130, 150)   # emitter collar
    if -back <= u < h0 - 2.0 and abs(v) <= 0.6:
        iu = int(math.floor(u))
        if iu % 4 == 1:
            return NEON[1] if iu % 8 == 1 else NEON[3]            # circuit lights
        return (224, 230, 240) if v * s >= 0 else (140, 150, 170)
    if -back - 1.4 <= u < -back and abs(v) <= 0.8:
        return (140, 150, 170)
    return None


# ---- swords
def shp_sanguine_rapier(u, v, s, L):
    """The Countess's rapier: a needle of crimson steel with a blood-red core, a swept gold cup-hilt."""
    tip = L + 1.5
    if 2.2 <= u <= tip:
        hw = _taper(u, tip, 0.62, 5.0)
        if abs(v) <= hw:
            if abs(v) < 0.3 and u < tip - 2:
                return (220, 30, 50)
            return (236, 220, 226) if v * s > 0 else (150, 110, 124)
    d = math.hypot(u - 1.2, v)
    if 1.8 <= d <= 3.0 and u > -0.5:
        return (240, 196, 90) if v * s > 0 else (150, 100, 40)       # swept ring guard
    if 0.6 <= u < 2.2 and abs(v) <= 1.2:
        return (240, 196, 90)
    if -3.4 <= u < 0.6 and abs(v) <= 0.7:
        return (100, 20, 34) if int(math.floor(u)) % 2 else (50, 10, 20)
    if -4.6 <= u < -3.4 and abs(v) <= 1.2:
        return (240, 196, 90) if v * s > 0 else (150, 100, 40)
    return None


def shp_pharaoh_khopesh(u, v, s, L):
    """The Veiled Pharaoh's khopesh: a straight neck of gold, then the great sickle curve, its inner edge honed white."""
    tip = L + 1.5
    vl = v * s
    neck = tip * 0.42
    if 1.8 <= u <= neck and abs(v) <= 0.8:
        return (230, 186, 90) if vl > 0 else (150, 100, 40)
    if u > neck - 0.5:
        # sickle: a disc arc centred off the neck on +v, blade band between radii
        cu, cv = neck + (tip - neck) * 0.5, 2.6
        R = (tip - neck) * 0.62
        d = math.hypot((u - cu) / 1.05, v - cv)
        a = math.atan2(v - cv, u - cu)
        band = 3.0 * min(1.0, (0.7 - a) / 1.4)   # grows out of the neck, tapers to the hooked point
        if R - band <= d <= R and -2.95 <= a <= 0.7:
            if d > R - 0.9:
                return (255, 246, 220)            # the honed outer edge
            return (240, 196, 90) if d > R - 1.8 else (170, 120, 50)
    if 0.8 <= u < 1.8 and abs(v) <= 1.8:
        return (240, 196, 90) if vl > 0 else (150, 100, 40)
    if -3.4 <= u < 0.8 and abs(v) <= 0.72:
        return (60, 100, 210) if int(math.floor(u)) % 2 else (30, 50, 130)
    if -4.4 <= u < -3.4 and abs(v) <= 1.1:
        return (240, 196, 90)
    return None


# ---- daggers
def shp_barnacle_fang(u, v, s, L):
    """The Ferryman's knife: a curved fang of shell, crusted with barnacles, on a sea-green grip."""
    tip = L + 1.5
    c = 0.5 - 0.024 * max(0.0, u - 2) ** 2
    dv = v - c
    if 1.8 <= u <= tip:
        hw = _taper(u, tip, 0.9, 4.0)
        if abs(dv) <= hw:
            if (int(u * 1.3) * 5 + int(v * 2)) % 7 == 0 and u < tip - 3:
                return (120, 150, 130)            # barnacles
            return _band(dv * s, hw, (236, 222, 200), (190, 170, 146), (110, 96, 86), 0.2)
    if 0.8 <= u < 1.8 and abs(v - 0.5) <= 1.5:
        return (110, 150, 140)
    if -3.0 <= u < 0.8 and abs(v - 0.5) <= 0.72:
        return (60, 110, 100) if int(math.floor(u)) % 2 else (30, 60, 56)
    if -4.0 <= u < -3.0 and abs(v - 0.5) <= 1.1:
        return (236, 222, 200)
    return None


def shp_carving_knife(u, v, s, L):
    """The Butler's carving knife: a broad straight blade, spotless but for the red at its heel."""
    tip = L + 1.5
    if 1.8 <= u <= tip:
        top = 1.5 if u < tip - 3.5 else 1.5 * (tip - u) / 3.5 + 0.2
        if -0.7 <= v <= top:
            if u < 4.2 and v > 0.2 and int(u * 3) % 2:
                return (170, 30, 40)              # blood at the heel
            return (230, 234, 244) if v > top - 0.8 else ((170, 176, 196) if v * s > 0 else (100, 104, 124))
    if 0.8 <= u < 1.8 and abs(v) <= 1.3:
        return (150, 150, 160)
    if -3.4 <= u < 0.8 and abs(v) <= 0.8:
        if int(math.floor(u)) in (-2, 0) and abs(v) < 0.4:
            return (200, 200, 210)                # rivets
        return (40, 30, 34) if v * s > 0 else (20, 14, 18)
    return None


# ---- great weapons
def shp_tidecleaver(u, v, s, L):
    """A drowned headsman's cleaver dredged from the Barrows, crusted with barnacles and pale coral."""
    tip = L + 1.5
    if 2.6 <= u <= tip:
        if u > tip - (v + 2.0) * 0.5:
            return None
        if -2.0 <= v <= 2.6:
            if 2.6 - v < 0.9:
                return (206, 220, 222)            # edge
            k = (int(u * 1.4) * 7 + int(v * 1.7) * 3) % 9
            if k == 0:
                return (230, 200, 190)            # coral
            if k == 4:
                return (110, 140, 120)            # barnacle
            return (110, 130, 140) if v * s > 0.4 else ((74, 92, 104) if v * s > -1 else (44, 56, 66))
    if 0.8 <= u < 2.6 and abs(v) <= 3.4:
        return (90, 110, 120) if u < 1.7 else (44, 56, 66)
    if -5.0 <= u < 0.8 and abs(v) <= 0.75:
        return (60, 90, 90) if int(math.floor(u)) % 2 else (30, 46, 50)
    if -6.4 <= u < -5.0 and abs(v) <= 1.3:
        return (110, 130, 140)
    return None


def shp_vael_greatsword(u, v, s, L):
    """King Vael's greatsword: a blade of fused bone, ridged like a spine, a corroded gold guard with a skull;
    pale ghost-fire runs along its edges."""
    tip = L + 1.5
    vl = v * s
    if 2.6 <= u <= tip:
        hw = min(1.9, 0.5 + (tip - u) * 0.5)
        if abs(v) <= hw + 0.6:
            if abs(v) > hw:
                return (170, 220, 255) if (int(u * 2) + (v > 0)) % 3 else None   # ghost-fire edge
            iu = int(math.floor(u))
            if abs(v) < 0.6 and iu % 3 == 0 and u < tip - 3:
                return (120, 112, 100)            # vertebra ridge
            return _band(vl, hw, (236, 228, 204), (190, 180, 156), (120, 110, 96), 0.3)
    if 0.8 <= u < 2.6 and abs(v) <= 4.2:
        if abs(v) < 1.1 and u > 1.2:
            return (236, 228, 204) if vl > 0 else (150, 140, 120)      # skull at the guard
        return (200, 160, 70) if vl > 0 else (110, 90, 50)
    if -5.0 <= u < 0.8 and abs(v) <= 0.75:
        return (80, 50, 110) if int(math.floor(u)) % 2 else (40, 24, 60)   # purple-wrapped grip
    if -6.6 <= u < -5.0 and abs(v) <= 1.3:
        return (200, 160, 70) if vl > 0 else (110, 90, 50)
    return None


def shp_meteor_maul(u, v, s, L):
    """A maul whose head is a fist of fallen star: black iron split by white-blue light."""
    tip = L + 1.5
    h0 = tip - 7.0
    if h0 <= u <= tip:
        du = u - h0
        hw = 4.6 - 0.6 * abs(math.sin(du * 1.7 + (0.7 if v > 0 else 0)))
        if abs(v) <= hw:
            k = abs(((v * 1.1 - du * 1.3) % 4.2) - 2.1)
            if k < 0.35:
                return (230, 244, 255)
            if k < 0.8:
                return (110, 160, 255)
            if (int(u * 3) * 7 + int(v * 3) * 5) % 23 == 0:
                return (255, 255, 255)            # star specks
            return (60, 58, 76) if v * s > 0.8 else ((40, 38, 54) if v * s > -1.2 else (24, 22, 34))
    if -2.8 <= u < h0 and abs(v - 0.5) <= 0.75:
        return (100, 104, 124) if (v - 0.5) * s > 0 else (50, 52, 66)
    if -4.0 <= u < -2.8 and abs(v - 0.5) <= 1.25:
        return (110, 160, 255)
    return None


# ---- katanas
def shp_starblade(u, v, s, L):
    """Astrel's blade: black glass cracked with starlight, a silver tsuba."""
    tip = L + 1.5
    c = 0.5 - 0.0062 * max(0.0, u - 2) ** 2
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 0.85, 3.0)
        dv = v - c
        if abs(dv) <= hw:
            if dv > hw - 0.55:
                return (230, 240, 255)
            if (int(u * 2.3) * 3 + int(dv * 4)) % 11 == 0:
                return (255, 255, 255)
            if abs(((u * 0.9 + dv * 2) % 3.6) - 1.8) < 0.25:
                return (140, 180, 255)            # starlight cracks
            return (30, 30, 50) if dv * s > 0 else (14, 14, 28)
    if 1.0 <= u < 2.0 and abs(v - 0.5) <= 1.6:
        return (220, 226, 240) if v * s > 0 else (110, 116, 140)
    if -5.0 <= u < 1.0 and abs(v - 0.5) <= 0.75:
        return (200, 210, 240) if (int(math.floor(u)) + (v > 0.5)) % 2 else (24, 26, 50)
    if -6.0 <= u < -5.0 and abs(v - 0.5) <= 0.8:
        return (220, 226, 240)
    return None


def shp_plasma_katana(u, v, s, L):
    """A NEO-HALLOW blade: a black hilt throwing a sheet of magenta plasma with a white-hot core."""
    tip = L + 1.5
    if 2.0 <= u <= tip:
        hw = _taper(u, tip, 1.0, 2.5)
        if abs(v - 0.3) <= hw:
            d = abs(v - 0.3)
            return NEON[0] if d < 0.4 else (NEON[3] if d < hw - 0.5 else NEON[4])
    if 1.0 <= u < 2.0 and abs(v - 0.3) <= 1.4:
        return NEON[1]
    if -5.0 <= u < 1.0 and abs(v - 0.3) <= 0.75:
        if int(math.floor(u)) % 3 == 0:
            return NEON[1]
        return (40, 40, 52) if v * s > 0 else (18, 18, 26)
    if -6.0 <= u < -5.0 and abs(v - 0.3) <= 0.8:
        return (120, 124, 140)
    return None


# ---- whips: the handle (rigid, in the hand); the lash is drawn by render_whip
WHIP = {
    "headsman_chain": dict(grip=((70, 50, 40), (36, 26, 22)), ferrule=(150, 150, 160),
                           link=((170, 170, 184), (96, 96, 110), (46, 46, 56)), every=0, tip="hook"),
    "gravechain":     dict(grip=((120, 84, 56), (64, 44, 30)), ferrule=(150, 96, 60),
                           link=((176, 116, 72), (110, 70, 44), (60, 38, 28)), bone=(226, 216, 190), every=6, tip="skull"),
    "orrery_whip":    dict(grip=((60, 60, 90), (30, 30, 50)), ferrule=(230, 190, 90),
                           link=((255, 220, 120), (200, 150, 60), (120, 80, 30)), orb=(180, 220, 255), every=7, tip="star"),
}


def _shp_whip_handle(kind):
    sp = WHIP[kind]
    def f(u, v, s, L):
        if 1.6 <= u <= 3.2 and abs(v) <= 1.0:
            return sp["ferrule"]
        if -3.4 <= u < 1.6 and abs(v) <= 0.75:
            return sp["grip"][0] if (int(math.floor(u)) + (v > 0)) % 2 else sp["grip"][1]
        if -4.6 <= u < -3.4 and abs(v) <= 1.2:
            return sp["ferrule"]
        return None
    return f


shp_headsman_chain = _shp_whip_handle("headsman_chain")
shp_gravechain = _shp_whip_handle("gravechain")
shp_orrery_whip = _shp_whip_handle("orrery_whip")

for _k, _b in (("thornwood_staff", 12.0), ("sun_sceptre", 12.0)):
    STAFF_BACK[_k] = _b
for _k in ("antler_scythe", "briar_scythe", "crimson_scythe", "last_kindling"):
    STAFF_BACK[_k] = 6.0          # scythes share the staff haft path (both ends of the haft drawn)
    SCYTHE_BACK[_k] = 6.0
RASTER_POST["antler_scythe"] = _post_ribbon
LONGHAFT.update({"choir_harpoon": shp_choir_harpoon, "scarab_spear": shp_scarab_spear, "saint_lance": shp_saint_lance})

WPN.update({
    "antler_scythe":  (shp_antler_scythe, 22, 6.5, 13.0, "blade"),
    "briar_scythe":   (shp_briar_scythe, 21, 6.5, 12.0, "blade"),
    "crimson_scythe": (shp_crimson_scythe, 22, 6.5, 12.5, "blade"),
    "last_kindling":  (shp_last_kindling, 23, 6.5, 13.5, "blade"),
    "thornwood_staff": (shp_thornwood_staff, 17, 12.5, 2.0, "blade"),
    "sun_sceptre":    (shp_sun_sceptre, 17, 12.5, 4.5, "blade"),
    "choir_harpoon":  (shp_choir_harpoon, 20, SPEAR_BACK + 1.5, 3.2, "blade"),
    "scarab_spear":   (shp_scarab_spear, 20, SPEAR_BACK + 1.5, 2.4, "blade"),
    "saint_lance":    (shp_saint_lance, 21, SPEAR_BACK + 1.5, 2.4, "blade"),
    "sanguine_rapier": (shp_sanguine_rapier, 20, 5.0, 3.2, "blade"),
    "pharaoh_khopesh": (shp_pharaoh_khopesh, 18, 4.8, 6.0, "blade"),
    "barnacle_fang":  (shp_barnacle_fang, 10, 4.4, 2.2, "blade"),
    "carving_knife":  (shp_carving_knife, 11, 4.0, 2.0, "blade"),
    "tidecleaver":    (shp_tidecleaver, 24, 6.8, 3.6, "blade"),
    "vael_greatsword": (shp_vael_greatsword, 26, 7.0, 4.4, "blade"),
    "meteor_maul":    (shp_meteor_maul, 21, 4.4, 5.2, "maul"),
    "starblade":      (shp_starblade, 20, 6.2, 2.5, "blade"),
    "plasma_katana":  (shp_plasma_katana, 20, 6.2, 2.5, "blade"),
    "headsman_chain": (shp_headsman_chain, 3, 5.0, 1.4, "blade"),
    "gravechain":     (shp_gravechain, 3, 5.0, 1.4, "blade"),
    "orrery_whip":    (shp_orrery_whip, 3, 5.0, 1.4, "blade"),
})
V9_IDS = ["antler_scythe", "briar_scythe", "thornwood_staff", "choir_harpoon", "tidecleaver", "barnacle_fang",
          "sanguine_rapier", "carving_knife", "crimson_scythe", "vael_greatsword", "headsman_chain", "gravechain",
          "pharaoh_khopesh", "sun_sceptre", "scarab_spear", "starblade", "meteor_maul", "orrery_whip",
          "saint_lance", "plasma_katana", "last_kindling"]
WPN_IDS += V9_IDS
SMEAR.update({
    "antler_scythe":  ((210, 255, 200), (120, 230, 140), (50, 120, 70)),
    "briar_scythe":   ((236, 226, 206), (180, 150, 110), (110, 84, 60)),
    "crimson_scythe": P_BLOOD,
    "last_kindling":  ((255, 252, 240), (220, 230, 255), (150, 170, 220)),
    "thornwood_staff": ((210, 250, 190), (140, 200, 110), (80, 120, 60)),
    "sun_sceptre":    P_GOLD,
    "choir_harpoon":  ((210, 255, 250), (100, 230, 210), (40, 120, 120)),
    "scarab_spear":   ((220, 255, 200), (120, 220, 160), (40, 120, 90)),
    "saint_lance":    (NEON[0], NEON[1], NEON[3]),
    "sanguine_rapier": P_BLOOD,
    "pharaoh_khopesh": P_GOLD,
    "barnacle_fang":  ((236, 250, 246), (150, 200, 190), (70, 110, 110)),
    "carving_knife":  ((240, 244, 255), (168, 180, 214), (90, 98, 130)),
    "tidecleaver":    ((210, 240, 240), (120, 170, 180), (60, 90, 100)),
    "vael_greatsword": ((230, 244, 255), (150, 200, 255), (90, 110, 190)),
    "meteor_maul":    ((240, 248, 255), (130, 170, 255), (60, 70, 150)),
    "starblade":      ((255, 255, 255), (160, 190, 255), (70, 80, 170)),
    "plasma_katana":  (NEON[0], NEON[3], NEON[4]),
    "headsman_chain": ((230, 234, 244), (150, 156, 176), (80, 84, 100)),
    "gravechain":     ((244, 226, 200), (190, 140, 96), (110, 70, 44)),
    "orrery_whip":    ((255, 244, 200), (190, 220, 255), (120, 110, 180)),
})


# ---- whip lash: Catmull-Rom curve through control points, tapering, per-kind link pattern, tip ornament
def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 +
                        (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(2))


def lash_curve(pts, step=0.05):
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
        k = int(1 / step)
        for j in range(k):
            out.append(_cr(p0, p1, p2, p3, j / k))
    out.append(pts[-1])
    return out


def resample(curve, n):
    d = [0.0]
    for a, b in zip(curve, curve[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = d[-1] or 1.0
    out, j = [], 0
    for i in range(n):
        s_ = L * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s_:
            j += 1
        seg = (d[j + 1] - d[j]) or 1.0
        t = (s_ - d[j]) / seg
        a, b = curve[j], curve[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out, L


def draw_lash(g, pts, kind):
    sp = WHIP[kind]
    curve = lash_curve(pts)
    pts2, L = resample(curve, max(4, int(sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(curve, curve[1:])) * 2)))
    n = len(pts2)
    for i, (x, y) in enumerate(pts2):
        s_ = i / (n - 1) * L
        thick = s_ < L * 0.4
        c = sp["link"][0] if int(s_ / 1.5) % 2 == 0 else sp["link"][1]
        if sp.get("every") and int(s_) % sp["every"] == 0 and 3 < s_ < L - 3:
            c = sp.get("bone") or sp.get("orb")
        put(g, x, y, c)
        if thick:
            put(g, x, y + 1, sp["link"][2])
    tx, ty = pts2[-1]
    if L < 7:            # a stub (the rest of the lash is drawn in-engine): no ornament at the hand
        return (tx, ty)
    ax, ay = pts2[-1][0] - pts2[-3][0], pts2[-1][1] - pts2[-3][1]
    al = math.hypot(ax, ay) or 1
    ax, ay = ax / al, ay / al
    if sp["tip"] == "hook":      # the headsman's hook: a small curved blade
        for k in range(4):
            put(g, tx + ax * k, ty + ay * k, (200, 204, 220) if k < 3 else (240, 244, 255))
        for k in range(1, 4):
            put(g, tx + ax * 3 - ay * k * 0.9 - ax * k * 0.5, ty + ay * 3 + ax * k * 0.9 - ay * k * 0.5, (170, 174, 190))
    elif sp["tip"] == "skull":
        for a2, b2, c in ((0, 0, (226, 216, 190)), (1, 0, (226, 216, 190)), (0, 1, (160, 150, 130)), (1, 1, (40, 30, 30)),
                          (-1, 0, (190, 180, 156)), (0, -1, (236, 228, 204)), (1, -1, (236, 228, 204))):
            put(g, tx + a2, ty + b2, c)
    else:                        # a glass star orb
        for a2, b2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
            put(g, tx + a2, ty + b2, (255, 255, 255) if (a2, b2) == (0, 0) else sp["orb"])
        for a2, b2 in ((-1, 0), (2, 1), (0, -1), (1, 2)):
            put(g, tx + a2, ty + b2, (110, 160, 255))
    return (tx, ty)


def default_lash(tip, bxy):
    """A whip at rest: the lash hangs from the handle in a soft curve and trails along the floor behind."""
    x, y = tip
    if y > 30:   # handle held low: the lash just drops to the floor and trails back
        return [(x, y), (x - 1, min(38.5, y + 4)), (x - 5, 38.5), (x - 11, 38.5), (x - 16, 38.5)]
    return [(x, y), (x + 1.5, y + 5), (x + 1.0, y + 9.5), (x - 1.0, min(36.0, y + 13)), (x - 3.5, 38.5), (x - 9, 38.5),
            (x - 14, 38.5)]


def render_whip(w, kind, dust=True):
    info = {}
    g = draw_weapon(kind, w.hand, w.ang, w.slen, w.planted, w.held, w.fitb, info=info)
    a = math.radians(info["ang"])
    hx, hy = info["hand"]
    tip = (hx + math.cos(a) * 3.6, hy + math.sin(a) * 3.6)
    lash = [tip] + list(w.lash) if w.lash else default_lash(tip, w.bxy)
    fxg = blank()
    c0, c1, c2 = SMEAR[kind]
    span = lambda pts: sum(math.hypot(b2[0] - a2[0], b2[1] - a2[1]) for a2, b2 in zip(pts, pts[1:]))
    if w.lash_prev and w.lash and span([tip] + list(w.lash)) > 8 and span([tip] + list(w.lash_prev)) > 8:   # motion smear (not for stubs)
        prev = [tip] + list(w.lash_prev)
        A_, _ = resample(lash_curve(prev), 24)
        B_, _ = resample(lash_curve(lash), 24)
        for k, f in enumerate((0.33, 0.66)):
            mid = [(A_[i][0] + (B_[i][0] - A_[i][0]) * f, A_[i][1] + (B_[i][1] - A_[i][1]) * f) for i in range(24)]
            for i, (x, y) in enumerate(resample(lash_curve(mid), 60)[0]):
                if i > 8 and (int(x) + int(y) + k) % 2 == 0:
                    put(fxg, x, y, c2 if f < 0.5 else c1)
    if w.fx:
        extra = move_fx(kind, info, tuple(f for f in w.fx if f[0] not in ("arc", "sweep", "streak")), dust, w.fx_pal)
        for y in range(H):
            for x in range(W):
                if extra[y][x] is not None and fxg[y][x] is None:
                    fxg[y][x] = extra[y][x]
    lg = blank()
    draw_lash(lg, lash, kind)
    for y in range(H):
        for x in range(W):
            if lg[y][x] is not None:
                g[y][x] = lg[y][x]
    outline(g)
    if w.held:
        fx0, fy0 = int(round(w.hand[0])), int(round(w.hand[1]))
        for a2, b2 in FIST:
            if 0 <= fx0 + a2 < W and 0 <= fy0 + b2 < H:
                g[fy0 + b2][fx0 + a2] = None
    img = to_img(fxg)
    img.alpha_composite(to_img(g))
    w.info = info
    if w.mirror:
        m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        m.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT).crop((7, 0, W, H)), (0, 0))
        img = m
    if w.mask is not None:
        px, mk = img.load(), w.mask.load()
        for y in range(H):
            for x in range(W):
                if mk[x, y][3]:
                    px[x, y] = (0, 0, 0, 0)
    return img

# ---------------------------------------------------------------- v9 scythe: wide reaping arcs, the blade hooks foes toward you
GRIP_SCYTHE = 5.5


def sc_1():  # raise the scythe, bring it down in front and drag it back: the hook pulls
    return mseq([(dict(dx=-1, dy=1, hand=(30, 17), ang=-120, footB=(OX + 6, 39), flow=0.3), 70),
                 (dict(dx=1, hand=(34, 17), ang=-62, flow=0.7, flutter=1, fx=[sw(w=0.4)]), 45),
                 (dict(dx=3, dy=2, hand=(39, 24), ang=6, footF=(FF[0] + 3, 39), flow=1.1, flutter=2, fx=[sw(w=0.55)]), 45),
                 (dict(dx=1, dy=2, hand=(33, 26), ang=14, footB=(OX + 6, 39), footF=(FF[0] + 2, 39), flow=0.9, flutter=3,
                       fx=[("speed", (54, 30), 3, 10)]), 60),
                 (dict(dy=1, hand=(33, 26), ang=-18, flow=0.5, flutter=4), 90),
                 (dict(hand=(34, 26), ang=-40, flow=0.3), 90)], grip=GRIP_SCYTHE)


def sc_2():  # a full turn at the waist: the blade reaps round both sides
    RG = dict(sq=0.3, w=12.0)
    return mseq([(dict(dx=-1, dy=2, hand=(29, 27), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.3), 60),
                 (dict(dx=1, dy=2, hand=(34, 27), ang=2, footF=(FF[0] + 2, 39), flow=1.3, flutter=1,
                       fx=[("ring", (29, 28), 25, 180, 0, RG)]), 45),
                 (dict(dx=1, dy=2, hand=(34, 27), ang=2, footF=(FF[0] + 2, 39), flow=1.5, flutter=2, mirror=True, behind=True,
                       fx=[("ring", (29, 28), 25, 180, 0, RG)]), 45),
                 (dict(dx=2, dy=2, hand=(36, 27), ang=10, footF=(FF[0] + 3, 39), flow=1.3, flutter=3,
                       fx=[("ring", (29, 28), 25, 170, 10, RG)]), 60),
                 (dict(dx=1, dy=1, hand=(34, 27), ang=-10, flow=0.6, flutter=4), 100),
                 (dict(hand=(33, 26), ang=-30, flow=0.3), 90)], grip=GRIP_SCYTHE)


def sc_3():  # finisher: heave it high and reap straight down, the blade biting the floor
    return mseq([(dict(dy=1, hand=(31, 18), ang=-110, flow=0.3), 80),
                 (dict(dx=-1, hand=(29, 14), ang=-150, footB=(OX + 6, 39), flow=0.3, flutter=1), 100),
                 (dict(dx=-1, dy=-1, head_dx=-1, hand=(28, 13), ang=-168, footB=(OX + 6, 39), flow=0.2, flutter=2,
                       fx=[("glint", "tip")]), 130),
                 (dict(dx=1, dy=-1, hand=(33, 13), ang=-100, flow=0.7, flutter=3, fx=[sw(w=0.35)]), 40),
                 (dict(dx=3, dy=2, hand=(38, 19), ang=-30, footF=(FF[0] + 3, 39), flow=1.1, flutter=4, fx=[sw(w=0.5)]), 45),
                 (dict(dx=3, dy=4, head_dy=1, hand=(38, 26), ang=24, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.2, flutter=5,
                       fx=[sw(w=0.5), ("dust", 50, 5)]), 55),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 27), ang=26, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=0.6, flutter=6,
                       fx=[("dust", 51, 2)]), 180),
                 (dict(dx=1, dy=2, hand=(35, 27), ang=-10, flow=0.3), 140)], grip=GRIP_SCYTHE)


def sc_heavy():  # reaping sweep: wind the blade far back, then a huge arc over the top and through
    return mseq([(dict(dx=-1, dy=2, hand=(30, 29), ang=150, flow=0.3), 90),
                 (dict(dx=-2, dy=3, head_dx=-1, hand=(27, 26), ang=176, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.2,
                       flutter=1), 130),
                 (dict(dx=-3, dy=3, head_dx=-1, hand=(26, 24), ang=-170, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2,
                       flutter=2, fx=[("glint", "tip")]), 160),
                 (dict(dy=2, hand=(31, 21), ang=-100, flow=0.8, flutter=3, fx=[sw(w=0.4)]), 45),
                 (dict(dx=3, dy=1, hand=(38, 21), ang=-22, footF=(FF[0] + 3, 39), flow=1.3, flutter=4, fx=[sw(w=0.6)]), 50),
                 (dict(dx=4, dy=2, hand=(40, 25), ang=30, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.4, flutter=5,
                       fx=[sw(w=0.6)]), 55),
                 (dict(dx=4, dy=3, hand=(38, 27), ang=26, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=6,
                       fx=[("dust", 57, 4)]), 60),
                 (dict(dx=3, dy=4, head_dy=1, hand=(37, 28), ang=27, footB=(OX + 7, 39), footF=(FF[0] + 4, 39), flow=0.5,
                       flutter=7, fx=[("dust", 56, 2)]), 200),
                 (dict(dx=1, dy=1, hand=(34, 27), ang=-20, flow=0.3), 150)], grip=GRIP_SCYTHE)


# ---------------------------------------------------------------- v9 whip: the lash (pose-space control points) cracks at the tip
def wh_1():  # overhead-to-forward crack
    return mseq([(dict(dx=-1, hand=(30, 17), ang=-120, flow=0.3, lash=[(24, 12), (17, 14), (12, 20), (10, 27)]), 60),
                 (dict(dx=1, hand=(35, 19), ang=-60, flow=0.7, flutter=1, lash=[(33, 10), (26, 8), (20, 12), (16, 18)]), 40),
                 (dict(dx=2, hand=(40, 24), ang=-10, footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                       lash=[(47, 21), (54, 20), (59, 22), (62, 21)], fx=[("flare", (60, 21), 5)]), 45),
                 (dict(dx=2, hand=(39, 25), ang=10, footF=(FF[0] + 2, 39), flow=0.9, flutter=3,
                       lash=[(46, 25), (53, 27), (58, 30), (61, 33)]), 60),
                 (dict(dx=1, hand=(35, 27), ang=40, flow=0.5, flutter=4, lash=[(38, 31), (42, 36), (46, 38.5), (52, 38.5)]), 90),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 100)])


def wh_2():  # low backhand that rises into an overhead curl
    return mseq([(dict(dx=-1, dy=1, hand=(30, 30), ang=150, flow=0.3, lash=[(24, 34), (18, 37), (12, 38.5), (6, 38.5)]), 60),
                 (dict(dx=1, dy=1, hand=(34, 29), ang=100, flow=0.6, flutter=1, lash=[(33, 35), (38, 38), (45, 38.5), (51, 36)]), 40),
                 (dict(dx=2, hand=(39, 24), ang=-20, footF=(FF[0] + 2, 39), flow=1.0, flutter=2,
                       lash=[(47, 22), (54, 18), (59, 15), (62, 13)], fx=[("flare", (61, 13), 4)]), 45),
                 (dict(dx=2, hand=(38, 21), ang=-50, footF=(FF[0] + 2, 39), flow=0.9, flutter=3,
                       lash=[(44, 13), (49, 8), (55, 6), (60, 8)]), 55),
                 (dict(dx=1, hand=(35, 24), ang=-40, flow=0.5, flutter=4, lash=[(41, 18), (46, 20), (51, 26), (55, 33)]), 90),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 100)])


def wh_3():  # finisher: swing it round overhead, then crack it down on both sides
    return mseq([(dict(dy=1, hand=(33, 19), ang=-90, flow=0.3, lash=[(30, 10), (25, 13), (21, 20), (19, 27)]), 70),
                 (dict(dy=-1, hand=(33, 12), ang=-95, flow=0.6, flutter=1, lash=[(30, 5), (22, 4), (15, 7), (11, 13)]), 50),
                 (dict(dy=-1, hand=(34, 12), ang=-85, flow=0.7, flutter=2, lash=[(38, 4), (46, 3), (53, 5), (58, 10)]), 50),
                 (dict(dx=1, dy=2, hand=(36, 22), ang=-30, footF=(FF[0] + 2, 39), flow=1.1, flutter=3,
                       lash=[(44, 22), (51, 27), (57, 33), (61, 38)]), 45),
                 (dict(dx=1, dy=2, hand=(36, 22), ang=-30, footF=(FF[0] + 2, 39), flow=1.3, flutter=4, mirror=True,
                       lash=[(44, 24), (51, 30), (57, 35), (62, 38.5)], fx=[("dust", 60, 3)]), 45),
                 (dict(dx=2, dy=3, hand=(38, 27), ang=20, footF=(FF[0] + 3, 39), flow=1.2, flutter=5,
                       lash=[(45, 32), (52, 37), (58, 38.5), (63, 38.5)], fx=[("dust", 58, 4), ("flare", (61, 37), 4)]), 45),
                 (dict(dx=1, dy=2, hand=(36, 28), ang=40, flow=0.6, flutter=6, lash=[(40, 33), (45, 38.5), (51, 38.5), (57, 38.5)]), 120),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 110)])


def wh_heavy():  # chain throw: coil, fling it straight out, catch, and haul back hand over hand
    return mseq([(dict(dx=-1, dy=1, hand=(30, 18), ang=-130, flow=0.3, lash=[(28, 10), (22, 9), (19, 14), (22, 18)]), 90),
                 (dict(dx=-2, dy=2, head_dx=-1, hand=(28, 16), ang=-150, footB=(OX + 5, 39), flow=0.2, flutter=1,
                       lash=[(22, 10), (16, 12), (12, 18), (11, 25)], fx=[("glint", (29, 14))]), 130),
                 (dict(dx=1, dy=1, hand=(36, 20), ang=-40, flow=0.9, flutter=2, lash=[(40, 14), (46, 12), (52, 13), (57, 16)]), 40),
                 (dict(dx=3, dy=1, hand=(41, 23), ang=-4, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.3, flutter=3,
                       lash=[(48, 23), (54, 23), (59, 23), (63, 23)], fx=[("flare", (62, 23), 6), ("speed", (30, 18), 3, 10)]), 50),
                 (dict(dx=3, dy=1, hand=(41, 23), ang=-2, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.0, flutter=4,
                       lash=[(48, 24), (54, 25), (59, 25), (63, 24)]), 60),
                 (dict(dy=2, hand=(31, 24), ang=160, footB=(OX + 5, 39), flow=0.8, flutter=5, lash=[(40, 24), (48, 24), (55, 24), (60, 24)],
                       fx=[("speed", (58, 20), 3, 12)]), 70),
                 (dict(dx=-1, dy=2, hand=(28, 25), ang=170, footB=(OX + 5, 39), flow=0.6, flutter=6,
                       lash=[(36, 27), (42, 30), (47, 33), (50, 36)]), 80),
                 (dict(dy=1, hand=(33, 26), ang=-20, flow=0.4, flutter=7, lash=[(38, 33), (42, 38.5), (47, 38.5), (52, 38.5)]), 140),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 100)])


V9_MOVES = [("sc_1", sc_1), ("sc_2", sc_2), ("sc_3", sc_3), ("sc_heavy", sc_heavy),
            ("wh_1", wh_1), ("wh_2", wh_2), ("wh_3", wh_3), ("wh_heavy", wh_heavy)]
MOVE_CLASS.update({"sc": ("briar_scythe",), "wh": ("gravechain",)})
ACTIVE.update({"sc_1": (2, 3), "sc_2": (1, 3), "sc_3": (4, 5), "sc_heavy": (4, 6),
               "wh_1": (2, 3), "wh_2": (2, 3), "wh_3": (3, 5), "wh_heavy": (3, 4)})
HIT_X0.update({"sc_1": 0, "sc_3": -2, "sc_heavy": -6, "wh_1": 0, "wh_2": 0, "wh_heavy": 0})




# ---------------------------------------------------------------- v9 weapon arts (logic by agent G via ART_IMPL; release = ACTIVE[0])
P_GREEN = ((210, 255, 200), (120, 230, 140), (50, 120, 70))
P_TEAL = ((210, 255, 250), (100, 230, 210), (40, 120, 120))
P_STAR = ((255, 255, 255), (170, 200, 255), (80, 90, 180))
P_NEON = ((255, 255, 255), (255, 70, 200), (120, 255, 250))
P_PALE = ((255, 255, 250), (255, 240, 200), (170, 190, 240))


def art_reap():  # heave the scythe far back, then one enormous reaping cut into the ground
    return mseq([(dict(dy=1, hand=(31, 20), ang=-100, flow=0.3), 90),
                 (dict(dx=-1, dy=-1, hand=(30, 13), ang=-150, footB=(OX + 6, 39), flow=0.3, flutter=1, aura=1,
                       fx=[("glint", "tip")]), 120),
                 (dict(dx=-1, dy=-1, head_dx=-1, hand=(30, 11), ang=-178, footB=(OX + 5, 39), flow=0.2, flutter=2, aura=1), 70),
                 (dict(dx=1, dy=-1, hand=(33, 13), ang=-95, flow=0.8, flutter=3, fx=[sw(w=0.4)]), 40),
                 (dict(dx=3, dy=3, hand=(39, 22), ang=10, footF=(FF[0] + 3, 39), flow=1.3, flutter=4,
                       fx=[sw(w=0.7), ("flare", "tip", 7)]), 50),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=50, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=1.0, flutter=5,
                       fx=[sw(w=0.5), ("dust", 52, 7)]), 60),
                 (dict(dx=3, dy=5, head_dy=1, hand=(38, 28), ang=52, footB=(OX + 6, 39), footF=(FF[0] + 4, 39), flow=0.5, flutter=6,
                       fx=[("dust", 53, 3)]), 200),
                 (dict(dx=1, dy=2, hand=(35, 27), ang=-10, flow=0.3), 140)], grip=GRIP_SCYTHE, art=True)


def art_harvest_moon():  # draw the scythe far back, then one rising sweep that looses a crescent moon
    MOON = dict(sq=0.85, w=9.0, pal=P_GREEN)
    return mseq([(dict(dy=1, hand=(32, 25), ang=-30, flow=0.3), 90),
                 (dict(dx=-1, dy=3, hand=(29, 29), ang=160, footB=(OX + 5, 39), flow=0.3, flutter=1), 120),
                 (dict(dx=-2, dy=4, head_dx=-1, hand=(27, 29), ang=172, footB=(OX + 4, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=2,
                       aura=2, aura_pal=P_GREEN, fx=[("glint", "tip")]), 140),
                 (dict(dx=2, dy=1, hand=(38, 22), ang=-40, footF=(FF[0] + 3, 39), flow=1.4, flutter=3,
                       fx=[("ring", (31, 26), 24, 170, -40, MOON), ("flare", "tip", 6, P_GREEN)]), 50),
                 (dict(dx=2, dy=-1, hand=(35, 14), ang=-100, footB=(OX + 9, 38), footF=(FF[0] + 3, 39), flow=1.2, flutter=4,
                       fx=[("ring", (31, 26), 24, -40, -110, MOON)]), 70),
                 (dict(dx=1, hand=(33, 15), ang=-120, flow=0.6, flutter=5), 160),
                 (dict(dy=1, hand=(34, 26), ang=-30, flow=0.3), 130)], grip=GRIP_SCYTHE, art=True)

def art_lash():  # wind back, then the arm snaps out again and again (agent G draws the long lash to each crack)
    stub = lambda x, y: [(x, y), (x + 2, y)]
    return mseq([(dict(dx=-1, hand=(30, 17), ang=-120, flow=0.3, lash=[(24, 12), (17, 14), (12, 20), (10, 27)]), 80),
                 (dict(dx=-2, dy=1, head_dx=-1, hand=(28, 16), ang=-140, footB=(OX + 5, 39), flow=0.2, flutter=1, aura=1,
                       lash=[(22, 10), (15, 11), (10, 16), (8, 23)], fx=[("glint", (29, 14))]), 100),
                 (dict(dx=1, hand=(36, 22), ang=-6, footF=(FF[0] + 2, 39), flow=1.1, flutter=2, lash=stub(40, 21)), 45),
                 (dict(dx=1, hand=(35, 19), ang=-50, flow=0.9, flutter=3, lash=stub(37, 16)), 45),
                 (dict(dx=1, dy=1, hand=(36, 23), ang=6, footF=(FF[0] + 2, 39), flow=1.2, flutter=4, lash=stub(40, 24)), 45),
                 (dict(dx=1, hand=(35, 18), ang=-60, flow=0.9, flutter=5, lash=stub(37, 15)), 45),
                 (dict(dx=2, hand=(37, 22), ang=-4, footB=(OX + 7, 39), footF=(OX + 23, 39), flow=1.4, flutter=6, lash=stub(41, 22)), 50),
                 (dict(dx=1, hand=(35, 27), ang=40, flow=0.6, flutter=7, lash=[(38, 31), (42, 36), (46, 38.5), (52, 38.5)]), 110),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 100)], art=True)

def art_chain_drag():  # whirl the chain overhead, fling it (agent G draws it to the hook), haul the catch in, finish with a crack
    stub = lambda x, y: [(x, y), (x + 2, y)]
    return mseq([(dict(hand=(33, 16), ang=-100, flow=0.3, lash=[(28, 8), (34, 4), (40, 6), (42, 11)]), 80),
                 (dict(hand=(33, 15), ang=-95, flow=0.4, flutter=1, lash=[(36, 4), (28, 3), (22, 7), (20, 13)]), 80),
                 (dict(dx=-1, hand=(32, 15), ang=-100, flow=0.4, flutter=2, aura=1, lash=[(40, 6), (46, 4), (50, 8), (49, 13)],
                       fx=[("glint", (48, 12))]), 110),
                 (dict(dx=1, hand=(36, 22), ang=-4, footB=(OX + 6, 39), footF=(OX + 22, 39), flow=1.3, flutter=3, lash=stub(40, 22),
                       fx=[("speed", (26, 18), 4, 12)]), 45),
                 (dict(dx=1, hand=(36, 22), ang=-2, footB=(OX + 6, 39), footF=(OX + 22, 39), flow=1.0, flutter=4, lash=stub(40, 22)), 70),
                 (dict(dx=-1, dy=2, head_dx=-1, hand=(31, 23), ang=170, footB=(OX + 4, 39), flow=0.9, flutter=5, lash=stub(35, 23),
                       fx=[("speed", (52, 20), 3, 12)]), 70),
                 (dict(dx=3, dy=1, head_dx=1, hand=(39, 22), ang=-4, footB=(OX + 4, 37), footF=(OX + 16, 36), air=True, flow=1.8,
                       flutter=6, lash=stub(43, 22), fx=[("speed", (20, 17), 5, 16)]), 60),
                 (dict(dx=2, hand=(40, 24), ang=-10, footF=(FF[0] + 2, 39), flow=1.2, flutter=7,
                       lash=[(47, 21), (54, 20), (59, 22), (62, 21)], fx=[("flare", (61, 21), 7)]), 50),
                 (dict(dx=2, hand=(39, 25), ang=10, footF=(FF[0] + 2, 39), flow=0.9, flutter=8, lash=[(46, 25), (53, 27), (58, 30), (61, 33)]), 70),
                 (dict(dy=1, hand=(33, 26), ang=-20, flow=0.4, flutter=9, lash=[(38, 33), (42, 38.5), (47, 38.5), (52, 38.5)]), 140)], art=True)

def art_blood_frenzy():  # the blade raised before the face drinks the light, then a frenzy of thrusts
    thrust = lambda dx, hy, ang, n: dict(dx=dx, hand=(41, hy), ang=ang, footF=(FF[0] + 3, 39), flow=1.2, fx=[("streak", n)], fx_pal=P_BLOOD)
    back = dict(dx=1, hand=(35, 25), ang=-2, flow=0.8)
    return mseq([(dict(hand=(34, 22), ang=-92, off=(31, 26), flow=0.3), 90),
                 (dict(dy=1, hand=(34, 21), ang=-92, off=(31, 25), flow=0.2, flutter=1, aura=2, aura_pal=P_BLOOD,
                       fx=[("flare", "tip", 6, P_BLOOD)]), 140),
                 (dict(flutter=2, **thrust(3, 24, -4, 16)), 40), (dict(flutter=3, **back), 40),
                 (dict(flutter=4, **thrust(3, 20, -14, 16)), 40), (dict(flutter=5, **back), 40),
                 (dict(dy=1, flutter=6, **thrust(3, 27, 8, 16)), 40),
                 (dict(dx=4, dy=1, hand=(43, 24), ang=0, footB=(OX + 8, 39), footF=(OX + 25, 39), flow=1.5, flutter=7,
                       fx=[("streak", 22), ("flare", "tip", 7, P_BLOOD)], fx_pal=P_BLOOD), 60),
                 (dict(dx=1, hand=(35, 26), ang=-30, flow=0.4), 160)], art=True)


def art_tidal_surge():  # raise the harpoon high, hold, then drive it into the ground and loose a wave of black water
    return mseq([(dict(dx=-1, dy=1, hand=(31, 22), ang=-40, flow=0.3), 90),
                 (dict(dx=-1, hand=(30, 15), ang=-130, footB=(OX + 6, 39), flow=0.3, flutter=1), 90),
                 (dict(dx=-1, dy=-1, hand=(30, 14), ang=-150, footB=(OX + 6, 39), flow=0.3, flutter=2, aura=1, aura_pal=P_TEAL,
                       fx=[("glint", "tip")]), 130),
                 (dict(dx=1, hand=(34, 14), ang=-60, flow=0.8, flutter=3, fx=[sw(w=0.4)], fx_pal=P_TEAL), 45),
                 (dict(dx=3, dy=4, head_dy=1, hand=(40, 28), ang=30, footF=(FF[0] + 4, 39), flow=1.3, flutter=4,
                       fx=[("flare", (52, 36), 8, P_TEAL), ("dust", 50, 5), ("wave", (50, 26), 11, 7)], fx_pal=P_TEAL), 50),
                 (dict(dx=3, dy=4, head_dy=1, hand=(40, 28), ang=31, footF=(FF[0] + 4, 39), flow=0.9, flutter=5,
                       fx=[("wave", (56, 24), 13, 8)], fx_pal=P_TEAL), 80),
                 (dict(dx=3, dy=4, head_dy=1, hand=(40, 29), ang=32, footF=(FF[0] + 4, 39), flow=0.5, flutter=6), 200),
                 (dict(dx=1, dy=1, hand=(34, 26), ang=-10, flow=0.3), 140)], grip=GRIP_SPEAR, art=True)

def art_solar_flare():  # hold the blade up to the sun until it blazes, then bring the light down
    return mseq([(dict(hand=(33, 24), ang=-40, off=(30, 26), flow=0.3), 90),
                 (dict(dy=-1, hand=(33, 12), ang=-88, off=(31, 14), flow=0.2, flutter=1, aura=1, aura_pal=P_GOLD,
                       fx=[("flare", "tip", 7, P_GOLD)]), 140),
                 (dict(dy=-1, hand=(33, 12), ang=-88, off=(31, 14), flow=0.3, flutter=2, aura=2, aura_pal=P_GOLD,
                       fx=[("flare", "tip", 10, P_GOLD), ("rings", (35, 4), (6, 10))], fx_pal=P_GOLD), 70),
                 (dict(dx=3, dy=2, hand=(39, 24), ang=20, off=(30, 26), footF=(FF[0] + 3, 39), flow=1.3, flutter=3,
                       fx=[sw(w=0.6), ("flare", "tip", 6, P_GOLD)], fx_pal=P_GOLD), 50),
                 (dict(dx=3, dy=3, hand=(38, 28), ang=50, off=(30, 27), footF=(FF[0] + 3, 39), flow=0.9, flutter=4,
                       fx=[("embers", (48, 30), 5, 2)]), 70),
                 (dict(dx=3, dy=3, hand=(38, 28), ang=52, off=(30, 27), footF=(FF[0] + 3, 39), flow=0.5, flutter=5), 180),
                 (dict(dx=1, hand=(35, 26), ang=-30, off=(31, 26), flow=0.3), 140)], art=True)


def art_starfall():  # point the blade at the sky until a star answers, then cut it down
    return mseq([(dict(hand=(33, 24), ang=-40, flow=0.3), 90),
                 (dict(dx=-1, hand=(32, 14), ang=-90, flow=0.2, flutter=1, aura=1, aura_pal=P_STAR,
                       fx=[("glint", "tip"), ("flare", (32, 2), 4, P_STAR)]), 150),
                 (dict(dx=-1, hand=(32, 14), ang=-90, flow=0.3, flutter=2, aura=2, aura_pal=P_STAR,
                       fx=[("flare", (32, 2), 8, P_STAR)]), 70),
                 (dict(dx=3, dy=2, hand=(39, 24), ang=30, footF=(FF[0] + 3, 39), flow=1.3, flutter=3,
                       fx=[sw(w=0.55, a0=-90)], fx_pal=P_STAR), 50),
                 (dict(dx=3, dy=3, hand=(38, 28), ang=55, footF=(FF[0] + 3, 39), flow=0.9, flutter=4, fx=[("dust", 50, 4)]), 70),
                 (dict(dx=3, dy=3, hand=(38, 28), ang=56, footF=(FF[0] + 3, 39), flow=0.5, flutter=5), 180),
                 (dict(dx=1, hand=(34, 26), ang=-35, flow=0.3), 140)], grip=GRIP_KATANA, art=True)


def art_overclock():  # crouch, then a glitching dash (frames 2-3 while dashing) that ends in a flicked cut
    dash = dict(dx=4, dy=3, head_dx=2, hand=(30, 29), ang=172, off=(36, 26), footB=(OX + 2, 37), footF=(OX + 13, 36), air=True, flow=2.0,
                aura=1, aura_pal=P_NEON)
    return mseq([(dict(dx=-1, dy=3, hand=(30, 29), ang=168, off=(32, 28), footB=(OX + 5, 39), flow=0.3), 70),
                 (dict(dx=-1, dy=4, head_dy=1, hand=(30, 29), ang=170, off=(32, 28), footB=(OX + 5, 39), flow=0.2, flutter=1,
                       aura=1, aura_pal=P_NEON, fx=[("flare", "tip", 5, P_NEON)]), 120),
                 (dict(flutter=2, fx=[("speed", (18, 18), 6, 20, P_NEON)], **dash), 50),
                 (dict(flutter=5, fx=[("speed", (16, 19), 6, 18, P_NEON)], **{**dash, "footB": (OX + 4, 36), "footF": (OX + 11, 37)}), 50),
                 (dict(dx=2, dy=1, hand=(37, 17), ang=-80, off=(30, 26), footF=(FF[0] + 2, 39), flow=1.0, flutter=6,
                       fx=[sw(w=0.4), ("flare", "tip", 6, P_NEON)], fx_pal=P_NEON), 60),
                 (dict(dx=1, hand=(36, 25), ang=30, off=(30, 26), flow=0.7, flutter=7, fx=[sw(w=0.4)], fx_pal=P_NEON), 80),
                 (dict(hand=(35, 27), ang=-45, flow=0.3), 120)], art=True)

def art_pale_pyre():  # raise the scythe, then plant it upright: a ring of pale fire answers from the ground
    plant = dict(dx=1, dy=1, hand=(35, 25), ang=-90, off=(33, 29))
    return mseq([(dict(hand=(33, 22), ang=-60, flow=0.3), 90),
                 (dict(dy=-1, hand=(32, 14), ang=-100, flow=0.2, flutter=1, aura=1, aura_pal=P_PALE, fx=[("glint", "tip")]), 140),
                 (dict(dy=-2, hand=(33, 12), ang=-96, flow=0.3, flutter=2, aura=2, aura_pal=P_PALE), 60),
                 (dict(flow=1.2, flutter=3, fx=[("flare", (35, 37), 9, P_PALE), ("dust", 35, 6), ("rings", (35, 34), (6, 10))],
                       fx_pal=P_PALE, **plant), 50),
                 (dict(flow=0.8, flutter=4, fx=[("rings", (35, 34), (11, 16))], fx_pal=P_PALE, **plant), 90),
                 (dict(flow=0.5, flutter=5, fx=[("rings", (35, 34), (16, 22))], fx_pal=P_PALE, **plant), 200),
                 (dict(dy=1, hand=(34, 26), ang=-40, flow=0.3), 140)], grip=GRIP_SCYTHE, art=True)


V9_ARTS = [("art_reap", art_reap), ("art_harvest_moon", art_harvest_moon), ("art_lash", art_lash),
           ("art_chain_drag", art_chain_drag), ("art_blood_frenzy", art_blood_frenzy), ("art_tidal_surge", art_tidal_surge),
           ("art_solar_flare", art_solar_flare), ("art_starfall", art_starfall), ("art_overclock", art_overclock),
           ("art_pale_pyre", art_pale_pyre)]
ACTIVE.update({"art_reap": (4, 4), "art_harvest_moon": (3, 3), "art_lash": (2, 2), "art_chain_drag": (3, 3),
               "art_blood_frenzy": (2, 2), "art_tidal_surge": (4, 4), "art_solar_flare": (3, 3), "art_starfall": (3, 3),
               "art_overclock": (2, 2), "art_pale_pyre": (3, 3)})




# ---------------------------------------------------------------- v9b Tidebreath swimming (agent B's physics picks these up)
class XformWpn(RotWpn):
    """Weapon cel of a turned frame (swimming): the same rotate-about-a-point + shift as the body layers."""
    def __init__(self, inner, ang, center, off):
        self.inner, self.ang, self.center, self.off = inner, ang, center, off

    def render(self, kind, dust=True, extras=True):
        return self.inner.render(kind, dust, extras).rotate(self.ang, resample=Image.NEAREST, center=self.center, translate=self.off)


def xform_frame(cels, ang, center, off):
    out = {}
    for n, c in cels.items():
        if isinstance(c, (Wpn, RotWpn)):
            out[n] = XformWpn(c, ang, center, off)
        else:
            img = c if isinstance(c, Image.Image) else to_img(c)
            out[n] = img.rotate(ang, resample=Image.NEAREST, center=center, translate=off)
    return out


def swim():  # side stroke under water: the far arm reaches and pulls, the weapon rides along the body, legs scissor, cape trailing
    """Posed upright, then the body layers are turned a lossless 90 degrees (head forward); the weapon is drawn
    directly in the turned frame (crisp, along the body, pointing back)."""
    reach = [(28, 11), (31, 13), (32, 18), (30, 23), (27, 20), (26, 14)]
    C = (28, 24)
    out = []
    for k in range(6):
        t = k / 6 * 2 * math.pi
        bob = [0, 0, 1, 1, 1, 0][k]
        off = (1, 6 + bob)
        T = lambda x, y: (C[0] - (y - C[1]) + off[0], C[1] + (x - C[0]) + off[1])   # upright -> turned (clockwise 90)
        hand, ang = (31, 30), 92 + 3 * math.sin(t)
        p = dict(hand=hand, ang=ang, off=reach[k], sword=False,
                 footB=(OX + 9 + 3.0 * math.sin(t), 39), footF=(OX + 17 - 3.0 * math.sin(t), 38), bendB=1, bendF=-1)
        cels = pose({**dict(footB=FB, footF=FF), **p})
        cels["Cape"] = draw_streamer((OX + 9, OY + 11), 96, 19, 5, 9, k * 1.05, amp=1.4, k=0.6)
        cels = xform_frame(cels, -90, C, off)
        cels["Head"] = to_img(draw_helmet(OX + 13, OY + 12 + bob))   # the head lifts to look ahead (not turned face-down)
        hs = T(*hand)
        w = Wpn(hs, ang + 90, 16, fitb=False)
        w.cels, w.bxy = cels, (0, 0)
        w.shield = ((26.5, 24.0 + off[1] - 6), 90, 0.78, "behind")                     # slung on the back, which faces up
        w.offw = (T(*reach[k]), -10 + 20 * math.sin(t), 13, False)                     # a twin's second blade in the stroking hand
        tipx, tipy = hs[0] - 4, hs[1]
        w.lash = [(tipx - 5, tipy + 1 + math.sin(t)), (tipx - 10, tipy + math.sin(t + 1)), (tipx - 15, tipy + 1 + math.sin(t + 2)),
                  (tipx - 19, tipy + math.sin(t + 3))]                                   # a whip's lash trails in the current
        cels["Sword"] = w
        out.append((cels, 85))
    return out


def tread():  # treading water at the surface: upright, legs kicking below, the free hand sculling, cape afloat behind
    rows = [(0, (22, 26), (OX + 8, 38), (OX + 18, 36), 40), (1, (24, 27), (OX + 10, 36), (OX + 16, 38), 44),
            (1, (22, 28), (OX + 8, 38), (OX + 18, 36), 40), (0, (20, 27), (OX + 6, 37), (OX + 20, 38), 36)]
    out = []
    for i, (dy, off, fb, ff, ang) in enumerate(rows):
        cels = pose({**dict(footB=FB, footF=FF), **dict(dy=dy, hand=(33, 29), ang=ang, slen=16, off=off, footB=fb, footF=ff,
                                                        bendB=1, bendF=1, air=True)})
        cels["Cape"] = draw_streamer((OX + 9, OY + 12 + dy), 174, 17, 5, 8, i * 1.5, amp=1.0, k=0.7)
        out.append((cels, 115))
    return out


V9_SWIM = [("swim", swim), ("tread", tread)]


# ================================================================ v10 (weapon feel): every class's own up / air / down attacks
# Appended after the v9 swim frames. Tags <prefix>_up / _air / _down; the engine picks them through moveset() (MOVESETS[cls].up/
# air/down) and falls back to the sword's attack_up / air_attack / attack_down. Down attacks all pogo (engine: ATK flag `down`).
AIRB = dict(dy=-3, **TUCK)          # airborne base: body lifted, knees pulled up
LEGS_BACK = dict(footB=(OX + 6, 31), footF=(OX + 10, 33), bendB=-1, bendF=-1)   # diving: legs swept back behind


def DIVE(ln, k=0, x0=20, x1=41, y=24):
    """Wind lines streaming up either side of a plunging body (pose space; never across the knight)."""
    return [("vspeed", (x0 - k, y + k), 2, ln), ("vspeed", (x1 + k, y - 2 + k), 2, ln - 2)]


def cape_dive(frames, idx, dy=-4, x=OX + 9):
    """Plunging frames: the cape is torn upward behind the shoulders (as slam_dive)."""
    for n, i in enumerate(idx):
        frames[i][0]["Cape"] = draw_streamer((x, OY + 12 + dy), 250 + 5 * (n % 2), 14, 5, 9, 0.8 + n * 1.7, amp=1.1, k=0.7)
    return frames


def cape_trail(frames, idx, dy=-3, ang=176):
    """Fast airborne frames: the cape streams flat behind."""
    for n, i in enumerate(idx):
        frames[i][0]["Cape"] = draw_streamer((OX + 9, OY + 11 + dy), ang - 3 * n, 20, 5, 8, 0.6 + n * 1.9, amp=1.0, k=0.65)
    return frames


# ---------------------------------------------------------------- dagger: flip-stab, quick jab, reverse-grip dive
def dg_up():  # dip, then spring onto the toes and jab straight up
    return mseq([(dict(dy=2, hand=(31, 28), ang=-40, off=(33, 26), footB=(OX + 7, 39), flow=0.3), 50),
                 (dict(dy=1, hand=(33, 22), ang=-78, off=(30, 26), flow=0.5, flutter=1, fx=[sw(w=0.4)]), 35),
                 (dict(dy=-1, hand=(33, 13), ang=-88, off=(26, 24), footB=(OX + 9, 37), flow=0.9, flutter=2, fx=[("streak", 12)]), 50),
                 (dict(dy=-1, hand=(33, 12), ang=-86, off=(26, 24), footB=(OX + 9, 37), flow=0.8, flutter=3, fx=[("streak", 6)]), 60),
                 (dict(hand=(34, 19), ang=-70, off=(29, 25), flow=0.5, flutter=4), 70),
                 (dict(hand=(35, 26), ang=-45, off=(31, 26), flow=0.3), 80)])


def dg_air():  # tuck, a forward flip with the blade leading the turn, and a stab out of it
    fr = mseq([(dict(dy=-3, head_dy=1, hand=(30, 20), ang=-150, off=(32, 25), flow=0.8, **TUCK), 45)])
    cy = 25.0
    w = Wpn((38.5, 30.5), 35, 18, fitb=True)
    w.fx = (("ring", (31.5, cy), 12.0, -150, 40, dict(sq=1.0, w=3.2)),)
    fr.append(({"Cape": cape_swirl(250, 31.5, cy), "Torso": roll_ball(95, cy=cy), "Sword": w}, 50))
    fr += mseq([(dict(dy=-2, hand=(41, 29), ang=28, off=(22, 22), footB=(OX + 6, 33), footF=(OX + 14, 35), air=True,
                      flow=1.4, flutter=2, fx=[("streak", 14)]), 45),
                (dict(dy=-2, hand=(41, 29), ang=30, off=(23, 23), footB=(OX + 6, 34), footF=(OX + 14, 36), air=True,
                      flow=1.1, flutter=3, fx=[("streak", 6)]), 60),
                (dict(dy=-3, hand=(35, 26), ang=-30, off=(31, 26), flow=0.6, flutter=4, **AIR), 90)])
    return cape_trail(fr, [2, 3])


def dg_down():  # reverse grip: the fist rises in front, then both hands drive the blade down under the feet
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-5, head_dy=0, hand=(37, 18), ang=95, off=(33, 19), flow=0.9, footB=(OX + 9, 34), footF=(OX + 17, 34)), 50),
               (dict(hand=(34, 29), ang=90, off=(33, 27), flow=1.3, flutter=1, fx=[("streak", 10)] + DIVE(9)), 45),
               (dict(dy=-3, hand=(34, 29), ang=90, off=(33, 27), flow=1.5, flutter=3, fx=DIVE(7, 1)), 55),
               (dict(hand=(34, 29), ang=91, off=(33, 27), flow=1.3, flutter=5), 60),
               (dict(dy=-3, head_dy=0, hand=(35, 25), ang=-20, off=(31, 26), flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- great: an overhead cleave that hangs, a great rising arc, a plunge
def gs_up():  # sink with the blade trailing low behind, then one great arc from the floor to the sky
    return mseq([(dict(dx=-1, dy=3, hand=(31, 31), ang=150, footB=(OX + 6, 39), flow=0.3), 100),
                 (dict(dx=-1, dy=4, head_dy=1, hand=(30, 31), ang=160, footB=(OX + 6, 39), footF=(FF[0] + 1, 39), flow=0.2, flutter=1,
                       fx=[("glint", "tip")]), 120),
                 (dict(dx=1, dy=1, hand=(37, 26), ang=-20, footF=(FF[0] + 2, 39), flow=0.9, flutter=2,
                       fx=[("arc", (30, 24), 140, -20, dict(sq=0.9, w=0.6))]), 45),
                 (dict(dx=1, dy=-2, hand=(34, 13), ang=-92, slen=16, footB=(OX + 9, 37), flow=1.2, flutter=3, fx=[sw(w=0.55)]), 55),
                 (dict(dy=-1, hand=(29, 13), ang=-135, flow=0.8, flutter=4, fx=[sw(w=0.35)]), 110),
                 (dict(dy=1, hand=(31, 19), ang=-120, flow=0.4, flutter=5), 120),
                 (dict(dy=1, hand=(33, 25), ang=-70, flow=0.3), 110)], grip=GRIP_GREAT)


def gs_air():  # heave it overhead and hang there a beat (the engine stalls the rise), then cleave down in front
    return mseq([(dict(hand=(30, 17), ang=-120, flow=0.8), 70),
                 (dict(head_dx=-1, hand=(28, 14), ang=-165, flow=1.0, flutter=1, fx=[("glint", "tip")]), 110),
                 (dict(hand=(32, 13), ang=-100, flow=0.6, flutter=2, fx=[sw(w=0.35)]), 45),
                 (dict(dx=1, hand=(38, 21), ang=-15, slen=16, flow=0.9, flutter=3, fx=[sw(w=0.55)]), 50),
                 (dict(dx=2, hand=(38, 28), ang=45, flow=1.1, flutter=4, fx=[sw(w=0.5)], **AIR), 70),
                 (dict(dx=1, hand=(36, 29), ang=60, flow=0.7, flutter=5, **AIR), 110),
                 (dict(hand=(34, 26), ang=20, flow=0.4, **AIR), 100)], dict(dy=-4, **TUCK), grip=GRIP_GREAT)


def gs_down():  # lift the blade point-down before you, then drive it under the feet with both hands
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-6, head_dy=0, hand=(36, 17), ang=80, slen=13, flow=0.9, footB=(OX + 9, 34), footF=(OX + 17, 34)), 90),
               (dict(hand=(34, 27), ang=90, slen=16, flow=1.3, flutter=1, fx=[("streak", 12)] + DIVE(10)), 50),
               (dict(dy=-3, hand=(34, 27), ang=90, slen=16, flow=1.5, flutter=3, fx=DIVE(8, 1)), 60),
               (dict(hand=(34, 27), ang=90, slen=16, flow=1.3, flutter=5), 70),
               (dict(dy=-3, head_dy=0, hand=(35, 25), ang=30, flow=0.7, flutter=4, **AIR), 120)], base, grip=GRIP_GREAT)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- spear: skyward thrust, a flat air thrust, tip-first dive
def sp_up():  # coil low with the spear raised, then drive it straight at the sky with both hands
    return mseq([(dict(dx=-1, dy=3, hand=(30, 29), ang=-70, footB=(OX + 6, 39), flow=0.3), 80),
                 (dict(dy=-1, hand=(33, 14), ang=-88, footB=(OX + 9, 37), flow=0.9, flutter=1, fx=[("streak", 18)]), 45),
                 (dict(dy=-2, hand=(33, 13), ang=-89, footB=(OX + 9, 36), footF=(FF[0], 38), flow=1.0, flutter=2, fx=[("streak", 8)]), 60),
                 (dict(hand=(33, 18), ang=-86, flow=0.6, flutter=3), 90),
                 (dict(hand=(34, 24), ang=-62, flow=0.4, flutter=4), 70),
                 (dict(hand=(35, 27), ang=-48, flow=0.3), 60)], grip=GRIP_SPEAR)


def sp_air():  # draw the spear back along the body, then a flat thrust at full stretch
    stretch = dict(dx=2, hand=(40, 24), footB=(OX + 5, 34), footF=(OX + 13, 36))
    fr = mseq([(dict(dx=-2, hand=(27, 23), ang=-4, flow=0.6), 70),
               (dict(ang=0, flow=1.4, flutter=1, fx=[("streak", 22)], **stretch), 45),
               (dict(ang=0, flow=1.2, flutter=2, fx=[("streak", 10)], **stretch), 60),
               (dict(hand=(34, 24), ang=-4, flow=0.7, flutter=3), 90),
               (dict(hand=(34, 26), ang=-20, flow=0.4, **AIR), 80)], AIRB, grip=GRIP_SPEAR)
    return cape_trail(fr, [1, 2])


def sp_down():  # turn the spear tip-down before you and ride it down
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-6, head_dy=0, hand=(35, 16), ang=86, flow=0.9, footB=(OX + 9, 34), footF=(OX + 17, 34)), 60),
               (dict(hand=(34, 26), ang=90, flow=1.3, flutter=1, fx=[("streak", 14)] + DIVE(10), **LEGS_BACK), 45),
               (dict(dy=-3, hand=(34, 26), ang=90, flow=1.5, flutter=3, fx=DIVE(8, 1), **LEGS_BACK), 55),
               (dict(hand=(34, 26), ang=90, flow=1.3, flutter=5, **LEGS_BACK), 60),
               (dict(dy=-3, head_dy=0, hand=(34, 25), ang=-10, flow=0.7, flutter=4, **AIR), 90)], base, grip=GRIP_SPEAR)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- katana: rising crescent, iaido air draw, one-handed stab down
def kt_up():  # from low at the hip, a rising crescent that ends pointing at the sky
    return mseq([(dict(dx=-1, dy=2, hand=(31, 31), ang=140, footB=(OX + 6, 39), flow=0.3), 70),
                 (dict(dy=1, hand=(35, 30), ang=100, flow=0.5, flutter=1), 35),
                 (dict(dx=1, dy=-1, hand=(38, 20), ang=-40, footB=(OX + 9, 37), flow=1.0, flutter=2,
                       fx=[("arc", (30, 22), 110, -40, dict(sq=1.0, w=0.4))]), 45),
                 (dict(dx=1, dy=-2, hand=(33, 12), ang=-100, footB=(OX + 9, 36), flow=1.1, flutter=3, fx=[sw(w=0.4)]), 55),
                 (dict(hand=(30, 14), ang=-130, flow=0.6, flutter=4), 90),
                 (dict(hand=(35, 26), ang=-45, flow=0.3), 90)], grip=GRIP_KATANA)


def kt_air():  # iaido in the air: sheathed at the hip, then one flash of a draw-cut
    fr = mseq([(dict(hand=(30, 28), ang=168, off=(32, 27), sheath=True, flow=0.7), 80),
               (dict(dx=1, hand=(33, 26), ang=-172, off=(31, 27), flow=0.6, flutter=1), 30),
               (dict(dx=3, hand=(40, 24), ang=-4, off=(24, 25), flow=1.4, flutter=2,
                     fx=[("flash", 21, 6, 62), ("arc", (31, 26), 172, -4, dict(sq=0.35, w=0.3))]), 45),
               (dict(dx=3, hand=(40, 20), ang=-36, off=(24, 25), flow=1.2, flutter=3, fx=[("flash", 21, 16, 52), sw(w=0.35)]), 55),
               (dict(dx=2, hand=(38, 17), ang=-50, off=(25, 25), flow=0.8, flutter=4), 100),
               (dict(hand=(35, 26), ang=-40, off=(30, 26), flow=0.4, **AIR), 90)], AIRB)
    return cape_trail(fr, [2, 3])


def kt_down():  # one arm driven straight down, the blade a needle under the feet; the free arm flung up behind
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-6, head_dy=0, hand=(36, 17), ang=82, slen=14, off=(30, 22), flow=0.9, footB=(OX + 9, 34),
                     footF=(OX + 17, 34)), 50),
               (dict(hand=(33, 31), ang=90, slen=16, off=(19, 14), flow=1.3, flutter=1, fx=[("streak", 12)] + DIVE(9)), 40),
               (dict(dy=-3, hand=(33, 31), ang=90, slen=16, off=(19, 15), flow=1.5, flutter=3, fx=[("glint", "tip")] + DIVE(7, 1)), 55),
               (dict(hand=(33, 31), ang=90, slen=16, off=(20, 16), flow=1.3, flutter=5), 60),
               (dict(dy=-3, head_dy=0, hand=(35, 26), ang=-40, off=(30, 26), flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- staff: an overhead twirl, an air wheel, a pole-vault stomp
def st_up():  # hoist the staff overhead and spin it flat, like a rotor: both ends cut the air above you
    RG = dict(sq=0.32, w=2.6)
    ring = lambda a: ("ring", (32.5, 12), 15.5, a - 260, a, RG)
    top = dict(dy=-1, hand=(32, 12), footB=(OX + 8, 38))
    return mseq([(dict(dy=1, hand=(31, 19), ang=-150, flow=0.3), 55),
                 (dict(ang=-4, flow=0.8, flutter=1, fx=[ring(0)], **top), 40),
                 (dict(ang=-2, slen=8, flow=1.0, flutter=2, fx=[ring(90)], **top), 40),
                 (dict(ang=-176, flow=1.0, flutter=3, fx=[ring(180)], **top), 40),
                 (dict(ang=-178, slen=8, flow=0.9, flutter=4, fx=[ring(270)], **top), 45),
                 (dict(hand=(33, 19), ang=-100, flow=0.5, flutter=5), 80),
                 (dict(hand=(33, 26), ang=-40, flow=0.3), 80)], grip=GRIP_STAFF)


def st_air():  # an air wheel: the staff turns a full circle before you, the far end cutting behind
    P0 = (34, 22)
    wheel = lambda a0, a1: [("ring", (P0[0] + 1, P0[1]), 15.5, a0, a1, dict(sq=1.0, w=3.4))]
    return mseq([(dict(hand=(31, 22), ang=-150, flow=0.6), 45),
                 (dict(dx=1, hand=P0, ang=-70, flow=0.9, flutter=1, fx=wheel(-150, -70)), 40),
                 (dict(dx=1, hand=P0, ang=10, flow=1.1, flutter=2, fx=wheel(-70, 10)), 40),
                 (dict(dx=1, hand=P0, ang=90, flow=1.2, flutter=3, fx=wheel(10, 90)), 40),
                 (dict(dx=1, hand=P0, ang=170, flow=1.1, flutter=4, fx=wheel(90, 170)), 45),
                 (dict(hand=(33, 25), ang=-20, flow=0.5, **AIR), 90)], AIRB, grip=GRIP_STAFF)


def st_down():  # plant the staff under you like a vaulting pole and stomp down along it, feet together
    base = dict(dy=-4, **TUCK)
    stomp = dict(footB=(OX + 12, 36), footF=(OX + 16, 37))
    fr = mseq([(dict(dy=-6, hand=(34, 17), ang=80, slen=20, flow=0.9, footB=(OX + 9, 34), footF=(OX + 17, 34)), 55),
               (dict(dy=-5, hand=(33, 21), ang=90, slen=22, flow=1.3, flutter=1, fx=[("streak", 10)] + DIVE(9), **stomp), 45),
               (dict(dy=-4, hand=(33, 21), ang=90, slen=22, flow=1.5, flutter=3, fx=DIVE(7, 1), **stomp), 55),
               (dict(dy=-4, hand=(33, 21), ang=90, slen=22, flow=1.3, flutter=5, **stomp), 60),
               (dict(dy=-3, hand=(33, 25), ang=-20, flow=0.7, flutter=4, **AIR), 90)], base, grip=GRIP_STAFF)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- sword & shield: a shielded undercut, an upward bash, shield-surf
def sh_up():  # shield punched up over the head, tilted forward; the blade thrusts up behind its rim
    tilt = dict(rot=65, sx=0.5, oy=-1, layer="over")
    return mseq([(dict(dy=2, hand=(31, 27), ang=-70, off=(34, 24), footB=(OX + 7, 39), flow=0.3, shield=HIP), 55),
                 (dict(dy=-1, hand=(31, 15), ang=-84, off=(34, 11), footB=(OX + 9, 37), flow=0.9, flutter=1, shield=tilt, behind=True,
                       fx=[("flare", (38, 1), 4), ("streak", 8)]), 45),
                 (dict(dy=-1, hand=(31, 14), ang=-86, off=(34, 11), footB=(OX + 9, 37), flow=0.8, flutter=2, shield=tilt, behind=True), 60),
                 (dict(hand=(33, 20), ang=-70, off=(34, 19), flow=0.5, flutter=3, shield=dict(rot=35, sx=0.55)), 80),
                 (dict(hand=(34, 27), ang=-35, off=(32, 25), flow=0.3), 80)])


def sh_air():  # shield raised before the face, the blade sweeps low beneath its rim
    guard = dict(off=(36, 19), shield=dict(sx=0.62))
    return mseq([(dict(hand=(28, 28), ang=170, off=(33, 22), flow=0.6, shield=HIP), 50),
                 (dict(hand=(32, 29), ang=150, flow=0.8, flutter=1, fx=[sw(w=0.35)], **guard), 35),
                 (dict(dx=1, hand=(40, 27), ang=5, flow=1.2, flutter=2, fx=[sw(w=0.5)], **guard), 45),
                 (dict(dx=1, hand=(39, 23), ang=-35, flow=1.0, flutter=3, fx=[sw(w=0.45)], **guard), 60),
                 (dict(hand=(35, 26), ang=-25, off=(32, 25), flow=0.5, **AIR), 90)], AIRB)


def sh_down():  # flip the shield under your feet and ride it down like a sled
    base = dict(dy=-4, head_dy=1, **TUCK)
    surf = dict(hand=(33, 17), ang=-130, off=(22, 21), footB=(OX + 10, 34), footF=(OX + 18, 34),
                shield=dict(abs=(31.5, 40.5), rot=90, sx=0.45, layer="front"))
    fr = mseq([(dict(dy=-5, hand=(33, 18), ang=-110, off=(32, 28), flow=0.8, shield=dict(rot=55, sx=0.5)), 55),
               (dict(flow=1.3, flutter=1, fx=DIVE(9, 0, 18, 44), **surf), 45),
               (dict(dy=-3, flow=1.5, flutter=3, fx=DIVE(7, 1, 18, 44), **surf), 55),
               (dict(flow=1.3, flutter=5, **surf), 60),
               (dict(dy=-3, head_dy=0, hand=(35, 26), ang=-30, off=(32, 25), flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- twin blades: scissor up-cut, an X in the air, a crossed drill
def tw_up():  # both blades low, then scissored up past each other over the head
    return mseq([(dict(dy=2, hand=(33, 30), ang=50, offw=((31, 30), 70), footB=(OX + 7, 39), flow=0.3), 50),
                 (dict(dy=1, hand=(37, 24), ang=-30, offw=((35, 26), -10, 18, True), offsw=0.4, flow=0.8, flutter=1, fx=[sw(w=0.45)]), 35),
                 (dict(dy=-1, hand=(35, 14), ang=-65, offw=((32, 15), -115, 18, True), offsw=0.45, footB=(OX + 9, 37), flow=1.1, flutter=2,
                       fx=[sw(w=0.5)]), 45),
                 (dict(dy=-1, hand=(34, 13), ang=-75, offw=((32, 14), -105, 18, True), footB=(OX + 9, 37), flow=0.9, flutter=3), 60),
                 (dict(hand=(34, 22), ang=-60, offw=((31, 24), -30), flow=0.5), 80),
                 (dict(hand=(35, 27), ang=-25, offw=((30, 27), 150), flow=0.3), 80)])


def tw_air():  # both blades cocked over the shoulder, then brought through at once: an X opens in front
    fr = mseq([(dict(hand=(30, 17), ang=-130, offw=((29, 18), -110), flow=0.6), 50),
               (dict(hand=(31, 15), ang=-150, offw=((29, 16), -160), flow=0.8, flutter=1), 35),
               (dict(dx=2, hand=(40, 24), ang=15, offw=((38, 20), -25, 18, True), offsw=0.5, flow=1.3, flutter=2, fx=[sw(w=0.5)]), 45),
               (dict(dx=2, hand=(38, 29), ang=55, offw=((39, 19), -50, 18, True), offsw=0.45, flow=1.1, flutter=3, fx=[sw(w=0.45)]), 55),
               (dict(hand=(35, 26), ang=-20, offw=((31, 27), 150), flow=0.5, **AIR), 90)], AIRB)
    return cape_trail(fr, [2, 3])


def tw_down():  # blades crossed point-down under the feet, twisting like a drill as you fall
    base = dict(dy=-4, head_dy=1, **TUCK)
    drill = lambda a: [("ring", (33.5, 38), 5.5, a - 220, a, dict(sq=0.4, w=2.0))]
    fr = mseq([(dict(dy=-5, hand=(34, 18), ang=-100, offw=((32, 18), -80), flow=0.8, footB=(OX + 9, 34), footF=(OX + 17, 34)), 50),
               (dict(hand=(32, 28), ang=100, slen=15, offw=((35, 28), 80, 15, True), flow=1.3, flutter=1, fx=drill(0) + DIVE(9)), 40),
               (dict(dy=-3, hand=(32, 28), ang=82, slen=15, offw=((35, 28), 98, 15, True), flow=1.5, flutter=3, fx=drill(180) + DIVE(7, 1)), 45),
               (dict(hand=(32, 28), ang=100, slen=15, offw=((35, 28), 80, 15, True), flow=1.3, flutter=5, fx=drill(360)), 50),
               (dict(dy=-3, head_dy=0, hand=(35, 26), ang=-20, offw=((31, 27), 150), flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- scythe: an arcing hook, a spinning reap, a blade-down plunge
def sc_up():  # from low behind, the blade hooks up over the top
    return mseq([(dict(dx=-1, dy=2, hand=(31, 30), ang=150, footB=(OX + 6, 39), flow=0.3), 70),
                 (dict(dy=1, hand=(36, 27), ang=30, flow=0.7, flutter=1, fx=[sw(w=0.4)]), 40),
                 (dict(dx=1, dy=-1, hand=(36, 17), ang=-70, footB=(OX + 9, 37), flow=1.1, flutter=2, fx=[sw(w=0.55)]), 45),
                 (dict(dy=-1, hand=(32, 13), ang=-115, footB=(OX + 9, 37), flow=0.9, flutter=3, fx=[sw(w=0.45)]), 55),
                 (dict(hand=(30, 15), ang=-140, flow=0.5, flutter=4), 90),
                 (dict(hand=(34, 26), ang=-40, flow=0.3), 90)], grip=GRIP_SCYTHE)


def sc_air():  # a tucked, tilted spin: the blade reaps a full circle round the body
    RG = dict(sq=0.42, w=12.0)
    return mseq([(dict(dx=-1, hand=(29, 24), ang=176, flow=0.6), 55),
                 (dict(dx=1, hand=(34, 24), ang=2, flow=1.3, flutter=1, fx=[("ring", (29, 25), 25, 180, 0, RG)]), 45),
                 (dict(dx=1, hand=(34, 24), ang=2, flow=1.5, flutter=2, mirror=True, behind=True,
                       fx=[("ring", (29, 25), 25, 180, 0, RG)]), 45),
                 (dict(dx=1, hand=(35, 24), ang=8, flow=1.3, flutter=3, fx=[("ring", (29, 25), 25, 170, 8, RG)]), 50),
                 (dict(hand=(34, 25), ang=-15, flow=0.6, **AIR), 100)], AIRB, grip=GRIP_SCYTHE)


def sc_down():  # heave the scythe overhead, then swing its head down under you, the blade hooked beneath the feet
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-6, head_dy=0, hand=(33, 16), ang=-100, flow=0.8, footB=(OX + 9, 34), footF=(OX + 17, 34)), 60),
               (dict(hand=(36, 26), ang=70, flow=1.3, flutter=1, fx=[sw(w=0.5)] + DIVE(9)), 45),
               (dict(dy=-3, hand=(36, 27), ang=76, flow=1.5, flutter=3, fx=DIVE(7, 1)), 55),
               (dict(hand=(36, 27), ang=76, flow=1.3, flutter=5), 60),
               (dict(dy=-3, head_dy=0, hand=(34, 26), ang=-30, flow=0.7, flutter=4, **AIR), 90)], base, grip=GRIP_SCYTHE)
    return cape_dive(fr, [1, 2, 3])


# ---------------------------------------------------------------- whip: a vertical crack, a circling lash, a straight-down crack
def wh_up():  # the lash trails low, then the arm snaps up and the tip cracks straight overhead
    return mseq([(dict(dy=2, hand=(32, 29), ang=70, flow=0.3, lash=[(34, 33), (36, 37), (40, 38.5), (46, 38.5)]), 60),
                 (dict(hand=(35, 20), ang=-60, flow=0.7, flutter=1, lash=[(37, 25), (37, 31), (35, 36), (32, 38.5)]), 40),
                 (dict(dy=-1, hand=(34, 14), ang=-88, footB=(OX + 9, 37), flow=1.0, flutter=2, lash=[(34, 6), (35, 2), (35.5, 0.5)],
                       fx=[("flare", (35, 1), 5)]), 45),
                 (dict(dy=-1, hand=(34, 14), ang=-84, footB=(OX + 9, 37), flow=0.9, flutter=3, lash=[(36, 5), (41, 2), (47, 3), (52, 7)]), 55),
                 (dict(hand=(35, 22), ang=-40, flow=0.5, flutter=4, lash=[(40, 18), (45, 21), (49, 27), (51, 34)]), 90),
                 (dict(hand=(35, 27), ang=-50, flow=0.3), 90)])


def wh_air():  # the lash is swung in a full circle round the body, cracking in front and behind
    return mseq([(dict(hand=(30, 18), ang=-120, flow=0.6, lash=[(26, 12), (20, 12), (15, 15), (12, 20)]), 55),
                 (dict(hand=(35, 17), ang=-60, flow=0.9, flutter=1, lash=[(39, 10), (46, 8), (52, 11), (55, 17)]), 40),
                 (dict(dx=1, hand=(38, 24), ang=10, flow=1.2, flutter=2, lash=[(45, 27), (50, 32), (49, 38), (43, 41)],
                       fx=[("flare", (50, 33), 4)]), 45),
                 (dict(hand=(32, 27), ang=140, flow=1.3, flutter=3, lash=[(26, 32), (19, 35), (12, 33), (7, 27)],
                       fx=[("flare", (8, 27), 4)]), 45),
                 (dict(hand=(30, 20), ang=-130, flow=1.1, flutter=4, lash=[(24, 13), (17, 10), (11, 11), (7, 16)]), 50),
                 (dict(hand=(35, 26), ang=-40, flow=0.5, **AIR), 90)], AIRB)


def wh_down():  # whirl it overhead, then crack it straight down beneath the feet
    base = dict(dy=-4, head_dy=1, **TUCK)
    fr = mseq([(dict(dy=-5, hand=(31, 15), ang=-100, flow=0.8, lash=[(30, 8), (34, 4), (39, 5), (42, 9)],
                     footB=(OX + 9, 34), footF=(OX + 17, 34)), 55),
               (dict(hand=(35, 22), ang=40, flow=1.2, flutter=1, lash=[(40, 24), (43, 29), (42, 35), (40, 40)]), 40),
               (dict(hand=(34, 26), ang=88, flow=1.4, flutter=2, lash=[(34.5, 33), (35, 38), (35, 42.5)],
                     fx=[("flare", (35, 42), 5)] + DIVE(8)), 45),
               (dict(hand=(34, 26), ang=88, flow=1.3, flutter=3, lash=[(35, 33), (36, 37), (37, 42.5)]), 55),
               (dict(dy=-3, head_dy=0, hand=(35, 26), ang=-40, flow=0.7, flutter=4, **AIR), 90)], base)
    return cape_dive(fr, [2, 3])


V10_MOVES = [("dg_up", dg_up), ("dg_air", dg_air), ("dg_down", dg_down),
             ("gs_up", gs_up), ("gs_air", gs_air), ("gs_down", gs_down),
             ("sp_up", sp_up), ("sp_air", sp_air), ("sp_down", sp_down),
             ("kt_up", kt_up), ("kt_air", kt_air), ("kt_down", kt_down),
             ("st_up", st_up), ("st_air", st_air), ("st_down", st_down),
             ("sh_up", sh_up), ("sh_air", sh_air), ("sh_down", sh_down),
             ("tw_up", tw_up), ("tw_air", tw_air), ("tw_down", tw_down),
             ("sc_up", sc_up), ("sc_air", sc_air), ("sc_down", sc_down),
             ("wh_up", wh_up), ("wh_air", wh_air), ("wh_down", wh_down)]
ACTIVE.update({"dg_up": (2, 3), "dg_air": (2, 3), "dg_down": (1, 3),
               "gs_up": (2, 3), "gs_air": (3, 4), "gs_down": (1, 3),
               "sp_up": (1, 2), "sp_air": (1, 2), "sp_down": (1, 3),
               "kt_up": (2, 3), "kt_air": (2, 3), "kt_down": (1, 3),
               "st_up": (1, 4), "st_air": (2, 4), "st_down": (1, 3),
               "sh_up": (1, 2), "sh_air": (2, 3), "sh_down": (1, 3),
               "tw_up": (2, 3), "tw_air": (2, 3), "tw_down": (1, 3),
               "sc_up": (2, 3), "sc_air": (1, 3), "sc_down": (1, 3),
               "wh_up": (2, 3), "wh_air": (1, 4), "wh_down": (2, 3)})
HIT_EXTRAS |= {"sh_up", "sh_air", "sh_down", "tw_up", "tw_air", "tw_down"}
V10_UP = {t for t, _ in V10_MOVES if t.endswith("_up")}
V10_DOWN = {t for t, _ in V10_MOVES if t.endswith("_down")}
V10_AIR = {t for t, _ in V10_MOVES if t.endswith("_air")}
HIT_X0.update({"kt_air": -2, "sh_air": -2, "tw_air": -2, "sp_air": -2, "dg_air": -2, "gs_air": -4})   # iaido flash / trailing smears


ANIMS = [("idle", idle), ("run", run), ("jump_up", jump_up), ("jump_fall", jump_fall), ("land", land),
         ("roll", roll), ("attack1", attack1), ("attack2", attack2), ("attack3", attack3), ("heavy", heavy),
         ("hurt", hurt), ("heal", heal), ("death", death),
         # v3 additions (appended; the frames above keep their indices)
         ("attack_up", attack_up), ("attack_down", attack_down), ("air_attack", air_attack), ("cast", cast),
         ("parry", parry), ("riposte", riposte), ("wall_slide", wall_slide), ("double_jump", double_jump),
         ("rest", rest), ("rise", rise)] + MOVES + ARTS + TRAV + V8_MOVES + V8_ARTS + V9_MOVES + V9_ARTS + V9_SWIM + V10_MOVES   # v4 movesets after frame 124, v5 arts after 252,
                                                            # v7 traversal after 308, v8 classes/techniques after 329

# v10 polish: these tags ease back toward the idle pose at the end (last frame split; active frames and total time unchanged)
SETTLE_TAGS = ({"attack1", "attack2", "attack3", "heavy", "attack_up", "riposte", "counter", "backstep", "plunge_land", "sh_counter"}
               | {n for n, _ in MOVES + V9_MOVES} | {n for n, _ in V8_MOVES if n.split("_")[0] in ("st", "tw")}
               | {"sh_1", "sh_2", "sh_3", "sh_heavy"} | {n for n, _ in V10_MOVES if n.endswith("_up")})
ANIMS = [(n, settled(f) if n in SETTLE_TAGS else f) for n, f in ANIMS]

BODY_LAYERS = [l for l in LAYERS if l != "Sword"]
PREVIEW_TAGS = ["idle", "attack1", "heavy", "attack_up"]

def over(body, wpn):
    """What the engine shows: the player sheet, then the weapon overlay on top."""
    img = body.copy()
    if wpn is not None:
        img.alpha_composite(wpn)
    return img

def grid_sheet(rows, bg=(92, 92, 100, 255), cell_bg=(58, 58, 66, 255), gap_after=()):
    """rows: list of lists of frame images (None = spacer)."""
    cols = max(len(r) for r in rows)
    sheet = Image.new("RGBA", (cols * (W + 1), len(rows) * (H + 1)), bg)
    for ry, r in enumerate(rows):
        for cx, im in enumerate(r):
            if im is None:
                continue
            cell = Image.new("RGBA", (W, H), cell_bg)
            cell.alpha_composite(im)
            sheet.alpha_composite(cell, (cx * (W + 1), ry * (H + 1)))
    return sheet

def movesets_preview(raw, tags, body_comp, wpn, prev_dir, scale=3):
    """art/previews/movesets.png: each class's tags as rows (class weapon composited), labelled."""
    from PIL import ImageDraw
    rows, labels = [], []
    for pre, kinds in MOVE_CLASS.items():
        for kind in kinds:
            for t, a, b in tags:
                if t.startswith(pre + "_"):
                    rows.append([over(body_comp[i], wpn[kind][i]) for i in range(a, b + 1)])
                    act = ACTIVE.get(t, (0, -1))
                    labels.append((f"{t} [{kind}]", [raw[i][1] for i in range(a, b + 1)], act))
    sh = grid_sheet(rows)
    lw = 30
    out = Image.new("RGBA", (sh.width + lw, sh.height), (92, 92, 100, 255))
    out.alpha_composite(sh, (lw, 0))
    # active frames get a gold tick under the cell
    d = ImageDraw.Draw(out)
    for ry, (_, _, act) in enumerate(labels):
        for i in range(act[0], act[1] + 1):
            x = lw + i * (W + 1)
            d.line([(x, ry * (H + 1) + H - 1), (x + 5, ry * (H + 1) + H - 1)], fill=(255, 196, 90, 255))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    for ry, (lab, mss, act) in enumerate(labels):
        y = ry * (H + 1) * scale
        d.text((4, y + 4), lab.split(" ")[0], fill=(255, 255, 255, 255))
        d.text((4, y + 18), lab.split(" ")[1], fill=(200, 200, 210, 255))
        d.text((4, y + 32), f"{sum(mss)}ms", fill=(200, 200, 210, 255))
        for i, ms in enumerate(mss):
            d.text(((lw + i * (W + 1)) * scale + 3, y + 3), str(ms), fill=(255, 220, 150, 255))
    out.save(os.path.join(prev_dir, "movesets.png"))

def arts_preview(raw, tags, body_comp, wpn, prev_dir, scale=3, kinds=("longsword", "greatsword")):
    """art/previews/arts.png: each weapon art (art_*) as one row per weapon in `kinds`, labelled,
    per-frame ms on top, the key frame(s) ticked in gold."""
    from PIL import ImageDraw
    rows, labels = [], []
    for t, a, b in tags:
        if t.startswith("art_"):
            for kind in kinds:
                rows.append([over(body_comp[i], wpn[kind][i]) for i in range(a, b + 1)])
                labels.append((t[4:], kind, [raw[i][1] for i in range(a, b + 1)], ACTIVE.get(t, (0, -1))))
    sh = grid_sheet(rows)
    lw = 30
    out = Image.new("RGBA", (sh.width + lw, sh.height), (92, 92, 100, 255))
    out.alpha_composite(sh, (lw, 0))
    d = ImageDraw.Draw(out)
    for ry, (_, _, _, act) in enumerate(labels):
        for i in range(act[0], act[1] + 1):
            x = lw + i * (W + 1)
            d.line([(x, ry * (H + 1) + H - 1), (x + 5, ry * (H + 1) + H - 1)], fill=(255, 196, 90, 255))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    for ry, (name, kind, mss, _) in enumerate(labels):
        y = ry * (H + 1) * scale
        d.text((4, y + 4), name, fill=(255, 255, 255, 255))
        d.text((4, y + 18), kind[:10], fill=(200, 200, 210, 255))
        d.text((4, y + 32), f"{sum(mss)}ms", fill=(200, 200, 210, 255))
        for i, ms in enumerate(mss):
            d.text(((lw + i * (W + 1)) * scale + 3, y + 3), f"{i}:{ms}", fill=(255, 220, 150, 255))
    out.save(os.path.join(prev_dir, "arts.png"))

def write_meta(raw, tags):
    """assets/player_meta.json: per-move active window, damage box (feet-relative, facing right)
    measured from the class weapon's blade + smear on the active frames, and a slash-fx point."""
    import json
    moves = meta_for(raw, tags)
    meta = {"native": 1, "anchor": [28, 40], "facing": "right",
            "classes": {"dagger": ["dagger"], "great": ["greatsword", "maul"], "spear": ["spear"], "katana": ["katana"],
                        "sword": ["longsword", "oathbrand", "kalden"], "staff": ["quarterstaff"],
                        "shield": ["knight_shield"], "twin": ["twinfangs"], "scythe": ["briar_scythe"], "whip": ["gravechain"]},
            "moves": moves}
    with open(os.path.join(asebuild.ASSETS, "player_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    return meta


def meta_for(raw, tags):
    AX, AY = 28, 40
    moves = {}
    for t, a, b in tags:
        if t not in ACTIVE:
            continue
        kinds = MOVE_CLASS.get(t.split("_")[0], ("longsword",)) if "_" in t and t.split("_")[0] in MOVE_CLASS else ("longsword",)
        i0, i1 = ACTIVE[t]
        xs, ys, pts = [], [], []
        for i in range(a + i0, a + i1 + 1):
            w = raw[i][0].get("Sword")
            for kind in kinds:
                if t in HIT_EXTRAS or t in HIT_X0 or t in HIT_OVERRIDE or kind in V8_IDS:
                    img = w.render(kind, dust=False, extras=t in HIT_EXTRAS)
                else:
                    img = w.render(kind, dust=False) if isinstance(w, Wpn) else w.render(kind)
                bb = img.getbbox()
                if not bb:
                    continue
                xs += [bb[0], bb[2]]
                ys += [bb[1], bb[3]]
                info = {}
                draw_weapon(kind, w.hand, w.ang, w.slen, w.planted, w.held, w.fitb, info=info)
                aa = math.radians(info["ang"])
                px_, py_ = info["hand"][0] + math.cos(aa) * info["tip"] * 0.62, info["hand"][1] + math.sin(aa) * info["tip"] * 0.62
                if w.mirror:
                    px_ = 56 - px_
                pts.append((px_, min(py_, 38.0)))
            if t in BODY_HIT:   # dash arts: the charging body itself is the damage box
                bb = compose(imgs(raw[i][0], None)).getbbox()
                xs += [bb[0], bb[2]]
                ys += [bb[1], bb[3]]
        hit = [min(xs) - AX, min(ys) - AY, max(xs) - AX, min(max(ys), AY) - AY]
        if t in V10_DOWN:   # plunges: the blade's own column (no smear / wind lines), reaching under the feet like the sword's
            bx0, bx1, by0 = 99, -99, 99
            for i in range(a + i0, a + i1 + 1):
                w = raw[i][0].get("Sword")
                sv = (w.fx, w.offfx)
                w.fx, w.offfx = (), ()
                bb = w.render(kinds[0], dust=False, extras=t in HIT_EXTRAS).getbbox()
                w.fx, w.offfx = sv
                if bb:
                    bx0, bx1, by0 = min(bx0, bb[0]), max(bx1, bb[2]), min(by0, bb[1])
            big = 3 if t == "gs_down" else 0
            x0, x1 = min(-6, max(-12, bx0 - AX - big)), max(10, min(16, bx1 - AX + big))   # never narrower than the sword's
            hit = [x0, max(-16, by0 - AY), x1, 22 + big]
        elif t in V10_UP:   # long weapons are shortened to fit under the frame top: the real reach goes higher
            hit = [max(-20, hit[0]), hit[1] - 14, hit[2], hit[3]]
        if t in HIT_X0:
            hit[0] = max(hit[0], HIT_X0[t])
        if t in HIT_OVERRIDE:
            hit = list(HIT_OVERRIDE[t])
        fxat = [round(sum(p[0] for p in pts) / len(pts)) - AX, round(sum(p[1] for p in pts) / len(pts)) - AY]
        moves[t] = {"active": [i0, i1], "hit": hit, "fxAt": list(FXAT_OVERRIDE.get(t, fxat))}
    return moves

import random

# ================================================================ v8: weapon-signature FX sheets (wpn_fx_*), built via Aseprite
# python3 art/gen_player.py --fx   (house style: crisp colour bands, ordered dither instead of blur, 2 layers)
_B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _bt(x, y):
    return (_B4[y & 3][x & 3] + 0.5) / 16.0


def _rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def _ramp(ramp, v, x, y):
    v = max(0.0, min(1.0, v))
    f = v * (len(ramp) - 1)
    i = int(f)
    if f - i > _bt(x, y):
        i += 1
    return _rgba(ramp[min(i, len(ramp) - 1)])


FX_INK = [(34, 16, 58), (70, 36, 120), (120, 76, 196), (184, 142, 250), (236, 222, 255)]
FX_WIND = [(70, 96, 108), (120, 160, 168), (176, 222, 214), (230, 250, 246), (255, 255, 255)]
FX_STORM = [(40, 60, 120), (90, 140, 230), (170, 214, 255), (230, 246, 255), (255, 255, 255)]
FX_MAGMA = [(90, 24, 18), (170, 50, 22), (240, 110, 34), (255, 180, 70), (255, 240, 180)]
FX_FROST = [(40, 70, 130), (90, 150, 214), (160, 210, 246), (220, 244, 255), (255, 255, 255)]
FX_GOLD = [(120, 80, 30), (210, 150, 60), (255, 214, 120)]


def _img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _put(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c if len(c) == 4 else _rgba(c))


def _clean(img, keep=1):
    """drop isolated single pixels (house rule: no stray specks)."""
    px = img.load()
    w, h = img.size
    kill = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and sum(1 for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and 0 <= x + a < w
                                   and 0 <= y + b < h and px[x + a, y + b][3]) < keep:
                kill.append((x, y))
    for p in kill:
        px[p] = (0, 0, 0, 0)
    return img


def _outline_img(img, col=(12, 8, 20, 255)):
    px = img.load()
    w, h = img.size
    add = [(x, y) for y in range(h) for x in range(w) if not px[x, y][3] and any(
        0 <= x + a < w and 0 <= y + b < h and px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in add:
        px[p] = col
    return img


def _emit(name, w, h, frames, ms, tag):
    """frames: list of (glow, core) images; ms: int or list."""
    ms = ms if isinstance(ms, (list, tuple)) else [ms] * len(frames)
    asebuild.build("wpn_fx_" + name, w, h, ["Glow", "Core"],
                   [{"ms": m, "cels": {"Glow": gl, "Core": co}} for (gl, co), m in zip(frames, ms)], [(tag, 0, len(frames) - 1)])
    return [Image.alpha_composite(gl, co) for gl, co in frames]


def fx_glyph():   # a violet ink sigil hanging on the wound, gold marks turning round it
    W_, H_ = 21, 21
    cx = cy = 10.5
    out = []
    for f in range(6):
        gl, co = _img(W_, H_), _img(W_, H_)
        rot = f * 20
        pulse = [0, 1, 2, 1, 0, 1][f]
        for y in range(H_):
            for x in range(W_):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if 7.6 <= d <= 8.6:
                    co.putpixel((x, y), _rgba(FX_INK[3]))
                elif 6.6 <= d < 7.6 and (x + y) % 2 == 0:
                    gl.putpixel((x, y), _rgba(FX_INK[1], 200))
                elif d < 4 + pulse * 0.5 and _bt(x, y) < 0.35 - d * 0.05:
                    gl.putpixel((x, y), _rgba(FX_INK[2], 160))
        for k in range(3):   # gold marks on the ring
            a = math.radians(rot + k * 120)
            for r in (7.2, 8.2, 9.2):
                _put(co, cx - 0.5 + math.cos(a) * r, cy - 0.5 + math.sin(a) * r, FX_GOLD[2] if r < 9 else FX_GOLD[1])
        # inner rune: a turning triangle of ink strokes with a bright eye
        pts = [(cx - 0.5 + math.cos(math.radians(-rot * 1.5 + k * 120 - 90)) * 5, cy - 0.5 + math.sin(math.radians(-rot * 1.5 + k * 120 - 90)) * 5) for k in range(3)]
        for i in range(3):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 3]
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for j in range(n + 1):
                _put(co, x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n, FX_INK[3] if j % 3 else FX_INK[4])
        for a2, b2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
            _put(co, cx - 1 + a2, cy - 1 + b2, FX_INK[4] if pulse else FX_GOLD[2])
        out.append((gl, co))
    return _emit("glyph", W_, H_, out, 80, "glyph")


def fx_inkburst():   # the glyph bursts: a violet flash, then a ragged ring of ink thrown outward, flinging drops
    W_, H_ = 33, 33
    cx = cy = 16.5
    rnd = random.Random(7)
    drops = [(rnd.uniform(0, 6.283), rnd.uniform(0.9, 1.35), rnd.choice((1, 1, 2))) for _ in range(12)]
    lobes = [rnd.uniform(0, 6.283) for _ in range(3)]
    out = []
    for f in range(7):
        gl, co = _img(W_, H_), _img(W_, H_)
        R = [5, 8, 10.5, 12, 13, 13.5, 14][f]
        th = [5, 4.2, 3.4, 2.6, 2.0, 1.5, 1.0][f]
        for y in range(H_):
            for x in range(W_):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                edge = R * (0.86 + 0.1 * math.sin(a * 5 + 1.3) + 0.06 * math.sin(a * 9 + 0.4))
                edge += sum(2.2 * max(0.0, math.cos(a - l)) ** 8 for l in lobes) * min(1, f / 2)
                if f == 0:
                    if d < edge:
                        co.putpixel((x, y), _rgba(FX_INK[4] if d < R * 0.55 else FX_INK[3]))
                    elif d < edge + 1.5 and (x + y) % 2 == 0:
                        gl.putpixel((x, y), _rgba(FX_INK[2], 200))
                    continue
                inner = edge - th
                if inner <= d < edge:
                    v = (d - inner) / th
                    if f >= 5 and _bt(x, y) > (1.0 if f == 5 else 0.6):
                        continue
                    co.putpixel((x, y), _rgba(FX_INK[3] if v > 0.66 and f < 4 else (FX_INK[2] if v > 0.3 else FX_INK[1])))
                elif d < inner and f <= 2 and _bt(x, y) < 0.3 - f * 0.08:
                    gl.putpixel((x, y), _rgba(FX_INK[2], 140))
        for (a, sp, sz) in drops:   # flung droplets, falling a little
            r = R * sp
            x, y = cx - 0.5 + math.cos(a) * r, cy - 0.5 + math.sin(a) * r + f * f * 0.15
            if 1 <= f <= 6 and not (f == 6 and sz == 1):
                _put(co, x, y, FX_INK[3] if f < 4 else FX_INK[2])
                if sz == 2:
                    _put(co, x + 1, y, FX_INK[2]); _put(co, x, y + 1, FX_INK[1]); _put(co, x + 1, y + 1, FX_INK[1])
                _put(gl, x - math.cos(a) * 1.5, y - math.sin(a) * 1.5, _rgba(FX_INK[1], 190))
        out.append((gl, co))
    return _emit("inkburst", W_, H_, out, [40, 45, 50, 55, 60, 70, 80], "inkburst")


def fx_inkblot():   # a flung drop of ink (travels right), wobbling, with a short tail
    W_, H_ = 11, 9
    out = []
    for f in range(4):
        gl, co = _img(W_, H_), _img(W_, H_)
        sx, sy = [(1.0, 1.0), (1.15, 0.85), (1.0, 1.0), (0.88, 1.12)][f]
        for y in range(H_):
            for x in range(W_):
                dx, dy = (x + 0.5 - 6.5) / (2.6 * sx), (y + 0.5 - 4.5) / (2.6 * sy)
                d = math.hypot(dx, dy)
                if d <= 1:
                    co.putpixel((x, y), _rgba(FX_INK[4] if (dx < -0.1 and dy < -0.2 and d < 0.6) else (FX_INK[2] if d < 0.7 else FX_INK[1])))
        for i in range(1, 4):   # tail
            _put(gl, 4 - i, 4 + (f % 2) * (i // 2), _rgba(FX_INK[2 if i < 3 else 1], 220))
        _outline_img(co, (20, 8, 34, 255))
        out.append((gl, co))
    return _emit("inkblot", W_, H_, out, 70, "inkblot")


def fx_gust():   # a short wind crescent travelling right: three streaks bowed forward, the middle one bright
    W_, H_ = 29, 19
    out = []
    for f in range(4):
        gl, co = _img(W_, H_), _img(W_, H_)
        for j, (yo, L, br) in enumerate(((-5, 15, 3), (0, 22, 4), (5, 13, 3))):
            sh = (f + j) % 2
            for i in range(L):
                q = i / max(1, L - 1)                  # 0 tail .. 1 head
                x = 3 + (22 - L) + i + sh
                yy = 9 + yo + (-1 if yo < 0 else 1) * (1.6 * (1 - q) ** 2) * (1 if yo else 0)
                if q < 0.3 and (i + f) % 2:
                    continue
                c = FX_WIND[br] if q > 0.65 else (FX_WIND[br - 1] if q > 0.3 else FX_WIND[br - 2])
                _put(co, x, yy, c)
                if j == 1 and q > 0.45:
                    _put(co, x, yy + 1, FX_WIND[2] if q > 0.8 else FX_WIND[1])
                if q > 0.5:
                    _put(gl, x - 1, yy - 1 if yo <= 0 else yy + 1, _rgba(FX_WIND[1], 150))
        out.append((gl, co))
    return _emit("gust", W_, H_, out, 60, "gust")


def fx_whirl():   # a travelling whirlwind: stacked wind rings round a swaying funnel, dust at its foot (bottom-anchored)
    W_, H_ = 37, 53
    out = []
    for f in range(6):
        gl, co = _img(W_, H_), _img(W_, H_)
        ph = f / 6.0 * 2 * math.pi
        for k in range(11):
            yc = H_ - 3 - k * 4.6
            t = (H_ - 1 - yc) / (H_ - 1)
            rx = 2.5 + 15 * t ** 1.25
            ry = 1.2 + 1.3 * t
            cxy = 18 + 2.0 * math.sin(t * 4.5 + ph)
            gap = ph * 1.5 + k * 0.9                   # the ring's open end turns with the wind
            for s_ in range(int(rx * 7) + 8):
                a = s_ / (int(rx * 7) + 8) * 2 * math.pi
                if math.cos(a - gap) > 0.72:
                    continue
                x, y = cxy + math.cos(a) * rx, yc + math.sin(a) * ry
                front = math.sin(a) > 0
                if front:
                    _put(co, x, y, FX_WIND[3] if abs(math.cos(a)) < 0.7 else FX_WIND[2])
                elif (int(x) + int(y)) % 2 == 0:
                    _put(gl, x, y, _rgba(FX_WIND[1], 200))
        for i in range(6):   # loose streaks spun off the funnel
            t = (i * 0.17 + f * 0.05) % 1
            x0 = 18 + (12 + 5 * t) * (1 if i % 2 else -1) * t
            y0 = H_ - 4 - t * 44
            for j in range(4):
                _put(co if j < 2 else gl, x0 + (j if i % 2 else -j), y0 - j * 0.4, FX_WIND[2] if j < 2 else _rgba(FX_WIND[1], 170))
        rnd = random.Random(f)
        for i in range(12):   # dust kicked up at the base
            a = rnd.uniform(0.2, math.pi - 0.2)
            x, y = 18 + math.cos(a) * rnd.uniform(4, 13), H_ - 1 - math.sin(a) * rnd.uniform(0, 5)
            _put(co, x, y, (150, 138, 124) if i % 2 else (104, 94, 86))
        out.append((gl, co))
    return _emit("whirl", W_, H_, out, 70, "whirl")


def _bolt_pts(rnd, x0, y0, x1, y1, jag):
    n = max(4, int(abs(y1 - y0) / 7))
    pts = [(x0, y0)]
    for i in range(1, n):
        k = i / n
        pts.append((x0 + (x1 - x0) * k + rnd.uniform(-jag, jag), y0 + (y1 - y0) * k))
    pts.append((x1, y1))
    return pts


def _stroke(img, pts, c, w=1):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for j in range(n + 1):
            x, y = x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n
            for a in range(-(w // 2), w - w // 2):
                _put(img, x + a, y, c)


def fx_bolt():   # a bolt from the sky (bottom-anchored): strike, flash, flicker, fade
    W_, H_ = 33, 129
    out = []
    rnd = random.Random(3)
    main = _bolt_pts(rnd, 16 + rnd.uniform(-6, 6), 0, 16, H_ - 2, 5)
    branches = []
    for k in (3, 6, 9, 12):
        if k < len(main) - 1:
            x0, y0 = main[k]
            branches.append(_bolt_pts(rnd, x0, y0, x0 + rnd.choice((-1, 1)) * rnd.uniform(6, 13), y0 + rnd.uniform(12, 22), 3))
    for f in range(6):
        gl, co = _img(W_, H_), _img(W_, H_)
        if f == 0:   # leader
            _stroke(co, main[:len(main) // 2 + 1], FX_STORM[2])
        else:
            vis = [1, 1, 0.8, 0.6, 0.3][f - 1]
            jit = random.Random(f)
            pts = [(x + (jit.uniform(-1, 1) if 0 < i < len(main) - 1 else 0), y) for i, (x, y) in enumerate(main)]
            if vis >= 0.6:
                _stroke(gl, pts, _rgba(FX_STORM[1], 200), 5 if f <= 2 else 3)
            _stroke(co, pts, FX_STORM[3] if vis > 0.5 else FX_STORM[2], 2 if f <= 2 else 1)
            _stroke(co, pts, FX_STORM[4], 1)
            if f <= 3:
                for b in branches:
                    _stroke(co, b, FX_STORM[2] if f > 1 else FX_STORM[3])
            if f <= 3:   # ground flash
                R = [0, 9, 11, 8, 5][f] if f < 5 else 0
                for y in range(H_ - 8, H_):
                    for x in range(W_):
                        d = math.hypot((x + 0.5 - 16.5) / 1.6, (y + 0.5 - H_) * 1.2)
                        if d < R:
                            (co if d < R * 0.45 else gl).putpixel((x, y), _ramp(FX_STORM, 1 - d / R, x, y))
        out.append((gl, co))
    return _emit("bolt", W_, H_, out, [40, 45, 50, 60, 70, 80], "bolt")


def fx_lava():   # a burning seam in the floor (bottom-anchored, looping)
    W_, H_ = 17, 9
    out = []
    rnd = random.Random(11)
    base = [4 + (1 if rnd.random() < 0.4 else 0) - (1 if rnd.random() < 0.3 else 0) for _ in range(W_)]
    for f in range(4):
        gl, co = _img(W_, H_), _img(W_, H_)
        for x in range(W_):
            y0 = base[x] + 2
            heat = 0.55 + 0.45 * math.sin(x * 0.9 + f * 1.6)
            co.putpixel((x, y0), _ramp(FX_MAGMA, 0.6 + 0.4 * heat, x, y0))
            if 2 <= x <= W_ - 3:
                co.putpixel((x, y0 + 1), _rgba(FX_MAGMA[2] if heat > 0.5 else FX_MAGMA[1]))
            _put(gl, x, y0 - 1, _rgba(FX_MAGMA[1], 150 if (x + f) % 2 else 90))
            if (x * 5 + f * 3) % 11 == 0:   # a bubble breaking the surface
                _put(co, x, y0 - 1 - (f % 2), FX_MAGMA[3])
        out.append((gl, co))
    return _emit("lava", W_, H_, out, 110, "lava")


def fx_erupt():   # the seam erupts: a molten geyser climbs, crowns in a splash and collapses (bottom-anchored)
    W_, H_ = 25, 49
    out = []
    hts = [10, 26, 40, 45, 36, 22, 9]
    rnd = random.Random(5)
    blobs = [(rnd.uniform(-1, 1), rnd.uniform(0.6, 1.1)) for _ in range(9)]
    for f in range(7):
        gl, co = _img(W_, H_), _img(W_, H_)
        top = H_ - hts[f]
        crown = f <= 3
        for y in range(top, H_):
            t = (H_ - y) / max(1, hts[f])               # 0 foot .. 1 crown
            hw = 2.2 + 1.4 * t + 0.9 * math.sin(y * 0.55 + f * 1.7)
            if crown and t > 0.8:
                hw += 3.2 * math.sin((t - 0.8) / 0.2 * math.pi) ** 0.7
            if t < 0.12:
                hw += 3 * (0.12 - t) / 0.12            # splayed foot
            for x in range(W_):
                d = abs(x + 0.5 - 12.5) / max(0.8, hw)
                if d > 1:
                    continue
                v = 1 - d * 0.75 - (0.25 if f >= 5 else 0) - 0.2 * t
                img = co if d < 0.8 else gl
                img.putpixel((x, y), _ramp(FX_MAGMA, v, x, y) if img is co else _rgba(FX_MAGMA[1], 220))
        if f >= 2:
            for bx, sp in blobs:   # molten drops thrown off the crown
                x = 12.5 + bx * (f - 1) * 3.2 * sp
                y = H_ - hts[min(f, 3)] - 2 + (f - 2) ** 2 * 2.4 * sp
                if 0 <= y < H_ - 1:
                    _put(co, x, y, FX_MAGMA[3]); _put(co, x + 1, y, FX_MAGMA[2]); _put(co, x, y + 1, FX_MAGMA[1]); _put(co, x + 1, y + 1, FX_MAGMA[1])
        _outline_img(co, (40, 12, 10, 255)) if f < 6 else None
        out.append((gl, co))
    return _emit("erupt", W_, H_, out, [45, 50, 55, 60, 70, 80, 90], "erupt")


def fx_frost():   # frost burst: a star of ice shards bursting from a white flash, then shattering away
    W_, H_ = 37, 37
    c = 18.5
    rnd = random.Random(9)
    spikes = [(k * 45 + rnd.uniform(-12, 12), rnd.uniform(0.7, 1.0)) for k in range(8)] + \
             [(k * 45 + 22 + rnd.uniform(-8, 8), rnd.uniform(0.4, 0.6)) for k in range(8)]
    out = []
    for f in range(7):
        gl, co = _img(W_, H_), _img(W_, H_)
        L = [6, 12, 16, 17, 17, 17, 17][f]
        brk = [0, 0, 0, 0.2, 0.45, 0.7, 0.9][f]
        for (a, s) in spikes:
            ar = math.radians(a)
            dx, dy = math.cos(ar), math.sin(ar)
            n = L * s
            off = brk * 5
            for i in range(int(n)):
                q = i / max(1, n)
                if brk and (int(q * 5) % 2 == 1) and _bt(i, int(a)) < brk:
                    continue
                hw = 1.6 * (1 - q)
                for w_ in (-1, 0, 1):
                    if abs(w_) > hw:
                        continue
                    x, y = c - 0.5 + dx * (i + off) - dy * w_, c - 0.5 + dy * (i + off) + dx * w_
                    col = FX_FROST[4] if (w_ == 0 and q < 0.5 and f < 4) else (FX_FROST[3] if w_ <= 0 else FX_FROST[1])
                    _put(co, x, y, col)
                _put(gl, c - 0.5 + dx * (i + off) + dy * 2, c - 0.5 + dy * (i + off) - dx * 2, _rgba(FX_FROST[1], 150))
        if f <= 2:   # core flash
            R = [5, 7, 5][f]
            for y in range(H_):
                for x in range(W_):
                    d = math.hypot(x + 0.5 - c, y + 0.5 - c)
                    if d < R:
                        (co if d < R * 0.6 else gl).putpixel((x, y), _ramp(FX_FROST, 1 - d / R + 0.3, x, y))
        _clean(co)
        out.append((gl, co))
    return _emit("frost", W_, H_, out, [40, 45, 50, 60, 70, 80, 90], "frost")


FX_ALL = [fx_glyph, fx_inkburst, fx_inkblot, fx_gust, fx_whirl, fx_bolt, fx_lava, fx_erupt, fx_frost]


# ---- v9 signature FX
FX_THORN = [(30, 22, 18), (70, 52, 38), (120, 96, 66), (170, 150, 110)]
FX_GREEN = [(40, 90, 50), (90, 180, 100), (160, 240, 170)]
FX_TEAL = [(20, 60, 70), (40, 140, 140), (100, 230, 210), (210, 255, 250), (255, 255, 255)]
FX_BLOOD = [(60, 6, 16), (140, 16, 34), (220, 40, 60), (255, 140, 150), (255, 230, 230)]
FX_PALE = [(150, 170, 220), (220, 230, 255), (255, 244, 210), (255, 252, 240), (255, 255, 255)]


def fx_thorn():   # thorns of the Warden's wood erupt from the ground and sink back (bottom-anchored)
    W_, H_ = 17, 31
    hts = [8, 20, 28, 26, 18, 8]
    out = []
    for f, h in enumerate(hts):
        gl, co = _img(W_, H_), _img(W_, H_)
        for spk, (ox, lean, sc) in enumerate(((8.5, 0.0, 1.0), (4.5, -0.35, 0.65), (12.5, 0.4, 0.55))):
            hh = h * sc
            for y in range(int(H_ - hh), H_):
                t = (H_ - y) / max(1, hh)                 # 0 root .. 1 point
                cx = ox + lean * (H_ - y)
                hw = 2.2 * max(0.0, 1 - t) ** 0.8 + 0.2
                for x in range(W_):
                    d = x + 0.5 - cx
                    if abs(d) <= hw:
                        c = FX_THORN[3] if d < -hw * 0.3 else (FX_THORN[2] if d < hw * 0.3 else FX_THORN[1])
                        if abs(d) < 0.5 and 0.2 < t < 0.8 and (y + spk) % 5 == 0:
                            c = FX_GREEN[2]                 # glowing sap
                        co.putpixel((x, y), _rgba(c))
                # side barbs
                if int(H_ - y) % 6 == 3 and 0.1 < t < 0.8:
                    _put(co, cx + hw + 1, y - 1, FX_THORN[2]); _put(co, cx - hw - 1, y - 1, FX_THORN[2])
        if f <= 2:
            for x in range(W_):
                if (x + f) % 2 == 0:
                    _put(gl, x, H_ - 1 - (x % 3 == 0), _rgba(FX_GREEN[1], 180))
        _outline_img(co, (14, 10, 10, 255))
        out.append((gl, co))
    return _emit("thorn", W_, H_, out, [40, 45, 70, 90, 70, 60], "thorn")


def _lance(name, pal, W_=27, H_=9, n=3):   # a travelling lance (right), a bright head and a tapering, flickering tail
    out = []
    for f in range(n):
        gl, co = _img(W_, H_), _img(W_, H_)
        cy = H_ // 2
        for x in range(W_):
            q = x / (W_ - 1)                             # 0 tail .. 1 head
            hw = (1.8 if q > 0.8 else 1.2 * q + 0.2) if q < 0.97 else 0.6
            wob = math.sin(x * 0.9 + f * 2.1) * 0.5 * (1 - q)
            for y in range(H_):
                d = abs(y + 0.5 - (cy + 0.5 + wob))
                if d <= hw:
                    c = pal[4] if (d < 0.6 and q > 0.6) else (pal[3] if d < hw * 0.6 else pal[2])
                    if q < 0.3 and (x + y + f) % 2:
                        continue
                    co.putpixel((x, y), _rgba(c))
                elif d <= hw + 1.2 and q > 0.4 and (x + y) % 2 == 0:
                    gl.putpixel((x, y), _rgba(pal[1], 190))
        out.append((gl, co))
    return _emit(name, W_, H_, out, 60, name)


def fx_waterlance():
    return _lance("waterlance", FX_TEAL)


def fx_bloodlance():
    return _lance("bloodlance", FX_BLOOD, W_=25, H_=7)


def fx_sundisc():   # a spinning disc of sunlight with a hot core and turning rays
    W_, H_ = 17, 17
    c = 8.5
    out = []
    for f in range(4):
        gl, co = _img(W_, H_), _img(W_, H_)
        for y in range(H_):
            for x in range(W_):
                dx, dy = x + 0.5 - c, y + 0.5 - c
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx) + f * 0.39
                if d < 3.2:
                    co.putpixel((x, y), _rgba((255, 250, 220) if d < 1.8 else (255, 214, 104)))
                elif d < 5.2:
                    co.putpixel((x, y), _rgba((240, 170, 60) if int((a + 7) / 0.785) % 2 else (255, 214, 104)))
                elif d < 7.8 and abs(((a + 7) % 0.785) - 0.39) < 0.12:
                    (co if d < 6.6 else gl).putpixel((x, y), _rgba((255, 214, 104) if d < 6.6 else (200, 130, 40), 255 if d < 6.6 else 200))
        out.append((gl, co))
    return _emit("sundisc", W_, H_, out, 50, "sundisc")


def fx_starshard():   # a shard of the sky falling point-first (drawn pointing down), a comet tail above it
    W_, H_ = 11, 23
    out = []
    for f in range(3):
        gl, co = _img(W_, H_), _img(W_, H_)
        for y in range(H_):
            q = y / (H_ - 1)                              # 0 tail .. 1 point
            if q > 0.62:                                  # the shard
                hw = 2.6 * (1 - (q - 0.62) / 0.38) ** 0.9 + 0.2 if q > 0.78 else 2.6 * ((q - 0.62) / 0.16) ** 0.6
                for x in range(W_):
                    d = abs(x + 0.5 - 5.5)
                    if d <= hw:
                        co.putpixel((x, y), _rgba((255, 255, 255) if d < 0.8 else ((200, 220, 255) if x < 5.5 else (110, 150, 240))))
            else:                                         # tail
                hw = 1.6 * q + 0.2
                for x in range(W_):
                    d = abs(x + 0.5 - 5.5 - math.sin(y * 0.8 + f * 2) * 0.4 * (1 - q))
                    if d <= hw and ((x + y + f) % 2 == 0 or q > 0.35):
                        (co if d < hw * 0.5 else gl).putpixel((x, y), _rgba((200, 220, 255) if d < hw * 0.5 else (110, 150, 240), 255 if d < hw * 0.5 else 190))
        out.append((gl, co))
    return _emit("starshard", W_, H_, out, 60, "starshard")


def fx_pyre():   # a pyre of pale white flame (bottom-anchored, looping)
    W_, H_ = 17, 33
    out = []
    for f in range(6):
        gl, co = _img(W_, H_), _img(W_, H_)
        ph = f / 6 * 2 * math.pi
        for y in range(H_):
            t = (H_ - y) / H_                             # 0 foot .. 1 top
            for tongue, (ox, amp, ht) in enumerate(((8.5, 1.4, 1.0), (5.5, 1.0, 0.7), (11.5, 1.1, 0.78))):
                if t > ht:
                    continue
                tt = t / ht
                cx = ox + math.sin(tt * 5 + ph + tongue) * amp * tt
                hw = 3.2 * (1 - tt) ** 0.7 * (0.9 if tongue else 1.0) + 0.3
                for x in range(W_):
                    d = abs(x + 0.5 - cx)
                    if d <= hw:
                        v = 1 - d / hw * 0.6 - tt * 0.5
                        img = co if v > 0.25 else gl
                        c = _ramp(FX_PALE, v, x, y)
                        if img is gl:
                            c = (c[0], c[1], c[2], 190)
                        img.putpixel((x, y), c)
        for i in range(3):   # embers breaking off the top
            yy = (H_ - 26 - ((f * 5 + i * 9) % 12))
            _put(co, 6 + i * 3 + (f % 2), yy, FX_PALE[3])
        out.append((gl, co))
    return _emit("pyre", W_, H_, out, 70, "pyre")


FX_ALL += [fx_thorn, fx_waterlance, fx_bloodlance, fx_sundisc, fx_starshard, fx_pyre]


def fx_main():
    sheets = []
    for fn in FX_ALL:
        frames = fn()
        sheets.append((fn.__name__, frames))
    # preview: every sheet's frames on a dark strip, 4x
    rows = []
    for name, frames in sheets:
        w, h = frames[0].size
        strip = Image.new("RGBA", (len(frames) * (w + 2) + 2, h + 4), (40, 36, 48, 255))
        for i, im in enumerate(frames):
            strip.alpha_composite(im, (2 + i * (w + 2), 2))
        rows.append(strip)
    W2 = max(r.width for r in rows)
    H2 = sum(r.height for r in rows)
    pv = Image.new("RGBA", (W2, H2), (24, 22, 30, 255))
    y = 0
    for r in rows:
        pv.alpha_composite(r, (0, y))
        y += r.height
    pv = pv.resize((pv.width * 4, pv.height * 4), Image.NEAREST)
    pv.save(os.path.join(asebuild.ART, "previews", "wpn_fx.png"))
    print("wpn_fx:", [n for n, _ in sheets])


def _ase_build(name, w, h, layers, frames, tags, tries=3):
    """asebuild.build with a timeout + retry: a stuck Aseprite process no longer hangs the whole run."""
    import shutil, subprocess, tempfile
    for attempt in range(tries):
        tmp = tempfile.mkdtemp(prefix=f"ase_{name}_")
        try:
            with open(os.path.join(tmp, "manifest.txt"), "w") as fh:
                fh.write(f"size {w} {h}\n")
                fh.write("layers " + ",".join(layers) + "\n")
                fh.write("frames " + ",".join(str(int(f["ms"])) for f in frames) + "\n")
                for t, a, b in tags:
                    fh.write(f"tag {t} {a + 1} {b + 1}\n")
            for i, f in enumerate(frames):
                for layer, img in f["cels"].items():
                    if img.getbbox():
                        img.save(os.path.join(tmp, f"{layer}_{i + 1}.png"))
            src = os.path.join(asebuild.ART, f"{name}.aseprite")
            subprocess.run([asebuild.ASEPRITE, "-b", "--script-param", f"dir={tmp}", "--script-param", f"out={src}", "--script",
                            os.path.join(asebuild.ART, "build_sprite.lua")], check=True, timeout=240)
            subprocess.run([asebuild.ASEPRITE, "-b", src, "--sheet", os.path.join(asebuild.ASSETS, f"{name}.png"),
                            "--sheet-type", "horizontal", "--data", os.path.join(asebuild.ASSETS, f"{name}.json"),
                            "--format", "json-array", "--list-tags"], check=True, stdout=subprocess.DEVNULL, timeout=240)
            return src
        except subprocess.TimeoutExpired:
            print("aseprite timed out on", name, "- retrying", flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    raise RuntimeError("aseprite kept hanging on " + name)


_RAW = None


def _wpn_frames(kind):
    return [imgs(c, kind).get("Sword") for c, _ in _RAW]


V8_PREVIEW = [  # (tag, kinds) rows of art/previews/expansion.png
    ("st_1", ("quarterstaff", "inkquill")), ("st_2", ("quarterstaff", "windstaff")), ("st_3", ("quarterstaff", "lantern_staff")),
    ("st_4", ("quarterstaff", "inkquill")), ("st_heavy", ("quarterstaff", "windstaff")),
    ("sh_1", ("knight_shield", "twinborne")), ("sh_2", ("knight_shield", "overseer_bulwark")), ("sh_3", ("knight_shield",)),
    ("sh_heavy", ("knight_shield", "overseer_bulwark")), ("sh_guard", ("knight_shield", "twinborne")),
    ("sh_block", ("knight_shield",)), ("sh_parry", ("knight_shield",)), ("sh_break", ("knight_shield",)),
    ("sh_counter", ("knight_shield",)),
    ("tw_1", ("twinfangs",)), ("tw_2", ("twinfangs",)), ("tw_3", ("twinfangs",)), ("tw_4", ("twinfangs",)),
    ("tw_5", ("twinfangs",)), ("tw_heavy", ("twinfangs",)),
    ("counter", ("longsword", "colossus_hammer")), ("backstep", ("first_ember", "stormvein")),
    ("plunge", ("longsword", "glacier_maul")), ("plunge_fall", ("longsword", "glacier_maul")),
    ("plunge_land", ("longsword", "glacier_maul")), ("sp_jump", ("stormfang",)), ("sp_dive", ("stormfang",)),
    ("idle", ("knight_shield", "twinfangs", "lantern_staff")), ("run", ("overseer_bulwark", "twinfangs")),
    ("sh_rest", ("knight_shield", "twinborne")),
    ("art_whirlwind", ("quarterstaff",)), ("art_gale_vault", ("windstaff",)), ("art_ink_mark", ("inkquill",)),
    ("art_aegis", ("knight_shield",)), ("art_frost_aegis", ("twinborne",)), ("art_shield_charge", ("overseer_bulwark",)),
    ("art_magma_quake", ("colossus_hammer",)), ("art_thunder_lunge", ("stormfang",)), ("art_tolling_blow", ("bell_hammer",)),
    ("art_twin_tempest", ("twinfangs",)), ("art_backstep_slash", ("longsword", "katana")),
    ("sc_1", ("briar_scythe", "antler_scythe")), ("sc_2", ("crimson_scythe",)), ("sc_3", ("last_kindling", "antler_scythe")),
    ("sc_heavy", ("briar_scythe", "last_kindling")),
    ("wh_1", ("gravechain", "headsman_chain")), ("wh_2", ("orrery_whip",)), ("wh_3", ("gravechain", "orrery_whip")),
    ("wh_heavy", ("headsman_chain",)), ("idle", ("headsman_chain", "antler_scythe")), ("run", ("gravechain",)),
    ("art_reap", ("briar_scythe",)), ("art_harvest_moon", ("antler_scythe",)), ("art_lash", ("gravechain",)),
    ("art_chain_drag", ("headsman_chain",)), ("art_blood_frenzy", ("sanguine_rapier",)), ("art_tidal_surge", ("choir_harpoon",)),
    ("art_solar_flare", ("pharaoh_khopesh",)), ("art_starfall", ("starblade",)), ("art_overclock", ("plasma_katana",)),
    ("art_pale_pyre", ("last_kindling",)),
    ("swim", ("longsword", "greatsword", "knight_shield", "gravechain")), ("tread", ("longsword", "spear", "twinfangs")),
]


def expansion_preview(raw, tags, body_comp, wpn, prev_dir, scale=3):
    from PIL import ImageDraw
    rows, labels = [], []
    tagd = {t: (a, b) for t, a, b in tags}
    for t, kinds in V8_PREVIEW:
        for kind in kinds:
            if kind not in wpn or t not in tagd:
                continue
            a, b = tagd[t]
            rows.append([over(body_comp[i], wpn[kind][i]) for i in range(a, b + 1)])
            labels.append((t, kind, [raw[i][1] for i in range(a, b + 1)], ACTIVE.get(t, (0, -1))))
    if not rows:
        return
    sh = grid_sheet(rows)
    lw = 34
    out = Image.new("RGBA", (sh.width + lw, sh.height), (92, 92, 100, 255))
    out.alpha_composite(sh, (lw, 0))
    d = ImageDraw.Draw(out)
    for ry, (_, _, _, act) in enumerate(labels):
        for i in range(act[0], act[1] + 1):
            x = lw + i * (W + 1)
            d.line([(x, ry * (H + 1) + H - 1), (x + 5, ry * (H + 1) + H - 1)], fill=(255, 196, 90, 255))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(out)
    for ry, (name, kind, mss, _) in enumerate(labels):
        y = ry * (H + 1) * scale
        d.text((4, y + 4), name, fill=(255, 255, 255, 255))
        d.text((4, y + 18), kind[:13], fill=(200, 200, 210, 255))
        d.text((4, y + 32), f"{sum(mss)}ms", fill=(200, 200, 210, 255))
        for i, ms in enumerate(mss):
            d.text(((lw + i * (W + 1)) * scale + 3, y + 3), f"{i}:{ms}", fill=(255, 220, 150, 255))
    out.save(os.path.join(prev_dir, "expansion.png"))
    # new weapons lineup: each over a few frames of its own class
    CLS_TAGS = {"staff": ["idle", "st_1", "st_4"], "shield": ["idle", "sh_1", "sh_guard"], "twin": ["idle", "tw_3"],
                "great": ["idle", "gs_1"], "spear": ["idle", "sp_3"], "katana": ["idle", "kt_1"], "dagger": ["idle", "dg_2"],
                "sword": ["idle", "attack1", "heavy"], "scythe": ["idle", "sc_1", "sc_3"], "whip": ["idle", "wh_1", "wh_3"]}
    KCLS = {"frostbrand": "sword", "pagecutter": "dagger", "colossus_hammer": "great", "glacier_maul": "great",
            "bell_hammer": "great", "forge_cleaver": "great", "stormfang": "spear", "stormvein": "katana",
            "quarterstaff": "staff", "windstaff": "staff", "inkquill": "staff", "lantern_staff": "staff",
            "knight_shield": "shield", "twinborne": "shield", "overseer_bulwark": "shield", "twinfangs": "twin",
            "first_ember": "sword",
            "antler_scythe": "scythe", "briar_scythe": "scythe", "crimson_scythe": "scythe", "last_kindling": "scythe",
            "thornwood_staff": "staff", "sun_sceptre": "staff", "choir_harpoon": "spear", "scarab_spear": "spear",
            "saint_lance": "spear", "sanguine_rapier": "sword", "pharaoh_khopesh": "sword", "barnacle_fang": "dagger",
            "carving_knife": "dagger", "tidecleaver": "great", "vael_greatsword": "great", "meteor_maul": "great",
            "starblade": "katana", "plasma_katana": "katana", "headsman_chain": "whip", "gravechain": "whip", "orrery_whip": "whip"}
    rows = []
    for kind in V8_IDS + V9_IDS:
        if kind not in wpn:
            continue
        r = []
        for t in CLS_TAGS[KCLS[kind]]:
            a, b = tagd[t]
            r += [over(body_comp[i], wpn[kind][i]) for i in range(a, b + 1)] + [None]
        rows.append(r[:-1])
    if rows:
        sh = grid_sheet(rows)
        sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(os.path.join(prev_dir, "weapons_v8.png"))


def main(build=True, kinds=None, previews=True):
    global _RAW
    raw, tags = [], []
    for name, fn in ANIMS:
        start = len(raw)
        raw += list(fn())
        tags.append((name, start, len(raw) - 1))
    body = [imgs(c, None) for c, _ in raw]
    body_comp = [compose(b) for b in body]
    kinds = kinds or WPN_IDS
    _RAW = raw
    import multiprocessing as mp
    with mp.get_context("fork").Pool(min(16, len(kinds))) as pool:
        wpn = dict(zip(kinds, pool.map(_wpn_frames, kinds)))
    if build:
        from concurrent.futures import ThreadPoolExecutor
        jobs = [("player", BODY_LAYERS, [{"ms": ms, "cels": b} for b, (_, ms) in zip(body, raw)])]
        for kind in kinds:
            jobs.append(("wpn_" + kind, ["Weapon"], [{"ms": ms, "cels": ({"Weapon": w} if w is not None else {})}
                                                    for w, (_, ms) in zip(wpn[kind], raw)]))
        with ThreadPoolExecutor(3) as ex:   # a few Aseprite instances at once (many at once can hang)
            list(ex.map(lambda j: _ase_build(j[0], W, H, j[1], j[2], tags), jobs))
    prev_dir = os.path.join(asebuild.ART, "previews")
    os.makedirs(prev_dir, exist_ok=True)
    if previews and "longsword" in wpn:
        # player preview: one row per animation, 3x, mid-grey (body + longsword)
        rows = [[over(body_comp[i], wpn["longsword"][i]) for i in range(a, b + 1)] for _, a, b in tags]
        grid_sheet(rows).resize(((max(len(r) for r in rows)) * (W + 1) * 3, len(rows) * (H + 1) * 3),
                                Image.NEAREST).save(os.path.join(prev_dir, "player.png"))
    if previews and all(k in wpn for k in WPN_IDS):
        rows = []
        for kind in WPN_IDS:
            r = []
            for t in PREVIEW_TAGS:
                _, a, b = next(x for x in tags if x[0] == t)
                r += [over(body_comp[i], wpn[kind][i]) for i in range(a, b + 1)] + [None]
            rows.append(r[:-1])
        sh = grid_sheet(rows)
        sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(os.path.join(prev_dir, "weapons.png"))
        movesets_preview(raw, tags, body_comp, wpn, prev_dir)
        arts_preview(raw, tags, body_comp, wpn, prev_dir)
        techniques_preview(raw, tags, body_comp, wpn, prev_dir)
    expansion_preview(raw, tags, body_comp, wpn, prev_dir)
    if build:
        write_meta(raw, tags)
    old = os.path.join(prev_dir, "player_preview.png")
    if os.path.exists(old):
        os.remove(old)
    print("player:", len(raw), "frames;", [(t, a, b) for t, a, b in tags])
    return raw, tags, body_comp, wpn


if __name__ == "__main__":
    _kinds = None
    for _a in sys.argv:
        if _a.startswith("--kinds="):
            _kinds = _a.split("=", 1)[1].split(",")
    if "--fx" in sys.argv:
        fx_main()
    else:
        main(build="--preview-only" not in sys.argv, kinds=_kinds)
