// ------------------------------------------------------------------ data: stats, skills, enemies, items
const STATS = [
  { k: 'vig', name: 'Vigor', desc: 'Maximum HP' },
  { k: 'mnd', name: 'Mind', desc: 'Maximum FP' },
  { k: 'end', name: 'Endurance', desc: 'Stamina and poise' },
  { k: 'str', name: 'Strength', desc: 'Heavy attack and stance damage' },
  { k: 'dex', name: 'Dexterity', desc: 'Light attack damage, faster casting' },
  { k: 'fth', name: 'Faith', desc: 'Sorcery and incantation power' },
];
const BASE_STATS = { vig: 10, mnd: 8, end: 10, str: 11, dex: 11, fth: 9 };
const BASE_LEVEL = 1;
const softcap = s => s <= 40 ? s : 40 + (s - 40) * 0.35;
function levelOf(st) { return BASE_LEVEL + STATS.reduce((a, s) => a + st[s.k] - BASE_STATS[s.k], 0); }
function levelCost(L) { return Math.round(90 + 20 * L + 1.75 * L * L); }
function charmOn(id) { return typeof SAVE !== 'undefined' && SAVE && SAVE.charmsEq && SAVE.charmsEq.includes(id); }
function derive(st, skills) {
  const v = softcap(st.vig), m = softcap(st.mnd), e = softcap(st.end), f = softcap(st.fth);
  const wid = (typeof SAVE !== 'undefined' && SAVE && SAVE.weapon) || 'longsword', W = WEAPONS[wid];
  const wlv = (SAVE && SAVE.weapons && SAVE.weapons[wid]) || 0;
  const ar = weaponAR(st, wid, wlv);
  const d = {
    maxHp: Math.round((60 + 10.5 * v + 0.08 * v * v) * (charmOn('c_crimson') ? 1.15 : 1)),
    maxFp: Math.round((30 + 5 * m) * (charmOn('c_azure') ? 1.25 : 1)),
    maxSt: Math.round(72 + 2.8 * e),
    light: ar,
    heavy: ar * (1 + 0.012 * (softcap(st.str) - 10)),
    spell: (1 + 0.045 * (f - 9)) * (W.holy ? 1 + W.holy : 1) * (charmOn('c_scholar') ? 1.15 : 1) * (charmOn('c_ember') ? 1.15 : 1),
    castSpeed: 1 + 0.008 * (softcap(st.dex) - 10),
    poise: 12 + e * 0.8 + (skills.has('steadfast') ? 25 : 0),
    W, wid, wlv, ar,
  };
  for (const f of HOOKS.derive) f(d, st, skills);
  return d;
}

// skill tree — 3 branches × 5, each node requires the one above it
const SKILLS = [
  { id: 'keen_edge', br: 0, t: 0, cost: 1, name: 'Keen Edge', desc: '+12% physical damage.' },
  { id: 'fourth_strike', br: 0, t: 1, cost: 1, name: 'Fourth Strike', desc: 'Your light combo gains a spinning fourth strike.' },
  { id: 'charged_arts', br: 0, t: 2, cost: 2, name: 'Charged Arts', desc: 'Heavy attacks charge faster. A full charge looses a crescent of ash.' },
  { id: 'riposte_mastery', br: 0, t: 3, cost: 2, name: 'Riposte Mastery', desc: 'Wider parry window. Critical hits deal +50% and restore 10% HP.' },
  { id: 'bloodthirst', br: 0, t: 4, cost: 3, name: 'Bloodthirst', desc: 'Melee hits build Bleed. A full bleed meter bursts for heavy damage.' },
  { id: 'ash_bolt', br: 1, t: 0, cost: 1, name: 'Ash Bolt', desc: 'Sorcery: hurl a bolt of golden ash. (U to cast, Q to switch spell)' },
  { id: 'sunspear', br: 1, t: 1, cost: 1, name: 'Sunspear', desc: 'Incantation: throw a piercing spear of light.' },
  { id: 'azure_thrift', br: 1, t: 2, cost: 2, name: 'Azure Thrift', desc: 'All spells cost 30% less FP.' },
  { id: 'emberburst', br: 1, t: 3, cost: 2, name: 'Emberburst', desc: 'Incantation: a ring of fire erupts around you.' },
  { id: 'soul_siphon', br: 1, t: 4, cost: 3, name: 'Soul Siphon', desc: 'Melee hits restore FP. Kills restore FP and a little HP.' },
  { id: 'quickstep', br: 2, t: 0, cost: 1, name: 'Quickstep', desc: 'Rolling costs 30% less stamina and is invulnerable for longer.' },
  { id: 'iron_flask', br: 2, t: 1, cost: 1, name: 'Iron Flask', desc: '+1 flask charge.' },
  { id: 'steadfast', br: 2, t: 2, cost: 2, name: 'Steadfast', desc: 'Greater poise, and damage taken is reduced by 10%.' },
  { id: 'last_stand', br: 2, t: 3, cost: 2, name: 'Last Stand', desc: 'Below 30% HP you deal 25% more damage.' },
  { id: 'second_wind', br: 2, t: 4, cost: 3, name: 'Second Wind', desc: 'Rolling through an attack slows time, refills stamina and empowers your next strike.' },
];
const BRANCHES = ['Blade', 'Ash', 'Veil'];
const SPELLS = {
  ash_bolt: { name: 'Ash Bolt', fp: 10, icon: 'ash_bolt' },
  sunspear: { name: 'Sunspear', fp: 18, icon: 'sunspear' },
  emberburst: { name: 'Emberburst', fp: 26, icon: 'emberburst' },
};

const ITEMS = {
  shard: { name: 'Memory Shard', icon: 'shard', desc: 'A splinter of a forgotten battle. +1 skill point.' },
  seed: { name: 'Crimson Seed', icon: 'flask_red', desc: 'A seed of the Pale Root. +1 flask charge.' },
  gold: { name: 'Golden Cinders', icon: 'cinder', desc: 'A hoard of cinders.' },
  talon: { name: 'Hound\'s Talon', icon: 'talon', desc: 'Cling to walls and leap from them. (Jump while sliding on a wall)' },
  wings: { name: 'Ashen Wings', icon: 'wings', desc: 'Jump again in midair.' },
  key: { name: 'Cathedral Key', icon: 'key', desc: 'Opens the sealed gate of the Sunken Cathedral.' },
};

// enemy archetypes. dmg per attack tag; poise = stance before flinch; stance = stance before a critical stagger
const ENEMY = {
  hollow_soldier: { hp: 110, cinders: 45, speed: 34, aggro: 150, range: 34, poise: 20, stance: 70, dmg: { attack: 34 }, cool: [0.6, 1.4], lunge: { attack: 70 } },
  shield_warden: { hp: 260, cinders: 110, speed: 22, aggro: 140, range: 40, poise: 60, stance: 130, dmg: { bash: 42 }, cool: [0.9, 1.7], guard: true, lunge: { bash: 90 } },
  rot_crawler: { hp: 50, cinders: 25, speed: 62, aggro: 120, range: 60, poise: 10, stance: 30, dmg: { lunge: 22 }, cool: [0.8, 1.6], contact: 14 },
  gloom_wisp: { hp: 60, cinders: 35, speed: 55, aggro: 170, range: 90, poise: 10, stance: 30, dmg: { dive: 26 }, cool: [1.2, 2.2], flying: true },
  hollow_archer: { hp: 80, cinders: 50, speed: 30, aggro: 220, range: 200, poise: 15, stance: 50, dmg: { arrow: 24 }, cool: [1.4, 2.4], ranged: 'arrow' },
  ember_acolyte: { hp: 120, cinders: 70, speed: 26, aggro: 200, range: 180, poise: 15, stance: 60, dmg: { fireball: 30 }, cool: [1.6, 2.6], ranged: 'fireball', blink: true },
  rot_hulk: { hp: 480, cinders: 280, speed: 20, aggro: 150, range: 56, poise: 90, stance: 220, dmg: { smash: 58 }, cool: [1.3, 2.1], rot: 35, lunge: { smash: 30 } },
  bog_spitter: { hp: 95, cinders: 85, speed: 30, aggro: 200, range: 190, poise: 15, stance: 50, dmg: { rotglob: 24 }, cool: [1.6, 2.6], ranged: 'rotglob', rot: 40 },
  mire_witch: { hp: 150, cinders: 150, speed: 22, aggro: 210, range: 170, poise: 20, stance: 70, dmg: { mist: 9 }, cool: [2.6, 3.6], ranged: 'mist', rot: 30 },
  gilded_sentinel: { hp: 720, cinders: 520, speed: 30, aggro: 170, range: 64, poise: 999, stance: 280, dmg: { sweep: 56, thrust: 62 }, cool: [0.8, 1.5], elite: true, lunge: { thrust: 140, sweep: 40 } },
  root_spawn: { hp: 40, cinders: 35, speed: 72, aggro: 140, range: 24, poise: 5, stance: 20, dmg: { burst: 46 }, cool: [0.3, 0.6], suicide: true },
  sun_seraph: { hp: 130, cinders: 170, speed: 52, aggro: 220, range: 160, poise: 15, stance: 60, dmg: { lightorb: 28, dive: 34 }, cool: [1.8, 2.8], flying: true, ranged: 'lightorb' },
  grimoire: { hp: 85, cinders: 110, speed: 48, aggro: 210, range: 170, poise: 12, stance: 45, dmg: { inkbolt: 26, dive: 24 }, cool: [1.6, 2.6], flying: true, ranged: 'inkbolt' },
  ink_hound: { hp: 120, cinders: 120, speed: 95, aggro: 170, range: 70, poise: 18, stance: 60, dmg: { pounce: 36 }, cool: [0.7, 1.3], leap: [230, -150] },
  lantern_monk: { hp: 210, cinders: 170, speed: 26, aggro: 150, range: 50, poise: 40, stance: 110, dmg: { swing: 44 }, cool: [1.0, 1.8], lunge: { swing: 40 } },
  grave_knight: { hp: 900, cinders: 420, speed: 30, aggro: 170, range: 58, poise: 999, stance: 260, dmg: { combo: 52, slam: 68 }, cool: [0.7, 1.4], elite: true, lunge: { combo: 60, slam: 40 } },
};

const AREAS = {
  ramparts: { name: 'The Ashen Ramparts', ambient: 0.42, amb: 'ash', tint: '#1a1420' },
  catacombs: { name: 'Rootbound Catacombs', ambient: 0.6, amb: 'dust', tint: '#0a0c10' },
  cathedral: { name: 'The Sunken Cathedral', ambient: 0.55, amb: 'gold', tint: '#0e0c14' },
  mire: { name: 'The Weeping Mire', ambient: 0.42, amb: 'spore', tint: '#0b120e' },
  crown: { name: 'The Pale Crown', ambient: 0.12, amb: 'petal', tint: '#cfd8e6' },
  archives: { name: 'The Ashen Archives', ambient: 0.44, amb: 'gold', tint: '#0c0a12' },
};
