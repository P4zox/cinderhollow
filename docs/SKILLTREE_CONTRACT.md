# Cinderhollow — Skill tree redesign contract

The current tree (`SKILLS` in `web/src/01_data.js`, drawn by the `tree` screen in `web/src/08_ui.js`) is too small.
It has 15 nodes in three straight lines of five, 27 points in total, and it's fully bought by mid-game because points
come from every level plus 42 Memory Shards. This redesign makes it a build-defining system. Read
`docs/EXPANSION_CONTRACT.md` §0 and `docs/EXPANSION3_CONTRACT.md` §0 for the general rules: per-agent builds,
per-agent test folders, no git, code style, and the art pipeline.

## Design (binding)
- **Five branches**, each a small web of about 12 nodes: trunk nodes, at least two **forks** (pick one of two;
  the other locks while the first is learned), and one **keystone** capstone that changes how you play.
  - **Blade**: combos, heavies, crits. Keystone *Relentless*: each hit in an unbroken combo deals +5% more,
    stacking to +25%; the stack is lost if you get hit or stop attacking for 1.2 s.
  - **Ash**: sorcery and incantations, FP. Keystone *Spellblade*: melee hits shave 0.4 s off every spell
    cooldown.
  - **Veil**: rolls, parries, stamina, defence. Keystone *Shadowstep*: rolling through an attack at the last
    moment puts you behind the attacker.
  - **Blood**: bleed, lifesteal, low-HP risk. Keystone *Crimson Pact*: bleed procs heal 6% max HP, but you
    carry one fewer crimson flask.
  - **Flame**: weapon arts, buffs, cooldowns. Keystone *Kindled*: arts leave a short fire trail, and all art
    cooldowns are 20% shorter.
- **Arsenal page**: one mastery node per weapon class (sword, dagger, great, spear, katana, staff, shield, twin,
  scythe, whip; mirror uses the class it copies). Each is active only while that class is equipped, cost 2, and
  has an effect particular to that class (for example Whip: the tip crack also staggers small foes; Scythe:
  reaping heals more).
- **Wayfarer ring**: about 8 utility nodes.
  - Technique upgrades: longer Root Hook, faster glide, a second Ember Dash charge in the air, a Cinder Slam
    shockwave.
  - Exploration perks: breakable walls glint when near; +10% cinders.
  - None of them may make the air-attack limit or smash limit more generous. Those limits are deliberate.
- **Keep** the existing node ids whose effects survive (`keen_edge`, `fourth_strike`, `charged_arts`,
  `riposte_mastery`, `bloodthirst`, `azure_thrift`, `soul_siphon`, `quickstep`, `iron_flask`, `steadfast`,
  `last_stand`, `second_wind`). The code already checks them with `has(id)`.
- **Spells leave the tree.** `ash_bolt`, `sunspear` and `emberburst` stop being skill nodes. Make them
  obtainable instead:
  - Ash Bolt is known from the start.
  - Sunspear and Emberburst are sold by the Scribe (or the region merchant where the Scribe has no shop), at
    prices around the early-game shop.
  - Players who already learned them keep them in `spellsOwned`.
- **Point economy**: `skillPoints()` = `floor((level − 1) / 2)` + Memory Shards − spent.
  - Tune node costs (1–4, keystones 4) so that a full, normal run gives about 60–70% of the tree's total cost.
  - Report the tree's total cost and the expected points at the end of a normal run.
  - New Game+ keeps skills and shards, as it does today.
- **Respec**:
  - The Pale Tear keeps working.
  - Add one free respec per journey at the Ashwright (`SAVE.freeRespec`).
- **Migration**: on first load, if `SAVE.skillv < 2`:
  - keep learned ids that still exist and drop the rest;
  - refund the points;
  - add the three spells to `spellsOwned` if their old skills were learned;
  - show a toast: "The skill tree has changed: your points are refunded."
  - set `skillv = 2`.

## Data format (the UI agent builds only from this)
In a new `web/src/57_skills.js`, replace the contents of `SKILLS` in place (`SKILLS.length = 0; SKILLS.push(...)`), so
every existing reference keeps working. Each node looks like this:
```js
{ id, br: 'blade'|'ash'|'veil'|'blood'|'flame'|'arsenal'|'way', name, desc, cost,
  x, y,              // layout position in tree units (the UI scales them): branches radiate from a centre, arsenal and
                     // wayfarer sit on their own pages or rings
  req: [ids],        // all required
  excl: [ids],       // fork partners: can't be learned together
  key: true?,        // keystone
  cls: 'whip'?,      // arsenal node: only active with this weapon class equipped
  icon: 'sk_<id>',   // icon name (the UI agent draws the icons)
  stat: fn?  }       // optional: returns the "before → after" numbers shown in the UI
```
`SKILL_BRANCHES = [{ id, name, color, desc }]`. `skillLearnable(id)` returns `{ ok, why }`. `learnSkill(id)` and
`skillBuildSummary()` return a list of readable totals for the summary panel.

## Ownership
| Agent | Job | Files |
|---|---|---|
| **SK** | Node design, every effect, point economy, spells out of the tree, respec, migration, balance of nodes | new `web/src/57_skills.js`; `skillPoints()` and the Rebirth code in `web/src/08_ui.js`; small `has()` hook points in other files where an effect needs them (list them under SHARED EDITS); `tools/shots/sk/` |
| **ST** | The new tree screen and ~75 icons | new `web/src/58_skilltree_ui.js`, which overrides the `tree` screen's input and render; new `art/gen_skills.py` (asset prefix `sk_`, one or two icon sheets registered in `ICON_SHEETS`); `tools/shots/st/` |

ST works from SK's data. Until SK's file exists, prototype against a copy of the old 15 nodes laid out in the new
format, then switch.

## Quality bar
- **Effects:** every node has a real, visible effect that is tested headless (a before/after number, or a
  behaviour check). No node is only flavour.
- **Keystones** must feel like new play, not +X%.
- **Balance:** no single branch or keystone combination may beat the others by more than about 15% boss DPS or
  survivability. Use `tools/shots/dps_bench.js` as the base.
- **The screen:**
  - a pannable constellation on a dark parchment field, with the game's gold UI style;
  - lines drawn between requirements, with fork pairs clearly marked;
  - learned / available / locked states;
  - a detail panel with before → after numbers, and a build-summary panel;
  - smooth camera, keyboard + controller (`39_pad.js`) + mouse/touch;
  - reachable from the same shrine menu entry as today.
  
  Look at your own screenshots.
- **Icons:** 16×16 like the other `ui_icons`, in the same style, and readable.
- **Before you finish:**
  - Run `tools/shots/stress.js`, `dormant_chk.js`, `v19_test.js` and `keys_test.js` against your build.
  - Run the lead's `tools/shots/lead/final.sh`, or at least its edge and phantom parts. Point it at your build by
    running the node lines inside it with `SHOT_HTML`.
  - Report what you built, SHARED EDITS, NEEDS, test results, screenshots and known issues.
