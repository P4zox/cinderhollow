"""WA1 timing table: every WA1 v13 tag (wind-up / total at speed 1 vs WEAPON_REVAMP.md) and the existing tags the tables reuse,
with the playback speed WM would need to hit the table's total.   python3 tools/shots/wa1/timing.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "art"))
import gen_player as G

FN = dict(G.ANIMS)
REUSE = [("ls J", "attack1", 160, 380), ("ls JJ", "attack2", 160, 380), ("ls JJJ poke", "attack3", 200, 420),
         ("ls JJJJ crit (attack4)", "riposte", 300, 650), ("ls K", "heavy", 380, 700), ("ls riposte", "riposte", 250, 600),
         ("ls air J", "air_attack", 150, 330), ("ls air up", "attack_up", 160, 360), ("ls air down", "attack_down", 100, 300),
         ("kt J", "kt_1", 120, 330), ("kt JJ", "kt_2", 120, 330), ("kt K drawn (rushing draw)", "kt_heavy", 260, 620),
         ("kt air J", "kt_air", 140, 330), ("kt air up", "kt_up", 160, 360), ("kt air down", "kt_down", 100, 280),
         ("gs J", "gs_1", 300, 700), ("gs JJ", "gs_2", 300, 700), ("gs JJJ", "gs_3", 320, 760),
         ("gs air J", "gs_air", 220, 560), ("gs air up", "gs_up", 240, 560), ("gs air down", "gs_down", 140, 390),
         ("ml air J (gs_air)", "gs_air", 200, 520), ("ml air up (gs_up)", "gs_up", 220, 520), ("ml air down (gs_down)", "gs_down", 140, 380),
         ("sh J", "sh_1", 120, 320), ("sh JJ", "sh_2", 120, 320), ("sh JJJ", "sh_3", 140, 340), ("sh K", "sh_heavy", 200, 520),
         ("sh I->J counter", "sh_counter", 200, 520), ("sh air J", "sh_air", 120, 300), ("sh air up", "sh_up", 150, 340),
         ("sh air down", "sh_down", 100, 300)]


def wt(tag):
    ms = [m for _, m in FN[tag]()]
    a = G.ACTIVE.get(tag) or {"riposte": (3, 4)}.get(tag)
    return (sum(ms[:a[0]]) if a else None), sum(ms), len(ms)


print("== new WA1 tags (speed 1) ==")
print(f"{'tag':18} {'frames':>6} {'wind':>5} {'total':>6} {'table':>10}  check")
bad = 0
for e in G._v13a.register(G):
    t = e[0]
    w, tot, n = wt(t)
    sp = G._v13a.SPEC.get(t)
    ok = "loop/stance" if not sp else ("OK" if (w, tot) == sp else "MISMATCH")
    bad += ok == "MISMATCH"
    print(f"{t:18} {n:6} {w if w is not None else '-':>5} {tot:6} {('%d/%d' % sp) if sp else '':>10}  {ok}")
print("== existing tags the tables reuse (for WM: speed = tag total / table total) ==")
for lab, t, tw, tt in REUSE:
    w, tot, n = wt(t)
    print(f"{lab:26} {t:12} tag {w:4}/{tot:<5} table {tw:4}/{tt:<5} speed x{tot / tt:.2f} -> wind {w * tt / tot:.0f}")
print("mismatches:", bad)
sys.exit(1 if bad else 0)
