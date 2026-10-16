// ------------------------------------------------------------------ The Hearthkeeper (v17 Cold Forge, agent BOSS)
// The one who keeps the fire under the Last Hearth: tall, veiled in soot, a flue cowl ringed by a crown of grate bars,
// a smith's apron over old ritual plate. Kind `hearthkeeper`; his arena is AREA's (docs/v17/forge_area.md: a spawn
// {t:'boss', kind:'hearthkeeper'} in front of the sealed Great Furnace). Three phases:
//   1 The Smith (100-66%)     the slim beaked hammer and the long tongs: slam, low sweep, a three-blow string, the tongs
//                             grab (lifted, hammered, flung), a quick pinch, the ringing floor, a leaping slam, a fan of
//                             sparks struck off the hammer, a backhand for whoever stands behind him
//   2 The Arsenal (66-30%)    the hammer is driven into the coals and left there; he draws weapons glowing from the
//                             coals -- a blade, a spear, a chain -- each for a short pattern telegraphed like the player's
//                             own type, then drops it hissing (the spear is thrown instead); between them he kicks coals
//   3 The Last Fire (30-0%)   the forge's light goes into him: the arena darkens except for the white coal he carries in
//                             the flame tongs. Fire crescent, ember rain (the falling light marks the floor first),
//                             bellows blasts high and low, the burning grip, a nova from his chest, a fast string, and a
//                             lunge from the dark where only the coal shows where he is
// TEMPERING: every phase has a window (30 / 26 / 22 s of fighting). Break his stance before it runs out or he kneels and
//   re-tempers his weapon (+12% damage, +6% speed a level, up to two; the channel takes extra stance damage and can be
//   broken). A stance break or a fatality cools him back to nothing. The bar under his health shows the window.
// He drops the Hearthkeeper's Core where he burns away (not on the kill): taking it sets SAVE.flags['w2:open'] and calls
// AREA's cfFurnaceOpen() if it exists. Rekindle rematches never drop it again and never re-close the furnace.
// Sprite: art/gen_hearthkeeper.py + art/hearthkeeper_rig.py + art/hk_moves.py -> assets/hearthkeeper_p<ph>_<n>,
// assets/hearthkeeper_meta.json (per-frame hit / hurt rects, telegraph points, events, weapon points, hammer heat
// pixels, root shifts), assets/hearthkeeper_props (dropped weapons, the embedded hammer, the core, the crown in the ash).
BOSS_INFO.hearthkeeper = { name: 'The Hearthkeeper', hp: 5600, cinders: 32000, reward: ['emberstone', 'emberstone', 'shard'],
  quote: '“The fire is kept. It is not given.”' };
// the journey (59_difficulty.js / 69_adaptive.js): post-game, between the Sovereign and the First Ember
Object.assign(BOSS_CURVE, { hearthkeeper: [2.95, 1.60] });   // v17 bench (tools/shots/v17/boss/bal): TTK in line with Vael / Astrel
if (!BOSS_INFO.hearthkeeper._curved) { BOSS_INFO.hearthkeeper.hp = Math.round(BOSS_INFO.hearthkeeper.hp * BOSS_CURVE.hearthkeeper[0]); BOSS_INFO.hearthkeeper._curved = 1; }
Object.assign(BOSS_STAGE, { hearthkeeper: 12.5 });

const HK = { shots: [], sparks: [], marks: [], ash: [], jets: [], rings: [], props: [], log: [], spears: [], dark: 0, darkOn: false, said: {} };
const HK_META = () => ASSETS.hearthkeeper_meta || { sheets: {}, attacks: {}, telegraph: {}, events: {}, pts: {}, body: {}, shift: {}, heat: {}, anchor: [80, 139], hurtbox: [66, 40, 30, 96] };
const HK_P2AT = 0.66, HK_P3AT = 0.30;
const HK_WIN = { 1: 30, 2: 26, 3: 22 };          // seconds of fighting before he re-tempers
const HK_STANCE = { 1: 340, 2: 380, 3: 320 };
const hkDmg = (d, b) => BOSS_DMG * d * NGP.dmg * 1.25 * (1 + 0.12 * ((b || boss || {}).temper || 0));
function hkM(kind, tag, ph) { const M = HK_META()[kind] || {}; return (M['p' + ph] || {})[tag]; }
function hkSheet(tag, ph) {
  const S = HK_META().sheets || {};
  let n = (S['p' + ph] || {})[tag];
  if (!n) for (const q of [ph, 1, 2, 3]) if ((S['p' + q] || {})[tag]) { n = S['p' + q][tag]; break; }
  return sheet(n || 'hearthkeeper_p1_1', { meta: HK_META() });
}
const hkSfx = {
  ring: () => { tone(1320, 0.9, 0.05, 'sine', 0.995); tone(1980, 0.6, 0.025, 'sine', 0.99); tone(660, 1.1, 0.04, 'triangle', 0.998); },
  hiss: () => noise(0.7, 3200, 0.6, 0.12, 'highpass', 0.6),
  chain: () => { for (let i = 0; i < 4; i++) tone(900 + i * 140, 0.05, 0.03, 'square', 0.8, i * 0.035); },
  anvil: () => { tone(880, 0.5, 0.06, 'triangle', 0.99); noise(0.12, 2400, 1, 0.3, 'bandpass'); },
};

// ---- the moves. tag = animation (its sheet phase is the boss's phase unless `ph`); dmg / parry per hit window;
//      on = meta event -> handler; unbl = a grab (cannot be blocked or parried: the tell flares red-orange)
const HK_MOVES = {
  // P1 the smith
  slam:     { tag: 'slam', dmg: [62], parry: [false], on: { land() { hkLand(this, 'hammer'); } } },
  sweep:    { tag: 'sweep', dmg: [48], parry: [false] },
  combo:    { tag: 'combo', dmg: [42, 44, 64], parry: [true, true, false], on: { land() { hkLand(this, 'hammer'); } } },
  grab:     { tag: 'grab', dmg: [16], parry: [false], unbl: true, step: { 4: 150 }, onHit() { this.startHold('grabhold'); } },
  snap:     { tag: 'snap', dmg: [34], parry: [true] },
  ring:     { tag: 'ring', dmg: [40], parry: [false], on: { ring() { hkRing(this); } } },
  leap:     { tag: 'leap', dmg: [66], parry: [false], on: { takeoff() { this.leapStart(); }, land() { hkLand(this, 'hammer', true); } } },
  sparks:   { tag: 'sparks', dmg: [], on: { sparks() { hkSparks(this); } } },
  backhand: { tag: 'backhand', dmg: [50], parry: [false], noTrack: true },
  // P2 the arsenal (patterns below)
  draw_blade: { tag: 'draw_blade', on: { draw() { hkDrawn(this, 'blade'); } } },
  bl_rising:  { tag: 'bl_rising', dmg: [52], parry: [true], on: { rise() { hkCrescent(this, 1, 210); } } },
  bl_cleave:  { tag: 'bl_cleave', dmg: [46, 50], parry: [true, true] },
  bl_charge:  { tag: 'bl_charge', dmg: [70], parry: [false], on: { charge() { sfx.charge(); }, chop() { hkLand(this, 'blade'); hkCrescent(this, 1, 250); } } },
  drop_blade: { tag: 'drop_blade', on: { drop() { hkDrop(this, 'blade'); } } },
  draw_spear: { tag: 'draw_spear', on: { draw() { hkDrawn(this, 'spear'); } } },
  sp_thrust:  { tag: 'sp_thrust', dmg: [40, 42, 56], parry: [true, true, false] },
  sp_lunge:   { tag: 'sp_lunge', dmg: [58], parry: [false], on: { dash() { this.dashStart(70); } } },
  sp_hurl:    { tag: 'sp_hurl', dmg: [], on: { throw() { hkHurl(this); } } },
  draw_chain: { tag: 'draw_chain', on: { draw() { hkDrawn(this, 'chain'); } } },
  ch_lash:    { tag: 'ch_lash', dmg: [54], parry: [false], on: { crack() { hkSfx.chain(); shake = Math.max(shake, 4); } } },
  ch_sweep:   { tag: 'ch_sweep', dmg: [44], parry: [false] },
  ch_hook:    { tag: 'ch_hook', dmg: [18, 50], parry: [false, true], onHit(wi) { if (wi === 0) this.hooked = true; }, on: { hook() { hkSfx.chain(); }, yank() { if (this.hooked) { hkSfx.chain(); sfx.heavySwing(); } } } },
  drop_chain: { tag: 'drop_chain', on: { drop() { hkDrop(this, 'chain'); } } },
  coal_kick:  { tag: 'coal_kick', dmg: [], on: { kick() { hkCoals(this); } } },
  // P3 the last fire
  ft_sweep:   { tag: 'ft_sweep', dmg: [56], parry: [false], burn: 14, on: { sweep() { hkCrescent(this, 1, 230); if (this.temper) hkCrescent(this, -1, 180); } } },
  ember_rain: { tag: 'ember_rain', dmg: [], on: { rain() { hkEmberRain(this); } } },
  bellows_lo: { tag: 'bellows_lo', dmg: [], on: { blast() { hkJet(this, 'lo'); } } },
  bellows_hi: { tag: 'bellows_hi', dmg: [], on: { blast() { hkJet(this, 'hi'); } } },
  flame_grab: { tag: 'flame_grab', dmg: [14], parry: [false], unbl: true, step: { 3: 240, 4: 140 }, onHit() { this.startHold('fgrabhold'); } },
  nova:       { tag: 'nova', dmg: [], on: { nova() { hkNova(this); } } },
  ft_combo:   { tag: 'ft_combo', dmg: [40, 42, 52], parry: [true, true, false], burn: 10 },
  dark_lunge: { tag: 'dark_lunge', dmg: [60], parry: [false], burn: 12, on: { dark() { this.darkT = 1; sfx.fire(); }, lunge() { this.darkT = 0; flashScreen = Math.max(flashScreen, 0.15); sfx.bossSwing(); if (Math.abs(P.x - this.x) > 90) this.dashStart(-62); } } },
  // every phase
  temper:     { tag: 'temper', on: { tempered() { this.tempered(); } } },
};
// the held throws (entered from a grab that lands): not picked on their own
const HK_HOLDS = {
  grabhold:  { tag: 'grabhold', on: { strike1() { this.holdHit(30); }, strike2() { this.holdHit(38, true); }, throw() { this.holdThrow(22); } } },
  fgrabhold: { tag: 'fgrabhold', on: { burn1() { this.holdHit(28); }, burn2() { this.holdHit(34, true); }, throw() { this.holdThrow(24); } } },
};
// P2: a weapon is drawn, used for a short pattern, then dropped hissing (each slot: one move, or a choice by range)
const HK_SETS = {
  blade: ['draw_blade', ['bl_rising', 'bl_cleave', 'bl_charge'], ['bl_rising', 'bl_cleave', 'bl_charge'], 'drop_blade'],
  spear: ['draw_spear', ['sp_thrust', 'sp_lunge'], 'sp_thrust', 'sp_hurl'],      // one dash at most
  chain: ['draw_chain', ['ch_lash', 'ch_sweep', 'ch_hook'], ['ch_lash', 'ch_sweep', 'ch_hook'], 'drop_chain'],
};
const HK_RANGE = {   // [best min, best max] distance for the ranged choices inside a set
  bl_rising: [40, 150], bl_cleave: [0, 90], bl_charge: [60, 220], sp_thrust: [0, 120], sp_lunge: [110, 999],
  ch_lash: [60, 170], ch_sweep: [0, 90], ch_hook: [90, 260],
};

class HearthkeeperBoss extends BossBase {
  constructor(x, y) {
    super('hearthkeeper', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.hearthkeeper.hp * NGP.hp);
    this.stanceMax = this.stanceBase = HK_STANCE[1]; this.critRange = 58; this.speed = 1;
    this.state = 'dormant'; this.face = -1; this.recent = []; this.picks = {}; this.queue = []; this.cool = 0.8;
    this.temper = 0; this.tWin = HK_WIN[1]; this.weapon = null; this.airH = 0; this.darkT = 0; this.name = BOSS_INFO.hearthkeeper.name;
    this.sph = 1; this.fired = {}; this.setS('dormant', 'intro', false); this.anim.speed = 0;
  }
  // the floor between the walls either side of where he stands (AREA's arena or the training chamber)
  bounds() {
    if (this._bd && this._bd.room === room) return this._bd;
    if (room.id === 'CF8') return (this._bd = { room, L: 72, R: 782 });     // AREA: x 40..808 (fog .. furnace doors), less his longest in-sprite lunge (30 px)
    const def = room.def, ty = clamp(Math.floor(this.floor / TILE) - 2, 0, def.h - 1), tx = clamp(Math.floor(this.x / TILE), 1, def.w - 2);
    const solid = x => isSolidT(cellType((def.map[ty] || '')[x] || '#'));
    let a = tx, b = tx;
    while (a > 1 && !solid(a - 1)) a--;
    while (b < def.w - 2 && !solid(b + 1)) b++;
    let L = Math.max(a * TILE + 40, TILE + 40), R = Math.min((b + 1) * TILE - 40, room.pw - TILE - 40);
    if (R - L < 120) { L = TILE + 40; R = room.pw - TILE - 40; }
    return (this._bd = { room, L, R });
  }
  get L() { return this.bounds().L; }
  get R() { return this.bounds().R; }
  setS(st, tag, loop = true, ph = this.phase) {
    this.state = st; this.tag = tag; this.sph = ph;
    this.sh = hkSheet(tag, ph);
    this.anim = new Anim(this.sh, tag, loop, this.speed);
  }
  facePlayer() { if (Math.abs(P.x - this.x) > 6) this.face = P.x < this.x ? -1 : 1; }
  wake() { return Math.abs(P.x - this.x) < 15 * TILE && P.ground && P.state !== 'dead'; }
  activate() {
    if (this.active || this.cutting) return;
    super.activate();
    if (this.active && !this.cutting && this.state === 'dormant') { this.rising = true; this.setS('dormant', 'intro', false); this.anim.speed = 1.6; this.anim.i = 1; }
  }
  hurtbox() {
    if (!this.alive || this.hidden) return null;
    const B = hkM('body', this.tag, this.sph), r = (B && B[this.anim.i]) || HK_META().hurtbox || [66, 40, 30, 96];
    return metaRect(this.sh, this, r);
  }
  canStagger() { return !this.airH && !this.dash && !this.grabbed && this.state !== 'transform' && !(this.state === 'attack' && ['leap', 'sp_lunge'].includes(this.atk) && this.air); }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  onCritStart() { super.onCritStart(); this.cool0(); }
  cool0() { if (this.temper > 0) toast('The temper breaks. He is cold iron again.', 2.4); this.temper = 0; this.tWin = HK_WIN[this.phase]; this.applySpeed(); }
  applySpeed() { this.speed = (this.phase === 1 ? 1 : this.phase === 2 ? 1.08 : 1.16) * (1 + 0.06 * this.temper); }
  stagger() {
    if (this.pendShift) this.endShift();
    this.critDone = false; this.stanceImmune = 7; this.staggers = (this.staggers || 0) + 1;
    this.stanceMax = Math.min(this.stanceMax * 1.15, this.stanceBase * 2);
    this.stance = 0; this.chain = 0; this.airH = 0; this.y = this.floor; this.queue = []; this.dash = null; this.air = null; this.darkT = 0;
    this.releaseHold();
    if (this.weapon) hkDrop(this, this.weapon);
    this.cool0();
    this.setS('stagger', 'stagger', false); this.t = 2.0;
    sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 60, this.face);
  }
  hit(info) {
    if (!this.alive || !this.active) { if (!this.active && !this.cutting) this.activate(); return; }
    if (this.state === 'transform' || this.rising) return;
    // the temper channel is a commitment: blows there break stance harder
    if (this.state === 'attack' && this.atk === 'temper' && !info.crit) info = { ...info, poise: (info.poise || 0) * 1.6 };
    super.hit(info);
    if (!this.alive) return;
    if (this.phase === 1 && this.hp < this.maxHp * HK_P2AT) { this.hp = Math.round(this.maxHp * HK_P2AT); this.pendingPhase = 2; }
    if (this.phase === 2 && this.hp < this.maxHp * HK_P3AT) { this.hp = Math.round(this.maxHp * HK_P3AT); this.pendingPhase = 3; }
  }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 95; if (this.stance >= this.stanceMax && this.canStagger()) this.stagger(); }

  // ---------------------------------------------------------------- choosing
  weights(d, behind) {
    const ph = this.phase, band = d < 95 ? 0 : d < 185 ? 1 : 2;
    if (ph === 1) {
      if (behind && d < 100) return { backhand: 3, snap: 0.4 };
      return [
        { combo: 1.4, snap: 1.4, sweep: 1.2, slam: 1.0, grab: 1.1, ring: 0.6, sparks: 0.2 },
        { slam: 1.3, grab: 1.2, ring: 1.0, leap: 0.9, sparks: 1.0, combo: 0.7, sweep: 0.6 },
        { leap: 1.8, sparks: 1.5, ring: 1.0, walk: 0.8 }][band];
    }
    if (ph === 2) {
      const w = [{ blade: 1.2, chain: 1.0, spear: 0.8, coal_kick: 0.9 }, { blade: 1.0, chain: 1.2, spear: 1.1, coal_kick: 0.8 },
        { spear: 1.5, chain: 1.2, blade: 0.6, coal_kick: 1.0, walk: 0.6 }][band];
      if (behind && d < 90) w.coal_kick = 0.3;
      return w;
    }
    return [
      { ft_combo: 1.4, ft_sweep: 1.0, flame_grab: 1.1, nova: 1.1, bellows_lo: 0.6, dark_lunge: 0.4 },
      { ft_sweep: 1.2, bellows_lo: 1.0, bellows_hi: 1.0, ember_rain: 1.0, dark_lunge: 1.2, nova: 0.6, flame_grab: 0.5 },
      { ember_rain: 1.4, bellows_lo: 1.2, bellows_hi: 1.2, dark_lunge: 1.4, ft_sweep: 0.8 }][band];
  }
  pickMove() {
    if (this.tWin <= 0) return 'temper';
    const d = Math.abs(P.x - this.x), behind = (P.x - this.x) * this.face < -16;
    const w = this.weights(d, behind);
    const ban = this.recent.slice(0, 1);
    let e = Object.entries(w).filter(([k, v]) => v > 0 && !ban.includes(k));
    if (!e.length) e = Object.entries(w);
    e = e.map(([k, v]) => [k, v / (1 + 0.45 * (this.picks[k] || 0))]);     // favour what he hasn't shown yet this phase
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e[0][0];
  }
  begin(m) {
    HK.log.push(m); if (HK.log.length > 600) HK.log.shift();
    this.recent.unshift(m); this.recent.length = Math.min(this.recent.length, 4); this.picks[m] = (this.picks[m] || 0) + 1;
    if (m === 'walk') { this.facePlayer(); this.setS('walk', 'walk'); this.t = rand(0.7, 1.1); return; }
    if (HK_SETS[m]) { this.queue = HK_SETS[m].slice(); this.set = m; return this.next(); }
    this.queue = []; this.set = null; this.start(m);
  }
  next() {
    let s = this.queue.shift();
    if (!s) return false;
    if (Array.isArray(s)) {   // a choice by range, never the one just used
      const d = Math.abs(P.x - this.x), ok = s.filter(k => k !== this.last);
      const fit = ok.filter(k => !HK_RANGE[k] || (d >= HK_RANGE[k][0] && d <= HK_RANGE[k][1]));
      const L = fit.length ? fit : ok.length ? ok : s;
      s = L[irand(0, L.length - 1)];
    }
    this.start(s); return true;
  }
  start(m) {
    if (this.pendShift) this.endShift();
    if (!['backhand'].includes(m)) this.facePlayer();
    this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.hooked = false; this.brk = 0;
    const M = HK_MOVES[m];
    this.setS('attack', M.tag, false);
    this.anim.speed = this.speed;
    if (m === 'temper') { this.chan = this.phase === 1 ? 1.8 : 1.5; sfx.charge(); if (!HK.said.temper) { HK.said.temper = 1; toast('The Hearthkeeper kneels to re-temper. Break his stance!', 2.6); } }
    if (M.unbl) { this.unblT = 0.9; sfx.charge(); }
  }

  // ---------------------------------------------------------------- update
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim;
    this.unblT = Math.max(0, (this.unblT || 0) - dt);
    if (this.state === 'dead') { an.update(dt); this.events(); if (an.done) an.hold(); this.ambient(dt); return; }
    if (this.state === 'transform') {    // update only runs in play: no scene is driving the change, so it plays out itself
      an.update(dt); this.ambient(dt);
      if (an.done && this.transformTo) this.finishPhase(this.transformTo);
      return;
    }
    if (!this.active) { an.update(dt); if (!this.cutting && this.wake()) this.activate(); this.ambient(dt); return; }
    if (this.rising) {    // a repeat meeting: he stands up out of his vigil without the scene
      an.update(dt);
      if (an.done) { this.rising = false; this.setS('idle', 'idle'); this.cool = 0.5; }
      this.ambient(dt); return;
    }
    if (!['stagger', 'transform'].includes(this.state) && !this.pendingPhase && P.state !== 'dead') this.tWin -= dt;
    if (!this.holdF) an.speed = this.speed;
    an.update(dt);
    if (this.pendingPhase && ['idle', 'walk'].includes(this.state) && P.state !== 'dead' && state === 'play') return this.phaseScene(this.pendingPhase);
    switch (this.state) {
      case 'dormant': case 'idle':
        if (this.tag !== 'idle' || this.state === 'dormant') this.setS('idle', 'idle');
        this.facePlayer(); this.cool -= dt;
        if (P.state !== 'dead' && this.cool <= 0) this.begin(this.pickMove());
        break;
      case 'walk': {
        this.t -= dt; this.facePlayer();
        this.x = clamp(this.x + this.face * 48 * this.speed * dt, this.L, this.R);
        if (an.changed && an.i % 4 === 0) { sfx.step(); shake = Math.max(shake, 1); }
        if (this.t <= 0 || Math.abs(P.x - this.x) < 100) { this.setS('idle', 'idle'); this.cool = Math.min(this.cool, 0.12); }
        break;
      }
      case 'ready':   // between the moves of a weapon set: the last frame (his guard) held a beat (its travel not yet applied)
        this.t -= dt; an.i = an.n - 1; an.t = 0;
        if (this.t <= 0) { if (!this.next()) { this.setS('idle', 'idle'); this.cool = 0.4; } }
        break;
      case 'attack': this.updateAttack(dt); break;
      case 'stagger': {
        this.t -= dt;
        const kn = (hkM('events', 'stagger', this.sph) || {}).kneel ?? an.n - 1;
        if (an.i >= kn && this.t > 0.45) { an.i = kn; an.t = 0; }
        if (an.done) { this.endShift(); this.setS('idle', 'idle'); this.cool = 0.35; }
        break;
      }
    }
    this.x = clamp(this.x, this.L, this.R);
    this.airH = Math.max(0, this.airH || 0);
    this.y = this.floor - this.airH;
    this.ambient(dt);
  }
  events() {
    const an = this.anim; if (!an.changed) return;
    const ev = hkM('events', this.tag, this.sph); if (!ev) return;
    const M = HK_MOVES[this.atk] && HK_MOVES[this.atk].tag === this.tag ? HK_MOVES[this.atk] : HK_HOLDS[this.tag] || null;
    for (const [k, f] of Object.entries(ev)) {
      if (f !== an.i || this.fired[k]) continue;
      this.fired[k] = 1;
      if (M && M.on && M.on[k]) M.on[k].call(this);
      if (HK_SCENE[k]) HK_SCENE[k](this);
    }
  }
  updateAttack(dt) {
    const an = this.anim, hold = HK_HOLDS[this.tag], M = hold || HK_MOVES[this.atk], tag = this.tag, ph = this.sph;
    const wins = ((hkM('attacks', tag, ph) || {}).windows) || [];
    const first = wins.length ? wins[0].active[0] : 99;
    if (an.i < first - 1 && !M.noTrack && !hold && !this.dash && !this.air) this.facePlayer();
    if (an.changed) for (const tq of hkM('telegraph', tag, ph) || []) if (tq.frame === an.i) {
      const p = metaPoint(this.sh, this, tq.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint();
      if (M.unbl) { HK.flare = { x: p.x, y: p.y, t: 0.5 }; sfx.howl(); }
    }
    this.fired = this.fired || {};
    if (M.step && M.step[an.i] && !hold) this.x = clamp(this.x + this.face * M.step[an.i] * dt * this.speed, this.L, this.R);   // stepping into the reach
    this.events();
    if (this.atk === 'temper') this.temperTick(dt);
    if (this.dash) this.dashTick(dt);
    if (this.air) this.airTick(dt);
    if (this.grabbed) this.holdTick(dt);
    if (this.hooked && an.i >= ((hkM('events', tag, ph) || {}).yank ?? 99) && P.state !== 'dead') {   // hauled in on the chain
      const tx = clamp(this.x + this.face * 34, this.L - 20, this.R + 20);
      P.x = approach(P.x, tx, 300 * dt); P.vx = 0;
      if (Math.random() < 0.5) particles.push({ x: P.x, y: P.y - 12, vx: rand(-20, 20), vy: -rand(10, 30), life: 0.4, kind: 'fire' });
    }
    // hit windows
    if (!hold) wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (this.phase >= 2) sfx.fire(); }
      if (this.hitIds.has(wi)) return;
      const r = metaRect(this.sh, this, (w.rects && w.rects[an.i]) || w.hit);
      if (overlap(r, playerHurtbox())) {
        const dmg = hkDmg((M.dmg && (M.dmg[wi] ?? M.dmg[0])) || 40, this);
        if (hurtPlayer(dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: !!(M.parry && M.parry[wi]) && !M.unbl, src: this, burn: M.burn })) {
          this.hitIds.add(wi);
          if (M.onHit) M.onHit.call(this, wi);
        }
      }
    });
    if (an.done) this.endMove();
  }
  endShift() {
    const sx = hkM('shift', this.tag, this.sph);
    if (sx) this.x = clamp(this.x + this.face * sx, this.L, this.R);
    this.pendShift = false;
  }
  endMove() {
    const a = this.atk;
    const toGuard = this.queue.length && P.state !== 'dead' && !this.pendingPhase;
    if (toGuard) this.pendShift = true; else this.endShift();
    this.air = null; this.dash = null; this.airH = 0; this.darkT = 0; this.releaseHold(); this.hooked = false; this.holdF = false;
    if (this.pendingPhase) { this.queue = []; this.dropAll(); this.setS('idle', 'idle'); this.cool = 0.1; return; }
    if (this.queue.length && P.state !== 'dead') {
      // a weapon set: hold the guard a beat, then the next move (shorter in the last phases)
      this.state = 'ready'; this.t = (this.phase === 2 ? rand(0.35, 0.6) : 0.35) / (1 + 0.1 * this.temper); return;
    }
    const d = Math.abs(P.x - this.x), ph = this.phase;
    const chainP = ph === 3 ? 0.4 : ph === 2 ? 0.25 : 0.2;
    if (['snap', 'sweep', 'combo', 'backhand', 'ft_combo', 'ft_sweep', 'coal_kick'].includes(a) && this.chain < 1 && Math.random() < chainP && P.state !== 'dead' && this.tWin > 0) {
      this.chain++;
      const opts = ph === 1 ? (d < 90 ? ['snap', 'grab', 'sweep'] : ['ring', 'sparks', 'leap']) : ph === 2 ? ['coal_kick'] : (d < 90 ? ['nova', 'flame_grab', 'ft_combo'] : ['dark_lunge', 'bellows_lo', 'bellows_hi']);
      const nx = opts.filter(o => !this.recent.slice(0, 2).includes(o));
      if (nx.length) return this.begin(nx[irand(0, nx.length - 1)]);
    }
    this.chain = 0; this.setS('idle', 'idle');
    this.cool = (ph === 1 ? rand(0.8, 1.3) : ph === 2 ? rand(0.6, 1.0) : rand(0.45, 0.8)) / (1 + 0.15 * this.temper);
  }
  dropAll() { if (this.weapon) hkDrop(this, this.weapon); }
  // ---- tempering
  temperTick(dt) {
    const an = this.anim, ev = hkM('events', this.tag, this.sph) || {};
    if (this.chan > 0) {
      this.chan -= dt;
      if (ev.loop1 !== undefined && an.i > ev.loop1) { an.i = ev.loop0; an.t = 0; }
      if (Math.random() < 0.6) particles.push({ x: this.x + this.face * rand(18, 34), y: this.floor - rand(0, 4), vx: rand(-30, 30), vy: -rand(40, 110), g: 260, life: rand(0.4, 0.8), kind: 'fire' });
      addLight(this.x + this.face * 26, this.floor - 6, 46, '255,150,70', 0.8);
    }
  }
  tempered() {
    this.temper = Math.min(2, this.temper + 1); this.tWin = HK_WIN[this.phase]; this.applySpeed();
    flashScreen = Math.max(flashScreen, 0.25); shake = Math.max(shake, 5); hkSfx.anvil(); sfx.fire();
    toast(this.temper >= 2 ? 'Tempered again: his weapon burns white.' : 'Re-tempered: his weapon glows, and strikes harder.', 2.6);
  }
  // ---- the leap: carried over to you on 'takeoff', held at the top, down on 'land'
  leapStart() {
    const ev = hkM('events', 'leap', 1) || {}, pt = (HK_META().pts.p1 || {}).leap, hp = pt && pt[ev.land];
    const reach = hp ? hp[0] - HK_META().anchor[0] : 56;
    this.facePlayer();
    this.air = { x0: this.x, tx: clamp(P.x - this.face * reach, this.L, this.R), t: 0, T: 0.8, apex: ev.apex };
    sfx.jump(); spawnFx('dust', this.x, this.floor, this.face);
  }
  airTick(dt) {
    const A = this.air, an = this.anim; A.t += dt;
    const k = clamp(A.t / A.T, 0, 1);
    this.x = lerp(A.x0, A.tx, k * k * (3 - 2 * k));
    this.airH = Math.sin(Math.PI * k) * 74;
    if (an.i >= A.apex && k < 0.86) { an.i = A.apex; an.t = 0; }
    if (this.fired.land) { this.airH = 0; this.x = A.tx; this.air = null; }
  }
  // ---- the spear dash: the frame holds while he crosses the floor
  dashStart(off = 70) {
    this.facePlayer();
    const end = clamp(P.x + this.face * off, this.L, this.R);
    this.dash = { to: end, t: 0 }; this.holdF = true; this.anim.speed = 0; sfx.spear && sfx.spear(); sfx.bossSwing();
  }
  dashTick(dt) {
    const D_ = this.dash; D_.t += dt;
    this.x = approach(this.x, D_.to, 360 * dt);
    if (Math.random() < 0.8) particles.push({ x: this.x - this.face * rand(4, 20), y: this.floor - rand(0, 6), vx: -this.face * rand(30, 80), vy: -rand(10, 40), life: 0.4, kind: Math.random() < 0.5 ? 'fire' : 'dust' });
    if (Math.abs(this.x - D_.to) < 2 || D_.t > 0.9 || this.x <= this.L || this.x >= this.R) { this.dash = null; this.holdF = false; this.anim.speed = this.speed; spawnFx('dust', this.x, this.floor, this.face); shake = Math.max(shake, 3); }
  }
  // ---- the holds: the tongs (P1), the burning hand (P3)
  startHold(tag) {
    if (this.grabbed || P.state === 'dead') return;
    this.grabbed = true; this.fired = {};
    this.setS('attack', tag, false); this.anim.speed = this.speed; this.hitIds = new Set();
    sfx.fire(); flashScreen = Math.max(flashScreen, 0.2);
  }
  holdPt() {
    const k = this.tag === 'fgrabhold' ? 'p3_handf' : 'p1_tong', L = (HK_META().pts[k] || {})[this.tag];
    const q = L && L[this.anim.i];
    return q ? metaPoint(this.sh, this, q) : { x: this.x + this.face * 40, y: this.y - 60 };
  }
  holdTick(dt) {
    if (P.state === 'dead') { this.releaseHold(); return; }
    const q = this.holdPt();
    P.x = clamp(q.x, TILE + 8, room.pw - TILE - 8); P.y = Math.min(this.floor, q.y + 22); P.vx = 0; P.vy = 0;
    if (P.state !== 'hurt') setP('hurt', 'hurt');
    if (Math.random() < 0.6) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(4, 22), vx: rand(-20, 20), vy: -rand(20, 50), life: 0.5, kind: 'fire' });
    addLight(q.x, q.y, 44, '255,170,90', 0.8);
  }
  holdHit(d, big) {
    if (!this.grabbed) return;
    P.inv = 0; hurtPlayer(hkDmg(d, this), this.face, ++hazardId, { src: this });
    if (P.state !== 'dead') setP('hurt', 'hurt');
    shake = Math.max(shake, big ? 8 : 5); (big ? sfx.bigHit : sfx.hit)(); hkSfx.anvil();
    const q = this.holdPt(); spawnFx(fxOr('parry_spark', 'hit'), q.x, q.y + 6, this.face);
  }
  holdThrow(d) {
    if (!this.grabbed) return;
    P.inv = 0; hurtPlayer(hkDmg(d, this), this.face, ++hazardId, { src: this });
    this.grabbed = false; P.vx = this.face * 230; P.vy = -170; P.ground = false; sfx.boom();
  }
  releaseHold() { if (this.grabbed) { this.grabbed = false; if (P.state === 'hurt') P.vx = this.face * 160; } }

  // ---------------------------------------------------------------- phases
  phaseScene(ph) {
    if (this.pendShift) this.endShift();
    this.pendingPhase = 0; hkClearAttacks(); this.queue = []; this.releaseHold(); this.dropAll();
    this.state = 'transform'; this.stance = 0; this.airH = 0; this.y = this.floor; this.chain = 0; this.darkT = 0; this.facePlayer();
    const b = this, first = !SAVE.flags['cutp' + ph + ':hearthkeeper'];
    SAVE.flags['cutp' + ph + ':hearthkeeper'] = 1;
    const tag = ph === 2 ? 'p2shift' : 'p3shift', sph = ph - 1;
    const total = () => { let s = 0; for (let i = 0; i < b.anim.n; i++) s += b.anim.ms(i); return s / 1000; };
    b.setS('transform', tag, false, sph); b.fired = {};
    const steps = [
      { pan: { x: b.x + b.face * 20, y: b.y - 60 }, dur: 0.5 },
      ...(first ? [say('The Hearthkeeper', ph === 2 ? 'You would hold a blade the forge made? Then meet all of them.' : 'The forge is cold. Only the last fire is left — and it is mine to keep.')] : [wait(0.2)]),
      { dur: 0.1, until: () => b.anim.done, max: 6 },
      { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
    ];
    this.transformTo = ph;
    playCutscene(steps, () => b.finishPhase(ph));
  }
  // the end of a change (the scene's end, or -- when no scene can run, as in headless benches -- the animation's end)
  finishPhase(ph) {
    const b = this, tag = ph === 2 ? 'p2shift' : 'p3shift';
    if (b.transformTo !== ph) return;
    b.transformTo = 0;
    if (b.tag === tag) { b.fired = b.fired || {}; for (const k of ['impact', 'free', 'lift', 'kindle']) if (!b.fired[k] && HK_SCENE[k] && (hkM('events', tag, ph - 1) || {})[k] !== undefined) { b.fired[k] = 1; HK_SCENE[k](b); } }
    b.endShift();
    b.phase = ph; b.stanceMax = b.stanceBase = HK_STANCE[ph]; b.stanceImmune = 0; b.picks = {}; b.recent = [];
    b.tWin = HK_WIN[ph]; b.applySpeed();
    b.setS('idle', 'idle'); b.cool = 0.6; b.weapon = null;
    if (ph === 3) { b.name = 'The Hearthkeeper, the Last Fire'; hkDark(true); }
    bossBanner = { name: b.name, t: 0 };
  }
  die() {
    // he cannot fall before the last fire: a killing blow ends the phase instead
    if (this.phase < 3) { this.hp = Math.max(1, Math.round(this.maxHp * (this.phase === 1 ? HK_P2AT : HK_P3AT))); this.pendingPhase = this.phase + 1; return; }
    this.releaseHold(); this.queue = []; this.dropAll();
    this.state = 'dead'; this.airH = 0; this.y = this.floor; this.darkT = 0; this.hidden = false;
    this.setS('dead', 'death', false, 3); this.fired = {};
    hkClearAttacks(); projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.felled();
    victoryBanner = { text: 'THE HEARTH GOES COLD', t: 0 };
    this.rewards();
  }
  rewards() {
    // the Core is not handed over on the kill: it is left in the ash (see hkCoreProp), so it leaves the cores' auto-drop
    const c = CORES.hearthkeeper;
    if (c) delete CORES.hearthkeeper;
    try { super.rewards(); } finally { if (c) CORES.hearthkeeper = c; }
    if (!this.rematch && !this.trn && !(typeof TRAINING !== 'undefined' && TRAINING.on)) {
      SAVE.hk = { room: room.id, x: Math.round(this.x), y: Math.round(this.floor) };
      saveGame();
    }
  }
  // ---------------------------------------------------------------- look
  ambient(dt) {
    if (['transform', 'dead', 'dormant'].includes(this.state) || this.rising) this.events();
    if (this.state === 'dead' && this.anim.i >= ((hkM('events', 'death', 3) || {}).out ?? 99)) return;
    const ph = this.state === 'transform' ? this.sph : this.phase, head = this.headPt();
    const eye = { x: this.x + this.face * 3, y: this.y - 91 + (this.body() ? this.body().y0 - (this.y - 96) : 0) };
    addLight(eye.x, eye.y, 18, '255,150,70', 0.35);
    if (ph === 1 && this.temper > 0 && head) addLight(head.x, head.y, 26 + 8 * this.temper, '255,150,70', 0.5 + 0.15 * this.temper);
    if (ph === 2) {
      addLight(this.x + this.face * 14, this.floor - 4, 54, '255,130,60', 0.45);
      if (head && this.weapon) { addLight(head.x, head.y, 34 + 10 * this.temper, '255,170,90', 0.6 + 0.1 * this.temper); if (this.temper && Math.random() < 0.4) particles.push({ x: head.x + rand(-3, 3), y: head.y + rand(-3, 3), vx: rand(-10, 10), vy: -rand(20, 40), life: 0.5, kind: 'fire' }); }
    }
    if (ph === 3 && head) {
      const k = this.darkT > 0 ? 0.6 : 1;
      addLight(head.x, head.y, (70 + 14 * this.temper) * k, '255,190,120', 0.9);
      if (Math.random() < 0.5 + 0.2 * this.temper) particles.push({ x: head.x + rand(-2, 2), y: head.y - 3, vx: rand(-8, 8), vy: -rand(20, 50), life: rand(0.3, 0.6), kind: 'fire' });
    }
    // the tempering window running out: the weapon smokes
    if (this.active && this.alive && this.tWin < 6 && this.tWin > 0 && head && Math.random() < 0.3) particles.push({ x: head.x + rand(-3, 3), y: head.y - 2, vx: rand(-6, 6), vy: -rand(10, 25), life: 0.9, kind: 'ash' });
  }
  headPt() {
    const L = (HK_META().pts['p' + this.sph] || {})[this.tag], q = L && L[this.anim.i];
    return q ? metaPoint(this.sh, this, q) : null;
  }
  body() { return this.hurtbox(); }
  draw() {
    if (this.hidden) return;
    let opt = this.flash > 0 ? { flash: Math.min(0.22, this.flash * 0.3), flashColor: '#b8b0a6' } : this.state === 'stagger' ? { flash: 0.12 + 0.08 * Math.sin(time * 20), flashColor: '#e6e4f0' } : {};
    if (this.darkT > 0) opt = { flash: 0.82, flashColor: '#07060a' };       // gone into the dark: only the coal shows
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    this.drawHeat();
    if (this.darkT > 0) { const h = this.headPt(); if (h) drawGlow(() => { g.fillStyle = '#fff4dc'; g.fillRect(Math.round(h.x) - 1, Math.round(h.y) - 1, 3, 3); g.fillStyle = 'rgba(255,170,80,0.6)'; g.fillRect(Math.round(h.x) - 2, Math.round(h.y) - 2, 5, 5); }); }
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 84 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
  }
  // the re-tempered hammer: its head glows from the meta's heat pixels (face white-hot, edges red)
  drawHeat() {
    if (this.sph !== 1 || !(this.temper > 0 || this.tag === 'temper')) return;
    const H = (HK_META().heat.p1 || {})[this.tag], L = H && H[this.anim.i]; if (!L || !L.length) return;
    const sh = this.sh, flip = this.face !== sh.native, k = this.tag === 'temper' && !this.temper ? clamp(this.anim.i / 8, 0, 1) : 1;
    const hot = this.temper >= 2 ? ['#ffe2a0', '#f07f24'] : ['#ffb453', '#cf4c14'];
    drawGlow(() => {
      g.globalAlpha = 0.85 * k;
      for (let i = 0; i < L.length; i += 3) {
        const fx = L[i], fy = L[i + 1], lv = L[i + 2];
        const x = flip ? Math.round(this.x) - (fx - sh.ax) - 1 : Math.round(this.x) + (fx - sh.ax), y = Math.round(this.y) - sh.ay + fy;
        g.fillStyle = lv >= 2 ? hot[0] : hot[1]; g.fillRect(x, y, 1, 1);
      }
      g.globalAlpha = 1;
    });
  }
}

// ---------------------------------------------------------------- things that leave his body
function hkClearAttacks() { HK.shots = []; HK.sparks = []; HK.ash = []; HK.jets = []; HK.rings = []; HK.spears = []; HK.flare = null; }
const hkArenaX = x => clamp(x, TILE + 8, room.pw - TILE - 8);
function hkPt(b, which = 'head') {
  const k = which === 'hand' ? 'p' + b.sph + '_hand' : 'p' + b.sph, L = (HK_META().pts[k] || {})[b.tag], q = L && L[b.anim.i];
  return q ? metaPoint(b.sh, b, q) : { x: b.x + b.face * 40, y: b.y - 50 };
}
// a heavy blow landing: dust, a short shock either side; tempered, the floor where it fell burns a moment
function hkLand(b, kind, big) {
  const p = hkPt(b), x = p.x;
  shake = Math.max(shake, big ? 11 : 8); sfx.boom(); if (kind === 'hammer') hkSfx.anvil();
  spawnFx(fxOr('slam_impact', 'shockwave'), x, b.floor, b.face);
  for (let i = 0; i < 14; i++) particles.push({ x: x + rand(-16, 16), y: b.floor - 2, vx: rand(-110, 110), vy: -rand(40, 150), g: 320, life: 0.7, kind: i % 2 ? (b.phase >= 2 || b.temper ? 'fire' : 'spark') : 'dust' });
  hazards.push({ hk: true, x, y: b.floor, w: big ? 64 : 48, h: 16, dmg: hkDmg(big ? 28 : 22, b), id: ++hazardId, life: 0.12, update() {} });
  if (b.temper > 0 || kind === 'blade') HK.shots.push({ kind: 'patch', x, y: b.floor, vx: 0, dir: b.face, life: 1.2 + 0.4 * b.temper, id: ++hazardId, dmg: hkDmg(16, b), w: 30, h: 10, every: 0.5 });
}
// the ringing floor: shock rings run both ways along the floor (cold blue-white in his first phase); jump them
function hkRing(b) {
  const p = hkPt(b); hkSfx.ring(); shake = Math.max(shake, 7);
  const n = 1 + (b.temper >= 1 ? 1 : 0);
  for (let k = 0; k < n; k++) for (const dir of [-1, 1]) HK.shots.push({ kind: 'ring', x: p.x + dir * 10, y: b.floor, vx: dir * (175 + k * 40), dir, life: 2.4, id: ++hazardId, dmg: hkDmg(36, b), w: 14, h: 16, delay: k * 0.4 });
}
// sparks struck off the hammer: a fan of hot points flying at you, fizzling where they land
function hkSparks(b) {
  const p = hkPt(b), n = 5 + 2 * b.temper; sfx.fire(); hkSfx.anvil();
  for (let i = 0; i < n; i++) {   // each lands at its own spot around you: a fan to read and slip between
    const tx = P.x + (i - (n - 1) / 2) * 26 + rand(-4, 4);
    HK.sparks.push(Object.assign({ x: p.x, y: p.y, g: 380, id: ++hazardId, dmg: hkDmg(24, b), life: 2.5, big: false }, hkLob(p, tx, b.floor, -150 - 30 * (i % 3), 380)));
  }
}
// a lob from p that comes down at (tx, floor) with launch speed vy0 (negative = up)
function hkLob(p, tx, floor, vy0, g_) {
  const h = floor - 2 - p.y, T = (-vy0 + Math.sqrt(vy0 * vy0 + 2 * g_ * Math.max(0, h))) / g_;
  return { vx: clamp((tx - p.x) / Math.max(0.2, T), -420, 420), vy: vy0 };
}
function hkCoals(b) {
  const p = { x: b.x + b.face * 40, y: b.floor - 8 }, n = 5 + b.temper; sfx.fire();
  for (let i = 0; i < n; i++) { const tx = P.x + (i - (n - 1) / 2) * 30 + rand(-5, 5); HK.sparks.push(Object.assign({ x: p.x, y: p.y, g: 420, id: ++hazardId, dmg: hkDmg(26, b), life: 3, big: true }, hkLob(p, tx, b.floor, -130 - 25 * (i % 3), 420))); }
}
// ground fire running along the floor (the rising cut, the charged chop, the flame sweep)
function hkCrescent(b, dir, spd) {
  const d = dir * b.face, p = hkPt(b);
  HK.shots.push({ kind: 'fire', x: clamp(p.x, b.L - 40, b.R + 40), y: b.floor, vx: d * spd, dir: d, life: 2.4, id: ++hazardId, dmg: hkDmg(b.phase >= 3 ? 40 : 36, b), w: 18, h: 26 });
  sfx.fire();
}
function hkDrawn(b, w) {
  b.weapon = w; const p = hkPt(b); sfx.fire(); flashScreen = Math.max(flashScreen, 0.1);
  for (let i = 0; i < 16; i++) particles.push({ x: b.x + b.face * rand(20, 40), y: b.floor - 2, vx: rand(-60, 60), vy: -rand(60, 160), g: 300, life: rand(0.5, 1), kind: 'fire' });
  if (p) addLight(p.x, p.y, 60, '255,180,100', 1);
  if (!HK.said[w]) { HK.said[w] = 1; toast({ blade: 'He draws a blade from the coals.', spear: 'He draws a spear from the coals.', chain: 'He draws a chain from the coals.' }[w], 2); }
}
function hkDrop(b, w) {
  if (!w) return;
  const h = hkPt(b, 'hand');
  HK.props.push({ kind: w, x: clamp(h.x, b.L - 30, b.R + 30), y: b.floor, face: b.face, t: 0 });
  b.weapon = null; hkSfx.hiss();
}
// the thrown spear: a hot javelin at where you will be; it sticks, and bursts a breath later
function hkHurl(b) {
  const p = hkPt(b, 'hand'); b.weapon = null;
  const tx = P.x + P.vx * 0.3, ty = P.y - 12, t = clamp(Math.abs(tx - p.x) / 330, 0.3, 0.75), g_ = 260;
  HK.spears.push({ x: p.x, y: p.y, vx: (tx - p.x) / t, vy: (ty - p.y) / t - 0.5 * g_ * t, g: g_, id: ++hazardId, dmg: hkDmg(44, b), st: 'fly', t: 0 });
  sfx.spear ? sfx.spear() : sfx.bossSwing();
}
// ember rain: curtains of embers; where each will fall the floor glows first (the light is the cue)
function hkEmberRain(b) {
  sfx.crumble(); sfx.fire(); flashScreen = Math.max(flashScreen, 0.15);
  const L = b.L - 24, R = b.R + 24, waves = 3 + (b.temper >= 1 ? 1 : 0);
  for (let w = 0; w < waves; w++) {
    const g1 = rand(L + 40, R - 40); let g2 = rand(L + 40, R - 40);
    for (let n = 0; n < 8 && Math.abs(g2 - g1) < 130; n++) g2 = rand(L + 40, R - 40);
    const gaps = [w === 0 ? clamp(P.x + rand(-50, 50), L + 30, R - 30) : g1, g2];
    for (let x = L; x <= R; x += 22) if (!gaps.some(gx => Math.abs(x - gx) < 30)) HK.ash.push({ x: x + rand(-3, 3), y: 0, fall: false, delay: 0.75 + w * 1.15, id: ++hazardId, dmg: hkDmg(32, b), fl: b.floor });
  }
}
// the bellows blast: a jet of fire out of the coal across the floor, low (jump it) or high (stay down); a thin line of
// light shows where it will run first
function hkJet(b, lvl) {
  const p = hkPt(b), dir = b.face, x0 = p.x, x1 = dir > 0 ? b.R + 40 : b.L - 40;
  const band = lvl === 'lo' ? [b.floor - 17, b.floor] : [b.floor - 54, b.floor - 28];
  HK.jets.push({ x0, x1, y0: band[0], y1: band[1], dir, st: 'warn', t: 0, warn: 0.3, dur: 0.6 + 0.1 * b.temper, id: ++hazardId, dmg: hkDmg(46, b) });
  sfx.charge();
}
function hkNova(b) {
  const p = hkPt(b); shake = Math.max(shake, 9); sfx.boom(); sfx.roar(); flashScreen = Math.max(flashScreen, 0.35);
  for (let k = 0; k <= b.temper && k < 2; k++) HK.rings.push({ x: p.x, y: p.y, r: 6 - k * 60, v: 165, id: ++hazardId, dmg: hkDmg(44, b), fl: b.floor });
  hazards.push({ hk: true, x: b.x, y: b.floor, w: 70, h: 70, dmg: hkDmg(40, b), id: ++hazardId, life: 0.12, update() {} });
}

// ---------------------------------------------------------------- scene events (the transforms, the intro, the death)
const HK_SCENE = {
  impact(b) { shake = 12; sfx.boom(); hkSfx.anvil(); flashScreen = 0.4; for (let i = 0; i < 30; i++) particles.push({ x: b.x + b.face * rand(10, 70), y: b.floor - 2, vx: rand(-120, 120), vy: -rand(60, 200), g: 300, life: rand(0.6, 1.2), kind: 'fire' }); HK.coalsT = 1; },
  free(b) {   // the hammer stays in the coals
    const L = (HK_META().pts.p1 || {}).p2shift, q = L && L[L.length - 1];
    const p = q ? metaPoint(b.sh, b, q) : { x: b.x + b.face * 40, y: b.floor };
    HK.props.push({ kind: 'hammer', x: p.x, y: b.floor, face: b.face, t: 0, keep: true });
  },
  lift(b) { hkDark(true); sfx.kindle(); flashScreen = 0.3; },
  kindle(b) { sfx.fire(); shake = 4; },
  ignite(b) { sfx.kindle(); flashScreen = Math.max(flashScreen, 0.15); },
  plant(b) { shake = 4; sfx.boom(); },
  ash(b) { sfx.crumble(); },
  gone(b) { hkDark(false); if (!b.rematch && !b.trn && !(typeof TRAINING !== 'undefined' && TRAINING.on) && !SAVE.flags['w2:open']) hkCoreProp(b.x, b.floor); HK.props = HK.props.filter(p => p.kind !== 'hammer'); HK.props.push({ kind: 'crown', x: b.x - b.face * 4, y: b.floor, face: b.face, t: 0, keep: true }); },
};

// ---------------------------------------------------------------- the Hearthkeeper's Core: taken, not given
function hkCoreProp(x, y) {
  if (props.some(p => p.type === 'hk_core')) return;
  const p = { type: 'hk_core', x, y, face: 1, t: 0, anim: { update() {} },
    prompt() { return 'Take the Hearthkeeper’s Core'; },
    interact() { hkTakeCore(this); return true; },
    update(dt) { this.t += dt; addLight(this.x, this.y - 12, 40 + 6 * Math.sin(this.t * 2.4), '255,190,120', 0.8); if (Math.random() < 0.25) particles.push({ x: this.x + rand(-3, 3), y: this.y - 14, vx: rand(-5, 5), vy: -rand(10, 25), life: rand(0.6, 1.1), kind: 'ember' }); },
    draw() { const sh = sheet('hearthkeeper_props'); if (!sh.ok) return; const t = sh.tag('core'); drawGlow(() => drawSprite(sh, t.from + Math.floor(this.t * 5) % (t.to - t.from + 1), this.x, this.y + 4, 1, { pivot: [36, 52] })); } };
  props.push(p); return p;
}
function hkTakeCore(p) {
  props = props.filter(q => q !== p);
  if (typeof crGrant === 'function' && !crGrant('hearthkeeper')) banner(CORES.hearthkeeper.name, 'Its fire is yours already. The furnace answers it all the same.', 'core_hearthkeeper');
  SAVE.flags['w2:open'] = 1; if (SAVE.hk) SAVE.hk.taken = 1;
  flashScreen = Math.max(flashScreen, 0.3); sfx.kindle && sfx.kindle();
  for (let i = 0; i < 24; i++) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(4, 20), vx: rand(-40, 40), vy: -rand(30, 90), life: rand(0.5, 1.1), kind: 'ember' });
  saveGame();
  if (typeof cfFurnaceOpen === 'function') { try { cfFurnaceOpen(); } catch (e) { console.error(e); } }
}
// the Core: a stance trait (balanced with the other 32: docs/BOSS_CORES.md)
CORES.hearthkeeper = { name: 'Hearthkeeper’s Core', trait: 'Retemper', col: '#ffb45a', pk: 'ember', poise: 0.12,
  desc: '+12% stance damage; breaking a foe’s stance re-tempers the weapon: the next three enchanted moves deal +12%.',
  proc(t, info, A, x) {
    if (!t || !x.first) return;
    const n = t.staggers || 0;
    if (t.state === 'stagger' && t._crHkSeen !== n) { t._crHkSeen = n; CR.hk = { n: 3, mv: CR.mv }; if (typeof crU === 'function') crU('retemper', 1); }
  },
  edgeFn() { const H = CR.hk; if (!H) return 0; if (H.last === CR.mv) return 0.12; if (H.n <= 0 || H.mv === CR.mv) return 0; H.last = CR.mv; H.n--; return 0.12; } };
CORES.hearthkeeper.kind = 'hearthkeeper'; CORES.hearthkeeper.rgb = '255,180,90';

// ---------------------------------------------------------------- the dark of the last phase (lighting only)
function hkDark(on) {
  if (!room) return;
  if (room.id === 'CF8' && typeof cfArenaDark === 'function') { HK.darkOn = !!on; return; }   // AREA's arena dims itself (HK.darkK eases in)
  const base = room.def.hkBase || room.def;
  if (!on) { if (room.def.hkBase) room.def = base; HK.darkOn = false; return; }
  const b0 = base.biome, nb = 'hk_dark_' + b0, A = AREAS[b0] || {};
  if (!AREAS[nb]) {
    AREAS[nb] = Object.assign({}, A, { ambient: Math.min(0.93, Math.max((A.ambient || 0.5) + 0.25, 0.82)), tint: '#1c1418' });
    if (typeof SCALES !== 'undefined' && SCALES[b0]) SCALES[nb] = SCALES[b0];
    if (typeof ROOTS !== 'undefined' && ROOTS[b0]) ROOTS[nb] = ROOTS[b0];
    if (typeof LX_AMB !== 'undefined') { const c = (LX_AMB[b0] || '150,140,140').split(',').map(Number); LX_AMB[nb] = c.map(v => Math.round(v * 0.55)).join(','); }
  }
  for (const k of ['far', 'mid']) if (!SHEETS[`bg_${nb}_${k}`]) SHEETS[`bg_${nb}_${k}`] = sheet(`bg_${b0}_${k}`);
  room.def = Object.assign(Object.create(base), { biome: nb, hkBase: base });
  HK.darkOn = true;
}

// ---------------------------------------------------------------- the per-frame world
HOOKS.enter.push(def => {
  hkClearAttacks(); HK.props = []; HK.darkOn = false; HK.darkK = 0;
  // the Core still lies where he burned away, until it is taken
  const S = SAVE && SAVE.hk;
  if (S && S.room === def.id && SAVE.flags['boss:hearthkeeper'] && !SAVE.flags['w2:open'] && !(typeof TRAINING !== 'undefined' && TRAINING.on)) {
    hkCoreProp(S.x, S.y); HK.props.push({ kind: 'crown', x: S.x - 4, y: S.y, face: 1, t: 99, keep: true });
  }
});
HOOKS.death.push(() => { hkClearAttacks(); });
HOOKS.update.push(dt => {
  if (room && room.id === 'CF8' && typeof cfArenaDark === 'function') { const k0 = HK.darkK || 0, k = approach(k0, HK.darkOn ? 1 : 0, dt * 0.7); if (k !== k0 || k > 0) { HK.darkK = k; cfArenaDark(k); } }
  for (const p of HK.props) p.t += dt;
  HK.props = HK.props.filter(p => p.keep || p.t < 7);
  if (HK.flare) { HK.flare.t -= dt; if (HK.flare.t <= 0) HK.flare = null; }
  const B = boss && boss.kind === 'hearthkeeper' ? boss : null;
  if (!B || !B.alive) { if (HK.shots.length || HK.sparks.length || HK.ash.length || HK.jets.length || HK.rings.length || HK.spears.length) hkClearAttacks(); if (HK.darkOn && (!B || B.state !== 'dead')) hkDark(false); return; }
  const hb = playerHurtbox();
  for (const s of HK.shots) {
    if (s.delay > 0) { s.delay -= dt; continue; }
    s.life -= dt; s.x += s.vx * dt;
    if (s.x < TILE + 4 || s.x > room.pw - TILE - 4) s.life = 0;
    if (s.kind === 'patch') { s.tick = (s.tick || 0) - dt; if (s.tick <= 0 && overlap(rect(s.x - s.w / 2, s.y - s.h, s.x + s.w / 2, s.y), hb)) { s.tick = s.every; hurtPlayer(s.dmg, P.x < s.x ? -1 : 1, ++hazardId, { src: B, burn: 8 }); } addLight(s.x, s.y - 4, 26, '255,140,60', 0.5); continue; }
    if (Math.random() < 0.5) particles.push({ x: s.x - s.dir * rand(0, 10), y: s.y - rand(0, s.h * 0.6), vx: -s.dir * rand(5, 25), vy: -rand(20, 50), life: 0.5, kind: s.kind === 'ring' ? 'spark' : 'fire' });
    addLight(s.x, s.y - 10, s.kind === 'ring' ? 28 : 40, s.kind === 'ring' ? '200,220,255' : '255,160,80', 0.8);
    if (!s.hit && overlap(rect(s.x - s.w / 2, s.y - s.h, s.x + s.w / 2, s.y), hb) && hurtPlayer(s.dmg, s.dir, s.id, { src: B, burn: s.kind === 'fire' ? 12 : 0 })) s.hit = true;
  }
  HK.shots = HK.shots.filter(s => s.life > 0);
  for (const s of HK.sparks) {
    s.life -= dt;
    if (s.ground) { s.gt -= dt; if (s.gt <= 0) s.life = 0; if (s.big && !s.hit2 && overlap(rect(s.x - 5, s.y - 6, s.x + 5, s.y), hb) && hurtPlayer(s.dmg * 0.5, 0, s.id + 0.5, { src: B, burn: 8 })) s.hit2 = true; continue; }
    s.vy += s.g * dt; s.x += s.vx * dt; s.y += s.vy * dt;
    if (s.y >= B.floor - 1) { s.y = B.floor - 1; s.ground = true; s.gt = s.big ? 1.2 : 0.35; }
    if (s.x < TILE + 4 || s.x > room.pw - TILE - 4) s.life = 0;
    if (!s.hit && overlap(rect(s.x - 3, s.y - 3, s.x + 3, s.y + 3), hb) && hurtPlayer(s.dmg, s.vx < 0 ? -1 : 1, s.id, { src: B, burn: s.big ? 10 : 0 })) { s.hit = true; s.life = 0; }
    addLight(s.x, s.y, s.big ? 20 : 14, '255,170,90', 0.6);
  }
  HK.sparks = HK.sparks.filter(s => s.life > 0);
  for (const s of HK.spears) {
    s.t += dt;
    if (s.st === 'fly') {
      s.vy += s.g * dt; s.x += s.vx * dt; s.y += s.vy * dt;
      if (!s.hit && overlap(rect(s.x - 5, s.y - 4, s.x + 5, s.y + 4), hb) && hurtPlayer(s.dmg, s.vx < 0 ? -1 : 1, s.id, { src: B, burn: 10 })) s.hit = true;
      if (s.y >= B.floor - 2 || s.x < TILE + 6 || s.x > room.pw - TILE - 6) { s.y = Math.min(s.y, B.floor - 2); s.st = 'stuck'; s.t = 0; s.ang = Math.atan2(s.vy, s.vx); sfx.boom(); shake = Math.max(shake, 3); }
      addLight(s.x, s.y, 26, '255,170,90', 0.7);
    } else if (s.st === 'stuck') {
      addLight(s.x, s.y - 4, 30 + 30 * s.t, '255,150,70', 0.6 + 0.4 * s.t);
      if (s.t > 0.45) { s.st = 'gone'; hazards.push({ hk: true, x: s.x, y: B.floor, w: 48, h: 30, dmg: hkDmg(36, B), id: ++hazardId, life: 0.14, update() {} }); sfx.fire(); sfx.boom(); spawnFx(fxOr('slam_impact', 'shockwave'), s.x, B.floor, 1); for (let i = 0; i < 18; i++) particles.push({ x: s.x + rand(-10, 10), y: B.floor - 2, vx: rand(-90, 90), vy: -rand(40, 150), g: 300, life: 0.7, kind: 'fire' }); }
    }
  }
  HK.spears = HK.spears.filter(s => s.st !== 'gone');
  for (const a of HK.ash) {
    if (!a.fall) { a.delay -= dt; addLight(a.x, a.fl - 2, 16, '255,160,80', 0.35 + 0.25 * Math.sin(time * 14)); if (a.delay <= 0) { a.fall = true; a.y = cam.y - 12; } continue; }
    a.y += 320 * dt;
    if (Math.random() < 0.3) particles.push({ x: a.x + rand(-2, 2), y: a.y - rand(0, 8), vx: 0, vy: -rand(5, 20), life: 0.4, kind: 'fire' });
    if (!a.hit && overlap(rect(a.x - 4, a.y - 10, a.x + 4, a.y), hb) && hurtPlayer(a.dmg, P.x < a.x ? -1 : 1, a.id, { src: B, burn: 8 })) a.hit = true;
    addLight(a.x, a.y - 4, 18, '255,170,90', 0.6);
    if (a.y >= a.fl) { a.gone = true; for (let i = 0; i < 3; i++) particles.push({ x: a.x, y: a.fl - 2, vx: rand(-40, 40), vy: -rand(20, 60), g: 300, life: 0.4, kind: 'fire' }); }
  }
  HK.ash = HK.ash.filter(a => !a.gone);
  for (const j of HK.jets) {
    j.t += dt;
    if (j.st === 'warn' && j.t >= j.warn) { j.st = 'fire'; j.t = 0; sfx.fire(); sfx.boom(); shake = Math.max(shake, 5); }
    else if (j.st === 'fire') {
      const lo = Math.min(j.x0, j.x1), hi = Math.max(j.x0, j.x1), reach = Math.min(1, j.t / 0.12);
      const xa = j.dir > 0 ? j.x0 : j.x0 - (j.x0 - j.x1) * reach, xb = j.dir > 0 ? j.x0 + (j.x1 - j.x0) * reach : j.x0;
      if (!j.hit && overlap(rect(Math.max(lo, xa), j.y0, Math.min(hi, xb), j.y1), hb) && hurtPlayer(j.dmg, j.dir, j.id, { src: B, burn: 14 })) j.hit = true;
      for (let x = Math.min(xa, xb); x < Math.max(xa, xb); x += 36) addLight(x, (j.y0 + j.y1) / 2, 34, '255,150,70', 0.7);
      if (Math.random() < 0.9) particles.push({ x: rand(Math.min(xa, xb), Math.max(xa, xb)), y: rand(j.y0, j.y1), vx: j.dir * rand(60, 160), vy: -rand(10, 50), life: 0.45, kind: 'fire' });
      if (j.t >= j.dur) j.st = 'gone';
    }
  }
  HK.jets = HK.jets.filter(j => j.st !== 'gone');
  for (const r of HK.rings) {
    r.r += r.v * dt; if (r.r <= 0) continue;
    const d = Math.hypot(P.x - r.x, P.y - 12 - r.y);
    if (!r.hit && Math.abs(d - r.r) < 7 && hurtPlayer(r.dmg, P.x < r.x ? -1 : 1, r.id, { src: B, burn: 10 })) r.hit = true;
  }
  HK.rings = HK.rings.filter(r => r.r < 300);
});
HOOKS.render.push(() => {
  // the weapons he left behind: the hammer in the coals, the dropped blade / chain cooling and hissing, the crown
  const ps = sheet('hearthkeeper_props');
  if (ps.ok) for (const p of HK.props) {
    const t = ps.tag(p.kind); if (!t) continue;
    const n = t.to - t.from + 1, k = p.kind === 'hammer' ? Math.min(n - 1, Math.floor(p.t / 4)) : p.kind === 'crown' ? 0 : Math.min(n - 1, Math.floor(p.t / 1.3));
    drawSprite(ps, t.from + k, p.x, p.y + 4, p.face, { pivot: [36, 52] });
    if (p.kind !== 'crown' && k < n - 1) { addLight(p.x, p.y - 4, 30, '255,140,60', 0.6 * (1 - k / n)); if (Math.random() < 0.15) particles.push({ x: p.x + rand(-14, 14), y: p.y - 3, vx: rand(-4, 4), vy: -rand(12, 26), life: 0.9, kind: 'dust' }); }
  }
  const B = boss && boss.kind === 'hearthkeeper' ? boss : null;
  if (!B) return;
  drawGlow(() => {
    // the grab tell: the jaws flare red-orange (it cannot be blocked)
    if (HK.flare) { const a = HK.flare.t / 0.5; g.fillStyle = `rgba(255,90,40,${0.7 * a})`; g.fillRect(Math.round(HK.flare.x) - 3, Math.round(HK.flare.y) - 1, 7, 3); g.fillRect(Math.round(HK.flare.x) - 1, Math.round(HK.flare.y) - 3, 3, 7); addLight(HK.flare.x, HK.flare.y, 30, '255,90,40', a); }
    for (const s of HK.shots) {
      if (s.delay > 0) continue;
      const X = Math.round(s.x), Y = Math.round(s.y);
      if (s.kind === 'ring') {           // the anvil's ring: a thin standing ripple of cold light
        for (let i = 0; i < s.h; i++) { const w = Math.round(3 * Math.sin((i / s.h) * Math.PI) + 1); g.fillStyle = i % 3 ? 'rgba(184,198,210,0.75)' : 'rgba(226,235,242,0.95)'; g.fillRect(X - w, Y - i - 1, 1, 1); g.fillRect(X + w, Y - i - 1, 1, 1); }
        g.fillStyle = 'rgba(226,235,242,0.5)'; g.fillRect(X - 7, Y - 1, 14, 1);
      } else if (s.kind === 'patch') {
        for (let x = -s.w / 2; x < s.w / 2; x += 2) { const h = 2 + Math.round(3 * Math.abs(Math.sin(x * 0.7 + time * 9))); g.fillStyle = 'rgba(207,76,20,0.8)'; g.fillRect(X + x, Y - h, 2, h); g.fillStyle = '#ffb453'; g.fillRect(X + x, Y - 1, 1, 1); }
      } else {                           // a running wall of fire, leaning into its travel
        for (let i = 0; i < s.h; i++) {
          const k = i / s.h, w = Math.round((s.w / 2) * (1 - k) * (0.7 + 0.3 * Math.sin(time * 20 + i)));
          g.fillStyle = k < 0.25 ? '#fff8e8' : k < 0.5 ? '#ffb453' : k < 0.75 ? '#f07f24' : 'rgba(207,76,20,0.8)';
          g.fillRect(X - w + Math.round(s.dir * k * 4), Y - i - 1, Math.max(1, w * 2 - 2), 1);
        }
      }
    }
    for (const s of HK.sparks) {
      const X = Math.round(s.x), Y = Math.round(s.y);
      if (s.ground) { const a = s.gt / (s.big ? 1.2 : 0.35); g.fillStyle = `rgba(255,180,83,${a})`; g.fillRect(X - (s.big ? 2 : 1), Y - 1, s.big ? 4 : 2, 1); if (s.big) { g.fillStyle = `rgba(240,127,36,${a})`; g.fillRect(X - 1, Y - 3 - Math.round(Math.sin(time * 16) + 1), 2, 2); } continue; }
      g.fillStyle = '#fff8e8'; g.fillRect(X - (s.big ? 1 : 0), Y - (s.big ? 1 : 0), s.big ? 3 : 2, s.big ? 3 : 2);
      g.fillStyle = 'rgba(240,127,36,0.8)'; g.fillRect(Math.round(X - s.vx * 0.02), Math.round(Y - s.vy * 0.02), 1, 1);
    }
    for (const a of HK.ash) {
      if (!a.fall) { const k = 0.4 + 0.35 * Math.sin(time * 16); g.fillStyle = `rgba(255,170,90,${k})`; g.fillRect(Math.round(a.x) - 4, Math.round(a.fl) - 1, 8, 1); continue; }
      g.fillStyle = '#ffe2a0'; g.fillRect(Math.round(a.x) - 1, Math.round(a.y) - 5, 3, 5); g.fillStyle = 'rgba(240,127,36,0.7)'; g.fillRect(Math.round(a.x), Math.round(a.y) - 12, 1, 7);
    }
    for (const j of HK.jets) {
      const ym = Math.round((j.y0 + j.y1) / 2);
      if (j.st === 'warn') { const a = 0.35 + 0.4 * Math.sin(time * 40); g.fillStyle = `rgba(255,190,120,${a})`; const xa = Math.min(j.x0, j.x1), xb = Math.max(j.x0, j.x1); for (let x = xa; x < xb; x += 3) g.fillRect(Math.round(x), ym, 2, 1); continue; }
      const reach = Math.min(1, j.t / 0.12), fade = j.t > j.dur - 0.15 ? (j.dur - j.t) / 0.15 : 1;
      const xa = j.dir > 0 ? j.x0 : j.x0 - (j.x0 - j.x1) * reach, xb = j.dir > 0 ? j.x0 + (j.x1 - j.x0) * reach : j.x0;
      for (let x = Math.min(xa, xb); x < Math.max(xa, xb); x += 2) {
        const h = (j.y1 - j.y0) / 2 * (0.75 + 0.25 * Math.sin(x * 0.3 + time * 30)), X = Math.round(x);
        g.fillStyle = `rgba(207,76,20,${0.7 * fade})`; g.fillRect(X, Math.round(ym - h), 2, Math.round(h * 2));
        g.fillStyle = `rgba(255,180,83,${0.9 * fade})`; g.fillRect(X, Math.round(ym - h * 0.55), 2, Math.round(h * 1.1));
        g.fillStyle = `rgba(255,248,232,${fade})`; g.fillRect(X, ym - 1, 2, 2);
      }
    }
    for (const r of HK.rings) {
      if (r.r <= 0) continue;
      const n = Math.max(24, Math.floor(r.r * 0.9)), a = clamp(1.3 - r.r / 300, 0.25, 1);
      for (let k = 0; k < n; k++) { const th = k / n * 6.283, x = r.x + Math.cos(th) * r.r, y = r.y + Math.sin(th) * r.r; if (y > r.fl + 1) continue; g.fillStyle = k % 3 ? `rgba(255,180,83,${a})` : `rgba(255,248,232,${a})`; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2); }
      for (let k = 0; k < 6; k++) { const th = k / 6 * 6.283 + time; addLight(r.x + Math.cos(th) * r.r, r.y + Math.sin(th) * r.r, 34, '255,170,90', 0.55 * a); }
    }
  });
  // the thrown spear (lit by the game's lighting like the dropped weapons)
  if (ps.ok) for (const s of HK.spears) { const t = ps.tag('spearfly'); const ang = s.st === 'fly' ? Math.atan2(s.vy, s.vx) : s.ang; drawRotated(ps, t.from, s.x, s.y, ang, 1); }
});
// the tempering bar: under his health, the window running down; two pips for the levels he has
HOOKS.hud.push(() => {
  const b = boss; if (!b || b.kind !== 'hearthkeeper' || !b.active || !b.alive || state !== 'play') return;
  const bx = 156, by = 208, bw = 216, f = clamp(b.tWin / HK_WIN[b.phase], 0, 1);
  const X = ox + bx * scale, Y = oy + by * scale, Hh = Math.max(1, scale * 0.9);
  vctx.fillStyle = 'rgba(18,12,16,0.85)'; vctx.fillRect(X, Y, bw * scale, Hh);
  vctx.fillStyle = f < 0.2 ? `rgba(255,${120 + 60 * Math.sin(time * 10)},60,0.95)` : 'rgba(150,170,190,0.8)'; vctx.fillRect(X, Y, bw * scale * f, Hh);
  for (let i = 0; i < 2; i++) { vctx.fillStyle = i < b.temper ? (b.temper >= 2 ? '#ffe2a0' : '#f07f24') : 'rgba(60,50,46,0.9)'; vctx.fillRect(X + (bw + 3 + i * 4) * scale, Y - scale, 2.5 * scale, 2.5 * scale); }
});

// ---------------------------------------------------------------- the meeting (first time; Esc skips)
BOSS_CUTS.hearthkeeper = b => [
  act(() => { b.setS('dormant', 'intro', false); b.anim.speed = 0; b.anim.i = 0; b.face = P.x < b.x ? -1 : 1; }),
  bossPan(b, 50, 1.2),
  say('', 'Beneath the Last Hearth, someone has kept the fire all this while.'),
  act(() => { b.anim.speed = 1; b.fired = {}; }),
  { dur: 1.6, tween: () => { if (Math.random() < 0.5) particles.push({ x: b.x + rand(-8, 8), y: b.y - rand(40, 90), vx: rand(-6, 6), vy: -rand(10, 30), life: rand(0.6, 1.2), kind: 'ember' }); } },
  say('The Hearthkeeper', 'Every blade the Hallow carried was drawn from this fire. You carry one of them.'),
  say('The Hearthkeeper', 'Lay it on the anvil… or be tempered with it.', { dur: 2.0 }),
  { dur: 0.1, until: () => b.anim.done, max: 3 },
  { do() { b.rising = false; if (b.tag !== 'idle') b.setS('dormant', 'idle'); b.anim.speed = 1; }, always: true },
];
BOSS_SPAWN.hearthkeeper = (cx, fy) => sheet('hearthkeeper_p1_1').ok ? new HearthkeeperBoss(cx, fy) : null;
if (typeof window !== 'undefined' && window.__game) window.__game.hk = { HK, HK_MOVES, HK_HOLDS, HK_SETS, HearthkeeperBoss, hkDark, hkTakeCore, hkCoreProp,
  moves: () => Object.keys(HK_MOVES), meta: HK_META,
  force(m) { const b = boss; if (!b || b.kind !== 'hearthkeeper') return false; b.cool = 99; b.begin(m); return true; },
  hold() { if (boss) boss.cool = 99; },
  ev: s => eval(s) };
