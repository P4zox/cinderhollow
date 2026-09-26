"""Driver shared by the Necropolis creature generators (agent N): renders pose lists through necro_rig.draw_body,
collects hit pixels, writes sheet + meta + previews through enemy_kit.export (Aseprite)."""
import json, math, os, sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ART)
import enemy_kit as K  # noqa: E402
import necro_rig as NR  # noqa: E402
from enemy_kit import Layer, bbox  # noqa: E402

BUILD = "--preview" not in sys.argv
ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))


def render(outfit, anims, s, ox, floor, loops=("idle", "walk"), post=None, extra=None):
    """anims: [(tag, [(ms, pose), ...])]; poses in unit-human coords. Returns (anims_out, infos)."""
    out, infos = [], {}
    for tag, frames in anims:
        drv = [f[1]["C"][0] for f in frames]
        sway = K.spring(drv, loop=tag in loops, extra=[f[1].get("wind", 0.0) for f in frames])
        lst, inf = [], []
        for k, (ms, pose) in enumerate(frames):
            q = NR.scaled(pose, s, ox, 0, floor)
            q["lift"] = pose.get("lift", 0.0) * s
            Ls, info = NR.draw_body(q, k, sway[k], outfit)
            if extra:
                extra(Ls, info, q, k, tag)
            imgs = {}
            for n in NR.LAYERS:
                v = Ls.get(n)
                if v is None:
                    continue
                imgs[n] = K.render_layer(v) if isinstance(v, Layer) else v.image()
            if pose.get("post"):
                imgs = pose["post"](imgs)
            if post:
                imgs = post(imgs, tag, k)
            info["pose"] = q
            lst.append((ms, imgs))
            inf.append(info)
        out.append((tag, lst))
        infos[tag] = inf
    return out, infos


def hit_rect(infos, tag, ks, floor=True, x_min=None, pad=0, use_blade=True):
    pts = set()
    for k in ks:
        pts |= infos[tag][k].get("hit", set())
        if use_blade:
            pts |= infos[tag][k].get("blade", set()) or set()
    pts = {p for p in pts if K.inb(*p)}
    r = bbox(pts, pad)
    if r is None:
        return None
    if x_min is not None and r[0] < x_min:
        r[2] -= x_min - r[0]
        r[0] = x_min
    if floor:
        r[3] = K.H - r[1]
    return r


def hurtbox(anims, names, inset=(1, 0, 1), floor=True, frame=0, tag=0):
    imgs = anims[tag][1][frame][1]
    x0, y0, x1, y1 = K.opaque_bbox(imgs, names)
    return [x0 + inset[0], y0 + inset[1], (x1 - x0) - inset[0] - inset[2], (K.H if floor else y1) - (y0 + inset[1])]


def pt(p):
    return [int(round(p[0])), int(round(p[1]))]


def export(name, anims, meta, flat_order=None):
    tags, flats = K.export(name, NR.LAYERS, anims, meta, build=BUILD, flat_order=flat_order)
    return tags, flats


def closeup(name, anims, picks, scale=6, bg=(70, 70, 82, 255)):
    """A few chosen frames side by side, big (for eyeballing proportions)."""
    ims = []
    for tag, k in picks:
        fr = dict(anims)[tag][k][1]
        flat = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
        for n in NR.LAYERS:
            if n in fr:
                flat.alpha_composite(fr[n])
        ims.append(flat)
    sheet = Image.new("RGBA", (len(ims) * (K.W + 2) * scale, K.H * scale), bg)
    for i, im in enumerate(ims):
        sheet.alpha_composite(im.resize((K.W * scale, K.H * scale), Image.NEAREST), (i * (K.W + 2) * scale, 0))
    sheet.save(os.path.join(ART, "previews", f"{name}_closeup.png"))


def collapse(names, sq, burn=0.0, seed=0, spread=0.25, cx=None, pal=("U5", "U4", "U3", "U2", "U1")):
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


BODY = ["Cape", "WeaponBack", "BackArm", "BackLeg", "Body", "FrontLeg", "Head", "Weapon", "FrontArm"]
