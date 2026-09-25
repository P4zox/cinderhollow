#!/usr/bin/env python3
"""Enemy generator -- the Tempest Spire (storm-lashed sea-cliff ruin at night). Same contract as ART_SPEC section 4.

    python3 art/gen_spire_enemies.py                        build everything (Aseprite)
    python3 art/gen_spire_enemies.py --preview              previews + meta only (no Aseprite)
    python3 art/gen_spire_enemies.py --only sp_crow,fx_sp_strike [--preview]

Assets (all face RIGHT; grounded ones stand on the bottom row):
    sp_crow        40x32  storm crow, flies in flocks (floats: anchor = body centre [20,16])
    sp_scarecrow   56x56  scarecrow hollow: hangs on its post until the player is near, rips free, reaps
    sp_post        56x56  the empty wooden cross-post the scarecrow hangs on (engine draws it behind, same anchor)
    sp_acolyte     48x56  lightning acolyte: storm-priest with a copper lightning-rod staff (ranged caster)
    fx_sp_spark    32x32  electric impact burst (centred)
    fx_sp_strike   48x216 lightning strike from the sky (pivot bottom-centre)
Outputs per creature: art/<name>.aseprite, assets/<name>.png/.json, assets/<name>_meta.json,
art/previews/<name>.png (4x, one row per tag) and art/previews/<name>_hitbox.png; FX previews in
art/previews/fx_spire.png. Palette: cold night storm (spire_enemy_kit.py), lightning #1c4fa6 -> #eef9ff.
Code: spire_enemy_crow.py, spire_enemy_scarecrow.py, spire_enemy_acolyte.py, spire_enemy_fx.py.
"""
import json, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import spire_enemy_kit as S  # noqa: E402  (registers the Spire ramps first)
import spire_enemy_crow as crow  # noqa: E402
import spire_enemy_scarecrow as scare  # noqa: E402
import spire_enemy_acolyte as aco  # noqa: E402
import spire_enemy_fx as fx  # noqa: E402

BUILD = "--preview" not in sys.argv

ASSETS = {
    "sp_crow": (lambda: crow.build(BUILD), crow.SPEC, True),
    "sp_post": (lambda: scare.build_post(BUILD), {"idle": 1}, False),
    "sp_scarecrow": (lambda: scare.build(BUILD), scare.SPEC, True),
    "sp_acolyte": (lambda: aco.build(BUILD), aco.SPEC, True),
    "fx_sp_spark": (lambda: fx.build_spark(BUILD), {"sp_spark": 5}, False),
    "fx_sp_strike": (lambda: fx.build_strike(BUILD), {"sp_strike": 8}, False),
}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    fx_done = []
    for name, (fn, spec, has_meta) in ASSETS.items():
        if only and name not in only:
            continue
        res = fn()
        if name.startswith("fx_"):
            fx_done.append(res)
        else:
            print(name, json.dumps(res) if res else "")
        if BUILD:
            print("  tags", S.verify(name, spec, has_meta))
    if fx_done:
        fx.preview(fx_done)
    if not only or "sp_scarecrow" in only or "sp_post" in only:
        scare.post_preview()


if __name__ == "__main__":
    main()
