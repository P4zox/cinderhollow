#!/usr/bin/env python3
"""Environment art for the `barrows` biome -- THE DROWNED BARROWS (tombs beneath the Sunken Cathedral, black tide).

Builds (art/<name>.aseprite + assets/<name>.png/.json via asebuild):
  tiles_barrows    48 frames 16x16, tag `all`, standard index layout (ART_SPEC section 6)    (barrows_env_tiles.py)
  bg_barrows_far   512x216 opaque, tileable, tag `loop` (4 frames: caustics + silt motes)      (barrows_env_bg.py)
  bg_barrows_mid   512x216 transparent, tileable, tag `loop` (1 frame)                         (barrows_env_bg.py)
  db_bell db_boat db_lamp db_grate db_bones db_window db_statue                               (barrows_env_props.py)
Previews -> art/previews/: env_barrows.png (tiles + parallax + props, labelled), room_barrows.png (384x216 mock room
at 3x with water), db_props.png (every prop tag as a row, 4x).

Usage: python3 art/gen_barrows_env.py [--no-ase]
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                             # noqa: E402
import barrows_env_tiles as bt                              # noqa: E402
import barrows_env_bg as bb                                 # noqa: E402
import barrows_env_props as bp                              # noqa: E402
from envlib import scale, blank, h01                        # noqa: E402

BIOME = "barrows"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = os.path.join(HERE, "previews")
GREY = (70, 70, 76, 255)
os.makedirs(PREV, exist_ok=True)

# mock room: # solid, = one-way platform, g = platform with the drain grate over it, ^ floor spikes, v ceiling
# spikes, x chain, r kelp, k candles, b bone pile (tile decos), ~ water (not solid), X breakable wall
ROOM = [
    "########################",
    "####vvv######....#######",
    "#..x..........r......x##",
    "#..x..........r........#",
    "#......................#",
    "#...==g=........===....#",
    "#......................#",
    "#......................#",
    "##....................##",
    "##k..^^.............b.X#",
    "#######~~~~~~~~~~~######",
    "#######~~~~~~~~~~~######",
    "#######~~~~~~~~~~~######",
    "########################",
]
WATER_Y = 10 * 16 + 5          # water surface in the pool


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X"


def flatten(w, h, layers, frame):
    img = blank(w, h)
    for L in layers:
        c = frame["cels"].get(L)
        if c is not None:
            img.alpha_composite(c)
    return img


def pframe(props, name, tag, k=0):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return flatten(w, h, layers, frames[a + k])


def render_room(tiles, far, mid, props, fframe=0):
    fg = ROOM
    img = Image.new("RGBA", (384, 216), (6, 12, 14, 255))
    img.alpha_composite(far[fframe], (0, 0))
    img.alpha_composite(mid.crop((40, 0, 424, 216)), (0, 0))
    # indoor back wall fading toward open space (same rule as the engine)
    for y in range(len(fg)):
        for x in range(len(fg[0])):
            if solid_at(fg, x, y):
                continue
            d = 9
            for yy in range(-3, 4):
                for xx in range(-3, 4):
                    if solid_at(fg, x + xx, y + yy):
                        d = min(d, max(abs(xx), abs(yy)))
            a = 1 if d <= 1 else 0.8 if d == 2 else 0.5 if d == 3 else 0.28
            t = tiles[38 + int(h01(x, y) * 4)].copy()
            t.putalpha(t.getchannel("A").point(lambda v: int(v * a)))
            img.alpha_composite(t, (x * 16, y * 16))
    # background decor: the chapel window on the back wall
    img.alpha_composite(pframe(props, "db_window", "idle"), (262, 34))
    front = blank(384, 216)
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch in "#X":
                m = (1 if not solid_at(fg, x, y - 1) else 0) | (2 if not solid_at(fg, x + 1, y) else 0) | \
                    (4 if not solid_at(fg, x, y + 1) else 0) | (8 if not solid_at(fg, x - 1, y) else 0)
                idx = 46 if ch == "X" else m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)
                front.alpha_composite(tiles[idx], (x * 16, y * 16))
                if ch == "#" and m & 1 and h01(x * 5, y, 1) < 0.3:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch in "=g":
                l, r = row[x - 1] in "=g", row[x + 1] in "=g"
                front.alpha_composite(tiles[33 if (l and r) else 32 if r else 34 if l else 35], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "xrkb":
                img.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
    # the drain grate: two 16px platform cells wide, drawn over the platform at 'g'
    for y, row in enumerate(fg):
        x = row.find("g")
        if x >= 0:
            front.alpha_composite(pframe(props, "db_grate", "idle"), (x * 16 - 8, y * 16))
    # props
    img.alpha_composite(pframe(props, "db_bell", "ring", 1), (15 * 16 + 8 - 16, 2 * 16))   # hangs from the ceiling
    img.alpha_composite(pframe(props, "db_statue", "idle"), (17 * 16, 10 * 16 - 64))
    img.alpha_composite(pframe(props, "db_lamp", "loop", 0), (3 * 16 + 4, 10 * 16 - 40))
    img.alpha_composite(pframe(props, "db_bones", "loop", 2), (19 * 16 - 20, 10 * 16 - 24))
    pl = os.path.join(ASSETS, "player.png")
    if os.path.exists(pl):
        p = Image.open(pl).convert("RGBA").crop((0, 0, 64, 40))
        img.alpha_composite(p, (10 * 16 - 28, WATER_Y - 12 - 40))                          # on the boat's deck
        wp = os.path.join(ASSETS, "wpn_longsword.png")
        if os.path.exists(wp):
            img.alpha_composite(Image.open(wp).convert("RGBA").crop((0, 0, 64, 40)), (10 * 16 - 28, WATER_Y - 12 - 40))
    img.alpha_composite(front)
    boat = pframe(props, "db_boat", "rock", 1)
    img.alpha_composite(boat, (7 * 16 + 20, WATER_Y - 24))
    # dark translucent teal water in the pool, drawn over the boat's lower hull
    water = Image.new("RGBA", (384, 216), (0, 0, 0, 0))
    wp_ = water.load()
    for y in range(WATER_Y, 216):
        for x in range(7 * 16, 18 * 16):
            if y == WATER_Y:
                wp_[x, y] = (70, 130, 124, 200) if h01(x // 3, 0, 4) < 0.55 else (40, 90, 88, 190)
            else:
                wp_[x, y] = (6, 26, 30, 170 + min(60, (y - WATER_Y) * 3))
            if y == WATER_Y + 3 and h01(x // 2, 5, 9) < 0.12:
                wp_[x, y] = (47, 150, 140, 200)
    img.alpha_composite(water)
    return img


def label(d, xy, s, col=(235, 235, 235, 255)):
    d.text(xy, s, fill=col)


def env_sheet(tiles, far, mid, props):
    """Tiles enlarged + parallax far/mid/composite + props, all labelled."""
    k = 4
    cols = 12
    cw, chh = 16 * k + 6, 16 * k + 16
    trows = (48 + cols - 1) // cols
    Wd = 1060
    rows_h = 22 + trows * chh + 22 + 216 + 22 + 216 + 22 + 220
    out = Image.new("RGBA", (Wd, rows_h), GREY)
    d = ImageDraw.Draw(out)
    y = 4
    label(d, (6, y), "tiles_barrows (48 x 16x16, tag all) @4x")
    y += 18
    for i, t in enumerate(tiles):
        x0, y0 = 6 + (i % cols) * cw, y + (i // cols) * chh
        bgc = Image.new("RGBA", (16 * k, 16 * k), (26, 30, 34, 255))
        bgc.alpha_composite(scale(t, k))
        out.paste(bgc, (x0, y0))
        label(d, (x0, y0 + 16 * k + 1), str(i), (210, 210, 210, 255))
    y += trows * chh + 4
    label(d, (6, y), "bg_barrows_far (512x216 opaque, loop x4)")
    label(d, (530, y), "bg_barrows_mid (512x216, over magenta)")
    y += 18
    out.alpha_composite(far[0], (6, y))
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255))
    m.alpha_composite(mid)
    out.alpha_composite(m, (530, y))
    y += 216 + 4
    label(d, (6, y), "far + mid composite, tiled twice (wrap seam at the centre)")
    y += 18
    c = far[0].copy()
    c.alpha_composite(mid)
    out.alpha_composite(c.crop((256, 0, 512, 216)), (6, y))
    out.alpha_composite(c, (6 + 256, y))
    out.alpha_composite(c.crop((0, 0, 1060 - 6 - 768, 216)), (6 + 768, y))
    y += 216 + 4
    label(d, (6, y), "props (1x-native shown at 2x on the far layer)")
    y += 18
    strip = far[0].crop((0, 0, 512, 100)).copy()
    x = 4
    for name in ("db_bell", "db_lamp", "db_statue", "db_window", "db_bones", "db_grate", "db_boat"):
        tag = props[name][4][0][0]
        im = pframe(props, name, tag)
        if x + im.size[0] > 512:
            break
        strip.alpha_composite(im, (x, 96 - im.size[1]))
        x += im.size[0] + 4
    out.alpha_composite(scale(strip, 2), (6, y))
    out.save(os.path.join(PREV, f"env_{BIOME}.png"))


def props_sheet(props, k=4):
    rows = []
    for name, (w, h, layers, frames, tags) in props.items():
        for (t, a, b) in tags:
            rows.append((name, t, w, h, [flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    rw = max(len(r[4]) * (r[2] * k + 6) for r in rows) + 170
    rh = sum(r[3] * k + 8 for r in rows) + 8
    sheet = Image.new("RGBA", (rw, rh), GREY)
    d = ImageDraw.Draw(sheet)
    y = 8
    for (name, t, w, h, ims) in rows:
        label(d, (6, y + 2), f"{name} {w}x{h}")
        label(d, (6, y + 14), f"  {t} ({len(ims)})", (200, 200, 160, 255))
        x = 170
        for im in ims:
            sheet.alpha_composite(scale(im, k), (x, y))
            if name == "db_boat":
                dd = ImageDraw.Draw(sheet)
                dd.line([(x + 12 * k, y + 12 * k), (x + 100 * k - 1, y + 12 * k)], fill=(255, 80, 80, 120))
                dd.line([(x, y + 24 * k), (x + w * k, y + 24 * k)], fill=(80, 160, 255, 120))
            x += w * k + 6
        y += h * k + 8
    sheet.save(os.path.join(PREV, "db_props.png"))


def verify(name, n_frames, tags, size):
    with open(os.path.join(ASSETS, f"{name}.json")) as fh:
        d = json.load(fh)
    got = [(t["name"], t["from"], t["to"]) for t in d["meta"]["frameTags"]]
    assert len(d["frames"]) == n_frames, (name, len(d["frames"]), n_frames)
    assert got == [tuple(t) for t in tags], (name, got, tags)
    fr = d["frames"][0]["sourceSize"]
    assert (fr["w"], fr["h"]) == size, (name, fr, size)
    return name, size, got


def check_clean(name, img, glow_ok=False):
    al = set(img.getdata(3))
    if not glow_ok:
        assert al <= {0, 255}, f"{name} not pixel-clean: {sorted(al)[:8]}"


def main():
    ase = "--no-ase" not in sys.argv
    tiles = bt.build_tileset()
    for i, t in enumerate(tiles):
        check_clean(f"tile {i}", t)
    far = bb.build_far()
    mid = bb.build_mid()
    for f in far:
        assert f.getextrema()[3][0] == 255, "far layer must be opaque"
    check_clean("bg_barrows_mid", mid)
    props = {n: f() for n, f in bp.PROPS.items()}
    for name, (w, h, layers, frames, tags) in props.items():
        for fr in frames:
            for im in fr["cels"].values():
                assert im.size == (w, h)
                check_clean(name, im, glow_ok=name in ("db_bell", "db_bones"))
    # boat contract: deck top row y=12 across x=12..99 in every frame, nothing opaque directly above it there
    w, h, layers, frames, tags = props["db_boat"]
    for fr in frames:
        im = flatten(w, h, layers, fr)
        px = im.load()
        for x in range(12, 100):
            assert px[x, 12][3] == 255, ("boat deck gap", x)
    env_sheet(tiles, far, mid, props)
    props_sheet(props)
    img = render_room(tiles, far, mid, props)
    scale(img, 3).save(os.path.join(PREV, f"room_{BIOME}.png"))
    if ase:
        report = []
        asebuild.build(f"tiles_{BIOME}", 16, 16, ["Tiles"], [{"ms": 100, "cels": {"Tiles": t}} for t in tiles],
                       [("all", 0, 47)])
        asebuild.build(f"bg_{BIOME}_far", 512, 216, ["Layer"], [{"ms": 170, "cels": {"Layer": f}} for f in far],
                       [("loop", 0, len(far) - 1)])
        asebuild.build(f"bg_{BIOME}_mid", 512, 216, ["Layer"], [{"ms": 1000, "cels": {"Layer": mid}}],
                       [("loop", 0, 0)])
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
        report.append(verify(f"bg_{BIOME}_far", len(far), [("loop", 0, len(far) - 1)], (512, 216)))
        report.append(verify(f"bg_{BIOME}_mid", 1, [("loop", 0, 0)], (512, 216)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
    print("built", BIOME)


if __name__ == "__main__":
    main()
