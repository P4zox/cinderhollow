// ------------------------------------------------------------------ The Pale Sovereign, reworked (agent Z)
// Phases 1-2: MetaBoss-driven with a much larger moveset (sheets split per tag: sovereign_meta.sheets).
// Phase 3 (at 30%): she unmakes herself and the Root wakes -- "The Pale Root, Unbound", a vast serpentine
// star-beast assembled along a swimming spine (art/gen_sovbeast.py), fought in the void inside the Root's heart.
// Her final death (phase 3 only) still ends the game (victoryBanner.ending -> beginEnding).
const SOV = { marks: [], bind: null, rings: [], meteors: [], well: null };
const SOV_P3AT = 0.3, SOV_BEAST_HP = 3400;
const SOV_QUOTE = BOSS_INFO.sovereign.quote, SOV_QUOTE3 = 'It remembers what it was, before she wore it.';
const SOV_RANGED = new Set(['rain', 'lance', 'orbs', 'beam', 'crown', 'petals', 'spears']);
Object.assign(AREAS, { sov_void: { name: 'The Heart of the Root', ambient: 0.22, amb: 'mote', tint: '#05040b' } });
Object.assign(SCALES, { sov_void: [0, 1, 5, 7, 8] });
Object.assign(ROOTS, { sov_void: 41.2 });

// the phase-3 arena: swap the parallax/lighting biome of the *built* room only (the ROOMS def is untouched,
// so a rebuilt room -- death, reload -- is always the Pale Crown again)
function sovSetVoid(on) {
  if (!room) return;
  if (on && room.def.biome !== 'sov_void') room.def = Object.assign(Object.create(room.def), { biome: 'sov_void' });
  else if (!on && room.def.biome === 'sov_void') room.def = Object.getPrototypeOf(room.def);
}
const sovDmg = d => BOSS_DMG * d * NGP.dmg * 1.15, sovDmgB = d => sovDmg(d * 1.3);   // final boss: hits harder than Morvain; the beast harder still
// floor warning glyphs (drawn under hazards until `life` runs out)
function sovMark(x, y, life, w = 16, strong = false) { SOV.marks.push({ x, y, life, t: 0, w, strong }); }
// a delayed hazard that plays an fx sheet and is active on some of its frames
function sovFxHazard(o) {
  const h = { x: o.x, y: o.y, w: o.w, h: o.h, dmg: sovDmg(o.dmg), id: ++hazardId, life: 6, delay: o.delay || 0, fx: null,
    onStart: h => { h.fx = spawnFx(fxOr(o.fx, 'pillar'), h.x + (o.fxdx || 0), h.y, o.dir || 1, null, { bottom: true, speed: o.speed || 1 }); if (!h.fx) h.life = 0; o.onStart && o.onStart(h); },
    update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } const i = h.fx.anim.i; if (i >= o.act[0] && i <= o.act[1]) addLight(h.x, h.y - h.h / 2, 50, '255,230,170', 0.8); o.update && o.update(h); },
    active: h => h.fx && h.fx.anim.i >= o.act[0] && h.fx.anim.i <= o.act[1] };
  if (o.mark !== false) sovMark(o.x, o.y, (o.delay || 0) + 0.05, o.markW || 16, o.strong);
  hazards.push(h); return h;
}
function sovWhip(x, floor, delay, dir) {
  return sovFxHazard({ x: x + dir * 12, fxdx: -dir * 12, y: floor, w: 34, h: 58, dmg: 40, delay, fx: 'sov_whip', act: [3, 6], dir, markW: 22,
    onStart: () => { sfx.pillar(); for (let i = 0; i < 6; i++) particles.push({ x: x + rand(-8, 8), y: floor - 2, vx: rand(-50, 50), vy: -rand(40, 120), g: 400, life: 0.5, kind: 'rock' }); } });
}
function sovSpear(x, floor, delay) {
  return sovFxHazard({ x, y: floor, w: 14, h: 88, dmg: 46, delay, fx: 'sov_spear', act: [3, 5], markW: 14, strong: true,
    onStart: () => { sfx.pillar(); shake = Math.max(shake, 2); } });
}
// straight light ray from (x,y) along angle a (radians), stopped by the floor; returns end point and hit test
function sovRay(x, y, a, maxL, floor) {
  const dx = Math.cos(a), dy = Math.sin(a);
  let L = maxL;
  if (dy > 0.001) L = Math.min(L, (floor - y) / dy);
  return { x, y, a, L, ex: x + dx * L, ey: y + dy * L };
}
function sovRayHits(r, w = 7) {
  const hb = playerHurtbox();
  for (let s = 6; s <= r.L; s += 6) { const px = r.x + Math.cos(r.a) * s, py = r.y + Math.sin(r.a) * s; if (overlap(rect(px - w, py - w, px + w, py + w), hb)) return true; }
  return false;
}
function sovDrawRay(r, k = 1, thin = false) {
  const s = fxSheet('sov_beam');
  if (thin || !s.ok) {   // aim line: a thin dashed thread of light
    g.save(); g.globalAlpha = 0.35 + 0.35 * Math.sin(time * 30) * k;
    for (let d = 8; d < r.L; d += 7) { g.fillStyle = d % 14 < 7 ? '#fff4c8' : '#e6b85c'; g.fillRect(Math.round(r.x + Math.cos(r.a) * d), Math.round(r.y + Math.sin(r.a) * d), 2, 1); }
    g.restore(); return;
  }
  const t = s.tag(Object.keys(s.tags)[0]), n = t.to - t.from + 1, f = t.from + Math.floor(time * 16) % n;
  for (let d = 0; d < r.L; d += s.fw - 2) {
    const cx = r.x + Math.cos(r.a) * (d + s.fw / 2), cy = r.y + Math.sin(r.a) * (d + s.fw / 2);
    g.save(); g.globalAlpha = k; g.translate(Math.round(cx), Math.round(cy)); g.rotate(r.a);
    g.drawImage(s.img, s.frames[f].x, s.frames[f].y, s.fw, s.fh, -s.fw / 2, -s.fh / 2, s.fw, s.fh); g.restore();
    if (d % 48 < s.fw) addLight(cx, cy, 44, '255,230,170', 0.9 * k);
  }
  const e = fxSheet('sov_beamend');
  if (e.ok && r.L < 1000) { const te = e.tag(Object.keys(e.tags)[0]); drawSprite(e, te.from + Math.floor(time * 14) % (te.to - te.from + 1), r.ex, r.ey, 1, { center: true, alpha: k }); addLight(r.ex, r.ey - 6, 70, '255,220,150', k); }
}

// ================================================================== phases 1-2
class SovereignBoss extends MetaBoss {
  constructor(x, y, cfg) {
    super('sovereign', x, y, cfg);
    this.meta = ASSETS.sovereign_meta || {};
    this.smap = this.meta.sheets || { p1: {}, p2: {} };
    for (const k of ['p1', 'p2']) for (const n of Object.values(this.smap[k] || {})) sheet(n, { meta: this.meta });
    this.hidden = false; this.recent = [];
  }
  hasTag(tag) { return !!((this.smap.p1 || {})[tag]); }
  sheetFor(tag) {
    const m = this.phase >= 2 ? this.smap.p2 : this.smap.p1, n = (m && m[tag]) || (this.smap.p1 && this.smap.p1[tag]);
    return n ? sheet(n, { meta: this.meta }) : this.sheetsArr[this.phase >= 2 && this.sheetsArr[1] ? 1 : 0];
  }
  setS(st, tag, loop = true) {
    this.state = st;
    let sh = this.sheetFor(tag);
    if (!sh.has(tag)) { tag = 'idle'; sh = this.sheetFor('idle'); }
    this.sh = sh; this.tag = tag; this.anim = new Anim(sh, tag, loop, this.speed);
  }
  hurtbox() { if (this.hidden || this.phase === 3) return null; return super.hurtbox(); }
  canStagger() { return !this.hidden && this.state !== 'transform' && !(this.state === 'attack' && ['nova', 'rings', 'crown', 'vanish', 'grabhold'].includes(this.atk)); }
  pickMove() {
    const d = Math.abs(P.x - this.x), w = this.weights(d, this.phase === 2);
    if (w[this.last]) w[this.last] *= 0.25;
    if (this.recent[1] && w[this.recent[1]]) w[this.recent[1]] *= 0.6;
    const e = Object.entries(w).filter(([k, v]) => v > 0 && (k === 'glide' || k === 'blink' || this.hasTag(k)));
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e.length ? e[0][0] : 'glide';
  }
  start(m) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.spawned = false; this.air = null; this.fired = {}; this.mv = {};
    this.recent.unshift(m); this.recent.length = Math.min(this.recent.length, 3);
    this.rangedRun = SOV_RANGED.has(m) ? (this.rangedRun || 0) + 1 : 0;
    if (m === 'glide') {
      this.setS('glide', 'glide'); this.t = 1.6;
      const side = Math.abs(P.x - this.L) < 110 ? 1 : Math.abs(P.x - this.R) < 110 ? -1 : (Math.random() < 0.5 ? -1 : 1);
      this.glideTo = clamp(P.x + side * rand(70, 120), this.L + 40, this.R - 40); return;
    }
    if (m === 'blink') m = this.atk = 'vanish';
    this.setS('attack', m, false);
    const wins = metaWindows(this.sh, m); this.firstActive = wins.length ? wins[0].active[0] : 4;
    const M = this.moves[m]; M && M.begin && M.begin.call(this);
  }
  update(dt) {
    if (this.phase === 3 || this.state === 'transform') return this.p3update(dt);
    if (this.state === 'blinking') return this.blinkUpdate(dt);
    super.update(dt);
    if (this.alive && this.active && this.phase === 2 && this.hp <= this.maxHp * SOV_P3AT) this.pendingP3 = true;
    if (this.pendingP3 && this.alive && this.active && P.state !== 'dead' && ['idle', 'glide', 'walk'].includes(this.state) && state === 'play') this.startTransform();
  }
  updateAttack(dt) {
    if (this.pendingP3 && this.anim.done && this.phase === 2) { this.setS('idle', 'idle'); return; }
    const M = this.moves[this.atk] || {};
    M.tick && M.tick.call(this, dt, this.anim);
    if (this.state !== 'attack') return;   // tick may have switched move (grab -> grabhold, vanish -> blink)
    // her own chaining (more aggressive than the MetaBoss default): p1 50% x1, p2 70% up to x2
    const an = this.anim, ch = this.chains && this.chains[this.atk];
    if (an.done && ch && !this.pendingPhase && !this.pendingP3 && P.state !== 'dead' && this.chain < (this.phase === 2 ? 2 : 1) && Math.random() < (this.phase === 2 ? 0.7 : 0.5)) {
      const nx = typeof ch === 'function' ? ch.call(this, Math.abs(P.x - this.x)) : ch;
      if (nx) { this.chain++; this.mv.rays = null; return this.start(nx); }
    }
    const saved = this.chains;
    if (an.done) { this.chain = 0; this.chains = null; }   // chaining decided above, not by MetaBoss
    super.updateAttack(dt);
    this.chains = saved;
  }
  blinkUpdate(dt) {
    this.commonUpdate(dt); this.anim.update(dt); this.hover += dt;
    this.t -= dt;
    for (let i = 0; i < 2; i++) particles.push({ x: this.blinkTo + rand(-30, 30), y: this.baseY - rand(20, 130), vx: rand(-20, 20), vy: rand(-10, 20), life: 0.7, kind: 'petal' });
    addLight(this.blinkTo, this.baseY - 70, 60, '255,240,210', 0.7);
    if (this.t <= 0) { this.x = this.blinkTo; this.hidden = false; this.facePlayer(); this.start('cross'); sfx.glint(); }
  }
  stagger() {
    if (this.phase === 3) return this.beastStagger();
    super.stagger(); this.setS('stagger', 'stagger', false); this.anim.speed = 1; this.t = 2.0;
    this.releaseBind();
  }
  releaseBind() { if (SOV.bind) { if (SOV.bind.fx) SOV.bind.fx.kill = true; SOV.bind = null; } }
  hit(info) {
    if (this.state === 'transform' || this.hidden) return;
    if (this.phase === 3) return;       // the beast is hit through its parts
    super.hit(info);
  }
  die() {
    if (this.phase < 3) {   // she cannot die before the Root wakes
      this.hp = Math.max(1, Math.round(this.maxHp * 0.02)); this.pendingP3 = true;
      if (this.phase === 1) this.pendingPhase = true;
      return;
    }
    this.beastDie();
  }
  draw() {
    if (this.phase === 3 || (this.state === 'transform' && this.tHidden && this.spine)) return this.beastDraw();
    if (this.hidden) return;
    super.draw();
    if (this.state === 'attack' && this.atk === 'grab' && this.anim.i <= 2) addLight(this.x + this.face * 30, this.y - 70, 40, '255,220,150', 0.6);
  }
}

// ---- move helpers (phases 1-2)
function sovUntil(an, fi) { let s = -an.t; for (let i = an.i; i < fi && i < an.n; i++) s += an.ms(i); return Math.max(0.05, s / 1000 / an.speed); }
function sovMeta() { return ASSETS.sovereign_meta || {}; }
function sovPetals(b) {
  const sp = sovMeta().spawn.petals, o = metaPoint(b.sh, b, sp.at), n = b.phase === 2 ? 9 : 7;
  for (let k = 0; k < n; k++) {
    const a = (-58 + k * 76 / (n - 1)) * Math.PI / 180, v = 190 + (k % 2) * 25;
    projectiles.push({ owner: 'enemy', kind: 'sovpetal', sh: 'fx_sov_petal', x: o.x, y: o.y, vx: Math.cos(a) * b.face * v, vy: Math.sin(a) * v,
      dmg: sovDmg(30), life: 3.2, r: 4, t: 0, id: ++hazardId, sov: 'petal', turn: 0.42 + k * 0.05 });
  }
  sfx.bossSwing(); shake = Math.max(shake, 3);
}
function sovRingBurst(b, set, fl) {
  const id = ++hazardId;
  for (const [a, c] of set) for (const s of [-1, 1]) {
    const x0 = b.x + s * a, x1 = b.x + s * c, lo = Math.min(x0, x1), hi = Math.max(x0, x1);
    if (hi < TILE || lo > room.pw - TILE) continue;
    hazards.push({ x: (lo + hi) / 2, y: fl, w: hi - lo - 2, h: 44, dmg: sovDmg(44), id, life: 0.5, t: 0, update() {}, active: h => h.t > 0.04 && h.t < 0.3 });
    for (let x = lo + 14; x < hi; x += 28) spawnFx(fxOr('sov_band', 'pillar'), x, fl, 1, null, { bottom: true });
  }
  sfx.pillar(); sfx.boom(); shake = Math.max(shake, 6); flashScreen = Math.max(flashScreen, 0.15);
}
function sovRingMarks(b, set, fl, life) {
  for (const [a, c] of set) for (const s of [-1, 1]) for (let d = a + 8; d < c; d += 16) { const x = b.x + s * d; if (x > TILE && x < room.pw - TILE) sovMark(x, fl, life, 16, true); }
}
const SOV_BANDS_A = [[0, 44], [88, 132], [176, 220], [264, 308], [352, 396]];
const SOV_BANDS_B = [[44, 88], [132, 176], [220, 264], [308, 352], [396, 440]];

function sovBeamTick(b, an, kind) {
  const F = sovMeta().frames[kind], p2 = b.phase === 2, fl = b.floor;
  b.mv.rays = null;
  if (!F) return;
  const i = an.i, k = Math.min(1, an.t / Math.max(1, an.ms(i)));
  const world = deg => (b.face > 0 ? deg : 180 - deg) * Math.PI / 180;
  if (kind === 'beam') {
    const h = F[Math.min(i, F.length - 1)].hand, o = metaPoint(b.sh, b, h);
    if (i >= 2 && i <= 4) { b.mv.rays = [sovRay(o.x, o.y, world(-20), 460, fl)]; b.mv.thin = true; return; }
    if (i < 5 || i > 11) return;
    const a0 = F[i].ang, a1 = F[Math.min(11, i + 1)].ang ?? a0;
    let ang = lerp(a0, a1, i < 11 ? k : 0);
    if (p2) ang += (ang + 20) * 0.16;
    const h1 = F[Math.min(11, i + 1)].hand, hp = [lerp(h[0], h1[0], k), lerp(h[1], h1[1], k)], oo = metaPoint(b.sh, b, hp);
    b.mv.rays = [sovRay(oo.x, oo.y, world(ang), 460, fl)]; b.mv.thin = false;
  } else {
    const o = metaPoint(b.sh, b, F[Math.min(i, F.length - 1)].halo); o.y -= 3;
    const dirs = p2 ? [1, -1] : [1];
    if (i >= 2 && i <= 4) { b.mv.rays = dirs.map(s => sovRay(o.x, o.y, (s * b.face > 0 ? 64 : 116) * Math.PI / 180, 520, fl)); b.mv.thin = true; return; }
    if (i < 5 || i > 11) return;
    const ang = lerp(64, 8, Math.min(1, (i - 5 + k) / 7));
    b.mv.rays = dirs.map(s => sovRay(o.x, o.y, (s * b.face > 0 ? ang : 180 - ang) * Math.PI / 180, 520, fl)); b.mv.thin = false;
  }
  if (an.changed && an.i === 5) { sfx.fire(); sfx.boom(); shake = Math.max(shake, 5); }
  b.mv.rays.forEach((r, ri) => {
    if (Math.random() < 0.6) particles.push({ x: r.ex, y: r.ey - 2, vx: rand(-80, 80), vy: -rand(30, 140), g: 300, life: 0.5, kind: 'gold' });
    if (!b.mv['hit' + ri] && sovRayHits(r) && hurtPlayer(sovDmg(kind === 'beam' ? 50 : 48), r.ex < P.x ? 1 : -1, b.atkId * 10 + 3 + ri, { src: b })) b.mv['hit' + ri] = true;
  });
}

function makeSovereign2(x, y) {
  const meta = () => sovMeta();
  BOSS_INFO.sovereign.quote = SOV_QUOTE;
  return new SovereignBoss(x, y, {
    sheets: ['sovereign', 'sovereign_p2'], stanceMax: 520, walkSpeed: 0, prefer: 90, p2at: 0.6, p2speed: 1.22, p2tag: 'nova', critRange: 80, floating: true,
    introTag: 'nova', cool1: [0.28, 0.6], cool2: [0.15, 0.4], victory: 'SOVEREIGN RELEASED', deathParticle: 'petal',
    onIntro() { sfx.roar(); flashScreen = 0.5; },
    onPhase2() { flashScreen = 0.8; shake = 10; sfx.roar(); toast('The crown shatters. Her light turns to fire.'); },
    weights(d, p2) {
      let w;
      if (d < 90) w = { sweep: 2.0, combo: 2.4, grab: 1.5, nova: p2 ? 1.2 : 0.7, rings: 1.0, lash: 0.8, blink: 0.7, glide: 0.5 };
      else if (d > 220) w = { glide: 1.0, blink: 1.8, beam: 1.6, lance: 1.0, rain: 0.9, orbs: 1.2, spears: 1.1, crown: 1.2, petals: 1.0 };
      else w = { lash: 1.6, petals: 1.4, orbs: 1.1, beam: 1.2, crown: 1.0, spears: 0.9, summon: 1.0, rain: 0.7, lance: 0.7, combo: 0.9, blink: 1.1, rings: 0.9, glide: 0.5 };
      if (this.rangedRun >= 2) for (const k of SOV_RANGED) if (w[k]) w[k] *= 0.3;
      if (!p2) { w.crown = (w.crown || 0) * 0.6; w.rings = (w.rings || 0) * 0.7; }
      return w;
    },
    chains: {
      sweep(d) { return d < 90 ? 'combo' : 'lash'; }, combo(d) { return d < 100 ? 'grab' : 'blink'; }, lance(d) { return d < 90 ? 'sweep' : 'rain'; },
      rain: 'lance', summon: 'sweep', nova: 'glide', lash: 'petals', petals: 'orbs', cross(d) { return d < 100 ? 'combo' : 'beam'; },
      beam: 'blink', crown: 'lash', spears: 'orbs', rings: 'blink', orbs: d => d < 100 ? 'sweep' : 'lash',
    },
    moves: {
      sweep: { dmg: [44, 50], shake: 3, body: true },
      nova: { dmg: [70], shake: 10, on: { 8() { spawnFx(fxOr('sov_nova', 'roar_ring'), this.x, this.y - 70, 1); flashScreen = 0.4; sfx.boom(); } } },
      rain: { dmg: [], spawn() {
        const n = this.phase === 2 ? 9 : 6;
        for (let k = 0; k < n; k++) lightPillar(clamp(P.x + (this.phase === 2 ? (k % 2 ? 1 : -1) * Math.ceil(k / 2) * 34 : (k % 2 ? 1 : -1) * Math.ceil(k / 2) * 44 + rand(-10, 10)), this.L, this.R), this.floor, 0.1 + k * (this.phase === 2 ? 0.12 : 0.28), 46);
        sfx.charge();
      } },
      lance: { dmg: [], spawn(at) {
        const n = this.phase === 2 ? 3 : 2;
        for (let k = 0; k < n; k++) {
          const pr = { owner: 'enemy', kind: 'sovlance', x: at.x, y: at.y, vx: 0, vy: 0, dmg: sovDmg(42), life: 2.2, r: 6, t: 0, id: ++hazardId, sh: 'fx_sov_lance', delay: 0.001 + k * 0.24 };
          pr.onStart = () => { const a = Math.atan2(P.y - 14 - pr.y, P.x - pr.x); pr.vx = Math.cos(a) * 310; pr.vy = Math.sin(a) * 310; sfx.spear(); };
          projectiles.push(pr);
        }
      } },
      summon: { dmg: [], spawn() {
        const dir = P.x < this.x ? -1 : 1, n = this.phase === 2 ? 8 : 6;
        for (let k = 1; k <= n; k++) rootSpikeAt(clamp(this.x + dir * k * 30, this.L, this.R), this.floor, 0.15 + k * 0.1, 44);
        if (this.phase === 2) for (let k = 0; k < 3; k++) rootSpikeAt(clamp(P.x + rand(-30, 30), this.L, this.R), this.floor, 0.9 + k * 0.2, 44);
      } },
      lash: { dmg: [], on: { 4() {
        const dir = this.face, p2 = this.phase === 2, n = p2 ? 7 : 5;
        for (let k = 0; k < n; k++) { const x = this.x + dir * (40 + k * 40); if (x > this.L - 10 && x < this.R + 10) sovWhip(x, this.floor, 0.4 + k * (p2 ? 0.1 : 0.13), dir); }
        if (p2) for (let k = 0; k < 3; k++) { const x = this.x - dir * (40 + k * 40); if (x > this.L - 10 && x < this.R + 10) sovWhip(x, this.floor, 0.55 + k * 0.13, -dir); }
        shake = Math.max(shake, 5); sfx.boom();
      } } },
      combo: { dmg: [40, 44, 60], parry: true, step: 70, shake: 3,
        on: { 9() { const t = meta().telegraph.combo; spawnFx('telegraph', this.x + this.face * 60, this.y - 70, this.face); sfx.glint(); sfx.charge(); } },
        tick(dt, an) { if (an.i >= 11 && an.i <= 12) this.x = clamp(this.x + this.face * 240 * dt, this.L, this.R); } },
      petals: { dmg: [], on: { 4() { sovPetals(this); }, 8() { if (this.phase === 2) sovPetals(this); } } },
      grab: { dmg: [], tick(dt, an) {
        if (an.i >= 3 && an.i <= 5) this.x = clamp(this.x + this.face * 60 * dt, this.L, this.R);
        const r = meta().grab && meta().grab.rects[an.i];
        if (!r || this.mv.tried || P.state === 'dead') return;
        if (!overlap(metaRect(this.sh, this, r), playerHurtbox())) return;
        this.mv.tried = true;
        if (hurtPlayer(sovDmg(20), this.face, this.atkId * 10 + 1, { src: this })) {
          SOV.bind = { x: P.x, t: 0, boss: this, fx: spawnFx(fxOr('sov_bind', 'root_spike'), P.x, this.floor, 1, null, { bottom: true, loop: true }) };
          sfx.boom(); shake = 6; this.start('grabhold');
        }
      } },
      grabhold: { dmg: [], on: { 4() {
        if (!SOV.bind) return;
        P.inv = 0; hurtPlayer(sovDmg(62), this.face, this.atkId * 10 + 2, { src: this });
        spawnFx(fxOr('sov_burst', 'shockwave'), P.x, P.y - 14, 1); lightPillar(P.x, this.floor, 0, 0);
        flashScreen = 0.5; shake = 10; sfx.boom(); this.releaseBind();
        P.vx = this.face * 170;
      } } },
      orbs: { dmg: [], on: { 6() {
        const H = meta().spawn.orbs.halo, n = this.phase === 2 ? 5 : 3, pick = n === 5 ? [0, 1, 2, 3, 4] : [0, 2, 4];
        pick.forEach((hi, k) => {
          const q = metaPoint(this.sh, this, H[hi]), a = Math.atan2(P.y - 14 - q.y, P.x - q.x) + (k - (n - 1) / 2) * 0.35;
          projectiles.push({ owner: 'enemy', kind: 'sovorb', sh: 'fx_sov_orb', x: q.x, y: q.y, vx: Math.cos(a) * 105, vy: Math.sin(a) * 105, homing: 1.7, delay: k * 0.12,
            dmg: sovDmg(34), life: 4, r: 5, t: 0, id: ++hazardId });
        });
        sfx.spear();
      } } },
      beam: { dmg: [], tick(dt, an) { sovBeamTick(this, an, 'beam'); } },
      crown: { dmg: [], tick(dt, an) { sovBeamTick(this, an, 'crown'); } },
      spears: { dmg: [], on: { 5() {
        const fl = this.floor, xs = []; for (let x = this.L; x <= this.R; x += 44) xs.push(x);
        const off = Math.random() < 0.5 ? 0 : 1;
        xs.forEach((x, k) => sovSpear(x, fl, (k + off) % 2 ? 1.3 : 0.6));
        if (this.phase === 2) for (let k = -1; k <= 1; k++) sovSpear(clamp(P.x + k * 22, this.L, this.R), fl, 2.0);
        sfx.charge(); shake = Math.max(shake, 4);
      } } },
      vanish: { dmg: [], tick(dt, an) {
        if (!an.done) return;
        this.state = 'blinking'; this.hidden = true; this.t = this.phase === 2 ? 0.3 : 0.42;
        let tx = P.x - (P.face || 1) * 78;
        if (tx < this.L + 30 || tx > this.R - 30) tx = P.x + (P.face || 1) * 78;
        this.blinkTo = clamp(tx, this.L + 30, this.R - 30); sfx.glint();
      } },
      cross: { dmg: [58], shake: 5, step: 60 },
      rings: { dmg: [], tick(dt, an) {
        if (an.i >= 2 && !this.mv.m1) { this.mv.m1 = true; sovRingMarks(this, SOV_BANDS_A, this.floor, sovUntil(an, 6)); sfx.charge(); }
        if (an.i >= 6 && !this.mv.b1) { this.mv.b1 = true; sovRingBurst(this, SOV_BANDS_A, this.floor); an.speed = 0.5; sovRingMarks(this, SOV_BANDS_B, this.floor, sovUntil(an, 10)); }
        if (an.i >= 10 && !this.mv.b2) { this.mv.b2 = true; an.speed = this.speed; sovRingBurst(this, SOV_BANDS_B, this.floor); }
      } },
    },
    wake() { return P.x > 4 * TILE + 24; },
    ambient() {
      if (this.hidden) return;
      if (Math.random() < 0.5) particles.push({ x: this.x + rand(-80, 80), y: this.y - rand(20, 140), vx: rand(-10, 10), vy: rand(8, 20), life: 2, kind: this.phase === 2 ? 'fire' : 'petal' });
      addLight(this.x, this.y - 80, this.phase === 2 ? 150 : 120, this.phase === 2 ? '255,190,110' : '255,245,220', 0.8);
    },
  });
}

// ================================================================== phase 3: The Pale Root, Unbound
const SB = { N: 44, SEG: 8, RADII: [2, 3, 4, 5, 6, 7, 8, 10, 12, 14], HEADA: [] };
for (let i = 0; i < 17; i++) SB.HEADA.push(-90 + i * 11.25);
SB.rad = [];
for (let i = 0; i < SB.N; i++) {
  const u = i / (SB.N - 1); let r = 5.5 + 6.5 * Math.pow(Math.min(1, u / 0.32), 0.9);
  if (u > 0.45) r *= Math.pow(Math.max(0, 1 - (u - 0.45) / 0.55), 0.85);
  r = Math.max(2, r); SB.rad.push(SB.RADII.reduce((a, b) => Math.abs(b - r) < Math.abs(a - r) ? b : a));
}
const sbSheet = r => sheet('sov_seg_' + String(r).padStart(2, '0'));
function sbAngIdx(a) { let aa = (a * 180 / Math.PI) % 180; if (aa < 0) aa += 180; return Math.round(aa / 11.25) % 16; }
function sbMirror(a) {   // heading angle -> [frame index into -90..90, flip]
  let d = a * 180 / Math.PI; const flip = Math.cos(a) < 0;
  if (flip) d = 180 - d; d = ((d + 180) % 360 + 360) % 360 - 180;
  let best = 0; for (let i = 1; i < 17; i++) if (Math.abs(SB.HEADA[i] - d) < Math.abs(SB.HEADA[best] - d)) best = i;
  return [best, flip];
}

Object.assign(SovereignBoss.prototype, {
  initSpine(x, y, under) {
    this.spine = []; this.hv = { x: 0, y: 0 }; this.strands = [];
    for (let i = 0; i < SB.N; i++) {
      if (under) this.spine.push({ x: x + Math.sin(i * 0.5) * 20, y: this.floor + 30 + i * 3 });
      else this.spine.push({ x: x - this.face * i * SB.SEG * 0.85, y: y + Math.sin(i * 0.25) * 30 + i * 1.2 });
    }
    // flowing filaments: the mane (head) and a dorsal line of threads along the neck and back
    const anchors = [0, 0, 0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 20, 23];
    anchors.forEach((a, k) => { const p = this.spine[a], n = a === 0 ? 9 : 7; this.strands.push({ a, k, len: n, pts: Array.from({ length: n }, () => ({ x: p.x, y: p.y })) }); });
    this.tgt = { x: x, y: y }; this.hspd = 150; this.hacc = 3; this.wob = 0; this.dive = false; this.tailPull = null;
  },
  startTransform() {
    if (this.state === 'transform' || this.phase === 3) return;
    this.pendingP3 = false; this.pendingPhase = false; this.releaseBind();
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player'); SOV.marks = []; this.mv = {};
    this.state = 'transform'; this.tHidden = false; this.stance = 0; this.air = null; this.facePlayer();
    this.initSpine(this.x, this.floor, true); this.beastOut = 0; this.haloK = 0;
    const b = this, first = !SAVE.flags['cutp3:sovereign'], ox = this.x;
    const emerge = dur => ({ dur, tween: (dt, k) => {
      const e = 1 - Math.pow(1 - k, 2.2), H = b.spine[0];
      b.tgt = { x: ox + Math.sin(e * Math.PI * 1.6) * 70 * b.face, y: b.floor + 20 - e * 150 }; b.hspd = 260; b.hacc = 8; b.wob = 0; b.dive = k < 0.9;
      b.headSteer(dt); b.beastSim(dt, true); b.beastOut = k; b.haloK = Math.max(0, k * 1.4 - 0.6);
      if (Math.random() < 0.9) particles.push({ x: ox + rand(-30, 30), y: b.floor - 2, vx: rand(-90, 90), vy: -rand(60, 200), g: 300, life: 0.8, kind: Math.random() < 0.5 ? 'gold' : 'rock' });
      shake = Math.max(shake, 3);
      const t = camTargetFor(ox, Math.min(H.y, b.floor - 60)); cam.x = lerp(cam.x, t.x, Math.min(1, dt * 4)); cam.y = lerp(cam.y, t.y, Math.min(1, dt * 3));
    } });
    const hover = dur => ({ dur, tween: dt => { b.tgt = { x: b.spine[0].x, y: b.floor - 120 }; b.wob = 8; b.headSteer(dt); b.beastSim(dt); const t = camTargetFor(b.spine[0].x, b.floor - 80); cam.x = lerp(cam.x, t.x, Math.min(1, dt * 3)); } });
    const unmake = dur => ({ dur, tween: (dt, k) => {
      b.anim.speed = 1.2;
      if (Math.random() < 0.9) particles.push({ x: b.x + rand(-50, 50), y: b.y - rand(10, 130), vx: rand(-20, 20), vy: -rand(30, 90), life: rand(0.8, 1.6), kind: Math.random() < 0.6 ? 'petal' : 'gold' });
      shake = Math.max(shake, 2);
    } });
    const wake = act(() => {
      flashScreen = 1; shake = 14; sfx.boom(); sfx.roar(); sovSetVoid(true); b.tHidden = true;
      spawnFx(fxOr('sov_burst', 'roar_ring'), ox, b.floor - 60, 1);
      for (let i = 0; i < 40; i++) particles.push({ x: ox + rand(-20, 20), y: b.floor - rand(0, 100), vx: rand(-150, 150), vy: -rand(20, 200), g: 120, life: rand(0.8, 1.8), kind: 'gold' });
    });
    const roar = act(() => {
      const H = b.spine[0]; sfx.roar(); shake = 14; flashScreen = 0.5; b.haloK = 1; b.mouthOpen = true;
      spawnFx('roar_ring', H.x, H.y, 1); spawnFx(fxOr('sov_burst', 'roar_ring'), b.haloPos().x, b.haloPos().y, 1);
    });
    const steps = first ? [
      { pan: { x: b.x, y: b.y - 70 }, dur: 0.7 },
      act(() => { b.setS('transform', 'death', false); b.anim.speed = 0.55; }),
      { dur: 2.6, say: ['The Pale Sovereign', 'Enough. You want the Root? Then meet it — as it was, before I wore it.'], tween: () => { if (b.anim.i >= 6) b.anim.speed = 0; } },
      unmake(1.2), wake, emerge(2.5), roar, hover(1.0), act(() => { b.mouthOpen = false; }),
      { pan: { x: P.x, y: P.y - 30 }, dur: 0.6 },
    ] : [
      { pan: { x: b.x, y: b.y - 70 }, dur: 0.4 }, act(() => { b.setS('transform', 'death', false); b.anim.i = 6; b.anim.speed = 1.6; }),
      unmake(0.7), wake, emerge(1.6), roar, hover(0.4), act(() => { b.mouthOpen = false; }),
      { pan: { x: P.x, y: P.y - 30 }, dur: 0.5 },
    ];
    playCutscene(steps, () => b.finalizeP3());
  },
  finalizeP3() {
    if (this.phase === 3) return;
    this.phase = 3; this.state = 'beast'; this.tHidden = true; this.hidden = true; this.active = true; sovSetVoid(true);
    this.name = 'The Pale Root, Unbound';
    this.maxHp = Math.round(SOV_BEAST_HP * NGP.hp); this.hp = this.maxHp; this.displayHp = 0; this.dmgT = 0; this.dmgShown = 0;
    this.stanceBase = this.stanceMax = 600; this.stance = 0; this.stanceImmune = 0; this.speed = 1; this.bleed = 0; this.rotT = 0;
    if (!this.spine || this.beastOut < 0.95) this.initSpine(this.x, this.floor - 110, false);
    this.haloK = 1; this.mouthOpen = false; this.parts = this.makeParts();
    this.bs = 'swim'; this.bt = 0; this.cool = 1.0; this.swimSide = P.x < this.spine[0].x ? 1 : -1; this.lastB = null; this.starsCd = 3; this.wellCd = 6;
    this.rays = null; this.critDone = true;
    SAVE.flags['cutp3:sovereign'] = 1; BOSS_INFO.sovereign.quote = SOV_QUOTE3; bossBanner = { name: this.name, t: 0 };
    this.anim = new Anim(this.sheetFor('death'), 'death', false); this.anim.i = this.anim.n - 1;
  },
  makeParts() {
    const B = this, alive = () => B.alive && B.active && B.phase === 3 && B.bs !== 'intro';
    const head = { name: 'head', boss: true, critRange: 70, x: 0, y: 0, face: 1, get alive() { return alive(); },
      hurtbox() { return B.headRect(); }, hit(info) { B.partHit(info, 1.25, 1.15); },
      critable() { return B.critable(); }, onCritStart() { B.onCritStart(); }, onParried() { B.onParried(); } };
    const parts = [head];
    for (const [a, c] of [[3, 9], [10, 16], [17, 23], [24, 31], [32, 40]])
      parts.push({ name: 'body', boss: true, critRange: 0, x: 0, y: 0, face: 1, get alive() { return alive(); },
        hurtbox() { return B.segRect(a, c); }, hit(info) { B.partHit(info, 0.75, 0.8); }, critable() { return false; }, onParried() {} });
    return parts;
  },
  headC() { const H = this.spine[0], S1 = this.spine[1], a = Math.atan2(H.y - S1.y, H.x - S1.x); return { x: H.x + Math.cos(a) * 12, y: H.y + Math.sin(a) * 12, a }; },
  headRect() { if (!this.spine || this.state === 'dead') return null; const c = this.headC(); if (c.y > this.floor + 4) return null; return rect(c.x - 15, c.y - 12, c.x + 15, c.y + 12); },
  segRect(a, c) {
    if (!this.spine || this.state === 'dead') return null;
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (let i = a; i <= c; i++) { const p = this.spine[i], r = SB.rad[i] * 0.8; if (p.y - r > this.floor) continue; x0 = Math.min(x0, p.x - r); x1 = Math.max(x1, p.x + r); y0 = Math.min(y0, p.y - r); y1 = Math.max(y1, Math.min(this.floor, p.y + r)); }
    return x1 > x0 ? rect(x0, y0, x1, y1) : null;
  },
  haloPos() { const p = this.spine[5] || this.spine[0]; return { x: p.x, y: p.y - 20 }; },
  partHit(info, m, pm) {
    if (!this.alive || this.phase !== 3) return;
    BossBase.prototype.hit.call(this, { ...info, dmg: info.dmg * m, poise: (info.poise || 0) * pm });
    for (let i = 0; i < 4; i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 90), vy: -rand(20, 90), g: 200, life: 0.5, kind: 'gold' });
  },
  headSteer(dt) {
    const H = this.spine[0];
    let tx = this.tgt.x, ty = this.tgt.y;
    if (this.wob) { tx += Math.sin(time * 2.1) * this.wob; ty += Math.cos(time * 2.7) * this.wob * 0.6; }
    const dx = tx - H.x, dy = ty - H.y, dist = Math.hypot(dx, dy) || 1, want = Math.min(this.hspd, dist * 3.2);
    const k = Math.min(1, dt * this.hacc);
    this.hv.x = lerp(this.hv.x, dx / dist * want, k); this.hv.y = lerp(this.hv.y, dy / dist * want, k);
    H.x += this.hv.x * dt; H.y += this.hv.y * dt;
    H.x = clamp(H.x, -120, room.pw + 120); H.y = Math.max(-160, H.y);
    if (!this.dive && H.y > this.floor - 12) H.y = this.floor - 12;
  },
  beastSim(dt, emerging = false) {
    const S = this.spine, N = S.length, fl = this.floor, tp = this.tailPull;
    for (let i = 1; i < N; i++) {
      const b = S[i], u = i / N;
      b.x += Math.sin(time * 1.6 - i * 0.33) * dt * 16 * u; b.y += Math.cos(time * 1.25 - i * 0.29) * dt * 11 * u;
      if (tp && u > 0.5) { const w = Math.pow((u - 0.5) / 0.5, 1.6), k = Math.min(1, dt * tp.k) * w; b.x += (tp.x - b.x) * k; b.y += (tp.y - b.y) * k; }
      if (i < N - 1) { const a = S[i - 1], c = S[i + 1]; b.x = lerp(b.x, (a.x + c.x) / 2, 0.06); b.y = lerp(b.y, (a.y + c.y) / 2, 0.06); }
    }
    for (let i = 1; i < N; i++) {
      const a = S[i - 1], b = S[i], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
      b.x = a.x + dx / d * SB.SEG; b.y = a.y + dy / d * SB.SEG;
      if (!this.dive && !emerging && b.y > fl - SB.rad[i] * 0.7) b.y = lerp(b.y, fl - SB.rad[i] * 0.7, Math.min(1, dt * 10));
    }
    // filaments: follow-the-leader threads streaming behind their anchors
    for (const s of this.strands) {
      const A = S[s.a], B2 = S[Math.min(N - 1, s.a + 1)], ang = Math.atan2(A.y - B2.y, A.x - B2.x);
      const up = Math.cos(ang) >= 0 ? -1 : 1, nx = -Math.sin(ang) * up, ny = Math.cos(ang) * up;
      const off = s.a === 0 ? -2 + (s.k - 1) * 3 : SB.rad[s.a] * 0.8;
      let px = A.x + nx * off - Math.cos(ang) * (s.a === 0 ? 4 : 0), py = A.y + ny * off;
      for (let j = 0; j < s.pts.length; j++) {
        const q = s.pts[j];
        q.y += (Math.sin(time * 3 + j * 0.8 + s.k) * 6 + 4) * dt; q.x += Math.cos(time * 2.2 + j + s.k) * 5 * dt;
        const dx = q.x - px, dy = q.y - py, d = Math.hypot(dx, dy) || 1, L = s.a === 0 ? 5 : 4.5;
        if (d > L) { q.x = px + dx / d * L; q.y = py + dy / d * L; }
        px = q.x; py = q.y;
      }
    }
  },
});

// ---- beast AI
const SB_CHAIN = { beam: 'bite', dive: 'rings', tail: 'bite', rings: 'tail', halo: 'beam', well: 'bite', starfall: 'tail', bite: 'tail' };
Object.assign(SovereignBoss.prototype, {
  go(bs) { this.bs = bs; this.bt = 0; },
  pickBeast() {
    const H = this.spine[0], d = Math.abs(P.x - H.x);
    const w = { bite: d < 170 ? 2.4 : 0.8, beam: 1.4, stars: this.starsCd <= 0 ? 1.1 : 0, starfall: 1.0, rings: 1.2, halo: 0.9, tail: 1.3, dive: 1.1, well: this.wellCd <= 0 ? 0.9 : 0 };
    if (w[this.lastB]) w[this.lastB] *= 0.2;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((a, [, v]) => a + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return 'bite';
  },
  beastStart(m) {
    this.dbl = Math.random() < 0.5;
    this.lastB = m; this.atkId = ++hazardId; this.hitOnce = {}; this.mouthOpen = false; this.rays = null; this.chainN = this.chainN || 0;
    this.go(m + '0');
  },
  toSwim(cool, noChain) {
    const p3b = this.hp < this.maxHp * 0.5, nx = SB_CHAIN[this.lastB];
    if (!noChain && nx && this.state === 'beast' && P.state !== 'dead' && this.chainN < (p3b ? 2 : 1) && Math.random() < (p3b ? 0.6 : 0.45)) {
      this.chainN++; this.tailPull = null; this.dive = false; this.rays = null; this.beastStart(nx); return;
    }
    this.go('swim'); this.cool = cool ?? (p3b ? rand(0.2, 0.45) : rand(0.35, 0.7)); this.tailPull = null; this.dive = false; this.mouthOpen = false; this.rays = null; this.hspd = 140; this.hacc = 3; this.chainN = 0; if (Math.random() < 0.35) this.swimSide *= -1; },
  beastStagger() {
    this.critDone = false; this.stanceImmune = 7; this.staggers = (this.staggers || 0) + 1;
    this.stanceMax = Math.min(this.stanceMax * 1.15, (this.stanceBase || (this.stanceBase = this.stanceMax)) * 2);
    this.stance = 0; this.state = 'stagger'; this.t = 2.4; this.go('stagger'); this.dive = false; this.tailPull = null; this.rays = null; this.mouthOpen = true;
    SOV.well = null; const H = this.spine[0];
    this.tgt = { x: clamp(H.x, this.L, this.R), y: this.floor - 10 }; this.hspd = 300; this.hacc = 8; this.wob = 0;
    sfx.glint(); sfx.roar(); spawnFx(fxOr('parry_flash', 'parry_spark'), H.x, H.y, 1); shake = 8;
  },
  critable() {
    if (this.phase !== 3) return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone;
    return this.state === 'stagger' && !this.critDone && this.spine && this.headC().y > this.floor - 30;
  },
  canStagger() {
    if (this.phase === 3) return this.state !== 'dead' && !this.dive && this.bs !== 'intro';
    return !this.hidden && this.state !== 'transform' && !(this.state === 'attack' && ['nova', 'rings', 'crown', 'vanish', 'grabhold'].includes(this.atk));
  },
  bodyHits(dmg, minI = 0) {   // contact damage from body pieces (tail sweep, dive)
    const hb = playerHurtbox();
    for (let i = minI; i < SB.N; i++) {
      const p = this.spine[i], r = SB.rad[i] + 2;
      if (p.y - r > this.floor) continue;
      if (overlap(rect(p.x - r, p.y - r, p.x + r, p.y + r), hb)) return hurtPlayer(sovDmgB(dmg), P.x < p.x ? -1 : 1, this.atkId, { src: this });
    }
    return false;
  },
  p3update(dt) {
    if (this.state === 'transform') { this.commonUpdate(dt); this.anim.update(dt); return; }
    this.commonUpdate(dt);
    const S = this.spine, H = S[0], fl = this.floor, p3b = this.hp < this.maxHp * 0.5, sp = p3b ? 1.15 : 1;
    this.bt += dt; this.starsCd -= dt; this.wellCd -= dt;
    if (this.state === 'dead') { this.deathUpdate(dt); this.headSteer(dt); this.beastSim(dt); this.updateParts(); return; }
    const dirP = P.x < H.x ? -1 : 1, t = this.bt;
    this.wob = 0;
    switch (this.bs) {
      case 'swim':
        this.tgt = { x: clamp(P.x + this.swimSide * 95, this.L, this.R), y: fl - 64 + Math.sin(time * 1.4) * 18 }; this.wob = 10; this.hspd = 140 * sp; this.hacc = 3;
        this.cool -= dt;
        if (p3b && (this.harass = (this.harass ?? 2.5) - dt) <= 0) {   // enraged: a lone homing star while it circles
          this.harass = 2.5; const hp = this.haloPos();
          projectiles.push({ owner: 'enemy', kind: 'sovstar', sh: 'fx_sov_star', x: hp.x, y: hp.y - 44, vx: 0, vy: -60, homing: 1.4, dmg: sovDmgB(26), life: 4.5, r: 4, t: 0, id: ++hazardId }); sfx.spear();
        }
        if (this.cool <= 0 && P.state !== 'dead') this.beastStart(this.pickBeast());
        break;
      case 'stagger':
        this.t -= dt; this.hspd = 300;
        if (this.t <= 0) { this.state = 'beast'; this.mouthOpen = false; this.toSwim(0.4, true); }
        break;
      // -- bite: pull back, lunge at where you stand, then linger low (punish)
      case 'bite0':
        this.tgt = { x: clamp(P.x - dirP * 110, this.L - 30, this.R + 30), y: fl - 95 }; this.hspd = 240; this.hacc = 5;
        if (t > 0.22) this.mouthOpen = true;
        if (t > 0.3 && !this.hitOnce.g) { this.hitOnce.g = 1; spawnFx('telegraph', H.x, H.y, 1); sfx.glint(); }
        if (t > (p3b ? 0.46 : 0.56)) { this.lunge = { x: P.x + dirP * 18, y: fl - 12 }; this.go('bite1'); sfx.bossSwing(); }
        break;
      case 'bite1':
        this.tgt = this.lunge; this.hspd = 640; this.hacc = 14;
        if (!this.hitOnce.b && this.headRect() && overlap(this.headRect(), playerHurtbox()) && hurtPlayer(sovDmgB(54), dirP, this.atkId, { parryable: true, src: this })) this.hitOnce.b = 1;
        if (t > 0.45 || Math.hypot(H.x - this.lunge.x, H.y - this.lunge.y) < 10) { this.go('bite2'); shake = Math.max(shake, 5); sfx.boom(); spawnFx('shockwave', H.x, fl, 1); }
        break;
      case 'bite2':
        this.tgt = { x: H.x, y: fl - 16 }; this.hspd = 60; this.hacc = 3;
        if (t > 0.2) this.mouthOpen = false;
        if ((p3b ? this.chainN < 2 : this.chainN < 1 && this.dbl) && t > 0.35) { this.chainN++; this.atkId = ++hazardId; this.hitOnce = {}; this.go('bite0'); this.bt = 0.25; }
        else if (t > 0.7) this.toSwim();
        break;
      // -- sword of light: a golden beam that sweeps the floor from beyond you back toward the beast
      case 'beam0': {
        const side = H.x < P.x ? -1 : 1; this.beamSide = side;
        this.tgt = { x: clamp(P.x + side * 150, this.L - 20, this.R + 20), y: fl - 150 }; this.hspd = 280; this.hacc = 5;
        if (t > 0.8) { this.go('beam1'); this.mouthOpen = true; sfx.charge(); }
        break;
      }
      case 'beam1': {
        this.tgt = { x: H.x, y: H.y }; this.hspd = 40;
        const side = this.beamSide, m = this.headC();
        if (!this.beamXs || t < dt * 1.5) { this.beamXs = clamp(P.x - side * 80, TILE, room.pw - TILE); this.beamXe = H.x - side * 34; }
        for (let i = 0; i < 2; i++) { const a = rand(0, 6.28); particles.push({ x: m.x + Math.cos(a) * 30, y: m.y + Math.sin(a) * 30, vx: -Math.cos(a) * 60, vy: -Math.sin(a) * 60, life: 0.5, kind: 'gold' }); }
        const r = sovRay(m.x, m.y, Math.atan2(fl - m.y, this.beamXs - m.x), 700, fl); this.rays = [r]; this.raysThin = true;
        if (t > 0.5 && !this.hitOnce.g) { this.hitOnce.g = 1; spawnFx('telegraph', m.x, m.y, 1); sfx.glint(); }
        if (t > (p3b ? 0.75 : 0.95)) { this.go('beam2'); sfx.fire(); sfx.boom(); shake = 6; }
        break;
      }
      case 'beam2': {
        const T = p3b ? 0.85 : 1.05, k = Math.min(1, t / T), e = k * k * (3 - 2 * k), m = this.headC();
        const cx = lerp(this.beamXs, this.beamXe, e), r = sovRay(m.x, m.y, Math.atan2(fl - m.y, cx - m.x), 700, fl);
        this.rays = [r]; this.raysThin = false; shake = Math.max(shake, 2);
        if (Math.random() < 0.8) particles.push({ x: r.ex, y: fl - 2, vx: rand(-90, 90), vy: -rand(40, 160), g: 300, life: 0.6, kind: 'gold' });
        const tk = 'b' + Math.floor(t / 0.4);   // the sword of light lingers: it can catch you again every 0.4 s
        if (!this.hitOnce[tk] && sovRayHits(r, 8) && hurtPlayer(sovDmgB(this.hitOnce.any ? 34 : 56), r.ex < P.x ? 1 : -1, this.atkId * 10 + Math.floor(t / 0.4), { src: this })) { this.hitOnce[tk] = 1; this.hitOnce.any = 1; }
        if (k >= 1) { this.rays = null; this.beamXs = null; this.go('beam3'); this.mouthOpen = false; }
        break;
      }
      case 'beam3':
        this.tgt = { x: H.x, y: fl - 36 }; this.hspd = 120;
        if (t > 0.65) this.toSwim();
        break;
      // -- pale stars: slow homing stars loosed from the halo while the beast keeps fighting
      case 'stars0': {
        this.tgt = { x: clamp(P.x - dirP * 60, this.L, this.R), y: fl - 140 }; this.hspd = 220;
        const hp = this.haloPos();
        for (let i = 0; i < 2; i++) { const a = rand(0, 6.28); particles.push({ x: hp.x + Math.cos(a) * 60, y: hp.y + Math.sin(a) * 60, vx: -Math.cos(a) * 70, vy: -Math.sin(a) * 70, life: 0.8, kind: 'gold' }); }
        if (t < dt * 1.5) sfx.charge();
        if (t > 0.9) {
          const n = p3b ? 10 : 7;
          for (let k = 0; k < n; k++) {
            const a = -Math.PI / 2 + (k - (n - 1) / 2) * (Math.PI * 1.4 / n);
            projectiles.push({ owner: 'enemy', kind: 'sovstar', sh: 'fx_sov_star', x: hp.x + Math.cos(a) * 44, y: hp.y + Math.sin(a) * 44, vx: Math.cos(a) * 70, vy: Math.sin(a) * 70,
              homing: 1.25, delay: k * 0.12, dmg: sovDmgB(30), life: 5.5, r: 4, t: 0, id: ++hazardId });
          }
          sfx.spear(); flashScreen = 0.2; this.starsCd = 9; this.toSwim(0.5, true);
        }
        break;
      }
      // -- starfall: meteors rain onto marked ground in waves
      case 'starfall0': {
        this.tgt = { x: clamp(P.x, this.L, this.R), y: fl - 160 }; this.hspd = 240;
        if (t > 0.3 && !this.hitOnce.r) { this.hitOnce.r = 1; sfx.roar(); shake = 6; this.mouthOpen = true; }
        const waves = p3b ? 4 : 3, gap = p3b ? 0.5 : 0.6;
        for (let wv = 0; wv < waves; wv++) if (t > 0.6 + wv * gap && !this.hitOnce['w' + wv]) {
          this.hitOnce['w' + wv] = 1;
          const xs = [P.x, P.x + rand(40, 70), P.x - rand(40, 70), rand(this.L, this.R), rand(this.L, this.R)];
          for (const x of xs) SOV.meteors.push({ x: clamp(x, this.L, this.R), t: 0, delay: 0.85, id: ++hazardId });
          sfx.charge();
        }
        if (t > 0.6 + waves * gap + 0.9) { this.mouthOpen = false; this.toSwim(0.5); }
        break;
      }
      // -- ring waves: the beast strikes the ground; rings of light roll outward (jump them)
      case 'rings0': {
        if (t < dt * 1.5) this.ringX = clamp(H.x + (P.x - H.x) * 0.35, this.L, this.R);
        this.tgt = { x: this.ringX, y: fl - 12 }; this.hspd = 320; this.hacc = 7;
        if (t > 0.35 && !this.hitOnce.g) { this.hitOnce.g = 1; spawnFx('telegraph', H.x, H.y, 1); sfx.glint(); }
        if (t > 0.8) { this.go('rings1'); shake = 10; sfx.boom(); spawnFx('shockwave', this.ringX, fl, 1); spawnFx(fxOr('sov_beamend', 'hit'), this.ringX, fl - 8, 1); }
        break;
      }
      case 'rings1': {
        this.tgt = { x: this.ringX, y: fl - 14 }; this.hspd = 60;
        const sched = p3b ? [0, 0.45, 0.8, 1.25] : [0, 0.55, 1.0];
        sched.forEach((s, k) => { if (t >= s && !this.hitOnce['r' + k]) { this.hitOnce['r' + k] = 1; for (const d of [-1, 1]) hazards.push({ x: this.ringX, y: fl, w: 12, h: 24, vx: d * 175, dir: d, dmg: sovDmgB(40), id: ++hazardId, life: 4.5, sovWave: true, update(h, dt) { h.x += h.vx * dt; if (h.x < TILE || h.x > room.pw - TILE) h.life = 0; if (Math.random() < 0.5) particles.push({ x: h.x, y: h.y - rand(0, 20), vx: -h.vx * 0.1, vy: -rand(10, 50), life: 0.4, kind: 'gold' }); } }); sfx.pillar(); shake = Math.max(shake, 4); } });
        if (t > sched[sched.length - 1] + 0.6) this.toSwim();
        break;
      }
      // -- ring of light: the halo casts a vast expanding circle (roll through it)
      case 'halo0': {
        this.tgt = { x: clamp(P.x - dirP * 90, this.L, this.R), y: fl - 110 }; this.hspd = 220;
        if (t < dt * 1.5) sfx.charge();
        if (t > 0.6 && !this.hitOnce.g) { this.hitOnce.g = 1; const hp = this.haloPos(); spawnFx('telegraph', hp.x, hp.y - 44, 1); sfx.glint(); }
        const n = p3b ? 2 : 1;
        for (let k = 0; k < n; k++) if (t > 1.1 + k * 0.55 && !this.hitOnce['h' + k]) { this.hitOnce['h' + k] = 1; const hp = this.haloPos(); SOV.rings.push({ x: hp.x, y: hp.y, r: 40, v: 230, id: ++hazardId }); sfx.boom(); flashScreen = 0.25; shake = 6; }
        if (t > 1.1 + n * 0.55 + 0.25) this.toSwim();
        break;
      }
      // -- tail sweep: the tail rises on the far side and scythes along the floor (jump it)
      case 'tail0': {
        const side = this.tailSide || (this.tailSide = (H.x < P.x ? -1 : 1));
        this.tgt = { x: clamp(P.x + side * 120, this.L - 40, this.R + 40), y: fl - 150 }; this.hspd = 260;
        this.tailPull = { x: P.x - side * 170, y: fl - 110, k: 4 };
        if (t > 0.75 && !this.hitOnce.g) { this.hitOnce.g = 1; const tt = S[SB.N - 1]; spawnFx('telegraph', tt.x, tt.y, 1); sfx.glint(); }
        if (t > 1.0) { this.tailX0 = P.x; this.go('tail1'); sfx.bossSwing(); }
        break;
      }
      case 'tail1': {
        const side = this.tailSide, k = Math.min(1, t / (p3b ? 0.6 : 0.7));
        this.tailPull = { x: lerp(this.tailX0 - side * 170, this.tailX0 + side * 190, k), y: fl - 6, k: 12 };
        if (!this.hitOnce.b && this.bodyHits(48, Math.floor(SB.N * 0.55))) this.hitOnce.b = 1;
        if (Math.random() < 0.8) { const q = S[SB.N - 3]; if (q.y > fl - 20) particles.push({ x: q.x, y: fl - 2, vx: rand(-60, 60), vy: -rand(30, 120), g: 300, life: 0.5, kind: 'gold' }); }
        if (k >= 1) { this.go('tail2'); this.tailSide = null; }
        break;
      }
      case 'tail2':
        this.tailPull = t < 0.3 ? this.tailPull : null;
        this.tgt = { x: H.x, y: fl - 50 }; this.hspd = 120;
        if (t > 0.45) this.toSwim();
        break;
      // -- dive: rises out of sight, marks the ground, plunges through the floor and bursts out elsewhere
      case 'dive0':
        this.tgt = { x: clamp(P.x - dirP * 60, this.L, this.R), y: -110 }; this.hspd = 360; this.hacc = 4;
        if (t > 0.75) { this.go('dive1'); sfx.roar(); }
        break;
      case 'dive1': {
        if (t < 0.45) { this.diveX = clamp(P.x, this.L, this.R); }
        else if (!this.hitOnce.m) {
          this.hitOnce.m = 1; let dir = Math.random() < 0.5 ? -1 : 1, xe = this.diveX + dir * 200;
          if (xe < this.L + 20 || xe > this.R - 20) { dir = -dir; xe = this.diveX + dir * 200; }
          this.emergeX = clamp(xe, this.L + 20, this.R - 20);
          const rest = (p3b ? 0.7 : 0.9) - 0.45;
          sovMark(this.diveX, fl, rest + 0.35, 44, true); sovMark(this.emergeX, fl, rest + 0.9, 40, false); sfx.charge();
        }
        this.tgt = { x: this.diveX, y: -100 }; this.hspd = 300;
        if (t > (p3b ? 0.7 : 0.9)) { this.go('dive2'); this.dive = true; sfx.bossSwing(); }
        break;
      }
      case 'dive2':
        this.tgt = { x: this.diveX, y: fl + 80 }; this.hspd = 560; this.hacc = 14;
        if (!this.hitOnce.b && this.bodyHits(52)) this.hitOnce.b = 1;
        if (H.y > fl && !this.hitOnce.p) { this.hitOnce.p = 1; shake = 12; sfx.boom(); sfx.crumble(); spawnFx(fxOr('sov_burst', 'shockwave'), this.diveX, fl - 30, 1); spawnFx('shockwave', this.diveX, fl, 1); for (let i = 0; i < 30; i++) particles.push({ x: this.diveX + rand(-20, 20), y: fl - 2, vx: rand(-160, 160), vy: -rand(60, 240), g: 460, life: rand(0.5, 1), kind: i % 2 ? 'rock' : 'gold' }); }
        if (H.y > fl + 50) this.go('dive3');
        break;
      case 'dive3':
        this.tgt = { x: this.emergeX, y: fl + 60 }; this.hspd = 460;
        if (!this.hitOnce.b && this.bodyHits(52)) this.hitOnce.b = 1;
        if (Math.random() < 0.5) particles.push({ x: H.x + rand(-10, 10), y: fl - 1, vx: rand(-40, 40), vy: -rand(20, 80), g: 300, life: 0.4, kind: 'rock' });
        if (Math.abs(H.x - this.emergeX) < 16) this.go('dive4');
        break;
      case 'dive4': {
        this.tgt = { x: this.emergeX + (this.emergeX < P.x ? 30 : -30), y: fl - 140 }; this.hspd = 520;
        if (!this.hitOnce.b && this.bodyHits(52)) this.hitOnce.b = 1;
        if (H.y < fl && !this.hitOnce.e) { this.hitOnce.e = 1; shake = 12; sfx.boom(); sfx.roar(); spawnFx(fxOr('sov_burst', 'shockwave'), this.emergeX, fl - 30, 1); spawnFx('shockwave', this.emergeX, fl, 1); for (let i = 0; i < 30; i++) particles.push({ x: this.emergeX + rand(-20, 20), y: fl - 2, vx: rand(-160, 160), vy: -rand(60, 240), g: 460, life: rand(0.5, 1), kind: i % 2 ? 'rock' : 'gold' }); }
        if (H.y < fl - 110) this.go('dive5');
        break;
      }
      case 'dive5':
        this.tgt = { x: H.x, y: fl - 70 }; this.hspd = 150;
        if (!this.hitOnce.b && this.bodyHits(52)) this.hitOnce.b = 1;
        if (S[SB.N - 1].y < fl - 4 || t > 1.4) this.toSwim(p3b ? 0.3 : 0.6);
        break;
      // -- gravity well: a black star drags you in, then bursts
      case 'well0': {
        this.tgt = { x: clamp(P.x - dirP * 100, this.L, this.R), y: fl - 120 }; this.hspd = 220;
        if (t > 0.6) { SOV.well = { x: clamp(P.x + rand(-30, 30), this.L + 40, this.R - 40), y: fl - 62, t: 0, grow: 0, st: 'pull', id: ++hazardId }; this.go('well1'); sfx.charge(); sfx.roar(); }
        break;
      }
      case 'well1': {
        const w = SOV.well; if (!w) { this.toSwim(); break; }
        w.grow = Math.min(1, w.grow + dt * 2);
        this.tgt = { x: w.x + Math.cos(t * 1.8) * 110, y: w.y - 30 + Math.sin(t * 1.8) * 40 }; this.hspd = 200;
        if (t > (p3b ? 3.0 : 2.6)) { w.st = 'collapse'; w.ct = 0; this.go('well2'); sfx.glint(); }
        break;
      }
      case 'well2': {
        const w = SOV.well; if (!w) { this.toSwim(); break; }
        w.ct = t;
        if (t > 0.7) {
          const d = Math.hypot(P.x - w.x, P.y - 12 - w.y);
          if (d < 84) hurtPlayer(sovDmgB(64), P.x < w.x ? -1 : 1, w.id, { src: this });
          spawnFx(fxOr('sov_burst', 'shockwave'), w.x, w.y, 1); shake = 12; flashScreen = 0.5; sfx.boom();
          for (let i = 0; i < 40; i++) { const a = rand(0, 6.28); particles.push({ x: w.x, y: w.y, vx: Math.cos(a) * rand(80, 220), vy: Math.sin(a) * rand(80, 220), life: 0.7, kind: 'gold' }); }
          SOV.well = null; this.wellCd = 11; this.go('well3');
        }
        break;
      }
      case 'well3':
        this.tgt = { x: H.x, y: fl - 30 }; this.hspd = 110;
        if (t > 0.75) this.toSwim();
        break;
      default: this.toSwim();
    }
    this.headSteer(dt); this.beastSim(dt); this.updateParts();
    const c = this.headC();
    this.x = c.x; this.y = Math.min(fl, c.y); this.face = Math.cos(c.a) < 0 ? -1 : 1;
    this.camX = clamp(lerp(P.x, c.x, 0.4), P.x - 150, P.x + 150);
    this.beastAmbient();
  },
  updateParts() {
    if (!this.parts) return;
    for (const p of this.parts) {
      const r = p.hurtbox(); if (!r) continue;
      p.x = (r.x0 + r.x1) / 2; p.y = p.name === 'head' ? (this.state === 'stagger' ? this.floor : r.y1) : r.y1; p.face = this.face;
    }
  },
  beastAmbient() {
    const hp = this.haloPos(), c = this.headC();
    addLight(hp.x, hp.y, 110 * (this.haloK || 0), '255,235,190', 0.9);
    addLight(c.x, c.y, this.mouthOpen ? 70 : 44, '255,225,160', 0.9);
    for (let i = 8; i < SB.N; i += 9) addLight(this.spine[i].x, this.spine[i].y, 40, '200,180,255', 0.5);
    if (Math.random() < 0.5) { const i = irand(0, SB.N - 1), p = this.spine[i]; particles.push({ x: p.x + rand(-6, 6), y: p.y + rand(-6, 6), vx: rand(-8, 8), vy: -rand(5, 20), life: rand(0.8, 1.6), kind: 'mote' }); }
  },
  beastDie() {
    this.state = 'dead'; this.bs = 'death'; this.bt = 0; this.dive = false; this.tailPull = null; this.rays = null; this.mouthOpen = true;
    SOV.well = null; SOV.rings = []; SOV.meteors = []; SOV.marks = []; this.releaseBind();
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 14; hitstop = 0.35; slowmo = 2.0; flashScreen = 0.8; sfx.roar(); sfx.felled();
    this.deathK = 0; this.restored = false;
    victoryBanner = { text: 'THE ROOT FALLS SILENT', t: 0, ending: true };
    this.rewards();
  },
  deathUpdate(dt) {
    const H = this.spine[0];
    this.deathK = Math.min(1, this.deathK + dt / 3.4);
    this.tgt = { x: H.x + Math.sin(time * 3) * 20, y: this.floor - 120 }; this.hspd = 60; this.wob = 14;
    this.haloK = Math.max(0, 1 - this.deathK * 1.6);
    const cut = Math.floor(SB.N * (1 - this.deathK));
    for (let k = 0; k < 3; k++) { const p = this.spine[Math.min(SB.N - 1, cut + k)]; particles.push({ x: p.x + rand(-10, 10), y: p.y + rand(-10, 10), vx: rand(-40, 40), vy: -rand(20, 90), life: rand(0.8, 1.8), kind: Math.random() < 0.5 ? 'gold' : 'petal' }); }
    if (this.deathK > 0.8 && !this.restored) { this.restored = true; flashScreen = 1; sfx.kindle && sfx.kindle(); sovSetVoid(false); }
  },
  beastDraw() {
    const S = this.spine; if (!S) return;
    const N = S.length, fl = this.floor, dead = this.state === 'dead';
    const cut = dead ? Math.floor(N * (1 - this.deathK)) : N;
    if (cut <= 1) return;
    g.save(); g.beginPath(); g.rect(-400, -600, room.pw + 800, fl + 601); g.clip();
    const opt = this.flash > 0 ? { flash: this.flash * 0.6 } : this.state === 'stagger' ? { flash: 0.12 + 0.08 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    // halo
    const hs = sheet('sov_halo');
    if (hs.ok && this.haloK > 0.01) { const hp = this.haloPos(), t = hs.tag('loop'); drawSprite(hs, t.from + Math.floor(time * (this.bs === 'halo0' ? 22 : 9)) % (t.to - t.from + 1), hp.x, hp.y, 1, { center: true, alpha: Math.min(1, this.haloK) }); }
    // dorsal fin (behind the body)
    const fs = sheet('sov_fin');
    if (fs.ok && cut > 10) { const i = 8, a = Math.atan2(S[i - 1].y - S[i].y, S[i - 1].x - S[i].x), [fi, flip] = sbMirror(a), tg = fs.tag(Math.floor(time * 2.5) % 2 ? 'f1' : 'f0'); drawSprite(fs, tg.from + fi, S[i].x, S[i].y, flip ? -1 : 1, { center: true, ...opt }); }
    // filaments behind
    this.drawStrands(cut);
    // body: silhouette pass then fill pass so the whole length shares one outline
    for (const pas of ['line', 'fill']) for (let i = Math.min(N - 2, cut - 2); i >= 0; i--) {
      const p0 = S[i], p1 = S[i + 1], sh = sbSheet(SB.rad[i]); if (!sh.ok) continue;
      const ai = sbAngIdx(Math.atan2(p1.y - p0.y, p1.x - p0.x)), tg = sh.tag(pas === 'line' ? 'line' : 'fill' + (i % 3));
      drawSprite(sh, tg.from + ai, (p0.x + p1.x) / 2, (p0.y + p1.y) / 2, 1, pas === 'fill' ? { center: true, ...opt } : { center: true });
    }
    // star dust twinkling in the body
    for (let i = 2; i < cut - 1; i += 2) { const p = S[i], r = SB.rad[i]; if (hash2(i, Math.floor(time * 6)) > 0.6) { g.fillStyle = hash2(i * 7, Math.floor(time * 6)) > 0.5 ? '#fffbe8' : '#ffeaa0'; g.fillRect(Math.round(p.x + (hash2(i, 3) - 0.5) * r), Math.round(p.y + hash2(i, 5) * r * 0.6), 1, 1); } }
    // tail fan
    const ts = sheet('sov_tail');
    if (ts.ok && !dead) { const a = Math.atan2(S[N - 1].y - S[N - 2].y, S[N - 1].x - S[N - 2].x); let d = a * 180 / Math.PI; d = (d + 360) % 360; const tg = ts.tag(Math.floor(time * 3) % 2 ? 't1' : 't0'); drawSprite(ts, tg.from + Math.round(d / 15) % 24, S[N - 1].x, S[N - 1].y, 1, { center: true }); }
    // head
    const hsh = sheet('sov_head');
    if (hsh.ok) { const a = Math.atan2(S[0].y - S[1].y, S[0].x - S[1].x), [fi, flip] = sbMirror(a), tg = hsh.tag(this.mouthOpen ? 'open' : 'closed'); drawSprite(hsh, tg.from + fi, S[0].x, S[0].y, flip ? -1 : 1, { center: true, ...opt }); }
    g.restore();
    // exposed-head cue while staggered (crit prompt)
    if (this.state === 'stagger' && this.critable()) { const c = this.headC(); g.fillStyle = '#ffd070'; const y = Math.round(c.y - 20 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(c.x) - 1, y, 3, 3); g.fillRect(Math.round(c.x), y - 1, 1, 5); g.fillRect(Math.round(c.x) - 2, y + 1, 5, 1); }
  },
  drawStrands(cut) {
    for (const s of this.strands || []) {
      if (s.a >= cut) continue;
      const S = this.spine, A = S[s.a];
      let px = A.x, py = A.y;
      s.pts.forEach((q, j) => {
        const n = Math.max(Math.abs(q.x - px), Math.abs(q.y - py)) | 0, a = 1 - j / s.pts.length * 0.65;
        g.fillStyle = `rgba(${j < 3 ? '255,244,200' : '240,200,110'},${a})`;
        for (let k = 0; k <= n; k++) g.fillRect(Math.round(lerp(px, q.x, k / (n || 1))), Math.round(lerp(py, q.y, k / (n || 1))), 1, 1);
        px = q.x; py = q.y;
      });
    }
  },
});

// ================================================================== hooks
const sovBoss = () => boss && boss instanceof SovereignBoss ? boss : null;
function sovClear() { SOV.marks = []; SOV.rings = []; SOV.meteors = []; SOV.well = null; if (SOV.bind && SOV.bind.fx) SOV.bind.fx.kill = true; SOV.bind = null; }
HOOKS.enter.push(() => sovClear());
HOOKS.death.push(() => { sovClear(); sovSetVoid(false); });
HOOKS.update.push(dt => {
  const B = sovBoss();
  if (!B) { if (SOV.marks.length || SOV.bind || SOV.well) sovClear(); if (room && room.def.biome === 'sov_void') sovSetVoid(false); return; }
  for (const m of SOV.marks) { m.t += dt; m.life -= dt; }
  SOV.marks = SOV.marks.filter(m => m.life > 0);
  // the grab: roots hold you where you stood until the burst (or the move is interrupted)
  const bd = SOV.bind;
  if (bd) {
    bd.t += dt;
    if (!B.alive || B.state !== 'attack' || !['grab', 'grabhold'].includes(B.atk) || P.state === 'dead' || bd.t > 2.5) B.releaseBind();
    else { P.x = bd.x; P.vx = 0; if (P.vy < 0) P.vy = 0; if (P.state !== 'hurt') setP('hurt', 'hurt'); }
  }
  // petal blades: drift out, hang, then snap toward where you are
  for (const pr of projectiles) if (pr.sov === 'petal' && !pr.turned && pr.delay <= 0) {
    if (pr.t < pr.turn) { const k = Math.pow(0.15, dt); pr.vx *= k; pr.vy *= k; }
    else { pr.turned = true; const a = Math.atan2(P.y - 12 - pr.y, P.x - pr.x); pr.vx = Math.cos(a) * 250; pr.vy = Math.sin(a) * 250; }
  }
  // meteors
  for (const m of SOV.meteors) {
    m.t += dt;
    if (!m.marked) { m.marked = true; sovMark(m.x, B.floor, m.delay, 24, true); }
    if (m.t >= m.delay + 0.22 && !m.hit) {
      m.hit = true; shake = Math.max(shake, 5); sfx.boom();
      spawnFx(fxOr('sov_beamend', 'hit'), m.x, B.floor - 8, 1);
      hazards.push({ x: m.x, y: B.floor, w: 26, h: 34, dmg: sovDmgB(42), id: m.id, life: 0.14, t: 0, update() {} });
      for (let i = 0; i < 10; i++) particles.push({ x: m.x, y: B.floor - 2, vx: rand(-100, 100), vy: -rand(40, 160), g: 400, life: 0.6, kind: 'gold' });
    }
  }
  SOV.meteors = SOV.meteors.filter(m => m.t < m.delay + 0.5);
  // expanding rings of light
  for (const r of SOV.rings) {
    r.r += r.v * dt;
    const d = Math.hypot(P.x - r.x, P.y - 12 - r.y);
    if (!r.hit && Math.abs(d - r.r) < 9 && hurtPlayer(sovDmgB(46), P.x < r.x ? -1 : 1, r.id, { src: B })) r.hit = true;
  }
  SOV.rings = SOV.rings.filter(r => r.r < 640);
  // gravity well pull (applied to the player's next move via pushVx)
  const w = SOV.well;
  if (w && w.st === 'pull' && P.state !== 'dead') {
    const dx = w.x - P.x, s = (50 + 45 * clamp(1 - Math.abs(dx) / 220, 0, 1)) * w.grow;
    P.pushVx = Math.sign(dx) * Math.min(s, Math.abs(dx) * 4);
    if (Math.random() < 0.8) { const a = rand(0, 6.28), rr = rand(60, 120); particles.push({ x: w.x + Math.cos(a) * rr, y: w.y + Math.sin(a) * rr * 0.7, vx: -Math.cos(a) * rr * 1.2, vy: -Math.sin(a) * rr * 0.8, life: 0.8, kind: 'gold' }); }
  }
  if (w) addLight(w.x, w.y, 90, '255,210,140', 0.8);
});
HOOKS.render.push(() => {
  const B = sovBoss(); if (!B) return;
  const mk = fxSheet('sov_mark');
  for (const m of SOV.marks) {
    const pulse = 0.55 + 0.45 * Math.sin(m.t * 18), a = (m.strong ? 0.9 : 0.5) * Math.min(1, m.t * 6) * pulse;
    if (mk.ok) { const t = mk.tag(Object.keys(mk.tags)[0]); for (let x = m.x - m.w / 2; x < m.x + m.w / 2; x += 16) drawSprite(mk, t.from + Math.floor(time * 12) % 4, x + 8, m.y, 1, { bottom: true, alpha: a }); }
    else { g.fillStyle = `rgba(255,220,140,${a})`; g.fillRect(Math.round(m.x - m.w / 2), Math.round(m.y) - 1, m.w, 1); }
    addLight(m.x, m.y - 4, 20 + m.w * 0.6, '255,220,150', 0.5 * a);
  }
  const rw = fxSheet('sov_ringwave');
  for (const h of hazards) if (h.sovWave && rw.ok) { const t = rw.tag(Object.keys(rw.tags)[0]); drawSprite(rw, t.from + Math.floor(time * 14) % 4, h.x, h.y, h.dir, { bottom: true }); addLight(h.x, h.y - 12, 34, '255,230,170', 0.8); }
  const ms = fxSheet('sov_meteor');
  for (const m of SOV.meteors) if (m.t > m.delay && !m.hit && ms.ok) { const k = (m.t - m.delay) / 0.22, y = lerp(cam.y - 30, B.floor, k), t = ms.tag(Object.keys(ms.tags)[0]); drawSprite(ms, t.from + Math.floor(time * 14) % 4, m.x, y, 1, { bottom: true }); addLight(m.x, y - 6, 40, '255,230,170', 1); }
  for (const r of SOV.rings) {
    const n = Math.max(24, Math.floor(r.r * 0.9)), a = clamp(1.3 - r.r / 640, 0.2, 1);
    for (let k = 0; k < n; k++) { const th = k / n * 6.283, x = r.x + Math.cos(th) * r.r, y = r.y + Math.sin(th) * r.r; if (y > B.floor + 2) continue; g.fillStyle = `rgba(255,${k % 3 ? 236 : 250},${k % 3 ? 170 : 230},${a})`; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2); }
    for (let k = 0; k < 8; k++) { const th = k / 8 * 6.283 + time; addLight(r.x + Math.cos(th) * r.r, r.y + Math.sin(th) * r.r, 40, '255,230,170', 0.6 * a); }
  }
  const w = SOV.well, wsh = fxSheet('sov_well');
  if (w) {
    if (wsh.ok) { const t = wsh.tag(Object.keys(wsh.tags)[0]); drawSprite(wsh, t.from + Math.floor(time * 12) % 8, w.x, w.y, 1, { center: true, alpha: Math.min(1, w.grow + 0.2) }); }
    const R = 84, col = w.st === 'collapse' ? `rgba(255,240,200,${0.5 + 0.5 * Math.sin(time * 30)})` : 'rgba(255,210,140,0.35)';
    g.fillStyle = col;
    for (let k = 0; k < 72; k++) { const th = k / 72 * 6.283, x = w.x + Math.cos(th) * R, y = w.y + Math.sin(th) * R; if (y < B.floor && k % 2 === 0) g.fillRect(Math.round(x), Math.round(y), 1, 1); }
    if (w.st === 'collapse') { const rr = R * (1 - Math.min(1, w.ct / 0.7)); for (let k = 0; k < 48; k++) { const th = k / 48 * 6.283; g.fillStyle = '#fff4c8'; g.fillRect(Math.round(w.x + Math.cos(th) * rr), Math.round(w.y + Math.sin(th) * rr), 1, 1); } }
  }
  const rays = B.phase === 3 ? B.rays : (B.state === 'attack' && B.mv && B.mv.rays);
  if (rays) for (const r of rays) sovDrawRay(r, 1, B.phase === 3 ? B.raysThin : B.mv.thin);
});

// ---- intro cutscene (same beats as before; sheet-aware so the nova pose still plays)
BOSS_CUTS.sovereign = b => [
  act(() => { b.baseY = b.floor - 170; b.y = b.baseY; b.setS('dormant', 'glide'); }),
  { pan: { x: b.x, y: b.floor - 150 }, dur: 1.2 },
  { dur: 2.6, tween: (dt, k) => { b.baseY = lerp(b.floor - 170, b.floor, 1 - Math.pow(1 - k, 3)); b.y = b.baseY - 10; const t = camTargetFor(b.x, b.y - 60); cam.x = lerp(cam.x, t.x, Math.min(1, dt * 3)); cam.y = lerp(cam.y, t.y, Math.min(1, dt * 3)); if (Math.random() < 0.8) particles.push({ x: b.x + rand(-70, 70), y: b.y - rand(20, 140), vx: rand(-10, 10), vy: rand(10, 30), life: 2, kind: 'petal' }); } },
  act(() => { b.baseY = b.floor; b.setS('dormant', 'idle'); }),
  say('The Pale Sovereign', 'So. The little ember climbed all the way to my heart.'),
  say('The Pale Sovereign', F('v_truth') ? 'And you brought my seedling’s blessing with you. How sweet. I will take you both.' : 'Kneel, and I will make you a root. Stand, and I will make you ash.'),
  act(() => { b.setS('dormant', 'nova', false); }), wait(0.7),
  act(() => { flashScreen = 0.8; shake = 10; sfx.roar(); spawnFx(fxOr('sov_nova', 'roar_ring'), b.x, b.y - 70, 1); }), wait(1.2),
  { do() { b.baseY = b.floor; b.setS('dormant', 'idle'); }, always: true },
];
BOSS_SPAWN.sovereign = (cx, fy) => makeSovereign(cx, fy);
