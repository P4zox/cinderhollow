# v14 weapon pass: guard group (Sword & Shield, Spear)

Files: `web/src/76_mech_guard.js`, `art/player_v14_guard.py` (8 new tags), `tools/shots/v14/guard/` (`routes.js`,
`bench.js`, `explore.js`). Build: `web/dist/v14_guard.html`. No engine change.

I played every move through real inputs in the harness (`explore.js`, then `routes.js`). I tested press timings, hold
lengths, hop directions, guard poke loops, charge-dash loops and perfect-guard projectiles against the dummy. I also
played the new moves against a real boss (Gravetusk, summoned in the Training Grounds; see `bench.js`).

## Critique

### Sword & Shield

**Bugs and hard inputs**

| Area | What I found |
|---|---|
| Perfect rush on the beat | A press on the very frame a cut ends was never "perfect". `mvQueue` stamps the press after the move clock has passed `total`, so `late < 0` and `mvPerfect` rejects it. The 80 ms grace after the move did not apply to the J route either: the late chain path drops the `perfect` flag. Players who press on the rhythm (the natural thing) missed about half the time. |
| Perfect-rush flash | The flash showed on the 2nd cut even when the rush had already been lost. That cut promised a reward the K could not give. |
| Parry when holding I | Holding I turned the parry into the guard at ~95 ms. The 170 ms parry window was halved for anyone who presses and holds. Every block also paid the parry's 10 stamina. |
| Perfect guard (V): counter bonus | The +50% counter bonus never expired. A perfect guard minutes earlier still buffed the next counter. |
| Perfect guard (V): reflect | The reflect also flipped lingering clouds and ticking hazards. Homing missiles kept homing, back onto the player. |

**Fine as is**
- **Perfect rush (II):** learnable. The window is the last 150 ms plus 80 ms after, about 230 ms, with a visible flash. It is
  strong: 3.37/s, the highest sustained route on a "safe" weapon.
- **Shield slam (III):** guard → K any time. It is a straight upgrade of K from the guard. I left it: the guard costs
  time, and bashes are the weapon's stagger tool.
- **Falling bash (IV):** works and pogos.
- **Perfect guard (V):** the 100 ms window is tight, but it is a rank V reward and every try costs a fresh I press.
- **Backhop → leaping slash:** fine. Net +20 px, 1.8 dmg over 1.0 s.
- **Walking while healing:** fine. About 54 px per second of drinking.

### Spear

**Too strong**
- **Guard poke loop:** `sp_gpoke` had `guarding: true` for its whole length. Holding I and tapping J poked at
  **2.25/s while blocking 100% of the time**: near full damage with a permanent frontal block.
- **Charge-dash finisher:** it was free (`cost: 0`) and dealt the full 2.2 from a 0 ms run. The loop "hold K while
  moving 0.43 s, release" did **2.74/s and 70 poise per second for 2 stamina in 3.8 s**. It was the spear's best route,
  and almost free.

**Hard or ambiguous inputs**
- **Charged counter (III):** the check was "K held at any frame 100-140 ms into the counter". It was not too tight; it
  was ambiguous. Any tap held 117 ms or more (most real taps) charged by accident, so at III the quick counter was
  unreliable.
- **Hops:** they turned you to the held direction. Hopping away turned your back, and the guard only blocks frontally.
  The 2nd and 3rd hops of a chain went the same way as the first, whatever you held.

**Smaller issues**
- **Power guard (IV):** free, and K re-armed it forever. It also showed no pose.
- **Heavy guard:** not too safe on its own. It is the cheapest block (5 + 0.5 × dmg), but it chips on big hits and
  pushes you about 33 px out. The poke loop was the safety exploit, not the guard. Turning: the guard never turns (the
  old comment claimed a slow turn). That is fine as the spear's weakness: walking backwards keeps the guard up, and you
  let go of I to turn.
- **Hop poke route:** crashed silently once a route became a function (the hop poke now evaluates it).

## Changes

### Sword & Shield
- **Perfect rush timing:** the "perfect" check is `shPerfect`: the last 150 ms of the move, up to 80 ms after it, and
  the end frame. It rides on the route itself (`sh_1` → J returns `{ id: 'sh_2', perfect }`), so late presses keep it.
- **Perfect rush flash:** on `sh_2` it only shows while the rush is alive.
- **Perfect rush numbers:** 0.85 / **1.1** / **1.8** (was 1.2 / 2.0). The route measures 3.12/s (was 3.37): still
  +23% over J J J J for timing play, but no longer far above every other weapon.
- **Parry / hold:** holding I keeps the full 170 ms parry, then raises the guard. A press that only became a block
  refunds the parry's 10 stamina.
- **Perfect guard bonus:** the +50% expires with its counter window (0.6 s).
- **Perfect guard reflect:** only real missiles (moving, not static, ticking or effect sprites). Homing is off, and they
  are aimed at the nearest foe in front.

### Spear
- **Guard poke:** guarded during its coil (0-110 ms) and recovery (260 ms+), but open during the thrust. Damage 0.9 →
  **0.8**. The loop is now 1.98/s with the guard up 63% of the time.
- **Charge-dash finisher:** costs **12** stamina. It deals the full 2.2 (V 3.0) and 70 poise only after a 400 ms run; a
  quick release is a 1.4 / 40 thrust (V 1.8).
- **Charged counter:** K must be held without a break for **150 ms of real time from its press** (hitstop included). The
  coil carries on, so the charged hit still lands about 360 ms after the press. While K is held, the tip warms (a light)
  as a cue. Taps up to 133 ms stay quick.
- **Hops** keep you facing the foe. You hop forward only while pushing toward it; otherwise you hop back. Chained hops
  follow the same rule (`dodgeUpdate`).
- **Power guard:** not re-armed while it is up, and it shows `sp_pguard` while you stand. It is still free: a
  per-activation cost made big blocks break the guard.

## New combos

| Weapon | Input | Rank | Wind / total ms | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|
| SnS | **J K**: shield jab | I | 110 / 330 | 0.7 | 28 | 9 | A bash woven into the chain. J goes on to the 3rd cut (J K J J = 2.43/s, 66 poise/s vs 55). |
| SnS | **J J J K**: rim upper | I | 200 / 540 | 1.2 | 50 | 14 | An alternative finisher that launches small foes. Jump and keep cutting. |
| SnS | **L → K**: shield charge | I | 200 / 520 | 1.1 | 60 | 14 | Back in behind the shield after a backhop: stagger instead of the leap's damage. |
| SnS | **J J (pause) J**: wheel cut | II | 160 / 560 | 0.6 + 0.7 | 30 | 12 | Wait 100-300 ms after the 2nd cut. A full turn that hits both sides, for crowds. |
| Spear | **J J J K**: impaling drive | I | 220 / 660 | 0.75 + 0.85 | 50 | 16 | Thrust it home and twist it deeper: a stagger finisher (2.54/s vs J J J 2.63). |
| Spear | **L → K**: hop lunge | I | 200 / 540 | 1.3 | 35 | 15 | Off the hop (usually a back hop), a long low lunge back in (50 px). |
| Spear | **J J (pause) J**: wheeling haft | II | 180 / 600 | 0.55 + 0.7 | 30 | 13 | The spear spun flat: tip in front, butt behind. The spear's answer to a crowd. |
| Spear | **counter-thrust → J**: rising sweep | III | 160 / 500 | 1.2 | 40 | 12 | Payoff after a block: the haft swept up overhead, launching small foes. |

Notes on the new combos:
- Each has its own animation (anticipation, smear, impact, follow-through, settle), with a fallback tag after it.
- New rank-gated moves are added to `unlocks`.
- Both types have a full `combos` move list (18 entries each).
- None uses forward or back as a modifier.
- All of them hit Gravetusk in the real-boss pass.

## Bench (x light AR per second; dummy, infinite stamina, from real inputs; `bench.js`)

| Route | Before | After |
|---|---|---|
| SnS J J J J | 2.55 | 2.53 |
| SnS II perfect rush J J K | 3.37 (on the beat: ~50% landed) | 3.12 (all land) |
| SnS J K J J / J J J K / J J . J (II) | – | 2.43 / 2.43 / 2.38 |
| SnS L → J / L → K | 2.0 / – | 2.0 / 1.53 (85 poise/s) |
| Spear J J J | 2.62 | 2.63 |
| Spear guard poke loop | **2.25, guard up 100%** | 1.98, guard up 63% |
| Spear charge dash, quick release | **2.74 for ~0 stamina** | 1.93 (13 stam/s) |
| Spear charge dash, 0.4 s run | – | 2.22 |
| Spear J J J K / J J . J (II) / L → K | – | 2.54 / 2.17 / 1.73 |

Boss bench (`tools/shots/wm/bench.js`, before): SnS 1.11, Spear 1.28 (the highest of the nine; its 60 px reach keeps
hitting where the others fall short). The J chain is unchanged, so this is unchanged.

## Shared WM checks this intentionally breaks

In `tools/shots/wm/routes.js`:
- `spear w10 J w30 -> sp_gpoke`: dmg 0.8 (table 0.9).
- `spear move+hK w50 relK -> sp_finish`: stam 12 (table 0).
- `spear R3 ... -> sp_ccounter`: wind 217 / total 667. The charged counter now starts from the counter's own clock, so
  the hit lands about 360 ms after the K press as the table says; the test times it from the switch.

Already failing before this pass, for every type: `J w6 J w6 J (w6 J)`. With the single-press queue, a press 100 ms
after another, inside the same move, is dropped.

In `tools/shots/wm/mech.js`, "9 types x 4 unlocks" fails: SnS now has 5 unlocks and Spear 6.

---
# v14c: spear animation audit and more J/K combos

## Spear animation audit (every sp_* tag)

I audited all 25 spear tags: the 9 old ones in `gen_player.py`, 11 in `player_v13_b.py`, and the v14 ones, including
the lead's `sp_guard_back`. I checked them in previews at 4x and in game. A per-frame check,
`tools/shots/v14/guard/spear_audit.py`, now reports "shrunk frames: none".

Montages are in `tools/shots/v14/guard/spear_audit/`:
- `before_after_frames.png`: 15 key frames, before and after, from the same renderer as the sheet.
- `before_counters_grid.png` / `after_counters_grid.png`: every frame of the counter, charged counter, finish and drive.
- `after_ingame.png`: in-game shots with the hit box drawn.

### What was wrong

| Problem | Where | Detail |
|---|---|---|
| The spear shrank at the moment of impact | `sp_counter` f2-4 (0.79-0.84), `sp_finish` f2-4 (0.63-0.79), `sp_ccounter` f3-5 (0.63-0.79), `sp_drive` f2-5 (0.63-0.97), `sp_hoplunge` f2-4 (0.63-0.82) | `draw_weapon` shortens a weapon (down to 45%) until it fits the 64 x 40 frame, whose feet sit at x 28. These lunges put the hands 46-49 px out, so the tip would have passed x 63 and the spear was drawn 20-37% shorter on exactly the strike frames. The spear visibly telescoped on every counter. |
| Smaller shrinks | `sp_heavy` f5-6 and `sp_charge_run` (0.97) | Same cause. |
| Vertical spears shrank | `sp_up` f1-3 (0.47-0.87), `sp_down` f1-3 (0.74-0.79), `sp_3` f3 (0.55), `sp_rsweep` f3-4 (0.53-0.61) | Hands too high for an upward spear, or too low for a downward one. |
| Wrong animation on K | `sp_heavy` | The row asked for `sp_high` but the sheet never had it, so K played the level lunge under a box that rose 64 px. |
| Tip flipped in one frame | `sp_wheel` f0 | The tip flipped from forward (the end of `sp_2`) to backward. |
| Guard didn't read as a brace | `sp_guard` | The haft was held up at -36°, like a walking stick, rather than braced at the foe. |
| Thrusts drew ~34 px but hit 60 px out | All thrusts | A frame can only draw about 35 px ahead of the feet, so a 26 px stretch of each thrust's reach was invisible. |

No problems on these points:
- Grip: both hands are always on the haft. The off hand sits 6 px behind on the shaft (7.5 px in the guard).
- Attachment and overlay: the `wpn_spear` overlay lines up with the hands in game.
- Thrusts: every thrust leads with the tip; the only backward tips are swing wind-ups (`sp_3`, `sp_wheel`).

### What I changed

| Fix | Detail |
|---|---|
| Lunge poses | Every lunge keeps hands + body at or under 41 px, so the tip ends at x ~62. The full stretch now reads through the lean instead of a stubby spear. Files: `player_v13_b.py` (counter, finish, charged counter, charge run, guard poke), `gen_player.py` (`sp_heavy`, `sp_3`, `sp_up`, `sp_down`), and my v14 tags. |
| Vertical poses | Hands placed so the whole spear fits: `sp_up` thrusts from shoulder height, `sp_down` rides with the hands at the chest. |
| New `sp_high` tag | A real high thrust: coil low, step in, drive the spear up at 40°. Its box is now -4..50 out, up to 52 high (was 64). |
| Wheeling haft wind-up | The spear rolls up over the head, then round behind. |
| Guard pose | Crouched wide behind a haft levelled at -27°. The lead's walk and back-walk foot fixes are kept; they inherit the pose. |
| Reach ghost | On each thrust's hit, two pale, fading copies of the spear lance on along the thrust line to the real reach (`thrust: deg` on each thrust row; render in `76_mech_guard.js`). What you see is what connects. |
| Overhead sweep reach | `sp_3`'s reach is now its drawn arc (44 px, was 60): a sweep can't show a ghost. |

Frame counts are unchanged except for the new `sp_high`.

## More J/K combos (v14c)

| Weapon | Input | Rank | Wind / total ms | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|
| SnS | **K J**: under-rim cut | I | 110 / 330 | 0.9 | 15 | 9 | After the bash, a fast flat cut from under the shield; J J go on to the 3rd cut and the finisher. |
| SnS | **K K**: shield hammer | I | 220 / 560 | 1.3 | 60 | 16 | The shield hauled overhead and its rim hammered down: a 120-poise stagger pair. |
| SnS | **J K K**: backhand rim bash | I | 200 / 520 | 1.2 | 50 | 15 | Jab, then the shield flung out edge-first in a backhand. |
| SnS | **J J J J K**: aegis plant | II | 200 / 600 | 1.0 | 70 | 14 | The shield planted after the finisher: a stagger on both sides, to make room. |
| Spear | **J K**: twin thrust | I | 150 / 520 | 0.5 + 0.6 | 28 | 13 | A poke at the knee, then the chest; J goes on to the overhead sweep. |
| Spear | **J J K**: recoil thrust | I | 160 / 460 | 1.1 | 25 | 12 | The feet step back 18 px while the spear goes out: poke and keep the wall. |
| Spear | **K J**: falling haft | I | 180 / 520 | 1.2 | 40 | 12 | From the high thrust, raise the spear and chop the haft down in front. |
| Spear | **K K**: sky rake | II | 200 / 560 | 1.3 | 40 | 15 | A second, steeper high thrust that lifts small foes: the spear's anti-air string. |

Each has its own new animation tag. All of them start from real inputs in `routes.js` (48/48 OK) and hit Gravetusk in the
real-boss pass. Hold K is still the shield rush, and hold K while moving is still the charge dash.

Behaviour changes for the spear:
- A K pressed inside the J chain is now the twin or recoil thrust. Previously it was `@K`: the high thrust, or the
  charge dash when moving.
- To start the charge dash out of a chain, let the chain end first.

### Bench (x light AR per second, dummy, real inputs)

| Route | Dmg/s | Poise/s |
|---|---|---|
| SnS J J J J (reference) | 2.53 | 55 |
| SnS K J J J | 2.47 | 80 |
| SnS K K | 2.27 | 111 |
| SnS J K K | 2.29 | 74 |
| SnS J J J J K (II) | 2.40 | 72 |
| Spear J J J (reference) | 2.62 | 38 |
| Spear J K J | 2.41 | 44 |
| Spear J J K | 2.51 | 43 |
| Spear K J | 2.29 | 67 |
| Spear K K (II) | 2.31 | 65 |

All are below each weapon's main combo: they trade damage for stagger, spacing or anti-air.

The shared WM `routes.js` breaks the same 3 checks as before (`sp_gpoke` damage, `sp_finish` stamina,
`sp_ccounter` timing) and nothing new. Every SnS/Spear check in `mech.js` passes.
