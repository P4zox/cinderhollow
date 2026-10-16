# v17 brief: unique weapon arts for the Bow, Martial Arts and Warbell

The owner's rule: every weapon type must be unique. Three types still borrow another weapon's default art:
Bow → Backstep Slash, Martial Arts → Bloodstep, Warbell → War Cry. Each gets its own art, built to the same
standard as the v9 arts (web/src/16_gear3.js: `impl()`, the hold-to-charge contract, ART_IMPL, P.g2) and the
v14–v16 movesets: its own animation, its own effects and sound, its own icon. Tone: dark mythology, sleek,
never cartoony. Aesthetics and animation matter more than flashy effects; keep light and flash restrained
(one main light per effect, k ≤ 0.8; no screen-filling white).

Work on the current branch (`arts-spear`). **Do not commit, push or publish**; the lead commits. Other agents edit
the tree at the same time: touch only your own new files plus the small, named lines in the shared files below.

## The three arts (lead's design; refine the details, keep the identity)

### A1. Bow: **Ashen Volley** (id `ashen_volley`)
Kick off the foe into a back-flip (brief i-frames, ~0.25 s) and, at the top of the flip, loose a fan of three
burning arrows down and forward into the spot you just left. The arrows obey the bow's short-range rule
(they burn out at BW_RANGE). Hold: five arrows that stick and burst a beat later. Any arrow that lands raises the
bow's charge level by one (ties the art to the bow's chain). It punishes a foe that chases you, and it is the bow's
answer to being too close.

### A2. Martial Arts: **Litany of Fists** (id `litany`)
The art follows the current style:
- **Swift:** a stepping flurry of rapid palm and knuckle strikes (6–7 hits) ending in a rising knee that launches
  small foes. Hold: more strikes and a longer step.
- **Iron:** one planted, armoured "bell-breaker" palm that drives a short shockwave forward (heavy stance damage,
  shoves small foes). Hold: a bigger wave that also breaks guards.
If Focus (the perfect-dodge buff) is active, the art gets its Focus bonus too. No style switch happens.

### A3. Warbell: **Funeral Peal** (id `funeral_peal`)
Swing the bell overhead and drive it into the ground: a ring of sound expands both ways along the floor
(blunt stance damage, it swallows enemy missiles it touches), and the peal writes notes into the staff (design it
from the bell's note rules in web/src/78_mech_bell.js; for example one note per foe struck, or a fixed chord that
sets up a Perform). It must make the next Perform better, not replace it. Hold: the ring travels further and
stuns small foes.

## Contract

- **Registration:** `registerGear({ arts: { <id>: { name, fp, desc } } })` and an `impl()` the way 16_gear3.js does
  (put each art in its own new file: `web/src/81_art_bow.js`, `81_art_fist.js`, `81_art_bell.js`). Set the
  weapon's and the type's `art` in 77_types15.js (`ashstring`/`bow`, `penitent_knuckles`/`fist`,
  `dirge_bell`/`bell`; WEAPONS[...].art and WTYPE_INFO[...].art). Tune fp/cd via 60_wbal's WB_ART_TUNE pattern or
  your own table in your file. Check that old saves holding the borrowed art id still load and are corrected
  (60_wbal locks SAVE.art to the weapon's art; verify).
- **Animation:** dedicated tags `art_<id>` (and, if needed, extra tags with your prefix) drawn in a new module
  `art/player_v17_<type>.py` hooked into art/gen_player.py the way v15/v16 modules are (find `player_v16_fatal`).
  Use the type's real weapon (its overlay) and IK. Preview without a full build: `python3 art/player_preview.py
  rows out.png tag:kind`. A full build is ONLY via `tools/shots/v14/artbuild.sh` (mkdir lock, ~27 min; wait for the
  lock, never run two). Do as much as you can with previews before building.
- **Effects:** your own effect sprites if you need them (follow how fx_g2_* / fatality effects are drawn; procedural
  canvas drawing in your file is fine and keeps the build light). Sound with the existing tone()/noise()/sfx helpers.
- **Icon:** `a_<id>` in an icon sheet (see art/gen_ui15.py and how ui_icons15 is registered; add to it or make
  `ui_icons17` via a small new generator). The Esc / blacksmith / Move List screens must show the name, icon, desc.
- **Move List / combo hint:** if the art appears in the type's Move List (80_movehelp.js / 80b map), name it there.
- **Balance:** damage per FP in line with the other arts (look at WB_ART_TUNE and docs/weapon_balance.md); it must
  not beat the type's own best combos on boss time-to-kill. Measure.
- **Docs:** `docs/v17/<type>_art.md` (design as built, numbers, tests, open decisions). The lead updates
  WEAPON_REVAMP.md.

## Build and test

- Test build: `BUILD_OUT=web/dist/v17_<type>.html python3 web/build_web.py` (non-release, `window.__game`).
  Never write `web/dist/index.html` (tracked release file).
- Harness: `SHOT_HTML=$PWD/web/dist/v17_<type>.html sh tools/shots/wm/run.sh <test.js> <outdir>` with the
  helpers in tools/shots/wm/_prelude.js (W().reset(type, ...), dummy, tap/down/up, frame, E(eval)). Look at
  tools/shots/v16/fguard/paths.js for an example. Put tests in `tools/shots/v17/<type>/` (gitignored: list them in
  your report so the lead can `git add -f`).
- Tests must show: the art starts from the art key with the type equipped, costs its FP, the tap and hold versions
  both work, hits land and deal the intended damage, it ends in idle, no page errors; plus the art's own rule
  (charge level up / style variants / notes written). Also run `tools/shots/wm/run.sh tools/shots/wm/mech.js` and
  the type's v15 route test (tools/shots/v15/... or the type's routes.js) to confirm nothing regressed.
- Make snapshots (PNG frames) of the art in action so the lead can review the look.

## Report

Files changed, design as built, numbers, tests and results, snapshot paths, open decisions for the owner.
