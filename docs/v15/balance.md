# v15 balance, phase 1: boss difficulty and the skill tree against the new weapons

Role `balance`. Phase 1 covers the 9 existing weapon types. Phase 2 (all 14 types' stats) comes later.

## How it was measured

**A scripted boss bot** (`tools/shots/v15/balance/bot_lib.js`, run with `run.sh` / `matrix.sh`) fights every boss in the
Training Grounds with every weapon type:

- **Build.** The expected build for the boss's stage, the same as `adaptExpected` in `69_adaptive`: level 5 + 6 per
  stage, weapon at +min(5, stage/2). Mastery rank I to V by stage. No skills, unless the run is a skill sweep.
  Adaptive scaling stays on, and the expected build lands at x1.
- **Offence.** The bot attacks with the type's main route (the light chain) only while the boss is calm: between attacks
  or staggered. It keeps 30% stamina in reserve to start a chain and 12% to continue one.
- **Defence.** A "reactive oracle" answers each blow that would land with the type's own defensive tool:
  - roll, sidestep or dash for the Maul, Dual Blades, Staff and Whip;
  - parry for the Longsword (parryable blows only; anything else is rolled);
  - the Iai parry for the Katana, which sheathes whenever it's quiet;
  - guard for the Sword & Shield, Spear and Greatsword (only if the stamina covers the block; otherwise it rolls).

  The defence only works when the player is free or able to cancel. Its success chance grows with the size of the
  tool's window: `0.45 + window_ms / 700`. That gives a roll 0.85, a sidestep or parry about 0.68, a dash 0.70 and a
  guard 0.92.
- **Measured.** Time to kill (projected from HP left when the fight runs past 180 s), damage taken in max-HP units (HP is
  refilled every frame), staggers, parries, Iai parries and blocks. Some runs use a real-HP model instead: the bot drinks
  a flask below 25% and flask use is counted.
- **Repeats.** Two seeds per boss/type pair. That gives 25 bosses x 9 types x 2 = 450 fights per matrix (about 40 s on
  6 cores).
- **Bosses left out (7).** The bot can't play their set pieces: Warden, Ferryman, Choir, Colossus, Saint, Sovereign and
  Venn. They either never take damage from it or run on a fixed timer.

It's a crude player. Compare bosses with each other and types with each other; don't read the numbers as absolutes.

**Skill sweeps** (`sweep.sh`, `sweepsum.py`): the same matrix (Gravetusk, Omen, Kalden, Champion, Bellringer and
Pharaoh x 9 types x 2 seeds) is run once with no skills and once per node with only that node. The result is each node's
change in time to kill and damage taken, per type.

**Functional tests:** `skills_test.js` (21 checks, all passing). Every reworked node is played through real inputs on the
dummy.

## Part 1: the skill tree

### What was broken (found in code, confirmed by test)

| Node | Problem with the new move engine | Who it hit |
|---|---|---|
| **Tireless + Flowing Form** | New attacks were detected by "a fresh `P.hitSet`". `mvStart` makes one, and so does **every hit** of a move, so the refund fired 2 to 13 times per move. A Longsword J J J J cost 55 stamina bare, 2.9 with both nodes; a Greatsword J J J cost 62, then **0**. Tireless alone gave 40-58% instead of 20%. | Everyone: attacks were free. |
| **Fourth Strike** | Nothing read it. The text promised an extra combo hit; the move tables decide combos now. | Dead node. |
| **Charged Arts** (charge time) | `chargeTime()` is never called. Every type charges on its own clock (`gsMs`, `mlMs`, `P.mvT`). Only the crescent still fired. | Dead (half). |
| **Blade Dancer, Frenzy** | They nudged `P.anim.speed`, which the move engine resets to 0 every frame (moves run on `P.mvT`). Measured: 1867 ms with and without. | Dead nodes. |
| **Lingering Flame** | Extends War Cry and Cinder Blade. No weapon's locked art is a buff any more. | Dead node. |
| **Deflect** | Only fired on `HOOKS.parry`, which only the Longsword/shield parry and the katana's Iai call. | 3 of 9 types. |
| **Measured Cut** | Only fired on `comboStep === 0`, the first light. The Katana's Iai and the Greatsword's charged blows never counted. | Light-chain types only. |
| **Relentless, Spellblade** | Counted per hit: a 3-hit Demon move gave 3 stacks, or 1.2 s of spell cooldown. | Dual Blades/Staff runaway. |
| **Leech, Pyre Heart, Soul Siphon** | A flat amount per hit. A Dual Blades Demon chain (12 hits) healed 9.6% HP; a Greatsword J J J (3 hits) healed 2.4% for the same damage. | Multi-hit types x3-4. |
| **Bloodthirst** | +16 bleed per hit, the same multi-hit inflation. The strongest node in the tree before the fix: **-16% time to kill overall, -38% on the Dual Blades**, for 1 point at the root. | Dual Blades, Katana. |
| **Light Feet** | Added its own stamina regen even in Demon Mode, where regen is meant to be 0. | Dual Blades exploit. |

### What changed (`web/src/57_skills.js`; save ids unchanged)

- **New-move detection.** A wrapper on `mvStart` replaces the `hitSet` trigger. It fires once per move that actually
  starts. Refunds are a share of what the move **really cost**: charge-level costs, `o.cost` overrides, the weapon's
  stamina factor.
  - **Tireless** is now exactly -20%.
  - **Flowing Form** gives -35% on moves chained out of another move (any branch, not only `step > 0`).
  - **Evasive Strike** applies to the move started out of a roll.
- **Blade Dancer** (+12% light swing speed) and **Frenzy** (+12% below half HP) now act on the move clock through a wrapper
  on `mvSpeed`. They add to the type's own speed bonuses, and the total is capped at **+40%**: Demon + perfect dodge +
  Blade Dancer + Frenzy = x1.40. Stances aren't sped up (`noHit` and `loop` moves), so the Iai and foresight windows keep
  their length.
- **Fourth Strike becomes Finishing Blow:** every finisher (`fin`) deals +20% damage and +30% stance damage.
- **Charged Arts:** every charge stance runs 1.55x as fast, so Greatsword level 3 comes at 517 ms instead of 817. That
  covers the Greatsword and Maul levels and the Longsword, shield, whip, dual, katana-focus and spear holds. The crescent
  is kept. A move can opt out with `noSkillCharge: true`.
- **Measured Cut:** the first move after 0.8 s without striking deals +25%. Opening out of a charge, a sheathe or an Iai
  stance counts (Greatsword charged release 189 -> 236).
- **Deflect** now triggers on every type's clean defence, through a wrapper on `mvGain`. That covers the parry, Iai
  parry, foresight, snap counter, perfect dodge, and a counter landing after a guard, block or brace. It pays +25
  stamina and 3% HP, once per 0.6 s, with no double payout for a defence followed by its counter.
- **Lingering Flame:** after a weapon art, melee hits deal +12% for 6 s. Art buffs still last 40% longer.
- **Damage-based instead of per-hit**, in "light-hit units" (the hit's multiplier):
  - **Bloodthirst:** 12 bleed per unit. A Dual 0.35 hit gets 4, a Longsword light 12, a Greatsword charged 3.0 hit 36.
  - **Leech:** 0.8% HP per unit.
  - **Pyre Heart:** 1 FP per unit.
  - **Soul Siphon:** 2 FP per unit. This is a one-line edit in `04_player.js`.
  - **Relentless** and **Spellblade** count once per move that connects. Spellblade gives 0.5 s per move.
- **Relentless:** the stack now survives 2.5 s without attacking (was 1.2), so it can carry across a boss's attack if
  you aren't hit. Before this, the bot showed -3% time to kill for a 4-point keystone; now it's -7%.
- **Light Feet** respects the type's regen factor (none in Demon Mode).
- Node texts, stat previews and the build summary are updated to match.

### Node value before and after

Change in time to kill / damage taken vs no skills. Negative is better. Bot noise is about ±4%.

| Node | Before: time to kill (worst type) | After: time to kill (per type range) | After: damage taken |
|---|---|---|---|
| Bloodthirst (1 pt) | -16% (**Dual -38%**, Katana -28%) | -7% (Dual -20%, Katana -18%; others 0 to -8) | -4% |
| Tireless / Flowing Form | stamina-free attacks | -1% / -2% (now honest: the bot rarely runs out) | ~0 |
| Blade Dancer | 0 (dead) | -5% (-10% Staff, -8% Dual/LS/Maul) | +3 |
| Frenzy | 0 (dead) | -3% (real HP model; -13% Dual) | -1 |
| Measured Cut | -8% | -7% (all types -1 to -13; Greatsword/Spear most) | -2 |
| Relentless (keystone) | -3% | -7% | 0 |
| Finishing Blow | 0 (dead) | -2% on the J-chain bot (+20% on finishers; the bot rarely reaches them) | — |
| Leech | per hit, Dual x3 | flasks used -23% (the best sustain node, now the same for every type) | — |
| Steadfast | -6% / -15% taken | -5% / -10% taken (Greatsword -14 / -13) | the strongest defensive node; kept |

Charged Arts, Crushing Weight, Iron Flask and Vein Burst show 0 because the bot doesn't hold K, drink or fight crowds.
They are verified in `skills_test.js` instead.

## Part 2: bosses

### Boss changes

| Change | File | Why (bot numbers) |
|---|---|---|
| **BOSS_CURVE re-tuned for 13 bosses** (table below) | `59_difficulty.js` | Outliers in time to kill / damage taken for their stage. |
| **Astrel's supernova no longer always kills.** Blows already sized to your health (`opt.pctHp`, or the nova's 82% of max HP) skip the boss curve (x1.6), adaptive scaling and Hard's x1.5. | `59`, `64`, `69` | It landed for **1.00 max HP**, cover or no cover. |
| **Parry stance follows the stance bar's growth.** Each parry still adds 30% of the boss's **original** bar. Each stagger grows the bar x1.15 (up to x2), so it now takes 3.3 -> 6.7 parries to break, not 3.3 forever. | `67_parry.js` | Longsword/shield vs Vael: **19 staggers a fight** (Sanguine, Kalden and Astrel 7-9). Longsword after: Vael 14, Kalden 6, Sanguine 6.5. |
| **An Iai parry of an unparryable blow** (grab, slam, magic, projectile) still negates the blow, but adds half the stance and doesn't count toward the "two parries break the combo" recoil. | `67_parry.js` | The Katana's Iai negates everything: 10-36 Iai parries a fight. It was best in class on Overseer, Ice Warden, Pharaoh and Astrel. |

Parry suite (`tools/shots/parry/parry_all.js`): 32/32 OK after the change.

BOSS_CURVE `[HP, damage]`, before -> after:

- **Omen:** 1.53/1.14 -> 1.40/0.98
- **Librarian:** 2.50/1.43 -> 3.00/1.50
- **Unwritten:** HP 2.56 -> 2.35
- **Champion:** HP 2.62 -> 2.90
- **Ice Warden:** damage 1.32 -> 1.15
- **Butler:** HP 2.70 -> 3.10
- **Overseer:** HP 2.86 -> 2.60
- **Scarab:** HP 2.90 -> 3.30
- **Pharaoh:** 2.94/1.60 -> 2.80/1.45
- **Orrery:** HP 2.94 -> 3.20
- **Astrel:** 2.98/1.60 -> 2.80/1.45
- **Enforcer:** HP 2.98 -> 3.30
- **Sentinels:** HP 3.00 -> 3.40

Six of these pass the old x3 HP cap: Butler, Scarab, Orrery, Enforcer and Sentinels were at or near the cap and still
fell in about a minute.

Per boss, before -> after. Times to kill and damage taken are geometric means over the 9 types. Damage taken is in HP
bars: 1.0 is one full health bar.

| Boss (stage) | Time to kill | Damage taken | Note |
|---|---|---|---|
| Omen (3) | 118 -> 114 s | **4.56 -> 3.92** | Still the early-game wall, but no longer the highest damage per minute in the game (2.4/min). |
| Librarian (5) | 47 -> 55 s | 0.18 -> 0.22 | Still easy: her damage is mostly projectiles a roll clears. |
| Champion (6) | 68 -> 72 s | 0.98 -> 0.71* | |
| Ice Warden (6.5) | 128 -> 127 s | 3.97 -> 3.62 | Biggest single blow: the stomp, 0.44 of max HP. |
| Butler (7) | 57 -> 65 s | 0.66 -> 0.76 | |
| Overseer (9) | 286 -> 280 s | 2.83 -> 3.01* | |
| Scarab (9.5) | 57 -> 65 s | 1.07 -> 1.21 | |
| Pharaoh (10) | 204 -> 195 s | **4.30 -> 3.95** | |
| Astrel (10.5) | 188 -> 175 s | **5.66 -> 4.46** | |
| Enforcer (10.5) | 61 -> 68 s | 1.07 -> 1.17 | |
| Sentinels (11) | 51 -> 56 s | 0.66 -> 0.63* | |

\* Within noise. The full tables are in `tools/shots/v15/balance/results/`: `boss_curve_*.txt` and
`matrix_{before,after}_{ttk,taken,staggers}.txt`.

**Tried and rejected:**
- **A longer breather** (+0.25 s in every phase): it moved the Greatsword's time to kill by only 2-5%. The gaps aren't
  what holds slow weapons back.
- **A shared breather for duos and trios** (after any twin attacks, the other waits too): no measurable change on the
  Twins, Executioners, Coven or Sentinels. Reverted.

### Per-type picture against real bosses (after; geometric mean over 25 bosses)

Time to kill and damage taken are relative to the average of all 9 types: 1.00 is average, below 1.00 is faster or
safer.

| | Dual | Longsword | Katana | Sword & Shield | Spear | Greatsword | Maul | Staff | Whip |
|---|---|---|---|---|---|---|---|---|---|
| Time to kill (relative) | **0.61** | 0.94 | **0.65** | 1.27 | 1.27 | 1.27 | 0.84 | 1.17 | **1.35** |
| Damage taken (relative) | 0.70 | 0.99 | 1.08 | 1.16 | 0.83 | **1.57** | 0.92 | 1.00 | 0.95 |
| Staggers per fight | 0.2 | 3.6 | 2.1 | 2.9 | 0.7 | 1.6 | 3.6 | 1.1 | **0.1** |

The Maul staggers a lot (3.6 a fight) but not excessively: about the same as the parrying Longsword. It's not a boss
problem.

## Weapon-side findings for phase 2 (not touched: 74/75/76 files)

1. **Dual Blades are the strongest type against bosses.** They are the fastest type on 14 of 25 bosses (the Katana on 10, the Maul on 1), at
   0.41-0.91 of the field's time, and they take the least damage, even with a lower defence success chance (0.70) than a roll. Their short
   moves leave them committed less often.
2. **The Katana's Iai parry negates every blow**, including grabs, slams, magic and projectiles (`76_mech_blade.js`,
   `hurt`). On top of that, the auto counter-cut follows. That's 10-36 Iai parries a fight, and the Katana is fastest or
   near-fastest on most bosses (0.43-0.71 of the field on Sanguine, Vessel, Ice Warden, Vael and Kalden).
   - **Suggestion:** an unparryable blow is deflected with no counter-cut, or costs stamina.
   - The boss side (half stance, no recoil chain) is done.
3. **The Greatsword is weakest:** 1.27 time to kill and **1.57 damage taken**. It's slowest on Gravetusk, Coven,
   Champion, Twins and Astrel. Its commit-heavy swings get punished, and the breather isn't the fix (see above).
   - **Suggestions:** more damage per opening, less recovery, or charge armour on more blows.
   - Steadfast (-14% time to kill) and Measured Cut (-8%) are now its best skill picks.
4. **The Whip (1.35, 0.1 staggers) and Spear (1.27, 0.7 staggers) almost never stagger a boss.** That makes Executioner
   and Riposte Mastery worthless for them, and for the Dual Blades (0.2). They need more poise per second, or a
   type-specific way to open a boss.
5. **Guard costs scale with boss damage, which scales with your HP, while stamina grows slowly.** A typical 18%-of-max-HP
   blow can be blocked this many times on a full bar:

   | Stage | Sword & Shield | Greatsword | Spear |
   |---|---|---|---|
   | 1 | 2.8 | 2.3 | 4.3 |
   | 13 | 1.8 | 1.3 | 2.7 |

   Blocking gets worse as the journey goes on (`tools/shots/v15/balance/guardcost.js`). Suggestion: cost by % of max HP,
   or block costs that grow with END.
6. **Native bleed on the Dual Blades (14) and Katana (18)** makes the Blood branch their best investment (Bloodthirst
   -20% / -18% time to kill even after the fix). This is a bleed-weapon identity, but worth watching when the stats are
   tuned.
7. **The 5 new types:**
   - **Charged Arts** applies to any `loop` + `noHit` heavy stance named `*_hold` / `*charge` / `*_cwind`, or flagged
     `charge`. If the Switch Axe's blade charge must stay hard, give that move `noSkillCharge: true`.
   - **Blade Dancer** speeds every `light`-kind move. The Martial Art "quick" style will benefit most.
   - The bot needs a profile per new type in `bot_lib.js` (`PROF` / `ALT`) before phase 2 can bench them.

## Other findings (not mine to fix)

- **`35_starfall.js:966`:** the supernova multiplies by `NGP.dmg`, and `hurtPlayer` multiplies by it again, so NG+ is
  applied twice.
- **`tools/shots/sk/nodes.js`** (the old skill suite) still checks removed things: the `m_*` masteries, `chargeTime()`,
  combo length for Fourth Strike, `comboStep` for Measured Cut. Its failures are stale tests, not regressions. It already
  failed 14 checks before v15. Use `tools/shots/v15/balance/skills_test.js` for the v15 tree.

## Files

- **Changed:**
  - `web/src/57_skills.js`
  - `web/src/59_difficulty.js`
  - `web/src/64_diffmode.js`
  - `web/src/67_parry.js`
  - `web/src/69_adaptive.js`
  - `web/src/04_player.js` (one line: Soul Siphon; shared)
- **Tests and benches:** `tools/shots/v15/balance/`
  - `bot_lib.js`, `run.sh`, `matrix.sh`, `matrix2.sh`, `sweep.sh`
  - `summarize.py`, `bosscurve.py`, `sweepsum.py`
  - `skills_test.js`, `skstam.js`, `guardcost.js`, `inventory.js`, `trace.js`
  - `results/` (the tables)
- **Run:**

  ```
  BUILD_OUT=web/dist/v15_balance.html python3 web/build_web.py
  sh tools/shots/v15/balance/matrix.sh /tmp/m '{"secs":180,"retreat":30,"rollToward":true}' '[1,2]'
  python3 tools/shots/v15/balance/bosscurve.py /tmp/m
  SHOT_HTML=web/dist/v15_balance.html sh tools/shots/wm/run.sh tools/shots/v15/balance/skills_test.js /tmp/sk
  ```

## Phase 2a: the nine types against bosses

**Ask:**
- Bring the Dual Blades and Katana down toward the pack and the Greatsword up.
- Target: every type's boss time to kill within about ±15% of the average at the expected build, each keeping its
  identity.
- The Katana's Iai parry should no longer fully negate blows that can't be parried.
- Guard costs should stop getting worse over the journey.
- Make stagger-based nodes worth having for the Whip and Spear.

### Bench changes (how each type is played)

Each type is now benched on its best route at the expected build:

- **Katana:** K -> K Iai loop.
- **Greatsword:** level-3 charge (1.2 s hold).
- **Sword & Shield:** J J K.
- **Whip:** tipped K.
- **The other five:** the light chain.

The Whip now keeps 40 px from the boss's edge. At 50 px the bot sat in a dead zone: too far for the handle, too close
for the tip (the J chain landed 0.0 staggers a fight). Whip results swing a lot with spacing (time to kill 84-127 s on
the same bosses at 40 vs 50 px), so its "before" number below is pessimistic. Much of its gap was the bot, not the
weapon.

Matrices: 25 bosses x 9 types x 3 seeds.

### Changes

| Change | File | Effect |
|---|---|---|
| **Katana Iai vs. unparryable blows.** A parryable blow (anything `opt.parryable`, plus 67's `PARRY_MELEE` list) is still negated and counter-cut. Anything else is only turned aside by the scabbard: it costs stamina like a shield block (6 + 0.8 x dmg, guard-scaled), there is no counter-cut, no mastery XP and no Deflect. Without the stamina, the blow lands. | `76_mech_blade.js` | Picked over "chip damage" because it reads like the shield block it imitates. The Katana now pays for turtling: damage taken goes 0.91 -> 1.44 of the field, and Iai counters drop from 10-36 a fight to the parryable blows only. |
| **Greatsword weight.** Every striking move is hyper-armoured against blows under 35% of max HP and takes 40% less damage while it swings. A held charge takes x0.7 (was x0.8). | `76_mech_heavy.js` | Speed is unchanged. Time to kill 1.30 -> 0.99 of the field; damage taken 1.65 -> 1.26 (most of what's left lands while holding a 1.2 s charge, which the bot always does). |
| **Guard cost scales with level.** Block costs (Sword & Shield, Spear, Greatsword, and the Iai's scabbard turn) are multiplied by 210 / the HP a typical build of your level has (by level, not by your Vigor, so stacking Vigor doesn't make blocks free). Never dearer than before. | `76_mech_guard.js` (`mvGuardScale`), `76_mech_heavy.js` | Full-bar blocks of a typical late blow (18% of max HP), stage 1 -> stage 13: Sword & Shield 2.8 -> 3.9 (was 2.8 -> 1.8); Greatsword 2.3 -> 2.8 (was 2.3 -> 1.3); Spear 4.3 -> 6.1 (was 4.3 -> 2.7). Endurance now pays off. |
| **Spear poise +40%** on every strike. | `76_mech_guard.js` | Staggers per fight 0.7 -> 1.3. |
| **Whip tip hits deal x1.6 poise** (`WH_TIP_POISE`). | `76_mech_reach.js` | Staggers per fight 1.9 -> 2.0 on its K route (0.0 -> tip-dependent on the J chain); spacing for the tip now also breaks stances. |
| **Executioner also covers counters** (any `counter` move: riposte, Iai cut, shield / spear / Greatsword / Maul counters): +30% damage and +30 stamina, as for critical hits. | `57_skills.js` | Node value -1% -> -3% time to kill (Katana -13%, Sword & Shield -8%, Longsword -6%). The Whip and Spear benefit through their new staggers (crits), not counters. |
| **Attack rating per type** (`WM_AR_TUNE`, a factor on the base 42). The move tables are untouched, so every route and bench in AR units reads the same. | `74_arsenal9.js` | Factors: Dual 0.60, Katana 0.80, Maul 0.95, Longsword 1, Greatsword 1, Whip 1.10, Spear 1.24, Staff 1.18, Sword & Shield 1.18. |

### Before -> after

Relative to the average of the nine types; geometric mean over 25 bosses; 1.00 is the average.

| Type | Time to kill (relative) | Damage taken (relative) | Staggers per fight |
|---|---|---|---|
| Dual Blades | 0.62 -> **0.87** | 0.71 -> 0.97 | 0.2 -> 0.2 |
| Katana | 0.60 -> **0.90** | 0.91 -> 1.44 | 2.7 -> 3.0 |
| Longsword | 0.96 -> 1.01 | 1.00 -> 1.04 | 3.5 -> 3.6 |
| Maul | 0.85 -> 0.97 | 0.93 -> 1.03 | 3.6 -> 3.7 |
| Greatsword | 1.30 -> **0.99** | 1.65 -> 1.26 | 2.3 -> 2.5 |
| Sword & Shield | 1.23 -> 1.10 | 1.19 -> 1.02 | 3.7 -> 3.9 |
| Spear | 1.30 -> 1.10 | 0.79 -> 0.65 | 0.7 -> 1.3 |
| Staff | 1.19 -> 1.08 | 1.02 -> 0.90 | 1.1 -> 0.8 |
| Whip | 1.32* -> 1.00 | 1.07 -> 0.89 | 1.9 -> 2.0 |

\* Bot at 50 px; see the bench note above.

**Every type now lands within 0.87-1.10 of the average time to kill** (target ±15%). The fastest type per boss is now
spread across five types (Dual 7, Whip 6, Katana 5, Greatsword 4, Spear 3); before, it was only the Dual Blades or the Katana
on 24 of 25 bosses.

The identities still show in damage taken:
- The Spear (0.65) and Staff (0.90) are the safe ones.
- The Katana (1.44) and Greatsword (1.26) trade safety for their big hits.

Files: `tools/shots/v15/balance/results/phase2a_rel_{before,after}.txt` and `phase2a_boss_curve.txt`.

### Tests (all green)

| Suite | Result |
|---|---|
| `tools/shots/v14/blade/routes.js` | 45/45 |
| `tools/shots/v14/heavy/routes.js` | 56/56 |
| `tools/shots/v14/guard/routes.js` | 48/48 |
| `tools/shots/v14/dual/routes.js` | 34/34 |
| `tools/shots/v14/reach/routes.js` | 54/54 |
| `tools/shots/wm/mech.js` | 63/63 |
| `tools/shots/v15/balance/skills_test.js` | 21/21 |

**Expected numbers changed on purpose in `wm/mech.js`:**
- The Iai parry test now uses a parryable blow.
- A new test covers an unparryable blow: deflected for stamina, no counter-cut.
- Greatsword, shield and spear guard costs are multiplied by `mvGuardScale()`.
- The Greatsword charge damage factor is x0.7 (was x0.8).

`skills_test.js` (my file): its Deflect check now uses a parryable blow.

Run them all with `sh tools/shots/v15/balance/routes_all.sh [outdir]`.

### Bot profiles for the five new types (phase 2b)

`PROF` and `ALT` in `bot_lib.js`. `iWhen` presses I in an opening.

| Type | Main route | Defence | `ALT` route |
|---|---|---|---|
| Switch Axe | J chain | roll / sidestep | J J J J K K |
| Bow | J volley chain | limb deflect (the type's own I, `def: 'tapI'`) | K held 850 ms |
| Martial Arts | Swift J chain | slip step | J J I J J (a shift strike) |
| Scythe | J chain | roll | K held 700 ms (Reap) |
| Warbell | J J J | roll | J K J J |

- **Switch Axe:** morphs (I) at a full gauge (`P.sxG >= 100`).
- **Warbell:** Performs (I) with 2+ notes (`P.belNotes`).
- A smoke run on Gravetusk with the in-progress movesets works for all five (dmg/s 0.83-1.28).
- Their spacing (`de`) will need the same check as the Whip's once the movesets settle.

### Notes for later

- **The guard now gets slightly better late** (more blocks per bar as Endurance grows). If you want it exactly flat,
  multiply `mvGuardScale()` by `103 / D.maxSt`.
- **The Dual Blades' AR factor (0.60) is the biggest cut.** Their per-hit numbers on screen drop by 40%. Their dummy dps
  (A12) in AR units is unchanged. Demon Mode isn't benched by the bot, so a skilled Demon player will still sit above
  the pack.
- **The ±15% band is measured by a crude bot.** Spacing-sensitive types (Whip, Spear) and the Greatsword's charge greed
  are where it is least reliable.
