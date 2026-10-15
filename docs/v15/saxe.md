# v15 Switch Axe (`saxe`, weapon Gravegrinder): build write-up

Owner's ask: "switch axe (blade to charge, press I to switch once it fully charges into axe chainsaw, massive damage but
5 star difficulty on mastering, so charging the blade need to be hard)". Spec: WEAPON_REVAMP.md C1. Built in
`web/src/78_mech_saxe.js` (moves, gauge, HUD, feedback) and `art/player_v15_saxe.py` (29 tags + the morphing weapon).
Tests: `tools/shots/v15/saxe/routes.js` (47 checks, all pass), `bench.js`, `bossfight.js` (run with
`tools/shots/v15/balance/run.sh`), `snaps.js` + `montage.py` (in-game shots: `out/montage.png`, HUD: `out/hud.png`).
Art previews: `tools/shots/v15/saxe/prev/` (`blade.png`, `axe.png`, `axe2.png`, `forms.png`: the morph strip,
`generic_axe.png`: the shared tags drawn as the axe).

## The weapon has two forms, and they morph

**The shape.** The Gravegrinder is one jack-knife mechanism, drawn by a single blade-space shape. Its geometry follows a
form `(slide, rot)`, where both values run from 0 to 1:
- **rot:** the sword blade swings 180° round a gold hinge pin and out through the open side. At 0 the blade points
  straight ahead (the **sword**). At 1 it is folded back along the haft with its edge tucked in (the **axe**).
- **slide:** the toothed axe head rides the telescoping haft. At 0 it is folded flat at the hilt, where it reads as a
  toothed housing on the blade's back. At 1 it has slid out to the end of a long haft, opened into the axe head. The
  chain teeth on its edge crawl from frame to frame (the chain phase).

**The morph tags** (`sx_morph`, `sx_unmorph`, `sx_release`'s ending, `sx_vent`) step the form one frame at a time, in a
mechanical order:
1. unlatch
2. swing the blade round
3. slide the head along the haft
4. lock with a clank and a flare at the pin

The pose keeps moving the whole time. For example, the Morph slash hoists the sword overhead, the blade swings back
against the sky, the head rides up the haft and locks, and then the axe comes down into the floor. The sound has two
parts: a click as the latch opens, then a clank when it locks.

**How each tag gets the right form.** `sxseq()` stamps a form on every weapon cel of an sx_ tag (`w.sxf`), and a small
hook on `Wpn.render` feeds that form to the shape. Shared tags (idle, run, roll, jump, hurt, heal and so on) carry no
form of their own, so two overlays are built from the same shape:

| Overlay | Shared tags drawn as | sx_ tags |
|---|---|---|
| `wpn_gravegrinder` | the **sword** (blade mode, where you spend most of the fight) | their own form |
| `wpn_gravegrinder_axe` | the **axe** (rolling, jumping or getting hit in axe mode shows the axe; the run drags the head along the floor) | their own form |

`gravegrinder_axe` is registered in `G.WPN`, `G.SMEAR` and `WPN_IDS` from `register()`, so `gen_player` builds the
second overlay by itself.

**Runtime.** `78_mech_saxe.js` wraps `sheet()`. While `P.sxAxe` is set, `sheet('wpn_gravegrinder')` returns the _axe
sheet. Every place that draws the weapon calls that function, so they all follow with no shared-file edits: 09_main,
the MV ghosts, 77_cores' enchant glow, 61_feel's tip, 43_systems and 31_barrows. This is the cleanest single point I
found. A per-mode field on WEAPONS would have meant editing about six readers.

**Cost.** One more overlay sheet: about 0.5 MB of PNG and 0.1 MB of frame JSON in the test HTML, plus a chunk in the
release build. It is lazily decoded, like any other sheet.

## The Switch Gauge (hard to fill, as asked)

| Rule | Value |
|---|---|
| Landed blade hit (real foes only, once per hit index) | +4 (**+7 on the beat**: the press came in the move's last 150 ms) |
| Edge rush (J×4 finisher) | +10 (+13 on the beat) |
| Ratchet cut, per tooth | +3 |
| Ratchet twist (K K) | +12, only if both bites land |
| Hone (hold K): rooted, open | +10/s |
| A blade swing that finds nothing with a foe within 90 px | −10 |
| Taking damage (any hit that gets through) | −25 |
| 2 s without attacking | −4/s |
| At 100 | **locks**: no losses; the weapon glows ember and "I" pulses on the HUD |
| I below 100 | a dry rev (sputter, a puff of smoke), nothing else |

**Axe mode.** The gauge starts at 100 and drains 6/s, plus 4 for each axe move that lands (once per move), plus 15/s
while grinding. Overdrive (Mastery IV) cuts all of it by 30%. At 0 the axe **vents**: steam, the head folds shut, and you
stand in a 0.6 s stagger where you cannot act. Full Release and Morph back empty the gauge without venting.

**I in axe mode:**
- **Full Release** (Mastery III, gauge ≥ 40): deals 3.0–6.0, scaling with the gauge.
- **Morph back:** a rising cut, used below 40 or before Mastery III.

**HUD** (right of the stamina bar, at y 21, 38 px wide):
- **The bar:** amber while it fills; white-gold and breathing when locked; red while it drains in axe mode.
- **The Release line:** a tick at 40 once Full Release is unlocked. The bar goes darker red below it.
- **Feedback:** a flash on gain, and a red frame on loss.
- **The form glyph:** a sword or an axe head, left of the bar.

**In the world:**

| Moment | Feedback |
|---|---|
| Locked full | ember glow on the whole weapon, breathing; ember light and cinders |
| Axe mode | a hotter red glow and fire motes |
| Hone | sparks and light at the point |
| Grind | sparks and light at the head; a chainsaw buzz on each bite |
| Vent | a steam plume |
| Lock moment | chime, sparks, flash |

## Moves (final numbers)

Dmg is in light-AR multiples. Times are wind-up/total in ms. The rank is the Mastery rank (I means from the start).

### Blade mode

| Input | Move | Rank | Wind/Total | Dmg | Poise | Stam | Purpose |
|---|---|---|---|---|---|---|---|
| J | Rising edge | I | 140/360 | 0.9 | 10 | 10 | |
| J J | Falling edge | I | 140/360 | 0.95 | 10 | 10 | |
| J J J | Double slash | I | 160/420 | 0.55 ×2 | 16 | 12 | two gauge hits |
| J J J J | Edge rush | I | 220/560 | 1.3 | 30 | 14 | finisher, lunge 24, +10 gauge |
| J J (pause) J | Ratchet cut | II | 160/600 | 0.6 ×3 | 24 | 14 | 110–450 ms after the 2nd cut ends; J goes on to the Edge rush |
| K | Phial thrust | I | 240/600 | 1.3 | 28 | 16 | |
| K K | Ratchet twist | I | 200/640 | 0.7 ×2 | 30 | 16 | +12 if both land |
| J K | Hook heave | I | 220/620 | 1.2 | 34 | 14 | lifts light foes; J goes on to the Falling edge |
| hold K | Hone | I | loop | – | – | 0 | +10/s, rooted; J, L or I (when locked) leaves it |
| ↑J | Skyward edge | I | 160/400 | 1.0 | 14 | 12 | |
| L → J | Lunging edge | I | 140/400 | 1.1 | 14 | 12 | |
| air J | Air edge | I | 150/330 | 1.0 | 12 | 12 | |
| air ↓J | Pogo | I | 100/300 | 0.9 | 12 | 10 | both forms |
| air K | Plunge | I | shared | 1.3 | 45 | 16 | |
| L | Roll | I | 420 | – | – | 16 | |
| I (gauge 100) | **Morph slash** | I | 300/700 | 2.0 | 60 | 0 | armour < 35% max HP; the axe arrives on the hit; J goes to Wild swing, K to Rev thrust |

### Axe mode

All axe moves have armour against blows under 25% max HP.

| Input | Move | Rank | Wind/Total | Dmg | Poise | Stam | Purpose |
|---|---|---|---|---|---|---|---|
| J | Axe overhead | I | 420/920 | 2.9 | 45 | 16 | slam |
| J J | Wild swing | I | 400/900 | 3.2 | 50 | 18 | |
| J J J | Grinder sweep | I | 360/1100 | 0.9 ×5 | 70 | 20 | finisher |
| K | Rev thrust | I | 300/900 | 0.6 ×4 | 50 | 16 | |
| hold K | **Chainsaw grind** | I | loop | 0.28 / 80 ms | 8/bite | 0 | walk at 30%; +15/s drain |
| K K | Ripping heave | II | 420/1000 | 2.6 | 80 | 20 | launches |
| ↑J | Rising grinder | I | 300/760 | 1.5 | 40 | 16 | |
| air J | Falling cleave | I | 200/520 | 1.4 | 40 | 16 | |
| air K | Axe plunge | I | shared | 1.8 | 90 | 20 | |
| L | Heavy sidestep | I | 520 | – | – | 18 | 34 px, i-frames 0.22 s; L → J goes to the overhead |
| I (≥ 40) | **Full Release** | III | 500/1500 | 3.0–6.0 | 120 | 0 | lunge, 8 bites (0.25 each) and a burst (1.0), all × (1 + (g − 40)/60); armour 35%; commit; folds back to the blade |
| I (< 40) | Morph back | I | 260/620 | 1.4 | 40 | 0 | |
| (gauge 0) | Vented | – | 600 | – | – | – | can't act |

### Mastery

| Rank | Unlock |
|---|---|
| II | Ratchet cut, Ripping heave |
| III | Full Release |
| IV | Overdrive (drain −30%) |
| V | Grinding halo: Full Release ends in a ring burst (0.8, 40 poise, fire) and refunds 30 gauge |

## Bench (`bench.js`, light-AR dmg/s, dummy, infinite stamina, real presses, the game's own hitstop)

| Route | dmg/s |
|---|---|
| blade J J J J (**main loop**) | **2.48** |
| blade J J J J on the beat | 2.47 (same damage; the beat buys gauge) |
| blade K K | 2.18 |
| blade J K | 2.25 |
| axe J J J (gauge held full) | **3.53** (the burst, while the gauge lasts) |
| axe K (rev thrust) loop | 2.60 |
| axe K K (II) | 2.65 |
| axe hold K grind | 3.24 (drains 21/s) |

**Gauge fill, from 0 to 100,** on the dummy where every blow lands:

| Route | Time |
|---|---|
| J J J J, early presses | 6.6 s |
| J J J J on the beat | 4.5 s |
| K K | 7.8 s |
| Hone | 10.2 s |

**Full cycle, 40 s:** fill on the beat, Morph slash, axe J J J until the vent, repeat.

| Rank | dmg/s | Notes |
|---|---|---|
| I | 3.02 | 3 morphs, 2 vents |
| III | 2.92 | cashing in 40–52 as a Full Release; no vents |
| V | 3.10 | the halo's refund |

**Against real bosses** (`bossfight.js`, the v15 balance bot, expected builds, 2 seeds each). The bot plays blade
J J J J in openings, morphs the moment the gauge locks, then plays axe J J J. For comparison:

| Boss | Switch Axe dps | Longsword | Greatsword |
|---|---|---|---|
| Hound | 1.03 / 0.82 | 1.00 / 0.99 | 1.00 / 0.95 |
| Warden | 0.22 / 0.22 | 0.26 / 0.24 | 0.25 / 0.24 |
| Kalden | 0.57 / 0.50 | 0.58 / 0.51 | 0.51 / 0.68 |
| Librarian | 1.00 / 1.03 | 0.94 / 0.90 | 1.19 / 0.90 |

- **Fills are rare against a boss:** the bot filled the gauge 0–1 times per fight. Hits taken cost it 25–560 gauge
  over a fight, so the gauge really is hard to earn.
- **When it does fill, the axe phase lifts the fight above the Longsword.** On the Librarian it killed in 50–51 s,
  against 61–64 s for the Longsword.
- **A bot that never fills plays like a Longsword.** It lands at about Longsword level.

A player who hits the beats, hones in safe windows and avoids hits gets the burst much more often. That is the
★★★★★ ceiling.

## Deviations from C1 and why

- **The gauge economy is tighter than the spec** (+4/+7 per hit instead of +6/+10; Hone 10/s instead of 12). The owner
  asked for the blade's charge to be hard. On a dummy, perfect beat timing takes 4.5 s to fill, against 3.6 s at the
  spec's numbers. On a boss, with roughly 1.3 s openings, −25 per hit taken and the idle bleed, a fill is several clean
  openings.
- **"4 per chainsaw hit" is read as once per landed axe move.** Per bite, the grind would empty the gauge in about
  1.4 s. The grind instead pays its +15/s on top.
- **Axe damage is raised** (overhead 1.6 → 2.9, wild swing 1.8 → 3.2, sweep 0.45 → 0.9 per bite, rev 0.5 → 0.6).
  At the spec's numbers the axe J J J measured about 1.9 dmg/s, below the blade's 2.48. That is not "massive damage",
  and not the "~3.5 while the gauge lasts" that C1 itself targets. The grind is 0.28 per bite, not 0.35, which keeps it
  under the axe J chain.
- **Morph back and Full Release clear the gauge to 0.** Full Release folds back to the blade with no vent stagger: the
  burst is the clean way out. A release cut short by a hit still folds back.
- **K and hold K share a start.** K starts the thrust or rev thrust at once. If K is still held 190 ms in (200 ms on the
  rev thrust) and was pressed for that move, it turns into the Hone or the grind. Taps get no extra latency.
- **The axe's ↑J (Rising grinder) and the heavy sidestep's tag are additions,** so that every weapon has an up attack.
  The air K plunge is the shared plunge, with numbers that depend on the mode.
- **No new weapon art.** It keeps Magma Quake (the grinder splitting the ground), as the platform set it.

## Decisions for the owner

- **Gauge difficulty:** these are the knobs at the top of 78 (`SX`). If filling should be harder or easier, `hit`/`beat`
  and `hurt` are the ones that matter.
- **Axe burst:** about 3.5 dmg/s while the gauge lasts. A full cycle on the dummy (fill, morph, axe until the vent)
  averages about 3.0, against 2.48 for the blade alone.
- **The second overlay** (`wpn_gravegrinder_axe`) costs about 0.6 MB. The alternative is axe-only tags for every shared
  action, which costs more frames.

## Shared files

None edited. The second overlay is registered from `art/player_v15_saxe.py`. That is one more entry in WPN_IDS, so every
art build writes `assets/wpn_gravegrinder_axe.*`. `sheet()` is wrapped from `78_mech_saxe.js`, as 61_feel wraps
`drawSprite`.

**Known test conflict:** the platform skeleton test `tools/shots/v15/platform/types.js` still expects a rank-II L → K
named `sx_rollk`, which no longer exists. On the Switch Axe, L → K is the Phial thrust in blade mode and the Rev thrust in
axe mode. That check fails by design. Every other saxe line passes, and `wm/mech.js` passes.
