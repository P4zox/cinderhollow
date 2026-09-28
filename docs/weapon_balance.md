# Weapon balance (weapon-feel pass, agent WB)

Contract: `docs/WEAPON_FEEL_CONTRACT.md` B1–B4. Everything here is measured, not estimated.

## How it was measured
- **`tools/shots/wb/bench_real.js`** — the realistic bench. Gravetusk held in place (max HP set to 3500 so %-based procs are boss-sized) swings every 2 s: a **1.3 s opening** to attack in, then a **0.7 s swing** the player rolls through. **Real stamina** (no refills; a swing is only started if a roll stays affordable after it, the roll costs stamina), **no FP spells**, a charged heavy on every third opening when it can land before the swing. Each weapon at **+5**, stats vig 35 / mnd 25 / end 25 / **str 30 / dex 30 / fth 25**, no skills, no charms, 60 s per weapon, fixed dice.
  - `sig` = damage done by signature code (tagged by wrapping every `SIGS` callback and every WFX / projectile it spawns); `status` = bleed/frost bursts and burn/rot ticks; `far60` = DPS with the player pinned 64 px from the boss's hurtbox; `farR` = signature DPS pinned at 1.5× the weapon's own melee reach (must be 0); `art` = DPS in the same loop when the weapon's art is used whenever it is ready (azure flask when dry).
- **Before/after use the same tree.** `tools/shots/wb/mk_baseline.py` swaps only WB's files back to their pre-pass copies (`tools/shots/wb/baseline/`) and drops `60_wbal.js`, so WA's new aerials and WC's hitstop are in both columns.
- `tools/shots/wb/art_bench.js` (one use of every art, tapped and charged), `sig_test.js` (worst case: infinite stamina, mash + a charged heavy every 2 s), `dominance.js` (B2 found-weapon axes), `lock_test.js` (B4), and the old `tools/shots/dps_bench.js` for continuity.
- Re-run: `BUILD_OUT=web/dist/wb.html python3 web/build_web.py && python3 tools/shots/wb/mk_baseline.py web/dist/wb.html web/dist/wb_base.html && tools/shots/wb/run_bench.sh web/dist/wb.html out.json` (and the same for `wb_base.html`); `python3 tools/shots/wb/table.py after.json before.json`.

## Realistic bench, before → after (DPS)

| weapon | class | base | DPS | sig DPS (%) | status DPS (%) | far60 | farR sig | with art |
|---|---|---|---|---|---|---|---|---|
| Carving Knife | dagger | 24 → 21 | 117 → **98** | 0 (0%) → 0 (0%) | 29 (25%) → 21 (21%) | 0 | 0 | 144 → 126 |
| Barnacle Fang | dagger | 23 → 21 | 117 → **93** | 0 (0%) → 0 (0%) | 38 (32%) → 21 (22%) | 0 | 0 | 143 → 134 |
| Hollow Fang | dagger | 21 | 113 → **92** | 0 (0%) → 0 (0%) | 42 (37%) → 13 (14%) | 0 | 0 | 137 → 121 |
| Pagecutter | dagger | 20 → 21 | 101 → **92** | 0 (0%) → 0 (0%) | 25 (25%) → 13 (14%) | 0 | 0 | 128 → 107 |
| Rotmaw Cleaver ★ | great | 50 → 52 | 106 → **109** | 0 (0%) → 0 (0%) | 20 (19%) → 20 (18%) | 0 | 0 | 94 → 120 |
| Greatsword of King Vael ★ | great | 56 | 135 → **108** | 26 (19%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 164 → 146 |
| Gravetusk ★ | great | 48 → 62 | 82 → **105** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 125 → 167 |
| Colossus Greathammer ★ | great | 55 → 47 | 120 → **103** | 0 (0%) → 0 (0%) | 25 (21%) → 21 (21%) | 0 | 0 | 241 → 143 |
| Meteor Maul | great | 60 | 105 → **105** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 118 → 121 |
| Cinder Maul | great | 50 → 46 | 108 → **99** | 0 (0%) → 0 (0%) | 22 (20%) → 20 (20%) | 0 | 0 | 127 → 117 |
| Forge Cleaver | great | 47 | 99 → **99** | 0 (0%) → 0 (0%) | 21 (21%) → 21 (21%) | 0 | 0 | 122 |
| Glacier Maul | great | 50 → 56 | 93 → **97** | 0 (0%) → 0 (0%) | 14 (15%) → 15 (16%) | 0 | 0 | 114 → 133 |
| Bell-Ringer’s Hammer | great | 49 → 55 | 87 → **97** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 143 → 124 |
| Gravecleaver | great | 46 → 57 | 77 → **95** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 123 → 122 |
| Tidecleaver | great | 50 → 64 | 74 → **94** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 118 → 130 |
| Starblade ★ | katana | 42 → 32 | 135 → **111** | 16 (12%) → 3 (2%) | 0 (0%) → 0 (0%) | 40 → 0 | 40 → 0 | 247 → 150 |
| Plasma Katana | katana | 40 → 36 | 119 → **107** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 160 → 130 |
| Duskveil | katana | 29 | 105 → **105** | 0 (0%) → 0 (0%) | 13 (12%) → 13 (12%) | 0 | 0 | 160 → 163 |
| Stormvein | katana | 30 → 31 | 98 → **101** | 0 (0%) → 0 (0%) | 4 (4%) → 4 (4%) | 0 | 0 | 155 → 148 |
| The First Ember ★ | mirror | 38 → 29 | 143 → **105** | 24 (17%) → 0 (0%) | 18 (13%) → 14 (13%) | 0 | 0 | 209 → 136 |
| The Last Kindling ★ | scythe | 43 → 29 | 144 → **108** | 39 (27%) → 2 (1%) | 19 (14%) → 15 (14%) | 0 | 0 | 252 → 162 |
| Antler of the Warden ★ | scythe | 36 → 37 | 119 → **105** | 15 (12%) → 2 (2%) | 0 (0%) → 0 (0%) | 0 | 0 | 145 → 150 |
| Crimson Scythe | scythe | 37 | 105 → **105** | 0 (0%) → 0 (0%) | 8 (8%) → 8 (8%) | 0 | 0 | 142 |
| Briar Scythe | scythe | 32 → 43 | 70 → **92** | 0 (0%) → 0 (0%) | 8 (12%) → 8 (9%) | 0 | 0 | 115 → 153 |
| Twinborne ★ | shield | 34 → 31 | 113 → **104** | 0 (0%) → 0 (0%) | 13 (12%) → 13 (12%) | 0 | 0 | 126 → 112 |
| Overseer’s Bulwark | shield | 33 → 43 | 79 → **103** | 0 (0%) → 0 (0%) | 11 (14%) → 15 (15%) | 0 | 0 | 125 → 158 |
| Knight’s Sword and Shield | shield | 28 → 36 | 76 → **98** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 74 → 101 |
| SAINT-0 Lance ★ | spear | 44 → 27 | 225 → **109** | 68 (30%) → 8 (8%) | 0 (0%) → 0 (0%) | 23 → 0 | 24 → 0 | 296 → 97 |
| Sovereign’s Rootspear ★ | spear | 34 → 31 | 126 → **107** | 4 (3%) → 5 (4%) | 0 (0%) → 0 (0%) | 18 → 0 | 19 → 0 | 160 → 135 |
| Stormfang ★ | spear | 35 → 30 | 149 → **107** | 31 (21%) → 6 (5%) | 0 (0%) → 0 (0%) | 29 → 0 | 30 → 0 | 176 → 131 |
| Harpoon of the Drowned Choir ★ | spear | 36 → 38 | 131 → **104** | 11 (9%) → 1 (1%) | 0 (0%) → 0 (0%) | 19 → 0 | 20 → 0 | 146 → 157 |
| Scarab Spear | spear | 37 → 34 | 113 → **104** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 130 → 118 |
| Rootspear | spear | 29 → 37 | 74 → **94** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 90 → 118 |
| Oswin’s Windstaff ★ | staff | 32 → 44 | 93 → **101** | 29 (31%) → 1 (1%) | 0 (0%) → 0 (0%) | 44 → 0 | 44 → 0 | 143 → 160 |
| Unwritten Quill ★ | staff | 30 → 42 | 102 → **99** | 40 (39%) → 7 (7%) | 0 (0%) → 0 (0%) | 0 | 0 | 137 → 147 |
| Sun Sceptre | staff | 34 → 41 | 67 → **97** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 88 → 157 |
| Librarian’s Lantern Staff | staff | 29 → 41 | 54 → **90** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 71 → 122 |
| Thornwood Staff | staff | 27 → 40 | 48 → **90** | 0 (0%) → 0 (0%) | 0 (0%) → 4 (5%) | 0 | 0 | 116 → 141 |
| Pilgrim’s Quarterstaff | staff | 28 → 45 | 45 → **87** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 109 → 139 |
| Oath of Kalden ★ | sword | 44 → 35 | 135 → **107** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 193 → 153 |
| Morvain’s Eclipse ★ | sword | 34 → 31 | 118 → **107** | 11 (10%) → 4 (3%) | 0 (0%) → 0 (0%) | 21 → 0 | 22 → 0 | 168 → 149 |
| Khopesh of the Veiled Pharaoh ★ | sword | 35 → 26 | 150 → **107** | 10 (7%) → 3 (3%) | 18 (12%) → 13 (12%) | 11 → 2 | 11 → 0 | 174 → 110 |
| Sanguine Rapier ★ | sword | 32 | 114 → **105** | 9 (8%) → 1 (1%) | 13 (11%) → 13 (12%) | 11 → 0 | 11 → 0 | 171 → 149 |
| Frostbrand | sword | 31 → 35 | 94 → **105** | 0 (0%) → 0 (0%) | 16 (17%) → 17 (16%) | 0 | 0 | 129 → 144 |
| Ashen Longsword | sword | 30 → 42 | 68 → **96** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 98 → 143 |
| Oathbrand | sword | 27 → 34 | 75 → **95** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 108 → 149 |
| Twinfangs | twin | 26 | 101 → **101** | 0 (0%) → 0 (0%) | 13 (12%) → 13 (12%) | 0 | 0 | 159 → 150 |
| Headsman’s Chain | whip | 32 → 35 | 94 → **103** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 145 → 148 |
| Orrery Lash | whip | 36 → 35 | 104 → **101** | 0 (0%) → 0 (0%) | 0 (0%) → 0 (0%) | 0 | 0 | 232 → 135 |
| Gravechain | whip | 30 → 35 | 83 → **96** | 0 (0%) → 0 (0%) | 4 (5%) → 4 (4%) | 0 | 0 | 192 → 142 |

★ = boss weapon (has a signature). Kalden's blade counts as one.

## Class check (B2)

| class | best found weapon | DPS | vs median | boss weapons (DPS, vs best found) |
|---|---|---|---|---|
| dagger | Carving Knife | 98 | -5% |  |
| great | Meteor Maul | 105 | +1% | Gravetusk 105 (+0%), Rotmaw Cleaver 109 (+4%), Colossus Greathammer 103 (-2%), Greatsword of King Vael 108 (+3%) |
| katana | Plasma Katana | 107 | +3% | Starblade 111 (+4%) |
| scythe | Crimson Scythe | 105 | +1% | Antler of the Warden 105 (+0%), The Last Kindling 108 (+3%) |
| shield | Overseer’s Bulwark | 103 | +0% | Twinborne 104 (+1%) |
| spear | Scarab Spear | 104 | +0% | Sovereign’s Rootspear 107 (+3%), Stormfang 107 (+3%), Harpoon of the Drowned Choir 104 (+0%), SAINT-0 Lance 109 (+5%) |
| staff | Sun Sceptre | 97 | -6% | Oswin’s Windstaff 101 (+4%), Unwritten Quill 99 (+2%) |
| sword | Frostbrand | 105 | +1% | Oath of Kalden 107 (+2%), Morvain’s Eclipse 107 (+2%), Sanguine Rapier 105 (+0%), Khopesh of the Veiled Pharaoh 107 (+2%) |
| twin | Twinfangs | 101 | -2% |  |
| whip | Headsman’s Chain | 103 | +0% |  |

Median of the class bests: **103.5**; every class's best found weapon is within ±15% (the widest is 97–107). The First Ember (mirroring the straight sword) is at 105, +0% on the best found sword. Before this pass the class bests ran 67–119 and boss weapons ran up to +99% over their class's best found weapon (SAINT-0 225 vs the Scarab Spear 113).

### Why the numbers moved the way they did
- **Charged heavies are the most stamina-efficient attack** in this game (2 × 1.55 × class heavy mult for one stamina bill, plus stance damage toward a riposte). Classes whose heavy can't be afforded in a boss opening lose that: the **staff** spin costs 80% of max stamina, so realistic staff play is lights only and staves benched at 45–67. Fixed within WB's files by making staves **stamina-cheap** (`stam` 0.9 → 0.55: "fast and patient") and raising `base` ~15–45%; their lights now hit about like a katana's. A cleaner fix is in NEEDS (spin cost), after which the staff bases should come back down.
- **Tri-scalers** (C/C/C: First Ember, Khopesh, Last Kindling; SAINT-0's D/B/C) are strongest at the neutral 30/30/25 spread, so their `base` fell most.
- **Status** was trimmed where it passed ~20% of DPS: dagger bleed 26 → 14, Barnacle Fang 24 → 16, Carving Knife 20 → 15, Pagecutter 22 → 15, Glacier Maul frost 34 → 30, Colossus fire 0.30 → 0.25. The Vael greatsword's ghost-fire burn is gone (now a visual).
- Found weapons that were strictly dominated (Ashen Longsword by Frostbrand, Rootspear by the Scarab Spear, the Lantern Staff by the Sun Sceptre) got a reason; `dominance.js` reports none left. Each found weapon's axes where it's its class's best:

  - Ashen Longsword: arStr, arDex
  - Oathbrand: arFth, holy
  - Frostbrand: reach, frost
  - Hollow Fang: speed, economy
  - Pagecutter: arFth, speed, economy, crit
  - Barnacle Fang: bleed
  - Carving Knife: arStr, arDex, reach, poise
  - Gravecleaver: arDex, speed, reach, economy
  - Cinder Maul: fire
  - Glacier Maul: frost
  - Bell-Ringer’s Hammer: arFth, economy, poise
  - Forge Cleaver: speed, economy
  - Tidecleaver: reach, economy
  - Meteor Maul: arStr
  - Rootspear: arDex, arFth
  - Scarab Spear: arStr, poise
  - Duskveil: bleed
  - Stormvein: reach
  - Plasma Katana: arStr, arDex, arFth, speed
  - Pilgrim’s Quarterstaff: arStr, arDex, speed
  - Librarian’s Lantern Staff: poise
  - Thornwood Staff: speed, bleed
  - Sun Sceptre: arFth, holy
  - Knight’s Sword and Shield: arDex, speed, economy, guard
  - Overseer’s Bulwark: arStr, arFth, poise, fire
  - Twinfangs: (none)
  - Briar Scythe: arStr, arFth, economy
  - Crimson Scythe: arDex, reach, poise, bleed
  - Headsman’s Chain: arStr, poise
  - Gravechain: arDex, speed, economy, bleed
  - Orrery Lash: arDex, arFth, speed, economy

- Stat changes besides `base`: dagger speed 1.4 → 1.45 and stamina 0.65 → 0.6 (fastest, cheapest dagger); Stormvein reach 1.1 → 1.2; Lantern Staff poise 1.0 → 1.2; staves stamina 0.9 → 0.55.

## Signatures (B1)
Worst case (`sig_test.js`: infinite stamina, mashing, charged heavy every 2 s) and a single plain light hit:

| weapon | first light hit adds | sig share, worst case | shortest gap between sig bursts (s) |
|---|---|---|---|
| Oath of Kalden | 0 → 0 | 0% → 0% | None → None |
| Gravetusk | 0 → 0 | 0% → 5% | None → 2.57 |
| Morvain’s Eclipse | 0 → 0 | 22% → 3% | 1.85 → 3.85 |
| Rotmaw Cleaver | 0 → 0 | 11% → 1% | 0.53 → 0.58 |
| Sovereign’s Rootspear | 0 → 0 | 2% → 4% | None → 3.68 |
| Unwritten Quill | 0 → 0 | 34% → 4% | 0.63 → 0.7 |
| Twinborne | 0 → 0 | 0% → 0% | None → None |
| Colossus Greathammer | 0 → 0 | 35% → 3% | 0.52 → 0.53 |
| Stormfang | 0 → 0 | 26% → 4% | 1.88 → 4 |
| Oswin’s Windstaff | 30 → 0 | 26% → 3% | 0.53 → 1.07 |
| The First Ember | 61 → 0 | 19% → 0% | 0.55 → None |
| Antler of the Warden | 0 → 0 | 21% → 3% | 1.63 → 3.53 |
| Harpoon of the Drowned Choir | 0 → 0 | 11% → 1% | 1.47 → None |
| Sanguine Rapier | 0 → 0 | 27% → 8% | 1.83 → 3.83 |
| Greatsword of King Vael | 0 → 0 | 3% → 1% | None → None |
| Khopesh of the Veiled Pharaoh | 0 → 0 | 10% → 3% | 0.77 → 3.85 |
| Starblade | 0 → 0 | 37% → 3% | 0.67 → 3.85 |
| SAINT-0 Lance | 45 → 6 | 33% → 6% | 0.62 → 1.15 |
| The Last Kindling | 17 → 0 | 19% → 2% | 0.5 → 0.87 |

Gaps under 2.5 s after the pass are ticks of one trigger (a rot pool, burning seams, a pyre, the whirlwind) or two independent sources (SAINT-0's per-foe glitch and its finisher line); every trigger that deals damage sits behind `sigGo` (finisher or charged heavy, ≥ 2.5 s internal cooldown) or a per-foe cooldown ≥ 2.5 s. Realistic bench: every signature ≤ 8% of its weapon's DPS; `farR` (signature damage at 1.5× reach) is 0 for every weapon; `far60` is 0 for every weapon.

Sustain: the Sanguine Rapier's crit heal went from 30% of the blow (up to 25% max HP, every crit) to 3% max HP every 6 s (rapier: 89 → 16 HP/min in the bench). Arts that drink (Blood Frenzy, Pale Pyre, Reap) now share a **boss-fight budget of one flask** (`60_wbal.js`): rapier with its art 624 → 257 HP in the 60 s bench (the flask cap is ~240 at 35 Vigor).

## Arts (B4)
`art_bench.js`: one use on the held boss with the weapon that now carries it. "hits" = damage ÷ that weapon's light attack rating.

| art | carried by (after) | FP | cooldown (s) | hits per use (tap) | hits per FP | hits per cooldown-second | i-frames tap / charged (s) |
|---|---|---|---|---|---|---|---|
| crescent | Ashen Longsword | 12 → 10 | 4.1 → 4 | 1.4 | 0.116 → 0.14 | 0.339 → 0.35 | 0/0 → 0/0 |
| bloodstep | Hollow Fang, Stormvein, Barnacle Fang | 8 → 8 | 3.3 → 4 | 1.34 | 0.168 → 0.168 | 0.406 → 0.335 | 0.3/0.47 → 0.3/0.47 |
| stormleap | Gravetusk, Glacier Maul, Meteor Maul | 16 → 14 | 5 → 5 | 2.94 | 0.184 → 0.21 | 0.588 → 0.588 | 0/0 → 0/0 |
| warcry | Gravecleaver, Rootspear, Rotmaw Cleaver, Scarab Spear | 10 → 8 | 18 → 13 | 0 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |
| moonwave | Duskveil, Oath of Kalden, Sovereign’s Rootspear, Frostbrand, Greatsword of King Vael | 14 → 12 | 4.6 → 5 | 2.38 | 0.17 → 0.198 | 0.517 → 0.476 | 0/0 → 0/0 |
| cinderblade | Cinder Maul, Oathbrand, Forge Cleaver, Librarian’s Lantern Staff | 14 → 12 | 26 → 26 | 0 | 0 → 0 | 0 → 0 | 0/0 → 0/0 |
| whirlwind | Pilgrim’s Quarterstaff, Thornwood Staff | 14 → 26 | 4.6 → 11 | 5.26 | 0.376 → 0.202 | 1.143 → 0.478 | 0/0 → 0/0 |
| gale_vault | Oswin’s Windstaff | 16 → 22 | 5 → 8 | 3.07 | 0.192 → 0.14 | 0.614 → 0.384 | 0.38/0.38 → 0.38/0.38 |
| ink_mark | Pagecutter, Unwritten Quill | 12 → 12 | 4.1 → 6.5 | 2.41 | 0.201 → 0.201 | 0.588 → 0.371 | 0/0 → 0/0 |
| aegis | Knight’s Sword and Shield | 10 → 10 | 3.7 → 7 | 0 | 0 → 0 | 0 → 0 | 1.2/1.82 → 0.7/1 |
| frost_aegis | Twinborne | 12 → 12 | 4.1 → 7 | 0 | 0 → 0 | 0 → 0 | 1.2/1.82 → 0.7/1 |
| shield_charge | Overseer’s Bulwark | 12 → 16 | 4.1 → 6 | 2.52 | 0.211 → 0.158 | 0.617 → 0.42 | 0.13/0.13 → 0.13/0.13 |
| magma_quake | Colossus Greathammer | 20 → 30 | 5.9 → 15 | 7.9 | 0.388 → 0.263 | 1.314 → 0.527 | 0/0 → 0/0 |
| thunder_lunge | Stormfang | 16 → 14 | 5 → 5 | 2.8 | 0.176 → 0.2 | 0.562 → 0.56 | 0.35/0.35 → 0.35/0.35 |
| tolling_blow | Bell-Ringer’s Hammer | 16 → 24 | 5 → 9 | 3.03 | 0.189 → 0.126 | 0.606 → 0.337 | 0/0 → 0/0 |
| twin_tempest | Twinfangs | 18 → 24 | 5.5 → 8.5 | 5.3 | 0.294 → 0.221 | 0.964 → 0.624 | 0/0 → 0/0 |
| echo | The First Ember | 6 → 16 | 3 → 8 | 5.15 | 0.858 → 0.322 | 1.717 → 0.644 | 0/0 → 0/0 |
| backstep_slash | Morvain’s Eclipse, Carving Knife | 10 → 10 | 3.7 → 3.7 | 2.01 | 0.201 → 0.201 | 0.543 → 0.543 | 0.23/0.23 → 0.23/0.23 |
| reap | Briar Scythe, Crimson Scythe | 14 → 12 | 4.6 → 4.5 | 1.79 | 0.128 → 0.149 | 0.389 → 0.398 | 0/0 → 0/0 |
| harvest_moon | Antler of the Warden | 18 → 16 | 5.5 → 5.5 | 3.21 | 0.179 → 0.201 | 0.585 → 0.584 | 0/0 → 0/0 |
| lash | Gravechain, Orrery Lash | 10 → 20 | 3.7 → 9 | 3.87 | 0.389 → 0.194 | 1.051 → 0.43 | 0/0 → 0/0 |
| chain_drag | Headsman’s Chain | 14 → 16 | 4.6 → 6 | 2.74 | 0.196 → 0.171 | 0.598 → 0.457 | 0.02/0.02 → 0.02/0.02 |
| blood_frenzy | Sanguine Rapier | 12 → 14 | 12 → 12 | 3.65 | 0.304 → 0.261 | 0.304 → 0.304 | 0/0 → 0/0 |
| tidal_surge | Harpoon of the Drowned Choir, Tidecleaver | 16 → 14 | 5 → 6 | 1.86 | 0.116 → 0.133 | 0.37 → 0.31 | 0/0 → 0/0 |
| solar_flare | Khopesh of the Veiled Pharaoh, Sun Sceptre | 16 → 18 | 5 → 6.5 | 2.94 | 0.181 → 0.163 | 0.58 → 0.452 | 0/0 → 0/0 |
| starfall | Starblade | 18 → 26 | 5.5 → 9 | 5.72 | 0.318 → 0.22 | 1.042 → 0.636 | 0/0 → 0/0 |
| overclock | SAINT-0 Lance, Plasma Katana | 14 → 10 | 4.6 → 6 | 1.48 | 0.105 → 0.148 | 0.32 → 0.247 | 0.3/0.3 → 0.3/0.3 |
| pale_pyre | The Last Kindling | 22 → 22 | 6.3 → 9.5 | 4.76 | 0.215 → 0.216 | 0.749 → 0.501 | 0/0 → 0/0 |

Per-use damage is unchanged (the art code belongs to agent G); the balance lever is FP and cooldown (`WB_ART_TUNE` in `60_wbal.js`), plus Aegis / Frost Aegis capped at 0.7 s (charged 1.0 s) of perfect guard instead of 1.2 / 1.8 s every 3.7 s. Buff arts (War Cry, Cinder Blade, Overclock) read 0 here; their value is the "with art" column of the realistic bench, where most weapons now gain +25–60% from their art (before: −11% to +142%). Low outliers left: Overclock on SAINT-0 (its speed buff can't show in a stamina-bound bench), Aegis/Frost Aegis (defensive), War Cry on the Rotmaw (+10%). Echo repeats whichever art you used last, so it is priced against the strongest (16 FP, 8 s).

## Old bench (`tools/shots/dps_bench.js`, infinite stamina, base stats) for continuity
| weapon | before | after |
|---|---|---|
| Ashen Longsword | L 53(12h)/s  H 95(10h)/s  light=46 heavy=47 | L 75(12h)/s  H 134(10h)/s  light=65 heavy=66 |
| Hollow Fang | L 67(14h)/s  H 126(11h)/s  light=33 heavy=33 | L 52(14h)/s  H 109(11h)/s  light=33 heavy=33 |
| Gravecleaver | L 102(13h)/s  H 153(9h)/s  light=72 heavy=73 | L 129(13h)/s  H 196(9h)/s  light=89 heavy=90 |
| Rootspear | L 33(7h)/s  H 80(9h)/s  light=45 heavy=46 | L 42(7h)/s  H 103(9h)/s  light=58 heavy=58 |
| Duskveil | L 161(28h)/s  H 150(10h)/s  light=45 heavy=45 | L 162(28h)/s  H 149(10h)/s  light=45 heavy=45 |
| Cinder Maul | L 143(13h)/s  H 234(8h)/s  light=78 heavy=79 | L 130(13h)/s  H 214(8h)/s  light=72 heavy=73 |
| Oathbrand | L 37(9h)/s  H 79(10h)/s  light=40 heavy=41 | L 46(9h)/s  H 98(10h)/s  light=50 heavy=51 |
| Oath of Kalden | L 229(30h)/s  H 152(10h)/s  light=69 heavy=70 | L 185(30h)/s  H 121(10h)/s  light=55 heavy=56 |
| Gravetusk | L 119(13h)/s  H 163(8h)/s  light=75 heavy=76 | L 171(17h)/s  H 212(8h)/s  light=97 heavy=98 |
| Morvain’s Eclipse | L 66(14h)/s  H 184(30h)/s  light=52 heavy=53 | L 49(11h)/s  H 101(10h)/s  light=47 heavy=48 |
| Rotmaw Cleaver | L 135(20h)/s  H 223(47h)/s  light=78 heavy=79 | L 120(13h)/s  H 178(9h)/s  light=81 heavy=82 |
| Sovereign’s Rootspear | L 61(12h)/s  H 98(9h)/s  light=51 heavy=52 | L 36(8h)/s  H 85(9h)/s  light=47 heavy=47 |
| Frostbrand | L 51(9h)/s  H 116(11h)/s  light=48 heavy=48 | L 56(9h)/s  H 129(11h)/s  light=54 heavy=55 |
| Pagecutter | L 67(15h)/s  H 107(12h)/s  light=31 heavy=31 | L 54(15h)/s  H 109(12h)/s  light=32 heavy=33 |
| Colossus Greathammer | L 154(21h)/s  H 281(48h)/s  light=85 heavy=86 | L 132(13h)/s  H 218(8h)/s  light=73 heavy=74 |
| Glacier Maul | L 167(15h)/s  H 209(10h)/s  light=78 heavy=78 | L 163(14h)/s  H 231(10h)/s  light=87 heavy=88 |
| Bell-Ringer’s Hammer | L 125(13h)/s  H 167(8h)/s  light=76 heavy=76 | L 141(13h)/s  H 189(8h)/s  light=85 heavy=86 |
| Forge Cleaver | L 133(13h)/s  H 212(8h)/s  light=74 heavy=75 | L 133(13h)/s  H 216(8h)/s  light=74 heavy=75 |
| Stormfang | L 47(9h)/s  H 167(21h)/s  light=54 heavy=55 | L 35(7h)/s  H 85(9h)/s  light=46 heavy=47 |
| Stormvein | L 151(28h)/s  H 141(10h)/s  light=47 heavy=47 | L 154(28h)/s  H 143(10h)/s  light=48 heavy=49 |
| Pilgrim’s Quarterstaff | L 48(14h)/s  H 229(21h)/s  light=43 heavy=44 | L 77(14h)/s  H 370(21h)/s  light=70 heavy=70 |
| Oswin’s Windstaff | L 140(50h)/s  H 266(66h)/s  light=49 heavy=49 | L 130(27h)/s  H 346(30h)/s  light=67 heavy=68 |
| Unwritten Quill | L 112(36h)/s  H 404(107h)/s  light=44 heavy=45 | L 40(11h)/s  H 327(28h)/s  light=62 heavy=63 |
| Librarian’s Lantern Staff | L 48(16h)/s  H 237(21h)/s  light=43 heavy=44 | L 68(14h)/s  H 326(21h)/s  light=61 heavy=62 |
| Knight’s Sword and Shield | L 105(27h)/s  H 27(4h)/s  light=43 heavy=44 | L 58(11h)/s  H 32(4h)/s  light=56 heavy=56 |
| Twinborne | L 70(12h)/s  H 35(4h)/s  light=52 heavy=53 | L 66(12h)/s  H 32(4h)/s  light=48 heavy=48 |
| Overseer’s Bulwark | L 58(11h)/s  H 46(4h)/s  light=51 heavy=51 | L 77(11h)/s  H 59(4h)/s  light=66 heavy=67 |
| Twinfangs | L 145(39h)/s  H 21(2h)/s  light=41 heavy=41 | L 147(39h)/s  H 21(2h)/s  light=41 heavy=41 |
| The First Ember | L 191(61h)/s  H 388(27h)/s  light=58 heavy=59 | L 128(39h)/s  H 41(2h)/s  light=44 heavy=45 |
| Antler of the Warden | L 202(45h)/s  H 262(41h)/s  light=55 heavy=56 | L 169(27h)/s  H 185(10h)/s  light=57 heavy=58 |
| Briar Scythe | L 175(25h)/s  H 189(10h)/s  light=49 heavy=50 | L 201(22h)/s  H 249(10h)/s  light=66 heavy=67 |
| Thornwood Staff | L 61(14h)/s  H 248(21h)/s  light=41 heavy=42 | L 84(16h)/s  H 356(21h)/s  light=61 heavy=62 |
| Harpoon of the Drowned Choir | L 48(9h)/s  H 126(15h)/s  light=55 heavy=56 | L 50(10h)/s  H 118(9h)/s  light=58 heavy=59 |
| Tidecleaver | L 110(13h)/s  H 174(9h)/s  light=78 heavy=78 | L 160(13h)/s  H 215(8h)/s  light=99 heavy=100 |
| Barnacle Fang | L 69(12h)/s  H 116(11h)/s  light=36 heavy=36 | L 52(12h)/s  H 109(11h)/s  light=33 heavy=33 |
| Sanguine Rapier | L 235(50h)/s  H 223(47h)/s  light=49 heavy=50 | L 73(14h)/s  H 139(11h)/s  light=49 heavy=50 |
| Carving Knife | L 57(12h)/s  H 120(11h)/s  light=38 heavy=38 | L 52(12h)/s  H 94(11h)/s  light=33 heavy=33 |
| Crimson Scythe | L 210(26h)/s  H 230(11h)/s  light=58 heavy=58 | L 211(26h)/s  H 229(11h)/s  light=58 heavy=58 |
| Greatsword of King Vael | L 160(14h)/s  H 239(14h)/s  light=87 heavy=88 | L 140(13h)/s  H 189(8h)/s  light=87 heavy=88 |
| Headsman’s Chain | L 128(31h)/s  H 125(13h)/s  light=50 heavy=50 | L 141(30h)/s  H 138(13h)/s  light=54 heavy=55 |
| Gravechain | L 149(30h)/s  H 139(14h)/s  light=47 heavy=47 | L 168(30h)/s  H 159(14h)/s  light=54 heavy=55 |
| Khopesh of the Veiled Pharaoh | L 112(23h)/s  H 173(21h)/s  light=53 heavy=54 | L 41(10h)/s  H 101(10h)/s  light=40 heavy=40 |
| Sun Sceptre | L 56(14h)/s  H 264(21h)/s  light=50 heavy=51 | L 38(9h)/s  H 329(21h)/s  light=61 heavy=62 |
| Scarab Spear | L 42(7h)/s  H 108(9h)/s  light=58 heavy=59 | L 44(9h)/s  H 106(9h)/s  light=53 heavy=54 |
| Starblade | L 267(48h)/s  H 265(32h)/s  light=65 heavy=66 | L 138(29h)/s  H 136(10h)/s  light=49 heavy=50 |
| Meteor Maul | L 150(13h)/s  H 204(8h)/s  light=93 heavy=94 | L 148(13h)/s  H 207(8h)/s  light=93 heavy=94 |
| Orrery Lash | L 143(30h)/s  H 134(13h)/s  light=55 heavy=56 | L 139(30h)/s  H 132(13h)/s  light=54 heavy=55 |
| SAINT-0 Lance | L 80(20h)/s  H 213(24h)/s  light=67 heavy=68 | L 97(30h)/s  H 91(13h)/s  light=41 heavy=42 |
| Plasma Katana | L 177(28h)/s  H 184(10h)/s  light=62 heavy=63 | L 158(28h)/s  H 164(10h)/s  light=56 heavy=57 |
| The Last Kindling | L 186(74h)/s  H 310(111h)/s  light=65 heavy=66 | L 138(35h)/s  H 187(11h)/s  light=44 heavy=45 |

This bench has infinite stamina, so it overrates the staff spin (a staff heavy every 0.3 s) and ignores stamina costs; use `bench_real.js` for decisions.


## Art reassignment (B4: each weapon has exactly one art, its own)
| weapon | before | after | why |
|---|---|---|---|
| Morvain's Eclipse ★ | Ashen Crescent | **Backstep Slash** | Morvain fights by backstepping and lunging in; the charged version looses the golden crescent. Gives the orphan art a home. |
| Carving Knife | Bloodstep | **Backstep Slash** | the Butler's hop-back-and-carve; a second home for the orphan |
| Oathbrand | Ashen Crescent | **Cinder Blade** | a cathedral blade that burns with its prayers |
| Pagecutter | Bloodstep | **Ink Seal** (`ink_mark`) | the scribe's knife "forever wet with violet ink" |
| Stormvein | Moonwave | **Bloodstep** | a lightning-quick draw-and-dash through the foe |
| Gravecleaver (greatsword) | Storm Leap | **War Cry** | "carries the weight of a hundred oaths": the ramparts' dead answer |
| Tidecleaver | Storm Leap | **Tidal Surge** | the drowned headsman drives the cleaver in and the sea answers |
| SAINT-0 Lance ★ | Thunder Lunge (Cindervane's) | **Overclock** | NEO-HALLOW's glitching dash; Thunder Lunge stays Stormfang's |
| Sun Sceptre | Cinder Blade | **Solar Flare** | a sceptre crowned with the sun |

Unchanged, and why they fit: Oath of Kalden ★ Moonwave (with its own teal oath slash), Gravetusk ★ Storm Leap (the Hound's pounce is its signature move), Rotmaw ★ War Cry (the Vessel's many-mouthed hunger roar), Sovereign's Rootspear ★ Moonwave (pale light), Greatsword of King Vael ★ Moonwave (pale-blue ghost-fire wave), Colossus ★ Magma Quake, Stormfang ★ Thunder Lunge, Windstaff ★ Gale Vault, Unwritten Quill ★ Ink Seal, Twinborne ★ Frost Aegis, First Ember ★ Echo, Antler ★ Harvest Moon, Choir Harpoon ★ Tidal Surge, Sanguine Rapier ★ Blood Frenzy, Khopesh ★ Solar Flare, Starblade ★ Starfall, Last Kindling ★ Pale Pyre; found weapons keep theirs (Longsword Crescent, Hollow Fang / Barnacle Fang Bloodstep, Maul / Forge Cleaver Cinder Blade, Glacier / Meteor Maul Storm Leap, Bell Hammer Tolling Blow, Rootspear / Scarab Spear War Cry, Duskveil / Frostbrand Moonwave, Plasma Katana Overclock, staves Whirlwind / Cinder Blade, shields Aegis / Shield Charge, Twinfangs Twin Tempest, scythes Reap, whips Lash / Chain Drag). Every art keeps an animation authored for its weapon's class or a generic one.

## Old art chests and shop entries
| where | was | now |
|---|---|---|
| A7 The Unbound Folio (`tools/regions/10_archives.py`) chest | `art:backstep_slash` | `ash_cache` (Tempering Cache: 1 emberstone + 300 cinders) |
| any other `art:*` item (old saves, other agents' rooms or shops) | Ash of X | the same cache (`ITEMS['art:*']` rewritten in `60_wbal.js`; `SHOPS` entries rewritten at load) |

No other room, region file or `SHOPS` list held an `art:` entry (searched `tools/rooms.py`, `tools/regions/*.py` incl. `60_oldsecrets.py` and `83_sa.py`, and `web/src`).

## Integrator follow-up (staff)
WB's NEEDS 1 applied: the staff spin now costs 45% of max stamina (was 80%), staff `stam` 0.55 → 0.8, and staff bases were retuned.
bench_real (60 s): quarterstaff 89, thornwood 88, lantern 97, sun sceptre 100, windstaff★ 98 (sig 2%), quill★ 94 (sig 8%). far60 = 0 for all.
