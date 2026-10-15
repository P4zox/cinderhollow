# v14 weapon pass: Reach group (Staff, Whip)

Files: `web/src/76_mech_reach.js`, `art/player_v14_reach.py` (8 new tags), `tools/shots/v14/reach/`
(`routes.js` 39 route checks, `bench.js` table and real-boss bench, `vis.js` + `montage.py` in-game frames,
`probe.js`/`probe2.js` exploratory probes). Build: `web/dist/v14_reach.html`.

Everything below was played through real inputs in the harness (press, hold and timing sequences), against the WM
dummy and against Gravetusk (C5) with its own AI.

## Critique: Staff

| # | Finding | Kind | Fix |
|---|---|---|---|
| 1 | **J pressed during the vault's plant was lost.** The vault only peeked the buffer from 0.22 s, so a press in the first ~40 ms had expired: "I, J" typed quickly gave a bare vault. | input | J and K are latched at any point of the vault and played as soon as it can be left (0.22 s, in the air). |
| 2 | **The documented vault cycle (vault, J, K, dive) didn't fit in the air.** The vault gives ~0.65 s of air after the plant; J (320) + K (460) landed mid-spin. The spin finisher (III) **whiffed from a vault every time** (it landed before its hit). | too hard | The staff's spinning air moves glide: the fall is capped (60 px/s for the spins, 50 for the vault kick, 90 for the cartwheel) while the staff turns. I → J → K now lands both hits; I → K → K lands the finisher. |
| 3 | **Dive-kick refund loop.** Every bounce refunded the air attack it used, so the dive kick never counted: an endless pogo on a head, momentum topped up for free. Other weapons' pogos count. | exploit | The refund works once per trip through the air (reset on landing). |
| 4 | **The spin cost 30% of the bar** (43 stamina at 142 max) for 1.6 dmg. It also got pricier as you levelled Endurance and had a denial toast. A tax, not a choice. | balance | Flat 24 stamina (the Whirling Staff skill still cuts it by 55/80); no denial toast. Spin loop 2.49/s with 60 poise on both sides: a real alternative to J J J J. |
| 5 | **Gale (V) whiffed most of its hits.** The tornado ran off at 120 px/s, so a foe standing in front took 1 hit (0 at 50 px), and it ate all 3 momentum stacks. In the air it spawned at your height and floated over grounded foes. | too weak / bug | Slower (50 px/s), hits at 0.12/0.38/0.64 s: a foe at 30-50 px takes all 3 (3 × 0.6 = 1.8, still modest: only what stands in it). Ground only (air K is always the aerial spin). |
| 6 | **The double vault (IV) was unreachable in practice.** I pressed during an air move wasn't latched; the press played on landing as a ground vault. | input | I cancels a staff air move once its hit is out, if a head is in range. |
| 7 | **Ground game weak?** J J J J was 2.40/s (LS 2.81). On the real boss, the crude bot's staff ground route did ~60% of the Longsword's. The staff is meant to be weaker on the ground, but not that much. | balance | st_1/st_2 0.85 → 0.9, st_4 1.4 → 1.5 (poise 40). J J J J 2.40 → about 2.53/s (90% of LS). The new J J K launcher gives a way from the ground into the air game. |
| 8 | Vault itself: 41 px up, 33 px forward standing (84 holding forward), 0.8 s, invulnerable 0.2 s. Readable and useful. | ok | none |

## Critique: Whip

| # | Finding | Kind | Fix |
|---|---|---|---|
| 1 | **Thousand lashes misfired on mashing.** The check was "J held at 250-300 ms into the lash", so any mash tap that happened to be down in that 50 ms window started the flurry (reproduced: mashing at rank V gave wh_1 → wh_thousand). A deliberate hold could also slip past the window on a slow frame. | bug | J must be held **continuously from the lash's start** for 240 ms, checked from 240 ms to the end of the lash. 7 mash rhythms tested: never triggers; 280 ms and 400 ms holds always do. |
| 2 | The **overhead charge** used the same 50 ms "held at 120-170 ms" check (same mash risk on K K). | bug | Continuous hold from the start, from 180 ms to just before the hit. 5 K-mash rhythms: never triggers. |
| 3 | **The tip was invisible.** The drawn chain reaches ~36 px (the 64 px frame), but the lash hits at 80 px and the tip zone is 60-80 px: the tip spark appeared in empty air, twice as far as the whip you could see. | readability | The engine draws the rest of the lash (`whLashFx`): grey links unfurl out to the real reach while the hit is out, the tip zone hot, a glint at the tip (both sides on spins, along the floor for the trip lash). The tip zone is the last 30% (was 25%): a 24 px band, not 20. |
| 4 | **Thunderclap too strong**: 3.2 from anywhere. The tipped K loop with claps was 3.07/s (+15% over its table, the top sustained number in the game) and needed no spacing for the clap. | balance | 2.5, ×1.3 at the tip = 3.25 (the 3.2 fantasy needs spacing). The crack meter fills +20 per tipped heavy (was 25: 5 Ks per clap, not 4). The loop is 3.02/s at perfect spacing and 2.10/s close. |
| 5 | **Grapple = a permanent lock.** Each pull called breakStance (a 1.8 s stagger) on a 2 s cooldown: a small foe was out of the fight 90% of the time for 14 stamina. | exploit | The pulled foe staggers 0.6 s. The slam (III) and the new reel kick (II) are the follow-ups. |
| 6 | **Snap counter for free.** With the grapple on cooldown, I armed the 150 ms snap at no cost, so mashing I kept it armed 100% of the time. | exploit | Arming it without a grapple costs 6 stamina and it can't be re-armed for 0.5 s (mash = 33% coverage at most). |
| 7 | Grapple follow-ups (slam) needed the K to land after the 300 ms grapple state; a press during it expired. | input | J / K pressed in the grapple's tail (from 0.16 s) leave it at once. A J pressed while zipping to a large foe is kept for arrival. |
| 8 | Up close the whip had nothing: 0.8 untipped lashes. | design | New L → K coil spin and grapple → J reel kick both put small foes back at the tip. |
| 9 | J J K had no branch (it played a plain heavy). | design | J J K = trip lash (unless the clap is ready: then the clap). |

## New combos

Timing is wind-up / total (ms). Dmg in light AR (tip ×1.3 where marked).

| Weapon | Input | Rank | Move | Time | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|---|
| Staff | J J K | I | **Pole launcher** (`st_rise`) | 170 / 470 | 1.0 | 28 | 12 | Upswing that launches small foes and carries you ~45 px up: the ground-to-air bridge (air J/K follow). Not an air attack itself. |
| Staff | I → J | I | **Vault kick** (`st_vkick`) | 110 / 360 | 1.1 | 24 | 10 | The vault's own attack: a flying two-footed kick off the pole. Counts as an air attack. |
| Staff | air J J | I | **Cartwheel** (`st_air2`) | 120 / 400 | 0.5 + 0.6 | 18 | 11 | Turn over the staff: butt end behind, head in front. The air string that covers both sides. |
| Staff | air ↓J → K | II | **Pole drop** (`st_pdrop`) | 150* / 520 | 1.4 | 40 | 16 | Off the dive kick's bounce: hang, then ride the staff point down; a shock both sides on landing, or a bounce off a head. Uses the smash limit (like every plunge). *The hit lands on impact. |
| Whip | J J K | I | **Trip lash** (`wh_trip`) | 200 / 560 | 1.0 (tip 1.3) | 22 | 12 | A low crack along the floor. Tipped, it trips a small foe. At 100 crack, J J K is the thunderclap instead. |
| Whip | L → K | I | **Coil spin** (`wh_coil`) | 140 / 520 | 0.6 + 0.7 | 26 | 14 | The close-range answer: the chain whirls round you (both sides, 46 px) and the 2nd hit flings small foes out to 64 px, onto the tip. |
| Whip | air J J | I | **Skyfall crack** (`wh_air2`) | 150 / 400 | 1.0 (tip 1.3) | 16 | 10 | From the circular lash, a long crack down to the floor ahead: hit grounded foes from the air at range. |
| Whip | grapple → J | II | **Reel kick** (`wh_reelkick`) | 150 / 460 | 1.2 | 30 | 12 | Pull a small foe in, then kick it back out to the tip. On a large foe (zip), it is the arrival strike. |

None of the new routes beats the main loops: staff J J K is 2.35/s before its air follow-up; whip J J K tipped is 2.49/s
(J J J tipped 2.29, tipped K 2.73); the coil spin loop is 1.50/s (it is a reset, not damage). Lunges are small (vault kick
22 px drive, launcher 35 px/s drift).

The full move list of each weapon is in the type's `combos` (17 rows each); the rank II pole drop and reel kick were added
to `unlocks`.

## Art (`art/player_v14_reach.py`)

8 tags, each with anticipation, smear, impact, follow-through and settle, timed to its row with `tm()`:
`st_rise` (planted low behind, a wind-palette upswing arc, rising wind lines), `st_vkick` (tucked over the pole, legs drawn
back, a two-footed kick with the cape streaming), `st_air2` (a mirrored back-strike then a wind-tinted front chop),
`st_pdrop` (hang, flip the point down, dive lines, a planted crouch with dust on both sides), `wh_trip` (sink low, the
chain skims the floor and snaps at the ankle), `wh_coil` (a whirl ring at the waist, front, behind, then flung flat),
`wh_reelkick` (turn the back, a spinning heel kick with the chain trailing), `wh_air2` (arm high, the lash cracked down
to the floor). Every move row lists its new tag first and an old one as fallback.

## Bench (before → after)

Table bench (`tools/shots/v14/reach/bench.js`; dummy that follows, infinite stamina, dmg/s in light AR):

| Route | Before | After |
|---|---|---|
| Staff J J J J | 2.40 | 2.52 |
| Staff K spin loop | 2.49 (at 30% of the bar) | 2.49 (24 stamina) |
| Whip J J J untipped / tipped | 1.93 / 2.29 | 1.93 / 2.29 |
| Whip tipped K loop | 2.73 | 2.73 |
| Whip tipped K + thunderclaps | 3.07 | 3.02 (needs spacing now) |
| Whip close K + thunderclaps | 2.10 (claps 3.2 anyway) | 2.10 |
| Whip L K coil loop | n/a | 1.50 |

Real boss (Gravetusk with its AI, 40 s, a scripted player that rolls through its swings; noisy, compare within a row):

| Plan | Before | After |
|---|---|---|
| Staff vault cycle (I, J, K, ↓J) | 0.45 dmg/s, 6 hits taken | 0.63 dmg/s, 2 hits taken |
| Staff ground J J J J | 0.58 | 0.44-0.58 (noise) |
| Whip at the tip (J J K) | 1.08, 12 hits taken | 1.12, 13 hits taken |
| Whip close (J J J) | 0.53 | 0.53 |
| Reference: Longsword / Spear | | 0.85 / 0.71 |

## Shared tests this intentionally changes

- `tools/shots/wm/mech.js`: "WH: tip hits fill the crack meter (+10 light, +25 heavy)" (now +20); "WEAPON_UNLOCKS: 9 types
  × 4 unlocks" (the staff and whip now list 5).
- `tools/shots/wm/routes.js`: "staff K → st_heavy" (stam 24 vs 30% max); "whip crack K → wh_thunder" (2.5 close vs 3.2).
  Also failing: "staff J w6 J w6 J w6 J → st_4" (and the same for SnS's sh_4). That one comes from the engine's 2-deep
  queue (c3a3c72): four presses inside ~360 ms drop the fourth. Not a staff change.

## For the lead

- The whip at perfect tip spacing is the top sustained damage of the group (tipped K 2.73, with claps 3.02; the real-boss
  bot puts it above the Longsword). It pays for that with more hits taken at that range. I left the heavy alone: say if
  you want it at 1.3 (2.49/s).
- Air ↓K is the Cinder Slam technique for every weapon, so the pole drop hangs off the dive kick (↓J → K) instead.

## v14c: J/K mixes

Three new combos per weapon, each with its own animation (`art/player_v14_reach.py`, v14c block). Staff mixes play into
the vault, the air and momentum; whip mixes play into spacing, the tip and control. Every existing route still works
(`tools/shots/v14/reach/routes.js`: 54/54, 15 new checks).

| Weapon | Input | Rank | Move | Time | Dmg | Poise | Stam | What it's for |
|---|---|---|---|---|---|---|---|---|
| Staff | J K | I | **Back vault** (`st_bvault`) | 150 / 500 | 0.8 | 22 | 12 | Plant the staff ahead and flip back over it, feet kicking up through the foe. Ends ~44 px back and 43 px up, in the air (air J/K follow). The hit is airborne: +1 momentum from the ground. A disengage. |
| Staff | K → J | I | **Spin vault** (`st_svault`) | 230 / 560 | 1.1 | 34 | 13 | The spin's swing carries you up and over (a low ~35 px hop forward); the staff chops down from above. Airborne hit: +1 momentum. Lands before it ends (no free aerial spin after it). |
| Staff | air K → J | I | **Comet** (`st_comet`) | 160* / 500 | 1.1, +25% per momentum stack spent | 30 + 12 per stack | 14 | Out of the aerial spin, dive staff-first at 40° (64 px forward at most) and drive it into the floor. **Spends the momentum**: 3 stacks = ×1.75, 66 poise. Bounces off a head. Smash limit. *Hits on impact. |
| Whip | J K | I | **Tip flick** (`wh_flick`) | 110 / 340 | 0.5 (tip only: 0.65) | 6 | 7 | A fast wrist-snap to the very end of the chain. Misses entirely off the tip; a tip hit feeds the crack meter +15. A precision builder. J K J continues into Lash II. At 100 crack, J K is the thunderclap. |
| Whip | K → J | I | **Wrench** (`wh_wrench`) | 130 / 460 | 0.7 (tip only: 0.91) | 40 | 10 | After the heavy crack, haul on the taut chain: a small foe at the tip is dragged in to 30 px and staggered 0.5 s; a boss takes the 40 poise. Control at range. |
| Whip | J J J K | II | **Cyclone** (`wh_cyclone`) | 200 / 640 | 0.8 + 0.8 (tip 1.04 each) | 30 | 16 | The whirl kept turning into two full-length cracks, ahead then behind, each with its own tip: the spacer caught between two foes. (Rank I: J J J then a late K is the heavy crack, as before.) |

Engine-side, `whTip` now gives a spin's back lash its own tip (the cyclone and the whirl lash); forward lashes are
unchanged. The crack fill per move can be set with a row's `crack` (the flick: 15).

### Bench (exact cycles: route, land, dummy back in front; dmg/s in light AR, infinite stamina)

| Route | dmg/s | Compare |
|---|---|---|
| Staff J K (back vault) | 1.79 | a disengage, not damage |
| Staff J K + air J | 2.50 | = J J J J 2.50, but you end 40 px away in the air |
| Staff K → J (spin vault) | 2.31 | spin loop 2.49 |
| Whip J K (flick), tipped | 2.35 | J J J tipped 2.22; builds crack 1.5× faster per press |
| Whip K → J (wrench), tipped | 2.37 | tipped K loop 2.73 |
| Whip J J J K (cyclone), tipped | 2.52 | tipped K loop 2.73 |

First pass of the staff mixes was too strong (back-vault loop 2.93/s with a following dummy, spin-vault loop 3.17/s: its
hop left time for a free aerial spin with momentum). Trimmed: back vault 1.0 → 0.8, spin vault 1.2 → 1.1 and a lower
hop (vy 200 → 165) so it lands before the move ends.
