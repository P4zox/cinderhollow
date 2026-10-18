# Shading cleanup, phase 1

Branch `shading` (from `main` at daec1c7). The owner said the in-game shading "is weird" and "things get too bright".
This pass changes the dynamic-lighting pass (`web/src/41_light.js`), the post pass (`web/src/40_gfx.js`), classic lighting
(`03_world.js`), the knight's fill light (`09_main.js`, plus the bench-vista copy in `43_systems.js`), the hit flash
(`00_core.js`), Deep lava (`23_deep.js`) and the forge ambient (`82_forge.js`).

## What was wrong

- **Shoulders everywhere, no tone map.** The lighting pass soft-clipped the light (KNEE/TOP), capped it per pixel, then
  rolled off highlights per channel at 0.75. The post pass then added bloom and light shafts, applied mood and grade, and
  rolled off per channel again at 0.72. These per-channel shoulders turned every hot area cream (lit stone, snow, lit
  fog, a lit hit flash) and squeezed it into a flat band. Bloom and shafts were added after the shoulders with no limit,
  so High bloom plus Strong shafts washed whole areas out (see the Pale Crown in the stress montage).
- **The knight's fill light** (r 100, k 0.9, so about 1.5× peak after gain) was the brightest light in most rooms. It made
  a lit disc around him with a visible linear-falloff edge, and on pale backgrounds (the Threshold fog, the Crown) a big
  dithered halo.
- **Light bands:** each light was cut into 5 steps, and every step edge got a 4×4 Bayer checker. Several lights
  overlapping gave dotted rings across the walls. AO was quantized with the same Bayer pattern.
- **Blocky shading:** AO was baked per 16 px tile from the tile neighbours. The shadow SDF was built from square tiles,
  and Hard shadows marched the 1-texel-per-tile occupancy map. The result was stair-stepped squares.
- **Rim light:** this was a pseudo-normal from albedo luminance, so painted detail read as bumps. In the catacombs it
  made a bright crescent of fake relief next to torches.
- **Haze was dead.** A v15 edit put `if (lp.z > 24.0) Lh += c;` behind a `//` comment on the same line, so the haze and
  the drifting dust it carries have been off since v15.
- **Hit flash × light:** the flash tint was drawn into the albedo and then multiplied by the light. A 0.55 white flash
  under a strong lamp became a flat cream shape (`hk_flash55`).
- **Lava in the Deep** was drawn into the lit layer, so the orange lava lights multiplied it to a deep red.

## What changed

### 1. One tone curve (`GFX_TM` in 40_gfx.js, used by both passes)
- `tmap()` works on the brightest channel and scales the other two by the same ratio, so hue is kept and nothing turns
  cream. It is linear up to the knee `GFX_TONE.k = 0.6` and uses a Reinhard shoulder from there toward 1.0, which it
  never reaches, so lit stone can't clip. A small toe (`t = 0.004`) deepens the last few % of black. `tmapInv()` is its
  exact inverse.
- Lighting pass: everything is computed in scene light: `albedo × (ambient × AO + banded lights) + haze`, times the
  scene exposure (`LX_TUNE.expo 1.2 × LX_EXPO[Brightness]`), then `tmap` is applied once. Only the very hottest light
  (scene > 0.7, full at 4) drifts up to 40 % toward white (`desat`), so coloured lamps on stone don't go neon. Bright art
  (lava, runes, eyes, sky; max channel > 0.84) is mixed back to its painted colour (`emi` 0.65 → 0.85). Emitters
  (`lowFx`) and overlays (`lowTop`) go on top in display space, as painted.
- Post pass: the frame is lifted back to scene light with `tmapInv`, bloom and shafts are added there, and `tmap` maps
  it again. A frame with nothing added comes back unchanged, and glow piles up into the shoulder instead of clipping.
  Bloom and shafts share a soft cap: `add / (1 + max(add)/0.45)`, so together they add at most 0.45. Strengths are
  `GFX_TONE.bloom [0, .3, .45]` and `rays [0, .7, 1.05]`. The two old per-channel shoulders are gone. Mood and grade run
  after the curve. Lit stone leaves the curve at ≤ ~0.93, so only painted emitters can reach 1. The vignette is a little
  lighter (0.42 → 0.32), because the in-world 2D vignette already darkens the corners.
- Light colours are less saturated (`LX_TUNE.sat` 0.85 → 0.68). The old per-channel shoulder used to hide the hue
  squaring (orange light on orange stone); the hue-keeping curve shows it.
- Light gain is 2.0 → 1.7. Dark stone takes at most 2.2× light (`lmax`, a soft cap, so there are no flat plateaus).
  Bright or saturated art takes about 1.3×.
- Haze: the dead line is fixed and haze is capped (`hcap`), but haze ships at 0 (`haze`, `hazeRays`). When it was on,
  every lamp drew a round "light in the air" disc (archives, Last Field, dunes), which looked worse.
- **Hit flashes** (light tints, luminance ≥ 0.45: white, cream, gold): under Dynamic lighting the sprite is drawn lit and
  the flash tint goes over it in the overlay layer (`lxFlashSplit` / `lxFlashOver`). The result is
  `lit sprite × (1 − f) + colour × f`, the same as an unlit frame, whatever the light. Dark tints (the Hearthkeeper's
  "gone dark", ghosts) stay in the lit layer.
- **Deep lava** is drawn through `drawGlow` (an emitter) and shows as painted.

### 2. Light bands: Stepped (new default), Smooth, Dithered
- The summed light (not each lamp) is cut into `steps = 6` levels, evenly spaced in sqrt (perceptual) space up to
  `bmax = 2.6`. Each step edge is a short smooth ramp: `bsoft = 0.25` of a step, and at least ~1 px via `fwidth`. There
  is no dither. Below the first step the light fades smoothly, so a lamp has no hard outer ring.
- The light falloff is now windowed, `(1 − x²)^1.5` instead of linear: it has no slope at the radius, so there is no
  visible disc edge.
- Settings › Light bands: `Stepped` (slot 0, so old "Pixel" saves move over by themselves), `Smooth`, `Dithered` (the old
  Bayer look, for anyone who wants it back).
- AO is no longer Bayer-quantized.
- Migration `lxv 2` (41_light.js): Light bands goes to Stepped unless the player chose Smooth, and Rim light goes off once.

### 3. Shadows and AO without tile squares
- The SDF (4 texels per tile) gets a separable gaussian blur (σ ≈ 6 px) before it is quantized. Straight walls stay where
  they are, and every corner rounds by about 6 px, inside and outside.
- AO gets the same blur, over open air only (walls keep 255 and don't bleed into the contact shade). Strength is 0.42 →
  0.5 to make up for the blur.
- Hard shadows are now the soft-shadow sphere-trace with a small light (`hard = 0.3`), so they use the rounded SDF too.
  The occupancy-texture march is gone. The penumbra is a little wider: the light size is `0.05 × r` (it was 0.045),
  clamped to 2-12 px.
- The march jitter (Bayer) is gone.
- Cost: the room bake on entry is about 60 % slower (SF11, 544×192 texels: 12 → 21 ms; C8: 6 → 11 ms). Frame time is
  unchanged: present 1.75-4.0 ms in both builds.

### 4. Rim light: default Off, rebuilt as edges only
The luminance pseudo-normal is gone. `Rim light: On` now lights only the lip of the terrain: the outer ~1-6 px of a wall,
using the SDF gradient as the normal, where that edge faces a light. **It ships Off.** The tile art already paints a lit
lip on every ledge, so in captures (`after_rim/`, not kept) the edge rim was nearly invisible and cost 4 extra SDF taps per
pixel. The old luminance rim was what made the fake bumps. Sprites can't get a true silhouette rim without a sprite mask
layer, which would be a phase-2 job.

### 5. The knight's fill light
- Light: `addLight(P.x, P.y − 12, 60, '255,188,140', 0.42)` (was r 100, k 0.9, '255,210,170', y − 16). It is smaller,
  warmer, lower and dimmer.
- In the lighting pass it is a "soft fill": strength < 0 in `LP` marks it. Soft fills get their own smooth accumulator:
  the falloff is applied twice (a² ≈ (1 − x²)³), they are not banded, and they get no rim or haze. Pale art takes only
  `min(1, 1.4·(1 − albedo luminance)²)` of them: the knight's dark plate takes all of it, Threshold fog about 22 %, so
  there is no halo. The old `PL` uniform is gone.
- It scales with the region's darkness (`AREAS[b].ambient`): full from 0.45, none at 0.25 or less (Crown, Dunes, Last
  Field, Training), a trace at the Threshold (0.3), and ×1.6 while a boss has snuffed the lamps (`darkT`).
- Review follow-up: the white glow behind the knight's helmet in the Threshold (CT2) was not this light. It was the
  "unread lore page" marker (43_systems.js, r 28, k 0.55-0.7). The page sits on the spawn spot, and the marker's banded
  disc showed against the pale fog. The proof is in `before_after_fill_zoom.png`: with the fill off (`s_threshold_nofill`)
  the halo stays, and with the page read (`s_threshold_read`) it is gone. The marker now passes `LX_SOFT` and is drawn as a
  soft fill: no band rings, and only a trace on pale art. It still glows on dark stone, with its gold motes. Checked with
  no halo: Crown snow (X10), Dunes sand (DU1), Last Field (LF1) and the Pale Crown vista (X11), standing and seated, and CT2
  (`before_after_fill_bright.png`).
- Classic: the darkness hole for the knight is r × 1.2, k × 1.65, with a soft mid stop, so there is no disc edge. The warm
  glow uses `screen` instead of `lighter`, so it can't push a wall to flat white. The bench vista's copy of the fill
  (43_systems.js) matches.

### 6. Exposure calibration
The darkest regions sat at a mean luminance of 8-15/255. `LX_BOOST` (ambient lift per region) was raised:
catacombs 1.25 → 1.65, crimson 1.3 → 2.0, ember 1.3 → 1.55, thornveil 1.35 → 1.6, spire 1.1 → 1.45, starfall 1.1 → 1.5,
cathedral 1.1 → 1.15, and forge 1.45 → 2.0 (in 82_forge.js). New entries are deep 1.25, archives 1.3, neohallow 1.4,
hermit 1.15 and ramparts 1.1. A lot of the darkness is in the art itself (crimson walls, starfall sky), so those rooms
stay moody, around 12/255, but readable.

### Defaults after the change
- `LX_DEFAULTS = { light: 3 (Soft shadows), lband: 0 (Stepped), rim: 0 }`.
- `GFX_DEFAULTS` are unchanged (shaders on on desktop via `gfxV15`, bloom Low, shafts Soft, mood On, vignette On, grade
  Natural).
- The presets are unchanged, and all of them were re-checked: High bloom + Strong shafts + Bright is the stress set and
  no longer washes out.
- Brightness: Dark / Normal / Bright scales the ambient by `LX_BRIGHT [0.8, 1, 1.25]` and the whole lit scene by
  `LX_EXPO [0.88, 1, 1.12]`, before the curve, so Bright never clips. Without the lighting pass (Classic, or shaders
  off) the post pass exposes by `GFX_TONE.expo [0.86, 1, 1.12]` through the same curve. Measured monotonic: catacombs
  mean 18.8 / 25.4 / 33.6.

## Measurements
World-only captures (no HUD), 1152×648. Every shot is re-seeded (`Math.random`) and `time` is reset, so the before and
after captures are the same frame. The before build is `main` (daec1c7) at default settings. Columns: mean, p95,
**% of pixels with luminance ≥ 245**, and **% "cream"**: luminance ≥ 170 with chroma < 18 % of max, which measures the
washed-out flats.

Note: in plain default captures neither build reaches 245. The old double shoulder had an asymptote below 1. The old
problem shows instead as highlights crushed into a narrow cream band: the p95 drops at the Threshold, Dunes, Last Field
and Archives, and the cream % at the Threshold (8.1 → 0.8), Barrows (1.0 → 0.0), Crown (12.8 → 6.1) and the flash test
(0.44 → 0.21). The pixels at ≥ 245 after the change (≤ 0.2 %) are painted emitters only: sparks, slash fx and the
Crown's white sky art.

| shot | mean before | mean after | p95 before | p95 after | % ≥245 before | % ≥245 after | % cream before | % cream after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| d_catacombs | 21.1 | 25.3 | 86.8 | 91.3 | 0.00 | 0.02 | 0.09 | 0.02 |
| d_crimson | 8.5 | 11.3 | 31.5 | 43.8 | 0.00 | 0.00 | 0.03 | 0.01 |
| d_hermit | 24.9 | 21.6 | 101.4 | 64.9 | 0.00 | 0.00 | 0.03 | 0.00 |
| d_lightsout | 5.4 | 1.2 | 37.0 | 5.4 | 0.00 | 0.00 | 0.03 | 0.00 |
| h_deep | 8.8 | 10.4 | 31.3 | 35.4 | 0.00 | 0.00 | 0.04 | 0.00 |
| h_ember | 9.8 | 12.0 | 33.4 | 40.0 | 0.00 | 0.00 | 0.03 | 0.00 |
| h_flue | 13.4 | 20.5 | 37.6 | 45.6 | 0.00 | 0.00 | 0.12 | 0.08 |
| h_forge_hearth | 16.6 | 22.8 | 52.2 | 66.1 | 0.00 | 0.00 | 0.15 | 0.16 |
| h_neon | 9.4 | 11.9 | 36.6 | 43.3 | 0.00 | 0.00 | 0.31 | 0.03 |
| hk_flash55 | 10.4 | 14.6 | 31.3 | 35.7 | 0.00 | 0.00 | 0.44 | 0.20 |
| hk_flash55_screen | 29.4 | 33.9 | 51.4 | 53.9 | 0.00 | 0.00 | 0.46 | 0.34 |
| hk_p1_flash0 | 21.3 | 27.3 | 81.6 | 82.7 | 0.00 | 0.11 | 0.48 | 0.33 |
| hk_p1_flash1 | 20.3 | 26.4 | 80.5 | 80.4 | 0.00 | 0.07 | 0.32 | 0.20 |
| hk_p1_flash2 | 19.5 | 25.6 | 76.2 | 78.4 | 0.00 | 0.04 | 0.33 | 0.27 |
| hk_p3_flash | 14.0 | 11.5 | 74.3 | 60.1 | 0.00 | 0.00 | 0.30 | 0.07 |
| r_archives | 17.8 | 20.8 | 72.0 | 60.6 | 0.00 | 0.00 | 0.02 | 0.00 |
| r_barrows | 35.3 | 34.9 | 161.3 | 155.8 | 0.00 | 0.00 | 1.03 | 0.02 |
| r_catacombs | 14.6 | 19.0 | 52.5 | 50.0 | 0.00 | 0.00 | 0.03 | 0.01 |
| r_cathedral | 24.3 | 25.8 | 70.0 | 76.6 | 0.00 | 0.00 | 0.22 | 0.05 |
| r_crimson | 8.6 | 12.8 | 38.6 | 53.6 | 0.00 | 0.00 | 0.03 | 0.00 |
| r_crown | 80.5 | 87.0 | 211.0 | 205.3 | 0.00 | 0.11 | 12.77 | 6.06 |
| r_deep | 20.1 | 21.8 | 86.0 | 87.8 | 0.00 | 0.00 | 0.02 | 0.00 |
| r_dunes | 40.0 | 38.5 | 132.7 | 110.7 | 0.00 | 0.00 | 0.02 | 0.00 |
| r_ember | 14.4 | 17.4 | 47.6 | 55.3 | 0.00 | 0.00 | 0.04 | 0.00 |
| r_forge | 9.5 | 15.1 | 32.8 | 41.4 | 0.00 | 0.00 | 0.08 | 0.01 |
| r_hermit | 19.5 | 21.6 | 66.4 | 61.9 | 0.00 | 0.00 | 0.03 | 0.00 |
| r_hoarfrost | 28.6 | 31.4 | 114.8 | 127.0 | 0.00 | 0.00 | 0.74 | 0.52 |
| r_lastfield | 73.8 | 74.9 | 182.0 | 160.2 | 0.00 | 0.00 | 0.03 | 0.02 |
| r_mire | 37.2 | 38.7 | 135.8 | 135.1 | 0.00 | 0.00 | 0.09 | 0.00 |
| r_necropolis | 25.8 | 25.0 | 81.6 | 73.9 | 0.00 | 0.00 | 1.06 | 0.67 |
| r_neohallow | 8.7 | 12.3 | 35.7 | 49.3 | 0.00 | 0.00 | 0.07 | 0.00 |
| r_ramparts | 24.3 | 23.1 | 79.5 | 68.5 | 0.00 | 0.00 | 0.05 | 0.00 |
| r_spire | 15.6 | 19.3 | 53.5 | 60.5 | 0.00 | 0.00 | 0.13 | 0.07 |
| r_starfall | 9.1 | 12.4 | 30.2 | 46.3 | 0.00 | 0.00 | 0.56 | 0.14 |
| r_thornveil | 16.7 | 20.3 | 50.6 | 56.3 | 0.00 | 0.00 | 0.12 | 0.00 |
| r_threshold | 74.0 | 73.8 | 190.8 | 130.4 | 0.00 | 0.00 | 8.10 | 0.23 |
| r_training | 179.0 | 186.7 | 218.9 | 230.9 | 0.00 | 0.00 | 66.05 | 67.96 |
| s_LF1 | 73.1 | 74.2 | 176.0 | 156.9 | 0.00 | 0.00 | 0.03 | 0.02 |
| s_X11 | 72.8 | 71.5 | 187.2 | 142.8 | 0.00 | 0.47 | 1.06 | 0.50 |
| s_crown_snow | 29.7 | 31.9 | 93.5 | 107.4 | 0.00 | 0.06 | 0.70 | 0.37 |
| s_dunes_sand | 55.9 | 54.2 | 190.5 | 154.9 | 0.00 | 0.01 | 0.06 | 0.00 |
| s_threshold_nofill | 60.4 | 73.4 | 109.6 | 130.3 | 0.00 | 0.00 | 0.38 | 0.23 |
| s_threshold_read | 74.0 | 73.6 | 191.8 | 130.4 | 0.00 | 0.00 | 9.04 | 0.35 |
| v_DU15 | 54.1 | 52.2 | 150.2 | 141.0 | 0.00 | 0.00 | 0.00 | 0.00 |
| v_HF14 | 25.2 | 25.3 | 107.6 | 108.9 | 0.00 | 0.00 | 0.19 | 0.18 |
| v_K11 | 32.1 | 32.1 | 100.1 | 99.7 | 0.00 | 0.00 | 0.04 | 0.03 |
| v_LF1 | 69.8 | 70.3 | 163.3 | 160.5 | 0.00 | 0.00 | 0.00 | 0.00 |
| v_R11 | 36.7 | 35.8 | 121.4 | 117.0 | 0.00 | 0.00 | 0.01 | 0.01 |
| v_SP15 | 25.8 | 25.2 | 74.1 | 70.2 | 0.00 | 0.00 | 0.43 | 0.36 |
| v_X11 | 82.2 | 83.1 | 170.7 | 168.5 | 0.00 | 0.19 | 0.55 | 0.24 |

Other settings (stress = Bright + High bloom + Strong shafts, Classic, shaders off, Hard shadows, Dark and Bright) are
in `tools/shots/v17/shading/luminance.md`.

## Montages (tools/shots/v17/shading/, gitignored like every capture under tools/shots)
- `before_after_regions_{1,2,3}.png`: one room per region (22 regions).
- `before_after_vistas.png`: 5 seated bench vistas (R11, K11, HF14, SP15, DU15). These are nearly unchanged because the
  vista renders through classic lighting into the overlay layer. Only the post pass and the knight's fill changed for
  them.
- `before_after_dark.png`: dark rooms and lights-out (`darkT`) with the knight's light.
- `before_after_hot.png`: lava, ember, the forge hearth, the flue, neon.
- `before_after_boss.png` and `_boss_zoom.png`: the Hearthkeeper mid-flurry with hit flashes (phases 1 and 3), plus the
  0.55 white flash stress test (a hollow soldier under the arena light, with and without a 0.3 screen flash).
- `before_after_buffers.png`: AO (LX.dbg 2) and the light buffer (LX.dbg 3). Square AO and checker rings before; rounded
  AO and clean steps after.
- `before_after_bands_zoom.png`: native-pixel crops of the bands.
- `before_after_fill_zoom.png` and `before_after_fill_bright.png`: the knight's fill and the page marker on pale art
  (Threshold, Crown snow, Dunes sand, LF1, X11).
- `before_after_stress.png`, `_classic.png` (shaders off), `_brightness_dark.png`, `_brightness_bright.png`.

## Reproduce
```
BUILD_OUT=web/dist/shading_before.html python3 web/build_web.py   # on main
BUILD_OUT=web/dist/shading.html python3 web/build_web.py          # on shading
tools/shots/v17/shading/run_all.sh $PWD/web/dist/shading_before.html before
tools/shots/v17/shading/run_all.sh $PWD/web/dist/shading.html after
(cd tools/shots/v17/shading && ./montage.sh)                      # montages + luminance.md
```
- `shoot.sh <html> <out> [settings-json] [names…]` takes look knobs without a rebuild: `TUNE='{"bsoft":0.3}'` (LX_TUNE)
  and `TONE='{"k":0.55}'` (GFX_TONE).
- `stats.py <dir> [<dir2>]` prints the table.

## Regression tests (run one at a time, test build `web/dist/shading.html`)
- `tools/shots/wm/run.sh tools/shots/wm/mech.js`: 64/64, with the lead's test fix 09fc871 (the blade-guard check
  blocks 333 ms after the raise; the 67 ms perfect guard is checked separately).
- `tools/shots/v17/boss/run.sh tools/shots/v17/boss/flow.js`: full flow, no errors. Phases, temper, death/core, furnace,
  rekindle and rematch are all as in `flow_result.txt`, apart from frame-count jitter.
- `node tools/shots/shot.js tools/shots/v17/area/checks.js` (from tools/shots/): no errors, all pages and dialogue present.
- Settings matrix (Hard shadows, Rim On, Smooth, Dithered, Classic, shaders off): no console errors.

## Phase 2 candidates
- A true sprite rim: needs a sprite-mask layer (alpha of bodies) next to `low`.
- Lights on far parallax layers: a lamp lights the painted sky behind it as if it were a wall (the step rings around the
  Hermit's lamp sit on the sky). Lights could skip pixels that came from the parallax layers.
- Per-room exposure (an auto-exposure from the scene's average, smoothed over time) instead of per-region `LX_BOOST`.
- Other emissive tiles drawn into the lit layer, like the Deep lava was. Worth an audit of HOOKS.render tile painters.
