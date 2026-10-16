# v17 A1 — the Bow's own art: Ashen Volley (`ashen_volley`)

Replaces the borrowed Backstep Slash on the Ashstring Recurve (brief: docs/v17/ARTS_BRIEF.md A1).

## As built

**Tap O (12 FP, 5 s cooldown).**
1. *Coil* (90 ms): a low crouch on the back foot, an arrow on the string. Holding O stays here (the usual art charge,
   0.6 s to charge, 1.6 s max) with an ember gathering on the arrowhead.
2. *Kick* (release frame): a snap kick off the foe in front (0–26 px ahead, 6–30 px up): **0.5 × light AR**, poise 12 (light on purpose: a common foe is not flinched out of the spot the volley comes down on).
   I-frames start here and last **0.25 s** (`P.artI`).
3. *Back-flip*: 60 ms after the kick you push off (vx 150 back, vy −210, drag 400 px/s²); the body turns 90° (lying
   back), 180° (inverted), 270° (belly-down, head to the foe).
4. *The volley at the top* (0.2 s after the push-off, ~34 px up, ~25 px back): full draw, then **three burning arrows**
   fanned 0.12 rad apart, aimed at the nearest foe below-ahead within reach (its middle), else at the floor where you
   stood. **0.6 × light AR each** (1.8 total), poise 12 each. They are real bow arrows (78_mech_bow.js `bwArrow`, level-2
   amber glow + a flame on each head): walls and wards stop them and they **burn out at BW_RANGE (72 px of flight)**;
   `pb: true`, so a foe in the point-blank band takes no 0.9 cut. A 0.12 s hang at the top while they loose.
5. *Coming round*: the turn finishes (320° → upright) and you fall; a deep landing crouch ~29 px behind where you
   started, facing the same way, then the bow's rest. ~1.07 s in all (measured; i-frames 0.33 s measured incl. the kick's 0.05 s hitstop).

**The bow's chain:** the first arrow of a volley that lands on a foe raises the bow's charge level by one
(`P.bwLv` 1 → 2 → 3, `bwBank` + the level-up creak/flash). So the art flows into a level-2 tap-K power shot (1.4) or a
draw that starts a level higher. While the art plays the level does not gutter (`P.bwIdle` held at 0).

**Hold O (charged, same 12 FP):** **five arrows** (0.35 each, spread 0.1 rad) that **stick** — in the foe or in the
floor — smoulder (a swelling ember, one small light) and **burst 0.42 s later**: a 13 px star of fire, **0.25 × light AR**
each, poise 12, heavy. Five arrows into a boss = 5 bursts. A held volley that misses still bursts on the floor where the
arrows stuck (a trap for a chaser).

| | kick | arrows | bursts | total (× light AR) | per FP | per cooldown-s |
|---|---|---|---|---|---|---|
| tap | 0.5 | 3 × 0.6 | – | **2.3** | 0.19 | 0.46 |
| hold | 0.5 | 5 × 0.35 | 5 × 0.25 | **3.5** (+52%) | 0.29 | 0.70 |

In line with the other arts (weapon_balance.md: Backstep Slash 2.0 / 10 FP / 3.7 s = 0.20 per FP, 0.54 per cd-s;
Harvest Moon 0.20 / 0.58; charged versions are typically +35–60%).

**Boss time-to-kill** (tools/shots/v17/bow/bench_art.js, boss-sized dummy, 20 s, infinite stamina, light-AR / s):

| route | dmg/s |
|---|---|
| J J J J (main loop, foe at 30) | 2.58 |
| J J J → hold K (lv3) | 2.48 |
| L L → hold K (II) | 2.30 |
| art only, tapped on cooldown | 0.46 |
| art only, held | 0.69 |
| J J J J + art whenever ready (foe at 24) | 2.41 |
| art → K (the banked level) + J J J J | 2.05 |

The art never beats the bow's own routes on a boss; it is the answer to being chased / too close (i-frames, 29 px of
distance, a volley into the chaser, a level for the next shot), not a damage button.

## Files

- `web/src/81_art_bow.js` — registration (`registerGear` arts, fp/cd in `AV`), `ART_IMPL.ashen_volley` (the 16_gear3
  `impl()` contract written out: release frame 1, chargeAt 0, P.g2 phases 1 kick · 2 rising · 3 hang/volley · 4 falling ·
  5 landing), `ART_SYNC.ashen_volley`, the volley/stick/burst logic (`AVS`), procedural flames and bursts, sounds
  (tone/noise). Without the `art_ashen_volley` tag (an old sheet) the bow's tags stand in (bw_stab / bw_recoil / bw_air /
  bw_diveshot). Debug handle `window.__game.av`.
- `art/player_v17_bow.py` — the `art_ashen_volley` tag (11 frames incl. the settle frame; meta active = frame 1, the
  kick). Reuses player_v15_bow's bow, draw state and pull arm (`bseq`/`AIM`/`LOOSE`); the flip frames are posed upright
  and turned whole with `G.xform_frame` (90 / 180 / 270 are lossless; only the brief 320° frame is a free turn). The shot
  frames are posed with the bow raised at −48° so that turned 270° the arrow points 42° below the horizon, forward.
  `V17_NOROT=1` previews the upright poses. Hooked through the shared V17 loop in art/gen_player.py (already there).
- `art/gen_ui17_bow.py` → `assets/ui_icons17_bow.png/.json`, `art/ui_icons17_bow.aseprite` (one icon, `a_ashen_volley`:
  the flip's arc in ash and three burning arrows fanned out of its top). 81_art_bow.js pushes the sheet to ICON_SHEETS.
- `web/src/77_types15.js` — `ashstring.art` and `WTYPE_INFO.bow.art` = `ashen_volley` (and the header table).

Old saves: `SAVE.art = 'backstep_slash'` with the Ashstring is corrected to `ashen_volley` on the next frame by
60_wbal's `wbLockArt` (tested). `ITEMS['art:ashen_volley']` is the Tempering Cache, as 60_wbal does for every art.
Move List: the art is not listed per type there (the art screens read `ARTS[WTYPE_INFO.bow.art]`), so nothing to add.

## Tests (tools/shots/v17/bow/, gitignored)

- `art.js` — from real inputs: the lock / old save, fp/cd, the icon; tap (FP cost, kick 0.5 once, three arrows 1.8,
  level 1→2, 2→3, 3 stays 3, i-frames, rise, landing distance, ends idle on the floor, duration); the banked level feeds
  the next power shot; hold (charged, 12 FP, five arrows 1.75, five bursts 1.25, level up, idle); on nothing (no level,
  held arrows burst on the floor); a foe at 110 px is out of reach; the cooldown; facing left; a mid-air start.
- `bench_art.js` — the table above.
- `snaps.js` — in-game frames in the Training Grounds (tap and hold on a hollow soldier, a held volley on the floor) →
  `snap/s_*.png`, montage `snap_montage.png`. `prev/` holds the art previews (player_preview rows).
- Results: `art.txt` (all pass), `bench_art.txt`.
- Regression: `tools/shots/wm/mech.js` and `tools/shots/v15/bow/routes.js` pass unchanged.

## Open decisions for the owner

1. **Level gain per volley vs per arrow.** Built as +1 per volley (the first arrow that lands). Per arrow would take a
   3-arrow volley straight to level 3 — strong with the lv3 power shot (2.0, pierces).
2. **"Burning" is visual** (a flame on each head, ember trail, fire bursts); the arrows and bursts do not set `fire`
   or apply a burn DoT, to keep the numbers above exact. A short burn on the held bursts would suit the name.
3. **The kick barely staggers** (poise 12, no shove) so the chaser stays in the spot the volley comes down on; with
   poise 25 a hollow soldier flinched ~60 px away and the volley hit it at the range falloff.
4. The icon lives in its own one-icon sheet (`ui_icons17_bow`) to stay out of the other two agents' files; the lead may
   fold it into a shared `ui_icons17`.
