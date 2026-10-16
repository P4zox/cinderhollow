# v16 Fatalities: the heavy group (agent `fheavy`)

Greatsword "Grave Sunder", Maul "Death Knell", Warbell "Grand Requiem". These are the weightiest weapons, so each
fatality sells its mass with a long anticipation, big hitstop, cracked floors, flat shockwaves, and stone and dust
thrown up (a small lit-layer debris system lives in this file).

Files: `web/src/79c_fatal_heavy.js` (registrations, debris, the bell synth, custom FX),
`art/player_v16_fatal_heavy.py` (tags `gs_fatal`, `ml_fatal`, `wb_fatal`), and tests in `tools/shots/v16/fheavy/`.
No shared files were edited.

## The three

| | Greatsword "Grave Sunder" | Maul "Death Knell" | Warbell "Grand Requiem" |
|---|---|---|---|
| colour | `255,168,92` ember | `255,200,128` hot brass | `242,214,150` pale bell-gold |
| dur / tag | 1700 ms, `gs_fatal` (16 frames) | 1650 ms, `ml_fatal` (20 frames) | 1800 ms, `wb_fatal` (22 frames) |
| beats (share of 5.0 / 8.0) | 620 impale 1.5 · 1090 sunder 3.5 | 650 crash 1.5 · 1120 pound 3.5 | 400 toll I 1.0 · 810 toll II 1.2 · 1270 toll III 2.8 |
| name shown | on the sunder | on the pound | on toll III |

**Grave Sunder.** The knight hauls the slab up into a deep coil with the blade wound behind the shoulder (a glint).
He springs about 30 px up and a step closer (a `move` with `dy`). At the apex he turns the blade point-down in both
fists and hangs there while motes gather into it. Then he dives with short ghosts and streaks and **impales** it
through the foe into the floor at 620 ms: 0.13 s hitstop, kickY 3, molten ground cracks running out both ways, a
flat shockwave, sparks, and hot-faced stone chunks and dust. He kneels over the hilt while the buried steel runs
molten from the floor up (the tag's `heat` creeps up over 3 frames, plus a glowing seam and pool drawn in `draw`). The
ground trembles twice, a second, wider crack network opens, and embers lift off the seams. At 1090 he **rips it
free** in one rising cleave, the big beat: slow-mo, a 0.16 s stop, shake 13, the boom and the name. It throws a
rising crescent, a pillar of light where the blade came out, a burst of embers and sparks, 18 stones and a dust
cloud. A small foe is impaled in place (pinned), then flung up 22 px and dropped. He holds the blade high while the
pillar burns, and the pillar, cracks and embers outlive the fatality.

**Death Knell.** One full wind-up spin, with the hammer whirled flat round the waist (light ghosts, dust kicked off
the floor). The hammer is wheeled up over the top and hung over the helm while the head gathers light. It **crashes**
down on the foe at 650 ms: two concentric force rings round the foe, a flat ground ring, a short crack, dust and
stone, and the screen jolts (kickY 4). The rebound heaves it straight back up onto the toes, higher than before, and
the head glows white-hot. The **pound** at 1120 drives it into the floor. You get a bell-bright flash (impact star
r 54), one crisp dome of light opening from the strike point (clipped at the floor), three wide flat ground rings,
the floor broken both ways (104 px), a big dust cloud and stone, and a deep dull iron clang (`fhBell` at 73 Hz) over
the boom. He kneels over the haft while the dust settles and a last flat echo ring goes out at 1380.

**Grand Requiem.** Three tolls on the foe, each heavier than the last: a lift-and-drop, a heave over the back
shoulder, then the full wind-up over the top. Each toll is audible as a struck bell (hum, prime, minor-third tierce,
quint, nominal, strike partial and noise) and they rise in pitch **A2 110 → C3 131 → E3 165 Hz**, a minor triad
climbing to the last. The third toll adds an octave-down hum. Each toll sends 2/3/4 slightly wavering, dotted rings
of sound across the screen (r 150 / 210 / 300) plus a flat ground ring. After each toll everything shudders: `tick`
keeps a buzzing tremor alive for 340 ms, stronger every toll. Before the last toll, light streams into the bell and it
glows. At **toll III** a **giant bell silhouette in light** drops onto the foe's floor line. It is 96–132 px tall,
scaled to the foe's height: a hot 1-px outline, a faint dithered body, lip / sound-bow / waist bands, a crown loop,
and the clapper swinging inside. Its lip shivers while it rings, then it dissolves from the crown down over about
1.3 s, with one last ground ripple at 1520.

## Tests (real inputs: K on a staggered foe, `web/dist/v16_fheavy.html`)

`sh tools/shots/v16/fheavy/run.sh arenas <type>`, `... foes`, `... snaps <type> <arena> <at-list> [foe] [suffix]`

- **Boss arenas** (`arenas_<type>.txt`; 5 real arenas: Omen, Twin Executioners (multi-body), Bell-Ringer, Hoarfrost
  Twins (multi-body), Kalden). All three types give 5.00 x AR (maul 5.01), split greatsword 65 / 152, maul 62 / 144,
  bell 48 / 57 / 134. In every arena: invulnerable mid-fatality (a 9999 blow, spikes and a projectile do nothing), the
  other body of a duo never moves, the boss is released at the end, the player ends idle, and the boss leaves stagger
  26–37 frames later and attacks again.
- **Regular foes** (`foes_result.txt`, allPass). These cover: the real tag plays (no fallback), 8.0 x AR (7.98–8.00)
  on a tough foe, and execution on the last beat when HP ≤ 12 x AR (alive mid-way, dead after). They also cover
  invulnerability, the greatsword's leap (30 px up, lands on the same floor, dy 0), the foe lifted 22 px and landed,
  nothing left held, the cinematic layers cleared, and the next light attack starting (`gs_1`, `ml_1`, `wb_1`).
- **Framework regression** (`types_result.txt`): `tools/shots/v16/fatality/types.js` passes all 14 types on this build.
- No page errors in any run.
- **Contact sheets**: `gs_boss_sheet.png` / `gs_foe_sheet.png` (Omen), `ml_boss_sheet.png` (Executioners),
  `ml_boss2_sheet.png` / `ml_foe_sheet.png` (Kalden), `wb_boss_sheet.png` / `wb_foe_sheet.png` (Bell-Ringer).
  Pose previews are in `prev/`.

## Notes / decisions

- I cut the ghost trails hard (greatsword dive and maul spin: every 50–70 ms, alpha ≤ 0.18). A vertical dive or an
  in-place spin stacks `mvAfterimage` copies into a white blob that hid the knight.
- The maul's rings stay compact and ground-hugging (one crisp dome, flat rings). The wide wavering rings that cross
  the screen are kept for the Warbell, so the two blunt weapons read differently.
- Effect lights stay at k ≤ 0.8. The boss still flashes white for a beat on each hit; that is the framework's hit
  flash, as for the longsword.
- The snapshot harness pins `Math.random` to 0.5. The `snaps` mode reseeds it with a small LCG so the sparks, stones
  and dust look natural in the sheets.
