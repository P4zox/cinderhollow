// ------------------------------------------------------------------ bosses
let boss = null;
const BOSS_DMG = 0.7;   // global boss damage scale (tuned down on request)
const BOSS_INFO = {
  hound: { name: 'Gravetusk, the Rootbound Hound', hp: 1650, cinders: 3000, reward: ['talon', 'shard'] },
  omen: { name: 'Morvain, the Ashen Omen', hp: 3200, cinders: 12000, reward: ['shard'] },
};
class BossBase {
  constructor(kind, x, y) {
    const I = BOSS_INFO[kind];
    Object.assign(this, { kind, name: I.name, x, y, floor: y, face: -1, hp: I.hp, maxHp: I.hp, displayHp: I.hp, active: false, boss: true,
                          phase: 1, speed: 1, poise: 0, stance: 0, flash: 0, hitIds: new Set(), dmgShown: 0, dmgT: 0, cool: 1, chain: 0,
                          introT: 0, bleed: 0, critRange: 60 });
  }
  get alive() { return this.state !== 'dead'; }
  get L() { return TILE + 20; }
  get R() { return room.pw - TILE - 20; }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  activate() {
    if (this.active || this.cutting) return;
    if (bossCutsceneStart(this)) return;
    this.active = true; this.introT = 2.6; bossBanner = { name: this.name, t: 0 };
    sfx.roar(); shake = 6;
  }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  // one critical per stagger; the stagger is held just long enough for the riposte to land, never extended
  onCritStart() { this.critDone = true; this.t = Math.max(this.t || 0, 0.9); }
  hit(info) {
    if (!this.alive || !this.active) { if (!this.active) this.activate(); return; }
    let dmg = Math.round(info.dmg * (this.state === 'stagger' && !info.crit ? 1.3 : 1));
    this.hp = Math.max(0, this.hp - dmg); this.flash = 1;
    this.dmgShown = this.dmgT > 0 ? this.dmgShown + dmg : dmg; this.dmgT = 2.2;
    hitstop = Math.max(hitstop, info.big ? 0.1 : 0.05); shake = Math.max(shake, info.big ? 4 : 2);
    (info.big ? sfx.bigHit : sfx.hit)();
    spawnFx(info.big ? fxOr('parry_spark', 'hit') : 'hit', info.x, info.y, info.dir);
    for (let i = 0; i < (info.big ? 10 : 5); i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 90), vy: -rand(20, 90), g: 260, life: rand(0.3, 0.6), kind: info.fire ? 'fire' : 'spark' });
    if (info.rotDot) this.rotT = 4;
    if (info.bleed) {
      this.bleed += info.bleed * 0.7;
      if (this.bleed >= 100) { this.bleed = 0; const bd = Math.round(this.maxHp * 0.06 + 40); this.hp = Math.max(0, this.hp - bd); this.dmgShown += bd; sfx.bleed(); spawnFx(fxOr('bleed', 'blood'), info.x, info.y, info.dir); }
    }
    if (this.hp <= 0) return this.die();
    if (info.crit) { this.stance = 0; this.t = Math.min(this.t || 0, 0.45); return; }
    if (this.stanceImmune > 0 || this.state === 'stagger') return;
    this.stance += info.poise;
    if (this.stance >= this.stanceMax && this.canStagger()) this.stagger();
  }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 90; if (this.stance >= this.stanceMax && this.canStagger()) this.stagger(); }
  stagger() {
    this.critDone = false; this.stanceImmune = 7; this.staggers = (this.staggers || 0) + 1;
    this.stanceMax = Math.min(this.stanceMax * 1.15, (this.stanceBase || (this.stanceBase = this.stanceMax)) * 2);
    this.stance = 0; this.state = 'stagger'; this.anim.set('stagger', false, 1); this.t = 2.0; this.chain = 0; this.air = null; this.y = this.floor;
    sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 50, this.face);
  }
  commonUpdate(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt; this.stance = Math.max(0, this.stance - dt * 5);
    if (this.state !== 'stagger') this.stanceImmune = Math.max(0, (this.stanceImmune || 0) - dt);
    if (this.rotT > 0 && this.alive && this.active) {
      this.rotT -= dt; const d = this.maxHp * 0.006 * dt; this.hp = Math.max(1, this.hp - d); this.dmgShown += d; this.dmgT = Math.max(this.dmgT, 0.5);
      if (Math.random() < 0.4) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(10, 80), vx: 0, vy: -rand(5, 20), life: 0.6, kind: 'spore' });
    } this.bleed = Math.max(0, this.bleed - dt * 5);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    this.camX = this.x;
  }
  rewards() {
    SAVE.flags['boss:' + this.kind] = 1;
    gainCinders(BOSS_INFO[this.kind].cinders, this.x, this.y - 40);
    const items = BOSS_INFO[this.kind].reward;
    items.forEach((id, i) => setTimeout(() => grantItem(id, P.x, P.y - 20), 2600 + i * 2400));
    saveGame();
  }
}

// ================================================================== Gravetusk, the Rootbound Hound
class Hound extends BossBase {
  constructor(x, y) {
    super('hound', x, y);
    this.sheets = [sheet('hound'), sheet('hound_p2', { meta: ASSETS.hound_meta })];
    this.sh = this.sheets[0]; this.state = 'dormant'; this.anim = new Anim(this.sh, 'idle'); this.stanceMax = 320;
  }
  canStagger() { return !this.air && this.state !== 'howl'; }
  hurtbox() { if (!this.alive) return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 50, this.y - 64, this.x + 50, this.y); }
  setS(st, tag, loop = true) { this.state = st; this.anim.set(tag, loop, this.speed); }
  choose() {
    const d = Math.abs(P.x - this.x), p2 = this.phase === 2, behind = (P.x - this.x) * this.face < 0;
    let w;
    if (behind && d < 90) w = { sweep: 4, bite: 0.3 };
    else if (d < 80) w = { bite: 3, sweep: 1.6, pounce: 0.3, howl: p2 ? 0.6 : 0.3 };
    else if (d < 190) w = { pounce: 3, bite: 0.8, charge: 1, howl: p2 ? 1.2 : 0.7, prowl: 0.8 };
    else w = { charge: 3, pounce: 1.5, howl: p2 ? 1.6 : 1, prowl: 1 };
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return 'bite';
  }
  start(m) {
    this.facePlayer(); this.last = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.atk = m; this.air = null; this.spawned = false;
    if (m === 'prowl') { this.setS('prowl', 'prowl'); this.t = rand(0.6, 1.1); return; }
    if (m === 'charge') { this.setS('charge', 'charge'); this.t = 1.5; this.chargeDir = this.face; sfx.roar(); spawnFx('telegraph', this.x + this.face * 50, this.y - 50, this.face); return; }
    if (m === 'howl') { this.setS('howl', 'howl', false); return; }
    this.setS('attack', m, false);
  }
  update(dt) {
    this.commonUpdate(dt);
    const sh = this.sh, an = this.anim; an.update(dt);
    if (!this.active) { this.facePlayer(); if (P.x > 4 * TILE + 24 && P.x < room.pw - 3 * TILE) this.activate(); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.state !== 'intro') { this.setS('intro', 'howl', false); sfx.howl(); } if (an.done) an.hold(); if (this.introT <= 0) { this.setS('idle', 'idle'); this.cool = 0.6; } return; }
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle':
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') break;
        if (this.cool <= 0) this.start(this.choose());
        else if (d > 120) { this.setS('prowl', 'prowl'); this.t = 0.5; }
        break;
      case 'prowl':
        this.facePlayer(); this.t -= dt; this.cool -= dt;
        this.x = clamp(this.x + this.face * 70 * this.speed * dt, this.L + 30, this.R - 30);
        if (this.t <= 0 || d < 70) { this.setS('idle', 'idle'); this.cool = Math.min(this.cool, 0.15); }
        break;
      case 'attack': this.updateAttack(dt); break;
      case 'charge': {
        this.t -= dt;
        this.x += this.chargeDir * 250 * this.speed * dt;
        if (an.changed && an.i % 2 === 0) { shake = Math.max(shake, 2); sfx.step(); particles.push({ x: this.x - this.chargeDir * 40, y: this.y, vx: -this.chargeDir * 40, vy: -rand(10, 40), life: 0.5, kind: 'dust' }); }
        const w = metaWindows(sh, 'charge')[0];
        const r = w ? metaRect(sh, this, w.hit) : rect(this.x + this.face * 20, this.y - 60, this.x + this.face * 75, this.y);
        if (!this.hitIds.has(0) && overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * 50, this.chargeDir, this.atkId)) { this.hitIds.add(0); P.vx = this.chargeDir * 200; }
        const pastPlayer = (this.x - P.x) * this.chargeDir > 70;
        if (this.x < this.L + 20 || this.x > this.R - 20) {
          this.x = clamp(this.x, this.L + 20, this.R - 20); shake = 9; sfx.boom();
          spawnFx('shockwave', this.x + this.chargeDir * 40, this.y, 1);
          if (this.phase === 2) for (let k = 0; k < 4; k++) this.rootSpike(this.x - this.chargeDir * (60 + k * 40), 0.2 + k * 0.12);
          this.setS('idle', 'idle'); this.cool = 0.9;
        } else if (this.t <= 0 || pastPlayer) { this.setS('idle', 'idle'); this.cool = rand(0.5, 0.9); }
        break;
      }
      case 'howl':
        if (an.changed && an.i === Math.floor(an.n * 0.4)) {
          sfx.howl(); shake = 8; flashScreen = 0.3; spawnFx('roar_ring', this.x + this.face * 30, this.y - 60, 1);
          const n = this.phase === 2 ? 7 : 4;
          if (this.phase === 2) for (let k = 0; k < n; k++) this.rootSpike(this.x + this.face * (50 + k * 34), 0.25 + k * 0.1);
          for (let k = 0; k < (this.phase === 2 ? 3 : 3); k++) this.rootSpike(clamp(P.x + (k - 1) * 30 * (this.phase === 2 ? 1 : 0) + rand(-6, 6), this.L, this.R), 0.3 + k * (this.phase === 2 ? 0.12 : 0.45));
        }
        if (an.i >= Math.floor(an.n * 0.4) && Math.random() < 0.5) particles.push({ x: this.x + rand(-50, 50), y: this.y - rand(20, 80), vx: 0, vy: -rand(20, 60), life: 1, kind: 'root' });
        if (an.done) { if (this.pendingPhase) this.enterPhase2(); else { this.setS('idle', 'idle'); this.cool = 0.5; } }
        break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { if (this.pendingPhase) this.enterPhase2(); else { this.setS('idle', 'idle'); this.cool = 0.3; } }
        break;
      case 'dead':
        if (an.i >= 3 && Math.random() < 0.5) particles.push({ x: this.x + rand(-50, 50), y: this.y - rand(0, 60), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: 'gold' });
        if (an.done) an.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp * 0.55 && this.alive && !this.pendingPhase) {
      if (['attack', 'charge', 'stagger', 'howl'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    if (this.phase === 2 && Math.random() < 0.3) particles.push({ x: this.x + rand(-40, 40), y: this.y - rand(20, 70), vx: 0, vy: -rand(20, 40), life: 0.8, kind: 'fire' });
    addLight(this.x + this.face * 40, this.y - 50, this.phase === 2 ? 90 : 60, this.phase === 2 ? '255,150,60' : '255,210,120', 0.8);
    this.x = clamp(this.x, this.L, this.R);
  }
  enterPhase2() {
    this.phase = 2; this.speed = 1.15; this.pendingPhase = false; this.stance = 0;
    if (this.sheets[1].ok) { this.sh = this.sheets[1]; const a = this.anim; this.anim = new Anim(this.sh, a.tag, a.loop, a.speed); }
    this.facePlayer(); this.setS('howl', 'howl', false); this.cool = 0.4;
    toast('The roots ignite'); bossPhase2Scene(this);
  }
  rootSpike(x, delay) {
    const id = ++hazardId;
    hazards.push({ x, y: this.floor, w: 14, h: 56, dmg: BOSS_DMG * 40, id, life: 3, delay, fx: null,
      onStart: h => { h.fx = spawnFx(fxOr('root_spike', 'pillar'), h.x, h.y, 1); if (!h.fx) h.life = 0; else sfx.pillar(); },
      update: h => { if (!h.fx || h.fx.anim.done) h.life = 0; else if (h.fx.anim.i === 3 && h.fx.anim.changed) shake = Math.max(shake, 2.5); },
      active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5 });
    // ground crack telegraph
    hazards.push({ x, y: this.floor, w: 0, h: 0, dmg: BOSS_DMG * 0, life: delay + 0.1, delay: 0, active: () => false,
      update: h => { if (Math.random() < 0.6) particles.push({ x: h.x + rand(-6, 6), y: h.y - 1, vx: 0, vy: -rand(10, 40), life: 0.4, kind: 'root' }); } });
  }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, wins = metaWindows(sh, a);
    const first = wins.length ? wins[0].active[0] : 3;
    if (an.i < first - 1) this.facePlayer();
    if (an.changed && an.i === Math.max(0, first - 2)) {
      const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[a];
      const p = tel ? metaPoint(sh, this, tel.at) : { x: this.x + this.face * 60, y: this.y - 50 };
      spawnFx('telegraph', p.x, p.y, this.face); sfx.glint();
    }
    if (a === 'pounce') {
      if (an.changed && an.i === Math.max(1, first - 1) && !this.air) {
        let T = 0; for (let i = an.i; i <= (wins[0] ? wins[0].active[1] : an.i + 3); i++) T += an.ms(i);
        T = T / 1000 / an.speed;
        this.air = { x0: this.x, tx: clamp(P.x - this.face * 20, this.L + 40, this.R - 40), t: 0, T };
        sfx.bossSwing();
      }
      if (this.air) {
        this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
        this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * 60;
        if (k >= 1) {
          this.air = null; this.y = this.floor; shake = 9; sfx.boom();
          spawnFx('shockwave', this.x + this.face * 30, this.floor, 1); spawnFx('dust', this.x, this.floor, 1);
          hazards.push({ x: this.x + this.face * 30, y: this.floor, w: 110, h: 22, dmg: BOSS_DMG * 34, id: ++hazardId, life: 0.15 });
          if (this.phase === 2) for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.floor, vx: dd * 170, w: 14, h: 14, dmg: BOSS_DMG * 30, id: ++hazardId, life: 1.2, wave: true, dir: dd, color: 'root' });
        }
      }
    }
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) {
        sfx.bossSwing();
        if (a === 'bite') { this.x = clamp(this.x + this.face * 26, this.L, this.R); const q = metaRect(sh, this, w.hit); spawnFx(fxOr('bite', 'hit'), this.face > 0 ? q.x1 - 14 : q.x0 + 14, (q.y0 + q.y1) / 2, this.face); }
        if (a === 'sweep') { shake = Math.max(shake, 3); for (let i = 0; i < 10; i++) particles.push({ x: this.x + rand(-70, 70), y: this.floor - rand(0, 6), vx: rand(-80, 80), vy: -rand(20, 70), g: 300, life: 0.5, kind: 'dust' }); }
      }
      if (this.hitIds.has(wi) || !w.hit) return;
      const r = metaRect(sh, this, w.hit);
      if (a === 'bite' || a === 'pounce') { if (this.face > 0) r.x0 = Math.min(r.x0, this.x); else r.x1 = Math.max(r.x1, this.x); }
      if (overlap(r, playerHurtbox())) {
        const dmg = { bite: 55, pounce: 62, sweep: 44 }[a] * (this.phase === 2 ? 1.1 : 1);
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: a === 'bite', src: this })) this.hitIds.add(wi);
      }
    });
    if (an.done) {
      this.air = null; this.y = this.floor;
      if (this.pendingPhase) return this.enterPhase2();
      const d = Math.abs(P.x - this.x);
      if (this.chain < (this.phase === 2 ? 2 : 1) && Math.random() < (this.phase === 2 ? 0.65 : 0.35)) {
        this.chain++;
        const next = { bite: d < 80 ? (Math.random() < 0.5 ? 'bite' : 'sweep') : 'pounce', pounce: d < 80 ? 'bite' : 'charge', sweep: d < 90 ? 'bite' : 'pounce' }[a];
        if (next) return this.start(next);
      }
      this.chain = 0; this.setS('idle', 'idle'); this.cool = this.phase === 1 ? rand(0.9, 1.5) : rand(0.5, 0.95);
    }
  }
  die() {
    this.state = 'dead'; this.anim.set('death', false, 1); this.air = null; this.y = this.floor;
    hazards = []; shake = 12; hitstop = 0.3; slowmo = 1.4; flashScreen = 0.6; sfx.roar();
    victoryBanner = { text: 'BEAST FELLED', t: 0 }; sfx.felled();
    this.rewards();
  }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'dormant') opt.alpha = 1;
    if (!this.sh.ok) { g.fillStyle = '#6a6070'; g.fillRect(Math.round(this.x - 60), Math.round(this.y - 70), 120, 70); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
  }
}

// ================================================================== Morvain, the Ashen Omen (reworked by agent M)
// Twenty moves over three sheets (same 176x128 frame + anchor, swapped per move):
//   boss(_p2)   idle walk backstep combo thrust leap spin cast eruption roar stagger death      (art/gen_boss.py)
//   omen_a(_p2) feint rising sweep grab impale dash drag                                         (art/omen_moves.py)
//   omen_b(_p2) plunge throw counter ward flurry invoke
// Branching strings (OMEN_CHAIN, mid-combo mixups), reactions (flask use, button mashing, spells at range),
// and at half health the Throne of Ash dissolves into the Eclipsed Crown, whose army fights too (25_omen2.js).
const OMEN_SHEET = { feint: 'a', rising: 'a', sweep: 'a', grab: 'a', impale: 'a', dash: 'a', drag: 'a',
                     plunge: 'b', throw: 'b', counter: 'b', ward: 'b', flurry: 'b', invoke: 'b' };
// dmg per hit group · groups: frame -> group · track: frames that turn to face you · steps: px moved during a frame
// lunge: frame whose step closes the gap · parry: can be parried · bothSides: hits behind him too · custom: frames with bespoke hit logic
const OMEN = {
  combo: { dmg: [45, 45, 58], groups: { 2: 0, 6: 1, 10: 2 }, track: [0, 1, 4, 5, 8], steps: { 2: 22, 6: 18, 10: 34 }, fx: { 2: 'arc_down', 6: 'arc_up', 10: 'arc_wide' }, parry: true },
  thrust: { dmg: [62], track: [0, 1, 2], steps: { 4: 20 }, lunge: 3, fx: { 3: 'thrust' }, parry: true },
  leap: { dmg: [66], track: [0, 1] },
  spin: { dmg: [52], track: [0, 1, 2], steps: { 3: 14, 4: 14, 5: 14 }, fx: { 3: 'spin' }, bothSides: true },
  cast: { dmg: [], track: [0, 1, 2, 3, 4, 5] },
  eruption: { dmg: [44], track: [0, 1, 2] },
  feint: { dmg: [64], groups: { 5: 0, 6: 0 }, track: [0, 1, 2, 3, 4], lunge: 5, lungeMax: 120, parry: true },
  rising: { dmg: [50, 60], groups: { 2: 0, 3: 0, 6: 1 }, track: [0, 1, 3, 4], steps: { 2: 16 }, parry: true },
  sweep: { dmg: [48], groups: { 2: 0, 3: 0 }, track: [0, 1], lunge: 2, lungeMax: 110, bothSides: true },
  grab: { dmg: [], track: [0, 1], lunge: 2, lungeMax: 90, custom: [2, 3] },
  impale: { dmg: [], track: [], custom: [] },
  dash: { dmg: [56, 48], groups: { 3: 1 }, track: [0, 1, 3], custom: [2] },
  drag: { dmg: [55], groups: { 5: 0 }, track: [0, 1, 2, 3, 4], steps: { 5: 18 } },
  plunge: { dmg: [62], track: [0, 1] },
  throw: { dmg: [], track: [0, 1], custom: [2] },
  counter: { dmg: [72], groups: { 4: 0, 5: 0 }, track: [0], bothSides: true },
  ward: { dmg: [], track: [0] },
  flurry: { dmg: [26, 26, 26, 26, 30, 54], groups: { 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 9: 5 }, track: [0, 1, 7, 8],
            steps: { 2: 16, 3: 8, 4: 16, 5: 8, 6: 14, 9: 26 }, parry: true },
  invoke: { dmg: [], track: [0, 1, 2, 3] },
};
const OMEN_FX_PIVOT = { arc_down: [68, 48], arc_up: [60, 50], arc_wide: [140, 30], spin: [104, 46], thrust: [124, 16] };
// branching follow-ups (d = distance to you); a string can run 2-3 deep in phase 2
const OMEN_CHAIN = {
  combo: (b, d) => d < 70 ? b.any(['spin', 'sweep', 'rising']) : b.any(['thrust', 'dash']),
  thrust: (b, d) => d < 80 ? b.any(['spin', 'flurry', 'sweep']) : b.any(['leap', 'dash']),
  leap: (b, d) => d < 80 ? b.any(['combo', 'sweep', 'grab']) : 'thrust',
  spin: (b, d) => d < 90 ? b.any(['thrust', 'feint']) : 'dash',
  feint: (b, d) => d < 80 ? b.any(['sweep', 'combo', 'grab']) : 'thrust',
  rising: (b, d) => d < 80 ? b.any(['spin', 'sweep']) : 'thrust',
  sweep: (b, d) => d < 80 ? b.any(['rising', 'feint', 'grab']) : 'dash',
  dash: (b, d) => b.phase === 2 && b.any([0, 1]) ? 'dash' : d < 80 ? b.any(['rising', 'flurry']) : 'cast',
  drag: (b, d) => d < 90 ? b.any(['thrust', 'spin']) : 'leap',
  plunge: (b, d) => d < 90 ? b.any(['sweep', 'spin']) : 'dash',
  flurry: (b, d) => d < 80 ? b.any(['grab', 'spin']) : 'dash',
  counter: (b, d) => d < 100 ? 'thrust' : 'dash',
  cast: (b, d) => d < 90 ? 'spin' : b.any(['eruption', 'dash']),
  eruption: (b, d) => d < 90 ? 'sweep' : b.any(['cast', 'leap', 'plunge']),
  invoke: (b, d) => b.any(['dash', 'leap']),
  ward: (b, d) => d < 90 ? 'thrust' : 'dash',
};
const OMEN_COOL = { grab: 7, throw: 6, counter: 5, ward: 7, invoke: 7, plunge: 3, drag: 4 };
// light sounds built from the core synth (distinct tells per family)
const omSfx = {
  grab: () => { tone(160, 0.5, 0.12, 'sawtooth', 2.2); tone(640, 0.35, 0.06, 'triangle', 0.6); },
  stance: () => { tone(1175, 0.5, 0.07, 'triangle', 1.0); tone(1568, 0.6, 0.05, 'sine', 1.0, 0.08); },
  ward: () => { tone(392, 0.8, 0.08, 'sine', 1.2); tone(784, 0.8, 0.05, 'triangle', 1.2, 0.05); },
  dash: () => { noise(0.35, 1800, 0.8, 0.35, 'bandpass', 2.5); tone(330, 0.2, 0.08, 'sawtooth', 3); },
  blade: () => noise(0.18, 1400, 1.2, 0.2, 'bandpass', 0.6),
  lane: () => { tone(98, 1.1, 0.14, 'sawtooth', 1.8); noise(1.0, 400, 0.5, 0.18, 'lowpass', 1.5); },
  beam: () => { tone(880, 0.7, 0.07, 'sine', 0.5); tone(1320, 0.6, 0.04, 'triangle', 0.5, 0.1); },
};
class Omen extends BossBase {
  constructor(x, y) {
    super('omen', x, y);
    this.meta = ASSETS.boss_meta || { hurtbox: [70, 28, 53, 100], attacks: {}, anchor: [100, 128] };
    this.SH = {
      base: [sheet('boss', { native: -1 }), sheet('boss_p2', { native: -1, meta: this.meta })],
      a: [sheet('omen_a', { native: -1 }), sheet('omen_a_p2', { native: -1, meta: ASSETS.omen_a_meta })],
      b: [sheet('omen_b', { native: -1 }), sheet('omen_b_p2', { native: -1, meta: ASSETS.omen_b_meta })],
    };
    this.sheets = this.SH.base;
    this.sh = this.sheets[0]; this.state = 'dormant'; this.anim = new Anim(this.sh, 'idle'); this.stanceMax = 400; this.spears = [];
    this.hitLog = []; this.recent = []; this.cds = {}; this.lines = []; this.cres = []; this.blade = null; this.mark = null;
  }
  canStagger() { return !this.air && this.state !== 'roar' && !this.caught && !(this.state === 'attack' && ['impale', 'dash'].includes(this.atk)); }
  hurtbox() { return this.alive ? metaRect(this.sh, this, this.meta.hurtbox) : null; }
  get M() { return this.sh.meta || this.meta; }
  sheetFor(tag) { const set = this.SH[OMEN_SHEET[tag] || 'base'], s = set[this.phase - 1]; return s && s.ok && s.has(tag) ? s : set[0]; }
  has(tag) { const s = this.sheetFor(tag); return s.ok && s.has(tag); }
  setB(st, tag, loop = true) {
    this.state = st; if (!this.has(tag)) tag = 'idle';
    const s = this.sheetFor(tag);
    if (s !== this.sh) { this.sh = s; this.anim = new Anim(s, tag, loop, this.speed); } else this.anim.set(tag, loop, this.speed);
  }
  toBase() { const s = this.sheetFor('idle'); if (s !== this.sh) { this.sh = s; this.anim = new Anim(s, 'idle', true, 1); } }
  any(list) { return list[Math.floor(Math.random() * list.length)]; }
  pick(w) {
    const e = Object.entries(w).filter(([k, v]) => v > 0 && (k === 'walk' || k === 'backstep' || this.has(k)) && !(this.cds[k] > 0));
    if (!e.length) return 'combo';
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e[0][0];
  }
  choose(dist) {
    const p2 = this.phase === 2; let w;
    if (dist < 70) w = { combo: 1.8, spin: 1.3, feint: 1.5, sweep: 1.3, grab: 1.1, flurry: 1.2, rising: 1.1, counter: 0.6, backstep: 0.7, thrust: 0.3, eruption: p2 ? 0.6 : 0, ward: p2 ? 0.4 : 0 };
    else if (dist < 150) w = { thrust: 1.6, feint: 1.1, dash: 1.5, rising: 1.1, leap: 1.2, drag: 1.0, flurry: 0.9, grab: 0.7, eruption: 0.9, cast: 0.7, throw: 0.8, plunge: 0.8, walk: 0.4 };
    else w = { dash: 2.0, leap: 1.4, plunge: 1.3, throw: 1.5, cast: 1.2, eruption: 1.2, drag: 1.1, invoke: p2 ? 1.6 : 0.8, walk: 0.5 };
    if (P.hp < D.maxHp * 0.35) { w.grab = (w.grab || 0) + 0.8; w.dash = (w.dash || 0) + 0.6; }   // smells blood
    this.recent.forEach((m, i) => { if (w[m]) w[m] *= i === this.recent.length - 1 ? 0.15 : 0.5; });
    return this.pick(w);
  }
  start(name, from = 0) {
    if (!this.has(name)) name = 'combo';
    this.facePlayer(); this.atk = name; this.hits = new Set(); this.id = ++hazardId * 10; this.last = name;
    this.recent.push(name); if (this.recent.length > 3) this.recent.shift();
    if (OMEN_COOL[name]) this.cds[name] = OMEN_COOL[name] * (this.phase === 2 ? 0.75 : 1);
    this.pillarsQueued = false; this.spearsFired = false; this.fired = {}; this.air = null; this.y = this.floor; this.mixed = false;
    this.countering = this.warding = false; this.mark = null; this.holdT = 0;
    this.lunge = clamp(Math.abs(P.x - this.x) - 40, 10, (OMEN[name] && OMEN[name].lungeMax) || 150);
    this.setB('attack', name, false);
    if (from) { this.anim.i = from; this.anim.t = 0; }
    const S = OMEN_START[name]; if (S) S.call(this);
  }
  point(p) { return metaPoint(this.sh, this, p); }
  mp(tag, key, i = this.anim.i) { const P_ = this.M.points && this.M.points[tag]; const v = P_ && P_[key] && P_[key][i]; return v ? this.point(v) : { x: this.x + this.face * 30, y: this.y - 60 }; }
  rectM(r, reachBody = false) {
    const sh = this.sh, relX0 = r[0] - sh.ax; let relX1 = r[0] + r[2] - sh.ax;
    if (reachBody && relX0 < 0) relX1 = Math.max(relX1, 4);
    const y0 = this.y - sh.ay + r[1], y1 = y0 + r[3];
    return this.face === -1 ? rect(this.x + relX0, y0, this.x + relX1, y1) : rect(this.x - relX1, y0, this.x - relX0, y1);
  }
  // ---- the fight reads you: flasks, mashing, spells from range
  watchPlayer(dt) {
    for (const k in this.cds) this.cds[k] -= dt;
    this.spamCd = (this.spamCd || 0) - dt;
    const ps = P.state;
    if (ps === 'heal' && this.lastPS !== 'heal') this.react = 'heal';
    if (ps === 'cast' && this.lastPS !== 'cast' && Math.abs(P.x - this.x) > 110 && Math.random() < (this.phase === 2 ? 0.7 : 0.4)) this.react = this.react || 'cast';
    this.lastPS = ps;
    this.hitLog = this.hitLog.filter(t => time - t < 1.7);
    if (this.hitLog.length >= 3 && this.spamCd <= 0) { this.react = this.react || 'spam'; this.spamCd = 4.5; this.hitLog = []; }
  }
  startReaction() {
    const r = this.react, d = Math.abs(P.x - this.x); this.react = null;
    if (!r || P.state === 'dead') return false;
    if (r === 'heal') {
      if (typeof omBgPunish === 'function' && this.phase === 2) omBgPunish();
      this.start(d < 200 ? 'dash' : this.any(['throw', 'cast'])); return true;
    }
    if (r === 'spam') { if (d > 110) return false; const r2 = Math.random(); this.start(this.phase === 2 && r2 < 0.35 ? 'ward' : r2 < 0.6 ? 'counter' : 'grab'); return true; }
    if (r === 'cast') { this.start(this.phase === 2 ? 'ward' : 'dash'); return true; }
    return false;
  }
  hit(info) {
    if (this.alive && this.active && this.state === 'attack' && (this.countering || this.warding) && (P.x - this.x) * this.face > 0) return this.guardHit(info);
    if (this.alive && this.active) this.hitLog.push(time);
    super.hit(info);
  }
  guardHit(info) {
    sfx.parry(); hitstop = Math.max(hitstop, 0.1); shake = Math.max(shake, 3); this.flash = 0.6;
    spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir);
    for (let i = 0; i < 10; i++) particles.push({ x: info.x, y: info.y, vx: -info.dir * rand(20, 110), vy: -rand(20, 90), g: 300, life: rand(0.3, 0.6), kind: 'spark' });
    if (this.countering) {   // struck the stance: answered at once
      this.countering = false; this.facePlayer(); this.anim.i = 4; this.anim.t = 0; this.anim.changed = true; flashScreen = 0.25;
    } else if (this.warding) {
      this.blocked = (this.blocked || 0) + 1;
      if (Math.abs(P.x - this.x) < 80) P.vx = this.face * 150;
    }
  }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    if (!this.active) { this.facePlayer(); if (P.x > 4 * TILE + 24) this.activate(); this.updateSpears(dt); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.state !== 'intro') this.setB('intro', 'roar', false); if (an.done) an.hold(); if (an.changed && an.i === 3) { sfx.roar(); shake = 8; spawnFx('roar_ring', this.x, this.y - 50, 1); } if (this.introT <= 0) { this.setB('idle', 'idle'); this.cool = 0.5; } return; }
    this.watchPlayer(dt);
    const dist = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': case 'walk':
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') { if (this.state !== 'idle') this.setB('idle', 'idle'); break; }
        if (this.react && this.startReaction()) break;
        if (this.cool <= 0) {
          const m = this.choose(dist);
          if (m === 'walk') { this.setB('walk', 'walk'); this.cool = rand(0.35, 0.7); }
          else if (m === 'backstep') { this.setB('backstep', 'backstep', false); this.bs = { x0: this.x, t: 0 }; this.last = 'backstep'; }
          else this.start(m);
        } else if (dist > 90 || this.state === 'walk') {
          if (this.state !== 'walk') this.setB('walk', 'walk');
          this.x = clamp(this.x + this.face * (this.phase === 1 ? 40 : 56) * dt, this.L + 30, this.R - 30);
          if (dist < 60) this.setB('idle', 'idle');
        }
        break;
      case 'backstep': {
        let T = 0; for (let i = 0; i < 4; i++) T += an.ms(i); T = T / 1000 / this.speed;
        this.bs.t += dt; const k = Math.min(1, this.bs.t / T);
        this.x = clamp(this.bs.x0 - this.face * 80 * Math.sin(k * Math.PI / 2), this.L + 30, this.R - 30);
        this.y = this.floor - Math.sin(k * Math.PI) * 10;
        if (an.done) {
          this.y = this.floor;
          if (this.pendingPhase) { this.enterPhase2(); break; }
          this.start(this.any(this.phase === 2 ? ['dash', 'cast', 'throw', 'plunge', 'thrust', 'invoke'] : ['thrust', 'dash', 'eruption', 'leap', 'throw']));
        }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'stagger':
        this.t -= dt;
        if (an.i === 2 && this.t > 0.3) an.hold();
        if (an.done || this.t <= -0.6) { if (this.pendingPhase) this.enterPhase2(); else { this.setB('idle', 'idle'); this.cool = 0.35; } }
        break;
      case 'roar':
        if (an.changed && an.i === 3) {
          sfx.roar(); shake = 10; flashScreen = 0.5;
          spawnFx('roar_ring', this.x, this.y - 50, 1); spawnFx('shockwave', this.x, this.floor, 1);
          if (dist < 70) hurtPlayer(BOSS_DMG * 20, P.x < this.x ? -1 : 1, ++hazardId);
        }
        if (an.i >= 3) for (let i = 0; i < 2; i++) particles.push({ x: this.x + rand(-40, 40), y: this.y - rand(0, 100), vx: 0, vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'gold' });
        if (an.done) { this.setB('idle', 'idle'); this.cool = 0.2; }
        break;
      case 'dead':
        if (an.i >= 4 && Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 90), vx: 0, vy: -rand(15, 45), life: rand(1, 2.2), kind: 'gold' });
        if (an.done) an.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp / 2 && this.alive && !this.pendingPhase) {
      if (['attack', 'backstep', 'stagger'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    if (this.phase === 2 && this.alive && Math.random() < 0.35) particles.push({ x: this.x + rand(-28, 28), y: this.y - rand(10, 100), vx: 0, vy: -rand(10, 30), life: rand(0.8, 1.6), kind: 'gold' });
    addLight(this.x, this.y - 60, this.phase === 2 ? 110 : 70, '255,200,110', 0.8);
    this.updateSpears(dt); this.updateBlade(dt); this.updateLines(dt); this.updateCres(dt);
  }
  enterPhase2() {
    this.releaseCatch(); this.recallBlade();
    this.phase = 2; this.speed = 1.15; this.chain = 0; this.pendingPhase = false; this.air = null; this.y = this.floor; this.mark = null;
    this.countering = this.warding = false;
    this.sh = this.sheetFor('roar'); this.anim = new Anim(this.sh, 'roar', false, 1);
    this.facePlayer(); this.state = 'roar';
    if (typeof omPhase2Begin === 'function') omPhase2Begin(this);
    bossPhase2Scene(this);
  }
  stagger() {
    this.releaseCatch(); this.recallBlade(); this.countering = this.warding = false; this.mark = null;
    this.toBase(); super.stagger();
  }
  telegraph(tag, i) {
    const tg = this.M.telegraph && this.M.telegraph[tag], t = tg && tg[String(i)];
    if (!t) return; const p = this.point(t); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint();
  }
  updateAttack(dt) {
    const a = this.atk, A = OMEN[a] || { dmg: [], track: [] }, an = this.anim, M = (this.M.attacks && this.M.attacks[a]) || { active: [], rects: {} }, FLOOR = this.floor;
    if (A.track.includes(an.i)) { this.facePlayer(); this.lunge = clamp(Math.abs(P.x - this.x) - 40, 10, A.lungeMax || 150); }
    if (an.changed) this.telegraph(a, an.i);
    let step = A.steps && A.steps[an.i];
    if (A.lunge === an.i) step = this.lunge;
    if (step) this.x = clamp(this.x + this.face * step * dt / (an.ms() / an.speed / 1000), this.L + 24, this.R - 24);
    if (an.changed && M.active.includes(an.i) && a !== 'leap' && a !== 'eruption' && !(A.custom || []).includes(an.i)) {
      sfx.bossSwing();
      const fxName = A.fx && A.fx[an.i];
      if (fxName) {
        const pt = this.meta.body && this.meta.body[fxName];
        if (pt) { const q = this.point(pt); spawnFx(fxName, q.x, q.y, this.face, null, { pivot: OMEN_FX_PIVOT[fxName], center: false, bottom: false, rot: fxName === 'thrust' && this.meta.thrust_angle_deg ? -this.meta.thrust_angle_deg * Math.PI / 180 : 0 }); }
        else spawnFx(fxOr(fxName, 'boss_slash'), this.x + this.face * 6, this.y - 74, this.face);
      }
    }
    const U = OMEN_UPD[a];
    if (U && U.call(this, an, dt, FLOOR, M) === 'stop') return;
    if (this.state !== 'attack' || this.atk !== a) return;
    if (M.active.includes(an.i) && M.rects && !(A.custom || []).includes(an.i)) {
      const rr = M.rects[String(an.i)], group = A.groups ? A.groups[an.i] : 0;
      if (rr && !this.hits.has(group)) {
        const r = this.rectM(rr, !A.bothSides);
        if (overlap(r, playerHurtbox())) {
          const dmg = (A.dmg[group] ?? A.dmg[0] ?? 40) * (this.phase === 2 ? 1.12 : 1);
          if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.id + group, { parryable: !!A.parry, src: this })) this.hits.add(group);
        }
      }
    }
    if (an.done) this.finish();
  }
  finish() {
    const a = this.atk, FLOOR = this.floor;
    this.y = FLOOR; this.air = null; this.mark = null; this.countering = this.warding = false;
    if (this.charge) { this.charge.kill = true; this.charge = null; }
    if (this.pendingPhase) { this.enterPhase2(); return; }
    if (this.react && this.startReaction()) return;
    const d = Math.abs(P.x - this.x), maxC = this.phase === 2 ? 2 : 1, pc = this.phase === 2 ? 0.62 : 0.36;
    if (P.state !== 'dead' && this.chain < maxC && Math.random() < pc && OMEN_CHAIN[a]) {
      const nx = OMEN_CHAIN[a](this, d);
      if (nx && !(this.cds[nx] > 0)) { this.chain++; this.start(nx); return; }
    }
    this.chain = 0; this.setB('idle', 'idle');
    this.cool = (this.phase === 1 ? rand(0.55, 1.0) : rand(0.25, 0.6)) + ({ grab: 0.5, plunge: 0.25, invoke: 0.35, throw: 0.2 }[a] || 0);
  }
  pillar(x, delay) {
    const FLOOR = this.floor;
    hazards.push({ x, y: FLOOR, w: 16, h: 110, dmg: BOSS_DMG * 50, id: ++hazardId, life: 5, delay, fx: null,
      onStart: h => { h.fx = spawnFx('pillar', h.x, FLOOR, 1); if (!h.fx) h.life = 0; else sfx.pillar(); },
      update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } const i = h.fx.anim.i; if (i >= 3 && i <= 6) { addLight(h.x, FLOOR - 50, 60, '255,210,120', 1); if (Math.random() < 0.5) particles.push({ x: h.x + rand(-6, 6), y: FLOOR - rand(0, 100), vx: 0, vy: -rand(30, 70), life: 0.5, kind: 'gold' }); if (i === 3 && h.fx.anim.changed) shake = Math.max(shake, 2.5); } },
      active: h => h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 6 });
    // warning: a thin shaft of light and a burning ring on the floor until the pillar rises
    hazards.push({ x, y: FLOOR, w: 0, h: 0, dmg: 0, life: delay + 0.18, delay: 0, active: () => false, omWarn: true,
      update: h => { addLight(h.x, FLOOR - 4, 20, '255,210,120', 0.5 + 0.3 * Math.sin(time * 30)); if (Math.random() < 0.4) particles.push({ x: h.x + rand(-5, 5), y: FLOOR - 2, vx: 0, vy: -rand(10, 40), life: 0.4, kind: 'gold' }); } });
  }
  // ---- light spears: aimed (hover, track you, launch) or fixed (rain columns, spear walls)
  spear(x, y, hover, o = {}) {
    this.spears.push({ x, y, vx: 0, vy: 0, hover, life: 4, id: ++hazardId, ang: o.ang ?? Math.PI / 2, t: 0, spread: o.spread || 0,
                       fixed: !!o.fixed, spd: o.spd || 300, col: !!o.col, dmg: o.dmg || (this.phase === 2 ? 28 : 30) });
  }
  updateSpears(dt) {
    for (const s of this.spears) {
      s.t += dt;
      if (s.hover > 0) {
        s.hover -= dt; if (!s.fixed) s.ang = Math.atan2(P.y - 14 - s.y, P.x + s.spread - s.x);
        if (s.hover <= 0) { s.vx = Math.cos(s.ang) * s.spd; s.vy = Math.sin(s.ang) * s.spd; sfx.spear(); }
        addLight(s.x, s.y, 20, '255,220,140', 0.8); continue;
      }
      s.x += s.vx * dt; s.y += s.vy * dt; s.life -= dt;
      addLight(s.x, s.y, 26, '255,220,140', 0.9);
      if (Math.random() < 0.5) particles.push({ x: s.x, y: s.y, vx: 0, vy: -rand(0, 10), life: 0.3, kind: 'gold' });
      const tip = rect(s.x - 5, s.y - 4, s.x + 5, s.y + 4);
      if (overlap(tip, playerHurtbox()) && hurtPlayer(BOSS_DMG * s.dmg, sign(s.vx), s.id)) { s.life = 0; spawnFx('spear_impact', s.x, s.y); }
      else if (s.y >= this.floor - 1 || (s.t > 0.1 && solidAtPx(s.x, s.y)) || s.x < -40 || s.x > room.pw + 40) { s.life = 0; spawnFx('spear_impact', s.x, Math.min(s.y, this.floor - 4)); shake = Math.max(shake, 1.5); }
    }
    this.spears = this.spears.filter(s => s.life > 0);
  }
  // ---- the thrown greatsword: out, hang, home back to his open hand; it cuts both ways
  updateBlade(dt) {
    const b = this.blade; if (!b) return;
    b.t += dt; b.rot += dt * 22;
    if (Math.random() < 0.6) particles.push({ x: b.x + rand(-10, 10), y: b.y + rand(-10, 10), vx: 0, vy: -rand(5, 20), life: 0.35, kind: 'gold' });
    addLight(b.x, b.y, 50, '255,210,120', 0.9);
    if (b.t % 0.25 < dt) omSfx.blade();
    if (b.phase === 'out') {
      const sp = Math.max(60, 330 * (1 - b.dist / b.max));
      const nx = b.x + b.dir * sp * dt; b.dist += Math.abs(nx - b.x); b.x = nx;
      if (this.phase === 2) b.y = b.y0 - Math.sin(Math.min(1, b.dist / b.max) * Math.PI) * 34;
      if (b.dist >= b.max - 4 || b.x < TILE + 20 || b.x > room.pw - TILE - 20) { b.phase = 'hang'; b.t = 0; }
    } else if (b.phase === 'hang') {
      if (this.phase === 2) b.y = approach(b.y, P.y - 16, 60 * dt);   // it drifts down to meet you
      if (b.t > (this.phase === 2 ? 0.55 : 0.4)) { b.phase = 'back'; b.id = ++hazardId; }
    } else if (b.phase === 'back') {
      const h = this.mp('throw', 'handn', 5), dx = h.x - b.x, dy = h.y - b.y, d = Math.hypot(dx, dy) || 1, sp = this.phase === 2 ? 440 : 380;
      b.x += dx / d * sp * dt; b.y += dy / d * sp * dt;
      if (d < 16 || b.t > 3) { this.blade = null; if (this.state === 'attack' && this.atk === 'throw') this.caughtBlade = true; return; }
    }
    const r = rect(b.x - 14, b.y - 14, b.x + 14, b.y + 14);
    if (b.phase !== 'hang' && overlap(r, playerHurtbox())) hurtPlayer(BOSS_DMG * 44 * (this.phase === 2 ? 1.1 : 1), sign(P.x - b.x) || 1, b.id, { src: this });
  }
  recallBlade() { if (this.blade) { spawnFx('spear_impact', this.blade.x, this.blade.y); this.blade = null; } }
  // ---- lines of light left on the floor (dash path, drag furrow): they glow, then erupt
  omLine(x0, x1, delay, h, dmg, armed = true) {
    const l = { x0: Math.min(x0, x1), x1: Math.max(x0, x1), t: 0, delay, h, dmg, armed, id: ++hazardId };
    this.lines.push(l); return l;
  }
  updateLines(dt) {
    for (const l of this.lines) {
      if (!l.armed) continue;
      l.t += dt;
      if (l.t >= l.delay && l.t - dt < l.delay) { sfx.pillar(); shake = Math.max(shake, 5); for (let x = l.x0; x < l.x1; x += 10) particles.push({ x: x + rand(-4, 4), y: this.floor - rand(0, l.h), vx: 0, vy: -rand(40, 110), life: rand(0.4, 0.8), kind: 'gold' }); }
      const on = l.t >= l.delay && l.t < l.delay + 0.28;
      if (on) { for (let x = l.x0 + 16; x < l.x1; x += 48) addLight(x, this.floor - l.h / 2, 60, '255,220,140', 1);
        if (overlap(rect(l.x0, this.floor - l.h, l.x1, this.floor), playerHurtbox())) hurtPlayer(BOSS_DMG * l.dmg, P.x < (l.x0 + l.x1) / 2 ? -1 : 1, l.id); }
      if (l.t > l.delay + 0.6) l.gone = true;
    }
    this.lines = this.lines.filter(l => !l.gone);
  }
  // ---- crescent waves (flurry finisher): tall, travel along the floor; roll through them
  updateCres(dt) {
    for (const c of this.cres) {
      c.t += dt; c.x += c.vx * dt; c.life -= dt;
      addLight(c.x, this.floor - 30, 50, '255,220,140', 0.9);
      if (c.x < TILE || c.x > room.pw - TILE) c.life = 0;
      if (overlap(rect(c.x - 8, this.floor - 56, c.x + 8, this.floor), playerHurtbox()) && hurtPlayer(BOSS_DMG * 40, sign(c.vx), c.id)) {}
    }
    this.cres = this.cres.filter(c => c.life > 0);
  }
  // ---- the grab
  catchPlayer() {
    this.caught = true; P.vx = P.vy = 0; setP('rest', 'hurt', false); P.face = -this.face;
    sfx.bigHit(); omSfx.grab(); hitstop = 0.14; shake = 6; flashScreen = 0.2;
    this.start('impale');
  }
  holdPlayer() {
    if (!this.caught) return;
    if (P.state === 'dead') { this.caught = false; return; }
    const h = this.mp('impale', 'hand');
    P.x = h.x - this.face * 2; P.y = h.y + 23; P.vx = P.vy = 0; P.face = -this.face;
    if (P.state !== 'rest') setP('rest', 'hurt', false);
  }
  impaleHit(dmg, release) {
    if (!this.caught) return;
    P.state = 'hurt'; P.inv = 0; P.lastHit = undefined;
    hurtPlayer(BOSS_DMG * dmg * (this.phase === 2 ? 1.1 : 1), this.face, ++hazardId, { src: this });
    spawnFx('hit', P.x, P.y - 14, this.face); hitstop = Math.max(hitstop, 0.12); shake = Math.max(shake, 7);
    for (let i = 0; i < 14; i++) particles.push({ x: P.x, y: P.y - 14, vx: rand(-80, 80), vy: -rand(20, 120), g: 300, life: rand(0.4, 0.8), kind: 'gold' });
    if (P.state === 'dead') { this.caught = false; return; }
    if (release) { this.caught = false; setP('hurt', 'hurt'); P.vx = this.face * 230; P.vy = -170; P.ground = false; P.inv = 0.7; }
    else setP('rest', 'hurt', false);
  }
  releaseCatch() { if (this.caught) { this.caught = false; if (P.state === 'rest') { setP('hurt', 'hurt'); P.vy = -60; P.inv = 0.6; } } }
  die() {
    this.releaseCatch(); this.recallBlade();
    this.toBase();
    this.state = 'dead'; this.anim.set(this.sh.has('death') ? 'death' : 'stagger', false, 1); this.air = null; this.y = this.floor;
    hazards = []; this.spears = []; this.lines = []; this.cres = []; this.mark = null; if (this.charge) { this.charge.kill = true; this.charge = null; }
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'OMEN VANQUISHED', t: 0 };
    if (typeof omPhase2End === 'function') omPhase2End(this);
    this.rewards();
  }
  draw() {
    // floor lines under him
    for (const l of this.lines) {
      const fy = this.floor, on = l.armed && l.t >= l.delay, k = l.armed ? clamp(l.t / l.delay, 0, 1) : 0.4;
      if (!on) {
        const a = 0.35 + 0.45 * k + 0.2 * Math.sin(time * (20 + 20 * k));
        g.fillStyle = `rgba(255,214,120,${a})`; g.fillRect(Math.round(l.x0), fy - 2, Math.round(l.x1 - l.x0), 2);
        g.fillStyle = `rgba(255,250,220,${a * 0.8})`; g.fillRect(Math.round(l.x0), fy - 1, Math.round(l.x1 - l.x0), 1);
        for (let x = l.x0; x < l.x1; x += 7) if ((x + Math.floor(time * 30)) % 3 === 0) { g.fillStyle = `rgba(255,200,90,${a * 0.6})`; g.fillRect(Math.round(x), fy - 3 - Math.floor(k * 3), 1, 1 + Math.floor(k * 3)); }
        addLight((l.x0 + l.x1) / 2, fy - 3, Math.min(120, (l.x1 - l.x0) / 2 + 20), '255,210,120', 0.35 + 0.3 * k);
      } else {
        const u = (l.t - l.delay) / 0.6, hh = l.h * (u < 0.15 ? u / 0.15 : 1) * (1 - Math.max(0, u - 0.5) * 2);
        for (let y = 0; y < hh; y++) {
          const f = y / l.h;
          g.fillStyle = `rgba(${255},${Math.round(240 - f * 90)},${Math.round(190 - f * 150)},${(1 - f) * 0.85 * (1 - u * 0.6)})`;
          g.fillRect(Math.round(l.x0), Math.round(fy - y - 1), Math.round(l.x1 - l.x0), 1);
        }
        g.fillStyle = 'rgba(255,255,240,0.9)'; g.fillRect(Math.round(l.x0), fy - 2, Math.round(l.x1 - l.x0), 2);
      }
    }
    if (this.mark) {   // where he will land
      const a = 0.4 + 0.35 * Math.sin(time * 26), w = this.mark.w || 34;
      g.strokeStyle = `rgba(255,214,120,${a})`; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(this.mark.x), this.floor - 1, w, 3, 0, 0, 6.3); g.stroke();
      g.fillStyle = `rgba(255,190,90,${a * 0.35})`; g.fill();
      addLight(this.mark.x, this.floor - 4, 40, '255,210,120', 0.6);
    }
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : (this.state === 'roar' && this.anim.i >= 3 ? { flash: 0.2 + 0.15 * Math.sin(time * 24), flashColor: '#ffcf6a' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : (this.countering || this.warding) ? { flash: 0.12 + 0.1 * Math.sin(time * 16), flashColor: '#ffe7a0' } : {});
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    const ls = fxSheet('light_spear');
    for (const s of this.spears) {
      if (s.col && s.hover > 0) {   // rain column warning
        const a = 0.18 + 0.3 * Math.sin(time * 30);
        g.fillStyle = `rgba(255,220,140,${a})`; g.fillRect(Math.round(s.x), Math.round(s.y), 1, Math.round(this.floor - s.y));
        g.fillStyle = `rgba(255,220,140,${a + 0.2})`; g.fillRect(Math.round(s.x) - 4, this.floor - 1, 9, 1);
      } else if (s.hover > 0) {
        const a = 0.15 + 0.25 * Math.sin(time * 30);
        for (let i = 1; i < 18; i++) if ((i + Math.floor(time * 20)) % 3) { g.fillStyle = `rgba(255,220,140,${a})`; g.fillRect(Math.round(s.x + Math.cos(s.ang) * i * 9), Math.round(s.y + Math.sin(s.ang) * i * 9), 1, 1); }
      }
      if (ls.ok) drawRotated(ls, ls.tag(Object.keys(ls.tags)[0]).from + Math.floor(s.t * 16) % 4, s.x, s.y, s.ang, s.hover > 0 ? 0.6 + 0.4 * Math.sin(time * 30) : 1);
      else { g.fillStyle = '#ffd77a'; g.fillRect(Math.round(s.x) - 2, Math.round(s.y) - 1, 5, 2); }
    }
    const bs = sheet('fx_om_blade');
    if (this.blade && bs.ok) drawSprite(bs, Math.floor(this.blade.rot) % 8, this.blade.x, this.blade.y, this.blade.dir, { center: true });
    const cs = sheet('fx_om_crescent');
    for (const c of this.cres) if (cs.ok) drawSprite(cs, Math.floor(c.t * 16) % 4, c.x, this.floor, sign(c.vx), { bottom: true, alpha: Math.min(1, c.life * 3) });
  }
}
// ---- per-move setup and frame logic (this = Omen). Return 'stop' when the move handed off to another.
const OMEN_START = {
  grab() { omSfx.grab(); },
  counter() { this.stanceT = this.phase === 2 ? 1.7 : 1.35; },
  ward() { this.wardT = this.phase === 2 ? 1.4 : 1.1; this.blocked = 0; },
  dash() { this.dash = null; },
  drag() { this.dragT = 0; this.furrow = null; },
  throw() { this.caughtBlade = false; },
};
function omAir(b, tx, h, T) { b.air = { x0: b.x, tx, y0: b.y, h, t: 0, T }; }
function omFrames(an, a, z) { let T = 0; for (let i = a; i <= z; i++) T += an.ms(i); return T / 1000 / an.speed; }
const OMEN_UPD = {
  combo(an) {   // mid-string mixup: the third hit can become a thrust, a rising cut or a leap
    if (an.changed && an.i === 8 && !this.mixed) {
      this.mixed = true;
      if (Math.random() < (this.phase === 2 ? 0.5 : 0.3)) {
        const d = Math.abs(P.x - this.x), nx = d > 100 ? 'leap' : this.any(['thrust', 'rising', 'thrust']);
        this.start(nx, nx === 'thrust' ? 2 : 1); return 'stop';
      }
    }
  },
  feint(an, dt) {   // the hold is random; sometimes the twitch is skipped
    if (an.changed && an.i === 2) { this.holdT = rand(0, this.phase === 2 ? 0.7 : 0.45); this.skipTwitch = Math.random() < 0.45; }
    if (an.i === 2 && this.holdT > 0) { this.holdT -= dt; an.hold(); if (Math.random() < 0.3) particles.push({ x: this.x + this.face * rand(-40, 0), y: this.y - rand(80, 120), vx: 0, vy: -rand(5, 20), life: 0.4, kind: 'gold' }); }
    if (an.changed && an.i === 3 && this.skipTwitch) { an.i = 4; an.t = 0; }
  },
  rising(an, dt, FLOOR) {
    if (an.changed && an.i === 2) { sfx.bossSwing(); omAir(this, clamp(P.x - this.face * 40, this.L + 30, this.R - 30), 68, omFrames(an, 2, 5)); }
    if (this.air) {
      if (an.i <= 4) this.air.tx = clamp(P.x - this.face * 40, this.L + 30, this.R - 30);
      this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
      this.x = lerp(this.air.x0, this.air.tx, 1 - Math.pow(1 - k, 2)); this.y = FLOOR - this.air.h * Math.sin(Math.min(1, k * 1.4) * Math.PI / 2);
      if (an.i >= 4) this.mark = { x: this.x + this.face * 40, w: 30 };
    }
    if (an.changed && an.i === 6) {
      this.air = null; this.mark = null; this.y = FLOOR; shake = 10; sfx.boom();
      const cx = this.x + this.face * 40;
      spawnFx('shockwave', cx, FLOOR, 1); spawnFx('ground_crack', cx, FLOOR, 1);
      hazards.push({ x: cx, y: FLOOR, w: 84, h: 24, dmg: BOSS_DMG * 38, id: this.id + 7, life: 0.2 });
      if (this.phase === 2) for (const d of [-1, 1]) hazards.push({ x: cx, y: FLOOR, vx: d * 180, w: 16, h: 14, dmg: BOSS_DMG * 34, id: ++hazardId, life: 1.3, wave: true, dir: d });
    }
  },
  sweep(an) {
    if (an.changed && an.i === 2) { shake = Math.max(shake, 3); for (let i = 0; i < 12; i++) particles.push({ x: this.x + this.face * rand(0, 90), y: this.floor - rand(0, 6), vx: this.face * rand(20, 90), vy: -rand(20, 70), g: 300, life: 0.5, kind: 'dust' }); }
  },
  grab(an, dt, FLOOR, M) {
    if (an.i <= 1) { const h = this.mp('grab', 'hand'); addLight(h.x, h.y, 34, '255,170,90', 0.9); if (Math.random() < 0.5) particles.push({ x: h.x + rand(-5, 5), y: h.y + rand(-5, 5), vx: 0, vy: -rand(10, 30), life: 0.4, kind: 'fire' }); }
    if (an.changed && an.i === 2) sfx.bossSwing();
    if (M.active.includes(an.i) && !this.caught && P.state !== 'dead' && !iframes() && !(P.inv > 0)) {
      const r = this.rectM(M.rects[String(an.i)]);
      if (overlap(r, playerHurtbox())) { this.catchPlayer(); return 'stop'; }
    }
  },
  impale(an) {
    this.holdPlayer();
    if (an.changed && an.i === 2) { this.impaleHit(68, false); flashScreen = 0.3; }
    if (an.changed && an.i === 4) this.impaleHit(24, true);
    if (an.i === 3) addLight(this.x + this.face * 26, this.y - 80, 60, '255,220,140', 1);
  },
  dash(an, dt, FLOOR) {
    if (an.i === 1) { addLight(this.x, this.y - 50, 80, '255,210,120', 0.9); if (Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 70), vx: -this.face * rand(10, 40), vy: -rand(5, 20), life: 0.4, kind: 'gold' }); }
    if (an.changed && an.i === 1) omSfx.dash();
    if (an.changed && an.i === 2 && !this.dash) {
      let x1 = clamp(P.x + this.face * 80, this.L + 24, this.R - 24);
      if ((x1 - this.x) * this.face < 60) x1 = clamp(this.x + this.face * 130, this.L + 24, this.R - 24);
      this.dash = { x0: this.x, x1, px: this.x }; sfx.bossSwing(); omSfx.blade(); shake = Math.max(shake, 3);
    }
    if (an.i === 2 && this.dash && !this.dash.done) {
      an.hold(); const d = this.dash; d.px = this.x;
      this.x = approach(this.x, d.x1, 820 * dt);
      for (let i = 0; i < 3; i++) particles.push({ x: this.x - this.face * rand(0, 50), y: this.y - rand(10, 80), vx: -this.face * rand(20, 60), vy: 0, life: 0.35, kind: 'gold' });
      if (!this.hits.has(0) && overlap(rect(Math.min(d.px, this.x) - 18, FLOOR - 64, Math.max(d.px, this.x) + 18, FLOOR), playerHurtbox()) &&
          hurtPlayer(BOSS_DMG * 56 * (this.phase === 2 ? 1.1 : 1), this.face, this.id, { src: this })) this.hits.add(0);
      if (Math.abs(this.x - d.x1) < 1) {
        d.done = true;
        this.omLine(d.x0, this.x, this.phase === 2 ? 0.38 : 0.46, this.phase === 2 ? 58 : 42, 40);
      }
    }
  },
  drag(an, dt, FLOOR) {
    const tip = this.mp('drag', 'tip');
    if (an.i >= 1 && an.i <= 4) {
      this.dragT += dt;
      const sp = this.phase === 2 ? 118 : 92;
      this.x = clamp(this.x + this.face * sp * dt, this.L + 24, this.R - 24);
      if (!this.furrow) this.furrow = this.omLine(tip.x, tip.x, 0.3, this.phase === 2 ? 56 : 44, 38, false);
      this.furrow.x0 = Math.min(this.furrow.x0, tip.x); this.furrow.x1 = Math.max(this.furrow.x1, tip.x);
      if (Math.random() < 0.8) particles.push({ x: tip.x, y: FLOOR - 1, vx: -this.face * rand(20, 90), vy: -rand(20, 80), g: 300, life: 0.4, kind: 'spark' });
      if (an.changed && an.i % 2 === 0) sfx.step();
      const d = Math.abs(P.x - this.x);
      if (an.changed && an.i === 4 && this.dragT < (this.phase === 2 ? 1.6 : 1.3) && d > 58) { an.i = 1; an.t = 0; }
    }
    if (an.changed && an.i === 6 && this.furrow) {
      this.furrow.armed = true; this.furrow.t = 0; this.furrow = null;
      if (this.phase === 2) for (const k of [0, 1]) hazards.push({ x: this.x + this.face * 40, y: FLOOR, vx: this.face * (190 + k * 50), w: 16, h: 16, dmg: BOSS_DMG * 34, id: ++hazardId, life: 1.6, delay: k * 0.3, wave: true, dir: this.face });
    }
  },
  plunge(an, dt, FLOOR) {
    if (an.changed && an.i === 2) { sfx.bossSwing(); omAir(this, clamp(P.x - this.face * 24, this.L + 30, this.R - 30), 84, omFrames(an, 2, 4)); for (let i = 0; i < 10; i++) particles.push({ x: this.x + rand(-20, 20), y: FLOOR, vx: rand(-60, 60), vy: -rand(20, 60), g: 200, life: 0.5, kind: 'dust' }); }
    if (this.air) {
      if (an.i <= 3) this.air.tx = clamp(P.x - this.face * 24, this.L + 30, this.R - 30);
      this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
      this.x = lerp(this.air.x0, this.air.tx, 1 - Math.pow(1 - k, 2)); this.y = FLOOR - this.air.h * Math.sin(Math.min(1, k * 1.3) * Math.PI / 2);
      this.mark = { x: this.air.tx + this.face * 24, w: 40 };
    }
    if (an.changed && an.i === 5) {
      this.air = null; this.mark = null; this.y = FLOOR; shake = 13; sfx.boom(); flashScreen = 0.25;
      const cx = this.x + this.face * 24;
      spawnFx('shockwave', cx, FLOOR, 1, null, { speed: 1.3 }); spawnFx('ground_crack', cx, FLOOR, 1);
      hazards.push({ x: cx, y: FLOOR, w: 70, h: 34, dmg: BOSS_DMG * 46, id: this.id + 8, life: 0.2 });
      for (const d of [-1, 1]) for (let k = 0; k < (this.phase === 2 ? 2 : 1); k++)
        hazards.push({ x: cx, y: FLOOR, vx: d * (200 - k * 40), w: 16, h: 15, dmg: BOSS_DMG * 36, id: ++hazardId, life: 1.6, delay: k * 0.38, wave: true, dir: d });
    }
  },
  throw(an, dt, FLOOR) {
    if (an.changed && an.i === 2) {
      const p = this.mp('throw', 'grip', 2);
      this.blade = { x: p.x, y: FLOOR - 28, y0: FLOOR - 28, dir: this.face, phase: 'out', t: 0, dist: 0, max: this.phase === 2 ? 270 : 225, rot: 0, id: ++hazardId };
      sfx.bossSwing(); omSfx.blade();
    }
    if (an.i >= 4 && an.i <= 6) { const h = this.mp('throw', 'handn'); addLight(h.x, h.y, 30, '255,210,120', 0.8); }
    if (an.i === 6 && !this.caughtBlade && this.blade) an.hold();
    if (an.changed && an.i === 7) { sfx.glint(); shake = Math.max(shake, 3); }
  },
  counter(an, dt) {
    if (an.changed && an.i === 1 && this.stanceT > 0) { this.countering = true; omSfx.stance(); }
    if (this.countering) {
      this.stanceT -= dt;
      addLight(this.x + this.face * 20, this.y - 70, 50, '255,230,160', 0.7);
      if (an.changed && an.i === 4) { an.i = 1; an.t = 0; }   // hold the stance loop
      if (this.stanceT <= 0) {
        this.countering = false;
        if (Math.random() < 0.55) { this.facePlayer(); an.i = 4; an.t = 0; an.changed = true; }
        else { this.chain = 0; this.setB('idle', 'idle'); this.cool = 0.55; return 'stop'; }   // lowers his guard: the opening
      }
    }
    if (an.changed && an.i === 4 && this.phase === 2) this.cres.push({ x: this.x + this.face * 40, vx: this.face * 240, t: 0, life: 1.4, id: ++hazardId });
  },
  ward(an, dt, FLOOR) {
    const sg = this.M.sigil ? this.point(this.M.sigil) : { x: this.x + this.face * 46, y: this.y - 62 };
    if (an.changed && an.i === 1) { this.warding = true; omSfx.ward(); }
    if (this.warding) {
      this.wardT -= dt;
      addLight(sg.x, sg.y, 60, '255,230,160', 0.9);
      for (const pr of projectiles) if (pr.owner === 'player' && Math.abs(pr.x - sg.x) < 20 + Math.abs(pr.vx || 0) * dt && Math.abs(pr.y - sg.y) < 40) {
        pr.life = 0; this.blocked = (this.blocked || 0) + 1; sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), pr.x, pr.y, -this.face);
      }
      if (an.changed && an.i === 4) { an.i = 1; an.t = 0; }
      if (this.wardT <= 0) { this.warding = false; an.i = 4; an.t = 0; an.changed = true; }
    }
    if (an.changed && an.i === 4) {
      sfx.pillar(); shake = 8; flashScreen = 0.3;
      spawnFx('roar_ring', sg.x, sg.y, 1);
      hazards.push({ x: sg.x, y: FLOOR, w: 64, h: 90, dmg: BOSS_DMG * 40, id: this.id + 4, life: 0.15 });
      const n = Math.min(8, 3 + (this.blocked || 0) + (this.phase === 2 ? 1 : 0));
      for (let k = 0; k < n; k++) { const c = k - (n - 1) / 2; this.spear(sg.x + c * 14, sg.y - 30 - Math.abs(c) * 5, 0.3 + k * 0.08, { spread: c * 5 }); }
    }
  },
  flurry(an) {
    if (an.changed && an.i === 9) {
      shake = Math.max(shake, 6);
      this.cres.push({ x: this.x + this.face * 50, vx: this.face * 250, t: 0, life: 1.6, id: ++hazardId });
      if (this.phase === 2) this.cres.push({ x: this.x + this.face * 50, vx: this.face * 330, t: -0.3, life: 1.6, id: ++hazardId });
    }
  },
  invoke(an, dt, FLOOR) {
    const tip = this.mp('invoke', 'tip');
    if (an.changed && an.i === 1) { this.charge = spawnFx('cast_charge', tip.x, tip.y, 1, null, { loop: true }); sfx.charge(); }
    if (this.charge) { this.charge.x = tip.x; this.charge.y = tip.y; addLight(tip.x, tip.y, 60, '255,220,140', 1); }
    if (an.changed && an.i === 4) {
      if (this.charge) { this.charge.kill = true; this.charge = null; }
      flashScreen = 0.3; sfx.glint();
      const kind = this.any(this.phase === 2 ? ['rain', 'ring', 'wall', 'rain'] : ['rain', 'ring']);
      this.invokeKind = kind;
      const top = Math.max(8, cam.y + 4);
      if (kind === 'rain') {
        const gap = irand(1, 5);
        for (let k = 0; k < 7; k++) { if (k === gap) continue; const x = clamp(P.x + (k - 3) * 34, this.L, this.R); this.spear(x, top, 0.75 + Math.abs(k - 3) * 0.08, { fixed: true, col: true, spd: 520 }); }
        if (this.phase === 2) for (let k = 0; k < 5; k++) this.spear(clamp(P.x + (k - 2) * 34 + 17, this.L, this.R), top, 1.55 + k * 0.05, { fixed: true, col: true, spd: 520 });
      } else if (kind === 'ring') {
        const n = this.phase === 2 ? 8 : 6;
        for (let k = 0; k < n; k++) { const a = -Math.PI * (0.06 + 0.88 * k / (n - 1)); this.spear(P.x + Math.cos(a) * 84, Math.max(top, P.y - 16 + Math.sin(a) * 70), 0.7 + k * 0.13); }
      } else {   // spear wall from the far side: low row (jump it) then high row (stay down)
        const side = P.x < room.pw / 2 ? 1 : -1, x0 = side > 0 ? room.pw - TILE - 6 : TILE + 6, ang = side > 0 ? Math.PI : 0;
        for (let k = 0; k < 4; k++) this.spear(x0, FLOOR - 9, 0.8 + k * 0.05, { fixed: true, ang, spd: 330 });
        for (let k = 0; k < 4; k++) this.spear(x0, FLOOR - 52, 1.6 + k * 0.05, { fixed: true, ang, spd: 330 });
      }
      if (this.phase === 2 && typeof omBgCall === 'function') omBgCall(kind === 'wall' ? 'shards' : 'beams');
    }
  },
  cast(an) {
    if (an.changed && an.i === 1) { const p = this.point(this.meta.cast_point); this.charge = spawnFx('cast_charge', p.x, p.y, 1, null, { loop: true }); sfx.charge(); }
    if (this.charge) { const p = this.point(this.meta.cast_point); this.charge.x = p.x; this.charge.y = p.y; addLight(p.x, p.y, 60, '255,220,140', 1); }
    if (an.changed && an.i === 5 && !this.spearsFired) {
      this.spearsFired = true; flashScreen = 0.2;
      if (this.charge) { this.charge.kill = true; this.charge = null; }
      const p = this.point(this.meta.cast_point), n = this.phase === 2 ? 7 : 5;
      for (let k = 0; k < n; k++) { const c = k - (n - 1) / 2; this.spear(p.x + c * 20, p.y - Math.abs(c) * 6 - 18, 0.35 + k * 0.09, { spread: c * 6 }); }
    }
  },
  leap(an, dt, FLOOR, M) {
    if (an.changed && an.i === 2) {
      const T = (an.ms(2) + an.ms(3) + an.ms(4)) / an.speed / 1000;
      this.air = { x0: this.x, tx: clamp(P.x - this.face * 26, this.L + 30, this.R - 30), t: 0, T };
    }
    if (this.air) { this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T); this.x = lerp(this.air.x0, this.air.tx, k); this.y = FLOOR - Math.sin(k * Math.PI) * 70; this.mark = { x: this.air.tx + this.face * 40, w: 30 }; }
    if (an.changed && an.i === 5) {
      this.air = null; this.mark = null; this.y = FLOOR; shake = 10; sfx.boom();
      const r = this.rectM(M.rects['5'] || [40, 100, 100, 28]), cx = (r.x0 + r.x1) / 2;
      spawnFx('shockwave', cx, FLOOR, 1); spawnFx('ground_crack', cx, FLOOR, 1);
      hazards.push({ x: cx, y: FLOOR, w: 80, h: 24, dmg: BOSS_DMG * 40, id: this.id + 5, life: 0.2 });
      if (this.phase === 2) for (const d of [-1, 1]) hazards.push({ x: cx, y: FLOOR, vx: d * 175, w: 16, h: 14, dmg: BOSS_DMG * 36, id: ++hazardId, life: 1.4, wave: true, dir: d });
    }
  },
  eruption(an, dt, FLOOR) {
    if (an.changed && an.i === 3) {
      shake = 6; sfx.boom();
      const p = this.point(this.meta.eruption_point);
      spawnFx('ground_crack', p.x, FLOOR, this.face); spawnFx('shockwave', p.x, FLOOR, 1, null, { speed: 1.4 });
      hazards.push({ x: p.x, y: FLOOR, w: 36, h: 30, dmg: BOSS_DMG * 36, id: this.id + 3, life: 0.15 });
    }
    if (an.changed && an.i === 4 && !this.pillarsQueued) {
      this.pillarsQueued = true;
      const p = this.point(this.meta.eruption_point), dir = P.x < p.x ? -1 : 1;
      for (let k = 1; k <= 9; k++) { const x = p.x + dir * k * 32; if (x < this.L - 10 || x > this.R + 10) break; this.pillar(x, 0.1 + k * 0.11); }
      if (this.phase === 2) for (let k = 0; k < 3; k++) this.pillar(clamp(P.x + rand(-40, 40), this.L, this.R), 0.7 + k * 0.25);
    }
  },
};
let bossBanner = null, victoryBanner = null;
