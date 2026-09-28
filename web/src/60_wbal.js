// ------------------------------------------------------------------ weapon-feel pass (agent WB): arts locked to weapons, art tuning,
// signature info. docs/WEAPON_FEEL_CONTRACT.md B1/B4, numbers in docs/weapon_balance.md (bench: tools/shots/wb/).
// Each weapon has exactly one art, its own (WEAPONS[id].art; the First Ember's is its Echo), and it can't be changed:
// SAVE.art is forced to it on load, on every weapon swap and on NG+ (checked every frame -- cheap). SAVE.arts,
// SAVE.artPinned and the "Ash of X" items are obsolete: old saves keep the fields, nothing reads them.
function wbArtOf(id) { const w = WEAPONS[id || (SAVE && SAVE.weapon)]; return w && ARTS[w.art] ? w.art : 'crescent'; }
const WB_CLS_LABEL = { sword: 'straight sword', dagger: 'dagger', great: 'greatsword', spear: 'spear', katana: 'katana', staff: 'staff',
  shield: 'sword and shield', twin: 'twinblades', scythe: 'scythe', whip: 'whip', mirror: 'mirror blade' };
function wbClassLabel(cls) { return WB_CLS_LABEL[cls] || 'weapon'; }
function wbLockArt() {
  if (typeof SAVE === 'undefined' || !SAVE || !SAVE.weapon) return;
  const a = wbArtOf(SAVE.weapon);
  if (SAVE.art !== a) SAVE.art = a;
  if (SAVE.artPinned) delete SAVE.artPinned;   // the old "keep my art across swaps" pin
  const c = WEAPON_CLASS[SAVE.weapon];
  if (c && c !== 'mirror') { SAVE.x3 = SAVE.x3 || {}; SAVE.x3.wbLastW = SAVE.weapon; }   // the weapon the First Ember remembers
}
// called by the equipment screens when a weapon is put in hand
function wbOnEquip(id) {
  wbLockArt();
  if (WEAPON_CLASS[id] === 'mirror') {
    toast(`The First Ember takes the shape of your ${wbClassLabel(wcls())}`, 3.2);
    wbSeedEcho();
  }
}
// the First Ember's Echo repeats the last art performed; fresh from a load, that is the art of the weapon it remembers
function wbSeedEcho() {
  if (typeof GEAR2 === 'undefined' || !GEAR2.S || GEAR2.S.lastArt) return;
  const w = SAVE.x3 && SAVE.x3.wbLastW; if (w && WEAPONS[w] && wbArtOf(w) !== 'echo') GEAR2.S.lastArt = wbArtOf(w);
}
HOOKS.update.push(() => { wbLockArt(); if (SAVE && SAVE.weapon === 'first_ember') wbSeedEcho(); });
HOOKS.enter.push(() => wbLockArt());
HOOKS.rest.push(() => wbLockArt());

// ---- art tuning (B4): the art is part of the weapon now, so none may be a trap or a crutch.
// fp / cd from tools/shots/wb/art_bench.js (damage per use in light hits) and bench_real.js's art column; see weapon_balance.md.
const WB_ART_TUNE = {
  crescent: { fp: 10, cd: 4 }, bloodstep: { fp: 8, cd: 4 }, stormleap: { fp: 14, cd: 5 }, warcry: { fp: 8, cd: 13 }, moonwave: { fp: 12, cd: 5 },
  cinderblade: { fp: 12 }, whirlwind: { fp: 26, cd: 11 }, gale_vault: { fp: 22, cd: 8 }, ink_mark: { fp: 12, cd: 6.5 },
  aegis: { fp: 10, cd: 7 }, frost_aegis: { fp: 12, cd: 7 }, shield_charge: { fp: 16, cd: 6 }, magma_quake: { fp: 30, cd: 15 },
  thunder_lunge: { fp: 14, cd: 5 }, tolling_blow: { fp: 24, cd: 9 }, twin_tempest: { fp: 24, cd: 8.5 }, echo: { fp: 16, cd: 8 },
  backstep_slash: { fp: 10, cd: 3.7 }, reap: { fp: 12, cd: 4.5 }, harvest_moon: { fp: 16, cd: 5.5 }, lash: { fp: 20, cd: 9 },
  chain_drag: { fp: 16, cd: 6 }, blood_frenzy: { fp: 14, cd: 12 }, tidal_surge: { fp: 14, cd: 6 }, solar_flare: { fp: 18, cd: 6.5 },
  starfall: { fp: 26, cd: 9 }, overclock: { fp: 10, cd: 6 }, pale_pyre: { fp: 22, cd: 9.5 },
};
for (const [id, t] of Object.entries(WB_ART_TUNE)) if (ARTS[id]) Object.assign(ARTS[id], t);
// Aegis / Frost Aegis: a perfect guard for a moment, not a second of invulnerability every few seconds
const WB_GUARD_MAX = { tap: 0.7, charged: 1.0 };
for (const id of ['aegis', 'frost_aegis']) {
  const I = ART_IMPL[id]; if (!I || I._wb) continue;
  const up = I.update; I._wb = true;
  I.update = function (dt, grav) { up.call(this, dt, grav); const s = P.g2; if (s && s.rel && s.dur) s.dur = Math.min(s.dur, s.ch ? WB_GUARD_MAX.charged : WB_GUARD_MAX.tap); };
}

// Sustain: a weapon may heal at most one flask's worth in a whole boss fight -- the arts that drink (Blood Frenzy, Pale Pyre,
// Reap) included, now that they come with the weapon. Their heals all go through 16_gear3.js's heal() (window.__gear3.S.heal);
// what an art heals past the budget during a boss fight is taken back the same frame.
const WB_HEAL_ARTS = new Set(['blood_frenzy', 'pale_pyre', 'reap']);
const WB_SUS = { used: 0, boss: null, last: 0 };
function wbFlaskHp() { return Math.round((D.maxHp * 0.42 + 20) * (typeof flaskMul === 'function' ? flaskMul() : 1)); }
HOOKS.update.push(() => {
  const G3 = typeof window !== 'undefined' && window.__gear3; if (!G3 || !P || !D) return;
  if (P.state === 'art') P.wbArtT = time;
  const h = G3.S.heal || 0, d = h - WB_SUS.last; WB_SUS.last = h;
  if (!boss || !boss.active) { WB_SUS.used = 0; WB_SUS.boss = null; return; }
  if (boss !== WB_SUS.boss) { WB_SUS.boss = boss; WB_SUS.used = 0; }
  if (d <= 0 || !WB_HEAL_ARTS.has(SAVE.art) || !(P.state === 'art' || G3.S.frenzyT > 0 || time - (P.wbArtT || -9) < 4)) return;
  const take = Math.min(d, Math.max(0, wbFlaskHp() - WB_SUS.used)); WB_SUS.used += take;
  if (d > take) P.hp = Math.max(1, P.hp - (d - take));
});

// ---- the old "Ash of X" items: a chest, shop or save that still holds one gives a tempering cache instead
ITEMS.ash_cache = { name: 'Tempering Cache', icon: 'i_emberstone', sheet: 'ui_icons2', cache: { emberstone: 1, cinders: 300 },
  desc: 'A scholar’s pouch: an emberstone wrapped in 300 cinders. Weapon arts are bound to their weapons now; this is what the ash was worth.' };
for (const id of Object.keys(ARTS)) ITEMS['art:' + id] = { ...ITEMS.ash_cache, legacyArt: id };
for (const list of Object.values(SHOPS)) for (const e of list) if (/^art:/.test(e.item)) e.item = 'ash_cache';

// ---- signature info for the gear panel (04b_sigs.js `info`); the First Ember's is live (it names the class it mirrors)
for (const id of Object.keys(SIGS)) if (WEAPONS[id]) Object.defineProperty(WEAPONS[id], 'sigInfo', { get() { return SIGS[id].info; }, configurable: true });

// debug handle for tools/shots/wb/*
if (typeof window !== 'undefined' && window.__game) window.__game.wb = { sus: WB_SUS, artOf: wbArtOf, lock: wbLockArt, onEquip: wbOnEquip, tune: WB_ART_TUNE, sigLimit: () => sigLimit(), sigReach: () => sigReach() };
