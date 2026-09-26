"""NEO-HALLOW creature kit (agent NH): the enemy_kit / gen_enemies3 method with a chrome + neon palette.

Ramps (per process; repurposes letters this family never uses):
  S chrome white (shiny)   U gunmetal navy   X cyan glow (fixed)   T magenta glow (fixed)   R red sensor (fixed)
"""
import math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import gen_enemies3 as E3  # noqa: E402
from enemy_kit import Layer, FXLayer, Rig, ID, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, dirv, bbox  # noqa: E402,F401
from gen_enemies3 import n_tube, curve, mk, spawn_pt, rot, madd, disc_glow, halo_dots  # noqa: E402,F401

NEW = {
    "S": ["#1a1f30", "#39425c", "#667291", "#9ba7c0", "#cdd6e6", "#eef2f9", "#ffffff"],
    "U": ["#05060c", "#0b0e19", "#141a2b", "#20283f", "#303b58", "#46557a"],
    "X": ["#0b4d66", "#13a3c9", "#3fe0ff", "#b8f6ff", "#f2feff"],
    "T": ["#6e0f5c", "#c21d97", "#ff3fc0", "#ff9fe2", "#fff0fb"],
    "R": ["#5a0a18", "#b01530", "#ff3050", "#ff9aa8"],
}
for _r, _cols in NEW.items():
    for _k in [k for k in list(K.HEX) if k[0] == _r and k != "OUT"]:
        del K.HEX[_k]; K.RGBA.pop(_k, None)
    keys = []
    for _i, _c in enumerate(_cols):
        k = f"{_r}{_i}"
        K.HEX[k] = _c
        K.RGBA[k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        keys.append(k)
    K.RAMP[_r] = keys
K.SHINY.update({"S": 0.88, "U": 0.93})
K.SMEAR.update({"cyan": ["X4", "X3", "X2", "X1"], "pink": ["T4", "T3", "T2", "T1"], "chrome": ["S6", "S5", "S4", "S3"]})
K.HEX["OUT"] = "#05060c"; K.RGBA["OUT"] = (5, 6, 12, 255)


def glow_line(FX, a, b, cols=("X3", "X2")):
    pts = line(a, b)
    for i, q in enumerate(pts):
        FX.put([q], cols[i % len(cols)])
    return pts


def circuit(L, pts, col="X2"):
    """Thin circuit trace decal along a polyline, only on the layer's own pixels."""
    ps = [q for q in polyline([ip(p) for p in pts]) if q in L.px]
    L.decal(ps, col)
    return ps
