#!/usr/bin/env python3
"""Stormward Spire expansion props (xrc_sp_*) — THE TEMPEST SPIRE: fishers' row, kite lines, the lighthouse and the
Stormwarden. Same palette + hand as art/spire_props.py (ramps imported from spire_tiles / spire_props).

    python3 art/gen_xrc_spire.py              full build (Aseprite) + previews
    python3 art/gen_xrc_spire.py --preview    previews only (no Aseprite)

Sheets (frame size, tags, anchor):
  xrc_sp_hut        80x64   idle 0 | rattle 1-4                 bottom   (roof top = row 0: the walkway plank line)
  xrc_sp_nets       48x48   sway 0-3                            bottom
  xrc_sp_boat       48x20   bob 0-3                             bottom   (keel on rows 18-19)
  xrc_sp_crates     32x24   idle 0                              bottom
  xrc_sp_pipe       16x48   idle 0                              top
  xrc_sp_grate      48x48   idle 0 | warn 1-2 | burst 3-8       center   (gout blasts RIGHT)
  xrc_sp_pennant    16x32   loop 0-5                            bottom
  xrc_sp_kite       48x32   kite0 0-5 | kite1 6-11 | kite2 12-17  center (line leaves the bottom-centre)
  xrc_sp_winch      32x32   idle 0                              bottom
  xrc_sp_bignest    64x32   idle 0                              bottom
  xrc_sp_lantern    96x112  loop 0-3                            bottom
  xrc_sp_railing    48x16   idle 0                              bottom   (tiles horizontally every 48 px)
  xrc_sp_colossus   176x304 idle 0                              bottom   (bottom row = the waterline)
  xrc_sp_seaview    512x216 loop 0                              tileable parallax, horizon y=128
Previews -> art/previews/xrc_sp_preview.png (+ xrc_sp_context.png, xrc_sp_seaview.png)
"""
import os, sys, json
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
PREV = os.path.join(HERE, "previews")
os.makedirs(PREV, exist_ok=True)

import xrc_spire_props as P                                # noqa: E402
import xrc_spire_big as B                                  # noqa: E402
from envlib import scale                                   # noqa: E402

SHEETS = [
    ("xrc_sp_hut", P.hut), ("xrc_sp_nets", P.nets), ("xrc_sp_boat", P.boat), ("xrc_sp_crates", P.crates),
    ("xrc_sp_pipe", P.pipe), ("xrc_sp_grate", P.grate), ("xrc_sp_pennant", P.pennant), ("xrc_sp_kite", P.kite),
    ("xrc_sp_winch", P.winch), ("xrc_sp_bignest", P.bignest), ("xrc_sp_lantern", B.lantern),
    ("xrc_sp_railing", P.railing), ("xrc_sp_colossus", B.colossus), ("xrc_sp_seaview", B.seaview),
]
EXPECT = {
    "xrc_sp_hut": ((80, 64), [("idle", 1), ("rattle", 4)]),
    "xrc_sp_nets": ((48, 48), [("sway", 4)]),
    "xrc_sp_boat": ((48, 20), [("bob", 4)]),
    "xrc_sp_crates": ((32, 24), [("idle", 1)]),
    "xrc_sp_pipe": ((16, 48), [("idle", 1)]),
    "xrc_sp_grate": ((48, 48), [("idle", 1), ("warn", 2), ("burst", 6)]),
    "xrc_sp_pennant": ((16, 32), [("loop", 6)]),
    "xrc_sp_kite": ((48, 32), [("kite0", 6), ("kite1", 6), ("kite2", 6)]),
    "xrc_sp_winch": ((32, 32), [("idle", 1)]),
    "xrc_sp_bignest": ((64, 32), [("idle", 1)]),
    "xrc_sp_lantern": ((96, 112), [("loop", 4)]),
    "xrc_sp_railing": ((48, 16), [("idle", 1)]),
    "xrc_sp_colossus": ((176, 304), [("idle", 1)]),
    "xrc_sp_seaview": ((512, 216), [("loop", 1)]),
}
BG = (18, 22, 34, 255)          # dark storm blue
BG2 = (26, 30, 46, 255)


def flat(w, h, layers, fr):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for l in layers:
        c = fr["cels"].get(l)
        if c is not None:
            im.alpha_composite(c)
    return im


def check(name, built):
    w, h, layers, frames, tags = built
    (ew, eh), et = EXPECT[name]
    assert (w, h) == (ew, eh), (name, w, h)
    assert [(t, b - a + 1) for t, a, b in tags] == et, (name, tags)
    assert tags[-1][2] == len(frames) - 1, name
    for fr in frames:
        for c in fr["cels"].values():
            assert c.size == (w, h), (name, c.size)
            if name != "xrc_sp_seaview":
                assert all(a in (0, 255) for a in set(c.getdata(3))), name + " not pixel-clean"


def verify_json(name, built):
    w, h, layers, frames, tags = built
    d = json.load(open(os.path.join(ASSETS, f"{name}.json")))
    got = [(t["name"], t["from"], t["to"]) for t in d["meta"]["frameTags"]]
    assert got == [(t, a, b) for t, a, b in tags], (name, got)
    assert len(d["frames"]) == len(frames), name
    for fr in d["frames"]:
        assert (fr["frame"]["w"], fr["frame"]["h"]) == (w, h), name
    sheet = Image.open(os.path.join(ASSETS, f"{name}.png"))
    assert sheet.size == (w * len(frames), h), (name, sheet.size)
    return f"{name}: {w}x{h} x{len(frames)} " + " ".join(f"{t}[{a}-{b}]" for t, a, b in got)


def preview(built_all):
    k = 3
    rows = []
    for name, built in built_all:
        if name == "xrc_sp_seaview":
            continue
        w, h, layers, frames, tags = built
        ims = [flat(w, h, layers, f) for f in frames]
        rows.append((name, tags, w, h, ims))
    # pack rows: each sheet on its own line (wrap long sheets)
    maxw = 1900
    out_rows = []
    for (name, tags, w, h, ims) in rows:
        per = max(1, (maxw - 10) // (w * k + 6))
        for i in range(0, len(ims), per):
            out_rows.append((name if i == 0 else "", tags if i == 0 else None, w, h, ims[i:i + per], i))
    H = sum(h * k + 22 for (_, _, w, h, _, _) in out_rows) + 20
    sv = dict(built_all).get("xrc_sp_seaview")
    if sv:
        H += 216 * 2 + 30
    sheet = Image.new("RGBA", (maxw, H), BG)
    d = ImageDraw.Draw(sheet)
    y = 8
    for (name, tags, w, h, ims, i0) in out_rows:
        if name:
            d.text((8, y), name + "  " + " ".join(f"{t}[{a}-{b}]" for t, a, b in tags), fill=(220, 220, 230, 255))
        y += 12
        x = 8
        for j, im in enumerate(ims):
            cell = Image.new("RGBA", (w * k, h * k), BG2 if (i0 + j) % 2 else BG)
            cell.alpha_composite(scale(im, k))
            sheet.alpha_composite(cell, (x, y))
            x += w * k + 6
        y += h * k + 10
    if sv:
        w, h, layers, frames, tags = sv
        im = flat(w, h, layers, frames[0])
        bgf = Image.open(os.path.join(ASSETS, "bg_spire_far.png")).convert("RGBA").crop((0, 0, 512, 216))
        bgf.alpha_composite(im)
        d.text((8, y), "xrc_sp_seaview (2x, over bg_spire_far frame 0)", fill=(220, 220, 230, 255))
        sheet.alpha_composite(scale(bgf, 2), (8, y + 12))
    sheet.save(os.path.join(PREV, "xrc_sp_preview.png"))


def context(built_all):
    """A mock slice of the Spire at 1x (then 3x): props on the causeway floor next to the player for scale."""
    B_ = dict(built_all)
    W, H = 384, 216
    far = Image.open(os.path.join(ASSETS, "bg_spire_far.png")).convert("RGBA").crop((0, 0, 512, 216)).crop((0, 0, W, H))
    img = far.copy()
    sv = B_.get("xrc_sp_seaview")
    if sv:
        img.alpha_composite(flat(*sv[:3], sv[3][0]).crop((0, 0, W, H)))
    col = B_.get("xrc_sp_colossus")
    if col:
        c = flat(*col[:3], col[3][0])
        img.alpha_composite(c, (200, 186 - c.size[1] + 40))      # 1x, waterline below the causeway
    tiles = Image.open(os.path.join(ASSETS, "tiles_spire.png")).convert("RGBA")
    floor = 176
    for x in range(0, W, 16):
        img.alpha_composite(tiles.crop((16, 0, 32, 16)), (x, floor))            # top-exposed ashlar
        img.alpha_composite(tiles.crop((0, 0, 16, 16)), (x, floor + 16))

    def put(name, cx, fy, fi=0, anchor="bottom"):
        b = B_.get(name)
        if not b:
            return
        w, h, layers, frames, tags = b
        im = flat(w, h, layers, frames[fi])
        if anchor == "bottom":
            img.alpha_composite(im, (int(cx - w / 2), fy - h))
        elif anchor == "top":
            img.alpha_composite(im, (int(cx - w / 2), fy))
        else:
            img.alpha_composite(im, (int(cx - w / 2), int(fy - h / 2)))

    x = 0
    for (nm, w_, fi) in (("xrc_sp_hut", 80, 1), (None, 30, 0), ("xrc_sp_nets", 48, 1), ("xrc_sp_crates", 32, 0),
                         ("xrc_sp_winch", 32, 0), ("xrc_sp_bignest", 64, 0), ("xrc_sp_lantern", 96, 1)):
        if nm:
            put(nm, x + w_ / 2, floor, fi)
        else:
            px_player = x + w_ // 2
        x += w_
    put("xrc_sp_pennant", 60, floor - 64, 2)                   # on the hut's roof walk
    put("xrc_sp_kite", 150, 44, 2, "center")
    put("xrc_sp_kite", 214, 70, 9, "center")
    put("xrc_sp_kite", 262, 34, 15, "center")
    put("xrc_sp_pipe", 300, 0, 0, "top")
    pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
    img.alpha_composite(pl, (px_player - 28, floor - 40))
    # below: a strip of surf with the boat moored in it (sunk 4 px)
    sea = Image.open(os.path.join(ASSETS, "sp_sea.png")).convert("RGBA")
    out = Image.new("RGBA", (W, H + 40), BG)
    out.alpha_composite(img)
    out.alpha_composite(Image.open(os.path.join(ASSETS, "bg_spire_far.png")).convert("RGBA").crop((0, 176, W, 216)),
                        (0, H))
    bt_ = B_.get("xrc_sp_boat")
    if bt_:
        out.alpha_composite(flat(*bt_[:3], bt_[3][1]), (60, H + 8 + 4 - 20))
        out.alpha_composite(flat(*bt_[:3], bt_[3][3]), (250, H + 8 + 4 - 20))
    for x in range(0, W, 16):
        out.alpha_composite(sea.crop((0, 0, 16, 16)), (x, H + 8))
        out.alpha_composite(sea.crop((96, 0, 112, 16)), (x, H + 24))
    scale(out, 3).save(os.path.join(PREV, "xrc_sp_context.png"))


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    ase = "--preview" not in sys.argv
    built_all = []
    for name, fn in SHEETS:
        if only and not any(o in name for o in only):
            continue
        b = fn()
        check(name, b)
        built_all.append((name, b))
    preview(built_all)
    context(built_all)
    if ase:
        import asebuild
        rep = []
        for name, (w, h, layers, frames, tags) in built_all:
            asebuild.build(name, w, h, layers, frames, tags)
            rep.append(verify_json(name, (w, h, layers, frames, tags)))
        for r in rep:
            print("  ", r)
    print("ok", [n for n, _ in built_all])


if __name__ == "__main__":
    main()
