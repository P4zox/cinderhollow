# Cinderhollow — Weapon Revamp Plan

**Status:** plan under discussion. Nothing is built yet. Part A is the design of the nine weapons, Part B is how it gets
built. Update this file as decisions are made, and build only once the open questions are answered.

## Contents
- **Part A: Design**
  - A0. Decisions and open questions
  - A1. Shared rules (how to read the tables, timing, stamina, the air limit)
  - A2–A10. The nine weapons
  - A11. Weapon Mastery
  - A12. Balance comparison
- **Part B: Build plan**

---
# Part A — Design

## A0. Decisions and open questions

**Decided (user)**
- Delete all 50 current weapons and keep **9 default weapons, one per type**: Longsword, Katana, Greatsword, Maul,
  Sword & Shield, Dual Blades, Spear, Staff, Whip. Dagger, Scythe and the First Ember's mirror class are removed, and
  Maul and Greatsword become two separate types.
- Each weapon keeps one **default weapon art**, locked to it.
- **Monster Hunter style:** every type has its own combos, techniques and a unique mechanic. No two types play alike.
- **Controls:** **J** light · **K** heavy · **I** block, or the type's own defensive/special button · **L** roll or step.
- **Weapon Mastery** ranks I–V per type, earned by fighting with it. Each rank unlocks moves, not stats.
- The **Longsword is the easy all-rounder** for starting out.

**Open questions**
1. **Staff and the 2-air-attack limit:** should the Staff be the exception, or stay within the limit?
2. **No block:** Dual Blades and Whip have no block. OK? (The Dual Blades now defend with the perfect dodge.)
3. **Whip grapple:** can it pull the player to bosses, or only to hook rings and large regular foes?
4. **Progression:** how does a weapon get stronger over the run (upgrade levels, boss materials, element infusions)?
5. **Switching type:** can you switch mid-journey, or pick once at the start?
6. **Boss drops:** what do bosses drop now that boss weapons are gone?
7. **New Game+:** does mastery carry over?

## A1. Shared rules

**Reading the tables**
- **Dmg** is a multiplier of the weapon's attack rating. The Longsword's first light hit is 1.0, and every type is
  balanced against that.
- **Poise** is the stagger power against a foe's stance: a Longsword light is 12, a heavy 45.
- **Stam** is the stamina cost. A new character has about 100 stamina (more with Endurance), regenerating at roughly
  45 per second when you're not attacking.
- **Time** is wind-up / total, in milliseconds:
  - *wind-up* is the delay before the hit lands (how readable and punishable the move is);
  - *total* is how long until you can act again, at normal speed.
- **Dmg/s** is a route's total damage divided by its total time. **Per opening** is the most damage you can land in a
  boss's 1.3-second window between attacks.

**Universal rules (every weapon)**
- **Buffer:** inputs pressed up to 180 ms early are queued.
- **Roll-cancel:** you can cancel into L after a hit lands, except on moves marked *commit*.
- **Branches:** pressing K at a step of the light combo takes that step's heavy branch, if the weapon has one.
- **Holding K** charges heavies (and on the Spear, holding K while moving starts the charge dash).
- **Air limit:** at most **2 airborne attacks**, then you must land, and the lock lasts 0.25 s after landing.
  - A down attack that pogos off a foe, spikes or brambles doesn't count.
  - A plunge (K in the air) uses the existing smash limit.
- **Every weapon has** an up-attack (↑J), a down-attack pogo (↓J in the air) and a plunge (K in the air).

---
## A2. Longsword: the all-rounder

**Identity:** balanced in everything, easy to learn, with a branching combo that teaches the rest of the game.

**Strengths:** good reach, decent speed, a parry with a payoff, no hard commitments except the finisher.
**Weaknesses:** no specialty: less burst than the Katana or Greatsword, less defense than the Sword & Shield or Spear.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Downward slash | Fast opener | 1.0 | 12 | 12 | 160 / 380 | Roll-cancel after the hit |
| J J | Rising slash | Pressure | 1.05 | 12 | 12 | 160 / 380 | Small step forward |
| J J J | Poke | Reach | 1.1 | 14 | 13 | 200 / 420 | +30% reach; chases a backing foe |
| J J J J | **Critical slash** | Payoff | 2.0 | 40 | 18 | 300 / 650 | **Commit** (no roll-cancel) |
| K | Overhead slash | Simple heavy | 1.6 | 45 | 24 | 380 / 700 | |
| hold K | **Charged overhead** | Stance break | 2.4 | 70 | 30 | 450 charge + 380 / 1100 | Blade flashes at full charge |
| J J K | **Horizontal slash** | Crowds, wide | 1.7 | 35 | 22 | 330 / 640 | 150° arc in front |
| J J J K | **Heavy poke** | Long punish | 1.9 | 38 | 24 | 350 / 680 | Lunges 60 px, pierces |
| I | Parry | Defense | – | – | 10 | window 170 | |
| I → J | **Riposte** | Parry payoff | 2.2 | 50 | 10 | 250 / 600 | Within 0.6 s of a parry |
| L | Roll | Dodge | – | – | 16 | 420 | 0.28 s invulnerable |
| L → J | Quick slash | Punish after a dodge | 1.2 | 14 | 12 | 140 / 400 | |
| air J | Air slash | Air hit | 1.0 | 12 | 12 | 150 / 330 | Counts toward the limit |
| air ↑J | Rising cut | Fliers | 1.0 | 12 | 12 | 160 / 360 | |
| air ↓J | Plunge stab | **Pogo** | 0.9 | 12 | 10 | 100 / 300 | Bounces |
| air K | Plunge | Ground slam | 1.5 | 70 | 18 | – | Smash limit |
| Art | **Ashen Crescent** | Ranged wave | per art | | FP | | Default art |

**Routes:** J J J J = 5.15 dmg over 1.83 s (**2.81/s**) · J J K = 3.75 over 1.40 s (2.68/s) · J J J K = 5.05 over
1.88 s (2.69/s) · **Per opening:** J J J = 3.15, or riposte 2.2 after a parry.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Step slash** | L forward → J | A quick forward step-cut instead of a roll (1.2 dmg, 10 stam), to stay close |
| III | **Foresight cut** | I → K | A counter stance (0.4 s). If you're hit during it, the hit is negated and you answer with a 2.8 slash |
| IV | **Pommel strike** | J J J → hold K | A pommel bash: 1.0 dmg with 90 poise, built to break stance |
| V | **Ember edge** | J J J J with perfect timing | The critical slash ignites and a burning follow-up hit lands (+1.2 + burn) |

**Animation reuse:** today's sword combo (`attack1`–`attack4`, `heavy`, `attack_up`, `air_attack`, `attack_down`).
**About 8 new moves:** charged overhead, horizontal slash, heavy poke, riposte, quick slash, step slash, foresight cut,
pommel strike.

---
## A3. Katana: the patient duelist

**Identity:** fewer, bigger cuts drawn from the sheathe. You win by setting up the draw.

**Mechanic: the Sheathe**
- **Tapping I** sheathes the blade (300 ms).
- **While sheathed:**
  - you walk at 70% speed and can't block;
  - **K becomes an Iai draw:** 90 ms wind-up, 2.2 dmg;
  - **tapping I just before a hit lands** (150 ms window) is an **Iai parry**: the hit is negated and you counter-cut
    automatically.
- **K while drawn** is a rushing draw that **sheathes you again** afterwards, so K → K is a natural loop.

**Strengths:** the fastest heavy in the game (Iai), huge burst, a strong counter, a nimble sidestep.
**Weaknesses:** no real block; the triple flurry staggers poorly; the sidestep's invulnerability is short; being caught
sheathed and slow is deadly.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Quick cut | Opener | 0.9 | 10 | 10 | 120 / 330 | |
| J J | Return cut | Pressure | 0.9 | 10 | 10 | 120 / 330 | |
| J J J | **Triple flurry** | Chip | 3 × 0.45 | 18 | 16 | 180 / 600 | Three fast hits; low stagger |
| J J J → I | Flurry sheathe | Set up the Iai | – | – | 4 | 250 | Sheathes straight out of the flurry |
| K (drawn) | Rushing draw | Gap-close | 1.4 | 30 | 20 | 260 / 620 | Dashes 40 px; **sheathes you afterwards** |
| K (sheathed) | **Iai draw** | Burst | 2.2 | 45 | 18 | **90** / 520 | Fastest heavy in the game |
| hold K (sheathed) | **Focus draw** | Dash-through | 2.6 | 55 | 28 | 400 charge + 120 / 900 | Dashes 90 px through the foe; invulnerable for 0.15 s |
| I (drawn) | Sheathe | Stance | – | – | 4 | 300 | |
| I (sheathed, timed) | **Iai parry** | Counter | 2.4 | 60 | 12 | window 150 | Hit negated, automatic counter-cut |
| L | **Sidestep** | Dodge | – | – | 10 | 260 | Only 0.16 s invulnerable, but quick to recover |
| L → J | Step cut | Punish | 1.1 | 12 | 10 | 120 / 360 | |
| air J | Air draw | Air hit | 1.0 | 12 | 12 | 140 / 330 | |
| air ↑J | Crescent | Fliers | 1.0 | 14 | 12 | 160 / 360 | |
| air ↓J | Needle stab | **Pogo** | 0.9 | 10 | 10 | 100 / 280 | |
| air K | Falling draw | Plunge | 1.5 | 60 | 18 | – | |
| Art | **Moonwave** | | | | FP | | |

**Routes:** J J J = 3.15 over 1.26 s (2.50/s) · **K → K loop** = 3.6 over 1.14 s (**3.16/s**, but 38 stamina a loop
and needs the sheathe timed) · **Per opening:** sheathed beforehand, Iai + J J = **4.0**, the best of any weapon if
prepared.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Sheathed stride** | – | Walk at full speed while sheathed |
| III | **Flash step** | L while sheathed | A blink of 80 px through the foe with a 1.6 cut; fully invulnerable |
| IV | **Thousand cuts** | J J J → I | Each flurry hit echoes 0.5 s later (+0.9 total) |
| V | **Moonlit iai** | perfect Iai parry | Time slows to 50% for 0.6 s and your next Iai deals 3.0 |

**Animation reuse:** today's katana combo (`kt_1`–`kt_3`, `kt_heavy`, `kt_up`, `kt_air`, `kt_down`, with the iaido air
draw). **About 9 new moves:** sheathe, sheathed walk and idle, Iai draw, focus draw, Iai parry, sidestep, step cut,
flash step, moonlit counter.

---
## A4. Greatsword: one huge hit at a time

**Identity:** slow, heavy and patient. Read the boss, pre-charge, and release into its opening.

**Mechanic: charge levels**
- How long you hold K sets the level:

  | Level | Hold time | Dmg | Poise |
  |---|---|---|---|
  | 1 | 0–400 ms | 1.8 | 50 |
  | 2 | 400–800 ms | 2.6 | 70 |
  | 3 | 800–1200 ms | **3.6** | 95 |

- Holding past 1.3 s **overcharges** and drops the hit back to level 2.
- **K again within 0.5 s** of a charged slash chains into a **Strong charged slash**: the same levels, ×1.25 damage.
- **While charging** you can't be flinched by hits under 30% of your max HP; you still take damage, at ×0.8.

**Strengths:** the biggest single hits; a flinch-proof charge; stance breaking.
**Weaknesses:** the slowest roll and the weakest light attacks; a guard that takes chip damage; every miss is punished.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Overhead hack | Slow opener | 1.3 | 32 | 20 | 300 / 700 | |
| J J | Wide sweep | Crowds | 1.35 | 32 | 20 | 300 / 700 | 170° arc |
| J J J | Rising arc | Launch | 1.6 | 45 | 22 | 320 / 760 | Launches small foes |
| K / hold K | **Charged slash** | Main damage | 1.8 / 2.6 / 3.6 | 50 / 70 / 95 | 28 / 32 / 36 | hold + 200 / +500 | Flinch-proof while charging |
| K after a charged slash | **Strong charged slash** | Chain | ×1.25 | | +4 | hold + 220 / +560 | Within 0.5 s |
| I | **Blade guard** | Block | – | – | 1.2 × dmg | – | Frontal only; 25% chip and pushback; **no parry** |
| L | Roll (heavy) | Dodge | – | – | 18 | 520 | 0.28 s invulnerable |
| L → K | Rolling heavy | Punish | starts at level 1 | | 28 | | Banks 200 ms of charge |
| air J | Air cleave | Air hit | 1.3 | 40 | 16 | 220 / 560 | **Hangs**: cancels upward speed for 0.15 s |
| air ↑J | Great arc | Fliers | 1.2 | 35 | 16 | 240 / 560 | |
| air ↓J | Two-handed plunge | **Pogo** | 1.1 | 45 | 12 | 140 / 390 | Wider box |
| air K | Earth plunge | Plunge | 1.8 | 90 | 20 | – | |
| Art | **Storm Leap** | | | | FP | | |

**Routes:** J J J = 4.25 over 2.16 s (1.97/s; lights are weak by design) · a level 3 charge, held ahead of time = 3.6 per
0.7 s release · **level 3 → strong level 3** = 8.1 over 3.5 s (**2.31/s**) · **Per opening:** a pre-charged
level 3 = **3.6** in one hit.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Shoulder tackle** | L while charging | A 300 ms tackle (0.6 dmg, 40 poise). You can't be flinched, take 60% less damage, and **keep your charge level** |
| III | **True Charged Slash** | K after a strong charged slash | A two-part slash: 1.5 + **4.5** at full charge |
| IV | **Guard tackle** | block → K | Tackle out of a block straight into a level 2 charge |
| V | **Wrath charge** | hold past level 3 | A fourth level replaces the overcharge: **4.2** + a flame burst + burn |

**Animation reuse:** today's great-weapon set (`gs_1`–`gs_3`, `gs_heavy`, `gs_up`, `gs_air`, `gs_down`). **About 10 new
moves:** a charge pose for each level (×3), the strong charged slash, the true charged slash (two parts), blade guard,
shoulder tackle, wrath charge, rolling heavy.

---
## A5. Maul: the stunner

**Identity:** a brawler that never stops moving. It charges while walking, knocks bosses down, and plays the stun game.

**Mechanic: walk-charge and stun**
- **Holding K** charges while you walk at 60% speed. What you get depends on when you release:

  | Level | Hold time | Move | Dmg | Poise |
  |---|---|---|---|---|
  | 1 | under 450 ms | **Charged upswing** | 1.6 | 60 |
  | 2 | 450–900 ms | **Double smash** | 2 × 1.2 | 55 each |
  | 3 | over 900 ms, released at once | **Big smash** | 3.0 | 90 |
  | 3 | over 900 ms, kept held | **Spinning bludgeon** | 0.5 per spin (up to 4) | 20 |
  | 3, spin released | – | Spin finisher | 2.0 | 90 |

- **Stun:** maul hits fill a boss's stance **×1.6**. Hits to its upper body fill ×1.2 more. A full stance means a
  knockdown.

**Strengths:** the best at stance breaking and knockdowns; mobile charging; a brace that tanks a hit.
**Weaknesses:** short reach and no guard; brace still costs HP; the spin is easy to whiff.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Overhead smash | Opener | 1.2 | 40 | 18 | 260 / 620 | |
| J J | Overhead smash II | Pressure | 1.25 | 40 | 18 | 260 / 620 | |
| J J J | **Upswing** | Big stagger | 1.6 | 70 | 22 | 300 / 720 | Launches small foes |
| hold K (move) | **Walk-charge** | Main damage | see the charge table | | 24 / 28 / 32 | – | 60% walk speed while charging |
| I | **Brace** | Tank one hit | – | – | 15 + 0.5 × dmg | window 600 | Hits can't flinch you and do 50% damage |
| L | Roll | Dodge | – | – | 16 | 460 | **Releases your charge** (unless Mastery II) |
| L → J | Rolling swing | Punish | 1.3 | 35 | 16 | 200 / 560 | |
| air J | Hammer spin | Air hit | 1.2 | 30 | 16 | 200 / 520 | |
| air ↑J | Rising hammer | Fliers | 1.1 | 30 | 14 | 220 / 520 | |
| air ↓J | **Ground pound** | **Pogo** | 1.0 | 50 | 12 | 140 / 380 | Big bounce |
| air K | Meteor plunge | Plunge | 1.8 | 100 | 20 | – | Small shockwave |
| Art | **Tolling Blow** | | | | FP | | |

**Routes:** J J J = 4.05 over 1.96 s (2.07/s, but **×1.6 stun**) · level 2 double smash = 2.4 over 0.9 s release ·
**Per opening:** a pre-charged **big smash 3.0** (90 poise × 1.6 stun).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Charge step** | L while charging | Roll without losing the charge |
| III | **Big Bang** | J J J → K → K → K → K | A timed 4-hit chain: 1.0, 1.0, 1.2, **3.0** (stun ×2) |
| IV | **Steered spin** | while spinning | Steer the spin; each spin does 0.6 |
| V | **Earthshaker** | hold level 3 for 1.4 s | The overcharge sends out a 64 px shockwave: 1.5 dmg, +100 stun |

**Animation reuse:** the great-weapon frames as a base, re-posed with the maul head. **About 12 new moves:** walk-charge
(walk cycle with the maul raised), charged upswing, double smash, big smash, spin loop, spin finisher, brace, the Big
Bang chain (×4), earthshaker.

---
## A6. Sword & Shield: safe and versatile

**Identity:** the safest weapon. A full block, the fastest swings, a jump-in attack, and the only weapon that drinks
flasks with the blade out.

**Mechanic: guard and utility**
- **Hold I** to block anything frontal. It costs stamina (6 + 0.8 × damage) and has no chip damage. **Tap I** to parry.
- **Flasks with your weapon out:** healing is 30% faster and you can still walk slowly.
- **L is a backhop:** a short hop backwards that leads into the **leaping slash**.

**Strengths:** the best defense, the fastest attacks, good stagger from shield bashes, and it's forgiving.
**Weaknesses:** the lowest burst, short reach, and a block that gets broken once your stamina runs out.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Quick slash | Opener | 0.85 | 10 | 9 | 120 / 320 | |
| J J | Return slash | Pressure | 0.85 | 10 | 9 | 120 / 320 | |
| J J J | Cross slash | Pressure | 0.9 | 12 | 10 | 140 / 340 | |
| J J J J | **Shield bash** finisher | Stagger | 1.4 | 55 | 14 | 220 / 560 | Small foes reel |
| K | Shield bash | Stagger | 1.2 | 60 | 16 | 200 / 520 | |
| hold K | **Charged shield rush** | Break stance | 1.8 | 90 | 24 | 350 charge + 220 / 800 | Dashes 70 px |
| I (hold / tap) | Block / parry | Defense | – | – | 6 + 0.8 × dmg / 10 | parry window 170 | |
| I → J | Guard counter | Payoff | 1.9 | 45 | 10 | 200 / 520 | After a block or parry |
| L | **Backhop** | Dodge | – | – | 12 | 300 | 0.14 s invulnerable, short |
| L → J | **Leaping slash** | Gap-close | 1.8 | 40 | 16 | 320 / 700 | Jumps forward with an overhead cut |
| air J | Air slash | Air hit | 0.85 | 10 | 9 | 120 / 300 | |
| air ↑J | Shield uppercut | Fliers | 0.9 | 20 | 10 | 150 / 340 | |
| air ↓J | **Shield surf** | **Pogo** | 0.9 | 20 | 10 | 100 / 300 | Widest pogo box |
| air K | Falling slash | Plunge | 1.4 | 70 | 16 | – | |
| Art | **Aegis** | | | | FP | | |

**Routes:** J J J J = 4.0 over 1.56 s (**2.56/s**) · block → counter 1.9 · **Per opening:** J J J + K ≈ **3.6** (the
bashes stagger, which opens more windows).

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Perfect rush** | J J K, each press on the flash | Each timed hit is stronger: 1.0, 1.2, 2.0 (**3.36/s**) |
| III | **Shield slam** | block → K | A 1.6 slam with 110 poise |
| IV | **Falling bash** | air ↓K | A 1.6 plunge with 80 poise that also pogos |
| V | **Perfect guard** | block within the last 100 ms | Reflects projectiles, takes no stamina, and the next counter deals +50% |

**Animation reuse:** today's sword & shield set (`sh_*`: block, guard, counter, the shield-surf down attack). **About 7
new moves:** shield-bash finisher, charged rush, backhop, leaping slash, perfect rush (×3 timing flashes), shield
slam, falling bash.

---
## A7. Dual Blades: the frenzy

**Identity:** relentless and high-risk. Burn stamina for a flurry and dance around the boss.

**Mechanic: Demon Mode** (toggled with I)
- **Stamina drains** at 12 per second and doesn't regenerate.
- **You swing 20% faster** and your combos get longer.
- **L becomes a demon dash:** 120 ms, 0.12 s invulnerable, 8 stamina, chains twice.
- **The demon gauge:** each hit in Demon Mode fills it by 3%. When it's full you enter **Archdemon**, which lasts 20 s.
  - In Archdemon, the gauge drains at 5% per second.
  - **Hold K** for the **Blade Dance**: eight hits of 0.4, then a 1.0 finisher (4.2 total over 1.4 s), which empties
    the gauge.
- **Running out of stamina** drops you out of Demon Mode, exhausted: stamina won't regenerate for 1.5 s.

**Mechanic: Perfect dodge** (works with the roll and the demon dash)
- A dodge started just before a hit would land is a perfect dodge. The window depends on the dodge:
  - **normal roll: 100 ms** (precise; the reward for a well-read roll);
  - **demon dash: 175 ms** (more forgiving, which pushes you to play in Demon Mode).
- The hit is avoided, time flickers for a moment, and a silver afterimage is left behind.
- **Stamina:** a perfect dodge **restores 25 stamina at once**, even in Demon Mode, where stamina normally doesn't
  regenerate. That makes it the main way to stay in Demon Mode longer.
- **Attack speed:** a perfect dodge grants **+0.1 attack speed** (+10%) for **6 s**.
  - It **doesn't stack**; each new perfect dodge refreshes it back to 6 s.
  - It adds to Demon Mode's +20%, for **+30% at most**.
- **Rules:**
  - Only one perfect dodge counts per boss attack, so you can't farm one long hitbox.
  - It works against bosses, elites and regular foes alike.
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
| J J J J | Spin | Finisher | 1.2 | 20 | 12 | 220 / 520 | |
| J ×5 / ×6 (Demon) | Demon flurry chain | Extend | 2 × 0.5 / 3 × 0.45 | 8 | 8 / 10 | 100 / 280 | Demon Mode only |
| K | Lunge | Gap-close | 1.1 | 15 | 12 | 200 / 480 | Dashes 60 px |
| K (Demon) | **Demon flurry** | Burst | 6 × 0.3 | 30 | 16 | 150 / 800 | |
| hold K (Archdemon) | **Blade Dance** | Big finisher | 8 × 0.4 + 1.0 | 60 | – | 1400 | Empties the gauge |
| I | **Demon Mode** toggle | Mode | – | – | drain 12/s | 200 | **No block** |
| L | Roll / demon dash | Dodge | – | – | 16 / 8 | 420 / 120 | **Perfect dodge** if timed within 100 ms (roll) / 175 ms (demon dash) of a hit: +25 stamina, +0.1 attack speed for 6 s (refreshes) |
| L (perfect) → J | **Counter flurry** | Perfect-dodge payoff | 3 × 0.45 | 15 | 8 | 80 / 300 | Comes out instantly after a perfect dodge |
| L → J | Dash slash | Punish | 1.0 | 10 | 8 | 100 / 320 | |
| air J | Twin spin | Air hit | 2 × 0.45 | 8 | 9 | 120 / 330 | |
| air ↑J | Scissor up-cut | Fliers | 2 × 0.45 | 8 | 9 | 140 / 340 | |
| air ↓J | **Drill** | **Pogo** | 3 × 0.3 | 10 | 10 | 100 / 320 | |
| air K | Twin plunge | Plunge | 1.3 | 50 | 16 | – | |
| Art | **Twin Tempest** | | | | FP | | |

**Routes:** J J J J = 4.0 over 1.42 s (**2.82/s**) · in Demon Mode, 20% faster with longer chains: ≈ **3.4/s**, but
only for about 5–6 s at a time · **in Demon Mode with the perfect-dodge buff** (+30% speed): ≈ **3.7/s**, and each
perfect dodge's +25 stamina extends Demon Mode by about 2 s · **Per opening:** in Demon Mode, about **4.4**; the
Blade Dance gives 4.2 by itself.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Dash-through cut** | demon dash → J | Cut through the foe as you dash: 1.0 dmg, 15 poise. After a perfect dodge it deals 1.5 |
| III | **Blade Dance II** | hold K (Archdemon) | Three more hits and a cross-cut finisher (+1.5) |
| IV | **Iron lungs** | – | The Demon Mode drain drops from 12/s to 8/s |
| V | **Archfiend** | – | Archdemon lasts 30 s, and your dashes leave a burning trail (0.3 per tick) |

**Animation reuse:** today's twin set (`tw_1`–`tw_5`, `tw_heavy`, `tw_up`, `tw_air`, `tw_down`). **About 9 new moves:**
demon stance and aura, demon chain hits 5–6, demon flurry, demon dash, Blade Dance (long), dash slash, the Archdemon
aura variant, and the perfect-dodge afterimage plus counter flurry.

---
## A8. Spear: the walking wall

**Identity:** plant your feet, block anything frontal, and poke the boss to death from behind the guard.

**Mechanic: guard and poke**
- **The I guard** blocks almost anything frontal, **even big hits**.
  - It costs 5 + 0.5 × damage in stamina and pushes you back hard.
  - Hits worth more than 30% of your max HP still do 10% chip damage.
  - You can walk slowly while guarding.
- **Guard poke:** I + J attacks without dropping your guard.
- **Counter-thrust:** I then K, within 0.5 s of a block.
- **Hop (L):** a short hop instead of a roll. Chain two, or three with Mastery II.
- **Charge dash:** hold K while moving to wind up for 400 ms, then run for up to 3 s, hitting every 0.3 s. Release K
  for a finishing thrust, or press I to stop.

**Strengths:** the longest poke reach, the strongest guard, safe steady damage, and a gap-closing charge.
**Weaknesses:** the least mobile (no roll), low burst, a slow turn while guarding, and struggles with fliers.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Poke | Opener | 1.0 | 14 | 11 | 140 / 380 | 1.5× sword reach |
| J J | Poke II | Pressure | 1.0 | 14 | 11 | 140 / 380 | |
| J J J | Poke III | Pressure | 1.15 | 18 | 12 | 160 / 420 | Hop → J continues the chain |
| K | High thrust | Fliers, tall foes | 1.4 | 35 | 18 | 260 / 600 | Upward arc |
| I (hold) | **Heavy guard** | Block | – | – | 5 + 0.5 × dmg | – | Big hits do 10% chip |
| I + J | **Guard poke** | Safe chip | 0.9 | 12 | 10 | 140 / 380 | Guard stays up |
| block → K | **Counter-thrust** | Payoff | 2.0 | 60 | 14 | 160 / 520 | Within 0.5 s |
| hold K (move) | **Charge dash** | Gap-close | 0.4 per 0.3 s | 15 | 8 per second | 400 wind-up | Release: **finishing thrust 2.2** (70 poise) |
| L | **Hop** | Dodge | – | – | 8 | 260 | 0.14 s invulnerable; chain 2 |
| L → J | Hop poke | Pressure | 1.0 | 14 | 10 | 120 / 360 | |
| air J (rising) | **Jump thrust dive** | Dive in | 1.5 | 40 | 16 | – | Attack while rising after a jump |
| air ↑J | Sky thrust | Fliers | 1.1 | 20 | 12 | 180 / 420 | |
| air ↓J | Tip-first strike | **Pogo** | 0.9 | 14 | 10 | 100 / 300 | |
| air K | Lance plunge | Plunge | 1.5 | 70 | 18 | – | |
| Art | **Thunder Lunge** | | | | FP | | |

**Routes:** J J J = 3.15 over 1.18 s (2.67/s) · poke → hop → poke rhythm ≈ 2.6/s while staying out of reach ·
**Per opening:** J J J = 3.15, or **block → counter-thrust 2.0** against any attack you block.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Triple hop** | L L L | Chain three hops |
| III | **Charged counter** | block → hold K | A 3.0 counter-thrust with 90 poise |
| IV | **Power guard** | I + K | For 1 s: no pushback and no chip from anything; stamina cost ×1.5 |
| V | **Thunder charge** | charge dash | The dash pierces with lightning (+0.5 per hit) and the finisher deals 3.0 |

**Animation reuse:** today's spear set (`sp_1`–`sp_3`, `sp_heavy`, `sp_up`, `sp_air`, `sp_down`, and the spear dive).
**About 9 new moves:** guard stance and guard walk, guard poke, counter-thrust, hop, charge-dash run cycle, finishing
thrust, power guard, charged counter.

---
## A9. Staff: master of the air

**Identity:** vault over the boss, fight from above, and never stand where it swings.

**Mechanic: vault and momentum**
- **I vaults** you off the staff: 350 ms, about 2.2 tiles up and forward.
  - Invulnerable for the first 0.2 s; costs 15 stamina.
  - **The vault itself isn't an attack**, so it doesn't count toward the air limit (see open question 1).
- **Both ends hit:** combo hits strike in front and slightly behind.
- **Momentum:** each air hit adds a stack, up to 3, for +8% damage each.
  - Stacks last until 0.5 s after landing.
  - Your first ground swing after landing keeps them.

**Strengths:** the best evasion (it's hard to be where the boss swings), hits on both sides, momentum burst, good
against fliers.
**Weaknesses:** low poise, weak on the ground, the air limit caps its burst, and it punishes mistimed vaults.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Strike | Opener | 0.85 | 12 | 10 | 140 / 360 | |
| J J | Butt strike | Both sides | 0.85 | 12 | 10 | 140 / 360 | Also hits behind |
| J J J | Low sweep | Trip | 0.9 | 16 | 11 | 160 / 380 | Trips small foes |
| J J J J | Overhead | Finisher | 1.4 | 35 | 14 | 240 / 560 | |
| K | **360° spin** | Both sides | 2 × 0.8 | 60 | 30% of max stamina | 220 / 640 | Front and back |
| I | **Vault** | Mobility | – | – | 15 | 350 | Invulnerable for 0.2 s; not an attack |
| L | Roll | Dodge | – | – | 16 | 420 | |
| L → J | Low sweep | Punish | 1.1 | 20 | 10 | 140 / 380 | |
| air J | Aerial strike | Air hit (+1 momentum) | 0.9 | 14 | 10 | 120 / 320 | |
| air K | **Aerial spin** | Both sides (+1) | 1.4 | 40 | 16 | 180 / 460 | Counts toward the limit |
| air ↑J | Rising twirl | Fliers | 0.9 | 14 | 10 | 140 / 340 | |
| air ↓J | **Dive kick** | **Pogo** (+1) | 1.0 | 30 | 10 | 100 / 300 | Bouncing refunds one air attack |
| Art | **Whirlwind** | | | | FP | | |

**Routes:** J J J J = 4.0 over 1.66 s (2.41/s) · vault cycle (vault, J, K, dive kick) = 3.3 at +8–24% momentum ≈ **3.8
over 1.7 s (2.2/s)**, spent mostly out of reach · **Per opening:** vault in, aerial spin, then dive ≈ **3.0**, with
almost no risk.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Roll vault** | L → I | Vault straight out of a roll |
| III | **Spin finisher** | air K → K | A second aerial spin: 1.8 dmg, uses one air attack |
| IV | **Double vault** | I in the air near a foe | Vault off the foe's head; refunds the air attacks once per jump |
| V | **Gale** | K with 3 momentum stacks | The spin becomes a travelling tornado: 3 hits of 0.6 |

**Animation reuse:** today's staff set (`st_1`–`st_4`, the `st_heavy` spin, `st_up`, `st_air`, `st_down`, and the
pole-vault down attack). **About 8 new moves:** vault launch, aerial spin, dive kick, low sweep, rising twirl, roll
vault, spin finisher, gale tornado.

---
## A10. Whip: control the space

**Identity:** a precision spacer. Fight at the very end of the lash, crack the tip for big damage, and drag things
where you want them.

**Mechanic: tip crack and grapple**
- **The tip:** the last 25% of a lash's reach deals **×1.3** damage and fills the **crack meter** (+10 for a light,
  +25 for a heavy).
- **At 100 crack,** your next K is a **thunderclap**: 3.2 dmg, 90 poise, a small blast and a stagger.
- **I grapples** (4 tiles, 2 s cooldown):
  - a small foe is pulled to you, stunned for 0.5 s;
  - a large foe or hook ring pulls **you** to it (whether bosses count is open question 3).

**Strengths:** the longest reach in the game, safe spacing, crowd control, huge damage with good tip accuracy.
**Weaknesses:** **no block**, weak up close, damage depends on precise spacing, and the hardest weapon to master.

| Input | Move | Job | Dmg | Poise | Stam | Time | Notes |
|---|---|---|---|---|---|---|---|
| J | Lash | Opener | 0.8 (tip 1.04) | 8 | 9 | 160 / 400 | 2× sword reach |
| J J | Lash II | Pressure | 0.8 (tip 1.04) | 8 | 9 | 160 / 400 | |
| J J J | **Whirl lash** | Both sides | 1.1 | 20 | 14 | 260 / 620 | Front and back |
| K | Heavy crack | Main damage | 1.4 (tip 1.82) | 30 | 18 | 300 / 680 | +25 crack on a tip hit |
| hold K | Overhead crack | Long reach | 2.0 | 45 | 24 | 500 charge + 300 / 1100 | 2.4× sword reach |
| K at 100 crack | **Thunderclap** | Burst | 3.2 | 90 | 20 | 300 / 700 | Small blast and a stagger |
| I | **Grapple** | Pull | – | – | 14 | 300 | 4 tiles, 2 s cooldown |
| L | Roll | Dodge | – | – | 16 | 420 | |
| L → J | Retreat lash | Kite | 1.0 | 10 | 10 | 160 / 420 | Hits while backing off 40 px |
| air J | Circular lash | Both sides | 0.9 | 12 | 10 | 160 / 380 | |
| air ↑J | Vertical crack | Fliers | 0.9 | 14 | 10 | 160 / 380 | Tip flare |
| air ↓J | Down crack | **Pogo** | 0.9 | 12 | 10 | 120 / 320 | Long box below |
| air K | Lash plunge | Plunge | 1.3 | 50 | 16 | – | |
| Art | **Lash** | | | | FP | | |

**Routes:** J J J untipped = 2.7 over 1.42 s (1.9/s); **tipped ≈ 3.18 (2.24/s)** · tipped K = 1.82 per 0.68 s (**2.68/s**)
· **Per opening:** tipped J J + K ≈ **3.9** from the safest range in the game, or a thunderclap at 3.2.

**Mastery**

| Rank | Unlock | Input | Effect |
|---|---|---|---|
| II | **Snap counter** | I within 150 ms of a hit | Lashes the attacker out of its move: the hit is negated, small foes stagger, a boss takes +60 stance |
| III | **Grapple slam** | grapple → K | Pull a small foe in and slam it: 1.6 dmg, stunned |
| IV | **Double crack** | K → K | A follow-up crack: 1.4 then 1.8, both with tip bonuses |
| V | **Thousand lashes** | hold J | A held flurry: 8 × 0.45, tip-only, so it's a spacing test |

**Animation reuse:** today's whip set (`wh_1`–`wh_3`, `wh_heavy`, `wh_up`, `wh_air`, `wh_down`, the lash physics).
**About 8 new moves:** overhead crack, thunderclap, grapple throw and pull, retreat lash, snap counter, grapple slam,
double crack, thousand lashes.

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
  | A successful parry, block counter, Iai parry or snap counter | 5 |

- **Ranks:**

  | Rank | XP | Roughly when |
  |---|---|---|
  | II | 300 | Early: the second region with one weapon |
  | III | 900 | Mid-game |
  | IV | 2,000 | Late-game |
  | V | 4,000 | End-game, or a dedicated main |

- **Unlocks are moves, not stats.** A rank-I weapon is complete and viable; ranks add options and style.
- A **mastery screen** (in the equipment menu) shows each type's rank, XP bar, the moves learned and the next unlock,
  with its input.
- A rank-up shows a banner, "Longsword Mastery III: Foresight cut", and then a short demo of the input.

## A12. Balance comparison

| Weapon | Main combo dmg/s | Best route dmg/s | Per opening | Defense | Mobility | Reach | Difficulty |
|---|---|---|---|---|---|---|---|
| Longsword | 2.81 | 2.81 | 3.15 (riposte 2.2) | Parry | Roll | Mid | ★ |
| Katana | 2.50 | 3.16 (K → K loop) | **4.0** (prepared Iai) | Iai parry | Sidestep | Mid | ★★★★ |
| Greatsword | 1.97 | 2.31 (charge chain) | **3.6** (one hit) | Chip guard | Slow roll | Mid | ★★★ |
| Maul | 2.07 | 2.67 (×1.6 stun) | 3.0 + knockdown | Brace | Walk-charge | Short | ★★★ |
| Sword & Shield | 2.56 | 3.36 (perfect rush, IV) | 3.6 | **Full block + parry** | Backhop | Short | ★ |
| Dual Blades | 2.82 | **3.4** (Demon) / 3.7 with the perfect-dodge buff | 4.4 | None (perfect dodge) | **Demon dash** | Shortest | ★★★★ |
| Spear | 2.67 | 2.67 | 3.15 / counter 2.0 | **Heavy guard** | Hop | **Long** | ★★ |
| Staff | 2.41 | 2.2 in the air (safe) | 3.0 | Vault evasion | **Vault** | Mid | ★★★★ |
| Whip | 1.90 untipped | 2.68 (tipped K) | 3.9 | None | Roll | **Longest** | ★★★★★ |

**Balance principle:** every type lands at about **2.5–2.8 damage per second** of sustained play, and the higher numbers
come with a real cost:
- the Katana's prep time;
- the Dual Blades' stamina drain, lack of a block, and perfect-dodge timing to reach the top end;
- the Greatsword's commitment to each swing;
- the Whip's spacing precision.

The safer the weapon (Sword & Shield, Spear), the lower its burst. These numbers are targets: Part B's benchmark
re-measures every type against real bosses (openings, stamina, rolls) and tunes them to within ±10%.

---
# Part B — Build plan

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
  player and its weapon overlay.
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
  cancel windows; test with real key presses, not only the bot.
- **Boss balance** was tuned around current weapons: re-run the strength-matching and difficulty checks after.
- **Air limit**: the Staff vault decision (open question 1) affects every air rule.

## B6. Suggested order
1. Answer the open questions (Part A).
2. Build the **Longsword end to end** (moves, mastery, select screen, save migration) as the template and play it.
3. Build the other 8 types in two parallel batches.
4. Content + progression, then balance and the full test pass; publish.
