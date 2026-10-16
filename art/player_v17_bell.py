"""v17 weapon art for the Warbell: FUNERAL PEAL (art_funeral_peal, weapon dirge_bell) -- docs/v17/bell_art.md.

Same register(G) contract as player_v15_bell.py: return [(tag, fn, opts)], fn() -> [(cels, ms)]. Hooked into gen_player.py
after V16 (the v17 block). The engine (web/src/81_art_bell.js) reads these frame indices:

  0  settle      the bell hanging low in front, weight on the front foot
  1  backswing   swung back low past the heel, the body turning away with it
  2  heave       up over the back shoulder, the body unwinding
  3  CROWN       the bell hung straight up over the helm on the toes, arched back  (the art key held: the charge hold frame)
  4  the drive   brought down through the front, mouth first
  5  IMPACT      driven into the floor, knees deep (meta active = 5: the release frame; the peal rings out from here)
  6  pressed     knelt over the haft, leaning the bell into the floor while the ring rolls away both ways
  7  still       the ring gone past; the weight comes off
  8  rise        the bell lifted off the floor
  (9 settle)     settled() eases the last frame toward the idle hold

The bell carries its own pale-gold smear (the "rings" / "ring" / "flare" fx take the dirge_bell's smear tones).
  python3 art/player_v17_bell.py    # frame / timing check
"""
import math

G = None   # gen_player, set by register()
SPEC = {}
GRIP = 4.0   # two hands on the haft, as the v15 bell
REL = 5      # the release (impact) frame
CROWN = 3    # the charge hold frame (the bell overhead)


def _floor(x, k=0, **kw):   # the bell mouth-down on the floor in front, knees bent over it (as player_v15_bell._floor)
    d = dict(dx=3, dy=5 + k, head_dy=1 + k, hand=(x - 1, 21), ang=58 + 2 * k, footB=(G.OX + 6, 39), footF=(G.FF[0] + 4, 39))
    if "ang" in kw:
        kw["ang"] = 58 + (kw["ang"] - 80) * 0.5
    d.update(kw)
    return d


def art_funeral_peal():
    OX, FF = G.OX, G.FF
    KN = dict(footB=(OX + 4, 39), footF=(FF[0] + 5, 39))   # a wide kneel over the bell
    fr = [
        # 0 settle: the bell low in front, the weight gathering on the front foot
        (dict(dx=1, dy=3, hand=(36, 28), ang=62, footF=(FF[0] + 2, 39), flow=0.4), 80),
        # 1 backswing: dragged back low past the heel, the shoulders turning away with it
        (dict(dx=-1, dy=3, head_dx=-1, hand=(28, 30), ang=168, footB=(OX + 5, 39), footF=(FF[0] + 1, 39), flow=0.5, flutter=1,
              fx=[("dust", 12, 3)]), 120),
        # 2 heave: up over the back shoulder, the body unwinding under it
        (dict(dx=-1, dy=0, head_dx=-1, hand=(28, 19), ang=-172, behind=True, footB=(OX + 6, 38), footF=(FF[0] + 1, 39), flow=0.8, flutter=2,
              fx=[("ring", (29, 22), 12, 170, 215, dict(sq=1.0, w=2.0))]), 90),
        # 3 CROWN: hung straight up over the helm, up on the toes, arched -- the bell at the top of its swing (the charge hold)
        (dict(dx=-1, dy=-1, head_dx=-1, hand=(26, 12), ang=-150, footB=(OX + 7, 37), footF=(FF[0] + 2, 38), flow=0.3, flutter=3,
              fx=[("glint", "tip")]), 130),
        # 4 the drive: brought down through the front, mouth first, the cape torn up behind
        (dict(dx=1, dy=0, hand=(34, 15), ang=-75, footF=(FF[0] + 3, 39), flow=1.3, flutter=4, fx=[G.sw(w=0.4)]), 40),
        # 5 IMPACT: driven into the floor, knees deep; a flare at the lip and the first of the ring opening
        (dict(flow=1.5, flutter=5, fx=[("dust", 44, 14), ("flare", (44, 37), 8), ("rings", (44, 37), (6, 11))],
              **_floor(42, 1, ang=76, **KN)), 70),
        # 6 pressed: knelt over the haft, leaning the bell into the floor while the ring rolls away both ways
        (dict(flow=1.0, flutter=6, fx=[("dust", 44, 6), ("rings", (44, 37), (13, 18))],
              **_floor(42, 1, ang=78, head_dy=2, **KN)), 200),
        # 7 still: the ring gone past, the weight comes off the haft
        (dict(flow=0.6, flutter=7, fx=[("dust", 42, 2)], **_floor(42, 0, ang=76, **KN)), 170),
        # 8 rise: the bell hauled up off the floor
        (dict(dx=1, dy=3, hand=(36, 27), ang=60, footF=(FF[0] + 2, 39), flow=0.4, flutter=8), 130),
        (dict(dx=0, dy=2, hand=(34, 26), ang=42, flow=0.3, flutter=9), 110),
    ]
    return G.mseq(fr, grip=GRIP)


def register(g):
    global G
    G = g
    E = []
    tot = 80 + 120 + 90 + 130 + 40 + 70 + 200 + 170 + 130 + 110
    SPEC["art_funeral_peal"] = (80 + 120 + 90 + 130 + 40, tot)
    E.append(("art_funeral_peal", g.settled_art(art_funeral_peal) if hasattr(g, "settled_art") else art_funeral_peal,
              dict(active=(REL, REL), kinds=("dirge_bell",), both=True)))
    return E


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_player as GP
    mod = sys.modules.get("player_v17_bell")
    fns = dict(GP.ANIMS)
    for t, (w, tot0) in mod.SPEC.items():
        ms = [m for _, m in fns[t]()]
        act = GP.ACTIVE.get(t)
        print(f"{t:18} frames {len(ms):3}  wind {sum(ms[:act[0]]):5}  total {sum(ms):5}  spec {w}/{tot0}  active {act}")
