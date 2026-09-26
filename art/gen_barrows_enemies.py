#!/usr/bin/env python3
"""Enemy generator -- the Drowned Barrows (tombs beneath a sunken cathedral flooded by a black tide).
Same contract as ART_SPEC section 4 (see docs/ART_SPEC.md, docs/EXPANSION2_CONTRACT.md).

    python3 art/gen_barrows_enemies.py                        build everything (Aseprite)
    python3 art/gen_barrows_enemies.py --preview              previews + meta only (no Aseprite)
    python3 art/gen_barrows_enemies.py --only db_eel,fx_db_splash [--preview]

Assets (all face RIGHT):
    db_pilgrim    48x48  drowned pilgrim with a teal-ember censer (feet on the bottom row, anchor [24,48])
    db_eel        72x32  lantern eel, lives underwater (anchor = body centre [36,16])
    db_barnacle   48x32  barnacle crawler, ribcage-shelled crab thing (feet on the bottom row, anchor [24,32])
    fx_db_splash  48x32  black-water splash crown, 6 frames, pivot bottom-centre
Outputs per creature: art/<name>.aseprite, assets/<name>.png/.json, assets/<name>_meta.json,
art/previews/<name>.png (4x, one row per tag) + art/previews/<name>_hitbox.png; art/previews/fx_db_splash.png.
Code: barrows_enemy_kit.py (palette + helpers), barrows_enemy_pilgrim.py, barrows_enemy_eel.py,
barrows_enemy_barnacle.py, barrows_enemy_fx.py.
"""
import json, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import barrows_enemy_kit as B  # noqa: E402  (registers the Barrows ramps first)
import spire_enemy_kit as S  # noqa: E402
import barrows_enemy_pilgrim as pil  # noqa: E402
import barrows_enemy_eel as eel  # noqa: E402
import barrows_enemy_barnacle as bar  # noqa: E402
import barrows_enemy_fx as fx  # noqa: E402

BUILD = "--preview" not in sys.argv

ASSETS = {
    "db_pilgrim": (lambda: pil.build(BUILD), pil.SPEC, True),
    "db_eel": (lambda: eel.build(BUILD), eel.SPEC, True),
    "db_barnacle": (lambda: bar.build(BUILD), bar.SPEC, True),
    "fx_db_splash": (lambda: fx.build_splash(BUILD), {"fx_db_splash": 6}, False),
}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, (fn, spec, has_meta) in ASSETS.items():
        if only and name not in only:
            continue
        res = fn()
        print(name, json.dumps(res) if res else "")
        if BUILD:
            print("  tags", S.verify(name, spec, has_meta))


if __name__ == "__main__":
    main()
