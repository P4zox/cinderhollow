# Weapon Revamp — build contract (read fully before touching anything)

The design is **docs/WEAPON_REVAMP.md**. Its Part A move tables (damage, poise, stamina, timing, mastery unlocks) are
the specification. This file covers who owns what, the shared APIs, tag names and rules. Read §0 of
`docs/EXPANSION_CONTRACT.md` for the harness:
- per-agent builds: `BUILD_OUT=web/dist/<you>.html python3 web/build_web.py`;
- tests: `SHOT_HTML=web/dist/<you>.html node tools/shots/shot.js <script> <outdir>`;
- **no git** (the lead manages the local `weapon-revamp` branch; **nothing is pushed or published**).

Edit only the files you own. For anything else, write a `NEEDS:` line in your report with the exact patch.

## 1. Decisions (binding)
- **Weapons:** all 50 are deleted. **Exactly 9 remain, one per type.** Existing ids are kept so icons and overlays
  still work:

  | Type id | Weapon id | Name | Default art (locked) | Anim prefix | Existing anim base |
  |---|---|---|---|---|---|
  | `longsword` | `longsword` | Ashen Longsword | `crescent` | `ls_` (new) + sword tags | `attack1-4`, `heavy`, `attack_up/air_attack/attack_down`, `parry`, `riposte` |
  | `katana` | `katana` | Duskveil | `moonwave` | `kt_` | `kt_1-3`, `kt_heavy`, `kt_up/air/down` |
  | `greatsword` | `greatsword` | Gravecleaver | `stormleap` | `gs_` | `gs_1-3`, `gs_heavy`, `gs_up/air/down` |
  | `maul` | `maul` | Cinder Maul | `tolling_blow` | `ml_` (new) | the `gs_` frames, re-posed |
  | `sns` | `knight_shield` | Knight's Sword and Shield | `aegis` | `sh_` | `sh_1-3`, `sh_heavy`, `sh_up/air/down`, `sh_block/guard`, `sh_counter` |
  | `dual` | `twinfangs` | Twinfangs | `twin_tempest` | `tw_` | `tw_1-5`, `tw_heavy`, `tw_up/air/down` |
  | `spear` | `spear` | Rootspear | `thunder_lunge` | `sp_` | `sp_1-3`, `sp_heavy`, `sp_up/air/down`, spear dive |
  | `staff` | `quarterstaff` | Pilgrim's Quarterstaff | `whirlwind` | `st_` | `st_1-4`, `st_heavy`, `st_up/air/down` |
  | `whip` | `headsman_chain` | Headsman's Chain | `lash` | `wh_` | `wh_1-3`, `wh_heavy`, `wh_up/air/down` |

  The Dagger, Scythe and mirror types are removed.
- **Choosing and switching:**
  - All 9 types are available. **New Game asks for a starting weapon** (after the difficulty).
  - **Weapons can only be changed at shrines:** a shrine menu option "Change weapon". The Esc equipment screen shows
    the weapon read-only.
  - The Training Grounds panel may still switch freely (it's a sandbox).
- **Progression:** each type keeps its own upgrade level, +0 to +5, with the existing Emberstone costs.
- **Weapon Mastery:**
  - Ranks I–V per type; XP and thresholds are in WEAPON_REVAMP.md §A11.
  - Ranks unlock the moves listed in each weapon's Mastery table, and those moves are gated by rank.
  - Mastery **carries into New Game+**.
- **The skill tree's Arsenal page becomes the Weapon Mastery page:** the 9 types, each with its rank, XP and unlocks.
  The old Arsenal nodes (`m_<cls>`) are removed and their points refunded.
- **Bosses:** boss weapon rewards become Emberstones plus cinders. Boss signature effects (SIGS) are removed with the
  boss weapons.
- **Staff:** the vault is **not** an attack. The 2-air-attack limit (`AIR_CHAIN`/`AIR_CD`) applies to every type,
  unchanged.
- **Whip grapple:** pulls you to hook rings and large non-boss foes; pulls small foes to you; **never** bosses.
- **Kept untouched, and must keep working:** parry rework (67), breathers (71), strength-matching (69), difficulty (64),
  progression costs (70), integrity (68), Training Grounds (65), save slots (66), mouse (63).

## 2. Ownership
| Agent | Job | Owns |
|---|---|---|
| **WS: systems and content** | Weapon data down to 9; weapon types; mastery XP and ranks; the mastery screen and skill-tree page; New Game weapon select; shrine "Change weapon"; read-only equipment slot; loot, shop and boss-reward conversion; SIGS removal; save migration; Training Grounds weapon tab | new `web/src/74_arsenal9.js` (and more `74*` files if needed); `web/src/01b_gear.js` (WEAPONS / ARTS data), `13_weapons.js`, `15_weapons2.js`, `04b_sigs.js`, `60_wbal.js`, `29_ui2.js`, `08b_menus.js`, `08_ui.js` (shrine menu only), `57_skills.js`, `58_skilltree_ui.js`, `65_training.js` (weapon tab), `64_diffmode.js`/`66_slots.js` (title flow only), `09_main.js` (newSave / armory only), `05_combat.js` (item grant only), `tools/rooms.py` + `tools/regions/*.py` (only `w:` item / reward entries), `tools/shots/ws/` |
| **WM: moves and mechanics** | The move-table engine and all 9 types' moves and mechanics per WEAPON_REVAMP.md Part A; hitboxes; the balance bench | `web/src/04_player.js`; new `web/src/75_moves.js` (move tables + `WEAPON_UNLOCKS`), new `web/src/76_mech_*.js` (one per mechanic, or grouped); `web/src/61_feel.js` (class weights for the new type ids); `tools/shots/wm/` |
| **WA1: animation A** | New tags for Longsword, Katana, Greatsword, **Maul**, Sword & Shield, and trimming the overlay list to the 9 weapons | `art/player_v13_a.py`; `art/gen_player.py` (only: `WPN_IDS` → the 9 weapon ids, metadata `meta_for` for new tags, bug fixes); `tools/shots/wa1/` |
| **WA2: animation B** | New tags for Dual Blades, Spear, Staff, Whip | `art/player_v13_b.py`; `tools/shots/wa2/` |
| Lead | Integration, the final asset build, the full test suite, the local commit | everything else |

**Art build rule:** `art/gen_player.py` builds `assets/player*` and every `wpn_*` in one go, and two builds at once
would overwrite each other.
- **WA2 never runs a full build.** Iterate with `art/player_preview.py` (contact sheets from the generator, no assets
  written). Your module is imported through `register(G)`.
- **WA1** may run full builds, at most one at a time, after the 9-weapon trim (a much faster build). Report when
  you do.
- The lead runs the final build.

## 3. Tag names (WA ↔ WM)
- Tags are `<prefix>_<move>`. Each new tag must match the **timing** in WEAPON_REVAMP.md: total time from the table,
  hit frames at the wind-up.
- Each tag's `player_meta` entry needs an active window and a hit box. WA1 adds what `meta_for` needs.
- **Where a move can reuse an existing tag, WM maps it there** and no new tag is needed.
- **WM must fall back to the nearest existing tag** when a new tag isn't in the sheet yet (`pHas(tag)`), so WM can
  build before the art lands.

**New tags to author:**

| Prefix | New tags |
|---|---|
| **ls** | `ls_kc_hold`, `ls_kc`, `ls_jjk`, `ls_jjjk`, `ls_quick`, `ls_step`, `ls_fore_stance`, `ls_fore_cut`, `ls_pommel` |
| **kt** | `kt_sheathe`, `kt_sheathed_idle`, `kt_sheathed_walk`, `kt_iai`, `kt_focus_hold`, `kt_focus`, `kt_iai_parry`, `kt_sidestep`, `kt_stepcut`, `kt_flurry`, `kt_flash` |
| **gs** | `gs_charge_hold` (loop; glow per level is engine FX), `gs_charged`, `gs_strong`, `gs_true1`, `gs_true2`, `gs_guard`, `gs_tackle`, `gs_rollheavy`, `gs_wrath` |
| **ml** | `ml_1`, `ml_2`, `ml_3`, `ml_charge_walk` (loop), `ml_charge_idle`, `ml_upswing`, `ml_double`, `ml_bigsmash`, `ml_spin` (loop), `ml_spin_end`, `ml_brace`, `ml_rollswing`, `ml_bb1`, `ml_bb2`, `ml_bb3`, `ml_bb4`, `ml_quake` (maul aerials reuse `gs_up/air/down`) |
| **sh** | `sh_4` (shield-bash finisher), `sh_rush_hold`, `sh_rush`, `sh_backhop`, `sh_leap`, `sh_slam`, `sh_fallbash` |
| **tw** | `tw_demon_on`, `tw_d5`, `tw_d6`, `tw_dflurry`, `tw_ddash`, `tw_dance`, `tw_dance2`, `tw_dashslash`, `tw_counter` |
| **sp** | `sp_guard` (stance), `sp_guard_walk` (loop), `sp_gpoke`, `sp_counter`, `sp_hop`, `sp_charge_run` (loop), `sp_finish`, `sp_pguard`, `sp_ccounter` |
| **st** | `st_vault`, `st_aspin`, `st_aspin2`, `st_divekick`, `st_lowsweep`, `st_twirl_up`, `st_gale` |
| **wh** | `wh_overhead_hold`, `wh_overhead`, `wh_thunder`, `wh_grapple`, `wh_grapple_pull`, `wh_retreat`, `wh_snap`, `wh_slam`, `wh_double`, `wh_thousand` (loop) |

## 4. Shared APIs (WS ↔ WM)
**WS provides,** in `74_arsenal9.js`:
- `WTYPES`: the 9 type ids, in the table order above.
- `WTYPE_INFO[type]` = `{ weapon, name, art, prefix, desc, icon }`.
- `wtype()`: the current type id. `wcls()` must return the **type id** for the equipped weapon, and `WEAPON_CLASS`
  maps the 9 weapon ids to type ids.
- `masteryRank(type)` → 1..5 · `masteryXP(type)` · `masteryGain(type, xp, why)` · `MASTERY_XP = [0, 300, 900, 2000, 4000]`.
- WS hooks XP for hits and kills. **WM calls** `masteryGain(wtype(), 5, 'counter')` on successful parries, counters,
  Iai parries, snap counters and perfect dodges.

**WM provides,** in `75_moves.js`:
- `WEAPON_UNLOCKS[type] = [{ rank, id, name, input, desc }]`, from each weapon's Mastery table. WS's mastery screen
  and skill-tree page render it.
- `moveset()` / `MOVESETS[type]` keyed by the new type ids. Every system that reads `ATK[P.state]` keeps working:
  parry, feel, skills, Training Grounds.
- A rank-gated move simply isn't available below its rank. The engine asks `masteryRank(wtype()) >= rank`, which reads
  1 if WS's file isn't present yet.

## 5. Rules
- **Old saves:**
  - Old weapon classes map to new types: sword → longsword, dagger → dual, twin → dual, great → greatsword (maul,
    colossus_hammer, glacier_maul, bell_hammer, meteor_maul, gravetusk, rotmaw → maul), scythe → greatsword,
    shield → sns, mirror → longsword.
  - A type starts at the best upgrade level among the old weapons that map to it.
  - Every type the player owned a weapon of starts at mastery rank II.
  - The equipped weapon becomes its type's weapon. Removed arts are dropped.
  - WS writes and tests this.
- **The skill tree's Flame branch** reads the current art, so it still works with the 9 arts.
- **The 61_feel weights** move to the new type ids (WM).
- **Quality bar:**
  - Animations follow the taste rules: sleek, heroic, smooth silhouettes, no jaggies or clipping.
  - Each mechanic has its feedback: the Katana sheathe glint, the Greatsword charge glow per level, the Maul stun, the
    Demon Mode aura, the perfect-dodge afterimage, the Staff momentum, the Whip tip spark.
  - Look at your own previews and screenshots.
- **Tests before you report:**
  - WS: migration, the select screen, shrine-only switching, mastery XP and ranks, the skill-tree page, loot
    conversion.
  - WM: every input in every table produces its move, with damage, poise and stamina within ±10% of the table;
    each mechanic; rank gating; the air limit; and a bench of dmg/s per route against the table.
  - WA: every new tag renders for its weapon, and timing matches the table.
  - Everyone runs `stress.js`, `keys_test.js`, `v19_test.js` and `dormant_chk.js` on their build.

## 6. Report (every agent)
- What you built.
- Files touched.
- NEEDS, as exact patches.
- Test output.
- The preview and screenshot paths you looked at.
- Known issues.
- Open design calls you made, so the lead can raise them with the user.
