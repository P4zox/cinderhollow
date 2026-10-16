#!/usr/bin/env python3
"""UI icon v17 for the Martial Arts' weapon art, Litany of Fists -> art/ui_icons17_fist.aseprite + assets/ui_icons17_fist.png/.json

16x16, ONE tag (a_litany), layers Outline + Icon like gen_ui*.py: one strong silhouette lit from the upper-left, the house
1px near-black outline on its own layer. The icon: an upright wrapped hand, palm out (the prayer half of the litany), an
iron band over the knuckles; pale Swift blow-lines stream off the fingers to the left, an ember Iron shock opens on the
right -- the art's two faces. The game finds the sheet through ICON_SHEETS (web/src/81_art_fist.js pushes it).
Re-runnable: python3 art/gen_ui17_fist.py [--preview-only]   (preview -> art/previews/ui17_fist.png)
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402

S = 16
OUTLINE = (8, 7, 12)
PAL = {
    'W': (218, 204, 176), 'w': (160, 142, 114), 'd': (96, 80, 64),        # the wrappings
    'I': (196, 200, 214), 'i': (120, 122, 140), 'j': (64, 64, 80),           # the iron knuckle band
    'B': (226, 240, 255), 'b': (150, 196, 240), 'c': (86, 118, 170),         # Swift: pale steel-blue
    'E': (255, 226, 160), 'e': (255, 150, 70), 'r': (168, 66, 30),          # Iron: ember
}
A_LITANY = [
    "................",
    "......W.W.......",
    ".....WdWdW......",
    ".....WdWdW....e.",
    ".BBb.WdWdW.....e",
    ".....WdWdW..r..e",
    "....jIIIIi..r..E",
    "BBbc.jiiij..E..e",
    "...wWWWWwd..r..e",
    "...wWWWWwd..r.e.",
    "....wWWWwd....e.",
    ".....wWWd.......",
    ".....dwdw.......",
    ".....wdwd.......",
    ".....dddd.......",
    "................",
]


def icon(rows):
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pix = {(x, y): PAL[c] for y, r in enumerate(rows) for x, c in enumerate(r) if c in PAL}
    for (x, y), c in pix.items():
        body.putpixel((x, y), c + (255,))
    for y in range(S):
        for x in range(S):
            if (x, y) not in pix and any((x + a, y + b) in pix for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE + (255,))
    return body, out


ICONS = [("a_litany", A_LITANY)]


def main():
    frames, tags, comps = [], [], []
    for i, (name, rows) in enumerate(ICONS):
        body, out = icon(rows)
        frames.append({"ms": 100, "cels": {"Outline": out, "Icon": body}})
        tags.append((name, i, i))
        c = out.copy()
        c.alpha_composite(body)
        comps.append(c)
    if "--preview-only" not in sys.argv:
        asebuild.build("ui_icons17_fist", S, S, ["Outline", "Icon"], frames, tags)
    Z = 10
    sheet = Image.new("RGBA", (len(comps) * (S + 4) * Z, (S + 4) * Z), (40, 36, 46, 255))
    for i, c in enumerate(comps):
        sheet.alpha_composite(c.resize((S * Z, S * Z), Image.NEAREST), ((i * (S + 4) + 2) * Z, 2 * Z))
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    sheet.save(os.path.join(HERE, "previews", "ui17_fist.png"))
    print("ui_icons17_fist:", len(frames), "icons")


if __name__ == "__main__":
    main()
