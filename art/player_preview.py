"""Fast contact sheets of player tags without rebuilding the sheets (WA's review tool).

  python3 art/player_preview.py rows  out.png  tag:kind,kind  tag:kind ...   # one row per (tag, kind)
  python3 art/player_preview.py dirs  out_prefix                              # every class x up/air/down (+ sword)
  python3 art/player_preview.py class <cls> out.png                           # every tag of one class, 2 weapons

Each row: label, frames at 3x on a mid-grey cell, per-frame ms, active frames ticked gold, and (with HB=1) the
meta damage box of the active frames outlined in red (feet-relative, as write_meta computes it).
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_player as G

W, H = G.W, G.H
_FN = dict(G.ANIMS)
_CACHE = {}


def frames(tag):
    if tag not in _CACHE:
        _CACHE[tag] = list(_FN[tag]())
    return _CACHE[tag]


def render(tag, kind):
    out = []
    for cels, ms in frames(tag):
        body = G.compose(G.imgs(cels, None))
        w = G.imgs(cels, kind).get("Sword") if kind else None
        out.append((G.over(body, w), ms, cels))
    return out


def hitbox(tag, kind):
    """write_meta's box for this tag with weapon `kind` (frame coords), or None."""
    if tag not in G.ACTIVE:
        return None
    raw = frames(tag)
    tags = [(tag, 0, len(raw) - 1)]
    saved = dict(G.MOVE_CLASS)
    pre = tag.split("_")[0]
    try:
        if pre in G.MOVE_CLASS:
            G.MOVE_CLASS[pre] = (kind,)
        m = G.meta_for(raw, tags)
    finally:
        G.MOVE_CLASS.clear(); G.MOVE_CLASS.update(saved)
    mv = m.get(tag)
    if not mv:
        return None
    x0, y0, x1, y1 = mv["hit"]
    return (x0 + 28, y0 + 40, x1 + 28, y1 + 40), mv["active"]


def sheet(rows, out, scale=3, show_hb=None):
    """rows: [(label, sublabel, tag, kind)]"""
    show_hb = os.environ.get("HB") == "1" if show_hb is None else show_hb
    lw = 38
    data = []
    for lab, sub, tag, kind in rows:
        fr = render(tag, kind)
        hb = hitbox(tag, kind) if show_hb else None
        data.append((lab, sub, tag, fr, hb))
    cols = max(len(d[3]) for d in data)
    # hitboxes may poke out of the 64x40 frame (up/down extensions): pad each cell
    PX, PY = (8, 22) if show_hb else (0, 0)
    cw, ch = W + 2 * PX + 1, H + 2 * PY + 1
    img = Image.new("RGBA", (lw + cols * cw, len(data) * ch), (92, 92, 100, 255))
    for ry, (lab, sub, tag, fr, hb) in enumerate(data):
        act = G.ACTIVE.get(tag, (0, -1))
        for i, (im, ms, _) in enumerate(fr):
            cell = Image.new("RGBA", (W + 2 * PX, H + 2 * PY), (58, 58, 66, 255))
            cell.alpha_composite(im, (PX, PY))
            d = ImageDraw.Draw(cell)
            d.line([(PX, PY + H - 1), (PX + W - 1, PY + H - 1)], fill=(80, 80, 90, 255))
            if act[0] <= i <= act[1]:
                d.line([(PX, PY + H + (PY and 1) - 1), (PX + 7, PY + H + (PY and 1) - 1)], fill=(255, 196, 90, 255))
                if hb:
                    (x0, y0, x1, y1), _ = hb
                    d.rectangle([x0 + PX, y0 + PY, x1 + PX - 1, y1 + PY - 1], outline=(255, 60, 60, 255))
            img.alpha_composite(cell, (lw + i * cw, ry * ch))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for ry, (lab, sub, tag, fr, hb) in enumerate(data):
        y = ry * ch * scale
        d.text((4, y + 4), lab, fill=(255, 255, 255, 255))
        d.text((4, y + 18), sub[:14], fill=(200, 200, 210, 255))
        d.text((4, y + 32), f"{sum(f[1] for f in fr)}ms", fill=(200, 200, 210, 255))
        for i, f in enumerate(fr):
            d.text(((lw + i * cw) * scale + 3, y + 3), f"{i}:{f[1]}", fill=(255, 220, 150, 255))
    img.save(out)
    print(out, img.size)


CLS = [("sword", "attack", ("longsword", "oathbrand")), ("dg", "dagger", ("dagger", "carving_knife")),
       ("gs", "great", ("greatsword", "colossus_hammer")), ("sp", "spear", ("spear", "saint_lance")),
       ("kt", "katana", ("katana", "plasma_katana")), ("st", "staff", ("quarterstaff", "lantern_staff")),
       ("sh", "shield", ("knight_shield", "overseer_bulwark")), ("tw", "twin", ("twinfangs",)),
       ("sc", "scythe", ("briar_scythe", "last_kindling")), ("wh", "whip", ("gravechain", "orrery_whip"))]
SWORD_DIR = {"up": "attack_up", "air": "air_attack", "down": "attack_down"}


def dir_tag(pre, d):
    if pre == "sword":
        return SWORD_DIR[d]
    t = f"{pre}_{d}"
    return t if t in _FN else SWORD_DIR[d]


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode in ("rows", "zoom"):
        if mode == "zoom":
            rows = []
            for spec in sys.argv[3:]:
                tag, kinds = spec.split(":")
                for k in kinds.split(","):
                    rows.append((tag, k, tag, k))
            sheet(rows, sys.argv[2], scale=int(os.environ.get("SC", "6")))
            sys.exit(0)
        rows = []
        for spec in sys.argv[3:]:
            tag, kinds = spec.split(":")
            for k in kinds.split(","):
                rows.append((tag, k, tag, k))
        sheet(rows, sys.argv[2])
    elif mode == "dirs":
        pre_out = sys.argv[2]
        which = sys.argv[3].split(",") if len(sys.argv) > 3 else ["up", "air", "down"]
        for d in which:
            rows = [(f"{c}_{d}", k, dir_tag(p, d), k) for p, c, ks in CLS for k in ks[:1]]
            sheet(rows, f"{pre_out}_{d}.png")
    elif mode == "class":
        pre, out = sys.argv[2], sys.argv[3]
        ks = next(k for p, c, k in CLS if p == pre)
        tags = [t for t, _ in G.ANIMS if t.startswith(pre + "_")] if pre != "sword" else \
            ["attack1", "attack2", "attack3", "heavy", "attack_up", "air_attack", "attack_down", "riposte"]
        rows = [(t, k, t, k) for t in tags for k in ks]
        sheet(rows, out)
