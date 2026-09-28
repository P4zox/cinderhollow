// ------------------------------------------------------------------ boss weapons: each carries its former owner's signature
// Weapon-feel pass (agent WB, docs/WEAPON_FEEL_CONTRACT.md B1): a signature is the boss's power shown through light, particles,
// slash FX and tone -- a flourish, not a second weapon. Its gameplay part is small and bounded:
//   * damage only on the combo finisher or a charged heavy (the staff's spin counts), behind an internal cooldown (>= 2.5 s)
//   * on-hit procs: >= 2 s per target and small numbers, or purely visual
//   * nothing that deals damage reaches past 1.5x the weapon's own melee reach (sigLimit); projectiles are short flourishes
//   * no real sustain, no crowd control on bosses
// Budget: signature damage <= ~8% of the weapon's sustained DPS in tools/shots/wb/bench_real.js. `info` is the one-line
// in-world summary the gear panel shows (WEAPONS[id].sigInfo, set in 60_wbal.js).
const REACH_MUL = 1.12;   // global forward-reach bonus for side attacks
function isFinisher(state) { const ms = moveset(); return state === ms.combo[ms.combo.length - 1] || state === 'attack4'; }
function sigRect(A) {
  const front = A.up || A.down ? A.reach[1] : A.reach[1] * (A.cls ? 1 : D.W.reach) * REACH_MUL;
  return rect(P.x + P.face * A.reach[0], P.y + A.ys[0], P.x + P.face * front, P.y + A.ys[1]);
}
function sigPoint(r) { return { x: P.face > 0 ? Math.max(r.x0 + 10, r.x1 - 14) : Math.min(r.x1 - 10, r.x0 + 14), y: (r.y0 + r.y1) / 2 }; }
const SIG_ROT = { attack1: 0.45, attack2: -0.45, attack3: 0, attack4: 0.2, heavy: 0.55, attack_up: -1.3, attack_down: 1.5, air_attack: 0,
  gs_1: 0.6, gs_2: -0.6, gs_3: 0, gs_heavy: 0.9, sp_1: 0, sp_2: -0.35, sp_3: 0.5, sp_heavy: 0,
  st_1: 0, st_2: -0.8, st_3: 0.2, st_4: 0.9, st_heavy: 0, sh_1: 0.5, sh_2: -0.6, sh_3: 0, sh_heavy: 0, sh_counter: 0,
  tw_1: 0.5, tw_2: 0.5, tw_3: -0.6, tw_4: 0, tw_5: 0.9, tw_heavy: 0.4, counter: -0.6, backstep: -0.3 };
// per-class directional tags (<cls>_up / _air / _down, agent WA) fall back on their ATK flags
function sigRot(A) { const r = SIG_ROT[P.state]; if (r !== undefined) return r; A = A || ATK[P.state] || {}; return A.up ? -1.3 : A.down ? 1.5 : A.air ? 0.25 : 0; }
function sigTrail(A, sg) {
  const r = sigRect(A);
  for (let i = 0; i < 3; i++) particles.push({ x: P.face > 0 ? r.x1 - rand(0, 10) : r.x0 + rand(0, 10), y: rand(r.y0, r.y1), vx: P.face * rand(10, 50), vy: -rand(0, 30), life: rand(0.2, 0.45), kind: Math.random() < 0.75 ? sg.pk : sg.pk2 });
  addLight((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, 46, sg.light, 0.8);
}
function burst(x, y, n, k1, k2, spd = 100) { for (let i = 0; i < n; i++) particles.push({ x: x + rand(-8, 8), y: y + rand(-12, 12), vx: P.face * rand(20, spd), vy: -rand(10, 70), g: 160, life: rand(0.3, 0.7), kind: Math.random() < 0.7 ? k1 : k2 }); }

// ---- the gameplay budget: trigger, cooldown, reach
const SIG_ICD = 2.5;
function sigReach() {   // the weapon's own melee reach in px ahead of the player (its current moveset)
  const ms = moveset(); let r = 30;
  for (const tag of [...ms.combo, ms.heavy]) { const A = ATK[tag]; if (A) r = Math.max(r, A.reach[1] * (A.cls ? 1 : D.W.reach) * REACH_MUL); }
  return r;
}
const sigLimit = () => sigReach() * 1.5;
const sigBig = A => !!A && ATK[P.state] === A && (isFinisher(P.state) && A.kind !== 'heavy' || (A.kind === 'heavy' && (P.charged || A.staffSpin)));   // finisher / charged heavy (the spin); never a plunge
function sigGo(A, key = 'fx', cd = SIG_ICD) {   // may this swing's flourish deal damage? (finisher / charged heavy, off cooldown)
  if (!sigBig(A)) return false;
  P.sigCd = P.sigCd || {}; if ((P.sigCd[key] || 0) > time) return false;
  P.sigCd[key] = time + cd; return true;
}
function sigTargetCd(t, key, cd) { if (!t || t.prop) return false; const k = '_sigT_' + key; if ((t[k] || 0) > time) return false; t[k] = time + cd; return true; }
// clip a damage rect to [ox - L, ox + L]; null when nothing is left
function sigClip(r, ox = P.x, L = sigLimit()) { const x0 = Math.max(r.x0, ox - L), x1 = Math.min(r.x1, ox + L); return x1 > x0 ? rect(x0, r.y0, x1, r.y1) : null; }
function sigStrike(r, dmg, opt = {}) { const c = sigClip(r, opt.ox, opt.L); return c ? wStrike(c, dmg, opt) : []; }
const sigSmallFoe = t => !t.prop && !t.boss && !(t.cfg && t.cfg.elite);
function sigFrontTarget(x, y, range, dirFace = P.face) {
  let best = null, bd = 1e9;
  for (const t of targets()) {
    if (t.prop) continue; const hb = hbOf(t); if (!hb) continue;
    const near = dirFace > 0 ? hb.x0 : hb.x1, dx = (near - x) * dirFace;   // distance to the facing edge of the foe
    if (dx < -((hb.x1 - hb.x0) / 2 + 10) || dx > range || Math.abs((hb.y0 + hb.y1) / 2 - y) > 60) continue;
    if (dx < bd) { bd = dx; best = t; }
  }
  return best;
}
const hbMid = t => { const hb = t.hurtbox(); return { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2 }; };

// ---- shared flourishes (purely visual)
// a crescent of the signature's light swept through the blow
function sigArc(p, col, rot, opt = {}) {
  const face = P.face, R = opt.r || 20, life = opt.life || 0.26, w = opt.w || 3;
  wfx({ life, draw() {
    const k = this.t / life, a = (1 - k) * (opt.alpha ?? 0.9), r = R * (0.85 + 0.35 * k);
    g.save(); g.translate(Math.round(p.x), Math.round(p.y)); g.scale(face, 1); g.rotate(rot);
    g.lineCap = 'round';
    for (const [c, lw, al] of [[col, w + 3, 0.28], [col, w, 0.8], ['#ffffff', 1, 0.9]]) {
      g.globalAlpha = a * al; g.strokeStyle = c; g.lineWidth = lw; g.beginPath(); g.arc(-r * 0.55, 0, r, -1.05 + k * 0.25, 1.05 + k * 0.25); g.stroke();
    }
    g.restore(); addLight(p.x, p.y, R + 18, opt.light || '255,230,190', 0.7 * (1 - k));
  } });
}
// the finisher's colour flourish: an arc, a spray of the boss's motes and a two-note tone
function sigFlourish(A, sg, r, opt = {}) {
  const p = sigPoint(r), heavy = A.kind === 'heavy';
  sigArc(p, sg.glow, sigRot(A), { r: heavy ? 26 : 20, light: sg.light, w: heavy ? 4 : 3 });
  burst(p.x, p.y, heavy ? 16 : 10, sg.pk, sg.pk2, 130);
  if (opt.tone !== false) { tone(opt.f0 || 520, 0.3, 0.04, 'triangle', 0.8); tone((opt.f0 || 520) * 1.5, 0.25, 0.025, 'sine', 0.9, 0.05); }
}
// a sprite flourish that flies a short way and fades (spears, lances, needles): dies at `dist` px, or at the limit
function sigBolt(o) {
  const L = Math.min(o.dist ?? 1e9, o.L ?? sigLimit()) - Math.abs(o.x - P.x);
  return wfx(Object.assign({ skip: new Set(), ox: P.x, x0: o.x, life: 1, update(dt) {
    this.x += this.vx * dt; this.y += this.vy * dt;
    const gone = Math.abs(this.x - this.x0);
    if (gone >= L || solidAtPx(this.x, this.y)) { this.onEnd && this.onEnd(); return false; }
    this.k = gone / Math.max(1, L);
    if (this.dmg > 0) for (const t of sigStrike(rect(this.x - 6, this.y - 4, this.x + 6, this.y + 4), this.dmg, { skip: this.skip, poise: this.poise || 10, dir: Math.sign(this.vx) || 1, kind: 'spell', ox: this.ox, L: this.Lmax })) this.onHit && this.onHit(t);
    if (this.trail && Math.random() < 0.7) particles.push({ x: this.x - Math.sign(this.vx) * 6, y: this.y + rand(-1, 1), vx: -this.vx * 0.1, vy: rand(-10, 10), life: 0.25, kind: this.trail });
  }, draw() {
    const a = Math.max(0, 1 - Math.max(0, (this.k || 0) - 0.45) / 0.55) * (this.alpha ?? 1), f = Math.sign(this.vx) || 1;
    if (this.fx) { const s = fxSheet(this.fx); if (s.ok) { const tg = s.tag(Object.keys(s.tags)[0]); drawRotated(s, tg.from + Math.floor(this.t * 14) % (tg.to - tg.from + 1), this.x, this.y, Math.atan2(this.vy, this.vx), a); } }
    else if (!wfxDraw(this.sheet, this.t, this.x, this.y, f, { center: true, loop: true, alpha: a, rot: Math.atan2(this.vy, Math.abs(this.vx)) * f })) { g.globalAlpha = a; g.fillStyle = this.col || '#fff'; g.fillRect(this.x - 4, this.y - 1, 8, 2); g.globalAlpha = 1; }
    addLight(this.x, this.y, 26, this.light || '255,255,255', 0.6 * a);
  } }, o, { Lmax: o.L ?? sigLimit() }));
}
function sigFloorX(x) { const fy = wFloorBelow(x, P.y - 6); return fy !== null && Math.abs(fy - P.y) <= 24 && !solidAtPx(x, fy - 8) ? fy : null; }

// ================================================================== the signatures
const SIGS = {
  kalden: { glow: '#7ff0d0', light: '120,230,200', pk: 'teal', pk2: 'gold', replaceFx: true,
    info: 'Moonlit teal slashes that ring like a struck bell. No extra effect.',
    swing(A, r) {
      const p = sigPoint(r), heavy = A.kind === 'heavy', rot = sigRot(A);
      spawnFx(fxOr('kalden_slash', 'slash3'), p.x, p.y, P.face, null, { rot, speed: heavy ? 0.8 : 1.15, alpha: 0.95 });
      if (heavy || isFinisher(P.state)) { spawnFx(fxOr('kalden_slash', 'slash3'), p.x + P.face * 8, p.y, P.face, null, { rot: rot * 0.5, speed: 0.7, alpha: 0.55 }); shake = Math.max(shake, heavy ? 4 : 2); }
      tone(heavy ? 330 : 440, 0.35, 0.05, 'triangle', 0.55); tone(heavy ? 660 : 880, 0.25, 0.03, 'sine', 0.7);
      burst(p.x, p.y, heavy ? 18 : 9, 'teal', 'gold');
    },
    finisher(A, r) { if (sigBig(A)) sigArc(sigPoint(r), '#7ff0d0', sigRot(A), { r: 28, life: 0.34, light: '120,230,200' }); } },
  gravetusk: { glow: '#ffd27a', light: '255,200,110', pk: 'root', pk2: 'gold',
    info: 'Finisher or charged heavy: golden roots split the ground where the blow lands · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 10, 'root', 'gold'); tone(150, 0.3, 0.06, 'sawtooth', 0.6); },
    finisher(A, r) {
      if (!sigBig(A) && A.kind !== 'heavy') return;
      const go = sigGo(A), skip = new Set(), L = sigLimit(), n = A.kind === 'heavy' ? 4 : 3;
      sfx.crumble(); shake = Math.max(shake, 3); if (sigBig(A)) sigFlourish(A, this, r, { f0: 196 });
      for (let k = 0; k < n; k++) {
        const x = P.x + P.face * Math.min(L - 4, 22 + k * 14), fy = sigFloorX(x); if (fy === null) break;
        const at = 0.06 + k * 0.07;
        wfx({ life: at + 0.5, x, fy, done: false, update() {
          if (this.t < at || this.done) return; this.done = true;
          spawnFx(fxOr('root_spike', 'hit'), this.x, this.fy, P.face, null, { bottom: true });
          for (let i = 0; i < 6; i++) particles.push({ x: this.x + rand(-5, 5), y: this.fy - 2, vx: rand(-40, 40), vy: -rand(40, 120), g: 380, life: 0.5, kind: i % 2 ? 'gold' : 'root' });
          if (go) sigStrike(rect(this.x - 8, this.fy - 30, this.x + 8, this.fy + 1), D.light * 0.3, { skip, poise: 20 });
        }, draw() { if (this.t >= at) addLight(this.x, this.fy - 12, 28, '255,200,110', 0.7 * Math.max(0, 1 - (this.t - at) / 0.5)); } });
      }
    } },
  omen: { glow: '#ffcf6a', light: '255,210,120', pk: 'gold', pk2: 'ember', replaceFx: true,
    info: 'Golden arcs on every blow. Finisher or charged heavy: a fan of light spears that fades a tile past the blade · every 2.5 s',
    swing(A, r) {
      const p = sigPoint(r), heavy = A.kind === 'heavy', rot = sigRot(A);
      spawnFx(fxOr('boss_slash', 'slash3'), p.x, p.y, P.face, null, { rot, speed: heavy ? 0.85 : 1.2, alpha: 0.95 });
      burst(p.x, p.y, heavy ? 16 : 8, 'gold', 'ember'); tone(heavy ? 392 : 523, 0.3, 0.05, 'triangle', 0.6);
    },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A), p = sigPoint(r), n = A.kind === 'heavy' ? 5 : 3;
      for (let k = 0; k < n; k++) {
        const off = k - (n - 1) / 2;
        sigBolt({ x: P.x + P.face * 14, y: p.y - 2 + off * 6, vx: P.face * 360, vy: off * 45, dist: Math.abs(p.x - P.x) + 18, fx: 'light_spear', trail: 'gold', light: '255,220,140',
          dmg: go && off === 0 ? D.light * 0.3 : 0, poise: 12 });
      }
      sfx.spear(); flashScreen = Math.max(flashScreen, 0.06); sigFlourish(A, this, r, { f0: 587 });
    } },
  rotmaw: { glow: '#9ae05a', light: '150,210,90', pk: 'spore', pk2: 'ember',
    info: 'Charged heavy: a brief pool of rot where the blow lands · every 3 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 10, 'spore', 'ember'); if (A.kind === 'heavy' || isFinisher(P.state)) spawnFx(fxOr('rot_hit', 'hit'), p.x, p.y, P.face); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      sigFlourish(A, this, r, { f0: 147 });
      if (A.kind !== 'heavy' || !sigGo(A, 'fx', 3)) return;
      const x = P.x + P.face * Math.min(30, sigLimit() - 20);
      projectiles.push({ owner: 'player', kind: 'mist', x, y: P.y, vx: 0, vy: 0, dmg: D.heavy * 0.05, life: 1.6, r: 18, pierce: true, tick: 0.5, static: true, t: 0, hits: new Set(), face: P.face, sh: 'fx_rotmist' });
      sfx.fire();
    } },
  scepter: { glow: '#fff2c8', light: '255,245,220', pk: 'petal', pk2: 'gold',
    info: 'Finisher: a short lance of pale light. Charged heavy: a pillar falls just ahead · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'petal', 'gold'); tone(988, 0.25, 0.04, 'sine', 1.3); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A), p = sigPoint(r); sigFlourish(A, this, r, { f0: 659 });
      if (A.kind === 'heavy') {
        const x = P.x + P.face * Math.min(56, sigLimit() - 12), fy = sigFloorX(x);
        spawnFx(fxOr('holy_burst', 'parry_flash'), P.x + P.face * 30, P.y - 18, P.face, null, { alpha: 0.8 });
        if (fy !== null) {
          const skip = new Set(); sfx.pillar();
          wfx({ life: 0.7, x, fy, done: false, update() {
            if (this.t < 0.12 || this.done) return; this.done = true; shake = Math.max(shake, 4); flashScreen = Math.max(flashScreen, 0.06);
            spawnFx(fxOr('lightpillar', 'holy_burst'), this.x, this.fy, P.face, null, { bottom: true });
            if (go) sigStrike(rect(this.x - 10, this.fy - 80, this.x + 10, this.fy + 1), D.heavy * 0.35, { skip, poise: 30, big: true });
          }, draw() { const k = Math.min(1, this.t / 0.12); addLight(this.x, this.fy - 30, 50, '255,240,200', 0.8 * k * Math.max(0, 1 - (this.t - 0.12) / 0.58)); } });
        }
      } else {
        sigBolt({ x: P.x + P.face * 18, y: p.y, vx: P.face * 380, vy: 0, dist: Math.abs(p.x - P.x) + 20, fx: 'sov_lance', trail: 'petal', light: '255,245,220', dmg: go ? D.light * 0.3 : 0, poise: 14 });
        sfx.spear();
      }
    } },
  // ---- v8 expansion boss weapons (helpers wfx / wStrike / wZap / wAddFrost / wAddBurn live in 13_weapons.js)
  inkquill: { glow: '#b890ff', light: '170,120,240', pk: 'ink', pk2: 'gold',
    info: 'A wound it opens is signed with a glyph that bursts a moment later (once per foe every 2.5 s). The spin flings a little ink.',
    swing(A, r) {
      const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 14 : 7, 'ink', 'gold');
      tone(A.kind === 'heavy' ? 311 : 523, 0.25, 0.04, 'sine', 0.6);
      if (A.staffSpin) { sigInkBlots(sigGo(A)); sigFlourish(A, this, r, { f0: 311 }); }
    },
    hit(t, info) { sigInkGlyph(t, info); } },
  twinborne: { get glow() { return P && P.sigCharge > 0 ? '#ff9a40' : '#a8dcff'; }, get light() { return P && P.sigCharge > 0 ? '255,160,70' : '170,220,255'; },
    get pk() { return P && P.sigCharge > 0 ? 'ember' : 'frost'; }, pk2: 'frost',
    info: 'Blocking stokes the blade (up to 3): the next blow bursts into flame for a little more. Blocks chill lesser attackers.',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, P.sigCharge > 0 ? 'fire' : 'frost', 'frost'); },
    hit(t, info) {   // a stoked blade: the next blow bursts into flame
      if (!(P.sigCharge > 0) || t.prop) return;
      P.sigCharge--;
      t.hit({ dmg: D.light * 0.3, poise: 12, dir: info.dir, kind: 'spell', x: info.x, y: info.y, big: true, fire: true, sig: true });
      spawnFx(fxOr('cinderblade', 'hit'), info.x, info.y, P.face); sfx.fire();
      sigArc({ x: info.x, y: info.y }, '#ff9a40', rand(-0.6, 0.6), { r: 16, light: '255,160,70' });
      for (let i = 0; i < 14; i++) particles.push({ x: info.x, y: info.y, vx: rand(-70, 70), vy: -rand(30, 120), g: 120, life: rand(0.3, 0.7), kind: 'fire' });
    },
    block(src) {   // blocking chills the attacker and stokes the blade
      P.sigCharge = Math.min(3, (P.sigCharge || 0) + 1);
      tone(1320, 0.2, 0.05, 'triangle', 0.7); tone(220, 0.3, 0.05, 'sawtooth', 1.4);
      for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * 14, y: P.y - rand(10, 26), vx: P.face * rand(30, 140), vy: rand(-40, 20), life: rand(0.3, 0.6), kind: 'frost' });
      if (src && !src.prop && !src.boss && typeof src.hit === 'function' && src.hurtbox && src.hurtbox()) wAddFrost(src, 24);
    } },
  colossus_hammer: { glow: '#ff9a40', light: '255,150,60', pk: 'ember', pk2: 'fire',
    info: 'Heavies crack the ground with glowing seams. A fully charged heavy makes them burn and erupt · every 3 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 16 : 8, 'ember', 'fire'); tone(90, 0.3, 0.06, 'sawtooth', 0.6); },
    finisher(A, r) { if (A.kind !== 'heavy') return; const hot = !!P.charged && sigGo(A, 'fx', 3); sigLavaCrack(hot); if (sigBig(A)) sigFlourish(A, this, r, { f0: 110 }); } },
  stormfang: { glow: '#9fd0ff', light: '150,200,255', pk: 'frost', pk2: 'spark',
    info: 'Finisher: lightning arcs into the foe before you. Charged heavy: a bolt falls on it · every 2.5 s, melee range only',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'frost', 'spark'); noise(0.08, 4000, 2, 0.08, 'highpass'); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A); sigFlourish(A, this, r, { f0: 880, tone: false });
      if (A.kind === 'heavy') sigSkyBolt(go); else sigChain(sigPoint(r), go);
    },
    dive(t, info) { wZap(info.x - P.face * 20, info.y - 6, info.x, info.y, 0.14); noise(0.1, 3500, 2, 0.1, 'highpass'); } },
  windstaff: { glow: '#c8fff4', light: '200,250,240', pk: 'mote', pk2: 'dust',
    info: 'Every blow sends a puff of wind. Finisher: a gust that buffets. The spin looses a short whirlwind · every 2.5 s',
    swing(A, r) {
      const p = sigPoint(r); burst(p.x, p.y, 6, 'mote', 'dust');
      if (A.staffSpin) { sigWhirlwind(sigGo(A)); sigFlourish(A, this, r, { f0: 262 }); }
      else if (A.kind === 'light') { const big = isFinisher(P.state); sigGust(p, big && sigGo(A)); if (big) sigFlourish(A, this, r, { f0: 330, tone: false }); }
    } },
  first_ember: { glow: '#ffb050', light: '255,180,90', pk: 'ember', pk2: 'gold',
    get info() { return `Mirrors your ${wbClassLabel(wcls())} (the last weapon you fought with). Every blow leaves a golden echo; a finisher's echo strikes again for 15% · once per foe every 2.5 s`; },
    swing(A, r) { sigEmberEcho(A, r); },
    hit(t, info, A) {   // the echo: always seen, only a finisher's lands
      if (t.prop) return;
      const lands = !!A && isFinisher(P.state) && sigTargetCd(t, 'echo', SIG_ICD);
      wfx({ life: 0.36, update() {
        if (this.t < 0.3 || this.done) return; this.done = true;
        if (t.alive === false) return;
        if (lands) t.hit({ dmg: info.dmg * 0.15, poise: (info.poise || 0) * 0.2, dir: info.dir, kind: 'light', x: info.x, y: info.y, fire: true, sig: true });
        spawnFx(fxOr('embers', 'hit'), info.x, info.y, info.dir, null, lands ? {} : { alpha: 0.6 }); tone(lands ? 740 : 988, 0.2, lands ? 0.04 : 0.02, 'triangle', 0.8);
        for (let i = 0; i < (lands ? 10 : 5); i++) particles.push({ x: info.x, y: info.y, vx: rand(-60, 60), vy: -rand(20, 90), g: 100, life: rand(0.3, 0.6), kind: 'ember' });
      } });
    } },
  // ---- v9 (Expansion 2) boss weapons
  antler_scythe: { glow: '#9fe8a0', light: '140,230,150', pk: 'spore', pk2: 'root',
    info: 'Finisher or charged heavy: thorns wake along the sweep · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 14 : 7, 'spore', 'root'); },
    finisher(A, r) { if (!sigBig(A)) return; sig9Thorns(A.kind === 'heavy' ? 4 : 3, sigGo(A) ? 0.3 : 0); sigFlourish(A, this, r, { f0: 247 }); } },
  choir_harpoon: { glow: '#7ff0e0', light: '100,230,210', pk: 'teal', pk2: 'frost',
    info: 'Finisher or charged heavy: a lance of black water leaps off the tip and drags lesser foes in · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'teal', 'frost'); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A), p = sigPoint(r); sigFlourish(A, this, r, { f0: 220, tone: false });
      if (A.kind === 'heavy') for (const vy of [-50, 0, 50]) sig9WaterLance(p, vy, go && vy === 0 ? 0.3 : 0); else sig9WaterLance(p, 0, go ? 0.3 : 0);
    },
    dive(t, info) { burst(info.x, info.y, 10, 'teal', 'frost'); noise(0.2, 1200, 0.8, 0.1, 'bandpass', 0.6); } },
  sanguine_rapier: { glow: '#ff5060', light: '240,60,80', pk: 'blood', pk2: 'fire',
    info: 'Finisher or charged heavy: a needle of blood. A critical blow drinks a sip (3% HP) · every 6 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 6, 'blood', 'blood'); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A), p = sigPoint(r); sigFlourish(A, this, r, { f0: 440, tone: false });
      sig9BloodLance(p, 0, go); if (A.kind === 'heavy') { sig9BloodLance(p, -40, false); sig9BloodLance(p, 40, false); }
    },
    crit(t, dmg) {   // every critical blow drinks -- a sip, not a meal
      const drink = (P.sigDrinkT || 0) <= time;
      for (let i = 0; i < 16; i++) particles.push({ x: t.x + rand(-8, 8), y: t.y - rand(6, 26), vx: (P.x - t.x) * rand(2, 3), vy: -rand(0, 30), life: 0.45, kind: 'blood' });
      if (!drink) return;
      P.sigDrinkT = time + 6;
      const h = Math.round(D.maxHp * 0.03);
      P.hp = Math.min(D.maxHp, P.hp + h); popup(P.x, P.y - 34, h, '#ff6a7a'); sfx.bleed();
    } },
  vael_greatsword: { glow: '#a8dcff', light: '150,200,255', pk: 'frost', pk2: 'teal',
    info: 'Wounds flicker with ghost-fire. Charged heavy: spectral chains rise and bind the foe before you (lesser foes are slowed) · every 3 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 16 : 8, 'frost', 'teal'); tone(A.kind === 'heavy' ? 180 : 260, 0.35, 0.04, 'sine', 0.6); },
    hit(t, info) { if (!t.prop) sigGhostFire(t); },   // ghost-fire in the wound: seen, not felt
    finisher(A, r) { if (!sigBig(A)) return; sigFlourish(A, this, r, { f0: 165, tone: false }); if (A.kind === 'heavy') sig9Chains(sigGo(A, 'fx', 3)); } },
  pharaoh_khopesh: { glow: '#ffd070', light: '255,210,120', pk: 'gold', pk2: 'dust',
    info: 'Finisher: a disc of sunlight flung out and back. Charged heavy: a burst of scouring sand · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'gold', 'dust'); if (A.kind === 'heavy') sig9Sand(false, true); },
    finisher(A, r) { if (!sigBig(A)) return; const go = sigGo(A); sigFlourish(A, this, r, { f0: 494 }); if (A.kind === 'heavy') sig9Sand(go); else sig9SunDisc(sigPoint(r), go); } },
  starblade: { glow: '#c8d8ff', light: '190,210,255', pk: 'mote', pk2: 'frost',
    info: 'Finisher or charged heavy: shards of the sky fall on what stands within reach · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'mote', 'frost'); tone(1480, 0.2, 0.03, 'sine', 1.3); },
    finisher(A, r) { if (!sigBig(A)) return; sig9Stars(A.kind === 'heavy' ? 5 : 3, sigGo(A)); sigFlourish(A, this, r, { f0: 1175, tone: false }); } },
  saint_lance: { glow: '#70fff8', light: '120,255,250', pk: 'teal', pk2: 'spark',
    info: 'Wounds glitch (a flicker, and once per foe every 2.5 s a small echo). Finisher or charged heavy: a neon line cut through the air ahead · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 6, 'teal', 'spark'); tone(1760, 0.08, 0.04, 'square', 0.5); },
    finisher(A, r) { if (!sigBig(A)) return; sig9Laser(sigPoint(r), A.kind === 'heavy', sigGo(A)); sigFlourish(A, this, r, { f0: 1319, tone: false }); },
    hit(t, info) { sig9Glitch(t, info); },
    dive(t, info) { sig9Laser({ x: info.x - P.face * 24, y: info.y }, false, false); } },
  last_kindling: { glow: '#fff4d0', light: '255,244,210', pk: 'mote', pk2: 'gold',
    info: 'Wounds flare with pale fire. Finisher or charged heavy: a pyre rises where the foe stands and burns a moment · every 2.5 s',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'mote', 'gold'); },
    hit(t, info) { if (!t.prop && sigTargetCd(t, 'flare', 0.8)) sigPaleFlare(info.x, info.y); },
    finisher(A, r) {
      if (!sigBig(A)) return;
      const go = sigGo(A), t = sigFrontTarget(P.x, P.y - 16, sigReach()), L = sigLimit();
      sigFlourish(A, this, r, { f0: 523, tone: false });
      const x = t ? clamp(hbMid(t).x, P.x - L + 10, P.x + L - 10) : P.x + P.face * Math.min(34, L - 10);
      sig9Pyre(x, P.y, go);
      if (A.kind === 'heavy') sig9Pyre(P.x + P.face * 10, P.y, false);
    } },
};
// ---- v9 signature helpers (entities live in 13_weapons.js's WFX list)
const sig9Pyres = [];
function sig9Thorns(n, mult) {   // thorns erupt along the sweep, one after another; one shared cut per foe
  sfx.crumble();
  const skip = new Set(), L = sigLimit();
  for (let k = 0; k < n; k++) {
    const x = P.x + P.face * Math.min(L - 6, 22 + k * 14), fy = sigFloorX(x);
    if (fy === null) break;
    wfx({ life: 0.55 + k * 0.07, x, fy, at: k * 0.07, face: P.face, done: false,
      update() {
        if (this.t >= this.at + 0.05 && !this.done) { this.done = true; if (mult > 0) sigStrike(rect(this.x - 7, this.fy - 26, this.x + 7, this.fy + 1), D.light * mult, { poise: 16, skip, dir: this.face });
          for (let i = 0; i < 5; i++) particles.push({ x: this.x + rand(-5, 5), y: this.fy - 2, vx: rand(-40, 40), vy: -rand(40, 110), g: 380, life: 0.5, kind: i % 2 ? 'spore' : 'root' }); }
      },
      draw() { if (this.t >= this.at) { if (!wfxDraw('thorn', this.t - this.at, this.x, this.fy + 1, this.face)) { g.fillStyle = '#6a8a40'; g.fillRect(this.x - 1, this.fy - 18, 3, 18); } addLight(this.x, this.fy - 10, 22, '140,230,150', 0.5); } } });
  }
}
function sig9WaterLance(p, vy, mult) {
  sfx.spear(); noise(0.2, 1200, 0.8, 0.12, 'bandpass', 0.6);
  sigBolt({ x: p.x, y: p.y, vx: P.face * 300, vy, dist: Math.abs(p.x - P.x) + 26, sheet: 'waterlance', trail: 'teal', light: '100,230,210', col: '#70e8d8', dmg: D.light * mult, poise: 12,
    onHit(t) { if (sigSmallFoe(t) && t.vx !== undefined) { t.vx = -P.face * 120; weaponPull(t, { chain: false }); } } });   // the tide drags lesser foes in
}
function sig9BloodLance(p, vy, go) {
  sigBolt({ x: p.x, y: p.y, vx: P.face * 360, vy, dist: Math.abs(p.x - P.x) + 20, sheet: 'bloodlance', trail: 'blood', light: '240,60,80', col: '#e02040', dmg: go ? D.light * 0.2 : 0, poise: 8,
    onHit(t) { if (t.hit && !t.prop) t.hit({ dmg: 0, poise: 0, dir: P.face, kind: 'spell', x: t.x, y: t.y - 14, bleed: 8, quiet: true }); } });
  tone(880, 0.15, 0.04, 'sawtooth', 0.5);
}
function sigGhostFire(t) {   // a pale-blue flicker in the wound (no damage)
  if (!sigTargetCd(t, 'ghost', 0.5)) return;
  const hb = t.hurtbox && t.hurtbox(); if (!hb) return;
  wfx({ life: 1.2, draw() {
    const h2 = t.hurtbox && t.hurtbox(); if (!h2) return;
    const a = Math.max(0, 1 - this.t / 1.2);
    if (Math.random() < 0.5) particles.push({ x: rand(h2.x0 + 4, h2.x1 - 4), y: rand(h2.y0 + 6, h2.y1 - 4), vx: rand(-6, 6), vy: -rand(15, 40), life: 0.4, kind: Math.random() < 0.6 ? 'frost' : 'teal' });
    addLight((h2.x0 + h2.x1) / 2, (h2.y0 + h2.y1) / 2, 30, '150,200,255', 0.5 * a);
  } });
}
function sigPaleFlare(x, y) {   // a small pale flame licks up from the wound (no damage)
  tone(620, 0.2, 0.02, 'sine', 1.4);
  wfx({ life: 0.5, x, y, draw() { const a = 1 - this.t / 0.5; wfxDraw('pyre', this.t, this.x, this.y + 8, 1, { alpha: 0.55 * a }); addLight(this.x, this.y, 24, '255,244,210', 0.5 * a); } });
  for (let i = 0; i < 5; i++) particles.push({ x: x + rand(-4, 4), y: y + rand(-6, 6), vx: rand(-10, 10), vy: -rand(20, 50), life: 0.4, kind: 'mote' });
}
function sig9Chains(go) {   // spectral chains burst from the ground and bind the nearest foe within reach
  const L = sigLimit(), t = sigFrontTarget(P.x, P.y - 16, L - 10);
  tone(120, 0.6, 0.08, 'sawtooth', 1.4); noise(0.4, 2400, 1, 0.15, 'highpass');
  if (!t) {   // nothing in reach: the chains lash the air where the blow lands
    const x = P.x + P.face * Math.min(40, L - 10), fy = sigFloorX(x) ?? P.y;
    wfx({ life: 0.5, draw() { const a = 1 - this.t / 0.5; g.globalAlpha = a; for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? '#8fc8ff' : '#dff0ff'; g.fillRect(Math.round(x + (i - 4) * 3), Math.round(fy - 4 - i * 3 * Math.min(1, this.t * 6)), 2, 2); } g.globalAlpha = 1; addLight(x, fy - 12, 28, '150,200,255', 0.6 * a); } });
    return;
  }
  const hb = t.hurtbox(); if (!hb) return;
  const fy = wFloorBelow((hb.x0 + hb.x1) / 2, hb.y1 - 4) ?? hb.y1;
  wfx({ life: 1.4, anchors: [(hb.x0 + hb.x1) / 2 - 22, (hb.x0 + hb.x1) / 2 + 22], fy, bound: false,
    update() {
      if (!this.bound && this.t > 0.25) {
        this.bound = true;
        if (t.alive !== false && t.hit) {
          if (go) t.hit({ dmg: D.heavy * 0.35, poise: 30, dir: P.face, kind: 'spell', x: t.x, y: t.y - 16, big: true, sig: true });
          if (sigSmallFoe(t)) { t._slowT = 1.0; wSlowWrap(t); }   // lesser foes only: kings are not bound
        }
      }
      if (t.alive === false) return false;
    },
    draw() {
      const h2 = t.hurtbox && t.hurtbox(); if (!h2) return;
      const k = Math.min(1, this.t / 0.25), cy = (h2.y0 + h2.y1) / 2, cx = (h2.x0 + h2.x1) / 2, a = Math.max(0, 1 - Math.max(0, this.t - 1.0) / 0.4);
      g.save(); g.globalAlpha = a;
      for (const ax of this.anchors) {   // chain links from the grave to the foe
        const ex = ax + (cx - ax) * k, ey = this.fy + (cy - this.fy) * k, n = Math.max(3, Math.round(Math.hypot(ex - ax, ey - this.fy) / 4));
        for (let i = 0; i <= n; i++) { const x = ax + (ex - ax) * i / n, y = this.fy + (ey - this.fy) * i / n; g.fillStyle = i % 2 ? '#8fc8ff' : '#dff0ff'; g.fillRect(Math.round(x) - (i % 2), Math.round(y) - 1, 2 + (i % 2), 2); }
      }
      g.restore(); addLight(cx, cy, 34, '150,200,255', 0.6 * a);
    } });
}
function sig9SunDisc(p, go) {   // a disc of sunlight flung out to the end of reach, then back to the hand
  sfx.heavySwing(); tone(660, 0.3, 0.04, 'triangle', 1.2);
  const L = sigLimit(), ox = P.x, skip = new Set();
  wfx({ life: 1.2, x: p.x, y: p.y, dir: P.face, back: false,
    update(dt) {
      if (!this.back) { this.x += this.dir * 300 * dt; if (Math.abs(this.x - ox) >= L - 8 || solidAtPx(this.x + this.dir * 6, this.y)) this.back = true; }
      else { const dx = P.x - this.x, dy = P.y - 18 - this.y, d = Math.hypot(dx, dy) || 1; this.x += dx / d * 320 * dt; this.y += dy / d * 320 * dt; if (d < 10) return false; }
      if (go) sigStrike(rect(this.x - 7, this.y - 7, this.x + 7, this.y + 7), D.light * 0.25, { skip, poise: 10, fire: true, kind: 'spell', ox, L });
      if (Math.random() < 0.5) particles.push({ x: this.x, y: this.y, vx: rand(-20, 20), vy: rand(-20, 20), life: 0.3, kind: 'gold' });
    },
    draw() { if (!wfxDraw('sundisc', this.t, this.x, this.y, 1, { center: true, loop: true })) { g.fillStyle = '#ffd070'; g.fillRect(this.x - 4, this.y - 4, 8, 8); } addLight(this.x, this.y, 34, '255,210,120', 0.8); } });
}
function sig9Sand(go, soft) {   // the heavy raises a burst of scouring sand around you
  if (!soft) { sfx.crumble(); shake = Math.max(shake, 4); spawnFx('shockwave', P.x, P.y, 1); }
  if (go) sigStrike(rect(P.x - 40, P.y - 30, P.x + 40, P.y + 2), D.heavy * 0.25, { poise: 20, kind: 'spell' });
  for (let i = 0; i < (soft ? 12 : 40); i++) { const a = rand(0, Math.PI); particles.push({ x: P.x + Math.cos(a) * rand(4, 20), y: P.y - rand(0, 8), vx: Math.cos(a) * rand(60, 160) * (Math.random() < 0.5 ? 1 : -1), vy: -rand(20, 110), g: 260, life: rand(0.4, 0.9), kind: 'dust' }); }
}
function sig9Stars(n, go) {   // star shards fall on what stands within reach; only the first to strike a foe hurts it
  const L = sigLimit(), xs = [], skip = new Set();
  for (const t of targets()) { if (t.prop) continue; const hb = t.hurtbox(); if (!hb) continue; const near = P.face > 0 ? hb.x0 : hb.x1; if ((near - P.x) * P.face > -10 && Math.abs(near - P.x) < L - 8) xs.push(clamp((hb.x0 + hb.x1) / 2, P.x - L + 12, P.x + L - 12)); }
  for (let k = 0; k < n; k++) {
    const x = xs.length ? xs[k % xs.length] + rand(-10, 10) : P.x + P.face * Math.min(L - 10, 26 + k * 14);
    const fy = wFloorBelow(x, P.y - 8) ?? P.y;
    wfx({ life: 1.2, x: x + P.face * 30, y: fy - 110, tx: x, fy, at: k * 0.1, hit: false,
      update(dt) {
        if (this.t < this.at || this.hit) return this.hit ? this.t < this.hitT + 0.3 : undefined;
        const k2 = Math.min(1, (this.t - this.at) / 0.28); this.cx = this.x + (this.tx - this.x) * k2; this.cy = this.y + (this.fy - this.y) * k2;
        if (Math.random() < 0.8) particles.push({ x: this.cx, y: this.cy, vx: rand(-10, 10), vy: -rand(0, 20), life: 0.3, kind: 'mote' });
        if (k2 >= 1) { this.hit = true; this.hitT = this.t; if (go) sigStrike(rect(this.tx - 10, this.fy - 24, this.tx + 10, this.fy + 1), D.light * 0.3, { skip, poise: 14, kind: 'spell' }); shake = Math.max(shake, 2); tone(1320, 0.3, 0.05, 'triangle', 0.5); for (let i = 0; i < 10; i++) particles.push({ x: this.tx, y: this.fy - 2, vx: rand(-80, 80), vy: -rand(30, 120), g: 300, life: 0.5, kind: i % 2 ? 'mote' : 'frost' }); }
      },
      draw() {
        if (this.t < this.at) return;
        if (!this.hit) { const a = Math.atan2(this.fy - this.y, this.tx - this.x) - Math.PI / 2; if (!wfxDraw('starshard', this.t, this.cx ?? this.x, this.cy ?? this.y, 1, { center: true, loop: true, rot: a })) { g.fillStyle = '#e8f0ff'; g.fillRect(this.cx - 1, this.cy - 3, 3, 6); } addLight(this.cx ?? this.x, this.cy ?? this.y, 30, '200,220,255', 0.8); }
        else { addLight(this.tx, this.fy - 8, 40, '200,220,255', Math.max(0, 1 - (this.t - this.hitT) / 0.3)); }
      } });
  }
}
function sig9Laser(p, wide, go) {   // a neon line drawn through the air -- cut off at the end of reach
  const dir = P.face, L = sigLimit(); let x1 = p.x;
  for (let k = 0; Math.abs(p.x + dir * k - P.x) <= L; k += 4) { if (solidAtPx(p.x + dir * k, p.y)) break; x1 = p.x + dir * k; }
  const hw = wide ? 5 : 3;
  if (go) sigStrike(rect(Math.min(p.x, x1), p.y - hw - 2, Math.max(p.x, x1), p.y + hw + 2), D.light * 0.2, { poise: 12, kind: 'spell', dir });
  tone(2200, 0.15, 0.05, 'square', 0.4); tone(440, 0.25, 0.05, 'sawtooth', 2); flashScreen = Math.max(flashScreen, 0.05);
  wfx({ life: 0.3, x0: p.x, x1, y: p.y, hw, draw() {
    const a = 1 - this.t / this.life, jit = Math.floor(this.t * 60) % 3 - 1, lo = Math.min(this.x0, this.x1), w = Math.abs(this.x1 - this.x0);
    g.save(); g.globalAlpha = a;
    g.fillStyle = 'rgba(255,70,200,0.8)'; g.fillRect(Math.round(lo), Math.round(this.y - this.hw + jit), Math.round(w), this.hw * 2);
    g.fillStyle = '#78fff8'; g.fillRect(Math.round(lo), Math.round(this.y - 1), Math.round(w), 2);
    g.fillStyle = '#ffffff'; g.fillRect(Math.round(lo), Math.round(this.y), Math.round(w), 1);
    for (let i = 0; i < 4; i++) { g.fillStyle = i % 2 ? '#ff46c8' : '#78fff8'; g.fillRect(Math.round(lo + rand(0, w)), Math.round(this.y + rand(-8, 8)), Math.round(rand(4, 14)), 1); }   // glitch slivers
    g.globalAlpha = a * 0.8; g.fillStyle = '#ffffff'; g.fillRect(Math.round(dir > 0 ? lo + w : lo) - 1, Math.round(this.y - 3), 2, 6);   // the line's burning end
    g.restore(); addLight(lo + w / 2, this.y, w / 2 + 20, '120,255,250', 0.7 * a);
  } });
}
function sig9Glitch(t, info) {   // the wound glitches: always seen; once per foe every 2.5 s a small corrupted echo lands
  if (t.prop || (t._glitchT || 0) > time) return;
  t._glitchT = time + 0.2;
  const lands = sigTargetCd(t, 'glitch', SIG_ICD);
  wfx({ life: 0.4, done: false, update() {
    if (this.t >= 0.22 && !this.done) { this.done = true; if (lands && t.alive !== false) t.hit({ dmg: info.dmg * 0.08, poise: 4, dir: info.dir, kind: 'spell', x: info.x, y: info.y, quiet: true, sig: true }); tone(1200 + rand(0, 800), 0.06, 0.04, 'square', 0.3); }
  }, draw() {
    const hb = t.hurtbox && t.hurtbox(); if (!hb) return;
    for (let i = 0; i < 3; i++) { g.fillStyle = (Math.floor(this.t * 40) + i) % 2 ? 'rgba(120,255,250,0.8)' : 'rgba(255,70,200,0.8)'; g.fillRect(Math.round(hb.x0 + rand(-6, 6)), Math.round(rand(hb.y0, hb.y1)), Math.round(hb.x1 - hb.x0), 1); }
  } });
}
function sig9Pyre(x, y, go) {   // a pyre of pale flame where the foe stood: three small licks of fire when it counts
  const fy = wFloorBelow(x, y - 6); if (fy === null || solidAtPx(x, fy - 8)) return;
  while (sig9Pyres.length && (sig9Pyres[0].dead || sig9Pyres.length >= 4)) { const o = sig9Pyres.shift(); o.life = Math.min(o.life, o.t + 0.2); }
  const ox = P.x, L = sigLimit();
  const e = wfx({ life: 1.3, x, fy, tick: 0.1, n: 0,
    update(dt) {
      if (go && this.n < 3 && (this.tick -= dt) <= 0) { this.tick = 0.35; this.n++; sigStrike(rect(this.x - 9, this.fy - 30, this.x + 9, this.fy + 1), D.light * 0.08, { quiet: true, kind: 'spell', fire: true, ox, L }); }
      if (Math.random() < 0.3) particles.push({ x: this.x + rand(-5, 5), y: this.fy - rand(4, 26), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'mote' });
    },
    draw() { const a = Math.min(1, this.t / 0.12, (this.life - this.t) / 0.3); if (!wfxDraw('pyre', this.t, this.x, this.fy + 1, 1, { loop: true, alpha: a })) { g.fillStyle = `rgba(255,244,210,${0.6 * a})`; g.fillRect(this.x - 4, this.fy - 22, 8, 22); } addLight(this.x, this.fy - 14, 36, '255,244,210', 0.7 * a); } });
  sig9Pyres.push(e);
  tone(520, 0.3, 0.03, 'sine', 1.5);
}
// ---- v8 signature helpers
function sigInkGlyph(t, info) {
  if (t.prop || !sigTargetCd(t, 'glyph', SIG_ICD)) return;
  const ox = info.x - t.x, oy = info.y - t.y;
  wfx({ life: 1.05, fired: false, x: info.x, y: info.y,
    update() {
      if (!this.fired) { this.x = t.x + ox; this.y = t.y + oy; }
      if (this.t >= 0.62 && !this.fired) {
        this.fired = true;
        if (t.alive !== false) t.hit({ dmg: D.light * 0.14 * (1 + (D.spell - 1) * 0.5), poise: 8, dir: t.x > P.x ? 1 : -1, kind: 'spell', x: this.x, y: this.y, sig: true });
        sfx.bolt(); noise(0.2, 700, 1, 0.2, 'lowpass');
        for (let i = 0; i < 10; i++) particles.push({ x: this.x, y: this.y, vx: rand(-80, 80), vy: rand(-90, 30), g: 200, life: rand(0.3, 0.6), kind: 'ink' });
      }
    },
    draw() {
      if (!this.fired) { const k = Math.min(1, this.t / 0.15); wfxDraw('glyph', this.t, this.x, this.y, 1, { center: true, loop: true, alpha: k }); addLight(this.x, this.y, 22, '170,120,240', 0.6); }
      else { wfxDraw('inkburst', this.t - 0.62, this.x, this.y, 1, { center: true }); addLight(this.x, this.y, 40, '170,120,240', 0.8); }
    } });
}
function sigInkBlots(go) {   // the spin flings ink both ways; it splashes out within reach
  const L = sigLimit(), ox = P.x, skip = new Set();
  for (const d of [-1, 1]) for (let k = 0; k < 2; k++) {
    wfx({ life: 1.4, x: P.x + d * 10, y: P.y - 20, vx: d * rand(70, 130), vy: -rand(110, 200), splat: -1,
      update(dt) {
        if (this.splat >= 0) return this.t - this.splat < 0.4;
        this.vy += 520 * dt; this.x += this.vx * dt; this.y += this.vy * dt;
        if (Math.abs(this.x - ox) > L) { this.splat = this.t; return; }
        if (Math.random() < 0.5) particles.push({ x: this.x, y: this.y, vx: 0, vy: 0, life: 0.25, kind: 'ink' });
        const hit = go ? sigStrike(rect(this.x - 5, this.y - 5, this.x + 5, this.y + 5), D.light * 0.12, { skip, poise: 6, dir: d, ox, L }) : [];
        if (hit.length || solidAtPx(this.x, this.y)) { this.splat = this.t; sfx.hit(); }
      },
      draw() {
        if (this.splat >= 0) wfxDraw('inkburst', (this.t - this.splat) * 1.4, this.x, this.y, 1, { center: true, alpha: 0.85 });
        else if (!wfxDraw('inkblot', this.t, this.x, this.y, this.vx > 0 ? 1 : -1, { center: true, loop: true })) { g.fillStyle = '#6a3ab0'; g.fillRect(Math.round(this.x) - 2, Math.round(this.y) - 2, 4, 4); }
        addLight(this.x, this.y, 16, '170,120,240', 0.5);
      } });
  }
}
function sigLavaCrack(hot) {   // seams of magma along the blow; only a fully charged heavy makes them burn and erupt
  const segs = [], L = sigLimit();
  for (let k = 0; k < 6; k++) {
    const x = P.x + P.face * (18 + k * 12); if (Math.abs(x - P.x) > L - 6) break;
    const fy = wFloorBelow(x, P.y - 4);
    if (fy === null || Math.abs(fy - P.y) > 20) break;
    segs.push({ x, fy });
  }
  if (!segs.length) return;
  sfx.fire(); shake = Math.max(shake, hot ? 5 : 3);
  const life = hot ? 1.8 : 0.9, eskip = new Set();
  wfx({ life, segs, face: P.face, tick: 0.2,
    update(dt) {
      if (hot && (this.tick -= dt) <= 0) {   // the seams burn whatever stands in them
        this.tick = 0.45; const skip = new Set();
        for (const s2 of this.segs) wStrike(rect(s2.x - 7, s2.fy - 18, s2.x + 7, s2.fy + 1), D.heavy * 0.04, { skip, fire: true, quiet: true });
      }
      if (hot) this.segs.forEach((s2, i) => {   // the eruption: one burst of magma per foe
        const at = 0.12 + i * 0.07;
        if (!s2.erupted && this.t >= at) {
          s2.erupted = this.t; shake = Math.max(shake, 5); if (i % 2 === 0) sfx.boom();
          wStrike(rect(s2.x - 9, s2.fy - 44, s2.x + 9, s2.fy + 1), D.heavy * 0.22, { skip: eskip, poise: 30, big: true, fire: true, kind: 'heavy' });
          for (let q = 0; q < 10; q++) particles.push({ x: s2.x + rand(-5, 5), y: s2.fy - 4, vx: rand(-40, 40), vy: -rand(120, 260), g: 420, life: rand(0.5, 1.0), kind: 'fire' });
        }
      });
      if (Math.random() < (hot ? 0.4 : 0.2)) { const s2 = this.segs[irand(0, this.segs.length - 1)]; particles.push({ x: s2.x + rand(-6, 6), y: s2.fy - 1, vx: 0, vy: -rand(20, 50), life: 0.5, kind: 'ember' }); }
    },
    draw() {
      const fade = Math.min(1, (this.life - this.t) / 0.5) * (hot ? 1 : 0.7);
      for (const s2 of this.segs) {
        if (!wfxDraw('lava', this.t + s2.x * 0.013, s2.x, s2.fy + 2, this.face, { loop: true, alpha: fade })) { g.fillStyle = `rgba(255,120,40,${fade})`; g.fillRect(s2.x - 6, s2.fy - 1, 12, 2); }
        addLight(s2.x, s2.fy - 4, 26, '255,130,50', 0.7 * fade);
        if (s2.erupted) wfxDraw('erupt', this.t - s2.erupted, s2.x, s2.fy + 1, this.face);
      }
    } });
}
function sigChain(p, go) {   // lightning arcs into the foe before you (and on to lesser foes within reach)
  const L = sigLimit(), hops = [], seen = new Set(); let from = p, t = sigFrontTarget(P.x, p.y, sigReach() + 8);
  while (t && hops.length < 3) {
    seen.add(t); const c = hbMid(t);
    hops.push({ t, from, to: c }); from = c;
    let nb = null, nd = 60;
    for (const q of targets()) { if (!sigSmallFoe(q) || seen.has(q)) continue; const h2 = q.hurtbox(); if (!h2) continue; const cx = (h2.x0 + h2.x1) / 2; if (Math.abs(cx - P.x) > L) continue; const d = Math.hypot(cx - c.x, (h2.y0 + h2.y1) / 2 - c.y); if (d < nd) { nd = d; nb = q; } }
    t = nb;
  }
  if (!hops.length) { wZap(p.x, p.y, p.x + P.face * 26, p.y + rand(-8, 8), 0.12); noise(0.1, 3500, 2, 0.1, 'highpass'); return; }
  wfx({ life: 0.1 + hops.length * 0.08, i: 0,
    update() {
      while (this.i < hops.length && this.t >= this.i * 0.08) {
        const h = hops[this.i++]; wZap(h.from.x, h.from.y, h.to.x, h.to.y, 0.2);
        if (go && h.t.alive !== false) h.t.hit({ dmg: D.light * (this.i === 1 ? 0.3 : 0.15), poise: 10, dir: P.face, kind: 'spell', x: h.to.x, y: h.to.y, big: this.i === 1, sig: true });
        noise(0.12, 3000, 2, 0.16, 'highpass'); tone(1800, 0.08, 0.04, 'square', 0.5);
      }
    } });
}
function sigSkyBolt(go) {   // a bolt falls on the foe before you (or on the end of your reach)
  const L = sigLimit(), t = sigFrontTarget(P.x, P.y - 16, L - 10);
  let x = P.x + P.face * Math.min(56, L - 10);
  if (t) x = clamp(hbMid(t).x, P.x - L + 10, P.x + L - 10);
  const fy = wFloorBelow(x, P.y - 8) ?? P.y;
  sfx.charge();
  wfx({ life: 0.85, x, fy, struck: false,
    update() {
      if (!this.struck && this.t >= 0.3) {
        this.struck = true; flashScreen = Math.max(flashScreen, 0.18); shake = Math.max(shake, 6);
        noise(0.7, 900, 0.7, 0.6, 'lowpass', 0.4); noise(0.25, 5000, 2, 0.3, 'highpass'); tone(60, 0.5, 0.3, 'sawtooth', 0.5);
        if (go) sigStrike(rect(this.x - 14, this.fy - 90, this.x + 14, this.fy + 2), D.heavy * 0.35, { poise: 30, big: true, kind: 'heavy' });
        for (let i = 0; i < 16; i++) particles.push({ x: this.x + rand(-6, 6), y: this.fy - 2, vx: rand(-120, 120), vy: -rand(40, 160), g: 400, life: rand(0.3, 0.6), kind: 'spark' });
      }
    },
    draw() {
      if (this.t < 0.3) {   // telegraph: the air crackles over the spot
        const k = this.t / 0.3; g.fillStyle = `rgba(170,210,255,${0.25 + 0.35 * k})`; g.fillRect(Math.round(this.x - 8 * k), Math.round(this.fy) - 1, Math.round(16 * k), 1);
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-6, 6), y: this.fy - rand(0, 40), vx: 0, vy: -20, life: 0.2, kind: 'frost' });
        addLight(this.x, this.fy - 8, 20 + 20 * k, '170,210,255', 0.6);
      } else {
        if (!wfxDraw('bolt', this.t - 0.3, this.x, this.fy + 2, 1)) wDrawBolt(wBoltPath(this.x + rand(-10, 10), this.fy - 110, this.x, this.fy), 1 - (this.t - 0.3) / 0.55, 1.4);
        addLight(this.x, this.fy - 40, 90, '180,220,255', Math.max(0, 1 - (this.t - 0.3) / 0.5));
      }
    } });
}
function sigGust(p, go) {   // a puff of wind off every blow; a finisher's gust buffets what it meets
  tone(300, 0.2, go ? 0.03 : 0.015, 'sine', 1.8); noise(0.2, 1500, 0.7, go ? 0.12 : 0.05, 'bandpass', 0.5);
  const L = sigLimit(), ox = P.x, skip = new Set(), life = go ? 0.3 : 0.14;
  wfx({ life, x: p.x, y: p.y, face: P.face,
    update(dt) {
      this.x += this.face * 260 * dt;
      if (Math.abs(this.x - ox) > L || solidAtPx(this.x + this.face * 6, this.y)) return false;
      if (go) for (const t of sigStrike(rect(this.x - 10, this.y - 12, this.x + 10, this.y + 12), D.light * 0.2, { skip, poise: 8, dir: this.face, ox, L })) if (sigSmallFoe(t) && t.vx !== undefined) t.vx += this.face * 120;
    },
    draw() { if (!wfxDraw('gust', this.t, this.x, this.y, this.face, { center: true, alpha: (go ? 1 : 0.6) * (1 - this.t / this.life) })) { g.fillStyle = 'rgba(210,250,240,0.5)'; g.fillRect(this.x - 6, this.y - 1, 12, 2); } } });
}
function sigWhirlwind(go) {   // the spin looses a short whirlwind; it carries lesser foes, never great ones
  const L = sigLimit(), ox = P.x, x0 = P.x + P.face * 22, fy = wFloorBelow(x0, P.y - 8) ?? P.y;
  noise(1.0, 700, 0.6, 0.3, 'bandpass', 1.6); tone(180, 0.7, 0.05, 'sine', 1.6);
  wfx({ life: 1.3, x: x0, fy, face: P.face, tick: 0, n: 0,
    update(dt) {
      if (Math.abs(this.x - ox) < L - 14 && !solidAtPx(this.x + this.face * 12, this.fy - 8)) this.x += this.face * 70 * dt;
      if (go && this.n < 3 && (this.tick -= dt) <= 0) { this.tick = 0.4; this.n++; sigStrike(rect(this.x - 14, this.fy - 44, this.x + 14, this.fy), D.light * 0.1, { poise: 6, dir: this.face, quiet: this.n > 1, ox, L }); }
      for (const t of targets()) {   // small foes are caught and carried along
        if (!sigSmallFoe(t) || !t.hurtbox()) continue;
        if (Math.abs(t.x - this.x) < 24 && Math.abs(t.y - this.fy) < 34) { t.x += (this.x - t.x) * Math.min(1, dt * 6); if (t.vx !== undefined) t.vx = this.face * 70; }
      }
      if (Math.random() < 0.6) particles.push({ x: this.x + rand(-12, 12), y: this.fy - rand(0, 40), vx: rand(-40, 40), vy: -rand(20, 70), life: 0.4, kind: Math.random() < 0.5 ? 'dust' : 'mote' });
    },
    draw() {
      const a = Math.min(1, this.t / 0.15, (this.life - this.t) / 0.35);
      if (!wfxDraw('whirl', this.t, this.x, this.fy + 1, this.face, { loop: true, alpha: a })) { g.fillStyle = `rgba(210,250,240,${0.4 * a})`; g.fillRect(this.x - 8, this.fy - 40, 16, 40); }
      addLight(this.x, this.fy - 20, 30, '200,250,240', 0.4 * a);
    } });
}
// First Ember: the swing's golden afterimage replays a heartbeat later
function sigEmberEcho(A) {
  const snap = { f: P.anim.frame, x: P.x, y: P.y, face: P.face }, big = sigBig(A);
  wfx({ life: big ? 0.7 : 0.55, draw() {
    if (this.t < 0.16) return;
    const a = (big ? 0.7 : 0.55) * (1 - (this.t - 0.16) / (this.life - 0.16));
    drawSprite(sheet('player'), snap.f, snap.x, snap.y, snap.face, { flash: 1, flashColor: '#ffb050', alpha: a });
    const ws = sheet('wpn_first_ember'); if (ws.ok) drawSprite(ws, snap.f, snap.x, snap.y, snap.face, { flash: 1, flashColor: '#fff0c0', alpha: a });
    addLight(snap.x + snap.face * 14, snap.y - 18, 40, '255,180,90', a);
  } });
  if (big) { const r = sigRect(A); sigArc(sigPoint(r), '#ffb050', sigRot(A), { r: 24, life: 0.4, light: '255,180,90', alpha: 0.7 }); }
}
// Twinborne: a stoked blade smoulders between blows
HOOKS.update.push(() => {
  if (!P || SAVE.weapon !== 'twinborne' || !(P.sigCharge > 0)) return;
  if (Math.random() < 0.2 * P.sigCharge) particles.push({ x: P.x + P.face * rand(6, 18), y: P.y - rand(14, 28), vx: 0, vy: -rand(15, 40), life: 0.4, kind: 'fire' });
});
// bosses are big: give the player's blows a little more to hit
function hbOf(t) { const hb = t.hurtbox(); if (!hb || !t.boss) return hb; return rect(hb.x0 - 8, hb.y0 - 6, hb.x1 + 8, hb.y1); }
