#!/usr/bin/env python3
"""Morvain phase 2 -- "The Eclipsed Crown": the arena the Throne of Ash dissolves into, and its fighters.

    python3 art/omen_bg.py            build everything through Aseprite
    python3 art/omen_bg.py --preview  previews only (art/previews/omen_bg_*.png)

Outputs (assets/ + art/*.aseprite):
    bg_omen_far   512x216  golden eclipse sky: the black sun wearing a crown of light, a cathedral of light
    bg_omen_mid   512x216  broken gilded arches, floating crown shards, the spectral spear ranks on the far ledge
    omen_colossus 352x256  a colossal spectral echo of Morvain (rig from gen_boss, re-lit as a ghost at 2x)
                           tags idle raise swing recover   (the background knights that sweep the arena lanes)
    fx_om_blade   96x96    the thrown greatsword, spinning (8)
    fx_om_crescent 48x72   crescent wave of light (4)
    fx_om_shard   16x36    a falling crown shard (4)
"""
import math, os, sys
import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import gen_boss as gb  # noqa: E402

BW, BH = 512, 216
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hexc(h, a=255):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), a)


SKY = [hexc(h) for h in ("#050309", "#0b0712", "#140c1c", "#1f1224", "#2f1826", "#452024", "#642d20",
                         "#8a421e", "#b5601f", "#dc8a2c", "#f3b95a")]
GOLD = [hexc(h) for h in ("#2b1a0e", "#4f3314", "#7d5519", "#b2822a", "#dfb24a", "#fbe7a0", "#fffbe8")]
GHOST = [hexc(h) for h in ("#0d0a14", "#161020", "#211829", "#2e2234", "#40303f", "#5a4452", "#7a5f62")]
ASH = [hexc(h) for h in ("#0a0710", "#140d18", "#1e1420", "#2c1c26", "#3d262a")]


def quant(v, pal, x, y):
    """v in 0..1 -> palette entry with 4x4 ordered dither between neighbouring steps."""
    n = len(pal) - 1
    f = np.clip(v, 0, 1) * n
    i = np.floor(f).astype(int)
    fr = f - i
    th = BAYER[y % 4, x % 4]
    i = np.where(fr > th, i + 1, i)
    return np.clip(i, 0, n)


def to_img(idx, pal, alpha=None):
    arr = np.array(pal, dtype=np.uint8)[idx]
    if alpha is not None:
        arr[..., 3] = np.where(alpha, arr[..., 3], 0)
    return Image.fromarray(arr, "RGBA").copy()


def vnoise(w, h, sx, sy, seed, wrap=True):
    rng = np.random.RandomState(seed)
    gx, gy = int(math.ceil(w / sx)) + 2, int(math.ceil(h / sy)) + 2
    grid = rng.rand(gy, gx)
    if wrap:
        gxw = w // sx
        grid[:, gxw:] = grid[:, :gx - gxw]
    ys, xs = np.mgrid[0:h, 0:w]
    fx, fy = xs / sx, ys / sy
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = grid[y0, x0] * (1 - tx) + grid[y0, x0 + 1] * tx
    b = grid[y0 + 1, x0] * (1 - tx) + grid[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


def fbm(w, h, sx, sy, seed, oct=3):
    v, amp, tot = 0, 1.0, 0
    for o in range(oct):
        v = v + vnoise(w, h, max(2, sx >> o), max(2, sy >> o), seed + o * 17) * amp
        tot += amp; amp *= 0.5
    return v / tot


SUN = (212, 58, 27)   # black sun centre + radius (far layer)


# =========================================================================== far layer
def build_far():
    ys, xs = np.mgrid[0:BH, 0:BW]
    # sky: near-black vault -> burning amber horizon band, brightest under the sun
    v = 0.06 + 0.62 * np.clip((ys - 10) / 140.0, 0, 1) ** 1.6
    dx = np.minimum(np.abs(xs - SUN[0]), BW - np.abs(xs - SUN[0]))
    glow = np.exp(-((dx / 150.0) ** 2) - (((ys - SUN[1]) / 110.0) ** 2))
    v += 0.28 * glow
    v -= 0.2 * np.clip((ys - 156) / 20.0, 0, 1)
    # ash cloud bands, lit from below
    cl = fbm(BW, BH, 64, 10, 11)
    band = np.exp(-(((ys - 96) / 24.0) ** 2)) + 0.6 * np.exp(-(((ys - 134) / 12.0) ** 2))
    v += (cl - 0.5) * 0.35 * band
    v += (fbm(BW, BH, 128, 32, 3) - 0.5) * 0.08
    idx = quant(v, SKY, xs, ys)
    img = to_img(idx, SKY)
    px = img.load()
    # sun corona: soft rings + a crown of long rays (taller at the top)
    cx, cy, R = SUN
    for y in range(BH):
        for x in range(BW):
            ddx = x - cx
            if ddx > BW / 2: ddx -= BW
            if ddx < -BW / 2: ddx += BW
            d = math.hypot(ddx, y - cy)
            a = math.atan2(y - cy, ddx)
            if d < R - 0.5:
                px[x, y] = hexc("#020104") if d < R - 2.5 else hexc("#0a0508")
                continue
            if d < R + 1.6:
                px[x, y] = GOLD[6] if (y - cy) < R * 0.2 else GOLD[5]
                continue
            # rays: 24 thin spikes, the upper ones long like a crown
            k = (a + math.pi) / (2 * math.pi) * 24
            fr = abs(k - round(k))
            up = max(0.0, -math.sin(a))
            ln = R * (0.35 + 0.9 * up ** 1.5) * (1.0 if int(round(k)) % 2 == 0 else 0.55)
            if fr < 0.09 * (1 - (d - R) / (ln + 1)) and d < R + ln:
                t = (d - R) / (ln + 1)
                px[x, y] = GOLD[6] if t < 0.2 else GOLD[5] if t < 0.45 else GOLD[4] if t < 0.75 else GOLD[3]
                continue
            # halo falloff (dithered)
            h = math.exp(-((d - R) / 11.0))
            if h > 0.15 and BAYER[y % 4, x % 4] < h * 0.9:
                px[x, y] = GOLD[5] if h > 0.7 else GOLD[4] if h > 0.45 else GOLD[3]
    # the cathedral of light on the horizon: thin gilded ribs and spires (ghost architecture)
    def gl(x, y, c):
        x %= BW
        if 0 <= y < BH:
            px[x, y] = c

    def spire(x0, base, top, w):
        for y in range(top, base):
            t = (y - top) / max(1, base - top)
            hw = max(0, int(w * t ** 0.7))
            gl(x0 - hw, y, GOLD[3]); gl(x0 + hw, y, GOLD[2])
            if y % 9 == 0:
                for xx in range(x0 - hw, x0 + hw + 1):
                    gl(xx, y, GOLD[2] if xx % 2 else GOLD[1])
        gl(x0, top - 1, GOLD[5]); gl(x0, top - 2, GOLD[4])

    for (x0, base, top, w) in ((40, 156, 72, 7), (96, 156, 98, 5), (330, 156, 64, 8), (386, 156, 92, 5),
                               (452, 156, 80, 6), (150, 156, 110, 4), (270, 156, 106, 4)):
        spire(x0, base, top, w)
    for (ax0, ax1, top) in ((40, 96, 110), (330, 386, 106), (386, 452, 116)):   # arches between spires
        for x in range(ax0, ax1 + 1):
            t = (x - ax0) / (ax1 - ax0)
            y = int(top + (156 - top) * (1 - math.sin(t * math.pi)) * 0.55)
            gl(x, y, GOLD[3]); gl(x, y + 1, GOLD[1])
    # dark ash dunes / far ruins silhouette at the horizon
    ridge = 156 + 6 * (fbm(BW, 1, 48, 1, 5)[0] - 0.5) * 2
    for x in range(BW):
        for y in range(int(ridge[x]), BH):
            px[x, y] = ASH[1] if y > ridge[x] + 3 else ASH[3]
        px[x, int(ridge[x])] = GOLD[2] if abs(((x - SUN[0] + BW / 2) % BW) - BW / 2) < 120 else ASH[4]
    return img


# =========================================================================== mid layer
def ghost_knight(px, x0, base, h, spear=True, seed=0):
    """A small kneeling-rank spectral knight silhouette with an upright spear (the Spear Choir)."""
    w = max(3, h // 4)
    head = (x0, base - h + 3)
    for y in range(base - h + 6, base):
        t = (y - (base - h + 6)) / max(1, h - 6)
        hw = int(w * (0.55 + 0.45 * min(1, t * 1.6)))   # shoulders -> cloak
        for x in range(x0 - hw, x0 + hw + 1):
            if 0 <= x < BW:
                px[x, y] = GHOST[2] if x < x0 + hw - 1 else GHOST[1]
        if 0 <= x0 - hw < BW:
            px[x0 - hw, y] = GOLD[2] if t < 0.5 else GHOST[4]
    for dy in range(-3, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) < 4 and 0 <= x0 + dx < BW:
                px[x0 + dx, head[1] + dy] = GHOST[3]
    if 0 <= x0 - 1 < BW:
        px[x0 - 1, head[1]] = GOLD[5]   # eye slit
    for k in (-2, 0, 2):                  # crown points
        if 0 <= x0 + k < BW:
            px[x0 + k, head[1] - 4] = GOLD[3]
    if spear:
        sx = x0 + w + 1
        for y in range(base - h - 10, base):
            if 0 <= sx < BW:
                px[sx, y] = GHOST[4]
        for y in range(base - h - 14, base - h - 9):
            if 0 <= sx < BW:
                px[sx, y] = GOLD[5] if y < base - h - 12 else GOLD[4]


def build_mid():
    img = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    px = img.load()
    ys, xs = np.mgrid[0:BH, 0:BW]
    # the far ledge where the spear choir stands (y 190..216)
    LEDGE = 150
    n = fbm(BW, BH, 32, 8, 21)
    for x in range(BW):
        top = LEDGE + int((n[0, x] - 0.5) * 4)
        for y in range(top, BH):
            v = 0.2 + 0.5 * (1 - (y - top) / 30.0) + (n[y, x] - 0.5) * 0.3
            px[x, y] = ASH[int(np.clip(v * 4, 0, 4))]
        px[x, top] = GOLD[2] if x % 5 else GOLD[3]
    # two ranks of the Spear Choir along the ledge (their spear tips are what glints before a volley)
    for i, x0 in enumerate(range(8, BW, 22)):
        ghost_knight(px, x0 + (i % 2) * 4, LEDGE + 1, 17 + (i % 3), seed=i)
    # broken gilded arches framing the view (left and right of the 512 tile)
    def arch(cx, span, spring, top, thick, broken):
        for t in np.linspace(0, math.pi, 900):
            if broken[0] <= t <= broken[1]:
                continue
            x = cx - math.cos(t) * span / 2
            y = spring - math.sin(t) * (spring - top)
            for dy in range(0, thick):
                for dx in range(-1, 2):
                    nx, ny = int(x + dx + math.cos(t) * dy * 0.8), int(y + dy * max(0.5, math.sin(t)))
                    if 0 <= nx < BW and 0 <= ny < BH and px[nx, ny][3] == 0 or (0 <= nx < BW and 0 <= ny < BH and dy > 0):
                        px[nx, ny] = GOLD[3] if dy == 0 else GHOST[3] if dy == 1 else GHOST[1]
        for side in (-1, 1):
            x = int(cx + side * span / 2)
            for y in range(int(spring), LEDGE):
                for k in range(thick + 2):
                    xx = x - side * k
                    if 0 <= xx < BW:
                        px[xx, y] = GOLD[3] if k == 0 and side < 0 else GHOST[2] if k < thick else GHOST[1]
    arch(120, 150, 84, 10, 6, (1.7, 2.3))
    arch(390, 130, 90, 22, 5, (0.6, 1.1))
    # floating crown shards drifting above the ranks
    rng = np.random.RandomState(7)
    for k in range(16):
        cx, cy = rng.randint(0, BW), rng.randint(24, 128)
        L = rng.randint(5, 12)
        ang = rng.uniform(-0.5, 0.5)
        for u in range(-L, L + 1):
            wv = max(0, int(2.2 * (1 - abs(u) / (L + 1))))
            for v in range(-wv, wv + 1):
                x = int(cx + math.sin(ang) * u + math.cos(ang) * v)
                y = int(cy - math.cos(ang) * u + math.sin(ang) * v)
                if 0 <= x < BW and 0 <= y < BH:
                    px[x, y] = GOLD[5] if v < 0 else GOLD[3] if v == 0 else GOLD[1]
    return img


# =========================================================================== the colossal echoes (background knights)
CW, CH = 352, 256


def ghostify(flat):
    """Rig frame (176x128) -> smooth 2x spectral silhouette: cool violet body, gold rim, glowing blade/eyes."""
    src = np.array(flat).astype(float)
    a = src[..., 3] / 255.0
    lum = (0.3 * src[..., 0] + 0.59 * src[..., 1] + 0.11 * src[..., 2]) / 255.0
    hot = (src[..., 0] > 200) & (src[..., 1] > 120) & (src[..., 2] < 200) & (a > 0)   # gold glow / smear
    A = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((CW, CH), Image.BILINEAR)) / 255.0
    Lm = np.array(Image.fromarray((lum * 255).astype(np.uint8)).resize((CW, CH), Image.BILINEAR)) / 255.0
    Hm = np.array(Image.fromarray((hot * 255).astype(np.uint8)).resize((CW, CH), Image.BILINEAR)) / 255.0
    mask = A > 0.5
    ys, xs = np.mgrid[0:CH, 0:CW]
    v = 0.28 + Lm * 1.6 + 0.12 * (1 - ys / CH)
    idx = quant(v, GHOST, xs, ys)
    out = np.array(GHOST, dtype=np.uint8)[idx]
    # glow keeps its heat
    gi = np.clip((Hm - 0.35) * 2.2, 0, 1)
    gidx = quant(0.45 + gi * 0.55, GOLD, xs, ys)
    gcol = np.array(GOLD, dtype=np.uint8)[gidx]
    hm = Hm > 0.35
    out[hm] = gcol[hm]
    mask |= hm
    # rim: top/left edges lit gold by the sun, others a pale ghost line
    up = np.roll(mask, 1, 0); up[0] = False
    lf = np.roll(mask, 1, 1); lf[:, 0] = False
    dn = np.roll(mask, -1, 0); dn[-1] = False
    rt = np.roll(mask, -1, 1); rt[:, -1] = False
    edge_top = mask & (~up | ~lf)
    edge_bot = mask & (~dn | ~rt)
    up2 = np.roll(up, 1, 0); up2[0] = False
    edge_top2 = mask & up & ~up2 & ~edge_top
    out[edge_bot & ~hm] = GHOST[6]
    out[edge_top2 & ~hm] = GOLD[2]
    out[edge_top & ~hm] = GOLD[4]
    # dissolve into mist toward the bottom (dithered)
    fade = np.clip((ys - 176) / 80.0, 0, 1)
    keep = (BAYER[ys % 4, xs % 4] >= fade) | hm
    out[..., 3] = np.where(mask & keep, 255, 0)
    return Image.fromarray(out, "RGBA")


def colossus_frames():
    P_ = gb.P_
    WB = dict(wlayer="WeaponBack")
    poses = [
        ("idle", 400, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
        ("idle", 400, P_(P=(100, 86), C=(98, 63), Hd=(94, 42), grip=(80, 85), wang=147, cape_wind=1.2)),
        ("raise", 160, P_(P=(101, 86), C=(103, 62), Hd=(99, 42), tw=0.7, grip=(98, 50), wang=316, **WB,
                          foot_near=(78, 127), foot_far=(122, 127))),
        ("raise", 200, P_(P=(103, 90), C=(108, 63), Hd=(104, 44), tw=1.1, grip=(108, 36), wang=328, **WB,
                          foot_near=(76, 127), foot_far=(124, 127), eyes=1.5)),
        ("raise", 300, P_(P=(104, 92), C=(111, 67), Hd=(106, 49), tw=1.4, grip=(116, 74), wang=356, **WB,
                          foot_near=(70, 127), foot_far=(126, 127), look=-1, eyes=2.0, cape_wind=-1)),
        ("swing", 70, P_(P=(95, 97), C=(83, 75), Hd=(73, 56), tw=-1.2, grip=(64, 102), wang=181,
                         foot_near=(62, 127), foot_far=(125, 127), cape_wind=4, cape_flare=6, tab_wind=4,
                         fx=[("hsweep", (96, 110), 22, 88, 0.16, -12, 178)])),
        ("swing", 110, P_(P=(96, 96), C=(86, 74), Hd=(76, 55), tw=-1.0, grip=(66, 104), wang=170,
                          foot_near=(63, 127), foot_far=(124, 127), cape_wind=3,
                          fx=[("hsweep", (96, 110), 26, 86, 0.16, 110, 190, 0.45)])),
        ("swing", 160, P_(P=(96, 96), C=(86, 74), Hd=(76, 55), tw=-1.0, grip=(66, 104), wang=170,
                          foot_near=(63, 127), foot_far=(124, 127), cape_wind=2)),
        ("recover", 220, P_(P=(99, 90), C=(93, 67), Hd=(86, 47), tw=-0.4, grip=(74, 94), wang=156,
                            foot_near=(70, 127), foot_far=(122, 127), cape_wind=1)),
        ("recover", 260, P_(P=(100, 85), C=(98, 61), Hd=(93, 40), grip=(80, 84), wang=148)),
    ]
    sec = gb.secondary([(ms, p) for _, ms, p in poses], loop=False)
    frames, tags = [], []
    for i, (tag, ms, p) in enumerate(poses):
        L, FX, info = gb.render(p, i, sec[i])
        imgs = gb.compose(L, FX, info)
        p2 = gb.p2_layers(info, i, 0.8, imgs)
        flat = gb.flatten({**imgs, **p2}, [n for n in gb.P2_ORDER if n not in ("Cracks", "Embers")])
        frames.append({"ms": ms, "cels": {"Ghost": ghostify(flat)}})
        if not tags or tags[-1][0] != tag:
            tags.append([tag, i, i])
        else:
            tags[-1][2] = i
    return frames, [tuple(t) for t in tags]


# =========================================================================== small fx
def fx_blade_frames():
    S = 96
    frames = []
    for k in range(8):
        ang = k * 45
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        pxd = img.load()
        # centre the blade's midpoint on the frame: grip placed so u=22 lands at the centre
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        grip = (S / 2 - ca * 22, S / 2 - sa * 22)
        wpx, edge = gb.weapon_geom(grip, ang, 1)
        for (x, y), c in wpx.items():
            if 0 <= x < S and 0 <= y < S:
                pxd[x, y] = gb.RGBA[c]
        # motion arc trailing behind the spin
        for t in range(1, 26):
            a2 = math.radians(ang - t * 3.2)
            for r in (30, 31, 32):
                x, y = int(S / 2 + math.cos(a2) * r), int(S / 2 + math.sin(a2) * r)
                if 0 <= x < S and 0 <= y < S and pxd[x, y][3] == 0:
                    pxd[x, y] = gb.RGBA["Y2" if t < 6 else "Y1" if t < 14 else "Y0"]
        frames.append({"ms": 45, "cels": {"FX": img}})
    return frames


def fx_crescent_frames():
    w, h = 48, 72
    frames = []
    for k in range(4):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pxd = img.load()
        for y in range(h):
            for x in range(w):
                d1 = math.hypot((x - 14) / 1.0, (y - h / 2) / 1.25)
                d2 = math.hypot((x - 5) / 1.0, (y - h / 2) / 1.3)
                if d1 < 28 and d2 > 26 - k * 0.5:
                    t = (d1 - (d2 - 26)) / 28
                    edge = 28 - d1
                    c = "Y3" if edge < 2 else "Y2" if edge < 4.5 else "Y1" if edge < 8 else "Y0"
                    if edge >= 8 and (x + y + k) % 3:
                        continue
                    pxd[x, y] = gb.RGBA[c]
        for i in range(6):   # streaks trailing back
            y = int(h / 2 + (i - 2.5) * 9)
            for x in range(0, 10 + (i * 5 + k * 3) % 8):
                if 0 <= y < h and pxd[x, y][3] == 0:
                    pxd[x, y] = gb.RGBA["Y1" if x > 6 else "Y0"]
        frames.append({"ms": 60, "cels": {"FX": img}})
    return frames


def fx_shard_frames():
    w, h = 16, 36
    frames = []
    for k in range(4):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pxd = img.load()
        for y in range(h):
            t = y / (h - 1)
            hw = 5.2 * (1 - abs(t - 0.28) / 0.72) if t > 0.28 else 5.2 * (t / 0.28) ** 0.6
            for x in range(w):
                d = x + 0.5 - w / 2
                if abs(d) <= hw:
                    c = GOLD[5] if d < -hw * 0.3 else GOLD[4] if d < 0.4 else GOLD[2]
                    if abs(d) > hw - 1:
                        c = GOLD[1] if d > 0 else GOLD[4]
                    if int(y) == (4 + k * 8) % h and d < 0:
                        c = GOLD[6]
                    pxd[x, y] = c
        frames.append({"ms": 70, "cels": {"FX": img}})
    return frames


def main():
    prev = "--preview" in sys.argv
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    far, mid = build_far(), build_mid()
    comp = far.copy(); comp.alpha_composite(mid)
    comp.resize((BW * 2, BH * 2), Image.NEAREST).save(os.path.join(ART, "previews", "omen_bg_comp.png"))
    cf, ctags = colossus_frames()
    cs = Image.new("RGBA", (CW * len(cf) // 2, CH), (28, 20, 30, 255))
    for i, f in enumerate(cf):
        cs.alpha_composite(f["cels"]["Ghost"].resize((CW // 2, CH // 2), Image.NEAREST), (i * CW // 2, 0))
    cs.save(os.path.join(ART, "previews", "omen_colossus.png"))
    bl, cr, sh = fx_blade_frames(), fx_crescent_frames(), fx_shard_frames()
    if prev:
        return
    asebuild.build("bg_omen_far", BW, BH, ["Sky"], [{"ms": 1000, "cels": {"Sky": far}}], [("loop", 0, 0)])
    asebuild.build("bg_omen_mid", BW, BH, ["Ruins"], [{"ms": 1000, "cels": {"Ruins": mid}}], [("loop", 0, 0)])
    asebuild.build("omen_colossus", CW, CH, ["Ghost"], cf, ctags)
    asebuild.build("fx_om_blade", 96, 96, ["FX"], bl, [("spin", 0, 7)])
    asebuild.build("fx_om_crescent", 48, 72, ["FX"], cr, [("wave", 0, 3)])
    asebuild.build("fx_om_shard", 16, 36, ["FX"], sh, [("fall", 0, 3)])


if __name__ == "__main__":
    main()
