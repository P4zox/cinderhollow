# BG rollout, agent C (branch `bg-overhaul`), 2026-10-16

Agent C's share of `BG_ROLLOUT.md`: the pilot's weak spots (catacombs, cathedral), threshold, ember, hermit, the neohallow
far-layer seam, and the per-biome smooth back-wall veil (engine: `01_data.js` / `03_world.js`), including the veil requests from
agents A and B. Method as in `bg_pilot.md` (`art/bgv2lib.py`, unchanged). Montage: `tools/shots/v17/bgroll/C_before_after.png`
(in game, shaders on, default lighting, no enemies; left = before, right = after). Nothing committed. The shared ComfyUI
server was stopped at the end (the lead allowed it; the queue was empty).

## Files
| File | What |
|---|---|
| `art/gen_bg_threshold_v2.py`, `gen_bg_hermit_v2.py`, `gen_bg_ember_v2.py` | new: guide + prompts + picked seeds + post + build (same CLI as the pilot: `--guide`, `--render`, `--no-ase`) |
| `art/gen_bg_catacombs_v2.py` | skull restamp (`SKULLS`, `SKULL_PX`, `stamp_skulls`); the guide paints pixel-identically to the pilot's |
| `art/gen_bg_cathedral_v2.py` | new mid guide (true pointed arches, two orders, weed, censers, tide marks) + re-render; far: finer LIGHT steps, `dk` 0.3, `clean_olive()` |
| `art/gen_neo_env.py` | the far sky / cloud noise is now tileable (`period=`); only `bg_neohallow_far` changes (mid and cyber are byte-identical) |
| `art/bg_src/{threshold,hermit,ember}/` | guides, edges, renders, `out_*`, `preview.png`, `stats.json`; `v1/` = old layers (ignored); `sweep/` = seed sweeps (see the note at the end) |
| `assets/bg_{threshold,hermit,ember,catacombs,cathedral,neohallow}_*` + `art/*.aseprite` | rebuilt; same names, 512x216, tags and frame counts (neohallow far keeps 4 frames, `loop` 0–3), far opaque, mid binary alpha. `bg_catacombs_mid` is unchanged |
| `web/src/01_data.js` | `AREAS.archives.veil`; new `AREA_VEIL` table (threshold, hermit, ember, dunes, necropolis, deep) |
| `web/src/03_world.js` | `drawSmoothVeil(R, ctx, alphaOf, wallAt)` factored out of `renderRoomLayers` (same output for catacombs/cathedral); veil key read from `AREAS[b].veil` or `AREA_VEIL[b]`; `registerTile(..., { gap: true })` + `TILE_GAP`; `R.veilSmooth` |
| `web/src/24_secrets.js` (hermit/ember, mine) | the `'&'` back-wall gap tile is `gap: true` and no longer clears a hard 16 px cell when the room uses the smooth veil |
| `web/src/82_forge.js` (threshold, mine) | `CFA_KIND.hall`: the bricks fade out over a band toward the broken arch instead of a hard 16x8 staircase (CT1) |
| `web/src/34_dunes.js` (agent B's biome; B asked for it) | `duOpenBack` (DU1–DU4) draws its own back layer, so the veil key alone could not reach DU1: it now calls `drawSmoothVeil` with the same alphas (0.85 / 0.35 / 0). 6-line change, nothing else touched |
| `tools/shots/v17/bgroll/C/` | `snap.js`, `before/` (bundle built before any C change), `after/`, `raw/seam_crops_x3.png`; per biome copies in `bgroll/<biome>/{before,after}/` (threshold, ember, hermit, neohallow, catacombs, cathedral), veil shots in `bgroll/{dunes,necropolis,archives,deep}/after_veil_C/`, layer crops in `bgroll/{catacombs,cathedral}/raw/` |

Rebuilds are deterministic: rerunning the five `gen_bg_*_v2.py` and `gen_neo_env.py --only=bg` reproduces the shipped assets
byte-for-byte (md5 checked). Renders: `*_render.png` are local (gitignored); `--render` regenerates them with ComfyUI.

## 1. Pilot weak spots
- **catacombs, skull rows read as shelves of jars at 1x.** The model rendered the guide's skulls as rounded blobs. Fix in post: the
  guide records every skull it paints (`SKULLS`, 213); after the palette lock each skull that is still visible in the guide
  (not covered by a root, niche or buttress: 172) is restamped as a crisp 5x5 pixel skull (`SKULL_PX`: rounded cranium, two
  1 px sockets, jaw with teeth), its ramp step picked from the band's local brightness so the light pooling is kept. Reads as
  skulls at 1x in C10/C8; `catacombs/raw/skulls_pilot_vs_C_x3.png`. No re-render; the far layer is otherwise the pilot's.
- **cathedral rose-window dither.** The halo spanned a big gap in the LIGHT ramp (7884a0 → a0b0c8), so it was dithered over a wide
  area. Added three in-family steps (`8a9ab6`, `96a6c0`, `b2c0d4`) and lowered `dk` 0.35 → 0.3: a fine, short dither now (0.22
  gave visible rings, so 0.3 it is).
- **cathedral olive smudges on the piers.** They quantized to a grey-olive accent (`#363838`) and stray gold. `clean_olive()`
  repaints any non-blue pixel outside the allowed gold zones (`GOLD_OK`: capitals, the gilded sill, the rose boss, the chandelier,
  the two candle stands) with the cool colour of the same value (1368 px).
- **cathedral plain mid arcade.** Root cause: the shared `arch_pts()` "pointed" head is elliptical (horizontal tangent at the
  apex), so the arcade rendered round. The mid guide now uses a local two-centred `gothic()` arch with two moulded orders, a hood
  moulding and voussoir joints, water weed hanging from the intrados, larger pierced censers on link chains and tide marks on the
  piers; re-rendered (seed 2, denoise 0.66, cn 0.6→0.8). The model drops thin weed, so it is drawn at 1x after (`draw_weeds`).
  K7/K3s: a pointed, richer arcade, still dark and quiet behind the player (`cathedral/raw/mid_pilot_vs_C_x2.png`).
  `GFX_SUN.cathedral` unchanged (the far layer did not move).

## 2. threshold (The Ashen Threshold, World 2 entrance)
- **v1:** 8 colours, puffy posterized clouds, five plain obelisk sticks, a repeating 64 px arcade, a moon-like disc.
- **v2 far** (seed 8, pix 0.4, denoise 0.62, cn 0.55→0.7): a pale cold storm sky with long stratus, a sea of mist, and far off a
  colossal wall running the whole width, its top lost in cloud near the gate and lower, broken and hazier away from it (no box
  ends). In it, a vast shut gate with a 1 px seam of light (redrawn crisp in post at x=339) and a light from behind the wall, no
  sun disc ("light with no sun to make it"). Aerial haze in post keeps the beyond vague. The seam sits at far x≈340: CT2 shows far
  x 0..471, so the seam is on the right as the player sets out and slides behind the gate prop (screen x≈264) at the east end,
  which fits the lore page ("it does not seem to get nearer"); CT1 sees it through the broken arch.
- **v2 mid** (seed 2): a causeway viaduct with varied spans and a collapsed one, a tall banded obelisk, a fluted stump, a
  cenotaph with a carved ring, a broken obelisk, a ruined portal (two posts and a cracked lintel, an echo of the gate) and a
  fallen obelisk. No figures. The vaults under the deck are filled opaque (`fill_vaults`: shadowed underside lifting to mist):
  seen through, the bright mist sea sat right behind the player at causeway height and the room lights blew it to white.
- **CT1 staircase:** the hard 16x8 brick staircase was the hall prop (`CFA_KIND.hall`), not the veil: its bricks now fade out over
  a band toward the opening. The threshold veil smooths the back-wall boxes in the opening.
- Palette: the v1 ramps extended both ways in the same cold slate family plus a faint warm white (13 colours far, 8 mid).
  No `GFX_SUN` entry (none before either).

## 3. ember and hermit
- **ember** (v1: rows of identical posts, dotted squiggles, a mid ground band hiding the lava horizon). v2 far (seed 2): a dark
  volcanic hollow, groups of hexagonal basalt columns at two depths lit from below, a distant ember lake raised to y≈156 so it shows,
  the Pale Root's burning taproots hanging from the vault with glowing cracks. v2 mid: causeway-like stepped basalt clusters
  (tallest off-centre, a few snapped), low ground (y≈198), two charred hanging roots. E5 now shows the lake and columns between
  the pillars; E4 is mostly back wall either way; E6 (vista overlay `xsc_bg_hearth`) shows the roots.
- **hermit** (v1: gradient sunset with a glowing bar that read as a lens streak, banded hills, 3-colour stacked-triangle pines).
  v2 far (seed 3, denoise 0.5): a banded dusk sky with lit stratus and a few stars, layered ranges, and the Pale Root breaching the
  far range as a colossal pale arching root with rootlets and a side root diving back in. It rendered near-white (frosted), so post
  warms it to ivory-gold and pulls it down a step. v2 mid: a continuous tree line of wind-bent spruce. Isolated trees showed only
  their tips over the rooms' terrain and read as small standing figures (rejected twice), so it is a forest band now; in H2/H3 it
  sits below the terrain anyway. H2/H3/H1 also needed the gap fix below.

## 4. neohallow
- **Far seam:** the cloud band and the sky noise were not tileable (`vnoise` without `period`). Now `period=` with a cell size that
  divides 512 (`BW / 11` for the 48 px clouds). Seam ratio 1.69 → 0.69; `C/raw/seam_crops_x3.png`. Nothing else changed.
- **NH17 magenta checker squares: intended.** NH17 is "The Dev Room" (`02_rooms.js`), whose spawns are `xsc` kinds `missingtex`
  (x2), `tpose` and `devdesk`: a deliberate missing-texture joke in a secret room. Left alone.

## 5. Smooth back-wall veil
`drawSmoothVeil` interpolates the per-tile veil alphas bilinearly (sampled at tile centres), so walls fade across each 16 px tile
instead of stepping. Set for (all `[1, .8, .5, aOpen]`, the old stepped values only smoothed):
| biome | aOpen | why |
|---|---|---|
| catacombs / cathedral | 0.18 / 0.28 | the pilot's, unchanged (output identical after the refactor; checked by image diff, only light-flicker noise differs) |
| archives (`AREAS.archives.veil`) | 0.28 | agent A: the light column's hard pale box in A8/A16/A2. With the veil its edges are soft and it is no darker, so a softer open value was not needed |
| deep | 0.28 | agent A: the bright falls behind the stepped boxes (D5/D11); a modest gain |
| necropolis | 0.28 | agent B: NV15's hard rectangle around the open area; gone |
| dunes | 0.28 | agent B: DU1's box frame. DU1–DU4 redraw their own back layer (`duOpenBack`), so that function now uses `drawSmoothVeil` too; the frame is gone |
| threshold | 0.28 | CT1's boxes in the arch opening (plus the hall fix above) |
| hermit | 0.24 | H1–H3: the windows onto the dusk were hard boxes. The `'&'` gap tile cleared a hard 16 px cell over the veil, so gap tiles are now alpha 0 in the veil mask (it fades into them) and skip the clear when `R.veilSmooth` |
| ember | 0.28 | E5/E6 boxes; E6 also has `'&'` gaps |
Crown, spire, hoarfrost, mire: none (A and B: no box edges seen). Rollback: delete the keys / the `AREA_VEIL` entries.

## Caveats (honest list)
- **threshold far** is soft and low in contrast by design (haze), with a light ordered dither in the sky; it is clearly richer
  than v1 (a focal gate, a real wall, structured sky), but it is not as crisp as ramparts. The wall's sloping top reads a little
  like a dam line across the sky in CT2.
- **hermit:** the arching root is the brightest thing in the sky and a strong shape; in game the back-wall veil softens it. If it
  feels too dominant, lower it further in `far_post` (the 0.86 factor). The mid tree line is hidden by the terrain in H2/H3, so
  the mid layer contributes little there.
- **ember E4** looks the same as before (the back wall covers the parallax in that room).
- **catacombs:** the other pilot caveats (ceiling roots as arcs, the plain floor band) were not in my brief and are unchanged.
- **dunes `duOpenBack`** is in agent B's file; the change is minimal and isolated, but B/the lead should know it is there.
- **`.gitignore`:** `art/bg_src/*/sweep/` is already ignored in the working tree (added by another agent); my sweeps (threshold
  15 MB, hermit 7 MB, ember 5 MB, cathedral 4 MB) stay local.
- Test bundles `web/dist/bgrollC.html` / `bgrollC_before.html` are scratch (dist is ignored).
