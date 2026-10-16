# v17 A3: Warbell, Funeral Peal (`funeral_peal`)

The Warbell's own weapon art, in place of the borrowed War Cry. Brief: docs/v17/ARTS_BRIEF.md.

## As built

Swing the bell back low past the heel, haul it over the back shoulder, and drive it mouth-first into the floor. A ring of
sound rolls away along the floor **both ways** from the lip (14 px ahead of the feet):

- **Blunt.** Each foe the rings pass through is struck once (one hit per foe across both rings), `kind: 'heavy'`, `big`, with
  the bell's x1.3 stance damage (via `mvPoiseFor` → the bell's `poiseMod`). Fury (+8%) applies to it.
- **Swallows missiles.** Enemy projectiles inside the travelling ring (its front 10 px, floor to ring height) are destroyed,
  each with a high Ash chime.
- **Writes notes, never plays them.** Every foe the **forward** ring strikes rings **Ember**, every foe the **backward** ring
  strikes rings **Ash**, one note per foe, at most **2** (tap) / **3** (hold), through 78_mech_bell's own `belAddNote` (same
  sound, glyph and staff pop). A whiff rings nothing, as with every bell blow. The peal does not empty the staff and plays no
  toll: it sets up the next Perform (e.g. a foe ahead and one behind = Ember Ash; two ahead = Ember Ember → Fury), it does not
  replace it.
- **Hold** (art key ≥ 0.6 s, the bell hung over the back shoulder): the ring rolls further, hits harder, stuns small foes
  (`GEAR2.stun`, elites half) and rattles boss stance (+30).
- The rings follow the floor: they stop at a wall, at a gap, or at their range. Started in the air, the bell holds its last
  wind-up frame and falls faster until it lands, then strikes (gives up after 1.5 s airborne).
- Hyper-armour while the art plays (as Tolling Blow / Magma Quake).

| | tap | hold |
|---|---|---|
| damage per foe | 2.8 × light AR | 3.4 × light AR |
| stance (before the bell's x1.3) | 70 | 100 (+30 boss stance) |
| ring range each way | 88 px | 140 px |
| ring speed / height | 300 px/s, 32 px | 320 px/s, 38 px |
| notes written | ≤ 2 | ≤ 3 |
| small-foe stun | – | 1.8 s |
| FP / cooldown | 14 / 6.5 s | same |

All in `FPL` / `FPL_TUNE` at the top of web/src/81_art_bell.js.

**Sound:** a half-muffled funeral toll: 78_mech_bell's `belToll` pitched down (0.84, held 0.75), a low-passed thud of iron
on stone, and two quieter bells answering 0.42 s and 0.85 s later (the peal). Each struck foe adds its note's bell partials.
**Effects** (procedural, glow layer, in 81_art_bell.js): at the lip a flat shock ring (`belRing`), dust and one light
(k 0.8); each travelling ring is a standing quarter-arc of bone-white dots with a core in its note's colour (Ember ahead,
Ash behind), two fainter echoes lagging behind it, a seam of light left in the floor where it passed, dust kicked off the
front and one light per ring (k 0.5). No screen flash.

**Animation** `art_funeral_peal` (art/player_v17_bell.py, the Dirgebell overlay, two-handed, 1140 ms + settle frame; the engine
plays the recovery after the impact at 1.25x, so a tap is 1.15 s from the key to idle; the charge hold is reached after 290 ms,
so a charged peal needs the key held ~0.9 s):
0 settle low in front · 1 dragged back low past the heel · 2 heave, back turned, bell behind at shoulder height · **3 hauled
over the back shoulder (the charge hold)** · 4 the drive, mouth first (smear) · **5 IMPACT, kneeling into it (meta
active = release)** · 6 pressed over the haft while the ring rolls away · 7 the weight comes off · 8-9 rise, settle.
In the sheet since the 19:02 full build (assets/player*, art_funeral_peal = frames 3246-3256, meta active [5, 5]). Without the
tag the art falls back to `wb_toll` (release frame 4, hold frame 1): `ART_IMPL.funeral_peal` switches `release` / `chargeAt` on
`P.artOwn`.

**Icon** `a_funeral_peal` in its own sheet `ui_icons17_bell` (art/gen_ui17_bell.py → assets/ui_icons17_bell.png/.json,
pushed onto ICON_SHEETS by 81_art_bell.js): the Dirgebell mouth-down on a floor line, two standing rings either side
(Ember-cored ahead, Ash behind). Shown in Esc › Equipment (name, icon, FP 14, cooldown 6.5 s, desc) and the weapon cards.

## Files

- new: web/src/81_art_bell.js, art/player_v17_bell.py, art/gen_ui17_bell.py, assets/ui_icons17_bell.{png,json},
  tools/shots/v17/bell/* (art.js, bench.js, snaps.js, menu.js, crop.py, outputs), docs/v17/bell_art.md
- shared (surgical): web/src/77_types15.js (dirge_bell and WTYPE_INFO.bell `art: 'funeral_peal'`, header table);
  art/gen_player.py (the v17 module block: loads player_v17_{bow,fist,bell}.py if present, `+ V17_MOVES` in ANIMS)

## Saves

Nothing new is stored. `77_types15.js` names the art; 60_wbal's `wbLockArt` forces `SAVE.art` to the weapon's art every frame
and on load / rest / room entry, so a save holding the borrowed `warcry` with the Dirgebell is corrected (test). War Cry
itself is untouched (other weapons still carry it). `ITEMS['art:funeral_peal']` is the Tempering Cache like every other
legacy "Ash of" item.

## Tests (tools/shots/v17/bell/)

`SHOT_HTML=$PWD/web/dist/v17_bell.html sh tools/shots/wm/run.sh tools/shots/v17/bell/art.js tools/shots/v17/bell/out` -- all pass:
art locked to the Warbell, old War Cry save corrected, fp 14 / cd 6.5, icon found, no collision with `tolling_blow`; tap from
the art key costs 14 FP, one blunt 2.8 hit, Ember from a foe ahead, Ash from a foe behind, Ember Ash with one each side, a
whiff writes nothing and keeps the staff, 120 px out of tap reach, three foes → three hits / two notes; hold: 3 × 3.4 hits
including a foe at 120 px, three notes; stun tap 0 / hold 1.8 s on a real Hollow Soldier; an arrow swallowed; 5 FP denied;
peal Ember Ember → Perform plays Fury; started airborne it lands and strikes; ends in idle (1.15 s, the dedicated animation); no
page errors. Regression: tools/shots/wm/mech.js 63/63 OK, tools/shots/v15/bell/routes.js 50/50 OK.

## Balance (bench.js, v15 boss.js rules: Gravetusk held, swinging every 2 s, real stamina, 30 s)

| plan | dmg/s (light AR) | boss staggers |
|---|---|---|
| J J J + notes into a Perform (the bell's best boss play) | 1.43 | 2 |
| the art alone, whenever ready (FP refilled) | 0.47 | 0 |
| best play + the art whenever ready (FP refilled) | 1.63 (+14%), 4 Performs instead of 2 | 2 |

One use on a still target: tap 2.80 light hits (0.200 per FP, 0.431 per cooldown-second), held 3.40 (0.243 / 0.523) -- inside
the art table's band (weapon_balance.md: 0.13-0.26 per FP; Tolling Blow 3.03 per use at 24 FP, Pale Pyre 0.216 per FP).
First pass was 2.4 / 3.0 at cd 7: with the dedicated (slower) animation it added nothing in the boss loop (1.43 → 1.40), so
it was raised once. It cannot beat the bell's
own combos on boss time-to-kill; its value is the notes (twice the Performs), stance, crowd control both sides and missiles.

## Open decisions for the owner

- **Note rule.** Built: one note per foe, Ember ahead / Ash behind, cap 2 (3 held). Alternatives considered: a fixed chord
  (e.g. always Ash Ember = Iron hymn), or Gold for the peal itself. Against a lone boss the tap writes one Ember.
- **Tuning.** +14% in the boss loop is at the low end of what other arts add (+25-60% in bench_real); FP 12 or cd 5.5 would
  raise it. Left conservative because the notes also double the Performs and the ring is an AoE both ways.
- **Move List.** No type lists its art in its Move List (80_movehelp builds rows from the type's `combos`); not added.
- **Icon sheet.** Its own `ui_icons17_bell` to avoid clashing with the bow/fist agents; it can be merged into one
  `ui_icons17` later (the game finds icons by name across ICON_SHEETS).
- Echo (Gold Gold) does not re-ring the peal's hits (Echo is for move hits); could be added.

## Snapshots

tools/shots/v17/bell/snap/montage_tap.png (tap: wind-up, drive, impact, the rings rolling both ways, a foe each side),
snap/montage_hold.png (charged: the crown hold, the longer ring, stunned foes, an arrow swallowed), snap/*.png (single frames),
snap_menu/equip1.png (Esc › Equipment art row), prev/art_v5z.png (the animation strip, 6x), art/previews/ui17_bell.png (icon).
