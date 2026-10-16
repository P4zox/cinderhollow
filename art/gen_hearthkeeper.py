#!/usr/bin/env python3
"""The Hearthkeeper -- the Cold Forge boss (agent BOSS, v17).  Rig: art/hearthkeeper_rig.py.

    python3 art/gen_hearthkeeper.py                    full build (Aseprite): every sheet + meta + previews
    python3 art/gen_hearthkeeper.py --preview          previews only (no Aseprite)
    python3 art/gen_hearthkeeper.py --only idle,slam --preview      quick iteration on some tags

How a move is authored: a list of KEY poses.  Each key changes only what it names (everything else carries over from the
key before) and says how the body gets there: `n` in-between frames over `ms`, with an easing curve `e` (anticipation:
slow 'out' into the wind-up and a held key; the strike: an 'in' snap over one or two fast frames; follow-through: an
'out' settle past the hit before the recovery).  Hands are aimed in polar form from the shoulder (angle `an`/`af`,
reach `rn`/`rf` as a share of the arm's length), so tweened hands travel on arcs, never straight lines; the elbow
follows by IK.  Cloth is not keyed: the veil, sleeves, apron, hem and the ring of keys are springs driven by the
body's own motion (they trail a lunge, swing past a stop and settle).  Feet lift on their own when they move.

Outputs
    assets/hearthkeeper_p<phase>_<n>.png/.json     per phase, tags packed <= 18 frames a sheet
    assets/hearthkeeper_meta.json                  anchor, per-frame hit rects, hurt rects, telegraph points, events,
                                                   weapon-head points, hammer heat pixels, root shifts, sheet map
    assets/hearthkeeper_props.png/.json            the dropped weapons cooling, the embedded hammer, the core, the crown
    art/previews/hearthkeeper_*.png                strips, contact sheet, hitbox overlay
Faces RIGHT; anchor (AX, AY) = the floor line under his feet.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import hearthkeeper_rig as R  # noqa: E402
from hearthkeeper_rig import W, H, AX, AY, FLOOR, HIP_Y, L_UA, L_FA  # noqa: E402

PREVIEW = "--preview" in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
PV = os.path.join(ART, "previews")
os.makedirs(PV, exist_ok=True)
ARM = L_UA + L_FA

# ============================================================================ easing
EASE = {
    "lin": lambda u: u,
    "io": lambda u: u * u * (3 - 2 * u),
    "in": lambda u: u * u,
    "in3": lambda u: u * u * u,
    "out": lambda u: 1 - (1 - u) * (1 - u),
    "out3": lambda u: 1 - (1 - u) ** 3,
    "back": lambda u: 1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2,     # overshoot then settle
}

DEFAULT = dict(x=0.0, y=0.0, lean=3.0, tilt=2.0, fn=8.0, ff=-7.0, fnl=0.0, ffl=0.0,
               an=78.0, rn=0.8, af=96.0, rf=0.8, pno=0.0, pfo=0.0,
               wa=90.0, two=0.0, tw=12.0, ta=98.0, topen=3.0, wbelow=6.0, wabove=34.0, wcurve=-3.5,
               ca=0.0, cl=30.0, cb=0.0, cs=0.0,
               eyes=0.55, fire=0.0, crown=0.0, chest=0.0, wheat=0.0, theat=0.0, coal=1.0, wind=0.0,
               lift_n=0.0, lift_f=0.0, flare=1.0, hemlift=0.0, spread_n=1.0, spread_f=1.0, hold_cloth=0.0, gnd=0.0, dissolve=0.0)
DISCRETE = ("hw", "weapon", "mn", "mf", "wb", "wflip", "tongs_far", "two_front", "spear_front", "hide", "lock", "lights", "wfree")
PER_KEY = ("fx", "act", "tel", "ev", "sm", "pt")       # belong to the key's own frame only (act: also its in-betweens)


def K(n=1, ms=None, e="io", hold=0, **kw):
    return dict(_n=n, _ms=ms if ms is not None else 100 * n, _e=e, _hold=hold, **kw)


# ============================================================================ the timeline
class Anim:
    def __init__(self, tag, keys, loop=False, common=None, phase=1):
        self.tag, self.loop, self.phase = tag, loop, phase
        st = dict(DEFAULT)
        st.update(common or {})
        self.keys = []
        t = 0.0
        for i, k in enumerate(keys):
            s = dict(st)
            for a, v in k.items():
                if not a.startswith("_") and a not in PER_KEY:
                    s[a] = v
            for d in DISCRETE:
                s.setdefault(d, None)
            per = {a: k[a] for a in PER_KEY if a in k}
            if i == 0:
                seg = 0.0
                t0 = 0.0
            else:
                seg = k["_ms"]
                t0 = t
            t = t0 + seg
            if s.get("wfree") == "keep":          # let go of the weapon where the last key left it
                prev = dict(st)
                hn_, _, _ = hands(prev)
                s["wfree"] = (hn_[0], hn_[1], prev["wa"])
            ps = self._polar(s)
            self.keys.append(dict(state=ps, per=per, t=t, t0=t0, n=k["_n"] if i else 1, ease=k["_e"],
                                  hold=k.get("_hold", 0), ms0=k["_ms"] if i == 0 else 0))
            t += k.get("_hold", 0)
            st = ps
            # per-key one-shot params do not carry
        self.T = t
        # frames: (time, key index, k-th in-between)
        self.frames = []
        for i, k in enumerate(self.keys):
            if i == 0:
                self.frames.append(dict(t=0.0, key=0, sub=0, dur=k["ms0"] + k["hold"]))
                continue
            for j in range(1, k["n"] + 1):
                tt = k["t0"] + k["t"] * 0 + (k["t"] - k["t0"]) * j / k["n"]
                dur = (k["t"] - k["t0"]) / k["n"] + (k["hold"] if j == k["n"] else 0)
                self.frames.append(dict(t=tt, key=i, sub=j, dur=dur))
        if loop:     # a loop's last key equals its first: drop the duplicate frame
            pass
        self.total = sum(f["dur"] for f in self.frames)

    def _polar(self, s):
        """Hands given as absolute 'hn'/'hf' (dx from AX, dy from AY) become polar about that key's shoulder."""
        s = dict(s)
        for side in ("n", "f"):
            k = "h" + side
            if k in s and s[k] is not None:
                sh = shoulders(s)[0 if side == "n" else 1]
                tgt = (AX + s[k][0], AY + s[k][1])
                v = R.sub(tgt, sh)
                s["a" + side] = R.ang(v)
                s["r" + side] = min(1.0, math.hypot(*v) / ARM)
                s[k] = None
        return s

    def state_at(self, t):
        if self.loop and self.T > 0:
            t = t % self.T
        ks = self.keys
        if t <= 0:
            return dict(ks[0]["state"]), 0.0, None
        for i in range(1, len(ks)):
            k = ks[i]
            if t <= k["t"]:
                u = (t - k["t0"]) / max(1e-6, k["t"] - k["t0"])
                return mix(ks[i - 1]["state"], k["state"], EASE[k["ease"]](max(0.0, min(1.0, u))), u), u, i
            if t <= k["t"] + k["hold"]:
                return dict(k["state"]), 1.0, i
        return dict(ks[-1]["state"]), 1.0, len(ks) - 1


def mix(a, b, w, u):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out[k] = va + (vb - va) * w
        else:
            out[k] = vb if u > 0 else va
    # feet that travel lift on an arc (unless the keys lift them)
    lock = b.get("lock") or ""
    for f in ("fn", "ff"):
        dx = abs(b[f] - a[f])
        if dx > 2.5 and f[1] not in lock:
            out[f + "l"] = out[f + "l"] + math.sin(math.pi * w) * min(7.0, 1.5 + dx * 0.22)
    return out


def shoulders(s):
    hip = (AX + s["x"], HIP_Y + s["y"])
    neck = R.add(hip, R.rot((0, -R.SPINE), s["lean"]))
    sh_n = R.add(R.at(hip, neck, 0.9, 1.4), (0.4, 0.6))
    sh_f = R.at(hip, neck, 0.93, -3.6)
    return sh_n, sh_f, hip, neck


def ground_wa(s, hn):
    """the weapon angle (near s['wa']) that puts the hammer's head on the floor"""
    k = (FLOOR - 3.5 - hn[1]) / max(1.0, s["wabove"])
    if abs(k) >= 1:
        return s["wa"]
    a1 = math.degrees(math.asin(k)); cands = [a1, 180 - a1]
    best = min((c + 360 * n for c in cands for n in range(-2, 3)), key=lambda c: abs(c - s["wa"]))
    return best


def hands(s):
    sh_n, sh_f, hip, neck = shoulders(s)
    hn = R.add(sh_n, R.mul(R.dirv(s["an"]), s["rn"] * ARM))
    if s.get("gnd", 0) > 0 and s.get("weapon") == "hammer":
        s["wa"] = s["wa"] + (ground_wa(s, hn) - s["wa"]) * s["gnd"]
    hf = R.add(sh_f, R.mul(R.dirv(s["af"]), s["rf"] * ARM))
    if s["two"] > 0 and s.get("weapon") in ("hammer", "spear", "blade"):
        haft = R.sub(hn, R.mul(R.dirv(s["wa"]), s["tw"]))
        hf = R.lerp(hf, haft, s["two"])
    return hn, hf, hip


def weapon_seg(s, hn):
    """(inner, outer) points of the striking part, for smears."""
    w = s.get("weapon")
    if s.get("hw") == "handf":
        _, hf, _ = hands(s)
        return R.sub(hf, R.mul(R.dirv(s["af"]), 4)), R.add(hf, R.mul(R.dirv(s["af"]), 3)), None
    if s.get("hw") == "tong":
        _, hf, _ = hands(s)
        d = R.dirv(s["ta"]); mid = R.add(hf, R.mul(d, 30 * 1.02))
        return R.sub(mid, R.mul(d, 6)), R.add(mid, R.mul(d, 2)), None
    if w == "hammer":
        d = R.dirv(s["wa"]); head = R.add(hn, R.mul(d, s["wabove"]))
        v = R.mul(R.perp(d), s.get("wflip") or 1)
        face = R.add(head, R.mul(v, 6.0))
        return R.add(head, R.mul(d, -7.0)), R.add(head, R.mul(d, 3.5)), face
    if w == "blade":
        d = R.dirv(s["wa"]); return R.add(hn, R.mul(d, 36)), R.add(hn, R.mul(d, 49)), None
    if w == "spear":
        d = R.dirv(s["wa"]); tip = R.add(R.sub(hn, R.mul(d, s["wbelow"])), R.mul(d, 58)); return R.sub(tip, R.mul(d, 16)), tip, None
    if w == "chain":
        tip = R.add(hn, R.mul(R.dirv(s["ca"]), s["cl"]))
        return R.sub(tip, R.mul(R.unit(R.sub(tip, hn)), 5)), tip, None
    if w == "ftongs":
        d = R.dirv(s["wa"]); mid = R.add(hn, R.mul(d, 28 * 0.62 + 28 * 0.4))
        return R.sub(mid, R.mul(d, 9)), R.add(mid, R.mul(d, 5)), None
    if s.get("tongs_far"):
        return None
    return None


# ============================================================================ secondary motion (cloth springs)
def cloth_track(anim):
    """Integrate springs over the timeline (seconds; the keys are in ms); returns per-frame cloth values."""
    dt = 1 / 240.0
    loops = 3 if anim.loop else 1
    T = max(0.1, anim.T / 1000.0)
    times = [f["t"] / 1000.0 for f in anim.frames]

    def raw(t):
        s, _, _ = anim.state_at(t * 1000.0)
        hn, hf, hip = hands(s)
        return s, hn, hf, hip

    springs = {"wind": [0.0, 0.0], "apron": [0.0, 0.0], "ring": [0.0, 0.0], "hnx": [0.0, 0.0], "hny": [1.0, 0.0], "hfx": [0.0, 0.0], "hfy": [1.0, 0.0]}
    W0, Z = 13.0, 0.42

    def step(name, target, w0=W0, z=Z):
        x, v = springs[name]
        a = -w0 * w0 * (x - target) - 2 * z * w0 * v
        v += a * dt; x += v * dt
        springs[name] = [x, v]

    snaps = []
    t0 = 0.0 if anim.loop else -0.3
    n = int((T * loops - t0) / dt) + 2
    prev = raw(t0 if not anim.loop else 0.0)
    for j in range(n):
        tt = t0 + j * dt
        cur = raw(max(0.0, tt) if not anim.loop else tt)
        s, hn, hf, hip = cur
        _, phn, phf, phip = prev
        vx = (hip[0] - phip[0]) / dt; vy = (hip[1] - phip[1]) / dt
        vhn = ((hn[0] - phn[0]) / dt, (hn[1] - phn[1]) / dt)
        vhf = ((hf[0] - phf[0]) / dt, (hf[1] - phf[1]) / dt)
        step("wind", s["wind"] + 0.034 * vx - 0.01 * vy)
        step("apron", -0.016 * vx)
        step("ring", -0.02 * vx, w0=9, z=0.3)
        step("hnx", -0.0045 * vhn[0], w0=11, z=0.35); step("hny", 1.0 - 0.0035 * vhn[1], w0=11, z=0.35)
        step("hfx", -0.0045 * vhf[0], w0=11, z=0.35); step("hfy", 1.0 - 0.0035 * vhf[1], w0=11, z=0.35)
        prev = cur
        snaps.append((tt, {k: v[0] for k, v in springs.items()}))
    base = T * (loops - 1) if anim.loop else 0.0
    out = []
    for t in times:
        tgt = base + t
        j = min(len(snaps) - 1, max(0, int(round((tgt - t0) / dt))))
        out.append(snaps[j][1])
    return out


# ============================================================================ resolve a state into a rig pose
def resolve(s, cloth, phase):
    p = {}
    sh_n, sh_f, hip, neck = shoulders(s)
    hn, hf, _ = hands(s)
    p["hx"], p["hy"] = hip
    p["lean"], p["tilt"] = s["lean"], s["tilt"]
    p["fnx"], p["fny"] = AX + s["fn"], FLOOR - s["fnl"]
    p["ffx"], p["ffy"] = AX + s["ff"], FLOOR - s["ffl"]
    p["hn"], p["hf"] = hn, hf
    an_eff = R.ang(R.sub(hn, sh_n)); af_eff = R.ang(R.sub(hf, sh_f))
    p["pn"] = R.dirv(an_eff + 90 + s["pno"]); p["pf"] = R.dirv(af_eff + 90 + s["pfo"])
    w = s.get("weapon")
    p["weapon"] = w if w not in (None, "none") else None
    p["mn"] = s.get("mn") or ("fist" if p["weapon"] or True else "open")
    p["mf"] = s.get("mf") or "fist"
    if p["weapon"] in ("hammer", "spear", "blade", "ftongs"):
        p["gn"] = R.dirv(s["wa"])
    elif p["weapon"] == "chain":
        p["gn"] = R.dirv(s["ca"] + 90)
    else:
        p["gn"] = R.dirv(an_eff + 90)
    if s.get("tongs_far"):
        p["gf"] = R.dirv(s["ta"])
    elif s["two"] > 0.5 and p["weapon"]:
        p["gf"] = R.dirv(s["wa"])
    else:
        p["gf"] = R.dirv(af_eff + 90)
    for k in ("wa", "wbelow", "wabove", "wcurve", "ca", "cl", "cb", "cs", "ta", "topen", "eyes", "fire", "crown", "chest",
              "wheat", "theat", "coal", "lift_n", "lift_f", "flare", "hemlift", "spread_n", "spread_f"):
        p[k] = s[k]
    for k in ("wb", "wflip", "tongs_far", "two_front", "spear_front"):
        p[k] = s.get(k)
    if p["wflip"] is None:
        p["wflip"] = 1
    hc = 1.0 - s.get("hold_cloth", 0.0)
    p["wind"] = cloth["wind"] * hc + s["wind"] * (1 - hc)
    p["apron_sway"] = cloth["apron"]
    p["ring_sway"] = cloth["ring"]
    p["hang_n"] = (cloth["hnx"], max(0.35, cloth["hny"]))
    p["hang_f"] = (cloth["hfx"], max(0.35, cloth["hfy"]))
    p["hem"] = hip[1] + 28
    p["lights"] = list(s.get("lights") or [])
    if s.get("wfree"):
        p["wfree"] = s["wfree"]
    return p


# ============================================================================ in-sprite fx (data, so frames render in workers)
def fx_apply(cv, info, wres, spec, fi):
    k = spec[0]
    imp = wres.get("tip") if "face" in wres else wres.get("head")     # the striking point (the hammer's face)
    if k == "sparks":            # ('sparks', x, y, n, dir_deg, spread_deg, reach); x None = at the striking point, on the floor
        _, x, y, n, dr, sp, reach = spec
        if x is None:
            x, y = imp[0], min(FLOOR, imp[1] + 2)
        for i in range(n):
            a = dr + (R.hash01(i, 1, 21 + fi) - 0.5) * sp
            r = 3 + reach * R.hash01(i, 2, 21) ** 0.7
            p = R.add((x, y), R.mul(R.dirv(a), r))
            p = (p[0], min(p[1], FLOOR))
            tail = R.add(p, R.mul(R.dirv(a), -min(3.0, r * 0.25)))
            if i % 3 == 0:
                cv.glow(R.line(tail, p), "E4" if r > reach * 0.5 else "E6")
                cv.glow([p], "E7" if r < reach * 0.4 else "E5")
            else:
                cv.glow_under(R.line(tail, p), "E4" if r > reach * 0.5 else "E5", behind=True)
    elif k == "burst":           # ('burst', n, reach, at): sparks bursting from the weapon head ('tong' = the tongs' jaws)
        _, n, reach, where = spec
        c = (info.get("tong_mid") if where == "tong" else imp) or imp
        for i in range(n):
            a = (R.hash01(i, 3, 71 + fi) - 0.5) * 360
            r = 2 + reach * R.hash01(i, 4, 71) ** 0.6
            p = R.add(c, R.mul(R.dirv(a), r))
            tail = R.add(p, R.mul(R.dirv(a), -min(2.5, r * 0.3)))
            cv.glow(R.line(tail, p), "E5" if r < reach * 0.6 else "E4")
            cv.glow([p], "E7" if r < reach * 0.35 else "E6")
        cv.lights.append((c, 36.0, 1.0))
    elif k == "ring":            # ('ring', x, w, hot): the floor flash of a strike
        _, x, w, hot = spec
        if x is None:
            x = int(round(imp[0]))
        for dx in range(-w, w + 1):
            kk = 1 - abs(dx) / (w + 1)
            if kk > 0.15:
                cv.glow([(x + dx, FLOOR)], R.heat_col((0.2 + kk * 0.8) * hot), 255 if kk > 0.4 else 190)
            if kk > 0.6:
                cv.glow([(x + dx, FLOOR - 1)], "E3", 130)
    elif k == "dust":            # ('dust', x, n, w)
        _, x, n, w = spec
        for i in range(n):
            q = (x + (R.hash01(i, 1, 31 + fi) - 0.5) * w, FLOOR - R.hash01(i, 2, 32) * 5)
            cv.glow([q], "S5" if i % 3 else "S4", 190)
    elif k == "coals":           # ('coals', x0, x1, n, h): glowing coal bits in the air / on the floor
        _, x0, x1, n, h = spec
        for i in range(n):
            q = (x0 + (x1 - x0) * R.hash01(i, 4, 6 + fi), FLOOR - R.hash01(i, 5, 6) * h)
            cv.glow([q, R.add(q, (1, 0))], "E3" if i % 2 else "E4")
    elif k == "steam":           # ('steam', x, y, n)
        _, x, y, n = spec
        for i in range(n):
            q = (x + (R.hash01(i, 1, 51 + fi) - 0.5) * 10, y - R.hash01(i, 2, 52 + fi) * 14)
            cv.glow([q], "Q3" if i % 3 else "Q4", 130 if i % 2 else 190)
    elif k == "embers":          # ('embers', x0, y0, x1, y1, n)
        _, x0, y0, x1, y1, n = spec
        for i in range(n):
            q = (x0 + (x1 - x0) * R.hash01(i, 1, 63 + fi), y0 + (y1 - y0) * R.hash01(i, 2, 63 + fi))
            cv.glow([q], "E5" if i % 4 == 0 else "E4", 255 if i % 3 else 190)
            cv.glow([R.add(q, (0, 1))], "E2", 130)
    elif k == "smear":
        _, pix = spec
        wm = set(wres.get("m", set()))
        for (q, c, a) in pix:
            if q not in wm and q not in cv.fx:
                cv.fx[q] = R.RGBA[c][:3] + (a,)
    elif k == "flare":           # ('flare', x, y, r): a burst of light at a point (the hot weapon drawn, the coal flaring)
        _, x, y, r = spec
        if x is None:
            x, y = imp if imp else info["hip"]
        for a in range(0, 360, 30):
            for s in range(2, int(r) + 2):
                if s % 2 == 0:
                    cv.glow([R.add((x, y), R.mul(R.dirv(a + fi * 7), s))], "E5" if s < r * 0.6 else "E3", 255 if s < r * 0.6 else 190)
        cv.lights.append(((x, y), 40.0, 1.0))
    elif k == "light":           # ('light', x, y, r, k)
        _, x, y, r, kk = spec
        cv.lights.append(((x, y), r, kk))


SMEAR_COLS = {"cold": ("Q4", "Q3", "Q2"), "hot": ("E6", "E5", "E3"), "fire": ("E6", "E4", "E2")}


def smear_pixels(anim, f_prev, f_cur, style):
    """The swept band of the striking part between two frames (sub-sampled along the same eased timeline)."""
    t0, t1 = f_prev["t"], f_cur["t"]
    segs = []
    N = 40
    for i in range(N + 1):
        t = t0 + (t1 - t0) * i / N
        s, _, _ = anim.state_at(t)
        hn, hf, hip = hands(s)
        seg = weapon_seg(s, hn)
        if seg:
            segs.append(seg)
    if len(segs) < 2:
        return []
    cols = SMEAR_COLS[style]
    best = {}
    n = len(segs) - 1
    for i in range(n):
        a0, b0, _ = segs[i]; b1 = segs[i + 1][1]
        age = 1 - (i + 1) / n                    # 0 = newest
        L = R.dist(a0, b0) or 1
        inward = R.unit(R.sub(a0, b0))
        width = 1.0 + (L * 0.55) * (1 - age) ** 1.3           # thick at the weapon, thinning to a hairline at the tail
        steps = max(1, int(R.dist(b0, b1) * 2))
        for k in range(steps + 1):
            c = R.lerp(b0, b1, k / steps)
            for j in range(int(width) + 1):
                q = R.ipt(R.add(c, R.mul(inward, j)))
                sc = (1 - age) * (1 - j / (width + 1))
                if q not in best or sc > best[q]:
                    best[q] = sc
    out = []
    for q, sc in best.items():
        if q[1] > FLOOR or sc < 0.06:
            continue
        if sc > 0.55:
            out.append((q, cols[0], 255))
        elif sc > 0.25:
            out.append((q, cols[1], 220))
        else:
            out.append((q, cols[2], 150))
    return out


# ============================================================================ render one frame (used in workers)
ANIMS = {}          # tag -> (builder, phase list)
_CACHE = {}


def get_anim(tag, phase):
    key = (tag, phase)
    if key not in _CACHE:
        a = ANIMS[(tag, phase)](phase)
        a.cloth = cloth_track(a)
        _CACHE[key] = a
    return _CACHE[key]


def smear_style(anim, phase, s):
    w = s.get("weapon")
    if w == "hammer":
        return "hot" if s["wheat"] > 0.3 else "cold"
    if w == "ftongs":
        return "fire"
    if w in ("blade", "spear", "chain"):
        return "hot"
    return "cold"


def render_frame(args):
    tag, phase, i = args
    a = get_anim(tag, phase)
    f = a.frames[i]
    s, _, _ = a.state_at(f["t"])
    key = a.keys[f["key"]]
    per = key["per"] if f["sub"] == key["n"] or f["key"] == 0 else {}
    p = resolve(s, a.cloth[i], phase)
    fx = list(per.get("fx", []))
    act = key["per"].get("act") if f["key"] > 0 else None
    sm = key["per"].get("sm") or act
    if sm and i > 0 and s.get("hw") != "handf":
        pix = smear_pixels(a, a.frames[i - 1], f, smear_style(a, phase, s))
        if tag not in BACK_OK:
            pix = [q for q in pix if q[0][0] >= AX - 4]
        if pix:
            fx.insert(0, ("smear", pix))
    p["fx"] = [(lambda cv, info, wres, sp=sp: fx_apply(cv, info, wres, sp, i)) for sp in fx]
    img, info = R.figure(p, phase, fi=i)
    if s.get("dissolve", 0) > 0:
        img = dissolve(img, s["dissolve"], i)
    # info for the meta
    wres = info["weapon"]
    hit = set()
    if act and s.get("hw") == "handf":
        hit |= {q for q, t in info["mask"].items() if t == "hand" and R.dist(q, p["hf"]) < 6}
        hit |= {R.ipt(R.add(p["hf"], (dx, dy))) for dx in range(-7, 8) for dy in range(-7, 8)}
    elif act and s.get("hw") == "tong":
        hit |= set(info["tongs"].get("px", set()))
        hit = {q for q in hit if R.dist(q, info["tongs"]["mid"]) < 16}
    elif act:
        hit |= set(wres.get("m", set()))
        if s.get("weapon") == "spear":
            d = R.dirv(s["wa"])
            for k in range(0, 34, 2):
                hit.add(R.ipt(R.sub(wres["tip"], R.mul(d, k))))
        for spx in fx:
            if spx[0] == "smear":
                hit |= {q for q, c, al in spx[1]}
        hit = {q for q in hit if q[1] <= FLOOR and 0 <= q[0] < W and 0 <= q[1] < H}
    body = {q for q, t in info["mask"].items() if t in ("body", "head")}
    head = wres.get("head")
    if s.get("weapon") == "hammer":
        head = wres.get("tip")
    heat = []
    if s.get("weapon") == "hammer" and "m" in wres:
        edge = R.edge_of(wres["m"])
        for q in sorted(wres["m"]):
            lv = 2 if q in wres.get("face", ()) else (1 if q in edge else 0)
            if lv:
                heat.append((q[0], q[1], lv))
    out = dict(hit=sorted(hit), body=bbox(body), head=pt(head) if head else None,
               hand=pt(p["hn"]), handf=pt(p["hf"]), heat=heat,
               tong=pt(info["tongs"]["mid"]) if info.get("tongs") else None)
    return img.tobytes(), out


def dissolve(img, k, fi):
    """burn away to ash from the crown down: pixels above a ragged falling line turn to embers, then are gone"""
    px = img.load()
    bb = img.getbbox()
    if not bb:
        return img
    y0, y1 = bb[1], bb[3]
    line_y = y0 + (y1 - y0 + 14) * k
    for y in range(y0, y1):
        for x in range(bb[0], bb[2]):
            if px[x, y][3] == 0:
                continue
            edge = line_y + (R.hash01(x, 0, 7) - 0.5) * 10
            if y < edge - 3:
                px[x, y] = (0, 0, 0, 0)
                if R.hash01(x, y, fi) > 0.985 and y + 6 < FLOOR:
                    px[x, max(0, y - int(6 * k))] = R.RGBA["E4"] if R.hash01(x, y, 2) > 0.5 else R.RGBA["K3"]
            elif y < edge:
                px[x, y] = R.RGBA["E5"] if R.hash01(x, y, fi + 1) > 0.5 else R.RGBA["E3"]
    return img


def bbox(pts, pad=0):
    if not pts:
        return None
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return [min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 1 + 2 * pad, max(ys) - min(ys) + 1 + 2 * pad]


def pt(q):
    return [int(round(q[0])), int(round(q[1]))]


# ============================================================================ the moves
from hk_moves import register  # noqa: E402  (the move library: art/hk_moves.py)
register(ANIMS, K, Anim)


# ============================================================================ build
PHASE_TAGS = {}


def build_all(tags_by_phase):
    import multiprocessing as mp
    jobs = []
    for ph, tags in tags_by_phase.items():
        for t in tags:
            a = get_anim(t, ph)
            for i in range(len(a.frames)):
                jobs.append((t, ph, i))
    ctx = mp.get_context("fork")
    with ctx.Pool(min(16, os.cpu_count() or 4)) as pool:
        res = pool.map(render_frame, jobs, chunksize=2)
    out = {}
    for (t, ph, i), (raw, inf) in zip(jobs, res):
        out.setdefault((ph, t), []).append((Image.frombytes("RGBA", (W, H), raw), inf))
    return out


def preview_strip(name, frames, durs, scale=3, bg=(70, 72, 82, 255)):
    n = len(frames)
    sh = Image.new("RGBA", (n * W * scale, H * scale + 14), (36, 38, 46, 255))
    d = ImageDraw.Draw(sh)
    for i, im0 in enumerate(frames):
        im = Image.new("RGBA", (W, H), bg)
        im.alpha_composite(im0)
        for x in range(W):
            im.putpixel((x, AY), (52, 46, 46, 255))
        sh.alpha_composite(im.resize((W * scale, H * scale), Image.NEAREST), (i * W * scale, 0))
        d.text((i * W * scale + 4, H * scale + 1), f"{i}  {int(durs[i])}ms", fill=(200, 200, 210, 255))
    sh.save(os.path.join(PV, name))


def pack(tags, cnt, cap=18):
    bins = []
    for t in sorted(tags, key=lambda t: -cnt[t]):
        for b in bins:
            if sum(cnt[x] for x in b) + cnt[t] <= cap:
                b.append(t); break
        else:
            bins.append([t])
    return bins


def main():
    import hk_moves
    tags_by_phase = {ph: [t for t in hk_moves.PHASE_TAGS[ph] if ONLY is None or t in ONLY] for ph in (1, 2, 3)}
    built = build_all(tags_by_phase)
    meta = {"native": 1, "frame": [W, H], "anchor": [AX, AY], "floor_y": AY, "sheets": {}, "attacks": {}, "telegraph": {},
            "events": {}, "pts": {}, "heat": {}, "body": {}, "shift": {}, "dur": {}}
    for ph in (1, 2, 3):
        P = f"p{ph}"
        cnt = {}
        for t in tags_by_phase[ph]:
            a = get_anim(t, ph)
            fr = built[(ph, t)]
            durs = [f["dur"] for f in a.frames]
            preview_strip(f"hearthkeeper_{t}_p{ph}.png", [im for im, _ in fr], durs)
            cnt[t] = len(fr)
            infos = [inf for _, inf in fr]
            # windows from the keys' act ids
            wins = {}
            for i, f in enumerate(a.frames):
                k = a.keys[f["key"]]
                act = k["per"].get("act") if f["key"] > 0 else None
                if act and infos[i]["hit"]:
                    wins.setdefault(act, []).append(i)
            W_ = []
            for wid in sorted(wins):
                fs = wins[wid]
                pts_ = {i: [q for q in infos[i]["hit"] if t in BACK_OK or q[0] >= AX - 6] or infos[i]["hit"] for i in fs}
                rects = {str(i): bbox(pts_[i]) for i in fs}
                W_.append({"active": [fs[0], fs[-1]], "hit": union([rects[str(i)] for i in fs]), "rects": rects})
            if W_:
                meta["attacks"].setdefault(P, {})[t] = {"windows": W_}
            tel, ev = [], {}
            for i, f in enumerate(a.frames):
                k = a.keys[f["key"]]
                if f["key"] > 0 and f["sub"] != k["n"]:
                    continue
                if k["per"].get("tel"):
                    at_ = infos[i]["head"] or infos[i]["hand"]
                    if k["per"]["tel"] == "tong":
                        at_ = infos[i]["tong"] or at_
                    if k["per"]["tel"] == "hand":
                        at_ = infos[i]["hand"]
                    if k["per"]["tel"] == "handf":
                        at_ = infos[i]["handf"]
                    tel.append({"frame": i, "at": at_})
                if k["per"].get("ev"):
                    for e in str(k["per"]["ev"]).split(","):
                        ev[e] = i
                if k["per"].get("pt"):
                    ev[k["per"]["pt"]] = i
            if tel:
                meta["telegraph"].setdefault(P, {})[t] = tel
            if ev:
                meta["events"].setdefault(P, {})[t] = ev
            meta["pts"].setdefault(P, {})[t] = [inf["head"] for inf in infos]
            meta["pts"].setdefault(P + "_hand", {})[t] = [inf["hand"] for inf in infos]
            if t in ("fgrabhold", "flame_grab"):
                meta["pts"].setdefault(P + "_handf", {})[t] = [inf["handf"] for inf in infos]
            if any(inf["tong"] for inf in infos):
                meta["pts"].setdefault(P + "_tong", {})[t] = [inf["tong"] for inf in infos]
            meta["body"].setdefault(P, {})[t] = [shrink(inf["body"]) for inf in infos]
            meta["dur"].setdefault(P, {})[t] = [int(round(d)) for d in durs]
            if any(inf["heat"] for inf in infos):
                meta["heat"].setdefault(P, {})[t] = [[v for q in inf["heat"] for v in q] for inf in infos]
            sx = round(a.keys[-1]["state"]["x"])
            if sx:
                meta["shift"].setdefault(P, {})[t] = sx
        if not tags_by_phase[ph]:
            continue
        groups = pack(list(cnt), cnt)
        names = [f"hearthkeeper_p{ph}_{gi + 1}" for gi in range(len(groups))]
        meta["sheets"][P] = {t: names[gi] for gi, grp in enumerate(groups) for t in grp}
        if not PREVIEW and ONLY is None:
            import asebuild
            for gi, grp in enumerate(groups):
                frames, tg = [], []
                for t in grp:
                    a = get_anim(t, ph)
                    tg.append((t, len(frames), len(frames) + cnt[t] - 1))
                    for (im, _), f in zip(built[(ph, t)], a.frames):
                        frames.append({"ms": max(16, int(round(f["dur"]))), "cels": {"body": im}})
                asebuild.build(names[gi], W, H, ["body"], frames, tg)
                print("sheet", names[gi], grp, len(frames), flush=True)
    # the global hurtbox: the idle body
    hb = meta["body"]["p1"].get("idle", [[60, 40, 34, 98]])[0] if "p1" in meta["body"] else [60, 40, 34, 98]
    meta["hurtbox"] = hb
    meta["notes"] = ("faces right; anchor = floor line. attacks.p<ph>.<tag>.windows[].rects keyed by frame index in the tag. "
                     "events.p<ph>.<tag>.<name> = frame index. pts = weapon head (hammer: striking face) per frame. "
                     "heat = hammer-head pixels [x,y,level,...] per frame (tempering glow). body = hurt rect per frame. "
                     "shift = root travel (px) applied when the tag ends.")
    if ONLY is None:
        with open(os.path.join(ART, "..", "assets", "hearthkeeper_meta.json"), "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
        hit_preview(built, meta)
        contact(built)
    for ph in (1, 2, 3):
        for t, d in meta["attacks"].get(f"p{ph}", {}).items():
            print(f"p{ph}", t, [w["active"] for w in d["windows"]], [w["hit"] for w in d["windows"]])
    return meta, built


BACK_OK = {"backhand", "ch_sweep"}


def shrink(b):
    if not b:
        return None
    return [b[0] + 2, b[1] + 1, max(4, b[2] - 4), max(4, b[3] - 2)]


def union(rs):
    rs = [r for r in rs if r]
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
    x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return [x0, y0, x1 - x0, y1 - y0]


def hit_preview(built, meta):
    rows = []
    for ph in (1, 2, 3):
        for t, d in meta["attacks"].get(f"p{ph}", {}).items():
            fr = built[(ph, t)]
            row = []
            for w in d["windows"]:
                for k, r in w["rects"].items():
                    k = int(k)
                    im = Image.new("RGBA", (W, H), (60, 62, 70, 255))
                    im.alpha_composite(fr[k][0])
                    im = im.resize((W * 2, H * 2), Image.NEAREST)
                    dr = ImageDraw.Draw(im)
                    dr.rectangle([r[0] * 2, r[1] * 2, (r[0] + r[2]) * 2, (r[1] + r[3]) * 2], outline=(255, 60, 60))
                    b = meta["body"][f"p{ph}"][t][k]
                    if b:
                        dr.rectangle([b[0] * 2, b[1] * 2, (b[0] + b[2]) * 2, (b[1] + b[3]) * 2], outline=(60, 255, 90))
                    dr.text((4, 4), f"p{ph} {t} {k}", fill=(230, 230, 230, 255))
                    row.append(im)
            rows.append(row)
    if not rows:
        return
    cols = max(len(r) for r in rows)
    sh = Image.new("RGBA", (cols * W * 2, len(rows) * H * 2), (30, 30, 34, 255))
    for y, r in enumerate(rows):
        for x, im in enumerate(r):
            sh.paste(im, (x * W * 2, y * H * 2))
    sh.save(os.path.join(PV, "hearthkeeper_hitbox.png"))


def contact(built):
    """Every tag, every frame, 1x, one row per tag (proportion drift check)."""
    keys = sorted(built, key=lambda k: (k[0], k[1]))
    cols = max(len(built[k]) for k in keys)
    sh = Image.new("RGBA", (cols * W + 120, len(keys) * H), (40, 42, 50, 255))
    d = ImageDraw.Draw(sh)
    for y, k in enumerate(keys):
        d.text((4, y * H + 4), f"p{k[0]} {k[1]}", fill=(220, 220, 230, 255))
        for x, (im, _) in enumerate(built[k]):
            sh.alpha_composite(im, (120 + x * W, y * H))
    sh.save(os.path.join(PV, "hearthkeeper_contact.png"))


if __name__ == "__main__" and "--props" not in sys.argv:
    main()


# ============================================================================ props: what he leaves on the floor
PW, PH, PAX, PAY = 72, 56, 36, 52


def build_props(write=True):
    """embedded hammer (cooling), the dropped blade / spear / chain (cooling, steam), the core (pulsing), the crown in
    the ash, the thrown spear (flying, for drawRotated)."""
    PF = PAY - 1
    frames, tags = [], []

    def canvas():
        return R.Canvas(PW, PH)

    def clip(cv):
        for d_ in (cv.px, cv.fx, cv.fxb):
            for q in [q for q in d_ if q[1] > PF]:
                del d_[q]

    def add(tag, ims, ms=160):
        tags.append((tag, len(frames), len(frames) + len(ims) - 1))
        for im in ims:
            frames.append({"ms": ms, "cels": {"body": im}})

    ims = []
    for h in (1.0, 0.75, 0.45, 0.2, 0.0):
        cv = canvas()
        R.draw_hammer(cv, (PAX, PF - 36), 90, below=6, above=34, heat=h, flip=1)
        if h > 0.3:
            R.halo(cv, {(x, PF) for x in range(PAX - 9, PAX + 10)}, "E3", 130)
        clip(cv); ims.append(cv.render(ref_y=30))
    add("hammer", ims, 400)
    for name, fn in (("blade", lambda cv, h: R.draw_blade(cv, (PAX - 24, PF - 3), -3, ln=44, curve=-2, heat=h)),
                     ("spear", lambda cv, h: R.draw_spear(cv, (PAX, PF - 2), -2, below=30, heat=h)),
                     ("chain", lambda cv, h: R.draw_chain(cv, (PAX - 28, PF - 2), (PAX + 24, PF - 4), bend=-3, heat=h, slack=2))):
        ims = []
        for k, h in enumerate((1.0, 0.7, 0.45, 0.25, 0.08)):
            cv = canvas()
            if h < 0.15:
                cv2 = canvas()
            fn(cv, max(0.05, h))
            if h < 0.5:          # cooling: the glow sinks, the steel shows; a thread of steam
                for q in list(cv.fx):
                    c = cv.fx[q]
                    if c[3] > 0 and (c[0] > 150) and R.hash01(q[0], q[1], k) > h * 1.6:
                        cv.fx.pop(q)
                        cv.flat([q], "I", 2 if R.hash01(q[0], q[1], 9) > 0.5 else 3)
            for i in range(6 - k):
                q = (PAX - 20 + R.hash01(i, k, 3) * 40, PF - 3 - R.hash01(i, k, 4) * 12 * (1 + k * 0.3))
                cv.glow([q], "Q3" if i % 2 else "Q4", 130)
            clip(cv); ims.append(cv.render(ref_y=30))
        add(name, ims, 500)
    # the core: a white coal caged in grate bars, breathing
    ims = []
    for k in range(4):
        cv = canvas()
        c = (PAX, PF - 12)
        r = 3.4 + 0.5 * math.sin(k * math.pi / 2)
        cv.glow(R.mask_disc(c, r), "E7")
        cv.glow(R.mask_disc(R.add(c, (0.5, 0.6)), r * 0.55), "E6")
        R.halo(cv, R.mask_disc(c, r), "E5", 220, behind=True)
        R.halo(cv, R.mask_disc(c, r + 1), "E3", 110, r=2, behind=True)
        for bx in (-6, -2.5, 2.5, 6):
            cv.flat(R.line(R.add(c, (bx, -6.5)), R.add(c, (bx * 0.85, 6.5))), "I", 4 if bx < 0 else 3)
        cv.flat(R.line((c[0] - 7, c[1] - 7), (c[0] + 7, c[1] - 7)), "I", 4)
        cv.flat(R.line((c[0] - 7, c[1] + 7), (c[0] + 7, c[1] + 7)), "I", 2)
        for i in range(3):
            q = R.add(c, ((R.hash01(i, k, 5) - 0.5) * 10, -9 - R.hash01(i, k, 6) * 6))
            cv.glow([q], "E5" if i % 2 else "E4", 190)
        clip(cv); ims.append(cv.render(ref_y=30))
    add("core", ims, 180)
    # the crown in the ash
    cv = canvas()
    ash = R.poly_mask([(PAX - 22, PF + 1), (PAX - 10, PF - 4), (PAX + 2, PF - 6), (PAX + 14, PF - 3), (PAX + 24, PF + 1)])
    cv.paint(R.n_plate(ash, bevel=2.0, tilt=(0, -0.3)), "K", bias=-1)
    rc = (PAX + 2, PF - 6)
    for a in range(0, 360, 10):
        cv.flat([R.ipt(R.add(rc, (math.cos(math.radians(a)) * 6, math.sin(math.radians(a)) * 1.6)))], "I", 3)
    for a, hgt in ((200, 5), (250, 6), (300, 7), (20, 7), (70, 9), (115, 8), (160, 6)):
        base = R.add(rc, (math.cos(math.radians(a)) * 6, math.sin(math.radians(a)) * 1.6))
        tip = R.add(base, (math.cos(math.radians(a)) * 2 + 3, -hgt * 0.6))
        cv.flat(R.line(base, tip), "I", 4 if 0 < a < 180 else 2)
    for i in range(4):
        cv.glow([(PAX - 14 + i * 9, PF - 2 - (i % 2))], "E3", 190)
    clip(cv)
    add("crown", [cv.render(ref_y=30)], 400)
    # the thrown spear, flying (horizontal, the point to the right; drawn rotated in the game)
    cv = canvas()
    R.draw_spear(cv, (PAX - 4, 28), 0, below=26, heat=1.0)
    add("spearfly", [cv.render(ref_y=30)], 400)
    if write and not PREVIEW:
        import asebuild
        asebuild.build("hearthkeeper_props", PW, PH, ["body"], frames, tags)
    sh = Image.new("RGBA", (len(frames) * PW * 3, PH * 3), (60, 62, 70, 255))
    for i, f in enumerate(frames):
        sh.alpha_composite(f["cels"]["body"].resize((PW * 3, PH * 3), Image.NEAREST), (i * PW * 3, 0))
    sh.save(os.path.join(PV, "hearthkeeper_props.png"))
    return tags


if __name__ == "__main__" and ONLY is None:
    build_props()
