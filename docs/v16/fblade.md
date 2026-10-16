# v16 Fatalities: the blade agent (`fblade`): Katana, Switch Axe, Scythe

Files: `web/src/79b_fatal_blade.js` (added after the Longsword, which is unchanged), `art/player_v16_fatal_blade.py`
(tags `kt_fatal`, `sx_fatal`, `sx_fatal_a`, `scy_fatal`; `ls_fatal` is unchanged), tests and contact sheets in
`tools/shots/v16/fblade/`. Build: `BUILD_OUT=web/dist/v16_fblade.html python3 web/build_web.py`.

## 2. KATANA "Moonsever" (1500 ms, colour 205,225,255)
This is the owner's idea: dash through the foe and slice, leaving a large horizontal blade line.
- **Anticipation (0–300):** you sink into the iai crouch, sheathed, with your thumb on the guard (a glint and a click of
  tension). A faint pale **moon ring** rises behind the foe and grows brighter during the whole sequence.
- **Blink (300):** you dash **through** the foe in 55 ms (30 px past its far edge), leaving blue-shade afterimages, speed
  lines and a draw-flash. Beat 1 (1.0 share) lands as you pass. It leaves only a **1-px hairline** through the foe, and
  the foe's white hit flash is held down, because the cut has not "arrived" yet.
- **Zanshin (400–720):** you hold still behind the foe, back turned and blade out low. Then a **chiburi** flick throws a
  few pale droplets off the edge.
- **Sheathe (720–990):** you slide the blade home slowly. The visible steel shortens as your hand nears the saya, with a
  long steel-slide sound.
- **CLICK (990):** beat 2 (4.0 share) with slow-mo 0.5, hitstop, shake 10, flash, boom and the name. A **460 px
  slash line** splits the screen across the foe at 42% of its height, tilted 4° up. It holds for 400 ms, then bursts into
  pale light, with motes drifting up afterwards. At the same moment the **foe is split**: the target is drawn twice,
  clipped above and below the cut line, and its upper half slides 4 px along the cut while the line holds, then drops
  back when the line bursts. The moon ring is cut in two, its halves drift apart and dissolve.
- You end sheathed, standing behind the foe and facing away from it (the iconic shot).

## 10. SWITCH AXE "Grinder's Mercy" (1700 ms, colour 255,160,70)
- **Draw-back (0–280):** the blade is drawn back level at the hip and the phial lights (ember glow, sparks).
  - From **axe form** (`sx_fatal_a`), the axe comes off your shoulder, swings down level and the blade jack-knifes out
    of the haft, so it can stab.
- **Stab (285):** the blade is rammed in. Beat 1 (0.8 share): sparks and a flash at the head.
- **The unfold INSIDE the foe (420–660):** the cels step through the real morph forms in four mechanical clanks:
  unlatch, swing, slide, then LOCK at 600 (a jolt, a flash, a sawtooth growl). **Molten seams** branch through the
  foe's body from the head, a custom fx that stays clipped to the hurtbox.
- **Grind (660–1150):** the chain crawls (its phase advances on every cel) and your body shakes with it. Sparks pour
  off the head every 30 ms, a hot star flickers where it bites, the chainsaw noise loops, and the screen jitters.
  Two bites land at 760 and 960 (0.6 share each).
- **Phial burst (1150):** beat 4 (3.0 share) with slow-mo, flash, boom and the name. A ragged **fireball** made of 34
  1-px fire tongues bursts out of the wound (hot core, then ember, then deep red, curling up as it cools). With it come
  an impact star, a flat ground ring, sparks, embers and dust. The blast throws the head up and you a step back. The
  seams then flare and cool to dark red.
- **Recovery:**
  - From **sword form**, the grinder folds back into the sword, with clanks.
  - From **axe form**, it is hoisted back onto your shoulder with the chain still ticking.
- **It ends in the form it started in**, and the Switch Gauge, the lock and the form are **frozen** for the whole
  fatality: no drain, no bleed, no vent.
- All four blows land at the head's height and reach (`hy` / `x` set in `start`), not at the middle of a tall boss.

## 13. SCYTHE "Last Harvest" (1600 ms, colour 205,185,255)
- **Hook (0–290):** you raise the scythe and reach over the foe. A **spectral reaper's blade** grows out of yours: a
  snath of 52–90 px from your shoulder, a curved blade with a bright edge, a soft fill and ghost outlines along its arc.
  The blade drops **behind the foe's neck**.
  - Beat 1 (0.7 share) is the hook biting at the top of the foe, with a jolt toward you. A small foe is hauled 5 px in.
- **Haul (300–560):** you lean back on the haft and the ghost snath shortens under the strain.
- **The full circle (560–760):** the blade is pulled through the foe (beat 2, 4.3 share, at 600: slow-mo, boom, name)
  and on round the body: under the floor, behind you, over the top and down in front. The cels spin with matching
  soul-violet ring smears.
- **The pale crescent moon (655+):** a crescent of 0.92 × the ghost's reach over the upper half of the circle. It
  lingers for 620 ms and shatters into shards.
- **Harvest (760–1500):** 22 souls rise out of the foe and stream into the upright blade, which glows (aura levels
  1 → 3, a light and a pulsing star at the tip, three rising chimes). You then rest the blade.
- **Afterwards your scythe holds all 3 souls** (`P.scySouls = SCY_MAX`, Reap ready). This is the weapon's own resource,
  so it is no Core proc. **Decision for the owner:** this makes the fatality feed straight into a full Reap. Remove the
  `end()` in the scythe registration if that's too generous.
- On pale backgrounds (the Pale Crown sentinels arena) the additive light washes out, so the ghost blade also gets a
  dusk-violet shade on the lit layer (`drawLit`) to keep it readable.

## Tests (real inputs: K on a staggered foe)
- `tools/shots/v16/fblade/check.js` → `check_result.txt`: **ALL PASS (28 cases)**.
  - Setup: katana, scythe, and the Switch Axe from both forms, each in 4 real arenas (Omen, Frostbound Twins, Gilded
    Sentinels, Antlered Warden; the twins and sentinels are multi-body) plus 3 regular foes.
  - Boss checks: 5.0 × AR dealt (katana 4.99, others 5.00), the player is immune mid-way (blow, spikes, killPlayer),
    the other body never moves, the boss is released, and recovery takes 26–37 frames before the boss attacks again.
  - Foe checks: 8.0 × AR on a tough foe, executed at ≤ 12 × AR, 8 × AR (alive) just above that line, ends idle.
  - Weapon rules: the saxe's gauge and form are exactly kept (both forms), the scythe has 3 souls afterwards, and the
    katana's split is active (`splitSeen` 26 frames) and cleaned up.
- `arenas_<type>_result.txt`: the framework's 11-arena test for each type, all pass. The one exception is the Ice
  Warden at 0.75 × AR, which is its 85% shell, identical to the Longsword reference.
- `framework_tests_result.txt`: the framework's 27 checks still pass with these files loaded.
- Contact sheets:
  - `kt_boss_sheet.png` (Omen) and `kt_foe_sheet.png`
  - `sx_boss_sheet.png` (Warden, sword form) and `sx_foe_sheet.png`
  - `sxa_boss_sheet.png` (Twins, axe form) and `sxa_foe_sheet.png`
  - `scy_boss_sheet.png` (Executioners) and `scy_foe_sheet.png`
  - Regenerate them with `sh tools/shots/v16/fblade/snap_all.sh`. Tag previews are in `prev/`.

## Notes
- Lights stay at k ≤ 0.8 everywhere.
- The katana's split draws the target twice for about 0.5 s. The second pass mutes `addLight` / `drawGlow`, so lights
  and glow don't double. If a boss's body is drawn by its owner rather than by the part itself, the split silently
  does nothing.
- The saxe tag is chosen through a getter (`get tag()`, read when the fatality starts) by `P.sxAxe`.
- One small wrapper in my file: `MV.types.saxe.tickAll` is skipped while the saxe fatality plays. This is what
  freezes the gauge, and it is the only touch outside a `fatalityRegister` call.
- No edits to `79_fatality.js` or any other shared file.
