# v15 Scythe: the reaper (scythe agent)

Weapon: **Requiem** (`requiem_scythe`), type `scythe`, ★★★. Spec: WEAPON_REVAMP.md C4. Code: `web/src/78_mech_scythe.js`.
Art: `art/player_v15_scythe.py` (21 new `scy_*` tags, 140 frames). Tests: `tools/shots/v15/scythe/`.

The JS prefix is `scy`/`SCY_`, and the move ids and tags are `scy_*`. `sc*` belongs to 24_secrets, and the v9 `sc_*` tags
stay in the sheet only as fallbacks. 78 sets `WTYPE_INFO.scythe.prefix/first` to `scy_` / `scy_1` (77 said `sc_`).

## Identity

- **Wide arcs, front and back.** Every J reap also cuts 12 px behind you. The turning harvest, spiral, pendulum, the
  crescents, the Reap, the leg sweep and the air arc cut fully on both sides (40–48 px behind).
- **The hooked tip.** A far-edge hit drags a small foe toward you instead of knocking it away. The drag stops at the
  sweet spot (half the reach), so the next swing can still reach it with the far edge. The J K hook pull drags a small
  foe 30 px in and staggers it briefly.
- **Souls.** A hit with the **far half of the arc** harvests one soul, once per move. "Far half" means the target's
  near edge is at least 45% of the move's reach away, on whichever side it was struck. You can hold at most 3, shown as
  wisps orbiting the blade head. A hit up close, on the haft, harvests nothing, so you keep the blade's length between
  you and the foe.
  - Souls fade one at a time after 15 s with no harvest. The HUD line under the pips counts down, and the wisps flicker
    in the last 3 s.
  - A blow that lands on you scatters one soul (armour and i-frames don't count as a blow landing).
- **Reap = hold K with souls.** It spends every soul you hold.
  - Damage 1.6 / 2.4 / 3.2 and poise 50 / 70 / 90 for 1 / 2 / 3 souls; it cuts front and back.
  - Mastery IV: 2 souls already reap at full strength.
  - Mastery V: a Reap that connects heals 2% of max HP per soul spent.
- **Hold K with no souls** gives the charged crescent: it gleams when full at 0.5 s and deals 2.0. Release it early
  and you get the plain wide crescent.
- **I = Hook step** (14 stamina, 380 ms). The blade catches behind the nearest foe ahead and you swing round to land
  11 px past its far edge, facing it.
  - The foe must be roughly level, with its near edge within 64 px.
  - You are invulnerable for the first 0.3 s, and shades of the reaper trail the swing.
  - Bosses can be hooked from Mastery III.
  - If there is nothing to hook, or a wall stands where you would land, it is a 26 px hooking step with no i-frames.
  - **I → J** (Mastery II) is the backstab reap.

HUD (`T.hud`): three soul flames right of the stamina bar. They turn white once the Reap would hit at full strength, and
a thin line under them shows the fade timer. In the world:
- the soul wisps (a violet flame with a tail, solid on the normal layer plus glow and light, so they read on pale walls too);
- harvested souls fly from the hit to the orbit, and spent souls fly into the blade;
- a gleam and star while charging;
- a violet flash, shake and soul sparks on the Reap;
- quiet sine/triangle tones for harvest, Reap, hook and charge.

## Moves (final numbers; dmg in AR, wind/total ms)

| Input | Move (id) | Rank | Wind/Total | Dmg | Poise | Stam | Reach (front/back) | Purpose |
|---|---|---|---|---|---|---|---|---|
| J | Low reap (`scy_1`) | I | 160/360 | 0.9 | 10 | 10 | 44 / 12 | opener, shin-height crescent |
| J J | High reap (`scy_2`) | I | 160/360 | 0.95 | 12 | 10 | 44 / 12 | neck-height crescent |
| J J J | Turning harvest (`scy_3`) | I | 200/540 | 0.65 ×2 | 20 | 12 | 44 / 40 | ahead, turn, behind |
| J J J J | Harvest moon (`scy_4`) | I | 280/680 | 1.7 | 40 | 14 | 46 / 10 | finisher, great overhead moon |
| J J (pause) J | Pendulum (`scy_pend`) | II | 180/560 | 0.7 ×2 | 24 | 12 | 44 / 40 | out ahead, back behind; J: harvest moon |
| J K | Hook pull (`scy_hook`) | I | 200/560 | 0.8 | 20 | 12 | 46 | drags small foes 30 px in; J: high reap |
| J J K | Scything spiral (`scy_spiral`) | I | 220/700 | 0.45 ×3 | 30 | 14 | 42 / 42 | three turns, crowds |
| K | Wide crescent (`scy_heavy`) | I | 280/680 | 1.3 | 30 | 16 | 48 / 42 | flat arc round both sides |
| K K | Twin crescent (`scy_twin`) | I | 260/760 | 0.8 ×2 | 40 | 18 | 46 / 42 | rising moon + flat crescent |
| hold K, no souls | Charged crescent (`scy_charge` → `scy_charged`) | I | hold 0.5 s, then 240/720 | 2.0 | 50 | 16 + 4 | 50 / 46 | soul-light crescent |
| hold K, souls (also J / J J + hold K) | **Reap** (`scy_reap`) | I | 170 hold, then 320/1000 | 1.6 / 2.4 / 3.2 | 50 / 70 / 90 | 16 + 2 | 52 / 48 | spends all souls |
| ↑J | Rising harvest (`scy_up`) | I | 180/460 | 1.0 | 20 | 12 | art (tall) | launches small foes, fliers |
| L → J | Ghost slash (`scy_rollj`) | I | 140/420 | 1.0 | 14 | 12 | 44 | lunge 24, leaves a shade; J: high reap |
| L → K | Leg sweep (`scy_rollk`) | I | 200/560 | 1.1 | 30 | 14 | 40 / 40, low | trips small foes |
| I | **Hook step** (`scy_hstep`) | I (bosses III) | 120/380 | – | – | 14 | 64 aim | to the foe's back, inv 0.3 s |
| I → J | Backstab reap (`scy_backstab`) | II | 120/480 | 1.6 | 40 | 10 | 44 | punish from behind |
| air J | Air arc (`scy_air`) | I | 150/380 | 0.9 | 12 | 10 | 40 / 40 | full circle |
| air J J | Crescent dive (`scy_dive`) | I | 150/480 | 1.2 | 20 | 12 | art | hang, then dive at a slant to the floor |
| air ↓J | Grave pogo (`scy_down`) | I | 100/300 | 0.9 | 12 | 10 | art (down) | pogo |
| air K | Grave plunge (shared plunge, fall tag `scy_plunge`) | I | – | 1.5 | 70 | 18 | shared | blade flipped point-down |

Notes on the table:
- For the charged crescent and the Reap, the K tap has already spent 16 stamina; the hold adds the rest (20 and 18 in all).
- Mastery: II gives the pendulum and the backstab reap. III gives the hook step round bosses. IV makes 2 souls a
  full-strength Reap. V makes the Reap heal 2% max HP per soul. Every move row has its own tag; the `sc_*` fallbacks
  only matter before an art build.

## Bench (`bench.js`; table: still target, infinite stamina, 12 s; dmg/s in AR)

| Route | dmg/s |
|---|---|
| J J J J (target at 38 px, far edge) | **2.50** |
| J J J J (24 px, no souls) | 2.50 (the souls are what being close costs you) |
| J J J + hold K Reap | **2.65** |
| J J J J + Reap | 2.68 |
| Mastery IV: J J + hold K Reap (2 souls = full) | 2.68 (2.94 before the Reap's recovery went 900 → 1000 ms) |
| J J K spiral | 2.20 |
| J K hook pull | 2.00 |
| K / K K | 2.04 |
| charged crescent loop | 1.33 |
| pendulum route (II) | 2.21 |
| hook step → backstab loop (II) | 1.87 |

The main loop sits at 2.5, and the Reap route at about 2.65, inside the 2.4–2.8 band; every other route is below the
main loop. Boss bench (Gravetusk held in place, swinging every 2 s, real stamina): J J J J gives **0.89**. For
comparison, the same bench gives Longsword 0.99, Whip 0.95, Greatsword 0.98 and Staff 0.75. On that bench, stamina rarely
lets a Reap through (the roll each cycle eats it), so in practice the Reap is a punish, not a loop.

## Tests

- **`routes.js`** (51 checks, all OK). It covers:
  - every move from real inputs, each on its own tag;
  - mashing J ×8, which stops at the harvest moon;
  - hits behind you, and turning between chain steps;
  - the hook pull drag, the spiral, and the pendulum's rank gate and timing;
  - K, K K, hold K charge versus early release, and the stamina totals;
  - souls: none from the haft, harvest, the cap of 3, the 15 s fade, scatter on a hit, Reap 1/2/3 souls, IV with 2 souls, the V heal;
  - ↑J, L → J and L → K;
  - the hook step: lands behind facing the foe; no boss at I but a boss at III; I → J gated at II; a whiff step; i-frames;
  - air J J, the pogo, and the plunge on `scy_plunge`;
  - travel with forward held: J 0, K 12, L→J 29, L→K 27, hold K 24 px (all ≤ 36);
  - on a real boss (Gravetusk, C5), the rank III hook step lands past its far edge facing it, and a 3-soul Reap lands 3.20.
- **`bench.js`**: see above.
- **`shots.js` + `montage.py`**: in-game impact frames of every move, in `out/montage.png`. **`dark.js`**: the wisps,
  charge and Reap in a dark room, in `out/dark/montage.png`. **`prev.sh`**: sheet previews with hit boxes, in `prev/*.png`.
- The platform's `types.js` passes for the scythe except one check: it expects the skeleton's placeholder rule that
  L → K needs Mastery II. C4 gives the leg sweep at rank I, so that check is the skeleton's and should drop the scythe.

## Deviations from C4 and why

- **Harvest moon is 1.7 (C4: 1.5), and the low and high reaps total 360 ms (C4: 400).** At C4's numbers the main loop
  measured 2.19–2.37, under the 2.4 floor.
- **Reach is set in the rows (44–52 front)**, not measured from the art. The frame caps drawn reach at about 40, and the
  scythe should out-reach the Longsword's 40, since its whole game is spacing for the far edge.
- **Hold K means Reap everywhere.** K out of J or J J plays the hook pull or the spiral, and the chain's routes take K
  first. So if K is still held 150 ms into either of those with souls in hand, it becomes the Reap. A tapped K stays the
  route.
- **The Reap recovers in 1000 ms (C4: 900).** Without that, the Mastery IV J J + Reap loop measured 2.94.
- **Hook pull** also briefly staggers a small foe (0.45 s), so the J that follows lands.
- **Hook step travel.** It moves as far as the foe is wide: about 55 px on a small foe, about 130 px round Gravetusk.
  It is the type's deliberate dash, so it is exempt from the 36 px rule.
- **Added rules (not in C4):** souls fade after 15 s, and a blow that lands on you scatters one. The intent is that souls
  can't be banked before a boss door and that taking hits costs you the Reap. The far-edge drag stops at the sweet spot.
- **Air K** is the shared plunge (1.5 / 70 / 18) with its own fall tag. A separate grave-plunge move would duplicate the
  smash-limit plumbing for no gain.
- **Weapon art:** I kept the default art, Reap (`art_reap`), the scythe's own soul-harvest art. There is no new FP skill.

## Decisions for the owner

- **Soul fade and the scatter-on-hit rule** are my additions. Removing them makes the Reap easier to bank.
- **IV "Lean harvest"** makes 2 souls a full Reap. That turns the Reap loop into J J + Reap. It measured 2.94 with C4's
  900 ms Reap, so the Reap now recovers in 1000 ms, and the route sits at 2.68. If it still feels strong, make IV slow
  the fade instead.
- **Old scythes in pre-revamp saves** still convert to the Greatsword (platform decision). They could become the Requiem now.
