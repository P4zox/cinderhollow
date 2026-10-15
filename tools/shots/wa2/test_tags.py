"""WA2 self-test: every v13 tag of player_v13_b renders on its weapon, its timing matches docs/WEAPON_REVAMP.md Part A
(total ms, wind-up = ms before the first active frame), loops close seamlessly, and meta_for writes a box for each attack.

    python3 tools/shots/wa2/test_tags.py
"""
import os, sys
from PIL import ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "art"))
import gen_player as G
import player_v13_b as B

KIND = {"tw": "twinfangs", "sp": "spear", "st": "quarterstaff", "wh": "headsman_chain"}
FN = dict(G.ANIMS)


def diff(a, b):
    d = ImageChops.difference(a, b).convert("L")
    return sum(1 for v in d.getdata() if v > 8)


fails = []
rows = []
for tag, (wind, total, act, typ) in B.TIMING.items():
    kind = KIND[tag[:2]]
    if tag not in FN:
        fails.append(f"{tag}: not in ANIMS")
        continue
    fr = list(FN[tag]())
    ms = [m for _, m in fr]
    imgs = []
    for cels, _ in fr:
        w = G.imgs(cels, kind).get("Sword")
        if w is None or not w.getbbox():
            fails.append(f"{tag}: frame without a {kind} cel")
        imgs.append(G.over(G.compose(G.imgs(cels, None)), w))
    tot = sum(ms)
    wu = sum(ms[:act[0]]) if act else None
    ok = tot == total and (wind is None or wu == wind) and (act is None or act[1] < len(fr))
    note = ""
    if typ == "loop" and len(imgs) > 2:   # seam: last -> first must be no bigger a jump than the frames inside the loop
        inner = max(diff(a, b) for a, b in zip(imgs, imgs[1:]))
        seam = diff(imgs[-1], imgs[0])
        note = f"seam {seam}px / max step {inner}px"
        if seam > inner * 1.15:
            ok = False
            note += " SEAM JUMP"
    meta = ""
    if act:
        m = G.meta_for([(c, x) for c, x in fr], [(tag, 0, len(fr) - 1)]).get(tag)
        if not m:
            ok = False
            meta = "NO META"
        else:
            meta = f"hit {m['hit']}" + (f" hits {m['hits']}" if "hits" in m else "")
    if not ok:
        fails.append(f"{tag}: total {tot} (want {total}) wind-up {wu} (want {wind}) {note}")
    rows.append((tag, kind, len(fr), wu, wind, tot, total, act, typ, "ok" if ok else "FAIL", note or meta))

print(f"{'tag':18} {'weapon':15} {'fr':>3} {'wind':>11} {'total':>11} {'active':>8} {'type':6} {'':4} meta / loop")
for tag, kind, n, wu, wind, tot, total, act, typ, st, extra in rows:
    w = f"{wu if wu is not None else '-'}/{wind if wind is not None else '-'}"
    t = f"{tot}/{total}"
    print(f"{tag:18} {kind:15} {n:>3} {w:>11} {t:>11} {str(act or '-'):>8} {typ:6} {st:4} {extra}")
print(f"\n{len(rows)} tags, {len(fails)} failures")
for f in fails:
    print("FAIL", f)
sys.exit(1 if fails else 0)
