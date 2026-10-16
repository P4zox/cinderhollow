# Move help: combo hints and the Move List panel

The owner asked for two things:

> "can u add combo hint at right top so the player can see available moves after pressing, and a more polished weapon move description panel to list out all the moves."

Built in two new files: `web/src/80_movehelp.js` (engine, HUD, panel, setting) and `web/src/80b_movehelp_map.js` (the
path map). No mech file was edited. The only shared hook-ins are wrappers and one additive splice, all inside
`80_movehelp.js`:

| Hook-in | What it does |
| --- | --- |
| `SETTING_ROWS` (08b_menus.js) | One row spliced in just above "Save & quit" (earlier rows keep their indices) |
| `onPressHook` | Wrapped, to time the last press |
| `renderMasteryScreen` / `wmScreenInput` (74_arsenal9.js) | Wrapped: in list mode the panel takes over |
| `HOOKS.update` / `HOOKS.hud` / `HOOKS.enter` | Its own entries |

## How moves are recognised: paths

Every Move List entry (each type's `combos` in `76_mech_*.js` / `78_mech_*.js`, plus the Fatality row from
`79_fatality.js`) is mapped to a **path**: the move ids the player goes through, one step per key press, each step with
its key.

- **Automatic.** The entry's input (`J J K`, `air ↓J`, `L → J`, ...) is parsed and walked through the move rows' `next`
  routes from the type's neutral moves (`T.light[0]`, `T.K`, `T.air`, `T.down`, `T.up`, `T.rollJ`, `T.counter`). This
  resolves about 130 of the 325 entries.
- **Map.** Everything else is listed in `80b_movehelp_map.js` (`MH_MAP[type][entry name]`). That covers custom
  handlers (`onK`, `onI`, `rollK`), states ("Iai → J", "block → K", "Demon: K"), holds and releases, pauses and late
  presses, and contexts. Format:
  - `'KEY=node KEY=node'`, or `'>node KEY=node'` to start at an existing node.
  - The object form `{ p, ctx, names }` adds a context and per-step names. Arrays give alternatives.
  - `null` marks an entry that isn't a move: Keep charging ×2, Steered spin, Point-blank burst, Vented.
- **Nodes.**
  - Move ids (`P.state`), MV_STATES states (`vault`, `brace`, `grapple`) and `spdive`.
  - Pseudo nodes: `@roll` (the dodge and the 0.25 s after it), `@parry` (the parry stance and its counter window),
    `@counter` (`P.gcT > 0`), `@guard`, `@plunge`.
- **Contexts.** These gate an entry's first step:
  - Katana: sheathed / drawn.
  - Dual blades: demon / arch.
  - Martial arts: swift / iron, and the ember contexts.
  - Switch axe: axe / blade / sxfull / sxrel / sxlow.
  - Scythe: souls / nosouls.
  - Bell: notes. Whip: crack. Staff: momentum.

## The combo hint (HUD, top right)

- **Where you are.** Each frame the HUD works out your position from `mhNodes`:
  - the move playing;
  - the last move, for 0.3 s after it ends (the chain window);
  - the dodge, parry, counter window, guard or plunge.
- **What it lists.** The next step of every path through that node, plus the move row's own `next` routes. These are
  ordered J, K, I, L, with a plain press before its held, paused or late variant, and capped at 5.
- **When nothing is running.**
  - In the air: the air moves.
  - Within 1.6 s of a stance or mode change: that context's moves. Examples are Katana sheathed, Demon Mode, Iron
    style and Axe mode.
- **Labels.**
  - A finishing step shows the entry's name.
  - A middle step shows the name its move is known by, with a step counter ("Light chain 3/4"). That name comes from the
    first entry in the Move List's own order.
  - The heading names where you are ("LIGHT CHAIN 2/4", "DODGE", "SHEATHED", "AIRBORNE", "STAGGERED").
- **Rank.** Hints only show moves your Mastery rank has unlocked. Both the entry's rank and the destination move row's
  rank are checked.
- **Fatality.** A staggered foe in range (`fatReady()`) replaces the list with "K Fatality: <the type's fatality
  name>" (red-tinted, pulsing) and "J Riposte".
- **Look.**
  - A plate that fades out to the left, with a gold hairline and a diamond.
  - Key caps in the game's gold-on-dark style. Words such as hold, (pause), air, late and tap are drawn as small text
    before the key.
  - Keys right-aligned against the names, and rows that slide in over 0.1 s.
  - The labels are your bound keys (`keysOf`), and controller labels when a pad is active.
- **Timing.** The hint appears after a press and stays while the chain runs. It starts to fade 1.2 s after the chain
  window closes (measured: 1.52 s after the last move ends, gone at 1.83 s). It shows nothing if you haven't pressed
  anything in the last 3 s.
- **Placement.** It sits under the cinders (y 34, or 44 with the lost-cinders line). A pickup banner pushes it below
  the banner. It never reaches the boss bar, which is at the bottom.
- **When it is hidden.**
  - In menus, cutscenes and dialogue, and during a fatality.
  - While a region or area title card shows.
  - When Settings › **Combo hints** is Off. The setting is On by default and saved with the other settings.

## The Move List panel

It opens as before: Esc › Equipment › Weapon › mastery screen › Enter, or the MOVE LIST button. It now uses the full
panel area.

- **Header.** Weapon icon, name, ◂ ▸ type switch (clickable), "MOVE LIST · n moves · i / 14", mastery rank with pips,
  and a ◂ MASTERY back button.
- **List.** Entries are grouped under gold section headers with counts:
  - Light combos, Heavy & charge, Special (I) / stance, Dodge (L) follow-ups, Air, Mastery moves, Fatality.
  - Each row has a rank badge (II to V), the name, and the input drawn as key glyphs (with a SWIFT / IRON / AXE /
    DEMON chip where the input has that prefix).
  - Locked rows are dimmed. Names too long for a row ("Strike · Butt strike · Low sweep · Overhead") show as
    "Strike … Overhead".
  - The list scrolls with a scrollbar; clicking the scrollbar track jumps.
- **Detail pane.**
  - A stage with a looping animation preview of the whole path: idle, then each step's resolved tag at its own speed,
    lifted for air steps. It draws the player sheet plus the weapon overlay.
  - Under the stage, the path's keys with the playing step lit.
  - Name, then RANK or "LOCKED · MASTERY III" (the preview is dimmed when locked), the input glyphs, and the full
    description.
  - LEADS INTO: up to 3 next presses from the move at your rank.
  - Number chips from the final move row: DMG (n×dmg for multi-hits), POISE, STAM, HIT AT and RECOVER (seconds).
  - Entries without a real move show the weapon's idle pose.
- **Controls.**
  - Keyboard / controller: ↑/↓ moves through the entries (wrapping, scrolling to keep the selection's section header
    in view), ←/→ switches weapon type, Enter replays the preview, Esc goes back.
  - Mouse: hover selects, click selects, the wheel scrolls, the arrows switch type, and the back button closes.

## Tests

All run against `web/dist/movehelp.html`. Outputs are in `tools/shots/movehelp/`.

**`hints.js`** (`tools/shots/wm/run.sh`): 88 checks, all OK.

- All 14 types:
  - Every entry is mapped.
  - Every step of every path is offered at the step before: 267 / 267.
  - Rank I offers nothing above rank I.
- Live, with real inputs, every plain J/K chain of every type: 137 / 137 prefixes show their next press.
- Specifics:
  - Longsword: J J (with and without the rank II wheel slash), the roll, the air.
  - Katana sheathed, Iai → J.
  - Demon Mode and Demon K.
  - Iron style.
  - Switch axe morph.
  - Sword & shield guard.
  - Greatsword and scythe chains.
- Fatality on a staggered dummy for 3 types: shown, then gone when the stagger ends. Not shown out of range.
- The fade timing.
- Off setting, the settings row, menu hiding, and rebound keys (J → F shows "F").

**`panel.js`** (`tools/shots/shot.js`): 17 checks, all OK.

- Keyboard navigation and wrap, type switching.
- Mouse: row hover, row click, both arrows.
- Scrolling.
- Every entry of the 14 types renders (325 rows, no error).
- 306 / 306 entries with a real move have a preview; 278 show numbers.
- Esc order.
- The setting saved to localStorage, tested outside the Training Grounds sandbox.

**`snaps.js`**: the hint during real combos, in room C4 for 9 types, plus the air, the fatality, and rebound keys.

**Images.**

- `hint_montage.png`: the top-right crop of each shot.
- `panel_montage.png`: the panel for all 14 types, plus a locked entry.

## Notes and decisions for the owner

- The path map lives in its own file rather than as `id` fields in the 14 mech files. This keeps the mech files
  untouched (other agents own them), and the tests catch drift: an entry renamed in a mech file shows up as unresolved.
- Some entries share a key at the same spot. The bell's J J → I Swiftness and J J J → I Grand toll are an example. The
  hint shows the first in Move List order.
- Entries whose condition can't be read from the state show their move, without the condition. Examples are "near a
  foe" and the bow's "lv3 shot".
