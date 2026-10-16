# v17 Cold Forge: build contract (three agents in parallel)

Read first: `docs/v17/AREA_PLAN.md` (the approved plan), `art/concepts/forge/CONCEPTS.md` and the concept PNGs in
`art/concepts/forge/` (approved direction), `docs/EXPANSION2_CONTRACT.md` §0 and `docs/EXPANSION3_CONTRACT.md` §7–8
(how areas, bosses and enemies are added; arena-clamp lessons). Branch: `forge`. **Do not commit, push or publish**;
the lead integrates and commits. Never write `web/dist/index.html`; test builds go to `web/dist/v17_<you>.html`.

Owner decisions (2026-10-16):
- Boss head = **A (veiled, grate-bar crown) with B's flue cowl** (the tall soot cowl rising like a chimney, the grate
  crown ringing it). **Slim beaked hammer.**
- The elite (the Unforged) art must be **redone** — the concept read as a stick figure.
- The boss must have **as many attack moves as the other top bosses** (Vael / the Warden ~20, Venn 34 entries):
  target **22–26 distinct attacks** across 3 phases.
- Owner taste (strict): dark mythology, sleek and smooth, never chubby, blocky or cartoonish; slender or heroic
  silhouettes, small menacing heads, smooth curves, restrained glow, dark palettes. Quality bar: Morvain, Kalden,
  the Vessel, the Pale Sovereign, the Frostbound Twins, Sister Venn. Animation quality matters more than effects:
  arms must not be thin straight sticks (the concept's weakness) — real forearms, hands, cloth that follows.
- Effects restrained: one main light per effect, k ≤ 0.8, no screen-filling white; cap a target's white hit flash
  where many hits land in a row.

## Ids and ownership

| thing | id | owner |
|---|---|---|
| biome | `forge` (Cold Forge); AREAS name "The Cold Forge" | AREA |
| rooms | `CF1`… (forge), `CT1`… (Ashen Threshold) | AREA |
| region file | `tools/regions/86_forge.py` (anchor: patch `ROOM('E6')` for the entrance) | AREA |
| area code | `web/src/82_forge.js` (biome setup, AREAS, lighting/grade table entries, music, anvils, vents, furnace doors, threshold, gate, map, region card, E6 fire burning low after) | AREA |
| enemies | `web/src/83_forge_foes.js`: `cf_smith`, `cf_wraith`, `cf_hulk`, `cf_mite`, elite `cf_unforged` | FOES |
| boss | `web/src/84_hearthkeeper.js`, kind `hearthkeeper`, BOSS_INFO name "The Hearthkeeper" | BOSS |
| boss art | `art/gen_hearthkeeper.py` (+ rig module), sheet `hearthkeeper` | BOSS |
| enemy art | `art/gen_forge_foes.py`, sheets `cf_*` | FOES |
| area art | `art/gen_forge_env.py` → `tiles_forge`, `bg_forge_far`, `bg_forge_mid` (+ threshold backdrop) | AREA |

Shared tables: add entries **from your own file** with `Object.assign(...)`/push where the engine allows it (ENEMY,
ENEMY_CLASSES, ATTACK_TAGS, BIOME_TIER, BOSS_INFO, BOSS_SPAWN, BOSS_CUTS, PHASE2_LINES, CORES, GFX tables,
LX tables, SCALES/ROOTS, LORE_PAGES, NPC lines). If a table can only be extended by editing its home file, make one
minimal surgical edit and re-read the file right before editing (others edit the tree at the same time).
`tools/rooms.py` regenerates `web/src/02_rooms.js`: **only AREA runs it.**

## Hand-offs

- **Boss arena (AREA → BOSS):** room `CF_BOSS` id of AREA's choice (tell BOSS in your file header and in
  `docs/v17/forge_area.md`), a spawn `{t:'boss', kind:'hearthkeeper'}`, a flat floor at least 34 tiles wide with the
  sealed **Great Furnace** on the far wall (its doors are AREA's, drawn in the backdrop/props) and a coal bed. BOSS may
  ask for arena changes through the lead.
- **The core and World 2 (BOSS → AREA):** the Hearthkeeper drops the **Hearthkeeper's Core** (`CORES.hearthkeeper`,
  balanced with the other 32, see 77_cores.js and docs/BOSS_CORES.md). When the player **obtains the core** (not on
  the kill), BOSS sets `SAVE.flags['w2:open'] = 1` and calls `cfFurnaceOpen()` if it exists (AREA defines it: the
  furnace cools, the doors unbar with a slow grind, a short cutscene, the way through to the Threshold opens). AREA
  must also open it on room entry when the flag is already set. Rekindle rematches never re-close it.
- **Spawns (FOES → AREA):** FOES lists the enemy ids, sizes and intended rooms in `docs/v17/forge_foes.md` early;
  AREA places them. The Unforged gets 1–2 placements (a mini-arena each), rolling one of the 14 weapon types per
  encounter.
- **World 2 gate:** the Ashen Threshold ends at a great shut gate (World 2 isn't built). Interacting shows a line that
  hints at what's beyond; leave a clear hook (`CT_GATE` room id + a commented function) for linking World 2 later.

## Mechanics (from the plan; refine, keep the identity)

- **Anvils** (AREA): strike with a heavy or a finisher (`heavy` kind hit or a move flagged as a finisher) → its ring
  opens the iron shutters keyed to it for a few seconds. **Hearth vents** flare across floors on a beat.
- **Tempering** (BOSS): if his stance isn't broken within a window, he re-tempers his weapon (stronger, glowing); a
  stance break / fatality resets it. He must be critable (fatalities work: `critRange`, `onCritStart`; see
  79_fatality.js) and joins Rekindle (`crHomes`/training scan), BOSS_CURVE (59_difficulty.js), BOSS_STAGE
  (69_adaptive.js), NG+ (`NGP`).
- **Phases** (BOSS): P1 The Smith (hammer + tongs, grab), P2 The Arsenal (glowing blade / spear / chain from the
  coals, each a short pattern, then dropped hissing), P3 The Last Fire (arena darkens except the hearth; flame tongs,
  ember rain, bellows blast). Light is the danger and the cue in P3.

## Tests (each agent)

Harness: `SHOT_HTML=$PWD/web/dist/v17_<you>.html sh tools/shots/wm/run.sh <test.js> <out>` (helpers in
tools/shots/wm/_prelude.js); tests in `tools/shots/v17/<you>/`. Show: no page errors; reachability (AREA: walk the
route with `tools/reach.py` and a bot pass; furnace opens only after the core); FOES: each foe spawns, attacks, can
be killed, the hulk can be staggered into a fatality; BOSS: every move fires, phases transition, tempering, fatality
on stagger, core → flag → doors, rematch, time-to-kill with 3+ weapon types in line with the other late bosses (see
how tools/shots/tr/bosses* and the v15 balance bench measured it). Snapshots/montages for the lead to review the look.

## Report

Files, design as built, numbers, tests and results, snapshot paths, open decisions.
