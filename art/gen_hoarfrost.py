#!/usr/bin/env python3
"""Environment art for the `hoarfrost` biome — THE HOARFROST AQUEDUCT (docs/ART_SPEC.md section 6 contract).

Builds:
  tiles_hoarfrost     66 frames of 16x16, tags `all` 0..47 (standard layout) + `extra` 48..65
                      (48-63 ice-floor terrain by AIR mask, 64 water surface, 65 water body)  (hoarfrost_tiles.py)
  bg_hoarfrost_far    512x216 opaque, tileable, tag `loop`                                     (hoarfrost_bg.py)
  bg_hoarfrost_mid    512x216 transparent, tileable, tag `loop`                                (hoarfrost_bg.py)
  hf_icicle  (16x32: idle 1, shake 2, fall 1, shatter 5 — pivot TOP-centre; shatter drawn low, bottom row = floor)
  hf_icefall (32x48: top 1, mid 4, bottom 1 — stack vertically, bottom row of `bottom` = floor)
                                                                                               (hoarfrost_props.py)
Previews -> art/previews/: tiles_hoarfrost.png, seams_hoarfrost.png, env_hoarfrost.png,
room_hoarfrost.png (384x216 mock room at 3x, player + longsword for scale), props_hoarfrost.png.

Usage: python3 art/gen_hoarfrost.py [--no-ase]   (--no-ase: previews only, skip Aseprite export)
"""
import os, sys, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                          # noqa: E402
import env_preview                                       # noqa: E402
import hoarfrost_tiles, hoarfrost_bg, hoarfrost_props    # noqa: E402
from envlib import scale, blank, h01                     # noqa: E402
from gen_env import build_bg, verify                     # noqa: E402  (read-only reuse)

BIOME = "hoarfrost"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV
N_TILES = 66
TILE_TAGS = [("all", 0, 47), ("extra", 48, 65)]
ICE0, WSURF, WBODY = 48, 64, 65
WATER_ALPHA = 0.7

# --------------------------------------------------------------------------- mock room
# '#' solid  'I' ice-floor solid  'X' breakable  '=' one-way  '^' floor spikes  'v' ceiling spikes
# '~' water surface  'w' water body  'C' chain(42)  'r' icicle curtain(43)  'k' candles(44)
# 'o' frozen rubble(45)  't' snowdrift tuft(47)
ROOM = dict(
    fg=[
        "#########.......########",
        "#rr######.......#..vv###",
        "#..C..................C#",
        "#..C....................",
        "#.......................",
        "#..====.............====",
        "#......................#",
        "##..........=..........#",
        "###....................#",
        "###k.o.........t.....X##",
        "#####IIIII....#####^^^##",
        "##########~~~~##########",
        "##########wwww##########",
        "########################",
    ],
    bg=[(14, 2, 22, 9)],                                  # indoor pocket: cistern wall
    # (name, tag, frame, centre column, floor row | None, hang-from row | None)
    props=[("hf_icicle", "idle", 0, 6.0, None, 2), ("hf_icicle", "shake", 0, 7.6, None, 2)],
    icefall=(18.0, 1, 10),                                # centre column, top row, floor row
    player=(7, 10),
)


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#XI"


def mask_solid(fg, x, y):
    """Neighbour test for terrain masks: water counts as filled (no snow lip under the pool)."""
    return solid_at(fg, x, y) or fg[y][x] in "~w"


def prop_frame(props, name, tag, k):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return env_preview.flatten(w, h, layers, frames[a + k])


def sheet_frame(name, i=0):
    p = os.path.join(ASSETS, f"{name}.png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    return im.crop((i * 64, 0, i * 64 + 64, 40))


def with_alpha(im, a):
    im = im.copy()
    al = im.getchannel("A").point(lambda v: int(v * a))
    im.putalpha(al)
    return im


def render_room(tiles, far, mid, props, camx=0):
    fg = ROOM["fg"]
    Wp, Hp = 384, 216
    img = Image.new("RGBA", (Wp, Hp), (20, 20, 26, 255))
    for layer, fac in ((far, 0.08), (mid, 0.3)):
        ox = -int(camx * fac) % 512
        img.alpha_composite(layer, (ox - 512, 0))
        img.alpha_composite(layer, (ox, 0))
    for (x0, y0, x1, y1) in ROOM["bg"]:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if not solid_at(fg, x, y):
                    r = h01(x * 7 + 3, y * 13 + 5, 9)
                    k = 41 if x in (x0, x1) else (38 if r < 0.78 else (39 if r < 0.88 else 40))
                    img.alpha_composite(tiles[k], (x * 16, y * 16))
    # frozen waterfall column (decor, behind the play layer)
    cx, top, floor = ROOM["icefall"]
    ice = props["hf_icefall"]
    y = top * 16
    segs = [("top", 0)]
    n_mid = (floor * 16 - top * 16 - 96 + 47) // 48
    segs += [("mid", i % 4) for i in range(n_mid)]
    for (tag, k) in segs:
        img.alpha_composite(prop_frame(props, "hf_icefall", tag, k), (int(cx * 16 - 16), y))
        y += 48
    img.alpha_composite(prop_frame(props, "hf_icefall", "bottom", 0), (int(cx * 16 - 16), floor * 16 - 48))
    front = blank(Wp, Hp)
    water = blank(Wp, Hp)
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch in "#XI":
                m = 0
                if not mask_solid(fg, x, y - 1): m |= 1
                if not mask_solid(fg, x + 1, y): m |= 2
                if not mask_solid(fg, x, y + 1): m |= 4
                if not mask_solid(fg, x - 1, y): m |= 8
                if ch == "I":
                    idx = ICE0 + m
                elif ch == "X":
                    idx = 46
                else:
                    idx = m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)
                front.alpha_composite(tiles[idx], (x * 16, y * 16))
                if m & 1 and ch == "#" and h01(x * 5, y, 1) < 0.3 and y > 0:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l = x > 0 and row[x - 1] == "="
                r = x < len(row) - 1 and row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else (32 if r else (34 if l else 35))], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "~w":
                water.alpha_composite(tiles[WSURF if ch == "~" else WBODY], (x * 16, y * 16))
            elif ch in "Crkot":
                img.alpha_composite(tiles[{"C": 42, "r": 43, "k": 44, "o": 45, "t": 47}[ch]], (x * 16, y * 16))
    for (name, tag, k, cx, floor, hang) in ROOM["props"]:
        im = prop_frame(props, name, tag, k)
        y = floor * 16 - im.size[1] if floor is not None else hang * 16
        img.alpha_composite(im, (int(cx * 16 - im.size[0] / 2), y))
    pl, wp = sheet_frame("player"), sheet_frame("wpn_longsword")
    px_, fy = ROOM["player"]
    for im in (pl, wp):
        if im is not None:
            img.alpha_composite(im, (px_ * 16 + 8 - 28, fy * 16 - 40))
    img.alpha_composite(front)
    img.alpha_composite(with_alpha(water, WATER_ALPHA))
    scale(img, 3).save(os.path.join(PREV, f"room_{BIOME}.png"))
    return img


def env_preview_img(tiles, far, mid):
    """Tileset strip (all 66) + far + mid over magenta + composite + wrap-seam strip."""
    strip = blank(16 * len(tiles), 16)
    for i, t in enumerate(tiles):
        strip.alpha_composite(t, (i * 16, 0))
    strip = scale(strip, 1)
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255))
    m.alpha_composite(mid)
    comp = far.copy()
    comp.alpha_composite(mid)
    wrap = Image.new("RGBA", (512, 216))
    wrap.alpha_composite(comp.crop((256, 0, 512, 216)), (0, 0))
    wrap.alpha_composite(comp.crop((0, 0, 256, 216)), (256, 0))
    Wd = max(strip.size[0], 1024)
    out = Image.new("RGBA", (Wd, strip.size[1] + 216 * 2 + 30), (70, 70, 76, 255))
    out.alpha_composite(strip, (0, 0))
    out.alpha_composite(far, (0, strip.size[1] + 10))
    out.alpha_composite(m, (512, strip.size[1] + 10))
    out.alpha_composite(comp, (0, strip.size[1] + 236))
    out.alpha_composite(wrap, (512, strip.size[1] + 236))
    d = ImageDraw.Draw(out)
    d.text((516, strip.size[1] + 238), "wrap seam at centre", fill=(255, 255, 255, 255))
    out.save(os.path.join(PREV, f"env_{BIOME}.png"))


def seam_test(tiles, k=4):
    """Random blob using every mask + variants; the middle band uses the ice-floor set on its top
    surfaces (mixed with normal tiles) and a water pool, drawn on grey: checks seams at 4x."""
    rnd = random.Random(3)
    Wt, Ht = 16, 10
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
            if 4 <= x <= 11 and h01(x, y, 2) < 0.55:
                idx = ICE0 + m
            img.alpha_composite(tiles[idx], (x * 16, y * 16))
    scale(img, k).save(os.path.join(PREV, f"seams_{BIOME}.png"))


def props_sheet(props, k=4):
    rows = []
    for name, (w, h, layers, frames, tags) in props:
        for (t, a, b) in tags:
            rows.append((name, t, w, h, [env_preview.flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    rw = max(len(r[4]) * (r[2] * k + 6) for r in rows) + 170
    rh = sum(r[3] * k + 8 for r in rows) + 8
    sheet = Image.new("RGBA", (rw, rh), env_preview.GREY)
    d = ImageDraw.Draw(sheet)
    y = 8
    for (name, t, w, h, ims) in rows:
        d.text((6, y + 2), name, fill=(235, 235, 235, 255))
        d.text((6, y + 14), f"  {t} ({len(ims)})", fill=(200, 200, 160, 255))
        x = 170
        for im in ims:
            sheet.alpha_composite(scale(im, k), (x, y))
            x += w * k + 6
        y += h * k + 8
    # the frozen waterfall stacked (top + mid x2 + bottom) to check the vertical joins
    w, h, layers, frames, tags = dict(props)["hf_icefall"]
    tg = {t: a for (t, a, b) in tags}
    stack = blank(w, h * 4)
    for i, fi in enumerate((tg["top"], tg["mid"], tg["mid"] + 2, tg["bottom"])):
        stack.alpha_composite(env_preview.flatten(w, h, layers, frames[fi]), (0, i * h))
    big = Image.new("RGBA", (rw + w * 3 + 20, max(rh, h * 4 * 3 + 16)), env_preview.GREY)
    big.alpha_composite(sheet, (0, 0))
    big.alpha_composite(scale(stack, 3), (rw + 10, 8))
    big.save(os.path.join(PREV, f"props_{BIOME}.png"))


def main():
    ase = "--no-ase" not in sys.argv
    report = []
    props = {n: f() for n, f in hoarfrost_props.PROPS.items()}
    tiles = hoarfrost_tiles.build_tileset()
    assert len(tiles) == N_TILES
    for i, t in enumerate(tiles):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    for i in (WSURF, WBODY):
        assert tiles[i].getextrema()[3][0] == 255, f"water tile {i} must be fully opaque"
    far_fn, mid_fn = hoarfrost_bg.BUILDERS[BIOME]
    far, mid = far_fn(), mid_fn()
    assert far.getextrema()[3][0] == 255, "far layer must be opaque"
    assert all(a in (0, 255) for a in set(mid.getdata(3))), "mid layer must be pixel-clean"
    env_preview.tileset_sheet(BIOME, tiles)
    seam_test(tiles)
    env_preview_img(tiles, far, mid)
    render_room(tiles, far, mid, props)
    for name, (w, h, layers, frames, tags) in props.items():
        for f in frames:
            for c in f["cels"].values():
                assert all(a in (0, 255) for a in set(c.getdata(3))), name + " not pixel-clean"
    props_sheet(list(props.items()))
    if ase:
        asebuild.build(f"tiles_{BIOME}", 16, 16, ["Tiles"],
                       [{"ms": 100, "cels": {"Tiles": t}} for t in tiles], TILE_TAGS)
        build_bg(f"bg_{BIOME}_far", far, True)
        build_bg(f"bg_{BIOME}_mid", mid, True)
        report.append(verify(f"tiles_{BIOME}", N_TILES, TILE_TAGS, (16, 16)))
        report.append(verify(f"bg_{BIOME}_far", 1, [("loop", 0, 0)], (512, 216)))
        report.append(verify(f"bg_{BIOME}_mid", 1, [("loop", 0, 0)], (512, 216)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
        print("json tags verified:", len(report), "sheets")
    print("built", BIOME)


if __name__ == "__main__":
    main()
