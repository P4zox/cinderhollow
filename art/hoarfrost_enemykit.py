"""Helpers for art/gen_hoarfrost_enemies.py (Hoarfrost Aqueduct creatures).

Registers the cold region ramps into enemy_kit (in this process only) and carries copies of the
gen_enemies3 driver helpers (render_anims, hit_rect, hurtbox, n_tube, curve, hitbox preview) so the
Archives generator is never imported (it mutates enemy_kit ramps).
"""
import json, math, os, sys

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
from enemy_kit import Layer, FXLayer, ip, bbox, mask_disc, norm3, poly_mask, hash01  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

# =========================================================================== palette (Hoarfrost)
HF_RAMPS = {
    # dressed blue-black aqueduct stone
    "S": ["#06080d", "#0c1119", "#151c28", "#212c3c", "#324257", "#4c6078"],
    # glassy binding ice (top step = specular glint)
    "U": ["#0a1828", "#142e4a", "#214b70", "#35709c", "#5f9fca", "#b4e0f4"],
    # frost-grey veil cloth
    "X": ["#0a0c12", "#141821", "#20252f", "#313743", "#4a515d", "#6f7884"],
    # frost bone (masks, skeletal arms)
    "H": ["#15181e", "#2b3139", "#48505b", "#6b7581", "#96a1ac", "#c6d0d8"],
    # lurker hide: pale translucent blue-white
    "E": ["#0e1620", "#1c2a38", "#314556", "#4d6679", "#7590a1", "#a9c2cc"],
    # frost-light (fixed colours)
    "J": ["#0d2138", "#1a4a78", "#2f7fbf", "#6fbaf2", "#c4ecff", "#ffffff"],
}
for _r, _cols in HF_RAMPS.items():
    _keys = []
    for _i, _c in enumerate(_cols):
        _k = f"{_r}{_i}"
        K.HEX[_k] = _c
        K.RGBA[_k] = tuple(int(_c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        _keys.append(_k)
    K.RAMP[_r] = _keys
K.SHINY.update({"U": 0.86})
K.SMEAR.update({
    "frost": ["J5", "J4", "J3", "J2"],
    "rime": ["J4", "U4", "U3", "U2"],
})
FROST_PAL = ("J5", "J4", "J3", "J2", "J1")


# =========================================================================== small math
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


def resample(pts, radii):
    """Interpolate radii along a Catmull-Rom curve of pts: returns (curve_pts, curve_radii)."""
    cp = curve(pts, 5)
    n = len(cp)
    rr = []
    for i in range(n):
        t = i / (n - 1) * (len(radii) - 1)
        a = int(min(len(radii) - 2, t))
        u = t - a
        rr.append(radii[a] + (radii[a + 1] - radii[a]) * u)
    return cp, rr


def ribbon(pts, w_up, w_dn, n=6, jag=0.0, jag_from=0.5, fi=0, seed=0, jag_up=0.0):
    """Cloth / body strip along a smooth curve. w_up / w_dn: half widths (lists over pts) on the left / right
    of the travel direction. Ragged (tattered) edges from t >= jag_from. Returns (polygon, samples[(x,y,t)])."""
    cp = curve(pts, n)
    m = len(cp)

    def wi(ws, t):
        s = t * (len(ws) - 1)
        a = int(min(len(ws) - 2, s))
        u = s - a
        return ws[a] + (ws[a + 1] - ws[a]) * u
    up, dn, samp = [], [], []
    for i, p in enumerate(cp):
        t = i / (m - 1)
        a = cp[max(0, i - 1)]
        b = cp[min(m - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        tx, ty = tx / l, ty / l
        nx, ny = ty, -tx                          # left of travel
        wu, wd = wi(w_up, t), wi(w_dn, t)
        if t >= jag_from:
            k = (t - jag_from) / max(1e-6, 1 - jag_from)
            if jag:
                wd += jag * k * ((1.0 if (i // 2 + fi) % 3 == 0 else -0.6) * (0.6 + 0.8 * hash01(i // 2, fi // 2, seed)))
            if jag_up:
                wu += jag_up * k * ((1.0 if (i // 2 + fi + 1) % 3 == 0 else -0.5) * (0.6 + 0.8 * hash01(i // 2, 7, seed)))
        up.append((p[0] + nx * max(0.0, wu), p[1] + ny * max(0.0, wu)))
        dn.append((p[0] - nx * max(0.0, wd), p[1] - ny * max(0.0, wd)))
        samp.append((p[0], p[1], t))
    return up + dn[::-1], samp


def nearest_t(samp, q):
    best, bt = 1e9, 0.0
    for sx, sy, t in samp:
        d = (q[0] + .5 - sx) ** 2 + (q[1] + .5 - sy) ** 2
        if d < best:
            best, bt = d, t
    return bt


def disc_glow(FX, c, r, pal, squash=1.0):
    n = len(pal)
    for q in mask_disc(c, r, r * squash):
        d = math.hypot(q[0] + .5 - c[0], (q[1] + .5 - c[1]) / squash) / max(r, 0.5)
        FX.put([q], pal[min(n - 1, int(d * n))])


def star(FX, c, arm, core="J5", mid="J4", tip="J3", diag=True):
    """Cold glint: cross flare with short diagonals."""
    x, y = ip(c)
    FX.put([(x, y)], core)
    for d in range(1, arm + 1):
        col = mid if d < arm else tip
        for q in ((x + d, y), (x - d, y), (x, y + d), (x, y - d)):
            FX.put([q], col)
    if diag:
        for q in ((x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
            FX.put([q], tip)


def rim(L_, mats, level, side=(0, -1), raise_only=True):
    """Cold rim light along the edges facing `side` so dark bodies separate from dark backgrounds.
    raise_only: never darken an already brighter pixel."""
    pts = []
    for q, e in L_.px.items():
        if e[0] in mats and not isinstance(e[3], str) and (q[0] + side[0], q[1] + side[1]) not in L_.px:
            pts.append((q, e))
    for q, e in pts:
        if raise_only and not isinstance(e[3], tuple):
            if K.level_of(e, *q) >= level:
                continue
        e[3] = ("LVL", level)


# =========================================================================== driver
def render_anims(spec, layers, draw, anims, sway_key="C", loops=("idle", "walk", "fly")):
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


def hurtbox(anims, names, inset=(1, 0, 1), floor=True, frame=0, tag=0):
    imgs = anims[tag][1][frame][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs, names)
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2],
            (K.H if floor else y1 - inset[1]) - (y0 + inset[1])]


def outline_img(img, col="OUT"):
    """Return an image holding a 1px outline around img's opaque pixels (for re-outlining shattered pieces)."""
    W, H = img.size
    src = img.load()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o = out.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + a < W and 0 <= y + b < H and src[x + a, y + b][3]:
                    o[x, y] = K.RGBA[col]
                    break
    return out


def frost_dissolve(imgs, frac, names, fx_name="FX", seed=0, rise=10, drift=4, pal=FROST_PAL, bottom_up=False):
    """Dissolve layers into drifting snow / ice motes. Edges glow cold; lost pixels drift up-back as motes."""
    W, H = K.W, K.H
    motes = {}
    out = dict(imgs)
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
                t = 0.6 * hash01(x, y, 91 + seed) + 0.4 * ((1 - y / H) if bottom_up else (y / H))
                if t >= frac:
                    if t < frac + 0.06:
                        dst[x, y] = K.RGBA[pal[2] if hash01(x, y, 92) > 0.5 else pal[3]]
                    else:
                        dst[x, y] = src[x, y]
                elif hash01(x, y, 93 + seed) < 0.08:
                    age = frac - t
                    mx = int(x - age * drift * 3 + math.sin(y * 0.5 + age * 8) * 1.5)
                    my = int(y - age * rise - hash01(x, y, 94) * 2)
                    if 0 <= mx < W and 0 <= my < H and age < 0.5:
                        motes[(mx, my)] = pal[0] if age < 0.08 else pal[1] if age < 0.18 else pal[2] if age < 0.3 \
                            else pal[3]
        out[n] = new
    fx = imgs[fx_name].copy() if fx_name in imgs else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fp = fx.load()
    for (x, y), c in motes.items():
        fp[x, y] = K.RGBA[c]
    out[fx_name] = fx
    return out


def shatter(imgs, names, t, seeds=18, seed=0, floor=None, spread=0.7, target="Body", fx="FX", cx=None, glow=0.0):
    """Split the named layers into Voronoi chunks that tumble outward and fall into a pile on the floor.
    t 0..1. Result is merged into `target` (re-outlined); other named layers are cleared."""
    W, H = K.W, K.H
    floor = H - 1 if floor is None else floor
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n in names:
        if n in imgs:
            comp.alpha_composite(imgs[n])
    box = comp.getbbox()
    out = dict(imgs)
    for n in names:
        out[n] = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not box:
        return out
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2 if cx is None else cx
    sp = [(x0 + (x1 - x0) * hash01(k, 1, seed), y0 + (y1 - y0) * hash01(k, 2, seed)) for k in range(seeds)]
    src = comp.load()
    cells = {k: [] for k in range(seeds)}
    for y in range(y0, y1):
        for x in range(x0, x1):
            if src[x, y][3] == 0:
                continue
            k = min(range(seeds), key=lambda j: (x - sp[j][0]) ** 2 * 0.8 + (y - sp[j][1]) ** 2)
            cells[k].append((x, y))
    res = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k in sorted(cells, key=lambda k: -max((p[1] for p in cells[k]), default=0)):
        pts = cells[k]
        if not pts:
            continue
        xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
        bx0, by0, bx1, by1 = min(xs_), min(ys_), max(xs_) + 1, max(ys_) + 1
        piece = Image.new("RGBA", (bx1 - bx0, by1 - by0), (0, 0, 0, 0))
        pp = piece.load()
        for (x, y) in pts:
            pp[x - bx0, y - by0] = src[x, y]
        ccx = (bx0 + bx1) / 2
        # tall chunks topple over as they fall
        if t > 0.45 and (by1 - by0) > (bx1 - bx0) * 1.3:
            piece = piece.transpose(Image.ROTATE_90 if hash01(k, 5, seed) > 0.5 else Image.ROTATE_270)
        pw, ph = piece.size
        tipx = (ccx - cx) * spread * (0.6 + 0.8 * hash01(k, 3, seed)) + (hash01(k, 4, seed) - 0.5) * 4
        nx = ccx + tipx * min(1.0, t * 1.3) - pw / 2
        top0 = by1 - ph
        land = floor + 1 - ph - int(hash01(k, 6, seed) * 2) * (1 if t >= 0.99 else 0)
        ny = top0 + (land - top0) * min(1.0, t * t * 1.25)
        res.alpha_composite(piece, (int(round(nx)), int(round(min(ny, land)))))
    ol = outline_img(res)
    ol.alpha_composite(res)
    out[target] = ol
    return out


# =========================================================================== previews
def hitbox_preview(name, tags, flats, meta, scale=4):
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
    ext = 30   # room to the right for rects that reach past the frame (breath cone)
    sheet = Image.new("RGBA", ((cols * (W + ext + pad)) * scale, len(rows) * (H + pad + lab) * scale), K.BG)
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
            fr = Image.new("RGBA", (W + ext, H), K.BG)
            cell = Image.new("RGBA", (W, H), K.BG_CELL)
            cell.alpha_composite(flats[i])
            fr.alpha_composite(cell)
            big = fr.resize(((W + ext) * scale, H * scale), Image.NEAREST)
            d = ImageDraw.Draw(big)

            def rect(rc, col, wdt=1):
                x, y, w, h = rc
                d.rectangle([x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1], outline=col, width=wdt)
            rect(meta["hurtbox"], (60, 230, 90, 255))
            for w in wins:
                if w["active"][0] <= k <= w["active"][1]:
                    rect(w["hit"], (255, 50, 50, 255), 2)
                    hx, hy, hw, hh = w["hit"]
                    px = max(0, hx + hw - 6)
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
            sheet.alpha_composite(big, (k * (W + ext + pad) * scale, y0 + lab * scale))
    sheet.save(os.path.join(ART, "previews", f"{name}_hitbox.png"))


def verify(name, spec):
    """Check the exported Aseprite json: tag names, frame counts, and the meta's frame indices."""
    with open(os.path.join(K.asebuild.ASSETS, f"{name}.json")) as fh:
        js = json.load(fh)
    tags = {t["name"]: (t["from"], t["to"]) for t in js["meta"]["frameTags"]}
    assert list(tags) == list(spec), (name, list(tags))
    for t, n in spec.items():
        assert tags[t][1] - tags[t][0] + 1 == n, (name, t, tags[t])
    mp = os.path.join(K.asebuild.ASSETS, f"{name}_meta.json")
    if os.path.exists(mp):
        with open(mp) as fh:
            meta = json.load(fh)
        for t, a in meta.get("attacks", {}).items():
            for w in a.get("windows", [a]):
                assert 0 <= w["active"][0] <= w["active"][1] < spec[t], (name, t, w)
        for key in ("spawn", "telegraph"):
            for t, s in meta.get(key, {}).items():
                assert 0 <= s["frame"] < spec[t], (name, key, t, s)
    durs = [f["duration"] for f in js["frames"]]
    return {t: [a, b, durs[a:b + 1]] for t, (a, b) in tags.items()}
