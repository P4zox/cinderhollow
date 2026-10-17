# v17 vistas, agent V3: SF16, SF17, NH15, E6, H3, CT2 (branch `bg-overhaul`), 2026-10-17

Brief: `docs/v17/VISTA_BRIEF.md`. Each of the six bench rooms now has its own painted view. The view replaces the biome
parallax (and the old `xsc_bg_*` overlay from `55_sc.js`) in that room only. After the lead review, revision 2 redrew the NH15 Root and the E6 taproot and columns, and revision 3 reshaped the E6 taproot. All six beat the old views standing and seated
(montage: `tools/shots/v17/vista/v3_before_after.png`. Columns: before / after standing, then before / after seated with
the lore panel hidden). Nothing committed, pushed or published.

## Files
| File | What |
|---|---|
| `web/src/85v_v3.js` | `vistaRegister` for the six rooms, their `fx` motion, `v3At()` (maps a point painted in a layer to the screen the way `vistaLayer` places it), the E6 `w2:open` layer swap, and per-room `GFX_SUN` overrides swapped on room entry (NH15 only, see below) |
| `art/vista_v3lib.py` | V3 helpers on top of `bgv2lib`: `seg_field` (per-pixel across/along coordinates of tapered limbs, for crisp trunks and roots), `Canvas` (guide painter for any layer size, no wrap), `use_prefix` (ComfyUI outputs go to `output/vista_v3/<room>_*`), `render`/`sweep`/`pick`, `pixelize` (palette lock + accents + Bayer dither on flat areas + orphan cleanup), `cover_alpha`, `fill_under` (the sky behind a cut-out layer), `knee` (soft highlight knee), `patch_rows`, `stars`, `draw1x`, `build` (asebuild, tag `loop`), `preview`, `cli` |
| `art/gen_vista_{sf16,sf17,nh15,e6,h3,ct2}.py` | per room: guides, prompts (`RENDER`), post and grade, build. `python3 art/gen_vista_<r>.py` rebuilds the assets from the saved renders. Other modes: `--guide`, `--sweep <layer> 1,2,3 [tag]`, `--pick <layer> <seed> [tag]` (copies the pick to `<layer>_render.png`), `--no-ase` |
| `art/bg_src/vista_<r>/` | guides, covers, edges, `out_*.png`, `preview*.png`. `*_render.png` and `sweep/` are gitignored by the existing rules (`art/bg_src/*/*_render.png`, `art/bg_src/*/sweep/`). The build needs `*_render.png` locally; without them, re-sweep and re-pick the seeds listed below |
| `assets/vista_<r>_<layer>.png/.json` + `art/vista_<r>_<layer>.aseprite` | 21 sheets: `sf16_{sky,ridge,near}`, `{sf17,nh15,h3,ct2}_{sky,far,mid}`, `e6_{sky,far,mid}` + `e6_{sky,far,mid}cold`. All are 512x240, 1 frame, tag `loop`. Sky layers are opaque; the others have binary alpha |
| `tools/shots/v17/vista/<room>/` | `before_*` / `after_*`: `_stand`, `_seat` (with the lore panel), `_seatclear` (lore panel hidden). E6 also has `_low_*` (w2:open). CT2 also has `_gate_stand` (east end) |
| `tools/shots/v17/vista/v3/` | `snap.js` (standing + seated per room, run through `tools/shots/shot.js`), `before/`, `after/`, iteration shots `it1..it11/` |

The rebuild is deterministic: rerunning the six generators reproduces all 21 PNGs md5-identically.
Test bundles: `web/dist/vista_v3.html` and `vista_v3_before.html` (dist is ignored).

## Layout facts (all rooms)
- Layers are 240 tall and bottom-anchored, so there are 24 px of extra sky. I measured each room's camera at the bench
  (standing cam.y; seated `sysVistaView` y0, which rises up to 160 px into the sky). Each layer's `dy` keeps the painting
  covering the frame in both views (no tint band at the top or bottom).
  - SF16: cam.y 70, seated −58
  - SF17: 54 / −92
  - NH15: 104 / −60
  - E6: 72 / 0
  - H3: 8 / 0
  - CT2: 344 / 116
- Scroll factors are low (sky 0.02, far 0.05, mid 0.08–0.16). These are small rooms (cam.x ≤ 192 except CT2), so the
  focal point stays where it was composed.
- The seated parallax is drawn at screen scale with cam = the view's x0/y0, so `fx` that uses `v3At()` stays on its painting
  in both views.
- No figures in any layer. Seeds with figure-like shapes were rejected, and two lens-flare orbs in SF17 were patched out.

## Per room
**SF16 The Stargazer's Seat: night, looking up.** The galactic arch climbs out of the far ranges at the left and crosses the
whole sky, with its warm core low over the mountains, dust rifts, and violet and teal nebula pockets (put back in post
because the render greyed them). On the far crest is the astronomers' road: two observatory domes stamped crisp at 1x
(drum, cap, shutter slit; the right one still lit, with a lit door) and a snapped tower. Glass spires are in the near dark.
Stars are crisp 1 px stamps, dense in the band. fx: stars that breathe, and rare small far meteors from the top of the
arch (the room's own `meteorshower` prop is still the near shower). Seeds: sky `b4` (denoise 0.55, pix 0.45), ridge 2,
near 2.

**SF17 The Crater Edge: first light, looking out.** This view is deliberately unlike SF16: low, wide, dawn instead of night.
- Sky: a rose-gold band on the horizon under lit stratus, the last stars and a morning star.
- Crater: the black glass plain mirrors the dawn. In its heart, the fallen star is a cluster of blue shards with a column
  of cold light rising into the morning.
- The left crag carries the shattered observatory (broken drum, dome ribs and a canted telescope, drawn crisp at 1x).
- fx: the heart breathes (glow and column swell), frost motes rise off it, and glints tremble in the dawn's reflection.
- Seeds: far/mid `b5`. The sky layer is the far render with the land cut out.
- I tried a `GFX_SUN` override toward the dawn and reverted it, because the rays washed the frame. Starfall's default stays.

**NH15 Neon Skyline: the city in the rain, the Root through it** (revised after the lead review). Neohallow's neon
identity is kept: magenta/cyan/amber neon, rain, lit windows.
- The far plane is a rain-hazed city (render, far `fard` seed 1, denoise 0.45, pix 0.35, saved as `far_render.png`).
- **The Pale Root is drawn crisp at 1x** over that render (`draw_root`, geometry `root_chains(long=True)`), using the
  shared `seg_field` helper (per-pixel position across and along each limb). It reads as a colossal ancient tree the city
  grew around:
  - Dark violet-grey bark that never glows by itself: an 8-step ramp topping out at `#4a4068`.
  - Furrows and lit ridges that follow the limbs.
  - Neon rim light, cyan on the left edge (the cyan district) and magenta on the right, stronger toward the city below,
    plus a magenta up-light on the lower trunk.
  - A flared foot with four buttress roots standing among the towers, in front of the far tower row.
  - Rain haze dithered in at its base only. Three limbs and the crown are cut away by streaky cloud strata that thicken
    with height, so they disappear into the cloud deck.
  - The render's own soft trunk is removed from the layer, so it never shows through.
- The mid towers are drawn procedurally as crisp pixel art: dark glass, a neon-lit edge, windows lit floor by floor, crown
  bands, abstract glyph signs with no letters, and antenna masts.
- fx: two searchlights sweep the cloud deck, rivers of light (tail and head lights) cross three sky lanes, red aviation
  lights blink, and the signs stutter.
- **`GFX_SUN.neohallow` is overridden to strength 0.08 in NH15 only** (`V3_SUN` in `85v_v3.js`, swapped on entry and
  restored on leaving). At 0.25 the god-ray pass bloomed the pale trunk behind the standing player to white. The trunk is
  dark now, but the override stays: the city's light comes from below, not from a sun.

**E6 The Last Hearth: the ember hollow through the broken window** (revised twice after the lead review).
- The view: one massive gnarled taproot of the Pale Root comes down out of the vault into a molten lake, with smoke banks
  lit from below and basalt column groups at two depths.
- **The root and the columns are drawn crisp at 1x** over the render (`draw_taproot`, `draw_columns`; geometry in
  `taproot_chains`, `far_columns`, `near_columns`).
- **The root (revision 3):** the revision 2 root crown read as a giant spider, so it was replaced.
  - One continuous trunk, leaning slightly, off-vertical and asymmetric. It is gnarled (its girth swells and pinches) and
    tapers from about 58 px wide at the top of the frame to about 22 px at the lake, with no bulge.
  - The trunk itself plunges straight down into the lava. A long root parts from its left flank high up, a short one low on
    the right, and both drop straight down into the lava.
  - Three thin rootlets hang and trail from its flanks, ending in the air.
  - All of it is cut at the waterline, with a bright meniscus and a dark rippled reflection under each of the three feet.
  - Kept from revision 2: a near-black backlit silhouette with furrows, ember-lit edges brightening toward the lake, and a
    few thin broken fissures glowing hotter toward the lake.
  - The render's old painted roots are cleared from the layer (the old guide's root area, x 36..180 above the lake), so the
    sky layer's haze shows there instead.
- **The columns:** faceted, with a lit facet toward the glow, a mid facet, a dark facet, a lit cap, joint lines, and lake
  light at their feet.
- fx: the root's foot breathes in the lake, sparks climb its flank, and ash drifts.
- **After `SAVE.flags['w2:open']`** (the hearth burns low, `82_forge.js`), the layer set switches to `vista_e6_*cold` (a
  getter on `layers`). It has the same shapes with a cold colour set:
  - Ash-grey and dull red, a cold root, dead fissures, a grey meniscus.
  - A thin pale cold light lies on the horizon right of the root, "from wherever that draught comes from".
  - fx: no breathing glow and no sparks, and the ash falls thicker and grey.
- Seeds: far/mid `b4`.

**H3 The Hermit's Garden: dusk over a mountain lake, through the long window.** The sun has just gone into the notch
between two peaks. Its gold pools there and runs down the lake as a path, with mist on the water line, rose and violet
stratus, the first stars, and dark spruce on the near slopes (mostly hidden by the window). This is one framed, deep,
quiet view, unlike the region's wide banded dusk. fx: the sun's path shivers on the water, stars breathe, and a few
fireflies drift over the slope. Seeds: far/mid `b5`. The Pale Root arching over the range (the region's motif) was tried:
every render turned it into a rainbow, so it was dropped from this view. The region's own backdrop keeps it.

**CT2 The Last Gate: the World 2 vista. The beyond stays vague.**
- A pale storm ceiling in long strata over an abyss of mist. Ahead, the cloud thins over a light with no source: a tall
  glow, rays rising up into the cloud, and a few impossibly tall pale shapes in it that could be spires or cloud.
  Behind you, the old causeway recedes into the mist on broken piers, with obelisks along it.
- The light sits at sky x 331. Standing, it barely moves on screen across the whole 1472 px room ("it does not seem to get
  nearer"). Seated, it stands exactly behind the gate prop (`cfa gate2`).
- fx (`SYS.vista.k`): as you sit, the light opens up. A tall breathing glow and rays rise around and above the gate's dark
  silhouette, so the gate is lit from behind. Far ash rises and is drawn in toward the light ("as if the world beyond were
  breathing in").
- The painting is held a step lower in value with a highlight knee. The threshold room light makes a dithered disc around
  the player on a pale sky (present before too); this keeps it softer. I tried lifting CT2's ambient (0.3 → 0.16), which
  only washed the room out, so it was reverted (`V3_AMB` is empty).
- Seeds: far/mid 4.

## Engine / shared edits
- None outside `web/src/85v_v3.js`. The per-room `GFX_SUN` swap (NH15) lives there and restores the biome entry on leaving.
- `art/vista_v3lib.py` is new. `bgv2lib.py` is unchanged.

## Caveats (honest list)
- Pixel density is the rollout's painterly 2–3 px look, with crisp 1x hand-drawn details (domes, observatory ruin, NH15
  towers and Root, E6 root and columns, stars).
- NH15 and E6 crisp passes: the render's old softer root shapes are removed from the far layer in both rooms.
- E6: the guide (`guide_far.png`, `cover_far.png`) still holds the original root geometry the render was made from. The
  build uses it only to clear that area. A future `--guide` re-render would paint from the current `taproot_chains`.
- E6's view mostly shows through the hall's back-wall veil. The `w2:open` version is intentionally dark, but the root keeps
  its silhouette. The cold horizon light is subtle and reads best seated.
- CT2 standing still shows the threshold lighting's dithered player-light disc. It is part of that biome's lighting, not the
  painting.
- `art/bg_src/vista_*` hold 11–23 MB each, mostly `sweep/` and `*_render.png`, which are both already gitignored.
- ComfyUI on :8188 was down when I started, so I started it (`~/ComfyUI/run.sh`). I did not stop it. All my outputs are under
  the `vista_v3/` prefix.
