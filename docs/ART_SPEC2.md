# Cinderhollow — Art Spec v2 (full-game expansion)

Everything in `docs/ART_SPEC.md` still applies (pipeline, style rules, meta format, previews,
facing RIGHT, feet on bottom row, visual verification with the Read tool). This file adds the
expansion. Never break existing assets' names, tags or frame order; the engine already uses them.

## Story & setting (use this to inform every design)
The **Pale Root**, a colossal golden world-tree, fell. Its sap (grace) curdled into ash-gold
**cinders**, and the land beneath (the Sunken Hallow) became a grave of hollowed knights. The
player is an **Ashbound** knight (dark steel, crimson cape) woken on the cliffs.
- **Sister Venn** — the shrine keeper: a slight, hooded woman in pale grey robes with a candle-lantern; secretly the Root's last seedling (faint gold veins at her hands and throat).
- **Old Ashwright** — the smith & merchant: broad, bald, soot-black leather apron, one gold prosthetic arm, works at an anvil.
- **The Hollow Scribe** — a tall, thin, robed skeleton-scholar with a quill and a floating book; sells spells.
- **Ser Kalden the Oathless** — a rival knight in battered white-and-teal plate with a tattered blue cloak; later consumed by rot (phase 2: rot-green growths, one arm swollen).
- **Morvain, the Ashen Omen** — existing boss.
- **The Pale Sovereign (Queen Ysolde)** — the corrupted heart of the Root: a towering, floating divine queen, white-gold porcelain skin cracked with gold light, a halo-crown of roots, wing-like branching roots behind her, long flowing robes. Phase 2: crown shattered, cracks burning, robes ablaze with gold-white fire.
New regions: **The Weeping Mire** (drowned rot swamp: sickly greens, murky teal water, dead trees, rot-orange fungal glow) and **The Pale Crown** (the top of the fallen tree: white-gold bark, glowing sap veins, a pale blue-white sky, drifting petals).

## A. Weapons — edit `art/gen_player.py`
Split the player into a **body sheet + weapon overlay sheets** with identical frames/tags:
- `player`: exactly as now but **without the Sword layer** (all other layers, frames, tags, durations unchanged; still 125 frames).
- `wpn_<id>` (64×40, same 125 frames, same tags, same durations): only the weapon, drawn with the same hand position/angle per frame that `draw_sword` uses now. The engine draws `player` then `wpn_<id>` at the same frame. Planted poses (`rest`) plant the weapon.
Weapons (id — look):
| id | look |
|---|---|
| `longsword` | the current sword, pixel-identical |
| `dagger` | short curved dagger (length ~10), bone grip |
| `greatsword` | huge slab blade (length ~25, 3px wide), rusted iron with gold runes |
| `spear` | long spear (shaft ~28 incl. head) — pole passes behind the hand, leaf blade |
| `katana` | slender curved blade (length ~20), pale moonlight-blue edge, wrapped grip |
| `maul` | long haft (length ~20) with a heavy block head glowing ember-orange at seams |
| `oathbrand` | holy straight sword (length ~19), white-gold blade with a faint glow line |
| `kalden` | Kalden's greatsword: black blade with teal-gold filigree (length ~22) |
Keep the whole weapon inside the frame (shorten slightly on extreme poses if needed).
Preview `art/previews/weapons.png`: one row per weapon over the idle/attack1/heavy/attack_up frames composited on the body.

## B. Icons & FX — `art/gen_ui2.py`, `art/gen_fx3.py`
`ui_icons2` (16×16, one tag per icon, one frame each):
weapons `w_longsword w_dagger w_greatsword w_spear w_katana w_maul w_oathbrand w_kalden`;
arts `a_crescent a_stormleap a_bloodstep a_cinderblade a_warcry a_moonwave`;
charms `c_crimson c_azure c_horn c_fang c_ember c_heel c_crest c_scholar c_greed c_grace c_thorn c_veil`;
spells `s_shards s_warmth s_lance s_rotmist`; items `i_emberstone i_tear i_bell i_letter i_crownkey i_rotseed i_herb`.
`ui_panel` (1 frame, 96×64): ornate dark panel with gold corner filigree (9-slice friendly: corners within 8px).
FX (`fx_<name>`, tag = name, same conventions as fx2):
| name | size | frames | notes |
|---|---|---|---|
| `moonwave` | 48×48 | 4 loop | pale-blue crescent wave travelling right |
| `stormleap` | 96×40 | 8 | ground burst of wind/ash rings, pivot bottom |
| `bloodstep` | 48×32 | 5 | crimson afterimage streak |
| `cinderblade` | 32×32 | 4 loop | fire aura licking (drawn around a blade), transparent core |
| `warcry` | 64×64 | 8 | expanding gold shout ring |
| `shards` | 12×12 | 4 loop | small violet-gold crystal shard, travelling right |
| `warmth` | 32×48 | 6 loop | gentle golden healing motes rising, pivot bottom |
| `lance` | 40×12 | 4 loop | frost lance travelling right, icy blue |
| `rotmist` | 64×48 | 8 | rot-green poison cloud, pivot bottom |
| `rot_hit` | 32×32 | 5 | green splatter |
| `holy_burst` | 64×64 | 8 | white-gold radiant explosion |
| `petal` | 8×8 | 4 loop | a falling white-gold petal |
Previews `art/previews/ui2.png`, `art/previews/fx3.png`.

## C. New enemies — `art/gen_enemies2.py` (same rules as section 4 of v1, meta required)
| name | frame | tags | description |
|---|---|---|---|
| `rot_hulk` | 64×56 | idle(4) walk(6) smash(10, active ~6–7) hurt(2) death(8) | bloated swamp brute, rot-green growths, huge fist |
| `bog_spitter` | 40×32 | idle(4) crawl(6) spit(9, spawn frame 5) hurt(2) death(6) | toad-like rot creature with an orange throat sac |
| `mire_witch` | 48×56 | idle(4) walk(6) cast(10, spawn frame 6) hurt(2) death(6) | hunched hag in moss robes with a lantern of rot |
| `gilded_sentinel` | 64×64 | idle(4) walk(6) sweep(12, two windows) thrust(9) hurt(2) death(8) | tall golden-armored halberdier, root growth through the armor |
| `root_spawn` | 32×24 | idle(4) crawl(6) burst(7: swells then explodes, active 5–6) hurt(2) death(6) | small glowing golden root creature |
| `sun_seraph` | 48×48 | fly(6 loop) cast(10, spawn frame 6) dive(6) hurt(2) death(6) | flying porcelain angel-husk with root wings; anchor = body center |
Projectiles: `proj_rotglob` 16×16 (`fly` 4 loop), `proj_lightorb` 12×12 (`fly` 4 loop).
Preview each `art/previews/<name>.png` + hitbox overlays.

## D. Bosses Kalden & Vessel — `art/gen_kalden.py`, `art/gen_vessel.py`
**Ser Kalden the Oathless** `kalden` + `kalden_p2` (96×72, face right, feet bottom, ~52px tall, human-scale knight much like the player but larger and more ornate; greatsword `kalden`).
Tags: `idle`(6) `walk`(8) `combo`(14: three slashes, three windows) `thrust`(9: lunging stab) `leap`(12: jump + plunging slash, drawn in place, active near the end) `guard`(2 loop) `backstep`(6) `rotburst`(12: phase-2 AoE, rot erupts from his body, active ~6–8) `stagger`(4) `death`(12).
Meta: attacks with windows, telegraph points, `rotburst` hit covering both sides.
**The Vessel of Rot** `vessel` (160×128): a mountainous grotesque of fused hollowed bodies and fungus, one huge maw, many arms, glowing rot-orange pustules. Tags: `idle`(6) `crawl`(8 loop) `slam`(10: arm slam, active 5–6) `sweep`(10: arms sweep low both sides) `spew`(12: vomits rot, spawn frame 6 at the maw) `stagger`(4) `death`(12). Meta + telegraph.
FX: `fx_rot_wave` (32×24, 4 loop, travelling right, rot ground wave), `fx_kalden_slash` (80×48, 4, teal-gold arc).
Previews + hitbox overlays.

## E. Final boss — `art/gen_sovereign.py`
**The Pale Sovereign** `sovereign` + `sovereign_p2` (192×160, faces LEFT natively is NOT allowed — face RIGHT; she floats: anchor = [cx, 150] i.e. her hem hovers ~10px above the floor). ~130px tall. Tags: `idle`(8 loop, hovering) `glide`(8 loop) `sweep`(12: branch-wing sweeps, two windows, low) `rain`(10: raises hand, spawn frame 6 — engine rains light from above) `lance`(10: summons a spear of light, spawn frame 6 at the hand) `nova`(14: gathers then radiant explosion around her, active 8–10) `summon`(10: roots erupt — engine spawns spikes) `stagger`(4) `death`(14: the crown cracks, she dissolves into petals & light).
FX: `fx_sov_nova` (160×120, 8, radiant ring), `fx_lightpillar` (24×120, 8, pivot bottom: thin warning line → pillar of light → fade), `fx_sov_lance` (64×16, 4 loop, travelling right).
Preview + hitbox overlay. This is the climax — it must look spectacular.

## F. Environment for new biomes — `art/gen_env2.py` (reuse `envlib.py` helpers)
Biomes `mire` and `crown`: `tiles_<b>` (48 frames, exact same index layout as v1), `bg_<b>_far` (512×216 opaque), `bg_<b>_mid` (512×216 transparent), mock room previews `art/previews/room_<b>.png`.
Mire: waterlogged dark peat & mossy stone, roots, dead trees in far layers, fog. Crown: pale white-gold bark (tiles look like bark/wood and gold sap), sky with enormous branches and clouds, drifting light.
Props: `prop_anvil` (48×32, `loop` 6: glowing anvil with sparks for Ashwright's forge), `prop_bell` (32×48, `idle`(1) `ring`(6): a great bell — rung to open the Crown), `prop_throne` (64×80, 1 frame `idle`: root throne at the Crown summit), `prop_grave` (24×24, 1 frame: knight's grave marker, for lore).

## G. NPCs, portraits & story art — `art/gen_npcs.py`, `art/gen_story.py`
NPC sheets (face right, feet bottom): `npc_venn` 32×48 `idle`(6 loop) `talk`(4 loop); `npc_ashwright` 48×48 `idle`(8 loop, hammering) `talk`(4 loop); `npc_scribe` 32×56 `idle`(6 loop, book floating) `talk`(4 loop); `npc_kalden` 48×48 `idle`(4) `talk`(4) `kneel`(1).
Portraits: `portrait_venn`, `portrait_ashwright`, `portrait_scribe`, `portrait_kalden`, `portrait_player` — 64×64, one tag `p`, 1 frame, framed bust on transparent, strong readable faces/masks.
Story panels (384×216 opaque, 1 frame, tag `p`), painterly pixel art illustrations:
`story_1` the Pale Root standing golden over a kingdom; `story_2` the Root falling, ash raining; `story_3` hollowed knights in the ruins, a lone shrine flame; `story_4` the Ashbound knight waking on the cliff (from behind, cape, the fallen Root on the horizon);
`story_end_kindle` the knight seated on the root throne, the tree glowing anew (bittersweet); `story_end_ash` the knight walking away at dawn as the last golden light fades and green shoots sprout from ash.
Previews `art/previews/npcs.png`, `art/previews/story.png`.
