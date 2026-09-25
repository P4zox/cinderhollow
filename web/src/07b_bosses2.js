// ------------------------------------------------------------------ data-driven bosses: Kalden, the Vessel of Rot, the Pale Sovereign
Object.assign(BOSS_INFO, {
  kalden: { name: 'Ser Kalden, the Oathless', hp: 2300, cinders: 6000, reward: ['w:kalden', 'c_crest', 'bell', 'letter'], quote: '“I swore to guard it. I will guard it from you.”' },
  vessel: { name: 'The Vessel of Rot', hp: 2800, cinders: 5000, reward: ['c_fang', 'rotseed', 'sp:rotmist', 'w:rotmaw'], quote: 'Many mouths. One hunger.' },
  sovereign: { name: 'The Pale Sovereign', hp: 4400, cinders: 20000, reward: ['w:scepter'], quote: '“Kneel, little ember. Become my root.”' },
});
BOSS_INFO.hound.quote = 'It still guards the roots it was grafted to.';
BOSS_INFO.omen.quote = '“None shall pass to the Crown. None.”';
BOSS_INFO.omen.reward = ['shard', 'charmslot', 'w:omen'];
BOSS_INFO.hound.reward = ['talon', 'shard', 'w:gravetusk'];

class MetaBoss extends BossBase {
  constructor(kind, x, y, cfg) {
    super(kind, x, y);
    Object.assign(this, cfg);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO[kind].hp * NGP.hp);
    const meta = ASSETS[cfg.sheets[0] + '_meta'];
    this.sheetsArr = cfg.sheets.map(n => sheet(n, { meta }));
    this.sh = this.sheetsArr[0]; this.state = 'dormant'; this.anim = new Anim(this.sh, 'idle'); this.hover = 0;
    this.baseY = y;
  }
  canStagger() { return !this.air && !(this.state === 'attack' && ['rotburst', 'nova'].includes(this.atk)); }
  hurtbox() { if (!this.alive) return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 20, this.y - 60, this.x + 20, this.y); }
  setS(st, tag, loop = true) { this.state = st; this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, this.speed); }
  pickMove() {
    const d = Math.abs(P.x - this.x), w = this.weights(d, this.phase === 2);
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w).filter(([k, v]) => v > 0 && (k === 'walk' || k === 'backstep' || k === 'glide' || this.sh.has(k)));
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e.length ? e[0][0] : 'idle';
  }
  start(m) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.spawned = false; this.air = null; this.fired = {};
    if (m === 'walk') { this.setS('walk', this.sh.has('walk') ? 'walk' : this.sh.has('crawl') ? 'crawl' : 'glide'); this.t = rand(0.6, 1.1); return; }
    this.rangedRun = ['rain', 'lance'].includes(m) ? (this.rangedRun || 0) + 1 : 0;
    if (m === 'glide') { this.setS('glide', this.sh.has('glide') ? 'glide' : 'idle'); this.t = 1.8; const side = Math.abs(P.x - this.L) < 110 ? 1 : Math.abs(P.x - this.R) < 110 ? -1 : (Math.random() < 0.5 ? -1 : 1); this.glideTo = clamp(P.x + side * rand(70, 120), this.L + 40, this.R - 40); return; }
    if (m === 'backstep') { this.setS('backstep', this.sh.has('backstep') ? 'backstep' : 'idle', false); this.bs = { x0: this.x, t: 0 }; return; }
    if (m === 'guard') { this.setS('guard', 'guard'); this.t = rand(0.8, 1.4); return; }
    this.setS('attack', m, false);
    const wins = metaWindows(this.sh, m); this.firstActive = wins.length ? wins[0].active[0] : 4;
  }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    this.hover += dt;
    if (this.floating) this.y = this.baseY - 10 + Math.sin(this.hover * 1.6) * 3;
    if (!this.active) { this.facePlayer(); if (this.wake()) this.activate(); return; }
    if (this.introT > 0) {
      this.introT -= dt;
      if (this.state !== 'intro') { this.setS('intro', this.introTag || 'idle', false); this.onIntro && this.onIntro(); }
      if (an.done) an.hold();
      if (this.introT <= 0) { this.setS('idle', 'idle'); this.cool = 0.6; }
      return;
    }
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle':
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') break;
        if (this.cool <= 0) this.start(this.pickMove());
        else if (d > this.prefer + 40 && this.walkSpeed) { this.setS('walk', this.sh.has('walk') ? 'walk' : this.sh.has('crawl') ? 'crawl' : 'glide'); this.t = 0.4; }
        break;
      case 'walk':
        this.facePlayer(); this.t -= dt; this.cool -= dt;
        this.x = clamp(this.x + this.face * this.walkSpeed * this.speed * dt, this.L + 20, this.R - 20);
        if (this.t <= 0 || d < this.prefer) { this.setS('idle', 'idle'); this.cool = Math.min(this.cool, 0.2); }
        break;
      case 'glide': {
        this.t -= dt; this.face = this.glideTo < this.x ? -1 : 1;
        this.x = approach(this.x, this.glideTo, 170 * this.speed * dt);
        if (Math.random() < 0.4) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(10, 60), vx: 0, vy: rand(10, 30), life: 1, kind: 'petal' });
        if (this.t <= 0 || Math.abs(this.x - this.glideTo) < 4) { this.facePlayer(); this.setS('idle', 'idle'); this.cool = 0.15; }
        break;
      }
      case 'backstep': {
        this.bs.t += dt; const T = Math.max(0.3, an.total()), k = Math.min(1, this.bs.t / T);
        this.x = clamp(this.bs.x0 - this.face * 80 * Math.sin(k * Math.PI / 2), this.L + 20, this.R - 20);
        if (an.done || k >= 1) { if (this.pendingPhase) return this.enterPhase2(); this.start(this.phase === 2 && Math.random() < 0.5 ? (this.sh.has('rotburst') ? 'thrust' : 'lance') : this.pickMove()); }
        break;
      }
      case 'guard': {
        this.facePlayer(); this.t -= dt;
        if (this.guardHit) { this.guardHit = false; this.start('thrust'); break; }
        if (this.t <= 0) { this.setS('idle', 'idle'); this.cool = 0.2; }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { if (this.pendingPhase) this.enterPhase2(); else { this.setS('idle', 'idle'); this.cool = 0.3; } }
        break;
      case 'dead':
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-40, 40), y: this.y - rand(0, 100), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: this.deathParticle || 'gold' });
        if (an.done) an.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp * this.p2at && this.alive && !this.pendingPhase) {
      if (['attack', 'stagger', 'backstep'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    this.ambient && this.ambient(dt);
    this.x = clamp(this.x, this.L, this.R);
  }
  hit(info) {
    if (this.state === 'guard' && !info.crit && info.kind !== 'heavy' && info.dir === -this.face && info.melee) {
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); P.vx = -P.face * 100; P.st -= 10; hitstop = 0.06;
      this.stance += info.poise * 0.5; this.guardHit = true; return;
    }
    super.hit(info);
  }
  enterPhase2() {
    this.phase = 2; this.speed = this.p2speed || 1.15; this.pendingPhase = false; this.stance = 0; this.air = null;
    if (this.sheetsArr[1] && this.sheetsArr[1].ok) { this.sh = this.sheetsArr[1]; }
    this.facePlayer(); this.onPhase2 && this.onPhase2();
    this.start(this.p2tag || 'idle');
    if (this.state === 'attack') this.p2roar = true;
    bossPhase2Scene(this);
  }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, M = this.moves[a] || {}, wins = metaWindows(sh, a);
    if (an.i < this.firstActive - 1 || (M.track && M.track.includes(an.i))) this.facePlayer();
    // telegraph glint
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    else if (!tel && an.changed && an.i === Math.max(0, this.firstActive - 2)) { spawnFx('telegraph', this.x + this.face * 20, this.y - 50, this.face); sfx.glint(); }
    if (M.leap) this.updateLeap(dt, M);
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) {
        sfx.bossSwing();
        if (M.fx) { const q = metaRect(sh, this, w.hit); spawnFx(fxOr(M.fx, 'boss_slash'), (q.x0 + q.x1) / 2, (q.y0 + q.y1) / 2, this.face); }
        if (M.shake) shake = Math.max(shake, M.shake);
      }
      if (M.step) this.x = clamp(this.x + this.face * M.step * dt, this.L, this.R);
      if (this.hitIds.has(wi) || !w.hit) return;
      const r = metaRect(sh, this, w.hit);
      if (M.body) { if (this.face > 0) r.x0 = Math.min(r.x0, this.x); else r.x1 = Math.max(r.x1, this.x); }
      if (overlap(r, playerHurtbox())) {
        const dmg = (M.dmg ? (M.dmg[wi] ?? M.dmg[0]) : 40) * (this.phase === 2 ? 1.1 : 1) * NGP.dmg;
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: !!M.parry, src: this, rot: M.rot })) this.hitIds.add(wi);
      }
    });
    // scripted per-frame events (projectiles, hazards)
    if (M.on) for (const [fi, fn] of Object.entries(M.on)) if (an.changed && an.i === +fi && !this.fired[fi]) { this.fired[fi] = true; fn.call(this); }
    const sp = sh.meta && sh.meta.spawn && sh.meta.spawn[a];
    if (sp && M.spawn && !this.spawned && an.i >= sp.frame) { this.spawned = true; M.spawn.call(this, metaPoint(sh, this, sp.at)); }
    if (an.done) {
      this.air = null; if (!this.floating) this.y = this.floor;
      if (this.pendingPhase) return this.enterPhase2();
      const d = Math.abs(P.x - this.x), chain = this.chains && this.chains[a];
      if (chain && this.chain < (this.phase === 2 ? 2 : 1) && Math.random() < (this.phase === 2 ? 0.6 : 0.3)) {
        this.chain++; const nx = typeof chain === 'function' ? chain.call(this, d) : chain; if (nx) return this.start(nx);
      }
      this.chain = 0; this.setS('idle', 'idle');
      this.cool = this.phase === 1 ? rand(...this.cool1) : rand(...this.cool2);
    }
  }
  updateLeap(dt, M) {
    const an = this.anim, wins = metaWindows(this.sh, this.atk), land = wins.length ? wins[0].active[0] : an.n - 3;
    if (an.changed && an.i === M.leap && !this.air) {
      let T = 0; for (let i = an.i; i < land; i++) T += an.ms(i); T = Math.max(0.2, T / 1000 / an.speed);
      this.air = { x0: this.x, tx: clamp(P.x - this.face * 16, this.L + 20, this.R - 20), t: 0, T };
    }
    if (this.air) {
      this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
      this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * (M.height || 70);
      if (k >= 1) { this.air = null; this.y = this.floor; shake = 8; sfx.boom(); spawnFx('shockwave', this.x + this.face * 10, this.floor, 1); M.onLand && M.onLand.call(this); }
    }
  }
  die() {
    this.state = 'dead'; this.anim.set(this.sh.has('death') ? 'death' : 'stagger', false, 1); this.air = null; if (!this.floating) this.y = this.floor;
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    this.onDeath ? this.onDeath() : (victoryBanner = { text: this.victory || 'ENEMY FELLED', t: 0 });
    this.rewards();
  }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (!this.sh.ok) { g.fillStyle = '#806a70'; g.fillRect(Math.round(this.x - 24), Math.round(this.y - 60), 48, 60); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
  }
}
function lightPillar(x, floor, delay, dmg) {
  hazards.push({ x, y: floor, w: 18, h: 120, dmg: BOSS_DMG * dmg * NGP.dmg, id: ++hazardId, life: 5, delay, fx: null,
    onStart: h => { h.fx = spawnFx(fxOr('lightpillar', 'pillar'), h.x, floor, 1, null, { bottom: true }); if (!h.fx) h.life = 0; },
    update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } const i = h.fx.anim.i; if (i === 3 && h.fx.anim.changed) { sfx.pillar(); shake = Math.max(shake, 2.5); } if (i >= 3 && i <= 5) addLight(h.x, floor - 50, 70, '255,240,200', 1); },
    active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5 });
}
function rootSpikeAt(x, floor, delay, dmg) {
  hazards.push({ x, y: floor, w: 14, h: 56, dmg: BOSS_DMG * dmg * NGP.dmg, id: ++hazardId, life: 3, delay, fx: null,
    onStart: h => { h.fx = spawnFx(fxOr('root_spike', 'pillar'), h.x, h.y, 1); if (!h.fx) h.life = 0; else sfx.pillar(); },
    update: h => { if (!h.fx || h.fx.anim.done) h.life = 0; },
    active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5 });
}

// ================================================================== Ser Kalden, the Oathless
function makeKalden(x, y) {
  const K = new MetaBoss('kalden', x, y, {
    sheets: ['kalden', 'kalden_p2'], stanceMax: 300, walkSpeed: 46, prefer: 56, p2at: 0.5, p2speed: 1.15, p2tag: 'rotburst', critRange: 44,
    introTag: 'guard', cool1: [0.8, 1.4], cool2: [0.45, 0.9], victory: 'OATH FULFILLED', deathParticle: 'gold',
    onIntro() { sfx.roar(); },
    weights(d, p2) {
      if (d < 70) return { combo: 3, thrust: 0.8, guard: p2 ? 0.4 : 1.2, backstep: 0.9, rotburst: p2 ? 1.4 : 0, leap: 0.3 };
      if (d < 160) return { thrust: 2.5, leap: 1.6, walk: 1.2, combo: 0.5, rotburst: p2 ? 0.8 : 0 };
      return { leap: 2.6, walk: 2, thrust: 1 };
    },
    chains: { combo(d) { return d < 80 ? (this.phase === 2 ? 'rotburst' : 'thrust') : 'leap'; }, thrust: 'combo', leap: 'combo' },
    moves: {
      combo: { dmg: [36, 36, 48], parry: true, step: 70, fx: 'kalden_slash' },
      thrust: { dmg: [54], parry: true, step: 230, fx: 'thrust' },
      leap: { dmg: [58], leap: 2, height: 80, onLand() { if (this.phase === 2) for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.floor, vx: dd * 160, w: 14, h: 12, dmg: BOSS_DMG * 30, rot: 25, id: ++hazardId, life: 1.2, wave: true, dir: dd, color: 'rot' }); } },
      rotburst: { dmg: [46], rot: 60, shake: 8, on: { 6() { sfx.fire(); spawnFx(fxOr('rotmist', 'shockwave'), this.x, this.floor, 1, null, { bottom: true }); for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.floor, vx: dd * 150, w: 16, h: 14, dmg: BOSS_DMG * 32, rot: 30, id: ++hazardId, life: 1.6, wave: true, dir: dd, color: 'rot' }); } } },
    },
    wake() { return P.x > 4 * TILE + 24; },
    ambient() { if (this.phase === 2 && Math.random() < 0.3) particles.push({ x: this.x + rand(-16, 16), y: this.y - rand(10, 50), vx: 0, vy: -rand(10, 25), life: 0.8, kind: 'spore' }); addLight(this.x, this.y - 30, 60, this.phase === 2 ? '150,210,90' : '160,220,230', 0.6); },
  });
  return K;
}

// ================================================================== The Vessel of Rot
function makeVessel(x, y) {
  return new MetaBoss('vessel', x, y, {
    sheets: ['vessel'], stanceMax: 420, walkSpeed: 34, prefer: 70, p2at: 0.5, p2speed: 1.2, p2tag: 'spew', critRange: 70,
    introTag: 'spew', cool1: [1.0, 1.7], cool2: [0.6, 1.1], victory: 'VESSEL SUNDERED', deathParticle: 'spore',
    onIntro() { sfx.roar(); shake = 8; },
    weights(d, p2) {
      if (d < 80) return { slam: 2.5, sweep: 2, spew: p2 ? 1 : 0.4 };
      return { walk: 2, spew: 1.8, slam: 0.6 };
    },
    chains: { slam: 'sweep', sweep: 'slam', spew: 'slam' },
    moves: {
      slam: { dmg: [60], rot: 30, body: true, shake: 8, on: { 5() { const px = this.x + this.face * 50; spawnFx('shockwave', px, this.floor, 1); hazards.push({ x: px, y: this.floor, w: 56, h: 8, dmg: 6, rot: 24, tick: 0.5, id: ++hazardId, life: 5, pool: true }); } } },
      sweep: { dmg: [44], rot: 20, shake: 4 },
      spew: { dmg: [], spawn(at) {
        const n = this.phase === 2 ? 7 : 5;
        for (let k = 0; k < n; k++) { const T = 0.7 + k * 0.06, tx = P.x + (k - (n - 1) / 2) * 34; projectiles.push({ owner: 'enemy', kind: 'rotglob', x: at.x, y: at.y, vx: (tx - at.x) / T, vy: -200 - k * 10, g: 470, dmg: BOSS_DMG * 30 * NGP.dmg, rot: 35, life: 3, r: 6, t: 0, id: ++hazardId, pool: true }); }
        sfx.fire(); shake = 4;
      } },
    },
    wake() { return P.ground; },
    ambient() { if (Math.random() < 0.4) particles.push({ x: this.x + rand(-60, 60), y: this.y - rand(10, 90), vx: 0, vy: -rand(5, 20), life: 1, kind: 'spore' }); addLight(this.x, this.y - 50, 90, '170,220,90', 0.5); },
  });
}

// ================================================================== The Pale Sovereign (final boss)
// Reworked in web/src/26_sovereign2.js: 15 attacks across two phases, then the phase-3 beast
// ("The Pale Root, Unbound"). Her final death there still ends the game.
function makeSovereign(x, y) { return makeSovereign2(x, y); }

// ================================================================== The Head Librarian (Archives mini-boss)
BOSS_INFO.librarian = { name: 'The Head Librarian', hp: 1300, cinders: 2600, reward: ['shard', 'emberstone', 'emberstone'], quote: 'Silence in the stacks.' };
let darkT = 0;   // the Librarian's snuff: the room goes black except for lantern light
function makeLibrarian(x, y) {
  return new MetaBoss('librarian', x, y, {
    sheets: ['head_librarian'], stanceMax: 260, walkSpeed: 34, prefer: 56, p2at: 0.5, p2speed: 1.2, p2tag: 'snuff', critRange: 40,
    introTag: 'idle', cool1: [0.9, 1.6], cool2: [0.6, 1.1], victory: 'THE STACKS FALL SILENT', deathParticle: 'ink',
    weights(d, p2) {
      if (d < 70) return { swing: 3, slam: 1.6, snuff: darkT > 0 ? 0 : (p2 ? 1.2 : 0.5) };
      return { walk: 2.2, snuff: darkT > 0 ? 0 : 1, slam: 0.4 };
    },
    chains: { swing: d => d < 70 ? 'slam' : null, slam: 'swing' },
    moves: {
      swing: { dmg: [40, 46], parry: true, step: 50 },
      slam: { dmg: [58], shake: 7, on: { 6() { spawnFx('shockwave', this.x + this.face * 30, this.floor, 1); sfx.boom(); } } },
      snuff: { dmg: [], spawn() { darkT = this.phase === 2 ? 8 : 6; sfx.roar(); flashScreen = 0.2; toast('The lights go out.', 2); } },
    },
    wake() { return P.x < room.pw - 4 * TILE - 24; },
    ambient() { addLight(this.x + this.face * 14, this.y - 30, darkT > 0 ? 70 : 50, '190,160,255', 1); },
    onDeath() { darkT = 0; victoryBanner = { text: 'THE STACKS FALL SILENT', t: 0 }; },
  });
}
