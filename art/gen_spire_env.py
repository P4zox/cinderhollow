#!/usr/bin/env python3
"""Environment art for the `spire` biome — THE TEMPEST SPIRE (docs/ART_SPEC.md section 6 contract).

Builds:
  tiles_spire    48 frames of 16x16, tag `all`, standard index layout                    (spire_tiles.py)
  bg_spire_far   512x216 opaque, tileable, 10 frames: loop 0-3, flash 4-6, flash2 7-9       (spire_bg.py)
  bg_spire_mid   512x216 transparent, tileable, 4 frames: loop 0-3                          (spire_bg.py)
  sp_windmill sp_cottage sp_fence sp_lamp sp_wheat sp_bridge sp_sea sp_debris sp_window    (spire_props.py)
Previews -> art/previews/: tiles_spire.png, seams_spire.png, env_spire.png (far: every frame, mid: every frame,
composite + wrap seam), room_spire.png (+ room_spire_flash.png: the same room on flash frame 4),
props_spire.png.

Usage: python3 art/gen_spire_env.py [--no-ase]   (--no-ase: previews only, skip Aseprite export)
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                        # noqa: E402
import env_preview                                     # noqa: E402
import spire_tiles, spire_bg, spire_props              # noqa: E402
from envlib import scale, blank, h01                   # noqa: E402
from gen_env import verify                             # noqa: E402  (read-only reuse)

BIOME = "spire"
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
PREV = env_preview.PREV

FAR_MS = [130, 130, 130, 130, 60, 90, 150, 70, 100, 150]
FAR_TAGS = [("loop", 0, 3), ("flash", 4, 6), ("flash2", 7, 9)]
MID_MS = 150

# --------------------------------------------------------------------------- mock room (outdoor causeway)
# '#' solid  'X' breakable  '=' one-way  '^' floor spikes  'v' ceiling spikes  'b' sp_bridge span
# '~' sp_sea (surface on the top '~' row, deep below)   'C' chain(42)  'B' banner(43)  'L' lantern(44)
# 'o' bones(45)  't' tuft(47)   'w' background wall (38-40)  'p' pilaster(41)
ROOM = dict(
    fg=[
        "........................",
        "........................",
        "...............#########",
        "...............#########",
        "................vvC....B",
        "..................C.....",
        "..........====.........#",
        "........................",
        "........................",
        "..t.....o.........L...tX",
        "##########bbbbbb####^^##",
        "##########......########",
        "##########~~~~~~########",
        "##########~~~~~~########",
    ],
    bg=[
        "........................",
        "........................",
        "........................",
        "........................",
        "................pww...wp",
        "................pww...wp",
        "................pww...wp",
        "................pww...wp",
        "................pww...wp",
        "................pww...wp",
        "........................",
        "........................",
        "........................",
        "........................",
    ],
    # (name, tag, frame, centre x px, floor row) — drawn in this order behind the player
    props=[("sp_windmill", "loop", 0, 44, 10), ("sp_cottage", "idle", 0, 114, 10),
           ("sp_window", "idle", 0, 328, 10), ("sp_fence", "idle", 0, 22, 10), ("sp_lamp", "loop", 1, 280, 10)],
    front=[("sp_wheat", "loop", 0, 92, 10), ("sp_wheat", "loop", 3, 358, 10)],
    player=(12, 10),
)


def solid_at(fg, x, y):
    if y < 0 or y >= len(fg) or x < 0 or x >= len(fg[0]):
        return True
    return fg[y][x] in "#X"


def prop_frame(props, name, tag, k):
    w, h, layers, frames, tags = props[name]
    a = [t for t in tags if t[0] == tag][0][1]
    return env_preview.flatten(w, h, layers, frames[a + k])


def sheet_frame(name, i=0):
    p = os.path.join(ASSETS, f"{name}.png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    return im.crop((i * 64, 0, i * 64 + 64, 40))


def render_room(tiles, far, mid, props, out_name, camx=0, seaf=0):
    fg = ROOM["fg"]
    Wp, Hp = 384, 216
    img = Image.new("RGBA", (Wp, Hp), (20, 20, 26, 255))
    for layer, fac in ((far, 0.08), (mid, 0.3)):
        ox = -int(camx * fac) % 512
        img.alpha_composite(layer, (ox - 512, 0))
        img.alpha_composite(layer, (ox, 0))
    for y, row in enumerate(ROOM["bg"]):
        for x, ch in enumerate(row):
            if ch in "wp" and not solid_at(fg, x, y):
                r = h01(x, y, 9)
                k = 41 if ch == "p" else (38 if r < 0.6 else (39 if r < 0.8 else 40))
                img.alpha_composite(tiles[k], (x * 16, y * 16))
    for (name, tag, k, cx, floor) in ROOM["props"]:
        im = prop_frame(props, name, tag, k)
        img.alpha_composite(im, (int(cx - im.size[0] / 2), floor * 16 - im.size[1]))
    front = blank(Wp, Hp)
    seatop = min(y for y, row in enumerate(fg) if "~" in row)
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
                if m & 1 and h01(x * 5, y, 1) < 0.35 and y > 0 and fg[y - 1][x] == ".":
                    front.alpha_composite(tiles[47], (x * 16, y * 16 - 16))
            elif ch == "=":
                l = x > 0 and row[x - 1] == "="
                r = x < len(row) - 1 and row[x + 1] == "="
                front.alpha_composite(tiles[33 if (l and r) else (32 if r else (34 if l else 35))], (x * 16, y * 16))
            elif ch == "^":
                front.alpha_composite(tiles[36], (x * 16, y * 16))
            elif ch == "v":
                front.alpha_composite(tiles[37], (x * 16, y * 16))
            elif ch == "b":
                l = x > 0 and row[x - 1] == "b"
                r = x < len(row) - 1 and row[x + 1] == "b"
                tag = "m" if (l and r) else ("l" if r else ("r" if l else "s"))
                if l and r and x == 13:
                    tag = "crack"
                front.alpha_composite(prop_frame(props, "sp_bridge", tag, 0), (x * 16, y * 16))
            elif ch == "~":
                tag = "surf" if y == seatop else "deep"
                front.alpha_composite(prop_frame(props, "sp_sea", tag, seaf % (6 if tag == "surf" else 4)),
                                      (x * 16, y * 16))
            elif ch in "CBLot":
                img.alpha_composite(tiles[{"C": 42, "B": 43, "L": 44, "o": 45, "t": 47}[ch]], (x * 16, y * 16))
    pl, wp = sheet_frame("player"), sheet_frame("wpn_longsword")
    px_, fy = ROOM["player"]
    for im in (pl, wp):
        if im is not None:
            img.alpha_composite(im, (px_ * 16 + 8 - 28, fy * 16 - 40))
    img.alpha_composite(front)
    for (name, tag, k, cx, floor) in ROOM["front"]:
        im = prop_frame(props, name, tag, k)
        img.alpha_composite(im, (int(cx - im.size[0] / 2), floor * 16 - im.size[1]))
    scale(img, 3).save(os.path.join(PREV, out_name))
    return img


def props_sheet(props, far, k=4):
    """One row per tag; each frame on mid grey, and (for the window) over the storm parallax."""
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
        if name in ("sp_window", "sp_sea"):                 # also over the parallax, as it will be seen
            bgc = far.crop((300, 0, 300 + w * (3 if name == "sp_sea" else 1), h)).copy()
            if name == "sp_sea":
                for i in range(3):
                    bgc.alpha_composite(ims[0], (i * w, 0))
            else:
                bgc.alpha_composite(ims[0])
            sheet.alpha_composite(scale(bgc, k), (x, y))
        y += h * k + 8
    sheet.save(os.path.join(PREV, f"props_{BIOME}.png"))


def env_preview_img(tiles, fars, mids):
    """Tileset strip; every far frame (labelled); every mid frame over magenta; composite + wrap seam."""
    strip = blank(16 * 48, 16)
    for i, t in enumerate(tiles):
        strip.alpha_composite(t, (i * 16, 0))
    strip = scale(strip, 2)
    Wd = 1024 + 12
    rows_far = (len(fars) + 1) // 2
    Hd = strip.size[1] + 10 + rows_far * 226 + 2 * 226 + 226 + 10
    out = Image.new("RGBA", (Wd, Hd), (70, 70, 76, 255))
    d = ImageDraw.Draw(out)
    out.alpha_composite(strip, (0, 0))
    y0 = strip.size[1] + 10
    names = {0: "loop", 4: "flash", 7: "flash2"}
    for i, im in enumerate(fars):
        x, y = (i % 2) * 524, y0 + (i // 2) * 226
        out.alpha_composite(im, (x, y))
        d.text((x + 4, y + 4), f"far {i} {names.get(i, '')} {FAR_MS[i]}ms", fill=(255, 255, 255, 255))
    y0 += rows_far * 226
    for i, m in enumerate(mids):
        bgm = Image.new("RGBA", (512, 216), (120, 40, 120, 255))
        bgm.alpha_composite(m)
        x, y = (i % 2) * 524, y0 + (i // 2) * 226
        out.alpha_composite(bgm, (x, y))
        d.text((x + 4, y + 4), f"mid {i}", fill=(255, 255, 255, 255))
    y0 += 2 * 226
    comp = fars[0].copy()
    comp.alpha_composite(mids[0])
    wrap = Image.new("RGBA", (512, 216))
    wrap.alpha_composite(comp.crop((256, 0, 512, 216)), (0, 0))
    wrap.alpha_composite(comp.crop((0, 0, 256, 216)), (256, 0))
    out.alpha_composite(comp, (0, y0))
    out.alpha_composite(wrap, (524, y0))
    d.text((528, y0 + 4), "wrap seam at centre", fill=(255, 255, 255, 255))
    out.save(os.path.join(PREV, f"env_{BIOME}.png"))


def clean(img):
    return all(a in (0, 255) for a in set(img.getdata(3)))


def main():
    ase = "--no-ase" not in sys.argv
    report = []
    props = {n: f() for n, f in spire_props.PROPS.items()}
    tiles = spire_tiles.build_tileset()
    for i, t in enumerate(tiles):
        assert clean(t), f"tile {i} not pixel-clean"
    fars = spire_bg.build_spire_far()
    mids = spire_bg.build_spire_mid()
    for f in fars:
        assert f.getextrema()[3][0] == 255, "far layer must be opaque"
    for m in mids:
        assert clean(m), "mid layer must be pixel-clean"
    for name, (w, h, layers, frames, tags) in props.items():
        for f in frames:
            for c in f["cels"].values():
                assert clean(c), name + " not pixel-clean"
    env_preview.tileset_sheet(BIOME, tiles)
    env_preview.seam_test(BIOME, tiles)
    env_preview_img(tiles, fars, mids)
    render_room(tiles, fars[0], mids[0], props, f"room_{BIOME}.png")
    render_room(tiles, fars[4], mids[0], props, f"room_{BIOME}_flash.png", seaf=3)
    props_sheet(list(props.items()), fars[0])
    if ase:
        asebuild.build(f"tiles_{BIOME}", 16, 16, ["Tiles"], [{"ms": 100, "cels": {"Tiles": t}} for t in tiles],
                       [("all", 0, 47)])
        report.append(verify(f"tiles_{BIOME}", 48, [("all", 0, 47)], (16, 16)))
        asebuild.build(f"bg_{BIOME}_far", 512, 216, ["Layer"],
                       [{"ms": FAR_MS[i], "cels": {"Layer": im}} for i, im in enumerate(fars)], FAR_TAGS)
        report.append(verify(f"bg_{BIOME}_far", len(fars), FAR_TAGS, (512, 216)))
        asebuild.build(f"bg_{BIOME}_mid", 512, 216, ["Layer"],
                       [{"ms": MID_MS, "cels": {"Layer": im}} for im in mids], [("loop", 0, len(mids) - 1)])
        report.append(verify(f"bg_{BIOME}_mid", len(mids), [("loop", 0, len(mids) - 1)], (512, 216)))
        for name, (w, h, layers, frames, tags) in props.items():
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
        for r in report:
            print("  ", r)
        print("json tags verified:", len(report), "sheets")
    print("built", BIOME)


if __name__ == "__main__":
    main()
