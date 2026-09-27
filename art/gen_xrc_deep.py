#!/usr/bin/env python3
"""THE BURNING DEEP -- extra props (xrc_dp_*), drawn in the hand of deep_tiles / deep_props.

    python3 art/gen_xrc_deep.py              build every sheet through Aseprite + preview
    python3 art/gen_xrc_deep.py --preview    preview only (no Aseprite)
    python3 art/gen_xrc_deep.py --only gear,cart   limit to some sheets (names without the xrc_dp_ prefix)

Drawing lives in xrc_deep_lib.py (helpers), xrc_deep_a.py and xrc_deep_b.py (props).
Preview -> art/previews/xrc_dp_preview.png
"""
import os, sys, json
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xrc_deep_a as A      # noqa: E402
import xrc_deep_b as B      # noqa: E402
from envlib import scale    # noqa: E402

ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREV = os.path.join(HERE, "previews")

SHEETS = {
    "xrc_dp_gear": A.build_gear,
    "xrc_dp_pipes": A.build_pipes,
    "xrc_dp_cage": A.build_cage,
    "xrc_dp_timbers": A.build_timbers,
    "xrc_dp_ore": A.build_ore,
    "xrc_dp_cart": A.build_cart,
    "xrc_dp_furnace": B.build_furnace,
    "xrc_dp_anvil": A.build_anvil,
    "xrc_dp_seat": B.build_seat,
    "xrc_dp_hoard": B.build_hoard,
    "xrc_dp_vent": B.build_vent,
    "xrc_dp_crucible": B.build_crucible,
    "xrc_dp_reliquary": B.build_reliquary,
    "xrc_dp_glyphs": B.build_glyphs,
}
BG = (16, 11, 10, 255)


def flat(w, h, layers, frame):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for l in layers:
        if l in frame["cels"]:
            im.alpha_composite(frame["cels"][l])
    return im


def check_clean(name, w, h, layers, frames):
    for i, f in enumerate(frames):
        im = flat(w, h, layers, f)
        assert im.size == (w, h)
        al = set(im.getdata(3))
        assert al <= {0, 255}, f"{name} frame {i}: partial alpha {al}"


def preview(built, k=3):
    rows = []
    for name, (w, h, layers, frames, tags) in built.items():
        for (t, a, b) in tags:
            rows.append((name, t, w, h, [flat(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    # pack rows into two columns when they are short
    lab = 150
    items = []
    for (name, t, w, h, ims) in rows:
        rw = lab + len(ims) * (w * k + 6)
        items.append((rw, h * k + 10, name, t, w, ims))
    maxw = 1800
    # simple shelf packing
    shelves, cur, cw, chh = [], [], 0, 0
    for it in items:
        if cw + it[0] > maxw and cur:
            shelves.append((cur, chh)); cur, cw, chh = [], 0, 0
        cur.append(it); cw += it[0] + 20; chh = max(chh, it[1])
    if cur:
        shelves.append((cur, chh))
    ctx = context_strip()
    ctx3 = scale(ctx, 3)
    W = max([maxw, ctx3.size[0]] + [it[0] for it in items]) + 20
    Hh = sum(s[1] for s in shelves) + 20 + ctx3.size[1] + 40
    sheet = Image.new("RGBA", (W, Hh), BG)
    d = ImageDraw.Draw(sheet)
    y = 10
    for shelf, sh in shelves:
        x = 10
        for (rw, rh, name, t, w, ims) in shelf:
            d.text((x, y + 2), name.replace("xrc_dp_", ""), fill=(230, 220, 200, 255))
            d.text((x, y + 14), f"{t} ({len(ims)})", fill=(200, 160, 110, 255))
            xx = x + lab
            for im in ims:
                d.rectangle((xx - 1, y - 1, xx + im.size[0] * k, y + im.size[1] * k), outline=(40, 30, 26, 255))
                sheet.alpha_composite(scale(im, k), (xx, y))
                xx += w * k + 6
            x += rw + 20
        y += sh
    d.text((10, y + 8), "in context (1x game pixels shown at 3x)", fill=(230, 220, 200, 255))
    sheet.alpha_composite(ctx3, (10, y + 24))
    os.makedirs(PREV, exist_ok=True)
    out = os.path.join(PREV, "xrc_dp_preview.png")
    sheet.convert("RGB").save(out)
    return out


def _f0(name, tag=None, k=0):
    w, h, layers, frames, tags = BUILT[name]
    a = 0 if tag is None else [t for t in tags if t[0] == tag][0][1]
    return flat(w, h, layers, frames[a + k])


BUILT = {}


def context_strip():
    """A 448x216 slice of a Deep hall: far/mid backgrounds, a masonry floor, the player and props at 1x."""
    W, H = 640, 216
    img = Image.new("RGBA", (W, H), (20, 10, 8, 255))
    try:
        far = Image.open(os.path.join(ASSETS, "bg_deep_far.png")).convert("RGBA")
        mid = Image.open(os.path.join(ASSETS, "bg_deep_mid.png")).convert("RGBA")
        for ox in range(0, W, 512):
            img.alpha_composite(far, (ox, 0))
            img.alpha_composite(mid, (ox, 0))
        tiles = Image.open(os.path.join(ASSETS, "tiles_deep.png")).convert("RGBA")
        tl = [tiles.crop((i * 16, 0, i * 16 + 16, 16)) for i in range(48)]
    except FileNotFoundError:
        tl = None
    floor = 184
    have = lambda n: n in BUILT

    def put(name, x, anchor="bottom", tag=None, k=0, y=None):
        if not have(name):
            return
        im = _f0(name, tag, k)
        w, h = im.size
        if anchor == "bottom":
            img.alpha_composite(im, (x - w // 2, floor - h))
        elif anchor == "top":
            img.alpha_composite(im, (x - w // 2, y))
        else:
            img.alpha_composite(im, (x - w // 2, y - h // 2))
    # back-wall props first
    put("xrc_dp_gear", 40, "center", y=120)
    put("xrc_dp_timbers", 130)
    put("xrc_dp_furnace", 300)
    put("xrc_dp_glyphs", 190, "center", tag="g0", y=150)
    put("xrc_dp_glyphs", 208, "center", tag="g1", y=150)
    put("xrc_dp_glyphs", 400, "center", tag="g2", y=150)
    put("xrc_dp_glyphs", 418, "center", tag="g3", y=150)
    put("xrc_dp_crucible", 470, "top", tag="pour", y=0)
    put("xrc_dp_cage", 232, "top", y=40)
    put("xrc_dp_pipes", 20)
    put("xrc_dp_seat", 560)
    put("xrc_dp_ore", 90)
    put("xrc_dp_anvil", 440)
    put("xrc_dp_hoard", 610)
    put("xrc_dp_reliquary", 520, tag="open", k=2)
    put("xrc_dp_cart", 170, tag="roll")
    put("xrc_dp_vent", 505, tag="erupt", k=1)
    pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
    img.alpha_composite(pl, (205 - 24, floor - 40))
    if tl:
        for x in range(0, W, 16):
            img.alpha_composite(tl[1], (x, floor))
            img.alpha_composite(tl[0], (x, floor + 16))
    return img


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        only = {"xrc_dp_" + s for s in args[args.index("--only") + 1].split(",")}
    ase = "--preview" not in args
    for name, fn in SHEETS.items():
        if only and name not in only:
            continue
        BUILT[name] = fn()
        w, h, layers, frames, tags = BUILT[name]
        check_clean(name, w, h, layers, frames)
    if ase:
        import asebuild
        for name, (w, h, layers, frames, tags) in BUILT.items():
            asebuild.build(name, w, h, layers, frames, tags)
            d = json.load(open(os.path.join(ASSETS, name + ".json")))
            got = [(t["name"], t["from"], t["to"]) for t in d["meta"]["frameTags"]]
            assert got == [tuple(t) for t in tags], (name, got)
            f0 = d["frames"][0]["frame"]
            assert (f0["w"], f0["h"]) == (w, h) and len(d["frames"]) == len(frames), name
            print(f"  {name:20s} {w}x{h}  frames {len(frames)}  tags {got}")
    print("preview ->", preview(BUILT))


if __name__ == "__main__":
    main()
