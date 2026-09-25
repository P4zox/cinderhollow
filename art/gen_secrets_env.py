#!/usr/bin/env python3
"""Environment art for agent X's biomes: `hermit` (The Hermit's Hollow) and `ember` (Ember's Hollow).

    python3 art/gen_secrets_env.py [--no-ase]

Builds tiles_<b> (48 frames 16x16, tag `all`), bg_<b>_far (512x216 opaque), bg_<b>_mid (512x216 transparent).
Previews: art/previews/tiles_<b>.png, seams_<b>.png, room_<b>.png (mock room, 3x, player for scale).
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import env_preview  # noqa: E402
import secrets_env as SE  # noqa: E402
from envlib import scale, blank, h01  # noqa: E402
from gen_env import build_tiles, build_bg, verify  # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), "assets")
ROOM = [
    "########################",
    "########...&&&&...######",
    "##r.........&&.......x##",
    "##....................##",
    "#......................#",
    "#...====.........===...#",
    "#......................#",
    "#......................#",
    "##k..........b.......k.#",
    "######....##########^^##",
    "######....##########^^##",
    "#######################.",
    "########################",
    "########################",
]


def render_room(biome, tiles, far, mid):
    img = Image.new("RGBA", (384, 216), (10, 8, 10, 255))
    img.alpha_composite(far)
    img.alpha_composite(mid)
    solid = lambda x, y: y < 0 or y >= len(ROOM) or x < 0 or x >= 24 or ROOM[y][x] == "#"
    back = blank(384, 216)
    front = blank(384, 216)
    for y, row in enumerate(ROOM):
        for x, ch in enumerate(row):
            if not solid(x, y) and ch != "&":
                back.alpha_composite(tiles[38 + int(h01(x, y, 1) * 4)], (x * 16, y * 16))
            if ch == "#":
                m = (1 if not solid(x, y - 1) else 0) | (2 if not solid(x + 1, y) else 0) | (4 if not solid(x, y + 1) else 0) | (8 if not solid(x - 1, y) else 0)
                front.alpha_composite(tiles[m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y, 1) < 0.3 and y > 0:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l, r = x > 0 and row[x - 1] == "=", x < 23 and row[x + 1] == "="
                front.alpha_composite(tiles[33 if l and r else 32 if r else 34 if l else 35], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch in "xrkb":
                back.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
    img.alpha_composite(back)
    shade = Image.new("RGBA", (384, 216), (4, 3, 8, 110))
    img.alpha_composite(shade)
    p = os.path.join(ASSETS, "player.png")
    if os.path.exists(p):
        pl = Image.open(p).convert("RGBA").crop((0, 0, 64, 40))
        img.alpha_composite(pl, (12 * 16 + 8 - 28, 9 * 16 - 40))
    img.alpha_composite(front)
    scale(img, 3).save(os.path.join(env_preview.PREV, f"room_{biome}.png"))


def main():
    ase = "--no-ase" not in sys.argv
    for biome in ("hermit", "ember"):
        tiles = SE.build_tileset(biome)
        for i, t in enumerate(tiles):
            assert all(a in (0, 255) for a in set(t.getdata(3))), f"{biome} tile {i} not pixel-clean"
        far_fn, mid_fn = SE.BUILDERS[biome]
        far, mid = far_fn(), mid_fn()
        env_preview.tileset_sheet(biome, tiles)
        env_preview.seam_test(biome, tiles)
        render_room(biome, tiles, far, mid)
        if ase:
            build_tiles(biome, tiles, True)
            build_bg(f"bg_{biome}_far", far, True)
            build_bg(f"bg_{biome}_mid", mid, True)
            print(verify(f"tiles_{biome}", 48, [("all", 0, 47)], (16, 16)))
        print("built", biome)


if __name__ == "__main__":
    main()
