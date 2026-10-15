"""WA1 contact sheets: every v13 WA1 tag on its weapon, 3x (HB=1 outlines the meta hit box on active frames).
   python3 tools/shots/wa1/sheets.py <outdir> [prefix ...]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "art"))
import player_preview as PP
import gen_player as G

KIND = {"ls": "longsword", "kt": "katana", "gs": "greatsword", "ml": "maul", "sh": "knight_shield"}
out = sys.argv[1]
pres = sys.argv[2:] or list(KIND)
os.makedirs(out, exist_ok=True)
tags = [e[0] for e in G._v13a.register(G)]
for p in pres:
    rows = [(t, KIND[p], t, KIND[p]) for t in tags if t.startswith(p + "_")]
    PP.sheet(rows, os.path.join(out, f"wa1_{p}.png"))
