#!/usr/bin/env python3
"""Environment art for the v2 biomes (docs/ART_SPEC2.md section F).

Builds, for each biome (mire, crown):
  tiles_<b>     48 frames of 16x16, tag `all`, same index layout as v1   (env2_tiles.py)
  bg_<b>_far    512x216 opaque, tileable, tag `loop`                      (env2_bg.py)
  bg_<b>_mid    512x216 transparent, tileable, tag `loop`                 (env2_bg.py)
and the props prop_anvil, prop_bell, prop_throne, prop_grave             (env2_props.py).

Previews -> art/previews/: tiles_<b>.png (4x, indexed), seams_<b>.png, env_<b>.png (tileset +
parallax + a wrap-seam strip), room_<b>.png (384x216 mock room at 3x with the player for scale),
props2.png.

Usage: python3 art/gen_env2.py [--no-ase]   (--no-ase: previews only, skip Aseprite export)
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                        # noqa: E402
import env_preview                                     # noqa: E402
import env2_tiles, env2_bg, env2_props                 # noqa: E402
from envlib import scale, blank, h01                   # noqa: E402
from gen_env import build_tiles, build_bg, verify      # noqa: E402  (read-only reuse)

BIOMES = ["mire", "crown"]
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV

# --------------------------------------------------------------------------- mock rooms
# '#' solid  'X' breakable  '=' one-way  '^' floor spikes  'v' ceiling spikes
# 'C' hanging strand(42)  'R' hanging roots(43)  'k' light cluster(44)  'b' clutter(45)  't' tuft(47)
# '~' poison water (drawn by the engine; faked here only to judge contrast)
ROOMS = {
    "mire": dict(
        fg=[
            "........................",
            "........................",
            "...............#########",
            "...............#C.R.vv.#",
            "................C.R....#",
            "....===................#",
            "........................",
            "#.......===............#",
            "##t.b.................X#",
            "#####.......b....k....##",
            "#####~~~~~~~#^^#########",
            "#####~~~~~~~############",
            "#####~~~~~~~############",
            "########################",
        ],
        bg=[(16, 3, 22, 9)],                   # indoor pocket: background walls
        props=[("prop_grave", "idle", 0, 3.5, 9), ("prop_anvil", "loop", 2, 19.5, 10)],
        player=(15, 10),
    ),
    "crown": dict(
        fg=[
            "..............##########",
            "..............##########",
            "..............CRvv......",
            "...............R........",
            "........................",
            ".....====...............",
            "........................",
            "#..............==.......",
            "##.................#####",
            "###t....k..........X####",
            "##########..#^^#########",
            "##########..############",
            "##########..############",
            "##########..############",
        ],
        bg=[],
        props=[("prop_bell", "idle", 0, 5.0, 10), ("prop_throne", "idle", 0, 21.5, 8)],
        player=(16, 10),
    ),
}


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X"


def prop_frame(props, name, tag, k):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return env_preview.flatten(w, h, layers, frames[a + k])


def render_room(biome, tiles, far, mid, props, camx=0):
    R = ROOMS[biome]
    fg = R["fg"]
    Wp, Hp = 384, 216
    img = Image.new("RGBA", (Wp, Hp), (20, 20, 26, 255))
    for layer, fac in ((far, 0.08), (mid, 0.3)):
        ox = -int(camx * fac) % 512
        img.alpha_composite(layer, (ox - 512, 0))
        img.alpha_composite(layer, (ox, 0))
    # background walls in the indoor pocket (engine: indoor rooms only)
    for (x0, y0, x1, y1) in R["bg"]:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if not solid_at(fg, x, y):
                    r = h01(x, y, 9)
                    k = 41 if x in (x0, x1) else (38 if r < 0.62 else (39 if r < 0.85 else 40))
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
            elif ch in "CRkbt":
                img.alpha_composite(tiles[{"C": 42, "R": 43, "k": 44, "b": 45, "t": 47}[ch]], (x * 16, y * 16))
    # props (bottom-centred on tile column cx, standing on the top of row `floor`)
    for (name, tag, k, cx, floor) in R["props"]:
        im = prop_frame(PROPS_CACHE, name, tag, k)
        img.alpha_composite(im, (int(cx * 16 - im.size[0] / 2), floor * 16 - im.size[1]))
    pp = os.path.join(ASSETS, "player.png")
    if os.path.exists(pp):
        pl = Image.open(pp).convert("RGBA").crop((0, 0, 64, 40))
        px_, fy = R["player"]
        img.alpha_composite(pl, (px_ * 16 + 8 - 28, fy * 16 - 40))
    img.alpha_composite(front)
    # fake poison water (the engine draws its own) so the terrain contrast can be judged
    wat = blank(Wp, Hp)
    wd = ImageDraw.Draw(wat)
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch == "~":
                top = y * 16 + (4 if y > 0 and fg[y - 1][x] != "~" else 0)
                wd.rectangle([x * 16, top, x * 16 + 15, y * 16 + 15], fill=(52, 92, 50, 170))
                if top != y * 16:
                    wd.line([x * 16, top, x * 16 + 15, top], fill=(150, 200, 110, 220))
    img.alpha_composite(wat)
    scale(img, 3).save(os.path.join(PREV, f"room_{biome}.png"))
    return img


# --------------------------------------------------------------------------- previews
def env_preview_img(biome, tiles, far, mid):
    """Tileset strip + far + mid over magenta + composite + a wrap-seam strip (tiled twice)."""
    strip = blank(16 * 48, 16)
    for i, t in enumerate(tiles):
        strip.alpha_composite(t, (i * 16, 0))
    strip = scale(strip, 2)
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255))
    m.alpha_composite(mid)
    comp = far.copy()
    comp.alpha_composite(mid)
    wrap = Image.new("RGBA", (512, 216))
    wrap.alpha_composite(comp.crop((256, 0, 512, 216)), (0, 0))      # 256..512 | 0..256: seam in the middle
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
    out.save(os.path.join(PREV, f"env_{biome}.png"))


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
    sheet.save(os.path.join(PREV, "props2.png"))


PROPS_CACHE = {}


def main():
    ase = "--no-ase" not in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    report = []
    PROPS_CACHE.update({n: f() for n, f in env2_props.PROPS.items()})
    for biome in BIOMES:
        if only and biome not in only and "props" not in only:
            continue
        tiles = env2_tiles.build_tileset(biome)
        far_fn, mid_fn = env2_bg.BUILDERS[biome]
        far, mid = far_fn(), mid_fn()
        assert far.getextrema()[3][0] == 255, "far layer must be opaque"
        assert all(a in (0, 255) for a in set(mid.getdata(3))), "mid layer must be pixel-clean"
        env_preview.tileset_sheet(biome, tiles)
        env_preview.seam_test(biome, tiles)
        env_preview_img(biome, tiles, far, mid)
        render_room(biome, tiles, far, mid, PROPS_CACHE)
        if ase:
            build_tiles(biome, tiles, True)
            build_bg(f"bg_{biome}_far", far, True)
            build_bg(f"bg_{biome}_mid", mid, True)
            report.append(verify(f"tiles_{biome}", 48, [("all", 0, 47)], (16, 16)))
            report.append(verify(f"bg_{biome}_far", 1, [("loop", 0, 0)], (512, 216)))
            report.append(verify(f"bg_{biome}_mid", 1, [("loop", 0, 0)], (512, 216)))
        print("built", biome)
    for name, (w, h, layers, frames, tags) in PROPS_CACHE.items():
        for f in frames:
            for c in f["cels"].values():
                assert all(a in (0, 255) for a in set(c.getdata(3))), name + " not pixel-clean"
        if ase:
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
    props_sheet(list(PROPS_CACHE.items()))
    if ase:
        for r in report:
            print("  ", r)
        print("json tags verified:", len(report), "sheets")


if __name__ == "__main__":
    main()
