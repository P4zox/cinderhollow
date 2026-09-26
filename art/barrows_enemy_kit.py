"""Helpers for gen_barrows_enemies.py (the Drowned Barrows enemies, agent B's art sub-agent).

Built on enemy_kit.py + spire_enemy_kit.py (read-only reuse: normals, outline renderer, anim driver, hit rects,
hitbox preview, Aseprite export). Adds the Drowned Barrows ramps (process-local, multi-letter keys so they can
never collide with other kits' single-letter ramps):

    dF  drowned flesh, pale grey-green        #6f7f78 .. #a9b5ab at the lit end
    dC  sodden black-teal cloth
    dV  verdigris bronze                     dB  pale drowned bone (faintly green)
    dS  chalky barnacle shell                dE  eel skin, black-green (glossy)
    dK  dark chitin (crawler legs)
    dG  bioluminescent glow (fixed)          #0e3b3a #17736b #2fbfb0 #8ff0e0 #e6fffa
    dW  black water + foam (fixed)
Outline colour is the region's near-black (8,7,12).
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import spire_enemy_kit as S  # noqa: E402  (helpers: render_anims, hit_rect, hurtbox, export, verify, n_tube...)
from enemy_kit import hash01, ip, line, polyline, mask_disc  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402

RAMPS = {
    "dF": ["#1c2322", "#2f3a37", "#4a5752", "#6f7f78", "#8d9c93", "#a9b5ab"],
    "dC": ["#090e11", "#111b1f", "#19272b", "#233638", "#2f4747", "#43615d"],
    "dV": ["#0f1f1c", "#1a3832", "#28574a", "#3a7a66", "#58a086", "#8ac6a8"],
    "dB": ["#23241f", "#403f36", "#646152", "#8c8a76", "#b5b49d", "#dcdcc6"],
    "dS": ["#1c201e", "#333a36", "#515953", "#747c74", "#9da398", "#c5c8ba"],
    "dE": ["#050908", "#0a1411", "#12211c", "#1c3029", "#28443a", "#3d5f52", "#6a8f80"],
    "dK": ["#0c1112", "#18221f", "#25332f", "#354a44", "#4f6b62"],
    "dG": ["#0e3b3a", "#17736b", "#2fbfb0", "#8ff0e0", "#e6fffa"],
    "dW": ["#04080a", "#0a1519", "#10242a", "#18373c", "#245052", "#3f7472", "#9fc9c0", "#dcefe8"],
}
for _r, _cols in RAMPS.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"dE": 0.9, "dV": 0.93})
K.RGBA["OUT"] = (8, 7, 12, 255)
K.HEX["OUT"] = "#08070c"
K.SMEAR.update({
    "tide": ["dG4", "dG3", "dG2", "dG1"],
    "brine": ["dW7", "dW6", "dW5", "dW4"],
    "tide2": ["dG3", "dG2", "dG1", "dG0"],
    "claw": ["dF5", "dF4", "dF3", "dF2"],
})
GLOW = ("dG4", "dG3", "dG2", "dG1", "dG0")
STRETCH = []          # limb-length violations (proportion drift) collected while drawing


def check_reach(tag, a, b, lmax):
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    if d > lmax + 0.35:
        STRETCH.append((tag, round(d, 2), lmax))


# =========================================================================== small parts
def barnacles(L, spots, seed=0, bias=0):
    """Cluster of little conical barnacles: spots = [(centre, r)]; each gets a dark pore on top."""
    for k, (c, r) in enumerate(spots):
        L.paint(K.n_dome(c, r, r * 0.9, tilt=(-0.1, -0.15)), "dS", bias, ao=1)
        if r >= 1.0:
            q = ip((c[0] + 0.1, c[1] - r * 0.25))
            L.fixed({q: "dS1" if hash01(k, seed, 3) < 0.6 else "dG1"})


def glow_rim(layer, lc, radius, cols=("dG2", "dG1")):
    """Teal under-light: silhouette pixels that face the light source within radius pick up a glow rim."""
    add_ = {}
    for (x, y), e in layer.px.items():
        dx, dy = lc[0] - (x + .5), lc[1] - (y + .5)
        d = math.hypot(dx, dy)
        if d > radius or d < 0.5:
            continue
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        facing = ((x + sx, y) not in layer.px and abs(dx) > abs(dy) * 0.4) or \
                 ((x, y + sy) not in layer.px and abs(dy) > abs(dx) * 0.4)
        if facing:
            add_[(x, y)] = cols[0] if d < radius * 0.5 else cols[1]
    for p, c in add_.items():
        layer.px[p][3] = c


def halo_dots(FX, c, r, n, fi, cols, skip=()):
    for k in range(n):
        a = k * 2 * math.pi / n + fi * 0.41
        rr = r + (k % 3) * 0.8
        q = ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.9))
        if (k + fi) % 2 == 0 and q not in skip:
            FX.put([q], cols[k % len(cols)])


def drips(FX, sources, fi, floor=None, period=5, fall=2.2, seed=0, skip=()):
    """Black-water drips falling from source points: each source sheds a drop that falls and resets.
    A drop is a 1x2 dark teal streak with a pale glint pixel at the bottom (reads on dark robes)."""
    out = set()
    for k, src in enumerate(sources):
        ph = (fi + int(hash01(k, seed, 7) * period)) % period
        if ph == 0:
            q = ip((src[0], src[1] + 0.6))
            if q not in skip:
                FX.put([q], "dW4")
            continue
        y = src[1] + 0.6 + ph * fall + 0.25 * ph * ph
        if floor is not None and y > floor:
            if y - floor < fall * 1.5:            # tiny splash ring at the floor
                x = int(src[0])
                FX.put([(x - 1, int(floor)), (x + 1, int(floor))], "dW5")
            continue
        q = ip((src[0], y))
        if q in skip:
            continue
        if (q[0], q[1] - 1) not in skip:
            FX.put([(q[0], q[1] - 1)], "dW3")
        FX.put([q], "dW6")
        out.add(q)
    return out


def star(FX, c, r, cols=("dG4", "dG3", "dG2"), diag=True):
    S.star(FX, c, r, cols=cols, diag=diag)


def puddle(FX, x0, x1, y, fi=0, seed=0):
    """Thin black-water pool on the floor row with a pale ripple glint."""
    for x in range(int(x0), int(x1) + 1):
        FX.put([(x, y)], "dW2" if (x + seed) % 4 else "dW3")
    for k in range(2):
        gx = int(x0 + (x1 - x0) * hash01(k, fi, seed + 3))
        FX.put([(gx, y)], "dW5")


# =========================================================================== previews
def dark_preview(names, out, scale=2, bg=(14, 14, 20, 255)):
    """1x + 2x rows of every frame on a dark background (readability check)."""
    rows = []
    for name in names:
        sheet = Image.open(os.path.join(K.asebuild.ASSETS, f"{name}.png")).convert("RGBA")
        rows.append((name, sheet))
    Wt = max(s.width for _, s in rows) * (1 + scale) + 8
    Ht = sum(s.height * scale + 6 for _, s in rows) + 8
    img = Image.new("RGBA", (min(Wt, 6000), Ht), bg)
    y = 4
    for name, s in rows:
        img.alpha_composite(s, (4, y))
        big = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
        img.alpha_composite(big, (8 + s.width, y)) if 8 + s.width + big.width <= img.width else None
        y += s.height * scale + 6
    img.save(out)
