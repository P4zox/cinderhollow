#!/usr/bin/env python3
"""THE PALE CROWN - extra region props (xrc_cr_*).

    python3 art/gen_xrc_crown.py              full build (Aseprite) + preview
    python3 art/gen_xrc_crown.py --preview    preview only (no Aseprite)

Sheets (frame size, tags, anchor):
  xrc_cr_sapvein     16x64   loop(6)   top     glowing sap vein in living pale bark (wall decoration)
  xrc_cr_rootknot    48x32   idle(1)   bottom  gnarled pale root knot, white flowers, gilded ring
  xrc_cr_portrait    32x40   idle(1)   center  bark-grown gothic frame, a pale knight of the court
  xrc_cr_brazier     16x40   loop(6)   bottom  slender thorned-bronze brazier, pale white-gold flame
  xrc_cr_blossom     32x24   loop(4)   bottom  pale Root blossoms on a low twig, swaying, petals fall
  xrc_cr_heartbloom  176x176 loop(6)   bottom  THE HEARTBLOOM landmark (core centre (88, 66))
  xrc_cr_panorama    512x216 idle(1)   tileable parallax layer for the Crown Overlook vista

Helpers: xrc_crown_lib.py (raster/shading), xrc_crown_props.py (small props),
xrc_crown_bloom.py (Heartbloom), xrc_crown_pano.py (panorama).
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREV = os.path.join(HERE, "previews")
PREVIEW_ONLY = "--preview" in sys.argv[1:]

import xrc_crown_props as P
import xrc_crown_bloom as B
import xrc_crown_pano as V

SHEETS = [
    ("xrc_cr_sapvein", P.sapvein),
    ("xrc_cr_rootknot", P.rootknot),
    ("xrc_cr_portrait", P.portrait),
    ("xrc_cr_brazier", P.brazier),
    ("xrc_cr_blossom", P.blossom),
    ("xrc_cr_heartbloom", B.heartbloom),
    ("xrc_cr_panorama", V.panorama),
]
EXPECT = {
    "xrc_cr_sapvein": (16, 64, [("loop", 0, 5)]),
    "xrc_cr_rootknot": (48, 32, [("idle", 0, 0)]),
    "xrc_cr_portrait": (32, 40, [("idle", 0, 0)]),
    "xrc_cr_brazier": (16, 40, [("loop", 0, 5)]),
    "xrc_cr_blossom": (32, 24, [("loop", 0, 3)]),
    "xrc_cr_heartbloom": (176, 176, [("loop", 0, 5)]),
    "xrc_cr_panorama": (512, 216, [("idle", 0, 0)]),
}

PALE_BG = (190, 200, 214, 255)
DARK_BG = (22, 19, 27, 255)


def frame_imgs(built):
    w, h, layers, frames, tags = built
    out = []
    for f in frames:
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for ly in layers:
            if ly in f["cels"]:
                im.alpha_composite(f["cels"][ly])
        out.append(im)
    return out


def sheet_frame(name, i):
    """read frame i back from the exported assets/<name>.png (what the game will load)"""
    im = Image.open(os.path.join(ASSETS, name + ".png")).convert("RGBA")
    w, h, _ = EXPECT[name]
    return im.crop((i * w, 0, i * w + w, h))


def load_asset_frame(name, i=0):
    im = Image.open(os.path.join(ASSETS, name + ".png")).convert("RGBA")
    j = json.load(open(os.path.join(ASSETS, name + ".json")))
    fr = j["frames"][i]["frame"]
    return im.crop((fr["x"], fr["y"], fr["x"] + fr["w"], fr["y"] + fr["h"]))


def up(im, k):
    return im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST)


def context_scene(frames):
    """384x216 game-resolution mock of a Great Boughs room: far + mid bg, crown tiles, the props."""
    sc = Image.new("RGBA", (384, 216), (0, 0, 0, 255))
    far = Image.open(os.path.join(ASSETS, "bg_crown_far.png")).convert("RGBA")
    mid = Image.open(os.path.join(ASSETS, "bg_crown_mid.png")).convert("RGBA")
    sc.alpha_composite(far.crop((40, 0, 424, 216)))
    sc.alpha_composite(mid.crop((100, 0, 484, 216)))
    tiles = Image.open(os.path.join(ASSETS, "tiles_crown.png")).convert("RGBA")
    T = lambda i: tiles.crop((i * 16, 0, i * 16 + 16, 16))
    FLOOR = 184
    # background wall panel behind the portrait / vein, a left pillar and a ceiling ledge
    for ty in range(0, FLOOR, 16):
        for tx in range(16, 112, 16):
            sc.alpha_composite(T(38 + ((tx // 16 + ty // 16) % 2)), (tx, ty))
    for ty in range(0, 216, 16):
        sc.alpha_composite(T(2 if ty < FLOOR else 0), (0, ty))
    for tx in range(16, 112, 16):
        sc.alpha_composite(T(4), (tx, 0))
    for tx in range(0, 384, 16):
        sc.alpha_composite(T(1 if tx else 0), (tx, FLOOR))
        sc.alpha_composite(T(0), (tx, FLOOR + 16))

    def put(name, fi, x, anchor, y=FLOOR):
        im = frames[name][fi]
        w, h = im.size
        if anchor == "bottom":
            sc.alpha_composite(im, (int(x - w // 2), y - h))
        elif anchor == "top":
            sc.alpha_composite(im, (int(x - w // 2), y))
        else:
            sc.alpha_composite(im, (int(x - w // 2), int(y - h // 2)))

    put("xrc_cr_sapvein", 2, 34, "top", 16)
    put("xrc_cr_portrait", 0, 68, "center", 96)
    put("xrc_cr_sapvein", 4, 98, "top", 16)
    put("xrc_cr_brazier", 1, 128, "bottom")
    put("xrc_cr_rootknot", 0, 40, "bottom")
    player = load_asset_frame("player", 0)
    sc.alpha_composite(player, (150 - 32, FLOOR - 40))
    put("xrc_cr_blossom", 1, 196, "bottom")
    put("xrc_cr_heartbloom", 0, 292, "bottom")
    put("xrc_cr_brazier", 3, 372, "bottom")
    return sc


def preview(frames):
    K = 3
    font = None
    label_h = 14
    blocks = []
    for name, _ in SHEETS:
        if name == "xrc_cr_panorama":
            continue
        imgs = frames[name]
        w, h = imgs[0].size
        row_w = len(imgs) * (w * K + 6)
        bh = label_h + 2 * (h * K + 6)
        b = Image.new("RGBA", (row_w, bh), (60, 60, 70, 255))
        d = ImageDraw.Draw(b)
        d.text((2, 1), f"{name}  {w}x{h}  x{len(imgs)}", fill=(240, 240, 240, 255))
        for r, bg in enumerate((PALE_BG, DARK_BG)):
            for i, im in enumerate(imgs):
                cell = Image.new("RGBA", (w, h), bg)
                cell.alpha_composite(im)
                b.paste(up(cell, K), (i * (w * K + 6), label_h + r * (h * K + 6)))
        blocks.append(b)
    # panorama at 2x over bg_crown_far
    far = Image.open(os.path.join(ASSETS, "bg_crown_far.png")).convert("RGBA")
    pano = far.copy()
    pano.alpha_composite(frames["xrc_cr_panorama"][0])
    pb = Image.new("RGBA", (1024, 432 + label_h), (60, 60, 70, 255))
    ImageDraw.Draw(pb).text((2, 1), "xrc_cr_panorama 512x216 over bg_crown_far (2x)", fill=(240, 240, 240, 255))
    pb.paste(up(pano, 2), (0, label_h))
    blocks.append(pb)
    # tiling check: two copies side by side, 1x
    tb = Image.new("RGBA", (1024, 216 + label_h), (60, 60, 70, 255))
    ImageDraw.Draw(tb).text((2, 1), "panorama tiled twice (1x, seam at x=512)", fill=(240, 240, 240, 255))
    tb.paste(frames["xrc_cr_panorama"][0], (0, label_h))
    tb.paste(frames["xrc_cr_panorama"][0], (512, label_h))
    blocks.append(tb)
    # in context at game resolution (2x)
    sc = context_scene(frames)
    cb = Image.new("RGBA", (768, 432 + label_h), (60, 60, 70, 255))
    ImageDraw.Draw(cb).text((2, 1), "in context (384x216 room at 2x, player for scale)", fill=(240, 240, 240, 255))
    cb.paste(up(sc, 2), (0, label_h))
    blocks.append(cb)
    W = max(b.size[0] for b in blocks)
    H = sum(b.size[1] + 8 for b in blocks)
    out = Image.new("RGBA", (W, H), (40, 40, 48, 255))
    y = 0
    for b in blocks:
        out.paste(b, (0, y))
        y += b.size[1] + 8
    os.makedirs(PREV, exist_ok=True)
    path = os.path.join(PREV, "xrc_cr_preview.png")
    out.save(path)
    up(sc, 1).save(os.path.join(PREV, "xrc_cr_context.png"))
    return path


def check_json(name):
    j = json.load(open(os.path.join(ASSETS, name + ".json")))
    w, h, tags = EXPECT[name]
    got = [(t["name"], t["from"], t["to"]) for t in j["meta"]["frameTags"]]
    fr = j["frames"]
    assert got == tags, (name, got)
    assert all(f["frame"]["w"] == w and f["frame"]["h"] == h for f in fr), name
    assert len(fr) == tags[-1][2] + 1, (name, len(fr))
    return got


def main():
    frames = {}
    for name, fn in SHEETS:
        built = fn()
        w, h, layers, fr, tags = built
        ew, eh, etags = EXPECT[name]
        assert (w, h) == (ew, eh) and list(tags) == etags, (name, w, h, tags)
        frames[name] = frame_imgs(built)
        if not PREVIEW_ONLY:
            import asebuild
            asebuild.build(name, w, h, layers, fr, tags)
            print(name, "tags", check_json(name))
    if not PREVIEW_ONLY:        # preview from the exported sheets = exactly what ships
        frames = {n: [sheet_frame(n, i) for i in range(len(frames[n]))] for n, _ in SHEETS}
    print("preview:", preview(frames))


if __name__ == "__main__":
    main()
