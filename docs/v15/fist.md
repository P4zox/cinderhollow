# v15 Martial Arts (`fist`, prefix `ft_`, Penitent's Knuckles): the moveset

Spec: WEAPON_REVAMP.md C3 (★★★★, 33 entries). The build has all of it: **37 move rows, 43 new animation tags**, and no
move falls back to a borrowed tag.

Files:
- `web/src/78_mech_fist.js`: the moves, the trait and the HUD.
- `art/player_v15_fist.py`: the tags, the second fist and the kicking legs.
- `tools/shots/v15/fist/`: `routes.js` (77 checks), `bench.js`, `snaps.js`, `montage.png`, `prev/*.png`.

## The trait: two styles, one body

The style is stored in `P.ftStyle` and is either `swift` or `iron`.

- **Swift** is fast and light. You fight up on your toes with the guard high. L is a **slip step**: 8 stamina, 240 ms,
  0.18 s invulnerable, 46 px.
- **Iron** is slow, rooted and low. It walks at 82% speed. Its wind-ups are **armoured**: a blow under 20% of max HP
  doesn't flinch it. The shoulder charge, the shoulder bash, the iron fist and its charge are armoured all the way
  through. L is the **iron step**: 12 stamina, 340 ms, 0.16 s invulnerable, 30 px. Its poise per chain is 124, against
  Swift's 37.
- **I from neutral** changes style. It is a 300 ms flourish: Swift → Iron sinks into the roots, Iron → Swift is a
  light hop. **I in the air** changes style instantly.
- **I during a ground move** is a **Shift strike**. You can press it any time from 30 ms into the move. It fires 50 ms
  after the move's first hit, which cancels the rest of the move into the other style's linking blow at **x1.15**:
  - Swift → **Falling star**, an Iron heel drop. J continues the Iron chain (elbow), K is the hammer fist.
  - Iron → **Wind cut**, four Swift blows. J continues the Swift chain (cross), K is the snap kick.
  - An I pressed behind a queued J or K belongs to the move that press starts, so a fast `J J I` shifts out of the
    cross.
  - A J or K already pressed behind the I plays after the Shift strike, so `J J J I K` works.
  - An I pressed up to 150 ms after a move ends still shifts.
  - Mashing I during a Shift strike is dropped; it doesn't queue a flourish.
- **Flow** has 5 pips and is shared by both styles. A move that lands gives +0.5, a Shift strike +1, a perfect dodge +1,
  and each hundred-fists hit +0.08. After 6 s without a hit it fades by 1 pip every 1.5 s.
  - At ranks I–IV, a Shift strike at 5 Flow becomes an **Ember shift**: x1.3 plus a burn, and it spends the Flow.
  - At rank V the Flow is kept: **hold I** in neutral (220 ms) spends it on the **Ember palm**. A tap still changes
    style.
- **Feedback:**
  - On a style change, a ring of light in the new style's colour (Swift steel-blue, Iron ember), its own sound, and an
    afterimage of the old style on each Shift.
  - In Iron, a low ember glow at the knuckles. At full Flow the wraps smoulder.
  - Armour shows as a brief orange aura when it soaks a blow.
  - The iron fist charge brightens through its 2 levels, each with a glint.
  - Smears are coloured by style: Swift steel-blue, Iron ember.
- **HUD** (`T.hud`, y = 22, right of the stamina bar): a style glyph (Swift: pale double chevron; Iron: ember block),
  then 5 Flow pips. They pulse when full, and at rank V a ring shows that the palm is ready.

## Perfect dodge → Focus (both styles; added on the owner's request)

- **The window.** A slip step or iron step started at most **120 ms** before a blow lands is a perfect dodge: the blow
  meets the dodge in its first 120 ms, inside the i-frames.
  - Why 120 rather than the Dual Blades' 100: the fist's dodges are short (0.18 / 0.16 s invulnerable, against the
    roll's 0.28), and it fights point-blank, where blows give less warning.
  - 120 ms was already the Flowing counter's window, so it stays one rule.
  - A dodge 121–180 ms ahead still avoids the blow, but gives no Focus.
- **Focus lasts 6 s.**
  - Every martial-arts hit deals **×1.1**. This goes through `hitMod`, and the hundred fists, the dives and the stomp
    shockwave multiply it in themselves.
  - Every hit box reaches **+6 px**. I chose a flat 6 px, which is about 20% of a jab's box. It applies to the front edge
    (both edges on spins) through a wrapper of `mvRect` in `78_mech_fist.js`, and to the manual boxes too.
  - A new perfect dodge refreshes the 6 s; it never stacks.
  - It also gives +1 Flow and Mastery XP.
- **No farming.** There is one perfect dodge per blow and per enemy attack, keyed with the Dual Blades' `twKeys`: a
  hazard's or beam's ticks are one blow, and one boss attack's windows share its attack id. Body contact is never a
  blow.
- **Rank III.** A Swift perfect slip → J is still the Flowing counter, and it gets the Focus bonus too (1.54). A perfect
  Iron step → J is the palm.
- **Feedback:**
  - a chime (bright for Swift, lower for Iron);
  - a 0.09 s slow-time flicker;
  - an afterimage, sparks and a flash in the style's colour;
  - both fists glow in the style's colour while Focus lasts;
  - on the HUD, a timer ring around the style glyph that drains over the 6 s.
- **Move List:** a new entry, "Perfect dodge (Focus)", for both styles.

## Moves

Times are wind / total in ms; dmg is in light-AR units.

### Swift

| Input | Move | Rank | Wind/Total | Dmg | Poise | Stam | Notes |
|---|---|---|---|---|---|---|---|
| J | Jab | I | 80/220 | 0.5 | 4 | 6 | far fist; J cross, K rising knee |
| J J | Cross | I | 80/220 | 0.55 | 5 | 6 | J hook, (beat) J backfist, K whirlwind |
| J J J | Hook | I | 100/260 | 0.65 | 8 | 7 | |
| J J J J | Knee rush | I | 120/480 | 0.4 ×3 | 20 | 10 | finisher, 24 px drive (clinch, 3 knees) |
| J J (pause) J | Spinning backfist | II | 140/400 | 0.9 | 14 | 8 | press 110–300 ms after the cross; J knee rush |
| K | Snap kick | I | 140/380 | 0.9 | 12 | 9 | K roundhouse, J cross |
| K K | Double roundhouse | I | 160/560 | 0.6 ×2 | 20 | 12 | the 2nd kick spins, higher |
| J K | Rising knee | I | 120/380 | 0.8 | 14 | 9 | small hop, pops light foes; J cross |
| J J K | Whirlwind kick | I | 160/520 | 0.5 ×2 | 18 | 11 | both sides |
| hold K | Hundred fists | II | loop | 0.15 / 65 ms | 2/hit | 16/s | up to 3 s; a tap is still the snap kick, no added delay |
| ↑J | Rising uppercut | I | 120/400 | 0.8 | 16 | 9 | launch |
| L | Slip step | I | 240 | – | – | 8 | 0.18 s invulnerable |
| L → J | Shadow jab | I | 100/320 | 0.8 | 10 | 8 | J cross |
| L → K | Sliding sweep | I | 140/460 | 0.9 | 22 | 10 | low, trips (reel) light foes |
| L (perfect) → J | Flowing counter | III | 80/400 | 1.4 | 30 | 6 | slip a blow in its first 120 ms; J goes out at once |

### Iron

| Input | Move | Rank | Wind/Total | Dmg | Poise | Stam | Notes |
|---|---|---|---|---|---|---|---|
| J | Iron palm | I | 260/560 | 1.1 | 30 | 12 | J elbow, K grapple throw |
| J J | Elbow drive | I | 260/560 | 1.2 | 34 | 12 | J shoulder, K pillar kick |
| J J J | Shoulder charge | I | 320/740 | 1.6 | 60 | 16 | finisher, armoured through, 28 px |
| K | Hammer fist | I | 340/800 | 1.5 | 50 | 16 | K stomp, J elbow |
| K K | Mountain stomp | I | 360/900 | 1.0 + 0.6 shock | 40 + 30 | 18 | the shockwave hits both sides (r 34) |
| hold K | Iron fist | I | charge → 160/620 | 1.8 / 2.6 | 60 / 90 | 20 | levels at 320 / 900 ms, armoured, turnable; release before lv1 = hammer fist |
| J K | Grapple throw | I | 240/800 | 1.6 | 50 | 16 | a small foe lands behind you (stance broken); a boss takes the palm |
| J J K | Pillar kick | I | 300/760 | 1.4 | 50 | 16 | heel straight up, launch |
| ↑J | Heaven's uppercut | I | 300/700 | 1.3 | 40 | 14 | launch |
| L / L → K | Iron step / Shoulder bash | I | 340 / 200/560 | – / 1.2 | – / 50 | 12 / 14 | the bash is a 30 px armoured dash |
| L → J | (Iron palm) | I | | | | | the palm out of the step (not in the plan) |

### Switching and shared

| Input | Move | Rank | Wind/Total | Dmg | Poise | Stam | Notes |
|---|---|---|---|---|---|---|---|
| I (neutral) | Change style | I | 300 | – | – | 0 | `ft_toiron` / `ft_toswift` |
| Swift move → I | Falling star | I | 260/640 | 1.4 ×1.15 | 50 | 14 | Iron heel drop; J elbow, K hammer |
| Iron move → I | Wind cut | I | 120/520 | 0.28 ×4 ×1.15 | 20 | 12 | J cross, K snap kick |
| Swift J J J → I → K | Tempest to mountain | III | 100/900 | 0.3 ×4 + 1.0 | 60 | 18 | 4 Swift blows, then the Iron hammer fist |
| Iron hold K → I | Iron to wind release | IV | 90/480 | 1.2 / 1.6 / 2.2 | 30/45/70 | 10 | dash-punch through (46 px, 140 ms invulnerable), ends in Swift; J cross |
| hold I (5 Flow) | Ember palm | V | 380/900 | 3.0 | 120 | 0 | commit, 30% armour, burn, empties Flow |
| Swift air J / air J J | Air kick / Triple air kick | I | 110/300 · 100/440 | 0.7 · 0.3+0.3+0.4 | 10 · 15 | 8 · 10 | the triple kick holds the fall so all 3 land |
| Iron air J | Diving elbow | I | 160 + dive | 1.2 | 34 | 12 | 60° dive; impact on landing, or bounces off a foe it meets |
| air K | Diving heel | I | 150 + dive | 1.3 | 50 | 14 | steep dive (replaces the plunge), same bounce |
| air ↓J | Stomp | I | 100/280 | 0.8 | 12 | 8 | pogo |

**Mastery unlocks:**
- II: Spinning backfist, Hundred fists.
- III: Flowing counter, Tempest to mountain.
- IV: Iron to wind release.
- V: Ember palm.

The Move List has 32 entries, each description 70 characters or fewer.

## Animation

43 tags in total:
- **Stances:**
  - `ft_sw_idle`: a 6-frame bounce on the toes, guard high, the far fist leading.
  - `ft_sw_run`: a boxer's run, guard up, leaning in.
  - `ft_ir_idle`: low and wide; the lead palm open at the chest, the near fist chambered at the hip, a slow breath.
  - `ft_ir_walk`: a heavy, low stride.
  - Both cycles plant the foot on the backward half of the stride and lift it on the forward swing.
- **Dodges:** `ft_slip` and `ft_istep`.
- **Holds:** `ft_hundred` and `ft_ichg` (loops).
- **Flourishes:** `ft_toiron` and `ft_toswift`.
- **Attacks:** one tag per move, each with:
  - anticipation, then a smear, impact, follow-through and settle;
  - its time-map matched to its move row;
  - active frames and a fixed feet-relative hit box (`hit=`) in the meta;
  - `hits=` for the multi-hit moves (knee rush, roundhouse, whirlwind, wind cut, tempest, triple air kick), so each
    hit lands on its drawn frame.
- **Both fists read.** `register()` adds `penitent_knuckles` to `G.TWIN_KINDS` / `G.EXTRA_KINDS`, so every frame's
  `offw` puts the second spiked knuckle on the far hand. `front=True` draws it over the body when the hand is out in
  front. This happens at runtime inside the fist module and touches no shared file. Shared tags (roll, jump, hurt,
  heal, Bloodstep) show the far knuckle tucked at the back hip, where the body hides it.
- **Kicks have real legs.** `kF` / `kB` replace a leg with a longer IK leg (seg 6.0–6.8 against 5.2) plus a real foot
  that points along `toe`: a heel for the pillar and the falling star, the ball of the foot for the snap kick, the
  instep for the roundhouse. Spins use mirrored frames (the backfist, the whirlwind, the 2nd roundhouse).
- **Smears:**
  - punches: `speed` lines and a knuckle flare;
  - kicks: `ring` bands swept round the hip;
  - colour by style: Swift `SWIFT` steel-blue, Iron `IRON` ember, the palm `EMBERP`, the counter silver.
- **Art budget:** 235 new frames. The player sheet is now 2957 frames with all five v15 types.

## Tests

`tools/shots/v15/fist/routes.js` passes **77 / 77** (14 of the checks are perfect-dodge checks: perfect against late
in both styles, refreshing without stacking, one per attack, hazard ticks, body contact, reach (a jab at 43 px misses
without Focus and lands with it), damage (jab 0.55, palm 1.21, hundred fists 0.165 a hit), the Flowing counter with
Focus (1.54), Iron step → J being the palm, and the 6 s expiry). Every move is driven from real inputs (press, hold, timing), and
the run covers:
- **Rank gates:** backfist / hundred II, counter / tempest III, release IV, palm V.
- **Mashing:** J ×12 stops at the knee rush.
- **The flourish and stances:** the 300 ms flourish and the Iron idle tag.
- **Iron armour:** a 10% blow doesn't flinch the palm's wind-up; 30% does; a Swift jab does.
- **The Shift system:** the cancel 56 ms after the hit, the ×1.15 and ×1.3 Ember shift, the full
  Swift → Iron → Swift dance, the late Shift (70 ms after the move ended), and that an I at 230 ms is a style change
  instead.
- **Flow:** it builds correctly, and holding I at 5 Flow is a palm while a tap is a style change.
- **Air, turning and travel:** the air moves (including the instant air switch), turning between chain steps, and lunge
  travel (knee 25, shoulder 30, sweep 5, bash 13 px, release 41 px as a dash).

`tools/shots/wm/mech.js`: no failures.

`snaps.js` takes 30 in-game shots in the Rootgate hall, collected in `montage.png`.

## Bench (`bench.js`: dummy, infinite stamina, real inputs, 12 s per route)

| Route | dmg/s |
|---|---|
| **Swift J J J J (main loop)** | **2.41** |
| Shift dance: J, then (J I)… (cross → falling star → elbow → wind cut …) | 2.79 (the skill ceiling, top of the band) |
| Iron J → I → J J J | 2.64 |
| Tempest: J J J → I → K (III) | 2.50 |
| Swift K J J J | 2.38 |
| Swift J J → I → J J | 2.31 |
| Swift K K | 2.17 |
| Hundred fists (II) | 2.09 |
| Iron J J J | 2.04 (124 poise per chain) |
| Swift J K / J J K | 2.01 / 2.01 |
| Iron J J K / J K | 1.94 / 1.93 |
| Iron K K | 1.77 (70 poise stomp) |
| Iron hold K lv2 loop | 1.17 (hold time counted; 2.6 in one hit inside an opening) |
| **With Focus kept up:** Swift J J J J / Iron J J J / Shift dance | **2.65 / 2.24 / 3.07** (+10%, like the Dual Blades' 3.4 → 3.7) |

**Boss bench** on Gravetusk, held in place and swinging every 2 s: a bot attacks inside the 1.3 s opening and rolls
through each swing, on real stamina.

| Route | dmg/s |
|---|---|
| Iron J J J | 1.51 |
| Shift dance | 1.22 |
| Swift J J J J | 0.82 |

The swing catches Swift mid-chain and flinches it, while Iron's armour soaks it. That's the intended trade (Swift wants
the slip step), and the crude bot never dodges early. For scale, the Katana's mixes score about 1.16 on this bot.

## Deviations from C3 (and why)

- **Perfect dodge with Focus (owner's request, added after the build):** described in its own section above.

- **Knee rush:** 0.35 ×3 → **0.4 ×3**, which lifts the main loop from 2.33 to 2.41 (into the band).
- **Hundred fists:** 0.2 / 60 ms → **0.15 / 65 ms**, 14 → 16 stamina/s, with a 3 s cap. At plan rates it ran 3.3 dmg/s,
  above every main loop; now it's 2.1, an alternative.
- **Iron chain:** totals tightened a little (palm and elbow 600 → 560, shoulder 760 → 740), from 1.99 to 2.04 dmg/s.
- **Shift strikes:** the Falling star went 1.5 → **1.4** and the Wind cut 0.3 → **0.28 ×4**. With the +15% and the cancel
  at the hit, the alternating dance otherwise ran about 3.0. It now tops out at 2.79 and costs 44 stamina a cycle.
- **Tempest to mountain** reads as Falling star → K when the star came out of the hook (Swift J J J → I → K): four Swift
  blows, then the Iron hammer fist (2.2). From any other move, K after the star is the plain hammer fist.
- **Ember shift (new, ranks I–IV):** the plan's Flow did nothing before rank V, so a full gauge now ignites the next
  Shift strike (x1.3, burn). At V the Flow is saved for the Ember palm instead.
- **New routes:**
  - snap kick → J (cross), hammer fist → J (elbow), Iron L → J (palm);
  - I in the air is an instant style change;
  - K tapped in Iron is the hammer fist through the charge, with no added delay.
- **The air moves:**
  - The diving heel replaces the plunge as air K, and the diving elbow is Iron's air J. Both dives bounce off a foe they
    meet in the air; otherwise they land with an impact.
  - The triple air kick holds the fall, because from a hop the 2nd and 3rd kicks used to land after touchdown.
- **Weapon art:** the borrowed default, **Bloodstep**, is kept. Its martial dash-through fits, and no new art was
  made.

## Shared files

None were edited. The second knuckle is registered at runtime from `art/player_v15_fist.py`.

The platform agent's `tools/shots/v15/platform/types.js` still checks the skeleton ids (`ft_1`, `ft_heavy`, `ft_rollj` …),
so its fist rows now fail, as they do for the other moveset agents. This file's `routes.js` replaces those checks.

## Decisions for the owner

- **Ember shift.** Should Flow do something before Mastery V? I made a Shift strike at 5 Flow ignite. The alternative is
  plan-pure: Flow only for the palm.
- **Where Swift sits on the boss bot.** It is the weakest route there, because it flinches. If that feels bad in play,
  give the Swift chain a little poise armour on the knee rush, or make the slip step cheaper.
- **The skill ceiling.** The Shift dance reaches 2.79 dmg/s on the dummy. A balance pass could take the Shift multiplier
  to x1.1 if it proves too easy.
