// ------------------------------------------------------------------ X: secrets & mini-bosses
// The Hermit's Hollow + Oswin (behind R1's golden seal), the Hollow Champion gauntlet (R4), the Gilded Sentinel
// pair (X3), Ember's Hollow + the First Ember (beneath X4's cracked floor) and the true epilogue.
// Rooms: tools/regions/50_secrets.py. Art: art/gen_secrets*.py. Contract: docs/EXPANSION_CONTRACT.md.

// ================================================================== biomes
Object.assign(AREAS, {
  hermit: { name: 'The Hermit’s Hollow', ambient: 0.56, amb: 'dust', tint: '#0e0b0c', map: '#6e5c46' },
  ember: { name: 'Ember’s Hollow', ambient: 0.38, amb: 'ember', tint: '#0c0607', map: '#7a3322' },
});
Object.assign(SCALES, { hermit: [0, 2, 5, 7, 9], ember: [0, 1, 4, 6, 7] });
Object.assign(ROOTS, { hermit: 49, ember: 41.2 });

const SC_SEAL_T = 25, SC_GAP_T = 26;
const scSealBroken = () => !!(SAVE && SAVE.flags && SAVE.flags['sc:seal']);
function scSyncSeal() {   // the seal tile is solid until the flag is set (neighbouring rooms read the same id)
  const want = !scSealBroken();
  if (want === SOLID_EXT.has(SC_SEAL_T)) return false;
  if (want) SOLID_EXT.add(SC_SEAL_T); else SOLID_EXT.delete(SC_SEAL_T);
  return true;
}
function scMask(R, x, y) {
  const air = (xx, yy) => !isSolidT(tileAtR(R, xx, yy));
  return (air(x, y - 1) ? 1 : 0) | (air(x + 1, y) ? 2 : 0) | (air(x, y + 1) ? 4 : 0) | (air(x - 1, y) ? 8 : 0);
}
// '$' — the golden seal: ordinary cliff rock until broken, then an open cave mouth
registerTile('$', SC_SEAL_T, { solid: true, draw(ctx, sh, px, py, x, y, R, back) {
  if (!scSealBroken()) { drawTile(ctx, sh, scMask(R, x, y) & (x === 0 ? ~8 : 15), px, py); return; }
  const hs = sheet('tiles_hermit');
  drawTile(back, hs.ok ? hs : sh, 38 + ((x + y) & 1), px, py, 1);
  back.fillStyle = 'rgba(6,4,6,0.55)'; back.fillRect(px, py, 16, 16);
} });
// '&' — a gap in a cave's back wall: the back layer is cleared so the parallax (the Pale Root) shows through
registerTile('&', SC_GAP_T, { draw(ctx, sh, px, py, x, y, R, back) { back.clearRect(px, py, 16, 16); } });

// ================================================================== small shared helpers
const scBossDmg = (d, b) => BOSS_DMG * d * NGP.dmg * (b && b.phase === 2 ? 1.1 : 1) * ((b && b.dmgK) || 1);
function scAsh(x, y, n = 16, kind = 'ash', spd = 60) { for (let i = 0; i < n; i++) particles.push({ x: x + rand(-8, 8), y: y - rand(0, 24), vx: rand(-spd, spd), vy: -rand(20, spd * 1.4), g: 60, life: rand(0.6, 1.4), kind }); }
function scDrawTall(sh, frame, x, top, bottom, alpha) {   // stack a sprite column from top to bottom (fog walls)
  if (!sh.ok) { g.fillStyle = `rgba(255,210,130,${0.25 * alpha})`; g.fillRect(x - 8, top, 16, bottom - top); return; }
  for (let yy = bottom; yy > top + 1; yy -= sh.fh) drawSprite(sh, frame, x, yy, 1, { bottom: true, alpha });
}
function scPrompt(p, label) {   // "E  label" bubble above the player (screen space, hud hook)
  const sx = P.x - cam.x, sy = P.y - cam.y - 38, tw = textW('E  ' + label, 6.5) + 10;
  box(sx - tw / 2, sy - 8, tw, 11, 0.7);
  text('E', sx - tw / 2 + 5, sy, 6.5, '#e6c77a', 'left'); text(label, sx - tw / 2 + 13, sy, 6.5, '#e8dcc0', 'left', { weight: 500 });
}
function scNear(p, dx = 18, dy = 26) { return Math.abs(p.x - P.x) < dx && Math.abs(p.y - P.y) < dy; }
function scSimpleProp(type, name, x, y, tag, extra = {}) {
  const sh = sheet(name);
  const p = { type, x, y, face: 1, sh, anim: new Anim(sh, sh.has(tag) ? tag : Object.keys(sh.tags)[0] || tag, true), ...extra };
  return p;
}

// ================================================================== R1: the golden seal (a fully charged heavy breaks it)
SPAWNS.sc_seal = (s, c) => {
  if (scSealBroken()) return;
  const x0 = 0, x1 = 2 * TILE, y0 = 8 * TILE, y1 = 11 * TILE;
  const p = scSimpleProp('sc_seal', 'sc_seal', TILE, y1, 'idle', { hintT: 0, flare: 0 });
  p.hurtbox = () => p.broken ? null : rect(x0 + 10, y0 + 2, x1 + 3, y1 - 2);
  p.onHit = info => {
    if (p.broken) return;
    if (info.kind === 'heavy' && info.charged) return scBreakSeal(p);
    // everything else rings off the stone
    sfx.block(); tone(740, 0.5, 0.05, 'sine', 0.98); tone(1110, 0.4, 0.03, 'triangle');
    spawnFx(fxOr('parry_spark', 'hit'), clamp(info.x, x0 + 16, x1 + 2), clamp(info.y, y0 + 4, y1 - 4), -1);
    for (let i = 0; i < 6; i++) particles.push({ x: x1, y: clamp(info.y, y0, y1), vx: rand(20, 90), vy: -rand(20, 80), g: 300, life: 0.5, kind: 'gold' });
    p.flare = 1; if (p.sh.has('flare')) p.anim.set('flare', false);
    if (info.melee) { P.vx = 90; hitstop = Math.max(hitstop, 0.05); }
    if (time - p.hintT > 3) { p.hintT = time; toast('The stone hums. A heavier blow might break it.', 3); }
  };
  p.update = dt => {
    p.flare = Math.max(0, p.flare - dt * 2.5);
    if (p.anim.tag === 'flare' && p.anim.done) p.anim.set('idle', true);
    if (p.broken) { if (p.anim.done) p.taken = true; return; }
    const pulse = 0.35 + 0.2 * Math.sin(time * 1.7) + p.flare * 0.8;
    addLight(x1 - 6, (y0 + y1) / 2, 26 + 20 * p.flare, '255,210,120', pulse);
    if (Math.random() < 0.04 + p.flare * 0.3) particles.push({ x: x1 - rand(0, 6), y: rand(y0 + 6, y1 - 6), vx: rand(2, 10), vy: -rand(4, 14), life: 1.2, kind: 'mote' });
  };
  p.draw = () => { drawSprite(p.sh, p.anim.frame, p.x, p.y, 1, { bottom: true, alpha: p.broken ? 1 : 0.55 + 0.25 * Math.sin(time * 1.7) + 0.2 * p.flare }); };
  props.push(p);
};
function scBreakSeal(p) {
  p.broken = true; SAVE.flags['sc:seal'] = 1; scSyncSeal();
  if (p.sh.has('shatter')) p.anim.set('shatter', false); else p.taken = true;
  renderRoomLayers(room);
  sfx.crumble(); sfx.boom(); sfx.glint(); [392, 523, 659, 784].forEach((f, i) => tone(f, 1.6, 0.06, 'sine', 1, 0.1 + i * 0.09));
  shake = 9; hitstop = 0.16; flashScreen = 0.35;
  for (let i = 0; i < 26; i++) particles.push({ x: rand(4, 30), y: rand(8 * TILE, 11 * TILE), vx: rand(20, 140), vy: -rand(20, 150), g: 420, life: rand(0.6, 1.3), kind: Math.random() < 0.6 ? 'rock' : 'gold' });
  toast('The seal shatters. Warm air breathes out of the rock.', 4);
  saveGame();
}

// ================================================================== the Hermit's Hollow: campfire, prayer flags, mat, cairn
SPAWNS.sc_fire = (s, c) => {
  const p = scSimpleProp('sc_fire', 'sc_campfire', c.cx, c.fy, 'loop');
  p.update = () => {
    addLight(p.x, p.y - 12, 120 + Math.sin(time * 9) * 5 + Math.sin(time * 23) * 3, '255,160,80', 1, LX_FLICKER);
    if (Math.random() < 0.35) particles.push({ x: p.x + rand(-5, 5), y: p.y - rand(8, 16), vx: rand(-6, 6), vy: -rand(20, 50), life: rand(0.4, 1.0), kind: 'fire' });
    if (Math.random() < 0.08) particles.push({ x: p.x + rand(-3, 3), y: p.y - 20, vx: rand(-4, 4), vy: -rand(10, 20), life: 2, kind: 'ash' });
  };
  props.push(p);
};
const SC_FLAG_COLS = ['#6e2a24', '#8a6a2c', '#3e4a5a', '#b8ac92', '#4a5a3c'];
SPAWNS.sc_flags = (s, c) => {
  const x0 = s.x * TILE + 8, x1 = (s.x1 || s.x + 10) * TILE + 8, y = s.y * TILE + 4;
  props.push({ type: 'sc_flags', x: (x0 + x1) / 2, y, face: 1, anim: { update() {} }, draw() {
    const n = Math.floor((x1 - x0) / 9);
    g.fillStyle = '#2a2220';
    for (let i = 0; i <= 64; i++) { const t = i / 64; g.fillRect(Math.round(lerp(x0, x1, t)), Math.round(y + Math.sin(t * Math.PI) * 14), 1, 1); }
    for (let k = 1; k < n; k++) {
      const t = k / n, fx0 = Math.round(lerp(x0, x1, t)), fy0 = Math.round(y + Math.sin(t * Math.PI) * 14) + 1;
      const sway = Math.sin(time * 1.6 + k * 0.9) * 1.2;
      g.fillStyle = SC_FLAG_COLS[k % SC_FLAG_COLS.length];
      for (let j = 0; j < 7; j++) { const w = j < 5 ? 5 : 4 - (j - 5) * 2; g.fillRect(Math.round(fx0 - 2 + sway * j / 7), fy0 + j, Math.max(1, w), 1); }
      g.fillStyle = 'rgba(10,6,8,0.35)'; g.fillRect(Math.round(fx0 + 1 + sway * 0.5), fy0 + 1, 1, 5);
    }
  } });
};
SPAWNS.sc_mat = (s, c) => props.push(scSimpleProp('sc_mat', 'sc_mat', c.cx, c.fy, 'idle', { update() { if (Math.random() < 0.05) particles.push({ x: this.x + 9, y: this.y - 8, vx: rand(-2, 2), vy: -rand(6, 12), life: 2.2, kind: 'dust' }); } }));
SPAWNS.sc_cairn = (s, c) => props.push(scSimpleProp('sc_cairn', 'sc_cairn', c.cx, c.fy, 'idle'));
SPAWNS.sc_ashes = (s, c) => {
  const p = scSimpleProp('sc_ashes', 'sc_ashes', c.cx, c.fy, 'loop');
  p.update = () => { addLight(p.x, p.y - 4, 40, '255,110,50', 0.6 + 0.2 * Math.sin(time * 2)); if (Math.random() < 0.15) particles.push({ x: p.x + rand(-14, 14), y: p.y - 3, vx: rand(-3, 3), vy: -rand(8, 24), life: 1.2, kind: 'ember' }); };
  props.push(p);
};

// ================================================================== fog walls (boss / gauntlet arenas)
const SC_GAUNT = { active: false, wave: 0, t: 0, spawned: [], champ: false };
SPAWNS.sc_fog = (s, c) => {
  if (SAVE.flags['boss:' + s.kind]) return;
  const x = s.x * TILE + 8, top = (s.top || 0) * TILE, fy = c.fy;
  const on = () => boss && boss.kind === s.kind && boss.alive && (boss.active || (s.gauntlet && SC_GAUNT.active));
  const sh = sheet('prop_fog');
  const p = { type: 'sc_fog', x, y: fy, face: 1, sh, anim: new Anim(sh, 'loop', true), on,
    update() { if (on()) { addLight(x, fy - 40, 50, '255,210,130', 0.6); if (Math.random() < 0.1) particles.push({ x: x + rand(-6, 6), y: rand(top, fy), vx: 0, vy: -rand(5, 15), life: 1, kind: 'mote' }); } },
    draw() { if (on()) scDrawTall(sh, p.anim.frame, x, top, fy, 0.8); } };
  props.push(p);
  room.dyn.push({ x0: x - 8, x1: x + 8, y0: top - 400, y1: fy, on });
};

// ================================================================== Oswin, the Ashen Pilgrim (level-scaled, secret)
BOSS_INFO.oswin = { name: 'Oswin, the Ashen Pilgrim', hp: 1500, cinders: 4000, reward: ['w:windstaff', 'c_bead', 'sp:wind_ward'], quote: '“Few find this place. Fewer leave it.”' };
function scWhirl(b, x, dir, dmg) {
  projectiles.push({ owner: 'enemy', kind: 'sc_whirl', x, y: b.floor - 14, vx: dir * 135, vy: 0, dmg: scBossDmg(dmg, b), life: 2.4, r: 9, t: 0, id: ++hazardId, sh: 'fx_sc_whirl', face: dir });
}
class Oswin extends MetaBoss {
  // stay inside the fog-walled arena (west wall .. the golden fog at column 27): vaults and dashes can never leave it
  get L() { return TILE + 22; }
  get R() { return 27 * TILE - 22; }
  constructor(x, y) {
    super('oswin', x, y, {
      sheets: ['oswin', 'oswin_p2'], stanceMax: 240, walkSpeed: 52, prefer: 52, p2at: 0.5, p2speed: 1.15, p2tag: 'spin', critRange: 44,
      introTag: 'rise', cool1: [0.55, 1.1], cool2: [0.35, 0.8], victory: 'THE PILGRIM RESTS', deathParticle: 'ash',
      weights(d, p2) {
        if (d < 64) return { combo: 3, spin: p2 ? 1.8 : 1.2, counter: 1.1, backstep: 0.7, vault: 0.35 };
        if (d < 150) return { vault: 2, combo: 1, dash: p2 ? 2.2 : 0, walk: 1, spin: p2 ? 0.8 : 0.2 };
        return { vault: 1.6, dash: p2 ? 2.4 : 0, walk: 2.2 };
      },
      chains: { combo(d) { return d < 72 ? (this.phase === 2 ? 'dash' : 'spin') : 'vault'; }, vault: 'combo', backstep(d) { return this.phase === 2 ? 'dash' : 'vault'; },
                riposte: 'spin', dash: 'combo', spin: d => d < 60 ? 'combo' : null },
      moves: {
        combo: { dmg: [26, 26, 34], parry: true, step: 70, fx: null },
        spin: { dmg: [36], shake: 3, on: {} },
        vault: { dmg: [42], parry: true, leap: 2, height: 58, over: true },
        riposte: { dmg: [46], parry: true, step: 160 },
        dash: { dmg: [40], body: true },
      },
      wake() { return P.x < 25 * TILE && P.ground; },
      onIntro() { this.facePlayer(); },
      ambient(dt) {
        addLight(this.x, this.y - 30, 56, this.phase === 2 ? '220,225,235' : '255,190,120', 0.55);
        if (this.phase === 2 && Math.random() < 0.5) particles.push({ x: this.x + rand(-22, 22), y: this.y - rand(8, 44), vx: this.face * -rand(10, 40), vy: -rand(4, 20), life: 0.8, kind: 'ash' });
      },
      onPhase2() { flashScreen = 0.4; shake = 6; sfx.howl(); toast('Ash-wind wraps the pilgrim’s staff.'); },
      onDeath() { victoryBanner = { text: 'THE PILGRIM RESTS', t: 0 }; setTimeout(() => toast('“Walk on, ember. Mind the ash.”', 4), 2200); },
    });
    const L = levelOf(SAVE.stats), k = 0.8 + 0.035 * (L - 1);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.oswin.hp * k * NGP.hp);
    this.dmgK = clamp(0.72 + 0.022 * (L - 1), 0.72, 1.7);
    this.level = L;
    for (const M of Object.values(this.moves)) if (M.dmg) M.dmg = M.dmg.map(v => v * this.dmgK);
    const self = this;
    this.moves.spin.on = { 4() { if (self.phase === 2) { for (const dd of [-1, 1]) scWhirl(self, self.x + dd * 22, dd, 26); sfx.howl(); } } };
    this.face = -1; this.anim.set(this.sh.has('sit') ? 'sit' : 'idle', true);
  }
  start(m) {
    if (m === 'lance' || m === 'thrust') m = this.phase === 2 ? 'dash' : 'vault';
    if (m === 'counter') { this.facePlayer(); this.last = m; this.atk = m; this.state = 'counter'; this.anim.set(this.sh.has('counter') ? 'counter' : 'idle', true); this.t = rand(1.0, 1.5); spawnFx('telegraph', this.x + this.face * 14, this.y - 34, this.face); sfx.glint(); return; }
    super.start(m);
    if (m === 'dash') { this.dash = null; }
  }
  update(dt) {
    if (!this.active) {
      this.commonUpdate(dt); this.anim.update(dt);
      if (!this.cutting) { this.face = -1; if (this.wake()) this.activate(); }
      this.ambient(dt); return;
    }
    if (this.state === 'counter' && this.introT <= 0) {
      this.commonUpdate(dt); this.anim.update(dt); this.facePlayer(); this.t -= dt;
      if (Math.random() < 0.4) particles.push({ x: this.x + this.face * rand(6, 20), y: this.y - rand(18, 32), vx: 0, vy: -rand(4, 12), life: 0.4, kind: 'mote' });
      addLight(this.x + this.face * 12, this.y - 26, 30, '240,240,255', 0.4 + 0.2 * Math.sin(time * 14));
      if (this.t <= 0) this.start(Math.abs(P.x - this.x) < 70 ? 'combo' : 'vault');
      if (this.phase === 1 && this.hp <= this.maxHp * this.p2at) { this.enterPhase2(); }
      this.ambient(dt); this.x = clamp(this.x, this.L, this.R); return;
    }
    super.update(dt);
  }
  hit(info) {
    if (this.state === 'counter' && this.active && !info.crit && info.melee) {
      // the counter-stance: the staff turns the blow aside and answers at once
      sfx.parry(); hitstop = 0.14; shake = 4;
      spawnFx(fxOr('parry_flash', 'parry_spark'), info.x, info.y, -info.dir);
      for (let i = 0; i < 10; i++) particles.push({ x: info.x, y: info.y, vx: -info.dir * rand(20, 120), vy: -rand(20, 90), g: 300, life: 0.5, kind: 'spark' });
      if (P.state !== 'dead') { setP('hurt', 'hurt'); P.vx = -P.face * 150; P.st = Math.max(0, P.st - 18); P.combo = 0; }
      this.start('riposte'); return;
    }
    super.hit(info);
  }
  updateAttack(dt) {
    const a = this.atk, an = this.anim;
    if (a === 'vault') { const f = this.firstActive; this.firstActive = 2; super.updateAttack(dt); if (this.atk === 'vault') this.firstActive = f; return; }
    if (a === 'dash') {
      const wins = metaWindows(this.sh, 'dash'), w = wins[0] || { active: [3, 5] };
      if (an.i < w.active[0]) this.facePlayer();
      if (an.i >= w.active[0] && an.i <= w.active[1]) {
        if (!this.dash) { this.dash = { to: clamp(P.x + this.face * 80, this.L + 10, this.R - 10) }; sfx.bossSwing(); spawnFx(fxOr('sc_gust', 'dust'), this.x, this.y - 20, this.face); }
        this.x = approach(this.x, this.dash.to, 560 * dt);
        if (Math.random() < 0.9) particles.push({ x: this.x - this.face * rand(4, 20), y: this.y - rand(4, 40), vx: -this.face * rand(30, 90), vy: -rand(0, 20), life: 0.5, kind: 'ash' });
      }
    }
    super.updateAttack(dt);
    if (a === 'dash' && this.state !== 'attack') this.dash = null;
  }
  updateLeap(dt, M) {
    if (!M.over) return super.updateLeap(dt, M);
    const an = this.anim, wins = metaWindows(this.sh, this.atk), land = wins.length ? wins[0].active[0] - 1 : an.n - 4;
    if (an.changed && an.i === M.leap && !this.air) {
      let T = 0; for (let i = an.i; i < land; i++) T += an.ms(i); T = Math.max(0.25, T / 1000 / an.speed);
      const over = P.x + this.face * 64;
      this.air = { x0: this.x, tx: clamp(over, this.L + 20, this.R - 20), t: 0, T };
      if (Math.abs(this.air.tx - P.x) < 30) this.air.tx = clamp(P.x - this.face * 56, this.L + 20, this.R - 20);   // cornered: land in front instead
      sfx.jump(); spawnFx('dust', this.x, this.floor, this.face);
    }
    if (this.air) {
      this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
      this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * (M.height || 60);
      if (Math.random() < 0.5) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(10, 30), vx: 0, vy: rand(-10, 10), life: 0.4, kind: this.phase === 2 ? 'ash' : 'dust' });
      if (k >= 1) { this.air = null; this.y = this.floor; this.facePlayer(); shake = 4; sfx.land(); spawnFx('dust', this.x, this.floor, this.face); }
    }
  }
}
BOSS_SPAWN.oswin = (cx, fy) => new Oswin(cx, fy);

// ================================================================== the Hollow Champion (R4 gauntlet)
BOSS_INFO.champion = { name: 'The Hollow Champion', hp: 1600, cinders: 5200, reward: ['w:twinfangs', 'shard'], quote: 'Undefeated. Unburied. Unwilling to yield.' };
function scSlashWave(b, dir, dmg) {
  projectiles.push({ owner: 'enemy', kind: 'sc_cslash', x: b.x + dir * 24, y: b.floor - 18, vx: dir * 210, vy: 0, dmg: scBossDmg(dmg, b), life: 1.3, r: 10, t: 0, id: ++hazardId, sh: 'fx_sc_cslash', face: dir });
}
class Champion extends MetaBoss {
  constructor(x, y) {
    super('champion', x, y, {
      sheets: ['champion', 'champion_p2'], stanceMax: 300, walkSpeed: 62, prefer: 50, p2at: 0.5, p2speed: 1.2, p2tag: 'whirl', critRange: 46,
      introTag: 'salute', cool1: [0.6, 1.2], cool2: [0.35, 0.85], victory: 'CHAMPION UNCROWNED', deathParticle: 'ash',
      weights(d, p2) {
        if (d < 64) return { flurry: 3, whirl: p2 ? 1.8 : 1.1, backstep: 1, cross: 0.5 };
        if (d < 170) return { cross: 2.4, leap: 1.4, walk: 1, whirl: p2 ? 1 : 0.3 };
        return { leap: 2.4, cross: 1.2, walk: 2 };
      },
      chains: { flurry(d) { return d < 80 ? 'whirl' : 'cross'; }, cross: 'flurry', backstep: 'cross', leap: 'flurry', whirl: d => d < 70 ? 'flurry' : 'cross' },
      moves: {
        flurry: { dmg: [22, 22, 24, 34], parry: true, step: 80 },
        cross: { dmg: [46], parry: true, step: 300, on: {} },
        whirl: { dmg: [26, 30], body: true, step: 120 },
        leap: { dmg: [50], leap: 2, height: 88, onLand() { if (this.phase === 2) for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.floor, vx: dd * 170, w: 12, h: 12, dmg: scBossDmg(26, this), id: ++hazardId, life: 1.0, wave: true, dir: dd, color: 'root' }); } },
      },
      wake() { return this.called && P.ground; },
      onIntro() { this.shown = true; this.y = this.floor; shake = 8; sfx.boom(); spawnFx('shockwave', this.x, this.floor, 1); scAsh(this.x, this.floor, 20, 'dust', 80); this.facePlayer(); },
      ambient(dt) {
        if (!this.shown) return;
        addLight(this.x, this.y - 30, 50, this.phase === 2 ? '255,140,70' : '230,210,170', 0.5);
        if (this.phase === 2 && Math.random() < 0.35) particles.push({ x: this.x + this.face * rand(-20, 24), y: this.y - rand(10, 40), vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'fire' });
      },
      onPhase2() { flashScreen = 0.3; shake = 6; sfx.roar(); toast('The Champion’s blades catch fire.'); },
      onDeath() { victoryBanner = { text: 'CHAMPION UNCROWNED', t: 0 }; SC_GAUNT.active = false; },
    });
    const self = this;
    this.moves.cross.on = { 5() { if (self.phase === 2) scSlashWave(self, self.face, 30); } };
    this.shown = false; this.called = false;
  }
  update(dt) {
    if (!this.active) { this.commonUpdate(dt); this.anim.update(dt); if (!this.cutting && this.wake()) this.activate(); return; }
    super.update(dt);
  }
  draw() { if (this.shown) super.draw(); }
}
BOSS_SPAWN.champion = (cx, fy) => new Champion(cx, fy);

// ---- the challenger's banner + waves
const SC_WAVES = [
  [['hollow_soldier', 12], ['hollow_soldier', 24], ['hollow_soldier', 33]],
  [['hollow_soldier', 13], ['shield_warden', 30], ['hollow_archer', 17, 6], ['hollow_soldier', 35]],
  [['grave_knight', 29], ['hollow_soldier', 12], ['hollow_archer', 29, 7], ['rot_crawler', 22]],
];
SPAWNS.sc_banner = (s, c) => {
  Object.assign(SC_GAUNT, { active: false, wave: 0, t: 0, spawned: [], champ: false });
  const done = !!SAVE.flags['boss:champion'];
  const p = scSimpleProp('sc_banner', 'sc_banner', c.cx, c.fy, done ? 'spent' : 'idle', { interactable: !done });
  p.update = () => {
    if (p.anim.tag === 'ring' && p.anim.done) p.anim.set('idle', true);
    if (!SAVE.flags['boss:champion']) addLight(p.x, p.y - 44, 30, '255,200,120', 0.35);
  };
  props.push(p); SC_GAUNT.banner = p;
};
function scStartGauntlet(p) {
  if (SAVE.flags['boss:champion']) { toast('The banner hangs still. None are left to answer.'); return; }
  if (!boss || boss.kind !== 'champion') return;
  Object.assign(SC_GAUNT, { active: true, wave: 0, t: 1.6, spawned: [], champ: false });
  if (p.sh.has('ring')) p.anim.set('ring', false);
  [220, 277, 330].forEach((f, i) => tone(f, 2.6, 0.12, 'sine', 1, i * 0.04)); tone(110, 3, 0.15, 'triangle');
  shake = 5; flashScreen = 0.2; sfx.roar();
  // the summit's own hollow step back into the ash to watch: the gauntlet is fought alone (they return later)
  for (const e of enemies) if (e.alive && !/gauntlet/.test(e.key)) { e.gone = true; spawnFx(fxOr('death_ash', 'dust'), e.x, e.y, 1); }
  toast('You sound the challenge. The hollow answer.', 3.5);
}
function scSpawnWave(k) {
  SC_GAUNT.spawned = [];
  SC_WAVES[k].forEach(([type, tx, ty], i) => {
    const x = tx * TILE + 8, y = ((ty ?? 10) + 1) * TILE;
    const e = makeEnemy(type, x, y, `R4:gauntlet:${k}:${i}:${Math.floor(time * 10)}`);
    e.aggro = true; e.cool = 0.9 + i * 0.25; e.face = P.x < x ? -1 : 1;
    enemies.push(e); SC_GAUNT.spawned.push(e);
    spawnFx(fxOr('death_ash', 'dust'), x, y, 1, null, { speed: 0.7 });
    scAsh(x, y, 12, 'ash', 50);
  });
  sfx.crumble(); toast(`The ${['first', 'second', 'last'][k]} of the fallen rises.`, 2.4);
}
function scUpdateGauntlet(dt) {
  const G_ = SC_GAUNT;
  if (!G_.active || room.id !== 'R4') return;
  if (P.state === 'dead') { G_.active = false; return; }
  if (G_.champ) return;
  if (G_.spawned.some(e => e.alive)) { G_.t = 1.8; return; }
  G_.t -= dt; if (G_.t > 0) return;
  if (G_.wave < SC_WAVES.length) { scSpawnWave(G_.wave); G_.wave++; G_.t = 1.8; return; }
  G_.champ = true;
  if (boss && boss.kind === 'champion') boss.called = true;
}

// ================================================================== the Gilded Sentinel pair (X3)
BOSS_INFO.sentinels = { name: 'The Gilded Sentinels', hp: 2200, cinders: 4800, reward: ['shard', 'emberstone'], quote: 'Two oaths. One gate. No mercy.' };
const SC_SENT = { sweep: [60, 64], thrust: [66] };
class SentinelPart extends BossBase {
  constructor(pair, x, y, idx) {
    super('sentinels', x, y);
    this.pair = pair; this.idx = idx; this.sh = sheet('gilded_sentinel'); this.anim = new Anim(this.sh, 'idle'); this.state = 'idle';
    this.hp = this.maxHp = this.displayHp = Math.round(1100 * NGP.hp * bossHpMul('sentinels')); this.stanceMax = 300; this.critRange = 50;
    this.name = idx ? 'Sentinel of the Dusk Gate' : 'Sentinel of the Dawn Gate';
    this.vx = 0; this.vy = 0; this.w = 16; this.h = 50; this.ground = true; this.cool = 0.8 + idx * 0.9; this.face = -1;
  }
  get L() { return 8 * TILE + 14; }
  get R() { return 46 * TILE - 14; }
  activate() { this.pair.activate(); }
  canStagger() { return this.state !== 'attack' || this.anim.i < 2; }
  hurtbox() { if (!this.alive) return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 10, this.y - 58, this.x + 10, this.y); }
  stagger() { super.stagger(); this.anim.set('hurt', false); this.vx = 0; }
  die() {
    this.state = 'dead'; this.anim.set('death', false); this.vx = 0;
    sfx.roar(); shake = 8; slowmo = 0.6; flashScreen = 0.3;
    const other = this.pair.parts.find(q => q !== this && q.alive);
    if (other) { other.enraged = true; other.stance = 0; toast(`${other.name} takes up the fallen oath.`, 3); spawnFx(fxOr('warcry', 'roar_ring'), other.x, other.y - 40, 1); }
  }
  hit(info) { super.hit(info); this.pair.onPartHit(this); }
  startAtk(tag) {
    this.facePlayer(); this.atk = tag; this.hitIds = new Set(); this.atkId = ++hazardId; this.state = 'attack'; this.anim.set(tag, false, this.enraged ? 1.18 : 1);
    const wins = metaWindows(this.sh, tag); this.firstActive = wins.length ? wins[0].active[0] : 3;
  }
  update(dt) {
    this.commonUpdate(dt); this.anim.update(dt);
    const an = this.anim;
    if (this.state === 'dead') { this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); if (an.done) { an.hold(); if (!this.gone) { this.gone = true; spawnFx(fxOr('death_ash', 'dust'), this.x, this.y, this.face); scAsh(this.x, this.y, 20, 'gold', 50); } } return; }
    if (!this.active || this.pair.introT > 0) { this.facePlayer(); this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); return; }
    const dx = P.x - this.x, d = Math.abs(dx), other = this.pair.parts.find(q => q !== this && q.alive), spd = this.enraged ? 1.3 : 1;
    switch (this.state) {
      case 'idle': case 'walk': {
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead') { this.setWalk(0, dt); break; }
        // flank: while the partner presses the attack, circle to the far side of the player
        let want = 0;
        const pressing = other && other.state === 'attack';
        const flankX = other ? clamp(P.x + (other.x < P.x ? 1 : -1) * 72, this.L, this.R) : null;
        const pincer = other && Math.sign(this.x - P.x) !== Math.sign(other.x - P.x) && Math.abs(other.x - P.x) < 96 && d < 96;
        if (this.cool <= 0 && pincer && other.cool <= 0.4 && other.state !== 'attack' && this.pair.pincerCool <= 0) {
          this.pair.pincerCool = 7; this.startAtk('thrust'); other.startAtk('thrust'); toast('The sentinels close in from both sides!', 2); break;
        }
        if (this.cool <= 0 && d < 70 && !pressing) { this.startAtk(d < 44 || Math.random() < 0.55 ? 'sweep' : 'thrust'); break; }
        if (pressing && flankX !== null) want = Math.abs(flankX - this.x) > 10 ? Math.sign(flankX - this.x) : 0;
        else want = d > 56 ? Math.sign(dx) : 0;
        this.setWalk(want, dt, spd * (pressing ? 1.25 : 1));
        break;
      }
      case 'attack': {
        const wins = metaWindows(this.sh, this.atk), cfg = ENEMY.gilded_sentinel;
        if (an.i < this.firstActive - 1) this.facePlayer();
        if (an.changed && an.i === Math.max(0, this.firstActive - 1)) { spawnFx('telegraph', this.x + this.face * 30, this.y - 50, this.face); sfx.glint(); }
        let lunging = false;
        wins.forEach((w, wi) => {
          if (an.i < w.active[0] || an.i > w.active[1]) return;
          lunging = true;
          if (an.changed && an.i === w.active[0]) {
            sfx.bossSwing(); const L_ = cfg.lunge && cfg.lunge[this.atk]; if (L_) this.vx = this.face * L_ * (this.enraged ? 1.2 : 1);
            if (this.enraged && this.atk === 'sweep' && wi === 1) { const px = this.x + this.face * 40; spawnFx('shockwave', px, this.y, 1); for (const dd of [-1, 1]) hazards.push({ x: px, y: this.y, vx: dd * 150, w: 12, h: 12, dmg: scBossDmg(24), id: ++hazardId, life: 0.9, wave: true, dir: dd }); shake = 6; }
          }
          if (this.hitIds.has(wi) || !w.hit) return;
          if (overlap(metaRect(this.sh, this, w.hit), playerHurtbox())) {
            const dmg = (SC_SENT[this.atk] || [50])[wi] ?? 50;
            if (hurtPlayer(scBossDmg(dmg) * (this.enraged ? 1.12 : 1), this.face, this.atkId * 10 + wi, { parryable: true, src: this })) this.hitIds.add(wi);
          }
        });
        if (!lunging) this.vx *= Math.pow(0.004, dt);
        this.phys(dt);
        if (an.done) { this.state = 'idle'; this.anim.set('idle', true); this.cool = this.enraged ? rand(0.4, 0.9) : rand(1.0, 1.8); }
        break;
      }
      case 'stagger':
        this.t -= dt; this.vx *= Math.pow(0.02, dt); this.phys(dt);
        if (an.i === an.n - 1) an.hold();
        if (Math.random() < 0.3) particles.push({ x: this.x + rand(-6, 6), y: this.y - 62, vx: 0, vy: -rand(10, 20), life: 0.4, kind: 'gold' });
        if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.4; }
        break;
    }
    this.x = clamp(this.x, this.L, this.R);
  }
  setWalk(dir, dt, spd = 1) {
    this.vx = approach(this.vx, dir * 36 * spd, 400 * dt);
    const want = dir ? 'walk' : 'idle';
    if (this.state !== want) { this.state = want; this.anim.set(want, true, dir ? spd : 1); }
    this.phys(dt);
  }
  phys(dt) { this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  onParried() { super.onParried(); if (this.state !== 'stagger') { this.state = 'idle'; this.anim.set('hurt', false); this.cool = 0.9; } }
  draw() {
    if (this.gone && this.anim.done) return;
    const tint = this.idx ? { flash: 0.16, flashColor: '#5a2a18' } : {};
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : this.enraged ? { flash: 0.12 + 0.08 * Math.sin(time * 9), flashColor: '#ff9a40' } : tint;
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 72 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    if (this.alive && this.active) {
      const w = 34, x = Math.round(this.x - w / 2), y = Math.round(this.y - 70);
      g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y - 1, w + 2, 4);
      g.fillStyle = this.enraged ? '#c05a1a' : '#8a6a1a'; g.fillRect(x, y, Math.max(0, w * this.hp / this.maxHp), 2);
    }
    addLight(this.x, this.y - 40, 50, '255,215,140', this.enraged ? 0.7 : 0.4);
  }
}
class SentinelPair extends BossBase {
  constructor(x, y) {
    super('sentinels', x, y);
    this.parts = [new SentinelPart(this, x - 60, y, 0), new SentinelPart(this, x + 60, y, 1)];
    this.hp = this.maxHp = this.displayHp = this.parts.reduce((s, q) => s + q.maxHp, 0);
    this.sh = sheet('gilded_sentinel'); this.state = 'dormant'; this.pincerCool = 4;
    const parts = this.parts;
    this.anim = { i: 0, n: 2, done: false, get frame() { return 0; }, update(dt) { for (const q of parts) if (q.alive) q.anim.update(dt); }, set(tag, loop) { for (const q of parts) if (q.alive) q.anim.set(tag, loop); } };
  }
  get alive() { return this.state !== 'dead'; }
  hurtbox() { return null; }
  canStagger() { return false; }
  onPartHit() { this.hp = this.parts.reduce((s, q) => s + Math.max(0, q.hp), 0); const hit = this.parts.filter(q => q.dmgT > 0); this.dmgShown = hit.reduce((s, q) => s + q.dmgShown, 0); this.dmgT = Math.max(...this.parts.map(q => q.dmgT)); }
  facePlayer() { for (const q of this.parts) if (q.alive) q.facePlayer(); }
  update(dt) {
    this.flash = 0; this.dmgT -= dt; this.pincerCool -= dt;
    const alive = this.parts.filter(q => q.alive);
    this.x = alive.length ? alive.reduce((s, q) => s + q.x, 0) / alive.length : this.x; this.camX = this.x;
    this.hp = this.parts.reduce((s, q) => s + Math.max(0, q.hp), 0);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    for (const q of this.parts) { q.active = this.active; q.update(dt); }
    if (!this.active) { if (!this.cutting && P.x > 9 * TILE && P.x < 45 * TILE && P.ground && this.state !== 'dead') this.activate(); return; }
    if (this.introT > 0) { this.introT -= dt; if (this.introT <= 0) this.state = 'idle'; }
    if (this.state !== 'dead' && !alive.length && this.parts.every(q => q.anim.done)) this.die();
  }
  die() {
    this.state = 'dead'; this.anim.i = 1;
    hazards = []; shake = 10; hitstop = 0.25; slowmo = 1.2; flashScreen = 0.5; sfx.felled();
    victoryBanner = { text: 'THE GATE STANDS OPEN', t: 0 };
    this.rewards();
  }
  draw() { for (const q of this.parts) q.draw(); }
}
BOSS_SPAWN.sentinels = (cx, fy) => new SentinelPair(cx, fy);

// ================================================================== The First Ember (secret superboss, Ember's Hollow)
BOSS_INFO.first_ember = { name: 'The First Ember', hp: 5200, cinders: 30000, reward: ['w:first_ember', 'c_echo', 'sp:ember_echo'], quote: 'The ash made it first. It made you after.' };
const SC_EMB_CV = document.createElement('canvas'); SC_EMB_CV.width = 96; SC_EMB_CV.height = 64;
const SC_EMB = SC_EMB_CV.getContext('2d'); SC_EMB.imageSmoothingEnabled = false;
const SC_CRACK = (() => {   // a tileable field of burning cracks, masked onto the silhouette at draw time
  const c = document.createElement('canvas'); c.width = 64; c.height = 64; const x = c.getContext('2d');
  const segs = [];
  for (let k = 0; k < 16; k++) {
    let px = hash2(k, 1) * 64, py = hash2(k, 2) * 64, a = hash2(k, 3) * 6.28;
    for (let s = 0; s < 7; s++) { const nx = px + Math.cos(a) * 3.2, ny = py + Math.sin(a) * 3.2; segs.push([px, py, nx, ny, s]); px = nx; py = ny; a += (hash2(k, s + 9) - 0.5) * 1.6; }
  }
  for (const [a, b, c2, d, s] of segs) {
    const n = 4; for (let i = 0; i <= n; i++) { const X = Math.round(lerp(a, c2, i / n)) & 63, Y = Math.round(lerp(b, d, i / n)) & 63; x.fillStyle = s < 2 ? '#ffd27a' : s < 5 ? '#ff8a30' : '#c0401a'; x.fillRect(X, Y, 1, 1); }
  }
  return c;
})();
function scDrawEmberSprite(sh, frame, X, Y, face, opt = {}) {
  if (!sh || !sh.ok) return;
  const f = sh.frames[frame]; if (!f) return;
  const cw = SC_EMB_CV.width, chh = SC_EMB_CV.height, ox_ = (cw - f.w) >> 1, oy_ = chh - f.h;
  SC_EMB.globalCompositeOperation = 'source-over'; SC_EMB.globalAlpha = 1; SC_EMB.clearRect(0, 0, cw, chh);
  SC_EMB.drawImage(sh.img, f.x, f.y, f.w, f.h, ox_, oy_, f.w, f.h);
  SC_EMB.globalCompositeOperation = 'source-atop';
  SC_EMB.fillStyle = opt.weapon ? '#2a0e08' : '#1a0c10'; SC_EMB.globalAlpha = opt.weapon ? 0.7 : 0.8; SC_EMB.fillRect(0, 0, cw, chh);
  SC_EMB.globalAlpha = opt.crack ?? (0.8 + 0.2 * Math.sin(time * 3 + (opt.seed || 0)));
  const sx = Math.floor(time * 6) % 64;
  for (let yy = -64; yy < chh + 64; yy += 64) for (let xx = -64; xx < cw + 64; xx += 64) SC_EMB.drawImage(SC_CRACK, xx + sx, yy - Math.floor(time * 9) % 64);
  if (opt.flash) { SC_EMB.globalAlpha = Math.min(1, opt.flash); SC_EMB.fillStyle = opt.flashColor || '#ffd9a0'; SC_EMB.fillRect(0, 0, cw, chh); }
  SC_EMB.globalCompositeOperation = 'source-over'; SC_EMB.globalAlpha = 1;
  const flip = face !== sh.native, ax = sh.ax + ox_, ay = sh.ay + oy_, rx = Math.round(X), ry = Math.round(Y);
  g.save(); g.globalAlpha = opt.alpha ?? 1;
  if (opt.clipBottom !== undefined) { g.beginPath(); g.rect(rx - 80, ry - 120, 160, Math.round(opt.clipBottom) - (ry - 120)); g.clip(); }
  if (flip) { g.translate(rx, 0); g.scale(-1, 1); g.drawImage(SC_EMB_CV, -ax, ry - ay); }
  else g.drawImage(SC_EMB_CV, rx - ax, ry - ay);
  g.restore();
}
function scEmberRim(sh, frame, X, Y, face, a) {   // a thin burning outline around the silhouette
  for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) drawSprite(sh, frame, X + dx, Y + dy, face, { flash: 1, flashColor: '#ff6a24', alpha: a * 0.75 });
}
// ---- the First Ember's arsenal: every weapon set, drawn from the player sheet's class animations + wpn_<id> overlays.
// sig = signature effect it carries over from that weapon's former owner (see scEmberSig).
const SC_ARSENAL = [
  { wid: 'omen', sig: 'omen' }, { wid: 'kalden', sig: 'kalden' }, { wid: 'longsword' },
  { wid: 'pagecutter' }, { wid: 'dagger' },
  { wid: 'colossus_hammer', sig: 'lava' }, { wid: 'greatsword' },
  { wid: 'stormfang', sig: 'storm' }, { wid: 'spear' },
  { wid: 'stormvein' }, { wid: 'katana' },
  { wid: 'inkquill', sig: 'ink' }, { wid: 'windstaff', sig: 'wind' }, { wid: 'quarterstaff' },
  { wid: 'knight_shield' }, { wid: 'twinborne', sig: 'frost' },
  { wid: 'twinfangs' },
];
const SC_ART_ANIM = { crescent: ['attack2', 0.8], moonwave: ['heavy', 1.0], bloodstep: ['air_attack', 1.0], stormleap: ['double_jump', 1], warcry: ['cast', 1.1], cinderblade: ['cast', 1.1] };
// arts of the new weapons, mapped onto the Ember's own implementations
const SC_ART_MAP = { whirlwind: 'spinwind', gale_vault: 'stormleap', ink_mark: 'glyphs', aegis: 'guard', frost_aegis: 'guard', shield_charge: 'bloodstep',
  thunder_lunge: 'bloodstep', twin_tempest: 'bloodstep', magma_quake: 'stormleap', tolling_blow: 'stormleap', echo: 'moonwave' };
const SC_EMBER_DMG = { light: 46, heavy: 58, art: 50, bolt: 34, sig: 30 };     // Morvain-scale per-hit numbers (x BOSS_DMG)
const scEmberLog = [];                                                          // debug: recent hits on the player
class FirstEmber extends BossBase {
  constructor(x, y) {
    super('first_ember', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.first_ember.hp * NGP.hp);
    this.sh = sheet('player'); this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant'; this.stanceMax = 300; this.critRange = 40;
    this.w = 10; this.h = 26; this.vx = 0; this.vy = 0; this.ground = true; this.face = -1;
    this.rise = 0; this.hidden = true; this.reactCool = 1; this.healed = 0; this.buffT = 0; this.fireT = 0;
    this.echoes = []; this.cool = 1; this.strings = 0; this.restEvery = 3; this.teleCool = 4; this.swaps = 0; this.wids = {};
    this.arsenal = SC_ARSENAL.filter(a => WEAPONS[a.wid] && sheet('wpn_' + a.wid).ok && this.clsOk(WEAPON_CLASS[a.wid]));
    if (!this.arsenal.length) this.arsenal = [{ wid: 'longsword' }];
    this.equip(this.arsenal.find(a => a.wid === 'longsword') || this.arsenal[0], true);
  }
  clsOk(c) { const s = MOVESETS[c]; return !!s && (c === 'sword' || (this.sh.has(s.combo[0]) && !!ATK[s.combo[0]] && !!ATK[s.heavy])); }
  equip(a, quiet) { this.arm = a; this.wid = a.wid; this.wids[a.wid] = 1; if (!quiet) this.swaps++; }
  get cls() { const c = WEAPON_CLASS[this.wid] || 'sword'; return this.clsOk(c) ? c : 'sword'; }
  moveset() { return MOVESETS[this.cls] || MOVESETS.sword; }
  wsheet() { const s = sheet('wpn_' + this.wid); return s.ok ? s : sheet('wpn_longsword'); }
  reach() { const A = ATK[this.moveset().combo[0]] || ATK.attack1; return Math.max(26, A.reach[1] * (A.cls ? 1 : (WEAPONS[this.wid] || {}).reach || 1)); }
  hurtbox() { if (!this.alive || this.hidden) return null; return rect(this.x - 7, this.y - 27, this.x + 7, this.y); }
  canStagger() { return !['roll', 'art', 'blink'].includes(this.state) && this.ground; }
  critable() { return this.state === 'stagger' && !this.critDone; }
  iframes() { return (this.state === 'roll' && this.anim.i >= 1 && this.anim.i <= 6) || (this.state === 'art' && this.artI) || this.state === 'intro' || (this.state === 'blink' && this.blinkT < 0.42); }
  setA(st, tag, loop = false, speed = 1) { this.state = st; this.anim.set(this.sh.has(tag) ? tag : 'attack1', loop, speed); }
  stagger() { super.stagger(); this.anim.set('hurt', false, 0.5); this.vx = -this.face * 40; this.atk = null; this.guarding = false; }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 120; if (this.stance >= this.stanceMax) this.stagger(); else { this.setA('recoil', 'hurt', false, 0.8); this.vx = -this.face * 80; this.cool = 0.35; } }
  wake() { return P.ground && P.x > 6 * TILE; }
  get fast() { return this.phase === 2 ? 1.12 : 1; }
  update(dt) {
    this.commonUpdate(dt); this.anim.update(dt);
    this.buffT -= dt; this.fireT -= dt; this.reactCool -= dt; this.teleCool -= dt;
    this.updateEchoes(dt);
    if (!this.active) { if (!this.cutting && this.state === 'dormant' && this.wake()) this.activate(); return; }
    this.hidden = this.state === 'blink' && this.blinkT < 0.42; this.rising = false;
    if (this.introT > 0) {
      this.introT -= dt; this.state = 'intro';
      if (this.introT > 1.0) { this.rising = true; this.rise = clamp(1 - (this.introT - 1.0) / 1.6, 0, 1); if (this.anim.tag !== 'rest') this.anim.set('rest', false); this.anim.i = this.anim.n - 1; if (Math.random() < 0.8) particles.push({ x: this.x + rand(-10, 10), y: this.floor - rand(0, 20), vx: 0, vy: -rand(20, 60), life: 0.8, kind: 'ember' }); }
      else if (this.anim.tag !== 'rise' && this.sh.has('rise')) { this.anim.set('rise', false); this.facePlayer(); }
      if (this.introT <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.4; }
      this.phys(dt); return;
    }
    const dx = P.x - this.x, d = Math.abs(dx);
    this.guarding = this.cls === 'shield' && ['idle', 'run', 'guard'].includes(this.state);
    // reactive defence: it reads your swing (parry, roll away, or raise the shield)
    if (['idle', 'run', 'guard'].includes(this.state) && this.reactCool <= 0 && ATK[P.state] && P.anim.i <= 1 && d < 64 && P.state !== this.lastSeen) {
      this.lastSeen = P.state; const r = Math.random();
      if (this.cls === 'shield') { this.facePlayer(); this.setA('guard', 'sh_guard', true); this.t = 0.5; this.reactCool = 1.2; }
      else if (r < (this.phase === 2 ? 0.22 : 0.16)) { this.facePlayer(); this.setA('parry', 'parry', false, 1); this.parryT = 0.3; this.reactCool = 2.6; sfx.glint(); }
      else if (r < 0.36) { this.startRoll(-Math.sign(dx) || -this.face); this.reactCool = 1.6; }
      else this.reactCool = 0.5;
    }
    if (!ATK[P.state]) this.lastSeen = null;
    switch (this.state) {
      case 'idle': case 'run': case 'guard': {
        this.facePlayer(); this.cool -= dt; this.t = (this.t || 0) - dt;
        if (P.state === 'dead') { this.stand(dt); break; }
        if (this.state === 'guard' && this.t > 0) { this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt); break; }
        if (this.hp < this.maxHp * (this.phase === 1 ? 0.62 : 0.18) && this.healed < this.phase && d > 100) { this.healed = this.phase; this.setA('heal', 'heal', false, 0.8); this.healDone = false; break; }
        if (this.cool <= 0) { this.decide(d, dx, dt); break; }
        const reach = this.reach();
        if (d > reach + 4) this.run(Math.sign(dx), dt); else this.stand(dt);
        break;
      }
      case 'atk': this.updateAtk(dt); break;
      case 'switch': {
        this.t -= dt; this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt); this.facePlayer();
        if (!this.swapped && this.t < 0.14) { this.swapped = true; this.equip(this.nextArm); spawnFx(fxOr('sc_eburst', 'hit'), this.x + this.face * 8, this.y - 16, 1, null, { speed: 1.6 }); tone(520, 0.2, 0.05, 'triangle', 1.6); sfx.fire(); }
        if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.05; }
        break;
      }
      case 'rest':     // a rare, short punish window: it gutters, catches its breath
        this.t -= dt; this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt);
        if (Math.random() < 0.2) particles.push({ x: this.x + rand(-5, 5), y: this.y - rand(18, 26), vx: 0, vy: -rand(5, 12), life: 0.6, kind: 'ash' });
        if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.1; }
        break;
      case 'blink': this.updateBlink(dt); break;
      case 'roll': {
        const dashing = this.anim.i <= 6;
        this.vx = dashing ? this.rollDir * 225 : approach(this.vx, 0, 900 * dt);
        if (dashing && Math.random() < 0.8) this.echoes.push({ ghost: true, f: this.anim.frame, x: this.x, y: this.y, face: this.face, life: 0.22 });
        this.phys(dt);
        if (this.anim.done) { if (this.rollAttack && Math.abs(P.x - this.x) < 80) { this.facePlayer(); const ms = this.moveset(); this.startAtk(ms.combo[ms.combo.length - 1], 1, 0.1); this.comboStep = -1; } else { this.state = 'idle'; this.anim.set('idle', true); this.cool = rand(0.05, 0.2); } }
        break;
      }
      case 'parry':
        this.parryT -= dt; this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt);
        if (this.anim.done) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.15; }
        break;
      case 'recoil':
        this.vx *= Math.pow(0.05, dt); this.phys(dt);
        if (this.anim.done) { this.state = 'idle'; this.anim.set('idle', true); this.cool = Math.max(this.cool, 0.3); }
        break;
      case 'cast': {
        this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt);
        if (this.anim.i >= 2 && this.anim.i <= 5) addLight(this.x + this.face * 12, this.y - 18, 40, '255,120,60', 0.9);
        if (!this.fired && this.anim.i >= 4) { this.fired = true; this.castBolt(); }
        if (this.anim.done) this.endString(0.2);
        break;
      }
      case 'heal':
        this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt);
        if (!this.healDone && this.anim.i >= 3) { this.healDone = true; const h = Math.round(this.maxHp * 0.07); this.hp = Math.min(this.maxHp, this.hp + h); spawnFx('heal', this.x, this.y, this.face, this, { tint: '#ff7a3a' }); sfx.heal(); popup(this.x, this.y - 34, h, '#ff9a5a'); }
        if (this.anim.done) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.2; }
        break;
      case 'art': this.updateArt(dt); break;
      case 'stagger':
        this.t -= dt; this.vx *= Math.pow(0.02, dt); this.phys(dt);
        if (this.anim.i === this.anim.n - 1 && this.t > 0.2) this.anim.hold();
        if (this.t <= 0) { if (this.pendingPhase) this.enterPhase2(); else { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.2; } }
        break;
      case 'dead':
        this.vx *= Math.pow(0.05, dt); this.phys(dt);
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(0, 28), vx: rand(-10, 10), vy: -rand(15, 50), life: rand(0.8, 1.6), kind: 'ember' });
        if (this.anim.done) this.anim.hold();
        break;
    }
    if (this.guarding && this.state === 'idle' && this.sh.has('sh_guard') && this.anim.tag === 'idle') this.anim.set('sh_guard', true);
    if (this.phase === 1 && this.hp <= this.maxHp * 0.5 && this.alive && !this.pendingPhase) {
      if (['atk', 'art', 'roll', 'stagger', 'cast', 'heal', 'blink', 'switch'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    if (this.pendingPhase && ['idle', 'run', 'parry', 'recoil', 'guard', 'rest'].includes(this.state)) this.enterPhase2();
    this.x = clamp(this.x, this.L - 10, this.R + 10);
    if (!this.hidden && Math.random() < 0.35) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(4, 26), vx: rand(-6, 6), vy: -rand(10, 35), life: rand(0.4, 0.9), kind: 'ember' });
  }
  // ---- choosing: it hardly ever stops. Long strings, weapon swaps between them, a rare breath.
  decide(d, dx, dt) {
    const reach = this.reach(), r = Math.random(), p2 = this.phase === 2;
    if (p2 && this.teleCool <= 0 && d < 260 && Math.random() < 0.55) return this.startBlink();
    if (this.strings >= this.nextSwap) return this.startSwitch();
    if (d < reach + 10) {
      if (r < 0.58) return this.startCombo();
      if (r < 0.76) return this.startHeavy();
      if (r < 0.9) return this.startArt();
      return this.startRoll(-this.face, true);
    }
    if (d < 170) {
      if (r < 0.34) return this.startRoll(Math.sign(dx), true);
      if (r < 0.6) return this.startArt();
      if (r < 0.78) return this.startCast();
      this.run(Math.sign(dx), dt); this.cool = 0.12; return;
    }
    if (r < 0.35) return this.startCast();
    if (r < 0.6) return this.startArt();
    this.run(Math.sign(dx), dt); this.cool = 0.15;
  }
  get nextSwap() { return this._ns ?? (this._ns = irand(1, 2)); }
  endString(extra = 0) {
    this.strings++; this.comboStep = -1;
    const p2 = this.phase === 2;
    if (this.strings % this.restEvery === 0 && Math.random() < 0.8) {   // rare punish window
      this.state = 'rest'; this.anim.set('idle', true, 0.5); this.t = p2 ? rand(0.55, 0.8) : rand(0.8, 1.1); this.restEvery = irand(3, 4);
      tone(110, 0.5, 0.05, 'sine', 0.7); return;
    }
    this.state = 'idle'; this.anim.set('idle', true);
    this.cool = (p2 ? rand(0.04, 0.2) : rand(0.12, 0.35)) + extra;
  }
  startSwitch() {
    const pool = this.arsenal.filter(a => a.wid !== this.wid && (this.phase === 2 || a.wid !== SAVE.weapon));
    const byCls = {}; for (const a of pool) (byCls[WEAPON_CLASS[a.wid]] ||= []).push(a);
    const classes = Object.keys(byCls).filter(c => c !== this.cls);
    const cls = classes.length ? classes[irand(0, classes.length - 1)] : null;
    const list = cls ? byCls[cls] : pool;
    this.nextArm = (this.phase === 2 && SAVE.weapon && WEAPONS[SAVE.weapon] && WEAPON_CLASS[SAVE.weapon] !== 'mirror' && Math.random() < 0.2 && SAVE.weapon !== this.wid)
      ? { wid: SAVE.weapon } : list[irand(0, list.length - 1)] || this.arsenal[0];
    this.strings = 0; this._ns = irand(1, 2); this.swapped = false; this.facePlayer();
    this.setA('switch', this.sh.has('parry') ? 'parry' : 'idle', false, 1.2); this.t = 0.28;
    for (let i = 0; i < 10; i++) particles.push({ x: this.x + this.face * rand(4, 16), y: this.y - rand(8, 24), vx: rand(-30, 30), vy: -rand(20, 60), life: 0.4, kind: 'ember' });
  }
  phys(dt) { this.vy = Math.min(this.vy + 860 * dt, 430); moveBody(this, dt); }
  run(dir, dt) { this.vx = approach(this.vx, dir * 118 * this.fast, 1200 * dt); if (dir) this.face = dir; if (this.state !== 'run') { this.state = 'run'; this.anim.set('run', true); } this.phys(dt); }
  stand(dt) { this.vx = approach(this.vx, 0, 1400 * dt); if (this.state !== 'idle' && this.state !== 'guard') { this.state = 'idle'; this.anim.set('idle', true); } this.phys(dt); }
  startRoll(dir, attack = false) { this.rollDir = dir; this.face = dir; this.rollAttack = attack; this.setA('roll', 'roll', false, 1); sfx.roll(); spawnFx('dust', this.x - dir * 6, this.y, dir); }
  startCombo() { this.comboStep = 0; const ms = this.moveset(); this.startAtk(ms.combo[0], 0.82, this.phase === 2 ? 0.22 : 0.28); }
  startHeavy() { const ms = this.moveset(), A = ATK[ms.heavy] || ATK.heavy; this.startAtk(ms.heavy, 0.9, 0); this.charge = A.noCharge ? 0 : (this.phase === 2 ? 0.45 : 0.55); if (A.noCharge) this.hold = 0.3; this.comboStep = -1; }
  startAtk(name, speed = 1, hold = 0) {
    const A = ATK[name] || ATK.attack1; this.facePlayer();
    this.atk = name; this.A = A; this.hitDone = false; this.hitBack = false; this.atkId = ++hazardId; this.hold = hold; this.charge = 0; this.glinted = false;
    this.setA('atk', A.anim || name, false, speed * this.fast);
  }
  updateAtk(dt) {
    const A = this.A, an = this.anim, heavy = A.kind === 'heavy';
    if (an.i < A.active[0]) this.facePlayer();
    // readable wind-up: it holds the frame before the strike while the blade flares
    if (an.i === Math.max(0, A.active[0] - 1)) {
      if (heavy && this.charge > 0) {
        this.charge -= dt; an.t = Math.min(an.t, 5);
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(0, 30), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'fire' });
        if (this.charge <= 0.15 && !this.glinted) { this.glinted = true; spawnFx('telegraph', this.x - this.face * 2, this.y - 36, this.face); sfx.glint(); }
      } else if (this.hold > 0) {
        this.hold -= dt; an.t = Math.min(an.t, 5);
        if (this.hold <= 0.14 && !this.glinted) { this.glinted = true; spawnFx('telegraph', this.x + this.face * 14, this.y - 26, this.face); sfx.glint(); }
      }
    }
    if (an.changed && an.i === A.active[0]) {
      if (A.lunge) this.vx = this.face * A.lunge * 0.9;
      (heavy || A.big ? sfx.heavySwing : sfx.swing)();
      if (A.fx) spawnFx(fxOr(A.fx, 'slash'), this.x + this.face * A.fxAt[0], this.y + A.fxAt[1], this.face, null, { tint: '#ff5a1a' });
      if (A.slam) { shake = 6; sfx.boom(); spawnFx('shockwave', this.x + this.face * 22, this.y, 1); for (const dd of [-1, 1]) hazards.push({ x: this.x + this.face * 22, y: this.y, vx: dd * 150, w: 12, h: 12, dmg: scBossDmg(24, this), id: ++hazardId, life: 0.8, wave: true, dir: dd, color: 'root' }); }
      if (A.spin || A.staffSpin) { spawnFx(fxOr('spin', 'slash3'), this.x, this.y, 1, null, { tint: '#ff5a1a' }); if (this.arm.sig === 'wind') for (const dd of [-1, 1]) scWhirl(this, this.x + dd * 20, dd, 26); }
      this.sigSwing(A, heavy);
      if (this.phase === 2 && heavy) this.echoes.push({ at: 0.55, x: this.x, y: this.y, face: this.face, A, f: an.frame, id: ++hazardId });
    }
    if (an.i >= A.active[0] && an.i <= A.active[1]) {
      const base = heavy ? SC_EMBER_DMG.heavy : SC_EMBER_DMG.light, m = Math.min(1.1, A.mult || 1) * (this.buffT > 0 ? 1.15 : 1) * (this.fireT > 0 ? 1.1 : 1);
      const dmg = scBossDmg(base * m, this);
      if (!this.hitDone && overlap(this.atkRect(A, this.x, this.y, this.face), playerHurtbox())) {
        if (this.hurt_(dmg, this.face, this.atkId, !A.spin)) this.hitDone = true;
      }
      if ((A.spin || A.staffSpin) && !this.hitBack && overlap(this.atkRect(A, this.x, this.y, -this.face), playerHurtbox())) {
        if (this.hurt_(dmg, -this.face, this.atkId + 0.5, false)) this.hitBack = true;
      }
    }
    if (this.ground) this.vx *= Math.pow(0.0008, dt);
    this.phys(dt);
    if (this.state !== 'atk') return;
    if (an.i > A.active[1] && this.comboStep >= 0) {
      const seq = this.moveset().combo;
      if (this.comboStep + 1 < seq.length && Math.abs(P.x - this.x) < 90) {
        this.comboStep++; this.startAtk(seq[this.comboStep], 1.0, this.comboStep === seq.length - 1 ? 0.16 : 0.07); return;
      }
      if (this.comboStep + 1 >= seq.length && Math.random() < (this.phase === 2 ? 0.55 : 0.4)) { this.comboStep = -1; if (Math.random() < 0.6) this.startHeavy(); else this.startArt(); return; }
    }
    if (an.done) this.endString();
  }
  hurt_(dmg, dir, id, parryable) {
    const hp0 = P.hp, ok = hurtPlayer(dmg, dir, id, { parryable, src: this });
    if (ok) { scEmberLog.push({ t: time, raw: Math.round(dmg), got: Math.round(hp0 - P.hp), atk: this.atk || this.artId, wid: this.wid }); if (scEmberLog.length > 200) scEmberLog.shift(); }
    return ok;
  }
  atkRect(A, x, y, face) {
    const front = A.reach[1] * (A.cls ? 1 : ((WEAPONS[this.wid] || {}).reach || 1)) * REACH_MUL;
    return rect(x + face * A.reach[0], y + A.ys[0], x + face * front, y + A.ys[1]);
  }
  isFinisher() { const ms = this.moveset(); return this.atk === ms.combo[ms.combo.length - 1]; }
  // ---- signature effects carried over from each weapon's former owner (hostile versions)
  sigSwing(A, heavy) {
    const sig = this.arm.sig, fin = heavy || this.isFinisher(), px = this.x + this.face * 22, py = this.y - 18;
    if (sig === 'omen') {
      spawnFx(fxOr('boss_slash', 'slash3'), px, py, this.face, null, { speed: heavy ? 0.85 : 1.2, alpha: 0.95 });
      if (fin) { const n = heavy ? 3 : 1; for (let k = 0; k < n; k++) projectiles.push({ owner: 'enemy', kind: 'sc_espear', x: this.x + this.face * 16, y: this.y - 20 + (k - (n - 1) / 2) * 8, vx: this.face * (250 + k * 20), vy: (k - (n - 1) / 2) * 20, dmg: scBossDmg(SC_EMBER_DMG.sig, this), life: 1.1, r: 5, t: 0, id: ++hazardId, sh: 'fx_light_spear' }); sfx.spear(); }
    } else if (sig === 'kalden') {
      spawnFx(fxOr('kalden_slash', 'slash3'), px, py, this.face, null, { speed: heavy ? 0.8 : 1.15, alpha: 0.95 });
      if (fin) { projectiles.push({ owner: 'enemy', kind: 'sc_kcres', x: this.x + this.face * 22, y: this.y - 20, vx: this.face * 230, vy: 0, dmg: scBossDmg(SC_EMBER_DMG.sig + 6, this), life: 0.85, r: 12, t: 0, id: ++hazardId, sh: 'fx_kalden_slash', face: this.face }); tone(440, 0.3, 0.05, 'triangle', 0.55); }
    } else if (sig === 'ink' && fin) this.glyphs(heavy ? 3 : 1);
    else if (sig === 'storm' && fin) {
      if (typeof wZap === 'function') wZap(this.x + this.face * 20, this.y - 20, this.x + this.face * 60, this.y - 18 + rand(-8, 8), 0.14);
      if (heavy) this.skyBolt(P.x);
    } else if (sig === 'lava' && heavy) {
      for (const dd of [this.face]) hazards.push({ x: this.x + dd * 26, y: this.y, vx: dd * 120, w: 16, h: 14, dmg: scBossDmg(28, this), id: ++hazardId, life: 1.5, wave: true, dir: dd, color: 'root' });
      sfx.fire();
    } else if (sig === 'frost') for (let i = 0; i < 8; i++) particles.push({ x: px, y: py, vx: this.face * rand(20, 90), vy: rand(-40, 20), life: 0.5, kind: 'frost' });
  }
  glyphs(n) {   // inkquill: violet glyphs written onto the ground at your feet, bursting a moment later
    for (let k = 0; k < n; k++) {
      const x = clamp(P.x + (k - (n - 1) / 2) * 30, this.L, this.R), y = P.y - 14;
      hazards.push({ x, y: y + 14, w: 30, h: 30, dmg: scBossDmg(SC_EMBER_DMG.sig, this), id: ++hazardId, life: 0.95, t: 0,
        active: h => h.t > 0.68 && h.t < 0.82,
        update: h => { if (h.t > 0.68 && !h.boom) { h.boom = true; sfx.bolt(); for (let i = 0; i < 12; i++) particles.push({ x: h.x, y: y, vx: rand(-70, 70), vy: rand(-70, 30), g: 150, life: 0.5, kind: 'ink' }); } } });
      const hz = hazards[hazards.length - 1];
      if (typeof wfx === 'function') wfx({ life: 0.95, draw() { if (hz.boom) { if (typeof wfxDraw === 'function') wfxDraw('inkburst', this.t - 0.68, x, y, 1, { center: true }); } else { if (!(typeof wfxDraw === 'function' && wfxDraw('glyph', this.t, x, y, 1, { center: true, loop: true, alpha: 0.5 + 0.5 * Math.sin(this.t * 20) }))) { g.strokeStyle = '#b890ff'; g.strokeRect(x - 8, y - 8, 16, 16); } addLight(x, y, 26, '170,120,240', 0.7); } } });
    }
    tone(311, 0.3, 0.05, 'sine', 0.6);
  }
  skyBolt(x) {  // stormfang: a sky bolt called onto your position (thin warning line first)
    const fy = this.floor;
    hazards.push({ x, y: fy, w: 22, h: 150, dmg: scBossDmg(40, this), id: ++hazardId, life: 0.95, t: 0,
      active: h => h.t > 0.5 && h.t < 0.66,
      update: h => {
        if (h.t < 0.5) { if (Math.random() < 0.5) particles.push({ x: x + rand(-3, 3), y: fy - rand(0, 140), vx: 0, vy: 0, life: 0.2, kind: 'frost' }); addLight(x, fy - 20, 18, '170,210,255', 0.5); }
        else if (!h.struck) { h.struck = true; flashScreen = Math.max(flashScreen, 0.2); shake = Math.max(shake, 6); noise(0.6, 900, 0.7, 0.5, 'lowpass', 0.4); if (typeof wZap === 'function') wZap(x + rand(-10, 10), fy - 180, x, fy, 0.25); }
      } });
    sfx.charge();
  }
  castBolt() {
    const a = Math.atan2(P.y - 16 - (this.y - 18), P.x - this.x), n = this.phase === 2 ? 3 : 2;
    for (let k = 0; k < n; k++) {
      const aa = a + (k - (n - 1) / 2) * 0.2;
      projectiles.push({ owner: 'enemy', kind: 'sc_ebolt', x: this.x + this.face * 14, y: this.y - 18, vx: Math.cos(aa) * 240, vy: Math.sin(aa) * 240, dmg: scBossDmg(SC_EMBER_DMG.bolt, this), life: 1.8, r: 5, t: 0, id: ++hazardId, sh: 'fx_sc_ebolt', face: this.face });
    }
    sfx.bolt(); sfx.fire();
  }
  startCast() { this.facePlayer(); this.fired = false; this.setA('cast', 'cast', false, 0.85 * this.fast); sfx.charge(); spawnFx('telegraph', this.x + this.face * 10, this.y - 22, this.face); }
  startArt() {
    const raw = (WEAPONS[this.wid] && WEAPONS[this.wid].art) || 'crescent';
    let id = SC_ART_ANIM[raw] ? raw : (SC_ART_MAP[raw] || 'crescent');
    if (id === 'guard' && this.cls !== 'shield') id = 'crescent';
    this.artId = id; this.artT = 0; this.artFired = false; this.artI = false; this.facePlayer(); this.atkId = ++hazardId;
    if (id === 'guard') { this.setA('guard', 'sh_guard', true); this.t = 0.6; this.cool = 0; return; }
    if (id === 'spinwind' || id === 'glyphs') {   // staff arts: a flourish, then the effect
      this.setA('art', this.sh.has('st_heavy') ? 'st_heavy' : 'attack2', false, 0.8 * this.fast); spawnFx('telegraph', this.x, this.y - 30, this.face); sfx.charge(); this.artRel = 2; return;
    }
    const own = 'art_' + id, A = this.sh.has(own) ? [own, 0.85] : SC_ART_ANIM[id];
    this.setA('art', A[0], false, A[1] * this.fast);
    this.artRel = this.sh.has(own) && ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves[own] ? ASSETS.player_meta.moves[own].active[0] : { crescent: 2, moonwave: 4, bloodstep: 1, stormleap: 0, warcry: 3, cinderblade: 3 }[id];
    spawnFx('telegraph', this.x, this.y - 30, this.face); sfx.charge();
    if (id === 'stormleap') { this.vy = -330; this.ground = false; this.vx = clamp((P.x - this.x) * 1.1, -180, 180); sfx.jump(); }
  }
  updateArt(dt) {
    const id = this.artId, an = this.anim; this.artT += dt;
    if (id === 'bloodstep') {
      if (this.artT < 0.3) { this.vx = 0; this.phys(dt); return; }                 // crouch: read it
      const dashing = this.artT < 0.56;
      this.artI = dashing; this.vx = dashing ? this.face * 370 : this.vx * 0.8; this.vy = 0; moveBody(this, dt);
      if (dashing) { this.echoes.push({ ghost: true, f: an.frame, x: this.x, y: this.y, face: this.face, life: 0.25, red: true }); if (!this.artFired && overlap(rect(this.x - 14, this.y - 26, this.x + 14, this.y), playerHurtbox())) { if (this.hurt_(scBossDmg(SC_EMBER_DMG.art, this), this.face, this.atkId, false)) this.artFired = true; } }
      if (this.arm.sig === 'storm' && dashing && Math.random() < 0.3 && typeof wZap === 'function') wZap(this.x, this.y - 14, this.x - this.face * 30, this.y - 14 + rand(-6, 6), 0.1);
      if (this.artT > 0.78) this.endString();
      return;
    }
    if (id === 'stormleap') {
      this.phys(dt);
      if (this.artT > 0.15 && this.ground && !this.artFired) {
        this.artFired = true; shake = 8; sfx.boom();
        spawnFx(fxOr('stormleap', 'shockwave'), this.x, this.y, 1, null, { bottom: true, tint: '#ff5a1a' });
        if (overlap(rect(this.x - 58, this.y - 30, this.x + 58, this.y + 2), playerHurtbox())) this.hurt_(scBossDmg(SC_EMBER_DMG.art + 10, this), P.x < this.x ? -1 : 1, this.atkId, false);
        for (const dd of [-1, 1]) hazards.push({ x: this.x, y: this.y, vx: dd * 160, w: 12, h: 12, dmg: scBossDmg(26, this), id: ++hazardId, life: 1.0, wave: true, dir: dd, color: 'root' });
        this.anim.set('land', false);
      }
      if ((this.artFired && this.anim.done) || this.artT > 2.5) this.endString();
      return;
    }
    this.vx = approach(this.vx, 0, 900 * dt); this.phys(dt);
    if (!this.artFired && an.i >= this.artRel) {
      this.artFired = true;
      if (id === 'warcry') { this.buffT = 10; sfx.roar(); shake = 4; spawnFx(fxOr('warcry', 'roar_ring'), this.x, this.y - 16, 1, null, { tint: '#ff6a2a' }); }
      else if (id === 'cinderblade') { this.fireT = 14; sfx.fire(); }
      else if (id === 'spinwind') { for (const dd of [-1, 1]) scWhirl(this, this.x + dd * 20, dd, 28); spawnFx(fxOr('spin', 'slash3'), this.x, this.y, 1, null, { tint: '#ff5a1a' }); sfx.howl(); }
      else if (id === 'glyphs') this.glyphs(3);
      else {
        const moon = id === 'moonwave';
        projectiles.push({ owner: 'enemy', kind: 'sc_ecres', x: this.x + this.face * 20, y: this.y - (moon ? 20 : 16), vx: this.face * (moon ? 250 : 220), vy: 0, dmg: scBossDmg(SC_EMBER_DMG.art, this), life: moon ? 1.1 : 0.95, r: moon ? 13 : 10, t: 0, id: ++hazardId, sh: 'fx_sc_ecres', face: this.face });
        (moon ? sfx.spear : sfx.heavySwing)();
      }
    }
    if (an.done) this.endString();
  }
  // ---- phase 2: it vanishes and reappears at your back. The tell: ember sparks gather behind you with a rising hiss.
  startBlink() {
    this.teleCool = rand(4.2, 6.5); this.blinkT = 0; this.state = 'blink'; this.vx = 0;
    spawnFx(fxOr('sc_eburst', 'hit'), this.x, this.y - 14, 1, null, { speed: 1.5 }); scAsh(this.x, this.y, 18, 'ember', 70);
    let tx = P.x - P.face * 24;
    if (tx < this.L - 6 || tx > this.R + 6 || solidAtPx(tx, P.y - 8)) tx = P.x + P.face * 24;
    this.blinkTo = clamp(tx, this.L - 6, this.R + 6); this.blinkY = P.y;
    noise(0.3, 2400, 1.2, 0.18, 'highpass', 0.5);
  }
  updateBlink(dt) {
    this.blinkT += dt;
    const tellStart = 0.12, tellEnd = 0.42;             // 0.30 s of sparks + sound at the spot before it appears
    if (this.blinkT < tellEnd) {
      if (this.blinkT > tellStart) {
        if (!this.tellSnd) { this.tellSnd = true; tone(330, 0.3, 0.07, 'sawtooth', 2.4); noise(0.3, 1200, 1, 0.2, 'bandpass', 2); }
        for (let i = 0; i < 3; i++) particles.push({ x: this.blinkTo + rand(-7, 7), y: this.blinkY - rand(0, 28), vx: rand(-15, 15), vy: -rand(10, 50), life: 0.35, kind: Math.random() < 0.5 ? 'ember' : 'fire' });
        addLight(this.blinkTo, this.blinkY - 14, 34 + 40 * (this.blinkT - tellStart), '255,120,50', 1);
      }
      return;
    }
    if (!this.appeared) {
      this.appeared = true; this.tellSnd = false; this.x = this.blinkTo; this.y = this.blinkY; this.vy = 0; this.facePlayer();
      spawnFx(fxOr('sc_eburst', 'hit'), this.x, this.y - 14, 1, null, { speed: 2 }); sfx.fire();
      const ms = this.moveset(), name = Math.random() < 0.5 ? ms.heavy : ms.combo[0], A = ATK[name] || ATK.attack1;
      this.startAtk(name, 1.1, 0); this.charge = 0; this.comboStep = A.kind === 'heavy' ? -1 : 0;
      this.appeared = false; return;
    }
  }
  hit(info) {
    if (!this.alive) return;
    if (!this.active) { this.activate(); return; }
    if (this.hidden || this.state === 'intro') return;
    if (this.iframes()) { if (Math.random() < 0.3) popup(this.x, this.y - 30, 0, '#a09080'); return; }
    if (this.state === 'parry' && this.parryT > 0 && info.melee && !info.crit) {
      // mirrored parry: your blow is turned, and it answers with your own riposte
      sfx.parry(); hitstop = 0.18; shake = 4;
      spawnFx(fxOr('parry_flash', 'parry_spark'), this.x + this.face * 12, this.y - 18, this.face, null, { tint: '#ff7a2a' });
      if (P.state !== 'dead') { setP('hurt', 'hurt'); P.vx = -P.face * 140; P.st = Math.max(0, P.st - 20); P.combo = 0; }
      this.parryT = 0; setTimeout(() => { if (this.alive && boss === this && this.state === 'parry') { this.startAtk('attack4', 0.9, 0.12); this.comboStep = -1; } }, 280);
      return;
    }
    if (this.guarding && info.melee && !info.crit && info.dir === -this.face) {
      // shield up: frontal blows are stopped; a heavy blow cracks the guard
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); hitstop = 0.06;
      P.vx = -P.face * 100; P.st = Math.max(0, P.st - 12);
      this.stance += info.poise * (info.kind === 'heavy' ? 0.9 : 0.35);
      if (this.arm.sig === 'frost' && typeof wAddFrost === 'function') for (let i = 0; i < 8; i++) particles.push({ x: P.x, y: P.y - 16, vx: rand(-40, 40), vy: -rand(10, 50), life: 0.4, kind: 'frost' });
      if (this.stance >= this.stanceMax && this.stanceImmune <= 0) { this.stagger(); return; }
      if (info.kind === 'heavy') { super.hit({ ...info, dmg: info.dmg * 0.5 }); return; }
      if (this.state !== 'atk' && Math.random() < 0.55) { this.facePlayer(); this.startAtk(this.sh.has('sh_counter') && ATK.sh_counter ? 'sh_counter' : 'sh_heavy', 1.05, 0.1); this.comboStep = -1; }
      return;
    }
    super.hit(info);
    if (this.alive && !['stagger', 'atk', 'art', 'blink'].includes(this.state) && info.poise > 60 && Math.random() < 0.35) { this.setA('recoil', 'hurt', false, 1); this.vx = info.dir * 90; }
  }
  updateEchoes(dt) {
    for (const e of this.echoes) {
      if (e.ghost) { e.life -= dt; continue; }
      e.at -= dt;
      if (e.at <= 0 && !e.done) {
        e.done = true; e.life = 0.3;
        sfx.swing(); spawnFx(fxOr(e.A.fx || 'slash', 'slash'), e.x + e.face * (e.A.fxAt ? e.A.fxAt[0] : 18), e.y + (e.A.fxAt ? e.A.fxAt[1] : -17), e.face, null, { tint: '#ff5a1a', alpha: 0.8 });
        if (overlap(this.atkRect(e.A, e.x, e.y, e.face), playerHurtbox())) this.hurt_(scBossDmg(30, this), e.face, e.id, true);
      }
      if (e.done) e.life -= dt;
    }
    this.echoes = this.echoes.filter(e => e.ghost ? e.life > 0 : !(e.done && e.life <= 0));
  }
  enterPhase2() {
    this.phase = 2; this.pendingPhase = false; this.stance = 0; this.speed = 1.1; this.teleCool = 2.5;
    this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.6; this.facePlayer();
    const mine = SAVE.weapon && WEAPONS[SAVE.weapon] && WEAPON_CLASS[SAVE.weapon] !== 'mirror' && this.clsOk(WEAPON_CLASS[SAVE.weapon]) ? SAVE.weapon : null;
    const was = this.wid;
    if (mine) this.equip({ wid: mine, sig: (SC_ARSENAL.find(a => a.wid === mine) || {}).sig });
    flashScreen = 0.7; shake = 10; sfx.roar(); sfx.fire();
    spawnFx(fxOr('sc_eburst', 'holy_burst'), this.x, this.y - 16, 1, null, { tint: '#ff6a2a' });
    scAsh(this.x, this.y, 30, 'ember', 90);
    const name = (WEAPONS[this.wid] || {}).name || 'your blade';
    if (!SAVE.flags['cutp2:first_ember']) {
      SAVE.flags['cutp2:first_ember'] = 1;
      const b = this, now = this.wid;
      playCutscene([
        { pan: { x: b.x, y: b.y - 40 }, dur: 0.5 },
        act(() => { b.wid = was; b.anim.set(b.sh.has('rest') ? 'rest' : 'hurt', false); flashScreen = 0.5; shake = 6; }), wait(0.7),
        act(() => { b.wid = now; b.flash = 1; flashScreen = 0.8; sfx.fire(); spawnFx(fxOr('sc_eburst', 'holy_burst'), b.x, b.y - 16, 1, null, { tint: '#ff6a2a' }); for (let i = 0; i < 40; i++) particles.push({ x: b.x + rand(-20, 20), y: b.y - rand(0, 40), vx: rand(-60, 60), vy: -rand(20, 120), life: rand(0.5, 1.2), kind: 'ember' }); }),
        say('', `It takes up ${name} — and every blade you have ever carried burns in its hands.`, { dur: 2.6 }),
        act(() => { b.anim.set(b.sh.has('rise') ? 'rise' : 'idle', false); }), wait(0.5),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ], () => { b.state = 'idle'; b.anim.set('idle', true); b.cool = 0.4; });
    } else toast(`The First Ember takes up ${name}. Its shape will not hold still.`, 3);
  }
  die() {
    this.state = 'dead'; this.anim.set('death', false, 0.8); this.echoes = []; this.hidden = false;
    hazards = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.8; flashScreen = 0.8; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE FIRST EMBER GOES OUT', t: 0 };
    SAVE.flags.true_ending = 1;
    this.rewards();
    SC_EPI.t = 11.5;
  }
  draw() {
    const wsh = this.wsheet();
    for (const e of this.echoes) {
      if (e.ghost) { drawSprite(this.sh, e.f, e.x, e.y, e.face, { alpha: e.life / 0.25 * 0.45, flash: 1, flashColor: e.red ? '#c02010' : '#3a1008' }); continue; }
      const a = e.done ? Math.max(0, e.life / 0.3) : 0.25 + 0.2 * Math.sin(time * 30);
      drawSprite(this.sh, e.f, e.x, e.y, e.face, { alpha: a * 0.7, flash: 1, flashColor: '#ff6a24' });
      drawSprite(wsh, e.f, e.x, e.y, e.face, { alpha: a * 0.7, flash: 1, flashColor: '#ffb060' });
    }
    if (this.hidden && !this.rising) return;
    const clipBottom = this.rising ? this.floor + 1 : undefined, Y = this.rising ? this.y + Math.round((1 - this.rise) * 30) : this.y;
    const alpha = this.state === 'dead' ? clamp(1 - (this.anim.done ? (this.deadT = (this.deadT || 0) + 1 / 60) : 0), 0, 1) : this.state === 'blink' ? clamp((this.blinkT - 0.42) * 8, 0, 1) : 1;
    const fl = this.flash > 0 ? { flash: this.flash * 0.45, flashColor: '#ff9a50' } : this.state === 'stagger' ? { flash: 0.2 + 0.1 * Math.sin(time * 20), flashColor: '#ffb040' } : this.state === 'rest' ? { flash: 0.15, flashColor: '#3a2020' } : {};
    const fr = this.anim.frame;
    if (alpha > 0) {
      if (!this.rising) scEmberRim(this.sh, fr, this.x, Y, this.face, alpha * (this.state === 'rest' ? 0.35 : 0.6 + 0.3 * Math.sin(time * 5)));
      scDrawEmberSprite(this.sh, fr, this.x, Y, this.face, { ...fl, alpha, clipBottom });
      scDrawEmberSprite(wsh, fr, this.x, Y, this.face, { weapon: true, crack: this.fireT > 0 || this.phase === 2 ? 1 : 0.8, alpha, clipBottom, seed: 2, ...(this.fireT > 0 ? { flash: 0.3, flashColor: '#ff6a24' } : {}) });
    }
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 40 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); g.fillRect(Math.round(this.x), y - 1, 1, 5); g.fillRect(Math.round(this.x) - 2, y + 1, 5, 1); }
    addLight(this.x, this.y - 16, this.phase === 2 ? 90 : 76, '255,110,50', this.state === 'rest' ? 0.5 : 1);
    if (this.state === 'parry' || this.state === 'guard') addLight(this.x + this.face * 10, this.y - 20, 30, '255,200,120', 1);
  }
}
if (typeof window !== 'undefined' && window.__game) window.__game.sc = { emberLog: scEmberLog, get epi() { return SC_EPI.t; } };
BOSS_SPAWN.first_ember = (cx, fy) => new FirstEmber(cx, fy);

// ================================================================== cutscenes
BOSS_CUTS.oswin = b => [
  act(() => { b.face = -1; b.anim.set(b.sh.has('sit') ? 'sit' : 'idle', true); }),
  bossPan(b, 34, 1.4),
  say('', 'An old pilgrim sits by the fire, his back to you.'),
  say('Oswin', 'Few find this place. Fewer leave it.'),
  act(() => { holdAnim(b, 'rise'); sfx.step(); }), wait(0.9),
  act(() => { b.facePlayer(); holdAnim(b, 'twirl'); sfx.swing(); setTimeout(() => sfx.swing(), 220); }), wait(1.1),
  say('Oswin', 'Come, then. Let us see what the ash has made of you.'),
];
BOSS_CUTS.champion = b => [
  act(() => { b.shown = true; b.y = b.floor - 200; b.anim.set(b.sh.has('leap') ? 'leap' : 'idle', false); b.anim.i = Math.min(4, b.anim.n - 1); b.anim.done = true; b.facePlayer(); }),
  { pan: { x: b.x, y: b.floor - 90 }, dur: 0.7 },
  { dur: 0.55, tween: (dt, k) => { b.y = lerp(b.floor - 200, b.floor, k * k); } },
  act(() => { b.y = b.floor; shake = 10; sfx.boom(); spawnFx('shockwave', b.x, b.floor, 1); scAsh(b.x, b.floor, 26, 'dust', 90); holdAnim(b, 'idle'); }), wait(0.5),
  say('', 'The last of the rampart’s champions. It has never lost.'),
  act(() => { holdAnim(b, 'salute'); sfx.glint(); }), wait(1.3),
];
BOSS_CUTS.sentinels = b => [
  act(() => { for (const q of b.parts) { q.face = P.x < q.x ? -1 : 1; q.anim.set('idle', true); } }),
  { pan: { x: b.x, y: b.y - 50 }, dur: 1.2 },
  say('', 'Two golden sentinels still guard a gate that fell long ago.'),
  act(() => { sfx.glint(); for (const q of b.parts) { spawnFx('telegraph', q.x + q.face * 20, q.y - 56, q.face); q.anim.set('thrust', false); } }), wait(0.9),
  act(() => { for (const q of b.parts) q.anim.set('idle', true); sfx.roar(); shake = 6; }), wait(0.6),
];
BOSS_CUTS.first_ember = b => {
  const R = SAVE.remnant && SAVE.remnant.room === room.id ? SAVE.remnant : null;
  const x0 = R ? clamp(R.x, b.L, b.R) : b.x;
  return [
    act(() => { b.x = x0; b.hidden = true; b.rising = false; b.face = P.x < b.x ? -1 : 1; }),
    { pan: { x: x0, y: b.floor - 40 }, dur: 1.4 },
    say('', R ? 'Where you fell, your ashes stir.' : 'The ashes stir. They remember a shape.'),
    act(() => { b.rising = true; b.rise = 0; b.anim.set('rest', false); b.anim.i = b.anim.n - 1; b.anim.done = true; sfx.fire(); shake = 3; }),
    { dur: 2.2, tween: (dt, k) => { b.rise = k; if (Math.random() < 0.9) particles.push({ x: b.x + rand(-10, 10), y: b.floor - rand(0, 30 * k), vx: rand(-10, 10), vy: -rand(20, 60), life: rand(0.5, 1.1), kind: 'ember' }); addLight(b.x, b.floor - 14, 50 + 30 * k, '255,110,50', 1); } },
    act(() => { b.rising = false; b.hidden = false; b.rise = 1; b.anim.set('rise', false); b.facePlayer(); }), wait(0.8),
    say('The First Ember', 'I burned before the Root. Before the grace. Before you.'),
    say('The First Ember', 'You wear my shape, little ash. Let me take it back.'),
    act(() => { b.anim.set('parry', false); sfx.glint(); flashScreen = 0.5; shake = 8; sfx.roar(); spawnFx(fxOr('sc_eburst', 'holy_burst'), b.x, b.y - 16, 1, null, { tint: '#ff6a2a' }); }), wait(1.0),
  ];
};
PHASE2_LINES.oswin = ['Oswin', 'Hm. Then I shall stop holding back the wind.'];
PHASE2_LINES.champion = ['', 'The Champion’s twin blades catch fire.'];

// ================================================================== the true epilogue
const SC_EPI = { t: 0 };
const SC_TRUE_END = [
  { img: 'sc_story_true_1', alt: 'story_end_ash', lines: ['The First Ember guttered out, and the Hollow went dark.', 'In the dark, something small and warm was left in your hand.'] },
  { img: 'sc_story_true_2', alt: 'story_end_kindle', lines: ['It was not grace, nor ash. It was the first spark — the one the Root was grown from.', 'You carried it up into the light, and the Hallow began, very slowly, to remember itself.'] },
  { img: 'sc_story_true_2', alt: 'story_end_kindle', lines: ['Venn named the new sapling after no one.', 'It was enough that it grew.'] },
];
function scPlayTrueEpilogue() {
  const slides = SC_TRUE_END.map(s => ({ img: sheet(s.img).ok ? s.img : s.alt, lines: s.lines }));
  SAVE.endings = SAVE.endings || {}; SAVE.endings.true = 1; SAVE.flags.true_epilogue = 1; saveGame();
  playCine(slides, () => { state = 'play'; clearBuffer(); toast('The true ending. The Hallow remembers.', 4.5); });
}

// ================================================================== hooks
HOOKS.enter.push(def => {
  if (scSyncSeal() && (def.id === 'R1' || def.id === 'H1')) renderRoomLayers(room);
  if (SAVE.flags.true_ending && !SAVE.flags.true_epilogue && SC_EPI.t <= 0) SC_EPI.t = 2.5;
  if (def.id === 'E3') { room.scUp = room.updrafts; room.scUpProps = props.filter(p => p.type === 'updraft'); room.dyn.push({ x0: 2 * TILE, x1: 5 * TILE, y0: -40, y1: 4, on: () => boss && boss.kind === 'first_ember' && boss.alive && boss.active }); }
});
HOOKS.update.push(dt => {
  if (!room) return;
  if (scSyncSeal() && (room.id === 'R1' || room.id === 'H1')) renderRoomLayers(room);
  // the banner in R4
  const bn = SC_GAUNT.banner;
  if (room.id === 'R4' && bn && props.includes(bn)) {
    if (!SC_GAUNT.active && !SAVE.flags['boss:champion'] && scNear(bn) && free() && P.ground && peek('interact')) { take('interact'); scStartGauntlet(bn); }
    scUpdateGauntlet(dt);
  }
  // E3: the updraft sleeps while the First Ember lives
  if (room.id === 'E3' && room.scUp) {
    const fight = boss && boss.kind === 'first_ember' && boss.alive && boss.active;
    room.updrafts = fight ? [] : room.scUp;
    const shown = props.some(p => p.type === 'updraft');
    if (fight && shown) props = props.filter(p => p.type !== 'updraft');
    else if (!fight && !shown) props.push(...room.scUpProps);
  }
  if (SC_EPI.t > 0 && (SC_EPI.t -= dt) <= 0 && state === 'play') scPlayTrueEpilogue();
});
HOOKS.hud.push(() => {
  if (state !== 'play' || !room) return;
  const bn = SC_GAUNT.banner;
  if (room.id === 'R4' && bn && props.includes(bn) && !SC_GAUNT.active && !SAVE.flags['boss:champion'] && scNear(bn) && free() && P.ground) scPrompt(bn, 'Sound the challenge');
  if (SC_GAUNT.active && room.id === 'R4' && !SC_GAUNT.champ) text(`The Champion’s Gauntlet  ·  ${Math.max(1, SC_GAUNT.wave)} / ${SC_WAVES.length}`, W / 2, 22, 6.5, '#e6c77a', 'center', { alpha: 0.9 });
});
