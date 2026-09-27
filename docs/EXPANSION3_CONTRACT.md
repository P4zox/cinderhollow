# Cinderhollow — Expansion 3 build contract (read fully before touching anything)

Expansion 3 grows the world from 118 to ~269 rooms (plan: `docs/expansion3_plan.html`, machine-readable room list:
`docs/expansion3_rooms.json`) and adds a real lighting system. It runs in phases:

- **Phase 0 (this document, §1–§6):** lighting (agent **LX**), kit mechanics (agent **KM**), kit systems (agent **KS**).
- **Phase 1/2 (§7, filled in later by the lead):** region agents build the rooms on top of the kit.

`docs/EXPANSION_CONTRACT.md` and `docs/EXPANSION2_CONTRACT.md` **still apply in full**. That includes ground rules,
registries and hooks, boss conventions, and the playtest lessons in EXPANSION2 §0: every room enterable and exitable,
barriers can't be jumped over, and no physics jitter. Read them first.

## 0. Ground rules for this round
- **Build:** `BUILD_OUT=web/dist/<agent>.html python3 web/build_web.py` (agent id in lower case: `lx`, `km`, `ks`).
  Never write `web/dist/index.html` or `web/dist/pub/`. The lead builds and publishes those.
- **Tests:** `SHOT_HTML=web/dist/<agent>.html node tools/shots/shot.js tools/shots/<agent>/<test>.js tools/shots/<agent>/out`.
  Put scripts in `tools/shots/<agent>/`.
- **Regressions:** before you finish, run `tools/shots/stress.js` and `tools/shots/dormant_chk.js` against your build.
  Both must be clean (dormant_chk's `sentinels`/`coven` BAD lines are known false alarms).
- **No git.** Don't commit, don't push. The lead does that.
- **Files you don't own are read-only.** If you need a change in one, put a `NEEDS: <file> — <what and why>` line in
  your final report. For a one-line hook insertion into a shared file, make it and list it under `SHARED EDITS:`.
- Code style: match the surrounding code (dense one-liners, short comments that explain *why*). Use existing helpers
  (`rect`, `overlap`, `clamp`, `approach`, `text`, `panel`, `uiSel`, `wfx`, `registerTile`, `ROOM_CHARS`, `SPAWNS`,
  `HOOKS`, `addLight`, `spawnFx`, `sfx`, `tone`, `noise`, `toast`).
- **Art** goes through the existing pipeline: a Python/PIL generator in `art/`, then `art/asebuild.py build(...)`, which
  writes `assets/*.png/json`. Keep sheets small (under 600k px each where possible). Every new sheet costs memory on phones.
- **Performance budget:** 60 fps on a mid laptop with shaders on. The phone build (`TOUCH_UI`, shaders off by default)
  must not get slower. Check with `tools/shots/mobile.js` on a local split build: `SPLIT=1 BUILD_OUT=...`, then serve
  `web/dist/pub` with `python3 -m http.server`.
- New save fields go under `SAVE.x3 = { ... }`, created lazily (`SAVE.x3 = SAVE.x3 || {}`), so old saves load.

## 1. Ownership (Phase 0)
| Agent | Job | Files you own (create or edit) |
|---|---|---|
| **LX** | Dynamic lighting | new `web/src/41_light.js`; `renderLighting` in `web/src/03_world.js`; the shader and `presentWorld` in `web/src/40_gfx.js`; the lit/unlit layer split in `renderWorld` (`web/src/09_main.js`, that function only); `tools/shots/lx/` |
| **KM** | Kit mechanics: moving parts, hazards, puzzle parts | new `web/src/42_kit.js`, new `art/gen_kit.py` (+ `art/kit_*.py`), asset prefix `kit_`; test room `T1` in new `tools/regions/95_kit_test.py`; `tools/shots/km/` |
| **KS** | Kit systems: doors, trials, gauntlets, vistas, hidden passages, lore, completion, map, reachability | new `web/src/43_systems.js`, new `tools/reach.py`; `renderMap` in `web/src/08_ui.js` (that function and new map helpers only); the Status tab in `web/src/08b_menus.js`; the validation section of `tools/rooms.py` (call into `reach.py` and door-pair checks only); new `art/gen_sys.py`, asset prefix `sys_`; test room `T2` in new `tools/regions/96_sys_test.py`; `tools/shots/ks/` |

KM and KS publish their APIs in **`docs/KIT_API.md`**. KM writes the `## Mechanics` section and KS writes the
`## Systems` section. Region agents build only from that file, so every spawn kind, field and default goes in it,
with a DSL example. Test rooms `T1`/`T2` use `test=True` like `T0`, and are placed at `gx=-400 / -300`, `gy=0`.

## 2. Room DSL conventions (all kit content)
- Kit objects are placed through the existing `spawns=[{...}]` kwarg on `Room(...)`. Use `t: 'kit'` with `kind: '<name>'`
  (KM) or `t: 'sys'` with `kind: '<name>'` (KS), plus tile coords `x`, `y` and kind-specific fields. Register handlers in
  `SPAWNS` (read `09_main.js` for how spawns are dispatched). Don't add new single-character map tiles unless a thing
  really is a tile. The free tile chars left are `0 3 4 5 6 7 8 9 ! ? * [ ] { }`, minus any `registerTile` already
  uses; grep first. If you add one, reserve it in KIT_API.md.
- Wiring between objects uses string ids: `id: 'gateA'`, `targets: ['gateA', 'gateB']`, `group: 'bells1'`. Ids are
  local to a room.
- Anything that remembers state across visits (an opened gate, a solved puzzle, a cleared gauntlet, a found vista)
  stores it in `SAVE.flags['x3:<roomId>:<id>'] = 1`.
- Every kit object needs a region skin. Use a `skin:` field, defaulting to the room's biome, drawn from the kit sheets
  with per-biome palettes. At minimum a stone/wood/metal/crystal/neon variant that reads right in every biome.

## 3. LX — dynamic lighting (read `renderWorld`, `renderLighting`, `presentWorld` first)
Today's lighting paints a darkness layer over the world with soft holes cut at each light, plus a faint additive glow.
Replace it, when shaders are on, with a lighting pass in the WebGL shader:

1. **Lit and unlit layers.** `renderWorld` draws the lit scene (parallax, tiles, props, characters, weapons, water) into
   `low`. Everything that *emits* light (fx sprites, projectiles, particles of glowing kinds, spell effects, lava glow,
   light props' flames, boss glow parts) goes into a second canvas `lowFx`. The top overlays (`renderTop` hooks,
   `flashScreen`, the low-HP tint, the vignette, the boss-phase tint) go into `lowTop`. The shader composites
   `lit(low) + lowFx`, then `lowTop` on top, then the existing post effects. When shaders are off or unavailable,
   draw all three into `low` in that order and keep today's Canvas 2D `renderLighting`, so the fallback looks the same
   as now.
2. **Colored light buffer.** `addLight(x, y, r, color, k)` stays the public API. Add an optional 6th argument `o`
   (`{ flicker, shadow: false, height }`). The shader gets the lights on screen: cap 48, sorted by contribution, sent as
   uniform arrays or a small data texture. Each pixel gets `albedo × (ambient + Σ light)`. **Ambient** comes from
   `AREAS[biome]`: turn the current `ambient` darkness into an ambient color and level per biome (a cool blue-grey in
   the Catacombs, warm in the Deep, green in the Mire…). Put a table in `41_light.js`. Keep every existing darkness
   mechanic working: `darkT` phases, `snuffProof` lights, boss `ambient()`.
3. **Pixel-art falloff.** Quantize light into about 5 bands and use a 4×4 Bayer dither across each band edge, in
   game-pixel space (384×216), so it reads as hand-drawn and never as a smooth gradient. Add an option to turn the
   banding off (smooth).
4. **Tile shadows.** On `enterRoom`, upload an occluder mask (1 texel per tile) of the room's solid tiles (`SOLID`,
   not one-way `=`). In the shader, march from each pixel toward each shadow-casting light, 8–16 steps, soft edge,
   so walls, pillars and floors block light and light spills through doorways. Pixels inside solid tiles are lit from
   their surface only; don't black out wall faces the player sees. Tiles next to a light's own cell must not shadow it
   (lanterns hang on walls). Lights with `shadow: false` skip the test (big ambient fills, spell glows).
5. **Tile ambient occlusion.** At room load, bake an AO texture: open cells next to solid tiles darken toward the
   corner, and floor/wall seams get a soft contact shade. Apply it multiplicatively to the lit layer.
6. **Flicker.** Lanterns, candles, torches and braziers get `flicker: true` (find where they call `addLight`): a smooth
   noise on intensity and a little on radius, per light (seeded by position, so they don't pulse together).
7. **Glow stays bright.** `lowFx` is added after lighting, so fire, spells, eyes and lava stay bright in the dark and feed
   the bloom. Move boss/enemy parts that glow into `lowFx` where it's easy (eyes, cores, runes: grep for
   `addLight(` next to a draw call). A generic helper `drawGlow(fn)` that runs a draw callback into `lowFx` is enough.
8. **Settings.** In the Graphics menu (`GFX_ROWS` in `40_gfx.js`) add **Lighting**: `Classic` (today's look), `Dynamic`,
   `Dynamic + shadows` (default on desktop when shaders are on). Add **Light bands**: `Pixel` / `Smooth`. On phones
   keep shaders off by default, as now; if a phone turns shaders on, cap it at 16 lights and 8 shadow steps.
9. **Verify** in at least these rooms, with before/after screenshots: `R1` (outdoor dusk), `C2` (catacomb lanterns),
   `K1` (cathedral), `M2` (mire), `D2` (lava), `A2` (archives), `SP7` (Cindervane arena), `NV4` (necropolis), `NH2`
   (neon), a boss fight with spells flying, and a dark-phase boss (Morvain P2 or the Sovereign). Nothing may get
   unreadably dark. The player must always be readable: keep a soft personal light like today's
   `addLight(P.x, P.y - 16, 100, …)`. Report the frame time of the shader pass on this machine
   (`performance.now()` around `presentWorld`, averaged over 300 frames) for Classic and for Dynamic + shadows.

## 4. KM — kit mechanics (`t: 'kit'`)
Build each piece to be reused everywhere. Each piece gets a clean look in 3–5 skins, collision that never jitters or
traps the player, sound, and light (`addLight`) where it glows. The player standing on a moving thing must move with
it exactly, with no sliding or sinking. Find the existing `oneway` dyn platforms and `P.pushVx` and build on those.

**Moving parts**
- `mover`: a platform moving along waypoints `path: [[x,y],…]` (tile coords), with `speed`, `loop` or `pingpong`,
  `wait`. Can be `solid` or `oneway`, with width `w` in tiles. Optional `trigger: 'stand'` (starts when stood on) or
  `trigger: '<switchId>'`.
- `crumble`: a ledge that shakes and falls after `delay` (default 0.5 s) when stood on, and respawns after `respawn`
  (default 3 s; 0 = never).
- `sinker`: sinks slowly while stood on (`rate`), then rises back. For the Mire stones and the Dunes sands.
- `phase`: a platform that is solid only during its slice of a beat: `period`, `on: [start, end]` as fractions,
  `group`. Show a clear warning before it vanishes (blink or fade). For the Mirelight, Bellwalk and Glitch Run rooms.
- `lift`: a vertical `mover` preset with a chain drawn up to the ceiling.
- `swing`: a rope or vine the player grabs by touching it. Jump releases with the swing's momentum. `len`, `amp`,
  `period`, or player-driven. Drawn as rope, chain or vine by skin.
- `pendulum`: a swinging blade or axe (hazard): `len`, `period`, `phase`, `dmg`.
- `rising`: a rising hazard floor (lava, water, poison, sand) for chase rooms. Starts when triggered, has `speed`,
  stops at `stopY`, and resets on death or when a trial resets.
- `wind`: an area force (`w`, `h`, `vx`, `vy`), optionally on/off on a `period`. Reuse the Spire wind code if it fits.
- `spring` (optional): a bounce pad, only where a region asks for it.

**Puzzle parts**
- `lever` (strike or interact) and `switch` (stays down): toggle `targets`. `timer: 5` makes it revert after 5 s, with
  a ticking sound and a visible countdown.
- `plate`: a pressure plate, active while the player (or a `crate`, if you add one) stands on it.
- `gate`: a vertical barrier, tile-aligned `h` tiles tall, reaching the ceiling (EXPANSION2 §0). Opens and closes when
  its id is toggled. Can start `open`. `persist: true` stores the open state in a flag.
- `seq`: an ordered puzzle over `group` members. Members are any strikable kit objects: `bell`, `lantern`, `glyph`,
  `stop`, `frame`. `order: [ids]`. A wrong hit resets with a clear sound; the right order toggles `targets` and plays
  a chime. The clue is placed by the region agent.
- `beam` + `mirror`: a light beam from a source; mirrors rotate 45° per strike; the beam lights a `socket`, which
  toggles `targets`. The beam is drawn in `lowFx` if LX's API exists, else on `g`. It counts as a light.
- `level`: a fluid level (water, poison, slag) for a region of the room: `y` tiles, `states: [y0,y1,…]`, set by levers.
  Uses the existing water and poison hazard tiles where possible, or its own swim/poison volume.
- `brazier`: lit or unlit. Striking it toggles it (or a fire spell lights it). Can be a `seq` member or a `targets`
  source. Emits light when lit.

Put every piece in test room `T1` with a short labelled demo of each. Record a contact sheet of screenshots, and test
the player riding each moving part for 10 s without jitter (log P.y deltas).

## 5. KS — kit systems (`t: 'sys'`)
- **Doors and passages** (`door`): a pair of doors in two rooms: `{t:'sys', kind:'door', x, y, id:'d1', to:'ROOM', toId:'d1',
  look:'arch'|'crack'|'hatch'|'portal'|'ladder', auto: false}`. Interact to pass; `auto` passes on touch. Fade, arrive at
  the partner, facing out. Door pairs are validated at build time: every `to/toId` must exist and point back. Generalise
  the NEO-HALLOW warp (`36_neohallow.js`) instead of copying it. The world map must connect door-linked rooms visually
  (a dotted line between the two doors).
- **Hidden passages** (`passage`): an opening that is solid until a condition is true: `cond: { flag: 'boss:cindervane',
  restAfter: true, minTime: 300 }`, meaning the flag is set **and** (you rested at a shrine after it was set **or**
  `minTime` seconds have passed since). Store the set-time in `SAVE.x3.t['<flag>']` when the flag first gets set (hook
  flag writes, or check each room entry). When it opens on entry, play a crack and a chime, add a soft light and
  seeds or embers blowing through, and show it on the map only after you step through. This drives **The Last Field**
  (lead spec in the plan page).
- **Trials** (`trial`): place a `sigil` at the start and a `goal` (a chest or pedestal) at the end:
  `{t:'sys', kind:'trial', x, y, id:'tr', par: 45, reward: 'c_xxx', region: 'Spire'}`, and
  `{t:'sys', kind:'trial_goal', x, y, trial:'tr'}`. Interact with the sigil to start: stamina and FP refilled, timer on
  the HUD, air-attack/smash counters reset. Any damage or hazard touch (spikes, lava, pits, `pendulum`, `rising`)
  inside the trial resets you to the sigil **instantly**, with no HP loss and no death, and resets the trial's kit
  objects (movers, crumbles, rising floors) to their start state. Enemies inside a trial are allowed but rare. Reaching
  the goal stops the timer and opens the reward chest on the first clear. Beating `par` shows a gold mark and grants a
  small cinder bonus. Store the best time in `SAVE.x3.trials[id]`. Leaving the room aborts the trial. A trial must be
  retryable forever, and the reward can't be taken twice.
- **Gauntlets** (`gauntlet`): a challenge marker `{t:'sys', kind:'gauntlet', x, y, id:'g1', look:'banner'|'bell'|'stake'|'whistle'|'horn'|'idol'|'stones'|'drum'|'rack'|'terminal',
  gates: ['gL','gR'], waves: [[{type:'hollow_soldier', x, y}, …], …], reward: [...] }`. The room is walkable until you
  interact. Then the gates close (KM `gate`s), a "Wave 1/3" banner and counter show, and the waves spawn (existing
  enemy types from `ENEMY_CLASSES`, dropped in with a spawn effect). Clearing all waves reopens the gates, grants the
  reward once, and lights the marker permanently. It can be replayed later for cinders. Death inside resets it. A
  gauntlet must never be on the only route: the gates are open unless the fight is running.
- **Vista benches** (`bench`): sit (interact). The player sits (`rest` pose), and the camera eases out, either zooming
  out (render at a scale < 1, or widen the view rect; pick what works with the low-res canvas) or panning to a `view:
  [x,y]` focus point over 1.5 s. The music ducks to the region's ambient layer and a lore text box can appear (`lore:
  'page_id'`). Any input stands you up. The first sit logs the vista in `SAVE.x3.vistas`. No enemies may spawn while
  seated. Benches are safe spots but not shrines.
- **Lore pages** (`lore`): a stone, corpse or book prop that shows text when interacted with, and adds a page to the
  **Hallow Chronicle**: a new **Lore** section in the Inventory tab listing found pages by region. Page text lives in a
  registry `LORE_PAGES[id] = { region, title, text }` that region agents fill in. `lore` can also be attached to a
  `bench`.
- **Completion** (Status tab): per-region and total rooms visited, trials cleared (gold marks), vistas found, secrets
  found (rooms with `secret=True`), gauntlets cleared and lore pages.
- **Map upgrade** (`renderMap`): zoom (3 levels) and pan (arrow keys and left stick; the map opens centred on the
  player) for a world about twice the current size. Icons: shrine (existing), trial (sigil; gold when under par),
  gauntlet (banner), puzzle (only rooms with `puzzle=True` kwarg), vista (bench; only after found), secret, door
  links. A locked icon on rooms whose `needs` kwarg lists an ability you don't have. A small legend and a region
  filter. Travel (`29_ui2.js` shrine map) stays as it is. The regular map must stay fast with 270 rooms.
- **Reachability check** (`tools/reach.py`, run by `tools/rooms.py` validation): for each room, flood-fill the
  player's reachable standing cells from each entrance, using the real movement numbers from `04_player.js` (jump
  height and distance from `JUMP_V`, `GRAV_UP/DN`, `MAXV`, air dash, wall jump if `needs` includes it, double jump,
  hook points `@`, glide, triple jump). Every exit, item, chest and trial goal must be reachable under the room's
  `needs` (a Room kwarg: a list like `['talon', 'wings', 'hook', 'emberdash', 'gale', 'slam', 'tidebreath',
  'moonstep']`). Kit movers and platforms count as their swept area (an approximation is fine). Report ERR lines like
  the rest of validation; `STRICT=1` fails the build. Old rooms without `needs` are checked leniently: warnings, not
  errors. Don't break the build over old rooms.
- **Placement helper**: `tools/rooms.py` already errors on overlaps and leaks. Add a `free_spot(near_gx, near_gy, w, h,
  zone)` helper that region agents can call from their region files to find a free rectangle in their zone, and a
  `--zones` printout of free space.

Put every system in test room `T2` (and a small partner room for the door). Test: a door round trip, a passage that
opens after a rest, a trial clear and a reset on spikes, a gauntlet run, bench sitting, a lore page, and the map with
the icons.

## 6. Final report (every Phase 0 agent)
Report as plain text: what you built, where, the API summary (KM/KS also in KIT_API.md), `SHARED EDITS:`, `NEEDS:`,
test results with screenshot paths, known issues, and frame-time numbers (LX).

## 7. Phase 1/2: region agents
Added by the lead after Phase 0 lands: zones, room id ranges, anchors, rewards registry (13 trial charms, lore pages)
and per-region room assignments from `docs/expansion3_rooms.json`.
