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
      const n = A.kind === 'heavy' ? 3 : 1;
      for (let k = 0; k < n; k++) projectiles.push({ owner: 'player', kind: 'sunspear', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 16, y: P.y - 20 + (k - (n - 1) / 2) * 7,
        vx: P.face * (330 + k * 20), vy: (k - (n - 1) / 2) * 25, dmg: D.light * 0.9, life: 1.0, r: 6, pierce: true, sh: 'fx_light_spear' });
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
        t.hit({ dmg: info.dmg * 0.45, poise: (info.poise || 0) * 0.35, dir: info.dir, kind: 'light', x: info.x, y: info.y, fire: true, melee: true });
        spawnFx(fxOr('embers', 'hit'), info.x, info.y, info.dir); tone(740, 0.2, 0.04, 'triangle', 0.8);
        for (let i = 0; i < 8; i++) particles.push({ x: info.x, y: info.y, vx: rand(-60, 60), vy: -rand(20, 90), g: 100, life: rand(0.3, 0.6), kind: 'ember' });
      } });
    } },
};
// ---- v8 signature helpers
function sigInkGlyph(t, info) {
  if (t.prop || (t._glyphT || 0) > time) return;
  t._glyphT = time + 0.3;
  const ox = info.x - t.x, oy = info.y - t.y;
  wfx({ life: 1.05, fired: false, x: info.x, y: info.y,
    update() {
      if (!this.fired) { this.x = t.x + ox; this.y = t.y + oy; }
      if (this.t >= 0.62 && !this.fired) {
        this.fired = true;
        wStrike(rect(this.x - 14, this.y - 14, this.x + 14, this.y + 14), D.light * 0.55 * (1 + (D.spell - 1) * 0.6), { poise: 14, big: false });
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
  for (const d of [-1, 1]) for (let k = 0; k < 3; k++) {
    const b = wfx({ life: 1.4, x: P.x + d * 10, y: P.y - 20, vx: d * rand(90, 210), vy: -rand(110, 220), skip: new Set(), splat: -1,
      update(dt) {
        if (this.splat >= 0) return this.t - this.splat < 0.4;
        this.vy += 520 * dt; this.x += this.vx * dt; this.y += this.vy * dt;
        if (Math.random() < 0.5) particles.push({ x: this.x, y: this.y, vx: 0, vy: 0, life: 0.25, kind: 'ink' });
        const hit = wStrike(rect(this.x - 5, this.y - 5, this.x + 5, this.y + 5), D.light * 0.6, { skip: this.skip, poise: 10, dir: d });
        if (hit.length || solidAtPx(this.x, this.y)) { this.splat = this.t; sfx.hit(); wStrike(rect(this.x - 12, this.y - 12, this.x + 12, this.y + 8), D.light * 0.3, { skip: this.skip, quiet: true }); }
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
        const hit = wStrike(rect(this.x - 18, this.fy - 90, this.x + 18, this.fy + 2), D.heavy * 1.5, { poise: 60, big: true, kind: 'heavy' });
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
      if ((this.tick -= dt) <= 0) { this.tick = 0.3; wStrike(rect(this.x - 14, this.fy - 44, this.x + 14, this.fy), D.light * 0.3, { poise: 8, dir: this.face, quiet: this.t > 0.05 }); }
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
