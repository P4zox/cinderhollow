// ------------------------------------------------------------------ THE NECROPOLIS OF VAEL (agent N)
// A vertical city of the dead beneath the Catacombs, entered through a grate in the Ossuary floor (C2) and a drowned sump
// (needs Tidebreath; B's deep-water tile '"'). Great bells toll on a timer: every toll swaps the bone walkways '{' (set A)
// and '}' (set B) and slides the bell-hung platforms. Pale-blue ghost-fire everywhere.
// Enemies: nv_noble (hollow noble fencer, parries), nv_ringer (bone-bell ringer: stunning toll), nv_hound (skeletal hound).
// Bosses: The Twin Executioners (duo mini-boss, NV5) and King Vael, the Hollow Crown (3 phases with his spectral court, NV7).
// Every top-level name is prefixed nv/NV (all region files share one scope).
Object.assign(AREAS, { necropolis: { name: 'The Necropolis of Vael', ambient: 0.47, amb: 'ghost', tint: '#05060c', map: '#44507e' } });
Object.assign(SCALES, { necropolis: [0, 1, 3, 5, 8] });
Object.assign(ROOTS, { necropolis: 41.2 });
Object.assign(PCOL, { nvghost: '150,200,255', nvsoul: '200,230,255', nvchain: '120,170,235' });

const NV_T_A = 50, NV_T_B = 51;
const NV_BLUE = ['#0d1a3a', '#173463', '#2c5a9c', '#4f8ad0', '#86baf0', '#c4e2ff', '#f2f9ff'];
const nvIn = () => room && (room.def.biome === 'necropolis' || room.def.biome === 'nv_void');
const nvSfx = {
  toll: (p = 1, v = 1) => { [98, 123.5, 147].forEach((f, i) => tone(f * p, 3.2, 0.16 * v, 'sine', 1, i * 0.03)); tone(49 * p, 3.4, 0.22 * v, 'triangle'); tone(196 * p * 1.007, 2.2, 0.05 * v, 'sine'); noise(0.4, 700, 0.8, 0.22 * v, 'bandpass', 0.4); },
  hum: () => { tone(98, 1.3, 0.05, 'sine', 1.02); tone(147, 1.2, 0.03, 'triangle', 1.01); },
  handbell: (p = 1) => { [660, 830, 990].forEach((f, i) => tone(f * p, 1.1, 0.07, 'sine', 1, i * 0.02)); tone(330 * p, 1.2, 0.08, 'triangle'); },
  ghost: () => { tone(420, 0.9, 0.06, 'sine', 0.6); tone(630, 0.7, 0.04, 'sine', 0.55, 0.05); noise(0.6, 1800, 0.8, 0.08, 'bandpass', 0.5); },
  chain: () => { for (let i = 0; i < 5; i++) tone(1400 + i * 170, 0.08, 0.04, 'square', 0.7, i * 0.035); noise(0.3, 3000, 1.2, 0.12, 'highpass', 0.5); },
  whoosh: () => noise(0.4, 1100, 0.6, 0.3, 'bandpass', 0.3),
  bone: () => { noise(0.12, 1500, 1, 0.3, 'bandpass', 0.5); tone(300, 0.08, 0.06, 'square', 0.6); },
};

// ================================================================== per-room state
const NVR = { roomObj: null };
function nvReset() {
  Object.assign(NVR, { roomObj: room, walks: [], bell: null, bells: [], plats: [], rings: [], waves: [], fires: [], chains: [], souls: [], swords: [], void: null,
    safe: null, stunT: 0, hints: {}, flash: 0 });
}
function nvEnsure() { if (NVR.roomObj !== room) nvReset(); }

// ================================================================== bell walkways ('{' set A, '}' set B)
registerTile('{', NV_T_A, { solid: true, draw() {} });
registerTile('}', NV_T_B, { solid: true, draw() {} });
function nvSetOn(w) { return NVR.bell ? (NVR.bell.phase === 0) === (w.set === 0) : w.set === 0; }
function nvWalkTag(w) {
  const m = room.def.map[w.y], L = m[w.x - 1] === m[w.x], R = m[w.x + 1] === m[w.x];
  return L && R ? 'm' : R ? 'l' : L ? 'r' : 's';
}
function nvBodyIn(r) {
  if (overlap(r, playerHurtbox())) return true;
  return enemies.some(e => e.alive && !e.cfg.flying && overlap(r, e.hurtbox() || r));
}
function nvUpdateWalks(dt) {
  for (const w of NVR.walks) {
    const want = nvSetOn(w), idx = w.y * room.w + w.x;
    if (!want && w.on) { w.on = false; room.grid[idx] = T_EMPTY; w.a = 1; for (let i = 0; i < 3; i++) particles.push({ x: w.x * TILE + rand(2, 14), y: w.y * TILE + rand(0, 6), vx: rand(-20, 20), vy: rand(10, 40), g: 200, life: rand(0.4, 0.8), kind: 'nvghost' }); }
    if (want && !w.on) {   // becomes solid only once nothing stands inside the cell (never traps a body)
      const r = rect(w.x * TILE, w.y * TILE - 1, w.x * TILE + 16, w.y * TILE + 16);
      if (!nvBodyIn(r)) { w.on = true; room.grid[idx] = w.set === 0 ? NV_T_A : NV_T_B; w.a = 0; }
    }
    w.a = w.on ? Math.min(1, w.a + dt * 5) : Math.max(0, w.a - dt * 4);
  }
}
function nvDrawWalks() {
  const sh = sheet('nv_walk'), b = NVR.bell, warn = b && b.t < b.warn;
  for (const w of NVR.walks) {
    const px = w.x * TILE, py = w.y * TILE, tag = nvWalkTag(w);
    if (px + 16 < cam.x || px > cam.x + W || py + 16 < cam.y || py > cam.y + H) continue;
    const leaving = warn && w.on, coming = warn && !w.on;
    if (w.on || w.a > 0.02) {
      let dx = 0, dy = 0;
      if (leaving) { dx = Math.round(rand(-1, 1) * 0.6); dy = Math.floor(time * 16) % 2; }
      const flash = leaving && Math.floor(time * 12) % 2 ? { flash: 0.45, flashColor: '#9fd0ff' } : {};
      if (sh.ok) drawSprite(sh, sh.first(tag), px + 8 + dx, py + 16 + dy, 1, { bottom: true, alpha: Math.max(w.a, 0.05), ...flash });
      else { g.globalAlpha = w.a; g.fillStyle = '#b8ab8c'; g.fillRect(px + dx, py + dy, 16, 6); g.globalAlpha = 1; }
    }
    if (!w.on) {   // the ghost of the bridge: a faint dotted outline, brighter just before it returns
      const a = coming ? 0.35 + 0.3 * Math.sin(time * 18) : 0.14;
      g.fillStyle = `rgba(140,190,255,${a})`;
      for (let i = (Math.floor(time * 8) + w.x) % 3; i < 16; i += 3) g.fillRect(px + i, py + 1, 1, 1);
      if (coming) { for (let i = 0; i < 16; i += 2) g.fillRect(px + i, py + 5, 1, 1); addLight(px + 8, py + 3, 18, '140,190,255', 0.4); }
    }
  }
}

// ================================================================== the great bells (room clock) + bell props
function nvToll() {
  const b = NVR.bell; if (!b) return;
  b.phase ^= 1; b.t = b.every; b.n++;
  nvSfx.toll(NVR.bells.length && NVR.bells[0].big ? 0.84 : 1);
  shake = Math.max(shake, 3); NVR.flash = 0.35;
  for (const bp of NVR.bells) { bp.anim.set(bp.sh.has('toll') ? 'toll' : 'idle', false); bp.swing = 1; NVR.rings.push({ x: bp.x, y: bp.y + bp.h * 0.7, r: 8, max: 420, speed: 260, harmless: true }); }
  for (const p of NVR.plats) p.go();
}
function nvUpdateBell(dt) {
  const b = NVR.bell; if (!b) return;
  if (boss && boss.active && boss.alive) return;
  const was = b.t;
  b.t -= dt;
  if (was >= b.warn && b.t < b.warn) { nvSfx.hum(); for (const bp of NVR.bells) bp.glow = 1; }
  if (b.t <= 0) nvToll();
}
SPAWNS.nv_bell = (s, c) => {
  nvEnsure();
  const big = !!s.big, sh = sheet(big ? 'nv_bell_big' : 'nv_bell');
  let top = s.y * TILE; while (top > 0 && !solidAtPx(c.cx, top - 1)) top -= TILE;
  const p = { type: 'nv_bell', x: c.cx, y: s.y * TILE + 8, top, big, sh, face: 1, h: big ? 56 : 40, swing: 0, glow: 0,
    anim: new Anim(sh, 'idle', true),
    update(dt) {
      this.swing = Math.max(0, this.swing - (dt || 1 / 60) * 0.35); this.glow = Math.max(0, this.glow - (dt || 1 / 60) * 0.5);
      if (this.anim.done) this.anim.set('idle', true);
      addLight(this.x, this.y + this.h * 0.5, big ? 70 : 50, '140,190,255', 0.45 + 0.4 * this.glow);
    },
    draw() {
      const ang = Math.sin(time * 5.5) * 0.16 * this.swing, sx = this.x + Math.sin(ang) * 6;
      g.fillStyle = '#2a2622'; g.fillRect(Math.round(this.x) - 1, this.top, 2, Math.max(0, this.y - this.top)); g.fillStyle = '#4a4238'; g.fillRect(Math.round(this.x), this.top, 1, Math.max(0, this.y - this.top));
      if (this.sh.ok) drawSprite(this.sh, this.anim.frame, sx, this.y, 1, { pivot: [Math.floor(this.sh.fw / 2), 0], rot: ang, flash: this.glow > 0 ? this.glow * 0.35 * (0.6 + 0.4 * Math.sin(time * 20)) : 0, flashColor: '#aee0ff' });
      else { g.fillStyle = '#6a5a3a'; g.beginPath(); g.moveTo(sx - 6, this.y); g.lineTo(sx + 6, this.y); g.lineTo(sx + 14, this.y + this.h); g.lineTo(sx - 14, this.y + this.h); g.fill(); }
    } };
  NVR.bells.push(p); props.push(p);
};

// ================================================================== bell-hung platforms (shift on each toll)
SPAWNS.nv_plat = (s, c) => {
  nvEnsure();
  const w = (s.w || 3) * TILE, x0 = s.x * TILE, y0 = s.y * TILE, dx = (s.dx || 6) * TILE;
  const d = { x0, x1: x0 + w, y0, y1: y0 + 7, on: () => true };
  const p = { type: 'nv_plat', x: x0 + w / 2, y: y0, face: 1, anim: { update() {} }, d, w, base: x0, dx, k: 0, from: 0, to: 0, t: 1, sh: sheet('nv_plat'),
    go() { this.from = this.k; this.to = this.to > 0.5 ? 0 : 1; this.t = 0; },
    move(dt) {
      if (this.t >= 1) return;
      this.t = Math.min(1, this.t + dt / 1.7);
      const e = this.t < 0.5 ? 2 * this.t * this.t : 1 - Math.pow(-2 * this.t + 2, 2) / 2;
      const nk = lerp(this.from, this.to, e), nx = this.base + nk * this.dx, ddx = nx - this.d.x0;
      if (!ddx) return;
      const riding = b => b.ground && Math.abs(b.y - this.d.y0) < 2 && b.x + (b.w || 10) / 2 > this.d.x0 && b.x - (b.w || 10) / 2 < this.d.x1;
      const riders = [P, ...enemies.filter(e => e.alive && !e.cfg.flying)].filter(riding);
      this.d.x0 = nx; this.d.x1 = nx + this.w; this.k = nk; this.x = nx + this.w / 2;
      for (const b of riders) { const side = b.x + sign(ddx) * ((b.w || 10) / 2 + 1); if (!isSolidT(tileAt(Math.floor((side + ddx) / TILE), Math.floor((b.y - 4) / TILE)))) b.x += ddx; }
      // never let the slab slide into a body: push it along
      const hb = playerHurtbox(), r = rect(this.d.x0, this.d.y0, this.d.x1, this.d.y1);
      if (!riders.includes(P) && overlap(hb, r)) P.x = ddx > 0 ? this.d.x1 + 5.5 : this.d.x0 - 5.5;
    },
    update(dt) { this.move(dt || 1 / 60); addLight(this.x, this.d.y0 + 2, 30, '140,190,255', 0.3); },
    draw() {
      const x = Math.round(this.d.x0), y = Math.round(this.d.y0);
      for (const cx of [x + 4, x + this.w - 5]) { let top = y; while (top > 0 && !solidAtPx(cx, top - 1)) top -= 4; g.fillStyle = '#3a3a44'; for (let yy = top; yy < y; yy += 3) g.fillRect(cx, yy, 1, 2); g.fillStyle = '#5a5a66'; for (let yy = top + 1; yy < y; yy += 3) g.fillRect(cx + 1, yy, 1, 1); }
      if (this.sh.ok) drawSprite(this.sh, 0, this.x, y + 12, 1, { bottom: true });
      else { g.fillStyle = '#b8ab8c'; g.fillRect(x, y, this.w, 7); g.fillStyle = '#6a6250'; g.fillRect(x, y + 5, this.w, 2); }
    } };
  room.dyn.push(d); NVR.plats.push(p); props.push(p);
};

// ================================================================== decor props
const NV_DECO = { candles: 'candles', skulls: 'skulls', brazier: 'brazier', statue: 'statue', coffin: 'coffin', banner: 'banner',
  block: 'block', gallows: 'gallows', throne: 'throne' };
SPAWNS.nv_prop = (s, c) => {
  nvEnsure();
  const tag = NV_DECO[s.kind]; if (!tag) return;
  const sh = sheet('nv_props'), hang = s.kind === 'banner';
  const p = { type: 'nv_' + s.kind, x: c.cx, y: hang ? s.y * TILE : c.fy, face: s.face || 1, sh, anim: new Anim(sh, sh.has(tag) ? tag : 'candles', true), hang };
  p.anim.t = rand(0, 500);
  if (s.kind === 'candles') p.update = () => !NVR.void && addLight(p.x, p.y - 8, 34 + Math.sin(time * 9 + p.x) * 2, '140,190,255', 0.7, LX_FLICKER);
  if (s.kind === 'brazier') p.update = () => { if (NVR.void) return; addLight(p.x, p.y - 26, 64 + Math.sin(time * 7 + p.x) * 3, '130,185,255', 0.9, LX_FLICKER); if (Math.random() < 0.25) particles.push({ x: p.x + rand(-4, 4), y: p.y - 24, vx: rand(-4, 4), vy: -rand(14, 30), life: rand(0.5, 1), kind: 'nvghost' }); };
  if (s.kind === 'throne') p.update = () => !NVR.void && addLight(p.x, p.y - 50, 60, '130,185,255', 0.5);
  if (s.kind === 'statue') p.update = () => !NVR.void && addLight(p.x, p.y - 38, 22, '130,185,255', 0.35);
  p.draw = () => { if (NVR.void) return; if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, p.face, hang ? { pivot: [Math.floor(sh.fw / 2), 0] } : { bottom: true }); };
  props.push(p);
};

// ================================================================== toll rings (bells, ringers, Vael) + stun
function nvRing(x, y, opt = {}) {
  NVR.rings.push({ x, y, r: 6, speed: opt.speed || 170, max: opt.max || 150, id: ++hazardId, dmg: opt.dmg || 0, src: opt.src || null, stun: opt.stun ?? 0.6, harmless: !opt.dmg, boss: !!opt.boss });
}
function nvUpdateRings(dt) {
  for (const r of NVR.rings) {
    r.r += r.speed * dt;
    if (r.harmless) continue;
    const d = Math.hypot(P.x - r.x, (P.y - 13) - r.y);
    if (Math.abs(d - r.r) < 8) {
      if (hurtPlayer((r.boss ? BOSS_DMG : 1) * r.dmg * NGP.dmg, sign(P.x - r.x), r.id, { src: r.src })) { if (r.stun) { NVR.stunT = Math.max(NVR.stunT, r.stun); toast('Stunned by the toll', 1.1); } }
    }
  }
  NVR.rings = NVR.rings.filter(r => r.r < r.max);
}
function nvDrawRings() {
  for (const r of NVR.rings) {
    const a = (1 - r.r / r.max) * (r.harmless ? 0.45 : 0.9), n = Math.ceil(r.r * 2 * Math.PI / 1.6);
    for (let k = 0; k < n; k++) {
      const t = k / n * Math.PI * 2, x = r.x + Math.cos(t) * r.r, y = r.y + Math.sin(t) * r.r * (r.harmless ? 1 : 0.9);
      g.fillStyle = `rgba(200,230,255,${a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1);
      if (k % 2 === 0) { g.fillStyle = `rgba(90,150,230,${a * 0.6})`; g.fillRect(Math.round(x - Math.cos(t) * 2), Math.round(y - Math.sin(t) * 2), 1, 1); }
    }
    if (!r.harmless) { addLight(r.x + r.r, r.y - 4, 22, '150,200,255', 0.4 * a); addLight(r.x - r.r, r.y - 4, 22, '150,200,255', 0.4 * a); }
  }
}

// ================================================================== room setup / hooks
HOOKS.enter.push(def => {
  nvEnsure();
  if (def.biome !== 'necropolis') return;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x];
    if (ch === '{' || ch === '}') NVR.walks.push({ x, y, set: ch === '{' ? 0 : 1, on: true, a: 1 });
  }
  if (def.bells) NVR.bell = { every: def.bells.every || 6, warn: def.bells.warn || 1.4, t: (def.bells.every || 6) * 0.8, phase: 0, n: 0 };
  for (const w of NVR.walks) if (!nvSetOn(w)) { w.on = false; w.a = 0; room.grid[w.y * room.w + w.x] = T_EMPTY; }
  if (def.id === 'NV1') nvSumpGrate(17, 19, 22);
});
// a bone grate over a pool: walk over it dry; swimmers rise through it (one-way, like the Archives' ink steps)
function nvSumpGrate(c0, c1, row) {
  const y0 = row * TILE, d = { x0: c0 * TILE, x1: (c1 + 1) * TILE, y0, y1: y0 + 5, oneway: true, on: () => P.drop <= 0 && P.y <= y0 + 0.5 };
  room.dyn.push(d);
  props.push({ type: 'nv_grate', x: (c0 + c1 + 1) * TILE / 2, y: y0, face: 1, anim: { update() {} },
    draw() {
      for (let x = d.x0; x < d.x1; x++) {
        const bar = (x - d.x0) % 4 === 0;
        g.fillStyle = bar ? '#cbbd98' : '#6f6550'; g.fillRect(x, y0, 1, bar ? 4 : 2);
        if (!bar) { g.fillStyle = '#2e2922'; g.fillRect(x, y0 + 2, 1, 1); }
      }
      g.fillStyle = '#ddd2b2'; g.fillRect(d.x0, y0, d.x1 - d.x0, 1);
    } });
}
HOOKS.update.push(dt => {
  nvEnsure();
  if (room.id === 'C2') nvGrateHint();
  if (!nvIn()) return;
  for (const p of particles) if (p.amb && p.kind === 'mote') { p.kind = 'nvghost'; p.vy = -Math.abs(p.vy || 4) * 0.6; }
  nvUpdateBell(dt); nvUpdateWalks(dt); nvUpdateRings(dt); nvUpdateSafe();
  NVR.flash = Math.max(0, NVR.flash - dt * 1.5);
  if (NVR.stunT > 0) { NVR.stunT -= dt; if (P.state !== 'dead') { P.vx *= Math.pow(0.02, dt); if (P.state !== 'hurt') setP('hurt', 'hurt'); P.anim.i = 0; P.anim.t = 0; } }
  if (room.id === 'NV1') nvSumpHints();
  nvUpdateHazards(dt);
});
HOOKS.render.push(() => {
  if (room && room.id === 'C2') nvDrawGrateMarker();
  if (!nvIn()) return;
  nvDrawWalks(); nvDrawRings(); nvDrawHazards();
});
HOOKS.renderTop.push(() => {
  if (!nvIn()) return;
  if (NVR.flash > 0) { g.fillStyle = `rgba(170,210,255,${NVR.flash * 0.18})`; g.fillRect(0, 0, W, H); }
  if (NVR.stunT > 0 && P) {
    const x = P.x - cam.x, y = P.y - cam.y - 32;
    for (let k = 0; k < 3; k++) { const a = time * 6 + k * 2.1; g.fillStyle = k % 2 ? '#9fd0ff' : '#e8f4ff'; g.fillRect(Math.round(x + Math.cos(a) * 9), Math.round(y + Math.sin(a) * 3), 2, 2); }
  }
});
// safe respawn spots never sit on a bell walkway or a hanging platform
function nvUpdateSafe() {
  if (!P.ground) { if (NVR.safe) P.safe = { ...NVR.safe }; return; }
  const ty = Math.floor((P.y + 1) / TILE), xs = [P.x - 4, P.x + 4].map(x => Math.floor(x / TILE));
  const ts = xs.map(tx => tileAt(tx, ty));
  const onDyn = NVR.plats.some(p => P.x > p.d.x0 - 6 && P.x < p.d.x1 + 6 && Math.abs(P.y - p.d.y0) < 2);
  const good = !onDyn && ts.every(t => t === T_PLAT || (isSolidT(t) && t !== NV_T_A && t !== NV_T_B)) && !nearSpikes();
  if (good) NVR.safe = { x: P.x, y: P.y };
  if (NVR.safe) P.safe = { ...NVR.safe };
}

// ================================================================== entrances: the Ossuary grate (C2) and the drowned sump (NV1)
function nvGrateHint() {
  // one ↓+Space carries you through both bars of the grate (rows 11 and 13)
  if (P.drop > 0 && P.x > 36 * TILE - 4 && P.x < 39 * TILE + 4 && P.y < 13 * TILE && P.y >= 11 * TILE) P.drop = Math.max(P.drop, 0.2);
  const on = P.ground && P.x > 36 * TILE && P.x < 39 * TILE && Math.abs(P.y - 11 * TILE) < 2;
  if (on && !NVR.grateHint) { NVR.grateHint = true; toast(matchMedia('(pointer: coarse)').matches ? 'A grate over a black stair. Hold ▼ and press Jump to drop through' : 'A grate over a black stair. Hold ↓ and press Space to drop through', 4); }
  if (!on && (P.x < 33 * TILE || P.x > 42 * TILE)) NVR.grateHint = false;
}
function nvDrawGrateMarker() {
  if (SAVE.visited && SAVE.visited.NV1 && Math.abs(P.x - 37.5 * TILE) > 90) return;
  const x = 37.5 * TILE, y = 11 * TILE - 22 + Math.sin(time * 4) * 3, a = 0.45 + 0.3 * Math.sin(time * 4);
  g.fillStyle = `rgba(150,200,255,${a})`;
  for (let i = 0; i < 4; i++) g.fillRect(Math.round(x - 4 + i), Math.round(y + i), 8 - i * 2, 1);
  g.fillRect(Math.round(x - 1), Math.round(y - 5), 2, 5);
  addLight(x, 11 * TILE, 26, '140,190,255', 0.4);
}
function nvSumpHints() {
  const H = NVR.hints;
  if (!H.water && P.y > 18 * TILE && P.x < 10 * TILE && P.ground) {
    H.water = true;
    toast(SAVE.items.tidebreath ? 'The sump is flooded to the vault. You can breathe the black water now.' : 'Black water fills the sump, down and under the wall. No lungs could hold that long.', 4.5);
  }
  if (!H.gate && P.x > 12 * TILE && P.x < 16 * TILE && P.y > 18 * TILE && P.ground && !SAVE.flags['lever:NV1']) { H.gate = true; toast('A gate of bone bars. Its lever is on the other side.', 3); }
}

// ================================================================== lore
Object.assign(LORE, {
  nv1: ['A grave cut into the sump wall. The name has been chiselled away:', '“He carried the King’s bells down the stair. When the water rose, he stayed with them.”'],
  nv2: ['A noble’s grave, gilt flaking from the bone:', '“Lady Aurel of the Charnel Gate. She asked to be buried facing the city, so she might watch it sleep.”'],
  nv3: ['A court grave. The epitaph is a list of titles, each one struck through but the last:', '“— Herald — Knight — Confessor — Headsman — Servant.”'],
  nv4: ['A small grave at the foot of the throne stair:', '“King Vael bound his court to him with chains of his own grief. They follow him still. So do the bells.”'],
});

// ================================================================== region hazards (ghost-fire, chains, soul waves) — shared by enemies and bosses
function nvUpdateHazards(dt) {
  for (const f of NVR.fires) {   // ghost-fire pillars: a floor sigil warns, then a column of pale flame
    f.t += dt;
    if (f.t >= f.warn && !f.lit) { f.lit = true; nvSfx.ghost(); shake = Math.max(shake, 2); for (let i = 0; i < 10; i++) particles.push({ x: f.x + rand(-6, 6), y: f.y - rand(0, 20), vx: rand(-20, 20), vy: -rand(40, 140), life: rand(0.4, 0.9), kind: 'nvghost' }); }
    if (f.lit && f.t < f.warn + f.dur) {
      addLight(f.x, f.y - 30, 60, '140,190,255', 0.9);
      if (overlap(rect(f.x - f.w / 2, f.y - f.h, f.x + f.w / 2, f.y), playerHurtbox())) hurtPlayer(BOSS_DMG * f.dmg * NGP.dmg, sign(P.x - f.x), f.id, { src: f.src });
      if (Math.random() < 0.7) particles.push({ x: f.x + rand(-f.w / 2, f.w / 2), y: f.y - rand(0, f.h), vx: rand(-8, 8), vy: -rand(40, 90), life: rand(0.3, 0.6), kind: 'nvsoul' });
    }
    if (f.t > f.warn + f.dur) f.done = true;
  }
  NVR.fires = NVR.fires.filter(f => !f.done);
  for (const w of NVR.waves) {   // soul waves sliding along the floor (low: jump them)
    w.t += dt; w.x += w.vx * dt; w.life -= dt;
    if (solidAtPx(w.x + sign(w.vx) * 6, w.y - 4) || !solidAtPx(w.x, w.y + 2)) w.life = 0;
    if (overlap(rect(w.x - 6, w.y - (w.h || 14), w.x + 6, w.y), playerHurtbox())) hurtPlayer(BOSS_DMG * w.dmg * NGP.dmg, sign(w.vx), w.id, { src: w.src });
    addLight(w.x, w.y - 8, 30, '140,190,255', 0.6);
    if (Math.random() < 0.8) particles.push({ x: w.x + rand(-4, 4), y: w.y - rand(0, 12), vx: -w.vx * 0.1, vy: -rand(20, 60), life: 0.45, kind: 'nvsoul' });
  }
  NVR.waves = NVR.waves.filter(w => w.life > 0);
  for (const s of NVR.souls) {   // homing soul bolts (priest, ghost-fire volleys)
    s.t += dt; s.life -= dt;
    if (s.t < (s.delay || 0)) { s.x = s.ox; s.y = s.oy; continue; }
    if (s.home && s.life > 0.4) { const a = Math.atan2(P.y - 14 - s.y, P.x - s.x), cur = Math.atan2(s.vy, s.vx); let d = a - cur; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; const na = cur + clamp(d, -s.home * dt, s.home * dt), sp = Math.hypot(s.vx, s.vy); s.vx = Math.cos(na) * sp; s.vy = Math.sin(na) * sp; }
    s.x += s.vx * dt; s.y += s.vy * dt;
    addLight(s.x, s.y, 26, '150,200,255', 0.8);
    if (Math.random() < 0.6) particles.push({ x: s.x, y: s.y, vx: rand(-10, 10), vy: rand(-10, 10), life: 0.3, kind: 'nvsoul' });
    if (overlap(rect(s.x - 4, s.y - 4, s.x + 4, s.y + 4), playerHurtbox()) && hurtPlayer(BOSS_DMG * s.dmg * NGP.dmg, sign(s.vx), s.id, { src: s.src, parryable: false })) s.life = 0;
    if (solidAtPx(s.x, s.y)) s.life = 0;
  }
  NVR.souls = NVR.souls.filter(s => s.life > 0);
  for (const c of NVR.chains) { c.t += dt; if (c.update) c.update(c, dt); }
  NVR.chains = NVR.chains.filter(c => !c.done);
  nvUpdateSwords(dt);
}
function nvDrawHazards() {
  for (const f of NVR.fires) {
    const k = clamp(f.t / f.warn, 0, 1);
    if (!f.lit) {   // warning sigil on the floor
      const pulse = 0.5 + 0.5 * Math.sin(time * 26);
      g.fillStyle = `rgba(120,180,255,${0.2 + 0.5 * k * pulse})`;
      g.beginPath(); g.ellipse(Math.round(f.x), Math.round(f.y) - 1, 4 + (f.w / 2) * k, 1.5 + k, 0, 0, 6.3); g.fill();
      g.fillStyle = `rgba(230,245,255,${0.6 * k})`; g.fillRect(Math.round(f.x) - 1, Math.round(f.y) - 2, 3, 1);
      addLight(f.x, f.y - 4, 20 + 20 * k, '140,190,255', 0.5 * k);
      continue;
    }
    const e = (f.t - f.warn) / f.dur, a = e < 0.15 ? e / 0.15 : 1 - Math.max(0, (e - 0.6) / 0.4);
    const sh = fxSheet('nv_pillar');
    if (sh.ok) { const t = sh.tag(Object.keys(sh.tags)[0]); drawSprite(sh, t.from + Math.min(t.to - t.from, Math.floor(e * (t.to - t.from + 1))), f.x, f.y, 1, { bottom: true, alpha: 0.95 }); }
    else {
      for (let y = 0; y < f.h; y += 2) { const wob = Math.sin(y * 0.3 + time * 20) * 2; g.fillStyle = `rgba(${y % 6 ? '120,180,255' : '220,240,255'},${0.75 * a})`; g.fillRect(Math.round(f.x - f.w / 2 + 2 + wob), Math.round(f.y - y - 2), f.w - 4, 2); }
      g.fillStyle = `rgba(240,250,255,${0.9 * a})`; g.fillRect(Math.round(f.x) - 1, Math.round(f.y - f.h), 3, f.h);
    }
  }
  for (const w of NVR.waves) {
    const x = Math.round(w.x), y = Math.round(w.y), hh = w.h || 14;
    for (let i = 0; i < hh; i += 2) { const ww = Math.max(1, 6 - i * 0.35); g.fillStyle = i < 4 ? 'rgba(220,240,255,0.95)' : 'rgba(110,170,250,0.8)'; g.fillRect(Math.round(x - ww / 2 + Math.sin(time * 30 + i) * 1.5), y - i - 2, Math.round(ww), 2); }
  }
  for (const s of NVR.souls) {
    if (s.t < (s.delay || 0)) { g.fillStyle = `rgba(160,210,255,${0.3 + 0.3 * Math.sin(time * 30)})`; g.fillRect(Math.round(s.x) - 2, Math.round(s.y) - 2, 4, 4); continue; }
    const x = Math.round(s.x), y = Math.round(s.y);
    g.fillStyle = NV_BLUE[2]; g.fillRect(x - 3, y - 2, 6, 5); g.fillRect(x - 2, y - 3, 4, 7);
    g.fillStyle = NV_BLUE[4]; g.fillRect(x - 2, y - 1, 4, 3);
    g.fillStyle = NV_BLUE[6]; g.fillRect(x - 1, y - 1, 2, 2);
    let px = x, py = y; g.fillStyle = NV_BLUE[3]; for (let k = 0; k < 5; k++) { px -= sign(s.vx) * rand(1, 3); py += rand(-1.5, 1.5); g.fillRect(Math.round(px), Math.round(py), 1, 1); }
  }
  for (const c of NVR.chains) if (c.draw) c.draw(c);
  nvDrawSwords();
}
function nvFire(x, floor, opt = {}) {
  NVR.fires.push({ x, y: floor, t: 0, warn: opt.warn ?? 0.9, dur: opt.dur ?? 0.55, w: opt.w ?? 20, h: opt.h ?? 96, dmg: opt.dmg ?? 36, id: ++hazardId, src: opt.src || boss });
}
function nvWave(x, floor, dir, opt = {}) {
  NVR.waves.push({ x, y: floor, vx: dir * (opt.speed || 170), life: opt.life || 2.6, t: 0, dmg: opt.dmg ?? 30, id: ++hazardId, src: opt.src || boss, h: opt.h || 14 });
}
function nvSoul(x, y, vx, vy, opt = {}) {
  NVR.souls.push({ x, y, ox: x, oy: y, vx, vy, t: 0, life: opt.life || 2.6, dmg: opt.dmg ?? 26, id: ++hazardId, src: opt.src || boss, home: opt.home || 0, delay: opt.delay || 0 });
}
function nvClearHazards() { NVR.fires = []; NVR.waves = []; NVR.souls = []; NVR.chains = []; NVR.swords = []; NVR.rings = NVR.rings.filter(r => r.harmless); }
function nvGroundY(x, y0, maxd = 300) {
  for (let y = Math.max(0, y0); y < Math.min(room.ph, y0 + maxd); y += 2) if (isSolidT(tileAt(Math.floor(x / TILE), Math.floor(y / TILE)))) return Math.floor(y / TILE) * TILE;
  return null;
}

// ================================================================== enemies
Object.assign(ENEMY, {
  nv_noble: { hp: 150, cinders: 170, speed: 56, aggro: 190, range: 76, poise: 18, stance: 75, dmg: { thrust: 30, flurry: 21 }, cool: [0.7, 1.4], lunge: { thrust: 210, flurry: 70 } },
  nv_ringer: { hp: 175, cinders: 180, speed: 30, aggro: 210, range: 140, poise: 30, stance: 90, dmg: { swing: 32, ring: 20 }, cool: [1.6, 2.6] },
  nv_hound: { hp: 95, cinders: 120, speed: 118, aggro: 210, range: 70, poise: 10, stance: 45, dmg: { bite: 24, lunge: 28 }, cool: [0.6, 1.2], lunge: { bite: 90, lunge: 240 } },
});
Object.assign(ATTACK_TAGS, { nv_noble: ['thrust', 'flurry'], nv_ringer: ['swing'], nv_hound: ['lunge', 'bite'] });

// ---- hollow noble: a fencer. Sometimes parries a light frontal blow and ripostes at once.
ENEMY_CLASSES.nv_noble = class extends Enemy {
  hit(info) {
    if (this.alive && ['idle', 'walk'].includes(this.state) && this.aggro && info.melee !== false && info.kind !== 'heavy' && !info.crit
        && info.dir === -this.face && info.kind !== 'spell' && Math.random() < 0.3 && this.sh.has('parry')) {
      sfx.parry(); hitstop = 0.08; spawnFx(fxOr('parry_flash', 'parry_spark'), info.x, info.y, info.dir);
      P.vx = -P.face * 110; P.st -= 14;
      this.setA('parry', 'parry', false); this.parryT = 0.35; return;
    }
    super.hit(info);
  }
  update(dt) {
    if (this.state === 'parry') {
      this.anim.update(dt); this.flash = Math.max(0, this.flash - dt * 5); this.gravity(dt);
      if (this.anim.done) { this.startAttack('thrust'); }
      return;
    }
    super.update(dt);
  }
};
// ---- bone-bell ringer: rings its hand-bell (a stunning toll ring), clubs you with it up close
ENEMY_CLASSES.nv_ringer = class extends Enemy {
  update(dt) {
    if (this.alive && this.aggro && this.cool <= 0 && ['idle', 'walk'].includes(this.state) && P.state !== 'dead') {
      const adx = Math.abs(P.x - this.x), ady = Math.abs(P.y - this.y);
      if (adx < 150 && (adx > 50 || Math.random() < 0.35) && ady < 70 && this.canSee() && this.sh.has('ring')) { this.startAttack('ring'); }
    }
    super.update(dt);
  }
  updateAttack(dt) {
    if (this.atk !== 'ring') return super.updateAttack(dt);
    const an = this.anim, sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.ring;
    if (an.i < (sp ? sp.frame : 5) - 1) this.facePlayer();
    if (an.changed && an.i === Math.max(0, (sp ? sp.frame : 5) - 3)) { const p = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x, y: this.y - 30 }; spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    if (!this.spawned && an.i >= (sp ? sp.frame : 5)) {
      this.spawned = true; const p = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 10, y: this.y - 30 };
      nvSfx.handbell(); nvRing(p.x, this.y - 22, { dmg: this.cfg.dmg.ring, src: this, speed: 150, max: 140, stun: 0.65 });
      for (let i = 0; i < 8; i++) particles.push({ x: p.x, y: p.y, vx: rand(-60, 60), vy: rand(-60, 30), life: 0.5, kind: 'nvghost' });
    }
    this.vx *= Math.pow(0.004, dt); this.gravity(dt);
    if (an.done) { this.setA('idle', 'idle'); this.cool = rand(...this.cfg.cool); }
  }
  draw() { super.draw(); if (this.alive) addLight(this.x + this.face * 8, this.y - 24, 26, '140,190,255', 0.45); }
};
// ---- skeletal hound: fast, low; lunges from range
ENEMY_CLASSES.nv_hound = class extends Enemy {
  draw() { super.draw(); if (this.alive) addLight(this.x + this.face * 10, this.y - 14, 16, '140,190,255', 0.4); }
};


// ================================================================== shared helpers for the necropolis bosses
function nvLead(sh, tag, upto, speed = 1) { const t = sh.tag(tag); let s = 0; for (let i = t.from; i < t.from + upto && i <= t.to; i++) s += sh.frames[i].ms; return s / 1000 / speed; }
function nvFirstActive(sh, tag) { const w = metaWindows(sh, tag); if (w.length) return w[0].active[0]; const sp = sh.meta && sh.meta.spawn && sh.meta.spawn[tag]; return sp ? sp.frame : 4; }
function nvLastActive(sh, tag) { const w = metaWindows(sh, tag); if (w.length) return w[w.length - 1].active[1]; const sp = sh.meta && sh.meta.spawn && sh.meta.spawn[tag]; return sp ? sp.frame : 5; }
function nvPick(w) { const e = Object.entries(w).filter(([, v]) => v > 0); if (!e.length) return null; let r = Math.random() * e.reduce((s, [, v]) => s + v, 0); for (const [k, v] of e) if ((r -= v) <= 0) return k; return e[0][0]; }
function nvHurtPart(q, info, B) {   // shared damage handling for duo/court parts (stance, one crit per stagger, bleed)
  const dmg = Math.round(info.dmg * (q.state === 'stagger' && !info.crit ? 1.3 : 1) * (q.dmgMul || 1));
  q.hp = Math.max(0, q.hp - dmg); q.flash = 1;
  q.dmgShown = q.dmgT > 0 ? q.dmgShown + dmg : dmg; q.dmgT = 2.2;
  if (B) { B.dmgShown = B.dmgT > 0 ? B.dmgShown + dmg : dmg; B.dmgT = 2.2; }
  hitstop = Math.max(hitstop, info.big ? 0.1 : 0.05); shake = Math.max(shake, info.big ? 4 : 2);
  (info.big ? sfx.bigHit : sfx.hit)();
  spawnFx(info.big ? fxOr('parry_spark', 'hit') : 'hit', info.x, info.y, info.dir);
  for (let i = 0; i < (info.big ? 10 : 5); i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 90), vy: -rand(20, 90), g: 260, life: rand(0.3, 0.6), kind: q.ghost ? 'nvsoul' : 'spark' });
  if (info.bleed) { q.bleed = (q.bleed || 0) + info.bleed * 0.7; if (q.bleed >= 100) { q.bleed = 0; const bd = Math.round(q.maxHp * 0.06 + 40); q.hp = Math.max(0, q.hp - bd); q.dmgShown += bd; sfx.bleed(); spawnFx(fxOr('bleed', 'blood'), info.x, info.y, info.dir); } }
  return dmg;
}

// ================================================================== THE TWIN EXECUTIONERS (NV5 mini-boss, duo)
BOSS_INFO.executioners = { name: 'The Twin Executioners', hp: 2000, cinders: 9500, reward: ['w:headsman_chain', 'shard'],
  quote: 'The King’s justice outlived the King’s reason.' };
const NV_EX = {
  a: { name: 'The Headsman', short: 'Headsman', sheet: 'executioner_a', eye: '255,120,90' },
  b: { name: 'The Gaoler', short: 'Gaoler', sheet: 'executioner_b', eye: '150,200,255' },
};
const NV_EX_MOVES = {
  chop: { dmg: [54], band: [0, 110], w: 2.4, shake: 8 },
  sweep: { dmg: [46], band: [0, 125], w: 2.0, shake: 4, step: 40 },
  chain: { dmg: [], band: [95, 300], w: 1.6, ranged: true },
  leap: { dmg: [58], band: [140, 999], w: 1.4, leap: true, shake: 9 },
  charge: { dmg: [44], band: [120, 400], w: 1.1, rush: true },
};
class NvExecutioner {
  constructor(B, who, x, y) {
    const T = NV_EX[who], meta = ASSETS.executioner_a_meta;
    Object.assign(this, { B, who, T, kind: 'executioners', boss: true, name: T.name, short: T.short, x, y, floor: y, face: who === 'a' ? 1 : -1,
      state: 'idle', cool: 1, t: 0, stance: 0, stanceMax: 240, flash: 0, dmgShown: 0, dmgT: 0, bleed: 0, critRange: 60, speed: 1,
      enraged: false, hitIds: new Set(), fired: {}, chain: 0, role: who === 'a' ? 'press' : 'flank', nextHitAt: -9, air: null, cds: {} });
    this.hp = this.maxHp = this.displayHp = Math.round(1000 * NGP.hp);
    this.sh = sheet(T.sheet, { meta }); this.anim = new Anim(this.sh, 'idle');
  }
  get alive() { return this.state !== 'dead'; }
  get L() { return this.B.L; }
  get R() { return this.B.R; }
  other() { return this.B.parts.find(q => q !== this); }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  setA(tag, loop = true, speed = this.speed) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  hurtbox() { if (!this.alive) return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 14, this.y - 60, this.x + 14, this.y); }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  onCritStart() { this.critDone = true; this.t = Math.max(this.t || 0, 0.9); }
  busy() { return (this.state === 'attack' && this.anim.i <= nvLastActive(this.sh, this.atk)) || ['charge', 'dash', 'ready', 'roar'].includes(this.state); }
  hit(info) {
    if (!this.alive) return;
    if (!this.B.active) { this.B.activate(); return; }
    nvHurtPart(this, info, this.B);
    if (this.hp <= 0) return this.die();
    if (info.crit) { this.stance = 0; this.t = Math.min(this.t || 0, 0.45); return; }
    if (this.stanceImmune > 0 || this.state === 'stagger' || this.air || this.state === 'roar') return;
    this.stance += info.poise;
    if (this.stance >= this.stanceMax && this.state !== 'charge') this.stagger();
  }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger') return; this.stance += 90; if (this.stance >= this.stanceMax) this.stagger(); }
  stagger() {
    this.critDone = false; this.stanceImmune = 7; this.stanceMax = Math.min(this.stanceMax * 1.15, 480);
    this.stance = 0; this.state = 'stagger'; this.setA('stagger', false, 1); this.t = 2.0; this.chain = 0; this.air = null; this.y = this.floor;
    sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 50, this.face);
    const o = this.other(); if (o && o.alive) { o.role = 'press'; o.cool = Math.min(o.cool, 0.5); this.role = 'flank'; }
    this.B.abortDuo();
  }
  die() {
    this.state = 'dead'; this.setA('death', false, 1); this.hp = 0; this.air = null; this.y = this.floor;
    shake = 10; hitstop = 0.25; slowmo = 1.0; flashScreen = 0.4; sfx.roar();
    this.B.partDown(this);
  }
  pickMove(d) {
    const e = this.enraged, flank = this.role === 'flank' && !e, w = {};
    for (const [k, M] of Object.entries(NV_EX_MOVES)) {
      if (d < M.band[0] || d > M.band[1] || (this.cds[k] > 0)) continue;
      let v = M.w;
      if (flank) v *= M.ranged || M.leap || M.rush ? 1.8 : 0.35;
      if (k === 'chain' && this.who === 'b') v *= 1.6;
      if (k === this.last) v *= 0.25;
      w[k] = v;
    }
    return nvPick(w) || 'walk';
  }
  lead(tag) { return nvLead(this.sh, tag, nvFirstActive(this.sh, tag), this.speed); }
  clashes(m) { const o = this.other(); if (!o || !o.alive || this.enraged) return false; const at = time + this.lead(m); return o.state === 'attack' && Math.abs(at - o.nextHitAt) < 0.35; }
  approachSpot() {
    const o = this.other();
    if (this.role === 'flank' && o && o.alive && !this.enraged) {
      let side = o.x < P.x ? 1 : -1, gx = P.x + side * 130;
      if (gx < this.L || gx > this.R) { side = -side; gx = P.x + side * 130; }
      return clamp(gx, this.L, this.R);
    }
    return clamp(P.x + (this.x < P.x ? -1 : 1) * 64, this.L, this.R);
  }
  start(m, opt = {}) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.spawned = false; this.air = null; this.y = this.floor;
    this.duo = opt.duo || null;
    if (m === 'walk') { this.state = 'walk'; this.goal = this.approachSpot(); this.t = rand(0.4, 0.7); this.setA('walk'); return; }
    if (m === 'charge') { this.state = 'charge'; this.setA('charge', true, 1.2); this.t = 1.3; this.cdir = this.face; this.cds.charge = 6; spawnFx('telegraph', this.x + this.face * 20, this.y - 50, this.face); sfx.glint(); nvSfx.whoosh(); return; }
    this.state = 'attack'; this.setA(m, false, this.speed);
    if (m === 'chain') this.cds.chain = this.who === 'b' ? 3.5 : 5;
    if (m === 'leap') this.cds.leap = 3.5;
    this.nextHitAt = time + this.lead(m);
  }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt; this.stance = Math.max(0, this.stance - dt * 5);
    if (this.state !== 'stagger') this.stanceImmune = Math.max(0, (this.stanceImmune || 0) - dt);
    this.bleed = Math.max(0, (this.bleed || 0) - dt * 5);
    for (const k in this.cds) this.cds[k] -= dt;
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    this.anim.update(dt);
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': {
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead' || this.B.duo || this.B.wantDuo) break;
        if (this.cool <= 0) { const m = this.pickMove(d); if (m !== 'walk' && this.clashes(m)) { this.cool = 0.1; break; } this.start(m); break; }
        const gx = this.approachSpot();
        if (Math.abs(gx - this.x) > 28) { this.state = 'walk'; this.goal = gx; this.t = 0.45; this.setA('walk'); }
        break;
      }
      case 'walk': {
        this.t -= dt; this.cool -= dt;
        const dir = sign(this.goal - this.x);
        this.x += dir * 46 * this.speed * dt; this.face = this.role === 'flank' && !this.enraged ? (P.x < this.x ? -1 : 1) : dir;
        if (this.anim.changed && this.anim.i % 4 === 0) { shake = Math.max(shake, 1); sfx.step(); }
        if (this.t <= 0 || Math.abs(this.goal - this.x) < 4 || this.cool <= 0) { this.state = 'idle'; this.setA('idle'); this.facePlayer(); }
        break;
      }
      case 'dash': {   // duo positioning
        const dir = sign(this.goal - this.x);
        this.x = approach(this.x, this.goal, 150 * dt); this.face = dir;
        if (this.anim.tag !== 'walk') this.setA('walk', true, 1.8);
        if (Math.abs(this.goal - this.x) < 3) { this.state = 'ready'; this.facePlayer(); this.setA('idle'); }
        break;
      }
      case 'ready': this.facePlayer(); break;
      case 'charge': {
        this.t -= dt;
        this.x += this.cdir * 225 * this.speed * dt;
        if (this.anim.changed && this.anim.i % 2 === 0) { shake = Math.max(shake, 2); sfx.step(); particles.push({ x: this.x - this.cdir * 20, y: this.y, vx: -this.cdir * 40, vy: -rand(10, 40), life: 0.5, kind: 'dust' }); }
        const r = rect(this.x + this.cdir * 4, this.y - 56, this.x + this.cdir * 30, this.y);
        if (!this.hitIds.has(0) && overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * 44 * (this.enraged ? 1.12 : 1) * NGP.dmg, this.cdir, this.atkId, { src: this })) { this.hitIds.add(0); P.vx = this.cdir * 190; }
        const past = (this.x - P.x) * this.cdir > 90;
        if (this.x <= this.L || this.x >= this.R) { this.x = clamp(this.x, this.L, this.R); shake = 8; sfx.boom(); spawnFx('shockwave', this.x + this.cdir * 26, this.y, 1); this.state = 'recover'; this.t = 0.9; this.setA('stagger', false, 1); }
        else if (this.t <= 0 || past) { this.state = 'idle'; this.setA('idle'); this.cool = rand(0.5, 0.9); }
        break;
      }
      case 'recover':
        this.t -= dt; if (this.anim.done) this.anim.hold();
        if (this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.2; }
        break;
      case 'roar':
        if (this.anim.changed && this.anim.i === 3) { sfx.roar(); shake = 8; flashScreen = 0.25; spawnFx('roar_ring', this.x + this.face * 10, this.y - 50, 1); }
        if (this.anim.done) { this.state = 'idle'; this.setA('idle'); this.cool = 0.3; }
        break;
      case 'attack': this.updateAttack(dt); break;
      case 'stagger':
        this.t -= dt;
        if (this.anim.i === this.anim.n - 1 && this.t > 0.3) this.anim.hold();
        if (this.anim.done || this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.3; }
        break;
      case 'dead': if (this.anim.done) this.anim.hold(); break;
    }
    if (this.state !== 'dead' && !this.air) this.x = clamp(this.x, this.L, this.R);
  }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, M = NV_EX_MOVES[a] || {}, wins = metaWindows(sh, a);
    const first = nvFirstActive(sh, a);
    if (an.i < first - 1 && !this.duo && a !== 'leap') this.facePlayer();
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    if (an.i > nvLastActive(sh, a)) this.nextHitAt = -9;
    // ---- leap: rise at meta.leap.rise, land at meta.leap.land, arc between (target clamped inside the arena)
    if (M.leap) {
      const L = sh.meta.leap || { rise: 3, land: 9 };
      if (an.changed && an.i === L.rise && !this.air) {
        const T = nvLead(sh, a, L.land, an.speed) - nvLead(sh, a, L.rise, an.speed);
        this.air = { x0: this.x, tx: clamp(P.x - this.face * 30, this.L, this.R), t: 0, T: Math.max(0.2, T) }; sfx.jump(); nvSfx.whoosh();
      }
      if (this.air) {
        this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
        this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * 78;
        if (k >= 1) { this.air = null; this.y = this.floor; }
      }
    }
    // ---- strikes
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (M.shake) shake = Math.max(shake, M.shake); }
      if (M.step) this.x = clamp(this.x + this.face * M.step * dt, this.L, this.R);
      if (this.hitIds.has(wi) || !w.hit) return;
      const r = metaRect(sh, this, w.hit);
      if (overlap(r, playerHurtbox())) {
        const dmg = (M.dmg ? (M.dmg[wi] ?? M.dmg[0]) : 40) * (this.enraged ? 1.12 : 1) * NGP.dmg;
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: a === 'sweep', src: this })) this.hitIds.add(wi);
      }
    });
    // ---- impacts + the chain
    const sp = sh.meta && sh.meta.spawn;
    if ((a === 'chop' || a === 'leap') && sp && sp[a] && an.i >= sp[a].frame && !this.fired.impact) {
      this.fired.impact = true; const at = metaPoint(sh, this, sp[a].at), x = clamp(at.x, this.L - 20, this.R + 20);
      sfx.boom(); shake = Math.max(shake, 8); spawnFx('shockwave', x, this.floor, 1);
      for (let i = 0; i < 14; i++) particles.push({ x: x + rand(-10, 10), y: this.floor - 2, vx: rand(-100, 100), vy: -rand(40, 160), g: 400, life: rand(0.4, 0.8), kind: 'rock' });
      if (a === 'leap' || this.enraged) for (const dd of [-1, 1]) nvWave(x, this.floor, dd, { speed: 175, dmg: 26, life: a === 'leap' ? 1.3 : 0.9, src: this, h: 10 });
    }
    if (a === 'chain' && sp && sp.chain && an.i >= sp.chain.frame && !this.fired.chain) { this.fired.chain = true; nvThrowShackle(this, metaPoint(sh, this, sp.chain.at)); }
    if (an.done) {
      this.air = null; this.y = this.floor; this.nextHitAt = -9;
      if (this.duo) { this.duo = null; this.state = 'recover'; this.setA('idle', true, 0.6); this.t = 0.8; return; }
      const e = this.enraged, d = Math.abs(P.x - this.x);
      if (this.chain < (e ? 2 : 1) && Math.random() < (e ? 0.7 : 0.4) && !this.B.duo && !this.B.wantDuo && P.state !== 'dead') {
        const nx = d < 110 ? (a === 'chop' ? 'sweep' : 'chop') : d < 280 ? 'chain' : 'leap';
        if (nx !== a && !this.clashes(nx) && !(this.cds[nx] > 0)) { this.chain++; return this.start(nx); }
      }
      const long = this.chain >= 1; this.chain = 0;
      this.state = long ? 'recover' : 'idle'; this.setA('idle', true, long ? 0.6 : 1); this.t = long ? (e ? 0.6 : 0.9) : 0;
      this.cool = e ? rand(0.25, 0.55) : this.role === 'flank' ? rand(0.6, 1.1) : rand(0.4, 0.8);
    }
  }
  draw() {
    if (!this.sh.ok) { g.fillStyle = this.who === 'a' ? '#5a2a26' : '#2a2a34'; g.fillRect(Math.round(this.x - 14), Math.round(this.y - 60), 28, 60); return; }
    if (this.state === 'dead' && this.anim.done) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' }
      : this.state === 'ready' ? { flash: 0.12 + 0.1 * Math.sin(time * 30), flashColor: '#ffcaa0' } : this.enraged ? { flash: 0.08 + 0.05 * Math.sin(time * 9), flashColor: '#ff6040' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
  }
  light() { if (this.alive) { addLight(this.x + this.face * 8, this.y - 52, 36, this.T.eye, 0.5); addLight(this.x, this.y - 30, 70, '150,170,210', 0.35); } }
}
// the thrown shackle chain: flies along the floor-ish line; a hit binds and yanks the player in front of the thrower
function nvThrowShackle(q, at, opt = {}) {
  const dir = q.face, tipY = clamp(P.y - 14, q.floor - 40, q.floor - 8), spectral = !!opt.spectral;
  nvSfx.chain(); if (spectral) nvSfx.ghost();
  NVR.chains.push({ src: q, x0: at.x, y0: at.y, x: at.x, y: at.y, ty: tipY, dir, len: 0, max: opt.max || 250, st: 'out', id: ++hazardId, t: 0, spectral,
    update(c, dt) {
      if (!q.alive || q.state === 'stagger') { c.done = true; return; }
      if (c.st === 'out') {
        c.len += 520 * dt; c.x = c.x0 + dir * c.len; c.y = lerp(c.y0, c.ty, Math.min(1, c.len / 90));
        if (solidAtPx(c.x, c.y) || c.x < q.L - 40 || c.x > q.R + 40) c.st = 'back';
        if (overlap(rect(c.x - 5, c.y - 5, c.x + 5, c.y + 5), playerHurtbox())) {
          if (hurtPlayer(BOSS_DMG * (opt.dmg || 22) * NGP.dmg, -dir, c.id, { src: q })) { c.st = 'pull'; c.t = 0; P.vx = 0; toast(spectral ? 'Bound by the King’s chain!' : 'Shackled!', 1.1); if (opt.onHit) opt.onHit(); else if (q.B && q.B.onShackle) q.B.onShackle(q); }
          else if (P.inv > 0 || iframes()) {}   // rolled through it
        }
        if (c.len >= c.max) c.st = 'back';
      } else if (c.st === 'pull') {   // yank the player toward the thrower
        c.t += dt; const tx = q.x + dir * 58;
        if (P.state !== 'dead') { P.x = approach(P.x, clamp(tx, q.L - 30, q.R + 30), 420 * dt); P.vx = 0; if (!solidAtPx(P.x + sign(tx - P.x) * 6, P.y - 8)) {} if (P.state !== 'hurt') setP('hurt', 'hurt'); }
        c.x = P.x; c.y = P.y - 14; c.len = Math.abs(c.x - c.x0);
        if (c.t > 0.35 || Math.abs(P.x - tx) < 4) { c.st = 'back'; NVR.stunT = Math.max(NVR.stunT, 0.25); }
      } else { c.len -= 700 * dt; c.x = c.x0 + dir * Math.max(0, c.len); if (c.len <= 0) c.done = true; }
    },
    draw(c) {
      const n = Math.max(1, Math.floor(Math.abs(c.x - c.x0) / 3));
      for (let i = 0; i <= n; i++) {
        const k = i / n, x = lerp(c.x0, c.x, k), y = lerp(c.y0, c.y, k) + Math.sin(k * Math.PI) * 4 * (c.st === 'out' ? 1 : 0.3);
        g.fillStyle = c.spectral ? (i % 2 ? '#2c5a9c' : '#86baf0') : (i % 2 ? '#3a3a44' : '#8a8a96'); g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 3, 2);
        if (i % 2 === 0) { g.fillStyle = c.spectral ? '#e4f3ff' : '#c8c8d0'; g.fillRect(Math.round(x), Math.round(y) - 1, 1, 1); }
        if (c.spectral && i % 4 === 0) addLight(x, y, 16, '140,190,255', 0.35);
      }
      g.fillStyle = c.spectral ? '#86baf0' : '#5a5a66'; g.fillRect(Math.round(c.x) - 3, Math.round(c.y) - 3, 6, 6); g.fillStyle = c.spectral ? '#f2f9ff' : '#1a1a22'; g.fillRect(Math.round(c.x) - 1, Math.round(c.y) - 1, 2, 2);
    } });
}
class NvExecutioners extends BossBase {
  constructor(x, y) {
    super('executioners', x, y);
    this.parts = [new NvExecutioner(this, 'a', x - 40, y), new NvExecutioner(this, 'b', x + 40, y)];
    this.hp = this.maxHp = this.displayHp = this.parts.reduce((s, q) => s + q.maxHp, 0);
    this.sh = this.parts[0].sh; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant'; this.duoT = rand(6, 8);
  }
  get L() { return 2 * TILE + 26; }
  get R() { return 34 * TILE - 26; }
  canStagger() { return false; }
  hurtbox() { return null; }
  get alivePs() { return this.parts.filter(q => q.alive); }
  facePlayer() { for (const q of this.parts) if (q.alive) q.facePlayer(); this.face = P.x < this.x ? -1 : 1; }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt;
    this.hp = this.parts.reduce((s, q) => s + q.hp, 0);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    if (this.state === 'dead') { this.anim.update(dt); for (const q of this.parts) q.update(dt); return; }
    if (!this.active) {
      for (const q of this.parts) { q.anim.update(dt); if (!this.cutting) q.facePlayer(); }
      if (!this.cutting && P.x < 31 * TILE && P.state !== 'dead') this.activate();
      this.track(); return;
    }
    if (this.state !== 'fight') { this.state = 'fight'; for (const q of this.parts) { q.state = 'idle'; q.setA('idle'); q.facePlayer(); q.cool = q.who === 'a' ? 0.5 : 1.0; } }
    const live = this.alivePs;
    if (live.length === 2) {
      this.roleT = (this.roleT || 6) - dt;
      if (this.roleT <= 0 && !this.duo) { this.roleT = rand(5, 7); for (const q of this.parts) q.role = q.role === 'press' ? 'flank' : 'press'; }
      if (!this.duo) {
        this.duoT -= dt;
        if (this.duoT <= 0) this.wantDuo = (this.wantDuo || 0) + dt;
        if (this.wantDuo && P.state !== 'dead' && live.every(q => ['idle', 'walk', 'recover'].includes(q.state) || (q.state === 'attack' && q.anim.i > nvLastActive(q.sh, q.atk)))) { this.wantDuo = 0; this.startDuo(); }
        else if (this.wantDuo > 3) { this.wantDuo = 0; this.duoT = 2; }
      } else this.updateDuo(dt);
    }
    for (const q of this.parts) q.update(dt);
    this.track();
  }
  // duo technique: the two flank the player and fall on them in turn (chop then sweep, 0.45 s apart)
  startDuo() {
    const [a, b] = this.parts, roomL = P.x - this.L, roomR = this.R - P.x;
    const two = Math.min(roomL, roomR) >= 90;
    let side = a.x < P.x ? -1 : 1, ax, bx;
    if (two) { ax = P.x + side * 80; bx = P.x - side * 80; } else { side = roomL > roomR ? -1 : 1; ax = P.x + side * 70; bx = P.x + side * 150; }
    ax = clamp(ax, this.L, this.R); bx = clamp(bx, this.L, this.R);
    this.duo = { st: 'move', t: 0, kind: two ? 'cross' : 'line' };
    a.goal = ax; b.goal = bx;
    for (const q of this.parts) { q.state = 'dash'; q.chain = 0; }
    toast(two ? 'The executioners close in from both sides…' : 'The executioners bear down on you…', 1.4);
  }
  abortDuo() { this.wantDuo = 0; if (!this.duo) return; this.duo = null; this.duoT = rand(6, 8); for (const q of this.parts) if (q.alive && ['dash', 'ready'].includes(q.state)) { q.state = 'idle'; q.setA('idle'); q.cool = 0.3; } }
  updateDuo(dt) {
    const du = this.duo, [a, b] = this.parts;
    if (!a.alive || !b.alive) { this.abortDuo(); return; }
    du.t += dt;
    if (du.st === 'move') {
      if ((a.state === 'ready' && b.state === 'ready') || du.t > 1.5) { du.st = 'tell'; du.t = 0; for (const q of this.parts) { q.state = 'ready'; q.facePlayer(); } sfx.glint(); flashScreen = 0.1; }
    } else if (du.st === 'tell') {
      if (!du.a && du.t >= 0.4) { du.a = true; a.start('chop', { duo: true }); }
      if (!du.b && du.t >= 0.4 + a.lead('chop') + 0.45 - b.lead('sweep')) { du.b = true; b.start(du.kind === 'cross' ? 'sweep' : 'chain', { duo: true }); }
      for (const q of this.parts) if (q.state === 'ready') q.facePlayer();
      if (du.a && du.b) du.st = 'strike';
    } else if (du.st === 'strike') { if (a.state !== 'attack' && b.state !== 'attack') { this.duo = null; this.duoT = rand(7, 10); } }
  }
  onShackle(q) {   // a shackled player invites the other headsman's leap
    const o = q.other(); if (o && o.alive && ['idle', 'walk'].includes(o.state) && !this.duo) { o.cds.leap = 0; o.start(Math.abs(P.x - o.x) > 140 ? 'leap' : 'chop'); }
  }
  track() {
    const live = this.alivePs; if (!live.length) return;
    let near = live[0]; for (const q of live) if (Math.abs(q.x - P.x) < Math.abs(near.x - P.x)) near = q;
    this.x = near.x; this.y = this.floor;
    const mid = live.reduce((s, q) => s + q.x, 0) / live.length;
    this.camX = Math.abs(live[0].x - (live[1] || live[0]).x) > 300 ? near.x : mid;
  }
  partDown(q) {
    const o = q.other(); this.abortDuo();
    if (!(o && o.alive)) return this.die();
    this.phase = 2; o.enraged = true; o.role = 'press'; o.speed = 1.2; o.stance = 0; o.chain = 0; o.air = null; o.y = o.floor;
    o.state = 'roar'; o.setA('roar', false, 1); o.facePlayer();
    toast(o.who === 'a' ? 'The Headsman roars over his brother’s corpse.' : 'The Gaoler rattles its chains in fury.', 2.4);
  }
  die() {
    this.state = 'dead'; this.hp = 0; this.anim = new Anim(this.parts[0].sh, 'death', false);
    nvClearHazards(); projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'JUSTICE IS DONE', t: 0 };
    this.rewards();
  }
  ambient(dt) {
    if (state === 'cut') for (const q of this.parts) { q.flash = Math.max(0, q.flash - dt * 5); q.anim.update(dt); if (q.anim.done && q.cutTag && q.cutTag !== 'idle') { q.cutTag = null; q.setA('idle'); } }
    for (const q of this.parts) q.light();
  }
  draw() {
    const shadow = (x, w) => { g.fillStyle = 'rgba(6,4,10,0.5)'; g.beginPath(); g.ellipse(Math.round(x), Math.round(this.floor) + 1, w, 2.5, 0, 0, 6.3); g.fill(); };
    for (const q of this.parts) if (!(q.state === 'dead' && q.anim.done) && q.x !== this.x) shadow(q.x, q.air ? 12 : 20);
    for (const q of this.parts) if (q.state === 'dead') q.draw();
    for (const q of this.parts) if (q.state !== 'dead') q.draw();
    for (const q of this.parts) q.light();
  }
}
BOSS_SPAWN.executioners = (cx, fy) => new NvExecutioners(cx, fy);
BOSS_CUTS.executioners = b => {
  const [a, q] = b.parts, mid = (a.x + q.x) / 2;
  const play = (p, tag) => { p.setA(tag, tag === 'idle' || tag === 'walk'); p.cutTag = tag; };
  return [
    act(() => { a.face = 1; q.face = -1; play(a, 'idle'); play(q, 'idle'); b.track(); }),
    { pan: { x: mid, y: b.floor - 50 }, dur: 1.0 },
    say('', 'Two headsmen still keep the King’s justice in his empty yard.'),
    act(() => { play(q, 'chain'); nvSfx.chain(); }), wait(0.9),
    act(() => { a.facePlayer(); q.facePlayer(); play(a, 'roar'); play(q, 'roar'); }), wait(0.5),
    act(() => { sfx.roar(); shake = 8; flashScreen = 0.25; }), wait(1.0),
  ];
};
HOOKS.hud.push(() => {
  if (!boss || !boss.active || !boss.alive || state === 'cut') return;
  const bx = 156, by = 203, bw = 216;
  if (boss.kind === 'executioners') {
    const hw = bw / 2 - 4;
    boss.parts.forEach((q, i) => {
      const x = bx + i * (hw + 8);
      bar(x, by + 5, hw, 2, Math.max(0, q.hp) / q.maxHp, q.displayHp / q.maxHp, i === 0 ? '#9a3a2a' : '#5a6a8a');
      text(q.short + (q.alive ? '' : ' †'), i === 0 ? x : x + hw, by + 12, 5, i === 0 ? '#e0a090' : '#b0c0e0', i === 0 ? 'left' : 'right');
    });
  }
  if (boss.kind === 'vael' && boss.court) {
    const live = boss.court; const n = live.length; if (!n) return;
    const hw = (bw - (n - 1) * 6) / n;
    live.forEach((q, i) => {
      const x = bx + i * (hw + 6);
      bar(x, by + 5, hw, 2, Math.max(0, q.hp) / q.maxHp, q.displayHp / q.maxHp, q.alive ? '#6aa0e0' : '#2a3040');
      text(q.short + (q.alive ? '' : ' †'), x, by + 12, 5, q.alive ? '#b8d8ff' : '#5a6070', 'left');
    });
  }
});

// ================================================================== KING VAEL, THE HOLLOW CROWN (NV7) — 3 phases with his spectral court
BOSS_INFO.vael = { name: 'King Vael, the Hollow Crown', hp: 3800, cinders: 19000, reward: ['w:vael_greatsword', 'sp:soul_chains', 'c_crown'],
  quote: '“A king is only the grief his court agrees to carry.”' };
const NV_VB = new Set(['leap', 'chain', 'ghostfire', 'rain', 'nova', 'summon', 'absorb', 'rise']);
const NV_VM = {
  combo: { dmg: [44, 44, 58], parry: [true, true, false], band: [0, 150], w: 2.2 },
  string: { dmg: [40, 40, 44, 48, 62], parry: [true, true, true, false, false], band: [0, 140], w: 1.6 },
  spin: { dmg: [52], band: [0, 125], w: 1.1 },
  overhead: { dmg: [70], band: [30, 170], w: 1.3 },
  thrust: { dmg: [54], parry: [true], band: [100, 250], w: 1.5, lunge: [3, 4], dist: 120 },
  charge: { dmg: [48], band: [160, 430], w: 1.1, cd: 5 },
  leap: { dmg: [62], band: [220, 999], w: 1.2, cd: 4 },
  chain: { band: [150, 330], w: 1.3, cd: 5 },
  ghostfire: { band: [110, 999], w: 1.2, cd: 6 },
  rain: { band: [0, 999], w: 1.1, cd: 9, ph: 2 },
  nova: { band: [0, 190], w: 1.3, cd: 7, ph: 3 },
};
const NV_COURT = {
  knight: { name: 'Spectral Knight', short: 'Knight', sheet: 'vael_knight', hp: 420, walk: 58, prefer: 50, stance: 120, moves: { slash: { dmg: [36], band: [0, 80], w: 2.2 }, bash: { dmg: [28], band: [0, 70], w: 1.2, step: 70 } } },
  priest: { name: 'Spectral Confessor', short: 'Confessor', sheet: 'vael_priest', hp: 320, walk: 40, prefer: 180, stance: 90, moves: { cast: { band: [0, 999], w: 2 }, ward: { band: [0, 999], w: 0 } } },
  exec: { name: 'Spectral Headsman', short: 'Headsman', sheet: 'vael_exec', hp: 520, walk: 38, prefer: 64, stance: 160, moves: { chop: { dmg: [50], band: [0, 95], w: 2, shake: 6 }, sweep: { dmg: [42], band: [0, 110], w: 1.4 } } },
};
class NvCourtier {
  constructor(V, kind, x, y) {
    const C = NV_COURT[kind];
    Object.assign(this, { V, kind, C, name: C.name, short: C.short, boss: true, ghost: true, x, y, floor: y, face: P.x < x ? -1 : 1, state: 'appear',
      cool: rand(1.0, 1.8), t: 0, stance: 0, stanceMax: C.stance, flash: 0, dmgShown: 0, dmgT: 0, critRange: 44, speed: 1, hitIds: new Set(),
      fired: {}, nextHitAt: -9, wardT: rand(6, 8), alpha: 0 });
    this.hp = this.maxHp = this.displayHp = Math.round(C.hp * NGP.hp);
    this.sh = sheet(C.sheet); this.anim = new Anim(this.sh, 'appear', false);
  }
  get alive() { return this.state !== 'dead'; }
  get L() { return this.V.L; }
  get R() { return this.V.R; }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  setA(tag, loop = true, speed = this.speed) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  hurtbox() { if (!this.alive || this.state === 'appear' || this.state === 'absorbed') return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 8, this.y - 44, this.x + 8, this.y); }
  critable() { return this.state === 'stagger' && !this.critDone; }
  onCritStart() { this.critDone = true; this.t = Math.max(this.t || 0, 0.9); }
  hit(info) {
    if (!this.alive || this.state === 'appear' || this.state === 'absorbed') return;
    nvHurtPart(this, info, null);
    if (this.hp <= 0) return this.die();
    if (info.crit) { this.stance = 0; this.t = Math.min(this.t || 0, 0.45); return; }
    if (this.state === 'stagger') return;
    this.stance += info.poise;
    if (this.stance >= this.stanceMax) { this.stance = 0; this.critDone = false; this.state = 'stagger'; this.setA('hurt', false, 0.35); this.t = 1.5; sfx.glint(); if (this.kind === 'priest') this.channel = false; }
  }
  onParried() { if (this.state === 'stagger') return; this.stance += 70; if (this.stance >= this.stanceMax) { this.stance = 0; this.critDone = false; this.state = 'stagger'; this.setA('hurt', false, 0.35); this.t = 1.5; } }
  die() {
    this.state = 'dead'; this.setA('death', false, 1); nvSfx.ghost(); shake = 5; flashScreen = 0.15;
    for (let i = 0; i < 24; i++) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(0, 44), vx: rand(-40, 40), vy: -rand(20, 90), life: rand(0.6, 1.2), kind: 'nvsoul' });
    toast(`${this.name} fades.`, 1.6);
  }
  lead(tag) { return nvLead(this.sh, tag, nvFirstActive(this.sh, tag), this.speed); }
  start(m) {
    this.facePlayer(); this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {};
    if (m === 'walk') { this.state = 'walk'; this.t = rand(0.4, 0.8); this.setA('walk'); return; }
    this.state = 'attack'; this.setA(m, false, this.speed); this.nextHitAt = time + this.lead(m);
  }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt; this.stance = Math.max(0, this.stance - dt * 5);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    this.anim.update(dt); this.alpha = Math.min(1, this.alpha + dt * 1.5);
    const d = Math.abs(P.x - this.x), V = this.V;
    switch (this.state) {
      case 'appear': if (this.anim.done) { this.state = 'idle'; this.setA('idle'); } return;
      case 'absorbed': return;
      case 'idle': {
        this.facePlayer(); this.cool -= dt;
        if (this.kind === 'priest') { this.wardT -= dt; }
        if (P.state === 'dead' || V.state === 'summon' || V.state === 'absorb') break;
        if (this.cool <= 0) {
          if (this.kind === 'priest') {
            if (this.wardT <= 0 && V.alive && !(V.ward > 0)) { this.wardT = rand(10, 13); this.start('ward'); break; }
            if (d > 60) { this.start('cast'); break; }
          } else {
            const w = {};
            for (const [k, M] of Object.entries(this.C.moves)) if (M.w && d >= M.band[0] && d <= M.band[1]) w[k] = M.w * (k === this.last ? 0.3 : 1);
            const m = nvPick(w);
            // the court takes turns: one courtier strikes at a time, never on the same beat as the King
            if (m && !V.court.some(q => q !== this && q.alive && q.kind !== 'priest' && q.state === 'attack') && Math.abs(time + this.lead(m) - V.nextHitAt) > 0.35) { this.last = m; this.start(m); break; }
          }
        }
        const want = this.kind === 'priest' ? this.priestSpot() : clamp(P.x + (this.x < P.x ? -1 : 1) * this.C.prefer, this.L, this.R);
        if (Math.abs(want - this.x) > 16) { this.state = 'walk'; this.goal = want; this.t = 0.5; this.setA('walk'); }
        break;
      }
      case 'walk': {
        this.t -= dt; this.cool -= dt;
        const dir = sign(this.goal - this.x);
        this.x = clamp(this.x + dir * this.C.walk * this.speed * dt, this.L, this.R);
        this.face = this.kind === 'priest' ? (P.x < this.x ? -1 : 1) : dir;
        if (this.t <= 0 || Math.abs(this.goal - this.x) < 4) { this.state = 'idle'; this.setA('idle'); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'stagger': this.t -= dt; if (this.anim.done) this.anim.hold(); if (this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.6; } break;
      case 'dead': if (this.anim.done) this.anim.hold(); return;
    }
    this.x = clamp(this.x, this.L, this.R);
  }
  priestSpot() {   // keep a lane away from the player, behind the King when possible
    const side = this.V.x < P.x ? -1 : 1;
    let gx = P.x + side * this.C.prefer;
    if (gx < this.L + 10 || gx > this.R - 10) gx = P.x - side * this.C.prefer;
    return clamp(gx, this.L, this.R);
  }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, M = this.C.moves[a] || {}, wins = metaWindows(sh, a);
    if (an.i < nvFirstActive(sh, a) - 1) this.facePlayer();
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (M.shake) { shake = Math.max(shake, M.shake); if (a === 'chop') { const r = metaRect(sh, this, w.hit); spawnFx('shockwave', this.face > 0 ? r.x1 - 10 : r.x0 + 10, this.floor, 1); sfx.boom(); } } }
      if (M.step) this.x = clamp(this.x + this.face * M.step * dt, this.L, this.R);
      if (this.hitIds.has(wi) || !w.hit) return;
      if (overlap(metaRect(sh, this, w.hit), playerHurtbox())) {
        if (hurtPlayer(BOSS_DMG * (M.dmg ? M.dmg[wi] ?? M.dmg[0] : 30) * NGP.dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: a === 'slash', src: this })) { this.hitIds.add(wi); if (a === 'bash') P.vx = this.face * 180; }
      }
    });
    const sp = sh.meta && sh.meta.spawn && sh.meta.spawn[a];
    if (sp && an.i >= sp.frame && !this.fired.sp) {
      this.fired.sp = true; const at = metaPoint(sh, this, sp.at);
      if (a === 'cast') {   // three slow homing soul bolts, fanned
        nvSfx.ghost();
        for (let k = -1; k <= 1; k++) { const ang = Math.atan2(P.y - 16 - at.y, P.x - at.x) + k * 0.35; nvSoul(at.x, at.y, Math.cos(ang) * 105, Math.sin(ang) * 105, { dmg: 22, home: 1.1, life: 3.2, src: this, delay: 0.08 * (k + 1) }); }
      } else if (a === 'ward') {
        const V = this.V; if (V.alive) { V.ward = 4.5; nvSfx.ghost(); if (!NVR.hints.ward) { NVR.hints.ward = true; toast('The Confessor wards the King. Strike the Confessor down.', 3); } }
        for (let i = 0; i < 20; i++) { const t = i / 20; particles.push({ x: lerp(at.x, V.x, t) + rand(-4, 4), y: lerp(at.y, V.y - 60, t) + rand(-4, 4), vx: 0, vy: -rand(5, 20), life: 0.8, kind: 'nvsoul' }); }
      }
    }
    if (an.done) { this.state = 'idle'; this.setA('idle'); this.cool = this.kind === 'priest' ? rand(3.4, 4.8) : this.kind === 'exec' ? rand(2.0, 3.0) : rand(1.2, 2.0); this.nextHitAt = -9; }
  }
  draw() {
    if (this.state === 'dead' && this.anim.done) return;
    if (!this.sh.ok) { g.fillStyle = 'rgba(120,170,240,0.6)'; g.fillRect(Math.round(this.x - 8), Math.round(this.y - 44), 16, 44); return; }
    const a = (this.state === 'absorbed' ? 0 : 0.72) * this.alpha * (0.9 + 0.1 * Math.sin(time * 7 + this.x));
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.2, flashColor: '#ffffff' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, { ...opt, alpha: a });
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, { alpha: a * 0.35, blend: 'lighter' });
    if (this.alive) addLight(this.x, this.y - 30, 44, '140,190,255', 0.55);
  }
}

class NvVael extends BossBase {
  constructor(x, y) {
    super('vael', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.vael.hp * NGP.hp);
    const ma = ASSETS.vael_meta, mb = ASSETS.vael_b_meta;
    this.SA = [sheet('vael', { meta: ma }), sheet('vael_p3', { meta: ma })];
    this.SB = [sheet('vael_b', { meta: mb }), sheet('vael_b_p3', { meta: mb })];
    this.sh = this.SA[0]; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant';
    this.stanceMax = 480; this.critRange = 80; this.court = []; this.cds = {}; this.nextHitAt = -9; this.ward = 0; this.fireT = 4; this.chain = 0;
  }
  get L() { return TILE + 46; }
  get R() { return 44 * TILE - 40; }
  get parts() { return [this, ...this.court.filter(q => q.alive && q.state !== 'appear' && q.state !== 'absorbed')]; }
  sheetFor(tag) { const arr = NV_VB.has(tag) ? this.SB : this.SA, s = arr[this.phase >= 3 && arr[1].ok ? 1 : 0]; return s.ok ? s : arr[0]; }
  setA(tag, loop = false, speed = this.speed) {
    const sh = this.sheetFor(tag);
    if (sh !== this.sh || this.anim.s !== sh) { this.sh = sh; this.anim = new Anim(sh, sh.has(tag) ? tag : 'idle', loop, speed); }
    else this.anim.set(sh.has(tag) ? tag : 'idle', loop, speed);
  }
  hurtbox() { if (!this.alive) return null; const m = this.SA[0].meta; return m && m.hurtbox ? metaRect(this.SA[0], this, m.hurtbox) : rect(this.x - 22, this.y - 96, this.x + 22, this.y); }
  canStagger() { return !this.air && !['summon', 'absorb', 'rise'].includes(this.state) && !(this.state === 'attack' && ['leap', 'charge', 'nova'].includes(this.atk)); }
  hit(info) {
    if (this.alive && this.active && (this.state === 'summon' || this.state === 'absorb')) { spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); sfx.block(); return; }
    if (this.ward > 0 && this.active && this.alive) { info = { ...info, dmg: info.dmg * 0.35, poise: info.poise * 0.5 }; spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); }
    super.hit(info);
  }
  stagger() { super.stagger(); this.setA('stagger', false, 1); this.air = null; this.y = this.floor; this.charging = false; }
  activate() { if (this.active || this.cutting) return; super.activate(); if (this.active && !this.cutting) { this.state = 'idle'; this.setA('idle', true); } }
  wake() { return P.x < 40 * TILE && P.state !== 'dead'; }
  meta(tag) { return this.sheetFor(tag).meta || {}; }
  lead(tag) { const sh = this.sheetFor(tag), a = sh.meta && sh.meta.attacks && sh.meta.attacks[tag]; const f = a ? Math.min(...Object.keys(a.frames).map(Number)) : 4; return nvLead(sh, tag, f, this.speed); }
  update(dt) {
    this.commonUpdate(dt);
    this.ward = Math.max(0, this.ward - dt);
    for (const k in this.cds) this.cds[k] -= dt;
    this.anim.update(dt);
    for (const q of this.court) q.update(dt);
    if (!this.active) {
      if (this.state === 'dormant') { if (this.anim.tag !== 'rise') this.setA('rise', false, 0); this.anim.i = 0; this.anim.t = 0; }
      if (!this.cutting && this.wake()) this.activate();
      return;
    }
    const d = Math.abs(P.x - this.x), fd = (P.x - this.x) * this.face;
    switch (this.state) {
      case 'intro': case 'dormant': this.state = 'idle'; this.setA('idle', true); break;
      case 'idle':
        this.facePlayer(); this.cool -= dt;
        if (this.anim.tag !== 'idle') this.setA('idle', true);
        if (P.state === 'dead') break;
        if (this.pendingPhase) { this.beginPhase(this.pendingPhase); break; }
        if (this.cool <= 0) this.choose(d, fd);
        else if (d > 140) { this.state = 'walk'; this.setA('walk', true); this.t = 0.5; }
        break;
      case 'walk':
        this.facePlayer(); this.t -= dt; this.cool -= dt;
        this.x = clamp(this.x + this.face * 56 * this.speed * dt, this.L, this.R);
        if (this.anim.changed && this.anim.i % 4 === 1) { shake = Math.max(shake, 1.5); sfx.step(); }
        if (this.t <= 0 || d < 100 || this.pendingPhase) { this.state = 'idle'; this.setA('idle', true); this.cool = Math.min(this.cool, 0.2); }
        break;
      case 'attack': this.updateAttack(dt); break;
      case 'summon': this.updateSummon(dt); break;
      case 'absorb': this.updateAbsorb(dt); break;
      case 'stagger':
        this.t -= dt;
        if (this.anim.i === this.anim.n - 1 && this.t > 0.3) this.anim.hold();
        if (this.anim.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.4; }
        break;
      case 'dead':
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(0, 100), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: 'nvsoul' });
        if (this.anim.done) this.anim.hold();
        break;
    }
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * 0.66 && !this.pendingPhase) this.pendingPhase = 2;
    if (this.alive && this.phase === 2 && this.hp <= this.maxHp * 0.3 && !this.pendingPhase) this.pendingPhase = 3;
    // phase 3: in the void the crown's fire hunts the player
    if (this.phase >= 3 && this.alive && ['idle', 'walk', 'attack'].includes(this.state)) {
      this.fireT -= dt; if (this.fireT <= 0) { this.fireT = rand(2.6, 3.6); nvFire(clamp(P.x + P.vx * 0.35, this.L - 30, this.R + 30), this.floor, { warn: 0.9, dmg: 34, src: this }); }
    }
    if (!this.air) this.x = clamp(this.x, this.L, this.R);
    if (this.alive) this.camX = (this.x + P.x) / 2;
  }
  choose(d, fd) {
    const ph = this.phase, w = {};
    for (const [k, M] of Object.entries(NV_VM)) {
      if (M.ph && ph < M.ph) continue;
      if (d < M.band[0] || d > M.band[1] || this.cds[k] > 0) continue;
      w[k] = M.w * (k === this.last ? 0.25 : 1);
    }
    if (fd < -20 && d < 130) { w.spin = 3.5; delete w.combo; delete w.string; delete w.thrust; delete w.overhead; }
    if (ph >= 2 && w.string) w.string *= 1.4;
    if (ph >= 3) { for (const k of ['string', 'chain', 'charge', 'nova']) if (w[k]) w[k] *= 1.5; }
    if (ph === 2 && this.court.some(q => q.alive && q.state === 'attack')) { if (w.combo) w.combo *= 0.5; if (w.string) w.string *= 0.5; }
    const m = nvPick(w);
    if (!m) { this.state = 'walk'; this.setA('walk', true); this.t = 0.5; return; }
    this.startMove(m);
  }
  startMove(m) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.air = null; this.y = this.floor;
    this.state = 'attack'; this.setA(m, false, this.speed); this.charging = m === 'charge'; this.chargeT = 0;
    const M = NV_VM[m] || {}; if (M.cd) this.cds[m] = M.cd * (this.phase >= 3 ? 0.65 : 1);
    this.nextHitAt = time + this.lead(m);
  }
  groupOf(tag, i) { const a = this.sh.meta.attacks[tag]; const fs = Object.keys(a.frames).map(Number).sort((x, y) => x - y); let g = 0; for (let k = 1; k < fs.length && fs[k] <= i; k++) if (fs[k] - fs[k - 1] > 1) g++; return g; }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, M = NV_VM[a] || {}, ph = this.phase;
    const atk = sh.meta.attacks && sh.meta.attacks[a];
    const first = atk ? Math.min(...Object.keys(atk.frames).map(Number)) : 99;
    if (an.i < first - 1 && a !== 'leap' && !this.charging) this.facePlayer();
    for (const tel of (sh.meta.telegraph && sh.meta.telegraph[a]) || []) if (an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); addLight(p.x, p.y, 40, '140,190,255', 1); }
    // thrust lunge
    if (M.lunge && an.i >= M.lunge[0] && an.i <= M.lunge[1]) { let T = 0; for (let i = M.lunge[0]; i <= M.lunge[1]; i++) T += an.ms(i); T = T / 1000 / an.speed; this.x = clamp(this.x + this.face * M.dist / T * dt, this.L, this.R); }
    // shoulder charge: loop the rush frames until past the player or at the wall
    if (a === 'charge' && this.charging && an.i >= 2) {
      this.chargeT += dt;
      this.x += this.face * 265 * this.speed * dt;
      if (an.changed) { shake = Math.max(shake, 2.5); sfx.step(); particles.push({ x: this.x - this.face * 30, y: this.floor, vx: -this.face * 50, vy: -rand(10, 40), life: 0.5, kind: 'dust' }); }
      const past = (this.x - P.x) * this.face > 70, wall = this.x <= this.L || this.x >= this.R;
      if (wall) { this.x = clamp(this.x, this.L, this.R); shake = 9; sfx.boom(); spawnFx('shockwave', this.x + this.face * 30, this.floor, 1); this.charging = false; an.i = 6; an.t = 0; }
      else if (past || this.chargeT > 1.7) { this.charging = false; an.i = 6; an.t = 0; }
      else if (an.i >= 5 && an.t > an.ms() * 0.8) { an.i = 2; an.t = 0; this.hitIds.delete(0); }
    }
    // leap arc (frame 2 takes off, frame 5 lands)
    if (a === 'leap') {
      if (an.changed && an.i === 2 && !this.air) { const T = nvLead(sh, a, 5, an.speed) - nvLead(sh, a, 2, an.speed); this.air = { x0: this.x, tx: clamp(P.x - this.face * 20, this.L, this.R), t: 0, T: Math.max(0.25, T) }; nvSfx.whoosh(); sfx.jump(); }
      if (this.air) { this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T); this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * 92; if (k >= 1) { this.air = null; this.y = this.floor; } }
    }
    // strikes (per-frame rects from the art; one hit per strike of a string)
    const r0 = atk && atk.frames[String(an.i)];
    if (r0) {
      const gi = this.groupOf(a, an.i);
      if (an.changed && (an.i === first || !atk.frames[String(an.i - 1)])) { sfx.bossSwing(); nvSfx.whoosh(); }
      if (!this.hitIds.has(gi) && overlap(metaRect(sh, this, r0), playerHurtbox())) {
        const dmg = (M.dmg ? (M.dmg[gi] ?? M.dmg[M.dmg.length - 1]) : 44) * (ph >= 3 ? 1.15 : 1) * NGP.dmg;
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + gi, { parryable: !!(M.parry && M.parry[gi]), src: this })) { this.hitIds.add(gi); if (a === 'charge') P.vx = this.face * 220; }
      }
    }
    // spawns: impacts, chains, ghost fire, sword rain, the crown nova
    const sp = sh.meta.spawn && sh.meta.spawn[a];
    if (sp && an.i >= sp.frame && !this.fired.sp) {
      this.fired.sp = true; const at = metaPoint(sh, this, sp.at);
      if (a === 'overhead' || a === 'string' || a === 'leap') {
        const x = clamp(at.x, this.L - 30, this.R + 30);
        sfx.boom(); shake = Math.max(shake, 10); nvSfx.ghost(); spawnFx('shockwave', x, this.floor, 1);
        for (let i = 0; i < 16; i++) particles.push({ x: x + rand(-12, 12), y: this.floor - 2, vx: rand(-110, 110), vy: -rand(40, 170), g: 400, life: rand(0.4, 0.8), kind: i % 2 ? 'rock' : 'nvsoul' });
        for (const dd of [-1, 1]) nvWave(x, this.floor, dd, { speed: 190, dmg: 30, src: this, life: 2.2 });
        if (a === 'leap') { const r = rect(x - 44, this.floor - 34, x + 44, this.floor); if (overlap(r, playerHurtbox())) hurtPlayer(BOSS_DMG * 40 * NGP.dmg, sign(P.x - x), this.atkId * 10 + 7, { src: this }); }
        if (ph >= 2 && a === 'overhead') for (let k = 1; k <= 3; k++) nvFire(clamp(x + this.face * k * 64, this.L - 30, this.R + 30), this.floor, { warn: 0.45 + k * 0.22, dmg: 32, src: this });
      } else if (a === 'chain') {
        nvThrowShackle(this, at, { spectral: true, max: 310, dmg: 26, onHit: () => { this.chainHit = true; } });
      } else if (a === 'ghostfire') {
        nvSfx.ghost(); flashScreen = 0.1;
        const n = ph >= 3 ? 6 : ph === 2 ? 5 : 4;
        for (let k = 0; k < n; k++) nvFire(clamp(this.x + this.face * (56 + k * 30), this.L - 30, this.R + 30), this.floor, { warn: 0.6 + k * 0.15, dmg: 36, src: this, w: 26 });
        if (ph >= 2) for (let k = -1; k <= 1; k += 2) { const ang = Math.atan2(P.y - 16 - at.y, P.x - at.x) + k * 0.3; nvSoul(at.x, at.y, Math.cos(ang) * 120, Math.sin(ang) * 120, { dmg: 24, home: 1.0, src: this }); }
      } else if (a === 'rain') {
        nvSfx.toll(1.3, 0.5); flashScreen = 0.15;
        const n = ph >= 3 ? 9 : 7;
        for (let k = 0; k < n; k++) nvSwordFall(clamp(P.x + (k - (n - 1) / 2) * 38 + rand(-8, 8), this.L - 30, this.R + 30), this.floor, 0.85 + Math.abs(k - (n - 1) / 2) * 0.16 + rand(0, 0.1), this);
      } else if (a === 'nova') {
        sfx.roar(); nvSfx.toll(0.7, 0.8); shake = 10; flashScreen = 0.3;
        nvRing(this.x, this.y - 56, { dmg: 34, src: this, speed: 210, max: 280, stun: 0, boss: true });
        for (const dd of [-1, 1]) nvWave(this.x + dd * 20, this.floor, dd, { speed: 160, dmg: 28, src: this, life: 2.4 });
      }
    }
    if (an.done) {
      this.air = null; this.y = this.floor; this.nextHitAt = -9; this.charging = false;
      if (this.pendingPhase) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.1; return; }
      const maxChain = ph >= 3 ? 3 : 1, pc = ph >= 3 ? 0.7 : ph === 2 ? 0.4 : 0.3, d = Math.abs(P.x - this.x);
      if (a === 'chain' && this.chainHit) { this.chainHit = false; this.chain++; return this.startMove(ph >= 2 ? 'string' : 'combo'); }
      if (this.chain < maxChain && Math.random() < pc && P.state !== 'dead') {
        const nx = d < 130 ? (a === 'combo' || a === 'string' ? (ph >= 3 ? 'spin' : 'overhead') : 'combo') : d < 250 ? (a === 'thrust' ? 'charge' : 'thrust') : (this.cds.leap > 0 ? 'ghostfire' : 'leap');
        if (nx !== a && !(this.cds[nx] > 0)) { this.chain++; return this.startMove(nx); }
      }
      this.chain = 0; this.state = 'idle'; this.setA('idle', true);
      this.cool = ph === 1 ? rand(0.9, 1.4) : ph === 2 ? rand(0.9, 1.5) : rand(0.3, 0.6);
    }
  }
  // ---------------------------------------------------------------- phase changes
  beginPhase(ph) {
    this.pendingPhase = 0; this.chain = 0; this.air = null; this.y = this.floor; this.stance = 0; this.charging = false; nvClearHazards();
    if (ph === 2) { this.phase = 2; this.state = 'summon'; this.setA('summon', false, 1); this.summoned = false; this.phaseScene(2); }
    else { this.state = 'absorb'; this.setA('absorb', false, 1); this.absorbed = false; this.phaseScene(3); }
  }
  spawnCourt() {
    if (this.summoned) return; this.summoned = true;
    const fl = this.floor, px = P.x, side = this.x < px ? 1 : -1;
    const spots = [['knight', clamp(px + side * 70, this.L, this.R)], ['exec', clamp(px - side * 90, this.L, this.R)], ['priest', clamp(this.x - side * 70, this.L, this.R)]];
    for (const [k, x] of spots) { const q = new NvCourtier(this, k, x, fl); this.court.push(q); for (let i = 0; i < 18; i++) particles.push({ x: x + rand(-10, 10), y: fl - rand(0, 50), vx: rand(-20, 20), vy: -rand(20, 70), life: rand(0.6, 1.2), kind: 'nvsoul' }); }
    nvSfx.toll(0.8, 0.8); shake = 7; flashScreen = 0.35;
  }
  updateSummon(dt) {
    const an = this.anim, sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.summon;
    if (!this.summoned && an.i >= (sp ? sp.frame : 6)) this.spawnCourt();
    if (an.done) { this.spawnCourt(); this.state = 'idle'; this.setA('idle', true); this.cool = 1.2; }
  }
  updateAbsorb(dt) {
    const an = this.anim;
    if (an.i >= 2 && an.i <= 5) for (const q of this.court) if (q.alive && q.state !== 'absorbed') {
      for (let i = 0; i < 3; i++) { const t = Math.random(); particles.push({ x: lerp(q.x, this.x, t) + rand(-5, 5), y: lerp(q.y - 30, this.y - 70, t) + rand(-5, 5), vx: (this.x - q.x) * 0.8, vy: -rand(0, 20), life: 0.4, kind: 'nvsoul' }); }
    }
    if (!this.absorbed && an.i >= 6) {
      this.absorbed = true; this.phase = 3; this.speed = 1.2; let gain = 0;
      for (const q of this.court) if (q.alive) { gain += q.hp * 0.5; q.hp = 0; q.state = 'absorbed'; }
      gain = Math.min(gain, this.maxHp * 0.1); this.hp = Math.min(this.maxHp, this.hp + gain); this.displayHp = this.hp;
      flashScreen = 1; shake = 14; sfx.roar(); nvSfx.toll(0.6, 1);
      spawnFx('roar_ring', this.x, this.y - 70, 1, null, { tint: '#9cc8ff' });
      nvVoid(true);
      const i = an.i; this.setA('absorb', false, 1); this.anim.i = i;   // the blazing sheet from here on
    }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.5; this.court = this.court.filter(q => q.state !== 'absorbed'); }
  }
  phaseScene(ph) {
    const key = 'cutp' + ph + ':vael';
    const hasCourt = this.court.some(q => q.alive);
    const line = ph === 2 ? ['King Vael', 'Rise, my court. Your king has need of you once more.']
      : hasCourt ? ['King Vael', 'Come back to me… all of you. I will not fall alone.'] : ['King Vael', 'Alone again. Then let the crown burn — and the world with it.'];
    if (SAVE.flags[key]) { toast(line[1], 2.2); return; }
    SAVE.flags[key] = 1;
    playCutscene([
      { pan: { x: this.x, y: this.y - 60 }, dur: 0.5 },
      say(line[0], line[1], { dur: 2.4 }),
      { until: () => ph === 2 ? this.summoned || this.anim.done : this.absorbed, max: 3.2 },
      wait(ph === 3 ? 1.1 : 0.7),
      { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
    ], () => { if (ph === 2) this.spawnCourt(); });
  }
  ambient(dt) {
    if (state === 'cut') {
      for (const q of this.court) { q.anim.update(dt); q.alpha = Math.min(1, q.alpha + dt * 1.5); if (q.state === 'appear' && q.anim.done) { q.state = 'idle'; q.setA('idle'); } }
      if (this.state === 'summon') this.updateSummon(0);
      if (this.state === 'absorb') this.updateAbsorb(dt);
    }
    if (this.alive) {
      addLight(this.x + this.face * 14, this.y - 84, this.phase >= 3 ? 100 : 60, '140,190,255', this.phase >= 3 ? 1 : 0.6);
      if (NVR.void) addLight(this.x, this.y - 50, 120, '120,150,210', 0.7);
    }
  }
  die() {
    this.state = 'dead'; this.setA('death', false, 1); this.air = null; this.y = this.floor; this.charging = false;
    for (const q of this.court) if (q.alive) q.die();
    nvClearHazards(); projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    setTimeout(() => { nvSfx.toll(0.7, 1); if (room && room.id === 'NV7') { nvVoid(false); flashScreen = 0.5; } }, 2600);
    victoryBanner = { text: 'THE HOLLOW CROWN FALLS', t: 0 };
    this.rewards();
  }
  draw() {
    for (const q of this.court) q.draw();
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (!this.sh.ok) { g.fillStyle = '#6a5a2a'; g.fillRect(Math.round(this.x - 16), Math.round(this.y - 84), 32, 84); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    if (this.ward > 0 && this.alive) {
      const a = Math.min(1, this.ward) * (0.35 + 0.15 * Math.sin(time * 12));
      g.strokeStyle = `rgba(170,215,255,${a})`; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(this.x), Math.round(this.y - 52), 36, 58, 0, 0, 6.3); g.stroke();
      g.fillStyle = `rgba(120,180,255,${a * 0.18})`; g.fill();
      addLight(this.x, this.y - 52, 80, '140,190,255', 0.5);
    }
  }
}
BOSS_SPAWN.vael = (cx, fy) => new NvVael(cx, fy);
BOSS_CUTS.vael = b => [
  act(() => { b.setA('rise', false, 0); b.anim.i = 0; b.anim.t = 0; b.face = -1; }),
  bossPan(b, 64, 1.6),
  say('', 'Beneath his city of the dead, a king kneels before an empty throne.'),
  say('King Vael', 'My bells still toll. My court still kneels. My crown… still weighs.'),
  act(() => { b.facePlayer(); b.setA('rise', false, 1); b.anim.i = 2; nvSfx.chain(); }),
  say('King Vael', 'You come to take it? Then carry it — as I have.'),
  { until: () => b.anim.done, max: 2.0 },
  act(() => { b.setA('idle', true); sfx.roar(); shake = 10; flashScreen = 0.4; nvSfx.toll(0.8, 1); spawnFx('roar_ring', b.x, b.y - 70, 1, null, { tint: '#9cc8ff' });
    for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-40, 40), y: b.y - rand(0, 110), vx: 0, vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'nvsoul' }); }),
  wait(1.2),
];

// ================================================================== the spectral sword rain
function nvSwordFall(x, floor, warn, src) {
  NVR.swords.push({ x, y: floor, t: 0, warn, id: ++hazardId, src, landed: false });
}
function nvUpdateSwords(dt) {
  for (const s of NVR.swords) {
    s.t += dt;
    if (!s.landed && s.t >= s.warn + 0.12) {
      s.landed = true; shake = Math.max(shake, 2); if (Math.random() < 0.4) nvSfx.ghost();
      for (let i = 0; i < 6; i++) particles.push({ x: s.x + rand(-4, 4), y: s.y - 2, vx: rand(-60, 60), vy: -rand(20, 90), g: 300, life: 0.5, kind: 'nvsoul' });
    }
    if (s.t >= s.warn + 0.06 && s.t < s.warn + 0.3 && overlap(rect(s.x - 6, s.y - 46, s.x + 6, s.y), playerHurtbox())) hurtPlayer(BOSS_DMG * 32 * NGP.dmg, sign(P.x - s.x), s.id, { src: s.src });
    if (s.t > s.warn + 1.1) s.done = true;
  }
  NVR.swords = NVR.swords.filter(s => !s.done);
}
function nvDrawSwords() {
  for (const s of NVR.swords) {
    const x = Math.round(s.x);
    if (s.t < s.warn) {   // the mark: a pale line from above, a glyph on the floor
      const k = s.t / s.warn, a = 0.15 + 0.45 * k * (0.6 + 0.4 * Math.sin(time * 24));
      g.fillStyle = `rgba(150,200,255,${a})`;
      for (let y = s.y - 150; y < s.y; y += 5) g.fillRect(x, Math.round(y), 1, 2);
      g.beginPath(); g.ellipse(x, s.y - 1, 3 + 5 * k, 1.5, 0, 0, 6.3); g.fill();
      continue;
    }
    const fall = Math.min(1, (s.t - s.warn) / 0.12), tipY = s.y - 150 * (1 - fall) + 4, fade = s.t > s.warn + 0.7 ? 1 - (s.t - s.warn - 0.7) / 0.4 : 1;
    g.globalAlpha = Math.max(0, fade);
    g.fillStyle = '#a2cdf8'; g.fillRect(x - 1, Math.round(tipY - 38), 3, 36);
    g.fillStyle = '#eef8ff'; g.fillRect(x, Math.round(tipY - 38), 1, 36);
    g.fillStyle = '#63a0e6'; g.fillRect(x - 4, Math.round(tipY - 40), 9, 2); g.fillRect(x - 1, Math.round(tipY - 47), 3, 7);
    g.globalAlpha = 1;
    addLight(x, tipY - 20, 40, '150,200,255', 0.7 * fade);
  }
}

// ================================================================== the void (phase 3): nothing left but the King, his fire and you
Object.assign(SCALES, { nv_void: [0, 1, 3, 6, 8] }); Object.assign(ROOTS, { nv_void: 38.9 });
Object.assign(AREAS, { nv_void: { name: 'The Hollow Throne', ambient: 0.55, amb: 'ghost', tint: '#000000', map: '#44507e' } });
function nvVoid(on) {
  if (!room) return;
  if (on && !NVR.void) {
    NVR.void = { def: room.def, back: room.back, front: room.front };
    room.def = { ...room.def, biome: 'nv_void' };
    const mk = () => { const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; return c; };
    const back = mk(), front = mk(), fx = front.getContext('2d');
    const fl = 13 * TILE;   // the arena floor: a faint line, nothing more
    fx.fillStyle = 'rgba(70,90,140,0.55)'; fx.fillRect(0, fl, room.pw, 1);
    fx.fillStyle = 'rgba(40,52,90,0.4)'; for (let x = 0; x < room.pw; x += 3) fx.fillRect(x, fl + 2, 1, 1);
    room.back = back; room.front = front;
    particles = particles.filter(p => !p.amb);
  } else if (!on && NVR.void) {
    room.def = NVR.void.def; room.back = NVR.void.back; room.front = NVR.void.front; NVR.void = null;
  }
}
// the court's HUD is drawn with the executioners' (above); the King's court list:
if (window.__game) Object.assign(window.__game, { NVR, nvToll, nvFire, nvRing, nvWave, nvSoul, nvThrowShackle });
HOOKS.playerHurt.push((dmg, opt) => { if (window.__nvLog && nvIn()) { const s = opt.src; window.__nvLog.push([Math.round(dmg), s ? (s.name || s.type || s.kind) + ':' + (s.state === 'attack' ? s.atk : s.state) + ':' + (s.anim ? s.anim.i : '') : 'env', P.state]); } return dmg; });
