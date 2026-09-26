#!/usr/bin/env python3
"""Environment art for THE CRIMSON MANOR (agent C): a vampiric noble estate hidden underground.

Builds (all through art/asebuild.py -> art/<name>.aseprite + assets/<name>.png/.json):
  tiles_crimson   48 x 16x16, tag `all`, standard index layout (ART_SPEC section 6)          crimson_env_tiles.py
  bg_crimson_far  512x216 opaque, tileable, tag `loop` (4 frames of blood rain)             crimson_env_bg.py
  bg_crimson_mid  512x216 transparent, tileable, tag `loop` (1 frame)                        crimson_env_bg.py
  cm_interior     64x128: paper / wainscot / window / pilaster (1 frame each)               crimson_env_bg.py
  cm_candelabra cm_chandelier cm_sconce cm_lectern cm_table cm_barrel cm_winerack cm_coffin cm_carriage
                                                                                            crimson_env_props.py
  cm_portrait cm_bloodveil cm_statue cm_fountain                                            crimson_env_props2.py
Previews -> art/previews/crimson_*.png (tiles, seams, bg, interior, props, portraits, mock rooms).

Usage: python3 art/gen_crimson_env.py [--preview]     (--preview: previews only, skip Aseprite export)
"""
import os, sys, json, math
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                                     # noqa: E402
from envlib import scale, blank, h01                                # noqa: E402
import crimson_env_tiles as CT                                      # noqa: E402
import crimson_env_bg as CB                                         # noqa: E402
import crimson_env_props as CP1                                     # noqa: E402
import crimson_env_props2 as CP2                                    # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = os.path.join(HERE, "previews")
os.makedirs(PREV, exist_ok=True)
GREY = (70, 70, 76, 255)
DARK = (10, 8, 13, 255)


# =========================================================================== helpers
def flatten(w, h, layers, frame):
    img = blank(w, h)
    for L in layers:
        c = frame["cels"].get(L)
        if c is not None:
            img.alpha_composite(c)
    return img


def tag_frames(spec, tag):
    w, h, layers, frames, tags = spec
    a, b = [(t[1], t[2]) for t in tags if t[0] == tag][0]
    return [flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]


def verify(name, n_frames, tags, size):
    with open(os.path.join(ASSETS, f"{name}.json")) as fh:
        d = json.load(fh)
    got = [(t["name"], t["from"], t["to"]) for t in d["meta"]["frameTags"]]
    assert len(d["frames"]) == n_frames, (name, len(d["frames"]), n_frames)
    assert got == [tuple(t) for t in tags], (name, got, tags)
    fr = d["frames"][0]["sourceSize"]
    assert (fr["w"], fr["h"]) == size, (name, fr, size)
    return f"{name}: {size[0]}x{size[1]} x{n_frames}  " + " ".join(f"{t}[{b - a + 1}]" for t, a, b in got)


def is_clean(img, allow=()):
    return all(a in (0, 255) or a in allow for a in set(img.getdata(3)))


# =========================================================================== checks (contract)
def check_all(tiles, far, mid, interior, props):
    for i, t in enumerate(tiles):
        assert is_clean(t), f"tile {i} not pixel-clean"
    for i in range(16):
        assert tiles[i].getchannel("A").getextrema()[0] in (0, 255)
    for i in range(38, 42):
        assert tiles[i].getextrema()[3] == (255, 255), f"bg wall {i} must be opaque"
    for f in far:
        assert f.getextrema()[3][0] == 255, "far layer must be opaque"
    top = mid.crop((0, 0, 512, 60))
    assert top.getextrema()[3][1] == 0, "mid must be transparent in the upper part"
    w, h, layers, frames, tags = interior
    ims = {t: flatten(w, h, layers, frames[a]) for t, a, b in tags}
    assert ims["paper"].getextrema()[3] == (255, 255), "paper must be fully opaque"
    wa = ims["wainscot"].getchannel("A")
    assert wa.crop((0, 80, 64, 128)).getextrema() == (255, 255) and wa.crop((0, 0, 64, 80)).getextrema() == (0, 0)
    glaze = CB.window_glazing()
    ga = ims["window"].getchannel("A").load()
    gm = glaze.load()
    n = 0
    for y in range(128):
        for x in range(64):
            if gm[x, y]:
                assert ga[x, y] == 0, ("window pane not transparent", x, y)
                n += 1
    assert n > 1500, n
    bb = ims["window"].getbbox()
    pa = ims["pilaster"].getbbox()
    assert pa[1] == 0 and pa[3] == 128, pa
    # portraits: the eyes are dark sockets exactly at (13,15) and (18,15)
    for tag in "abcde":
        im = tag_frames(props["cm_portrait"], tag)[0]
        px = im.load()
        for (x, y) in CP2.EYES:
            c = px[x, y]
            assert c[3] == 255 and sum(c[:3]) < 170, (tag, (x, y), c)
            around = [px[x + dx, y + dy] for dx, dy in ((0, 2), (1, 1), (-1, 1))]
            assert max(sum(a[:3]) for a in around) > sum(c[:3]), (tag, "socket not darker than the face")
    # props: pixel-clean, right sizes (the blood veil may use a couple of alpha steps like prop_ashveil)
    for name, (w, h, layers, frames, tags) in props.items():
        for fr in frames:
            im = flatten(w, h, layers, fr)
            assert im.size == (w, h)
            if name != "cm_bloodveil":
                assert is_clean(im), f"{name} not pixel-clean"
    # the blood veil tiles vertically: each frame's top row continues its bottom row
    for im in tag_frames(props["cm_bloodveil"], "loop"):
        a0 = [im.getpixel((x, 0))[3] > 0 for x in range(32)]
        a1 = [im.getpixel((x, 63))[3] > 0 for x in range(32)]
        assert sum(1 for p, q in zip(a0, a1) if p != q) <= 4, "veil rows do not join"


# =========================================================================== previews
def tileset_preview(tiles, k=5):
    cols = 8
    cw = 16 * k + 6
    out = Image.new("RGBA", (cols * cw * 2 + 30, 6 * (16 * k + 18) + 8), (40, 40, 44, 255))
    d = ImageDraw.Draw(out)
    for side, bgc in enumerate((GREY, DARK)):
        ox = side * (cols * cw + 20)
        out.paste(Image.new("RGBA", (cols * cw + 6, 6 * (16 * k + 18) + 4), bgc), (ox + 4, 4))
        for i, t in enumerate(tiles):
            x, y = ox + 8 + (i % cols) * cw, 8 + (i // cols) * (16 * k + 18)
            out.alpha_composite(scale(t, k), (x, y))
            d.text((x, y + 16 * k + 2), str(i), fill=(220, 220, 220, 255))
    out.save(os.path.join(PREV, "crimson_tiles.png"))


def seam_preview(tiles, k=4):
    import random
    rnd = random.Random(3)
    Wt, Ht = 16, 9
    g = [[False] * Wt for _ in range(Ht)]
    for y in range(1, Ht - 1):
        for x in range(1, Wt - 1):
            g[y][x] = rnd.random() < 0.72
    img = Image.new("RGBA", (Wt * 16, Ht * 16), (30, 26, 36, 255))
    for y in range(Ht):
        for x in range(Wt):
            if not g[y][x]:
                continue
            m = (0 if y > 0 and g[y - 1][x] else 1) | (0 if x < Wt - 1 and g[y][x + 1] else 2) | \
                (0 if y < Ht - 1 and g[y + 1][x] else 4) | (0 if x > 0 and g[y][x - 1] else 8)
            img.alpha_composite(tiles[m + (16 if h01(x, y, 1) < 0.3 else 0)], (x * 16, y * 16))
    scale(img, k).save(os.path.join(PREV, "crimson_seams.png"))


def bg_preview(far, mid):
    out = Image.new("RGBA", (1024, 216 * 4 + 30), (40, 40, 44, 255))
    out.alpha_composite(far[0], (0, 0)); out.alpha_composite(far[0], (512, 0))      # tiled x2: seam check
    out.alpha_composite(far[2].crop((0, 0, 512, 216)), (0, 226))
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255)); m.alpha_composite(mid)
    out.alpha_composite(m, (512, 226))
    for i in range(2):
        c = far[1].copy(); c.alpha_composite(mid)
        out.alpha_composite(c, (i * 512, 452))
    # the mid layer tiled over itself (offset) on dark: seam check
    t = Image.new("RGBA", (1024, 216), DARK)
    t.alpha_composite(mid, (0, 0)); t.alpha_composite(mid, (512, 0))
    out.alpha_composite(t, (0, 678))
    out.save(os.path.join(PREV, "crimson_bg.png"))
    scale(far[0].crop((200, 30, 456, 216)), 3).save(os.path.join(PREV, "crimson_bg_moon.png"))


def interior_preview(interior, k=3):
    w, h, layers, frames, tags = interior
    ims = [flatten(w, h, layers, frames[a]) for t, a, b in tags]
    out = Image.new("RGBA", (2 * (4 * (w * k + 8)) + 20, h * k + 16), (40, 40, 44, 255))
    for side, bgc in enumerate((GREY, DARK)):
        ox = side * (4 * (w * k + 8) + 12)
        for i, im in enumerate(ims):
            cell = Image.new("RGBA", (w * k, h * k), bgc)
            cell.alpha_composite(scale(im, k))
            out.alpha_composite(cell, (ox + 8 + i * (w * k + 8), 8))
    out.save(os.path.join(PREV, "crimson_interior.png"))
    # tiling check: paper 2x2 + wainscot row
    t = Image.new("RGBA", (256, 256), DARK)
    for yy in (0, 128):
        for xx in range(0, 256, 64):
            t.alpha_composite(ims[0], (xx, yy))
    for xx in range(0, 256, 64):
        t.alpha_composite(ims[1], (xx, 128))
    scale(t, 3).save(os.path.join(PREV, "crimson_interior_tiling.png"))


def props_preview(props, fname, names, k=4):
    rows = []
    for name in names:
        w, h, layers, frames, tags = props[name]
        for (t, a, b) in tags:
            rows.append((name, t, w, h, [flatten(w, h, layers, frames[i]) for i in range(a, b + 1)]))
    rw = max(len(r[4]) * (r[2] * k + 6) for r in rows) + 170
    rh = sum(r[3] * k + 8 for r in rows) + 8
    for bgc, suf in ((GREY, ""), (DARK, "_dark")):
        sheet = Image.new("RGBA", (rw, rh), bgc)
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
        sheet.save(os.path.join(PREV, f"{fname}{suf}.png"))


def portraits_preview(props, k=6):
    w, h, layers, frames, tags = props["cm_portrait"]
    ims = [flatten(w, h, layers, f) for f in frames]
    cols = 6
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGBA", (cols * (w * k + 8) + 8, rows * (h * k + 8) + 8), DARK)
    for i, im in enumerate(ims):
        out.alpha_composite(scale(im, k), (8 + (i % cols) * (w * k + 8), 8 + (i // cols) * (h * k + 8)))
    # mark the eye points on a copy of the first row so the contract is visible
    d = ImageDraw.Draw(out)
    for i in range(5):
        for (ex, ey) in CP2.EYES:
            x0 = 8 + i * (w * k + 8) + ex * k
            y0 = 8 + ey * k
            d.rectangle([x0 + 1, y0 + 1, x0 + k - 2, y0 + k - 2], outline=(255, 40, 40, 255))
    out.save(os.path.join(PREV, "crimson_portraits.png"))


# =========================================================================== mock rooms
ROOM = [
    "########################",
    "########################",
    "#.....x.......vv......##",
    "#............r.........#",
    "#......................#",
    "#...====..........====.#",
    "#......................#",
    "#......................#",
    "##....................X#",
    "##..k.............b...X#",
    "#########...####...#####",
    "#########^^^####^^^#####",
    "########################",
    "########################",
]


def solid(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X"


def terrain(fg, tiles, front, back):
    for y, row in enumerate(fg):
        for x, ch in enumerate(row):
            if ch in "#X":
                m = (0 if solid(fg, x, y - 1) else 1) | (0 if solid(fg, x + 1, y) else 2) | \
                    (0 if solid(fg, x, y + 1) else 4) | (0 if solid(fg, x - 1, y) else 8)
                idx = 46 if ch == "X" else m + (16 if h01(x + 7, y * 3, 0) < 0.28 else 0)
                front.alpha_composite(tiles[idx], (x * 16, y * 16))
                if m & 1 and ch == "#" and h01(x * 5, y, 1) < 0.3 and y > 0:
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l, r = row[x - 1] == "=", row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else 32 if r else 34 if l else 35], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch in "xrkb":
                back.alpha_composite(tiles[{"x": 42, "r": 43, "k": 44, "b": 45}[ch]], (x * 16, y * 16))


def player_img():
    try:
        pl = Image.open(os.path.join(ASSETS, "player.png")).convert("RGBA").crop((0, 0, 64, 40))
        wp = Image.open(os.path.join(ASSETS, "wpn_longsword.png")).convert("RGBA").crop((0, 0, 64, 40))
        pl.alpha_composite(wp)
        return pl
    except Exception:
        return blank(64, 40)


def light_pass(img, lights, amb=0.5):
    """Crude stand-in for the engine's light pass: dark ambient veil with soft holes + warm additive glow."""
    W_, H_ = img.size
    dark = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    dp = dark.load()
    glow = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    gp = glow.load()
    for y in range(H_):
        for x in range(W_):
            k = 0.0
            g = 0.0
            for (lx, ly, r, s) in lights:
                d = math.hypot(x - lx, y - ly)
                if d < r:
                    k = max(k, (1 - d / r) * s)
                if d < r * 0.6:
                    g += (1 - d / (r * 0.6)) * 0.16 * s
            a = amb * (1 - min(1.0, k))
            dp[x, y] = (4, 3, 8, int(255 * a))
            if g > 0:
                gp[x, y] = (255, 150, 90, int(255 * min(0.35, g)))
    out = img.copy()
    out.alpha_composite(dark)
    out.alpha_composite(glow)
    return out


def room_preview(tiles, far, mid, interior, props):
    W_, H_ = 384, 216
    img = Image.new("RGBA", (W_, H_), (8, 6, 10, 255))
    img.alpha_composite(far[0].crop((150, 0, 534 if 534 <= 512 else 512, 216)), (0, 0))
    img.alpha_composite(far[0].crop((0, 0, 22, 216)), (362, 0))
    img.alpha_composite(mid.crop((60, 0, 444, 216)), (0, 0))
    w, h, layers, frames, tags = interior
    ims = {t: flatten(w, h, layers, frames[a]) for t, a, b in tags}
    glaze = CB.window_glazing()
    back = blank(W_, H_)
    floor = 160
    # paper everywhere (cut under the window glazing), windows, pilasters, wainscot along the floor
    wins = [(64, floor - 48 - 128 + 8 + 30), (192, floor - 48 - 128 + 8 + 30)]
    for yy in range(-96, H_, 128):
        for xx in range(0, W_, 64):
            back.alpha_composite(ims["paper"], (xx, yy))
    for (wx, wy) in wins:
        cut = Image.new("RGBA", (64, 128), (0, 0, 0, 0))
        m = Image.new("L", (W_, H_), 0)
        m.paste(glaze, (wx, wy))
        a = back.getchannel("A")
        a.paste(0, mask=m)
        back.putalpha(a)
        back.alpha_composite(ims["window"], (wx, wy))
    for xx in range(0, W_, 64):
        back.alpha_composite(ims["wainscot"], (xx, floor - 128))
    for px_ in (32, 160, 288):
        back.alpha_composite(ims["pilaster"], (px_ - 32, floor - 128))
    front = blank(W_, H_)
    terrain(ROOM, tiles, front, back)
    img.alpha_composite(back)
    # props
    def put(name, tag, cx, bottom, k=0):
        im = tag_frames(props[name], tag)[k]
        img.alpha_composite(im, (int(cx - im.size[0] / 2), int(bottom - im.size[1])))
    put("cm_portrait", "a", 48, 100)
    put("cm_portrait", "b", 272, 100)
    put("cm_portrait", "tear", 352, 88, 3)
    put("cm_sconce", "loop", 160, 72)
    put("cm_statue", "lady", 56, floor)
    put("cm_candelabra", "loop", 100, floor)
    put("cm_table", "idle", 208, floor)
    put("cm_lectern", "loop", 140, floor)
    put("cm_candelabra", "loop", 312, floor)
    put("cm_coffin", "open", 272, floor)
    # chandelier on a chain from the ceiling (pivot = its top-centre)
    ch = tag_frames(props["cm_chandelier"], "loop")[0]
    cx, top = 192, 64
    for y in range(32, top):
        img.putpixel((cx, y), (0x2d, 0x28, 0x33, 255) if y % 3 else (0x16, 0x13, 0x1a, 255))
    img.alpha_composite(ch, (cx - 32, top))
    # blood veil column on the right in the doorway
    veil = tag_frames(props["cm_bloodveil"], "loop")[0]
    img.alpha_composite(player_img(), (172 - 28, floor - 40))
    img.alpha_composite(front)
    for yb in (floor, floor - 64):
        v = veil.copy()
        v.putalpha(v.getchannel("A").point(lambda a: int(a * 0.9)))
        img.alpha_composite(v, (338 - 16, yb - 64 + 0))
    scale(img, 3).save(os.path.join(PREV, "crimson_room.png"))
    lights = [(100, floor - 38, 70, 1.0), (312, floor - 38, 70, 1.0), (192, top + 20, 90, 1.0), (160, 60, 50, 0.8),
              (208, floor - 30, 50, 0.7), (140, floor - 28, 40, 0.6)]
    scale(light_pass(img, lights, 0.55), 3).save(os.path.join(PREV, "crimson_room_lit.png"))


OUT_ROOM = [
    "........................",
    "........................",
    "........................",
    "........................",
    "..................=====.",
    "........................",
    "........................",
    "######..................",
    "######.......====.......",
    "######..................",
    "######.............#####",
    "#######^^^^#########1###",
    "########################",
    "########################",
]


def outdoor_preview(tiles, far, mid, props):
    W_, H_ = 384, 216
    img = Image.new("RGBA", (W_, H_), (8, 6, 10, 255))
    img.alpha_composite(far[1].crop((128, 0, 512, 216)), (0, 0))
    img.alpha_composite(mid.crop((250, 0, 512, 216)), (0, 0))
    img.alpha_composite(mid.crop((0, 0, 122, 216)), (262, 0))
    fg = [r.replace("1", "#") for r in OUT_ROOM]
    front = blank(W_, H_)
    back = blank(W_, H_)
    terrain(fg, tiles, front, back)
    img.alpha_composite(back)
    def put(name, tag, cx, bottom, k=0):
        im = tag_frames(props[name], tag)[k]
        img.alpha_composite(im, (int(cx - im.size[0] / 2), int(bottom - im.size[1])))
    put("cm_carriage", "idle", 170, 176)
    put("cm_fountain", "loop", 256, 176)
    put("cm_statue", "gargoyle", 330, 160)
    put("cm_barrel", "idle", 74, 112)
    put("cm_winerack", "idle", 30, 112)
    put("cm_coffin", "closed", 356, 64)
    img.alpha_composite(player_img(), (120 - 28, 176 - 40))
    img.alpha_composite(front)
    scale(img, 3).save(os.path.join(PREV, "crimson_room_outdoor.png"))


# =========================================================================== main
def main():
    ase = "--preview" not in sys.argv
    tiles = CT.build_tileset()
    far = CB.build_crimson_far(4)
    mid = CB.build_crimson_mid()
    interior = CB.build_interior()
    props = {}
    for mod in (CP1, CP2):
        for n, fn in mod.PROPS.items():
            props[n] = fn()
    check_all(tiles, far, mid, interior, props)
    tileset_preview(tiles)
    seam_preview(tiles)
    bg_preview(far, mid)
    interior_preview(interior)
    props_preview(props, "crimson_props", ["cm_candelabra", "cm_chandelier", "cm_sconce", "cm_lectern", "cm_table",
                                           "cm_barrel", "cm_winerack", "cm_coffin", "cm_bloodveil", "cm_fountain"])
    props_preview(props, "crimson_props2", ["cm_statue", "cm_carriage", "cm_portrait"], k=4)
    portraits_preview(props)
    room_preview(tiles, far, mid, interior, props)
    outdoor_preview(tiles, far, mid, props)
    if not ase:
        print("previews written (Aseprite export skipped)")
        return
    report = []
    asebuild.build("tiles_crimson", 16, 16, ["Tiles"], [{"ms": 100, "cels": {"Tiles": t}} for t in tiles],
                   [("all", 0, 47)])
    report.append(verify("tiles_crimson", 48, [("all", 0, 47)], (16, 16)))
    asebuild.build("bg_crimson_far", 512, 216, ["Layer"], [{"ms": 160, "cels": {"Layer": f}} for f in far],
                   [("loop", 0, len(far) - 1)])
    report.append(verify("bg_crimson_far", len(far), [("loop", 0, len(far) - 1)], (512, 216)))
    asebuild.build("bg_crimson_mid", 512, 216, ["Layer"], [{"ms": 1000, "cels": {"Layer": mid}}], [("loop", 0, 0)])
    report.append(verify("bg_crimson_mid", 1, [("loop", 0, 0)], (512, 216)))
    w, h, layers, frames, tags = interior
    asebuild.build("cm_interior", w, h, layers, frames, tags)
    report.append(verify("cm_interior", len(frames), tags, (w, h)))
    for name, (w, h, layers, frames, tags) in props.items():
        asebuild.build(name, w, h, layers, frames, tags)
        report.append(verify(name, len(frames), tags, (w, h)))
    for r in report:
        print("  ", r)
    print("built crimson")


if __name__ == "__main__":
    main()
