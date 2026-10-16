# BG rollout, agent B: hoarfrost, mire, necropolis, dunes (branch `bg-overhaul`), 2026-10-16

Method as in `docs/v17/bg_pilot.md`, assignment in `docs/v17/BG_ROLLOUT.md`. **All four beat their v1 layers in game**
(`tools/shots/v17/bgroll/B_before_after.png`, 2 rooms per biome, shaders on). Revised once after the lead review (dunes warmth, contrast and
the fallen head; hoarfrost calmer behind the play layer). Necropolis and mire are unchanged since the review. Mire is a light rework and its in-game gain is the
smallest: more depth and a moon behind the trees, but no new structure in front. Nothing committed, pushed or published.

## Files
| File | What |
|---|---|
| `art/gen_bg_{hoarfrost,mire,necropolis,dunes}_v2.py` | guide + prompts + picked seeds + grade per biome; same CLI as the pilot (`--guide`, `--render`, `--no-ase`) plus `--sweep far\|mid 1,2,3 [--denoise x --cn x --pix x]` (pass-1 seed sweep and contact sheet into `$BG_SWEEP`) |
| `art/bgv2b.py` | agent-B helpers on top of `bgv2lib`: `set_prefix()` (ComfyUI SaveImage prefix `bgroll/<biome>` on the shared server), `sweep()`, `profile()` (tileable 1-D ridge/dune profile), `smear_wrap()` + `render_layer_smear()` (see Seam below), `wrap_step()` |
| `art/bg_src/<biome>/` | guides, edges, `*_pass1.png` / `*_render.png` (gitignored), `out_*.png`, `preview.png`, `guide_preview.png`, `stats.json`, `render_times.json`; `v1/` = the old layers + aseprite (gitignored) |
| `assets/bg_<biome>_{far,mid}.png/.json`, `art/bg_<biome>_{far,mid}.aseprite` | rebuilt: same names, 512x216, 1 frame, tag `loop`, far opaque, mid binary alpha. **Mire: far only** (the audit said keep the mid; `bg_mire_mid` is untouched) |
| `web/src/40_gfx.js` | `GFX_SUN.dunes` far-sun coords `{x: 297, y: 34}` -> `{x: 294, y: 31}` (the painted sun moved 3 px). No other engine change |
| `tools/shots/v17/bgroll/` (gitignored like the pilot's) | `snap_b.js` (12 spots, 3 per biome), `cmp.py`, `before/`, `after/`, `<biome>/before_after.png` + the single shots, `B_before_after.png` |

Rebuild is deterministic from the saved renders (all four rebuilt twice, md5-identical). Old generators kept for rollback
(`hoarfrost_bg.py`, `env2_bg.py`, `necro_bg.py`, `dunes_bg.py`; or copy `art/bg_src/<biome>/v1/*` back).

## Hoarfrost (`gen_bg_hoarfrost_v2.py`)
- **Far**: the moon stays at (150,36). Two snow ranges lit on the moon side, frozen falls on the cliffs, gorge mist, the two-tier aqueduct
  receding toward the moon (same cosine scale idea as v1), a frozen lake and snowy pines at the bottom (v1's bottom 30 % was empty). The
  **painted aurora is kept** as a teal curtain in the upper right. The HF14 live aurora overlay (`51_rb.js`) still draws on top, untouched.
- **Mid**: near aqueduct piers with masonry and icicle soffits, three different spans (a big arch, two small arches with the deck fallen in
  at the end, a snapped channel) and a frozen waterfall with volume (blue ice flutes, a frozen splash pool) from the break. Pines and rocks at
  the base. The top 94 rows are empty (v1: 82).
- Render: far seed 6, denoise 0.72, cn 0.45->0.6, pixel-art-xl 0.45; mid seed 6, denoise 0.7, cn 0.5->0.7, pix 0.6. Grade: far gamma 0.88,
  sat 0.8, plus 4 moon-halo half-steps in the palette (the halo was a hard disc without them); mid black 16 / white 400 / gamma 0.8 with the
  ice blues kept so the waterfall stays cold.
- In game (HF14, HF6): depth where v1 was 88 % near-black; the moon, the aurora and the falls read; the player stays the brightest warm shape.
- **Revision after lead review** (HF6 was a touch bright and busy behind the play layer): `far_post` now drops the snow-range band
  (y≈56-128) by about 2 value steps (the brightest snow most) and softens it (a wrap-padded blur, 60 % mix), and the global dither went
  from `dk` 0.4 to 0.3. The moon, the aurora and the aqueduct keep their values. Far mean luminance went from 60.0 to 56.4.

## Mire (`gen_bg_mire_v2.py`, far only)
- The three identical islets are gone. Focal point: a drowned chapel with a spire and a faint candle-lit door at x≈215. Moss-hung dead
  trees on two banks of different size, crosses and posts in the water, distant ruined spires in the haze, a rippled reflection. The sky
  is soft cloud masses and a halo instead of dithered horizontal stripes. The moon stays at (338,58), so the mid layer lines up as before.
- Render: seed 2, denoise **0.48**, cn **0.7**->0.65, pix 0.5. At 0.55-0.62 every seed turned the chapel into a lit cabin or a "haunted
  house" (cartoony) or the trees into leafy ones, so the guide is held tighter. Grade black 10 / white 225 / gamma 1.12 so the tree and
  chapel silhouettes separate from the mist through the v1 mid trees and the back-wall veil.
- In game (M7, M2): the mire reads deeper (lit mist and a moon behind the mid trees). The improvement is real but modest; the chapel is
  mostly hidden behind the v1 mid trees in these two rooms. M14 looks the same as before (its own painted moon glow dominates).

## Necropolis (`gen_bg_necropolis_v2.py`)
- **Far**: a night city of the dead in three planes: a hazy skyline of bone needles and domes, the focal black cathedral at x≈205 (twin needle
  spires, a belfry, a tall pointed ghost-fire window), a terrace of varied mausolea (domes, gables, stepped tombs, obelisks) with a few lit
  doors, a cemetery ground with headstones and an iron fence, and a waning moon. Blue mist between the planes.
  The window is a pointed lancet, not a rose: the first sweep turned a round window into a clock face. The great bell of v1 did not survive the
  render as a readable bell (the belfry is lit). The mid layer keeps bells.
- **Mid**: an ossuary arcade with **five different bays and a collapsed one (no 256 period: repeat 0.97 -> 0.24)**, a ruined spandrel wall with
  a ragged top at y≈80, a snapped crown, a snapped pier with a bone heap, skull niches in the piers, chains with bells and blue ghost lanterns,
  and an iron railing. **The opaque top band is gone** (top 25 rows: 100 % -> 0 % coverage; first covered row 83).
- Render: far seed 5, denoise 0.74, cn 0.45->0.6, pix 0.45 (the guide is lifted x1.9 before rendering, because the dark first guide rendered as
  flat silhouettes, and graded back down); mid seed 2, denoise 0.7, pix 0.55. Far post: highlights above luminance 120 are compressed 2:1 so the
  window does not out-shine the play layer in NV10, where it sits behind the player at camera start.
- Rejected: far seed 3 (small hooded figures among the headstones), far seed 2 (a blue flame read as a creature), mid seeds 1, 3 and 4 (red
  lanterns, figures between the arches, purple lights).

## Dunes (`gen_bg_dunes_v2.py`)
- **Revision after lead review** (the first grade overcorrected to hazy, muddy brown): the ramps are now the v1 ramps at 0.8 saturation (was
  about 0.6) with grade sat 1.35, so **far saturation is 0.53** (v1 0.69, first pass 0.41). A luminance S-curve in `far_post` deepens the
  shaded faces of the temple and colossi and cleans the sky glow. The horizon haze band is lifted for aerial depth, and the mid layer is
  darker (black 52) with a 2 px gold rim (`RIM[3]` / `RIM[1]`), so DU3 separates far / mid / play. **The fallen head is moved down and scaled
  0.85x** (sunk to the lips, top at y≈160 instead of ≈130) and lifted ~35 % inside its outline (`mid_post`). It now sits low and reads as a
  rim-lit carved head under the DU1 platform instead of a dark mass behind the player. The mid was re-rendered (seed 2) and the far render was
  re-graded only (not re-rendered).
- Identity kept: the buried desert seen through a rift in a cavern roof. The roof is now layered sandstone strata with a sunlit lip and a few
  thin sand trickles, instead of the jagged band. **Saturation 0.69 -> 0.53 (far), 0.71 -> 0.61 (mid)**: the v1 ramps at 0.8 saturation, plus
  half-steps in the sky ramp so the sun halo has no rings.
- **The blocky Anubis is gone.** The jackal god now lives at background scale: far focal is a rock-cut temple in a far mesa (x≈75-245) with four
  seated colossi flanking a dark door (Abu Simbel read), with pyramids and far mountains in the haze. The mid layer has a colonnade under a
  broken architrave and cavetto cornice, **a fallen colossal sun-king head sunk in the dune** (sculpted face, striped headcloth, cracked brow),
  a pylon fragment and two obelisks. These are dark umber silhouettes against the bright far layer.
- The sun is painted at (294,31) (v1 (297,34)), so `GFX_SUN.dunes` follows it.
- Render: far seed 11, denoise 0.62, cn 0.55->0.65, pix 0.45, seam pass denoise 0.68 after `smear_wrap` (see Seam); mid seed 2, denoise 0.7,
  pix 0.55, graded black 52 / white 480 / gamma 0.78, gold rim. The far post fills one 18x18 box (`PATCH`) where the model left a creature-like stump.
- This was the hardest biome. With "jackal-headed" in the prompt, every seed sprinkled the empty dunes with jackals, riders or hooded
  walkers. The prompt now says "statues of ancient gods ... an empty lifeless desert". Seeds 1/3/4/5/6/7/8/10 of the various sweeps were
  rejected for that, seed 1 of the first sweep for a cute seated dog, and seed 7 for a torii gate. A seated jackal colossus in the guide
  rendered as a goat-like blob, so it became the temple facade.
- In game (DU1, DU3): warm, graphic desert light with no blocky bust behind the player. The rock temple is the focal point in DU3, and the player
  reads as a dark knight on a light ground. In DU1 the fallen head is low, under the platform, and rim-lit.

## Seam (worth knowing for every agent)
`bgv2lib.seam_pass` alone did **not** fix the dunes far wrap. The pass-1 dune bands ended at different heights on the two edges, and the tile
ControlNet (0.6) in the seam pass faithfully kept that hard step (wrap step 6.7 -> 5.4 at 3x). `bgv2b.smear_wrap()` replaces the ±48 px (3x)
around the wrap with a linear blend before the seam pass, and the model repaints it: **0.53**. `render_layer_smear()` is a drop-in for
`render_layer` that does this. Final 1x seam ratios: hoarfrost far 1.44 / mid 0.59, mire far 1.44, necropolis far 1.17 / mid 1.83 (an alpha
edge, a pier sits on the wrap, visually clean), dunes far 0.83 / mid 0.11. The seam crops were checked by eye.

## Metrics (v1 -> v2, audit definitions)
| Layer | colours | mean lum | near-black | repeat | seam |
|---|---|---|---|---|---|
| hoarfrost far | 20 -> 32 | 13.1 -> 56.4 | 0.88 -> 0.08 | 0.35 -> 0.53 | 0.96 -> 1.44 |
| hoarfrost mid | 14 -> 19 | 19.3 -> 47.1 | 0.83 -> 0.14 | 0.26 -> 0.34 | 0.12 -> 0.59 |
| mire far | 23 -> 31 | 38.5 -> 50.3 | 0.12 -> 0.03 | 0.70 -> 0.62 | 0.80 -> 1.44 |
| necropolis far | 71 -> 27 | 15.0 -> 50.7 | 0.70 -> 0.24 | 0.30 -> 0.22 | 1.18 -> 1.17 |
| necropolis mid | 4 -> 13 | 10.6 -> 30.2 | 0.99 -> 0.23 | **0.97 -> 0.24** | 9.98 -> 1.83 |
| dunes far | 25 -> 36 | 100 -> 110 | 0.15 -> 0.12 | 0.90 -> 0.90 (the roof's single cosine arc, not a repeat) | 0.84 -> 0.83 |
| dunes mid | 8 -> 10 | 32.7 -> 30.2 | 0.38 -> 0.30 | 0.33 -> 0.38 | 0.00 -> 0.11 |

Machine time per biome: about 2.5-4 min of finished renders (far + mid ≈ 80-160 s on the shared, busy server) plus 4-6 sweeps of 4-6 seeds.

## For agent C (`veil` key, 01_data.js / 03_world.js are C's)
The brighter far layers make the stepped back-wall veil boxes more visible in two of my biomes:
- **necropolis**: NV15 shows a hard-edged rectangle of parallax around the open area (`tools/shots/v17/bgroll/necropolis/after_necropolis__tight__NV15.png`).
  Please add a smoothing veil, e.g. `veil: [1, .8, .5, .28]` (smoothing only, like cathedral).
- **dunes**: DU1 shows the box frame around its window to the parallax, in v1 and v2 alike (`dunes/after_dunes__tight__DU1.png`). Smoothing veil
  `[1, .8, .5, .28]` please.
- hoarfrost and mire: no box edges seen in the shot rooms, so no veil is needed.

## Caveats (honest list)
- Pixel density is the pilot's look: painterly, with 2-3 px forms. It is softer than the 1 px-crisp ramparts layer.
- Mire: the gain is moderate in game, and the v1 mid trees hide most of the new chapel in the shot rooms.
- Necropolis far: the great bell of v1 is now only a lit belfry. The mid stone came out slightly warm-grey rather than blue even with the tint
  grade. It is dark enough that it does not matter in game.
- Dunes: if the owner wants the jackal god closer than the far temple's colossi, it would have to be painted, not rendered: every render of
  a jackal figure came out cute or creature-like.
- Hoarfrost far: some ordered dither is still visible in the sky at 3x zoom (house style, `dk` 0.3).
- The test bundle is `web/dist/bgroll_b.html` (ignored). It also contains whatever agents A and C had built at that moment, which does not
  affect my biomes.
