# v16 Fatalities — the agile group (agent `fagile`)

Dual Blades **Crimson Requiem**, Staff **Tempest Ascension**, Whip **Thunder Leash**, Martial Arts **Hundred Embers**.

Files: `web/src/79e_fatal_agile.js` (the four registrations + their custom drawing), `art/player_v16_fatal_agile.py`
(four tags: `tw_fatal` 1600 ms, `st_fatal` 1700, `wh_fatal` 1700, `ft_fatal` 1700; each tag's total = the def's `dur`, so
its frame ms are the choreography), tests in `tools/shots/v16/fagile/`. No shared file was edited; no framework change.

## The four fatalities

### Dual Blades — "Crimson Requiem" (1600 ms, crimson `235,70,80`)
Coil low with both blades crossed back (a crimson breath on the knight), a lunge that blurs out of sight — and the
knight is **gone** (240–760 ms: the tag holds a blank frame). In his place, **eight crimson phantoms** of him (real
dual-blade frames from `tw_heavy` / `tw_crossfall` / `tw_skyward` / `tw_4`, drawn as glowing silhouettes with two
echoes) strike through the foe from every angle — front, behind-high, below, behind, above, behind-low, then a
scissor pair — each leaving a hot cut of light that cools into a dark-red scar, inside a wheel of crimson arcs. The
phantoms stream back together above the foe and he **reappears** tucked in the air (flash), hangs with both blades
raised and crossed, then dives down its front and opens them in an **X**: a crimson cross is cut into the air, hangs
**burning** (flickering bars, licks of flame, shedding embers) for ~1 s, then breaks into falling fragments.
Beats: 0.4 / 0.4 / 0.4 on three phantoms (small hitstops), **3.8 on the X** (slow-mo, boom, name).

### Staff — "Tempest Ascension" (1700 ms, wind jade `190,235,215`)
Plant the staff ahead and **vault** onto the foe feet-first (a kick at its top), ride it up into **four turns in the
air** with the staff level at the waist — each turn throws a flat **wind ring**, wind streaks spiral round the knight
and a small foe is carried up with him — hang with the staff overhead while the wind gathers into it, flip it
point-down and **plunge** it into the floor: a **vortex** (a funnel of nine wheeling rings, widening upward, dust
riding the spiral) tears up out of the stone and rises away, grit thrown along the floor, flat shock rings.
Beats: 0.6 (vault kick), 0.5, 0.5 (spins), **3.4 on the plunge**.

### Whip — "Thunder Leash" (1700 ms, storm blue `150,195,255`)
Coil, then fling the chain: it flies at the foe's **neck** and the hook whips round it (two coils drawn on the front
of the neck, the hook hanging off them). Lean back and **yank** it taut (the chain quivers; a small foe is dragged
in). One full **turn** with the slack whirled round the waist — a small foe is swung **once round the knight** on the
chain, over his head and back to the front — static crawling on the links. Plant with the arm high (the hand
crackles), then the **crack**: thunder races down the chain from the hand to the neck, a **bolt** drops on the foe from
above the view with forks over its body, and little arcs keep **crawling** over it for 1.3 s. The chain glows, cools,
drops off the neck slack and is gathered back in. The chain past the handle is drawn in-engine (the sprite carries a
stub), from a per-frame hand table (`WH_FR`) kept in step with `wh_fatal`.
Beats: 0.5 (the wrap), 0.8 (the yank), **3.7 on the crack**.

### Martial Arts — "Hundred Embers" (1700 ms, ember `255,125,60`)
A **Swift palm flurry**: eight blows, near / far fists (both knuckles show via the twin-knuckle overlay), each with
two phantom fists between them — a pale steel-blue blur of dash lines and impact stars walking up and down the foe.
At 600 ms the feet **root mid-flurry and the style turns to Iron** (`ftSetStyle('iron')`: the style-change flash,
the knuckles' heat light): a rooted palm, then three heavy ember blows. Sink with both hands at the hip as the wraps
take fire (embers drawn in, cracks at the feet), and drive **both palms out as one**: a **pressure wave passes through
the foe and out of its back** (three travelling rings, sparks and embers blasting from its far side), and a **palm
print** is left burned on it — white-hot, ember, red, cooling from the middle, then crumbling to ash flakes (~2.3 s,
it follows a knocked-back foe). Beats: 0.35 / 0.35 (Swift), 0.7 (Iron), **3.6 on the Ember palm**.
The fatality ends in the Iron style (I switches back, as after a Shift strike).

## Notes
- Every effect is 1-px pixel art into the glow layer; all lights k ≤ 0.8 (most 0.3–0.6), one big light per effect.
- Seeded randomness only (`fatRng` / `fatHash`): the effects look the same in the deterministic test harness.
- Small foes only are moved (framework rule): the staff lifts / drops it, the whip drags it in, swings it round and
  slams it down (via `F.tm`, the framework's target motion), the palm knocks it back. Bosses never move.
- Boss damage on the Dual reads 4.95 × AR in the low-AR test kit: the boss rounds each blow to an integer and the Dual
  has three small beats (10.4 → 10). Real builds lose < 1%.

## Tests (`tools/shots/v16/fagile/`, HTML `web/dist/v16_fagile.html`)
`tests.js` (result `tests_result.txt`, **allPass: true**). For each of the four types, K is pressed with a real input
on a staggered boss in **5 real arenas**: hound, omen, twins (multi-body), executioners (multi-body) and bellringer.
Each fatality also runs on a tough hollow soldier and a weak one. Every frame is rendered, so all the draw code runs.
- Bosses: 5.01 × AR (Dual 4.95, from integer rounding, see above). The player can't be hurt mid-fatality
  (`hurtPlayer(9999)` + spikes are refused, HP unchanged). On twins / executioners the other body stays put the whole
  time. The boss is released and ends `idle`, and its stagger ends 23–34 frames later.
- Regular foes: 8.0 × AR on the tough one; the weak one is executed. The fatality ends `idle`, and a small foe that was
  moved is back on the ground and no longer held.
- No console errors in any run.
Snapshots: `mksnaps.sh <type> <room> <boss> <x> <y> <at-list>` wraps `../fatality/snaps.js` + `sheet.py` and writes
`<type>_boss_sheet.png` and `<type>_foe_sheet.png`. The boss sheets use: dual in the Omen arena, staff with the hound,
whip with the twins, fist with the bellringer. The snapshot labels run a little behind the game clock (the page keeps
rendering while a PNG is saved).
