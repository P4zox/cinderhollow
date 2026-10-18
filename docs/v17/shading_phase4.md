# Shading, phase 4: reflections, lit particles, real light shafts, depth haze, effect light

Branch `shading4` (from `main` at ad34746, the phase-3 release). The owner approved five items, most important first:
reflections, lit particles, real light shafts, depth haze, and light from spells and effects. Everything sits on top of the
phase 1–3 pipeline (one tone curve, the Stepped bands, the rounded SDF, the runtime normals, the silhouette buffer). No asset
changed. Classic and shaders off are pixel-identical to main.

Files: `web/src/41c_atmos.js` (new: the reflection mask and pass, the lit-particle layer, shaft sources, haze table, effect lights),
`41_light.js` (shader: particles, shafts, lamp shafts, haze; roof mask in the SDF texture; settings), `41b_surf.js` (the silhouettes
can be on without Character shadows), `40_gfx.js` (Settings rows, which suns keep the screen-space shafts), `00_core.js` (one hook
line in `drawSprite`), `09_main.js` (silhouette flag), `22_spire.js` / `32_crimson.js` (rain goes to the lit layer), `53_sa.js` /
`82_forge.js` (painted shafts give way to real ones), `50_ra.js` (lancets remember their glass), and 23 effect-light call sites
tagged `LX_FXL` (05, 04, 07, 07b, 13, 14, 16, 76, 78, 84).

## 1. Reflections (Settings › Graphics › Reflections)

The reflections are computed in screen space from the frame that is already lit, so nothing is drawn twice.

- **The mask (`lowR`).** Each frame, `lx4Mask` scans the visible tiles and fills flat rects in a game-resolution canvas. R holds
  the strength, G the waterline's screen row (+40), and B the kind × 32 + tint. The kinds are:
  - **water**: `~` rot water, `"` deep water (the Barrows, the Cold Forge's cisterns CF5 / CF10, the Necropolis gate, kit water
    basins), and `:` freezing water. Only columns whose top has open air above them count; a sealed tunnel has no surface. A rect
    reaches at most 44 px below the line.
  - **ice**: the top 10 px of `_` ice floors.
  - **wet stone**: the top 6 px of every floor in the wet regions. These are the materials' wet regions: the Mire, the Barrows, and
    the Spire under its rain.
  - **puddles**: the Spire's puddles.
  - Water that moves gets its own exact line. The kit basins that fill and drain use their own line, not the grid's. The Barrows
    arena tide and the cathedral stair's black water (`RA.waters`) are added too.
- **The pass (`LX_RF`).** This is a second full-screen pass at 384×216, run only on frames that have reflective pixels on screen. It
  reads the lit frame at the mirrored pixel:
  - **water**: rippled and wobbling with the drawn surface. Rows shift in pairs by whole pixels, the shift grows with depth, and the
    wobble uses `drawWater`'s own wave. The reflection fades in 4 clean steps (pixel-art strips).
  - **ice**: sharp and faint.
  - **wet stone**: the floor is seen at a grazing angle, so 1 px of floor mirrors 6 px of height. Only what is bright reflects
    (lamps, flames, spells), so these show as very faint, short streaks under the lamps.
  - **puddles**: a squashed, slightly rippled mirror.
  - **Bodies reflect whole or not at all** (lead review fix). Each body's box is recorded with its silhouette (`LXO.boxes`), and
    `lx4BodyK` gives each body one strength from how high its lowest point stands above the first water, ice or floor under it:
    full within 24 px, none past 56 px. A body whose feet are already under the line *wades*; dark water hides the part below
    the line, so its mirror would float loose (the first cut showed the knight's cloak alone, mid-water, in CF10), and it gets
    none. Over bright water (the Mire's rot water) a wading body still reflects. The 16 bodies nearest the water go to the shader
    as boxes; the smallest box holding a mirrored pixel decides, so every pixel of a body gets the same strength and the depth
    steps no longer cut it into pieces. Body reflections reach 84 px below the line; the surroundings still fade over 44 px.
    Dark armour over dark water is kept a step (×1.35) above the water's own luminance, so the silhouette reads as itself.
    Bodies never show through the surroundings' lighten-only path, only whole.
  - Bodies (the silhouette buffer) and emitters (`lowFx`) reflect strongly (0.75). The lit world reflects faintly (0.4) and only
    lightens the water, so bright rot water keeps its glow. The painted backdrop reflects barely (0.12), so a painting's own
    baked reflection is not mirrored a second time.
  - Each water type adds a hint of its own colour, and lightning adds the sky's flash to every surface.
  - The overlays (`lowTop`) are laid on after the reflections, and the HUD after that, so neither is ever mirrored.
- The silhouette buffer now runs whenever reflections or shafts need it, even with Character shadows Off. In that case it draws
  no pools, and the old ellipses stay.

## 2. Lit particles (Settings › Graphics › Lit particles)

- **What moved.** Dust, ash, spores, snow (the `petal` ambient), steam, soot, foam, drops, leaves, sand and the ambient motes now
  go to their own layer, `lowP`. The exception is the Deep's ember motes, which stay emissive. The Spire's rain and the Crimson
  blood rain go there too (`lxAir`).
- **How they are lit.** The shader lights each particle with the lamps the way it lights the air:
  - the same SDF shadows, but no wall-depth fade and no normals;
  - the light passes through the Stepped bands, so it stays in clean steps;
  - plus a share of the knight's fill and of the shafts (`pShaft`), so dust sparkles inside a beam.
- **Result.** Near a torch the dust is warm; under the moon it is cool. Away from lights it falls to the region's ambient, where
  before it glowed evenly.
- **What stayed emissive.** Embers, sparks, fire, gold, cinders and spell motes are unchanged.
- **Lamp lights.** Ambient motes used to add a tiny light each, which made bokeh discs in the Archives and the cathedral. Lit, they
  add no light (K7: 37 lights → 7). Classic is unchanged.

## 3. Real light shafts (Settings › Graphics › Light shafts: Off / Soft / Strong)

All three kinds are computed per pixel in the lighting pass (`shafts()`), cut into 3 clean steps, modulated by the existing
drifting dust noise, and sprinkled with single-pixel dust motes that drift.

- **Sun and moon through openings.**
  - A pixel in roofed air marches the SDF toward the region's sun (`GFX_SUN`) for up to 300 px. Roofed means solid within 10
    tiles straight up; all of an indoor room counts. The roof mask is the alpha of the SDF texture, blurred like the SDF.
  - Holes in ceilings, cave mouths and gaps between merlons let in slanted shafts. The bodies cut them (`occSeg`: silhouette taps
    along the ray inside the bodies' box). See K7's left stairwell and K11's ceiling, where the knight cuts the beam.
  - Only a high sun or moon (elevation > 30°) makes these. A sun painted low on the far layer (dunes, ramparts) would light the
    corridors flat.
- **Beams.** Up to 4 per frame, nearest first, with an origin, direction, width, spread, length and colour:
  - the cathedral's lancets, in their glass colour (gold, rose, blue);
  - the forge's cold vents;
  - the painted shafts in the Barrows (`xsa shaft`), now real.
  - A beam whose opening is cut in rock starts where it leaves the rock.
  - Each pixel marches back to the opening, so pillars and bodies cut the beam.
  - The flat painted versions are not drawn while real shafts are on.
- **Lamp shafts (indoors).** Up to 3 strong lamps (r 56–140, k ≥ 0.45, shadow-casting) light the air they shine through:
  - the shadowed light, falling off fast and brighter where the ray grazes an edge;
  - this gives the cone under the catacomb's hanging lamps, cut by its niche.
  - A lit disc alone reads as fog, so the open part is held at 0.2.
  - These lamps no longer feed the screen-space lamp bleed, so there is no double.
- **What stays screen-space.** The sun or moon over an open sky, and any sun painted on screen (vistas, the far layer's), keep the
  old screen-space bleed past the silhouettes. A trial of real open-sky shafts (`LX4_TUNE.open` 0.3–0.45) lifted the whole
  outdoor scene and cut hard-edged wedges in SP8, R5 and SP3, so it ships at 0. Indoors, the cathedral's moon above the view no
  longer washes the screen; it comes in through its holes and windows.
- **Needs** Hard or Soft shadows. Without them, the old shafts run as before.

## 4. Depth haze (Settings › Graphics › Depth haze)

- **How much.** The far backdrop fades toward the region's air: 0.26 outdoors, 0.16 indoors, and 0.1 in halls whose far painting
  is the room's own back wall. The mid layer fades about half as much, and the play layer not at all. Standing in a vista
  room (`VISTA_BG`) the haze takes 0.45 of that (those paintings carry their own aerial perspective); seated on the bench, the vista
  renders through its own path and is unchanged.
- **The air colour.** It is the colour of the region's far painting, weighted toward its lit parts (the horizon and sky). It is lit
  by the region's ambient, so it follows Brightness.
- **Lifts only.** The haze never darkens: dark mid silhouettes pale with distance, and a lit sky never dims. An earlier cut faded
  toward the plain mean. It darkened the Last Field's sky by 7 and the dunes temple's window view by 5, and was dropped.
- **Tuning.** `LX4_HAZE[biome] = [far, mid, 'r,g,b']` overrides any of the three.

## 5. Spell and effect light

- **Auto lights.** Every effect sheet (`fx_*`, `wpn_fx_*`) drawn into the glow layer becomes one light (`lxFxHook` in
  `drawSprite`):
  - its colour is the mean of the sheet's bright pixels, worked out once per sheet;
  - its radius is 0.95 × the frame's size (22–170 px);
  - its strength is 0.6, fading as the effect plays, × alpha, and lower for telegraphs.
  - Dark effects (smoke, dust, blood, ink) cast none.
  - It is skipped when the effect already has a light of its own (an explicit `addLight` within 16 px, at least half the size), so
    each effect has one main light.
- **Shadows.** The lights cast shadows like any lamp (r ≤ 280): walls, and the bodies with Character shadows On. Big ones (flame
  rings, novas, slams, a boss's bursts) throw brief shadows.
- **The cap.** Spell, weapon-art and boss-attack lights that were k 0.9–1.4 are tagged `LX_FXL` and capped at 0.8 under Dynamic
  lighting only. That is 23 call sites: projectiles, the frost weapon fx, gear spells, the ember edge, the guard flash, the bell's
  burst, the Hearthkeeper's drawn weapon, the saint and boss casts and pillars, and the player's charged swing. Carried flames
  and lamps are not tagged. Classic ignores the tag.

## Settings (Settings › Graphics)

| row | options | default | notes |
|---|---|---|---|
| Reflections (`refl`) | Off / On | On (desktop), Off (touch) | Needs Dynamic lighting. One small pass only on frames with water, ice or wet stone. |
| Lit particles (`lpart`) | Off / On | On (desktop), Off (touch) | Needs Dynamic lighting and a 10th texture unit (else Off). |
| Depth haze (`dhaze`) | Off / On | On | Needs Dynamic lighting. Costs nothing measurable. |
| Light shafts (`rays`) | Off / Soft / Strong | Soft (unchanged) | Extended: real shafts under Dynamic lighting with shadows (gain 1 / 1.5). |

New keys get their defaults from `LX_DEFAULTS`; there is no migration. Look knobs: `LX4_TUNE` (reflections `env body bg dark wD iD
wetD pudD wetS pudS wetT wetK sky`, particles `pAmb pLamp pShaft`, shafts `sun open lamp lampOpen lampE0 lampE1 lampTop beam gain reach
roofN`, haze `far mid farIn midIn farHall vista`, effects `fxMax fxK fxR fxMin fxMaxR`). Debug views (`LX.dbg`): 14 shafts (× 8),
15 lit-particle coverage.

## Measurements

### Frame time (`perf.js`, headless Chrome, the knight running 240 frames, presentWorld read back; `perf.txt`)

| room | main (phase 3, default) | phase 4, new options off | phase 4, all on (default) |
|---|---|---|---|
| C10 catacombs (lamp shafts) | 0.22 / 2.98 / 3.38 | 0.22 / 2.82 / 3.23 | 0.16 / 2.37 / 2.62 |
| CF5 cisterns (reflections, vent beam) | 0.18 / 2.26 / 2.57 | 0.18 / 2.26 / 2.58 | 0.18 / 2.44 / 2.73 |
| K7 cathedral (3 lancet beams, motes) | 0.24 / 2.26 / 2.61 | 0.22 / 2.28 / 2.64 | 0.24 / 2.48 / 2.85 |
| DB15 lagoon (reflections, 3 beams) | 0.46 / 2.65 / 3.26 | 0.45 / 2.61 / 3.20 | 0.36 / 2.66 / 3.13 |
| SP8 spire (puddles, wet stone, rain) | 0.37 / 2.39 / 2.91 | 0.38 / 2.52 / 3.07 | 0.45 / 2.85 / 3.46 |
| R5 ramparts | 0.16 / 2.23 / 2.51 | 0.25 / 2.40 / 2.79 | 0.28 / 2.65 / 3.08 |
| SF11 starfall | 0.41 / 2.38 / 2.93 | 0.42 / 2.58 / 3.16 | 0.43 / 2.70 / 3.30 |

(renderWorld / presentWorld / whole step, ms. Each room's first column is measured right after entering it, which makes C10's the
noisy one, as in phases 2 and 3. Per-option rows are in `perf.txt`.)

- Overall: +0.1–0.55 ms a frame against main (run-to-run noise is about ±0.15 ms). The heaviest frame is SP8, with puddles, wet
  stone, rain and 12 foes: whole frames stay at 2.6–3.5 ms.
- Reflections cost the mask (≈ 0.02 ms of CPU), one RGBA upload and the small pass (+0.1–0.2 ms), and only on frames that show
  water, ice or wet stone.
- Shafts cost one SDF march per roofed air pixel while a high sun is up, plus a march inside each beam.

### Size
- **Assets: +0 bytes.** No file under `assets/` changed.
- Code: the game source grows 4 245 504 → 4 281 250 B unminified (+35.7 KB, +12.7 KB gzipped). The release build minifies it.
  The split build was not rebuilt, because it writes the tracked `web/dist/pub/`.

### Luminance (`luminance.md`, the phase-1 `stats.py` over every region, vista, dark and hot spot, and the prototypes)

- **Default settings.** Every region and vista is within ±2.2 of main, except the Crown Overlook X11 (+4.0: the haze pales the
  mid layer of castles toward the sunset).
- **Effect frames.** These are brighter while the effect plays (flame ring +3.2, nova +3.2).
- **The cathedral.** It loses its moon wash and gains beams: −1.2 at default, −1.9 under stress.
- **No new pixels ≥ 245,** and cream % is unchanged or lower.
- **Classic and shaders off: pixel-identical** (all 11 captures, bounding box of the difference = none).

## Montages (`tools/shots/v17/shading4/`, gitignored like every capture)

- **Reflections.**
  - `before_after_reflections.png` and `_2.png`: CF5 (the smith; the knight floating), CF5b, CF10, DB15, M14, M7 (the knight
    at rot water), DB5 (the Ferryman's mere, the knight wading), HF8 and HF13 (the knight on ice), SP8, the knight jumping over
    DB15 and M7 (high: no reflection), and the holy burst over CF5's water.
  - `before_after_reflections_zoom.png`: native-pixel crops of the same.
- **Particles.**
  - `before_after_particles.png` and `_zoom.png`: dense clouds near lamps. These are the C10 motes and dust, the K7 motes (the
    bokeh discs before), HF14 snow, M14 spores, and SP8 rain.
- **Shafts.**
  - `before_after_shafts.png` and `_zoom.png`: K7 and K11 (lancet beams in their glass colours, the ceiling hole), C10 (the lamp
    cone), and CF5 (the vent).
- **Haze and effects.**
  - `before_after_haze.png`: X11, LF1, R11, DU10, C8.
  - `before_after_effects.png`: shockwave, nova, flame ring, holy burst, slam, parry.
- **Regression sets.**
  - `before_after_regions_{1,2,3}.png` (22 regions), `_vistas.png` (seated), `_dark_hot.png`.
  - `_boss.png` and `_boss_zoom.png`: the Hearthkeeper in CF8.
  - `_orbit.png`, `lightning_sequence.png` (the Spire), `_stress.png`, `_classic.png`, `_hard_smooth.png`.
- **Toggles** (the same frame with the option off, and on): `toggle_reflections.png`, `toggle_lit_particles.png`,
  `toggle_light_shafts.png` (Off / Soft / Strong), `toggle_depth_haze.png`, and `toggle_all_off.png`.

## Reproduce
```
BUILD_OUT=web/dist/shading4_before.html python3 web/build_web.py   # on main / ad34746
BUILD_OUT=web/dist/shading4.html python3 web/build_web.py          # on shading4
cd tools/shots/v17/shading4
./run_all.sh $PWD/../../../../web/dist/shading4_before.html before
./run_all.sh $PWD/../../../../web/dist/shading4.html after
sh montage.sh                                                       # montages + luminance.md
SHOT_HTML=<build> node ../../shot.js perf.js out                    # frame time
```
`shoot.sh <html> <out> [settings] [names]` takes `ALT`, `TUNE`, `NTUNE`, `TUNE4` (LX4_TUNE), `DBG` and `SPOTS`. A spot's 7th field is JS
to evaluate before the capture (e.g. `__cloud('mote', 300)`, a dense particle cloud, or a `spawnFx`). zsh does not split `$L`: pass
`${=L}`.

## Regression tests (one at a time, test build `web/dist/shading4.html`)
- `SHOT_HTML=… sh tools/shots/wm/run.sh tools/shots/wm/mech.js`: 64/64 OK, 0 BAD/FAIL.
- `SHOT_HTML=… sh tools/shots/v17/boss/run.sh tools/shots/v17/boss/flow.js`: the full flow, `errs: []`, 0 BAD/FAIL.
- `node shot.js v17/area/checks.js`: `errs: []`, 0 BAD/FAIL.
- `node shot.js v15/cores/flow.js`: 34/34 OK, 0 BAD/FAIL.
- `node shot.js tr/bosses.js`: 32/32 OK on the final run (an earlier run had the known flaky `saint0 … byPlayer=0`, which fails the
  same way on main).
- **Settings matrix.** These ran on CF5, SP8, K7, C8 and R11 with no console errors:
  - Character shadows Off (reflections and shafts keep the silhouettes alone);
  - Dynamic without shadows (the old shafts);
  - Surface lighting Off;
  - Smooth and Dithered bands;
  - each new option Off, and all of them Off;
  - Light shafts Strong.

  The Graphics menu scrolls and cycles the three new rows.

## Not done / next
- The Crimson blood pools, the NeoHallow neon puddles (`xsc puddles`) and the Venn and Necropolis custom particle systems are not
  wired in. Each is one `lx4Rect` call in `lx4Mask`, or one `lxAir` wrap.
- Wet-stone streaks reflect only what is already bright on screen. A lamp just off screen does not streak.
- Reflections see only what is on screen. A body above the top edge has no reflection, and the reflection fades over the top 8 px.
- Open-sky crepuscular shafts (`LX4_TUNE.open`) are built but ship at 0 (see §3).
- Seated bench vistas render through their own path and take neither haze nor real shafts (they keep the screen-space sun). They
  were already painted with both.
