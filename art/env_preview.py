"""Preview + mock-room renderers for the environment art (writes art/previews/*)."""
import os, random
from PIL import Image, ImageDraw
from envlib import scale, blank, h01

ART = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(ART, "previews")
os.makedirs(PREV, exist_ok=True)
GREY = (70, 70, 76, 255)


def tileset_sheet(biome, tiles, k=4):
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    cw, ch = 16 * k + 8, 16 * k + 18
    sheet = Image.new("RGBA", (cols * cw + 8, rows * ch + 8), GREY)
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(tiles):
        x, y = 8 + (i % cols) * cw, 8 + (i // cols) * ch
        # checker behind so transparency is visible
        bgc = Image.new("RGBA", (16 * k, 16 * k), (40, 40, 46, 255))
        bd = ImageDraw.Draw(bgc)
        for yy in range(0, 16 * k, 8):
            for xx in range(0, 16 * k, 8):
                if (xx // 8 + yy // 8) % 2:
                    bd.rectangle([xx, yy, xx + 7, yy + 7], fill=(52, 52, 60, 255))
        bgc.alpha_composite(scale(t, k))
        sheet.paste(bgc, (x, y))
        d.text((x, y + 16 * k + 2), str(i), fill=(230, 230, 230, 255))
    sheet.save(os.path.join(PREV, f"tiles_{biome}.png"))
    return sheet


def seam_test(biome, tiles, k=4):
    """Random solid blob using every mask + variants, drawn on grey: checks seams at 4x."""
    rnd = random.Random(3)
    Wt, Ht = 14, 9
    g = [[False] * Wt for _ in range(Ht)]
    for y in range(1, Ht - 1):
        for x in range(1, Wt - 1):
            g[y][x] = rnd.random() < 0.72
    img = Image.new("RGBA", (Wt * 16, Ht * 16), (46, 44, 56, 255))
    for y in range(Ht):
        for x in range(Wt):
            if not g[y][x]:
                continue
            m = 0
            if not (y > 0 and g[y - 1][x]): m |= 1
            if not (x < Wt - 1 and g[y][x + 1]): m |= 2
            if not (y < Ht - 1 and g[y + 1][x]): m |= 4
            if not (x > 0 and g[y][x - 1]): m |= 8
            idx = m + (16 if h01(x, y, 1) < 0.3 else 0)
            img.alpha_composite(tiles[idx], (x * 16, y * 16))
    scale(img, k).save(os.path.join(PREV, f"seams_{biome}.png"))


# --------------------------------------------------------------------------- mock room
ROOM_BG = [   # background wall region (b = bg wall, p = pilaster column)
    "........................",
    "........................",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "...............pbbbbbp..",
    "........................",
    "........................",
    "........................",
    "........................",
]
ROOM_FG = [
    "...............#########",
    "...............#########",
    "...............C.vv...##",
    "#..............C......##",
    "#.....................##",
    "##........====........##",
    "##....................##",
    "##....................##",
    "###.............=.....##",
    "###t...............c.o##",
    "#########...############",
    "#########^^^############",
    "########################",
    "########################",
]
SHRINE_AT = (4, 10)     # tile col, row whose top edge is the floor the shrine stands on
LANTERN_AT = (19, 2)    # tile col, row whose top edge the lantern hangs from
BREAKABLE = [(22, 5)]


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] == "#" or fg[y][x] == "X"


def render_room(biome, tiles, far=None, mid=None, props=None, camx=0):
    W, H = 384, 216
    img = Image.new("RGBA", (W, H), (20, 20, 26, 255))
    if far is not None:
        ox = -int(camx * 0.15) % 512
        img.alpha_composite(far, (ox - 512, 0))
        img.alpha_composite(far, (ox, 0))
    if mid is not None:
        ox = -int(camx * 0.4) % 512
        img.alpha_composite(mid, (ox - 512, 0))
        img.alpha_composite(mid, (ox, 0))
    fg = [r.ljust(24, "#") for r in ROOM_FG]
    for y, row in enumerate(ROOM_BG):
        for x, ch in enumerate(row):
            if ch in "bp":
                r = h01(x, y, 9)
                k = 41 if ch == "p" else (38 if r < 0.62 else (39 if r < 0.85 else 40))
                img.alpha_composite(tiles[k], (x * 16, y * 16))
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch in "#X":
                m = 0
                if not solid_at(fg, x, y - 1): m |= 1
                if not solid_at(fg, x + 1, y): m |= 2
                if not solid_at(fg, x, y + 1): m |= 4
                if not solid_at(fg, x - 1, y): m |= 8
                idx = m + (16 if h01(x, y, 5) < 0.3 else 0)
                if (x, y) in BREAKABLE:
                    idx = 46
                img.alpha_composite(tiles[idx], (x * 16, y * 16))
            elif ch == "=":
                l = x > 0 and row[x - 1] == "="
                r = x < len(row) - 1 and row[x + 1] == "="
                idx = 33 if (l and r) else (32 if r else (34 if l else 35))
                img.alpha_composite(tiles[idx], (x * 16, y * 16))
            elif ch == "^":
                img.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                img.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "CRcot":
                idx = {"C": 42, "R": 43, "c": 44, "o": 45, "t": 47}[ch]
                img.alpha_composite(tiles[idx], (x * 16, y * 16))
    if props:
        for (pimg, px_, py_) in props:
            img.alpha_composite(pimg, (int(px_), int(py_)))
    return img


def save_room(biome, img, k=3):
    scale(img, k).save(os.path.join(PREV, f"room_{biome}.png"))


def flatten(w, h, layers, frame):
    img = blank(w, h)
    for L in layers:
        c = frame["cels"].get(L)
        if c is not None:
            img.alpha_composite(c)
    return img


def props_sheet(props, k=4):
    """props: list of (name, (w, h, layers, frames, tags)); one row per tag, mid-grey bg."""
    rows = []
    for name, (w, h, layers, frames, tags) in props:
        for (t, a, b) in tags:
            rows.append((name, t, w, h, [flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    rw = max(len(r[4]) * (r[2] * k + 6) for r in rows) + 170
    rh = sum(r[3] * k + 8 for r in rows) + 8
    sheet = Image.new("RGBA", (rw, rh), GREY)
    d = ImageDraw.Draw(sheet)
    y = 8
    for (name, t, w, h, ims) in rows:
        d.text((6, y + 2), f"{name}", fill=(235, 235, 235, 255))
        d.text((6, y + 14), f"  {t} ({len(ims)})", fill=(200, 200, 160, 255))
        x = 170
        for im in ims:
            sheet.alpha_composite(scale(im, k), (x, y))
            x += w * k + 6
        y += h * k + 8
    sheet.save(os.path.join(PREV, "props.png"))
    return sheet
