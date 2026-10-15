# v15 CORES: boss Cores, enchanting, enchant visuals, Rekindle

Agent `cores`. Everything lives in **`web/src/77_cores.js`** (one file, wrappers only). **No other source file was edited.**
Tests: `tools/shots/v15/cores/` (bench, flow, rematch, visuals, showcase). Build: `BUILD_OUT=web/dist/v15_cores.html python3 web/build_web.py`.

## 1. Boss Cores

* Every one of the 32 bosses (`BOSS_STAGE` in 69_adaptive.js) has a Core (`CORES` table below). The first kill adds it to
  `SAVE.cores` on top of the boss's own rewards: 74_arsenal9's conversion of boss weapons into Emberstones + cinders is
  untouched (BossBase.prototype.rewards is wrapped; the original chain runs first). A banner names the Core after the boss's
  own item banners (2.6 s + 2.4 s per reward item).
* **Decision: one Core per boss for the whole save lineage.** New Game+ keeps every Core and every enchant (the same rule as
  Weapon Mastery); killing the boss again in NG+ does not give a second one. Reason: a Core can sit in one weapon at a time,
  so where you set it is the choice; duplicates would let every weapon carry the best Core and remove that choice.
* Inventory: a new **Boss Cores** category (the 8th tab icon) lists them with where each one sits; the detail panel shows
  the trait, what it empowers and which boss it came from. Icons are drawn in code: a small cut gem in the Core's colour in
  a dark iron cradle (two-tone for the Twins), with a faint glow of its colour.
* Training Grounds: a **Boss Core** row in the weapon panel cycles any Core (or none) on the weapon in hand (sandbox only).

## 2. Enchanting at the Ashwright

* His choices gain **"Enchant a weapon"** (right after "Temper a weapon"). With no Core yet he explains what one is.
* The screen (menu `enchant`): the weapon in hand and what it carries; "Remove" (free, the Core comes back) when it carries
  one; every Core owned, with where it sits (`in hand`, another weapon, or its price). Right panel: the Core, its trait in
  its colour, the rule ("finishers · heavies · counters · charged releases") and what Enter will do.
* **Setting a Core costs 400 cinders; removing is free.** Each weapon type keeps its own (`SAVE.enchants[type] = kind`); a
  Core is in one weapon at a time; setting it in a second weapon moves it (toast says from where). Cheap on purpose: the
  owner should feel free to experiment; the trait budget, not the price, keeps it in check.

### What an enchant touches (`crElig`)
Only the weapon's **finishers (`mv.fin`), heavies (`kind: 'heavy'`), counters (`A.counter`) and charged releases
(`P.charged`)** (and anything a future table marks `punish: true`). Never ordinary light attacks, weapon arts (`tech`),
plunges or critical ripostes (crits are already the biggest single hit in the game). Every type has plenty of eligible
moves (Longsword 13 of 25, Greatsword 17 of 23, Staff 7 of 19; the five new v15 types register theirs the same way and are
picked up automatically).

Two channels:
* **edge**: `mvHitCtx` is wrapped: the move's damage multiplier (and, for stance Cores, its poise) grows by a flat share.
  It applies to `playerStrike` hits (the move's own swings). Additive, never multiplied by itself.
* **proc**: a `HOOKS.strike` entry: statuses, delayed strikes, sustain. Runs on every melee hit of an eligible move
  (also shockwaves / `mvStrikeAt` follow-ups of that move). Per-move gates ("first hit of this move on this foe"), internal
  cooldowns, and per-foe gates keep multi-hit moves from multiplying it.

### Control effects: great foes resist
Small foes take a slow at full strength. Bosses, their bodies and elites take **40% of the strength for half the time, and
each application within 10 s of the last on the same foe lasts half as long again (floor 25%)**: the Glacial Core's chill is
15% / 2 s on a soldier, 6% / 1 s on a boss, then 0.5 s, 0.25 s, 0.25 s. Staggers (Curfew) only ever hit small foes.
Quiet damage-over-time on bosses never lands the killing blow (the same rule burn uses).

## 3. The trait table

"Bench" = the measured gain **on the eligible moves' own damage** (tools/shots/v15/cores/bench.js: Longsword J J J J + K
loops on the WM dummy for 6 cycles, then 5 s for delayed procs). In that rhythm eligible moves are 39% of all damage, so a
+10% Core is about **+4% overall DPS**. Target +8..15% (or a utility of that worth); gate: never above +16%.

| Boss | Core | Colour | Trait | Effect | Bench | Why it fits / why it's safe |
|---|---|---|---|---|---|---|
| Gravetusk (hound) | Gravetusk's Core | blood red | **Rend** | marks; the 3rd mark within 6 s tears for 30% of that blow | 10% | the hound worries a wound; needs three committed moves |
| Oswin | Pilgrim's Core | ash white | **Wayfarer's Wind** | +4%; the roll within 2 s after is free | 4% + rolls | the pilgrim's road: commit, then slip out for free |
| Thorn Coven | Coven Core | thorn green | **Thornbind** | 9% of the blow over 3 s; refresh, never past 2 doses | 8.9% | thorns take root; pool capped so spam can't stack it |
| Antlered Warden | Antlered Core | moss gold | **Antler's Weight** | +25% stance damage, +3% damage | 3% + stance | a charging stag breaks guards, not health bars |
| Morvain (omen) | Omen Core | gold | **Omen Line** | a gold line flares under the foe, erupts 0.45 s later for 14% of the move (every 1.5 s) | 14% | his floor lines; ICD keeps it to one per exchange |
| Vessel of Rot | Vessel Core | rot green | **Rot Sap** | 10% of the move as rot over 5 s; up to 3 rots | 9.7% | many mouths; never the old rot (0.6% max HP/s, far too strong) |
| Ser Kalden | Oathless Core | oath ember | **Unbroken Oath** | enchanted moves can't be flinched by blows < 20% max HP; -10% damage taken during them | utility | the knight who would not yield: hyper armour only while committed |
| Head Librarian | Librarian's Core | violet ink | **Overdue** | a page in the foe; your next ordinary blow within 4 s tears it for 15% of that move | 12.5% | rewards weaving lights after a finisher (the only Core that pays off light hits, and only once) |
| The Unwritten | Unwritten Core | deep ink | **Redaction** | +4%; the foe is blotted 3 s: its blows 12% softer (8% great foes) | 4% + defence | ink blind; works on the attacker's `src`, bosses' projectiles count when the boss is inked |
| The Ferryman | Ferryman's Core | spectral teal | **Toll of Breath** | +8 stamina per enchanted blow (every 0.6 s) | 48 st / 12 moves | "one breath for the crossing" |
| Drowned Choir | Choir Core | sea glow | **Resonance** | each enchanted move within 4 s of the last +4% more, to +12% | 8% | a chord that builds and fades; additive, capped |
| Hollow Champion | Champion's Core | tarnished gold | **Unyielding** | +12% if unhit for 6 s, else +4% | 12% (4% hit) | undefeated: rewards clean play |
| Ice Golem Warden | Glacial Core | ice blue | **Chill** | +5%; 15% slower 2 s (great foes 6% / 1 s, diminishing) | 5% + slow | frost slow, the resisted form on bosses |
| Frostbound Twins | Twinned Core | flame / frost | **Flame and Frost** | moves alternate: burn 8% over 3 s / chill 10%; +3% | 6.9% + slow | the only two-colour Core: the slash alternates orange and ice |
| Vesper (butler) | Vesper's Core | silver | **Attentive** | the move after an enchanted one plays 12% faster (within 1.5 s) | haste | impeccable service: tempo, not damage |
| Countess Sanguine | Sanguine Core | crimson | **Blood Tithe** | heal 5% of enchanted damage, ≤ 2% max HP per move | 31 HP / 12 moves | lifesteal sliver; per-move cap so multi-hit moves can't farm it |
| Twin Executioners | Headsman's Core | iron red | **Verdict** | +3%; +25% against foes below 30% | 3% (28% low) | the headsman finishes; a closer, not an opener |
| King Vael | Hollow Crown Core | pale void | **Grief's Due** | +3 FP per enchanted blow (every 0.8 s) | 18 FP / 12 moves | the grief his court carries; fuels arts and spells |
| The Bell-Ringer | Bell Core | bronze | **Toll** | every 3rd enchanted move rings 56 px: 30% of the move + 40 stance to each foe in it | 10% | every toll a name; strong in crowds by design |
| Cindervane | Drake Core | storm blue | **Stormcall** | +4%; arcs to the nearest other foe within 90 px for 35% (every 0.5 s); alone grounds for 4% | 7.9% (alone) | the lightning arc to a second foe |
| Forge Overseer | Overseer's Core | molten orange | **Forgefire** | 10% of the blow as fire over 3 s; refresh, ≤ 2 doses | 10.1% | the burn |
| Molten Colossus | Colossus Core | magma | **Molten Crack** | the foe takes +6% from ALL your blows for 4 s (refresh, no stack) | 12.9% | plates come off (Ashwright's advice); a debuff, not a bigger finisher |
| Scarab Knight | Scarab Core | sun gold | **Sun Shell** | +3%; a shell soaks 8% max HP of the next blow within 3 s (every 6 s) | 3% + shell | carapace |
| Veiled Pharaoh | Pharaoh's Core | dusk violet | **Dusk Count** | marks the foe; 3 s later the mark falls for 25% of that move (one mark per foe) | 12.5% | he counted every grain; delayed, readable |
| Orrery Sentinel | Orrery Core | star white | **Orbit** | +5%, +10% stance; pulls small foes within 72 px toward the blow | 5% + pull | gravity pull; bosses are never moved |
| Astrel | Star Core | starlight | **Starfall** | every 3rd enchanted move drops a star on its foe for 30% | 10% | she fell so nothing else would |
| Enforcer Mech | Enforcer Core | neon red | **Curfew** | +5%; small foes stagger (once / 4 s each); great foes only slow 10% briefly | 5% + control | compliance shock; the control is the resisted kind on bosses |
| SAINT-0 | Null Core | null cyan | **Nullify** | +4%; erases enemy projectiles within 64 px of the blow (every 2 s) | 4% + defence | "be archived" |
| Gilded Sentinels | Gilded Core | gilded | **Twin Oath** | a gilded echo 0.3 s after each enchanted move for 12% of it | 12% | two oaths, one gate: the second blow |
| Pale Sovereign | Sovereign Core | pale gold | **Kneel** | +15% stance, +4%; staggered foes take +8% more | 4% (12% staggered) | makes great foes kneel, then punishes the kneel |
| The First Ember | First Ember Core | ember red | **Kindling** | 3 enchanted moves build kindling; the 4th burns it for +40% | 6.7% | the first fire, banked then loosed |
| Venn | Last Kindling Core | pale flame | **Last Flame** | +16% below 40% HP, else +4% | 4% (16% low) | the last flame burns brightest when you're nearly out |

How the numbers were picked: the boss weapons used to be signature effects on EVERY hit (fire % on all heavies, bleed on all
blows, rot ticking 0.6% max HP/s), which is why they were too strong. Cores only touch committed moves (about 40% of damage),
so even the strongest (Omen Line, Molten Crack, Twin Oath, Unyielding at +12..14%) are ~+5% overall DPS. Utility Cores are
sized to "a free roll / 8 stamina / 3 FP / 2% HP per committed move". Nothing stacks with itself: DoTs are pools capped at
two doses, debuffs refresh, the chord is additive and capped, marks are one per foe.

## 4. Enchant visuals

* **Slash light (刀光) and hit sparks**: while an enchanted move plays (`mvUpdate` is wrapped) every `spawnFx` the player's
  move makes (the slash arc, `parry_spark` / `hit` on impact) gets `tint: <Core colour>` (spawnFx already supported tints:
  a 55% colour wash). Proc strikes tint their own hit sparks too.
* **Tip ribbon, impact sparks, charged flare**: `feelElement` (61_feel.js) is wrapped: during an enchanted move it returns the
  Core's element (glow colour, light rgb, particle kind), so the ribbon, the element burst and its light take the colour.
  Ordinary blows keep the weapon's own look (tested: no tint before the finisher).
* **Idle**: an enchanted blade sheds a faint rising ember of its colour from its tip every 0.2-0.4 s and holds a soft light
  (16 px, 0.22) on the blade. No aura, no loop sound.
* Proc effects are thin, glow-layer line work: the omen line and its pillar, a jagged storm arc between foes, the bell's
  expanding ring, a small dusk diamond above the marked foe, a falling star streak, Kalden's brief armour wash when a blow
  is shrugged off, the Scarab shell's faint light.
* Shots: `out/show_finisher_overseer_*.png` (dark den, Forgefire), `out/finisher_*.png`, `out/idle_glow_*.png`, `out/proc_*.png`.

## 5. Rekindle (boss rematch)

* **The effigy**: in a defeated boss's home room (31 bosses; homes from the Training Grounds' room scan), once nothing is
  alive and the victory banner has gone, an ember effigy stands where the player enters the arena (`TRN_PSTART`, else a dozen
  tiles from the boss; moved to the nearest dry, standable tile clear of the fog gates: in the Drowned Choir's pool that is
  the doorway ledge). A slender iron stake in a scatter of ash with the boss's Core hovering in its cradle, glowing its
  colour. Prompt: **"Rekindle <boss>"** (E). A short lore line and a choice: "Rekindle …" / "Let the ash lie".
* **The rematch**: `crRekindle` lifts `boss:<kind>` only for the synchronous `enterRoom` rebuild and restores it in a
  `finally`, so the boss's own spawn code, fog gates and arena machinery run exactly as at the first fight, and **every save
  (even one made mid-fight) still holds the flag**. Cut-scene flags are set, so the intro is the short roar + banner. The
  arena seals as before (tested: fog gates / walls on in 29 of 31; the open arenas, Vessel and Cindervane, never had fog).
  The Hollow Champion is pre-called (its banner gauntlet is skipped). Unlimited rematches.
* **A rekindled kill** (`boss.rematch`): Weapon Mastery +150 (same as any repeat kill) and **10% of the boss's cinders**
  (through gainCinders, so NG+ / difficulty / Greed apply). No Core, no items, no flags, no ending: the Sovereign's
  `victoryBanner.ending` is stripped and the First Ember's epilogue timer / Venn's finale timer are cleared. The effigy
  relights after the banner.
* **Death in a rematch: nothing is lost** (decision: better than a normal death). No remnant, cinders kept, a toast says so;
  you wake at your shrine as usual and the boss stays defeated. Once the rekindled boss is down, a death there is an ordinary
  one again. Leaving the room, resting, dying or quitting ends the rematch. A save written while the arena is being rebuilt
  (an enter hook that saves) is patched to hold the flag too (`saveGame` is wrapped only for that instant).
* **Excluded**: Venn (her death *is* the betrayal ending). Rekindling also waits while a story beat is still pending (the
  First Ember's epilogue, Venn's last flame, the Sovereign's ending banner) so no epilogue can fire mid-rematch.

## 6. Tests (all pass)

| File | Run | What |
|---|---|---|
| `bench.js` | `SHOT_HTML=web/dist/v15_cores.html sh tools/shots/wm/run.sh tools/shots/v15/cores/bench.js <out>` | the 32-row table above (small + great foe), budget gate ≤ 16%, light attacks never carry it (DoT and edge), Verdict / Last Flame / Unyielding exact multipliers, stance only on eligible moves, control resistance numbers, the Training row |
| `flow.js` | `SHOT_HTML=… node tools/shots/shot.js tools/shots/v15/cores/flow.js <out>` | first-kill drops on Gravetusk, Twins and Sentinels; boss cinders and Emberstone conversion still pay; the banner; no duplicates; effigy appears; a save made during the rematch rebuild holds the flag; the Ashwright dialogue → "Enchant a weapon" → set / cost / remove / reset → leave, all by real inputs; one Core one weapon; inventory category; save/load; Continue; NG+ keeps Cores and enchants; NG+ kill gives no duplicate |
| `rematch.js` | `… node tools/shots/shot.js tools/shots/v15/cores/rematch.js <out>` (~6 min) | for all 31: first kill → Core → effigy → prompt → rekindle → boss back with `rematch` → mid-fight save holds the flag → kill → flags, Cores, items, ending unchanged, Mastery +150 (plus any adds' kill XP), 10% cinders, no ending dialogue → effigy returns. Death in a rematch (cinders kept, no remnant, boss stays down); a normal death still leaves a remnant; three Twins rematches in a row |
| `visuals.js` | wm runner | slash tint and ribbon colour on finishers for 4 Cores, plain light hits, nothing tinted without a Core, idle ember, omen line + pillar, storm arc (second foe hit), bell ring, dusk sigil, starfall |
| `showcase.js` | shot.js | dark-arena snapshots: effigy, prompt, dialogue, rekindled banner, Forgefire / Stormcall finishers, idle blades |

## 7. Decisions for the owner
1. **Cores across NG+**: kept, never duplicated (one per boss for the save). Alternative: a second copy per NG+ cycle.
2. **Socket price** 400 cinders flat; removing free. Could be 0, or scale with the boss's stage.
3. **Rematch death costs nothing**; rematch pays 10% cinders + 150 Mastery. If farming worries you, drop cinders to 5%.
4. **Venn can't be rekindled** (story). Everyone else can, including the Sovereign after the ending.
5. Biggest Cores (+12..14% on eligible moves): Omen Line, Molten Crack, Twin Oath, Unyielding, Pharaoh, Overdue. If
   finishers feel too strong with the five new weapons' bigger finishers, shave those to +10%.
6. Crits/ripostes, weapon arts and plunges don't carry enchants. Easy to add (crElig) if you want ripostes to count.

## 8. Notes / pre-existing quirks found while testing (not changed; not in my files)
* A boss struck to zero **during its intro or a transformation** stands back up (Gravetusk in `intro`, the Antlered Warden in
  `xform`): its rewards fire, the flag is set, but it keeps fighting. Only reachable with absurd burst (99999 test hits); the
  Training Grounds already guards its sandbox against it (65_training.js line ~288). Normal damage can't reach it.
* Killing one Frostbound Twin during the 2.6 s opening guard leaves the survivor stuck in `absorb` (the guard pose overwrote
  the absorb animation), invulnerable. Same: unreachable with normal damage.
* Bows (v15) only carry enchants on hits that go through the strike hooks (`playerStrike` / `mvStrikeAt`); arrow projectiles
  that call `t.hit` directly get no proc.

## Shared-file edits
None. `web/src/77_cores.js` wraps: `mvStart`, `mvHitCtx`, `mvHurtPre`, `mvSpeed`, `mvDodge`, `mvUpdate` (75_moves.js),
`hurtPlayer`, `finishDeath`, `startNGPlus`, `feelElement`, `spawnFx`, `icon`, `drawDetail`, `menuInput`, `renderMenu`,
`npcScript`, `wmTrainingRows`, `saveGame` (only while a rematch arena is rebuilt), `BossBase.prototype.rewards`; pushes to `HOOKS.strike/update/render/enter` and `INV_CATS`.
