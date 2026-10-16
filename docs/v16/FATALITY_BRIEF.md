# v16 Fatalities: brief (every agent reads this fully)

Repo ~/Claude/cinderhollow, branch `fatality` (local). NEVER commit, push, publish, stash or switch branches — the lead
commits. Only edit the files your role owns; small additive edits elsewhere only if unavoidable, re-read first, listed in
your report. Build/test exactly as in docs/v15/BRIEF.md (BUILD_OUT=web/dist/v16_<role>.html; tests via
tools/shots/wm/run.sh or tools/shots/shot.js; full art builds ONLY via tools/shots/v14/artbuild.sh — a lock serialises
them, ~6-12 min each now, so build rarely; previews with art/player_preview.py). Tests in tools/shots/v16/<role>/,
write-up docs/v16/<role>.md.

## The owner's request (verbatim)
"now i want you to add a fatality move (very hurt) when u stagger enemy and press k, which every kind of weapon need to be
unique, visually cool, satisfying. to give u an example: long sword -> set the sword and a large slash with large blade
aura thing; katana -> dash through enemy and slice leave a large horizontal blade slash line"
Standing taste: animation and aesthetics first; dark mythology, sleek, never cartoony; effects must look great but not
noisy; every weapon type unique.

## How it fits the game
- Today, J on a staggered foe (t.critable(): bosses in 'stagger' after its first frame, regular foes 'stagger'/'parried')
  plays the generic critical riposte (04_player.js tryRiposte / critHit: 3.2 x AR on bosses, 4.5 on others; one per
  stagger via t.critDone; t.onCritStart() holds the target). KEEP that as the quick critical on J.
- NEW: **K on a critable foe = the FATALITY** of the weapon type in hand (14 types: longsword, katana, greatsword, maul,
  sns, dual, spear, staff, whip, saxe, bow, fist, scythe, bell). It uses the same target rules and consumes the stagger
  the same way (critDone), so it's either the riposte or the fatality, once per stagger.
- Damage ("very hurt"): bosses 5.0 x AR total (the riposte is 3.2), split however the choreography likes (the last blow
  biggest); regular foes: killed outright if their HP <= 12 x AR, else 8 x AR. Riposte Mastery / Executioner / D.W.crit
  multiply it like the riposte. Boss Cores: the fatality glows in the Core's colour (visual tint only), no procs.
- The player is invulnerable for the whole fatality and can't be interrupted; the target is held for its duration (extend
  what onCritStart does — bosses must not resume attacks mid-fatality, multi-body bosses too); total length 1.1–1.8 s;
  afterwards normal play resumes cleanly (no stuck states, the boss's own stagger/recovery continues correctly).
- Cinematic layer (shared): letterbox bars slide in, the world (not the player/target/effects) darkens ~50%, slow-motion
  on the big impact, hitstop, screen shake, a flash in the weapon's colour, a short low boom; optional camera punch-in if
  the renderer allows (investigate cam / scale in 09_main.js; don't break the HUD); a weapon-coloured vignette; the
  fatality's name shown briefly in the game's title font ("ASHEN CRESCENT" style) — subtle, cinematic.

## Shared API (the FRAMEWORK agent builds it; the weapon agents use it — keep this contract)
File web/src/79_fatality.js (framework). Each weapon registers in its own file:
  fatalityRegister(type, {
    name: 'Ashen Verdict',            // shown on screen
    col: '255,220,160',               // weapon colour (rgb string) for flash / vignette / aura
    tag: 'fx_ls',                     // the player animation tag (new art), fallback tags after it: tags: ['fx_ls','ls_crit']
    tags: [...],
    dur: 1500,                        // total ms (real time, before slow-mo)
    steps: [                          // the choreography on the fatality's own clock (ms)
      { at: 0,    move: { dx: 0 } },                    // player displacement relative to the start (px; + = forward)
      { at: 300,  fx: 'auraBlade', o: {...} },          // a framework VFX primitive or a custom draw fn(ctx, t, F)
      { at: 520,  hit: 1.5, slow: 0.25, shake: 8, flash: 0.3 },   // a damage beat: share of the 5.0 (sums to 5.0)
      { at: 900,  hit: 3.5, slow: 0.4, boom: true },
      ...
    ],
    draw(F, t) { ... },               // optional per-frame custom drawing (world space), F = { x, y, face, target, t, col }
  })
The framework provides VFX primitives (each a function usable from steps or draw): auraBlade (a huge translucent blade
silhouette that follows an arc), slashLine (a long thin light line across a large span that lingers then bursts),
crescent (big arc smear), shockwave rings, groundCrack, pillar of light, sparkBurst / emberBurst / soulWisps, afterimage
trail (player ghosts), speedLines, impactFlash, colourVignette, letterbox, worldDarken — tasteful pixel-art style (crisp
1-px lines, additive glow via the glow layer, no blurry blobs). Target movement helpers (lift, knockback, pin) for small
foes; bosses never move.
A generic fallback fatality (using existing tags) for any type without its own.

## The 14 fatalities (lead's design — build these; improve details freely, keep the core idea)
1. LONGSWORD "Ashen Verdict": plant the blade point-down for a heartbeat (light gathers along it), wrench it up into a
   rising cut, then a huge descending slash: a giant translucent aura blade 3x the sword's size follows the swing and
   leaves a crescent of light that lingers and shatters. (owner's idea)
2. KATANA "Moonsever": a blink dash THROUGH the foe (afterimages), stop behind it with the blade drawn, slow sheathe — click
   — and a long horizontal slash line splits the screen across the foe, holds, then bursts into pale light. (owner's idea)
3. GREATSWORD "Grave Sunder": leap, drive the greatsword point-first down into the foe, the ground cracks in molten lines,
   then rip it free in a rising cleave that throws embers and a pillar of light.
4. MAUL "Death Knell": a full wind-up spin, the hammer crashes down on the foe; concentric shockwave rings and dust burst,
   the screen jolts; a second overhead pound drives it into the floor with a bell-like flash.
5. SWORD & SHIELD "Bulwark's End": shield bash that rocks the foe, a step in and a downward stab, then a final shield slam
   that blooms a golden crest (the shield's emblem in light) over the foe.
6. DUAL BLADES "Crimson Requiem": vanish into a whirlwind of crimson cuts around the foe (afterimages striking from every
   angle), reappear above, and an X-slash finisher leaves a crimson cross burning in the air.
7. SPEAR "Skypiercer": impale and LIFT (small foes are hoisted on the spear; bosses: the spear drives in and you vault up
   the haft), a spiral of lightning runs down the spear, a final thrust that pierces through with a long light lance.
8. STAFF "Tempest Ascension": vault onto the foe, a rising multi-spin in the air with wind rings, then a plunging strike
   that bursts a vortex of wind and dust.
9. WHIP "Thunder Leash": the chain lashes round the foe's neck, a yank toward you, you spin it once around you, and a final
   crack sends thunder racing along the chain into the foe.
10. SWITCH AXE "Grinder's Mercy": stab the blade in, the axe UNFOLDS INSIDE the foe (morph), chainsaw grind with sparks
    pouring, then a phial burst explosion; works from either form and ends in the form you started in.
11. BOW "Point-Blank Pyre": a kick that stuns, nock three arrows at once, fire point-blank into the foe; the arrows ignite
    into a burning cross that flares and fades.
12. MARTIAL ARTS "Hundred Embers": a Swift palm flurry (blur of fists), switch to Iron mid-flurry, a rooted ember palm
    that sends a shockwave through the foe and leaves a glowing palm print that cools to ash.
13. SCYTHE "Last Harvest": hook the blade behind the foe's neck, pull through in a full-circle reaping arc that leaves a
    pale crescent moon, souls rise out of the foe and flow into the blade.
14. WARBELL "Grand Requiem": raise the bell and ring a great toll on the foe — concentric sound rings ripple across the
    screen, everything shudders — three tolls rising in pitch, the last one shows a giant bell silhouette in light.

## Quality bar
Each fatality must READ instantly as that weapon's signature, look great at the game's pixel scale, and feel weighty:
anticipation → impact (hitstop + flash + shake) → follow-through → a lingering after-image of the effect. New player
animation tags with real poses (look at art/player_v13_*.py, v14_*, v15_* for the quality bar and helpers). Test in a
real boss arena and on regular foes; capture before/after snapshots and a short contact sheet per fatality.
