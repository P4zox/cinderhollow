// ------------------------------------------------------------------ boss weapons: each carries its former owner's signature effects
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
function sigTrail(A, sg) {
  const r = sigRect(A);
  for (let i = 0; i < 3; i++) particles.push({ x: P.face > 0 ? r.x1 - rand(0, 10) : r.x0 + rand(0, 10), y: rand(r.y0, r.y1), vx: P.face * rand(10, 50), vy: -rand(0, 30), life: rand(0.2, 0.45), kind: Math.random() < 0.75 ? sg.pk : sg.pk2 });
  addLight((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, 46, sg.light, 0.8);
}
function burst(x, y, n, k1, k2, spd = 100) { for (let i = 0; i < n; i++) particles.push({ x: x + rand(-8, 8), y: y + rand(-12, 12), vx: P.face * rand(20, spd), vy: -rand(10, 70), g: 160, life: rand(0.3, 0.7), kind: Math.random() < 0.7 ? k1 : k2 }); }
// player-owned ground effects that hurt foes: root spikes and light pillars
function groundFx(kind, x, delay, dmg) {
  const f = { proot: ['root_spike', [0.18, 0.5]], ppillar: ['lightpillar', [0.3, 0.62]] }[kind];
  let fy = Math.floor(P.y / TILE) * TILE;
  for (let k = 0; k < 4 && !solidAtPx(x, fy + 1); k++) fy += TILE;   // find the floor under the point
  if (!solidAtPx(x, fy + 1) || solidAtPx(x, fy - 4)) return;
  projectiles.push({ owner: 'player', kind, x, y: fy, vx: 0, vy: 0, dmg, life: 0.9, r: 9, t: 0, pierce: true, static: true, fxName: f[0], win: f[1], hits: new Set(), poise: 40, face: P.face,
                    delay, onStart: () => kind === 'ppillar' ? sfx.pillar() : sfx.crumble() });
}
const SIGS = {
  kalden: { glow: '#7ff0d0', light: '120,230,200', pk: 'teal', pk2: 'gold', replaceFx: true,
    swing(A, r) {
      const p = sigPoint(r), heavy = A.kind === 'heavy', rot = SIG_ROT[P.state] ?? 0;
      spawnFx(fxOr('kalden_slash', 'slash3'), p.x, p.y, P.face, null, { rot, speed: heavy ? 0.8 : 1.15, alpha: 0.95 });
      if (heavy || isFinisher(P.state)) { spawnFx(fxOr('kalden_slash', 'slash3'), p.x + P.face * 8, p.y, P.face, null, { rot: rot * 0.5, speed: 0.7, alpha: 0.55 }); shake = Math.max(shake, heavy ? 4 : 2); }
      tone(heavy ? 330 : 440, 0.35, 0.05, 'triangle', 0.55); tone(heavy ? 660 : 880, 0.25, 0.03, 'sine', 0.7);
      burst(p.x, p.y, heavy ? 18 : 9, 'teal', 'gold');
    } },
  gravetusk: { glow: '#ffd27a', light: '255,200,110', pk: 'root', pk2: 'gold',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 10, 'root', 'gold'); tone(150, 0.3, 0.06, 'sawtooth', 0.6); },
    finisher(A, r) {
      const n = A.kind === 'heavy' ? 4 : 2, d = D.heavy * (A.kind === 'heavy' ? 1.0 : 0.7);
      for (let k = 0; k < n; k++) groundFx('proot', P.x + P.face * (30 + k * 20), 0.08 + k * 0.09, d);
      shake = Math.max(shake, 3);
    } },
  omen: { glow: '#ffcf6a', light: '255,210,120', pk: 'gold', pk2: 'ember', replaceFx: true,
    swing(A, r) {
      const p = sigPoint(r), heavy = A.kind === 'heavy', rot = SIG_ROT[P.state] ?? 0;
      spawnFx(fxOr('boss_slash', 'slash3'), p.x, p.y, P.face, null, { rot, speed: heavy ? 0.85 : 1.2, alpha: 0.95 });
      burst(p.x, p.y, heavy ? 16 : 8, 'gold', 'ember'); tone(heavy ? 392 : 523, 0.3, 0.05, 'triangle', 0.6);
    },
    finisher(A, r) {
      const n = A.kind === 'heavy' ? 2 : 1;
      for (let k = 0; k < n; k++) projectiles.push({ owner: 'player', kind: 'sunspear', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 16, y: P.y - 20 + (k - (n - 1) / 2) * 7,
        vx: P.face * (330 + k * 20), vy: (k - (n - 1) / 2) * 25, dmg: D.light * 0.65, life: 1.0, r: 6, pierce: true, sh: 'fx_light_spear' });
      sfx.spear(); flashScreen = Math.max(flashScreen, 0.08);
    } },
  rotmaw: { glow: '#9ae05a', light: '150,210,90', pk: 'spore', pk2: 'ember',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 10, 'spore', 'ember'); if (A.kind === 'heavy' || isFinisher(P.state)) spawnFx(fxOr('rot_hit', 'hit'), p.x, p.y, P.face); },
    finisher(A, r) {
      if (A.kind !== 'heavy') return;
      projectiles.push({ owner: 'player', kind: 'mist', x: P.x + P.face * 34, y: P.y, vx: 0, vy: 0, dmg: D.heavy * 0.22, life: 3.2, r: 26, pierce: true, tick: 0.45, static: true, t: 0, hits: new Set(), face: P.face, sh: 'fx_rotmist' });
      sfx.fire();
    } },
  scepter: { glow: '#fff2c8', light: '255,245,220', pk: 'petal', pk2: 'gold',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'petal', 'gold'); tone(988, 0.25, 0.04, 'sine', 1.3); },
    finisher(A, r) {
      if (A.kind === 'heavy') {
        groundFx('ppillar', P.x + P.face * 56, 0.05, D.heavy * 1.7);
        spawnFx(fxOr('holy_burst', 'parry_flash'), P.x + P.face * 30, P.y - 18, P.face, null, { alpha: 0.8 });
      } else {
        projectiles.push({ owner: 'player', kind: 'sovlance', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 20, y: P.y - 18, vx: P.face * 360, vy: 0, dmg: D.light * 1.1, life: 0.9, r: 6, pierce: true, sh: 'fx_sov_lance' });
        sfx.spear();
      }
    } },
  // ---- v8 expansion boss weapons (helpers wfx / wStrike / zap / addFrost / addBurn live in 13_weapons.js)
  inkquill: { glow: '#b890ff', light: '170,120,240', pk: 'ink', pk2: 'gold',
    swing(A, r) {
      const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 14 : 7, 'ink', 'gold');
      tone(A.kind === 'heavy' ? 311 : 523, 0.25, 0.04, 'sine', 0.6);
      if (A.staffSpin) sigInkBlots();
    },
    hit(t, info) { sigInkGlyph(t, info); } },
  twinborne: { get glow() { return P && P.sigCharge > 0 ? '#ff9a40' : '#a8dcff'; }, get light() { return P && P.sigCharge > 0 ? '255,160,70' : '170,220,255'; },
    get pk() { return P && P.sigCharge > 0 ? 'ember' : 'frost'; }, pk2: 'frost',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, P.sigCharge > 0 ? 'fire' : 'frost', 'frost'); },
    hit(t, info) {   // a stoked blade: the next blow bursts into flame
      if (!(P.sigCharge > 0) || t.prop) return;
      P.sigCharge--;
      t.hit({ dmg: D.light * 0.75, poise: 20, dir: info.dir, kind: 'spell', x: info.x, y: info.y, big: true, fire: true });
      wAddBurn(t, 3.5, D.light * 0.35);
      spawnFx(fxOr('cinderblade', 'hit'), info.x, info.y, P.face); sfx.fire();
      for (let i = 0; i < 14; i++) particles.push({ x: info.x, y: info.y, vx: rand(-70, 70), vy: -rand(30, 120), g: 120, life: rand(0.3, 0.7), kind: 'fire' });
    },
    block(src) {   // blocking chills the attacker and stokes the blade
      P.sigCharge = Math.min(3, (P.sigCharge || 0) + 1);
      tone(1320, 0.2, 0.05, 'triangle', 0.7); tone(220, 0.3, 0.05, 'sawtooth', 1.4);
      for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * 14, y: P.y - rand(10, 26), vx: P.face * rand(30, 140), vy: rand(-40, 20), life: rand(0.3, 0.6), kind: 'frost' });
      if (src && !src.prop && typeof src.hit === 'function' && src.hurtbox && src.hurtbox()) wAddFrost(src, 38);
    } },
  colossus_hammer: { glow: '#ff9a40', light: '255,150,60', pk: 'ember', pk2: 'fire',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 16 : 8, 'ember', 'fire'); tone(90, 0.3, 0.06, 'sawtooth', 0.6); },
    finisher(A) { if (A.kind === 'heavy') sigLavaCrack(!!P.charged); } },
  stormfang: { glow: '#9fd0ff', light: '150,200,255', pk: 'frost', pk2: 'spark',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'frost', 'spark'); noise(0.08, 4000, 2, 0.08, 'highpass'); },
    finisher(A, r) { if (A.kind === 'heavy') sigSkyBolt(); else sigChain(sigPoint(r)); },
    dive(t, info) { sigChain({ x: info.x, y: info.y }); } },
  windstaff: { glow: '#c8fff4', light: '200,250,240', pk: 'mote', pk2: 'dust',
    swing(A, r) {
      const p = sigPoint(r); burst(p.x, p.y, 6, 'mote', 'dust');
      if (A.staffSpin) sigWhirlwind(); else if (A.kind === 'light') sigGust(p);
    } },
  first_ember: { glow: '#ffb050', light: '255,180,90', pk: 'ember', pk2: 'gold',
    swing(A, r) { sigEmberEcho(A, r); },
    hit(t, info) {   // every blow strikes again a moment later
      if (t.prop) return;
      wfx({ life: 0.36, update() {
        if (this.t < 0.3 || this.done) return; this.done = true;
        if (t.alive === false) return;
        t.hit({ dmg: info.dmg * 0.25, poise: (info.poise || 0) * 0.3, dir: info.dir, kind: 'light', x: info.x, y: info.y, fire: true, melee: true });
        spawnFx(fxOr('embers', 'hit'), info.x, info.y, info.dir); tone(740, 0.2, 0.04, 'triangle', 0.8);
        for (let i = 0; i < 8; i++) particles.push({ x: info.x, y: info.y, vx: rand(-60, 60), vy: -rand(20, 90), g: 100, life: rand(0.3, 0.6), kind: 'ember' });
      } });
    } },
  // ---- v9 (Expansion 2) boss weapons
  antler_scythe: { glow: '#9fe8a0', light: '140,230,150', pk: 'spore', pk2: 'root',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 14 : 7, 'spore', 'root'); },
    finisher(A) { sig9Thorns(A.kind === 'heavy' ? 4 : 3, A.kind === 'heavy' ? 0.5 : 0.35); } },
  choir_harpoon: { glow: '#7ff0e0', light: '100,230,210', pk: 'teal', pk2: 'frost',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'teal', 'frost'); },
    finisher(A, r) { const p = sigPoint(r); if (A.kind === 'heavy') for (const vy of [-50, 0, 50]) sig9WaterLance(p, vy, 0.6); else sig9WaterLance(p, 0, 0.8); },
    dive(t, info) { sig9WaterLance({ x: info.x, y: info.y }, 0, 0.6); } },
  sanguine_rapier: { glow: '#ff5060', light: '240,60,80', pk: 'blood', pk2: 'fire',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 6, 'blood', 'blood'); },
    finisher(A, r) { const p = sigPoint(r); sig9BloodLance(p, 0); if (A.kind === 'heavy') { sig9BloodLance(p, -40); sig9BloodLance(p, 40); } },
    crit(t, dmg) {   // every critical blow drinks deep
      const h = Math.round(Math.min(D.maxHp * 0.25, dmg * 0.3));
      P.hp = Math.min(D.maxHp, P.hp + h); popup(P.x, P.y - 34, h, '#ff6a7a'); sfx.bleed();
      for (let i = 0; i < 16; i++) particles.push({ x: t.x + rand(-8, 8), y: t.y - rand(6, 26), vx: (P.x - t.x) * rand(2, 3), vy: -rand(0, 30), life: 0.45, kind: 'blood' });
    } },
  vael_greatsword: { glow: '#a8dcff', light: '150,200,255', pk: 'frost', pk2: 'teal',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, A.kind === 'heavy' ? 16 : 8, 'frost', 'teal'); tone(A.kind === 'heavy' ? 180 : 260, 0.35, 0.04, 'sine', 0.6); },
    hit(t, info) { if (!t.prop) wAddBurn(t, 2.5, D.light * 0.16); },   // ghost-fire in the wound
    finisher(A) { if (A.kind === 'heavy') sig9Chains(); } },
  pharaoh_khopesh: { glow: '#ffd070', light: '255,210,120', pk: 'gold', pk2: 'dust',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'gold', 'dust'); },
    finisher(A, r) { if (A.kind === 'heavy') sig9Sand(); else sig9SunDisc(sigPoint(r)); } },
  starblade: { glow: '#c8d8ff', light: '190,210,255', pk: 'mote', pk2: 'frost',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'mote', 'frost'); tone(1480, 0.2, 0.03, 'sine', 1.3); },
    finisher(A) { sig9Stars(A.kind === 'heavy' ? 5 : 3); } },
  saint_lance: { glow: '#70fff8', light: '120,255,250', pk: 'teal', pk2: 'spark',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 6, 'teal', 'spark'); tone(1760, 0.08, 0.04, 'square', 0.5); },
    finisher(A, r) { sig9Laser(sigPoint(r), A.kind === 'heavy'); },
    hit(t, info) { sig9Glitch(t, info); },
    dive(t, info) { sig9Laser({ x: info.x, y: info.y }, false); } },
  last_kindling: { glow: '#fff4d0', light: '255,244,210', pk: 'mote', pk2: 'gold',
    swing(A, r) { const p = sigPoint(r); burst(p.x, p.y, 8, 'mote', 'gold'); },
    hit(t, info) { sig9Pyre(t.x, t.y, t); },
    finisher(A) { if (A.kind === 'heavy') for (const k of [0, 1]) sig9Pyre(P.x + P.face * (8 + k * 26), P.y, null, true); } },
};
// ---- v9 signature helpers (entities live in 13_weapons.js's WFX list)
const sig9Pyres = [];
function sig9Thorns(n, mult) {   // thorns erupt along the sweep, one after another
  sfx.crumble();
  for (let k = 0; k < n; k++) {
    const x = P.x + P.face * (22 + k * 14), fy = wFloorBelow(x, P.y - 6);
    if (fy === null || Math.abs(fy - P.y) > 24 || solidAtPx(x, fy - 8)) break;
    wfx({ life: 0.55 + k * 0.07, x, fy, at: k * 0.07, face: P.face, done: false, skip: new Set(),
      update() {
        if (this.t >= this.at + 0.05 && !this.done) { this.done = true; wStrike(rect(this.x - 7, this.fy - 26, this.x + 7, this.fy + 1), D.light * mult, { poise: 22, skip: this.skip, dir: this.face });
          for (let i = 0; i < 5; i++) particles.push({ x: this.x + rand(-5, 5), y: this.fy - 2, vx: rand(-40, 40), vy: -rand(40, 110), g: 380, life: 0.5, kind: i % 2 ? 'spore' : 'root' }); }
      },
      draw() { if (this.t >= this.at) { if (!wfxDraw('thorn', this.t - this.at, this.x, this.fy + 1, this.face)) { g.fillStyle = '#6a8a40'; g.fillRect(this.x - 1, this.fy - 18, 3, 18); } addLight(this.x, this.fy - 10, 22, '140,230,150', 0.5); } } });
  }
}
function sig9Proj(o) {   // a straight player projectile drawn from a wpn_fx sheet, rotated along its flight
  return wfx(Object.assign({ skip: new Set(), life: 0.6, update(dt) {
    this.x += this.vx * dt; this.y += this.vy * dt;
    if (solidAtPx(this.x, this.y)) { this.onEnd && this.onEnd(); return false; }
    for (const t of wStrike(rect(this.x - 6, this.y - 4, this.x + 6, this.y + 4), this.dmg, { skip: this.skip, poise: this.poise || 12, dir: Math.sign(this.vx) || 1, kind: 'spell' })) this.onHit && this.onHit(t);
    if (this.trail && Math.random() < 0.7) particles.push({ x: this.x - Math.sign(this.vx) * 6, y: this.y + rand(-1, 1), vx: -this.vx * 0.1, vy: rand(-10, 10), life: 0.3, kind: this.trail });
  }, draw() { const a = Math.atan2(this.vy, Math.abs(this.vx)); if (!wfxDraw(this.sheet, this.t, this.x, this.y, Math.sign(this.vx) || 1, { center: true, loop: true, rot: a * (Math.sign(this.vx) || 1) })) { g.fillStyle = this.col || '#fff'; g.fillRect(this.x - 4, this.y - 1, 8, 2); } addLight(this.x, this.y, 26, this.light || '255,255,255', 0.6); } }, o));
}
function sig9WaterLance(p, vy, mult) {
  sfx.spear(); noise(0.2, 1200, 0.8, 0.12, 'bandpass', 0.6);
  sig9Proj({ x: p.x, y: p.y, vx: P.face * 300, vy, dmg: D.light * mult, sheet: 'waterlance', trail: 'teal', light: '100,230,210', col: '#70e8d8', poise: 16,
    onHit(t) { if (!t.prop && !t.boss && !(t.cfg && t.cfg.elite) && t.vx !== undefined) { t.vx = -P.face * 120; weaponPull(t, { chain: false }); } } });   // the tide drags them in
}
function sig9BloodLance(p, vy) {
  sig9Proj({ x: p.x, y: p.y, vx: P.face * 360, vy, dmg: D.light * 0.45, sheet: 'bloodlance', trail: 'blood', light: '240,60,80', col: '#e02040', poise: 10,
    onHit(t) { if (t.hit && !t.prop) t.hit({ dmg: 0, poise: 0, dir: P.face, kind: 'spell', x: t.x, y: t.y - 14, bleed: 16, quiet: true }); } });
  tone(880, 0.15, 0.04, 'sawtooth', 0.5);
}
function sig9Chains() {   // spectral chains burst from the ground and bind the nearest foe ahead
  const t = sigFrontTarget(P.x, P.y - 16, 130); if (!t) return;
  const hb = t.hurtbox(); if (!hb) return;
  const fy = wFloorBelow((hb.x0 + hb.x1) / 2, hb.y1 - 4) ?? hb.y1;
  tone(120, 0.6, 0.08, 'sawtooth', 1.4); noise(0.4, 2400, 1, 0.15, 'highpass');
  wfx({ life: 1.4, t0: t, anchors: [(hb.x0 + hb.x1) / 2 - 22, (hb.x0 + hb.x1) / 2 + 22], fy, bound: false,
    update() {
      if (!this.bound && this.t > 0.25) {
        this.bound = true; if (t.alive !== false && t.hit) { t.hit({ dmg: D.heavy * 0.9, poise: 40, dir: P.face, kind: 'spell', x: t.x, y: t.y - 16, big: true }); t._slowT = t.boss ? 1.2 : 2.0; wSlowWrap(t); }
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
function sig9SunDisc(p) {   // a disc of sunlight flung out that comes back to the hand
  sfx.heavySwing(); tone(660, 0.3, 0.04, 'triangle', 1.2);
  wfx({ life: 1.4, x: p.x, y: p.y, vx: P.face * 300, back: false, skip: new Set(),
    update(dt) {
      if (!this.back) { this.vx -= Math.sign(this.vx) * 520 * dt; if (Math.abs(this.vx) < 20 || solidAtPx(this.x + Math.sign(this.vx) * 6, this.y)) { this.back = true; this.skip = new Set(); } this.x += this.vx * dt; }
      else { const dx = P.x - this.x, dy = P.y - 18 - this.y, d = Math.hypot(dx, dy) || 1; this.x += dx / d * 320 * dt; this.y += dy / d * 320 * dt; if (d < 10) return false; }
      wStrike(rect(this.x - 7, this.y - 7, this.x + 7, this.y + 7), D.light * 0.3, { skip: this.skip, poise: 12, fire: true, kind: 'spell' });
      if (Math.random() < 0.5) particles.push({ x: this.x, y: this.y, vx: rand(-20, 20), vy: rand(-20, 20), life: 0.3, kind: 'gold' });
    },
    draw() { if (!wfxDraw('sundisc', this.t, this.x, this.y, 1, { center: true, loop: true })) { g.fillStyle = '#ffd070'; g.fillRect(this.x - 4, this.y - 4, 8, 8); } addLight(this.x, this.y, 34, '255,210,120', 0.8); } });
}
function sig9Sand() {   // the heavy raises a burst of scouring sand around you
  sfx.crumble(); shake = Math.max(shake, 4);
  wStrike(rect(P.x - 44, P.y - 30, P.x + 44, P.y + 2), D.heavy * 0.45, { poise: 30, kind: 'spell' });
  for (let i = 0; i < 40; i++) { const a = rand(0, Math.PI); particles.push({ x: P.x + Math.cos(a) * rand(4, 20), y: P.y - rand(0, 8), vx: Math.cos(a) * rand(60, 160) * (Math.random() < 0.5 ? 1 : -1), vy: -rand(20, 110), g: 260, life: rand(0.4, 0.9), kind: 'dust' }); }
  spawnFx('shockwave', P.x, P.y, 1);
}
function sig9Stars(n) {   // star shards fall on what stands before you
  const xs = [];
  for (const t of targets()) { if (t.prop) continue; const hb = t.hurtbox(); if (!hb) continue; const cx = (hb.x0 + hb.x1) / 2; if ((cx - P.x) * P.face > -10 && Math.abs(cx - P.x) < 150) xs.push(cx); }
  for (let k = 0; k < n; k++) {
    const x = xs.length ? xs[k % xs.length] + rand(-10, 10) : P.x + P.face * (30 + k * 18);
    const fy = wFloorBelow(x, P.y - 8) ?? P.y;
    wfx({ life: 1.2, x: x + P.face * 30, y: fy - 110, tx: x, fy, at: k * 0.1, hit: false, skip: new Set(),
      update(dt) {
        if (this.t < this.at || this.hit) return this.hit ? this.t < this.hitT + 0.3 : undefined;
        const k2 = Math.min(1, (this.t - this.at) / 0.28); this.cx = this.x + (this.tx - this.x) * k2; this.cy = this.y + (this.fy - this.y) * k2;
        if (Math.random() < 0.8) particles.push({ x: this.cx, y: this.cy, vx: rand(-10, 10), vy: -rand(0, 20), life: 0.3, kind: 'mote' });
        if (k2 >= 1) { this.hit = true; this.hitT = this.t; wStrike(rect(this.tx - 12, this.fy - 24, this.tx + 12, this.fy + 1), D.light * 0.65, { skip: this.skip, poise: 20, kind: 'spell' }); shake = Math.max(shake, 3); tone(1320, 0.3, 0.05, 'triangle', 0.5); for (let i = 0; i < 10; i++) particles.push({ x: this.tx, y: this.fy - 2, vx: rand(-80, 80), vy: -rand(30, 120), g: 300, life: 0.5, kind: i % 2 ? 'mote' : 'frost' }); }
      },
      draw() {
        if (this.t < this.at) return;
        if (!this.hit) { const a = Math.atan2(this.fy - this.y, this.tx - this.x) - Math.PI / 2; if (!wfxDraw('starshard', this.t, this.cx ?? this.x, this.cy ?? this.y, 1, { center: true, loop: true, rot: a })) { g.fillStyle = '#e8f0ff'; g.fillRect(this.cx - 1, this.cy - 3, 3, 6); } addLight(this.cx ?? this.x, this.cy ?? this.y, 30, '200,220,255', 0.8); }
        else { addLight(this.tx, this.fy - 8, 40, '200,220,255', Math.max(0, 1 - (this.t - this.hitT) / 0.3)); }
      } });
  }
}
function sig9Laser(p, wide) {   // a neon laser line drawn through the world
  let x1 = p.x; const dir = P.face;
  for (let k = 0; k < 200; k += 4) { if (solidAtPx(p.x + dir * k, p.y)) break; x1 = p.x + dir * k; }
  const hw = wide ? 5 : 3;
  wStrike(rect(Math.min(p.x, x1), p.y - hw - 2, Math.max(p.x, x1), p.y + hw + 2), D.light * (wide ? 0.75 : 0.65), { poise: 20, kind: 'spell', dir });
  tone(2200, 0.15, 0.05, 'square', 0.4); tone(440, 0.25, 0.05, 'sawtooth', 2); flashScreen = Math.max(flashScreen, 0.06);
  wfx({ life: 0.3, x0: p.x, x1, y: p.y, hw, draw() {
    const a = 1 - this.t / this.life, jit = Math.floor(this.t * 60) % 3 - 1, lo = Math.min(this.x0, this.x1), w = Math.abs(this.x1 - this.x0);
    g.save(); g.globalAlpha = a;
    g.fillStyle = 'rgba(255,70,200,0.8)'; g.fillRect(Math.round(lo), Math.round(this.y - this.hw + jit), Math.round(w), this.hw * 2);
    g.fillStyle = '#78fff8'; g.fillRect(Math.round(lo), Math.round(this.y - 1), Math.round(w), 2);
    g.fillStyle = '#ffffff'; g.fillRect(Math.round(lo), Math.round(this.y), Math.round(w), 1);
    for (let i = 0; i < 4; i++) { g.fillStyle = i % 2 ? '#ff46c8' : '#78fff8'; g.fillRect(Math.round(lo + rand(0, w)), Math.round(this.y + rand(-8, 8)), Math.round(rand(4, 14)), 1); }   // glitch slivers
    g.restore(); addLight(lo + w / 2, this.y, w / 2 + 20, '120,255,250', 0.7 * a);
  } });
}
function sig9Glitch(t, info) {   // the wound glitches: a corrupted copy of the blow lands a moment later
  if (t.prop || (t._glitchT || 0) > time) return;
  t._glitchT = time + 0.2;
  wfx({ life: 0.4, done: false, update() {
    if (this.t >= 0.22 && !this.done) { this.done = true; if (t.alive !== false) t.hit({ dmg: info.dmg * 0.35, poise: 6, dir: info.dir, kind: 'spell', x: info.x, y: info.y, quiet: true }); tone(1200 + rand(0, 800), 0.06, 0.04, 'square', 0.3); }
  }, draw() {
    const hb = t.hurtbox && t.hurtbox(); if (!hb) return;
    for (let i = 0; i < 3; i++) { g.fillStyle = (Math.floor(this.t * 40) + i) % 2 ? 'rgba(120,255,250,0.8)' : 'rgba(255,70,200,0.8)'; g.fillRect(Math.round(hb.x0 + rand(-6, 6)), Math.round(rand(hb.y0, hb.y1)), Math.round(hb.x1 - hb.x0), 1); }
  } });
}
function sig9Pyre(x, y, t, force) {   // a pyre of pale flame where the foe stood
  if (!force && t && (t._pyreT || 0) > time) return;
  if (t) t._pyreT = time + 1.0;
  const fy = wFloorBelow(x, y - 6); if (fy === null || solidAtPx(x, fy - 8)) return;
  while (sig9Pyres.length && (sig9Pyres[0].dead || sig9Pyres.length >= 5)) { const o = sig9Pyres.shift(); o.life = Math.min(o.life, o.t + 0.2); }
  const e = wfx({ life: 1.6, x, fy, tick: 0.1,
    update(dt) {
      if ((this.tick -= dt) <= 0) { this.tick = 0.35; wStrike(rect(this.x - 9, this.fy - 30, this.x + 9, this.fy + 1), D.light * 0.12, { quiet: true, kind: 'spell', fire: true }); }
      if (Math.random() < 0.3) particles.push({ x: this.x + rand(-5, 5), y: this.fy - rand(4, 26), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'mote' });
    },
    draw() { const a = Math.min(1, this.t / 0.12, (this.life - this.t) / 0.3); if (!wfxDraw('pyre', this.t, this.x, this.fy + 1, 1, { loop: true, alpha: a })) { g.fillStyle = `rgba(255,244,210,${0.6 * a})`; g.fillRect(this.x - 4, this.fy - 22, 8, 22); } addLight(this.x, this.fy - 14, 36, '255,244,210', 0.7 * a); } });
  sig9Pyres.push(e);
  tone(520, 0.3, 0.03, 'sine', 1.5);
}
// ---- v8 signature helpers
function sigInkGlyph(t, info) {
  if (t.prop || (t._glyphT || 0) > time) return;
  t._glyphT = time + 0.6;
  const ox = info.x - t.x, oy = info.y - t.y;
  wfx({ life: 1.05, fired: false, x: info.x, y: info.y,
    update() {
      if (!this.fired) { this.x = t.x + ox; this.y = t.y + oy; }
      if (this.t >= 0.62 && !this.fired) {
        this.fired = true;
        wStrike(rect(this.x - 14, this.y - 14, this.x + 14, this.y + 14), D.light * 0.45 * (1 + (D.spell - 1) * 0.6), { poise: 14, big: false });
        sfx.bolt(); noise(0.2, 700, 1, 0.2, 'lowpass');
        for (let i = 0; i < 10; i++) particles.push({ x: this.x, y: this.y, vx: rand(-80, 80), vy: rand(-90, 30), g: 200, life: rand(0.3, 0.6), kind: 'ink' });
      }
    },
    draw() {
      if (!this.fired) { const k = Math.min(1, this.t / 0.15); wfxDraw('glyph', this.t, this.x, this.y, 1, { center: true, loop: true, alpha: k }); addLight(this.x, this.y, 22, '170,120,240', 0.6); }
      else { wfxDraw('inkburst', this.t - 0.62, this.x, this.y, 1, { center: true }); addLight(this.x, this.y, 40, '170,120,240', 0.8); }
    } });
}
function sigInkBlots() {
  for (const d of [-1, 1]) for (let k = 0; k < 2; k++) {
    const b = wfx({ life: 1.4, x: P.x + d * 10, y: P.y - 20, vx: d * rand(90, 210), vy: -rand(110, 220), skip: new Set(), splat: -1,
      update(dt) {
        if (this.splat >= 0) return this.t - this.splat < 0.4;
        this.vy += 520 * dt; this.x += this.vx * dt; this.y += this.vy * dt;
        if (Math.random() < 0.5) particles.push({ x: this.x, y: this.y, vx: 0, vy: 0, life: 0.25, kind: 'ink' });
        const hit = wStrike(rect(this.x - 5, this.y - 5, this.x + 5, this.y + 5), D.light * 0.4, { skip: this.skip, poise: 10, dir: d });
        if (hit.length || solidAtPx(this.x, this.y)) { this.splat = this.t; sfx.hit(); wStrike(rect(this.x - 12, this.y - 12, this.x + 12, this.y + 8), D.light * 0.15, { skip: this.skip, quiet: true }); }
      },
      draw() {
        if (this.splat >= 0) wfxDraw('inkburst', (this.t - this.splat) * 1.4, this.x, this.y, 1, { center: true, alpha: 0.85 });
        else if (!wfxDraw('inkblot', this.t, this.x, this.y, this.vx > 0 ? 1 : -1, { center: true, loop: true })) { g.fillStyle = '#6a3ab0'; g.fillRect(Math.round(this.x) - 2, Math.round(this.y) - 2, 4, 4); }
        addLight(this.x, this.y, 16, '170,120,240', 0.5);
      } });
  }
}
function sigLavaCrack(charged) {
  const segs = [];
  for (let k = 0; k < 6; k++) {
    const x = P.x + P.face * (18 + k * 12), fy = wFloorBelow(x, P.y - 4);
    if (fy === null || Math.abs(fy - P.y) > 20) break;
    segs.push({ x, fy });
  }
  if (!segs.length) return;
  sfx.fire(); shake = Math.max(shake, 5);
  wfx({ life: 3.6, segs, face: P.face, tick: 0, charged,
    update(dt) {
      if ((this.tick -= dt) <= 0) {   // the seams keep burning whatever stands in them
        this.tick = 0.4; const skip = new Set();
        for (const s2 of this.segs) wStrike(rect(s2.x - 7, s2.fy - 18, s2.x + 7, s2.fy + 1), D.heavy * 0.18, { skip, fire: true, quiet: true, burn: [2, D.light * 0.2] });
      }
      if (this.charged) this.segs.forEach((s2, i) => {   // a fully charged blow: the seams erupt one after another
        const at = 0.12 + i * 0.07;
        if (!s2.erupted && this.t >= at) {
          s2.erupted = this.t; shake = Math.max(shake, 6); if (i % 2 === 0) sfx.boom();
          wStrike(rect(s2.x - 9, s2.fy - 44, s2.x + 9, s2.fy + 1), D.heavy * 1.0, { poise: 50, big: true, fire: true, kind: 'heavy', burn: [3, D.light * 0.3] });
          for (let q = 0; q < 10; q++) particles.push({ x: s2.x + rand(-5, 5), y: s2.fy - 4, vx: rand(-40, 40), vy: -rand(120, 260), g: 420, life: rand(0.5, 1.0), kind: 'fire' });
        }
      });
      if (Math.random() < 0.4) { const s2 = this.segs[irand(0, this.segs.length - 1)]; particles.push({ x: s2.x + rand(-6, 6), y: s2.fy - 1, vx: 0, vy: -rand(20, 50), life: 0.5, kind: 'ember' }); }
    },
    draw() {
      const fade = Math.min(1, (this.life - this.t) / 0.6);
      for (const s2 of this.segs) {
        if (!wfxDraw('lava', this.t + s2.x * 0.013, s2.x, s2.fy + 2, this.face, { loop: true, alpha: fade })) { g.fillStyle = `rgba(255,120,40,${fade})`; g.fillRect(s2.x - 6, s2.fy - 1, 12, 2); }
        addLight(s2.x, s2.fy - 4, 26, '255,130,50', 0.7 * fade);
        if (s2.erupted) wfxDraw('erupt', this.t - s2.erupted, s2.x, s2.fy + 1, this.face);
      }
    } });
}
function sigFrontTarget(x, y, range, dirFace = P.face) {
  let best = null, bd = 1e9;
  for (const t of targets()) {
    if (t.prop) continue; const hb = t.hurtbox(); if (!hb) continue;
    const cx = (hb.x0 + hb.x1) / 2, dx = (cx - x) * dirFace;
    if (dx < -10 || dx > range || Math.abs((hb.y0 + hb.y1) / 2 - y) > 60) continue;
    if (dx < bd) { bd = dx; best = t; }
  }
  return best;
}
function sigChain(p) {
  const hops = [], seen = new Set(); let from = p, t = sigFrontTarget(p.x, p.y, 110);
  while (t && hops.length < 3) {
    seen.add(t); const hb = t.hurtbox(), c = { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2 };
    hops.push({ t, from, to: c }); from = c;
    let nb = null, nd = 90;
    for (const q of targets()) { if (q.prop || seen.has(q)) continue; const h2 = q.hurtbox(); if (!h2) continue; const d = Math.hypot((h2.x0 + h2.x1) / 2 - c.x, (h2.y0 + h2.y1) / 2 - c.y); if (d < nd) { nd = d; nb = q; } }
    t = nb;
  }
  if (!hops.length) { wZap(p.x, p.y, p.x + P.face * 40, p.y + rand(-8, 8), 0.12); noise(0.1, 3500, 2, 0.1, 'highpass'); return; }
  wfx({ life: 0.1 + hops.length * 0.08, i: 0,
    update() {
      while (this.i < hops.length && this.t >= this.i * 0.08) {
        const h = hops[this.i++]; wZap(h.from.x, h.from.y, h.to.x, h.to.y, 0.2);
        if (h.t.alive !== false) h.t.hit({ dmg: D.light * 0.8 * (this.i === 1 ? 1 : 0.75), poise: 15, dir: P.face, kind: 'spell', x: h.to.x, y: h.to.y, big: this.i === 1 });
        noise(0.12, 3000, 2, 0.16, 'highpass'); tone(1800, 0.08, 0.04, 'square', 0.5);
      }
    } });
}
function sigSkyBolt() {
  const t = sigFrontTarget(P.x, P.y - 16, 150);
  let x = P.x + P.face * 70;
  if (t) { const hb = t.hurtbox(); x = (hb.x0 + hb.x1) / 2; }
  const fy = wFloorBelow(x, P.y - 8) ?? P.y;
  sfx.charge();
  wfx({ life: 0.85, x, fy, struck: false,
    update() {
      if (!this.struck && this.t >= 0.3) {
        this.struck = true; flashScreen = Math.max(flashScreen, 0.25); shake = Math.max(shake, 7);
        noise(0.7, 900, 0.7, 0.6, 'lowpass', 0.4); noise(0.25, 5000, 2, 0.3, 'highpass'); tone(60, 0.5, 0.3, 'sawtooth', 0.5);
        const hit = wStrike(rect(this.x - 18, this.fy - 90, this.x + 18, this.fy + 2), D.heavy * 0.9, { poise: 60, big: true, kind: 'heavy' });
        if (hit.length) sigChain({ x: this.x, y: this.fy - 20 });
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
const sigSmallFoe = t => !t.prop && !t.boss && !(t.cfg && t.cfg.elite);
function sigGust(p) {
  tone(300, 0.2, 0.03, 'sine', 1.8); noise(0.2, 1500, 0.7, 0.12, 'bandpass', 0.5);
  wfx({ life: 0.34, x: p.x, y: p.y, face: P.face, skip: new Set(),
    update(dt) {
      this.x += this.face * 260 * dt;
      if (solidAtPx(this.x + this.face * 6, this.y)) return false;
      for (const t of wStrike(rect(this.x - 10, this.y - 12, this.x + 10, this.y + 12), D.light * 0.35, { skip: this.skip, poise: 10, dir: this.face })) if (sigSmallFoe(t) && t.vx !== undefined) t.vx += this.face * 140;
    },
    draw() { if (!wfxDraw('gust', this.t, this.x, this.y, this.face, { center: true, alpha: 1 - this.t / this.life })) { g.fillStyle = 'rgba(210,250,240,0.5)'; g.fillRect(this.x - 6, this.y - 1, 12, 2); } } });
}
function sigWhirlwind() {
  const x0 = P.x + P.face * 22, fy = wFloorBelow(x0, P.y - 8) ?? P.y;
  noise(1.2, 700, 0.6, 0.3, 'bandpass', 1.6); tone(180, 0.8, 0.05, 'sine', 1.6);
  wfx({ life: 2.4, x: x0, fy, face: P.face, tick: 0,
    update(dt) {
      if (!solidAtPx(this.x + this.face * 12, this.fy - 8)) this.x += this.face * 70 * dt;
      if ((this.tick -= dt) <= 0) { this.tick = 0.4; wStrike(rect(this.x - 14, this.fy - 44, this.x + 14, this.fy), D.light * 0.2, { poise: 8, dir: this.face, quiet: this.t > 0.05 }); }
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
  const snap = { f: P.anim.frame, x: P.x, y: P.y, face: P.face };
  wfx({ life: 0.55, draw() {
    if (this.t < 0.16) return;
    const a = 0.55 * (1 - (this.t - 0.16) / 0.39);
    drawSprite(sheet('player'), snap.f, snap.x, snap.y, snap.face, { flash: 1, flashColor: '#ffb050', alpha: a });
    const ws = sheet('wpn_first_ember'); if (ws.ok) drawSprite(ws, snap.f, snap.x, snap.y, snap.face, { flash: 1, flashColor: '#fff0c0', alpha: a });
    addLight(snap.x + snap.face * 14, snap.y - 18, 40, '255,180,90', a);
  } });
}
// Twinborne: a stoked blade smoulders between blows
HOOKS.update.push(() => {
  if (!P || SAVE.weapon !== 'twinborne' || !(P.sigCharge > 0)) return;
  if (Math.random() < 0.2 * P.sigCharge) particles.push({ x: P.x + P.face * rand(6, 18), y: P.y - rand(14, 28), vx: 0, vy: -rand(15, 40), life: 0.4, kind: 'fire' });
});
// bosses are big: give the player's blows a little more to hit
function hbOf(t) { const hb = t.hurtbox(); if (!hb || !t.boss) return hb; return rect(hb.x0 - 8, hb.y0 - 6, hb.x1 + 8, hb.y1); }
