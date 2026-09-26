#!/usr/bin/env python3
"""Environment art for the `dunes` biome -- THE SUNSCORCHED DUNES (agent DU).

Builds:
  tiles_dunes     48 frames of 16x16, tag `all`, standard index layout               (dunes_tiles.py)
  tiles_dunes_fx  16x16: qs_top(6) qs_body(4) slope(1) sand(1)                      (dunes_tiles.py)
  bg_dunes_far    512x216 opaque, tileable, tag `loop`                               (dunes_bg.py)
  bg_dunes_mid    512x216 transparent, tileable, tag `loop`                          (dunes_bg.py)
  du_props, du_stele, du_altar, du_colossus                                         (dunes_props.py)
Previews -> art/previews/: tiles_dunes.png, seams_dunes.png, env_dunes.png, room_dunes.png (mock room at 3x), props_dunes.png

Usage: python3 art/gen_dunes_env.py [--no-ase]
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                   # noqa: E402
import env_preview                                # noqa: E402
import dunes_tiles, dunes_bg, dunes_props         # noqa: E402
from envlib import scale, blank, h01              # noqa: E402
from gen_env import build_tiles, build_bg, verify, env_preview_img  # noqa: E402  (read-only reuse)

BIOME = "dunes"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV

# mock room: '#' solid, '/' slope wedge (slope line from (4,8) to (12,12) in tile corners), '-' quicksand, '=' platform
ROOM = [
    "########################",
    "#.......x.......r......#",
    "#......................#",
    "#......................#",
    "#......................#",
    "#...............====...#",
    "#......................#",
    "#k.....................#",
    "####///................#",
    "######///..............#",
    "########///.......b....#",
    "##########//#---#####..#",
    "#############---#####..#",
    "########################",
]
SLOPE = (4, 8, 12, 12)


def _apply_slope(rows, x0, y0, x1, y1):
    g = [list(r) for r in rows]
    k = (y1 - y0) / (x1 - x0)
    ly = lambda px: (y0 + (px / 16.0 - x0) * k) * 16.0
    for cx in range(x0, x1):
        a_, b_ = ly(cx * 16), ly(cx * 16 + 16)
        lo, hi = min(a_, b_), max(a_, b_)
        for cy in range(len(g)):
            top = cy * 16
            if top >= hi + 3:
                g[cy][cx] = '#'
            elif top + 16 > lo:
                g[cy][cx] = '/'
            elif g[cy][cx] in '#/':
                g[cy][cx] = '.'
    return [''.join(r) for r in g]


ROOM = _apply_slope(ROOM, *SLOPE)


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#/"


def render_room(tiles, fxt, far, mid, props):
    fg = ROOM
    img = Image.new("RGBA", (384, 216), (40, 24, 12, 255))
    img.alpha_composite(far, (0, 0))
    img.alpha_composite(mid.crop((60, 0, 444, 216)), (0, 0))
    col = props["du_colossus"]
    cimg = env_preview.flatten(col[0], col[1], col[2], col[3][0])
    for y in range(len(fg)):
        for x in range(len(fg[0])):
            if solid_at(fg, x, y):
                continue
            d = 9
            for yy in range(-3, 4):
                for xx in range(-3, 4):
                    if solid_at(fg, x + xx, y + yy) and fg[min(len(fg) - 1, max(0, y + yy))][min(23, max(0, x + xx))] == "#":
                        d = min(d, max(abs(xx), abs(yy)))
            a = 1 if d <= 1 else 0.8 if d == 2 else 0.5 if d == 3 else 0.28
            t = tiles[38 + int(h01(x, y) * 4)].copy()
            t.putalpha(t.getchannel("A").point(lambda v: int(v * a)))
            img.alpha_composite(t, (x * 16, y * 16))
    img.alpha_composite(cimg, (200, 176 - 128 + 20))
    front = blank(384, 216)
    x0, y0, x1, y1 = SLOPE
    k = (y1 - y0) / (x1 - x0)
    slope_img, sand_img = fxt["slope"][0], fxt["sand"][0]
    sp, dp = slope_img.load(), sand_img.load()
    under_slope = set()
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch == "#":
                if any(fg[yy][x] == "/" for yy in range(0, y)):
                    under_slope.add((x, y))
                    front.alpha_composite(sand_img, (x * 16, y * 16))
                    continue
                m = (1 if not solid_at(fg, x, y - 1) else 0) | (2 if not solid_at(fg, x + 1, y) else 0) | \
                    (4 if not solid_at(fg, x, y + 1) else 0) | (8 if not solid_at(fg, x - 1, y) else 0)
                front.alpha_composite(tiles[m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y, 1) < 0.3:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "/":
                fp = front.load()
                for i in range(16):
                    X = x * 16 + i
                    ly = round((y0 + (X + 0.5 - x0 * 16) / 16 * k) * 16)
                    for j in range(max(0, ly - y * 16), 16):
                        dep = y * 16 + j - ly
                        fp[X, y * 16 + j] = sp[X % 16, dep] if dep < 16 else dp[X % 16, dep % 16]
            elif ch == "=":
                l, r = row[x - 1] == "=", row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else 32 if r else 34 if l else 35], (x * 16, y * 16))
            elif ch in "xrkb":
                img.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
            elif ch == "-":
                surf = fg[y - 1][x] != "-"
                front.alpha_composite(fxt["qs_top" if surf else "qs_body"][x % 4], (x * 16, y * 16))
    pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ASSETS, "wpn_longsword.png")).convert("RGBA").crop((0, 0, 64, 40))
    for (px_, py_) in ((15 * 16 + 8 - 28, 10 * 16 + 16 - 40 + 1), (3 * 16 + 8 - 28, 7 * 16 + 16 - 40 + 1)):
        img.alpha_composite(pl, (px_, py_))
        img.alpha_composite(wp, (px_, py_))
    st = props["du_stele"]
    img.alpha_composite(env_preview.flatten(st[0], st[1], st[2], st[3][0]), (18 * 16 - 4, 10 * 16 - 16))
    al = props["du_altar"]
    img.alpha_composite(env_preview.flatten(al[0], al[1], al[2], al[3][2]), (10 * 16 - 8, 16))
    img.alpha_composite(front)
    scale(img, 3).save(os.path.join(PREV, f"room_{BIOME}.png"))


def props_sheet(props, k=4):
    rows = []
    for name, (w, h, layers, frames, tags) in props.items():
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
    tiles = dunes_tiles.build_tileset()
    for i, t in enumerate(tiles):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    far_fn, mid_fn = dunes_bg.BUILDERS[BIOME]
    far, mid = far_fn(), mid_fn()
    assert far.getextrema()[3][0] == 255, "far layer must be opaque"
    props = {n: f() for n, f in dunes_props.PROPS.items()}
    fxw, fxh, fxl, fxf, fxtags = dunes_tiles.build_fx()
    fxt = {t: [env_preview.flatten(fxw, fxh, fxl, fxf[i]) for i in range(a, b + 1)] for t, a, b in fxtags}
    env_preview.tileset_sheet(BIOME, tiles)
    env_preview.seam_test(BIOME, tiles)
    env_preview_img(BIOME, tiles, far, mid)
    render_room(tiles, fxt, far, mid, props)
    props_sheet(props)
    if ase:
        report = []
        build_tiles(BIOME, tiles, True)
        build_bg(f"bg_{BIOME}_far", far, True)
        build_bg(f"bg_{BIOME}_mid", mid, True)
        asebuild.build("tiles_dunes_fx", fxw, fxh, fxl, fxf, fxtags)
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
        report.append(verify(f"bg_{BIOME}_far", 1, [("loop", 0, 0)], (512, 216)))
        report.append(verify(f"bg_{BIOME}_mid", 1, [("loop", 0, 0)], (512, 216)))
        report.append(verify("tiles_dunes_fx", len(fxf), fxtags, (16, 16)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
    print("built", BIOME)


if __name__ == "__main__":
    main()
