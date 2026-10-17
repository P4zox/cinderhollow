# Prop rework, batch B: Crimson + Barrows (branch `bg-overhaul`), 2026-10-17

Batch B of `docs/v17/PROPS_AUDIT.md`. Every target in the batch was redrawn: the Drowned Saint, the rose window, the
family portrait, 23 `xsa_cm` furniture tags, the fallen chandelier, the four base `cm_*` sheets, 11 `xsa_db` tags and the
Drowned Bell. No game code changed, and every sheet keeps its frame size, tag names, frame ranges, per-frame durations and
anchors. Nothing was committed, pushed or published.

## Results
| Sheet / tags | Rooms | Before | After |
|---|---|---|---|
| `xsa_saint/saint` 176x416 | DB10 | Flat teal robe, stepped plinth, blank face | A veiled marble saint. She has a sculpted face with closed eyes, brow, nose and mouth, and a mantle with radiating folds. Her raised forearms rise out of hanging sleeves, and a waist cord ties a long skirt of fanned folds that pools on the plinth. The bronze halo is the perch. The plinth is carved with a wave frieze. Algae grows in the hollows and on the ledges below the waterline, and barnacles cluster at the base |
| `xsa_rosewin/rosewin` 160x160 | DB10 | Flat vector circles | Moulded stone ring with 12 spokes, foiled roundels with cusps, pointed heads and a carved boss. The glass is grouped by zone (pale-teal roundels, deep-teal lancets, cold-blue ring, muted amber heart) with lead cames and a few broken panes |
| `xsa_portrait/familyportrait` 80x64 | CM13 | Three flat silhouettes in an orange frame | A dark oil painting in a carved gilt frame (roll, channel, acanthus torus, bead row, corner bosses, crest), in the style of `cm_portrait`. The Count in black rests his hand on her chair. The Countess in varnished crimson has two red points for eyes. The child in white lace stands to the side. All are lit by a candle from the left, with dim faces, dark eye hollows, a curtain swag and a column |
| `xsa_cm`: bookcase, bookcase_fallen, books, bed, wardrobe, hearth (3f), bellboard, desk, globe | CM9, CM14 | Rectangles, rainbow stripes | Carved mahogany with grain and bevels. The bookcase has fluted pilasters, a cornice and crest, and books with gilt bands, some leaning. The bed has a carved headboard, white linen and a velvet coverlet with folds and gilt fringe. The wardrobe has arched panels and a broken pediment. The hearth is a red-black marble surround with an animated fire. The bellboard has brass bells on springs and name plates. The desk has a candle |
| `xsa_cm`: cot, stove (2f), lamp_cm (4f), laundry, roses, pipes, piano, chimney, weathervane, gutterspout, bust, rug, canvasback, spyhole | CM10–CM17 | Flat | Iron cot, cast-iron range with a kettle and glowing grate, caged lantern, linens with folds and pegs, dead roses in a stone urn, bracketed pipes with a rusted valve, black-lacquer grand piano, brick stack with pots, iron crow vane, gargoyle spout, marble bust with a face, easel with eyeholes, lit spyhole |
| `xsa_chand/fallenchandelier` 112x64 | CM9 | Flat gold ring with spikes | Crushed gilt hoop with a toppled hub, a crumpled inner tier, snapped arms with candles, hanging crystals, debris across the floor, and slack chains |
| `cm_table`, `cm_coffin` (closed/open), `cm_winerack`, `cm_barrel` | CM5, CM6, CM9, CM11, CM13, CM15 | Flat black blocks | Black velvet cloth with a damask crimson runner, a silver candelabrum (still lit at y-26), goblets, a decanter and spilled wine. Lacquered coffins with gilt trim and handles; the open one shows its red lining. A rack of green bottle ends with foil seals and two broken, dripping bottles. A cask on chocks with hoops, a brass tap and a wine stain |
| `xsa_db`: pew, pearlclam (4f), coral, tomb, tomb_leak, tidemark, sluice, gravestone, gravecross, cairn, wellcover | DB10–DB17 | Flat teal, cartoon clams | Rotted pew with poppyhead ends. A fluted giant clam that opens on its glowing pearl. Branching and fan coral. A coped chest tomb with quatrefoil panels; the leaking one has a glowing crack and pool. A bronze-graduated tide post. A sluice with a gate, spindle and rusted wheel. A round-headed headstone with an hourglass, a ringed cross, a cairn with a bone marker, and an iron well lid |
| `xsa_bell/bigbell` 64x80 (hung) | DB17 | Dithered cone | A true bell profile (crown and headstock, waist, flared sound bow, lip) with a dark mouth, an inscription band, mouldings and verdigris streaks |

Self-scores next to the player and the cfa props: saint, rose window, portrait, wardrobe, bookcase, bed, hearth, desk, globe, piano, bust and bell come to 4. The rest come to 3.5–4. The weakest are the small wall pieces (spyhole, rug) and the cot, which are simple at their size. All of them beat their originals in game.

Kept pixel-exact from v1 (scored acceptable, not in the batch): `xsa_cm` grandclock, crows, trellis, chalk and `xsa_db` weeds,
chainlamp, candles_db. `xsa_lagoon` (optional) was not touched.

## Evidence (`tools/shots/v17/props/B/`)
| Path | What |
|---|---|
| `contact_crimson.png`, `contact_barrows.png`, `contact_saint.png` | Each reworked tag, all frames, with v1 above and new below, at 3x (2x for the saint), with the player at the same scale |
| `ba/<spot>.png` (30) | In-game before/after at 1152x648 in the same spots (before on the left). Before = a build of the v1 sheets, `web/dist/props_b_before.html` |
| `ba_montage_crimson.png`, `ba_montage_barrows.png` | All of those pairs at half size |
| `game_before/`, `game_after/` | The raw captures |
| `snap.js`, `contact.py`, `pairs.py` | To reproduce, run `BUILD_OUT=web/dist/props_b.html python3 web/build_web.py`, then `SHOT_HTML=$PWD/web/dist/props_b.html node tools/shots/shot.js tools/shots/v17/props/B/snap.js tools/shots/v17/props/B/game_after`, then `python3 tools/shots/v17/props/B/contact.py` and `python3 tools/shots/v17/props/B/pairs.py` |

## How it is made
- **`art/props_b_lib.py`** is a small 2.5D relief painter. Each prop is modelled at 4x (3x for the saint, 6x for the portrait) as parts. A part has a mask, a material ramp, a value within the ramp, a height profile (round bevel, dome, cylinder, sphere, lathe-turned, or explicit fold/feature fields) and a texture (wood grain, stone, speckle).
  - `light()` turns the height field into normals. It adds a key light, ambient light, cavity occlusion, a cast-shadow march, a rim and an optional point light (candle, fire, pearl). Fire, glass glow, the pearl and the leak are unlit emissive parts.
  - `pixels()` box-downscales to the frame and takes the majority material per pixel. It quantises the value to that material's ramp (light ordered dither only), removes orphans, lifts the top/left silhouette edge one step, drops the bottom/right edge one step, and adds the 1 px exterior outline (`08070c`, one step lighter on the lit side).
  - Helpers: `box`, `panel` (raised or arched fields), `turned`, `flame`, `rotate_rel`/`crop_rel` (the toppled bookcase), `build_sheet`, `contact`.
- **Contract.** `build_sheet()` takes the frame size, tags, ranges and per-frame durations from the v1 export and rebuilds through `asebuild`. It then asserts that the new json matches. Every `assets/*.json` of the batch is byte-identical to before (git shows no json change).
  - The foot row stays at the frame bottom. `laundry` and `bigbell` keep their top-centre hang point.
  - The light offsets are respected: the desk candle is at x+8, y-30; the table candelabrum at y-26; the lamp flame at y-28; the hearth fire at y-16.
- **Palettes.** `art/props_b_crimson_pal.py` holds the crimson ramps: mahogany, crimson, olive gilt, mauve iron and stone, red-black marble, linen, pale marble, bottle glass and fire. They are sampled from `cm_portrait`, `cm_statue`, `cm_candelabra`, `cm_sconce` and `tiles_crimson`. The barrows ramps are in `gen_props_b_barrows.py`: teal stone, verdigris, algae, bone, drowned wood, bronze, shell and pearl, from `tiles_barrows`, `db_statue` and `db_lamp`.
- **Light.** Crimson uses the manor's candle key from the upper left. Barrows uses cold light coming down through the water. Both were brightened after the first in-game check, because the rooms' darkness and water tint swallowed the first pass.
- **Animated tags** model frame 0 once and rebuild only the flames or glow per frame: hearth 3f, stove 2f, lamp_cm 4f (0,1,2,1), pearlclam 4f (shut, then open with a pulsing pearl). Frame counts and durations are the originals.
- **The AI pass (ComfyUI)** is `ai_detail()`. It runs bgv2 img2img (SDXL + pixel-art-xl + Lightning, lineart ControlNet, prefix `props_b/`) over the lit preview. It then folds only the render's high-frequency light/dark detail back into the value map, so the silhouette and materials never move.
  - **Finding:** on the saint it destroyed the face (robot head, open mouths) and smeared the folds into camouflage mottling at every setting tried (denoise 0.3–0.5, pixel LoRA 0–0.55, Illustrious checkpoint, ControlNet 0.65–0.85).
  - The saint and all the furniture are the relief model alone. The AI detail is used at low weight on the family portrait (painterly brush texture, with the faces and frame masked out) and on the rose window (glass texture).
  - Renders are cached as `art/bg_src/props_b/{portrait,rosewin}_render.png`. `--render` regenerates them, and a fresh render may differ slightly.

### The DB10 saint (preserve list)
She is painted into the back layer and also clipped over DB10's solid cells, `rect 36,13,11,25`. Those cells are cols 38–44 × rows 15–32 (the body, sprite x 32–143, y 48–335) and cols 36–46 × rows 33–37 (the plinth, x 0–175, y 336–415). The new silhouette covers 95.6 % of the body cells (v1: 84 %) and 98.3 % of the plinth cells (v1: 94 %), so less tile art shows through than before. Her draped sleeves and veil fill the gaps between the arms and the head. The halo's front rim sits on the row-14 perch (sprite y 32), and the waterline (row 18, y 96) is where the drowning starts.

## Files
- **Generators:** `art/gen_props_b_saint.py` (saint and rose window), `art/gen_props_b_portrait.py`, `art/gen_props_b_crimson.py` (`xsa_cm`, `xsa_chand`, `cm_table`, `cm_coffin`, `cm_winerack`, `cm_barrel`; takes `--only tag,...` and `--nobuild`) and `art/gen_props_b_barrows.py` (`xsa_db`, `xsa_bell`). Each is deterministic: a rerun reproduces the committed pixels.
- **Libraries:** `art/props_b_lib.py` and `art/props_b_crimson_pal.py`.
- **v1 backups** (tracked; the generators read the contract and the kept tags from them): `art/props_b_v1/` holds the png, json and aseprite of all 11 sheets.
- **Renders, guides and previews** are in `art/bg_src/props_b/`. `.gitignore` gained `art/bg_src/props_b/`.
- **Rebuilt:** `assets/{xsa_cm,xsa_portrait,xsa_chand,cm_table,cm_coffin,cm_winerack,cm_barrel,xsa_saint,xsa_rosewin,xsa_bell,xsa_db}.png` and the matching `art/*.aseprite`.

## Flags for the owner
- **Stale generators.** `art/gen_xsa_cm.py`, `art/gen_xsa_db.py`, `art/crimson_env_props.py` / `gen_crimson_env.py` still draw the v1 art. Running any of them overwrites this batch, so they should be retired or pointed at the new generators. They were not edited.
- **Portrait gaze eyes (pre-existing, not changed).** The CM13 gaze eyes (`saDrawGaze`, eyeY = 7·16+4−6 = 110) are drawn 2 px above the portrait's top edge (sprite top = 112). That happens because the portrait spawns at y 10 while the gaze spawns at y 7. The painted Countess's eyes sit at sprite (38.6/41.4, 15), which is screen y ≈ 127. The glow would need to come down about 17 px (and in about 2 px) to land on them. That is a room-data/code change, so it was left alone.
- **Changed footprints.** `bookcase_fallen` now lies across most of its frame (x 5–64) instead of the v1 corner (x 24–64). It reads as a toppled case with books spilled in front. `cm_coffin` closed sits 1 px lower (its foot is the same as `open` now).
- **Ignored tooling.** `tools/shots/*/*/` is gitignored, so `snap.js`, `contact.py` and `pairs.py` here, like the audit's own tools, are untracked unless they are force-added.
