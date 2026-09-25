#!/usr/bin/env python3
"""Enemy generator v3 -- the Ashen Archives (docs/EXPANSION_PLAN.md), same contract as ART_SPEC section 4.

    python3 art/gen_enemies3.py                      build every enemy + projectile (Aseprite)
    python3 art/gen_enemies3.py --preview            previews + meta only (no Aseprite)
    python3 art/gen_enemies3.py --only grimoire,ink_hound [--preview]

Outputs per enemy <name>:
    art/<name>.aseprite, assets/<name>.png + .json, assets/<name>_meta.json,
    art/previews/<name>.png (4x, one row per tag),
    art/previews/<name>_hitbox.png (hurtbox green, hit rects red on active frames, spawn magenta, telegraph cyan)
Projectile: proj_inkbolt (16x12, fly 4 loop).

Ashen Archives look: violet-black ink and vellum, cold iron, pale-violet fire as the only glow.
    grimoire        40x32  flying chained tome, one violet eye in its pages, torn-page wings (anchor = body centre)
    ink_hound       56x32  lean skeletal hound of glossy ink, glyph-scar eyes
    lantern_monk    40x48  gaunt hooded monk, stitched mouth, iron lantern on a chain
    head_librarian  72x72  mini-boss: towering elite monk, page mask, keys, huge violet lantern-censer
All face RIGHT, feet on the bottom row (the grimoire floats). Method + helpers: enemy_kit.py.
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, Rig, ID, add, sub, lerp, ip, line, polyline, bezier, ik,  # noqa: E402
                       hash01, mask_disc, poly_mask, n_plate, n_dome, n_capsule, norm3, swept, dirv, bbox)
from PIL import Image, ImageDraw  # noqa: E402

BUILD = "--preview" not in sys.argv

# =========================================================================== palette (Archives)
NEW_RAMPS = {
    # violet-black robe cloth
    "Z": ["#07060c", "#0f0d18", "#191526", "#252036", "#362e4e", "#4f4671"],
    # glossy ink (top step = wet specular glint)
    "N": ["#050409", "#0c0a15", "#161226", "#231d3a", "#352c55", "#7a6ea6"],
    # aged vellum / parchment
    "H": ["#1f1a1a", "#3a322e", "#5e5345", "#887a63", "#b3a584", "#d8ccac"],
    # ashen, bloodless flesh / bone
    "E": ["#17141a", "#2a252c", "#453d44", "#655b5e", "#8b807e", "#b3a89e"],
    # pale violet fire (fixed colours)
    "J": ["#2b1c50", "#523799", "#8a69d8", "#c4b1ff", "#f2ecff"],
}
for _r, _cols in NEW_RAMPS.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"N": 0.9})
K.SMEAR.update({
    "violet": ["J4", "J3", "J2", "J1"],
    "ink": ["J3", "J2", "J1", "J0"],
})

SPEC_FRAMES = {
    "grimoire": dict(fly=6, cast=9, hurt=2, death=6),
    "ink_hound": dict(idle=4, run=6, pounce=8, hurt=2, death=6),
    "lantern_monk": dict(idle=4, walk=6, swing=10, hurt=2, death=6),
    "head_librarian": dict(idle=6, walk=8, swing=12, snuff=10, slam=10, stagger=4, death=10),
}


# =========================================================================== generic driver
def render_anims(name, layers, draw, anims, sway_key="C", loops=("idle", "walk", "fly", "run")):
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


def hit_rect(infos, tag, ks, floor=True, x_min=None, pad=0):
    pts = set()
    for k in ks:
        pts |= infos[tag][k].get("hit", set())
    r = bbox(pts, pad)
    if x_min is not None and r[0] < x_min:
        r[2] -= x_min - r[0]
        r[0] = x_min
    if floor:
        r[3] = K.H - r[1]
    return r


def hurtbox(anims, names, inset=(1, 0, 1), floor=True, frame=0):
    imgs = anims[0][1][frame][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs, names)
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2],
            (K.H if floor else y1) - (y0 + inset[1])]


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def spawn_pt(p):
    return [int(round(p[0])), int(round(p[1]))]


def rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def madd(p, *vs):
    x, y = p
    for v, k in vs:
        x += v[0] * k
        y += v[1] * k
    return (x, y)


def n_tube(pts, radii, flat=1.0, step=0.35):
    """Smooth variable-radius tube along a polyline (organic limbs, necks, tails, torsos)."""
    samp = []
    for (a, ra), (b, rb) in zip(zip(pts, radii), zip(pts[1:], radii[1:])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            samp.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ra + (rb - ra) * t))
    samp.append((pts[-1][0], pts[-1][1], radii[-1]))
    R = max(radii) + 1
    xs = [s[0] for s in samp]
    ys = [s[1] for s in samp]
    out = {}
    for y in range(int(min(ys) - R) - 1, int(max(ys) + R) + 2):
        for x in range(int(min(xs) - R) - 1, int(max(xs) + R) + 2):
            px, py = x + .5, y + .5
            best = None
            for sx, sy, r in samp:
                dx, dy = px - sx, py - sy
                if abs(dx) > r or abs(dy) > r:
                    continue
                q = (dx * dx + dy * dy) / (r * r)
                if q <= 1 and (best is None or q < best[0]):
                    best = (q, dx / r, dy / r)
            if best:
                nx, ny = best[1] * flat, best[2] * flat
                out[(x, y)] = norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
    return out


def tube(R, L, pts, radii, mat, bias=0, ao=1, flat=1.0, clip=None):
    return L.paint(n_tube([R.T(p) for p in pts], radii, flat), mat, bias, ao, clip)


def curve(pts, n=16):
    """Catmull-Rom through pts (smooth sleek lines)."""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def disc_glow(FX, c, r, pal, squash=1.0):
    n = len(pal)
    for q in mask_disc(c, r, r * squash):
        d = math.hypot(q[0] + .5 - c[0], (q[1] + .5 - c[1]) / squash) / max(r, 0.5)
        FX.put([q], pal[min(n - 1, int(d * n))])


def halo_dots(FX, c, r, n, fi, cols, skip=()):
    """Sparse dithered light halo (no alpha): a ring of dots that shimmers per frame."""
    for k in range(n):
        a = k * 2 * math.pi / n + fi * 0.37
        rr = r + (k % 3) * 0.9
        q = ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.9))
        if (k + fi) % 2 == 0 and q not in skip:
            FX.put([q], cols[k % len(cols)])


def chain_px(a, b, sag=0.0, c1="K4", c2="K2"):
    """Iron chain between a and b: alternating link pixels along a (sagging) curve."""
    pts = []
    for i in range(13):
        t = i / 12
        pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)))
    out = {}
    for i, q in enumerate(dict.fromkeys(polyline(pts))):
        out[q] = c1 if i % 2 == 0 else c2
    return out


def lantern_rim(layer, lc, radius, cols=("J1", "J0"), side=1):
    """Under-light: pixels facing the lantern within radius get a violet rim (the lantern is the only light)."""
    add_ = {}
    for (x, y), e in layer.px.items():
        dx, dy = lc[0] - (x + .5), lc[1] - (y + .5)
        d = math.hypot(dx, dy)
        if d > radius or d < 0.5:
            continue
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        facing = ((x + sx, y) not in layer.px and abs(dx) > abs(dy) * 0.4) or \
                 ((x, y + sy) not in layer.px and abs(dy) > abs(dx) * 0.4)
        if facing:
            add_[(x, y)] = cols[0] if d < radius * 0.55 else cols[1]
    for p, c in add_.items():
        layer.px[p][3] = c


def hitbox_preview3(name, tags, flats, meta, scale=4):
    """Hurtbox green, hit rects red on active frames (+ a blue 10x26 player box at the far edge), anchor yellow,
    spawn point magenta on its frame, telegraph glint cyan on its frame."""
    W, H = K.W, K.H
    start = {t: (a, b) for t, a, b in tags}
    rows, seen = [], set()
    for t, d in meta.get("attacks", {}).items():
        rows.append((t, d["windows"] if "windows" in d else [d]))
        seen.add(t)
    for t in list(meta.get("spawn", {})) + list(meta.get("telegraph", {})):
        if t not in seen:
            rows.append((t, []))
            seen.add(t)
    rows.append((tags[0][0], []))
    pad, lab = 2, 10
    cols = max(start[t][1] - start[t][0] + 1 for t, _ in rows)
    sheet = Image.new("RGBA", ((cols * (W + pad)) * scale, len(rows) * (H + pad + lab) * scale), K.BG)
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

            def cross(pt, col):
                sx, sy = pt
                d.line([(sx * scale - 6, sy * scale + 2), (sx * scale + 10, sy * scale + 2)], fill=col, width=2)
                d.line([(sx * scale + 2, sy * scale - 6), (sx * scale + 2, sy * scale + 10)], fill=col, width=2)
            if sp and k == sp["frame"]:
                cross(sp["at"], (255, 60, 255, 255))
            if tg and k == tg["frame"]:
                cross(tg["at"], (60, 240, 255, 255))
            d.line([(ax * scale - 4, min(ay * scale, H * scale - 1)), (ax * scale + 4, min(ay * scale, H * scale - 1))],
                   fill=(255, 255, 0, 255))
            d.line([(ax * scale, ay * scale - 5), (ax * scale, ay * scale + 3)], fill=(255, 255, 0, 255))
            sheet.alpha_composite(big, (k * (W + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", f"{name}_hitbox.png"))


def export(name, layers, anims, meta, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD, flat_order=flat_order)
    if meta is not None:
        hitbox_preview3(name, tags, flats, meta)
    return tags, flats


# =========================================================================== 1. GRIMOIRE
GRIM_L = ["WingBack", "Pages", "Covers", "Chain", "WingFront", "FX"]
G_NEU = dict(O=(20.0, 16.0), tilt=0.0, gape=64.0, wing=-130.0, eye=1, orbit=0, flash=False, puff=0, drop=0.0,
             broken=False, torn=0.0, scatter=0.0, ink=True, wind=0.0, lock=True)
GP = mk(G_NEU)
LC = 17.0          # cover length


def page_wing(R, L, base, ang, scale, bias, fi, seed, torn=0.0):
    """Three torn vellum strips fanning from `base` (frame coords before R): scorched tips, scrawled ink."""
    tips = []
    for k, (da, ln, w) in enumerate(((-24, 10.0, 2.8), (0, 13.0, 3.2), (22, 9.0, 2.6))):
        a = ang + da * (1.0 + 0.25 * math.sin(fi * 1.3 + k))
        d = dirv(a)
        pv = (-d[1], d[0])
        b = madd(base, (d, 0.6 + torn * (2 + k * 1.5)), (pv, torn * (k - 1) * 2.0))
        Ln = ln * scale
        jag = 1.2 + hash01(k, seed, 3) * 1.2
        pts = [madd(b, (pv, w * 0.2)), madd(b, (d, Ln * 0.92), (pv, w * 0.55)), madd(b, (d, Ln - jag), (pv, w * 0.15)),
               madd(b, (d, Ln + 0.5), (pv, -w * 0.25)), madd(b, (d, Ln - 0.6 * jag), (pv, -w * 0.5)),
               madd(b, (pv, -w * 0.2))]
        m = R.mask(pts)
        # gentle curl across the strip
        L.paint(n_plate(m, 0.9, (0.0, -0.1), 1.0,
                        fold=lambda x, y, d=d: (0.35 * math.sin((x * d[0] + y * d[1]) * 0.9 + fi), 0.0)), "H", bias)
        # scrawled ink lines along the strip
        for j, o in enumerate((-0.6, 0.8)):
            s0, s1 = madd(b, (d, 2.0), (pv, o)), madd(b, (d, Ln - 3.0), (pv, o))
            L.decal([q for i, q in enumerate(line(R.T(s0), R.T(s1))) if hash01(q[0], q[1], seed + j) < 0.6], ("H", 1))
        # scorched ashen tips
        tp = R.T(madd(b, (d, Ln - 0.4)))
        L.decal([q for q in m if math.hypot(q[0] + .5 - tp[0], q[1] + .5 - tp[1]) < 1.3], ("Z", 3))
        tips.append(R.T(madd(b, (d, Ln))))
    return tips


def eye_px(c, glow, look=0.6, squint=0.0):
    """Almond eye looking right: violet iris, black slit pupil, white glint."""
    out = {}
    rx, ry = 3.5, 2.0 * (1 - squint)
    for y in range(int(c[1] - 3), int(c[1] + 4)):
        for x in range(int(c[0] - 4), int(c[0] + 5)):
            dx, dy = x + .5 - c[0], y + .5 - c[1]
            e = (dx / rx) ** 2 + (dy / max(ry, 0.6)) ** 2
            if e > 1.0:
                continue
            ir = math.hypot(dx - look, dy * 1.2)
            if abs(dx - look) < 0.55 and abs(dy) < 1.6 and squint < 0.6:
                c_ = "N0"
            elif ir < 1.6:
                c_ = "J4" if glow >= 3 else "J3"
            elif e < 0.7:
                c_ = "J3" if glow >= 2 else "J2"
            else:
                c_ = "J2" if glow >= 2 else "J1"
            out[(x, y)] = c_
    if squint < 0.6:
        g = (int(c[0] + look - 1.4), int(c[1] - 1))
        if g in out:
            out[g] = "J4"
    return out


def draw_grimoire(p, fi, sw):
    Ls = {n: Layer(n) for n in GRIM_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    O = (p["O"][0], p["O"][1] + p["drop"])
    R = Rig(p["tilt"], O)
    info = {"hit": set()}
    M = lambda x, y: (O[0] + x, O[1] + y)
    g = p["gape"]
    s = M(-9.0, 0.0)                                   # spine centre
    au, al = -g / 2, g / 2 + 4
    du, dl = dirv(au), dirv(al)
    nu = (math.sin(math.radians(au)), -math.cos(math.radians(au)))      # outward (up) normal of the upper cover
    nl = (-math.sin(math.radians(al)), math.cos(math.radians(al)))      # outward (down) normal of the lower cover
    t = 3.0
    # ---- wings of torn pages (far, then near after the covers)
    wb = M(-9.5, -3.2)
    if p["torn"] < 1.0:
        page_wing(R, Ls["WingBack"], add(wb, (1.4, -0.6)), p["wing"] + 26, 0.85, -1, fi + 2, 7, p["torn"])
    # ---- pages: inner mouth of ink, page blocks, eye
    Pg = Ls["Pages"]
    # fan of pages radiating from the gutter; fore-edges form an arc
    ut, lt = madd(s, (nu, 0.9), (du, LC - 0.8)), madd(s, (nl, 0.9), (dl, LC - 0.8))
    arcp = []
    for k in range(1, 12):
        tt = k / 12
        a_ = au + (al - au) * tt
        r_ = LC - 0.6 + 1.4 * math.sin(math.pi * tt) + 0.5 * math.sin(k * 1.7 + fi * 0.5)
        arcp.append(madd(s, (dirv(a_), r_)))
    fm = R.mask([madd(s, (nu, 0.9)), ut] + arcp + [lt, madd(s, (nl, 0.9))])
    Pg.paint(n_plate(fm, 1.2, (-0.15, -0.1), 0.9), "H", -1)
    ec = R.T(madd(s, (dirv((au + al) / 2), LC * 0.5)))
    sc = R.T(s)
    for q in fm:
        dx, dy = q[0] + .5 - sc[0], q[1] + .5 - sc[1]
        rr = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx)) - p["tilt"]
        k = int((ang - au) / 4.2 + 0.6 * hash01(int(rr / 3), 0, 17))
        de = math.hypot(q[0] + .5 - ec[0], q[1] + .5 - ec[1])
        if rr < 4.5:
            Pg.decal([q], ("H", 1))
        elif de < 5.2 + 2.2 * hash01(q[0], q[1], 21) and p["eye"] > 0:
            Pg.decal([q], ("N", 3 if de > 5 else 2))           # ink bleeding out of the hollow
        elif k % 2 == 0:
            Pg.decal([q], ("N", 2) if de < 9 and hash01(k, 1, 5) < 0.6 else ("H", 1 if rr < 8 else 2))
    # the pages part around an ink-flooded hollow holding the eye
    mid = dirv((au + al) / 2 + p["tilt"] * 0)
    ec = R.T(madd(s, (dirv((au + al) / 2), LC * 0.5)))
    oy = 2.0 + 1.2 * max(0.0, min(1.0, (g - 30) / 50))
    hole = mask_disc(ec, 4.0, oy + 0.4) if p["eye"] > 0 else set()
    Pg.paint({q: norm3(-(q[0] + .5 - ec[0]) * 0.25, -(q[1] + .5 - ec[1]) * 0.4, 1.0) for q in hole}, "N", -1, ao=0)
    sq = 0.0 if g > 40 else 0.7
    if p["eye"] > 0:
        Pg.fixed(eye_px(ec, p["eye"], squint=sq))
    elif g > 30:                                       # dead: a dull closed lid
        Pg.fixed({(int(ec[0]) + dx, int(ec[1])): "Z4" for dx in range(-2, 3)})
    # ink weeping from the hollow down across the pages
    for k, (dx, ln) in enumerate(((-1.5, 3.0), (1.0, 4.5), (2.8, 2.0))):
        top = (int(ec[0] + dx), int(ec[1] + oy + 0.6))
        ln2 = ln * min(1.0, g / 60) + (fi + k) % 2 * 0.7
        for j in range(int(ln2) + 1):
            q = (top[0], top[1] + j)
            if q in fm:
                Pg.fixed({q: "N3" if j < ln2 - 0.5 else "N5"})
    info["mouth"] = R.T(madd(s, (dirv((au + al) / 2), LC + 1.5)))
    # ---- covers: heavy black leather, rounded spine, iron corners
    Cv = Ls["Covers"]
    for side, (dd, nn) in enumerate(((du, nu), (dl, nl))):
        a0 = madd(s, (nn, 0.9))
        poly = [madd(a0, (dd, -0.4)), madd(a0, (dd, LC)), madd(a0, (dd, LC - 0.6), (nn, t)), madd(a0, (dd, 0.4), (nn, t))]
        cm = R.plate(Cv, poly, "Z", bevel=1.0, tilt=(-0.3, -0.8) if side == 0 else (-0.35, -0.1), strength=1.0,
                     bias=0)
        rim = [q for q in cm if (q[0] + round(nn[0]), q[1] + round(nn[1])) not in cm]
        if side == 0:
            Cv.decal(rim, ("Z", 5))
        # tooled border line + iron corner cap
        Cv.decal([q for q in line(R.T(madd(a0, (dd, 2.0), (nn, t - 0.6))), R.T(madd(a0, (dd, LC - 2.4), (nn, t - 0.6))))
                  if q in cm], ("Z", 4 if side == 0 else 3))
        cc = R.T(madd(a0, (dd, LC - 0.9), (nn, t * 0.6)))
        Cv.decal([q for q in cm if math.hypot(q[0] + .5 - cc[0], q[1] + .5 - cc[1]) < 1.7], ("K", 4 if side == 0 else 2))
    arc = [madd(s, (dirv(a), 2.2)) for a in (-90 + au * 0.5, -135, 180, 135, 90 + al * 0.5)]
    tube(R, Cv, arc, [1.6, 1.7, 1.8, 1.7, 1.6], "Z", bias=0, ao=0)
    for a in (-120, 180, 125):                                     # raised spine bands
        R.decal(Cv, [madd(s, (dirv(a), 3.0))], ("Z", 5))
    # ink strands dripping off the lower cover
    for k, (a_, ln) in enumerate(((0.25, 3.0), (0.6, 2.0))):
        top = R.T(madd(s, (dl, LC * a_), (nl, 1.0 + t)))
        ln2 = ln + ((fi + k * 3) % 4) * 0.5
        for j in range(int(ln2)):
            Cv.fill([(int(top[0]), int(top[1]) + j)], "N3" if j < ln2 - 1 else "N5")
    info["hit"] |= set(Cv.px) | set(Pg.px)
    # ---- chains: a band around each cover, a broken length with a padlock dangling from the lower one
    Ch = Ls["Chain"]
    if not p["broken"]:
        hang = R.T(madd(s, (dirv(150), 3.2)))
        end = (hang[0] - 4.2 - sw * 0.7, hang[1] + 4.6 + sw * 0.3)
        Ch.fixed(chain_px(hang, end, 1.4))
        if p["lock"]:
            e = ip(end)
            Ch.fixed({(e[0] - 1, e[1] + 1): "K4", (e[0] + 1, e[1] + 1): "K2", (e[0], e[1]): "K4"})
            Ch.fixed({(e[0] + dx, e[1] + dy): ("K4" if dx < 0 else "K3") for dx in (-1, 0, 1) for dy in (2, 3, 4)})
            Ch.fixed({(e[0], e[1] + 3): "N0"})
    else:
        for k in range(7):                                         # burst links flying off
            a = -math.pi * (0.1 + 0.8 * hash01(k, 3, 5))
            r = 4 + 7 * hash01(k, 4, 5)
            q = ip((O[0] + math.cos(a) * r, O[1] + 3 + math.sin(a) * r * 0.7))
            FX.put([q], "K4" if k % 2 else "K2")
    # ---- near wing
    if p["torn"] < 1.0:
        page_wing(R, Ls["WingFront"], wb, p["wing"], 1.0, 0, fi, 3, p["torn"])
    # ---- loose pages (death)
    if p["scatter"]:
        for k in range(6):
            a = -math.pi * (0.05 + 0.9 * hash01(k, 1, 44))
            r = 5 + 10 * p["scatter"] * hash01(k, 2, 44)
            c = (p["O"][0] + math.cos(a) * r, p["O"][1] + math.sin(a) * r * 0.6 + p["scatter"] * 10 * hash01(k, 3, 44))
            ang = 360 * hash01(k, 5, 44) + p["scatter"] * 90
            d, pv = dirv(ang), dirv(ang + 90)
            pts = [madd(c, (d, -1.8), (pv, -1.2)), madd(c, (d, 1.8), (pv, -1.0)), madd(c, (d, 1.6), (pv, 1.2)),
                   madd(c, (d, -1.6), (pv, 1.0))]
            m = poly_mask(pts)
            Ls["WingFront"].paint(n_plate(m, 0.8, (0.0, -0.2)), "H", -1 - (k % 2))
    if p["eye"] == 0 and p["drop"] > 3:
        y = K.H - 1
        for x in range(int(O[0] - 11), int(O[0] + 12)):
            FX.put([(x, y)], "J0" if abs(x - O[0]) < 7 else "Z3")
    # ---- ink trail
    if p["ink"]:
        base = R.T(madd(s, (nl, 2.0)))
        for k in range(4):
            tt = ((fi * 0.25 + k * 0.25) % 1.0)
            q = ip((base[0] - 1.5 - tt * 7 + k * 0.5, base[1] + 1 + tt * 5 + math.sin(k * 2 + fi) * 0.8))
            FX.put([q], "J1" if tt < 0.35 else "J0")
            if tt < 0.3:
                FX.put([(q[0] + 1, q[1])], "J0")
    # ---- fx: gathering glyph ring + motes, release flash, ink puff
    mo = info["mouth"]
    if p["orbit"]:
        n = p["orbit"]
        c = (mo[0] + 1.0, mo[1])
        r = 7.5 - n * 1.3
        for k in range(10 + 2 * n):
            a = k * 2 * math.pi / (10 + 2 * n) - fi * 0.5
            q = ip((c[0] + math.cos(a) * r * 0.55, c[1] + math.sin(a) * r))
            if (k + fi) % 3:
                FX.put([q], "J3" if k % 3 == 0 else "J2")
        for k in range(4 + n):
            a = fi * 1.3 + k * 2 * math.pi / (4 + n)
            rr = 10 - n * 2 + (k % 2) * 1.5
            FX.put([ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.8))], "J3" if k % 2 else "J1")
        if n >= 3:
            disc_glow(FX, c, 1.6, ("J4", "J3", "J2"))
        info["orb"] = c
    if p["flash"]:
        c = ip((mo[0] + 1.5, mo[1]))
        for ang in range(0, 360, 45):
            L_ = 6 if ang % 90 == 0 else 3
            if ang == 180:
                continue
            FX.put(line(c, (c[0] + math.cos(math.radians(ang)) * L_, c[1] + math.sin(math.radians(ang)) * L_)),
                   "J4" if ang % 90 == 0 else "J3")
        disc_glow(FX, (c[0] + .5, c[1] + .5), 2.4, ("J4", "J4", "J3"))
        info["flash"] = c
    if p["puff"]:
        for k in range(9):
            q = ip((mo[0] + math.cos(k * 0.7) * (1.5 + p["puff"] * 1.4), mo[1] + math.sin(k * 1.9) * (1 + p["puff"])))
            FX.put([q], "J0" if k % 2 else "Z4")
    return Ls, info


GFLAP = [-160, -140, -122, -140, -175, 172]


def g_fly():
    fr = []
    for i in range(6):
        bob = (0.0, 0.6, 1.0, 0.6, -0.2, -0.6)[i]
        fr.append((100, GP(O=(20.0, 16.0 + bob), wing=GFLAP[i], tilt=-3 + bob * 3, gape=62 + 4 * math.sin(i * 1.05))))
    return fr


def g_cast():
    return [
        (130, GP(gape=54, tilt=-2, wing=-140, O=(20.4, 16.2))),
        (140, GP(gape=78, tilt=-6, wing=-110, eye=2, orbit=1)),
        (150, GP(gape=92, tilt=-9, wing=-100, eye=2, orbit=2, O=(19.6, 15.8))),
        (150, GP(gape=102, tilt=-11, wing=-96, eye=2, orbit=3, O=(19.2, 15.6))),
        (340, GP(gape=108, tilt=-12, wing=-92, eye=3, orbit=3, O=(19.0, 15.4))),
        (70, GP(gape=78, tilt=8, wing=176, eye=3, flash=True, O=(18.0, 16.4), wind=3)),
        (110, GP(gape=58, tilt=5, wing=-176, eye=2, puff=1, O=(18.6, 16.4))),
        (140, GP(gape=60, tilt=2, wing=-150, puff=2, O=(19.4, 16.2))),
        (150, GP(gape=64, tilt=0, wing=-130)),
    ]


def g_hurt():
    return [(80, GP(gape=22, tilt=-20, wing=-84, eye=3, O=(18.0, 15.0))),
            (140, GP(gape=46, tilt=-9, wing=-110, eye=2, O=(19.0, 15.6)))]


def g_death():
    return [
        (90, GP(gape=92, tilt=-18, wing=-110, eye=3, O=(19.0, 15.0))),
        (110, GP(gape=120, tilt=-34, wing=-170, eye=2, broken=True, torn=0.5, O=(19.4, 15.6))),
        (110, GP(gape=146, tilt=-58, eye=1, broken=True, torn=1.0, scatter=0.3, drop=1.5, ink=False, O=(20.0, 16.0))),
        (120, GP(gape=166, tilt=-80, eye=0, broken=True, torn=1.0, scatter=0.6, drop=3.5, ink=False, lock=False,
                 O=(20.5, 16.0))),
        (140, GP(gape=176, tilt=-90, eye=0, broken=True, torn=1.0, scatter=0.85, drop=4.5, ink=False, lock=False,
                 O=(21.0, 16.0))),
        (700, GP(gape=178, tilt=-90, eye=0, broken=True, torn=1.0, scatter=1.0, drop=4.5, ink=False, lock=False,
                 O=(21.0, 16.0))),
    ]


def build_grimoire():
    K.setup(40, 32)
    anims, infos = render_anims("grimoire", GRIM_L, draw_grimoire,
                                [("fly", g_fly), ("cast", g_cast), ("hurt", g_hurt), ("death", g_death)],
                                sway_key="O", loops=("fly",))
    hb = hurtbox(anims, ["Covers", "Pages"], inset=(0, 0, 0), floor=False)
    fl = infos["cast"][5]["flash"]
    meta = {"native": 1, "frame": [40, 32], "anchor": [20, 16], "flying": True,
            "hurtbox": hb,
            "attacks": {"cast": {"active": [5, 5], "hit": [fl[0] - 5, fl[1] - 5, 11, 11]}},
            "spawn": {"cast": {"frame": 5, "at": spawn_pt(fl)}},
            "telegraph": {"cast": {"frame": 4, "at": spawn_pt(infos["cast"][4]["orb"])}},
            "notes": "faces right; floats (anchor = body centre). Body contact damage = hurtbox. cast: violet "
                     "burst at the maw active on frame 5 only (point-blank), proj_inkbolt spawns at spawn.cast.at "
                     "on frame 5; frame 4 is the held windup (telegraph)."}
    export("grimoire", GRIM_L, anims, meta)
    return meta


# =========================================================================== 2. INK HOUND
HOUND_L = ["FarLegs", "Tail", "Body", "NearHind", "NearFront", "Head", "FX"]
FL = 31.0
D_NEU = dict(P=(17.0, 15.0), S=(35.0, 15.5), arch=0.0, Hh=(44.5, 10.0), ha=16.0, jaw=0.0, ta=0.0, wave=0.0,
             hn=(15.0, FL, -2.4, -5.2), hf=(18.5, FL, -2.4, -5.2), fn=(36.0, FL, -0.3, -3.0), ff=(33.0, FL, -0.3, -3.0),
             eye=1, glyph=0, drip=True, lines=None, splash=None, wind=0.0, flash=False, wisps=True)
DP = mk(D_NEU)


def hound_leg(L, hip, paw, front, bias, claws=True):
    px, py, ox, oy = paw
    foot = (px, py - 0.9)
    mid = (px + ox, py + oy)                       # hock (hind) / wrist (front)
    if front:
        kn = ik(hip, mid, 5.6, 5.4, (-1, 0.15))
        radii = [1.9, 1.0, 0.8, 0.75]
    else:
        kn = ik(hip, mid, 6.2, 6.0, (1, 0.25))
        radii = [2.1, 1.05, 0.8, 0.75]
    L.paint(n_tube([hip, kn, mid, foot], radii), "N", bias)
    # long narrow paw with pale hooked claws
    L.paint(n_dome((foot[0] + 1.0, foot[1] + 0.3), 1.8, 0.85, tilt=(0, -0.2)), "N", bias, ao=0)
    if claws:
        t = ip((foot[0] + 2.4, foot[1] + 0.6))
        L.fixed({t: "E4" if bias >= 0 else "E2", (t[0] - 1, t[1] + 1): "E3" if bias >= 0 else "E1"})
    return kn, mid


def rune(pix, c, kind, col):
    x, y = ip(c)
    pat = {0: [(0, -1), (0, 0), (0, 1), (-1, -2), (1, -2)],          # branching mark
           1: [(0, -1), (0, 0), (0, 1), (1, 0), (1, -1)],            # thorn mark
           2: [(-1, -1), (0, 0), (1, 1), (1, -1), (-1, 1)]}[kind]    # crossed scar
    for dx, dy in pat:
        pix[(x + dx, y + dy)] = col


def draw_hound(p, fi, sw):
    Ls = {n: Layer(n) for n in HOUND_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    info = {"hit": set()}
    P, S, Hh, ha = p["P"], p["S"], p["Hh"], p["ha"]
    ax_ = sub(S, P)
    ln = math.hypot(*ax_)
    fwd = (ax_[0] / ln, ax_[1] / ln)
    up = (fwd[1], -fwd[0])
    dn = (-up[0], -up[1])
    gcol = ("Z3", "J0", "J1", "J2", "J3")[p["glyph"] + 1 if p["glyph"] >= 0 else 0]
    # ---- far legs (behind everything)
    Fl = Ls["FarLegs"]
    hound_leg(Fl, madd(P, (fwd, 1.4), (dn, 1.2)), p["hf"], False, -2)
    hound_leg(Fl, madd(S, (fwd, -0.8), (dn, 2.6)), p["ff"], True, -2)
    # ---- tail: long whip fraying into ink
    Tl = Ls["Tail"]
    ta, wv = p["ta"], p["wave"]
    t0 = madd(P, (fwd, -2.6), (up, 1.6))
    t1 = add(t0, rot((-4.0, 1.8 + 0.3 * sw), ta))
    t2 = add(t1, rot((-4.0, 1.0 + wv), ta))
    t3 = add(t2, rot((-3.2, -0.6 + wv * 1.6), ta))
    tp = curve([t0, t1, t2, t3], 4)
    Tl.paint(n_tube(tp, [1.5 - 1.0 * i / (len(tp) - 1) for i in range(len(tp))]), "N", -1)
    d3 = sub(t3, t2)
    l3 = math.hypot(*d3) or 1
    d3 = (d3[0] / l3, d3[1] / l3)
    for k, (da, L_) in enumerate(((-30, 3.0), (0, 4.0), (28, 2.5)) if p["wisps"] else ()):
        dd = rot(d3, da + wv * 8)
        pts = line(t3, madd(t3, (dd, L_ + (fi + k) % 2 * 0.8)))[1:]
        for j, q in enumerate(pts):
            FX.put([q], "N3" if j < len(pts) - 1 else ("J0" if k == 1 else "N4"))
    # ---- body: haunch, tucked loin, deep skeletal ribcage, brisket
    Bd = Ls["Body"]
    c0 = madd(P, (fwd, -1.6), (up, 0.2))
    c1 = madd(lerp(P, S, 0.32), (up, 1.0 + p["arch"]))
    c2 = madd(lerp(P, S, 0.66), (dn, 0.9), (up, p["arch"] * 0.4))
    c3 = madd(S, (dn, 1.6))
    c4 = madd(S, (fwd, 2.4), (dn, 0.6))
    cp = curve([c0, c1, c2, c3, c4], 5)
    rr = []
    for i in range(len(cp)):
        t = i / (len(cp) - 1)
        # radius profile: rump 3.3, loin 2.5, ribs 4.1, chest 4.5, brisket 3.2
        keys = [(0, 2.9), (0.25, 1.9), (0.52, 3.4), (0.76, 3.9), (1.0, 2.6)]
        for (ta_, ra), (tb, rb) in zip(keys, keys[1:]):
            if ta_ <= t <= tb:
                u = (t - ta_) / (tb - ta_)
                u = u * u * (3 - 2 * u)
                rr.append(ra + (rb - ra) * u)
                break
    bm = Bd.paint(n_tube(cp, rr), "N", 0)
    # ribs: dark grooves with a glint ridge (skeletal)
    for i in range(4):
        rx = lerp(P, S, 0.5 + 0.1 * i)
        a_ = madd(rx, (up, 1.8 + p["arch"] * 0.3))
        b_ = madd(rx, (dn, 3.6), (fwd, -1.6))
        pts = [q for q in line(a_, b_) if q in bm]
        Bd.decal(pts, ("N", 1))
        Bd.decal([(q[0] + 1, q[1]) for q in pts[:2] if (q[0] + 1, q[1]) in bm], ("N", 4))
    # vertebral spurs along the spine
    for i in range(7):
        t = 0.1 + i * 0.12
        c = lerp(P, S, t)
        topc = madd(c, (up, 3.0 + p["arch"] * (1 - abs(t - 0.4)) + (0.4 if 0.4 < t < 0.8 else -0.2)))
        q = ip(topc)
        while q in bm:
            q = (q[0], q[1] - 1)
        if i % 2 == 0:
            Bd.fixed({q: "N3"})
    # glyph scars on flank and haunch
    rp = {}
    rune(rp, madd(lerp(P, S, 0.7), (dn, 0.4)), 0, gcol)
    rune(rp, madd(P, (fwd, 0.4), (dn, 0.2)), 1, gcol)
    Bd.fixed({q: c for q, c in rp.items() if q in bm})
    info["hit"] |= set(bm)
    # ---- near hind leg with a lean haunch
    Nh = Ls["NearHind"]
    hip = madd(P, (fwd, 0.4), (dn, 1.0))
    Nh.paint(n_dome(madd(hip, (fwd, -0.3), (up, 0.8)), 2.8, 3.5, tilt=(-0.1, -0.1)), "N", 0)
    hound_leg(Nh, hip, p["hn"], False, 0)
    Nh.fixed({q: c for q, c in rp.items() if q in Nh.px})
    # ---- near front leg with shoulder blade
    Nf = Ls["NearFront"]
    sho = madd(S, (fwd, -0.4), (dn, 2.4))
    Nf.paint(n_dome(madd(sho, (up, 1.8), (fwd, -0.4)), 2.1, 3.1, tilt=(-0.1, -0.2)), "N", 0)
    _, wr = hound_leg(Nf, sho, p["fn"], True, 0)
    info["hit"] |= set(Nf.px)
    # ---- neck + head: long narrow skull, laid-back ear, glyph-scar eye
    Hd = Ls["Head"]
    G = lambda x, y: add(Hh, rot((x, y), ha))
    hb = G(-3.2, 0.6)
    n0 = madd(S, (fwd, 1.2), (up, 1.2))
    n1 = madd(lerp(n0, hb, 0.5), (up, 1.2))
    Hd.paint(n_tube(curve([n0, n1, hb], 4), [2.8, 2.4, 2.1, 1.9, 1.7, 1.6, 1.6, 1.6, 1.6]), "N", 0)
    ear = [G(-2.4, -1.4), G(-0.2, -2.1), G(-7.0, -6.2 + 0.4 * sw)]
    Hd.paint(n_plate(poly_mask(ear), 0.8, (-0.1, -0.3)), "N", -1, ao=0)
    hinge = (-0.6, 1.4)
    ja = p["jaw"] * 40.0
    J = lambda x, y: G(*add(hinge, rot(sub((x, y), hinge), ja)))
    jaw = [J(-1.2, 1.1), J(9.4, 1.3), J(9.0, 2.1), J(2.0, 2.9), J(-1.6, 2.6)]
    if p["jaw"] > 0.15:                            # violet-dark gullet
        Hd.fixed({q: ("J0" if hash01(*q, 3) < 0.5 else "Z2") for q in poly_mask([G(-1.0, 1.2), G(10.2, 1.2), J(9.4, 1.3)])})
    jm = poly_mask(jaw)
    Hd.paint(n_plate(jm, 0.8, (0.0, 0.3)), "N", -1)
    skull = [G(-3.6, -1.2), G(-1.2, -2.3), G(1.8, -2.1), G(3.4, -1.1), G(10.0, 0.0), G(11.2, 0.5), G(10.6, 1.2),
             G(2.4, 1.3), G(-1.4, 2.3), G(-3.7, 1.1)]
    sm = poly_mask(skull)
    Hd.paint(n_plate(sm, 1.3, (-0.15, -0.3), 1.1), "N", 0)
    Hd.decal([ip(G(10.6, 0.3))], ("N", 5))                               # wet nose glint
    Hd.decal([q for q in line(G(-1.0, 1.9), G(2.2, 1.2)) if q in sm], ("N", 1))   # cheekbone
    # teeth
    teeth = {}
    if p["jaw"] > 0.15:
        for x in (3.4, 5.8, 8.2):
            teeth[ip(G(x, 1.6))] = "E4"
            teeth[ip(G(x, 2.4))] = "E3"
        for x in (4.6, 7.0):
            teeth[ip(J(x, 1.1))] = "E3"
    else:
        teeth[ip(G(7.6, 1.6))] = "E4"                                     # a fang over the lip
    Hd.fixed(teeth)
    # glyph-scar eye: a slit burned vertically through the eye
    e = ip(G(1.6, -0.7))
    eyep = {e: "J4" if p["eye"] >= 2 else "J3", (e[0] + 1, e[1]): "J2" if p["eye"] < 3 else "J3",
            (e[0], e[1] - 1): gcol if p["glyph"] >= 1 else "J1", (e[0], e[1] + 1): "J1",
            (e[0] - 1, e[1] - 2): "J0" if p["eye"] < 3 else "J1"}
    if p["eye"] > 0:
        Hd.fixed(eyep)
    else:
        Hd.fixed({e: "N1", (e[0] + 1, e[1]): "N1"})
    # cold rim along the top line so the ink body separates from dark backgrounds
    for L_ in (Bd, Hd, Nh, Nf, Tl):
        L_.decal([q for q, e_ in L_.px.items() if (q[0], q[1] - 1) not in L_.px and e_[0] == "N"
                  and not isinstance(e_[3], str)], ("N", 4))
    info["hit"] |= set(Hd.px)
    info["eye"] = e
    info["jaw"] = G(10.5, 1.6)
    # ---- ink: drips from the belly / chest / jaw, speed streaks, splash
    if p["drip"]:
        for k, (src, L_) in enumerate(((madd(lerp(P, S, 0.62), (dn, 4.6)), 2.5), (madd(S, (dn, 6.0)), 1.8),
                                       (madd(lerp(P, S, 0.3), (dn, 2.8)), 1.5), (G(4.0, 3.2), 2.0))):
            ph = (fi * 0.5 + k * 0.37) % 1.0
            x0, y0 = ip(src)
            n = int(L_ + ph * 2)
            for j in range(n):
                FX.put([(x0, y0 + j)], "N3")
            FX.put([(x0, y0 + n)], "N5")
            if ph > 0.55:
                FX.put([(x0, y0 + n + 2 + int(ph * 3))], "J0")
    if p["lines"]:
        x0, x1, ys = p["lines"]
        for i, y in enumerate(ys):
            a = x0 + (i * 3) % 4
            b = x1 - (i * 5) % 6
            for x in range(a, b):
                FX.put([(x, y)], "J1" if x > (a + b) / 2 else "J0")
    if p["splash"]:
        cx, stg = p["splash"]
        for k in range(10):
            a = -math.pi * (0.08 + 0.84 * hash01(k, 1, 31))
            r = (2 + 6 * hash01(k, 2, 31)) * (0.7 if stg == 1 else 1.1)
            q = ip((cx + math.cos(a) * r * 1.3, FL - 0.5 + math.sin(a) * r * (0.8 if stg == 1 else 0.4)
                    + (0 if stg == 1 else 1.5)))
            FX.put([q], ("N4" if k % 3 else "J1") if stg == 1 else ("N3" if k % 2 else "J0"))
    return Ls, info


def d_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.4, 0.7, 0.3)[i]
        fr.append((180, DP(S=(35.0, 15.5 + b * 0.5), P=(17.0, 15.0 + b * 0.2), Hh=(44.5 + b * 0.2, 10.0 + b * 0.8),
                           ha=16 + b * 3, ta=-4 + 8 * math.sin(i * math.pi / 2), wave=math.sin(i * math.pi / 2 + 1))))
    return fr


def d_run():
    L = [  # P, S, arch, Hh, ha, hind near, hind far, front near, front far
        ((15.0, 13.5), (37.0, 14.0), -0.8, (47.5, 9.5), 8, (4.5, 25.0, 4.5, -1.8), (6.5, 26.5, 4.2, -2.2),
         (50.0, 24.5, -3.6, 0.2), (47.5, 26.5, -3.4, -0.6)),
        ((16.0, 14.5), (37.0, 15.5), 0.0, (46.5, 10.5), 12, (10.0, 24.0, 3.6, -3.0), (12.0, 25.5, 3.2, -3.2),
         (43.5, FL, -1.5, -3.0), (47.0, 27.0, -3.0, -1.5)),
        ((18.0, 15.0), (36.0, 16.0), 1.2, (45.0, 11.5), 16, (20.0, 25.0, -1.0, -4.2), (22.0, 26.5, -1.2, -4.0),
         (35.0, FL, 1.2, -3.0), (39.5, FL, -0.5, -3.0)),
        ((19.0, 13.5), (35.0, 14.5), 2.6, (44.5, 10.5), 14, (29.0, 26.0, -3.0, -3.5), (31.0, 27.0, -3.0, -3.2),
         (27.0, 25.5, 3.0, -2.2), (29.0, 26.5, 2.8, -2.0)),
        ((19.0, 15.0), (36.0, 15.0), 1.5, (46.0, 10.5), 10, (26.0, FL, -2.6, -4.6), (29.0, FL, -2.6, -4.6),
         (41.0, 26.0, -2.2, -2.6), (38.0, 27.0, -1.5, -3.0)),
        ((17.0, 14.5), (37.0, 14.5), 0.0, (47.0, 10.0), 8, (11.0, FL, -1.0, -5.0), (15.0, FL, -1.8, -5.0),
         (47.0, 25.5, -3.4, -0.8), (44.0, 27.0, -3.0, -1.6)),
    ]
    fr = []
    for i, (P, S, ar, Hh, ha, hn, hf, fn, ff) in enumerate(L):
        fr.append((70, DP(P=P, S=S, arch=ar, Hh=Hh, ha=ha, hn=hn, hf=hf, fn=fn, ff=ff, ta=-14 + 10 * math.sin(i * 1.05),
                          wave=1.2 * math.sin(i * 1.05 + 1.5), wind=-2.0)))
    return fr


def d_pounce():
    return [
        (150, DP(P=(16.0, 16.5), S=(33.0, 18.0), arch=0.5, Hh=(40.5, 15.0), ha=10, eye=2, glyph=1,
                 hn=(14.0, FL, -2.2, -4.8), hf=(17.0, FL, -2.2, -4.8), fn=(36.0, FL, 1.2, -2.8), ff=(33.5, FL, 1.0, -2.8),
                 ta=-6)),
        (320, DP(P=(14.5, 15.5), S=(31.0, 20.0), arch=1.5, Hh=(38.5, 18.0), ha=4, eye=3, glyph=2, jaw=0.25,
                 hn=(12.5, FL, -2.0, -5.0), hf=(16.0, FL, -2.0, -5.0), fn=(35.0, FL, 2.2, -2.2), ff=(32.5, FL, 2.0, -2.2),
                 ta=-24, wave=1.5)),
        (160, DP(P=(14.0, 17.5), S=(30.5, 19.5), arch=2.0, Hh=(38.0, 16.5), ha=0, eye=3, glyph=3, jaw=0.3,
                 hn=(13.5, FL, -2.8, -3.6), hf=(16.5, FL, -2.8, -3.6), fn=(34.5, FL, 1.8, -2.4), ff=(32.0, FL, 1.8, -2.4),
                 ta=-30, wave=-1.0)),
        (80, DP(P=(18.0, 15.0), S=(35.5, 10.5), arch=-1.0, Hh=(44.5, 6.0), ha=-8, eye=3, glyph=3, jaw=0.6,
                hn=(9.0, FL, 3.0, -4.0), hf=(11.5, FL, 2.6, -4.2), fn=(43.0, 17.0, -3.0, -0.5), ff=(41.0, 19.0, -3.0, -1.0),
                ta=10, wave=1.0, wind=3, splash=(10, 1))),
        (90, DP(P=(20.0, 12.0), S=(39.0, 12.5), arch=-1.2, Hh=(48.5, 12.5), ha=18, eye=3, glyph=3, jaw=1.0,
                hn=(7.0, 17.5, 4.6, -1.2), hf=(9.0, 19.5, 4.4, -1.6), fn=(52.0, 26.5, -3.2, -1.8), ff=(49.5, 28.5, -3.0, -2.2),
                ta=18, wave=0.5, wind=4, lines=(0, 16, (8, 11, 14, 17)))),
        (100, DP(P=(21.0, 15.0), S=(38.5, 17.0), arch=0.4, Hh=(47.5, 17.5), ha=26, eye=2, glyph=2, jaw=0.05,
                 hn=(21.0, 26.0, -1.2, -4.0), hf=(23.5, 27.0, -1.2, -4.0), fn=(46.5, FL, -1.5, -3.0), ff=(44.0, FL, -1.2, -3.0),
                 ta=8, wave=-1.0, splash=(47, 1))),
        (150, DP(P=(19.5, 16.0), S=(36.5, 17.5), arch=1.0, Hh=(45.5, 14.5), ha=20, eye=2, glyph=1,
                 hn=(19.0, FL, -2.4, -5.0), hf=(22.0, FL, -2.4, -5.0), fn=(41.0, FL, -0.2, -3.0), ff=(38.5, FL, 0.0, -3.0),
                 ta=0, wave=0.5, splash=(45, 2))),
        (190, DP(P=(17.5, 15.2), S=(35.3, 15.6), Hh=(44.7, 10.4), ha=17, glyph=0,
                 hn=(15.5, FL, -2.4, -5.2), hf=(18.5, FL, -2.4, -5.2), fn=(36.2, FL, -0.3, -3.0), ff=(33.2, FL, -0.3, -3.0))),
    ]


def d_hurt():
    return [
        (90, DP(P=(15.0, 15.0), S=(32.0, 14.0), arch=1.0, Hh=(40.0, 7.0), ha=-26, jaw=0.6, eye=3, glyph=3,
                hn=(13.0, FL, -2.2, -5.2), hf=(16.5, FL, -2.2, -5.2), fn=(34.0, 28.5, -1.0, -2.8), ff=(31.0, FL, -0.3, -3.0),
                ta=-20)),
        (140, DP(P=(16.0, 15.0), S=(33.8, 15.0), arch=0.5, Hh=(42.5, 8.8), ha=2, jaw=0.2, eye=2, glyph=1,
                 hn=(14.0, FL, -2.4, -5.2), hf=(17.5, FL, -2.4, -5.2), fn=(35.0, FL, -0.3, -3.0), ff=(32.0, FL, -0.3, -3.0),
                 ta=-8)),
    ]


def collapse(names, sq, burn=0.0, seed=0, spread=0.25, pal=("J2", "J1", "J0", "Z3", "Z2"), cx=None):
    """Squash the named layers down onto the floor line (spreading sideways) -- a body melting away or an
    emptied robe crumpling; optionally burn some of it into rising motes."""
    def f(imgs):
        box = K.opaque_bbox(imgs, names)
        out = dict(imgs)
        if box:
            x0, y0, x1, y1 = box
            nh = max(1, int(round((y1 - y0) * sq)))
            nw = int(round((x1 - x0) * (1 + spread * (1 - sq))))
            c = (x0 + x1) / 2 if cx is None else cx
            for n in names:
                if n in imgs:
                    crop = imgs[n].crop(box).resize((nw, nh), Image.NEAREST)
                    o = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
                    o.paste(crop, (int(c - nw / 2), K.H - nh))
                    out[n] = o
        if burn > 0:
            out = K.ember_dissolve(out, burn, names, seed=seed, rise=10, pal=pal)
        return out
    return f


def ink_melt(sq, burn=0.0, seed=0):
    return collapse(["FarLegs", "Tail", "Body", "NearHind", "NearFront", "Head"], sq, burn, seed)


def d_death():
    lie = dict(P=(17.0, 24.0), S=(34.0, 25.0), arch=0.5, Hh=(43.0, 26.5), ha=12, eye=0, glyph=0, drip=False,
               hn=(22.0, FL, -3.5, -1.5), hf=(24.5, FL, -3.5, -1.5), fn=(40.5, FL, -3.2, -0.5), ff=(38.0, FL, -3.0, -0.8),
               ta=20, wave=0.0, wisps=False)
    return [
        (100, DP(P=(15.0, 16.0), S=(31.0, 12.0), arch=0.5, Hh=(38.0, 5.5), ha=-36, jaw=0.8, eye=3, glyph=3,
                 hn=(13.0, FL, -2.2, -5.2), hf=(16.0, FL, -2.2, -5.2), fn=(35.0, 24.0, -1.5, -2.5), ff=(33.0, 26.0, -1.5, -2.5),
                 ta=-30)),
        (130, DP(P=(16.0, 20.0), S=(33.0, 21.5), arch=1.0, Hh=(41.5, 22.0), ha=30, jaw=0.4, eye=1, glyph=1,
                 hn=(12.0, FL, -3.0, -3.5), hf=(19.0, FL, -3.0, -3.5), fn=(38.0, FL, -1.5, -2.5), ff=(34.5, FL, -1.0, -2.5),
                 ta=0)),
        (140, DP(**dict(lie, eye=1, jaw=0.2))),
        (140, DP(**lie, post=ink_melt(0.6, 0.12), splash=(28, 2))),
        (160, DP(**lie, post=ink_melt(0.3, 0.25))),
        (600, DP(**lie, post=ink_melt(0.1, 0.3))),
    ]


def hound_puddle(imgs, width, fi):
    """Ink pool left behind after the melt."""
    fx = imgs["FX"].copy()
    px = fx.load()
    for x in range(int(28 - width), int(28 + width)):
        if px[x, K.H - 1][3] == 0:
            px[x, K.H - 1] = K.RGBA["N3" if abs(x - 28) < width * 0.6 else "Z2"]
        if abs(x - 28) < width * 0.5 and px[x, K.H - 2][3] == 0:
            px[x, K.H - 2] = K.RGBA["OUT"]
    out = dict(imgs)
    out["FX"] = fx
    return out


def build_hound():
    K.setup(56, 32)
    anims, infos = render_anims("ink_hound", HOUND_L, draw_hound,
                                [("idle", d_idle), ("run", d_run), ("pounce", d_pounce), ("hurt", d_hurt),
                                 ("death", d_death)], sway_key="S", loops=("idle", "run"))
    # ink pool under the melting body
    tag = [a for a in anims if a[0] == "death"][0]
    for k, w in ((3, 7), (4, 11), (5, 13)):
        ms, imgs = tag[1][k]
        tag[1][k] = (ms, hound_puddle(imgs, w, k))
    meta = {"native": 1, "frame": [56, 32], "anchor": [26, 32],
            "hurtbox": hurtbox(anims, ["Body", "Head"], inset=(2, 2, 5)),
            "attacks": {"pounce": {"active": [4, 5], "hit": hit_rect(infos, "pounce", [4, 5], x_min=34)}},
            "telegraph": {"pounce": {"frame": 3, "at": spawn_pt(infos["pounce"][3]["eye"])}},
            "notes": "faces right; pounce drawn in place (engine lunges it forward on frames 3-5): frames 1-2 are the "
                     "held coil (glyphs + eye flare), launch 3, active 4-5 (jaws + fore-claws), land 6, recover 7."}
    export("ink_hound", HOUND_L, anims, meta)
    return meta


# =========================================================================== shared: lantern + hooded robe
def lantern(L, FX, ring, down, sc, glow, fi, flare=0.0, halo=True, lid=0.0):
    """Iron cage lantern hanging from `ring` along unit vector `down` (frame coords). sc 1.0 = monk lantern,
    ~1.7 = the Head Librarian's censer. glow 0..3 (0 = snuffed). Returns (centre, pixel set)."""
    dx, dy = down
    rx, ry = dy, -dx                                # local +x (right when hanging straight down)
    T = lambda a, b: (ring[0] + rx * a * sc + dx * b * sc, ring[1] + ry * a * sc + dy * b * sc)
    pix = {}
    # hanging loop + pointed roof with finial
    for q in line(T(0, 0), T(0, 1.2)):
        pix[q] = "K3"
    roof = poly_mask([T(0, 0.8), T(2.9, 3.4), T(-2.9, 3.4)])
    for q in roof:
        pix[q] = "K4" if (q[0] + .5 - T(0, 2.4)[0]) * rx + (q[1] + .5 - T(0, 2.4)[1]) * ry < -0.4 else "K2"
    brim = poly_mask([T(-3.3, 3.2), T(3.3, 3.2), T(3.3, 4.2), T(-3.3, 4.2)])
    for q in brim:
        pix[q] = "K3"
    body = poly_mask([T(-2.6, 4.0), T(2.6, 4.0), T(2.3, 9.6), T(-2.3, 9.6)])
    glass = poly_mask([T(-1.7, 4.4), T(1.7, 4.4), T(1.5, 9.2), T(-1.5, 9.2)])
    c = T(0, 7.0)
    for q in body:
        pix[q] = "K2" if (q[0] + .5 - c[0]) * rx + (q[1] + .5 - c[1]) * ry < 0 else "K1"
    for q in glass:
        dd = math.hypot(q[0] + .5 - c[0], q[1] + .5 - c[1]) / sc
        f = glow + 0.35 * math.sin(fi * 2.3 + q[0]) + flare
        if glow <= 0.05:
            col = "Z2" if lid < 0.5 else "K1"
        elif dd < 0.9 and f > 1.2:
            col = "J4"
        elif dd < 1.7:
            col = "J3" if f > 0.8 else "J2"
        elif dd < 2.6:
            col = "J2" if f > 1.4 else "J1"
        else:
            col = "J1" if f > 1.0 else "J0"
        pix[q] = col
    # vertical cage bars across the glass
    for a in (() if sc < 1.4 else (-0.9, 0.9)):
        for q in line(T(a, 4.4), T(a, 9.2)):
            if q in glass and hash01(q[0], q[1], 5) < (0.8 if glow > 0 else 1.0):
                pix[q] = "K2" if pix[q] not in ("J4",) else pix[q]
    base = poly_mask([T(-3.0, 9.4), T(3.0, 9.4), T(2.4, 10.6), T(-2.4, 10.6)])
    for q in base:
        pix[q] = "K3" if (q[0] + .5 - c[0]) * rx < 0 else "K2"
    for q in line(T(0, 10.6), T(0, 11.6)):
        pix[q] = "K3"
    if lid > 0:                                    # snuffer cap clamped over the glass
        for q in poly_mask([T(-2.9, 3.6), T(2.9, 3.6), T(2.9, 3.6 + 6.2 * lid), T(-2.9, 3.6 + 6.2 * lid)]):
            pix[q] = "K3" if (q[0] + .5 - c[0]) * rx < -0.5 else "K2"
    L.fixed(pix)
    if glow > 0.3 and halo:
        halo_dots(FX, c, 4.8 * sc + glow * 0.8, 12 + int(sc * 6), fi, ("J1", "J0", "J0"), skip=set(pix))
        if glow + flare > 2.2:
            halo_dots(FX, c, 3.6 * sc + glow * 0.6, 10 + int(sc * 4), fi + 1, ("J2", "J1"), skip=set(pix))
    return c, set(pix)


def robe_mask(F, P, ln, floor, fi, seed, sw, heap=0.0, w=1.0, trail=1.0):
    """Tall severe robe from the shoulders to a ragged floor-length hem with a trailing back point."""
    hem = floor + 0.6
    fr = P[0] + (5.4 + heap * 3.0) * w - sw * 0.3
    bk = P[0] - (6.2 + heap * 3.4) * w - sw * 0.6
    pts = [F(-3.4 * w, -ln - 1.2), F(2.8 * w, -ln - 1.4), F(3.8 * w, -ln + 4.0), F(3.4 * w, -3.0),
           (fr, hem - 1.8)]
    n = 9
    for i in range(n + 1):
        t = i / n
        x = fr - (fr - bk) * t
        d = (0.9 + hash01(i, fi // 2, seed) * 0.8) if (i + fi) % 2 == 0 else -0.5
        pts.append((x, hem + d))
    pts += [(bk - 2.8 * trail - sw * 0.5, hem), (bk + 0.4, hem - 3.0), F(-4.8 * w, -2.0), F(-4.4 * w, -ln + 3.0)]
    return pts


def robe_fold(P, sw):
    return lambda x, y: (0.6 * math.sin((x - P[0] - sw * 0.25) * 1.15) * min(1.0, max(0.0, (y - P[1] + 9) / 12)), 0)


# =========================================================================== 3. LANTERN MONK
MONK_L = ["LanternBack", "BackArm", "Robe", "Head", "FrontArm", "Lantern", "FX"]
L_NEU = dict(P=(15.0, 32.0), C=(16.4, 20.0), Hd=(19.0, 12.6), hup=(0.35, -1), hf=(24.0, 29.0), hb=(12.0, 29.5),
             ring=None, glow=1.0, flare=0.0, behind=False, rot=0.0, piv=(0, 0), heap=0.0, fallen=False, feet=(0.0, 0.0),
             smear=None, sparks=0, lpos=None, wind=0.0, hem=0, smoke=0)
LP = mk(L_NEU)
CHAIN_IDLE = 5.0


def draw_monk(p, fi, sw):
    Ls = {n: Layer(n) for n in MONK_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    info = {"hit": set()}
    floor = K.H - 1.0
    shF, shB = F(1.4, -ln + 1.0), F(-2.4, -ln + 1.6)
    # ---- lantern position (swinging on its chain, or lying where it fell)
    hand = R.T(p["hf"])
    if p["lpos"]:
        ring, down = p["lpos"]
    else:
        ring = R.T(p["ring"]) if p["ring"] else (hand[0] + 0.6 - sw * 0.35, hand[1] + CHAIN_IDLE)
        dv = sub(ring, hand)
        dl = math.hypot(*dv) or 1
        down = (dv[0] / dl, dv[1] / dl)
        if down[1] < 0.2:                         # swung high: the cage trails the chain, still hangs roughly down
            down = (down[0] * 0.5, max(down[1], 0.2) + 0.5)
            l2 = math.hypot(*down)
            down = (down[0] / l2, down[1] / l2)
    LL = Ls["LanternBack"] if p["behind"] else Ls["Lantern"]
    lc, lpix = lantern(LL, FX, ring, down, 1.15, p["glow"], fi, p["flare"])
    if not p["lpos"]:
        LL.fixed(chain_px(hand, ring, 0.8 if math.hypot(*sub(ring, hand)) < 7 else 0.0))
    info["lantern"] = lc
    info["hit"] |= lpix
    # ---- back arm (hidden in its sleeve)
    Ba = Ls["BackArm"]
    hb = R.T(p["hb"])
    el = ik(R.T(shB), hb, 5.4, 5.2, (-1, 0.4))
    Ba.paint(n_tube([R.T(shB), el, hb], [1.8, 2.0, 2.3]), "Z", -1)
    Ba.paint(n_dome(add(hb, (0.6, 1.4)), 1.0, 1.2), "E", -1, ao=0)
    # ---- robe + capelet
    Rb = Ls["Robe"]
    if not p["fallen"]:
        m = R.mask(robe_mask(F, P, ln, floor, p["hem"], 5, sw, p["heap"]))
    else:
        m = R.mask([F(-3.4, -ln - 1.2), F(2.8, -ln - 1.4), F(4.2, 2.0), F(5.0, 9.0), F(-1.0, 11.0), F(-6.0, 8.0),
                    F(-4.8, -2.0)])
    Rb.paint(n_plate(m, 2.2, (-0.05, 0.0), 1.0, fold=robe_fold(P, sw)), "Z", 0)
    ys = [q[1] for q in m]
    if ys and not p["fallen"]:
        yb = max(ys)
        Rb.decal([q for q in m if q[1] >= yb - 1], ("Z", 1))                       # hem in shadow
    cape = [F(-4.8, -ln - 0.4), F(3.4, -ln - 1.0), F(4.6, -ln + 4.0), F(3.0, -ln + 5.4), F(1.4, -ln + 4.6),
            F(-0.6, -ln + 6.2), F(-2.4, -ln + 5.0), F(-4.4, -ln + 6.4 - sw * 0.1), F(-5.4, -ln + 3.0)]
    Rb.paint(n_plate(R.mask(cape), 1.4, (-0.1, -0.2), 1.0), "Z", 1)
    # rope cincture, knotted, with two vellum prayer-strips
    R.dline(Rb, F(-4.4, -3.4), F(3.6, -3.6), ("H", 1))
    kn = R.pt(F(3.4, -3.2))
    Rb.fixed({kn: "H2", (kn[0], kn[1] + 1): "H1", (kn[0] - 1, kn[1] + 2): "H1", (kn[0] - 1, kn[1] + 3): "H2"})
    for k, (a_, L_) in enumerate(((-1.2, 5.0), (0.6, 3.6))):
        top = R.pt(F(a_, -3.0))
        for j in range(int(L_)):
            q = (top[0] - (1 if j > 2 and k == 0 and sw > 0.5 else 0), top[1] + j)
            Rb.fixed({q: "H3" if j < 2 else "H2"})
        Rb.fixed({(top[0], top[1] + 1): "H2"})
    if not p["fallen"]:
        for k, off in enumerate(p["feet"]):                                        # bony toes under the hem
            x = P[0] + 2.4 + k * 2.6 + off
            Rb.fixed({(int(x), int(floor)): "E3" if k else "E4", (int(x) + 1, int(floor)): "E2" if k else "E3"})
    # ---- head: tall pointed hood, gaunt face, stitched-shut mouth
    Hl = Ls["Head"]
    G = K.basis(Hd, p["hup"])
    hood = [G(-4.4, 3.4), G(-4.8, -1.6), G(-3.4, -5.6), G(-1.4, -8.4), G(0.6, -10.8), G(1.6, -8.0), G(3.6, -5.0),
            G(4.8, -2.4), G(5.0, 0.6), G(3.4, 1.6), G(2.2, 5.2), G(-2.0, 6.0)]
    Hl.paint(n_plate(R.mask(hood), 1.6, (-0.15, -0.2), 1.1), "Z", 0)
    face = [G(1.0, -2.2), G(3.8, -2.4), G(4.6, -0.6), G(5.8, 1.2), G(4.5, 1.6), G(4.6, 2.8), G(4.2, 4.6),
            G(2.4, 5.4), G(0.8, 1.4)]
    fm = R.mask(face)
    Hl.paint(n_plate(fm, 0.9, (-0.25, -0.05)), "E", 1, ao=0)
    Hl.decal([q for q in fm if q[1] < R.T(G(0, -0.4))[1]], ("E", 1))              # upper face lost in hood shadow
    Hl.decal([q for q in line(R.T(G(1.6, 1.2)), R.T(G(3.0, 2.6))) if q in fm], ("E", 2))   # sunken cheek
    e = R.pt(G(3.2, -0.8))
    Hl.fixed({e: "OUT", (e[0] - 1, e[1]): "E0"})
    # stitched mouth: dark seam with pale thread crossing it
    ms = R.pt(G(3.6, 2.6))
    Hl.fixed({ms: "OUT", (ms[0] + 1, ms[1]): "E1", (ms[0], ms[1] - 1): "H4", (ms[0], ms[1] + 1): "H3",
              (ms[0] + 1, ms[1] - 1): "H3"})
    brow = [G(0.6, -4.0), G(4.9, -3.0), G(5.2, -1.8), G(1.4, -1.6)]
    Hl.paint(n_plate(R.mask(brow), 0.8, (-0.1, -0.5)), "Z", 0, ao=0)
    info["head"] = R.T(G(1, -2))
    # ---- front arm: bell sleeve, skeletal hand gripping the chain
    Fa = Ls["FrontArm"]
    el = ik(R.T(shF), hand, 5.4, 5.4, (-1, 0.5))
    Fa.paint(n_tube([R.T(shF), el, lerp(el, hand, 0.8)], [1.9, 2.1, 2.6]), "Z", 0)
    Fa.paint(n_dome(hand, 1.2, 1.3, tilt=(-0.1, -0.1)), "E", 0, ao=0)
    Fa.fixed({(int(hand[0]) + 1, int(hand[1]) + 1): "E3", (int(hand[0]) - 1, int(hand[1]) + 1): "E2"})
    # ---- the lantern is the only light: violet under-light on the near side
    if p["glow"] > 0.3:
        for L_ in (Rb, Hl, Fa, Ba):
            lantern_rim(L_, lc, 7.5 + p["glow"] * 1.5)
    # ---- fx
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, R.T(g0), a0, R.T(g1), a1, u0, u1, hw=1.6, pal="violet", taper=0.4, exclude=lpix)
    if p["sparks"]:
        cx = lc[0]
        for k in range(12):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 13))
            r = (2 + 7 * hash01(k, 2, 13)) * (0.7 if p["sparks"] == 1 else 1.2)
            q = ip((cx + math.cos(a) * r * 1.2, floor - 0.5 + math.sin(a) * r * (0.9 if p["sparks"] == 1 else 0.5)
                    + (0 if p["sparks"] == 1 else 2)))
            FX.put([q], ("J4", "J3", "J2")[k % 3] if p["sparks"] == 1 else ("J1", "J0")[k % 2])
    if p["smoke"]:
        for k in range(7):
            t = (k / 7 + fi * 0.13) % 1.0
            q = ip((lc[0] + math.sin(k * 1.7 + t * 5) * 1.5, lc[1] - 5 - t * 7 * p["smoke"]))
            FX.put([q], "Z4" if t < 0.5 else "Z3")
    return Ls, info


def c_idle():
    fr = []
    for i in range(4):
        b = (0.0, 0.5, 1.0, 0.5)[i]
        fr.append((200, LP(C=(16.4, 20.0 + b * 0.4), Hd=(19.0 + b * 0.1, 12.6 + b * 0.6), hf=(24.0, 29.0 + b * 0.4),
                           hb=(12.0, 29.5 + b * 0.4), hem=i, glow=(1.0, 1.2, 0.9, 1.1)[i])))
    return fr


def c_walk():
    fr = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.6 * abs(s_)
        fr.append((150, LP(P=(15.0 + 0.3 * c, 32.0 + b * 0.3), C=(16.8 + 0.4 * c, 20.0 + b), Hd=(19.5 + 0.4 * c, 12.6 + b),
                           hf=(24.2 + 0.3 * c, 29.0 + b), hb=(12.2 - 0.6 * c, 29.4 + b), hem=i,
                           feet=(1.5 * c, -1.5 * c), glow=1.0 + 0.15 * s_, wind=-1.5)))
    return fr


def c_swing():
    lean_b = dict(P=(14.6, 32.0), C=(14.6, 20.2), Hd=(16.4, 13.0), hup=(0.05, -1))
    up_ = dict(P=(14.4, 32.0), C=(14.2, 20.0), Hd=(15.8, 12.8), hup=(-0.05, -1))
    lunge = dict(P=(15.8, 32.0), C=(19.0, 20.8), Hd=(22.6, 14.2), hup=(0.7, -1))
    low = dict(P=(16.0, 32.2), C=(19.6, 22.0), Hd=(23.4, 15.8), hup=(0.9, -1))
    return [
        (150, LP(**lean_b, hf=(19.0, 28.0), hb=(10.6, 28.6), ring=(15.0, 35.0), behind=True, glow=1.2)),
        (140, LP(**lean_b, hf=(13.4, 20.4), hb=(9.8, 27.4), ring=(5.4, 25.0), behind=True, glow=1.4)),
        (140, LP(**up_, hf=(14.6, 11.4), hb=(10.0, 26.4), ring=(5.0, 7.0), glow=1.7, flare=0.4)),
        (300, LP(**up_, hf=(15.4, 10.2), hb=(10.2, 26.0), ring=(6.4, 2.4), glow=2.2, flare=0.8)),
        (70, LP(**lunge, hf=(25.0, 15.0), hb=(13.0, 27.0), ring=(32.0, 7.0), glow=2.0, wind=3,
                smear=[((15.4, 10.2), -135, (25.0, 15.0), -40, 6.0, 10.0)])),
        (70, LP(**lunge, hf=(28.0, 22.0), hb=(13.6, 27.4), ring=(35.0, 24.5), glow=2.0, wind=3,
                smear=[((25.0, 15.0), -40, (28.0, 22.0), 13, 6.0, 10.0)])),
        (90, LP(**low, hf=(27.4, 27.0), hb=(14.0, 28.4), ring=(33.4, 36.6), glow=1.6, sparks=1,
                smear=[((28.0, 22.0), 13, (27.4, 27.0), 60, 5.0, 11.0)])),
        (140, LP(**low, hf=(26.6, 28.0), hb=(14.0, 28.6), ring=(29.6, 37.0), glow=1.2, sparks=2)),
        (160, LP(P=(15.4, 32.0), C=(17.6, 20.6), Hd=(20.6, 13.4), hup=(0.5, -1), hf=(24.8, 29.0), ring=(28.0, 34.0),
                 glow=1.0)),
        (160, LP(hf=(24.2, 29.0), ring=(25.8, 34.0))),
    ]


def c_hurt():
    return [(90, LP(P=(14.6, 32.0), C=(14.2, 20.4), Hd=(15.6, 13.4), hup=(-0.3, -1), hf=(21.6, 28.0), hb=(10.0, 28.0),
                    ring=(26.4, 32.4), glow=1.8)),
            (140, LP(P=(14.8, 32.0), C=(15.4, 20.2), Hd=(17.6, 12.9), hup=(0.1, -1), hf=(23.0, 28.6), ring=(25.8, 33.4),
                     glow=1.2))]


def c_death():
    kneel = dict(P=(15.0, 38.0), C=(17.8, 27.0), Hd=(22.0, 22.0), hup=(0.9, -1), hf=(23.4, 37.0), hb=(13.0, 37.0),
                 heap=1.0, lpos=((29.0, 36.4), (0.0, 1.0)))
    sn = ["BackArm", "Robe", "Head", "FrontArm"]
    ash = ("H3", "Z4", "Z3", "Z2", "Z1")
    return [
        (110, LP(P=(14.4, 32.0), C=(13.8, 20.6), Hd=(14.6, 13.8), hup=(-0.5, -1), hf=(21.0, 30.0), hb=(9.6, 28.0),
                 ring=(24.0, 35.0), glow=1.6)),
        (140, LP(P=(14.8, 35.0), C=(16.4, 24.0), Hd=(19.6, 17.4), hup=(0.5, -1), hf=(23.0, 33.0), hb=(11.6, 33.0),
                 heap=0.5, ring=(26.0, 36.4), glow=1.3)),
        (200, LP(**kneel, glow=1.0)),
        (130, LP(**kneel, glow=0.7, post=collapse(sn, 0.62, 0.1, pal=ash, spread=0.3))),
        (150, LP(**kneel, glow=0.35, post=collapse(sn, 0.3, 0.18, pal=ash, spread=0.5))),
        (700, LP(**kneel, glow=0.0, smoke=1, post=collapse(sn, 0.16, 0.2, pal=ash, spread=0.6))),
    ]


def build_monk():
    K.setup(40, 48)
    anims, infos = render_anims("lantern_monk", MONK_L, draw_monk,
                                [("idle", c_idle), ("walk", c_walk), ("swing", c_swing), ("hurt", c_hurt),
                                 ("death", c_death)], loops=("idle", "walk"))
    meta = {"native": 1, "frame": [40, 48], "anchor": [16, 48],
            "hurtbox": hurtbox(anims, ["Robe", "Head"], inset=(2, 3, 2)),
            "attacks": {"swing": {"active": [5, 6], "hit": hit_rect(infos, "swing", [5, 6], x_min=22)}},
            "telegraph": {"swing": {"frame": 4, "at": spawn_pt(infos["swing"][4]["lantern"])}},
            "notes": "faces right; swing: lantern whirled up behind and held overhead (frames 1-3, 3 = held windup with "
                     "the flame flaring), whipped over (4) and down in front (active 5-6, low enough to hit the floor), "
                     "follow-through 7, recover 8-9. The lantern flame is the only light source (engine may add a "
                     "violet point light at the lantern; frame-0 lantern centre = hurtbox-relative idle position)."}
    export("lantern_monk", MONK_L, anims, meta)
    return meta



# =========================================================================== 4. HEAD LIBRARIAN (mini-boss)
LIB_L = ["LanternBack", "BackArm", "Robe", "Keys", "Head", "FrontArm", "Lantern", "FX"]
B_NEU = dict(P=(28.0, 44.0), C=(31.0, 25.0), Hd=(38.0, 15.4), hup=(0.55, -1), hf=(46.0, 41.0), hb=(22.0, 44.0),
             ring=None, ldir=None, behind=False, glow=1.2, flare=0.0, lid=0.0, heap=0.0, smear=None, sparks=0,
             burst=0, smoke=0, crack=0, mask=True, hem=0, rot=0.0, piv=(0, 0), lpos=None, wind=0.0, feet=(0.0, 0.0),
             snuff=0, pages=0.0, bgrip=None, eye=1)
BP = mk(B_NEU)
LSC = 2.0
BCHAIN = 4.0


def key_px(top, sw, big=False):
    """A hanging iron-bronze key: ring, shaft, toothed bit."""
    x, y = ip((top[0] - sw * 0.25, top[1]))
    px = {(x, y): "G2", (x - 1, y + 1): "G2", (x + 1, y + 1): "G1", (x, y + 2): "G1"}
    L_ = 4 if big else 3
    for j in range(L_):
        px[(x, y + 3 + j)] = "G2" if j == 0 else "G1"
    px[(x + 1, y + 2 + L_)] = "G2"
    px[(x + 1, y + 1 + L_)] = "G1"
    return px


def lib_cape(F, ln, depth, width, fi, seed, sw):
    pts = [F(-6.6 * width, -ln + 0.4), F(-4.0 * width, -ln - 1.4), F(4.0 * width, -ln - 1.8), F(6.6 * width, -ln + 0.6),
           F(5.8 * width, -ln + depth * 0.7)]
    n = 7
    for i in range(n + 1):
        t = i / n
        a = 5.8 * width - 12.4 * width * t
        d = depth + (1.6 if i % 2 == 0 else -0.4) * (0.7 + 0.6 * hash01(i, fi // 3, seed)) + t * 1.2 - sw * 0.1 * t
        pts.append(F(a, -ln + d))
    pts.append(F(-6.8 * width, -ln + depth * 0.5))
    return pts


def draw_librarian(p, fi, sw):
    Ls = {n: Layer(n) for n in LIB_L if n != "FX"}
    FX = FXLayer("FX")
    Ls["FX"] = FX
    R = Rig(p["rot"], p["piv"])
    P, C, Hd = p["P"], p["C"], p["Hd"]
    up = sub(C, P)
    ln = math.hypot(*up)
    F = K.basis(P, up)
    info = {"hit": set()}
    floor = K.H - 1.0
    shF, shB = F(2.6, -ln + 1.8), F(-3.6, -ln + 2.6)
    hand = R.T(p["hf"])
    # ---- the censer
    if p["lpos"]:
        ring, down = p["lpos"]
    else:
        ring = R.T(p["ring"]) if p["ring"] else (hand[0] + 0.8 - sw * 0.4, hand[1] + BCHAIN)
        if p["ldir"]:
            down = p["ldir"]
            l2 = math.hypot(*down)
            down = (down[0] / l2, down[1] / l2)
        else:
            dv = sub(ring, hand)
            dl = math.hypot(*dv) or 1
            down = (dv[0] / dl, dv[1] / dl)
            if dl < 6.5:                          # short grip: the censer simply hangs
                down = (dv[0] / dl * 0.25, 1.0)
                l2 = math.hypot(*down)
                down = (down[0] / l2, down[1] / l2)
            elif down[1] < 0.3:
                down = (down[0] * 0.5, max(down[1], 0.2) + 0.6)
                l2 = math.hypot(*down)
                down = (down[0] / l2, down[1] / l2)
    LL = Ls["LanternBack"] if p["behind"] else Ls["Lantern"]
    lc, lpix = lantern(LL, FX, ring, down, LSC, p["glow"], fi, p["flare"], lid=p["lid"])
    if not p["lpos"]:
        LL.fixed(chain_px(hand, ring, 1.0 if math.hypot(*sub(ring, hand)) < 8 else 0.0, "K3", "K1"))
    info["lantern"] = lc
    info["hit"] |= lpix
    # censer smoke curling off the roof
    if p["glow"] > 0.2 and not p["snuff"]:
        roof = madd(ring, (down, 1.6 * LSC))
        for k in range(6):
            t = ((fi * 0.17 + k / 6) % 1.0)
            q = ip((roof[0] - t * 5 + math.sin(t * 7 + k) * 1.2, roof[1] - 1 - t * 9))
            FX.put([q], "Z5" if t < 0.35 else "Z4" if t < 0.7 else "Z3")
    # ---- back arm: long sleeve, skeletal forearm
    Ba = Ls["BackArm"]
    hb = R.T(p["hb"])
    el = ik(R.T(shB), hb, 10.0, 10.0, (-1, 0.3))
    Ba.paint(n_tube([R.T(shB), el, lerp(el, hb, 0.4)], [2.6, 2.8, 3.6]), "Z", -1)
    Ba.paint(n_tube([lerp(el, hb, 0.3), hb], [1.0, 0.8]), "E", -1)
    Ba.paint(n_dome(hb, 1.3, 1.5), "E", -1, ao=0)
    for k in range(3):
        Ba.fixed({(int(hb[0]) - 1 + k, int(hb[1]) + 2): "E2", (int(hb[0]) - 1 + k, int(hb[1]) + 3 - (k == 1)): "E1"})
    # ---- robe: floor-length underrobe, two ragged mantles, stole of pressed pages
    Rb = Ls["Robe"]
    if p["heap"] < 1.5:
        m = R.mask(robe_mask(F, P, ln, floor, p["hem"], 9, sw, p["heap"], w=1.55, trail=1.6))
    else:
        m = R.mask(robe_mask(F, P, ln, floor, p["hem"], 9, sw, 1.0, w=1.55, trail=1.6))
    Rb.paint(n_plate(m, 2.6, (-0.05, 0.0), 1.0, fold=robe_fold(P, sw)), "Z", 0)
    ys = [q[1] for q in m]
    yb = max(ys)
    Rb.decal([q for q in m if q[1] >= yb - 1], ("Z", 1))
    c2 = R.mask(lib_cape(F, ln, 14.0, 1.25, p["hem"], 4, sw))
    Rb.paint(n_plate(c2, 1.8, (-0.1, -0.1), 1.0, fold=robe_fold(P, sw)), "Z", 0)
    c1 = R.mask(lib_cape(F, ln, 8.5, 1.3, p["hem"], 8, sw))
    Rb.paint(n_plate(c1, 1.6, (-0.2, -0.35), 1.0), "Z", 1)
    Rb.decal([q for q in c1 if (q[0], q[1] - 1) not in c1 and (q[0] - 1, q[1]) in c1], ("Z", 5))
    # stole of pressed pages hanging from the neck
    st = [F(2.0, -ln + 3.0), F(5.4, -ln + 2.4), F(6.4, 7.0), F(5.6, 10.4), F(4.6, 8.8), F(3.6, 11.2), F(2.8, 7.6)]
    sm = R.mask(st)
    Rb.paint(n_plate(sm, 0.9, (-0.3, 0.0)), "H", 0, ao=0)
    for q in sm:
        v = (q[1] - int(P[1])) % 3
        if v == 0:
            Rb.decal([q], ("H", 1))
        elif v == 1 and hash01(q[0], q[1], 71) < 0.45:
            Rb.decal([q], ("N", 3))                       # script
    # belt with a ring of keys
    R.dline(Rb, F(-6.4, -4.2), F(5.2, -4.6), ("L", 1))
    if not p["heap"]:
        for k, off in enumerate(p["feet"]):
            x = P[0] + 3.6 + k * 3.6 + off
            Rb.fixed({(int(x), int(floor)): "E3", (int(x) + 1, int(floor)): "E2", (int(x) + 2, int(floor)): "E1"})
    # ---- keys: bandolier across the chest + ring at the hip
    Kl = Ls["Keys"]
    a_, b_ = R.T(F(-3.4, -ln + 3.0)), R.T(F(5.0, -6.4))
    Kl.fixed(chain_px(a_, b_, 2.0, "K3", "K1"))
    for k, t in enumerate((0.34, 0.6, 0.84)):
        c = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t + 2.0 * 4 * t * (1 - t) + 1)
        Kl.fixed(key_px(c, sw * (1 + k * 0.2), big=(k == 1)))
    kr = R.T(F(-2.0, -3.4))
    Kl.fixed({q: "K3" for q in mask_disc((kr[0] + .5, kr[1] + 1.5), 1.8) - mask_disc((kr[0] + .5, kr[1] + 1.5), 0.9)})
    for k in range(2):
        Kl.fixed(key_px((kr[0] - 1.0 + k * 2.2, kr[1] + 3.0), sw * 1.5, big=k == 0))
    # ---- head: towering hood, mask of pressed pages
    Hl = Ls["Head"]
    G = K.basis(Hd, p["hup"])
    hood = [G(-6.6, 5.0), G(-7.2, -2.4), G(-5.0, -8.4), G(-2.2, -12.4), G(0.4, -16.2), G(2.0, -12.0), G(5.2, -7.6),
            G(7.0, -3.8), G(7.2, 1.2), G(5.0, 2.8), G(3.2, 7.6), G(-3.0, 9.0)]
    Hl.paint(n_plate(R.mask(hood), 2.0, (-0.15, -0.2), 1.1), "Z", 0)
    hol = [G(0.4, -6.0), G(6.4, -5.6), G(7.8, 1.0), G(5.4, 8.6), G(1.0, 7.6)]
    Hl.paint(n_plate(R.mask(hol), 1.0, (0.3, 0.3)), "Z", -2, ao=0)
    if p["mask"]:
        mk_ = [G(1.8, -5.2), G(5.8, -5.2), G(7.4, -3.0), G(7.0, -1.6), G(8.8, 2.4), G(8.4, 5.2), G(6.0, 8.4),
               G(3.8, 7.2), G(2.4, 3.4), G(1.6, 0.0)]
        mm = R.mask(mk_)
        Hl.paint(n_plate(mm, 1.1, (-0.3, -0.05), 1.0), "H", 0, ao=0)
        rows = sorted({q[1] for q in mm})
        for q in mm:
            if (q[1] - rows[0]) % 2 == 1 and hash01(q[0], q[1], 81) < 0.75:
                Hl.decal([q], ("H", 2))                   # layered page edges
        eye0, eye1 = R.T(G(4.0, -1.6)), R.T(G(7.0, -1.0))
        Hl.decal([q for q in line(eye0, eye1) if q in mm], "OUT")
        if p["eye"]:
            e = ip(lerp(eye0, eye1, 0.6))
            Hl.fixed({e: "J3" if p["eye"] == 1 else "J4"})
            if p["eye"] > 1:
                FX.put([(e[0] + 1, e[1]), (e[0], e[1] - 1)], "J1")
        Hl.decal([q for q in polyline([R.T(G(5.6, 2.4)), R.T(G(6.4, 3.6)), R.T(G(5.4, 5.2))]) if q in mm], ("H", 1))
        if p["crack"]:
            crk = polyline([R.T(G(3.6, -4.6)), R.T(G(4.6, -2.4)), R.T(G(3.8, 0.4)), R.T(G(5.2, 3.2))])
            Hl.decal([q for q in crk if q in mm], "OUT")
            if p["crack"] > 1:
                Hl.erase([q for q in mm if q[1] > R.T(G(0, 3.0))[1] and hash01(q[0], q[1], 83) < 0.5])
    else:
        # the hood is empty: only darkness and one ember of violet
        e = R.pt(G(4.8, -0.8))
        Hl.fixed({e: "J1"} if p["eye"] else {})
    brow = [G(1.0, -6.4), G(6.8, -5.4), G(7.4, -3.6), G(1.8, -3.8)]
    Hl.paint(n_plate(R.mask(brow), 0.9, (-0.1, -0.5)), "Z", 0, ao=0)
    info["mask"] = R.T(G(6.0, 0.0))
    # ---- front arm: sleeve, skeletal forearm, long fingers round the chain
    Fa = Ls["FrontArm"]
    el = ik(R.T(shF), hand, 10.0, 10.0, (-1, 0.5))
    Fa.paint(n_tube([R.T(shF), el, lerp(el, hand, 0.45)], [2.8, 3.0, 3.8]), "Z", 0)
    Fa.paint(n_tube([lerp(el, hand, 0.35), hand], [1.1, 0.9]), "E", 0)
    Fa.paint(n_dome(hand, 1.5, 1.6, tilt=(-0.1, -0.1)), "E", 0, ao=0)
    Fa.fixed({(int(hand[0]) + 1, int(hand[1]) + 2): "E3", (int(hand[0]) - 1, int(hand[1]) + 2): "E2",
              (int(hand[0]) + 2, int(hand[1]) + 1): "E4"})
    if p["bgrip"]:                                  # back hand drawn over the lantern (snuffing)
        g = R.T(p["bgrip"])
        Fa.paint(n_dome(g, 1.5, 1.4), "E", 0, ao=0)
        for k in range(3):
            Fa.fixed({(int(g[0]) - 1 + k, int(g[1]) + 1 + (k == 1)): "E3"})
    # ---- lantern light
    if p["glow"] > 0.3:
        for L_ in (Rb, Hl, Fa, Ba, Kl):
            lantern_rim(L_, lc, 11.0 + p["glow"] * 2.0 + p["flare"] * 3)
    # ---- fx
    if p["smear"]:
        for (g0, a0, g1, a1, u0, u1) in p["smear"]:
            info["hit"] |= swept(FX, R.T(g0), a0, R.T(g1), a1, u0, u1, hw=2.6, pal="violet", taper=0.35, exclude=lpix)
    if p["sparks"]:
        cx = lc[0]
        for k in range(16):
            a = -math.pi * (0.08 + 0.84 * hash01(k, 1, 23))
            r = (3 + 10 * hash01(k, 2, 23)) * (0.7 if p["sparks"] == 1 else 1.2)
            q = ip((cx + math.cos(a) * r * 1.3, floor - 0.5 + math.sin(a) * r * (0.9 if p["sparks"] == 1 else 0.5)
                    + (0 if p["sparks"] == 1 else 2.5)))
            FX.put([q], ("J4", "J3", "J2")[k % 3] if p["sparks"] == 1 else ("J1", "J0")[k % 2])
    if p["burst"]:                                  # violet fire erupting where the censer struck the floor
        st_ = p["burst"]
        cx = lc[0]
        for k in range(-4, 5):
            x = cx + k * (2.2 if st_ == 1 else 2.8)
            hgt = (9 - abs(k) * 1.6) * (1.0 if st_ == 1 else 0.6) + hash01(k, st_, 3) * 3
            if hgt <= 0.5:
                continue
            K.flame(FX, (x, floor + 0.5), hgt / 1.8, fi + k, seed=k, pal=("J4", "J4", "J3", "J2", "J1", "J0"))
            info["hit"] |= {(int(x), int(floor - hgt))}
    if p["snuff"]:                                  # all light snuffed: a ring of black smoke
        r = 5 + p["snuff"] * 5
        for k in range(26):
            a = k * 2 * math.pi / 26
            for dr in (0.0, 1.2):
                q = ip((lc[0] + math.cos(a) * (r + dr), lc[1] + math.sin(a) * (r + dr) * 0.75))
                FX.put([q], ("N1" if dr == 0 else "Z3") if (k + p["snuff"]) % 3 else "Z4")
        for k in range(10):
            a = k * 2 * math.pi / 10 + 0.3
            q = ip((lc[0] + math.cos(a) * r * 0.5, lc[1] + math.sin(a) * r * 0.4))
            FX.put([q], "N2")
    if p["smoke"]:
        for k in range(10):
            t = (k / 10 + fi * 0.11) % 1.0
            q = ip((lc[0] + math.sin(k * 1.7 + t * 5) * 2.0, lc[1] - 8 - t * 12 * p["smoke"]))
            FX.put([q], "Z4" if t < 0.5 else "Z3")
    if p["pages"]:
        for k in range(7):
            a = -math.pi * (0.1 + 0.8 * hash01(k, 1, 91))
            r = 3 + 12 * p["pages"] * hash01(k, 2, 91)
            c = (info["mask"][0] + math.cos(a) * r * 0.8, info["mask"][1] + math.sin(a) * r * 0.4 + p["pages"] * 22 * hash01(k, 3, 91))
            if c[1] < floor:
                ang = 360 * hash01(k, 5, 91) + p["pages"] * 120
                d, pv = dirv(ang), dirv(ang + 90)
                pts = [madd(c, (d, -1.6), (pv, -1.0)), madd(c, (d, 1.6), (pv, -0.8)), madd(c, (d, 1.4), (pv, 1.0)),
                       madd(c, (d, -1.4), (pv, 0.8))]
                Ls["Lantern"].paint(n_plate(poly_mask(pts), 0.8, (0.0, -0.2)), "H", -(k % 2))
    return Ls, info


def b_idle():
    fr = []
    for i in range(6):
        b = 0.5 - 0.5 * math.cos(i * math.pi / 3)
        fr.append((190, BP(C=(31.0, 25.0 + b * 0.6), Hd=(38.0 + b * 0.2, 15.4 + b * 1.0), hf=(46.0, 41.0 + b * 0.6),
                           hb=(22.0, 44.0 + b * 0.5), hem=i, glow=1.2 + 0.2 * math.sin(i * 2.1))))
    return fr


def b_walk():
    fr = []
    for i in range(8):
        ph = 2 * math.pi * i / 8
        c, s_ = math.cos(ph), math.sin(ph)
        b = 0.8 * abs(s_)
        fr.append((150, BP(P=(28.0 + 0.4 * c, 44.0 + b * 0.4), C=(31.4 + 0.6 * c, 25.0 + b), Hd=(38.6 + 0.6 * c, 15.4 + b),
                           hf=(46.2 + 0.4 * c, 41.0 + b), hb=(22.4 - 1.0 * c, 44.0 + b), hem=i, feet=(2.0 * c, -2.0 * c),
                           glow=1.2 + 0.15 * s_, wind=-1.5)))
    return fr


LEAN_B = dict(P=(27.4, 44.0), C=(28.4, 25.4), Hd=(34.4, 16.4), hup=(0.3, -1))
LUNGE = dict(P=(29.0, 44.0), C=(33.6, 26.0), Hd=(41.0, 17.4), hup=(0.8, -1))
TALL = dict(P=(27.6, 44.0), C=(29.2, 24.4), Hd=(34.6, 14.4), hup=(0.2, -1))


def b_swing():
    return [
        (150, BP(**LEAN_B, hf=(38.0, 42.0), hb=(20.0, 44.0), ring=(28.0, 52.0), behind=True, glow=1.4)),
        (160, BP(**LEAN_B, hf=(30.0, 40.0), hb=(19.0, 43.0), ring=(18.0, 44.0), ldir=(-0.5, 0.87), behind=True,
                 glow=1.6)),
        (260, BP(**LEAN_B, hf=(27.0, 37.0), hb=(18.6, 42.0), ring=(16.0, 36.0), ldir=(-0.45, 0.9), behind=True,
                 glow=2.0, flare=0.8)),
        (80, BP(**LUNGE, hf=(46.0, 42.0), hb=(24.0, 44.0), ring=(54.0, 48.0), ldir=(0.35, 0.94), glow=2.0, wind=3,
                smear=[((27.0, 37.0), 150, (46.0, 42.0), 40, 9.0, 24.0)])),
        (90, BP(**LUNGE, hf=(50.0, 38.0), hb=(25.0, 43.0), ring=(58.0, 38.0), ldir=(0.45, 0.9), glow=2.0,
                smear=[((46.0, 42.0), 40, (50.0, 38.0), 0, 9.0, 22.0)])),
        (140, BP(**LUNGE, hf=(46.0, 30.0), hb=(24.0, 42.0), ring=(55.0, 20.0), ldir=(0.3, 0.95), glow=1.6)),
        (140, BP(**TALL, hf=(38.0, 20.0), hb=(22.0, 40.0), ring=(28.0, 10.0), ldir=(-0.3, 0.95), behind=True,
                 glow=1.7)),
        (240, BP(**TALL, hf=(34.0, 18.0), hb=(21.0, 40.0), ring=(18.0, 12.0), ldir=(-0.5, 0.87), behind=True,
                 glow=2.1, flare=0.8)),
        (80, BP(**LUNGE, hf=(46.0, 24.0), hb=(24.0, 42.0), ring=(58.0, 18.0), ldir=(0.4, 0.92), glow=2.0, wind=3,
                smear=[((34.0, 20.0), -150, (46.0, 24.0), -25, 9.0, 19.0)])),
        (90, BP(**dict(LUNGE, C=(34.4, 27.4), Hd=(42.0, 19.4)), hf=(50.0, 40.0), hb=(25.0, 43.0), ring=(56.0, 48.0),
                ldir=(0.2, 0.98), glow=1.8, sparks=1, smear=[((46.0, 24.0), -25, (50.0, 40.0), 60, 8.0, 24.0)])),
        (160, BP(**LUNGE, hf=(47.0, 42.0), hb=(24.0, 44.0), ring=(52.0, 47.0), ldir=(0.3, 0.95), glow=1.4, sparks=2)),
        (180, BP(hf=(46.4, 41.0))),
    ]


def b_snuff():
    raise_ = dict(P=(27.6, 44.0), C=(29.8, 24.6), Hd=(36.0, 15.0), hup=(0.35, -1))
    return [
        (160, BP(hf=(44.0, 34.0), hb=(22.0, 42.0), ring=(45.0, 38.0), glow=1.3)),
        (160, BP(**raise_, hf=(46.0, 24.0), hb=(30.0, 34.0), ring=(47.0, 27.0), glow=1.6)),
        (180, BP(**raise_, hf=(51.0, 10.0), hb=(34.0, 26.0), ring=(52.0, 11.0), glow=2.0, flare=0.6)),
        (200, BP(**raise_, hf=(52.0, 8.6), hb=(44.0, 14.0), ring=(53.0, 9.6), glow=2.4, flare=1.2, eye=2)),
        (320, BP(**raise_, hf=(52.0, 8.2), hb=(50.0, 12.0), ring=(53.0, 9.2), glow=2.8, flare=1.6, eye=2,
                 bgrip=(53.0, 14.4), lid=0.25)),
        (100, BP(**raise_, hf=(52.0, 8.2), hb=(50.0, 13.0), ring=(53.0, 9.2), glow=0.6, lid=1.0, eye=2,
                 bgrip=(53.0, 17.0))),
        (90, BP(**raise_, hf=(52.0, 8.6), hb=(48.0, 16.0), ring=(53.0, 9.6), glow=0.0, lid=1.0, snuff=1, eye=2)),
        (170, BP(**raise_, hf=(51.0, 10.0), hb=(42.0, 22.0), ring=(52.0, 11.0), glow=0.0, lid=1.0, snuff=2, eye=2)),
        (180, BP(hf=(45.0, 34.0), hb=(24.0, 42.0), ring=(46.0, 38.0), glow=0.0, lid=0.6, smoke=1)),
        (180, BP(hf=(46.0, 40.0), ring=(47.0, 44.0), glow=0.6)),
    ]


def b_slam():
    arch = dict(P=(27.0, 44.0), C=(27.0, 25.2), Hd=(32.0, 15.6), hup=(-0.1, -1))
    low = dict(LUNGE, P=(29.4, 44.4), C=(35.0, 28.4), Hd=(43.0, 21.0))
    return [
        (150, BP(hf=(44.0, 34.0), hb=(30.0, 38.0), ring=(45.0, 38.0), glow=1.3)),
        (150, BP(**TALL, hf=(40.0, 22.0), hb=(34.0, 26.0), ring=(41.0, 26.0), glow=1.5)),
        (160, BP(**arch, hf=(30.0, 18.0), hb=(28.0, 20.0), ring=(20.0, 14.0), ldir=(-0.6, 0.8), behind=True,
                 glow=1.8, flare=0.5)),
        (320, BP(**arch, hf=(28.0, 16.0), hb=(26.0, 18.0), ring=(15.0, 14.0), ldir=(-0.5, 0.87), behind=True,
                 glow=2.4, flare=1.2, eye=2)),
        (70, BP(**LUNGE, hf=(46.0, 16.0), hb=(40.0, 19.0), ring=(54.0, 13.0), ldir=(0.6, 0.8), glow=2.2, wind=3,
                smear=[((28.0, 18.0), -160, (46.0, 16.0), -30, 8.0, 19.0)])),
        (70, BP(**dict(LUNGE, C=(34.4, 27.4), Hd=(42.0, 19.4)), hf=(52.0, 30.0), hb=(46.0, 32.0), ring=(58.0, 34.0),
                ldir=(0.3, 0.95), glow=2.2, smear=[((46.0, 16.0), -30, (52.0, 30.0), 50, 8.0, 22.0)])),
        (90, BP(**low, hf=(52.0, 40.0), hb=(46.0, 41.0), ring=(56.0, 46.0), ldir=(0.0, 1.0), glow=2.4, burst=1,
                sparks=1)),
        (110, BP(**low, hf=(52.0, 40.0), hb=(46.0, 41.0), ring=(56.0, 46.0), ldir=(0.0, 1.0), glow=1.8, burst=2,
                 sparks=2)),
        (200, BP(**LUNGE, hf=(49.0, 40.0), hb=(30.0, 42.0), ring=(52.0, 45.0), ldir=(0.2, 0.98), glow=1.4, smoke=1)),
        (200, BP(hf=(46.4, 41.0))),
    ]


def b_stagger():
    back = dict(P=(26.6, 44.0), C=(26.0, 25.6), Hd=(30.4, 17.0), hup=(-0.3, -1))
    return [
        (120, BP(**back, hf=(40.0, 44.0), hb=(30.0, 20.0), ring=(47.0, 50.0), glow=1.8, eye=2, crack=1)),
        (140, BP(**back, hf=(41.0, 45.0), hb=(32.0, 19.0), ring=(44.0, 51.0), glow=1.5, eye=2, crack=1)),
        (160, BP(P=(27.0, 44.0), C=(28.4, 25.6), Hd=(34.0, 16.6), hup=(0.2, -1), hf=(43.0, 44.0), hb=(26.0, 34.0),
                 ring=(42.4, 50.6), glow=1.3, crack=1)),
        (200, BP(hf=(45.4, 43.4), hb=(23.0, 42.0), ring=(45.6, 48.6), glow=1.2, crack=1)),
    ]


def b_death():
    kneel = dict(P=(27.0, 52.0), C=(30.4, 34.0), Hd=(37.6, 27.0), hup=(0.8, -1), hf=(44.0, 52.0), hb=(22.0, 54.0),
                 heap=1.0, lpos=((50.0, 48.0), (0.0, 1.0)))
    sn = ["BackArm", "Robe", "Keys", "Head", "FrontArm"]
    ash = ("H3", "Z4", "Z3", "Z2", "Z1")
    return [
        (120, BP(P=(26.6, 44.0), C=(25.6, 25.8), Hd=(29.6, 17.4), hup=(-0.4, -1), hf=(40.0, 44.0), hb=(28.0, 22.0),
                 ring=(48.0, 50.0), glow=2.0, eye=2, crack=1)),
        (140, BP(P=(26.6, 46.0), C=(27.0, 27.6), Hd=(32.0, 19.6), hup=(0.1, -1), hf=(42.0, 46.0), hb=(22.0, 46.0),
                 ring=(38.0, 52.0), glow=1.6, crack=2, pages=0.1, heap=0.4)),
        (160, BP(P=(26.8, 49.0), C=(29.0, 31.0), Hd=(35.0, 23.4), hup=(0.5, -1), hf=(44.0, 49.0), hb=(22.0, 50.0),
                 ring=(46.0, 52.0), glow=1.3, crack=2, pages=0.3, heap=0.7)),
        (200, BP(**kneel, glow=1.1, crack=2, pages=0.5)),
        (200, BP(**kneel, glow=0.9, mask=False, pages=0.75)),
        (140, BP(**kneel, glow=0.8, mask=False, pages=1.0, eye=0, post=collapse(sn, 0.72, 0.08, pal=ash, spread=0.2))),
        (140, BP(**kneel, glow=0.6, mask=False, eye=0, post=collapse(sn, 0.48, 0.14, pal=ash, spread=0.35))),
        (160, BP(**kneel, glow=0.4, mask=False, eye=0, post=collapse(sn, 0.28, 0.2, pal=ash, spread=0.5))),
        (200, BP(**kneel, glow=0.2, mask=False, eye=0, post=collapse(sn, 0.16, 0.24, pal=ash, spread=0.6))),
        (900, BP(**kneel, glow=0.0, mask=False, eye=0, smoke=1, post=collapse(sn, 0.12, 0.26, pal=ash, spread=0.65))),
    ]


def build_librarian():
    K.setup(72, 72)
    anims, infos = render_anims("head_librarian", LIB_L, draw_librarian,
                                [("idle", b_idle), ("walk", b_walk), ("swing", b_swing), ("snuff", b_snuff),
                                 ("slam", b_slam), ("stagger", b_stagger), ("death", b_death)], loops=("idle", "walk"))
    meta = {"native": 1, "frame": [72, 72], "anchor": [29, 72],
            "hurtbox": hurtbox(anims, ["Robe", "Head"], inset=(4, 4, 3)),
            "attacks": {
                "swing": {"windows": [
                    {"active": [3, 4], "hit": hit_rect(infos, "swing", [3, 4], x_min=36)},
                    {"active": [8, 9], "hit": hit_rect(infos, "swing", [8, 9], x_min=36)}]},
                "slam": {"active": [6, 7], "hit": hit_rect(infos, "slam", [6, 7], x_min=38)}},
            "spawn": {"snuff": {"frame": 6, "at": spawn_pt(infos["snuff"][6]["lantern"])},
                      "slam": {"frame": 6, "at": [int(infos["slam"][6]["lantern"][0]), 71]}},
            "telegraph": {"swing": {"frame": 2, "at": spawn_pt(infos["swing"][2]["lantern"])},
                          "snuff": {"frame": 4, "at": spawn_pt(infos["snuff"][4]["lantern"])},
                          "slam": {"frame": 3, "at": spawn_pt(infos["slam"][3]["lantern"])}},
            "light": {"idle": spawn_pt(infos["idle"][0]["lantern"])},
            "notes": "faces right. swing: two chain swings -- window 0 low underhand sweep (wind-up held on frame 2), "
                     "window 1 overhead smash (wind-up held on frame 7). snuff: lantern raised, flame flares (4, held), "
                     "lid clamps (5), all light snuffed on frame 6 -- spawn the darkness effect at spawn.snuff.at; the "
                     "lantern stays dark until frame 9. slam: censer hoisted behind (3 held), smashed into the floor, "
                     "active 6-7 with violet fire erupting (spawn.slam = floor impact point, frame 6). light.idle = "
                     "censer centre for an engine point light. Telegraph 'at' = glint point."}
    export("head_librarian", LIB_L, anims, meta)
    return meta



# =========================================================================== projectile
def build_projectiles3():
    """proj_inkbolt 16x12, flying right, centred on (8, 6): a glossy black ink teardrop with a violet-hot
    leading edge, a writhing tail and shed droplets."""
    K.setup(16, 12)
    frames = []
    for i in range(4):
        core, trail = FXLayer("Core"), FXLayer("Trail")
        cx, cy = 10.0, 6.0
        wob = (0.0, 0.4, 0.0, -0.4)[i]
        for y in range(12):
            for x in range(16):
                dx, dy = x + .5 - cx, y + .5 - cy
                if dx >= 0:
                    r = math.hypot(dx / 3.4, dy / (2.7 + wob * 0.3))
                else:                                          # teardrop tail narrowing back
                    half = 2.7 * max(0.0, 1 + dx / 8.5) ** 1.3
                    yy = dy - math.sin(dx * 0.8 + i * 1.57) * 0.9 * (-dx / 8.5)
                    r = abs(yy) / max(half, 0.01) if half > 0.35 else 9
                if r >= 1.0:
                    continue
                edge = r > 0.72
                if dx > 1.2 and r < 0.55:
                    c = "J4"
                elif dx > 0.2 and r < 0.8:
                    c = "J3"
                elif edge:
                    c = "J2" if dy < 0.5 else "J1"
                elif dx > -2.5:
                    c = "N3"
                else:
                    c = "N2"
                core.put([(x, y)], c)
        # wet glint on the ink body
        core.put([(int(cx - 2), int(cy - 1))], "N5")
        # dark outline for readability on bright backgrounds
        for (x, y) in list(core.px):
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if K.inb(*q) and q not in core.px:
                    trail.put([q], "OUT")
        # shed droplets
        for k in range(3):
            t = (i * 0.25 + k * 0.33) % 1.0
            q = (int(cx - 7 - t * 5), int(cy + (1 if k % 2 else -1) * (1.2 + t * 2.0)))
            if K.inb(*q):
                trail.put([q], "J2" if t < 0.3 else "J1" if t < 0.65 else "J0")
        frames.append((70, {"Trail": trail.image(), "Core": core.image()}))
    K.export("proj_inkbolt", ["Trail", "Core"], [("fly", frames)], None, build=BUILD)
    return {"proj_inkbolt": [16, 12]}


# =========================================================================== main
ENEMIES = {
    "grimoire": lambda: build_grimoire(),
    "ink_hound": lambda: build_hound(),
    "lantern_monk": lambda: build_monk(),
    "head_librarian": lambda: build_librarian(),
    "projectiles": lambda: build_projectiles3(),
}


def verify(name):
    """Check the exported Aseprite json: tag names, frame counts, and the meta's frame indices."""
    with open(os.path.join(K.asebuild.ASSETS, f"{name}.json")) as fh:
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
        for key in ("spawn", "telegraph"):
            for t, s in meta.get(key, {}).items():
                assert 0 <= s["frame"] < spec[t], (name, key, t, s)
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
