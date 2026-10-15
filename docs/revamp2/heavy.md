# v14 weapon pass: Heavy group (Greatsword + Maul)

Files: `web/src/76_mech_heavy.js`, `art/player_v14_heavy.py` (8 new tags), tests in `tools/shots/v14/heavy/`
(`routes.js`: 39 checks, all real inputs, all pass; `bench.js`: table and boss benches; `vis.js`: in-game snapshots).
Build: `BUILD_OUT=web/dist/v14_heavy.html python3 web/build_web.py`.

## Critique: what I found

All of this was found by playing through real inputs (press, hold, release, timing) against the WM dummy and a real boss
(Gravetusk, held in place, real stamina, 40 s).

### Both weapons
- **Holding K after a finisher did nothing (the worst bug).** The new mash rule drops a K pressed early in a finisher.
  Holding it then never starts the charge, because a charge needs a fresh press. Affected routes: J J J → hold K, and
  strong charged slash → hold K below Mastery III. On both heavies you spend 1-1.5 s holding K with nothing happening.
  The WM bench's "lv3 → strong lv3" measured 1.46 (−37%) for this reason. On the Maul, L → K had the same problem: it had
  no roll follow-up, so a K pressed in the roll expired.
- **A K tap out-damaged the whole weapon.** A tap released the level 1 slash 16 ms after the press. GS tap loop: 3.71/s
  on the dummy, against 2.70 for the lv3 loop and 1.99 for J J J. On the boss it was also the GS's best route (1.87).
  On the Maul the tap upswing (60 poise ×1.6 ×1.2) every 0.55 s was the best route for both damage and stun. The light chains
  and the charge, which are the weapons' identity, were pointless.
- **Stun vs bosses: no stunlock.** Bosses get 7 s of stance immunity after a stagger, and their stance max grows ×1.15
  each time. Over 40 s the Maul staggers the boss 4 times (about 9 s of stagger), the Greatsword 2-3 times, the Longsword once.
  That fits "the stunner", and the cap holds, so I left the ×1.6 / ×1.2 multipliers alone.

### Greatsword
- **Light chain (J J J 1.97/s).** It isn't useless for damage per stamina, but it had no way into the charge, and a K tap beat it.
- **Overcharge.** The lv3 window was 800-1300 ms with nothing to warn you before the drop.
- **Wrath (Mastery V).** It also applied to the strong and rolling charges, and with no upper limit at V you just held K
  until it auto-fired at 2.2 s. That gave a guaranteed level 4 with no timing at all.
- **Shoulder tackle: too safe.** You could tackle again and again in one charge. Four tackles in 1.4 s covered 175 px with
  full armour and a 60% damage cut, and every tackle kept the charge.
- **True charged slash.** Within budget: lv3 → strong lv3 → true lv3 is 2.35/s on the dummy, about the same as lv3 → strong
  lv3 at 2.32. It costs about 120 stamina and is gated at Mastery III. I left it unchanged.
- **Guard tackle and rolling heavy** work as designed.

### Maul
- **The big bounce never happened.** ml_down set vy −330 in its hit hook, then the engine's generic pogo overwrote it with
  −245 in the same frame, so the Maul bounced exactly like everything else.
- **Spin vs earthshaker collision.** The spin started at 1.3 s if you were moving (or at any rank below V). The earthshaker
  needed you standing still at 1.4 s. At V, standing still between 1.3 and 1.4 s did nothing; below V, standing still at 1.3 s
  spun. The big-smash window was 400 ms, and walking (the weapon's identity) pushed you into the spin.
- **Earthshaker too big.** 3.0 + a 64 px wave of 1.5 at 100 poise is 4.5 dmg and ~306 stun in one blow, about a full
  boss stagger, and it auto-fired. Big smash also had dead code for it (a `quake` option nothing set).
- **Big Bang (J J J → K → K → K → K).** It is easy to input: each K latches anywhere in its blow, and mashing K plays all
  four and stops. The failure case is pressing K during the 1st or 2nd light, which starts a charge instead. That's correct,
  and the move list now spells the input "J J J → K K K K".
- **Brace.** A 750 ms lock with no follow-up: K and L pressed during it were thrown away.
- **Walk-charge** (60%) and **charge step** work as designed.
- **The new queue rule.** Mashing J stops at the finisher (gs_1 gs_2 gs_3 idle; ml_1 ml_2 ml_3 idle). With the hold fix
  below, slow weapons stay responsive: holding K is never eaten.

## What I changed and why

| Change | Why |
|---|---|
| **Hold-through-the-end (both):** K held as any ground move ends (pressed during that move or the one before, not used by a route) starts the charge (`hvHoldEnd`) | Holding to pre-charge must never be eaten by the mash rule. Taps are still dropped, so mashing still stops at finishers |
| **Minimum heave:** a charge can't release before 180 ms (GS) / 150 ms (Maul) | A tap no longer beats everything. GS tap loop 3.71 → 2.85/s (boss 1.87 → 1.67, below the lv3 loop's 1.76); Maul tap 2.93 → 2.40 |
| GS lights 300/700 → 280/660 (gs_3 320/760 → 320/740) | Slightly less sluggish (1.99 → 2.06/s). Their job is now to feed the K branches |
| GS lv3 window to 1.4 s; the pips blink in the last 200 ms before an overcharge (and before wrath gutters) | A readable, forgiving 600 ms window with a clear "release now" cue |
| GS wrath: plain charge only, 1.4-2.1 s, then it overcharges too (auto-swing 2.6 s); burst r 44 → 40, burn 5 → 4 s on others | Keeps the timing skill at V and keeps the effect modest |
| GS shoulder tackle: once per charge (a 2nd L rolls); damage cut 60% → 50% | No more tackle-spam armour; it stays a strong, MH-like answer |
| GS blade guard opens a 0.7 s counter window (retort) | The chip guard pays something back |
| Maul: spin / earthshaker decided at one moment (1.4 s): moving = spin; standing still = earthshaker (V) or spin (below V); big smash window 900-1400 | One rule, one threshold, 500 ms window; pips blink 200 ms before it |
| Earthshaker wave 64 px / 1.5 / 100 poise → 56 px / 1.0 / 60 | Still the biggest stun in the game, no longer most of a stagger in one press |
| Maul upswing poise 60 → 50 | The tap was the best stun route |
| Maul L → K starts the walk-charge (after the roll's i-frames, 280 ms) | The press used to be lost |
| Maul ground pound bounce: applied after the engine's pogo, 290 (jump 272, plain pogo 245) | The "big bounce" actually happens now (peak 90 px vs 76) |
| Brace: past its 600 ms window any J / L / K leaves at once; a blow absorbed keeps the brace open ≥ 0.4 s for payback | No more dead 150 ms; the payback has a fair window |

## New combos (8)

| Weapon | Input | Rank | Wind / total ms | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|
| GS | **Hilt bash**: J → K / J J → K | I | 180 / 480 | 0.8 | 45 | 12 | Pommel shove. Keep K held: the charge goes on from 400 ms (level 2 at once). Makes lights the fast way into lv3: J → hold K = 2.41/s vs 2.06 for J J J |
| GS | **Momentum cleave**: J J J → K | I | 360 / 820 | 2.4 | 70 | 26 | The light chain's own finisher, a big overhead cleave out of the spin. 2.73/s mixed in; no charge needed |
| GS | **Retort**: block a blow → J (0.7 s, also after letting go of I) | I | 150 / 560 | 1.8 | 60 | 14 | Punish out of the chip guard; blade ripped up out of the floor (counter) |
| GS | **Leaping wide slash**: hold K → L (tackle) → J | III | 260 / 700 | 2.0 / 2.4 / 2.8 by level | 70 | 20 | Tackle through a blow, then cash the charge in at once instead of re-holding |
| Maul | **Payback**: brace a blow → K | I | 160 / 600 | 2.0 | 80 (stun ×2) | 18 | The brace's answer: an uppercut that launches small foes and stuns hard |
| Maul | **Haft jab**: hold K → J | I | 120 / 360 | 0.7 | 45 | 10 | Once per charge: a lunging jab (22 px) that keeps the charge, for mobile brawling and closing in while charging |
| Maul | **Third pound**: double smash → K (tap; hold = a fresh charge) | II | 260 / 700 | 1.6 | 80 | 22 | A third blow into the same spot; an alternative to re-charging (lv2 loop 1.60 → 1.76/s) |
| Maul | **Hammer spike**: air J J | IV | 200 / 500 | 1.3 | 50 | 14 | 2nd air blow, flows on once the spin's hit is out. Spikes small foes down and bounces you a little |

Each has its own animation (anticipation, smear, impact, follow-through, settle) in `art/player_v14_heavy.py`:
`gs_bash gs_mcleave gs_retort gs_leap ml_payback ml_jab ml_pound ml_spike`. Hit boxes are in player_meta.
The full command list is the `combos` array of each mvRegister (18 GS, 19 Maul entries). New unlocks: gs_leap (III),
ml_pound (II), ml_spike (IV).

## Bench (tools/shots/v14/heavy/bench.js; before = this file at HEAD on the same engine)

Table: WM dummy, infinite stamina, hold time counted, dmg/s in light-AR units.

| Route | Before | After |
|---|---|---|
| GS J J J | 1.99 | 2.06 |
| GS K tap loop | **3.71** | 2.85 |
| GS lv3 loop (1.0 s holds; the 0.5 s chain makes it lv3 / strong) | 2.70 | 2.70 |
| GS lv3 → strong lv3 | 2.32 | 2.32 |
| GS J → hold K (bash → lv3) | 1.97 (no bash) | 2.41 |
| GS J J J → K (cleave, then K loop) | 3.31 (K taps) | 2.73 |
| GS III lv3 → strong → true | 2.35 | 2.35 |
| Maul J J J | 2.02 | 2.02 |
| Maul K tap loop | **2.93** | 2.40 |
| Maul lv2 loop / lv3 loop | 1.60 / 1.75 | 1.60 / 1.75 |
| Maul II double → K | n/a | 1.76 |
| Maul V earthshaker loop | 1.87 | 1.66 |

Boss (Gravetusk held in place, real stamina, 40 s): dmg/s, staggers.

| Route | Before | After |
|---|---|---|
| LS J J J J (reference) | 1.49, 1 | 1.49, 1 |
| GS J J J | 1.49, 2 | 1.53, 2 |
| GS K tap | **1.87**, 3 | 1.67, 2 |
| GS lv3 loop | 1.76, 3 | 1.76, 3 |
| GS lv3 → strong lv3 | 1.43, 2 | 1.60, 2 |
| GS J → hold K | 1.39, 2 | 1.72, 3 |
| GS III → true | 1.41, 2 | 1.66, 3 |
| Maul J J J | 1.66, 4 | 1.66, 4 |
| Maul K tap | 1.60, 4 | 1.44, 4 |
| Maul III Big Bang | 1.67, 4 | 1.56, 4 |
| Maul V earthshaker | 1.69, **5** | 1.50, 4 |

The patient routes (pre-charge, bash into charge, strong chain) are now the Greatsword's best. The tap is a fallback.

## Shared WM checks this intentionally breaks
- `wm/routes.js` "greatsword J -> gs_1: wind 267 vs 300" (lights sped up to 280 / 660).
- `wm/mech.js` "ML V: earthshaker ... 1.5" (the wave is 1.0 now).
- `wm/mech.js` "WEAPON_UNLOCKS 9 × 4" was already failing; heavy now has 5 (GS) and 6 (Maul).
- `wm/bench.js` "lv3 -> strong lv3" now measures ~2.3 instead of 1.46: the hold fix, not a test change.

## For the lead
- No engine change. Everything is in my files, using `started` / `tick` / `onQueue` / `on.end` hooks.
- Is the payback's stun ×2 (192 poise high on a boss) right for a reactive move that costs half the blow's HP? I think so,
  since bracing is the Maul's only defence.
- The Maul plunge is 1.8 / 192 poise + a 58 poise wave per jump. The 2-smash limit and stagger immunity cap it, but it's
  the strongest stun per stamina. Left alone (shared plunge rules).
