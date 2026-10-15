# v15 Close-range Bow (`bow`, Ashstring Recurve): what was built

Owner's ask: "close range bow (like monster hunter, the hunter should use it in close range)". Spec: WEAPON_REVAMP.md C2.

Files (all owned by the bow agent): `web/src/78_mech_bow.js` (moveset, arrows, HUD, feedback),
`art/player_v15_bow.py` (20 tags and the restyled bow), tests in `tools/shots/v15/bow/`. Test build: `web/dist/v15_bow.html`.
No shared file was edited.

## The trait: charge levels and the sweet spot

- **Levels 1-3.** `P.bwLv` is the level banked for the *next* shot.
  - Each quick shot raises it: J J J = levels 1, 2, 3 (1, 2, then 3 arrows).
  - A charge step (L) raises it by one.
  - Holding K draws it up one level every 0.4 s, after a 120 ms raise.
  - The power shot, the pinning shot, the leaping point-blank and the dive shot spend it (back to 1).
  - After 1.5 s with no shot or step, it falls back to 1 (with a soft gutter sound and ash off the arrowhead).
- **The sweet spot.** The distance is measured from the shooter to the foe's near edge.
  - 24-64 px: ×1.0.
  - Under 16 px: ×0.7, easing up to ×1.0 by 24 px.
  - 64-120 px: falls from ×1.0 to ×0.5. Past 120 px: ×0.5.
  - The point-blank moves (recoil shot, leaping point-blank, counter shot, dive shot, hollow piercer) take no point-blank cut. The arc shot always deals ×1.
- **Arrows are real projectiles.** They live in `projectiles`, so walls stop them and boss wards (the Omen's sigil) block them.
  - The bow file sweeps each arrow's path against the targets itself: sweet spot, pierce, drilling. The engine's own test is held shut with `win`.
  - Hits go through the normal pipeline: `outgoing(D.light, …, 'melee')`, strike hooks, bleed and fire. They count as weapon hits, not spells.
  - Arrows are drawn as outlined pixel arrows (fletching, shaft, steel broadhead).
    - Level 1: a faint streak behind. Level 2: an amber tail. Level 3: a long gold tail and a lit head.
  - They stick in walls, the floor and foes for a moment.
- **Reading the level:**
  - **Arrowhead glow.** Level 1 is a cold pinpoint. Level 2 is an amber coal with a small star. Level 3 is a gold star with sparks.
    - It hangs on the real broadhead: the game finds the head's two unique colours in the current overlay frame and caches the position per frame.
  - **Each level gained while drawing** flashes and creaks at the head; the pitch rises with the level.
  - **The draw pose itself** pulls deeper per level: frames 2/3/4 of `bw_draw`, with a strain tremble at level 3.
  - **HUD:** three arrowheads in the level colour, and a bar under them.
    - While drawing, the bar shows progress to the next level. Otherwise it shows the time before the bank gutters.
- **Sweet-spot glint.** When the nearest foe ahead is 24-64 px away, a pure-white 4-point glint sweeps over the broadhead every 0.55 s.
  - The level colours are amber and gold, so white is reserved for the glint.
  - A white pip also blinks beside the HUD arrowheads.

## Move table (final)

dmg in light-AR units, ×sweet spot unless marked pb (point-blank: no cut under 24 px).

| Input | Move (tag) | Rank | Wind / total ms | Dmg | Poise | Stam | Purpose |
|---|---|---|---|---|---|---|---|
| J | Quick shot (`bw_1`) | I | 120 / 340 | 0.4 × arrows (1/2/3 = level) | 8 per arrow | 9 | Opens the volley, banks +1 |
| J J | Quick shot (`bw_2`) | I | 120 / 340 | same | | 9 | |
| J J J | Quick shot (`bw_3`) | I | 120 / 340 | same (3 arrows at lv3) | | 9 | |
| J J J J | Pinning shot (`bw_pin`) | I | 200 / 520 | 1.7 | 30 | 12 | Finisher; reels small foes; spends the level |
| hold K | Draw (`bw_draw`, `bw_drawwalk`) | I | loop | – | – | 0 (regen ×0.5) | +1 level / 0.4 s from the bank; walk 40%, turns with the stick; L = step (banks the drawn level), I = deflect |
| release K | Power shot (`bw_power`) | I | 70 / 520 (≥180 ms drawn) | 0.9 / 1.4 / 2.0 | 20 / 35 / 55 | 14 | lv3 pierces 3 foes; commit, its own L-cancel from 260 ms |
| lv3 power → K tap | Hollow piercer (`bw_hollow`) | III | 360 / 1100 | 6 × 0.4 (pb) | 70 | 22 | A slow arrow that bores through each foe in the line (6 bites per foe) |
| J → K tap | Arrow stab (`bw_stab`) | I | 120 / 380 | 0.8 (melee) | 16 | 10 | A jab with the nocked arrow; J goes back to the volley |
| stab → K tap | Recoil shot (`bw_recoil`) | I | 140 / 520 | 1.2 (pb) | 30 | 14 | The kick hops you 30 px up and back; banks +1 |
| ↑J | Arc shot (`bw_arc`) | I | 300 / 760 | 3 rising + 5 falling × 0.3 | 40 | 16 | Rain lands 40-90 px ahead; the rising three catch fliers |
| L | Charge step (`bw_step`) | I | 300 (160 inv, 40 px) | – | – | 12 | +1 level. Neutral steps back (out to the sweet spot); a held direction steps that way |
| L → J | Dash shot (`bw_dash`) | I | 140 / 400 | 0.5 + 0.25·lv split over lv arrows (1.0 at lv2) | 16 | 12 | Skid in 22 px; J continues the volley |
| L → K tap | Leaping point-blank (`bw_leap`) | I | 220 / 600 | 3 × 0.5 (pb) | 36 | 16 | Hop in 30 px, a fan loosed down into the foe; commit; spends the level |
| L → hold K | Step and draw | I | | | | | The draw starts from the step's level |
| I | Limb deflect (`bw_deflect`) | I | 150 window / 260 | – | – | 8 | A blow in the window is negated (counter XP) |
| deflect | Counter shot (`bw_counter`) | I | 80 / 460 | 1.6 (pb) | 40 | 0 | Automatic; invulnerable 0-240 ms; banks +1 |
| air J | Aerial shot (`bw_air`) | I | 150 / 380 | 0.9 | 12 | 10 | Loosed down at 24°; twice per jump |
| air ↓J | Talon stomp (`bw_down`) | I | 100 / 300 | 0.9 (melee) | 12 | 10 | Pogo off foes and spikes |
| air K | Hunter's dive (`bw_dive` → `bw_diveshot`) | I | dive, then 60 / 460 | 3 × 0.5 (pb) | 36 | 16 | Dive at 50°, then loose point-blank on landing or on reaching a foe; once per jump; replaces the plunge |
| L L | Double charge step | II | | | | | Back-to-back steps stack (+2); at rank I only one step between shots banks |
| ↑J | Arc shot ×7 | IV | | | | | 7 falling arrows |
| lv3 shot < 20 px | Point-blank burst | V | | +0.6 | 20 | | The shot bursts through the foe and hits behind it |

**The K rule:** tapping K plays the route's move, holding K draws.
- Tap K from neutral: a power shot at the banked level.
- J → K tap: the arrow stab. J → hold K: the draw, starting at the chain's level.
- The same holds for stab → K, L → K and lv3 power → K.

**Turning:**
- Every chain step turns with the stick.
- The draw turns, so the aim follows.
- A neutral L keeps your facing and steps back.

## Animation

There are 20 new tags, one for every move. The bow is restyled as a bigger horn-tipped recurve.
- **The string and arrow follow the draw** (`bwD` px per frame).
- **The drawing arm** is the far arm, with its elbow driven back and its fist drawn over the body on the string.
- **On the loose,** the string snaps straight, the arrow leaves (streak plus flare at the bow), and the hand flies back.

Previews:
- `tools/shots/v15/bow/prev/z*.png`, made with `python3 tools/shots/v15/bow/zoom.py out.png tag …`.
- In game: `tools/shots/v15/bow/out/montage.png` (snaps.js + crop.py) and `boss_montage.png`.

Frame by frame:
- `bw_drawwalk`: the stalk at full draw. Each foot is planted for half the cycle and pushed back along the floor, then lifted forward (12 px stride at ~50 px/s, the engine's 40% walk). There is no moonwalk.
- `bw_hollow`: sink, a long strained draw, then the loose shoves you back 3-4 px with dust.
- `bw_recoil`: point-blank, the bow angled down; the kick lifts you up and back.
- `bw_deflect`: the bow swept up so its upper limb turns the blow.

## Bench (`tools/shots/v15/bow/bench.js`, 12 s per route, real presses, infinite stamina)

| Route | Rank | Foe at | dmg/s |
|---|---|---|---|
| **J J J J (main loop)** | I | 44 px | **2.59** |
| J J J J point-blank | I | 14 px | 1.81 |
| J J J J far | I | 110 px | 1.63 |
| J J J → hold K (lv3 power from the bank) | I | 44 | 2.56 |
| L → hold K (lv2 power), step-cancel loop | I | 44 | 2.16 |
| L L → hold K (lv3 power), step-cancel loop | II | 44 | 2.33 |
| J K K (stab, recoil) | I | 26 | 2.29 |
| L → J (dash shot) loop | I | 44 | 2.06 |
| L → K tap (leaping point-blank) | I | 26 | 1.47 |
| lv3 power → hollow piercer | III | 44 | 1.41 (one foe; it pierces a whole line) |
| hold K lv3 loop | I | 44 | 1.33 |
| K tap loop (lv1) | I | 44 | 1.20 |
| ↑J arc shot (5 / 7 rain) | I / IV | 64 | 1.12 (a 16 px dummy catches 3; area and anti-air) |

The main loop is J J J J in the sweet spot. Every alternative sits below it:
- J J J → hold K (a lv3 power shot from the bank) is the closest, a hair under.
- The shot → charge-step loops land at about 2.2-2.3.
- Point-blank and far play cost about 30-35%.

Real bosses (`boss.js`, a simple bot keeping the sweet spot, Mastery III, 30 s; arrows only):

| Boss | Arrow dmg/s | Arrow hits (sweet / edge / point-blank) |
|---|---|---|
| Hound | 0.72 | 38 (30 / 2 / 6) |
| Kalden | 0.85 | 37 (34 / 3 / 0) |
| Omen | 0.47 | 26 (25 / 0 / 1); the Omen's ward blocks some arrows |

The bot spends most of its time closing distance and rolling, so these numbers are a functional check, not balance: the
arrows land, mostly in the sweet spot, and there were no errors.

## Tests

- `routes.js`: every move from real inputs, the levels, the sweet spot, the glint, pierce, the rank gates (II/III/IV/V), mashing, decay, turning and lunges. **43/43 pass.**
- `bench.js`, `boss.js`, `snaps.js` (+ `crop.py`), `zoom.py` (art previews).

Run with `SHOT_HTML=web/dist/v15_bow.html sh tools/shots/wm/run.sh tools/shots/v15/bow/<test>.js tools/shots/v15/bow/out`.

## Deviations from Part C, and why

- **Pinning shot 1.3 → 1.7.** With 0.4 quick shots, J J J J was 2.2 dmg/s. 1.7 puts it at about 2.6, and keeps J J J → draw (lv3 power 2.0) just below it.
- **Power shot wind 160 → 70 after release.** The draw is the wind-up. A power shot needs at least 180 ms of draw, so a tap K is about 180 + 520 ms.
- **Power shot is `commit`, with its own L-cancel from 260 ms.**
  - With the shared after-the-hit cancel, the MH loop (shot → charge step → shot) ran at 2.7-3.3 dmg/s, above the main loop.
  - It now runs at about 2.2-2.3.
- **Charge step.**
  - A neutral L steps *back*, which keeps a close-range bow in the sweet spot. A held direction steps that way.
  - At rank I, only one step between shots banks a level. Otherwise L, L, L would reach level 3 anyway and Mastery II's double step would mean nothing.
- **K is tap/hold everywhere** (see above). The spec's "K / release" and "K → K" are both kept, and holding K never eats a branch.
- **Dash shot** scales with the banked level: 0.5 + 0.25 per level, 1.0 at level 2 as in the spec.
- **Arc shot** also looses 3 rising arrows (0.3 each) that hit fliers, since ↑J is every type's anti-air.
- **Hunter's dive** (air K) replaces the shared plunge. It dives at 50° and looses a point-blank fan as it lands or meets a foe.
- **Hollow piercer** bores through each foe in turn: it slows to 34 px/s inside a foe, bites every 80 ms, and takes up to 6 bites per foe.
- **Weapon art:** the borrowed Backstep Slash is kept (no new bow art this pass).

## Decisions for the owner

1. **Arrow hits count as weapon (melee) hits.** They get the charm and skill bonuses, bleed and fire like a sword hit, and the dummy and bench count them. Spell bonuses don't apply.
2. **A neutral charge step goes backward.** The alternative is forward, like every other type's dodge. Backward fits "fight up close, but at the sweet spot".
3. **The point-blank cut is ×0.7.** Hugging the foe with J J J J drops the bow to about 1.8 dmg/s. The point-blank moves are exempt.
4. **The default art is still Backstep Slash.** A bow art, e.g. a point-blank volley, could come later.
5. **Platform test conflict.** `tools/shots/v15/platform/types.js` still expects the skeleton's ids (`bw_heavy`, `bw_rollj`, `bw_rollk`, a J J J chain named bw_1..3 landing as melee). The bow's real moves differ: K = draw / power shot, L → J = `bw_dash`, L → K = `bw_leap` (rank I). That test needs its bow rows updated.
