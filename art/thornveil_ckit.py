"""Thornveil Wood creature kit (agent T): palette ramps + shared body parts on top of enemy_kit.py.

Ramps (runtime additions to enemy_kit's material table; letters unused by the base kit):
  E  elder wood / desiccated wood-flesh (dark, cool grey-brown)
  H  moss (deep, cool blue-green)
  J  bone & antler (pale, warm)
  N  pale ribbon cloth
  S  spirit-light (fixed glow colours)
  U  bramble / thorn vine (dark red-brown)
  X  bark-cloth robe (near-black olive)
  Z  pale witch skin / ash
"""
import json, math, os, sys
ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import (Layer, FXLayer, add, sub, lerp, ip, line, polyline, ik, hash01, mask_disc, poly_mask,  # noqa: E402
                       n_plate, n_dome, n_capsule, norm3, dirv, bbox)
from PIL import Image, ImageDraw  # noqa: E402

NEW = {
    "E": ["#0b0a09", "#15120f", "#211c17", "#2f2820", "#40362b", "#564937"],
    "H": ["#0a1611", "#10231a", "#183423", "#22472d", "#30603a", "#4a7f4a"],
    "J": ["#26221c", "#453e32", "#716754", "#9e927a", "#c9bea2", "#ebe4cd"],
    "N": ["#3c3a35", "#5a574f", "#858073", "#aea896", "#d2ccb9", "#eee9da"],
    "S": ["#0f3a28", "#1b6444", "#2f9a5e", "#5fe08e", "#b4ffd0", "#f0fff6"],
    "U": ["#0e0807", "#1d110e", "#2f1c16", "#452a20", "#61392a", "#8a5a42"],
    "X": ["#09090a", "#111210", "#1a1c17", "#262a20", "#343a2b", "#465038"],
    "Z": ["#1c1c1f", "#34343a", "#55555c", "#7c7c82", "#a6a5a6", "#cfcdc6"],
}
for _r, _cols in NEW.items():
    K.RAMP[_r] = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[j:j + 2], 16) for j in (1, 3, 5)) + (255,)
        K.RAMP[_r].append(_k)
K.SMEAR["spirit"] = ["S5", "S4", "S3", "S2"]
K.SMEAR["wood"] = ["J4", "J3", "E5", "E4"]
BUILD = "--preview" not in sys.argv


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def madd(p, *vs):
    x, y = p
    for v, k in vs:
        x += v[0] * k
        y += v[1] * k
    return (x, y)


def curve(pts, n=8):
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


def chain(L, pts, radii, mat, bias=0, ao=1, flat=1.0):
    """A smooth tube as a chain of capsules (fast; pts/radii same length)."""
    out = set()
    for i in range(len(pts) - 1):
        out |= L.paint(n_capsule(pts[i], pts[i + 1], radii[i], radii[i + 1], flat), mat, bias, ao if i == 0 else 0)
    return out


def taper(n, r0, r1, pw=1.0):
    return [r0 + (r1 - r0) * (i / max(1, n - 1)) ** pw for i in range(n)]


def grain(L, pts, mat_lvl=1, seed=0, dens=0.35):
    """Dark bark grain: short streaks along a limb (decals on its own pixels)."""
    own = [q for q in pts if q in L.px]
    for q in own:
        if hash01(q[0] // 2, q[1], seed) < dens * 0.25:
            L.decal([q, (q[0], q[1] + 1)], (L.px[q][0], mat_lvl))


def rim(L, mats, lvl=4, side=(0, -1)):
    """Cold top rim so dark bodies separate from dark backgrounds."""
    for q, e in list(L.px.items()):
        if (q[0] + side[0], q[1] + side[1]) not in L.px and e[0] in mats and not isinstance(e[3], str):
            e[3] = ("LVL", lvl)


# ---------------------------------------------------------------- deer skull (profile, snout toward +x of `ang`)
def deer_skull(L, c, ang, s=1.0, eye=1, mat="J", bias=0, jaw=0.0):
    """c = cranium centre; ang = facing (0 = right, +down). Returns dict of key points (eye, snout, crown, antler bases)."""
    G = lambda x, y: add(c, rot((x * s, y * s), ang))
    cran = L.paint(n_dome(c, 3.0 * s, 2.6 * s, tilt=(-0.1, -0.25)), mat, bias)
    snout = [G(1.2, -1.6), G(4.5, -1.0), G(8.4, 0.2), G(9.2, 1.2), G(8.6, 2.0), G(4.0, 2.2), G(1.0, 2.4), G(-0.6, 1.6)]
    sm = poly_mask(snout)
    L.paint(n_plate(sm, 1.0, (0.05, -0.35), 1.0), mat, bias, ao=0)
    if jaw > 0:
        J = [G(0.2, 2.0), G(7.4, 2.4 + jaw * 2.4), G(7.2, 3.2 + jaw * 2.4), G(0.6, 3.2)]
        L.paint(n_plate(poly_mask(J), 0.8, (0, 0.3)), mat, bias - 1, ao=0)
    # nasal groove + cheek shadow
    L.decal([q for q in line(G(2.0, 1.0), G(7.6, 0.9)) if q in L.px], (mat, 1))
    e = ip(G(0.8, -0.3))
    eyep = {}
    if eye > 0:
        eyep = {e: "S4" if eye >= 2 else "S3", (e[0] + 1, e[1]): "S2", (e[0], e[1] - 1): "E0"}
        if eye >= 2:
            eyep[(e[0] - 1, e[1])] = "S2"
    else:
        eyep = {e: "E0", (e[0] + 1, e[1]): "E1"}
    L.fixed(eyep)
    return {"eye": e, "snout": G(9.0, 1.0), "crown": G(-0.6, -2.6), "ab": G(-0.2, -2.4), "ab2": G(-1.6, -2.0),
            "nape": G(-2.6, 1.0), "jaw": G(3.0, 3.0)}


def antler(L, base, ang, s=1.0, mat="J", bias=0, tines=3, spread=1.0, w=1.0):
    """Branching antler: main beam rising from `base` at angle `ang` (deg, -90 = straight up), curving back.
    Returns (tips, beam pts)."""
    d = dirv(ang)
    pv = (-d[1], d[0])
    beam = [base]
    L_ = 13.0 * s
    for i in range(1, 6):
        t = i / 5
        b = madd(base, (d, L_ * t), (pv, -2.8 * s * spread * math.sin(t * math.pi * 0.9) - 1.0 * s * t * t))
        beam.append(b)
    cp = curve(beam, 3)
    chain(L, cp, taper(len(cp), 1.25 * w * max(0.8, s), 0.55, 0.8), mat, bias, ao=0)
    tips = [cp[-1]]
    for k in range(tines):
        t = 0.28 + k * (0.62 / max(1, tines))
        q = cp[int(t * (len(cp) - 1))]
        ta = ang - (26 + 10 * k) * spread
        tl = (5.2 - k * 0.8) * s
        tp = madd(q, (dirv(ta), tl))
        mid = madd(lerp(q, tp, 0.5), (dirv(ta - 90), 0.6))
        chain(L, [q, mid, tp], [max(0.8 * w * s * 0.6, 0.8 * w), 0.62, 0.5], mat, bias, ao=0)
        tips.append(tp)
    # brow tine forward
    q = cp[int(0.12 * (len(cp) - 1))]
    tp = madd(q, (dirv(ang + 55), 3.6 * s))
    chain(L, [q, tp], [0.7 * w, 0.5], mat, bias, ao=0)
    tips.append(tp)
    L.fixed({ip(t): mat + "5" for t in tips if ip(t) in L.px})
    return tips, cp


def ribbon_px(pts, fi, seed, L=10, sway=0.0, pal=("N5", "N4", "N3", "N2")):
    """A pale ribbon hanging from pts[0] (frame coords), fluttering. Returns {pixel: colour}."""
    out = {}
    x, y = pts
    for i in range(L):
        t = i / max(1, L - 1)
        xx = x + math.sin(i * 0.45 + fi * 1.1 + seed) * (0.4 + 1.4 * t) + sway * t * 3
        c = pal[0] if i < 2 else pal[1] if t < 0.5 else pal[2] if t < 0.85 else pal[3]
        out[ip((xx, y + i))] = c
        if i % 3 == 1 and t < 0.8:
            out[ip((xx + 1, y + i))] = pal[2]
    return out


def moss_drape(L, pts, fi, seed, n=4, maxlen=6, mat="H"):
    """Beards of moss hanging from a list of anchor points."""
    out = {}
    for k, p in enumerate(pts[:n]):
        ln = 2 + int(hash01(k, seed, 3) * maxlen)
        for i in range(ln):
            q = ip((p[0] + math.sin(i * 0.6 + fi * 0.8 + k) * 0.6, p[1] + i + 1))
            out[q] = f"{mat}{3 if i < ln * 0.4 else 2 if i < ln * 0.8 else 1}"
    L.fixed({q: c for q, c in out.items()})


def glow_dots(FX, c, r, n, fi, cols=("S3", "S2"), seed=0):
    for k in range(n):
        a = k * 2 * math.pi / n + fi * 0.5 + seed
        rr = r * (0.6 + 0.4 * hash01(k, fi, seed))
        q = ip((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
        if (k + fi) % 2 == 0:
            FX.put([q], cols[k % len(cols)])


# ---------------------------------------------------------------- driver
def render_anims(layers, draw, anims, sway_key=None, loops=("idle", "walk", "fly", "run")):
    out, infos = [], {}
    for tag, fn in anims:
        fr = fn()
        if sway_key:
            drv = [p[sway_key][0] for _, p in fr]
            sway = K.spring(drv, loop=tag in loops, extra=[p.get("wind", 0.0) for _, p in fr])
        else:
            sway = [0.0] * len(fr)
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
            lst.append((ms, imgs))
            inf.append(info)
        out.append((tag, lst))
        infos[tag] = inf
    return out, infos


def hit_rect(infos, tag, ks, floor=True, x_min=None, pad=0, key="hit"):
    pts = set()
    for k in ks:
        pts |= infos[tag][k].get(key, set())
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
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2], (K.H if floor else y1) - (y0 + inset[1])]


def collapse(names, sq, burn=0.0, seed=0, spread=0.25, pal=("S4", "S3", "S2", "H3", "H2"), cx=None):
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
            out = K.ember_dissolve(out, burn, names, seed=seed, rise=12, pal=pal)
        return out
    return f


def export(name, layers, anims, meta, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=BUILD, flat_order=flat_order)
    return tags, flats


def spawn_pt(p):
    return [int(round(p[0])), int(round(p[1]))]


def contact(name, tags, flats, rows=None, scale=3, per_row=16):
    """A compact contact sheet (every frame, small) for quick proportion review."""
    W, H = K.W, K.H
    sel = [(t, a, b) for t, a, b in tags if rows is None or t in rows]
    n = sum(min(per_row, b - a + 1) for _, a, b in sel)
    cols = per_row
    rws = len(sel)
    sheet = Image.new("RGBA", (cols * (W + 2) * scale, rws * (H + 12) * scale), K.BG)
    d = ImageDraw.Draw(sheet)
    for r, (t, a, b) in enumerate(sel):
        d.text((2, r * (H + 12) * scale + 1), t, fill=(240, 240, 240, 255))
        for i in range(a, min(b + 1, a + cols)):
            fr = Image.new("RGBA", (W, H), K.BG_CELL)
            fr.alpha_composite(flats[i])
            sheet.alpha_composite(fr.resize((W * scale, H * scale), Image.NEAREST), ((i - a) * (W + 2) * scale, (r * (H + 12) + 10) * scale))
    sheet.save(os.path.join(ART, "previews", f"{name}_contact.png"))


def smooth_tube(L, pts, radii, mat, bias=0, ao=1, flat=1.0):
    """One continuous normal field along a polyline (no seams between segments, unlike `chain`)."""
    import enemy_kit as _K
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    R = max(radii) + 1
    out = {}
    segs = list(zip(pts, pts[1:], radii, radii[1:]))
    for y in range(int(min(ys) - R) - 1, int(max(ys) + R) + 2):
        for x in range(int(min(xs) - R) - 1, int(max(xs) + R) + 2):
            px, py = x + .5, y + .5
            best = None
            for (a, b, ra, rb) in segs:
                dx, dy = b[0] - a[0], b[1] - a[1]
                L2 = dx * dx + dy * dy or 1e-6
                t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
                qx, qy = a[0] + dx * t, a[1] + dy * t
                r = ra + (rb - ra) * t
                ox, oy = px - qx, py - qy
                q = (ox * ox + oy * oy) / (r * r)
                if q <= 1 and (best is None or q < best[0]):
                    best = (q, ox / r, oy / r)
            if best:
                nx, ny = best[1] * flat, best[2] * flat
                out[(x, y)] = _K.norm3(nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny)))
    return L.paint(out, mat, bias, ao)
