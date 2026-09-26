#!/usr/bin/env python3
"""Mini-boss generator -- "The Orrery Sentinel" (agent SF, Hall of the Orrery).

    python3 art/gen_starfall_orrery.py [--preview]

A clockwork celestial guardian: a dark-bronze core sphere with a single great starlit eye, a crown of gear teeth,
three armillary rings turning on their own axes, a pendulum with a star weight. Its planets are drawn by the engine
(fx_sf_planet) orbiting the core. Frame 128x100, faces RIGHT, anchor [64, 100] (the frame bottom; it floats).
Tags: idle(12 loop) charge(8) sweep(10) slam(10) stagger(6) death(12).
"""
import json, math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, n_dome, mask_disc, line, hash01, ip  # noqa: E402

W, H = 128, 100
K.setup(W, H)
BUILD = "--preview" not in sys.argv
EXTRA = {"X0": "#1a2a66", "X1": "#3a5ac4", "X2": "#7a9cf2", "X3": "#c6d8ff", "X4": "#ffffff",
         # dark bronze
         "Z0": "#140c08", "Z1": "#2a1a0e", "Z2": "#4a2e14", "Z3": "#74481c", "Z4": "#a26c2a", "Z5": "#d6a452"}
for k_, v_ in EXTRA.items():
    K.HEX[k_] = v_
    K.RGBA[k_] = tuple(int(v_[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    K.RAMP.setdefault(k_[0], []).append(k_)
K.SHINY["Z"] = 0.88
LAYERS = ["FXBack", "RingsBack", "Pendulum", "Core", "Eye", "RingsFront", "FX"]
FXL = {"FXBack", "FX"}
CX, CY = 64, 50
RINGS = [(46, 72, 0.0), (37, -58, 1.2), (28, 18, 2.4)]      # radius, tilt (deg, about the x axis), base spin phase


def rot(p, ax, ay, az):
    x, y, z = p
    # about x
    c, s = math.cos(ax), math.sin(ax); y, z = y * c - z * s, y * s + z * c
    # about y
    c, s = math.cos(ay), math.sin(ay); x, z = x * c + z * s, -x * s + z * c
    # about z
    c, s = math.cos(az), math.sin(az); x, y = x * c - y * s, x * s + y * c
    return x, y, z


def draw(p, fi):
    Ls = {n: Layer(n) for n in LAYERS if n not in FXL}
    FX, FXB = FXLayer("FX"), FXLayer("FXBack")
    Ls["FX"], Ls["FXBack"] = FX, FXB
    cx, cy = CX, CY + p.get("sink", 0)
    info = {"ring": set()}
    # ---------------- rings (split by depth: behind / in front of the core)
    for k, (r0, tilt, ph) in enumerate(RINGS):
        if p.get("broken", 0) > 0 and k < p["broken"]:
            continue
        r = r0 * p.get("rs", 1.0) * (p.get("rk", [1, 1, 1])[k])
        tl = math.radians(tilt * p.get("tk", 1.0) + p.get("tadd", [0, 0, 0])[k])
        spin = ph + p["spin"] * (1 if k % 2 == 0 else -1.3) * (1 + k * 0.25)
        n = int(2 * math.pi * r * 1.6)
        back, front = {}, {}
        for i in range(n):
            a = i / n * 2 * math.pi
            for w in (0.0, 0.9):
                x, y, z = rot(((r - w) * math.cos(a), (r - w) * math.sin(a), 0), tl, spin * 0.5, 0.35 * k)
                q = ip((cx + x, cy + y * 0.95 + p.get("drop", [0, 0, 0])[k]))
                notch = int(a / (2 * math.pi) * 24) % 2 == 0 and w > 0
                col = ("Z", 5) if z > r * 0.3 and w == 0 else ("Z", 4) if z > 0 else ("Z", 2) if z > -r * 0.4 else ("Z", 1)
                c = K.RAMP[col[0]][col[1] - (1 if notch else 0)]
                (front if z >= 0 else back)[q] = c
            if i % (n // 4) == 0:                                   # star studs
                x, y, z = rot((r * math.cos(a), r * math.sin(a), 0), tl, spin * 0.5, 0.35 * k)
                q = ip((cx + x, cy + y * 0.95 + p.get("drop", [0, 0, 0])[k]))
                (front if z >= 0 else back)[q] = "X4" if z >= 0 else "X2"
        Ls["RingsBack"].fixed(back)
        Ls["RingsFront"].fixed(front)
        info["ring"] |= set(front) | set(back)
    # ---------------- pendulum
    sw = p.get("sway", 0.0)
    bot = (cx + sw, cy + 44 - p.get("sink", 0) * 0.3)
    for q in line((cx, cy + 15), bot):
        Ls["Pendulum"].fixed({q: "Z2", (q[0] + 1, q[1]): "Z4"})
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0, 2), (0, -2)):
        Ls["Pendulum"].fixed({ip((bot[0] + dx, bot[1] + dy)): "X3" if (dx, dy) == (0, 0) else "X1"})
    FXB.put([ip((bot[0], bot[1] + 3)), ip((bot[0] + 2, bot[1]))], "X2")
    # ---------------- core sphere, iron bands, gear crown
    Co = Ls["Core"]
    R = 15.5
    Co.paint(n_dome((cx, cy), R, R), "Z", 0)
    for lat in (-6, 0, 6):                                          # iron bands
        pts = [ip((cx + math.sqrt(max(0, R * R - lat * lat)) * math.cos(a) * 0.98, cy + lat + math.sin(a) * 1.4))
               for a in [i / 30 * math.pi for i in range(31)]]
        Co.decal(pts, ("K", 2))
    for i in range(10):                                             # gear crown
        a = math.pi + i / 9 * math.pi
        q = (cx + math.cos(a) * (R + 1.8), cy + math.sin(a) * (R + 1.8) * 0.9)
        Co.paint(n_dome(q, 1.6, 1.6), "Z", -1 if i % 2 else 0)
    # cracks of starlight (phase 2 / death)
    cr = p.get("crack", 0.0)
    if cr > 0:
        pts = [(cx - 3, cy - 10), (cx - 5, cy - 4), (cx - 2, cy + 2), (cx - 6, cy + 8)]
        for a, b in zip(pts, pts[1:]):
            Co.decal(line(a, b), "X3" if cr > 0.5 else "X2")
    # ---------------- the eye
    Ey = Ls["Eye"]
    ex, ey = cx + 7.0, cy - 0.5
    glow = p.get("eye", 0.5)
    for y in range(-8, 9):
        for x in range(-6, 7):
            e = (x / 5.4) ** 2 + (y / 7.6) ** 2
            if e <= 1:
                q = ip((ex + x, ey + y))
                if e > 0.78:
                    Ey.fixed({q: "K1"})
                elif e > 0.55:
                    Ey.fixed({q: "X1" if glow > 0.3 else "X0"})
                elif glow < 0.9 and abs(x - p.get("look", 0)) < 0.6 and abs(y) < 4:
                    Ey.fixed({q: "K0"})                                            # the slit
                else:
                    lv = 4 if e < 0.12 + 0.2 * glow else 3 if e < 0.35 else 2
                    if glow < 0.3:
                        lv -= 1
                    Ey.fixed({q: "X%d" % lv})
    if glow > 0.6:
        for k in range(8):
            a = k / 8 * 2 * math.pi + fi * 0.3
            for i in range(9, 9 + int(glow * 5)):
                FX.put([ip((ex + math.cos(a) * i, ey + math.sin(a) * i))], "X2" if i % 2 else "X3")
    # ---------------- extra fx
    for i in range(int(p.get("motes", 0) * 14)):
        FX.put([ip((cx + (hash01(i, fi, 3) - 0.5) * 80, cy + (hash01(i, fi, 4) - 0.5) * 70))], "X3" if i % 3 else "X4")
    imgs = {n: (L.image() if n in FXL else K.render_layer(L)) for n, L in Ls.items()}
    if p.get("dissolve", 0) > 0:
        imgs = K.ember_dissolve(imgs, p["dissolve"], ["Core", "Eye", "Pendulum", "RingsBack", "RingsFront"], fx_name="FX", seed=5, rise=24,
                                pal=("X4", "X3", "X2", "X1", "X0"))
    return imgs, info


def anims():
    A = []
    A.append(("idle", [(dict(spin=i / 12 * 2 * math.pi, sway=math.sin(i / 12 * 2 * math.pi) * 2.5, eye=0.5 + 0.15 * math.sin(i)), 110) for i in range(12)]))
    ch = []
    for i in range(8):
        k = i / 7
        ch.append((dict(spin=k * 1.2, tk=1 - 0.8 * k, rs=1 - 0.25 * k, eye=0.5 + 0.5 * k, sway=0, motes=k, look=1), 110))
    A.append(("charge", ch))
    sw = []
    for i in range(10):
        k = min(1, i / 3)
        wide = 1 + 0.35 * k if i < 8 else 1.1
        sw.append((dict(spin=i * 0.9, rk=[wide, 1, 1], tadd=[18 * k, 0, 0], drop=[30 * k if i < 8 else 12, 0, 0], eye=0.8, sway=-3 + i * 0.6), 60 if 3 <= i <= 7 else 90))
    A.append(("sweep", sw))
    sl = []
    for i in range(10):
        up = [0, -4, -8, -10, -10, 4, 6, 3, 1, 0][i]
        sl.append((dict(spin=i * 0.5, sink=up, eye=1.0 if i < 5 else 0.7, rs=1.15 if i in (5, 6) else 1.0, sway=[0, 1, 2, 3, 3, -4, -3, -1, 0, 0][i], motes=1 if i == 5 else 0), [80, 80, 80, 90, 120, 50, 80, 110, 110, 110][i]))
    A.append(("slam", sl))
    st = []
    for i in range(6):
        st.append((dict(spin=0.3, sink=4 + i, tk=1 + 0.2 * i, eye=0.15 if i % 2 else 0.35, sway=4 - i, crack=0.3), 120))
    A.append(("stagger", st))
    de = []
    for i in range(12):
        k = i / 11
        de.append((dict(spin=0.3 + k, sink=4 + k * 10, eye=max(0, 0.6 - k), crack=1, broken=0 if k < 0.2 else 1 if k < 0.45 else 2 if k < 0.7 else 3,
                        drop=[k * 30, k * 20, k * 10], dissolve=max(0, (k - 0.3) / 0.7 * 0.95), sway=k * 6), 120))
    A.append(("death", de))
    return A


def main():
    out, tags_meta = [], {}
    for tag, frs in anims():
        seq = []
        for fi, (p, ms) in enumerate(frs):
            imgs, info = draw(p, fi)
            seq.append((ms, imgs))
        out.append((tag, seq))
    meta = {"native": 1, "anchor": [64, H], "hurtbox": [47, 32, 34, 62],
            "attacks": {"sweep": {"windows": [{"active": [3, 7], "hit": [0, 72, 128, 22]}]},
                        "slam": {"windows": [{"active": [5, 6], "hit": [26, 30, 76, 70]}]}},
            "spawn": {"eye": {"frame": 0, "at": [70, 52]}}}
    K.export("orrery", LAYERS, out, meta, build=BUILD, flat_order=LAYERS)
    print("orrery", "built" if BUILD else "previewed")


if __name__ == "__main__":
    main()
