#!/usr/bin/env python3
"""UI icon v17 (the Warbell's weapon art) -> art/ui_icons17_bell.aseprite + assets/ui_icons17_bell.png/.json

16x16, ONE tag (a_funeral_peal), layers Outline + Icon like gen_ui*.py: one strong silhouette lit from the upper-left, the house
1px near-black outline on its own layer. The Dirgebell (black iron, worn-gold lip and sound-bow band, the colours of
art/player_v17_bell.py / player_v15_bell.py) driven mouth-down into a floor line, its haft slanting up-right, and the peal rolling
away both ways as two standing rings -- the forward one cored Ember, the back one cored Ash (the notes it rings).
The game finds the sheet through ICON_SHEETS (web/src/81_art_bell.js pushes 'ui_icons17_bell').
Re-runnable: python3 art/gen_ui17_bell.py [--preview-only]   (preview -> art/previews/ui17_bell.png)
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402

S = 16
OUTLINE = (8, 7, 12)
IRON = ((150, 146, 162), (108, 104, 120), (70, 66, 82), (40, 36, 48))
GOLD = ((246, 218, 140), (196, 150, 72), (120, 82, 36))
BONE = (236, 230, 218)
EMBER = (224, 56, 62)
ASH = (196, 190, 178)
FLOOR = (84, 70, 62)
HAFT = ((92, 64, 44), (56, 38, 28))


def a_funeral_peal():
    pix = {}

    def put(x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < S and 0 <= y < S:
            pix[(x, y)] = c

    # the haft: from the crown up and to the right, chain-wound near the head
    for i in range(7):
        x, y = 9 + i * 0.8, 5 - i * 0.8
        put(x, y, HAFT[0] if i % 2 else IRON[1])
    put(14.6, 0.2, IRON[0])
    # the bell, mouth down: domed crown at y 4, a straight waist, the lip flaring to 9 px at y 11
    cx = 7.5
    for y in range(4, 12):
        t = (y - 4) / 7.0
        hw = 1.5 + 0.8 * t + (1.5 * (t - 0.6) / 0.4 if t > 0.6 else 0)
        for x in range(S):
            dx = x + 0.5 - (cx + 0.5)
            if abs(dx) > hw:
                continue
            q = dx / max(1.0, hw)
            if y == 11:
                c = GOLD[0] if q < -0.2 else (GOLD[1] if q < 0.5 else GOLD[2])     # the worn lip
            elif y == 9:
                c = GOLD[1] if q < 0.2 else GOLD[2]                                # the sound-bow band
            elif q < -0.45:
                c = IRON[0]
            elif q < 0.05:
                c = IRON[1]
            elif q < 0.55:
                c = IRON[2]
            else:
                c = IRON[3]
            put(x, y, c)
    put(7, 3, GOLD[1]); put(8, 3, GOLD[2])          # the crown loop
    put(6, 6, (220, 110, 50))                        # an ember glint in a rune cut
    # the floor line it bit into, cracked under the lip
    for x in range(S):
        put(x, 13, FLOOR)
    put(7, 12, GOLD[0]); put(8, 12, GOLD[1])        # the light at the lip
    # the peal: two standing rings rolling away along the floor (arcs rising off the floor from the lip, outward-bowed),
    # the outer one cored in its note's colour, a fainter inner echo
    for side, core in ((1, EMBER), (-1, ASH)):
        for e, (r, a1) in enumerate(((6.8, 62),)):
            n = 16
            for i in range(n + 1):
                a = math.radians(a1 * i / n)
                x = 8.0 + side * math.cos(a) * r - (0.5 if side > 0 else 0)
                y = 12.6 - math.sin(a) * r * 1.05
                if e and i % 2:
                    continue
                put(x, y, (core if i < n * 0.3 else BONE) if e == 0 else (GOLD[1] if i < n * 0.5 else GOLD[2]))
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for (x, y), c in pix.items():
        body.putpixel((x, y), tuple(c) + (255,))
    for y in range(S):
        for x in range(S):
            if (x, y) not in pix and any((x + a, y + b) in pix for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE + (255,))
    return body, out


ICONS = [("a_funeral_peal", a_funeral_peal)]


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
        asebuild.build("ui_icons17_bell", S, S, ["Outline", "Icon"], frames, tags)
    Z = 10
    sheet = Image.new("RGBA", ((S + 4) * Z * 2, (S + 4) * Z), (40, 36, 46, 255))
    for i, c in enumerate(comps):
        sheet.alpha_composite(c.resize((S * Z, S * Z), Image.NEAREST), (2 * Z, 2 * Z))
        # beside it at the size the UI draws it (9-10 px cells), on the panel colour
        small = Image.new("RGBA", (S, S), (28, 24, 34, 255)); small.alpha_composite(c)
        sheet.alpha_composite(small.resize((S * 3, S * 3), Image.NEAREST), ((S + 6) * Z, 2 * Z))
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    sheet.save(os.path.join(HERE, "previews", "ui17_bell.png"))
    print("ui_icons17_bell:", len(frames), "icons")


if __name__ == "__main__":
    main()
