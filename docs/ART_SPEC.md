# Cinderhollow — Art Spec (contract between art generators and the engine)

Game: side-scrolling soulslike metroidvania ("Elden Ring × Hollow Knight"). Internal
resolution **384×216**, 16px tiles, rendered with nearest-neighbour scaling. Dark,
desaturated world with **gold** (grace / cinders / holy) and **crimson** (blood, the
player's cape) accents. Region: *the Sunken Hallow*, ruins buried beneath the fallen
golden tree called **the Pale Root**. Original names only; no Elden Ring names or likenesses.

## Pipeline (mandatory)
- Every asset is produced by a Python generator in `art/gen_*.py` that draws cels with PIL
  and calls `asebuild.build(name, w, h, layers, frames, tags)` (see `art/asebuild.py`).
  That writes `art/<name>.aseprite` (layered, tagged) + `assets/<name>.png` (horizontal
  strip) + `assets/<name>.json`. Never hand-edit exported PNGs; rerun the generator.
- Look at `art/gen_player.py`, `art/gen_boss.py`, `art/gen_fx.py` for the house style and
  helpers (ramp shading, 1px dark outline `K`, limb segments, IK, layered parts).
- Style rules: 1px near-black outline (`(8,7,12)`), 3–5 step ramps, light from upper-left,
  no pure black fills, no anti-aliasing blur, no gradients except deliberate dithering.
  Keep silhouettes readable at 1× on a dark background. Pixel-clean: every pixel either
  fully opaque or fully transparent (FX may use a few alpha steps for glow).
- Verify every asset visually: render an enlarged preview (≥3×, on a mid-grey background,
  all tags as rows) to `art/previews/<name>.png` and LOOK at it with the Read tool. Iterate
  until it reads well. Animations must have clear anticipation → strike → recovery.

## Global conventions
- Creatures & player face **RIGHT** natively (the existing `boss`/`boss_p2` Morvain
  sheets face left; leave them alone).
- Creature frames: feet touch the **bottom row** of the frame; body horizontally near the
  anchor. The engine draws with the anchor point at the entity's feet.
- Frame durations (ms) are authored in the frames and used by the engine — time them well.
- FX sheets: centered pivot unless noted "bottom" (pivot = bottom-center).

## Creature meta (`assets/<name>_meta.json`) — required for every enemy/boss
```json
{
  "native": 1,
  "anchor": [ax, H],                 // feet point in frame coords (x usually body center)
  "hurtbox": [x, y, w, h],           // frame coords, facing right, the body
  "attacks": {                       // one entry per damaging tag
    "attack": { "active": [i0, i1],  // frame indices WITHIN the tag, inclusive
                "hit": [x, y, w, h] }// frame coords, facing right: the weapon sweep area
  },
  "spawn": {                         // projectile / fx spawn points (optional)
    "shoot": { "frame": i, "at": [x, y] }
  }
}
```
Write it from the generator (json.dump next to the sheet in `assets/`). Hit rects must
actually cover where the weapon is drawn on the active frames, reaching low enough to hit
a 10×26px player standing on the same floor.

## 1. Player additions — extend `art/gen_player.py` (64×40, anchor x=28, faces right)
Keep all existing tags and frames unchanged in look. ADD these tags:
| tag | frames | notes |
|---|---|---|
| `attack_up` | 6 | upward slash overhead, arc above head (active ≈ frames 2–3) |
| `attack_down` | 5 | airborne downward stab/pogo, sword pointing straight down below feet (active 1–3) |
| `air_attack` | 5 | horizontal cut while airborne, legs tucked |
| `cast` | 8 | off-hand raised forward, glowing gold at hand frames 3–5 (projectile spawns frame 4) |
| `parry` | 6 | quick guard-flick with sword/gauntlet, frames 1–2 are the "active" deflect pose |
| `riposte` | 8 | big lunging stab + twist, the critical-hit animation |
| `wall_slide` | 2 | clinging to a wall on the RIGHT side of the frame (facing the wall), sliding (loop) |
| `double_jump` | 4 | flip/tuck with cape swirl |
| `rest` | 4 | kneel with sword planted (hold last frame) |
| `rise` | 4 | stand up from kneel |
Preview: `art/previews/player.png`.

## 2. FX additions — new generator `art/gen_fx2.py` (existing fx_* stay as-is)
| name | size | frames | notes |
|---|---|---|---|
| `fx_ashbolt` | 32×16 | 4 loop | player's golden-ash sorcery bolt, travelling RIGHT, bright core + trailing embers |
| `fx_ashbolt_hit` | 32×32 | 6 | bolt impact burst |
| `fx_flame_ring` | 96×48 | 8 | "Emberburst" AoE: ring of fire erupting from ground, pivot bottom |
| `fx_pogo` | 32×24 | 4 | spark burst below feet on a successful down-strike |
| `fx_slash_up` | 48×48 | 4 | upward crescent above the player, pivot = its bottom-center |
| `fx_slash_air` | 48×32 | 4 | horizontal crescent, travelling right |
| `fx_riposte` | 64×48 | 6 | crimson critical burst with white core |
| `fx_levelup` | 64×64 | 10 | golden pillar/burst around the player, pivot bottom |
| `fx_cinder` | 8×8 | 4 loop | small golden cinder mote (the currency pickup) |
| `fx_death_ash` | 48×48 | 8 | enemy dissolving into ash & gold motes (pivot bottom) |
| `fx_wall_dust` | 16×16 | 4 | dust puff for wall slide/wall jump |
| `fx_bleed` | 48×48 | 6 | bleed proc: crimson spray burst |
| `fx_grace_glow` | 32×32 | 6 loop | soft golden guidance light (used on shrines & items) |
| `fx_parry_flash` | 48×48 | 5 | white-gold star flash on successful parry |
Preview: `art/previews/fx2.png`.

## 3. UI icons — `art/gen_ui.py` → sheet `ui_icons` (16×16 per frame, ONE tag per icon, 1 frame each)
Skill nodes: `keen_edge`, `fourth_strike`, `charged_arts`, `riposte_mastery`, `bloodthirst`,
`ash_bolt`, `sunspear`, `azure_thrift`, `emberburst`, `soul_siphon`,
`quickstep`, `iron_flask`, `steadfast`, `last_stand`, `second_wind`.
Items/HUD: `flask_red`, `flask_blue`, `cinder`, `shard` (skill point), `key`, `talon` (wall-jump
relic), `wings` (double-jump relic), `map`, `shrine`, `skull`, `lock`.
Also a sheet `ui_frame` (single 1-frame tag `frame`, 24×24): ornate gold-on-black node frame
with transparent 16×16 center. Preview: `art/previews/ui.png`.

## 4. Enemies — `art/gen_enemies.py` (one sheet + meta per enemy, face right)
| name | frame | tags (frames) | description |
|---|---|---|---|
| `hollow_soldier` | 48×40 | idle(4) walk(6) attack(8: 3 windup, delayed hold, 2 active, recovery) hurt(2) death(6) | rotted foot-soldier, dented helm, broken longsword, ragged tabard |
| `shield_warden` | 56×48 | idle(4) walk(6) guard(2 loop) bash(9) hurt(2) death(6) | armored brute with tower shield + short spear; `bash` = shield shove then spear thrust (two active windows ok: use the thrust) |
| `rot_crawler` | 40×24 | idle(4) crawl(6) lunge(7) hurt(2) death(6) | low, fast many-legged rot bug with a glowing orange sac |
| `gloom_wisp` | 40×32 | fly(6 loop) dive(6) hurt(2) death(6) | flying skull-moth / wraith, frames floated (NOT feet on bottom: anchor = body center, set anchor accordingly) |
| `hollow_archer` | 48×40 | idle(4) walk(6) shoot(9, arrow released frame 6) hurt(2) death(6) | hooded skeletal archer with longbow |
| `ember_acolyte` | 48×48 | idle(4 loop, robe flicker) walk(6) cast(10, fireball spawns frame 6) blink(6: vanish into embers) hurt(2) death(6) | robed cultist with burning censer-staff |
| `grave_knight` | 72×56 | idle(4) walk(6) combo(12: two big swings, active ~3–4 and ~8–9) slam(10: overhead ground slam, active 6–7) hurt(2) death(8) | elite: towering knight in black-gold plate with a greatsword |
Projectiles (face right, centered): `proj_arrow` 16×8 (1 tag `fly`, 2 frames), `proj_fireball`
16×16 (`fly` 4 loop). Each enemy's meta must include `attacks` for its damaging tags and
`spawn` for shoot/cast. Preview each as `art/previews/<name>.png`.

## 5. Mid-boss — `art/gen_hound.py` → `hound` sheet + `hound_meta.json`
**Gravetusk, the Rootbound Hound**: a huge ash-grey wolf-boar, ribs of the Pale Root's
golden roots grafted through its back, glowing gold eyes. Frame **160×96**, faces right,
feet on bottom row. Must look completely unlike Morvain (quadruped, low and wide).
Tags: `idle`(6) `prowl`(8 loop) `bite`(8: rear back, snap forward) `pounce`(10: crouch, leap arc
drawn in place, land — the engine moves it) `sweep`(9: whole-body tail/root sweep behind+front)
`howl`(10: rears up, root-glow flares; engine spawns root spikes) `charge`(4 loop, full sprint)
`stagger`(4) `death`(10). Phase 2 variant sheet `hound_p2` (same frames/tags, roots burning
orange-gold, embers). Meta with attacks for bite/pounce/sweep/charge.
FX: `fx_root_spike` 24×64 (8 frames: telegraph glow crack in ground → spike erupts → retracts;
pivot bottom), `fx_bite` 48×32 (4). Preview `art/previews/hound.png`.

## 6. Environment — `art/gen_env.py`
Three biomes: `ramparts` (ash-grey stone ramparts under a dusky amber sky, the Pale Root
visible far away), `catacombs` (dark earthen crypt, bone niches, invading golden-brown roots,
teal candle-light), `cathedral` (sunken pale-marble cathedral, gold filigree, still water,
shafts of light). Each biome needs:

**Tileset** `tiles_<biome>`: 48 frames of 16×16 (a single tag `all`), exact indices:
- 0–15: solid terrain; index = bitmask of which neighbours are AIR: N=1, E=2, S=4, W=8.
  Exposed edges get the top-lit surface lip (N) / shaded edges; 0 = deep interior (darker, low detail).
- 16–31: same 16 masks, alternate variant (cracks, moss, roots, inset brick) for variety.
- 32/33/34/35: one-way platform left end / middle / right end / single (thin, ~5px tall at top).
- 36: floor spikes/thorns (hazard) pointing up, sitting on the tile bottom. 37: ceiling spikes pointing down.
- 38–41: background wall tiles (non-solid, clearly darker/lower contrast than terrain).
- 42–45: transparent decoration overlays: hanging chain, hanging roots, candle cluster, bone pile.
- 46: breakable (secret) wall: looks like 0 with a subtle crack.
- 47: rubble/grass top tuft overlay (transparent, sits on top of a surface).
**Parallax**: `bg_<biome>_far` 512×216 opaque (sky/far architecture, horizontally tileable),
`bg_<biome>_mid` 512×216 transparent except silhouettes of arches/pillars/roots in the lower
2/3 (tileable). 1 tag `loop` each (may be 1 frame, or a few frames of subtle animation).

**Props** (face right, bottom-anchored, centered):
| name | size | tags |
|---|---|---|
| `prop_shrine` | 48×64 | `unlit`(1) `kindle`(6) `lit`(6 loop) — grace shrine: stone plinth with a gold-flame brazier + a small kneeling statue |
| `prop_fog` | 32×80 | `loop`(6) golden translucent fog wall (boss door) |
| `prop_gate` | 16×64 | `closed`(1) `opening`(6) `open`(1) iron portcullis |
| `prop_lever` | 16×24 | `off`(1) `pull`(4) `on`(1) |
| `prop_urn` | 16×24 | `idle`(1) `break`(5) |
| `prop_lantern` | 16×32 | `loop`(4) hanging lantern, flame flicker |
| `prop_remnant` | 24×32 | `loop`(6) the player's dropped cinders: pulsing crimson-gold wisp |
| `prop_item` | 16×16 | `loop`(6) glowing item orb |
| `prop_chest` | 32×24 | `closed`(1) `open`(5) |
| `prop_elevator` | 48×16 | `idle`(1) stone lift platform |
Preview everything to `art/previews/env_<biome>.png` / `art/previews/props.png`, and additionally render a
mock room screenshot per biome (384×216, tiles assembled into a small room over the parallax) to
check the tiles tile seamlessly and read against the background.
