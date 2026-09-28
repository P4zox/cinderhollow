#!/usr/bin/env python3
"""Quick in-memory render of Venn boss tags (no Aseprite): python3 tools/shots/vn/quick.py out.png tag:phase[:frames] ...
frames = comma list of frame indices (default: 0). Crops around her, 5x, on two backgrounds (dark arena / mid grey)."""
import os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "art"))
sys.argv, argv = [sys.argv[0], "--preview"], sys.argv
import gen_venn as GV  # noqa
import venn_rig as R  # noqa
out = argv[1]
BOX = tuple(int(v) for v in os.environ.get("BOX", "40,16,160,126").split(","))
S = int(os.environ.get("S", 4))
cells = []
for spec in argv[2:]:
    parts = spec.split(":")
    tag, ph = parts[0], int(parts[1])
    ks = [int(k) for k in parts[2].split(",")] if len(parts) > 2 else [0]
    fr, _ = GV.build_tag(tag, ph)
    for k in ks:
        im = R.flatten(fr[k]["cels"]).crop(BOX)
        for bg in ((18, 16, 24, 255), (70, 70, 78, 255)):
            b = Image.new("RGBA", im.size, bg); b.alpha_composite(im)
            cells.append(b.resize((im.width * S, im.height * S), Image.NEAREST))
cols = min(len(cells), int(os.environ.get("COLS", 4)))
rows = (len(cells) + cols - 1) // cols
w, h = cells[0].size
sh = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 255))
for i, c in enumerate(cells):
    sh.paste(c, ((i % cols) * w, (i // cols) * h))
sh.save(out)
print(out)
