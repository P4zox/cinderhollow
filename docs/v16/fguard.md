# v16 Fatalities: the guard group (role `fguard`)

Sword & Shield "Bulwark's End", Spear "Skypiercer", Bow "Point-Blank Pyre" (brief items 5, 7, 11).

Files: `web/src/79d_fatal_guard.js` (registrations, custom effects, the spear's guard-K hook), `art/player_v16_fatal_guard.py`
(tags `sh_fatal`, `sp_fatal`, `sp_fatal_vault`, `bw_fatal`; `python3 art/player_v16_fatal_guard.py` prints the frame check),
tests and contact sheets in `tools/shots/v16/fguard/`. No edits to shared files.

## 1. Bulwark's End (sns, 1500 ms, gold `255,212,120`)

| ms | beat | what you see |
|---|---|---|
| 0–220 | | step in behind the shield, sink low and coil behind its rim (a glint on the rim) |
| 222 | **bash** 1.0 | the shield driven out with the whole body: a small heater-shaped imprint of light flashes where it struck, a ring, sparks; small foes are rocked back 9 px and pinned |
| 350–560 | | a step in, the blade raised high and cocked point-down over the foe |
| 562 | **stab** 1.2 | the downward stab: a line of light along the blade through the foe, sparks spraying down-forward |
| 730–980 | | wrench free, haul the shield overhead rim to the sky; gold motes stream into it, the world darkens further |
| 1004 | **slam** 2.8 | slow-mo, boom, name. The shield hammered down rim-first: the **golden crest** (the shield's own heater outline, an inner outline, the ember-eye, the gold bar and cross-arm) blooms over the foe with an echo thrown outward and rays round it; ground rings, gold cracks, sparks, embers |
| 1080–1500 | | hold low under the crest (a glint sweeps down it), rise. The crest holds ~640 ms, then breaks up from its point and lifts off as gold motes (outlives the fatality) |

The crest is sized to the foe (85% of its hurtbox height, 42–74 px), drawn by `fgCrest` (scanline raster in the glow layer).

## 2. Skypiercer (spear, 1600 ms, storm blue `170,210,255`)

Two variants chosen at the start (`F.variant`, swapped in `start(F)`: steps, tag and share sum):

**Hoist** (small foes — the framework's `fatSmall`): `sp_fatal`.
impale (202, 1.0) → lever the spear up, arms driven high: the foe **rides the tip** (the framework's target motion
re-aimed every frame at the spear tip from a per-frame hand/angle table, `SP_HANDS`; ~17 px off the floor while held,
~28 px at the thrust) → a bolt out of the sky strikes the impaled foe (582, 0.8) and spirals down the haft in two strands
→ sink → **skyward thrust** (882, 3.2: slow-mo, boom, name) — a long lance of light along the haft through the foe into the
sky, crackle in the wound → the foe is flung off the tip (1030) and dropped (1190).

**Vault** (bosses, boss parts, elites — they never move): `sp_fatal_vault`.
impale upward into the chest (202, 1.0) → spring, swing up and over the lodged spear (the engine moves the body: the
pose keeps the spearhead at the wound, apex ~23 px up) → at the apex the bolt finds you and the lightning spirals down the
spear into the boss (770, 0.8) → **drive it home** (812, 3.2): your whole weight down the haft, the body drops with it; a
lance of light from above your head down through the wound into the floor, cracks and rings where it meets the floor,
crackle in the wound → wrench free and drop back (1060), land (1180).

Note: the player sheet can't draw below the feet line, so at the apex the spear's lower end is the frame bottom; the
geometry puts that end at the wound (a faint light line hums along the lodged haft).

## 3. Point-Blank Pyre (bow, 1500 ms, ember `255,145,60`)

kick chambered → **kick** (175, 0.8): a heel to the chest, a ring and grey sparks, small foes shoved back 10 px and pinned
→ three arrows on the string (the two outer shafts are drawn by the engine, fanned ±8° about the nock, on the real
arrowhead found by `bwTip()`), at full draw their heads smoulder → **loose** point-blank (682, 1.4): three arrows stand in
the foe in a tight fan (at least 24 px ahead of you), the wounds glow hotter → the bow swept down and away like a struck
match → **the pyre** (990, 2.8: slow-mo, boom, name): the arrows ignite into a burning cross — a stake from above them to
the floor and a crossbar through them, 3-px white-hot beams with flame tongues licking up (white root, orange body,
dithered red swaying tips), a dithered soot backing so it reads on bright bosses, embers, ground rings and a scorch; it
cools to ember red, breaks up from the ends and smokes away (~1.3 s). The arrows char.
The fatality draws its own arrows (no projectiles: the bow's 72 px burn-out doesn't matter at point-blank).
New primitive in my file: `FATFX.fgPyre` (glow + lit + smoke).

## 4. Tests (`tools/shots/v16/fguard/`, `SHOT_HTML=web/dist/v16_fguard.html sh tools/shots/wm/run.sh <test> <out>`)

- `arenas_<type>.js` (framework `arenas.js` per type): omen, twins (duo), executioners (duo), warden, hound.
  All 15 runs: 5.0 × AR (sns 5.01, spear 5.00, bow 5.02 — rounding of the mid-rand), invulnerable mid-fatality (blow,
  spikes, projectile), the other body of the duos never moves, boss released, recovery 26–37 frames, the boss attacks
  again, player idle after. Results `arenas_<type>.txt`.
- `foes.js`: hollow soldier with real K on a broken stance. Tough foe 8.0 × AR (7.98 / 8.01 / 8.00), weak foe executed
  (the last beat kills), elite: 8 × AR and the spear picks the vault (foe never moves, the player rises 24 px); hoist:
  foe lifted (14 px while it's held on the tip for a weak foe executed at the thrust, 30 px peak for a tough one thrown
  off the tip), lands after; invulnerable, released, idle, J acts after. `pass: true`. Results `foes.txt`.
- `paths.js`: K out of the held guard (sns parry-guard, spear heavy guard — needs my hook), K held (the bow's draw does
  not steal it), J then K latched mid-move (sns, bow), Move List rows name the fatality. Spear J→K is informational: by the
  time sp_1 ends the foe has slid past the 34 px crit range, so the latched K plays sp_jk as the framework intends.
- Framework regression on `web/dist/v16_fguard.html`: `fatality/tests.js` 27/27 (its "every primitive" check now also
  spawns my `fgPyre` with empty options — it defaults everything), `fatality/types.js` all 14 types pass
  (`fw_tests.txt`, `fw_types.txt`).
- `snaps_<type>.js` + `sheet.py`: `sns_boss_sheet.png`, `sns_foe_sheet.png`, `spear_boss_sheet.png`,
  `spear_foe_sheet.png`, `spear_warden_boss_sheet.png`, `bow_boss_sheet.png`, `bow_foe_sheet.png`; art previews in `prev/`.

## 5. Notes for the lead

- The spear's heavy guard handles K itself (76_mech_guard.js `guardUpdate` → `sp_heavy` / counter), so the framework's K
  paths never saw it: `79d_fatal_guard.js` wraps `MV.types.spear.guardUpdate` (fatality first on a critable foe).
- Lights: one main light per effect, k ≤ 0.8; the boss's own white hit flash shows on the first beats (as in the
  reference).
