# Shading, phase 3: character shadows, contact pools, materials, eye adaptation, lightning

Branch `shading3` (from `main` at 1286646, the phase-2 release). The owner approved five items: bodies cast shadows, contact
shadows, materials, the phase-2 leftovers (pre-warmed boss normals, normals for rotated / raw draws), and eye adaptation plus
lightning that casts shadows. Everything stays inside the phase 1–2 pipeline: one tone curve, the summed light cut into the
Stepped bands, the rounded SDF shadows, the runtime normals in `lowN`. No asset changed.

Files: `web/src/41b_surf.js` (silhouette / pool buffer, materials, pre-warm, rotated normals), `41_light.js` (shader, sky light,
settings), `40_gfx.js` (eye adaptation, Settings rows), `09_main.js` (which draws cast shadows, pools instead of the ellipse),
`00_core.js` (hook calls for rotated draws), `22_spire.js` and `34_dunes.js` (lightning), `42_kit.js` (moving platforms / gate bars).

## 1. Bodies cast shadows

A new game-resolution buffer `lowO`. While `renderWorld` draws the knight (and his weapon), foes, the boss, and props between
20 and 160 px that don't glow, `LXO.occ` is set and every `drawSprite` / `drawRotated` also draws the same frame into `lowO` with
the same transform and alpha. `lxoFinish` flattens it to a silhouette (`source-in` red). The pass uploads it as
`LUMINANCE_ALPHA` (texture unit 8, LINEAR so taps come out soft).

The wall is behind the bodies. A ray from a wall pixel `p` to a lamp crosses the bodies' plane part of the way there, at
`q = p + dir × min(dist × ckz, cmx)` (`ckz` 0.32, at most `cmx` 26 px). If a silhouette covers `q`, the body shades `p`. That gives
the shadow you'd see on a wall right behind a figure: the silhouette about 1.4× larger, offset away from the lamp, mostly
behind the body, with a fringe that grows as the lamp gets closer. It costs 3 taps (`q` and ±perpendicular, spread
`0.75 + off × 0.07`, so the penumbra widens with the offset) and runs only when `q` lies in this frame's silhouette box
(`OBB`, a uniform). Elsewhere it costs nothing.

- **No self-shadowing:** a pixel covered by a silhouette receives no body shadows. Bodies sit in one plane, and the knight in
  front of a boss would otherwise be shadowed at the wrong offset.
- **Carried lamps** (a lantern, a torch, the Hearthkeeper's flame at the hammer head): if a silhouette covers the lamp or any
  point 6 px around it, that lamp casts no body shadow. Before this check, the Hearthkeeper's arm threw a huge shadow from its
  own flame.
- Only shadow-casting lamps (`sh`: Hard / Soft shadows, r 16–280, `o.shadow !== false`, flagged by +2048 on `LC.w`; a light
  can opt out with `o.cast: false`). The knight's soft fill casts none. The light keeps `1 − csh × cover` (`csh` 0.72), and the
  bands then step it like any other light.
- Backdrop pixels are not shadowed (a shadow on the sky would be wrong).

## 2. Contact pools

After the bodies are drawn, `lxoFinish` draws a soft radial ellipse into `lowO` (`destination-over`, so it stays under the
silhouettes) under the knight, every live foe, the boss and props that stand on a floor. In the pass,
`pool = A − L × A`. The pool darkens the ambient light (as AO) and 60 % of the lamp light, in 3 clean steps like the bands
(smooth with Smooth bands). Bodies in the air (jumping, flying foes) get a pool on the floor found below them (`lxoFloor`, up
to 7 tiles; one-way platforms count). It is wider and fainter with height, and it tightens and darkens as the body comes down
(gone at 88 px). With Character shadows on, Dynamic lighting no longer draws the old flat ellipses. Classic draws them as
before.

## 3. Materials

No new art. `lowN`'s B channel now holds the art pixel's luminance in 6 bits plus a 2-bit material: 0 matte, 1 metal
highlight, 2 sheen, 3 metal. The trust check reads the 6-bit luminance; its extra tolerance of 0.008 covers the quantization.
Materials are decided when the normals are built:

- A small hint table, `LXN_MAT`. Sheets marked `metal` (the knight, his weapons, the Hearthkeeper, armoured foes, the
  Unforged, iron props, bells, cages, gates, chandeliers…) allow metal. Inside them a pixel is metal if it is greyish
  (chroma < 0.36, value ≥ 0.1, not an inner line). Red cloth, gold trim, wood and skin in the same sheet stay matte. A metal
  pixel is a **highlight** (1) when the artist painted it bright: luminance ≥ max(0.4, 1.6 × the sprite's median), or a local
  peak (+0.07 over its 4 neighbours) at ≥ 0.75 × that. All other metal is 3. `ice` sheets: pale blue-white pixels take sheen.
  Every other sheet is matte.
- Room layers take their region's material from `LXN_MAT_ROOM`: Hoarfrost ice on both layers. The Mire, the Barrows and the
  outdoor Spire (under rain) get wet stone, on the terrain only.

In the shader, each lamp with r > 40 adds a specular term from `n·h`. `h` is halfway between the direction to the lamp (lamp
`shz` px in front of the plane) and the viewer, who sits 420 px in front of the screen centre, so glints slide a little as the
view moves:

- highlight: `smoothstep(0.95, 0.98, n·h) × 2.2`. Sharp, almost binary.
- metal body: `smoothstep(0.93, 0.99) × 0.18`. A faint sheen.
- wet / ice: `(n·h)^6 × 0.45`. A soft broad sheen.

The normals have only 8 directions × 3 tilts, so a glint jumps from facet to facet as a lamp or the knight moves. It stays
small and stepped and never smears. Specular light is added as light of its own (like the rim), metal tints it 35 % toward
its own colour, and it is soft-capped at 0.5. Sparks and motes (r ≤ 40) and the knight's soft fill make no glints; otherwise
every ember sparkled on the walls of the Deep. Lava is drawn as an emitter, so it has no light to catch. A trial of glassy
rock beside it (Deep room layers as wet) lit the stone too much (r_deep mean +1.9) and was dropped.

Tuning history: the first cut (glint threshold 0.94, metal body × 0.25, cap 0.75) lit the whole chest plate of the
Hearthkeeper beside its phase-3 flame cream. Now the glints sit on its helmet, shoulder and arm, and the plate stays dark
iron (`before_after_boss_zoom.png`).

## 4. Phase-2 leftovers

- **Pre-warm.** On room entry, big foes (frames > 64×64) queue the first 3 frames of every animation. When a boss appears,
  changes sheet or changes phase, its current frame is built at once (under the room fade or its intro). The first 6 frames
  of every animation in its current sheet, and the first 2 of every sheet in its family, are queued too. The family is the
  sheets sharing its name up to the phase: `hearthkeeper_p1_*`, `cindervane` + `cindervane_p2/p3`… Pre-warm jobs wait in their
  own queue (`LXN.wq`) and run only when nothing that is being drawn is waiting, so they never delay the look-ahead frames.
  Sheets still decoding are retried. The budget is ×2 in cutscenes / dialogue (×3 while fading, as before). Measured with
  `warm.js` (the Hearthkeeper fight with a real clock, seeded): after entry, **0** boss frames were drawn flat through 15 s of
  phase 1 and 5 s of phase 3, against 7 with the pre-warm off. The ~15 flat draws in the first 5 frames after entry are the
  forge's big props, under the fade.
- **Rotated draws.** `drawSprite` with `rot` and `drawRotated` now mirror their normals. The normal image is drawn with the
  same transform, and its vectors are turned by the transform's own rotation and mirror, quantized to 16 angles. That error
  (≤ 11°) is below the 8-direction quantization of the normals. The result is cached per sheet / frame / angle / mirror. This
  covers the Hearthkeeper's thrown spears, lit arrows and projectiles, swinging bells and chandeliers (42_kit, crimson,
  necropolis), cranes in the Deep and archive pieces. Rotated bodies also go into the silhouette buffer. Checked in
  `rot_n` (debug view 8): spears at 6 angles show correctly turned edges.
- **Raw draws.** `lxnRaw(sh, frame, x, y)` mirrors an unscaled `g.drawImage` of a sheet frame. It is used for moving platforms
  (`kitDrawSlab`) and rising gate bars (whole bars only: the clip isn't mirrored). The other raw draws in the code are tinted
  silhouettes (afterimages, the ember doppelgänger), far sky drakes, backdrops or emitters. They have no normals to give, and
  they stay flat on purpose.

## 5. Eye adaptation and lightning

**Eye adaptation** (40_gfx.js, `GFX_EYE`) is not an auto-exposure. Each region keeps its calibrated look. On a room change,
the room's 3rd lit frame is metered: a box-filtered 48×27 copy of the lit image, read back once (0.3 ms). The first two frames
are skipped because they lack the room's lamps and sit under the fade. That reading is compared with the eye's key for the last
room, which is metered on entry and refreshed every 2 s as the view moves. The post pass's exposure then starts at
`A0 = (new / old)^0.5`, clamped to 0.72–1.35, and settles to exactly 1 with τ = 0.3 s (95 % in about 0.9 s, mostly while the
room fades in). Differences under |ln| 0.1 do nothing. It is never applied on the Classic or shaders-off path. Measured
(`after_expo.txt`):

| transition | frame 3 | frame 21 | frame 63 |
|---|---:|---:|---:|
| Last Field → catacomb C10 (bright → dark) | 0.733 | 0.892 | 0.989 |
| C10 → Dunes DU10 (dark → bright) | 1.136 | 1.048 | 1.005 |
| Crown X7 → Crimson CM9 (bright → dark) | 0.720 | 0.886 | 0.988 |

**Lightning** (`lxSkyLight` in 41_light.js). Under Dynamic lighting with shadows, the Spire's `SPR.flash` (sky flashes, strikes,
the Cindervane's roars and dives) and the Pharaoh's storm bolts (`DU.storm.flash`) become a directional light from the sky. It
goes into slot 0 of the light list with `LP.z < 0` meaning "directional". It is shadowed by the same SDF sphere-trace (up to
170 px toward the sky, an 18 px "sun" for the penumbra), it casts body shadows (shifted 9 px down-slant), and it wraps and
glints like any lamp. 35 % of the flash stays an unshadowed fill, so rooms under a roof still flicker. Classic and Dynamic
without shadows keep the old single 420 px point light. The slant comes from the strike's side of the screen, or, for sky
flashes, from a hash of the time. No `Math.random`, so seeded tests stay in step. The overlay flash is unchanged. Result: the
flash lights ledge tops, helmets and shoulders, leaves the faces under the ledges in shade, and throws the foes' shadows down
and to the side (`lightning_sequence.png`, `lightning_zoom.png`).

## Settings (Settings › Graphics)

| row | options | default | notes |
|---|---|---|---|
| Character shadows (`csh`) | Off / Contact / On | On (desktop), Off (touch) | Contact: pools only. On: + cast shadows (needs Hard/Soft shadows). Off: the old ellipses. |
| Materials (`mat`) | Off / On | On (desktop), Off (touch) | Needs Surface lighting (which is Off on touch too). The bits are always built; Off just zeroes the term. |
| Eye adaptation (`eyead`) | Off / On | On | Needs Dynamic lighting. |

New keys get their defaults from `LX_DEFAULTS`; there is no migration. The silhouette buffer needs a 9th texture unit. On a GPU
with only 8 (`MAX_TEXTURE_IMAGE_UNITS < 9`), the shader is compiled without it (`OCC 0`), and cast shadows and pools are
skipped. New `LX_TUNE` knobs: `csh con ckz cmx csk glk shk eyez sky skyFill skyReach`. `LXN_TUNE`: `mCh mLo mHi mHk mPk iceV`.
`LXO_TUNE`: `pool air propMin propMax`. Debug views (`LX.dbg`): 11 silhouettes (red) / pools (green), 12 materials (red
highlight, green sheen, blue metal), 13 the specular light alone.

## Measurements

### Frame time (`perf.js`, headless Chrome, the knight running 240 frames, presentWorld read back; `perf.txt`)

| room | phase 2 (main) | phase 3, new options off | Contact | Shadows | all on (default) |
|---|---|---|---|---|---|
| C10 catacombs, 9 lights | 0.17 / 2.71 / 3.05 | 0.17 / 2.73 / 3.07 | 0.13 / 2.22 / 2.45 | 0.13 / 2.19 / 2.39 | 0.15 / 2.16 / 2.38 |
| R5 ramparts, 9 foes | 0.20 / 2.41 / 2.73 | 0.17 / 2.10 / 2.36 | 0.20 / 2.12 / 2.39 | 0.22 / 2.18 / 2.48 | 0.22 / 2.19 / 2.50 |
| CF5 forge | 0.15 / 2.01 / 2.25 | 0.15 / 2.07 / 2.32 | 0.16 / 2.07 / 2.31 | 0.16 / 2.13 / 2.37 | 0.23 / 2.19 / 2.52 |
| SF11 starfall, 8 foes | 0.30 / 2.04 / 2.46 | 0.36 / 2.14 / 2.63 | 0.33 / 2.17 / 2.60 | 0.38 / 2.26 / 2.74 | 0.38 / 2.28 / 2.77 |
| SP8 spire, 12 foes | 0.32 / 2.20 / 2.65 | 0.32 / 2.22 / 2.68 | 0.40 / 2.35 / 2.85 | 0.39 / 2.38 / 2.89 | 0.44 / 2.46 / 3.00 |
| SP8, lightning held on | 0.25 / 2.13 / 2.48 | 0.32 / 2.29 / 2.73 | 0.39 / 2.42 / 2.91 | 0.40 / 2.41 / 2.90 | 0.40 / 2.42 / 2.93 |

(renderWorld / presentWorld / whole step, ms. C10's first column is the first setting after entering the room, which makes
it the noisy one, as in phase 2.)

- Overall, about +0.1–0.35 ms a frame against phase 2. That is the silhouette / pool canvas and its upload (+0.05–0.1 ms
  CPU), the shadow taps near bodies and the specular term (+0.1–0.25 ms GPU), and the lightning march during a flash
  (≈ +0.1 ms). Whole frames stay at 2.4–3.0 ms.
- Eye adaptation: one 0.3 ms readback on room entry plus one every 2 s.
- Room entry: unchanged. The pre-warm spends the existing per-frame budget only when nothing drawn is waiting.

### Size
- **Assets: +0 bytes.** No file under `assets/` changed.
- Code: the game script grows 4 214 413 → 4 241 200 B in the (unminified) test build (+26.8 KB, +9.9 KB gzipped). The
  release build minifies it. The split build was not rebuilt: it writes the tracked `web/dist/pub/`.

### Luminance (`luminance.md`, the phase-1 `stats.py` over every region, vista, dark and hot spot)
Default-setting means stay within ±0.2 of phase 2 everywhere except **r_spire** (16.5 → 17.1, p95 51.8 → 54.8). That is the
wet-stone sheen under the moon-lamp on its ledge. No new pixels ≥ 245, and cream % is unchanged (±0.02). Stress (Bright +
High bloom + Strong shafts): ±0.1. **Classic and shaders off: pixel-identical** (all 7 captures, bounding box of the
difference = none).

## Montages (`tools/shots/v17/shading3/`, gitignored like every capture)
- `before_after_proto.png`, `_proto_2.png`, `_proto_zoom.png`: the prototype rooms with their foes. Lamp-lit catacomb C10 (+
  the knight mid-jump), the dusk ramparts R5, C8, the forge CF5, the Deep D11, the Hoarfrost HF14, the Mire M14, the Spire SP8,
  X11, H3.
- `before_after_orbit.png` and `_orbit_zoom.png`: one lamp moved around the knight, a shield warden, a rot hulk and the
  Hearthkeeper in a dark catacomb. This is the clearest view of the cast shadows: the hulk's on the skull shelf, the knight's
  between him and the warden, plus the pools and glints.
- `before_after_boss.png` and `_boss_zoom.png`: the Hearthkeeper in CF8 at fixed frames, phase 1 at the furnace, phase 3 in the
  dark with its flame (glints on helmet and arm, body shadows on the wall, pools).
- `lightning_sequence.png`, `_2.png`, `lightning_zoom.png`: SP8 calm, a sky flash at frames 1, 4, 8 and 14 of its decay, and a
  strike to the knight's right (frames 16, 19). The after column has the sky light with shadows; the before column has the
  old unshadowed flash light.
- `exposure_transition_strip.png` (+ `expo_b2d.png`, `expo_d2b.png`, `expo_b2d2.png`): frames 3, 9, 15, 21, 30, 39, 51 and 63
  after each teleport, shown without the fade.
- `toggle_character_shadows.png` (Off | Contact | On, same frame) and `toggle_materials.png` (Off | On).
- Regression sets: `before_after_regions_{1,2,3}.png`, `_vistas.png` (seated), `_dark_hot.png`, `_stress.png`,
  `_classic.png` (shaders off + Classic), `_hard_smooth.png`.

## Reproduce
```
BUILD_OUT=web/dist/shading3_before.html python3 web/build_web.py   # on main / 1286646
BUILD_OUT=web/dist/shading3.html python3 web/build_web.py          # on shading3
cd tools/shots/v17/shading3
./run_all.sh $PWD/../../../../web/dist/shading3_before.html before
./run_all.sh $PWD/../../../../web/dist/shading3.html after
sh montage.sh                                                       # montages + luminance.md
SHOT_HTML=<build> node ../../shot.js perf.js out                    # frame time
SHOT_HTML=<build> node ../../shot.js warm.js out                    # flat boss frames (prepend window.__noWarm = 1 to compare)
```
`shoot.sh <html> <out> [settings] [names]` takes `ALT` (the same frame under other settings), `TUNE`, `NTUNE`, `DBG='[11,12,13]'`
and `SPOTS`. `orbit.sh` takes the same. `storm.js` and `expo.js` take `window.__shSet`.

## Regression tests (one at a time, test build `web/dist/shading3.html`)
- `SHOT_HTML=… sh tools/shots/wm/run.sh tools/shots/wm/mech.js`: 64/64 OK, 0 BAD/FAIL.
- `SHOT_HTML=… sh tools/shots/v17/boss/run.sh tools/shots/v17/boss/flow.js`: the full flow, `errs: []`, 0 BAD/FAIL.
- `node shot.js v17/area/checks.js` (from tools/shots/): `errs: []`, 0 BAD/FAIL.
- `node shot.js v15/cores/flow.js`: 34/34 OK, 0 BAD/FAIL.
- `node shot.js tr/bosses.js`: 1 BAD, `saint0 … byPlayer=0`. It **fails the same way on main** (1286646, the before build), so it
  predates this branch. All other bosses are OK.
- Settings matrix (Character shadows Contact / Off, Materials Off, Eye adaptation Off, Surface lighting Off, Dynamic without
  shadows, Hard shadows, Dithered bands, bloom + shafts off) on C10, R5, SP8 and C8: no console errors. The Graphics menu shows
  and cycles the three new rows.

## Not done / next
- Bodies only shadow the wall plane. A body standing in front of another (the knight before a boss) does not shade it, because
  the projection would be at the wrong depth.
- A lamp carried inside a silhouette casts no body shadows at all, not even onto other bodies' walls. Per-body IDs in the
  buffer would allow "everyone but the carrier".
- The hint table lists sheets by name. A foe that is armoured but not listed stays matte. Adding it is one regex entry in
  `LXN_MAT`.
- Lava stays an emitter: no sheen on it, by design.
- The tinted silhouette draws (afterimages, the ember doppelgänger in 24_secrets) have no normals. Their art is a flat tint,
  so a normal would have nothing to light.
