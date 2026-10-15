#!/usr/bin/env python3
"""UI icons v15 (the five new weapon types) -> art/ui_icons15.aseprite + assets/ui_icons15.png/.json

16x16 frames, ONE tag per icon (w_<weaponId>), layers Outline + Icon like gen_ui*.py. Each icon is the in-game weapon
itself (art/player_v15_weapons.py's shape, the same blade-space function the wpn_* overlay uses) rasterised on the
icon diagonal at its own zoom, lit from the upper-left, with the house 1px near-black outline.
The game finds the sheet through ICON_SHEETS (web/src/77_types15.js pushes 'ui_icons15').
Re-runnable: python3 art/gen_ui15.py [--preview-only]   (preview -> art/previews/ui15.png)
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import gen_player as G  # noqa: E402  (installs the v15 weapons into G.WPN)
import player_v15_weapons as V  # noqa: E402

S = 16
OUTLINE = (8, 7, 12)
# weapon id -> (grip x, grip y, angle deg, length L, zoom, haft back)
LAYOUT = {
    "gravegrinder":      (3.8, 12.2, -45, 13.0, 0.9, 5.0),
    "ashstring":         (6.6, 9.4, -45, 10.5, 0.80, 0),
    "penitent_knuckles": (6.4, 9.6, -45, 4.0, 1.75, 0),
    "requiem_scythe":    (4.4, 11.6, -45, 15.0, 0.72, 5.0),
    "dirge_bell":        (3.6, 12.4, -45, 11.0, 1.02, 0),
}


def icon(kind):
    shape = G.WPN[kind][0]
    hx, hy, ang, L, k, back = LAYOUT[kind]
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    lit = 1 if (-0.5 * px - py) > 0 else -1
    pix = {}
    for y in range(S):
        for x in range(S):
            u = ((x - hx) * dx + (y - hy) * dy) / k
            v = ((x - hx) * px + (y - hy) * py) / k
            c = shape(u, v, lit, L, back) if kind in G.STAFF_BACK else shape(u, v, lit, L)
            if c is not None:
                pix[(x, y)] = G.PAL[c] if isinstance(c, str) else c
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for (x, y), c in pix.items():
        body.putpixel((x, y), tuple(c) + (255,))
    for y in range(S):
        for x in range(S):
            if (x, y) not in pix and any((x + a2, y + b2) in pix for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE + (255,))
    return body, out


ICONS = ["w_" + V.V15_WPN[t] for t in V.V15_TYPES]


def main():
    frames, tags, comps = [], [], []
    for i, name in enumerate(ICONS):
        body, out = icon(name[2:])
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        tags.append((name, i, i))
        c = out.copy()
        c.alpha_composite(body)
        comps.append(c)
    if "--preview-only" not in sys.argv:
        asebuild.build("ui_icons15", S, S, ["Outline", "Icon"], frames, tags)
    Z = 8
    sheet = Image.new("RGBA", (len(comps) * (S + 4) * Z, (S + 4) * Z), (40, 36, 46, 255))
    for i, c in enumerate(comps):
        sheet.alpha_composite(c.resize((S * Z, S * Z), Image.NEAREST), ((i * (S + 4) + 2) * Z, 2 * Z))
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    sheet.save(os.path.join(HERE, "previews", "ui15.png"))
    print("ui_icons15:", len(frames), "icons")


if __name__ == "__main__":
    main()
