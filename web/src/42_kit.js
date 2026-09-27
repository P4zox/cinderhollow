// ------------------------------------------------------------------ EXPANSION 3 KIT — MECHANICS (agent KM)
// Reusable moving parts, hazards and puzzle parts for every region. Rooms place them as spawns:
//   spawns=[{t:'kit', kind:'mover', x, y, ...}]      (full reference: docs/KIT_API.md, section "Mechanics")
// Moving parts: mover lift crumble sinker phase swing pendulum rising wind spring crate
// Puzzle parts: lever switch plate gate seq (+ members bell lantern glyph stop frame brazier) beam mirror socket level
// Wiring: string ids local to the room. A *source* (lever, switch, plate, seq, socket, member, brazier) is `active` or not and
// lists `targets`; a *consumer* (gate, mover, lift, level, beam, rising, wind…) derives its state every frame from the sources
// that target it (logic 'toggle' = parity, 'any', 'all', or a count for `level`), XOR its start state, or from `trigger`.
// Riding: slabs live in room.dyn (moveBody lands on a dyn's own top — see dynTopAt in 03_world.js) and are moved AFTER the
// player's physics each frame, carrying riders by the exact same delta, so a rider's feet never leave the surface.
// Trials (KS) call kitReset(roomId) to put movers/crumbles/sinkers/rising floors/ropes/crates back to their start state.
const KIT = { roomObj: null, objs: [], byId: {}, t: 0, cnt: {}, tot: {}, force: {}, safe: null, carry: null, rideO: null, onChange: [], fl: [], hid: 0 };
const KIT_SKINS = ['stone', 'bone', 'wood', 'iron', 'crystal', 'neon'];
const KIT_SKIN_OF = { ramparts: 'stone', catacombs: 'bone', cathedral: 'stone', mire: 'wood', crown: 'bone', archives: 'wood', hoarfrost: 'crystal',
  spire: 'iron', deep: 'iron', ember: 'iron', hermit: 'wood', thornveil: 'wood', barrows: 'stone', crimson: 'wood', necropolis: 'bone', nv_void: 'bone',
  dunes: 'bone', starfall: 'crystal', sov_void: 'crystal', neohallow: 'neon', neohallow_cyber: 'neon' };
// per-skin colours for everything drawn live (ropes, chains, beams, fallbacks). glow = light colour of lit parts.
const KIT_PAL = {
  stone: { k: '#0c0a10', d: '#2e2b35', m: '#4f4b58', l: '#7a7584', h: '#a8a2b0', acc: '#d8a850', glow: '255,196,120', rope: 'rope' },
  bone: { k: '#100c0a', d: '#4a4234', m: '#8a7e66', l: '#bfb394', h: '#e6dcc0', acc: '#8ec0f0', glow: '150,200,255', rope: 'chain' },
  wood: { k: '#0c0806', d: '#3a2618', m: '#5e4028', l: '#8a6440', h: '#b08a5a', acc: '#9ad070', glow: '255,190,110', rope: 'vine' },
  iron: { k: '#08080a', d: '#26262c', m: '#44444e', l: '#6c6c78', h: '#9a9aa8', acc: '#ff8a3a', glow: '255,140,60', rope: 'chain' },
  crystal: { k: '#060812', d: '#1e2a48', m: '#34508a', l: '#5a88c8', h: '#a8d8ff', acc: '#c8a8ff', glow: '160,200,255', rope: 'chain' },
  neon: { k: '#05050d', d: '#141424', m: '#26263e', l: '#3c3c5c', h: '#6a6a90', acc: '#30f0ff', glow: '60,240,255', rope: 'cable' },
};
const KIT_FLUID = {   // rising floors + levels: body colour, surface colour, light, damage (fraction of max HP), tile it writes
  lava: { body: '#7a1606', top: '#ffb040', mid: '#e0501a', light: '255,120,40', dmg: 0.3, alpha: 0.96, fire: true },
  slag: { body: '#3a1a10', top: '#ff9a3a', mid: '#a8401a', light: '255,130,50', dmg: 0.3, alpha: 0.96, fire: true },
  poison: { body: '#27421a', top: '#a8d060', mid: '#4f7a2a', light: '150,210,90', dmg: 0.2, alpha: 0.78, rot: true },
  water: { body: '#08222a', top: '#8ad8e0', mid: '#1c5058', light: '110,200,220', dmg: 0.15, alpha: 0.62 },
  sand: { body: '#6a4a24', top: '#e0b870', mid: '#a67a3e', light: '255,200,120', dmg: 0.2, alpha: 0.98 },
  data: { body: '#0a0a24', top: '#30f0ff', mid: '#6a30d0', light: '60,240,255', dmg: 0.25, alpha: 0.85 },
};
const KIT_KINDS = {};
const kitNoop = () => {};
const kitTrig = o => { const t = o.spec.trigger; return !!t && t !== 'stand' && t !== 'enter' && t !== 'zone'; };   // pulls from a source id
const kitSfx = {
  clunk: () => { noise(0.12, 300, 0.8, 0.3, 'lowpass'); tone(110, 0.12, 0.12, 'square', 0.6); },
  click: () => { tone(1400, 0.04, 0.06, 'square', 0.5); noise(0.05, 2500, 1, 0.1, 'highpass'); },
  tick: (hi) => tone(hi ? 1760 : 1320, 0.035, 0.05, 'square', 0.9),
  chime: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 1.1, 0.07, 'triangle', 1, i * 0.09)),
  wrong: () => { tone(185, 0.5, 0.09, 'sawtooth', 0.8); tone(196, 0.5, 0.09, 'sawtooth', 0.8); noise(0.2, 400, 0.8, 0.15, 'lowpass'); },
  note: (n, kind) => { const f = 220 * Math.pow(2, [0, 2, 3, 5, 7, 8, 10, 12, 14, 15][((n % 10) + 10) % 10] / 12); if (kind === 'bell') { tone(f, 2.2, 0.1, 'sine'); tone(f * 2.76, 1.2, 0.03, 'sine'); tone(f / 2, 2.4, 0.06, 'triangle'); } else if (kind === 'stop') { tone(f, 1.2, 0.06, 'sawtooth', 1); tone(f * 1.5, 1.1, 0.03, 'triangle'); } else { tone(f * 2, 0.7, 0.06, 'triangle'); tone(f * 3, 0.5, 0.025, 'sine'); } },
  blip: (on) => tone(on ? 880 : 520, 0.06, 0.035, 'triangle', on ? 1.3 : 0.7),
  boing: () => { tone(180, 0.25, 0.14, 'triangle', 2.6); noise(0.08, 900, 1, 0.1, 'bandpass'); },
  whoosh: (v = 1) => noise(0.28, 700, 0.9, 0.16 * v, 'bandpass', 2.2),
  creak: () => tone(rand(90, 130), 0.3, 0.035, 'sawtooth', 1.3),
  hum: () => { tone(330, 0.5, 0.05, 'sine', 1.02); tone(495, 0.45, 0.03, 'sine'); },
  turn: () => { noise(0.1, 1200, 1, 0.14, 'bandpass'); tone(700, 0.06, 0.05, 'square', 0.8); },
  lift: () => { noise(0.35, 200, 0.7, 0.18, 'lowpass'); tone(70, 0.3, 0.08, 'square', 1.2); },
};
const kitSkin = s => { const k = s.skin; if (k && KIT_PAL[k]) return k; if (k && KIT_SKIN_OF[k]) return KIT_SKIN_OF[k]; return KIT_SKIN_OF[room.def.biome] || 'stone'; };
const kitKey = id => `x3:${room.id}:${id}`;
function kitStore() { SAVE.x3 = SAVE.x3 || {}; SAVE.x3.kit = SAVE.x3.kit || {}; return SAVE.x3.kit; }
const kitNear = (x, y, r = 260) => Math.abs(x - P.x) < r && Math.abs(y - P.y) < r * 0.7;   // sounds only when it matters to the player
function kitEnsure() {
  if (KIT.roomObj === room) return;
  Object.assign(KIT, { roomObj: room, objs: [], byId: {}, t: 0, cnt: {}, tot: {}, force: {}, safe: null, carry: null, rideO: null, fl: [] });
}

// ================================================================== wiring
// source.active: true/false. consumer.on: derived. ids are local to the room.
function kitObj(kind, s) {
  const o = { type: 'kit_' + kind, kind, spec: s, id: s.id || null, face: 1, anim: { update() {} }, skin: kitSkin(s), targets: s.targets || [] };
  o.pal = KIT_PAL[o.skin];
  KIT.objs.push(o); if (o.id) { if (KIT.byId[o.id]) console.warn(`kit: duplicate id ${o.id} in ${room.id}`); KIT.byId[o.id] = o; }
  return o;
}
function kitTally() {   // how many sources target each id, and how many of them are active (one-frame snapshot)
  const cnt = {}, tot = {};
  for (const o of KIT.objs) if (o.src) for (const t of o.targets) { tot[t] = (tot[t] || 0) + 1; if (o.active) cnt[t] = (cnt[t] || 0) + 1; }
  KIT.cnt = cnt; KIT.tot = tot;
}
function kitSrc(id) { const o = KIT.byId[id]; return !!(o && (o.src ? o.active : o.on)); }
// consumer state: start ^ (sources by logic) ^ trigger; kitForce(id, bool) overrides (KS gauntlets close gates with it)
function kitDerive(o, start) {
  if (o.id && KIT.force[o.id] !== undefined) return KIT.force[o.id];
  const n = o.id ? KIT.cnt[o.id] || 0 : 0, tot = o.id ? KIT.tot[o.id] || 0 : 0, lg = o.spec.logic || 'toggle';
  let v = lg === 'all' ? (tot > 0 && n === tot) : lg === 'any' ? n > 0 : (n & 1) === 1;
  if (o.spec.trigger && o.spec.trigger !== 'stand' && o.spec.trigger !== 'enter' && o.spec.trigger !== 'zone') v = v !== kitSrc(o.spec.trigger);
  return start ? !v : v;
}
function kitSetActive(o, v, quiet) {
  if (o.active === v) return;
  o.active = v;
  if (o.persistKey && !o.spec.timer && !quiet) { SAVE.flags[o.persistKey] = v ? 1 : 0; saveGame(); }
  kitTally();   // the change lands this frame, not next
  for (const f of KIT.onChange) f(o.id, v, o);
  if (!quiet) for (const t of o.targets) { const q = KIT.byId[t]; if (q && q.ping) q.ping(v); }
}
function kitChanged(o, v) { for (const f of KIT.onChange) f(o.id, v, o); }
// public helpers (KS / region code)
function kitForce(id, v) { if (v === null || v === undefined) delete KIT.force[id]; else KIT.force[id] = !!v; }
function kitOn(id) { const o = KIT.byId[id]; return !!(o && (o.src ? o.active : o.on)); }
function kitReset(roomId, opt = {}) {
  if (!room || (roomId && roomId !== room.id)) return;
  KIT.t = 0; KIT.carry = null;
  for (const o of KIT.objs) if (o.reset && (!o.puzzle || opt.all)) o.reset(!!opt.all);
  kitTally();
}

// ================================================================== bodies + slabs (everything you stand on)
function kitBodies() {
  const L = [P];
  for (const e of enemies) if (e.alive && !e.cfg.flying) L.push(e);
  for (const o of KIT.objs) if (o.kind === 'crate' && o.body) L.push(o.body);
  return L;
}
const kitHB = b => rect(b.x - b.w / 2, b.y - b.h, b.x + b.w / 2, b.y);
// is b standing on slab d right now? (feet on its top, overlapping it)
const kitStands = (b, d) => b.ground && Math.abs(b.y - d.y0) < 1.5 && b.x + b.w / 2 - 1 > d.x0 && b.x - b.w / 2 + 1 < d.x1;
function kitFree(b, x, y, skip) {   // would body b fit at (x, y)? (ignores `skip`'s own slab)
  if (skip) skip.off = true;
  const hw = b.w / 2 - 0.5; let ok = true;
  for (const yy of [y - b.h + 0.5, y - b.h * 0.66, y - b.h * 0.33, y - 0.5]) {
    for (const xx of [x - hw, x, x + hw]) if (solidAtPx(xx, yy)) { ok = false; break; }
    if (!ok) break;
  }
  if (skip) skip.off = false;
  return ok;
}
// o gets a slab: x,y = left tile + row (surface = top of row y, like '='), w tiles wide, 8 px thick. one-way unless solid:true
function kitSlab(o, s, defW) {
  o.w = (s.w ?? defW) * TILE; o.th = 8; o.oneway = !s.solid; o.solidNow = true; o.off = false; o.alpha = 1;
  const x0 = s.x * TILE, y0 = s.y * TILE;
  o.d = { x0, x1: x0 + o.w, y0, y1: y0 + o.th, kit: o, oneway: o.oneway,
          on: () => o.solidNow && !o.off && (!o.oneway || (P.drop <= 0 && P.y <= o.d.y0 + 0.5)) };
  o.x = x0 + o.w / 2; o.y = y0;
  room.dyn.push(o.d);
}
// move a slab to (nx, ny) px, carrying riders by the same delta. Returns false (and doesn't move) when it would crush the
// player: a rising slab waits under a low ceiling, a solid slab waits rather than push you into a wall.
function kitSlabMove(o, nx, ny, dt) {
  const d = o.d, dx = nx - d.x0, dy = ny - d.y0;
  if (Math.abs(dx) < 1e-6 && Math.abs(dy) < 1e-6) { if (o === KIT.rideO) KIT.rideV = 0; return true; }
  const bodies = kitBodies();
  const riders = o.solidNow && !o.off ? bodies.filter(b => kitStands(b, d) && (b !== P || P.drop <= 0)) : [];
  for (const b of riders) if (b === P && dy && !kitFree(b, b.x, ny, o)) return false;   // up into a ceiling / down into a floor: it waits
  const push = [];
  if (!o.oneway && o.solidNow) {
    const r = rect(nx, ny, nx + o.w, ny + o.th);
    for (const b of bodies) {
      if (riders.includes(b)) continue;
      const hb = kitHB(b); if (!overlap(hb, r)) continue;
      let px = b.x, py = b.y;
      if (hb.y1 <= d.y0 + 2) py = ny;                      // was above: lift it onto the top
      else if (hb.y0 >= d.y1 - 2) py = ny + o.th + b.h;    // was below: shove it down
      else px = b.x < nx + o.w / 2 ? nx - b.w / 2 - 0.01 : nx + o.w + b.w / 2 + 0.01;
      if (!kitFree(b, px, py, o)) { if (b === P) return false; continue; }
      push.push([b, px, py]);
    }
  }
  const oy0 = d.y0;
  d.x0 = nx; d.x1 = nx + o.w; d.y0 = ny; d.y1 = ny + o.th; o.x = nx + o.w / 2; o.y = ny;
  for (const b of riders) { b.y = ny; if (dx && kitFree(b, b.x + dx, ny, o)) b.x += dx; }
  for (const [b, px, py] of push) { if (py > b.y) b.vy = Math.max(b.vy, 0); b.x = px; b.y = py; }
  // scoop: a falling body whose feet the rising top just swept past lands on it next frame instead of passing through
  if (dy < 0 && o.solidNow) for (const b of bodies) {
    if (riders.includes(b) || b.vy < 0 || (b === P && P.drop > 0)) continue;
    if (b.y > ny && b.y <= oy0 + 0.5 && b.x + b.w / 2 - 1 > d.x0 && b.x - b.w / 2 + 1 < d.x1) b.y = ny;
  }
  if (riders.includes(P)) { KIT.rideO = o; KIT.rideV = dx / Math.max(dt, 1e-3); }
  return true;
}
function kitSlabOverlapped(o) {   // anyone inside the slab's box? (phases/crumbles don't re-solidify into a body)
  const r = rect(o.d.x0, o.d.y0 - 1, o.d.x1, o.d.y1);
  return kitBodies().some(b => overlap(kitHB(b), r) && !(Math.abs(b.y - o.d.y0) < 0.6));
}
function kitStoodBy(o, who = 'player') {   // player (or player+crates) standing on this slab
  if (!o.solidNow || o.off) return false;
  if (kitStands(P, o.d) && P.drop <= 0) return true;
  if (who === 'any') for (const q of KIT.objs) if (q.kind === 'crate' && q.body && kitStands(q.body, o.d)) return true;
  return false;
}
function kitDrawSlab(o, x0, y0, alpha = 1, crack = 0, jx = 0, jy = 0) {
  const sh = sheet('kit_plat'), n = Math.max(1, Math.round(o.w / TILE)), X = Math.round(x0 + jx), Y = Math.round(y0 + jy);
  if (sh.ok && sh.has(o.skin)) {
    const t = sh.tag(o.skin); g.save(); g.globalAlpha = alpha;
    for (let i = 0; i < n; i++) {
      const f = sh.frames[t.from + (n === 1 ? 3 : i === 0 ? 0 : i === n - 1 ? 2 : 1)];
      g.drawImage(sh.img, f.x, f.y, f.w, f.h, X + i * TILE, Y, f.w, f.h);
      if (crack && sh.has('crack')) { const c = sh.frames[sh.tag('crack').from + Math.min(crack, 2) - 1]; g.drawImage(sh.img, c.x, c.y, c.w, c.h, X + i * TILE, Y, c.w, c.h); }
    }
    g.restore(); return;
  }
  const p = o.pal; g.save(); g.globalAlpha = alpha;
  g.fillStyle = p.k; g.fillRect(X, Y, o.w, 9); g.fillStyle = p.m; g.fillRect(X + 1, Y + 1, o.w - 2, 6); g.fillStyle = p.h; g.fillRect(X + 1, Y + 1, o.w - 2, 1);
  g.fillStyle = p.d; for (let x = X + 3; x < X + o.w - 2; x += 8) g.fillRect(x, Y + 4, 1, 3);
  g.restore();
}

// ================================================================== MOVING PARTS
// ---- mover: a platform on waypoints. path [[x,y],…] (tile coords of its left end), speed tiles/s, loop|pingpong, wait s
function kitMoverInit(o, s, def) {
  kitSlab(o, s, def.w);
  const pts = (s.path && s.path.length ? s.path : [[s.x, s.y]]).map(([x, y]) => ({ x: x * TILE, y: y * TILE }));
  Object.assign(o, { pts, loop: !!s.loop, speed: (s.speed ?? def.speed) * TILE, wait: s.wait ?? def.wait, trig: s.trigger ?? def.trigger ?? null, ret: s.return ?? def.ret ?? 0 });
  o.stops = i => o.wait > 0 || (!o.loop && (i === 0 || i === o.pts.length - 1));
  o.reset = () => {
    Object.assign(o, { i: 0, dir: 1, u: 0, v: 0, waitT: s.delay ?? 0, idle: o.trig === 'stand', retT: 0, blockT: 0 });
    if (s.offset && o.pts.length > 1) {   // stagger identical movers: start a fraction of the way along the path
      const segs = o.loop ? o.pts.length : o.pts.length - 1; let dist = 0; const L = [];
      for (let i = 0; i < segs; i++) { const a = o.pts[i], b = o.pts[(i + 1) % o.pts.length]; L.push(Math.hypot(b.x - a.x, b.y - a.y)); dist += L[i]; }
      let r = (s.offset % 1) * dist; for (let i = 0; i < segs; i++) { if (r < L[i]) { o.i = i; o.u = r; break; } r -= L[i]; }
      o.v = o.speed;
    }
    const p = kitMoverPos(o), px = Math.round(p.x), py = Math.round(p.y); o.d.x0 = px; o.d.x1 = px + o.w; o.d.y0 = py; o.d.y1 = py + o.th; o.x = px + o.w / 2; o.y = py;
  };
  o.reset();
}
function kitMoverNext(o) { const n = o.pts.length; if (o.loop) return (o.i + 1) % n; let j = o.i + o.dir; if (j < 0 || j >= n) { o.dir = -o.dir; j = o.i + o.dir; } return j; }
function kitMoverPos(o) {
  if (o.pts.length < 2) return o.pts[0];
  const save = o.dir, j = kitMoverNext(o); o.dir = save;
  const a = o.pts[o.i], b = o.pts[j], L = Math.hypot(b.x - a.x, b.y - a.y) || 1, k = clamp(o.u / L, 0, 1);
  return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
}
function kitMoverUpdate(o, dt, running) {
  if (o.pts.length < 2) return;
  if (o.waitT > 0) { o.waitT -= dt; return; }
  const dir0 = o.dir, j = kitMoverNext(o), a = o.pts[o.i], b = o.pts[j], L = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  const acc = Math.max(40, o.speed * 3), stop = o.stops(j);
  let tv = running ? o.speed : 0;
  if (stop) tv = Math.min(tv, Math.sqrt(2 * acc * Math.max(0, L - o.u)) + 6);   // ease into stops
  o.v = approach(o.v, tv, acc * dt);
  if (o.v <= 0) { o.dir = dir0; return; }
  let u = o.u + o.v * dt, i = o.i, arrived = false;
  if (u >= L) { arrived = true; u = stop ? L : u - L; }
  const k = clamp(u / L, 0, 1), nx = a.x + (b.x - a.x) * k, ny = a.y + (b.y - a.y) * k;
  o.dir = dir0;
  if (!kitSlabMove(o, Math.round(nx), Math.round(ny), dt)) { o.v = 0; o.blockT += dt; return; }
  o.blockT = 0;
  if (arrived) {
    kitMoverNext(o); o.i = j; o.u = stop ? 0 : u;
    if (stop) { o.v = 0; o.waitT = o.wait; if (o.trig === 'stand' || o.lift) o.idle = true; if (o.lift && kitNear(o.x, o.y)) kitSfx.clunk(); }
    else if (o.u > 0) { const p = kitMoverPos(o); kitSlabMove(o, Math.round(p.x), Math.round(p.y), dt); }
  } else o.u = u;
}
KIT_KINDS.mover = s => {
  const o = kitObj('mover', s); kitMoverInit(o, s, { w: 3, speed: 2, wait: 0.5 });
  o.tick = dt => {
    o.on = kitDerive(o, !(s.trigger && s.trigger !== 'stand'));
    let run = o.on;
    if (o.trig === 'stand') {
      const stood = kitStoodBy(o);
      if (o.idle && stood && o.waitT <= 0) { o.idle = false; o.retT = 0; }
      if (o.idle && !stood && o.ret > 0 && o.i !== 0) { o.retT += dt; if (o.retT >= o.ret) { o.idle = false; o.retT = 0; } }
      run = run && !o.idle;
    }
    kitMoverUpdate(o, dt, run);
  };
  o.draw = () => kitDrawSlab(o, o.d.x0, o.d.y0);
  return o;
};
// ---- lift: vertical mover with chains to the ceiling. x,y = home stop; to = other stop row. Stand on it to ride; call it
// from either landing by standing next to its shaft. auto:true = runs up and down on its own.
KIT_KINDS.lift = s => {
  const o = kitObj('lift', s), to = s.to ?? s.y - 6;
  const spec = { ...s, path: [[s.x, s.y], [s.x, to]], trigger: s.auto ? (s.trigger && s.trigger !== 'stand' ? s.trigger : null) : (s.trigger ?? 'stand') };
  o.spec = spec; o.lift = true;
  kitMoverInit(o, spec, { w: 3, speed: 3, wait: s.auto ? 0.8 : 0.3, ret: 0 });
  o.call = s.call ?? !s.auto;
  let top = Math.min(s.y, to) * TILE; while (top > 0 && !isSolidT(tileAt(Math.floor((s.x * TILE + 4) / TILE), Math.floor((top - 1) / TILE)))) top -= TILE;
  o.top = top;
  o.tick = dt => {
    o.on = kitDerive(o, !(spec.trigger && spec.trigger !== 'stand'));
    let run = o.on;
    if (spec.trigger === 'stand') {
      const stood = kitStoodBy(o);
      if (o.idle && stood && o.waitT <= 0) { o.idle = false; kitSfx.lift(); }
      // call: standing on a landing next to the shaft while the lift waits at the other stop brings it to you
      if (o.idle && o.call && !stood && P.ground && o.waitT <= 0) {
        const far = o.pts[o.i === 0 ? 1 : 0];
        if (Math.abs(P.y - far.y) < 2 && Math.abs(P.x - (far.x + o.w / 2)) < o.w / 2 + 28) { o.idle = false; kitSfx.lift(); }
      }
      run = run && !o.idle;
    }
    const wasV = o.v; kitMoverUpdate(o, dt, run);
    if (o.v > 1) o.chainT = (o.chainT || 0) + (o.d.y0 - (o.lastY ?? o.d.y0));
    o.lastY = o.d.y0;
    if (wasV < 1 && o.v >= 1 && kitNear(o.x, o.y) && !spec.trigger) kitSfx.lift();
  };
  o.draw = () => {
    const x0 = o.d.x0, y0 = o.d.y0, sh = sheet('kit_gate');
    for (const cx of [x0 + 4, x0 + o.w - 5]) kitDrawChain(cx, o.top, y0 - 2, o.pal, o.chainT || 0);
    if (sh.ok && sh.has('yoke_' + o.skin)) { const f = sh.first('yoke_' + o.skin); for (const cx of [x0 + 4, x0 + o.w - 5]) drawSprite(sh, f, cx + 0.5, y0 + 1, 1, { bottom: true }); }
    kitDrawSlab(o, x0, y0);
  };
  return o;
};
function kitDrawChain(cx, y0, y1, pal, phase = 0, style = 'chain') {
  const X = Math.round(cx), off = ((Math.round(phase) % 4) + 4) % 4;
  if (style === 'rope' || style === 'vine') { g.fillStyle = pal.d; g.fillRect(X, y0, 1, y1 - y0); g.fillStyle = pal.l; for (let y = y0 + off; y < y1; y += 4) g.fillRect(X, y, 1, 2); return; }
  for (let y = y0 - off; y < y1; y += 4) {
    const a = Math.max(y, y0), b = Math.min(y + 3, y1); if (b <= a) continue;
    if (((y - y0 + off) >> 2) & 1) { g.fillStyle = pal.k; g.fillRect(X, a, 1, b - a); g.fillStyle = pal.h; g.fillRect(X, a, 1, 1); }
    else { g.fillStyle = pal.k; g.fillRect(X - 1, a, 3, b - a); g.fillStyle = pal.l; g.fillRect(X - 1, a, 1, b - a); g.fillStyle = pal.m; g.fillRect(X + 1, a, 1, b - a); }
  }
}
// ---- crumble: shakes `delay` s after you stand on it, falls, returns after `respawn` s (0 = never)
KIT_KINDS.crumble = s => {
  const o = kitObj('crumble', s); kitSlab(o, s, 2);
  const delay = s.delay ?? 0.5, respawn = s.respawn ?? 3;
  o.reset = () => { Object.assign(o, { st: 'idle', t: 0, alpha: 1, bits: [] }); o.solidNow = true; };
  o.reset();
  o.tick = dt => {
    if (o.st === 'idle' && kitStoodBy(o, 'any')) { o.st = 'shake'; o.t = delay; if (kitNear(o.x, o.y)) { noise(0.25, 700, 0.8, 0.1, 'bandpass'); kitSfx.creak(); } }
    else if (o.st === 'shake') {
      o.t -= dt;
      if (Math.random() < 0.3) particles.push({ x: rand(o.d.x0, o.d.x1), y: o.d.y0 + 7, vx: 0, vy: rand(10, 40), g: 300, life: 0.5, kind: 'dust' });
      if (o.t <= 0) {
        o.st = 'gone'; o.t = respawn; o.solidNow = false; if (kitNear(o.x, o.y)) sfx.crumble();
        for (let i = 0; i < o.w / TILE; i++) o.bits.push({ x: o.d.x0 + i * TILE, y: o.d.y0, vy: rand(0, 30), vr: rand(-3, 3), r: 0, life: 1.4 });
        for (let i = 0; i < 6; i++) particles.push({ x: rand(o.d.x0, o.d.x1), y: o.d.y0 + rand(0, 6), vx: rand(-40, 40), vy: rand(-30, 30), g: 400, life: rand(0.5, 1), kind: 'rock' });
      }
    } else if (o.st === 'gone' && respawn > 0) {
      o.t -= dt;
      if (o.t <= 0 && !kitSlabOverlapped(o)) { o.st = 'back'; o.alpha = 0; o.solidNow = true; }
    } else if (o.st === 'back') { o.alpha = Math.min(1, o.alpha + dt * 3); if (o.alpha >= 1) o.st = 'idle'; }
    for (const b of o.bits) { b.vy += 520 * dt; b.y += b.vy * dt; b.r += b.vr * dt; b.life -= dt; }
    o.bits = o.bits.filter(b => b.life > 0);
  };
  o.draw = () => {
    const sh = sheet('kit_plat');
    for (const b of o.bits) {
      if (sh.ok && sh.has(o.skin)) drawRotated(sh, sh.first(o.skin) + 1, b.x + 8, b.y + 8, b.r, Math.min(1, b.life * 1.5));
      else { g.fillStyle = o.pal.m; g.fillRect(Math.round(b.x), Math.round(b.y), 16, 6); }
    }
    if (o.st === 'gone') return;
    const sk = o.st === 'shake', k = sk ? 1 - o.t / delay : 0;
    kitDrawSlab(o, o.d.x0, o.d.y0, o.alpha, sk ? (k > 0.5 ? 2 : 1) : 1, sk ? Math.round(rand(-1, 1) * (0.5 + k)) : 0, sk && Math.random() < k ? 1 : 0);
  };
  return o;
};
// ---- sinker: sinks at `rate` tiles/s while stood on (after `delay`), down to `depth` tiles; rises back at `rise` when left
KIT_KINDS.sinker = s => {
  const o = kitObj('sinker', s); kitSlab(o, s, 2);
  const rate = (s.rate ?? 0.75) * TILE, rise = (s.rise ?? 1) * TILE, depth = (s.depth ?? 3) * TILE, delay = s.delay ?? 0.15;
  let depth2 = 0; while (depth2 < depth && !isSolidT(tileAt(Math.floor((o.d.x0 + 2) / TILE), Math.floor((o.d.y1 + depth2) / TILE))) && !isSolidT(tileAt(Math.floor((o.d.x1 - 2) / TILE), Math.floor((o.d.y1 + depth2) / TILE)))) depth2++;   // rests on the bottom
  const maxS = Math.min(depth, depth2);
  o.reset = () => { o.sink = 0; o.stT = 0; kitSlabMove(o, o.d.x0, s.y * TILE, 1 / 60); };
  o.sink = 0; o.stT = 0;
  o.tick = dt => {
    const on = kitStoodBy(o, 'any');
    o.stT = on ? o.stT + dt : 0;
    const want = on && o.stT >= delay ? Math.min(maxS, o.sink + rate * dt) : Math.max(0, o.sink - rise * dt);
    if (want !== o.sink && kitSlabMove(o, o.d.x0, s.y * TILE + Math.round(want), dt)) {
      if (want > o.sink && Math.random() < 0.25) particles.push({ x: rand(o.d.x0, o.d.x1), y: o.d.y0 + 6, vx: rand(-10, 10), vy: -rand(5, 20), life: 0.6, kind: o.skin === 'wood' ? 'spore' : 'dust' });
      o.sink = want;
    }
  };
  o.draw = () => kitDrawSlab(o, o.d.x0, o.d.y0, 1, 0, 0, 0);
  return o;
};
// ---- phase: solid only during its slice of a beat. period s, on:[a,b] fractions, offset fraction. Blinks before vanishing.
KIT_KINDS.phase = s => {
  const o = kitObj('phase', s); kitSlab(o, s, 2);
  const period = s.period ?? 2, on = s.on || [0, 0.5], off = s.offset || 0, warn = s.warn ?? Math.min(0.45, period * (((on[1] - on[0] + 1) % 1) || 1) * 0.35);
  o.phaseAt = t => { const k = (((t / period + off) % 1) + 1) % 1; return on[0] <= on[1] ? (k >= on[0] && k < on[1]) : (k >= on[0] || k < on[1]); };
  o.left = t => { let k = 0; for (let i = 1; i <= 60; i++) { if (!o.phaseAt(t + i * period / 60)) { k = i * period / 60; break; } } return k; };
  o.reset = () => { o.was = o.phaseAt(KIT.t); o.solidNow = o.was; o.alpha = o.was ? 1 : 0; };
  o.reset();
  o.tick = dt => {
    const want = o.phaseAt(KIT.t);
    if (want && !o.solidNow) { if (!kitSlabOverlapped(o)) { o.solidNow = true; if (kitNear(o.x, o.y, 200)) kitSfx.blip(true); } }
    else if (!want && o.solidNow) { o.solidNow = false; if (kitNear(o.x, o.y, 200)) kitSfx.blip(false); }
    o.alpha = approach(o.alpha, o.solidNow ? 1 : 0, dt * (o.solidNow ? 9 : 6));
    o.warnK = o.solidNow ? clamp(1 - o.left(KIT.t) / warn, 0, 1) : 0;
    if (o.solidNow) addLight(o.x, o.d.y0 + 4, 26, o.pal.glow, 0.3 * o.alpha);
  };
  o.draw = () => {
    const blink = o.warnK > 0 && Math.floor(KIT.t * (8 + 10 * o.warnK)) % 2 === 1;
    if (o.alpha > 0.02) kitDrawSlab(o, o.d.x0, o.d.y0, o.alpha * (blink ? 0.35 : 1));
    // ghost outline while absent so you can read where it will be; bright rim while solid
    const a = o.solidNow ? 0.55 * o.alpha * (blink ? 0.3 : 1) : 0.22;
    g.fillStyle = `rgba(${o.pal.glow},${a})`;
    const X = Math.round(o.d.x0), Y = Math.round(o.d.y0);
    if (o.solidNow) g.fillRect(X + 1, Y, o.w - 2, 1);
    else for (let x = X; x < X + o.w; x += 3) { g.fillRect(x, Y, 1, 1); g.fillRect(x + 1, Y + 7, 1, 1); }
  };
  return o;
};
// ---- spring: a bounce pad on the floor. power px/s (default 520 ≈ 2× jump height)
KIT_KINDS.spring = s => {
  const o = kitObj('spring', s);
  const x0 = s.x * TILE, fy = (s.y + 1) * TILE, pw = s.power ?? 520;
  o.x = x0 + 8; o.y = fy; o.w = TILE; o.th = 6; o.oneway = true; o.solidNow = true; o.off = false; o.squash = 0;
  o.d = { x0: x0 + 1, x1: x0 + 15, y0: fy - 6, y1: fy, kit: o, oneway: true, on: () => !o.off && P.drop <= 0 && P.y <= o.d.y0 + 0.5 };
  room.dyn.push(o.d);
  o.tick = dt => {
    o.squash = Math.max(0, o.squash - dt * 5);
    if (kitStands(P, o.d) && P.state !== 'dead') {
      P.vy = -pw; P.ground = false; P.y -= 1; P.coyote = 0; P.airDash = true; if (SAVE.items.wings) P.airJumps = 1; KIT.boost = { vy: -pw };
      if (!ATK[P.state]) setP('air', 'jump_up', false);
      o.squash = 1; kitSfx.boing(); spawnFx('dust', o.x, fy, 1);
    }
    for (const q of KIT.objs) if (q.kind === 'crate' && q.body && kitStands(q.body, o.d)) { q.body.vy = -pw * 0.8; q.body.y -= 1; q.body.ground = false; o.squash = 1; }
  };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'spring_' + o.skin;
    if (sh.ok && sh.has(tg)) { drawSprite(sh, sh.first(tg) + (o.squash > 0.4 ? 1 : 0), o.x, fy, 1, { bottom: true }); return; }
    g.fillStyle = o.pal.k; g.fillRect(x0 + 1, fy - 7, 14, 7); g.fillStyle = o.pal.acc; g.fillRect(x0 + 2, fy - 7 + (o.squash > 0.4 ? 2 : 0), 12, 2);
  };
  return o;
};
// ---- crate: a pushable box (walk into it). Presses plates, blocks beams, rides slabs. Stand on it.
KIT_KINDS.crate = s => {
  const o = kitObj('crate', s);
  const sx = s.x * TILE + 8, sy = (s.y + 1) * TILE;
  o.body = { x: sx, y: sy, w: 16, h: 16, vx: 0, vy: 0, ground: true, crate: o };
  o.off = false; o.oneway = false; o.solidNow = true;
  o.d = { x0: sx - 8, x1: sx + 8, y0: sy - 16, y1: sy, kit: o, on: () => !o.off };
  room.dyn.push(o.d);
  const sync = () => { o.d.x0 = o.body.x - 8; o.d.x1 = o.body.x + 8; o.d.y0 = o.body.y - 16; o.d.y1 = o.body.y; o.x = o.body.x; o.y = o.body.y; };
  o.reset = () => { Object.assign(o.body, { x: sx, y: sy, vx: 0, vy: 0, ground: true }); sync(); };
  sync();
  o.tick = dt => {
    const b = o.body;
    // pushing: the player walks into its side on the ground; box and player move together (no stutter)
    const ax = inputX();
    if (ax && P.ground && free() && b.ground && P.hitWall === ax && Math.abs(P.y - b.y) < 8 && Math.abs((P.x + ax * (P.w / 2)) - (b.x - ax * 8)) < 1.5) {
      const dx = ax * 52 * dt;
      o.off = true; const ok = kitFree(b, b.x + dx, b.y, null); o.off = false;
      if (ok) { b.x += dx; sync(); P.x += dx; o.pushT = (o.pushT || 0) + dt; if (o.pushT > 0.3) { o.pushT = 0; noise(0.12, 260, 0.7, 0.07, 'lowpass'); } }
    }
    // gravity (its own slab off while it moves)
    o.off = true; b.vy = Math.min(b.vy + GRAV_DN * dt, FALL_MAX); b.vx = 0; const was = b.ground; moveBody(b, dt); o.off = false;
    if (b.ground && !was && kitNear(b.x, b.y)) sfx.land();
    // riders on the box move with it vertically (it only falls)
    sync();
    if (b.y > room.ph + 40) o.reset();
  };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'crate_' + o.skin;
    if (sh.ok && sh.has(tg)) { drawSprite(sh, sh.first(tg), o.body.x, o.body.y, 1, { bottom: true }); return; }
    const X = Math.round(o.body.x - 8), Y = Math.round(o.body.y - 16), p = o.pal;
    g.fillStyle = p.k; g.fillRect(X, Y, 16, 16); g.fillStyle = p.m; g.fillRect(X + 1, Y + 1, 14, 14); g.fillStyle = p.l; g.fillRect(X + 1, Y + 1, 14, 1);
    g.fillStyle = p.d; g.fillRect(X + 2, Y + 7, 12, 2);
  };
  return o;
};
// ---- swing: a rope / chain / vine hanging from x,y. Touch it in the air to grab; ←/→ pump, ↑/↓ climb, jump lets go with
// the swing's momentum. len tiles, amp degrees + period s = its idle sway. drive:'auto' = it swings on its own schedule.
KIT_KINDS.swing = s => {
  const o = kitObj('swing', s);
  const ax0 = s.x * TILE + 8, ay0 = s.y * TILE + 2, L = (s.len ?? 5) * TILE, amp = (s.amp ?? 25) * Math.PI / 180, per = s.period ?? 2.6, auto = s.drive === 'auto';
  o.anchor = { x: ax0, y: ay0 }; o.len = L; o.x = ax0; o.y = ay0; o.style = s.rope || o.pal.rope;
  o.reset = () => { o.ang = amp * Math.sin((s.phase || 0) * Math.PI * 2); o.av = amp * Math.PI * 2 / per * Math.cos((s.phase || 0) * Math.PI * 2); o.e = undefined; o.cd = 0; o.held = false; if (P.hook && P.hook.kit === o) { P.hook = null; setP('air', 'jump_fall', false); } };
  o.reset();
  const w = Math.PI * 2 / per;
  o.tick = dt => {
    o.cd -= dt;
    const mine = P.hook && P.hook.kit === o;
    if (o.held && (!mine || P.state !== 'hook')) {   // released (jump / roll / hurt): keep its motion, go free
      o.held = false; o.cd = 0.3; o.e = undefined; if (mine) P.hook = null;
    }
    if (o.held) {
      const H = P.hook;
      if (auto) {   // the rope carries you on its own schedule
        o.ang = amp * Math.sin(KIT.t * w + (s.phase || 0) * Math.PI * 2); o.av = amp * w * Math.cos(KIT.t * w + (s.phase || 0) * Math.PI * 2);
        const nx = ax0 + Math.sin(o.ang) * H.len, ny = ay0 + Math.cos(o.ang) * H.len + 34;
        if (kitFree(P, nx, ny, null)) { P.x = nx; P.y = ny; }
        H.ang = o.ang; H.av = o.av;
      } else {
        // a rope can't swing up over its anchor: stop at ~100° and fall back
        if (Math.abs(H.ang) > 1.75) { const na = sign(H.ang) * 1.75, nx = ax0 + Math.sin(na) * H.len, ny = ay0 + Math.cos(na) * H.len + 34; H.ang = na; if (H.av * sign(na) > 0) H.av = 0; if (kitFree(P, nx, ny, null)) { P.x = nx; P.y = ny; } }
        o.ang = H.ang; o.av = H.av;
      }
      const ay = (held.has('down') ? 1 : 0) - (held.has('up') ? 1 : 0);   // climb
      if (ay) { const nl = clamp(H.len + ay * 46 * dt, 18, L); const nx = ax0 + Math.sin(H.ang) * nl, ny = ay0 + Math.cos(H.ang) * nl + 34; if (kitFree(P, nx, ny, null)) { H.len = nl; P.x = nx; P.y = ny; } }
      if (Math.abs(o.av) > 1.6 && Math.random() < dt * 1.2) kitSfx.creak();
      return;
    }
    if (auto) { o.ang = amp * Math.sin(KIT.t * w + (s.phase || 0) * Math.PI * 2); o.av = amp * w * Math.cos(KIT.t * w + (s.phase || 0) * Math.PI * 2); }
    else {   // free: its idle sway plus whatever motion it was left with, dying away (a damped offset — no resonance)
      const ph = KIT.t * w + (s.phase || 0) * Math.PI * 2, tgt = amp * Math.sin(ph), tv = amp * w * Math.cos(ph);
      if (o.e === undefined) { o.e = o.ang - tgt; o.ev = o.av - tv; }
      o.ev += (-(w * w) * o.e - 2 * 0.35 * w * o.ev) * dt; o.e += o.ev * dt;
      o.ang = tgt + o.e; o.av = tv + o.ev;
    }
    // grab: hands near any point of the rope, in the air, not holding ↓
    if (o.cd > 0 || P.ground || held.has('down') || !(free() || P.state === 'roll') || P.state === 'wall' || P.state === 'dead') return;
    const hx = P.x, hy = P.y - 24, sx = Math.sin(o.ang), sy = Math.cos(o.ang);
    const t = clamp((hx - ax0) * sx + (hy - ay0) * sy, 14, L), px = ax0 + sx * t, py = ay0 + sy * t;
    if (Math.hypot(hx - px, hy - py) > 9) return;
    const len = clamp(t - 10, 18, L), a = o.ang;
    const av = auto ? o.av : clamp((P.vx * Math.cos(a) - P.vy * Math.sin(a)) / len * 0.9 + o.av * 0.5, -3.6, 3.6);
    P.hook = { h: o.anchor, len, ang: a, av, zip: false, rope: true, kit: o };
    P.x = ax0 + Math.sin(a) * len; P.y = ay0 + Math.cos(a) * len + 34; P.vx = P.vy = 0;
    setP('hook', pHas('hook_swing') ? 'hook_swing' : 'jump_fall', true);
    o.held = true; kitSfx.creak(); noise(0.08, 900, 0.8, 0.1, 'bandpass');
    if (P.airJumps !== undefined && SAVE.items.wings) P.airJumps = 1; P.airDash = true;
  };
  o.draw = () => {
    const H = o.held && P.hook && P.hook.kit === o ? P.hook : null, sx = Math.sin(o.ang), sy = Math.cos(o.ang);
    const pts = [];
    if (H) { const hx = P.x, hy = P.y - 34; pts.push([ax0, ay0], [hx, hy], [hx + sx * (L - H.len), hy + sy * (L - H.len)]); }
    else { const bend = clamp(-o.av * 0.06, -0.25, 0.25); pts.push([ax0, ay0], [ax0 + Math.sin(o.ang + bend) * L * 0.5, ay0 + Math.cos(o.ang + bend) * L * 0.5], [ax0 + sx * L, ay0 + sy * L]); }
    kitDrawRope(pts, o.style, o.pal);
    const sh = sheet('kit_gate');
    if (sh.ok && sh.has('anchor_' + o.skin)) drawSprite(sh, sh.first('anchor_' + o.skin), ax0, ay0 + 4, 1, { bottom: true });
    else { g.fillStyle = o.pal.k; g.fillRect(ax0 - 3, ay0 - 2, 6, 4); g.fillStyle = o.pal.acc; g.fillRect(ax0 - 1, ay0 - 1, 2, 2); }
    if (o.style === 'cable') { const e = pts[pts.length - 1]; addLight(e[0], e[1], 18, o.pal.glow, 0.45); }
  };
  return o;
};
function kitDrawRope(pts, style, pal) {
  // 2-3 px wide so it reads against dark walls: dark outline, lit core, a twist / link highlight every few pixels
  const col = style === 'vine' ? ['#0e1a0a', '#3a6428', '#7aa844', '#a8d060'] : style === 'chain' ? ['#0a0a0e', pal.m, pal.l, pal.h] : style === 'cable' ? ['#06060e', '#1a8aa8', '#30e8ff', '#d0ffff'] : ['#140e08', '#6e5232', '#a07c50', '#caa878'];
  let n = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[i + 1], L = Math.hypot(x1 - x0, y1 - y0), steps = Math.max(1, Math.ceil(L));
    const horiz = Math.abs(x1 - x0) > Math.abs(y1 - y0);
    for (let k = 0; k < steps; k++, n++) {
      const x = Math.round(lerp(x0, x1, k / steps)), y = Math.round(lerp(y0, y1, k / steps));
      const sx = horiz ? 0 : 1, sy = horiz ? 1 : 0;   // widen across the rope
      g.fillStyle = col[0]; g.fillRect(x - sx, y - sy, 1 + 2 * sx, 1 + 2 * sy);
      if (style === 'chain') {
        const link = n % 6;
        g.fillStyle = link < 3 ? col[2] : col[1]; g.fillRect(x - (link < 3 ? 0 : sx), y - (link < 3 ? 0 : sy), 1 + (link < 3 ? 0 : sx), 1 + (link < 3 ? 0 : sy));
        if (link === 0) { g.fillStyle = col[3]; g.fillRect(x, y, 1, 1); }
      } else if (style === 'cable') {
        g.fillStyle = (n + Math.floor(time * 30)) % 9 < 2 ? col[3] : col[2]; g.fillRect(x, y, 1, 1);
      } else {
        g.fillStyle = col[1]; g.fillRect(x - sx, y - sy, 1 + sx, 1 + sy);
        g.fillStyle = n % 4 < 2 ? col[2] : col[1]; g.fillRect(x, y, 1, 1);
        if (n % 4 === 0) { g.fillStyle = col[3]; g.fillRect(x - sx, y - sy, 1, 1); }
        if (style === 'vine' && n % 9 === 4) { const d = n % 18 < 9 ? 1 : -1; g.fillStyle = col[2]; g.fillRect(x + d * 2, y - 1, 2, 1); g.fillStyle = col[3]; g.fillRect(x + d * 2 + (d > 0 ? 1 : 0), y - 2, 1, 1); g.fillStyle = col[1]; g.fillRect(x + d * 2, y, 2, 1); }
      }
    }
  }
}
// ---- pendulum: a swinging blade (hazard). x,y = pivot cell; len tiles, period s, amp degrees, phase 0..1, dmg
KIT_KINDS.pendulum = s => {
  const o = kitObj('pendulum', s);
  const px = s.x * TILE + 8, py = s.y * TILE + 2, L = (s.len ?? 4) * TILE, per = s.period ?? 2.2, amp = (s.amp ?? 60) * Math.PI / 180, dmg = s.dmg ?? 30;
  o.x = px; o.y = py; o.hid = 'kpend' + (++KIT.hid);
  o.at = () => { const a = amp * Math.sin((KIT.t / per + (s.phase || 0)) * Math.PI * 2); return { a, bx: px + Math.sin(a) * L, by: py + Math.cos(a) * L }; };
  o.tick = dt => {
    const { a, bx, by } = o.at(), av = amp * Math.cos((KIT.t / per + (s.phase || 0)) * Math.PI * 2);
    const swingN = Math.floor((KIT.t / per + (s.phase || 0)) * 2 + 0.5);
    if (swingN !== o.lastN) { o.lastN = swingN; if (kitNear(bx, by, 220)) kitSfx.whoosh(0.8); }
    const hb = playerHurtbox(), r = 10;
    const cx = clamp(bx, hb.x0, hb.x1), cy = clamp(by, hb.y0, hb.y1);
    if (Math.hypot(bx - cx, by - cy) < r && P.state !== 'dead') hurtPlayer(dmg * NGP.dmg, sign(av * Math.cos(a)) || sign(P.x - bx), o.hid + ':' + swingN, { src: o, kit: 'pendulum' });
  };
  o.draw = () => {
    const { a, bx, by } = o.at();
    kitDrawRope([[px, py], [px + Math.sin(a) * (L - 10), py + Math.cos(a) * (L - 10)]], 'chain', o.pal);
    const sh = sheet('kit_parts'), tg = 'blade_' + o.skin;
    if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg), bx, by, 1, { pivot: [16, 16], rot: -a });
    else { g.save(); g.translate(Math.round(bx), Math.round(by)); g.rotate(-a); g.fillStyle = o.pal.k; g.fillRect(-12, -3, 24, 8); g.fillStyle = o.pal.h; g.fillRect(-11, 3, 22, 1); g.restore(); }
    if (o.skin === 'neon') addLight(bx, by, 30, o.pal.glow, 0.7);
    const sh2 = sheet('kit_gate');
    if (sh2.ok && sh2.has('anchor_' + o.skin)) drawSprite(sh2, sh2.first('anchor_' + o.skin), px, py + 4, 1, { bottom: true });
  };
  return o;
};
// ---- rising: a hazard floor that climbs for chase rooms. x..x+w tiles wide, surface starts at row y, stops at stopY.
// trigger: 'enter' (default) | 'zone' (+ zone:[x,y,w,h]) | '<id>'. Touching it hurts (fluid dmg) and sends you back to
// `respawn` [x,y] (default: where you stood when it started) with the floor reset. goal:[x,y,w,h] = escaped, it drains.
KIT_KINDS.rising = s => {
  const o = kitObj('rising', s);
  const F = KIT_FLUID[s.fluid || 'lava'] || KIT_FLUID.lava, x0 = (s.x ?? 0) * TILE, x1 = s.w ? x0 + s.w * TILE : room.pw;
  const base = (s.y + 1) * TILE + 4, stop = (s.stopY ?? 1) * TILE + 4, spd = (s.speed ?? 1.2) * TILE, delay = s.delay ?? 1.2;
  const trig = s.trigger || (s.zone ? 'zone' : 'enter');
  o.F = F; o.x = (x0 + x1) / 2; o.y = base; o.x0 = x0; o.x1 = x1;
  o.reset = () => { Object.assign(o, { sy: base, st: trig === 'enter' ? 'wait' : 'armed', t: delay, from: null, done: false }); };
  o.reset();
  const inZone = z => z && P.x >= z[0] * TILE && P.x < (z[0] + z[2]) * TILE && P.y > z[1] * TILE && P.y <= (z[1] + z[3]) * TILE;
  o.tick = dt => {
    if (o.st === 'armed') {
      const go = trig === 'zone' ? inZone(s.zone) : trig !== 'enter' && kitSrc(trig);
      if (go) { o.st = 'wait'; o.t = delay; }
    }
    if (o.st === 'wait') { if (!o.from) o.from = { x: P.safe.x, y: P.safe.y }; if (o.t === delay) { if (F.fire) { shake = Math.max(shake, 5); sfx.boom(); } else kitSfx.whoosh(1); toast(s.msg || 'It\'s rising — climb!', 2.5); } o.t -= dt; if (o.t <= 0) o.st = 'rise'; }
    else if (o.st === 'rise') { o.sy = Math.max(stop, o.sy - spd * dt); if (Math.random() < 0.3) shake = Math.max(shake, 0.8); if (o.sy <= stop) o.st = 'top'; }
    else if (o.st === 'drain') o.sy = Math.min(base, o.sy + spd * 2 * dt);
    if (s.goal && !o.done && (o.st === 'rise' || o.st === 'top') && inZone(s.goal) && P.ground) { o.done = true; o.st = 'drain'; sfx.felled(); }
    // caught
    if (P.state !== 'dead' && P.inv <= 0 && P.y - 6 > o.sy && P.x > x0 && P.x < x1 && o.st !== 'drain') kitFluidHurt(F, o, () => {
      const to = s.respawn ? { x: s.respawn[0] * TILE + 8, y: (s.respawn[1] + 1) * TILE } : o.from || P.safe;
      o.reset(); if (trig === 'enter') { o.st = 'wait'; o.t = delay; }
      return to;
    });
    for (let x = Math.max(x0, cam.x - 20) + 20; x < Math.min(x1, cam.x + W + 20); x += 48) addLight(x, o.sy + 4, 60, F.light, F.fire ? 0.9 : 0.45);
  };
  o.fluid = () => ({ x0, x1, y: o.sy, y1: room.ph, F });
  return o;
};
// fluid hit: damage (fraction of max HP), then back to a spot the callback picks
function kitFluidHurt(F, o, respawn) {
  if (P.state === 'dead' || P.inv > 0) return;
  // through the playerHurt hooks like any hit (charms, KS trials): a hook returning 0 cancels it and owns the respawn
  const opt = { src: o, kit: o.kind, hazard: true, fire: !!F.fire };
  let dmg = Math.round(D.maxHp * (o.spec.dmg ?? F.dmg) * NGP.dmg);
  for (const f of HOOKS.playerHurt) dmg = Math.round(f(dmg, opt) ?? dmg);
  if (dmg <= 0) { P.inv = Math.max(P.inv, 0.5); return; }
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; shake = 6; hitstop = 0.1; sfx.hurt();
  if (F.fire) { sfx.fire(); for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 10), vx: rand(-60, 60), vy: -rand(60, 180), g: 420, life: rand(0.4, 0.8), kind: Math.random() < 0.5 ? 'fire' : 'ember' }); }
  if (F.rot && typeof addRot === 'function') addRot(60);
  popup(P.x, P.y - 30, dmg, F.fire ? '#ff8a3a' : '#c8e0a0');
  if (P.hp <= 0) return killPlayer(0);
  P.inv = 1.0; P.vx = 0; P.vy = -140; setP('hurt', 'hurt');
  const to = respawn();
  fadeTo(() => { P.x = to.x; P.y = to.y; P.vx = P.vy = 0; setP('idle', 'idle', true); updateCamera(0, true); });
}
function kitDrawFluid(f, t) {
  // drawn only over open cells, so a pool stays inside its basin and a rising floor climbs a shaft between its walls
  const F = f.F, x0 = Math.max(f.x0, Math.floor(cam.x) - 2), x1 = Math.min(f.x1, Math.ceil(cam.x + W) + 2), sy = f.y;
  const yb = Math.min(f.y1, Math.ceil(cam.y + H) + 2);
  if (x1 <= x0 || sy > yb) return;
  const wave = x => Math.sin(t * 2.4 + x * 0.11) * 1.5 + Math.sin(t * 3.7 + x * 0.23);
  g.save(); g.globalAlpha = F.alpha;
  for (let tx = Math.floor(x0 / TILE); tx * TILE < x1; tx++) {
    const cx0 = Math.max(x0, tx * TILE), cx1 = Math.min(x1, tx * TILE + TILE); if (cx1 <= cx0) continue;
    let run = null;
    for (let ty = Math.floor(sy / TILE); ty * TILE < yb; ty++) {
      const o = !isSolidT(tileAt(tx, ty)), y0 = Math.max(sy + 3, ty * TILE), y1 = Math.min(yb, ty * TILE + TILE);
      if (o && y1 > y0) { if (!run) run = [y0, y1]; else run[1] = y1; }
      else if (run) { g.fillStyle = F.body; g.fillRect(cx0, run[0], cx1 - cx0, run[1] - run[0]); run = null; }
    }
    if (run) { g.fillStyle = F.body; g.fillRect(cx0, run[0], cx1 - cx0, run[1] - run[0]); }
  }
  for (let x = Math.floor(x0 / 2) * 2; x < x1; x += 2) {
    if (isSolidT(tileAt(Math.floor(x / TILE), Math.floor((sy + 2) / TILE)))) continue;
    const w = wave(x);
    g.globalAlpha = F.alpha; g.fillStyle = F.mid; g.fillRect(x, Math.round(sy + 2 + w), 2, 4);
    g.globalAlpha = Math.min(1, F.alpha + 0.25); g.fillStyle = F.top; g.fillRect(x, Math.round(sy + 1 + w), 2, 1);
  }
  if (F.fire) { g.globalAlpha = 0.8; g.fillStyle = 'rgba(255,220,120,1)'; for (let x = x0 + ((Math.floor(t * 40)) % 23); x < x1; x += 23) if (!isSolidT(tileAt(Math.floor(x / TILE), Math.floor((sy + 6) / TILE)))) g.fillRect(x, Math.round(sy) + 5 + (x % 7), 1, 1); }
  g.restore();
}
// ---- wind: an area force. x,y,w,h tiles; vx, vy px/s (vy<0 lifts you in the air); period + on:[a,b] = gusts
KIT_KINDS.wind = s => {
  const o = kitObj('wind', s);
  const r = { x0: s.x * TILE, y0: s.y * TILE, x1: (s.x + (s.w ?? 4)) * TILE, y1: (s.y + (s.h ?? 4)) * TILE }, vx = s.vx ?? 0, vy = s.vy ?? 0;
  const per = s.period || 0, on = s.on || [0, 0.5];
  o.x = (r.x0 + r.x1) / 2; o.y = r.y1; o.r = r; o.streaks = []; o.k = 0;
  const gustAt = t => { if (!per) return true; const k = (((t / per + (s.offset || 0)) % 1) + 1) % 1; return on[0] <= on[1] ? k >= on[0] && k < on[1] : k >= on[0] || k < on[1]; };
  o.tick = dt => {
    o.on = kitDerive(o, !kitTrig(o));
    const want = o.on && gustAt(KIT.t), warn = o.on && per && !want && gustAt(KIT.t + 0.6);
    o.k = approach(o.k, want ? 1 : warn ? 0.12 : 0, dt * (want ? 4 : 2));
    if (want && !o.was && kitNear(o.x, o.y, 300)) kitSfx.whoosh(1.2);
    o.was = want;
    const inside = P.x > r.x0 && P.x < r.x1 && P.y - 12 > r.y0 && P.y - 12 < r.y1;
    if (inside && o.k > 0.15 && !['hook', 'rest', 'dead', 'rise'].includes(P.state)) {
      if (vx) P.pushVx = (P.pushVx || 0) + vx * o.k * (P.ground ? 1 : 1.15);
      if (vy && !P.ground) { const tv = vy * o.k; if (vy < 0 ? P.vy > tv : P.vy < tv) P.vy = approach(P.vy, tv, (Math.abs(vy) * 5 + 700) * dt); }
    }
    if (inside && vy < 0 && o.k > 0.5 && P.state === 'air' && P.vy < 0) P.coyote = 0;
    const rate = (want ? 26 : warn ? 5 : 0) * (r.x1 - r.x0) * (r.y1 - r.y0) / 40000;
    let n = rate * dt;
    const dir = Math.atan2(vy, vx || 0.0001), sp = Math.hypot(vx, vy) * 2.2 + 120;
    while (n > 0) { if (Math.random() < n) o.streaks.push({ x: rand(r.x0, r.x1), y: rand(r.y0, r.y1), vx: Math.cos(dir) * sp, vy: Math.sin(dir) * sp, life: rand(0.3, 0.7), len: rand(5, 14) }); n -= 1; }
    for (const q of o.streaks) { q.x += q.vx * dt; q.y += q.vy * dt; q.life -= dt; }
    o.streaks = o.streaks.filter(q => q.life > 0 && q.x > r.x0 - 8 && q.x < r.x1 + 8 && q.y > r.y0 - 8 && q.y < r.y1 + 8);
  };
  o.fx = () => {
    const c = o.skin === 'neon' ? '120,240,255' : o.skin === 'crystal' ? '200,225,255' : o.skin === 'wood' ? '200,220,170' : '210,215,225';
    const dx = Math.cos(Math.atan2(vy, vx || 0.0001)), dy = Math.sin(Math.atan2(vy, vx || 0.0001));
    for (const q of o.streaks) { const a = Math.min(1, q.life * 3) * 0.45; g.fillStyle = `rgba(${c},${a})`; for (let i = 0; i < q.len; i += 1) g.fillRect(Math.round(q.x - dx * i), Math.round(q.y - dy * i), 1, 1); }
  };
  o.draw = () => {};
  return o;
};

// ================================================================== PUZZLE PARTS
// strike/interact helpers shared by every strikable part
function kitStrikable(o, box, fn, prompt) {
  o.hurtbox = () => (o.canHit ? o.canHit() : true) ? box() : null;
  o.onHit = info => { if (o.hitT > 0) return; o.hitT = 0.25; fn(info); };
  o.interact = () => { if (o.hitT > 0 || (o.canHit && !o.canHit())) return; o.hitT = 0.25; fn({ kind: 'interact' }); };
  o.prompt = () => (o.canHit ? o.canHit() : true) ? (typeof prompt === 'function' ? prompt() : prompt) : null;
}
// a timer on a source: reverts after `timer` s, ticking, with a countdown ring over it
function kitTimerTick(o, dt) {
  if (!o.spec.timer || !o.active || o.timerT === undefined) return;
  const was = o.timerT; o.timerT -= dt;
  const step = o.timerT < 1.5 ? 0.25 : 0.5;
  if (Math.floor(was / step) !== Math.floor(o.timerT / step) && kitNear(o.x, o.y, 400)) kitSfx.tick(o.timerT < 1.5);
  if (o.timerT <= 0) { o.timerT = undefined; o.flip(false, true); }
}
function kitDrawTimer(o, x, y) {
  if (!o.spec.timer || !o.active || o.timerT === undefined) return;
  const n = 8, k = o.timerT / o.spec.timer;
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + i / n * Math.PI * 2, lit = i < Math.ceil(k * n);
    g.fillStyle = lit ? (k < 0.3 && Math.floor(time * 8) % 2 ? '#ff6040' : `rgb(${o.pal.glow})`) : 'rgba(40,36,44,0.8)';
    g.fillRect(Math.round(x + Math.cos(a) * 5) - 1, Math.round(y + Math.sin(a) * 5) - 1, 2, 2);
  }
}
function kitSourceInit(o, s, persistDefault) {
  o.src = true; o.x = s.x * TILE + 8; o.y = (s.y + 1) * TILE; o.hitT = 0;
  o.persistKey = o.id && (s.persist ?? persistDefault) && !s.timer ? kitKey(o.id) : null;
  o.start = !!s.on;
  o.active = o.persistKey && SAVE.flags[o.persistKey] !== undefined ? !!SAVE.flags[o.persistKey] : o.start;
  o.puzzle = true;
  o.reset = all => { if (!all) return; o.timerT = undefined; kitSetActive(o, o.start, true); };
}
// ---- lever: strike or interact flips it (and toggles its targets). timer:s reverts. once:true = can't be flipped back.
KIT_KINDS.lever = s => {
  const o = kitObj('lever', s); kitSourceInit(o, s, !s.timer);
  o.flip = (v, auto) => {
    kitSetActive(o, v); o.swing = 1;
    if (v && s.timer) o.timerT = s.timer;
    if (!auto) { kitSfx.clunk(); shake = Math.max(shake, 2); } else kitSfx.click();
    if (!auto && s.msg) toast(s.msg, 2.5);
  };
  o.canHit = () => !(s.once && o.active);
  kitStrikable(o, () => rect(o.x - 7, o.y - 22, o.x + 7, o.y), () => {
    if (s.timer && o.active) { o.timerT = s.timer; kitSfx.clunk(); return; }   // re-arms a running timer
    o.flip(!o.active, false);
  }, 'Pull');
  o.tick = dt => { o.hitT -= dt; o.swing = Math.max(0, (o.swing || 0) - dt * 4); kitTimerTick(o, dt); };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'lever_' + o.skin;
    if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg) + (o.active ? 1 : 0), o.x, o.y, s.face || 1, { bottom: true });
    else { g.fillStyle = o.pal.k; g.fillRect(o.x - 6, o.y - 5, 12, 5); g.save(); g.translate(o.x, o.y - 4); g.rotate(o.active ? 0.6 : -0.6); g.fillStyle = o.pal.l; g.fillRect(-1, -14, 2, 14); g.fillStyle = o.pal.acc; g.fillRect(-2, -16, 4, 3); g.restore(); }
    kitDrawTimer(o, o.x, o.y - 30);
  };
  return o;
};
// ---- switch: a button that stays down once pressed (strike / interact). timer:s pops it back up.
KIT_KINDS.switch = s => {
  const o = kitObj('switch', s); kitSourceInit(o, s, !s.timer);
  o.flip = (v, auto) => { kitSetActive(o, v); if (v && s.timer) o.timerT = s.timer; if (!auto) { kitSfx.click(); kitSfx.clunk(); } else kitSfx.click(); if (!auto && s.msg) toast(s.msg, 2.5); };
  o.canHit = () => !o.active || !!s.timer;
  kitStrikable(o, () => rect(o.x - 7, o.y - 14, o.x + 7, o.y), () => { if (o.active && s.timer) { o.timerT = s.timer; kitSfx.click(); } else if (!o.active) o.flip(true, false); }, 'Press');
  o.tick = dt => { o.hitT -= dt; kitTimerTick(o, dt); };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'switch_' + o.skin;
    if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg) + (o.active ? 1 : 0), o.x, o.y, 1, { bottom: true });
    else { g.fillStyle = o.pal.k; g.fillRect(o.x - 6, o.y - 12, 12, 12); g.fillStyle = o.active ? o.pal.acc : o.pal.l; g.fillRect(o.x - 3, o.y - (o.active ? 7 : 10), 6, 3); }
    if (o.active) addLight(o.x, o.y - 8, 18, o.pal.glow, 0.4);
    kitDrawTimer(o, o.x, o.y - 22);
  };
  return o;
};
// ---- plate: active while the player, a crate or an enemy stands on it. w tiles. latch:true stays down. timer:s holds
// it down that long after you step off (ticking).
KIT_KINDS.plate = s => {
  const o = kitObj('plate', s); kitSourceInit(o, s, !!s.latch);
  const w = (s.w ?? 1) * TILE, x0 = s.x * TILE;
  o.x = x0 + w / 2; o.pw = w;
  o.flip = (v, auto) => { kitSetActive(o, v); if (kitNear(o.x, o.y)) (v ? kitSfx.clunk : kitSfx.click)(); };
  o.tick = dt => {
    const r = rect(x0 + 1, o.y - 3, x0 + w - 1, o.y + 1);
    const pressed = kitBodies().some(b => b.ground && overlap(kitHB(b), r));
    if (pressed) { if (!o.active) o.flip(true); if (s.timer) o.timerT = s.timer; }
    else if (o.active && !s.latch) { if (s.timer) kitTimerTick(o, dt); else o.flip(false); }
    o.down = approach(o.down || 0, o.active ? 1 : 0, dt * 10);
  };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'plate_' + o.skin;
    for (let i = 0; i < w / TILE; i++) {
      if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg) + (o.down > 0.5 ? 1 : 0), x0 + i * TILE + 8, o.y, 1, { bottom: true });
      else { g.fillStyle = o.pal.k; g.fillRect(x0 + i * TILE + 1, o.y - 3 + Math.round(o.down * 2), 14, 3); g.fillStyle = o.active ? o.pal.acc : o.pal.l; g.fillRect(x0 + i * TILE + 2, o.y - 3 + Math.round(o.down * 2), 12, 1); }
    }
    if (o.active) addLight(o.x, o.y - 3, 20, o.pal.glow, 0.35);
    kitDrawTimer(o, o.x, o.y - 14);
  };
  return o;
};
// ---- gate: a barrier in one column from the floor (x,y = its bottom cell) up to the ceiling (h auto-fills to the first
// solid tile above, so it can't be jumped). open:true starts open. persist:true keeps it open for good once opened.
KIT_KINDS.gate = s => {
  const o = kitObj('gate', s);
  const cx = s.x * TILE + 8, bot = (s.y + 1) * TILE;
  let h = s.h;
  if (!h) { h = 1; while (h < 24 && s.y - h >= 0 && !isSolidT(tileAt(s.x, s.y - h))) h++; if (s.y - h < 0 || h >= 24) console.warn(`kit gate ${o.id} in ${room.id}: no ceiling above (x ${s.x}, y ${s.y})`); }
  else if (!isSolidT(tileAt(s.x, s.y - h))) console.warn(`kit gate ${o.id} in ${room.id}: h=${h} doesn't reach the ceiling — it can be jumped`);
  const top = bot - h * TILE;
  o.x = cx; o.y = bot; o.top = top; o.h = h;
  o.persistKey = o.id && s.persist ? kitKey(o.id) : null;
  o.on = kitDerive(o, !!s.open) || !!(o.persistKey && SAVE.flags[o.persistKey]);
  o.k = o.on ? 1 : 0;   // 0 closed … 1 open
  const neon = o.skin === 'neon';
  o.d = { x0: s.x * TILE + 3, x1: s.x * TILE + 13, y0: top, y1: bot, kit: o, on: () => neon ? o.k < 0.5 : o.d.y1 - o.d.y0 > 2 };
  room.dyn.push(o.d);
  o.sync = () => { o.d.y1 = neon ? bot : Math.round(bot - (bot - top - 4) * o.k); };
  o.sync();
  o.tick = dt => {
    let want = kitDerive(o, !!s.open);
    if (o.persistKey && SAVE.flags[o.persistKey]) want = true;
    if (want && o.persistKey && !SAVE.flags[o.persistKey] && o.k > 0.95) { SAVE.flags[o.persistKey] = 1; saveGame(); }
    if (want !== o.on) { o.on = want; kitChanged(o, want); if (kitNear(o.x, o.y, 360)) sfx.gate(); if (want && s.msg) toast(s.msg, 2.5); }
    const nk = approach(o.k, o.on ? 1 : 0, dt * (neon ? 5 : o.on ? 1.3 : 2.2));
    if (nk < o.k) {   // closing: never onto the player — shove them out the side they're on
      const ny1 = neon ? bot : Math.round(bot - (bot - top - 4) * nk), hb = playerHurtbox(), r = rect(o.d.x0, top, o.d.x1, ny1);
      if (overlap(hb, r)) {
        const dir = P.x < cx ? -1 : 1;
        for (const d of [dir, -dir]) { const nx = d < 0 ? o.d.x0 - P.w / 2 - 0.02 : o.d.x1 + P.w / 2 + 0.02; if (kitFree(P, nx, P.y, o)) { P.x = nx; break; } }
      }
      for (const e of enemies) if (e.alive && overlap(e.hurtbox ? e.hurtbox() || kitHB(e) : kitHB(e), r)) e.x = e.x < cx ? o.d.x0 - e.w / 2 - 0.1 : o.d.x1 + e.w / 2 + 0.1;
    }
    if (nk !== o.k && Math.random() < 0.3 && !neon) particles.push({ x: cx + rand(-6, 6), y: o.d.y1, vx: rand(-20, 20), vy: -rand(5, 30), life: 0.4, kind: 'dust' });
    o.k = nk; o.sync();
    if (neon && o.k < 0.95) addLight(cx, (top + bot) / 2, 40, o.pal.glow, 0.6 * (1 - o.k));
  };
  o.draw = () => kitDrawGate(o, cx, top, bot);
  o.reset = all => { if (!all) return; o.on = kitDerive(o, !!s.open) || !!(o.persistKey && SAVE.flags[o.persistKey]); o.k = o.on ? 1 : 0; o.sync(); };
  o.puzzle = true;
  return o;
};
function kitDrawGate(o, cx, top, bot) {
  const sh = sheet('kit_gate'), X = cx - 8;
  if (o.skin === 'neon') {   // laser gate: beams fade out instead of sliding
    const a = 1 - o.k; if (a <= 0.02) { if (sh.ok && sh.has('cap_neon')) { drawSprite(sh, sh.first('cap_neon'), cx, top + 16, 1, { bottom: true }); drawSprite(sh, sh.first('foot_neon'), cx, bot, 1, { bottom: true }); } return; }
    if (sh.ok && sh.has('cap_neon')) { drawSprite(sh, sh.first('cap_neon'), cx, top + 16, 1, { bottom: true }); drawSprite(sh, sh.first('foot_neon'), cx, bot, 1, { bottom: true }); }
    for (const bx of [X + 4, X + 8, X + 11]) {
      for (let y = top + 6; y < bot - 4; y++) { const fl = (y + Math.floor(time * 60) + bx) % 11 === 0; g.fillStyle = `rgba(${fl ? '220,255,255' : '60,240,255'},${a * (fl ? 1 : 0.85)})`; g.fillRect(bx, y, 1, 1); }
      g.fillStyle = `rgba(60,240,255,${0.18 * a})`; g.fillRect(bx - 1, top + 6, 3, bot - top - 10);
    }
    return;
  }
  const y1 = o.d.y1;
  if (sh.ok && sh.has('bar_' + o.skin)) {
    const bar = sh.frames[sh.first('bar_' + o.skin)], foot = sh.frames[sh.first('foot_' + o.skin)];
    // bars: tile upward from the moving bottom edge, clipped under the cap
    g.save(); g.beginPath(); g.rect(X, top, 16, bot - top); g.clip();
    for (let y = y1 - 16; y > top - 16; y -= 16) g.drawImage(sh.img, bar.x, bar.y, 16, 16, X, Math.round(y), 16, 16);
    g.drawImage(sh.img, foot.x, foot.y, 16, 16, X, Math.round(y1 - 16), 16, 16);
    g.restore();
    drawSprite(sh, sh.first('cap_' + o.skin), cx, top + 16, 1, { bottom: true });
    return;
  }
  const p = o.pal;
  for (const bx of [X + 3, X + 7, X + 11]) { g.fillStyle = p.k; g.fillRect(bx - 1, top, 3, y1 - top); g.fillStyle = p.l; g.fillRect(bx, top, 1, y1 - top); }
  g.fillStyle = p.k; g.fillRect(X + 1, top, 14, 5); g.fillStyle = p.m; g.fillRect(X + 2, top + 1, 12, 3);
}
// ---- seq: an ordered puzzle. group:'g' gathers every member (bell/lantern/glyph/stop/frame/brazier) with that group;
// order:[ids] is the answer. A wrong strike resets (dissonant sound); the full order toggles targets + chimes. persist
// (default true) keeps it solved.
KIT_KINDS.seq = s => {
  const o = kitObj('seq', s); kitSourceInit(o, s, true);
  o.order = s.order || []; o.prog = 0; o.bad = 0;
  o.members = () => KIT.objs.filter(q => q.member && q.spec.group === s.group);
  o.hit = m => {
    if (o.active) return;
    if (m.id && m.id === o.order[o.prog]) {
      o.prog++; m.lit = true; m.flash = 1;
      if (o.prog >= o.order.length) { kitSetActive(o, true); setTimeout(() => { kitSfx.chime(); flashScreen = Math.max(flashScreen, 0.15); if (s.msg) toast(s.msg, 3); }, 250); for (const q of o.members()) q.lit = true; }
    } else {
      o.prog = 0; o.bad = 0.8; setTimeout(kitSfx.wrong, 180); m.wrongT = 0.8;
      for (const q of o.members()) q.lit = false;
    }
  };
  o.reset = all => { if (!all) return; o.prog = 0; kitSetActive(o, o.start, true); for (const q of o.members()) q.lit = q.startLit || false; };
  o.tick = dt => { o.bad = Math.max(0, o.bad - dt); };
  o.draw = () => {};
  return o;
};
// members: struck in a seq's group, or standalone sources (targets). note: pitch 0..9 for bells/stops.
function kitMember(kind, s, box, drawFn, prompt) {
  const o = kitObj(kind, s); kitSourceInit(o, s, false);
  o.member = true; o.lit = false; o.flash = 0; o.wrongT = 0; o.note = s.note ?? 0;
  o.seq = () => KIT.objs.find(q => q.kind === 'seq' && q.spec.group && q.spec.group === s.group);
  o.strike = info => {
    o.flash = 1; o.ring = 1;
    if (kind === 'bell' || kind === 'stop') kitSfx.note(o.note, kind); else if (kind === 'glyph' || kind === 'frame') kitSfx.note(o.note, 'glass');
    const q = o.seq();
    if (q) { if (q.active) return; q.hit(o); if (kind === 'lantern' || kind === 'brazier') { if (o.lit) sfx.fire(); } return; }
    if (kind === 'brazier' || kind === 'lantern') {
      const light = info && (info.fire || info.kind === 'spell') ? true : !o.active;
      if (light !== o.active) { kitSetActive(o, light); o.lit = light; if (light) sfx.fire(); else noise(0.3, 500, 0.6, 0.15, 'lowpass', 0.5); }
    } else if (o.targets.length || s.id) { kitSetActive(o, !o.active); o.lit = o.active; }
  };
  kitStrikable(o, () => box(o), o.strike, prompt);
  o.tick = dt => {
    o.hitT -= dt; o.flash = Math.max(0, o.flash - dt * 2); o.ring = Math.max(0, (o.ring || 0) - dt * 0.8); o.wrongT = Math.max(0, o.wrongT - dt);
    if (!o.seq()) o.lit = o.active;
  };
  o.draw = () => drawFn(o);
  return o;
}
const kitLitK = o => o.lit ? 1 : o.flash * 0.8;
function kitDrawMember(o, tag, frameLit, x, y, opt = {}) {
  const sh = sheet('kit_parts'); if (!sh.ok || !sh.has(tag)) return false;
  const f = sh.first(tag) + (o.lit && frameLit !== null ? frameLit : 0);
  drawSprite(sh, f, x, y, 1, { ...opt, flash: o.wrongT > 0 ? o.wrongT * 0.7 : o.flash * 0.35, flashColor: o.wrongT > 0 ? '#ff3030' : '#fff2c0' });
  return true;
}
KIT_KINDS.bell = s => kitMember('bell', s, o => rect(o.x - 8, s.y * TILE, o.x + 8, s.y * TILE + 22), o => {
  // bell hangs from its cell's top; a cord runs up to the ceiling
  const bx = o.x, by = s.y * TILE; let top = by; while (top > 0 && !solidAtPx(bx, top - 1)) top -= 4;
  g.fillStyle = '#2a2622'; g.fillRect(Math.round(bx), top, 1, by - top + 2);
  const ang = Math.sin(time * 9) * 0.22 * o.ring;
  const sh = sheet('kit_parts');
  if (sh.ok && sh.has('bell')) drawSprite(sh, sh.first('bell') + (o.lit ? 1 : 0), bx, by + 2, 1, { pivot: [16, 2], rot: ang, flash: o.wrongT > 0 ? o.wrongT * 0.7 : o.flash * 0.4, flashColor: o.wrongT > 0 ? '#ff3030' : '#fff2c0' });
  else { g.fillStyle = '#9a7a3a'; g.fillRect(bx - 6, by + 2, 12, 12); }
  if (kitLitK(o) > 0) addLight(bx, by + 10, 34, '255,210,140', 0.5 * kitLitK(o));
}, 'Ring');
KIT_KINDS.lantern = s => { const o = kitMember('lantern', s, o => rect(o.x - 6, o.y - 22, o.x + 6, o.y), o => {
  if (!kitDrawMember(o, 'lantern', 1, o.x, o.y, { bottom: true })) { g.fillStyle = o.lit ? '#ffc070' : '#3a3440'; g.fillRect(o.x - 3, o.y - 16, 6, 10); }
  if (o.lit) { addLight(o.x, o.y - 12, 60 + Math.sin(time * 9 + o.x) * 2, '255,180,100', 0.9, { flicker: true }); if (Math.random() < 0.05) particles.push({ x: o.x + rand(-2, 2), y: o.y - 18, vx: 0, vy: -rand(8, 18), life: 0.5, kind: 'fire' }); }
}, () => o.lit ? null : 'Light'); o.lit = o.active = !!s.on; o.startLit = !!s.on; return o; };
KIT_KINDS.glyph = s => kitMember('glyph', s, o => rect(o.x - 8, s.y * TILE, o.x + 8, s.y * TILE + 16), o => {
  const cy = s.y * TILE + 8, sh = sheet('kit_parts');
  if (sh.ok && sh.has('glyph')) {
    drawSprite(sh, sh.first('glyph') + ((s.sym ?? 0) % 8), o.x, cy, 1, { center: true, flash: o.wrongT > 0 ? o.wrongT * 0.7 : 0, flashColor: '#ff3030' });
    const k = kitLitK(o);
    if (k > 0 && sh.has('glyph_lit')) drawSprite(sh, sh.first('glyph_lit') + ((s.sym ?? 0) % 8), o.x, cy, 1, { center: true, alpha: k });
  } else { g.fillStyle = '#3a3642'; g.fillRect(o.x - 6, cy - 7, 12, 14); g.fillStyle = o.lit ? '#9ad0ff' : '#6a6478'; g.fillRect(o.x - 1, cy - 4, 2, 8); }
  if (kitLitK(o) > 0) addLight(o.x, cy, 26, o.pal.glow === '255,140,60' ? '255,170,90' : '150,200,255', 0.6 * kitLitK(o));
}, 'Touch');
KIT_KINDS.stop = s => kitMember('stop', s, o => rect(o.x - 8, s.y * TILE, o.x + 8, s.y * TILE + 16), o => {
  const cy = s.y * TILE + 8;
  if (!kitDrawMember(o, 'stop', 1, o.x, cy, { center: true })) { g.fillStyle = '#2a2024'; g.fillRect(o.x - 5, cy - 5, 10, 10); g.fillStyle = o.lit ? '#e0c070' : '#8a7050'; g.fillRect(o.x - 3, cy - 3, 6, 6); }
  if (kitLitK(o) > 0) addLight(o.x, cy, 20, '255,210,140', 0.45 * kitLitK(o));
}, 'Pull');
KIT_KINDS.frame = s => kitMember('frame', s, o => rect(o.x - 10, s.y * TILE - 8, o.x + 10, s.y * TILE + 16), o => {
  const cy = s.y * TILE + 4;
  if (!kitDrawMember(o, 'frame', 1, o.x, cy, { center: true })) { g.fillStyle = '#5a4020'; g.fillRect(o.x - 10, cy - 12, 20, 24); g.fillStyle = '#1a1418'; g.fillRect(o.x - 8, cy - 10, 16, 20); }
  if (kitLitK(o) > 0) addLight(o.x, cy - 3, 22, '255,80,80', 0.5 * kitLitK(o));
}, 'Touch');
KIT_KINDS.brazier = s => { const o = kitMember('brazier', s, o => rect(o.x - 8, o.y - 22, o.x + 8, o.y), o => {
  const sh = sheet('kit_parts'), tg = 'brazier_' + o.skin;
  if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg) + (o.lit ? 1 + Math.floor(time * 10 + o.x) % 3 : 0), o.x, o.y, 1, { bottom: true, flash: o.wrongT > 0 ? o.wrongT * 0.7 : 0, flashColor: '#ff3030' });
  else { g.fillStyle = o.pal.k; g.fillRect(o.x - 6, o.y - 12, 12, 12); if (o.lit) { g.fillStyle = '#ffb040'; g.fillRect(o.x - 3, o.y - 18, 6, 6); } }
  if (o.lit) {
    const neon = o.skin === 'neon';
    addLight(o.x, o.y - 20, 64 + Math.sin(time * 7 + o.x) * 3, neon ? '60,240,255' : o.skin === 'crystal' ? '150,200,255' : '255,160,70', 0.95, { flicker: true });
    if (Math.random() < 0.3) particles.push({ x: o.x + rand(-4, 4), y: o.y - 22, vx: rand(-4, 4), vy: -rand(14, 30), life: rand(0.4, 0.8), kind: neon ? 'teal' : 'fire' });
  }
}, () => o.lit ? 'Douse' : 'Light'); o.lit = o.active = s.lit !== undefined ? !!s.lit : !!s.on; o.start = o.active; o.startLit = o.active; return o; };

// ---- beam + mirror + socket: a light beam from `beam` (dir: right|left|up|down|ur|ul|dr|dl) travels cell to cell;
// mirrors (rot 0..3 = — \ | /) rotate 45° per strike and reflect it; a socket it reaches lights and toggles its targets.
const KIT_DIRS = { right: 0, dr: 1, down: 2, dl: 3, left: 4, ul: 5, up: 6, ur: 7 };
const KIT_DV = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]];
KIT_KINDS.beam = s => {
  const o = kitObj('beam', s);
  o.tx = s.x; o.ty = s.y; o.x = s.x * TILE + 8; o.y = s.y * TILE + 8; o.dir = KIT_DIRS[s.dir] ?? (typeof s.dir === 'number' ? s.dir : 0);
  o.style = s.style || (o.skin === 'neon' ? 'neon' : o.skin === 'crystal' ? 'star' : 'sun');
  o.col = { sun: ['255,220,140', '255,250,220'], star: ['150,200,255', '235,245,255'], neon: ['60,240,255', '220,255,255'] }[o.style];
  o.path = [];
  o.tick = dt => { o.on = kitDerive(o, !kitTrig(o)); o.path = o.on ? kitTrace(o) : []; };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'emitter_' + o.style;
    if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg), o.x, o.y, 1, { pivot: [16, 16], rot: o.dir * Math.PI / 4 });
    else { g.fillStyle = '#2a2430'; g.fillRect(o.x - 6, o.y - 6, 12, 12); g.fillStyle = `rgb(${o.col[0]})`; g.fillRect(o.x - 2, o.y - 2, 4, 4); }
  };
  o.fx = () => kitDrawBeam(o);
  return o;
};
function kitTrace(o) {
  const cells = new Map();
  for (const q of KIT.objs) if (q.kind === 'mirror' || q.kind === 'socket' || (q.kind === 'beam' && q !== o)) cells.set(q.tx + ',' + q.ty, q);
  for (const q of KIT.objs) if (q.kind === 'crate' && q.body) cells.set(Math.floor(q.body.x / TILE) + ',' + Math.floor((q.body.y - 8) / TILE), q);
  const pts = [[o.x, o.y]], seen = new Set(); let x = o.tx, y = o.ty, d = o.dir;
  for (let i = 0; i < 80; i++) {
    const [dx, dy] = KIT_DV[d], nx = x + dx, ny = y + dy;
    const blocked = solidAtPx(nx * TILE + 8, ny * TILE + 8) || (dx && dy && solidAtPx((x + dx) * TILE + 8, y * TILE + 8) && solidAtPx(x * TILE + 8, (y + dy) * TILE + 8));
    if (blocked || nx < -1 || ny < -1 || nx > room.w || ny > room.h) { pts.push([x * TILE + 8 + dx * 8, y * TILE + 8 + dy * 8]); break; }
    x = nx; y = ny;
    const q = cells.get(x + ',' + y);
    if (!q) continue;
    pts.push([x * TILE + 8, y * TILE + 8]);
    if (q.kind === 'socket') { q.hitBy = o; break; }
    if (q.kind !== 'mirror') break;
    const k = x + ',' + y + ',' + d; if (seen.has(k)) break; seen.add(k);
    // reflect: direction angle a (45° steps) off a mirror line at θ = rot·45°: a' = 2θ − a
    d = (((2 * q.rot - d) % 8) + 8) % 8; q.litT = 0.1;
  }
  return pts;
}
function kitDrawBeam(o) {
  if (o.path.length < 2) return;
  const draw = () => {
    for (let i = 0; i < o.path.length - 1; i++) {
      const [x0, y0] = o.path[i], [x1, y1] = o.path[i + 1], n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0))), nx = -(y1 - y0) / n, ny = (x1 - x0) / n;
      for (let k = 0; k <= n; k++) {
        const x = Math.round(lerp(x0, x1, k / n)), y = Math.round(lerp(y0, y1, k / n)), sh = Math.sin(time * 14 - k * 0.35 - i);
        g.fillStyle = `rgba(${o.col[0]},${0.22 + 0.08 * sh})`; g.fillRect(Math.round(x + nx * 2), Math.round(y + ny * 2), 1, 1); g.fillRect(Math.round(x - nx * 2), Math.round(y - ny * 2), 1, 1);
        g.fillStyle = `rgba(${o.col[0]},0.75)`; g.fillRect(Math.round(x + nx), Math.round(y + ny), 1, 1); g.fillRect(Math.round(x - nx), Math.round(y - ny), 1, 1);
        g.fillStyle = `rgba(${o.col[1]},${0.9 + 0.1 * sh})`; g.fillRect(x, y, 1, 1);
      }
    }
  };
  if (typeof drawGlow === 'function') drawGlow(draw); else draw();
  let acc = 0;
  for (let i = 0; i < o.path.length; i++) {
    const [x, y] = o.path[i]; if (i === 0 || i === o.path.length - 1) { addLight(x, y, 30, o.col[0], 0.8, { shadow: false }); continue; }
    addLight(x, y, 26, o.col[0], 0.6, { shadow: false });
  }
  for (let i = 0; i < o.path.length - 1; i++) {   // soft fill light along long runs
    const [x0, y0] = o.path[i], [x1, y1] = o.path[i + 1], L = Math.hypot(x1 - x0, y1 - y0);
    for (let d = 48 - acc; d < L; d += 64) addLight(lerp(x0, x1, d / L), lerp(y0, y1, d / L), 34, o.col[0], 0.35, { shadow: false });
    acc = (acc + L) % 64;
  }
}
KIT_KINDS.mirror = s => {
  const o = kitObj('mirror', s);
  o.tx = s.x; o.ty = s.y; o.x = s.x * TILE + 8; o.y = (s.y + 1) * TILE; o.cy = s.y * TILE + 8; o.hitT = 0; o.litT = 0; o.spin = 0;
  o.style = s.style || (o.skin === 'neon' ? 'neon' : o.skin === 'crystal' ? 'star' : 'sun');
  const key = o.id && (s.persist ?? true) ? `${room.id}:${o.id}` : null;
  o.start = ((s.rot ?? 0) % 4 + 4) % 4;
  o.rot = key && kitStore()[key] !== undefined ? kitStore()[key] : o.start;
  o.puzzle = true;
  o.reset = all => { if (all) { o.rot = o.start; if (key) delete kitStore()[key]; } };
  o.canHit = () => !s.fixed;
  kitStrikable(o, () => rect(o.x - 8, o.cy - 8, o.x + 8, o.cy + 8), () => { o.rot = (o.rot + 1) % 4; o.spin = 1; kitSfx.turn(); if (key) kitStore()[key] = o.rot; }, 'Turn');
  o.tick = dt => { o.hitT -= dt; o.litT -= dt; o.spin = Math.max(0, o.spin - dt * 6); };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'mirror_' + o.style, ang = -o.spin * Math.PI / 4;
    if (sh.ok && sh.has(tg)) drawSprite(sh, sh.first(tg) + o.rot, o.x, o.cy, 1, { pivot: [16, 16], rot: ang });
    else { g.save(); g.translate(o.x, o.cy); g.rotate(o.rot * Math.PI / 4 + ang); g.fillStyle = '#c0c8d8'; g.fillRect(-7, -1, 14, 2); g.restore(); }
    if (o.litT > 0) addLight(o.x, o.cy, 18, '255,240,200', 0.4);
  };
  return o;
};
KIT_KINDS.socket = s => {
  const o = kitObj('socket', s); kitSourceInit(o, s, true);
  o.tx = s.x; o.ty = s.y; o.cy = s.y * TILE + 8; o.hitBy = null; o.gk = o.active ? 1 : 0;
  o.style = s.style || (o.skin === 'neon' ? 'neon' : o.skin === 'crystal' ? 'star' : 'sun');
  o.tick = dt => {
    const lit = !!o.hitBy; o.hitBy = null;   // beams trace before sockets read (kitUpdate order)
    if (lit && !o.active) { kitSetActive(o, true); kitSfx.hum(); setTimeout(kitSfx.chime, 200); if (s.msg) toast(s.msg, 3); }
    else if (!lit && o.active && !o.persistKey) kitSetActive(o, false);
    o.gk = approach(o.gk, o.active ? 1 : lit ? 0.6 : 0, dt * 3);
    if (o.gk > 0) addLight(o.x, o.cy, 40, o.style === 'neon' ? '60,240,255' : o.style === 'star' ? '150,200,255' : '255,220,140', 0.8 * o.gk);
  };
  o.draw = () => {
    const sh = sheet('kit_parts'), tg = 'socket_' + o.style;
    if (sh.ok && sh.has(tg)) { drawSprite(sh, sh.first(tg), o.x, o.cy, 1, { center: true }); if (o.gk > 0) drawSprite(sh, sh.first(tg) + 1, o.x, o.cy, 1, { center: true, alpha: o.gk }); }
    else { g.fillStyle = '#2a2430'; g.fillRect(o.x - 7, o.cy - 7, 14, 14); g.fillStyle = `rgba(255,220,140,${0.3 + 0.7 * o.gk})`; g.fillRect(o.x - 3, o.cy - 3, 6, 6); }
  };
  return o;
};
// ---- level: a fluid (water|poison|slag|lava|sand|data) in the area x,y,w,h (tiles), its surface on one of `states`
// (absolute rows). The state index = start + the number of active sources targeting its id (so two valves give 0/1/2).
// water writes the Barrows deep-water tile (swim with Tidebreath), poison the rot-water tile '~' (rot); slag, lava, sand
// and data hurt on touch. Only open cells ('.') in the area fill: leave the basin empty in the map.
KIT_KINDS.level = s => {
  const o = kitObj('level', s);
  const F = KIT_FLUID[s.fluid || 'water'] || KIT_FLUID.water, states = s.states && s.states.length ? s.states : [s.y], spd = (s.speed ?? 1.5) * TILE;
  const ax = s.x, aw = s.w ?? 4, ay = s.h ? s.y : Math.min(...states), ah = s.h ?? (room.h - ay);
  const x0 = ax * TILE, x1 = (ax + aw) * TILE;
  const tileId = s.fluid === 'poison' ? T_WATER : (s.fluid || 'water') === 'water' ? (typeof DB_T_WATER !== 'undefined' ? DB_T_WATER : T_WATER) : null;
  o.F = F; o.x = (x0 + x1) / 2; o.x0 = x0; o.x1 = x1; o.bottom = (ay + ah) * TILE;
  const cells = [];   // the open cells we may flood (and what they were)
  for (let ty = Math.max(0, ay); ty < Math.min(room.h, ay + ah); ty++) for (let tx = Math.max(0, ax); tx < Math.min(room.w, ax + aw); tx++) {
    const t = room.grid[ty * room.w + tx]; if (t === T_EMPTY || t === T_PLAT) cells.push([tx, ty, t]);
  }
  const idxNow = () => clamp((s.start ?? 0) + (o.id ? (KIT.force[o.id] !== undefined ? (KIT.force[o.id] ? 1 : 0) : KIT.cnt[o.id] || 0) : 0), 0, states.length - 1);
  o.write = () => { if (tileId !== null) for (const [tx, ty, t0] of cells) room.grid[ty * room.w + tx] = (ty * TILE + 8 >= o.sy && t0 === T_EMPTY) ? tileId : t0; };
  o.init = () => { kitTally(); o.idx = idxNow(); o.sy = states[o.idx] * TILE; o.y = o.sy; o.write(); };
  o.init();
  o.tick = dt => {
    const i = idxNow();
    if (i !== o.idx) { o.idx = i; if (kitNear(o.x, o.sy, 400)) { noise(1.4, 260, 0.6, 0.25, 'lowpass', 0.6); tone(60, 1.2, 0.1, 'sine', 1.1); } kitChanged(o, i); }
    const ty = states[o.idx] * TILE;
    if (Math.abs(ty - o.sy) > 0.01) {
      const was = Math.round((o.sy - 8) / TILE); o.sy = approach(o.sy, ty, spd * dt);
      if (Math.round((o.sy - 8) / TILE) !== was) o.write();
      if (Math.random() < 0.3) particles.push({ x: rand(x0, x1), y: o.sy, vx: 0, vy: -rand(5, 20), life: 0.5, kind: F.fire ? 'ember' : s.fluid === 'poison' ? 'spore' : 'frost' });
    }
    o.y = o.sy;
    if (tileId === null && P.state !== 'dead' && P.inv <= 0 && P.y - 6 > o.sy && P.y - 6 < o.bottom && P.x > x0 && P.x < x1) kitFluidHurt(F, o, () => kitLevelSafe(o));
    const lk = F.fire ? 0.85 : 0.3;
    for (let x = Math.max(x0, cam.x - 20) + 16; x < Math.min(x1, cam.x + W + 20); x += 48) addLight(x, o.sy + 4, F.fire ? 56 : 40, F.light, lk);
  };
  o.fluid = () => ({ x0, x1, y: o.sy, y1: o.bottom, F, mask: true });
  o.puzzle = true;
  o.reset = all => { if (all) o.init(); };
  return o;
};
function kitLevelSafe(o) { const s = KIT.safe || P.safe; return s.y - 6 > o.sy && s.x > o.x0 && s.x < o.x1 ? (typeof spNearestGround === 'function' && spNearestGround(P.x, o.sy - 20)) || s : s; }

// ---- label: a debug caption (test rooms only; drawn over the world in screen space)
KIT_KINDS.label = s => { const o = kitObj('label', s); o.x = s.x * TILE; o.y = s.y * TILE; o.text = s.text || ''; o.draw = kitNoop; return o; };
HOOKS.hud.push(() => {
  if (KIT.roomObj !== room || !room.def.test || state !== 'play') return;
  for (const o of KIT.objs) if (o.kind === 'label') { const x = o.x - cam.x, y = o.y - cam.y; if (x > -80 && x < W + 10 && y > -10 && y < H + 10) text(o.text, x, y + 8, 5.5, '#f0e2b8', 'left', { weight: 600 }); }
});

// ================================================================== dispatch + frame loop
SPAWNS.kit = (s, c) => {
  kitEnsure();
  const f = KIT_KINDS[s.kind];
  if (!f) { console.warn(`kit: unknown kind '${s.kind}' in ${c.id}`); return; }
  const o = f(s, c);
  if (o) { o.update = kitNoop; o.draw = o.draw || kitNoop; props.push(o); }   // props' own update would run it twice: the kit ticks from its hook
};
function kitUpdate(dt) {
  KIT.t += dt;
  kitTally();
  // order matters: sources settle, beams trace (sockets read them), then everything that moves carries its riders
  const order = ['lever', 'switch', 'plate', 'seq', 'bell', 'lantern', 'glyph', 'stop', 'frame', 'brazier', 'mirror', 'beam', 'socket', 'gate', 'level', 'wind',
                 'mover', 'lift', 'sinker', 'crumble', 'phase', 'spring', 'crate', 'swing', 'pendulum', 'rising'];
  KIT.rideO = null;
  for (const k of order) for (const o of KIT.objs) if (o.kind === k && o.tick) o.tick(dt);
  // momentum: jumping off a moving slab keeps a little of its sideways speed
  if (KIT.rideO && KIT.rideV) KIT.lastRide = { vx: KIT.rideV, t: 0 };
  else if (KIT.lastRide) {
    const L = KIT.lastRide;
    if (P.ground || P.state === 'hook' || P.state === 'wall' || L.t > 0.4) KIT.lastRide = null;
    else { L.t += dt; P.pushVx = (P.pushVx || 0) + L.vx * (1 - L.t / 0.4); }
  }
  // spring launch: the variable-jump cut (jump released → rise eased to -90) must not eat a bounce; keep the ballistic arc
  if (KIT.boost) {
    const B = KIT.boost;
    if (P.state !== 'air' || P.hitCeil || P.ground) KIT.boost = null;
    else {
      if (B.y !== undefined) { const want = B.y + B.vy * dt; if (P.y > want + 0.01 && kitFree(P, P.x, want, null)) P.y = want; }   // undo the cut's lost rise
      B.vy += GRAV_UP * dt;
      if (B.vy >= -90) KIT.boost = null; else { P.vy = B.vy; B.y = P.y; }
    }
  }
  // never remember a moving / vanishing slab as the spot to respawn at after spikes
  let onKit = false;
  if (P.ground) for (const o of KIT.objs) if (o.d && o.kind !== 'gate' && kitStands(P, o.d)) { onKit = true; break; }
  if (onKit) { if (KIT.safe) P.safe = { ...KIT.safe }; }
  else if (P.ground && P.state !== 'hurt') KIT.safe = { ...P.safe };
}
HOOKS.update.push(dt => { if (KIT.roomObj !== room || !KIT.objs.length) return; kitUpdate(dt); });
HOOKS.enter.push(def => {
  kitEnsure();
  if (!KIT.objs.length) return;
  kitTally();
  for (const o of KIT.objs) if (o.kind === 'gate') { o.on = kitDerive(o, !!o.spec.open) || !!(o.persistKey && SAVE.flags[o.persistKey]); o.k = o.on ? 1 : 0; o.sync(); }
  for (const o of KIT.objs) if (o.kind === 'seq') { if (o.active) for (const q of o.members()) q.lit = true; else for (const q of o.members()) q.lit = q.startLit || false; }
  for (const o of KIT.objs) if (o.kind === 'level') o.init();
  if (P) KIT.safe = { ...P.safe };
});
HOOKS.render.push(() => {
  if (KIT.roomObj !== room || !KIT.objs.length) return;
  for (const o of KIT.objs) if (o.fx) o.fx();
  for (const o of KIT.objs) if (o.fluid) { const f = o.fluid(); kitDrawFluid(f, time + o.x * 0.01); }
});
if (window.__game) Object.assign(window.__game, { KIT, kitReset, kitForce, kitOn });
