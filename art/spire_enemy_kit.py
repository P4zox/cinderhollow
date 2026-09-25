"""Helpers for gen_spire_enemies.py (Tempest Spire enemies). Built on enemy_kit.py (read-only reuse);
the generic driver / hitbox preview mirror gen_enemies3.py so the output format is identical.

Adds the Spire palette ramps to enemy_kit's tables (process-local):
    S  storm-crow feathers, blue-black with a cold storm-blue sheen (top step = specular)
    U  lightning (fixed colours)  #1c4fa6 #2f7ae0 #5aa8ff #a4d6ff #eef9ff
    X  sackcloth grey-brown          H  dry straw, muted ochre        Z  dark cool coat cloth
    g  weathered grey wood           E  rain-soaked slate-blue robe   N  verdigris copper
    J  bright copper (shiny)       r  muted rust (scythe blade)
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, ip, line, polyline, hash01, norm3, bbox  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402

RAMPS = {
    "S": ["#07080e", "#0e1220", "#182039", "#243353", "#36507c", "#6a90bd"],
    "U": ["#1c4fa6", "#2f7ae0", "#5aa8ff", "#a4d6ff", "#eef9ff"],
    "X": ["#171412", "#28231f", "#3d3630", "#554b41", "#716454", "#8e806b"],
    "H": ["#241c10", "#3e3219", "#5e4c27", "#7e6936", "#9d874c"],
    "Z": ["#0b0b0e", "#16161b", "#222128", "#312f38", "#46434e"],
    "g": ["#121110", "#211f1c", "#34302b", "#4a453d", "#655e53", "#857c6e"],
    "E": ["#080a10", "#10151f", "#1a2230", "#263346", "#36485f", "#4f6682"],
    "N": ["#0f1f1c", "#1a3832", "#2a584b", "#407a67", "#62a088", "#8cc0a4"],
    "r": ["#1c0f0d", "#351a14", "#53281b", "#6f3a23", "#8c5234"],
    "J": ["#1f100b", "#3f2014", "#63361d", "#87512a", "#a87042", "#cc9a66"],
}
for _r, _cols in RAMPS.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"S": 0.93, "J": 0.9})
K.SMEAR.update({
    "cold": ["U4", "U3", "S5", "S4"],
    "storm": ["U4", "U3", "U2", "U1"],
    "feather": ["S5", "S4", "S3", "S2"],
})


# =========================================================================== geometry
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
    """Smooth variable-radius tube along a polyline."""
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


def curve(pts, n=16):
    """Catmull-Rom through pts."""
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
    for q in K.mask_disc(c, r, r * squash):
        d = math.hypot(q[0] + .5 - c[0], (q[1] + .5 - c[1]) / squash) / max(r, 0.5)
        FX.put([q], pal[min(n - 1, int(d * n))])


def jag_pts(a, b, n, amp, seed):
    """Jagged lightning polyline a -> b (n segments, perpendicular jitter amp)."""
    pts = [a]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(1, n):
        t = i / n
        o = (hash01(i, seed, 71) * 2 - 1) * amp
        pts.append((a[0] + dx * t + nx * o, a[1] + dy * t + ny * o))
    pts.append(b)
    return pts


def arc_fx(FX, a, b, n, amp, seed, core="U4", edge="U2"):
    """A small crackling arc on the FX layer: bright core line with a dimmer 1px fringe on alternate pixels."""
    pts = polyline(jag_pts(a, b, n, amp, seed))
    for i, q in enumerate(pts):
        FX.put([q], core)
    for i, q in enumerate(pts):
        if i % 2 == 0:
            for d in ((1, 0), (0, 1)):
                r = (q[0] + d[0], q[1] + d[1])
                if r not in FX.px:
                    FX.put([r], edge)
    return set(pts)


def star(FX, c, r, cols=("U4", "U3", "U2"), diag=True):
    x, y = ip(c)
    FX.put([(x, y)], cols[0])
    for k in range(1, r + 1):
        col = cols[0] if k == 1 else cols[1] if k < r else cols[2]
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            FX.put([(x + d[0] * k, y + d[1] * k)], col)
    if diag:
        for d in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            FX.put([(x + d[0], y + d[1])], cols[1])
            if r >= 3:
                FX.put([(x + d[0] * 2, y + d[1] * 2)], cols[2])


def rim_light(layer, lc, radius, cols=("U2", "U1")):
    """Cold under-light: silhouette pixels facing the light source within radius get a blue rim."""
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
            add_[(x, y)] = cols[0] if d < radius * 0.5 else cols[1]
    for p, c in add_.items():
        layer.px[p][3] = c


# =========================================================================== driver
def render_anims(spec, layers, draw, anims, sway_key, loops=("idle", "walk", "fly", "perch", "hidden")):
    out, infos = [], {}
    assert list(spec) == [t for t, _ in anims], list(spec)
    for tag, fn in anims:
        fr = fn()
        assert spec[tag] == len(fr), (tag, len(fr))
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


def hurtbox(anims, names, inset=(1, 0, 1, 0), floor=True, frame=0, tag=0):
    imgs = anims[tag][1][frame][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs, names)
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2],
            (K.H if floor else y1 - inset[3]) - (y0 + inset[1])]


def mk(neutral):
    def P_(**kw):
        d = dict(neutral)
        d.update(kw)
        return d
    return P_


def spawn_pt(p):
    return [int(round(p[0])), int(round(p[1]))]


def collapse(names, sq, burn=0.0, seed=0, spread=0.25, pal=("H4", "H3", "X3", "X2", "X1"), cx=None, rise=10):
    """Squash the named layers onto the floor line (spreading sideways); optionally burn some into motes."""
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
            out = K.ember_dissolve(out, burn, names, seed=seed, rise=rise, pal=pal)
        return out
    return f


# =========================================================================== previews / export
def hitbox_preview3(name, tags, flats, meta, scale=4):
    """Hurtbox green, hit rects red on active frames (+ blue 10x26 player box), anchor yellow,
    spawn point magenta on its frame, telegraph glint cyan on its frame (same as gen_enemies3)."""
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


def export(name, layers, anims, meta, build, flat_order=None):
    tags, flats = K.export(name, layers, anims, meta, build=build, flat_order=flat_order)
    if meta is not None:
        hitbox_preview3(name, tags, flats, meta)
    return tags, flats


def verify(name, spec, meta_expected=True):
    """Check the exported Aseprite json: tag names, frame counts, and the meta's frame indices."""
    with open(os.path.join(K.asebuild.ASSETS, f"{name}.json")) as fh:
        js = json.load(fh)
    tags = {t["name"]: (t["from"], t["to"]) for t in js["meta"]["frameTags"]}
    assert list(tags) == list(spec), (name, list(tags))
    for t, n in spec.items():
        assert tags[t][1] - tags[t][0] + 1 == n, (name, t, tags[t])
    if meta_expected:
        with open(os.path.join(K.asebuild.ASSETS, f"{name}_meta.json")) as fh:
            meta = json.load(fh)
        for t, a in meta.get("attacks", {}).items():
            for w in a.get("windows", [a]):
                assert 0 <= w["active"][0] <= w["active"][1] < spec[t], (name, t, w)
        for key in ("spawn", "telegraph"):
            for t, s in meta.get(key, {}).items():
                assert 0 <= s["frame"] < spec[t], (name, key, t, s)
    return {t: [a, b] for t, (a, b) in tags.items()}
