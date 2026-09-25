#!/usr/bin/env python3
"""Environment art (docs/ART_SPEC.md section 6).

Builds, for each biome (ramparts, catacombs, cathedral):
  tiles_<biome>     48 frames of 16x16, tag `all`             (env_tiles.py)
  bg_<biome>_far    512x216 opaque, tileable, tag `loop`       (env_bg.py)
  bg_<biome>_mid    512x216 transparent, tileable, tag `loop`  (env_bg.py)
and the props prop_shrine, prop_fog, prop_gate, prop_lever, prop_urn, prop_lantern,
prop_remnant, prop_item, prop_chest, prop_elevator (env_props.py).

Previews -> art/previews/: tiles_<biome>.png (4x, indexed), seams_<biome>.png,
env_<biome>.png (tileset + parallax), props.png, room_<biome>.png (384x216 mock room at 3x).

Usage: python3 art/gen_env.py [--no-ase]   (--no-ase: previews only, skip Aseprite export)
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asebuild                                   # noqa: E402
import env_tiles, env_bg, env_props, env_preview  # noqa: E402
from envlib import scale, blank                   # noqa: E402

BIOMES = ["ramparts", "catacombs", "cathedral"]
ASSETS = os.path.join(os.path.dirname(HERE), "assets")


def build_tiles(biome, tiles, ase=True):
    frames = [{"ms": 100, "cels": {"Tiles": t}} for t in tiles]
    if ase:
        asebuild.build(f"tiles_{biome}", 16, 16, ["Tiles"], frames, [("all", 0, 47)])


def build_bg(name, img, ase=True):
    if ase:
        asebuild.build(name, 512, 216, ["Layer"], [{"ms": 1000, "cels": {"Layer": img}}], [("loop", 0, 0)])


def env_preview_img(biome, tiles, far, mid):
    """Tileset strip + far + mid (mid over magenta so the transparency is obvious)."""
    strip = blank(16 * 48, 16)
    for i, t in enumerate(tiles):
        strip.alpha_composite(t, (i * 16, 0))
    strip = scale(strip, 2)
    m = Image.new("RGBA", (512, 216), (120, 40, 120, 255))
    m.alpha_composite(mid)
    comp = far.copy()
    comp.alpha_composite(mid)
    W = max(strip.size[0], 1024)
    out = Image.new("RGBA", (W, strip.size[1] + 216 * 2 + 30), (70, 70, 76, 255))
    out.alpha_composite(strip, (0, 0))
    out.alpha_composite(scale(far, 1), (0, strip.size[1] + 10))
    out.alpha_composite(m, (512, strip.size[1] + 10))
    out.alpha_composite(comp, (0, strip.size[1] + 236))
    out.save(os.path.join(env_preview.PREV, f"env_{biome}.png"))


def room(biome, tiles, far, mid, props):
    sh = props["prop_shrine"]
    lt = props["prop_lantern"]
    shrine_lit = env_preview.flatten(sh[0], sh[1], sh[2], sh[3][7])
    lantern = env_preview.flatten(lt[0], lt[1], lt[2], lt[3][0])
    sc, sr = env_preview.SHRINE_AT
    lc, lr = env_preview.LANTERN_AT
    placed = [(shrine_lit, sc * 16, sr * 16 - 64), (lantern, lc * 16, lr * 16)]
    # the player for scale (read-only use of the existing sheet)
    pp = os.path.join(ASSETS, "player.png")
    if os.path.exists(pp):
        pl = Image.open(pp).convert("RGBA").crop((0, 0, 64, 40))
        placed.append((pl, 15 * 16 + 4 - 28, 10 * 16 - 40))
    img = env_preview.render_room(biome, tiles, far, mid, placed)
    env_preview.save_room(biome, img)


def verify(name, n_frames, tags, size):
    with open(os.path.join(ASSETS, f"{name}.json")) as fh:
        d = json.load(fh)
    got = [(t["name"], t["from"], t["to"]) for t in d["meta"]["frameTags"]]
    assert len(d["frames"]) == n_frames, (name, len(d["frames"]), n_frames)
    assert got == [tuple(t) for t in tags], (name, got, tags)
    fr = d["frames"][0]["sourceSize"]
    assert (fr["w"], fr["h"]) == size, (name, fr, size)
    return got


def main():
    ase = "--no-ase" not in sys.argv
    report = []
    props = {n: f() for n, f in env_props.PROPS.items()}
    for biome in BIOMES:
        tiles = env_tiles.build_tileset(biome)
        far_fn, mid_fn = env_bg.BUILDERS[biome]
        far, mid = far_fn(), mid_fn()
        assert far.getextrema()[3][0] == 255, "far layer must be opaque"
        build_tiles(biome, tiles, ase)
        build_bg(f"bg_{biome}_far", far, ase)
        build_bg(f"bg_{biome}_mid", mid, ase)
        env_preview.tileset_sheet(biome, tiles)
        env_preview.seam_test(biome, tiles)
        env_preview_img(biome, tiles, far, mid)
        room(biome, tiles, far, mid, props)
        if ase:
            report.append(verify(f"tiles_{biome}", 48, [("all", 0, 47)], (16, 16)))
            report.append(verify(f"bg_{biome}_far", 1, [("loop", 0, 0)], (512, 216)))
            report.append(verify(f"bg_{biome}_mid", 1, [("loop", 0, 0)], (512, 216)))
        print("built", biome)
    for name, (w, h, layers, frames, tags) in props.items():
        if ase:
            asebuild.build(name, w, h, layers, frames, tags)
            report.append(verify(name, len(frames), tags, (w, h)))
    env_preview.props_sheet(list(props.items()))
    if ase:
        print("json tags verified:", len(report), "sheets")


if __name__ == "__main__":
    main()
