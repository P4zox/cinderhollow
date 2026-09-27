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

## 7. Phase 1/2 — region agents (everyone reads this whole file, then `docs/KIT_API.md`)
Build the rooms listed for your regions in `docs/expansion3_rooms.json` (the plan page `docs/expansion3_plan.html`
shows the same list, with the reasoning per region). Names, types, sizes and ideas are the brief. You may adjust a size
by ±25% or reword a name if the room plays better, but keep the type and the spirit. Build **every** room on your
list. Build with the kit (`docs/KIT_API.md`) and each region's own tiles, enemies, hazards and parallax.

### 7.1 Agents, regions, files
| Agent | Regions (build order) | Room files (new) | Engine file (new) | Art (new) / asset prefix |
|---|---|---|---|---|
| **RA** | Ashen Ramparts, Rootbound Catacombs, Sunken Cathedral | `tools/regions/80_ra.py` | `web/src/50_ra.js` | `art/gen_xra*.py` / `xra_` |
| **RB** | Weeping Mire, Ashen Archives, Hoarfrost Aqueduct | `tools/regions/81_rb.py` | `web/src/51_rb.js` | `art/gen_xrb*.py` / `xrb_` |
| **RC** | Stormward Spire (+ **The Last Field** and the **Ember Hatchling** spell), The Deep, The Crown | `tools/regions/82_rc.py` | `web/src/52_rc.js` | `art/gen_xrc*.py` / `xrc_` |
| **SA** | Thornveil Wood, Drowned Barrows, Crimson Manor | `tools/regions/83_sa.py` | `web/src/53_sa.js` | `art/gen_xsa*.py` / `xsa_` |
| **SB** | Necropolis of Vael, Sunscorched Dunes | `tools/regions/84_sb.py` | `web/src/54_sb.js` | `art/gen_xsb*.py` / `xsb_` |
| **SC** | Starfall Crater, NEO-HALLOW, The Ember, The Hermit's Hollow | `tools/regions/85_sc.py` | `web/src/55_sc.js` | `art/gen_xsc*.py` / `xsc_` |

Build: `BUILD_OUT=web/dist/<agent>.html python3 web/build_web.py`. Tests go in `tools/shots/<agent>/`. Everything else is
read-only (use `NEEDS:`). **Old rooms of your own regions** may be patched **only from your own room file** with
`ROOM('K3')` (it runs after the old modules): add `door`/`passage` spawns, open a wall where your zone touches it, add
a lore stone. Never move, resize or re-lay an old room, and never break its existing routes, items or boss arena. Old
rooms of other agents' regions are off limits.

### 7.2 Zones (global tile coords; every new room lies fully inside its region's zone)
| Region | Zone x | Zone y | Notes |
|---|---|---|---|
| Ramparts | −112…15 | −90…−1 | directly above `R1` (outdoor, open sky); a room here can join R1's open top edge |
| Rootbound Catacombs | −330…−113 | 43…112 | door-linked pocket |
| Sunken Cathedral | 372…491 | −160…−15 | above `K3s`/`K4` (K3s top edge at y 0) |
| Weeping Mire | 150…227 | 99…180 | below `M6`/`M2` |
| Ashen Archives | 250…371 | −160…−61 | above the Archives (A7 top at y −60) |
| Hoarfrost Aqueduct | 150…249 | −160…−39 | above `HF6`/`HF7` |
| Stormward Spire (+ Last Field) | −112…149 | −220…−91 | above the Stormspire (SP7 top at y −90) |
| The Deep | 228…399 | 135…260 | below `D5` |
| The Crown | 565…760 | −13…39 | east of `X5` (X5's east edge is x 564) |
| Thornveil Wood | −330…−141 | −120…42 | west; **avoid the test rooms T0 (−200,0), T1 (−400,0), T2 (−300,0)** |
| Drowned Barrows | 585…760 | 84…220 | door-linked pocket |
| Crimson Manor | 453…564 | 41…83 | touches `CM7`/`CM4`'s east edge (x 452) |
| Necropolis of Vael | −112…149 | 113…260 | below the Necropolis (bottom y 112) |
| Sunscorched Dunes | 400…584 | 147…260 | below `DU8` (bottom y 146) |
| Starfall Crater | 492…760 | −220…−93 | above the crater (tops at y −92) |
| NEO-HALLOW | 1000…1400 | −150…150 | its own district |
| The Ember | 565…760 | 40…83 | door-linked from the Ember rooms |
| The Hermit's Hollow | −140…−41 | 0…14 | west of `H1`; the vista becomes 32×14 so it fits |

Use `free_spot(...)` from KS to place rooms inside your zone. `python3 tools/rooms.py` must report **0 errors**
(overlap, leaks, doors, reachability) with `STRICT=1`.

### 7.3 Room ids, kwargs and structure
- **Ids** continue each region's prefix after its highest existing number: Ramparts `R5…`, Catacombs `C7…`, Cathedral `K5…`,
  Mire `M7…`, Archives `A8…`, Hoarfrost `HF8…`, Spire `SP8…`, The Last Field `LF1`, Deep `D9…`, Crown `X6…`, Thornveil
  `TV9…`, Barrows `DB10…`, Crimson `CM9…`, Necropolis `NV8…`, Dunes `DU9…`, Starfall `SF10…`, NEO-HALLOW `NH8…`, Ember
  `E4…`, Hermit `H2…`. The build's duplicate-id check catches collisions.
- New rooms use their region's **biome** (music, ambient, enemy scaling, region card). The Last Field gets its own biome
  `lastfield`, registered by RC.
- Kwargs on every new room: `needs=[...]` (abilities the room requires, for reachability and the map lock icon),
  `x3=True`, and one of `puzzle=True` / `secret=True` / `vista=True` / `trial=True` / `gauntlet=True` / `grand=True` /
  `parkour=True` (path rooms have none). KS's map and completion code reads these.
- **Structure: wings, not dead ends.** Each region's new rooms form one or two **wings**. A wing branches off an old room
  of the region (a clear, signposted archway, crack or door), runs through its path rooms as a spine, and **loops back**
  into a *different* old room of the region, opening a shortcut the first time you come out. Vistas, trials, puzzles,
  secrets and gauntlets hang off the spine. At least one wing per region should start next to the main route, so
  players find it without a guide. Never change the story's critical path.
- **Gating:** main-path/spine rooms need at most what the plan's `needs` says (`start` means none; `wall jump` =
  `talon`). The double jump (`wings`) is in an optional secret room, so never require it outside trials and secrets.
  Rooms that need later abilities show a visible, tantalising reason to come back (a hook point just out of reach, a
  cracked floor).
- **Trials:** story-region trials are "one step below Hollow Knight's White Palace". Side-region trials (and the Ember's
  final trial) are full White Palace difficulty. Every trial must be cleared once by a scripted headless run, or by
  proof via `tools/reach.py` plus a recorded manual route, before you report it done. Set `par` about 25% above your
  own clear time.
- **Puzzles:** the clue is always in the game (a mural, a book, a hymn sheet, glowing veins) and readable without outside
  knowledge. After 3 wrong attempts, show a gentle hint toast. A solved puzzle stays solved.
- **Vistas:** a bench (KS `bench`), a composed view (parallax or a big painted backdrop, with a `view` focus point),
  ambient-only music, a lore page, and **no enemies**. They should be the prettiest rooms in each region.
- **Grand rooms:** 2–3 distinct routes (high, low, secret) and at least one landmark you can see from far away. Check
  that 60 fps holds with lighting on.
- **Gauntlets:** opt-in (KS `gauntlet`), never on the only route, 3 waves plus an elite, using the region's existing
  enemies.

### 7.4 Rewards registry
- **Trial charms** (define with `registerGear` in your engine file, draw the icon in your art, and implement the effect
  with `charmOn` hooks; keep effects fair, since they stack with everything):
  Cathedral `c_x3_chime` *Chime of Ascent* (double jump 15% higher) · Archives `c_x3_ink` *Inkbound Grapple* (Root
  Hook 30% longer reach, faster pull) · Hoarfrost `c_x3_rime` *Rime Heart* (Ember Dash chills foes it passes through) ·
  Spire `c_x3_storm` *Stormglass Feather* (glide 25% faster, stronger updrafts) · Deep `c_x3_slag` *Slagwalker's
  Sole* (the first lava touch in 10 s bounces you out unharmed) · Crown `c_x3_crown` *Sovereign's Sigil* (techniques
  cost no stamina, +8% damage) · Thornveil `c_x3_thorn` *Thornstep Ring* (air-attack limit 3 instead of 2) · Barrows
  `c_x3_lung` *Drowned Lung* (double breath, swim 25% faster) · Necropolis `c_x3_hood` *Headsman's Hood* (a roll
  through an attack at the last moment slows time for 1 s) · Dunes `c_x3_scarab` *Scarab Wing* (no landing lag from
  any height) · Starfall `c_x3_moon` *Moonlit Stride* (floatier jump apex, +8% run speed) · NEO-HALLOW `c_x3_glitch`
  *Glitch Driver* (air dash 35% longer with damaging afterimages) · Ember `c_x3_flame` *Heart of the First Flame*
  (all spell and art cooldowns 30% shorter).
- **Other rewards:** gauntlets, puzzles and secrets pay in `emberstone` (weapon upgrades), `shard` (+1 skill point),
  `seed` (+1 flask), `gold` (cinders) and lore pages. Budget per region: 2 emberstones, 1 shard and at most 1 seed,
  spread across its side rooms.
- **Lore:** each region writes 3–6 `LORE_PAGES` (vistas, secrets, lore stones) in the game's voice. It's grave, sparse
  and specific, never modern or jokey (NEO-HALLOW's Dev Room is the one exception). Page ids are `<agent>_<n>`.
- **RC only:** the Ember Hatchling spell (`sp:ember_hatchling`, FP 30, `cd: 25`, a summoned drake cub for 10 s: spits
  fireballs at the nearest enemy, dives to bite and burn, damage scales like other spells, one cub at a time, can't be
  hit). It comes with its cub sprite (appear/fly/spit/dive/vanish), icon, pickup, lore and The Last Field room exactly
  as specified on the plan page.

### 7.5 Quality bar and done
- Every new room is enterable and exitable both ways, passes STRICT validation and reachability, and is covered by the
  stress sweep (add your rooms to `tools/shots/spots.json` via a copy in your test folder, or pass them into your own
  sweep script).
- Look at a screenshot of **every** new room (Read the PNGs). Fix empty-looking rooms, misaligned tiles, floating props,
  unreadable darkness and overlapping decor. Rooms should look hand-built and rich, not generated.
- Final report: the room list with ids, zones used, anchors patched (`SHARED EDITS:`), `NEEDS:`, test results and a
  contact-sheet path, known issues.

## 8. Integration pass: walkable wings, no doors (binding; supersedes §7.2 zones and the door-based wing links)
The user wants every new room reachable **by walking**, like the original world. No doors, ladders, hatches or
teleports between rooms. To make room, `tools/rooms.py` now moves whole regions (`world_shift`):
- `spire`, `archives` and `starfall` old rooms move **up 70**.
- `necropolis`, `mire`, `deep`, `dunes`, `barrows` and `crimson` old rooms move **down 90**.
- Everything else stays.

**Coordinates:**
- Old rooms keep their original coordinates in their source files and are shifted when they're built.
- New rooms (`x3=True`) are placed in **final world coordinates**.
- `python3 tools/rooms.py --show` and `--zones` print the final layout.

**Connector shafts.** The six old links the move cut are rejoined by generated shafts, W1–W6 (`WORLD_LINKS` in
rooms.py): W1 R3–SP1, W2 C2–NV1, W3 C3–M1, W4 K2–DB1, W5 K3–A1, W6 X4–SF1. Each one is a plain zigzag of one-way
ledges. The owning agent may redesign or dress it by patching `ROOM('Wn')` from their own room file. They can make it
wider, add rooms beside it or run it through their wing, as long as both ends still meet the original openings and it
stays climbable with the needs of the rooms it joins. Owners: W1 RC, W2 RA, W3 RB, W4 SA, W5 RB, W6 SC.

### 8.1 New zones (final coordinates; every new room of yours fits inside, and nobody else's does)
| Agent | Region | Zone |
|---|---|---|
| RA | Ramparts | x −112…99, y −69…−1 (above R1–R3; R4's top too if you reach it) |
| RA | Catacombs | x 36…145, y 57…145 (below C1–C4; W2 runs through it at x≈83–88) |
| RA | Cathedral | x 252…347, y −69…13 plus x 356…419, y −69…−15 (above K1, K2, K3s; W5 is at x≈349–355) |
| RB | Mire | x 153…252, y 57…145 (above M1–M6, below C5/C6) |
| RB | Archives | x 250…371, y −260…−131 (above the Archives) |
| RB | Hoarfrost | x 150…249, y −200…−39 (above HF5–HF7) |
| RC | Spire + The Last Field | x −112…149, y −260…−141, plus x −112…15, y −140…−70. **LF1 must sit directly against SP7's west wall**, opened by the hidden `passage` (see §8.2). |
| RC | Deep | x 228…399, y 225…350 (below the Deep) |
| RC | Crown | x 565…760, y −80…−1 (east of X5) |
| SA | Thornveil | x −112…35, y 43…140 (below TV2–TV5) |
| SA | Barrows | x 253…379, y 29…117 (above DB1–DB5, below K2/K4; W4 is at x≈335–340) |
| SA | Crimson | x 380…600, y 61…111 (above the Crimson rooms) |
| SB | Necropolis | x −112…149, y 203…330 (below) |
| SB | Dunes | x 400…600, y 237…350 plus x 585…760, y 112…236 |
| SC | Starfall | x 492…760, y −300…−163 plus x 749…900, y −170…−70 |
| SC | NEO-HALLOW | x 1000…1400, y −150…150 (unchanged; its portal stays a portal) |
| SC | Ember | x 525…760, y 0…60 plus x 452…524, y 41…60 |
| SC | Hermit's Hollow | x −140…−41, y 0…14 |
Test rooms T0–T2b are not in any zone.

### 8.2 What to change
1. **Re-place every new room** in your zone so each wing touches its region's (shifted) old rooms **edge to edge**:
   - Open a wall segment in the old room (`ROOM('X').open(...)` or fill/put from your file) and a matching opening in
     your room.
   - The entry and the loop-back are real openings you walk, jump or drop through.
   - Rooms inside a wing connect by edges too.
2. **Remove every `door` spawn** that links rooms (anchors and internal ones). Allowed exceptions:
   - the NEO-HALLOW entry portal (it was always a portal);
   - one-way shortcut **gates** (KM `gate` + lever) at the loop-back;
   - **hidden `passage`s** that open wall cells in place, such as The Last Field in SP7's west wall and the Hermit's wall.
   
   A key-locked study or a sealed crypt becomes a **gate** (or passage) in a wall you walk through once it's open.
3. **Add shrines** throughout the new areas. Every wing gets at least one shrine; grand/large wings (and the Spire,
   Deep, Starfall and Dunes wings) get two:
   - Put one near the start of the wing and one near the far end or before a trial/gauntlet cluster.
   - Use map char `'S'` with the room kwarg `shrine='<Name>'`, one shrine per room, on solid ground with 3 free cells above.
   - The names must be new and in the region's voice.
   - They appear on the travel map automatically, so check that one travel map screenshot shows them.
4. **Vertical edges** follow the old rules. A climb up through a floor opening needs ledges or a wall-jump shaft that
   the room's `needs` allow. A drop down needs a readable way back or a marker (EXPANSION2 §0).
5. **Keep everything else as is:** the rooms' contents, puzzles, trials, rewards and lore. Change a room's size only
   where the new placement needs it.

### 8.3 Reachability
KS is fixing the limits you reported in `tools/reach.py`:
- swimming;
- outdoor top edges;
- bottom-entrance jumps;
- seed-span starvation;
- glide length and updraft drift;
- pruned wall-jump shafts.

Until that lands you may iterate with `NOREACH=1`, but your final state must pass full reachability under `STRICT=1`
with zero ERR lines on your ids and on the old rooms you patched. Use `reach_ignore` only for a mechanic the checker
truly can't model, and name it in your report.

### 8.4 Done means
- **Validation:** `STRICT=1 python3 tools/rooms.py` shows 0 ERR on your ids (including W shafts you own).
- **Doors:** `grep "kind='door'\|kind: 'door'"` finds no door in your files except the allowed ones.
- **Walk test:** a headless test walks each wing **without teleporting inside it**. It enters from the old room, goes
  through the spine to the loop-back, then back again, and logs every room change. Every edge between two of your
  rooms, and between your rooms and old rooms, is crossed at least once in each direction where that direction is
  meant to be possible.
- **Phantom damage:** stand still for 3 s on every floor spot you can reach in each new room, with enemies removed,
  and confirm there is no damage except from visible hazards. This is how the lead found a leftover void bug in RA's
  code: region state that wasn't reset per room.
- **Regressions:** `tools/shots/stress.js` and `tools/shots/dormant_chk.js` are clean.
- **Report:** a contact sheet of every room, plus the world map (zoomed out) showing your wings attached.
