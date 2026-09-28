# Cinderhollow — Weapon feel pass: contract (read fully before touching anything)

## What the user asked for, and the rule behind every decision
The user wants weapons to be about **look and motion first, effects second**:
- **Look and motion:** animation, silhouette, arcs, trails, sound and impact.
- **Effects:** extra projectiles, procs, healing and damage over time. Some boss weapons "broke the game."

What this pass must deliver:
- Nerf the special effects on all weapons.
- Balance the weapons against each other.
- Make every class's attacks look great in every direction, including airborne.
- **Each weapon has exactly one art, its own, and it can't be changed.**

When in doubt: *make it prettier, make it do less.* A signature should read as that boss's power through visuals and sound. It should not act as a second weapon.

Read these before starting:
- `docs/EXPANSION_CONTRACT.md` §0: per-agent builds, test harness, the Aseprite pipeline, the taste rules.
- `docs/EXPANSION3_CONTRACT.md` §0.

In short:
- Build to `BUILD_OUT=web/dist/<you>.html python3 web/build_web.py`.
- Test with `SHOT_HTML=web/dist/<you>.html node tools/shots/shot.js <script> <outdir>`.
- Put your tests in `tools/shots/<you>/`.
- **No git.**
- Edit only files you own. For anything else, put a `NEEDS:` line in your report with the exact patch.

## Hard constraints (all agents)
- **The air-attack limit stays exactly as it is.** `AIR_CHAIN = 2` and `AIR_CD = 0.25` in `04_player.js`: at most two airborne attacks, then you must land. Every new airborne attack must go through `airAtkGate` / `airAtkStart` like the current ones.
  - A pogo refund (`airRefund`) happens only on a real pogo: a down attack hitting a foe, spikes or bramble.
- The smash limit (`smashReady`) is unchanged.
- Arts keep their cooldowns: `cdBase('art', id)` and `cdLeft`.
- The difficulty curve (`59_difficulty.js`) is not touched. The goal is that weapons stop trivialising it.
- The game must still run with any old save.

## Ownership
| Agent | Job | Owns (may edit/create) | Asset prefixes |
|---|---|---|---|
| **WA — animation** | Per-class directional and airborne attacks, and a polish pass on every class's existing animations | `art/gen_player.py` (plus new helper modules `art/player_*.py`); `web/src/04_player.js`; `assets/player*`, `assets/wpn_*` (not `wpn_fx_*`); `tools/shots/wa/` | `player`, `wpn_` |
| **WB — balance, signatures, locked arts** | Nerf every weapon effect, rebalance damage, lock arts to weapons | `web/src/04b_sigs.js`, `web/src/13_weapons.js`, `web/src/15_weapons2.js`, the `WEAPONS` / `ARTS` data in `web/src/01b_gear.js`; new `web/src/60_wbal.js`; the art-picking code in `web/src/29_ui2.js`, `web/src/08b_menus.js`, and the art lines in `web/src/05_combat.js` (`it.weapon` / `it.art`) and `web/src/09_main.js` (lines 217–218 only); `art:` chest/shop entries in `tools/rooms.py` / `tools/regions/*.py` / `SHOPS` (only the entry, nothing else in those rooms); the `wpn_fx_*` sheets (their generator lives in `gen_player.py`: ask WA via NEEDS, or add a new `art/gen_wfx2.py` with prefix `wfx2_`); `tools/shots/wb/` | `wfx2_` |
| **WC — hit feel** | Engine-side impact, sound and motion polish shared by every weapon | new `web/src/61_feel.js`; new `web/src/62_wsfx.js` (weapon sounds); new `art/gen_feel.py` if you need FX sheets; `tools/shots/wc/` | `feel_` |
| Integrator (main session) | Everything else; merges, final benchmarks, publishing | — | — |

WC works only by wrapping or hooking from its own files, for example `HOOKS.update`, wrapping `playerStrike`, `spawnFx`, `hitstop` setters, or `sfx.*`. It never edits `04_player.js` or `04b_sigs.js`; it asks with `NEEDS:` for a hook point if wrapping is impossible.

## WA — animation (the biggest job; take your time, quality over speed)
Today every class shares the **sword's** `attack_up`, `attack_down` and `air_attack` poses: a greatsword or a whip in the air swings like a longsword. Fix this.

1. **New tags per class.** For each class `p ∈ {dg, gs, sp, kt, st, sh, tw, sc, wh}` add `p_up`, `p_air` and `p_down`. The sword keeps `attack_up`, `air_attack` and `attack_down`, polished.
   - Add them to `MOVESETS[cls]` as `up`, `air` and `down`, and pick them in the attack input code (around `04_player.js:238`) through `moveset()`.
   - The mirror class uses the copied class's set.
   - Each tag's `ATK` entry carries flags:
     - `up: true` on the up attack;
     - `air: true` on the air attack;
     - `down: true` on the down attack, pogo included.
   - Hitboxes and active frames come from `assets/player_meta.json`, as for the combos.
   - Fall back to the sword tags if a frame is missing.
   - Replace every check of `P.state === 'attack_down'`, `'air_attack'` or `'attack_up'` in your file with a flag check (`ATK[P.state].down` and so on).
     - Other files that check these names or `anim.tag` need a `NEEDS:` line; the integrator patches them.
     - Known ones: `30_thornveil.js:234`, `31_barrows.js:247`, `12_traversal.js:122`, `14_gear2.js:547`, `24_secrets.js:543`, `57_skills.js`.
2. **Each class's aerials must read as that weapon.** These are suggestions; improve on them.
   - **Dagger:** a flip-stab air attack; a quick upward jab; a reverse-grip dive-stab down.
   - **Greatsword/hammer:** a heavy overhead cleave in the air that briefly hangs you (it cancels upward velocity); a great rising arc up; a two-handed blade-down plunge (bigger box, a little slower).
   - **Spear:** a horizontal air thrust (long thin box); a vertical skyward thrust up; a spear-tip-first down strike.
     - The spear dive (`startSpDive`, `sp_jump`) stays as it is.
   - **Katana:** an iaidō-style air draw-cut; a rising crescent up; a straight downward stab.
   - **Staff:** an air twirl that hits in front and a little behind; an overhead twirl up; a pole-vault stomp down.
   - **Shield:** an air slash; a shield-raised upward bash; a shield-surf stomp down (the shield under your feet is the pogo).
   - **Twin:** a two-blade cross-cut in the air; a scissor up-cut; a crossed-blades drill down.
   - **Scythe:** a spinning reap in the air (hits both sides, lower damage); an arcing hook up; a blade-down reap plunge.
   - **Whip:** a circular lash in the air (both sides); a vertical crack up; a straight-down crack that pogos.
3. **Polish every existing animation.** That's the combo, the heavy, and the counter, backstep and shield counter techniques, for all classes. For each move:
   - an anticipation frame;
   - a smear or sweep on the strike frames (`fx` sweep / arc);
   - follow-through;
   - recovery that settles back to idle.

   Frame timings should give light attacks a snappy feel and heavy attacks weight. Keep the active frames roughly where they are, or retune `active` and the metadata together, so the balance agent's numbers stay valid. Fix anything that looks jaggy, clips through the body or pops between frames. Regenerate **all 50** `wpn_*` overlay sheets so every weapon renders on every new tag.
4. **Tuning of the new tags** (relative to the class's `combo[0]` mult):
   - up attack ×1.0;
   - air attack ×1.0 (spin variants ×0.8 on each side);
   - down attack ×0.9.

   Poise, cost and lunge come from the class's `CLASS_TUNING`. The down attack must pogo off foes, spikes and bramble for every class.
5. **Quality bar.** Follow the user's taste rules: sleek, smooth and heroic, with no chubby or blocky shapes and no noisy grids. Look at your own previews:
   - `art/previews/` contact sheets per class, three times scale, every direction;
   - in-game screenshots with `snap`, including mid-air;
   - 2–3 weapons per class.

   The aerials must look distinct from class to class in a side-by-side sheet.
6. **Tests.** A script that, for every class:
   - does up, air and down on a training dummy or an enemy;
   - asserts the hit landed;
   - checks that the pogo works on spikes;
   - asserts the air limit: a third airborne attack is refused until you land.

   Also run `tools/shots/air_test.js`, `stress.js`, `v19_test.js` and `keys_test.js`.

## WB — balance, signatures, locked arts
### B1. Signatures (`SIGS`): aesthetic first, effect second
Every boss weapon keeps its identity:
- glow;
- particles;
- slash FX;
- tones;
- light.

Make these *more* striking where they are thin. For example, a finisher can play the boss's colour flourish on screen, such as a short sweep of light spears that fade after one tile. The **gameplay** part is cut down to these rules:
- **Damage:** extra hit damage from a signature totals no more than **~8% of the weapon's sustained DPS** in the realistic bench (B3). Today it is often 30–50%.
- **Triggers:** effects that fire damage fire only on the **combo finisher or a charged heavy**, never on every light hit. Each has an internal cooldown of **≥ 2.5 s**. On-hit procs (First Ember echo, SAINT glitch, Quill glyph, Last Kindling pyre, Vael ghost-fire) get **≥ 2 s per target** and small numbers, or become purely visual.
- **Reach:** no signature damage beyond **~1.5× the weapon's own melee reach**. Projectiles become short flourishes: lances and discs die after about 1.5 tiles past the blade; the laser is cut to that length; star shards and sky bolts target only foes within melee-plus range. No homing across the room.
- **Sustain:** the Sanguine Rapier's crit heal goes to ≤ 3% max HP with a 6 s cooldown, or becomes a visual "drink" with no heal. No weapon may heal more than a flask's worth in a whole boss fight.
- **Control:** crowd control on bosses (Vael chains slow, harpoon pull, whirlwind carry) doesn't affect bosses at all, or is halved.
- **Twinborne:** block stoking stays, but each charge's burst ≤ 0.35× light damage.
- **Colossus:** the lava seams deal half as much, last half as long, and erupt only on a fully charged heavy.
- **First Ember:** the echo is visual on light hits. On the finisher only, it deals a 15% echo. Also make it obvious which class it's mirroring: show a toast when you equip it, and add a line to its detail panel.
- Each description should state what the effect does and how often, briefly and in-world. Add a `sigInfo` string per weapon, for example "Finisher: a short lance of light · every 2.5 s", which the gear detail panel shows. If the panel can't show it, add it to the desc.

### B2. Base damage and passives
- **Boss weapons:** total benched DPS, signature included, must be **≤ +5%** over the best found weapon of the same class at the same upgrade level and the same stat spread. Adjust `base`; the look stays.
- **Found weapons:** within a class, no found weapon may be strictly worse than another on every axis. Each should have one clear reason to exist:
  - reach;
  - speed;
  - poise;
  - a status buildup;
  - scaling.

  Tune the numbers to get there. Don't add new mechanics.
- **Status buildups** (bleed, frost, fire and holy splits): trim the outliers so no weapon's status proc adds more than ~20% of its DPS against a boss.
- **Across classes:** in the realistic bench, each class's best weapon lands within **±15%** of the median. Heavier classes may deal more per hit but less per opening.

### B3. Benchmarks (write these, in `tools/shots/wb/`)
- `bench_real.js`, modelled on `tools/shots/sk/bench.js`: a boss held in place with a **1.3 s opening then a 0.7 s swing** cycle.
  - Stamina is real: no refill.
  - Rolls cost stamina.
  - No FP spells.
  - Measure each weapon at +5 with a neutral stat spread (for example str 30 / dex 30 / fth 25).
  - Report:
    - total DPS;
    - DPS from signature damage only (tag the signature damage sources);
    - damage dealt while more than 60 px from the boss.
- Also run the old `tools/shots/dps_bench.js` for continuity.
- Write the before-and-after table to `docs/weapon_balance.md`.

### B4. Arts are locked to the weapon (user decision, binding)
- `SAVE.art` always equals `WEAPONS[SAVE.weapon].art` (for the mirror, the First Ember's own `echo`).
  - Enforce it on load, on weapon swap and on NG+.
  - Remove the art picker row and the art cycling from the equipment menus (`29_ui2.js`, `08b_menus.js`).
  - The art slot on the equipment screen stays as a **read-only** display of the weapon's art, with its name, FP, cooldown and description.
  - The weapon detail panel shows its art.
- `SAVE.arts`, `SAVE.artPinned` and the "Ash of X" items become obsolete.
  - Old saves: ignore these fields.
  - Stop granting arts on weapon pickup; it's harmless, but clean it up.
  - Art chests and shop entries (`art:` in rooms and shops, for example A7's `art:backstep_slash` and the ones in `10_archives.py`, `60_oldsecrets.py` and `83_sa.py`) become an emberstone plus 300 cinders, or whatever fits the spot. List each change.
- Since the art is now part of the weapon, **reassign arts so each fits its weapon**. Today many weapons share generic arts; for example Morvain's Eclipse (`omen`) has `crescent` and Gravetusk has `stormleap`.
  - Use existing `ARTS` only; you may add at most a few thin variants that reuse existing art code with a different FX tint or number.
  - Give every **boss** weapon an art that fits its boss. Many already have one.
  - Give the orphan `backstep_slash` a weapon.
  - Found weapons of one class may share an art, but prefer variety.
- Rebalance arts so none is an outlier:
  - damage per FP;
  - damage per cooldown;
  - no art that one-shots a boss phase or grants long invincibility.

  This matters more now that you can't avoid a bad art.
- Update the skill tree's Flame-branch balance notes if the art change moves its numbers: report it; don't edit `57_skills.js`, which belongs to the integrator.
- Tests:
  - the menus: an art can't be changed, and the display is right for each weapon, mirror included;
  - old-save migration;
  - the benches;
  - `stress.js`, `dormant_chk.js`, `keys_test.js`.

## WC — hit feel (engine side; shared by every weapon)
All of this is aesthetic. It must not change damage, reach or timing windows by more than a frame, with one exception: hitstop may freeze both sides equally.
- **Hitstop by weight:** tiny for daggers, whips and twins; medium for swords, katanas, spears and staves; heavy for greatswords and hammers. Charged heavies and finishers get more. Cap it so it never makes a combo feel sluggish; about 0.12 s at most. Boss hits get slightly less, so fights don't stutter.
- **Screen shake and camera:** a small directional camera kick along the swing on heavies and finishers, and a vertical kick for down attacks and pogos. Respect a new **Settings › Graphics › Screen shake** toggle (Off / Low / Full); ask the integrator via `NEEDS:` for the menu row if it isn't in your file. It also scales the existing `shake`.
- **Impact sparks by material and element:**
  - metal sparks on armoured foes;
  - dust on stone;
  - blood on flesh;
  - frost, fire, holy and ink tints following the weapon's element or signature glow.

  Use short-lived particles and the lighting (`addLight`).
- **Weapon sounds:** a whoosh per class, pitched by weapon weight; heavier impacts for heavy classes; a distinct crack for the whip tip and a ring for the shield; a charged-heavy release. Keep them synthesised with the existing `tone` / `noise` helpers, at the same loudness as the current `sfx`, with no clipping.
- **Motion trail:** an optional engine-side afterimage or ribbon on the weapon tip during active frames. It is subtle, tinted by the weapon's glow (`SIGS[w].glow`, or a steel tint for found weapons), and off when Graphics › Effects is Low if such a setting exists. It must not double up with WA's baked smears; it should read as light, not a second blade.
- **Air-attack landing:** a dust puff and a soft thud when you land from an air or down attack, and a little squash on landing.
- Tests: screenshots mid-swing for each class; a performance check (`stress.js`) showing the frame time doesn't regress more than about 5%; `keys_test.js`.

## Report (every agent)
- What you built.
- Files touched.
- SHARED EDITS and NEEDS, as exact patches.
- Test results, with the actual output.
- Screenshots or contact sheets: paths you looked at yourself.
- Known issues.
