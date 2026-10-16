"""Write docs/BOSS_CORES.md: every boss Core as the game defines it (web/src/77_cores.js CORES).

  BUILD_OUT=web/dist/lead.html python3 web/build_web.py
  SHOT_HTML=web/dist/lead.html sh tools/shots/wm/run.sh tools/shots/lead/cores_dump.js /tmp/x > /tmp/cores.json
  python3 tools/cores_doc.py /tmp/cores.json
Boss names, colour words, bench gains and the flavour line come from the trait table in docs/v15/cores.md.
"""
import json, re, sys

CAT = {  # how each Core plays, for the overview
    'Bonus strikes': ['hound', 'omen', 'librarian', 'bellringer', 'cindervane', 'pharaoh', 'astrel', 'sentinels', 'first_ember'],
    'Damage over time': ['coven', 'vessel', 'twins', 'overseer'],
    'Raw power and stance': ['warden', 'choir', 'champion', 'executioners', 'colossus', 'orrery', 'sovereign', 'hearthkeeper', 'venn'],
    'Control': ['ice_warden', 'enforcer', 'unwritten'],
    'Defence': ['kalden', 'scarab', 'saint0'],
    'Sustain and tempo': ['oswin', 'ferryman', 'butler', 'sanguine', 'vael'],
}


def table_rows(md):
    rows = {}
    for l in md.split('\n'):
        if not l.startswith('| ') or l.startswith('| Boss') or l.startswith('|---'):
            continue
        c = [x.strip() for x in l.strip('|').split('|')]
        if len(c) < 7:
            continue
        m = re.search(r'\(([a-z_0-9]+)\)', c[0])
        key = m.group(1) if m else None
        rows[key or c[1]] = dict(boss=re.sub(r'\s*\([a-z_0-9]+\)', '', c[0]), core=c[1], colour=c[2], bench=c[5], why=c[6])
    return rows


def main(src, out='docs/BOSS_CORES.md'):
    d = json.load(open(src))
    cost, cin, xp = d.pop('_cost'), d.pop('_cin'), d.pop('_xp')
    rows = table_rows(open('docs/v15/cores.md').read())
    def info(k, c):
        r = rows.get(k) or next((v for v in rows.values() if v['core'].replace("'", '’') == c['name']), {})
        return r
    order = sorted(d, key=lambda k: (d[k]['stage'] if d[k]['stage'] is not None else 99, k))
    L = ['# Cinderhollow — Boss Cores', '',
         f'Every boss drops its **Core** on the first kill — {len(d)} in all. Socket one into a weapon at the **Ashwright**',
         f'("Enchant a weapon", **{cost} cinders**; removing it is free and gives the Core back). Each of the 14 weapon types keeps',
         'its own Core, and a Core sits in one weapon at a time.', '',
         '**What an enchant touches:** only **finishers, heavy attacks, counters and charged releases** — never light attacks,',
         'weapon arts or plunges. Those "enchanted moves" glow in the Core\'s colour on every weapon. The bonus is modest by',
         'design: +3–14% on the enchanted moves themselves, about +5% of your total damage at most (boss weapons used to be',
         'far stronger). Control effects are weaker on bosses (40% strength for half the time, less with each repeat), and no',
         'effect stacks with itself.', '',
         f'**Rekindle:** a cleared arena keeps an ember effigy that revives its boss for a rematch, as often as you like (not',
         f'Sister Venn). A rematch win gives +{xp} Weapon Mastery and {int(cin * 100)}% of the boss\'s cinders; dying in one costs',
         'nothing. New Game+ keeps your Cores and enchants and never drops a duplicate.', '',
         '*Generated from the game\'s own Core table (`web/src/77_cores.js`) by `tools/cores_doc.py`; reasoning, budget gates',
         'and tests: `docs/v15/cores.md`.*', '',
         '## Contents', '1. [At a glance](#at-a-glance)', '2. [Every Core, in journey order](#every-core-in-journey-order)',
         '3. [Picking a Core](#picking-a-core)', '', '## At a glance', '']
    for cat, keys in CAT.items():
        names = ', '.join(f"{d[k]['name']} (*{d[k]['trait']}*)" for k in keys if k in d)
        L.append(f'- **{cat}:** {names}')
    L += ['', '| Boss | Core | Trait | Colour | Gain on enchanted moves |', '|---|---|---|---|---|']
    for k in order:
        c, r = d[k], info(k, d[k])
        col = c['col'] + (f" / {c['col2']}" if c['col2'] else '')
        L.append(f"| {r.get('boss', k)} | {c['name']} | {c['trait']} | {r.get('colour', '')} `{col}` | {r.get('bench', '')} |")
    L += ['', '## Every Core, in journey order', '']
    for k in order:
        c, r = d[k], info(k, d[k])
        cat = next((n for n, ks in CAT.items() if k in ks), '')
        L += [f"### {c['name']} — *{c['trait']}*",
              f"**Boss:** {r.get('boss', k)} · **Colour:** {r.get('colour', '')} (`{c['col']}`{' / `' + c['col2'] + '`' if c['col2'] else ''}) · "
              f"**Type:** {cat}{'' if c['rematch'] else ' · *cannot be rekindled*'}", '',
              f"{c['desc']}", '']
        if r.get('why'):
            L += [f"*{r['why'][0].upper() + r['why'][1:]}.*", '']
    L += ['## Picking a Core', '',
          '- **Combo weapons with many finishers** (Longsword, Dual Blades, Martial Arts, Sword & Shield) get the most from',
          '  per-move procs: *Rend*, *Twin Oath*, *Resonance*, *Starfall*.',
          '- **Big single hits** (Greatsword, Maul, Katana Iai, Switch Axe) suit flat and delayed bonuses: *Omen Line*,',
          '  *Dusk Count*, *Kindling*, *Molten Crack*, *Antler\'s Weight* for stance.',
          '- **Crowds:** *Toll*, *Stormcall*, *Orbit*. **Bosses:** *Molten Crack*, *Verdict*, *Kneel*, *Unyielding*.',
          '- **Surviving:** *Unbroken Oath*, *Sun Shell*, *Blood Tithe*, *Redaction*, *Nullify* (projectile-heavy fights).',
          '- **Stamina and FP:** *Toll of Breath*, *Wayfarer\'s Wind*, *Grief\'s Due* (weapon arts), *Attentive* for tempo.',
          '- Bow arrows carry the procs and the colour but not the flat damage bonuses, so procs suit the Bow best.', '']
    open(out, 'w').write('\n'.join(L))
    print('wrote', out, len(d), 'cores')


if __name__ == '__main__':
    main(*sys.argv[1:])
