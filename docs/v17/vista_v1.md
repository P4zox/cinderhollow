# v17 vistas, agent V1: R11, K11, M14, A14, HF14, SP15 (branch `bg-overhaul`), 2026-10-17

Brief: `docs/v17/VISTA_BRIEF.md`. Each of the six bench rooms now has its own painted view, registered through the
`85_vistas.js` hook. **Montage:** `tools/shots/v17/vista/V1_before_after.png`. It shows each room in game with shaders on:
before on the left, after on the right, and each pair is standing at the bench and then seated (about 2.8 s after sitting,
lore card hidden). Single shots are in `tools/shots/v17/vista/<room>/{before,after}_{stand,seat}.png`. SP15 also has
`SP15_flash_{stand,seat}.png`. Nothing has been committed, pushed or published.

## Files
| File | What |
|---|---|
| `web/src/85v_v1.js` | Registers the six vistas and their fx. Shared helpers: `v1At` (painting px to screen), `v1Zoom` (the seated view's zoom, for fx anchored to room props), `v1Flakes`. It also holds the per-room overrides listed below |
| `art/vista_v1_lib.py` | V1 pipeline on top of `bgv2lib`. `CAMS` holds the measured camera ranges per room. `place`/`geometry` check that a layer covers the screen at every camera extreme (all six pass). Also: `VG` guide painter (no wrap), `sweep`/`pick` (ComfyUI prefix `vista_v1/<room>`), `kpal` + `pixelize` (BOX down, palette lock with flat-only Bayer dither, majority), `ase`, `comp_preview`, and the shared `cli` |
| `art/gen_vista_{r11,k11,m14,a14,hf14,sp15}.py` | One generator per room: guide, prompts, `RENDER` picks, post, build. CLI: none (build), `--guide`, `--sweep <layer> 1,2,3 [--dn --cn --pix --tag]`, `--render`, `--no-ase` |
| `art/bg_src/vista_<room>/` | Guides, edges, alpha masks, `out_*.png`, `preview.png`. `*_render.png` and `sweep/` are gitignored by the existing patterns |
| `assets/vista_<room>_*.png/.json`, `art/vista_<room>_*.aseprite` | 12 sheets, tag `loop`. hf14_aur has 2 frames; every other sheet has 1 |
| `tools/shots/v17/vista/` | `snap_v1.js` (stand + seat per room), `snap_one.sh`, `cams_v1.js` (camera ranges), `flash_v1.js`, `montage_v1.py`, `_before/`, and the per-room folders |

Every layer is a single painting rather than a tile (`wrap: false`), sized to the room's measured camera range, so there are no
wrap seams. The rebuild is deterministic: running all six generators twice gives md5-identical assets. Method as in the pilot:
a painted guide at 3x, then SDXL + pixel-art-xl 0.45–0.55 + Lightning img2img with ControlNet lineart, then palette lock. The
palette is 36–48 k-means colours from the painting itself, plus explicit accent colours (stars, flames) that k-means drops.

## Per room
- **R11 Watcher's Perch (ramparts):** the Hallow at last light. A violet-to-ember dusk sky and a valley drowned in mist. On the
  horizon the Pale Root stands as a colossal pale tree lit from within, with the Hallow's spires at its foot. The wall and its
  signal fires wind toward it, and there is a castle crag on the left (lore ra_1: "a pale light rose … and did not set").
  - Layers: far 432x240 (fac 0.02) and mid 432x240 (crags, wall, watchtower; fac 0.12).
  - fx: lit cloud wisps, a slow breathing of the Root's light, beacon flicker, rolling mist bands and warm falling ash.
  - Every seed rendered the trunk as a white beam inside a glow band. `far_post` removes the band, and `paint_trunk` repaints
    the trunk at 1x as a tapered ivory tree that is brightest at its heart.
  - Post fixes: the watchtower window rendered as a round red blob that read as an eye; it is now a slit, and the fire is a
    small flame (`mid_post`). A thin post on the right hill that read as a standing figure is patched out (`far_patch`).
  - Replaces 50_ra.js's procedural `xra_pano` band (the yellow branching "Root").
- **K11 The Rose Window (cathedral, indoor):** the upper nave at dawn, warm where the regular backdrop is cold moonlight. The
  great rose window has intricate tracery and muted jewel glass. Below it are clerestory lancets; around it are piers and
  vaults, plus a far lancet.
  - Layer: far 416x232 (fac 0.08, vfac 0.15).
  - fx: four coloured dawn shafts from the painted window to the floor, dust motes, and a slow glow pulse.
  - The picked seed (sweep b, seed 3) painted a small robed figure under the lancets, which is refilled (`PATCH`).
  - Room overrides, all in `85v_v1.js`:
    - The old flat-colour `xra_rose` prop is hidden while the painting is loaded. Its gold motes stay. Its three lights move
      down to where the shafts land, softer, because dynamic lighting multiplies the parallax and blew the painted glass to
      white.
    - The open-space back-wall veil is thinned in K11 only (a blurred mask, ×0.4), so the small arch tiles no longer lace over
      the window.
- **M14 Fisherman's Rest (mire, indoor):** the last of the dusk, an amber afterglow under a deep teal sky. Drowned cypresses
  hung with moss and a stilt village with a chapel spire stand in silhouette, with a few lit windows. The marsh is a black
  mirror with lights on the water.
  - One far layer, 400x224. The reeds-and-tree mid layer was tried: the tree rendered mushy, and the room's own water and reed
    props hide it, so it was dropped.
  - fx: the village windows and lanterns breathe, and a few pale lights drift and fade over the water, standing on nothing
    (rb_2: "more than there were lanterns").
  - Room override: 51_rb.js `xrbBackdrop` painted an opaque night over the parallax. With the vista loaded, M14 now only clears
    the back wall in the open part of the room.
  - Seeds with a figure standing in the water (sweep s2) or dark head-like blobs (s3) were rejected.
- **A14 The Reading Nook (archives, indoor):** the nook is now a room. Its back wall is solid bookshelf tiles, darkened, and only
  the tall window's glass is open (an arch matching `xrb_awin`'s interior, running 3 px under the frame).
  - Through the window: rain over the Archives' gothic skyline, a broken tower and gables with violet candle windows ("the
    candles … burn violet"), and the Pale Root rising pale beyond.
  - The painting is rendered for the window's neighbourhood only, at 6 render px per game px. It is room-locked (fac 0,
    vfac 1), since the room is exactly one screen wide. It is graded up, because the archives ambient halves the parallax.
  - Layers: far + flash. The flash is a slow storm, one flash every 9–16 s with a double flicker.
  - fx: slanting rain beyond the glass.
  - The rain area's full-box flash (`XRB.flash`) is zeroed in this room, because it lit a pale rectangle over the wall.
- **HF14 Frostbitten Overlook (hoarfrost):** no moon; the aurora is the only light. A great V-folded green curtain with violet
  fringes hangs over a basin of black ice. A snow peak sits under the fold, the dam's arches cross the ice, and snowy pines
  stand in the near corners.
  - Layers: far 424x232, mid (pines and rocks, fac 0.1), and `aur`, 2 frames taken from the painting's own green light with
    drifting rays. The fx crossfades `aur` additively so the curtains breathe.
  - fx also: star twinkle and light snow.
  - Every seed broke the ice into land patches, so the ice is rebuilt in post as a mirror of the high sky (compressed ×2.4,
    since the viewer is high above). The 1 px stars are added at 1x.
  - Replaces 51_rb.js's procedural aurora and reservoir band in this room. It drew through `drawGlow`, so it showed over the
    terrain.
- **SP15 Lighthouse Balcony (spire):** the open sea at night. The moon sits in a clear patch between billowing storm clouds and
  lays a silver road on the swells. On the right is the thunderhead, and the lighthouse hides the right third of the painting,
  so everything is composed into the left two thirds.
  - Layers: far, flash (the thunderhead lit from inside with a bolt) and mid (sea stacks, fac 0.12).
  - The flash layer's alpha follows the Spire's own `SPR.flash`, so it keeps time with the thunder and the room flash.
  - fx: the moon's halo is drawn unlit (`drawGlow`, open sky in both views; the storm's ambient made it grey). The lamp's beam
    turns over the water from the `lantern_room` prop, and it follows the seated zoom.
  - Replaces 52_rc.js's seaview band and beam in this room.
  - Rejected seeds:
    - eye-like ring holes in the clouds;
    - a storm front rendered as cliffs;
    - boats and lighthouses on the horizon.

## Light shafts (`GFX_SUN`)
`40_gfx.js` is untouched. `85v_v1.js` wraps `gfxRaySources` and swaps the biome entry for the current frame only, for rooms
listed in `V1_SUN`:
- **R11:** at the Root's foot (0.42, warm). Ramparts follows the regular far layer's sun, which is not in this painting.
- **K11:** at the rose window (0.22, threshold 0.45; stronger values blew it out while standing).
- **SP15:** at the moon (0.3, cool).

HF14 and M14/A14 keep the biome default, or have none.

## Caveats
- **Pixel density:** these are the pilot's painterly pixels (2–3 px forms), not the 1 px crispness of the ramparts layer. R11's
  crown twigs are the softest part.
- **Seated vs standing:** the parallax is not zoomed in the seated view (engine behaviour), so distant things look relatively
  larger seated. That reads as depth. The rooms are composed for both.
- **Patched seeds:** K11 and R11 each needed one figure-like detail patched out (noted in the scripts). Dynamic lighting darkens
  every vista, so SP15 and A14 are graded brighter than their renders.
- **Re-render drift:** `--render` re-renders from the current guides. R11's mid layer was picked from a sweep made before a
  later guide tweak, so a re-render will not match it exactly. The build from the saved renders is exact.
- **Pre-existing, not changed:** 51_rb.js's `a_window` prop rolls `Math.random() < 0.02` every frame. That sets `XRB.flash` and
  schedules a thunder `tone` roughly every second in A14. My fx zeroes the visual flash in A14, but the frequent thunder tone
  remains (51_rb.js, owner RB).
- **Test bundles:** `web/dist/vista_v1.html` and `vista_v1_before.html` are scratch (dist is ignored). The before bundle was
  built before any V1 change. The final after bundle also contains V2/V3's `85v_*.js`, which do not touch these rooms.
