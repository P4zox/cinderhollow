# NEO-HALLOW art upgrade (branch `neohallow`, from main 72274ca), 2026-10-18

The owner asked for the cyberpunk region's backdrop and art to be higher quality and more beautiful: a rain-soaked,
neon-lit vertical megacity seen from inside a secret pocket of the Hallow. The look should be dark, moody and cinematic,
with restrained glow. Player and enemies must stay readable. It also has to stay consistent with World 2's planned
"Neon Megacity" (`docs/v18/WORLD2_PLAN.md`: Arcology Zero, vertical cyberpunk around the Root's fossil crown, rain,
holograms, a corporate cathedral).

All 17 rooms, the SAINT-0 fight and its cyberspace phase, the NH15 vista (standing and seated) and NH17 were snapshotted
before and after the change. No room data, tile index, frame size, tag, frame count or anchor changed.

## What changed

| Area | Files | What |
|---|---|---|
| Backdrop, far | `art/gen_bg_neohallow_v2.py` → `bg_neohallow_far` | **Sky:** a cloud deck lit from below by the city, magenta on one side and cyan over the cyan district. The sky is a ComfyUI img2img render of a painted guide (seed 4, denoise 0.42, lineart CN 0.42→0.6, pixel-art-xl 0.4, prefix `neo/`), then palette-locked.<br>**City (drawn at 1x on top):** three depths of towers fading into the rose/teal fog. Each nearer depth is darker, with more lit floors, and the offices light up in clusters.<br>**Landmarks:** Arcology Zero (stepped tiers with lit ring decks and a magenta glyph banner; its crown needle goes into the cloud) and the Pale Root (a petrified violet-grey column, hazed by distance and rim-lit faintly, rising into the cloud).<br>**Details:** five holo boards that glow into the fog. The 4 `loop` frames only blink the red aviation lights. |
| Backdrop, mid (outdoors) | → `bg_neohallow_mid` | **Towers:** six near towers drawn at 1x. They are dark curtain-wall glass (floor slabs and mullions), with offices lit in clusters, neon-lit corners and side pods. One tower climbs out of the frame. Their feet are lost in street fog.<br>**Neon:** vertical glyph signs, a facade holo column and a rooftop board. Each sign washes the facade next to it in its own colour (a falloff from the sign's rectangle, dithered).<br>**Roofs and links:** skybridges with lit undersides, water tanks, vents, AC units, masts and cables. The gaps between towers show the far city. |
| Backdrop, mid (indoors) | → `bg_neohallow_inmid` (new) | Indoor rooms (NH4, NH6, NH7, NH8, NH10, NH13, NH14, NH16, NH17) now show the hall's own glass wall instead of floating towers. It has steel piers every 128 px with pointed tracery heads (the World 2 "corporate cathedral"), transoms, two server towers with blinking LEDs, and a wainscot with a cable tray and a magenta LED strip. The panes are open, so the city shows through them. |
| Backdrop motion | `web/src/36_neohallow.js` (`drawParallax` override, `NH_BGFX`) | **How it draws:** the layers are drawn like the engine's parallax (same factors, same `lxMidG` mid mask). Their frames play at 2.5 fps.<br>**World-continuous offset:** each room shows its own slice of the city (`room.def.gx`). Before, every room's left edge showed the same skyline.<br>**Motion:** flying traffic in three lanes (tail lights one way, head lights the other), two searchlights sweeping the cloud deck, boards and signs that stutter now and then, and steam puffs off the rooftop vents.<br>**Fx positions:** the generator writes the fx points between the `// <nh-bgfx>` markers.<br>**Unchanged:** cyberspace and the NH15 vista keep their own paths. |
| Tiles | `art/gen_tiles_neohallow_v2.py` → `tiles_neohallow` | Same 48-tile contract. Contents:<br>- **Solids:** dark gunmetal cladding in 16×8 panels with bevelled seams, rivets and rain streaks below the seams. The mass darkens away from open sides, so big blocks read as silhouettes.<br>- **Edges:** every roof edge has a wet steel lip (a broken specular line) over a segmented cyan LED trim. The west face takes a cold rim; undersides carry magenta service lights.<br>- **Details (by mask):** vent grate, lit slit window, conduit, worn hazard chevrons, a vein of the fossil Root, and an access hatch deep in the mass.<br>- **Other tiles:** steel catwalk grating with an LED edge, cyan-tipped data spikes, quiet back walls (panel / server LEDs / conduit / dead glyph panel), and roof clutter on 30 % of tops.<br>`tiles_neohallow_cyber` is unchanged. |
| Props | `art/gen_props_neohallow_v2.py` | **Look:** volume (a cold rim on the lit side, a falling shadow, a 1 px dark outline), grime and rust low down. Neon appears only where something is a light. Holograms use partial alpha with scanlines. The glyphs are made-up strokes with no letters.<br>**Sheets:**<br>- `nh_deco` (all 13 tags): box signs with lit glass, holo billboards (an eye, scrolling glyphs, the Root logo) with a glitch frame, a lamp, a lattice antenna, an exhaust vent, a station canopy with glass sides, a pylon, a server rack, and a floor sigil projector.<br>- `nh_term`: a kiosk with a tilted screen and scrolling lines.<br>- `nh_train`: a streamlined maglev car with a lit cabin, a magenta line and glowing pads.<br>- `xsc_m`: only `vending`, `watertower` and `maglev` were redrawn. **`devdesk` is untouched.**<br>- `xsc_s`: only `dumpster`.<br>A pixel diff against `art/bg_src/neohallow/v1/` confirms that only those tags changed. `nh_portal` and `nh_turret` read well and were left alone. |
| Code-drawn decor | `web/src/55_sc.js` | **Pipes, railings and warning stripes** now tile the new `nh_kit` sheet (16×16 pieces: `pipe`, `pipe_j`, `rail`, `rail_p`, `stripe`, `stripe_e`). The old fills remain as a fallback.<br>**Other decor redrawn in code:**<br>- Cables: a bundle of three with a rim, and blinking junction boxes.<br>- Windows: a recessed frame with a dim pane lit from inside; some have blinds.<br>- Steam vents: a slatted box with an amber lip on the warning. The column is soft puffs, drawn into the lit-particle layer.<br>- Billboard Climb's phase slabs: dark glass, a neon frame, glyphs and scanlines.<br>- Data Highway maglev overlays: moved onto the new car art. |
| Atmosphere | `36_neohallow.js`, `41c_atmos.js`, `41b_surf.js` | **Rain:** two depths (fine far rain and near rain) plus 3 px splashes on the roofs in view. It is drawn through `lxAir`, so with Lit particles on, the drops take the colour of the neon they pass (the sign lights are colour-matched).<br>**Reflections:** the neon puddles (`xsc puddles`) are wired into `lx4Mask` as the puddle kind (the one-line hook phase 4 listed). Outdoor NEO-HALLOW floors count as wet stone (`LX4_WET`, outdoors only, like the Spire). Room layers take the `wet` material (`LXN_MAT_ROOM`, outdoors only), so roof lips catch the lamps. When Reflections are on, the painted puddle and sign reflections drop back to faint glints.<br>**Metal:** `nh_*` sheets join the metal material list.<br>**Deco lights:** heights retuned to the new art. The antenna has a blinking red light. The vent steams from its stack. |

Rebuild commands (all deterministic from the saved sky render):

```
python3 art/gen_bg_neohallow_v2.py
python3 art/gen_tiles_neohallow_v2.py
python3 art/gen_props_neohallow_v2.py
```

- `gen_bg_neohallow_v2.py` rebuilds the far, mid and inmid layers and also rewrites `NH_BGFX` in `36_neohallow.js`. Run it with `--render 4` to re-render the sky with ComfyUI.
- All three take `--no-ase` (previews only). The sky render (`art/bg_src/neohallow/far_render.png`) is gitignored like every bg render; without it, run `--render 4`.
- The v1 sheets are copied to `art/bg_src/neohallow/v1/` locally (gitignored); git history (72274ca) has them too. `art/gen_neo_env.py` still builds the cyber layers.

## Lessons / decisions
- **ComfyUI is used only for the sky.**
  - At denoise 0.55–0.68 the model ignores the city layout: it turns towers into vertical light streaks or a second skyline. The renders are in `art/bg_src/neohallow/sweep/` (seed 3 at 0.68 was the most atmospheric).
  - Everything with structure (towers, windows, signs, the Root, the arcology) is drawn crisp at 1x. As the bg pilot and NH15 found, renders turn that detail to mush.
- **Composition follows the rooms.** The rooftop floors cover the layers below about y 168, so the fog glow peaks just above that, with the skyline depths standing against it.
- **Neon spill was capped.** A first pass let the signs light the facades in round blobs, and the amber spill quantised to a flat brown slab. The spill now falls off from the sign's rectangle and stays ≤ 0.8 before the palette lock.
- **The Root was simplified.** Two passes with bare limbs read as horns or a claw. It is now a colossal column with one stub, lost in the cloud and hazed by distance. That is the "grey spine through the neon" from the lore, and it stays consistent with NH15, which keeps its own painted Root.
- **The indoor glass wall** fixes indoor rooms that floated in open sky. The rooms keep the old stepped veil (`AREAS.neohallow.veil` was not needed: the wall is dark enough that no boxes show).

## Checks (test build `web/dist/neo.html`; before = `web/dist/neo_before.html` from 72274ca)
- `wm/mech.js`: **64 OK, 0 BAD/FAIL**.
- `v17/area/checks.js`: `errs: []`, **0 BAD/FAIL**.
- `tr/bosses.js`: **31 OK**, 2 lines that are not OK. Both fail the same way on the before build, so neither comes from this change:
  - `EXC astrel … lxnGenFrame`: reproduced on `neo_before.html`.
  - `BAD saint0 … byPlayer=0`: the known flake. Over 3 alternating runs per build, the after build failed 1/3 and the before build failed 1/3.
- **SAINT-0 played through the training summon** (`tools/shots/v17/neo/saint_train.js`, a bot that up-slashes when it floats):
  - After: phases 1/2/3 including cyberspace, 606 damage dealt by the player's own hits, boss killed at step 2219, no errors.
  - Before: the same flow, killed at 2275.
- **Graphics modes** (NH2, NH9, NH4) under Classic lighting, shaders off, Reflections plus Lit particles off, and Strong shafts: no console errors (`graphics_modes.png`).
- **Reflection mask** (`LX4.rn`, debug): NH15 50 rects / 23 puddles, NH9 77 / 43, NH2 36 (wet roofs), NH4 0 (indoors).
- **Layer stats** (`art/bg_src/neohallow/stats.json`):
  - far: 788 colours, mean luminance 33.0, near-black 0.29.
  - mid: 1097 colours, mean luminance 25.7.
  - The v1 layers were near-uniform dark with dotted windows.

## Deliverables (`tools/shots/v17/neo/`, gitignored like every capture)
- `before_after_rooms_1..7.png`: every NH room standing (33 spots, 2 with foes), NH15 seated, and NH17 (the Dev Room joke intact: missing textures and the T-pose).
- `before_after_saint0.png`: the SAINT-0 fight in phase 1, phase 2 and the cyberspace phase.
- `saint0_training_fight.png`: the fight through the training summon.
- `before_after_zoom.png` and `before_after_zoom_saint0.png`: native-pixel crops at ×3.
- `toggle_reflections_off_on.png`: the knight and a laser mirrored in the wet roof.
- `graphics_modes.png`.
- `snap.js` (all rooms plus the fight), `saint_train.js`, `modes.js` and `sheet.py` (montages) to reproduce. Raw before and after shots are in `before/` and `after/`.

Reproduce:

```
BUILD_OUT=web/dist/neo.html python3 web/build_web.py
cd tools/shots && SHOT_HTML=$PWD/../../web/dist/neo.html node shot.js v17/neo/snap.js v17/neo/after
```

## Caveats / not done
- **NH7 floor and void:** the arena's deletable floor and the data abyss (`nhDrawVoid`, `nhDrawDelFloor`) are still code-drawn as before. They read fine against the new wall.
- **Cyberspace:** the cyber variants (`bg_neohallow_cyber_*`, `tiles_neohallow_cyber`) were judged acceptable and left as they are. The phase is still the white wireframe void.
- **NH15:** keeps its V3 vista painting. Only its props and tiles changed.
- **Reflections are subtle on purpose:** wet stone only streaks what is already bright on screen (a phase-4 limitation).
- **Indoor rooms** show the glass wall mostly through the 0.28 back-wall veil, so the hall reads dim and moody rather than open.
- **Frame time** was not re-measured. The added cost is the fx (a few dozen 1–2 px rects and two gradient beams per frame) and one extra mid sheet. No new shader work.
