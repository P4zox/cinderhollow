# Cinderhollow — Weapon Revamp

**Status:** built, then tuned in the **v14 weapon pass** and its follow-up rounds v14b and v14c (branch
`weapon-revamp`). Part A describes the nine weapons as
they play **now**: every number in the tables is the number in the code (`web/src/75_moves.js` and the
`web/src/76_mech_*.js` files). Part B is the original build plan, kept for reference. When the code changes, change the
tables here with it.

## Contents
- **v14 weapon pass: what changed**
- **Part A: Design**
  - A0. Decisions and open questions
  - A1. Shared rules (how to read the tables, timing, the input queue, turning, lunges, stamina, the air limit)
  - A2–A10. The nine weapons
  - A11. Weapon Mastery
  - A12. Balance comparison
  - A13. Move lists (every weapon's full command list, as in the game)
- **Part B: Build plan**

---
## v14 weapon pass: what changed

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
  The rules are in A1.
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
  they trade damage for stagger, reach, spacing, crowd cover or flow (benches in A12).
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
  frames, K plays a real high thrust (`sp_high`), and thrust hits show a "reach ghost" out to their true reach (A8).
- **Engine:** no change to the shared rules in A1.

---
# Part A — Design

## A0. Decisions and open questions

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
4. **Progression:** how does a weapon get stronger over the run (upgrade levels, boss materials, element infusions)?
5. **Switching type:** can you switch mid-journey, or pick once at the start?
6. **Boss drops:** what do bosses drop now that boss weapons are gone?
7. **New Game+:** does mastery carry over?

## A1. Shared rules

**Reading the tables**
- **Dmg** is a multiplier of the weapon's attack rating. The Longsword's first light hit is 1.0, and every type is
  balanced against that. "2 × 0.45" means two hits of 0.45. A whip value in brackets is the tipped hit (×1.3).
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
    (see A4 and A5).
- **Late presses:** a J pressed within **0.3 s after a move ended** still continues that move's chain (K uses the move's
  own window; e.g. 0.5 s after a Greatsword charged slash). Some combos use this on purpose: "J J (beat) J" means
  pressing the third J a little *after* the second swing ends.
- **Perfect timing** (where a move rewards it): a press in the move's **last 150 ms, on its last frame, or up to 80 ms
  after it ends**. The Longsword's ember edge and the Sword & Shield's perfect rush use slightly wider windows of their
  own (see A2, A6).

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

---
## A2. Longsword: the all-rounder

**Identity:** balanced in everything, easy to learn, with a branching combo that teaches the rest of the game. K
branches off every step of the light chain (J K, J J K, J J J K), and since v14c the heavy branches too (K J, K K).

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

---
## A3. Katana: the patient duelist

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
  - **tapping I just before a hit lands** (150 ms window) is an **Iai parry**: the hit is negated and you counter-cut
    automatically. Each try costs 6 stamina, and a whiff stands you there 270 ms more (420 total).
- **K while drawn** is a rushing draw that **sheathes you again** afterwards, so K → K is a natural loop. The new J J K
  (crescent sheathe), Iai → J → I and Iai → J → K (thrust home) also end sheathed. (J K mid-chain is the Kesa cut,
  not the rushing draw.)

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
| I (sheathed, timed) | **Iai parry** | Counter | 2.4 | 60 | 6 + 12 | window 150 | Hit negated; the counter-cut is 70 / 500, invulnerable 0–260 ms |
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

---
## A4. Greatsword: one huge hit at a time

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
- **While charging** you can't be flinched by hits under 30% of your max HP; you still take damage, at ×0.8.
- **Keep charging (v14):** if K is held as any ground swing ends, the charge starts at once. A K *tap* pressed early in a
  finisher is still dropped (mashing stops), but holding K to pre-charge is never eaten.

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
| I | **Blade guard** | Block | – | – | 1.2 × dmg | – | Frontal only; 25% chip and heavy pushback; **no parry**; a blocked blow opens a 0.7 s counter window |
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

---
## A5. Maul: the stunner

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

---
## A6. Sword & Shield: safe and versatile

**Identity:** the safest weapon. A full block, the fastest swings, a jump-in attack, and the only weapon that drinks
flasks with the blade out.

**Mechanic: guard and utility**
- **Hold I** to block anything frontal. It costs stamina (6 + 0.8 × damage) and has no chip damage. **Tap I** to parry
  (170 ms window, 10 stamina).
  - *v14:* holding I keeps the **whole** 170 ms parry window, then raises the guard (it used to become the guard at
    ~95 ms). A press that only ever blocked gives the parry's 10 stamina back.
- **Flasks with your weapon out:** healing is 30% faster and you can still walk slowly.
- **L is a backhop:** a short hop backwards that leads into the **leaping slash** (J) or the **shield charge** (K).

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

---
## A7. Dual Blades: the frenzy

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

---
## A8. Spear: the walking wall

**Identity:** plant your feet, block anything frontal, and poke the boss to death from behind the guard.

**Mechanic: guard and poke**
- **The I guard** blocks almost anything frontal, **even big hits**.
  - It costs 5 + 0.5 × damage in stamina and pushes you back hard.
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

**Strengths:** the longest poke reach, the strongest guard, safe steady damage, and a gap-closing charge. The best
real-boss numbers of the nine plain chains (its 60 px reach keeps landing).
**Weaknesses:** the least mobile (no roll), low burst, a guard that can't turn, and it struggles with fliers.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Poke | Opener | 1.0 | 14 | 11 | 140 / 380 | 1.5× sword reach (60 px) |
| J K | **Twin thrust** (v14c) | Two-height poke | 0.5 + 0.6 | 28 | 13 | 150 / 520 | A poke at the knee, then the chest; J goes on to the overhead sweep (J K J) |
| J J | Poke II | Pressure | 1.0 | 14 | 11 | 140 / 380 | |
| J J K | **Recoil thrust** (v14c) | Poke and keep the wall | 1.1 | 25 | 12 | 160 / 460 | The feet step back 18 px while the spear goes out; finisher |
| J J J | Overhead sweep | Pressure | 1.15 | 18 | 12 | 160 / 420 | Finisher; 44 px reach, its drawn arc (*v14c: was 60*); hop → J continues the chain |
| J J J K | **Impaling drive** (v14) | Stagger finisher | 0.75 + 0.85 | 50 | 16 | 220 / 660 | Thrust it home, then twist it deeper |
| K | High thrust | Fliers, tall foes | 1.4 | 35 | 18 | 260 / 600 | v14c: a real `sp_high` thrust (coil low, drive up at 40°); box 50 px out, 52 px up (was 64). J: falling haft; K (II): sky rake |
| K J | **Falling haft** (v14c) | Chop down | 1.2 | 40 | 12 | 180 / 520 | From the high thrust, the spear raised and the haft chopped down in front; finisher |
| I (hold) | **Heavy guard** | Block | – | – | 5 + 0.5 × dmg | – | Big hits do 10% chip; walk slowly |
| I + J | **Guard poke** | Safe chip | 0.8 | 12 | 10 | 140 / 380 | Guard up except during the thrust (110–260 ms). *v14: was 0.9 and fully guarded* |
| block → K | **Counter-thrust** | Payoff | 2.0 | 60 | 14 | 160 / 520 | Within 0.5 s |
| hold K (move) | **Charge dash** | Gap-close | 0.4 per 0.3 s | 15 | 8 per second | 400 wind-up | Runs up to 3 s; I stops. From neutral only: a K inside the J chain is a thrust (v14c), so let the chain end first |
| release K | Finishing thrust | Dash payoff | 2.2 (after a 0.4 s run) / 1.4 (sooner) | 70 / 40 | 12 | 120 / 480 | |
| L | **Hop** | Dodge | – | – | 8 | 260 | 0.14 s invulnerable, 40 px; chain 2 |
| L → J | Hop poke | Pressure | 1.0 | 14 | 10 | 120 / 360 | Picks the poke chain up where it left off (within 1.2 s) |
| L → K | **Hop lunge** (v14) | Back in | 1.3 | 35 | 15 | 200 / 540 | Off the hop (usually a back hop), a long low lunge back in (50 px) |
| air J (rising) | **Jump thrust dive** | Dive in | 1.5 | 40 | 16 | – | Attack while rising after a jump |
| air J | Air thrust | Air hit | 1.0 | 14 | 11 | 140 / 360 | |
| ↑J | Sky thrust | Fliers | 1.1 | 20 | 12 | 180 / 420 | |
| air ↓J | Tip-first strike | **Pogo** | 0.9 | 14 | 10 | 100 / 300 | |
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
| II | **Wheeling haft** (v14) | J J (pause) J | Wait a beat (100 ms or more) after the 2nd poke: the spear spun flat, tip in front, butt behind (0.55 + 0.7, 30 poise, 13 stam, 180 / 600). The spear's answer to a crowd |
| II | **Sky rake** (v14c) | K K | A second, steeper high thrust (box 40 px out, 60 px up) that lifts small foes: 1.3 dmg, 40 poise, 15 stam, 200 / 560. The spear's anti-air string |
| III | **Charged counter** | block → hold K | Keep K held without a break for **150 ms from its press**: a 3.0 counter-thrust with 90 poise (360 / 800, the hit about 360 ms after the press). The tip warms while K is held as a cue; taps up to ~133 ms stay quick. *v14: any slightly long tap used to charge by accident* |
| III | **Rising sweep** (v14) | counter-thrust → J | The haft swept up overhead after the counter: 1.2 dmg, 40 poise, 12 stam, 160 / 500; launches small foes |
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

---
## A9. Staff: master of the air

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

---
## A10. Whip: control the space

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

---
## A11. Weapon Mastery

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
- **Unlocks per type (after v14c):** Longsword 5, Katana 5, Greatsword 6, Maul 7, Sword & Shield 6, Dual Blades 7,
  Spear 7, Staff 5, Whip 6: **54** in all (it was 4 per type before v14, 48 after v14). Most new ones sit at rank II, so
  the first rank-up comes with a new combo, not just a tweak. Rank I alone now has 3–4 J / K mixes per weapon on top of
  the light chain.
- A **mastery screen** (Esc → weapon mastery) shows each type's rank, XP bar, the moves learned and the next unlock,
  with its input. **Enter, or the MOVE LIST button, opens the weapon's full move list** (every move, with its input and
  the rank it needs); ↑↓ scroll it, ←→ switch weapon.
- A rank-up shows a banner, "Longsword Mastery III: Foresight cut", and then a short demo of the input.

## A12. Balance comparison

Dmg/s numbers are the v14 and v14c benches: the dummy, infinite stamina, real inputs
(`tools/shots/v14/<group>/bench.js`). "Main combo" is the plain light chain; "best route" is the best sustained route at
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

**Against real bosses** (a crude bot on Gravetusk and others; compare within a weapon, not too precisely across them):
the Katana's Iai loop still leads every weapon by about 15–20% (the fast Iai lands inside openings); the Spear has the
best plain chain (its reach keeps hitting); the Whip at the tip edges out the Longsword but takes more hits; the Maul
staggers the boss most often (about 4 times in 40 s); the Staff's vault cycle deals the least but takes the fewest hits.
The per-group numbers are in `docs/revamp2/`.

**Balance principle:** most types land at about **2.5–2.8 damage per second** on their main chain, and the higher
numbers come with a real cost:
- the Katana's prep time and stamina (42 per K → K loop);
- the Dual Blades' stamina drain, exhaustion, lack of a block, and perfect-dodge timing to reach the top end;
- the Sword & Shield's perfect rush timing (rank II);
- the Whip's spacing precision (the thunderclap pays only at the tip).

Two types sit lower on paper by design: the **Greatsword** (1.83 on lights; its value is the 3.9 single hit inside a
boss opening, flinch-proof charging and stance damage) and the **Whip untipped** (1.93; it's built around the tip).
The safer the weapon (Sword & Shield, Spear), the lower its burst. These numbers are still targets to re-check: Part B's
benchmark re-measures every type against real bosses (openings, stamina, rolls) and tunes them to within ±10%.

<!-- MOVELIST:BEGIN -->
## A13. Move lists (every weapon, as in the game)

The full command list of each weapon, 194 moves in all, exactly as the in-game **Move List** shows it (Esc → weapon mastery → Enter, or the MOVE LIST button). **Rank** is the Weapon Mastery rank that unlocks the move (I = available from the start). Inputs: **J** light, **K** heavy, **I** block / parry / special, **L** roll / step, **↑ / ↓** held, **air** = while airborne, **hold** = keep the button down, **(pause)** = wait a beat before the last press, **→** = right after the previous move. This section is generated from the code by `tools/movelist_doc.py`; the tables in A2–A10 have the timings and numbers.

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
| I | Iai parry | I (sheathed, timed) | Just before a blow lands: negate it and counter-cut (2.4). |
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

<!-- MOVELIST:END -->

---
# Part B — Build plan

**Status:** the nine move tables, the per-type mechanics and Weapon Mastery are built (`web/src/75_moves.js`,
`web/src/76_mech_*.js`, `web/src/74_arsenal9.js`). **The v14 weapon pass is done, with its v14b and v14c rounds:** its
write-ups are `docs/revamp2/{blade,heavy,guard,dual,reach}.md` (v14c in a section at the end of each), its route tests are `tools/shots/v14/<group>/routes.js` (benches in
`bench.js` next to them; groups: `blade`, `heavy`, `guard`, `dual`, `reach`). Some older shared checks in
`tools/shots/wm/` (routes.js, mech.js) still assert pre-v14 numbers (e.g. 4 unlocks per type, the earthshaker's 1.5,
the thunderclap's 3.2); the write-ups list them. The plan below is the original one, kept for reference.

## B1. What changes in the game
| Area | Today | After the revamp |
|---|---|---|
| Weapons | 50 weapons in 10 classes (+ mirror) | 9 weapons, one per type |
| Classes | sword, dagger, great, spear, katana, staff, shield, twin, scythe, whip | longsword, katana, greatsword, maul, sns, dual, spear, staff, whip (dagger and scythe removed; great split into greatsword + maul) |
| Movesets | 3–5-hit light combo + 1 heavy per class | Full move tables per type (Part A: branches, holds, I/L moves, mastery unlocks) |
| Weapon pickups | 18 weapon items in rooms, ~26 boss weapon rewards, shop entries | Replaced (see open question 6: materials / arts / charms) |
| Boss signatures (SIGS) | 19 boss-weapon effects | Removed with the boss weapons |
| Arts | 28 arts, locked to weapons | 9 default arts (one per type); the rest retired or reused |
| Upgrades | +0 to +5 with Emberstones per weapon | Per open question 4 |
| New | – | Weapon select at New Game, Weapon Mastery ranks I–V, per-type mechanics (spirit/sheathe/charge/brace/demon/guard/vault/crack) |
| Skill tree | Arsenal page: one mastery node per class (10) | Arsenal page re-keyed to the 9 new types |
| Training Grounds | Pick any of 50 weapons | Pick any of 9 types + set mastery rank |

## B2. Phases
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

## B3. Agents (parallel, separate files)
| Agent | Job |
|---|---|
| Systems | Phase 1 + save migration + weapon select + mastery screen |
| Combat | Phase 2 mechanics, move tables, hitboxes, balance numbers |
| Animation (2 agents, split by type) | Phase 3 frames and overlays |
| Content | Phase 4 loot/rewards/shops/skill tree/Training Grounds |
| Lead (integrator) | Merging, benchmarks, full test suite, publishing |

## B4. Old saves
- A save's current weapon maps to its new type (dagger → dual blades? scythe → greatsword? — to decide); its upgrade
  level carries over.
- Every type a save had weapons of starts at mastery rank II, so veterans don't restart from nothing.
- Retired weapons and arts are converted (cinders / Emberstones / the new reward type).

## B5. Risks
- **Animation volume** is the long pole: about 80 new moves. Mitigation: reuse current frames as the base, build the
  Longsword fully first as the template, then the rest in two parallel batches.
- **Input complexity** (branches, holds, timing windows) can feel mushy: tune with buffered inputs and generous
  cancel windows; test with real key presses, not only the bot. (v14 did exactly this: every v14 test drives real
  presses, holds and releases on the 60 Hz clock.)
- **Boss balance** was tuned around current weapons: re-run the strength-matching and difficulty checks after.
- **Air limit**: the Staff vault decision (open question 1) affects every air rule.

## B6. Suggested order
1. Answer the open questions (Part A).
2. Build the **Longsword end to end** (moves, mastery, select screen, save migration) as the template and play it.
3. Build the other 8 types in two parallel batches.
4. Content + progression, then balance and the full test pass; publish.
