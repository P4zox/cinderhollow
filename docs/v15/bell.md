# v15: the Warbell (`bell`, weapon Dirgebell) -- bell agent

Spec: docs/WEAPON_REVAMP.md C5. Code: `web/src/78_mech_bell.js` (globals `bel*` / `BEL_*`, player state `P.bel*`; move ids and
animation tags `wb_*`, nothing else in the game uses that prefix). Art: `art/player_v15_bell.py` (20 new tags, and a restyled
Dirgebell). Tests: `tools/shots/v15/bell/{routes,bench,boss}.js` (routes: 50/50 OK). Previews: `tools/shots/v15/bell/out/pv_{a,b,c}.png`,
in-game: `out/montage_world.png`, `out/montage_hud.png`.

## The trait: notes, tolls, Perform

- **Notes.** A blow that *lands* rings a note into a 3-note staff (oldest falls off): J blows ring **Ash** (white), K blows
  ring **Ember** (crimson), the up J rings **Gold**. One note per move; the double slam rings one per hit. A whiff rings
  nothing (no pre-buffing in an empty room; the bell sounds when it strikes something).
- **Sound.** Each note is its own struck-bell pitch, synthesised from inharmonic partials (hum, prime, minor-third tierce,
  quint, nominal + a short strike): Ember G3, Ash D4, Gold B♭4 -- a dark G-minor triad. A Perform plays the staff back as
  an arpeggio, then a great low toll (G2) under it; the Encore tolls a third higher; Echo re-rings are an octave-up Gold.
- **Tolls** (a run of notes in the staff, in order) -- buffs last 30 s:

  | Toll | Notes | Buff |
  |---|---|---|
  | Swiftness | Ash Ash | stamina regen +25% |
  | Iron hymn | Ash Ember | finishers and heavies don't flinch from hits < 20% max HP |
  | Fury | Ember Ember | +8% damage |
  | Echo | Gold Gold | the next 3 hits ring again 0.16 s later for 30% |
  | Mending (II) | Ash Gold Ember | heal 10% max HP over 10 s, once per 60 s |

  A full staff can hold two tolls (Ash Ash Ember = Swiftness + Iron hymn; Ash Ember Ember = Iron hymn + Fury).
- **I = Perform** (needs ≥ 1 note; an empty staff = a dull deny clank and a red flash of the staff): a ringing blow on both
  sides (1.2, 40 poise), plays every toll in the staff, empties it, grants the buffs. **Encore** (III, I again): 1.4 both
  sides and every toll still sounding goes back to 30 s (Echo back to 3 charges; Mending's heal isn't re-armed).
- **Blunt:** every bell hit does ×1.3 stance damage. **Hold K** winds the toll; while winding, hits < 25% max HP don't flinch.

### Feedback
- **HUD** (`T.hud`, the column right of the stamina bar): a 3-line staff with a note head + stem per slot (Gold on the top
  line, Ash middle, Ember low) in the note colour; the newest note pops in; the staff lines flash red on a denied Perform.
  Right of it, in small caps, the toll(s) a Perform would play now ("Swiftness · Iron hymn"). Below: one icon per toll
  sounding -- a ring draining over its 30 s (blinks in the last 3 s) around a glyph (chevrons, a shield, a flame, a cross,
  echo arcs) with Echo's charges as pips.
- **World:** each struck note: a ring flash in the note colour at the impact, a spark burst, a small note glyph that floats
  up. Perform: two expanding pixel shock rings (glow layer) from the bell, a big warm light, dust, the toll names popping
  over the head; Grand toll adds a third, wider ring; the IV echo wave is a ring rolling out to 64 px. Wind-up: the bell
  hums ember-red, a star glint once wound. Tolls sounding: a mote per toll circling the knight in its colour, a soft light;
  Mending: rising motes.

## Moves (dmg in AR multiples; wind / total ms)

| Input | Move | Rank | Note | Dmg | Poise | Stam | Wind/Total | Notes |
|---|---|---|---|---|---|---|---|---|
| J | Left swing | I | Ash | 1.1 | 18 | 12 | 190/460 | diagonal forehand |
| J J | Right swing | I | Ash | 1.15 | 18 | 12 | 190/460 | rising backhand |
| J J J | Overhead clang | I | Ash | 1.8 | 45 | 16 | 290/720 | finisher, mouth-first into the floor |
| J J (pause) J | Chime spin | II | Ash | 0.7 ×2 | 30 | 14 | 220/640 | both sides; pause = 110-450 ms after the right swing ended |
| J J J → K | Knell | I | Ember | 1.6 | 55 | 18 | 320/820 | low sweep, knocks small foes away (new) |
| J → K / J J → K | Backswing | I | Ember | 1.2 | 30 | 14 | 240/620 | → J: overhead clang |
| K | Forward slam | I | Ember | 1.5 | 40 | 16 | 280/680 | |
| K K | Double slam | I | Ember ×2 | 1.05 ×2 | 60 | 20 | 300/880 | finisher |
| hold K | Wind-up toll | I | Ember | 2.4 | 80 | 22 | wound at 650 ms; release 200/760 | armoured while winding (<25%) and in the release (<25%) |
| ↑J | Peal uppercut | I | Gold | 1.1 | 25 | 12 | 220/560 | ↑J again: another peal |
| ↑J → J | Falling peal | I | Ash | 1.2 | 30 | 12 | 200/560 | new |
| I | Perform | I | – | 1.2 | 40 | 14 | 300/900 | both sides; plays the tolls |
| I → I | Encore | III | – | 1.4 | 50 | 10 | 260/800 | both sides; refreshes |
| L → J | Ringing lunge | I | Ash | 1.0 | 20 | 12 | 160/440 | 22 px dash; → J: right swing |
| L → K | Bell drop | I | Ember | 1.4 | 45 | 16 | 260/640 | |
| air J | Air swing | I | Ash | 1.0 | 18 | 12 | 180/420 | |
| air ↓J | Bell pogo | I | Ash | 0.9 | 12 | 10 | 100/300 | |
| air K | Bell plunge | I | Ember | 1.8 | 90 | 20 | dive | on a foe mid-air: 1.8 + bounce; to the floor: landing blow 1.8 + shock ring r 44 (0.4) |
| L | Heavy roll | I | | | | 18 | 480 | 0.26 s i-frames, 66 px |

Mastery: II Chime spin + three-note tolls (Mending); III Encore; IV echo wave (Perform / Encore +0.6 out to 64 px);
V Grand toll (a Perform with a full staff stuns small foes and adds 60 stance damage to bosses). Every attack routes I to
Perform (the press is latched during the move and plays at its end). Holding K through any swing starts the wind-up as it
ends (the heavy group's `hvHoldEnd`).

## Bench (tools/shots/v15/bell/bench.js, dummy, infinite stamina, 12 s per route)

| Route | Rank | dmg/s |
|---|---|---|
| **J J J (main loop)** | I | **2.45** |
| J J J + Fury | I | 2.65 |
| K K | I | 2.32 |
| J J J → K (knell) | I | 2.26 |
| J → K (backswing) → J | I | 2.18 |
| J J J → I (Perform each loop) | I | 2.09 |
| K K → I | I | 2.14 |
| ↑J ↑J → I (Echo) → J J J | I | 2.13 |
| J J J → I, Fury + Echo kept up | I | 2.80 |
| J J J → I → I (Encore) | III | 2.00 |
| J J J → I with the echo wave | IV | 2.29 |
| wind-up toll loop (0.7 s holds) | I | 1.60 |

(The mixed J/K routes are pressed mechanically; a press dropped by the finisher mash rule shifts the pattern, so their hit
tallies mix in neighbouring moves -- the dmg/s is still that loop as played.)

Main loop J J J 2.45 (2.65 with Fury); every alternative sits below it; a Perform costs ~0.35 dmg/s while you play it and
pays back through the buffs. Boss bench (boss.js: Gravetusk held in place swinging every 2 s, real stamina, 30 s):
plain J J J **1.08** (the nine on the same bench: 0.75-1.31; maul 1.09, greatsword 0.98, longsword 0.99); notes into a
Perform every ~6 s (Fury / Swiftness up, K slams mixed in) **1.38**, 2 boss staggers in 30 s vs 1.

## Deviations from Part C and why

- **Numbers.** The table's J J J was 2.02 dmg/s, under the 2.4-2.8 target; light chain raised to 1.1 / 1.15 / 1.8 and
  sped up (460 / 460 / 720) → 2.45. Forward slam 1.4 → 1.5, double slam 1.0 → 1.05 ×2 and 900 → 880 ms (K K 2.32, below the
  main loop). Wind-up toll 2.2 / 70 → 2.4 / 80 (a held punish at 1.6 dmg/s should hit like one).
- **Notes ring on hit, not on swing** -- see above; it also keeps the Perform loop from being free.
- **Added moves** for parity with the nine (20 moves + 4 toll entries in the Move List): Knell (J J J → K), Falling peal
  (↑J → J), and the hold-K wind-up is its own stance tag; the plunge is the bell's own move (heave, dive, landing tag)
  instead of the shared plunge.
- **Bell drop** (L → K) is rank I as in C5 (the skeleton had it at II).
- **Weapon art restyled** (`player_v15_bell.py` sets `G.WPN['dirge_bell']`): the platform's bell was a gold outline round a
  dark body and read as a hollow frame against the armour; now cast iron shaded across its width with a black rim, gold
  only at the lip and one sound-bow band, a dark mouth with the clapper, rune-cut ember glints, a slightly larger head.
- **Default weapon art** stays the borrowed War Cry (it fits the rallying-buff identity); no new art.

## Decisions for the owner
- Notes on hit (current) vs on swing (Monster Hunter's horn rings on the swing, which allows buffing before a fight).
- Fury +8% / Swiftness +25% / Iron hymn 20% are the C5 values; the balance agent may want Fury at +6% if Perform loops
  end up too strong with the cores.

## Tests
- `routes.js` 50/50: every move from real inputs (all 20 play their own `wb_*` tag, no fallback), the J J (pause) J rank gate
  and both-sides reach, K tap / hold / held-through-a-swing, every toll and its effect (regen x1.25, Fury x1.08, Iron hymn
  holding through a 10% hit, Echo's 3 re-rings at 30%, Mending 10% over 10 s and its 60 s cooldown, buffs ending at 30 s),
  Perform with an empty staff denied, Encore gated at III and refreshing, the IV echo wave reaching 56 px, V's stun and +60
  boss stance, blunt x1.3, wind-up armour, roll / air / plunge (mid-air bounce and floor shock), mashing stops at the clang,
  turning between steps, a weapon change dropping the staff and buffs.
- The platform's skeleton check (`tools/shots/v15/platform/types.js`) now fails two bell lines by design: K is `wb_slam`
  (the skeleton expected `wb_heavy`) and L → K is rank I as in C5 (the skeleton gated it at II). The lead may want to drop
  those two skeleton assertions for the bell. `tools/shots/wm/mech.js` passes.
