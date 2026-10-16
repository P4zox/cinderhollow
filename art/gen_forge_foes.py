#!/usr/bin/env python3
"""The Cold Forge foes (v17, agent FOES).  All face RIGHT; feet on the frame's floor row.

    python3 art/gen_forge_foes.py                       build everything (Aseprite) + meta + previews
    python3 art/gen_forge_foes.py --only cf_smith,uf:katana
    python3 art/gen_forge_foes.py --preview             previews + meta only (no Aseprite)

cf_unforged_<type>  176x112  anchor [64,106]  the elite, one sheet per weapon type (14):
                    idle(6) walk(8) hurt(3) death(10) atk1 atk2 atk3   (art/forge_foes_unforged*.py)
cf_smith            96x72    anchor [40,68]   Hollow Smith      (art/forge_foes_beasts.py)
cf_wraith           96x72    anchor [44,68]   Quench Wraith
cf_hulk             128x96   anchor [52,92]   Bellows Hulk
cf_mite             24x16    anchor [12,15]   Cinder Mite
Meta (assets/<name>_meta.json): anchor, hurtbox, attacks{tag:{windows:[{active,hit,both?}]}}, telegraph{tag:{at}},
holds{tag:[frame...]}, pts{name:[[x,y] per frame of the sheet]}.
"""
import math, os, sys
from multiprocessing import Pool

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import forge_foes_kit as K  # noqa: E402

BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

UF_TYPES = ["longsword", "katana", "greatsword", "maul", "sns", "dual", "spear", "staff", "whip", "saxe", "bow", "fist",
            "scythe", "bell"]


# ================================================================ shared: frames -> images + meta
def run_frames(frames, drawfn, shoulder_fn, smear_cols=("Q1", "Q2", "Q4", "Q5")):
    """frames: [(ms, pose, flags)].  drawfn(pose) -> (canvas, info).  Adds motion smears / streaks from the previous
    frame's weapon tip, renders.  Returns [(ms, img, info, flags)]."""
    out = []
    prev = None
    for ms, p, fl in frames:
        cv, info = drawfn(p)
        fx = set()
        if prev is not None and (fl.get("sm") or fl.get("st")) and info.get("tip") and prev.get("tip"):
            s = shoulder_fn(p)
            t0, t1 = prev["tip"], info["tip"]
            if fl.get("st"):
                d = K.unit(K.sub(t1, t0))
                for o in (-1.5, 1.5):
                    v = K.mul(K.perp(d), o)
                    fx |= K.streak(cv, K.add(K.sub(t0, K.mul(d, 6)), v), K.add(t1, v), 0.0, cols=smear_cols[:3],
                                   alpha=150)
            else:
                a0 = math.degrees(math.atan2(t0[1] - s[1], t0[0] - s[0]))
                a1 = math.degrees(math.atan2(t1[1] - s[1], t1[0] - s[0]))
                dd = (a1 - a0 + 180) % 360 - 180
                if abs(dd) > 4:
                    r_out = math.hypot(t1[0] - s[0], t1[1] - s[1]) + 1.0
                    r_in = max(4.0, r_out - min(9.0, r_out * 0.32))
                    fx |= K.smear(cv, s, r_in, r_out, a1 - dd * 0.85, a1, cols=smear_cols, alpha=170)
        img = cv.render(ref_y=60, ydark=0.006)
        info["fx"] = fx
        out.append((ms, img, info, fl))
        prev = info
    return out


def root_motion(frames, ax, keys=("hip", "nf", "ff")):
    """Forward travel of the hip becomes root motion: after the furthest point the move never retreats (recoveries
    keep their ground), and every frame is drawn with the hip back over the anchor.  Returns the per-frame offsets."""
    off = [p["hip"][0] - ax for _, p, _ in frames]
    k = max(range(len(off)), key=lambda i: off[i])
    root = []
    for i, (ms, p, fl) in enumerate(frames):
        o = off[i] if i <= k else max(off[i], off[k])
        lift = o - off[i]
        for kk in keys:
            if kk in p and isinstance(p[kk], tuple):
                p[kk] = (p[kk][0] + lift - o, p[kk][1])
        root.append(round(o, 2))
    return root


def build_meta(anchor, hurtbox, tags_frames, pts_names=("tip", "heart", "head")):
    """tags_frames: [(tag, [(ms, img, info, flags)])] -> (anims, meta)."""
    meta = {"native": 1, "anchor": list(anchor), "hurtbox": list(hurtbox), "attacks": {}, "telegraph": {}, "holds": {},
            "pts": {n: [] for n in pts_names}, "root": []}
    anims = []
    for tag, frs in tags_frames:
        anims.append((tag, [(ms, img) for ms, img, _, _ in frs]))
        wins = {}
        for i, (ms, img, info, fl) in enumerate(frs):
            meta["root"].append(fl.get("_root", 0))
            for n in pts_names:
                q = info.get(n)
                meta["pts"][n].append([round(q[0], 1), round(q[1], 1)] if q else None)
            a = fl.get("a")
            if a:
                w = wins.setdefault(a, {"active": [i, i], "hit": None})
                w["active"][1] = i
                pix = set(info.get("hit", set())) | (set(info.get("fx", set())) if fl.get("st") else set())
                if fl.get("body"):
                    pix |= info.get("body", set())
                if fl.get("kick") and info.get("foot"):
                    fx_, fy_ = info["foot"]
                    pix |= {(int(fx_ + dx), int(fy_ + dy)) for dx in range(-3, 8) for dy in range(-6, 2)}
                w["hit"] = K.union(w["hit"], K.bbox_of(pix))
                if fl.get("both"):
                    w["both"] = 1
            if fl.get("hold"):
                runs = meta["holds"].setdefault(tag, [])
                if runs and runs[-1][1] == i - 1 and frs[i - 1][3].get("_key") == fl.get("_key"):
                    runs[-1][1] = i
                else:
                    runs.append([i, i])
            for sk in ("shot", "wave", "hit", "fling"):
                if fl.get(sk) and not (i > 0 and frs[i - 1][3].get(sk)):
                    meta.setdefault("spawn" if sk in ("shot", "wave") else sk, {}).setdefault(tag, []).append(i)
        if wins:
            ws = [wins[k] for k in sorted(wins)]
            for w in ws:
                if w["hit"] is None:
                    w["hit"] = [anchor[0], anchor[1] - 40, 30, 40]
            meta["attacks"][tag] = {"windows": ws}
            f0 = ws[0]["active"][0]
            tip = frs[max(0, f0 - 1)][2].get("tip")
            if tip:
                meta["telegraph"][tag] = {"at": [round(tip[0]), round(tip[1])], "frame": max(0, f0 - 1)}
    return anims, meta


# ================================================================ the Unforged
def build_unforged(wt):
    import forge_foes_unforged as U
    import forge_foes_unforged_moves as M
    drawfn = lambda p: U.draw(p, wt)
    shoulder = lambda p: U.shoulder_pts(p)[0]
    cols = ("Q1", "Q2", "Q4", "Q5")
    if wt in ("saxe",):
        cols = ("E1", "E2", "E4", "E6")
    tagged = []
    idle = M.idle(wt)
    walk = M.walk(wt)
    for name, frs, loop in (("idle", idle, True), ("walk", walk, True)):
        K.add_sway(frs, loop=loop)
        tagged.append((name, run_frames(frs, drawfn, shoulder, cols)))
    tagged.append(("hurt", run_frames(K.add_sway(M.hurt(wt)), drawfn, shoulder, cols)))
    tagged.append(("death", run_frames(K.add_sway(M.death(wt)), drawfn, shoulder, cols)))
    mv = M.moves(wt)
    for tag in ("atk1", "atk2", "atk3"):
        frs = K.add_sway(K.seq(mv[tag]))
        root = root_motion(frs, U.AX)
        for (ms, p, fl), r in zip(frs, root):
            fl["_root"] = r
        tagged.append((tag, run_frames(frs, drawfn, shoulder, cols)))
    anims, meta = build_meta((U.AX, U.FLOOR), [U.AX - 9, U.FLOOR - 70, 18, 70], tagged)
    meta["wtype"] = wt
    name = f"cf_unforged_{wt}"
    K.export_sheet(name, U.W, U.H, anims, meta, build=BUILD)
    n = sum(len(f) for _, f in anims)
    return f"{name}: {n} frames, " + ", ".join(f"{t}:{len(f)}" for t, f in anims)


# ================================================================ main
def job(j):
    kind, arg = j
    if kind == "uf":
        return build_unforged(arg)
    import forge_foes_beasts as B
    return B.build(arg, BUILD)


if __name__ == "__main__":
    jobs = [("uf", t) for t in UF_TYPES] + [("beast", n) for n in ("cf_smith", "cf_wraith", "cf_hulk", "cf_mite")]
    if ONLY:
        jobs = [j for j in jobs if (j[1] in ONLY) or (f"uf:{j[1]}" in ONLY) or (j[0] == "uf" and "uf" in ONLY)]
    for j in jobs:      # sequential: parallel Aseprite runs were seen to hang
        print(job(j), flush=True)
