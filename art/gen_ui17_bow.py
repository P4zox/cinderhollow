#!/usr/bin/env python3
"""UI icon v17 for the Bow's art, Ashen Volley -> art/ui_icons17_bow.aseprite + assets/ui_icons17_bow.png/.json

16x16, one tag (a_ashen_volley), layers Outline + Icon like gen_ui*.py: the back-flip's arc in pale ash over the top-left,
and three arrows loosed out of it down and forward, their heads burning (ember to gold), a last fleck of fire behind each.
The game finds the sheet through ICON_SHEETS (web/src/81_art_bow.js pushes 'ui_icons17_bow').
Re-runnable: python3 art/gen_ui17_bow.py [--preview-only]   (preview -> art/previews/ui17_bow.png)
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402

S = 16
OUTLINE = (8, 7, 12)
ASH_LIT, ASH, ASH_DK = (214, 206, 192), (150, 140, 130), (96, 88, 84)
SHAFT, SHAFT_DK = (186, 160, 118), (128, 104, 74)
FLETCH = (176, 56, 46)
HEAD_HOT, HEAD, HEAD_DK = (255, 236, 170), (255, 164, 70), (196, 84, 40)
FIRE = (238, 110, 44)


def a_ashen_volley():
    px = {}

    def put(x, y, c):
        if 0 <= x < S and 0 <= y < S:
            px[(x, y)] = c
    # the flip's arc: a thin sweep of ash up the left side, from the floor to the top of the turn (lit on the outside)
    cx, cy, r = 6.5, 8.5, 6.0
    for k in range(0, 50):
        d = 100 + k * 3.2                   # from below-left round the left to the top
        a = math.radians(d)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        put(int(round(x)), int(round(y)), ASH_LIT if 160 < d < 240 else (ASH if d < 250 else ASH_DK))
    # three arrows loosed from the top of the turn, fanned down and forward
    ox, oy = 5.6, 2.8
    for ang, L in ((16, 10.6), (44, 11.4), (72, 10.6)):
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        sx, sy = ox + c * 1.6, oy + s * 1.6
        pts = []
        for i in range(int(L * 2) + 1):
            t = i / 2.0
            p = (int(round(sx + c * t)), int(round(sy + s * t)))
            if not pts or pts[-1] != p:
                pts.append(p)
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            if i < 1:
                put(x, y, FLETCH)
            elif i >= n - 2:
                put(x, y, HEAD_HOT if i == n - 1 else HEAD)
            elif i >= n - 4:
                put(x, y, FIRE if i == n - 3 else SHAFT)
            else:
                put(x, y, SHAFT if i % 3 else SHAFT_DK)
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for (x, y), col in px.items():
        body.putpixel((x, y), col + (255,))
    for y in range(S):
        for x in range(S):
            if (x, y) not in px and any((x + a2, y + b2) in px for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE + (255,))
    return body, out


ICONS = [("a_ashen_volley", a_ashen_volley)]


def main():
    frames, tags, comps = [], [], []
    for i, (name, fn) in enumerate(ICONS):
        body, out = fn()
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        tags.append((name, i, i))
        c = out.copy()
        c.alpha_composite(body)
        comps.append(c)
    if "--preview-only" not in sys.argv:
        asebuild.build("ui_icons17_bow", S, S, ["Outline", "Icon"], frames, tags)
    Z = 10
    sheet = Image.new("RGBA", (len(comps) * (S + 4) * Z, (S + 4) * Z), (40, 36, 46, 255))
    for i, c in enumerate(comps):
        sheet.alpha_composite(c.resize((S * Z, S * Z), Image.NEAREST), ((i * (S + 4) + 2) * Z, 2 * Z))
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    sheet.save(os.path.join(HERE, "previews", "ui17_bow.png"))
    print("ui_icons17_bow:", len(frames), "icons")


if __name__ == "__main__":
    main()
