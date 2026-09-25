"""Tempest Spire FX (see gen_spire_enemies.py):
    fx_sp_spark   32x32, 5 frames, tag sp_spark, centred: electric impact burst
    fx_sp_strike  48x216, 8 frames, tag sp_strike, pivot bottom-centre: lightning strike from the sky
House FX style (gen_fx*.py): crisp colour bands, ordered falloff instead of blur, only a couple of alpha steps
for the halo, two layers (Glow under Core). Lightning ramp #1c4fa6 #2f7ae0 #5aa8ff #a4d6ff #eef9ff.
"""
import math, os
from PIL import Image, ImageDraw
import enemy_kit as K
from enemy_kit import hash01, line, polyline
import spire_enemy_kit as S

L0, L1, L2, L3, L4 = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in S.RAMPS["U"]]
SMOKE = [(40, 46, 60), (58, 66, 84), (80, 90, 110)]
B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bt(x, y):
    return (B4[y & 3][x & 3] + 0.5) / 16.0


def A(c, a=255):
    return (c[0], c[1], c[2], a)


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(img, x, y, c, over=True):
    x, y = int(round(x)), int(round(y))
    w, h = img.size
    if 0 <= x < w and 0 <= y < h:
        if over or img.getpixel((x, y))[3] == 0:
            img.putpixel((x, y), c)


def put_line(img, pts, c, over=True):
    for q in polyline([(p[0] + 0.5, p[1] + 0.5) for p in pts]) if len(pts) > 1 else [pts[0]]:
        put(img, q[0], q[1], c, over)


def halo(img, pts, r, c, keep=1.0, seed=0):
    """Dilate a set of pixels by radius r into `img` (only onto empty pixels), ordered-dither thinning by keep."""
    w, h = img.size
    seen = set()
    for (x, y) in pts:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy > r * r + 0.5:
                    continue
                q = (x + dx, y + dy)
                if q in seen or not (0 <= q[0] < w and 0 <= q[1] < h):
                    continue
                seen.add(q)
                if keep < 1.0 and bt(q[0] + seed, q[1]) > keep:
                    continue
                if img.getpixel(q)[3] == 0:
                    img.putpixel(q, c)


def jag(a, b, n, amp, seed, bias=0.0):
    pts = [a]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(1, n):
        t = i / n
        o = ((hash01(i, seed, 71) * 2 - 1) + bias) * amp * (0.6 + 0.4 * math.sin(t * math.pi))
        pts.append((a[0] + dx * t + nx * o, a[1] + dy * t + ny * o))
    pts.append(b)
    return pts


def raster(pts):
    return list(dict.fromkeys(polyline([(p[0] + 0.5, p[1] + 0.5) for p in pts])))


def build_frames(name, W, H, layers, cels, ms, tag, build_ase):
    frames = [{"ms": m, "cels": c} for m, c in zip(ms, cels)]
    if build_ase:
        K.asebuild.build(name, W, H, layers, frames, [(tag, 0, len(frames) - 1)])
    return (name, frames, layers)


# =========================================================================== spark
def build_spark(build_ase):
    """Electric impact burst: white core pops, blue forked sparks crack outward, quick fade."""
    W = H = 32
    cx, cy = 15.5, 15.5
    cels = []
    for k in range(5):
        glow, core = blank(W, H), blank(W, H)
        if k == 0:
            for q in K.mask_disc((cx + .5, cy + .5), 3.2):
                d = math.hypot(q[0] + .5 - cx - .5, q[1] + .5 - cy - .5)
                put(core if d < 2.0 else glow, q[0], q[1], A(L4) if d < 1.4 else A(L3) if d < 2.2 else A(L2))
            for a in range(0, 360, 90):
                for r in range(3, 7):
                    put(core, cx + math.cos(math.radians(a + 20)) * r, cy + math.sin(math.radians(a + 20)) * r,
                        A(L3) if r < 5 else A(L2))
            halo(glow, [(int(cx), int(cy))], 5, A(L1, 150), keep=0.55)
        else:
            L = [0, 12.5, 14.0, 13.0, 11.0][k]
            st = [0, 0.0, 0.25, 0.55, 0.8][k]              # rays retreat from the centre as they fade
            core_pts = []
            for j in range(7):
                a = j * 2 * math.pi / 7 + 0.35 + hash01(j, 3, 9) * 0.5
                r0, r1 = L * st + 1.5, L * (0.8 + 0.3 * hash01(j, 4, 9))
                p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
                p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
                pts = raster(jag(p0, p1, 4, 1.6, j * 13 + 2))
                if k >= 3:
                    pts = [q for i, q in enumerate(pts) if (i + j + k) % 3 != 0]
                col = A(L4) if k == 1 else A(L3) if k == 2 else A(L2) if k == 3 else A(L1)
                for q in pts:
                    put(core, q[0], q[1], col)
                core_pts += pts
                # forks off the brighter rays
                if k <= 2 and j % 2 == 0 and len(pts) > 5:
                    b0 = pts[len(pts) // 2]
                    fa = a + (0.7 if j % 4 == 0 else -0.7)
                    fk = raster(jag(b0, (b0[0] + math.cos(fa) * 4.5, b0[1] + math.sin(fa) * 4.5), 2, 1.0, j))
                    for q in fk:
                        put(core, q[0], q[1], A(L3) if k == 1 else A(L2))
                # a spark mote flung past the ray tip
                if k >= 2:
                    tp = (cx + math.cos(a) * (r1 + 2 + k), cy + math.sin(a) * (r1 + 2 + k))
                    put(core, tp[0], tp[1], A(L3) if k < 4 else A(L1))
            if k <= 2:
                disc_r = [0, 2.6, 1.6][k]
                for q in K.mask_disc((cx + .5, cy + .5), disc_r):
                    put(core, q[0], q[1], A(L4))
                halo(glow, core_pts, 1, A(L1, 170) if k == 1 else A(L0, 150), keep=0.8 if k == 1 else 0.5, seed=k)
                halo(glow, [(int(cx), int(cy))], [0, 7, 6][k], A(L1, 120), keep=0.45, seed=k)
        cels.append({"Glow": glow, "Core": core})
    return build_frames("fx_sp_spark", W, H, ["Glow", "Core"], cels, [40, 50, 50, 60, 70], "sp_spark", build_ase)


# =========================================================================== strike
def build_strike(build_ase):
    """Lightning strike from the sky onto the ground, pivot bottom-centre (48x216).
    0-1 warning (faint flickering pre-strike leader + glowing ground ring), 2 full bolt + ground splash,
    3 bolt with side branches, 4 thinner bolt + ground sparks, 5-7 fading afterglow, sparks, smoke."""
    W, H = 48, 216
    cx, gy = 24, H - 1
    # irregular channel: uneven segment lengths, sharp kinks, drifting back towards the centre line
    main, x, y, i = [(cx + 3.0, 0.0)], cx + 3.0, 0.0, 0
    while y < gy - 12:
        i += 1
        y += 7 + 13 * hash01(i, 1, 23)
        sgn = 1 if (x < cx) != (hash01(i, 3, 23) < 0.25) else -1
        kick = sgn * (3.0 + 7.0 * hash01(i, 2, 23))
        x = max(cx - 12, min(cx + 12, x + kick + (cx - x) * 0.18))
        main.append((x, min(y, gy - 8)))
    main.append((cx, gy - 1))
    crooked = [main[0]]
    for j, (a, b) in enumerate(zip(main, main[1:])):          # crook every segment a little
        m = ((a[0] + b[0]) / 2 + (hash01(j, 5, 23) * 2 - 1) * 2.2, (a[1] + b[1]) / 2 + (hash01(j, 6, 23) - 0.5) * 3)
        crooked += [m, b]
    main = crooked
    main_px = raster(main)
    # side branches (used from frame 3)
    branches = []
    for i, (idx, side, ln) in enumerate(((5, -1, 28), (10, 1, 32), (16, -1, 24), (21, 1, 18))):
        idx = min(idx, len(main) - 3)
        x, y = main[idx]
        end = (max(2, min(W - 3, x + side * (13 + 4 * hash01(i, 1, 3)))), y + ln)
        br = raster(jag((x, y), end, 6, 2.2, 40 + i))
        sub = raster(jag(br[len(br) // 2], (br[len(br) // 2][0] + side * 5, br[len(br) // 2][1] + 9), 3, 1.2, 60 + i))
        branches.append((br, sub))
    cels = []
    for k in range(8):
        glow, core = blank(W, H), blank(W, H)
        if k <= 1:
            # faint, thin, flickering leader: a different dotted line each frame, dim blue
            lead = raster(jag((cx + 2, 0), (cx, gy - 2), 22, 4.0 + k, 11 + k * 7))
            for i, q in enumerate(lead):
                if (i // (2 + k)) % 2 == 0 and hash01(i, k, 3) < (0.55 + 0.25 * k):
                    put(glow, q[0], q[1], A(L1 if k == 0 else L2, 200 if k == 0 else 235))
            # glowing ground ring (ellipse), brighter and wider on frame 1
            rx, ry = 11 + 2 * k, 2.6 + 0.5 * k
            n = 90
            for i in range(n):
                a = 2 * math.pi * i / n
                x, y = cx + math.cos(a) * rx, gy - 2 + math.sin(a) * ry
                front = math.sin(a) > 0
                put(core if front else glow, x, y, A(L3) if front else A(L2, 220))
                if front and k == 1:
                    put(glow, x, y - 1, A(L1, 200))
            for q in K.mask_disc((cx + .5, gy - 1.5), rx - 2.5, ry - 0.8):
                if bt(*q) < 0.35 + 0.15 * k:
                    put(glow, q[0], q[1], A(L1, 150))
            # a couple of static crawls on the ground
            for j in range(3 + k):
                x = cx + (hash01(j, k, 5) * 2 - 1) * rx
                put(core, x, gy - (j % 2), A(L3))
        elif k <= 4:
            w_core = [0, 0, 2, 2, 1][k]
            ccol = A(L4) if k < 4 else A(L3)
            pts = set(main_px)
            if w_core == 2:
                pts |= {(x + 1, y) for x, y in main_px}
            for q in pts:
                put(core, q[0], q[1], ccol)
            if k == 3:
                for br, sb in branches:
                    for i, q in enumerate(br):
                        put(core, q[0], q[1], A(L4) if i < len(br) * 0.45 else A(L3))
                    for q in sb:
                        put(core, q[0], q[1], A(L2))
                    halo(glow, br, 1, A(L1, 200))
            # halo: blue fringe + a wider dithered outer glow
            halo(glow, list(pts), 1 if k == 4 else 2, A(L2, 230))
            halo(glow, list(pts), 3 if k == 4 else 4, A(L0, 150), keep=0.5 if k != 2 else 0.7, seed=k)
            # ground splash
            if k == 2:
                for q in K.mask_disc((cx + .5, gy + 0.5), 7.5, 5.0):
                    if q[1] <= gy:
                        d = math.hypot((q[0] + .5 - cx - .5) / 7.5, (q[1] + .5 - gy - .5) / 5.0)
                        put(core, q[0], q[1], A(L4) if d < 0.45 else A(L3) if d < 0.75 else A(L2))
                for j, (dx, h) in enumerate(((-16, 5), (-11, 9), (-6, 12), (6, 11), (11, 8), (16, 5))):
                    ray = raster([(cx + dx * 0.35, gy - 1), (cx + dx, gy - h)])
                    for i, q in enumerate(ray):
                        put(core, q[0], q[1], A(L4) if i < 3 else A(L3))
                halo(glow, [(cx + dx, gy) for dx in range(-14, 15)], 2, A(L1, 190))
            else:
                # sparks skittering out along the ground
                for j in range(8):
                    sgn = -1 if j % 2 else 1
                    x = cx + sgn * (5 + (k - 2) * 4 + hash01(j, k, 7) * 8)
                    y = gy - int(hash01(j, k, 8) * (4 if k == 3 else 6))
                    put(core, x, y, A(L4) if k == 3 else A(L3))
                    put(core, x - sgn, y + 1, A(L2))
                for q in K.mask_disc((cx + .5, gy + 0.5), 5.0 - k * 0.5, 2.4):
                    if q[1] <= gy:
                        put(core, q[0], q[1], A(L3) if k == 3 else A(L2))
        else:
            f = (k - 5) / 2.0                            # 0 .. 1 over frames 5-7
            # afterglow: the lower part of the channel flickers and breaks up
            n_keep = int(len(main_px) * (0.45 - 0.2 * f))
            seg = main_px[-n_keep:]
            for i, q in enumerate(seg):
                if (i // 3 + k) % 2 == 0 and bt(q[0], q[1] + k) < 0.9 - 0.3 * f:
                    put(glow, q[0], q[1], A(L1 if k < 7 else L0, 220 - 40 * (k - 5)))
            # scorch ember glow on the ground
            for q in K.mask_disc((cx + .5, gy + 0.5), 4.0 - f, 1.6):
                if q[1] <= gy and bt(*q) < 0.8 - 0.3 * f:
                    put(core, q[0], q[1], A(L2) if k == 5 else A(L1))
            # sparks arcing out and falling
            for j in range(6):
                sgn = -1 if j % 2 else 1
                t = (k - 4) / 3.0
                x = cx + sgn * (6 + 12 * t + hash01(j, 1, 9) * 5)
                y = gy - 2 - 9 * math.sin(math.pi * min(1.0, t + hash01(j, 2, 9) * 0.3)) * (0.6 + hash01(j, 3, 9))
                if hash01(j, k, 4) < 0.85 - 0.25 * f:
                    put(core, x, y, A(L3) if k == 5 else A(L2) if k == 6 else A(L1))
            # a little smoke rising off the strike point
            for j in range(4):
                sx = cx + (j - 1.5) * 3 + math.sin(k + j) * 1.2
                sy = gy - 3 - (k - 4) * 3 - j * 1.5
                r = 1.4 + 0.5 * (k - 5) + 0.3 * (j % 2)
                for q in K.mask_disc((sx, sy), r, r * 0.8):
                    if bt(q[0] + j, q[1]) < 0.75 - 0.2 * f:
                        put(glow, q[0], q[1], A(SMOKE[min(2, j % 2 + (1 if k == 5 else 0))], 210 - 40 * (k - 5)))
        cels.append({"Glow": glow, "Core": core})
    return build_frames("fx_sp_strike", W, H, ["Glow", "Core"], cels, [120, 120, 60, 60, 60, 80, 80, 80],
                        "sp_strike", build_ase)


# =========================================================================== preview
def preview(results):
    BG = (86, 86, 94, 255)
    CELL = (30, 32, 44, 255)
    rows = []
    for name, frames, layers in results:
        w, h = frames[0]["cels"][layers[0]].size
        S_ = 4 if h <= 64 else 2
        row = Image.new("RGBA", ((len(frames) * (w + 4) + 4) * S_, (h + 16) * S_), BG)
        d = ImageDraw.Draw(row)
        d.text((4, 4), f"{name}  ({len(frames)}f, ms {[f['ms'] for f in frames]})", fill=(240, 240, 245, 255))
        for i, f in enumerate(frames):
            cell = Image.new("RGBA", (w, h), CELL)
            for L in layers:
                cell.alpha_composite(f["cels"][L])
            row.alpha_composite(cell.resize((w * S_, h * S_), Image.NEAREST), ((4 + i * (w + 4)) * S_, 14 * S_))
        rows.append(row)
    Wt = max(r.width for r in rows)
    sheet = Image.new("RGBA", (Wt, sum(r.height for r in rows)), BG)
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    sheet.save(os.path.join(K.ART, "previews", "fx_spire.png"))
