# v17 plan: a new area and boss — The Cold Forge / The Hearthkeeper (DRAFT, awaiting owner approval)

## Why here
Lore page sc_13 (room E6, "The Last Hearth", post-game ember region): "Someone keeps this fire ... No one has ever
seen them." E6 already has a floor grate hint. The new area lies under that grate: the forge where the Hallow's
weapons were made, and the boss is the one who keeps the fire. It ties the world to the weapon revamp.

## The area: The Cold Forge (~14 rooms, biome `forge`)
- Entrance: break E6's grate (slam) and drop through the flue. Optional, post-game-ish (ember region).
  Also reachable in NG+ (needs only talon + slam, slam is re-earned).
- Look: the fire is kept above; below, the forge is dead. Slate, black iron, soot, quench water gone still. The
  only warm light is the flue's shaft from above and the coals in the boss arena. Contrast with the ember biome.
- Route: flue descent (vertical) → Hall of Racks (thousands of unfinished blades) → Quench Cisterns (still black
  water, steam) → Bellows Gallery (the gimmick) → Anvil Court (shrine) → the Hearth Below (boss).
- Gimmick, weapon-centred: **anvils**. Strike an anvil with a heavy / finisher and its ring opens iron shutters for a
  few seconds (different shutters answer different anvils). Hearth vents flare across floors on a beat (timing).
- Enemies (4 + elite):
  - Hollow Smiths (hammer + tongs; the tongs grab and hold you over coals).
  - Quench Wraiths (steam that rises from cisterns; a hiss before they lunge).
  - Bellows Hulks (heavy poise; built to be staggered — the fatality showcase).
  - Cinder Mites (small swarmers that cling and burn).
  - Elite **the Unforged**: a body of failed blades that fights with one of the 14 weapon types (rolled per room),
    so players meet movesets they don't use.
- Story: Ashwright (the smith) and Venn react to the forge and its keeper (also starts filling the old gap where
  NPCs never mention Expansion 2).

## The boss: The Hearthkeeper (3 phases, Venn/SAINT-0 quality bar, ~22–26 moves)
- Look: tall and gaunt, veiled in soot, a smith's leather apron over old ritual plate, a ring of tongs and keys at
  the belt. Sleek silhouette, never bulky. A concept sheet comes to you for approval before any rig work.
- P1 "The Smith": a forge hammer and tongs. Heavy, readable, punishes greed; tongs grab.
- P2 "The Arsenal": pulls weapons glowing from the coals — a blade, a spear, a chain — and throws or swings each
  for a short pattern, then discards it. Each one telegraphs like its player type.
- P3 "The Last Fire": the arena goes dark except the hearth; he takes up the fire itself (flame tongs, ember
  rain, a sweeping bellows blast). Light is the danger and the cue.
- Rule: **Tempering** — if you don't break his stance within a window, he re-tempers his weapon (stronger,
  glowing). Stagger and fatalities are how you keep him down; the fight is built around the weapon systems.
- Joins Rekindle rematches, adaptive scaling, the difficulty curve, NG+.
- Drops the **Hearthkeeper's Core** (enchant at the blacksmith, balanced with the other 32).

## The entrance to World 2 (owner request: opens after you obtain the core)
- Behind the boss arena stands the Great Furnace, the thing the keeper guarded. Its mouth is sealed by heat.
- When you take the Hearthkeeper's Core, the keeper's fire goes out: the furnace cools to black, its iron doors
  unbar with a slow grind (a short cutscene; save flag `w2:open`, set on taking the core, so a player who leaves the
  core unclaimed doesn't open it).
- Through the doors: **The Ashen Threshold** (1–2 rooms, a shrine for fast travel) ending at a great gate and a vista
  over World 2. The gate is the hand-off point: World 2's first room links here when it's built. Until then the gate
  stays shut with a line that hints at what's beyond.
- Upstairs, the Last Hearth's fire in E6 burns low from then on (the promise is broken) — a small, felt change.
- What World 2 is (setting, scale) is its own plan, decided with the owner.

## Build order (each step shown to you before the next big one)
1. Boss concept sheet + area mood frames (incl. the Great Furnace doors) → owner approval.
2. Rooms (tools/regions/), biome art (tiles, parallax), lighting, music.
3. Enemies (4 + elite).
4. Boss rig + moves + phases; core; rematch; balance runs with several weapon types.
5. The World 2 entrance (furnace doors, Ashen Threshold, gate).
6. Story lines, map, region card, docs, tests, demo video of the fight.
Local branch only until you say push.
