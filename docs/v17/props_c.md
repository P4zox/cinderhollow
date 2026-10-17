# Props rework, batch C: Thornveil, Starfall, Ember and Hermit (branch `bg-overhaul`), 2026-10-17

This is batch C of `docs/v17/PROPS_AUDIT.md`. 45 tags on 15 sheets were redrawn. One new sheet (`xsc_ruins`) was added, and it needed
one small code change, described below. Every other sheet keeps the v1 contract exactly: the same frame size, tags, from/to, per-frame
durations, frame order and anchors. A rebuild asserts this (`props_c_lib.build_sheet` re-reads the exported json and compares it with
the v1 json). Tags that are not in this batch keep their v1 pixels, and this was checked pixel for pixel:

- `xsa_tv`: `skullpost`, `antlers`, `rootcurtain` and `thornbed`.
- `xsc_s`: `glassgrass`, `grass`, `meteor`, `wellshard`, `ashpile`, and the Neohallow `dumpster`.
- `xsc_m`: the Neohallow `vending`, `watertower`, `devdesk`, `maglev`, and `chimes`.
- `xsc_l`: `fallenstar` (and its glow), `embertree` (and its glow), and `comet`.

`tv_tree`, `xsa_oak` and `xsa_elder` belong to the trees pass and were not touched. `art/treelib.py` is imported and was not modified.

## Deliverables
| Path | What |
|---|---|
| `art/props_c_lib.py` | The shared painter: a 4x supersampled canvas with dome, cylinder and facet shading, a 1x resolve, per-material ramp lock, rim light, selective outline, the v1-contract sheet builder, previews, and an optional ComfyUI texture pass |
| `art/gen_props_c_thornveil.py` | Builds `tv_fern`, `tv_shroom`, `tv_vine`, `xsa_tv` (12 tags) and `xsa_tvbig` |
| `art/gen_props_c_starfall.py` | Builds `sf_spire`, `sf_godbone`, `sf_idol`, `sf_lens`, `sf_arch`, `sf_orrering` and `sf_telescope`. It also makes the Starfall `xsc` tags (`emberrock`, `wayshrine`, `dome`) |
| `art/gen_props_c_ember.py` | Builds `xsc_m` (5 tags) and `xsc_l/hut` (8 tags), the small `xsc_s` set, and the new `xsc_ruins`. A plain run builds all three `xsc_*` sheets once, together with the Starfall tags |
| `art/bg_src/props_c/v1/` | v1 backups (png, json and aseprite) of every sheet touched. Gitignored. The generators read the untouched tags and the contract from here |
| `art/bg_src/props_c/preview/` | Previews per target: new frames next to v1 with the player at the same scale |
| `tools/shots/v17/props/C/contact_{thornveil,starfall,ember}.png` | Before/after contact sheets, 3x, with every reworked tag, v1 on the left and new on the right (`contact.py`) |
| `tools/shots/v17/props/C/ingame_{thornveil,starfall,ember}.png` | In-game before/after pairs for 30 spots (`ingame.py`). The raw shots are in `before/` and `after/`, and `snap.js` lists the spots |

To rebuild, run `python3 art/gen_props_c_thornveil.py`, then `python3 art/gen_props_c_starfall.py spire godbone idol lens arch orrery telescope`,
then `python3 art/gen_props_c_ember.py` (this one also writes the xsc sheets). Each script takes target names, and `--no-ase` writes previews only.
All three are deterministic and need no ComfyUI.
For in-game shots, run `BUILD_OUT=web/dist/props_c.html python3 web/build_web.py`, then
`SHOT_HTML=$PWD/web/dist/props_c.html node tools/shots/shot.js tools/shots/v17/props/C/snap.js tools/shots/v17/props/C/after`.

**Warning: the old generators would overwrite this work.** `art/gen_xsa.py` (its `build_tv`), `art/gen_xsc.py`, `art/thornveil_props.py`
and `art/starfall_props.py` still build the same sheets with the old art. Do not rerun them for these sheets, or retire their entries for them.

## Method, and why it is procedural rather than img2img
The audit's production method was ComfyUI img2img over a guide. The trees pass ended up procedural for the same reason this batch did:
most of these sprites are 16–48 px. At that size an SDXL render box-downscaled to the frame turns into mush, and then the palette lock
and cleanup rebuild the form anyway. So every target is modelled instead:
- Each part is a shape with real geometry: caps, rocks, pots and mounds are height-field domes, stems, ribs, posts and tubes are cylinders,
  and crystals and cut stone are flat facets.
- Light comes from the upper left, plus the region's own light: bioluminescence in Thornveil, cold starlight in Starfall, embers and firelight in the Ember.
- Each part is painted at 4x and resolved to 1x by majority material and mean value. Each material is locked to a hand-picked ramp with a light ordered dither.
- It is finished with a 1 px rim on the lit edges and a selective outline: dark on the shadow side, and a mix with the fill on the lit side.
- The tiniest foliage (`tv_fern`) is drawn straight at 1x, because a frond only reads as a 1 px rachis with 1–2 px pinnae.
- Bark (the root arch, the dead trees, the fungus stump, the nest bough) uses `treelib.Wood` with the tv_tree shade parameters and ramps. It therefore
  has the same fissured bark, moss on the up-facing sides and grey-green rim as the new trunks.

I tested the ComfyUI path (`props_c_lib.ai_texture` / `apply_ai`: tile ControlNet over the procedural colours, luminance
histogram-matched back) on the two biggest props, the hut and the godbone, with 2 seeds each. It added only a slight organic
variation to the thatch and bone. It also made the rebuild depend on gitignored renders, so I did not use it.
The helper stays in the lib, and the test renders are in `art/bg_src/props_c/sweep/` (gitignored).

Animated props keep their frames, and no frame is a separate render:
- `tv_vine`: rows shift sideways, more towards the tip; the pivot row never moves. Frames: rest, right, rest, left.
- `xsa_tv/fungus`: the glow cycles 1.3, 1.17, 1.04, 1.17, and spores drift.
- `xsa_tv/cauldron`: bubbles, flame heights and steam per frame.
- `sf_spire`: the cores breathe and a glint climbs the ridge.
- `sf_lens`: the caustic turns in the glass.
- `sf_orrering`: the inner rings rotate in true 3D, one geometry per frame.
- `xsc_m/hearth`: fire tongues with phase-shifted heights and sway on one geometry.
- `deadshrine`: the four heat states use the code's `n`: 0 means burning, 1 a dull glow, 2 cold, 3 toppled with the cap broken beside it.

## Anchors and lights preserved
Every standing prop keeps its foot on the frame's bottom row, so it stays bottom-centre. The hanging props `tv_vine` (pivot [8,0]), `xsa_tv/herbs` (SA_HANG) and
`xsc_s/hangingpots` (drawn at y+30) hang from the top row. These code lights did not move, and the art was placed under them:
- `tv_shroom` at y-10 sits under the caps' glowing gills.
- `fungus` at y-12 sits at the colony's gills.
- `cauldron` at y-18 sits at the brew surface.
- `sf_lens` at y-30 sits in the lens.
- `sf_spire` at y-18 sits at the crystal cores.
- `sf_telescope` at x+10, y-40 sits at the objective end.
- `wayshrine` at y-22 sits in the flame niche.
- `emberrock` at y-6 sits on the glowing veins.
- `dome` at x+10, y-50 sits at the slit and barrel.
- `deadshrine` at y-14 sits at the niche fire.
- `hearth` at y-16 sits at the fire.
- `hut` window: the light is at x+2, y-22, and the window spans x+6..17, y-32..-23. The chimney top was lowered to y-67 so that the smoke particle
  (x+18, y-64) leaves its mouth.
- `stonelantern` at y-12 sits in the fire box.
- `lantern` at y-10 sits in the paper body.

## Per target: before, then after (score against the audit's 1–5 bar)
### Thornveil (palette: the tv_tree bark, moss and rim ramps, plus prop ramps sampled from tiles_thornveil and bg_thornveil_mid)
| Tag | v1 | New | Score |
|---|---|---|---|
| tv_fern (32 uses) | green checker blob | an arching crown of fronds with alternating pinnae, light tips, darker back fronds, a fiddlehead | 2 → 4 |
| tv_shroom (25) | cartoon mint caps on beige sticks | a cluster of slender mycena with bell caps, translucent lower caps and glowing gill bands, pale stems, on a moss and soil base | 2 → 3.5 |
| tv_vine 4f | brown wobbly stick | a twisted woody liana with a second strand wound round it, paired ivy leaves that thin to a frayed tip, and a sway | 2 → 3.5 |
| xsa_tvbig/rootarch | flat brown inverted Y | a trunk out of the canopy splitting into two buttress roots in tv_tree bark and moss, with aerial roots, moss beards and floor mist | 2 → 4 |
| xsa_tv/fungus 4f | teal cartoon dome cluster | a rotten treelib stump with a broken top, a colony of glowing mycena, bracket shelves and a mossy limb; the glow pulses | 2 → 3.5 |
| mossrock, stones, stone_l, stone_s | flat grey shapes | domed and cracked stone with moss on the up-facing sides. The standing stones carry a carved spiral lit faintly by the forest spirit. The cairn is stacked flat stones | 2 → 3.5 |
| mossbank | flat speckled mound | a lit moss mound with fern tufts, tiny glowing caps and pale wood-sorrel flowers | 2 → 3 |
| nest | brown oval with eggs | a woven twig bowl with speckled eggs over its rim | 2 → 3 |
| herbs | coloured triangles | bundles of drying herbs: fanned stems tied with twine on a sagging cord | 2 → 3.5 |
| snare 2f | thin bar, then a triangle | f0 is an open ring of rusted jaws with teeth round a pan; f1 is the jaws sprung shut into a toothed arch, chained to a stake | 2 → 3 |
| shelves | rainbow boxes | a witch's shelf of flasks, bottles and lidded jars with glass highlights and a cobweb | 2 → 3.5 |
| cauldron 3f | cartoon pot with yellow flames | an iron cauldron whose belly is lit by the fire beneath, a bubbling green brew and steam | 2 → 3.5 |
| hide | a sack on sticks | a pelt laced into a frame of lashed poles | 2 → 3.5 |

### Starfall (palette: obsidian and starlight from tiles_starfall, bg_starfall_mid and vista_sf16; cool stone; cold ivory bone; tarnished bronze with verdigris streaks)
| Tag | v1 | New | Score |
|---|---|---|---|
| sf_spire 4f (17 uses) | saturated blue saw-tooth | black-glass prisms, each with a lit face, a dark face, a sky-lit termination and a cold core vein, in a glass pool | 2 → 4 |
| sf_godbone (9) | grey blobby horns | a dead god's vertebra (body, neural arch, raking spine, transverse wings) and three grooved ribs, one snapped, with starlight cracks and glass crystals grown through | 2 → 4 |
| sf_idol (6) | flat round face | a carved head from a sculpted height field: brow, closed lids, nose, lips, cheeks. The crown is chipped, starlight seeps through cracks, the halo is snapped, and the head is sunk to the jaw | 2 → 3.5 |
| sf_lens 4f | lollipop | a bronze stand with collars and a stepped foot. A clawed ring holds a dark lens with a turning caustic and a held star | 2 → 3.5 |
| sf_arch | bent pipe | a fluted observatory pillar with base and capital, voussoirs springing off it that break raggedly in the air, fallen fragments and starlit cracks | 2 → 3.5 |
| sf_orrering 8f | two flat rings | a broken armillary: three ribbon rings in 3D (bronze and verdigris, two of them with gaps) round a crystal heart on a sunk stone foot | 2 → 3.5 |
| sf_telescope | yellow tube | a banded bronze tube with dew-shield, eyepiece and cracked lens on an iron tripod | 2 → 3.5 |
| xsc_s/emberrock (11) | flat blue blob | a pitted meteorite with fusion crust and glowing blue-white veins | 2 → 3.5 |
| xsc_s/wayshrine | plain post with a light | a stone stele with a roof cap and a niche holding a cold flame | 2 → 3.5 |
| xsc_l/dome | flat dome of radial lines | a pale stone drum with pilasters, cornice and door, and a ribbed iron dome half fallen in, the night sky and stars showing through the hole. The barrel comes out of the slit | 2 → 3.5 |

### Ember and Hermit (palette: ash-grey basalt, char, ember and ash for the Ember; weathered timber, thatch, clay, hermit stone and warm glow for the Hollow)
| Tag | v1 | New | Score |
|---|---|---|---|
| xsc_m/deadshrine 4f | flat grey lantern box | a basalt wayside shrine with plinth, cracked body, a fire niche and a pitched cap, ash on its tops; the four heat states; when toppled the cap lies cracked in two beside it | 2 → 3.5 |
| xsc_m/deadtree 2f | stick Y | two charred trees in treelib bark with ember-lit cracks deep in the char and ash on the boughs | 2 → 3.5 |
| xsc_m/hearth 6f | flat grey box with stripy flames | jambs of fire-blackened blocks, a lintel and mantel beam with pots, a soot-stained back, firedogs, logs with live seams, and a coal bed with a 6-frame fire | 2 → 3.5 |
| xsc_m/pine | clip-art triangle | a dark fir: separate drooping, ragged tiers round a thin trunk, lit tops and shadowed undersides | 2 → 3 |
| xsc_m/shelves | flat boxes | a hermit's shelf of books (some leaning), clay pots, a bottle and a basket on top | 2 → 3.5 |
| xsc_l/hut | cartoon cabin | a dry-stone footing, plank walls with corner posts, a strapped door, a warm mullioned window, a steep shaggy thatch with moss and a stone chimney | 2 → 3.5 |
| xsc_s: lantern, jars, rug, embershelf, hangingpots, firewood, stonelantern, herbs | flat | a paper lantern on a crooked post; three clay jars; a worn striped rug with fringe; a stone fire-plinth with an ember bowl; copper pots and a ladle on a rail; a log stack showing end-grain; a stone lantern with a lit box; a planter of herbs and lavender | 2 → 3–3.5 |

## Code change (optional ruins item, done): `XS_KIND.ruins` now uses a sprite
`web/src/55_sc.js` changed by about 13 lines inside `XS_KIND.ruins`.
- **New sheet `xsc_ruins`** (24x16 frames, made by `gen_props_c_ember.py`). Tags: `shaft` (2 tiles that repeat seamlessly), `base`, `cap` and `broken` (2).
  The pieces are fluted basalt drums with joints and cracks, lit on the right edge by the ember glow.
- **Same columns as before:** the bake lays out exactly the same columns at the same positions, heights and alpha (0.75). It draws shaft tiles from
  `yt` to `yb`, the base at `yb-16`, and a capital or a broken top at `yt-12`. The cap/broken choice and the variant use the same `hash2` as before.
- **Fallback:** the old `fillRect` columns are still there. They are drawn if the sheet is missing.
- **If the image is still decoding at bake time:** the columns are painted into the same back layer when it loads, provided the room has not changed.
- **Pre-warm:** the spawn touches `sheet('xsc_ruins').img` early.
- **Effect:** in E4, E5 and E7 the colonnades read as carved basalt rather than flat bars. They stay deliberately dim, because they are back-layer dressing.

## Notes and leftovers
- **Floating deadshrines in E5.** The E5 deadshrine at (22,24), and the one at (84,6), stand on spawn rows with no floor directly under them. They float in v1 too.
  This is a room-data placement issue, so it is not in this batch.
- **Brightness.** The new Thornveil fungus and shrooms are deliberately less saturated than the mint v1. They read through their glowing gills
  and the code light. If the owner wants them to pop more, raise the `glow` factors in `fungus_frames` and `shroom_model`.
- **The before shot of TV11_east is missing.** The first before run teleported into TV9, so the in-game sheet shows 11 Thornveil pairs. TV11's
  fungus, shroom and fern are covered by TV11_west.
- **Nothing was committed, pushed or published.**
