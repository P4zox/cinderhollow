#!/usr/bin/env python3
"""Environment art for the `thornveil` biome -- THORNVEIL WOOD (agent T).

Builds (Aseprite via asebuild):
  tiles_thornveil   48 x 16x16, tag `all`, standard index layout           (thornveil_tiles.py)
  bg_thornveil_far  512x216 opaque, tileable                                (thornveil_bg.py)
  bg_thornveil_mid  512x216 transparent, tileable
  tv_tree tv_idol tv_ribbons tv_fern tv_shroom tv_vine tv_pod tv_hatch tv_hazards tv_fog   (thornveil_props.py)
Previews -> art/previews/: tiles_thornveil.png, seams_thornveil.png, env_thornveil.png, props_thornveil.png,
room_thornveil.png (mock room, 3x)

Usage: python3 art/gen_thornveil_env.py [--no-ase]
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                   # noqa: E402
import env_preview                                # noqa: E402
import thornveil_tiles, thornveil_bg, thornveil_props   # noqa: E402
from envlib import scale, blank, h01              # noqa: E402

PREV = env_preview.PREV
ASE = "--no-ase" not in sys.argv

ROOM = [
    "########################",
    "#####vv#################",
    "#....x.......r......x..#",
    "#......................#",
    "#......................#",
    "#...====.........====..#",
    "#......................#",
    "#......................#",
    "###.................k..#",
    "###b...k...........###.#",
    "########^^^^###########.",
    "########################",
    "########################",
    "########################",
]


def solid(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] == "#"


def render_room(tiles, far, mid, props):
    fg = ROOM
    img = Image.new("RGBA", (384, 216), (7, 16, 13, 255))
    img.alpha_composite(far, (0, 0))
    img.alpha_composite(mid.crop((60, 0, 444, 216)), (0, 0))
    back = blank(384, 216)
    for y in range(len(fg)):
        for x in range(len(fg[0])):
            if solid(fg, x, y):
                continue
            d = 9
            for yy in range(-3, 4):
                for xx in range(-3, 4):
                    if solid(fg, x + xx, y + yy):
                        d = min(d, max(abs(xx), abs(yy)))
            a = 1 if d <= 1 else 0.8 if d == 2 else 0.5 if d == 3 else 0.28
            t = tiles[38 + int(h01(x, y) * 4)].copy()
            t.putalpha(t.getchannel("A").point(lambda v: int(v * a)))
            back.alpha_composite(t, (x * 16, y * 16))
    tr = props["tv_tree"][2]
    back.alpha_composite(tr[0], (120 - 48, 9 * 16 + 16 - 240 + 16))
    back.alpha_composite(tr[2], (250 - 48, 10 * 16 - 240 + 16))
    img.alpha_composite(back)
    front = blank(384, 216)
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch == "#":
                m = (0 if solid(fg, x, y - 1) else 1) | (0 if solid(fg, x + 1, y) else 2) | (0 if solid(fg, x, y + 1) else 4) | (0 if solid(fg, x - 1, y) else 8)
                front.alpha_composite(tiles[m + (16 if h01(x + 7, y * 3) < 0.28 else 0)], (x * 16, y * 16))
                if m & 1 and h01(x * 5, y) < 0.3:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                L = x > 0 and row[x - 1] == "="
                R = x + 1 < len(row) and row[x + 1] == "="
                front.alpha_composite(tiles[33 if L and R else 32 if R else 34 if L else 35], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "xrkb":
                front.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))
    img.alpha_composite(front)
    # a few props
    idol = props["tv_idol"][2][0]
    img.alpha_composite(idol, (200 - 20, 10 * 16 - 64))
    rib = props["tv_ribbons"][2][0]
    img.alpha_composite(rib, (60 - 16, 8 * 16 - 48))
    hz = props["tv_hazards"][2]
    for i, x in enumerate((13, 14)):
        img.alpha_composite(hz[i], (x * 16 - 4, 10 * 16 - 24 + 16 - 16))
    for i, y in enumerate((5, 6, 7)):
        img.alpha_composite(hz[3 + min(i, 3)] if i < 2 else hz[6], (18 * 16 - 4, y * 16 - 8))
    pod = props["tv_pod"][2][0]
    img.alpha_composite(pod, (10 * 16 - 4, 2 * 16))
    fog = props["tv_fog"][2][0]
    img.alpha_composite(fog, (230, 100))
    img.alpha_composite(fog, (100, 110))
    return img


def main():
    tiles = thornveil_tiles.build()
    far, mid = thornveil_bg.far(), thornveil_bg.mid()
    assert far.getextrema()[3][0] == 255
    props = {n: f() for n, f in thornveil_props.PROPS.items()}
    props.update(thornveil_props.small_props())
    if ASE:
        asebuild.build("tiles_thornveil", 16, 16, ["Tiles"], [{"ms": 100, "cels": {"Tiles": t}} for t in tiles], [("all", 0, 47)])
        for nm, im in (("bg_thornveil_far", far), ("bg_thornveil_mid", mid)):
            asebuild.build(nm, 512, 216, ["Layer"], [{"ms": 1000, "cels": {"Layer": im}}], [("loop", 0, 0)])
        for nm, (w, h, frames, tags) in props.items():
            ms = 160 if nm in ("tv_idol", "tv_ribbons", "tv_vine") else 110
            asebuild.build(nm, w, h, ["Art"], [{"ms": ms, "cels": {"Art": f}} for f in frames], tags)
    env_preview.tileset_sheet("thornveil", tiles)
    env_preview.seam_test("thornveil", tiles)
    comp = far.copy(); comp.alpha_composite(mid)
    out = Image.new("RGBA", (1024, 216 * 2 + 10), (70, 70, 76, 255))
    out.alpha_composite(far, (0, 0)); out.alpha_composite(comp, (512, 0))
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255)); m.alpha_composite(mid)
    out.alpha_composite(m, (0, 226))
    out.save(os.path.join(PREV, "env_thornveil.png"))
    # props sheet
    rows = []
    for nm, (w, h, frames, tags) in props.items():
        rows.append(scale(thornveil_kit_strip(frames), 3 if h < 100 else 1))
    W = max(r.size[0] for r in rows); Hh = sum(r.size[1] + 6 for r in rows)
    sh = Image.new("RGBA", (W, Hh), (70, 70, 76, 255))
    y = 0
    for r in rows:
        sh.alpha_composite(r, (0, y)); y += r.size[1] + 6
    sh.save(os.path.join(PREV, "props_thornveil.png"))
    scale(render_room(tiles, far, mid, props), 3).save(os.path.join(PREV, "room_thornveil.png"))
    print("thornveil env ok")


def thornveil_kit_strip(frames):
    from thornveil_kit import strip
    return strip(frames)


if __name__ == "__main__":
    main()
