// ------------------------------------------------------------------ THE BURNING DEEP (agent D): the root-forges beneath the Mire
// Rooms D1-D8 (tools/regions/40_deep.py). Lava '*' (tile 20), conveyor belts '<' '>' (21/22), burn status, the rising-magma
// escape (D6), the forge hatch shortcut (D1 <-> D7), slag imps / forge sentries / magma crawlers, the Forge Overseer and
// the Molten Colossus. Art: tiles_deep*, bg_deep_*, dp_*, overseer*, colossus*, fx_dp_* (art/gen_deep*.py).
Object.assign(AREAS, { deep: { name: 'The Burning Deep', ambient: 0.52, amb: 'ember', tint: '#170604', map: '#8a4020' } });
Object.assign(SCALES, { deep: [0, 1, 3, 6, 7] });
Object.assign(ROOTS, { deep: 41.2 });
const T_LAVA = 20, T_BELT_L = 21, T_BELT_R = 22;
const DP = { safe: null, safeT: 0, sluice: null, lavaT: 0, heat: 0, hint: {} };
const dpDeep = () => room && room.def.biome === 'deep';
const dpFx = n => fxOr('dp_' + n);
const dpSheet = n => sheet(n);
const DP_BELT = 58;           // conveyor push (px/s)

// ---- tiles: lava is drawn live (animated) from the render hook; the cached layer only gets the dark body + the pool lip
function lavaSurface(R, x, y) { return y === 0 || R.grid[(y - 1) * R.w + x] !== T_LAVA; }
registerTile('*', T_LAVA, { draw(ctx, sh, px, py, x, y, R) {
  ctx.fillStyle = '#2a0503'; ctx.fillRect(px, py, 16, 16);
} });
function drawBeltTile(ctx, sh, px, py, x, y, R, frame) {
  const fx = sheet('tiles_deep_fx'), t = R.grid[y * R.w + x];
  const L = x > 0 && [T_BELT_L, T_BELT_R].includes(R.grid[y * R.w + x - 1]), Rr = x + 1 < R.w && [T_BELT_L, T_BELT_R].includes(R.grid[y * R.w + x + 1]);
  const part = !L && !Rr ? 'belt_m' : !L ? 'belt_l' : !Rr ? 'belt_r' : 'belt_m';
  if (fx.ok && fx.has(part)) {
    const tg = fx.tag(part), n = tg.to - tg.from + 1, f = fx.frames[tg.from + ((frame % n) + n) % n];
    ctx.drawImage(fx.img, f.x, f.y, 16, 16, px, py, 16, 16);
    return;
  }
  ctx.fillStyle = '#2a2224'; ctx.fillRect(px, py, 16, 16);
  ctx.fillStyle = '#4a3c38'; ctx.fillRect(px, py, 16, 5);
  ctx.fillStyle = '#8a6a50';
  const off = ((frame % 4) + 4) % 4 * (t === T_BELT_L ? -1 : 1);
  for (let i = 0; i < 4; i++) ctx.fillRect(px + ((i * 4 + off) % 16 + 16) % 16, py + 1, 2, 2);
}
registerTile('<', T_BELT_L, { solid: true, draw(ctx, sh, px, py, x, y, R) { drawBeltTile(ctx, sh, px, py, x, y, R, 0); } });
registerTile('>', T_BELT_R, { solid: true, draw(ctx, sh, px, py, x, y, R) { drawBeltTile(ctx, sh, px, py, x, y, R, 0); } });

function lavaCellAt(x, y) { return tileAt(Math.floor(x / TILE), Math.floor(y / TILE)) === T_LAVA; }
// a body is "in lava" when its lower body overlaps a lava cell below the surface wobble
function inLava(b, depth = 4) {
  for (const xx of [b.x - b.w / 2 + 2, b.x, b.x + b.w / 2 - 2]) {
    const y = b.y - 1, tx = Math.floor(xx / TILE), ty = Math.floor(y / TILE);
    if (tileAt(tx, ty) !== T_LAVA) continue;
    const surf = tileAt(tx, ty - 1) !== T_LAVA ? ty * TILE + depth : ty * TILE;
    if (b.y > surf) return true;
  }
  return false;
}
function beltUnder(b) {
  for (const xx of [b.x - b.w / 2 + 1, b.x, b.x + b.w / 2 - 1]) {
    const t = tileAt(Math.floor(xx / TILE), Math.floor((b.y + 1) / TILE));
    if (t === T_BELT_L) return -1; if (t === T_BELT_R) return 1;
  }
  return 0;
}
function lavaNear(x, y, r = 1) {
  const tx = Math.floor(x / TILE), ty = Math.floor((y + 1) / TILE);
  for (let dx = -r; dx <= r; dx++) for (let dy = -1; dy <= 1; dy++) if (tileAt(tx + dx, ty + dy) === T_LAVA) return true;
  return false;
}

// ---- burn status (fire damage over time). c_slag halves fire damage and burn build-up.
function addBurn(n) {
  if (!P || P.state === 'dead') return;
  if (charmOn('c_slag')) n *= 0.5;
  if (P.dpBurnT > 0) { P.dpBurnT = Math.min(6, P.dpBurnT + n * 0.01); return; }
  P.dpBurn = (P.dpBurn || 0) + n; P.dpBurnD = 1.2;
  if (P.dpBurn >= 100) {
    P.dpBurn = 0; P.dpBurnT = 4.5; sfx.fire();
    spawnFx(fxOr('dp_burst', 'hit'), P.x, P.y - 12, P.face, null, { tint: '#ff8030' });
    if (!DP.hint.burn) { DP.hint.burn = 1; toast('Burning — roll to smother the flames', 3); }
  }
}
function updateBurn(dt) {
  if (!P) return;
  P.dpBurnD = (P.dpBurnD || 0) - dt;
  if (P.dpBurnD <= 0) P.dpBurn = Math.max(0, (P.dpBurn || 0) - 14 * dt);
  if (P.dpBurnT > 0 && P.state !== 'dead') {
    P.dpBurnT -= dt * (P.state === 'roll' ? 3 : 1);
    P.hp = Math.max(1, P.hp - D.maxHp * 0.028 * (charmOn('c_slag') ? 0.5 : 1) * dt);
    if (Math.random() < 0.6) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(2, 26), vx: rand(-8, 8), vy: -rand(30, 60), life: 0.45, kind: 'fire' });
    addLight(P.x, P.y - 14, 46, '255,140,60', 0.7);
  }
}
HOOKS.playerHurt.push((dmg, opt) => {
  DP.hurts = (DP.hurts || 0) + 1;
  if (opt.fire && charmOn('c_slag')) dmg *= 0.5;
  if (opt.burn) addBurn(opt.burn);
  return dmg;
});
HOOKS.rest.push(() => { if (P) { P.dpBurn = 0; P.dpBurnT = 0; } });
HOOKS.death.push(() => { if (P) { P.dpBurn = 0; P.dpBurnT = 0; } });
HOOKS.hud.push(() => {
  if (!P || (!(P.dpBurn > 0) && !(P.dpBurnT > 0))) return;
  let sy = 28;
  if (P.rot > 0 || P.rotT > 0) sy += 6;
  if (P.cryT > 0) sy += 8;
  if (P.fireT > 0) sy += 8;
  const on = P.dpBurnT > 0;
  bar(10, sy, 40, 2, on ? P.dpBurnT / 4.5 : P.dpBurn / 100, 0, on ? '#ff7a2a' : '#a8461c');
  text(on ? 'BURNING' : 'burn', 54, sy + 3, 5, on ? '#ffb070' : '#e08a50', 'left');
});

// ---- lava: heavy fire damage, then back to the last safe ground (like thorns)
function lavaHurt(frac = 0.3, respawn = null) {
  if (P.state === 'dead' || P.inv > 0) return;
  let dmg = Math.round(D.maxHp * frac * (charmOn('c_slag') ? 0.5 : 1) * NGP.dmg);
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; shake = 6; hitstop = 0.1; sfx.hurt(); sfx.fire();
  popup(P.x, P.y - 30, dmg, '#ff8a3a');
  for (let i = 0; i < 18; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 10), vx: rand(-60, 60), vy: -rand(60, 180), g: 420, life: rand(0.4, 0.8), kind: Math.random() < 0.5 ? 'fire' : 'ember' });
  spawnFx(fxOr('dp_splash', 'hit'), P.x, P.y, 1, null, { bottom: true });
  addBurn(55);
  if (P.hp <= 0) return killPlayer(0);
  P.inv = 1.0; P.vx = 0; P.vy = -140; setP('hurt', 'hurt');
  const to = respawn || DP.safe || P.safe;
  fadeTo(() => { P.x = to.x; P.y = to.y; P.vx = P.vy = 0; setP('idle', 'idle', true); updateCamera(0, true); if (DP.sluice && respawn) resetSluice(); });
}

// ---- the forge hatch (shortcut between D7's ceiling and D1's floor), opened by D7's lever
SPAWNS.dp_hatch = (s, c) => {
  const top = s.side === 'top', x0 = s.x * TILE, x1 = x0 + 2 * TILE, y0 = top ? s.y * TILE : 0, y1 = top ? y0 + 2 * TILE : TILE;
  const open = () => !!SAVE.flags['lever:D7'];
  const hp = { type: 'dp_hatch', x: x0 + TILE, y: top ? y0 : y1, face: 1, top, anim: { update() {} }, k: open() ? 1 : 0,
    update(dt) { this.k = approach(this.k, open() ? 1 : 0, dt * 1.6); if (open() && this.k < 1 && Math.random() < 0.3) particles.push({ x: rand(x0, x1), y: this.y, vx: rand(-20, 20), vy: rand(10, 60), g: 300, life: 0.6, kind: 'rock' }); },
    draw() { drawHatch(this, x0, x1); } };
  props.push(hp);
  room.dyn.push({ x0, x1, y0, y1, on: () => !open() });
};
function drawHatch(h, x0, x1) {
  const sh = sheet('dp_props');
  const y = h.top ? h.y : h.y - TILE;
  if (h.k >= 0.99) {   // swung open: grate hangs against the wall
    if (sh.ok && sh.has('hatch_open')) { drawSprite(sh, sh.first('hatch_open'), x0 - 4, y, 1, { pivot: [0, 0] }); return; }
    g.fillStyle = '#2a2024'; g.fillRect(x0 - 3, y, 3, 30); return;
  }
  if (sh.ok && sh.has('hatch')) { drawSprite(sh, sh.first('hatch'), x0, y, 1, { pivot: [0, 0], alpha: 1 - h.k * 0.7 }); return; }
  g.fillStyle = '#1c1618'; g.fillRect(x0, y, x1 - x0, 6);
  g.fillStyle = '#5a4640'; for (let x = x0 + 2; x < x1; x += 5) g.fillRect(x, y, 2, 6);
  g.fillStyle = '#b08a3a'; g.fillRect((x0 + x1) / 2 - 2, y + 2, 4, 3);
}

// ---- the Crucible (D8): a vast chained vessel of molten metal over the arena; the Colossus tips it (see Colossus.grab)
SPAWNS.dp_crucible = (s, c) => {
  const cr = { type: 'dp_crucible', x: s.x * TILE + 8, y: (s.y + 5) * TILE, hx: s.x * TILE + 8, face: 1, ang: 0, av: 0, pour: 0, anim: { update() {} },
    update(dt) {
      this.av += (-this.ang * 5 - this.av * 1.4) * dt; if (this.hold !== undefined) { this.ang = approach(this.ang, this.hold, dt * 0.9); this.av = 0; } else this.ang += this.av * dt;
      addLight(this.x, this.y - 18, 70 + Math.sin(time * 3) * 6, '255,130,50', 0.9);
      if (Math.random() < 0.08) particles.push({ x: this.x + rand(-20, 20), y: this.y - 34, vx: rand(-6, 6), vy: -rand(10, 30), life: 1.2, kind: 'ember' });
    },
    draw() { drawCrucible(this); } };
  props.push(cr); room.crucible = cr;
};
function drawCrucible(cr) {
  const sh = sheet('dp_crucible');
  // chains from the ceiling to the lugs (drawn procedurally so they follow the tilt)
  const lug = s => ({ x: cr.x + Math.cos(cr.ang) * s * 30, y: cr.y - 40 + Math.sin(cr.ang) * s * 30 });
  for (const s of [-1, 1]) {
    const a = lug(s), top = { x: cr.hx + s * 42, y: 2 * TILE };
    const n = Math.ceil(Math.hypot(a.x - top.x, a.y - top.y) / 4);
    for (let i = 0; i <= n; i++) { const x = lerp(top.x, a.x, i / n), y = lerp(top.y, a.y, i / n); g.fillStyle = i % 2 ? '#3a2e2c' : '#6a564c'; g.fillRect(Math.round(x) - (i % 2 ? 0 : 1), Math.round(y), i % 2 ? 1 : 3, 2); }
  }
  if (sh.ok) { drawSprite(sh, sh.first(sh.has('idle') ? 'idle' : Object.keys(sh.tags)[0]) + (Math.floor(time * 6) % Math.max(1, sh.tag('idle').to - sh.tag('idle').from + 1)), cr.x, cr.y, 1, { rot: cr.ang }); return; }
  g.save(); g.translate(Math.round(cr.x), Math.round(cr.y)); g.rotate(cr.ang);
  g.fillStyle = '#1a1416'; g.fillRect(-34, -48, 68, 44); g.fillStyle = '#ff7a2a'; g.fillRect(-30, -50, 60, 5); g.restore();
}

// ---- the rising magma escape (D6 Sluice Stair)
SPAWNS.dp_sluice = (s, c) => {
  if (SAVE.flags['dp:sluice']) { DP.sluice = { done: true, y: room.ph - 2 * TILE + 6, base: room.ph - 2 * TILE + 6 }; return; }
  DP.sluice = { armed: true, active: false, y: room.ph - 2 * TILE + 10, base: room.ph - 2 * TILE + 10, entry: { x: room.pw - 20, y: (s.y + 1) * TILE }, t: 0 };
};
function resetSluice() {
  const S = DP.sluice; if (!S || S.done) return;
  S.active = true; S.y = S.base; S.t = -1.6; S.warned = false;
}
function updateSluice(dt) {
  const S = DP.sluice; if (!S) return;
  if (S.done) { S.y = approach(S.y, S.base + 30, dt * 20); return; }
  if (S.armed && !S.active && P.y > room.ph - 9 * TILE) {
    S.active = true; S.t = -1.6; shake = 8; sfx.boom(); sfx.roar(); flashScreen = 0.2;
    toast('The sluice gates burst — climb!', 3);
  }
  if (!S.active) return;
  S.t += dt;
  if (S.t > 0) {
    const v = 30 + Math.min(14, S.t * 0.8);   // slow start, then a steady push (a clean climb has ~5 s spare)
    S.y = Math.max(7 * TILE + 6, S.y - v * dt);
    if (Math.random() < 0.3) shake = Math.max(shake, 1.2);
  }
  if (P.state !== 'dead' && P.inv <= 0 && P.y - 6 > S.y) lavaHurt(0.35, S.entry);
  // escaped: the west door at the top
  if (P.x < 5 * TILE && P.y <= 6 * TILE + 2 && P.ground) {
    S.done = true; S.active = false; SAVE.flags['dp:sluice'] = 1; saveGame();
    toast('The sluice chokes on its own slag and falls still.', 3.5); sfx.felled();
  }
}
function drawMagma(y0, x0, x1, bottom) {
  const top = Math.round(y0);
  for (let x = Math.floor(x0 / 2) * 2; x < x1; x += 2) {
    const w = Math.sin(time * 2.6 + x * 0.09) * 2 + Math.sin(time * 4.1 + x * 0.21) * 1;
    const yy = Math.round(top + w);
    g.fillStyle = '#ffe9a0'; g.fillRect(x, yy, 2, 1);
    g.fillStyle = '#ffb040'; g.fillRect(x, yy + 1, 2, 2);
    g.fillStyle = '#f06a18'; g.fillRect(x, yy + 3, 2, 4);
    g.fillStyle = '#b8300c'; g.fillRect(x, yy + 7, 2, 7);
    g.fillStyle = '#6a1206'; g.fillRect(x, yy + 14, 2, Math.max(0, bottom - yy - 14));
  }
  for (let i = 0; i < 6; i++) { const x = x0 + ((i * 97 + Math.floor(time * 3) * 53) % Math.max(1, x1 - x0)); g.fillStyle = '#ffd070'; g.fillRect(Math.round(x), top + 4 + (i % 3) * 5, 2, 1); }
}

// ---- update / render / enter hooks
HOOKS.enter.push(def => {
  if (def.id !== 'D6') DP.sluice = null; DP.safe = P ? { x: P.x, y: P.y } : null; DP.safeT = 0.3;
  if (def.biome !== 'deep') return;
  const H = SAVE.hints, once = (k, m, d = 4.5) => { if (!H[k]) { H[k] = 1; setTimeout(() => toast(m, d), 1200); } };
  if (def.id === 'D1') once('dp_enter', 'The air shimmers with heat. Far below, something vast is breathing.');
  if (def.id === 'D2') once('dp_chasm', SAVE.items.gale ? 'Heat rises off the lava — glide into it (hold jump while falling).' : 'The chasm is far too wide to leap. The heat rising off it could carry something light…');
  if (def.id === 'D3') once('dp_belt', 'Forge belts still run down here. Mind where they carry you.');
  if (def.id === 'D7') once('dp_hatch', 'A grate in the ceiling opens onto the Cinder Throat. The lever works it.');
});
HOOKS.update.push(dt => {
  updateBurn(dt);
  if (!dpDeep()) return;
  DP.heat += dt;
  // safe ground for lava respawns: firm, not a belt, not at the lip of a pool
  DP.safeT -= dt;
  if (P.ground && P.state !== 'hurt' && DP.safeT <= 0 && !beltUnder(P) && !lavaNear(P.x, P.y, 1) && !lavaNear(P.x - 12, P.y, 0) && !lavaNear(P.x + 12, P.y, 0)) {
    DP.safe = { x: P.x, y: P.y }; DP.safeT = 0.25;
  }
  if (DP.safe) P.safe = DP.safe;
  // belts push whatever stands on them
  const bd = P.ground ? beltUnder(P) : 0;
  if (bd && P.state !== 'hurt') P.pushVx = bd * DP_BELT;
  for (const e of enemies) if (e.alive && e.ground && !e.cfg.flying && e.type !== 'dp_magma_crawler') {
    const d = beltUnder(e); if (d && !solidAtPx(e.x + d * (e.w / 2 + 2), e.y - 4)) e.x += d * DP_BELT * 0.8 * dt;
  }
  // lava
  if (P.state !== 'dead' && inLava(P)) lavaHurt(0.3);
  for (const e of enemies) if (e.alive && e.type !== 'dp_magma_crawler' && !e.cfg.flying && inLava(e)) {
    e.dpLavaCd = (e.dpLavaCd || 0) - dt;
    if (e.dpLavaCd <= 0) { e.dpLavaCd = 0.5; e.hit({ dmg: e.maxHp * 0.4 + 10, poise: 0, dir: -e.face, kind: 'env', x: e.x, y: e.y - 6, fire: true }); }
  }
  updateSluice(dt);
  // lava glow + embers
  const tx0 = Math.floor(cam.x / TILE) - 1, tx1 = Math.floor((cam.x + W) / TILE) + 1, ty0 = Math.floor(cam.y / TILE) - 1, ty1 = Math.floor((cam.y + H) / TILE) + 1;
  for (let ty = Math.max(0, ty0); ty <= Math.min(room.h - 1, ty1); ty++) for (let tx = Math.max(0, tx0); tx <= Math.min(room.w - 1, tx1); tx++) {
    if (room.grid[ty * room.w + tx] !== T_LAVA || !lavaSurface(room, tx, ty)) continue;
    if ((tx + ty) % 2 === 0) addLight(tx * TILE + 8, ty * TILE + 4, 58 + Math.sin(time * 2 + tx) * 4, '255,110,40', 0.85);
    if (Math.random() < 0.02) particles.push({ x: tx * TILE + rand(0, 16), y: ty * TILE + 2, vx: rand(-6, 6), vy: -rand(20, 50), life: rand(0.6, 1.2), kind: 'ember' });
  }
  if (['D5', 'D8', 'D7', 'D1'].includes(room.id)) for (let x = 60; x < room.pw; x += 150) addLight(x, room.ph - 3 * TILE - 30, 150, '255,110,40', 0.45);
  const S = DP.sluice;
  if (S) for (let x = 16; x < room.pw; x += 40) addLight(x, S.y + 4, 70, '255,120,40', 0.95);
  if (Math.random() < 0.25) particles.push({ x: cam.x + rand(0, W), y: cam.y + H + 4, vx: rand(-4, 4), vy: -rand(18, 40), life: rand(3, 6), kind: 'ember', amb: true, sway: rand(0, 6) });
});
HOOKS.render.push(() => {
  if (!room || !room.grid) return;
  if (!dpDeep() && !room.grid.some(t => t === T_LAVA || t === T_BELT_L || t === T_BELT_R)) return;
  const fxs = sheet('tiles_deep_fx');
  const tx0 = Math.max(0, Math.floor(cam.x / TILE) - 1), tx1 = Math.min(room.w - 1, Math.floor((cam.x + W) / TILE) + 1);
  const ty0 = Math.max(0, Math.floor(cam.y / TILE) - 1), ty1 = Math.min(room.h - 1, Math.floor((cam.y + H) / TILE) + 1);
  const fr = Math.floor(time * 8);
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    const t = room.grid[ty * room.w + tx], px = tx * TILE, py = ty * TILE;
    if (t === T_LAVA) {
      const surf = lavaSurface(room, tx, ty), tag = surf ? 'lava_top' : 'lava_body';
      if (fxs.ok && fxs.has(tag)) { const tg = fxs.tag(tag), n = tg.to - tg.from + 1, f = fxs.frames[tg.from + (Math.floor(time * (surf ? 7 : 4)) + tx * 3 + ty) % n]; g.drawImage(fxs.img, f.x, f.y, 16, 16, px, py, 16, 16); }
      else if (surf) drawMagma(py + 3, px, px + 16, py + 16); else { g.fillStyle = '#6a1206'; g.fillRect(px, py, 16, 16); }
    } else if (t === T_BELT_L || t === T_BELT_R) drawBeltTile(g, null, px, py, tx, ty, room, t === T_BELT_L ? -fr : fr);
  }
  const S = DP.sluice;
  if (S && (S.active || S.done || S.armed)) drawMagma(S.y, Math.max(0, cam.x - 4), Math.min(room.pw, cam.x + W + 4), room.ph);
});

// ================================================================== fire shots + fire hazards (own lists: they carry burn / fire)
// shot: {x,y,vx,vy,g,r,dmg,burn,id,life,t,kind,onLand}  haz: {x,y,w,h,dmg,burn,tick,id,life,t,delay,active(),update(),draw()}
DP.shots = []; DP.haz = [];
HOOKS.enter.push(() => { DP.shots = []; DP.haz = []; });
function dpShot(o) { const s = { g: 520, r: 4, life: 3, t: 0, id: ++hazardId, kind: 'slag', burn: 30, ...o }; DP.shots.push(s); return s; }
function dpHaz(o) { const h = { w: 20, h: 12, life: 1, t: 0, id: ++hazardId, burn: 20, tick: 0, ...o }; DP.haz.push(h); return h; }
function hazRect(h) { return h.rect ? h.rect(h) : rect(h.x - h.w / 2, h.y - h.h, h.x + h.w / 2, h.y); }
function slagPuddle(x, y, life = 1.6, w = 22) {
  dpHaz({ x, y, w, h: 6, life, dmg: 6, burn: 16, tick: 0.45, kind: 'puddle',
    draw(h) { const a = Math.min(1, h.life * 1.5), fr = Math.floor(time * 10);
      g.fillStyle = `rgba(255,${120 + (fr % 3) * 20},40,${0.85 * a})`; g.fillRect(Math.round(h.x - h.w / 2 + 2), Math.round(h.y) - 2, h.w - 4, 2);
      g.fillStyle = `rgba(255,220,120,${a})`; g.fillRect(Math.round(h.x - h.w / 2 + 5), Math.round(h.y) - 3, h.w - 10, 1);
      if (Math.random() < 0.2) particles.push({ x: h.x + rand(-h.w / 2, h.w / 2), y: h.y - 2, vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'fire' });
      addLight(h.x, h.y - 3, 24, '255,120,40', 0.6 * a); } });
}
function updateDpShots(dt) {
  for (const s of DP.shots) {
    s.t += dt; s.life -= dt; s.vy += s.g * dt; s.x += s.vx * dt; s.y += s.vy * dt;
    if (Math.random() < 0.6) particles.push({ x: s.x, y: s.y, vx: -s.vx * 0.1, vy: rand(-15, 5), life: 0.35, kind: Math.random() < 0.5 ? 'fire' : 'ember' });
    addLight(s.x, s.y, 30, '255,130,50', 0.8);
    const r = rect(s.x - s.r, s.y - s.r, s.x + s.r, s.y + s.r);
    if (overlap(r, playerHurtbox())) { if (hurtPlayer(s.dmg, sign(s.vx), s.id, { fire: true, burn: s.burn })) { s.life = 0; spawnFx(fxOr('dp_splash', 'hit'), s.x, s.y + 4, 1, null, { bottom: true }); } }
    if (solidAtPx(s.x, s.y + s.r) || lavaCellAt(s.x, s.y)) {
      s.life = 0; sfx.fire();
      const fy = Math.floor((s.y + s.r) / TILE) * TILE;
      spawnFx(fxOr('dp_splash', 'hit'), s.x, fy, 1, null, { bottom: true });
      for (let i = 0; i < 7; i++) particles.push({ x: s.x, y: fy - 2, vx: rand(-60, 60), vy: -rand(40, 110), g: 380, life: 0.5, kind: 'fire' });
      if (s.onLand) s.onLand(s, fy); else if (solidAtPx(s.x, fy + 2)) slagPuddle(s.x, fy);
    }
  }
  DP.shots = DP.shots.filter(s => s.life > 0);
  for (const h of DP.haz) {
    if (h.delay > 0) { h.delay -= dt; if (h.delay <= 0 && h.onStart) h.onStart(h); continue; }
    h.life -= dt; h.t += dt;
    if (h.update) h.update(h, dt);
    if (h.active === undefined || h.active(h)) {
      if (overlap(hazRect(h), playerHurtbox())) hurtPlayer(h.dmg, h.dir || (P.x < h.x ? -1 : 1), h.tick ? h.id + '_' + Math.floor(h.t / h.tick) : h.id, { fire: true, burn: h.burn, parryable: false, src: h.src });
    }
  }
  DP.haz = DP.haz.filter(h => h.life > 0);
}
function drawDpShots() {
  const sh = fxSheet('dp_slag');
  for (const s of DP.shots) {
    if (sh.ok) { const t = sh.tag(Object.keys(sh.tags)[0]), n = t.to - t.from + 1; drawSprite(sh, t.from + Math.floor(s.t * 14) % n, s.x, s.y, sign(s.vx), { center: true }); }
    else { g.fillStyle = '#ffb040'; g.fillRect(Math.round(s.x) - 2, Math.round(s.y) - 2, 5, 5); g.fillStyle = '#ffe9a0'; g.fillRect(Math.round(s.x) - 1, Math.round(s.y) - 1, 2, 2); }
  }
  for (const h of DP.haz) if (!(h.delay > 0) && h.draw) h.draw(h);
}
HOOKS.update.push(dt => updateDpShots(dt));
HOOKS.render.push(() => drawGlow(drawDpShots));   // glowing shots stay bright under dynamic lighting

// ================================================================== enemies
Object.assign(ENEMY, {
  dp_slag_imp: { hp: 72, cinders: 95, speed: 82, aggro: 200, range: 170, poise: 12, stance: 45, dmg: { claw: 20 }, cool: [1.1, 1.9], lunge: { claw: 90 } },
  dp_forge_sentry: { hp: 320, cinders: 240, speed: 24, aggro: 170, range: 74, poise: 70, stance: 190, dmg: { bash: 40, jet: 11 }, cool: [1.3, 2.1], lunge: { bash: 120 } },
  dp_magma_crawler: { hp: 150, cinders: 160, speed: 52, aggro: 150, range: 34, poise: 25, stance: 80, dmg: { bite: 30, burst: 34 }, cool: [1.4, 2.4], lunge: { bite: 60 } },
});
Object.assign(ATTACK_TAGS, { dp_slag_imp: ['claw'], dp_forge_sentry: ['bash'], dp_magma_crawler: ['bite'] });
const DP_LIVE = ['hurt', 'stagger', 'parried', 'dead'];
function dpPre(e, dt) {   // the shared per-frame bookkeeping of Enemy.update (so subclasses can run their own brains)
  e.flash = Math.max(0, e.flash - dt * 5); e.poise = Math.max(0, e.poise - dt * 12); e.stance = Math.max(0, e.stance - dt * 6);
  e.bleed = Math.max(0, e.bleed - dt * 6); e.dmgT -= dt;
  if (e.rotT > 0) { e.rotT -= dt; e.hp -= e.maxHp * 0.025 * dt; if (e.hp <= 0) { e.die({ dir: 0 }); return false; } }
  e.anim.update(dt);
  if (!e.aggro && e.canSee()) { e.aggro = true; e.cool = Math.max(e.cool, 0.5); }
  if (e.aggro && (Math.abs(e.dist()) > e.cfg.aggro * 1.9 || Math.abs(P.y - e.y) > 170 || P.state === 'dead')) { e.lostT += dt; if (e.lostT > 2.5) { e.aggro = false; e.lostT = 0; } } else e.lostT = 0;
  e.cool -= dt;
  return true;
}
function metaPt(e, key, fallback) { const m = e.sh.meta && e.sh.meta.spawn && e.sh.meta.spawn[key]; return m ? metaPoint(e.sh, e, m.at) : fallback; }

// ---- slag imp: a wiry forge-imp that darts about, hurls molten slag in arcs and hops away from blades
class DpImp extends Enemy {
  update(dt) {
    if (DP_LIVE.includes(this.state)) return super.update(dt);
    if (!dpPre(this, dt)) return;
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    this.hopCool = (this.hopCool || 0) - dt;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        const back = -sign(dx);
        if (adx < 44 && this.hopCool <= 0 && Math.abs(dy) < 30 && ledgeAhead({ x: this.x + back * 34, y: this.y, w: this.w }, back) && !lavaNear(this.x + back * 40, this.y, 0)) {
          this.state = 'hop'; this.anim.set(this.sh.has('hop') ? 'hop' : 'idle', false); this.vx = back * 150; this.vy = -200; this.hopCool = 2.2; sfx.jump(); break;
        }
        if (adx < 30 && Math.abs(dy) < 24 && this.cool <= 0) { this.startAttack('claw'); break; }
        if (this.cool <= 0 && adx < c.range && adx > 36 && Math.abs(dy) < 120 && this.canSee()) { this.startAttack('throw'); this.thrown = false; break; }
        const want = adx < 70 ? back : adx > 130 ? sign(dx) : 0;
        this.walk(want, dt, want === back ? 0.7 : 1);
        break;
      }
      case 'hop':
        this.gravity(dt);
        if (this.ground && this.vy >= 0) { this.setA('idle', 'idle'); this.cool = Math.min(this.cool, 0.25); }
        break;
      case 'attack': {
        const an = this.anim;
        if (this.atk === 'throw') {
          if (an.i < 4) this.facePlayer();
          if (an.changed && an.i === 3) { const p = metaPt(this, 'throw', { x: this.x - this.face * 6, y: this.y - 22 }); spawnFx('telegraph', p.x, p.y, this.face); }
          const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.throw;
          if (!this.thrown && an.i >= (sp ? sp.frame : 5)) {
            this.thrown = true;
            const at = metaPt(this, 'throw', { x: this.x + this.face * 6, y: this.y - 24 });
            const T = clamp(Math.abs(P.x - at.x) / 190, 0.45, 0.85), tx = P.x + P.vx * 0.25;
            dpShot({ x: at.x, y: at.y, vx: (tx - at.x) / T, vy: ((P.y - 8 - at.y) - 0.5 * 520 * T * T) / T, dmg: 22 * NGP.dmg, burn: 32 });
            sfx.shoot(); sfx.fire();
          }
          this.vx *= Math.pow(0.004, dt); this.gravity(dt);
          if (an.done) { this.setA('idle', 'idle'); this.cool = rand(...c.cool); }
        } else this.updateAttack(dt);
        break;
      }
    }
    if (this.alive && Math.random() < 0.12) particles.push({ x: this.x + rand(-4, 4), y: this.y - rand(6, 20), vx: 0, vy: -rand(10, 25), life: 0.5, kind: 'ember' });
    addLight(this.x, this.y - 14, 30, '255,130,50', 0.55);
  }
}

// ---- forge sentry: slow armoured automaton-knight; frontal blows glance off its plate; a flame jet at close range
class DpSentry extends Enemy {
  hit(info) {
    if (this.alive && !info.crit && info.kind !== 'heavy' && info.kind !== 'env' && info.dir === -this.face && ['idle', 'walk', 'attack'].includes(this.state)) {
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); hitstop = Math.max(hitstop, 0.04);
      for (let i = 0; i < 4; i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(-80, -20), vy: -rand(20, 80), g: 300, life: 0.4, kind: 'spark' });
      if (info.melee) { P.vx = -P.face * 70; }
      return super.hit({ ...info, dmg: info.dmg * 0.3, poise: info.poise * 0.5, quiet: true });
    }
    return super.hit(info);
  }
  turnSlow(dt) {   // armour makes it slow to turn: the player can flank it
    const want = P.x < this.x ? -1 : 1;
    if (want === this.face) { this.turnT = 0; return; }
    this.turnT = (this.turnT || 0) + dt;
    if (this.turnT > 0.55) { this.face = want; this.turnT = 0; }
  }
  update(dt) {
    if (DP_LIVE.includes(this.state)) return super.update(dt);
    if (!dpPre(this, dt)) return;
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.turnSlow(dt);
        const front = sign(dx) === this.face;
        if (front && this.cool <= 0 && Math.abs(dy) < 30) {
          if (adx < 30) { this.startAttack('bash'); break; }
          if (adx < 70) { this.atk = 'jet'; this.hitIds = new Set(); this.atkId = ++hazardId; this.setA('attack', 'jet', false); this.jetFx = null; break; }
        }
        this.walk(front && adx > 44 ? this.face : 0, dt, 1);
        break;
      }
      case 'attack': {
        const an = this.anim;
        if (this.atk !== 'jet') { this.updateAttack(dt); break; }
        const J = (this.sh.meta && this.sh.meta.jet_frames) || [5, 10];
        const noz = metaPt(this, 'jet', { x: this.x + this.face * 16, y: this.y - 24 });
        if (an.changed && an.i === Math.max(0, J[0] - 3)) { spawnFx('telegraph', noz.x, noz.y, this.face); sfx.glint(); }
        if (an.i < J[0] - 1) addLight(noz.x, noz.y, 20 + an.i * 4, '255,150,60', 0.8);
        if (an.i >= J[0] && an.i <= J[1]) {
          if (an.changed && an.i === J[0]) { sfx.fire(); this.jetId = ++hazardId; }
          const L = 62, x0 = noz.x, x1 = noz.x + this.face * L;
          const r = rect(Math.min(x0, x1), noz.y - 9, Math.max(x0, x1), noz.y + 12);
          this.flameT = (this.flameT || 0) + dt;
          if (overlap(r, playerHurtbox())) hurtPlayer(c.dmg.jet * NGP.dmg, this.face, this.jetId + '_' + Math.floor(this.flameT / 0.22), { fire: true, burn: 22 });
          addLight(noz.x + this.face * 30, noz.y, 60, '255,140,50', 1);
          if (Math.random() < 0.9) particles.push({ x: noz.x + this.face * rand(4, L), y: noz.y + rand(-6, 6), vx: this.face * rand(60, 140), vy: -rand(10, 40), life: 0.35, kind: Math.random() < 0.6 ? 'fire' : 'ember' });
          this.jetting = { x: noz.x, y: noz.y, t: an.i - J[0] };
        } else this.jetting = null;
        this.vx *= Math.pow(0.004, dt); this.gravity(dt);
        if (an.done) { this.jetting = null; this.setA('idle', 'idle'); this.cool = rand(...c.cool); }
        break;
      }
    }
  }
  draw() {
    super.draw();
    if (this.jetting && this.alive) {
      const s = fxSheet('dp_flame');
      if (s.ok) { const t = s.tag(Object.keys(s.tags)[0]), n = t.to - t.from + 1; drawSprite(s, t.from + Math.floor(time * 16) % n, this.jetting.x, this.jetting.y, this.face, { pivot: [0, Math.floor(s.fh / 2)] }); }
      else { g.fillStyle = 'rgba(255,150,60,0.8)'; g.fillRect(Math.round(Math.min(this.jetting.x, this.jetting.x + this.face * 60)), Math.round(this.jetting.y - 6), 60, 12); }
    }
  }
}

// ---- magma crawler: a plated lava-salamander that swims under the slag and bursts out at whoever stands near the pool
class DpCrawler extends Enemy {
  constructor(type, x, y, key) {
    super(type, x, y, key);
    const tx = Math.floor(x / TILE), ty = Math.floor((y - 1) / TILE);
    let l = tx, r = tx;
    while (tileAtR(room, l - 1, ty) === T_LAVA) l--;
    while (tileAtR(room, r + 1, ty) === T_LAVA) r++;
    this.pool = { x0: l * TILE + 8, x1: (r + 1) * TILE - 8, y: ty * TILE };
    this.state = 'sub'; this.y = this.pool.y + 13; this.anim.set(this.sh.has('sub') ? 'sub' : 'idle', true); this.cool = rand(0.6, 1.4);
  }
  hurtbox() { if (this.state === 'sub' || this.state === 'surfacing') return null; return super.hurtbox(); }
  critable() { return super.critable(); }
  update(dt) {
    if (this.state === 'dead') return super.update(dt);
    if (['hurt', 'stagger', 'parried'].includes(this.state)) { super.update(dt); if (this.alive && inLava(this, 8) && this.state === 'hurt') this.submerge(); return; }
    if (!dpPre(this, dt)) return;
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'sub': {
        const near = Math.abs(P.x - clamp(P.x, this.pool.x0, this.pool.x1)) < 90 && dy > -110 && dy < 40 && P.state !== 'dead';
        const tx = clamp(near ? P.x : (this.pool.x0 + this.pool.x1) / 2 + Math.sin(time * 0.7 + this.id) * 20, this.pool.x0, this.pool.x1);
        this.x = approach(this.x, tx, 55 * dt); this.face = tx < this.x ? -1 : this.face;
        if (tx > this.x + 1) this.face = 1;
        this.y = this.pool.y + 13;
        if (Math.random() < 0.15) particles.push({ x: this.x + rand(-10, 10), y: this.pool.y + 2, vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'ember' });
        if (near && this.cool <= 0 && Math.abs(P.x - this.x) < 100) {
          this.state = 'surfacing'; this.anim.set(this.sh.has('burst') ? 'burst' : 'idle', false); this.facePlayer(); this.atkId = ++hazardId;
          spawnFx('telegraph', this.x, this.pool.y - 4, this.face); sfx.glint();
        }
        break;
      }
      case 'surfacing': {   // bubbling telegraph, then the leap
        this.facePlayer(); this.y = this.pool.y + 13 - Math.min(6, this.anim.i * 2);
        if (Math.random() < 0.7) particles.push({ x: this.x + rand(-12, 12), y: this.pool.y + 1, vx: rand(-20, 20), vy: -rand(30, 90), g: 300, life: 0.5, kind: 'fire' });
        addLight(this.x, this.pool.y, 40 + this.anim.i * 6, '255,160,60', 1);
        const lf = (this.sh.meta && this.sh.meta.burst_leap) || 3;
        if (this.anim.i >= lf) {
          this.state = 'leap'; this.y = this.pool.y - 18; this.ground = false;
          const T = 0.62, tx = clamp(P.x, this.x - 150, this.x + 150);
          this.vx = (tx - this.x) / T; this.vy = -320; sfx.fire(); sfx.swing();
          spawnFx(fxOr('dp_splash', 'hit'), this.x, this.pool.y + 4, 1, null, { bottom: true });
          for (let i = 0; i < 14; i++) particles.push({ x: this.x + rand(-8, 8), y: this.pool.y, vx: rand(-80, 80), vy: -rand(60, 200), g: 420, life: 0.6, kind: Math.random() < 0.5 ? 'fire' : 'ember' });
        }
        break;
      }
      case 'leap': {
        this.vy = Math.min(this.vy + 800 * dt, 420); moveBody(this, dt); this.clampRoom();
        this.face = this.vx < 0 ? -1 : 1;
        const hb = super.hurtbox();
        if (hb && overlap(hb, playerHurtbox())) hurtPlayer(c.dmg.burst * NGP.dmg, this.face, this.atkId, { fire: true, burn: 35, parryable: false, src: this });
        if (this.vy > 0 && inLava(this, 2)) { this.submerge(); break; }
        if (this.ground) { this.state = 'walk'; this.setA('walk', 'crawl'); this.landT = 0; this.cool = 0.6; shake = Math.max(shake, 2); spawnFx('dust', this.x, this.y, 1); }
        break;
      }
      case 'idle': case 'walk': {
        this.landT = (this.landT || 0) + dt;
        const home = (this.pool.x0 + this.pool.x1) / 2, goHome = this.landT > 6 || this.hp < this.maxHp * 0.35 || !this.aggro;
        if (inLava(this, 6)) { this.submerge(); break; }
        if (goHome) {
          const d = sign(home - this.x); this.face = d;
          this.vx = approach(this.vx, d * c.speed, 400 * dt); if (this.anim.tag !== 'crawl') this.setA('walk', 'crawl');
          this.gravity(dt);
          if (Math.abs(home - this.x) < 30 || lavaNear(this.x + d * 12, this.y, 0)) { this.vx = d * 70; this.vy = -160; this.ground = false; this.state = 'leap'; this.atkId = ++hazardId; this.anim.set(this.sh.has('burst') ? 'burst' : 'idle', false); this.anim.i = Math.min(4, this.anim.n - 1); }
          break;
        }
        this.facePlayer();
        if (adx < 34 && Math.abs(dy) < 24 && this.cool <= 0) { this.startAttack('bite'); break; }
        let want = adx > 26 ? sign(dx) : 0;
        if (want && lavaNear(this.x + want * 14, this.y, 0) && !ledgeAhead(this, want)) want = 0;
        this.walk(want, dt, 1, 'walk');
        if (this.anim.tag === 'walk' && this.sh.has('crawl')) this.anim.set('crawl', true);
        break;
      }
      case 'attack': this.updateAttack(dt); break;
    }
    addLight(this.x, this.y - 8, this.state === 'sub' ? 24 : 34, '255,120,40', 0.7);
  }
  submerge() {
    this.state = 'sub'; this.vx = 0; this.vy = 0; this.y = this.pool.y + 13; this.x = clamp(this.x, this.pool.x0, this.pool.x1);
    this.anim.set(this.sh.has('sub') ? 'sub' : 'idle', true); this.cool = rand(1.2, 2.2); this.hp = Math.min(this.maxHp, this.hp + this.maxHp * 0.15);
    spawnFx(fxOr('dp_splash', 'hit'), this.x, this.pool.y + 4, 1, null, { bottom: true }); sfx.fire();
  }
  draw() {
    if (this.state === 'sub') { if (this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, {}); return; }
    super.draw();
  }
}
Object.assign(ENEMY_CLASSES, { dp_slag_imp: DpImp, dp_forge_sentry: DpSentry, dp_magma_crawler: DpCrawler });

// ================================================================== the Forge Overseer (mini-boss, D5 Foundry Halls)
// Its tower forge-shield blocks every frontal blow (chip damage + guard meter): flank it (it turns slowly), break its guard
// with heavy blows, or punish the slam when the shield is hauled overhead. Camping behind it earns a blast from its vents.
BOSS_INFO.overseer = { name: 'The Forge Overseer', hp: 2500, cinders: 7000, reward: ['w:overseer_bulwark', 'c_brand'],
  quote: 'Ashwright built it to keep the forge. No one ever told it the forge had gone out.' };
function flameDir(b, i) {
  const m = b.sh.meta, a = ((m.flame_ang && m.flame_ang[i]) ?? 0) * Math.PI / 180;
  return { x: Math.cos(a) * b.face, y: Math.sin(a), a };
}
function makeOverseer(x, y) {
  const meta = ASSETS.overseer_meta;
  if (meta && meta.attacks && meta.attacks.vent) { meta.ventHit = meta.attacks.vent.hit; delete meta.attacks.vent; }
  const B = new MetaBoss('overseer', x, y, {
    sheets: ['overseer'], stanceMax: 300, walkSpeed: 30, prefer: 64, p2at: 0.5, p2speed: 1.2, p2tag: 'vent', critRange: 52,
    introTag: 'vent', cool1: [1.0, 1.6], cool2: [0.6, 1.1], victory: 'THE WARDEN IS EXTINGUISHED', deathParticle: 'fire', guard: 0, hot: false,
    onIntro() { sfx.roar(); shake = 5; },
    onPhase2() { this.hot = true; flashScreen = 0.4; shake = 8; sfx.roar(); toast('Its furnace overheats — the shield glows white-hot', 3); },
    weights(d, p2) {
      const behind = (P.x - this.x) * this.face < 0;
      if (behind && d < 120) return { vent: 6 };
      if (d < 56) return { bash: 1.4, slam: 2.2, flame: 1.2, vent: 0.5 };
      if (d < 140) return { flame: 3, bash: 2, slam: 1, walk: 1 };
      return { walk: 3, bash: 1.4, flame: p2 ? 1.4 : 0.5 };
    },
    chains: { flame(d) { return d < 90 ? 'bash' : null; }, bash: 'slam', slam(d) { return d < 150 ? 'flame' : null; } },
    moves: {
      bash: { dmg: [44], step: 200, body: true, shake: 4 },
      slam: { dmg: [58], shake: 9, on: { 7() {
        const q = metaRect(this.sh, this, this.sh.meta.attacks.slam.hit), cx = this.face > 0 ? q.x1 - 8 : q.x0 + 8;
        sfx.boom(); spawnFx('shockwave', cx, this.floor, 1); spawnFx(fxOr('dp_burst', 'hit'), cx, this.floor - 10, 1);
        for (const dd of [-1, 1]) hazards.push({ x: cx, y: this.floor, vx: dd * 165, w: 14, h: 14, dmg: BOSS_DMG * 30 * NGP.dmg, id: ++hazardId, life: 1.5, wave: true, dir: dd, color: 'root' });
        if (this.phase === 2) for (const dd of [-40, 40]) slagPuddle(cx + dd, this.floor, 3, 30);
      } } },
      vent: { dmg: [], on: { 4() {
        const r = this.sh.meta.ventHit || [0, 4, 30, 52], box = metaRect(this.sh, this, r);
        sfx.fire(); sfx.boom(); shake = Math.max(shake, 5);
        dpHaz({ x: (box.x0 + box.x1) / 2, y: box.y1, w: box.x1 - box.x0 + (this.phase === 2 ? 26 : 10), h: box.y1 - box.y0, life: 0.45, dmg: BOSS_DMG * 34 * NGP.dmg, burn: 45, src: this,
          draw(h) { if (Math.random() < 0.9) for (let k = 0; k < 3; k++) particles.push({ x: h.x + rand(-h.w / 2, h.w / 2), y: h.y - rand(0, h.h), vx: -B.face * rand(40, 120), vy: -rand(10, 60), life: 0.4, kind: Math.random() < 0.6 ? 'fire' : 'ember' }); addLight(h.x, h.y - h.h / 2, 70, '255,140,50', 1); } });
      } } },
      flame: { dmg: [] },
    },
    wake() { return P.x < room.pw - 4 * TILE - 24 && P.x > 3 * TILE; },
    ambient(dt) {
      addLight(this.x, this.y - 40, this.hot ? 90 : 60, '255,140,60', 0.8);
      if (this.hot && Math.random() < 0.3) particles.push({ x: this.x + this.face * rand(10, 26), y: this.y - rand(10, 60), vx: 0, vy: -rand(10, 40), life: 0.6, kind: 'fire' });
      this.guard = Math.max(0, this.guard - dt * (this.state === 'attack' ? 4 : 9));
      this.flaming = null;
      if (this.state === 'attack' && this.atk === 'flame' && this.alive) {
        const m = this.sh.meta, FF = m.flame_frames || [5, 14], i = this.anim.i;
        if (i >= FF[0] && i <= FF[1] && m.nozzle) {
          const n = metaPoint(this.sh, this, m.nozzle[i]), d = flameDir(this, i), L = this.phase === 2 ? 155 : 140;
          this.flaming = { x: n.x, y: n.y, d, L };
          if (this.anim.changed && i === FF[0]) { sfx.fire(); this.flameId = ++hazardId; this.flameT = 0; }
          this.flameT = (this.flameT || 0) + dt;
          const hb = playerHurtbox();
          for (let s = 8; s <= L; s += 8) {
            const px = n.x + d.x * s, py = n.y + d.y * s, r = 5 + s * 0.09;
            if (solidAtPx(px, py)) { if (this.phase === 2 && Math.random() < dt * 5) slagPuddle(px, Math.floor(py / TILE) * TILE, 2.5, 24); break; }
            if (overlap(rect(px - r, py - r, px + r, py + r), hb)) { hurtPlayer(BOSS_DMG * 16 * NGP.dmg, this.face, this.flameId + '_' + Math.floor(this.flameT / 0.2), { fire: true, burn: 22 }); break; }
            if (s % 24 === 0) addLight(px, py, 40 + s * 0.2, '255,150,60', 1);
          }
        }
      }
      // phase 2: the white-hot shield sears on contact
      if (this.hot && this.alive && this.active) {
        const m = this.sh.meta;
        if (m && m.shield && overlap(metaRect(this.sh, this, m.shield), playerHurtbox())) hurtPlayer(BOSS_DMG * 12 * NGP.dmg, this.face, 'osh' + Math.floor(time * 2), { fire: true, burn: 25 });
      }
    },
  });
  B.facePlayer = function () {
    const want = P.x < this.x ? -1 : 1;
    if (want === this.face || !this.active || this.introT > 0) { this.face = want; this.behindSince = undefined; return; }
    if (this.behindSince === undefined) this.behindSince = time;
    if (time - this.behindSince > (this.phase === 2 ? 0.4 : 0.6)) { this.face = want; this.behindSince = undefined; }
  };
  B.shieldUp = function () { return !(this.state === 'stagger' || this.state === 'dead' || (this.state === 'attack' && this.atk === 'slam' && this.anim.i >= 1 && this.anim.i <= 8)); };
  B.hit = function (info) {
    if (this.alive && this.active && !info.crit && info.kind !== 'env' && info.dir === -this.face && this.shieldUp()) {
      const heavy = info.kind === 'heavy';
      this.guard += heavy ? (info.charged ? 62 : 36) : info.kind === 'spell' ? 10 : 13;
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); hitstop = Math.max(hitstop, heavy ? 0.08 : 0.05); shake = Math.max(shake, 2);
      for (let i = 0; i < 6; i++) particles.push({ x: info.x, y: info.y, vx: -info.dir * rand(20, 100), vy: -rand(20, 90), g: 300, life: 0.45, kind: 'spark' });
      if (info.melee) { P.vx = -P.face * (heavy ? 60 : 110); P.st -= heavy ? 4 : 9; }
      const chip = Math.round(info.dmg * (heavy ? 0.3 : 0.1));
      this.hp = Math.max(1, this.hp - chip); this.dmgShown = this.dmgT > 0 ? this.dmgShown + chip : chip; this.dmgT = 2.2; this.flash = 0.3;
      if (this.guard >= 100) {
        this.guard = 0;
        if (this.stanceImmune > 0) { this.guard = 70; return; }
        toast('Guard broken!', 1.6); sfx.crumble(); this.air = null; this.stagger(); this.t = 2.4;
      }
      return;
    }
    const back = info.dir === this.face;
    MetaBoss.prototype.hit.call(this, back && !info.crit ? { ...info, dmg: info.dmg * 1.15, poise: info.poise * 1.3 } : info);
  };
  B.draw = function () {
    MetaBoss.prototype.draw.call(this);
    if (this.hot && this.alive && this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, { alpha: 0.18 + 0.08 * Math.sin(time * 9), flash: 1, flashColor: '#ff6a20', blend: 'lighter' });
    const f = this.flaming;
    if (f) {
      const s = fxSheet('dp_breath');
      if (s.ok) { const t = s.tag(Object.keys(s.tags)[0]), n = t.to - t.from + 1; drawSprite(s, t.from + Math.floor(time * 14) % n, f.x, f.y, this.face, { pivot: [0, Math.floor(s.fh / 2)], rot: f.d.a }); }
      else { g.fillStyle = 'rgba(255,140,50,0.8)'; g.fillRect(Math.round(f.x), Math.round(f.y) - 6, this.face * f.L, 12); }
    }
  };
  return B;
}
BOSS_SPAWN.overseer = (cx, fy) => makeOverseer(cx, fy);
HOOKS.hud.push(() => {   // the Overseer's guard meter under its health bar
  if (!boss || boss.kind !== 'overseer' || !boss.active || !boss.alive) return;
  bar(156, 208, 70, 1.5, boss.guard / 100, 0, boss.guard > 70 ? '#ffb040' : '#b08a3a');
  text('guard', 230, 210, 4.5, '#c9a060', 'left', { weight: 500 });
});

// ================================================================== the Molten Colossus (main boss, D8 The Crucible)
// A near-invulnerable forge-god: every blow on its obsidian body or iron plates only chips 5 HP (clang + tiny numbers).
// The way to win is its LEGS: hits on the legs fill a TOPPLE meter (glowing cracks spread over its knees, a bar under the
// health bar). When it fills, the Colossus crashes forward and its molten CORE (the heart) lies bare near the ground for a
// few seconds -- core hits deal 1.8x damage and it can be riposted. It heaves itself up with a shockwave and the cycle
// repeats. Phase 2 (50%): the shell sloughs off and it adds arena-wide AOEs (eruptions with safe gaps, shockwave rings,
// wide slag rain, a lava flood over one half, marching fire-pillar lines).
BOSS_INFO.colossus = { name: 'The Molten Colossus', hp: 5200, cinders: 24000, reward: ['slam', 'w:colossus_hammer', 'c_core'],
  quote: '“A god to work the anvil when my arm gave out.” — Ashwright' };
const COL_DMG = { slam: 70, fist: 58, stomp: 40, sweep: 52 };
const COL_BODY_DMG = 5, COL_CORE_MULT = 2.0, COL_TOPPLE = 100;
const COL_ANIM = { erupt: 'rain', flood: 'rain', pillars: 'fist', rings: 'stomp', kstomp: 'stomp' };
class Colossus extends BossBase {
  constructor(x, y) {
    super('colossus', x, y);
    this.meta = ASSETS.colossus_meta || { sheets: { p1: {}, p2: {} }, frames: {}, attacks: {}, telegraph: {}, anchor: [107, 176] };
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.colossus.hp * NGP.hp);
    const names = new Set([...Object.values(this.meta.sheets.p1), ...Object.values(this.meta.sheets.p2)]);
    for (const n of names) { sheet(n, { meta: this.meta }); if (ASSETS[n + '_pl']) sheet(n + '_pl', { meta: this.meta }); }
    this.stanceMax = 1e9; this.critRange = 80; this.face = 1; this.speed = 1; this.grabCool = 8; this.behindT = 0;
    this.topple = 0; this.toppleIdle = 0; this.topples = 0; this.aoeRun = 0;
    this.setA('dormant', 'stagger', false); this.anim.i = this.anim.n - 1; this.anim.done = true;
    this.parts = ['knee_n', 'knee_f', 'chest', 'arm', 'body'].map(n => this.mkPart(n));
    this.plates = { knee_n: true, knee_f: true, arm: true, chest: true };
  }
  mkPart(name) {
    const B = this;
    return { name, boss: true, x: B.x, y: B.floor, face: 1, critRange: 80,
      get alive() { return B.alive && B.active; },
      hurtbox() { return B.partRect(name); },
      hit(info) { B.partHit(this, info); },
      critable() { return name === 'chest' && B.critable(); },
      onCritStart() { B.onCritStart(); },
      onParried() {} };
  }
  sheetFor(tag) { const m = this.meta.sheets; return sheet((this.phase === 2 || !m.p1[tag]) ? (m.p2[tag] || m.p1[tag]) : m.p1[tag], { meta: this.meta }); }
  setA(state, tag, loop = true, speed = 1) { this.state = state; this.tag = tag; this.sh = this.sheetFor(tag); this.anim = new Anim(this.sh, tag, loop, this.speed * speed); }
  fd() { const f = this.meta.frames[this.tag]; return f ? f[Math.min(this.anim.i, f.length - 1)] : null; }
  pt(p) { return { x: this.x + (p[0] - 107) * this.face, y: this.y - 176 + p[1] }; }
  mrect(r) { return this.face > 0 ? rect(this.x + r[0] - 107, this.y - 176 + r[1], this.x + r[0] + r[2] - 107, this.y - 176 + r[1] + r[3])
                                  : rect(this.x - (r[0] + r[2] - 107), this.y - 176 + r[1], this.x - (r[0] - 107), this.y - 176 + r[1] + r[3]); }
  get exposed() { return this.state === 'toppled' || (this.state === 'rising' && this.anim.i <= 1); }
  partRect(name) {
    const f = this.fd(); if (!f || !f.parts || !this.alive) return null;
    const P_ = f.parts;
    if (name === 'knee_n' || name === 'knee_f') {        // the whole lower leg: knee plate down to the foot
      const k = this.mrect(P_[name]), ft = this.pt(f.feet[name === 'knee_n' ? 0 : 1]);
      return rect(Math.min(k.x0, ft.x - 13), k.y0, Math.max(k.x1, ft.x + 13), this.floor);
    }
    if (name === 'body') {                                // torso / hips: anything between the chest and the knees
      const c = this.mrect(P_.chest), a = this.mrect(P_.knee_n), b = this.mrect(P_.knee_f);
      const x0 = Math.min(a.x0, b.x0) + 6, x1 = Math.max(a.x1, b.x1) - 6;
      return rect(Math.min(x0, c.x0), c.y0 - 24, Math.max(x1, c.x1), Math.min(a.y0, b.y0) - 1);
    }
    return P_[name] ? this.mrect(P_[name]) : null;
  }
  get L() { return TILE + 70; }
  get R() { return room.pw - TILE - 70; }
  hurtbox() { return this.partRect('body'); }
  canStagger() { return false; }
  wake() { return P.x < room.pw - 7 * TILE; }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  // ---- damage model
  chip(info) {
    if (time - (this.chipT || -9) < 0.1) { spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); return; }   // one chip per blow
    this.chipT = time;
    const n = COL_BODY_DMG;
    this.hp = Math.max(1, this.hp - n); this.flash = Math.max(this.flash, 0.25);
    this.dmgShown = this.dmgT > 0 ? this.dmgShown + n : n; this.dmgT = 2.2;
    popup(info.x, info.y - 6, n, '#b8b0a0'); sfx.block(); hitstop = Math.max(hitstop, info.big ? 0.06 : 0.035);
    spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir);
    for (let i = 0; i < 5; i++) particles.push({ x: info.x, y: info.y, vx: -info.dir * rand(20, 110), vy: -rand(20, 100), g: 320, life: 0.45, kind: 'spark' });
    if (info.melee && !info.big) P.vx = -P.face * 40;
  }
  partHit(part, info) {
    if (!this.alive || !this.active) return;
    if (part.name === 'chest' && this.exposed) {           // the molten core: real damage
      const t0 = this.t;
      spawnFx(fxOr('dp_burst', 'hit'), info.x, info.y, info.dir);
      for (let i = 0; i < 8; i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 120), vy: -rand(30, 130), g: 380, life: 0.6, kind: 'fire' });
      super.hit({ ...info, dmg: info.dmg * (info.crit ? 1.5 : COL_CORE_MULT), poise: 0 });
      if (info.crit) this.t = Math.max(this.t, t0 - 0.6);   // a riposte never cuts the window short
      return;
    }
    this.chip(info);
    if ((part.name === 'knee_n' || part.name === 'knee_f') && !this.exposed && this.state !== 'shed' && this.state !== 'rising') {
      // leg damage follows the weight of the blow (its poise): a dagger jab ~2, a sword cut ~4, heavies 8-11, a charged great weapon ~19
      const amt = info.kind === 'spell' ? 2.5 : clamp(4 * Math.sqrt(Math.max(1, info.poise || 12) / 12), 1.5, 22);
      this.topple += amt; this.toppleIdle = 0;
      spawnFx('hit', info.x, info.y, info.dir, null, { tint: '#ff8a30' });
      if (this.topple >= this.toppleMax()) this.doTopple();
    }
  }
  toppleMax() {   // grows with every fall (x2 at most) and with the boss's HP scaling (difficulty, strength-matching)
    const adapt = typeof adaptCur !== 'undefined' && adaptCur.kind === 'colossus' ? adaptCur.hp : 1, diff = typeof diffCfg === 'function' ? diffCfg().bossHp : 1;
    return COL_TOPPLE * Math.min(2, 1 + 0.3 * this.topples) * Math.sqrt(adapt * diff);
  }
  doTopple() {
    this.topple = 0; this.topples++; this.air = null; this.breathing = null; this.critDone = false; this.chain = 0;
    if (room.crucible) { room.crucible.hold = undefined; room.crucible.pouring = false; }
    this.pourDir = undefined; this.flooded = false;
    this.setA('toppled', 'topple', false); this.t = (this.phase === 2 ? 4.4 : 5.4) + this.anim.total();
    sfx.crumble(); sfx.roar(); shake = 6;
    if (this.topples === 1) toast('It topples! Strike the glowing core!', 3);
  }
  critable() { return this.state === 'toppled' && this.anim.i >= 3 && !this.critDone; }
  breakPlate(name) {
    if (!this.plates[name]) return;
    this.plates[name] = false;
    const r = this.partRect(name) || rect(this.x - 10, this.y - 60, this.x + 10, this.y - 40), cx = (r.x0 + r.x1) / 2, cy = (r.y0 + r.y1) / 2;
    sfx.crumble(); shake = Math.max(shake, 8);
    spawnFx(fxOr('dp_burst', 'hit'), cx, cy, 1);
    for (let i = 0; i < 5; i++) spawnFx(fxOr('dp_debris', 'hit'), cx + rand(-10, 10), cy + rand(-8, 8), 1, null, { speed: rand(0.6, 1.2) });
    for (let i = 0; i < 24; i++) particles.push({ x: cx + rand(-8, 8), y: cy + rand(-8, 8), vx: rand(-140, 140), vy: -rand(40, 200), g: 460, life: rand(0.6, 1.2), kind: i % 3 ? 'rock' : 'fire' });
  }
  activate() {
    if (this.active || this.cutting) return;
    if (bossCutsceneStart(this)) return;
    this.active = true; bossBanner = { name: this.name, t: 0 }; sfx.roar(); shake = 8; this.setA('idle', 'idle'); this.cool = 1;
  }
  // ---- attack choice
  weights(d, nearLegs, behind) {
    const p2 = this.phase === 2, w = {};
    if (nearLegs) Object.assign(w, { stomp: 3.0, kstomp: 1.6, sweep: 1.2, fist: behind ? 0 : 1.0 });
    else if (d < 180) Object.assign(w, { slam: 2.4, fist: 1.2, sweep: 2.0, breath: 1.6 });
    else Object.assign(w, { breath: 1.6, rain: 1.4, walk: 2.2, sweep: 0.6 });
    if (behind && !nearLegs) w.stomp = (w.stomp || 0) + 2;
    w.rain = (w.rain || 0.5) * (p2 ? 1.4 : 1);
    if (this.grabCool <= 0 && room.crucible) w.grab = p2 ? 2.5 : 2.2;
    if (p2) {
      const aoe = this.aoeRun >= 2 ? 0.25 : 1;       // never three area attacks in a row
      Object.assign(w, { erupt: 1.6 * aoe, flood: 1.2 * aoe, pillars: 1.5 * aoe, rings: (nearLegs ? 2.2 : 1.2) * aoe });
      if (w.rain) w.rain *= aoe;
    }
    if (w[this.last]) w[this.last] *= 0.25;
    return w;
  }
  pick() {
    const d = Math.abs(P.x - this.x), behind = (P.x - this.x) * this.face < 0;
    const f = this.fd(), feet = f ? f.feet.map(q => this.pt(q).x) : [this.x];
    const nearLegs = feet.some(x => Math.abs(P.x - x) < 46) || d < 60;
    const e = Object.entries(this.weights(d, nearLegs, behind)).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e[0][0];
  }
  start(m) {
    this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {};
    this.aoeRun = ['erupt', 'flood', 'pillars', 'rings', 'rain', 'grab'].includes(m) ? this.aoeRun + 1 : 0;
    if (m === 'walk') { this.setA('walk', 'walk'); this.t = rand(1.0, 1.8); return; }
    if (m === 'grab') {
      const cr = room.crucible; this.facePlayer();
      this.gotoX = clamp(cr.hx + 30 * this.face, this.L, this.R); this.gotoT = 4.5;
      if (Math.abs(this.x - this.gotoX) > 14) { this.setA('goto', 'walk'); return; }
    }
    if (m !== 'stomp' && m !== 'kstomp' && m !== 'rings') this.facePlayer();
    this.setA('attack', COL_ANIM[m] || m, false, m === 'kstomp' ? 1.35 : 1);
  }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    for (const pt of this.parts) { const r = this.partRect(pt.name); if (r) pt.x = (r.x0 + r.x1) / 2; pt.y = this.floor; pt.face = this.face; }
    this.ambient(dt);
    if (!this.active) { if (this.state === 'dormant' && an.done) an.hold(); if (this.wake()) this.activate(); return; }
    this.grabCool -= dt;
    this.toppleIdle += dt;
    if (this.toppleIdle > 2.5 && !this.exposed) this.topple = Math.max(0, this.topple - dt * 7);
    const d = Math.abs(P.x - this.x), behind = (P.x - this.x) * this.face < 0;
    switch (this.state) {
      case 'idle': case 'walk': {
        this.cool -= dt;
        if (behind) { this.behindT += dt; if (this.behindT > (this.phase === 2 ? 0.55 : 0.85)) { this.facePlayer(); this.behindT = 0; } } else this.behindT = 0;
        if (P.state === 'dead') { if (this.state !== 'idle') this.setA('idle', 'idle'); break; }
        if (this.state === 'walk') {
          this.t -= dt; this.x = clamp(this.x + this.face * (this.phase === 2 ? 36 : 26) * dt, this.L, this.R);
          if (an.changed && (an.i === 1 || an.i === 5)) { shake = Math.max(shake, 3); sfx.step(); sfx.boom(); }
          if (this.t <= 0 || d < 80) { this.setA('idle', 'idle'); this.cool = Math.min(this.cool, 0.3); }
        } else if (d > 200 && this.cool > 0.4) { this.facePlayer(); this.setA('walk', 'walk'); this.t = 0.8; }
        if (this.cool <= 0) this.start(this.pick());
        break;
      }
      case 'goto': {
        this.gotoT -= dt;
        this.x = approach(this.x, this.gotoX, (this.phase === 2 ? 75 : 60) * dt);
        if (an.changed && (an.i === 1 || an.i === 5)) { shake = Math.max(shake, 3); sfx.boom(); }
        if (Math.abs(this.x - this.gotoX) < 4) { this.gotoX = null; this.setA('attack', 'grab', false); this.atkId = ++hazardId; this.fired = {}; }
        else if (this.gotoT <= 0) { this.gotoX = null; this.grabCool = 4; this.start(Math.abs(P.x - this.x) < 180 ? 'slam' : 'breath'); }
        break;
      }
      case 'attack': this.updateAttack(dt); break;
      case 'toppled': {
        this.t -= dt;
        if (an.changed && an.i === 3) {      // the crash
          shake = 15; hitstop = Math.max(hitstop, 0.12); sfx.boom(); sfx.crumble(); flashScreen = 0.2;
          const c = this.pt(this.fd().heart);
          spawnFx('shockwave', c.x, this.floor, 1); spawnFx(fxOr('dp_burst', 'hit'), c.x, c.y, 1);
          for (let i = 0; i < 40; i++) particles.push({ x: c.x + rand(-60, 60), y: this.floor - 2, vx: rand(-180, 180), vy: -rand(60, 240), g: 500, life: rand(0.5, 1.1), kind: i % 3 ? 'rock' : 'fire' });
        }
        if (an.done) an.hold();
        if (an.i >= 3 && Math.random() < 0.6) { const c = this.pt(this.fd().heart); particles.push({ x: c.x + rand(-10, 10), y: c.y + rand(-8, 8), vx: rand(-20, 20), vy: -rand(30, 80), life: 0.6, kind: 'fire' }); }
        if (this.t <= 0) { this.setA('rising', 'rise', false); this.fired = {}; }
        break;
      }
      case 'rising': {
        if (an.changed && an.i === 2) { const q = this.pt(this.fd().feet[0]); spawnFx('telegraph', q.x, q.y - 40, this.face); sfx.glint(); sfx.charge(); }
        if (an.i >= 4 && !this.fired.up) {  // heaves up and stamps: a ring of force around it
          this.fired.up = true; const c = this.x, fl = this.floor, p2 = this.phase === 2;
          shake = 12; sfx.boom(); spawnFx('shockwave', c, fl, 1); spawnFx(fxOr('dp_burst', 'hit'), c, fl - 20, 1);
          dpHaz({ x: c, y: fl, w: 170, h: 34, life: 0.18, dmg: BOSS_DMG * 36 * NGP.dmg, burn: 20, src: this });
          for (let k = 0; k < (p2 ? 3 : 1); k++) for (const dd of [-1, 1]) hazards.push({ x: c + dd * 60, y: fl, vx: dd * 170, delay: k * 0.45, w: 14, h: 14, dmg: BOSS_DMG * 28 * NGP.dmg, id: ++hazardId, life: 1.8, wave: true, dir: dd, color: 'root' });
        }
        if (an.done) { if (this.pendingPhase) this.enterPhase2(); else { this.setA('idle', 'idle'); this.cool = this.phase === 2 ? 0.6 : 0.9; } }
        break;
      }
      case 'shed':
        if (an.changed && an.i % 3 === 0 && an.i < 9) { shake = 8; sfx.crumble(); const c = this.pt([80 + rand(0, 60), 60 + rand(0, 80)]); for (let k = 0; k < 3; k++) spawnFx(fxOr('dp_debris', 'hit'), c.x + rand(-20, 20), c.y + rand(-20, 20), 1); for (let k = 0; k < 20; k++) particles.push({ x: c.x, y: c.y, vx: rand(-160, 160), vy: -rand(40, 200), g: 460, life: 1, kind: k % 2 ? 'rock' : 'fire' }); }
        if (an.done) { this.setA('idle', 'idle'); this.cool = 0.5; }
        break;
      case 'dead':
        if (an.i < an.n - 2 && Math.random() < 0.7) particles.push({ x: this.x + rand(-60, 60), y: this.y - rand(0, 120), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: Math.random() < 0.5 ? 'ember' : 'ash' });
        if (an.done) an.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp * 0.5 && this.alive && !this.pendingPhase) {
      if (['attack', 'goto', 'toppled', 'rising'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    this.x = clamp(this.x, this.L, this.R);
  }
  updateAttack(dt) {
    const an = this.anim, a = this.atk, tag = this.tag, f = this.fd(), p2 = this.phase === 2;
    const tel = this.meta.telegraph[tag];
    if (tel && an.changed && an.i === tel.frame) { const q = this.pt(tel.at); spawnFx('telegraph', q.x, q.y, this.face); sfx.glint(); if (tag === 'slam' || tag === 'breath') sfx.charge(); }
    const W = this.meta.attacks[tag];
    if (W && tag !== 'sweep' && an.i >= W.active[0] && an.i <= W.active[1] && !this.hitIds.has(0)) {
      if (overlap(this.mrect(W.hit), playerHurtbox()) && hurtPlayer(BOSS_DMG * COL_DMG[tag] * (p2 ? 1.1 : 1) * (a === 'kstomp' ? 0.8 : 1) * NGP.dmg, P.x < this.x ? -1 : 1, this.atkId, { src: this })) this.hitIds.add(0);
    }
    const once = (i, fn) => { if (an.i >= i && !this.fired[i]) { this.fired[i] = true; fn(); } };
    if (tag === 'slam') once(8, () => {
      const hb = this.mrect(f.hbox), cx = (hb.x0 + hb.x1) / 2;
      shake = 13; sfx.boom(); sfx.crumble(); flashScreen = 0.15;
      spawnFx('shockwave', cx, this.floor, 1); spawnFx(fxOr('dp_burst', 'hit'), cx, this.floor - 16, 1);
      for (const dd of [-1, 1]) hazards.push({ x: cx, y: this.floor, vx: dd * 175, w: 16, h: 16, dmg: BOSS_DMG * 34 * NGP.dmg, id: ++hazardId, life: 2.2, wave: true, dir: dd, color: 'root' });
      for (let i = 0; i < 30; i++) particles.push({ x: cx + rand(-30, 30), y: this.floor - 2, vx: rand(-160, 160), vy: -rand(60, 240), g: 500, life: rand(0.5, 1), kind: i % 2 ? 'rock' : 'fire' });
      if (p2) { const dir = sign(P.x - cx); for (let k = 1; k <= 4; k++) this.pillar(cx + dir * k * 48, 0.25 + k * 0.16); }
    });
    if (tag === 'fist') once(5, () => {
      const h = this.pt(f.hand);
      shake = 10; sfx.boom(); spawnFx('shockwave', h.x, this.floor, 1); spawnFx(fxOr('dp_burst', 'hit'), h.x, this.floor - 12, 1);
      for (let i = 0; i < 18; i++) particles.push({ x: h.x + rand(-20, 20), y: this.floor - 2, vx: rand(-120, 120), vy: -rand(60, 200), g: 480, life: 0.8, kind: 'rock' });
      if (a === 'pillars') for (const dd of [-1, 1]) for (let k = 1; k <= 9; k++) this.pillar(h.x + dd * (40 + k * 40), 0.35 + k * 0.13);   // two marching lines
      else if (p2) for (const dd of [-28, 28]) slagPuddle(h.x + dd, this.floor, 3.5, 30);
    });
    if (tag === 'stomp') once(6, () => {
      const ft = this.pt(f.feet[0]), rings = a === 'rings' ? 3 : 1;
      shake = 9; sfx.boom(); spawnFx('shockwave', ft.x, this.floor, 1);
      for (let k = 0; k < rings; k++) for (const dd of [-1, 1]) hazards.push({ x: ft.x, y: this.floor, vx: dd * (a === 'rings' ? 190 : 150), delay: k * 0.5, w: 14, h: 12, dmg: BOSS_DMG * 26 * NGP.dmg, id: ++hazardId,
        life: a === 'rings' ? 3 : p2 ? 1.3 : 0.7, wave: true, dir: dd, color: 'root', onStart() { spawnFx('shockwave', ft.x, this.y, 1); sfx.boom(); shake = Math.max(shake, 5); } });
    });
    if (tag === 'sweep' && an.i >= 4 && an.i <= 7) {
      const hb = this.mrect(f.hbox), r = rect(hb.x0 - 6, hb.y0 + 4, hb.x1 + 6, this.floor);
      if (an.changed && an.i === 4) { sfx.bossSwing(); sfx.fire(); }
      if (Math.random() < 0.9) particles.push({ x: rand(r.x0, r.x1), y: this.floor - rand(0, 10), vx: this.face * rand(40, 160), vy: -rand(40, 180), g: 420, life: 0.6, kind: 'fire' });
      addLight((r.x0 + r.x1) / 2, this.floor - 12, 70, '255,140,50', 1);
      if (!this.hitIds.has(1) && overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * COL_DMG.sweep * (p2 ? 1.1 : 1) * NGP.dmg, this.face, this.atkId + 1, { src: this, fire: true, burn: 30 })) this.hitIds.add(1);
      if (p2 && an.changed) slagPuddle((r.x0 + r.x1) / 2, this.floor, 3, 34);
    }
    this.breathing = null;
    if (tag === 'breath' && an.i >= 5 && an.i <= 12 && f) {
      const m = this.pt(f.mouth), ang = f.breath, dx = Math.cos(ang) * this.face, dy = Math.sin(ang), L = p2 ? 230 : 190;
      if (an.changed && an.i === 5) { sfx.fire(); sfx.roar(); this.brId = ++hazardId; this.brT = 0; }
      this.brT = (this.brT || 0) + dt;
      this.breathing = { x: m.x, y: m.y, ang, L };
      const hb = playerHurtbox();
      for (let s = 10; s <= L; s += 9) {
        const px = m.x + dx * s, py = m.y + dy * s, r = 6 + s * 0.1;
        if (solidAtPx(px, py)) { if (Math.random() < dt * (p2 ? 8 : 3)) slagPuddle(px, Math.floor(py / TILE) * TILE, 2.6, 28); for (let k = 0; k < 2; k++) particles.push({ x: px, y: py - 2, vx: rand(-80, 80), vy: -rand(30, 120), g: 300, life: 0.5, kind: 'fire' }); break; }
        if (overlap(rect(px - r, py - r, px + r, py + r), hb)) { hurtPlayer(BOSS_DMG * 20 * NGP.dmg, this.face, this.brId + '_' + Math.floor(this.brT / 0.2), { fire: true, burn: 30 }); break; }
        if (s % 36 === 0) addLight(px, py, 60, '255,150,60', 1);
      }
    }
    if (a === 'rain') once(5, () => {
      const n = p2 ? 16 : 6; shake = 10; sfx.roar(); flashScreen = 0.15;
      for (let k = 0; k < n; k++) {
        const x = clamp(k < 3 ? P.x + (k - 1) * 34 : p2 ? lerp(2 * TILE, room.pw - 2 * TILE, (k - 3 + Math.random()) / (n - 3)) : rand(this.L - 50, this.R + 50), 2 * TILE, room.pw - 2 * TILE);
        this.slagDrop(x, 0.15 + (k < 3 ? k : Math.random() * 6) * (p2 ? 0.22 : 0.24));
      }
    });
    if (a === 'erupt') once(4, () => this.erupt());
    if (a === 'flood') once(4, () => this.halfFlood());
    if (a === 'grab') this.updateGrab(an, f, p2);
    if (an.done) {
      this.breathing = null;
      if (this.pendingPhase) return this.enterPhase2();
      if (a === 'grab') this.grabCool = p2 ? 12 : 16;
      const d = Math.abs(P.x - this.x);
      const chain = { slam: d < 90 ? 'stomp' : 'sweep', fist: 'slam', sweep: d > 150 ? 'breath' : null, stomp: 'fist' }[a];
      if (p2 && chain && this.chain < 1 && Math.random() < 0.45) { this.chain++; return this.start(chain); }
      this.chain = 0; this.setA('idle', 'idle'); this.cool = p2 ? rand(0.7, 1.2) : rand(1.1, 1.8);
      if (['erupt', 'flood', 'pillars', 'rings'].includes(a)) this.cool += 0.5;
    }
  }
  // ---- phase-2 area attacks
  erupt() {   // the whole floor erupts except two safe gaps (one close enough to reach)
    const gapW = 72, near = clamp(P.x + (Math.random() < 0.5 ? -1 : 1) * rand(60, 130), 2 * TILE + 40, room.pw - 2 * TILE - 40);
    let far = rand(2 * TILE + 40, room.pw - 2 * TILE - 40); for (let k = 0; k < 8 && Math.abs(far - near) < 160; k++) far = rand(2 * TILE + 40, room.pw - 2 * TILE - 40);
    shake = 8; sfx.roar(); toast('The floor splits — find the dark ground!', 2); this.lastGaps = [near, far];
    for (let x = TILE + 18; x < room.pw - TILE - 10; x += 34) if (Math.abs(x - near) > gapW / 2 && Math.abs(x - far) > gapW / 2) this.pillar(x, 1.35, 30);
  }
  halfFlood() {   // lava wells up over the half of the arena the player stands on
    const mid = room.pw / 2, left = P.x < mid, x0 = left ? TILE : mid, x1 = left ? mid : room.pw - TILE, fl = this.floor, warn = 1.8;
    sfx.gate(); shake = 6;
    dpHaz({ kind: 'floodwarn', x: (x0 + x1) / 2, y: fl, w: 0, h: 0, life: warn, dmg: 0, active: () => false,
      draw(h) { const a = 0.4 + 0.4 * Math.sin(time * 14); for (let x = x0 + 8; x < x1; x += 24) { g.fillStyle = `rgba(255,${120 + (x % 3) * 30},40,${a})`; g.fillRect(Math.round(x), fl - 2, 12, 2); } for (let x = x0 + 20; x < x1; x += 64) addLight(x, fl - 4, 40, '255,120,40', 0.6); } });
    dpHaz({ kind: 'flood', x: (x0 + x1) / 2, y: fl, w: x1 - x0, h: 10, delay: warn, life: 3.2, dmg: BOSS_DMG * 22 * NGP.dmg, burn: 40, tick: 0.35,
      onStart() { sfx.fire(); sfx.boom(); shake = 7; },
      draw(h) { const k = Math.min(1, h.t * 3), a = Math.min(1, h.life * 1.2); g.globalAlpha = a; drawMagma(fl - 2 - 6 * k, x0, x1, fl + 2); g.globalAlpha = 1; for (let x = x0 + 30; x < x1; x += 60) addLight(x, fl - 6, 70, '255,120,40', 0.9 * a); } });
  }
  updateGrab(an, f, p2) {
    const cr = room.crucible; if (!cr) return;
    if (an.i >= 4 && an.i <= 13 && this.pourDir === undefined) { const h = this.pt(f.hand); this.pourDir = Math.abs(h.x - cr.x) < 60 ? sign(P.x - cr.hx) : 0; }
    if (an.i >= 6 && an.i <= 13 && this.pourDir) cr.hold = 0.9 * this.pourDir;
    if (an.i >= 4 && an.changed && an.i < 8) { sfx.gate(); shake = Math.max(shake, 3); }
    if (an.i >= 9 && an.i <= 13 && Math.abs(cr.ang) > 0.5) {
      const sp = cr.spout();
      cr.pouring = true;
      if (!this.flooded) {
        this.flooded = true; sfx.fire(); sfx.boom();
        const dir = this.pourDir || 1, x0 = sp.x, wallX = dir > 0 ? room.pw - TILE : TILE, life = p2 ? 4.2 : 3.4;
        dpHaz({ kind: 'flood', x: x0, y: this.floor, w: 0, h: 10, life, dmg: BOSS_DMG * 22 * NGP.dmg, burn: 40, tick: 0.35, dir,
          rect(h) { const e = x0 + dir * Math.min(Math.abs(wallX - x0), h.t * 300); return rect(Math.min(x0 - 20 * dir, e), h.y - 8, Math.max(x0 - 20 * dir, e), h.y); },
          draw(h) { const r = hazRect(h), a = Math.min(1, h.life * 1.2); g.globalAlpha = a; drawMagma(h.y - 6 - Math.min(1, h.t * 3) * 2, r.x0, r.x1, h.y + 2); g.globalAlpha = 1; for (let x = r.x0; x < r.x1; x += 40) addLight(x, h.y - 6, 60, '255,120,40', 0.9 * a); } });
      }
    } else cr.pouring = false;
    if (an.i >= 14) { cr.hold = undefined; cr.pouring = false; }
    if (an.done) { this.pourDir = undefined; this.flooded = false; cr.hold = undefined; cr.pouring = false; }
  }
  pillar(x, delay, w = 20) {
    dpHaz({ x, y: this.floor, w, h: 96, life: 1.2, delay, dmg: BOSS_DMG * 36 * NGP.dmg, burn: 40, kind: 'pillar',
      onStart(h) { h.fx = spawnFx(fxOr('dp_pillar', 'pillar'), h.x, h.y, 1, null, { bottom: true }); sfx.pillar(); },
      active(h) { return h.fx && h.fx.anim.i >= 3 && h.fx.anim.i <= 5; },
      update(h) { if (h.fx && h.fx.anim.i >= 2) addLight(h.x, h.y - 40, 70, '255,140,50', 1); if (h.fx && h.fx.anim.i === 3 && h.fx.anim.changed) shake = Math.max(shake, 3); } });
    dpHaz({ x, y: this.floor, w: 0, h: 0, life: delay + 0.05, dmg: 0, active: () => false, draw(h) {
      const s = fxSheet('dp_marker'), k = Math.min(1, h.t / Math.max(0.2, delay)); if (s.ok) drawSprite(s, s.tag(Object.keys(s.tags)[0]).from + Math.floor(time * 10) % 4, h.x, h.y, 1, { bottom: true });
      for (let i = 0; i < 3; i++) { const yy = h.y - 4 - ((time * 40 + i * 9 + h.x) % 26) * k; g.fillStyle = `rgba(255,${150 + i * 30},60,${0.35 + 0.5 * k})`; g.fillRect(Math.round(h.x - 1 + (i - 1) * 4), Math.round(yy), 2, 2); }
      addLight(h.x, h.y - 3, 18 + 16 * k, '255,120,40', 0.5 + 0.4 * k); } });
  }
  slagDrop(x, delay) {
    const B = this, top = 2 * TILE + 4, fl = this.floor;
    dpHaz({ x, y: fl, w: 22, h: 30, life: 1.6 + delay, t: 0, kind: 'drop', dmg: BOSS_DMG * 32 * NGP.dmg, burn: 32,
      active(h) { return h.t > 0.85 + delay && h.t < 1.0 + delay; },
      update(h) {
        if (h.t > 0.85 + delay && !h.hitGround) { h.hitGround = true; sfx.fire(); spawnFx(fxOr('dp_splash', 'hit'), h.x, fl, 1, null, { bottom: true }); for (let i = 0; i < 8; i++) particles.push({ x: h.x, y: fl - 2, vx: rand(-90, 90), vy: -rand(40, 150), g: 420, life: 0.6, kind: 'fire' }); slagPuddle(h.x, fl, B.phase === 2 ? 3 : 1.8, 24); }
      },
      draw(h) {
        const mk = fxSheet('dp_marker'), dr = fxSheet('dp_drip'), tt = h.t - delay;
        if (tt < 0) return;
        if (tt < 0.9 && mk.ok) drawSprite(mk, mk.tag(Object.keys(mk.tags)[0]).from + Math.floor(time * 12) % 4, h.x, fl, 1, { bottom: true });
        if (tt < 0.9) { addLight(h.x, fl - 2, 22 + tt * 20, '255,120,40', 0.7); g.fillStyle = 'rgba(255,160,60,0.8)'; g.fillRect(Math.round(h.x) - 1, top, 3, 2 + Math.floor(tt * 4)); }
        if (tt > 0.45 && tt < 0.85) { const k = (tt - 0.45) / 0.4, y = lerp(top, fl, k * k); if (dr.ok) drawSprite(dr, dr.tag(Object.keys(dr.tags)[0]).from + Math.floor(time * 12) % 2, h.x, y, 1, { center: true }); else { g.fillStyle = '#ffb040'; g.fillRect(Math.round(h.x) - 2, Math.round(y) - 6, 4, 8); } addLight(h.x, y, 30, '255,150,60', 0.9); }
      } });
  }
  enterPhase2() {
    this.pendingPhase = false; this.phase = 2; this.speed = 1.18; this.chain = 0; this.aoeRun = 0;
    for (const n of Object.keys(this.plates)) this.breakPlate(n);
    this.facePlayer(); this.setA('shed', 'shed', false); this.breathing = null;
    if (room.crucible) { room.crucible.hold = undefined; room.crucible.pouring = false; }
    flashScreen = 0.6; shake = 12; sfx.roar();
    toast('Its shell sloughs away — the heartwood fire beneath is bare', 3.2);
    bossPhase2Scene(this);
  }
  die() {
    this.state = 'dead'; this.breathing = null; this.phase = 2; this.setA('dead', 'death', false);
    hazards = []; DP.haz = []; DP.shots = []; projectiles = projectiles.filter(p => p.owner === 'player');
    if (room.crucible) { room.crucible.hold = undefined; room.crucible.pouring = false; }
    shake = 14; hitstop = 0.35; slowmo = 1.8; flashScreen = 0.7; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE FORGE-GOD IS UNMADE', t: 0 };
    this.rewards();
  }
  ambient(dt) {
    const p2 = this.phase === 2;
    if (this.alive) addLight(this.x + this.face * 30, this.y - 90, p2 ? 180 : 160, '255,130,50', p2 ? 1 : 0.9);
    const f = this.fd();
    if (f && this.alive) {
      const h = this.pt(f.heart), ex = this.exposed;
      addLight(h.x, h.y, ex ? 90 + Math.sin(time * 8) * 8 : p2 ? 70 : 40, '255,190,90', 1);
      if (Math.random() < (p2 ? 0.8 : 0.35)) particles.push({ x: this.x + rand(-60, 60), y: this.y - rand(20, 150), vx: rand(-6, 6), vy: -rand(20, 50), life: rand(0.6, 1.4), kind: Math.random() < 0.6 ? 'ember' : 'fire' });
      if (this.topple > 30 && !ex) for (const n of ['knee_n', 'knee_f']) { const r = this.partRect(n); if (r) addLight((r.x0 + r.x1) / 2, r.y0 + 10, 26 + this.topple * 0.3, '255,140,50', this.topple / (this.toppleMax() * 1.1)); }
    }
  }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.6 } : {};
    if (!this.sh.ok) { g.fillStyle = '#2a1a18'; g.fillRect(Math.round(this.x - 60), Math.round(this.y - 160), 120, 160); return; }
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    const f = this.fd();
    // intact armour plates (clipped per part); the breastplate is torn away while it lies toppled (the core shows)
    const pl = sheet(this.sh.name + '_pl', { meta: this.meta });
    if (pl.ok && this.phase === 1 && this.alive && f) for (const n of Object.keys(this.plates)) {
      if (!this.plates[n] || (n === 'chest' && (this.exposed || this.state === 'toppled'))) continue;
      const r = this.mrect(f.parts[n]);
      g.save(); g.beginPath(); g.rect(Math.floor(r.x0) - 2, Math.floor(r.y0) - 2, r.x1 - r.x0 + 4, r.y1 - r.y0 + 4); g.clip();
      drawSprite(pl, this.anim.frame, this.x, this.y, this.face, this.flash > 0 ? { flash: this.flash * 0.5 } : {});
      g.restore();
    }
    // topple meter drawn on the legs: glowing cracks that spread as the legs are battered
    if (f && this.alive && this.topple > 0 && !this.exposed) for (const n of ['knee_n', 'knee_f']) {
      const r = this.mrect(f.parts[n]), k = this.topple / this.toppleMax(), cx = (r.x0 + r.x1) / 2, cy = (r.y0 + r.y1) / 2;
      const segs = Math.ceil(k * 9);
      for (let s = 0; s < segs; s++) {
        const a = hash2(s, n.length) * 6.28, L = 4 + hash2(s, 7) * 10 * k, x0 = cx + (hash2(s, 3) - 0.5) * 10, y0 = cy + (hash2(s, 5) - 0.5) * 14;
        for (let t = 0; t < L; t++) { g.fillStyle = t < 2 ? '#ffe9a0' : k > 0.7 ? '#ffb040' : '#f06a18'; g.fillRect(Math.round(x0 + Math.cos(a) * t), Math.round(y0 + Math.sin(a) * t), 1, 1); }
      }
    }
    // the bared core pulses white-hot
    if (this.exposed && f) {
      const c = this.pt(f.heart), s = 10 + Math.sin(time * 10) * 2;
      g.save(); g.globalCompositeOperation = 'lighter';
      const gr = g.createRadialGradient(c.x, c.y, 0, c.x, c.y, s * 2.2);
      gr.addColorStop(0, 'rgba(255,240,190,0.9)'); gr.addColorStop(0.4, 'rgba(255,150,60,0.5)'); gr.addColorStop(1, 'rgba(255,90,30,0)');
      g.fillStyle = gr; g.fillRect(c.x - s * 2.2, c.y - s * 2.2, s * 4.4, s * 4.4); g.restore();
    }
    const b = this.breathing;
    if (b) {
      const s = fxSheet('dp_breath');
      if (s.ok) { const t = s.tag(Object.keys(s.tags)[0]), n = t.to - t.from + 1; drawSprite(s, t.from + Math.floor(time * 14) % n, b.x, b.y, this.face, { pivot: [0, Math.floor(s.fh / 2)], rot: b.ang }); if (b.L > 180) drawSprite(s, t.from + (Math.floor(time * 14) + 2) % n, b.x + Math.cos(b.ang) * this.face * 70, b.y + Math.sin(b.ang) * 70, this.face, { pivot: [0, Math.floor(s.fh / 2)], rot: b.ang, alpha: 0.8 }); }
    }
  }
}
HOOKS.hud.push(() => {   // the topple meter / core window under the Colossus's health bar
  if (!boss || boss.kind !== 'colossus' || !boss.active || !boss.alive) return;
  if (boss.exposed) { const k = boss.state === 'toppled' ? clamp(boss.t / (boss.phase === 2 ? 4.4 : 5.4), 0, 1) : 0; bar(156, 208, 90, 1.5, k, 0, '#ffe08a'); text('CORE EXPOSED', 250, 210, 4.8, '#ffe08a', 'left', { weight: 700 }); return; }
  bar(156, 208, 90, 1.5, boss.topple / boss.toppleMax(), 0, boss.topple > boss.toppleMax() * 0.7 ? '#ffb040' : '#c0561c');
  text('topple — strike its legs', 250, 210, 4.5, '#d8a060', 'left', { weight: 500 });
});
BOSS_SPAWN.colossus = (cx, fy) => new Colossus(cx, fy);
try { window.__dpDbg = { get hazards() { return hazards; }, get haz() { return DP.haz; }, get hurts() { return DP.hurts || 0; } }; } catch (e) {}   // headless test access
// crucible spout (world) for the pour, and the molten stream while pouring
const _crSpawn = SPAWNS.dp_crucible;
SPAWNS.dp_crucible = (s, c) => {
  _crSpawn(s, c);
  const cr = room.crucible; cr.py = (s.y + 2) * TILE + 8;
  cr.spout = function () { const sgn = this.ang >= 0 ? 1 : -1, lx = 46 * sgn, ly = 9 - 10; return { x: this.x + Math.cos(this.ang) * lx - Math.sin(this.ang) * ly, y: this.py + Math.sin(this.ang) * lx + Math.cos(this.ang) * ly }; };
};
function drawCrucible(cr) {
  const sh = sheet('dp_crucible'), py = cr.py || cr.y;
  const lug = s => ({ x: cr.x + Math.cos(cr.ang) * s * 30, y: py + Math.sin(cr.ang) * s * 30 });
  for (const s of [-1, 1]) {
    const a = lug(s), top = { x: cr.hx + s * 34, y: 2 * TILE };
    const n = Math.ceil(Math.hypot(a.x - top.x, a.y - top.y) / 4);
    for (let i = 0; i <= n; i++) { const x = lerp(top.x, a.x, i / n), y = lerp(top.y, a.y, i / n); g.fillStyle = i % 2 ? '#2a201e' : '#5a4840'; g.fillRect(Math.round(x) - (i % 2 ? 0 : 1), Math.round(y), i % 2 ? 1 : 3, 3); }
  }
  if (sh.ok) { const t = sh.tag('idle'); drawSprite(sh, t.from + Math.floor(time * 6) % (t.to - t.from + 1), cr.x, py, 1, { rot: cr.ang, pivot: [48, 10] }); }
  if (cr.pouring && cr.spout) {
    const sp = cr.spout(), ps = fxSheet('dp_pour'), floor = room.ph - 3 * TILE;
    if (ps.ok) { const t = ps.tag(Object.keys(ps.tags)[0]); for (let y = sp.y; y < floor; y += ps.fh - 2) drawSprite(ps, t.from + Math.floor(time * 12) % 4, sp.x, y, 1, { pivot: [16, 0] }); }
    else { g.fillStyle = '#ffb040'; g.fillRect(Math.round(sp.x) - 4, Math.round(sp.y), 8, floor - sp.y); }
    for (let y = sp.y; y < floor; y += 30) addLight(sp.x, y, 50, '255,140,50', 1);
  }
}

// ---- cutscenes: Ashwright's voice-over as the forge-god wakes
Object.assign(BOSS_CUTS, {
  colossus: b => [
    act(() => { b.setA('dormant', 'stagger', false); b.anim.i = b.anim.n - 1; b.anim.done = true; b.face = 1; }),
    bossPan(b, 90, 1.6),
    say('Old Ashwright', 'So. You found my forge… and the thing I left sleeping in it.'),
    say('Old Ashwright', 'I smelted the Root’s heartwood into a body that would never tire.'),
    say('Old Ashwright', 'A god to work the anvil when my arm gave out.'),
    act(() => { shake = 6; sfx.boom(); dustFall(30); for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-60, 60), y: b.y - rand(20, 150), vx: 0, vy: -rand(20, 70), life: rand(0.6, 1.4), kind: 'ember' }); }), wait(0.5),
    say('Old Ashwright', 'It worked, all right. Worked the whole Hallow into slag.'),
    say('Old Ashwright', 'Put it out, Ashbound. Hah — put out my finest fire.'),
    act(() => { b.setA('idle', 'idle'); b.facePlayer(); sfx.roar(); shake = 12; flashScreen = 0.4; spawnFx('roar_ring', b.x + b.face * 30, b.y - 110, 1); }), wait(1.0),
  ],
});
PHASE2_LINES.colossus = ['Old Ashwright', 'The shell’s off — that’s raw heartwood burning. Strike fast.'];

// ---- the way down from the Sunken Road: embers and a warm glow rise out of the shaft so it reads as an entrance
HOOKS.update.push(() => {
  if (!room || room.id !== 'M4') return;
  const x0 = 41 * TILE, x1 = 44 * TILE, y = 14 * TILE;
  if (Math.random() < 0.5) particles.push({ x: rand(x0 + 2, x1 - 2), y: y - rand(0, 10), vx: rand(-6, 6), vy: -rand(25, 70), life: rand(0.8, 1.6), kind: Math.random() < 0.6 ? 'fire' : 'spark' });
  addLight((x0 + x1) / 2, y - 12, 70, '255,130,50', 0.9);
});
