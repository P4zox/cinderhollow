#!/usr/bin/env python3
"""Enemy generator v2 -- spec section C (docs/ART_SPEC2.md), same rules as ART_SPEC section 4.

    python3 art/gen_enemies2.py                      build every enemy + projectile (Aseprite)
    python3 art/gen_enemies2.py --preview            previews + meta only (no Aseprite)
    python3 art/gen_enemies2.py --only rot_hulk,root_spawn [--preview]

Outputs per enemy <name>:
    art/<name>.aseprite, assets/<name>.png + .json, assets/<name>_meta.json,
    art/previews/<name>.png (4x, one row per tag),
    art/previews/<name>_hitbox.png (hurtbox green, hit rects red on active frames, spawn points magenta)
Projectiles: proj_rotglob (16x16, fly 4 loop), proj_lightorb (12x12, fly 4 loop).

Weeping Mire enemies (rot_hulk, bog_spitter, mire_witch): sickly greens, murky teal, rot-orange glow.
Pale Crown enemies (gilded_sentinel, root_spawn, sun_seraph): white-gold porcelain, gold armour, pale roots.
All face RIGHT, feet on the bottom row (sun_seraph floats: anchor = body centre, "flying": true).
Method + helpers: enemy_kit.py (normal-field shading, sel-out outline, Rig with rotation).
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, basis, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, leg, arm, blade_px, swept,
                       speed_lines, thrust_lines, rot_pt, dirv, bbox, flame)
from PIL import Image, ImageDraw  # noqa: E402

BUILD = "--preview" not in sys.argv

# =========================================================================== extra palette ramps
NEW_RAMPS = {
    # bloated swamp flesh (sickly pale yellow-green)
    "E": ["#12170f", "#1f2b1b", "#34452c", "#52663f", "#798953", "#a8ad77"],
    # murky teal moss / bog water
    "N": ["#0b1513", "#122523", "#1b3833", "#285048", "#3a6b5c", "#578a72"],
    # rot-green glow (fixed colours, spores / bile)
    "J": ["#27410f", "#4f7a17", "#8dbf2e", "#cdee6a", "#f3ffc4"],
    # peat / bog mud
    "H": ["#130e0a", "#221812", "#35281c", "#4b3a27", "#665034"],
    # white porcelain (cool-warm white)
    "S": ["#27232d", "#48434f", "#736e79", "#a39d9a", "#d2cbbd", "#f5f0e2"],
    # bright crown gold
    "U": ["#382107", "#65400e", "#9c6915", "#d09a2a", "#f0ca58", "#fff3b4"],
    # pale white-gold bark (the Pale Root)
    "X": ["#29201a", "#4a3b2c", "#76624a", "#a38c68", "#cbb68b", "#ebdfbd"],
}
for _r, _cols in NEW_RAMPS.items():
    keys = []
    for _i, _c in enumerate(_cols):
        k = f"{_r}{_i}"
        K.HEX[k] = _c
        K.RGBA[k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        keys.append(k)
    K.RAMP[_r] = keys
K.SHINY.update({"S": 0.9, "U": 0.9})
K.SMEAR.update({
    "bog": ["E5", "E5", "E4", "E3"],
    "rot": ["J4", "J3", "J2", "J1"],
    "holy": ["Y3", "Y2", "U5", "U4"],
    "pale": ["S5", "S4", "U5", "U4"],
})

# =========================================================================== generic driver
SPEC_FRAMES = {   # docs/ART_SPEC2.md section C
    "rot_hulk": dict(idle=4, walk=6, smash=10, hurt=2, death=8),
    "bog_spitter": dict(idle=4, crawl=6, spit=9, hurt=2, death=6),
    "mire_witch": dict(idle=4, walk=6, cast=10, hurt=2, death=6),
    "gilded_sentinel": dict(idle=4, walk=6, sweep=12, thrust=9, hurt=2, death=8),
    "root_spawn": dict(idle=4, crawl=6, burst=7, hurt=2, death=6),
    "sun_seraph": dict(fly=6, cast=10, dive=6, hurt=2, death=6),
}


def render_anims(name, layers, draw, anims, sway_key="C", loops=("idle", "walk", "fly", "crawl")):
    out, infos = [], {}
    spec = SPEC_FRAMES[name]
    assert list(spec) == [t for t, _ in anims], (name, list(spec))
    for tag, fn in anims:
        fr = fn()
        assert spec[tag] == len(fr), (name, tag, len(fr))
        drv = [p[sway_key][0] if isinstance(p[sway_key], tuple) else p[sway_key] for _, p in fr]
        sway = K.spring(drv, loop=tag in loops, extra=[p.get("wind", 0.0) for _, p in fr])
        lst, inf = [], []
        for k, (ms, p) in enumerate(fr):
            Ls, info = draw(p, k, sway[k])
            imgs = {}
            for n in layers:
                v = Ls.get(n)
                if v is None:
                    continue
                imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
            if p.get("post"):
                imgs = p["post"](imgs)
            if p.get("snap"):
                box = K.opaque_bbox(imgs, p["snap"])
                if box and box[3] != K.H:
                    dy = K.H - box[3]
                    imgs = K.shift_imgs(imgs, 0, dy, p["snap"])
                    info["hit"] = {(x, y + dy) for (x, y) in info.get("hit", set())}
            lst.append((ms, imgs))
            inf.append(info)
        out.append((tag, lst))
        infos[tag] = inf
    return out, infos


def hit_rect(infos, tag, ks, floor=True, x_min=None, x_max=None):
    pts = set()
    for k in ks:
        pts |= infos[tag][k].get("hit", set())
    r = bbox(pts)
    if x_min is not None and r[0] < x_min:
        r[2] -= x_min - r[0]; r[0] = x_min
    if x_max is not None and r[0] + r[2] > x_max:
        r[2] = x_max - r[0]
    if floor:
        r[3] = K.H - r[1]
    return r


def hurtbox(anims, names, inset=(1, 0, 1), floor=True):
    imgs = anims[0][1][0][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs, names)
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2],
            (K.H if floor else y1) - (y0 + inset[1])]


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def rag_hem(x0, x1, y, fi, seed, depth=2.5, sway=0.0):
    """Ragged cloth hem: polygon points from x1 back to x0 along y (teeth hang down)."""
    pts = []
    n = max(2, int((x1 - x0) / 1.6))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x0 - x1) * t
        d = depth * (0.3 + hash01(i, fi // 2, seed)) if i % 2 == 0 else depth * 0.15
        pts.append((x + sway * (0.4 + 0.6 * t), y + d))
    return pts


def disc_glow(FX, c, r, pal, squash=1.0):
    """Radial fixed-colour blob: pal ordered bright core -> dim edge."""
    n = len(pal)
    for q in mask_disc(c, r, r * squash):
        d = math.hypot(q[0] + .5 - c[0], (q[1] + .5 - c[1]) / squash) / max(r, 0.5)
        FX.put([q], pal[min(n - 1, int(d * n))])


def strand(L, a, b, sag, color, noout=True):
    """Hanging strand (moss, drool): quadratic sag between a and b."""
    pts = []
    for i in range(9):
        t = i / 8
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)
        pts.append((x, y))
    if isinstance(L, FXLayer):
        L.put(polyline(pts), color)
    else:
        L.fill(polyline(pts), color, noout=noout)


def hitbox_preview2(name, tags, flats, meta, scale=4):
    """Kit-style debug overlay + spawn rows: hurtbox green, hit rects red on active frames, a blue 10x26 player
    box at the far edge of the hit, anchor cross yellow, spawn point magenta (on the spawn frame)."""
    W, H = K.W, K.H
    start = {t: (a, b) for t, a, b in tags}
    rows = []
    for t, d in meta.get("attacks", {}).items():
        rows.append((t, d["windows"] if "windows" in d else [d], None))
    for t, s in meta.get("spawn", {}).items():
        if t not in meta.get("attacks", {}):
            rows.append((t, [], s))
    rows.append((tags[0][0], [], None))
    pad, lab = 2, 10
    cols = max(start[t][1] - start[t][0] + 1 for t, _, _ in rows)
    sheet = Image.new("RGBA", ((cols * (W + pad)) * scale, len(rows) * (H + pad + lab) * scale), K.BG)
    dd = ImageDraw.Draw(sheet)
    ax, ay = meta["anchor"]
    for r, (t, wins, sp) in enumerate(rows):
        a, b = start[t]
        y0 = r * (H + pad + lab) * scale
        txt = t + "  " + "  ".join(f"active {w['active']} hit {w['hit']}" for w in wins)
        if sp is None and t in meta.get("spawn", {}):
            sp = meta["spawn"][t]
        if sp:
            txt += f"  spawn frame {sp['frame']} at {sp['at']}"
        dd.text((4, y0 + 2), txt, fill=(235, 235, 240, 255))
        for i in range(a, b + 1):
            k = i - a
            fr = Image.new("RGBA", (W, H), K.BG_CELL)
            fr.alpha_composite(flats[i])
            big = fr.resize((W * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rect(w["hit"], (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = w["hit"]
                    px = min(W - 10, max(0, hx + hw - 6))
                    rect([px, H - 26, 10, 26], (90, 150, 255, 255))
            if sp and k == sp["frame"]:
                sx, sy = sp["at"]
                d.line([(sx * scale - 6, sy * scale + 2), (sx * scale + 10, sy * scale + 2)], fill=(255, 60, 255, 255), width=2)
                d.line([(sx * scale + 2, sy * scale - 6), (sx * scale + 2, sy * scale + 10)], fill=(255, 60, 255, 255), width=2)
            d.line([(ax * scale - 4, min(ay * scale, H * scale - 1)), (ax * scale + 4, min(ay * scale, H * scale - 1))],
                   fill=(255, 255, 0, 255))
            d.line([(ax * scale, ay * scale - 5), (ax * scale, ay * scale + 3)], fill=(255, 255, 0, 255))
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", f"{name}_hitbox.png"))


def export(name, layers, anims, meta, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD, flat_order=flat_order)
    if meta is not None:
        hitbox_preview2(name, tags, flats, meta)
    return tags, flats


def spawn_pt(p):
    return [int(round(p[0])), int(round(p[1]))]


def ground_burst(FX, ix, floor, stage, seed, pal_hot, pal_cold, spread=12, n=16):
    """Debris burst fanning up from the floor at x=ix (stage 1 = fresh, 2 = falling). Returns the point set."""
    pts = set()
    for k in range(n):
        a = -math.pi * (0.06 + 0.88 * hash01(k, 7, seed))
        r = (3 + spread * hash01(k, 8, seed + 1)) * (0.65 if stage == 1 else 1.0)
        q = ip((ix + math.cos(a) * r * 1.25, floor - 1 + math.sin(a) * r * (0.9 if stage == 1 else 0.6)
                + (0 if stage == 1 else 2.8 * (r / 10) ** 2)))
        c = (pal_hot if stage == 1 else pal_cold)[k % 3]
        FX.put([q], c)
        if k % 3 == 0 and stage == 1:
            FX.put([(q[0] + 1, q[1])], c)
        pts.add(q)
    return pts


# =========================================================================== 1. ROT HULK
HULK_L = ["BackArm", "BackLeg", "Body", "FrontLeg", "Growth", "FrontArm", "Head", "FX"]
H_NEU = dict(P=(25.0, 41.0), C=(28.0, 25.5), Hd=(37.0, 26.0), hup=(0.25, -1), fb=(20.0, 55), ff=(31.0, 55),
             hb=(18.6, 43.0), hf=(42.0, 47.4), rot=0.0, piv=(0, 0), legs_fixed=False, kb=None, kf=None,
             eye=1, jaw=0.0, glow=1, smear=None, impact=0, wind=0.0, spores=0, drool=True, pulse=0.0,
             epref=(-1, 0.35))
HP = mk(H_NEU)


def draw_hulk(p, fi, sw):
    Ls = {n: Layer(n) for n in HULK_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(3.0, -ln + 4.4), F(-5.2, -ln + 3.6)
    hB, hF = F(-3.6, 0.2), F(3.4, 0.2)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    info = {"hit": set()}
    floor = K.H - 1
    g = p["glow"]
    # ---- back arm (thick, hanging)
    arm(R, Ls["BackArm"], shB, p["hb"], 7.0, 7.4, 3.0, 2.6, "E", bias=-1, fist_r=2.9, pref=(-1, 0.3))
    # ---- legs: short bowed stumps, mud-caked feet
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(LR, Ls[nm], hip, ft, 7.0, 7.0, 4.0, 3.3, "E", bias=bias, boot="H", flen=4.4, heel=2.6, boot_h=3.4,
                knee=kn, pref=(1, 0.2))
        LR.dome(Ls[nm], add(k, (0.8, 0.2)), 2.0, 1.8, "V", bias=bias)          # knee growth
        LR.decal(Ls[nm], [add(k, (1.4, -0.4))], ("V", 5 + bias))
    # ---- body: hunched hump, distended belly, rag loincloth
    Bd = Ls["Body"]
    hump = R.dome(Bd, F(-2.8, -ln + 2.8), 11.4, 10.0, "E", bias=-1, tilt=(0.0, -0.05))
    Bd.decal([q for q in hump if hash01(q[0] - int(P[0]), q[1] - int(P[1]), 3) < 0.07], ("E", 2))
    chest = R.dome(Bd, F(5.2, -ln + 5.2), 6.4, 5.6, "E", bias=0)
    belly = R.dome(Bd, F(3.4, -4.4), 8.8, 7.6, "E", bias=0, tilt=(0.05, 0.1))
    bc = F(3.4, -4.4)
    for k in range(-2, 3):          # stretched veins across the belly
        a = add(bc, (-5.0, -3.0 + k * 2.2))
        b = add(bc, (5.5, -1.2 + k * 2.6))
        pts = [q for q in line(R.T(a), R.T(b)) if q in belly and hash01(q[0], q[1], 5 + k) < 0.55]
        Bd.decal(pts, ("V", 2))
    R.decal(Bd, [add(bc, (3.6, 1.6)), add(bc, (4.2, 1.6))], ("E", 1))          # navel pit
    # loincloth of rotten sacking
    loin = [F(-6.4, -1.6), F(6.4, -1.6), F(5.2, 2.4)] + \
        rag_hem(P[0] - 3.8 - sw * 0.2, P[0] + 4.4 - sw * 0.4, P[1] + 3.2, fi, 11, 2.6) + [F(-6.0, 1.8)]
    lm = R.mask(loin)
    Bd.paint(n_plate(lm, 1.3, (0.0, 0.1), 1.0, fold=lambda x, y: (0.5 * math.sin((x - P[0]) * 1.4), 0)), "H", bias=0)
    R.dline(Bd, F(-6.6, -1.4), F(6.6, -1.4), ("N", 1))
    # ---- growths: fungal shelves, pustules, mushroom caps, hanging moss
    Gr = Ls["Growth"]
    hc = F(-2.8, -ln + 2.8)
    for k, (ang, s) in enumerate(((-146, 0.95), (-170, 0.7), (-124, 0.6))):
        ca, sa = dirv(ang)
        base = (hc[0] + ca * 10.6, hc[1] + sa * 9.2)
        shelf = [add(base, (-3.4 * s, 0.4)), add(base, (-2.4 * s, -1.6 * s)), add(base, (0.4, -2.2 * s)),
                 add(base, (2.8 * s, -1.2 * s)), add(base, (3.6 * s, 0.6)), add(base, (0.0, 1.2))]
        m = R.plate(Gr, shelf, "N", bevel=1.0, tilt=(-0.1, -0.35), bias=0)
        under = [q for q in m if (q[0], q[1] + 1) not in m]
        Gr.decal(under, "O2" if g else "O0")
        Gr.decal([q for q in m if (q[0], q[1] - 1) not in m and hash01(q[0], q[1], 9) < 0.5], ("N", 5))
    # mushroom caps along the top of the hump
    for k, (ang, s) in enumerate(((-72, 1.0), (-58, 0.7), (-84, 0.6))):
        ca, sa = dirv(ang)
        base = (hc[0] + ca * 11.0, hc[1] + sa * 9.6)
        stem_top = add(base, (0.2, -1.6 * s - 0.6))
        R.cap(Gr, base, stem_top, 0.7, 0.6, "X", bias=-1, ao=0)
        cap = R.dome(Gr, add(stem_top, (0, -0.4)), 2.2 * s + 0.4, 1.3 * s + 0.4, "R", bias=0, ao=0)
        R.decal(Gr, [add(stem_top, (-0.6, -1.0))], "O3" if g else "R3")
    # glowing pustules (fixed colours)
    pus = []
    for k, (a, b, r) in enumerate(((-7.2, -ln + 6.4, 1.8), (-4.4, -ln + 8.6, 1.0), (-1.2, -ln - 1.6, 1.2),
                                   (7.4, -5.4, 0.9))):
        c = R.T(F(a, b))
        rr = r * (1.0 + 0.12 * p["pulse"] * (1 if k % 2 else 0.6))
        pal = ("O5", "O4", "O3", "O2", "O1") if g >= 2 else ("O4", "O3", "O2", "O1", "O1") if g else \
            ("O2", "O1", "O1", "O0", "O0")
        pix = {}
        for q in mask_disc(c, rr + 0.35):
            d = math.hypot(q[0] + .5 - c[0] + 0.4, q[1] + .5 - c[1] + 0.4) / (rr + 0.35)
            pix[q] = pal[min(4, int(d * 4.2))]
        Gr.fixed(pix)
        pus.append(c)
    info["pus"] = pus
    # hanging moss beards from the shoulders / belly
    for k, (a, b, L_) in enumerate(((7.4, -ln + 6.0, 6.5), (4.6, -6.0, 5.0), (-9.6, -ln + 7.0, 7.0), (9.0, -8.5, 4.0))):
        s0 = R.T(F(a, b))
        s1 = (s0[0] - sw * 0.35 + math.sin(fi * 1.3 + k) * 0.5, s0[1] + L_)
        strand(Gr, s0, s1, 0.4, "N2" if k % 2 else "N3")
        Gr.fill([ip(s1)], "N1", noout=True)
    # ---- head: small, sunk forward between the shoulders; underbite with tusks, rot-orange eyes
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    jw = p["jaw"]
    R.plate(Hl, [G(-2.2, 0.6), G(3.2, 0.4 + jw * 0.5), G(5.4, 1.6 + jw), G(5.2, 3.6 + jw), G(2.8, 4.8 + jw),
                 G(-1.6, 4.0 + jw * 0.4)], "E", bevel=1.2, tilt=(-0.1, 0.1), bias=-1)
    R.dome(Hl, G(0.6, -0.6), 4.0, 3.5, "E", tilt=(-0.05, -0.05), bias=1)
    R.dline(Hl, G(0.8, -1.4), G(4.4, -1.2), ("E", 2))                        # heavy brow
    cowl = [G(-4.4, 1.6), G(-4.6, -1.6), G(-3.2, -4.2), G(0.0, -5.0), G(2.6, -4.4), G(3.4, -3.0), G(1.0, -2.8),
            G(-1.0, -1.6), G(-1.6, 1.8)]                                      # sodden moss cowl
    cw = R.plate(Hl, cowl, "N", bevel=1.2, tilt=(-0.1, -0.3), bias=0)
    Hl.decal([q for q in cw if hash01(q[0], q[1], 29) < 0.2], ("N", 5))
    R.dline(Hl, G(1.6, 1.4 + jw * 0.3), G(4.8, 1.8 + jw * 0.8), "OUT")          # mouth
    if jw > 0.8:
        R.decal(Hl, [G(3.2, 2.0 + jw * 0.5), G(4.0, 2.2 + jw * 0.6)], ("F", 1))
    for dx in (2.6, 4.4):                                                       # tusks
        Hl.fixed({R.pt(G(dx, 1.0 + jw * 0.6)): "B4", R.pt(G(dx, 0.2 + jw * 0.6)): "B5" if dx > 3 else "B3"})
    if p["eye"]:
        e1, e2 = R.pt(G(1.8, -0.6)), R.pt(G(3.4, -0.4))
        FX.put([e1], "O4" if p["eye"] == 1 else "O5")
        FX.put([e2], "O3" if p["eye"] == 1 else "O5")
        if p["eye"] > 1:
            FX.put([(e2[0] + 1, e2[1]), (e2[0] + 2, e2[1] - 1), (e1[0] - 1, e1[1] - 1)], "O3")
    if p["drool"] and p["rot"] == 0:
        m0 = R.T(G(4.4, 3.4 + jw))
        dl = 2 + (fi % 3)
        strand(Hl, m0, (m0[0] - sw * 0.2, m0[1] + dl), 0.0, "J2")
        Hl.fill([ip((m0[0] - sw * 0.2, m0[1] + dl + 1))], "J3", noout=True)
    # ---- the huge fist arm
    Fa = Ls["FrontArm"]
    hf = p["hf"]
    el = ik(shF, hf, 8.6, 9.2, p["epref"])
    R.cap(Fa, shF, el, 4.0, 3.4, "E", bias=0)
    R.cap(Fa, el, hf, 3.8, 3.6, "N", bias=0)                                   # bog-crusted forearm
    fm = R.dome(Fa, hf, 6.2, 5.6, "N", bias=0, tilt=(0.0, 0.05))
    dv = sub(R.T(hf), R.T(el))
    dl_ = math.hypot(*dv) or 1
    d_ = (dv[0] / dl_, dv[1] / dl_)
    pp = (-d_[1], d_[0])
    hT = R.T(hf)
    for o in (-3.3, -1.1, 1.1, 3.3):                                           # knuckle boulders
        c = (hT[0] + d_[0] * 3.9 + pp[0] * o, hT[1] + d_[1] * 3.9 + pp[1] * o)
        fm |= Fa.paint(n_dome(c, 1.7, 1.7), "N", bias=0, ao=1)
    Fa.decal([q for q in fm if hash01(q[0] - int(hT[0]), q[1] - int(hT[1]), 17) < 0.12], ("V", 4))
    for k in range(5):                                                         # growth nodules on the forearm
        c = lerp(R.T(el), hT, 0.15 + 0.16 * k)
        c = (c[0] + pp[0] * (1.8 if k % 2 else -1.8), c[1] + pp[1] * (1.8 if k % 2 else -1.8))
        m = Fa.paint(n_dome(c, 1.3, 1.2), "V", bias=0, ao=1)
    fa = [q for q in line(R.T(el), lerp(R.T(el), hT, 0.62))]                    # glowing rot seam up the forearm
    Fa.decal([(q[0] + int(round(pp[0] * 1.2)), q[1] + int(round(pp[1] * 1.2))) for q in fa],
             "O3" if g >= 2 else "O2" if g else "O0")
    sm_ = R.dome(Fa, add(shF, (-0.4, -0.6)), 4.8, 4.2, "E", bias=0)          # boulder shoulder
    Fa.decal([q for q in sm_ if hash01(q[0], q[1], 23) < 0.06], ("E", 2))
    sp = R.T(add(shF, (-1.0, -3.2)))
    shelf = [add(sp, (-3.2, 0.6)), add(sp, (-1.6, -1.6)), add(sp, (1.4, -1.8)), add(sp, (3.2, 0.2)), add(sp, (0, 1.2))]
    m = Fa.paint(n_plate(poly_mask(shelf), 1.0, (-0.1, -0.35)), "N", bias=0)
    Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], "O2" if g else "O0")
    info["fist"] = hT
    info["hit"] |= set(q for q in fm)
    # ---- fx: smear, impact, spores
    if p["smear"]:
        sm = p["smear"]
        s0 = R.T(shF)
        g0 = sm["h0"]
        a0 = math.degrees(math.atan2(g0[1] - s0[1], g0[0] - s0[0]))
        a1 = math.degrees(math.atan2(hT[1] - s0[1], hT[0] - s0[0]))
        if sm.get("wrap"):
            a0 -= 360 if a0 > a1 else 0
        r1 = math.hypot(hT[0] - s0[0], hT[1] - s0[1])
        hot = swept(FX, s0, a0, s0, a1, r1 - 4.5, r1 + 4.5, hw=1.4, start=sm.get("start", 0.0), pal="bog",
                    exclude=fm, taper=sm.get("taper", 0.35), clip_y=floor, streak=True)
        info["hit"] |= hot
    if p["impact"]:
        st = p["impact"]
        ix = int(round(min(hT[0] + 6.5, K.W - 6)))
        pts = ground_burst(FX, ix, floor, st, 60, ("J4", "J3", "H4"), ("J2", "N4", "H3"), spread=15, n=28)
        pts |= ground_burst(FX, ix - 2, floor, st, 64, ("J4", "E4", "H4"), ("N3", "H3", "N2"), spread=9, n=12)
        for dx in range(-16, 17):                                  # mud shock along the floor
            if hash01(dx, 3, 62) < (0.85 if st == 1 else 0.55):
                FX.put([(ix + dx, floor)], ("J3" if abs(dx) < 4 else "E4" if abs(dx) < 10 else "N3") if st == 1
                       else ("N4" if abs(dx) < 8 else "N2"))
                if st == 1 and abs(dx) < 12 and hash01(dx, 4, 63) < 0.5:
                    FX.put([(ix + dx, floor - 1)], "N4")
        if st == 1:
            for ang in range(-170, -5, 20):
                L_ = 10 if ang % 40 == 10 else 6
                FX.put(line((ix, floor - 1), (ix + math.cos(math.radians(ang)) * L_ * 1.2,
                                              floor - 1 + math.sin(math.radians(ang)) * L_)),
                       "E5" if ang % 40 == 10 else "E4")
        info["hit"] |= pts
        info["impact_x"] = ix
    for q in fm:                                                   # never paint FX over the fist itself
        FX.px.pop(q, None)
    if p["spores"]:
        s = p["spores"]
        for k, c in enumerate(pus):
            for j in range(4):
                a = -math.pi * (0.15 + 0.7 * hash01(k, j, 70))
                r = 2 + s * 2.4 + 2.5 * hash01(j, k, 71)
                q = ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r - s))
                FX.put([q], ("J4", "J3", "J2", "J1")[min(3, s - 1 + (j % 2))])
    return Ls, info


def h_idle():
    fr = []
    for i in range(4):
        b = (0, 0.6, 1.0, 0.6)[i]
        fr.append((230, HP(P=(25.0, 41.0 + b * 0.3), C=(28.0, 25.5 + b), Hd=(37.0, 26.0 + b * 1.1),
                           hb=(18.6, 43.0 + b * 0.6), hf=(42.0, 47.4 + b * 0.5), pulse=b, jaw=b * 0.5)))
    return fr


def h_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (27.6 + 4.2 * c, 55 - max(0.0, -s) * 2.6)
        fb = (23.4 - 4.2 * c, 55 - max(0.0, s) * 2.6)
        bob = 1.5 * abs(c)
        lurch = 0.8 * s
        fr.append((150, HP(P=(25.4, 40.6 + bob), C=(28.6 + lurch, 25.2 + bob), Hd=(37.6 + lurch * 1.2, 25.8 + bob),
                           ff=ff, fb=fb, hb=(19.0 - 1.6 * c, 42.6 + bob), hf=(42.6 + 1.4 * c, 47.0 + bob * 0.4 - 0.8 * s),
                           pulse=0.5 + 0.5 * s)))
    return fr


def h_smash():
    back = dict(P=(23.6, 41.2), C=(22.8, 25.6), Hd=(30.0, 25.2), hup=(-0.05, -1), fb=(17.5, 55), ff=(31.0, 55),
                hb=(15.6, 40.0))
    down = dict(P=(27.4, 42.6), C=(31.8, 28.6), Hd=(40.0, 31.4), hup=(0.5, -1), fb=(19.0, 55), ff=(35.0, 55),
                hb=(22.0, 44.0))
    return [
        (140, HP(P=(24.6, 41.4), C=(26.4, 26.2), Hd=(34.4, 27.6), hf=(39.0, 44.0), hb=(18.0, 43.0), jaw=0.6)),
        (150, HP(P=(24.0, 41.2), C=(24.6, 25.8), Hd=(32.2, 26.6), hf=(36.0, 29.0), hb=(17.0, 42.0), jaw=1.0)),
        (170, HP(**back, hf=(31.0, 13.0), jaw=1.4, eye=2, glow=2, epref=(1, 0.2))),
        (200, HP(**dict(back, C=(22.0, 25.4), Hd=(29.0, 24.8)), hf=(22.0, 13.0), jaw=1.6, eye=2, glow=2, pulse=1,
                 epref=(1, -0.2))),
        (460, HP(**dict(back, P=(23.4, 41.4), C=(21.6, 25.6), Hd=(28.6, 25.0)), hf=(20.6, 13.0), jaw=1.8, eye=2,
                 glow=2, pulse=1.4, epref=(1, -0.2))),
        (60, HP(**dict(down, C=(29.0, 27.0), Hd=(37.0, 29.0)), hf=(44.0, 20.0), jaw=1.2, eye=2, wind=4,
                epref=(-0.3, -1), smear=dict(h0=(20.6, 13.0), start=0.1))),
        (70, HP(**down, hf=(46.6, 49.0), jaw=2.0, eye=2, impact=1, wind=3,
                smear=dict(h0=(44.0, 24.0), taper=0.3))),
        (120, HP(**down, hf=(46.6, 49.2), jaw=1.6, eye=2, impact=2)),
        (240, HP(**dict(down, C=(30.6, 28.0), Hd=(38.6, 30.4)), hf=(46.0, 48.8), jaw=0.8, pulse=0.5)),
        (220, HP(P=(25.4, 41.4), C=(28.6, 26.2), Hd=(36.8, 28.0), hf=(43.0, 47.6), hb=(19.0, 43.4), jaw=0.3)),
    ]


def h_hurt():
    return [(80, HP(P=(24.2, 41.2), C=(24.4, 25.4), Hd=(31.6, 25.2), hup=(-0.3, -1), hf=(39.0, 44.0), hb=(16.4, 41.0),
                    jaw=1.6, eye=2, glow=2, pulse=1.5)),
            (150, HP(P=(24.6, 41.0), C=(26.4, 25.4), Hd=(34.4, 26.6), hf=(41.0, 46.6), hb=(17.6, 42.6), jaw=0.8))]


def h_death():
    kneel = dict(kb=(20.4, 53.2), kf=(29.4, 53.4), fb=(13.4, 55), ff=(22.0, 55))
    return [
        (100, HP(P=(23.6, 41.2), C=(23.2, 25.2), Hd=(30.4, 24.6), hup=(-0.35, -1), hf=(38.0, 42.0), hb=(15.6, 40.0),
                 jaw=2.0, eye=2, glow=2, pulse=1.6)),
        (160, HP(P=(24.4, 43.4), C=(25.8, 28.0), Hd=(33.6, 29.4), hup=(0.1, -1), fb=(18.0, 55), ff=(31.0, 55),
                 hf=(40.0, 48.0), hb=(18.0, 45.0), jaw=1.6, eye=1, glow=1, drool=False)),
        (220, HP(**kneel, P=(24.6, 46.0), C=(27.8, 30.6), Hd=(35.8, 32.4), hup=(0.3, -1), hf=(42.0, 49.0),
                 hb=(19.0, 48.0), jaw=1.4, eye=1, glow=1, drool=False)),
        (320, HP(**kneel, P=(24.6, 46.2), C=(28.6, 31.4), Hd=(36.6, 33.4), hup=(0.4, -1), hf=(42.4, 49.0),
                 hb=(19.4, 48.4), jaw=1.8, eye=1, glow=1, pulse=1.0, drool=False)),
        (130, HP(**kneel, P=(24.0, 46.4), C=(33.0, 35.2), Hd=(41.0, 39.0), hup=(0.8, -1), hf=(46.0, 49.0),
                 hb=(22.0, 49.0), jaw=1.6, eye=0, glow=1, spores=1, drool=False)),
        (110, HP(**dict(kneel, kb=(19.4, 53.4), kf=(26.4, 53.6), fb=(12.0, 55), ff=(18.6, 55)), P=(22.6, 47.4),
                 C=(35.4, 40.2), Hd=(43.6, 45.0), hup=(1.2, -1), hf=(50.0, 49.6), hb=(26.0, 50.0), jaw=1.2, eye=0,
                 glow=0, spores=2, drool=False, epref=(0.2, -1))),
        (120, HP(**dict(kneel, kb=(19.0, 53.6), kf=(25.4, 53.8), fb=(11.0, 55), ff=(17.6, 55)), P=(22.0, 48.6),
                 C=(36.0, 45.0), Hd=(45.0, 49.4), hup=(1.6, -1), hf=(52.0, 50.0), hb=(28.0, 51.0), jaw=0.8, eye=0,
                 glow=0, spores=3, drool=False, epref=(0.2, -1), impact=2)),
        (900, HP(**dict(kneel, kb=(19.0, 53.6), kf=(25.4, 53.8), fb=(11.0, 55), ff=(17.6, 55)), P=(22.0, 48.8),
                 C=(36.0, 45.4), Hd=(45.0, 49.8), hup=(1.6, -1), hf=(52.0, 50.2), hb=(28.0, 51.2), jaw=0.6, eye=0,
                 glow=0, drool=False, epref=(0.2, -1))),
    ]


def build_hulk():
    K.setup(64, 56)
    anims, infos = render_anims("rot_hulk", HULK_L, draw_hulk,
                                [("idle", h_idle), ("walk", h_walk), ("smash", h_smash), ("hurt", h_hurt),
                                 ("death", h_death)])
    meta = {"native": 1, "frame": [64, 56], "anchor": [26, 56],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg"], inset=(2, 1, 2)),
            "attacks": {"smash": {"active": [6, 7], "hit": hit_rect(infos, "smash", [6, 7], x_min=32)}}}
    export("rot_hulk", HULK_L, anims, meta)
    return meta


# =========================================================================== 2. BOG SPITTER
SPIT_L = ["BackLegs", "Body", "Head", "Sac", "FrontLegs", "FX"]
T_NEU = dict(B=(16.5, 22.0), tilt=0.0, sq=1.0, flip=False, lift=0.0, ext=0.0, fr=0.0, fext=0.0, open=0.0, sac=0.25,
             glow=1, eye=1, glob=False, spray=0, drip=0, splat=0, twitch=0.0, wind=0.0, curl=0.0)
TP = mk(T_NEU)


def draw_spitter(p, fi, sw):
    Ls = {n: Layer(n) for n in SPIT_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    B = p["B"]
    fy = K.H - 1.0 - p["lift"]
    if p["flip"]:
        R = Rig(-p["tilt"], B, sy=-1.0)
    else:
        R = Rig(-p["tilt"], (B[0], K.H - 1.0), sx=1.0 / max(0.7, p["sq"]) ** 0.5, sy=p["sq"])
    Fb = lambda a, b: (B[0] + a, B[1] + b)
    info = {"hit": set()}
    g = p["glow"]
    # ---- legs (far pair first, darker; near pair on top)
    for side, nm in ((1, "BackLegs"), (0, "FrontLegs")):
        L = Ls[nm]
        bias = -1 if side else 0
        e = p["ext"]
        tw = p["twitch"] * math.sin(fi * 2.3 + side * 1.7)
        cu = p["curl"]
        dx = -1.6 if side else 0.0
        hip = Fb(-6.0 + dx, 1.4)
        knee = lerp((B[0] + 1.2 + dx, fy - 3.2), (B[0] - 7.5 + dx, fy - 4.6), e)
        ank = lerp((B[0] - 6.8 + dx, fy - 1.3), (B[0] - 13.0 + dx, fy - 1.4), e)
        toe = lerp((B[0] - 1.6 + dx, fy), (B[0] - 16.0 + dx, fy - 0.2), e)
        if cu:
            knee = lerp(knee, Fb(-2.0 + dx, 5.5 + tw), cu)
            ank = lerp(ank, Fb(-7.0 + dx, 8.0 + tw), cu)
            toe = lerp(toe, Fb(-4.0 + dx, 9.5 + tw * 1.5), cu)
        R.cap(L, hip, knee, 3.4 if not side else 2.8, 2.2, "N", bias=bias)
        R.cap(L, knee, ank, 1.6, 1.2, "N", bias=bias)
        R.cap(L, ank, toe, 1.0, 0.8, "N", bias=bias - (0 if side else 0))
        tq = R.T(toe)
        L.fixed({ip(add(tq, (0.6, 0.0))): "E3" if side else "E4", ip(add(tq, (0.3, -1.0))): "E2" if side else "E3"})
        # fore leg
        sh = Fb(5.0 + dx * 0.6, 3.2)
        fe = p["fext"]
        hand = lerp((B[0] + 7.6 + p["fr"] + dx * 0.6, fy), (B[0] + 12.5 + dx * 0.6, fy - 3.0), fe)
        if cu:
            hand = lerp(hand, Fb(9.0 + dx, 8.6 + tw), cu)
        el = ik(sh, hand, 3.6, 4.2, (-1, 0.2))
        R.cap(L, sh, el, 1.6, 1.2, "N", bias=bias)
        R.cap(L, el, hand, 1.1, 0.9, "N", bias=bias)
        hq = R.T(hand)
        L.fixed({ip(add(hq, (1.0, 0.0))): "E3" if side else "E4", ip(add(hq, (-0.6, 0.0))): "E2" if side else "E3"})
    # ---- body: warty teal back, pale sickly belly
    Bd = Ls["Body"]
    back = R.dome(Bd, Fb(-1.4, 0.0), 10.4, 6.8, "N", bias=0, tilt=(0.0, -0.05))
    belly = R.dome(Bd, Fb(3.0, 3.0), 7.8, 3.8, "E", bias=1, tilt=(-0.1, 0.05))
    Bd.decal([q for q in back if hash01(q[0] - int(B[0]), q[1] - int(B[1]), 5) < 0.13], ("V", 3))
    Bd.decal([q for q in back if hash01(q[0] - int(B[0]), q[1] - int(B[1]), 6) < 0.05], ("N", 5))
    for k, (a, b, r) in enumerate(((-6.0, -2.4, 1.6), (-1.8, -3.6, 1.3), (-8.6, 1.6, 1.2), (1.6, -1.0, 1.0),
                                   (-4.0, 1.8, 1.0))):                     # mottled sickly blotches
        c = R.T(Fb(a, b))
        Bd.decal([q for q in mask_disc(c, r, r * 0.8) if q in back], ("E", 3))
        Bd.decal([q for q in mask_disc((c[0] - 0.4, c[1] - 0.4), r * 0.5, r * 0.4) if q in back], ("E", 4))
    Bd.decal([q for q in belly if (q[1] - int(B[1])) % 2 == 0 and hash01(q[0], 0, 7) < 0.5], ("E", 3))
    # glowing fungal nubs along the spine
    for k, a in enumerate((-8.0, -4.6, -1.2, 2.0)):
        c = R.T(Fb(a, -6.2 + 0.08 * a * a * 0.15))
        rr = 1.1 if k % 2 else 0.8
        Bd.fixed({q: ("O4" if g >= 2 else "O3" if g else "O1") if math.hypot(q[0] + .5 - c[0] + 0.3, q[1] + .5 - c[1] + 0.3) < rr * 0.7
                  else ("O2" if g else "O0") for q in mask_disc(c, rr + 0.4)})
    # ---- throat sac (fixed glow colours + veins), bulges under the jaw
    Sc = Ls["Sac"]
    s = p["sac"]
    if s > 0:
        c = R.T(Fb(8.4 + 1.5 * s, 4.4 + 0.6 * s))
        rx, ry = 2.6 + 2.4 * s, 2.0 + 1.9 * s
        if not p["flip"] and c[1] + ry > K.H - 1.5:
            c = (c[0] + 0.5 * (c[1] + ry - K.H + 1.5), K.H - 1.5 - ry)
        pal = ("O1", "O2", "O3", "O4", "O5") if g >= 2 else ("O1", "O1", "O2", "O3", "O4") if g else \
            ("O0", "O0", "O1", "O1", "O2")
        pix = {}
        m = mask_disc(c, rx, ry)
        for q in m:
            ex, ey = (q[0] + .5 - c[0]) / rx, (q[1] + .5 - c[1]) / ry
            d = math.hypot(ex + 0.3, ey + 0.35)
            pix[q] = pal[4] if d < 0.3 else pal[3] if d < 0.62 else pal[2] if d < 0.9 else pal[1]
            if ex * ex + ey * ey > 0.72:
                pix[q] = pal[1] if ey < 0.2 else pal[0]
        for t in (-2, 0, 2):
            for q in line((c[0] + t * 0.7, c[1] - ry * 0.8), (c[0] + t * 1.2 + 0.4, c[1] + ry * 0.7)):
                if q in pix and hash01(q[0], q[1], 21) < 0.65:
                    pix[q] = pal[0]
        Sc.fixed(pix)
        info["sac"] = c
    # ---- head: flat wide skull, bulging eyes, hinged lower jaw
    Hl = Ls["Head"]
    R.dome(Hl, Fb(7.6, -1.6), 6.4, 4.6, "N", bias=0, tilt=(0.0, -0.1))
    hinge = Fb(4.4, 1.4)
    op = p["open"]
    ua = -op * 14.0                 # upper jaw tips up a little
    la = op * 34.0                  # lower jaw drops
    up_tip = add(hinge, (10.2 * math.cos(math.radians(ua)), 10.2 * math.sin(math.radians(ua)) - 0.6))
    lo_tip = add(hinge, (9.6 * math.cos(math.radians(la)), 9.6 * math.sin(math.radians(la)) + 0.6))
    if op > 0.1:
        inner = [hinge, up_tip, add(up_tip, (-0.4, 0.8)), lo_tip]
        Hl.fill(R.mask(inner), "F1")
        Hl.decal([q for q in R.mask([add(hinge, (1.5, 0.8)), add(lo_tip, (-2.0, -1.4)), add(lo_tip, (-3.8, -0.4))])],
                 "C3")                                                              # tongue
        if p["glob"]:
            gc = R.T(lerp(hinge, lerp(up_tip, lo_tip, 0.5), 0.72))
            disc_glow(FX, gc, 2.8, ("J4", "J3", "J3", "J2", "O3"))
            info["glob"] = gc
    # upper jaw lip
    R.plate(Hl, [add(hinge, (-1.0, -1.6)), add(up_tip, (-1.4, -2.2)), add(up_tip, (0.6, -0.4)), add(up_tip, (0.0, 0.6)),
                 add(hinge, (0.0, 0.4))], "N", bevel=1.1, tilt=(0.0, -0.2), bias=0)
    # lower jaw (pale)
    lj = R.plate(Hl, [add(hinge, (0.0, -0.4)), add(lo_tip, (0.2, -0.8)), add(lo_tip, (0.4, 0.6)), add(lo_tip, (-2.4, 2.0)),
                      add(hinge, (0.0, 2.2))], "E", bevel=1.1, tilt=(0.0, 0.2), bias=0)
    R.dline(Hl, add(hinge, (0.6, 0.2)), up_tip, "OUT")
    for k in range(3):   # nostrils / warts on the snout
        R.decal(Hl, [add(up_tip, (-2.2 - k * 1.6, -1.4 - (k % 2) * 0.4))], ("V", 2))
    # bulging eyes
    for k, (ex_, ey_) in enumerate(((4.6, -5.2), (7.6, -5.0))):
        c = Fb(ex_, ey_)
        R.dome(Hl, c, 2.2, 2.0, "N", bias=-1 if k == 0 else 0, tilt=(0, -0.2))
        if p["eye"]:
            e = R.pt(add(c, (0.6, 0.1)))
            FX.put([e], ("J3" if p["eye"] == 1 else "J4") if k else ("J2" if p["eye"] == 1 else "J3"))
            FX.put([(e[0] - 1, e[1])], "OUT")
        else:
            R.dline(Hl, add(c, (-1.2, 0.2)), add(c, (1.4, 0.2)), "OUT")
    info["mouth"] = R.T(lerp(up_tip, lo_tip, 0.5))
    info["hit"] |= set(Hl.px)
    # ---- fx
    if p["spray"]:
        m0 = info["mouth"]
        n = p["spray"]
        for k in range(22):
            a = math.radians(-28 + 48 * hash01(k, 1, 41))
            r = (2 + 10 * hash01(k, 2, 42)) * (0.75 if n == 1 else 1.1)
            q = ip((m0[0] + math.cos(a) * r, m0[1] + math.sin(a) * r + (n - 1) * (r / 5) ** 2))
            FX.put([q], ("J4", "J3", "O3")[k % 3] if n == 1 else ("J2", "J1", "O1")[k % 3])
    if p["drip"]:
        m0 = info["mouth"]
        strand(FX, (m0[0] - 2, m0[1] + 1), (m0[0] - 2.4, m0[1] + 1 + p["drip"]), 0, "J2")
    if p["splat"]:
        c = info.get("sac") or R.T(Fb(9, 5))
        n = p["splat"]
        for k in range(20):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 1, 51))
            r = (1.5 + 7 * hash01(k, 2, 52)) * (0.6 if n == 1 else 1.0)
            q = ip((c[0] + math.cos(a) * r * 1.3, c[1] + math.sin(a) * r * (0.9 if n == 1 else 0.5) + (n - 1) * 2.5 * (r / 6) ** 2))
            FX.put([q], ("O5", "O4", "J3")[k % 3] if n == 1 else ("O2", "J1", "O1")[k % 3])
    return Ls, info


def t_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1.0, 0.5)[i]
        fr.append((200, TP(B=(16.5, 22.0 + b * 0.4), sq=1.0 - 0.03 * b, sac=0.25 + 0.35 * b, open=0.0,
                           glow=2 if i == 2 else 1)))
    return fr


def t_crawl():
    fr = []
    keys = [  # (Bx, By, sq, tilt, ext, fr, fext, lift)
        (15.6, 22.6, 0.92, 2, 0.0, -0.8, 0.0, 0.0),
        (16.4, 21.4, 1.06, -6, 0.65, 0.0, 0.3, 0.0),
        (17.6, 20.4, 1.1, -3, 1.0, 1.4, 0.8, 0.0),
        (18.0, 21.4, 1.0, 5, 0.6, 2.0, 0.1, 0.0),
        (17.2, 22.6, 0.9, 4, 0.2, 0.6, 0.0, 0.0),
        (16.4, 22.4, 0.95, 1, 0.0, -0.4, 0.0, 0.0),
    ]
    for i, (bx, by, sq, tl, e, fr_, fe, lf) in enumerate(keys):
        fr.append((90, TP(B=(bx, by), sq=sq, tilt=tl, ext=e, fr=fr_, fext=fe, lift=lf, sac=0.3 + 0.1 * (i % 2))))
    return fr


def t_spit():
    return [
        (130, TP(B=(16.2, 22.2), sq=0.96, sac=0.4, tilt=2)),
        (150, TP(B=(15.4, 21.2), sq=1.04, tilt=-12, sac=0.8, glow=1, fr=-0.6)),
        (170, TP(B=(14.8, 20.8), sq=1.08, tilt=-16, sac=1.25, glow=2, eye=2, fr=-1.0, open=0.1)),
        (380, TP(B=(14.6, 20.6), sq=1.1, tilt=-18, sac=1.6, glow=2, eye=2, fr=-1.2, open=0.15)),
        (80, TP(B=(17.8, 22.2), sq=0.94, tilt=8, sac=0.9, glow=2, eye=2, open=0.8, glob=True, fr=1.0, wind=3)),
        (60, TP(B=(18.4, 22.4), sq=0.92, tilt=10, sac=0.35, glow=1, eye=2, open=1.0, spray=1, fr=1.2, wind=2)),
        (120, TP(B=(17.4, 22.2), sq=0.96, tilt=4, sac=0.25, open=0.7, spray=2, drip=3, fr=0.8)),
        (160, TP(B=(16.8, 22.0), sq=0.98, tilt=1, sac=0.25, open=0.25, drip=4)),
        (180, TP(B=(16.5, 22.0), sac=0.3)),
    ]


def t_hurt():
    return [(80, TP(B=(14.8, 21.2), sq=1.1, tilt=-14, sac=0.9, glow=2, eye=2, open=0.5, ext=0.3)),
            (140, TP(B=(15.8, 22.2), sq=0.94, tilt=-4, sac=0.5, open=0.2))]


def t_death():
    return [
        (90, TP(B=(14.6, 21.0), sq=1.12, tilt=-18, sac=1.1, glow=2, eye=2, open=0.8, ext=0.5)),
        (100, TP(B=(15.0, 19.6), tilt=-34, sq=1.08, sac=1.3, glow=2, eye=2, open=0.7, ext=0.9, fext=1.0)),
        (110, TP(B=(16.0, 16.0), tilt=-8, flip=True, sac=1.3, glow=2, eye=0, open=0.5, curl=0.2, twitch=1.0,
                 splat=1, snap=SPIT_L[:-1])),
        (120, TP(B=(16.0, 16.0), tilt=-8, flip=True, sac=0.35, glow=0, eye=0, open=0.4, curl=0.45, twitch=1.0,
                 splat=2, snap=SPIT_L[:-1])),
        (140, TP(B=(16.0, 16.0), tilt=-8, flip=True, sac=0.25, glow=0, eye=0, open=0.35, curl=0.75, twitch=0.5,
                 snap=SPIT_L[:-1])),
        (700, TP(B=(16.0, 16.0), tilt=-8, flip=True, sac=0.2, glow=0, eye=0, open=0.3, curl=1.0,
                 snap=SPIT_L[:-1])),
    ]


def build_spitter():
    K.setup(40, 32)
    anims, infos = render_anims("bog_spitter", SPIT_L, draw_spitter,
                                [("idle", t_idle), ("crawl", t_crawl), ("spit", t_spit), ("hurt", t_hurt),
                                 ("death", t_death)], sway_key="B")
    meta = {"native": 1, "frame": [40, 32], "anchor": [17, 32],
            "hurtbox": hurtbox(anims, ["Body", "Head", "Sac"], inset=(1, 1, 1)),
            "attacks": {},
            "spawn": {"spit": {"frame": 5, "at": spawn_pt(infos["spit"][5]["mouth"])}}}
    export("bog_spitter", SPIT_L, anims, meta)
    return meta


# =========================================================================== 3. MIRE WITCH
WITCH_L = ["Pole", "BackArm", "Robe", "Head", "Lantern", "FrontArm", "FX"]
M_NEU = dict(P=(20.0, 38.0), C=(23.6, 27.2), Hd=(29.6, 24.6), hup=(0.55, -1), hb=(17.6, 36.0), hf=(28.6, 35.0),
             pang=-58.0, lsw=0.0, glow=1.0, eye=1, rot=0.0, piv=(0, 0), fallen=False, hem=0, pole="hand",
             wind=0.0, flash=False, orbit=0, puff=0, heap=0.0, feet=(0.0, 0.0), lantern=None, jaw=0.0)
MP = mk(M_NEU)
POLE = dict(lo=-5.0, hi=17.0)


def lantern_pix(L, FX, top, glow, fi):
    """Iron cage lantern hanging from `top` (frame coords). Returns its centre."""
    c = (top[0], top[1] + 3.6)
    cq = ip(c)
    pix = {}
    for dy in range(-3, 4):
        for dx in range(-2, 3):
            q = (cq[0] + dx, cq[1] + dy)
            if abs(dx) == 2 or dy in (-3, 3):
                pix[q] = "I3" if (dx < 0 or dy == -3) else "I2"
            else:
                r = math.hypot(dx + 0.3, dy - 0.4)
                if glow <= 0.05:
                    pix[q] = "N1" if r > 1 else "J0"
                else:
                    hot = glow + 0.4 * math.sin(fi * 2.1)
                    pix[q] = ("J4" if r < 0.9 and hot > 1.2 else "J3") if r < 1.2 else ("J2" if dy < 2 else "O3")
    for dy in (-2, -1, 0, 1, 2):
        pix[(cq[0], cq[1] + dy)] = pix.get((cq[0], cq[1] + dy)) if glow > 1.6 else "I2" if dy % 2 else pix[(cq[0], cq[1] + dy)]
    pix.update({(cq[0] - 1, cq[1] - 4): "I3", (cq[0], cq[1] - 4): "I4", (cq[0] + 1, cq[1] - 4): "I2",
                (cq[0], cq[1] - 5): "I3", (cq[0], cq[1] + 4): "I2"})
    L.fixed(pix)
    if glow > 0.6:   # soft sickly halo (a few alpha-free dither dots)
        for k in range(10 + int(glow * 4)):
            a = k * 2 * math.pi / (10 + int(glow * 4)) + fi * 0.4
            r = 3.6 + glow * 1.0 + (k % 2) * 0.8
            q = ip((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
            if q not in pix and (k + fi) % 2 == 0:
                FX.put([q], "J2" if glow > 1.8 else "J1")
    return c


def draw_witch(p, fi, sw):
    Ls = {n: Layer(n) for n in WITCH_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(1.8, -ln + 1.4), F(-2.0, -ln + 2.0)
    info = {"hit": set()}
    floor = K.H - 1.0
    # ---- gnarled pole (behind the body), lantern dangling from its crook
    if p["pole"] == "hand":
        g, a = R.T(p["hf"]), R.A(p["pang"])
    else:
        g, a = p["pole"]
    ca, sa = dirv(a)
    s0 = (g[0] + ca * POLE["lo"], g[1] + sa * POLE["lo"])
    s1 = (g[0] + ca * POLE["hi"], g[1] + sa * POLE["hi"])
    px_, py_ = -sa, ca
    if py_ < 0:
        px_, py_ = -px_, -py_
    pts = []
    for i in range(9):
        t = i / 8
        wob = math.sin(t * 9.0 + 1.3) * 0.6
        pts.append((s0[0] + (s1[0] - s0[0]) * t + px_ * wob, s0[1] + (s1[1] - s0[1]) * t + py_ * wob))
    crook = [s1, (s1[0] + ca * 1.6 + px_ * 1.2, s1[1] + sa * 1.6 + py_ * 1.2),
             (s1[0] + ca * 2.0 + px_ * 3.0, s1[1] + sa * 2.0 + py_ * 3.0)]
    Pl = Ls["Pole"]
    ppix = {}
    for i, q in enumerate(polyline(pts)):
        ppix[q] = "W4" if i % 6 == 0 else "W3"
    for q in polyline(crook):
        ppix[q] = "W3"
    for k in (0.3, 0.62):                                    # knots + a dead twig
        q = ip(lerp(s0, s1, k))
        ppix[(q[0] + 1, q[1])] = "W2"
    tw = lerp(s0, s1, 0.7)
    for q in line(tw, (tw[0] - px_ * 2.4 + ca * 1.4, tw[1] - py_ * 2.4 + sa * 1.4))[1:]:
        ppix[q] = "W2"
    Pl.fixed(ppix)
    hang = crook[-1]
    # ---- back arm
    arm(R, Ls["BackArm"], shB, p["hb"], 4.6, 4.8, 1.6, 1.8, "N", bias=-1, fist="E", fist_r=1.0, pref=(-1, 0.5))
    # ---- robe: hunched moss-sodden bell with a ragged, dragging hem
    Rb = Ls["Robe"]
    sx = -sw * 0.6
    if not p["fallen"]:
        hem = floor + 0.4 - p["heap"] * 0.5
        spread = 7.6 + p["heap"] * 4.0
        pts = [F(-4.2, -ln - 0.2), F(2.6, -ln - 0.8), F(4.2, -3.0), F(4.6, 0.6),
               (P[0] + spread + sx * 0.3, hem - 1.6)]
        n = 10
        for i in range(n + 1):
            t = i / n
            x = P[0] + spread + 0.4 + sx * 0.3 - (2 * spread + 1.6) * t + sx * 0.4 * t
            d = (0.9 + hash01(i, p["hem"], 3) * 0.6) if (i + p["hem"]) % 2 == 0 else -0.4
            pts.append((x, hem + d))
        pts += [(P[0] - spread - 1.2 + sx * 0.7, hem - 1.8), F(-5.0, 1.0), F(-5.2, -3.0)]
        m = R.mask(pts)
    else:
        m = R.mask([F(-4.2, -ln - 0.2), F(2.6, -ln - 0.8), F(4.6, 3.0), F(6.0, 11.0), F(-1.0, 13.5), F(-6.0, 10.0),
                    F(-5.0, 1.0)])
    Rb.paint(n_plate(m, 2.2, (-0.05, 0.0), 1.0, fold=lambda x, y: (0.65 * math.sin((x - P[0] - sw * 0.2) * 1.05)
                                                                  * min(1.0, max(0.0, (y - P[1] + 5) / 9)), 0)),
             "N", bias=0)
    hump = R.dome(Rb, F(-2.4, -ln + 1.2), 5.6, 5.0, "N", bias=0, tilt=(-0.05, -0.1))
    m = m | hump
    Rb.decal([q for q in m if hash01(q[0] - int(P[0]), q[1] - int(P[1]), 7) < 0.1], ("D", 2))
    ys = [q[1] for q in m]
    ybot = max(ys) if ys else 0
    Rb.decal([q for q in m if q[1] >= ybot - 1 and not p["fallen"]], ("H", 2))                  # mud-soaked hem
    Rb.decal([q for q in m if q[1] == ybot - 2 and hash01(q[0], 1, 9) < 0.5 and not p["fallen"]], ("H", 3))
    R.dline(Rb, F(-4.6, -2.2), F(4.2, -2.6), ("L", 3))                                          # rope belt
    R.decal(Rb, [F(3.4, -2.0), F(3.6, -1.0), F(3.2, 0.2)], ("L", 2))
    R.dline(Rb, F(2.4, -ln + 1.0), F(3.8, -3.2), ("N", 1))
    # little charms dangling from the belt: bone + a rot-orange mushroom
    Rb.fixed({R.pt(F(-1.6, -1.2)): "B4", R.pt(F(-1.6, -0.2)): "B3", R.pt(F(1.0, -1.0)): "O3", R.pt(F(1.0, -0.2)): "X4"})
    # bare clawed toes peeking under the hem
    if not p["fallen"]:
        for k, off in enumerate(p["feet"]):
            x = P[0] + 3.0 + k * 3.2 + off
            Rb.fixed({(int(x), int(floor)): "E3" if k else "E4", (int(x) + 1, int(floor)): "E2" if k else "E3"})
    # moss beards hanging from the hump & sleeves
    for k, (a_, b_, L_) in enumerate(((-6.4, -ln + 3.0, 7.0), (-4.0, -ln + 6.0, 5.0), (-6.0, -4.0, 6.0))):
        s_ = R.T(F(a_, b_))
        strand(Rb, s_, (s_[0] - sw * 0.4 - 0.5, s_[1] + L_), 0.5, "N3" if k % 2 else "D2")
    # ---- head: moss hood, long hooked-nose hag face, stringy hair, one sickly eye
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    jw = p["jaw"]
    hood = [G(-4.6, 4.8), G(-5.0, -0.6), G(-3.8, -4.4), G(-0.6, -5.8), G(3.2, -5.0), G(4.8, -2.8), G(3.8, -2.2),
            G(1.8, -3.0), G(0.0, -2.2), G(-0.8, 0.6), G(-0.6, 5.0)]
    hm = R.plate(Hl, hood, "N", bevel=1.3, tilt=(-0.1, -0.2), strength=1.2, bias=0)
    Hl.decal([q for q in hm if hash01(q[0], q[1], 31) < 0.12], ("D", 3))
    for k, (dx, L_) in enumerate(((-0.6, 6.0), (0.2, 4.5), (-1.4, 7.5))):   # stringy grey hair
        s_ = R.T(G(dx, -1.2))
        strand(Hl, s_, (s_[0] - sw * 0.3 - 0.8 + k * 0.2, s_[1] + L_), 0.3, "P3" if k != 1 else "P4")
    face = [G(0.4, -2.4), G(2.8, -2.6), G(3.8, -1.0), G(6.8, 2.0), G(6.0, 2.6), G(4.2, 1.8), G(4.4, 2.8 + jw),
            G(3.2, 4.4 + jw), G(1.2, 4.2 + jw), G(0.4, 1.0)]
    R.plate(Hl, face, "E", bevel=1.0, tilt=(-0.25, -0.1), bias=1, ao=0)
    R.dline(Hl, G(0.6, -2.4), G(3.4, -2.4), ("N", 1))                         # hood shadow on the brow
    R.decal(Hl, [G(5.2, 1.0)], ("V", 3))                                     # nose wart
    R.dline(Hl, G(2.4, 2.9 + jw * 0.5), G(4.0, 2.9 + jw * 0.5), "OUT")
    if jw > 0.6:
        R.decal(Hl, [G(3.0, 3.5 + jw * 0.5)], ("F", 1))
    R.decal(Hl, [G(3.7, 3.0 + jw * 0.5)], "B5")                               # snaggle tooth
    if p["eye"]:
        e = R.pt(G(2.4, -1.0))
        FX.put([e], "J3" if p["eye"] == 1 else "J4")
        FX.put([(e[0] - 1, e[1])], "OUT")
        if p["eye"] > 1:
            FX.put([(e[0] + 1, e[1] - 1), (e[0] - 1, e[1])], "J2")
    # ---- lantern on its chain
    lsw = p["lsw"]
    if p["lantern"] is None:
        ch_end = (hang[0] + math.sin(math.radians(lsw)) * 3.0, hang[1] + math.cos(math.radians(lsw)) * 3.0)
        Ls["Lantern"].fill(line(hang, ch_end)[1:], "I2", noout=True)
        lc = lantern_pix(Ls["Lantern"], FX, ch_end, p["glow"], fi)
    else:
        lc = lantern_pix(Ls["Lantern"], FX, p["lantern"], p["glow"], fi)
    info["lantern"] = lc
    # ---- near sleeve + bony claw on the pole
    Fa = Ls["FrontArm"]
    arm(R, Fa, shF, p["hf"], 4.6, 4.8, 1.8, 2.1, "N", bias=0, fist="E", fist_r=1.2, pref=(-1, 0.6))
    hq = R.pt(p["hf"])
    Fa.fixed({(hq[0] + 1, hq[1] + 1): "E4", (hq[0] + 1, hq[1] - 1): "E3"})
    sl = R.T(lerp(shF, p["hf"], 0.55))
    strand(Fa, sl, (sl[0] - sw * 0.3, sl[1] + 4.5), 0.3, "D2")
    # ---- fx: gathering rot motes, release flash, smoke puff
    if p["orbit"]:
        n = p["orbit"]
        for k in range(4 + n * 2):
            ang = fi * 1.1 + k * 2 * math.pi / (4 + n * 2)
            r = 10.0 - n * 2.0 + (k % 2) * 1.5
            q = ip((lc[0] + math.cos(ang) * r, lc[1] + math.sin(ang) * r * 0.8))
            FX.put([q], "J3" if k % 2 else "O3")
            FX.put([ip((lc[0] + math.cos(ang - 0.35) * (r + 1.4), lc[1] + math.sin(ang - 0.35) * (r + 1.4) * 0.8))],
                   "J1")
    if p["flash"]:
        c = ip(lc)
        for ang in range(0, 360, 45):
            L_ = 7 if ang % 90 == 0 else 4
            FX.put(line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_)),
                   "J4" if ang % 90 == 0 else "J3")
        FX.put(list(mask_disc((c[0] + .5, c[1] + .5), 2.6)), "J4")
        FX.put([c], "Y3")
    if p["puff"]:
        for k in range(8):
            q = ip((lc[0] - 1 + math.cos(k * 0.9) * (2 + p["puff"]), lc[1] - 3 - p["puff"] * 1.6 + math.sin(k * 1.3) * 1.8))
            FX.put([q], "N4" if k % 2 else "N3")
    return Ls, info


def m_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((190, MP(C=(23.6, 27.2 + b * 0.6), Hd=(29.6 + b * 0.2, 24.6 + b * 0.8), hf=(28.6, 35.0 + b * 0.4),
                           hb=(17.6, 36.0 + b * 0.5), hem=i, lsw=(0, 8, 0, -8)[i], glow=(1.0, 1.2, 0.9, 1.1)[i])))
    return fr


def m_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s)
        fr.append((140, MP(P=(20.2, 38.0 + b * 0.4), C=(24.0 + 0.4 * c, 27.0 + b), Hd=(30.2 + 0.5 * c, 24.4 + b),
                           hf=(28.8 + 0.4 * c, 34.6 + b), hb=(17.8 - 0.8 * c, 35.6 + b), pang=-60 + 3 * c, hem=i,
                           lsw=-12 + 8 * s, glow=1.0 + 0.15 * s, feet=(1.6 * c, -1.6 * c), wind=-1.5)))
    return fr


def m_cast():
    raise_ = dict(C=(22.6, 26.8), Hd=(28.2, 23.6), hup=(0.35, -1), hf=(27.0, 26.0), pang=-78, hb=(16.0, 30.0))
    cock = dict(P=(19.6, 38.2), C=(21.4, 27.4), Hd=(26.4, 24.6), hup=(0.15, -1), hf=(23.6, 25.0), pang=-112,
                hb=(15.2, 29.6))
    return [
        (140, MP(hf=(28.0, 36.0), pang=-50, lsw=20, glow=1.2, jaw=0.3)),
        (150, MP(**raise_, lsw=-10, glow=1.6, eye=2, orbit=1, jaw=0.6)),
        (160, MP(**dict(raise_, hf=(27.6, 24.6), pang=-82), lsw=4, glow=2.0, eye=2, orbit=2, jaw=0.8)),
        (160, MP(**dict(raise_, hf=(27.4, 24.4), pang=-86), lsw=-4, glow=2.4, eye=2, orbit=3, jaw=0.9)),
        (170, MP(**cock, lsw=30, glow=2.7, eye=2, orbit=3, jaw=1.0)),
        (380, MP(**dict(cock, C=(21.0, 27.6), Hd=(25.8, 24.8), pang=-116), lsw=36, glow=3.0, eye=2, orbit=3,
                 jaw=1.2)),
        (70, MP(P=(20.6, 38.0), C=(25.0, 27.8), Hd=(31.4, 26.0), hup=(0.7, -1), hf=(29.0, 32.0), pang=-52,
                hb=(18.0, 33.0), lsw=55, glow=0.4, eye=2, flash=True, wind=3, jaw=1.4)),
        (120, MP(P=(20.4, 38.0), C=(24.6, 27.6), Hd=(30.8, 25.6), hup=(0.65, -1), hf=(29.0, 32.4), pang=-54,
                 hb=(18.0, 34.0), lsw=40, glow=0.3, puff=1, jaw=0.8)),
        (160, MP(hf=(29.6, 33.0), pang=-44, lsw=-8, glow=0.6, puff=2, jaw=0.3)),
        (160, MP(hf=(28.8, 34.6), pang=-54, lsw=6, glow=0.9)),
    ]


def m_hurt():
    return [(80, MP(P=(19.2, 38.2), C=(21.6, 27.6), Hd=(26.6, 24.4), hup=(0.1, -1), hf=(26.4, 33.0), pang=-72,
                    hb=(15.0, 32.0), lsw=30, glow=1.6, eye=2, jaw=1.2)),
            (140, MP(P=(19.6, 38.0), C=(22.8, 27.2), Hd=(28.4, 24.4), hup=(0.4, -1), hf=(27.8, 34.4), pang=-62,
                     lsw=14, glow=1.2, jaw=0.4))]


def m_death():
    heap = dict(P=(19.6, 43.0), C=(22.8, 34.4), Hd=(28.6, 33.6), hup=(0.9, -1), hf=(27.0, 43.0), hb=(17.0, 44.0),
                heap=1.0, pole=((33.0, 54.6), 184), lantern=(38.0, 47.2), glow=0.5, eye=0, jaw=1.0)
    piv = (22.0, 48.0)
    return [
        (100, MP(P=(19.0, 38.2), C=(20.8, 27.8), Hd=(25.6, 24.2), hup=(0.0, -1), hf=(25.6, 32.0), pang=-80,
                 hb=(14.6, 31.0), lsw=40, glow=1.8, eye=2, jaw=1.4)),
        (140, MP(P=(19.4, 40.4), C=(22.4, 30.4), Hd=(28.0, 28.4), hup=(0.5, -1), hf=(27.8, 38.0), pang=-30,
                 hb=(16.8, 38.0), heap=0.4, lsw=-30, glow=1.2, eye=1, jaw=1.0)),
        (180, MP(**dict(heap, pole=((31.0, 51.0), 205), lantern=(37.0, 45.6), glow=0.9))),
        (120, MP(**heap, rot=30, piv=piv, snap=["BackArm", "Robe", "Head", "FrontArm"])),
        (130, MP(**dict(heap, glow=0.15), rot=58, piv=piv, fallen=True, snap=["BackArm", "Robe", "Head", "FrontArm"])),
        (700, MP(**dict(heap, glow=0.0, puff=2), rot=70, piv=piv, fallen=True,
                 snap=["BackArm", "Robe", "Head", "FrontArm"])),
    ]


def build_witch():
    K.setup(48, 56)
    anims, infos = render_anims("mire_witch", WITCH_L, draw_witch,
                                [("idle", m_idle), ("walk", m_walk), ("cast", m_cast), ("hurt", m_hurt),
                                 ("death", m_death)], loops=("idle", "walk"))
    meta = {"native": 1, "frame": [48, 56], "anchor": [21, 56],
            "hurtbox": hurtbox(anims, ["Robe", "Head"], inset=(2, 1, 2)),
            "attacks": {},
            "spawn": {"cast": {"frame": 6, "at": spawn_pt(infos["cast"][6]["lantern"])}}}
    export("mire_witch", WITCH_L, anims, meta)
    return meta


# =========================================================================== 4. GILDED SENTINEL
SENT_L = ["WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Roots", "Head", "Weapon", "FrontArm", "FX"]
HAL = dict(butt=-11.0, head=17.0, tip=24.5)
S_NEU = dict(P=(25.5, 41.5), C=(26.6, 28.8), Hd=(28.2, 19.6), hup=(0.08, -1), fb=(20.0, 63), ff=(31.5, 63),
             hf=(35.0, 41.0), hb=None, wang=-80, wl="Weapon", rot=0.0, piv=(0, 0), legs_fixed=False, kb=None,
             kf=None, eye=1, sap=1.0, smear=None, lines=None, weapon="hand", wind=0.0, fallen=False, crack=0,
             side=1)
SNP = mk(S_NEU)


def halberd_px(grip, ang, side=1):
    """Halberd in frame coords: dark shaft, gold-steel axe blade (on `side`), back hook and top spike.
    Returns (pix, blade_set, spike_tip)."""
    ca, sa = dirv(ang)
    vx, vy = -sa * side, ca * side            # blade side
    P_ = lambda u, v: (grip[0] + ca * u + vx * v, grip[1] + sa * u + vy * v)
    pix, blade = {}, set()
    for q in line(P_(HAL["butt"], 0), P_(HAL["head"] + 0.5, 0)):
        pix[q] = "W3"
    pix[ip(P_(HAL["butt"], 0))] = "U3"
    for u in (-0.8, 0.8, HAL["head"] - 1.2):
        pix[ip(P_(u, 0))] = "U2"                                    # grip wraps / collar
    # spike
    sp = line(P_(HAL["head"], 0), P_(HAL["tip"], 0))
    for i, q in enumerate(sp):
        pix[q] = "S5" if i > len(sp) - 3 else "S4"
        blade.add(q)
    for q in line(P_(HAL["head"], 0.8), P_(HAL["tip"] - 2.5, 0.6)):
        pix.setdefault(q, "S3")
        blade.add(q)
    # crescent axe blade
    ax = poly_mask([P_(HAL["head"] - 5.0, 0.6), P_(HAL["head"] - 6.6, 3.2), P_(HAL["head"] - 6.8, 5.6),
                    P_(HAL["head"] - 4.0, 5.0), P_(HAL["head"] - 1.0, 5.2), P_(HAL["head"] + 1.4, 5.8),
                    P_(HAL["head"] + 1.2, 3.0), P_(HAL["head"] + 0.4, 0.6)])
    for q in ax:
        # edge = outermost band in v
        dx, dy = q[0] + .5 - grip[0], q[1] + .5 - grip[1]
        v = dx * vx + dy * vy
        pix[q] = "S5" if v > 4.6 else "U4" if v > 3.3 else "U3" if v > 1.8 else "U2"
        blade.add(q)
    # back hook
    for q in line(P_(HAL["head"] - 2.0, -0.6), P_(HAL["head"] - 0.2, -3.2)):
        pix[q] = "U3"
        blade.add(q)
    pix[ip(P_(HAL["head"] + 0.2, -3.4))] = "U4"
    # gold root-filigree on the socket
    pix[ip(P_(HAL["head"] - 2.8, 0.4))] = "Y1"
    return pix, blade, P_(HAL["tip"], 0)


def root(L, pts, r0, r1, mat="X", bias=0, sap=1.0, R=ID, seed=0):
    """Gnarled root: capsules along a polyline (frame/model coords through R), sap-lit crack down the middle."""
    n = len(pts) - 1
    allm = set()
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        allm |= R.cap(L, a, b, ra, rb, mat, bias=bias, ao=0)
    if sap > 0.2:
        cr = []
        for i in range(n):
            if i % 2 == seed % 2 or r0 > 1.2:
                cr += line(R.T(pts[i]), R.T(lerp(pts[i], pts[i + 1], 0.7)))
        L.decal([q for q in cr if q in allm and hash01(q[0], q[1], 81 + seed) < 0.7],
                "Y2" if sap > 1.5 else "Y1" if sap > 0.8 else "U3")
    return allm


def draw_sentinel(p, fi, sw):
    Ls = {n: Layer(n) for n in SENT_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    LR = ID if p["legs_fixed"] else R
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = basis(P, up)
    shF, shB = F(1.4, -ln + 2.0), F(-3.0, -ln + 2.4)
    hB, hF = F(-2.4, 0.8), F(2.4, 0.8)
    if p["legs_fixed"]:
        hB, hF = R.T(hB), R.T(hF)
    info = {"hit": set()}
    floor = K.H - 1
    sap = p["sap"]
    # ---- halberd
    if p["weapon"] == "hand":
        g, a = R.T(p["hf"]), R.A(p["wang"])
        pix, blade, tip = halberd_px(g, a, p["side"])
        ca, sa = dirv(a)
        hand2 = (p["hf"][0] - ca * 6.0, p["hf"][1] - sa * 6.0) if p["hb"] is None else p["hb"]
    else:
        pix, blade, tip = halberd_px(*p["weapon"], p["side"])
        hand2 = p["hb"]
    pix = {q: c for q, c in pix.items() if q[1] <= floor}
    blade = {q for q in blade if q[1] <= floor}
    Ls[p["wl"]].fixed(pix)
    info["hit"] |= blade
    info["tip"] = tip
    # ---- back arm
    hbk = hand2 or F(-3.4, -2.0)
    arm(R, Ls["BackArm"], shB, hbk, 7.6, 7.8, 2.0, 1.9, "K", bias=-1, fore="U", fist_r=1.7, pref=(-1, 0.6))
    R.dome(Ls["BackArm"], add(shB, (0.2, -0.6)), 3.2, 2.8, "U", bias=-1)
    # ---- legs: gold greaves, porcelain knee-cops
    for nm, hip, ft, bias, kn in (("BackLeg", hB, p["fb"], -1, p["kb"]), ("FrontLeg", hF, p["ff"], 0, p["kf"])):
        k = leg(LR, Ls[nm], hip, ft, 10.4, 10.6, 2.8, 2.3, "K", bias=bias, boot="U", flen=4.2, heel=2.2, boot_h=3.4,
                knee=kn)
        th = lerp(hip, k, 0.45)
        LR.cap(Ls[nm], lerp(hip, k, 0.1), lerp(hip, k, 0.8), 2.9, 2.6, "U", bias=bias, ao=1)       # cuisse
        LR.dome(Ls[nm], add(k, (0.6, 0.0)), 2.4, 2.2, "S", bias=bias)
        LR.dline(Ls[nm], add(k, (-1.2, 2.6)), add(k, (1.6, 2.4)), ("U", 1 + bias))
    # a root coils round the back shin
    kb_ = p["kb"] or ik(hB, (p["fb"][0], p["fb"][1] - 1.4), 10.4, 10.6, (1, -0.1))
    rp = [lerp(kb_, p["fb"], t) for t in (0.1, 0.45, 0.8)]
    root(Ls["BackLeg"], [add(rp[0], (2.4, 0.4)), add(rp[1], (-2.0, 0.2)), add(rp[2], (2.2, 0.0)),
                         (p["fb"][0] - 3.4, floor - 0.2)], 1.1, 0.7, bias=-1, sap=sap * 0.6, R=LR, seed=1)
    # ---- torso: gold cuirass, porcelain tabard, faulds
    Bd = Ls["Body"]
    faulds = [F(-5.0, -2.0), F(4.6, -2.0), F(5.4, 4.2), F(-5.6, 4.2)]
    R.plate(Bd, faulds, "U", bevel=1.5, tilt=(0.0, 0.2), bias=-1)
    for k in range(2):
        R.dline(Bd, F(-5.4, 0.2 + k * 2.0), F(5.0, 0.2 + k * 2.0), ("U", 1))
    torso = [F(-5.0, -1.0), F(-5.8, -ln + 3.0), F(-4.0, -ln - 1.2), F(2.6, -ln - 1.8), F(5.4, -ln + 1.0),
             F(5.6, -ln + 5.4), F(4.4, -1.0)]
    tm = R.plate(Bd, torso, "U", bevel=2.8, tilt=(-0.35, -0.15), strength=1.35)
    R.dline(Bd, F(1.2, -ln - 1.4), F(1.8, -2.0), ("U", 5))
    R.dline(Bd, F(2.0, -ln - 1.2), F(2.6, -2.0), ("U", 2))
    R.dline(Bd, F(-4.2, -ln - 1.0), F(2.6, -ln - 1.6), ("S", 4))            # porcelain gorget rim
    # porcelain tabard with gold hem
    tx = F(1.2, -2.2)
    if not p["fallen"]:
        tb = [add(tx, (-2.8, 0)), add(tx, (3.0, 0)), add(tx, (3.6 - sw * 0.4, 11.0)), add(tx, (0.2 - sw * 0.6, 12.6)),
              add(tx, (-3.2 - sw * 0.4, 11.0))]
        tbm = R.plate(Bd, tb, "S", bevel=1.4, tilt=(-0.2, 0.0), fold=lambda x, y: (0.4 * math.sin(x * 1.2), 0))
        ybot = max(q[1] for q in tbm)
        Bd.decal([q for q in tbm if q[1] >= ybot - 1], ("U", 3))
        R.decal(Bd, [add(tx, (0.2, 4.0)), add(tx, (0.2, 5.0)), add(tx, (-0.8, 4.6)), add(tx, (1.2, 4.6))], ("U", 3))
    R.cap(Bd, F(0.2, -ln - 0.8), add(Hd, (-0.6, 4.4)), 2.2, 2.0, "S", bias=-1)   # porcelain neck
    # ---- roots bursting through the armour (chest seam, shoulder, back)
    Rt = Ls["Roots"]
    cs = F(2.4, -ln + 4.4)
    root(Rt, [cs, F(4.6, -ln + 2.0), F(4.2, -ln - 1.6), F(1.6, -ln - 3.6), F(-1.6, -ln - 3.8)], 1.9, 0.7,
         sap=sap, R=R, seed=2)
    root(Rt, [F(-4.0, -ln + 5.0), F(-6.6, -ln + 2.4), F(-7.4 - sw * 0.2, -ln - 1.0), F(-6.0 - sw * 0.3, -ln - 3.4)],
         1.7, 0.6, sap=sap, R=R, seed=3)
    root(Rt, [F(-3.6, -1.0), F(-6.4, 1.6), F(-7.0 - sw * 0.3, 5.0)], 1.1, 0.5, sap=sap * 0.8, R=R, seed=4)
    for q in (R.pt(cs), R.pt(F(-4.0, -ln + 5.0))):                     # sap-lit wounds in the plate
        Rt.fixed({q: "Y2" if sap > 1.5 else "Y1", (q[0] + 1, q[1]): "Y0" if sap > 0.5 else "U2"})
    # ---- head: gold great-helm, porcelain face-mask with a kintsugi crack, crown of root-thorns
    Hl = Ls["Head"]
    G = basis(Hd, p["hup"])
    for k, (bx, h, lean) in enumerate(((-2.8, 6.0, -1.4), (-0.6, 8.0, -0.4), (1.6, 6.8, 0.8), (3.4, 4.4, 1.6))):
        root(Hl, [G(bx, -4.4), G(bx + lean * 0.5, -4.4 - h * 0.55), G(bx + lean, -4.4 - h)], 1.0, 0.35,
             sap=sap * 0.7, R=R, seed=5 + k)
    helm = [G(-4.2, 4.4), G(-4.6, -1.6), G(-3.4, -4.8), G(2.2, -5.4), G(4.4, -3.2), G(4.8, 1.2), G(3.8, 4.6)]
    R.plate(Hl, helm, "U", bevel=2.0, tilt=(-0.3, -0.2), strength=1.3)
    mask = [G(0.4, -3.6), G(3.6, -3.4), G(4.6, -0.8), G(4.4, 2.6), G(3.2, 4.4), G(0.6, 4.2), G(-0.2, 0.4)]
    mm = R.plate(Hl, mask, "S", bevel=1.2, tilt=(-0.45, -0.25), strength=1.0, bias=1)
    R.dline(Hl, G(0.8, -1.2), G(4.4, -1.2), "OUT")                          # eye slit
    R.dline(Hl, G(1.8, 2.6), G(3.8, 2.6), ("S", 2))                          # closed serene mouth
    crack = [G(2.2, -3.4), G(2.8, -2.2), G(2.2, -0.6), G(3.0, 0.8), G(2.6, 2.0)] if not p["crack"] else \
        [G(2.2, -3.4), G(2.8, -2.2), G(2.2, -0.6), G(3.0, 0.8), G(2.6, 2.0), G(1.4, 3.6), G(0.4, 4.2)]
    Hl.decal([q for q in polyline([R.T(c) for c in crack]) if q in mm], ("U", 4))
    R.dline(Hl, G(-4.0, 4.0), G(3.6, 4.2), ("U", 3))
    if p["eye"]:
        for k, d in enumerate(((1.8, -1.2), (3.8, -1.2))):
            FX.put([R.pt(G(*d))], ("Y2" if k == 0 else "Y1") if p["eye"] == 1 else "Y3")
        if p["eye"] > 1:
            e = R.pt(G(3.8, -1.2))
            FX.put([(e[0] + 1, e[1]), (e[0] + 2, e[1] - 1), (e[0] + 3, e[1] - 1)], "Y1")
    # ---- near arm: gold vambrace, layered pauldron, porcelain elbow
    Fa = Ls["FrontArm"]
    el = arm(R, Fa, shF, p["hf"], 7.6, 7.8, 2.2, 2.0, "K", bias=0, fore="U", fist_r=1.9, pref=(-1, 0.7))
    R.dome(Fa, el, 1.6, 1.6, "S", ao=0)
    for k, (dx, dy, rx, ry) in enumerate(((0.6, 2.6, 3.6, 2.2), (0.2, 0.4, 4.2, 2.8), (-0.2, -1.6, 4.4, 3.2))):
        c = add(shF, (dx, dy))
        m = R.dome(Fa, c, rx, ry, "U" if k else "S", tilt=(0.05, 0.1))
        Fa.decal([q for q in m if (q[0], q[1] + 1) not in m], ("U", 2) if k else ("U", 3))
    # ---- fx
    if p["smear"]:
        sm = p["smear"]
        hot = swept(FX, R.T(sm["g0"]), sm["a0"], R.T(p["hf"]), R.A(p["wang"]), 9, HAL["tip"] + 0.5, hw=1.4,
                    mid=sm.get("mid"), start=sm.get("start", 0.0), pal="holy", exclude=blade,
                    taper=sm.get("taper", 0.72), clip_y=floor)
        info["hit"] |= hot
    if p["lines"]:
        l = p["lines"]
        hot = thrust_lines(FX, R.T(p["hf"]), R.A(p["wang"]), l.get("u0", 4), l.get("u1", 20),
                           l.get("offs", (-2.4, 2.4, -4.2)), pal="holy", flash=l.get("flash"))
        info["hit"] |= {q for q in hot if q[0] > R.T(p["hf"])[0] + 8}
    return Ls, info


def n2_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1, 0.5)[i]
        fr.append((240, SNP(P=(25.5, 41.5 + b * 0.3), C=(26.6, 28.8 + b), Hd=(28.2, 19.6 + b),
                            hf=(35.0, 41.0 + b * 0.6), wang=-80 + b, sap=1.0 + 0.3 * b)))
    return fr


def n2_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s = math.cos(ph), math.sin(ph)
        ff = (26.4 + 6.0 * c, 63 - max(0.0, -s) * 3.2)
        fb = (25.2 - 6.0 * c, 63 - max(0.0, s) * 3.2)
        bob = 1.3 * abs(c)
        fr.append((150, SNP(P=(25.8, 41.0 + bob), C=(27.2, 28.4 + bob), Hd=(28.9, 19.2 + bob), ff=ff, fb=fb,
                            hf=(35.4 + 0.8 * c, 40.6 + bob), wang=-78 + 3 * c)))
    return fr


def n2_sweep():
    WB = dict(wl="WeaponBack")
    back = dict(P=(24.6, 42.2), C=(23.6, 29.8), Hd=(24.4, 20.6), hup=(-0.15, -1), fb=(16.5, 63), ff=(32.5, 63))
    lunge = dict(P=(28.4, 43.4), C=(31.4, 31.2), Hd=(33.8, 22.6), hup=(0.4, -1), fb=(18.5, 63), ff=(38.0, 63))
    low = dict(P=(25.0, 44.6), C=(23.8, 32.6), Hd=(24.6, 23.6), hup=(-0.1, -1), fb=(17.5, 63), ff=(33.5, 63))
    rise = dict(P=(28.0, 42.0), C=(30.6, 29.6), Hd=(32.6, 20.4), hup=(0.3, -1), fb=(19.0, 63), ff=(37.0, 63))
    return [
        (150, SNP(P=(25.2, 42.0), C=(26.0, 29.4), Hd=(27.4, 20.2), hf=(33.0, 36.0), wang=-45)),
        (170, SNP(**back, hf=(26.4, 27.4), wang=-150, **WB)),
        (420, SNP(**dict(back, C=(23.0, 30.2), Hd=(23.6, 21.0)), hf=(25.2, 26.6), wang=-160, eye=2, sap=2.0, **WB)),
        (60, SNP(**lunge, hf=(39.4, 38.6), wang=8, wind=4, side=1,
                 smear=dict(g0=(25.2, 26.6), a0=-160, mid=(34.0, 22.0), start=0.18))),
        (90, SNP(**lunge, hf=(38.4, 43.0), wang=48, wind=3, smear=dict(g0=(39.4, 38.6), a0=8, taper=0.5))),
        (150, SNP(**dict(lunge, C=(30.4, 31.6), Hd=(32.6, 23.0)), hf=(34.0, 45.0), wang=110, **WB)),
        (170, SNP(**low, hf=(27.4, 45.0), wang=160, side=-1, **WB)),
        (300, SNP(**dict(low, C=(23.2, 33.0), Hd=(23.8, 24.0)), hf=(26.6, 45.4), wang=166, side=-1, eye=2, sap=2.0,
                  **WB)),
        (60, SNP(**rise, hf=(38.6, 36.0), wang=-24, wind=4, side=-1,
                 smear=dict(g0=(26.6, 45.4), a0=166, mid=(38.0, 52.0), start=0.12))),
        (90, SNP(**rise, hf=(36.4, 29.0), wang=-66, wind=3, side=-1, smear=dict(g0=(38.6, 36.0), a0=-24, taper=0.5))),
        (180, SNP(P=(26.6, 42.0), C=(28.2, 29.4), Hd=(30.0, 20.2), fb=(19.0, 63), ff=(34.0, 63), hf=(35.6, 36.0),
                  wang=-72, side=-1)),
        (200, SNP(P=(25.8, 41.6), C=(27.0, 28.9), Hd=(28.6, 19.7), hf=(35.0, 40.6), wang=-80)),
    ]


def n2_thrust():
    lvl = dict(P=(24.2, 42.4), C=(23.0, 30.0), Hd=(24.0, 21.0), hup=(-0.1, -1), fb=(15.5, 63), ff=(31.0, 63))
    lunge = dict(P=(29.6, 43.6), C=(33.0, 31.6), Hd=(35.6, 23.2), hup=(0.45, -1), fb=(18.0, 63), ff=(40.0, 63))
    return [
        (140, SNP(P=(25.0, 42.0), C=(25.6, 29.6), Hd=(27.0, 20.4), hf=(31.0, 37.0), wang=-8, side=1)),
        (160, SNP(**lvl, hf=(26.0, 36.4), wang=-4, side=1)),
        (170, SNP(**dict(lvl, C=(22.2, 30.2), Hd=(23.0, 21.2)), hf=(22.6, 35.6), wang=-2, eye=2, sap=1.6, side=1)),
        (380, SNP(**dict(lvl, P=(23.8, 42.6), C=(21.8, 30.4), Hd=(22.6, 21.4)), hf=(21.8, 35.4), wang=-2, eye=2,
                  sap=2.0, side=1)),
        (60, SNP(**lunge, hf=(39.6, 37.0), wang=1, wind=4, side=1,
                 lines=dict(u0=-6, u1=18, offs=(-2.4, 2.6, -4.4), flash=HAL["tip"] + 0.5))),
        (110, SNP(**lunge, hf=(39.8, 37.2), wang=1, side=1, lines=dict(u0=4, u1=18, offs=(-2.4, 2.6)))),
        (170, SNP(**dict(lunge, P=(28.0, 43.0), C=(30.6, 30.8), Hd=(32.8, 22.0)), hf=(34.0, 37.6), wang=-6, side=1)),
        (180, SNP(P=(26.2, 42.2), C=(27.4, 29.6), Hd=(29.0, 20.4), fb=(18.5, 63), ff=(33.5, 63), hf=(33.6, 38.6),
                  wang=-40, side=1)),
        (200, SNP(P=(25.6, 41.6), C=(26.8, 28.9), Hd=(28.4, 19.7), hf=(35.0, 40.8), wang=-78)),
    ]


def n2_hurt():
    return [(80, SNP(P=(24.4, 41.8), C=(23.4, 29.2), Hd=(23.8, 20.2), hup=(-0.35, -1), hf=(33.0, 40.0), wang=-100,
                     eye=2, sap=2.0)),
            (150, SNP(P=(25.0, 41.6), C=(25.6, 29.0), Hd=(26.8, 19.8), hup=(-0.1, -1), hf=(34.2, 40.8), wang=-88))]


def n2_death():
    KN = dict(P=(24.0, 50.0), C=(26.4, 37.6), Hd=(29.2, 28.4), hup=(0.35, -1), kb=(21.0, 61.6), kf=(31.0, 61.8),
              fb=(11.5, 63), ff=(21.5, 63), eye=0, sap=0.6, crack=1)
    plant = ((38.0, 44.0), -96)
    piv = (26.0, 50.0)
    fall = []
    for rot, ms in ((22, 130), (50, 120), (72, 900)):
        fall.append((ms, SNP(**dict(KN, C=(26.0, 37.4), Hd=(28.6, 28.0), sap=0.2), rot=rot, piv=piv,
                             legs_fixed=True, fallen=True, weapon=((40.0, 61.4), 178), hf=(33.0, 50.0),
                             hb=(29.0, 51.0), snap=["BackArm", "Body", "Roots", "Head", "FrontArm"])))
    return [
        (130, SNP(P=(24.0, 41.8), C=(22.8, 29.4), Hd=(22.8, 20.6), hup=(-0.5, -1), hf=(32.0, 38.0), wang=-110,
                  eye=2, sap=2.2, crack=1)),
        (150, SNP(P=(24.6, 45.4), C=(26.4, 33.0), Hd=(28.8, 24.0), hup=(0.2, -1), fb=(18.5, 63), ff=(32.0, 63),
                  weapon=plant, hf=(37.4, 40.6), hb=(35.8, 43.0), eye=1, sap=1.6, crack=1)),
        (220, SNP(**KN, weapon=plant, hf=(37.2, 41.4), hb=(35.4, 44.0))),
        (320, SNP(**dict(KN, C=(26.6, 38.2), Hd=(30.0, 29.6), hup=(0.6, -1), sap=1.2), weapon=plant,
                  hf=(37.2, 42.0), hb=(35.4, 44.4))),
        (140, SNP(**dict(KN, C=(27.4, 38.8), Hd=(31.4, 30.8), hup=(0.7, -1), sap=0.8), weapon=((42.0, 50.0), -60),
                  hf=(36.0, 46.0), hb=(34.0, 47.0))),
    ] + fall


def build_sentinel():
    K.setup(64, 64)
    anims, infos = render_anims("gilded_sentinel", SENT_L, draw_sentinel,
                                [("idle", n2_idle), ("walk", n2_walk), ("sweep", n2_sweep), ("thrust", n2_thrust),
                                 ("hurt", n2_hurt), ("death", n2_death)])
    meta = {"native": 1, "frame": [64, 64], "anchor": [26, 64],
            "hurtbox": hurtbox(anims, ["Body", "Head", "BackLeg", "FrontLeg"], inset=(2, 0, 2)),
            "attacks": {
                "sweep": {"windows": [
                    {"active": [3, 4], "hit": hit_rect(infos, "sweep", [3, 4], x_min=30)},
                    {"active": [8, 9], "hit": hit_rect(infos, "sweep", [8, 9], x_min=30)}]},
                "thrust": {"active": [4, 5], "hit": hit_rect(infos, "thrust", [4, 5], x_min=34)}}}
    export("gilded_sentinel", SENT_L, anims, meta)
    return meta


# =========================================================================== 5. ROOT SPAWN
SPAWN_L = ["BackLegs", "Body", "Sprout", "FrontLegs", "FX"]
R_NEU = dict(B=(15.0, 15.0), swell=1.0, sq=1.0, tilt=0.0, glow=1, ph=0.0, gait=0.0, lift=1.2, legs="walk",
             eye=1, sprout=1.0, shake=0.0, blast=0, crumble=0.0, wind=0.0, body=True)
RP = mk(R_NEU)
CRACKS = [[(-4.2, -1.0), (-2.0, -0.4), (-1.0, 1.4), (1.2, 1.8), (3.4, 3.0)],
          [(-2.4, -3.8), (-1.4, -2.0), (0.8, -1.8), (2.0, -0.4), (4.4, -0.8)],
          [(-4.0, 2.4), (-2.2, 3.4), (-0.6, 3.0)],
          [(0.2, -4.2), (0.6, -2.8)]]


def draw_rootspawn(p, fi, sw):
    Ls = {n: Layer(n) for n in SPAWN_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    B = (p["B"][0] + p["shake"] * (1 if fi % 2 else -1), p["B"][1])
    s = p["swell"]
    floor = K.H - 1.0
    R = Rig(-p["tilt"], (B[0], floor), sx=s, sy=s * p["sq"])
    info = {"hit": set()}
    g = p["glow"]
    GL = {0: ("X1", "X1", "X2"), 1: ("U3", "U4", "Y1"), 2: ("Y0", "Y1", "Y2"), 3: ("Y1", "Y2", "Y3")}[g]
    # ---- rootlet legs
    if p["body"]:
        for side, nm in ((1, "BackLegs"), (0, "FrontLegs")):
            L = Ls[nm]
            for i, rx in enumerate((-3.2, 0.0, 3.0)):
                root_ = (B[0] + rx + (0.8 if side else 0), B[1] + 3.0)
                ph = p["ph"] + i * 2.1 + side * math.pi
                spread = (-4.6, 0.4, 4.8)[i] * (0.8 if side else 1.0)
                if p["legs"] == "walk":
                    fx_ = root_[0] + spread + p["gait"] * math.cos(ph)
                    fy_ = floor - max(0.0, math.sin(ph)) * p["lift"]
                    kn = (root_[0] + spread * 0.6 + p["gait"] * 0.3 * math.cos(ph), root_[1] + 0.6 - (0.5 if side else 0))
                else:                                       # curled (dead)
                    cu = p["legs"]
                    fx_ = root_[0] + spread * (0.9 - 0.7 * cu)
                    fy_ = floor - 0.4 * cu
                    kn = (root_[0] + spread * 0.7, root_[1] + 2.0 + 1.2 * cu)
                pts = [R.T(root_), R.T(kn), (fx_ if s == 1 else R.T((fx_, fy_))[0], min(floor, R.T((fx_, fy_))[1]))]
                pix = {}
                for q in polyline(pts[:2]):
                    pix[q] = "X2" if side else "X3"
                for q in polyline(pts[1:]):
                    pix[q] = "X1" if side else "X2"
                pix[ip(pts[1])] = "X3" if side else "X4"
                pix[ip(pts[2])] = "U3" if g and not side else "X2"
                L.fixed(pix)
    # ---- body: a knot of pale root, gold light leaking from the cracks
    Bd = Ls["Body"]
    if p["body"]:
        m = R.dome(Bd, B, 5.8, 4.8, "X", bias=0, tilt=(0.0, -0.05))
        if p["crumble"]:
            m = {q for q in m if hash01(q[0], q[1], 91) > p["crumble"] * (0.4 + 0.6 * (1 - (q[1] - B[1] + 5) / 10))}
            for q in list(Bd.px):
                if q not in m:
                    del Bd.px[q]
        # woven root bands
        for k, (a, b) in enumerate((((-5.2, 1.6), (3.0, -4.2)), ((-3.6, -3.4), (5.4, 2.0)), ((-5.0, -1.2), (2.2, 4.4)))):
            pts = line(R.T(add(B, a)), R.T(add(B, b)))
            Bd.decal([q for q in pts if q in m], ("X", 4 if k != 1 else 1))
        for k, cr in enumerate(CRACKS):
            pts = polyline([R.T(add(B, c)) for c in cr])
            Bd.decal([q for q in pts if q in m], GL[1] if k < 2 else GL[0])
            if g >= 2:
                Bd.decal([q for i, q in enumerate(pts) if q in m and i % 3 == 1], GL[2])
        if g >= 3:
            Bd.decal([q for q in m if hash01(q[0], q[1], 7 + fi) < 0.12], "Y2")
        # face: two sap-lit eye holes
        if p["eye"]:
            for d in ((3.0, -0.6), (4.6, -0.2)):
                q = R.pt(add(B, d))
                Bd.fixed({q: "Y3" if p["eye"] > 1 or g >= 2 else "Y2"})
            Bd.fixed({R.pt(add(B, (3.8, 0.8))): "OUT"})
        info["hit"] |= set(Bd.px)
    info["core"] = R.T(B)
    # ---- sprout: two tendrils and a gold leaf on the crown
    if p["body"] and p["sprout"] > 0:
        Sp = Ls["Sprout"]
        top = add(B, (-0.6, -4.4))
        for k, (dx, h) in enumerate(((-1.6, 4.4), (1.4, 3.2))):
            tip = add(top, (dx - sw * 0.4 + math.sin(fi * 1.3 + k) * 0.4, -h * p["sprout"]))
            pts = [R.T(add(top, (dx * 0.3, 0))), R.T(lerp(add(top, (dx * 0.3, 0)), tip, 0.6)), R.T(tip)]
            Sp.fixed({q: "X4" if k else "X3" for q in polyline(pts)})
            tq = ip(pts[-1])
            if k == 0:
                Sp.fixed({tq: "U5" if g else "U2", (tq[0] + 1, tq[1]): "U4" if g else "U1",
                          (tq[0] + 1, tq[1] - 1): "U3" if g else "U1", (tq[0] + 2, tq[1] - 1): "U4" if g else "U1"})
            else:
                Sp.fixed({tq: "Y2" if g >= 2 else "U4" if g else "U1"})
    # ---- fx: gathering light, blast
    if g >= 2 and p["body"] and not p["blast"]:
        c = R.T(B)
        for k in range(6 + 2 * g):
            ang = fi * 0.9 + k * 2 * math.pi / (6 + 2 * g)
            r = 9.0 - g * 1.4 + (k % 2)
            q = ip((c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * r * 0.8))
            FX.put([q], "Y2" if k % 2 else "Y1")
    if p["blast"]:
        c = (B[0] + 0.5, B[1] - 0.5)
        st = p["blast"]
        pts = set()
        if st == 1:
            disc_glow(FX, c, 6.2, ("Y3", "Y3", "Y3", "Y2", "U5", "U4"))
            for ang in range(0, 360, 30):
                L_ = 13 if ang % 60 == 0 else 9
                seg = line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_ * 0.8))
                FX.put(seg, "Y3" if ang % 60 == 0 else "U5")
                pts |= set(seg)
            ring = [q for q in mask_disc(c, 10.5, 8.5) if q not in mask_disc(c, 9.0, 7.2)]
            FX.put([q for q in ring if hash01(q[0], q[1], 3) < 0.7], "U4")
        else:
            ring = [q for q in mask_disc(c, 14.5, 11.5) if q not in mask_disc(c, 12.6, 10.0)]
            FX.put([q for q in ring if hash01(q[0], q[1], 4) < 0.55], "U3")
            ring2 = [q for q in mask_disc(c, 7.0, 5.5) if q not in mask_disc(c, 5.6, 4.4)]
            FX.put([q for q in ring2 if hash01(q[0], q[1], 5) < 0.5], "U5")
            for k in range(7):
                a = 2 * math.pi * k / 7 + 0.4
                FX.put([ip((c[0] + math.cos(a) * 2.6, c[1] + math.sin(a) * 2.2 - 1))], "Y2" if k % 2 else "S5")
            pts |= set(ring) | set(ring2)
        for k in range(10):                                  # root shards flung outward
            a = 2 * math.pi * hash01(k, 1, 97)
            r = (4 + 5 * hash01(k, 2, 98)) * (1.0 if st == 1 else 1.7)
            a0 = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.8 + (st - 1) * 2)
            a1 = (a0[0] + math.cos(a) * 2, a0[1] + math.sin(a) * 1.6)
            FX.put(line(a0, a1), "X4" if k % 2 else "X3")
        for dx in range(-12, 13):
            if hash01(dx, 6, 99) < (0.8 if st == 1 else 0.5):
                FX.put([(int(c[0]) + dx, int(floor))], ("Y2" if abs(dx) < 6 else "U4") if st == 1 else "U3")
        info["hit"] |= pts | set(FX.px)
    return Ls, info


def r_idle():
    fr = []
    for i in range(4):
        b = (0, 0.5, 1.0, 0.5)[i]
        fr.append((180, RP(B=(15.0, 15.0 + b * 0.3), sq=1.0 - 0.04 * b, ph=i * math.pi / 2, gait=0.3, lift=0.3,
                           glow=2 if i == 2 else 1, sprout=1.0 - 0.1 * b)))
    return fr


def r_crawl():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        fr.append((70, RP(B=(15.2, 14.8 + 0.5 * abs(math.sin(ph * 1.5))), ph=ph, gait=2.0, lift=1.6,
                          tilt=1.5 * math.sin(ph), sq=1.0 + 0.04 * math.cos(ph * 2))))
    return fr


def r_burst():
    return [
        (150, RP(B=(15.0, 15.4), sq=0.94, gait=0.2, glow=1)),
        (140, RP(B=(15.0, 14.8), swell=1.12, glow=2, gait=0.3, lift=0.3, eye=2)),
        (140, RP(B=(15.0, 14.6), swell=1.24, glow=2, shake=0.5, gait=0.4, lift=0.4, eye=2)),
        (120, RP(B=(15.0, 14.4), swell=1.36, glow=3, shake=0.6, gait=0.4, lift=0.4, eye=2)),
        (300, RP(B=(15.0, 14.2), swell=1.46, glow=3, shake=0.8, gait=0.2, lift=0.2, eye=2, sprout=0.6)),
        (70, RP(B=(15.0, 14.6), blast=1, body=False)),
        (140, RP(B=(15.0, 14.6), blast=2, body=False)),
    ]


def r_hurt():
    return [(80, RP(B=(13.8, 15.2), tilt=-14, sq=1.08, glow=2, eye=2, ph=1, gait=2.0, lift=1.4)),
            (130, RP(B=(14.6, 15.0), tilt=-5, glow=1, ph=2, gait=1.0, lift=0.6))]


def r_death():
    return [
        (90, RP(B=(13.8, 15.2), tilt=-16, sq=1.08, glow=2, eye=2, ph=1, gait=2.2, lift=1.6)),
        (100, RP(B=(14.6, 16.4), tilt=-6, sq=0.85, glow=1, legs=0.3, eye=1)),
        (110, RP(B=(15.0, 17.6), tilt=4, sq=0.7, glow=1, legs=0.6, eye=0, sprout=0.6)),
        (120, RP(B=(15.0, 18.2), tilt=6, sq=0.62, glow=0, legs=0.85, eye=0, sprout=0.4, crumble=0.25)),
        (130, RP(B=(15.0, 18.4), tilt=6, sq=0.58, glow=0, legs=1.0, eye=0, sprout=0.3, crumble=0.5)),
        (700, RP(B=(15.0, 18.6), tilt=6, sq=0.55, glow=0, legs=1.0, eye=0, sprout=0.0, crumble=0.62)),
    ]


def build_rootspawn():
    K.setup(32, 24)
    anims, infos = render_anims("root_spawn", SPAWN_L, draw_rootspawn,
                                [("idle", r_idle), ("crawl", r_crawl), ("burst", r_burst), ("hurt", r_hurt),
                                 ("death", r_death)], sway_key="B")
    meta = {"native": 1, "frame": [32, 24], "anchor": [15, 24],
            "hurtbox": hurtbox(anims, ["Body"], inset=(1, 0, 1)),
            "attacks": {"burst": {"active": [5, 6], "hit": hit_rect(infos, "burst", [5, 6])}},
            "self_destruct": "burst"}
    export("root_spawn", SPAWN_L, anims, meta)
    return meta


# =========================================================================== 6. SUN SERAPH
SERA_L = ["WingBack", "BackArm", "Robe", "Body", "Head", "FrontArm", "WingFront", "FX"]
A_NEU = dict(O=(24.0, 24.0), tilt=0.0, wing=-150.0, fold=0.0, eye=1, halo=1, crack=0, glow=1, tailph=0.0,
             hf=(6.0, 1.0), hb=(3.0, 2.0), orb=0, flash=False, lines=None, wind=0.0, drop=0.0, tail=1.0,
             wings=True, shatter=0.0, motes=True)
AP2 = mk(A_NEU)


def root_wing(R, L, FX, root_pt, ang, scale, bias, fold, glow, fi, far=False):
    """A wing of branching pale roots with sap-gold leaf buds at the tips (model coords through R)."""
    ca, sa = dirv(ang)
    k = scale * (1 - 0.45 * fold)
    main_len = 15.0 * k
    tip = (root_pt[0] + ca * main_len, root_pt[1] + sa * main_len)
    root(L, [root_pt, lerp(root_pt, tip, 0.35), lerp(root_pt, tip, 0.7), tip], 1.6 * scale, 0.45, bias=bias,
         sap=glow * (0.5 if far else 1.0), R=R, seed=11 if far else 12)
    tips = [tip]
    for t, da, ln_ in ((0.3, 34, 8.5), (0.52, 22, 8.0), (0.72, 12, 6.0), (0.45, -18, 6.5), (0.8, -12, 4.0)):
        a2 = ang + da * (1 - 0.5 * fold)
        b0 = lerp(root_pt, tip, t)
        b1 = (b0[0] + math.cos(math.radians(a2)) * ln_ * k, b0[1] + math.sin(math.radians(a2)) * ln_ * k)
        bm = lerp(b0, b1, 0.5)
        bm = (bm[0] - sa * 0.6, bm[1] + ca * 0.6)
        L.fixed({q: ("X2" if far else "X3") for q in polyline([R.T(b0), R.T(bm), R.T(b1)])})
        tips.append(b1)
    for j, t_ in enumerate(tips):
        q = R.pt(t_)
        c1 = ("U3" if far else "U4") if glow else "X2"
        c2 = ("Y1" if glow >= 2 else "U4" if not far else "U3") if glow else "X3"
        L.fixed({q: c2, (q[0] + 1, q[1]): c1, (q[0], q[1] - 1): c1})
        if glow >= 2 and not far and (j + fi) % 2 == 0:
            FX.put([(q[0] + 1, q[1] - 1)], "Y2")
    return tips


def draw_seraph(p, fi, sw):
    Ls = {n: Layer(n) for n in SERA_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    O = (p["O"][0], p["O"][1] + p["drop"])
    R = Rig(p["tilt"], O)
    info = {"hit": set()}
    g = p["glow"]
    Ob = lambda a, b: (O[0] + a, O[1] + b)
    sh = Ob(-3.2, -4.6)
    # ---- halo (behind everything)
    if p["halo"]:
        hc = Ob(-0.8, -11.4)
        ring = [q for q in mask_disc(R.T(hc), 5.6, 5.8) if q not in mask_disc(R.T(hc), 4.6, 4.8)]
        if p["halo"] == 2:                       # shattered: only fragments
            ring = [q for q in ring if hash01(q[0] // 2, q[1] // 2, 61) < 0.35]
        Ls["WingBack"].fixed({q: ("Y2" if g >= 2 else "U5") if (q[0] + q[1]) % 3 == 0 else ("U4" if g else "U2")
                              for q in ring})
    # ---- wings
    if p["wings"]:
        root_wing(R, Ls["WingBack"], FX, add(sh, (1.6, -0.8)), R.A(p["wing"]) + 18 - p["tilt"], 0.95, -1, p["fold"],
                  g, fi, far=True)
    # ---- back arm
    hb = Ob(*p["hb"])
    arm(R, Ls["BackArm"], Ob(-1.4, -5.6), hb, 4.2, 4.4, 1.2, 1.0, "S", bias=-1, fist_r=1.0, pref=(-1, 0.4))
    # ---- robe: porcelain-white shroud, gold hem, trailing into dangling roots
    Rb = Ls["Robe"]
    if p["tail"] > 0:
        tl = p["tail"]
        n = 12
        spine = []
        for i in range(n + 1):
            t = i / n
            x = O[0] - 0.4 - 6.5 * t * tl + sw * 0.35 * t + math.sin(p["tailph"] + t * 4.0) * 1.3 * t
            y = O[1] + 0.4 + 13.5 * t * tl
            spine.append((x, y))
        up_, dn = [], []
        for i, (x, y) in enumerate(spine):
            t = i / n
            wd = 3.8 + 2.6 * t
            up_.append((x + wd * 0.9, y))
            dn.append((x - wd, y + (1.2 if i % 3 == 1 and t > 0.4 else 0)))
        m = R.mask(up_ + dn[::-1])
        if tl < 1:
            m = {q for q in m if hash01(q[0], q[1], 70 + fi) < 0.3 + 0.7 * tl ** 2}
        Rb.paint(n_plate(m, 1.6, (0.0, 0.0), 1.0,
                         fold=lambda x, y: (0.5 * math.sin((x - O[0]) * 1.1 + p["tailph"] * 0.5), 0.0)), "S", bias=1)
        ybot = max(q[1] for q in m) if m else 0
        Rb.decal([q for q in m if (q[0], q[1] + 1) not in m and q[1] > O[1] + 4], ("U", 3))
        # dangling roots under the hem
        for k in range(3):
            base = lerp(spine[-1], spine[-3], 0.3 * k)
            base = (base[0] + (k - 1) * 2.4, base[1] + 0.6)
            L_ = (5.0, 7.0, 4.0)[k] * tl
            end = (base[0] - 1.0 + math.sin(p["tailph"] + k * 1.7) * 1.6 + sw * 0.3, base[1] + L_)
            pts = [R.T(base), R.T(lerp(base, end, 0.5)), R.T(end)]
            Rb.fill(polyline(pts), "X3" if k != 1 else "X4", noout=False)
    # ---- body: hollow porcelain torso, sap light through a broken chest
    Bd = Ls["Body"]
    R.cap(Bd, Ob(-0.4, 1.0), Ob(0.0, -2.0), 2.6, 3.2, "S", bias=1)
    cm = R.dome(Bd, Ob(0.2, -3.4), 4.0, 3.8, "S", bias=1, tilt=(-0.15, -0.15))
    R.dline(Bd, Ob(-3.4, 0.4), Ob(3.0, 0.2), ("U", 3))                      # gold girdle
    R.decal(Bd, [Ob(1.0, 0.6)], ("U", 4))
    hole = R.T(Ob(1.4, -3.4))
    hp = {}
    for q in mask_disc(hole, 1.7, 1.9):
        d = math.hypot(q[0] + .5 - hole[0], q[1] + .5 - hole[1])
        hp[q] = ("Y3" if d < 0.9 else "Y2") if g >= 2 else ("Y2" if d < 0.9 else "Y1") if g else ("U1" if d < 1 else "S1")
    Bd.fixed(hp)
    crk = [Ob(1.4, -3.4), Ob(2.6, -5.4), Ob(2.2, -6.6)] + ([Ob(1.4, -3.4), Ob(-0.8, -1.8), Ob(-2.2, -2.6)]
                                                          if p["crack"] else [])
    Bd.decal([q for q in polyline([R.T(c) for c in crk[:3]]) if q in cm], "U4" if g else "S2")
    if p["crack"]:
        Bd.decal([q for q in polyline([R.T(c) for c in crk[3:]]) if q in cm], "Y1" if g else "S1")
    # ---- head: blank porcelain mask, gold-tear kintsugi, thorn crown
    Hl = Ls["Head"]
    Hc = Ob(1.2, -10.4)
    R.cap(Hl, Ob(0.4, -6.4), Ob(0.8, -8.0), 1.2, 1.2, "S", bias=-1)
    hm = R.dome(Hl, Hc, 3.2, 3.8, "S", bias=1, tilt=(-0.2, -0.1))
    for k, d in enumerate(((1.4, -0.8), (3.0, -0.6))):
        e = R.pt(add(Hc, d))
        Hl.fixed({e: "OUT", (e[0] + (1 if k else -1) * 0, e[1] + 1): "OUT"})
        if p["eye"]:
            FX.put([e], ("Y2" if k else "Y1") if p["eye"] == 1 else "Y3")
    Hl.decal([q for q in polyline([R.T(add(Hc, (1.4, 0.4))), R.T(add(Hc, (1.0, 2.2))), R.T(add(Hc, (1.6, 3.2)))])
              if q in hm], ("U", 4))
    if p["crack"] > 1:
        Hl.decal([q for q in polyline([R.T(add(Hc, (-1.8, -3.0))), R.T(add(Hc, (0.2, -1.2))), R.T(add(Hc, (-0.4, 1.0)))])
                  if q in hm], "Y1" if g else "S1")
    for k, (dx, h, lean) in enumerate(((-1.6, 3.2, -0.8), (0.2, 4.0, 0.0), (1.8, 3.0, 0.8))):
        pts = [R.T(add(Hc, (dx, -3.2))), R.T(add(Hc, (dx + lean * 0.5, -3.2 - h * 0.6))), R.T(add(Hc, (dx + lean, -3.2 - h)))]
        Hl.fixed({q: "X4" if k == 1 else "X3" for q in polyline(pts)})
        Hl.fixed({ip(pts[-1]): "U4" if g else "X4"})
    info["hit"] |= set(Hl.px) | set(Bd.px)
    # ---- near arm
    hf = Ob(*p["hf"])
    arm(R, Ls["FrontArm"], Ob(1.6, -5.6), hf, 4.2, 4.4, 1.3, 1.1, "S", bias=0, fist_r=1.1, pref=(-1, 0.5))
    R.dline(Ls["FrontArm"], lerp(Ob(1.6, -5.6), hf, 0.62), lerp(Ob(1.6, -5.6), hf, 0.7), ("U", 3))   # gold bracelet
    info["hand"] = R.T(hf)
    # ---- near wing
    if p["wings"]:
        root_wing(R, Ls["WingFront"], FX, sh, R.A(p["wing"]) - p["tilt"], 1.12, 0, p["fold"], g, fi)
    # ---- fx: light orb, motes, flash, dive streaks
    if p["orb"]:
        n = p["orb"]
        c = R.T(Ob(*p.get("orbat", (7.0, -12.0))))
        disc_glow(FX, c, 1.2 + n * 0.9, ("Y3", "Y3", "Y2", "U5", "U4")[:2 + n])
        for k in range(4 + 2 * n):
            ang = fi * 1.1 + k * 2 * math.pi / (4 + 2 * n)
            r = 9.0 - n * 1.4 + (k % 2)
            FX.put([ip((c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * r * 0.8))], "Y2" if k % 2 else "U5")
        info["orb"] = c
    if p["flash"]:
        c = ip(R.T(hf))
        c = (c[0] + 2, c[1])
        for ang in range(0, 360, 45):
            L_ = 7 if ang % 90 == 0 else 4
            FX.put(line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_)),
                   "Y3" if ang % 90 == 0 else "U5")
        FX.put(list(mask_disc((c[0] + .5, c[1] + .5), 2.4)), "Y3")
        info["flash"] = c
    if p["motes"] and not p["orb"]:
        for k in range(3):
            t = ((fi * 0.37 + k * 0.33) % 1.0)
            q = ip((O[0] - 5 - t * 6 + k * 2, O[1] + 10 + t * 5 - k))
            FX.put([q], "Y2" if t < 0.3 else "U4" if t < 0.6 else "U2")
    if p["lines"]:
        (x0, y0), (x1, y1), offs = p["lines"]
        for i, o in enumerate(offs):
            seg = line((x0, y0 + o), (x1 - (i % 2) * 3, y1 + o))
            for j, q in enumerate(seg):
                FX.put([q], "Y3" if j > len(seg) * 0.7 else "U5" if j > len(seg) * 0.35 else "U3")
    if p["shatter"]:
        sh_ = p["shatter"]
        for k in range(12):
            a = 2 * math.pi * hash01(k, 1, 88)
            r = 2 + 9 * sh_ * hash01(k, 2, 89)
            q = ip((O[0] + math.cos(a) * r, O[1] - 4 + math.sin(a) * r * 0.8 + sh_ * 6 * hash01(k, 3, 90)))
            FX.put([q, (q[0] + 1, q[1])], "S5" if k % 3 == 0 else "S4" if k % 3 == 1 else "U4")
    return Ls, info


SFLAP = [-150, -128, -110, 176, 162, -178]


def a2_fly():
    fr = []
    for i in range(6):
        bob = (0.0, 0.4, 0.8, 1.0, 0.4, -0.3)[i]
        fr.append((100, AP2(O=(24.0, 24.0 - bob), wing=SFLAP[i], tailph=i * math.pi / 3, tilt=-2 + bob * 2,
                            hf=(5.4, 2.0 + bob * 0.4), hb=(2.6, 2.8))))
    return fr


def a2_cast():
    up = dict(hf=(6.4, -10.0), hb=(4.4, -10.6))
    return [
        (130, AP2(O=(24.0, 24.2), wing=-140, hf=(6.0, -3.0), hb=(3.6, -2.0), tailph=0.5, glow=1)),
        (140, AP2(O=(23.6, 24.6), wing=-122, **up, tailph=1.0, glow=2, orb=1, eye=2, tilt=-4)),
        (150, AP2(O=(23.4, 24.8), wing=-112, **up, tailph=1.5, glow=2, orb=1, eye=2, tilt=-6)),
        (150, AP2(O=(23.2, 25.0), wing=-104, **up, tailph=2.0, glow=2, orb=2, eye=2, tilt=-8)),
        (160, AP2(O=(23.0, 25.2), wing=-98, **up, tailph=2.5, glow=2, orb=3, eye=2, tilt=-10)),
        (360, AP2(O=(22.8, 25.4), wing=-94, hf=(6.0, -10.6), hb=(4.0, -11.2), tailph=3.0, glow=2, orb=3, eye=2,
                  tilt=-12)),
        (70, AP2(O=(25.0, 24.4), wing=178, hf=(11.0, -3.6), hb=(9.4, -2.6), tailph=3.6, glow=2, flash=True, eye=2,
                 tilt=8, wind=3)),
        (120, AP2(O=(24.6, 24.2), wing=170, hf=(10.0, -2.4), hb=(8.0, -1.6), tailph=4.2, glow=1, tilt=5)),
        (150, AP2(O=(24.2, 24.0), wing=-170, hf=(7.6, 0.0), hb=(5.0, 0.6), tailph=4.8, tilt=1)),
        (150, AP2(O=(24.0, 24.0), wing=-150, hf=(5.6, 1.6), hb=(2.8, 2.6), tailph=5.4)),
    ]


def a2_dive():
    return [
        (140, AP2(O=(23.0, 23.4), tilt=-18, wing=-120, eye=2, glow=2, hf=(5.0, -4.0), hb=(3.0, -3.0), tailph=0.5)),
        (240, AP2(O=(22.4, 23.6), tilt=-22, wing=-112, eye=2, glow=2, hf=(4.4, -5.0), hb=(2.6, -4.0), tailph=1.2)),
        (70, AP2(O=(26.0, 25.0), tilt=38, wing=-176, fold=0.6, eye=2, glow=2, hf=(9.6, -3.0), hb=(8.6, -2.0),
                 tailph=2.0, wind=4, lines=((7, 10), (20, 20), (-2, 1, 4)))),
        (90, AP2(O=(27.0, 26.4), tilt=42, wing=-172, fold=0.65, eye=2, glow=2, hf=(9.8, -2.6), hb=(8.8, -1.6),
                 tailph=2.8, wind=3, lines=((9, 13), (21, 22), (-1, 2)))),
        (150, AP2(O=(25.2, 25.0), tilt=6, wing=168, eye=1, hf=(6.6, 1.0), hb=(4.0, 1.6), tailph=3.5)),
        (150, AP2(O=(24.2, 24.2), tilt=-2, wing=-140, eye=1, hf=(5.6, 1.8), hb=(2.8, 2.6), tailph=4.2)),
    ]


def a2_hurt():
    return [(80, AP2(O=(22.6, 23.0), tilt=-18, wing=-160, fold=0.3, eye=2, crack=1, glow=2, hf=(3.0, -2.0),
                     hb=(1.0, -1.0), tailph=1)),
            (140, AP2(O=(23.4, 23.6), tilt=-8, wing=-140, eye=1, crack=1, hf=(4.6, 1.0), hb=(2.0, 2.0), tailph=2))]


def a2_death():
    return [
        (90, AP2(O=(22.6, 23.0), tilt=-20, wing=-164, fold=0.3, eye=2, crack=2, glow=2, halo=2, hf=(3.0, -3.0),
                 hb=(1.0, -2.0), tailph=1)),
        (120, AP2(O=(23.0, 24.0), tilt=-6, wing=170, fold=0.6, eye=1, crack=2, glow=1, halo=2, hf=(4.0, 2.0),
                  hb=(2.0, 3.0), tailph=2, tail=0.8, shatter=0.3)),
        (110, AP2(O=(23.4, 24.0), tilt=24, wing=150, fold=0.85, eye=0, crack=2, glow=0, halo=0, hf=(4.0, 4.0),
                  hb=(2.0, 4.0), tailph=3, tail=0.6, drop=5.0, shatter=0.6, motes=False)),
        (100, AP2(O=(23.8, 24.0), tilt=55, wing=140, fold=1.0, eye=0, crack=2, glow=0, halo=0, hf=(3.0, 5.0),
                  hb=(1.0, 5.0), tailph=4, tail=0.35, drop=10.0, shatter=0.9, motes=False)),
        (110, AP2(O=(24.2, 24.0), tilt=82, wing=130, fold=1.0, eye=0, crack=2, glow=0, halo=0, hf=(2.0, 5.0),
                  hb=(0.0, 5.0), tail=0.15, drop=15.0, motes=False)),
        (700, AP2(O=(24.6, 24.0), tilt=92, wing=130, fold=1.0, eye=0, crack=2, glow=0, halo=0, hf=(2.0, 5.0),
                  hb=(0.0, 5.0), tail=0.0, drop=16.0, motes=False, wings=False)),
    ]


def build_seraph():
    K.setup(48, 48)
    anims, infos = render_anims("sun_seraph", SERA_L, draw_seraph,
                                [("fly", a2_fly), ("cast", a2_cast), ("dive", a2_dive), ("hurt", a2_hurt),
                                 ("death", a2_death)], sway_key="O", loops=("fly",))
    meta = {"native": 1, "frame": [48, 48], "anchor": [24, 24], "flying": True,
            "hurtbox": [a + b for a, b in zip(hurtbox(anims, ["Body", "Head"], inset=(0, 0, 0), floor=False),
                                              [0, 0, 0, 9])],
            "attacks": {"dive": {"active": [2, 3], "hit": hit_rect(infos, "dive", [2, 3], floor=False)}},
            "spawn": {"cast": {"frame": 6, "at": spawn_pt(infos["cast"][6]["flash"])}}}
    export("sun_seraph", SERA_L, anims, meta)
    return meta


# =========================================================================== projectiles
def build_projectiles2():
    # ---- rot glob 16x16, flying right, centred on (8, 8): wobbling bile blob, orange rot core, dripping trail
    K.setup(16, 16)
    frames = []
    for i in range(4):
        core, glow = FXLayer("Core"), FXLayer("Trail")
        cx, cy = 9.5, 8.0
        wob = (0.0, 0.5, 0.0, -0.5)[i]
        for y in range(16):
            for x in range(16):
                dx, dy = x + .5 - cx, y + .5 - cy
                ex, ey = dx / (4.2 + wob), dy / (3.8 - wob)
                r = math.hypot(ex * (0.85 if dx < 0 else 1.0), ey)
                if r < 1.0:
                    rr = math.hypot(dx + 1.2, dy + 1.2)
                    if rr < 1.2:
                        c = "J4"
                    elif math.hypot(dx - 0.8 - wob * 0.4, dy - 0.6) < 1.1:
                        c = "O4"
                    elif math.hypot(dx - 0.8 - wob * 0.4, dy - 0.6) < 2.0:
                        c = "O2"
                    elif r < 0.55:
                        c = "J3"
                    elif r < 0.8:
                        c = "J2"
                    else:
                        c = "J1" if dy < 1 else "N3"
                    core.put([(x, y)], c)
                elif r < 1.22 and dy > -1:
                    glow.put([(x, y)], "N2")
        # outline for readability on bright backgrounds
        for (x, y) in list(core.px):
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if K.inb(*q) and q not in core.px and q not in glow.px:
                    glow.put([q], "OUT")
        # dripping trail blobs
        for k in range(4):
            t = (i * 0.25 + k * 0.27) % 1.0
            q = (int(cx - 5 - t * 7), int(cy + math.sin(k * 2.1 + i) * 2.0 + t * 2))
            glow.put([q], "J2" if t < 0.4 else "J1" if t < 0.7 else "N3")
            if t < 0.4:
                glow.put([(q[0] - 1, q[1])], "J1")
        frames.append((80, {"Trail": glow.image(), "Core": core.image()}))
    K.export("proj_rotglob", ["Trail", "Core"], [("fly", frames)], None, build=BUILD)
    # ---- light orb 12x12, flying right, centred on (6, 6): white-hot core, pulsing gold ring, spinning rays
    K.setup(12, 12)
    frames = []
    for i in range(4):
        core, ring = FXLayer("Core"), FXLayer("Glow")
        cx, cy = 6.0, 6.0
        pulse = (0.0, 0.35, 0.7, 0.35)[i]
        for y in range(12):
            for x in range(12):
                dx, dy = x + .5 - cx, y + .5 - cy
                r = math.hypot(dx, dy)
                if r < 1.5:
                    core.put([(x, y)], "Y3")
                elif r < 2.4:
                    core.put([(x, y)], "S5" if (x + y + i) % 3 else "Y2")
                elif r < 3.2:
                    core.put([(x, y)], "U5")
                elif r < 3.9 + pulse * 0.6 and hash01(x, y, i) < 0.75:
                    ring.put([(x, y)], "U4")
        for k in range(4):                       # rotating cross rays
            a = math.radians(i * 22.5 + k * 90)
            for L_ in (4.2, 5.2):
                q = ip((cx + math.cos(a) * L_, cy + math.sin(a) * L_))
                ring.put([q], "Y2" if L_ < 5 else "U4")
        for k in range(2):                       # trailing motes
            t = (i * 0.25 + k * 0.5) % 1.0
            ring.put([(int(cx - 4 - t * 2), int(cy + (k * 2 - 1) * (1 + t)))], "U3")
        frames.append((70, {"Glow": ring.image(), "Core": core.image()}))
    K.export("proj_lightorb", ["Glow", "Core"], [("fly", frames)], None, build=BUILD)
    return {"proj_rotglob": [16, 16], "proj_lightorb": [12, 12]}


# =========================================================================== main
ENEMIES = {
    "rot_hulk": build_hulk,
    "bog_spitter": build_spitter,
    "mire_witch": build_witch,
    "gilded_sentinel": build_sentinel,
    "root_spawn": build_rootspawn,
    "sun_seraph": build_seraph,
    "projectiles": build_projectiles2,
}


def verify(name):
    """Check the exported Aseprite json: tag names, frame counts, and the meta's frame indices."""
    path = os.path.join(K.asebuild.ASSETS, f"{name}.json")
    with open(path) as fh:
        js = json.load(fh)
    tags = {t["name"]: (t["from"], t["to"]) for t in js["meta"]["frameTags"]}
    spec = SPEC_FRAMES.get(name)
    if spec:
        assert list(tags) == list(spec), (name, list(tags))
        for t, n in spec.items():
            assert tags[t][1] - tags[t][0] + 1 == n, (name, t, tags[t])
        with open(os.path.join(K.asebuild.ASSETS, f"{name}_meta.json")) as fh:
            meta = json.load(fh)
        for t, a in meta.get("attacks", {}).items():
            for w in a.get("windows", [a]):
                assert 0 <= w["active"][0] <= w["active"][1] < spec[t], (name, t, w)
        for t, s in meta.get("spawn", {}).items():
            assert 0 <= s["frame"] < spec[t], (name, t, s)
    return {t: [a, b] for t, (a, b) in tags.items()}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    for name, fn in ENEMIES.items():
        if only and name not in only:
            continue
        meta = fn()
        print(name, json.dumps(meta))
        if BUILD:
            if name == "projectiles":
                for n in meta:
                    print("  tags", n, verify(n))
            else:
                print("  tags", verify(name))


if __name__ == "__main__":
    main()
