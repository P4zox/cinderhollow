# Cinderhollow expansion — build contract (read fully before touching anything)

Several agents build the expansion **at the same time in the same tree**. This file is the single source of truth for
who owns which files, which ids exist, where each region sits on the world grid and how it is gated.
Plan and story context: `docs/EXPANSION_PLAN.md`. Art conventions + creature meta format: `docs/ART_SPEC.md`, `docs/ART_SPEC2.md`.

## 0. Ground rules
- **Only edit files you own (section 2).** Everything else is read-only for you. If you truly need a change in a shared
  file, don't make it: put a `NEEDS:` line in your final report with the exact patch, and the integrator applies it.
- Add content through the registries/hooks in section 3 from **your own new files**.
- Build to your own output so builds don't clobber each other:
  `BUILD_OUT=web/dist/<you>.html python3 web/build_web.py` (it also regenerates `web/src/02_rooms.js` via `tools/rooms.py`).
  The build no longer fails on room validation errors — **read the `ERR` lines and make sure none are from your rooms.**
  Other agents' region files may be half-finished at any moment; ignore errors that aren't yours.
- Test headlessly: `SHOT_HTML=web/dist/<you>.html node tools/shots/shot.js <script.js> <outdir>` — the script body runs in
  the page as an async function with `G = window.__game`, `boot()` (new game, skips intro) and `await snap(name)` (saves the
  canvas PNG). `python3 tools/shots/sheet.py '<outdir>/*.png' montage.png 4` builds a contact sheet you can Read.
  Debug API on `window.__game`: `step(n, hold[], tap[])`, `tp(room, tx, ty)` (ty = the row the player **stands in**, i.e. one
  above the floor row), `give({...})`, `giveArmory()`, `grantTechniques()`, getters `P boss enemies room state SAVE D props cut`.
  Actions for hold/tap: left right up down jump attack heavy roll parry spell art hook interact pause.
- All art goes through Aseprite: generate cels with Python/PIL, then `art/asebuild.py build(name, w, h, layers, frames, tags)`
  → `art/<name>.aseprite` + `assets/<name>.png/.json` (+ write `assets/<name>_meta.json` yourself for creatures).
  Look at `art/gen_kalden.py`, `art/gen_sovereign.py`, `art/gen_enemies3.py`, `art/gen_archives.py` for the house style.
- **Boss/creature design taste (user feedback, mandatory):** dark mythology, cool, sleek, smooth silhouettes; small
  menacing heads; heroic/slender anatomy; restrained glow accents on dark palettes; no chubby/bulbous/blocky/cartoon
  shapes, no noisy texture grids, no jaggy staircase outlines. The approved quality bar is Morvain (`assets/boss*.png`),
  Gravetusk (`hound`), Ser Kalden (`kalden`), the Vessel and the Pale Sovereign. Approved concept sheets (build the
  sprites from these): `art/concepts/unwritten.png`, `twins.png`, `cindervane.png` (drawn from the user's reference
  `ref_cindervane.png`), `colossus.png` (+ `*_closeup.png`, `*_idle/air/roar/breath.png`). Bosses without a concept sheet
  must be designed to the same bar.
- Asset names must be prefixed so they can't collide (section 2 lists your prefixes).
- Keep performance sane: sprite sheets as horizontal strips, ≤ ~4096 px wide per sheet where possible (split p1/p2 like Kalden).

## 1. Decisions already made (don't reopen)
- Region play order: Ashen Archives → Hoarfrost Aqueduct → Tempest Spire → Burning Deep. New regions are **optional** side
  content (main path stays Hound → Morvain → Kalden → Sovereign). Spirit echoes: **out**. Oswin: **level-scaled**.
- Unlock chain: wall-jump (Gravetusk) → Archives · Root Hook (The Unwritten) → Hoarfrost · Ember Dash (Twins) → Tempest
  Spire · Gale Cloak (Cindervane) → Burning Deep · Cinder Slam (Colossus) → old-area secrets + Ember's Hollow.
  Technique item ids already exist: `hook`, `emberdash`, `gale`, `slam` (grant with `grantItem(id)` or boss `reward`).
- Every main boss gets an intro cutscene (first encounter only, Esc skips) and a phase-2 mini-scene; see §3.6.
- Global boss damage scale `BOSS_DMG = 0.7` applies to every boss hit (`hurtPlayer(BOSS_DMG * dmg * NGP.dmg, …)`).

## 2. Ownership
| Agent | Owns (may edit/create) | Asset prefixes |
|---|---|---|
| **W — weapons & player** | `art/gen_player.py`, `web/src/04_player.js`, `web/src/04b_sigs.js`, new `web/src/13_weapons.js`, `assets/player*`, `assets/wpn_*` | `player`, `wpn_` |
| **G — spells, charms, arts, icons** | new `web/src/14_gear2.js`, new `art/gen_ui3.py`, new `art/gen_fx4.py` | `ui_icons3`, `fx_g_` |
| **A — Archives finale** | new `tools/regions/10_archives.py`, new `web/src/20_archives2.js`, new `art/gen_unwritten.py` (+ helpers `art/unwritten_*.py`) | `unwritten`, `fx_ink_`, `ar2_` |
| **H — Hoarfrost Aqueduct** | `tools/regions/20_hoarfrost.py`, `web/src/21_hoarfrost.js`, `art/gen_hoarfrost*.py`, `art/hoarfrost_*.py` | `hoarfrost`, `tiles_hoarfrost`, `bg_hoarfrost_*`, `hf_`, `twins*`, `ice_warden*`, `fx_hf_` |
| **S — Tempest Spire** | `tools/regions/30_spire.py`, `web/src/22_spire.js`, `art/gen_spire*.py`, `art/spire_*.py` | `tiles_spire`, `bg_spire_*`, `sp_`, `cindervane*`, `bellringer*`, `fx_sp_` |
| **D — Burning Deep** | `tools/regions/40_deep.py`, `web/src/23_deep.js`, `art/gen_deep*.py`, `art/deep_*.py` | `tiles_deep`, `bg_deep_*`, `dp_`, `colossus*`, `overseer*`, `fx_dp_` |
| **X — secrets & mini-bosses** | `tools/regions/50_secrets.py`, `web/src/24_secrets.js`, `art/gen_secrets*.py`, `art/secrets_*.py` | `tiles_hermit`, `tiles_ember`, `bg_hermit_*`, `bg_ember_*`, `sc_`, `oswin*`, `champion*`, `first_ember*`, `fx_sc_` |
| Integrator (main session) | everything else (`00_core`, `01_data`, `01b_gear`, `03_world`, `05_combat`, `06_enemies`, `07*`, `08*`, `09_main`, `10_story`, `11_cutscene`, `12_traversal`, `tools/rooms.py`, docs) | — |

Region modules in `tools/regions/` run inside `rooms.py`'s namespace **after** the base rooms, in file-name order. They
create rooms with `Room(...)` and may patch the specific old rooms listed as their anchor (§4) via `ROOM('R4')`.

## 3. Registries and hooks (all already in the engine)
### 3.1 Gear — `registerGear({weapons, arts, charms, spells, items}, iconSheet='ui_icons3')` (01b_gear.js)
Adds to `WEAPONS/ARTS/CHARMS/SPELL_DEFS/SPELLS/ITEMS` and creates the `w:<id>`, `art:<id>`, `sp:<id>`, `<charm id>` item
entries. Weapon fields: `name base sc{str,dex,fth} speed reach stam poise art desc` + optional `bleed fire holy armor rot boss frost`.
Icons: item icon name `w_<id>`, `a_<id>`, `s_<id>`, `<charm id>` looked up in the given icon sheet (G draws **all** new icons
into `ui_icons3` as named tags; see how `ui_icons2` is used in `08_ui.js`/`08b_menus.js`).
### 3.2 Hooks — `HOOKS.<name>.push(fn)` (00_core.js)
`update(dt)` each play frame after hazards · `render()` world space, after entities/projectiles · `renderTop()` screen
space, after lighting · `hud()` after the HUD · `enter(def)` after a room is built · `rest(shrine)` after resting ·
`derive(D, stats, skills)` mutate derived stats · `playerHurt(dmg, opt) → dmg` (opt has `src`, `rot`, your own keys like
`frost`/`burn`) · `strike(target, info, A)` after each player melee hit · `parry(src)` · `cast(spellId)` · `death()`.
**Only act when relevant** (e.g. check `room.def.biome === 'hoarfrost'`).
Player movement modifiers, set every frame from an `update` hook while relevant (they reset on room entry):
`P.fric` (accel multiplier, e.g. 0.25 on ice) and `P.pushVx` (px/s external push: wind, conveyors).
### 3.3 Spells and arts
`SPELL_CAST[id] = sp => {…}` (sp = spell power multiplier; use `fireProjectile`-style projectiles pushed to `projectiles`
with `owner: 'player'`, or direct `t.hit(...)` over `targets()`).
`ART_IMPL[id] = { fallback: [animTag, speed], release: frame, start(), update(dt, grav) }` — used when the player has no
`art_<id>` animation; `update` must eventually `setP('idle','idle',true)`. If W later adds an `art_<id>` tag the engine
plays it instead and still calls your `update`.
### 3.4 Rooms, spawns, tiles
- Prefer `spawns=[…]` on a Room over new map characters:
  `{t:'enemy', type:'frost_wraith', x, y}` (auto-respawns on rest, tracked as killed) · `{t:'boss', kind:'twins', x, y}` ·
  any other `t` you register in `SPAWNS[t] = (spec, {cx, fy, key, def, id}) => {…}`. Validation checks the cell exists,
  isn't solid and stands on ground (add flying enemy types to `FLYING`, or set `air: True`).
- Enemy types: add configs with `Object.assign(ENEMY, {...})` (see `01_data.js` for fields) and, for custom AI,
  `ENEMY_CLASSES[type] = class extends Enemy {…}`. Add attack tags to `ATTACK_TAGS` if you use the generic Enemy AI.
- Map characters for bosses/props (if you really need one): `ROOM_CHARS[ch] = ({x,y,cx,fy,key,def,id}) => {…}` and add
  `ch` to `GROUNDED` in your region module if it must stand on ground. Taken chars: `# = ^ v B ~ @ % | Y S N g F G L O T C i
  u l E I R s w c f a e K h p m n o y q d j H M Q V Z J W x r k b P A`.
- New tiles: `registerTile(ch, id, {solid, draw(ctx, tilesheet, px, py, x, y, R, backCtx)})` (03_world.js) — `draw` paints
  into the room's cached front layer once at build. Reserved chars/ids: Hoarfrost `_` `:` `,` ids 10–14 · Spire `;` `'` ids
  15–19 · Deep `*` `<` `>` ids 20–24 · Secrets `$` `&` ids 25–29 · Archives ids 30–34. Add solid chars to `SOLID` in your
  region module for validation. Hazard/physics behaviour for your tiles → your `update` hook (use `tileAt(tx, ty)`).
- Custom props: push objects into `props` with `type`, `x`, `y`, `anim: { update() {} }` (or a real Anim) and optional
  `update(dt)`, `draw()` (world space), `hurtbox()` + `onHit(info)` (makes it a strike target; `info.kind === 'heavy' &&
  info.charged` = fully charged heavy). Solid blockers: push `{x0,x1,y0,y1,on:()=>bool}` (px) into `room.dyn`.
- Biome: add `Object.assign(AREAS, { <biome>: { name, ambient, amb, tint } })` and `Object.assign(SCALES, …)`,
  `Object.assign(ROOTS, …)` (085_music.js) from your JS file. Tiles load from `tiles_<biome>` (48-tile layout, copy the
  index layout of an existing `art/gen_env*.py` tileset) and parallax from `bg_<biome>_far` / `bg_<biome>_mid`.
### 3.5 Bosses
- `BOSS_INFO[kind] = { name, hp, cinders, reward: [itemIds…], quote }`. Rewards are granted automatically on death
  (`rewards()` in BossBase). Use `MetaBoss` (07b_bosses2.js) + a `<kind>_meta.json` like Kalden/Sovereign, or subclass
  `BossBase` for special bodies. Spawn through a `{t:'boss', kind}` spawn with `SPAWNS.boss` (register one handler per kind:
  `BOSS_SPAWN[kind] = (cx, fy) => new …` — `SPAWNS.boss` is provided by the integrator and calls `BOSS_SPAWN[spec.kind]`
  unless `SAVE.flags['boss:'+kind]`). Put fog walls `F` at arena exits like existing boss rooms and set `boss='<kind>'` on the Room.
- Duo / multi-part bosses: give the boss object `parts = [...]`; each part needs `alive, x, y, face, hurtbox(), hit(info)`
  (and optionally `critable()`, `onCritStart()`, `boss: true`, `onParried()`). `targets()` then lists the parts instead of the
  boss. Keep aggregate `hp/maxHp/displayHp/name/phase/active/alive/dmgShown/dmgT` on the main object for the HUD bar; draw
  extra bars from a `hud` hook if you want.
- Boss damage to the player: `hurtPlayer(BOSS_DMG * dmg * NGP.dmg, dir, uniqueHitId, { parryable, src: this })`.
- One critical per stagger + `stanceImmune` 7 s are enforced by `BossBase.hit/stagger` — reuse them, don't reimplement.
### 3.6 Cutscenes (11_cutscene.js)
`BOSS_CUTS[kind] = b => [steps…]` (played automatically by `BossBase.activate()` the first time) and
`PHASE2_LINES[kind] = [speaker, line]` (call `bossPhase2Scene(this)` when you enter phase 2). Steps: `act(fn)`,
`say(who, text)`, `wait(s)`, `bossPan(b, dy, dur)`, `{pan:{x,y},dur}`, `{dur, tween:(dt,k)=>…}`, `holdAnim(b, tag)`.
The camera now holds after each pan. Keep intros ≲ 10 s.

## 4. World grid zones and anchors (global tile coords; rooms must stay inside their zone and not overlap anything)
Existing world: x −200…564, y −42…98 (print with `python3 tools/rooms.py --show`). Outdoor rooms have open sky on top —
never place a room directly on top of an outdoor room's top edge unless its bottom row is open to it.
| Region | Zone | Anchor (the only old room you may patch) | Gate |
|---|---|---|---|
| A Archives finale | existing A1–A6 (A6 now gy −46, h 18; new A7 at 324, −60, 24×14; test `tp('A6',3,14)`, `tp('A7',12,12)`) | `A6` (boss room exists, `boss='unwritten'`), `A1`–`A5` for loot placement only | — |
| H Hoarfrost | x 160…250, y −44…14 | `R4` east wall (col 39), rows 3–10 → first Hoarfrost room at gx 160 | a gap only crossable with Root Hook (`@` points) right at the start |
| S Tempest Spire | x 0…158, y −90…−2 (row y = −1 only directly above R3, x 96…119) | `R3` top wall (row 0) — open a few cells and build the connector upward | an ash veil `%` that needs Ember Dash, in the connector |
| D Burning Deep | x 150…400, y 84…170 (not overlapping M6 = x 212…247, y 84…97) | `M4` floor at local cols 41–43 (global x 289–291) → connector at gy 84 | a lava chasm only crossable by gliding (Gale Cloak) |
| X Hermit's Hollow | x −40…−1, y 0…14 | `R1` west wall (cols 0–1) | golden seal `$`: breaks only to a fully charged heavy |
| X Ember's Hollow | x 444…600, y 1…40 (not overlapping X1 = x 420…443, y 14…27) | `X4` floor (rows 11–13) | cracked floor `Y` (Cinder Slam); needs hook + dash inside |
| X Champion gauntlet | inside `R4` | `R4` (spawns/hooks only; H also opens R4's east wall) | optional |
| X Gilded Sentinel pair | inside `X3` | `X3` | optional |
| X Knight's Sword & Shield | new chest in `R2` | `R2` | — |

## 5. Id registry (use exactly these ids)
**Weapons** (class in brackets; ★ boss weapon with a `SIGS` signature effect implemented by W):
`frostbrand` [sword] Hoarfrost found · `pagecutter` [dagger] Archives found · `colossus_hammer`★ [great] Colossus ·
`glacier_maul` [great] Ice Golem Warden · `bell_hammer` [great] Bell-Ringer · `forge_cleaver` [great] Deep found ·
`stormfang`★ [spear] Cindervane · `stormvein` [katana] Spire found · `quarterstaff` [staff] Ashwright's shop ·
`windstaff`★ [staff] Oswin · `inkquill`★ [staff] The Unwritten · `lantern_staff` [staff] Head Librarian ·
`knight_shield` [shield] R2 chest · `twinborne`★ [shield] Frostbound Twins · `overseer_bulwark` [shield] Forge Overseer ·
`twinfangs` [twin] Hollow Champion · `first_ember`★ [mirror] The First Ember.
**Weapon arts:** `whirlwind` (quarterstaff) · `gale_vault` (windstaff) · `ink_mark` "Ink Seal" (inkquill) · `aegis`
(knight_shield) · `frost_aegis` (twinborne) · `shield_charge` (overseer_bulwark) · `magma_quake` (colossus_hammer) ·
`thunder_lunge` (stormfang) · `tolling_blow` (bell_hammer) · `twin_tempest` (twinfangs) · `echo` (first_ember) ·
`backstep_slash` (found in the Archives as `art:backstep_slash`).
**Spells:** `ink_seal` Archives found · `glyph_swarm` Unwritten · `glacial_wall` Hoarfrost found · `frost_nova` Twins ·
`magma_orb` Deep found · `chain_lightning` Spire found · `stormcall` Cindervane · `wind_ward` Oswin · `ember_echo` First Ember.
**Charms:** `c_bead` Oswin · `c_lantern` Head Librarian · `c_quill` Unwritten · `c_frostheart` Hoarfrost found ·
`c_aegis` Ice Golem Warden · `c_twin` Twins · `c_slag` Deep found · `c_brand` Forge Overseer · `c_core` Colossus ·
`c_feather` Spire found · `c_scale` Cindervane · `c_clapper` Bell-Ringer · `c_echo` First Ember.
(Effects: see the catalogue in `docs/EXPANSION_PLAN.md`. G defines every charm/spell/art + icon and implements effects that
live in general combat; effects tied to a region mechanic are implemented by that region's agent with `charmOn(id)`:
`c_frostheart` (H frost), `c_slag` (D lava/fire), `c_feather` (longer glide + second air dash — integrator), `c_lantern` (A dark rooms).)
**Boss kinds** (`BOSS_INFO` keys / `boss:` flags): `unwritten` · `ice_warden` · `twins` · `bellringer` · `cindervane` ·
`overseer` · `colossus` · `oswin` · `champion` · `sentinels` · `first_ember`. Existing: hound omen kalden vessel sovereign librarian.
**Rewards** (put these in each `BOSS_INFO.reward`): unwritten → `hook, w:inkquill, sp:glyph_swarm, c_quill` ·
librarian (A updates the existing entry) → `w:lantern_staff, c_lantern, shard` · ice_warden → `w:glacier_maul, c_aegis` ·
twins → `emberdash, w:twinborne, sp:frost_nova, c_twin` · bellringer → `w:bell_hammer, c_clapper` · cindervane → `gale,
w:stormfang, sp:stormcall, c_scale` · overseer → `w:overseer_bulwark, c_brand` · colossus → `slam, w:colossus_hammer, c_core` ·
oswin → `w:windstaff, c_bead, sp:wind_ward` · champion → `w:twinfangs, shard` · sentinels → `shard, emberstone` ·
first_ember → `w:first_ember, c_echo, sp:ember_echo` (+ sets flag `true_ending`).

## 6. Balance anchors
Existing boss HP: Gravetusk 1650, Head Librarian 1300, Kalden 2300, Vessel 2800, Morvain 3200, Sovereign 4400.
Existing enemies: grimoire 85 hp, ink_hound 120, lantern_monk 210, grave_knight elite. Suggested new: Unwritten 2600,
Ice Golem Warden 2200, Twins 1700 each, Bell-Ringer 2300, Cindervane 4200, Forge Overseer 2500, Colossus 5200,
Oswin 1500 × (0.8 + 0.035 × (level − 1)) (level-scaled), Hollow Champion 1600, Gilded Sentinels 1100 each, First Ember 5200.
Hard but fair: every big attack needs a readable telegraph (use the `telegraph` fx / glint), and a punish window.

## 7. Report back
End with: files created/changed, asset list, how to reach & test your content (room ids + `tp` coordinates), known
issues, and any `NEEDS:` patches for shared files.

## 8. Round 2 ownership (boss reworks, 2026-09-25)
M (Morvain): `web/src/07_bosses.js` (Omen), `art/gen_boss.py`, new `25_omen2.js`, `art/omen_*.py`, assets `boss*` `omen_*` `fx_om_*` `bg_omen_*`.
Z (Sovereign): `makeSovereign` in `07b_bosses2.js`, `art/gen_sovereign.py`, new `26_sovereign2.js`, `art/sovereign_*.py` `art/gen_sovbeast*.py`, assets `sovereign*` `sov_*` `fx_sov_*` `bg_sov_*`.
A additionally: `web/src/10_story.js`, new `tools/regions/60_oldsecrets.py`, new `web/src/27_oldsecrets.js`.
S/H/D/X/W: unchanged. Integrator: shrine/travel UI in `08_ui.js`, balance pass.
