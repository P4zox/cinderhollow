# v17 painted vistas, agent V2 (branch `bg-overhaul`), 2026-10-17

Rooms: X11 The Crown Overlook, LF1 The Long Evening, CM16 Moonlit Conservatory, DU15 The Last Oasis, TV14 Mossbed Glade,
DB15 Pearl Lagoon. Brief: `docs/v17/VISTA_BRIEF.md`. Montage: `tools/shots/v17/vista/V2_before_after.png` (in game, shaders on,
default lighting: before / after standing at the bench, before / after seated). Nothing committed, pushed or published.

## Files
| File | What |
|---|---|
| `web/src/85v_v2.js` | the six `vistaRegister` calls with their fx; the per-room `GFX_SUN` swap; a per-room smooth back-wall veil (TV14, DB15); DB15 drops its old flat lagoon backdrop; a debug probe (`window.__v2probe`) |
| `art/vista_v2lib.py` | helpers on top of `bgv2lib`: `Canvas` (a 3x guide of any size), `render` / `sweep` (ComfyUI, outputs under `output/vista_v2/<room>_*` on the shared server), `inpaint`, `seg_dark`, `to_pixels` (k-means palette + extra colours fitted to the brightest / darkest pixels, Lab lock, flat-area Bayer dither, orphan cleanup), `key`, `build` (any size, 1+ frames, tag `loop`), `composite_preview` |
| `art/gen_vista_{x11,lf1,cm16,du15,tv14,db15}.py` | guide, prompts, picked seeds, grade, hand-painted parts, build. `--guide`, `--sweep <layer> <seeds> [--denoise x --cn x --tag t]`, plain run = build from the saved renders, `--no-ase` = previews only |
| `art/bg_src/vista_<room>/` | guides, edges, masks, `*_render.png` (the picked renders; gitignored like the rollout's), `sweep/` (gitignored), `out_*.png`, `preview.png` |
| `assets/vista_<room>_<layer>.png/.json`, `art/vista_<room>_<layer>.aseprite` | 13 sheets: cm16 far/glint/mid, x11 far/land, lf1 sky/far/mid, du15 far/glint, tv14 far, db15 far/glint. Rebuilds are byte-identical from the saved renders (md5 checked) |
| `tools/shots/v17/vista/` | `snap_v2.js` (standing at the bench + one more spot, then seated ~3 s, lore panel hidden), `probe_v2.js` (how much backdrop shows through each room), `montage_v2.py`, `<room>/{before,after}_*.png`, `v2_before/`, `v2_after/`, `V2_before_after.png` |

No shared engine file was edited. Everything room-specific lives in `85v_v2.js` (loads after `85_vistas.js`, so the vistas
replace the old LF1 / X11 / DU15 sky overrides in `52_rc.js` / `54_sb.js` for those rooms only; if a sheet is missing,
`85_vistas.js` falls back and the old overrides draw again).

## Method
The pipeline's guide -> SDXL + pixel-art-xl + Lightning img2img -> BOX down -> palette lock, with three changes that the
paintings needed:
- **Freer renders for skies and forests.** The rollout settings (denoise ~0.6, ControlNet 0.45-0.65) copied the guides' flat
  shapes (the forest came out as flat bars, the storm walls as blobs). Denoise 0.68-0.85 with ControlNet 0.3-0.45 gave the
  painted clouds, mist and light; the guide still places the light source and the horizon.
- **Hand-painted silhouettes where the model failed.** Every render turned the Spire's thunderhead into a castle and the
  castles into storms (X11), and every render of LF1's land came out as flat brown mush. Those parts are painted at 1x in the
  generators (crisp 2-tone silhouettes, a warm rim on the sun side, lit windows) and sit on their own parallax plane. LF1's land
  then gets a light texture pass (img2img denoise 0.4 over its own 3x upscale, cut back out with its own 1x alpha, so the shapes
  stay exactly as painted).
- **Grading for the room light.** Dynamic lighting multiplies the backdrop by the biome ambient (~0.43-0.62) except pixels
  whose brightest channel passes ~214, which show as painted. A light that fades slowly across that knee shows as a wide
  dithered ring, and mid-bright rock picks up the room lamps' 16 px shadow boxes. So the light sources (moon, sun, glade, the
  lagoon's arch) are pushed over the knee, the halo crosses it in a narrow step, highlights near white are compressed 2:1
  (the bloom spreads them otherwise), and the rest is held a little darker.
- Palette: k-means per layer (24-40 colours) plus 4-10 colours fitted to the brightest pixels: with one global k-means the moon's
  maria and the sun's rings collapsed into one flat colour.
- Water glints and star twinkle are frame-animated overlay layers (`glint`, 4 frames, same scroll as the painting), the rest of
  the motion is fx in screen space. All fx draw in alpha-stepped batches; the six rooms cost 0.3-1.4 ms/frame headless.

## Per room
**X11 The Crown Overlook** (crown, outdoor). Kept from the old panorama overlay: the whole Hallow under a sea of cloud with its
landmarks standing out of it (lore rc_10). Now: golden hour from the top of the world, a low sun laying a road of light over a
painted cloud sea, a towering thunderhead lit rose on its crown over the Spire, the Ramparts on their crag, the drowned
Cathedral's twin spires with a sunlit rose window, the Spire's lighthouse with its lamp (`land` plane, fac 0.035 against the
sky's 0.02). **Revised after the lead review** (the first landmarks were flat 1x cut-outs): `land2_paint()` builds each landmark
at 3x from separate masses (crag and strata ledges; curtain wall, crenels, round towers with conical roofs, keep and turret,
gatehouse; west towers, cornices, spires, pinnacles, lancets, nave gable, a buttress; sea stack, lighthouse shaft, gallery,
lantern), each lit by its own ramp from the shaded side to the sun side with a warm rim on the sunward edge, aerial perspective
toward the sky render's own colour cooled to violet (stronger for the far lighthouse, and near every base where the sea's mist
rises), and billows in the sea's own colours wrapping their feet (lower toward the ends, so no cloud "plates"). Then a texture
pass (img2img seed 4, denoise 0.42, lineart 0.6) over sky + landmarks, cut back out with their own alpha, and the 1 px sun-side
rims put back. `LAND_V2 = False` rebuilds the first version. fx: the Deep's red breath pulsing through a rift in the clouds, lightning in the thunderhead with an occasional bolt
to the sea, a veil of cloud drifting over the landmarks' feet, the sun's bloom. Render: sky sweep seed 2 (denoise 0.68).
`GFX_SUN.crown` is switched off in this room (`sun: null`): the painted sun sits in the view and its rays washed the player
out. Caveat: the sky's glow still shows a dithered halo ring in the standing view (the engine's emissive knee); it is the same
as the crown's old tree halo.

**LF1 The Long Evening** (lastfield, outdoor). Kept: the evening that never ends, the low sun, the god-rays breathing (redrawn
in the vista's fx with the old code's numbers), the warm light (`addLight` at the sun), the wheat and the warm wind (the room's
own, untouched). Raised (lore rc_4/rc_5): her storm stands over the field as a heavy cloud deck whose rippled underside burns
crimson and gold, the sun sunk in a bank of gold cloud; the drake stones on the far hill, the Stormspire with its lamp in the
east, harvested fields and hedgerows (planes: sky 0.015, far 0.05, mid 0.12, single paintings 424-560 px wide covering
cam.x 0..1408). fx: god-rays, slow lightning moving inside the deck. Sky seed 7 of sweep `b` (denoise 0.85, cn 0.3).
`GFX_SUN.lastfield` off here. Caveat: the land is the plainest part (1x painting + texture pass); the stooks blur into
the field texture.

**CM16 The Moonlit Conservatory** (crimson, outdoor). Through the glasshouse mullions: a pale silver moon with a faint rose
halo (the Manor's red moon gone quiet) over the Countess's night garden: the Manor's east wing with lit windows, a reflecting
canal and a white garden folly, cypress rows, a broken fence (`mid`, fac 0.14). fx: the moon breathes, low mist drifts over the
canal; `glint` twinkles stars and shimmers the moon's road. The painting rides with vfac 0.29 + dy 21 so the moon is high in
the glass standing and clears the roof's arches seated. `GFX_SUN.crimson` follows the moon here (uv 0.61, 0.75, strength 0.22,
cool white). The far plane is the render with the fence repainted as water (inpaint), so the planes never double.

**DU15 The Last Oasis** (dunes, indoor). Kept: the sun-kings' sunset and its pyramid (old `xsb_sky`). Raised (lore sb_7, the
evening "on water that has never learned it is underground"): a still lake from the pool to the horizon holding the sunset
upside down, pyramids and two obelisks in the haze, the sun on the dunes' rim. fx: heat shimmer along the horizon, the first
stars; `glint` breaks and re-forms the sun's reflection. Seed 5 of sweep `b`. `GFX_SUN.dunes` (its far-layer anchor follows
`bg_dunes_far`, not this sky) is replaced here by the painted sun (uv 0.55, 0.52, strength 0.18, indoors on). The render's pale
sun leaned green; it is pushed warm in the grade.

**TV14 Mossbed Glade** (thornveil, indoor). Past the Mother Oak the old wood opens onto a sunlit glade far off, colossal trunks
receding into green-gold mist: the one place in the Thornveil where the morning gets in (the regular backdrop is dark teal
trunks). fx: slanted shafts breathing, pollen motes. Seed 6 of sweep `b` (denoise 0.84). The back-wall veil is smoothed for
this room only (`V2_VEIL`, `[1, .72, .4, .16]`, set on `AREAS.thornveil.veil` only while this room's layers render), so the
view is not cut into 16 px boxes.

**DB15 Pearl Lagoon** (barrows, indoor). **Revised after the lead review** (the mouth was a flat bright slab): new guide with a
rugged mouth (a wandering outline), lit inner rock edges, and through it a pale sea under luminous mist to a far horizon with
sea stacks fading into the haze (no sun, no disc: the light has no visible source); god-rays slant from the mouth down into
the cave (fx). New pick: sweep `c` seed 14 (denoise 0.76, cn 0.4; seed 11 rejected for a moon disc). Grade: the opening keeps
its own shading with local contrast inside it, its brightest value ~204 (short of white and of the bloom, which had washed it
flat in the standing view), the cave around it held darker, the mirrored opening broken into ripples. Before, nothing of the backdrop showed: the room's own flat lagoon painting
(`xsa_lagoon` 'lagoonback', painted opaque into the back layer) covered all of it (probe: 1% visible). With the vista's art
present, `85v_v2.js` leaves that prop out on entry and smooths the back wall (`[1, .7, .36, .1]`), and the room opens onto a
drowned sea-cave: a natural arch full of pale light with no source ("light comes down here from somewhere no one has found"),
stalactites, still water mirroring it in broken ripples. fx: the light breathes, shafts slant down over the water, caustics
waver on the cave roof; `glint` ripples the reflection and sets a few pearl glints. Caveat: standing at the bench, the player light's banded dither shows on
the bright opening's left edge (engine lighting); seated it is clean. If the lead prefers the old lagoon prop, delete the DB15
enter hook and its `V2_VEIL` entry (the vista then sits unseen behind the prop).

## Rejected / notes
- X11 `near` cloud-billow plane (guide + mask kept in `gen_vista_x11.py`): rendered flat and sat under the floor anyway.
- Seeds rejected for figures: CM16 s1 (bats on the moon), TV14 b8 (a deer), DB15 b7 (a boat with a figure), DU15 sweeps (pier
  boardwalks instead of the sun's road), DB15 first sweep (a flat white pill for the arch), DB15 b6 (picked first, replaced
  after the lead review: a flat slab in the mouth).
- The shared ComfyUI server was up when I started; I never stopped it. My outputs use the prefix `vista_v2/<room>`.
- `art/bg_src/vista_lf1/guide_{far,mid}tex.png` are 3x upscales used as texture-pass guides (~1 MB each); everything big is
  under the existing `*_render.png` / `sweep/` ignores.
- Test bundles: `web/dist/vista_v2.html` (after) and `web/dist/vista_v2_before.html` (built before any V2 change); both ignored.
