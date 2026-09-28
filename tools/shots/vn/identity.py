#!/usr/bin/env python3
"""Gameplay identity check for the Venn restyle (agent VN).
    python3 tools/shots/vn/identity.py <before_assets_dir> <after_assets_dir>
Compares venn_boss_meta.json (every field except 'notes'), and for every venn_boss_*, fx_vn_*, npc_venn sheet:
image size, frame count, frame rects, per-frame durations and tags."""
import json, os, sys, glob
from PIL import Image
B, A = sys.argv[1], sys.argv[2]
bad = 0
mb = json.load(open(os.path.join(B, "venn_boss_meta.json")))
ma = json.load(open(os.path.join(A, "venn_boss_meta.json")))
keys = sorted(set(mb) | set(ma))
for k in keys:
    if k == "notes":
        continue
    same = mb.get(k) == ma.get(k)
    print(f"meta.{k:14s} {'IDENTICAL' if same else 'DIFFERENT'}")
    bad += not same
names = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(B, "*.json"))
               if os.path.basename(p).startswith(("venn_boss_p", "fx_vn_", "npc_venn")))
for n in names:
    jb = json.load(open(os.path.join(B, n + ".json"))); ja = json.load(open(os.path.join(A, n + ".json")))
    fb = [(f["frame"], f["duration"]) for f in jb["frames"]]; fa = [(f["frame"], f["duration"]) for f in ja["frames"]]
    tb = [(t["name"], t["from"], t["to"], t.get("direction")) for t in jb["meta"].get("frameTags", [])]
    ta = [(t["name"], t["from"], t["to"], t.get("direction")) for t in ja["meta"].get("frameTags", [])]
    sb = Image.open(os.path.join(B, n + ".png")).size; sa = Image.open(os.path.join(A, n + ".png")).size
    ok = fb == fa and tb == ta and sb == sa
    changed = Image.open(os.path.join(B, n + ".png")).convert("RGBA").tobytes() != Image.open(os.path.join(A, n + ".png")).convert("RGBA").tobytes()
    print(f"{n:18s} frames {len(fa):3d} size {sa[0]}x{sa[1]} tags {len(ta):2d}  {'OK' if ok else 'MISMATCH'}  pixels {'changed' if changed else 'UNCHANGED'}")
    bad += not ok
print("RESULT:", "ALL IDENTICAL" if bad == 0 else f"{bad} MISMATCHES")
sys.exit(1 if bad else 0)
