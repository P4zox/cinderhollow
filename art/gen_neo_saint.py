#!/usr/bin/env python3
"""SAINT-0, the Null Saint (agent NH) -- rework: a biblically-accurate-angel machine (an ophanim of chrome and light).

    python3 art/gen_neo_saint.py [--preview]

The boss is assembled live by the engine from these parts (so every frame keeps identical proportions):
  saint0_socket  80x80  the eye's glowing cavity                                     idle(1)
  saint0_iris    48x48  the cyber-lens iris: segmented cyan ring, magenta blades, a black pupil   spin(8)
  saint0_lid     80x80  the chrome casing + a six-blade iris diaphragm (the eyelid)  aperture(7: 0 shut -> 6 wide)
                        death(6: the casing shatters)
  saint0_lens    14x10  one of the small eyes studding the interlocking rings        open(1) blink(3) fire(2)
  *_wire               the same frames as navy wireframe on transparent (phase 3, the inverted cyberspace arena)
The rotating rings, their lens positions, the feather-of-light wings and the data halo are drawn by the engine.
Previews: art/previews/saint0_parts.png
"""
import math, os, sys
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
from envlib import pick, bt  # noqa: E402

BUILD = "--preview" not in sys.argv
H = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
CHROME = [H(c) for c in ("#1a1f30", "#39425c", "#667291", "#9ba7c0", "#cdd6e6", "#eef2f9", "#ffffff")]
NAVY = [H(c) for c in ("#05060c", "#0b0e19", "#141a2b", "#20283f", "#303b58", "#46557a")]
CY = [H(c) for c in ("#0b4d66", "#13a3c9", "#3fe0ff", "#b8f6ff", "#f2feff")]
MG = [H(c) for c in ("#6e0f5c", "#c21d97", "#ff3fc0", "#ff9fe2", "#fff0fb")]
OUT = H("#05060c")
T = (0, 0, 0, 0)
LIGHT = (-0.55, -0.68, 0.48)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)


def shade(nx, ny, nz, x, y, ramp=CHROME, bias=0.0, spec=True):
    ndl = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    v = 0.12 + 0.95 * max(0.0, ndl) + bias
    if spec and 2 * ndl * nz - LIGHT[2] > 0.9: return ramp[-1]
    return pick(ramp[:-1], min(1.0, v), x, y)


def outline(im):
    src = im.copy(); px = src.load(); w, h = im.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 and any(0 <= x + a < w and 0 <= y + b < h and px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), OUT)
    return im


# ------------------------------------------------------------------ socket
def socket():
    im = Image.new("RGBA", (80, 80), T); px = im.load()
    for y in range(80):
        for x in range(80):
            dx, dy = x + 0.5 - 40, y + 0.5 - 40; r = math.hypot(dx, dy)
            if r > 27: continue
            k = r / 27
            c = pick([NAVY[0], NAVY[1], NAVY[2], CY[0], CY[1]], k ** 2.2, x, y)
            if 25 <= r < 26.2: c = CY[2]
            a = math.atan2(dy, dx)
            if r > 20 and int((a + math.pi) / (2 * math.pi) * 24) % 3 == 0 and abs(r - 22.5) < 0.6: c = CY[1]   # etched rings
            px[x, y] = c
    return im


# ------------------------------------------------------------------ iris
def iris(f):
    im = Image.new("RGBA", (48, 48), T); px = im.load()
    rot = f / 8 * (2 * math.pi / 12)
    for y in range(48):
        for x in range(48):
            dx, dy = x + 0.5 - 24, y + 0.5 - 24; r = math.hypot(dx, dy); a = math.atan2(dy, dx)
            if r > 18: continue
            c = None
            if r > 14.5:                                           # outer segmented cyan ring (rotates)
                seg = int(((a + rot) % (2 * math.pi)) / (2 * math.pi) * 12)
                gap = ((a + rot) % (2 * math.pi / 12)) < 0.12
                c = CY[1] if gap else (CY[3] if r < 16 else CY[2])
                if r > 17.2: c = CY[0]
            elif r > 13.2: c = NAVY[1]
            elif r > 8.0:                                          # magenta blade ring (counter-rotates)
                b = ((a - rot * 1.7 + (r - 8) * 0.18) % (2 * math.pi / 8)) / (2 * math.pi / 8)
                c = MG[3] if b < 0.18 else MG[2] if b < 0.55 else MG[1]
                if r > 12.4: c = MG[0]
            elif r > 6.6: c = CY[2] if int((a - rot * 3) * 6) % 2 else CY[1]    # data ticks
            else: c = NAVY[0]                                     # pupil
            px[x, y] = c
    for (x, y, c) in ((21, 20, CY[4]), (22, 20, (255, 255, 255, 255)), (21, 21, CY[3]), (27, 27, CY[1])):
        px[x, y] = c
    return im


# ------------------------------------------------------------------ lid: chrome casing + diaphragm
def lid(k, broken=0.0, seed=0):
    im = Image.new("RGBA", (80, 80), T); px = im.load()
    ropen = 2.0 + k * 23.5
    for y in range(80):
        for x in range(80):
            dx, dy = x + 0.5 - 40, y + 0.5 - 40; r = math.hypot(dx, dy); a = math.atan2(dy, dx)
            if r > 35.5: continue
            c = None
            if r >= 26.5:                                          # the casing: a chrome torus of 8 plates
                t = (r - 31) / 4.6                                 # -1..1 across the tube
                nz = math.sqrt(max(0.05, 1 - t * t)); nx, ny = t * dx / r, t * dy / r
                seam = abs(((a + math.pi) % (math.pi / 4)) - math.pi / 8) < 0.035 * 35 / r * 1.4 or abs(((a + math.pi) % (math.pi / 4))) < 0.03
                c = shade(nx, ny, nz, x, y)
                if seam: c = CHROME[1]
                if abs(r - 31) < 0.5 and int((a + math.pi) / (2 * math.pi) * 48) % 6 == 0: c = CY[2]   # circuit studs
            elif r >= ropen:                                       # diaphragm blades
                bl = ((a + (r - ropen) * 0.09 + 6.283) % (2 * math.pi / 6)) / (2 * math.pi / 6)
                edge = bl < 0.07
                nz = 0.8; nx, ny = -0.3 * math.cos(a * 6), -0.35
                c = shade(nx, ny, nz, x, y, bias=-0.12 + bl * 0.2, spec=False)
                if edge: c = CHROME[1]
                if r < ropen + 1.2: c = CY[3] if k > 0.15 else CHROME[2]     # lit lip of the aperture
            if c is not None:
                if broken:
                    frag = int((a + math.pi) / (2 * math.pi) * 10) + 10 * int(r / 7)
                    hh = ((frag * 2654435761) >> 7) % 1000 / 1000
                    if hh < broken * 1.05 - 0.05: continue
                    if ((x * 31 + y * 17 + frag) % 11) < broken * 4: continue
                px[x, y] = c
    return outline(im)


# ------------------------------------------------------------------ small ring eyes
def lens(state):
    im = Image.new("RGBA", (14, 10), T); px = im.load()
    op = {"open": 1.0, "half": 0.5, "shut": 0.0, "fire": 1.0, "fire2": 1.0}[state]
    for y in range(10):
        for x in range(14):
            u, v = (x + 0.5 - 7) / 6.6, (y + 0.5 - 5) / 4.2
            if u * u + v * v > 1: continue
            lidh = math.sqrt(max(0, 1 - u * u)) * op
            inside = abs(v) < lidh * 0.72
            if inside:
                d = math.hypot(u * 6.6, v * 4.2)
                c = NAVY[0] if d < 1.3 else CY[2] if d < 2.6 else CY[0]
                if state.startswith("fire"): c = (255, 255, 255, 255) if d < 1.8 else CY[4] if d < 3 else CY[2]
            else:
                c = CHROME[4] if v < 0 else CHROME[2]
                if abs(abs(v) - lidh * 0.72) < 0.22: c = CHROME[1]
            px[x, y] = c
    return outline(im)


def wire_frame(im):
    w, h = im.size; src = im.load(); out = Image.new("RGBA", (w, h), T); o = out.load()
    lum = lambda c: (c[0] * 3 + c[1] * 6 + c[2]) / 10
    for y in range(h):
        for x in range(w):
            c = src[x, y]
            if c[3] == 0: continue
            edge = any(not (0 <= x + a < w and 0 <= y + b < h) or src[x + a, y + b][3] == 0 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            glow = (c[0] > 200 and c[2] > 150 and c[1] < 160) or (c[2] > 200 and c[1] > 180 and c[0] < 120)
            if edge: o[x, y] = (11, 16, 48, 255)
            elif glow: o[x, y] = (255, 63, 192, 255)
            elif any(0 <= x + a < w and 0 <= y + b < h and src[x + a, y + b][3] and abs(lum(src[x + a, y + b]) - lum(c)) > 60 for a, b in ((1, 0), (0, 1))):
                o[x, y] = (44, 58, 154, 255)
            elif (x + y) % 4 == 0: o[x, y] = (170, 182, 225, 255)
    return out


def save(name, fw, fh, frames, tags, ms=90):
    if BUILD:
        asebuild.build(name, fw, fh, ["art"], [{"ms": ms, "cels": {"art": f}} for f in frames], tags)


def main():
    parts = {
        "saint0_socket": (80, 80, [socket()], [("idle", 0, 0)]),
        "saint0_iris": (48, 48, [iris(f) for f in range(8)], [("spin", 0, 7)]),
        "saint0_lid": (80, 80, [lid(k / 6) for k in range(7)] + [lid(1.0, b / 5, b) for b in range(1, 7)], [("aperture", 0, 6), ("death", 7, 12)]),
        "saint0_lens": (14, 10, [lens(s) for s in ("open", "half", "shut", "half", "fire", "fire2")], [("open", 0, 0), ("blink", 1, 3), ("fire", 4, 5)]),
    }
    prev = Image.new("RGBA", (13 * 84, 4 * 84 * 2), (40, 40, 52, 255))
    row = 0
    for name, (fw, fh, frames, tags) in parts.items():
        save(name, fw, fh, frames, tags)
        wires = [wire_frame(f) for f in frames]
        save(name + "_wire", fw, fh, wires, tags)
        for i, f in enumerate(frames):
            prev.alpha_composite(f, (i * 84, row * 84))
            pw = Image.new("RGBA", f.size, (220, 228, 238, 255)); pw.alpha_composite(wires[i]); prev.alpha_composite(pw, (i * 84, (row + 4) * 84))
        row += 1
    # a composite of the whole eye at a few apertures
    for i, k in enumerate((0, 2, 4, 6)):
        c = Image.new("RGBA", (80, 80), T)
        c.alpha_composite(parts["saint0_socket"][2][0]); c.alpha_composite(parts["saint0_iris"][2][i * 2], (16 + i, 16)); c.alpha_composite(parts["saint0_lid"][2][k])
        prev.alpha_composite(c, (700 + (i % 2) * 84 - 84 * 2 + 84 * 2, 84 * 2 + (i // 2) * 84 + 336))
    os.makedirs(os.path.join(ART, "previews"), exist_ok=True)
    prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).save(os.path.join(ART, "previews", "saint0_parts.png"))


if __name__ == "__main__":
    main()
