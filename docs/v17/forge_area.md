# v17 Cold Forge: area notes (AREA agent) — read this, BOSS and FOES

Status: **layout fixed** (coordinates below won't move). Room file `tools/regions/86_forge.py`, engine `web/src/82_forge.js`.

## The boss arena (AREA → BOSS)

| | |
|---|---|
| room id | **`CF8`** "The Hearth Below", biome `forge` |
| world position | gx 805, gy 66, **58 × 21 tiles** (928 × 336 px) |
| floor | top of local row **18** → feet at **y = 288 px** (standing row 17). Rows 18–20 solid. Flat from x 1 to x 50 (49 tiles, no steps, no pits) in front of the furnace |
| roof | rows 0–1 solid; open air rows 2–17 (16 rows = 256 px) |
| entry | west wall open rows 14–17 (from CF7 The Anvil Court). Fog wall `F` at (1, 17) (`boss='hearthkeeper'`, `entry='W'`) |
| spawn | `{t:'boss', kind:'hearthkeeper', x:40, y:17}` → BOSS_SPAWN.hearthkeeper(cx = 648, fy = 288, spec) |
| the Great Furnace | drawn by AREA at the east end (sprite `cfa_furnace`, centre x 800 px): a riveted beehive whose chimney runs up through the roof. It stands on the far (back) wall: you can walk in front of its face. Its right half (local x 51–57, rows 2–11) is solid terrain (tile `0`, invisible: the sprite draws it), so **the arena's east wall is x = 816 px** from roof to floor. The arched **mouth** (x 768–832 px, y 192–288, drawn) holds the **doors**; while shut, cells x 51–57, rows 12–17 are solid at runtime (the way on runs east through the furnace's throat to the room's edge at x 928) (the map has them open so validation sees the way to the Threshold) |
| fight bounds | clamp the boss to **x 40 … 808 px** (your L 64 / R 794 is fine): west = inside the fog wall (x 32 px), east = the solid flank / shut doors at x 816 px. 49 tiles of flat floor |
| coal bed | a low bed of coals in front of the furnace: local x **38–47** (px 608–768), on the floor (feet line y 288). Drawn and lit by AREA (`cfArena.coals` = {x0: 608, x1: 768, y: 288}); it's **decor only** (no damage) unless BOSS wants it to bite in P3 — then read `cfArena.coals` and hurt from your own file |
| bellows | two great bellows hang on chains at local x ≈ 9 and x ≈ 31 (centre px 152 and 504, nozzle tips at y ≈ 150). Decor; `cfArena.bellows` = [{x, y}] for a P3 bellows blast source if you want it |
| darkness | P3 "the arena goes dark except the hearth": set `cfArena.dark = 0..1` from your file each frame (AREA lowers the ambient light and the bellows/backdrop glow by it; the coals stay lit). Reset to 0 on death/exit (AREA also resets it on room entry) |
| hooks AREA provides | `cfFurnaceOpen()` (call after the core is obtained and `SAVE.flags['w2:open'] = 1`); `cfArena` (object above; also `cfArena.mouth` = the doors' rect in px); `cfArenaDark(k)` = sets `cfArena.dark`. Note: AREA's other top-level names are prefixed `cfa`/`CFA` (FOES owns `cf`/`CF`) |

`cfFurnaceOpen()` is safe to call any time: it plays the cutscene (the coals and the furnace seam go out, the bar
lifts, the doors grind open, cold air) only if the player is in CF8, otherwise it just records the state; on the next
entry into CF8 the doors are already open. Rekindle/rematch never re-closes them (they only look at `w2:open`).

## Enemy rooms (AREA places FOES' enemies from `docs/v17/forge_foes.md`)

The room file emits `t:'enemy'` spawns once `web/src/83_forge_foes.js` defines a type (until then a `t:'cf_foe'` stand-in).
Placements as built (room: types):
CF1 The Ash Pit: cf_mite ×3 · CF2 The Long Flue: cf_mite ×3, cf_smith · CF3 The Flue: cf_mite ×4 (on ledges) ·
CF4 Hall of Racks: cf_smith ×2, cf_mite ×2 · CF9 The Reject Pile: **cf_unforged** (mini-arena 1, 36 tiles of floor) ·
CF5 Quench Cisterns: cf_wraith ×3 (on the piers), cf_smith · CF6 Bellows Gallery: cf_hulk, cf_wraith, cf_mite ×3,
cf_smith · CF13 The Tempering Vault: **cf_unforged** (mini-arena 2, 38 tiles) · CF12 The Slag Chute: cf_hulk (lower floor,
guarding the way down to the Anvil Court), cf_wraith, cf_mite · CF11 The Ledger Room: cf_smith · CF7 Anvil Court, CF8,
CF10, CT1, CT2: none. Both Unforged arenas seal behind you (iron bars, `cfa` seal) until it falls.

## Route

E6 The Last Hearth (slam the grate beside the hearth) → CF1 The Ash Pit → CF2 The Long Flue → CF3 The Flue (the
descent) → CF4 Hall of Racks → CF5 The Quench Cisterns → CF6 The Bellows Gallery → CF7 The Anvil Court (shrine) →
CF8 The Hearth Below (boss) → furnace doors → CT1 The Ashen Threshold (shrine) → CT2 The Last Gate (vista, the
shut gate; World 2 hook `CT_GATE`).

## Design as built (AREA)

- **Entrance:** E6's hearth floor runs on over a 4-cell soot grate (`Y`, flush with the hearth, x 28–31 row 15; E6's
  `needs` became `talon, slam`, which it already required through the Expanse). Cold air rises through it with a hint
  toast; Cinder Slam breaks it and the pit opens east into CF1. E5 sits right under the hearth, so the flue first runs
  east (Ash Pit, Long Flue over the Trial room) and only then drops (CF3) into the forge under the Expanse.
- **Anvils** (`t:'cfa', kind:'anvil'`): a heavy, finisher, plunge or slam rings one (pale arcs, a cold flash, an
  inharmonic ring); its keyed kit gates (forge shutters) lift for 6–8 s with a ticking countdown bar, then fall. Light
  blows clank (one hint toast). Each shutter has the sign of its anvil on the lintel (hammer, tongs, flame, ox); every
  shutter on the main route has a small return anvil on its far side. CF4: the intro shutter (A) and the Reject Pile's
  (B, wedged open for good once the Unforged there falls). CF6: two shutters whose anvils sit on the catwalk and on a
  high ledge reached by an ingot stair. CF11: three practice anvils rung in the ledger's order (ox, flame, hammer)
  open the reliquary (3 wrong tries → hint).
- **Hearth vents** (CF6): floor grates whose flare runs across the strip as a wave every 3.2 s (warm glow + hiss 0.5 s
  before, 24 dmg × NG+); the bellows above breathe on the same clock and their exhale gusts push the player west along
  the gallery (not on the high anvil ledge).
- **Unforged arenas:** CF9 and CF13 seal with iron bars once you're inside while it lives; they lift when it falls.
- **Still water:** the Barrows' deep water (`"`), re-rendered black and still with a faint sheen and drip ripples.
- **The furnace:** see the arena table. `cfFurnaceOpen()`: pan, the coals and the seam die (2.2 s), the bar lifts, the
  doors grind open (2.6 s), cold air, a subtitle; door cells opened. Entering CF8 with `w2:open` set: already open.
- **The Threshold:** CT1 (shrine, a dark hall with a broken arch onto the ash-light, the open furnace leaf), CT2
  (vista bench, the causeway, the gate with the keeper's grate-crown sigil, two veiled guardians). Touching the gate
  gives one of three lines. `CT_GATE` + `cfWorld2Link()` in 82_forge.js are the World 2 hook.
- **E6 after:** with `w2:open` the Last Hearth's fire is banked to embers (small red light, one toast).
- **NPCs:** Venn (a beat after first seeing the forge; a VENN_BEATS entry after the keeper), Ashwright (a beat on
  first sight, one after the keeper, and an "Ask about the Cold Forge" choice) — all from 82_forge.js (npcScript wrap).
- **Biomes:** `forge` (The Cold Forge, ambient 0.5, cold blue LX, desaturated grade, tier like the Ember) and
  `threshold` (The Ashen Threshold, pale). Music: the generic drone + a slow cold figure with a far anvil on the bar;
  the threshold's open fifths (ambient only on the vista).

## Tests (AREA) — `SHOT_HTML=$PWD/web/dist/v17_area.html node tools/shots/shot.js tools/shots/v17/area/<t>.js <out>`
- `walk.js` — every edge crossed both ways by input (67 checks, 0 fails), incl. the grate, chimneys, the descent and
  the climb back up the Flue, anvils (light vs heavy), shutters timing out, seal, lever gate, ledger, furnace shut
  until `w2:open` then open after `cfFurnaceOpen()`, and staying open on re-entry.
- `checks.js` — random-input stress with live foes in all 15 rooms (0 exceptions), phantom damage at 43 spots (none),
  NPC lines, lore pages, the vista bench, the map. `look.js` / `look3.js` — snapshots (montages in tools/shots/v17/area/).
- `STRICT=1 python3 tools/rooms.py` — 0 errors (reach: every forge room "everything reachable").

## Lead review pass: room-themed parallax
`art/gen_forge_bg.py` → `cfa_bg_<theme>` (far + mid, 512×216): **flue** (CF1–CF3: soot chimneys receding, iron bands, a
warm flue glow far up, pipes and buckets), **racks** (CF4/CF9/CF13: arched bays of blades under grey vent shafts, great
racks mid-ground; also the generic `bg_forge_*`), **cistern** (CF5/CF10: vaulted hall mirrored in still water, tanks,
a gantry), **bellows** (CF6: rows of hanging bellows, a walking beam, coal glints in far grates), **court**
(CF7/CF11/CF12: a round grate-window as the focal light, hammer racks, an arcade), **hearth** (CF8: huge courses,
pillars, embers rising). Values lifted a few steps; cool rims on mid silhouettes; warm accents only at fire. Also:
forge bg wall tiles one step lighter, the cistern water less opaque with the vent light mirrored in it, cold vent
lights added in CF1, CF2, CF5, CF6, CF9, CF12, CF13. `CFA_BG` in 82_forge.js maps rooms to themes.
