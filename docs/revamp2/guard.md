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
