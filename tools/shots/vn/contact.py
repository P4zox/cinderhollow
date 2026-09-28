#!/usr/bin/env python3
"""Before/after contact sheets for Sister Venn (agent VN).

    python3 tools/shots/vn/contact.py <before_assets_dir> <after_assets_dir> <outdir>

For every phase/tag of venn_boss_meta.json: a row pair (before on top, after below), frames sampled (<= 10),
cropped around her and scaled 2x on a dark arena grey. Plus an idle close-up per phase (6x) and the NPC sheet.
"""
import json, os, sys
from PIL import Image, ImageDraw

B, A, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
BG = (22, 20, 28, 255)


def load(d, name):
    im = Image.open(os.path.join(d, name + ".png")).convert("RGBA")
    js = json.load(open(os.path.join(d, name + ".json")))
    tags = {t["name"]: (t["from"], t["to"]) for t in js["meta"]["frameTags"]}
    fr = [f["frame"] for f in js["frames"]]
    return im, tags, fr


def frame(d, sheet, tag, k, box):
    im, tags, fr = load(d, sheet)
    a, b = tags[tag]
    f = fr[a + k]
    c = im.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).crop(box)
    bg = Image.new("RGBA", c.size, BG)
    bg.alpha_composite(c)
    return bg


meta = json.load(open(os.path.join(A, "venn_boss_meta.json")))
BOX = (20, 8, 180, 126)
S = 2
for ph in ("p1", "p2", "p3"):
    rows = []
    for tag, sheet in sorted(meta["sheets"][ph].items()):
        _, tags, _ = load(A, sheet)
        a, b = tags[tag]
        n = b - a + 1
        ks = sorted(set(round(i * (n - 1) / max(1, min(10, n) - 1)) for i in range(min(10, n))))
        for d in (B, A):
            rows.append((f"{ph} {tag} {'before' if d == B else 'after'} ({n}f)", [frame(d, sheet, tag, k, BOX) for k in ks]))
    w = (BOX[2] - BOX[0]) * S
    h = (BOX[3] - BOX[1]) * S
    sheet_im = Image.new("RGBA", (10 * w, len(rows) * (h + 12)), (10, 10, 12, 255))
    dr = ImageDraw.Draw(sheet_im)
    for r, (lab, ims) in enumerate(rows):
        y = r * (h + 12)
        dr.text((4, y), lab, fill=(220, 220, 220, 255))
        for i, im in enumerate(ims):
            sheet_im.paste(im.resize((w, h), Image.NEAREST), (i * w, y + 12))
    # split into chunks of 8 rows so each image stays readable
    per = 8
    for c in range(0, len(rows), per):
        part = sheet_im.crop((0, c * (h + 12), 10 * w, min(len(rows), c + per) * (h + 12)))
        part.save(os.path.join(OUT, f"venn_{ph}_{c // per:02d}.png"))
    # close-up of idle frame 0
    cb = (46, 30, 150, 124)
    ims = [frame(d, meta["sheets"][ph]["idle"], "idle", 0, cb).resize(((cb[2] - cb[0]) * 4, (cb[3] - cb[1]) * 4), Image.NEAREST)
           for d in (B, A)]
    cu = Image.new("RGBA", (ims[0].width * 2 + 8, ims[0].height), (0, 0, 0, 255))
    cu.paste(ims[0], (0, 0)); cu.paste(ims[1], (ims[0].width + 8, 0))
    cu.save(os.path.join(OUT, f"venn_{ph}_idle_closeup.png"))
print("ok", OUT)
