// ------------------------------------------------------------------ v17 THE COLD FORGE: foes (agent FOES, docs/v17/forge_foes.md)
// Hollow Smith `cf_smith` (hammer; the tongs grab and hold you over their heat), Quench Wraith `cf_wraith` (lies still as
// a ring of steam until you come near, hisses, lunges), Bellows Hulk `cf_hulk` (never flinches, built to be staggered: its
// core flares as its stance gives; after a bellows blast it vents and takes stance damage x1.8), Cinder Mite `cf_mite`
// (swarms, leaps, clings and burns; a roll shakes it off) and the elite the Unforged `cf_unforged`, a knight bound from
// failed blades that takes up one of the 14 weapon types per encounter (spawn spec `w` fixes it) and fights with that
// type's signature moves. Art: art/gen_forge_foes.py (sheets cf_*, one cf_unforged_<type> per type).
// Everything here is added from this file (ENEMY / ATTACK_TAGS / ENEMY_CLASSES / BIOME_TIER / SPAWNS / HOOKS).

const CFF = { fx: [], coals: [], rings: [], force: null, log: [], mites: [] };
if (!BIOME_TIER.forge) BIOME_TIER.forge = { hp: 1.9, dmg: 1.55, cin: 1.7 };
const CFF_TYPES = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip', 'saxe', 'bow', 'fist', 'scythe', 'bell'];

Object.assign(ENEMY, {
  cf_smith: { name: 'Hollow Smith', hp: 230, cinders: 260, speed: 30, aggro: 170, range: 52, poise: 30, stance: 100, dmg: { hammer: 40, grab: 12, toss: 24 }, cool: [0.8, 1.5] },
  cf_wraith: { name: 'Quench Wraith', hp: 130, cinders: 220, speed: 44, aggro: 150, range: 120, poise: 14, stance: 55, dmg: { lunge: 36, claw: 26 }, cool: [1.0, 1.8] },
  cf_hulk: { name: 'Bellows Hulk', hp: 640, cinders: 680, speed: 22, aggro: 170, range: 72, poise: 999, stance: 175, dmg: { slam: 60, sweep: 46, blast: 12 }, cool: [1.2, 2.0] },
  cf_mite: { name: 'Cinder Mite', hp: 22, cinders: 30, speed: 70, aggro: 150, range: 72, poise: 1, stance: 8, dmg: { leap: 10 }, cool: [0.9, 1.7], burn: 4 },
  cf_unforged: { name: 'The Unforged', hp: 1000, cinders: 1300, speed: 50, aggro: 210, range: 90, poise: 999, stance: 330, dmg: { atk: 42 }, cool: [0.55, 1.1], elite: true },
});
Object.assign(ATTACK_TAGS, { cf_smith: ['hammer', 'grab', 'toss'], cf_wraith: ['lunge', 'claw'], cf_hulk: ['slam', 'sweep', 'blast'], cf_mite: ['leap'], cf_unforged: ['atk1', 'atk2', 'atk3'] });

const cffSfx = {
  hiss: (v = 1) => { noise(0.7 * v, 5200, 0.6, 0.16, 'highpass', 0.6); noise(0.4 * v, 2400, 1, 0.08, 'bandpass', 1.4); },
  clang: () => { tone(620, 0.35, 0.07, 'triangle', 0.97); tone(1240, 0.25, 0.04, 'sine'); noise(0.1, 3200, 2, 0.15, 'highpass'); },
  clack: () => { tone(900, 0.06, 0.06, 'square', 0.7); tone(700, 0.06, 0.05, 'square', 0.7, 0.07); },
  bellows: () => { noise(0.9, 260, 0.6, 0.45, 'lowpass', 2.2); tone(70, 0.8, 0.1, 'sawtooth', 1.4); },
  flare: () => { tone(180, 0.5, 0.08, 'sawtooth', 2.4); noise(0.3, 1400, 1, 0.1, 'bandpass', 1.6); },
  sizzle: () => noise(0.25, 3800, 1, 0.08, 'highpass', 0.8),
  toll: (f = 196) => { tone(f, 1.6, 0.14, 'triangle', 1); tone(f * 2.01, 1.2, 0.06, 'sine'); tone(f * 2.76, 0.8, 0.03, 'sine'); },
  shatter: () => { noise(0.6, 2600, 0.7, 0.35, 'bandpass', 0.4); [880, 1170, 1480, 990].forEach((f, i) => tone(f, 0.3, 0.04, 'triangle', 0.8, i * 0.05)); },
};

// Enemy.update's bookkeeping for the brains that run their own switch (as 32_crimson's cmPre)
function cffPre(e, dt) {
  e.flash = Math.max(0, e.flash - dt * 5); e.poise = Math.max(0, e.poise - dt * 12); e.stance = Math.max(0, e.stance - dt * 6);
  e.bleed = Math.max(0, e.bleed - dt * 6); e.dmgT -= dt; e.t += dt;
  if (e.rotT > 0) { e.rotT -= dt; e.hp -= e.maxHp * 0.025 * dt; if (e.hp <= 0) { e.die({ dir: 0 }); return false; } }
  e.anim.update(dt);
  if (!e.aggro && e.canSee()) { e.aggro = true; e.cool = Math.max(e.cool, 0.4); if (e.onAggro) e.onAggro(); }
  if (e.aggro && (Math.abs(e.dist()) > e.cfg.aggro * 1.9 || Math.abs(P.y - e.y) > 170 || P.state === 'dead')) { e.lostT += dt; if (e.lostT > 2.5) { e.aggro = false; e.lostT = 0; } } else e.lostT = 0;
  e.cool -= dt;
  e.spikeCd = (e.spikeCd || 0) - dt;
  if (e.spikeCd <= 0 && spikeHit(e)) { e.spikeCd = 0.6; e.hit({ dmg: e.maxHp * 0.34 + 10, poise: 0, dir: -e.face, kind: 'env', x: e.x, y: e.y - 6 }); if (!e.alive) return false; }
  return true;
}
const CFF_LIVE = ['hurt', 'stagger', 'parried', 'dead'];
const cffPt = (e, name, i = e.anim.frame) => { const m = e.sh.meta, q = m && m.pts && m.pts[name] && m.pts[name][i]; return q ? metaPoint(e.sh, e, q) : { x: e.x + e.face * 10, y: e.y - e.h * 0.6 }; };
function cffHitWindows(e, dmgOf, opt = {}) {   // the art's hit windows, once each per attack
  const an = e.anim, wins = metaWindows(e.sh, e.atk);
  let on = false;
  wins.forEach((w, wi) => {
    if (an.i < w.active[0] || an.i > w.active[1]) return;
    on = true;
    if (an.changed && an.i === w.active[0]) { (opt.heavy ? sfx.heavySwing : sfx.swing)(); if (opt.onStart) opt.onStart(w, wi); }
    if (e.hitIds.has(wi) || !w.hit) return;
    const r = metaRect(e.sh, e, w.hit);
    if (!overlap(r, playerHurtbox())) return;
    const d = dmgOf(wi, w, r);
    if (d <= 0) return;
    const parry = opt.parryable === undefined ? true : (typeof opt.parryable === 'function' ? opt.parryable(wi) : opt.parryable);
    const dir = w.both ? sign(P.x - e.x) || e.face : e.face;
    if (hurtPlayer(d, dir, e.atkId * 10 + wi, { parryable: parry, src: e })) { e.hitIds.add(wi); if (opt.onHit) opt.onHit(wi, w); }
    else if (e.state === 'parried') return;
    else if (P.lastHit === e.atkId * 10 + wi) e.hitIds.add(wi);
  });
  return on;
}
// small effects drawn by this file: shock waves (travelling), rings (expanding), embers, coals (lobbed)
function cffShock(x, y, dir, opt = {}) {
  const h = { x, y, vx: dir * (opt.v || 150), w: 12, h: opt.h || 12, dmg: opt.dmg || 30, id: ++hazardId, life: opt.life || 0.9, wave: true, dir, color: 'fire' };
  hazards.push(h); CFF.fx.push({ k: 'shock', h, t: 0 }); return h;
}
function cffRing(x, y, opt = {}) {   // a ring of sound / heat expanding along the floor both ways out to r
  CFF.rings.push({ x, y, r: 0, R: opt.R || 72, v: opt.v || 220, dmg: opt.dmg || 24, id: ++hazardId, t: 0, col: opt.col || '240,212,150', h: opt.h || 16, src: opt.src || null });
}
function cffUpdateFx(dt) {
  for (const f of CFF.fx) { f.t += dt; if (f.k === 'shock' && f.h.life > 0) addLight(f.h.x, f.h.y - 6, 26, '255,140,60', 0.5); }
  CFF.fx = CFF.fx.filter(f => f.k === 'shock' ? f.h.life > 0 : f.t < (f.life || 0.5));
  for (const r of CFF.rings) {
    r.t += dt; r.r = Math.min(r.R, r.r + r.v * dt);
    const dx = Math.abs(P.x - r.x);
    if (r.r < r.R && Math.abs(dx - r.r) < 9 && P.y > r.y - r.h - 20 && P.y <= r.y + 2 && P.ground) hurtPlayer(r.dmg, sign(P.x - r.x) || 1, r.id, { src: r.src });
    addLight(r.x - r.r, r.y - 6, 22, r.col, 0.35); addLight(r.x + r.r, r.y - 6, 22, r.col, 0.35);
  }
  CFF.rings = CFF.rings.filter(r => r.r < r.R || r.t < 0.5 + r.R / r.v);
  for (const c of CFF.coals) {
    c.t += dt;
    if (c.landed) { c.life -= dt; if (overlap(rect(c.x - 9, c.y - 6, c.x + 9, c.y), playerHurtbox())) hurtPlayer(c.dmg * 0.5, sign(P.x - c.x) || 1, c.id + '_' + Math.floor(c.t / 0.5)); addLight(c.x, c.y - 3, 18, '255,120,50', 0.6 * Math.min(1, c.life)); if (Math.random() < dt * 8) particles.push({ x: c.x + rand(-6, 6), y: c.y - 1, vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'fire' }); continue; }
    c.vy += 420 * dt; c.x += c.vx * dt; c.y += c.vy * dt;
    addLight(c.x, c.y, 16, '255,140,60', 0.6);
    if (overlap(rect(c.x - 3, c.y - 3, c.x + 3, c.y + 3), playerHurtbox()) && hurtPlayer(c.dmg, sign(c.vx) || 1, c.id, { src: c.src })) { c.life = 0; c.landed = true; continue; }
    if (solidAtPx(c.x, c.y)) { c.landed = true; c.y = Math.floor(c.y / TILE) * TILE; c.life = 1.2; cffSfx.sizzle(); for (let i = 0; i < 6; i++) particles.push({ x: c.x, y: c.y - 2, vx: rand(-40, 40), vy: -rand(20, 70), g: 300, life: 0.4, kind: 'fire' }); }
    if (c.t > 4) c.life = 0;
  }
  CFF.coals = CFF.coals.filter(c => !c.landed || c.life > 0);
}
function cffDrawFx() {
  for (const f of CFF.fx) if (f.k === 'shock' && f.h.life > 0) {   // a low tongue of heat running along the floor
    const x = Math.round(f.h.x), y = Math.round(f.h.y);
    for (let i = -6; i <= 6; i++) { const hh = Math.round((1 - Math.abs(i) / 7) * (6 + 3 * Math.sin(time * 30 + i))); if (hh <= 0) continue; g.fillStyle = 'rgba(150,40,12,0.85)'; g.fillRect(x + i, y - hh, 1, hh); g.fillStyle = 'rgba(255,170,80,0.9)'; g.fillRect(x + i, y - hh, 1, 1); }
  }
  for (const r of CFF.rings) {
    const a = r.r < r.R ? 0.9 : Math.max(0, 0.9 - (r.t - r.R / r.v) * 2);
    for (const s of [-1, 1]) {
      const x = Math.round(r.x + s * r.r), y = Math.round(r.y);
      g.fillStyle = `rgba(${r.col},${a})`; g.fillRect(x - 1, y - r.h, 2, r.h);
      g.fillStyle = `rgba(${r.col},${a * 0.45})`; g.fillRect(x - s * 3, y - r.h + 3, 1, r.h - 6); g.fillRect(x - s * 6, y - r.h + 6, 1, r.h - 10);
    }
  }
  for (const c of CFF.coals) {
    const x = Math.round(c.x), y = Math.round(c.y);
    if (c.landed) { g.fillStyle = 'rgba(120,30,10,0.9)'; g.fillRect(x - 7, y - 2, 14, 2); g.fillStyle = `rgba(255,${120 + Math.floor(60 * Math.sin(time * 12))},40,0.9)`; g.fillRect(x - 4, y - 3, 8, 1); continue; }
    g.fillStyle = '#5a1409'; g.fillRect(x - 2, y - 2, 4, 4); g.fillStyle = '#f07f24'; g.fillRect(x - 1, y - 2, 2, 3); g.fillStyle = '#ffe2a0'; g.fillRect(x, y - 1, 1, 1);
  }
}
HOOKS.update.push(dt => { if (CFF.fx.length || CFF.rings.length || CFF.coals.length) cffUpdateFx(dt); });
HOOKS.render.push(() => { if (CFF.fx.length || CFF.rings.length || CFF.coals.length) cffDrawFx(); });
HOOKS.enter.push(() => { CFF.fx = []; CFF.rings = []; CFF.coals = []; });

// ================================================================== THE UNFORGED (elite)
// Moves per weapon type (art tags atk1-3, art/forge_foes_unforged_moves.py). dmg: per hit window, x the base (46, tiered).
// range: [min, max] px to the player to pick it; w: weight. hold: per hold-run of the art (in order): seconds, 'apex' (until
// the jump turns), 'land' (until grounded), 'guard' (blocks frontal blows; a blow struck into it fires the counter at once),
// 'run' (charges at the player), 'tp' (vanishes, reappears behind the player). jump: [run#, vx|'aim', vy]: the impulse when
// that hold-run starts. dash: {win: vx} extra speed through an active window. Specials: shot, wave, ring, pull, blast.
const UF_KITS = {
  longsword: { pref: 44, atk1: { dmg: [1.0, 1.0, 1.15], range: [0, 64], w: 3, hold: [0.12, 0.1] },
               atk2: { dmg: [1.75], range: [10, 74], w: 2, hold: [0.55], heat: 1 },
               atk3: { dmg: [1.3], range: [0, 60], w: 1.4, hold: ['guard'], guardT: 0.95, dash: { 1: 160 } } },
  katana: { pref: 70, sheathed: true, atk1: { dmg: [1.55], range: [56, 150], w: 3, hold: [0.38], dash: { 1: 520 }, through: true },
            atk2: { dmg: [0.95, 1.05], range: [0, 56], w: 2, hold: [0.12] },
            atk3: { dmg: [1.0], range: [44, 160], w: 1.5, hold: [0.55], wave: 'crescent' } },
  greatsword: { pref: 48, atk1: { dmg: [1.85], range: [0, 66], w: 2.4, hold: [0.7], heat: 1, shock: 1 },
                atk2: { dmg: [1.3], range: [0, 72], w: 2, hold: [0.22] },
                atk3: { dmg: [0.8, 1.2], range: [56, 140], w: 1.6, hold: [0.25], dash: { 1: 300 } } },
  maul: { pref: 46, atk1: { dmg: [1.8], range: [0, 62], w: 2.4, hold: [0.32], shock: 2 },
          atk2: { dmg: [0.85, 0.85], range: [0, 72], w: 1.6, hold: [0.22], dash: { 1: 60, 2: 60 } },
          atk3: { dmg: [1.6], range: [60, 160], w: 1.6, hold: ['apex'], jump: [0, 'aim', -300], land: true, shock: 2, ring: 1 } },
  sns: { pref: 40, guard: true, atk1: { dmg: [0.9, 0.95], range: [0, 56], w: 3, hold: [0.12] },
         atk2: { dmg: [0.9], range: [44, 130], w: 1.8, hold: [0.28], dash: { 1: 270 }, push: 1 },
         atk3: { dmg: [1.35], range: [0, 64], w: 1.4, hold: ['guard'], guardT: 1.1 } },
  dual: { pref: 40, demon: true, atk1: { dmg: [0.45, 0.45, 0.45, 0.45, 0.5, 0.55], range: [0, 54], w: 3, hold: [0.12], dash: { 1: 40, 3: 40, 5: 40 } },
          atk2: { dmg: [1.1], range: [56, 150], w: 2, hold: [0.3], dash: { 1: 440 }, through: true },
          atk3: { dmg: [0.55, 0.55, 0.6], range: [0, 66], w: 1.6, hold: [0.2], dash: { 1: 70, 2: 70, 3: 70 } } },
  spear: { pref: 62, atk1: { dmg: [0.9, 1.0], range: [36, 92], w: 3, hold: [0.15] },
           atk2: { dmg: [0.8, 1.3], range: [84, 190], w: 2, hold: [0.38, 'run'] },
           atk3: { dmg: [1.35], range: [44, 104], w: 1.5, hold: [0.1], dash: { 1: 320 } } },
  staff: { pref: 46, atk1: { dmg: [0.6, 0.6, 0.75], range: [0, 64], w: 3, hold: [0.14] },
           atk2: { dmg: [1.2], range: [54, 150], w: 2, hold: [0.24, 'apex', 'land'], jump: [1, 'aim', -280] },
           atk3: { dmg: [0.8, 1.05], range: [0, 60], w: 1.6, hold: [0.24] } },
  whip: { pref: 74, kite: true, atk1: { dmg: [1.0], range: [40, 100], w: 3, hold: [0.22], tip: 1 },
          atk2: { dmg: [0.5, 0.9], range: [50, 100], w: 1.6, hold: [0.18, 0.12], pull: 1 },
          atk3: { dmg: [1.5], range: [40, 100], w: 1.4, hold: [0.25], tip: 1, blast: 1 } },
  saxe: { pref: 44, atk1: { dmg: [0.9, 1.0], range: [0, 62], w: 3, hold: [0.14] },
          atk2: { dmg: [1.3], range: [0, 62], w: 1.8, hold: [0.38], next: 'atk3' },
          atk3: { dmg: [1.8], range: [34, 70], w: 0, hold: [0.3], blast: 1 } },
  bow: { pref: 70, kite: true, atk1: { dmg: [0.95], range: [30, 120], w: 3, hold: [0.24], shot: 'arrow' },
         atk2: { dmg: [1.8], range: [40, 130], w: 1.6, hold: [0.6], shot: 'heavy', heat: 1 },
         atk3: { dmg: [0.8, 0.8], range: [0, 46], w: 2.4, hold: [0.18, 'land'], jump: [1, -150, -200], shot: 'arrow' } },
  fist: { pref: 30, atk1: { dmg: [0.5, 0.5, 0.75], range: [16, 50], w: 3, hold: [0.12] },
          atk2: { dmg: [1.6], range: [0, 56], w: 1.6, hold: [0.5], push: 1, heat: 1 },
          atk3: { dmg: [1.45], range: [46, 140], w: 1.6, hold: ['apex'], jump: [0, 'aim', -300], land: true, shock: 1 } },
  scythe: { pref: 52, atk1: { dmg: [1.3], range: [0, 72], w: 3, hold: [0.3] },
            atk2: { dmg: [0.55, 0.9], range: [40, 92], w: 1.6, hold: [0.24, 0.14], pull: 1 },
            atk3: { dmg: [1.25], range: [30, 130], w: 1.6, hold: [0.24, 'tp'] } },
  bell: { pref: 44, atk1: { dmg: [1.0, 0.9], range: [24, 66], w: 3, hold: [0.24] },
          atk2: { dmg: [1.8], range: [0, 72], w: 1.6, hold: [0.65], ring: 2, heat: 1 },
          atk3: { dmg: [1.1], range: [0, 60], w: 1.4, hold: [0.3], ring: 3 } },
};
const UF_COL = { longsword: '200,215,240', katana: '205,225,255', greatsword: '255,160,80', maul: '255,190,120', sns: '255,215,150', dual: '235,70,80',
  spear: '170,210,255', staff: '190,235,215', whip: '150,195,255', saxe: '255,150,70', bow: '255,145,60', fist: '255,125,60', scythe: '205,185,255', bell: '240,212,150' };

function cffUfRoll(key) {
  if (CFF.force && CFF_TYPES.includes(CFF.force)) return CFF.force;
  // a spawn spec may fix the type: {"t":"enemy","type":"cf_unforged","w":"katana"}
  const m = /^(.+):sp(\d+)$/.exec(key || '');
  const def = m && typeof ROOM_BY !== 'undefined' && ROOM_BY[m[1]], spec = def && def.spawns && def.spawns[+m[2]];
  if (spec && spec.w && CFF_TYPES.includes(spec.w)) return spec.w;
  const mine = typeof wtype === 'function' ? wtype() : null;
  const pool = CFF_TYPES.filter(t => t !== mine && sheet('cf_unforged_' + t).ok);
  return pool.length ? pool[Math.floor(Math.random() * pool.length) % pool.length] : 'longsword';
}

class CffUnforged extends Enemy {
  constructor(type, x, y, key) {
    super(type, x, y, key);
    this.wt = cffUfRoll(key);
    this.sh = sheet('cf_unforged_' + this.wt); if (this.sh.ok) this.sh.img;
    this.anim = new Anim(this.sh, 'idle');
    this.w = 18; this.h = 44; this.kit = UF_KITS[this.wt]; this.cool = 0.9; this.last = []; this.combo = null;
    this.runs = (this.sh.meta && this.sh.meta.holds) || {};   // [[first, last], ...] per tag: one per held key of the art
    CFF.log.push({ t: 'uf', wt: this.wt });
  }
  get demon() { return this.kit.demon && this.hp < this.maxHp * 0.55; }
  onAggro() {
    if (this.announced) return; this.announced = true;
    const nm = (typeof WTYPE_INFO !== 'undefined' && WTYPE_INFO[this.wt] && WTYPE_INFO[this.wt].name) || this.wt;
    toast(`The Unforged takes up the ${nm}.`, 2.6); cffSfx.clang();
  }
  // the sns stance and the guard holds turn frontal blows on the blades
  guarding(info) {
    if (info.crit || info.dir !== -this.face || info.kind === 'env') return false;
    if (this.state === 'attack' && this.holdKind === 'guard' && this.holdT > 0) return 'counter';
    if (this.kit.guard && ['idle', 'walk'].includes(this.state) && info.kind !== 'heavy' && info.kind !== 'spell') return 'block';
    return false;
  }
  hit(info) {
    if (!this.alive || this.tpT > 0) return;
    const g_ = this.guarding(info);
    if (g_) {
      cffSfx.clang(); sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir);
      this.stance += info.poise * 0.5; P.vx = -P.face * 110; hitstop = Math.max(hitstop, 0.06);
      const d = Math.round(info.dmg * 0.12); this.hp -= d; popup(info.x, info.y - 8, d, '#9a9aa8'); this.flash = 0.3;
      if (this.hp <= 0) return this.die(info);
      if (this.stance >= this.cfg.stance) return this.breakStance();
      if (g_ === 'counter') { this.holdT = 0; this.countered = true; this.facePlayer(); }
      return;
    }
    super.hit(info);
  }
  breakStance() { this.holdT = 0; this.tpT = 0; super.breakStance(); }
  pick() {
    const dx = Math.abs(P.x - this.x), dy = Math.abs(P.y - this.y), K_ = this.kit;
    if (dy > 46) return null;
    const c = [];
    for (const t of ['atk1', 'atk2', 'atk3']) {
      const m = K_[t]; if (!m || !m.w || dx < m.range[0] || dx > m.range[1] || !this.sh.has(t)) continue;
      let w = m.w; if (this.last[0] === t) w *= 0.45; if (this.last[0] === t && this.last[1] === t) w = 0;
      c.push([t, w]);
    }
    if (!c.length) return null;
    let s = c.reduce((a, b) => a + b[1], 0) * Math.random();
    for (const [t, w] of c) { if ((s -= w) <= 0) return t; }
    return c[c.length - 1][0];
  }
  begin(tag) {
    this.startAttack(tag); this.mv = this.kit[tag] || {}; this.run = -1; this.holdT = 0; this.holdKind = null; this.countered = false; this.pulled = false; this.spawnDone = new Set();
    this.firstActive = 99; const wins = metaWindows(this.sh, tag); if (wins.length) this.firstActive = wins[0].active[0];
    this.last.unshift(tag); this.last.length = Math.min(this.last.length, 3);
    if (this.demon) this.anim.speed = 1.22;
  }
  update(dt) {
    if (CFF_LIVE.includes(this.state)) { this.holdT = 0; return super.update(dt); }
    if (this.tpT > 0) { this.tpT -= dt; this.flash = 0; if (this.tpT <= 0) this.reappear(); return; }
    if (!cffPre(this, dt)) return;
    const dx = this.dist(), adx = Math.abs(dx), K_ = this.kit;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.combo) { const t = this.combo; this.combo = null; this.begin(t); break; }
        if (this.cool <= 0) { const t = this.pick(); if (t) { this.begin(t); break; } }
        let want = adx > K_.pref + 10 ? sign(dx) : 0;
        if (K_.kite && adx < K_.pref - 26) want = -sign(dx);
        this.walk(want, dt, this.demon ? 1.25 : 1);
        if (want === -sign(dx)) this.face = sign(dx);
        break;
      }
      case 'attack': this.updAtk(dt); break;
    }
    // presence: the heart between the blades; the weapon's colour when it means harm
    if (this.alive) {
      const h = cffPt(this, 'heart');
      addLight(h.x, h.y, 18 + (this.demon ? 10 : 0), this.demon ? '235,70,80' : '255,130,60', 0.45);
      addLight(this.x, this.y - 36, 46, '150,165,200', 0.32);   // a cold sheen off the blades: it must read in the dark
      if (this.state === 'attack' && this.holdT > 0) { const tp = cffPt(this, 'tip'); addLight(tp.x, tp.y, 24 + 16 * Math.sin(time * 18), UF_COL[this.wt], 0.55); }
    }
  }
  holdSpec(k) { const h = this.mv.hold || []; return h[k] !== undefined ? h[k] : 0; }
  updAtk(dt) {
    const an = this.anim, mv = this.mv, tag = this.atk, m = this.sh.meta || {};
    const runs = this.runs[tag] || [];
    if (an.i < this.firstActive - 1 && !mv.noTrack) this.facePlayer();
    // root motion: the art's forward travel moves the body (smoothly, over each frame)
    const fi = an.frame, root = m.root || [], dr = (root[fi] || 0) - (an.i > 0 ? (root[fi - 1] || 0) : 0);
    let vx = dr / Math.max(0.03, an.ms() / 1000 / (an.speed || 1));
    // holds
    if (an.changed) {
      const k = runs.findIndex(r => r[1] === an.i);
      if (k >= 0 && k > this.run) {
        this.run = k; const hs = this.holdSpec(k);
        this.holdKind = typeof hs === 'string' ? hs : 'time'; this.holdT = typeof hs === 'number' ? hs : 2.5;
        if (hs === 'guard') this.holdT = mv.guardT || 1;
        if (hs === 'run') this.holdT = 0.75;
        if (hs === 'tp') { this.holdT = 0.32; this.vanish(); }
        if (k === 0 || hs === 'guard') this.tell();
        if (mv.jump && mv.jump[0] === k) this.jump();
        if (this.holdT <= 0) this.holdKind = null;
      }
    }
    if (this.holdT > 0) {
      an.t = 0;   // freeze on the held frame
      this.holdT -= dt;
      const hk = this.holdKind;
      if (hk === 'apex' && this.vy > -30) this.holdT = 0;
      if (hk === 'land' && this.ground) this.holdT = 0;
      if (hk === 'run') { vx += 230; if (Math.abs(P.x - this.x) < 30 || !ledgeAhead(this, this.face) || wallAt(this, this.face)) this.holdT = 0; if (Math.random() < 0.4) particles.push({ x: this.x - this.face * 8, y: this.y - 2, vx: -this.face * rand(10, 40), vy: -rand(5, 25), life: 0.4, kind: 'dust' }); }
      if (hk === 'guard') { this.facePlayer(); if (Math.random() < 0.2) particles.push({ x: this.x + this.face * 12, y: this.y - rand(20, 50), vx: 0, vy: -rand(5, 15), life: 0.3, kind: 'spark' }); }
      if ((hk === 'time' || hk === 'guard') && mv.heat && Math.random() < 0.35) { const tp = cffPt(this, 'tip'); particles.push({ x: tp.x + rand(-4, 4), y: tp.y + rand(-4, 4), vx: rand(-10, 10), vy: -rand(10, 40), life: 0.5, kind: 'fire' }); }
      if (this.holdT <= 0 && this.countered) { this.facePlayer(); }
    }
    // a leap that strikes on landing waits in the air on the frame before the blow
    if (mv.land && this.air && !this.ground && an.i >= this.firstActive - 1) { an.t = 0; an.i = Math.min(an.i, this.firstActive - 1); }
    // dashes through active windows
    const wins = metaWindows(this.sh, tag);
    wins.forEach((w, wi) => { if (an.i >= w.active[0] && an.i <= w.active[1] && mv.dash && mv.dash[wi + 1]) vx += mv.dash[wi + 1]; });
    if (!this.air) {
      this.vx = this.face * vx;
      if (this.vx && (!ledgeAhead(this, sign(this.vx)) || wallAt(this, sign(this.vx)))) this.vx = 0;
    }
    // hit windows
    const base = this.cfg.dmg.atk;
    cffHitWindows(this, (wi, w, r) => {
      let d = base * ((mv.dmg || [])[wi] ?? 1);
      if (mv.tip) { const tipX = this.face > 0 ? r.x1 : r.x0; if (Math.abs(P.x - tipX) < (r.x1 - r.x0) * 0.32) { d *= 1.3; spawnFx(fxOr('parry_spark', 'hit'), P.x, P.y - 16, this.face); } }
      return d;
    }, { heavy: (mv.dmg || [1])[0] > 1.4, parryable: wi => !(mv.through && wi === 0),
         onStart: (w, wi) => this.onWindow(w, wi), onHit: (wi) => this.onHit(wi) });
    // projectiles from the art's spawn frames
    const sp = m.spawn && m.spawn[tag];
    if (sp && an.changed && sp.includes(an.i) && !this.spawnDone.has(an.i)) { this.spawnDone.add(an.i); this.shoot(); }
    // the pull of a hooked whip / scythe
    if (this.pulled && this.holdT > 0) { const tx = this.x + this.face * 30; P.x = approach(P.x, tx, 260 * dt); P.vx = 0; }
    if (this.air && this.ground && this.vy >= 0 && an.i > 0) this.air = false;
    if (this.air) { this.vy = Math.min(this.vy + 800 * dt, 420); moveBody(this, dt); this.clampRoom(); }
    else this.gravity(dt);
    if (an.done) {
      this.anim.speed = 1; this.air = false; this.pulled = false;
      if (mv.next) { this.combo = mv.next; this.setA('idle', 'idle'); this.cool = 0; return; }
      this.setA('idle', 'idle'); this.cool = rand(...this.cfg.cool) * (this.demon ? 0.6 : 1);
    }
  }
  tell() {
    const t = this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[this.atk];
    const p = t ? metaPoint(this.sh, this, t.at) : cffPt(this, 'tip');
    spawnFx('telegraph', p.x, p.y, this.face); sfx.glint();
  }
  jump() {
    const j = this.mv.jump; let vx = j[1];
    if (vx === 'aim') { const tAir = 2 * -j[2] / 800; vx = clamp(((P.x - this.x) * this.face - (j[3] ?? 22)) / tAir, 20, 220); }
    this.vx = this.face * vx; this.vy = j[2]; this.ground = false; this.air = true; sfx.jump();
  }
  vanish() {   // the scythe's hook step: it comes apart into falling blades and rebinds behind you
    this.tpT = 0.34; cffSfx.shatter();
    for (let i = 0; i < 16; i++) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, 60), vx: rand(-40, 40), vy: -rand(0, 40), g: 300, life: 0.5, kind: 'spark' });
  }
  reappear() {
    let nx = P.x - (P.face || 1) * 34;
    if (nx < 16 || nx > room.pw - 16 || solidAtPx(nx, this.y - 8)) nx = P.x + (P.face || 1) * 34;
    this.x = clamp(nx, 16, room.pw - 16); this.facePlayer(); this.holdT = 0; this.flash = 0.6;
    spawnFx(fxOr('death_ash', 'dust'), this.x, this.y, 1); for (let i = 0; i < 12; i++) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(0, 60), vx: 0, vy: -rand(10, 40), life: 0.5, kind: 'spark' });
  }
  onWindow(w, wi) {
    const mv = this.mv;
    if (this.air && wi === 0 && mv.jump) this.vy = Math.max(this.vy, 200);   // the vault kick dives
    const last = wi === metaWindows(this.sh, this.atk).length - 1;
    if (!last) return;
    const r = metaRect(this.sh, this, w.hit), fx = this.face > 0 ? r.x1 - 6 : r.x0 + 6;
    if (mv.shock) { shake = Math.max(shake, 6); sfx.boom(); spawnFx('shockwave', fx, this.y, 1); spawnFx('ground_crack', fx, this.y, 1);
      if (mv.shock === 2) for (const d of [-1, 1]) cffShock(fx, this.y, d, { dmg: this.cfg.dmg.atk * 0.55 });
      else cffShock(fx, this.y, this.face, { dmg: this.cfg.dmg.atk * 0.55 }); }
    if (mv.ring) { cffSfx.toll(mv.ring === 3 ? 262 : 196); cffRing(this.x + (mv.ring === 3 ? 0 : this.face * 24), this.y, { R: mv.ring === 3 ? 64 : 86, dmg: this.cfg.dmg.atk * 0.6, src: this }); if (mv.ring === 2) shake = Math.max(shake, 5); }
    if (mv.blast) {
      const tp = cffPt(this, 'tip'), bx = tp.x, by = this.y; sfx.boom(); shake = Math.max(shake, 5);   // the crack / the release lands on the floor under the tip
      spawnFx(fxOr('ashbolt_hit', 'hit'), bx, by - 10, 1, null, { tint: '#ff7030' }); spawnFx('ground_crack', bx, by, 1);
      for (let i = 0; i < 14; i++) particles.push({ x: bx, y: by - 4, vx: rand(-90, 90), vy: rand(-130, -20), g: 260, life: rand(0.3, 0.7), kind: 'fire' });
      addLight(bx, by - 12, 50, '255,140,60', 0.8);
      hazards.push({ x: bx, y: by, w: 36, h: 34, dmg: this.cfg.dmg.atk * 0.6, id: ++hazardId, life: 0.15 });
    }
    if (mv.wave === 'crescent') {
      const tp = cffPt(this, 'tip');
      projectiles.push({ owner: 'enemy', kind: 'moonwave', x: this.x + this.face * 20, y: this.y - 20, vx: this.face * 210, vy: 0, dmg: this.cfg.dmg.atk * 0.9, life: 0.62, r: 9, t: 0, id: ++hazardId });
    }
  }
  onHit(wi) {
    const mv = this.mv;
    if (mv.pull && wi === 0) { this.pulled = true; this.holdT = Math.max(this.holdT, 0.35); cffSfx.clack(); }
    if (mv.push) { P.vx = this.face * 260; }
  }
  shoot() {
    const mv = this.mv, tp = cffPt(this, 'tip'), d = this.cfg.dmg.atk;
    let ang = Math.atan2(P.y - 12 - tp.y, P.x - tp.x); if (this.face < 0) { ang = Math.PI - ang; if (ang > Math.PI) ang -= 2 * Math.PI; } ang = clamp(ang, -0.3, 0.9); if (this.face < 0) ang = Math.PI - ang;
    if (mv.shot === 'heavy') {
      for (const k of [-0.08, 0, 0.08]) projectiles.push({ owner: 'enemy', kind: 'arrow', x: tp.x, y: tp.y, vx: Math.cos(ang + k) * 300, vy: Math.sin(ang + k) * 300, g: 0, dmg: d * (k ? 0.7 : 1.8) * (mv.dmg[0] ? 1 : 1), life: 0.42, r: 3, t: 0, id: ++hazardId });
      shake = Math.max(shake, 3);
    } else projectiles.push({ owner: 'enemy', kind: 'arrow', x: tp.x, y: tp.y, vx: Math.cos(ang) * 240, vy: Math.sin(ang) * 240, g: 40, dmg: d * 0.95, life: 0.38, r: 3, t: 0, id: ++hazardId });
    sfx.shoot(); tone(200, 0.15, 0.06, 'triangle', 0.6);
  }
  die(info) {
    super.die(info); cffSfx.shatter(); this.holdT = 0; this.tpT = 0;
    if (info) for (let i = 0; i < 10; i++) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(10, 60), vx: rand(-60, 60), vy: -rand(20, 90), g: 360, life: rand(0.5, 1.0), kind: 'spark' });
  }
  draw() {
    if (this.tpT > 0) { if (Math.random() < 0.6) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(0, 50), vx: 0, vy: rand(10, 40), life: 0.3, kind: 'spark' }); return; }
    if (this.state === 'attack' && this.holdKind === 'guard' && this.holdT > 0) {   // the parry stance: a steel glint on the blade
      const tp = cffPt(this, 'tip'); g.fillStyle = `rgba(${UF_COL[this.wt]},${0.5 + 0.5 * Math.sin(time * 20)})`; g.fillRect(Math.round(tp.x) - 1, Math.round(tp.y) - 1, 2, 2);
    }
    const f0 = this.flash; if (this.state === 'attack' && this.holdT > 0 && this.holdKind === 'time' && this.mv.heat) this.flash = Math.max(this.flash, 0.12 + 0.1 * Math.sin(time * 16));
    super.draw(); this.flash = f0;
    if (this.demon && this.alive) { const h = cffPt(this, 'head'); g.fillStyle = 'rgba(235,70,80,0.9)'; g.fillRect(Math.round(h.x + this.face * 2), Math.round(h.y - 1), 2, 1); }
  }
}
ENEMY_CLASSES.cf_unforged = CffUnforged;

// ================================================================== the regular foes: a shared attack runner
// root motion from the art (meta.root), hold-runs (meta.holds) held for spec.hold[k] s (the first one is the tell), hit
// windows from the art, spawn frames (meta.spawn) -> spec.onSpawn.
function cffBegin(e, tag, spec) {
  e.startAttack(tag); e.spec = spec || {}; e.run = -1; e.holdT = 0; e.spawnDone = new Set();
  const w = metaWindows(e.sh, tag); e.firstActive = w.length ? w[0].active[0] : 99;
}
function cffRunAtk(e, dt) {
  const an = e.anim, m = e.sh.meta || {}, tag = e.atk, sp = e.spec || {};
  if (an.i < e.firstActive - 1 && !sp.noTrack) e.facePlayer();
  const root = m.root || [], fi = an.frame;
  let vx = ((root[fi] || 0) - (an.i > 0 ? (root[fi - 1] || 0) : 0)) / Math.max(0.03, an.ms() / 1000);
  const runs = (m.holds || {})[tag] || [];
  if (an.changed) {
    const k = runs.findIndex(r => r[1] === an.i);
    if (k >= 0 && k > e.run) {
      e.run = k; e.holdT = (sp.hold || [])[k] || 0;
      if (k === 0) { const t = m.telegraph && m.telegraph[tag]; const q = t ? metaPoint(e.sh, e, t.at) : cffPt(e, 'tip'); spawnFx('telegraph', q.x, q.y, e.face); if (sp.tell) sp.tell(e); else sfx.glint(); }
    }
  }
  if (e.holdT > 0) { an.t = 0; e.holdT -= dt; if (sp.holding) sp.holding(e, dt); }
  const wins = metaWindows(e.sh, tag);
  if (sp.dash) wins.forEach(w => { if (an.i >= w.active[0] && an.i <= w.active[1]) vx += sp.dash; });
  e.vx = e.face * vx;
  if (e.vx && (!ledgeAhead(e, sign(e.vx)) || wallAt(e, sign(e.vx)))) e.vx = 0;
  if (sp.windows !== false) cffHitWindows(e, wi => (e.cfg.dmg[tag] || 20) * ((sp.dmg || [])[wi] ?? 1), { heavy: sp.heavy, parryable: sp.parryable ?? true, onStart: sp.onStart && ((w, wi) => sp.onStart(e, w, wi)), onHit: sp.onHit && (wi => sp.onHit(e, wi)) });
  const spn = m.spawn && m.spawn[tag];
  if (spn && an.changed && spn.includes(an.i) && !e.spawnDone.has(an.i)) { e.spawnDone.add(an.i); if (sp.onSpawn) sp.onSpawn(e); }
  for (const key of ['hit', 'fling']) { const fr = m[key] && m[key][tag]; if (fr && an.changed && fr.includes(an.i) && sp['on_' + key]) sp['on_' + key](e); }
  e.gravity(dt);
  return an.done;
}

// ================================================================== HOLLOW SMITH
// Hammer (overhead, sparks), the tongs grab (unparryable, a block doesn't stop it, a roll does): it lifts you on the
// hot tongs (three burns), then hammers you off them; a hot coal flicked from the tongs at mid range.
const CFF_SMITH = {
  hammer: { hold: [0.16], heavy: true, onStart: (e, w) => { const q = metaRect(e.sh, e, w.hit), x = e.face > 0 ? q.x1 - 4 : q.x0 + 4; cffSfx.clang(); shake = Math.max(shake, 3); for (let i = 0; i < 10; i++) particles.push({ x, y: e.y - 2, vx: rand(-70, 70), vy: -rand(30, 110), g: 320, life: rand(0.3, 0.6), kind: 'spark' }); } },
  grab: { hold: [0.24], windows: false, tell: () => cffSfx.clack() },
  toss: { hold: [0.16], windows: false, onSpawn: e => { const t = cffPt(e, 'tongs'), T = 0.75, dx = clamp(P.x - t.x, -170, 170); CFF.coals.push({ x: t.x, y: t.y, vx: dx / T, vy: -200, dmg: e.cfg.dmg.toss, id: ++hazardId, t: 0, life: 1, src: e }); cffSfx.sizzle(); } },
};
class CffSmith extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.grabCd = rand(1, 3); this.tossCd = rand(1, 2); }
  update(dt) {
    if (this.state === 'hold' || this.state === 'throw') return this.updHold(dt);
    if (CFF_LIVE.includes(this.state)) return super.update(dt);
    if (!cffPre(this, dt)) return;
    this.grabCd -= dt; this.tossCd -= dt;
    const dx = this.dist(), adx = Math.abs(dx), dy = Math.abs(P.y - this.y);
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.cool <= 0 && dy < 30 && adx < 44) { if (this.grabCd <= 0 && Math.random() < 0.45) { this.grabCd = rand(4.5, 6.5); cffBegin(this, 'grab', CFF_SMITH.grab); } else cffBegin(this, 'hammer', CFF_SMITH.hammer); break; }
        if (this.cool <= 0 && dy < 50 && adx > 70 && adx < 170 && this.tossCd <= 0) { this.tossCd = rand(3.5, 5); cffBegin(this, 'toss', CFF_SMITH.toss); break; }
        this.walk(adx > 36 ? sign(dx) : 0, dt, 1);
        break;
      }
      case 'attack': {
        if (this.atk === 'grab') this.tryGrab();
        if (this.state !== 'attack') break;
        if (cffRunAtk(this, dt)) { this.setA('idle', 'idle'); this.cool = rand(...this.cfg.cool); }
        break;
      }
    }
    if (this.alive && this.state === 'attack' && this.atk === 'grab') { const t = cffPt(this, 'tongs'); addLight(t.x, t.y, 18, '255,130,60', 0.5); }
    if (this.alive) addLight(this.x + this.face * 6, this.y - 40, 12, '255,120,50', 0.3);
  }
  tryGrab() {   // the tongs' window: a roll (i-frames) slips it; a block does not
    const w = metaWindows(this.sh, 'grab')[0], i = this.anim.i;
    if (!w || i < w.active[0] || i > w.active[1] || this.caught) return;
    if (!overlap(metaRect(this.sh, this, w.hit), playerHurtbox()) || P.state === 'dead') return;
    if (P.inv > 0 || iframes() || SETTINGS.god) return;
    this.caught = true; this.burns = 0; this.burnT = 0.25; this.holdLeft = 1.05;
    P.vx = P.vy = 0; setP('rest', 'hurt', false); P.face = -this.face; cffSfx.clack(); sfx.bigHit(); hitstop = 0.1; shake = 4;
    this.setA('hold', 'hold', true);
  }
  holdPlayer() {
    const t = cffPt(this, 'tongs');
    P.x = t.x; P.y = t.y + 14; P.vx = P.vy = 0; P.face = -this.face;
    if (P.state !== 'rest' && P.state !== 'dead') setP('rest', 'hurt', false);
  }
  burn(dmg, release) {
    P.state = 'hurt'; P.inv = 0; P.lastHit = undefined;
    hurtPlayer(dmg, this.face, ++hazardId, { src: this });
    if (P.state === 'dead') { this.caught = false; return; }
    if (release) { this.caught = false; setP('hurt', 'hurt'); P.vx = this.face * 220; P.vy = -190; P.ground = false; P.inv = 0.7; }
    else setP('rest', 'hurt', false);
  }
  updHold(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt; this.anim.update(dt); this.vx = 0; this.gravity(dt);
    const t = cffPt(this, 'tongs');
    addLight(t.x, t.y, 30, '255,120,50', 0.7);
    if (Math.random() < 0.7) particles.push({ x: P.x + rand(-5, 5), y: P.y - rand(0, 22), vx: rand(-10, 10), vy: -rand(20, 50), life: 0.4, kind: 'fire' });
    if (!this.caught) { if (this.state === 'throw' && !this.anim.done) return; this.setA('idle', 'idle'); this.cool = rand(1.0, 1.6); return; }
    this.holdPlayer();
    if (this.state === 'hold') {
      this.burnT -= dt; this.holdLeft -= dt;
      if (this.burnT <= 0) { this.burnT = 0.33; this.burns++; cffSfx.sizzle(); this.burn(this.cfg.dmg.grab); }
      if (this.holdLeft <= 0 && this.caught) { this.setA('throw', 'throw', false); this.spec = { on_hit: e => { if (e.caught) { cffSfx.clang(); e.burn(e.cfg.dmg.hammer * 0.75); } }, on_fling: e => { if (e.caught) e.burn(0.0001, true); } }; this.throwSeen = new Set(); }
      return;
    }
    // throw: the hammer blow, then the fling
    const m = this.sh.meta || {}, i = this.anim.i;
    for (const key of ['hit', 'fling']) { const fr = m[key] && m[key].throw; if (fr && fr.includes(i) && !this.throwSeen.has(key)) { this.throwSeen.add(key); this.spec['on_' + key](this); } }
    if (this.anim.done) { if (this.caught) this.burn(0.0001, true); this.setA('idle', 'idle'); this.cool = rand(1.0, 1.6); }
  }
  hit(info) { super.hit(info); if (this.caught && (!this.alive || this.state === 'stagger' || this.state === 'hurt')) this.letGo(); }
  letGo() { if (!this.caught) return; this.caught = false; if (P.state === 'rest') { setP('hurt', 'hurt'); P.vy = -80; P.inv = 0.6; } }
  die(info) { this.letGo(); super.die(info); }
}
ENEMY_CLASSES.cf_smith = CffSmith;

// ================================================================== QUENCH WRAITH
// Lies as a ring of still water until you come near; rises with a hiss; hisses (the tell) then lunges a long way, or
// claws up close. Its touch is scalding steam: a hit also takes stamina. After a lunge it may sink and rise elsewhere.
const CFF_WRAITH = {
  hiss: { hold: [0.22], windows: false, tell: () => cffSfx.hiss() },
  lunge: { dash: 230, parryable: true, onHit: () => { P.st = Math.max(0, P.st - 22); } },
  claw: { hold: [0.12], onHit: () => { P.st = Math.max(0, P.st - 14); } },
};
class CffWraith extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.state = 'still'; this.anim.set('rise', false); this.anim.done = true; this.w = 14; this.h = 40; }
  hurtbox() { return ['still', 'rising', 'sunk'].includes(this.state) ? null : super.hurtbox(); }
  hit(info) { if (['still', 'sunk'].includes(this.state)) return; super.hit(info); }
  update(dt) {
    if (this.state === 'still' || this.state === 'sunk') {
      this.t += dt; this.gravity(dt); this.sunkT = (this.sunkT || 0) - dt;
      const near = Math.abs(P.x - this.x) < 84 && Math.abs(P.y - this.y) < 50 && P.state !== 'dead';
      if ((this.state === 'still' && near) || (this.state === 'sunk' && this.sunkT <= 0)) { this.state = 'rising'; this.anim.set('rise', false); cffSfx.hiss(0.8); this.aggro = true; this.facePlayer(); }
      return;
    }
    if (this.state === 'rising') { this.anim.update(dt); this.gravity(dt); if (Math.random() < 0.4) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, 30), vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'dust' }); if (this.anim.done) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.5; } return; }
    if (this.state === 'sinking') { this.anim.update(dt); this.gravity(dt); if (this.anim.done) this.resurface(); return; }
    if (CFF_LIVE.includes(this.state)) return super.update(dt);
    if (!cffPre(this, dt)) return;
    const dx = this.dist(), adx = Math.abs(dx), dy = Math.abs(P.y - this.y);
    switch (this.state) {
      case 'idle': case 'walk': {
        if (this.anim.tag !== 'idle') this.anim.set('idle', true);
        this.facePlayer();
        if (this.cool <= 0 && dy < 34 && adx < 40) { cffBegin(this, 'claw', CFF_WRAITH.claw); break; }
        if (this.cool <= 0 && dy < 34 && adx >= 40 && adx < 132 && ledgeAhead(this, this.face)) { cffBegin(this, 'hiss', CFF_WRAITH.hiss); break; }
        const want = adx > 60 ? sign(dx) : adx < 30 ? -sign(dx) : 0;   // drifts, keeping a lunge's distance
        let d = want; if (d && (!ledgeAhead(this, d) || wallAt(this, d))) d = 0;
        this.vx = approach(this.vx, d * this.cfg.speed, 300 * dt); this.state = d ? 'walk' : 'idle'; this.gravity(dt);
        break;
      }
      case 'attack': {
        if (cffRunAtk(this, dt)) {
          if (this.atk === 'hiss') { cffBegin(this, 'lunge', CFF_WRAITH.lunge); cffSfx.hiss(0.5); break; }
          if (this.atk === 'lunge' && Math.random() < 0.4) { this.state = 'sinking'; this.anim.set('sink', false); cffSfx.hiss(0.6); break; }
          this.state = 'idle'; this.anim.set('idle', true); this.cool = rand(...this.cfg.cool);
        }
        break;
      }
    }
    if (this.alive) { const h = cffPt(this, 'head'); addLight(h.x, h.y, 26, '190,215,235', 0.35); }
  }
  resurface() {   // rises again from the floor beside you
    let nx = null;
    for (let k = 0; k < 12 && nx === null; k++) {
      const x = P.x + (k % 2 ? -1 : 1) * rand(70, 110); if (x < 16 || x > room.pw - 16) continue;
      if (solidAtPx(x, this.y - 8) || !groundBelow({ x, y: this.y, w: this.w, h: this.h }, 2)) continue; nx = x;
    }
    if (nx !== null) this.x = nx;
    this.state = 'sunk'; this.sunkT = 0.6; this.anim.set('rise', false); this.anim.done = true;
  }
  draw() {
    if (this.state === 'still' || this.state === 'sunk') {   // a ring of still water and a breath of steam
      const x = Math.round(this.x), y = Math.round(this.y), a = 0.35 + 0.15 * Math.sin(this.t * 2);
      g.fillStyle = `rgba(10,14,20,0.8)`; g.fillRect(x - 12, y - 1, 24, 2);
      g.fillStyle = `rgba(150,175,195,${a})`; g.fillRect(x - 10 + Math.round(Math.sin(this.t) * 2), y - 1, 6, 1); g.fillRect(x + 3, y - 1, 5, 1);
      if (Math.random() < 0.05) particles.push({ x: x + rand(-8, 8), y: y - 2, vx: 0, vy: -rand(6, 16), life: 1.2, kind: 'dust' });
      return;
    }
    super.draw();
  }
}
ENEMY_CLASSES.cf_wraith = CffWraith;

// ================================================================== BELLOWS HULK
// Never flinches, but is built to be staggered: its stance gives far sooner than its health, its core flares as the
// stance runs out (the tell), and after the bellows blast it VENTS (1.6 s slumped, the core open: stance damage x1.8).
// Slam (two fists; heat runs along the floor both ways), sweep (a long backhand), blast (a cone of hot air and cinders).
const CFF_HULK = {
  slam: { hold: [0.22], heavy: true, onStart: (e, w) => { const q = metaRect(e.sh, e, w.hit), x = e.face > 0 ? q.x1 - 6 : q.x0 + 6; shake = Math.max(shake, 7); sfx.boom(); spawnFx('shockwave', x, e.y, 1); spawnFx('ground_crack', x, e.y, 1); for (const d of [-1, 1]) cffShock(x, e.y, d, { dmg: e.cfg.dmg.slam * 0.5, v: 140 }); } },
  sweep: { hold: [0.18], heavy: true },
  blast: { hold: [0.35], windows: false, tell: e => { cffSfx.bellows(); }, onSpawn: e => cffBlast(e) },
};
function cffBlast(e) {   // the bellows empties through the chest grate: a cone of hot air in front, 0.5 s
  const c = cffPt(e, 'core'); cffSfx.bellows(); shake = Math.max(shake, 4);
  const h = { x: c.x + e.face * 40, y: e.y, w: 70, h: 36, dmg: e.cfg.dmg.blast, id: ++hazardId, life: 0.55, tick: 0.18, src: e, update(h, dt) { h.x = e.x + e.face * 46; } };
  hazards.push(h);
  for (let i = 0; i < 40; i++) { const a = rand(-0.35, 0.35); particles.push({ x: c.x, y: c.y, vx: e.face * Math.cos(a) * rand(120, 260), vy: Math.sin(a) * rand(80, 160) - 20, g: 60, life: rand(0.3, 0.6), kind: i % 3 ? 'fire' : 'ash' }); }
  CFF.fx.push({ k: 'blast', t: 0, life: 0.55, e });
}
class CffHulk extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.w = 22; this.h = 44; this.vent = 0; this.flared = false; this.blastCd = rand(2, 4); }
  hit(info) {
    if (!this.alive) return;
    const k = this.vent > 0 ? 1.8 : 1;
    super.hit(k !== 1 ? { ...info, poise: info.poise * k } : info);
    if (this.state === 'stagger' && !this.staggerSeen) { this.staggerSeen = true; this.vent = 0; cffSfx.flare(); spawnFx(fxOr('parry_flash', 'parry_spark'), cffPt(this, 'core').x, cffPt(this, 'core').y, this.face, null, { alpha: 0.8 }); }
    if (this.state !== 'stagger') this.staggerSeen = false;
  }
  update(dt) {
    if (CFF_LIVE.includes(this.state)) { if (this.state === 'stagger') this.coreFx(dt, 1); return super.update(dt); }
    if (!cffPre(this, dt)) return;
    this.blastCd -= dt;
    const dx = this.dist(), adx = Math.abs(dx), dy = Math.abs(P.y - this.y), sk = this.stance / this.cfg.stance;
    if (sk > 0.6 && !this.flared) { this.flared = true; cffSfx.flare(); }
    if (sk < 0.45) this.flared = false;
    switch (this.state) {
      case 'vent':
        this.vent -= dt; this.vx *= Math.pow(0.02, dt); this.gravity(dt);
        if (Math.random() < 0.3) particles.push({ x: this.x + this.face * 8 + rand(-6, 6), y: this.y - rand(30, 50), vx: rand(-10, 10), vy: -rand(10, 30), life: 0.8, kind: 'ash' });
        if (this.vent <= 0) { this.setA('idle', 'idle'); this.cool = 0.4; }
        break;
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.cool <= 0 && dy < 40) {
          if (adx < 60 && this.blastCd <= 0 && Math.random() < 0.4) { this.blastCd = rand(6, 9); cffBegin(this, 'blast', CFF_HULK.blast); break; }
          if (adx < 46) { cffBegin(this, Math.random() < 0.55 ? 'slam' : 'sweep', Math.random() < 0.55 ? CFF_HULK.slam : CFF_HULK.sweep); this.spec = CFF_HULK[this.atk]; break; }
          if (adx < 70) { cffBegin(this, 'sweep', CFF_HULK.sweep); break; }
        }
        this.walk(adx > 40 ? sign(dx) : 0, dt, 1);
        break;
      }
      case 'attack':
        if (cffRunAtk(this, dt)) {
          if (this.atk === 'blast') { this.state = 'vent'; this.anim.set('vent', true); this.vent = 1.6; cffSfx.hiss(1.2); break; }
          this.setA('idle', 'idle'); this.cool = rand(...this.cfg.cool);
        }
        break;
    }
    this.coreFx(dt, this.vent > 0 ? 0.85 : sk);
  }
  coreFx(dt, k) {   // the stagger tell: the core flares as the stance gives (and while it vents)
    if (!this.alive) return;
    const c = cffPt(this, 'core'), f = clamp((k - 0.3) / 0.7, 0, 1);
    addLight(c.x, c.y, 16 + 30 * f, '255,140,60', 0.35 + 0.5 * f);
    if (f > 0.4 && Math.random() < f * 0.6) particles.push({ x: c.x + rand(-3, 3), y: c.y + rand(-4, 4), vx: this.face * rand(10, 50), vy: -rand(20, 70), g: 120, life: rand(0.3, 0.6), kind: 'fire' });
    this.coreK = f;
  }
  draw() {
    super.draw();
    if (this.alive && this.coreK > 0.5) {   // a hot flicker over the grate
      const c = cffPt(this, 'core'), a = (this.coreK - 0.5) * 1.6 * (0.6 + 0.4 * Math.sin(time * 30));
      g.fillStyle = `rgba(255,${190 + Math.floor(40 * Math.sin(time * 20))},120,${a})`; g.fillRect(Math.round(c.x) - 1, Math.round(c.y) - 2, 3, 5);
    }
  }
  setA(st, tag, loop = true, speed = 1) { super.setA(st, tag, loop, speed); }
}
ENEMY_CLASSES.cf_hulk = CffHulk;
const cffDrawBlast = () => {
  for (const f of CFF.fx) if (f.k === 'blast') {
    const e = f.e, c = cffPt(e, 'core'), k = f.t / f.life;
    for (let i = 0; i < 26; i++) {
      const d = 6 + (i * 37 % 64) * (0.4 + k), yy = c.y + ((i * 13) % 17 - 8) * (0.3 + d / 64) + (e.y - c.y) * 0.3 * (d / 64);
      g.fillStyle = `rgba(255,${120 + (i * 29) % 100},60,${(1 - k) * 0.7})`; g.fillRect(Math.round(c.x + e.face * d), Math.round(yy), 2, 1);
    }
  }
};
HOOKS.render.push(() => { if (CFF.fx.length) cffDrawBlast(); });

// ================================================================== CINDER MITE
// Crawls, leaps at you; a leap that lands clings (up to three at once) and burns every half second until you roll it
// off (or it drops away after 4 s).
class CffMite extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.w = 12; this.h = 8; this.cool = rand(0.3, 1.2); }
  hurtbox() { return this.state === 'cling' ? null : super.hurtbox(); }
  update(dt) {
    if (this.state === 'cling') return this.updCling(dt);
    if (CFF_LIVE.includes(this.state)) return super.update(dt);
    if (!cffPre(this, dt)) return;
    const dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (this.cool <= 0 && adx < 74 && adx > 10 && Math.abs(dy) < 30 && this.ground) { this.startAttack('leap'); this.leapt = false; break; }
        this.walk(adx > 14 ? sign(dx) : 0, dt, 1);
        break;
      }
      case 'attack': {
        const an = this.anim, w = metaWindows(this.sh, 'leap')[0] || { active: [2, 4] };
        if (!this.leapt && an.i >= w.active[0]) { this.leapt = true; this.vx = this.face * clamp(adx * 2.4, 90, 190); this.vy = -150; this.ground = false; tone(1800, 0.06, 0.03, 'square', 0.6); }
        if (this.leapt && !this.ground && an.i >= w.active[1]) an.t = 0;   // stays curled until it lands
        if (this.leapt && !this.ground && overlap(this.hurtbox() || rect(0, 0, 0, 0), playerHurtbox()) && P.state !== 'dead') {
          const clingers = enemies.filter(e => e.state === 'cling').length;
          if (P.inv <= 0 && !iframes() && !SETTINGS.god && clingers < 3) { this.clingOn(); break; }
          if (hurtPlayer(this.cfg.dmg.leap, this.face, this.atkId, { src: this })) {}
        }
        if (!this.leapt) this.vx *= Math.pow(0.01, dt);
        this.vy = Math.min(this.vy + 600 * dt, 400); moveBody(this, dt); this.clampRoom();
        if (an.done && this.ground) { this.setA('idle', 'crawl'); this.state = 'idle'; this.cool = rand(...this.cfg.cool); }
        break;
      }
    }
    if (this.alive) addLight(this.x, this.y - 4, 12, '255,120,50', 0.3);
  }
  clingOn() {
    this.state = 'cling'; this.anim.set('cling', true); this.clingT = 4; this.burnT = 0.5; this.off = { x: rand(-4, 4), y: -rand(6, 20) };
    sfx.hit(); cffSfx.sizzle(); P.flash = 0.6; tone(1400, 0.1, 0.04, 'square', 0.5);
  }
  updCling(dt) {
    this.anim.update(dt); this.flash = Math.max(0, this.flash - dt * 5);
    this.x = P.x + this.off.x * (P.face || 1); this.y = P.y + this.off.y + 8; this.face = -(P.face || 1);
    this.clingT -= dt; this.burnT -= dt;
    if (this.burnT <= 0 && P.state !== 'dead') {
      this.burnT = 0.5; const d = Math.max(1, Math.round(this.cfg.burn * NGP.dmg * (BIOME_TIER.forge && room && room.def.biome === 'forge' ? 1 : 1)));
      P.hp = Math.max(0, P.hp - d); popup(P.x, P.y - 30, d, '#ff8a4a'); CFF.burns = (CFF.burns || 0) + 1; P.flash = 0.3; cffSfx.sizzle();
      for (let i = 0; i < 4; i++) particles.push({ x: this.x + rand(-3, 3), y: this.y - 4, vx: rand(-20, 20), vy: -rand(20, 50), life: 0.4, kind: 'fire' });
      if (P.hp <= 0) killPlayer(this.face);
    }
    addLight(this.x, this.y - 4, 14, '255,120,50', 0.5);
    if (P.state === 'roll' || this.clingT <= 0 || P.state === 'dead' || P.state === 'rest') this.shakeOff();
  }
  shakeOff() {
    this.state = 'idle'; this.anim.set('hurt', false); this.vx = -(P.face || 1) * rand(60, 120) * (Math.random() < 0.5 ? 1 : -1); this.vy = -140; this.ground = false;
    this.cool = rand(0.8, 1.4); this.y = P.y; this.x = clamp(this.x, 10, room.pw - 10); if (solidAtPx(this.x, this.y - 4)) this.x = P.x;
  }
  draw() { if (this.state !== 'cling') super.draw(); }
  drawCling() { Enemy.prototype.draw.call(this); const a = 0.5 + 0.5 * Math.sin(time * 14); g.fillStyle = `rgba(255,150,60,${a})`; g.fillRect(Math.round(this.x) - 1, Math.round(this.y) - 6, 2, 2); }
}
ENEMY_CLASSES.cf_mite = CffMite;
HOOKS.render.push(() => { for (const e of enemies) if (e.type === 'cf_mite' && e.state === 'cling') e.drawCling(); });   // over the player it clings to
// a clutch of mites: {"t": "cf_swarm", "x": tx, "y": ty, "n": 4}
SPAWNS.cf_swarm = (s, c) => {
  const n = clamp(s.n || 3, 1, 8);
  for (let k = 0; k < n; k++) { const key = `${c.key}:${k}`; if (killed.has(key)) continue; enemies.push(makeEnemy('cf_mite', c.cx + (k - (n - 1) / 2) * 14, c.fy, key)); }
};

if (typeof window !== 'undefined' && window.__game) window.__game.cff = { CFF, CFF_TYPES, UF_KITS, force: t => { CFF.force = t; } };
