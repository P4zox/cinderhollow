# v15 visuals: run lean, shaders and dynamic lighting

Role `visuals`. Files: `art/gen_player.py` (pose lean + run), `web/src/40_gfx.js` (post pass), `web/src/41_light.js`
(lighting pass). Tests and images live in `tools/shots/v15/visuals/`.

## 1. The knight leans forward when he runs

- `pose()` has a new `lean` parameter: how many px the shoulders sit ahead of the hips. It defaults to 0, so every other
  tag is unchanged. The torso row-shears about the belt (OY+19), so the hips and tassets stay put and the chest tips
  forward. The pauldron, head, cape anchor and both shoulder joints move rigidly with the row they sit on: shoulders +2,
  pauldron +2, head +3 at lean 2. That keeps the helmet and pauldron stamps clean instead of sheared.
- `run()` uses `RUN_LEAN = 2`. The feet, stride, timing (8 x 45 ms), `leg=5.7` and plant-and-push cycle are untouched,
  so the backward half still has no foot lift.
- Weapon grip: the hand stays where it was, so every weapon cel is drawn exactly as before and the arm IK simply reaches
  from the forward shoulder. The slung shield and the resting twin blade (`w.bxy` extras) ride the lean by
  `lk * 2.5` px (1 px). I checked every overlay: the 9 v14 kinds (`run_before.png` / `run_after.png`), the 5 v15 kinds
  (`run_after_v15kinds.png`) and the game itself (`run_lean_ingame.png`: 9 weapons x 4 frames running right in R2).
  `run_lean_0_vs_2.png` shows lean 0 and lean 2 side by side.
- Built with `tools/shots/v14/artbuild.sh`, which locks against other agents' builds. That changed `assets/player.png`,
  `wpn_knight_shield.png` and `wpn_twinfangs.png` (the extras), plus their `.aseprite` files. The build also refreshed a
  few `sc_*` hit boxes in `assets/player_meta.json`. Those came from the lead's scythe changes in b13c7f3, not from
  the lean.
- If the lean should be stronger or weaker, change `RUN_LEAN`: 3 is clearly athletic, 1 is barely visible.

## 2. Shaders and dynamic lighting

All of this sits behind Settings › Graphics. Shaders stay **off by default** (the owner's earlier decision). Once a
player turns shaders on, the new options below are on by default.

| What | Where | Setting (default) |
|---|---|---|
| **Soft shadows**: the lights sphere-trace a per-room signed distance field of the walls. Each light is a disc (radius ~4.5% of its reach), so a penumbra is sharp where a shadow starts and widens as it falls away. Light still sinks into a wall from its surface. The penumbra keeps the 5 pixel-art bands and the Bayer dither. | `41_light.js`: `lxSdf` and `lxEdt` (exact Felzenszwalb EDT at 4 texels per tile, ±127 px in a byte) and the `SOFT` branch of `LX_FS` | Lighting: Classic / Dynamic / Hard shadows / **Soft shadows**. Saves on hard shadows move up once (`lxv` 1). |
| **Rim light**: a pseudo-normal from the art's own luminance (bright reads as raised). An edge facing a light catches it and the far edge falls off. Walls get half. The knight's own fill light is excluded, because it sits inside him and would darken his outline. | `LX_FS` (`nrm`, `RIM`, `PL`) | Rim light: **On** |
| **Light shafts**: a screen-space radial blur toward up to 3 sources: the sun or moon of an outdoor biome, the cathedral's moonlit windows, and the strongest big lamps in view. The ramparts and dunes suns follow the sun painted in their far parallax layer. Sources fade in and out, so they never pop. With shafts on, the lit-air haze is a bit thicker and slow dust drifts through it (volumetric light, already shadowed per light). | `40_gfx.js`: `GFX_RAY`, `GFX_SUN`, `gfxRaySources`; `LX_FS` `fogm` | Light shafts: Off / **Soft** / Strong |
| **Better bloom**: a soft-knee bright pass at half resolution, a separable 9-tap gaussian at 1/2 and 1/4 resolution, and 2 bilinear taps in the full-resolution shader. This replaces the 12-tap ring that ran at full output resolution. | `GFX_BP`, `GFX_BLR`, `gfxChainInit`, `gfxPass` | Bloom Off / Low / High (unchanged) |
| **Region mood**: each biome gets a split-tone (shadow and highlight tints), saturation and contrast about a low pivot. It blends over about 0.5 s on a region change and sits under the chosen colour grade. | `GFX_MOOD`, `gfxMood`, post shader | Region mood: **On** |

- The Graphics list now has 17 rows, so it scrolls: 13 rows show at a time, with ▲ / ▼ markers
  (`shots/menu_gfx_*.png`). The presets are unchanged and don't include the new keys, so "Cinematic" etc. still match.
- **Fallbacks:**
  - No WebGL, or the context is lost: the plain blit with classic lighting, no errors (`nogl.js`; `lx/robust.js` context
    loss).
  - The bloom/shaft framebuffers fail: `GFX.chain = false` falls back to the old single-pass ring bloom with no shafts.
  - The lighting program fails to compile: `LX.bad` falls back to classic lighting, as before.
  - Touch devices: 16 lights and 10 soft-shadow steps (desktop: 48 and 20).
  - Uniform budget: `NL` now reserves 28 vectors, so a minimal 64-vector GPU still links.
- Test probe: `GFX.sync` now reads one pixel back (`gfxSync`) instead of calling `gl.finish()`. Chrome's finish returned
  early, so the old probe mostly timed command submission.

## 3. Before / after

`tools/shots/v15/visuals/compare_1.png` (R1 ramparts dusk, C2 catacombs, K1 cathedral, X1 crown, D3 and D2 the Deep,
HF6 hoarfrost) and `compare_2.png` (DU1 dunes, NV2 necropolis, TV2 thornveil, SF2 starfall, NH2 neohallow, A2 archives).
Each room is shot at the same camera spot and settings (shaders on, Cinematic look, the darkest lighting option of each
build). The raw shots are in `shots/before_<room>.png` and `shots/after_<room>.png`. Per-feature A/B on one frozen
frame: `ab.js`, which renders `G.step(0)` so only the setting changes.

What changes, honestly:
- **Most visible:** the ramparts sunset now throws shafts through the battlements and the dead tree. The cathedral
  windows let moonlight fall diagonally across the nave. Lamps bleed a little light past silhouettes. Lava rooms read
  warmer and deeper.
- **Subtle by design:** soft shadows, rim light and region mood. They show most near a lamp, and not much in rooms with
  only 2 or 3 lights (NV2, TV2).

## 4. Performance

Numbers are present-pass ms per frame with GL sync, measured in one page with the old and new pipelines interleaved in
batches. Other agents share the machine, so separate runs were too noisy. Scripts: `abperf.js` and `massab.js`.

| 1920x1080 | old pipeline | v15 defaults |
|---|---|---|
| Apple M5 Pro (Metal), 6 rooms: GL cost over shaders-off | 1.07 to 1.90 ms | 0.83 to 1.43 ms |
| Busy room (TR2, ~37 foes; `tr/mass_spawn.js` setup), M5 Pro: present | 3.94 ms | 3.32 ms (hard shadows 3.38, shafts off 3.43) |
| SwiftShader (software GL, a weak-GPU proxy), 6 rooms: GL cost | 51 to 61 ms | 28 to 39 ms |
| SwiftShader busy room: present (shaders off: 37.6) | 95.9 ms | 65.8 ms |

- The full-resolution shader dropped from 13+ texture taps to about 4. That pays for the soft shadows, the shafts and
  everything else, with room to spare.
- Room bake (AO + occluders + SDF), paid on room entry and when a breakable wall opens:
  - E5 (the biggest real room): 5.5 → 7.2 ms
  - R5: 2.7 → 4.7 ms
  - C2: 1.1 → 1.9 ms
  - T1 (100x100 test room): 13.5 ms
- `matrix.js`: 288 Lighting / shafts / bloom / rim / mood / bands combinations x 2 rooms all render with no GL error and
  no fallback.

## Decisions for the owner

1. Shaders stay **off by default**. These upgrades only show once a player turns shaders on. Turning shaders on by
   default is now cheaper than it used to be, if you want that.
2. Light shafts default to **Soft**. Strong is the more dramatic look (sunset rays). Say if you want Strong as the
   default.
3. `RUN_LEAN = 2` (head 3 px ahead of the hips). One number to change.
4. ComfyUI wasn't needed: everything is procedural.

## Re-running

- `tools/shots/v15/visuals/run.sh web/dist/v15_visuals.html after shots`: the room shots.
  `run.sh <before.html> before shots` makes the other half; then `python3 cmp.py before after out.png [rooms]`.
- `SHOT_HTML=<html> VIEW=1920x1080 node tools/shots/v15/visuals/shotx.js tools/shots/v15/visuals/abperf.js out`: A/B
  perf. Add `EXTRA_ARGS="--use-angle=swiftshader --enable-unsafe-swiftshader"` for the weak-GPU proxy (slow).
- `shotx.js` is a copy of `tools/shots/shot.js` with `VIEW` and `EXTRA_ARGS`. Other scripts: `dbg.js` (light-only /
  SDF / normal debug views, `LX.dbg` 3 / 7 / 8), `shadow.js`, `menu.js`, `matrix.js`, `nogl.js`, `bake.js`,
  `runlean.js`, and `leanview.py` (lean preview without a build).
