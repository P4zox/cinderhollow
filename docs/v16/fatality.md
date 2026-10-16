# v16 Fatalities — the framework (agent `fatality`)

This is the **contract** for the weapon agents. Framework code: `web/src/79_fatality.js`. Reference fatality (Longsword
"Ashen Verdict"): `web/src/79b_fatal_blade.js` + `art/player_v16_fatal_blade.py` (tag `ls_fatal`).

## 1. What the player gets

- **K on a critable foe** (exactly the foes / range J's riposte uses: `critTarget()` — bosses in `stagger` after its
  first frame, regular foes in `stagger` / `parried`, within `t.critRange || 34` px and 30 px of height) on the ground
  plays the fatality of the weapon type in hand. **J keeps the quick riposte.** Either one consumes the stagger
  (`t.onCritStart()` → `critDone`): once per stagger.
- K paths covered: the neutral K (`mvNeutral`), any direct heavy start (`mvNeutralK`, e.g. the guard's `startHeavy`), the
  shield's guard K (`mvGuardK`), K out of a parry (`mvParryUpdate`), and **K pressed during a move**: it latches even on a
  finisher (`mvRouted`) and the move's end leads into the fatality (`mvNext` → `'@K'`). In the air K stays the plunge.
- **Damage** ("very hurt"): AR = `outgoing(D.light, 1, 'melee')` × Riposte Mastery 1.5 × Executioner 1.3 × Dagger
  mastery 1.25 × `D.W.crit` (the riposte's multipliers). Bosses take **5.0 × AR**; a regular foe with HP ≤ **12 × AR** is
  **executed** (dies on the last beat), else takes **8.0 × AR**. The total is split over the steps' `hit` shares
  (normalised, so any weights work). Every beat is `t.hit({ dmg, poise: 0, dir, kind: 'crit', crit: true, fatality: true,
  melee: true, big: true, x, y })`: no stagger bonus, no bleed / fire / rot, **no strike hooks** (Boss Cores never proc;
  their colour tints the fatality). A boss's own armour still applies (the Ice Warden's shell takes 85%, as for the
  riposte). Riposte Mastery's 5% heal and Executioner's +30 stamina are paid at the end.
- **Invulnerable + uninterruptible**: `hurtPlayer` / `spikeHurt` / `killPlayer` refuse, HP can't drop (environment
  drains are undone each frame), and if anything sets another player state mid-fatality it is put back. A room change
  aborts it cleanly (`fatAbort`, `FAT.last.aborted`).
- **The hold**: the target's *owner* (the boss object — for duos / multi-body bosses the container whose `.parts` holds
  the target) gets an instance `update` stand-in for the whole fatality: no body of it moves, attacks or ticks. Its own
  update returns at the end and its stagger continues (each crit beat cuts the timer to ≤ 0.45 s, like the riposte). A
  boss that dies mid-fatality is released at once so its death plays. Measured recovery: 23–37 frames after the end.
- **Cinematic layer**: letterbox bars (17 px), the world darkened ~46% (terrain, props, other foes, the duo's other
  body: not the player, the target or effects), a vignette in the weapon colour, colour flashes, slow-mo / hitstop /
  shake / camera kick on the beats, a low boom, the name in the title font (Cinzel, spaced caps under the top bar,
  hairlines + diamonds), the camera leaning to the player/target midpoint, and a small **punch-in** (≤ 5.5%) done on the
  finished world image before the HUD (`presentWorld` wrapper): smooth when shaders are on, nearest otherwise; scaled by
  Settings › Screen shake. The GPU lighting stays 1:1, the HUD is untouched.
- **Move List**: every type's `combos` gets `{ name: 'Fatality', input: 'K on a staggered foe', desc }` (the desc names
  the registered fatality, a getter, so later registrations show up).
- **Fallback**: any type without a registration plays "Last Rite": its counter / first light tag, then its heavy tag
  (the big beat lands on that tag's own hit frame), crescent → aura blade → impact flash, ground shockwave, a pillar.

## 2. Registering a fatality

One file per weapon group, loaded after the framework: name it `web/src/79<letter>_fatal_<group>.js` (`79b_fatal_blade.js`
exists; e.g. `79c_fatal_heavy.js`, `79d_fatal_guard.js`, `79e_fatal_agile.js`, `79f_fatal_new.js` — anything sorting after
`79_fatality.js`).

```js
fatalityRegister('katana', {
  name: 'Moonsever',               // shown on screen (upper-cased)
  col: '205,225,255',              // weapon colour 'r,g,b' (or '#rrggbb'); a socketed Boss Core pulls it 70% toward its own
  tag: 'kt_fatal',                 // the player animation tag, time-mapped over the fatality (see §3)
  tags: ['kt_3', 'riposte'],       // fallbacks while the sheet doesn't have the tag yet
  dur: 1500,                       // total ms on the fatality clock (1100..1800). Slow-mo / hitstop stretch real time.
  cine: { dark: 0.5 },             // optional overrides of { bars: 1, dark: 0.5, vig: 1, zoom: 1 } (0 = layer off)
  steps: [ ... ],                  // §4, any order (sorted by `at`)
  draw(F, t) {},                   // optional, every frame: world space, GLOW layer, globalCompositeOperation 'lighter'
  drawLit(F, t) {},                // optional, every frame: world space, the lit layer (normal blending)
  tick(F, dt) {},                  // optional, every frame after the steps / anim / movement
  start(F) {}, end(F, aborted) {}, // optional
});
```

## 3. Animation

- `tag` (then `tags`, then `riposte` / `attack3` / `idle`) is chosen with `pHas`, set with speed 0 and **time-mapped**:
  the tag's frames (their ms in the sheet) are stretched over `[0, span)`, where span = `def.span` or the first `anim`
  step's `at` or `dur`. **Make the tag's total ms equal `dur`** and the frame times are the choreography exactly
  (`ls_fatal`: 1600 ms tag, `dur: 1600`).
- A step `{ at, anim: 'tag' | ['tag', 'fallback'], span }` switches tag; it runs until the next `anim` step (or `dur`).
- Art: `art/player_v16_fatal_<group>.py` (`blade heavy guard agile new`; the four others are stubs returning `[]`),
  loaded by `gen_player.py` after V15 (a failing module is skipped with a warning). Same `register(G)` contract as v13–v15:
  return `[(tag, fn, opts)]`; name tags `<prefix>_fatal` (`ls_fatal`, `kt_fatal`, `gs_fatal`, `ml_fatal`, `sh_fatal`,
  `tw_fatal`, `sp_fatal`, `st_fatal`, `wh_fatal`, `sx_fatal`, `bw_fatal`, `ft_fatal`, `scy_fatal`, `wb_fatal`); no
  `active` meta needed (damage comes from the beats). `python3 art/player_v16_fatal_blade.py` prints a frames/total check;
  preview with `python3 art/player_preview.py rows out.png ls_fatal:longsword`. Full build only via
  `tools/shots/v14/artbuild.sh`.

## 4. Steps (all fields optional except `at`, ms on the fatality clock; several keys may share one step)

| key | meaning |
|---|---|
| `move: { dx, dy, gap, through, tx, dur = 120, ease = 'out' }` | tween the player to an offset **relative to the start position, along the starting facing** (+ = forward; `dy` < 0 = up — any non-zero dy suspends gravity until it returns to 0). `gap: n` = stand n px before the target's near hurtbox edge (clamped to −10…+60 px from where you are); `through: n` = n px past its far edge (dash through); `tx: n` = n px from its centre. `dur: 0` = blink. Walls stop you (moveBody). |
| `anim`, `span` | §3 |
| `face: -1` / `'target'` | turn round / face the target (F.face; the move frame stays the starting facing) |
| `hit: share`, + `stop` `slow` `shake` `flash` `boom` `kick` `kickY` `zoom` `x` `hy` | a damage beat. Feel defaults: the last beat (the one completing the shares) `stop .13 shake 9 flash .45 kick 2.4 zoom 1`, others `stop .06 shake 4 flash .15 kick 1.2 zoom .45`. `slow` = seconds of the game's slow-mo (time × 0.35), `stop` = hitstop s, `flash` = weapon-colour screen flash 0..1, `boom` = the low boom, `kick` = camera kick px (feelKick), `zoom` = punch-in pulse 0..1. Impact point: the target's hurtbox centre, `hy` 0 (top) .. 1 (feet), `x` px along the facing from the player. |
| `shake`, `stop`, `slow`, `flash`, `boom`, `kick` without `hit` | the same feel with no damage (anticipation thuds, the plant) |
| `name: true` | show the fatality's name now (put it on the big beat) |
| `fx: 'name' \| fn(ctx, t, F, e)`, `o: {...}` | spawn a primitive (§5) or a custom draw (called every frame in the glow layer for `o.life` ms, default 400) |
| `target: { lift, knock, pin, drop, dur, ease }` | move a **small** foe (never a boss / boss part / elite / prop): `lift` px up, `knock` px away along the facing (both cumulative targets, tweened over `dur`), `pin` hold here, `drop` back to its start height. It lands by itself when released. |
| `ghosts: { dur, every, col, life, alpha }` | afterimage trail of the player for `dur` ms |
| `cine: { bars, dark, vig, zoom }` | change the cinematic targets from here on (they always fade out over the last 200 ms) |
| `sfx: 'name' \| fn(F)` | `sfx[name]()` or your own `tone()` / `noise()` |
| `call: fn(F, step)` | anything else |

Damage: shares are weights (`hit: 1` + `hit: 4` = 20% / 80%). A def with no `hit` deals everything at the end.

## 5. VFX primitives (`FATFX`; also `F.fx(name, o)` from code)

Common `o`: `anchor` = `'target'` (hurtbox centre, default) | `'ground'` (target's feet line) | `'top'` | `'player'`
(feet) | `'shoulder'` | `'start'` | `'tip'` (weapon tip now) | `fn(F) → {x, y}`; `dx` (along the facing) / `dy` offsets;
`follow: true` re-anchors every frame; `col` overrides the colour; `life` ms. Angles are **facing-space degrees**: 0 =
forward, −90 = up, +90 = down. Everything is crisp 1-px pixel art (scanline polygons, Bayer-dithered fades) drawn
additively into the glow layer (bright in the dark, feeds the bloom) and adds coloured lights.

| primitive | options (defaults) |
|---|---|
| `auraBlade` | huge translucent blade (fill + bright edges + fuller + guard + tip star, ghost outlines along the recent arc). `anchor 'player', dy -19, follow true`; `keys: [[ms, angle, alpha, ease], ...]` (or `a0 a1 dur`); `len 58` `w 7` `r0 5`; clipped at the start floor line unless `floor: false`; `ghosts: 0` off; `fade` ms; `a` alpha × |
| `slashLine` | thin line of light across a span: draws in (`grow 70`), holds flickering (`hold 380`), bursts into drifting fragments + sparks (`burst 260`). `len 340`, `ang 0` (tilt), `thick 1|2`, `sparks 22` |
| `crescent` | big arc smear round a pivot, sweeps open `a0` → `a1` (tail → head) in `grow 80`, lingers `linger 420` (dissolving), shatters to `shards 24` over `shatter 320`. `anchor 'player', dy -19`, `r 60`, `thick 16`, `sq 1` (y squash), `floor` clip |
| `shockwave` | expanding ellipse rings: `r0 4 r1 90 dur 420 rings 2 gap 90 sq 1 (0.22 = flat on the ground) thick 2` |
| `groundCrack` | molten cracks along the floor face, glowing → cooling to dark scars: `anchor 'ground'`, `len 60` per side, `branches 5`, `dur 1100`, `both: false` = forward only, `col` (default ember) |
| `pillar` | column of light from the floor up past the view: `anchor 'ground'`, `w 16`, `grow 70`, `dur 600` |
| `sparkBurst` | streak sparks (61_feel's pool): `n 16 spd 170`, cone: `dir` + `arc` |
| `emberBurst` | slow rising embers: `n 14 spd 60 rise 70 w 24 h 10 col` |
| `soulWisps` | wisps that rise out of the target (`from: 'target'`) or a ring (`from: 'ring', r 40`: a gathering) then stream into `to: 'tip' \| 'player' \| 'target' \| fn(F)`: `n 8 dur 800 rise 260 stagger 30` |
| `afterimage` | one player ghost now, or a trail with `dur` (+ `every col life alpha`) |
| `speedLines` | streaks rushing past: `anchor 'player'`, `n 12 dur 260 band [-40, 4] dir` |
| `impactFlash` | 4-point star + diamond core + light: `r 30 dur 160` |

Letterbox, world darken and the coloured vignette are not steps: they are the cinematic layer (`def.cine` / `cine` step).

Drawing helpers for `draw` / custom fx (all world space, current `g`): `fatLine(x0,y0,x1,y1[,clipY])`,
`fatPoly([[x,y],...][,clipY])` (convex), `fatRaster(x0,y0,x1,y1, fn(x,y)→palette index, pal)` (keep boxes ≲ 160×160 px),
`fatEllipse(cx,cy,rx,ry)`, `fatDith(x,y,a)`, `fatHash(x,y)`, `fatRng(seed)`, colours `fatMix(a,b,k)`, `fatHot(c)`,
`fatLite(c)`, `fatDeep(c)`, `fatAng(deg, face)`, `fatEase(name, k)` (`linear out in inout snap back`), particles
`fatSpark(x,y,vx,vy,col,life,gravity)`, `fatPart({...})`, `mvStar`, `mvAfterimage`, `addLight`.

## 6. The running fatality `F` (passed to draw / tick / fns; `FAT.on` while it plays)

`F.type def name t (ms) dur target owner boss (bool) small (movable) x y (player now) x0 y0 (start) face0 face col
(final rgb) base (weapon) core (Core rgb or null) unit (AR) total exec shareSum shares dealt beats`, methods
`F.fx(name, o)`, `F.tc()` → `{x, y, top, floor, hb}` of the target (last known if it died), `F.tip(mode)`, `F.shoulder()`,
`F.aura(alpha = .25, spread)` (keep it ≤ .15: it whitens fast), `F.light(x, y, r, k)`.
After the end: `FAT.last = { type, name, boss, exec, unit, total, dealt, beats: [{at, share, dmg, got}], aborted, dur }`.
Knobs: `FAT.zoomAmt` (0.055), `FAT_CINE`, `FAT_COL` (fallback colours), `FAT_BOSS / FAT_REG / FAT_EXEC`.

## 7. Quality notes from building Ashen Verdict

- Lights add up fast under the dynamic lighting: one big light per effect at k ≤ 0.8, or the boss whitens out.
- The darkened world makes thin 1-px lines read beautifully; prefer an outline + low-alpha fill to solid shapes.
- The boss's own hit flash (white) shows for a beat on every hit — keep beats few (2–4) and let the effects carry it.
- Anticipation → impact → follow-through → linger: the crescent / cracks / embers outliving `dur` are what make it feel
  heavy; effects keep running after the fatality ends.

## 8. Tests (`tools/shots/v16/fatality/`, `SHOT_HTML=web/dist/v16_<role>.html sh tools/shots/wm/run.sh <test> <outdir>`)

- `tests.js` — 27 checks with real inputs: K starts it, 8×AR / execute ≤ 12×AR / not above, once per stagger, J ripostes
  (and blocks a later K), mastery × executioner multipliers + heal / stamina, invulnerable (blow, projectile, spikes,
  killPlayer) + uninterruptible, target released, cinematic cleared, acts after, K during a move latches, the guard K
  path, room exit aborts, Move List rows, target lift / knock / land, every primitive + a custom fn draws.
- `types.js` — all 14 types: a staggered boss in a real arena (5.0×AR, released, recovers) + a staggered regular foe
  (8×AR), each ending idle. `arenas.js` — 11 real boss arenas incl. 3 multi-body (twins, executioners, sentinels):
  damage, invulnerability mid-fatality, the other body never moves, the boss recovers and attacks again.
- `snaps.js` (+ `window.__type`, `__arena`, `__at`, `__foe`) and `sheet.py <dir> <prefix> <out.png>`: before / during /
  after snapshots and a contact sheet. `ls_boss_sheet.png`, `ls_foe_sheet.png`: the Longsword.
