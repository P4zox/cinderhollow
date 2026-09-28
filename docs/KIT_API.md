# Cinderhollow — Kit API (Expansion 3)

Region agents build rooms only from this file. Kit objects are placed with `spawns=[{...}]` on a `Room(...)`:
`t: 'kit'` (mechanics, section written by KM) or `t: 'sys'` (systems, section written by KS). Coordinates are tile
coordinates inside the room (`x`, `y` = the cell the object stands in, one row above its floor). Ids are local to a room.

## Mechanics

Engine: `web/src/42_kit.js`. Art: `art/gen_kit.py` + `art/kit_draw.py` → `assets/kit_plat` (16×16 slab pieces),
`kit_gate` (gate bars/caps, lift shackles, rope anchors), `kit_parts` (32×32 props). Live demo of every part: test room
**T1** (`tools/regions/95_kit_test.py`, `__game.tp('T1', x, y)`; five floors stacked vertically, rows 0/20/40/60/80).

### Placing, skins, wiring (read first)
```python
Room('XX1', …, spawns=[
    dict(t='kit', kind='mover', x=10, y=8, w=3, path=[[10, 8], [18, 8]], speed=2),
    dict(t='kit', kind='lever', x=4, y=10, id='L1', targets=['gA']),
    dict(t='kit', kind='gate',  x=22, y=10, id='gA'),
])
```
- **Coordinates are tiles.** Three conventions, by kind:
  - *slabs* (`mover lift crumble sinker phase`): `x` = left tile, `y` = the row the slab lies in; its walkable top is the
    top edge of row `y`, exactly like a `=` tile. The slab is 8 px thick, `w` tiles wide.
  - *standing props* (`lever switch plate crate spring brazier lantern gate`): `x, y` = the empty cell they stand in (the
    floor is row `y+1`), same as enemies.
  - *hung / wall props* (`bell glyph stop frame mirror socket beam`, `swing`/`pendulum` anchors): `x, y` = the cell they
    occupy. Bells, ropes and blades hang from the top of that cell (put them right under a ceiling).
  - *areas* (`wind level rising`): `x, y, w, h` (see each kind).
- **Skins:** every part takes `skin: 'stone'|'bone'|'wood'|'iron'|'crystal'|'neon'` (a biome name also works). Default =
  the room's biome: ramparts/cathedral/barrows → stone · catacombs/necropolis/crown/dunes → bone · mire/archives/
  thornveil/crimson/hermit → wood · spire/deep/ember → iron · hoarfrost/starfall/sov_void → crystal · neohallow → neon.
  Neon gates are laser gates; neon/crystal/stone beams are cyan/starlight/sunlight.
- **Ids** (`id: 'gA'`) are local to the room. **Sources** (lever, switch, plate, seq, socket, and bell/lantern/glyph/stop/
  frame/brazier when not in a seq) have an `active` state and a `targets: [ids]` list. **Consumers** (gate, mover, lift,
  wind, beam, level) derive their state every frame from the sources that target them, combined by `logic`:
  `'toggle'` (default: flips once per active source — XOR), `'any'` (on while ≥1 is active), `'all'` (on only while every
  source targeting it is active). The result is XORed with the consumer's start state (`open: True` on a gate, a mover
  runs by default). A consumer can also *pull* from a source with `trigger: '<sourceId>'` (runs while that source is
  active). `level` uses a count instead (see below).
- **Persistence:** `persist: True` stores state in `SAVE.flags['x3:<room>:<id>']` (needs an `id`). Defaults: levers and
  switches without a `timer` persist; seqs and sockets persist (a solved puzzle stays solved); a gate with
  `persist: True` stays open for good once it has opened (use it for shortcuts); mirrors remember their rotation
  (`SAVE.x3.kit`). Everything else resets when you re-enter the room.
- **Sound, light, prompts** are built in (strike or interact with E on every strikable part; lit parts call `addLight`).
- **Build check:** `95_kit_test.py` lints every `t:'kit'` spawn in region modules numbered below 95 and prints `ERR` lines
  (unknown kind, wiring to a missing id, seq order ids that aren't members, gates that don't reach a ceiling, missing
  ids on gates/levels/seqs/sockets/seq members, mover paths outside the room). Fix them like room errors.

### Moving parts
| kind | fields (default) | notes |
|---|---|---|
| `mover` | `x, y`, `w` (3), `path` `[[x,y],…]` tile coords of its left end (none = static slab), `speed` tiles/s (2), `loop` (False = ping-pong), `wait` s at stops (0.5), `solid` (False = one-way), `trigger` (`'stand'` or a source id), `return` s (0; with `'stand'`: drift home after that long unridden), `offset` 0..1 (stagger along the path), `delay` s | Eases into and out of stops. `trigger:'stand'` waits at each end until stood on (use with ping-pong paths). Solid movers never crush the player: they wait. Enemies and crates ride too. |
| `lift` | `x, y` home stop, `to` other stop row (y−6), `w` (3), `speed` (3), `wait`, `auto` (False), `call` (True), `trigger`, `solid` | Chains run to the ceiling. Default: stand on it to ride; stand on the landing next to its shaft to call it. `auto: True` = runs up and down forever. For a floor-level stop, dig the floor out under the lift (T1 floor 0). |
| `crumble` | `x, y`, `w` (2), `delay` s (0.5), `respawn` s (3; 0 = never), `solid` | Cracked look telegraphs it. Shakes, drops, fades back in only when nobody is in the way. Crates trigger it too. |
| `sinker` | `x, y`, `w` (2), `rate` tiles/s (0.75), `depth` tiles (3, stops on the bottom), `delay` s (0.15), `rise` tiles/s (1) | Sinks while stood on, rises when left. Put it on top of a pool (`~` poison, `"` water, or a `level`) for the Mire/Dunes. |
| `phase` | `x, y`, `w` (2), `period` s (2), `on` `[a, b]` fractions of the period it is solid (`[0, 0.5]`; wraps if a > b), `offset` 0..1, `warn` s (auto ≈ 35% of the on-time, max 0.45), `group` | Solid only in its slice of the beat; blinks faster before it vanishes; a faint dotted outline shows where it will be. Never re-solidifies into a body. All phases share the room clock (starts at 0 on entry). |
| `swing` | `x, y` anchor, `len` tiles (5), `amp` degrees (25), `period` s (2.6), `phase` 0..1, `drive` (`'player'` or `'auto'`), `rope` (`'rope'|'chain'|'vine'|'cable'`, by skin) | Touch it in the air to grab (hold ↓ to fall past). ←/→ pump, ↑/↓ climb, jump lets go with its momentum (+ refreshes air jump/dash), roll drops. `'auto'` ropes carry you on their own schedule (kite lines). Can't loop over the anchor. |
| `pendulum` | `x, y` pivot, `len` tiles (4), `period` s (2.2), `amp` degrees (60), `phase` 0..1, `dmg` (30 × NG+) | Blade hazard (hits within 10 px of the blade centre), once per swing; `hurtPlayer(..., {src, kit:'pendulum'})`. The blade centre hangs `len` tiles below the top of the pivot cell; to sweep a standing player, its lowest point should be ~1 tile above the floor (T1: pivot row 30, floor row 37, `len` 6). |
| `rising` | `x` (0), `w` (room), `y` = the empty row just above where it starts (flush with that row's floor), `stopY` row (1), `speed` tiles/s (1.2), `delay` s (1.2), `fluid` (`'lava'|'slag'|'poison'|'water'|'sand'|'data'`), `trigger` (`'enter'`; `'zone'` + `zone: [x,y,w,h]`; or a source id), `respawn` `[x, y]` (where you stood when it started), `goal` `[x,y,w,h]` (reaching it drains it), `dmg` fraction of max HP (by fluid, lava 0.3), `msg` | Chase floor. Touch it: damage + back to `respawn`, floor reset and re-armed. Drawn only over open cells (it climbs between the walls). Resets on `kitReset`. |
| `wind` | `x, y, w` (4), `h` (4), `vx`, `vy` px/s, `period` s (0 = always on), `on` `[a, b]`, `offset`, `trigger` | Pushes the player inside the area (`P.pushVx`; ×1.15 in the air). `vy < 0` is an updraft that lifts you while airborne (−200 ≈ climbs steadily). Gusts show a faint warning 0.6 s before. Streaks show direction. |
| `spring` | `x, y`, `power` px/s (520 ≈ 13 tiles high) | Bounce pad; the full arc happens whether or not jump is held. Refreshes air jump/dash. Bounces crates. |
| `crate` | `x, y` | Push it by walking into it; stand on it; it falls, rides movers, presses plates, blocks beams. Back to its spot on re-entry, on `kitReset`, or if it falls out of the room. |

### Puzzle parts
| kind | fields (default) | notes |
|---|---|---|
| `lever` | `x, y`, `id`, `targets`, `timer` s, `once` (False), `on` (False = start state), `persist` (True unless timer), `msg`, `face` | Strike or E flips it. With `timer` it snaps back after that long, ticking faster near the end, with a countdown ring above; striking it again re-arms. `once`: can't be flipped back. |
| `switch` | same as lever | A button that stays down once pressed (strike / E); `timer` pops it up again. |
| `plate` | `x, y`, `w` (1), `id`, `targets`, `latch` (False), `timer` s | Active while the player, a crate or an enemy stands on it (flush with the floor). `latch`: stays down. `timer`: stays down that long after you step off. |
| `gate` | `x, y` = its bottom cell, `id`, `h` (auto: up to the first solid tile above), `open` (False), `logic`, `persist`, `msg` | Bars slide up into the ceiling; neon = lasers that switch off. It always reaches a ceiling (leave `h` out; a short `h` or no ceiling logs a warning and a lint ERR). Closing never traps the player: they're shoved out the side they're on. KS gauntlets close it with `kitForce(id, false)`. |
| `seq` | `x, y` (any free cell; invisible), `id`, `group`, `order` `[member ids]`, `targets`, `persist` (True), `msg` | Ordered puzzle over every member with the same `group`. Right strike: that member lights; the full order → chime, all members stay lit, targets toggle. Wrong: dissonant sting, the member flashes red, all go dark. Place the clue yourself (lore, carving, grave text). Repeated ids in `order` are fine. |
| `bell` | `x, y` (hangs from the cell top), `id`, `group`, `note` 0..9, `targets` | Rings a pitched bell. Reach: a jump attack from the floor hits a bell hung 4–5 rows up. |
| `lantern` | `x, y` (standing), `id`, `group`, `on` | Lit = warm light. Standalone: strike toggles it. |
| `glyph` | `x, y` (wall tablet in that cell), `id`, `group`, `sym` 0..7 (rune shape), `note` | For ciphers: eight distinct runes. |
| `stop` | `x, y` (wall organ stop), `id`, `group`, `note` | For hymn puzzles: plays its note. |
| `frame` | `x, y` (portrait, centred a little above the cell), `id`, `group` | Eyes glow red when lit. |
| `brazier` | `x, y` (standing), `id`, `group`, `lit` (False), `targets` | Strike toggles it; a spell or a fire weapon only lights it. Flame colour by skin (orange; blue for bone/crystal; cyan for neon). As a source, active = lit. |
| `beam` | `x, y`, `dir` (`'right'|'left'|'up'|'down'|'ur'|'ul'|'dr'|'dl'`), `id`, `trigger`/`logic` (on by default), `style` (`'sun'|'star'|'neon'`, by skin) | Emitter. The beam travels cell to cell (8 directions), stops at solid tiles, closed gates, solid movers, crates and other emitters, and is drawn through LX's `drawGlow` with lights along it. |
| `mirror` | `x, y`, `id`, `rot` 0..3 (`0 = —`, `1 = \`, `2 = |`, `3 = /`), `fixed` (False), `persist` (True) | Strike to turn 45°. Reflection: `—`/`|` send a beam back or let it pass edge-on; `/` turns right→up, up→right, left→down, down→left; `\` turns right→down, down→right, left→up, up→left. |
| `socket` | `x, y`, `id`, `targets`, `persist` (True), `msg` | Lights (and toggles its targets) when a beam reaches it. With `persist: False` it goes dark when the beam leaves. |
| `level` | area `x, y, w, h` (`y` defaults to the highest state, `h` to the room bottom), `states` `[row, …]` surface rows, `start` index (0), `id`, `fluid` (`'water'|'poison'|'slag'|'lava'|'sand'|'data'`), `speed` tiles/s (1.5), `dmg` | The surface sits on `states[start + number of active sources targeting id]` (clamped): two valves → three heights. Fills only open `.` cells in the area (leave the basin empty; walls contain it). `water` writes the Barrows deep-water tile (swim with Tidebreath, floating without), `poison` the rot water `~`; slag/lava/sand/data hurt like `rising` and send you to safe ground. |
| `label` | `x, y`, `text` | Debug caption, drawn only in `test=True` rooms. |

### DSL examples
```python
# Winch House: two timed winches must both be up for the portcullis (T1 floor 2)
dict(t='kit', kind='lever', x=80, y=56, id='W1', targets=['g5'], timer=6),
dict(t='kit', kind='lever', x=90, y=56, id='W2', targets=['g5'], timer=6),
dict(t='kit', kind='gate', x=94, y=56, id='g5', logic='all'),
# pressure plate + crate
dict(t='kit', kind='crate', x=40, y=56), dict(t='kit', kind='plate', x=45, y=56, w=2, id='pl1', targets=['g1']),
dict(t='kit', kind='gate', x=51, y=56, id='g1', logic='any'),
# a shortcut lever that stays open forever
dict(t='kit', kind='lever', x=3, y=10, id='sc', targets=['sg'], once=True), dict(t='kit', kind='gate', x=8, y=10, id='sg', persist=True),
# the Dirge: bells in order
*[dict(t='kit', kind='bell', x=5 + 4 * i, y=72, id=f'b{i+1}', group='dirge', note=[0, 2, 4, 5][i]) for i in range(4)],
dict(t='kit', kind='seq', x=20, y=76, id='dirge', group='dirge', order=['b3', 'b1', 'b4', 'b2'], targets=['gd']),
# a lift called from either landing; a crumbling bridge; sinking stones on poison
dict(t='kit', kind='lift', x=49, y=17, to=5),
*[dict(t='kit', kind='crumble', x=x, y=14, w=2) for x in (65, 69, 73)],
*[dict(t='kit', kind='sinker', x=x, y=17, w=2, depth=2) for x in (81, 85, 89)],
# Glitch Run: four beat platforms, each solid for half the beat, a quarter apart
*[dict(t='kit', kind='phase', x=5 + 4 * i, y=35, w=2, period=2.4, on=[i / 4, (i / 4 + 0.5) % 1]) for i in range(4)],
# vine swing / headsman's axes / lava chase / valve room / sunlight puzzle
dict(t='kit', kind='swing', x=44, y=20, len=9, rope='vine'),
dict(t='kit', kind='pendulum', x=66, y=30, len=6, phase=0.33),
dict(t='kit', kind='rising', x=43, y=96, w=17, stopY=83, speed=0.9, fluid='lava', zone=[43, 93, 8, 4], respawn=[40, 96], goal=[50, 80, 9, 2]),
dict(t='kit', kind='level', x=6, y=88, w=13, h=11, states=[98, 93, 89], fluid='water', id='lvl'),
dict(t='kit', kind='lever', x=3, y=96, targets=['lvl']), dict(t='kit', kind='lever', x=21, y=96, targets=['lvl']),
dict(t='kit', kind='beam', x=77, y=75, dir='right'), dict(t='kit', kind='mirror', x=84, y=75, id='M1', rot=0),
dict(t='kit', kind='socket', x=92, y=72, id='so1', targets=['g9']),
dict(t='kit', kind='wind', x=18, y=42, w=3, h=15, vy=-200),   # an updraft shaft
```

### JS API (for KS and region code)
- `kitReset(roomId, {all})` — back to the start state: movers/lifts/sinkers/crumbles/phases (room clock → 0), ropes (drop
  the player), rising floors, crates. `{all: true}` also resets puzzle parts (levers, switches, plates, seqs, members,
  mirrors, gates, levels) — without it, trials don't undo puzzles. Only acts if `roomId` is the current room.
- `kitForce(id, bool)` — force a consumer's state (gate: `true` = open); `kitForce(id, null)` releases it to its wiring.
- `kitOn(id)` — a source's `active` / a consumer's current state.
- `KIT.onChange.push((id, value, obj) => …)` — called when a source flips or a gate/level changes.
- `KIT.objs`, `KIT.byId[id]` — the room's kit objects (`kind`, `id`, `active`/`on`, `reset()`); they are also in `props`
  (type `kit_<kind>`, with `hurtbox/onHit/interact/prompt` where strikable).
- Hazard damage: pendulums go through `hurtPlayer(dmg, dir, id, {src, kit:'pendulum'})`. Rising floors and hurting levels
  run `HOOKS.playerHurt` with `opt = {src, kit, hazard: true, fire}` before applying damage; a hook that returns `0`
  cancels it (no damage, no respawn: the hook owns the reset, as a trial does).
- Riding: slabs are `room.dyn` entries `{x0,x1,y0,y1,on,kit}`; `moveBody` lands bodies on a dyn's own top
  (`dynTopAt` in `03_world.js`), and kit slabs move after the player's physics each frame, carrying riders by the same
  whole-pixel delta, so a rider never slides, sinks or jitters. Jumping off a moving slab keeps a little of its sideways
  speed. A kit slab is never remembered as a spike-respawn spot (`P.safe`).
- Limits: enemies standing on *one-way* slabs drop through while the player is below them (engine one-way rule) — use
  `solid: True` for slabs that carry enemies. Crates can be pushed, not pulled: don't make a puzzle that needs pulling.

## Systems

Engine: `web/src/43_systems.js`. Map: `renderMap` in `web/src/08_ui.js`. Completion: Status tab in `web/src/08b_menus.js`.
Art: `art/gen_sys.py` → `assets/sys_door`, `sys_trial`, `sys_gaunt`, `sys_bench`, `sys_lore`, `sys_icons`, `sys_micons`.
Checker: `tools/reach.py` (called by `tools/rooms.py`). Live demo of every system: test rooms **T2** (+ partner **T2b**) in
`tools/regions/96_sys_test.py` (`__game.tp('T2', 9, 26)`).

**Names in this section are frozen.** New fields may be added; nothing here will be renamed.

### Conventions
- Every system object is a spawn `dict(t='sys', kind='<kind>', x=…, y=…, …)`. `x, y` = the **empty cell the object stands
  in** (its floor is row `y+1`), like enemies and KM's standing props. The reach checker and the validator check that
  doors, sigils, goals, benches, lore props and gauntlet markers stand on ground.
- `id` is local to the room. Anything that remembers "done" uses `SAVE.flags['x3:<room>:<id>']` or `SAVE.x3.*` (below).
- `skin: 'stone'|'wood'|'metal'|'crystal'|'neon'` on doors, sigils, goals and benches. Default by biome:
  ramparts/catacombs/cathedral/crown/spire/barrows/necropolis/dunes → stone · mire/archives/hermit/thornveil/crimson/
  lastfield → wood · deep/ember → metal · hoarfrost/starfall → crystal · neohallow → neon.
- Everything works with keyboard, controller and touch: objects are used with **interact** (E / pad Y / touch "Use"),
  and show the usual HUD prompt when you stand at them.

### `door` — a pair of doors joining two rooms that don't touch
```python
dict(t='sys', kind='door', x=12, y=10, id='d1', to='XX7', toId='d1', look='arch')         # in room XX3
dict(t='sys', kind='door', x=3,  y=20, id='d1', to='XX3', toId='d1', look='arch')         # in room XX7 (the partner)
```
| field | default | |
|---|---|---|
| `id` | — (required) | local id; the partner points back with `toId` |
| `to`, `toId` | — (required); `toId` defaults to `id` | the partner room and door id. **Validated both ways**: every door's partner must exist and point back (ERR otherwise) |
| `look` | `'arch'` | `arch` (stone/wood/… archway) · `crack` (a fissure in rock) · `hatch` (trapdoor in the floor) · `ladder` (rises into the dark) · `portal` (a swirling ring; `skin:'neon'` glitches like the NEO-HALLOW crack) |
| `auto` | `False` | `True`: passes on touch (walk into it) instead of on interact. Put auto doors at dead ends — walking past one takes it |
| `face` | into the room (`x < w/2` → right) | the direction the player faces on arrival |
| `skin` | biome | |

The player steps into the door (0.25 s), the screen fades, and they arrive standing on the partner's cell, facing `face`.
Arrival never lands in a wall: if the partner cell isn't standable at runtime the nearest standable cell within 6 is used
(the validator already rejects doors that don't stand on ground). An auto door doesn't fire again until you step away from
it. The map draws each door and a dotted line to its partner once both rooms are explored. A door is also an exit and an
entrance for the reachability check. Using a door during a trial ends the trial.

### `passage` — a hidden opening that is solid until a condition holds (checked on room entry)
```python
# The Last Field: the wall where Cindervane fell splits after you rest, or 5 minutes after the kill
dict(t='sys', kind='passage', x=46, y=14, w=1, h=3, id='lastfield',
     cond={'flag': 'boss:cindervane', 'restAfter': True, 'minTime': 300}, drift='seed')
```
| field | default | |
|---|---|---|
| `x, y` | — | the **bottom-left** cell of the opening; it covers columns `x … x+w-1`, rows `y-h+1 … y` |
| `w`, `h` | `1`, `3` | size in tiles. **Leave these cells open (`.`) in the map**; the engine fills them with the room's own wall tiles while closed, so validation, leaks and reachability see the open shape |
| `cond` | always open | `{'flag': f}` open once `SAVE.flags[f]` is set · `+ 'restAfter': True` and only after a shrine rest *after* the flag was first set · `+ 'minTime': s` or once `s` seconds of play have passed since. With both `restAfter` and `minTime`: whichever comes first. Also `'item': id` (needs `SAVE.items[id]`). A bare string means `{'flag': string}` |
| `drift` | `'ember'` | what blows through once open: `'seed'` (seeds + wheat), `'ember'`, `'ash'`, `'petal'`, … (any particle kind) |
| `wind` | away from the nearer wall | `1` / `-1`: which way the draught blows |
| `light` | `'255,214,150'` | colour of the soft light in the opening |
| `hint` | `True` | while the flag is set but the time isn't right, a hairline crack with a thread of light shows in the rock |

The state is evaluated only when a room is entered, so it never pops open in front of you. The first entry after it
opens plays the reveal (crack, rubble, chime); after that it is simply open, with light and drift. It appears on the map
only after you've walked through it. Flag times: `SAVE.x3.t[flag]` (play time when first seen set), last rest:
`SAVE.x3.restAt`. JS: `sysCond(cond)` evaluates any cond object.

### `trial` + `trial_goal` — optional timed parkour
```python
dict(t='sys', kind='trial', x=4, y=30, id='tr', par=45, reward='c_x3_storm', region='Stormward Spire'),
dict(t='sys', kind='trial_goal', x=58, y=6, trial='tr'),
```
| field | default | |
|---|---|---|
| `id` | — (required) | |
| `par` | `60` | seconds. Set it ~25% above your own clear time (EXPANSION3 §7.3) |
| `reward` | none | an item id granted once, on the **first** clear (charm, `emberstone`, `shard`, `seed`, `gold`, `sp:…`) |
| `bonus` | `300` | cinders granted the first time you beat par |
| `name` | `'Trial of the <region>'` | shown on the HUD; `region` feeds the default name |
| `needs` | the room's `needs` | abilities the trial requires; without them the sigil stays sealed (prompt "Sealed", a toast names what's missing) |
| `skin` | biome | |
| `trial_goal.trial` | — (required) | the sigil's `id`. The goal is a pedestal with a reliquary: it opens on the first clear and shows a gold mark once par is beaten |

Interact with the sigil: stamina and FP refill, air-attack/smash counters reset, kit objects reset (`kitReset`), and the
clock starts when you step off the sigil. **Any** blow or hazard (enemy hits, projectiles, spikes, lava, KM `pendulum`/
`rising`, falling out of the room, any direct HP loss) sends you back to the sigil instantly with no HP lost and no death;
the kit objects and any foes killed in the attempt reset too. Parries, shield blocks and i-frames still work as usual.
Touch the goal to stop the clock. Leaving the room or taking a door ends the trial. Interact with the sigil mid-run to
restart. Retryable forever; the reward can't be taken twice. Records: `SAVE.x3.trials['<room>:<id>'] =
{best, clears, gold, got}`. The map shows the sigil (gold once under par) and the best time. Region hazards that hurt the
player must go through `hurtPlayer` (or be direct HP loss): both are caught.

### `gauntlet` — an opt-in arena behind a challenge marker
```python
dict(t='kit', kind='gate', x=10, y=10, id='gL', open=True),     # KM gates, one per way out, reaching the ceiling
dict(t='kit', kind='gate', x=37, y=10, id='gR', open=True),
dict(t='sys', kind='gauntlet', x=24, y=10, id='g1', look='banner', name='The Muster Yard', gates=['gL', 'gR'],
     waves=[[dict(type='hollow_soldier', x=14, y=10), dict(type='hollow_soldier', x=33, y=10)],
            [dict(type='hollow_archer', x=16, y=10), dict(type='shield_warden', x=30, y=10)],
            [dict(type='grave_knight', x=24, y=10)]],
     reward=['emberstone', 'shard']),
```
| field | default | |
|---|---|---|
| `id` | — (required) | |
| `look` | `'banner'` | `banner bell stake whistle horn idol stones drum rack terminal` — each has its own call (sound) and a lit state |
| `gates` | `[]` | ids of KM `gate`s. They are forced **open** on room entry and whenever the fight isn't running (`kitForce(id, true)`), closed while it runs. Give them `open=True` so they don't animate on entry |
| `waves` | — (required) | list of waves; each a list of `{type, x, y}` (enemy type from `ENEMY` / `ENEMY_CLASSES`, tile coords of the cell it stands in; flying types may float). 3 waves + an elite (§7.3) |
| `reward` | `[]` | item ids granted once, on the first clear (numbers = cinders) |
| `replay` | `300 + 120 × waves` | cinders for each later clear |
| `name` | `'The Gauntlet'` | shown on the opening banner |

Interact to start: gates slam, "WAVE 1" banner, foes rise out of ash at their spots, a wave counter sits at the top of the
HUD. Clearing the last wave opens the gates, grants the reward on the first clear, and lights the marker for good
(`SAVE.flags['x3:<room>:<id>'] = 1`; clears counted in `SAVE.x3.gaunt`). Dying or leaving resets it. A gauntlet must
never be on the only route (its gates stand open unless you ask for the fight).

### `bench` — a vista bench
```python
dict(t='sys', kind='bench', x=20, y=18, id='bench', view=[48, 10], lore='rc_3')
```
| field | default | |
|---|---|---|
| `id` | `'bench'` | |
| `view` | room centre | tile coords the camera settles on while seated |
| `zoom` | fit the room | view scale 0.4–1 (1 = no zoom, just the pan). Default: as wide as the room allows, down to 0.55; the view never shows past the room's walls |
| `lore` | none | a `LORE_PAGES` id shown in a text box while seated (and added to the Chronicle) |
| `face` | toward `view` | |
| `skin` | biome | |

Sit (interact): the rest pose, the camera eases out over 1.5 s (zoom + pan, letterbox bars, crossfade), the music drops
to its ambient layer (no bells). Any input stands you up (Esc/Map still open their screens). The first sit logs
`SAVE.x3.vistas['x3:<room>:<id>']` and the map shows the bench from then on. Seated you can't be hurt. It is not a shrine
(no healing, no respawn). Rooms with `vista=True` play ambient-only music as long as you're in them.

### `lore` — a page of the Hallow Chronicle
```python
dict(t='sys', kind='lore', x=30, y=10, page='rb_2', look='stone')
```
`look`: `stone` (standing stone) · `corpse` (a fallen knight holding a page) · `book` (lectern) · `tablet` · `scroll` ·
`none` (invisible; use your own prop). `face` flips it. Interact ("Read" / "Search") opens the page reader; the first
read adds the page to the **Hallow Chronicle** (Inventory › Hallow Chronicle, grouped by region, Enter re-reads).
Unread pages glow. Pages live in a registry you fill from your region's JS file:
```js
Object.assign(LORE_PAGES, {
  rb_2: { region: 'archives', title: 'The Last Catalogue', text: 'First paragraph.\nSecond paragraph.' },
});
```
`region` = the biome id (it groups the page and counts toward that region's completion). `text` wraps automatically;
`\n` starts a paragraph; long pages page with ←/→. Ids `<agent>_<n>`. Found pages: `SAVE.x3.lore[id]`.

### Room kwargs read by the systems
```python
Room('SP9', 'Gale Stair', 'spire', gx, gy, 24, 40, indoor=True, needs=['talon', 'gale'], x3=True, parkour=True)
```
| kwarg | read by |
|---|---|
| `needs=[…]` | **reachability** (exactly these abilities: `talon wings hook emberdash gale slam tidebreath moonstep`; `['start']` = none) and the **map lock icon** (shown while you lack one). Default for sigils' `needs` |
| `x3=True` | marks an Expansion 3 room: reachability errors are ERR (not WARN) even without `needs` |
| `puzzle=True` | map: puzzle icon |
| `secret=True` | map: secret icon; completion: secrets found; a "You discovered a secret" toast on first entry |
| `vista=True` | ambient-only music in the room |
| `trial=True` / `gauntlet=True` / `grand=True` / `parkour=True` | room type tags (kept for tools/completion; the trial/gauntlet icons come from the spawns themselves) |
| `test=True` | never on the map (unless you're in it), excluded from completion |
| `reach_open=[(x, y), …]` | reachability treats these cells as open (a wall your region's own mechanic breaks, an ink stair that appears…) |
| `reach_ignore=True` | reachability skips the room entirely (last resort; say why in a comment) |

### Completion (Status tab) and the map
Status tab: per region (discovered regions) and in total — rooms visited, trials cleared (✦ = under par), vistas found,
secrets found (`secret=True` rooms visited), gauntlets cleared, lore pages. Totals come from the room list, so they
update as rooms are added. JS: `sysCompletion()`.
Map (Tab / pad View / touch Map): opens centred on you at the middle zoom; ←↑↓→ / left stick / drag pan, Enter / pad A /
Space / mouse wheel cycle 3 zoom levels, Q / pad LB / E cycle a region filter. Icons: shrine, trial (gold under par),
gauntlet (lit when cleared), puzzle, vista (after found), secret, door + dotted link, passage (after walked through),
lock (unmet `needs`), great foes, you. Room shapes are drawn from the map itself.

### Placement helper (tools/rooms.py namespace)
```python
gx, gy = free_spot(-40, -120, 48, 14, 'Spire')            # zone by name (EXPANSION3 §7.2) or (x0, x1, y0, y1)
r = Room('SP9', 'Gale Stair', 'spire', gx, gy, 48, 14, …)
```
`free_spot(near_gx, near_gy, w, h, zone, margin=0)` returns the free top-left spot nearest to `(near_gx, near_gy)` inside
the zone that overlaps no room built so far (region modules run in file order, so later modules see earlier rooms) and
keeps clear of the test rooms, or `None`. Use it while laying out, then **hard-code the result** so the layout never
shifts when another agent adds a room. `python3 tools/rooms.py --zones` prints every zone's occupancy (1 char = 4×4 tiles)
and a free spot for a few common sizes.

### Validation and reachability (python3 tools/rooms.py; STRICT=1 fails on any ERR)
- `ERR <room>: door <id> → <to>:<toId> …` — partner missing, not pointing back, or door not standing on ground.
- `ERR <room>: sys <kind> …` — unknown kind, missing `id`/`waves`/`trial`, a goal without its sigil, a lore `page` id
  format, or a sigil/goal/bench/lore/marker not standing on ground.
- `ERR <room>: reach: …` — from `tools/reach.py`, for rooms with `needs` or `x3=True` (old rooms print the same as `WARN`):
  - `… item at (x,y) / chest / trial goal / door / lore … is unreachable with needs […]`
  - `… exit W edge rows 7-10 can't be reached from any entrance`
  - `… entering by N edge cols 8-11 there is no way out again` (a soft-lock)
  - `… entering by S edge cols 1-3, exit N edge cols 1-3 can't be reached` (rooms with `world_link=True` or
    `reach_both_ways=True`: every exit must be reachable from every entrance). Leaving through a top opening needs the
    player's feet above 13 px from the top edge (`checkRoomExit`), so the last ledge must sit ≤ 2–3 rows below it.
- The checker simulates the real physics frame by frame (numbers read from `04_player.js`): run 122 px/s, jump ≈ 57 px
  (3 tiles + a little; the ledge assist can pop you onto a 4th only with perfect timing — don't design for it), running
  jump ≈ 7 tiles across, base air dash +4.4 tiles, wall jumps, double jump (`wings`), Moonstep, Gale glide + updrafts,
  Root Hook swings (`@`, range 130 px), deep water `"` (swim anywhere with `tidebreath`, otherwise float/paddle on the surface
  and leap out at 300 px/s), starlight `+` (40% less gravity), open sky above outdoor rooms, entering up through a floor
  opening at 260–272 px/s with jump held and the air jump unspent (300 with `talon`), **pogo off spikes** (a spike floor can be crossed by pogoing: use lava `*`,
  bottomless drops or `rising` floors for hard barriers), drop-through `=`. KM movers/lifts count as their swept path,
  crumble/sinker/phase/spring/crate as ledges where they start, swings as grab points; gates count as open.
- Results are cached per room in `tools/.reach_cache.json` (only changed rooms re-run; uncached rooms run in parallel,
  ~1–4 s each). `NOREACH=1` skips the check for a quick build. Debug one room:
  `python3 tools/reach.py SP9 --show` (ASCII: `S` standing cells reached, `!` standing cells missed, `*` air visited),
  `--needs=talon,wings` to try other abilities. `python3 tools/reach.py --selftest` runs the known-answer layouts.

### JS API (region code)
`LORE_PAGES` (registry) · `sysCond(cond)` · `sysFlagTime(flag)` · `sysCompletion()` · `SYS.trial` (running trial or null:
check it before spawning trouble) · `SYS.vista` (seated) · `sysGate(id, open)` · `sysLater(sec, fn)` (game-time delay).

## Reserved tile chars (lead)
- `'9'` (tile id 81): RB's ink abyss (Archives), a hazard for reachability. Don't reuse it.
