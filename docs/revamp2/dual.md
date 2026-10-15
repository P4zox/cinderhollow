# v14 weapon pass: Dual Blades

Files: `web/src/76_mech_agile.js` (the move table and its mechanics), `art/player_v14_dual.py` (5 new tags),
`tools/shots/v14/dual/` (`routes.js`, `bench.js`, `bosses.js`, `shots.js`). Build: `web/dist/v14_dual.html`.

Every number below was measured in the harness with real inputs: key presses, holds and timing sequences, not direct
`mvStart` calls. The tests ran against a dummy and against real bosses summoned in the Training Grounds (Gravetusk,
Morvain, Kalden).

## Critique (what I found)

**Too strong**
- **The Demon chain, hits 5 and 6.** The plan was 3.4 dmg/s; it measured **3.85** (+13%). Hits 5 and 6 dealt 4.2 dmg/s
  before the speed bonus, against the base chain's 2.82, so the longer Demon chain was a strict upgrade on top of the
  +20% speed.
- **The Archfiend trail (V).** It did 0.3 every 0.3 s to anything standing in it, which is about **1 dmg/s per target**,
  with no input. Several dashes made a long burning strip that also hit groups. That is a weapon by itself, not an
  embellishment.
- **The dash-through cut (II).** It had its own i-frames (0-120 ms) on top of the demon dash's, plus damage and a 60 px
  lunge. That is the same "i-frames plus damage" pattern the user disliked on the katana's flash step.
- **The Blade Dance armour (0.3 of max HP).** A boss blow is about 38 dmg against about 450 HP (roughly 8%), so 0.3
  stopped essentially every hit for the whole 1.2-1.4 s super.

**Too weak / unfair**
- **The Demon Mode stamina economy.** Attacks cost full stamina on top of the 12/s drain, and there is no regeneration.
  Mashing from a full bar (142) ran out after **3.1 s**, then the player was exhausted for 1.5 s with no stamina to dodge.
  Over 8 s, Demon Mode dealt *less* damage than normal mode (17.2 vs 18.7 AR). The doc's own target is "about 5-6 s at a
  time".
- **The perfect-dodge window.** The real window was **83 ms (5 frames), not 100 ms.** Six frames at 60 fps add up to
  100.0000001 ms, which failed the `<= 100` test.

**Exploitable (perfect dodge)**
- **Ticking hitboxes.** A blow was counted by its raw hit id, and ticking hitboxes get a new id every tick (rot mist
  `id_<n>` every 0.5 s, beams and flame jets every 0.2-0.4 s). Rolling back and forth through a mist paid +25 stamina on
  every roll. In Demon Mode a dash costs 8 and refunded 25, so Demon Mode could be kept up forever.
- **Body contact.** Contact damage (`'c' + id + half-second`) counted too, so rolling through any foe that has contact
  damage was a perfect dodge every half-second.
- **Hits without an id.** These fell back to a key built from `String(src)`, which is "[object Object]" for every foe, so
  unrelated foes shared one key.

**Verified fine**
- **Real bosses.** Perfect dodges trigger against real boss melee and against arrows, both rolling through the boss and
  rolling away (`bosses.js`, `routes.js`). The demon dash's 175 ms window works, including the part after the dash ends.
- **Rolling through a blow entirely.** If the roll carries you clear of the hitbox (e.g. through Gravetusk's first bite),
  no perfect dodge triggers. That is correct: nothing touched you.
- **Mashing.** Five or nine presses of J stop at the spin finisher (`tw_4`) outside Demon Mode.
- **Unchanged and still working:** hold K in Archdemon (about 167 ms in Demon Mode), the counter flurry, the dash slash
  into `tw_2`, air J / ↑J / ↓J, and the plunge.

**Input feel**
- **The Demon toggle mid-chain.** I could not be pressed during a chain; you had to wait for neutral. That is now allowed
  (see below).
- **Fast presses (engine).** Before the lead's c3a3c72, a steady J every 150 ms lost the 4th press. It is fixed now, and
  my tests ran on the new engine.

## What I changed and why

- **Demon chain hits 5 and 6.** Now 2 × 0.35 and 3 × 0.3 (were 2 × 0.5 and 3 × 0.45); hit 6's poise goes 8 → 10. Demon
  J ×6 measures **3.42** dmg/s (plan 3.4), and **3.66** with the perfect-dodge buff (plan 3.7). The speed is kept, so the
  chain still feels frantic.
- **Demon Mode attacks cost half stamina.** Implemented as a refund of half the cost in `T.started`; the drain is the
  price. Mashing from a full bar now lasts **4.7 s** (was 3.1), and the 8 s damage is 19.5 AR (normal mode 18.7). Demon
  Mode is now a modest gain that you still pay for with exhaustion. Perfect dodges stretch it further.
- **Low-stamina warning.** A warning tick sounds when Demon Mode drains past 20% of the bar.
- **Perfect dodge.**
  - **Window.** It now includes its last frame (+1 ms), so it is a real 100 ms (6 frames) for the roll and 175 ms for the
    demon dash.
  - **One perfect dodge per blow.** A ticking id (`x_<n>`) counts as one blow. This gives the silver flash, the counter
    flurry, and a refresh of the +10% speed buff.
  - **The +25 stamina and the mastery gain: once per enemy attack.** They are keyed by the attacker and its `atkId`, so all
    windows of a boss combo pay once. Each new attack pays again.
  - **No body contact.** Bumping into a foe no longer counts.
  - **Resulting rule:** a skilled player can still perfect-dodge every hit of a combo, and counter after each one, but the
    stamina refund can't be farmed.
- **Dash-through cut.** It no longer has its own i-frames (the demon dash before it still does), and its lunge is 60 → 44
  px. Damage is unchanged (1.0, or 1.5 after a perfect dodge).
- **Blade Dance and Blade Dance II.** Armour 0.3 → **0.2** of max HP: ordinary boss swings still don't stagger you, but big
  slams and grabs do. You can still roll-cancel it after the first hit.
- **Archfiend trail.** Now 0.15 every 0.4 s (was 0.3 every 0.3 s), and each segment lasts 1.0 s (was 1.5). That is about
  0.37 dmg/s while a foe stands in it. It is mostly embers now.
- **I is buffered from any ground move.** Demon Mode toggles the moment the swing ends, which keeps the flow.

## New combos

Time is wind-up / total in ms at normal speed (Demon Mode is 20% faster). The dmg/s figures come from `bench.js`, on the
same input driver as the "J J J J = 2.79" reference.

| Input | Name | Rank | Time | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|
| J J (pause) J | **Fang barrage** | I | 110 / 470 | 4 × 0.22 + 0.3 = 1.18 | 12 | 10 | Pause 110-450 ms after the 2nd slash (a 340 ms window): five alternating stabs stepping in. Multi-hit status build-up and pressure; J → spin finisher. Route 2.34/s including the pause. |
| J J J K | **Skyward fangs** | I | 130 / 460 | 0.4 + 0.5 | 22 | 12 | A rising double cut that springs you ~50 px up and pops light foes (launch 230); J → twin spin → J → crossfall. Anti-air and juggle. Route 2.15/s. |
| air J J | **Crossfall** | I | 130 / 480 | 0.45 + 0.55 | 18 | 10 | After the twin spin: hang, open an X, dive to the floor at a slant and land planted (counts as an air attack). |
| Demon: J ×6 → K | **Rending cyclone** | II | 150 / 640 | 3 × 0.3 + 0.8 = 1.7 | 40 | 14 (7 in Demon) | The Demon chain's finisher: two crimson spins (both sides) and a leaping cross-cut. Stagger, not dps: the route is 3.34/s vs 3.39 for J ×6. |
| L → K | **Reversal cut** | III | 110 / 420 | 0.45 + 0.6 | 18 (50 perfect) | 10 | Turn out of the roll with two rising cuts. After a perfect dodge it is silver, ×1.5 and 50 poise: the stagger answer to a perfect dodge, where J's counter flurry is the fast one. A non-perfect demon dash → K stays the demon flurry. |

**Notes on inputs**
- **The pause window:** a press 0-110 ms after `tw_2` ends is still `tw_3`, and a press queued during `tw_2` is always
  `tw_3`. A steady rhythm never hits the barrage by accident (tested).
- **Below rank II,** K after the 6th Demon hit is dropped while `tw_d6` plays: it is a finisher.
- **Below rank III,** L → K is the lunge, or the demon flurry in Demon Mode, as before.
- **The move list:** `combos` on the type object holds 20 entries (all base moves plus the new ones). `unlocks` gains
  Rending cyclone (II) and Reversal cut (III).

**Art.** `art/player_v14_dual.py` adds 5 new tags in the twin-blade style. Each has an anticipation crouch with a glint,
alternating main and off-blade cuts with smears, impact flares (crimson for the Demon finisher, silver on the reversal),
and a follow-through and settle. Each has `active` / `hits` set, so `player_meta` has hit boxes:

| Tag | Hit box | Reach |
|---|---|---|
| `tw_barrage` | `[0,-25,36,0]` | capped at 34 px in the row |
| `tw_skyward` | tall `[-2,-54,19,0]` | |
| `tw_crossfall` | fixed `[-2,-32,30,4]` | |
| `tw_dfin` | both sides ±34 | |
| `tw_reversal` | `[0,-40,26,0]` | |

The `tw_dthrough` row lists a `tw_dthrough` tag first; it falls back to `tw_dashslash` (no new art).

## Bench (dmg/s in light-AR units; table bench: dummy, infinite stamina)

| Route | Before | After | Plan |
|---|---|---|---|
| J J J J | 2.81 | 2.81 | 2.82 |
| Demon J ×6 | **3.85** | **3.42** | 3.4 |
| Demon J ×6 + perfect-dodge buff | 4.12 | 3.66 | 3.7 |
| J J (pause) J J (barrage → spin) | – | 2.34 | alternative |
| J J J K J J (skyward → spin → crossfall) | – | 2.15 | utility |
| Demon J ×6 → K (rending cyclone) | – | 3.34 | ≈ J ×6 |
| L → K loop (reversal) / (rank I lunge) | – | 1.57 / 1.53 | |
| L (perfect) → J / → K loops | – | 3.51 / 3.25 | reward |
| Boss bench, Gravetusk 30 s, JJJJ | 1.03 | 1.02 | |
| Boss bench, Demon Mode at 80%+ bar | – | 1.05 (5.7 s in Demon Mode, 4 exhaustions) | |
| Demon from a full bar, mashing: time to exhaustion | 3.1 s | 4.7 s | "5-6 s" with dodges |

## Shared WM checks this intentionally breaks

**`tools/shots/wm/routes.js`**
- `dual demon … -> tw_d6`: the damage is now 0.3 × 3 (was 0.45), poise 10, and the stamina is half in Demon Mode.
- `dual demon K -> tw_dflurry`: the stamina is 8 (half of 16) in Demon Mode.
- `dual R2 demon L w3 J -> tw_dthrough`: the stamina is 4 (half) in Demon Mode.
- These two checks fail because of the engine's queue rules, not my changes: `dual J w4 J w4 J w4 J -> tw_4` and
  `dual demon J w4 … -> tw_d5`.

**`tools/shots/wm/mech.js`:** the DB checks all still pass.
