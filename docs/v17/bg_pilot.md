# Background v2 pilot: catacombs + cathedral (branch `bg-overhaul`), 2026-10-16

Pilot of the ComfyUI-assisted method from `BG_AUDIT.md` on the two weakest main-path backdrops. **Result: both clearly beat the
v1 layers in game** (`tools/shots/v17/bgpilot/before_after.png`). Nothing committed.

## What changed
| File | Change |
|---|---|
| `art/bgv2lib.py` | new shared pipeline: guide painter, ComfyUI render + seam pass, palette lock, cleanup, keying, rim, asebuild, metrics |
| `art/gen_bg_catacombs_v2.py`, `art/gen_bg_cathedral_v2.py` | per-biome guide + prompts + picked seeds + grade; rebuild from the saved renders |
| `art/bg_src/<biome>/` | guides, edges, raw renders (`*_pass1.png` before the seam pass, `*_render.png` seamless), outputs, stats; `v1/` = old layers |
| `assets/bg_{catacombs,cathedral}_{far,mid}.png/.json`, `art/bg_*.aseprite` | rebuilt. Same names, 512x216, 1 frame, tag `loop`, far opaque, mid binary alpha |
| `web/src/03_world.js` (+17 lines), `web/src/01_data.js` | **engine change, opt-in**: `AREAS[b].veil = [a1, a2, a3, aOpen]` gives the indoor back-wall veil a smooth falloff (the same per-tile alphas, interpolated bilinearly across tiles). Set for catacombs `[1, .75, .42, .18]` (open space 0.28 -> 0.18) and cathedral `[1, .8, .5, .28]` (smoothing only). All other biomes take the old code path, unchanged |
| `.gitignore` | ignores `art/bg_src/*/*_pass1.png`, `*_render.png`, `v1/` (the raw renders are ~8 MB for the two biomes). The build needs `*_render.png` locally; without them run `--render` (ComfyUI) |

`GFX_SUN` is unchanged. The cathedral source (uv x 0.38, above the view) lands on the new rose window (far x=150) at camera start.
I tried making it follow the painted rose (`{x:150, y:20, w:512}`), but that puts the source inside the view and blows out K3s
around the player, so it was reverted. Catacombs has no `GFX_SUN` entry and gets none.

## Why the veil change
With a backdrop bright enough to read under the indoor ambient (x0.39 for both biomes), the stepped back-wall veil
(1 / .8 / .5 / .28 per 16 px tile) showed as hard boxes around the bright focal (C10 first pass). Smoothing the alpha removed the
boxes without dimming anything. In catacombs the 0.28 skull-tile veil also doubled up with the painted skull walls, so its open-space
alpha went to 0.18. To roll back, delete the `veil` keys. To extend the fix, add the key to other indoor biomes (it also softens the 16 px
wall-to-sky staircase, audit cross-cutting item 4).

## Method as built
1. **Guide (`guide_far`/`guide_mid`)**: a tileable 3x (1536x648) value and colour sketch painted in numpy/PIL. Every shape is drawn at
   x-512, x and x+512, so the wrap is seamless by construction. The far layer has one unique 512 composition with no repeat period.
   The focal point sits at x≈150–240, because rooms only ever show far-layer x≈0..420 (factor 0.08, `cam.x` is room-local). A wider
   far layer would not be seen, so the layers stay 512 wide. Taller layers expose the tint at the bottom as the camera descends
   (`oy + H - f.h`), so they stay 216 tall.
   The mid guide has real masonry values (blocks, mortar, lit faces, voussoirs). On flat dark silhouettes the model added nothing,
   so the guide is rendered bright and graded dark afterwards.
2. **Render**: SDXL base + `pixel-art-xl` **at 0.6** + Lightning 8-step, cfg 1, euler/sgm_uniform. img2img over the guide (blurred
   1.0–1.5 px) with ControlNet Union `canny/lineart` from the guide's edges, strength 0.45–0.5, ending at 0.6–0.7.
   - pixel-art-xl at 1.0 paints ~8 px blocks at 3x, which is ~2.7 game px per art pixel and too chunky. At 0.35–0.6 the
     downscale keeps 1–2 px detail. 0.6 kept the pixel-art read.
   - The IP-Adapter ramparts style reference (weight 0.35, "style transfer") was tested on catacombs. It only pulled the image
     toward purple-gold and added nothing to the rendering, so it was not used.
   - Seeds were swept (4–8 per layer) and picked by eye. Seeds whose distant door or window grew a standing figure were rejected,
     because it reads as an enemy.
3. **Seam**: roll by half, regenerate a feathered centre band (±128 px far, ±96 px mid at 1x) with `SetLatentNoiseMask` at denoise
   0.5 (ControlNet tile 0.6), keep everything outside the band, roll back. The far seams are invisible (`raw/seam_crops_x3.png`).
4. **Post (`far_post`, hi-res)**: catacombs pools light around the arch and darkens the roof and floor. Cathedral **builds the water
   in post**: every seed ignored the guide's flood, so below the water line it adds a rippled, darkened, blue-shifted mirror of the
   nave plus a lit edge.
5. **Pixel scale + palette**: BOX down to 512x216, then a nearest-in-Lab lock to the v1 ramps **extended upward in the same hue
   family** (v1 catacombs topped out at #382c2e) plus ≤ 4–8 accents from k-means. Bayer 4x4 dither is used only on flat gradients
   between close ramp neighbours (house style; `dk` 0.55 catacombs, 0.35 cathedral). A 3x3 majority filter removes orphans.
6. **Mid**: same render, keyed with the guide's own coverage (BOX down, threshold 0.5 = binary alpha), graded darker and less
   saturated than the far layer, palette-locked to the silhouette ramps, with a 1 px rim on sky-facing edges.
7. **Build + check**: `asebuild.build` (asserts the size, the tag and 1 frame), the parallax-only `preview.png`, and in-game
   snapshots with shaders on (`tools/shots/v17/bgpilot/snap.js`, run through `tools/shots/shot.js`). The build is deterministic:
   rerunning `gen_bg_*_v2.py` reproduces the shipped assets pixel-identically from the saved renders.

Commands: `python3 art/gen_bg_<biome>_v2.py` (build), `--guide` (guides only), `--render` (guides + ComfyUI + build), `--no-ase`.

## Prompts and parameters (as in the scripts' `RENDER` dicts)
- **catacombs far** (seed 2, denoise 0.8, cn 0.45→0.6, pix 0.6): *pixel art, dark fantasy, vast underground ossuary catacomb, walls
  built of stacked human skulls and bones in rows, a great pointed stone arch opening onto a receding vaulted crypt corridor,
  distant small chapel lit by a shaft of golden light, gnarled dark tree roots hanging from the vault ceiling, dust in the air,
  side-scroller game background, muted warm brown and umber palette with teal accents, atmospheric depth, haze, highly detailed*
- **catacombs mid** (seed 1, denoise 0.6, cn 0.5→0.7): *ruined crypt stone arches and broken pillars, weathered masonry blocks, thick
  gnarled tree roots draped over the arches, rubble and skulls at the base, isolated on a flat dark background…*
- **cathedral far** (seed 3, denoise 0.78, cn 0.45→0.6): *interior of a vast flooded gothic cathedral at night, a great rose window
  with muted stained glass above three tall lancet windows, cold pale moonlight streaming in shafts, clustered stone piers and
  ribbed vaults, a shattered lancet window, still black water covering the nave floor with reflections, broken pews half sunk…
  muted desaturated slate blue palette with faint gold…*
- **cathedral mid** (seed 1, denoise 0.72, cn 0.5→0.7): *gothic cathedral nave arcade, pointed stone arches on clustered pillars with
  carved capitals, hanging bronze censers on long chains, broken wooden pews in water, isolated on a flat dark background…*
- The negative prompt is ignored at cfg 1. Steering comes from the guide and the prompt only. In the first sweep, the skull niches
  drawn as shelves rendered as a library, so the guide moved to packed skull rows between long-bone courses.

## Metrics (v1 → v2; `art/bg_src/<biome>/stats.json`, audit definitions)
| Layer | colours | mean lum | near-black | repeat | seam |
|---|---|---|---|---|---|
| catacombs far | 22 → 25 | 18.7 → 57.0 | 0.77 → 0.06 | → 0.49 | 0.49 → 1.27 |
| catacombs mid | → 10 | → 29.2 | | → 0.23 | → 3.69 (alpha edge: an arch lands on the wrap pier; visually clean) |
| cathedral far | 17 → 26 | 38.8 → 60.5 | 0.12 → 0.02 | 1.00 → 0.59 | 0.43 → 0.96 |
| cathedral mid | → 14 | → 27.6 | | → 0.69 (pier rhythm, but no two bays alike) | → 1.03 |

## Time
Measured as agent wall time, with the pipeline written during the catacombs pass:
- **catacombs**: about 30 min. About 44 ComfyUI images ≈ 5.5 min of machine time (7–8 s per 1536x648 image warm, about 15 s per
  seamless layer). Three in-game loops: values, veil boxes, glow size.
- **cathedral**: about 10 min. About 18 images ≈ 2.3 min. Two in-game loops: dither and water, then the `GFX_SUN` test.

With the library in place, a further biome is mostly guide painting plus 1–2 in-game loops. The audit's estimate of 1.5–2.5 h per
biome with a human picking at each stage still looks right for a person; the machine time is negligible.

## Issues and caveats (honest list)
- **Pixel density**: the result is a little softer and chunkier (2–3 px forms) than the hand-built ramparts layer, which is
  1 px-crisp. It reads as painterly pixel art at the game scale, but it is not as clean as ramparts. Lowering pixel-art-xl further
  gives finer but more "AI-painterly" detail.
- **Catacombs far**: the ceiling roots render as looping arcs rather than hanging roots (a guide artefact the model kept), and the
  bottom ~30 px is a plain dark floor band (usually under the play floor). The skull rows read as skulls at 2x; at 1x some read as
  shelves of jars.
- **Cathedral far**: the light dither around the rose window is still visible, and there are small olive/gold smudges on some piers
  (the model's "gilding"). The mid arcade is clean but plain. K3s is the hottest case: the rose halo sits left of the player. The
  player still reads (dark silhouette on light), but if it feels too bright, lower `white`/`gamma` in the cathedral far grade.
- **Model behaviour**: SDXL ignores water and figure-free instructions at cfg 1, so expect to add water and reflections in post and
  to reject seeds with figures. ControlNet keeps the guide's structure faithfully, so composition mistakes must be fixed in the guide.
- The shots, `snap.js` and the montage live under `tools/shots/v17/bgpilot/`, which the existing `.gitignore` excludes (as it
  does for the audit). The test bundle is `web/dist/bgpilot.html` (also ignored).

## Deliverables
- `tools/shots/v17/bgpilot/before_after.png`: C8, C10, K7, K3s before/after (in game, shaders on). Single shots are in
  `before/`, `after/` (plus C3 and K1).
- `tools/shots/v17/bgpilot/raw/`: `<biome>_{far,mid}_{v1,v2}.png` and `seam_crops_x3.png`.
- `art/bg_src/<biome>/preview.png` (parallax-only composites at 3 camera x), `guide_preview.png`, `guide_*.png`, renders.
