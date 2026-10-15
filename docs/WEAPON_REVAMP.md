# Cinderhollow — Weapons

**Status (v15, branch `overnight-v15`):** 14 weapon types, each with its own combos, mechanic and Weapon Mastery,
plus boss Cores and enchanting. Every number in the tables is the number in the code (`web/src/75_moves.js` the
engine, `web/src/76_mech_*.js` the nine original types, `web/src/78_mech_*.js` the five v15 types) — when the code
changes, change the tables here with it. Section 7 is generated from the game (`tools/movelist_doc.py`).

## Contents
1. [Overview](#1-overview) — controls, the 14 weapon types at a glance, where things live
2. [Shared rules](#2-shared-rules) — reading the tables, timing, the input queue, turning, lunges, stamina, the air limit
3. [The weapons](#3-the-weapons)
   - 3.1 Longsword
   - 3.2 Katana
   - 3.3 Greatsword
   - 3.4 Maul
   - 3.5 Sword & Shield
   - 3.6 Dual Blades
   - 3.7 Spear
   - 3.8 Staff
   - 3.9 Whip
   - 3.10 Switch Axe
   - 3.11 Close-range Bow
   - 3.12 Martial Arts
   - 3.13 Scythe
   - 3.14 Warbell
4. [Weapon Mastery](#4-weapon-mastery)
5. [Boss Cores and enchanting](#5-boss-cores-and-enchanting)
6. [Balance](#6-balance)
7. [Move lists](#7-move-lists) — every weapon's full command list, as in the game
- [Appendix A. Changelog](#appendix-a-changelog) — v14 (v14b, v14c) and v15
- [Appendix B. Decisions and open questions](#appendix-b-decisions-and-open-questions)
- [Appendix C. Original build plan](#appendix-c-original-build-plan)

---
## 1. Overview

**Controls:** **J** light · **K** heavy · **I** block, parry or the type's own special · **L** roll or step · **↑ / ↓** held
for up / down attacks · jump separate. Combos are built from these (J J K, hold K, L → J, air ↓J …); Section 2 has the
rules for timing, holds and the input queue.

**The 14 weapon types**

| Type | Weapon | Difficulty | Identity | Mechanic | Section |
|---|---|---|---|---|---|
| Longsword | Ashen Longsword | ★ | The all-rounder: branching combos, parry → riposte | Parry and riposte | 3.1 |
| Katana | Duskveil | ★★★★ | The patient duelist: sheathe, Iai draw, Iai parry | The sheathe and the Iai draw | 3.2 |
| Greatsword | Gravecleaver | ★★★ | One huge hit at a time: charge levels, swing armour | Charge levels | 3.3 |
| Maul | Cinder Maul | ★★★ | The stunner: walk-charge, brace, knockdowns | Walk-charge and stun | 3.4 |
| Sword & Shield | Knight’s Sword and Shield | ★ | Safe and versatile: full guard, parry, backhop | Full guard, parry and backhop | 3.5 |
| Dual Blades | Twinfangs | ★★★★ | The frenzy: Demon Mode, perfect dodge | Demon Mode and the perfect dodge | 3.6 |
| Spear | Rootspear | ★★ | The walking wall: heavy guard, hop, charge dash | Heavy guard, hop and charge dash | 3.7 |
| Staff | Pilgrim’s Quarterstaff | ★★★★ | Master of the air: vault, momentum | Vault and momentum | 3.8 |
| Whip | Headsman’s Chain | ★★★★★ | Control the space: tip crack, grapple | Tip crack and grapple | 3.9 |
| Switch Axe | Gravegrinder | ★★★★★ | The grinder: earn the Switch Gauge, morph into a chainsaw axe | The Switch Gauge and the morph | 3.10 |
| Bow | Ashstring Recurve | ★★★ | The point-blank hunter: levels climb through the chain, a sweet spot | Charge levels and the sweet spot | 3.11 |
| Martial Arts | Penitent’s Knuckles | ★★★★ | Two styles, one body: Swift and Iron, Shift strikes across them | Swift and Iron styles | 3.12 |
| Scythe | Requiem | ★★★ | The reaper: arcs front and back, souls for the Reap, hook step | Souls and the hook step | 3.13 |
| Warbell | Dirgebell | ★★★ | The tolling bell: notes become tolls (buffs), Perform | Notes and tolls | 3.14 |

Attack factors (each type's base attack 42 × its factor) are listed in Section 2.

**Where things live**
- Code: `web/src/74_arsenal9.js` (types, mastery, select / shrine / mastery screens), `75_moves.js` (move engine),
  `76_mech_*.js` (the nine), `77_types15.js` (the five v15 types' data), `78_mech_*.js` (the five v15 movesets),
  `77_cores.js` (boss Cores, enchanting, Rekindle). Art: `art/player_v13_*.py`, `player_v14_*.py`, `player_v15_*.py`.
- Tests: `tools/shots/v14/<group>/routes.js` (the nine), `tools/shots/v15/<type>/routes.js` (the five),
  `tools/shots/wm/mech.js`, `tools/shots/v15/platform/run_all.sh`, `tools/shots/v15/balance/` (boss bot).
- Write-ups: `docs/revamp2/*.md` (v14 pass), `docs/v15/*.md` (v15: platform, the five types, cores, balance, visuals).

---
## 2. Shared rules

**Reading the tables**
- **Dmg** is a multiplier of the weapon's attack rating. The Longsword's first light hit is 1.0, and every type is
  balanced against that. **Attack factors (v15):** each type's weapon has its base attack (42) multiplied by a per-type
  factor (`WM_AR_TUNE` in `74_arsenal9.js`; the v15 types set theirs in their own `78_mech_*` file through
  `wmApplyArTune()`). The move tables and every dmg/s figure in this doc are in AR units, so they don't change with the
  factor; the numbers on screen do. Factors: Longsword, Greatsword, Switch Axe, Bow, Scythe 1.0; Katana 0.80; Maul 0.95;
  Sword & Shield 1.18; Dual Blades 0.60; Spear 1.24; Staff 1.25; Whip 1.10; Martial Arts 0.92; Warbell 1.12. "2 × 0.45" means two hits of 0.45. A whip value in brackets is the tipped hit (×1.3).
- **Poise** is the stagger power against a foe's stance, for the whole move: a Longsword light is 12, a heavy 45.
- **Stam** is the stamina cost. A new character has about 100 stamina (more with Endurance), regenerating at roughly
  45 per second when you're not attacking.
- **Time** is wind-up / total, in milliseconds:
  - *wind-up* is the delay before the hit lands (how readable and punishable the move is);
  - *total* is how long until you can act again, at normal speed.
- **Distances** are in pixels; a tile is 16 px. The Longsword's light reaches 40 px ("sword reach").
- **Dmg/s** comes from the v14 benches (`tools/shots/v14/<group>/bench.js`): the route played with real key presses on
  the training dummy, infinite stamina, in light-AR units. **Per opening** is the most damage you can land in a boss's
  1.3-second window between attacks (worked out from the table).
- **(v14)** / **(v14c)** mark a move added in the v14 pass or its third round. A Roman numeral in the Input column means the move needs that
  Mastery rank.

**The input queue (v14, every weapon)**
- **Buffer:** a press made up to 180 ms before you're free to act is kept.
- **During a move, one press is queued** and plays when the move ends. **Up to two more presses of the same button** wait
  behind it and are judged by the moves that follow, so **J J J J tapped fast plays all four**.
- **Mashing stops at finishers.** On a finisher, or on the last step of a chain, a press that would *start a new chain*
  only counts in the move's **last 120 ms**; earlier presses are dropped. Mashing J therefore ends the combo at its
  finisher. To go again, press near the end of the finisher or after it.
  - A press that *continues* a designed route still counts from 30 ms in: a K branch (J J J → K), or a route built as a
    deliberate loop (the Katana's Iai → K → K …). A route that just restarts the light chain doesn't count as a
    continuation.
  - The Greatsword and Maul add one exception: **K held** through the end of a swing always starts the charge
    (see Section 3.3 and Section 3.4).
- **Late presses:** a J pressed within **0.3 s after a move ended** still continues that move's chain (K uses the move's
  own window; e.g. 0.5 s after a Greatsword charged slash). Some combos use this on purpose: "J J (beat) J" means
  pressing the third J a little *after* the second swing ends.
- **Perfect timing** (where a move rewards it): a press in the move's **last 150 ms, on its last frame, or up to 80 ms
  after it ends**. The Longsword's ember edge and the Sword & Shield's perfect rush use slightly wider windows of their
  own (see Section 3.1, Section 3.5).

**Turning (v14)**
- **Each step of a chain turns** to face the direction you hold as it starts. So does **L → J** out of a roll.
- Held-charge stances (the Longsword's charged overhead, the Katana's focus draw) also turn with the stick, so you can
  line the release up. The Maul turns freely while walk-charging. A few moves turn on their own: they face the nearest
  foe (the Longsword's wheeling cut, the Katana's turning draw).

**Lunges (v14)**
- A swing's step covers its **full distance only while you push forward**; standing still it's **half**. Dash moves
  (gap-closers with their own lead-in, e.g. the focus draw, the shield rush, the haft jab) always travel the full
  distance.
- **Every lunge ends planted:** your speed is cut when the step ends, so nothing slides past its distance.

**Other universal rules**
- **Roll-cancel:** you can cancel into L after a hit lands, except on moves marked *commit*.
- **Branches:** pressing K at a step of the light combo takes that step's heavy branch, if the weapon has one.
- **Holding K** charges heavies (and on the Spear, holding K while moving starts the charge dash).
- **Air limit:** at most **2 airborne attacks**, then you must land, and the lock lasts 0.25 s after landing.
  - A down attack that pogos off a foe, spikes or brambles doesn't count.
  - A plunge (K in the air) uses the existing smash limit.
- **Air strings (v14):** a J pressed **within 0.3 s after an air swing ends** still continues its air route, so
  air J J combos work even when the second press is a little late. Five types have an air J J string (Longsword,
  Maul at IV, Dual Blades, Staff, Whip); on the Katana, Greatsword, Sword & Shield and Spear a second air J is simply
  another air swing.
- **Every weapon has** an up-attack (↑J), a down-attack pogo (↓J in the air) and a plunge (K in the air).
- **Guard-cost scaling (v15):** every block cost (Sword & Shield, Spear, Greatsword, and the Katana's and Bow's turn of
  an unparryable blow) is multiplied by the **guard scale** = 210 / the max HP a typical build of your level has, capped
  at 1 (`mvGuardScale`, `76_mech_guard.js`). It goes by level, not by your Vigor, so stacking Vigor doesn't make blocks
  free. Boss blows grow with your HP while stamina grows slowly, so blocking used to get worse over the journey; now a
  full bar blocks a typical late blow (18% of max HP) a little more often late than early, and never costs more than
  before.
- **Parryable vs unparryable (v15):** the counters that negate a blow outright (the Katana's Iai parry, the Bow's limb
  deflect) only do so for **parryable** blows. Grabs, slams, magic, projectiles and boss blows outside the parry list
  are turned aside for block stamina, with no counter, no mastery XP and no Deflect.

---
## 3. The weapons

Each section: identity, the trait / mechanic, the move tables (input, rank, timing, dmg, poise, stamina), Mastery,
routes and balance notes.

### 3.1 Longsword: the all-rounder

**Identity:** balanced in everything, easy to learn, with a branching combo that teaches the rest of the game. K
branches off every step of the light chain (J K, J J K, J J J K), and since v14c the heavy branches too (K J, K K).

**v15 (balance):** attack factor ×1.0 (the reference). Boss time to kill 1.02 of the 14-type average, damage taken
1.02, 3.6 staggers a fight.

**Strengths:** good reach, decent speed, a parry with a payoff, no hard commitments except the finisher.
**Weaknesses:** no specialty: less burst than the Katana or Greatsword, less defense than the Sword & Shield or Spear.

**v14:** every lunge was shortened (the heavy poke from 60 to 30 px; nothing else steps more than ~30 px, held
forward). The charged overhead turns while held.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Downward slash | Fast opener | 1.0 | 12 | 12 | 160 / 380 | Roll-cancel after the hit |
| J J | Rising slash | Pressure | 1.05 | 12 | 12 | 160 / 380 | 16 px step |
| J J J | Poke | Reach | 1.1 | 14 | 13 | 200 / 420 | +30% reach; 18 px step, 34 px if the foe is backing off |
| J J J J | **Critical slash** | Payoff | 2.0 | 40 | 18 | 300 / 650 | **Commit** (no roll-cancel); finisher |
| J K | **Lifting cleave** (v14) | Branch, fliers | 1.4 | 28 | 18 | 260 / 600 | Tall rising box; launches light foes. J after it is the poke (J K J J); K the splitting cleave |
| J K K | **Splitting cleave** (v14c) | Launch, then smash | 1.7 | 50 | 22 | 260 / 700 | From the lifting cleave's high finish straight down into the floor (slam); finisher |
| J J K | **Horizontal slash** | Crowds, wide | 1.7 | 35 | 22 | 330 / 640 | Wide flat arc in front |
| J J J K | **Heavy poke** | Long punish | 1.9 | 38 | 24 | 350 / 680 | 58 px reach; 30 px lunge |
| K | Overhead slash | Simple heavy | 1.6 | 45 | 24 | 380 / 700 | 20 px |
| K J | **Return slash** (v14c) | Heavy into lights | 1.0 | 14 | 12 | 150 / 420 | The blade bites the floor and snaps back up; J J after it: the poke and the crit (K J J J). Also after the charged overhead |
| K K | **Crosswise strike** (v14c) | Tall foes, low fliers | 1.5 | 38 | 22 | 300 / 660 | Hilt over the head, the blade flat across the brow: a high box (12–52 px up), 46 px reach; finisher |
| hold K | **Charged overhead** | Stance break | 2.4 | 70 | 30 | 150 + 300 charge, then 380 / 650 | K must stay **held since the press** (v14c: a fast second K is the crosswise strike, never a charge). Blade flashes at full charge; turns while held; let go early for the plain overhead. J after it: the return slash |
| I | Parry | Defense | – | – | 10 | window 170 | |
| I → J | **Riposte** | Parry payoff | 2.2 | 50 | 10 | 250 / 600 | Within 0.6 s of a parry |
| L | Roll | Dodge | – | – | 16 | 420 | 0.28 s invulnerable, 74 px |
| L → J | Quick slash | Punish after a dodge | 1.2 | 14 | 12 | 140 / 400 | J after it: the rising slash |
| L → K | **Wheeling cut** (v14) | Roll through, turn back | 1.5 | 32 | 18 | 240 / 600 | Turns onto the nearest foe (within 100 px), else the held direction; a wide flat cut |
| air J | Air slash | Air hit | 1.0 | 12 | 12 | 150 / 330 | Counts toward the limit |
| air J J | **Falling crescent** (v14) | Air string | 1.0 | 14 | 12 | 150 / 360 | Overhead-to-boots crescent; the box reaches below your feet |
| ↑J | Rising cut | Fliers | 1.0 | 12 | 12 | 160 / 360 | |
| air ↓J | Plunge stab | **Pogo** | 0.9 | 12 | 10 | 100 / 300 | Bounces |
| air K | Plunge | Ground slam | 1.5 | 70 | 18 | – | Smash limit |
| Art | **Ashen Crescent** | Ranged wave | per art | | FP | | Default art |

**Routes (bench):** J J J J **2.74/s** · J J K 2.62 · J J J K 2.68 · J K J J 2.67 · J J (beat) J J (II) 2.62 · pommel
route (IV) 2.34 · ember edge (V) **2.87** · v14c: K J J J 2.51, K K loop 2.26, J K K 2.24 (alternatives for stagger,
reach and rhythm, not damage) · **Per opening:** J J J = 3.15, or riposte 2.2 after a parry.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Step slash** | L forward → J | J in the first 150 ms of a forward roll turns it into a gliding step-cut (1.2 dmg, 10 stam, 140 / 400, 36 px); the roll's stamina comes back. Stay close |
| II | **Wheel slash** (v14) | J J (beat) J | Press the third J 110–300 ms *after* the rising slash ends: a full turn that cuts behind you, then in front (2 × 0.8, 30 poise, 18 stam, 200 / 620). J after it: the critical slash (ember edge works from it too). Pressed sooner, it's the poke |
| III | **Foresight cut** | I → K | A 320 ms counter stance (8 stam; 18 with the parry). A blow inside it is negated and answered with a 2.8 slash (120 / 520, 50 poise, invulnerable 0–220 ms, 28 px). A whiff leaves you standing 200 ms more. *v14: was free and 400 ms; mashing it negated 10 of 12 blows, now 3* |
| IV | **Pommel strike** | J J J → hold K | Hold K at least 180 ms (during the poke, or up to 230 ms into the heavy poke): a pommel bash, 1.0 dmg with **90 poise**, 16 stam, 260 / 600. A tap stays the heavy poke. *v14: the hold is now read reliably* |
| V | **Ember edge** | J J J J on the flash | Press the 4th J in the poke's last 160 ms (20 ms grace) or up to 100 ms after it: the critical slash ignites and a burning follow-up lands (+1.2, 4 s burn). At rank V the poke's tip lights up and ticks for exactly that window |

**Animation reuse:** today's sword combo (`attack1`–`attack4`, `heavy`, `attack_up`, `air_attack`, `attack_down`).
**About 8 new moves:** charged overhead, horizontal slash, heavy poke, riposte, quick slash, step slash, foresight cut,
pommel strike. **v14 tags** (`art/player_v14_blade.py`): `ls_jk`, `ls_rollk`, `ls_air2`, `ls_wheel`; **v14c:** `ls_kj`,
`ls_kk`, `ls_jkk`.

### 3.2 Katana: the patient duelist

**Identity:** fewer, bigger cuts drawn from the sheathe. You win by setting up the draw. **v14** made the drawn light
chain slower and more deliberate (it isn't the katana's game) and put the fun in the sheathe/draw routes.

**Mechanic: the Sheathe**
- **Tapping I** sheathes the blade (300 ms, 4 stam).
- **While sheathed:**
  - you walk at 70% speed and can't block;
  - **J becomes a draw cut** (v14): everything from the sheathe is a draw;
  - **K becomes an Iai draw:** 110 ms wind-up, 2.2 dmg. A tap adds no delay of its own (press to hit is 117–217 ms
    for a 1–9 frame tap);
  - **holding K** is the focus draw (400 ms);
  - **tapping I just before a hit lands** (150 ms window) is an **Iai parry**: a parryable hit is negated and you
    counter-cut automatically (v15: an unparryable one is only turned aside for block stamina, with no counter). Each try costs 6 stamina, and a whiff stands you there 270 ms more (420 total).
- **K while drawn** is a rushing draw that **sheathes you again** afterwards, so K → K is a natural loop. The new J J K
  (crescent sheathe), Iai → J → I and Iai → J → K (thrust home) also end sheathed. (J K mid-chain is the Kesa cut,
  not the rushing draw.)

**v15 (balance):** attack factor **×0.80** (AR 42 → 33.6). The **Iai parry only fully counters parryable blows**: a
blow that can't be parried (grabs, slams, magic, projectiles, most boss blows outside the parry list) is only turned
aside by the scabbard. That costs stamina like a shield block (6 + 0.8 × dmg, guard-scaled, see Section 2), with no counter-cut,
no mastery XP and no Deflect; without the stamina the blow lands. Boss time to kill went 0.60 → 0.91 of the average and
damage taken 0.91 → 1.42: the Katana now pays for turtling.

**Strengths:** the fastest heavy in the game (Iai), huge burst, a strong counter, a nimble sidestep.
**Weaknesses:** no real block; the slowest light chain of the blades, and its flurry staggers poorly; the sidestep's
invulnerability is short; being caught sheathed and slow is deadly.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Quick cut | Opener | 0.9 | 10 | 10 | 140 / 380 | *v14: was 120 / 330* |
| J K | **Kesa cut** (v14c) | Stepping cleave | 1.4 | 32 | 18 | 260 / 640 | A half step back into a high guard, then a shoulder-to-hip cut on a long step (14 px). J after it: the return cut and the flurry. *J K used to fall through to the rushing draw; a neutral K still rushes* |
| J J | Return cut | Pressure | 0.9 | 10 | 10 | 140 / 380 | |
| J J J | **Triple flurry** | Chip | 3 × 0.45 | 18 | 16 | 200 / 680 | Three fast hits; low stagger; finisher |
| J J J → I | Flurry sheathe | Set up the Iai | – | – | 4 | 250 | Sheathes straight out of the flurry |
| J J J K | **Helm splitter** (v14c) | Stagger ending | 1.6 | 50 | 20 | 320 / 760 | The flurry rises into a high guard, holds a breath, then one vertical cut. The stagger the flurry lacks; an alternative to J J J → I |
| J J K | **Crescent sheathe** (v14) | Chain into Iai setup | 1.3 | 26 | 16 | 240 / 660 | A wide turning cut; the follow-through sheathes you, so K next is an Iai |
| J (sheathed) | **Draw cut** (v14) | Quick draw | 1.1 | 12 | 10 | 120 / 400 | A low cut from the hip; J after it: the return cut |
| K (drawn) | Rushing draw | Gap-close | 1.3 | 22 | 24 | 300 / 760 | Dashes 30 px; **sheathes you afterwards**. *v14: was 1.4 / 30 / 20 / 700* |
| K (sheathed) | **Iai draw** | Burst | 2.2 | 40 | 18 | **110** / 600 | Fastest heavy in the game; 20 px |
| Iai → J | **Swallow return** (v14) | Follow-up | 1.1 | 14 | 10 | 100 / 480 | The edge snaps back up the Iai's line. I after it sheathes at once (flurry-sheathe speed); K: thrust home |
| Iai → J → K | **Thrust home** (v14c) | Reach, re-sheathe | 1.1 | 22 | 14 | 160 / 640 | A lunging straight thrust (56 px reach), a chiburi flick, sheathed: K next is an Iai. Draw, return, thrust, draw |
| hold K (sheathed) | **Focus draw** | Dash-through | 2.6 | 55 | 28 | 400 hold, then 140 / 580 | Dashes 60 px through the foe; invulnerable for 0.15 s; turns while held |
| I (drawn) | Sheathe | Stance | – | – | 4 | 300 | |
| I (sheathed, timed) | **Iai parry** | Counter | 2.4 | 60 | 6 + 12 | window 150 | A parryable blow is negated; the counter-cut is 70 / 500, invulnerable 0–260 ms. An unparryable blow is only turned aside for block stamina, no counter (v15) |
| L | **Sidestep** | Dodge | – | – | 10 | 260 | Only 0.16 s invulnerable, 46 px, quick to recover |
| L → J | Step cut | Punish | 1.1 | 12 | 10 | 140 / 400 | J after it: the return cut |
| air J | Air draw | Air hit | 1.0 | 12 | 12 | 150 / 370 | |
| ↑J | Crescent | Fliers | 1.0 | 14 | 12 | 180 / 400 | |
| air ↓J | Needle stab | **Pogo** | 0.9 | 10 | 10 | 100 / 280 | |
| air K | Falling draw | Plunge | 1.5 | 60 | 18 | – | |
| Art | **Moonwave** | | | | FP | | |

**Routes (bench):** J J J 2.17/s (the lowest blade route, on purpose) · **K → K loop 2.59–2.62** (42 stamina a loop;
was 2.70) · J J K K 2.45 · Iai → J → I loop 2.47 · J J J → I → K with thousand cuts (IV) 2.54 · v14c: Iai → J → K loop
2.56, J K J J 2.07, J J J K 2.06 · **Per opening:** sheathed
beforehand, Iai → swallow return = **3.3** in 1.08 s. Against real bosses (bot) the Iai loop still leads every weapon by
about 15–20%, because the fast Iai lands inside openings.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Sheathed stride** | – | Walk at full speed while sheathed |
| II | **Turning draw** (v14) | focus draw → K | The focus draw dashed you through the foe: whirl round onto the nearest foe (else back the way you came), cut and sheathe (1.6 dmg, 35 poise, 16 stam, 160 / 620) |
| III | **Flash step** | L while sheathed | A 50 px blink, invulnerable 0–240 ms, 14 stam, 80 / 380. **No cut** (v14): it keeps you sheathed, so K out of it is an Iai |
| IV | **Thousand cuts** | J J J → I | Each flurry hit echoes 0.5 s later for 0.3 (+0.9 total). Only straight out of the flurry |
| V | **Moonlit iai** | Iai parry in its first 60 ms | Time slows for a moment (0.43 s) and your next Iai within **8 s** deals 3.0 (a pale ring on the HUD drains) |

**Animation reuse:** today's katana combo (`kt_1`–`kt_3`, `kt_heavy`, `kt_up`, `kt_air`, `kt_down`, with the iaido air
draw). **About 9 new moves:** sheathe, sheathed walk and idle, Iai draw, focus draw, Iai parry, sidestep, step cut,
flash step, moonlit counter. **v14 tags:** `kt_draw`, `kt_jjk`, `kt_tsubame`, `kt_turn`; **v14c:** `kt_kesa`, `kt_kabuto`,
`kt_tsuki`.

### 3.3 Greatsword: one huge hit at a time

**Identity:** slow, heavy and patient. Read the boss, pre-charge, and release into its opening. The light chain is
there to feed the K branches (hilt bash into a charge, the momentum cleave), not to win on its own.

**v14b:** after the heavy pass, every Greatsword swing was made about 25% slower and the damage per hit was raised to
match, so each blow lands with more weight.

**Mechanic: charge levels**
- How long you hold K sets the level:

  | Level | Hold time | Dmg | Poise | Stam |
  |---|---|---|---|---|
  | 1 | 180–400 ms | 2.0 | 50 | 28 |
  | 2 | 400–800 ms | 2.85 | 70 | 32 |
  | 3 | 800–1400 ms | **3.9** | 95 | 36 |
  | 4, wrath (Mastery V) | 1400–2100 ms | **4.5** | 110 | 40 |

- **Minimum heave (v14):** a charge can't release before 180 ms, so a K tap is a level 1 slash 180 ms later, not an
  instant one. (A tap used to out-damage the whole weapon: 3.71/s.)
- Holding past **1.4 s overcharges** and drops the hit back to level 2. The three pips over your head **blink in the
  last 200 ms** before the overcharge: release now. Held far too long (2.2 s, 2.6 with wrath), it swings on its own.
- **K again within 0.5 s** of a charged slash chains into a **Strong charged slash**: the same levels, ×1.25 damage
  (2.5 / 3.56 / 4.88), +4 stamina.
- **While charging** you can't be flinched by hits under 30% of your max HP; you still take damage, at ×0.7 (v15; was ×0.8).
- **Swing armour (v15):** every striking move is hyper-armoured against blows under 35% of max HP and takes 40% less
  damage while it swings.
- **Keep charging (v14):** if K is held as any ground swing ends, the charge starts at once. A K *tap* pressed early in a
  finisher is still dropped (mashing stops), but holding K to pre-charge is never eaten.

**v15 (balance):** attack factor ×1.0. **Every striking move is hyper-armoured** against blows under 35% of max HP and
takes **40% less damage** while it swings; a held charge takes ×0.7 (was ×0.8). Speed is unchanged. Boss time to kill
went 1.30 → 1.00 of the average, damage taken 1.65 → 1.24. Blade guard costs are guard-scaled (Section 2).

**Strengths:** the biggest single hits; a flinch-proof charge; stance breaking.
**Weaknesses:** the slowest swings, roll and light attacks; a guard that takes chip damage; every miss is punished.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Overhead hack | Slow opener | 1.45 | 32 | 20 | 350 / 820 | 14 px |
| J J | Wide sweep | Crowds | 1.5 | 32 | 20 | 350 / 820 | Wide arc that clips just behind you |
| J J J | Rising arc | Launch | 1.8 | 45 | 22 | 400 / 920 | Launches small foes; finisher |
| J → K, J J → K | **Hilt bash** (v14) | Into the charge | 0.8 | 45 | 12 | 220 / 580 | A pommel shove. Keep K held: the charge goes on from 400 ms (level 2 at once). J: the turning sweep |
| J (J) → K → J | **Turning sweep** (v14c) | Crowds, both sides | 2.0 | 55 | 22 | 420 / 1000 | From the hilt bash's shoulder rest, the body wheels round in a flat sweep that also covers 20 px behind; finisher |
| J J J → K | **Momentum cleave** (v14) | Chain finisher | 2.6 | 70 | 26 | 430 / 980 | The spin rolls on into a full overhead cleave; no charge needed. K tapped (II): earthsplitter; K held: a fresh charge |
| K / hold K | **Charged slash** | Main damage | 2.0 / 2.85 / 3.9 | 50 / 70 / 95 | 28 / 32 / 36 | hold + 250 / 620 | Flinch-proof while charging. J: the upheaval |
| charged slash → J | **Upheaval** (v14c) | Heavy into lights | 1.8 | 55 | 20 | 440 / 1000 | Wrench the buried blade up out of the floor; lifts small foes. Also after the strong, rolling and wrath releases. J again: the rising arc (K → J → J). A J pressed during a short charge carries into the release. *J here used to restart the light chain* |
| K after a charged slash | **Strong charged slash** | Chain | ×1.25 | same | +4 | hold + 280 / 700 | Within 0.5 s |
| I | **Blade guard** | Block | – | – | 1.2 × dmg × guard scale | – | Frontal only; 25% chip and heavy pushback; **no parry**; a blocked blow opens a 0.7 s counter window |
| block → J | **Retort** (v14) | Guard payoff | 1.8 | 60 | 14 | 170 / 640 | Within 0.7 s of a block, also after letting go of I: the blade torn up out of the floor |
| L | Roll (heavy) | Dodge | – | – | 18 | 520 | 0.28 s invulnerable, 70 px |
| L → J | Overhead hack | Punish | 1.45 | 32 | 20 | 350 / 820 | Starts the light chain |
| L → hold K | Rolling heavy | Punish | charge levels | | 28+ | hold + 280 / 750 | Banks 200 ms of charge |
| air J | Air cleave | Air hit | 1.45 | 40 | 16 | 250 / 640 | **Hangs**: cancels upward speed for a beat |
| ↑J | Great arc | Fliers | 1.3 | 35 | 16 | 280 / 640 | |
| air ↓J | Two-handed plunge | **Pogo** | 1.1 | 45 | 12 | 150 / 430 | Wider box |
| air K | Earth plunge | Plunge | 1.8 | 90 | 20 | – | |
| Art | **Storm Leap** | | | | FP | | |

**Routes (bench, after v14b):** J J J **1.83/s** (lights are weak by design) · **level 3 loop 2.52** · level 3 → strong
level 3 2.25 · v14c: level 3 → J → J (upheaval, spin) 2.21, J → K → J (turning sweep) 1.98, J J J → K → K
(earthsplitter, II) 2.01 · for reference, Longsword J J J J 2.74 · **Per opening:** a pre-charged level 3 = **3.9** in one hit. (The other
Greatsword numbers in `docs/revamp2/heavy.md`, e.g. hilt bash → level 3 at 2.41, were measured before v14b.)

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Shoulder tackle** | L while charging | **Once per charge** (a 2nd L is a plain roll): a 300 ms tackle (0.6 dmg, 40 poise, 10 stam, 40 px). You can't be flinched, take **half** damage, and **keep your charge level**. *v14: was unlimited with a 60% damage cut* |
| II | **Earthsplitter** (v14c) | J J J → K → K (tap) | Plough the buried blade 20 px forward through the floor (dust trail, ground crack) and rip it out level: 2.4 dmg, 85 poise, 26 stam, 520 / 1200. K *held* after the cleave is a fresh charge instead |
| III | **True Charged Slash** | K after a strong charged slash | Charge again, then a two-part slash: a rising backhand (1.5, 280 / 520) and a slam that scales with the level, 2.5 / 3.56 / **4.88** (310 / 880, 1.2× poise). Stamina: level cost + 8 |
| III | **Leaping wide slash** (v14) | hold K → L (tackle) → J | Cash the charge in at once with a bounding sweep: 2.0 / 2.4 / 2.8 by level, 70 poise, 20 stam, 310 / 840 |
| IV | **Guard tackle** | block → K | Tackle out of a block straight into a level 2 charge |
| V | **Wrath charge** | hold past level 3 | Plain charge only (not strong or rolling): a fourth level from 1.4 to 2.1 s replaces the overcharge: **4.5** + a small flame burst (0.4 in a 40 px radius, 4 s burn), 280 / 800. Past 2.1 s it overcharges too |

**Animation reuse:** today's great-weapon set (`gs_1`–`gs_3`, `gs_heavy`, `gs_up`, `gs_air`, `gs_down`). **About 10 new
moves:** a charge pose for each level (×3), the strong charged slash, the true charged slash (two parts), blade guard,
shoulder tackle, wrath charge, rolling heavy. **v14 tags** (`art/player_v14_heavy.py`): `gs_bash`, `gs_mcleave`,
`gs_retort`, `gs_leap`; **v14c:** `gs_heave`, `gs_turn`, `gs_split`.

### 3.4 Maul: the stunner

**Identity:** a brawler that never stops moving. It charges while walking, knocks bosses down, and plays the stun game.

**Mechanic: walk-charge and stun**
- **Holding K** charges while you walk at 60% speed (you can turn freely). What you get depends on when you release:

  | Level | Hold time | Move | Dmg | Poise | Stam | Time |
  |---|---|---|---|---|---|---|
  | 1 | 150–450 ms | **Charged upswing** | 1.6 | 50 | 24 | 200 / 520 |
  | 2 | 450–900 ms | **Double smash** | 2 × 1.2 | 55 each | 28 | 180 / 900 |
  | 3 | 900–1400 ms, released | **Big smash** | 3.0 | 90 | 32 | 300 / 750 |
  | 3 | held to 1.4 s while moving (or below Mastery V) | **Spinning bludgeon** | 0.5 per spin (one every 320 ms, up to 4) | 20 | 32 | – |
  | – | spin released | Spin finisher | 2.0 | 90 | – | 200 / 500 |
  | V | held to 1.4 s standing still | **Earthshaker** | 3.0 + wave 1.0 | 90 + 60 | 32 | 300 / 750 |

- **Minimum heave (v14):** a charge can't release before 150 ms.
- **One decision at 1.4 s (v14):** moving = the spin; standing still = the earthshaker at Mastery V (the spin below V).
  The pips blink 200 ms before that moment. Release before it for the big smash (a 500 ms window, 900–1400 ms).
- **Keep charging (v14):** as on the Greatsword, K held as a ground swing ends starts the walk-charge.
- **Tap vs hold (v14c):** after J or J J, a K *tapped* is the side blow; a K *held* 150 ms or more is the walk-charge.
- **Stun:** maul hits fill a boss's stance **×1.6**. Hits to its upper body fill ×1.2 more. A full stance means a
  knockdown ("STUNNED"). Bosses get 7 s of stance immunity after a stagger and their stance grows ×1.15 each time, so
  there's no stunlock: over 40 s the Maul staggers a boss about 4 times, more than any other weapon.

**v15 (balance):** attack factor **×0.95**. Boss time to kill 0.98 of the average, damage taken 1.01, 3.7 staggers a fight.

**Strengths:** the best at stance breaking and knockdowns; mobile charging; a brace that tanks a hit and pays back.
**Weaknesses:** short reach and no guard; brace still costs HP; the spin is easy to whiff.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Overhead smash | Opener | 1.2 | 40 | 18 | 260 / 620 | 34 px reach |
| J J | Overhead smash II | Pressure | 1.25 | 40 | 18 | 260 / 620 | |
| J J J | **Upswing** | Big stagger | 1.6 | 70 | 22 | 300 / 720 | Launches small foes; finisher |
| J → K, J J → K (tap) | **Side blow** (v14c) | Knock aside | 1.15 | 55 | 18 | 240 / 660 | A flat hook that knocks small foes aside and staggers them. J: the upswing (J → K → J); K (II): backswing slam. *K held here (150 ms+) is still the walk-charge* |
| K (upswing) → J | **Hammer drop** (v14c) | Spike the launch | 1.4 | 60 | 18 | 220 / 600 | The raised hammer comes straight down and spikes a launched small foe. J again: the upswing (K → J → J) |
| hold K (move) | **Walk-charge** | Main damage | see the charge table | | 24 / 28 / 32 | – | 60% walk speed while charging. *v14: upswing poise 60 → 50* |
| hold K → J | **Haft jab** (v14) | Brawl while charging | 0.7 | 45 | 10 | 120 / 360 | Once per charge; lunges 22 px. K still held: the charge goes on; let go: it releases at its level |
| I | **Brace** | Tank one hit | – | – | 15 + 0.5 × dmg | window 600 | Blows can't flinch you and do 50% damage. *v14:* past the window any J / K / L leaves at once; a blow absorbed keeps it open at least 0.4 s more |
| brace a blow → K | **Payback** (v14) | Brace payoff | 2.0 | 80 (stun ×2) | 18 | 160 / 600 | An uppercut out of the brace; launches small foes |
| L | Roll | Dodge | – | – | 16 | 460 | **Releases your charge** (unless Mastery II) |
| L → J | Rolling swing | Punish | 1.3 | 35 | 16 | 200 / 560 | |
| L → hold K | Rolling charge | Re-engage | – | – | – | – | Straight into the walk-charge once the roll's i-frames are spent (280 ms). *v14: the press used to be lost* |
| air J | Hammer spin | Air hit | 1.2 | 30 | 16 | 200 / 520 | |
| ↑J | Rising hammer | Fliers | 1.1 | 30 | 14 | 220 / 520 | |
| air ↓J | **Ground pound** | **Pogo** | 1.0 | 50 | 12 | 140 / 380 | Big bounce (290, vs 245 for a plain pogo). *v14: actually works now* |
| air K | Meteor plunge | Plunge | 1.8 | 100 | 20 | – | 46 px shockwave (0.4, 30 poise) |
| Art | **Tolling Blow** | | | | FP | | |

**Routes (bench):** J J J **2.02/s** (×1.6 stun; the most staggers of any weapon on a real boss) · K tap loop 2.40
(was 2.93) · level 2 loop 1.60 · level 3 loop 1.75 · double smash → third pound (II) 1.76 · earthshaker loop (V) 1.66
· v14c: J → K → J 1.97, J → K → K (II) 2.06, K → J → J 2.01 · **Per opening:** a pre-charged **big smash 3.0** (90 poise × 1.6 stun).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Charge step** | L while charging | Roll without losing the charge (it resumes if K is still held) |
| II | **Third pound** (v14) | double smash → K (tap) | A hop and a third blow into the same spot: 1.6 dmg, 80 poise, 22 stam, 260 / 700. Keep K *held* instead for a fresh charge |
| II | **Backswing slam** (v14c) | J → K → K (taps) | The side blow's momentum carries the body all the way round into an overhead slam: 2.0 dmg, 90 poise, 26 stam, 320 / 820 |
| III | **Big Bang** | J J J → K K K K | A 4-hit chain: 1.0, 1.0 (220 / 520, 14 stam each), 1.2 (240 / 560, 16), then a leaping **3.0** (360 / 900, 24, stun ×2). Mashing K plays all four and stops |
| IV | **Steered spin** | while spinning | Steer the spin; each spin does 0.6 |
| IV | **Hammer spike** (v14) | air J J | A second air blow, once the spin's hit is out: 1.3 dmg, 50 poise, 14 stam, 200 / 500. Spikes small foes into the ground and bounces you a little |
| V | **Earthshaker** | hold K 1.4 s, standing still | The overcharge slammed down: a big smash plus a 56 px shockwave both ways, **1.0 dmg, 60 poise**. *v14: was 64 px / 1.5 / 100, nearly a full boss stagger in one press* |

**Animation reuse:** the great-weapon frames as a base, re-posed with the maul head. **About 12 new moves:** walk-charge
(walk cycle with the maul raised), charged upswing, double smash, big smash, spin loop, spin finisher, brace, the Big
Bang chain (×4), earthshaker. **v14 tags:** `ml_payback`, `ml_jab`, `ml_pound`, `ml_spike`; **v14c:** `ml_side`, `ml_drop`,
`ml_backslam`.

### 3.5 Sword & Shield: safe and versatile

**Identity:** the safest weapon. A full block, the fastest swings, a jump-in attack, and the only weapon that drinks
flasks with the blade out.

**Mechanic: guard and utility**
- **Hold I** to block anything frontal. It costs stamina (6 + 0.8 × damage, × the guard scale since v15, Section 2) and has no
  chip damage. **Tap I** to parry
  (170 ms window, 10 stamina).
  - *v14:* holding I keeps the **whole** 170 ms parry window, then raises the guard (it used to become the guard at
    ~95 ms). A press that only ever blocked gives the parry's 10 stamina back.
- **Flasks with your weapon out:** healing is 30% faster and you can still walk slowly.
- **L is a backhop:** a short hop backwards that leads into the **leaping slash** (J) or the **shield charge** (K).

**v15 (balance):** attack factor **×1.18**; block costs are guard-scaled (Section 2), so a full bar blocks a typical late blow
3.9 times at stage 13 instead of 1.8. Boss time to kill 1.12 of the average, damage taken 0.99, 3.9 staggers a fight.

**Strengths:** the best defense, the fastest attacks, good stagger from shield bashes, and it's forgiving.
**Weaknesses:** the lowest burst, short reach, and a block that gets broken once your stamina runs out.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Quick slash | Opener | 0.85 | 10 | 9 | 120 / 320 | |
| J J | Return slash | Pressure | 0.85 | 10 | 9 | 120 / 320 | |
| J J J | Cross slash | Pressure | 0.9 | 12 | 10 | 140 / 340 | |
| J J J J | **Shield bash** finisher | Stagger | 1.4 | 55 | 14 | 220 / 560 | Small foes reel |
| J J J J K | **Aegis plant** (v14c, II) | Make room | 1.0 | 70 | 14 | 200 / 600 | The shield planted rim-down after the finisher: a stagger on both sides (30 px each way) |
| J K | **Shield jab** (v14) | Stagger in the chain | 0.7 | 28 | 9 | 110 / 330 | A quick shield punch in place of the 2nd cut; J goes on to the cross slash (J K J J); K: backhand rim bash |
| J K K | **Backhand rim bash** (v14c) | Stagger pair | 1.2 | 50 | 15 | 200 / 520 | Jab, then the shield flung out edge-first: 78 poise for the pair; finisher |
| J J J K | **Rim upper** (v14) | Launcher finisher | 1.2 | 50 | 14 | 200 / 540 | The rim driven up through the foe: launches small foes. Jump and keep cutting |
| K | Shield bash | Stagger | 1.2 | 60 | 16 | 200 / 520 | Small foes reel. J: under-rim cut; K: shield hammer |
| K J | **Under-rim cut** (v14c) | Bash into lights | 0.9 | 15 | 9 | 110 / 330 | A fast flat cut from under the shield; J J go on to the cross slash and the finisher (K J J J) |
| K K | **Shield hammer** (v14c) | Big stagger | 1.3 | 60 | 16 | 220 / 560 | The shield hauled overhead, rim hammered down: 120 poise for the pair; finisher |
| hold K | **Charged shield rush** | Break stance | 1.8 | 90 | 24 | 120 + 230 charge, then 220 / 450 | Dashes 70 px; hits under 30% of your max HP don't stop it |
| I (hold / tap) | Block / parry | Defense | – | – | 6 + 0.8 × dmg / 10 | parry window 170 | |
| I → J | Guard counter | Payoff | 1.9 | 45 | 10 | 200 / 520 | Within 0.6 s of a block or parry |
| L | **Backhop** | Dodge | – | – | 12 | 300 | 0.14 s invulnerable, 44 px back |
| L → J | **Leaping slash** | Gap-close | 1.8 | 40 | 16 | 320 / 700 | Jumps forward 64 px with an overhead cut |
| L → K | **Shield charge** (v14) | Back in, stagger | 1.1 | 60 | 14 | 200 / 520 | Drive 52 px back in behind the shield; small foes reel. Stagger instead of the leap's damage |
| air J | Air slash | Air hit | 0.85 | 10 | 9 | 120 / 300 | |
| ↑J | Shield uppercut | Fliers | 0.9 | 20 | 10 | 150 / 340 | |
| air ↓J | **Shield surf** | **Pogo** | 0.9 | 20 | 10 | 100 / 300 | Widest pogo box |
| air K | Falling slash | Plunge | 1.4 | 70 | 16 | – | Mastery IV: the falling bash |
| Art | **Aegis** | | | | FP | | |

**Routes (bench):** J J J J **2.53/s** · perfect rush (II) **3.12** · J K J J 2.43 · J J J K 2.43 · J J (pause) J (II)
2.38 · L → J 2.0 · L → K 1.53 (but 85 poise/s) · v14c: K J J J 2.47 (80 poise/s), K K 2.27 (111 poise/s), J K K 2.29,
J J J J K (II) 2.40 · **Per opening:** J J J K ≈ **3.8** (the bashes stagger, which opens
more windows).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Perfect rush** | J J K, each press on the flash | Each timed hit is stronger: 0.85, **1.1**, then a **1.8** bash (70 poise, 16 stam, 200 / 520). The window is the cut's last 150 ms, its last frame, or 80 ms after it; the 2nd cut only flashes while the rush is still alive. *v14: was 1.0 / 1.2 / 2.0, and a press on the beat missed about half the time* |
| II | **Wheel cut** (v14) | J J (pause) J | Wait 100–300 ms after the 2nd cut: a full turn, the blade in front and the shield edge behind (0.6 + 0.7, 30 poise, 12 stam, 160 / 560). For crowds |
| II | **Aegis plant** (v14c) | J J J J K | After the finisher, plant the shield: 1.0 dmg both sides, 70 poise, 14 stam, 200 / 600. Room to breathe, not damage |
| III | **Shield slam** | block → K | A 1.6 slam with 110 poise (18 stam, 260 / 620) |
| IV | **Falling bash** | air K | Replaces the plunge: a 1.6 plunge with 80 poise that also pogos |
| V | **Perfect guard** | a blow within 100 ms of pressing I | No stamina, almost no pushback; real missiles fly back at the nearest foe in front (homing off; clouds and hazards aren't reflected); the next counter within its 0.6 s window deals +50% (*v14: the bonus used to never expire*) |

**Animation reuse:** today's sword & shield set (`sh_*`: block, guard, counter, the shield-surf down attack). **About 7
new moves:** shield-bash finisher, charged rush, backhop, leaping slash, perfect rush (×3 timing flashes), shield
slam, falling bash. **v14 tags** (`art/player_v14_guard.py`): `sh_jab`, `sh_rim`, `sh_charge`, `sh_wheel`; **v14c:** `sh_kj`,
`sh_kk`, `sh_jkk`, `sh_aegis`.

### 3.6 Dual Blades: the frenzy

**Identity:** relentless and high-risk. Burn stamina for a flurry and dance around the boss.

**Mechanic: Demon Mode** (toggled with I; *v14:* I can be pressed mid-chain and toggles the moment the swing ends)
- **Stamina drains** at 12 per second and doesn't regenerate. A warning tick sounds when a fifth of the bar is left.
- **Attacks cost half stamina (v14):** the drain is the price. Mashing from a full bar now lasts about 4.7 s (was 3.1).
- **You swing 20% faster** and the light chain runs to 6 hits.
- **L becomes a demon dash:** 120 ms, 0.12 s invulnerable, 8 stamina, 52 px, chains twice.
- **The demon gauge:** each hit in Demon Mode fills it by 3%. When it's full you enter **Archdemon**, which lasts 20 s.
  - In Archdemon, the gauge drains over the 20 s.
  - **Hold K** for the **Blade Dance**: eight hits of 0.4, then a 1.0 finisher (4.2 total over 1.4 s), which empties
    the gauge. It has light armour (blows under **20%** of your max HP don't stagger you; *v14: was 30%*, which stopped
    almost every boss blow).
- **Running out of stamina** drops you out of Demon Mode, exhausted: stamina won't regenerate for 1.5 s.

**Mechanic: Perfect dodge** (works with the roll and the demon dash)
- A dodge started just before a hit would land is a perfect dodge. The window depends on the dodge:
  - **normal roll: 100 ms** (6 frames, its last frame included; *v14: it was really 83 ms*);
  - **demon dash: 175 ms** (more forgiving, and it runs on past the end of the 120 ms dash).
- The hit is avoided, time flickers for a moment, and a silver afterimage is left behind.
- **Stamina:** a perfect dodge **restores 25 stamina at once**, even in Demon Mode.
- **Attack speed:** a perfect dodge grants **+0.1 attack speed** (+10%) for **6 s**. It doesn't stack; each new perfect
  dodge refreshes it. It adds to Demon Mode's +20%, for **+30% at most**.
- **Rules (v14):**
  - **One perfect dodge per blow.** The ticks of a beam, flame jet or mist count as one blow.
  - **The +25 stamina comes once per enemy attack:** all the hits of one boss combo pay once; each new attack pays again.
    A skilled player can still perfect-dodge (and counter) every hit, but the stamina can't be farmed.
  - **Bumping into a foe's body isn't a blow.**
  - It works against bosses, elites and regular foes alike, melee and projectiles.
- **Feedback:** a sharp silver chime, a short afterimage, and a small blade icon under the stamina bar with a ring
  showing how much of the 6 s is left.

**v15 (balance):** attack factor **×0.60** (AR 42 → 25.2), the biggest cut: per-hit numbers on screen drop by 40%, while
the dmg/s figures here (in AR units) are unchanged. It was the fastest type on 14 of 25 bosses; now 0.89 of the average
time to kill, damage taken 0.95. The bot doesn't bench Demon Mode, so a skilled Demon player still sits above the pack.

**Strengths:** the highest sustained damage, great mobility, multi-hit status buildup, and perfect dodges that refuel
and speed it up.
**Weaknesses:** **no block**, the shortest reach, low poise per hit, and stamina management under pressure. Its best
play needs perfect-dodge timing.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Double slash | Opener | 2 × 0.45 | 6 | 8 | 100 / 300 | |
| J J | Double slash II | Pressure | 2 × 0.45 | 6 | 8 | 100 / 300 | |
| J J J | Cross slash | Pressure | 2 × 0.5 | 8 | 9 | 110 / 300 | |
| J J J J | Spin | Finisher | 1.2 | 20 | 12 | 220 / 520 | Mashing stops here outside Demon Mode |
| J J K | **Hooking cross** (v14c) | Reel, flow | 0.45 + 0.55 | 20 | 11 | 140 / 440 | Wide low stance, both blades hooked in at the knees: reels non-elite foes. J: the cross slash (J J K J K flows into skyward fangs and the air string). *J J K used to fall through to the lunge* |
| J J (pause) J | **Fang barrage** (v14) | Pressure, status | 4 × 0.22 + 0.3 | 12 | 10 | 110 / 470 | Press 110–450 ms after the 2nd slash ends: five alternating stabs, stepping in. J: the spin. A steady rhythm never triggers it by accident |
| J J J K | **Skyward fangs** (v14) | Anti-air, juggle | 0.4 + 0.5 | 22 | 12 | 130 / 460 | A rising double cut that springs you ~50 px up and pops light foes. J: twin spin, J: crossfall |
| J ×5 / ×6 (Demon) | Demon chain | Extend | 2 × 0.35 / 3 × 0.3 | 8 / 10 | 8 / 10 | 100 / 280 | Demon Mode only. *v14: was 2 × 0.5 / 3 × 0.45* |
| K | Lunge | Gap-close | 1.1 | 15 | 12 | 200 / 480 | Dashes 60 px. J: spiral pursuit; K: fang pounce |
| K J | **Spiral pursuit** (v14c) | Crowds, both sides | 3 × 0.25 + 0.35 | 12 | 10 | 120 / 480 | A drifting corkscrew, two turns, blades out like a wheel (±33 px, 24 px drift). J rejoins the chain at the cross slash |
| K K | **Fang pounce** (v14c) | Stagger | 1.3 | 35 | 14 | 230 / 600 | A short hop off the lunge, both blades chopped down together as you land. Scripted to land on the hit: not an air attack |
| K (Demon) | **Demon flurry** | Burst | 6 × 0.3 | 30 | 16 | 150 / 800 | II: J → bloodwheel |
| hold K (Archdemon) | **Blade Dance** | Big finisher | 8 × 0.4 + 1.0 | 60 | – | 150 / 1400 | Armour vs blows under 20% max HP; empties the gauge |
| I | **Demon Mode** toggle | Mode | – | – | drain 12/s | 200 | **No block** |
| L | Roll / demon dash | Dodge | – | – | 16 / 8 | 420 / 120 | **Perfect dodge** within 100 ms (roll) / 175 ms (demon dash) of a hit: +25 stamina (once per attack), +0.1 attack speed for 6 s |
| L (perfect) → J | **Counter flurry** | Perfect-dodge payoff | 3 × 0.45 | 15 | 8 | 80 / 300 | Comes out instantly after a perfect dodge |
| L → J | Dash slash | Punish | 1.0 | 10 | 8 | 100 / 320 | 30 px; J: back into the chain |
| air J | Twin spin | Air hit | 2 × 0.45 | 8 | 9 | 120 / 330 | |
| air J J | **Crossfall** (v14) | Air string | 0.45 + 0.55 | 18 | 10 | 130 / 480 | Hang, open an X, dive to the floor at a slant and land planted. Counts as an air attack |
| ↑J | Scissor up-cut | Fliers | 2 × 0.45 | 8 | 9 | 140 / 340 | |
| air ↓J | **Drill** | **Pogo** | 3 × 0.3 | 10 | 10 | 100 / 320 | |
| air K | Twin plunge | Plunge | 1.3 | 50 | 16 | – | |
| Art | **Twin Tempest** | | | | FP | | |

Stamina costs in the table are normal-mode costs; in Demon Mode every attack costs half.

**Routes (bench):** J J J J **2.81/s** · Demon J ×6 **3.42** (was 3.85) · Demon J ×6 with the perfect-dodge buff
**3.66** · J J (pause) J J 2.34 · J J J K J J 2.15 (utility) · Demon J ×6 → K (II) 3.34 · perfect-dodge loops:
L → J 3.51, L → K (III) 3.25 · v14c: K J J J 2.44, K K 2.22, J J K J J 2.65, Demon K J J J K (II) 2.92 (vs Demon K loop 2.61) · **Per opening:**
in Demon Mode about **4**; the Blade Dance gives 4.2 by itself (5.7
with Blade Dance II). On a real boss (bot) the Demon Mode bench barely beats normal mode (1.05 vs 1.02): it's a modest
gain you pay for with exhaustion, stretched by perfect dodges.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Dash-through cut** | demon dash → J | Cut through the foe as you dash: 1.0 dmg, 15 poise, 8 stam, 100 / 320, 44 px. After a perfect dodge it deals 1.5. *v14: no i-frames of its own (the dash before it has them), 60 → 44 px* |
| II | **Rending cyclone** (v14) | Demon: J ×6 → K | The Demon chain's finisher: two crimson spins (both sides) and a leaping cross-cut, 3 × 0.3 + 0.8, 40 poise, 14 stam (7 in Demon), 150 / 640. Stagger, not damage. Below II, K after the 6th hit is dropped |
| II | **Bloodwheel** (v14c) | Demon: K → J | Out of the demon flurry: a somersault, both blades wheeling over the head and down in front, landing on the 3rd cut (3 × 0.3, 15 poise, 10 stam, 120 / 440). J carries on into demon chain hits 5 and 6 (then K: rending cyclone). Below II, J in the flurry is dropped (it's a finisher) |
| III | **Blade Dance II** | hold K (Archdemon) | Three more hits and a bigger cross-cut: 8 × 0.4 + 3 × 0.3 + 1.6 = 5.7 (+1.5), 80 poise, 150 / 1680 |
| III | **Reversal cut** (v14) | L → K | Turn out of the roll with two rising cuts: 0.45 + 0.6, 18 poise, 10 stam, 110 / 420. After a perfect dodge it's silver, ×1.5 and 50 poise: the stagger answer to a perfect dodge (J's counter flurry is the fast one). A non-perfect demon dash → K stays the demon flurry |
| IV | **Iron lungs** | – | The Demon Mode drain drops from 12/s to 8/s |
| V | **Archfiend** | – | Archdemon lasts 30 s, and your dashes leave a smouldering trail: 0.15 every 0.4 s to a foe standing in it, each segment lasting 1 s (about 0.37 dmg/s). *v14: was 0.3 every 0.3 s for 1.5 s, a weapon by itself* |

**Animation reuse:** today's twin set (`tw_1`–`tw_5`, `tw_heavy`, `tw_up`, `tw_air`, `tw_down`). **About 9 new moves:**
demon stance and aura, demon chain hits 5–6, demon flurry, demon dash, Blade Dance (long), dash slash, the Archdemon
aura variant, and the perfect-dodge afterimage plus counter flurry. **v14 tags** (`art/player_v14_dual.py`):
`tw_barrage`, `tw_skyward`, `tw_crossfall`, `tw_dfin`, `tw_reversal`; **v14c:** `tw_spiral`, `tw_pounce`, `tw_hook`, `tw_bwheel`.

### 3.7 Spear: the walking wall

**Identity:** plant your feet, block anything frontal, and poke the boss to death from behind the guard.

**Mechanic: guard and poke**
- **The I guard** blocks almost anything frontal, **even big hits**.
  - It costs 5 + 0.5 × damage in stamina (× the guard scale since v15, Section 2) and pushes you back hard.
  - Hits worth more than 30% of your max HP still do 10% chip damage.
  - You can walk slowly behind it (backwards too). **The guard never turns:** let go of I to face the other way.
- **Guard poke:** I + J pokes from the guard. *v14:* the guard covers the coil (0–110 ms) and the recovery (from
  260 ms), but **not the thrust itself**. It used to be guarded the whole time, poking at 2.25/s behind a permanent block.
- **Counter-thrust:** I then K, within 0.5 s of a block.
- **Hop (L):** a short hop instead of a roll. *v14:* it **keeps you facing the foe**: you hop toward it only while you
  push at it, otherwise you hop back. Chain two, or three with Mastery II; chained hops follow the same rule.
- **Charge dash:** hold K while moving to wind up for 400 ms, then run (175 px/s) for up to 3 s, hitting every 0.3 s
  and draining 8 stamina a second. Release K for the finishing thrust, or press I to stop. *v14:* the finisher costs
  12 stamina and only deals its full damage after a 400 ms run; it used to be free and full from a 0 ms run.

**v15 (balance):** attack factor **×1.24**, and **+40% poise on every strike** (rounded; the tables below show the new
values; the charge dash's run hits and the finishing thrust's 70 / 40 are unchanged). Staggers per boss fight 0.7 → 1.3.
Block costs are guard-scaled (Section 2): a full bar blocks a typical late blow 6.1 times at stage 13 instead of 2.7. Boss
time to kill 1.12 of the average, damage taken 0.64 (the safest type).

**Strengths:** the longest poke reach, the strongest guard, safe steady damage, and a gap-closing charge. The best
real-boss numbers of the nine plain chains (its 60 px reach keeps landing).
**Weaknesses:** the least mobile (no roll), low burst, a guard that can't turn, and it struggles with fliers.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Poke | Opener | 1.0 | 20 | 11 | 140 / 380 | 1.5× sword reach (60 px) |
| J K | **Twin thrust** (v14c) | Two-height poke | 0.5 + 0.6 | 39 | 13 | 150 / 520 | A poke at the knee, then the chest; J goes on to the overhead sweep (J K J) |
| J J | Poke II | Pressure | 1.0 | 20 | 11 | 140 / 380 | |
| J J K | **Recoil thrust** (v14c) | Poke and keep the wall | 1.1 | 35 | 12 | 160 / 460 | The feet step back 18 px while the spear goes out; finisher |
| J J J | Overhead sweep | Pressure | 1.15 | 25 | 12 | 160 / 420 | Finisher; 44 px reach, its drawn arc (*v14c: was 60*); hop → J continues the chain |
| J J J K | **Impaling drive** (v14) | Stagger finisher | 0.75 + 0.85 | 70 | 16 | 220 / 660 | Thrust it home, then twist it deeper |
| K | High thrust | Fliers, tall foes | 1.4 | 49 | 18 | 260 / 600 | v14c: a real `sp_high` thrust (coil low, drive up at 40°); box 50 px out, 52 px up (was 64). J: falling haft; K (II): sky rake |
| K J | **Falling haft** (v14c) | Chop down | 1.2 | 56 | 12 | 180 / 520 | From the high thrust, the spear raised and the haft chopped down in front; finisher |
| I (hold) | **Heavy guard** | Block | – | – | 5 + 0.5 × dmg | – | Big hits do 10% chip; walk slowly |
| I + J | **Guard poke** | Safe chip | 0.8 | 17 | 10 | 140 / 380 | Guard up except during the thrust (110–260 ms). *v14: was 0.9 and fully guarded* |
| block → K | **Counter-thrust** | Payoff | 2.0 | 84 | 14 | 160 / 520 | Within 0.5 s |
| hold K (move) | **Charge dash** | Gap-close | 0.4 per 0.3 s | 15 | 8 per second | 400 wind-up | Runs up to 3 s; I stops. From neutral only: a K inside the J chain is a thrust (v14c), so let the chain end first |
| release K | Finishing thrust | Dash payoff | 2.2 (after a 0.4 s run) / 1.4 (sooner) | 70 / 40 | 12 | 120 / 480 | |
| L | **Hop** | Dodge | – | – | 8 | 260 | 0.14 s invulnerable, 40 px; chain 2 |
| L → J | Hop poke | Pressure | 1.0 | 20 | 10 | 120 / 360 | Picks the poke chain up where it left off (within 1.2 s) |
| L → K | **Hop lunge** (v14) | Back in | 1.3 | 49 | 15 | 200 / 540 | Off the hop (usually a back hop), a long low lunge back in (50 px) |
| air J (rising) | **Jump thrust dive** | Dive in | 1.5 | 56 | 16 | – | Attack while rising after a jump |
| air J | Air thrust | Air hit | 1.0 | 20 | 11 | 140 / 360 | |
| ↑J | Sky thrust | Fliers | 1.1 | 28 | 12 | 180 / 420 | |
| air ↓J | Tip-first strike | **Pogo** | 0.9 | 20 | 10 | 100 / 300 | |
| air K | Lance plunge | Plunge | 1.5 | 70 | 18 | – | |
| Art | **Thunder Lunge** | | | | FP | | |

**Routes (bench):** J J J **2.63/s** · guard-poke loop 1.98 with the guard up 63% of the time (was 2.25 at 100%) ·
charge dash quick release 1.93 (13 stam/s; was 2.74 for almost nothing), after a 0.4 s run 2.22 · J J J K 2.54 ·
J J (pause) J (II) 2.17 · L → K 1.73 · v14c: J K J 2.41, J J K 2.51, K J 2.29 (67 poise/s), K K (II) 2.31 · **Per opening:** J J J = 3.15, or **block → counter-thrust 2.0** (3.0 charged,
III) against any attack you block.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Triple hop** | L L L | Chain three hops |
| II | **Wheeling haft** (v14) | J J (pause) J | Wait a beat (100 ms or more) after the 2nd poke: the spear spun flat, tip in front, butt behind (0.55 + 0.7, 42 poise, 13 stam, 180 / 600). The spear's answer to a crowd |
| II | **Sky rake** (v14c) | K K | A second, steeper high thrust (box 40 px out, 60 px up) that lifts small foes: 1.3 dmg, 56 poise, 15 stam, 200 / 560. The spear's anti-air string |
| III | **Charged counter** | block → hold K | Keep K held without a break for **150 ms from its press**: a 3.0 counter-thrust with 126 poise (360 / 800, the hit about 360 ms after the press). The tip warms while K is held as a cue; taps up to ~133 ms stay quick. *v14: any slightly long tap used to charge by accident* |
| III | **Rising sweep** (v14) | counter-thrust → J | The haft swept up overhead after the counter: 1.2 dmg, 56 poise, 12 stam, 160 / 500; launches small foes |
| IV | **Power guard** | I + K | For 1 s: no pushback and no chip from anything; blocks cost ×1.5 stamina. Free, but it can't be re-armed while it's up, and it has its own pose |
| V | **Thunder charge** | charge dash | The dash pierces with lightning (+0.5 per hit) and the finisher deals 3.0 (1.8 on a quick release) |

**Animation reuse:** today's spear set (`sp_1`–`sp_3`, `sp_heavy`, `sp_up`, `sp_air`, `sp_down`, and the spear dive).
**About 9 new moves:** guard stance and guard walk, guard poke, counter-thrust, hop, charge-dash run cycle, finishing
thrust, power guard, charged counter. **v14 tags:** `sp_drive`, `sp_hoplunge`, `sp_wheel`, `sp_rsweep`; **v14c:** `sp_jk`,
`sp_jjk`, `sp_kj`, `sp_kk`, `sp_high`, `sp_guard_back`.

**Animation audit (v14c):** all 25 spear tags were checked frame by frame (`tools/shots/v14/guard/spear_audit.py`:
"shrunk frames: none").
- *No more telescoping:* the 64 × 40 frame used to force the spear 20–37% shorter on exactly the strike frames of the
  counters, finisher, drive and hop lunge. The lunges were re-posed (hands and body within 41 px) so the full spear fits
  and the stretch reads through the lean. The up and down thrusts were re-posed the same way.
- *Reach ghost:* a frame can only draw a thrust's tip ~34 px out, but thrusts hit at 60 px. On each thrust hit, two pale
  fading copies of the spear lance on along the thrust line to the real reach, so what you see is what connects.
- *Guard:* a crouched, levelled brace (haft at −27°) instead of a walking-stick pose. The guard walk no longer
  moonwalks, and backing off behind the guard has its own cycle (`sp_guard_back`).
- *Wheeling haft:* the spear now rolls up over the head and round behind, instead of flipping in one frame.

### 3.8 Staff: master of the air

**Identity:** vault over the boss, fight from above, and never stand where it swings.

**Mechanic: vault and momentum**
- **I vaults** you off the staff: 350 ms, about 41 px up and 33 px forward standing still (84 px holding forward).
  - Invulnerable for the first 0.2 s; costs 15 stamina.
  - **The vault itself isn't an attack**, so it doesn't count toward the air limit (see open question 1).
  - **Presses during the vault are kept (v14):** J or K pressed at any point of it plays as soon as it can be left
    (0.22 s, in the air): I → J is the vault kick, I → K the aerial spin, I → ↓J the dive kick.
- **Both ends hit:** combo hits strike in front and slightly behind.
- **Momentum:** each air hit adds a stack, up to 3, for +8% damage each.
  - Stacks last until 0.5 s after landing.
  - Your first ground swing after landing keeps them.
- **Glide (v14):** while the staff turns, the spinning air moves slow your fall (the aerial spins to 60 px/s, the vault
  kick 50, the cartwheel 90), so a whole vault string fits in one jump. Before, the spin finisher whiffed from a vault
  every time.

**v15 (balance):** attack factor **×1.25** (1.18 in phase 2a, raised in 2b when it drifted to 1.15 in the 14-type field).
Boss time to kill 1.04 of the average, damage taken 0.87.

**Strengths:** the best evasion (it's hard to be where the boss swings), hits on both sides, momentum burst, good
against fliers.
**Weaknesses:** low poise, weaker on the ground, the air limit caps its burst, and it punishes mistimed vaults.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Strike | Opener | 0.9 | 12 | 10 | 140 / 360 | Also hits 14 px behind. *v14: was 0.85* |
| J K | **Back vault** (v14c) | Disengage | 0.8 | 22 | 12 | 150 / 500 | Plant the staff ahead and flip back over it, feet kicking up through the foe; ends ~44 px back and 43 px up, in the air (air J / K follow). The hit is airborne: +1 momentum from the ground |
| J J | Butt strike | Both sides | 0.9 | 12 | 10 | 140 / 360 | Hits 30 px behind |
| J J J | Low sweep | Trip | 0.9 | 16 | 11 | 160 / 380 | Trips small foes |
| J J J J | Overhead | Finisher | 1.5 | 40 | 14 | 240 / 560 | *v14: was 1.4 / 35* |
| J J K | **Pole launcher** (v14) | Ground to air | 1.0 | 28 | 12 | 170 / 470 | Plant and heave: launches small foes and carries you ~45 px up. Not an air attack itself; air J / K follow |
| K | **360° spin** | Both sides | 2 × 0.8 | 60 | 24 | 220 / 640 | Front and back. *v14: a flat 24 stamina (was 30% of the bar)*; the Whirling Staff skill makes it cheaper. J: spin vault |
| K → J | **Spin vault** (v14c) | Over the top | 1.1 | 34 | 13 | 230 / 560 | The spin carries you up and over in a low hop (~35 px forward); the staff chops down from above. Airborne hit: +1 momentum. Lands before it ends |
| I | **Vault** | Mobility | – | – | 15 | 350 | Invulnerable for 0.2 s; not an attack |
| I → J | **Vault kick** (v14) | Vault attack | 1.1 | 24 | 10 | 110 / 360 | A flying two-footed kick off the planted pole, driving forward. Counts as an air attack |
| I → K | Vault spin | Vault attack | 1.4 | 40 | 16 | 180 / 460 | The aerial spin straight out of the vault |
| L | Roll | Dodge | – | – | 16 | 420 | |
| L → J | Low sweep | Punish | 1.1 | 20 | 10 | 140 / 380 | Both sides; trips |
| air J | Aerial strike | Air hit (+1 momentum) | 0.9 | 14 | 10 | 120 / 320 | |
| air J J | **Cartwheel** (v14) | Air string, both sides | 0.5 + 0.6 | 18 | 11 | 120 / 400 | Turn over the staff: the butt behind you, then the head in front |
| air K | **Aerial spin** | Both sides (+1) | 1.4 | 40 | 16 | 180 / 460 | Replaces the plunge; counts toward the limit. J: comet |
| air K → J | **Comet** (v14c) | Spend momentum | 1.1, +25% per stack | 30 + 12 per stack | 14 | 160* / 500 | Dive staff-first at 40° (64 px forward at most) into the floor, or bounce off a head. **Spends the momentum:** 3 stacks = ×1.75, 66 poise. Uses the smash limit. *The hit lands on impact |
| ↑J | Rising twirl | Fliers | 0.9 | 14 | 10 | 140 / 340 | |
| air ↓J | **Dive kick** | **Pogo** (+1) | 1.0 | 30 | 10 | 100 / 300 | Its first bounce in a jump refunds one air attack. *v14: it used to refund every bounce, an endless pogo* |
| Art | **Whirlwind** | | | | FP | | |

**Routes (bench):** J J J J **2.52/s** (was 2.40; about 90% of the Longsword) · K spin loop 2.49 (60 poise on both
sides) · J J K 2.35 before its air follow-up · v14c (exact-cycle bench): J K 1.79 (a disengage), J K + air J 2.50, K → J 2.31
· on a real boss (bot), the vault cycle (I, J, K, ↓J) now lands
0.63 dmg/s with 2 hits taken (was 0.45 with 6) · **Per opening:** vault in, vault kick, then aerial spin ≈ **2.6** with
momentum, with almost no risk.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Roll vault** | L → I | Vault straight out of a roll (from 80 ms in) |
| II | **Pole drop** (v14) | air ↓J → K | Off the dive kick's bounce: hang, then ride the staff point straight down. 1.4 dmg, 40 poise, 16 stam, a two-sided shock (36 px each way) where you land, or a bounce off a foe's head. Uses the smash limit, like every plunge. (Air ↓K is every weapon's Cinder Slam, so the pole drop hangs off the dive kick) |
| III | **Spin finisher** | air K → K | A second, wider aerial spin ending in a chop: 1.8 dmg, 45 poise, 16 stam, 120 / 540. Lands from a vault now (glide) |
| IV | **Double vault** | I in the air near a foe | Vault off the foe's head (or a boss's): refunds the air attacks, once per jump. *v14:* it cancels an air move once that move's hit is out, so it's reachable mid-string |
| V | **Gale** | K with 3 momentum stacks | Spend the momentum: a slow tornado (50 px/s) that strikes at 0.12, 0.38 and 0.64 s, 0.6 each, so a foe 30–50 px in front takes all three (1.8). Ground only; 16 stam. *v14: it used to run off at 120 px/s and miss* |

**Animation reuse:** today's staff set (`st_1`–`st_4`, the `st_heavy` spin, `st_up`, `st_air`, `st_down`, and the
pole-vault down attack). **About 8 new moves:** vault launch, aerial spin, dive kick, low sweep, rising twirl, roll
vault, spin finisher, gale tornado. **v14 tags** (`art/player_v14_reach.py`): `st_rise`, `st_vkick`, `st_air2`,
`st_pdrop`; **v14c:** `st_bvault`, `st_svault`, `st_comet`.

### 3.9 Whip: control the space

**Identity:** a precision spacer. Fight at the very end of the lash, crack the tip for big damage, and drag things
where you want them.

**Mechanic: tip crack and grapple**
- **The tip:** the last **30%** of a lash's reach (*v14: was 25%*; a 24 px band on an 80 px lash) deals **×1.3**
  damage and fills the **crack meter**: +10 for a light, **+20** for a heavy (*v14: was 25*, so a clap takes 5 tipped
  heavies, not 4).
- **You can see the tip (v14):** the drawn whip only reaches ~36 px, so while a lash is out the game draws the rest of
  the chain out to its real reach, with the tip zone glowing and a glint where it snaps.
- **At 100 crack,** your next K (or J K, or J J K) is a **thunderclap**: **2.5 dmg, ×1.3 at the tip (3.25)**, 90 poise, a small
  blast and a stagger. *v14: was 3.2 from any range.*
- **I grapples** (64 px, 14 stamina, 2 s cooldown):
  - a small foe is pulled to you and staggered for **0.6 s** (*v14: was a 1.8 s stagger every 2 s, a permanent lock*);
  - a large foe or hook ring pulls **you** to it; **never bosses** (open question 3);
  - J or K pressed in the grapple's tail (from 0.16 s) leaves it at once for the follow-ups.

**v15 (balance):** attack factor **×1.10**, and **tip hits deal ×1.6 poise** (`WH_TIP_POISE`), so spacing for the tip also
breaks stances (staggers per boss fight with tipped K: 1.9 → 2.1). Boss time to kill 0.99 of the average, damage taken 0.86.

**Strengths:** the longest reach in the game, safe spacing, crowd control, huge damage with good tip accuracy.
**Weaknesses:** **no block**, weak up close (the coil spin helps), damage depends on precise spacing, and the hardest
weapon to master.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Lash | Opener | 0.8 (1.04) | 8 | 9 | 160 / 400 | 2× sword reach (80 px) |
| J K | **Tip flick** (v14c) | Precision builder | tip only: 0.65 | 6 | 7 | 110 / 340 | A fast wrist-snap to the very end of the chain: misses entirely off the tip; a tip hit adds **+15** crack. J: Lash II (J K J). At 100 crack, J K is the thunderclap |
| J J | Lash II | Pressure | 0.8 (1.04) | 8 | 9 | 160 / 400 | |
| J J J | **Whirl lash** | Both sides | 1.1 | 20 | 14 | 260 / 620 | The whole lash, front and back; no tip bonus; finisher |
| J J K | **Trip lash** (v14) | Trip, chain branch | 1.0 (1.3) | 22 | 12 | 200 / 560 | A low crack along the floor; tipped, it trips a small foe. At 100 crack it's the thunderclap instead |
| K | Heavy crack | Main damage | 1.4 (1.82) | 30 | 18 | 300 / 680 | +20 crack on a tip hit. J: wrench |
| K → J | **Wrench** (v14c) | Control at range | tip only: 0.91 | 40 | 10 | 130 / 460 | Haul on the taut chain: a small foe at the tip is dragged in to 30 px and staggered 0.5 s; anything bigger takes the 40 poise |
| hold K | Overhead crack | Long reach | 2.0 (2.6) | 45 | 24 | 180 + 380 charge, then 300 / 600 | 2.4× sword reach (96 px). K must be held from the press (*v14:* a K mash can't trigger it) |
| K at 100 crack | **Thunderclap** | Burst | 2.5 (3.25) | 90 | 20 | 300 / 700 | Small blast and a stagger |
| I | **Grapple** | Pull | – | – | 14 | 300 | 64 px, 2 s cooldown |
| L | Roll | Dodge | – | – | 16 | 420 | |
| L → J | Retreat lash | Kite | 1.0 (1.3) | 10 | 10 | 160 / 420 | Backs off 40 px while it cracks forward: the tip lands where you were |
| L → K | **Coil spin** (v14) | Close-range answer | 0.6 + 0.7 | 26 | 14 | 140 / 520 | The chain whirls round you (both sides, 46 px); the 2nd hit flings small foes out to 64 px, onto the tip |
| air J | Circular lash | Both sides | 0.9 | 12 | 10 | 160 / 380 | |
| air J J | **Skyfall crack** (v14) | Air string | 1.0 (1.3) | 16 | 10 | 150 / 400 | From the circle, a long crack down to the floor ahead: hit grounded foes from the air at range |
| ↑J | Vertical crack | Fliers | 0.9 (1.17) | 14 | 10 | 160 / 380 | Tip flare |
| air ↓J | Down crack | **Pogo** | 0.9 | 12 | 10 | 120 / 320 | Long box below |
| air K | Lash plunge | Plunge | 1.3 | 50 | 16 | – | |
| Art | **Lash** | | | | FP | | |

**Routes (bench):** J J J untipped **1.93/s**, tipped **2.29** · tipped K loop **2.73** · tipped K with thunderclaps
**3.02** at perfect spacing (2.10 up close; was 3.07 from anywhere) · J J K tipped 2.49 · coil-spin loop 1.50 (a reset,
not damage) · v14c (exact-cycle bench, tipped): J K 2.35 (fills crack 1.5× faster per press), K → J 2.37, J J J K
(II) 2.52 · **Per opening:** tipped J J + K ≈ **3.9** from the safest range in the game, or a tipped thunderclap at
3.25. On a real boss (bot) the whip at the tip edges out the Longsword, and takes more hits at that range.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Snap counter** | I within 150 ms of a hit | Lashes the attacker out of its move: the hit is negated, small foes stagger, a boss takes +60 stance. With the grapple on cooldown, arming it costs 6 stamina and it can't be re-armed for 0.5 s (*v14: mashing I used to keep it armed for free*) |
| II | **Reel kick** (v14) | grapple → J | Kick the foe you just reeled in back out to the tip (1.2 dmg, 30 poise, 12 stam, 150 / 460). On a large foe it's the arrival strike: a J pressed while the chain hauls you in is kept |
| II | **Cyclone** (v14c) | J J J K | The whirl keeps turning into two full-length cracks, ahead then behind, **each with its own tip** (0.8 + 0.8, tip 1.04 each; 30 poise, 16 stam, 200 / 640): the spacer caught between two foes. Below II, a late K after J J J is the heavy crack. Not at 100 crack (the K is the clap) |
| III | **Grapple slam** | grapple → K | Pull a small foe in and slam it: 1.6 dmg, 60 poise, 16 stam, 250 / 600, stunned |
| IV | **Double crack** | K → K | A follow-up crack: the heavy crack (1.4), then 1.8 (35 poise, 18 stam, 220 / 550), both with tip bonuses |
| V | **Thousand lashes** | hold J | Keep J held from the lash's start for 240 ms: a held flurry of 8 × 0.45, **tip-only**, so it's a spacing test (32 poise, 20 stam, 80 / 1000). *v14:* mashing never triggers it |

**Animation reuse:** today's whip set (`wh_1`–`wh_3`, `wh_heavy`, `wh_up`, `wh_air`, `wh_down`, the lash physics).
**About 8 new moves:** overhead crack, thunderclap, grapple throw and pull, retreat lash, snap counter, grapple slam,
double crack, thousand lashes. **v14 tags:** `wh_trip`, `wh_coil`, `wh_air2`, `wh_reelkick`; **v14c:** `wh_flick`,
`wh_wrench`, `wh_cyclone`.

### 3.10 Switch Axe: the grinder

**Identity:** a blade that earns its fury. Blade mode is a quick sword whose only job is to fill the Switch Gauge the hard
way; at a full gauge, I morphs it into a chainsaw axe that does the most damage in the game until the gauge runs dry.
Weapon: **Gravegrinder** (base 42, scaling Str B / Dex C, speed 0.86, reach 1.2, stamina 1.3, poise 1.6, armoured;
default art Magma Quake). Built in `web/src/78_mech_saxe.js`; write-up `docs/v15/saxe.md`.

**Trait: the Switch Gauge (0–100), deliberately hard to fill.** Only Blade mode fills it, and only by landing blows on
real foes (props don't count). Each hit index of a move pays once.
- **Gains:**
  - +4 per landed blade hit; **+7 on the beat** (the press came in the last 150 ms of the move before, or up to 80 ms
    after it ended). The beat can only apply to moves reached through a chain (Falling edge, Double slash, Edge rush,
    Hook heave); Rising edge, Phial thrust, Skyward edge and Lunging edge always pay +4, the air edge a flat +4.
  - Edge rush (J J J J): +10, or +13 on the beat.
  - Ratchet cut (II): +3 per tooth (three teeth).
  - Ratchet twist (K K): +12 at the end of the move, only if both bites landed; nothing per bite.
  - **Hone** (hold K): +10/s, rooted and open. The pogo, the plunge and the Morph slash pay nothing.
- **Losses** (Blade mode only):
  - A blade swing that comes out, lands nothing and had a foe within 90 px (60 px vertically) when it swung: −10.
  - Taking damage (any hit that gets through): −25. In Axe mode a hit costs no gauge.
  - Idle bleed: after 2 s without a damaging saxe move, −4/s (not while honing).
- **At 100 the gauge locks:** no losses of any kind, the weapon glows ember and an "I" pulses on the HUD. The Hone
  can't be started while locked (and ends by itself the moment the gauge locks). **I = Morph slash.** I below 100 is a
  dry rev: a sputter and a puff of smoke, nothing else.
- **Axe mode:** the gauge starts at 100 and drains 6/s, plus 4 once per axe move that lands, plus 15/s while grinding
  (21/s in all). Overdrive (IV) cuts every drain by 30%. At 0 the axe **vents**: as soon as you are on the ground and
  free (the current move finishes first; the grind vents at once), it folds back to the blade in a 0.6 s stagger
  ("Vented") in which you can't act, and the gauge is 0.
- **I in Axe mode** (on the ground): **Full Release** at gauge ≥ 40 from Mastery III, otherwise **Morph back**. Both
  empty the gauge to 0 and fold back to the blade without venting. A Full Release cut short by a hit still folds back.
  The gauge doesn't drain during a Full Release.
- **Death, resting or switching weapons** resets everything: Blade mode, gauge 0, unlocked.
- **HUD:** a phial bar right of the stamina bar: amber while filling, white-gold and breathing when locked, red while it
  drains (darker red below 40 once Full Release is unlocked, with a tick at 40). A flash on gain, a red frame on loss,
  and a sword or axe glyph for the form.

**Strengths:** the highest burst in the game once morphed, an armoured Morph slash, a Full Release that empties the gauge.
**Weaknesses:** the gauge fills slowly and drains when you're hit or whiff; the axe is slow and vents you when it runs dry.

Dmg is in multiples of the weapon's attack. Stam is the move's base cost. Every move can be roll-cancelled once its hit
is out, except those marked commit. Launches only lift non-boss, non-elite, non-flying foes.

**Blade mode** (a fast-ish sword, the gauge builder)

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Rising edge | I | 0.9 | 10 | 10 | 140/360 | +4 gauge |
| J J | Falling edge | I | 0.95 | 10 | 10 | 140/360 | +4 (+7 on the beat) |
| J J J | Double slash | I | 0.55 ×2 | 16 | 12 | 160/420 | 120 ms between bites; two gauge hits, +4 (+7) each |
| J J J J | Edge rush | I | 1.3 | 30 | 14 | 220/560 | Finisher; 24 px lunge; +10 gauge (+13 on the beat) |
| J J (pause) J | Ratchet cut | II | 0.6 ×3 | 24 | 14 | 160/600 | Press 110–450 ms after the Falling edge ends (on the ground). Three sawing bites, 120 ms apart, 10 px lunge, +3 gauge a tooth. J: Edge rush. A sooner press is the Double slash |
| K | Phial thrust | I | 1.3 | 28 | 16 | 240/600 | 16 px lunge; +4 gauge. K: Ratchet twist. Held: the Hone |
| K K | Ratchet twist | I | 0.7 ×2 | 30 | 16 | 200/640 | Finisher; 150 ms between bites; +12 gauge if both land, none otherwise |
| J K | Hook heave | I | 1.2 | 34 | 14 | 220/620 | Launches light foes; 12 px lunge; +4 (+7 on the beat). J: Falling edge |
| hold K | Hone | I | – | – | 0 | loop | Comes out of the Phial thrust if K, pressed for that thrust, is still held 190–240 ms in (taps get no delay). +10 gauge/s, rooted; not while locked. Leave with J (Rising edge), L, I (Morph slash, when locked) or by letting go; a hit costs 25 |
| ↑J | Skyward edge | I | 1.0 | 14 | 12 | 160/400 | One arc up over the helm; +4 gauge |
| L | Roll | I | – | – | 16 | 420 | 0.28 s invulnerable, 74 px |
| L → J | Lunging edge | I | 1.1 | 14 | 12 | 140/400 | Long low cut out of the roll, 28 px lunge; +4 gauge. J: Falling edge |
| L → K | Phial thrust (from the roll) | I | 1.3 | 28 | 16 | 240/600 | The plain K thrust out of the roll |
| air J | Air edge | I | 1.0 | 12 | 12 | 150/330 | +4 gauge (never the beat bonus) |
| air ↓J | Pogo | I | 0.9 | 12 | 10 | 100/300 | Same move in both forms; pays no gauge |
| air K | Plunge | I | 1.3 | 45 | 16 | – | The shared plunge, with Blade-mode numbers |
| I (gauge < 100) | Dry rev | I | – | – | – | – | Sputter and smoke, nothing happens |
| I (gauge 100) | **Morph slash** | I | 2.0 | 60 | 0 | 300/700 | Armour vs blows under 35% max HP; commit; slam; finisher; 12 px lunge. The axe locks in at the strike frame and the gauge is set to 100. J: Wild swing, K: Rev thrust |

**Axe mode** (slow, heavy, the chainsaw; this is where the damage is)

The axe moves (J chain, rev thrust, grind, ripping heave, ↑J, air J) have armour against blows under 25% of max HP.
You walk at 75% speed in Axe mode.

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Axe overhead | I | 2.9 | 45 | 16 | 420/920 | Slam; 14 px lunge. J: Wild swing, K: Rev thrust |
| J J | Wild swing | I | 3.2 | 50 | 18 | 400/900 | 16 px lunge |
| J J J | Grinder sweep | I | 0.9 ×5 | 70 | 20 | 360/1100 | Finisher; five chain bites 65 ms apart; 10 px lunge |
| K (or J K) | Rev thrust | I | 0.6 ×4 | 50 | 16 | 300/900 | Four bites 60 ms apart. K: Ripping heave (II). Held: the grind |
| hold K | **Chainsaw grind** | I | 0.28 per bite | 8 per bite | 0 | loop (a bite every 80 ms) | Comes out of the Rev thrust if K, pressed for it, is still held 200–300 ms in. Walk at 30% of full speed; drains 15/s on top of the 6/s. Leave with L or by letting go; at gauge 0 it vents at once |
| K K | Ripping heave | II | 2.6 | 80 | 20 | 420/1000 | Finisher; launches (stronger than the Hook heave); 12 px lunge |
| ↑J | Rising grinder | I | 1.5 | 40 | 16 | 300/760 | The head dragged up off the floor and over |
| air J | Falling cleave | I | 1.4 | 40 | 16 | 200/520 | |
| air ↓J | Pogo | I | 0.9 | 12 | 10 | 100/300 | The blade's pogo (no armour, no drain per hit) |
| air K | Axe plunge | I | 1.8 | 90 | 20 | – | The shared plunge, with Axe-mode numbers |
| L | Heavy sidestep | I | – | – | 18 | 520 | 34 px over 360 ms, 0.22 s invulnerable |
| L → J | Axe overhead (from the sidestep) | I | 2.9 | 45 | 16 | 420/920 | |
| L → K | Rev thrust (from the sidestep) | I | 0.6 ×4 | 50 | 16 | 300/900 | |
| I (gauge ≥ 40) | **Full Release** | III | 3.0–6.0 | 120 | 0 | 500/1500 | Lunge (18 px), eight grinding bites of 0.25 (60 ms apart) and a 1.0 burst at 980 ms, all × (1 + (gauge − 40) / 60): 3.0 at 40, 6.0 at 100. Armour 35%; commit; finisher; reaches 8 px behind. Empties the gauge; the burst folds back to the blade with no vent |
| I (gauge < 40, or before III) | Morph back | I | 1.4 | 40 | 0 | 260/620 | The blade jack-knifes out as a rising cut, 10 px lunge; gauge to 0, Blade mode. J: Falling edge |
| (gauge 0) | Vented | – | – | – | – | 600 | Commit: 0.6 s you can't act; folds back to the blade |

**Routes (bench):** `tools/shots/v15/saxe/bench.js` (dummy, infinite stamina, light-AR dmg/s): blade J J J J **2.48/s**
(main loop; 2.47 on the beat: the beat buys gauge, not damage) · blade K K 2.18 · blade J K 2.25 · axe J J J with the
gauge held full **3.53** · axe rev thrust loop 2.60 · axe K K (II) 2.65 · axe grind 3.24 (drains 21/s). **Gauge fill
0 → 100** on the dummy: J J J J early 6.6 s, on the beat 4.5 s, K K 7.8 s, Hone 10.2 s. **Full 40 s cycle** (fill on the
beat, morph, axe J J J until the vent): rank I 3.02, rank III 2.92 (cashing in 40–52 as a Full Release, no vents),
rank V 3.10. **Real bosses:** the phase 2b balance matrix (`docs/v15/balance.md`, 25 bosses × 3 seeds) puts its time
to kill at 1.00 of the 14-type average, damage taken 1.11, 0.7 staggers per fight; it morphed in about 40% of fights.
In the saxe `bossfight.js` run (4 bosses × 2 seeds) the bot filled the gauge 0–1 times per fight; blade mode alone plays
like a Longsword, and the axe phase lifts the fight when it comes (the Librarian: 50–51 s against 61–64 s for the
Longsword).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Ratchet cut** | J J (pause) J | Press 110–450 ms after the Falling edge ends: three sawing bites (0.6 each, 24 poise, 14 stam, 160/600), +3 gauge a tooth. J: Edge rush |
| II | **Ripping heave** | Axe: K → K | Out of the Rev thrust, the head torn up through the foe: 2.6, 80 poise, 20 stam, 420/1000. Launches |
| III | **Full Release** | Axe: I (gauge ≥ 40) | Lunge, eight bites (0.25) and a burst (1.0), × (1 + (gauge − 40) / 60): 3.0–6.0. 120 poise, armour 35%. Empties the gauge and folds back to the blade without venting. Below III, I in Axe mode is always Morph back |
| IV | **Overdrive** | – | Every axe drain 30% slower: 4.2/s, 2.8 per landed move, and 10.5/s extra while grinding |
| V | **Grinding halo** | Full Release | The burst ends in a ring around you (46 px, 34 px tall): 0.8 dmg, 40 poise, fire; the gauge comes back at 30 (in Blade mode, unlocked) |

**Deviations from the plan:**
- **Tighter gauge economy:** +4 / +7 per hit (plan +6 / +10); Edge rush +10 / +13 (plan +12); Ratchet twist +12 (plan
  +15); Hone +10/s (plan +12/s). The Ratchet cut's +3 a tooth is new. A whiff only costs when a foe was within 90 px;
  the −25 and the idle bleed apply in Blade mode only, never once locked.
- **"4 per chainsaw hit" became 4 once per landed axe move;** the grind pays its 15/s on top instead (per bite it would
  have emptied the gauge in about 1.4 s).
- **Axe damage raised:** overhead 1.6 → 2.9, wild swing 1.8 → 3.2, sweep 0.45 → 0.9 per bite, rev thrust 0.5 → 0.6 per
  bite. The grind went down, 0.35 → 0.28 per bite. At the plan's numbers the axe J J J measured about 1.9 dmg/s, below
  the blade.
- **Morph back and Full Release clear the gauge to 0,** and the Release folds back to the blade with no vent.
- **K and hold K share a start:** the Hone and the grind come out of the Phial thrust / Rev thrust when K is still held
  (190 ms / 200 ms in), so taps have no delay. The Hone can't start while locked.
- **Added:** the axe ↑J (Rising grinder), axe L → J / L → K, blade L → K (the thrust), the blade air J and pogo, and
  mode-dependent plunges (1.3 / 45 / 16 blade, 1.8 / 90 / 20 axe). There is no separate L → K move (the skeleton's
  rank-II `sx_rollk` was dropped). Morph slash armour is 35%, axe-move armour 25%, and the Morph slash chains into the
  Wild swing / Rev thrust.
- **Grinding halo** got numbers: 0.8 dmg, 40 poise, fire, 46 px ring.

**Attack factor:** the Switch Axe has no `WM_AR_TUNE` entry (none in `74_arsenal9.js` or `78_mech_saxe.js`), so its
factor is 1.0: the Gravegrinder keeps base 42.

### 3.11 Close-range Bow: the point-blank hunter

**Identity:** a Monster-Hunter bow fought up close. Chain shots to climb charge levels, step to keep the foe in the
sweet spot, and spend the level on one big shot. Weapon: **Ashstring Recurve** (type `bow`, prefix `bw_`; base 42,
Str E / Dex A, speed 1.15, reach 1.3, stamina 0.85, poise 0.8; default art Backstep Slash).

**Trait: charge levels and the sweet spot**
- **Levels 1–3.** `P.bwLv` is the level banked for the *next* shot.
  - Each quick shot, the dash shot, the recoil shot and the counter shot bank +1 after they loose (J J J = levels 1, 2, 3).
  - A charge step (L) banks +1. At rank I only **one** step between shots banks; Mastery II allows two.
  - Holding K draws from the banked level: the first 120 ms raise and nock the bow, then +1 level every **400 ms**
    (from level 1: level 2 at 520 ms, level 3 at 920 ms of draw).
  - The power shot, the pinning shot, the leaping point-blank and the dive shot **spend** it (back to 1).
  - After **1.5 s** with no bow move and no step, the bank falls back to 1.
- **The sweet spot.** Each arrow measures from where it was loosed to the foe's near edge:
  - 24–64 px: ×1.0.
  - Under 16 px: ×0.7, easing up to ×1.0 between 16 and 24 px.
  - 64–120 px: falls from ×1.0 to ×0.5. Past 120 px: ×0.5.
  - **Point-blank moves** (recoil shot, leaping point-blank, counter shot, dive shot, hollow piercer) take no
    point-blank cut. The arc shot always deals ×1.0.
- **Arrows are real projectiles.** Walls stop them and wards block them. They hit as weapon (melee) hits, through the
  normal damage pipeline (strike hooks, bleed, fire), not as spells.
- **The K rule: tap K plays the route's move, hold K draws.** A release under **110 ms** plays the tap move; a power
  shot needs at least **180 ms** of draw. Tap K from neutral = a power shot at the banked level.
- **Limb deflect (I).** A **150 ms** window on the ground. A **parryable** blow in it is negated (counter XP) and
  answered automatically with the counter shot. An **unparryable** blow is only turned aside: it costs block stamina
  (6 + 0.8 × dmg, guard-scaled), stamina regen pauses 0.8 s, and there is no counter shot. Without the stamina, the
  blow lands.
- **Reading it:** the arrowhead glows by level (cold steel, amber, gold); three HUD arrowheads show the level, with a
  bar for draw progress or the time before the bank gutters; a white glint sweeps the broadhead every 0.55 s while the
  nearest foe ahead (within 90 px) is 24–64 px away.

**Strengths:** safe mid-close range, charge levels that climb through a chain, a limb deflect with a counter shot.
**Weaknesses:** weak far away and too close alike, light poise, and every big shot asks you to stand and draw.

Damage is per arrow in light-AR units, × the sweet spot unless marked pb. Poise is the whole move's total if every
arrow lands.

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Quick shot (`bw_1`) | I | 0.4 ×1/2/3 (arrows = banked level) | 8 per arrow | 9 | 120/340 | Banks +1. J: next quick shot; K tap: arrow stab; hold K: draw |
| J J | Quick shot (`bw_2`) | I | 0.4 ×1/2/3 | 8 per arrow | 9 | 120/340 | Banks +1 |
| J J J | Quick shot (`bw_3`) | I | 0.4 ×1/2/3 (×3 at lv3) | 8 per arrow | 9 | 120/340 | 6 px step; banks +1 |
| J J J J | **Pinning shot** (`bw_pin`) | I | 1.7 | 30 | 12 | 200/520 | Finisher; 8 px step; breaks the stance of small non-elite foes; spends the level |
| hold K | **Draw** (`bw_draw`) | I | – | – | 0 | loop | +1 level / 400 ms after a 120 ms raise, from the bank; walk at 40%, turns with the stick; stamina regen ×0.5. L: charge step banking the drawn level; I: limb deflect |
| release K (≥ 180 ms) / tap K | **Power shot** (`bw_power`) | I | 0.9 / 1.4 / 2.0 (lv1/2/3) | 20 / 35 / 55 | 14 | 70/520 | Level 3 pierces 3 foes; kicks you back; spends the level. Commit, with its own roll-cancel from 260 ms. K within 450 ms after: draw from level 1 |
| lv3 power shot → K tap | **Hollow piercer** (`bw_hollow`) | III | 0.4 ×6 per foe (pb) | 70 | 22 | 360/1100 | One slow arrow (230 px/s, 34 px/s inside a foe) boring through every foe in the line: a bite every 80 ms, up to 6 per foe; commit |
| J → K tap | **Arrow stab** (`bw_stab`) | I | 0.8 (melee) | 16 | 10 | 120/380 | A jab with the nocked arrow, 10 px step. J: back into the volley after the last quick shot; K tap: recoil shot |
| J → K → K tap | **Recoil shot** (`bw_recoil`) | I | 1.2 (pb) | 30 | 14 | 140/520 | Loosed slightly downward; the kick hops you 30 px up and back; banks +1 |
| ↑J | **Arc shot** (`bw_arc`) | I | 0.3 ×3 rising + 0.3 ×5 falling | 40 (+8 per rising arrow) | 16 | 300/760 | The rain lands 40–90 px ahead from 0.3 s after the loose, staggered 45 ms; no sweet-spot scaling. The rising three catch fliers |
| L | **Charge step** (`bw_step`) | I | – | – | 12 | –/300 | 160 ms invulnerable, 40 px. Neutral steps back, a held direction steps that way. Banks +1 (one step between shots at rank I). J from 150 ms, K from 120 ms |
| L L | Double charge step | II | – | – | 12 + 12 | –/300 each | The second step straight out of the first (from 150 ms); both bank, so L L takes level 1 to 3 |
| L → J | **Dash shot** (`bw_dash`) | I | 0.5 + 0.25 × lv, split over lv arrows (0.75 / 1.0 / 1.25) | 16 | 12 | 140/400 | Skid in 22 px; banks +1. J: quick shot `bw_3`; K tap: arrow stab |
| L → K tap | **Leaping point-blank** (`bw_leap`) | I | 0.5 ×3 (pb) | 36 | 16 | 220/600 | Hop in 30 px and loose a fan of three down into the foe; commit; spends the level |
| L → hold K | Step and draw | I | – | – | 0 | loop | The draw starts from the level the step banked |
| I (timed) | **Limb deflect** (`bw_deflect`) | I | – | – | 8 | 150 window / 260 | Ground only. Parryable blow: negated, counter shot. Unparryable: block stamina (6 + 0.8 × dmg, guard-scaled), no counter |
| deflect (auto) | **Counter shot** (`bw_counter`) | I | 1.6 (pb) | 40 | 0 | 80/460 | Counter-hit; invulnerable 0–240 ms; loosed at level 2 or the bank if higher; banks +1 |
| air J | **Aerial shot** (`bw_air`) | I | 0.9 | 12 | 10 | 150/380 | Loosed down at 24°, pushes you back a little; counts toward the 2-per-jump air limit |
| air ↓J | **Talon stomp** (`bw_down`) | I | 0.9 (melee) | 12 | 10 | 100/300 | The lower limb stamped down; pogo off foes and spikes |
| air K | **Hunter's dive** (`bw_dive`) | I | – | – | 16 | loop (≤ 1.2 s) | Replaces the plunge. A 0.1 s beat, then a dive at about 50°; once per jump. Ends on landing, on reaching a foe (< 14 px) or after 1.2 s |
| dive end | **Dive shot** (`bw_diveshot`) | I | 0.5 ×3 (pb) | 36 | 0 | 60/460 | A point-blank fan; bounces you up if it fires before landing; spends the level |

**Routes / balance** (bow bench `tools/shots/v15/bow/bench.js`, 12 s per route, real presses, infinite stamina, foe at
44 px unless noted): J J J J **2.59/s** (the main loop) · point-blank (14 px) 1.81 · far (110 px) 1.63 · J J J → hold K
(lv3 power from the bank) 2.56 · L → hold K step-cancel loop 2.16 · L L → hold K (II) 2.33 · J K K at 26 px 2.29 · L → J
loop 2.06 · L → K tap at 26 px 1.47 · lv3 power → hollow piercer (III) 1.41 on one foe · hold K lv3 loop 1.33 · K tap
loop 1.20 · arc shot at 64 px 1.12. Against real bosses (phase 2b balance matrix, 25 bosses, bot at 36 px on J J J J
with the limb deflect): time to kill **0.95** and damage taken **0.95** of the 14-type average (0.67 / 0.65 before the
deflect fix).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Double charge step** | L L | A second charge step straight out of the first (from 150 ms into it, 12 stam each). Two steps between shots both bank, +1 level each |
| III | **Hollow piercer** | lv3 power shot → K tap | One slow drilling arrow through everything in a line: 0.4 per bite, a bite every 80 ms, up to 6 per foe, 70 poise, point-blank, 22 stam, 360/1100 |
| IV | **Arc shot ×7** | ↑J | The arc shot looses seven falling arrows instead of five (0.3 each, the 40 poise shared between them) |
| V | **Point-blank burst** | – (lv3 shot < 20 px) | A level-3 arrow landing with the foe's near edge under 20 px away bursts through: +0.6 dmg, 20 poise, and it hits up to 30 px behind the foe |

**Deviations from the plan:**
- Quick shots 0.35 → **0.4** per arrow, and the pinning shot 1.3 → **1.7**, so J J J J (about 2.6/s) stays the main
  loop with J J J → draw (lv3 power 2.0) just under it.
- Power shot wind 160 → **70 ms** after release (the draw is the wind-up; at least 180 ms of draw), and it is a
  **commit** with its own roll-cancel from 260 ms, so the shot → charge step loop can't outrun the main loop.
- **K is tap/hold everywhere**: J → K tap is the arrow stab, J → hold K the draw; the same for stab → K, L → K and
  lv3 power → K (the hollow piercer).
- The **charge step** steps *back* when neutral, and at rank I only one step between shots banks (otherwise Mastery
  II's L L would mean nothing).
- The **dash shot** scales with the banked level (0.5 + 0.25 per level; 1.0 at level 2 as planned).
- The **arc shot** adds three rising arrows that hit fliers.
- **Hunter's dive** replaces the shared plunge: a dive at about 50° ending in a point-blank fan of 3 × 0.5.
- The **hollow piercer** bores through each foe in turn (6 bites per foe), rather than a single 0.4 ×6 line.
- The **limb deflect** only fully counters parryable blows (v15 balance phase 2b, the Katana's Iai rule); unparryable
  blows cost block stamina with no counter shot. Before this the counter shot was the bow's top damage source.
- The **counter shot** gained 0–240 ms invulnerability; the burst applies to every level-3 arrow inside 20 px.

**Attack factor:** no `WM_AR_TUNE` entry is set for `bow` (neither in `74_arsenal9.js` nor in `78_mech_bow.js`), so its
factor is **1.0** and the Ashstring Recurve keeps base 42.

### 3.12 Martial Arts: two styles, one body

**As built (v15):** `fist` / prefix `ft_`, weapon **Penitent's Knuckles** (base 42, STR C / DEX B, speed 1.35, reach 0.7,
stamina 0.75, poise 0.9), default art **Bloodstep**. Code: `web/src/78_mech_fist.js`; write-up: `docs/v15/fist.md`.

**Identity:** two styles in one body. **Swift** is fast, light and evasive; **Iron** is slow, rooted, armoured and breaks
stance. The skill is crossing between them in the middle of a combo, so a chain can run Swift → Iron → Swift.

**Mechanic: Swift and Iron** (the style is `P.ftStyle`)
- **Swift:** quick hands and kicks, guard high. L is the **slip step**: 8 stamina, 240 ms, 0.18 s invulnerable, 46 px.
  A blow met in the **first 120 ms** of the slip is a **perfect slip**: +1 Flow and a brief slow-motion flash (and at
  rank III the Flowing counter).
- **Iron:** walks at **82%** speed. Every Iron move is **armoured during its wind-up** (until its hit time): a blow under
  **20% of max HP** doesn't flinch it. The shoulder charge, the shoulder bash, the iron fist charge and the iron fist
  itself are armoured **all the way through**. The Falling star counts as an Iron move (armoured wind-up); the diving
  elbow and the Tempest to mountain are not armoured. L is the **iron step**: 12 stamina, 340 ms, 0.16 s invulnerable,
  30 px, with no perfect slip. Iron's J J J chain deals 124 poise against Swift's 37.

**Mechanic: the switch and the Shift strike**
- **I from neutral** (on the ground) changes style with a **300 ms flourish** (0 stamina). **I in the air** changes style
  instantly.
- **I during a ground move is a Shift strike.** The press is taken from **30 ms** into the move and fires **50 ms after
  the move's first hit**, cancelling the rest of it into the other style's linking blow at **×1.15** damage:
  - any Swift ground move → **Falling star** (Iron heel drop); J carries on with the Iron chain (elbow), K is the hammer
    fist;
  - any Iron ground move → **Wind cut** (four Swift blows); J carries on with the Swift chain (cross), K is the snap
    kick.
  - On a multi-hit move (knee rush, roundhouse, whirlwind) the cancel comes after the first hit, so the later hits are
    given up.
  - **Late Shift:** an I pressed up to **150 ms after a move ends** still shifts out of it.
  - An I pressed behind an already-queued J or K belongs to the move that press starts (a fast `J J I` shifts out of the
    cross). A J or K already queued behind the I plays after the Shift strike (`J J J I K`).
  - The Shift strikes themselves, the holds, the air moves, the Tempest, the release and the Ember palm can't be
    shifted. I mid-move on such a move is dropped, except in its last 150 ms, where it stays buffered as a style change.
  - A Shift needs stamina above 0; the linking blow costs its own stamina (14 / 12).
- **Flow** (5 pips, shared by both styles): **+0.5** for a move that lands (once per move), **+1** for a Shift strike or
  the Flowing counter, **+1** for a perfect slip, **+0.08** per Hundred-fists hit. After **6 s** without gaining Flow it
  drops to the pip below every **1.5 s**.
  - **Ranks I–IV: Ember shift.** A Shift strike made at 5 Flow ignites: **×1.3** instead of ×1.15, plus a 3 s burn
    (0.08 light AR per second), and it spends all the Flow.
  - **Rank V:** the Flow is kept instead; **hold I** in neutral for 220 ms spends it on the **Ember palm**. A tap of I
    still changes style.
- A landed Shift strike and a perfect slip each count toward Weapon Mastery.
- **Feedback:** a ring of light in the new style's colour on a change (Swift steel-blue, Iron ember) with its own sound;
  an afterimage of the old style on each Shift; an ember glow at the knuckles in Iron; smouldering wraps at full Flow; a
  short orange aura when the armour soaks a blow; the iron fist charge brightens with a glint at each level.
- **HUD** (right of the stamina bar): a style glyph (Swift a pale double chevron, Iron an ember block) and the 5 Flow
  pips, which pulse when full; at rank V a ring shows the palm is ready.

**Strengths:** the most moves of any weapon, the fastest strikes, armoured Iron blows, combos that cross styles.
**Weaknesses:** the shortest reach, low damage per hit in Swift, and the style dance is a lot to learn.

**Swift style**

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Jab | I | 0.5 | 4 | 6 | 80 / 220 | 6 px. J: cross; K: rising knee |
| J J | Cross | I | 0.55 | 5 | 6 | 80 / 220 | 8 px. J: hook (or the backfist, II); K: whirlwind kick |
| J J J | Hook | I | 0.65 | 8 | 7 | 100 / 260 | J: knee rush. I here, then K, is the Tempest to mountain (III) |
| J J J J | Knee rush | I | 0.4 ×3 | 20 | 10 | 120 / 480 | Finisher: three driving knees 95 ms apart, 24 px drive |
| J J (pause) J | Spinning backfist | II | 0.9 | 14 | 8 | 140 / 400 | Press 110–300 ms after the cross ends (sooner is the hook). Reaches 10 px behind. J: knee rush |
| K | Snap kick | I | 0.9 | 12 | 9 | 140 / 380 | 8 px. K: double roundhouse; J: cross |
| K K | Double roundhouse | I | 0.6 ×2 | 20 | 12 | 160 / 560 | Finisher; kicks 200 ms apart, the second higher |
| J K | Rising knee | I | 0.8 | 14 | 9 | 120 / 380 | A small hop, 12 px; launches light foes. J: cross |
| J J K | Whirlwind kick | I | 0.5 ×2 | 18 | 11 | 160 / 520 | Finisher; spins, hits both sides, 140 ms apart |
| hold K | Hundred fists | II | 0.15 every 65 ms | 2 per hit | 4 + 16/s | loop | Held 130 ms to start (released sooner: the snap kick, with no added delay). Up to 3 s; stops on release or at 0 stamina; stamina doesn't regenerate while it runs |
| ↑J | Rising uppercut | I | 0.8 | 16 | 9 | 120 / 400 | Launches light foes, reaches fliers |
| L | Slip step | I | – | – | 8 | 240 | 0.18 s invulnerable, 46 px. Perfect slip in the first 120 ms: +1 Flow |
| L → J | Shadow jab | I | 0.8 | 10 | 8 | 100 / 320 | 20 px dash-in. J: cross |
| L → K | Sliding sweep | I | 0.9 | 22 | 10 | 140 / 460 | Finisher; 26 px low slide; trips (breaks the stance of) non-elite small foes |
| L (perfect) → J | Flowing counter | III | 1.4 | 30 | 6 | 80 / 400 | Counter, finisher, 20 px, +1 Flow. J during a perfect slip fires at once, turned to the nearest foe within 90 px |

"Light foes" are non-boss, non-elite, non-flying foes; a launch also breaks their stance.

**Iron style**

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Iron palm | I | 1.1 | 30 | 12 | 260 / 560 | 10 px. J: elbow; K: grapple throw |
| J J | Elbow drive | I | 1.2 | 34 | 12 | 260 / 560 | 10 px. J: shoulder charge; K: pillar kick |
| J J J | Shoulder charge | I | 1.6 | 60 | 16 | 320 / 740 | Finisher; armoured all the way through; 28 px |
| K | Hammer fist | I | 1.5 | 50 | 16 | 340 / 800 | Both fists overhead. K: mountain stomp; J: elbow |
| K K | Mountain stomp | I | 1.0 + 0.6 | 40 + 30 | 18 | 360 / 900 | Finisher; the 0.6 / 30 is a shockwave around you (34 px radius, both sides) |
| hold K | Iron fist | I | 1.8 / 2.6 | 60 / 90 | 20 | charge, then 160 / 620 | Levels at 320 / 900 ms held; fires on release or at 2.5 s. Turnable while charging; charge and blow armoured through; 18 px dash. Released before 320 ms: the hammer fist (no added delay). Counts as a charge for Charged Arts |
| J K | Grapple throw | I | 1.6 | 50 | 16 | 240 / 800 | Finisher. A small foe (not a boss, elite or flier) is heaved 18 px behind you, stance broken; not if a wall is there. A boss just takes the palm |
| J J K | Pillar kick | I | 1.4 | 50 | 16 | 300 / 760 | Finisher; a heel straight up (tall box); launches light foes |
| ↑J | Heaven's uppercut | I | 1.3 | 40 | 14 | 300 / 700 | Launches light foes |
| L | Iron step | I | – | – | 12 | 340 | 0.16 s invulnerable, 30 px; no perfect slip |
| L → J | Iron palm | I | 1.1 | 30 | 12 | 260 / 560 | The palm out of the step; J J carries on with the Iron chain |
| L → K | Shoulder bash | I | 1.2 | 50 | 14 | 200 / 560 | Finisher; a 30 px armoured dash |

**Switching and shared**

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| I (neutral) | Change style | I | – | – | 0 | 300 / 300 | Swift ⇄ Iron flourish (`ft_toiron` / `ft_toswift`). In the air: instant |
| I mid-combo | Shift strike | I | ×1.15 | – | – | fires 50 ms after the hit | Cancels any ground move of a style into the other style's linking blow (the next two rows). Up to 150 ms late still counts |
| Swift move → I | Falling star | I | 1.4 (×1.15) | 50 | 14 | 260 / 640 | Iron heel drop out of a hop; armoured wind-up; +1 Flow. J: elbow; K: hammer fist |
| Iron move → I | Wind cut | I | 0.28 ×4 (×1.15) | 20 | 12 | 120 / 520 | Four Swift blows 70 ms apart, 14 px; +1 Flow. J: cross; K: snap kick |
| Shift at 5 Flow | Ember shift | I | ×1.3 | – | – | – | Ranks I–IV only: the Shift strike burns (3 s) and spends all the Flow |
| Swift J J J → I → K | Tempest to mountain | III | 0.3 ×4 + 1.0 | 60 | 18 | 100 / 900 | Finisher. Only when the Falling star came out of the hook; 4 Swift blows 90 ms apart, then the Iron hammer fist (2.2 total). Not armoured |
| Iron hold K → I | Iron to wind release | IV | 1.2 / 1.6 / 2.2 | 30 / 45 / 70 | 10 | 90 / 480 | By charge level (none / 1 / 2). A 46 px dash-punch through the foe, invulnerable 0–140 ms; finisher; ends in Swift. J: cross |
| hold I (5 Flow) | Ember palm | V | 3.0 | 120 | 0 | 380 / 900 | Hold I 220 ms in neutral; the palm's clock then starts at 110 ms (270 ms to the hit). Commit; armour vs blows under 30% max HP; a 4 s burn (0.1 light AR per second); empties the Flow; 16 px |
| Swift air J | Air kick | I | 0.7 | 10 | 8 | 110 / 300 | J (still airborne): triple air kick |
| Swift air J J | Triple air kick | I | 0.3 + 0.3 + 0.4 | 15 | 10 | 100 / 440 | Kicks 80 ms apart; the fall is held to 35 px/s so all three land from a hop |
| Iron air J | Diving elbow | I | 1.2 | 34 | 12 | 160 + dive / 560 | Hangs 160 ms, then dives at a slant (150 px/s forward, 300 down) to the floor. A foe met on the way: bounce off it; else the impact lands on touchdown. Counts toward the air limit |
| air K | Diving heel | I | 1.3 | 50 | 14 | 150 + dive / 620 | Both styles; replaces the plunge. A steep dive (110 forward, 430 down), same bounce or landing impact. Counts toward the air limit |
| air ↓J | Stomp | I | 0.8 | 12 | 8 | 100 / 280 | Both styles; pogo off foes and spikes |

The dives hold their dive frames until you land, then play the impact frames to the total (260 ms after landing for the
elbow, 300 ms for the heel).

**Routes / balance** (`tools/shots/v15/fist/bench.js`: training dummy, infinite stamina, real inputs, 12 s per route;
light-AR units, so the ×0.92 attack factor doesn't change them): Swift J J J J **2.41/s** (main loop) · Shift dance
J, (J I)… **2.79** (the skill ceiling, 44 stamina a cycle) · Iron J → I → J J J 2.64 · Tempest J J J → I → K (III) 2.50
· Swift K J J J 2.38 · Swift J J → I → J J 2.31 · Swift K K 2.17 · Hundred fists (II) 2.09 · Iron J J J 2.04 · Swift
J K / J J K 2.01 / 2.01 · Iron J J K / J K 1.94 / 1.93 · Iron K K 1.77 · Iron hold K level 2 loop 1.17 (hold time
counted; 2.6 in one hit inside an opening). **Boss bench** (Gravetusk, a bot swinging inside the 1.3 s opening and
rolling each swing): Iron J J J 1.51, Shift dance 1.22, Swift J J J J 0.82; Swift is caught mid-chain while Iron's
armour soaks the swing. **Real-boss bot** (`docs/v15/balance.md` phase 2b, 25 bosses, route J I J J J): time to kill
**0.92** of the 14-type average, damage taken **1.21**, 2.4 staggers per fight. It trades safety for its big hits.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Spinning backfist** | Swift: J J (pause) J | Press the third J 110–300 ms after the cross ends: a full turn into a backfist (0.9, 14 poise, 8 stam, 140 / 400). J: knee rush |
| II | **Hundred fists** | Swift: hold K | Held past 130 ms: a jab storm, 0.15 every 65 ms (2 poise each), 4 stamina to start then 16 a second, up to 3 s. A tap stays the snap kick |
| III | **Flowing counter** | Swift: L (perfect) → J | Slip a blow in the slip's first 0.12 s, then J: a 1.4 counter palm (30 poise, 6 stam, 80 / 400), out at once and turned to the foe |
| III | **Tempest to mountain** | Swift: J J J → I → K | K after a Falling star that came out of the hook: four Swift blows into an Iron hammer fist, 0.3 ×4 + 1.0 = 2.2 (60 poise, 18 stam) |
| IV | **Iron to wind release** | Iron: hold K → I | Let the charge go as a Swift dash-punch through the foe: 1.2 / 1.6 / 2.2 (30 / 45 / 70 poise) by charge level, 10 stam, 46 px, invulnerable for 140 ms; you end in Swift |
| V | **Ember palm** | hold I (5 Flow) | Spend all the Flow on one burning palm: 3.0 dmg, 120 poise, 4 s burn, 30% armour, commit. From V the Ember shift no longer fires (the Flow is kept for the palm) |

**Animation:** 43 new tags (`art/player_v15_fist.py`), including the two stances' idles and walks (`ft_sw_idle`,
`ft_sw_run`, `ft_ir_idle`, `ft_ir_walk`), the two dodges, the two holds and the two flourishes; the far hand carries the
second knuckle, and kicks use real IK legs. No move borrows another type's tag.

**Deviations from the plan:**
- **Knee rush:** 0.35 ×3 → **0.4 ×3** (the main loop rose from 2.33 to 2.41 dmg/s).
- **Hundred fists:** 0.2 every 60 ms at 14 stamina/s → **0.15 every 65 ms** at **16/s** (plus 4 to start), capped at
  3 s. At plan rates it ran 3.3 dmg/s, above every main loop; now 2.09.
- **Iron chain totals tightened:** palm and elbow 600 → **560**, shoulder charge 760 → **740** (1.99 → 2.04 dmg/s).
- **Shift strikes toned down:** Falling star 1.5 → **1.4**, Wind cut 0.3 ×4 → **0.28 ×4** (with 20 poise, 12 stam,
  120 / 520, which the plan didn't give). The alternating dance would otherwise run about 3.0 dmg/s.
- **The Shift is wider than the plan's two examples:** every Swift or Iron ground move can shift, not only Swift J J
  and Iron J; the cancel comes 50 ms after the hit, and a press up to 150 ms late still counts. I in the air is an
  instant style change.
- **Ember shift (new, ranks I–IV):** in the plan Flow did nothing before rank V; now a full gauge ignites the next
  Shift strike (×1.3 and a burn). At V the Flow is saved for the Ember palm. Flow rates and fading are new detail.
- **Tempest to mountain** is its own move reached as Falling star → K, only when the star came out of the hook; from
  any other move K after the star is the plain hammer fist.
- **Mountain stomp poise** is split 40 on the stamp + 30 on the shockwave (the plan's 70 in total).
- **Perfect slip** is defined as the first 120 ms of the slip and gives +1 Flow; the Flowing counter goes out at once
  from inside the slip.
- **New routes:** snap kick → J (cross), hammer fist → J (elbow), Iron L → J (palm), the backfist → J (knee rush), the
  release → J (cross); an Iron K tap is the hammer fist with no charge delay.
- **The air moves:** the diving heel replaces the plunge as air K in both styles; the diving elbow is Iron's air J;
  both bounce off a foe met in the air. The triple air kick holds the fall. The plan gave no numbers for the air moves,
  the release, or the Iron fist's timing; those are all as built above.
- **Ember palm:** 3.0 / 120 poise as planned, plus commit, 30% armour and a 4 s burn.
- **Move list:** the plan counted 33 entries; the in-game list has **32** (the code has 39 move rows, counting the
  hold states `ft_khold`, `ft_ichg`, `ft_ihold` and the two flourishes).
- **Weapon art:** the default Bloodstep is kept; no new art was made.
- **Attack factor:** `WM_AR_TUNE.fist = 0.92` (set in `78_mech_fist.js`, balance phase 2b), so the Knuckles' attack is
  42 → 38.6. On the real-boss bot the shift route was 16% faster than the 14-type average (0.84–0.86); it now sits at
  0.92.

### 3.13 Scythe: the reaper

**Identity:** wide arcs that cut in front and behind, a hooked tip that drags small foes in instead of knocking them
away, souls harvested with the far edge of the blade, and a hook step that swings you round to the foe's back. You play
the blade's length: stand where the far edge lands, gather souls, and spend them on one great Reap.

Weapon: **Requiem** (`requiem_scythe`), 42 AR, scaling Str C / Dex C / Fth E, speed 0.95, reach 1.35, stamina 1.05,
poise 1.1, **bleed 10** (the scythe's hits build bleed natively). Default art: **Reap** (`art_reap`). Code:
`web/src/78_mech_scythe.js` (prefix `scy_`, globals `scy*` / `SCY_*`).

**Mechanic: front and back.** Every arc also cuts behind you.
- The J reaps (low reap, high reap, harvest moon) cut 10–12 px behind you; the backstab reap 6 px.
- The turning harvest, pendulum, scything spiral, both crescents, the charged crescent, the Reap, the leg sweep and the
  air arc are full spins: 40–48 px behind.
- Reach is set per move (40–52 px in front), not read from the art.

**Mechanic: the hooked tip.**
- A **far-edge** hit (see souls below) on a **small foe** drags it 8 px toward you instead of letting it fly off. The
  drag stops at the sweet spot (half the move's reach plus half the foe's width), so the next swing still meets it with
  the far edge. Walls stop the drag.
- "Small foe": not a boss, elite, flier or prop, and a hurtbox no wider than 28 px and no taller than 44 px.
- **J K, the hook pull,** drags a small foe 30 px in (to 14 px from you) and, if it isn't already staggered, breaks its
  stance for at most 0.45 s, so the J that follows lands. Its far-edge drag is replaced by this pull.

**Mechanic: souls** (max **3**, shown as violet wisps orbiting the blade's head, and as three flames on the HUD)
- **Harvest:** a hit with the **far half of the arc** harvests one soul, **once per move**. Far half means the target's
  near edge is at least **45%** of the move's reach away, on whichever side it was struck. For ↑J it is the same 45% of
  the move's height above you; the air ↓J pogo always counts as far. A hit on the haft, up close, harvests nothing.
- The Reap itself harvests nothing.
- **Fade:** souls fade one at a time after **15 s** with no harvest; after the first fades, the next goes 2.5 s later,
  and so on. A harvest (even at 3 souls) resets the timer. The wisps flicker in the last 3 s, and a thin HUD line under
  the flames counts down.
- **Scatter:** a blow that lands on you scatters one soul. Negated blows, armoured blows, zero-damage hits and hits
  during i-frames don't.
- The HUD flames and the wisps turn white once the Reap would hit at full strength (3 souls; 2 from Mastery IV).

**Mechanic: hold K**
- **With souls: the Reap.** K still held 170 ms into the wide crescent (up to 270 ms) turns it into the Reap, which
  spends **every** soul: **1.6 / 2.4 / 3.2** damage and **50 / 70 / 90** poise for 1 / 2 / 3 souls, cutting front
  (52 px) and back (48 px). Hold K is the Reap everywhere: out of J K or J J K, K still held from the press 150–200 ms
  into the hook pull or spiral (with souls) also becomes the Reap. A tapped K stays the route. The Reap's stamina is 18
  in all, whichever move it grows out of (the starting move's cost plus the rest).
- **With no souls: the charged crescent.** The hold becomes a charge (you slow to a stop); at **0.5 s** the blade
  gleams and a star shows. Release when full for the charged crescent (2.0, 50 poise). Release early and the wide
  crescent resumes from its 170 ms mark at no extra cost. The charge releases by itself at 1.6 s.

**Mechanic: I = Hook step** (14 stamina, 120 / 380, commit: no roll-cancel)
- Aims at the nearest foe ahead: its near edge between -10 and 64 px in front, roughly level (its centre no more than
  60 px above your feet, its bottom no more than 34 px above them).
- The blade catches behind it and you swing round (90–300 ms into the move) to land **11 px past its far edge**,
  turned to face it at 250 ms. You are **invulnerable for 0.3 s** from the start, and shades of the reaper trail the swing.
  The travel is as wide as the foe (about 55 px round a small foe, about 130 px round Gravetusk); it is the type's
  deliberate dash and is exempt from the 36 px lunge rule.
- **Bosses** (and boss parts) can only be hooked from Mastery III.
- If there is nothing to hook, or the landing spot is a wall, a gap or blocked on the way, it is a short **hooking step**
  of up to 26 px (stopped by walls) with **no i-frames**.
- Out of it: **J** = backstab reap (Mastery II), **K** = neutral K (wide crescent, or hold for the Reap / charge).
- With no stamina left, I is refused.

**Strengths:** hits both sides, pulls small foes in, a hook step behind the foe, a soul-fed burst.
**Weaknesses:** slow to recover, weak right up close, and the Reap is only as strong as the souls you gathered.

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Low reap | I | 0.9 | 10 | 10 | 160/360 | Reach 44 front / 12 behind. J: high reap; K: hook pull |
| J J | High reap | I | 0.95 | 12 | 10 | 160/360 | 44 / 12. J: turning harvest; K: scything spiral; J after a pause: pendulum (II) |
| J J J | Turning harvest | I | 0.65 ×2 | 20 | 12 | 200/540 | Ahead, turn, behind (44 / 40, 150 ms between hits). J: harvest moon |
| J J J J | Harvest moon | I | 1.7 | 40 | 14 | 280/680 | Finisher, great overhead moon (46 / 10). Mashing J stops here |
| J J (pause) J | **Pendulum** | II | 0.7 ×2 | 24 | 12 | 180/560 | J 110–450 ms after the high reap ends (on the ground, ↑ not held): out ahead, then behind (44 / 40, 170 ms apart). J: harvest moon |
| J K | **Hook pull** | I | 0.8 | 20 | 12 | 200/560 | Reach 46. Drags small foes 30 px in, breaks their stance (≤ 0.45 s). J: high reap. K held 150 ms with souls: the Reap |
| J J K | Scything spiral | I | 0.45 ×3 | 30 | 14 | 220/700 | Three turns round you (42 / 42, 130 ms apart); finisher. K held 150 ms with souls: the Reap |
| K | Wide crescent | I | 1.3 | 30 | 16 | 280/680 | One flat arc ahead and behind (48 / 42), 10 px lunge. K: twin crescent; hold: Reap or charge |
| K K | Twin crescent | I | 0.8 ×2 | 40 | 18 | 260/760 | Round and back again (46 / 42, 200 ms apart); finisher |
| hold K (no souls) | **Charged crescent** | I | 2.0 | 50 | 16 + 4 | hold 0.5 s, then 240/720 | Soul-light crescent (50 / 46), 12 px lunge, finisher. Early release: the wide crescent from 170 ms |
| hold K (souls) | **Reap** | I | 1.6 / 2.4 / 3.2 | 50 / 70 / 90 | 18 total | hold 170 ms, then 320/1000 | Spends every soul; 52 / 48, 12 px lunge, finisher. Also out of J K / J J K (K held) |
| ↑J | Rising harvest | I | 1.0 | 20 | 12 | 180/460 | Blade swept up overhead (art box); launches small non-flying foes (200) and breaks their stance |
| I | **Hook step** | I (bosses III) | – | – | 14 | 120/380 | Swing round behind the nearest foe ahead (64 px), invulnerable 0.3 s; whiff: 26 px step, no i-frames. Commit |
| I → J | **Backstab reap** | II | 1.6 | 40 | 10 | 120/480 | Cut into its back (44 / 6); finisher |
| L → J | Ghost slash | I | 1.0 | 14 | 12 | 140/420 | 44 px reach, 24 px lunge, leaves your shade. J: high reap |
| L → K | Leg sweep | I | 1.1 | 30 | 14 | 200/560 | Low turn at the ankles (40 / 40, 18 px tall), turns to the held direction; trips small foes (stance break); finisher |
| air J | Air arc | I | 0.9 | 12 | 10 | 150/380 | Full circle (40 / 40). J: crescent dive; ↓J: pogo; ↑J: rising harvest |
| air J J | Crescent dive | I | 1.2 | 20 | 12 | 150/480 | Hangs 110 ms, then dives to the floor at a slant (380 down, 90 forward) and lands planted. Counts as an air attack |
| air ↓J | Grave pogo | I | 0.9 | 12 | 10 | 100/300 | Blade hooked under your feet: pogo; always a far-edge hit |
| air K | Grave plunge | I | 1.5 | 70 | 18 | – | The shared plunge with its own fall tag (`scy_plunge`); smash limit |

Damage is in multiples of AR; poise is for the whole move; Wind/Total in ms. Stamina "16 + 4" is the K press plus the
charge release; the Reap's "18 total" is the starting move's cost topped up to 18.

**Routes / balance:** `bench.js` (still target, infinite stamina, 12 s, dmg/s in AR): J J J J **2.50** (far edge, 38 px;
the same at 24 px with no souls) · J J J + hold K Reap **2.65** · J J J J + Reap 2.68 · Mastery IV J J + Reap 2.68 ·
J J K spiral 2.20 · J K hook pull 2.00 · K / K K 2.04 · charged crescent loop 1.33 · pendulum route (II) 2.21 · hook
step → backstab loop (II) 1.87. The main loop and the Reap route sit inside the 2.4–2.8 band; every other route is
below the main loop. **Boss bench** (Gravetusk held in place, swinging every 2 s, real stamina): J J J J **0.89**
(Longsword 0.99, Whip 0.95, Greatsword 0.98, Staff 0.75); there, stamina rarely leaves room for a Reap, so in practice
it is a punish, not a loop. **Phase 2b bot** (25 bosses, route J J J + hold K Reap at 16 px, roll for defence): time to
kill **1.05** of the 14-type average, damage taken **0.93** (one of the safe types), 0.8 staggers per fight. Skill
notes: Bloodthirst adds only +6 per light hit's worth on the scythe (it already bleeds; was -27% time to kill, now
-14%); Blade Dancer is a strong node here (-16%).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Pendulum** | J J (pause) J | Press J 110–450 ms after the high reap ends (on the ground): out ahead, then back behind you. 0.7 ×2, 24 poise, 12 stam, 180/560. J: harvest moon |
| II | **Backstab reap** | I → J | Out of the hook step, a reaping cut down its back: 1.6, 40 poise, 10 stam, 120/480, finisher |
| III | **Grave hook** | I near a boss | The hook step catches bosses (and boss parts) too: swing round behind them, invulnerable 0.3 s |
| IV | **Lean harvest** | hold K (2 souls) | Two souls already reap at full strength (3.2, 90 poise); the flames turn white at 2 |
| V | **Requiem** | hold K (souls) | A Reap that connects restores 2% of max HP for every soul spent (rounded), once per Reap |

**Deviations from the plan:**
- **Low and high reaps recover at 360 ms** (plan: 400), the **turning harvest is 0.65 ×2 at 200/540** (plan: 0.6 ×2,
  200/560), and the **harvest moon is 1.7 at 280/680** (plan: 1.5, 300/720). At the plan's numbers the main loop
  measured 2.19–2.37, under the 2.4 floor.
- **The Reap recovers in 1000 ms** (plan: 900). With 900 the Mastery IV J J + Reap loop measured 2.94.
- **Hold K means the Reap everywhere:** K held 150 ms into the hook pull or the spiral (with souls) becomes the Reap; a
  tapped K stays the route. The plan only had hold K from neutral.
- **The far half is defined** as the target's near edge past 45% of the move's reach, either side, once per move.
- **Added rules not in the plan:** souls fade after 15 s without a harvest (then one every 2.5 s), and a blow that lands
  on you scatters one. Souls can't be banked before a boss door, and taking hits costs you the Reap.
- **The far-edge drag** is 8 px and stops at the sweet spot, so the hook never pulls a foe onto the haft.
- **The hook pull** also breaks a small foe's stance briefly (0.45 s) so the follow-up J lands.
- **Hook step** is 120/380 (plan: 360 total), with 0.3 s of invulnerability, landing 11 px past the foe's far edge; a
  whiff is a 26 px step without i-frames. Its travel scales with the foe's width and is exempt from the 36 px rule.
- **Charged crescent** got concrete timings: full at 0.5 s, then 240/720, stamina 16 + 4; early release falls back to
  the wide crescent.
- **Air K** is the shared plunge (1.5 / 70 / 18) with its own fall tag, not a separate grave-plunge move.
- **Reach is set in the move rows** (44–52 px in front) instead of measured from the art, so the scythe out-reaches the
  Longsword.
- The weapon keeps the default **Reap** art; there is no new FP skill.

**Attack factor:** no `WM_AR_TUNE` entry is set for `scythe` (neither in `74_arsenal9.js` nor in `78_mech_scythe.js`),
so its factor is **1.0** and Requiem keeps its 42 base AR.

### 3.14 Warbell: the tolling bell

**Identity:** a slow, blunt bell that keeps score. Every blow that lands rings a note; the order you ring them in
decides which buffs a Perform will give you. You choose your buffs by how you fight, then spend a beat to toll them.

**Weapon:** Dirgebell (`dirge_bell`, type `bell`, move prefix `wb_`): base AR 42 before the attack factor (47.0 after
×1.12, see below), scaling Str A / Fth D, speed 0.8, reach 1.1, stamina 1.35, poise 1.8, armoured. Default art: War Cry.

**Trait: notes, tolls, Perform**
- **Notes.** A blow that **lands** rings one note into a 3-note staff (HUD); when a 4th note rings, the oldest falls off.
  J blows ring **Ash** (white), K blows ring **Ember** (crimson), the up J (peal uppercut) rings **Gold**. One note per
  move (on its first hit to land), except the double slam, which rings one Ember per hit. A whiff rings nothing, and
  props don't count. Perform and Encore ring no note. Each note has its own bell pitch (Ember G3, Ash D4, Gold B♭4).
- **Tolls.** A toll is a run of notes in the staff, oldest to newest, in that exact order (Ember Ash is not Iron hymn).
  A full staff can hold two tolls at once (Ash Ash Ember = Swiftness + Iron hymn; Ash Ember Ember = Iron hymn + Fury).
  Mending (3 notes) only counts from Mastery II.
- **I = Perform** (on the ground, needs at least 1 note and some stamina): a ringing blow on both sides, 1.2 dmg. It
  plays every toll the staff holds, empties the staff, and sets each of those buffs to **30 s** (a toll already sounding
  is reset to 30 s, not extended). With an empty staff, I is a dull deny clank (the staff flashes red) and nothing comes
  out. Every ground attack routes I to Perform: the press is latched during the move and plays at its end.
- **Blunt:** every bell hit does **×1.3 stance damage**.
- **Hold K** winds the toll: the wind-up is a stance (`wb_kwind`) that is armoured against hits under **25% max HP**.
  At **650 ms** it is wound (the bell hums its Ember note and glints); release then gives the wind-up toll. Letting go
  before 650 ms gives the forward slam, its clock already started at the held time (up to 200 ms). At **2200 ms** it
  releases by itself. L during the wind-up rolls; leaving the ground cancels it.
- **Hold K through any swing:** if K is held through the end of a ground swing (and nothing else was queued), the
  wind-up starts as it ends. After the light chain, a K held at least 150 ms (180 ms after the forward slam) also goes
  into the wind-up instead of the K follow-up.
- A weapon change empties the staff and drops every buff.

**Strengths:** blunt stance damage, buffs you choose by how you fight, a ringing area blow.
**Weaknesses:** slow swings and a heavy roll; the buffs ask you to plan your notes before you need them.

| Toll | Notes | Buff |
|---|---|---|
| Swiftness | Ash Ash | stamina regen ×1.25 (+25%) for 30 s |
| Iron hymn | Ash Ember | for 30 s, finishers and heavy moves don't flinch from hits under 20% max HP |
| Fury | Ember Ember | +8% damage (×1.08) for 30 s |
| Echo | Gold Gold | 3 charges for 30 s: each landed hit rings again on the same foe 0.16 s later for 30% of that hit (6 poise). The buff ends when the 3 charges are spent. Perform and Encore hits don't use a charge |
| Mending (II) | Ash Gold Ember | heal 10% max HP over 10 s; once per 60 s (a Perform on cooldown shows "Mending: not yet" and plays the other tolls) |

| Input | Move | Rank | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|
| J | Left swing (Ash) | I | 1.1 | 18 | 12 | 190 / 460 | 8 px lunge. K: backswing; hold K: wind-up |
| J J | Right swing (Ash) | I | 1.15 | 18 | 12 | 190 / 460 | 8 px lunge. K: backswing; a J after a pause: chime spin (II) |
| J J J | Overhead clang (Ash) | I | 1.8 | 45 | 16 | 290 / 720 | Finisher, 10 px lunge; mashing J stops the combo here. K: knell |
| J J (pause) J | **Chime spin** (Ash) | II | 0.7 ×2 | 30 | 14 | 220 / 640 | Third J pressed 110–450 ms after the right swing ends. Both sides (36 px front, 34 px behind), 210 ms between hits; finisher. J: overhead clang |
| J J J → K | **Knell** (Ember) | I | 1.6 | 55 | 18 | 320 / 820 | Low sweep round the front (box 8 px behind), 10 px lunge; knocks small non-elite foes away; finisher, heavy |
| J → K / J J → K | Backswing (Ember) | I | 1.2 | 30 | 14 | 240 / 620 | Heavy; box 6 px behind. J: overhead clang |
| K | Forward slam (Ember) | I | 1.5 | 40 | 16 | 280 / 680 | Heavy, 10 px lunge. Comes out of the wind-up stance (tap / early release). K: double slam; hold K: wind-up |
| K K | Double slam (Ember ×2) | I | 1.05 ×2 | 60 | 20 | 300 / 880 | Heavy, 330 ms between hits, one Ember note per hit; finisher |
| hold K | Wind-up (stance) | I | – | – | – | wound at 650; auto-release at 2200 | Armoured against hits under 25% max HP while winding; stamina is paid on release |
| hold K, release | **Wind-up toll** (Ember) | I | 2.4 | 80 | 22 | 200 / 760 (after release) | Only once wound (650 ms+). Armoured (< 25% max HP), slam, 12 px lunge; finisher, heavy, counts as a charged heavy |
| ↑J | Peal uppercut (Gold) | I | 1.1 | 25 | 12 | 220 / 560 | For fliers (30 px reach). Also from any J chain with ↑ held. ↑J again: another peal |
| ↑J → J | **Falling peal** (Ash) | I | 1.2 | 30 | 12 | 200 / 560 | The raised bell brought straight down |
| I (1+ notes) | **Perform** | I | 1.2 | 40 | 14 | 300 / 900 | Both sides (40 px each way, 40 px up); plays the tolls (see above); heavy. I: Encore (III) |
| Perform → I | **Encore** | III | 1.4 | 50 | 10 | 260 / 800 | Both sides; resets every toll still sounding to 30 s (Echo back to 3 charges; Mending's heal is not re-armed); plays no new tolls; finisher |
| Perform / Encore | Echo wave | IV | 0.6 | 20 | – | 100 ms after the ring | A ring rolling out 64 px both ways (40 px up), heavy |
| Perform, 3 notes | Grand toll | V | – | +60 (bosses) | – | – | A full-staff Perform stuns small foes (breaks their stance) and adds 60 stance damage to bosses (after the ×1.3) |
| L | Heavy roll | I | – | – | 18 | 480 | 0.26 s invulnerable, 66 px. J from 192 ms, K from 260 ms into the roll, or either within 0.25 s after it |
| L → J | Ringing lunge (Ash) | I | 1.0 | 20 | 12 | 160 / 440 | 22 px dash. J: right swing |
| L → K | Bell drop (Ember) | I | 1.4 | 45 | 16 | 260 / 640 | 12 px lunge, slam; finisher, heavy |
| air J | Air swing (Ash) | I | 1.0 | 18 | 12 | 180 / 420 | Counts toward the air limit |
| air ↓J | Bell pogo (Ash) | I | 0.9 | 12 | 10 | 100 / 300 | **Pogo** |
| air K | **Bell plunge**: dive (Ember) | I | 1.8 | 90 | 20 | 200 ms heave, then dive | Heavy; counts toward the air limit. A foe struck on the way down takes 1.8 and you bounce up (air dash restored) |
| air K, landing | Bell plunge: landing (Ember) | I | 1.8 | 90 | 0 | 40 / 560 | On the floor: the landing blow plus a shock ring, r 44 px, 0.4 dmg, 30 poise; finisher, heavy |

Damage is in AR multiples per hit; poise is for the whole move, before the ×1.3 blunt bonus. Fury (+8%) multiplies all of
it. Iron hymn covers every move marked finisher or heavy above.

**Routes / balance:** dummy bench (`tools/shots/v15/bell/bench.js`: dummy, infinite stamina, 12 s per route, AR
multiples): J J J **2.45/s** (2.65 with Fury) · K K 2.32 · J J J → K 2.26 · J → K → J 2.18 · J J J → I each loop 2.09 ·
K K → I 2.14 · ↑J ↑J → I (Echo) → J J J 2.13 · J J J → I with Fury + Echo kept up **2.80** · Encore loop (III) 2.00 · echo
wave loop (IV) 2.29 · wind-up toll loop (0.7 s holds) 1.60. Boss bench (`boss.js`: Gravetusk held in place, swinging every
2 s, real stamina, 30 s): plain J J J 1.08 (the nine on the same bench: 0.75–1.31); notes into a Perform every ~6 s
1.38, with 2 staggers in 30 s instead of 1. Real-boss bot (balance phase 2b; 25 bosses, J J J at 10 px, Perform at 3
notes, roll): time to kill 1.06–1.17 → **1.04** of the 14-type average after the attack factor, damage taken 1.13 →
1.03, 2.7 → 2.5 staggers per fight.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Chime spin** | J J (pause) J | Third J 110–450 ms after the right swing ends: the bell whirled round you, both sides, 0.7 ×2, 30 poise, 14 stam, 220 / 640 (Ash). Pressed sooner, it's the overhead clang |
| II | **Three-note tolls** | Ash Gold Ember → I | Mending: heal 10% of max HP over 10 s, once per 60 s |
| III | **Encore** | Perform → I | Ring it again: 1.4 both sides, 50 poise, 10 stam, 260 / 800; every toll still sounding goes back to 30 s |
| IV | **Echo wave** | Perform / Encore | 100 ms after the ring, a wave rolls out to 64 px both ways: +0.6, 20 poise |
| V | **Grand toll** | Perform with 3 notes | A full staff stuns small foes and adds 60 stance damage to bosses |

**Deviations from the plan:**
- **Notes ring on hit, not on swing.** The plan said every blow rings a note; built, only a blow that lands does (no
  buffing in an empty room, and the Perform loop isn't free).
- **Numbers.** The plan's J J J came out at 2.02 dmg/s, under target, so the light chain went from 1.0 / 1.05 / 1.5 at
  200/500, 200/500, 300/760 to 1.1 / 1.15 / 1.8 at 190/460, 190/460, 290/720. Forward slam 1.4 → 1.5 (700 → 680 ms),
  double slam 1.0 ×2 → 1.05 ×2 (900 → 880 ms), wind-up toll 2.2 / 70 → 2.4 / 80 with its timing defined (wound at 650
  ms, release 200 / 760, auto-release at 2.2 s). The chime spin, backswing, peal uppercut, Perform, Encore, roll and air
  numbers are as planned; timings were added where the plan left them blank.
- **Added moves:** Knell (J J J → K), Falling peal (↑J → J); the hold-K wind-up is its own armoured stance; the plunge is
  the bell's own move (heave, dive, mid-air bounce, landing blow with a shock ring) instead of the shared plunge. The
  backswing also comes off the right swing (J J → K), not only J → K.
- **Iron hymn** covers heavy moves as well as finishers (the plan said finishers only).
- **Rules the plan left open, now fixed:** a toll must be in order; a full staff can play two tolls; Mending only counts
  from Mastery II and isn't refreshed by the Encore; Echo's re-ring comes 0.16 s later and its 3 charges end the buff;
  an empty-staff I is a deny clank; the chime spin's pause is 110–450 ms; the Grand toll's +60 is counted after the ×1.3.
- **Bell drop (L → K)** is rank I, as the plan has it.
- **Attack factor:** `WM_AR_TUNE.bell = 1.12` (set at the end of `78_mech_bell.js`, balance phase 2b) raises the
  Dirgebell's base AR from 42 to 47.0, because the real-boss bot had the Warbell 14% slower to kill than the 14-type
  average (1.14–1.17 on J J J + Perform); after it, 1.04.

---
## 4. Weapon Mastery

**How it works**
- Each type has its own **mastery rank, I to V**.
- You earn mastery XP only with the weapon in your hands:

  | Action | XP |
  |---|---|
  | A hit | 1 |
  | A kill | 5 |
  | An elite kill | 20 |
  | A boss kill | 150 (300 the first time) |
  | A successful parry, block counter, Iai parry, snap counter or perfect dodge | 5 |

- **Ranks:**

  | Rank | XP | Roughly when |
  |---|---|---|
  | II | 300 | Early: the second region with one weapon |
  | III | 900 | Mid-game |
  | IV | 2,000 | Late-game |
  | V | 4,000 | End-game, or a dedicated main |

- **Unlocks are moves, not stats.** A rank-I weapon is complete and viable; ranks add options and style.
- **Unlocks per type (v15, 14 types):** Longsword 5, Katana 5, Greatsword 6, Maul 7, Sword & Shield 6, Dual Blades 7,
  Spear 7, Staff 5, Whip 6, Switch Axe 5, Bow 4, Martial Arts 6, Scythe 5, Warbell 5: **79** in all (the nine had 4 each
  before v14, 48 after v14, 54 after v14c; the five v15 types add 25). The move lists hold **310** moves (Section 7). Most new ones sit at rank II, so
  the first rank-up comes with a new combo, not just a tweak. Rank I alone now has 3–4 J / K mixes per weapon on top of
  the light chain.
- A **mastery screen** (Esc → weapon mastery) shows each of the 14 types' rank, XP bar, the moves learned and the next unlock,
  with its input. **Enter, or the MOVE LIST button, opens the weapon's full move list** (every move, with its input and
  the rank it needs); ↑↓ scroll it, ←→ switch weapon.
- A rank-up shows a banner, "Longsword Mastery III: Foresight cut", and then a short demo of the input.

---
## 5. Boss Cores and enchanting

- **Cores:** every boss drops its Core on the first kill (one per boss per save; New Game+ keeps them, no duplicates).
  They live in the inventory's "Boss Cores" tab.
- **Enchanting:** at the Ashwright, "Enchant a weapon" sockets a Core into the weapon in hand for 400 cinders (removing
  is free). Each weapon type keeps its own Core. The Core's trait applies only to **finishers, heavies, counters and
  charged releases** — never light attacks — through an edge (a flat bonus on the move) and/or a proc (an on-hit effect
  with internal cooldowns). Budget: +3–14% on the empowered moves (about +5% overall at most). Control effects are
  weaker on bosses (40% strength, half duration, diminishing). Bow arrows get the procs and colour but not the edge.
- **Visuals:** empowered swings glow in the Core's colour on every weapon (overlay glow, afterimage, light; the new
  types' own effects are tinted too); an enchanted blade sheds a faint ember when idle.
- **Rekindle:** a cleared boss arena has an effigy that revives the boss for a rematch, any number of times (not Sister
  Venn). Rematches clear the room's ordinary enemies; a win gives +150 Mastery XP and 10% of the boss's cinders; dying
  costs nothing.
- Full trait table and reasoning: `docs/v15/cores.md`.

---
## 6. Balance

**Dummy benches (the nine).** Dmg/s numbers are the v14 and v14c benches: the dummy, infinite stamina, real inputs
(`tools/shots/v14/<group>/bench.js`), in AR units, so the v15 attack factors don't change them. The five v15 types'
dummy numbers are in their Sections 3.10–3.14 sections. "Main combo" is the plain light chain; "best route" is the best sustained route at
that rank; "best J / K mix" is the strongest of the v14c mixed routes.

| Weapon | Main combo dmg/s | Best route dmg/s | Best J / K mix (v14c) | Per opening | Defense | Mobility | Reach | Difficulty |
|---|---|---|---|---|---|---|---|---|
| Longsword | 2.74 | 2.87 (ember edge, V) | 2.51 (K J J J) | 3.15 (riposte 2.2) | Parry | Roll | Mid | ★ |
| Katana | 2.17 | 2.59–2.62 (K → K loop) | 2.56 (Iai → J → K loop) | **3.3** (prepared Iai → swallow return) | Iai parry | Sidestep | Mid | ★★★★ |
| Greatsword | 1.83 | 2.52 (level 3 loop); 2.25 level 3 → strong | 2.21 (level 3 → J → J) | **3.9** (one hit) | Chip guard + retort | Slow roll | Mid | ★★★ |
| Maul | 2.02 | 2.40 (upswing taps); charge loops 1.60–1.76 | 2.06 (J → K → K, II) | 3.0 + knockdown | Brace + payback | Walk-charge | Short | ★★★ |
| Sword & Shield | 2.53 | 3.12 (perfect rush, II) | 2.47 (K J J J) | 3.8 | **Full block + parry** | Backhop | Short | ★ |
| Dual Blades | 2.81 | **3.42** (Demon) / 3.66 with the perfect-dodge buff | 2.65 (J J K J J); Demon K J J J K 2.92 (II) | ≈ 4 (Blade Dance 4.2) | None (perfect dodge) | **Demon dash** | Shortest | ★★★★ |
| Spear | 2.63 | 2.63 (charge dash after a run 2.22) | 2.51 (J J K) | 3.15 / counter 2.0 (3.0 charged) | **Heavy guard** | Hop | **Long** | ★★ |
| Staff | 2.52 | 2.49 (spin loop); the air game trades damage for safety | 2.50 (J K + air J, ending 40 px away in the air) | ≈ 2.6 from a vault | Vault evasion | **Vault** | Mid | ★★★★ |
| Whip | 1.93 untipped / 2.29 tipped | 3.02 (tipped K + thunderclaps) | 2.52 (J J J K tipped, II) | 3.9 | None (snap counter) | Roll | **Longest** | ★★★★★ |

No v14c mix beats its weapon's main loop: the mixes trade damage for stagger (poise per second is often 1.5–2× the light
chain's), reach, spacing, crowd cover or flow. Real-boss bot runs of the mixes (e.g. Katana J J J K 1.16, Longsword
K J J J 1.14 on Gravetusk) land level with the main chains.

**Against real bosses (v15, all 14 types).** The v15 balance pass (`docs/v15/balance.md`, phases 2a and 2b) runs a
scripted boss bot over 25 bosses × 14 types × 3 seeds at the expected build for each boss's stage, each type on its
best route with its own defensive tool. Numbers are relative to the 14-type average (geometric mean over 25 bosses):
1.00 is average, lower is faster or safer. It's a crude player: compare types with each other, not as absolutes.

| Type | Bot route | Attack factor | Time to kill | Damage taken | Staggers / fight |
|---|---|---|---|---|---|
| Longsword | J chain, parry | 1.0 | 1.02 | 1.02 | 3.6 |
| Katana | K → K Iai loop, Iai parry | 0.80 | 0.91 | 1.42 | 3.0 |
| Greatsword | level 3 charge (1.2 s hold), guard | 1.0 | 1.00 | 1.24 | 2.5 |
| Maul | J chain, roll | 0.95 | 0.98 | 1.01 | 3.7 |
| Sword & Shield | J J K, guard | 1.18 | 1.12 | 0.99 | 3.9 |
| Dual Blades | J chain, roll (no Demon Mode) | 0.60 | 0.89 | 0.95 | 0.2 |
| Spear | J chain, guard | 1.24 | 1.12 | **0.64** | 1.3 |
| Staff | J chain, roll | 1.25 | 1.04 | 0.87 | 0.7 |
| Whip | tipped K at 40 px, roll | 1.10 | 0.99 | 0.86 | 2.1 |
| Switch Axe | blade J J J J, axe J J J once morphed | 1.0 | 1.00 | 1.11 | 0.7 |
| Bow | J J J J at the sweet spot, limb deflect | 1.0 | 0.95 | 0.95 | 3.6 |
| Martial Arts | J I J J J (Swift jab, Shift strike, Iron chain), slip step | 0.92 | 0.92 | 1.21 | 2.4 |
| Scythe | J J J + hold K Reap, roll | 1.0 | 1.05 | 0.93 | 0.8 |
| Warbell | J J J, Perform at 3 notes, roll | 1.12 | 1.04 | 1.03 | 2.5 |

- **All 14 types land within 0.89–1.12 of the average time to kill** (target ±15%). Before phase 2a the Dual Blades or
  the Katana were fastest on 24 of 25 bosses; now the fastest type per boss is spread over eight types (Bow 8, Dual 5,
  Katana 5, Martial Arts 2, Whip 2, Greatsword 1, Switch Axe 1, Staff 1).
- **Identities show in damage taken:** the Spear (0.64), Whip (0.86), Staff (0.87) and Scythe (0.93) are the safe ones;
  the Katana (1.42), Greatsword (1.24) and Martial Arts (1.21) trade safety for their big hits.
- **What moved them:** the per-type attack factors (Section 2); the Katana's Iai and the Bow's deflect only fully counter
  parryable blows (Section 2); Greatsword swing armour and a ×0.7 charge (Section 3.3); guard-cost scaling (Section 2); Spear +40% poise (Section 3.7);
  Whip tip poise ×1.6 (Section 3.9). The skill tree was fixed alongside (`docs/v15/balance.md` part 1: nodes that were dead,
  per-hit nodes that multiplied on multi-hit weapons, Tireless and Flowing Form making attacks free).
- The Switch Axe morphed in about 40% of bot fights; its blade mode plays like a Longsword and the axe phase lifts a
  fight when it comes. The ±15% band is least reliable for spacing-sensitive types (Whip, Spear, Bow) and for the
  Greatsword's charge greed.

**Balance principle:** most types land at about **2.5–2.8 damage per second** on their main chain, and the higher
numbers come with a real cost:
- the Katana's prep time and stamina (42 per K → K loop);
- the Dual Blades' stamina drain, exhaustion, lack of a block, and perfect-dodge timing to reach the top end;
- the Sword & Shield's perfect rush timing (rank II);
- the Whip's spacing precision (the thunderclap pays only at the tip).

Two types sit lower on paper by design: the **Greatsword** (1.83 on lights; its value is the 3.9 single hit inside a
boss opening, flinch-proof charging and stance damage) and the **Whip untipped** (1.93; it's built around the tip).
The safer the weapon (Sword & Shield, Spear), the lower its burst. On real bosses the v15 attack factors close the rest
of the gap (table above).

---
<!-- MOVELIST:BEGIN -->
## 7. Move lists

The full command list of each weapon, 310 moves in all, exactly as the in-game **Move List** shows it (Esc → weapon mastery → Enter, or the MOVE LIST button). **Rank** is the Weapon Mastery rank that unlocks the move (I = available from the start). Inputs: **J** light, **K** heavy, **I** block / parry / special, **L** roll / step, **↑ / ↓** held, **air** = while airborne, **hold** = keep the button down, **(pause)** = wait a beat before the last press, **→** = right after the previous move. This section is generated from the code by `tools/movelist_doc.py`; the weapon sections (3.1–3.14) have the timings and numbers.

### Longsword — 21 moves (16 from the start)
*Ashen Longsword* · default art **Ashen Crescent** · mechanic: Parry and riposte

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Light chain | J J J J | Downward, rising, poke, then the critical slash (commits). |
| I | Lifting cleave | J K | A low-to-high heave that pops light foes up. J after it: the poke. |
| I | Horizontal slash | J J K | A wide flat sweep across the front for crowds. |
| I | Heavy poke | J J J K | A long two-handed thrust to punish from range. |
| I | Overhead slash | K | The simple heavy. |
| I | Return slash | K J | The blade snaps back up off the floor. J J after it: poke, crit. |
| I | Crosswise strike | K K | Hands flip overhead: a flat cut at head height for tall foes. |
| I | Splitting cleave | J K K | Lift the foe, then bring the blade straight down into the floor. |
| I | Charged overhead | hold K | Release when the blade flashes: 2.4 dmg, breaks stance. Turnable. |
| I | Riposte | I (parry) → J | After a parry: a lunging 2.2 counter. |
| I | Quick slash | L → J | A rising cut straight out of the roll. |
| I | Wheeling cut | L → K | Roll through, then turn on the nearest foe with a wide cut. |
| I | Up slash | ↑J | A rising overhead cut for fliers. |
| I | Falling crescent | air J J | A second air cut: a big crescent from overhead down past the feet. |
| I | Plunge stab | air ↓J | Pogo off foes and spikes. |
| I | Plunge | air K | A falling slam. |
| II | Step slash | L forward → J | The roll becomes a gliding cut: stay in close. |
| II | Wheel slash | J J (beat) J | Wait a beat after the 2nd cut: a turn that cuts both sides. J: crit. |
| III | Foresight cut | I → K | A short stance: a blow in it is negated and answered with a 2.8 cut. |
| IV | Pommel strike | J J J → hold K | Hold K ~0.2 s after the poke: a pommel bash with huge poise. |
| V | Ember edge | J J J ·J (on the flash) | Press the 4th J as the poke flashes: a burning follow-up (+1.2). |

### Katana — 22 moves (18 from the start)
*Duskveil* · default art **Moonwave** · mechanic: The sheathe and the Iai draw

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Light chain | J J J | Quick cut, return cut, then a triple flurry. |
| I | Flurry sheathe | J J J → I | Slide the blade home straight out of the flurry. |
| I | Helm splitter | J J J K | End the flurry with one raised vertical cut: the stagger it lacks. |
| I | Kesa cut | J K | A stepping shoulder-to-hip cleave. J after it: back to the chain. |
| I | Crescent sheathe | J J K | A wide turning cut that ends sheathed: K next is an Iai. |
| I | Sheathe | I | Sheathe the blade (70% walk). Everything from the sheathe is a draw. |
| I | Draw cut | J (sheathed) | A quick low draw-cut from the hip that flows into the chain. |
| I | Iai draw | K (sheathed) | The fastest heavy in the game: 2.2 dmg. |
| I | Swallow return | Iai → J | A reversed rising cut snapped back after the Iai. I: sheathe again. |
| I | Thrust home | Iai → J → K | A lunging thrust, then the blade is sheathed: K next is an Iai. |
| I | Focus draw | hold K (sheathed) | Hold 0.4 s, release: a dash-through cut, briefly invulnerable. |
| I | Iai parry | I (sheathed, timed) | Just before a parryable blow: negate it, counter-cut (2.4). |
| I | Rushing draw | K (drawn) | Dash in with a rising cut and sheathe again: K → K loops. |
| I | Step cut | L → J | A flat cut out of the sidestep. |
| I | Crescent | ↑J | A rising crescent for fliers. |
| I | Air draw | air J | An iaido draw in the air. |
| I | Needle stab | air ↓J | Pogo off foes and spikes. |
| I | Falling draw | air K | A plunge. |
| II | Turning draw | focus draw → K | You dashed through: whirl round, cut back, sheathe. |
| III | Flash step | L (sheathed) | An invulnerable blink that keeps the sheathe; K out of it is an Iai. |
| IV | Thousand cuts | J J J → I | The flurry sheathe makes every flurry hit echo (+0.3 each). |
| V | Moonlit iai | perfect Iai parry → K | A parry in the first 60 ms: time slows, your next Iai deals 3.0. |

### Greatsword — 21 moves (15 from the start)
*Gravecleaver* · default art **Storm Leap** · mechanic: Charge levels

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Light chain | J J J | Overhead hack, wide sweep, rising spin that lifts small foes. |
| I | Hilt bash | J → K  /  J J → K | A pommel shove. Keep K held: the charge goes on from level 2. |
| I | Momentum cleave | J J J → K | The spin rolls on into a full overhead cleave (2.6). |
| I | Turning sweep | J → K → J | Off the hilt bash, the body wheels round in a flat sweep (2.0). |
| I | Charged slash | hold K | Release on a pip: 2.0 / 2.85 / 3.9. Past 1.4 s it overcharges. |
| I | Upheaval | charged slash → J | Wrench the buried blade up out of the floor (1.8, lifts). J: spin. |
| I | Strong charged slash | charged slash → hold K | The same levels, ×1.25. |
| I | Keep charging | hold K through a swing | Keep K held as a swing ends and the next charge starts at once. |
| I | Blade guard | hold I | Block frontal blows: stamina and 25% chip, no parry. |
| I | Retort | block a blow → J | Within 0.7 s of a block: the blade torn up out of the floor (1.8). |
| I | Rolling heavy | L → hold K | A charged slash out of the roll, 200 ms already banked. |
| I | Great arc | ↑J | One arc from the floor to the sky, for fliers. |
| I | Air cleave | air J | Hangs a beat at the top, then cleaves down. |
| I | Two-handed plunge | air ↓J | Pogo off foes and spikes (wide). |
| I | Earth plunge | air K | A falling slam. |
| II | Shoulder tackle | hold K → L | Once per charge: shoulder through a blow and keep charging. |
| II | Earthsplitter | J J J → K → K | Plough the buried blade forward and rip it out level (2.4). |
| III | True charged slash | strong slash → hold K | A rising backhand, then 4.9 at full charge. |
| III | Leaping wide slash | hold K → L → J | Tackle, then cash the charge in at once with a bounding sweep. |
| IV | Guard tackle | block → K | Shoulder out of the guard into a level 2 charge. |
| V | Wrath | hold K past level 3 | A red fourth level (1.4-2.1 s): 4.5 and a small flame burst. |

### Maul — 22 moves (15 from the start)
*Cinder Maul* · default art **Tolling Blow** · mechanic: Walk-charge and stun

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Light chain | J J J | Two overhead smashes, then a golf-swing upswing that lifts small foes. |
| I | Side blow | J → K  /  J J → K (tap) | A flat hook that knocks small foes aside. J after it: the upswing. |
| I | Walk-charge | hold K | Walk at 60% while charging. Release: upswing / double / big smash. |
| I | Hammer drop | K (upswing) → J | The raised hammer comes straight down (1.4). J again: the upswing. |
| I | Spinning bludgeon | hold K 1.4 s (moving) | Up to 4 spins (0.5 each); let go for the 2.0 spin finisher. |
| I | Haft jab | hold K → J | Once per charge: a lunging jab (0.7) that keeps the charge going. |
| I | Keep charging | hold K through a swing | Keep K held as a swing ends and the walk-charge starts at once. |
| I | Brace | I | 0.6 s: blows can't flinch you and do half damage. |
| I | Payback | brace a blow → K | The braced head torn up into an uppercut (2.0, stuns ×2). |
| I | Rolling swing | L → J | A low-to-high sweep out of the roll. |
| I | Rolling charge | L → hold K | Come out of the roll already charging. |
| I | Rising hammer | ↑J | An upward blow for fliers. |
| I | Hammer spin | air J | A spinning blow in the air. |
| I | Ground pound | air ↓J | Pogo with a big bounce. |
| I | Meteor plunge | air K | A falling slam with a small shockwave. |
| II | Charge step | hold K → L | Roll without losing the charge. |
| II | Third pound | double smash → K | A hop and a third blow into the same spot (1.6). |
| II | Backswing slam | J → K → K | Off the side blow, all the way round into an overhead slam (2.0). |
| III | Big Bang | J J J → K K K K | Hook, backhand, uppercut, then a leaping 3.0 that stuns ×2. |
| IV | Steered spin | spin + ← / → | Steer the spinning bludgeon; each spin deals 0.6. |
| IV | Hammer spike | air J J | Spike small foes into the ground and bounce off. |
| V | Earthshaker | hold K 1.4 s, standing still | Slam the overcharge down: a shockwave both ways (1.0, stuns). |

### Sword & Shield — 22 moves (17 from the start)
*Knight’s Sword and Shield* · default art **Aegis** · mechanic: Full guard, parry and backhop

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Quick slash chain | J J J J | Three fast cuts and a reeling shield-bash finisher. |
| I | Shield jab | J K | A quick shield punch (28 poise); J carries on into the 3rd cut. |
| I | Rim upper | J J J K | The shield rim driven up through the foe: launches small foes. |
| I | Backhand rim bash | J K K | Jab, then the shield flung out edge-first: two bashes, 78 poise. |
| II | Aegis plant | J J J J K | Plant the shield after the finisher: staggers both sides. |
| II | Wheel cut | J J (pause) J | Wait a beat after the 2nd cut: a full turn, hits both sides. |
| II | Perfect rush | J J K on the flash | Press each on the light flash: 0.85, 1.1, then a 1.8 bash. |
| I | Shield bash | K | Drive the shield forward: 60 poise, small foes reel. |
| I | Under-rim cut | K J | A low cut after the bash; J J go on to the 3rd cut and finisher. |
| I | Shield hammer | K K | The shield raised overhead and its rim hammered down: 120 poise. |
| I | Charged shield rush | hold K | Dash 70 px behind the shield; light hits do not stop it. |
| I | Block / parry | I (hold / tap) | Hold to block anything frontal; tap to parry (170 ms). |
| I | Guard counter | block or parry → J | A heavy thrust over the rim, 1.9. |
| III | Shield slam | block → K | The shield brought down like a gate: 110 poise. |
| V | Perfect guard | I just before a blow | Within 100 ms: free block, projectiles fly back, counter +50%. |
| I | Backhop | L | A short hop back, 0.14 s invulnerable. |
| I | Leaping slash | L → J | Spring forward off the backhop with an overhead cut. |
| I | Shield charge | L → K | Land from the backhop and drive back in behind the shield. |
| I | Air slash | air J | A low cut beneath the raised shield. |
| I | Shield uppercut | ↑J | The shield punched overhead: for fliers. |
| I | Shield surf | air ↓J | Ride the shield down: the widest pogo. |
| I | Falling slash | air K | The plunge (IV: the falling bash, 1.6). |

### Dual Blades — 24 moves (19 from the start)
*Twinfangs* · default art **Twin Tempest** · mechanic: Demon Mode and the perfect dodge

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Twin slashes | J J J J | Two double slashes, a rising cross, then a spinning finisher. |
| I | Fang barrage | J J (pause) J | Wait a beat after the 2nd slash: five quick alternating stabs. J: spin |
| I | Skyward fangs | J J J K | A rising double cut that carries you up, popping light foes. J: air J |
| I | Hooking cross | J J K | Low hooks in from both sides; reels light foes. J: rising cross |
| I | Lunge | K | Dash in and open the blades in an X. |
| I | Spiral pursuit | K J | A drifting corkscrew of four cuts round you. J: back into the chain. |
| I | Fang pounce | K K | Hop off the lunge and chop both blades down together: stagger. |
| I | Demon Mode | I (tap) | Toggle: drains stamina, 20% faster swings, attacks cost half. No block |
| I | Demon chain | Demon: J ×6 | The chain runs on: a downward cut, then a spin with an upward rip. |
| I | Demon flurry | Demon: K | Six alternating cuts, advancing. Hits fill the demon gauge. |
| I | Blade Dance | Archdemon: hold K | Eight cuts and a crossed X (4.2). Light armour. Empties the gauge. |
| I | Perfect dodge | L just before a blow | Roll ≤0.1 s (demon dash ≤0.175 s) before a hit: +25 stam, +10% speed. |
| I | Counter flurry | L (perfect) → J | Straight out of a perfect dodge: three cuts at once. |
| I | Dash slash | L → J | Spring out of the roll and cut through. J: back into the chain. |
| I | Scissor up-cut | ↑J | Both blades scissored up past the head, for fliers. |
| I | Twin spin | air J | Both blades brought through at once: an X opens in front. |
| I | Crossfall | air J J | After the twin spin: a crossed dive to the floor, 2 hits. |
| I | Drill | air ↓J | Blades crossed under the feet, twisting: pogo off foes. |
| I | Twin plunge | air K | A falling slam. |
| II | Dash-through cut | demon dash → J | Cut straight through out of the dash. x1.5 after a perfect dodge. |
| II | Bloodwheel | Demon: K J | Out of the flurry, a somersault of crimson cuts. J: demon chain 5. |
| II | Rending cyclone | Demon: J ×6 → K | Two crimson spins and a leaping cross-cut: the demon chain finisher. |
| III | Blade Dance II | Archdemon: hold K | Three more cuts and a bigger cross-cut finisher. |
| III | Reversal cut | L → K | Turn out of the roll with a rising double cut. Perfect: silver, x1.5. |

### Spear — 22 moves (17 from the start)
*Rootspear* · default art **Thunder Lunge** · mechanic: Heavy guard, hop and charge dash

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Poke chain | J J J | Three long pokes (1.5x sword reach), the last an overhead sweep. |
| I | Twin thrust | J K | A poke at the knee, then the chest; J goes on to the sweep. |
| I | Recoil thrust | J J K | Step back while thrusting: hit and keep your distance. |
| I | Impaling drive | J J J K | Thrust it home, then twist and drive it deeper: 2 hits. |
| II | Wheeling haft | J J (pause) J | Wait a beat after the 2nd poke: spin the haft, hits both sides. |
| I | High thrust | K | An upward lunge: for fliers and tall foes. |
| I | Falling haft | K J | Raise the spear and chop the haft down in front. |
| II | Sky rake | K K | A second, steeper high thrust that lifts small foes. |
| I | Charge dash | hold K (moving) | Run with the spear levelled; let go of K for the finishing thrust. |
| I | Heavy guard | I (hold) | Blocks anything frontal; walk slowly behind it. Big hits chip 10%. |
| I | Guard poke | I + J | A short thrust from the guard; the guard is back after it. |
| I | Counter-thrust | block → K | Within 0.5 s of a block: a 2.0 lunge out of the guard. |
| III | Charged counter | block → hold K | Keep K held 150 ms: a 3.0 piercing lunge, 90 poise. |
| III | Rising sweep | counter-thrust → J | Sweep the haft up overhead after the counter: launches. |
| IV | Power guard | I + K | 1 s with no pushback or chip; blocks cost x1.5. |
| I | Hop | L | A short hop that keeps you facing the foe; chain 2 (II: 3). |
| I | Hop poke | L → J | Pokes on from where the chain left off. |
| I | Hop lunge | L → K | Off the hop, a long low lunge at full stretch. |
| I | Jump thrust dive | air J (rising) | Attack while rising after a jump: dive down the spear. |
| I | Sky thrust | ↑J | Straight up at the sky: for fliers. |
| I | Tip-first strike | air ↓J | Ride the spear tip down: the pogo. |
| I | Lance plunge | air K | The plunge. |

### Staff — 20 moves (15 from the start)
*Pilgrim’s Quarterstaff* · default art **Whirlwind** · mechanic: Vault and momentum

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Strike · Butt strike · Low sweep · Overhead | J J J J | Both ends: every step also hits just behind you. The sweep trips. |
| I | Pole launcher | J J K | Upswing that launches small foes and carries you into the air. |
| I | Back vault | J K | Flip back over the planted staff, kicking up through the foe. |
| I | Spin | K | Two full turns at the waist, front and back. 24 stamina. |
| I | Spin vault | K → J | Ride the spin up and over: the staff comes down from above. |
| I | Vault | I | Spring off the staff, up and forward. Invulnerable at the start. |
| I | Vault kick | I → J | A flying kick off the planted staff at the top of the vault. |
| I | Vault spin | I → K | The aerial spin straight out of the vault. |
| I | Low sweep | L → J | Out of a roll: a spinning sweep at the ankles, both sides. |
| I | Aerial strike | air J | An air wheel. Each air hit adds a momentum stack (+8%, max 3). |
| I | Cartwheel | air J J | Turn over the staff: the butt behind you, then the head in front. |
| I | Aerial spin | air K | A gliding spin round the waist, front and back. |
| I | Comet | air K → J | Dive staff-first to the floor; spends momentum: +25% per stack. |
| I | Rising twirl | ↑J | The staff wheels overhead: for fliers. |
| I | Dive kick | air ↓J | Pogo off a foe. The first bounce of a jump refunds an air attack. |
| II | Roll vault | L → I | Vault straight out of a roll. |
| II | Pole drop | air ↓J → K | Off the dive kick, drop on the staff point: a shock on both sides. |
| III | Spin finisher | air K → K | A second, wider aerial spin ending in a chop. |
| IV | Double vault | I in the air near a foe | Vault off its head (cancels an air move); refunds the air attacks. |
| V | Gale | K with 3 momentum | Spend the momentum: a slow tornado strikes 3 times. |

### Whip — 20 moves (14 from the start)
*Headsman’s Chain* · default art **Lash** · mechanic: Tip crack and grapple

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Lash · Lash II · Whirl lash | J J J | Twice sword reach. The last 30% of the lash is the tip: ×1.3. |
| I | Trip lash | J J K | A low crack along the floor. Tipped, it trips small foes. |
| I | Tip flick | J K | A fast wrist-snap, tip only: little damage, +15 crack. |
| I | Heavy crack | K | Fling the chain straight out. A tip hit fills the crack meter. |
| I | Wrench | K → J | Haul on the chain at the tip: drags small foes in, 40 poise. |
| I | Overhead crack | hold K | Whirl it overhead, release at full: 2.4× sword reach. |
| I | Thunderclap | K at 100 crack | 2.5 (3.25 at the tip), 90 poise, a blast and a stagger. |
| I | Grapple | I | Small foes are reeled in; large foes and hook rings pull you. 2 s. |
| I | Retreat lash | L → J | Back off 40 px and crack forward: the tip lands where you were. |
| I | Coil spin | L → K | Out of a roll, the chain whirls round you: small foes go to the tip. |
| I | Circular lash | air J | A full circle round the body, front and back. |
| I | Skyfall crack | air J J | From the circle, a long crack down to the floor ahead. |
| I | Vertical crack | ↑J | The tip cracks straight overhead: for fliers. |
| I | Down crack | air ↓J | Pogo off a foe on a long box below. |
| II | Snap counter | I just before a hit | Negate it and lash the attacker out of its move. 6 stamina. |
| II | Reel kick | grapple → J | Kick the foe you reeled in back out to the tip. |
| II | Cyclone | J J J K | Two full-length cracks, ahead then behind: a tip on both sides. |
| III | Grapple slam | grapple → K | Haul the catch overhead and slam it: 1.6 dmg, stunned. |
| IV | Double crack | K → K | A rising backhand into a second, harder crack. |
| V | Thousand lashes | hold J | Keep J held through the lash: 8 tip-only cracks. |

### Switch Axe — 22 moves (18 from the start)
*Gravegrinder* · default art **Magma Quake** · mechanic: The Switch Gauge and the morph

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Rising · Falling edge · Double slash · Edge rush | J J J J | The gauge builder: +4 a hit, +7 on the beat, the rush +10 (13). |
| I | On the beat | press late | Press in the last 150 ms of a swing: +7 gauge instead of +4. |
| I | Hook heave | J K | Hook under the guard and heave up over the shoulder. Lifts light foes. |
| I | Phial thrust | K | Drawn back level, then rammed out; the phial coughs fire. |
| I | Ratchet twist | K K | Re-drive the buried blade and wrench it: +12 gauge if both land. |
| I | Hone | hold K | Grind the edge on the floor: +10 gauge/s, rooted. A hit costs 25. |
| I | Skyward edge | ↑J | One straight arc up over the helm. |
| I | Lunging edge | L → J | A long low cut out of the roll. J: Falling edge. |
| I | Air edge  /  Pogo | air J  /  air ↓J | A cut in the hang; the weapon driven under the feet. |
| I | Morph slash | I (gauge full) | Armoured: the blade unfolds into the axe on the hit (2.0). Axe mode. |
| I | Axe: overhead · wild swing · grinder sweep | J J J | The damage: 2.9, 3.2, then five chain bites (0.9 each). |
| I | Axe: rev thrust | K | The head held out with the chain screaming: four bites. |
| I | Axe: chainsaw grind | hold K | A bite every 80 ms (0.28); walk at 30%. Drains 15 more a second. |
| I | Axe: rising grinder | ↑J | The head dragged up off the floor and over. |
| I | Axe: falling cleave  /  plunge | air J  /  air K | A chop as you drop (1.4); the axe plunge (1.8). |
| I | Axe: heavy sidestep | L | A short, slow shuffle under the weight. L → J: the overhead. |
| I | Morph back | Axe: I (gauge < 40) | The blade jack-knifes out of the haft as a rising cut (1.4). |
| I | Vented | gauge runs dry | The axe folds shut in a cloud of steam: 0.6 s you cannot act. |
| II | Ratchet cut | J J (pause) J | Wait a beat after the 2nd cut: three sawing bites, +3 each. |
| II | Ripping heave | Axe: K K | The head torn up through the foe and over (2.6). Launches. |
| III | Full Release | Axe: I (≥ 40) | Eight bites and a burst, 3.0-6.0 by the gauge. Folds back. |
| V | Grinding halo | Full Release | Ends in a ring burst and refunds 30 gauge. |

### Bow — 19 moves (15 from the start)
*Ashstring Recurve* · default art **Backstep Slash** · mechanic: Charge levels and the sweet spot

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Volley chain | J J J | Quick shots: 1, 2, then 3 arrows (0.4 each). Each raises the level. |
| I | Pinning shot | J J J J | One heavy arrow (1.7) that staggers small foes. Spends the level. |
| I | Draw | hold K | +1 level every 0.4 s, from the level you banked. Walk at 40%. |
| I | Power shot | release K | 0.9 / 1.4 / 2.0 by level; level 3 pierces. Tap K: banked level. |
| I | Charge step | L | A quick sidestep that raises the next shot one level. |
| I | Step and draw | L → hold K | Draw straight out of the step, from the level it banked. |
| I | Arrow stab | J → K | Jab the nocked arrow into the foe (0.8). J: back to the volley. |
| I | Recoil shot | J → K → K | A point-blank shot that kicks you 30 px back (1.2). |
| I | Dash shot | L → J | Skid in and loose at the banked level (1.0 at lv2). J: volley. |
| I | Leaping point-blank | L → K | Hop in and loose a fan of three down into the foe (1.5). |
| I | Limb deflect | I (timed) | A 150 ms window: turn the blow on the limb, counter shot (1.6). |
| I | Arc shot | ↑J | Loose high: five arrows rain 40-90 px ahead (0.3 each). |
| I | Aerial shot | air J | Loose down at a slant in mid-air (0.9). Twice per jump. |
| I | Talon stomp | air ↓J | Stamp down with the bow limb: pogo off foes and spikes. |
| I | Hunter's dive | air K | Dive at the foe and loose point-blank as you land (1.5). |
| II | Double charge step | L L | Two steps in a row: straight to level 3. |
| III | Hollow piercer | lv3 power shot → K | A drilling arrow through the whole line: 6 × 0.4. |
| IV | Arc shot ×7 | ↑J | Seven arrows in the arc. |
| V | Point-blank burst | lv3 shot < 20 px | The shot bursts through the foe: +0.6, and hits behind it. |

### Martial Arts — 32 moves (26 from the start)
*Penitent’s Knuckles* · default art **Bloodstep** · mechanic: Swift and Iron styles

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Change style | I | Swift (fast, light, evasive) ⇄ Iron (slow, armoured, breaks stance). |
| I | Shift strike | I mid-combo | Cancel on the hit into the other style’s linking blow (+15%). |
| I | Falling star | Swift: J J → I | An Iron heel drop out of the Swift chain. J: the Iron chain goes on. |
| I | Wind cut | Iron: J → I | Four quick Swift blows out of the Iron chain. J: the Swift chain. |
| I | Jab · Cross · Hook · Knee rush | Swift: J J J J | Quick hands, then three driving knees (finisher). |
| I | Snap kick | Swift: K | A fast front kick. J: back into the cross. |
| I | Double roundhouse | Swift: K K | Two turning kicks, the second higher. |
| I | Rising knee | Swift: J K | A jumping knee that pops light foes. J: the cross. |
| I | Whirlwind kick | Swift: J J K | A spinning kick that hits both sides. |
| I | Rising uppercut | Swift: ↑J | A springing uppercut: launches light foes, reaches fliers. |
| I | Slip step | Swift: L | A quick weave: 8 stamina, 0.18 s invulnerable. |
| I | Shadow jab | Swift: L → J | A jab out of the slip. J: the cross. |
| I | Sliding sweep | Swift: L → K | Slide in low and kick the legs out: trips light foes. |
| I | Iron palm · Elbow · Shoulder charge | Iron: J J J | Rooted blows; the shoulder charge is armoured through. |
| I | Hammer fist | Iron: K | Both fists brought down overhead: 50 poise. J: the elbow. |
| I | Mountain stomp | Iron: K K | A stamp that cracks the floor: a small shockwave both sides. |
| I | Iron fist | Iron: hold K | Armoured charge, 2 levels: 1.8 / 2.6. Turnable. |
| I | Grapple throw | Iron: J K | Throw a small foe over your shoulder; a boss takes the palm. |
| I | Pillar kick | Iron: J J K | A rising heel straight up through the foe: launches. |
| I | Heaven’s uppercut | Iron: ↑J | A rooted, rising uppercut with the whole body behind it. |
| I | Iron step · Shoulder bash | Iron: L / L → K | A short planted step; K out of it drives the shoulder in. |
| I | Air kick · Triple air kick | Swift: air J / air J J | A snapping kick, then three more scissoring. |
| I | Diving elbow | Iron: air J | Drop elbow-first at a slant to the floor. |
| I | Diving heel | air K | A steep heel-first dive; bounces off a foe it meets. |
| I | Stomp | air ↓J | Stamp down: pogo off foes and spikes. |
| I | Ember shift | Shift at 5 Flow | Full Flow ignites the next Shift strike: x1.3 and a burn. |
| II | Spinning backfist | Swift: J J (pause) J | Wait a beat after the cross: turn into a backfist. J: knee rush. |
| II | Hundred fists | Swift: hold K | Jabs as fast as the eye can follow while K is held. |
| III | Flowing counter | Swift: L (perfect) → J | Slip a blow at the last moment and answer it with a 1.4 palm. |
| III | Tempest to mountain | Swift: J J J → I → K | Falling star, then a Swift flurry into an Iron hammer fist. |
| IV | Iron to wind release | Iron: hold K → I | Loose the charge as a Swift dash-punch through the foe. |
| V | Ember palm | hold I (5 Flow) | All the Flow in one burning palm: 3.0, 120 poise. |

### Scythe — 20 moves (15 from the start)
*Requiem* · default art **Reap** · mechanic: Souls and the hook step

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Low reap · High reap · Turning harvest · Harvest moon | J J J J | Every reap also cuts just behind you. The far edge harvests a soul. |
| I | Hook pull | J K | Sink the hook and haul: drags small foes 30 px in. J: high reap. |
| I | Scything spiral | J J K | Three turns of the blade round you, front and back. |
| I | Wide crescent | K | One huge flat arc that cuts ahead and behind. |
| I | Twin crescent | K K | Two more crescents, round and back again: 40 poise. |
| I | Reap | hold K (souls) | Every soul on one great arc: 1.6 / 2.4 / 3.2, both sides. Also J / J J. |
| I | Charged crescent | hold K (no souls) | Hold till the blade gleams (0.5 s), release: 2.0, 50 poise. |
| I | Hook step | I | Hook the blade behind the foe ahead and swing round to its back. |
| I | Rising harvest | ↑J | The blade swept up overhead: lifts small foes, for fliers. |
| I | Ghost slash | L → J | Out of the roll, a pale cut that leaves your shade behind. |
| I | Leg sweep | L → K | A low turn at the ankles, both sides: trips small foes. |
| I | Air arc | air J | A full circle of the blade round you in the air. |
| I | Crescent dive | air J J | Out of the arc, dive to the floor at a slant behind the blade. |
| I | Grave pogo | air ↓J | The blade hooked under your feet: pogo off a foe. |
| I | Grave plunge | air K | Drop blade-first onto the floor or a foe below. |
| II | Pendulum | J J (pause) J | Out ahead, then back behind you. J: harvest moon. |
| II | Backstab reap | I → J | Swing round behind the foe and cut into its back: 1.6. |
| III | Grave hook | I near a boss | The hook step swings you round bosses as well. |
| IV | Lean harvest | hold K (2 souls) | Two souls are enough for a full-strength Reap. |
| V | Requiem | hold K (souls) | A Reap that connects heals 2% max HP per soul. |

### Warbell — 23 moves (18 from the start)
*Dirgebell* · default art **War Cry** · mechanic: Notes and tolls

| Rank | Move | Input | What it does |
|---|---|---|---|
| I | Left · Right · Overhead clang | J J J | Three Ash blows, the last a downward clang (finisher). |
| I | Knell | J J J → K | Off the clang, the bell dragged low round your front (Ember). |
| I | Backswing | J → K  /  J J → K | A backhand of the bell's shoulder (Ember). J: the overhead clang. |
| I | Forward slam | K | The bell mouth-first into the floor (Ember). |
| I | Double slam | K K | Up and down twice into the same spot: two Ember notes. |
| I | Wind-up toll | hold K | Swing the bell round behind you; from 0.65 s it's wound: 2.4 (Ember). |
| I | Peal uppercut | ↑J | The bell heaved up past the head, for fliers (Gold). ↑J again: Gold. |
| I | Falling peal | ↑J → J | The raised bell brought straight down (Ash). |
| I | Perform | I (1+ notes) | A ring both sides (1.2); plays every toll in the staff: 30 s buffs. |
| I | Swiftness | Ash Ash → I | Stamina regenerates 25% faster. |
| I | Iron hymn | Ash Ember → I | Finishers and heavies don't flinch from hits under 20% max HP. |
| I | Fury | Ember Ember → I | +8% damage. |
| I | Echo | Gold Gold → I | The next 3 hits ring again a beat later for 30%. |
| I | Ringing lunge | L → J | Out of the roll, a lunging swing (Ash). J: the right swing. |
| I | Bell drop | L → K | Out of the roll, the bell hauled over and dropped (Ember). |
| I | Air swing | air J | A swing in the air (Ash). |
| I | Bell pogo | air ↓J | Mouth-down onto a foe: pogo off it (Ash). |
| I | Bell plunge | air K | Dive mouth-first: 1.8, and a shock ring where it lands (Ember). |
| II | Chime spin | J J (pause) J | Wait a beat after the 2nd swing: a whirl both sides (0.7 ×2, Ash). |
| II | Mending | Ash Gold Ember → I | Heal 10% max HP over 10 s (once per 60 s). |
| III | Encore | Perform → I | Ring again (1.4) and refresh every toll still sounding. |
| IV | Echo wave | Perform / Encore | The ring rolls on to 64 px both ways (+0.6). |
| V | Grand toll | Perform with 3 notes | Stuns small foes; +60 stance damage to bosses. |

<!-- MOVELIST:END -->

---
## Appendix A. Changelog

### v14 weapon pass: what changed

**What was asked for**
- **No mashing past finishers.** Mashing J should end the combo at its finisher, not roll straight into the next one.
- **Combos turn.** Each step of a combo can turn to face the direction you hold.
- **Shorter Longsword lunges.** Swings shouldn't carry you across the room.
- **A slower, more deliberate Katana**, and a **flash step that doesn't cut** (an attack shouldn't also be a dodge).
- **A deep balance pass** on all nine weapons, played through real inputs against the dummy and real bosses.
- **3–5 new combos per weapon**, each with its own animation.

**What changed**
- **Engine (all weapons):** a new input queue (presses carry over so fast taps aren't lost, but mashing stops at
  finishers), every chain step and L → J turns to the held direction, lunges only travel their full distance while you
  push forward and always end planted, and air strings (air J J) can be pressed just after the first air swing.
  The rules are in Section 2.
- **37 new moves** across the nine types, each marked **(v14)** in the tables: Longsword 4, Katana 4, Greatsword 4,
  Maul 4, Sword & Shield 4, Dual Blades 5, Spear 4, Staff 4, Whip 4. Mastery now has 48 unlocks (was 36).
- **Fixes and balance, per weapon** (details in each section):
  - *Longsword:* lunges shortened; the pommel strike and ember edge now read their inputs reliably; foresight cut costs
    stamina and punishes a whiff.
  - *Katana:* lights and the rushing draw slower; the Iai tap no longer adds delay; the Iai parry costs stamina; flash
    step has no cut; K → K loop toned down.
  - *Greatsword:* a K tap can't out-damage the weapon (180 ms minimum heave); holding K through a swing starts the
    charge; wider level 3 window; wrath and the shoulder tackle reined in; then (v14b) every swing about 25% slower with
    more damage per hit.
  - *Maul:* one clear rule for spin vs earthshaker; earthshaker wave cut to 1.0; the big bounce now works; the brace can
    be left early.
  - *Sword & Shield:* perfect rush registers on the beat (and is weaker: 0.85 / 1.1 / 1.8); holding I keeps the full
    parry window; the perfect-guard bonus expires.
  - *Dual Blades:* Demon chain hits 5–6 lighter; Demon Mode attacks cost half stamina; perfect dodges can't be farmed;
    dash-through cut has no i-frames; Blade Dance armour and the Archfiend trail reduced.
  - *Spear:* the guard poke opens the guard during its thrust; the charge-dash finisher costs stamina and needs a run;
    the charged counter needs a deliberate hold; hops keep you facing the foe.
  - *Staff:* presses during the vault are kept; spinning air moves glide so a vault string fits in one jump; spin costs
    a flat 24 stamina; the dive-kick refund works once per jump; gale actually hits; slightly stronger ground chain.
  - *Whip:* the lash is drawn out to its real reach with a visible tip zone (now the last 30%); thunderclap 2.5 (×1.3 at
    the tip); crack +20 per tipped heavy; grapple stun 0.6 s; snap counter and thousand lashes can't be mashed.
- **In game:** Esc → weapon mastery → Enter (or the **MOVE LIST** button) shows each weapon's full move list (the
  `combos` list of each type), rank by rank.
- **Write-ups and tests:** `docs/revamp2/{blade,heavy,guard,dual,reach}.md` (critique, fixes, new combos, before/after
  benches); route tests in `tools/shots/v14/<group>/routes.js`, benches in `bench.js` next to them.

**v14c: more J / K mixes (round 3)**
- **What was asked for:** more combos that mix J and K both ways: K J, K K, J K J, J J K K and so on.
- **30 more moves**, each with its own animation, marked **(v14c)** in the tables: Longsword 3, Katana 3, Greatsword 3,
  Maul 3, Sword & Shield 4, Dual Blades 4, Spear 4, Staff 3, Whip 3. With v14 that's **67 new moves** since the pass
  began. Mastery now has **54 unlocks**: six of the new moves are rank II unlocks (Greatsword earthsplitter, Maul backswing
  slam, Sword & Shield aegis plant, Dual Blades bloodwheel, Spear sky rake, Whip cyclone); the rest are rank I.
- **Every heavy now branches.** On most weapons K is no longer a dead end: K J and K K lead somewhere (the Greatsword
  and Maul through their charged/upswing releases). None of the new routes beats a weapon's main loop on the dummy;
  they trade damage for stagger, reach, spacing, crowd cover or flow (benches in Section 6).
- **Inputs that changed meaning** (old routes kept where they mattered):
  - *Longsword:* K K is the crosswise strike. The charge stance now needs K **held since the press**, so a fast second
    K no longer starts a charge.
  - *Katana:* J K is the Kesa cut (it used to fall through to the rushing draw); a neutral K still rushes.
  - *Greatsword:* J right after a charged slash is the upheaval (it used to restart the light chain).
  - *Maul:* J → K *tapped* is the side blow; K *held* there still starts the walk-charge.
  - *Sword & Shield:* K J / K K branch off the shield bash; hold K is still the shield rush.
  - *Dual Blades:* K J / K K branch off the lunge and J J K is the hooking cross (they used to restart the chain or lunge
    again).
  - *Spear:* J K / J J K are thrusts inside the chain. To start the charge dash out of a chain, let the chain end first.
  - *Whip:* J K is the tip flick (K alone is still the heavy crack); K → J is the wrench.
  - *Staff:* aerial spin → J is the comet; J K the back vault; K → J the spin vault.
- **Animation fixes (all weapons):** the run and walk cycles no longer moonwalk: the feet plant and push back, a 16 px
  stride over 8 frames of 45 ms. The spear got a full audit: its walk-behind-the-guard cycle was fixed and a back-off
  cycle added (`sp_guard_back`), the guard is a levelled brace, the spear no longer shrinks ("telescopes") on strike
  frames, K plays a real high thrust (`sp_high`), and thrust hits show a "reach ghost" out to their true reach (Section 3.7).
- **Engine:** no change to the shared rules in Section 2.

### v15 overnight update: what changed

**14 weapon types.** Five new types join the nine, each with its own trait, 19–32 moves and Mastery unlocks
(Sections 3.10–3.14): the **Switch Axe** (Gravegrinder), the **Close-range Bow** (Ashstring Recurve), **Martial Arts**
(Penitent's Knuckles), the **Scythe** (Requiem) and the **Warbell** (Dirgebell). The in-game move lists now hold
**310 moves** (Section 7) and Mastery **79 unlocks** (Section 4). Sections 3.10–3.14 was written as a plan before the build and is now
rewritten as built, with each type's deviations from the plan.

**Boss Cores, enchanting and Rekindle** (`docs/v15/cores.md`, all in `web/src/77_cores.js`).
- Each of the 32 bosses drops a **Core** on its first kill (one per boss for the whole save, NG+ included).
- The Ashwright can **enchant** a weapon with a Core (400 cinders; removing is free; a Core sits in one weapon at a
  time). An enchant only touches the weapon's finishers, heavies, counters and charged releases, never ordinary lights,
  arts, plunges or crits: about +8–15% on those moves (a few percent overall), or a utility of that worth. Enchanted
  moves take the Core's colour (slash light, sparks, an idle ember on the blade).
- **Rekindle:** an ember effigy in a defeated boss's arena starts a rematch (all bosses except Venn): +150 Mastery and
  10% of the boss's cinders, no Core or items, and dying in a rematch costs nothing.

**Balance** (`docs/v15/balance.md`). A scripted boss bot benched all 14 types on 25 bosses.
- **All 14 types now land within about 0.89–1.12 of the average boss time to kill** (Section 6); before, the Dual Blades or
  the Katana were fastest on 24 of 25 bosses.
- **Skill tree fixes:** nodes that were dead under the move engine work again (Blade Dancer, Frenzy, Charged Arts,
  Deflect for every type, Fourth Strike reborn as Finishing Blow); Tireless and Flowing Form no longer make attacks free;
  per-hit nodes (Bloodthirst, Leech, Pyre Heart, Soul Siphon, Relentless, Spellblade) now pay by damage or once per move,
  so multi-hit weapons don't multiply them.
- **Per-type attack factors** on the base attack (Section 2): Dual Blades 0.60, Katana 0.80, Martial Arts 0.92, Maul 0.95,
  Whip 1.10, Warbell 1.12, Sword & Shield 1.18, Spear 1.24, Staff 1.25, the rest 1.0. The move tables and dmg/s figures
  here are in AR units and don't change.
- **The Katana's Iai parry and the Bow's limb deflect only fully counter parryable blows**; anything else is turned
  aside for block stamina with no counter (Section 2, Section 3.2, Section 3.11).
- **Guard costs scale with your level** (`mvGuardScale`), so blocking no longer gets worse over the journey (Section 2).
- Weapon-specific: Greatsword swing armour and a ×0.7 charge (Section 3.3), Spear +40% poise (Section 3.7), Whip tip poise ×1.6 (Section 3.9).
- Boss-side: 13 bosses re-tuned, Astrel's supernova no longer always kills, parry stance follows the stance bar's growth.

**Visuals** (`docs/v15/visuals.md`). The knight **leans forward when he runs** (2 px, same stride and timing). With
shaders on, new **dynamic lighting**: soft shadows traced against the walls, rim light, light shafts from suns, moons,
windows and big lamps, a better bloom and a per-region colour mood (all in Settings › Graphics, shaders still off by
default).

---
## Appendix B. Decisions and open questions

**Decided (user)**
- Delete all 50 old weapons and keep **9 default weapons, one per type**: Longsword, Katana, Greatsword, Maul,
  Sword & Shield, Dual Blades, Spear, Staff, Whip. Dagger, Scythe and the First Ember's mirror class are removed, and
  Maul and Greatsword become two separate types.
- Each weapon keeps one **default weapon art**, locked to it.
- **Monster Hunter style:** every type has its own combos, techniques and a unique mechanic. No two types play alike.
- **Controls:** **J** light · **K** heavy · **I** block, or the type's own defensive/special button · **L** roll or step.
- **Weapon Mastery** ranks I–V per type, earned by fighting with it. Each rank unlocks moves, not stats.
- The **Longsword is the easy all-rounder** for starting out.
- **v14:** mashing stops at finishers; combo steps turn; lunges shorter and planted; slower Katana with a non-damaging
  flash step; 3–5 new combos per weapon.
- **v14c:** 3–4 more J / K mixes per weapon (K J, K K, J K J, J J K K …), each with its own animation.

**Open questions** (where the build already behaves one way, it says so; that is not yet a user decision)
1. **Staff and the 2-air-attack limit:** should the Staff be the exception, or stay within the limit?
   *As built:* it stays within the limit. The vault isn't an attack; the vault kick and every air swing count; the dive
   kick's first bounce in a jump refunds one air attack; the double vault (IV) refunds them all once per jump.
2. **No block:** Dual Blades and Whip have no block. OK? *As built:* no block. The Dual Blades defend with the perfect
   dodge, the Whip with spacing and the snap counter (II).
3. **Whip grapple:** can it pull the player to bosses, or only to hook rings and large regular foes?
   *As built:* never bosses (nor boss parts). Small foes are pulled in; large foes and hook rings pull you.
4. **Progression:** how does a weapon get stronger over the run? *Decided:* tempering (+0 to +5 per weapon, kept per
   type), Weapon Mastery ranks (moves, not stats), and boss Cores enchanted at the Ashwright (v15, Section 5).
5. **Switching type:** can you switch mid-journey? *Decided (user):* pick a start weapon at New Game; change weapons
   only at shrines.
6. **Boss drops:** what do bosses drop now that boss weapons are gone? *Decided (user, v15):* Emberstones and cinders,
   plus the boss's Core on the first kill (Section 5).
7. **New Game+:** does mastery carry over? *As built:* yes, and so do Cores and enchants (no duplicate Cores).

---
## Appendix C. Original build plan

*The plan the nine-type revamp was built from (kept for reference; the v14 and v15 passes are in Appendix A).*


**Status:** the nine move tables, the per-type mechanics and Weapon Mastery are built (`web/src/75_moves.js`,
`web/src/76_mech_*.js`, `web/src/74_arsenal9.js`). **The v14 weapon pass is done, with its v14b and v14c rounds:** its
write-ups are `docs/revamp2/{blade,heavy,guard,dual,reach}.md` (v14c in a section at the end of each), its route tests are `tools/shots/v14/<group>/routes.js` (benches in
`bench.js` next to them; groups: `blade`, `heavy`, `guard`, `dual`, `reach`). Some older shared checks in
`tools/shots/wm/` (routes.js, mech.js) still assert pre-v14 numbers (e.g. 4 unlocks per type, the earthshaker's 1.5,
the thunderclap's 3.2); the write-ups list them. **v15 (branch `overnight-v15`) is built too:** five more types (Sections 3.10–3.14), boss Cores, and the 14-type balance pass;
write-ups in `docs/v15/` (one per type plus `balance.md`, `cores.md`, `visuals.md`), route tests in
`tools/shots/v15/<type>/routes.js`, balance benches in `tools/shots/v15/balance/`. The plan below is the original one, kept for reference.

### B1. What changes in the game
| Area | Today | After the revamp |
|---|---|---|
| Weapons | 50 weapons in 10 classes (+ mirror) | 9 weapons, one per type |
| Classes | sword, dagger, great, spear, katana, staff, shield, twin, scythe, whip | longsword, katana, greatsword, maul, sns, dual, spear, staff, whip (dagger and scythe removed; great split into greatsword + maul) |
| Movesets | 3–5-hit light combo + 1 heavy per class | Full move tables per type (Sections 2–4: branches, holds, I/L moves, mastery unlocks) |
| Weapon pickups | 18 weapon items in rooms, ~26 boss weapon rewards, shop entries | Replaced (see open question 6: materials / arts / charms) |
| Boss signatures (SIGS) | 19 boss-weapon effects | Removed with the boss weapons |
| Arts | 28 arts, locked to weapons | 9 default arts (one per type); the rest retired or reused |
| Upgrades | +0 to +5 with Emberstones per weapon | Per open question 4 |
| New | – | Weapon select at New Game, Weapon Mastery ranks I–V, per-type mechanics (spirit/sheathe/charge/brace/demon/guard/vault/crack) |
| Skill tree | Arsenal page: one mastery node per class (10) | Arsenal page re-keyed to the 9 new types |
| Training Grounds | Pick any of 50 weapons | Pick any of 9 types + set mastery rank |

### B2. Phases
**Phase 1 — Core systems (engine)**
- New weapon table (9 entries) and class list; remove the 41 others from data, shops, rooms and rewards.
- Input layer for the new move tables: combo routes with branches (J/K at each step), hold-K charge levels, I and L
  per-type behaviour, timing windows, cancel rules.
- Weapon Mastery: XP per type (hits, kills, boss kills), ranks I–V, unlock checks, a mastery screen.
- Weapon select at New Game (after difficulty): all 9 types with a looping preview and a short description.

**Phase 2 — Per-type mechanics** (one module per type)
Longsword riposte/branches · Katana sheathe + Iai parry + sidestep · Greatsword charge levels + tackle · Maul charge-walk
+ brace + stun meter · SnS block/backhop/flask-out · Dual Blades Demon Mode + Archdemon · Spear guard/counter/hop/charge
dash · Staff vault + momentum · Whip tip crack + grapple.

**Phase 3 — Animation** (the biggest job)
- About **80 new moves** across the nine types (see each weapon's "Animation reuse" line: Longsword 8, Katana 9,
  Greatsword 10, Maul 12, Sword & Shield 7, Dual Blades 9, Spear 9, Staff 8, Whip 8). Each needs frames for the
  player and its weapon overlay. (The v14 pass added 37 more tags and v14c another 30, plus `sp_high` and `sp_guard_back`, in
  `art/player_v14_<group>.py`.)
- Reuse what exists: current sword/katana/great/spear/staff/shield/twin/whip combos, aerials and heavies become the
  base of the new tables; the maul gets its own moves split from the greatsword.
- 9 weapon overlays instead of 50 (smaller sheets: the build gets lighter).

**Phase 4 — Content and progression**
- Replace weapon pickups, boss weapon rewards and shop weapons with the chosen reward type (open question 6).
- Progression system per open question 4.
- Skill tree Arsenal nodes re-keyed to the 9 types; Training Grounds weapon tab rebuilt (type + mastery rank).

**Phase 5 — Balance and testing**
- Benchmark every type (realistic boss bench: openings, stamina, rolls) so sustained damage lands within ±10%, and
  check the balance targets (burst, reach, defense, mobility).
- Re-run the full suite: all rooms, all 32 bosses, parry/breather/strength-matching, saves, controller, mouse, release
  build check.

### B3. Agents (parallel, separate files)
| Agent | Job |
|---|---|
| Systems | Phase 1 + save migration + weapon select + mastery screen |
| Combat | Phase 2 mechanics, move tables, hitboxes, balance numbers |
| Animation (2 agents, split by type) | Phase 3 frames and overlays |
| Content | Phase 4 loot/rewards/shops/skill tree/Training Grounds |
| Lead (integrator) | Merging, benchmarks, full test suite, publishing |

### B4. Old saves
- A save's current weapon maps to its new type (dagger → dual blades? scythe → greatsword? — to decide); its upgrade
  level carries over.
- Every type a save had weapons of starts at mastery rank II, so veterans don't restart from nothing.
- Retired weapons and arts are converted (cinders / Emberstones / the new reward type).

### B5. Risks
- **Animation volume** is the long pole: about 80 new moves. Mitigation: reuse current frames as the base, build the
  Longsword fully first as the template, then the rest in two parallel batches.
- **Input complexity** (branches, holds, timing windows) can feel mushy: tune with buffered inputs and generous
  cancel windows; test with real key presses, not only the bot. (v14 did exactly this: every v14 test drives real
  presses, holds and releases on the 60 Hz clock.)
- **Boss balance** was tuned around current weapons: re-run the strength-matching and difficulty checks after.
- **Air limit**: the Staff vault decision (open question 1) affects every air rule.

### B6. Suggested order
1. Answer the open questions (Sections 2–4).
2. Build the **Longsword end to end** (moves, mastery, select screen, save migration) as the template and play it.
3. Build the other 8 types in two parallel batches.
4. Content + progression, then balance and the full test pass; publish.
