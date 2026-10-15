"""Write every weapon's in-game move list into docs/WEAPON_REVAMP.md (section A13, between the MOVELIST markers).

The lists come from the game itself (each type's `combos` in web/src/76_mech_*.js), so the doc matches the Esc mastery
screen's Move List exactly. Regenerate after changing moves:
  BUILD_OUT=web/dist/lead.html python3 web/build_web.py
  SHOT_HTML=web/dist/lead.html sh tools/shots/wm/run.sh tools/shots/lead/combos_dump.js /tmp/x > /tmp/combos.json
  python3 tools/movelist_doc.py /tmp/combos.json
"""
import json, re, sys

ROMAN = ['I', 'II', 'III', 'IV', 'V']
BEGIN, END = '<!-- MOVELIST:BEGIN -->', '<!-- MOVELIST:END -->'


def section(d):
    total = sum(len(v['combos']) for v in d.values())
    out = [BEGIN, '## A13. Move lists (every weapon, as in the game)', '',
           f'The full command list of each weapon, {total} moves in all, exactly as the in-game **Move List** shows it '
           '(Esc → weapon mastery → Enter, or the MOVE LIST button). **Rank** is the Weapon Mastery rank that unlocks the '
           'move (I = available from the start). Inputs: **J** light, **K** heavy, **I** block / parry / special, '
           '**L** roll / step, **↑ / ↓** held, **air** = while airborne, **hold** = keep the button down, '
           '**(pause)** = wait a beat before the last press, **→** = right after the previous move. '
           'This section is generated from the code by `tools/movelist_doc.py`; the tables in A2–A10 have the timings '
           'and numbers.', '']
    for t, v in d.items():
        cs = v['combos']
        base = sum(1 for c in cs if (c.get('rank') or 1) == 1)
        out += [f"### {v['name']} — {len(cs)} moves ({base} from the start)",
                f"*{v['weapon']}* · default art **{v['art']}** · mechanic: {v['mech']}", '',
                '| Rank | Move | Input | What it does |', '|---|---|---|---|']
        for c in cs:
            r = ROMAN[max(1, min(5, int(c.get('rank') or 1))) - 1]
            esc = lambda s: str(s or '–').replace('|', '\\|')
            out.append(f"| {r} | {esc(c['name'])} | {esc(c.get('input'))} | {esc(c.get('desc'))} |")
        out.append('')
    out.append(END)
    return '\n'.join(out)


def main(src, doc='docs/WEAPON_REVAMP.md'):
    d = json.load(open(src))
    s = open(doc).read()
    sec = section(d)
    if BEGIN in s:
        s = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda m: sec, s, flags=re.S)
    else:   # first time: just before Part B
        i = s.index('# Part B')
        j = s.rfind('---', 0, i)
        s = s[:j] + sec + '\n\n' + s[j:]
    if '  - A13. Move lists' not in s:
        s = s.replace('  - A12. Balance comparison\n', '  - A12. Balance comparison\n  - A13. Move lists (every weapon\'s full command list, as in the game)\n', 1)
    open(doc, 'w').write(s)
    print('wrote', doc, sum(len(v['combos']) for v in d.values()), 'moves')


if __name__ == '__main__':
    main(*sys.argv[1:])
