# Cinderhollow — Expansion Plan (v6+)

Current: 27 rooms / 5 regions / 6 bosses. Target: ~47 rooms / 8 regions / 11 boss encounters.

## Traversal techniques (each region's boss unlocks the next)
| Technique | Effect | Opens |
|---|---|---|
| Ember Dash | air dash phases through ash veils + enemies | Hoarfrost Aqueduct |
| Root Hook | grapple + swing from golden hook points | upper Archives, shortcuts in old regions |
| Cinder Slam | down-slam breaks cracked floors, AoE on landing | Burning Deep, old-region secrets |

## New regions
| Region | Attaches | Rooms | Hazards / feel | Enemies | Boss → reward |
|---|---|---|---|---|---|
| Ashen Archives | top of K3 Bell Ascent | ~6 | vertical library, hooks, falling shelves | animated tomes, ink hounds, lantern monks | The Unwritten (ink-wraith caster, bullet-hell patterns, rewrites arena) → Root Hook + Faith quill-staff |
| Hoarfrost Aqueduct | west of R1 via ash veil | ~7 | ice physics, freezing water, frost buildup | frost wraiths, ice golems, under-ice lurkers | Frostbound Twins (flame + frost duo; survivor enrages with both elements) → Ember Dash + twin blades (dual-wield moveset) |
| The Burning Deep | below the Mire via cracked floors | ~7 | lava, rising magma, conveyors | slag imps, forge sentries, magma crawlers | Molten Colossus (multi-part, break armour plates → weak points) → Cinder Slam + molten greathammer |

## Extra encounters
- Mini-bosses: Hollow Champion gauntlet (R4 arena waves), Gilded Sentinel pair (Crown).
- Secret superboss: The First Ember — a dark mirror using the player's movesets, arts and parry, switching weapons between phases. Needs all 3 techniques. Reward: unique charm + true epilogue.

## Boss cutscenes (in-engine, skippable with Esc, first encounter only)
Letterbox bars, camera pans to the boss, lines in the NPC dialogue style, signature moment, then the name card. Phase-2 transitions get a ~4 s mini-scene.
| Boss | Intro | Phase-2 moment |
|---|---|---|
| Gravetusk | asleep among roots → eyes open, rises, howl shakes dust down | roots ignite |
| Morvain | kneeling in the throne hall → stands, speaks, draws blade in a gold flare | crown of light blooms |
| Ser Kalden | kneeling at Iselle's grave, rot-swollen arm → speaks to you if you met him, then gives in | rot bursts through his armour |
| Pale Sovereign | descends from the sky, throne glowing, speaks to you and Venn | crown shatters, robes catch fire |
| The Unwritten | ink bleeds out of the Scribe's unfinished book and takes shape | the room's pages invert |
| Frostbound Twins | they duel each other, then turn on you together | one falls, the other absorbs its element |
| Molten Colossus | Ashwright's voice-over as it wakes in the forge | its armour sloughs off |
| The First Ember | your own shadow rises from your last remnant spot | it switches to your equipped weapon |
The Vessel (optional) keeps its quick intro.

## Combat techniques
Plunging attack (heavy in air), guard counter (attack after a non-stagger parry), backstep strike (roll back + attack), charged arts (hold O), weapon-type specials (dagger backstab crits, spear jump thrust, katana parry-counter, greatsword charging hyper-armour swing), spirit echoes (summon, e.g. Kalden's echo; once per rest).

## Build order (each step ends playable + published)
1. Engine groundwork: hook points, ash veils, cracked floors, ice, lava, the new techniques; the **cutscene system** plus the four existing bosses' scenes.
2. Ashen Archives + The Unwritten (+ cutscene).
3. Hoarfrost Aqueduct + the Twins (dual-boss system + cutscene).
4. Burning Deep + Molten Colossus (multi-part boss system + cutscene).
5. Mini-bosses, the First Ember, spirit echoes, combat techniques.
6. Map rework + full balance pass (Armory + scripted route through the game).

## Open decisions
- Order of regions (proposed: Archives first).
- Spirit echoes in or out (they make the game easier).
- Scope: all three regions, or two + the superboss.

## Decisions (2026-09-25)
- Region order (play + build): Ashen Archives → Hoarfrost Aqueduct → Tempest Spire → Burning Deep; secret: Hermit's Hollow (Oswin, any time), Ember's Hollow (First Ember, post-game).
- Unlock chain: wall-jump (Hound) → Archives; Root Hook (Unwritten) → Hoarfrost (hook gap past Rampart Summit); Ember Dash (Twins) → Tempest Spire (ash veil on the sea wall); Gale Cloak (Cindervane) → Burning Deep (glide the lava chasm); Cinder Slam (Colossus) → old-area secrets + First Ember.
- Twin blades: kept (Hollow Champion's Twinfangs).
- New weapon sets: Staff (fast, weaker than spear; instant heavy costing 80% stamina) and Sword & Shield (hold-to-block guard, shield parry, shield-bash heavy).
- Secret boss Oswin, the Ashen Pilgrim behind R1 (charged heavy breaks the seal) → Oswin's Windstaff + Pilgrim's Bead.
- Main-boss concepts in art/concepts/: Twins v1 approved; Unwritten v3, Cindervane v3 (from user reference painting), Colossus v3 polished — awaiting user check. Earlier versions kept as *_v1 / *_v2.
- 2026-09-25: user said "finish the whole game". Build started. Defaults taken: Oswin level-scaled, spirit echoes out, new regions optional. Concepts v3 used as approved. Build contract: docs/EXPANSION_CONTRACT.md.
