# v14 weapon pass: Blade group (Longsword, Katana)

Files: `web/src/76_mech_blade.js`, `art/player_v14_blade.py`, tests in `tools/shots/v14/blade/`
(`routes.js` is the new-combo route test, 30/30; `probe.js` is the critique measurements; `bench.js` is the dummy and real-boss
bench; `shots.js` takes in-game frames). Build: `web/dist/v14_blade.html`.

Every test drives real inputs (press/hold/release on the 60 Hz clock). None of them call `mvStart` directly.

## 1. Critique

### Longsword
| Finding | Evidence (probe.js / routes.js) | Verdict |
|---|---|---|
| Forward travel | Per move, standing / holding forward (px): attack2 9/18, attack3 10/21, attack4 12/23, heavy 12/23, charged 14/27, heavy poke 20/**39**, riposte 13/25, quick slash 14/24 (+ the roll), foresight cut 18/**36**, step slash 37 (+12 of roll) | Mostly fine after the lead's pass. The heavy poke (39) and foresight cut (36) were still over the ~30-36 px budget. Step slash is a deliberate dash. |
| Pommel input (J J J → hold K) was unreliable | A K held for 250 ms but pressed early in the poke gave the **heavy poke**, because the hold was only checked when the poke ended, by which time K was already released. A K pressed just after the poke and held needed 150 ms by the 160 ms mark, so it missed by one frame (`at30f_hold250 → ls_jjjk`). | Bug: hard to perform |
| Ember edge "perfect timing" | The window was the poke's last 150 ms. A press on the poke's last frame failed (it counted as late = −13 ms). The "within 80 ms after" clause never worked, because mvNeutral's post-move path didn't pass `perfect` to string routes. The real window was about 150 ms, with no lead-in cue. | Hard to learn |
| Foresight (I → K) | Easy to input: K works up to 20 frames after I. But it was free (0 stamina) and gave a 400 ms negation of **any** blow, and the stance ended exactly when the window did. Mashing I K negated **10/12** blows. | Too strong (near-permanent invulnerability plus an auto 2.8 counter) |
| Charge hold | You couldn't turn while holding K. The heavy's hold was checked in a 50 ms slot (150-200 ms in). | Feel: added turning; the slot is now 80 ms |
| Fast J J K | Typed at ~100 ms gaps, the K was dropped (one-press queue plus 180 ms buffer). | Fixed by the lead's mvQ2 (c3a3c72); the routes now pass |
| Balance | J J J J 2.74 dmg/s, J J K 2.62, J J J K 2.68 (dummy). Real bosses: Gravetusk 1.15-1.20, Omen 0.81-0.93 (mid-pack) | OK: the all-rounder |

### Katana
| Finding | Evidence | Verdict |
|---|---|---|
| Iai on a K **tap** was delayed by the tap | A sheathed K press goes through the focus-hold state until release, so press-to-hit was 150 / 200 / 233 / 283 ms for 1 / 4 / 6 / 9-frame taps. The "fastest heavy" was slower than a light for normal taps. | Bug: the input felt laggy |
| Iai parry spam | `kt_iaiw` cost 0 stamina and recovered at 300 ms with a 150 ms window. Mashing I while sheathed negated **10/12** blows of any kind. | Exploit |
| Thousand cuts | Echoes came from `P.ktFlurry`, which was never cleared unless the flurry sheathe ran, so a later sheathe could echo old hits. | Bug (latent; reachable once Iai → J → I exists) |
| Moonlit iai | The slow-time is 0.43 s at 0.35x for **both** sides (cinematic). The 3.0 Iai was kept forever, even across rooms. | Slow-time is fine (not too strong); the buff now expires after 8 s and the HUD ring drains |
| Flash step (lead) | 49 px, no damage, inv 0-240 ms, 14 stamina, stays sheathed | Fine |
| Slower katana (lead) | kt_1/kt_2 380 ms, flurry 680 ms. J J J is 2.17 dmg/s, the lowest blade route, which is right for a chain that isn't the katana's game. | Feels deliberate. The fun is in the sheathe/draw routes (below). |
| K → K loop | 2.70 dmg/s on the dummy, about equal to the Longsword. Against real bosses (bot) it was the best route of any weapon: Gravetusk 1.51, Omen 1.34, with the fewest hits taken. The fast Iai lands inside openings, and the rush re-sheathes for free. | Too strong vs bosses; toned down (see 2) |
| Focus draw hold | Easy (400 ms). It couldn't turn during the hold. | Added turning |
| Sheathed J | J while sheathed silently played kt_1 and drew the blade | A missed identity beat; now the draw cut |

## 2. Changes (and why)
Longsword
- **Pommel:** the poke records when the queued K is released. K held ≥150 ms gives the pommel, wherever the hold happened (during the poke, or straight after it, up to 230 ms into the heavy poke). A tap gives the heavy poke. Probe: every 160/250 ms hold gives the pommel, every 100 ms tap gives the poke.
- **Ember edge:** the window is the last 160 ms of the poke, plus 20 ms of grace, through 100 ms after it ends (~280 ms). It is computed in my own route (`lsPerfect`), so it doesn't depend on the engine. Cue: at rank V the poke's tip lights up and a soft tick plays for exactly that window.
- **Foresight:** the stance costs 8 stamina (18 total with the parry). The window is 320 ms, and a whiff adds 200 ms of recovery. Mash test: 10/12 → 3/12 negated.
- **Travel:** heavy poke lunge 34 → 30 (35 px held forward). Foresight cut 34 → 28 (29 px).
- **Charge hold turns** with the stick. The heavy's hold check is 150-230 ms.
- Up+J queued into a function route still plays the up slash (`lsUpJ`).

Katana
- **Iai tap:** releasing before focus starts the Iai with its clock advanced by the time K was held (≤60 ms), so a tap adds no delay. Press-to-hit is now 117 / 133 / 167 / 217 ms (was 150 / 200 / 233 / 283).
- **Iai parry:** 6 stamina per try, total 300 → 420 ms (a whiff stands you 270 ms). Mash test: 10/12 → 3/12 negated. The window is still 150 ms (perfect ≤60 ms).
- **Rushing draw** (K → K's gap-closer) is toned down: dmg 1.4 → 1.3, poise 30 → 22, stamina 20 → 24, total 700 → 760 (a slower chiburi before the re-sheathe). **Iai** poise 45 → 40. K → K dropped from 2.70 → 2.59 on the dummy and from 1.51/1.34 → 1.47/1.13 against Gravetusk/Omen.
- Thousand cuts only echoes straight out of the flurry. Moonlit iai lasts 8 s. The focus hold turns with the stick.

## 3. New combos
Timing is wind / total in ms. Dmg is per hit, in units of AR. Poise is for the whole move. Each move has its own new animation tag (art/player_v14_blade.py), with the old tag listed after it as a fallback.

| Weapon | Input | Rank | Move (tag) | Timing | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|---|
| LS | J K | I | Lifting cleave (`ls_jk`) | 260 / 600 | 1.4 | 28 | 18 | A branch off step 1 that teaches "K branches at every step". It is a tall rising box that pops light foes up (launch), good vs fliers. J after it gives the poke, so J K J J is a full route. |
| LS | L → K | I | Wheeling cut (`ls_rollk`) | 240 / 600 | 1.5 | 32 | 18 | A dodge follow-up. You roll **through** a foe and K turns you onto the nearest one (else the held direction) with a wide flat cut. Planted 14 px. |
| LS | air J J | I | Falling crescent (`ls_air2`) | 150 / 360 | 1.0 | 14 | 12 | A real air string: the 2nd air cut is a big overhead-to-boots crescent instead of a repeat (the box reaches below the feet). Uses the normal 2-attack air limit. |
| LS | J J (beat) J | II | Wheel slash (`ls_wheel`) | 200 / 620 | 2 × 0.8 | 30 | 18 | Wait a beat (a press 110-300 ms after the rising cut ends): a full turn that cuts behind you, then in front. A crowd answer. J after it gives the critical slash (ember-eligible). |
| KT | J (sheathed) | I | Draw cut (`kt_draw`) | 120 / 400 | 1.1 | 12 | 10 | Everything from the sheathe is a draw: a low flat draw from the scabbard that flows into kt_2 / flurry. |
| KT | J J K | I | Crescent sheathe (`kt_jjk`) | 240 / 660 | 1.3 | 26 | 16 | A pivot, a wide crescent, a chiburi flick, and the blade slides home: you **end sheathed**, so K next is an Iai. It turns the light chain into Iai setup. |
| KT | Iai → J | I | Swallow return (`kt_tsubame`) | 100 / 480 | 1.1 | 14 | 10 | The wrist turns over and the edge snaps back up the Iai's line. I after it sheathes at once (flurry-sheathe speed), so draw → return → sheathe → draw is the duelist's rhythm. |
| KT | focus draw → K | II | Turning draw (`kt_turn`) | 160 / 620 | 1.6 | 35 | 16 | The focus draw dashes you **through** the foe. K whirls round onto the nearest foe (else back the way you came), cuts and sheathes. |

All 8 start from real inputs (routes.js). The rank gates hold (the beat gives the poke at rank I; focus → K gives the rushing draw at rank I). Every new move travels ≤ 14 px (turning draw: 17 px back toward the foe). Each new tag has active frames (the wheel slash has `hits` [2, 4] and a both-sides box), and the in-game resolve shows `real=true` for all 8.

`combos` (the full move list) and the II-rank unlocks (`ls_wheel`, `kt_turn`) were added to each type.

## 4. Bench (dmg/s in light-AR units, dummy, infinite stamina; bench.js / wm bench.js)
| Route | Before | After |
|---|---|---|
| LS J J J J | 2.74 | 2.74 |
| LS J J K | 2.51 | 2.62 (the lead's queue fix) |
| LS J J J K | 2.55 | 2.68 |
| LS J K J J (new) | – | 2.67 |
| LS J J (beat) J J (new, II) | – | 2.62 |
| LS J J J hold K pommel (IV) | (input failed) | 2.34 |
| LS ember J J J J (V) | – | 2.87 |
| KT J J J | 2.17 | 2.17 |
| KT K → K loop | 2.70 | **2.59** |
| KT J J K K (new) | – | 2.45 |
| KT Iai J I loop (new) | – | 2.47 |
| KT J J J I K (IV thousand cuts) | – | 2.54 |

Real-boss bot (40 s, own AI, rolls on wind-ups, real hits). The bot is crude, so treat this as relative only:

| Style | Gravetusk (dps, dmg taken/min) | Omen |
|---|---|---|
| LS J J J J | 1.15, 1086 | 0.81, 1808 |
| LS J K J J (new) | 1.20, 975 | 0.93, 1463 |
| KT K → K (before) | 1.51, 531 | 1.34, 1011 |
| KT K → K (after) | 1.47, 531 | 1.13, 1041 |
| KT J J K K (new) | 1.26, 1064 | 1.10, 1302 |
| Spear J J J / GS J J J / SnS / Dual (others' builds) | 1.20 / 1.13 / 0.96 / 1.04 | 0.94 / 0.91 / 0.69 / 0.79 |

The katana is no longer the best weapon on the dummy (Dual Demon is 3.85, the Longsword 2.74). Against bosses its Iai loop still leads the bot table by ~15-20%. That is the fastest-heavy identity: hits land inside openings, at the cost of 42 stamina per loop.

## v14c: more J/K mixes (round 3)
Six more combos, all at rank I, each with its own new animation tag. Every existing route still works: routes.js passes
45/45, including checks that J J K, J J J I, hold K and drawn K are unchanged.

| Weapon | Input | Move (tag) | Timing | Dmg | Poise | Stam | Identity / what it's for |
|---|---|---|---|---|---|---|---|
| LS | K J (also charged overhead → J) | Return slash (`ls_kj`) | 150 / 420 | 1.0 | 14 | 12 | The heavy that branches into lights. The blade bites the floor, the wrists turn and it snaps back up; then J J gives the poke and the crit. Teaches heavy → light. |
| LS | K K | Crosswise strike (`ls_kk`, Zwerchhau) | 300 / 660 | 1.5 | 38 | 22 | The hilt rises over the head and the blade flips flat across the brow. A high box (−52..−12) for tall foes and low fliers. |
| LS | J K K | Splitting cleave (`ls_jkk`) | 260 / 700 | 1.7 | 50 | 22 | From the lifting cleave's high finish, straight down into the floor (slam dust and shake). Launch, then smash. |
| KT | J K | Kesa cut (`kt_kesa`) | 260 / 640 | 1.4 | 32 | 18 | A half step back into a high guard, then a shoulder-to-hip cleave on a long step. J after it returns to kt_2 and the flurry. (J K used to fall through to the rushing draw; a neutral K still rushes.) |
| KT | J J J K | Helm splitter (`kt_kabuto`) | 320 / 760 | 1.6 | 50 | 20 | The flurry rises into jodan, holds a breath, then one vertical cut. It gives the low-stagger flurry a stagger ending, as an alternative to J J J I. |
| KT | Iai → J → K | Thrust home (`kt_tsuki`) | 160 / 640 | 1.1 | 22 | 14 | A lunging straight thrust (reach 56), a chiburi flick, sheathed: K next is an Iai. That makes draw, return, thrust, draw. |

Engine: none. Fix: the heavy only goes into the charge stance if K has stayed **held since the press**, so a fast second K
(at 150-230 ms) becomes the K K crosswise strike instead of a charge. The routes check K K at a 170 ms gap.

Bench (dmg/s on the dummy, infinite stamina): LS K J J J 2.51, K K loop 2.26, J K K 2.24. KT J K J J 2.07, J J J K 2.06,
Iai J K loop 2.56. All are below the main loops (LS J J J J 2.74, KT K → K 2.62); they are alternatives for stagger, reach
and rhythm, not better damage. Real-boss bot: KT J J J K 1.16 / 0.78 (Gravetusk / Omen), LS K J J J 1.14 / 0.77.
