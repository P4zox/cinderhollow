"""Shared toolkit for The Crimson Manor creatures (agent C art):
cm_servant, cm_hound, cm_gargoyle (gen_crimson_enemies.py) and the Butler (gen_crimson_butler.py).

Built on enemy_kit.py (normal-mapped parts, sel-out outlines, Rig) and a few read-only helpers from
gen_enemies3.py.  This module only ADDS palette ramps (lower-case keys so they never collide with the
upper-case ramps of other generators) and small helpers:

  palette   v pale grey-violet undead skin   k black livery wool      q black patent leather (shiny)
            r crimson velvet                  s tarnished silver (shiny) w white linen / gloves
            j silver-white hair               h hound hide (black-crimson) g black gargoyle stone
            m wing membrane (dark crimson)    fixed: e0..e4 red eye glow, b0..b4 blood, a0..a3 ash
  run_anims(...)          render tag functions -> per-phase frame lists + per-frame info
  hitbox_preview(...)     hurtbox / hit rects / 10x26 player / spawn / telegraph overlay preview
  bat_px(...)             tiny bat silhouettes (swarms, vanish)
  blood_drip / blood_pool / ash_dissolve
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import asebuild  # noqa: E402
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, ip, hash01, lerp, add, sub, line, polyline  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

BUILD = "--preview" not in sys.argv

RAMPS = {
    # pale grey-violet undead skin
    "v": ["#1d1824", "#352f40", "#565068", "#7c7690", "#a6a0b8", "#d2cddc"],
    # black livery wool (cool violet-black; top steps kept readable on dark rooms)
    "k": ["#07060a", "#100e16", "#1a1823", "#262434", "#38364b", "#545168"],
    # black patent leather / satin lapel (shiny)
    "q": ["#07060a", "#110f17", "#1d1a26", "#2d2a3a", "#4a4760", "#8e8aa6"],
    # crimson velvet
    "r": ["#1c040a", "#380812", "#5a0d19", "#861624", "#b0232e", "#d9453d"],
    # tarnished silver
    "s": ["#17151a", "#302c31", "#514b4e", "#79736f", "#a7a199", "#e0dcd2"],
    # white linen / gloves
    "w": ["#29252f", "#4b4652", "#78727f", "#a8a3ad", "#d4d0d6", "#f3f0ef"],
    # silver-white hair
    "j": ["#25232b", "#45424f", "#6d6a79", "#9a97a6", "#c8c5d0", "#efedf4"],
    # hound hide: hairless black-crimson
    "h": ["#08050a", "#120a10", "#1d0d15", "#2c111b", "#451823", "#6c2630"],
    # gargoyle: black stone
    "g": ["#0c0b0f", "#18171d", "#27252e", "#3a3743", "#524e5c", "#77727f"],
    # bat-wing membrane, dark crimson leather
    "m": ["#12040a", "#240812", "#3b0d1a", "#561424", "#77202d"],
}
FIXED = {
    # glowing red eyes (fixed colours = light)
    "e0": "#4a0509", "e1": "#8c0b12", "e2": "#d81e1e", "e3": "#ff5a3c", "e4": "#ffc6a8",
    # blood
    "b0": "#2a0206", "b1": "#4e0710", "b2": "#7a0c17", "b3": "#a8151d", "b4": "#d0302a",
    # ash
    "a0": "#2b272c", "a1": "#48424a", "a2": "#6c6570", "a3": "#958d96",
}
for _r, _cols in RAMPS.items():
    keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        keys.append(_k)
    K.RAMP[_r] = keys
for _k, _c in FIXED.items():
    K.HEX[_k] = _c
    K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
K.SHINY.update({"q": 0.9, "s": 0.9, "g": 0.97})
K.SMEAR.update({
    "silver": ["w5", "s5", "s4", "s2"],
    "silver_dim": ["s5", "s4", "s3", "s2"],
    "blood": ["e4", "e3", "b3", "b2"],
    "crimson": ["e3", "b4", "b3", "b2"],
    "stone": ["g5", "g4", "g3", "g2"],
})
RGBA = K.RGBA


# =========================================================================== driver
def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def run_anims(layers, draw, tagdefs, counts, loops=("idle", "walk", "run", "fly"), phases=(1,), sway_key="C",
              only=None):
    """tagdefs: [(tag, fn)] fn() -> [(ms, pose)].  draw(pose, frame_index, sway, phase) -> (Ls, info).
    Returns out{phase: [(ms, imgs)]}, infos{tag: [info (phase 1) ...]}, tags[(tag, a, b)]."""
    out = {ph: [] for ph in phases}
    infos, tags = {}, []
    n = 0
    for tag, fn in tagdefs:
        fr = fn()
        assert len(fr) == counts[tag], (tag, len(fr), counts[tag])
        if only and tag not in only:
            continue
        drv = [(p[sway_key][0] if isinstance(p[sway_key], tuple) else p[sway_key]) for _, p in fr]
        sway = K.spring(drv, loop=tag in loops, extra=[p.get("wind", 0.0) for _, p in fr])
        a = n
        infos[tag] = []
        for k, (ms, p) in enumerate(fr):
            for ph in phases:
                Ls, info = draw(p, k, sway[k], ph)
                imgs = {}
                for nm in layers:
                    v = Ls.get(nm)
                    if v is None:
                        continue
                    imgs[nm] = K.render_layer(v) if isinstance(v, Layer) else v.image()
                if p.get("post"):
                    imgs = p["post"](imgs, ph)
                out[ph].append((ms, imgs))
                if ph == phases[0]:
                    infos[tag].append(info)
            n += 1
        tags.append((tag, a, n - 1))
    return out, infos, tags


# =========================================================================== previews
def preview_rows(path, tags, flats, scale=3):
    W, H = K.W, K.H
    cols = max(b - a + 1 for _, a, b in tags)
    pad, lab = 2, 12
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(tags) * (H + pad + lab) * scale), (46, 46, 52, 255))
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(tags):
        y0 = r * (H + pad + lab) * scale
        d.text((4, y0 + 4), f"{t} ({b - a + 1})", fill=(230, 230, 230, 255))
        for i in range(a, b + 1):
            fr = Image.new("RGBA", (W, H), (92, 92, 98, 255))
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), ((i - a) * (W + pad) * scale,
                                                                                     y0 + lab * scale))
    sheet.save(path)


def closeup(path, flats, idx, scale=6, bg=(92, 92, 98, 255)):
    W, H = K.W, K.H
    sheet = Image.new("RGBA", (len(idx) * (W + 2) * scale, H * scale), (46, 46, 52, 255))
    for k, i in enumerate(idx):
        fr = Image.new("RGBA", (W, H), bg)
        fr.alpha_composite(flats[i])
        sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), (k * (W + 2) * scale, 0))
    sheet.save(path)


def hitbox_preview(path, tags, flats, meta, scale=3, extra_rows=()):
    """Hurtbox green, hit rect red on active frames (per-frame 'rects' if present, union orange), a blue 10x26
    player box standing at the far edge (and the near/back edge for both-sided hits), anchor yellow, spawn
    magenta, telegraph cyan."""
    W, H = K.W, K.H
    start = {t: (a, b) for t, a, b in tags}
    rows, seen = [], set()
    for t, d in meta.get("attacks", {}).items():
        rows.append((t, d["windows"] if "windows" in d else [d]))
        seen.add(t)
    for t in list(meta.get("spawn", {})) + list(meta.get("telegraph", {})) + list(extra_rows):
        if t not in seen and t in start:
            rows.append((t, []))
            seen.add(t)
    rows.append((tags[0][0], []))
    pad, lab = 2, 12
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", (cols * (W + pad) * scale, len(rows) * (H + pad + lab) * scale), (46, 46, 52, 255))
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        sp = meta.get("spawn", {}).get(t)
        tg = meta.get("telegraph", {}).get(t)
        txt = t + "  " + "  ".join(f"active {w['active']} hit {w['hit']}" for w in wins)
        if sp:
            txt += f"  spawn f{sp['frame']} {sp['at']}"
        if tg:
            txt += f"  telegraph f{tg['frame']} {tg['at']}"
        dd.text((4, y0 + 3), txt, fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), (92, 92, 98, 255))
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rr = w.get("rects", {}).get(str(k), w["hit"])
                    rect(w["hit"], (255, 170, 60, 255), 1)
                    rect(rr, (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = rr
                    rect([min(W - 10, max(0, hx + hw - 6)), H - 26, 10, 26], (90, 150, 255, 255))
                    if hx < ax - 12:
                        rect([max(0, hx - 4), H - 26, 10, 26], (90, 150, 255, 255))

            def cross(pt, col):
                sx, sy = pt
                d.line([(sx * scale - 6, sy * scale + 1), (sx * scale + 8, sy * scale + 1)], fill=col, width=2)
                d.line([(sx * scale + 1, sy * scale - 6), (sx * scale + 1, sy * scale + 8)], fill=col, width=2)
            if sp and k == sp["frame"]:
                cross(sp["at"], (255, 60, 255, 255))
            if tg and k == tg["frame"]:
                cross(tg["at"], (60, 240, 255, 255))
            yy = min(ay * scale, H * scale - 1)
            d.line([(ax * scale - 5, yy - 1), (ax * scale + 5, yy - 1)], fill=(255, 255, 0, 255), width=2)
            d.line([(ax * scale, yy - 8), (ax * scale, yy)], fill=(255, 255, 0, 255), width=2)
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(path)


# =========================================================================== meta helpers
def bbox(pts, pad=0):
    return K.bbox(pts, pad)


def union_rect(rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def attack_rect(infos, tag, a, b, x_min=None, x_max=None, floor=True, key="hit"):
    """Per-frame rects from the drawn weapon/smear pixels over the inclusive active range; each reaches the floor
    so a 10x26 player standing there is hit."""
    rs = {}
    for k in range(a, b + 1):
        pts = set(infos[tag][k].get(key, set()))
        if x_min is not None:
            pts = {q for q in pts if q[0] >= x_min}
        if x_max is not None:
            pts = {q for q in pts if q[0] <= x_max}
        r = bbox(pts)
        assert r, (tag, k)
        if floor:
            r[3] = K.H - r[1]
        rs[str(k)] = r
    return {"active": [a, b], "hit": union_rect(list(rs.values())), "rects": rs}


def write_meta(name, meta):
    with open(os.path.join(asebuild.ASSETS, f"{name}_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


# =========================================================================== small art helpers
BAT_SHAPES = {
    # 7x4 bat silhouettes, '#' body/wing, 'e' eye; facing right
    0: ["#.....#", "##.#.##", ".#####.", "...#..."],       # wings up
    1: [".......", "###.###", ".#####.", "#..#..#"],       # wings level
    2: [".......", "...#...", ".#####.", "##...##"],       # wings down
}
BAT_SMALL = {
    0: ["#...#", ".###.", "..#.."],
    1: ["##.##", ".###.", "....."],
    2: [".....", ".###.", "#...#"],
}


def bat_px(c, flap, small=False, body="k2", rim="k4", eye="e3", facing=1):
    """Pixel dict for one little bat centred at c (frame coords)."""
    sh = (BAT_SMALL if small else BAT_SHAPES)[flap % 3]
    h = len(sh)
    w = len(sh[0])
    x0 = int(round(c[0])) - w // 2
    y0 = int(round(c[1])) - h // 2
    out = {}
    for yy, row in enumerate(sh):
        for xx, ch in enumerate(row if facing > 0 else row[::-1]):
            if ch == "#":
                out[(x0 + xx, y0 + yy)] = body
    # top-lit rim on the upper pixels, one red eye on the head
    for (x, y) in list(out):
        if (x, y - 1) not in out and hash01(x, y, 5) < 0.6:
            out[(x, y)] = rim
    hx = x0 + w // 2 + (1 if facing > 0 else -1) * (0 if small else 1)
    hy = y0 + (1 if small else 2)
    if eye and not small:
        out[(hx, hy)] = eye
    return out


def outline_px(pix, col="OUT"):
    """1px dark outline around a pixel dict (for FX sprites that need to read on any background)."""
    o = {}
    for (x, y) in pix:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q not in pix:
                o[q] = col
    return o


def blood_drip(FX, src, fi, length=3.0, seed=0, cols=("b3", "b2", "b4")):
    """A drip hanging off src, stretching and releasing a droplet across frames."""
    ph = (fi * 0.37 + hash01(seed, 1, 71)) % 1.0
    x0, y0 = ip(src)
    n = int(length * (0.4 + ph))
    for j in range(n):
        FX.put([(x0, y0 + j)], cols[1] if j < n - 1 else cols[0])
    FX.put([(x0, y0 + n)], cols[2] if n else cols[0])
    if ph > 0.6:
        FX.put([(x0, y0 + n + 2 + int((ph - 0.6) * 10))], cols[0])


def blood_pool(FX, cx, width, floor, seed=0):
    for x in range(int(cx - width), int(cx + width) + 1):
        t = abs(x + .5 - cx) / max(1, width)
        if t < 1:
            FX.put([(x, floor)], "b2" if t < 0.6 else "b1")
            if t < 0.45 and hash01(x, 3, seed) < 0.7:
                FX.put([(x, floor - 1)], "b1" if t > 0.25 else "b3")


def ash_dissolve(imgs, frac, names, seed=0, rise=20, blood=True):
    """Burn layers into ash from the top down with a glowing blood-red edge; lost pixels drift up as ash."""
    pal = ("e3", "b4", "b3", "a2", "a1") if blood else ("a3", "a2", "a1", "a0", "a0")
    return K.ember_dissolve(imgs, frac, names, seed=seed, rise=rise, pal=pal)


def eye_glow(FX, e, level, dirx=1, trail=0):
    """Red glowing eye: level 1 = a dot, 2 = hot + a short flare, 3 = blazing (+cross glint), trail = streak length
    behind the eye (phase 2 / motion)."""
    x, y = e
    if level <= 0:
        return
    FX.put([(x, y)], "e3" if level == 1 else "e4")
    if level >= 1:
        FX.put([(x + dirx, y)], "e2")
    if level >= 2:
        FX.put([(x - dirx, y)], "e2")
    if level >= 3:
        FX.put([(x, y - 1), (x, y + 1)], "e2")
        FX.put([(x + 2 * dirx, y)], "e1")
    for t in range(trail):
        FX.put([(x - dirx * (2 + t), y + (1 if t > 1 else 0))], "e2" if t < 1 else "e1" if t < 3 else "e0")


def check_lengths(name, tagdefs, pairs, tol=0.8):
    """Proportion guard: joint distances (e.g. pelvis-chest, chest-head) must stay within tol of the reference in
    every pose of every tag.  pairs: [(joint_a, joint_b, reference_length)].  Prints and returns the offenders."""
    bad = []
    for tag, fn in tagdefs:
        for k, (_, p) in enumerate(fn()):
            for a, b, ref in pairs:
                if p.get(a) is None or p.get(b) is None:
                    continue
                d = math.dist(p[a], p[b])
                if abs(d - ref) > tol:
                    bad.append((tag, k, a + "-" + b, round(d, 2), ref))
    for b in bad:
        print(name, "PROPORTION", b)
    return bad


def normalize_spine(p, lt, ln_):
    """Keep the torso (P->C) and neck (C->Hd) lengths exactly constant: the pose keys only give directions."""
    q = dict(p)
    P, C, Hd = p["P"], p["C"], p["Hd"]
    d = math.dist(P, C) or 1.0
    C2 = (P[0] + (C[0] - P[0]) * lt / d, P[1] + (C[1] - P[1]) * lt / d)
    d2 = math.dist(C, Hd) or 1.0
    Hd2 = (C2[0] + (Hd[0] - C[0]) * ln_ / d2, C2[1] + (Hd[1] - C[1]) * ln_ / d2)
    q["C"], q["Hd"] = C2, Hd2
    return q


def clamp_reach(sh, hand, reach):
    """Pull a hand/foot target back inside the limb's reach so no segment is ever stretched."""
    d = math.dist(sh, hand)
    if d <= reach:
        return hand
    k = reach / d
    return (sh[0] + (hand[0] - sh[0]) * k, sh[1] + (hand[1] - sh[1]) * k)


def crumble(imgs, frac, names, center, seed=0, radius=24.0, blood=True, fx_name="FX", motes=0.05, rise=10):
    """Erode the named layers from the silhouette's outside in (coherent 2x2 chunks, no speckle): the eroding rim
    turns to ash (and blood), lost chunks drift away as a few motes.  frac 0 = intact .. 1 = gone."""
    W, H = K.W, K.H
    cx, cy = center
    out = dict(imgs)
    mp = {}
    for n in names:
        if n not in imgs:
            continue
        src = imgs[n].load()
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = new.load()
        for y in range(H):
            for x in range(W):
                if src[x, y][3] == 0:
                    continue
                d = min(1.0, math.hypot(x + .5 - cx, (y + .5 - cy) * 1.4) / radius)
                t = 0.3 * hash01(x // 2, y // 2, 70 + seed) + 0.7 * (1 - d)
                if t >= frac:
                    if t < frac + 0.06 and frac > 0.0:
                        c = "a2" if hash01(x // 2, y, 71) < 0.55 else ("b2" if blood else "a1")
                        dst[x, y] = K.RGBA[c]
                    else:
                        dst[x, y] = src[x, y]
                elif hash01(x, y, 72 + seed) < motes:
                    age = frac - t
                    if age < 0.35:
                        mx = int(x + (x - cx) * age * 0.6 + math.sin(y + age * 9) * 1.5)
                        my = int(y - age * rise * (1 if hash01(x, y, 73) < 0.6 else -0.6))
                        if 0 <= mx < W and 0 <= my < H:
                            mp[(mx, my)] = ("a3" if age < 0.12 else "a2" if age < 0.24 else "a1") \
                                if hash01(x, y, 74) < 0.7 or not blood else "b3"
        out[n] = new
    fx = imgs[fx_name].copy() if fx_name in imgs else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fp = fx.load()
    for (x, y), c in mp.items():
        if fp[x, y][3] == 0:
            fp[x, y] = K.RGBA[c]
    out[fx_name] = fx
    return out


def edge_check(name, tags, flats, allow_top=(), allow_bottom_only=True):
    """Warn when a frame's opaque pixels touch the left/right (or top) edge of the frame -- clipped art."""
    W, H = K.W, K.H
    for t, a, b in tags:
        for i in range(a, b + 1):
            bb = flats[i].getbbox()
            if not bb:
                continue
            x0, y0, x1, y1 = bb
            hit = []
            if x0 <= 0:
                hit.append("left")
            if x1 >= W:
                hit.append("right")
            if y0 <= 0 and t not in allow_top:
                hit.append("top")
            if hit:
                print(name, "EDGE", t, i - a, hit)
