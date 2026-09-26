"""Shared palette + helpers for agent DU's creature generators (gen_dunes_enemies.py, gen_dunes_scarab.py, gen_dunes_pharaoh.py).

Registers LOWER-CASE material ramps on top of enemy_kit (the upper-case letters belong to other agents' kits), so the Dunes
palette -- aged linen, white-hot sun gold, lapis, mummy skin, jackal black, scarab carapace, amber glow, sand, bronze -- can be
used with the kit's normal-field shading (Layer.paint / Rig.cap / Rig.plate ...).
"""
import math
import enemy_kit as K
from enemy_kit import hash01, ip, line, polyline, mask_disc

RAMPS = {
    # aged mummy linen (warm, dusty)
    "s": ["#241c14", "#3e3224", "#5c4c36", "#7c6a4c", "#a08c68", "#c6b28a", "#e2d4b0"],
    # sun gold (bright, clean -- the sun-kings' gilt)
    "g": ["#3a2208", "#6a4210", "#a06818", "#d09a2a", "#f2c84a", "#fff0a0"],
    # lapis lazuli
    "u": ["#0a1024", "#142450", "#203e80", "#3462aa", "#6292d0"],
    # desiccated mummy skin / tar
    "n": ["#120a08", "#20120e", "#341e16", "#4a2c20", "#643e2c"],
    # jackal black (obsidian, a violet sheen)
    "h": ["#08080c", "#121119", "#1d1b27", "#2c2838", "#3f3a50", "#5a5470"],
    # scarab carapace: black-green with a bronze-gold sheen
    "c": ["#060508", "#0e0c12", "#18141c", "#241e2a", "#342a36", "#4e3e36", "#9a7a3a"],
    # the Scarab Knight's golden carapace (deeper, heavier gold than the gilt)
    "e": ["#241406", "#44280a", "#6e4410", "#9c6418", "#c88a26", "#eab84a", "#fbe08e"],
    # packed sand (sand-soldiers, sand cloak)
    "z": ["#2a1809", "#3f250e", "#573413", "#704518", "#8a581f", "#a86f2a", "#c68c3c", "#dcaa58"],
    # bronze
    "b": ["#1a0e08", "#33200f", "#553616", "#7e5220", "#a8742e", "#d6a04a"],
    # deep crimson-violet (the Pharaoh's inner robe)
    "r": ["#12060c", "#220a14", "#34101e", "#4a1828", "#642236"],
}
FIXED = {
    # amber glow (eyes, sun fire)
    "a0": "#6a2a04", "a1": "#b25a0c", "a2": "#f0901c", "a3": "#ffc04a", "a4": "#fff0b0", "a5": "#fffcf0",
}
for _r, _cols in RAMPS.items():
    keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        keys.append(_k)
    K.RAMP[_r] = keys
for _k, _c in FIXED.items():
    K.HEX[_k] = _c
    K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
K.SHINY.update({"g": 0.86, "b": 0.9, "c": 0.88, "e": 0.96, "h": 0.94})
K.SMEAR.update({
    "sun": ["a5", "a4", "g4", "g3"],
    "sand": ["z7", "z6", "z5", "z4"],
    "khopesh": ["a5", "g5", "g4", "a2"],
    "bronze": ["g5", "b5", "b4", "b3"],
})
AMBER = ("a5", "a4", "a3", "a2", "a1")


def tube(R, L, pts, r0, r1, mat, bias=0, ao=0):
    """Capsule chain through pts, radius tapering r0 -> r1."""
    n = len(pts)
    m = set()
    for i in range(n - 1):
        t0, t1 = i / (n - 1), (i + 1) / (n - 1)
        m |= R.cap(L, pts[i], pts[i + 1], r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1, mat, bias, ao=ao)
    return m


def bands(L, mask, axis_a, axis_b, step=2.2, col=("s", 1), phase=0.0, only=None):
    """Linen wrapping bands: darker lines across a limb/torso mask, perpendicular to a->b."""
    ax, ay = axis_b[0] - axis_a[0], axis_b[1] - axis_a[1]
    l = math.hypot(ax, ay) or 1
    ax, ay = ax / l, ay / l
    pts = []
    for (x, y) in mask:
        u = (x + .5 - axis_a[0]) * ax + (y + .5 - axis_a[1]) * ay
        v = -(x + .5 - axis_a[0]) * ay + (y + .5 - axis_a[1]) * ax
        if ((u + v * 0.35 + phase) % step) < 0.75:
            pts.append((x, y))
    if only is not None:
        pts = [q for q in pts if q in only]
    L.decal(pts, col)
    return pts


def glint(FX, c, core="a5", arm="a3", big=False):
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        FX.put([(x + d[0], y + d[1])], arm)
    if big:
        for d in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 0), (-3, 0)):
            FX.put([(x + d[0], y + d[1])], arm)


def sun_disc(L, c, r, fi=0, glow=0, FX=None, mat="g"):
    """A gilt sun-disc (shaded dome) with an optional flare halo drawn into FX."""
    L.paint(K.n_dome(c, r, r, flat=0.8, tilt=(-0.1, -0.15)), mat, 0, ao=0)
    if glow and FX is not None:
        pal = AMBER
        for q in mask_disc(c, r * 0.7):
            d = math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) / max(0.5, r * 0.7)
            FX.put([q], pal[min(4, int(d * (3 if glow > 1 else 4)))])
        n = 10 + 4 * glow
        for k in range(n):
            a = k * 2 * math.pi / n + fi * 0.4
            rr = r + 1.6 + (k % 2) * (1.0 + glow * 0.8)
            q = ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
            FX.put([q], "a4" if k % 2 == 0 else "a3")
