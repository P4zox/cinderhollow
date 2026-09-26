# Cinderhollow — Expansion 2 build contract (read fully before touching anything)

This round adds **6 optional side regions, 1 secret portal region and 1 secret boss/ending**. The story still ends at the
Pale Sovereign; everything here is optional content woven into the existing world. **`docs/EXPANSION_CONTRACT.md` still
applies in full** (ground rules §0, registries/hooks §3, boss conventions §3.5, cutscenes §3.6) — read it first. This
file adds the round-2 ownership, zones, anchors, ids and the lessons from player bug reports.

## 0. Lessons from playtest bug reports (mandatory)
- **Bosses must never leave their arena or clip into terrain.** Clamp every movement (walks, dashes, leaps, vaults,
  teleports, knockback) to the arena bounds between its fog walls (override `L`/`R` like `Oswin` in `24_secrets.js`),
  keep ground bosses on the floor line, and never let a leap target lie inside a wall or beyond a fog wall. Test the
  arena edges explicitly (pin the player against each fog wall and force every movement move).
- **Every room must be enterable and exitable** without hidden inputs. If an exit needs ↓+Space (drop through a thin
  floor), show a prompt/marker (see the Cindervane arena and the ink stair). Never leave the player standing somewhere
  with walls at head height on both sides and no way off. Test walking in and out of every room, both directions.
- **Barriers can't be jumped over**: gates/seals must reach the ceiling (or have wall above them).
- **Consistent body proportions across all frames** of a creature (same head/limb/torso sizes in every animation), no
  limbs detaching, no sliding feet, no floating above or sinking below the floor line, no physics jitter. Review
  contact sheets of every animation side by side for proportion drift before you finish.
- Ground-slam/plunge exploits are now rate-limited globally (two in a row); don't add unlimited-bounce mechanics.

## 1. Ownership (in addition to the old table; everything not listed is read-only — use `NEEDS:` lines)
| Agent | Region / job | Files you own | Asset prefixes |
|---|---|---|---|
| **T** | Thornveil Wood (biome `thornveil`) | `tools/regions/70_thornveil.py`, `web/src/30_thornveil.js`, `art/gen_thornveil*.py`, `art/thornveil_*.py` | `tiles_thornveil`, `bg_thornveil_*`, `tv_`, `warden*`, `coven*`, `fx_tv_` |
| **B** | The Drowned Barrows (`barrows`) + **Tidebreath swimming (global)** | `tools/regions/71_barrows.py`, `web/src/31_barrows.js`, `art/gen_barrows*.py`, `art/barrows_*.py` | `tiles_barrows`, `bg_barrows_*`, `db_`, `choir*`, `ferryman*`, `fx_db_` |
| **C** | The Crimson Manor (`crimson`) | `tools/regions/72_crimson.py`, `web/src/32_crimson.js`, `art/gen_crimson*.py`, `art/crimson_*.py` | `tiles_crimson`, `bg_crimson_*`, `cm_`, `sanguine*`, `butler*`, `fx_cm_` |
| **N** | Necropolis of Vael (`necropolis`) | `tools/regions/73_necropolis.py`, `web/src/33_necropolis.js`, `art/gen_necro*.py`, `art/necro_*.py` | `tiles_necropolis`, `bg_necropolis_*`, `nv_`, `vael*`, `executioner*`, `fx_nv_` |
| **DU** | The Sunscorched Dunes (`dunes`) | `tools/regions/74_dunes.py`, `web/src/34_dunes.js`, `art/gen_dunes*.py`, `art/dunes_*.py` | `tiles_dunes`, `bg_dunes_*`, `du_`, `pharaoh*`, `scarab*`, `fx_du_` |
| **SF** | The Starfall Crater (`starfall`) + **Moonstep triple jump (global)** | `tools/regions/75_starfall.py`, `web/src/35_starfall.js`, `art/gen_starfall*.py`, `art/starfall_*.py` | `tiles_starfall`, `bg_starfall_*`, `sf_`, `astrel*`, `orrery*`, `fx_sf_` |
| **NH** | NEO-HALLOW (`neohallow`, secret portal region) | `tools/regions/76_neohallow.py`, `web/src/36_neohallow.js`, `art/gen_neo*.py`, `art/neo_*.py` | `tiles_neohallow`, `bg_neohallow_*`, `nh_`, `saint0*`, `enforcer*`, `fx_nh_` |
| **V** | Sister Venn secret boss + 4th ending | `web/src/37_venn.js`, the ending/choice section of `web/src/10_story.js` (ENDINGS, beginEnding, Venn's post-Sovereign dialogue), `art/gen_venn*.py`, `art/venn_*.py` | `venn_boss*`, `fx_vn_`, `story_end_venn*` |
| **W** | New weapon classes **scythe** + **whip**, all new weapon overlays + boss-weapon SIGS | `art/gen_player.py`, `web/src/04_player.js`, `web/src/04b_sigs.js`, new `web/src/15_weapons2.js` | `player*`, `wpn_*`, `wpn_fx_*` |
| **G** | New spells, charms, arts + all new icons | new `web/src/16_gear3.js`, new `art/gen_ui5.py`, new `art/gen_fx5.py` | `ui_icons5`, `fx_g2_` |

Builds: `BUILD_OUT=web/dist/<agent>.html python3 web/build_web.py` (lower-case agent letters). Test scripts go in
`tools/shots/<agent>/` so they don't overwrite each other.

## 2. World zones and anchors (global tile coords; stay inside your zone; `python3 tools/rooms.py --show` for maps)
| Region | Zone | Anchor (only old room you may patch) | Gate |
|---|---|---|---|
| Thornveil Wood | x −140…95, y 15…41 | `C2` (Ossuary) **top wall**: open a few cells of row 0 and climb up into the wood | a climb that needs wall-jump (early region, after Gravetusk) |
| Drowned Barrows | x 253…372, y 29…69 (DB1 at gy 28, directly under K2) | `K2` (Flooded Aisle) **floor** — avoid K2's spike pit (cols 12–14) and slam cache (cols 24–26) | a flooded crypt crossed with Root Hook |
| Crimson Manor | x 373…451 for y 29…69, plus x 332…451 for y 70…83 (CM1 starts at x 332, touching M5) | `M5` (Kalden's Vigil) **east wall** (col 35) | a blood veil that needs Ember Dash (reuse the ash-veil `%` mechanic or your own tile) |
| Necropolis of Vael | x −60…149, y 57…140 (NV1 at y 56, directly under C2) | `C2` **floor** (rows 11–13, pick cols clear of existing features) | an underwater passage that needs **Tidebreath** (B's deep-water tile) |
| Sunscorched Dunes | x 400…600, y 84…170 (don't touch D-rooms, x ≤ 399) | `D3` (Slag Wards) **east wall** (col 47) | a sand chasm crossed by gliding (Gale Cloak) |
| Starfall Crater | x 470…760, y −100…−16 (rooms above the outdoor Crown rooms X3–X5, x 444…563, must end at y ≤ −16 unless they are your connector) | `X4` (Crown Shrine) **top edge** — connector room with an open bottom | Cinder Slam + Moonstep inside (late region) |
| NEO-HALLOW | x 1000…1300, y −50…100 (disconnected; reached only by portal) | one hidden spot of your choice in an old room **not** listed as anyone's anchor (behind a breakable wall `B`, a Slam floor or a hook ledge), plus 2–3 subtle "glitch" hints in other old rooms | the secret portal itself |
| Sister Venn | the Sovereign's arena `X5`, after she dies | — | refusing the final choice |

## 3. Tiles, abilities, shared mechanics
- Tile chars/ids (register with `registerTile`): Thornveil `(` `)` ids 35–39 · Barrows `"` (deep water) `` ` `` ids 40–44 ·
  Crimson `[` `]` ids 45–49 · Necropolis `{` `}` ids 50–54 · Dunes `-` `/` ids 55–59 · Starfall `+` `?` ids 60–64 ·
  NEO `!` `1` `2` ids 65–69.
- **Tidebreath** (item id `tidebreath`, granted by the Drowned Choir): B implements swimming in the deep-water tile `"`
  **globally** (any room): swim in all directions, breath meter, drowning/push-out without the item. N uses `"` for the
  Necropolis gate. Put B's physics in an `update` hook keyed on the tile, not on the biome.
- **Moonstep** (item id `moonstep`, granted by Astrel): SF implements a third jump **globally** via hooks (e.g. an extra
  `P.airJumps` once per airtime when owned).
- New traversal item icons are drawn by G (`i_tidebreath`, `i_moonstep`).

## 4. Id registry
**New weapon classes** (W): `scythe` (wide sweeping arcs that pull foes in; heavy = reaping sweep that heals a little on
kill), `whip` (long reach, hits both sides at the end of the lash; heavy = chain pull that drags small foes to you).
**Weapons** (★ boss weapon with SIGS by W; class in brackets):
Thornveil `antler_scythe`★ [scythe] (Warden), `briar_scythe` [scythe] (found), `thornwood_staff` [staff] (found) ·
Barrows `choir_harpoon`★ [spear] (Choir), `tidecleaver` [great] (found), `barnacle_fang` [dagger] (Ferryman) ·
Crimson `sanguine_rapier`★ [sword] (Countess), `carving_knife` [dagger] (Butler), `crimson_scythe` [scythe] (found) ·
Necropolis `vael_greatsword`★ [great] (Vael), `headsman_chain` [whip] (Executioners), `gravechain` [whip] (found) ·
Dunes `pharaoh_khopesh`★ [sword] (Pharaoh), `sun_sceptre` [staff] (found), `scarab_spear` [spear] (Scarab Knight) ·
Starfall `starblade`★ [katana] (Astrel), `meteor_maul` [great] (found), `orrery_whip` [whip] (Orrery Sentinel) ·
NEO `saint_lance`★ [spear] (SAINT-0), `plasma_katana` [katana] (found) · Venn `last_kindling`★ [scythe] (Venn).
**Arts** (G): `reap` (briar_scythe), `harvest_moon` (antler_scythe), `lash` (gravechain), `chain_drag` (headsman_chain),
`blood_frenzy` (sanguine_rapier), `tidal_surge` (choir_harpoon), `solar_flare` (pharaoh_khopesh), `starfall` (starblade),
`overclock` (plasma_katana), `pale_pyre` (last_kindling). Other new weapons use existing arts.
**Spells** (G): `bramble_snare` (Thornveil found), `drowning_hymn` (Choir), `blood_lance` + `crimson_rite` (Crimson found / Countess),
`soul_chains` (Vael), `sunbeam` (Dunes found), `sandstorm` (Pharaoh), `comet` (Starfall found), `pulse_shot` (NEO found),
`null_field` (SAINT-0).
**Charms** (G defines; effects tied to a region mechanic are implemented by that region's agent via `charmOn`):
`c_antler` (Warden), `c_moss` (Thornveil found), `c_gill` (Barrows found: longer breath — B implements), `c_pearl` (Choir),
`c_bloodvial` (Crimson found), `c_countess` (Countess), `c_crown` (Vael), `c_court` (Necropolis found), `c_scarab` (Dunes found),
`c_sun` (Pharaoh), `c_star` (Astrel), `c_orrery` (Starfall found), `c_hack` (NEO found: reveals breakable walls — NH implements),
`c_neon` (SAINT-0), `c_lastflame` (Venn).
**Boss kinds + rewards** (`BOSS_INFO[kind].reward`):
`warden` → `w:antler_scythe, c_antler, shard` · `coven` (mini) → `sp:bramble_snare, emberstone` ·
`choir` → `tidebreath, w:choir_harpoon, sp:drowning_hymn, c_pearl` · `ferryman` (mini) → `w:barnacle_fang, emberstone` ·
`sanguine` → `w:sanguine_rapier, sp:crimson_rite, c_countess` · `butler` (mini) → `w:carving_knife, emberstone` ·
`vael` → `w:vael_greatsword, sp:soul_chains, c_crown` · `executioners` (mini, duo) → `w:headsman_chain, shard` ·
`pharaoh` → `w:pharaoh_khopesh, sp:sandstorm, c_sun` · `scarab` (mini) → `w:scarab_spear, emberstone` ·
`astrel` → `moonstep, w:starblade, c_star` · `orrery` (mini) → `w:orrery_whip, shard` ·
`saint0` → `w:saint_lance, sp:null_field, c_neon` · `enforcer` (mini) → `emberstone, shard` ·
`venn` → `w:last_kindling, c_lastflame` (+ 4th ending).
Found loot per region (place in chests/items): the "found" weapons/spells/charms above + emberstones and a shard.

## 5. Difficulty tiers (boss HP before NG+; all multi-phase with cutscenes for main bosses)
Thornveil early: Warden 2000 (coven 3×500) · Barrows mid: Choir 3000 (ferryman 1400) · Crimson mid: Countess 3200 (butler 1500)
· Necropolis mid-late: Vael 3800, 3 phases incl. his spectral court (executioners 2×1000) · Dunes late: Pharaoh 4000
(scarab 1800) · Starfall late: Astrel 4800 — hardest optional boss except the First Ember (orrery 2000) · NEO secret:
SAINT-0 4500, 3 phases (enforcer 2200) · Venn 5000, 3 phases, final-boss tier.
Enemies: `BIOME_TIER` in `06_enemies.js` already scales every enemy in your biome (thornveil 0.9, barrows 1.2, crimson 1.25,
necropolis 1.4, dunes 1.6, starfall 1.8, neohallow 1.7 × HP) — author base stats at roughly the old-region level.

## 6. Design direction per boss (dark mythology, cool, sleek; see the taste rules in EXPANSION_CONTRACT §0)
Reference images from the user: `art/concepts/ref_antlered_warden.png`, `ref_drowned_choir.png`, `ref_king_vael.png`
(follow them closely: silhouette, palette, key features). The Countess, Astrel, the Pharaoh, SAINT-0 and Venn have no
reference — the user said "surprise me": design them yourself to the same bar (see the prompts in the conversation
summary below) and keep proportions unified.
- **Antlered Warden**: towering gaunt forest god of dark twisted wood, huge branching antlers with moss and pale ribbons,
  small deer-skull face with glowing green eyes, long thin arms, living-wood staff with thorned vines, root cloak.
- **Drowned Choir**: colossal serpentine leviathan of fused drowned corpses, eel body, narrow skeletal fish head with needle
  teeth, a crest of screaming choir faces along its back, teal bioluminescent glow, dripping black water.
- **King Vael**: undead king in corroded gold/bone armour, spiked crown fused to a skull with pale blue ghost-fire eyes,
  tattered purple cape, massive bone greatsword, spectral chains; his court = spectral knight, priest, executioner.
- **Countess Sanguine**: tall slender vampiric noblewoman, crimson gown with high collar, porcelain skin, blood rapier;
  phase 2 gown becomes a torrent of blood with blood wings.
- **The Veiled Pharaoh**: tall mummified sun-king, gold linen, sun-disc crown, gold death mask with one amber eye slit,
  khopesh + sun sceptre, a sand cloak; sandstorm phase.
- **Astrel, the Fallen Star**: celestial swordswoman, obsidian/glass armour with starlight cracks, orbiting star-fragment
  halo, nebula hair, faceless silver mask, starlight blade; rotating constellation arena.
- **SAINT-0, the Null Saint** (cyberpunk — the one deliberate break from mythology): sleek white/chrome AI angel, faceless
  visor, six holographic panel wings, cyan/magenta circuit lines, data-ring halo, energy lance; phase 3 wireframe
  cyberspace arena. NEO-HALLOW is a neon rain-soaked megacity built on the fossilised Pale Root (synthwave music).
- **Sister Venn, the Last Kindling**: slender priestess in ivory and ash robes, pale-flame veil, white fire halo, root-and-
  flame scythe; phase 2 veil burns away, rootfire wings; phase 3 near-silent, very fast. Fought only if the player
  **refuses** the final choice after the Sovereign → 4th ending "The Ember Unbound".
