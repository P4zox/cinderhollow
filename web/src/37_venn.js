// ------------------------------------------------------------------ Sister Venn, the Last Kindling (agent V)
// Secret final boss. After the Pale Sovereign falls, refusing the final choice ("keep the last flame for yourself")
// turns Venn against you in the Heart of the Pale Root (X5). Three phases:
//   1 (100-60%)  veiled priestess: flame-scythe sweeps, a rising crescent, shrine-light pillars, halo rings, and she
//                drinks from the flask she once gave you (punishable: hit her hard enough and she staggers)
//   2 (60-20%)   the veil burns away; eyes of white gold; wings of burning roots: root lances, a wingbeat dive,
//                she drinks the dying Root (a channel that raises root spikes across the arena; break it)
//   3 (20-0%)    the halo cracks; the music falls to a single voice; blink-cuts, a desperate flurry, a leap slam
// Her death leads to the fourth ending, "The Ember Unbound" (ENDINGS.venn in 10_story.js).
// Sprite: art/gen_venn.py (+ art/venn_rig.py), fx: art/gen_venn_fx.py, meta: assets/venn_boss_meta.json.
BOSS_INFO.venn = { name: 'Sister Venn, the Last Kindling', hp: 5000, cinders: 40000, reward: ['w:last_kindling', 'c_lastflame'],
  quote: '“Then the flame goes to one who will carry it.”' };
const VN = { shots: [], rings: [], ghosts: [], flame: null, endT: 0, voice: null };
const VN_META = () => ASSETS.venn_boss_meta || { sheets: {}, attacks: {}, telegraph: {}, spawn: {}, anchor: [96, 122], hurtbox: [86, 60, 17, 58] };
const vnDmg = d => BOSS_DMG * d * NGP.dmg * 1.1;          // final-boss tier (same family as the Sovereign's 1.15)
const VN_ROOM = 'X5', VN_FLOORY = () => 11 * TILE;        // X5: floor rows 11-13
const VN_P2AT = 0.6, VN_P3AT = 0.2;

function vnSheet(tag, ph) {
  const S = VN_META().sheets || {};
  let n = (S['p' + ph] || {})[tag];
  if (!n) for (const q of [ph, 3, 2, 1]) if ((S['p' + q] || {})[tag]) { n = S['p' + q][tag]; break; }
  return sheet(n || 'venn_boss_p1_1', { meta: VN_META() });
}
function vnWindows(tag, ph) {
  const A = VN_META().attacks || {};
  for (const q of [ph, 3, 2, 1]) { const a = (A['p' + q] || {})[tag]; if (a) return a.windows || []; }
  return [];
}
function vnMetaAt(kind, tag, ph) {
  const M = VN_META()[kind] || {};
  for (const q of [ph, 3, 2, 1]) { const a = (M['p' + q] || {})[tag]; if (a) return a; }
  return null;
}

// ---- move table: tag = animation, dmg per window, parry per window, step (px/s) by frame, on = frame events
const VN_MOVES = {
  sweep:   { tag: 'sweep', dmg: [54], parry: [true], step: { 3: 130, 4: 90, 5: 30 } },
  reap:    { tag: 'reap', dmg: [50, 46], parry: [true, true], step: { 2: 120, 3: 90, 6: -40, 7: -30 } },
  rising:  { tag: 'rising', dmg: [46], parry: [true], step: { 3: 60 }, on: { 4() { vnCrescent(this); } } },
  pillars: { tag: 'cast', on: { 6() { vnPillars(this); } } },
  ring:    { tag: 'cast', on: { 6() { vnRing(this); } } },
  heal:    { tag: 'heal', on: { 8() { vnHeal(this); } } },
  lance:   { tag: 'lance', dmg: [58], parry: [false], on: { 6() { vnSpikesAt(this, [P.x - 18, P.x + 18], 0.55); } } },
  dive:    { tag: 'dive', dmg: [62], parry: [false], on: { 9() { vnLand(this, 2); } } },
  absorb:  { tag: 'absorb' },
  flurry:  { tag: 'flurry', dmg: [40, 40, 60], parry: [true, true, false], step: { 1: 230, 2: 120, 5: 170, 6: 90, 9: 260, 10: 120 },
             on: { 10() { vnLand(this, 1); } } },
  slam:    { tag: 'slam', dmg: [66], parry: [false], on: { 6() { vnLand(this, 3); } } },
  blinkcut: { tag: 'blink' },
};

class VennBoss extends BossBase {
  constructor(x, y) {
    super('venn', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.venn.hp * NGP.hp);
    this.stanceMax = this.stanceBase = 330; this.critRange = 52; this.speed = 1;
    this.state = 'dormant'; this.face = -1; this.recent = []; this.heals = 0; this.absorbs = 0; this.cool = 0.8;
    this.hidden = false; this.airH = 0; this.name = BOSS_INFO.venn.name;
    this.setS('dormant', 'idle', true);
  }
  // the arena between the fog at column 1 and the east wall, with room for the scythe to swing
  get L() { return 2 * TILE + 40; }
  get R() { return room.pw - TILE - 40; }
  setS(st, tag, loop = true) {
    this.state = st; this.tag = tag;
    this.sh = vnSheet(tag, this.phase);
    this.anim = new Anim(this.sh, tag, loop, this.speed);
  }
  facePlayer() { if (Math.abs(P.x - this.x) > 5) this.face = P.x < this.x ? -1 : 1; }
  wake() { return P.x > 7 * TILE && P.ground && P.state !== 'dead'; }
  activate() { vnDusk(1); super.activate(); }
  hurtbox() {
    if (!this.alive || this.hidden) return null;
    if (this.state === 'attack' && this.atk === 'blinkcut' && (this.anim.i >= 2 && this.anim.i <= 7)) return null;   // dissolved into fire
    const M = VN_META(), kneel = this.state === 'attack' && this.atk === 'heal' && this.anim.i >= 2 && this.anim.i <= 10;
    return metaRect(this.sh, this, (kneel && M.hurtbox_kneel) || M.hurtbox || [86, 60, 17, 58]);
  }
  canStagger() { return !this.airH && this.state !== 'transform' && !(this.state === 'attack' && ['blinkcut', 'dive', 'slam'].includes(this.atk)); }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  stagger() {
    this.critDone = false; this.stanceImmune = 7; this.staggers = (this.staggers || 0) + 1;
    this.stanceMax = Math.min(this.stanceMax * 1.15, this.stanceBase * 2);
    this.stance = 0; this.chain = 0; this.airH = 0; this.y = this.floor; this.hidden = false;
    this.setS('stagger', 'stagger', false); this.t = 2.0;
    sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 44, this.face);
  }
  hit(info) {
    if (!this.alive || !this.active) { if (!this.active && !this.cutting) this.activate(); return; }
    if (this.state === 'transform') return;
    const before = this.hp;
    super.hit(info);
    if (!this.alive) return;
    // phases can't be skipped: the change plays out first
    if (this.phase === 1 && this.hp < this.maxHp * VN_P2AT) { this.hp = Math.round(this.maxHp * VN_P2AT); this.pendingPhase = 2; }
    if (this.phase === 2 && this.hp < this.maxHp * VN_P3AT) { this.hp = Math.round(this.maxHp * VN_P3AT); this.pendingPhase = 3; }
    const dealt = before - this.hp;
    // the heal and the absorb are punishable: enough damage breaks them into a full stagger
    if (this.state === 'attack' && (this.atk === 'heal' || this.atk === 'absorb')) {
      this.brk = (this.brk || 0) + dealt;
      if (this.atk === 'heal' && this.anim.i < 8 && this.brk > this.maxHp * 0.035 && this.state !== 'stagger') { toast('The flask slips from her hands.', 2); this.stagger(); }
      if (this.atk === 'absorb' && this.brk > this.maxHp * 0.05 && this.state !== 'stagger') { toast('The Root’s grace scatters.', 2); this.chan = 0; this.stagger(); }
    }
  }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 95; if (this.stance >= this.stanceMax && this.canStagger()) this.stagger(); }

  // ---------------------------------------------------------------- choosing
  weights(d) {
    const ph = this.phase, hurt = this.hp / this.maxHp;
    if (ph === 1) {
      const w = d < 95 ? { sweep: 3, reap: 2.2, ring: d < 70 ? 1.0 : 0.4, pillars: 0.6, glide: 0.3 }
                       : { rising: 2.2, pillars: 1.8, ring: 0.4, glide: 2.0 };
      if (hurt < 0.86 && this.heals < 2 && d > 80 && Math.random() < 0.5) w.heal = 2.2;
      return w;
    }
    if (ph === 2) {
      if (hurt < 0.45 && this.absorbs < 1) return { absorb: 1 };
      return d < 95 ? { sweep: 2, reap: 2.4, lance: d > 50 ? 1.2 : 0.4, dive: 0.8, ring: 0.9 }
                    : { lance: d < 170 ? 2.2 : 0.6, dive: 2.2, rising: 1.6, pillars: 1.3, glide: 1.0 };
    }
    return d < 100 ? { flurry: 2.6, blinkcut: 1.4, slam: 1.2 } : { blinkcut: 2.8, slam: 2.0, flurry: 0.6 };
  }
  pickMove() {
    const w = this.weights(Math.abs(P.x - this.x));
    if (w[this.last] && Object.keys(w).length > 1) w[this.last] *= 0.25;
    if (this.recent[1] && w[this.recent[1]] && Object.keys(w).length > 2) w[this.recent[1]] *= 0.6;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e[0][0];
  }
  start(m) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.brk = 0;
    this.recent.unshift(m); this.recent.length = Math.min(this.recent.length, 3);
    if (m === 'glide') {
      const side = Math.abs(P.x - this.L) < 90 ? 1 : Math.abs(P.x - this.R) < 90 ? -1 : (P.x < this.x ? 1 : -1);
      const far = Math.abs(P.x - this.x) > 140;
      this.glideTo = clamp(far ? P.x + side * 70 : P.x + side * rand(110, 150), this.L + 10, this.R - 10);
      this.setS('glide', 'glide'); this.t = 1.3; return;
    }
    const M = VN_MOVES[m];
    this.setS('attack', M.tag, false);
    this.x0 = this.x;
    if (m === 'heal') { this.heals++; if (!F('vn_flask')) { setF('vn_flask'); toast('Venn drinks from the flask she once gave you.', 3); } }
    if (m === 'absorb') { this.absorbs++; this.chan = 3.4; this.spT = 0.4; this.spK = 0; sfx.charge(); toast('Venn drinks the dying Root.', 2.5); }
    if (m === 'dive' || m === 'slam') this.air = { tx: this.x };
  }
  // ---------------------------------------------------------------- update
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim;
    if (this.state === 'dead') {
      an.update(dt); if (an.done) { an.hold(); this.gone = true; }
      if (!this.gone && Math.random() < 0.5) particles.push({ x: this.x + rand(-14, 14), y: this.y - rand(0, 50), vx: rand(-8, 8), vy: -rand(15, 45), life: rand(1, 2), kind: Math.random() < 0.5 ? 'ash' : 'mote' });
      return;
    }
    if (this.state === 'transform') { this.ambient(dt); return; }
    if (!this.active) { an.update(dt); if (!this.cutting && this.wake()) this.activate(); this.ambient(dt); return; }
    an.speed = this.speed;
    an.update(dt);
    if (this.pendingPhase && ['idle', 'glide'].includes(this.state) && P.state !== 'dead' && state === 'play') return this.phaseScene(this.pendingPhase);
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'dormant': case 'idle':
        if (this.state === 'dormant') this.state = 'idle';
        this.facePlayer(); this.cool -= dt;
        if (P.state !== 'dead' && this.cool <= 0) this.start(this.pickMove());
        break;
      case 'glide': {
        this.t -= dt; this.face = this.glideTo < this.x ? -1 : 1;
        this.x = approach(this.x, this.glideTo, (this.phase === 1 ? 135 : 175) * dt);
        if (Math.random() < 0.4) particles.push({ x: this.x - this.face * rand(4, 16), y: this.y - rand(2, 10), vx: -this.face * rand(10, 30), vy: -rand(4, 16), life: 0.6, kind: 'mote' });
        if (this.t <= 0 || Math.abs(this.x - this.glideTo) < 3) { this.facePlayer(); this.setS('idle', 'idle'); this.cool = this.phase === 1 ? 0.25 : 0.12; }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.setS('idle', 'idle'); this.cool = 0.35; }
        break;
    }
    this.x = clamp(this.x, this.L, this.R);
    if (!this.airH) this.y = this.floor; else this.y = this.floor - this.airH;
    this.ambient(dt);
  }
  updateAttack(dt) {
    const an = this.anim, M = VN_MOVES[this.atk], wins = vnWindows(M.tag, this.phase), ph = this.phase;
    const first = wins.length ? wins[0].active[0] : 99;
    if (an.i < first - 1 && !['dive', 'slam', 'blinkcut'].includes(this.atk)) this.facePlayer();
    // glints before each strike
    const tel = vnMetaAt('telegraph', M.tag, ph);
    if (tel && an.changed) for (const tq of tel) if (an.i === tq.frame) { const p = metaPoint(this.sh, this, tq.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    // stepping into the cut
    if (M.step && M.step[an.i] !== undefined) this.x = clamp(this.x + this.face * M.step[an.i] * dt, this.L, this.R);
    // special movement
    if (this.atk === 'dive') this.diveMove(dt);
    else if (this.atk === 'slam') this.slamMove(dt);
    else if (this.atk === 'blinkcut') { if (this.blinkMove(dt)) return; }
    else if (this.atk === 'absorb') this.absorbTick(dt);
    // hit windows
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (ph >= 2) sfx.fire(); }
      if (this.hitIds.has(wi)) return;
      const r = metaRect(this.sh, this, (w.rects && w.rects[an.i]) || w.hit);
      if (overlap(r, playerHurtbox())) {
        const dmg = vnDmg((M.dmg && (M.dmg[wi] ?? M.dmg[0])) || 45) * (this.empowered ? 1.1 : 1);
        if (hurtPlayer(dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: !!(M.parry && M.parry[wi]), src: this })) this.hitIds.add(wi);
      }
    });
    if (M.on) for (const [fi, fn] of Object.entries(M.on)) if (an.changed && an.i === +fi && !this.fired[fi]) { this.fired[fi] = true; fn.call(this); }
    if (M.tag === 'cast' && an.changed && an.i === 3) { sfx.charge(); }
    if (an.done) {
      this.airH = 0; this.y = this.floor; this.air = null;
      const d = Math.abs(P.x - this.x);
      // phase 3 chains its moves together; earlier phases sometimes follow a cut with another
      const chainP = ph === 3 ? 0.55 : ph === 2 ? 0.4 : 0.25;
      if (this.pendingPhase) { this.setS('idle', 'idle'); this.cool = 0.1; return; }
      if (['sweep', 'reap', 'flurry', 'rising'].includes(this.atk) && this.chain < (ph === 3 ? 2 : 1) && Math.random() < chainP && P.state !== 'dead') {
        this.chain++;
        const nx = ph === 3 ? (d < 90 ? 'flurry' : 'blinkcut') : ph === 2 ? (d < 90 ? (this.atk === 'reap' ? 'sweep' : 'reap') : 'lance') : (d < 90 ? 'reap' : 'rising');
        if (nx !== this.atk || ph === 3) return this.start(nx);
      }
      this.chain = 0; this.setS('idle', 'idle');
      this.cool = ph === 1 ? rand(0.75, 1.35) : ph === 2 ? rand(0.5, 1.0) : rand(0.25, 0.6);
    }
  }
  frameK() { const an = this.anim; return clamp(an.t / Math.max(1, an.ms()), 0, 1); }
  diveMove(dt) {
    const i = this.anim.i, k = this.frameK(), A = this.air;
    const H = [0, 0, lerp(0, 45, k), lerp(45, 72, k), 72, 72, 72, lerp(72, 36, k), lerp(36, 0, k)][i] ?? 0;
    this.airH = Math.max(0, H);
    if (i >= 4 && i <= 6) { this.facePlayer(); A.tx = clamp(P.x - this.face * 12, this.L, this.R); this.x = approach(this.x, A.tx, 150 * dt); }
    if (i >= 7 && i <= 8) this.x = approach(this.x, A.tx, 320 * dt);
    if (this.anim.changed && i === 3) { sfx.howl(); for (let n = 0; n < 16; n++) particles.push({ x: this.x + rand(-40, 40), y: this.floor - rand(0, 10), vx: rand(-80, 80), vy: -rand(20, 80), life: 0.7, kind: 'ash' }); }
  }
  slamMove(dt) {
    const i = this.anim.i, k = this.frameK(), A = this.air;
    if (this.anim.changed && i === 2) { A.x0 = this.x; A.tx = clamp(P.x, this.L, this.R); sfx.jump(); }
    const H = [0, 0, lerp(0, 60, k), lerp(60, 72, k), lerp(72, 60, k), lerp(60, 0, k)][i] ?? 0;
    this.airH = Math.max(0, H);
    if (i >= 2 && i <= 5 && A.x0 !== undefined) { const t = (i - 2 + k) / 4; this.x = lerp(A.x0, A.tx, t); }
  }
  blinkMove(dt) {
    const an = this.anim;
    if (this.bl === undefined) this.bl = 0;
    if (an.i === 4 && !this.blinkWait && !this.blinkDone) {
      // gone: a glint where she will return
      this.blinkWait = 0.42; this.hidden = true; an.speed = 0;
      const behind = clamp(P.x - (P.face || 1) * 44, this.L, this.R), front = clamp(P.x + (P.face || 1) * 52, this.L, this.R);
      this.blinkTo = Math.abs(behind - P.x) > 30 ? behind : front;
      spawnFx('telegraph', this.blinkTo, this.floor - 30, 1); sfx.glint();
      spawnFx(fxOr('vn_burst', 'holy_burst'), this.x, this.floor - 30, 1);
    }
    if (this.blinkWait > 0) {
      this.blinkWait -= dt;
      if (this.blinkWait <= 0) {
        this.blinkDone = true; this.blinkWait = 0; this.hidden = false; this.x = this.blinkTo; this.facePlayer();
        an.i = 5; an.t = 0; an.speed = this.speed; an.changed = true; spawnFx(fxOr('vn_burst', 'holy_burst'), this.x, this.floor - 30, 1);
      }
      return true;
    }
    if (an.done && this.blinkDone) { this.blinkDone = false; this.hidden = false; this.start('flurry'); return true; }
    return false;
  }
  absorbTick(dt) {
    const an = this.anim;
    if (this.chan > 0) {
      this.chan -= dt;
      if (an.i >= 9 && this.chan > 0) { an.i = 4; an.t = 0; }
      // the Root's last grace streams in along the floor
      for (let n = 0; n < 2; n++) { const sx = rand(this.L - 30, this.R + 30); particles.push({ x: sx, y: this.floor - 2, vx: (this.x - sx) * 0.9, vy: -rand(30, 60), life: 1.1, kind: 'mote' }); }
      addLight(this.x, this.y - 44, 90, '255,230,170', 0.9);
      this.spT -= dt;
      if (this.spT <= 0) {   // alternating rows of burning roots across the arena: stand in the gaps
        this.spT = 0.95; this.spK++;
        const xs = []; for (let x = this.L - 20 + (this.spK % 2) * 40; x <= this.R + 20; x += 80) if (Math.abs(x - this.x) > 26) xs.push(x);
        vnSpikesAt(this, xs, 0.6);
      }
      if (this.chan <= 0) { this.hp = Math.min(this.maxHp * VN_P2AT, this.hp + this.maxHp * 0.05); this.empowered = true; popup(this.x, this.y - 70, Math.round(this.maxHp * 0.05), '#fff0b0'); sfx.heal(); flashScreen = 0.3; }
    } else if (an.i >= 4 && an.i < 10) { an.i = 10; an.t = 0; an.changed = true; }
  }
  phaseScene(ph) {
    this.pendingPhase = 0; hazards = hazards.filter(h => !h.vn); VN.shots = []; VN.rings = [];
    this.state = 'transform'; this.stance = 0; this.airH = 0; this.y = this.floor; this.hidden = false; this.chain = 0; this.facePlayer();
    const b = this, first = !SAVE.flags['cutp' + ph + ':venn'];
    SAVE.flags['cutp' + ph + ':venn'] = 1;
    let steps;
    if (ph === 2) {
      steps = [
        { pan: { x: b.x, y: b.y - 50 }, dur: 0.5 },
        act(() => { b.phase = 2; b.sh = vnSheet('transform', 2); b.anim = new Anim(b.sh, 'transform', false, 0.9); sfx.fire(); }),
        ...(first ? [say('Sister Venn', 'You would not even let me carry it gently.')] : [wait(0.6)]),
        { dur: 1.4, tween: () => { if (Math.random() < 0.9) particles.push({ x: b.x + rand(-6, 6), y: b.y - rand(40, 60), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.5, 1), kind: 'fire' }); } },
        act(() => { flashScreen = 0.8; shake = 10; sfx.roar(); spawnFx(fxOr('vn_burst', 'roar_ring'), b.x, b.y - 50, 1); for (let i = 0; i < 40; i++) particles.push({ x: b.x + rand(-60, 60), y: b.y - rand(20, 90), vx: rand(-60, 60), vy: -rand(20, 90), life: rand(0.6, 1.4), kind: Math.random() < 0.5 ? 'fire' : 'ember' }); }),
        ...(first ? [say('Sister Venn', 'Then burn with me. The Root will have its heart.')] : [wait(0.5)]),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ];
    } else {
      steps = [
        { pan: { x: b.x, y: b.y - 50 }, dur: 0.5 },
        act(() => { b.phase = 3; b.setS('transform', 'stagger', false); b.anim.speed = 0.7; sfx.glint(); shake = 6; }),
        wait(0.6),
        act(() => { flashScreen = 0.5; sfx.crumble(); b.setS('transform', 'idle'); spawnFx(fxOr('vn_burst', 'holy_burst'), b.x, b.y - 58, 1); for (let i = 0; i < 24; i++) particles.push({ x: b.x + rand(-12, 12), y: b.y - rand(50, 70), vx: rand(-40, 40), vy: rand(-20, 60), g: 200, life: rand(0.6, 1.2), kind: 'spark' }); }),
        ...(first ? [say('Sister Venn', '…please.', { dur: 2.0 })] : [wait(0.4)]),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ];
    }
    playCutscene(steps, () => {
      b.phase = ph; b.speed = ph === 2 ? 1.12 : 1.3; b.stanceMax = b.stanceBase = ph === 2 ? 360 : 300; b.stanceImmune = 0;
      b.setS('idle', 'idle'); b.cool = ph === 3 ? 0.3 : 0.6;
      vnDusk(ph);
      if (ph === 3) { b.name = 'Venn, the Last Kindling'; vnVoice(true); }
      bossBanner = { name: b.name, t: 0 };
    });
  }
  die() {
    // she cannot fall before the last phase: a killing blow ends the phase instead
    if (this.phase < 3) { this.hp = Math.max(1, Math.round(this.maxHp * (this.phase === 1 ? VN_P2AT : VN_P3AT))); this.pendingPhase = this.phase + 1; return; }
    this.state = 'dead'; this.hidden = false; this.airH = 0; this.y = this.floor; this.phase = 3;
    this.setS('dead', 'death', false);
    hazards = hazards.filter(h => !h.vn); VN.shots = []; VN.rings = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 2.0; flashScreen = 0.8; sfx.felled(); vnVoice(false);
    victoryBanner = { text: 'THE LAST KINDLING GOES OUT', t: 0 };
    SAVE.flags.venn_betrayed = 1;
    this.rewards();
    VN.endT = 8.2;           // after the rewards: the last flame comes to you, and the ending plays
  }
  ambient(dt) {
    if (this.hidden || this.state === 'dead' && this.anim.i > 8) return;
    const k = this.phase === 3 ? 0.8 : 1;
    addLight(this.x - this.face * 3, this.y - 60, 46 * k, '255,240,210', 0.6);
    addLight(this.x, this.y - 30, 40, '235,228,220', 0.35);            // her pale robes catch her own light
    if (this.phase >= 2 && Math.random() < 0.35) particles.push({ x: this.x - this.face * rand(10, 50), y: this.y - rand(40, 80), vx: rand(-10, 10), vy: -rand(10, 30), life: rand(0.5, 1), kind: 'ember' });
    if (this.phase === 3 && Math.random() < 0.3) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(50, 64), vx: rand(-6, 6), vy: rand(10, 30), life: 0.8, kind: 'spark' });
    // phase 3 leaves afterimages when she moves fast
    if (this.phase === 3 && this.state === 'attack' && ['flurry', 'slam'].includes(this.atk) && (this.ghostT = (this.ghostT || 0) - dt) <= 0) {
      this.ghostT = 0.05; VN.ghosts.push({ sh: this.sh, f: this.anim.frame, x: this.x, y: this.y, face: this.face, life: 0.25 });
    }
  }
  draw() {
    for (const gh of VN.ghosts) drawSprite(gh.sh, gh.f, gh.x, gh.y, gh.face, { alpha: gh.life / 0.25 * 0.4, flash: 1, flashColor: '#fff4d8' });
    if (this.hidden) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.6 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'dead' && this.gone) return;
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 70 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
  }
}

// ---------------------------------------------------------------- attacks that leave the body
function vnMarkHazard(o) {
  const h = { vn: true, x: o.x, y: o.y, w: o.w, h: o.h, dmg: vnDmg(o.dmg), id: ++hazardId, life: 4, delay: o.delay, fx: null, markT: o.delay,
    onStart: h => { h.fx = spawnFx(fxOr(o.fx, o.alt), h.x, h.y, 1, null, { bottom: true }); if (!h.fx) h.life = 0; else o.snd && o.snd(); },
    update: h => { if (!h.fx || h.fx.anim.done) { h.life = 0; return; } if (h.fx.anim.i >= o.act[0] && h.fx.anim.i <= o.act[1]) addLight(h.x, h.y - h.h / 2, 46, '255,235,180', 0.8); },
    active: h => h.fx && h.fx.anim.i >= o.act[0] && h.fx.anim.i <= o.act[1] };
  hazards.push(h); return h;
}
function vnPillar(x, fl, delay, dmg = 42) {
  return vnMarkHazard({ x, y: fl, w: 16, h: 100, dmg, delay, fx: 'vn_pillar', alt: 'lightpillar', act: [3, 5], snd: () => { sfx.pillar(); shake = Math.max(shake, 2); } });
}
function vnSpike(x, fl, delay, dmg = 44) {
  return vnMarkHazard({ x, y: fl, w: 12, h: 62, dmg, delay, fx: 'vn_spike', alt: 'root_spike', act: [3, 5], snd: () => sfx.pillar() });
}
function vnPillars(b) {
  const fl = b.floor, n = b.phase === 1 ? 5 : 6;
  sfx.kindle();
  // a procession of shrine-light toward you, then one where you stand
  for (let k = 0; k < n; k++) { const x = b.x + b.face * (34 + k * 34); if (x > b.L - 30 && x < b.R + 30) vnPillar(x, fl, 0.35 + k * 0.13); }
  vnPillar(clamp(P.x, b.L - 30, b.R + 30), fl, 0.95);
  if (b.phase >= 2) for (const dx of [-54, 54]) vnSpike(clamp(P.x + dx, b.L - 30, b.R + 30), fl, 1.25);
}
function vnSpikesAt(b, xs, delay) { xs.forEach((x, k) => vnSpike(clamp(x, 2 * TILE + 8, room.pw - TILE - 8), b.floor, delay + k * 0.02)); }
function vnRing(b) {
  const at = vnMetaAt('spawn', 'cast', b.phase), p = at ? metaPoint(b.sh, b, at.heart) : { x: b.x, y: b.y - 44 };
  const n = b.phase >= 2 ? 2 : 1;
  for (let k = 0; k < n; k++) VN.rings.push({ x: p.x, y: p.y, r: 6 - k * 70, v: 150, id: ++hazardId, dmg: vnDmg(40), fl: b.floor });
  sfx.kindle(); flashScreen = 0.25; spawnFx(fxOr('vn_burst', 'holy_burst'), p.x, p.y, 1);
}
function vnCrescent(b) {
  const mk = (dir, spd) => VN.shots.push({ kind: 'crescent', x: b.x + dir * 30, y: b.floor, vx: dir * spd, dir, life: 3, id: ++hazardId, dmg: vnDmg(b.phase >= 2 ? 38 : 34), w: 18, h: 26 });
  mk(b.face, b.phase >= 2 ? 230 : 200);
  if (b.phase >= 2) { for (let k = 1; k <= 3; k++) vnSpike(b.x - b.face * (28 + k * 30), b.floor, 0.25 + k * 0.12); }
  sfx.fire();
}
function vnLand(b, kind) {
  shake = kind === 3 ? 12 : 9; sfx.boom();
  spawnFx(fxOr('slam_impact', 'shockwave'), b.x + b.face * 26, b.floor, b.face);
  for (let i = 0; i < 16; i++) particles.push({ x: b.x + rand(-30, 30), y: b.floor - 2, vx: rand(-120, 120), vy: -rand(30, 140), g: 300, life: 0.7, kind: i % 2 ? 'fire' : 'ash' });
  if (kind === 1) return;
  const spd = kind === 3 ? 190 : 160;
  for (const dir of [-1, 1]) VN.shots.push({ kind: 'wave', x: b.x + dir * 22, y: b.floor, vx: dir * spd, dir, life: kind === 3 ? 2.6 : 1.1, id: ++hazardId, dmg: vnDmg(kind === 3 ? 42 : 34), w: 20, h: 22 });
}
function vnHeal(b) {
  if (b.state !== 'attack' || b.atk !== 'heal') return;
  const n = Math.round(b.maxHp * 0.07);
  b.hp = Math.min(b.maxHp, b.hp + n); b.displayHp = Math.min(b.displayHp, b.hp);
  popup(b.x, b.y - 60, n, '#fff0b0'); sfx.heal(); spawnFx(fxOr('vn_burst', 'heal'), b.x, b.y - 36, 1);
  for (let i = 0; i < 20; i++) particles.push({ x: b.x + rand(-16, 16), y: b.y - rand(0, 50), vx: 0, vy: -rand(20, 50), life: 1, kind: 'mote' });
}

// ---------------------------------------------------------------- the Heart dims as she burns (lighting only; parallax borrowed from the Crown)
Object.assign(AREAS, {
  vn_dusk1: { name: 'The Heart of the Pale Root', ambient: 0.4, amb: 'petal', tint: '#aab3c4' },
  vn_dusk2: { name: 'The Heart of the Pale Root', ambient: 0.6, amb: 'ash', tint: '#6e6a7a' },
  vn_dusk3: { name: 'The Heart of the Pale Root', ambient: 0.72, amb: 'ash', tint: '#2a2632' },
});
for (const n of ['vn_dusk1', 'vn_dusk2', 'vn_dusk3']) { Object.assign(SCALES, { [n]: SCALES.crown }); Object.assign(ROOTS, { [n]: ROOTS.crown }); }
function vnDusk(lv) {
  if (!room || room.id !== VN_ROOM) return;
  const base = room.def.vnBase || room.def;
  if (!lv) { room.def = base; return; }
  for (const k of ['far', 'mid']) if (!SHEETS[`bg_vn_dusk${lv}_${k}`]) SHEETS[`bg_vn_dusk${lv}_${k}`] = sheet(`bg_${base.biome}_${k}`);
  room.def = Object.assign(Object.create(base), { biome: 'vn_dusk' + lv, vnBase: base });
}

// ---------------------------------------------------------------- the voice (phase 3: the score falls to a single voice)
Object.assign(SCALES, { vn_hush: [0, 3, 7] });
Object.assign(ROOTS, { vn_hush: 41.2 });
const _vnMusicMode = musicMode;
musicMode = function () {
  const b = boss;
  if (b && b.kind === 'venn' && b.alive && b.active && b.phase === 3 && room && room.id === VN_ROOM && state !== 'dead') return 'vn_hush';
  return _vnMusicMode();
};
function vnVoice(on) {
  const ac = AC;
  if (!on) { if (VN.voice) { const v = VN.voice; try { v.g.gain.setTargetAtTime(0.0001, ac.currentTime, 0.6); v.o.stop(ac.currentTime + 2.5); v.lfo.stop(ac.currentTime + 2.5); } catch (e) {} VN.voice = null; } return; }
  if (!ac || VN.voice || muted) return;
  try {
    // a lone wordless voice: a soft saw through a vowel formant, slow vibrato, sliding between two notes
    const o = ac.createOscillator(), f1 = ac.createBiquadFilter(), gn = ac.createGain(), lfo = ac.createOscillator(), lg2 = ac.createGain();
    o.type = 'sawtooth'; o.frequency.value = 220; f1.type = 'bandpass'; f1.frequency.value = 800; f1.Q.value = 4;
    lfo.frequency.value = 5.2; lg2.gain.value = 3.5; lfo.connect(lg2).connect(o.frequency);
    gn.gain.value = 0.0001; o.connect(f1).connect(gn).connect(ac.destination);
    o.start(); lfo.start(); gn.gain.setTargetAtTime(0.05 * SETTINGS.music, ac.currentTime, 1.5);
    VN.voice = { o, g: gn, lfo, t: 0, step: 0 };
  } catch (e) {}
}
const VN_MELODY = [220, 196, 220, 261.6, 246.9, 220, 196, 174.6];

// ---------------------------------------------------------------- the arena, the choice, the finale
function vnAddFog() {
  if (!room || room.id !== VN_ROOM) return;
  let fp = props.find(p => p.type === 'fog');
  const x = 1, y = 10, cx = x * TILE + 8, fy = (y + 1) * TILE;
  if (!fp) { fp = makeProp('fog', cx, fy, { exit: false }); props.push(fp); }
  fp.on = () => !!(boss && boss.kind === 'venn' && boss.alive && boss.active);
  if (!room.dyn.some(d => d.vnFog)) room.dyn.push({ vnFog: true, x0: x * TILE, x1: x * TILE + 16, y0: (y - 4) * TILE, y1: fy, on: fp.on });
}
function vnEndingNpc() {
  const throne = props.find(p => p.type === 'throne');
  const npc = makeNpc('venn', throne ? throne.x - 30 : room.pw - 90, VN_FLOORY());
  npc.vnEnd = true; npc.interact = () => vnOfferEnding(npc);
  props.push(npc); return npc;
}
function vnBetray(npc) {
  SAVE.flags.venn_betrayed = 1; dialogAfterEnding = false; saveGame();
  const x = npc ? npc.x : P.x + 60;
  props = props.filter(p => p !== npc && !p.vnEnd);
  const b = new VennBoss(0, VN_FLOORY());
  b.x = clamp(x, b.L, b.R); b.face = P.x < b.x ? -1 : 1;
  b.setS('dormant', 'summon', false); b.anim.speed = 0;
  boss = b; vnAddFog(); b.activate();
}
function vnFinale() {
  if (!room || room.id !== VN_ROOM || SAVE.ending) return;
  const fl = VN_FLOORY(), x0 = boss && boss.kind === 'venn' ? boss.x : P.x + 40;
  VN.flame = { x: x0, y: fl - 22, t: 0 };
  playCutscene([
    { pan: { x: (x0 + P.x) / 2, y: fl - 50 }, dur: 1.0 },
    say('', 'Where she knelt there is only ash — and a small white flame, still burning.'),
    { dur: 2.4, tween: (dt, k) => { const e = k * k * (3 - 2 * k); VN.flame.x = lerp(x0, P.x + P.face * 6, e); VN.flame.y = lerp(fl - 22, P.y - 16, e) - Math.sin(k * Math.PI) * 26; } },
    act(() => { VN.flame = null; flashScreen = 1; shake = 4; sfx.kindle(); spawnFx(fxOr('vn_burst', 'holy_burst'), P.x, P.y - 16, 1); P.flash = 1; }),
    say('', 'You close your hand around the last flame of the Hallow.'),
    wait(0.8),
  ], () => { VN.flame = null; SAVE.ending = 'venn'; dialogAfterEnding = false; finishStory(); });
}
function vnClear() { VN.shots = []; VN.rings = []; VN.ghosts = []; VN.flame = null; }

HOOKS.enter.push(def => {
  vnClear(); VN.endT = 0; vnVoice(false);
  if (SAVE.flags.venn_betrayed) props = props.filter(p => !(p.type === 'npc' && p.id === 'venn'));   // she will not tend your shrines again
  if (def.id !== VN_ROOM || !SAVE.flags['boss:sovereign']) return;
  if (SAVE.flags.venn_betrayed && !SAVE.flags['boss:venn'] && !boss) {
    // she waits at the empty throne; the fog closes once you step in
    const b = new VennBoss(0, VN_FLOORY()); b.x = clamp(room.pw - 150, b.L, b.R); b.face = -1;
    boss = b; vnAddFog();
  } else if (!SAVE.ending && !SAVE.flags.venn_betrayed) vnEndingNpc();      // the choice is still waiting to be made
});
HOOKS.death.push(() => { vnClear(); vnVoice(false); });
HOOKS.update.push(dt => {
  for (const gh of VN.ghosts) gh.life -= dt;
  VN.ghosts = VN.ghosts.filter(gh => gh.life > 0);
  const B = boss && boss.kind === 'venn' ? boss : null;
  if (VN.endT > 0 && (VN.endT -= dt) <= 0) { if (state === 'play' && P.state !== 'dead') vnFinale(); else VN.endT = 0.5; }
  if (VN.voice && AC) {   // the voice sings slowly
    const v = VN.voice; v.t -= dt;
    if (v.t <= 0) { v.t = rand(1.6, 2.6); v.step++; v.o.frequency.setTargetAtTime(VN_MELODY[v.step % VN_MELODY.length], AC.currentTime, 0.25); }
    if (!B || !B.alive || room.id !== VN_ROOM) vnVoice(false);
  }
  if (!B) { if (VN.shots.length || VN.rings.length) { VN.shots = []; VN.rings = []; } return; }
  // ground-running flames: the rising crescent, the landing waves
  for (const s of VN.shots) {
    s.life -= dt; s.x += s.vx * dt;
    if (s.x < TILE + 4 || s.x > room.pw - TILE - 4) s.life = 0;
    if (Math.random() < 0.5) particles.push({ x: s.x - s.dir * rand(0, 10), y: s.y - rand(0, s.h * 0.6), vx: -s.dir * rand(5, 25), vy: -rand(20, 50), life: 0.5, kind: 'fire' });
    addLight(s.x, s.y - 12, 40, '255,225,160', 0.9);
    if (!s.hit && overlap(rect(s.x - s.w / 2, s.y - s.h, s.x + s.w / 2, s.y), playerHurtbox()) && hurtPlayer(s.dmg, s.dir, s.id, { src: B, burn: 15 })) s.hit = true;
  }
  VN.shots = VN.shots.filter(s => s.life > 0);
  // rings of white fire from her halo: roll through them
  for (const r of VN.rings) {
    r.r += r.v * dt;
    if (r.r <= 0) continue;
    const d = Math.hypot(P.x - r.x, P.y - 12 - r.y);
    if (!r.hit && Math.abs(d - r.r) < 7 && hurtPlayer(r.dmg, P.x < r.x ? -1 : 1, r.id, { src: B })) r.hit = true;
  }
  VN.rings = VN.rings.filter(r => r.r < 420);
});
HOOKS.render.push(() => {
  // floor glyphs under pending pillars / spikes
  const mk = fxSheet('vn_mark');
  for (const h of hazards) if (h.vn && h.delay > 0) {
    const a = 0.5 + 0.5 * Math.sin(time * 18);
    if (mk.ok) { const t = mk.tag(Object.keys(mk.tags)[0]); drawSprite(mk, t.from + Math.floor(time * 12) % (t.to - t.from + 1), h.x, h.y, 1, { bottom: true, alpha: a }); }
    else { g.fillStyle = `rgba(255,220,150,${a})`; g.fillRect(Math.round(h.x - 7), Math.round(h.y) - 1, 14, 1); }
    addLight(h.x, h.y - 4, 22, '255,220,150', 0.5 * a);
  }
  for (const s of VN.shots) {
    const sh = fxSheet(s.kind === 'crescent' ? 'vn_crescent' : 'vn_wave');
    if (sh.ok) { const t = sh.tag(Object.keys(sh.tags)[0]); drawSprite(sh, t.from + Math.floor(time * 14) % (t.to - t.from + 1), s.x, s.y, s.dir, { bottom: true }); }
    else { g.fillStyle = '#ffe4a0'; g.fillRect(Math.round(s.x - 6), Math.round(s.y - s.h), 12, s.h); }
  }
  for (const r of VN.rings) {
    if (r.r <= 0) continue;
    const n = Math.max(24, Math.floor(r.r * 0.9)), a = clamp(1.3 - r.r / 420, 0.25, 1);
    for (let k = 0; k < n; k++) {
      const th = k / n * 6.283, x = r.x + Math.cos(th) * r.r, y = r.y + Math.sin(th) * r.r;
      if (y > r.fl + 1) continue;
      g.fillStyle = `rgba(255,${k % 3 ? 238 : 250},${k % 3 ? 190 : 235},${a})`; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2);
    }
    for (let k = 0; k < 8; k++) { const th = k / 8 * 6.283 + time; addLight(r.x + Math.cos(th) * r.r, r.y + Math.sin(th) * r.r, 36, '255,235,190', 0.6 * a); }
  }
  // her ashes
  if (boss && boss.kind === 'venn' && boss.state === 'dead' && boss.gone) {
    const x = Math.round(boss.x), y = Math.round(boss.floor);
    g.fillStyle = '#6e6a75'; g.fillRect(x - 9, y - 2, 18, 2); g.fillStyle = '#928d98'; g.fillRect(x - 6, y - 3, 12, 1); g.fillRect(x - 3, y - 4, 6, 1);
    g.fillStyle = '#4f4b56'; g.fillRect(x + 10, y - 1, 26, 1); g.fillStyle = '#9c8a74'; g.fillRect(x + 12, y - 2, 20, 1);   // the fallen scythe
  }
  if (VN.flame) { addLight(VN.flame.x, VN.flame.y, 34, '255,245,220', 0.5); if (Math.random() < 0.6) particles.push({ x: VN.flame.x + rand(-2, 2), y: VN.flame.y - 3, vx: rand(-6, 6), vy: -rand(10, 30), life: 0.5, kind: 'mote' }); }
});

HOOKS.renderTop.push(() => {
  // the last flame, drawn over the lighting so it reads as the brightest thing in the dark
  const f = VN.flame; if (!f) return;
  const x = Math.round(f.x - cam.x), y = Math.round(f.y - cam.y), fl = Math.floor(time * 12) % 2;
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = '#1a1418'; g.fillRect(x - 3, y - 3, 7, 6); g.fillRect(x - 2, y - 6 - fl, 5, 4); g.fillRect(x - 1, y - 8 - fl, 3, 3);
  g.fillStyle = '#ffc158'; g.fillRect(x - 2, y - 2, 5, 4);
  g.fillStyle = '#fff5d8'; g.fillRect(x - 1, y - 4 - fl, 3, 6);
  g.fillStyle = '#ffffff'; g.fillRect(x, y - 6 - fl, 1, 6); g.fillRect(x - 1, y - 1, 3, 2);
});

// ---------------------------------------------------------------- the betrayal (first encounter only; Esc skips)
BOSS_CUTS.venn = b => [
  act(() => { b.setS('dormant', 'summon', false); b.anim.speed = 0; b.anim.i = 0; b.face = P.x < b.x ? -1 : 1; }),
  bossPan(b, 40, 1.0),
  say('Sister Venn', 'I lit your shrines. I pulled you out of the ash, again and again. I gave you my flask.'),
  say('Sister Venn', 'I was the Root’s last seed. If you will not give it a heart… then I will be its heart.'),
  act(() => { b.anim.speed = 1; sfx.fire(); shake = 3; }),
  { dur: 1.7, tween: () => { if (Math.random() < 0.8) particles.push({ x: b.x + rand(-8, 8), y: b.y - rand(10, 60), vx: rand(-10, 10), vy: -rand(20, 60), life: rand(0.6, 1.2), kind: Math.random() < 0.6 ? 'mote' : 'fire' }); addLight(b.x, b.y - 40, 60, '255,240,210', 1); } },
  act(() => { flashScreen = 0.7; shake = 8; sfx.kindle(); sfx.roar(); spawnFx(fxOr('vn_burst', 'holy_burst'), b.x, b.y - 50, 1); b.setS('dormant', 'idle'); }),
  say('Sister Venn', 'Forgive me, Ashbound. Or don’t.', { dur: 2.0 }),
  { do() { if (b.tag !== 'idle') b.setS('dormant', 'idle'); b.anim.speed = 1; }, always: true },
];
BOSS_SPAWN.venn = (cx, fy) => new VennBoss(cx, fy);
if (typeof window !== 'undefined' && window.__game) window.__game.vn = { VN, vnBetray, vnFinale, vnOfferEnding: (...a) => vnOfferEnding(...a), VennBoss, vnWindows,
  // test helper: is something about to hit the player within ~0.12 s?
  danger() {
    const b = boss; if (!b || b.kind !== 'venn') return false;
    for (const h of hazards) if (h.vn && ((h.delay > 0 && h.delay < 0.1) || (h.fx && h.fx.anim.i === 2)) && Math.abs(h.x - P.x) < h.w / 2 + 10) return true;
    for (const s of VN.shots) if ((s.x - P.x) * s.dir < 0 && Math.abs(s.x - P.x) < 34) return true;
    for (const r of VN.rings) { const d = Math.hypot(P.x - r.x, P.y - 12 - r.y); if (d - r.r > 0 && d - r.r < 20) return true; }
    if (b.state === 'attack') { const M = VN_MOVES[b.atk], w = vnWindows(M.tag, b.phase); for (const q of w) if (b.anim.i === q.active[0] - 1 && b.anim.t > b.anim.ms() * 0.4) return true;
      if (b.atk === 'blinkcut' && b.anim.i >= 5 && b.anim.i <= 6) return true; }
    return false;
  },
  hold() { if (boss) boss.cool = 99; }, biome: () => room && room.def.biome, amb: () => room && AREAS[room.def.biome].ambient };
