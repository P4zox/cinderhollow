# Background art audit (branch `bg-overhaul`), 2026-10-16

Audit and plan only. No game file was changed. Everything below was checked against in-game captures with shaders on (the
default, `SETTINGS.shaders=1 light=3`). The captures were made from a test build (`BUILD_OUT=web/dist/bg_audit.html`).

## Where the evidence is (`tools/shots/v17/bgaudit/`)
| Path | What |
|---|---|
| `overview_montage.png` | One in-game shot per biome, each next to its parallax-only composite (tint + far + mid) |
| `sheets/<biome>.png` | Contact sheet per biome: a wide/open room and a tight room in game (forge, ramparts and mire have extra rooms), then the parallax-only composite and the raw far and mid layers (2x, mid shown on a checkerboard) |
| `game/<biome>__<wide/tight>__<room>.png` | The 51 in-game captures (1152x648) |
| `raw/<biome>_{far,mid}_x2.png`, `raw/<biome>_{far,mid}_seam_x3.png`, `raw/<biome>_comp_cam{0,1400}.png`, `raw/cfa_bg_*_comp.png`, `raw/xsc_bg_*_comp.png` | Raw layers, the wrap seam (the layer tiled against itself, centred on the seam), and composites at two camera offsets |
| `seam_check.png` | The 12 layers with the highest seam score, side by side |
| `metrics.json` | Per layer: colour count, opacity, mean luminance, share of near-black pixels, saturation, wrap-seam ratio, flatness, best self-repeat period |
| `comfy_test/` | The ComfyUI pipeline test (see the last section) |
| `inv.js`, `snap.js`, `sheets.py`, `comfy_test.py` | Scripts to reproduce. Run: `SHOT_HTML=$PWD/web/dist/bg_audit.html node tools/shots/shot.js tools/shots/v17/bgaudit/snap.js tools/shots/v17/bgaudit/game`, then `python3 tools/shots/v17/bgaudit/sheets.py` |

## How backdrops are made and drawn (what a replacement must match)
- **Generators.** Every backdrop is procedural Python: tileable value noise, ordered dithering onto short hand-picked ramps,
  recursive limb trees, 1px rim light. The output goes through `art/asebuild.py:build()` to `art/bg_<b>_{far,mid}.aseprite` and
  `assets/bg_<b>_{far,mid}.png/.json`. Sources by biome:
  ramparts, catacombs, cathedral (`env_bg.py` via `gen_env.py`) · mire, crown (`env2_bg.py` via `gen_env2.py`) ·
  archives (`archives_bg.py`) · hoarfrost (`hoarfrost_bg.py`) · spire (`spire_bg.py`, `gen_spire_env.py`) · deep (`deep_bg.py`) ·
  hermit, ember (`secrets_env.py`) · thornveil (`thornveil_bg.py`) · barrows (`barrows_env_bg.py`) · crimson (`crimson_env_bg.py`) ·
  necropolis (`necro_bg.py`) · dunes (`dunes_bg.py`) · starfall and starfall_void (`gen_starfall_env.py`) · neohallow (`gen_neo_env.py`) ·
  forge, threshold (`gen_forge_env.py`), with the forge room themes in `gen_forge_bg.py` · omen (`omen_bg.py`) · sov_void (`gen_sovbeast.py`).
- **Format.** Each layer is 512x216 (the view is 384x216, `TILE` 16). The far layer is opaque and the mid layer is transparent. Each
  sheet has a `loop` tag. Some are animated: spire_far has 10 frames with `flash`/`flash2` tags (lightning, read by `22_spire.js`),
  barrows_far, crimson_far (rain), neohallow and sov_void_far have 4 frames each.
- **Drawing.** `drawParallax()` in `web/src/03_world.js:211` first fills `AREAS[b].tint`. It then tiles the far layer at x factor 0.08
  and y factor 0.02, and the mid layer at 0.3 and 0.08. The vertical offset is clamped to `[-(f.h-H)-20, 20]` and each layer is
  drawn bottom-aligned (`oy + H - f.h`). Taller layers are already supported, but every current layer is exactly 216 tall, so in
  tall rooms a layer can slide up by as much as 20 px. That leaves a flat tint band at the bottom, which the floor usually hides.
- **Overrides that wrap `drawParallax`.** Omen K4 sky (`25_omen2.js`) · Starfall nebula and constellations, plus the void phase
  (`35_starfall.js`) · Hoarfrost aurora (`51_rb.js`) · Ramparts Watcher's Perch pano `xra_pano` (`50_ra.js`) · Last Field five layers and the
  vistas, which reuse `bg_spire_*` and `bg_crown_far` (`52_rc.js`) · `xsb_sky` (`54_sb.js`) · secrets `xsc_bg_*` (`55_sc.js`) · training
  mask (`65_training.js`) · the per-room forge themes `CFA_BG` → `cfa_bg_<theme>` with `far`/`mid` tags (`82_forge.js:782`) ·
  sov_void and neohallow_cyber are swapped in at runtime by `26_sovereign2.js` and `36_neohallow.js`.
- **Far-layer sun coordinates.** `GFX_SUN` in `40_gfx.js:185` follows a sun painted into ramparts_far (243,111) and dunes_far
  (297,34). Cathedral, crown, hoarfrost, spire and others take screen-space ray sources. **If a redraw moves the sun or moon, update
  `GFX_SUN`.**
- **Indoor back walls.** In `indoor` rooms (245 of 299) the back-wall tiles cover the parallax: alpha 1 next to terrain, then 0.8,
  then 0.5, and 0.28 in open space (`03_world.js:180`). On top of that comes the biome ambient darkness (0.6 for catacombs). So in
  dark indoor biomes the parallax contributes almost nothing. Where the wall gives way to sky it ends in a hard 16px staircase
  (seen in CT1, DU1, H2). That is an engine issue, not a backdrop issue.
- **Existing ComfyUI precedent.** The Sunlit Yard (`git show 'stash@{0}^3:art/gen_sunlit.py'`, raw renders from
  `art/concepts/gen_sunlit_raw.py`): SDXL + pixel-art-xl + Lightning text2img at 1536x864 → BOX downscale → `quantize(MAXCOVERAGE,
  kmeans)` to 64 colours (sky) or 24 (arches) → white keying for the cutout layer → 40px crossfade `seamless()` → a contre-jour rim grade →
  `asebuild.build`. `~/Claude/pixelgen/comfy.py` adds img2img (`init_image`, `denoise`), ControlNet Union (`pose=`, `pose_type=`), an
  IP-Adapter reference (`ref=`) and an auto v-pred switch for NoobAI.

## Ranking (1 = poor, 5 = strong)
Columns: **D** depth/parallax readability · **P** painterly vs flat/procedural · **M** mood fit (dark mythology, sleek, not cartoony) ·
**C** consistency with the pixel scale and palette · **S** seams/tiling/repetition (5 = none visible) · **R** how well the player and
foes read against it. **Vis** is how much of the backdrop players actually see: main path, room count, and how much the indoor walls
hide it.

| # | Biome | D | P | M | C | S | R | Avg | Vis | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ramparts | 4 | 4 | 5 | 4 | 4 | 4 | **4.2** | main, high | keep (the quality bar) |
| 2 | lastfield (xrc_lf_*) | 4 | 4 | 4 | 4 | 4 | 4 | 4.0 | 1 room | keep |
| 3 | crimson | 4 | 3 | 4 | 4 | 4 | 4 | 3.8 | opt., mostly hidden | keep |
| 4 | omen (K4 boss sky) | 3 | 3 | 4 | 4 | 4 | 4 | 3.7 | boss | keep |
| 5 | thornveil | 4 | 3 | 4 | 3 | 4 | 3 | 3.5 | opt. | keep; later palette cleanup |
| 6 | starfall | 3 | 3 | 4 | 4 | 3 | 4 | 3.5 | opt. | keep; small fixes |
| 7 | sov_void / starfall_void | 3 | 3 | 4 | 4 | 4 | 3 | 3.5 | boss phases | keep |
| 8 | barrows | 3 | 3 | 4 | 4 | 3 | 3 | 3.3 | opt. | keep; small fixes |
| 9 | mire | 3 | 3 | 4 | 4 | 3 | 3 | 3.3 | **main** | light rework |
| 10 | forge (+6 cfa themes) | 3 | 3 | 4 | 4 | 2 | 3 | 3.2 | post-game, new | light pass later |
| 11 | spire | 3 | 2 | 4 | 4 | 3 | 3 | 3.0 | **main (exp. 1)** | rework |
| 12 | archives | 3 | 2 | 3 | 4 | 3 | 2 | 2.8 | **main (exp. 1)** | rework |
| 13 | hoarfrost | 2 | 2 | 3 | 4 | 3 | 3 | 2.8 | **main (exp. 1)** | rework |
| 14 | crown | 3 | 2 | 2 | 3 | 3 | 4 | 2.8 | **main, final, bright** | rework |
| 15 | cathedral | 2 | 2 | 3 | 4 | 1 | 4 | 2.7 | **main** | rework |
| 16 | dunes | 3 | 2 | 2 | 3 | 3 | 3 | 2.7 | opt. (19 rooms) | rework |
| 17 | catacombs | 2 | 2 | 3 | 3 | 3 | 2 | 2.5 | **main (19 rooms)** | rework |
| 18 | deep | 2 | 2 | 2 | 3 | 3 | 3 | 2.5 | **main (exp. 1)** | rework |
| 19 | necropolis | 2 | 2 | 3 | 4 | 1 | 3 | 2.5 | opt. (19 rooms) | rework |
| 20 | threshold | 2 | 1 | 3 | 3 | 2 | 4 | 2.5 | W2 entrance (2 rooms) | rework |
| 21 | neohallow | 3 | 2 | 3 | 3 | 2 | 2 | 2.5 | secret, off-style on purpose | fix the seam only |
| 22 | hermit | 2 | 1 | 3 | 3 | 4 | 4 | 2.3 | secret (4 rooms) | rework (cheap) |
| 23 | ember | 1 | 1 | 3 | 3 | 3 | 3 | 2.3 | secret, post-game (7) | rework (cheap) |
| — | training, neohallow_cyber | — | — | — | — | — | — | n/a | | intentional (white void, wireframe) |

## Defects by biome
- **ramparts** (4.2): the lower sky is horizontal dithered stripes, and the bottom third of the far layer is an empty flat purple
  band. Otherwise the reference for the whole set: one focal point (the golden root-tree in the sunset), three distinct depth
  planes, warm vs cool.
- **catacombs** (2.5): the far layer is three near-identical blocks of root plus niche wall. The niches are bare dark rectangles,
  the teal glows are coarse dither blobs, and 77% of pixels are near-black. Under ambient 0.6 and the back walls it is close to
  invisible in game (C8, C10). The mid arches are uniform dark slabs and the roots are 1–2px lines. Muddy darks; no depth
  reads at all.
- **cathedral** (2.7): the far layer is literally two copies of a 256px half (repeat correlation 1.00 at period 256), giving four
  identical lancet windows. The mid arcade also repeats every 256. Light shafts are diagonal dither stripes. It has no "sunken"
  idea (water, drowned nave) and no stained-glass colour, and is monotone slate. The player reads fine.
- **crown** (2.8): a bright pale world (ambient 0.12), so it is the most visible backdrop in the game. The puffy cumulus clouds and
  cotton-ball "bonsai" foliage read as cartoony, against the dark-myth rule. The mid root trunk is built from flat colour blocks with
  vertical steps. The far layer is chunky and low on detail, and branch tips are cut at the wrap seam. X10 (indoor) shows none of it.
- **archives** (2.8): the composition is good (a curved tower wall of shelf galleries, a central spiral book-tower). But it is
  dark violet-on-violet: the shelves are only horizontal lines, and 63% of pixels are near-black. In game (A8, A16) it dissolves into
  the back wall. There is a slight shelf misalignment at the wrap seam.
- **hoarfrost** (2.8): 88% near-black. The aqueduct is a flat silhouette band, the mountains are one plain ramp, and the frozen
  waterfall in the mid layer is crude. The bottom 30% of the far layer is empty. The aurora overlay in vista rooms (HF14) carries
  the look; without it the biome is flat.
- **spire** (3.0): a good idea (a storm sea, a far tower, the lightning frames). The mid layer is flat black blobs (flatness 0.77):
  cliffs, a windmill and a bridge with no interior value. The far sea is only scattered specks, and the cloud bands are
  procedural. The animated frames and tags must be kept, because `22_spire.js` and `52_rc.js` read them.
- **deep** (2.5): the far layer is repeating kiln cones with orange "eye" blobs, and the lava falls are ruler-straight sine lines.
  The mid layer is flat cartoon gears and pipes (a steampunk read that is off-identity). The bottom lava glow is the only depth cue.
- **mire** (3.3): the far trees stand on three identical islets, and the sky is horizontal banding. Overall it is muddy mid-green.
  The mid trees are fine. It needs variety and one focal point, not a redo.
- **necropolis** (2.5): the mid layer is four identical arches (repeat 0.97 at 256). It also has a fully opaque dark band about 25
  px tall across the top (`seam_alpha` 0.62), which covers the far sky. The far spires are generic triangles in flat navy. In game
  it reads as flat blue.
- **dunes** (2.7): oversaturated amber everywhere (saturation 0.69). The Anubis bust in the mid layer is blocky, flat and too big:
  in DU1 it sits right behind the player at the player's scale and reads like foreground. The sphinx and pyramids are posterized,
  and the jagged cave-mouth silhouette along the top is crude. A literal Egypt read instead of a dark-myth one.
- **threshold** (2.5): only 8 colours. The puffy posterized clouds, five plain obelisk "sticks" and a repeating arcade are the
  weakest drawing in the game, at a key story beat (the World 2 entrance). The CT1 wall-to-sky staircase edge is very visible here.
- **hermit** (2.3): a gradient sunset with a glowing "root" bar that looks like a lens streak. The hills are banded, and the mid
  layer is 3 colours of stacked-triangle pines.
- **ember** (2.3): rows of identical vertical posts and dotted ember squiggles. The mid layer's dark ground band hides the far
  layer's only good feature, the glowing lava horizon, so in game it is black with orange dots.
- **neohallow** (2.5): a hard vertical seam through the purple cloud band in the far layer (`seam_check.png`, bottom left). Window
  dots everywhere compete with the player in NH8. The magenta checker squares in NH17 look like missing-texture props, so check
  whether that is intended. The style is off-identity on purpose (a secret), so fix only the seam.
- **forge** (3.2): the base far layer repeats at 256. In game all six `cfa_bg` themes come out as one monochrome slate-blue
  with low contrast; only CF8 (the hearth) has warmth. The area was just shipped, so it gets a light value and accent pass only.
- **barrows / starfall / thornveil / crimson** (3.3–3.8): barrows_mid is near-black (95%). The starfall nebula is posterized into
  hard bands, and the comet streak repeats every 512. Thornveil has 169 colours (no palette discipline) and vertical dither
  streaks in the fog. Crimson's manor overlaps its castle silhouette. None of these needs a regeneration.

### Cross-cutting (engine-level, outside this art pass but worth one ticket)
1. All far layers are 512 wide, so with a 384 view a 256-period motif shows twice on one screen. A 1024-wide far layer for the
   reworked biomes is cheap, and `build_web.py` regrids wide sheets already.
2. All layers are 216 tall, so there is no vertical travel in tall rooms (NV10, CF3, SP12, W-shafts). New layers can be 256–288 tall
   with the extra height at the top; `drawParallax` already handles it.
3. Biome ambient darkness and the 0.28 back-wall alpha flatten the dark indoor biomes. Either paint those layers a few value steps
   lighter (as `gen_forge_bg.py` already does), or apply less of the darkness layer to the parallax.
4. The hard 16px back-wall staircase where an indoor wall meets open sky (CT1, DU1, H2).

## Recommended targets (most visible first)
1. **catacombs** · 2. **cathedral** · 3. **crown** · 4. **archives** · 5. **deep** · 6. **hoarfrost** · 7. **spire** · 8. **mire** (light) ·
9. **necropolis** · 10. **dunes** · 11. **threshold** · 12. **ember + hermit** (cheap, last).
Keep as they are: ramparts (the reference), lastfield, crimson, omen, the void skies, barrows, thornveil, starfall, training, cyber.
Later small fixes: neohallow seam; necropolis mid top band (if it isn't rebuilt); the forge value pass.

Per target, what to change (identity kept: same subject, palette family, silhouette language and dark tone; only depth, detail
and variety improve):
| Target | Far | Mid | Notes |
|---|---|---|---|
| catacombs | an ossuary vault receding into dark: tiers of skull niches with real depth falloff, one distant lit chapel or shaft of root-light as the focal point, root masses across the ceiling | broken arches with stone texture and rim light, roots draped over them | +2 value steps; teal glow only as an accent |
| cathedral | a drowned nave with one large rose or lancet group as the focal point; varied bays (no 256 repeat); moonlight shafts; water reflections at the base | an arcade with varied capitals, hanging censers and chains, broken pews in the water | keep the `GFX_SUN` cathedral entry (indoor moonlight) roughly matched |
| crown | the pale colossal tree crown in mist, with real bark and branch structure instead of cotton foliage; thin high cloud, not cumulus | ashen white boughs with sharp twig silhouettes; the root rendered as bark | keep the bright palette (gameplay readability); remove the cute shapes |
| archives | the tower interior with lit candle tiers, visible book spines in near shelves, stronger light shafts from the bell chamber | shelf towers with readable books, chained tomes | +2–3 value steps |
| deep | a root-forge cavern: petrified root ceiling, distant furnace towers with molten seams, curtains of lava with heat haze | forge machinery, but anvils, crucibles, chains and root-bound girders instead of cartoon gears | the deep is a main-path boss area |
| hoarfrost | a frozen aqueduct leading off into snow mountains under the moon; ice detail and depth fog | broken aqueduct arches with real ice, a frozen waterfall with volume | aurora overlay stays on top |
| spire | the storm sea with wave structure, the spire tower painted rather than silhouetted | cliffs, windmill and bridge with interior value and rain-wet rim light | **keep 10 frames and the `flash`/`flash2` tags**: generate the base once, then reapply the flash as a brightness/colour pass per frame |
| mire | remove the triple-islet repeat, add one far focal point (a drowned shrine or a giant dead tree), break the sky banding | keep | img2img at low denoise is enough |
| necropolis | a city of the dead under a night sky: varied mausolea and spires with depth fog | varied arches (no 256 period), **remove the opaque top band** | |
| dunes | the desert under a hazy sun; ruins and a distant colossal statue at background scale; less saturation | ruined columns; the Anubis is smaller, further back and more sculpted (or dropped) | keep the far-sun coords (297,34) or update `GFX_SUN` |
| threshold | a grey storm sky with structure, a distant broken wall or gate as the threshold to World 2 | a ruined arcade with weathered obelisks | the story beat earns a proper focal point |
| ember / hermit | a forest of charred trunks with a glowing horizon visible / a dusk sky with a real horizon | lower mid ground band so the far glow shows / pines with branch structure | small secret areas, so budget 1 h each |

## Production method per target
1. **Guide (composition).** Start from the current layer when its composition is fine (archives, mire, spire, hoarfrost). For
   cathedral, catacombs, necropolis, deep and threshold, break the repetition first: make a 512x216 (or 1024x256) layout and value
   sketch. The quickest way is to edit the existing generator's parameters (positions, a focal element) or paint it in Aseprite.
   Every structural mistake in the guide survives into the result (see the test).
2. **Generate at 3x** (1536x648; 3072x768 for a 1024-wide far layer, run as two overlapping halves) with SDXL base +
   `pixel-art-xl` + `sdxl_lightning_8step` (8 steps, cfg 1). Use img2img over the guide at **denoise 0.75–0.82**, plus
   **ControlNet Union `canny/lineart`** from the guide's edges at strength **0.4–0.5**, ending at 0.6. Optionally add an
   **IP-Adapter reference of `bg_ramparts_far`** at weight 0.3–0.4 to pull every biome toward the best layer's rendering style. Run
   4–8 seeds and pick by eye. Prompt: `pixel art, dark fantasy, <subject>, side-scroller game background, muted <palette>,
   atmospheric depth, haze`. Negative prompts do nothing at cfg 1, so steer with the prompt and the guide. NoobAI and Illustrious
   (25 steps, cfg ~5, about 3x slower) are for a biome where the base model's look is too photographic.
3. **Seamless.** Roll the image by half its width, then re-noise only a centre band 384 px wide at 3x scale with
   `SetLatentNoiseMask` at denoise 0.5. Composite with a feathered mask so pixels outside the band are untouched, then roll back.
   This is validated in the test; the seam is invisible. It is better than the Sunlit Yard crossfade, which shortens the layer and ghosts.
4. **Pixel scale and palette.** BOX-downscale to the exact layer size. Quantize to the biome's existing ramps (the hex ramps at the
   top of each `*_bg.py`) **plus at most 8 new accent colours**, aiming for ≤32 colours in the far layer and ≤16 in the mid layer, with
   no dither. Then remove 1px orphans with a 3x3 majority filter (the test result is a bit smudgy without it). Reapply the house
   ordered dither (`envlib.bt`) only on large gradients, so the layer matches the hand-built ones.
5. **Mid layers (alpha).** Generate the mid layer **on its own** against a flat white or grey ground, using ControlNet lineart from
   the guide silhouette. Key it with the guide's own alpha (dilated 1px) instead of colour keying, which is safer for dark
   silhouettes. Then hard-threshold alpha to 0/255 (the mid layers are binary today), add the 1px rim light on sky-facing edges as
   `env_bg.py` does, and keep the silhouette mostly in the lower two thirds so the far layer shows.
6. **Grade for the game.** Check under in-game lighting, not on a checkerboard. Keep the mid layer darker and lower in contrast
   than the play layer. Keep the far-layer brightness at or above the current one for dark biomes. Keep the hue contrast against
   the player's red cape and steel. Update `GFX_SUN` if a sun or moon moves.
7. **Build.** Write a new `art/gen_<biome>_bg2.py` per biome that loads the picked raw renders from `art/concepts/<biome>_bg_raw/`
   and writes **the same asset names, size, tags and frame count** through `asebuild.build`. Then nothing in `web/src` changes.
   Keep the old generator for rollback.
8. **Verify.** Re-run `snap.js` and `sheets.py`, compare the before/after contact sheets, and check the seam crops and the
   `metrics.json` deltas (repeat < 0.6, seam ratio < 1.5, near-black share down for the dark biomes).

**Time per biome**, with a human pick at each stage: guide 20–40 min · generation, about 2 layers × 6 seeds × (pass + seam pass) ≈
3–4 min of machine time · selection, keying, palette and grading 45–75 min · in-game check and tweaks 20–30 min.
**About 1.5–2.5 h per biome**, plus about 1 h for spire (animation frames) and for any 1024-wide far layer. The 11 rework targets
come to **about 20–26 h**, ember and hermit to about 2 h together.

## ComfyUI pipeline test (`tools/shots/v17/bgaudit/comfy_test/`)
- `~/ComfyUI/run.sh` started and answered on :8188 within 6 s. The server was stopped after the test (port 8188 is free).
- The test was img2img over `bg_cathedral_far` (nearest 3x → 1536x648, blur 1.2), SDXL base + pixel-art-xl + Lightning (8 steps),
  then the roll and masked seam pass, then BOX down to 512x216 and a palette lock (the original 17 colours plus 8 new accents).
  - **a** (`a_compare_cathedral.png`): ControlNet `tile` 0.55, denoise 0.62. Almost a copy of the source, only softer. Too conservative.
  - **b** (`b_compare_cathedral.png`): ControlNet `canny/lineart` 0.45 ending at 0.6, denoise 0.8. It added real masonry, tracery,
    vault ribs and a broken-pew base, and stayed in palette (14 colours). It lost the light shafts and the values flattened toward
    mid-grey, so a grade step is needed. **The four identical windows survived**, which shows that the composition has to be fixed
    in the guide. The seam is invisible (`b_seam_crop.png`). The high seam ratio, 1.72, comes from a pillar edge sitting at the wrap
    line, not a discontinuity.
- **Speed (M5 Pro, MPS):** 19.3 s for the first pass (includes the model load), then **about 7–8 s per 1536x648 image** warm
  (7.1 s pass, 8.1 s seam pass). That is about 15 s per finished seamless layer candidate.
