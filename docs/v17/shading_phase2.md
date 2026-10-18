# Shading, phase 2: surface lighting and a backdrop that lamps no longer paint

Branch `shading2` (from `main` at 08d2a1c, the phase-1 release). The owner's goal: "have good shading in game". Light
should wrap around forms the way it does in Blasphemous or Dead Cells. The knight, foes, bosses, props and bricks catch
light on the side facing a lamp, fall into shade on the far side, and take a crisp rim on the silhouette. Lamps also have
to stop lighting the far painted backdrops (`bg_*` parallax, `vista_*` paintings) as if they were a wall right behind
the lamp.

Files: `web/src/41b_surf.js` (new: normal generation, caches, the normal-buffer mirror), `41_light.js` (lighting shader,
backdrop layers, settings migration), `00_core.js` (one hook line in `drawSprite`), `03_world.js` (`drawParallax` keeps
its mid layer as a mask), `09_main.js` (`renderWorld` uses the backdrop layer and mirrors the room layers' normals),
`40_gfx.js` (Settings rows), `36_neohallow.js` (the glitch effect reads the backdrop too).

## 1. The backdrop has its own layer

Under Dynamic lighting `renderWorld` now draws `drawParallax()` (the biome layers and every override: vistas, the forge's
`CFA_BG`, the Crown, the Last Field, the Spire…) into `lowBg` instead of `low`. `low` starts transparent and holds only
the world, so its alpha is the world's coverage over the backdrop. The default `drawParallax` also copies its **mid**
layer (the silhouettes of arches, pillars and ruins in between) into `lowBgM`, which is used only as a mask. It is
composited straight back into `lowBg`, so overrides that draw after the base still land on top.

In the lighting shader:

- **World pixels** are lit as before: ambient × AO, banded lamps, shadows, plus the new surface terms below.
- **Backdrop pixels** take the ambient and only a share of the lamp light. That share is unshadowed, uses the same bands,
  and has no AO. A pure backdrop pixel skips the shadow march (it got cheaper).
  - The far layer's share is `LX_TUNE.bgSky = 0.03` (next to nothing) for skies and far views. In the halls whose far
    painting is the room's own back wall, it is `LX_BG_FAR`: catacombs 0.85, archives 0.8, forge 0.8, barrows 0.75,
    cathedral 0.6, deep 0.6, thornveil 0.4. The torch keeps its glow on the bone wall of the catacombs.
  - The mid layer's share is `LX_TUNE.bgMid = 0.3`.
  - Vista benches (`VISTA_BG`) count as views and take the sky share.
  - A region can override all of this with `AREAS[b].lxBg = [far, mid]`.
- **Seen through a back wall.** Indoor rooms fade their back walls to 0.8 / 0.5 / 0.28 alpha toward open space. Where
  the wall is mostly there (alpha 0.3 to 0.8), the backdrop behind it is lit with the wall, so the pool of lamp light on
  a wall stays whole. The faint outer steps light the backdrop only where it is dark (luminance < 0.12 to 0.4). A pale
  sky seen through them keeps the sky share. This is what removes the rings in the Hermit's window (H2/H3).
- If the GL pass dies, `lxFlatten` puts `lowBg` back under `low`. Classic and shaders-off never split the layers, and
  their captures are pixel-identical to the phase-1 build (all 7 of them, mean |Δ| = 0).

Result: the pink discs on the Crown Overlook's sky (X11) are gone, as are the stepped orange disc beside the Hermit's
lamp (H2), the wind-chime halo on the dusk sky (H3), the lantern's big disc on the Mire's sunset, and the floating
"bokeh" discs on the Last Field, Cathedral and Archives backdrops. See `before_after_backdrop*.png` and
`before_after_regions_*.png`.

Trade-off: a few rooms leaned on a lamp lighting the sky. The Spire's moon-lamp lit a bright wedge on the backdrop
(SP8). The Last Field's sun and ember lights warmed its painted sky: mean luminance 74.9 → 63.8, and 64.7 → 48.3 at
Brightness Dark. These now show as painted, under the region's ambient. If the owner wants one of them back, it takes a
single line: `AREAS.lastfield.lxBg = [0.4, 0.3]`.

## 2. Surface normals, generated from the art (no new assets)

No normal maps ship. Every normal is derived at runtime from the art itself and cached (`41b_surf.js`):

```
height = silhouette bevel × inner relief
  silhouette: distance to the sprite's edge (2-pass chamfer), quarter-circle profile over B px,
              B = 1.3 × its thickest part (a dome over a body), clamped 2-16 px; boxy art (fills > 72 % of its
              bounding box: tombs, crates, plinths) uses 0.35 × that, so it keeps a flat face with bevelled edges
  inner:      a shallow dip (1.1 px over 2 px) along the art's own dark lines: outlines, mortar, the gaps
              between plates, measured against the median luminance (×0.62) of the sprite, or of each 16 px
              cell for room layers
normal = gradient of the height, quantized to 8 directions × 3 tilts (≈26°, 52°, 77°)
```

The quantization keeps the light stepped like the Stepped bands. A form turns in three clean steps, there is no
smeared gradient, and the art stays crisp. Inner lines only reach the first tilt step, so plates and bricks turn gently
and never take a rim, and painted decals don't get embossed. Only a silhouette's outer pixel reaches the steepest step,
and only that step takes the rim.

- **Sprites.** Every lit `drawSprite` (the knight, his weapon overlay, foes, bosses, props) also draws its frame's normal
  image into `lowN`, with the same transform (flip, squash, alpha), in the same order. Whatever is on top wins, so the
  knight in front of a boss keeps his own silhouette. Normal images are cached per sheet, frame and facing: a mirrored
  draw uses a copy with x negated. Small frames (≤ 64×64: the knight, his weapon, most foes) are made on the spot,
  within 1.5 ms a frame. Big ones (bosses) are queued with the next 5 frames of the same animation and made within a
  3 ms/frame budget (9 ms while the screen fades), and they show flat for the frame or two before they are ready.
  Caches of sheets not drawn for a few rooms are dropped once they pass 16 M px. The knight and weapons are never
  dropped.
- **Room layers.** `room.back` and `room.front` get normal canvases, built in 32-row bands, nearest the camera first.
  Their key is the canvas itself (a `WeakMap`), so rooms that swap layers (crimson, omen, archives' inversion, broken
  walls) get theirs rebuilt. `front` uses a 3 px silhouette bevel (the lip of the terrain) plus brick relief. `back`
  uses brick relief only: its alpha veil must not read as edges.
- **Trust check.** `lowN.b` holds the luminance of the art pixel the normal was made from. The shader uses a normal only
  while the lit layer still shows that pixel (|Δ| < 0.035). Water, fog, fx, the dark hit-flash tints, decor painted onto
  a room layer later, and alpha fades all fall back to flat, which is exactly the phase-1 look. They never borrow the
  normal of whatever lies beneath.

## 3. The lighting model (41_light.js)

For a pixel with a normal (tilt > 0), per lamp:

- **Wrap**: `light × max(0, 1 + sk × facing)`, where `facing = dot(normal.xy, dir to lamp) × dist / (dist + shz)`.
  `sk = 1.25` and `shz = 18`. Right in front of a lamp (distance → 0) nothing is side-lit, because the lamp lights the
  face. The lit side takes up to about 2× the light and the far side falls toward 0. The summed light then goes through
  the same Stepped / Smooth / Dithered bands, so the turn of a form is also stepped.
- **Rim**: only the steepest tilt step (the silhouette's outer pixel), facing the lamp:
  `rim × light × smoothstep(0.2, 0.75, cos)`. It is added as light of its own, not multiplied by the albedo, so the
  knight's black outline catches it too. It is soft-capped at 0.6 and `rim = 1.0`.
- **The art's soft cap** (phase 1's `lmax`: bright or saturated art takes less light) is now computed from the *flat*
  light and scales the shaded light. Before this change the cap squeezed lit and shaded sides back together and the
  wrap all but vanished on the Hearthkeeper.
- **Ambient**: `AMB × (1 − 0.3 × n.y)`. The sky lights tops a little more than undersides, which gives forms volume
  even without a lamp.
- **The knight's fill** (a soft light at his chest) is frontal: `× mix(1, nz, 0.6)`. His edges turn away from it, which
  leaves room for the lamp's rim.
- Pixels without a normal (flat, backdrop, Surface lighting off) get exactly the phase-1 terms.

New `LX_TUNE` knobs: `sk`, `shz`, `ambk`, `ntol`, `bgSky`, `bgMid`. The normal-generation knobs are in `LXN_TUNE`.
Debug views (`LX.dbg`): 1 = the mid-layer mask (was: occluders), 8 = normals (x, y, trusted), 9 = world coverage,
10 = rim.

## 4. Settings

- **Settings › Graphics › Surface lighting: Off / On** (new, `SETTINGS.surf`). It defaults to On on desktop and Off on
  touch devices, where it would be one more layer to draw and upload. Off draws no normals, uploads no normal texture,
  and makes no caches.
- **Rim light: Off / On** is rebuilt on the silhouettes and defaults to **On** (migration `lxv 3` turns it on once). It
  needs Surface lighting.
- Classic and Shaders off are untouched.

## Measurements

### Size
- **Assets: +0 MB.** No normal sheets ship, and no file under `assets/` changed, so the release split build's asset chunks
  (about 33 MB) are unchanged. The split build itself was not rebuilt: it writes the tracked `web/dist/pub/`.
- Code: +12.0 KB minified (2 929 569 → 2 941 525 B), +4.3 KB gzipped. The test build is 36 153 → 36 174 KB.
- Runtime memory: normal caches hold about 0.6-1.6 M px per room in the measured rooms (RGBA ×2 facings for sprites,
  one canvas per room layer), plus three 384×216 layers.

### Frame time
Headless Chrome on the dev laptop, `tools/shots/v17/shading2/perf.js`: the knight running 240 frames per room.
`presentWorld` is the GPU lighting + post, read back so it really finishes.

| room | phase 1 (renderWorld / presentWorld / whole step) | phase 2 surface off | phase 2 surface + rim on (default) |
|---|---|---|---|
| C10 catacombs (9 lights, 4 foes) | 0.15 / 2.73 / 3.09 ms | 0.17 / 3.38 / 3.77 | 0.27 / 2.78 / 3.20 |
| R5 ramparts (9 foes) | 0.17 / 1.77 / 2.07 | 0.17 / 2.56 / 2.87 | 0.27 / 2.66 / 3.05 |
| X11 Crown Overlook | 0.16 / 1.79 / 2.07 | 0.15 / 2.58 / 2.86 | 0.16 / 2.68 / 2.93 |
| CF5 forge (4 foes) | 0.19 / 1.75 / 2.07 | 0.19 / 2.55 / 2.89 | 0.27 / 2.67 / 3.07 |
| SF11 starfall (8 foes) | 0.36 / 1.85 / 2.38 | 0.35 / 2.64 / 3.19 | 0.50 / 2.75 / 3.41 |

(C10 "surface off" is the first setting measured after entering the room, which makes it the noisy one.)

- Overall: about +0.8-1.0 ms a frame against phase 1. Most of it is the backdrop split, which is on whatever the
  setting: uploading `lowBg`, the mid mask, and `low` as RGBA. Surface lighting itself adds +0.1 ms of GPU (the normal
  texture) and 0.1-0.15 ms of CPU (the normal mirror). Whole frames stay at 2.9-3.4 ms, far under 16.7.
- On room entry: 9-74 sprite frames plus the room-layer bands, 35-108 ms in all, spread over 9-23 frames.
  That is 3 ms/frame, or 9 ms while the screen fades in. Room entry itself is unchanged (2-13 ms).

### Luminance
Same world-only captures as phase 1 (`luminance.md`, `stats.py`). Lit scenes stay within ±1 of phase 1: catacombs 25.3
→ 25.3, ramparts 23.1 → 23.3, forge hearth 22.8 → 23.3, Threshold 73.8 → 74.0. No new pixels ≥ 245 and no new cream.
The drops are all lamp light that used to sit on painted skies: Mire 38.7 → 31.4, Spire 19.3 → 16.5, Last Field
74.9 → 63.8, Dunes sand 54.2 → 50.9. Classic and shaders off: identical.

## Montages (`tools/shots/v17/shading2/`, gitignored like every capture)
- `before_after_orbit.png` and `_orbit_zoom.png`: one lamp moved left, right and above the knight, a shield warden, a
  rot hulk and the Hearthkeeper in a dark catacomb. This is the clearest view of wrap, shade and rim.
- `before_after_boss.png` and `_boss_zoom.png`: the Hearthkeeper in CF8 at fixed frames (deterministic: the page's own
  loop is stopped), phase 1 at the furnace, and phase 3 in the dark arena with its flame.
- `before_after_foes.png` and `_foes_zoom.png`: catacomb lamp room, ramparts with its torch, C8, the forge and the Deep
  over lava, foes kept in frame.
- `before_after_backdrop.png` and `_backdrop_zoom.png`: X11, H3, H2, the Crown, LF1, Crown snow.
- `before_after_regions_{1,2,3}.png`, `_vistas.png` (seated), `_dark.png`, `_hot.png`.
- Settings: `_stress.png`, `_classic.png` (shaders off), `_classic_light.png`, `_hard.png`, `_bands_smooth.png`,
  `_bands_dithered.png`, `_brightness_dark.png`, `_brightness_bright.png`.
- `toggle_surface_off_on.png` and `toggle_rim_off_on.png`: the same frame with the new option off (left) and on (right).
- Every capture is deterministic: `snap.js` and `boss.js` stop the page's own `requestAnimationFrame` loop, so only the
  script advances the game and both builds show the same moment.

## Reproduce
```
BUILD_OUT=web/dist/shading2_before.html python3 web/build_web.py   # on main / 08d2a1c
BUILD_OUT=web/dist/shading2.html python3 web/build_web.py          # on shading2
cd tools/shots/v17/shading2
./run_all.sh $PWD/../../../../web/dist/shading2_before.html before
./run_all.sh $PWD/../../../../web/dist/shading2.html after
sh montage.sh                                                       # montages + luminance.md
SHOT_HTML=<build> node ../../shot.js perf.js out                    # frame time
```
`shoot.sh <html> <out> [settings] [names]` takes look knobs live: `ALT='{"surfoff":{"surf":0}}'` saves the same frame again
under other settings, `TUNE='{"sk":1.6}'` (LX_TUNE),
`NTUNE='{"bK":1.0}'` (LXN_TUNE), `DBG='[8,10]'` (debug views), `SPOTS='[[name, room, tx, ty, kind, face]]'`.
`orbit.sh` takes the same `TUNE` / `NTUNE` / `DBG`.

## Regression tests (one at a time, test build `web/dist/shading2.html`)
- `SHOT_HTML=… sh tools/shots/wm/run.sh tools/shots/wm/mech.js`: 64/64 OK, 0 BAD/FAIL, no console errors.
- `SHOT_HTML=… sh tools/shots/v17/boss/run.sh tools/shots/v17/boss/flow.js`: the full flow (phases, temper, death/core, furnace,
  effigy, rekindle, rematch), `errs: []`, 0 BAD/FAIL.
- `node tools/shots/shot.js tools/shots/v17/area/checks.js` (from tools/shots/): `errs: []`, 0 BAD/FAIL, every page present.
- `node tools/shots/shot.js tools/shots/v15/cores/flow.js`: 34/34 OK, 0 BAD/FAIL.
- Settings matrix through `run_all.sh` (default, stress, shaders off, Classic, Hard shadows, Smooth, Dithered, Dark,
  Bright, surface off, rim off): no console errors. Classic and shaders off are pixel-identical to phase 1.

## Not done / next
- Bosses that draw themselves with raw `g.drawImage` or shapes instead of `drawSprite` have no normals and stay flat
  (phase-1 look). Most bodies go through `drawSprite`.
- `drawRotated` and rotated `drawSprite` draws (projectiles, spinning weapons) draw no normals.
- The first frame of a boss animation that hasn't been seen yet can show flat for a frame or two. Pre-warming a boss's
  sheets at its intro would hide that.
- Parallax overrides that paint their own mid layer (the forge's `CFA_BG`, the Crown panorama) are counted as "far". They
  take the far share of their region.
- Real baked normal maps were not needed. The derived normals with quantization read well at this resolution and cost
  no download. If an artist ever paints normals for the knight, `lxnGenFrame` is the one place to load them instead.
