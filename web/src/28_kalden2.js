// ------------------------------------------------------------------ Ser Kalden, reworked (agent K)
// Still a MetaBoss (07b_bosses2.js) -- same HP bar, crit/stagger rules, rewards, cutscene, fog and death -- with a far
// larger moveset spread over three sheets (same body placement, anchor x 40):
//   kalden(_p2)    idle walk combo thrust leap guard backstep rotburst stagger death          (art/gen_kalden.py)
//   kalden_b(_p2)  quick3 spin4 rising3 stab5 charge kick plunge lunge feint                   (art/kalden_moves.py)
//   kalden_c       rotcombo tendrils grab grabhold berserk   (phase 2 only: the rot arm)      (art/kalden_moves.py)
// Phase 1 is a sword knight: 3/4/5-hit strings with varied rhythm, a shoulder charge, a guard-break kick, a leaping
// plunge, backstep-into-lunge, a feint, his guard/counter. Phase 2 the rot-swollen arm takes over: rot-infused strings
// that leave pools, tendril lines erupting from the floor, a ring burst with a safe pocket, a grab, and at the end of
// him a berserk string. Tuned to sit between Gravetusk and Morvain (see the agent-K report for the numbers).
const KD = { marks: [], pools: [], mark: null };
const KD_SHEET = { quick3: 'b', spin4: 'b', rising3: 'b', stab5: 'b', charge: 'b', kick: 'b', plunge: 'b', lunge: 'b', feint: 'b',
                   rotcombo: 'c', tendrils: 'c', grab: 'c', grabhold: 'c', berserk: 'c' };
const KD_COOL = { grab: 7, tendrils: 5.5, rotring: 7, rotburst: 4, berserk: 11, charge: 3.5, plunge: 3.5, kick: 2.5, lunge: 2, feint: 3, guard: 3 };
const KD_ALIAS = { rotring: 'rotburst' };   // move name -> animation tag
const kdD = d => BOSS_DMG * d * NGP.dmg;
const kdSfx = {
  tendril: () => { noise(0.35, 260, 0.7, 0.35, 'lowpass', 1.6); tone(70, 0.3, 0.12, 'sawtooth', 1.4); },
  squelch: () => { noise(0.25, 500, 0.6, 0.4, 'lowpass', 0.4); tone(110, 0.2, 0.12, 'sawtooth', 0.5); },
  kick: () => { noise(0.12, 300, 1, 0.5, 'lowpass'); tone(95, 0.15, 0.2, 'square', 0.5); },
  rush: () => { noise(0.5, 350, 0.6, 0.3, 'lowpass', 1.2); tone(130, 0.35, 0.08, 'sawtooth', 1.5); },
};

// ---- hazards: rot tendrils (a floor crack warns first), rot pools
function kdTendril(x, floor, delay, dmg = 34, rot = 26, dir = 1) {
  if (x < TILE + 10 || x > room.pw - TILE - 10) return;
  KD.marks.push({ x, t: 0, life: delay + 0.12, w: 9 });
  hazards.push({ x, y: floor, w: 16, h: 58, dmg: kdD(dmg), rot, id: ++hazardId, life: 3, delay, fx: null, kd: true,
    onStart: h => { h.fx = spawnFx(fxOr('kd_tendril', 'root_spike'), h.x, floor, dir, null, { bottom: true }); if (!h.fx) h.life = 0; else { kdSfx.tendril(); shake = Math.max(shake, 2); for (let i = 0; i < 6; i++) particles.push({ x: h.x + rand(-8, 8), y: floor - 2, vx: rand(-50, 50), vy: -rand(40, 120), g: 400, life: 0.5, kind: 'spore' }); } },
    update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } const i = h.fx.anim.i; if (i >= 3 && i <= 5) addLight(h.x, floor - 30, 40, '170,220,90', 0.7); },
    active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5 });
}
function kdPool(x, floor, life = 5.5) {
  x = clamp(x, TILE + 26, room.pw - TILE - 26);
  while (KD.pools.length >= 4) { const o = KD.pools.shift(); o.h.life = 0; if (o.fx) o.fx.kill = true; }
  const fx = spawnFx(fxOr('kd_pool'), x, floor, 1, null, { bottom: true, loop: true, life });
  const h = { x, y: floor, w: 46, h: 8, dmg: kdD(6), rot: 9, tick: 0.5, id: ++hazardId, life, pool: true, delay: 0,
              update: h => addLight(h.x, floor - 4, 34, '170,220,90', 0.5) };
  hazards.push(h); KD.pools.push({ h, fx });
}
function kdWaves(b, x, spd = 160, life = 1.4) {
  for (const dd of [-1, 1]) hazards.push({ x, y: b.floor, vx: dd * spd, w: 16, h: 14, dmg: kdD(30), rot: 28, id: ++hazardId, life, wave: true, dir: dd, color: 'rot' });
}
function kdClear() { for (const p of KD.pools) if (p.fx) p.fx.kill = true; KD.pools = []; KD.marks = []; KD.mark = null; }
function kdFrames(an, a, z) { let T = 0; for (let i = a; i <= z && i < an.n; i++) T += an.ms(i); return T / 1000 / an.speed; }

class KaldenBoss extends MetaBoss {
  constructor(x, y, cfg) {
    super('kalden', x, y, cfg);
    this.SB = [sheet('kalden_b'), sheet('kalden_b_p2', { meta: ASSETS.kalden_b_meta })];
    this.SC = sheet('kalden_c');
    this.cds = {}; this.recent = []; this.blockT = 0; this.mv = {};
  }
  base() { return this.sheetsArr[this.phase === 2 && this.sheetsArr[1] && this.sheetsArr[1].ok ? 1 : 0]; }
  sheetFor(tag) {
    const k = KD_SHEET[tag];
    if (k === 'b') { const s = this.SB[this.phase - 1]; return s && s.ok && s.has(tag) ? s : this.SB[0]; }
    if (k === 'c') return this.SC;
    return this.base();
  }
  hasMove(m) {
    if (['walk', 'backstep', 'guard'].includes(m)) return true;
    const t = KD_ALIAS[m] || m, s = this.sheetFor(t);
    return s.ok && s.has(t);
  }
  setS(st, tag, loop = true) {
    this.state = st;
    let sh = this.sheetFor(tag);
    if (!sh.ok || !sh.has(tag)) { sh = this.base(); if (!sh.has(tag)) tag = 'idle'; }
    if (sh !== this.sh || this.anim.s !== sh) { this.sh = sh; this.anim = new Anim(sh, tag, loop, this.speed); }
    else this.anim.set(tag, loop, this.speed);
  }
  toBase() { const s = this.base(); if (this.sh !== s || this.anim.s !== s) { this.sh = s; this.anim = new Anim(s, 'idle', true, 1); } }
  canStagger() { return super.canStagger() && !this.caught && !(this.state === 'attack' && ['grabhold', 'berserk', 'charge'].includes(this.atk)); }
  pickMove() {
    const d = Math.abs(P.x - this.x), p2 = this.phase === 2, w = this.weights(d, p2);
    if (this.afterBack) { this.afterBack = false; return d > 200 ? (this.cds.plunge > 0 ? 'charge' : 'plunge') : Math.random() < 0.75 ? 'lunge' : 'charge'; }
    this.recent.forEach((m, i) => { if (w[m]) w[m] *= i === 0 ? 0.2 : 0.55; });
    const e = Object.entries(w).filter(([k, v]) => v > 0 && !(this.cds[k] > 0) && this.hasMove(k));
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e.length ? e[0][0] : 'combo';
  }
  start(m) {
    if (this.afterBack && m === 'thrust') { this.afterBack = false; m = 'lunge'; }
    if (m === 'backstep') this.afterBack = true;
    if (!this.hasMove(m)) m = 'combo';
    if (KD_COOL[m]) this.cds[m] = KD_COOL[m] * (this.phase === 2 ? 0.8 : 1);
    if (!['walk', 'backstep', 'guard'].includes(m)) { this.recent.unshift(m); this.recent.length = Math.min(this.recent.length, 3); }
    this.variant = KD_ALIAS[m] ? m : null;
    this.mv = {}; KD.mark = null;
    super.start(KD_ALIAS[m] || m);
    const M = this.moves[this.atk];
    if (this.state === 'attack' && M && M.begin) M.begin.call(this, this.anim);
  }
  update(dt) {
    for (const k in this.cds) this.cds[k] -= dt;
    if (this.active && this.alive) {
      if (typeof isBlocking === 'function' && isBlocking() && Math.abs(P.x - this.x) < 120) this.blockT = Math.min(3, this.blockT + dt); else this.blockT = Math.max(0, this.blockT - dt * 0.5);
      // he punishes a flask drunk in reach
      if (P.state === 'heal' && this.lastPS !== 'heal' && ['idle', 'walk'].includes(this.state) && Math.abs(P.x - this.x) < 230 && Math.random() < (this.phase === 2 ? 0.7 : 0.45))
        this.punish = true;
      this.lastPS = P.state;
      if (this.punish && ['idle', 'walk'].includes(this.state) && P.state !== 'dead') { this.punish = false; this.start(Math.abs(P.x - this.x) < 90 ? 'quick3' : this.cds.charge > 0 ? 'lunge' : 'charge'); }
    }
    super.update(dt);
    if (this.caught) this.holdPlayer();
  }
  // ---- attack driver: per-move tick, custom hits, rot in phase 2, and his own (branching) chains
  updateAttack(dt) {
    const a = this.atk, M = this.moves[a] || {}, an = this.anim;
    if (M.tick && M.tick.call(this, dt, an) === 'stop') return;
    if (this.state !== 'attack' || this.atk !== a) return;
    const wins = metaWindows(this.sh, a), n0 = this.hitIds.size;
    if (M.custom) for (let i = 0; i < wins.length; i++) this.hitIds.add(i);
    const savedRot = M.rot, savedChains = this.chains;
    if (this.phase === 2 && !M.rot) M.rot = M.p2rot ?? 10;
    let chainTo = null;
    if (an.done && !this.pendingPhase && P.state !== 'dead') chainTo = this.nextInChain(a);
    this.chains = null;
    super.updateAttack(dt);
    this.chains = savedChains; M.rot = savedRot;
    if (this.hitIds.size > n0 && !M.custom && M.onHit) M.onHit.call(this);
    if (chainTo && this.state === 'idle') { this.chain++; this.start(chainTo); }
    else if (an.done && this.state === 'idle') {
      this.chain = 0;
      this.cool = (this.phase === 1 ? rand(...this.cool1) : rand(...this.cool2)) + (M.rest || 0);
      if (this.lowHp()) this.cool *= 0.85;
    }
  }
  // MetaBoss leap, but aimed so the blade (not his feet) lands on you: the old version set him down 16px short and the
  // impact rect (23-56px ahead) sailed past -- the leap never hit
  updateLeap(dt, M) {
    const an = this.anim, wins = metaWindows(this.sh, this.atk), land = wins.length ? wins[0].active[0] : an.n - 3;
    if (an.changed && an.i === M.leap && !this.air) {
      let T = 0; for (let i = an.i; i < land; i++) T += an.ms(i); T = Math.max(0.2, T / 1000 / an.speed);
      this.air = { x0: this.x, tx: clamp(P.x - this.face * (M.aim ?? 34), this.L + 20, this.R - 20), t: 0, T };
    }
    if (this.air) {
      if (an.i < land - 2) this.air.tx = approach(this.air.tx, clamp(P.x - this.face * (M.aim ?? 34), this.L + 20, this.R - 20), 60 * dt);
      this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
      this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * (M.height || 70);
      if (k >= 1) { this.air = null; this.y = this.floor; shake = 8; sfx.boom(); spawnFx('shockwave', this.x + this.face * 30, this.floor, 1); M.onLand && M.onLand.call(this); }
    }
  }
  lowHp() { return this.phase === 2 && this.hp < this.maxHp * 0.25; }
  nextInChain(a) {
    const C = this.phase === 2 ? KD_CHAIN2 : KD_CHAIN1, f = C[a] || (this.phase === 2 && KD_CHAIN1[a]);
    if (!f) return null;
    const max = this.phase === 2 ? 2 : 1, pc = (this.lowHp() ? 0.5 : this.phase === 2 ? 0.36 : 0.36) * (this.moves[a].chainMul || 1);
    if (this.chain >= max || Math.random() >= pc) return null;
    const nx = f(this, Math.abs(P.x - this.x));
    return nx && !(this.cds[nx] > 0) && this.hasMove(nx) ? nx : null;
  }
  any(l) { return l[Math.floor(Math.random() * l.length)]; }
  go(an, dt, a, z, spd, stop = 34) { if (an.i >= a && an.i <= z && Math.abs(P.x - this.x) > stop) { this.x = clamp(this.x + this.face * spd * this.speed * dt, this.L + 20, this.R - 20); } }
  holdFor(an, dt, fi, lo, hi) {
    if (an.i === fi && this.mv['h' + fi] === undefined) this.mv['h' + fi] = rand(lo, hi);
    if (an.i === fi && this.mv['h' + fi] > 0) { this.mv['h' + fi] -= dt; an.hold(); }
  }
  // ---- the grab
  catchPlayer() {
    this.caught = true; P.vx = P.vy = 0; setP('rest', 'hurt', false); P.face = -this.face;
    sfx.bigHit(); kdSfx.squelch(); hitstop = 0.14; shake = 6; flashScreen = 0.2;
    this.start('grabhold');
  }
  holdPlayer() {
    if (!this.caught) return;
    if (P.state === 'dead' || this.state !== 'attack' || this.atk !== 'grabhold') { this.releaseCatch(); return; }
    const pts = this.sh.meta && this.sh.meta.points && this.sh.meta.points.grabhold;
    const h = pts ? metaPoint(this.sh, this, pts.hold[Math.min(this.anim.i, pts.hold.length - 1)]) : { x: this.x + this.face * 30, y: this.y - 30 };
    P.x = h.x; P.y = Math.min(this.floor, h.y + 16); P.vx = P.vy = 0; P.face = -this.face;
    if (P.state !== 'rest') setP('rest', 'hurt', false);
  }
  squeeze(dmg, rot, release) {
    if (!this.caught) return;
    P.state = 'hurt'; P.inv = 0; P.lastHit = undefined;
    hurtPlayer(kdD(dmg), this.face, ++hazardId, { src: this, rot });
    spawnFx(fxOr('rot_hit', 'hit'), P.x, P.y - 14, this.face); hitstop = Math.max(hitstop, 0.1); shake = Math.max(shake, 5);
    for (let i = 0; i < 12; i++) particles.push({ x: P.x, y: P.y - 14, vx: rand(-80, 80), vy: -rand(20, 110), g: 300, life: rand(0.4, 0.8), kind: 'spore' });
    if (P.state === 'dead') { this.caught = false; return; }
    if (release) { this.caught = false; setP('hurt', 'hurt'); P.vx = this.face * 150; P.vy = -150; P.ground = false; P.inv = 0.8; }
    else setP('rest', 'hurt', false);
  }
  releaseCatch() { if (this.caught) { this.caught = false; if (P.state === 'rest') { setP('hurt', 'hurt'); P.vy = -60; P.inv = 0.6; } } }
  stagger() { this.releaseCatch(); KD.mark = null; this.air = null; this.y = this.floor; this.toBase(); super.stagger(); }
  enterPhase2() { this.releaseCatch(); KD.mark = null; this.chain = 0; super.enterPhase2(); }
  die() { this.releaseCatch(); kdClear(); this.toBase(); super.die(); }
  hit(info) {
    if (this.state === 'guard' && !info.crit && info.kind !== 'heavy' && info.dir === -this.face && info.melee) {
      super.hit(info);   // blocked (MetaBoss): he answers with a counter -- thrust, kick or a spin
      if (this.guardHit) { this.guardHit = false; this.start(this.any(['thrust', 'kick', this.phase === 2 ? 'rotcombo' : 'spin4'])); }
      return;
    }
    super.hit(info);
  }
  draw() {
    if (KD.mark) {   // where the plunge will land
      const a = 0.35 + 0.35 * Math.sin(time * 26), col = this.phase === 2 ? '170,220,90' : '160,230,210';
      g.strokeStyle = `rgba(${col},${a})`; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(KD.mark.x), this.floor - 1, 22, 3, 0, 0, 6.3); g.stroke();
      g.fillStyle = `rgba(${col},${a * 0.3})`; g.fill();
      addLight(KD.mark.x, this.floor - 4, 36, col, 0.5);
    }
    super.draw();
  }
}

// ---- branching follow-ups (d = distance to you). Phase-2 table falls back to the phase-1 one.
const KD_CHAIN1 = {
  combo: (b, d) => d < 80 ? b.any(['kick', 'spin4', 'thrust']) : 'lunge',
  quick3: (b, d) => d < 80 ? b.any(['kick', 'stab5']) : 'charge',
  spin4: (b, d) => d < 90 ? 'feint' : 'lunge',
  rising3: (b, d) => d < 80 ? 'quick3' : 'plunge',
  stab5: (b, d) => d < 90 ? b.any(['combo', 'kick']) : 'charge',
  thrust: (b, d) => d < 80 ? b.any(['combo', 'quick3']) : 'leap',
  kick: (b, d) => d < 90 ? b.any(['quick3', 'combo', 'rising3']) : 'lunge',
  feint: (b, d) => d < 80 ? 'spin4' : 'lunge',
  leap: (b, d) => d < 90 ? b.any(['combo', 'quick3']) : 'thrust',
  plunge: (b, d) => d < 90 ? b.any(['spin4', 'kick']) : 'lunge',
  charge: (b, d) => d < 120 ? b.any(['rising3', 'quick3']) : 'leap',
  lunge: (b, d) => d < 80 ? b.any(['quick3', 'spin4', 'kick']) : 'plunge',
};
const KD_CHAIN2 = {
  combo: (b, d) => d < 80 ? b.any(['rotcombo', 'kick', 'rotburst']) : 'tendrils',
  quick3: (b, d) => d < 80 ? b.any(['rotcombo', 'grab', 'stab5']) : 'charge',
  rotcombo: (b, d) => d < 90 ? b.any(['grab', 'kick', 'spin4']) : 'tendrils',
  tendrils: (b, d) => d > 110 ? b.any(['lunge', 'charge', 'plunge']) : 'rotcombo',
  grab: (b, d) => d < 90 ? 'rotcombo' : 'tendrils',
  plunge: (b, d) => d < 100 ? b.any(['rotring', 'rotcombo']) : 'tendrils',
  rotburst: (b, d) => d < 90 ? 'rotcombo' : 'lunge',
  kick: (b, d) => d < 90 ? b.any(['rotcombo', 'quick3', 'grab']) : 'lunge',
  spin4: (b, d) => d < 90 ? b.any(['feint', 'rotcombo']) : 'tendrils',
  lunge: (b, d) => d < 80 ? b.any(['rotcombo', 'spin4', 'grab']) : 'plunge',
};

function makeKalden2(x, y) {
  return new KaldenBoss(x, y, {
    sheets: ['kalden', 'kalden_p2'], stanceMax: 300, walkSpeed: 52, prefer: 56, p2at: 0.5, p2speed: 1.15, p2tag: 'rotburst', critRange: 44,
    introTag: 'guard', cool1: [0.7, 1.25], cool2: [1.0, 1.6], victory: 'OATH FULFILLED', deathParticle: 'gold',
    onIntro() { sfx.roar(); },
    weights(d, p2) {
      let w;
      if (d < 75) w = { combo: 1.3, quick3: 1.4, spin4: 1.1, rising3: 1.0, stab5: 0.7, kick: 0.8 + this.blockT * 0.8, feint: 0.8, guard: p2 ? 0.3 : 0.8, backstep: 0.7, thrust: 0.3 };
      else if (d < 170) w = { thrust: 1.0, stab5: 1.1, lunge: 0.9, charge: 1.0, leap: 0.9, plunge: 0.8, walk: 1.0, feint: 0.5, quick3: 0.4 };
      else w = { charge: 1.8, leap: 1.4, plunge: 1.3, lunge: 0.8, walk: 1.4, thrust: 0.5 };
      if (p2) {
        for (const k in w) if (!['walk', 'backstep'].includes(k)) w[k] *= 0.6;
        if (d < 75) Object.assign(w, { rotcombo: 1.8, grab: 0.8, rotburst: 0.7, rotring: 0.6, tendrils: 0.5 });
        else if (d < 170) Object.assign(w, { tendrils: 1.4, rotcombo: 0.8, grab: 0.5, rotring: 0.3 });
        else Object.assign(w, { tendrils: 1.8 });
        if (this.lowHp()) w.berserk = 2.4;
      }
      return w;
    },
    moves: {
      // ---- his original four (unchanged behaviour, tuned numbers)
      combo: { dmg: [36, 36, 50], parry: true, step: 70, fx: 'kalden_slash' },
      thrust: { dmg: [54], parry: true, step: 230, fx: 'thrust' },
      leap: { dmg: [58], leap: 2, height: 80, onLand() { if (this.phase === 2) { kdWaves(this, this.x); kdPool(this.x + this.face * 20, this.floor, 4); } } },
      rotburst: { dmg: [46], rot: 60, shake: 8, on: { 6() {
        sfx.fire(); spawnFx(fxOr('rotmist', 'shockwave'), this.x, this.floor, 1, null, { bottom: true });
        if (this.variant === 'rotring') {   // the ring: tendrils burst out in rings; the pocket at his feet is safe after the burst
          const ring = [96, 136, 176, 216, 256];
          ring.forEach((r, k) => { for (const s of [-1, 1]) kdTendril(this.x + s * r, this.floor, 0.42 + k * 0.2, 32, 24, s); });
          if (!SAVE.hints.kd_ring) { SAVE.hints.kd_ring = 1; toast('Stay close after the burst, or roll through the rings.', 3); }
        } else for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.floor, vx: dd * 150, w: 16, h: 14, dmg: kdD(32), rot: 30, id: ++hazardId, life: 1.6, wave: true, dir: dd, color: 'rot' });
      } } },
      // ---- phase-1 sword strings
      quick3: { dmg: [28, 28, 48], parry: true, fx: 'kalden_slash', shake: 3,
        tick(dt, an) { this.go(an, dt, 1, 2, 150); this.go(an, dt, 4, 4, 90); this.holdFor(an, dt, 7, 0, this.phase === 2 ? 0.45 : 0.3); if (an.changed && an.i === 9) { shake = 7; sfx.boom(); spawnFx('shockwave', this.x + this.face * 30, this.floor, 1); if (this.phase === 2) kdPool(this.x + this.face * 30, this.floor, 4); } } },
      spin4: { dmg: [24, 24, 28, 42], parry: true, shake: 2,
        tick(dt, an) { this.go(an, dt, 1, 2, 140); this.go(an, dt, 6, 6, 110);  if (an.changed && an.i === 9) { sfx.bossSwing(); spawnFx(fxOr('kalden_slash', 'boss_slash'), this.x - this.face * 24, this.y - 24, -this.face); } } },
      rising3: { dmg: [38, 50, 46], parry: true, shake: 3,
        tick(dt, an) {
          this.go(an, dt, 1, 3, 120); this.go(an, dt, 9, 9, 260, 24);
          if (an.i >= 3 && an.i <= 4) this.y = this.floor - 6 * Math.sin(Math.min(1, (an.i - 3 + an.t / an.ms()) / 2) * Math.PI); else this.y = this.floor;
          if (an.changed && an.i === 6) { shake = 8; sfx.boom(); const cx = this.x + this.face * 30; spawnFx('shockwave', cx, this.floor, 1); hazards.push({ x: cx, y: this.floor, w: 70, h: 18, dmg: kdD(24), id: ++hazardId, life: 0.15 }); if (this.phase === 2) kdWaves(this, cx); }
        } },
      stab5: { dmg: [22, 22, 22, 48, 34], parry: true,
        tick(dt, an) { this.go(an, dt, 2, 6, 110, 40); this.holdFor(an, dt, 8, 0, 0.25); this.go(an, dt, 9, 9, 380, 26); } },
      charge: { dmg: [44], shake: 2, rest: 0.25, chainMul: 0.9,
        begin() { this.mv.run = 0; this.mv.dir = this.face; },
        tick(dt, an) {
          if (an.i < 2) return;
          if (an.i >= 2 && an.i <= 5 && !this.mv.stop) {
            if (an.changed && an.i === 2 && !this.mv.run) kdSfx.rush();
            this.face = this.mv.dir; this.mv.run += dt;
            this.x += this.mv.dir * 300 * this.speed * dt;
            if (an.changed && an.i % 2 === 0) { sfx.step(); particles.push({ x: this.x - this.mv.dir * 14, y: this.floor, vx: -this.mv.dir * 40, vy: -rand(10, 40), life: 0.5, kind: 'dust' }); shake = Math.max(shake, 1.5); }
            const wall = this.x <= this.L + 20 || this.x >= this.R - 20, past = (this.x - P.x) * this.mv.dir > 60;
            if (wall) { this.x = clamp(this.x, this.L + 20, this.R - 20); shake = 9; sfx.boom(); spawnFx('shockwave', this.x + this.mv.dir * 16, this.floor, 1); this.mv.stop = true; an.i = 6; an.t = 0; an.changed = true; an.speed = 0.55; }
            else if (past || this.mv.run > 1.5) { this.mv.stop = true; an.i = 6; an.t = 0; an.changed = true; }
            else if (an.i === 5 && an.t + dt * 1000 * an.speed >= an.ms()) { an.i = 2; an.t = 0; an.changed = true; }
          }
        },
        onHit() { P.vx = this.mv.dir * 240; P.vy = -80; } },
      kick: { dmg: [26], shake: 3, chainMul: 1.7,
        tick(dt, an) {
          this.go(an, dt, 0, 1, 90, 30);
          if (an.i >= 2 && an.i <= 3 && typeof isBlocking === 'function' && isBlocking()) {   // it breaks a raised guard outright
            const w = metaWindows(this.sh, 'kick')[0];
            if (w && overlap(metaRect(this.sh, this, w.hit), playerHurtbox()) && !this.mv.broke) { this.mv.broke = true; P.st = 0; }
          }
          if (an.changed && an.i === 2) kdSfx.kick();
        },
        onHit() { P.vx = this.face * 230; P.st = Math.max(0, P.st - 30); P.stDelay = Math.max(P.stDelay || 0, 0.8); shake = 5; } },
      plunge: { dmg: [], custom: true, shake: 9, rest: 0.2,
        tick(dt, an) {
          const land = 6;
          if (an.changed && an.i === 2 && !this.air) { sfx.bossSwing(); this.air = { x0: this.x, t: 0, T: kdFrames(an, 2, 5) + 0.25 }; }
          this.holdFor(an, dt, 4, 0.12, this.phase === 2 ? 0.35 : 0.45);
          if (this.air && an.i < land) {
            this.air.t += dt;
            const k = Math.min(1, this.air.t / this.air.T);
            if (an.i <= 4) this.x = approach(this.x, clamp(P.x, this.L + 20, this.R - 20), 280 * dt);
            this.y = this.floor - 72 * Math.sin(Math.min(1, an.i <= 4 ? Math.min(0.5, k) : 0.5 + (an.t / an.ms()) * 0.5) * Math.PI);
            KD.mark = { x: this.x };
          }
          if (an.changed && an.i === land) {
            this.air = null; this.y = this.floor; KD.mark = null; shake = 10; sfx.boom();
            spawnFx('shockwave', this.x + this.face * 18, this.floor, 1); spawnFx('ground_crack', this.x + this.face * 18, this.floor, 1);
            hazards.push({ x: this.x + this.face * 14, y: this.floor, w: 76, h: 40, dmg: kdD(60), id: ++hazardId, life: 0.16, rot: this.phase === 2 ? 14 : 0 });
            if (this.phase === 2) { kdWaves(this, this.x); kdPool(this.x + this.face * 18, this.floor); }
          }
        } },
      lunge: { dmg: [50], parry: true, shake: 3,
        tick(dt, an) { if (an.i >= 2 && an.i <= 4 && (this.mv.dist = (this.mv.dist || 0)) < 190) { const s = 600 * this.speed * dt; if (Math.abs(P.x - this.x) > 26) { this.x = clamp(this.x + this.face * s, this.L + 20, this.R - 20); this.mv.dist += s; } if (Math.random() < 0.6) particles.push({ x: this.x - this.face * 20, y: this.floor - 2, vx: -this.face * 60, vy: -rand(10, 30), life: 0.4, kind: 'dust' }); } } },
      feint: { dmg: [52], parry: true, fx: 'kalden_slash', shake: 3,
        tick(dt, an) {
          this.go(an, dt, 0, 1, 100);
          if (an.changed && an.i === 2 && Math.random() < 0.35) { an.i = 3; an.t = 0; }   // sometimes no twitch at all
          this.holdFor(an, dt, 3, 0.05, this.phase === 2 ? 0.8 : 0.6);
          if (an.i === 3 && this.mv.h3 !== undefined && this.mv.h3 <= 0 && !this.mv.mix) {
            this.mv.mix = true;
            if (Math.abs(P.x - this.x) < 70 && Math.random() < (this.blockT > 0.4 ? 0.8 : 0.25)) { this.start('kick'); return 'stop'; }
          }
          this.go(an, dt, 4, 4, 200, 30);
        } },
      // ---- phase 2: the rot arm
      rotcombo: { dmg: [30, 30, 40, 48], rot: 12, parry: true, shake: 3, rest: 0.5,
        tick(dt, an) {
          this.go(an, dt, 1, 2, 140); this.holdFor(an, dt, 10, 0, 0.3);
          if (an.i >= 5 && an.i <= 6 && Math.random() < 0.5) particles.push({ x: this.x + this.face * rand(4, 16), y: this.y - rand(24, 40), vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'spore' });
          if (an.changed && an.i === 12) {
            shake = 8; sfx.boom(); kdSfx.squelch();
            const pts = this.sh.meta.points && this.sh.meta.points.rotcombo, p = pts ? metaPoint(this.sh, this, pts.slam[0]) : { x: this.x + this.face * 60 };
            spawnFx(fxOr('rot_hit', 'shockwave'), p.x, this.floor - 6, this.face); kdPool(p.x, this.floor);
          }
        } },
      tendrils: { dmg: [30], rot: 20, rest: 0.45,
        tick(dt, an) {
          if (an.i <= 1 && Math.random() < 0.5) particles.push({ x: this.x + rand(-14, 14), y: this.y - rand(10, 50), vx: 0, vy: -rand(10, 30), life: 0.7, kind: 'spore' });
          if (an.changed && an.i === 2) {
            shake = 6; sfx.boom(); kdSfx.tendril();
            const dir = P.x < this.x ? -1 : 1, n = this.lowHp() ? 8 : 7, gap = 30, x0 = this.x + dir * 44;
            for (let k = 0; k < n; k++) kdTendril(x0 + dir * k * gap, this.floor, 0.34 + k * 0.1, 34, 20, dir);
            if (this.lowHp()) for (let k = 0; k < 3; k++) kdTendril(clamp(P.x + (k - 1) * 40, this.L, this.R), this.floor, 1.25 + k * 0.12, 30, 20, dir);
            else if (Math.random() < 0.5) for (let k = 0; k < 3; k++) kdTendril(this.x - dir * (44 + k * gap), this.floor, 0.5 + k * 0.12, 30, 20, -dir);
          }
        } },
      grab: { dmg: [], custom: true, rest: 0.3,
        tick(dt, an) {
          if (an.i <= 1) { const h = { x: this.x - this.face * 4, y: this.y - 34 }; addLight(h.x, h.y, 34, '170,220,90', 0.8); if (Math.random() < 0.5) particles.push({ x: h.x + rand(-5, 5), y: h.y + rand(-5, 5), vx: 0, vy: -rand(10, 30), life: 0.4, kind: 'spore' }); }
          if (an.changed && an.i === 2) { sfx.bossSwing(); kdSfx.squelch(); }
          this.go(an, dt, 2, 3, 160, 50);
          const w = metaWindows(this.sh, 'grab')[0];
          if (!w || an.i < w.active[0] || an.i > w.active[1] || this.caught || P.state === 'dead' || iframes() || P.inv > 0) return;
          const r = w.rects && w.rects[String(an.i)];
          if (overlap(metaRect(this.sh, this, r || w.hit), playerHurtbox())) { this.catchPlayer(); return 'stop'; }
        } },
      grabhold: { dmg: [], custom: true, rest: 0.5,
        tick(dt, an) {
          this.holdPlayer();
          if (an.changed && an.i === 1) this.squeeze(14, 24, false);
          if (an.changed && an.i === 2) this.squeeze(14, 24, false);
          if (an.changed && an.i === 3) { this.holdPlayer(); this.squeeze(42, 20, true); shake = 10; sfx.boom(); flashScreen = 0.25; kdPool(this.x + this.face * 34, this.floor); }
        } },
      berserk: { dmg: [26, 26, 28, 34, 40, 58], rot: 12, parry: true, shake: 3, rest: 0.8,
        begin() { sfx.roar(); flashScreen = 0.3; },
        tick(dt, an) {
          this.go(an, dt, 1, 4, 150); this.go(an, dt, 6, 8, 120);
          if (Math.random() < 0.5) particles.push({ x: this.x + rand(-20, 20), y: this.y - rand(10, 60), vx: 0, vy: -rand(20, 50), life: 0.7, kind: 'spore' });
          if (an.changed && an.i === 12) { shake = 12; sfx.boom(); sfx.fire(); flashScreen = 0.3; kdWaves(this, this.x, 190, 1.6); kdPool(this.x - 40, this.floor); kdPool(this.x + 40, this.floor); }
        } },
    },
    wake() { return P.x > 4 * TILE + 24; },
    ambient() { if (this.phase === 2 && Math.random() < 0.3) particles.push({ x: this.x + rand(-16, 16), y: this.y - rand(10, 50), vx: 0, vy: -rand(10, 25), life: 0.8, kind: 'spore' }); addLight(this.x, this.y - 30, 60, this.phase === 2 ? '150,210,90' : '160,220,230', 0.6); },
  });
}

// ---- floor warnings under the tendrils; state reset per room
HOOKS.update.push(dt => {
  if (!KD.marks.length) return;
  for (const m of KD.marks) m.t += dt;
  KD.marks = KD.marks.filter(m => m.t < m.life);
});
HOOKS.render.push(() => {
  if (!KD.marks.length || !boss || boss.kind !== 'kalden') return;
  const fl = boss.floor;
  for (const m of KD.marks) {
    const k = clamp(m.t / m.life, 0, 1), a = 0.3 + 0.5 * k + 0.2 * Math.sin(time * 30);
    g.fillStyle = `rgba(150,200,80,${a * 0.5})`; g.fillRect(Math.round(m.x - m.w), fl - 1, Math.round(m.w * 2), 1);
    g.fillStyle = `rgba(255,190,80,${a})`; g.fillRect(Math.round(m.x) - 1, fl - 2, 3, 1);
    if (Math.random() < 0.25) particles.push({ x: m.x + rand(-5, 5), y: fl - 1, vx: 0, vy: -rand(10, 35), life: 0.4, kind: 'spore' });
    addLight(m.x, fl - 3, 16 + 10 * k, '170,220,90', 0.35 + 0.3 * k);
  }
});
HOOKS.enter.push(() => { KD.marks = []; KD.pools = []; KD.mark = null; });
HOOKS.death.push(() => { KD.marks = []; KD.mark = null; });
try { window.__kd = { KD, get fx() { return fx; }, get hazards() { return hazards; }, get projectiles() { return projectiles; } }; } catch (e) {}   // debug handle for automated tests
