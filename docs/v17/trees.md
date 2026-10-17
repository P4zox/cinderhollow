# Trees pass: the Thornveil's trees (v17, branch `bg-overhaul`)

The owner asked to improve the tree in the moss region, vista room included. Three sheets were rebuilt. Each one keeps its frame size,
tags and foot anchor, so no room data changed.

| sheet | frame | tags | where | before | after |
|---|---|---|---|---|---|
| `xsa_oak` | 256x224 | `motheroak` | TV14 Mossbed Glade (back prop, x19 y13, foot = bottom row) | round green bubbles, stiff straight sticks, a plain cone trunk | a gnarled, twisting trunk with deep fissured bark and moss; buttress roots spread over mossy stones; a long west bough sags over the bench, hung with moss curtains; the crown is built from clustered leaf masses over a hazy back dome, with gaps of glade light, a backlit rim and a few glowing spores |
| `tv_tree` | 96x240 | `v0` `v1` `v2` | 13 Thornveil rooms (giant back trunks, drawn 12 px under the floor) | smooth columns | fissured bark with wandering grooves, moss climbing the lit side, knots, flared roots, bracket fungus, a top that fades into the dark. **v0** leans east, with a broken limb stub and ivy. **v1** leans west and splits in two near the top; its hollow and ribbon are kept. **v2** has an S-curve sway, burls, a bough leaving the frame, and a glowing ogham line with spores |
| `xsa_elder` | 240x440 | `elder` + new `front` | TV9 The Elder Canopy | a flat cone with a black band and a box-shaped hollow | a massive fissured trunk with buttress ridges. The cleft the high walk passes through shows the heartwood, with a faint living glow. The hollow is now a pointed arch with the wardens' ribbons, and ogham marks are cut into the flanks |

In-game before/after: `tools/shots/v17/trees/before_after.png`. It shows TV14 standing, seated and at the east end, plus TV2, TV10 and the
TV9 Elder. The "before" column is the current build with only the three old sheets swapped back in, so other agents' prop changes appear
on both sides. Shots come from `tools/shots/v17/trees/snap.js` (`node tools/shots/shot.js tools/shots/v17/trees/snap.js <out>`). The
montage comes from `montage.py`.

## How it is made

`art/gen_trees.py` uses `art/treelib.py`. The approach is procedural, with an optional painted texture pass.

- **Wood.** A skeleton of tapering, wobbling Catmull-Rom branches is stamped as discs on a 4x grid. Each pixel keeps the cross-section
  it lies on: across-axis `u`, along-axis `v`, radius and axis. Bark is then shaded as a real cylinder:
  - long wandering fissures at constant angular spacing, so they crowd towards the edges;
  - gaps where two plates merge;
  - the far wall of each groove lit;
  - cross-cracks;
  - moss on up-facing and lit surfaces;
  - a 1-2 px rim.

  Child branches are drawn first and the trunk swallows their roots. Leaders use `under=` so they grow out of the trunk without a seam.
- **Foliage** (`Leaves.lobe`). Each lobe is split into sub-masses filled with small scalloped clumps in a z-buffer. Value is the lobe's
  light, plus the sub-mass's light, plus each clump's own lit crescent, minus cavities (AO from the height field). Clumps therefore read
  as leaves rather than balloons. Sky gaps are ragged clusters of bites. Small dapples get neither an outline nor a rim.
- **Resolve to 1x.** Shading is locked to hand-picked ramps (`OAK_*`, `TV_*`, `ELD_*`, all in Thornveil's cold greens and umbers) with a
  narrow ordered dither. The crown is rimmed from the glade behind, and a 1 px outline is drawn on the open silhouette only. Moss
  strands, vines, spores, fungus, ogham, the hollow and the cleft are then painted at 1x.
- **Painted texture pass** (oak and trunks). The model's colours are composited over a backdrop at 4x and sent through ComfyUI img2img
  (SDXL, pixel-art-xl, Lightning, tile ControlNet from the guide itself, so nothing moves). Prefix `trees/`. The output is brought back
  to 1x. Its luminance is **histogram-matched to the model's values** and blended in (oak 0.75/0.6, trunks 0.55), so the model keeps
  the value design and the painting adds organic texture and moss. The Elder is purely procedural.

Files:
- `art/bg_src/trees/` (tracked):
  - the 1x results: `motheroak.png`, `tv_tree_v0..2.png`, `elder.png`, `elder_front.png`;
  - the guides the renders were made from: `guide_oak.png`, `guide_tv0..2.png`.
- Gitignored:
  - `*_render.png` (the painted passes);
  - `sweep/` (study renders);
  - previews in `art/previews/trees/`.

```
python3 art/gen_trees.py [oak|trees|elder ...] [--no-ase] [--render] [--procedural]
```

Without its cached render, the oak or trunk build **refuses** rather than silently shipping procedural colours. Use `--render` (ComfyUI
on :8188) to repaint, or `--procedural` to build without the pass. With the renders present, a rebuild is byte-identical.
`gen_xsa.py` (`motheroak()`, `elder_frames()`) and `thornveil_props.trees()` now load these PNGs, so re-running the old generators
reproduces the new art instead of the old.

## Engine change (one, in `web/src/53_sa.js` `saPaintSkins`)

The Elder's solid column (TV9 cols 52..59, `skins` look `elder`) used to be tiled 16x16 bark that matched nothing. It now draws the
**`xsa_elder` `front` frame**, the same tree lit as the solid trunk, cell by cell at the prop's placement. The column therefore *is*
the Elder. The column edges (frame x 47..49 and 174..176) get a dark seam with a lit or shaded edge, so the solid wall still reads
against the back-prop flare. If the sheet has no `front` tag, or a cell falls outside the frame, the old tiles are used. Nothing else
uses the `elder` look.

## Notes and hand-offs

- **Ownership overlap.** `docs/v17/PROPS_AUDIT.md` lists `xsa_elder` under props batch C. My brief also asked for it (same treatment),
  so it is done here with treelib, matching the new trunks. If batch C rebuilds it with a single tag, the column falls back to tiles
  safely.
- **Shared library.** `art/props_c_lib.py` (batch C) imports `art/treelib.py`. Changes to treelib's shading change their rootarch and
  roots too.
- **Not touched:**
  - the `bark` skin tiles (the solid trunk columns in TV9 and other rooms);
  - `xsa_tvbig/rootarch` (batch C);
  - TV14's vista backdrop (V2: `85v_v2.js`, `vista_tv14_*`).
- **Seated view.** The oak's top ~33 rows sit behind TV14's leaf ceiling. The crown is composed so the visible part (rows 33-115, and
  rows 72+ when standing) carries it.
