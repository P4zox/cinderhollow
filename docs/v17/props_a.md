# Prop rework, batch A: Dunes and Necropolis (branch `bg-overhaul`), 2026-10-17

This pass follows the audit (`docs/v17/PROPS_AUDIT.md`, batch A). It reworks 45 targets (47 tags) across the 9 sheets that batch A owns:
`xsb_big` (all tags), `xsb_tall`, `xsb_du`, `xsb_nv`, `du_colossus`, `du_stele`, `nv_bell`, `nv_bell_big` and `nv_props`.
**No code changed.** Every sheet keeps its frame size, its tags, its frame counts and order, its durations and its anchors.
Frames that were not reworked are copied pixel for pixel from the v1 backup, and the build checks this.
Nothing was committed, pushed or published.

## Rebuild
```
python3 art/gen_props_a.py                      # rebuild all 9 sheets (about 17 s; uses the cached renders, no server needed)
python3 art/gen_props_a.py --only xsb_du        # rebuild one sheet (a sheet is always rebuilt whole). Target keys work too, e.g. --only obelisk
python3 art/gen_props_a.py --render obelisk,jars0   # re-run ComfyUI for those render keys (<key>_render.png), then build
python3 art/gen_props_a.py --dry --preview DIR  # guide | render | 6x result per target, without building
python3 art/gen_props_a.py --contact DIR        # before/after contact sheets (v1 compared with assets/), player at the same scale
```
- `art/props_a_lib.py` is the shared kit. It has a hi-res painter `Cv` with masks, normal-lit volume (`pillow`, `cyl`,
  `revolve` for bodies of revolution, `relief` for sculpted height fields, `rotate`), the ComfyUI `render` call (outputs under the
  `props_a/` prefix), and the path back down to 1x: premultiplied `down`, an unsharp pass, per-material `lock`, `majority`, `rim`,
  `outline` and the 1x touch-up `Px`. It also has `rebuild` (frames swapped into the v1 sheet, with a contract check) and `contact`.
- `art/gen_props_a.py` has one function per target, the `TARGETS` registry (key -> sheet, tag, frames), and the region ramps
  (`DU_*` and `NV_*` in the lib, sampled from `bg_dunes_*`, `vista_du15_*`, `tiles_dunes`, `bg_necropolis_*` and `tiles_necropolis`).
- `art/bg_src/props_a/` is gitignored. It holds the ComfyUI renders (`<key>_render.png`), the IP-Adapter style references (crops
  of the new `bg_dunes_mid` and `bg_necropolis_far`) and **`v1/`, the backups of the 9 original sheets** (png, json and aseprite).
  A target with `mix > 0` whose render is missing re-renders itself, and that needs ComfyUI on :8188.
- **Do not re-run the old generators** for these sheets: `art/gen_xsb.py` (xsb_*), `art/dunes_props.py` (du_colossus, du_stele) and
  `art/necro_props.py` (nv_props, nv_bell*). They would overwrite this pass. `gen_xsb.py` also builds xsb_sky, xsb_icons and xsb_bug,
  which this pass leaves alone.

## Method (per target)
1. **Contract.** `L.rebuild(sheet, {tag: frames})` loads the v1 sheet, replaces only the reworked tags (the frame count is
   asserted), rebuilds through `asebuild.build`, and checks the tags, ranges, durations and frame size against v1. A full-sheet
   check after the final build gave: untouched frames identical to v1 on all 9 sheets, durations identical, and the json files
   unchanged (only the png and aseprite files differ).
2. **Guide.** Each frame is painted at 6–32x in frame coordinates, with real form lit from the upper left. Columns, jars, bells,
   braziers, helms and drums are bodies of revolution. The colossus head, the hand and the sun-wheel are sculpted height
   fields. The rest uses soft domes and planes. Volume comes from these, not from noise. Each part carries a material id, so it
   later snaps only to its own ramp (no stray hues).
3. **img2img** (bgv2 recipe): SDXL, pixel-art-xl and Lightning 8-step, ControlNet-union lineart from the guide's edges, and
   IP-Adapter "style transfer" from the region's new background at about 0.25. Denoise is 0.34–0.5. Only part of the render is kept
   (`mix` 0.1–0.5 over the guide), so the AI adds material such as stone grain, block joints and weathering, but never changes the
   silhouette or the anchors. The big back-layer paintings use the most (0.35–0.5). Small props use 0.1–0.25. A few pieces are
   guide-only (`mix 0`): du_stele, the headstones, bunk, kingskull and the bells. At those sizes the render only added noise.
4. **Down to 1x.** Premultiplied BOX downscale with the guide's own coverage as the alpha, so the grey key never bleeds. Then
   a light unsharp pass, a per-material palette lock, orphan cleanup, a 1 px outline (`#0d0806`/`#2a1a10` for the dunes,
   `#06060a`/`#14141e` for the necropolis, darkest on the shadow side) and a top rim (sun `#f4df9f` for the dunes, moon `#a8a6bc` for the necropolis).
   The back-layer `xsb_big` paintings and the colossus use an inner outline, so their footprint does not grow.
5. **1x detail** goes in after the lock, on the pixel grid, because carved detail does not survive a 20x box filter. This covers
   the hieroglyph columns (sunk mark plus lit lower-right lip), the dirge stave and its notes, eyes, skulls, crown gems, coin glints and the stele disc.
6. **Animation** never uses per-frame AI renders. Frame 0 goes through the pipeline and the rest are derived in code:
   - palms: fronds rotated about the crown
   - banner_du: column sway of the cloth (the pole stays)
   - brazier_du: a procedural fire layer per frame
   - du_stele: the sun disc breathing
   - bells: the clapper swinging under the lip, plus the cold strike sparks on frames 1–2 (same swing values as v1)
   - headstones: a drifting grave-light mote on the cross stone and the ghost-candle flame on headstone1

## Kept on purpose (preserve list)
| What | Where it lives | Kept as |
|---|---|---|
| obelisk tip light (`SB_LIGHT` y-92) | xsb_tall/obelisk | pyramidion tip at y 20 (frame 112) |
| jackal eye light (x+4, y-40) | xsb_du/statue_du | amber eye pixel at (28, 24), the head faces right |
| brazier fire light (y-30) | xsb_du/brazier_du | bowl lip at y 34, flames above it |
| scarab idol light (y-38), hoard (y-10), kingskull (y-20), headstone1 candle (x+9, y-9), nv statue (y-38), throne (y-50), stele (y-14) | | the sun disc, the gold, the skull, the flame at (33, 52–56), the hood glints, the pediment skull and the stele disc all sit on those points |
| DU11 cartouche centres (`sbInkTitles`: x0+26+i*46, y0+63) | xsb_big/titles | four rope ovals centred there, with plain dark fields so the inked glyph reads |
| the sealdoor's opening (the kit `gate` draws in it, DU13/DU14) | xsb_big/sealdoor | jamb inner faces at cx±8, opening left transparent |
| the dirge puzzle (NV12: five lines, lowest line = lowest bell, notes 0 2 1 4 3 0) | xsb_big/dirgeslab | same line rows (98, 91, 84, 77, 70) and the same note columns (x0+14+i*9) |
| sun-wheel position behind the DU13 mirror puzzle | xsb_big/sundial | same centre and radius |
| hang points | nv_bell, nv_bell_big | the bone yoke at the top centre (y 0) |
| bottom-centre foot rows | every standing prop | foot on the last row; sand drifts never go below it |

## What changed (per target)
**DU10 set (the owner's example).**
- `sunspire`: the toy striped pyramid is now a buried pyramid seen corner-on. The west face is sunlit and the east face umber.
  The lower courses are stepped where the casing is stripped, a smooth casing remains on top with a ragged edge, and the capstone is tarnished electrum.
  A small pylon shrine with a winged disc and a black door sits at its foot.
- `ruinarch`: a battered tomb gateway with sloped jambs and block courses, a cavetto lintel with a winged disc in faded lapis
  and tarnished gold (the cornice end broken off), a black doorway, and drifted sand.
- `obelisk`: a tapering shaft with a lit west face, a carved hieroglyph column, a chipped arris, a crack, a tarnished pyramidion and a stepped plinth.
- `ruincol` and `ruincol1`: fluted papyrus columns snapped off, with flaking lapis bands. ruincol also has a fallen drum.
- `statue_du`: a seated basalt Anubis in profile on a cavetto plinth, with a gold-inlaid collar and ear lining and an amber eye.

**du_colossus (DU3).** A weathered, toppled colossal pharaoh head sunk to the chin in the dune. It has a nemes with broad worn
bands, heavy-lidded closed eyes (no goggles), a broken-off nose, a crack through the brow, the uraeus snapped off, sand on the
crown, and a strong sunlit west side. It was sculpted as a height field, rotated 5°, then sunk.

**Small dunes props.**
- `jars` and `jars1`: storage jars, an amphora and oil jars in burnt umber clay, with painted bands, a cracked one, and shards.
- `crates`: dark cedar chests with bronze straps, an amphora and a roped linen bundle.
- `banner_du`: a tattered standard in faded indigo linen with a worn gold sun, ochre borders and a disc-and-horns finial.
- `scarabidol`: Khepri raising the sun on a pedestal.
- `hoard`: a slumped heap of tarnished gold with a gilt mask, an ewer, a casket and a canopic jar.
- `sarcophagus` and `sarcophagus1`: anthropoid coffins with nemes stripes, a calm face, crossed arms with crook and flail,
  and vulture wings. One is gilt and worn. The other is stripped to the gesso.
- `brazier_du`: a bronze bowl on lion legs.
- `palm`, `palm1` and `palm2`: date palms with ringed trunks, drooping fronds in dusty olive and dates.
- `palmdead`: a snapped, split trunk with dry fronds.
- `reeds 0–2`: the same pixels, recoloured from neon green onto the dusty palm ramp.
- `du_stele`: a round-topped stele with three glyph columns and a breathing sun disc.

**Other xsb_big.**
- `sealdoor`: battered jambs with glyph columns and a cavetto lintel with the winged eye.
- `sundial`: a carved sun-wheel relief. It has rings of hours, rays with lapis between them and a worn gilt sun face, and it is
  cracked with a wedge missing. It is darker than v1 so it backs the puzzle instead of dominating the room.
- `titles`: a carved frieze with four rope cartouches.
- `colossushand`: a colossal hand rising from the dune, with the little finger snapped and sand streaming through.
- `wagon`: a plank wagon with a torn linen hood over hoops and a smashed wheel, sunk in sand.
- `wagon2`: an overturned cart with a wheel to the sky and spilled jars.
- `dirgeslab`: a pointed stela with the dirge in ghost-light and mourners in relief.
- `gateleaves`: wrought-iron leaves with spear heads and scroll cresting. One sags on a broken hinge.
- Kept from v1: `camelbones`, `catafalque`, `tombwall` and `fence` (scored 3 in the audit).

**Necropolis.**
- `nv_bell` and `nv_bell_big`: true bell profiles in dark tarnished bronze (the olive green is gone). They have raised bands,
  an inscription band, a metal glint and a crack, with a skull clapper on the big bell.
- `statue`: a hooded mourner-knight with both hands on a sword's pommel and cold glints under the hood.
- `block`: an oak block with the headsman's bearded axe and a skull.
- `gallows`: a gibbet with a brace, a chain and a cage of bones.
- `throne`: a black gothic throne with bone spires, a pediment skull, skull armrests and a violet seat.
- `headstone`: a cracked cross stone.
- `headstone1`: a skull-relief stone with a bone ghost-candle.
- `dummy`: a pell with a straw body, a dented helm and a stuck blade.
- `bunk`: a plank cot with a thrown-back blanket and a skull pillow.
- `drum`: a rope-tensioned funeral drum with crossed femurs.
- `kingskull` and `kingskull1`: a crowned skull on a cushion and pedestal. In kingskull1 the crown is broken and the sockets glow ghost-blue.

## Evidence (`tools/shots/v17/props/A/`)
| Path | What |
|---|---|
| `contact_<sheet>.png` (9) | For every reworked tag: v1 frames, then the new frames (up to 4 per tag), with the player at the same scale |
| `game_du_before_after.png`, `game_nv_before_after.png` | 34 in-game spots in pairs (left BEFORE, right AFTER), same camera, shaders on, 19 dunes and 15 necropolis |
| `before/`, `after/` | the single 1152x648 captures |
| `snap.js`, `shoot.sh`, `montage.py` | `BUILD_OUT=web/dist/props_a.html python3 web/build_web.py; tools/shots/v17/props/A/shoot.sh web/dist/props_a.html tools/shots/v17/props/A/after [prefixes]; (cd tools/shots/v17/props/A; python3 montage.py ba du nv)`. The before set came from `web/dist/props_a_before.html`, built from the untouched sheets |

## Honest notes / what is still weakest
- Small props live at 12–25 px, so some read as "good pixel art" rather than painterly. The jars and the sarcophagi are the most
  compressed. They now have form, material and the region palette, but further work would mean hand-pixelling in Aseprite.
- The `kingskull` pair is still the brightest thing in its corner of NV15/NV16, because the props' own light hits the bone.
  A darker bone ramp would fix that if wanted.
- The `sundial` was darkened on purpose (the audit said it dominated DU13). If the puzzle needs it more visible, raise the 0.78 value factor in `big_sundial`.
- `xsb_nv/axestump`, `lamppost`, `cage`, `tombchest`, `mourner`, `rack` and the other v1 tags in these sheets were left as they were (scored 3).
