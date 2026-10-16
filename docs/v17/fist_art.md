# v17 A2: Martial Arts weapon art: Litany of Fists (`litany`)

The Martial Arts used to borrow Bloodstep. They now have their own art, Litany of Fists. Brief: `docs/v17/ARTS_BRIEF.md` A2.

## Design as built

The art follows the current style (`P.ftStyle`, `78_mech_fist.js`) and never changes it. It is "a prayer said with the hands" (the penitents fought bare of blade). A soft chime rises on each Swift blow, and the Iron palm rings like a cracked bell.

**Swift (tap):** the guard opens and the palms press together at the chest, head bowed (the wind-up, 0.2 s). Then comes a stepping flurry of **6 blows**, one every 75 ms. They alternate far palm high, near knuckle mid, far knuckle low and near palm high, each 0.32 light with 6 poise. The fighter steps in at 70 px/s but stops 12 px short of the nearest body ahead, so the flurry never walks through the foe. Each blow is one rising note of a G pentatonic line. A short clinch (80 ms) pulls the foe down onto a **rising knee** (0.9 heavy, 30 poise). The knee hops you up and **launches small foes** (not bosses, elites or fliers): vy −200 and the stance breaks. You land guard-up and go back to idle. Total time is about 1.4 s.

**Swift (hold):** **9 blows**, a longer step (100 px/s), and the knee at 1.15 with 40 poise.

**Iron (tap):** sink into the stance. The near palm draws back to the hip and the far hand rises upright before the face. The wind-up is 0.32 s, and the knuckles heat while you hold. Then one long planted step and the **bell-breaker palm** (1.4 heavy, 60 poise). The **shock** rolls forward along the floor: an ember dome over a cracked seam. It travels at 300 px/s for 72 px and is 24 px tall. It deals 0.9 heavy with 50 poise and hits each foe once. The palm and the shock **shove small foes** (200 px/s; the palm at 60% of that). The shock stops at walls and ledges. In the air the palm still lands, but the shock only rolls if a floor is within 40 px. The Iron art is **armoured** under the Iron rule: a blow under 20% of max HP doesn't flinch it, and the Iron armour flash shows. Total time is about 1.0 s.

**Iron (hold):** the palm hits 1.8 with 90 poise. The shock travels 116 px, is 34 px tall, and deals 1.4 with 80 poise and a 260 px/s shove. **Both the palm and the shock break guards:**
- A shield warden or barnacle with its guard up (`cfg.guard`, idle/walk/guard, facing you) has its stance broken.
- The mirror's raised shield (`t.guarding`) drops and the mirror staggers.
- The drowned shield boss reads `charged` on the hit, so +62 to its guard meter. The palm and the shock together crack it.

**Focus** (the perfect-dodge buff) applies as it does to every martial-arts blow: ×1.1 damage (`ftPdMul`) and +6 px reach on every box (`ftPdReach`). The flurry's hit marks turn whiter under Focus.

**Flow:** the art landing adds **1 Flow** once per use, like a Shift strike. It doesn't spend Flow and doesn't ignite.

**Cost:** **14 FP, cooldown 5.5 s** (`LT_TUNE` in `81_art_fist.js`). Swift has no armour and no i-frames. It is the "commit inside their guard" art; Iron is the armoured, stance-breaking one.

**Animations** (`art/player_v17_fist.py`, reusing the v15 fist rig, so both fists and the IK kicking leg are real):
- `art_litany` (Swift), 10 frames plus the settle frame:
  - 0 prayer, 1 prayer held (the charge-hold frame, with a pale glint)
  - 2–5 the four strike frames, looped once per blow
  - 6 clinch, 7 rising knee with an upward arc, 8 float, 9 landed
- `art_litany_iron`, 6 frames plus settle:
  - 0 rooted, near palm to the hip, far hand upright
  - 1 coil (the charge-hold frame, knuckle flare)
  - 2 the palm driven out, with the shock rings opening off it and the floor kicking up
  - 3 held through the wave, 4 drawing back, 5 the iron guard

The release frame is 2 (meta `active[0]`) and the charge holds frame 1. `81_art_fist.js` picks the tag from the style in `ART_IMPL.litany.start()` and drives the frames from its phases. If the sheet lacks the tags, it falls back to `ft_wind` / `ft_palm`.

**Effects** (procedural, in `81_art_fist.js`):
- Each blow leaves a small pale four-point mark with a streak back along the arm (a brighter one for the knee).
- The Iron shock is drawn per pixel: a hot 2 px rim on a floor-anchored quarter-ellipse, a dithered ember haze behind it, a faint echo rim and a hairline ember seam along the floor.
- One light per effect: the wave's front, k 0.5. The knee and the palm use a single `feelFlash`, k 0.8.
- There are no new sprites and no screen flash.

**Sound** uses `tone()` / `noise()`:
- Swift: a soft two-note chime on the wind-up, then a snap of noise plus one rising pentatonic note per blow. The knee is a heavy swing, a low thud and the top note.
- Iron: a low sawtooth drone on the wind-up. The palm is a sine thud, a 196 Hz triangle bell, inharmonic 523/731 Hz partials and a dry low noise crack, plus a brighter crack on the hold.

**Icon:** `a_litany` in `ui_icons17_fist` (`art/gen_ui17_fist.py`, registered in `81_art_fist.js` via `ICON_SHEETS`). It shows an upright wrapped hand, palm out, with an iron band over the knuckles, pale Swift blow-lines on the left and an ember shock on the right. The Esc, blacksmith, Training and HUD screens read the name, icon and desc from `ARTS.litany`.

**Move List:** no type's Move List names its weapon art (`80_movehelp.js` lists only the moveset's `combos`), so the art isn't added there.

**Saves:** `WEAPONS.penitent_knuckles.art` and `WTYPE_INFO.fist.art` are `'litany'` (`77_types15.js`). `60_wbal.js`'s `wbLockArt` forces `SAVE.art` to the weapon's art every frame, so a save holding `bloodstep` with the Knuckles in hand loads as `litany` (tested).

## Numbers

| | blows | damage (light hits) | poise | time |
|---|---|---|---|---|
| Swift tap | 6 × 0.32 + knee 0.9 | 2.82 | 66 | 1.37 s |
| Swift hold | 9 × 0.32 + knee 1.15 | 4.03 | 94 | 2.32 s (0.83 s of it held) |
| Iron tap | palm 1.4 + shock 0.9 | 2.30 | 110 | 1.00 s |
| Iron hold | palm 1.8 + shock 1.4 | 3.20 | 170 | 1.65 s |
| Focus | ×1.1 (Swift tap 3.10, Iron tap 2.53) | | | |

Hits per FP (tap): Swift 0.201, Iron 0.164. Hits per cooldown-second: 0.51 and 0.42. This is in the band of the other arts (`docs/weapon_balance.md`: 0.13–0.22 per FP, 0.31–0.64 per cd-second). Iron trades damage for stance damage and the shove.

## Balance

Measured with `tools/shots/v17/fist/bench.js`: the v15 fist boss bench (held Gravetusk, a 1.3 s opening, a roll every 2 s, real stamina, 30 s). With art, the art is used whenever it is ready, on real FP and no flasks.

| route | DPS (light/s) | art's share |
|---|---|---|
| Swift J J J J | 0.82 | |
| Swift J J J J + art | 1.57 | 30% |
| Iron J J J (the type's best boss route) | 1.51 | |
| Iron J J J + art | 1.69 | 23% |
| Shift dance J (J I) | 1.22 | |
| Shift dance + art | 1.78 | 26% |
| Swift art only (FP refilled) | 0.47 | |
| Iron art only (FP refilled) | 0.38 | |

The art alone is far below the type's best route, and the +art routes gain 12–46%. The other weapons' "with art" gain is +25–60%. Iron sits under that band because its art trades damage for stance damage and the shove. The Swift chain's +91% is mostly the chain itself: it is the weakest boss route at 0.82, and the art opens each window with a full flurry. On the dummy the art's own rate is about 2.1/s (Swift tap) and 2.3/s (Iron tap). The best combo, the Shift dance, runs at 2.79/s.

## Tests

All tests are in `tools/shots/v17/fist/`, run with `SHOT_HTML=$PWD/web/dist/v17_fist.html sh tools/shots/wm/run.sh <test> <outdir>`.

- `art.js` (output `art_out.txt`) passes. It covers:
  - the art key with the type equipped starts the art and costs 14 FP
  - tap and hold in both styles: every use ends in idle, the hold beats the tap, and the style is unchanged
  - Flow +1, Focus ×1.1
  - the knee launches a Hollow soldier, the Iron palm and shock shove it 50 px, and the shock reaches a foe 70 px away
  - the hold breaks a raised shield-warden guard and the tap doesn't
  - Iron armour: a 10% blow doesn't flinch, a 30% blow does, and Swift flinches
  - an old save's `bloodstep` is corrected to `litany`
  - no FP and on-cooldown both deny
  - no page errors
- `bench.js` (output `bench_out.txt`): the tables above.
- `snaps.js` plus `montage.py`: in-game frames (`snaps/`, `montage.png`).
- Regression: `tools/shots/wm/mech.js` 63/63 (`mech_out.txt`) and `tools/shots/v15/fist/routes.js` 77/0 (`routes_out.txt`).

## Open decisions for the owner

1. **Flow from the art:** +1 on landing. It could be 0 (keep the art outside the Flow economy) or full (let the art feed an Ember shift at once).
2. **Swift has no defence:** no armour and no i-frames during the 1.3 s flurry. A short slip at the start (about 0.1 s of i-frames, like the slip step) would make it a counter. Left out so Swift stays the commit-and-pray half.
3. **Iron hold breaks guards fully:** a raised small-foe guard breaks its stance at once. The drowned shield boss loses its guard to palm plus shock (124 of 100).
4. **The hold costs the same FP as the tap.** It is the other arts' rule; the hold's extra time is the price.
