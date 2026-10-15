// ------------------------------------------------------------------ Weapon revamp: the nine types (agent WS, docs/WEAPON_REVAMP_CONTRACT.md)
// The 50 weapons became 9, one per type. This file owns:
//   * the types: WTYPES, WTYPE_INFO, wtype(), wcls() (returns the type id), WEAPON_CLASS (the 9 weapon ids -> type ids)
//   * Weapon Mastery (WEAPON_REVAMP.md §A11): masteryRank / masteryXP / masteryGain, MASTERY_XP; XP for hits, kills, elites
//     and bosses; rank-up banners; mastery carries into New Game+
//   * the unlock lists (WM's WEAPON_UNLOCKS from 75_moves.js, else the Mastery tables of WEAPON_REVAMP.md)
//   * the shared UI: type cards, the looping preview, rank pips, XP bars, unlock lists. Used by the New Game weapon select
//     (64_diffmode.js), the shrine "Change weapon" screen (08_ui.js), the Esc mastery screen (29_ui2.js) and the skill
//     tree's Weapon Mastery page (58_skilltree_ui.js)
//   * loot conversion (room items, boss rewards, shops: Emberstones + cinders) and the old-save migration (contract §5)
// Saves: SAVE.weapons { weaponId: +lv } holds all nine; SAVE.mastery { type: xp }; SAVE.masteryBoss { kind: 1 } (first
// kills, for the 300 XP bonus); SAVE.wv = 9 marks a migrated / new save.

const WTYPES = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip'];
const MASTERY_XP = [0, 300, 900, 2000, 4000];
const WM_ROMAN = ['I', 'II', 'III', 'IV', 'V'];
// { weapon, name, art, prefix, desc (identity), icon } per the contract, plus what the select screen shows
const WTYPE_INFO = {
  longsword: { weapon: 'longsword', name: 'Longsword', art: 'crescent', prefix: 'ls_', first: 'attack1', diff: 1, mech: 'Parry and riposte',
    desc: 'Balanced in everything and easy to learn, with a branching combo that teaches the rest of the game.',
    str: 'Good reach, decent speed, a parry with a payoff, no hard commitments but the finisher.',
    weak: 'No specialty: less burst than the Katana or Greatsword, less defense than the Shield or Spear.' },
  katana: { weapon: 'katana', name: 'Katana', art: 'moonwave', prefix: 'kt_', first: 'kt_1', diff: 4, mech: 'The sheathe and the Iai draw',
    desc: 'Fewer, bigger cuts drawn from the sheathe. You win by setting up the draw.',
    str: 'The fastest heavy in the game, huge burst, a strong counter, a nimble sidestep.',
    weak: 'No real block; the flurry staggers poorly; caught sheathed and slow is deadly.' },
  greatsword: { weapon: 'greatsword', name: 'Greatsword', art: 'stormleap', prefix: 'gs_', first: 'gs_1', diff: 3, mech: 'Charge levels',
    desc: 'Slow, heavy and patient. Read the foe, pre-charge, and release into its opening.',
    str: 'The biggest single hits, a charge that can’t be flinched, stance breaking.',
    weak: 'The slowest roll and the weakest light attacks; every miss is punished.' },
  maul: { weapon: 'maul', name: 'Maul', art: 'tolling_blow', prefix: 'ml_', first: 'ml_1', alt: 'gs_1', diff: 3, mech: 'Walk-charge and stun',
    desc: 'A brawler that never stops moving: it charges while walking and knocks great foes down.',
    str: 'The best at stance breaking and knockdowns, mobile charging, a brace that tanks a hit.',
    weak: 'Short reach and no guard; bracing still costs HP; the spin is easy to whiff.' },
  sns: { weapon: 'knight_shield', name: 'Sword & Shield', art: 'aegis', prefix: 'sh_', first: 'sh_1', diff: 1, mech: 'Full guard, parry and backhop',
    desc: 'The safest weapon: a full block, the fastest swings, a jump-in attack, and flasks with the blade out.',
    str: 'The best defense, the fastest attacks, good stagger from shield bashes. Forgiving.',
    weak: 'The lowest burst, short reach, and a block that breaks once your stamina runs out.' },
  dual: { weapon: 'twinfangs', name: 'Dual Blades', art: 'twin_tempest', prefix: 'tw_', first: 'tw_1', diff: 4, mech: 'Demon Mode and the perfect dodge',
    desc: 'Relentless and high-risk. Burn stamina for a flurry and dance around the foe.',
    str: 'The highest sustained damage, great mobility, perfect dodges that refuel you.',
    weak: 'No block, the shortest reach, low poise per hit, stamina juggling under pressure.' },
  spear: { weapon: 'spear', name: 'Spear', art: 'thunder_lunge', prefix: 'sp_', first: 'sp_1', diff: 2, mech: 'Heavy guard, hop and charge dash',
    desc: 'The walking wall: plant your feet, block anything frontal and poke from behind the guard.',
    str: 'The longest poke reach, the strongest guard, steady damage, a gap-closing charge.',
    weak: 'The least mobile (a hop, no roll), low burst, a slow turn; struggles with fliers.' },
  staff: { weapon: 'quarterstaff', name: 'Staff', art: 'whirlwind', prefix: 'st_', first: 'st_1', diff: 4, mech: 'Vault and momentum',
    desc: 'Master of the air: vault over the foe, fight from above, never stand where it swings.',
    str: 'The best evasion, hits on both sides, momentum burst, good against fliers.',
    weak: 'Low poise, weak on the ground, and mistimed vaults are punished.' },
  whip: { weapon: 'headsman_chain', name: 'Whip', art: 'lash', prefix: 'wh_', first: 'wh_1', diff: 5, mech: 'Tip crack and grapple',
    desc: 'A precision spacer: fight at the very end of the lash and drag things where you want them.',
    str: 'The longest reach in the game, safe spacing, crowd control, huge damage at the tip.',
    weak: 'No block, weak up close, damage hangs on spacing. The hardest weapon to master.' },
};
for (const t of WTYPES) WTYPE_INFO[t].icon = 'w_' + WTYPE_INFO[t].weapon;
// weapon id -> type id (the nine only); WEAPON_CLASS gets it below
const WEAPON_TYPE = {}; for (const t of WTYPES) WEAPON_TYPE[WTYPE_INFO[t].weapon] = t;
// the art each weapon carries (the contract's locked defaults); WEAPONS re-keyed in type order so every list shows the nine alike
for (const t of WTYPES) { const id = WTYPE_INFO[t].weapon, w = WEAPONS[id]; if (!w) continue; w.art = WTYPE_INFO[t].art; delete WEAPONS[id]; WEAPONS[id] = w; }
// v15 balance (docs/v15/balance.md, Phase 2a): attack rating per type, as a factor on the weapon's base 42. Set from a scripted
// bot fighting 25 bosses with every type at the expected build (tools/shots/v15/balance): fast types that land whole chains
// inside every opening (Dual Blades, Katana) kill ~40% faster than the pack; the reach and guard types ~25% slower. The move
// tables (multiples of AR) are untouched, so every route and bench in AR units reads the same. Types not listed stay at 1.
const WM_AR_TUNE = { longsword: 1, katana: 0.8, greatsword: 1, maul: 0.95, sns: 1.18, dual: 0.6, spear: 1.24, staff: 1.25, whip: 1.1 };
// (the v15 types register later, in 77/78: each 78_mech_<type>.js sets WM_AR_TUNE[type] and calls wmApplyArTune() again)
function wmApplyArTune() { for (const [t, k] of Object.entries(WM_AR_TUNE)) { const w = WTYPE_INFO[t] && WEAPONS[WTYPE_INFO[t].weapon]; if (w && w._v15ar === undefined) { w._v15ar = w.base; w.base = Math.round(w.base * k * 10) / 10; } } }
wmApplyArTune();

function wtype() { const t = typeof SAVE !== 'undefined' && SAVE && WEAPON_TYPE[SAVE.weapon]; return t || 'longsword'; }
function wcls() { return wtype(); }   // the type id (contract §4); replaces 04_player.js's class lookup
// until WM's move tables (75_moves.js) key MOVESETS by type, alias the old class movesets so moveset() keeps working
const WM_OLD_CLS = { longsword: 'sword', katana: 'katana', greatsword: 'great', maul: 'great', sns: 'shield', dual: 'twin', spear: 'spear', staff: 'staff', whip: 'whip' };
try { if (typeof MOVESETS !== 'undefined') for (const t of WTYPES) if (!MOVESETS[t] && MOVESETS[WM_OLD_CLS[t]]) MOVESETS[t] = MOVESETS[WM_OLD_CLS[t]]; } catch (e) {}

// ---- the old 50 weapons -> types (contract §5)
const WM_OLD_TYPE = {
  longsword: 'longsword', oathbrand: 'longsword', kalden: 'longsword', omen: 'longsword', frostbrand: 'longsword', sanguine_rapier: 'longsword',
  pharaoh_khopesh: 'longsword', first_ember: 'longsword',
  dagger: 'dual', pagecutter: 'dual', barnacle_fang: 'dual', carving_knife: 'dual', twinfangs: 'dual',
  greatsword: 'greatsword', forge_cleaver: 'greatsword', tidecleaver: 'greatsword', vael_greatsword: 'greatsword',
  antler_scythe: 'scythe', briar_scythe: 'scythe', crimson_scythe: 'scythe', last_kindling: 'greatsword',
  maul: 'maul', colossus_hammer: 'maul', glacier_maul: 'maul', bell_hammer: 'maul', meteor_maul: 'maul', gravetusk: 'maul', rotmaw: 'maul',
  spear: 'spear', scepter: 'spear', stormfang: 'spear', choir_harpoon: 'spear', scarab_spear: 'spear', saint_lance: 'spear',
  katana: 'katana', stormvein: 'katana', starblade: 'katana', plasma_katana: 'katana',
  quarterstaff: 'staff', windstaff: 'staff', inkquill: 'staff', lantern_staff: 'staff', thornwood_staff: 'staff', sun_sceptre: 'staff',
  knight_shield: 'sns', twinborne: 'sns', overseer_bulwark: 'sns',
  headsman_chain: 'whip', gravechain: 'whip', orrery_whip: 'whip',
};
function wmTypeOfAny(id) { return WEAPON_TYPE[id] || WM_OLD_TYPE[id] || null; }
// WEAPON_CLASS (04_player.js): the nine weapon ids -> types, and the retired ids -> the type they became (old saves, the First
// Ember boss's arsenal); WM may move the declaration, hence the guard
try { if (typeof WEAPON_CLASS !== 'undefined') { for (const k of Object.keys(WEAPON_CLASS)) if (!WEAPON_TYPE[k] && !WM_OLD_TYPE[k]) delete WEAPON_CLASS[k]; Object.assign(WEAPON_CLASS, WM_OLD_TYPE, WEAPON_TYPE); } } catch (e) {}

// ================================================================== Weapon Mastery (§A11)
function wmStore() { if (!SAVE) return {}; if (!SAVE.mastery || typeof SAVE.mastery !== 'object') SAVE.mastery = {}; return SAVE.mastery; }
function masteryXP(type) { const v = +wmStore()[type || wtype()]; return v > 0 ? Math.min(MASTERY_XP[4], v) : 0; }
function masteryRank(type) { const x = masteryXP(type); let r = 1; for (let i = 1; i < MASTERY_XP.length; i++) if (x >= MASTERY_XP[i]) r = i + 1; return r; }
function wmSetRank(type, rank) { wmStore()[type] = MASTERY_XP[clamp(rank, 1, 5) - 1]; }
const WM = { log: [], rankUps: [] };   // debug: the last gains (tests read them)
function masteryGain(type, xp, why) {
  type = type || wtype();
  if (!SAVE || !WTYPE_INFO[type] || !(xp > 0)) return 0;
  const r0 = masteryRank(type), S = wmStore(), x0 = masteryXP(type);
  if (x0 >= MASTERY_XP[4]) return 0;
  S[type] = Math.min(MASTERY_XP[4], x0 + xp);
  WM.log.push([type, xp, why || '']); if (WM.log.length > 40) WM.log.shift();
  const r1 = masteryRank(type);
  if (r1 > r0) wmRankUp(type, r1);
  return S[type] - x0;
}
function wmRankUp(type, rank) {
  const I = WTYPE_INFO[type], u = wmUnlocks(type).filter(q => q.rank === rank), first = u[0];
  WM.rankUps.push([type, rank]);
  banner(`${I.name} Mastery ${WM_ROMAN[rank - 1]}${first ? ': ' + first.name : ''}`,
    first ? `${wmInput(first.input) !== '–' ? wmInput(first.input) + ' · ' : ''}${first.desc}` + (u.length > 1 ? ` (+${u.length - 1} more)` : '') : 'Your hand knows this weapon a little better.', I.icon);
  if (typeof sfx !== 'undefined' && sfx.levelup) sfx.levelup();
  flashScreen = Math.max(flashScreen || 0, 0.15);
  if (P) for (let i = 0; i < 18; i++) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(4, 30), vx: rand(-40, 40), vy: -rand(30, 110), g: 120, life: rand(0.5, 1), kind: 'gold' });
  WM.demo = { type, rank, t: time, input: first && first.input };
  saveGame();
}
// the first input of a fresh rank sits under the HUD for a few seconds: "Try it: L forward → J"
HOOKS.hud.push(() => {
  const d = WM.demo; if (!d || !P || state !== 'play') return;
  const k = time - d.t; if (k > 9 || !d.input || d.input === '–') { if (k > 9) WM.demo = null; return; }
  const a = clamp(Math.min(k - 3.2, 9 - k), 0, 1); if (a <= 0) return;
  const s = `Try it: ${wmInput(d.input)}`, w = textW(s, 5.4, 600) + 14;
  vctx.globalAlpha = 0.8 * a; vctx.fillStyle = 'rgba(8,6,10,0.9)'; vctx.fillRect(ox + (W / 2 - w / 2) * scale, oy + 176 * scale, w * scale, 10 * scale); vctx.globalAlpha = 1;
  text(s, W / 2, 183.4, 5.4, UIC.gold, 'center', { alpha: a });
});
// XP: a hit 1, a kill 5, an elite (or a boss foe in the crowd) 20, a boss 150 (300 the first time ever). Parries and
// counters are WM's (masteryGain(wtype(), 5, 'counter')).
HOOKS.strike.push(t => { if (t && !t.prop && !(typeof TRAINING !== 'undefined' && TRAINING.on && t.dummy)) masteryGain(wtype(), 1, 'hit'); });
{ const _die = Enemy.prototype.die; Enemy.prototype.die = function (info) {
  const r = _die.apply(this, arguments);
  if (info && !this._wmXp && !this.dummy) { this._wmXp = 1; const big = this.boss || (this.cfg && this.cfg.elite); masteryGain(wtype(), big ? 20 : 5, big ? 'elite' : 'kill'); }
  return r;
}; }
{ const _rw = BossBase.prototype.rewards; BossBase.prototype.rewards = function (...a) {
  if (SAVE && !this._wmXp) {
    this._wmXp = 1; SAVE.masteryBoss = SAVE.masteryBoss || {};
    const first = !SAVE.masteryBoss[this.kind]; SAVE.masteryBoss[this.kind] = 1;
    masteryGain(wtype(), first ? 300 : 150, first ? 'boss-first' : 'boss');
  }
  const B = BOSS_INFO[this.kind]; if (B && B.reward) B.reward = B.reward.map(id => wmLoot(id, B));   // a reward list set after load
  return _rw.apply(this, a);
}; }

// ---- the unlocks: WM's WEAPON_UNLOCKS when present, else the Mastery tables of WEAPON_REVAMP.md
const WM_UNLOCKS_DOC = {
  longsword: [[2, 'step_slash', 'Step slash', 'L forward → J', 'A quick forward step-cut instead of a roll (1.2 dmg), to stay close.'],
    [3, 'foresight', 'Foresight cut', 'I → K', 'A counter stance: a blow that lands during it is negated and answered with a 2.8 slash.'],
    [4, 'pommel', 'Pommel strike', 'J J J → hold K', 'A pommel bash: 1.0 dmg with 90 poise, built to break stance.'],
    [5, 'ember_edge', 'Ember edge', 'J J J J, perfect timing', 'The critical slash ignites and a burning follow-up lands (+1.2 and burn).']],
  katana: [[2, 'sheathed_stride', 'Sheathed stride', '–', 'Walk at full speed while sheathed.'],
    [3, 'flash_step', 'Flash step', 'L while sheathed', 'Blink 80 px through the foe with a 1.6 cut, fully invulnerable.'],
    [4, 'thousand_cuts', 'Thousand cuts', 'J J J → I', 'Each flurry hit echoes half a second later.'],
    [5, 'moonlit_iai', 'Moonlit iai', 'perfect Iai parry', 'Time slows for a moment and your next Iai deals 3.0.']],
  greatsword: [[2, 'tackle', 'Shoulder tackle', 'L while charging', 'A tackle that can’t be flinched, takes 60% less damage and keeps your charge level.'],
    [3, 'true_charged', 'True Charged Slash', 'K after a strong charged slash', 'A two-part slash: 1.5 then 4.5 at full charge.'],
    [4, 'guard_tackle', 'Guard tackle', 'I → K', 'Tackle out of a block straight into a level 2 charge.'],
    [5, 'wrath', 'Wrath charge', 'hold K past level 3', 'A fourth charge level: 4.2, a flame burst and burn.']],
  maul: [[2, 'charge_step', 'Charge step', 'L while charging', 'Roll without losing the charge.'],
    [3, 'big_bang', 'Big Bang', 'J J J → K K K K', 'A timed four-hit chain: 1.0, 1.0, 1.2 and a 3.0 that stuns twice as hard.'],
    [4, 'steered_spin', 'Steered spin', 'while spinning', 'Steer the spinning bludgeon; each spin deals 0.6.'],
    [5, 'earthshaker', 'Earthshaker', 'hold level 3 for 1.4 s', 'The overcharge sends out a 64 px shockwave that stuns.']],
  sns: [[2, 'perfect_rush', 'Perfect rush', 'J J K, on the flash', 'Each timed hit of the rush grows stronger: 1.0, 1.2, 2.0.'],
    [3, 'shield_slam', 'Shield slam', 'I → K', 'A 1.6 slam with 110 poise.'],
    [4, 'falling_bash', 'Falling bash', 'air ↓K', 'A 1.6 shield plunge with 80 poise that also pogos.'],
    [5, 'perfect_guard', 'Perfect guard', 'I at the last moment', 'Reflects projectiles, costs no stamina; the next counter deals +50%.']],
  dual: [[2, 'dash_cut', 'Dash-through cut', 'demon dash → J', 'Cut through the foe as you dash; 1.5 after a perfect dodge.'],
    [3, 'blade_dance2', 'Blade Dance II', 'hold K (Archdemon)', 'Three more hits and a cross-cut finisher.'],
    [4, 'iron_lungs', 'Iron lungs', '–', 'Demon Mode drains 8 stamina a second instead of 12.'],
    [5, 'archfiend', 'Archfiend', '–', 'Archdemon lasts 30 s and your dashes leave a burning trail.']],
  spear: [[2, 'triple_hop', 'Triple hop', 'L L L', 'Chain three hops.'],
    [3, 'charged_counter', 'Charged counter', 'I → hold K', 'A 3.0 counter-thrust with 90 poise.'],
    [4, 'power_guard', 'Power guard', 'I + K', 'For a second: no pushback and no chip damage; stamina costs ×1.5.'],
    [5, 'thunder_charge', 'Thunder charge', 'charge dash', 'The dash pierces with lightning and the finisher deals 3.0.']],
  staff: [[2, 'roll_vault', 'Roll vault', 'L → I', 'Vault straight out of a roll.'],
    [3, 'spin_finisher', 'Spin finisher', 'air K → K', 'A second aerial spin (1.8); it uses one air attack.'],
    [4, 'double_vault', 'Double vault', 'I in the air near a foe', 'Vault off a foe’s head; refunds the air attacks once per jump.'],
    [5, 'gale', 'Gale', 'K with 3 momentum', 'The spin becomes a travelling tornado: three hits of 0.6.']],
  whip: [[2, 'snap_counter', 'Snap counter', 'I as a blow lands', 'Lash the attacker out of its move: the hit is negated, small foes stagger.'],
    [3, 'grapple_slam', 'Grapple slam', 'grapple → K', 'Pull a small foe in and slam it: 1.6, stunned.'],
    [4, 'double_crack', 'Double crack', 'K → K', 'A follow-up crack: 1.4 then 1.8, both with tip bonuses.'],
    [5, 'thousand_lashes', 'Thousand lashes', 'hold J', 'A held flurry of eight tip-only lashes.']],
};
function wmUnlocks(type) {
  try { if (typeof WEAPON_UNLOCKS !== 'undefined' && WEAPON_UNLOCKS && Array.isArray(WEAPON_UNLOCKS[type]) && WEAPON_UNLOCKS[type].length)
    return WEAPON_UNLOCKS[type].map(u => ({ rank: +u.rank || 2, id: u.id, name: u.name || u.id, input: u.input || '–', desc: u.desc || '' })).sort((a, b) => a.rank - b.rank); } catch (e) {}
  return (WM_UNLOCKS_DOC[type] || []).map(([rank, id, name, input, desc]) => ({ rank, id, name, input, desc }));
}
// "J / K / I / L" in the tables are the default light / heavy / block / roll keys: show the player's own bindings
function wmInput(s) {
  if (!s || s === '–') return '–';
  const map = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
  return s.replace(/\b([JKIL])\b/g, (m, k) => { try { const b = keysOf(map[k])[0]; return b || k; } catch (e) { return k; } });
}

// ================================================================== loot conversion: weapons became Emberstones + cinders
// Room items and chests (tools/rooms.py + regions) name these caches directly; boss rewards and any stray 'w:<old id>'
// are converted here. Tiers follow where the weapon used to lie / how strong its boss was.
const WM_CACHES = {
  wc_small: { name: 'Small Tempering Cache', cache: { emberstone: 1, cinders: 400 } },
  wc_cache: { name: 'Tempering Cache', cache: { emberstone: 2, cinders: 800 } },
  wc_great: { name: 'Great Tempering Cache', cache: { emberstone: 2, cinders: 1600 } },
  wc_hoard1: { name: 'Ember Hoard', cache: { emberstone: 2, cinders: 1500 } },
  wc_hoard2: { name: 'Great Ember Hoard', cache: { emberstone: 3, cinders: 3000 } },
  wc_hoard3: { name: 'Sovereign Ember Hoard', cache: { emberstone: 4, cinders: 6000 } },
};
for (const [id, c] of Object.entries(WM_CACHES)) ITEMS[id] = { name: c.name, icon: 'i_emberstone', sheet: 'ui_icons2', cache: c.cache,
  desc: `${c.cache.emberstone} Emberstone${c.cache.emberstone > 1 ? 's' : ''} wrapped in ${c.cache.cinders} cinders. The Ashwright tempers any of your weapons with them.` };
function wmHoardFor(B) { const c = (B && B.cinders) || 0; return c >= 15000 ? 'wc_hoard3' : c >= 7000 ? 'wc_hoard2' : 'wc_hoard1'; }
function wmLoot(id, B) { const m = /^w:(.+)$/.exec(id || ''); if (!m || WEAPON_TYPE[m[1]] && !B) return id; return B ? wmHoardFor(B) : 'wc_cache'; }
for (const id of Object.keys(WM_OLD_TYPE)) if (!WEAPONS[id]) ITEMS['w:' + id] = { ...ITEMS.wc_cache, legacyWeapon: id };   // anything still naming an old weapon
const WM_BOSS_LOOT = {};   // kind -> [old reward, new reward] (for the report / tests)
if (typeof BOSS_INFO !== 'undefined') for (const [k, B] of Object.entries(BOSS_INFO)) if (B && Array.isArray(B.reward))
  B.reward = B.reward.map(id => { const n = /^w:/.test(id) ? wmHoardFor(B) : id; if (n !== id) WM_BOSS_LOOT[k] = [id, n]; return n; });
for (const list of Object.values(SHOPS)) for (let i = list.length - 1; i >= 0; i--) if (/^w:/.test(list[i].item)) list.splice(i, 1);

// ================================================================== saves
// new journeys: all nine weapons at +0, no mastery; the New Game select fills in the weapon (and difficulty)
const WSEL = { pending: null };
{ const _ns = newSave; newSave = function () {
  const s = _ns();
  s.weapons = {}; for (const t of WTYPES) s.weapons[WTYPE_INFO[t].weapon] = 0;
  s.mastery = {}; s.masteryBoss = {}; s.wv = 9;
  if (WSEL.pending) { s.weapon = WTYPE_INFO[WSEL.pending.type].weapon; if (WSEL.pending.diff !== undefined) s.diff = WSEL.pending.diff; }
  s.art = WEAPONS[s.weapon] ? WEAPONS[s.weapon].art : 'crescent'; s.arts = [s.art];
  return s;
}; }
{ const _ng = newGame; newGame = function (skipIntro) {
  const r = _ng.apply(this, arguments);
  if (skipIntro && WSEL.pending) { WSEL.pending = null; if (P && D) { refreshDerived(false); P.hp = D.maxHp; P.fp = D.maxFp; } saveGame(); }
  return r;
}; }
// old saves (contract §5): classes -> types, best level per type, rank II for every type owned, the weapon in hand -> its
// type's weapon, removed arts dropped, the Arsenal skill nodes removed (their points come back by themselves)
const WM_ARSENAL_NODES = ['m_sword', 'm_dagger', 'm_great', 'm_spear', 'm_katana', 'm_staff', 'm_shield', 'm_twin', 'm_scythe', 'm_whip'];
function wmMigrate(o) {
  const old = o.weapons && typeof o.weapons === 'object' ? o.weapons : {}, lv = {}, owned = new Set();
  for (const [id, l] of Object.entries(old)) { const t = wmTypeOfAny(id); if (!t) continue; owned.add(t); lv[t] = Math.max(lv[t] || 0, clamp(Math.floor(+l || 0), 0, 5)); }
  const eq = wmTypeOfAny(o.weapon) || 'longsword'; owned.add(eq);
  o.weapons = {}; for (const t of WTYPES) o.weapons[WTYPE_INFO[t].weapon] = lv[t] || 0;
  o.weapon = WTYPE_INFO[eq].weapon;
  o.mastery = o.mastery && typeof o.mastery === 'object' ? o.mastery : {};
  for (const t of owned) o.mastery[t] = Math.max(+o.mastery[t] || 0, MASTERY_XP[1]);
  o.masteryBoss = o.masteryBoss && typeof o.masteryBoss === 'object' ? o.masteryBoss : {};
  const arts = new Set(WTYPES.map(t => WTYPE_INFO[t].art));
  o.arts = (Array.isArray(o.arts) ? o.arts : []).filter(a => arts.has(a));
  o.art = WTYPE_INFO[eq].art; if (!o.arts.includes(o.art)) o.arts.push(o.art);
  delete o.lastCls; delete o.artPinned; if (o.x3) delete o.x3.wbLastW;
  const before = (o.skills || []).length;
  o.skills = (o.skills || []).filter(id => !WM_ARSENAL_NODES.includes(id));
  o.wv = 9;
  return { types: [...owned], refunded: before - o.skills.length };
}
function wmRawWv(raw) { try { const s = typeof raw === 'string' ? JSON.parse(raw) : raw; return s && s.wv; } catch (e) { return undefined; } }
let wmMigrateNote = null;
{ const _lg = loadGame; loadGame = function (...a) {
  const o = _lg.apply(this, a); if (!o) return o;
  let raw = null; try { raw = localStorage.getItem(SAVE_KEY); } catch (e) {}
  if (!(wmRawWv(raw) >= 9)) { const r = wmMigrate(o); if (!(typeof TRAINING !== 'undefined' && TRAINING.on)) wmMigrateNote = r; }
  else {   // a current save: make sure every type is present and the weapon is one of the nine
    o.weapons = o.weapons || {}; for (const t of WTYPES) if (o.weapons[WTYPE_INFO[t].weapon] === undefined) o.weapons[WTYPE_INFO[t].weapon] = 0;
    if (!WEAPON_TYPE[o.weapon]) o.weapon = WTYPE_INFO[wmTypeOfAny(o.weapon) || 'longsword'].weapon;
  }
  return o;
}; }
HOOKS.update.push(() => {
  const r = wmMigrateNote; if (!r || state !== 'play') return;
  wmMigrateNote = null;
  toast(`The arsenal is reforged: ${WTYPES.length} weapons, each with its own Mastery. ${r.types.length > 1 ? 'Every type you carried starts' : 'Your weapon starts'} at Mastery II. Change weapons at any shrine.`, 7);
  if (r.refunded) setTimeout(() => toast(`The Arsenal skills became Weapon Mastery: ${r.refunded} skill${r.refunded === 1 ? '' : 's'} refunded.`, 5), 2500);
  saveGame();
});
// New Game+ keeps every weapon's level (09_main) and, now, its mastery
{ const _ng = startNGPlus; startNGPlus = function (...a) {
  const m = SAVE.mastery, mb = SAVE.masteryBoss;
  const r = _ng.apply(this, a);
  SAVE.mastery = { ...(m || {}) }; SAVE.masteryBoss = { ...(mb || {}) }; SAVE.wv = 9; saveGame();
  return r;
}; }
// ---- equipping (shrines, the select screen, the Training Grounds)
function wmEquip(type, opt = {}) {
  const I = WTYPE_INFO[type]; if (!I || !WEAPONS[I.weapon]) return false;
  if (SAVE.weapons[I.weapon] === undefined) SAVE.weapons[I.weapon] = 0;
  const was = SAVE.weapon; SAVE.weapon = I.weapon; wbOnEquip(I.weapon);
  if (P && D) { const f = P.hp / D.maxHp; refreshDerived(false); P.hp = Math.max(1, Math.min(D.maxHp, Math.round(D.maxHp * f))); P.fp = Math.min(P.fp, D.maxFp); }
  if (P && was !== I.weapon && typeof sheet === 'function') sheet('wpn_' + I.weapon).img;   // start decoding the overlay
  if (!opt.quiet) { if (typeof sfx !== 'undefined') sfx.menu(); saveGame(); }
  return true;
}

// ================================================================== shared UI
function wmName(t) { return (WTYPE_INFO[t] || {}).name || t; }
function wmIcon(t, x, y, size, a = 1) { icon(WTYPE_INFO[t].icon, x, y, size, a); }
function wmPips(x, y, rank, o = {}) {   // five small diamonds, gold up to the rank
  const r = o.r || 1.6, gap = o.gap || 4.6;
  for (let i = 0; i < 5; i++) { const on = i < rank; uiDiamond(x + i * gap, y, r, on ? (o.col || UIC.gold) : '#2e261c'); if (!on) uiDiamond(x + i * gap, y, r, '#5a4a30', 0.8, true); }
}
function wmXpBar(x, y, w, type, h = 2) {
  const xp = masteryXP(type), r = masteryRank(type), lo = MASTERY_XP[r - 1], hi = MASTERY_XP[Math.min(4, r)], f = r >= 5 ? 1 : (xp - lo) / Math.max(1, hi - lo);
  uiRect(x, y, w, h, '#221c16'); uiRect(x, y, w * clamp(f, 0, 1), h, r >= 5 ? '#ffd070' : UIC.accent || '#b08a3a');
  return { xp, r, lo, hi, f };
}
function wmXpLabel(type) { const r = masteryRank(type), xp = masteryXP(type); return r >= 5 ? 'Mastered' : `${xp} / ${MASTERY_XP[r]} XP`; }
// the looping preview: idle, then the first combo hit, drawn from the player sheet + the weapon overlay (UI coords)
function wmFirstTag(type) {
  const ps = sheet('player'), I = WTYPE_INFO[type];
  try { const ms = typeof MOVESETS !== 'undefined' && MOVESETS[type]; const c = ms && (ms.combo ? ms.combo[0] : ms.light && ms.light[0]); if (typeof c === 'string' && ps.has(c)) return c; } catch (e) {}
  if (ps.has(I.first)) return I.first; if (I.alt && ps.has(I.alt)) return I.alt; return 'attack1';
}
function wmTagMs(sh, tag) { const t = sh.tag(tag); let n = 0; for (let i = t.from; i <= t.to; i++) n += sh.frames[i].ms; return Math.max(1, n); }
function wmFrameAt(sh, tag, ms) { const t = sh.tag(tag); let f = t.from; while (f < t.to && ms >= sh.frames[f].ms) { ms -= sh.frames[f].ms; f++; } return f; }
function wmBlit(sh, f, cx, by, k, a = 1) {
  const F = sh.frames[f]; if (!F) return;
  vctx.globalAlpha = a; vctx.imageSmoothingEnabled = false;
  vctx.drawImage(sh.img, F.x, F.y, F.w, F.h, ox + (cx - sh.ax * k) * scale, oy + (by - sh.ay * k) * scale, F.w * k * scale, F.h * k * scale);
  vctx.globalAlpha = 1;
}
function wmPreview(type, cx, by, k, t0 = 0) {
  const ps = sheet('player'), ws = sheet('wpn_' + WTYPE_INFO[type].weapon);
  if (!ps.ok) { wmIcon(type, cx - 16, by - 34, 32); return; }
  const atk = wmFirstTag(type), idleMs = Math.max(1100, wmTagMs(ps, 'idle')), atkMs = wmTagMs(ps, atk), tot = idleMs + atkMs + 250;
  const ms = ((time - t0) * 1000) % tot;
  let f;
  if (ms < idleMs) f = wmFrameAt(ps, 'idle', ms % wmTagMs(ps, 'idle'));
  else if (ms < idleMs + atkMs) f = wmFrameAt(ps, atk, ms - idleMs);
  else f = ps.tag(atk).to;
  // a soft floor glow and shadow under the figure
  const G = vctx.createRadialGradient(ox + cx * scale, oy + by * scale, 0, ox + cx * scale, oy + by * scale, 30 * k * scale);
  G.addColorStop(0, 'rgba(230,180,100,0.16)'); G.addColorStop(1, 'rgba(230,180,100,0)'); vctx.fillStyle = G; vctx.fillRect(ox + (cx - 30 * k) * scale, oy + (by - 30 * k) * scale, 60 * k * scale, 32 * k * scale);
  uiRect(cx - 9 * k, by - 0.6 * k, 18 * k, 1.2 * k, '#000', 0.35);
  wmBlit(ps, f, cx, by, k);
  if (ws.ok) wmBlit(ws, f, cx, by, k);
}
function wmStars(x, y, n, size = 4.6) { for (let i = 0; i < 5; i++) text('★', x + i * (size + 0.6), y, size, i < n ? UIC.gold : '#3a3026', 'left', { shadow: false }); }
// the weapon's identity block: name, weapon, identity line, strengths / weaknesses, art, difficulty. Returns the next y.
function wmCard(type, x, y, w, o = {}) {
  const I = WTYPE_INFO[type], wid = I.weapon, Wd = WEAPONS[wid] || {}, art = ARTS[I.art];
  text(I.name.toUpperCase(), x, y + 6, 8.4, UIC.gold, 'left', { spacing: 1.2 });
  const lv = SAVE && SAVE.weapons ? SAVE.weapons[wid] || 0 : 0;
  text(`${Wd.name || wid}${lv ? '  +' + lv : ''}`, x, y + 14, 5.4, UIC.muted, 'left', { weight: 500 });
  if (o.diff !== false) { text('DIFFICULTY', x + w - 30, y + 5, 3.9, UIC.faint, 'right', { spacing: 0.8 }); wmStars(x + w - 27, y + 5.4, I.diff, 4.2); }
  if (o.rank) { const r = masteryRank(type); text(`MASTERY ${WM_ROMAN[r - 1]}`, x + w, y + 14, 4.6, r > 1 ? UIC.gold : UIC.faint, 'right', { spacing: 0.8, weight: 600 }); }
  y += 19; uiFade(x, x + w, y, UI_RGB.accent, 0.5); y += 7;
  for (const l of wrap(I.desc, w, 5.6)) { text(l, x, y, 5.6, UIC.text, 'left', { weight: 400 }); y += 7.2; }
  y += 2;
  const LW = 44, row = (lab, col, s) => { text(lab, x, y, 4.2, col, 'left', { spacing: 0.8, weight: 600 }); const ls = wrap(s, w - LW, 5); ls.forEach((l, i) => text(l, x + LW, y + i * 6.4, 5, UIC.body, 'left', { weight: 400 })); y += Math.max(1, ls.length) * 6.4 + 2.5; };
  row('STRENGTHS', '#8fd89a', I.str);
  row('WEAKNESSES', '#e0907a', I.weak);
  row('MECHANIC', UIC.muted, I.mech);
  if (art && o.art !== false) {
    y += 1; icon('a_' + I.art, x - 1, y - 7, 9);
    text(art.name, x + 11, y, 5.4, UIC.hi, 'left', { weight: 600 });
    text('DEFAULT ART', x + 13 + textW(art.name, 5.4), y - 0.2, 3.9, UIC.faint, 'left', { spacing: 0.8 });
    text(`${art.fp} FP`, x + w, y, 4.8, UIC.fp || '#7fb0ff', 'right', { weight: 600 });
    y += 6.5;
    if (o.artDesc) for (const l of wrap(art.desc || '', w - 11, 4.6)) { text(l, x + 11, y, 4.6, UIC.dim, 'left', { weight: 400 }); y += 5.8; }
  }
  return y;
}
// the unlocks of a type: rank, name, input, effect (learned ones gold). Returns the next y.
function wmUnlockRows(type, x, y, w, maxY, o = {}) {
  const r = masteryRank(type), L = wmUnlocks(type), sz = o.size || 5;
  for (const u of L) {
    if (y > maxY) break;
    const got = r >= u.rank;
    uiDiamond(x + 1.6, y - 1.7, 1.5, got ? UIC.gold : '#3a3026'); if (!got) uiDiamond(x + 1.6, y - 1.7, 1.5, '#6a5a3e', 0.9, true);
    text(WM_ROMAN[u.rank - 1], x + 6, y, sz * 0.86, got ? UIC.gold : UIC.faint, 'left', { weight: 700 });
    text(u.name, x + 17, y, sz, got ? UIC.hi : UIC.muted, 'left', { weight: 600 });
    const inp = wmInput(u.input);
    if (inp !== '–') { const room = w - 17 - textW(u.name, sz, 600) - 5; text(inp, x + w, y, uiFit(inp, room, sz * 0.9, sz * 0.62, 500), got ? UIC.gold : UIC.faint, 'right', { weight: 500 }); }
    y += sz * 1.3;
    if (o.desc !== false) for (const l of wrap(u.desc, w - 17, sz * 0.86)) { if (y > maxY + 2) break; text(l, x + 17, y, sz * 0.86, got ? UIC.body : UIC.dim, 'left', { weight: 400 }); y += sz * 1.12; }
    y += o.gap ?? 2.4;
  }
  return y;
}
// the mastery block for one type: rank, pips, XP bar, the next unlock
function wmRankBlock(type, x, y, w) {
  const r = masteryRank(type), nx = wmUnlocks(type).find(u => u.rank > r);
  text(`MASTERY ${WM_ROMAN[r - 1]}`, x, y, 6.2, UIC.gold, 'left', { spacing: 1, weight: 600 });
  wmPips(x + w - 20, y - 2, r);
  y += 4; wmXpBar(x, y, w, type, 2.2);
  y += 8; text(wmXpLabel(type), x, y, 4.6, UIC.muted, 'left', { weight: 500 });
  if (nx) text(`Next: ${nx.name} at ${WM_ROMAN[nx.rank - 1]}`, x + w, y, 4.6, UIC.faint, 'right', { weight: 400 });
  return y + 6;
}

// ================================================================== New Game: choose your weapon (opened by 64_diffmode.js)
const TITLE_WSEL = { sel: 0, t0: 0 };
function wselOpen() { TITLE_WSEL.sel = 0; TITLE_WSEL.t0 = time; }
function wselMove(d) { TITLE_WSEL.sel = (TITLE_WSEL.sel + d + WTYPES.length) % WTYPES.length; TITLE_WSEL.t0 = time; sfx.menu(); }
function renderTitleWeapon() {
  vctx.fillStyle = 'rgba(4,3,6,0.95)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  uiTitle('CHOOSE YOUR WEAPON', 17, 8);
  text('You can change weapons later, at any shrine. Each one keeps its own upgrades and Mastery.', W / 2, 27, 4.8, UIC.faint, 'center', { weight: 400 });
  // v15: the strip scales with the count (9 types: 36 px cells; 14: 26 px, short labels)
  const n = WTYPES.length, pitch = Math.min(36, Math.floor(372 / n)), x0 = W / 2 - pitch * (n - 1) / 2, cy = 33, cs = Math.min(26, pitch - 4);
  WTYPES.forEach((t, i) => {
    const x = x0 + i * pitch, sel = i === TITLE_WSEL.sel;
    uiHit(x - cs / 2 - 2, cy - 1, cs + 4, cs + 10, () => { if (TITLE_WSEL.sel !== i) { TITLE_WSEL.sel = i; TITLE_WSEL.t0 = time; sfx.menu(); } });
    if (sel) stGlowSafe(x, cy + cs / 2, 22, UI_RGB.gold, 0.22 + 0.06 * uiPulse(3));
    uiCell(x - cs / 2, cy, cs, { sel, eq: sel });
    wmIcon(t, x - cs / 2 + 3, cy + 3, cs - 6, sel ? 1 : 0.62);
    const nm = n > 9 ? WTYPE_INFO[t].short || WTYPE_INFO[t].name : WTYPE_INFO[t].name;
    text(nm, x, cy + cs + 6.5, uiFit(nm, pitch - 2, 4.4, 3.4, 600), sel ? UIC.hi : UIC.faint, 'center', { weight: sel ? 600 : 500 });
  });
  const t = WTYPES[TITLE_WSEL.sel];
  // preview (left) and the card (right)
  panel(16, 72, 120, 126, 0.97); panel(142, 72, 226, 126, 0.97);
  text('IN HAND', 76, 82, 4.2, UIC.faint, 'center', { spacing: 1 });
  wmPreview(t, 74, 178, 2, TITLE_WSEL.t0);
  text(WEAPONS[WTYPE_INFO[t].weapon].name, 76, 192, uiFit(WEAPONS[WTYPE_INFO[t].weapon].name, 110, 5.2, 4, 600), UIC.gold, 'center');
  wmCard(t, 150, 76, 210, { artDesc: true });
  uiFooter([['←→', 'weapon'], ['Enter', 'begin the journey'], ['Esc', 'back']], 209);
}
function stGlowSafe(x, y, r, rgb, a) { const X = ox + x * scale, Y = oy + y * scale, g2 = vctx.createRadialGradient(X, Y, 0, X, Y, r * scale); g2.addColorStop(0, `rgba(${rgb},${a})`); g2.addColorStop(1, `rgba(${rgb},0)`); vctx.fillStyle = g2; vctx.fillRect(X - r * scale, Y - r * scale, 2 * r * scale, 2 * r * scale); }

// ================================================================== shrine: Change weapon (menu.screen 'wchange', from 08_ui.js)
function wchangeOpen(prev) { const i = Math.max(0, WTYPES.indexOf(wtype())); return { screen: 'wchange', sel: i, prev, t0: time }; }
function wchangeInput(M, a) {
  const conf = ['confirm', 'interact', 'attack', 'jump'].includes(a), n = WTYPES.length;
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { menu = M.prev; sfx.menu(); return; }
  if (a === 'up' || a === 'left') { M.sel = (M.sel + n - 1) % n; M.t0 = time; sfx.menu(); }
  else if (a === 'down' || a === 'right') { M.sel = (M.sel + 1) % n; M.t0 = time; sfx.menu(); }
  else if (conf) {
    const t = WTYPES[M.sel];
    if (t === wtype()) { sfx.deny(); toast(`The ${wmName(t)} is already in your hand`, 1.8); return; }
    wmEquip(t); sfx.kindle && sfx.kindle(); flashScreen = 0.15;
    toast(`${WEAPONS[WTYPE_INFO[t].weapon].name} in hand · Mastery ${WM_ROMAN[masteryRank(t) - 1]}`, 2.6);
    menu = M.prev;
  }
}
function renderWChange(M) {
  vctx.fillStyle = 'rgba(5,4,8,0.9)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  uiTitle('CHANGE WEAPON', 17, 8);
  // the nine (left)
  panel(12, 26, 132, 176, 0.96);
  const cur = wtype();
  if (WTYPES.length > 9) wchangeRows(M, cur);
  else WTYPES.forEach((t, i) => {
    const y = 31 + i * 18.6, sel = i === M.sel, I = WTYPE_INFO[t], lv = SAVE.weapons[I.weapon] || 0, r = masteryRank(t);
    uiHit(15, y, 126, 17.6, () => { if (M.sel !== i) { M.sel = i; M.t0 = time; } });
    if (sel) uiSel(15, y, 126, 17.6);
    uiCell(18, y + 1.8, 14, { eq: t === cur }); wmIcon(t, 19.5, y + 3.3, 11, sel || t === cur ? 1 : 0.7);
    text(I.name + (lv ? ` +${lv}` : ''), 36, y + 8.4, 5.8, sel ? UIC.hi : t === cur ? UIC.gold : UIC.text, 'left', { weight: sel ? 600 : 500 });
    wmPips(37, y + 13.4, r, { r: 1.2, gap: 3.6 });
    uiRect(57, y + 12.8, 46, 1.4, '#221c16'); { const q = wmXpBar(57, y + 12.8, 46, t, 1.4); }
    if (t === cur) text('IN HAND', 138, y + 8.2, 3.9, UIC.gold, 'right', { spacing: 0.8 });
  });
  // the chosen one (right): preview + card + mastery
  const t = WTYPES[M.sel];
  panel(150, 26, 222, 176, 0.96);
  wmPreview(t, 186, 98, 1.5, M.t0 || 0);
  const I = WTYPE_INFO[t], wid = I.weapon, lv = SAVE.weapons[wid] || 0;
  let y = 34;
  text(I.name.toUpperCase(), 222, y + 6, 7.6, UIC.gold, 'left', { spacing: 1 });
  text(`${WEAPONS[wid].name}${lv ? '  +' + lv : ''}`, 222, y + 14, 5.2, UIC.muted, 'left', { weight: 500 });
  text(`Attack ${Math.round(weaponAR(SAVE.stats, wid, lv))}`, 222, y + 22, 5.2, UIC.text, 'left', { weight: 600 });
  wmStars(334, y + 22, I.diff, 4.4);
  y = 64; for (const l of wrap(I.desc, 142, 4.9)) { text(l, 222, y, 4.9, UIC.body, 'left', { weight: 400 }); y += 6.2; }
  y = Math.max(y + 2, 104);
  uiFade(158, 364, y, UI_RGB.accent, 0.5); y += 9;
  y = wmRankBlock(t, 158, y, 206);
  y += 3; uiHead('Unlocks', 158, y, 206); y += 9;
  y = wmUnlockRows(t, 158, y, 206, 178, { desc: false, size: 5, gap: 1.2 });
  const art = ARTS[I.art];
  if (art) { const ay = 192; uiFade(158, 364, ay - 9, UI_RGB.accent, 0.35); icon('a_' + I.art, 158, ay - 7, 9); text(art.name, 170, ay, 5.4, UIC.hi, 'left', { weight: 600 });
    text('DEFAULT ART', 172 + textW(art.name, 5.4), ay - 0.2, 3.9, UIC.faint, 'left', { spacing: 0.8 }); text(`${art.fp} FP`, 364, ay, 4.8, UIC.fp, 'right', { weight: 600 }); }
  const here = t === cur;
  uiFooter([['↑↓', 'weapon'], ['Enter', here ? 'in hand' : 'take it up'], ['Esc', 'back']]);
}

// v15: more than nine types -> one compact row each (icon, name +lv, XP bar, rank pips); all 14 fit the 176 px panel
function wchangeRowH() { return Math.min(18.6, 170 / WTYPES.length); }
function wchangeRows(M, cur) {
  const ph = wchangeRowH();
  WTYPES.forEach((t, i) => {
    const y = 30 + i * ph, sel = i === M.sel, I = WTYPE_INFO[t], lv = SAVE.weapons[I.weapon] || 0, r = masteryRank(t), eq = t === cur;
    uiHit(15, y, 126, ph - 0.6, () => { if (M.sel !== i) { M.sel = i; M.t0 = time; } });
    if (sel) uiSel(15, y, 126, ph - 0.6);
    uiCell(18, y + 0.7, ph - 1.8, { eq }); wmIcon(t, 19, y + 1.7, ph - 3.8, sel || eq ? 1 : 0.7);
    text(I.name + (lv ? ` +${lv}` : ''), 32, y + ph * 0.52, 5.2, sel ? UIC.hi : eq ? UIC.gold : UIC.text, 'left', { weight: sel ? 600 : 500 });
    wmXpBar(32, y + ph - 2.6, 72, t, 0.9);
    wmPips(110, y + ph * 0.5 - 1, r, { r: 1.1, gap: 3.4 });
    if (eq) uiDiamond(137, y + ph * 0.5 - 1, 1.5, UIC.gold);
  });
}

// ================================================================== Esc › Equipment › Weapon: the mastery screen (29_ui2.js opens it)
function wmScreenOpen(M) { M.mastery = { sel: Math.max(0, WTYPES.indexOf(wtype())), list: false, row: 0, top: 0 }; sfx.menu(); }
// the weapon's full command list (each type's `combos` in 76_mech_*.js; the unlocks if a type has none)
function wmMoveList(type) {
  try { const T = typeof MV !== 'undefined' && MV.types[type]; if (T && Array.isArray(T.combos) && T.combos.length) return T.combos.map(c => ({ rank: +c.rank || 1, name: c.name, input: c.input || '–', desc: c.desc || '' })); } catch (e) {}
  return wmUnlocks(type);
}
function wmScreenInput(M, a) {
  const S = M.mastery, n = WTYPES.length;
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { if (S.list) { S.list = false; sfx.menu(); return; } M.mastery = null; sfx.menu(); return; }
  if (S.list) {   // the move list: ↑↓ move, ←→ weapon
    const L = wmMoveList(WTYPES[S.sel]);
    if (a === 'up') { S.row = (S.row + L.length - 1) % L.length; sfx.menu(); }
    else if (a === 'down') { S.row = (S.row + 1) % L.length; sfx.menu(); }
    else if (a === 'left' || a === 'right') { S.sel = (S.sel + (a === 'left' ? n - 1 : 1)) % n; S.row = 0; S.top = 0; sfx.menu(); }
    else if (['confirm', 'interact', 'attack', 'jump'].includes(a)) { S.list = false; sfx.menu(); }
    return;
  }
  if (a === 'up' || a === 'left') { S.sel = (S.sel + n - 1) % n; sfx.menu(); }
  else if (a === 'down' || a === 'right') { S.sel = (S.sel + 1) % n; sfx.menu(); }
  else if (['confirm', 'interact', 'attack', 'jump'].includes(a)) { S.list = true; S.row = 0; S.top = 0; sfx.menu(); }
}
function renderMoveList(S, x, y, w, maxY) {
  const t = WTYPES[S.sel], r = masteryRank(t), L = wmMoveList(t), rh = 7.4, rows = Math.max(1, Math.floor((maxY - y) / rh));
  S.row = clamp(S.row || 0, 0, L.length - 1);
  if (S.row < S.top) S.top = S.row; if (S.row >= S.top + rows) S.top = S.row - rows + 1; S.top = clamp(S.top, 0, Math.max(0, L.length - rows));
  for (let i = S.top; i < Math.min(L.length, S.top + rows); i++) {
    const m = L[i], yy = y + (i - S.top) * rh, sel = i === S.row, got = r >= m.rank;
    uiHit(x - 2, yy - 5.6, w + 4, rh, () => { S.row = i; }, () => { if (S.row !== i) { S.row = i; sfx.menu(); } });
    if (sel) uiSel(x - 2, yy - 5.6, w + 4, rh);
    if (m.rank > 1) text(WM_ROMAN[m.rank - 1], x + 1, yy, 4, got ? UIC.gold : UIC.faint, 'left', { weight: 700 });
    text(m.name, x + 9, yy, 5, sel ? UIC.hi : got ? UIC.text : UIC.faint, 'left', { weight: sel ? 600 : 500 });
    const inp = wmInput(m.input), room = w - 11 - textW(m.name, 5, 600) - 4;
    text(inp, x + w, yy, uiFit(inp, room, 4.6, 3.4, 500), got ? UIC.gold : UIC.faint, 'right', { weight: 500 });
  }
  if (L.length > rows) { const f = S.top / Math.max(1, L.length - rows); uiRect(x + w + 3, y - 5, 1, rows * rh, '#221c16'); uiRect(x + w + 3, y - 5 + f * (rows * rh - 8), 1, 8, UIC.gold); }
  const m = L[S.row]; if (!m) return;
  const dy = maxY + 4; uiFade(x, x + w, dy - 4, UI_RGB.accent, 0.4);
  const ls = wrap((r >= m.rank ? '' : `Unlocks at Mastery ${WM_ROMAN[m.rank - 1]}. `) + m.desc, w, 4.6);
  ls.slice(0, 2).forEach((l, i) => text(l, x, dy + 3 + i * 5.8, 4.6, r >= m.rank ? UIC.body : UIC.dim, 'left', { weight: 400 }));
}
function renderMasteryScreen(M) {
  const S = M.mastery, cur = wtype();
  panel(12, 30, 152, 172);
  text('WEAPON MASTERY', 18, 41, 6, UIC.gold, 'left', { spacing: 1 });
  text('rank · progress', 158, 41, 4.6, UIC.faint, 'right', { weight: 500 });
  uiHair(18, 44.5, 140, UIC.line, 0.8);
  const ph = Math.min(16.8, 151 / WTYPES.length), k = ph / 16.8;   // v15: rows shrink to fit every type (14: 10.8 px)
  WTYPES.forEach((t, i) => {
    const y = 48 + i * ph, sel = i === S.sel, r = masteryRank(t);
    uiHit(15, y, 146, ph - 0.8, () => { S.sel = i; }, () => { if (S.sel !== i) { S.sel = i; sfx.menu(); } });
    if (sel) uiSel(15, y, 146, ph - 0.8);
    const cs = Math.max(9, 13 * k), fs = k < 1 ? 5 : 5.6;
    uiCell(18, y + (ph - 0.8 - cs) / 2, cs, { eq: t === cur }); wmIcon(t, 19.5, y + (ph - 0.8 - cs) / 2 + 1.5, cs - 3, sel || t === cur ? 1 : 0.7);
    text(wmName(t), 18 + cs + 4, y + 7.6 * k + (k < 1 ? 0.6 : 0), fs, sel ? UIC.hi : t === cur ? UIC.gold : UIC.text, 'left', { weight: sel ? 600 : 500 });
    text(WM_ROMAN[r - 1], 156, y + 7.6 * k + (k < 1 ? 0.6 : 0), fs, r > 1 ? UIC.gold : UIC.faint, 'right', { weight: 700 });
    wmXpBar(18 + cs + 4, y + ph - 3.2 * Math.max(k, 0.75), 138 - cs - 4, t, k < 1 ? 1 : 1.4);
  });
  const t = WTYPES[S.sel], I = WTYPE_INFO[t];
  panel(170, 30, 202, 172, 0.8);
  const x = 179, w = 184;
  uiCell(x, 39, 26, { eq: t === cur }); wmIcon(t, x + 2, 41, 22);
  text(I.name, x + 33, 51, 7.6, UIC.gold, 'left');
  text(`${WEAPONS[I.weapon].name}${t === cur ? '  ·  in hand' : ''}`, x + 33, 60, 5, t === cur ? UIC.gold : UIC.muted, 'left', { weight: 500 });
  { const lab = S.list ? '◂ MASTERY' : 'MOVE LIST ▸', lw = textW(lab, 4.4, 600) + 6;
    uiHit(x + w - lw, 35, lw, 9, null, () => { S.list = !S.list; S.row = 0; S.top = 0; sfx.menu(); });
    uiRect(x + w - lw, 35, lw, 9, '#2a2016', 0.9); text(lab, x + w - 3, 41.4, 4.4, UIC.gold, 'right', { weight: 600, spacing: 0.6 }); }
  let y = 76;
  if (S.list) {
    uiHead('Move list', x, y - 4, w); text(`${wmMoveList(t).length} moves`, x + w, y - 4, 4.2, UIC.faint, 'right', { weight: 500 });
    renderMoveList(S, x, y + 6, w - 4, 182);
    uiFooter([['↑↓', 'move'], ['←→', 'type'], ['Esc', 'back']]);
    return;
  }
  y = wmRankBlock(t, x, y, w);
  y += 2; uiHead('Moves it teaches', x, y, w); y += 9;
  uiDiamond(x + 1.6, y - 1.7, 1.5, UIC.gold); text('I', x + 6, y, 4.3, UIC.gold, 'left', { weight: 700 }); text(`The full moveset: ${WTYPE_INFO[t].mech.toLowerCase()}`, x + 17, y, 5, UIC.hi, 'left', { weight: 600 });
  y += 4 + 2.4 + 3;
  wmUnlockRows(t, x, y, w, 194, { size: 5 });
  uiFooter([['↑↓', 'type'], ['Enter', 'move list'], ['Esc', 'back']]);
}

// ================================================================== Training Grounds: pick any type, set its mastery (65_training.js)
function wmTrainingRows(R, head) {
  const cur = wtype();
  head('In hand', `${WEAPONS[SAVE.weapon].name}`);
  R.push({ label: 'Upgrade level', val: () => '+' + (SAVE.weapons[SAVE.weapon] || 0), lr: d => { SAVE.weapons[SAVE.weapon] = clamp((SAVE.weapons[SAVE.weapon] || 0) + d, 0, 5); trnApplyBuild(false); },
    conf: () => { SAVE.weapons[SAVE.weapon] = ((SAVE.weapons[SAVE.weapon] || 0) + 1) % 6; trnApplyBuild(false); }, wpn: SAVE.weapon, desc: 'Tempering, +0 to +5 (◂ ▸).' });
  R.push({ label: 'Mastery rank', val: () => 'Rank ' + WM_ROMAN[masteryRank(wtype()) - 1], lr: d => { wmSetRank(wtype(), masteryRank(wtype()) + d); },
    conf: () => { wmSetRank(wtype(), masteryRank(wtype()) % 5 + 1); }, wpn: SAVE.weapon, desc: 'Rank I to V (◂ ▸): unlocks the moves of each rank for this weapon. Nothing flows back to your journey.' });
  R.push({ label: 'Master every weapon', act: true, conf: () => { for (const t of WTYPES) wmSetRank(t, 5); toast('Every weapon at Mastery V', 2); }, desc: `All ${WTYPES.length} weapons to Mastery V.` });
  head('Weapon types', `${WTYPES.length} types`);
  for (const t of WTYPES) {
    const id = WTYPE_INFO[t].weapon;
    R.push({ label: wmName(t), wpn: id, val: () => (SAVE.weapon === id ? '● ' : '') + 'Rank ' + WM_ROMAN[masteryRank(t) - 1], eq: () => SAVE.weapon === id,
      conf: () => { wmEquip(t, { quiet: true }); trnApplyBuild(false); sfx.menu(); }, desc: WTYPE_INFO[t].desc });
  }
}

// ---- debug handles for headless tests (tools/shots/ws/)
if (typeof window !== 'undefined' && window.__game) window.__game.ws = {
  WTYPES, WTYPE_INFO, WEAPON_TYPE, WM, MASTERY_XP, WM_BOSS_LOOT, WM_OLD_TYPE, TITLE_WSEL, WSEL,
  wtype: () => wtype(), wcls: () => wcls(), rank: t => masteryRank(t), xp: t => masteryXP(t), gain: (t, n, w) => masteryGain(t, n, w), setRank: wmSetRank,
  unlocks: t => wmUnlocks(t), migrate: o => wmMigrate(o), equip: t => wmEquip(t), loot: (id, b) => wmLoot(id, b),
};
