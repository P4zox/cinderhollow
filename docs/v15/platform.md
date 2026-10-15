# v15 platform: five new weapon types (platform agent)

The game now has **14 weapon types**: the nine, then the five from WEAPON_REVAMP.md Part C. Each new type works like the
nine everywhere: you can pick it at New Game, change to it at a shrine, temper it at the Ashwright, and it has its own
Mastery ranks, mastery screen and Move List, Training Grounds row and skill-tree alcove.
Each one has a **skeleton moveset** (one file per type) that the moveset agents replace.

## The five

| Type | id | prefix | Weapon (id) | Diff | Default art (locked) | Spec | Skeleton fallback tags |
|---|---|---|---|---|---|---|---|
| Switch Axe | `saxe` | `sx_` | **Gravegrinder** (`gravegrinder`) | ★★★★★ | Magma Quake | C1 | `gs_*` |
| Close-range Bow | `bow` | `bw_` | **Ashstring Recurve** (`ashstring`) | ★★★ | Backstep Slash | C2 | `sp_*` |
| Martial Arts | `fist` | `ft_` | **Penitent's Knuckles** (`penitent_knuckles`) | ★★★★ | Bloodstep | C3 | `dg_*` |
| Scythe | `scythe` | `sc_` | **Requiem** (`requiem_scythe`) | ★★★ | Reap | C4 | `sc_*` (the v9 scythe tags) |
| Warbell | `bell` | `wb_` | **Dirgebell** (`dirge_bell`) | ★★★ | War Cry | C5 | `ml_*`, `gs_air/down` |

- **Weapon stats** (in `web/src/77_types15.js`): every weapon has base attack 42, like the nine. Scaling letters:
  Gravegrinder B/C, Ashstring E/A, Knuckles C/B, Requiem C/C/E (+10 bleed), Dirgebell A/–/D.
  The Gravegrinder and the Dirgebell get `armor` (their heavies don't flinch, like the Greatsword's and the Maul's).
  The balance agent should re-tune these.
- **Default arts:** these are existing arts, picked to fit each weapon: Magma Quake (the grinder splits the ground),
  Backstep Slash (hop back, then lunge in), Bloodstep (a martial dash-through), Reap (the scythe's own soul-harvest art),
  War Cry (the bell's rallying buff). A moveset agent may make a new art later; if it does, register it in ARTS and set
  `WTYPE_INFO[type].art` and `WEAPONS[id].art`.
- **Weapon art (overlays `wpn_<id>`):** drawn by `art/player_v15_weapons.py`, in the same blade-space style as gen_player:
  - **Gravegrinder:** a switch axe in axe mode. The sword blade is folded along the haft, the crescent axe head has
    chain-teeth on its edge, and an ember phial sits below the head.
  - **Ashstring Recurve:** a recurve bow held at the grip, with an arrow nocked along the swing line (the arrow's head is
    the "blade").
  - **Penitent's Knuckles:** spiked iron knuckles over the fist, with wrist wraps trailing back. Only the main hand is drawn.
  - **Requiem:** a black haft with violet bands, and a bone-silver blade with a violet edge. It uses the v9 scythe haft
    path.
  - **Dirgebell:** a black-iron war-bell on a chain-wound haft, mouth toward the foe. It uses maul style: when planted, it
    rests its head on the floor.
- **Icons:** `w_<id>` come from `art/gen_ui15.py`, which draws each icon from the weapon's own shape. They are written to
  `assets/ui_icons15.*`, and 77 pushes `ui_icons15` onto `ICON_SHEETS`.

## Files

**New**
- `web/src/77_types15.js` adds all the data to the tables of 74_arsenal9 (nothing is redeclared):
  - the five WEAPONS / ITEMS entries (via `registerGear`);
  - `WTYPE_INFO`, which now also has a `short` label for every type;
  - `WTYPES` and `MOVESETS_TYPES` (the five are pushed onto both);
  - `WEAPON_TYPE`, `WEAPON_CLASS`, `ART_CLS` (art pose class), `FEEL_CLS_W` (hit weight), `WS_CLS` (whoosh sound),
    `WB_CLS_LABEL`.
- `web/src/78_mech_{saxe,bow,fist,scythe,bell}.js`: the skeleton movesets. Each file is owned by its moveset agent.
- `art/player_v15_weapons.py`: the five weapon shapes, the smear colours, and the `MOVE_CLASS` prefixes.
- `art/player_v15_{saxe,bow,fist,scythe,bell}.py`: stub tag modules, each with `register(G)` returning `[]`. Each is owned
  by its moveset agent.
- `art/gen_ui15.py`: the icons. Assets: `assets/ui_icons15.*` and `assets/wpn_{gravegrinder,ashstring,penitent_knuckles,requiem_scythe,dirge_bell}.*`
  (+ their `.aseprite` sources).
- Tests: `tools/shots/v15/platform/{types,ui,saves,smoke}.js`. Run them all with `run_all.sh`.

**Shared files edited** (small, additive)
- `art/gen_player.py`: the v15 hook. It runs right after the V14 loop and before `ANIMS`; `+ V15_MOVES` is added to
  `ANIMS`. In order, the hook:
  1. installs `player_v15_weapons`;
  2. loads `player_v15_<type>` in the fixed order saxe, bow, fist, scythe, bell;
  3. skips with a warning any module that fails to load.
- `web/src/74_arsenal9.js` (UI scales to any count):
  - the New Game strip: pitch `min(36, 372/n)`, short labels when n > 9;
  - Change Weapon: compact rows (`wchangeRows`, `wchangeRowH()`) when n > 9;
  - the Esc mastery list: row height `min(16.8, 151/n)`;
  - Training rows and the "nine" strings now count `WTYPES.length`.
- `web/src/58_skilltree_ui.js`: when there are more than 10 types, the Mastery page shows 7 alcoves per row
  (alcoves 34 px wide instead of 46), and the alcove header falls back to the short name.
- `web/src/08b_menus.js`: the forge's rows are `min(14.4, 134/n)` high.
- `web/src/09_main.js`: the Armory banner counts the weapons. `web/src/65_training.js`: one description string.
- Tests updated from 9 to 14 types: `tools/shots/ws/{select,switching,mastery,migration,loot}.js`, `tools/shots/wm/mech.js`.
  The unlock check is strict for the nine only, so the skeletons pass; the moveset agents' tests cover their own types.

Saves need no new field. `SAVE.weapons` gains the five ids at +0, filled in by 74's `loadGame` for any wv-9 save, and
mastery is keyed by type id. `wv` stays 9.

## UI with 14 types (screenshots: `tools/shots/v15/platform/out/ui/`)

| Screen | 9 types | 14 types |
|---|---|---|
| New Game strip | 26 px cells, 36 pitch | 22 px cells, 26 pitch, short labels (G. Sword, Shield, S. Axe, Fists …) |
| Shrine › Change Weapon | 18.6 px rows | 12.1 px rows: icon, name +lv, XP bar, rank pips, a gold diamond on the weapon in hand |
| Esc › Weapon Mastery | 16.8 px rows | 10.8 px rows (Move List unchanged; ←→ cycles all 14) |
| Skill tree › Mastery | 5 + 4 alcoves | 7 + 7 alcoves, still at full zoom (the page fits the field) |
| Ashwright forge | 14.4 px rows | 9.6 px rows |
| Training › Weapon tab, Inventory | already scroll / grid | unchanged |

`ui.js` checks the layout numbers against each panel and hovers the mouse over every row and cell of every list, and
each one selects. Clicking the Warbell on the strip starts the journey with it; clicking Martial Arts at the shrine
takes it up.

## How a moveset agent plugs in

1. **Moves:** replace the body of `web/src/78_mech_<type>.js` with your table: one `mvRegister('<type>', T, moves)`.
   This is the same contract as `76_mech_*.js` (read `75_moves.js` and one mech file). Nothing else in the game needs
   to change: equip, mastery gating, the Move List (`T.combos`), the unlocks screen (`T.unlocks`) and the preview loop all
   read from your table.
   - **T (type) hooks:**
     - the move ids: `light[]`, `K`, `up`, `air`, `down`, `light0()`;
     - input hooks: `onJ/onK/onAirK/onI/onL(ax)`, `rollJ` (id, `{id,...}` or fn), `rollK(g)`, `counter()`, `airRise()`;
     - defence: `dodge` (obj or fn), `dodgeUpdate`, `dodged0/dodged`, `parryUpdate`, `guardUpdate`, `guardK`,
       `guardCost`, `blockPose`, `blocked`;
     - damage and stats: `plunge`, `speed(A)`, `started(A,o)`, `hitMod(c)`, `poiseMod`, `onHit`, `hurt(c)`,
       `regenMul`, `walkMul`, `idleTag`, `healSpeed`, `healWalk`;
     - per-frame and drawing: `landed`, `tick/tickAll`, `render/renderAll`, `hud(x)`, `interrupted`;
     - the lists: `unlocks[]` ({rank, id, name, input, desc}) and `combos[]` ({rank, name, input, desc}).
   - **Move rows:**
     - animation and timing: `tags[]` (your tag first, then fallbacks), `wind`, `total`, `step`, `fin`, `commit`,
       `kind:'heavy'`;
     - damage and cost: `dmg`, `hits[]` + `gap`, `poise`, `stam` (number or fn);
     - hit box: `reach`, `back`, `spin` + `backReach`, `ys`, `box`;
     - movement: `lunge`, `lungeFn`, `lungeLead`, `dash`;
     - aerial: `up/air/down`, `hang`;
     - stances: `loop`, `noHit`;
     - gating: `rank`, `can(o)`;
     - routes: `next:{J,K,I}` (an id, an `{id,…}` object, `'@J'`, or a fn(q, A));
     - defence and effects: `inv:[a,b]`, `armor`, `dmgTaken`, `launch`, `reel`, `slam`, `counter`;
     - hooks: `on:{start, update, swing, hitStart, hit, end}`, `mod(c)`, `move(dt,…)`.
   - **Helpers:** `mvStart`, `mvHas(rank)`, `mvGain(why)`, `mvStrikeAt`, `mvShockwave`, `mvLater`, `mvBurn`,
     `mvHudBar/Pip/Ring`, `mvHudX()`, `mvAura`, `mvSpark`, `mvAfterimage`, `mvStar`.
2. **HUD:** draw your gauge in `T.hud(x)`, where `x = mvHudX()` (the column right of the stamina bar). Use y ≈ 18–26,
   like the Dual Blades' demon gauge (`76_mech_agile.js`). The engine only calls it while your type is in hand. The
   gauges per type are the Switch Gauge, the bow's charge level, the martial style + Flow pips, the scythe's souls and
   the warbell's 3-note staff.
3. **Animations:** return your tags from `art/player_v15_<type>.py` `register(G)` using the v13 contract (`tm()`-style
   timing like `player_v14_reach.py`; opts `active`, `hits`, `both`, `up`, `down`, `hit`, `fxat`, `kinds` …). Then:
   - Name tags with your prefix, so `MOVE_CLASS` measures their hit boxes with your weapon.
   - To restyle your weapon (the switch axe's sword mode, a second hand for the fists …), set `G.WPN['<id>']` /
     `G.SMEAR['<id>']` inside your `register`. It runs after `install`.
   - Preview without building: `python3 art/player_preview.py rows out.png sx_1:gravegrinder`.
   - Full build: `tools/shots/v14/artbuild.sh` (locked; it builds the v15 modules too).
4. **Mastery:** rank-gated moves set `rank: n`. `masteryRank('<type>')`, XP gain and rank-up banners are shared.
   `wmEquip('<type>')` equips the type (it is what the shrine, the Training Grounds and the test prelude's
   `W().reset('<type>', rank)` use).
5. **Tests:** the WM prelude works for the new types as it does for the nine:
   `W().reset('saxe', 1); W().dummy(26); W().tap('attack')`. Copy `tools/shots/v15/platform/types.js` for a start.

## Engine limits and gotchas

- **One scope:** all `web/src/*.js` files share one function scope, so every top-level name must be unique.
  - `sc*`/`SC_*` are taken by 24_secrets. Scythe: use `scy`/`SCY_`.
  - `wb*`/`WB_*` are taken by 60_wbal. Warbell: use `bel`/`BEL_`.
  - `sx`, `bw` and `ft` are free.
  - Prefix your `P.<field>` state the same way (e.g. `P.sxGauge`, `P.bwLv`, `P.ftStyle`, `P.scySouls`, `P.belNotes`).
- **Don't edit `75_moves.js`.** If a hook is missing, wrap it from your own file, or ask the platform/lead.
- **Input queue and air rules** (A1): one queued press plus up to two of the same button; a press that would start a new
  chain only counts in a finisher's last 120 ms; at most 2 air attacks per jump; L cancels after the hit unless the
  move is `commit`.
- **The `@`-routes:** a route of `'@J'` restarts the chain (it is not a continuation). A queued up+J only plays `T.up`
  when the J route is a string; for function routes, handle `q.up` yourself (see `lsUpJ` in `76_mech_blade.js`).
- **Art budget:**
  - Every new tag adds frames to `player.png` **and to all 14 overlays**. Today that is 2091 frames, about 28 MB for a
    test HTML; the release build is split into chunks.
  - Frames are 64×40, feet on row 39, and the weapon must stay inside the frame (`draw_weapon` shrinks long weapons to
    fit).
  - A full artbuild takes about 2–6 min (it waits on a lock).
- **The Scythe reuses the v9 `sc_*` tags.** Their hit boxes are now measured with the Requiem, so a moveset that keeps
  them gets the new reach. New scythe tags must not reuse those seven names.
- **Fist overlay:** only the main hand's knuckles are drawn. The off hand is the body sprite's gauntlet.

## Decisions for the owner

- **Weapon names:** Gravegrinder, Ashstring Recurve, Penitent's Knuckles, Requiem and Dirgebell.
- **Old saves:** pre-revamp saves (before the nine) still turn the old scythes into the Greatsword, as the revamp
  contract decided. They could map to the new Scythe instead; it is a one-line change in `WM_OLD_TYPE`.
- **Default arts are borrowed** from existing ones (see the table above). Bloodstep and War Cry are default arts again,
  so the migration keeps them in old saves' art lists.
