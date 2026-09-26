#!/usr/bin/env python3
"""Environment art for the `necropolis` biome -- THE NECROPOLIS OF VAEL (agent N).

Builds tiles_necropolis (48), bg_necropolis_far / _mid (512x216), props nv_props, nv_bell, nv_bell_big, nv_walk, nv_plat.
Previews -> art/previews/: tiles_necropolis.png, seams_necropolis.png, env_necropolis.png, room_necropolis.png, props_necropolis.png
Usage: python3 art/gen_necro_env.py [--no-ase]
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                   # noqa: E402
import env_preview                                # noqa: E402
import necro_tiles, necro_bg, necro_props         # noqa: E402
from envlib import scale, blank, h01              # noqa: E402
from gen_env import build_tiles, build_bg, verify, env_preview_img  # noqa: E402

BIOME = "necropolis"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV
ROOM = [
    "########################",
    "#..x.......r.......x...#",
    "#......................#",
    "#......................#",
    "#......................#",
    "#...====..........{{{..#",
    "#......................#",
    "#......................#",
    "###....................#",
    "###...............######",
    "######^^^^#####..#######",
    "#######################.",
    "########################",
    "########################",
]


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] == "#"


def flat(props, name, tag, k=0):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return env_preview.flatten(w, h, layers, frames[a + k])


def render_room(tiles, far, mid, props):
    fg = ROOM
    img = Image.new("RGBA", (384, 216), (5, 6, 12, 255))
    img.alpha_composite(far, (0, 0))
    img.alpha_composite(mid.crop((60, 0, 444, 216)), (0, 0))
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
    front = blank(384, 216)
    wk = {k: flat(props, "nv_walk", k) for k in "lmrs"}
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch == "#":
                m = (1 if not solid_at(fg, x, y - 1) else 0) | (2 if not solid_at(fg, x + 1, y) else 0) | \
                    (4 if not solid_at(fg, x, y + 1) else 0) | (8 if not solid_at(fg, x - 1, y) else 0)
                front.alpha_composite(tiles[m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y, 1) < 0.3:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l, r = row[x - 1] == "=", row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else 32 if r else 34 if l else 35], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "{":
                l, r = row[x - 1] == "{", row[x + 1] == "{"
                front.alpha_composite(wk["m" if l and r else "l" if r else "r" if l else "s"], (x * 16, y * 16))
            elif ch in "xrkb":
                img.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
    pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ASSETS, "wpn_longsword.png")).convert("RGBA").crop((0, 0, 64, 40))
    img.alpha_composite(pl, (8 * 16 + 8 - 28, 9 * 16 - 40))
    img.alpha_composite(wp, (8 * 16 + 8 - 28, 9 * 16 - 40))
    img.alpha_composite(flat(props, "nv_props", "brazier", 1), (4 * 16 + 8 - 24, 9 * 16 - 64))
    img.alpha_composite(flat(props, "nv_props", "statue"), (13 * 16 - 24, 9 * 16 - 64))
    img.alpha_composite(flat(props, "nv_props", "banner", 0), (10 * 16 - 24, 32))
    img.alpha_composite(flat(props, "nv_bell", "idle"), (16 * 16 - 16, 20))
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
    tiles = necro_tiles.build_tileset()
    for i, t in enumerate(tiles):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    far_fn, mid_fn = necro_bg.BUILDERS[BIOME]
    far, mid = far_fn(), mid_fn()
    assert far.getextrema()[3][0] == 255, "far layer must be opaque"
    props = {n: f() for n, f in necro_props.PROPS.items()}
    env_preview.tileset_sheet(BIOME, tiles)
    env_preview.seam_test(BIOME, tiles)
    env_preview_img(BIOME, tiles, far, mid)
    render_room(tiles, far, mid, props)
    props_sheet(props)
    if ase:
        report = []
        build_tiles(BIOME, tiles, True)
        build_bg(f"bg_{BIOME}_far", far, True)
        build_bg(f"bg_{BIOME}_mid", mid, True)
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
    print("built", BIOME)


if __name__ == "__main__":
    main()
