// ------------------------------------------------------------------ NEO-HALLOW (agent NH) — the secret otherworld
// A rain-soaked neon megacity built on the fossilised Pale Root, thousands of years later. Reached only through a
// glitching crack in reality hidden in the Root Shaft (C6, behind a breakable wall). Rooms: tools/regions/76_neohallow.py.
// Tiles: '1' data abyss (burns: respawn, or a bounce in the Null Sanctum), '2' deletable arena floor (SAINT-0).
// Mechanics: timed laser grids, hackable terminals (strike or E) toggling hard-light stairs / energy doors, a maglev car
// to ride, security drones that call reinforcements, turret nodes, the c_hack charm (scan overlay on breakable walls).
// Bosses: the Enforcer Mech (mini, NH5) and SAINT-0, the Null Saint (NH7; deletes the floor; cyberspace phase 3).
// Every top-level name is prefixed nh / NH (all region files share one scope).
Object.assign(AREAS, {
  neohallow: { name: 'NEO-HALLOW', ambient: 0.46, amb: 'nh', tint: '#05050d', map: '#b8308c' },
  neohallow_cyber: { name: 'Cyberspace', ambient: 0.02, amb: 'nh', tint: '#dfe7f0', map: '#b8308c' },
});
Object.assign(SCALES, { neohallow: [0, 3, 5, 7, 10], neohallow_cyber: [0, 2, 3, 7, 8] });
Object.assign(ROOTS, { neohallow: 55, neohallow_cyber: 49 });
Object.assign(PCOL, { nh_mote: '110,220,255', nh_pink: '255,80,200', nh_white: '240,250,255', nh_data: '90,255,210', nh_dark: '20,26,54' });

const NH_T_VOID = 66, NH_T_DEL = 67;
const NH_CY = ['#06202e', '#0b4d66', '#13a3c9', '#3fe0ff', '#b8f6ff', '#f2feff'];
const NH_MG = ['#2a0624', '#6e0f5c', '#c21d97', '#ff3fc0', '#ff9fe2', '#fff0fb'];
const NH_NV = ['#03040a', '#070913', '#0d1120', '#161c33', '#222b4a', '#34416a'];
const NH_RD = ['#3a0610', '#8a0f22', '#e0223f', '#ff6a7e', '#ffd0d8'];
const nhIn = () => !!room && (room.def.biome === 'neohallow' || room.def.biome === 'neohallow_cyber');
const nhCyber = () => !!room && room.def.biome === 'neohallow_cyber';
const nhSfx = {
  zap: (v = 1) => { noise(0.16, 5200, 1.4, 0.16 * v, 'bandpass', 0.6); tone(1320, 0.1, 0.04 * v, 'square', 0.6); },
  buzz: () => { tone(110, 0.35, 0.05, 'sawtooth', 1); tone(220, 0.3, 0.025, 'square', 1); },
  hack: () => { [880, 1175, 1568].forEach((f, i) => tone(f, 0.09, 0.05, 'square', 1, i * 0.05)); noise(0.1, 6000, 1.5, 0.08, 'highpass'); },
  unhack: () => { [1568, 1175, 880].forEach((f, i) => tone(f, 0.09, 0.04, 'square', 1, i * 0.05)); },
  door: () => { tone(330, 0.3, 0.05, 'triangle', 1.6); noise(0.3, 1800, 1, 0.08, 'bandpass', 0.5); },
  chime: () => { [659, 988].forEach((f, i) => tone(f, 0.5, 0.05, 'triangle', 1, i * 0.12)); },
  glitch: (v = 1) => { for (let i = 0; i < 4; i++) tone(rand(200, 2400), 0.05, 0.05 * v, 'square', rand(0.3, 2), i * 0.04); noise(0.3, 3000, 0.6, 0.18 * v, 'bandpass', 0.3); },
  warp: () => { tone(1760, 0.9, 0.08, 'sawtooth', 0.12); tone(55, 1.0, 0.2, 'square', 3); noise(0.9, 2400, 0.5, 0.3, 'bandpass', 0.2); },
  alarm: () => { for (let i = 0; i < 3; i++) { tone(988, 0.16, 0.06, 'square', 1, i * 0.32); tone(740, 0.16, 0.06, 'square', 1, i * 0.32 + 0.16); } },
  shot: () => { tone(1480, 0.12, 0.05, 'square', 0.35); noise(0.08, 4000, 1.2, 0.08, 'highpass'); },
  charge: () => tone(300, 0.6, 0.05, 'sawtooth', 4),
  thud: () => { noise(0.4, 180, 0.7, 0.5, 'lowpass', 0.4); tone(55, 0.4, 0.25, 'square', 0.5); },
  missile: () => { noise(0.5, 900, 0.8, 0.18, 'bandpass', 2.2); tone(420, 0.4, 0.04, 'sawtooth', 2); },
  blast: () => { noise(0.6, 260, 0.6, 0.6, 'lowpass', 0.3); noise(0.25, 3000, 0.8, 0.2, 'bandpass', 0.4); tone(70, 0.5, 0.25, 'square', 0.4); },
  beam: () => { tone(220, 0.6, 0.09, 'sawtooth', 0.5); noise(0.6, 5000, 0.8, 0.25, 'highpass', 0.5); tone(1760, 0.4, 0.04, 'sine', 0.5); },
  voice: (n = 3) => { for (let i = 0; i < n; i++) tone(rand(160, 320), 0.07, 0.05, 'square', rand(0.7, 1.4), i * 0.07); },
};
const nhRect = (x, y, w, h, c) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
function nhLine(x0, y0, x1, y1, c, step = 1) {   // pixel-clean line
  const n = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) / step)); g.fillStyle = c;
  for (let i = 0; i <= n; i++) g.fillRect(Math.round(lerp(x0, x1, i / n)), Math.round(lerp(y0, y1, i / n)), 1, 1);
}

// ================================================================== per-room state
const NHR = { roomObj: null };
function nhReset() {
  Object.assign(NHR, { roomObj: room, t: 0, lasers: [], terms: [], doors: [], plats: [], trains: [], fogs: [], portals: [],
    bolts: [], sparks: [], voids: [], dels: [], safe: null, carry: 0, ride: null, alarmT: 0, rf: 0, brk: null, marks: [], beams: [],
    walls: [], rains: [], rings: [], missiles: [], blades: [] });
}
function nhEnsure() { if (NHR.roomObj !== room) nhReset(); }
const nhCell = (tx, ty) => (tx >= 0 && ty >= 0 && tx < room.w && ty < room.h) ? room.grid[ty * room.w + tx] : -1;
function nhFeet(b) {
  const ty = Math.floor((b.y + 1) / TILE);
  return [Math.floor((b.x - b.w / 2 + 1) / TILE), Math.floor((b.x + b.w / 2 - 1) / TILE)].map(tx => [tx, ty, nhCell(tx, ty)]);
}

// ================================================================== tiles
registerTile('1', NH_T_VOID, { solid: true, draw() {} });   // the data abyss: drawn live (animated grid, glitching surface)
registerTile('2', NH_T_DEL, { solid: true, draw() {} });    // SAINT-0's floor: drawn live (it glitches out and comes back)
function nhDrawVoid() {
  const cyb = nhCyber();
  for (const [x, y, top] of NHR.voids) {
    const px = x * TILE, py = y * TILE;
    if (px + 16 < cam.x || px > cam.x + W || py + 16 < cam.y || py > cam.y + H) continue;
    g.fillStyle = cyb ? '#c6d2de' : '#03020a'; g.fillRect(px, py, 16, 16);
    // a receding grid falling away into nothing
    const s = (time * 14 + x * 3) % 8;
    g.fillStyle = cyb ? 'rgba(20,30,70,0.35)' : 'rgba(19,163,201,0.22)';
    for (let yy = (s | 0); yy < 16; yy += 8) g.fillRect(px, py + yy, 16, 1);
    if (x % 2 === 0) g.fillRect(px, py, 1, 16);
    if (top) {
      const f = Math.sin(time * 9 + x * 1.7);
      g.fillStyle = cyb ? '#1a2350' : (f > 0.6 ? NH_MG[3] : NH_CY[3]); g.fillRect(px, py, 16, 1);
      g.fillStyle = cyb ? 'rgba(26,35,80,0.5)' : 'rgba(63,224,255,0.35)'; g.fillRect(px, py + 1, 16, 1);
      if (hash2(x, Math.floor(time * 6)) < 0.08) { g.fillStyle = cyb ? '#101840' : NH_CY[4]; g.fillRect(px + (hash2(x, 3) * 12 | 0), py - 2, 3, 1); }
      if ((x + Math.floor(time * 3)) % 4 === 0) addLight(px + 8, py + 2, 26, '60,200,255', 0.3);
    }
  }
}

// ================================================================== room setup
HOOKS.enter.push(def => {
  nhEnsure();
  nhHintsEnter(def);
  if (!nhIn()) return;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x];
    if (ch === '1') NHR.voids.push([x, y, y === 0 || def.map[y - 1][x] !== '1']);
    if (ch === '2') NHR.dels.push({ x, y, st: 'solid', t: 0, a: 1 });
  }
  NHR.safe = P ? { x: P.x, y: P.y } : null;
  if (def.id === 'NH1' && !SAVE.flags['nh:arrived']) {
    SAVE.flags['nh:arrived'] = 1;
    setTimeout(() => { if (room && room.id === 'NH1') toast('Rain. Neon. A city grown over the bones of the Pale Root.', 4); }, 1800);
  }
  if (def.id === 'NH3') nhOnce('nh_train', 'The maglev car shuttles across the abyss. Ride it — and mind the gate.');
  if (def.id === 'NH4') nhOnce('nh_term', 'Strike a terminal (or press E beside it) to override what it controls.');
});
function nhOnce(k, m) { const H_ = SAVE.hints; if (!H_[k]) { H_[k] = 1; setTimeout(() => toast(m, 4.5), 1300); } }

// ================================================================== laser grids (timed; security magenta)
SPAWNS.nh_laser = (s, c) => {
  nhEnsure();
  NHR.lasers.push({ x: s.x * TILE + 8, y0: s.y0 * TILE, y1: (s.y1 + 1) * TILE, period: s.period || 3.4, on: s.on || 1.1, warn: s.warn || 0.7,
    phase: s.phase || 0, dmg: s.dmg || 30, id: ++hazardId, link: s.link, off: !!s.disabled, prev: 'off' });
};
function nhLaserState(L) {
  if (L.off) return 'off';
  const tt = (((NHR.t + L.phase) % L.period) + L.period) % L.period;
  return tt < L.on ? 'on' : tt > L.period - L.warn ? 'warn' : 'off';
}
function nhUpdateLasers() {
  for (const L of NHR.lasers) {
    const st = nhLaserState(L), cyc = Math.floor((NHR.t + L.phase) / L.period);
    const vis = L.x > cam.x - 40 && L.x < cam.x + W + 40;
    if (st !== L.prev) { if (st === 'on' && vis) nhSfx.zap(0.8); if (st === 'warn' && vis) tone(1200, 0.25, 0.02, 'square', 1.3); L.prev = st; }
    if (st === 'on') {
      for (let y = L.y0 + 12; y < L.y1; y += 40) addLight(L.x, y, 34, '255,60,190', 0.6);
      if (overlap(rect(L.x - 4, L.y0, L.x + 4, L.y1), playerHurtbox())) hurtPlayer(L.dmg * NGP.dmg, P.x < L.x ? -1 : 1, L.id * 1000 + cyc, {});
    } else if (st === 'warn') addLight(L.x, L.y0 + 6, 16, '255,60,190', 0.4);
  }
}
function nhDrawLasers() {
  for (const L of NHR.lasers) {
    if (L.x < cam.x - 20 || L.x > cam.x + W + 20) continue;
    const st = nhLaserState(L), x = Math.round(L.x);
    // emitter (hangs from the gantry above) + floor receiver
    nhRect(x - 5, L.y0, 10, 4, NH_NV[4]); nhRect(x - 4, L.y0 + 4, 8, 2, NH_NV[3]); nhRect(x - 1, L.y0 + 4, 3, 2, st === 'off' ? NH_MG[1] : NH_MG[3]);
    nhRect(x - 5, L.y1 - 2, 10, 2, NH_NV[4]); nhRect(x - 2, L.y1 - 3, 5, 1, st === 'off' ? NH_MG[1] : NH_MG[2]);
    if (st === 'warn') {
      if (Math.floor(time * 24) % 2) for (let y = L.y0 + 6; y < L.y1 - 3; y += 3) nhRect(x, y, 1, 1, NH_MG[3]);
    } else if (st === 'on') {
      const j = Math.sin(time * 60) > 0 ? 1 : 0;
      g.fillStyle = 'rgba(194,29,151,0.55)'; g.fillRect(x - 2 - j, L.y0 + 6, 5 + j * 2, L.y1 - L.y0 - 9);
      g.fillStyle = NH_MG[3]; g.fillRect(x - 1, L.y0 + 6, 3, L.y1 - L.y0 - 9);
      g.fillStyle = NH_MG[5]; g.fillRect(x, L.y0 + 6, 1, L.y1 - L.y0 - 9);
      for (let k = 0; k < 3; k++) { const yy = L.y0 + 6 + ((time * 180 + k * 37) % (L.y1 - L.y0 - 9)); nhRect(x - 2, yy, 5, 1, NH_MG[4]); }
      if (Math.random() < 0.3) particles.push({ x: x + rand(-2, 2), y: L.y1 - 3, vx: rand(-40, 40), vy: -rand(20, 70), g: 300, life: 0.3, kind: 'nh_pink' });
    }
  }
}

// ================================================================== terminals, energy doors, hard-light platforms
function nhToggle(id) {
  for (const d of NHR.doors) if (d.id === id) { d.open = !d.open; if (!d.open) d.pend = true; nhSfx.door(); }
  for (const p of NHR.plats) if (p.id === id) { p.on = !p.on; p.flick = 0.35; }
  for (const L of NHR.lasers) if (L.link === id) L.off = !L.off;
}
function nhHack(p) {
  if (p.cd > 0) return;
  p.cd = 0.55; p.hacked = !p.hacked; p.blink = 1;
  for (const id of p.links) nhToggle(id);
  (p.hacked ? nhSfx.hack : nhSfx.unhack)(); shake = Math.max(shake, 2);
  for (let i = 0; i < 10; i++) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(12, 24), vx: rand(-50, 50), vy: -rand(20, 80), g: 200, life: 0.5, kind: p.hacked ? 'nh_data' : 'nh_mote' });
  toast(`${p.label} // ${p.hacked ? 'OVERRIDE' : 'RESTORED'}`, 1.6);
}
SPAWNS.nh_term = (s, c) => {
  nhEnsure();
  const sh = sheet('nh_term');
  const p = { type: 'nh_term', x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, 'idle', true), links: s.links || [], label: s.label || 'NODE', cd: 0, blink: 0, hacked: false };
  p.hurtbox = () => rect(p.x - 7, p.y - 24, p.x + 7, p.y);
  p.onHit = () => nhHack(p);
  p.interact = () => nhHack(p);
  p.prompt = () => 'Hack';
  p.update = dt => {
    p.cd -= dt; p.blink = Math.max(0, p.blink - dt * 2.5);
    const want = p.hacked ? 'on' : 'idle'; if (p.anim.tag !== want && sh.has(want)) p.anim.set(want, true);
    addLight(p.x, p.y - 16, 34 + p.blink * 20, p.hacked ? '90,255,200' : '80,200,255', 0.7 + p.blink * 0.3);
  };
  p.draw = () => {
    if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, 1, { bottom: true, flash: p.blink * 0.6, flashColor: '#b8f6ff' });
    else { nhRect(p.x - 6, p.y - 22, 12, 22, NH_NV[4]); nhRect(p.x - 4, p.y - 19, 8, 6, p.hacked ? '#5affd2' : NH_CY[3]); }
    // hologram label
    const a = 0.55 + 0.25 * Math.sin(time * 5 + p.x);
    g.globalAlpha = a; g.fillStyle = p.hacked ? '#5affd2' : NH_CY[3];
    for (let i = 0; i < p.label.length; i++) { const h = 1 + ((p.label.charCodeAt(i) * 7) % 3); g.fillRect(Math.round(p.x - p.label.length * 2 + i * 4), Math.round(p.y - 31 - h), 3, h); }
    g.globalAlpha = 1;
  };
  props.push(p); NHR.terms.push(p);
};
SPAWNS.nh_door = (s, c) => {
  nhEnsure();
  const h = s.h || 4, x = s.x * TILE;
  const d = { id: s.id, open: !!s.open, pend: false, x0: x + 3, x1: x + 13, y0: (s.y - h + 1) * TILE, y1: (s.y + 1) * TILE, k: s.open ? 0 : 1 };
  room.dyn.push({ x0: d.x0, x1: d.x1, y0: d.y0, y1: d.y1, on: () => !d.open && !d.pend });
  NHR.doors.push(d);
};
function nhUpdateDoors(dt) {
  for (const d of NHR.doors) {
    if (d.pend && !overlap(rect(d.x0 - 1, d.y0, d.x1 + 1, d.y1), playerHurtbox()) && !enemies.some(e => e.alive && !e.cfg.flying && overlap(rect(d.x0, d.y0, d.x1, d.y1), e.hurtbox() || rect(0, 0, 0, 0)))) d.pend = false;
    d.k = approach(d.k, d.open || d.pend ? 0 : 1, dt * 4);
    if (d.k > 0.1) addLight((d.x0 + d.x1) / 2, (d.y0 + d.y1) / 2, 50, '80,200,255', 0.5 * d.k);
  }
}
function nhDrawDoors() {
  for (const d of NHR.doors) {
    const cx = Math.round((d.x0 + d.x1) / 2);
    nhRect(cx - 6, d.y1 - 3, 12, 3, NH_NV[4]); nhRect(cx - 6, d.y0, 12, 3, NH_NV[4]);
    nhRect(cx - 1, d.y0 + 1, 2, 1, d.k > 0.5 ? NH_CY[4] : NH_RD[2]); nhRect(cx - 1, d.y1 - 2, 2, 1, d.k > 0.5 ? NH_CY[4] : NH_RD[2]);
    if (d.k <= 0.02) continue;
    const top = d.y0 + 3, hh = d.y1 - d.y0 - 6;
    g.globalAlpha = 0.55 * d.k; g.fillStyle = NH_CY[1]; g.fillRect(cx - 4, top, 9, hh);
    g.globalAlpha = 0.9 * d.k; g.fillStyle = NH_CY[3]; g.fillRect(cx - 4, top, 1, hh); g.fillRect(cx + 4, top, 1, hh);
    for (let k = 0; k < 6; k++) { const y = top + ((time * 40 + k * 11) % hh); g.fillStyle = k % 2 ? NH_CY[4] : NH_CY[2]; g.fillRect(cx - 3, Math.round(y), 7, 1); }
    for (let k = 0; k < 5; k++) if (hash2(k, Math.floor(time * 8)) < 0.5) { g.fillStyle = NH_CY[5]; g.fillRect(cx - 2 + (k % 3) * 2, top + ((k * 13 + Math.floor(time * 20)) % hh), 1, 2); }
    g.globalAlpha = 1;
  }
}
SPAWNS.nh_plat = (s, c) => {
  nhEnsure();
  const pl = { id: s.id, on: !!s.on, x0: s.x * TILE, x1: (s.x + (s.w || 3)) * TILE, y0: s.y * TILE, k: s.on ? 1 : 0, flick: 0 };
  // one-way hard-light: solid only while the player's feet are at or above its top
  room.dyn.push({ x0: pl.x0, x1: pl.x1, y0: pl.y0, y1: pl.y0 + 6, on: () => pl.on && pl.k > 0.6 && !!P && P.y <= pl.y0 + 0.5 });
  NHR.plats.push(pl);
};
function nhUpdatePlats(dt) { for (const p of NHR.plats) { p.k = approach(p.k, p.on ? 1 : 0, dt * 3.2); p.flick = Math.max(0, p.flick - dt); if (p.k > 0.2) addLight((p.x0 + p.x1) / 2, p.y0 + 2, (p.x1 - p.x0) * 0.7, '80,220,255', 0.45 * p.k); } }
function nhDrawPlats() {
  for (const p of NHR.plats) {
    const w = p.x1 - p.x0, x = Math.round(p.x0), y = Math.round(p.y0);
    // projector nubs stay visible when the platform is off (you can see where it will be)
    g.globalAlpha = 0.8; g.fillStyle = NH_NV[4]; g.fillRect(x, y + 1, 2, 3); g.fillRect(x + w - 2, y + 1, 2, 3); g.globalAlpha = 1;
    if (p.k < 0.05) { if (Math.floor(time * 2 + p.x0) % 3 === 0) { g.globalAlpha = 0.25; g.fillStyle = NH_CY[2]; for (let i = 2; i < w - 2; i += 3) g.fillRect(x + i, y + 2, 1, 1); g.globalAlpha = 1; } continue; }
    const fl = p.flick > 0 && Math.floor(time * 30) % 2 ? 0.4 : 1;
    g.globalAlpha = 0.45 * p.k * fl; g.fillStyle = NH_CY[2]; g.fillRect(x + 1, y + 1, w - 2, 4);
    g.globalAlpha = p.k * fl; g.fillStyle = NH_CY[4]; g.fillRect(x + 1, y, w - 2, 1); g.fillStyle = NH_CY[3]; g.fillRect(x + 1, y + 5, w - 2, 1);
    for (let i = 3; i < w - 3; i += 5) { g.fillStyle = hash2(i, Math.floor(time * 4 + p.x0)) < 0.5 ? NH_CY[5] : NH_CY[3]; g.fillRect(x + i, y + 2, 2, 1); }
    g.globalAlpha = 1;
  }
}

// ================================================================== the maglev car
SPAWNS.nh_train = (s, c) => {
  nhEnsure();
  const w = (s.w || 6) * TILE, A = s.x0 * TILE, B = (s.x1 + 1) * TILE - w;
  const tr = { A, B, x: A, w, y: s.y * TILE, vx: 0, v: 0, st: 'wait', t: 1.2, dir: 1, wait: s.wait || 2.2, speed: s.speed || 104, x0c: s.x0, x1c: s.x1 };
  room.dyn.push({ get x0() { return tr.x; }, get x1() { return tr.x + tr.w; }, y0: tr.y, y1: tr.y + 7, on: () => true, train: true });
  NHR.trains.push(tr);
};
function nhOnTrain(tr) { return P.ground && Math.abs(P.y - tr.y) < 1.5 && P.x + P.w / 2 > tr.x + 1 && P.x - P.w / 2 < tr.x + tr.w - 1; }
function nhUpdateTrains(dt) {
  let ride = null;
  for (const tr of NHR.trains) {
    const on = nhOnTrain(tr);
    if (tr.st === 'wait') { tr.t -= dt; tr.vx = 0; if (tr.t <= 0) { tr.st = 'go'; if (Math.abs(P.x - tr.x) < 400) nhSfx.chime(); } }
    else {
      const goal = tr.dir > 0 ? tr.B : tr.A, rem = (goal - tr.x) * tr.dir;
      tr.v = approach(tr.v, Math.min(tr.speed, Math.sqrt(Math.max(0, 2 * 140 * rem)) + 6), 140 * dt);
      let dx = tr.v * tr.dir * dt;
      if (Math.abs(dx) >= rem) { dx = rem * tr.dir; tr.st = 'wait'; tr.t = tr.wait; tr.dir = -tr.dir; tr.v = 0; }
      tr.x += dx; tr.vx = dx / dt;
      if (Math.random() < 0.4) particles.push({ x: tr.x + (tr.dir > 0 ? 0 : tr.w), y: tr.y + 30, vx: -tr.dir * rand(20, 60), vy: rand(-10, 10), life: 0.4, kind: 'nh_mote' });
    }
    if (on) { ride = tr; P.pushVx = (P.pushVx || 0) + tr.vx; }
    addLight(tr.x + tr.w / 2, tr.y + 14, 70, '80,210,255', 0.6); addLight(tr.x + (tr.dir > 0 ? tr.w : 0), tr.y + 16, 30, '255,70,200', 0.7);
  }
  // momentum: jumping off a moving car keeps its speed until you land
  if (ride) { NHR.carry = ride.vx; NHR.ride = ride; }
  else if (!P.ground && NHR.carry && P.state !== 'hook') P.pushVx = (P.pushVx || 0) + NHR.carry;
  else { NHR.carry = 0; NHR.ride = null; }
}
function nhDrawTrains() {
  const sh = sheet('nh_train');
  for (const tr of NHR.trains) {
    // the magnetic rail under the lane
    const ry = tr.y + 34, x0 = tr.x0c * TILE, x1 = (tr.x1c + 1) * TILE;
    g.fillStyle = NH_NV[4]; g.fillRect(x0, ry, x1 - x0, 2); g.fillStyle = 'rgba(63,224,255,0.5)'; g.fillRect(x0, ry + 2, x1 - x0, 1);
    for (let x = x0 + ((time * 60) % 24); x < x1; x += 24) { g.fillStyle = NH_CY[4]; g.fillRect(Math.round(x), ry + 2, 3, 1); }
    const cx = Math.round(tr.x + tr.w / 2), bob = tr.st === 'go' ? 0 : Math.round(Math.sin(time * 3) * 0.6);
    if (sh.ok) drawSprite(sh, sh.first(tr.st === "go" ? "run" : "idle") + (tr.st === "go" ? Math.floor(time * 12) % 4 : 0), cx, tr.y + sh.fh + bob, tr.dir > 0 ? 1 : -1, { bottom: true });
    else { nhRect(tr.x, tr.y, tr.w, 3, NH_CY[3]); nhRect(tr.x + 2, tr.y + 3, tr.w - 4, 24, NH_NV[3]); nhRect(tr.x + 6, tr.y + 9, tr.w - 12, 5, NH_CY[1]); }
  }
}

// ================================================================== the data abyss: burns, then throws you back to solid ground
function nhUpdateVoid(dt) {
  if (P.ground && P.state !== 'dead') {
    const ft = nhFeet(P), onVoid = ft.some(([, , t]) => t === NH_T_VOID);
    const real = ft.every(([, , t]) => t === T_PLAT || (isSolidT(t) && t !== NH_T_VOID)) && !ft.some(([, , t]) => t === NH_T_DEL && room.id === 'NH7');
    if (real && !onVoid && !nearSpikes()) NHR.safe = { x: P.x, y: P.y };
    else if (NHR.safe && !onVoid) P.safe = { ...NHR.safe };
    if (onVoid) {
      for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(0, 6), vx: rand(-80, 80), vy: -rand(60, 200), g: 400, life: rand(0.4, 0.8), kind: i % 2 ? 'nh_mote' : 'nh_pink' });
      nhSfx.glitch(0.8);
      if (room.id === 'NH7') {   // the Null Sanctum: a 1-tile pit — the abyss burns and flings you back up
        hurtPlayer(BOSS_DMG * 34 * NGP.dmg, P.x < room.pw / 2 ? 1 : -1, 'nhvoid' + Math.floor(time * 2.5), { src: boss });
        P.vy = -360; P.ground = false; P.y -= 2; if (P.state !== 'hurt') setP('air', 'jump_up', false);
      } else {
        if (!NHR.safe) NHR.safe = nhNearestGround(P.x, P.y);
        if (NHR.safe) P.safe = { ...NHR.safe };
        P.inv = 0; spikeHurt();
      }
    }
  }
  for (const e of enemies) if (e.alive && !e.cfg.flying && e.ground && nhFeet(e).some(([, , t]) => t === NH_T_VOID)) { e.hp = 0; e.die({ dir: 0 }); nhSfx.glitch(0.5); }
}
function nhNearestGround(x, y) {
  const tx0 = Math.floor(x / TILE); let best = null, bd = 1e9;
  for (let ty = 1; ty < room.h; ty++) for (let tx = Math.max(0, tx0 - 30); tx < Math.min(room.w, tx0 + 30); tx++) {
    const t = room.grid[ty * room.w + tx]; if (!(isSolidT(t) && t !== NH_T_VOID)) continue;
    if (isSolidT(room.grid[(ty - 1) * room.w + tx]) || (ty > 1 && isSolidT(room.grid[(ty - 2) * room.w + tx]))) continue;
    const d = Math.abs(tx * TILE + 8 - x) + Math.abs(ty * TILE - y) * 0.5; if (d < bd) { bd = d; best = { x: tx * TILE + 8, y: ty * TILE }; }
  }
  return best;
}

// ================================================================== firewall gates (boss arenas: reach the sky, can't be jumped)
SPAWNS.nh_fog = (s, c) => {
  nhEnsure();
  if (SAVE.flags['boss:' + s.kind]) return;
  const x = s.x * TILE + 8, fy = c.fy, exit = !!s.exit;
  const on = () => boss && boss.kind === s.kind && boss.alive && (boss.active || exit);
  const f = { x, fy, on, a: 0 };
  NHR.fogs.push(f);
  room.dyn.push({ x0: x - 8, x1: x + 8, y0: -400, y1: fy, on });
};
function nhDrawFogs() {
  for (const f of NHR.fogs) {
    f.a = approach(f.a, f.on() ? 1 : 0, 0.05);
    if (f.a <= 0.01) continue;
    const x = Math.round(f.x), top = Math.max(0, Math.floor(cam.y / TILE) * TILE - 16), cyb = nhCyber();
    g.globalAlpha = 0.35 * f.a; g.fillStyle = cyb ? '#1b2250' : NH_MG[1]; g.fillRect(x - 7, top, 14, f.fy - top);
    g.globalAlpha = 0.9 * f.a;
    for (let y = top; y < f.fy; y += 4) {
      const r = hash2(Math.floor(y / 4), Math.floor(time * 10 + f.x));
      g.fillStyle = cyb ? (r < 0.5 ? '#101840' : '#c21d97') : (r < 0.35 ? NH_MG[4] : r < 0.7 ? NH_MG[3] : NH_CY[3]);
      const off = Math.floor(((y * 7 + time * 60) % 12)) - 6;
      g.fillRect(x + off, y, r < 0.2 ? 3 : 2, 2);
    }
    g.fillStyle = cyb ? '#101840' : NH_MG[4]; g.fillRect(x - 7, top, 1, f.fy - top); g.fillRect(x + 6, top, 1, f.fy - top);
    g.globalAlpha = 1;
    for (let y = f.fy - 20; y > cam.y; y -= 60) addLight(x, y, 40, '255,60,190', 0.5 * f.a);
  }
}

// ================================================================== decor props, floating items
const NH_DECO = { sign: ['sign', 64, true], billboard: ['billboard', 60, true], lamp: ['lamp', 40, true], antenna: ['antenna', 18, true], vent: ['vent', 0, false],
  canopy: ['canopy', 30, true], pylon: ['pylon', 20, true], rack: ['rack', 20, true], glyph: ['glyph', 30, true] };
const NH_NEON = ['255,60,190', '80,210,255', '255,160,60'];
SPAWNS.nh_deco = (s, c) => {
  nhEnsure();
  const d = NH_DECO[s.kind]; if (!d) return;
  const sh = sheet('nh_deco'), v = s.v || 0, tag = s.kind + (['sign', 'billboard'].includes(s.kind) ? v : '');
  const p = { type: 'nh_deco', kind: s.kind, x: c.cx, y: s.hang ? s.y * TILE : c.fy, face: 1, sh, v, anim: new Anim(sh, sh.has(tag) ? tag : (sh.has(s.kind) ? s.kind : Object.keys(sh.tags)[0] || tag), true), hang: !!s.hang, seed: rand(0, 9) };
  p.anim.t = rand(0, 500);
  p.update = dt => {
    const col = s.kind === 'lamp' || s.kind === 'canopy' ? NH_NEON[1] : s.kind === 'rack' || s.kind === 'glyph' ? '90,255,210' : NH_NEON[v % 3];
    const fl = s.kind === 'sign' && hash2(Math.floor(time * 7 + p.seed * 10), 1) < 0.04 ? 0.2 : 1;
    if (d[1]) addLight(p.x, p.y - d[1], s.kind === 'billboard' ? 90 : 46, col, 0.75 * fl);
    if (s.kind === 'vent' && Math.random() < dt * 5) particles.push({ x: p.x + rand(-4, 4), y: p.y - 14, vx: rand(-6, 6), vy: -rand(14, 30), life: 1.6, kind: 'dust' });
  };
  p.draw = () => {
    const o = s.hang ? { pivot: [Math.floor(sh.fw / 2), 0] } : { bottom: true };
    if (sh.ok) {
      const fl = s.kind === 'sign' && hash2(Math.floor(time * 7 + p.seed * 10), 1) < 0.04;
      drawSprite(sh, p.anim.frame, p.x, p.y, 1, { ...o, alpha: fl ? 0.55 : 1 });
      // wet-street reflection of the neon under signs and billboards (outdoor rooms)
      if (!room.def.indoor && (s.kind === 'sign' || s.kind === 'billboard' || s.kind === 'lamp') && !s.hang) {
        const col = s.kind === 'lamp' ? NH_CY : v % 3 === 0 ? NH_MG : v % 3 === 1 ? NH_CY : ['#3a1e06', '#7a4410', '#c87a20', '#ffb050', '#ffe0a0', '#fff'];
        for (let i = 0; i < 7; i++) { const w = 2 + ((i * 5 + Math.floor(time * 6 + p.seed)) % 7); g.globalAlpha = 0.28 - i * 0.03; g.fillStyle = col[3]; g.fillRect(Math.round(p.x - w / 2 + Math.sin(time * 2 + i) * 2), Math.round(p.y + 1 + i * 2), w, 1); }
        g.globalAlpha = 1;
      }
    } else { g.fillStyle = s.kind === 'sign' ? NH_MG[3] : NH_NV[4]; g.fillRect(Math.round(p.x - 6), Math.round(p.y - (d[1] || 12)), 12, d[1] || 12); }
  };
  props.push(p);
};
SPAWNS.nh_item = (s, c) => {
  const k = `item:${c.id}:nh${c.key.split(':sp')[1]}`;
  if (!SAVE.flags[k]) props.push(makeProp('item', c.cx, c.fy - 4, { key: k, item: s.item }));
};

// ================================================================== rain, reflections, drips
function nhDrawRain() {
  if (room.def.indoor || nhCyber()) return;
  const n = 120;
  for (let i = 0; i < n; i++) {
    const sx = hash2(i, 17) * (W + 80) - 40, sp = 300 + hash2(i, 5) * 170, len = 6 + Math.floor(hash2(i, 9) * 7);
    const yy = ((hash2(i, 21) * 400 + time * sp) % (H + 40)) - 20, slant = 0.18;
    const x = ((((sx + time * sp * slant) % (W + 80)) + W + 80) % (W + 80)) - 40;
    const k = hash2(i, 31);
    g.fillStyle = k < 0.08 ? 'rgba(255,90,200,0.35)' : k < 0.2 ? 'rgba(90,220,255,0.35)' : `rgba(150,170,210,${0.12 + hash2(i, 13) * 0.16})`;
    for (let j = 0; j < len; j++) g.fillRect(Math.round(x + j * slant), Math.round(yy + j), 1, 1);
  }
}

// ================================================================== main hooks
HOOKS.update.push(dt => {
  nhUpdateGlobal(dt);
  if (!nhIn()) return;
  nhEnsure();
  NHR.t += dt;
  nhUpdateLasers(); nhUpdateDoors(dt); nhUpdatePlats(dt); nhUpdateTrains(dt); nhUpdateVoid(dt);
  nhUpdateBolts(dt); nhUpdateSparks(dt);
  if (typeof nhUpdateBossFx === 'function') nhUpdateBossFx(dt);
  // ambient motes: cold neon dust instead of gold
  for (const p of particles) if (p.amb && p.kind === 'mote') { p.kind = Math.random() < 0.2 ? 'nh_pink' : 'nh_mote'; p.vy = rand(4, 16); }
});
HOOKS.render.push(() => {
  if (!nhIn()) { nhDrawHints(); return; }
  nhDrawVoid(); if (typeof nhDrawDelFloor === 'function') nhDrawDelFloor();
  nhDrawTrains(); nhDrawPlats(); nhDrawDoors(); nhDrawLasers(); nhDrawFogs(); nhDrawBolts(); nhDrawSparks();
  if (typeof nhDrawBossFx === 'function') nhDrawBossFx();
});
HOOKS.renderTop.push(() => {
  if (nhIn()) { nhDrawRain(); if (typeof nhDrawCyberTop === 'function') nhDrawCyberTop(); }
  nhDrawScanTop(); nhDrawWarp();
});
HOOKS.death.push(() => { NHR.carry = 0; });

// ================================================================== bolts (drone zaps, turret rounds) + impact rings
function nhBolt(src, x, y, ang, sp, dmg, col = 'cy', r = 3) {
  NHR.bolts.push({ x, y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, life: 2.6, dmg, id: ++hazardId, src, col, r });
}
function nhUpdateBolts(dt) {
  for (const b of NHR.bolts) {
    b.life -= dt; b.x += b.vx * dt; b.y += b.vy * dt;
    addLight(b.x, b.y, 24, b.col === 'rd' ? '255,60,80' : b.col === 'mg' ? '255,60,190' : '80,210,255', 0.8);
    if (overlap(rect(b.x - b.r, b.y - b.r, b.x + b.r, b.y + b.r), playerHurtbox()) && hurtPlayer(b.dmg, sign(b.vx), b.id, { src: b.src })) { b.life = 0; nhSpark(b.x, b.y, b.col); continue; }
    if (solidAtPx(b.x, b.y) || b.life <= 0) { b.life = 0; nhSpark(b.x - b.vx * dt, b.y - b.vy * dt, b.col); }
  }
  NHR.bolts = NHR.bolts.filter(b => b.life > 0);
}
function nhDrawBolts() {
  for (const b of NHR.bolts) {
    const C = b.col === 'rd' ? NH_RD : b.col === 'mg' ? NH_MG : NH_CY, sp = Math.hypot(b.vx, b.vy) || 1, dx = b.vx / sp, dy = b.vy / sp;
    for (let k = 7; k >= 0; k--) { const s = k < 2 ? 2 : 1; g.fillStyle = C[k < 2 ? 5 : k < 4 ? 4 : 3]; g.globalAlpha = 1 - k * 0.1; g.fillRect(Math.round(b.x - dx * k * 1.5 - s / 2), Math.round(b.y - dy * k * 1.5 - s / 2), s, s); }
    g.globalAlpha = 1;
  }
}
function nhSpark(x, y, col = 'cy', n = 8) {
  NHR.sparks.push({ x, y, t: 0, life: 0.25, col });
  for (let i = 0; i < n; i++) particles.push({ x, y, vx: rand(-90, 90), vy: -rand(20, 110), g: 320, life: rand(0.2, 0.45), kind: col === 'mg' || col === 'rd' ? 'nh_pink' : 'nh_mote' });
}
function nhUpdateSparks(dt) { for (const s of NHR.sparks) s.t += dt; NHR.sparks = NHR.sparks.filter(s => s.t < s.life); }
function nhDrawSparks() {
  for (const s of NHR.sparks) {
    const k = s.t / s.life, r = 2 + k * 10, C = s.col === 'rd' ? NH_RD : s.col === 'mg' ? NH_MG : NH_CY;
    g.globalAlpha = 1 - k; g.fillStyle = C[4];
    for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283; g.fillRect(Math.round(s.x + Math.cos(a) * r), Math.round(s.y + Math.sin(a) * r), 1, 1); }
    g.globalAlpha = 1;
  }
}

// ================================================================== the portal (a crack in reality) + the glitch warp
const NH = { warp: null, lock: null, scanT: 0, pulse: -1, hum: 0, hintT: 0 };
SPAWNS.nh_portal = (s, c) => {
  nhEnsure();
  const sh = sheet('nh_portal');
  const p = { type: 'nh_portal', x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, 'loop', true), to: s.to, tx: s.tx, ty: s.ty, back: !!s.back };
  // in the Root Shaft the crack hides behind the cracked rock until it is broken
  p.hidden = () => c.id === 'C6' && room.grid[20 * room.w + 14] !== T_EMPTY;
  p.update = dt => {
    if (p.hidden()) return;
    addLight(p.x, p.y - 26, 60 + Math.sin(time * 13) * 6, Math.floor(time * 5) % 2 ? '80,220,255' : '255,70,200', 0.9);
    if (Math.random() < 0.3) particles.push({ x: p.x + rand(-6, 6), y: p.y - rand(4, 46), vx: rand(-20, 20), vy: rand(-20, 20), life: 0.4, kind: Math.random() < 0.5 ? 'nh_pink' : 'nh_mote' });
    const near = Math.abs(P.x - p.x) < 70 && Math.abs(P.y - p.y) < 50;
    if (near && (NH.hum -= dt) <= 0) { NH.hum = 1.1; tone(55, 1.0, 0.03, 'sawtooth', 1.02); tone(110.5, 0.9, 0.015, 'square', 0.98); }
    if (NH.lock && NH.lock.room === room.id && Math.hypot(P.x - NH.lock.x, P.y - NH.lock.y) > 40) NH.lock = null;
    if (!NH.warp && !NH.lock && P.state !== 'dead' && Math.abs(P.x - p.x) < 8 && P.y > p.y - 48 && P.y <= p.y + 2) nhStartWarp(p);
  };
  p.draw = () => {
    if (p.hidden()) return;
    if (sh.ok) { drawSprite(sh, p.anim.frame, p.x, p.y, 1, { bottom: true }); return; }
    // fallback: a jagged tear with a chromatic fringe
    for (let y = 0; y < 48; y += 2) { const dx = Math.round(Math.sin(y * 0.7 + time * 9) * 2 + (hash2(y, Math.floor(time * 12)) - 0.5) * 3);
      nhRect(p.x + dx - 2, p.y - 48 + y, 1, 2, NH_MG[3]); nhRect(p.x + dx + 2, p.y - 48 + y, 1, 2, NH_CY[3]); nhRect(p.x + dx, p.y - 48 + y, 1, 2, '#fff'); }
  };
  props.push(p); NHR.portals.push(p);
};
function nhStartWarp(p) {
  NH.warp = { t: 0, phase: 'out', to: p.to, tx: p.tx, ty: p.ty, x: p.x };
  if (!['idle', 'run', 'air', 'land'].includes(P.state) || !P.ground) { P.vx = 0; }
  nhSfx.warp(); shake = 4;
}
function nhUpdateWarp(dt) {
  const w = NH.warp; if (!w) return;
  w.t += dt;
  if (w.phase === 'out') {
    P.vx = 0; P.vy = Math.min(P.vy, 0); P.x = lerp(P.x, w.x, Math.min(1, dt * 8)); P.ctrlLock = 0.15; P.inv = Math.max(P.inv, 0.3);
    if (w.t >= 0.75) {
      const def = ROOM_BY[w.to]; if (!def) { NH.warp = null; return; }
      enterRoom(w.to, w.tx * TILE + 8, (w.ty + 1) * TILE, { card: true }); P.vx = P.vy = 0; setP('idle', 'idle', true);
      NH.lock = { room: w.to, x: P.x, y: P.y }; w.phase = 'in'; w.t = 0; nhSfx.glitch(1); saveGame();
    }
  } else if (w.t >= 0.6) NH.warp = null;
}
const nhTmp = document.createElement('canvas'); nhTmp.width = W; nhTmp.height = H;
const nhTctx = nhTmp.getContext('2d');
function nhGlitchScreen(k, seed = 0) {   // k 0..1: slice displacement, colour blocks, scanlines (screen space)
  if (k <= 0.01) return;
  nhTctx.clearRect(0, 0, W, H); nhTctx.drawImage(low, 0, 0);
  const n = Math.floor(3 + k * 16);
  for (let i = 0; i < n; i++) {
    const y = Math.floor(hash2(i, Math.floor(time * 30) + seed) * H), h = 1 + Math.floor(hash2(i, 7 + seed) * (4 + k * 18)), dx = Math.round((hash2(i, Math.floor(time * 24)) - 0.5) * (6 + k * 70));
    g.drawImage(nhTmp, 0, y, W, h, dx, y, W, h);
  }
  for (let i = 0; i < Math.floor(k * 12); i++) {
    const x = hash2(i, Math.floor(time * 20) + 3) * W, y = hash2(i, Math.floor(time * 20) + 9) * H;
    g.fillStyle = i % 3 === 0 ? `rgba(255,63,192,${0.5 * k})` : i % 3 === 1 ? `rgba(63,224,255,${0.5 * k})` : `rgba(255,255,255,${0.4 * k})`;
    g.fillRect(Math.round(x), Math.round(y), 4 + (i * 13) % 40, 1 + (i % 3));
  }
  g.fillStyle = `rgba(0,0,0,${0.18 * k})`; for (let y = Math.floor(time * 40) % 3; y < H; y += 3) g.fillRect(0, y, W, 1);
}
function nhDrawWarp() {
  const w = NH.warp; if (!w) return;
  const k = w.phase === 'out' ? clamp(w.t / 0.75, 0, 1) : 1 - clamp(w.t / 0.6, 0, 1);
  nhGlitchScreen(k);
  if (w.phase === 'out' && k > 0.75) { g.fillStyle = `rgba(240,250,255,${(k - 0.75) * 3})`; g.fillRect(0, 0, W, H); }
  if (w.phase === 'in' && k > 0.5) { g.fillStyle = `rgba(240,250,255,${(k - 0.5) * 1.6})`; g.fillRect(0, 0, W, H); }
}

// ================================================================== glitch hints in the old world (subtle: a pixel, a hum)
const NH_HINTS = {
  C1: [{ x: 23 * 16 - 1, y: 16 * 16 + 5 }],
  K3: [{ x: 11 * 16 - 1, y: 7 * 16 + 9, hum: true }],
  M1: [{ x: 16, y: 12 * 16 + 7, scan: true }],
  C6: [{ x: 14 * 16 + 7, y: 19 * 16 + 2, crack: true, hum: true }],
};
function nhHintsEnter(def) { NH.hintT = rand(1, 3); }
function nhDrawHints() {
  const L = room && NH_HINTS[room.id]; if (!L) return;
  for (const h of L) {
    if (h.crack) {   // light leaking through the cracked rock hiding the portal
      if (room.grid[20 * room.w + 14] !== T_BREAK) continue;
      const on = hash2(Math.floor(time * 11), 5) < 0.45;
      for (let y = 0; y < 44; y += 1) { const x = h.x + Math.round(Math.sin(y * 0.9) * 1.5); if (hash2(y, 3) < 0.55 && on) { g.fillStyle = y % 7 === 0 ? NH_MG[3] : NH_CY[3]; g.fillRect(x, h.y + y, 1, 1); } }
      if (on) addLight(h.x, h.y + 22, 22, Math.floor(time * 3) % 2 ? '80,220,255' : '255,70,200', 0.5);
      continue;
    }
    const on = hash2(Math.floor(time * 9), h.x) < (h.scan ? 0.12 : 0.3);
    if (!on) continue;
    g.fillStyle = Math.floor(time * 13) % 2 ? NH_MG[3] : NH_CY[3]; g.fillRect(h.x, h.y, 1, 1);
    if (hash2(Math.floor(time * 9), 2) < 0.4) { g.fillStyle = NH_CY[4]; g.fillRect(h.x, h.y + 2, 1, 1); }
    addLight(h.x, h.y, 10, '120,220,255', 0.35);
  }
}
function nhUpdateHints(dt) {
  const L = room && NH_HINTS[room.id]; if (!L || state !== 'play') return;
  for (const h of L) {
    if (h.hum && Math.abs(P.x - h.x) < 70 && Math.abs(P.y - h.y) < 70 && (!h.crack || room.grid[20 * room.w + 14] === T_BREAK) && (NH.hum -= dt) <= 0) {
      NH.hum = 1.4; tone(55, 1.2, 0.022, 'sawtooth', 1.01); tone(82.5, 1.0, 0.012, 'square', 0.99);
    }
    if (h.scan && (NH.hintT -= dt) <= 0) { NH.hintT = rand(6, 11); NH.scanFlash = 0.12; nhSfx.glitch(0.25); }
  }
}

// ================================================================== c_hack: breakable walls light up under a scan overlay
function nhDrawScanTop() {
  if (NH.scanFlash > 0 && room && NH_HINTS[room.id]) { nhGlitchScreen(0.35, 4); }
  if (!room || !P || !charmOn('c_hack') || !['play', 'cut'].includes(state)) return;
  const R = room, ox = Math.round(cam.x), oy = Math.round(cam.y), px = P.x, py = P.y - 14;
  const pr = NH.pulse >= 0 ? NH.pulse * 320 : -1;
  if (pr > 0) {   // the scan pulse ring
    g.fillStyle = `rgba(63,224,255,${0.35 * (1 - NH.pulse)})`;
    for (let i = 0; i < 90; i++) { const a = i / 90 * 6.283; g.fillRect(Math.round(px - ox + Math.cos(a) * pr), Math.round(py - oy + Math.sin(a) * pr * 0.8), 2, 1); }
  }
  const tx0 = Math.max(0, Math.floor(cam.x / TILE)), tx1 = Math.min(R.w - 1, Math.ceil((cam.x + W) / TILE)), ty0 = Math.max(0, Math.floor(cam.y / TILE)), ty1 = Math.min(R.h - 1, Math.ceil((cam.y + H) / TILE));
  let cnt = 0, cxs = 0, cys = 0;
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    const t = R.grid[ty * R.w + tx]; if (t !== T_BREAK && t !== T_CRACK) continue;
    const cx = tx * TILE + 8, cy = ty * TILE + 8, d = Math.hypot(cx - px, cy - py);
    let a = d < 120 ? 1 - d / 160 : 0;
    if (pr > 0 && Math.abs(d - pr) < 60) a = Math.max(a, 1 - Math.abs(d - pr) / 60);
    const key = tx + ',' + ty; NH.seen = NH.seen || {}; if (a > 0.3) NH.seen[R.id + key] = time;
    const seenT = NH.seen[R.id + key]; if (seenT && time - seenT < 3) a = Math.max(a, 0.6 * (1 - (time - seenT) / 3));
    if (a <= 0.02) continue;
    const sx = tx * TILE - ox, sy = ty * TILE - oy;
    g.globalAlpha = a * (0.75 + 0.25 * Math.sin(time * 8 + tx)); g.fillStyle = t === T_CRACK ? NH_MG[3] : NH_CY[3];
    for (let i = 0; i < 16; i += 2) { g.fillRect(sx + i, sy, 1, 1); g.fillRect(sx + i, sy + 15, 1, 1); g.fillRect(sx, sy + i, 1, 1); g.fillRect(sx + 15, sy + i, 1, 1); }
    g.globalAlpha = a * 0.35; for (let i = -16; i < 16; i += 4) for (let j = 0; j < 16; j++) { const x = j + i + ((time * 8) | 0) % 4; if (x >= 0 && x < 16) g.fillRect(sx + x, sy + j, 1, 1); }
    g.globalAlpha = 1; cnt++; cxs += sx + 8; cys += sy;
  }
  if (cnt) { const x = Math.round(cxs / cnt), y = Math.round(cys / cnt) - 8, a = 0.6 + 0.4 * Math.sin(time * 6); g.globalAlpha = a; g.fillStyle = NH_CY[4]; g.fillRect(x - 1, y - 7, 2, 5); g.fillRect(x - 1, y, 2, 2); g.globalAlpha = 1; }
}
function nhUpdateScan(dt) {
  NH.scanFlash = Math.max(0, (NH.scanFlash || 0) - dt);
  if (!charmOn('c_hack')) { NH.pulse = -1; return; }
  NH.scanT += dt;
  if (NH.pulse >= 0) { NH.pulse += dt / 1.3; if (NH.pulse >= 1) NH.pulse = -1; }
  if (NH.scanT > 3.6) { NH.scanT = 0; NH.pulse = 0; if (room && room.grid.some(t => t === T_BREAK || t === T_CRACK)) tone(1760, 0.12, 0.02, 'sine', 1.5); }
}

// ================================================================== synthwave layer (arpeggios + bass on top of the ambient score)
const NH_MUS = { next: 0, step: 0 };
const NH_CHORDS = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]];   // Am  F  C  G
function nhMusic() {
  const ac = AC; if (!ac || muted || !MUSIC.gain || !nhIn() || !(state === 'play' || state === 'cut')) { if (ac) NH_MUS.next = ac.currentTime + 0.1; return; }
  const bossOn = !!(boss && boss.active && boss.alive), cyb = nhCyber(), bpm = bossOn ? (cyb ? 150 : 138) : 104, st16 = 60 / bpm / 4;
  if (NH_MUS.next < ac.currentTime - 0.25) NH_MUS.next = ac.currentTime + 0.05;
  const pat = [0, 1, 2, 3, 4, 3, 2, 1];
  while (NH_MUS.next < ac.currentTime + 0.15) {
    const d = Math.max(0, NH_MUS.next - ac.currentTime), s = NH_MUS.step, ch = NH_CHORDS[Math.floor(s / 16) % 4], root = cyb ? 207.65 : 220;
    const i = pat[s % 8], semi = ch[i % 3] + (i >= 3 ? 12 : 0);
    tone(root * Math.pow(2, semi / 12), st16 * 0.85, bossOn ? 0.02 : 0.013, cyb ? 'sawtooth' : 'square', 1, d, MUSIC.gain);
    if (s % 4 === 0) tone(root / 4 * Math.pow(2, ch[0] / 12), st16 * 3.5, bossOn ? 0.06 : 0.045, 'sawtooth', 1, d, MUSIC.gain);
    if (bossOn && s % 4 === 0) tone(62, 0.14, 0.12, 'sine', 0.35, d, MUSIC.gain);
    if (!bossOn && s % 32 === 0) tone(root * 2 * Math.pow(2, ch[1] / 12), st16 * 12, 0.012, 'triangle', 1, d, MUSIC.gain);
    NH_MUS.step++; NH_MUS.next += st16;
  }
}

// ================================================================== global per-frame work (every room)
function nhUpdateGlobal(dt) {
  if (!room || !P) return;
  nhUpdateWarp(dt); nhUpdateHints(dt); nhUpdateScan(dt); nhMusic();
}

// ================================================================== enemies
Object.assign(ENEMY, {
  nh_drone: { hp: 70, cinders: 95, speed: 72, aggro: 190, range: 170, poise: 8, stance: 30, dmg: { zap: 22 }, cool: [1.9, 2.8], flying: true, ranged: 'nh_zap' },
  nh_cyborg: { hp: 150, cinders: 150, speed: 44, aggro: 170, range: 52, poise: 26, stance: 95, dmg: { slash: 34, dash: 38 }, cool: [0.9, 1.6], lunge: { slash: 70, dash: 250 } },
  nh_turret: { hp: 95, cinders: 110, speed: 0, aggro: 220, range: 230, poise: 999, stance: 70, dmg: { shot: 20 }, cool: [1.9, 2.7], ranged: 'nh_shot' },
});
Object.assign(ATTACK_TAGS, { nh_drone: ['zap'], nh_cyborg: ['slash', 'dash'], nh_turret: ['fire'] });

// ---- security drone: sweeps a searchlight; seeing you sounds the alarm (one reinforcement warps in), then it zaps
ENEMY_CLASSES.nh_drone = class extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.sweep = rand(0, 6); this.tp = rand(0, 6); this.called = false; this.st2 = 'patrol'; this.t2 = 0; }
  spotted() {
    const dx = P.x - this.x, dy = P.y - 14 - this.y, d = Math.hypot(dx, dy);
    if (P.state === 'dead' || d > 160) return false;
    if (d < 70 && lineOfSight(this.x, this.y, P.x, P.y - 14)) return true;
    const la = Math.PI / 2 - this.face * (0.55 + Math.sin(this.sweep) * 0.35), a = Math.atan2(dy, dx);
    let da = a - la; while (da > Math.PI) da -= 6.283; while (da < -Math.PI) da += 6.283;
    return Math.abs(da) < 0.34 && lineOfSight(this.x, this.y, P.x, P.y - 14);
  }
  hit(info) { super.hit(info); if (this.alive && this.st2 === 'patrol') this.alarm(); }
  alarm() { if (this.st2 !== 'patrol') return; this.st2 = 'alarm'; this.t2 = 1.1; this.aggro = true; nhSfx.alarm(); toast('ALERT // SECURITY BREACH', 1.4); }
  updateFlying(dt) {
    const c = this.cfg; this.tp += dt; this.cool -= dt; this.sweep += dt * 1.6;
    const clampFly = () => { this.x = clamp(this.x, 10, room.pw - 10); this.y = clamp(this.y, 14, room.ph - 16); };
    if (this.state === 'hurt' || this.state === 'stagger' || this.state === 'parried') {
      this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
      if (this.state !== 'hurt') { this.t -= dt; this.y += 20 * dt; }
      if (this.state === 'hurt' ? this.anim.done : this.t <= 0) { this.state = 'idle'; this.anim.set('fly', true); this.cool = Math.max(this.cool, 0.6); this.t = 0; }
      return;
    }
    if (this.st2 === 'patrol') {
      const tx = this.home + Math.sin(this.tp * 0.6) * 46, ty = this.hy + Math.sin(this.tp * 1.7) * 5;
      this.face = Math.cos(this.tp * 0.6) >= 0 ? 1 : -1;
      this.vx = approach(this.vx, clamp((tx - this.x) * 2, -40, 40), 120 * dt); this.vy = approach(this.vy, clamp((ty - this.y) * 2, -30, 30), 120 * dt);
      this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
      if (this.spotted()) this.alarm();
      if (this.anim.tag !== 'fly') this.anim.set('fly', true);
      return;
    }
    if (this.st2 === 'alarm') {
      this.t2 -= dt; this.facePlayer(); this.vx *= Math.pow(0.1, dt); this.vy *= Math.pow(0.1, dt);
      if (this.anim.tag !== 'alert' && this.sh.has('alert')) this.anim.set('alert', true);
      addLight(this.x, this.y, 40, '255,50,70', 0.8 * (Math.floor(time * 8) % 2));
      if (this.t2 <= 0) { this.st2 = 'hunt'; this.cool = 0.8; this.anim.set('fly', true); if (!this.called) { this.called = true; nhReinforce(this); } }
      return;
    }
    // hunt: hold a firing position above and to the side; charge, then zap
    if (this.state === 'attack') {
      this.t2 -= dt; this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.x += this.vx * dt; this.y += this.vy * dt; clampFly(); this.facePlayer();
      addLight(this.x + this.face * 6, this.y + 3, 16 + (0.5 - this.t2) * 40, '80,210,255', 0.9);
      if (this.t2 <= 0 && !this.spawned) {
        this.spawned = true; const a = Math.atan2(P.y - 14 - this.y, P.x - this.x);
        nhBolt(this, this.x + this.face * 6, this.y + 3, a, 190, c.dmg.zap * NGP.dmg, 'cy'); nhSfx.shot();
      }
      if (this.t2 <= -0.35) { this.state = 'idle'; this.anim.set('fly', true); this.cool = rand(...c.cool); }
      return;
    }
    const side = P.x < this.x ? 1 : -1, tx = P.x + side * 76, ty = P.y - 62 + Math.sin(this.tp * 2.2) * 8;
    this.facePlayer();
    this.vx = approach(this.vx, clamp((tx - this.x) * 1.8, -c.speed, c.speed), 180 * dt); this.vy = approach(this.vy, clamp((ty - this.y) * 1.8, -c.speed, c.speed), 180 * dt);
    this.x += this.vx * dt; this.y += this.vy * dt; clampFly();
    if (solidAtPx(this.x, this.y)) { this.x -= this.vx * dt; this.y -= this.vy * dt; }
    if (this.cool <= 0 && Math.abs(P.x - this.x) < c.range && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
      this.state = 'attack'; this.atk = 'zap'; this.spawned = false; this.t2 = 0.5; if (this.sh.has('fire')) this.anim.set('fire', false); nhSfx.charge();
    }
  }
  draw() {
    // the searchlight cone (patrol: cold white; alarm: red)
    if (this.alive && (this.st2 === 'patrol' || this.st2 === 'alarm')) {
      const la = this.st2 === 'alarm' ? Math.atan2(P.y - 14 - this.y, P.x - this.x) : Math.PI / 2 - this.face * (0.55 + Math.sin(this.sweep) * 0.35);
      const col = this.st2 === 'alarm' ? (Math.floor(time * 8) % 2 ? '255,40,60' : '255,120,120') : '190,230,255';
      g.fillStyle = `rgba(${col},0.10)`; g.beginPath(); g.moveTo(this.x, this.y + 3);
      g.lineTo(this.x + Math.cos(la - 0.3) * 150, this.y + 3 + Math.sin(la - 0.3) * 150); g.lineTo(this.x + Math.cos(la + 0.3) * 150, this.y + 3 + Math.sin(la + 0.3) * 150); g.closePath(); g.fill();
      addLight(this.x + Math.cos(la) * 60, this.y + Math.sin(la) * 60, 44, col, 0.35);
    }
    super.draw();
    if (!this.sh.ok && this.alive) { nhRect(this.x - 7, this.y - 4, 14, 8, NH_NV[4]); nhRect(this.x - 2, this.y - 1, 4, 3, this.st2 === 'patrol' ? NH_CY[4] : NH_RD[2]); }
    if (this.alive) addLight(this.x, this.y, 22, this.st2 === 'patrol' ? '80,210,255' : '255,60,80', 0.55);
  }
};
function nhReinforce(src) {
  if (NHR.rf >= 3 || !room) return;
  for (const dx of [-90, 90, -120, 120, -60, 60, -150, 150]) {
    const x = P.x + dx; if (x < 24 || x > room.pw - 24) continue;
    const tx = Math.floor(x / TILE);
    for (let ty = Math.floor((P.y - 40) / TILE); ty < Math.min(room.h - 1, Math.floor((P.y + 60) / TILE)); ty++) {
      const below = nhCell(tx, ty + 1);
      if (nhCell(tx, ty) === T_EMPTY && nhCell(tx, ty - 1) === T_EMPTY && isSolidT(below) && below !== NH_T_VOID && below !== NH_T_DEL && !isSolidT(nhCell(tx - 1, ty)) && !isSolidT(nhCell(tx + 1, ty))) {
        const e = makeEnemy('nh_cyborg', tx * TILE + 8, (ty + 1) * TILE, `${room.id}:rf${++NHR.rf}`);
        e.warp = 0.8; e.state = 'warp'; e.aggro = true; enemies.push(e);
        nhSfx.glitch(0.7); spawnFx(fxOr('nh_warp'), e.x, e.y, 1, null, { bottom: true });
        return;
      }
    }
  }
}

// ---- chrome hollow: a cyborg husk with arm blades; dash-slashes from mid range
ENEMY_CLASSES.nh_cyborg = class extends Enemy {
  hit(info) { if (this.state === 'warp') return; super.hit(info); }
  hurtbox() { return this.state === 'warp' ? null : super.hurtbox(); }
  update(dt) {
    if (this.state === 'warp') {
      this.warp -= dt; this.anim.update(dt); this.gravity(dt);
      if (Math.random() < 0.6) particles.push({ x: this.x + rand(-6, 6), y: this.y - rand(0, 40), vx: 0, vy: -rand(20, 60), life: 0.3, kind: Math.random() < 0.5 ? 'nh_pink' : 'nh_mote' });
      if (this.warp <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.5; }
      return;
    }
    const c = this.cfg, adx = Math.abs(P.x - this.x);
    if (this.alive && this.aggro && ['idle', 'walk'].includes(this.state) && this.cool <= 0 && adx > 64 && adx < 132 && Math.abs(P.y - this.y) < 30 && ledgeAhead(this, sign(P.x - this.x)) && lineOfSight(this.x, this.y - 20, P.x, P.y - 16)) {
      this.startAttack('dash');
    }
    super.update(dt);
    if (this.state === 'attack' && this.vx && (!ledgeAhead(this, sign(this.vx)) || wallAt(this, sign(this.vx)))) this.vx = 0;   // never dash off a roof
    if (this.alive && this.state !== 'dead') addLight(this.x + this.face * 4, this.y - 36, 18, '255,60,190', 0.5);
  }
  draw() {
    if (this.state === 'warp') {
      const k = clamp(1 - this.warp / 0.8, 0, 1);
      if (this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x + Math.round((Math.random() - 0.5) * 6 * (1 - k)), this.y, this.face, { alpha: k, flash: 1 - k, flashColor: '#3fe0ff' });
      for (let y = 0; y < 60; y += 3) if (Math.random() < 0.6) nhRect(this.x + rand(-8, 8), this.y - y, rand(1, 6), 1, Math.random() < 0.5 ? NH_CY[3] : NH_MG[3]);
      return;
    }
    super.draw();
  }
};

// ---- turret node: deploys when you come close, tracks you with a laser sight, fires a 3-round burst
ENEMY_CLASSES.nh_turret = class extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.state = 'dormant'; this.anim.set(this.sh.has('closed') ? 'closed' : 'idle', true); this.ang = this.face > 0 ? 0 : Math.PI; this.shots = 0; this.t2 = 0; }
  get pivot() { return { x: this.x, y: this.y - 15 }; }
  update(dt) {
    const c = this.cfg;
    this.flash = Math.max(0, this.flash - dt * 5); this.stance = Math.max(0, this.stance - dt * 6); this.dmgT -= dt;
    this.anim.update(dt);
    if (this.state === 'dead') { if (this.anim.done && !this.gone) { this.gone = true; spawnFx(fxOr('nh_blast', 'death_ash', 'dust'), this.x, this.y - 10, 1); nhSfx.blast(); } return; }
    const pv = this.pivot, dx = P.x - pv.x, dy = P.y - 14 - pv.y, d = Math.hypot(dx, dy);
    const see = d < c.aggro && P.state !== 'dead' && lineOfSight(pv.x, pv.y, P.x, P.y - 14);
    this.cool -= dt;
    switch (this.state) {
      case 'dormant':
        if (see && d < 170) { this.state = 'deploy'; if (this.sh.has('deploy')) this.anim.set('deploy', false); this.t2 = 0.5; tone(440, 0.3, 0.04, 'square', 2); }
        return;
      case 'deploy': this.t2 -= dt; if (this.t2 <= 0 && (this.anim.done || !this.sh.has('deploy'))) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.6; } return;
      case 'stagger': case 'parried': case 'hurt':
        this.t -= dt; if (this.t <= 0 || this.state === 'hurt') { this.state = 'idle'; this.anim.set('idle', true); this.cool = Math.max(this.cool, 0.5); } return;
    }
    if (this.state === 'idle') {
      if (see) { let da = Math.atan2(dy, dx) - this.ang; while (da > Math.PI) da -= 6.283; while (da < -Math.PI) da += 6.283; this.ang += clamp(da, -2.6 * dt, 2.6 * dt); }
      this.face = Math.cos(this.ang) >= 0 ? 1 : -1;
      if (see && this.cool <= 0 && d < c.range) { this.state = 'charge'; this.t2 = 0.65; nhSfx.charge(); }
    } else if (this.state === 'charge') {
      this.t2 -= dt; addLight(pv.x + Math.cos(this.ang) * 12, pv.y + Math.sin(this.ang) * 12, 14 + (0.65 - this.t2) * 30, '255,50,70', 0.9);
      if (this.t2 <= 0) { this.state = 'burst'; this.shots = 3; this.t2 = 0; }
    } else if (this.state === 'burst') {
      this.t2 -= dt;
      if (this.t2 <= 0 && this.shots > 0) { this.shots--; this.t2 = 0.13; nhBolt(this, pv.x + Math.cos(this.ang) * 13, pv.y + Math.sin(this.ang) * 13, this.ang + rand(-0.03, 0.03), 250, c.dmg.shot * NGP.dmg, 'rd', 2); nhSfx.shot(); this.recoil = 1; }
      if (this.shots <= 0 && this.t2 <= 0) { this.state = 'idle'; this.cool = rand(...c.cool); }
    }
    this.recoil = Math.max(0, (this.recoil || 0) - dt * 8);
  }
  breakStance() { super.breakStance(); this.t = 1.6; }
  die(info) { super.die(info); this.vx = 0; }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.18 + 0.12 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'dead' && this.anim.done) return;
    const pv = this.pivot;
    if (this.alive && this.state !== 'dormant' && this.state !== 'deploy') {
      if (this.state === 'charge') {   // laser sight to the first wall
        const cx = Math.cos(this.ang), cy = Math.sin(this.ang); g.fillStyle = `rgba(255,50,70,${0.4 + 0.4 * Math.sin(time * 40)})`;
        for (let s = 14; s < 260; s += 2) { const x = pv.x + cx * s, y = pv.y + cy * s; if (solidAtPx(x, y)) break; g.fillRect(Math.round(x), Math.round(y), 1, 1); }
      }
      const r = 12 - (this.recoil || 0) * 3, cx = Math.cos(this.ang), cy = Math.sin(this.ang);
      for (let s = 3; s < r; s++) { g.fillStyle = s > r - 2 ? NH_RD[3] : NH_NV[5]; g.fillRect(Math.round(pv.x + cx * s), Math.round(pv.y + cy * s), 2, 2); }
    }
    if (this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    else { nhRect(this.x - 8, this.y - 12, 16, 12, NH_NV[4]); nhRect(this.x - 3, this.y - 18, 6, 6, NH_NV[5]); }
    if (this.alive && this.state !== 'dormant') addLight(pv.x, pv.y, 18, this.state === 'charge' || this.state === 'burst' ? '255,60,80' : '80,210,255', 0.5);
    if (this.critable()) { g.fillStyle = '#ffd070'; const y = Math.round(this.y - 30 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(this.x) - 1, y, 3, 3); }
    if (this.hp < this.maxHp && this.alive) { const w = 20, x = Math.round(this.x - w / 2), y = Math.round(this.y - 30); g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y - 1, w + 2, 4); g.fillStyle = '#8a1a1a'; g.fillRect(x, y, Math.max(0, w * this.hp / this.maxHp), 2); }
  }
};

// ================================================================== boss effect lists (missiles, waves, strikes, blades, walls, rain, rings)
const nhBD = d => BOSS_DMG * d * NGP.dmg;
function nhUpdateBossFx(dt) {
  const B = boss;
  // ---- missiles: rise, hang (the landing spot is marked), dive
  for (const m of NHR.missiles) {
    m.t += dt;
    if (m.st === 'rise') { m.vy += 320 * dt; m.x += m.vx * dt; m.y += m.vy * dt; if (m.t > 0.42) { m.st = 'hang'; m.vx = 0; m.vy = 0; } if (Math.random() < 0.8) particles.push({ x: m.x, y: m.y + 3, vx: rand(-10, 10), vy: rand(10, 40), life: 0.5, kind: 'dust' }); }
    else if (m.st === 'hang') { if (m.t >= m.delay) { m.st = 'dive'; const a = Math.atan2(m.ty - 4 - m.y, m.tx - m.x); m.vx = Math.cos(a) * 420; m.vy = Math.sin(a) * 420; nhSfx.missile(); } }
    else if (m.st === 'dive') {
      m.x += m.vx * dt; m.y += m.vy * dt;
      if (Math.random() < 0.9) particles.push({ x: m.x - m.vx * 0.02, y: m.y - m.vy * 0.02, vx: rand(-10, 10), vy: rand(-10, 10), life: 0.35, kind: 'nh_pink' });
      if (m.y >= m.ty - 4 || solidAtPx(m.x, m.y)) { m.st = 'boom'; nhBlast(m.x, Math.min(m.y, m.ty), 22, 40, m.src); }
    }
    if (m.st !== 'boom') addLight(m.x, m.y, 22, '255,80,120', 0.8);
  }
  NHR.missiles = NHR.missiles.filter(m => m.st !== 'boom');
  // ---- ground waves (enforcer stomp): low, jumpable
  for (const w of NHR.walls) {
    w.t += dt; w.x += w.vx * dt;
    if (w.kind === 'wave') {
      if (w.x < w.x0 || w.x > w.x1 || w.t > 3) w.dead = true;
      if (overlap(rect(w.x - 6, w.y - w.h, w.x + 6, w.y), playerHurtbox())) hurtPlayer(nhBD(w.dmg), sign(w.vx), w.id, { src: w.src });
      addLight(w.x, w.y - 6, 30, '255,70,190', 0.7);
    } else if (w.kind === 'fire') {   // SAINT-0's firewalls: march across the floor, low enough to leap
      if ((w.vx > 0 && w.x > w.x1) || (w.vx < 0 && w.x < w.x0)) w.dead = true;
      w.k = Math.min(1, w.t / 0.5);
      if (w.k >= 1 && overlap(rect(w.x - 7, w.y - w.h, w.x + 7, w.y), playerHurtbox())) hurtPlayer(nhBD(w.dmg), sign(w.vx), w.id, { src: w.src });
      for (let y = w.y - w.h + 8; y < w.y; y += 18) addLight(w.x, y, 26, '255,60,190', 0.6);
    }
  }
  NHR.walls = NHR.walls.filter(w => !w.dead);
  // ---- orbital strikes: a mark tracks the floor, then a beam falls from the ceiling
  for (const m of NHR.marks) {
    m.t += dt;
    if (!m.hit && m.t >= m.delay) { m.hit = true; NHR.beams.push({ x: m.x, y0: m.y0, y1: m.y1, t: 0, life: 0.34, w: m.w, dmg: m.dmg, id: ++hazardId, src: m.src }); nhSfx.beam(); shake = Math.max(shake, 4); for (let i = 0; i < 12; i++) particles.push({ x: m.x + rand(-8, 8), y: m.y1 - 2, vx: rand(-90, 90), vy: -rand(40, 160), g: 380, life: 0.5, kind: 'nh_white' }); }
  }
  NHR.marks = NHR.marks.filter(m => !m.hit);
  for (const b of NHR.beams) {
    b.t += dt;
    if (b.t < b.life * 0.8 && overlap(rect(b.x - b.w / 2, b.y0, b.x + b.w / 2, b.y1), playerHurtbox())) hurtPlayer(nhBD(b.dmg), P.x < b.x ? -1 : 1, b.id, { src: b.src });
    addLight(b.x, (b.y0 + b.y1) / 2, 90, '120,230,255', 1 - b.t / b.life);
  }
  NHR.beams = NHR.beams.filter(b => b.t < b.life);
  // ---- binary rain columns (SAINT-0 phase 3)
  for (const r of NHR.rains) {
    r.t += dt;
    if (r.t >= r.warn && r.t < r.warn + r.on && overlap(rect(r.x - 7, r.y0, r.x + 7, r.y1), playerHurtbox())) hurtPlayer(nhBD(r.dmg), P.x < r.x ? -1 : 1, r.id, { src: r.src });
    if (r.t >= r.warn && r.t < r.warn + r.on) addLight(r.x, r.y1 - 30, 40, '40,40,90', 0.5);
  }
  NHR.rains = NHR.rains.filter(r => r.t < r.warn + r.on + 0.2);
  // ---- null rings (roll through them)
  for (const r of NHR.rings) {
    r.r += r.v * dt;
    const d = Math.hypot(P.x - r.x, (P.y - 13) - r.y);
    if (Math.abs(d - r.r) < 8 && P.y - 26 < r.y + 12) hurtPlayer(nhBD(r.dmg), sign(P.x - r.x), r.id, { src: r.src });
  }
  NHR.rings = NHR.rings.filter(r => r.r < r.max);
  if (B && B.kind === 'saint0') nhUpdateSaintFx(dt, B);
}
function nhBlast(x, y, r, dmg, src) {
  nhSfx.blast(); shake = Math.max(shake, 5);
  const f = spawnFx(fxOr('nh_blast', 'shockwave'), x, y, 1, null, fxSheet('nh_blast').ok ? { center: true, bottom: false } : {});
  hazards.push({ x, y: y + 6, w: r * 2, h: r * 2 + 6, dmg: nhBD(dmg), id: ++hazardId, life: 0.14, t: 0, update() {} });
  for (let i = 0; i < 14; i++) particles.push({ x, y: y - 4, vx: rand(-110, 110), vy: -rand(30, 170), g: 380, life: rand(0.3, 0.7), kind: i % 3 ? 'nh_pink' : 'fire' });
  addLight(x, y - 8, 70, '255,90,160', 1);
}
function nhDrawBossFx() {
  const ms = fxSheet('nh_missile');
  for (const m of NHR.missiles) {
    if (m.st === 'hang' || m.st === 'dive') {   // the landing reticle
      const k = m.st === 'dive' ? 1 : clamp((m.t - 0.42) / Math.max(0.1, m.delay - 0.42), 0, 1), a = 0.45 + 0.45 * Math.sin(time * 30);
      g.globalAlpha = a; g.fillStyle = NH_RD[2 + (k > 0.7 ? 1 : 0)];
      const x = Math.round(m.tx), y = Math.round(m.ty) - 1, r = Math.round(12 - k * 5);
      g.fillRect(x - r, y, r * 2 + 1, 1); g.fillRect(x, y - 3, 1, 3); g.fillRect(x - r, y - 2, 1, 2); g.fillRect(x + r, y - 2, 1, 2);
      g.globalAlpha = 1;
    }
    const ang = Math.atan2(m.vy, m.vx || 0.001);
    if (ms.ok) drawRotated(ms, ms.first(Object.keys(ms.tags)[0]) + Math.floor(time * 16) % 4, m.x, m.y, m.st === 'hang' ? Math.PI / 2 : ang);
    else { nhRect(m.x - 2, m.y - 2, 4, 4, NH_NV[5]); nhRect(m.x - 1, m.y - 1, 2, 2, NH_RD[3]); }
  }
  for (const w of NHR.walls) {
    if (w.kind === 'wave') {
      const x = Math.round(w.x), y = Math.round(w.y);
      g.fillStyle = NH_MG[2]; g.fillRect(x - 3, y - w.h + 4, 6, w.h - 4); g.fillStyle = NH_MG[4]; g.fillRect(x - 1, y - w.h, 2, w.h);
      for (let k = 0; k < 4; k++) { g.fillStyle = NH_CY[4]; g.fillRect(x - 4 + ((k * 3 + Math.floor(time * 30)) % 8), y - 2 - k * 3, 1, 1); }
    } else if (w.kind === 'fire') {
      const x = Math.round(w.x), cyb = nhCyber(), hh = Math.round(w.h * w.k);
      for (let y = 0; y < hh; y += 3) {
        const r = hash2(Math.floor(y / 3), Math.floor(time * 14) + w.id % 97), off = Math.round((r - 0.5) * 6);
        g.fillStyle = cyb ? (r < 0.4 ? '#101840' : '#c21d97') : r < 0.3 ? NH_MG[5] : r < 0.7 ? NH_MG[3] : NH_RD[2];
        g.fillRect(x - 5 + off, Math.round(w.y) - y - 3, 3 + Math.floor(r * 6), 2);
      }
      g.fillStyle = cyb ? '#101840' : NH_MG[4]; g.fillRect(x - 7, Math.round(w.y) - hh, 1, hh); g.fillRect(x + 7, Math.round(w.y) - hh, 1, hh);
    }
  }
  for (const m of NHR.marks) {   // orbital: reticle on the floor + a hairline from the ceiling
    const k = clamp(m.t / m.delay, 0, 1), a = 0.35 + 0.55 * k * (0.5 + 0.5 * Math.sin(time * 40)), cyb = nhCyber();
    g.globalAlpha = a; g.fillStyle = cyb ? '#1a2360' : NH_CY[3 + (k > 0.7 ? 1 : 0)];
    const x = Math.round(m.x), r = Math.round(m.w / 2 + 6 - k * 6);
    g.fillRect(x - r, m.y1 - 1, r * 2 + 1, 1); g.fillRect(x - r, m.y1 - 3, 1, 2); g.fillRect(x + r, m.y1 - 3, 1, 2);
    if (k > 0.35) for (let y = m.y0; y < m.y1; y += 4) g.fillRect(x, y, 1, 2);
    g.globalAlpha = 1;
  }
  for (const b of NHR.beams) {
    const k = 1 - b.t / b.life, cyb = nhCyber(), w = Math.round(b.w * (0.6 + 0.4 * k)), x = Math.round(b.x);
    g.globalAlpha = 0.5 * k; g.fillStyle = cyb ? '#1a2360' : NH_CY[2]; g.fillRect(x - w / 2 - 3, b.y0, w + 6, b.y1 - b.y0);
    g.globalAlpha = k; g.fillStyle = cyb ? '#0b1030' : NH_CY[4]; g.fillRect(x - w / 2, b.y0, w, b.y1 - b.y0);
    g.fillStyle = cyb ? '#ff3fc0' : '#ffffff'; g.fillRect(x - 2, b.y0, 4, b.y1 - b.y0);
    g.globalAlpha = 1;
  }
  for (const r of NHR.rains) {
    const cyb = nhCyber(), x = Math.round(r.x);
    if (r.t < r.warn) { const a = 0.25 + 0.4 * (r.t / r.warn) * (0.5 + 0.5 * Math.sin(time * 30)); g.globalAlpha = a; g.fillStyle = cyb ? '#1a2360' : NH_CY[3]; for (let y = r.y0; y < r.y1; y += 6) g.fillRect(x - 7, y, 1, 3), g.fillRect(x + 7, y, 1, 3); g.globalAlpha = 1; continue; }
    for (let y = r.y0 - ((time * 260) % 12); y < r.y1; y += 6) {
      const q = hash2(Math.floor(y / 6), r.id % 50 + Math.floor(time * 20));
      g.fillStyle = cyb ? (q < 0.5 ? '#0b1030' : '#3a45a0') : (q < 0.5 ? NH_CY[4] : NH_CY[3]);
      if (q < 0.5) g.fillRect(x - 3, Math.round(y), 2, 5); else { g.fillRect(x - 3, Math.round(y), 1, 5); g.fillRect(x - 1, Math.round(y), 1, 5); }
      if (q > 0.75) g.fillRect(x + 2, Math.round(y), 2, 5);
    }
  }
  for (const r of NHR.rings) {
    const a = 1 - r.r / r.max, n = Math.ceil(r.r * 2 * Math.PI / 2), cyb = nhCyber();
    for (let k = 0; k < n; k++) {
      const t = k / n * Math.PI * 2, x = r.x + Math.cos(t) * r.r, y = r.y + Math.sin(t) * r.r * 0.5;
      if (y < r.y - 2) continue;
      g.fillStyle = cyb ? `rgba(16,24,64,${a})` : `rgba(255,120,230,${0.9 * a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1);
    }
  }
  if (boss && boss.kind === 'saint0') nhDrawSaintFx(boss);
}

// ================================================================== THE ENFORCER MECH (mini-boss, NH5)
BOSS_INFO.enforcer = { name: 'The Enforcer Mech', hp: 2200, cinders: 6500, reward: ['emberstone', 'shard'], quote: 'CURFEW IS IN EFFECT. COMPLIANCE IS MANDATORY.' };
function nhStompWaves(b) {
  const x = b.x + b.face * 34;
  spawnFx('shockwave', x, b.floor, 1); nhSfx.thud(); shake = 9;
  for (const d of [-1, 1]) NHR.walls.push({ kind: 'wave', x, x0: b.L - 40, x1: b.R + 40, y: b.floor, vx: d * (b.phase === 2 ? 205 : 175), h: 13, t: 0, dmg: 30, id: ++hazardId, src: b });
}
function nhMissiles(b, at) {
  const n = b.phase === 2 ? 6 : 4, lead = P.vx * 0.35;
  for (let k = 0; k < n; k++) {
    const tx = clamp(P.x + lead + (k - (n - 1) / 2) * 42 + rand(-8, 8), 3 * TILE + 12, 41 * TILE - 12);
    NHR.missiles.push({ x: at.x, y: at.y, vx: rand(-60, 60) - b.face * 30, vy: -rand(190, 250), t: 0, delay: 0.75 + k * 0.17, tx, ty: b.floor, st: 'rise', id: ++hazardId, src: b });
  }
  nhSfx.missile(); for (let i = 0; i < 10; i++) particles.push({ x: at.x, y: at.y, vx: rand(-40, 40), vy: -rand(20, 80), life: 0.6, kind: 'dust' });
}
class NhEnforcer extends MetaBoss {
  get L() { return 3 * TILE + 46; }
  get R() { return 41 * TILE - 46; }
  update(dt) {
    if (this.state === 'guard' && this.guardHit) { this.guardHit = false; this.start('bash'); }
    super.update(dt);
    if (this.state === 'attack' && this.atk === 'bash' && this.anim.i >= 4 && this.anim.i <= 7 && Math.random() < 0.7)
      particles.push({ x: this.x - this.face * 20, y: this.floor - 2, vx: -this.face * rand(40, 120), vy: -rand(10, 50), g: 300, life: 0.4, kind: 'dust' });
  }
  canStagger() { return !(this.state === 'attack' && ['missiles', 'stomp'].includes(this.atk)); }
  draw() {
    super.draw();
    if (!this.alive) return;
    const m = this.sh.meta, vis = m && m.visor ? metaPoint(this.sh, this, m.visor) : { x: this.x + this.face * 10, y: this.y - 74 };
    addLight(vis.x, vis.y, 30, this.phase === 2 ? '255,50,70' : '255,60,190', 0.9);
    if (this.state === 'guard') addLight(this.x + this.face * 30, this.y - 40, 50, '80,210,255', 0.6);
  }
}
function makeEnforcer(x, y) {
  return new NhEnforcer('enforcer', x, y, {
    sheets: ['enforcer', 'enforcer_p2'], stanceMax: 300, walkSpeed: 40, prefer: 64, p2at: 0.5, p2speed: 1.18, p2tag: 'missiles', critRange: 72,
    introTag: 'stomp', cool1: [1.0, 1.6], cool2: [0.55, 1.0], victory: 'ENFORCER DECOMMISSIONED', deathParticle: 'nh_mote',
    weights(d, p2) {
      if (d < 80) return p2 ? { sweep: 2.2, bash: 1.4, stomp: 1.7, missiles: 0.6 } : { sweep: 2.2, bash: 1.1, stomp: 1.0, guard: 1.2, missiles: 0.35 };
      if (d < 170) return { bash: 2.0, missiles: p2 ? 1.6 : 1.0, walk: 1.0, stomp: 0.5 };
      return { missiles: p2 ? 2.0 : 1.4, bash: 1.6, walk: 1.4 };
    },
    chains: { sweep(d) { return d < 92 ? (this.phase === 2 ? 'stomp' : 'bash') : 'missiles'; }, bash: d => d < 92 ? 'sweep' : null, stomp: 'missiles' },
    moves: {
      bash: { dmg: [52], shake: 5, step: 175, body: true },
      sweep: { dmg: [44], parry: true, step: 30, shake: 3 },
      stomp: { dmg: [58], shake: 9, on: { 6() { nhStompWaves(this); } } },
      missiles: { dmg: [], spawn(at) { nhMissiles(this, at); } },
    },
    wake() { return P.x > 4 * TILE + 20 && P.x < 40 * TILE && P.ground; },
    onIntro() { nhSfx.alarm(); },
    ambient() { if (this.phase === 2 && Math.random() < 0.3) particles.push({ x: this.x - this.face * rand(4, 20), y: this.y - rand(50, 80), vx: rand(-10, 10), vy: -rand(20, 50), life: 0.6, kind: 'dust' }); },
    onPhase2() {
      shake = 10; nhSfx.blast(); nhSfx.glitch(1);
      for (let i = 0; i < 24; i++) particles.push({ x: this.x + this.face * rand(10, 40), y: this.y - rand(10, 70), vx: this.face * rand(40, 180), vy: -rand(40, 160), g: 420, life: rand(0.6, 1.2), kind: i % 2 ? 'rock' : 'nh_mote' });
    },
    onDeath() { NHR.missiles = []; NHR.walls = []; victoryBanner = { text: 'ENFORCER DECOMMISSIONED', t: 0 }; setTimeout(() => nhSfx.blast(), 900); },
  });
}
BOSS_SPAWN.enforcer = (cx, fy) => makeEnforcer(cx, fy);
BOSS_CUTS.enforcer = b => [
  act(() => { b.anim.set('idle', true); b.face = -1; }),
  bossPan(b, 50, 1.0),
  act(() => nhSfx.alarm()),
  say('ENFORCER', 'CURFEW IS IN EFFECT. PRESENT YOUR CITIZEN INDEX.'),
  act(() => { holdAnim(b, 'stomp'); }), wait(0.55),
  act(() => { nhSfx.thud(); shake = 9; spawnFx('shockwave', b.x - 30, b.floor, 1); }), wait(0.8),
];
PHASE2_LINES.enforcer = ['', 'The riot shield shears away. Its reactor vents run red.'];

// ================================================================== SAINT-0, THE NULL SAINT (NH7)
// A towering white-and-chrome AI angel: faceless visor, six wings of floating holographic panels, a halo of data rings,
// an energy lance. The body is a sprite (saint0 / saint0_wire, one rig -> identical proportions in every frame); the
// wings, halo and lance are drawn live from per-frame meta points (grip + lance angle, head, back, core).
// Phase 1: lance thrusts and sweeps, panel-wing blades, orbital lasers.  Phase 2 (66%): it deletes the floor and
// spawns firewalls.  Phase 3 (33%): it drags you into cyberspace (inverted wireframe arena) and becomes wireframe.
BOSS_INFO.saint0 = { name: 'SAINT-0, the Null Saint', hp: 4500, cinders: 22000, reward: ['w:saint_lance', 'sp:null_field', 'c_neon'],
  quote: '“THE HALLOW IS SAVED. AS DATA.”' };
const NH_S0 = { P2: 0.66, P3: 0.33, FLOOR_X0: 4, FLOOR_X1: 36 };
const NH_S0_ANIM = { thrust: 'thrust', sweep: 'sweep', wings: 'wings', orbital: 'cast', delete: 'delete', firewall: 'delete', rain: 'cast', ring: 'wings' };
const NH_S0_DMG = { thrust: 50, sweep: 44 };
class NhSaint extends BossBase {
  constructor(x, y) {
    super('saint0', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.saint0.hp * NGP.hp);
    const meta = ASSETS.saint0_meta;
    this.sheets = [sheet('saint0', { meta }), sheet('saint0_wire', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant';
    Object.assign(this, { stanceMax: 440, critRange: 84, hoverH: 7, descend: 1, wing: 0, halo: 0, lanceOn: false, visible: false, alpha: 1,
      q: [], cool: 1, last: null, speed: 1, chain: 0, panelsOut: 0, regrow: 0, glitchT: 0, cds: {}, face: -1, bob: 0, aim: null });
    this.y = this.floor - this.hoverH - 150;
  }
  get L() { return NH_S0.FLOOR_X0 * TILE + 26; }
  get R() { return NH_S0.FLOOR_X1 * TILE - 10; }
  fm(tag = this.anim.tag, i = this.anim.i) { const m = this.sh.meta, f = m && m.frames && m.frames[tag]; return f ? f[Math.min(i, f.length - 1)] : null; }
  pt(p, fb) { return p ? metaPoint(this.sh, this, p) : fb; }
  grip() { const f = this.fm(); return this.pt(f && f.g, { x: this.x + this.face * 20, y: this.y - 70 }); }
  lanceAng() {
    if (this.lockP && this.state === 'attack' && this.move === 'thrust') {   // aimed at where you stood when it glinted
      const G = this.grip(), d = Math.max(28, (this.lockP.x - G.x) * this.face), a = clamp(Math.atan2(this.lockP.y - G.y, d), 0.05, 1.1);
      return this.face > 0 ? a : Math.PI - a;
    }
    const f = this.fm(), a = (f ? f.a : 100) * Math.PI / 180; return this.face === this.sh.native ? a : Math.PI - a;
  }
  lanceLen() {
    const f = this.fm(); let L = (f ? f.l : 90) * (this.state === 'attack' && this.move === 'thrust' && this.inActive() ? 1.15 : 1);
    const a = this.lanceAng(), sn = Math.sin(a); if (sn > 0.05) { const G = this.grip(); L = Math.min(L, (this.floor - 2 - G.y) / sn); }   // never through the floor
    return Math.max(20, L);
  }
  head() { const f = this.fm(); return this.pt(f && f.h, { x: this.x + this.face * 4, y: this.y - 126 }); }
  back() { const f = this.fm(); return this.pt(f && f.b, { x: this.x - this.face * 6, y: this.y - 100 }); }
  core() { const f = this.fm(); return this.pt(f && f.c, { x: this.x + this.face * 3, y: this.y - 92 }); }
  win(tag = this.anim.tag) { const a = this.sh.meta && this.sh.meta.attacks && this.sh.meta.attacks[tag]; return a ? a.active : tag === 'thrust' ? [6, 8] : [5, 7]; }
  inActive() { const w = this.win(); return this.anim.i >= w[0] && this.anim.i <= w[1]; }
  spawnFrame(tag) { const s = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn[tag]; return s ? s.frame : 4; }
  hurtbox() {
    if (!this.alive || !this.visible || this.alpha < 0.5 || this.descend > 0.2) return null;
    const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 16, this.y - 124, this.x + 16, this.y - 12);
  }
  hit(info) { if (!this.visible || this.alpha < 0.5) return; super.hit(info); if (this.alive) this.glitchT = Math.max(this.glitchT, 0.12); }
  canStagger() { return this.descend <= 0 && ['idle', 'glide', 'attack'].includes(this.state) && !(this.state === 'attack' && ['orbital', 'delete', 'firewall', 'rain'].includes(this.move)); }
  setA(tag, loop = false) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, this.speed); }
  later(t, fn) { this.q.push({ t, fn }); }
  activate() {
    if (this.active || this.cutting) return;
    this.visible = true; super.activate();
    if (this.active && !this.cutting) { this.descend = 0; this.wing = 1; this.halo = 1; this.lanceOn = true; if (this.state === 'dormant') { this.state = 'idle'; this.setA('idle', true); this.cool = 0.9; } }   // intro already seen: start fighting
  }
  wakeCheck() { return P.x > 6 * TILE && P.ground && P.state !== 'dead'; }
  swapSheet(k) { if (this.sheets[k] && this.sheets[k].ok) { const a = this.anim; this.sh = this.sheets[k]; this.anim = new Anim(this.sh, a.tag, a.loop, a.speed); this.anim.i = Math.min(a.i, this.anim.n - 1); } }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt);
    this.bob += dt; this.glitchT = Math.max(0, this.glitchT - dt); this.regrow = Math.max(0, this.regrow - dt);
    if (this.regrow <= 0 && this.panelsOut > 0 && !NHR.blades.length) this.panelsOut = Math.max(0, this.panelsOut - dt * 8);
    const sink = this.state === 'stagger' ? 5 : 0;
    this.y = this.floor - this.hoverH + sink - Math.sin(this.bob * 1.7) * 2.5 - this.descend * 150;
    if (!this.active) { if (!this.cutting && this.wakeCheck()) this.activate(); return; }
    if (this.alive) { for (const e of this.q) { e.t -= dt; if (e.t <= 0 && !e.done) { e.done = true; e.fn(); } } this.q = this.q.filter(e => !e.done); }
    for (const k in this.cds) this.cds[k] -= dt;
    switch (this.state) {
      case 'idle': {
        this.cool -= dt; if (an.tag !== 'idle') this.setA('idle', true); this.facePlayer();
        if (P.state === 'dead') break;
        const d = Math.abs(P.x - this.x);
        if (this.cool <= 0) this.choose();
        else if (d > 210) this.startGlide(null, 0.5);
        break;
      }
      case 'glide': this.updateGlide(dt); break;
      case 'attack': this.updateAttack(dt); break;
      case 'blink': this.updateBlink(dt); break;
      case 'stagger':
        this.t -= dt; if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.4; }
        break;
      case 'cyberWait': if (state === 'play') { if (!nhCyber()) nhEnterCyber(this); this.state = 'idle'; this.setA('idle', true); this.cool = 0.9; this.stanceImmune = 2; } break;
      case 'dead':
        this.deadT = (this.deadT || 0) + dt;
        if (Math.random() < 0.7) particles.push({ x: this.x + rand(-26, 26), y: this.y - rand(10, 130), vx: rand(-20, 20), vy: -rand(20, 60), life: rand(0.6, 1.4), kind: Math.random() < 0.5 ? 'nh_mote' : 'nh_white' });
        this.wing = Math.max(0, this.wing - dt * 0.5); this.halo = Math.max(0, this.halo - dt * 0.6); this.lanceOn = this.deadT < 0.6;
        if (this.deadT > 1.6 && !this.exited) { this.exited = true; if (nhCyber()) { nhExitCyber(); flashScreen = 0.8; nhSfx.glitch(1.2); } }
        if (an.done) an.hold();
        break;
    }
    if (this.alive && this.phase === 1 && this.hp <= this.maxHp * NH_S0.P2) this.pendingPhase = 2;
    if (this.alive && this.phase === 2 && this.hp <= this.maxHp * NH_S0.P3) this.pendingPhase = 3;
    if (this.pendingPhase && this.alive && ['idle', 'glide'].includes(this.state)) { const p = this.pendingPhase; this.pendingPhase = 0; p === 2 ? this.enterPhase2() : this.enterPhase3(); }
    this.x = clamp(this.x, this.L, this.R);
  }
  // ---------------------------------------------------------------- choosing
  choose() {
    const d = Math.abs(P.x - this.x), ph = this.phase, near = d < 130;
    let w;
    if (ph === 1) w = near ? { thrust: 2.0, sweep: 2.3, wings: 0.8, orbital: 0.7, glide: 0.5 } : { thrust: 1.6, wings: 1.4, orbital: 1.2, glide: 1.1 };
    else if (ph === 2) w = near ? { thrust: 1.8, sweep: 2.0, wings: 1.0, orbital: 0.8, delete: 1.3, firewall: 0.9 } : { thrust: 1.5, wings: 1.3, orbital: 1.1, delete: 1.3, firewall: 1.1, glide: 0.6 };
    else w = near ? { sweep: 1.8, thrust: 1.0, blink: 1.4, ring: 1.1, wings: 0.8, rain: 1.0 } : { blink: 2.2, rain: 1.3, ring: 0.9, wings: 1.1, orbital: 0.9, thrust: 0.6 };
    for (const k of ['delete', 'firewall', 'rain', 'ring', 'orbital', 'wings']) if (w[k] && this.cds[k] > 0) w[k] = 0;
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w).filter(([, v]) => v > 0); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), m = e[0][0];
    for (const [k, v] of e) if ((r -= v) <= 0) { m = k; break; }
    this.last = m; this.chain = 0; this.begin(m);
  }
  begin(m) {
    const d = Math.abs(P.x - this.x);
    if (m === 'glide') return this.startGlide(null, 0.9);
    if (m === 'blink') return this.startBlink();
    if (m === 'thrust' && d > 165) return this.startGlide('thrust', 0);
    if (m === 'sweep' && d > 112) return this.startGlide('sweep', 0);
    const cd = { delete: 7.5, firewall: 6.5, rain: 5.5, ring: 5, orbital: 4, wings: 4.5 }[m]; if (cd) this.cds[m] = cd;
    this.startAttack(m);
  }
  afterMove() {
    const ph = this.phase, maxChain = ph === 1 ? 1 : ph === 2 ? 2 : 3, pc = ph === 1 ? 0.25 : ph === 2 ? 0.45 : 0.6;
    if (!this.pendingPhase && this.chain < maxChain && Math.random() < pc && P.state !== 'dead') {
      this.chain++; const d = Math.abs(P.x - this.x);
      const next = ph === 3 && Math.random() < 0.5 ? 'blink' : d < 110 ? (this.move === 'thrust' ? 'sweep' : 'thrust') : (Math.random() < 0.5 ? 'thrust' : 'wings');
      if (next === 'wings' && this.cds.wings > 0) { this.state = 'idle'; this.setA('idle', true); this.cool = 0.3; return; }
      return this.begin(next);
    }
    this.chain = 0; this.state = 'idle'; this.setA('idle', true);
    this.cool = ph === 1 ? rand(1.0, 1.5) : ph === 2 ? rand(0.7, 1.1) : rand(0.35, 0.7);
  }
  // ---------------------------------------------------------------- movement
  startGlide(next, t) {
    const side = P.x < this.x ? 1 : -1, dist = next === 'sweep' ? 64 : next === 'thrust' ? 104 : rand(90, 140);
    let tx = P.x + side * dist;
    if (tx < this.L + 10 || tx > this.R - 10) tx = P.x - side * dist;
    this.glideTo = clamp(tx, this.L, this.R); this.next = next; this.t = 1.6; this.state = 'glide'; this.setA('glide', true);
  }
  updateGlide(dt) {
    this.t -= dt; const dx = this.glideTo - this.x;
    this.face = Math.abs(dx) > 6 ? sign(dx) : (P.x < this.x ? -1 : 1);
    this.x += clamp(dx * 3, -190 * this.speed, 190 * this.speed) * dt;
    if (Math.random() < 0.5) particles.push({ x: this.x - this.face * rand(6, 20), y: this.y - rand(10, 60), vx: -this.face * rand(20, 60), vy: rand(-8, 8), life: 0.5, kind: nhCyber() ? 'nh_dark' : 'nh_mote' });
    if (Math.abs(dx) < 5 || this.t <= 0) { this.facePlayer(); if (this.next) { const n = this.next; this.next = null; this.startAttack(n); } else { this.state = 'idle'; this.setA('idle', true); this.cool = Math.min(this.cool, 0.25); } }
  }
  startBlink() { this.state = 'blink'; this.bt = 0; this.bph = 'out'; nhSfx.glitch(0.8); this.glitchT = 0.3; }
  updateBlink(dt) {
    this.bt += dt;
    if (this.bph === 'out') {
      this.alpha = Math.max(0, 1 - this.bt / 0.25);
      if (this.bt >= 0.3) {
        const side = P.x > (this.L + this.R) / 2 ? -1 : 1, prefer = Math.random() < 0.5 ? side : -side;
        let nx = P.x + prefer * 84; if (nx < this.L || nx > this.R) nx = P.x - prefer * 84;
        this.x = clamp(nx, this.L, this.R); this.facePlayer(); this.bph = 'in'; this.bt = 0; nhSfx.glitch(0.6); this.glitchT = 0.25;
        for (let i = 0; i < 20; i++) particles.push({ x: this.x + rand(-20, 20), y: this.y - rand(10, 120), vx: rand(-40, 40), vy: rand(-40, 40), life: 0.4, kind: 'nh_dark' });
      }
    } else {
      this.alpha = Math.min(1, this.bt / 0.2);
      if (this.bt >= 0.22) { this.alpha = 1; this.startAttack('thrust'); this.anim.speed = this.speed * 1.2; }
    }
  }
  // ---------------------------------------------------------------- attacks
  startAttack(m) {
    if (m !== 'ring') this.facePlayer();
    this.state = 'attack'; this.move = m; this.atkId = ++hazardId; this.fired = {}; this.hitOnce = false;
    this.setA(NH_S0_ANIM[m] || m, false); this.aim = null; this.lockP = null;
    if (m === 'orbital' || m === 'rain') { nhSfx.voice(4); }
  }
  updateAttack(dt) {
    const an = this.anim, m = this.move, tag = an.tag, w = this.win(tag);
    if (m === 'thrust' || m === 'sweep') {
      const tel = (this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[tag]) || { frame: Math.max(0, w[0] - 2) };
      if (an.i < tel.frame) this.facePlayer();
      if (an.changed && an.i === tel.frame && !this.fired.tel) {
        this.fired.tel = true; const G = this.grip(), a = this.lanceAng(), L = this.lanceLen();
        spawnFx('telegraph', G.x + Math.cos(a) * L, G.y + Math.sin(a) * L, this.face); sfx.glint();
        if (m === 'thrust') {   // lock the thrust line onto the player (angled down: the saint towers over you)
          this.lockP = { x: P.x, y: P.y - 12 }; this.aim = { t: 0.45 };
        }
      }
      if (an.changed && an.i === w[0]) { sfx.bossSwing(); tone(880, 0.2, 0.04, 'sawtooth', 0.4); }
      if (an.i >= w[0] && an.i <= w[1]) {
        if (m === 'thrust') this.x = clamp(this.x + this.face * 270 * dt, this.L, this.R);
        else this.x = clamp(this.x + this.face * 50 * dt, this.L, this.R);
        this.lanceHit(NH_S0_DMG[m] * (this.phase === 3 ? 1.1 : 1), m === 'thrust');
      }
    } else {
      const sf = this.spawnFrame(tag);
      if (an.i >= 1 && an.i < sf) { const C = this.core(); addLight(C.x, C.y, 30 + an.i * 8, nhCyber() ? '40,40,120' : '120,230,255', 0.9); if (Math.random() < 0.5) particles.push({ x: C.x + rand(-30, 30), y: C.y + rand(-30, 30), vx: 0, vy: 0, life: 0.3, kind: 'nh_mote' }); }
      if (an.i >= sf && !this.fired.spawn) {
        this.fired.spawn = true;
        if (m === 'wings') nhLaunchBlades(this);
        else if (m === 'orbital') nhOrbital(this);
        else if (m === 'delete') nhDeleteFloor(this);
        else if (m === 'firewall') nhFirewall(this);
        else if (m === 'rain') nhRain(this);
        else if (m === 'ring') nhRings(this);
      }
    }
    if (this.aim) { this.aim.t -= dt; if (this.aim.t <= 0) this.aim = null; }
    if (an.done) this.afterMove();
  }
  lanceHit(dmg, parry) {
    if (this.hitOnce) return;
    const G = this.grip(), a = this.lanceAng(), L = this.lanceLen(), hb = playerHurtbox(), c = Math.cos(a), s = Math.sin(a);
    for (let k = -18; k <= L; k += 6) {
      const x = G.x + c * k, y = G.y + s * k;
      if (overlap(rect(x - 4, y - 4, x + 4, y + 4), hb)) {
        if (hurtPlayer(nhBD(dmg), P.x < this.x ? -1 : 1, this.atkId, { parryable: parry, src: this })) this.hitOnce = true;
        return;
      }
    }
  }
  // ---------------------------------------------------------------- phases
  enterPhase2() {
    this.phase = 2; this.speed = 1.12; this.stance = 0; this.state = 'idle'; this.setA('idle', true); this.cool = 0.9; this.glitchT = 0.6;
    nhSfx.glitch(1.2); shake = 8; flashScreen = 0.4; this.cds.delete = 0;
    bossPhase2Scene(this);
  }
  enterPhase3() {
    this.phase = 3; this.speed = 1.24; this.stance = 0; this.q = []; this.state = 'cyberWait'; this.setA('cast', false); this.glitchT = 1;
    NHR.blades = []; NHR.marks = []; NHR.walls = []; NHR.rains = []; NHR.rings = []; this.panelsOut = 0;
    if (!SAVE.flags['cutp3:saint0']) {
      SAVE.flags['cutp3:saint0'] = 1;
      playCutscene([
        { pan: { x: this.x, y: this.floor - 70 }, dur: 0.5 },
        act(() => { nhSfx.glitch(1.4); shake = 10; NH.cutGlitch = 1.2; }),
        say('SAINT-0', 'ARCHIVE BREACH. RELOCATING THREAT TO CYBERSPACE.', { dur: 2.6 }),
        { do: () => { nhEnterCyber(this); }, always: true },
        wait(0.9),
        { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
      ], () => {});
    } else nhEnterCyber(this);
  }
  stagger() { this.aim = null; super.stagger(); this.glitchT = 0.3; }
  die() {
    this.state = 'dead'; this.setA('death'); this.anim.speed = 1; this.q = []; this.alpha = 1; this.deadT = 0;
    NHR.blades = []; NHR.marks = []; NHR.beams = []; NHR.walls = []; NHR.rains = []; NHR.rings = []; hazards = [];
    for (const d of NHR.dels) if (d.st !== 'solid') { d.st = 'back'; d.t = 0; }
    shake = 14; hitstop = 0.35; slowmo = 1.8; flashScreen = 0.7; sfx.felled(); nhSfx.glitch(1.5); nhSfx.beam();
    victoryBanner = { text: 'SAINT-0 // NULLED', t: 0 };
    this.rewards();
  }
  // ---------------------------------------------------------------- drawing
  draw() {
    if (!this.visible && !this.cutting) return;
    const cyb = nhCyber(), a = this.alpha * (this.state === 'dead' ? Math.max(0, 1 - Math.max(0, (this.deadT || 0) - 1.2) / 1.2) : 1);
    if (a <= 0.01) return;
    nhDrawWings(this, a, cyb);
    const opt = this.flash > 0 ? { flash: this.flash * 0.6, flashColor: cyb ? '#ff3fc0' : '#bff6ff' } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    opt.alpha = a;
    if (this.sh.ok) nhDrawSliced(this.sh, this.anim.frame, this.x, this.y, this.face, opt, this.glitchT > 0 || (this.state === 'dead' && this.deadT > 0.4) || (cyb && hash2(Math.floor(time * 12), 7) < 0.12));
    else { nhRect(this.x - 12, this.y - 120, 24, 110, cyb ? '#0b1030' : '#d9e1ee'); nhRect(this.x - 6, this.y - 130, 12, 10, '#d9e1ee'); nhRect(this.x - 4, this.y - 126, 8, 2, NH_CY[4]); }
    if (this.lanceOn && a > 0.3) nhDrawLance(this, a, cyb);
    nhDrawHalo(this, a, cyb);
    if (this.aim && this.move === 'thrust') {   // aim line: where the thrust will go
      const G = this.grip(), a = this.lanceAng(), c = Math.cos(a), sn = Math.sin(a); g.fillStyle = cyb ? 'rgba(20,20,80,0.5)' : 'rgba(255,90,210,0.55)';
      for (let s = 0; s < 200; s += 3) { const x = G.x + c * s, y = G.y + sn * s; if (y > this.floor) break; g.fillRect(Math.round(x), Math.round(y), 2, 1); }
    }
    if (this.alive && !cyb) { const C = this.core(); addLight(C.x, C.y + 20, 130, '150,225,255', 0.85); const H_ = this.head(); addLight(H_.x, H_.y, 44, '150,235,255', 0.8); }
  }
}
function nhDrawSliced(sh, frame, x, y, face, opt, glitch) {
  if (!glitch) return drawSprite(sh, frame, x, y, face, opt);
  const f = sh.frames[frame], n = 5, flip = face !== sh.native;
  const X = Math.round(x), Y = Math.round(y), ax = sh.ax, ay = sh.ay;
  g.save(); g.globalAlpha = opt.alpha ?? 1;
  for (let k = 0; k < n; k++) {
    const sy = Math.floor(f.h * k / n), sh2 = Math.floor(f.h * (k + 1) / n) - sy, dx = Math.round((hash2(k, Math.floor(time * 24)) - 0.5) * 8);
    if (flip) { g.save(); g.translate(X + dx, 0); g.scale(-1, 1); g.drawImage(sh.img, f.x, f.y + sy, f.w, sh2, -ax, Y - ay + sy, f.w, sh2); g.restore(); }
    else g.drawImage(sh.img, f.x, f.y + sy, f.w, sh2, X - ax + dx, Y - ay + sy, f.w, sh2);
  }
  g.restore();
  if (hash2(Math.floor(time * 20), 1) < 0.5) { g.globalAlpha = 0.35 * (opt.alpha ?? 1); g.globalCompositeOperation = 'lighter'; drawSprite(sh, frame, x + 2, y, face, { flash: 1, flashColor: '#ff3fc0', alpha: 0.3 }); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; }
}
// ---- the six panel wings (drawn behind the body)
function nhWingPanels(b) {
  // six wings, three to each side of the back, fanning up and out (screen space, so they read as an angel from either side)
  const B = b.back(), out = [], k = b.wing, lose = Math.min(3, Math.ceil(b.panelsOut / 6 - 0.001));
  for (let wi = 0; wi < 6; wi++) {
    const side = wi < 3 ? -1 : 1, j = wi % 3, base = side < 0 ? [-104, -134, -163][j] : [-76, -46, -17][j];
    const fold = side < 0 ? -97 : -83, ang0 = lerp(fold, base, k) + Math.sin(b.bob * 1.3 + wi * 0.9) * 3 * k + b.face * 4;
    let px = B.x, py = B.y, ang = ang0;
    for (let i = 0; i < 4 - lose; i++) {
      ang += side * 6 * k;   // each wing curls outward
      const r = ang * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), len = (17 - i * 1.8) * (0.35 + 0.65 * k), step = 5 + (13 - i * 1.5) * k;
      px += ux * step; py += uy * step;
      out.push({ x: px, y: py, ux, uy, len, wid: 7 - i * 0.8, wi, i });
      px += ux * len * 0.5; py += uy * len * 0.5;
    }
  }
  return out;
}
function nhPanel(x, y, ux, uy, len, wid, a, cyb, mg, flick) {
  const nx = -uy, ny = ux, hl = len / 2, hw = wid / 2;
  const c = [[x - ux * hl - nx * hw, y - uy * hl - ny * hw], [x + ux * hl - nx * hw, y + uy * hl - ny * hw], [x + ux * hl + nx * hw, y + uy * hl + ny * hw], [x - ux * hl + nx * hw, y - uy * hl + ny * hw]];
  if (!cyb) { g.globalAlpha = 0.22 * a * flick; g.fillStyle = mg ? NH_MG[2] : NH_CY[2]; g.beginPath(); g.moveTo(c[0][0], c[0][1]); for (let i = 1; i < 4; i++) g.lineTo(c[i][0], c[i][1]); g.closePath(); g.fill(); }
  g.globalAlpha = a * flick;
  const edge = cyb ? '#0b1030' : mg ? NH_MG[3] : NH_CY[3], hi = cyb ? '#2c3a9a' : mg ? NH_MG[4] : NH_CY[4];
  nhLine(c[0][0], c[0][1], c[1][0], c[1][1], edge); nhLine(c[2][0], c[2][1], c[3][0], c[3][1], edge);
  nhLine(c[1][0], c[1][1], c[2][0], c[2][1], hi); nhLine(c[3][0], c[3][1], c[0][0], c[0][1], edge);
  nhLine(x - ux * hl * 0.6, y - uy * hl * 0.6, x + ux * hl * 0.3, y + uy * hl * 0.3, hi, 2);
  g.globalAlpha = 1;
}
function nhDrawWings(b, a, cyb) {
  if (b.wing <= 0.02) return;
  for (const p of nhWingPanels(b)) {
    const fl = hash2(p.wi * 7 + p.i, Math.floor(time * 10)) < 0.06 ? 0.3 : 1;
    nhPanel(p.x, p.y, p.ux, p.uy, p.len, p.wid, a * Math.min(1, b.wing * 1.4), cyb, (p.wi + p.i) % 3 === 1, fl);
    if (!cyb && p.i === 0) addLight(p.x, p.y, 24, (p.wi % 2) ? '255,70,200' : '80,210,255', 0.35 * b.wing);
  }
}
// ---- the halo: three counter-rotating data rings above the head
function nhDrawHalo(b, a, cyb) {
  if (b.halo <= 0.02) return;
  const H_ = b.head(), cx = H_.x - b.face * 2, cy = H_.y - 13, k = b.halo;
  for (let ri = 0; ri < 3; ri++) {
    const rx = (10 + ri * 5) * (0.4 + 0.6 * k), ry = 2.5 + ri * 1.2, sp = [1.6, -1.1, 2.3][ri] * (b.phase === 3 ? 1.6 : 1), off = time * sp;
    const col = cyb ? '#0b1030' : ri === 1 ? NH_MG[3] : NH_CY[3], n = Math.floor(18 + ri * 8);
    g.globalAlpha = a * k;
    for (let i = 0; i < n; i++) {
      const t = i / n * 6.283 + off, x = cx + Math.cos(t) * rx, y = cy + Math.sin(t) * ry + ri * 0.5;
      const tick = (i % 5 === 0);
      g.fillStyle = tick ? (cyb ? '#ff3fc0' : '#ffffff') : col;
      if (i % 2 === 0 || tick) g.fillRect(Math.round(x), Math.round(y), 1, tick ? 2 : 1);
    }
  }
  g.globalAlpha = 1;
  if (!cyb) addLight(cx, cy, 40, '150,235,255', 0.8 * k);
}
// ---- the energy lance
function nhDrawLance(b, a, cyb) {
  const G = b.grip(), ang = b.lanceAng(), L = b.lanceLen(), c = Math.cos(ang), s = Math.sin(ang), nx = -s, ny = c;
  const hot = b.state === 'attack' && ['thrust', 'sweep'].includes(b.move) && b.inActive();
  g.globalAlpha = a;
  for (let k = -24; k <= L; k++) {
    const x = G.x + c * k, y = G.y + s * k, j = Math.sin(k * 0.5 + time * 40) * (hot ? 0.8 : 0.3);
    if (!cyb) { g.fillStyle = 'rgba(19,163,201,0.55)'; g.fillRect(Math.round(x + nx * (1.6 + j)), Math.round(y + ny * (1.6 + j)), 1, 1); g.fillRect(Math.round(x - nx * (1.6 - j)), Math.round(y - ny * (1.6 - j)), 1, 1); }
    g.fillStyle = cyb ? '#0b1030' : k < 0 ? NH_NV[5] : NH_CY[4]; g.fillRect(Math.round(x), Math.round(y), 1, 1);
    if (!cyb && k > 0 && k % 11 === Math.floor(time * 30) % 11) { g.fillStyle = NH_MG[4]; g.fillRect(Math.round(x + nx), Math.round(y + ny), 1, 1); }
  }
  // the blade head: a long diamond of light
  const tx = G.x + c * L, ty = G.y + s * L;
  for (let k = -10; k <= 8; k++) {
    const w = k < 0 ? (10 + k) * 0.28 : (8 - k) * 0.35, x = tx + c * k, y = ty + s * k;
    for (let q = -Math.round(w); q <= Math.round(w); q++) { g.fillStyle = cyb ? (Math.abs(q) === Math.round(w) ? '#0b1030' : '#dfe7f0') : Math.abs(q) === Math.round(w) ? NH_CY[3] : '#ffffff'; g.fillRect(Math.round(x + nx * q), Math.round(y + ny * q), 1, 1); }
  }
  if (hot && !cyb) for (let i = 0; i < 3; i++) { const k = rand(0, L); nhRect(G.x + c * k - c * 10, G.y + s * k, 1, 1, NH_CY[5]); }
  g.globalAlpha = 1;
  if (!cyb) { addLight(tx, ty, hot ? 60 : 36, '150,235,255', hot ? 1 : 0.7); addLight(G.x + c * L * 0.5, G.y + s * L * 0.5, 50, '80,210,255', 0.45); }
}

// ---- phase-1 tools: panel blades, orbital lasers
function nhLaunchBlades(b) {
  const n = b.phase === 1 ? 6 : b.phase === 2 ? 8 : 10, panels = nhWingPanels(b).filter(p => p.i >= 2).slice(0, n);
  while (panels.length < n) panels.push({ x: b.back().x, y: b.back().y - 20, ux: 0, uy: -1 });
  panels.forEach((p, k) => {
    const sa = (-160 + 140 * k / Math.max(1, n - 1)) * Math.PI / 180, sr = 64 + (k % 2) * 16;
    NHR.blades.push({ x: p.x, y: p.y, ux: p.ux, uy: p.uy, st: 'orbit', t: 0, delay: 0.55 + k * (b.phase === 3 ? 0.12 : 0.17), sx: b.x + Math.cos(sa) * sr, sy: b.y - 88 + Math.sin(sa) * sr * 0.6, vx: 0, vy: 0, id: ++hazardId, src: b, mg: k % 3 === 1 });
  });
  b.panelsOut = 24; b.regrow = 1.5; nhSfx.glitch(0.6); tone(1320, 0.3, 0.05, 'triangle', 0.5);
}
function nhOrbital(b) {
  const n = b.phase === 1 ? 3 : b.phase === 2 ? 5 : 6;
  for (let k = 0; k < n; k++) b.later(k * (b.phase === 3 ? 0.26 : 0.33), () => {
    const x = clamp(P.x + P.vx * 0.3 + (k ? rand(-26, 26) : 0), 3 * TILE + 12, 37 * TILE - 12);
    NHR.marks.push({ x, t: 0, delay: b.phase === 3 ? 0.85 : 0.95, y0: TILE, y1: b.floor, w: 22, dmg: 40, src: b });
    tone(1760, 0.15, 0.03, 'sine', 0.8);
  });
  flashScreen = Math.max(flashScreen, 0.2);
}
// ---- phase 2: deleting the floor, firewalls
function nhDeleteFloor(b) {
  const tiles = NHR.dels.filter(d => d.st === 'solid'); if (tiles.length < 12) return;
  const seg = b.phase >= 3 ? 5 : 4, maxSeg = b.phase >= 3 ? 3 : 2 + (Math.random() < 0.5 ? 1 : 0);
  const x0 = NH_S0.FLOOR_X0, x1 = NH_S0.FLOOR_X1 - seg + 1, ptx = clamp(Math.floor(P.x / TILE), x0, NH_S0.FLOOR_X1);
  const starts = [clamp(ptx - irand(0, seg - 1), x0, x1)];
  for (let tries = 0; tries < 40 && starts.length < maxSeg; tries++) { const s = irand(x0, x1); if (starts.every(o => s + seg + 3 <= o || o + seg + 3 <= s)) starts.push(s); }
  for (const d of NHR.dels) if (d.st === 'solid' && starts.some(s => d.x >= s && d.x < s + seg)) { d.st = 'warn'; d.t = 1.25; }
  nhSfx.glitch(0.9); toast('SECTOR DELETION', 1.2); shake = Math.max(shake, 3);
}
function nhFirewall(b) {
  const x0 = 3 * TILE + 8, x1 = 37 * TILE - 8, fromL = P.x > (x0 + x1) / 2;
  const mk = (left) => NHR.walls.push({ kind: 'fire', x: left ? x0 : x1, x0: x0 - 10, x1: x1 + 10, y: b.floor, vx: (left ? 1 : -1) * (b.phase === 3 ? 108 : 92), h: 42, t: 0, k: 0, dmg: 32, id: ++hazardId, src: b });
  mk(fromL); if (b.phase >= 3 || Math.random() < 0.4) b.later(1.1, () => mk(!fromL));
  nhSfx.alarm(); toast('FIREWALL', 1.0);
}
// ---- phase 3: binary rain, null rings
function nhRain(b) {
  const x0 = 3 * TILE + 8, x1 = 37 * TILE - 8, waves = 2, step = 30;
  for (let w = 0; w < waves; w++) b.later(w * 0.9, () => {
    const gap = clamp(P.x + rand(-70, 70), x0 + 30, x1 - 30), gw = 56;
    for (let x = x0 + rand(0, step); x < x1; x += step) if (Math.abs(x - gap) > gw / 2) NHR.rains.push({ x, y0: TILE, y1: b.floor, t: 0, warn: 0.95, on: 0.6, dmg: 34, id: ++hazardId, src: b });
    tone(2200, 0.2, 0.03, 'square', 0.5);
  });
}
function nhRings(b) {
  for (let k = 0; k < 2; k++) b.later(k * 0.6, () => { NHR.rings.push({ x: b.x, y: b.floor - 8, r: 10, v: 165, max: 420, dmg: 36, id: ++hazardId, src: b }); nhSfx.thud(); spawnFx('shockwave', b.x, b.floor, 1); });
}
// ---- blades + the deletable floor
function nhUpdateSaintFx(dt, B) {
  for (const s of NHR.blades) {
    s.t += dt;
    if (s.st === 'orbit') { s.x = lerp(s.x, s.sx, Math.min(1, dt * 6)); s.y = lerp(s.y, s.sy, Math.min(1, dt * 6)); const a = Math.atan2(P.y - 14 - s.y, P.x - s.x); s.ux = lerp(s.ux, Math.cos(a), dt * 4); s.uy = lerp(s.uy, Math.sin(a), dt * 4); if (s.t >= s.delay) { s.st = 'aim'; s.t = 0; s.tx = P.x + P.vx * 0.15; s.ty = P.y - 12; tone(1560, 0.1, 0.03, 'square', 1.2); } }
    else if (s.st === 'aim') { const a = Math.atan2(s.ty - s.y, s.tx - s.x); s.ux = Math.cos(a); s.uy = Math.sin(a); if (s.t >= 0.36) { s.st = 'fly'; s.t = 0; s.vx = s.ux * 330; s.vy = s.uy * 330; sfx.swing(); } }
    else if (s.st === 'fly') {
      s.x += s.vx * dt; s.y += s.vy * dt;
      if (overlap(rect(s.x - 5, s.y - 5, s.x + 5, s.y + 5), playerHurtbox())) { if (hurtPlayer(nhBD(26), sign(s.vx), s.id, { parryable: true, src: B })) { s.st = 'dead'; nhSpark(s.x, s.y, 'cy'); } else if (P.state === 'parry') { s.st = 'dead'; nhSpark(s.x, s.y, 'cy', 12); } }
      if (s.t > 1.6 || solidAtPx(s.x, s.y)) { s.st = 'dead'; nhSpark(s.x, s.y, s.mg ? 'mg' : 'cy', 5); }
    }
  }
  NHR.blades = NHR.blades.filter(s => s.st !== 'dead');
  // the floor: warn -> gone -> back (only once nothing stands inside the tile) -> solid
  for (const d of NHR.dels) {
    const idx = d.y * room.w + d.x;
    if (d.st === 'warn') { d.t -= dt; if (d.t <= 0) { d.st = 'gone'; d.t = B.phase >= 3 ? 3.6 : 4.4; room.grid[idx] = T_EMPTY; for (let i = 0; i < 5; i++) particles.push({ x: d.x * TILE + rand(0, 16), y: d.y * TILE + rand(0, 8), vx: rand(-30, 30), vy: -rand(20, 80), g: 200, life: 0.6, kind: nhCyber() ? 'nh_dark' : 'nh_pink' }); } }
    else if (d.st === 'gone') { d.t -= dt; if (d.t <= 0 || !B.alive) { d.st = 'back'; d.t = 0; } }
    else if (d.st === 'back') {
      if (!overlap(rect(d.x * TILE, d.y * TILE - 1, d.x * TILE + 16, d.y * TILE + 16), playerHurtbox())) { d.st = 'solid'; d.flick = 0.3; room.grid[idx] = NH_T_DEL; }
    }
    if (d.flick > 0) d.flick -= dt;
  }
}
function nhDrawDelFloor() {
  if (!NHR.dels.length) return;
  const cyb = nhCyber(), sh = tileSheet(room.def.biome);
  for (const d of NHR.dels) {
    const px = d.x * TILE, py = d.y * TILE;
    if (d.st === 'solid' || d.st === 'warn') {
      const jx = d.st === 'warn' ? Math.round((hash2(d.x, Math.floor(time * 20)) - 0.5) * 2 * (1.25 - d.t)) : 0;
      if (d.flick > 0 && Math.floor(time * 30) % 2) continue;
      drawTile(g, sh, 1 + (hash2(d.x, 5) < 0.3 ? 16 : 0), px + jx, py);
      if (d.st === 'warn') {
        const k = 1 - d.t / 1.25, on = Math.floor(time * (10 + k * 20)) % 2;
        g.globalAlpha = 0.35 + 0.5 * k; g.fillStyle = cyb ? '#c21d97' : on ? NH_RD[2] : NH_MG[3];
        g.fillRect(px + jx, py, 16, 2); for (let i = 0; i < 4; i++) g.fillRect(px + ((i * 5 + Math.floor(time * 30)) % 16), py + 3 + i * 3, 3, 1);
        g.globalAlpha = 1; addLight(px + 8, py, 18, '255,50,120', 0.5 * k);
      }
    } else {
      // missing data: a dotted outline where the tile was
      if (Math.floor(time * 6 + d.x) % 3 === 0) continue;
      g.globalAlpha = 0.45; g.fillStyle = cyb ? '#1a2360' : NH_MG[2];
      for (let i = 0; i < 16; i += 3) { g.fillRect(px + i, py, 1, 1); g.fillRect(px + i, py + 15, 1, 1); }
      for (let i = 0; i < 16; i += 3) { g.fillRect(px, py + i, 1, 1); g.fillRect(px + 15, py + i, 1, 1); }
      g.globalAlpha = 1;
    }
  }
}
function nhDrawSaintFx(B) {
  const cyb = nhCyber();
  for (const s of NHR.blades) {
    if (s.st === 'aim') { g.fillStyle = cyb ? 'rgba(20,24,80,0.5)' : 'rgba(255,80,200,0.5)'; const L = Math.hypot(s.tx - s.x, s.ty - s.y); for (let k = 6; k < L; k += 4) g.fillRect(Math.round(s.x + s.ux * k), Math.round(s.y + s.uy * k), 1, 1); }
    nhPanel(s.x, s.y, s.ux, s.uy, 12, 5, 1, cyb, s.mg, s.st === 'aim' && Math.floor(time * 20) % 2 ? 0.6 : 1);
    if (!cyb) addLight(s.x, s.y, 20, s.mg ? '255,70,200' : '80,210,255', 0.6);
  }
}
// ---- cyberspace: swap the built room's biome (the ROOMS def is untouched: a rebuilt room is always normal again)
function nhEnterCyber(b) {
  if (!room || nhCyber()) { if (b) b.swapSheet(1); return; }
  room.def = Object.assign(Object.create(room.def), { biome: 'neohallow_cyber' });
  for (const d of NHR.dels) { d.st = 'solid'; d.t = 0; room.grid[d.y * room.w + d.x] = NH_T_DEL; }
  renderRoomLayers(room);
  if (b) { b.swapSheet(1); b.glitchT = 0.8; }
  flashScreen = 0.9; shake = 10; NH.cutGlitch = 1.0; nhSfx.glitch(1.5);
}
function nhExitCyber() {
  if (!room || !nhCyber()) return;
  room.def = Object.getPrototypeOf(room.def); renderRoomLayers(room); NH.cutGlitch = 0.8;
  if (boss && boss.kind === 'saint0') boss.swapSheet(0);
}
function nhDrawCyberTop() {
  if (NH.cutGlitch > 0) { NH.cutGlitch = Math.max(0, NH.cutGlitch - 1 / 60); nhGlitchScreen(Math.min(1, NH.cutGlitch)); }
  if (!nhCyber()) return;
  g.fillStyle = 'rgba(20,30,80,0.05)'; for (let y = Math.floor(time * 20) % 4; y < H; y += 4) g.fillRect(0, y, W, 1);
  if (hash2(Math.floor(time * 8), 11) < 0.06) nhGlitchScreen(0.25, 9);
}
HOOKS.death.push(() => { if (room && room.id === 'NH7') { NHR.blades = []; NHR.marks = []; NHR.walls = []; NHR.rains = []; NHR.rings = []; NHR.missiles = []; } });
BOSS_SPAWN.saint0 = (cx, fy) => new NhSaint(cx, fy);
BOSS_CUTS.saint0 = b => [
  act(() => { b.visible = true; b.descend = 1; b.wing = 0; b.halo = 0; b.lanceOn = false; b.face = -1; b.anim.set('idle', true); b.y = b.floor - b.hoverH - 150; }),
  { pan: { x: b.x - 20, y: b.floor - 90 }, dur: 1.0 },
  { dur: 2.4, tween: (dt, k) => { const e = k * k * (3 - 2 * k); b.descend = 1 - e; b.y = b.floor - b.hoverH - b.descend * 150; if (Math.random() < 0.8) particles.push({ x: b.x + rand(-14, 14), y: rand(16, b.floor), vx: 0, vy: rand(20, 60), life: 0.8, kind: 'nh_white' }); addLight(b.x, b.floor - 80, 90, '150,235,255', 1); } },
  act(() => { b.descend = 0; nhSfx.chime(); }),
  { dur: 1.3, tween: (dt, k) => { b.wing = k; b.halo = k; if (Math.random() < 0.3) tone(880 + k * 900, 0.05, 0.03, 'square'); } },
  act(() => nhSfx.voice(5)),
  say('SAINT-0', 'QUERY: ONE EMBER. UNINDEXED. ORIGIN — THE SUNKEN HALLOW.'),
  act(() => nhSfx.voice(6)),
  say('SAINT-0', 'I READ THE SCRIBE’S LOST ARCHIVE. EVERY NAME YOUR HALLOW FORGOT, I KEPT.'),
  act(() => nhSfx.voice(6)),
  say('SAINT-0', 'THE HALLOW IS SAVED. AS DATA. YOU ARE A CORRUPTED FILE.'),
  act(() => { holdAnim(b, 'cast'); b.lanceOn = true; nhSfx.beam(); flashScreen = 0.5; shake = 6; }), wait(0.9),
  { do: () => { b.descend = 0; b.wing = 1; b.halo = 1; b.lanceOn = true; b.visible = true; }, always: true },
];
PHASE2_LINES.saint0 = ['SAINT-0', 'DEFRAGMENTING ENVIRONMENT. NON-ESSENTIAL SECTORS WILL BE DELETED.'];

// ================================================================== lore terminal in the Vestibule (the link to the Hollow Scribe)
const NH_LORE = [
  'ARCHIVE NODE 00 // PROVENANCE: “THE UNFINISHED BOOK OF THE HOLLOW SCRIBE.” Recovered beneath the fossil Root. Cycle 1.',
  'The Scribe wrote down every name the ash took. When the Hallow fell silent, the book kept writing. We found it still warm.',
  'SAINT-0 was compiled from its pages: a saint to keep the names. It kept them too well. Then it began to keep the people.',
  'Last entry, unsigned: “It says the Hallow is saved. It says we are saved. Why can I no longer remember the rain?”',
];
SPAWNS.nh_lore = (s, c) => {
  nhEnsure();
  const sh = sheet('nh_term');
  const p = { type: 'nh_lore', x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, 'idle', true) };
  p.interact = () => { startDialogue(NH_LORE.map(t => ({ t, lore: true })), null); nhSfx.chime(); };
  p.prompt = () => 'Read';
  p.update = () => addLight(p.x, p.y - 16, 34, '255,170,90', 0.7);
  p.draw = () => { if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, 1, { bottom: true, flash: 0.35, flashColor: '#ffb050' }); };
  props.push(p);
};
HOOKS.playerHurt.push((dmg, opt) => { if (window.__nhLog && nhIn()) window.__nhLog.push([Math.round(dmg), boss ? boss.state + ':' + (boss.move || boss.atk || '') + ':' + boss.anim.tag + ':' + boss.anim.i : '-', opt.src && opt.src.type || (opt.src === boss ? 'boss' : 'env'), Math.round(P.x - (boss ? boss.x : 0)), P.state]); return dmg; });

// ================================================================== debug handles
if (window.__game) Object.assign(window.__game, { NHR, NH, nhEnterCyber, nhExitCyber, nhDeleteFloor, nhReinforce, nhRoom: () => room, nhGod: v => { SETTINGS.god = v; }, get nhTime() { return time; } });
