"""Trees pass (docs/v17/trees.md): a small procedural tree painter used by art/gen_trees.py.

Wood is a skeleton of tapering, wobbling branches (Catmull-Rom spines) stamped as discs on a 4x supersampled grid. Each disc
writes its local frame (across-axis u, along-axis v, radius, axis direction), so the bark can be shaded as a real cylinder:
furrows that wrap round the limb (they crowd towards the edges), a spiral twist, plates broken by cross-cracks, moss on the
up-facing surfaces, a rim of light on the silhouette. Foliage is many small scalloped leaf clumps scattered inside larger
masses, shaded by the mass (a lit sphere) and by the clump, so a canopy reads as layered leaf masses with holes, never as
balloons. Everything is resolved to 1x and locked to hand-picked ramps with an ordered dither.
"""
import math
import numpy as np
from PIL import Image

S = 4
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float)


def C(h):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ----------------------------------------------------------------------------------------------- noise
def tex_noise(n=256, seed=0, cells=(32, 16, 8, 4), gain=0.5):
    """Tileable smooth value noise (n x n, 0..1)."""
    rng = np.random.default_rng(seed); out = np.zeros((n, n), np.float32); tot = 0.0; amp = 1.0
    for c in cells:
        k = max(1, n // c)
        g = rng.random((k, k)).astype(np.float32)
        gp = np.pad(g, 2, mode='wrap')
        im = Image.fromarray(gp, 'F').resize(((k + 4) * c, (k + 4) * c), Image.BICUBIC)
        a = np.asarray(im)[2 * c:2 * c + n, 2 * c:2 * c + n]
        out += a * amp; tot += amp; amp *= gain
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-9)


class Noise:
    def __init__(self, seed, n=256, cells=(32, 16, 8, 4)):
        self.t = tex_noise(n, seed, cells); self.n = n

    def __call__(self, x, y):
        n = self.n; x = np.asarray(x, float); y = np.asarray(y, float)
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); tx = x - x0; ty = y - y0
        x0 %= n; y0 %= n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n
        t = self.t
        a = t[y0, x0] + (t[y0, x1] - t[y0, x0]) * tx
        b = t[y1, x0] + (t[y1, x1] - t[y1, x0]) * tx
        return a + (b - a) * ty


def smooth(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------------- spines
def catmull(pts, per=24):
    P = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (np.array(P[j], float) for j in (i - 1, i, i + 1, i + 2))
        for k in range(per):
            t = k / per; t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(np.array(pts[-1], float))
    return np.array(out)


def resample(curve, step):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(curve, axis=0).T))]
    L = d[-1]; n = max(2, int(L / step) + 1); s = np.linspace(0, L, n)
    return np.stack([np.interp(s, d, curve[:, 0]), np.interp(s, d, curve[:, 1])], 1), s, L


# ----------------------------------------------------------------------------------------------- wood
class Wood:
    """4x grid of wood: cov, u (across, -1..1), v (along, 1x px), r (radius), dx/dy (axis), bid (branch id), mossk."""

    def __init__(self, w, h):
        self.w, self.h = w, h; W, H = w * S, h * S
        self.cov = np.zeros((H, W), bool); self.u = np.zeros((H, W)); self.v = np.zeros((H, W)); self.r = np.ones((H, W))
        self.ax = np.zeros((H, W)); self.ay = np.full((H, W), -1.0); self.bid = np.full((H, W), -1, int)
        self.mossk = np.zeros((H, W)); self.twist = np.zeros((H, W)); self.kind = np.zeros((H, W), int)
        self.along = np.full((H, W), 1e9)
        self.n = 0

    def branch(self, pts, r0, r1, wob=0.0, wobf=0.05, seed=0, rprof=None, mossk=1.0, twist=0.25, step=0.3, v0=0.0, kind=0,
               clip_y=None, under=0.0):
        """pts: 1x control points from the base to the tip. rprof(t, s) -> radius (overrides the r0->r1 taper).
        under: for the first `under` px of its length the branch only fills uncovered pixels (it grows out of its parent seamlessly)."""
        rng = np.random.default_rng(seed)
        c, s, L = resample(catmull(pts), step)
        tng = np.gradient(c, axis=0); tng /= np.maximum(1e-9, np.hypot(tng[:, 0], tng[:, 1]))[:, None]
        nrm = np.stack([-tng[:, 1], tng[:, 0]], 1)
        if wob:
            ph = rng.uniform(0, 6.3, 3)
            off = wob * (np.sin(s * wobf + ph[0]) * 0.6 + np.sin(s * wobf * 2.3 + ph[1]) * 0.3 + np.sin(s * wobf * 5.1 + ph[2]) * 0.1)
            off *= np.clip(s / 6, 0, 1)   # the base stays where it was put
            c = c + nrm * off[:, None]
        t = s / max(L, 1e-6)
        rr = rprof(t, s) if rprof else r0 + (r1 - r0) * t
        rr = np.maximum(rr, 0.45)
        bid = self.n; self.n += 1
        W, H = self.w * S, self.h * S
        for (cx, cy), (tx, ty), (nx, ny), r, sv in zip(c, tng, nrm, rr, s):
            R = r * S; X0 = int(max(0, math.floor((cx - r) * S))); X1 = int(min(W, math.ceil((cx + r) * S) + 1))
            Y0 = int(max(0, math.floor((cy - r) * S))); Y1 = int(min(H, math.ceil((cy + r) * S) + 1))
            if X0 >= X1 or Y0 >= Y1: continue
            yy, xx = np.mgrid[Y0:Y1, X0:X1]
            px = (xx + 0.5) / S - cx; py = (yy + 0.5) / S - cy
            dd = px * px + py * py; m = dd <= r * r
            if clip_y is not None: m &= (yy + 0.5) / S <= clip_y
            sl = (slice(Y0, Y1), slice(X0, X1))
            if sv < under: m &= ~self.cov[sl]
            al = np.abs(px * tx + py * ty)
            m &= (self.bid[sl] != bid) | (al < self.along[sl])     # a pixel belongs to the cross-section it lies on
            if not m.any(): continue
            self.along[sl] = np.where(m, al, self.along[sl])
            u = (px * nx + py * ny) / r
            self.cov[sl] |= m
            for arr, val in ((self.u, u), (self.v, v0 + sv + px * tx + py * ty)):
                arr[sl] = np.where(m, val, arr[sl])
            self.r[sl] = np.where(m, r, self.r[sl]); self.ax[sl] = np.where(m, tx, self.ax[sl]); self.ay[sl] = np.where(m, ty, self.ay[sl])
            self.bid[sl] = np.where(m, bid, self.bid[sl]); self.mossk[sl] = np.where(m, mossk, self.mossk[sl])
            self.twist[sl] = np.where(m, twist, self.twist[sl]); self.kind[sl] = np.where(m, kind, self.kind[sl])
        return c, rr, s

    def blob(self, cx, cy, rx, ry, seed=0):
        """A stone (kind 1) the roots can grip: stamps an ellipse; u/v hold its normalized x/y (see stone_shade)."""
        rng = np.random.default_rng(seed); W, H = self.w * S, self.h * S; bid = self.n; self.n += 1
        X0 = int(max(0, (cx - rx - 1) * S)); X1 = int(min(W, (cx + rx + 1) * S)); Y0 = int(max(0, (cy - ry - 1) * S)); Y1 = int(min(H, (cy + ry + 1) * S))
        yy, xx = np.mgrid[Y0:Y1, X0:X1]
        qx = ((xx + 0.5) / S - cx) / rx; qy = ((yy + 0.5) / S - cy) / ry
        ang = np.arctan2(qy, qx); ph = rng.uniform(0, 6.3, 2)
        m = np.hypot(qx, qy) <= 1 + 0.08 * np.sin(3 * ang + ph[0]) + 0.05 * np.sin(5 * ang + ph[1])
        sl = (slice(Y0, Y1), slice(X0, X1))
        self.cov[sl] |= m; self.kind[sl] = np.where(m, 1, self.kind[sl]); self.bid[sl] = np.where(m, bid, self.bid[sl])
        self.u[sl] = np.where(m, np.clip(qx, -1, 1), self.u[sl]); self.v[sl] = np.where(m, np.clip(qy, -1, 1), self.v[sl])
        self.along[sl] = np.where(m, -1.0, self.along[sl])

    def stone_shade(self, nz, val, moss, light=(-0.6, -0.6, 0.5)):
        st = self.cov & (self.kind == 1)
        if not st.any(): return val, moss, st
        qx, qy = self.u, self.v; qz = np.sqrt(np.clip(1 - qx * qx - qy * qy, 0, 1))
        L = np.array(light, float); L /= np.linalg.norm(L)
        d = np.clip(qx * L[0] + qy * L[1] + qz * L[2], 0, 1)
        tex = nz(qx * 9 + self.bid * 13, qy * 9) - 0.5
        val = np.where(st, 0.2 + 0.7 * d + 0.1 * tex, val)
        moss = np.where(st, (qy < -0.25 + 0.3 * tex).astype(float), moss)
        return val, moss, st

    def shade(self, nz, light=(-0.55, -0.75, 0.38), rim_dir=(-0.4, -0.9), seed=1, ridges=0.42, furrow_depth=0.62, ambient=0.16,
              key=0.75, rimk=1.0, moss_amt=0.5, moss_side=(-1.0, -0.2), side_k=0.5, plate_len=9.0, gap=0.16, pattern='plates', gaps=0.3, fw=0.16):
        """-> (value 0..1, rim 0..1, moss 0..1, furrow 0..1) on the 4x grid. The bark is a cellular pattern laid out in the
        limb's own (angle, length) frame: plates elongated along the limb, deep fissures between them, which wrap round it."""
        cov = self.cov; u = np.clip(self.u, -0.999, 0.999)
        th = np.arcsin(u)
        nx_, ny_ = -self.ay, self.ax                       # in-plane normal of the axis (u > 0 side)
        Nx = np.sin(th) * nx_; Ny = np.sin(th) * ny_; Nz = np.cos(th)
        L = np.array(light, float); L /= np.linalg.norm(L)
        diff = np.clip(Nx * L[0] + Ny * L[1] + Nz * L[2], 0, 1)
        K = np.maximum(2.0, self.r * ridges)
        v = self.v
        a = K * (th / math.pi + 0.5) + self.twist * v / np.maximum(4, self.r) + 0.9 * nz(v * 0.05 + self.bid * 37, th * 5 + self.bid * 11)
        if pattern == 'fissure':
            # long wandering fissures round the limb (gaps where two plates merge), each groove's far wall catching the light
            ia = np.floor(a); best = np.full(a.shape, 9.0); sgn = np.zeros(a.shape); pid = np.zeros(a.shape)
            for k in (-1, 0, 1, 2):
                i = ia + k
                line = i + (0.5 * (nz(i * 37.3 + self.bid * 23, v * 0.032 + i * 7.1) - 0.5) + 0.18 * (nz(i * 19.9 + 77, v * 0.11 + i * 3.3) - 0.5)) * 2
                present = nz(i * 13.7 + 100 + self.bid * 29, v * 0.03 + i * 5.3) > gaps
                d = np.where(present, np.abs(a - line), 9.0)
                closer = d < best
                best = np.where(closer, d, best); sgn = np.where(closer, a - line, sgn)
            furrow = 1 - smooth(fw * 0.4, fw, best)
            cell = np.floor(a - 0.5 * 0) + np.floor(v / plate_len) * 31
            pt = nz(cell * 5.7, cell * 1.3 + 9)
            val = ambient + key * diff
            val = val * (1 - furrow_depth * furrow)
            val += 0.10 * (pt - 0.5) * (1 - furrow)
            lip = smooth(fw * 0.8, fw * 1.6, sgn) * (1 - smooth(fw * 2.2, fw * 3.6, sgn))
            sh = smooth(fw * 0.8, fw * 1.6, -sgn) * (1 - smooth(fw * 2.0, fw * 3.0, -sgn))
            val += 0.12 * lip * (0.4 + diff) - 0.06 * sh
            ck = nz(cell * 11.1 + 40, v * 0.5) 
            val -= 0.18 * smooth(0.82, 0.9, ck) * (1 - furrow)
        else:
            b = v / plate_len + 0.6 * nz(a * 3.1 + 50, v * 0.03)
            f1, f2, cid = worley(a, b + self.bid * 17.0, seed)
            edge = f2 - f1
            furrow = 1 - smooth(gap * 0.4, gap, edge)
            val = ambient + key * diff
            val = val * (1 - furrow_depth * furrow)
            val += 0.07 * (cid - 0.5) * (1 - furrow)
            rel = smooth(gap, gap * 3, edge)
            val += 0.08 * rel * diff
        val += 0.04 * (nz(self.v * 0.7, th * 24) - 0.5)
        rim = np.zeros_like(u)
        for rd in (rim_dir if isinstance(rim_dir[0], (tuple, list)) else [rim_dir]):
            R = np.array(rd[:2], float); k = rd[2] if len(rd) > 2 else 1.0; R /= np.linalg.norm(R)
            face = np.clip(np.sin(th) * (nx_ * R[0] + ny_ * R[1]), 0, 1)
            ed = (1 - np.abs(u)) * self.r                       # px from the silhouette edge
            rim = np.maximum(rim, (1 - smooth(0.6, 2.2, ed)) * face * k * rimk)
        up = np.clip(-Ny, 0, 1) * 0.9 + np.clip(Nx * moss_side[0] + Ny * moss_side[1], 0, 1) * side_k
        mn = nz(self.v * 0.09 + 100, th * 3 + self.bid * 7)
        moss = smooth(0.55, 0.75, up * 0.9 + mn * 0.6 - (1 - moss_amt) * 0.9) * self.mossk
        return np.where(cov, val, 0), np.where(cov, rim, 0), np.where(cov, moss, 0), np.where(cov, furrow, 0)


def worley(a, b, seed=0, jit=0.85):
    """F1, F2 and a per-cell random id of a unit-cell jittered grid evaluated at float coords (a, b)."""
    ia = np.floor(a).astype(np.int64); ib = np.floor(b).astype(np.int64)
    f1 = np.full(a.shape, 9.0); f2 = np.full(a.shape, 9.0); cid = np.zeros(a.shape)
    def h(x, y, k):
        q = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791 + k * 2654435761)
        q = (q ^ (q >> 13)) * 1274126177
        return ((q ^ (q >> 16)) & 0xFFFF) / 65535.0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx = ia + dx; cy = ib + dy
            px = cx + 0.5 + (h(cx, cy, 1) - 0.5) * jit; py = cy + 0.5 + (h(cx, cy, 2) - 0.5) * jit
            d = np.sqrt((a - px) ** 2 + (b - py) ** 2)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d)); cid = np.where(closer, h(cx, cy, 3), cid); f1 = np.where(closer, d, f1)
    return f1, f2, cid


# ----------------------------------------------------------------------------------------------- foliage
class Leaves:
    """4x grid of foliage. A lobe is split into sub-masses, each filled with small scalloped clumps; every clump is a little
    sphere in a z-buffer (height H) and carries a normal blended from the lobe, its sub-mass and itself. shade() lights the
    normals and darkens the cavities (where H sits below its blurred neighbourhood) so clumps read as layered leaf masses."""

    def __init__(self, w, h, light=(-0.5, -0.72, 0.48)):
        self.w, self.h = w, h; W, H = w * S, h * S
        self.cov = np.zeros((H, W), bool); self.H = np.full((H, W), -1e3)
        self.dl = np.zeros((H, W)); self.ds = np.zeros((H, W)); self.dc = np.zeros((H, W)); self.lift = np.zeros((H, W))
        L = np.array(light, float); self.L = L / np.linalg.norm(L)
        self.holes = []

    def lobe(self, cx, cy, rx, ry, seed, dens=1.0, clump=(2.4, 4.6), subs=None, zbase=0.0, lift=0.0, holes=0.0, drip=0.25, ragged=0.18,
             wts=(0.25, 0.5, 0.3), tilt=0.0, sub_r=(0.38, 0.6), droop=0.0):
        """tilt (radians) turns the lobe; droop bends its ends down (px at the tips)."""
        rng = np.random.default_rng(seed); W, H = self.w * S, self.h * S
        ct, st = math.cos(tilt), math.sin(tilt)
        ns = subs or int(np.clip(rx * ry / 140, 3, 9))
        sub = []
        for k in range(ns):
            a = rng.uniform(0, 2 * math.pi); d = rng.uniform(0.15, 0.62) if k else 0.0
            sx, sy = math.cos(a) * d, math.sin(a) * d * 0.85 - 0.05
            sr = rng.uniform(*sub_r)
            sub.append((sx, sy, sr * rx, sr * ry * rng.uniform(0.85, 1.15)))
        items = []
        for (sx, sy, srx, sry) in sub:
            n = int(dens * math.pi * srx * sry / (clump[0] * clump[1] * 0.9)) + 2
            for _ in range(n):
                a = rng.uniform(0, 2 * math.pi); d = rng.random() ** 0.55
                ux, uy = math.cos(a) * d, math.sin(a) * d
                items.append((sx * rx + ux * srx, sy * ry + uy * sry, ux, uy, sx, sy))
        # a few ragged sprays poking out of the outline, and leaves dripping under the lobe
        for _ in range(int(ragged * (rx + ry))):     # sprays on the sub-masses' rims (they stay attached)
            sx, sy, srx, sry = sub[int(rng.integers(len(sub)))]
            a = rng.uniform(math.pi * 1.05, math.pi * 1.95) if rng.random() < 0.6 else rng.uniform(0, 2 * math.pi)
            k = rng.uniform(0.85, 1.0)
            items.append((sx * rx + math.cos(a) * srx * k, sy * ry + math.sin(a) * sry * k, math.cos(a), math.sin(a), sx, sy))
        for _ in range(int(drip * rx)):               # leaves hanging under a sub-mass
            sx, sy, srx, sry = sub[int(rng.integers(len(sub)))]
            x = rng.uniform(-0.7, 0.7)
            items.append((sx * rx + x * srx, sy * ry + sry * math.sqrt(max(0, 1 - x * x)) * rng.uniform(0.8, 0.98), x * 0.6, 0.8, sx, sy))
        for (px0, py0, ux, uy, sx, sy) in items:
            lx, ly = px0 / rx, py0 / ry
            ccx, ccy = cx + px0 * ct - py0 * st, cy + px0 * st + py0 * ct + droop * lx * lx
            lx, ly = lx * ct - ly * st, lx * st + ly * ct; lr = min(1.0, math.hypot(lx, ly)); lz = math.sqrt(max(0.0, 1 - lr * lr))
            uz = math.sqrt(max(0.0, 1 - min(1.0, ux * ux + uy * uy)))
            rc = rng.uniform(*clump) * (0.8 + 0.35 * lz)
            ph1, ph2 = rng.uniform(0, 6.3, 2); lob = int(rng.integers(5, 8))
            X0 = int(max(0, (ccx - rc * 1.4) * S)); X1 = int(min(W, (ccx + rc * 1.4) * S + 1))
            Y0 = int(max(0, (ccy - rc * 1.4) * S)); Y1 = int(min(H, (ccy + rc * 1.4) * S + 1))
            if X0 >= X1 or Y0 >= Y1: continue
            yy, xx = np.mgrid[Y0:Y1, X0:X1]
            qx = (xx + 0.5) / S - ccx; qy = (yy + 0.5) / S - ccy
            ang = np.arctan2(qy, qx); dist = np.hypot(qx, qy)
            edge = rc * (1 + 0.2 * np.sin(lob * ang + ph1) + 0.1 * np.sin((2 * lob + 1) * ang + ph2))
            m = dist <= edge
            if not m.any(): continue
            q = np.clip(dist / edge, 0, 0.999); cz = np.sqrt(1 - q * q)
            hgt = zbase + lz * ry * 0.9 + uz * 3.0 + cz * rc
            sl = (slice(Y0, Y1), slice(X0, X1))
            put = m & (hgt > self.H[sl])
            if not put.any(): continue
            cnx, cny = qx / edge, qy / edge
            Lx, Ly, Lz = self.L
            dl = max(0.0, lx * Lx + ly * Ly + lz * Lz); ds = max(0.0, ux * Lx + uy * Ly + uz * Lz)
            dc = np.clip(cnx * Lx + cny * Ly + cz * Lz, 0, 1)
            self.cov[sl] |= put; self.H[sl] = np.where(put, hgt, self.H[sl])
            self.dl[sl] = np.where(put, dl, self.dl[sl]); self.ds[sl] = np.where(put, ds, self.ds[sl])
            self.dc[sl] = np.where(put, dc, self.dc[sl]); self.lift[sl] = np.where(put, lift, self.lift[sl])
        if holes:
            for _ in range(int(holes * rx * ry / 120)):
                a = rng.uniform(0, 2 * math.pi); d = rng.uniform(0.2, 0.9)
                hx, hy = cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry; hr = rng.uniform(0.9, 2.1)
                self.holes.append((hx, hy, hr))
                for _ in range(int(rng.integers(1, 3))):     # ragged: two or three overlapping bites
                    self.holes.append((hx + rng.uniform(-2, 2), hy + rng.uniform(-1.5, 1.5), hr * rng.uniform(0.5, 0.9)))

    def shade(self, ambient=0.1, wl=0.45, ws=0.3, wc=0.42, ao=0.03, ao_sigma=3.0):
        """value = the mass's light (lobe + sub-mass) + each clump's own lit crescent (centred, so it shifts the band up or down)
        - cavities."""
        Hc = np.where(self.cov, self.H, np.nan)
        base = np.nan_to_num(Hc, nan=np.nanmin(Hc) if self.cov.any() else 0)
        wgt = self.cov.astype(float)
        bl = gblur(base * wgt, ao_sigma * S) / np.maximum(gblur(wgt, ao_sigma * S), 1e-6)
        cav = np.clip((bl - base) * ao, 0, 1)
        v = ambient + wl * self.dl + ws * self.ds + wc * (self.dc - 0.55) - cav * 0.8 + self.lift
        return np.where(self.cov, v, 0), cav


def _box1(a, r, axis):
    if r < 1: return a
    n = a.shape[axis]; pad = [(0, 0)] * a.ndim; pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis); lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def gblur(a, s):
    r = max(1, int(round((math.sqrt(12 * s * s / 3 + 1) - 1) / 2)))
    for _ in range(3): a = _box1(_box1(a, r, 0), r, 1)
    return a


# ----------------------------------------------------------------------------------------------- 4x -> 1x
def down(a, w, h):
    H, W = a.shape[:2]
    return a.reshape(h, S, w, S, *a.shape[2:]).mean(axis=(1, 3))


def bayer(h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    return (B4[yy & 3, xx & 3] + 0.5) / 16


def ramp_index(val, n, dk=0.9, off=0.0):
    """value 0..1 -> ramp index with an ordered dither across band edges (dk = dither width in bands)."""
    h, w = val.shape
    f = np.clip(val, 0, 1) * (n - 1) + (bayer(h, w) - 0.5) * dk + off
    return np.clip(np.round(f), 0, n - 1).astype(int)


def neighbours(a):
    p = np.pad(a, 1)
    return p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]   # up, down, left, right


def outline(rgba, col=(10, 13, 12), alpha_min=1, ext=None):
    a = rgba[..., 3] >= alpha_min
    up, dn, lf, rt = neighbours(a)
    o = ~a & (up | dn | lf | rt)
    if ext is not None: o &= ext
    out = rgba.copy(); out[o] = (*col, 255)
    return out


def orphans(idx, mask, passes=1):
    """Replace single pixels whose value matches none of their 4 neighbours by the most common neighbour (inside mask)."""
    a = idx.copy()
    for _ in range(passes):
        p = np.pad(a, 1, mode='edge')
        nb = np.stack([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]], -1)
        lonely = mask & ~(nb == a[..., None]).any(-1)
        ys, xs = np.nonzero(lonely)
        for y, x in zip(ys, xs):
            v, c = np.unique(nb[y, x], return_counts=True); a[y, x] = v[np.argmax(c)]
    return a


def carve(holes, *grids, w=None, h=None):
    """Punch the collected sky holes through every given 4x coverage grid."""
    for hx, hy, hr in holes:
        for g in grids:
            Hh, Ww = g.shape
            X0 = int(max(0, (hx - hr) * S)); X1 = int(min(Ww, (hx + hr) * S + 1)); Y0 = int(max(0, (hy - hr) * S)); Y1 = int(min(Hh, (hy + hr) * S + 1))
            if X0 >= X1 or Y0 >= Y1: continue
            yy, xx = np.mgrid[Y0:Y1, X0:X1]
            m = np.hypot((xx + 0.5) / S - hx, ((yy + 0.5) / S - hy) * 1.25) <= hr
            g[Y0:Y1, X0:X1] &= ~m


def exterior(alpha, min_hole=14):
    """Transparent pixels that are part of the open background: connected to the frame border, or enclosed gaps of at least
    min_hole px. (Tiny enclosed holes are dappled light inside a leaf mass: they get no outline.)"""
    h, w = alpha.shape; seen = np.zeros_like(alpha, bool); out = np.zeros_like(alpha, bool)
    for y0 in range(h):
        for x0 in range(w):
            if alpha[y0, x0] or seen[y0, x0]: continue
            stack = [(y0, x0)]; seen[y0, x0] = True; comp = []; border = False
            while stack:
                y, x = stack.pop(); comp.append((y, x))
                if y == 0 or x == 0 or y == h - 1 or x == w - 1: border = True
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w and not alpha[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; stack.append((yy, xx))
            if border or len(comp) >= min_hole:
                ys, xs = zip(*comp); out[list(ys), list(xs)] = True
    return out


# ----------------------------------------------------------------------------------------------- 1x dressing
def strands(rgba, rng, anchors, cols, length=(4, 20), per=(2, 5), drift=0.0, sway=0.6, only_empty=True):
    """Hanging moss: curtains of 1 px strands from anchor points (x, y = the last opaque pixel), darker at the root, catching the
    light towards the tips. cols: dark..light ramp (RGB)."""
    h, w = rgba.shape[:2]
    for ax, ay, scale in anchors:
        n = int(rng.integers(per[0], per[1] + 1)); base = rng.uniform(*length) * scale
        for j in range(n):
            sx = ax + int(rng.integers(-2, 3)); L = int(max(2, base * rng.uniform(0.45, 1.0))); ph = rng.uniform(0, 6.3)
            for k in range(L):
                x = int(round(sx + math.sin(k * 0.33 + ph) * sway + k * drift)); y = ay + 1 + k
                if not (0 <= x < w and 0 <= y < h): break
                if only_empty and rgba[y, x, 3] > 0 and k > 1: break
                t = k / max(1, L - 1)
                ci = min(len(cols) - 1, int(t * (len(cols) - 0.8) + rng.uniform(-0.4, 0.4)))
                ci = max(0, ci)
                rgba[y, x, :3] = cols[ci]; rgba[y, x, 3] = 255 if t < 0.7 or rgba[y, x, 3] else 170   # the tips thin out


def vine(rgba, p0, p1, sag, col, leaf, rng, step=0.5):
    """A rope of 1 px between two points, sagging; small leaves along it."""
    h, w = rgba.shape[:2]
    (x0, y0), (x1, y1) = p0, p1; n = int(math.hypot(x1 - x0, y1 - y0) / step) + 2; last = None
    for i in range(n):
        t = i / (n - 1); x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        q = (int(round(x)), int(round(y)))
        if q == last or not (0 <= q[0] < w and 0 <= q[1] < h): continue
        last = q; rgba[q[1], q[0]] = (*col, 255)
        if rng.random() < 0.16:
            lx, ly = q[0] + int(rng.choice([-1, 1])), q[1] + 1
            if 0 <= lx < w and 0 <= ly < h: rgba[ly, lx] = (*leaf, 255)


def spore(rgba, x, y, core, halo, a=1.0):
    """A glowing spore: a bright core pixel and a soft translucent halo (drawn into empty pixels, blended over opaque ones)."""
    h, w = rgba.shape[:2]
    for dx, dy, k in ((0, 0, 1.0), (1, 0, 0.5), (-1, 0, 0.5), (0, 1, 0.5), (0, -1, 0.5), (1, 1, 0.2), (-1, 1, 0.2), (1, -1, 0.2), (-1, -1, 0.2),
                      (2, 0, 0.12), (-2, 0, 0.12), (0, 2, 0.12), (0, -2, 0.12)):
        xx, yy = x + dx, y + dy
        if not (0 <= xx < w and 0 <= yy < h): continue
        kk = k * a
        col = core if k == 1.0 else halo
        if k == 1.0:
            rgba[yy, xx, :3] = col; rgba[yy, xx, 3] = 255
        elif rgba[yy, xx, 3] == 0:
            rgba[yy, xx, :3] = col; rgba[yy, xx, 3] = int(255 * kk)
        else:
            rgba[yy, xx, :3] = rgba[yy, xx, :3] * (1 - kk * 0.6) + np.array(col) * kk * 0.6
