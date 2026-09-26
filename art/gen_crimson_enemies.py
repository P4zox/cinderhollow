#!/usr/bin/env python3
"""Enemies of the Crimson Manor (agent C) -- same contract as ART_SPEC section 4 (meta required).

    python3 art/gen_crimson_enemies.py                     build all three (Aseprite) + meta + previews
    python3 art/gen_crimson_enemies.py --preview           previews + meta only (no Aseprite)
    python3 art/gen_crimson_enemies.py --only cm_hound [--preview]

    cm_servant   64x48  anchor [28,48]  gaunt vampire manservant, black tailcoat livery, crimson waistcoat, white
                        gloves, a carving knife in each hand.  idle(4) walk(6) slash(9) lunge(10) emerge(6) hurt(2)
                        death(6)                                           -> art/crimson_enemy_servant.py
    cm_hound     64x40  anchor [30,40]  lean skeletal blood hound, black-crimson hide, iron collar + broken chain.
                        idle(4) run(6) bite(8) hurt(2) death(6)            -> art/crimson_enemy_hound.py
    cm_gargoyle  48x40  FLYING, anchor = body centre [24,22]  black-stone bat gargoyle with crimson membranes.
                        perch(2) wake(4) fly(6) dive(6) hurt(2) death(6)   -> art/crimson_enemy_gargoyle.py

All face RIGHT.  Outputs per enemy: art/<name>.aseprite, assets/<name>.png/.json, assets/<name>_meta.json,
art/previews/<name>.png (4x, one row per tag), <name>_hitbox.png, <name>_closeup.png.
"""
import os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import crimson_kit as CK  # noqa: E402
import enemy_kit as K  # noqa: E402
from PIL import Image  # noqa: E402

BUILD = "--preview" not in sys.argv
PV = os.path.join(ART, "previews")


def render(mod, sway_key="C"):
    mod.setup()
    kw = getattr(mod, "RUN_KW", {})
    out, infos, tags = CK.run_anims(mod.LAYERS, mod.draw_fn, mod.TAGDEFS, mod.COUNTS, loops=mod.LOOPS,
                                    sway_key=kw.get("sway_key", sway_key))
    flats = [K.flatten(imgs, mod.LAYERS) for _, imgs in out[1]]
    return out[1], infos, tags, flats


def export(name, mod, frames, infos, tags, flats, meta, close_idx=(0,)):
    CK.edge_check(name, tags, flats, allow_top=getattr(mod, "ALLOW_TOP", ()))
    CK.preview_rows(os.path.join(PV, f"{name}.png"), tags, flats, scale=4)
    CK.closeup(os.path.join(PV, f"{name}_closeup.png"), flats, list(close_idx), scale=8)
    CK.hitbox_preview(os.path.join(PV, f"{name}_hitbox.png"), tags, flats, meta, scale=4)
    CK.write_meta(name, meta)
    for t, d in meta.get("attacks", {}).items():
        for w in d.get("windows", [d]):
            print(" ", name, "attack", t, w["active"], w["hit"])
    print(" ", name, "hurtbox", meta["hurtbox"], "telegraph", meta.get("telegraph"), "spawn", meta.get("spawn"))
    if BUILD:
        asebuild.build(name, K.W, K.H, mod.LAYERS, [{"ms": ms, "cels": imgs} for ms, imgs in frames], tags)
        print("  built", name)


def widen(att, x0):
    """Extend an attack's rects back to x0 (the body/arms carried by a lunge are part of the hit)."""
    for r in list(att["rects"].values()) + [att["hit"]]:
        if r[0] > x0:
            r[2] += r[0] - x0
            r[0] = x0
    return att


# =========================================================================== cm_servant
def build_servant():
    import crimson_enemy_servant as S
    frames, infos, tags, flats = render(S)
    idle = infos["idle"][0]
    tb = CK.bbox(idle["torso"] | idle["head"])
    A = CK.attack_rect
    meta = {
        "native": 1,
        "frame": [S.W, S.H],
        "anchor": [S.AX, S.H],
        "hurtbox": [tb[0], tb[1], tb[2], S.H - tb[1]],
        "attacks": {
            "slash": {"windows": [A(infos, "slash", 4, 4, x_min=S.AX, key="hitF"),
                                  A(infos, "slash", 6, 6, x_min=S.AX, key="hitB")]},
            "lunge": widen(A(infos, "lunge", 5, 6, x_min=S.AX + 2), S.AX + 8),
        },
        "telegraph": {
            "lunge": {"frame": 3, "at": CK.pt(infos["lunge"][3]["eye"])},
            "slash": {"frame": 2, "at": CK.pt(infos["slash"][2]["glint"])},
        },
        "notes": "Faces right, anchor = feet. slash: crouch windup (hold f2), two quick slashes, front knife f4 then "
                 "back knife f6. lunge: coils f0-3 (telegraph f3: eye flare + bared fangs), launches f4, airborne "
                 "knife-first f5-6 (drawn in place ~4px above the floor; the engine carries it forward ~40-60px over "
                 "f4-f6), lands f7. emerge: f0 only the legs show at the top of the frame (dropping out of a portrait "
                 "hung above), f1 falling, f2 lands in a crouch (dust), f3 hold, f4-5 rise; spawn it with its anchor "
                 "on the floor under the portrait. walk: planted foot travels 3px per 110ms frame (~27 px/s). "
                 "death: crumbles into ash and a blood pool; last frame is only the pool.",
    }
    export("cm_servant", S, frames, infos, tags, flats, meta, close_idx=(0, tags[2][1] + 4))


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, fn in (("cm_servant", build_servant), ("cm_hound", build_hound), ("cm_gargoyle", build_gargoyle)):
        if only and name not in only:
            continue
        print(name)
        fn()


def build_hound():
    import crimson_enemy_hound as Hn
    frames, infos, tags, flats = render(Hn, sway_key="S")
    meta = Hn.meta(infos, tags, frames)
    export("cm_hound", Hn, frames, infos, tags, flats, meta, close_idx=(0, tags[2][1] + 4))


def build_gargoyle():
    import crimson_enemy_gargoyle as Gg
    frames, infos, tags, flats = render(Gg, sway_key="O")
    meta = Gg.meta(infos, tags, frames)
    export("cm_gargoyle", Gg, frames, infos, tags, flats, meta, close_idx=(0, tags[2][1]))


if __name__ == "__main__":
    main()
