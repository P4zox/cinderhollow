#!/usr/bin/env python3
"""Environment art for the `deep` biome -- THE BURNING DEEP (agent D).

Builds:
  tiles_deep      48 frames of 16x16, tag `all`, standard index layout            (deep_tiles.py)
  tiles_deep_fx   16x16 animated tiles: lava_top(8) lava_body(4) belt_l/m/r(4)   (deep_tiles.py via deep_props.py)
  bg_deep_far     512x216 opaque, tileable, tag `loop`                            (deep_bg.py)
  bg_deep_mid     512x216 transparent, tileable, tag `loop`                       (deep_bg.py)
  dp_crucible (96x72 idle 4), dp_props (32x32 hatch / hatch_open)                  (deep_props.py)
Previews -> art/previews/: tiles_deep.png, seams_deep.png, env_deep.png, room_deep.png (mock room at 3x), props_deep.png

Usage: python3 art/gen_deep_env.py [--no-ase]
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                   # noqa: E402
import env_preview                                # noqa: E402
import deep_tiles, deep_bg, deep_props            # noqa: E402
from envlib import scale, blank, h01              # noqa: E402
from gen_env import build_tiles, build_bg, verify  # noqa: E402  (read-only reuse)
from gen_env import env_preview_img               # noqa: E402

BIOME = "deep"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV

ROOM = [
    "########################",
    "#####vv####vvv##########",
    "#..x..........r......x.#",
    "#..x..........r........#",
    "#......................#",
    "#...====.........====..#",
    "#......................#",
    "#......................#",
    "###.................k..#",
    "###b...k.......>>>>###.#",
    "######****#####>>>>###.#",
    "######****#############.",
    "########################",
    "########################",
]


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X<>"


def flat(props, name, tag, k=0):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return env_preview.flatten(w, h, layers, frames[a + k])


def render_room(tiles, fxt, far, mid, props):
    fg = ROOM
    img = Image.new("RGBA", (384, 216), (20, 10, 8, 255))
    img.alpha_composite(far, (0, 0))
    img.alpha_composite(mid.crop((60, 0, 444, 216)), (0, 0))
    # indoor back wall fading toward open space
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
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "xrkb":
                img.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
            elif ch == "*":
                surf = fg[y - 1][x] != "*"
                front.alpha_composite(fxt["lava_top" if surf else "lava_body"][x % 4], (x * 16, y * 16))
            elif ch in "<>":
                l, r = row[x - 1] in "<>", row[x + 1] in "<>"
                part = "belt_l" if not l else "belt_r" if not r else "belt_m"
                front.alpha_composite(fxt[part][x % 4], (x * 16, y * 16))
    pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
    wp = Image.open(os.path.join(ASSETS, "wpn_longsword.png")).convert("RGBA").crop((0, 0, 64, 40))
    img.alpha_composite(pl, (10 * 16 + 8 - 28, 9 * 16 + 16 - 40 + 16))
    img.alpha_composite(wp, (10 * 16 + 8 - 28, 9 * 16 + 16 - 40 + 16))
    cru = flat(props, "dp_crucible", "idle", 0)
    img.alpha_composite(cru, (150, 20))
    img.alpha_composite(front)
    # crude warm light pass so the preview reads like the game (glow over lava)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gp = glow.load()
    for y in range(216):
        for x in range(384):
            d = min(((x - 128) ** 2 + (y - 168) ** 2) ** 0.5, 999)
            a = max(0, 1 - d / 90)
            if a > 0:
                gp[x, y] = (255, 110, 40, int(40 * a))
    img.alpha_composite(glow)
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
    tiles = deep_tiles.build_tileset()
    for i, t in enumerate(tiles):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    far_fn, mid_fn = deep_bg.BUILDERS[BIOME]
    far, mid = far_fn(), mid_fn()
    assert far.getextrema()[3][0] == 255, "far layer must be opaque"
    props = {n: f() for n, f in deep_props.PROPS.items()}
    w, h, layers, frames, tags = props["tiles_deep_fx"]
    fxt = {t: [env_preview.flatten(w, h, layers, frames[i]) for i in range(a, b + 1)] for t, a, b in tags}
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
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
        report.append(verify(f"bg_{BIOME}_far", 1, [("loop", 0, 0)], (512, 216)))
        report.append(verify(f"bg_{BIOME}_mid", 1, [("loop", 0, 0)], (512, 216)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
    print("built", BIOME)


if __name__ == "__main__":
    main()
