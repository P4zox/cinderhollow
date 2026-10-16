# v17 Cold Forge: foes (agent FOES)

Code: `web/src/83_forge_foes.js` (ENEMY / ATTACK_TAGS / ENEMY_CLASSES / BIOME_TIER.forge / SPAWNS.cf_swarm, all added from
that file; its globals are `CFF*` / `cff*` / `Cff*` / `UF_*` -- AREA's 82_forge.js owns `CFA*` / `cfa*`).
Art: `art/gen_forge_foes.py` (driver) + `art/forge_foes_kit.py` (rig, poses, tweening, export), `art/forge_foes_unforged.py`
(+ `_moves.py`), `art/forge_foes_beasts.py` -> sheets `cf_smith`, `cf_wraith`, `cf_hulk`, `cf_mite`,
`cf_unforged_<type>` x14 (+ `_meta.json` each) in `assets/`. Rebuild: `python3 art/gen_forge_foes.py [--only cf_hulk,uf:katana]`.

## Ids, sizes, placement (for AREA)

All are ordinary `{"t": "enemy", "type": "<id>", "x": tx, "y": ty}` spawns standing on a floor tile (y = the row the feet
stand in, as for every other enemy).

| id | what | body (px, player = 31) | floor it needs | intended rooms |
|---|---|---|---|---|
| `cf_smith` | Hollow Smith | ~50 tall, hurtbox 14x46 | 6+ tiles of floor | Hall of Racks, Bellows Gallery, Long Flue (1-2 per room) |
| `cf_wraith` | Quench Wraith: lies as a ring of still water until you come within ~5 tiles | ~48 tall, 16x44 | a floor tile (cistern edge) | Quench Cisterns (2-3), Slag Chute, 1 in the Bellows Gallery |
| `cf_hulk` | Bellows Hulk | ~62 tall hunched, 26x60 (body 22 wide) | 10+ tiles of flat floor, 5 tiles headroom | Bellows Gallery (1-2) |
| `cf_mite` | Cinder Mite | ~8 tall, 13x8 | any floor | the Flue ledges, Hall of Racks, anywhere as a garnish |
| `cf_unforged` | elite, the Unforged | ~76 tall, 18x70; reach to ~90 px (whip 118) | a mini-arena: 22+ tiles flat, 6 tiles headroom | CF9 The Reject Pile, CF13 The Tempering Vault (as placed) |

Extra spawn kinds:
- `{"t": "cf_swarm", "x": tx, "y": ty, "n": 4}` -- a clutch of `n` Cinder Mites (1-8) around x on that floor.
- The Unforged's spawn may carry `"w": "katana"` to fix its weapon type (any of the 14 ids); otherwise it rolls one per
  room entry, never the type the player is holding. An Unforged that has been killed stays dead (normal `killed` rules).
- Biome tier: `BIOME_TIER.forge = { hp: 1.9, dmg: 1.55, cin: 1.7 }` (post-game, a notch above the Burning Deep / Starfall),
  added only if AREA hasn't set one.

## Design as built

**Hollow Smith** (hp 230, poise 30, stance 100). An empty smith's coat and leather apron walking on its own, a deep hood
with one dim cinder, heavy iron gloves; forge hammer in the near hand, long tongs in the far one.
- *hammer*: raised over the head (tell 0.3 s + 0.16 s hold, glint), one overhead blow with sparks. 40.
- *grab*: tongs thrust open and clacking (tell + clack), lunge. A roll's i-frames slip it, a block does **not**, it is not
  parryable. Caught: lifted on the hot tongs (glowing), three burns (12 each, 0.33 s apart), then hammered off them
  (0.75 x hammer) and flung. Staggering or hurting the smith drops you.
- *toss*: at 70-170 px, flicks a hot coal from the tongs in an arc; it burns on the floor for 1.2 s.

**Quench Wraith** (hp 130, poise 14). Cold steam risen from still water: a long faceless skull, a ribbed vapour body
narrowing into its pool, long arms with hooked claws. Cold white, no fire.
- Sleeps as a ring of still water (no hurtbox) until you come within ~84 px, then *rises* with a hiss.
- *hiss* (the tell: head back, jaw open, a jet of steam, 0.22 s hold) -> *lunge*: stretches flat and shoots ~60 px (art
  root + dash). 36, and the scald takes 22 stamina. *claw*: two swipes up close (26, -14 stamina).
- After a lunge it may *sink* into the floor and rise again 70-110 px from you.

**Bellows Hulk** (hp 640, poise 999 = never flinches, stance 175 = staggers in ~6-7 ordinary hits). Redesigned: a hunched
heroic carrier; the great bellows **is** its back (an iron shell hinged at the shoulders that swings open with each breath,
pleated leather between, a throat over the shoulder into the grate in its chest). Long arms, iron vambraces, a small
long-jawed masked head jutting forward.
- *slam*: both fists raised (tell 0.36 s + 0.22), slammed down; heat runs along the floor both ways (jump it). 60.
- *sweep*: a long backhand. 46.
- *blast*: it inhales (the shell swings wide, the core goes white), then empties the bellows through the grate: a cone of
  hot air 70 px ahead for 0.55 s (ticks of 12). Then it **vents** for 1.6 s: slumped, the core open, stance damage x1.8.
- **The stagger tell**: the core flares (light, sparks, a rising note) once its stance passes 60 %. Stagger = it drops to
  one knee, core blazing; critable for the fatality (any weapon type's fatality; tested with the longsword's).

**Cinder Mite** (hp 22). A sleek iron tick with ember seams. Crawls, leaps (curled) at you; a leap that connects clings
(up to three at once, drawn over the player) and burns 4 every 0.5 s until you roll (or it drops off after 4 s).

**The Unforged** (elite; hp 1000, stance 330, base damage 42 x move multiplier). A tall knight bound from failed and
broken blades: a soot-black core under plates that are all blades (stacked rib-blades on the chest, pauldrons, tassets,
greaves, vambraces with blade spurs), a mantle of broken blades hanging from the shoulders, a small blade-tip helm with a
single ember slit and a crown of broken blades, a hot heart showing between the ribs. Its weapon is a player type's
silhouette in the same failed black iron with a glowing flaw. One sheet per type (`cf_unforged_<type>`, 176x112, ~65
frames: idle 6, walk 8, hurt 4 = its stagger (it sinks to one knee, the heart flaring; held while critable), death 11 (the
body comes apart in chunks as the blades fall out of it into a heap), atk1-3). Forward travel in the art is root motion
(`meta.root`), so lunges carry the body and recoveries never slide back. On first sight: a toast naming
the weapon. Every move has a held tell (glint + light on the weapon); charged moves glow with heat.

| type | atk1 | atk2 | atk3 |
|---|---|---|---|
| longsword | overhead, rising cut, lunging thrust | charged two-handed overhead | parry stance: a blow into it fires the riposte thrust at once |
| katana | sheathed crouch -> iai dash through you | draw cut up, cut down, re-sheathe | moonlit iai: a crescent wave |
| greatsword | charged cleave (heat) + a floor shock | wide sweep from behind | shoulder tackle -> rising slash |
| maul | overhead smash, shocks both ways | two advancing spins (front and back) | earthshaker: leaps at you, slams on landing, shocks + ring |
| sns | shield up while it walks (frontal light blows glance off); slash, rising slash | shield charge (pushes) | guard (blocks; a blow into it fires the counter thrust) |
| dual | six-cut flurry | demon dash through you | three-turn cyclone; below 55 % HP: Demon mode (red eye, 22 % faster, shorter rests) |
| spear | double thrust | crouch, then runs at you spear-first, final thrust | hop back -> long lunge |
| staff | spin combo striking front and back | plants the staff, vaults, dive-kicks | low sweep -> rising launcher |
| whip | overhead lash (the tip deals x1.3) | grapple: a hooked lash drags you in, then a backhand | thunderclap: a whirl overhead, a crack that bursts on the floor |
| saxe | two blade cuts | morph slash (blade unfolds into the axe) -> always followed by | full release: axe slam + a burst |
| bow | short-range shot (burns out ~90 px) | deep draw (heat) -> three heavy arrows | arrow stab, hop back, shot; it keeps its distance |
| fist | jab, cross, hook | iron palm (wind-up, heat, pushes) | falling star: leaps, heel-drop on landing + floor shock |
| scythe | reap striking front AND behind | hook pull (drags you in) -> slash | hook step: comes apart, rebinds behind you, reaps both sides |
| bell | two tolling blows | wind-up toll (long glow) -> slam + a ring wave out to 86 px | perform: a blow on both sides + echo rings out to 64 px |

## Tests (tools/shots/v17/foes/)
- `uf.js` -> `out_uf/`: every type's three moves fire and land, a free fight, death to a heap; 140 rolls (13 types seen,
  never the held one), a spawn's `w` fixes the type. Montages `montage_uf_a.png`, `montage_uf_b.png`.
- `beasts.js` -> `out_beasts/`: smith (hammer, grab -> hold -> throw, toss), wraith (still -> rise, hiss, lunge, claw,
  sink), hulk (slam, sweep, blast -> vent; stance -> core flare -> stagger -> fatality; vent x1.8), mite (leap, cling),
  each dies; `cf_swarm` spawns. Montage `montage_beasts.png`.
- `rooms.js` -> `out_rooms/`: every forge room with AREA's placements, foes awake, no page errors.

Snapshots / sheets for review: `lineup_foes.png` (+ `_1x`), `lineup_unforged_a.png` / `_b.png` (the 14 types), the
montages above, and per-sheet previews in `art/previews/cf_*.png`.

## Open decisions
- Damage/HP are first-pass (tier forge 1.9 / 1.55 / 1.7): smith 40, wraith 36, hulk slam 60, Unforged 42 x up to 1.85.
  No balance bench yet against a late build -- the lead may want to scale them with the rest of the post-game.
- The Unforged's weapons are player-type silhouettes in its own failed black iron with a hot flaw (the concept sheet's
  open question "its own blades or a clean player weapon" -- this is the middle road).
- `BIOME_TIER.forge` is set here only if AREA hasn't set it.
