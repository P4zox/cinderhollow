#!/usr/bin/env python3
"""Environment art for the `archives` biome — THE ASHEN ARCHIVES (docs/ART_SPEC.md section 6 contract).

Builds:
  tiles_archives     48 frames of 16x16, tag `all`, standard index layout      (archives_tiles.py)
  bg_archives_far    512x216 opaque, tileable, tag `loop`                        (archives_bg.py)
  bg_archives_mid    512x216 transparent, tileable, tag `loop`                   (archives_bg.py)
  prop_lectern (32x32 loop 4), prop_shelfcage (32x48 idle 1), prop_candelabra (16x32 loop 4)
                                                                                 (archives_props.py)
Previews -> art/previews/: tiles_archives.png, seams_archives.png, env_archives.png,
room_archives.png (384x216 mock room at 3x, player + longsword for scale), props_archives.png.

Usage: python3 art/gen_archives.py [--no-ase]   (--no-ase: previews only, skip Aseprite export)
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                        # noqa: E402
import env_preview                                     # noqa: E402
import archives_tiles, archives_bg, archives_props     # noqa: E402
from envlib import scale, blank, h01                   # noqa: E402
from gen_env import build_tiles, build_bg, verify      # noqa: E402  (read-only reuse)
from gen_env2 import env_preview_img                   # noqa: E402  (read-only reuse)

BIOME = "archives"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV

# --------------------------------------------------------------------------- mock room
# '#' solid  'X' breakable  '=' one-way  '^' floor spikes  'v' ceiling spikes
# 'C' chain+grimoire(42)  'k' candles(43)  'b' tomes(44)  'p' pages(45)  't' tuft(47)
ROOM = dict(
    fg=[
        "########........########",
        "#####vv#........###vv###",
        "#..C............C.....##",
        "#..C............C......#",
        "#.......................",
        "#..====........====.....",
        "#......................#",
        "##...........=.........#",
        "###....................#",
        "###b.....k......p....X##",
        "##########^^^###########",
        "########################",
        "########################",
        "########################",
    ],
    bg=[(15, 2, 21, 9)],                                  # indoor pocket: bookshelf wall
    # (name, tag, frame, centre column, floor row | None=hang from the top of row)
    props=[("prop_lectern", "loop", 0, 5.5, 10, None), ("prop_candelabra", "loop", 1, 7.5, 10, None),
           ("prop_candelabra", "loop", 2, 19.5, 10, None), ("prop_shelfcage", "idle", 0, 11.5, None, 0)],
    player=(14, 10),
)


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X"


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
                    r = h01(x, y, 9)
                    k = 41 if x in (x0, x1) else (38 if r < 0.6 else (39 if r < 0.82 else 40))
                    img.alpha_composite(tiles[k], (x * 16, y * 16))
    front = blank(Wp, Hp)
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch in "#X":
                m = 0
                if not solid_at(fg, x, y - 1): m |= 1
                if not solid_at(fg, x + 1, y): m |= 2
                if not solid_at(fg, x, y + 1): m |= 4
                if not solid_at(fg, x - 1, y): m |= 8
                idx = 46 if ch == "X" else m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)
                front.alpha_composite(tiles[idx], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y, 1) < 0.3 and y > 0:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l = x > 0 and row[x - 1] == "="
                r = x < len(row) - 1 and row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else (32 if r else (34 if l else 35))], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "Ckbpt":
                img.alpha_composite(tiles[{"C": 42, "k": 43, "b": 44, "p": 45, "t": 47}[ch]], (x * 16, y * 16))
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
    scale(img, 3).save(os.path.join(PREV, f"room_{BIOME}.png"))
    return img


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
    sheet.save(os.path.join(PREV, f"props_{BIOME}.png"))


def main():
    ase = "--no-ase" not in sys.argv
    report = []
    props = {n: f() for n, f in archives_props.PROPS.items()}
    tiles = archives_tiles.build_tileset()
    for i, t in enumerate(tiles):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    far_fn, mid_fn = archives_bg.BUILDERS[BIOME]
    far, mid = far_fn(), mid_fn()
    assert far.getextrema()[3][0] == 255, "far layer must be opaque"
    assert all(a in (0, 255) for a in set(mid.getdata(3))), "mid layer must be pixel-clean"
    env_preview.tileset_sheet(BIOME, tiles)
    env_preview.seam_test(BIOME, tiles)
    env_preview_img(BIOME, tiles, far, mid)
    render_room(tiles, far, mid, props)
    for name, (w, h, layers, frames, tags) in props.items():
        for f in frames:
            for c in f["cels"].values():
                assert all(a in (0, 255) for a in set(c.getdata(3))), name + " not pixel-clean"
    props_sheet(list(props.items()))
    if ase:
        build_tiles(BIOME, tiles, True)
        build_bg(f"bg_{BIOME}_far", far, True)
        build_bg(f"bg_{BIOME}_mid", mid, True)
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
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
