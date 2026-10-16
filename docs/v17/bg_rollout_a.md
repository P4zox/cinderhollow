# BG rollout, agent A: crown, archives, deep, spire (branch `bg-overhaul`), 2026-10-16

Method as in `bg_pilot.md` (guide → SDXL + pixel-art-xl 0.6 + Lightning img2img with ControlNet lineart → roll-and-repaint seam →
BOX down → palette lock to the v1 ramps extended upward → majority filter → asebuild). **All four v2 layers beat v1 in game**
(`tools/shots/v17/bgroll/A_before_after.png`, shaders on, default lighting, no veil change). Nothing committed.

Every biome keeps the same asset names, sizes, tags, frame counts and alpha contract (far opaque, mid binary alpha). spire keeps
its 10 + 4 frames, the `loop`/`flash`/`flash2` tags and the v1 frame timings. Each generator rebuilds its assets
pixel-identically from the saved renders (checked by md5). The v1 layers are in `art/bg_src/<biome>/v1/` for rollback.

## Files
| File | What |
|---|---|
| `art/bgroll_a_lib.py` | agent A helpers on top of `bgv2lib`: `use_prefix` (each biome's ComfyUI outputs go to `output/bgv2/<biome>_*` on the shared server), `sweep` / `finish` (seed sweep with a contact sheet, then the seam pass on the pick), `tree_segs` (upward branching limbs for the guides), `key_color` + `mid_pipeline_ck` (mid layers keyed by colour against the flat grey ground inside the guide's dilated coverage, so the model's own twigs and edges survive; thin parts get no rim), `seam_pass_free` (seam pass with no tile ControlNet, see deep) |
| `art/gen_bg_{crown,archives,deep,spire}_v2.py` | per biome: guide, prompts, `RENDER` settings, `PICK` seeds, post and grade, build. `--guide`, `--sweep <layer> <seeds> [tag]`, `--finish`, `--no-ase` |
| `art/bg_src/<biome>/` | guides, edges, `sweep/` (every candidate plus sheets), `*_pass1.png` / `*_render.png`, `out_*`, `preview.png`, `stats.json`, `v1/`. spire also has `out_far_0..9.png`, `out_mid_0..3.png` and `far_frames.png` |
| `assets/bg_{crown,archives,deep,spire}_{far,mid}.png/.json`, `art/bg_*.aseprite` | rebuilt |
| `tools/shots/v17/bgroll/<biome>/{before,after}/` | in-game shots: 4–5 rooms per biome. `after_veil_test/` (archives, deep) is the same rooms with the veil patched into a test bundle only. `raw/` has the v1/v2 layers and the parallax previews |
| `tools/shots/v17/bgroll/A_before_after.png`, `A_seam_crops_x3.png`, `snap_a.js`, `a_before/` | the montage, the wrap seams of all 8 layers, the snapshot script, the v1 captures |

No `web/src` file was touched. `03_world.js` and `01_data.js` were left to agent C; the needs are listed below.

## crown (The Pale Crown): most visible, rebuilt from scratch
- **v1 problems**: cumulus puffs, cotton-ball bonsai foliage, a root built from flat blocks. It read as cartoony.
- **v2 far** (sweep b, seed 5): a colossal pale world-tree rising out of a sea of mist. It has furrowed ashen bark, wide bare limbs
  ending in fine twigs with a faint gold light caught in them, and two ghost trees in deep haze. There are thin high cirrus clouds
  instead of cumulus, and half-sunk giant roots. The tree is at far x≈206, inside the visible range 0..420. The post grade deepens
  the zenith toward cool lavender-blue and adds a warm glow behind the crown, so the layer reads mythic and not foggy-grey. The
  palette is the v1 sky, cloud, branch and gold ramps plus a neutral ash-grey ramp (36 colours, still bright: mean lum 191).
- **v2 mid** (sweep c, seed 5, denoise 0.55): one gnarled ashen bough across the width, with furrowed bark, a lit crest, buttress
  roots and hanging rootlets. Four bare trees of very different sizes grow from it, with sharp twigs and sparse pale-gold leaf
  strokes. One is a snapped snag.
- **In game** (X7, X3, X9, X11, X10): the brightest biome now reads as solemn myth instead of a cartoon. The player and the gold
  Sentinels read as dark shapes on pale. The X11 panorama overlay still sits on top of the new far layer cleanly. `GFX_SUN.crown` is
  unchanged: it has no far-layer anchor, and the source at uv 0.68 still lands on the bright sky right of the tree.
- Caveat: at the bottom of X7 the trunk's lower bark sits behind the light bloom, so it reads as a soft pale column. That is
  acceptable and comes from the bloom, not the layer.

## archives (The Ashen Archives): v1 composition kept, re-lit as contre-jour
- **v1 problems**: violet on violet, 63% near-black, shelves as bare lines. It dissolved into the bookshelf back walls.
- First pass (a guide made from v1 lifted 2–3 steps, with coloured spines): the far layer became a busy brown book wall behind
  back-wall tiles that are themselves bookshelves, so the shelves doubled up as mush. Rejected.
- **v2 far** (sweep cj, seed 5; `guide_far2`): the same tower interior, but the focal is now a bold silhouette. The spiral
  book-tower (v1 CX 256) stands dark against the column of light falling from the bell chamber. Its helical gallery is picked out by
  candle points, and the slanted shafts are stronger. The wall tiers are curved shelf galleries, desaturated toward the violet air
  (post) so they stay quiet behind the shelf tiles. Mean lum 17.8 → 51.5, near-black share 0.63 → 0.07.
- **v2 mid** (seed 2): the v1 silhouettes (gothic shelf towers, ladders, bridge, cages, the chained tome, fallen books) re-rendered
  with readable coloured spines and carved crowns, then graded dark (black 10, white 640) so they stay behind the play layer.
- **In game** (A8, A16, A2, A11): the light column and tower now read clearly through the indoor veil. The player stays a dark
  shape. A11 is a dark room by design and stays dark before and after.

## deep (The Burning Deep): rebuilt from scratch
- **v1 problems**: repeating kiln cones with orange eye blobs, ruler-straight sine lava falls, flat cartoon gears and pipes (a
  steampunk read).
- **v2 far** (sweep c, seed 3): a root-forge cavern. A stepped forge-temple with a barred glowing mouth sits at x≈178, under a
  vault of hanging petrified roots, with dark cavern pillars. The lava falls are stepped cascades: each pours off a rock lip, pools
  on a ledge and spills again, so none is a straight column. A molten sea runs along the bottom.
  - The standard seam pass (tile ControlNet 0.6) redrew the sea's wrap edge as a hard vertical line. `seam_pass_free` (tile 0,
    denoise 0.6) fixed it. Seed 103 of that pass grew a standing hooded figure at the wrap and was rejected; seed 108 is used.
- **v2 mid** (seed 1): a braced iron gantry and a long beam bound by petrified roots, chains with iron crucibles (one pours a
  molten thread, repainted in post because the model greyed it), and a great anvil on a plinth. No gears.
- **In game** (D11, D5, D17, D2): the cavern has depth and a focal point. The orange falls are behind the dark play layer and do
  not take over the player (red cape on dark iron and brick). D2 is very dark under its own room lighting, before and after.

## spire (The Tempest Spire): animation kept
- **v1 problems**: the mid layer is flat black blobs, the far sea is only specks, and the cloud bands are procedural.
- **v2 far**: one static base (seed 3), rendered from the v1 composition: the median of the v1 loop frames, so no rain is baked in,
  with a painted tower and rolling swells. The 10 frames are rebuilt from it:
  - **loop 0–3 / frame 9**: v1's moving rain, whitecap and rod-spark pixels, added as a brightness delta on the v2 base.
  - **flash 4–6, flash2 7–9**: v1's light field (the frame minus the v1 median, blurred so v1's cloud edges do not show, and
    normalised around the tower so no dark halo appears) lifts the v2 clouds by their own luminance. The bolts are redrawn from v1's
    own geometry (`spire_bg.main_bolt`, `bolt_path`, same seeds) as clean strokes in the BOLT ramp.
  - The sky is graded dark with a soft knee on its highlights. At full brightness, the game's ray/bloom pass turned the lit
    horizon strata into a big pale halo behind the player (SP4/SP11 first pass). The flashes add the brightness back.
  - The grade is pulled toward v1's bruised violet. Frame timings are kept (130 ×4, 60, 90, 150, 70, 100, 150 ms).
- **v2 mid** (sweep b, seed 2): the v1 cliffs, hamlet, causeway arches and sea stacks, re-rendered with strata, crevices, ledges
  and a wet lit band on the sky-facing edges. The static parts come from the render. The moving parts (sails, wave bursts) are the
  v1 pixels re-graded onto the v2 stone ramp, so the 4-frame loop is unchanged.
- **In game** (SP4, SP11, SP8, SP15): the storm sky now has painted strata and the cliffs have form. The player keeps contrast.
  Still mostly dark, as the biome should be. `22_spire.js` swaps `loop` for `flash`/`flash2` the same way, and `52_rc.js` (SP15)
  reads the same tags. `GFX_SUN.spire` is unchanged (no painted moon).

## Metrics (v1 → v2, audit definitions; `art/bg_src/<biome>/stats.json`)
| Layer | colours | mean lum | near-black | repeat | seam |
|---|---|---|---|---|---|
| crown far | 38 → 36 | 195.5 → 190.9 | 0 → 0 | 0.51 → 0.58 | 1.48 → 1.04 |
| crown mid | 19 → 10 | 184.5 → 157.4 | | 0.15 → 0.23 | 0.54 → 0.93 |
| archives far | 21 → 24 | 17.8 → 51.5 | 0.63 → 0.07 | 0.84 → 0.79 (the cylinder's bay rhythm, by design) | 2.16 → 0.99 |
| archives mid | 27 → 19 | 22.0 → 42.7 | 0.53 → 0 | 0.28 → 0.32 | 1.11 → 2.26 (a shelf tower edge on the wrap; visually clean) |
| deep far | 25 → 30 | 26.4 → 38.1 | 0.75 → 0.35 | 0.30 → 0.50 | 0.73 → 1.02 |
| deep mid | 11 → 11 | 19.8 → 31.9 | 0.88 → 0.22 | 0.22 → 0.15 | 1.35 → 0.44 |
| spire far (frame 0; 36 colours over all 10) | 16 → 25 | 18.8 → 23.3 | 0.59 → 0.32 | 0.32 → 0.20 | 1.15 → 1.42 |
| spire mid (frame 0) | 12 → 18 | 19.2 → 26.4 | 0.88 → 0.26 | 0.37 → 0.40 | 1.77 → 1.30 |
All 8 wrap seams were checked by eye at 3x (`A_seam_crops_x3.png`).

## Needs for agent C (`01_data.js` / `03_world.js`)
- **archives**: add `veil: [1, 0.8, 0.5, 0.28]` (smoothing only, the cathedral setting). The new light column shows the stepped
  back-wall boxes at its edges in A16 and A2. Compare `archives/after/` with `archives/after_veil_test/`: it is smoother with the
  veil and no darker.
- **deep**: the same `veil: [1, 0.8, 0.5, 0.28]`, for the same reason (the bright falls behind the stepped veil in D5 and D11).
  It is a smaller gain than archives.
- **crown, spire**: no veil needed (mostly outdoor rooms).
- No `GFX_SUN` change for any of the four biomes.

## Notes for the lead
- `.gitignore` covers `*_pass1.png`, `*_render.png` and `v1/` but **not `art/bg_src/*/sweep/`**: 16–20 MB per biome here, and the
  other agents have sweep folders too. Suggest adding `art/bg_src/*/sweep/` before committing. `out_*`, guides, edges and stats are
  small and can be committed like the pilot's.
- The ComfyUI server on :8188 was not running when I started, so I started it (`~/ComfyUI/run.sh`). I did not stop it.
- Unused leftovers kept for reference: `guide_far()` in `gen_bg_archives_v2.py` (the rejected first pass) and `lava_fall()` in
  `gen_bg_deep_v2.py`.
- Remaining weak spots: the crown far still has a little of the model's soft painterly look in the far haze. The archives mid
  shelf towers are a bit chunky at 1x. Deep D2 and archives A11 are too dark under their own room lighting for any backdrop to
  matter. A tiny brazier at deep far x≈370 might read as a 2 px figure at 2x zoom, but it reads as a torch at 1x.
