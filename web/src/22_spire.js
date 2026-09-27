// ------------------------------------------------------------------ THE TEMPEST SPIRE (agent S)
// Storm-lashed sea cliffs above the Ramparts. Biome `spire`: crumbling bridges (';'), the storm sea / abyss ("'"),
// wind gusts, telegraphed lightning strikes, puddles that carry chain lightning, rain + sky flashes.
// Enemies: sp_crow (flocks that dive), sp_scarecrow (ambush from its post), sp_acolyte (chain-lightning caster).
// Bosses: the Bell-Ringer (mini-boss, SP5) and Cindervane, the Last Drake (SP7; tears the roof off in phase 2).
// Every top-level name is prefixed sp/SP (all region files share one scope).
Object.assign(AREAS, { spire: { name: 'The Tempest Spire', ambient: 0.5, amb: 'ash', tint: '#0a0d16' } });
Object.assign(SCALES, { spire: [0, 1, 5, 7, 10] });
Object.assign(ROOTS, { spire: 46.25 });

const SP_T_CRUMBLE = 15, SP_T_SEA = 16;
const SP_STORM = ['#0b1a3a', '#12306a', '#1c4fa6', '#2f7ae0', '#5aa8ff', '#a4d6ff', '#eef9ff'];
const spIn = () => room && room.def.biome === 'spire';
const spSfx = {
  crackle: () => { noise(0.35, 4200, 1.2, 0.12, 'highpass', 0.6); tone(1800, 0.2, 0.03, 'square', 0.5); },
  strike: () => { noise(0.25, 5200, 0.7, 0.55, 'highpass', 0.3); noise(0.9, 180, 0.7, 0.8, 'lowpass', 0.35); tone(60, 0.8, 0.35, 'sawtooth', 0.4); },
  thunder: (v = 1) => { noise(1.8, 110, 0.6, 0.55 * v, 'lowpass', 0.4); noise(1.2, 320, 0.5, 0.18 * v, 'bandpass', 0.5); },
  gustWarn: () => noise(1.0, 500, 0.5, 0.18, 'bandpass', 2.4),
  gust: () => noise(2.0, 900, 0.4, 0.22, 'bandpass', 0.5),
  zap: () => { noise(0.18, 3800, 1.5, 0.22, 'bandpass', 0.5); tone(1400, 0.12, 0.05, 'square', 0.4); },
  splash: () => { noise(0.5, 700, 0.6, 0.4, 'lowpass', 0.5); noise(0.3, 2600, 1, 0.14, 'highpass'); },
  toll: (p = 1) => { [131, 165, 196].forEach((f, i) => tone(f * p, 2.4, 0.16, 'sine', 1, i * 0.02)); tone(65 * p, 2.6, 0.2, 'triangle'); noise(0.3, 900, 0.8, 0.25, 'bandpass', 0.4); },
  caw: () => { tone(760, 0.16, 0.06, 'sawtooth', 0.7); tone(690, 0.2, 0.05, 'square', 0.6, 0.12); },
  screech: () => { tone(900, 0.9, 0.12, 'sawtooth', 0.45); noise(1.0, 2400, 0.8, 0.3, 'bandpass', 0.5); tone(140, 1.0, 0.2, 'sawtooth', 0.6); },
};

// ================================================================== per-room state
const SPR = { roomObj: null };
function spReset() {
  Object.assign(SPR, { roomObj: room, crumbles: new Map(), pieces: [], sea: [], puddles: [], bolts: [], arcs: [], strikes: [], rings: [], waves: [],
    debris: [], flames: [], streaks: [], gust: null, fieldGap: null, wind: null, stormT: rand(1.5, 3), skyT: rand(3, 7), sky: null, flash: 0, thunder: [], safe: null,
    stunT: 0, veilHint: false, bridgeLock: false, drift: 0, flock: {} });
}
function spEnsure() { if (SPR.roomObj !== room) spReset(); }

// ================================================================== tiles
registerTile(';', SP_T_CRUMBLE, { solid: true, draw() {} });          // drawn live (it shakes, falls, returns)
registerTile("'", SP_T_SEA, { solid: true, draw(ctx, sh, px, py, x, y, R) {    // dark water body under the surf row
  if (y > 0 && R.def.map[y - 1][x] === "'") { ctx.fillStyle = '#04070d'; ctx.fillRect(px, py, 16, 16); }
} });
const spCell = (tx, ty) => (tx >= 0 && ty >= 0 && tx < room.w && ty < room.h) ? room.grid[ty * room.w + tx] : -1;
function spFeetTiles(b) {
  const ty = Math.floor((b.y + 1) / TILE);
  return [Math.floor((b.x - b.w / 2 + 1) / TILE), Math.floor((b.x + b.w / 2 - 1) / TILE)].map(tx => [tx, ty, spCell(tx, ty)]);
}
function spGroundY(x, y0, maxd = 360) {   // first solid top at or below y0
  for (let y = Math.max(0, y0); y < Math.min(room.ph, y0 + maxd); y += 4) if (isSolidT(tileAt(Math.floor(x / TILE), Math.floor(y / TILE)))) return Math.floor(y / TILE) * TILE;
  return null;
}

// ================================================================== room setup (enter hook)
HOOKS.enter.push(def => {
  spEnsure();
  if (def.biome !== 'spire') return;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x];
    if (ch === ';') SPR.crumbles.set(y * def.w + x, { x, y, st: 'idle', t: 0, a: 1, sturdy: def.id === 'SP7' });
    if (ch === "'") SPR.sea.push([x, y, y === 0 || def.map[y - 1][x] !== "'"]);
  }
  if (def.wind) SPR.wind = { cfg: def.wind, st: 'calm', t: rand(def.wind.every[0] * 0.5, def.wind.every[1] * 0.7), k: 0 };
  // scarecrow posts stand whether or not their scarecrow still lives
  (def.spawns || []).forEach(s => { if (s.t === 'enemy' && s.type === 'sp_scarecrow') props.push(spDeco('post', s.x * TILE + 8, (s.y + 1) * TILE, 'sp_post', 'idle')); });
  if (def.id === 'SP7') spArenaSetup();
  if (def.id === 'SP1' && !SAVE.items.emberdash) setTimeout(() => { if (room && room.id === 'SP1') toast('Salt wind howls down from above. The way up is walled with ash.', 3.5); }, 1400);
});
HOOKS.rest.push(() => {
  if (!spIn()) return;
  (room.def.spawns || []).forEach((s, i) => { if (s.t === 'sp_perch') spPerchSpawn(s, { cx: s.x * TILE + 8, fy: (s.y + 1) * TILE, key: `${room.id}:sp${i}` }, true); });
});

// ================================================================== decor props
function spDeco(type, x, y, shName, tag, extra = {}) {
  const sh = sheet(shName);
  return { type: 'sp_' + type, x, y, face: 1, sh, anim: new Anim(sh, sh.has(tag) ? tag : Object.keys(sh.tags)[0] || tag, true), ...extra };
}
const SP_DECO = { lamp: ['sp_lamp', 'loop'], windmill: ['sp_windmill', 'loop'], cottage: ['sp_cottage', 'idle'], fence: ['sp_fence', 'idle'],
                  wheat: ['sp_wheat', 'loop'], window: ['sp_window', 'idle'] };
SPAWNS.sp_prop = (s, c) => {
  spEnsure();
  const d = SP_DECO[s.kind]; if (!d) return;
  const p = spDeco(s.kind, c.cx, c.fy, d[0], d[1]);
  if (s.kind === 'lamp') p.update = () => addLight(p.x + 3, p.y - 32, 64 + Math.sin(time * 9 + p.x) * 3, '255,180,100', 0.9, LX_FLICKER);
  if (s.kind === 'windmill') p.update = () => addLight(p.x - 4, p.y - 64, 26, '255,180,100', 0.5);
  if (s.kind === 'cottage') p.update = () => addLight(p.x + 8, p.y - 24, 34, '255,170,90', 0.55);
  if (s.kind === 'wheat') p.anim.t = rand(0, 600);
  if (s.kind === 'window') p.window = true;
  props.push(p);
};

// ================================================================== puddles
SPAWNS.sp_puddle = (s, c) => {
  spEnsure();
  SPR.puddles.push({ x0: s.x * TILE + 2, x1: (s.x + (s.w || 2)) * TILE - 2, y: c.fy, charge: 0, warn: 0, id: ++hazardId, seed: rand(0, 9) });
};
function spElectrify(pd, delay = 0) {
  if (pd.charge > 0 || pd.warn > 0 || pd.pending) return;
  pd.pending = delay;
}
function spDischarge(x, y, src) {   // a bolt lands at (x,y): nearby puddles take it and pass it on
  spawnFx('sp_spark', x, y, 1); spSfx.zap();
  for (let i = 0; i < 8; i++) particles.push({ x, y, vx: rand(-90, 90), vy: -rand(20, 110), g: 300, life: rand(0.2, 0.5), kind: 'spark' });
  let first = null, bd = 64;
  for (const pd of SPR.puddles) { const d = Math.hypot(clamp(x, pd.x0, pd.x1) - x, pd.y - y); if (d < bd) { bd = d; first = pd; } }
  if (first) { spArc(x, y, clamp(x, first.x0, first.x1), first.y - 1); spElectrify(first, 0.05); }
}
function spArc(x0, y0, x1, y1, life = 0.25) {
  const pts = [[x0, y0]], n = Math.max(3, Math.floor(Math.hypot(x1 - x0, y1 - y0) / 7));
  for (let i = 1; i < n; i++) { const t = i / n; pts.push([lerp(x0, x1, t) + rand(-4, 4), lerp(y0, y1, t) + rand(-4, 4)]); }
  pts.push([x1, y1]); SPR.arcs.push({ pts, life, max: life });
}
function spUpdatePuddles(dt) {
  for (const pd of SPR.puddles) {
    if (pd.pending !== undefined && pd.pending !== null) {
      pd.pending -= dt;
      if (pd.pending <= 0) { pd.pending = null; pd.warn = 0.3; spSfx.crackle(); }
    }
    if (pd.warn > 0) { pd.warn -= dt; if (pd.warn <= 0) { pd.charge = 0.75; pd.cyc = (pd.cyc || 0) + 1; spSfx.zap();
      for (const q of SPR.puddles) if (q !== pd && Math.abs((q.x0 + q.x1) / 2 - (pd.x0 + pd.x1) / 2) < 150 && Math.abs(q.y - pd.y) < 60 && !q.charge && !q.warn && q.pending == null) {
        spArc((pd.x0 + pd.x1) / 2, pd.y - 2, (q.x0 + q.x1) / 2, q.y - 2, 0.35); spElectrify(q, 0.18);
      } } }
    if (pd.charge > 0) {
      pd.charge -= dt;
      addLight((pd.x0 + pd.x1) / 2, pd.y - 4, 50, '120,180,255', 0.9);
      if (P.ground && P.x > pd.x0 - 4 && P.x < pd.x1 + 4 && Math.abs(P.y - pd.y) < 3) hurtPlayer(26 * NGP.dmg, sign(P.x - (pd.x0 + pd.x1) / 2), pd.id * 100 + pd.cyc, {});
      if (Math.random() < 0.5) particles.push({ x: rand(pd.x0, pd.x1), y: pd.y - 1, vx: rand(-20, 20), vy: -rand(20, 60), life: 0.3, kind: 'frost' });
    }
  }
}
function spDrawPuddles() {
  for (const pd of SPR.puddles) {
    const w = pd.x1 - pd.x0, x = Math.round(pd.x0), y = Math.round(pd.y);
    g.fillStyle = 'rgba(10,16,30,0.95)'; g.fillRect(x, y - 1, w, 2);
    g.fillStyle = 'rgba(70,100,150,0.55)'; g.fillRect(x + 1, y - 1, w - 2, 1);
    const sx = x + Math.floor(((time * 9 + pd.seed * 7) % Math.max(1, w - 6)));
    g.fillStyle = 'rgba(170,200,240,0.7)'; g.fillRect(sx, y - 1, 3, 1);
    if (pd.warn > 0 && Math.floor(time * 30) % 2) { g.fillStyle = 'rgba(120,180,255,0.8)'; g.fillRect(x, y - 1, w, 1); }
    if (pd.charge > 0) {
      g.fillStyle = SP_STORM[5];
      for (let k = 0; k < 3; k++) { let px = x + rand(0, w), py = y - 1; for (let j = 0; j < 8; j++) { g.fillRect(Math.round(px), Math.round(py), 1, 1); px += rand(-2, 3); py = y - 1 - rand(0, 4); } }
      g.fillStyle = 'rgba(160,210,255,0.8)'; g.fillRect(x, y - 1, w, 1);
    }
  }
}

// ================================================================== crumbling bridges
function spUpdateCrumbles(dt) {
  if (!SPR.crumbles.size) return;
  if (P.ground) for (const [tx, ty, t] of spFeetTiles(P)) if (t === SP_T_CRUMBLE) {
    const c = SPR.crumbles.get(ty * room.w + tx);
    if (c && c.st === 'idle' && !c.sturdy) { c.st = 'shake'; c.t = 0.6; noise(0.2, 700, 0.8, 0.08, 'bandpass'); }
  }
  for (const [idx, c] of SPR.crumbles) {
    if (c.st === 'shake') {
      c.t -= dt;
      if (Math.random() < 0.15) particles.push({ x: c.x * TILE + rand(2, 14), y: c.y * TILE + 5, vx: 0, vy: rand(10, 40), g: 300, life: 0.5, kind: 'dust' });
      if (c.t <= 0) spDropPlank(c, idx);
    } else if (c.st === 'gone') {
      if (SPR.bridgeLock) continue;
      c.t -= dt;
      const r = rect(c.x * TILE, c.y * TILE - 2, c.x * TILE + 16, c.y * TILE + 16);
      if (c.t <= 0 && !overlap(r, playerHurtbox()) && !enemies.some(e => e.alive && overlap(r, e.hurtbox() || r))) {
        c.st = 'idle'; c.a = 0; room.grid[idx] = SP_T_CRUMBLE;
      }
    } else if (c.a < 1) c.a = Math.min(1, c.a + dt * 2.5);
  }
}
function spPlankTag(c) {
  const L = spCell(c.x - 1, c.y) === SP_T_CRUMBLE || room.def.map[c.y][c.x - 1] === ';', R = room.def.map[c.y][c.x + 1] === ';';
  return L && R ? 'm' : R ? 'l' : L ? 'r' : 's';
}
function spDropPlank(c, idx, quiet) {
  c.st = 'gone'; c.t = 4.5; room.grid[idx] = T_EMPTY;
  const sh = sheet('sp_bridge');
  SPR.pieces.push({ x: c.x * TILE + 8, y: c.y * TILE + 8, vx: rand(-15, 15), vy: rand(0, 40), r: 0, vr: rand(-4, 4), f: sh.first(spPlankTag(c)), life: 2.5 });
  for (let i = 0; i < 5; i++) particles.push({ x: c.x * TILE + rand(0, 16), y: c.y * TILE + rand(0, 6), vx: rand(-40, 40), vy: rand(-30, 30), g: 400, life: rand(0.6, 1.1), kind: 'rock' });
  if (!quiet) noise(0.3, 400, 0.6, 0.2, 'lowpass', 0.5);
}
function spDrawCrumbles() {
  const sh = sheet('sp_bridge');
  for (const [, c] of SPR.crumbles) {
    if (c.st === 'gone') continue;
    let tag = spPlankTag(c), dx = 0, dy = 0;
    if (c.st === 'shake') { dx = Math.round(rand(-1, 1)); dy = Math.round(rand(0, 1)); if (Math.floor(time * 12) % 2 && tag === 'm') tag = 'crack'; }
    if (sh.ok) drawSprite(sh, sh.first(tag), c.x * TILE + 8 + dx, c.y * TILE + 16 + dy, 1, { bottom: true, alpha: c.a });
    else { g.fillStyle = '#5a4630'; g.fillRect(c.x * TILE + dx, c.y * TILE + dy, 16, 5); }
  }
  for (const p of SPR.pieces) if (sh.ok) drawRotated(sh, p.f, p.x, p.y, p.r, Math.min(1, p.life));
}

// ================================================================== the sea / abyss
function spNearestGround(x, y) {   // fallback respawn spot: closest solid, non-sea, non-crumble top with headroom
  const tx0 = Math.floor(x / TILE); let best = null, bd = 1e9;
  for (let ty = 1; ty < room.h; ty++) for (let tx = Math.max(0, tx0 - 30); tx < Math.min(room.w, tx0 + 30); tx++) {
    const t = room.grid[ty * room.w + tx]; if (!(isSolidT(t) && t !== SP_T_SEA && t !== SP_T_CRUMBLE)) continue;
    if (isSolidT(room.grid[(ty - 1) * room.w + tx]) || (ty > 1 && isSolidT(room.grid[(ty - 2) * room.w + tx]))) continue;
    const d = Math.abs(tx * TILE + 8 - x) + Math.abs(ty * TILE - y) * 0.5; if (d < bd) { bd = d; best = { x: tx * TILE + 8, y: ty * TILE }; }
  }
  return best;
}
function spUpdateSea(dt, piecesOnly) {
  if (piecesOnly) return spUpdatePieces(dt);
  // remember real ground for respawns (the engine would happily remember a crumbling plank or the sea)
  if (P.ground) {
    const ft = spFeetTiles(P), bad = ft.some(([, , t]) => t === SP_T_CRUMBLE || t === SP_T_SEA);
    if (!bad && ft.every(([, , t]) => t === T_PLAT || (isSolidT(t) && t !== SP_T_CRUMBLE && t !== SP_T_SEA)) && !nearSpikes()) SPR.safe = { x: P.x, y: P.y };
    else if (SPR.safe) P.safe = { ...SPR.safe };
    if (ft.some(([, , t]) => t === SP_T_SEA) && P.state !== 'dead') {
      if (!SPR.safe) SPR.safe = spNearestGround(P.x, P.y);
      if (SPR.safe) P.safe = { ...SPR.safe };
      spSfx.splash(); for (let i = 0; i < 18; i++) particles.push({ x: P.x + rand(-8, 8), y: P.y, vx: rand(-60, 60), vy: -rand(60, 180), g: 420, life: rand(0.5, 0.9), kind: 'frost' });
      P.inv = 0; spikeHurt();
    }
  }
  for (const e of enemies) if (e.alive && !e.cfg.flying && e.ground && spFeetTiles(e).some(([, , t]) => t === SP_T_SEA)) { e.hp = 0; e.die({ dir: 0 }); spSfx.splash(); }
  spUpdatePieces(dt);
}
function spUpdatePieces(dt) {
  for (const p of SPR.pieces) { p.vy += 500 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.r += p.vr * dt; p.life -= dt;
    const t = tileAt(Math.floor(p.x / TILE), Math.floor(p.y / TILE));
    if (t === SP_T_SEA && !p.splashed) { p.splashed = true; p.life = 0; for (let i = 0; i < 8; i++) particles.push({ x: p.x, y: p.y - 4, vx: rand(-40, 40), vy: -rand(40, 120), g: 420, life: 0.6, kind: 'frost' }); } }
  SPR.pieces = SPR.pieces.filter(p => p.life > 0);
}
function spDrawSea() {
  const sh = sheet('sp_sea'); if (!SPR.sea.length) return;
  for (const [x, y, top] of SPR.sea) {
    const px = x * TILE, py = y * TILE;
    if (px + 16 < cam.x || px > cam.x + W || py + 16 < cam.y || py > cam.y + H) continue;
    if (sh.ok) {
      const t = sh.tag(top ? 'surf' : 'deep'), n = t.to - t.from + 1;
      drawSprite(sh, t.from + (Math.floor(time * (top ? 9 : 6)) + x * 2 + (x % 3)) % n, px + 8, py + 16, 1, { bottom: true });
    }
    if (top && (x + Math.floor(time * 2)) % 5 === 0) addLight(px + 8, py + 2, 26, '120,160,220', 0.18);
  }
}

// ================================================================== wind gusts
function spUpdateWind(dt) {
  const w = SPR.wind; if (!w) return;
  const c = w.cfg; w.t -= dt;
  if (w.st === 'calm' && w.t <= 0) { w.st = 'warn'; w.t = 1.1; spSfx.gustWarn(); }
  else if (w.st === 'warn' && w.t <= 0) { w.st = 'gust'; w.t = c.dur; spSfx.gust(); }
  else if (w.st === 'gust' && w.t <= 0) { w.st = 'calm'; w.t = rand(c.every[0], c.every[1]); }
  const target = w.st === 'gust' ? 1 : w.st === 'warn' ? 0.12 : 0;
  w.k = approach(w.k, target, dt * (w.st === 'gust' ? 3 : 1.5));
  if (w.k > 0.2 && !['hook', 'rest', 'dead', 'rise'].includes(P.state)) P.pushVx = (P.pushVx || 0) + c.dir * c.push * w.k * (P.ground ? 1 : 1.15);
  // streaks: a few in the warning (cue), a torrent in the gust
  const rate = w.st === 'warn' ? 10 : w.st === 'gust' ? 70 : 1.5;
  let n = rate * dt; while (n > 0) { if (Math.random() < n) SPR.streaks.push({ x: c.dir > 0 ? cam.x - 30 : cam.x + W + 30, y: cam.y + rand(0, H), v: rand(260, 420) * c.dir, len: rand(8, 22) * (w.st === 'gust' ? 1.4 : 1), a: w.st === 'gust' ? rand(0.35, 0.6) : rand(0.15, 0.3), life: 2 }); n -= 1; }
  if (w.st === 'gust' && Math.random() < 0.4) particles.push({ x: cam.x + (c.dir > 0 ? rand(0, 60) : W - rand(0, 60)), y: cam.y + rand(0, H), vx: c.dir * rand(140, 260), vy: rand(-10, 20), life: 1.5, kind: 'ash' });
}
function spUpdateStreaks(dt) {
  for (const s of SPR.streaks) { s.x += s.v * dt; s.life -= dt; }
  SPR.streaks = SPR.streaks.filter(s => s.life > 0 && s.x > cam.x - 60 && s.x < cam.x + W + 60);
}
function spDrawStreaks() {
  for (const s of SPR.streaks) { g.fillStyle = `rgba(200,215,235,${s.a})`; g.fillRect(Math.round(s.x), Math.round(s.y), Math.round(s.len), 1); }
}

// ================================================================== lightning strikes + sky flashes
function spStrike(x, opt = {}) {
  const y = opt.y ?? spGroundY(x, Math.max(0, (opt.from ?? P.y) - 18));
  if (y === null || y === undefined) return null;
  const s = { x, y, t: 0, warn: opt.warn ?? 0.95, dmg: opt.dmg ?? 38, id: ++hazardId, fx: null, done: false, boss: !!opt.boss, harmless: !!opt.harmless };
  SPR.strikes.push(s); if (!opt.quiet) spSfx.crackle();
  return s;
}
function spUpdateStrikes(dt) {
  for (const s of SPR.strikes) {
    s.t += dt;
    if (!s.fx && s.t >= s.warn - 0.24) s.fx = spawnFx(fxOr('sp_strike', 'pillar'), s.x, s.y, 1, null, { bottom: true });
    if (s.t >= s.warn && !s.hit) {
      s.hit = true; spSfx.strike(); shake = Math.max(shake, 5); SPR.flash = Math.max(SPR.flash, 0.5);
      for (let i = 0; i < 14; i++) particles.push({ x: s.x, y: s.y - 2, vx: rand(-120, 120), vy: -rand(30, 160), g: 380, life: rand(0.3, 0.7), kind: 'spark' });
      for (const pd of SPR.puddles) if (Math.abs(clamp(s.x, pd.x0, pd.x1) - s.x) < 40 && Math.abs(pd.y - s.y) < 20) spElectrify(pd, 0.02);
    }
    if (s.t >= s.warn && s.t < s.warn + 0.2 && !s.harmless) {
      if (overlap(rect(s.x - 11, s.y - 210, s.x + 11, s.y), playerHurtbox())) hurtPlayer((s.boss ? BOSS_DMG : 1) * s.dmg * NGP.dmg, sign(P.x - s.x), s.id, { src: s.boss ? boss : null });
      addLight(s.x, s.y - 60, 140, '200,225,255', 1);
    }
    if (s.t > s.warn + 0.7) s.done = true;
  }
  SPR.strikes = SPR.strikes.filter(s => !s.done);
}
function spDrawStrikeWarn() {
  for (const s of SPR.strikes) {
    if (s.t >= s.warn) continue;
    const k = s.t / s.warn, pulse = 0.5 + 0.5 * Math.sin(time * 30);
    g.fillStyle = `rgba(120,180,255,${0.25 + 0.45 * k * pulse})`;
    g.beginPath(); g.ellipse(Math.round(s.x), Math.round(s.y) - 1, 6 + 10 * k, 2 + k, 0, 0, 6.3); g.fill();
    g.fillStyle = `rgba(230,245,255,${0.5 * k})`; g.fillRect(Math.round(s.x) - 1, Math.round(s.y) - 2, 3, 1);
    if (k > 0.45 && Math.random() < 0.35) { g.fillStyle = `rgba(190,220,255,${0.25 * k})`; let x = s.x, yy = s.y - 200; while (yy < s.y) { g.fillRect(Math.round(x), Math.round(yy), 1, 6); x += rand(-2, 2); yy += 6; } }
    addLight(s.x, s.y - 6, 30 + 30 * k, '120,180,255', 0.5 + 0.4 * k);
  }
}
function spSkyFlash(big = true) {
  const sh = SHEETS.bg_spire_far; if (!sh || !sh.ok) return;
  const t = sh.tags[Math.random() < 0.5 ? 'flash' : 'flash2'] || sh.tags.flash; if (!t) return;
  if (!sh.loopTag) sh.loopTag = { ...sh.tags.loop };
  SPR.sky = { from: t.from, to: t.to, i: 0, t: 0 };
  SPR.flash = Math.max(SPR.flash, big ? 0.55 : 0.3);
  SPR.thunder.push(rand(0.35, 1.3));
}
function spUpdateSky(dt) {
  const sh = SHEETS.bg_spire_far;
  if (SPR.sky && sh && sh.ok) {
    const s = SPR.sky; s.t += dt || clamp(time - (s.lt ?? time), 0, 0.1); s.lt = time;
    const k = s.from + Math.min(s.to - s.from, Math.floor(s.t / 0.1));
    sh.tags.loop = { from: k, to: k };
    if (s.t > (s.to - s.from + 1) * 0.1) { sh.tags.loop = { ...sh.loopTag }; SPR.sky = null; }
  }
  for (let i = SPR.thunder.length - 1; i >= 0; i--) { SPR.thunder[i] -= dt; if (SPR.thunder[i] <= 0) { spSfx.thunder(rand(0.6, 1)); shake = Math.max(shake, 1.5); SPR.thunder.splice(i, 1); } }
  SPR.flash = Math.max(0, SPR.flash - dt * 2.2);
  if (SPR.flash > 0) addLight(cam.x + W / 2, cam.y + H / 2, 420, '200,220,255', SPR.flash * 1.1);
  if (!spOpenSky()) return;
  SPR.skyT -= dt;
  if (SPR.skyT <= 0) { SPR.skyT = rand(6, 13) * (boss && boss.kind === 'cindervane' && boss.phase === 2 ? 0.5 : 1); spSkyFlash(); }
}
function spOpenSky() { return !room.def.indoor || (room.id === 'SP7' && SAVE && room.spRoofGone); }

// ================================================================== rain + screen overlays
function spDrawRain() {
  if (!spOpenSky()) return;
  const wind = SPR.wind ? SPR.wind.cfg.dir * SPR.wind.k : 0, slant = 0.25 + wind * 0.6;
  const n = room.id === 'SP7' ? 140 : 90;
  for (let i = 0; i < n; i++) {
    const sx = hash2(i, 7) * (W + 80) - 40, sp = 260 + hash2(i, 3) * 160, len = 5 + Math.floor(hash2(i, 5) * 6);
    const yy = ((hash2(i, 11) * 400 + time * sp) % (H + 40)) - 20, xx = sx + time * sp * slant;
    const x = ((xx % (W + 80)) + W + 80) % (W + 80) - 40;
    g.fillStyle = `rgba(165,185,225,${0.14 + hash2(i, 13) * 0.18})`;
    for (let k = 0; k < len; k++) g.fillRect(Math.round(x + k * slant), Math.round(yy + k), 1, 1);
  }
}
HOOKS.renderTop.push(() => {
  if (!spIn()) return;
  const rdt = clamp(time - (SPR.lastT ?? time), 0, 0.1); SPR.lastT = time;
  if (state !== 'play') { SPR.flash = Math.max(0, SPR.flash - rdt * 2.2); if (SPR.sky) spUpdateSky(0); if (SPR.pieces.length) spUpdateSea(rdt, true); }   // cutscenes / menus: keep flashes decaying
  spDrawSkyDrake();
  spDrawRain();
  if (SPR.flash > 0) { g.fillStyle = `rgba(210,228,255,${SPR.flash * 0.28})`; g.fillRect(0, 0, W, H); }
  if (SPR.stunT > 0 && P) {   // stunned: ringing stars around the head
    const x = P.x - cam.x, y = P.y - cam.y - 32;
    for (let k = 0; k < 3; k++) { const a = time * 6 + k * 2.1; g.fillStyle = k % 2 ? '#e8d9a0' : '#fff6d0'; g.fillRect(Math.round(x + Math.cos(a) * 9), Math.round(y + Math.sin(a) * 3), 2, 2); }
  }
});

// ================================================================== main update / render hooks
HOOKS.update.push(dt => {
  if (!spIn()) return;
  spEnsure();
  spUpdateCrumbles(dt); spUpdateSea(dt); spUpdateWind(dt); spUpdateStreaks(dt); spUpdatePuddles(dt);
  spUpdateStrikes(dt); spUpdateSky(dt); spUpdateGust(dt); spUpdateBolts(dt); spUpdateRings(dt); spUpdateWaves(dt); spUpdateDebris(dt); spUpdateFlames(dt);
  for (const a of SPR.arcs) a.life -= dt; SPR.arcs = SPR.arcs.filter(a => a.life > 0);
  // ambient storm strikes (never onto the player's head without a long warning)
  const st = room.def.storm;
  if (st && P.state !== 'dead') { SPR.stormT -= dt; if (SPR.stormT <= 0) { SPR.stormT = rand(st.every[0], st.every[1]); spStrike(P.x + rand(-50, 50) + P.vx * 0.5, { warn: 1.05 }); } }
  // stun from the Bell-Ringer's toll
  if (SPR.stunT > 0) { SPR.stunT -= dt; if (P.state !== 'dead') { P.vx *= Math.pow(0.02, dt); if (P.state !== 'hurt') setP('hurt', 'hurt'); P.anim.i = 0; P.anim.t = 0; } }
  // the veil hint
  if (room.id === 'SP1' && !SAVE.items.emberdash && !SPR.veilHint && P.x < 6 * TILE && P.y < 13 * TILE && P.y > 7 * TILE) { SPR.veilHint = true; toast('A wall of packed ash, hard as stone. Something that burns could pass through.', 4); }
  if (boss && boss.kind === 'cindervane' && boss.active && boss.alive) spCamBias(dt);
});
HOOKS.render.push(() => {
  if (!spIn()) return;
  spDrawSea(); spDrawPuddles(); spDrawCrumbles(); spDrawStrikeWarn(); spDrawFlames(); spDrawWaves(); spDrawDebris();
  drawGlow(() => { spDrawBolts(); spDrawRings(); spDrawBeam(); spDrawStreaks(); });
});

// ================================================================== Lightning acolyte bolts (chain through puddles)
function spFireBolt(from, x, y, dmg) {
  const a = Math.atan2(P.y - 14 - y, P.x - x), sp = 235;
  SPR.bolts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 2.2, t: 0, dmg, id: ++hazardId, src: from });
  spSfx.zap();
}
function spUpdateBolts(dt) {
  for (const b of SPR.bolts) {
    b.t += dt; b.life -= dt; b.x += b.vx * dt; b.y += b.vy * dt;
    addLight(b.x, b.y, 40, '140,190,255', 0.9);
    if (Math.random() < 0.6) particles.push({ x: b.x, y: b.y, vx: rand(-20, 20), vy: rand(-20, 20), life: 0.25, kind: 'frost' });
    if (overlap(rect(b.x - 4, b.y - 4, b.x + 4, b.y + 4), playerHurtbox())) {
      if (hurtPlayer(b.dmg * NGP.dmg, sign(b.vx), b.id, { src: b.src })) { b.life = 0; spDischarge(P.x, P.y - 2, b.src); continue; }
    }
    if (solidAtPx(b.x, b.y) || b.life <= 0) { b.life = 0; spDischarge(b.x - b.vx * dt, b.y - b.vy * dt, b.src); }
  }
  SPR.bolts = SPR.bolts.filter(b => b.life > 0);
}
function spDrawBolts() {
  for (const b of SPR.bolts) {
    const x = Math.round(b.x), y = Math.round(b.y);
    g.fillStyle = SP_STORM[2]; g.fillRect(x - 3, y - 2, 6, 5); g.fillRect(x - 2, y - 3, 5, 7);
    g.fillStyle = SP_STORM[4]; g.fillRect(x - 2, y - 1, 4, 3);
    g.fillStyle = SP_STORM[6]; g.fillRect(x - 1, y - 1, 2, 2);
    g.fillStyle = SP_STORM[5]; let px = x, py = y; for (let k = 0; k < 6; k++) { px -= sign(b.vx) * rand(1, 3); py += rand(-2, 2); g.fillRect(Math.round(px), Math.round(py), 1, 1); }
  }
  for (const a of SPR.arcs) {
    const al = a.life / a.max;
    for (let i = 0; i < a.pts.length - 1; i++) {
      const [x0, y0] = a.pts[i], [x1, y1] = a.pts[i + 1], n = Math.ceil(Math.hypot(x1 - x0, y1 - y0));
      for (let k = 0; k <= n; k++) { const x = Math.round(lerp(x0, x1, k / n)), y = Math.round(lerp(y0, y1, k / n)); g.fillStyle = `rgba(90,168,255,${0.6 * al})`; g.fillRect(x, y + 1, 1, 1); g.fillStyle = `rgba(238,249,255,${al})`; g.fillRect(x, y, 1, 1); }
    }
  }
}

// ================================================================== enemies
Object.assign(ENEMY, {
  sp_crow: { hp: 45, cinders: 60, speed: 95, aggro: 170, range: 110, poise: 6, stance: 25, dmg: { dive: 22 }, cool: [1.2, 2.4], flying: true },
  sp_scarecrow: { hp: 170, cinders: 150, speed: 32, aggro: 150, range: 46, poise: 30, stance: 90, dmg: { reap: 40, lunge: 34 }, cool: [0.8, 1.5], lunge: { reap: 40, lunge: 170 } },
  sp_acolyte: { hp: 140, cinders: 170, speed: 26, aggro: 230, range: 200, poise: 15, stance: 60, dmg: { bolt: 30 }, cool: [2.0, 3.1], ranged: 'sp_bolt' },
});
Object.assign(ATTACK_TAGS, { sp_crow: ['dive'], sp_scarecrow: ['reap', 'lunge'], sp_acolyte: ['cast'] });

// ---- storm crow: perches in flocks, circles the player, dives one at a time
ENEMY_CLASSES.sp_crow = class extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.orb = rand(0, 6.28); this.orbR = rand(55, 85); }
  perch(fy, flock) { this.perched = true; this.state = 'perch'; this.y = fy - 8; this.hy = this.y; this.flockId = flock; this.anim.set('perch', true); this.anim.t = rand(0, 400); this.face = Math.random() < 0.5 ? -1 : 1; }
  hit(info) { if (this.state === 'perch') this.wake(); super.hit(info); }
  wake() { if (this.state !== 'perch') return; this.state = 'takeoff'; this.anim.set('takeoff', false); this.vy = -90; this.aggro = true; if (Math.random() < 0.5) spSfx.caw(); if (this.flockId) SPR.flock[this.flockId] = true; }
  updateFlying(dt) {
    const c = this.cfg; this.t += dt; this.cool -= dt;
    const clampFly = () => { this.x = clamp(this.x, 10, room.pw - 10); this.y = clamp(this.y, 12, room.ph - 10); };
    switch (this.state) {
      case 'perch':
        if ((Math.abs(P.x - this.x) < 120 && Math.abs(P.y - this.y) < 90) || (this.flockId && SPR.flock[this.flockId] && Math.random() < dt * 4)) this.wake();
        return;
      case 'takeoff':
        this.y += this.vy * dt; this.vy = approach(this.vy, -30, 200 * dt); this.facePlayer();
        if (this.anim.done) { this.state = 'idle'; this.anim.set('fly', true); this.cool = rand(0.6, 1.6); }
        break;
      case 'idle': case 'walk': {
        if (this.anim.tag !== 'fly') this.anim.set('fly', true);
        if (!this.aggro && this.canSee()) this.aggro = true;
        let tx = this.home, ty = this.hy + Math.sin(this.t * 2) * 8;
        if (this.aggro) { const a = this.t * 1.4 + this.orb; tx = P.x + Math.cos(a) * this.orbR; ty = P.y - 62 + Math.sin(a * 1.7) * 14; this.face = sign(P.x - this.x); }
        this.vx = approach(this.vx, clamp((tx - this.x) * 2, -c.speed, c.speed), 260 * dt);
        this.vy = approach(this.vy, clamp((ty - this.y) * 2, -c.speed, c.speed), 260 * dt);
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (this.aggro && this.cool <= 0 && (SPR.diveT || 0) <= 0 && Math.abs(P.x - this.x) < 150 && P.y > this.y + 20 && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
          this.startAttack('dive'); SPR.diveT = 0.75; spSfx.caw(); this.diveAt = { x: P.x, y: P.y - 12 }; this.vx *= 0.2; this.vy *= 0.2;
        }
        break;
      }
      case 'attack': {
        const an = this.anim, w = metaWindows(this.sh, 'dive')[0] || { active: [2, 4] };
        if (an.i < w.active[0]) { this.vx *= Math.pow(0.02, dt); this.vy = approach(this.vy, -25, 200 * dt); this.face = sign(this.diveAt.x - this.x); if (an.changed && an.i === 1) spawnFx('telegraph', this.x + this.face * 4, this.y - 8, this.face); }
        else if (an.i <= w.active[1]) {
          if (!this.dv) { const a = Math.atan2(this.diveAt.y - this.y, this.diveAt.x - this.x); this.dv = { x: Math.cos(a), y: Math.sin(a) }; sfx.swing(); }
          this.vx = this.dv.x * 250; this.vy = this.dv.y * 250;
          if (!this.hitIds.has(0) && overlap(this.hurtbox(), playerHurtbox()) && hurtPlayer(c.dmg.dive * NGP.dmg, sign(this.vx), this.atkId, { parryable: true, src: this })) this.hitIds.add(0);
          if (an.i === w.active[1] && an.t > an.ms() * 0.7 && this.y < this.diveAt.y && Math.hypot(this.diveAt.x - this.x, this.diveAt.y - this.y) > 16) { an.t = 0; }   // keep plunging until the mark
        } else { this.vy = approach(this.vy, -140, 600 * dt); this.vx *= Math.pow(0.3, dt); }
        this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (solidAtPx(this.x, this.y + 4)) { this.y -= 6; this.vy = -120; }
        if (an.done) { this.dv = null; this.state = 'idle'; this.anim.set('fly', true); this.cool = rand(...c.cool); }
        break;
      }
      case 'hurt':
        this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
        if (this.anim.done) { this.state = 'idle'; this.anim.set('fly', true); this.cool = Math.max(this.cool, 0.5); }
        break;
      case 'stagger': case 'parried':
        this.t -= dt * 2; this.y += 30 * dt; clampFly(); if (this.anim.done) this.anim.hold();
        if (this.t <= 0 || this.t > 100) { this.state = 'idle'; this.anim.set('fly', true); this.cool = 0.6; this.t = 0; }
        break;
    }
    addLight(this.x, this.y, 18, '120,160,230', 0.3);
  }
};
function spPerchSpawn(s, c, onlyMissing) {
  const have = new Set(enemies.map(e => e.key));
  for (let k = 0; k < (s.n || 3); k++) {
    const key = `${c.key}:${k}`; if (killed.has(key) || (onlyMissing && have.has(key))) continue;
    const e = makeEnemy('sp_crow', c.cx + (k - (s.n - 1) / 2) * 13 + rand(-3, 3), c.fy, key);
    e.perch(c.fy, c.key); enemies.push(e);
  }
}
SPAWNS.sp_perch = (s, c) => { spEnsure(); spPerchSpawn(s, c, false); };

// ---- scarecrow hollow: slumps on its post until you come close
ENEMY_CLASSES.sp_scarecrow = class extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.state = 'hidden'; this.face = 1; this.anim.set('hidden', true); this.anim.t = rand(0, 500); }
  rise() { if (this.state !== 'hidden') return; this.state = 'rise'; this.anim.set('rise', false); this.aggro = true; sfx.urn(); tone(180, 0.5, 0.08, 'sawtooth', 0.6); }
  hit(info) { if (this.state === 'hidden') this.rise(); if (this.state === 'rise') { this.hp -= Math.round(info.dmg); this.flash = 1; popup(info.x, info.y - 10, info.dmg); sfx.hit(); if (this.hp <= 0) this.die(info); return; } super.hit(info); }
  update(dt) {
    if (this.state === 'hidden') {
      this.anim.update(dt); this.flash = Math.max(0, this.flash - dt * 5);
      const dx = Math.abs(P.x - this.x), dy = Math.abs(P.y - this.y);
      if (dx < 58 && dy < 40 && P.state !== 'dead') this.rise();
      return;
    }
    if (this.state === 'rise') {
      this.anim.update(dt); this.flash = Math.max(0, this.flash - dt * 5); this.gravity(dt);
      if (this.anim.i >= 3) this.facePlayer();
      if (this.anim.done) { this.setA('idle', 'idle'); this.cool = 0.35; }
      return;
    }
    super.update(dt);
  }
  draw() { super.draw(); if (this.state === 'hidden' || this.state === 'rise') { const eye = this.state === 'rise' && this.anim.i >= 1; if (eye) addLight(this.x, this.y - 40, 22, '120,170,255', 0.6); } }
};

// ---- lightning acolyte: slow, telegraphed bolts that chain through puddles
ENEMY_CLASSES.sp_acolyte = class extends Enemy {
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, sp = sh.meta && sh.meta.spawn && sh.meta.spawn.cast, tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph.cast;
    if (an.i < (sp ? sp.frame : 7) - 1) this.facePlayer();
    if (an.i >= 3 && an.i < (sp ? sp.frame : 7)) { const p = tel ? metaPoint(sh, this, tel.at) : { x: this.x + this.face * 12, y: this.y - 44 }; addLight(p.x, p.y, 20 + an.i * 5, '120,180,255', 0.9); if (Math.random() < 0.5) particles.push({ x: p.x + rand(-4, 4), y: p.y + rand(-4, 4), vx: rand(-20, 20), vy: rand(-20, 20), life: 0.2, kind: 'frost' }); }
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); spSfx.crackle(); }
    if (!this.spawned && an.i >= (sp ? sp.frame : 7)) {
      this.spawned = true; const p = sp ? metaPoint(sh, this, sp.at) : { x: this.x + this.face * 14, y: this.y - 44 };
      spFireBolt(this, p.x, p.y, this.cfg.dmg.bolt); SPR.flash = Math.max(SPR.flash, 0.12);
    }
    this.vx *= Math.pow(0.004, dt); this.gravity(dt);
    if (an.done) { this.setA('idle', 'idle'); this.cool = rand(...this.cfg.cool); }
  }
};

// ================================================================== the Bell-Ringer (Windmill Hamlet mini-boss)
BOSS_INFO.bellringer = { name: 'The Bell-Ringer', hp: 2300, cinders: 7000, reward: ['w:bell_hammer', 'c_clapper'], quote: 'Every toll, a name. He has forgotten all of them.' };
function spRing(x, y, opt = {}) {
  SPR.rings.push({ x, y, r: 6, speed: opt.speed || 175, max: opt.max || 330, id: ++hazardId, dmg: opt.dmg || 26, src: opt.src || boss });
  spawnFx(fxOr('sp_toll', 'roar_ring'), x, y - 4, 1); spSfx.toll(opt.pitch || 1); shake = Math.max(shake, 4);
}
function spUpdateRings(dt) {
  for (const r of SPR.rings) {
    r.r += r.speed * dt;
    const d = Math.hypot(P.x - r.x, (P.y - 13) - r.y);
    if (Math.abs(d - r.r) < 8 && P.y - 26 < r.y + 4) {
      if (hurtPlayer(BOSS_DMG * r.dmg * NGP.dmg, sign(P.x - r.x), r.id, { src: r.src })) { SPR.stunT = 0.75; P.vx = sign(P.x - r.x) * 60; toast('Stunned by the toll', 1.2); }
    }
  }
  SPR.rings = SPR.rings.filter(r => r.r < r.max);
}
function spDrawRings() {
  for (const r of SPR.rings) {
    const a = 1 - r.r / r.max, n = Math.ceil(r.r * 2 * Math.PI / 1.5);
    for (let k = 0; k < n; k++) {
      const t = k / n * Math.PI * 2, x = r.x + Math.cos(t) * r.r, y = r.y + Math.sin(t) * r.r;
      if (y > r.y + 2) continue;
      g.fillStyle = `rgba(255,236,190,${0.85 * a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1);
      g.fillStyle = `rgba(200,150,80,${0.5 * a})`; g.fillRect(Math.round(x - Math.cos(t) * 2), Math.round(y - Math.sin(t) * 2), 1, 1);
    }
    addLight(r.x + r.r, r.y - 6, 26, '255,220,160', 0.4 * a); addLight(r.x - r.r, r.y - 6, 26, '255,220,160', 0.4 * a);
  }
}
function makeBellringer(x, y) {
  return new MetaBoss('bellringer', x, y, {
    sheets: ['bellringer'], stanceMax: 280, walkSpeed: 34, prefer: 72, p2at: 0.5, p2speed: 1.15, p2tag: 'ring', critRange: 64,
    introTag: 'ring', cool1: [1.0, 1.6], cool2: [0.6, 1.05], victory: 'THE BELL FALLS SILENT', deathParticle: 'ash',
    weights(d, p2) {
      if (d < 110) return { swing: 2.4, slam: 1.6, ring: p2 ? 1.1 : 0.55 };
      return { walk: 2.2, ring: p2 ? 1.4 : 0.9, slam: 0.5 };
    },
    chains: { swing(d) { return d < 110 ? 'slam' : 'ring'; }, slam(d) { return this.phase === 2 ? 'ring' : (d < 110 ? 'swing' : null); }, ring: 'swing' },
    moves: {
      swing: { dmg: [44, 40], shake: 3, step: 30 },
      slam: { dmg: [56], shake: 8, spawn(at) { spawnFx('shockwave', at.x, this.floor, 1); sfx.boom(); spRing(at.x, this.floor - 8, { src: this, dmg: 22, speed: 190, max: 260 }); } },
      ring: { dmg: [], spawn(at) {
        spRing(at.x, at.y, { src: this });
        if (this.phase === 2) setTimeout(() => { if (boss === this && this.alive) spRing(at.x, at.y, { src: this, pitch: 1.19, speed: 200 }); }, 520);
      } },
    },
    wake() { return P.x > 3 * TILE + 24 && P.x < 26 * TILE; },
    ambient() { addLight(this.x, this.y - 70, 60, '255,210,150', 0.45); },
    onPhase2() { toast('The bell cracks. Its toll turns shrill.'); shake = 8; sfx.roar(); },
    onDeath() { SPR.rings = []; victoryBanner = { text: 'THE BELL FALLS SILENT', t: 0 }; setTimeout(() => spSfx.toll(0.84), 700); },
  });
}
BOSS_SPAWN.bellringer = (cx, fy) => sheet('bellringer').ok ? makeBellringer(cx, fy) : null;
BOSS_CUTS.bellringer = b => [
  act(() => { b.anim.set('walk', true); b.face = -1; }),
  bossPan(b, 50, 1.2),
  say('', 'In the square of the drowned hamlet, someone still keeps the hours.'),
  act(() => { holdAnim(b, 'ring'); }), wait(0.6),
  act(() => { spSfx.toll(); shake = 6; flashScreen = 0.25; spawnFx(fxOr('sp_toll', 'roar_ring'), b.x + b.face * 46, b.y - 16, 1); }), wait(1.2),
];
PHASE2_LINES.bellringer = ['', 'The bell cracks. Its toll turns shrill.'];

// ================================================================== CINDERVANE, THE LAST DRAKE
BOSS_INFO.cindervane = { name: 'Cindervane, the Last Drake', hp: 4200, cinders: 18000, reward: ['gale', 'w:stormfang', 'sp:stormcall', 'c_scale'],
  quote: '“The sky was ours before the Root. It will be ours after.”' };
const SP_CV_HIT = {   // frame-coord hit rects (facing right), tuned so no spot beside the drake is always safe
  bite: [[236, 118, 70, 58]], claw: [[164, 104, 108, 72]], tail: [[0, 88, 150, 88]], land: [[40, 118, 230, 58]], dive: [[110, 60, 140, 100]],
  buffet: [[160, 92, 128, 84]], slam: [[168, 110, 112, 66]], rush: [[196, 108, 86, 68]],
};
const SP_CV_DMG = { bite: 58, claw: 50, tail: 44, land: 42, dive: 60, buffet: 30, slam: 54, rush: 56 };
const SP_CV_ACTIVE = { bite: [6, 7], claw: [5, 6], tail: [6, 7], land: [2, 2], dive: [2, 5], buffet: [5, 6], slam: [6, 7] };
const SP_CV_P2 = 0.5, SP_CV_P3 = 0.125;
class SpCindervane extends BossBase {
  constructor(x, y) {
    super('cindervane', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.cindervane.hp * NGP.hp);
    const meta = ASSETS.cindervane_meta;
    this.sheets = [sheet('cindervane', { meta }), sheet('cindervane_p2', { meta }), sheet('cindervane_p3', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant';
    this.stanceMax = 520; this.critRange = 120; this.alt = 0; this.visible = false; this.cool = 1; this.last = null; this.speed = 1;
    this.q = []; this.chain = 0; this.offmap = false;
  }
  get L() { return 118; }
  get R() { return 33 * TILE - 118; }
  get fd() { return (P.x - this.x) * this.face; }
  get flightless() { return this.phase >= 3; }
  meta(i = this.anim.i) { const m = this.sh.meta; const f = m && m.frames && m.frames[this.anim.tag]; return f ? f[Math.min(i, f.length - 1)] : null; }
  hurtbox() {
    if (!this.alive || !this.visible || this.offmap) return null;
    const f = this.meta(); if (!f) return rect(this.x - 50, this.y - 90, this.x + 60, this.y);
    return metaRect(this.sh, this, f.hb);
  }
  hit(info) { if (this.offmap || !this.visible) return; super.hit(info); }
  canStagger() { return this.alt <= 1 && !this.offmap && ['idle', 'walk', 'attack', 'rushstop'].includes(this.state) && !['breath', 'roar', 'slam'].includes(this.atk); }
  setA(tag, loop = false, speed = this.speed) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  later(t, fn) { this.q.push({ t, fn }); }
  activate() { if (this.active || this.cutting) return; this.visible = true; super.activate(); if (this.active && !this.cutting) this.spawnIntro(); }
  spawnIntro() { this.alt = 170; this.state = 'intro'; this.setA('fly', true); this.introT = 2.4; spKnockBridge(); }
  wakeCheck() { return P.x < 33 * TILE - 8 && P.ground && P.state !== 'dead'; }
  coolFor() { return this.phase === 1 ? rand(1.0, 1.5) : this.phase === 2 ? rand(0.65, 1.05) : rand(0.2, 0.45); }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    if (!this.active) { if (!this.cutting && this.wakeCheck()) this.activate(); return; }
    if (this.alive) for (const e of this.q) { e.t -= dt; if (e.t <= 0 && !e.done) { e.done = true; e.fn(); } }
    this.q = this.q.filter(e => !e.done);
    if (this.state === 'intro') {   // re-attempt entrance: drops out of the storm, lands, roars
      this.introT -= dt; this.alt = Math.max(0, this.alt - 150 * dt);
      if (this.alt <= 0 && an.tag === 'fly') { this.setA('land'); an.i = 1; shake = 8; sfx.boom(); }
      if (an.tag === 'land' && an.done) { this.setA('roar'); sfx.roar(); shake = 8; }
      if (this.introT <= 0 && an.tag !== 'land') { this.state = 'idle'; this.setA('idle', true); this.cool = 0.8; }
      this.y = this.floor - this.alt; return;
    }
    if (this.state === 'tearWait') { if (state === 'play') this.startTear(); this.y = this.floor - this.alt; return; }
    if (this.state === 'breakWait') { if (state === 'play') this.startBreak(); this.y = this.floor - this.alt; return; }
    switch (this.state) {
      case 'idle': {
        this.cool -= dt;
        if (an.tag !== 'idle') this.setA('idle', true);
        if (P.state === 'dead') break;
        if (this.cool <= 0) this.choose();
        break;
      }
      case 'walk': {
        this.t -= dt; this.cool -= dt; this.facePlayer();
        this.x = clamp(this.x + this.face * 58 * this.speed * dt, this.L, this.R);
        if (an.changed && an.i % 4 === 1) { shake = Math.max(shake, 1.5); sfx.step(); }
        const d = Math.abs(P.x - this.x);
        if (this.t <= 0 || (d > 60 && d < 150)) { this.state = 'idle'; this.cool = Math.min(this.cool, 0.25); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'rushprep': this.updateRushPrep(dt); break;
      case 'rush': this.updateRush(dt); break;
      case 'rushstop': if (an.done) this.afterMove('rush'); break;
      case 'takeoff': this.updateTakeoff(dt); break;
      case 'fly': this.updateFly(dt); break;
      case 'ascend': this.updateAscend(dt); break;
      case 'sky': this.updateSky(dt); break;
      case 'dive': this.updateDive(dt); break;
      case 'pass': this.updatePass(dt); break;
      case 'descend': this.updateDescend(dt); break;
      case 'tear': this.updateTear(dt); break;
      case 'break': this.updateBreak(dt); break;
      case 'stagger':
        this.t -= dt;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.4; }
        break;
      case 'dead':
        if (this.alt > 0) { this.alt = Math.max(0, this.alt - 220 * dt); if (this.alt === 0) { shake = 10; sfx.boom(); } }
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-80, 80), y: this.y - rand(0, 90), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: an.i > 8 ? 'ash' : 'frost' });
        if (an.done) an.hold();
        break;
    }
    // phase thresholds are taken the next time the drake is free on the ground
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * SP_CV_P2) this.pendingPhase = 2;
    if (this.alive && this.phase === 2 && this.hp <= this.maxHp * SP_CV_P3) this.pendingPhase = 3;
    if (this.pendingPhase && this.alive && this.alt <= 0 && ['idle', 'walk'].includes(this.state)) { const p = this.pendingPhase; this.pendingPhase = 0; p === 2 ? this.enterPhase2() : this.enterPhase3(); }
    this.x = clamp(this.x, this.L, this.R);
    this.y = this.floor - this.alt;
    if (this.phase >= 2 && this.alive && !this.offmap && this.state !== 'sky') { this.p2T = (this.p2T ?? 3) - dt; if (this.p2T <= 0) { this.p2T = this.phase === 3 ? rand(2.2, 3.2) : rand(3.6, 5.2); spStrike(clamp(P.x + P.vx * 0.4 + rand(-24, 24), 24, 33 * TILE - 24), { warn: 1.0, boss: true, dmg: 40 }); } }
  }
  // ---------------------------------------------------------------- move choice
  choose() {
    if (this.pendingPhase) return;
    const fd = this.fd, d = Math.abs(P.x - this.x), ph = this.phase, behind = fd < -24;
    let w;
    if (behind && d < 170) w = { tail: 3.2, turn: 1.0, buffet: 0.3 };
    else if (fd < 110) w = { claw: 2.4, bite: 1.6, tail: 0.6, buffet: 1.3, rush: 0.4 };
    else if (fd < 175) w = { bite: 2.4, claw: 1.0, buffet: 1.0, rush: 1.1, breath: 0.35 };
    else w = { rush: 2.4, walk: 1.2, breath: 0.6, air: 0.5 };
    if (ph === 1) { w.air = (w.air || 0) + 0.25; }
    if (ph >= 2) { Object.assign(w, { field: 1.3, slam: fd > -40 && fd < 200 ? 1.2 : 0.4, breath: (w.breath || 0) + 0.8 }); }
    if (ph === 2) { w.air = (w.air || 0) + 0.9; w.sky = this.skyCd > 0 ? 0 : 1.1; }
    if (ph === 3) { w.field = 1.8; w.slam = 1.6; w.rush = (w.rush || 0) + 1.0; delete w.air; delete w.sky; delete w.walk; }
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w).filter(([, v]) => v > 0); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.chain = 0;
    this.begin(m);
  }
  begin(m) {
    if (m === 'turn') { this.facePlayer(); this.cool = 0.25; this.state = 'idle'; return; }
    if (m === 'walk') { this.state = 'walk'; this.setA('walk', true); this.t = rand(0.8, 1.3); return; }
    if (m === 'air') return this.startTakeoff(this.phase === 2 && Math.random() < 0.55 ? 'pass' : 'dive');
    if (m === 'sky') return this.startTakeoff('sky');
    if (m === 'rush') return this.startRush(false);
    this.startAttack(m === 'field' ? 'roar' : m, m);
  }
  // after a move: chain (phase-dependent) or rest
  afterMove(m) {
    const ph = this.phase, maxChain = ph === 1 ? 1 : ph === 2 ? 2 : 4, pc = ph === 1 ? 0.3 : ph === 2 ? 0.5 : 0.85;
    if (this.pendingPhase) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.2; return; }
    if (this.chain < maxChain && Math.random() < pc && P.state !== 'dead') {
      this.chain++;
      const fd = this.fd, behind = fd < -24;
      let next;
      if (m === 'rush' && ph >= 1 && Math.random() < (ph === 1 ? 0.45 : 0.7)) next = 'rush2';
      else if (behind) next = Math.random() < 0.7 ? 'tail' : 'rush';
      else if (fd < 110) next = ['claw', 'bite', 'buffet', ph >= 2 ? 'slam' : 'tail'][irand(0, 3)];
      else if (fd < 180) next = ['bite', 'rush', ph >= 2 ? 'field' : 'buffet'][irand(0, 2)];
      else next = ph >= 2 && Math.random() < 0.5 ? 'field' : 'rush';
      if (next === m && m !== 'rush') next = 'rush';
      if (next === 'rush2') return this.startRush(true);
      this.last = next; return this.begin(next);
    }
    this.chain = 0; this.state = 'idle'; this.setA('idle', true); this.cool = this.coolFor();
  }
  startAttack(tag, move = tag) {
    if (tag !== 'tail') this.facePlayer();
    this.state = 'attack'; this.atk = tag; this.move = move; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {};
    this.setA(tag, false);
  }
  hitRectFor(tag) { return (SP_CV_HIT[tag] || []).map(r => metaRect(this.sh, this, r)); }
  strikePlayer(tag, dmgK = 1, parry = false) {
    if (this.hitIds.has(0)) return;
    for (const r of this.hitRectFor(tag)) if (overlap(r, playerHurtbox())) {
      if (hurtPlayer(BOSS_DMG * SP_CV_DMG[tag] * dmgK * (this.phase >= 2 ? 1.1 : 1) * NGP.dmg, P.x < this.x ? -1 : 1, this.atkId, { parryable: parry, src: this })) { this.hitIds.add(0); return true; }
    }
    return false;
  }
  checkHits(tag) { const w = SP_CV_ACTIVE[tag]; if (!w || this.anim.i < w[0] || this.anim.i > w[1]) return; this.strikePlayer(tag, 1, tag === 'bite' || tag === 'claw'); }
  telegraph(tag) {
    const tel = this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[tag];
    if (tel && this.anim.changed && this.anim.i === tel.frame) { const p = metaPoint(this.sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); return true; }
    return false;
  }
  updateAttack(dt) {
    const an = this.anim, a = this.atk, ph = this.phase;
    this.telegraph(a);
    if (a === 'tail' && an.changed && an.i === 5) { spawnFx('telegraph', this.x - this.face * 100, this.y - 20, -this.face); sfx.glint(); }
    if ((a === 'buffet' || a === 'slam') && an.changed && an.i === (a === 'buffet' ? 4 : 5)) { const f = this.meta(); if (f) { const p = metaPoint(this.sh, this, f.mouth); spawnFx('telegraph', p.x, p.y, this.face); } sfx.glint(); }
    if (an.changed && SP_CV_ACTIVE[a] && an.i === SP_CV_ACTIVE[a][0]) { sfx.bossSwing(); if (a === 'tail') { shake = 5; for (let i = 0; i < 14; i++) particles.push({ x: this.x - this.face * rand(20, 140), y: this.floor - rand(0, 6), vx: -this.face * rand(40, 140), vy: -rand(20, 80), g: 300, life: 0.6, kind: 'dust' }); } }
    if (a === 'bite' && an.i >= 5 && an.i <= 6) this.x = clamp(this.x + this.face * 90 * dt, this.L, this.R);
    if (a === 'claw' && an.i >= 5 && an.i <= 6) this.x = clamp(this.x + this.face * 70 * dt, this.L, this.R);
    if (a === 'claw' && an.changed && an.i === 6) {
      shake = 6; sfx.boom(); const f = this.meta(); const p = f ? metaPoint(this.sh, this, f.hand) : { x: this.x + this.face * 90 };
      spawnFx('shockwave', p.x, this.floor, 1);
      if (ph === 3) { SPR.waves.push({ x: p.x, y: this.floor, vx: this.face * 210, life: 1.6, id: ++hazardId, dmg: 28 }); spStrike(clamp(P.x, 24, 33 * TILE - 24), { warn: 0.8, boss: true, dmg: 36 }); }
    }
    if (a === 'buffet' && an.changed && an.i === 5 && !this.fired.gust) {
      this.fired.gust = true; spSfx.gust(); sfx.heavySwing(); shake = 5;
      SPR.gust = { dir: this.face, t: 0.55, push: 240 };
      for (let i = 0; i < 26; i++) particles.push({ x: this.x + this.face * rand(60, 200), y: this.floor - rand(0, 70), vx: this.face * rand(200, 380), vy: rand(-30, 30), life: 0.6, kind: 'dust' });
      if (ph === 3) for (let k = 1; k <= 3; k++) spStrike(clamp(this.x + this.face * (90 + k * 60), 24, 33 * TILE - 24), { warn: 0.7 + k * 0.12, boss: true, dmg: 34, quiet: k > 1 });
    }
    if (a === 'slam' && an.changed && an.i === 6 && !this.fired.slam) { this.fired.slam = true; this.slamWaves(); }
    this.checkHits(a);
    if (a === 'breath') this.updateBreath(dt);
    if (a === 'roar' && an.changed && an.i === 5 && !this.fired.roar) {
      this.fired.roar = true; sfx.roar(); shake = 9; SPR.flash = 0.4; spSkyFlash(false);
      spawnFx('roar_ring', this.x + this.face * 110, this.y - 100, 1, null, { tint: '#9cc8ff' });
      if (this.move === 'field') this.lightningField();
    }
    if (an.done) { if (a === 'land') { this.state = 'idle'; this.setA('idle', true); this.cool = this.phase === 1 ? 0.9 : 0.5; return; } this.afterMove(this.move || a); }
  }
  // ---------------------------------------------------------------- phase 2+ area attacks
  lightningField() {   // strikes across the floor with one safe gap per wave (gap near the player, so it is always reachable)
    const waves = this.phase === 3 ? 3 : 2, x0 = 30, x1 = 33 * TILE - 30, step = this.phase === 3 ? 30 : 34, gapW = this.phase === 3 ? 66 : 80;
    for (let w = 0; w < waves; w++) this.later(w * (this.phase === 3 ? 0.75 : 0.95), () => {
      const gc = clamp(P.x + rand(-120, 120), x0 + gapW / 2, x1 - gapW / 2);
      SPR.fieldGap = { x: gc, w: gapW, t: 1.4 };
      let k = 0; for (let x = x0 + rand(0, step); x < x1; x += step) if (Math.abs(x - gc) > gapW / 2) spStrike(x, { y: this.floor, warn: this.phase === 3 ? 1.05 : 1.25, boss: true, dmg: 42, quiet: k++ > 0 });
      spSfx.crackle(); SPR.flash = Math.max(SPR.flash, 0.25);
    });
  }
  slamWaves() {   // arena-wide ground shockwaves; each ring is low enough to jump
    shake = 12; sfx.boom(); spSfx.strike(); SPR.flash = 0.5;
    const f = this.meta(), hx = f ? metaPoint(this.sh, this, f.hand).x : this.x + this.face * 90;
    spawnFx('shockwave', hx, this.floor, 1); spawnFx(fxOr('sp_strike', 'pillar'), hx, this.floor, 1, null, { bottom: true, speed: 1.6 });
    const n = this.phase === 3 ? 3 : 2;
    for (let k = 0; k < n; k++) this.later(k * 0.55, () => { for (const d of [-1, 1]) SPR.waves.push({ x: hx, y: this.floor, vx: d * (190 + k * 20), life: 3, id: ++hazardId, dmg: 32 }); if (k) { shake = Math.max(shake, 6); sfx.boom(); } });
    for (const pd of SPR.puddles) spElectrify(pd, 0.1);
    if (this.phase === 3) this.later(0.3, () => spStrike(clamp(P.x, 24, 33 * TILE - 24), { warn: 0.9, boss: true, dmg: 40 }));
  }
  // ---------------------------------------------------------------- rush (charging husk, drake-sized)
  startRush(again) {
    this.facePlayer(); this.state = 'rushprep'; this.atkId = ++hazardId; this.hitIds = new Set(); this.move = 'rush';
    this.setA('rushprep', false); if (again) { this.anim.i = 3; this.anim.t = 0; }
    this.rushTelegraphed = false;
  }
  updateRushPrep(dt) {
    const an = this.anim;
    if (an.i < 4) this.facePlayer();
    if (an.changed && an.i >= 2 && Math.random() < 0.9) { for (let i = 0; i < 6; i++) particles.push({ x: this.x - this.face * rand(10, 40), y: this.floor - 2, vx: -this.face * rand(40, 120), vy: -rand(10, 60), g: 300, life: 0.5, kind: 'dust' }); sfx.step(); }
    if (an.i >= 4 && !this.rushTelegraphed) { this.rushTelegraphed = true; const f = this.meta(); const p = f ? metaPoint(this.sh, this, f.mouth) : { x: this.x + this.face * 100, y: this.y - 20 }; spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); noise(0.5, 300, 0.7, 0.35, 'lowpass', 0.5); tone(90, 0.5, 0.2, 'sawtooth', 0.6); }
    if (an.done) { this.state = 'rush'; this.setA('rush', true); this.rushT = 0; this.rushGoal = this.face > 0 ? Math.min(this.R, P.x + 170) : Math.max(this.L, P.x - 170); sfx.roar(); shake = 4; }
  }
  updateRush(dt) {
    this.rushT += dt;
    const v = 330 * (this.phase === 3 ? 1.15 : 1), nx = this.x + this.face * v * dt;
    if (this.anim.changed && this.anim.i % 3 === 0) { shake = Math.max(shake, 3); sfx.step(); }
    if (Math.random() < 0.8) particles.push({ x: this.x - this.face * rand(40, 100), y: this.floor - rand(0, 4), vx: -this.face * rand(60, 160), vy: -rand(10, 60), g: 300, life: 0.5, kind: 'dust' });
    this.strikePlayer('rush');
    const done = (this.face > 0 && (nx >= this.rushGoal || nx >= this.R)) || (this.face < 0 && (nx <= this.rushGoal || nx <= this.L)) || this.rushT > 2.2;
    this.x = clamp(nx, this.L, this.R);
    if (done) {
      const wall = this.x <= this.L + 1 || this.x >= this.R - 1;
      if (wall) { shake = 9; sfx.boom(); for (let i = 0; i < 16; i++) particles.push({ x: this.x + this.face * 140, y: this.floor - rand(20, 120), vx: -this.face * rand(20, 80), vy: rand(-40, 40), g: 400, life: 1, kind: 'rock' }); }
      this.state = 'rushstop'; this.setA('rushstop', false);
    }
  }
  // ---------------------------------------------------------------- breath: rear + inhale (telegraph), a beam sweeps near -> far
  beamGeom() {
    const f = this.meta(); if (!f || !f.mouth) return null;
    const p = metaPoint(this.sh, this, f.mouth), ang = this.face > 0 ? f.mouth[2] : 180 - f.mouth[2];
    return { x: p.x, y: p.y, a: ang * Math.PI / 180 };
  }
  beamTrace(b, maxLen = 300) {
    const dx = Math.cos(b.a), dy = Math.sin(b.a); let len = 0, gx = null, gy = null;
    for (len = 6; len < maxLen; len += 4) { const x = b.x + dx * len, y = b.y + dy * len; if (solidAtPx(x, y) || y >= this.floor) { gx = x; gy = Math.min(y, this.floor); break; } }
    return { len, gx, gy, dx, dy };
  }
  beamDamage(b, tr, dmg, tick) {
    const hb = playerHurtbox(), id = this.atkId * 1000 + Math.floor(time / tick);
    for (let s = 6; s <= tr.len; s += 8) { const x = b.x + tr.dx * s, y = b.y + tr.dy * s; if (overlap(rect(x - 7, y - 7, x + 7, y + 7), hb)) { hurtPlayer(BOSS_DMG * dmg * NGP.dmg, sign(tr.dx), id, { src: this }); break; } }
    if (tr.gx !== null && (!this.lastFlame || Math.abs(this.lastFlame - tr.gx) > 14)) {
      this.lastFlame = tr.gx; spFlame(tr.gx, this.floor, dmg * 0.4);
      if (this.phase === 3 && this.atk === 'breath' && Math.random() < 0.35) spStrike(tr.gx, { y: this.floor, warn: 0.8, boss: true, dmg: 34, quiet: true });
    }
    addLight(b.x + tr.dx * tr.len * 0.5, b.y + tr.dy * tr.len * 0.5, 120, '150,200,255', 1);
  }
  updateBreath(dt) {
    const an = this.anim;
    if (an.i >= 3 && an.i <= 5) { const b = this.beamGeom(); if (b) { addLight(b.x, b.y, 30 + an.i * 6, '150,200,255', 0.9); if (Math.random() < 0.6) particles.push({ x: b.x + rand(-6, 6), y: b.y + rand(-6, 6), vx: rand(-10, 10), vy: rand(-10, 10), life: 0.3, kind: 'frost' }); } }
    if (an.changed && an.i === 4) { spSfx.crackle(); sfx.charge(); }
    if (an.changed && an.i === 6) { spSfx.screech(); this.lastFlame = null; }
    if (an.i >= 6 && an.i <= 11) {
      const b = this.beamGeom(); if (!b) return;
      if (this.phase >= 2) b.a += (this.face > 0 ? -1 : 1) * 0.12 * (an.i - 6) / 5;   // phase 2+: the sweep reaches most of the floor
      const tr = this.beamTrace(b, this.phase >= 2 ? 440 : 300); this.beam = { b, tr, t: time };
      this.beamDamage(b, tr, 26, 0.22);
      if (an.changed) noise(0.14, 2600, 0.8, 0.12, 'bandpass', 0.7);
    } else this.beam = null;
  }
  // ---------------------------------------------------------------- flight (phases 1-2; the wings break in phase 3)
  startTakeoff(plan) {
    if (this.flightless) return this.startRush(false);
    this.facePlayer(); this.state = 'takeoff'; this.setA('takeoff', false); this.atkId = ++hazardId; this.hitIds = new Set(); this.plan = plan; this.move = plan;
  }
  updateTakeoff(dt) {
    const an = this.anim;
    if (an.changed && an.i === 3) { sfx.heavySwing(); shake = 5; for (let i = 0; i < 20; i++) particles.push({ x: this.x + rand(-120, 120), y: this.floor - rand(0, 4), vx: rand(-160, 160), vy: -rand(10, 60), g: 200, life: 0.7, kind: 'dust' }); }
    if (an.i >= 3) this.alt = approach(this.alt, this.cruise(), 90 * dt);
    if (an.done) {
      if (this.plan === 'sky') { this.state = 'ascend'; this.setA('fly', true); spSfx.screech(); return; }
      this.state = 'fly'; this.setA('fly', true); this.t = 1.1; this.flyTo = this.plan === 'pass' ? this.passStart() : this.diveSpot();
    }
  }
  cruise() { return this.phase === 2 ? 66 : 38; }
  diveSpot() { const side = P.x > this.x ? -1 : 1; return clamp(P.x + side * rand(110, 150), this.L, this.R); }
  passStart() { return P.x > (this.L + this.R) / 2 ? this.L : this.R; }
  updateFly(dt) {
    this.t -= dt; this.alt = approach(this.alt, this.cruise(), 60 * dt);
    const dx = this.flyTo - this.x; this.face = this.plan === 'pass' ? (this.flyTo === this.L ? -1 : 1) : sign(P.x - this.x);
    this.x += clamp(dx * 2.2, -170, 170) * dt;
    if (this.anim.changed && this.anim.i === 2) noise(0.25, 300, 0.6, 0.25, 'lowpass', 0.5);
    if (Math.abs(dx) < 8 || this.t <= 0) {
      if (this.plan === 'pass') { this.face = this.x < (this.L + this.R) / 2 ? 1 : -1; this.state = 'pass'; this.setA('flybreath', true); this.t = 0; this.passWarn = 0.6; this.atkId = ++hazardId; spSfx.screech(); this.lastFlame = null; }
      else this.startDive();
    }
  }
  // ---- phase 2: it climbs out of the arena into the storm (untargetable) and rains lightning, then dives back in
  updateAscend(dt) {
    this.alt += 150 * dt; this.x = approach(this.x, (this.L + this.R) / 2, 60 * dt);
    if (this.alt > 250) { this.offmap = true; this.visible = false; this.state = 'sky'; this.skyT = rand(6.0, 7.0); this.skyNext = 0.6; this.skyCd = 2; this.skyX = rand(0, 1); toast('The drake vanishes into the storm.', 2); spSkyFlash(); }
  }
  updateSky(dt) {
    this.skyT -= dt; this.skyNext -= dt; this.skyX += dt * 0.12;
    if (this.skyNext <= 0 && this.skyT > 1.2) {
      this.skyNext = rand(0.38, 0.55);
      const aimed = Math.random() < 0.55, x = clamp(aimed ? P.x + P.vx * 0.45 + rand(-10, 10) : rand(30, 33 * TILE - 30), 24, 33 * TILE - 24);
      spStrike(x, { y: this.floor, warn: aimed ? 0.95 : 1.1, boss: true, dmg: 40, quiet: !aimed });
      if (Math.random() < 0.25) spSkyFlash(false);
    }
    if (this.skyT <= 0) {   // back out of the storm: a dive onto the player's position
      this.offmap = false; this.visible = true; this.skyCd = 1;
      this.x = clamp(P.x + (Math.random() < 0.5 ? -1 : 1) * 150, this.L, this.R); this.alt = 230; this.facePlayer();
      this.startDive(); spSfx.screech(); SPR.flash = 0.5;
    }
  }
  startDive() {
    this.state = 'dive'; this.setA('dive', false); this.atkId = ++hazardId; this.hitIds = new Set();
    this.target = clamp(P.x + P.vx * 0.25, this.L, this.R); this.facePlayer(); this.divePos = null; spSfx.screech();
  }
  updateDive(dt) {
    const an = this.anim;
    this.telegraph('dive');
    if (an.i < 2) { if (this.alt < 200) this.alt = approach(this.alt, this.cruise() + 14, 40 * dt); return; }
    if (!this.divePos) { this.divePos = { x0: this.x, a0: this.alt, t: 0 }; sfx.bossSwing(); }
    const D = this.divePos; D.t += dt;
    const dist = Math.hypot(this.target - D.x0, D.a0), T = Math.max(0.3, dist / 460), k = Math.min(1, D.t / T);
    this.x = lerp(D.x0, this.target - this.face * 60, k); this.alt = D.a0 * (1 - k * k);
    if (an.i >= 5 && k < 1) { an.i = 4; an.t = 0; }
    if (!this.hitIds.has(0)) for (const r of this.hitRectFor('dive')) if (overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * SP_CV_DMG.dive * NGP.dmg, P.x < this.x ? -1 : 1, this.atkId, { src: this })) this.hitIds.add(0);
    if (Math.random() < 0.7) particles.push({ x: this.x + rand(-60, 60), y: this.y - rand(30, 110), vx: -this.face * rand(40, 120), vy: -rand(40, 90), life: 0.4, kind: 'frost' });
    if (k >= 1) {
      this.alt = 0; shake = 12; sfx.boom(); spSfx.strike(); SPR.flash = 0.6;
      const hx = this.x + this.face * 100;
      if (this.phase >= 2) spawnFx(fxOr('sp_strike', 'pillar'), hx, this.floor, 1, null, { bottom: true, speed: 1.6 });
      spawnFx('shockwave', hx, this.floor, 1);
      if (this.phase >= 2) for (const d of [-1, 1]) SPR.waves.push({ x: hx, y: this.floor, vx: d * 175, life: 1.3, id: ++hazardId, dmg: 30 });
      for (const pd of SPR.puddles) spElectrify(pd, 0.1);
      this.startAttack('land'); this.anim.i = 2; this.anim.changed = true; this.hitIds = new Set();
    }
  }
  updatePass(dt) {
    this.alt = approach(this.alt, this.cruise(), 60 * dt);
    const b = this.beamGeom();
    if (this.passWarn > 0) { this.passWarn -= dt; if (b) { addLight(b.x, b.y, 40, '150,200,255', 1); } if (this.passWarn <= 0) { spSfx.crackle(); } return; }
    this.x += this.face * 150 * this.speed * dt;
    if (b) { const tr = this.beamTrace(b); this.beam = { b, tr, t: time }; this.beamDamage(b, tr, 22, 0.25); if (this.anim.changed) noise(0.14, 2600, 0.8, 0.1, 'bandpass', 0.7); }
    if ((this.face > 0 && this.x >= this.R - 2) || (this.face < 0 && this.x <= this.L + 2)) {
      this.beam = null;
      if (Math.random() < 0.6) { this.plan = 'dive'; this.state = 'fly'; this.setA('fly', true); this.t = 0.7; this.flyTo = this.diveSpot(); }
      else { this.state = 'descend'; this.setA('land', false); this.facePlayer(); }
    }
  }
  updateDescend(dt) {
    const an = this.anim;
    this.alt = Math.max(0, this.alt - 160 * dt);
    if (an.i >= 1 && this.alt > 0) { an.i = 1; an.t = 0; }
    if (this.alt <= 0) { shake = 9; sfx.boom(); spawnFx('shockwave', this.x, this.floor, 1); this.startAttack('land'); this.anim.i = 2; this.anim.changed = true; }
  }
  // ---------------------------------------------------------------- phase 2: rip the roof off, fight under the open storm
  enterPhase2() {
    this.phase = 2; this.stance = 0; this.speed = 1.12; this.beam = null; this.skyCd = 0;
    this.swapSheet(1);
    this.alt = 0; this.state = 'tearWait'; this.setA('idle', true); this.facePlayer();
    bossPhase2Scene(this);
  }
  swapSheet(k) { if (this.sheets[k] && this.sheets[k].ok) { const a = this.anim; this.sh = this.sheets[k]; this.anim = new Anim(this.sh, a.tag, a.loop, a.speed); } }
  startTear() { this.state = 'tear'; this.setA('roar', false); this.fired = {}; }
  updateTear(dt) {
    const an = this.anim;
    if (an.changed && an.i === 5 && !this.fired.tear) { this.fired.tear = true; sfx.roar(); spTearRoof(); }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.8; this.stanceImmune = 0; }
  }
  // ---------------------------------------------------------------- phase 3 (1/8 HP): the wings break
  enterPhase3() {
    this.phase = 3; this.stance = 0; this.speed = 1.22; this.beam = null; this.offmap = false; this.visible = true; this.alt = 0;
    this.state = 'breakWait'; this.setA('stagger', false); this.facePlayer(); this.q = [];
    shake = 12; sfx.crumble(); spSfx.thunder(1); SPR.flash = 0.8; spSkyFlash();
    this.shred();
    if (!SAVE.flags['cutp3:cindervane']) {
      SAVE.flags['cutp3:cindervane'] = 1;
      playCutscene([
        { pan: { x: this.x + this.face * 30, y: this.floor - 70 }, dur: 0.5 },
        act(() => { this.swapSheet(2); this.shred(); flashScreen = 0.6; shake = 10; sfx.roar(); }),
        say('', PHASE3_LINE[1], { dur: 2.6 }),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ], () => {});
    } else this.swapSheet(2);
  }
  shred() {   // membrane rags and bone splinters burst off the broken wings
    for (let i = 0; i < 40; i++) particles.push({ x: this.x + rand(-80, 40), y: this.y - rand(60, 140), vx: rand(-90, 90), vy: -rand(20, 120), g: 160, life: rand(1, 2), kind: i % 3 ? 'ash' : 'rock' });
    for (let i = 0; i < 20; i++) particles.push({ x: this.x + rand(-80, 40), y: this.y - rand(60, 140), vx: rand(-60, 60), vy: -rand(30, 90), life: 0.6, kind: 'frost' });
  }
  startBreak() { this.swapSheet(2); this.state = 'break'; this.setA('roar', false); this.fired = {}; this.stanceImmune = 3; }
  updateBreak(dt) {
    const an = this.anim;
    if (an.changed && an.i === 5 && !this.fired.b) { this.fired.b = true; sfx.roar(); spSfx.screech(); shake = 12; SPR.flash = 0.7; this.lightningField(); }
    if (an.done) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.6; }
  }
  stagger() { this.beam = null; super.stagger(); }
  die() {
    this.state = 'dead'; this.beam = null; this.offmap = false; this.visible = true; this.q = []; this.setA('death', false, 1);
    SPR.strikes = []; SPR.waves = []; SPR.flames = []; SPR.debris = []; SPR.gust = null; hazards = [];
    shake = 14; hitstop = 0.35; slowmo = 1.8; flashScreen = 0.6; sfx.roar(); sfx.felled(); spSkyFlash(); spSfx.thunder(1);
    victoryBanner = { text: 'THE LAST DRAKE FALLS', t: 0 };
    SPR.bridgeLock = false; for (const [, c] of SPR.crumbles) if (c.st === 'gone') c.t = 3.5;
    this.rewards();
  }
  draw() {
    if (!this.visible || this.offmap) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.7, flashColor: '#dfeaff' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'rushprep' && this.anim.i >= 3) { opt.flash = Math.max(opt.flash || 0, 0.12 + 0.1 * Math.sin(time * 30)); opt.flashColor = opt.flashColor || '#bcd8ff'; }
    if (!this.sh.ok) { g.fillStyle = '#23252e'; g.fillRect(Math.round(this.x - 70), Math.round(this.y - 90), 140, 90); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    const f = this.meta(); if (f && this.alive) { const hb = metaRect(this.sh, this, f.hb); addLight((hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, 150, '110,160,255', this.phase >= 2 ? 0.8 : 0.6); }
    if (this.alt > 4 && this.alive) { const s = clamp(1 - this.alt / 200, 0.2, 1); g.fillStyle = `rgba(6,4,10,${0.45 * s})`; g.beginPath(); g.ellipse(Math.round(this.x), this.floor + 1, 60 * s, 3, 0, 0, 6.3); g.fill(); }
    if (this.state === 'dive' && this.anim.i < 2 && this.target !== undefined) { const k = 0.5 + 0.5 * Math.sin(time * 28); g.fillStyle = `rgba(120,180,255,${0.35 + 0.35 * k})`; g.beginPath(); g.ellipse(Math.round(this.target + this.face * 40), this.floor - 1, 34, 3, 0, 0, 6.3); g.fill(); }
    if (this.state === 'rushprep' && this.anim.i >= 3) {   // the charge lane: a faint streak along the floor ahead
      const x0 = this.x + this.face * 120, len = 200; for (let s = 0; s < len; s += 6) { g.fillStyle = `rgba(190,215,255,${0.28 * (1 - s / len)})`; g.fillRect(Math.round(x0 + this.face * s), this.floor - 2, 4, 1); }
    }
  }
}
BOSS_SPAWN.cindervane = (cx, fy) => sheet('cindervane').ok ? new SpCindervane(cx, fy) : null;
const PHASE3_LINE = ['', 'Its wings tear to rags. Grounded, the last drake calls the whole sky down upon you.'];
// the buffet gust + the off-map silhouette in the storm
function spUpdateGust(dt) {
  const gu = SPR.gust; if (!gu) return;
  gu.t -= dt; if (gu.t <= 0) { SPR.gust = null; return; }
  if (!['hook', 'rest', 'dead'].includes(P.state)) P.pushVx = (P.pushVx || 0) + gu.dir * gu.push;
  for (let i = 0; i < 3; i++) SPR.streaks.push({ x: gu.dir > 0 ? cam.x - 20 : cam.x + W + 20, y: cam.y + rand(40, H - 10), v: gu.dir * rand(420, 560), len: rand(14, 28), a: rand(0.35, 0.6), life: 1.2 });
}
function spDrawSkyDrake() {
  const b = boss; if (!b || b.kind !== 'cindervane' || !b.offmap || !b.sh.ok) return;
  const sh = b.sh, t = sh.tag('fly'), f = sh.frames[t.from + Math.floor(time * 10) % (t.to - t.from + 1)];
  const k = (b.skyX % 1), x = lerp(-120, W + 40, k), y = 10 + Math.sin(time * 0.8) * 6;
  g.save(); g.globalAlpha = 0.5; g.filter = 'brightness(0.35)';
  g.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(x), Math.round(y), Math.round(f.w * 0.34), Math.round(f.h * 0.34));
  g.restore();
}

// ---- the breath beam + blue flames + ground waves
function spFlame(x, y, dmg) { SPR.flames.push({ x, y, life: 1.1, id: ++hazardId, dmg }); }
function spUpdateFlames(dt) {
  for (const f of SPR.flames) { f.life -= dt; addLight(f.x, f.y - 6, 30, '130,190,255', 0.6 * Math.min(1, f.life * 2)); if (Math.random() < 0.3) particles.push({ x: f.x + rand(-6, 6), y: f.y - rand(0, 6), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'frost' });
    if (f.life > 0.2 && overlap(rect(f.x - 8, f.y - 12, f.x + 8, f.y), playerHurtbox())) hurtPlayer(BOSS_DMG * f.dmg * NGP.dmg, sign(P.x - f.x), f.id * 10 + Math.floor(f.life * 3), { src: boss }); }
  SPR.flames = SPR.flames.filter(f => f.life > 0);
}
function spDrawFlames() {
  for (const f of SPR.flames) {
    const a = Math.min(1, f.life * 2), x = Math.round(f.x), y = Math.round(f.y);
    for (let k = 0; k < 5; k++) { const h = 4 + ((k * 7 + Math.floor(time * 20)) % 7), xx = x - 6 + k * 3; g.fillStyle = `rgba(47,122,224,${0.7 * a})`; g.fillRect(xx, y - h, 2, h); g.fillStyle = `rgba(164,214,255,${0.9 * a})`; g.fillRect(xx, y - Math.floor(h / 2), 1, Math.floor(h / 2)); }
  }
}
function spUpdateWaves(dt) {
  for (const w of SPR.waves) {
    w.x += w.vx * dt; w.life -= dt;
    if (solidAtPx(w.x + sign(w.vx) * 6, w.y - 4) || !solidAtPx(w.x, w.y + 2)) w.life = 0;
    if (overlap(rect(w.x - 7, w.y - 14, w.x + 7, w.y), playerHurtbox())) hurtPlayer(BOSS_DMG * w.dmg * NGP.dmg, sign(w.vx), w.id, { src: boss });
    if (Math.random() < 0.7) particles.push({ x: w.x + rand(-3, 3), y: w.y - rand(0, 10), vx: 0, vy: -rand(20, 60), life: 0.35, kind: 'frost' });
    addLight(w.x, w.y - 8, 34, '130,190,255', 0.7);
  }
  SPR.waves = SPR.waves.filter(w => w.life > 0);
}
function spDrawWaves() {
  for (const w of SPR.waves) { const x = Math.round(w.x), y = Math.round(w.y); g.fillStyle = SP_STORM[3]; g.fillRect(x - 3, y - 12, 6, 12); g.fillStyle = SP_STORM[6]; let px = x; for (let yy = y - 16; yy < y; yy += 2) { px += rand(-1.5, 1.5); g.fillRect(Math.round(px), yy, 1, 2); } }
}
function spDrawBeam() {
  const b = boss && boss.kind === 'cindervane' && boss.alive && boss.beam; if (!b || time - b.t > 0.05) return;
  const { x, y } = b.b, { dx, dy, len } = b.tr, nx = -dy, ny = dx;
  for (let s = 2; s < len; s += 1) {
    const w = 1.5 + s * 0.035, j = Math.sin(s * 0.45 + time * 40) * 0.8;
    const cx = x + dx * s + nx * j, cy = y + dy * s + ny * j;
    g.fillStyle = 'rgba(28,79,166,0.55)'; g.fillRect(Math.round(cx + nx * w * 1.6), Math.round(cy + ny * w * 1.6), 1, 1); g.fillRect(Math.round(cx - nx * w * 1.6), Math.round(cy - ny * w * 1.6), 1, 1);
    g.fillStyle = SP_STORM[4]; g.fillRect(Math.round(cx + nx * w), Math.round(cy + ny * w), 1, 1); g.fillRect(Math.round(cx - nx * w), Math.round(cy - ny * w), 1, 1);
    g.fillStyle = SP_STORM[5]; g.fillRect(Math.round(cx + nx * w * 0.5), Math.round(cy + ny * w * 0.5), 1, 1); g.fillRect(Math.round(cx - nx * w * 0.5), Math.round(cy - ny * w * 0.5), 1, 1);
    g.fillStyle = SP_STORM[6]; g.fillRect(Math.round(cx), Math.round(cy), 1, 1);
  }
  for (let k = 0; k < 3; k++) { let px = x + dx * 4, py = y + dy * 4; const L = len * rand(0.5, 1); g.fillStyle = SP_STORM[6];
    for (let s = 0; s < L; s += 3) { px += dx * 3 + rand(-2, 2); py += dy * 3 + rand(-2, 2); g.fillRect(Math.round(px), Math.round(py), 1, 1); } }
  if (b.tr.gx !== null) { g.fillStyle = SP_STORM[6]; g.fillRect(Math.round(b.tr.gx) - 3, Math.round(b.tr.gy) - 2, 7, 2); for (let i = 0; i < 2; i++) particles.push({ x: b.tr.gx, y: b.tr.gy - 2, vx: rand(-90, 90), vy: -rand(40, 140), g: 380, life: 0.4, kind: 'spark' }); }
}

// ---- the arena: windows onto the storm, the bridge, the roof
function spArenaSetup() {
  SPR.bridgeLock = false;
  const dead = SAVE.flags['boss:cindervane'];
  // punch the window openings through the back wall so the parallax storm shows through
  const wsh = sheet('sp_window');
  if (wsh.ok && room.back) {
    const f = wsh.frames[wsh.first('idle')], c = document.createElement('canvas'); c.width = f.w; c.height = f.h;
    const cx = c.getContext('2d'); cx.drawImage(wsh.img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
    let data = null; try { data = cx.getImageData(0, 0, f.w, f.h).data; } catch (e) {}
    const bctx = room.back.getContext('2d');
    for (const p of props) if (p.window && data) {
      const ox = Math.round(p.x - f.w / 2), oy = Math.round(p.y - f.h);
      for (let y = 0; y < f.h; y++) { let l = -1, r = -1; for (let x = 0; x < f.w; x++) if (data[(y * f.w + x) * 4 + 3] > 0) { if (l < 0) l = x; r = x; }
        if (l < 0) continue; for (let x = l; x <= r; x++) if (data[(y * f.w + x) * 4 + 3] === 0) bctx.clearRect(ox + x, oy + y, 1, 1); }
    }
  }
}
function spKnockBridge() {
  if (!room || room.id !== 'SP7') return;
  SPR.bridgeLock = true; let k = 0;
  for (const [idx, c] of SPR.crumbles) if (c.st !== 'gone') { spDropPlank(c, idx, k++ > 0); const pc = SPR.pieces[SPR.pieces.length - 1]; if (pc) { pc.vy = -rand(20, 90); pc.vx = rand(-40, 20); } }
  sfx.crumble(); shake = Math.max(shake, 6);
}
function spTearRoof() {
  if (!room || room.id !== 'SP7' || room.spRoofGone) return;
  room.spRoofGone = true;
  for (let y = 0; y <= 1; y++) for (let x = 0; x < room.w; x++) room.grid[y * room.w + x] = T_EMPTY;
  room.def = { ...room.def, indoor: false };
  renderRoomLayers(room);
  props = props.filter(p => !p.window);
  shake = 14; SPR.flash = 0.9; spSkyFlash(); spSfx.thunder(1); sfx.crumble(); flashScreen = 0.4;
  for (let i = 0; i < 16; i++) SPR.debris.push({ x: rand(40, 33 * TILE - 20), y: rand(-160, -20), vy: rand(0, 60), r: rand(0, 6), vr: rand(-5, 5), f: irand(0, 3), id: ++hazardId, delay: i * 0.14 + rand(0, 0.2) });
  for (let i = 0; i < 60; i++) particles.push({ x: rand(0, room.pw), y: rand(0, 30), vx: rand(-40, 40), vy: rand(20, 120), g: 300, life: rand(1, 2), kind: 'rock' });
  toast('The drake tears the spire open to the storm.', 3);
}
function spUpdateDebris(dt) {
  for (const d of SPR.debris) {
    if (d.delay > 0) { d.delay -= dt; continue; }
    d.vy = Math.min(d.vy + 520 * dt, 420); d.y += d.vy * dt; d.r += d.vr * dt;
    const gy = boss ? boss.floor : room.ph;
    if (d.y >= gy - 8) { d.dead = true; shake = Math.max(shake, 4); sfx.crumble(); for (let i = 0; i < 8; i++) particles.push({ x: d.x, y: gy - 4, vx: rand(-80, 80), vy: -rand(30, 130), g: 400, life: 0.7, kind: 'rock' });
      if (overlap(rect(d.x - 14, gy - 30, d.x + 14, gy), playerHurtbox())) hurtPlayer(BOSS_DMG * 32 * NGP.dmg, sign(P.x - d.x), d.id, { src: boss }); }
  }
  SPR.debris = SPR.debris.filter(d => !d.dead);
}
function spDrawDebris() {
  const sh = sheet('sp_debris'), gy = boss ? boss.floor : room.ph;
  for (const d of SPR.debris) {
    if (d.delay > 0.6) continue;
    const k = clamp(1 - (gy - d.y) / 260, 0.15, 1);
    g.fillStyle = `rgba(6,4,10,${0.5 * k})`; g.beginPath(); g.ellipse(Math.round(d.x), gy - 1, 14 * k + 2, 2.5, 0, 0, 6.3); g.fill();
    if (d.delay <= 0 && sh.ok) drawRotated(sh, sh.first('abcd'[d.f]), d.x, d.y, d.r, 1);
  }
}

// ---- camera: keep the drake's body in frame while it flies (pre-compensates the engine's vertical follow)
function spCamBias(dt) {
  const b = boss; if (!b || b.alt < 6 || b.offmap) return;
  const maxY = room.ph - H;
  let ty = P.y - 30 - H / 2 + (held.has('down') && P.ground && Math.abs(P.vx) < 5 ? 50 : 0) + (held.has('up') && P.ground && Math.abs(P.vx) < 5 ? -50 : 0);
  ty = maxY < 0 ? maxY / 2 : clamp(ty, 0, maxY);
  const want = clamp(Math.max(P.y - H + 34, Math.min(ty, b.y - 150)), 0, Math.max(0, maxY));
  const k = Math.min(1, dt * (P.vy > 200 ? 12 : 5)); if (k >= 1) return;
  cam.y = cam.y + (want - ty) * k / (1 - k);
}

// ---- cutscenes
BOSS_CUTS.cindervane = b => [
  act(() => { b.visible = true; b.alt = 220; b.y = b.floor - b.alt; b.face = 1; b.anim.set('fly', true); SPR.flash = 0.8; spSkyFlash(); }),
  { pan: { x: b.x + 60, y: b.floor - 70 }, dur: 1.1 },
  { dur: 2.0, tween: (dt, k) => { b.alt = 220 * Math.pow(1 - k, 2); b.y = b.floor - b.alt; if (Math.random() < 0.5) particles.push({ x: b.x + rand(-120, 120), y: b.y - rand(40, 150), vx: rand(-30, 30), vy: rand(30, 90), life: 1, kind: 'frost' }); } },
  act(() => { b.alt = 0; b.y = b.floor; b.anim.set('land', false); b.anim.i = 2; shake = 10; sfx.boom(); dustFall(30); spawnFx('shockwave', b.x, b.floor, 1); }), wait(0.9),
  act(() => { spawnFx(fxOr('sp_strike', 'pillar'), b.x - 120, b.floor, 1, null, { bottom: true }); spSfx.strike(); SPR.flash = 1; spSkyFlash(); }), wait(0.6),
  say('', 'The last drake of the Spire returns to its storm.'),
  act(() => { holdAnim(b, 'roar'); }), wait(0.55),
  act(() => { sfx.roar(); spSfx.screech(); shake = 12; flashScreen = 0.4; spawnFx('roar_ring', b.x + 110, b.y - 100, 1, null, { tint: '#9cc8ff' }); }), wait(0.9),
  { pan: { x: 38 * TILE, y: b.floor - 40 }, dur: 0.6 },
  { do: () => { b.alt = 0; b.visible = true; spKnockBridge(); }, always: true }, wait(1.0),
];
PHASE2_LINES.cindervane = ['', 'The drake rears into the rafters. The storm wants in.'];

// ---- debug helpers for tests
if (window.__game) Object.assign(window.__game, { SPR, spStrike, spSkyFlash, spRing, spTearRoof, spRoom: () => room });
HOOKS.playerHurt.push((dmg, opt) => { if (window.__spLog && spIn()) window.__spLog.push([Math.round(dmg), boss ? boss.state + ':' + boss.anim.tag + ':' + boss.anim.i : '-', opt.src && opt.src.type || (opt.src === boss ? 'boss' : 'env'), Math.round(P.x - (boss ? boss.x : 0)), P.state]); return dmg; });

// ---- SP7 exit prompt: the way out is dropping through the thin floor at the far right (↓ + Space)
HOOKS.update.push(() => {
  if (!room || room.id !== 'SP7' || (boss && boss.alive && boss.active)) return;
  const onExit = P.ground && P.x > 47 * TILE && P.x < 50 * TILE && P.y <= 16 * TILE + 2;
  if (onExit && !SPR.exitHint) { SPR.exitHint = true; toast(matchMedia('(pointer: coarse)').matches ? 'Hold ▼ and press Jump to drop down' : 'Hold ↓ and press Space to drop down', 4); }
  if (!onExit && P.x < 44 * TILE) SPR.exitHint = false;
});
HOOKS.render.push(() => {
  if (!room || room.id !== 'SP7' || (boss && boss.alive && boss.active)) return;
  const x = 48.5 * TILE, y = 16 * TILE - 22 + Math.sin(time * 4) * 3, a = 0.55 + 0.35 * Math.sin(time * 4);
  g.fillStyle = `rgba(255,214,120,${a})`;
  for (let i = 0; i < 4; i++) g.fillRect(Math.round(x - 4 + i), Math.round(y + i), 8 - i * 2, 1);   // small pulsing down-arrow over the exit
  g.fillRect(Math.round(x - 1), Math.round(y - 5), 2, 5);
});
