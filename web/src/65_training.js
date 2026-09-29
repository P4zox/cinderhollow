// ------------------------------------------------------------------ Training Grounds (agent TR): a white dev test chamber
// reached from the title screen. trainingStart() swaps in a throwaway SAVE and drops you in TR1 (tools/regions/90_training.py);
// Esc opens the control panel (player stats and cheats, weapon, magic & charms, skills, spawns, world); trainingExit()
// goes back to the title with the real save untouched.
// Isolation: while TRAINING.on, saveGame/saveSettings are no-ops, localStorage writes are dropped (key/pad bindings aside),
// every setTimeout made in the sandbox is cancelled on exit, deaths respawn you in the room, and endings are skipped.
// Bosses are summoned into TR2 by re-entering it with its def masked to the boss's home biome (so the region's hooks,
// hazards and tiers run as at home) while the chamber still draws, lights and sounds like the white chamber.
const TRAINING = { on: false };
const TRN = { real: null, killed: null, settings: null, timers: new Set(), blocked: [], base: {}, ohk: false, hitbox: false, freeze: false, ts: 1,
  count: 1, last: null, id: 0, tab: 0, step: 1, arena: 'home', stay: true };
const TRN_COUNTS = [1, 3, 5, 10, 20], TRN_FOE_CAP = 80;   // summoned foes alive at once, at most
const TRN_ROOMS = ['TR1', 'TR2'];
for (const id of TRN_ROOMS) if (ROOM_BY[id]) TRN.base[id] = ROOM_BY[id];
const trnRoom = R => !!(R && TRN.base[R.id]);                     // a training chamber (masked or not)
const trnHere = () => TRAINING.on && trnRoom(room);

// ---- the biome: bright, neutral, quiet
Object.assign(AREAS, { training: { name: 'Training Grounds', ambient: 0.02, amb: 'none', tint: '#f1f2f4', map: '#9aa0a8', lx: { amb: '250,250,252', lvl: 0.98 } } });
Object.assign(SCALES, { training: [0, 2, 4, 7, 9] });
Object.assign(ROOTS, { training: 65.4 });
if (typeof LX_AMB !== 'undefined') LX_AMB.training = '250,250,252';

// ================================================================== isolation
// 1) saveGame / saveSettings do nothing in the sandbox (re-wrapped on start in case a later file replaced them)
function trnGuard(name) {
  const f = window[name]; if (!f || f.trnWrap) return;
  const w = function (...a) { if (TRAINING.on) return; return f.apply(this, a); }; w.trnWrap = true;
  window[name] = w;
}
{ const _sg = saveGame; saveGame = function (...a) { if (TRAINING.on) return; return _sg.apply(this, a); }; saveGame.trnWrap = true; }
{ const _ss = saveSettings; saveSettings = function (...a) { if (TRAINING.on) { if (master) master.gain.value = SETTINGS.sfx; return; } return _ss.apply(this, a); }; saveSettings.trnWrap = true; }
// 2) storage: whatever still tries to write (a later save-slot layer, a stray helper) is dropped and logged
{ const SP = Storage.prototype, _set = SP.setItem, _rem = SP.removeItem, _clr = SP.clear;
  const ok = k => k === KEYS_STORE || k === PAD_STORE;
  SP.setItem = function (k, v) { if (TRAINING.on && this === window.localStorage && !ok(k)) { TRN.blocked.push(k); return; } return _set.call(this, k, v); };
  SP.removeItem = function (k) { if (TRAINING.on && this === window.localStorage && !ok(k)) { TRN.blocked.push('-' + k); return; } return _rem.call(this, k); };
  SP.clear = function () { if (TRAINING.on && this === window.localStorage) { TRN.blocked.push('*clear'); return; } return _clr.call(this); }; }
// 3) delayed callbacks (boss rewards, toasts, grants) made in the sandbox die with it
{ const _st = window.setTimeout; window.setTimeout = function (fn, ms, ...a) { const id = _st(fn, ms, ...a); if (TRAINING.on) TRN.timers.add(id); return id; }; }
// 4) no endings, no New Game+ from in here
{ const _be = beginEnding, _fs = finishStory;
  beginEnding = function (...a) { if (TRAINING.on) { state = 'play'; toast('Ending skipped: this is only a test', 3); return; } return _be.apply(this, a); };
  finishStory = function (...a) { if (TRAINING.on) { state = 'play'; dialog = null; toast('Ending skipped: this is only a test', 3); return; } return _fs.apply(this, a); }; }
// 5) death: back on your feet in the chamber, nothing lost
{ const _fd = finishDeath; finishDeath = function (...a) { if (!TRAINING.on) return _fd.apply(this, a); trnRespawn(); }; }

const TRN_ITEMS = ['hook', 'emberdash', 'gale', 'slam', 'wings', 'talon', 'tidebreath', 'moonstep'];
const TRN_SETTING_KEYS = ['god', 'infst', 'inffp', 'nocd'];
function trnNewSave() {
  const s = newSave();
  s.stats = { vig: 30, mnd: 20, end: 25, str: 25, dex: 25, fth: 20 };
  s.weapons = {}; for (const id of Object.keys(WEAPONS)) s.weapons[id] = 0;
  s.weapon = 'longsword';
  s.spellsOwned = Object.keys(SPELLS); s.spellSlots = 4; s.spellsEq = s.spellsOwned.slice(0, 2); s.spell = s.spellsEq[0] || null;
  s.charms = Object.keys(CHARMS); s.charmSlots = 4; s.charmsEq = [];
  for (const it of TRN_ITEMS) s.items[it] = 1;
  s.shards = 999; s.flaskBase = 6; s.flaskBlue = 2; s.diff = 1; s.skillv = 2; s.freeRespec = 0;
  s.inv = { emberstone: 99, tear: 9 };
  s.seenAreas = {}; for (const b of Object.keys(AREAS)) s.seenAreas[b] = 1;   // no cinematic region cards in here
  for (const k of Object.keys(BOSS_INFO)) for (const f of ['cut:', 'cutp2:', 'cutp3:']) s.flags[f + k] = 1;
  for (const id of TRN_ROOMS) s.visited[id] = 1;
  s.hints = { move: 1, heavy: 1, down: 1, rest: 1, boss: 1, menu: 1 };
  s.x3 = {}; s.trn = 1;
  return s;
}
function trnSpawnPt(id) {
  const def = TRN.base[id]; let sx = 8 * TILE + 8, sy = 19 * TILE;
  for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf('P'); if (x >= 0) { sx = x * TILE + 8; sy = (y + 1) * TILE; } }
  return [sx, sy];
}
function trainingStart() {
  if (TRAINING.on || !TRN.base.TR1) return;
  TRN.real = SAVE; TRN.killed = killed; TRN.settings = {}; for (const k of TRN_SETTING_KEYS) TRN.settings[k] = SETTINGS[k];
  TRN.blocked = []; TRN.timers.clear(); TRN.ohk = false; TRN.freeze = false; TRN.ts = 1; TRN.hitbox = false; TRN.last = null;
  TRAINING.on = true;
  trnGuard('saveGame'); trnGuard('saveSettings');
  for (const k of TRN_SETTING_KEYS) SETTINGS[k] = 0;
  SAVE = trnNewSave(); killed = new Set(); updNGP(); if (typeof wbLockArt === 'function') wbLockArt();
  if (typeof TITLE_DIFF !== 'undefined') TITLE_DIFF.open = false;
  menu = null; dialog = null; cut = null; boss = null; darkT = 0; slowmo = 0; hitstop = 0; victoryBanner = null; bossBanner = null; toasts = [];
  const [sx, sy] = trnSpawnPt('TR1');
  newPlayer(sx, sy); enterRoom('TR1', sx, sy, { card: true });
  state = 'play'; stateT = 0; clearBuffer(); fadeT = 0.3; fadePhase = 2;
  setTimeout(() => { if (trnHere()) toast(`${TOUCH_UI ? 'Menu' : 'Esc'} opens the control panel`, 4); }, 900);
}
function trainingExit() {
  if (!TRAINING.on) return;
  for (const id of TRN.timers) clearTimeout(id); TRN.timers.clear();
  boss = null; enemies = []; projectiles = []; hazards = []; menu = null; dialog = null; cut = null; cine = null;
  darkT = 0; slowmo = 0; hitstop = 0; victoryBanner = null; bossBanner = null; bannerMsg = null; toasts = []; popups = [];
  for (const k of TRN_SETTING_KEYS) SETTINGS[k] = TRN.settings[k];
  SAVE = TRN.real; killed = TRN.killed || new Set(); TRN.real = null; TRN.ts = 1; TRN.freeze = false;
  TRAINING.on = false;
  updNGP(); if (master) master.gain.value = SETTINGS.sfx;
  state = 'title'; stateT = 0; clearBuffer();
  titleBackdrop();
  fadeT = 0.3; fadePhase = 2;
}
function trnRespawn() {
  fadeTo(() => {
    const id = room && TRN.base[room.id] ? room.id : 'TR1', [sx, sy] = trnSpawnPt(id);
    boss = null; enemies = enemies.filter(e => e.dummy && !e.trn);
    newPlayer(sx, sy); trnEnter(id, sx, sy);
    state = 'play'; setP('rise', pHas('rise') ? 'rise' : 'idle', false);
    toast('Back on your feet. Nothing was lost.', 2.5);
  });
}
function trnEnter(id, px, py, def) {   // (re)enter a chamber, optionally as a masked copy (a boss's biome, its home layout)
  const base = TRN.base[id];
  ROOM_BY[id] = def || base;
  try { enterRoom(id, px, py, { quiet: true }); } finally { ROOM_BY[id] = base; }
  if (room.def.biome !== 'training') {   // some regions repaint the room's back layer on entry (the Crimson Manor's interior): back to white
    renderRoomLayers(room); if (typeof CM !== 'undefined' && CM.back0) CM.back0 = room.back;
  }
  areaCard = null; regionCard = null; P.vx = P.vy = 0;
}

// ---- rendering always uses the chamber's own look, whatever biome the def is masked as
function trnUnmasked(R, fn) {
  if (!trnRoom(R) || R.def.biome === 'training') return fn();
  const d = R.def; R.def = Object.assign(Object.create(d), { biome: 'training' });
  try { return fn(); } finally { R.def = d; }
}
{ const f = drawParallax; drawParallax = function () { return trnUnmasked(room, f); }; }
{ const f = renderLighting; renderLighting = function () { return trnUnmasked(room, f); }; }
{ const f = renderRoomLayers; renderRoomLayers = function (R) { return trnUnmasked(R, () => f(R)); }; }
{ const f = ambientParticles; ambientParticles = function (dt) { if (trnRoom(room)) return; return f(dt); }; }
if (typeof lxCollect === 'function') { const f = lxCollect; lxCollect = function (ls) { return trnUnmasked(room, () => f(ls)); }; }

// ---- time scale and frozen AI
function trnFrozenUpdate(dt) { this.flash = Math.max(0, (this.flash || 0) - dt * 5); this.dmgT = (this.dmgT || 0) - dt; if (this.commonUpdate) this.commonUpdate(dt); }
function trnApplyFreeze() {
  const on = TRAINING.on && TRN.freeze;
  const set = o => { if (!o || o.dummy) return; if (on && o.alive !== false) o.update = trnFrozenUpdate; else if (o.update === trnFrozenUpdate) delete o.update; };
  for (const e of enemies) set(e);
  set(boss);
}
{ const _u = update; update = function (dt) {
  if (TRAINING.on && state === 'play') { trnApplyFreeze(); return _u(dt * TRN.ts); }
  return _u(dt);
}; }
// one-hit kills
{ const _o = outgoing; outgoing = function (...a) { const d = _o.apply(this, a); return TRAINING.on && TRN.ohk ? Math.max(d, 99999) : d; }; }

// ---- Esc / Tab in the sandbox open the control panel instead of the pause menu and the map
{ const _p = onPressHook; onPressHook = (a, repeat) => {
  if (TRAINING.on && state === 'play' && !repeat && (a === 'pause' || a === 'map')) { audio(); trnOpen(); return; }
  return _p(a, repeat);
}; }

// ================================================================== the training dummy (never dies; damage numbers + DPS)
Object.assign(ENEMY, { trn_dummy: { hp: 1000, cinders: 0, speed: 0, aggro: 0, range: 0, poise: 1, stance: 140, dmg: {}, cool: [1, 1] } });
class TrnDummy extends Enemy {
  constructor(x, y, key) {
    super('trn_dummy', x, y, key);
    Object.assign(this, { face: -1, dummy: true, lastHp: this.hp, log: [], total: 0, first: 0, lastHit: -99, lastDmg: 0 });
  }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.poise = 0; this.stance = Math.max(0, this.stance - dt * 6);
    this.bleed = Math.max(0, this.bleed - dt * 6); this.dmgT -= dt; this.x = this.home; this.vx = this.vy = 0;
    if (this.rotT > 0) { this.rotT -= dt; this.hp -= this.maxHp * 0.025 * dt; }
    this.anim.update(dt);
    if (this.state === 'hurt' && this.anim.done) this.setA('idle', 'idle');
    if (this.state === 'stagger' || this.state === 'parried') { this.t -= dt; if (this.t <= 0) this.setA('idle', 'idle'); }
    if (this.state === 'dead') this.setA('idle', 'idle');
    // every point of damage this frame, from any source (blows, bleed, rot, burn, frost…), then top the buffer back up
    const d = this.lastHp - this.hp;
    if (d > 0.5) {
      if (time - this.lastHit > 3) { this.total = 0; this.first = time; this.log = []; }
      this.total += d; this.lastHit = time; this.lastDmg = Math.round(d); this.log.push([time, d]);
    }
    this.hp = this.maxHp; this.lastHp = this.hp;
    this.log = this.log.filter(q => time - q[0] < 5);
  }
  hit(info) { super.hit(info); if (this.state === 'hurt') this.anim.set('hurt', false); }
  die() { this.state = 'hurt'; this.anim.set('hurt', false); }   // it only wobbles; update() books the overkill
  get dps() { if (!this.log.length) return 0; const span = Math.max(1, Math.min(5, time - Math.max(this.first, time - 5))); return this.log.reduce((s, q) => s + q[1], 0) / span; }
}
ENEMY_CLASSES.trn_dummy = TrnDummy;
SPAWNS.trn_dummy = (s, c) => { if (!enemies.some(e => e.key === c.key)) enemies.push(new TrnDummy(c.cx, c.fy, c.key)); };

// ================================================================== the chamber: labels, floor rulers, the sealed doorway
const TRN_LABELS = {
  TR1: [[24, 2.4, 'TEST CHAMBER 01', 9, 'center'], [24, 3.3, 'MOVEMENT  ·  DAMAGE LAB', 5, 'center'], [2.9, 3.4, 'WALL-JUMP', 5, 'center'],
        [28.5, 15.6, 'SPIKES  ·  POGO ↓ + ATTACK', 5, 'center'], [28.5, 9.2, 'HOOK', 5, 'center'], [38.5, 16.6, 'BRAMBLE', 5, 'center'],
        [16.5, 14.5, 'PLATFORMS', 5, 'center'], [44.6, 13.6, 'ARENA ▸', 6, 'center']],
  TR2: [[28, 2.4, 'TEST CHAMBER 02', 9, 'center'], [28, 3.3, 'ARENA  ·  SUMMON FROM THE PANEL', 5, 'center']],
};
const TRN_INK = '#2e3238';
function trnDoorOn() { return !!(boss && boss.alive && room && room.id === 'TR2'); }
HOOKS.enter.push(def => {
  if (!TRAINING.on || !TRN.base[def.id]) return;
  if (def.id === 'TR2' && def.map === TRN.base.TR2.map) room.dyn.push({ x0: 0, x1: 16, y0: 14 * TILE, y1: 19 * TILE, on: trnDoorOn });   // a boss fight keeps you in
});
HOOKS.update.push(dt => {
  if (!trnHere()) return;
  SAVE.shards = 999;
  // brambles hurt and bounce here too (their own logic only runs in the Thornveil)
  if (room.id === 'TR1' && typeof tvUpdateBrambles === 'function' && room.def.biome !== 'thornveil') { tvEnsure(); tvUpdateBrambles(dt); }
});
HOOKS.render.push(() => {
  if (!trnHere()) return;
  drawGlow(() => {
    const fy = 19 * TILE, R = room;
    g.fillStyle = TRN_INK;
    for (let x = 1; x < R.w - 1; x++) {   // floor ruler: a tick per tile, a long one every five, on whatever floor the column has
      const f = trnColFloor(x); if (f < 0) continue;
      const big = x % 5 === 0; g.fillRect(x * TILE, f * TILE + 3, 1, big ? 5 : 2);
    }
    if (R.id === 'TR2' && trnFlat()) for (let y = 2; y < 19; y++) { const big = (19 - y) % 5 === 0; g.fillRect(R.pw - 16 - (big ? 5 : 2), y * TILE, big ? 5 : 2, 1); }   // height ruler
    if (R.id === 'TR2' && trnFlat() && trnDoorOn()) {   // the doorway field while a boss lives
      const a = 0.35 + 0.15 * Math.sin(time * 6); g.fillStyle = `rgba(240,138,36,${a})`; g.fillRect(4, 15 * TILE, 8, 4 * TILE);
      g.fillStyle = 'rgba(240,138,36,0.9)'; for (let y = 15 * TILE; y < 19 * TILE; y += 6) g.fillRect(4 + ((y / 6 + Math.floor(time * 8)) % 2) * 6, y, 2, 3);
    }
    if (TRN.hitbox) trnDrawHitboxes();
  });
});
function trnColFloor(x) {   // the surface row of the floor in column x (the solid run rising from the bottom), -1 if none
  let y = room.h - 1; if (!isSolidT(tileAt(x, y))) return -1;
  while (y > 1 && isSolidT(tileAt(x, y - 1))) y--;
  return y > 1 ? y : -1;
}
function trnDrawHitboxes() {
  const box = (r, c) => { if (!r) return; g.strokeStyle = c; g.lineWidth = 1; g.strokeRect(Math.round(r.x0) + 0.5, Math.round(r.y0) + 0.5, Math.max(1, Math.round(r.x1 - r.x0) - 1), Math.max(1, Math.round(r.y1 - r.y0) - 1)); };
  box(playerHurtbox(), 'rgba(40,200,90,0.95)');
  const A = ATK[P.state];
  if (A && P.anim.i >= A.active[0] && P.anim.i <= A.active[1] && A.reach) {
    const side = !A.up && !A.down, front = side ? A.reach[1] * (A.cls ? 1 : D.W.reach) * (typeof REACH_MUL !== 'undefined' ? REACH_MUL : 1) : A.reach[1];
    box(rect(P.x + P.face * A.reach[0], P.y + A.ys[0], P.x + P.face * front, P.y + A.ys[1]), 'rgba(255,200,40,0.95)');
  }
  for (const t of targets()) { try { box(t.hurtbox && t.hurtbox(), 'rgba(60,150,255,0.95)'); } catch (e) {} }
  for (const h of hazards) { let on = false; try { on = !h.delay && (!h.active || h.active(h)); } catch (e) {} if (on && h.w) box(rect(h.x - h.w / 2, h.y - h.h, h.x + h.w / 2, h.y), 'rgba(230,40,40,0.9)'); }
  for (const p of projectiles) if (p.owner !== 'player') { const r = p.r || 4; box(rect(p.x - r, p.y - r, p.x + r, p.y + r), 'rgba(230,40,40,0.9)'); }
}
HOOKS.hud.push(() => {
  if (!trnHere() || state === 'cut') return;
  const L = room.id === 'TR2' && !trnFlat() ? [[room.w / 2, 3.4, 'TEST CHAMBER 02', 9, 'center'], [room.w / 2, 4.3, `LAYOUT OF ${(ROOM_BY[room.def.trnHome] || {}).name || ''}`.toUpperCase(), 5, 'center']] : TRN_LABELS[room.id] || [];
  for (const [tx, ty, s, sz, al] of L) {
    const x = tx * TILE - cam.x, y = ty * TILE - cam.y;
    if (x > -200 && x < W + 200 && y > 30 && y < H + 20) text(s, x, y, sz, TRN_INK, al, { shadow: false, spacing: sz > 7 ? 2.4 : 1.1, alpha: sz > 7 ? 0.8 : 0.65 });
  }
  for (let x = 5; x < room.w - 1; x += 5) { const f = trnColFloor(x); if (f < 0) continue; const sx = x * TILE - cam.x, sy = f * TILE + 14 - cam.y; if (sx > -10 && sx < W + 10 && sy < H + 10) text(String(x), sx, sy, 4, '#5a606a', 'center', { shadow: false, weight: 500 }); }
  if (room.id === 'TR2' && trnFlat()) for (let y = 5; y < 19; y += 5) { const sx = room.pw - 24 - cam.x, sy = (19 - y) * TILE + 2 - cam.y; if (sx < W + 10) text(String(y), sx, sy, 4, '#5a606a', 'right', { shadow: false, weight: 500 }); }
  for (const e of enemies) if (e.dummy) {   // the dummy's readout
    const x = e.x - cam.x, y = e.y - 58 - cam.y; if (x < -60 || x > W + 60) continue;
    const act = time - e.lastHit < 3, dps = Math.round(e.dps);
    text(act ? `DPS ${dps}` : 'DPS —', x, y, 6.2, act ? '#c8541a' : TRN_INK, 'center', { shadow: false, weight: 700 });
    text(`total ${Math.round(e.total)}  ·  last ${e.lastDmg}`, x, y + 7, 4.4, TRN_INK, 'center', { shadow: false, weight: 500, alpha: 0.85 });
  }
  if (TRN.freeze || TRN.ts !== 1 || TRN.ohk || TRN.hitbox) {   // active test modes, top right
    const tags = [TRN.freeze && 'AI FROZEN', TRN.ts !== 1 && `TIME ×${TRN.ts}`, TRN.ohk && 'ONE-HIT KILLS', TRN.hitbox && 'HITBOXES'].filter(Boolean);
    text(tags.join('  ·  '), W - 8, H - 8, 5, '#c8541a', 'right', { shadow: false, weight: 700 });
  }
});

// ================================================================== bosses: where each lives, how to bring it here
const TRN_MAKE = { hound: (x, y) => new Hound(x, y), omen: (x, y) => new Omen(x, y), kalden: (x, y) => makeKalden(x, y), vessel: (x, y) => makeVessel(x, y),
  sovereign: (x, y) => makeSovereign(x, y), librarian: (x, y) => makeLibrarian(x, y) };
const TRN_CHAR_BOSS = { H: 'hound', M: 'omen', Q: 'kalden', V: 'vessel', Z: 'sovereign', J: 'librarian' };
const TRN_BOSS_NOTE = {};    // kind -> reason it can't be summoned (greyed out in the panel)
let TRN_BOSS_LIST = null;
function trnBosses() {
  if (TRN_BOSS_LIST) return TRN_BOSS_LIST;
  const out = [], seen = new Set();
  const add = (kind, r, x, y, spec) => {
    if (seen.has(kind) || !BOSS_INFO[kind] || !(TRN_MAKE[kind] || BOSS_SPAWN[kind])) return; seen.add(kind);
    let fl = y + 1; while (fl < r.h && '#BY='.indexOf(r.map[fl][x]) < 0 && !isSolidT(cellType(r.map[fl][x]))) fl++;
    out.push({ kind, name: BOSS_INFO[kind].name, room: r.id, biome: r.biome, region: (AREAS[r.biome] || {}).name || r.biome,
               hx: x, hy: y, wall: Math.max(3, Math.min(x, r.w - 1 - x)), air: spec && spec.air ? Math.max(0, fl - (y + 1)) : 0, spec: spec || {} });   // bosses stand on the chamber floor (the Ferryman's boat sits on water at home)
  };
  for (const r of ROOMS) {
    if (r.test) continue;
    for (let y = 0; y < r.h; y++) for (let x = 0; x < r.w; x++) { const k = TRN_CHAR_BOSS[r.map[y][x]]; if (k) add(k, r, x, y); }
    for (const s of r.spawns || []) if (s.t === 'boss') add(s.kind, r, s.x, s.y, s);
    if (r.boss && !seen.has(r.boss)) add(r.boss, r, r.w - 8, r.h - 4);
  }
  if (BOSS_SPAWN.venn && ROOM_BY.X5) add('venn', ROOM_BY.X5, 40, 10);
  for (const k of Object.keys(BOSS_SPAWN)) if (!seen.has(k) && ROOM_BY.TR2) add(k, TRN.base.TR2, 40, 18);
  const order = []; for (const b of out) if (!order.includes(b.region)) order.push(b.region);
  out.sort((a, b) => order.indexOf(a.region) - order.indexOf(b.region));
  return (TRN_BOSS_LIST = out);
}
function trnPrepFlags(kind) {
  delete SAVE.flags['boss:' + kind];
  for (const f of ['cut:', 'cutp2:', 'cutp3:']) SAVE.flags[f + kind] = 1;
}
function trnSummonBoss(kind) {
  const B = trnBosses().find(b => b.kind === kind); if (!B) return false;
  if (TRN_BOSS_NOTE[kind]) { sfx.deny(); toast(TRN_BOSS_NOTE[kind], 3); return false; }
  menu = null; state = 'play'; clearBuffer();
  for (const id of TRN.timers) clearTimeout(id); TRN.timers.clear();   // the last fight's pending callbacks
  trnPrepFlags(kind); darkT = 0; victoryBanner = null; bossBanner = null;
  const home = trnUseHome(kind) && trnArenaDef(B);
  let bx, by, px, py;
  if (home) {   // the boss's own arena, drawn as the chamber: every hard-coded floor, wall and set piece lines up
    bx = B.hx * TILE + 8; by = (B.hy + 1) * TILE;
    const st = TRN_PSTART[kind] || trnStartNear(home, B.hx, B.hy);
    px = st[0] * TILE + 8; py = (st[1] + 1) * TILE;
    trnEnter('TR2', px, py, home);
  } else {      // the flat chamber, re-entered as the boss's biome
    const def = TRN.base.TR2, fy = 19 * TILE;
    px = 9 * TILE + 8; py = fy; bx = (def.w - 1 - B.wall) * TILE + 8; by = fy - B.air * TILE;
    trnEnter('TR2', px, py, { ...def, biome: B.biome, boss: kind });   // a plain copy: phase arenas spread or chain the def
  }
  P.face = bx < P.x ? -1 : 1; P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks(); setP('idle', 'idle', true);
  const make = TRN_MAKE[kind] || BOSS_SPAWN[kind];
  boss = make(bx, by, { ...B.spec, x: Math.floor(bx / TILE), y: Math.floor(by / TILE) - 1 });
  if (!boss) { toast('It did not come.', 2); return false; }
  boss.trn = true; TRN.last = kind;
  if (TRN_PREP[kind]) TRN_PREP[kind](boss);
  if (boss.hp && typeof diffScaleHp === 'function') diffRescale();
  updateCamera(0, true);
  return true;
}
// ---- arenas: the flat chamber, or the boss's home layout (terrain only, sealed, white) when its fight is built around it
const TRN_NEEDS_HOME = new Set(['sanguine', 'venn', 'saint0', 'vael', 'unwritten', 'choir', 'ferryman', 'coven', 'warden', 'cindervane', 'colossus', 'twins', 'pharaoh']);
const trnUseHome = kind => TRN.arena === 'home' || TRN_NEEDS_HOME.has(kind);
// where the player starts in each home layout (the rows the headless boss checks use; others: the far side's floor)
const TRN_PSTART = { hound: [6, 10], omen: [6, 10], kalden: [6, 10], vessel: [6, 10], sovereign: [6, 10], venn: [6, 10], librarian: [20, 10], unwritten: [3, 14],
  ice_warden: [31, 10], twins: [4, 13], bellringer: [3, 10], cindervane: [46, 15], overseer: [40, 10], colossus: [46, 14], oswin: [30, 10], sentinels: [3, 8],
  first_ember: [10, 10], coven: [31, 10], warden: [5, 10], ferryman: [8, 7], choir: [3, 15], butler: [3, 9], sanguine: [6, 14], executioners: [30, 10],
  vael: [40, 12], orrery: [5, 12], astrel: [5, 16], enforcer: [6, 12], saint0: [8, 10] };
const TRN_KEEP_SPAWNS = new Set(['cm_chandelier', 'db_boat', 'dp_crucible', 'hf_fall']);   // arena machinery, not decor
function trnFloorIn(def, x) { for (let y = 1; y < def.h; y++) if (isSolidT(cellType(def.map[y][x])) && !isSolidT(cellType(def.map[y - 1][x]))) return y; return def.h - 1; }
// a start on the boss's own floor level, about a dozen tiles away (toward the middle of the room first)
function trnStartNear(def, hx, hy) {
  const dir = hx > def.w / 2 ? -1 : 1, floorAt = x => { for (let y = Math.max(1, hy - 2); y < def.h; y++) if (isSolidT(cellType(def.map[y][x])) && !isSolidT(cellType(def.map[y - 1][x]))) return y; return -1; };
  for (const d of [12, 14, 10, 16, 8, 18, 6]) for (const s of [dir, -dir]) {
    const x = hx + s * d; if (x < 2 || x > def.w - 3) continue;
    if (floorAt(x) === hy + 1) return [x, hy];
  }
  const x = clamp(hx + dir * 10, 2, def.w - 3); return [x, trnFloorIn(def, x) - 1];
}
const TRN_ARENAS = {};
function trnArenaDef(B) {
  const home = ROOM_BY[B.room]; if (!home || home.test) return null;
  if (TRN_ARENAS[B.kind]) return TRN_ARENAS[B.kind];
  const map = home.map.map((row, y) => [...row].map((ch, x) => {
    let c = cellType(ch) !== T_EMPTY || ch === '@' || ch === '|' ? ch : '.';
    const edge = x === 0 || x === home.w - 1 || y === home.h - 1 || (y === 0 && home.indoor);   // sealed: its exits lead nowhere here
    if (edge && !isSolidT(cellType(c))) c = '#';
    return c;
  }).join(''));
  const base = TRN.base.TR2;
  return (TRN_ARENAS[B.kind] = { ...home, id: base.id, name: base.name, gx: base.gx, gy: base.gy, test: true, secret: false, shrine: undefined, npcs: [], chests: [], items: [],
    graves: [], map, spawns: (home.spawns || []).filter(s => TRN_KEEP_SPAWNS.has(s.t)), boss: B.kind, trnHome: home.id });
}
const trnFlat = () => !!(room && room.def.map === TRN.base.TR2.map);
// per-boss nudges: things their home arena would have done
const TRN_PREP = {
  champion: b => { b.called = true; },   // normally woken by sounding the banner in R4 and surviving its gauntlet
};
// a few arenas run their boss's set pieces from a room-id check; the chamber runs the same pieces for that boss
const TRN_BRIDGE = {
  unwritten: {   // A6: ink bullets, ink platforms, floods, pages and the page-turn inversion
    update: dt => { updateInkBullets(dt); updateInkPlats(dt); updateInkFloods(dt); updateInkPages(dt, boss); updateDrift(dt); },
    render: () => { renderInversion(); drawInkFloods(); drawInkPlats(); drawInkPages(); drawInkBullets(); },
  },
  sanguine: {    // CM7: the ballroom's blood drops, the Countess's hold and the blood-rain column
    update: dt => { if (typeof cmEnsure === 'function') cmEnsure(); cmBallroomUpdate(dt); },
    render: () => { if (!trnFlat()) cmBallroomDraw(); },
    top: () => { if (CM.col && CM.col.k > 0) { const r0 = CM.rain; CM.rain = { k: boss && boss.alive ? 0.6 : 0.3 }; cmDrawRain(); CM.rain = r0; } },
  },
};
// a boss cut to zero during its intro (one-hit kills) would stand back up: finish it
HOOKS.update.push(() => { if (trnHere() && boss && boss.trn && boss.alive && boss.hp <= 0 && boss.die) { boss.introT = 0; try { boss.die(); } catch (e) {} } });
const trnBridge = () => trnHere() && room.id === 'TR2' && boss && boss.trn ? TRN_BRIDGE[boss.kind] : null;
HOOKS.update.push(dt => { const b = trnBridge(); if (b && b.update) b.update(dt); });
HOOKS.render.push(() => { const b = trnBridge(); if (b && b.render) b.render(); });
HOOKS.renderTop.push(() => { const b = trnBridge(); if (b && b.top) b.top(); });
// King Vael's void draws its own floor line at his throne room's height: redraw it on the chamber's floor
if (typeof nvVoid === 'function') { const _nv = nvVoid; nvVoid = function (on) {
  const r = _nv(on);
  if (on && trnHere() && trnFlat() && typeof NVR !== 'undefined' && NVR.void) {
    const fx = room.front.getContext('2d'), fl = 19 * TILE; fx.clearRect(0, 0, room.pw, room.ph);
    fx.fillStyle = 'rgba(70,90,140,0.55)'; fx.fillRect(0, fl, room.pw, 1);
    fx.fillStyle = 'rgba(40,52,90,0.4)'; for (let x = 0; x < room.pw; x += 3) fx.fillRect(x, fl + 2, 1, 1);
  }
  return r;
}; }
// killing a summoned boss: the banner, but no flags, cinders or items (the SAVE is a throwaway anyway; this keeps it clean)
{ const _rw = BossBase.prototype.rewards; BossBase.prototype.rewards = function (...a) {
  if (!TRAINING.on) return _rw.apply(this, a);
  sfx.felled(); toast(`${this.name} felled (training: no rewards)`, 3);
}; }

// ---- enemies
let TRN_ENEMY_LIST = null;
const trnPretty = s => s.replace(/^(tv|db|cm|nv|du|sf|nh|hf|sp|dp|sc|kd|ra|rb|rc|sa|sb)_/, '').split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
const TRN_ENEMY_NOTE = {};
function trnEnemies() {
  if (TRN_ENEMY_LIST) return TRN_ENEMY_LIST;
  const home = {};
  for (const r of ROOMS) {
    if (r.test) continue;
    for (const row of r.map) for (const ch of row) { const t = ENEMY_CHARS[ch]; if (t && !home[t]) home[t] = r.biome; }
    for (const s of r.spawns || []) if (s.t === 'enemy' && !home[s.type]) home[s.type] = r.biome;
  }
  const out = [];
  for (const type of Object.keys(ENEMY)) {
    if (type === 'trn_dummy') continue;
    if (!sheet(type).ok && !ENEMY_CLASSES[type]) continue;
    const b = home[type];
    out.push({ type, name: ENEMY[type].name || trnPretty(type), elite: !!ENEMY[type].elite, fly: !!ENEMY[type].flying, biome: b, region: b ? (AREAS[b] || {}).name || b : 'Unplaced' });
  }
  const order = []; for (const r of ROOMS) if (!order.includes(r.biome)) order.push(r.biome);
  out.sort((a, b) => (a.biome ? order.indexOf(a.biome) : 999) - (b.biome ? order.indexOf(b.biome) : 999));
  return (TRN_ENEMY_LIST = out);
}
function trnFloorY(x) {   // the floor under x (px), from the player's height down
  const tx = clamp(Math.floor(x / TILE), 1, room.w - 2);
  for (let ty = Math.max(1, Math.floor((P.y - 1) / TILE)); ty < room.h; ty++) if (isSolidT(tileAt(tx, ty)) || tileAt(tx, ty) === T_PLAT) return ty * TILE;
  return 19 * TILE;
}
const trnFoesAlive = () => enemies.filter(e => e.trn && e.alive !== false).length;
function trnSpawnEnemy(type, n = TRN.count) {
  if (TRN_ENEMY_NOTE[type]) { sfx.deny(); toast(TRN_ENEMY_NOTE[type], 3); return 0; }
  n = Math.min(n, TRN_FOE_CAP - trnFoesAlive());
  if (n <= 0) { sfx.deny(); toast(`The chamber holds ${TRN_FOE_CAP} foes at most. Clear some first.`, 2.6); return 0; }
  const fromPanel = state === 'menu';
  if (!(TRN.stay && fromPanel)) { menu = null; state = 'play'; } clearBuffer();
  let made = 0;
  for (let i = 0; i < n; i++) {
    // alternate sides, stepping outward; once a side is full, anywhere in the chamber that is not on top of you
    const side = (i % 2 ? -1 : 1) * P.face, step = Math.floor(i / 2);
    let x = P.x + side * (80 + step * 26);
    if (x < 3 * TILE || x > room.pw - 3 * TILE) x = P.x - side * (80 + step * 26);
    if (x < 3 * TILE || x > room.pw - 3 * TILE) { x = rand(3 * TILE, room.pw - 3 * TILE); if (Math.abs(x - P.x) < 56) x += (x < P.x ? -1 : 1) * 64; }
    x = clamp(x, 2 * TILE, room.pw - 2 * TILE);
    for (let k = 0; k < 8 && isSolidT(tileAt(Math.floor(x / TILE), Math.floor((P.y - 8) / TILE))); k++) x += (x < P.x ? 1 : -1) * TILE;
    const key = 'trn:' + (++TRN.id);
    const e = type === 'trn_dummy' ? new TrnDummy(x, trnFloorY(x), key) : makeEnemy(type, x, trnFloorY(x), key);
    e.trn = true; e.aggro = type !== 'trn_dummy'; enemies.push(e); made++;
    spawnFx(fxOr('parry_spark', 'hit'), e.x, e.y - 12, 1);
  }
  sfx.glint();
  if (fromPanel && TRN.stay) toast(`Summoned ×${made}  ·  ${trnFoesAlive()} foes in the chamber`, 1.8);
  return made;
}
function trnClearFoes() { enemies = enemies.filter(e => !e.trn || e.dummy); toast('Foes cleared', 1.4); }
function trnClear() {
  boss = null; hazards = []; projectiles = projectiles.filter(p => p.owner === 'player');
  enemies = enemies.filter(e => e.dummy && !e.trn); darkT = 0; victoryBanner = null; bossBanner = null;
  if (room && room.id === 'TR2' && room.def !== TRN.base.TR2) { const [sx, sy] = trnFlat() ? [P.x, P.y] : trnSpawnPt('TR2'); trnEnter('TR2', sx, sy); setP('idle', 'idle', true); }   // drop the borrowed biome / layout
  toast('Chamber cleared', 1.6);
}
function trnResetRoom() {
  const id = room && TRN.base[room.id] ? room.id : 'TR1', [sx, sy] = trnSpawnPt(id);
  boss = null; enemies = []; darkT = 0; victoryBanner = null; bossBanner = null;
  for (const t of TRN.timers) clearTimeout(t); TRN.timers.clear();
  newPlayer(sx, sy); trnEnter(id, sx, sy); setP('idle', 'idle', true);
}
function trnGoto(id) { const [sx, sy] = trnSpawnPt(id); boss = null; enemies = []; trnEnter(id, sx, sy); setP('idle', 'idle', true); }

// ---- builds
function trnLoadBuild() {
  let s = null; try { s = loadGame(); } catch (e) {}
  if (!s) { sfx.deny(); toast('No saved journey to copy', 2.5); return; }
  SAVE.stats = { ...s.stats }; SAVE.weapon = WEAPONS[s.weapon] ? s.weapon : 'longsword';
  for (const [id, lv] of Object.entries(s.weapons || {})) if (WEAPONS[id]) SAVE.weapons[id] = lv;
  SAVE.skills = (s.skills || []).filter(id => SKILL_BY[id]); SAVE.spellSlots = Math.max(1, s.spellSlots || 2); SAVE.charmSlots = Math.max(1, s.charmSlots || 1);
  SAVE.spellsEq = (s.spellsEq || []).filter(id => SPELLS[id]).slice(0, SAVE.spellSlots); SAVE.spell = SAVE.spellsEq.includes(s.spell) ? s.spell : SAVE.spellsEq[0] || null;
  SAVE.charmsEq = (s.charmsEq || []).filter(id => CHARMS[id]).slice(0, SAVE.charmSlots); SAVE.flaskBase = s.flaskBase || 4; SAVE.flaskBlue = s.flaskBlue || 1;
  trnApplyBuild(); toast('Your saved build (a copy: nothing flows back)', 3);
}
function trnApplyBuild(full = true) {
  if (typeof wbLockArt === 'function') wbLockArt();
  refreshDerived(false); if (full) { P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks(); }
  else { P.hp = Math.min(P.hp, D.maxHp); P.fp = Math.min(P.fp, D.maxFp); }
}

// ================================================================== the control panel (a `menu` screen: keyboard, pad, mouse)
const TRN_TABS = ['Player', 'Weapon', 'Magic', 'Skills', 'Spawn', 'World'];
function trnOpen(tab) {
  toasts = [];
  menu = { screen: 'trn', tab: tab ?? TRN.tab, sel: -1, off: 0 }; state = 'menu'; clearBuffer(); sfx.menu();
}
function trnClose() { menu = null; state = 'play'; clearBuffer(); sfx.menu(); }
const onOff = v => v ? 'On' : 'Off';
function trnToggleRow(label, get, set, desc) { return { label, val: () => onOff(get()), on: get, lr: () => set(!get()), conf: () => set(!get()), desc }; }
function trnRows(M) {
  const R = [];
  const head = (label, extra) => R.push({ head: true, label, extra });
  if (M.tab === 0) {
    head('Attributes', `Level ${levelOf(SAVE.stats)}  ·  step ×${TRN.step}`);
    for (const s of STATS) R.push({ label: s.name, stat: s.k, val: () => String(SAVE.stats[s.k]), lr: d => { SAVE.stats[s.k] = clamp(SAVE.stats[s.k] + d * TRN.step, 1, 99); trnApplyBuild(false); },
      conf: () => { TRN.step = TRN.step === 1 ? 10 : 1; }, desc: `${s.desc}. ◂ ▸ change by ${TRN.step}; Enter switches the step (1 / 10).`, big: true });
    head('Vitals');
    R.push({ label: 'Full heal', act: true, conf: () => { P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; P.rot = 0; P.rotT = 0; sfx.heal(); }, desc: 'Restore HP, FP and stamina and cure rot.' });
    R.push({ label: 'Refill flasks', act: true, conf: () => { refillFlasks(); sfx.heal(); }, desc: 'Crimson and azure flasks back to full.' });
    R.push({ label: 'Flask charges', val: () => String(SAVE.flaskBase), lr: d => { SAVE.flaskBase = clamp(SAVE.flaskBase + d, 1, 20); refillFlasks(); }, desc: 'How many flasks you carry (split at a shrine as usual).' });
    head('Cheats');
    R.push(trnToggleRow('God mode', () => !!SETTINGS.god, v => { SETTINGS.god = v ? 1 : 0; }, 'You take no damage and cannot die.'));
    R.push(trnToggleRow('Infinite FP', () => !!SETTINGS.inffp, v => { SETTINGS.inffp = v ? 1 : 0; }, 'FP never runs out.'));
    R.push(trnToggleRow('Infinite stamina', () => !!SETTINGS.infst, v => { SETTINGS.infst = v ? 1 : 0; }, 'Stamina never runs out.'));
    R.push(trnToggleRow('No cooldowns', () => !!SETTINGS.nocd, v => { SETTINGS.nocd = v ? 1 : 0; }, 'Spells and weapon arts are ready again at once.'));
    R.push(trnToggleRow('One-hit kills', () => TRN.ohk, v => { TRN.ohk = v; }, 'Every blow and spell of yours deals at least 99999.'));
    head('Build');
    R.push({ label: 'Copy my saved build', act: true, conf: trnLoadBuild, desc: 'Stats, weapons, skills, spells and charms from your saved journey. It is a copy: nothing done here flows back.' });
    R.push({ label: 'Reset to the training build', act: true, conf: () => { const k = SAVE.flags; SAVE = trnNewSave(); SAVE.flags = k; trnApplyBuild(); toast('Training build restored', 2); }, desc: 'Every weapon, spell and charm; level 87; no skills.' });
  } else if (M.tab === 1) {
    const cur = SAVE.weapon;
    head('In hand', WEAPONS[cur].name);
    R.push({ label: 'Upgrade level', val: () => '+' + (SAVE.weapons[SAVE.weapon] || 0), lr: d => { SAVE.weapons[SAVE.weapon] = clamp((SAVE.weapons[SAVE.weapon] || 0) + d, 0, 5); trnApplyBuild(false); }, conf: () => { SAVE.weapons[SAVE.weapon] = ((SAVE.weapons[SAVE.weapon] || 0) + 1) % 6; trnApplyBuild(false); }, wpn: cur, desc: 'Tempering, +0 to +5 (◂ ▸).' });
    head('Arsenal', `${Object.keys(WEAPONS).length} weapons`);
    const cls = id => { const c = WEAPON_CLASS[id] || '', l = typeof wbClassLabel === 'function' ? wbClassLabel(c) : c; return l.replace(/\b\w/g, m => m.toUpperCase()); };
    for (const id of Object.keys(WEAPONS)) R.push({ label: WEAPONS[id].name, wpn: id, val: () => (SAVE.weapon === id ? '● ' : '') + cls(id), eq: () => SAVE.weapon === id,
      conf: () => { SAVE.weapon = id; if (typeof wbOnEquip === 'function') wbOnEquip(id); trnApplyBuild(false); sfx.menu(); }, desc: WEAPONS[id].desc || '' });
  } else if (M.tab === 2) {
    head('Spells', `${SAVE.spellsEq.length} / ${SAVE.spellSlots} slots`);
    R.push({ label: 'Spell slots', val: () => String(SAVE.spellSlots), lr: d => { SAVE.spellSlots = clamp(SAVE.spellSlots + d, 1, 8); SAVE.spellsEq = SAVE.spellsEq.slice(0, SAVE.spellSlots); if (!SAVE.spellsEq.includes(SAVE.spell)) SAVE.spell = SAVE.spellsEq[0] || null; }, desc: 'How many spells you can attune.' });
    for (let i = 0; i < SAVE.spellSlots; i++) { const r = { k: 'spell', i }; R.push({ label: `Spell ${i + 1}`, gear: () => SAVE.spellsEq[i] && ['spell', SAVE.spellsEq[i]], val: () => SAVE.spellsEq[i] ? SPELLS[SAVE.spellsEq[i]].name : '—', lr: d => changeEquip(r, d), conf: () => changeEquip(r, 1), desc: '◂ ▸ cycle through every spell.' }); }
    head('Charms', `${SAVE.charmsEq.length} / ${SAVE.charmSlots} slots`);
    R.push({ label: 'Charm slots', val: () => String(SAVE.charmSlots), lr: d => { SAVE.charmSlots = clamp(SAVE.charmSlots + d, 1, 8); SAVE.charmsEq = SAVE.charmsEq.slice(0, SAVE.charmSlots); refreshDerived(); }, desc: 'How many charms you can wear.' });
    for (let i = 0; i < SAVE.charmSlots; i++) { const r = { k: 'charm', i }; R.push({ label: `Charm ${i + 1}`, gear: () => SAVE.charmsEq[i] && ['charm', SAVE.charmsEq[i]], val: () => SAVE.charmsEq[i] ? CHARMS[SAVE.charmsEq[i]].name : '—', lr: d => changeEquip(r, d), conf: () => changeEquip(r, 1), desc: '◂ ▸ cycle through every charm.' }); }
    R.push({ label: 'Remove all charms', act: true, conf: () => { SAVE.charmsEq = []; trnApplyBuild(false); }, desc: 'Take every charm off.' });
    R.push({ label: 'Open the equipment screen', act: true, conf: () => { menu = { screen: 'pause', tab: 0, sel: 0, trnRet: 2 }; sfx.menu(); }, desc: 'The full picker grid with icons and descriptions. Closing it brings you back here.' });
  } else if (M.tab === 3) {
    head('Skill tree', `${SAVE.skills.length} / ${SKILLS.length} learned`);
    R.push({ label: 'Open the skill tree', act: true, conf: () => { SAVE.shards = 999; const back = menu; menu = { screen: 'tree', br: 0, t: 0, prev: back }; if (typeof stOpen === 'function') stOpen(menu); sfx.menu(); }, desc: 'The real tree, with points to spare. Esc brings you back to this panel.' });
    R.push({ label: 'Learn everything', act: true, conf: trnLearnAll, desc: 'Learn every skill whose requirements are met, repeatedly. At each fork, the first branch is taken.' });
    R.push({ label: 'Unlearn everything', act: true, conf: trnUnlearnAll, desc: 'Forget every skill.' });
    head('Learned');
    for (const id of SAVE.skills) { const s = SKILL_BY[id]; if (s) R.push({ label: s.name, info: true, val: () => s.cost + ' pt', desc: s.desc || '' }); }
  } else if (M.tab === 4) {
    head('Summon');
    const cyc = d => { const o = TRN_COUNTS, i = Math.max(0, o.indexOf(TRN.count)); TRN.count = o[(i + d + o.length) % o.length]; };
    R.push({ label: 'Count', val: () => '×' + TRN.count, lr: d => cyc(d > 0 ? 1 : -1), conf: () => cyc(1), desc: `How many foes each summon brings: ×1 up to ×20 (at most ${TRN_FOE_CAP} alive at once). Bosses always come alone.` });
    R.push(trnToggleRow('Keep panel open', () => TRN.stay, v => { TRN.stay = v; }, 'On: summoning a foe keeps this panel open, so you can call in several kinds in a row. Close the panel to fight. Bosses always close it.'));
    R.push({ label: 'Foes in the chamber', info: true, val: () => String(trnFoesAlive()), desc: 'Summon a boss first, then call foes in beside it: summoning a boss re-builds the arena and sends the foes away.' });
    R.push({ label: 'Boss arena', val: () => TRN.arena === 'home' ? 'Home layout' : 'Flat chamber', lr: () => { TRN.arena = TRN.arena === 'home' ? 'flat' : 'home'; }, conf: () => { TRN.arena = TRN.arena === 'home' ? 'flat' : 'home'; },
      desc: 'Home layout: the boss\'s own arena shape, walls and floors (as the white chamber). Flat chamber: the wide open arena; a few bosses built around their arena always use their layout.' });
    R.push(trnToggleRow('Freeze AI', () => TRN.freeze, v => { TRN.freeze = v; }, 'Foes and bosses stand still: study hitboxes, test combos, measure damage.'));
    R.push({ label: 'Clear foes', act: true, conf: trnClearFoes, desc: 'Remove every summoned foe; a boss stays.' });
    R.push({ label: 'Clear all', act: true, conf: () => { trnClear(); trnClose(); }, desc: 'Remove every summoned foe and boss.' });
    if (TRN.last) R.push({ label: `Summon again: ${BOSS_INFO[TRN.last] ? BOSS_INFO[TRN.last].name : TRN.last}`, act: true, conf: () => trnSummonBoss(TRN.last), desc: 'The last boss, fresh.' });
    R.push({ label: 'Training dummy', enemy: 'trn_dummy', val: () => 'dummy', conf: () => trnSpawnEnemy('trn_dummy'), desc: 'Another dummy beside you: damage numbers and DPS, never dies.' });
    let reg = null;
    for (const B of trnBosses()) {
      if (B.region !== reg) { reg = B.region; head('Bosses · ' + reg); }
      R.push({ label: B.name.replace(/,.*$/, ''), boss: B, dis: !!TRN_BOSS_NOTE[B.kind], val: () => TRN_BOSS_NOTE[B.kind] ? 'n/a' : 'boss', conf: () => trnSummonBoss(B.kind),
        desc: TRN_BOSS_NOTE[B.kind] || `${B.name}. ${BOSS_INFO[B.kind].quote || ''}` });
    }
    reg = null;
    for (const E of trnEnemies()) {
      if (E.region !== reg) { reg = E.region; head('Foes · ' + reg); }
      R.push({ label: E.name, enemy: E.type, dis: !!TRN_ENEMY_NOTE[E.type], val: () => TRN_ENEMY_NOTE[E.type] ? 'n/a' : E.elite ? '★ elite' : E.fly ? 'flying' : '', conf: () => trnSpawnEnemy(E.type),
        desc: TRN_ENEMY_NOTE[E.type] || `HP ${ENEMY[E.type].hp}${E.elite ? '  ·  elite' : ''}${E.fly ? '  ·  flying' : ''}. Summons ×${TRN.count} around you.` });
    }
  } else {
    head('Rules');
    R.push({ label: 'Difficulty', val: () => DIFFS[diffIdx()].name, lr: d => setDiff((diffIdx() + (d > 0 ? 1 : 2)) % 3), conf: () => setDiff((diffIdx() + 1) % 3), desc: () => DIFFS[diffIdx()].desc });
    R.push({ label: 'Time scale', val: () => '×' + TRN.ts, lr: d => { const o = [0.25, 0.5, 1]; TRN.ts = o[clamp(o.indexOf(TRN.ts) + d, 0, 2)]; }, conf: () => { const o = [0.25, 0.5, 1]; TRN.ts = o[(o.indexOf(TRN.ts) + 1) % 3]; }, desc: 'Slow the whole world down to study an attack.' });
    R.push(trnToggleRow('Hitbox overlay', () => TRN.hitbox, v => { TRN.hitbox = v; }, 'Green: you. Yellow: your swing. Blue: what can be hit. Red: what hurts.'));
    head('Chamber');
    R.push({ label: 'Reset this room', act: true, conf: () => { trnResetRoom(); trnClose(); }, desc: 'Clear everything and start the room over.' });
    R.push({ label: 'Go to Chamber 01 (lab)', act: true, conf: () => { trnGoto('TR1'); trnClose(); }, desc: 'Wall-jump chimney, platforms, spikes, hook ring, brambles and the dummy.' });
    R.push({ label: 'Go to Chamber 02 (arena)', act: true, conf: () => { trnGoto('TR2'); trnClose(); }, desc: 'The open arena bosses are summoned into.' });
    head('Leave');
    R.push({ label: 'Exit to title', act: true, conf: () => trainingExit(), desc: 'Back to the title screen. Your saved journey was never touched.' });
  }
  return R;
}
function trnLearnAll() {
  SAVE.shards = 999;
  for (let changed = true, n = 0; changed && n < 50; n++) { changed = false; for (const s of SKILLS) if (skillLearnable(s.id).ok) { SAVE.skills.push(s.id); skOnLearn(s.id, true); changed = true; } }
  trnApplyBuild(false); sfx.levelup(); toast(`${SAVE.skills.length} skills learned`, 2);
}
function trnUnlearnAll() {
  const had = [...SAVE.skills]; SAVE.skills = []; for (const id of had) skOnLearn(id, false);
  SAVE.spellsEq = SAVE.spellsEq.filter(s => spellKnown(s)); if (!SAVE.spellsEq.includes(SAVE.spell)) SAVE.spell = SAVE.spellsEq[0] || null;
  trnApplyBuild(false); refillFlasks(); sfx.menu(); toast('Every skill forgotten', 2);
}
const trnSelectable = r => r && !r.head;
function trnInput(M, a) {
  const R = trnRows(M), conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (M.sel < 0 || !trnSelectable(R[M.sel])) M.sel = R.findIndex(trnSelectable);
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) return trnClose();
  if (a === 'spell' || a === 'map') { M.tab = TRN.tab = (M.tab + (a === 'spell' ? TRN_TABS.length - 1 : 1)) % TRN_TABS.length; M.sel = -1; M.off = 0; sfx.menu(); return; }
  if (a === 'up' || a === 'down') {
    const d = a === 'up' ? -1 : 1; let i = M.sel;
    for (let k = 0; k < R.length; k++) { i = (i + d + R.length) % R.length; if (trnSelectable(R[i])) break; }
    M.sel = i; sfx.menu(); return;
  }
  const r = R[M.sel]; if (!r || r.info) return;
  if (r.dis && (conf || a === 'right')) { sfx.deny(); toast(typeof r.desc === 'function' ? r.desc() : r.desc, 3); return; }
  if ((a === 'left' || a === 'right') && r.lr) { r.lr(a === 'left' ? -1 : 1); sfx.menu(); return; }
  if (conf && (r.conf || r.lr)) { (r.conf || (() => r.lr(1)))(); if (state === 'menu' && menu === M) sfx.menu(); }
}
// the panel's rows sit on the left; details (and the weapon in hand) on the right
const TRN_VIS = 12, TRN_RH = 12.2;
function trnRender(M) {
  const R = trnRows(M);
  if (M.sel < 0 || !trnSelectable(R[M.sel])) M.sel = R.findIndex(trnSelectable);
  uiBackdrop(0.72); uiStrips();
  // tabs
  const n = TRN_TABS.length, pitch = 56, x0 = W / 2 - pitch * (n - 1) / 2;
  TRN_TABS.forEach((t, i) => {
    const x = x0 + i * pitch, sel = i === M.tab;
    uiHit(x - 26, 9, 52, 16, null, () => { if (M.tab !== i) { M.tab = TRN.tab = i; M.sel = -1; M.off = 0; sfx.menu(); } });
    text(t.toUpperCase(), x, 18, 6.2, sel ? UIC.hi : UIC.faint, 'center', { spacing: 1.4, weight: sel ? 600 : 500 });
    if (sel) { uiDiamond(x, 22.5, 1.3, UIC.gold); uiFade(x - 3, x - 26, 22.2, UI_RGB.gold, 0.9); uiFade(x + 3, x + 26, 22.2, UI_RGB.gold, 0.9); }
    if (i < n - 1) uiDiamond(x + pitch / 2, 16, 0.9, '#5a4a30');
  });
  if (kl('Q')) { uiKey(kl('Q'), x0 - 36, 18.5, { size: 4.8, align: 'center' }); uiHit(x0 - 46, 10, 20, 12, null, () => uiAct('spell')); }
  { const xr = x0 + (n - 1) * pitch + 36; uiKey(kl('Tab'), xr, 18.5, { size: 4.8, align: 'center' }); uiHit(xr - 12, 10, 24, 12, null, () => uiAct('map')); }
  text('TRAINING GROUNDS', 12, 36, 4.6, UIC.faint, 'left', { spacing: 1.2 });
  // rows
  const px = 10, pw = 226, top = 40;
  panel(px, top, pw, 14 + TRN_VIS * TRN_RH);
  M.off = clamp(M.off, Math.max(0, M.sel - TRN_VIS + 1), Math.max(0, Math.min(M.sel, R.length - TRN_VIS)));
  if (M.sel >= 0 && M.sel - 1 >= 0 && R[M.sel - 1].head && M.sel - 1 < M.off) M.off = M.sel - 1;   // keep a row's heading in view
  for (let k = 0; k < TRN_VIS && M.off + k < R.length; k++) {
    const i = M.off + k, r = R[i], y = top + 12 + k * TRN_RH;
    if (r.head) {
      text(r.label.toUpperCase(), px + 8, y + 1, 4.6, UIC.dim, 'left', { spacing: 1.1, weight: 600 });
      if (r.extra) text(r.extra, px + pw - 8, y + 1, 4.6, UIC.faint, 'right', { weight: 500 });
      uiFade(px + 10 + textW(r.label.toUpperCase(), 4.6) + r.label.length * 1.1, px + pw - 10 - (r.extra ? textW(r.extra, 4.6, 500) + 4 : 0), y - 0.8, UI_RGB.accent, 0.45);
      continue;
    }
    const sel = i === M.sel, lr = !!r.lr;
    uiHit(px + 4, y - 8.5, pw - 8, TRN_RH - 1, () => { M.sel = i; }, () => { M.sel = i; if (r.info || r.stat) return; if (r.dis) { uiAct('confirm'); return; } if (r.conf) uiAct('confirm'); else if (lr) uiAct('right'); });
    if (sel) uiSel(px + 4, y - 8.5, pw - 8, TRN_RH - 1);
    const dim = r.dis || r.info;
    if (r.wpn && r.eq) icon('w_' + r.wpn, px + 8, y - 7.5, 9, r.eq() || sel ? 1 : 0.7);
    else if (r.gear && r.gear()) { const [k2, id] = r.gear(); const e = gearEntry(k2, id); if (e) icon(e.icon, px + 8, y - 7.5, 9); }
    const lx = px + (r.wpn && r.eq || r.gear ? 20 : 10);
    text(r.label, lx, y, 5.8, dim ? UIC.faint : sel ? UIC.hi : r.act ? UIC.gold : UIC.body, 'left', { weight: sel ? 600 : 500 });
    const v = r.val ? r.val() : r.act ? '▸' : '';
    const col = r.on ? (r.on() ? '#ffd070' : UIC.faint) : r.eq && r.eq() ? UIC.gold : dim ? UIC.faint : UIC.text;
    if (lr) {
      const vx = px + pw - 22;
      text(v, vx, y, 5.8, col, 'right', { weight: 600 });
      text('◂', vx - textW(v, 5.8) - 6, y, 5.8, sel ? UIC.gold : '#6a5a3e', 'center');
      text('▸', px + pw - 12, y, 5.8, sel ? UIC.gold : '#6a5a3e', 'center');
      uiHit(vx - textW(v, 5.8) - 11, y - 8.5, 10, TRN_RH - 1, () => { M.sel = i; }, () => { M.sel = i; uiAct('left'); });
      uiHit(px + pw - 17, y - 8.5, 11, TRN_RH - 1, () => { M.sel = i; }, () => { M.sel = i; uiAct('right'); });
      if (r.stat) {   // mouse shortcuts for the big steps
        for (const [dx, d, s] of [[-58, -10, '−10'], [-44, 10, '+10']]) {
          const bx = vx + dx; text(s, bx, y, 4.4, sel ? UIC.muted : '#5d5140', 'center', { weight: 500 });
          uiHit(bx - 6, y - 8, 12, TRN_RH - 2, () => { M.sel = i; }, () => { M.sel = i; SAVE.stats[r.stat] = clamp(SAVE.stats[r.stat] + d, 1, 99); trnApplyBuild(false); sfx.menu(); });
        }
      }
    } else if (v) text(v, px + pw - 10, y, r.act ? 5.8 : 5, col, 'right', { weight: r.act ? 600 : 500 });
  }
  uiScroll(px + pw - 3, top + 4, TRN_VIS * TRN_RH, M.off, TRN_VIS, R.length);
  trnRenderDetail(M, R[M.sel]);
  const r = R[M.sel];
  uiFooter([['↑↓', 'select'], ...(r && r.lr ? [['←→', 'change']] : []), ['Enter', r && r.stat ? 'step ×1/×10' : r && r.lr && !r.act ? 'next' : 'use'], ['Tab', 'tabs'], ['Esc', 'close']]);
}
function trnRenderDetail(M, r) {
  const px = 242, pw = 132, top = 40, ph = 14 + TRN_VIS * TRN_RH;
  panel(px, top, pw, ph, 0.85);
  let y = top + 12;
  const para = (s, c = UIC.body, sz = 5.2) => { for (const l of wrap(s, pw - 16, sz)) { if (y > top + ph - 6) break; text(l, px + 8, y, sz, c, 'left', { weight: 400 }); y += sz * 1.45; } };
  if (M.tab === 1 || (r && r.wpn)) {   // the weapon in hand (or under the cursor): icon, numbers, and its locked art
    const id = r && r.wpn || SAVE.weapon, w = WEAPONS[id], lv = SAVE.weapons[id] || 0;
    icon('w_' + id, px + 8, y - 6, 20);
    text(w.name, px + 32, y + 1, uiFit(w.name, pw - 40, 6.4, 4.4), UIC.gold, 'left');
    text(`${(typeof wbClassLabel === 'function' ? wbClassLabel(WEAPON_CLASS[id]) : '').replace(/\b\w/g, m => m.toUpperCase())}  ·  +${lv}`, px + 32, y + 8, 4.8, UIC.muted, 'left', { weight: 400 });
    y += 22;
    text(`Attack ${Math.round(weaponAR(SAVE.stats, id, lv))}`, px + 8, y, 5.4, UIC.text, 'left'); y += 8;
    const sc = w.sc || {}; text(`Scaling  Str ${sc.str ?? '-'}  Dex ${sc.dex ?? '-'}  Fth ${sc.fth ?? '-'}`, px + 8, y, 4.6, UIC.muted, 'left', { weight: 400 }); y += 9;
    const art = typeof wbArtOf === 'function' ? wbArtOf(id) : w.art, A = ARTS[art];
    if (A) {
      uiHead('Weapon art (bound)', px + 8, y, pw - 16); y += 8;
      icon('a_' + art, px + 8, y - 6, 10); text(A.name, px + 21, y + 1, 5.6, UIC.hi, 'left'); text(`${A.fp} FP`, px + pw - 8, y + 1, 4.8, UIC.fp, 'right'); y += 10;
      para(A.desc || '', UIC.body, 4.8);
    }
    y += 2; if (w.desc) para(w.desc, UIC.dim, 4.6);
    return;
  }
  if (r && r.gear && r.gear()) {
    const [k, id] = r.gear(), e = gearEntry(k, id);
    if (e) { icon(e.icon, px + 8, y - 6, 18); text(e.name, px + 30, y + 3, uiFit(e.name, pw - 38, 6.2, 4.4), UIC.gold, 'left'); y += 20; para(e.desc || ''); return; }
  }
  if (r && r.boss) {
    const B = r.boss, I = BOSS_INFO[B.kind];
    text(I.name, px + 8, y + 1, uiFit(I.name, pw - 16, 6.2, 4.2), UIC.gold, 'left'); y += 10;
    text(`HP ${I.hp}  ·  ${B.region}`, px + 8, y, 4.8, UIC.muted, 'left', { weight: 400 }); y += 8;
    text(`Home arena: ${ROOM_BY[B.room] ? ROOM_BY[B.room].name : B.room}`, px + 8, y, 4.6, UIC.faint, 'left', { weight: 400 }); y += 10;
    para(TRN_BOSS_NOTE[B.kind] ? TRN_BOSS_NOTE[B.kind] : I.quote || '', TRN_BOSS_NOTE[B.kind] ? UIC.down : UIC.body);
    y += 3; para(`Summoned into Chamber 02 (${trnUseHome(B.kind) ? 'its home layout' : 'the flat arena'}${TRN_NEEDS_HOME.has(B.kind) ? ', which its fight is built around' : ''}). Cutscenes are skipped; killing it grants nothing.`, UIC.dim, 4.6);
    return;
  }
  if (r && r.enemy && r.enemy !== 'trn_dummy') {
    const sh = sheet(r.enemy);
    if (sh.ok) {   // a still of the foe
      const f = sh.frames[sh.first(sh.has('idle') ? 'idle' : sh.has('fly') ? 'fly' : Object.keys(sh.tags)[0])], k = Math.min(1, 60 / Math.max(f.w, f.h)) * 1.4;
      vctx.imageSmoothingEnabled = false; vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, ox + (px + pw / 2 - f.w * k / 2) * scale, oy + (y - 4) * scale, f.w * k * scale, f.h * k * scale);
      y += f.h * k + 4;
    }
  }
  if (r && M.tab === 0 && r.stat) {
    text(`Level ${levelOf(SAVE.stats)}`, px + 8, y + 1, 7, UIC.gold, 'left'); y += 12;
    for (const [k, v] of [['HP', D.maxHp], ['FP', D.maxFp], ['Stamina', D.maxSt], ['Attack', Math.round(D.light)], ['Heavy', Math.round(D.heavy * 2)], ['Spell power', Math.round(D.spell * 100)]]) {
      text(k, px + 8, y, 5, UIC.dim, 'left', { weight: 500 }); text(String(v), px + pw - 8, y, 5.4, UIC.text, 'right'); y += 8;
    }
    y += 4;
  }
  if (r) { if (!r.boss && !r.enemy) text(r.label, px + 8, y + 1, uiFit(r.label, pw - 16, 6.2, 4.2), UIC.gold, 'left'), y += 10; para(typeof r.desc === 'function' ? r.desc() : r.desc || ''); }
}
{ const _mi = menuInput, _rm = renderMenu;
  menuInput = function (a) {
    if (menu && menu.screen === 'trn') return trnInput(menu, a);
    const ret = menu && menu.trnRet !== undefined ? menu.trnRet : null;
    const r = _mi(a);
    if (ret !== null && TRAINING.on && !menu && state === 'play') trnOpen(ret);   // the equipment screen hands back to the panel
    return r;
  };
  renderMenu = function () {
    if (menu && menu.screen === 'trn') { UIM.hits = []; trnRender(menu); uiAfterRender(); return; }
    return _rm();
  };
}

// ---- debug handles (tools/shots/tr/)
if (typeof window !== 'undefined' && window.__game) window.__game.trn = {
  TRAINING, TRN, start: trainingStart, exit: trainingExit, summon: trnSummonBoss, spawn: trnSpawnEnemy, clear: trnClear, reset: trnResetRoom, goto: trnGoto,
  bosses: () => trnBosses(), enemies: () => trnEnemies(), rows: t => trnRows({ tab: t }), open: trnOpen, notes: { boss: TRN_BOSS_NOTE, enemy: TRN_ENEMY_NOTE },
  learnAll: trnLearnAll, unlearnAll: trnUnlearnAll, get targets() { return targets(); }, get hazards() { return hazards; },
};
