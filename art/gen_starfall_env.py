#!/usr/bin/env python3
"""Environment art for the Starfall Crater (agent SF).

    python3 art/gen_starfall_env.py [--no-ase]

Builds tiles_starfall (48 x 16x16, tag all), sf_glass (32 x 16x16 star-glass masks, tag all), bg_starfall_far (512x216
opaque), bg_starfall_mid (512x216 transparent) and the props in starfall_props.PROPS (sf_*).
Previews: art/previews/tiles_starfall.png, seams_starfall.png, env_starfall.png, props_starfall.png.
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild  # noqa: E402
import env_preview  # noqa: E402
import starfall_env as SE  # noqa: E402
import starfall_props as SP  # noqa: E402
from envlib import scale, blank  # noqa: E402

PREV = env_preview.PREV


def build_strip(name, tiles, tag="all"):
    frames = [{"ms": 100, "cels": {"Tiles": t}} for t in tiles]
    asebuild.build(name, 16, 16, ["Tiles"], frames, [(tag, 0, len(tiles) - 1)])


def build_prop(name, w, h, anims):
    frames, tags = [], []
    for tag, frs in anims:
        a = len(frames)
        for ms, img in frs:
            assert img.size == (w, h), (name, img.size)
            frames.append({"ms": ms, "cels": {"Layer": img}})
        tags.append((tag, a, len(frames) - 1))
    asebuild.build(name, w, h, ["Layer"], frames, tags)


def main():
    ase = "--no-ase" not in sys.argv
    tiles = SE.build_tileset()
    glass = SE.build_glass()
    for i, t in enumerate(tiles + glass):
        assert all(a in (0, 255) for a in set(t.getdata(3))), f"tile {i} not pixel-clean"
    env_preview.tileset_sheet("starfall", tiles)
    env_preview.tileset_sheet("starfall_glass", glass)
    env_preview.seam_test("starfall", tiles)
    far, mid = SE.far(), SE.mid()
    comp = far.copy(); comp.alpha_composite(mid)
    sheet = Image.new("RGBA", (1024, 216 * 2), (0, 0, 0, 255))
    sheet.paste(comp, (0, 0)); sheet.paste(comp, (512, 0))
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255)); m.alpha_composite(mid)
    sheet.paste(far, (0, 216)); sheet.paste(m, (512, 216))
    scale(sheet, 2).save(os.path.join(PREV, "env_starfall.png"))
    props = {n: (w, h, f()) for n, (w, h, f) in SP.PROPS.items()}
    # props preview: every frame of every tag, 3x
    rows = []
    for n, (w, h, anims) in props.items():
        fr = [img for _, frs in anims for _, img in frs]
        row = Image.new("RGBA", (max(1, len(fr)) * (w + 4), h + 4), (70, 70, 80, 255))
        for i, img in enumerate(fr):
            row.alpha_composite(img, (i * (w + 4) + 2, 2))
        rows.append(row)
    W = max(r.size[0] for r in rows); H = sum(r.size[1] for r in rows)
    pv = Image.new("RGBA", (W, H), (50, 50, 58, 255)); y = 0
    for r in rows:
        pv.paste(r, (0, y)); y += r.size[1]
    scale(pv, 3).save(os.path.join(PREV, "props_starfall.png"))
    if ase:
        build_strip("tiles_starfall", tiles)
        build_strip("sf_glass", glass)
        for n, img in (("bg_starfall_far", far), ("bg_starfall_mid", mid)):
            asebuild.build(n, 512, 216, ["Layer"], [{"ms": 1000, "cels": {"Layer": img}}], [("loop", 0, 0)])
        for n, (w, h, anims) in props.items():
            build_prop(n, w, h, anims)
    print("built starfall env", "(previews only)" if not ase else "")


if __name__ == "__main__":
    main()
