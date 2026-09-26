// ------------------------------------------------------------------ THE DROWNED BARROWS (agent B) + TIDEBREATH swimming (global)
// Tombs beneath the Sunken Cathedral flooded by a black tide. Biome `barrows` (rooms DB1–DB8, tools/regions/71_barrows.py).
// Deep water '"' (tile id 40) works in ANY room (N uses it for the Necropolis gate): without the Tidebreath you float at the
// surface and can't dive; with it you swim in every direction and a breath meter drains while your head is under.
// A room may also carry a dynamic tide line (Room kw `tide` = base row; the Choir's song moves it).
// Enemies: db_pilgrim, db_eel (lantern eel, lunges out of the water), db_barnacle. Bosses: the Ferryman (DB5, mini) and the
// Drowned Choir (DB6). Every top-level name is prefixed db/DB (all region files share one scope).
Object.assign(AREAS, { barrows: { name: 'The Drowned Barrows', ambient: 0.5, amb: 'dust', tint: '#03090b', map: '#2c5a58' } });
Object.assign(SCALES, { barrows: [0, 1, 3, 7, 8] });
Object.assign(ROOTS, { barrows: 41.2 });
Object.assign(PCOL, { db_glow: '120,240,220', db_bubble: '170,230,225', db_foam: '200,240,235', db_bile: '120,230,150', db_ink: '10,18,20' });
Object.assign(ITEMS, {
  tidebreath: { name: 'Tidebreath', icon: 'i_tidebreath', sheet: 'ui_icons5',
    desc: 'The Choir’s last breath, caught in a pearl of black water. You can dive and swim through deep water in every direction (hold ↑/↓, Space strokes up). Mind your breath.' },
});
Object.assign(LORE, {
  db1: ['A pilgrim’s marker, green with age:', '“We came down to pray where the Cathedral’s roots drink. The water came up to meet us, and it was singing.”'],
  db2: ['A grave of the tide-keepers, scrubbed clean by the current:', '“Ring the drowned bells and the song falters. We rang them every night until there was no one left to ring.”'],
  db3: ['A chapel headstone. Someone has scratched a verse beneath it:', '“The Choir sings the tide up to the living and down to the dead. It only ever wanted a larger congregation.”'],
  db4: ['A small pearl-inlaid stone, deep in the cistern:', '“Breathe out once, and the water keeps the rest. That is the ferry fare. That is the whole of the fare.”'],
});

const DB_T_WATER = 40;
const dbIn = () => room && room.def.biome === 'barrows';
const dbSfx = {
  splash: (v = 1) => { noise(0.45, 650, 0.6, 0.35 * v, 'lowpass', 0.5); noise(0.25, 2400, 1, 0.12 * v, 'highpass'); },
  stroke: () => noise(0.18, 420, 0.8, 0.08, 'lowpass', 0.7),
  bubble: () => tone(rand(700, 1100), 0.08, 0.025, 'sine', 1.6),
  gasp: () => { noise(0.25, 1600, 0.8, 0.12, 'bandpass', 0.6); tone(300, 0.18, 0.04, 'triangle', 1.4); },
  choke: () => { noise(0.3, 300, 0.7, 0.25, 'lowpass', 0.5); tone(90, 0.3, 0.12, 'sawtooth', 0.6); },
  toll: (p = 1) => { [110, 138.6, 164.8].forEach((f, i) => tone(f * p, 2.8, 0.12, 'sine', 1, i * 0.03)); tone(55 * p, 3, 0.16, 'triangle'); noise(0.3, 700, 0.8, 0.18, 'bandpass', 0.4); },
  wail: (p = 1) => { [220, 277, 330, 392].forEach((f, i) => tone(f * p, 1.6, 0.05, 'sawtooth', 0.92, i * 0.05)); noise(1.4, 1400, 0.6, 0.18, 'bandpass', 0.6); },
  hum: (p = 1) => { [98, 147, 196].forEach((f, i) => tone(f * p, 2.2, 0.06, 'triangle', 1.02, i * 0.12)); },
};

// ================================================================== tiles
// '"' deep water: non-solid; the body is drawn live (translucent over whatever swims in it). Here we only darken the backdrop.
registerTile('"', DB_T_WATER, { draw(ctx, sh, px, py, x, y, R, back) { back.fillStyle = 'rgba(1,8,10,0.55)'; back.fillRect(px, py, 16, 16); } });

// ================================================================== per-room water state
const DBW = { roomObj: null };
function dbReset() {
  Object.assign(DBW, { roomObj: room, mask: null, cells: [], surf: [], body: null, currents: [], tide: null, bubbles: [], glints: [], streaks: [],
                       grate: null, boat: null, fall: [] });
}
function dbEnsure() { if (DBW.roomObj !== room) dbReset(); }
const dbCell = (tx, ty) => (tx >= 0 && ty >= 0 && tx < room.w && ty < room.h) ? room.grid[ty * room.w + tx] : tileAt(tx, ty);
function dbBuildWater(def) {
  const R = room, w = R.w, h = R.h, m = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) if (R.grid[i] === DB_T_WATER) m[i] = 1;
  // entity cells (chests, items, graves…) sitting in water are flooded too
  for (let pass = 0; pass < 3; pass++) for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x; if (m[i] || isSolidT(R.grid[i]) || def.map[y][x] === '.') continue;
    if ((x > 0 && m[i - 1]) || (x < w - 1 && m[i + 1]) || (y > 0 && m[i - w]) || (y < h - 1 && m[i + w])) { m[i] = 1; R.grid[i] = DB_T_WATER; }
  }
  DBW.mask = m; DBW.cells = []; DBW.surf = [];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (m[y * w + x]) {
    DBW.cells.push([x, y]);
    const up = y > 0 ? R.grid[(y - 1) * w + x] : tileAt(x, y - 1);
    if (up !== DB_T_WATER && !isSolidT(up)) DBW.surf.push([x, y]);
  }
  DBW.body = DBW.cells.length ? dbPrerenderBody(m, w, h) : null;
}
// the water body: translucent black-teal that deepens with depth; cached per room
function dbPrerenderBody(m, w, h) {
  const c = document.createElement('canvas'); c.width = w * TILE; c.height = h * TILE;
  const x = c.getContext('2d');
  for (let ty = 0; ty < h; ty++) for (let tx = 0; tx < w; tx++) if (m[ty * w + tx]) {
    let d = 0; for (let k = 1; k <= 6 && ty - k >= 0 && m[(ty - k) * w + tx]; k++) d = k;   // rows of water above this cell
    x.fillStyle = `rgba(${6 - d},${26 - d * 2},${30 - d * 2},${Math.min(0.9, 0.56 + d * 0.06)})`;
    x.fillRect(tx * TILE, ty * TILE, TILE, TILE);
  }
  return c;
}
// the arena tide: every non-solid cell below the line is water (mask prerendered once)
function dbSetupTide(def) {
  const R = room, c = document.createElement('canvas'); c.width = R.pw; c.height = R.ph;
  const x = c.getContext('2d');
  for (let ty = 0; ty < R.h; ty++) for (let tx = 0; tx < R.w; tx++) {
    if (isSolidT(R.grid[ty * R.w + tx]) && R.grid[ty * R.w + tx] !== T_PLAT) continue;
    x.fillStyle = `rgba(4,${22 + (ty % 2)},${26 + (tx % 3 === 0 ? 1 : 0)},0.62)`; x.fillRect(tx * TILE, ty * TILE, TILE, TILE);
  }
  const y = def.tide * TILE + 2;
  DBW.tide = { base: y, y, target: y, speed: 30, canvas: c, x0: TILE, x1: R.pw - TILE, t: 0 };
}
function dbTideTo(y, speed = 30) { if (DBW.tide) { DBW.tide.target = y; DBW.tide.speed = speed; } }

// is (x, y) (px, room space) in deep water?
function dbDeepAt(x, y) {
  if (DBW.roomObj !== room) dbReset();
  const t = dbCell(Math.floor(x / TILE), Math.floor(y / TILE));
  if (t === DB_T_WATER) return true;
  const T = DBW.tide;
  return !!(T && y >= T.y && x >= T.x0 && x <= T.x1 && !(isSolidT(t) && t !== T_PLAT));
}
// the surface above (x, y): { y, air } — air=false means a ceiling seals the water here
function dbSurface(x, y) {
  const tx = Math.floor(x / TILE); let ty = Math.floor(y / TILE);
  if (dbCell(tx, ty) === DB_T_WATER) {
    let k = 0; while (k++ < 60 && dbCell(tx, ty - 1) === DB_T_WATER) ty--;
    const up = dbCell(tx, ty - 1);
    if (!isSolidT(up) && DBW.tide && DBW.tide.y < ty * TILE) return dbSurface(x, ty * TILE - 1);
    return { y: ty * TILE, air: !isSolidT(up) };
  }
  const T = DBW.tide;
  if (T && y >= T.y) {
    for (let r = ty; r >= Math.floor(T.y / TILE); r--) { const c = dbCell(tx, r); if (isSolidT(c) && c !== T_PLAT && r * TILE + TILE <= y) return { y: r * TILE + TILE, air: false }; }
    return { y: T.y, air: true };
  }
  return { y, air: true };
}
function dbOpenColumn(x, y, maxd = 120) {   // nearest x (±) whose column is open from the water up to the surface
  for (let d = 8; d <= maxd; d += 8) for (const s of [-1, 1]) {
    const nx = x + s * d; if (isSolidT(tileAt(Math.floor(nx / TILE), Math.floor(y / TILE)))) continue;
    if (dbSurface(nx, y).air) return nx;
  }
  return null;
}

// ================================================================== room setup
HOOKS.enter.push(def => {
  dbEnsure();
  dbBuildWater(def);
  if (def.tide) dbSetupTide(def);
  const S = DBS; S.inWater = !!(P && dbDeepAt(P.x, P.y - 3)); S.jumpT = 0; S.noDiveT = 0; S.headIn = false;
  if (def.id === 'K2' && def.map[11][39] === '=') {   // the grate into the Barrows
    DBW.grate = { x0: 39 * TILE, x1: 41 * TILE, y: 11 * TILE };
    props.push({ type: 'db_grate', x: 40 * TILE, y: 11 * TILE, face: 1, sh: sheet('db_grate'), anim: { update() {}, frame: 0 },
      draw() { const s = this.sh; if (s.ok) drawSprite(s, s.first('idle'), this.x, this.y + 16, 1, { bottom: true }); else { g.fillStyle = '#3a3a3a'; for (let i = 0; i < 8; i++) g.fillRect(this.x - 15 + i * 4, this.y, 2, 4); } },
      update() { addLight(this.x, this.y + 20, 26, '120,230,210', 0.35); } });
  }
  if (def.biome === 'barrows' && def.id === 'DB2' && !SAVE.items.hook) setTimeout(() => { if (room && room.id === 'DB2') toast('A black tide runs across the crypt. Golden rings hang above it…', 3.5); }, 1400);
});
HOOKS.death.push(() => { DBS.breath = dbBreathMax(); DBS.inWater = false; });
HOOKS.rest.push(() => { DBS.breath = dbBreathMax(); });

// ================================================================== TIDEBREATH swimming (player)
const DBS = { breath: 12, inWater: false, headIn: false, jumpT: 0, noDiveT: 0, drownT: 0, stroke: 0, showT: 0, bubT: 0, slowTag: null };
const DB_SWIM_V = 104, DB_FLOAT_V = 58, DB_FLOAT_D = 17;
function dbBreathMax() { return 12 * (charmOn('c_gill') ? 1.75 : 1); }
const DB_BUSY = new Set(['hurt', 'cast', 'heal', 'parry', 'art', 'riposte', 'gbreak', 'counter', 'sh_counter', 'backstep', 'block', 'guard']);
function dbSwimUpdate(dt) {
  const S = DBS;
  if (!P || P.state === 'dead' || P.state === 'rest' || P.state === 'rise') { if (P && P.state !== 'dead') S.inWater = false; return; }
  S.jumpT -= dt; S.noDiveT -= dt; S.showT -= dt;
  const feet = dbDeepAt(P.x, P.y - 3), upper = dbDeepAt(P.x, P.y - 20);
  const head = dbDeepAt(P.x, P.y - 25);
  // breath
  const bm = dbBreathMax();
  if (head && P.state !== 'hook') {
    S.breath -= dt; S.showT = 2;
    if (!S.headIn) { S.headIn = true; }
    if ((S.bubT -= dt) <= 0) { S.bubT = rand(0.25, 0.7); DBW.bubbles.push({ x: P.x + P.face * 4, y: P.y - 24, vy: -rand(20, 40), life: 3, r: 1 }); if (Math.random() < 0.3) dbSfx.bubble(); }
    if (S.breath <= 0) {
      S.breath = 0; S.drownT -= dt;
      if (S.drownT <= 0) {
        S.drownT = 0.6; const dmg = Math.max(1, Math.round(D.maxHp * 0.09));
        if (!SETTINGS.god) { P.hp = Math.max(0, P.hp - dmg); P.flash = 1; popup(P.x, P.y - 30, dmg, '#6fd6c8'); }
        dbSfx.choke(); shake = Math.max(shake, 2);
        for (let i = 0; i < 6; i++) DBW.bubbles.push({ x: P.x + rand(-4, 4), y: P.y - rand(14, 26), vy: -rand(40, 70), life: 2, r: 1 + (Math.random() < 0.4) });
        if (!S.warned || S.warned < time - 4) { S.warned = time; toast('Drowning — get to the surface!', 1.6); }
        if (P.hp <= 0) { killPlayer(0); return; }
      }
    }
  } else {
    if (S.headIn) { S.headIn = false; if (S.breath < bm * 0.5) dbSfx.gasp(); }
    S.breath = Math.min(bm, S.breath + dt * bm / 1.4); S.drownT = 0.8;
  }
  if (S.breath < bm) S.showT = Math.max(S.showT, 0.6);
  // leaving the water
  if (!feet && !upper) {
    if (S.inWater) { S.inWater = false; if (P.state === 'swim') setP('air', P.vy < 0 ? 'jump_up' : 'jump_fall', false); }
    return;
  }
  if (!S.inWater) {
    if (!upper) return;                        // wading in something shallow
    S.inWater = true;
    const sf = dbSurface(P.x, P.y - 20);
    if (P.vy > 120 || Math.abs(P.vx) > 150) {
      spawnFx(fxOr('db_splash', 'dust'), P.x, sf.y + 2, 1, null, { bottom: true }); dbSfx.splash(clamp(P.vy / 400, 0.4, 1));
      for (let i = 0; i < 10; i++) particles.push({ x: P.x + rand(-8, 8), y: sf.y, vx: rand(-60, 60), vy: -rand(40, 140), g: 420, life: rand(0.4, 0.8), kind: 'db_foam' });
    }
    P.vy *= 0.3; P.vx *= 0.65;
  }
  if (P.state === 'hook') return;
  const hasTB = !!SAVE.items.tidebreath, sf = dbSurface(P.x, P.y - 13);
  const cur = dbCurrentAt(P.x, P.y - 13, sf);
  // busy states (attacks, casts, flasks, hurt): the water holds you up instead of gravity, blows come slower
  if (ATK[P.state] || DB_BUSY.has(P.state) || P.state === 'roll' || P.state === 'plunge' || P.state === 'slam' || P.state === 'spdive') {
    if (P.state === 'plunge' || P.state === 'slam' || P.state === 'spdive') { setP('swim', dbSwimTag(false), true); }
    else {
      if ((ATK[P.state] || P.state === 'cast') && S.slowTag !== P.state) { S.slowTag = P.state; P.anim.speed *= 0.8; }
      const tv = hasTB ? 8 : clamp((sf.y + DB_FLOAT_D - P.y) * 5, -150, 120);
      if (P.state !== 'roll') { P.vy = approach(P.vy, tv, 900 * dt); P.vx *= Math.pow(0.25, dt); }
      else P.vy = approach(P.vy, hasTB ? 0 : tv, 900 * dt);
      if (cur) P.pushVx = cur.v;
      return;
    }
  }
  S.slowTag = null;
  if (P.state !== 'swim') {
    if (P.state === 'air' && S.jumpT > 0 && P.vy < 0) return;   // just leapt out
    setP('swim', dbSwimTag(false), true);
  }
  P.airDash = true; P.airJumps = 0; P.coyote = 0;
  const ax = inputX(), ay = (held.has('down') ? 1 : 0) - (held.has('up') ? 1 : 0);
  const atTop = sf.air && P.y - 26 <= sf.y + 3;
  if (ax) P.face = ax;
  if (hasTB) {
    // free swimming: all eight directions, weighty acceleration, gentle sink when idle, Space strokes upward
    const up = held.has('jump') ? -1 : 0, vy0 = ay || up;
    const tvx = ax * DB_SWIM_V, tvy = vy0 ? vy0 * DB_SWIM_V * 0.9 : (atTop ? clamp((sf.y + DB_FLOAT_D - P.y) * 4, -80, 60) : 14);
    const acc = 330;
    P.vx = approach(P.vx, tvx, acc * dt * (ax && Math.sign(ax) !== Math.sign(P.vx) ? 1.6 : 1));
    P.vy = approach(P.vy, tvy, acc * dt);
    if (ay > 0) P.drop = 0.12;   // one-way ledges underwater don't stop a dive
    if (atTop && ay < 0 && !held.has('jump')) P.vy = Math.max(P.vy, -20);   // bob at the surface
    if ((ax || vy0) && (S.stroke -= dt) <= 0) { S.stroke = 0.55; dbSfx.stroke(); DBW.bubbles.push({ x: P.x - P.face * 6, y: P.y - 12, vy: -rand(15, 30), life: 2, r: 1 }); }
  } else {
    // no Tidebreath: the black water won't take you. Float, paddle, climb out.
    let tvx = ax * DB_FLOAT_V;
    if (!sf.air) {   // sealed above (under a ledge): drift toward open water
      const nx = dbOpenColumn(P.x, P.y - 13);
      if (nx !== null) tvx = sign(nx - P.x) * 90;
    }
    const tvy = sf.air ? clamp((sf.y + DB_FLOAT_D - P.y) * 5, -150, 110) : -60;
    P.vx = approach(P.vx, tvx, 300 * dt);
    P.vy = approach(P.vy, tvy, 700 * dt);
    if (ay > 0 && S.noDiveT <= 0) { S.noDiveT = 7; toast('The black water will not let you under.', 2); }
    if ((ax) && (S.stroke -= dt) <= 0) { S.stroke = 0.7; dbSfx.stroke(); }
  }
  if (cur) P.pushVx = cur.v;
  // actions in the water
  if (take('jump') && atTop) {
    const nearWall = wallAt(P, -1) || wallAt(P, 1) || solidAtPx(P.x - 9, P.y - 4) || solidAtPx(P.x + 9, P.y - 4) || solidAtPx(P.x - 9, P.y - 20) || solidAtPx(P.x + 9, P.y - 20);
    if (cur && cur.gate && !nearWall) { if (!S.tideMsg || S.tideMsg < time - 3) { S.tideMsg = time; toast('The black tide drags you back. There is nothing to climb here.', 2); } }
    else {
      P.vy = -300; P.ground = false; S.jumpT = 0.3; S.inWater = false;
      setP('air', 'jump_up', false); sfx.jump(); spawnFx(fxOr('db_splash', 'dust'), P.x, sf.y + 2, 1, null, { bottom: true, speed: 1.3 });
      for (let i = 0; i < 8; i++) particles.push({ x: P.x + rand(-6, 6), y: sf.y, vx: rand(-40, 40), vy: -rand(40, 120), g: 420, life: 0.6, kind: 'db_foam' });
      return;
    }
  }
  if (peek('attack') && P.st > 0) { take('attack'); if (ax) P.face = ax; startAttack(held.has('up') ? 'attack_up' : held.has('down') && hasTB && pHas('attack_down') ? 'attack_down' : 'air_attack'); return; }
  if (peek('roll') && P.st > 0) { take('roll'); P.airDash = true; doRoll(ax); if (hasTB && ay) P.vy = ay * 60; return; }
  if (peek('cast')) { take('cast'); startCast(); return; }
  if (peek('hook')) { take('hook'); if (tryHook()) return; }
  if (peek('heal')) { take('heal'); if (P.flasksR > 0) { P.flasksR--; setP('heal', 'heal'); P.healPending = 1; } else { sfx.deny(); toast('Your crimson flasks are empty'); } return; }
  if (peek('mana')) { take('mana'); if (P.flasksB > 0) { P.flasksB--; setP('heal', 'heal'); P.healPending = 2; } else { sfx.deny(); toast('Your azure flasks are empty'); } return; }
  const moving = Math.hypot(P.vx, P.vy) > 30;
  const tag = dbSwimTag(moving);
  if (P.anim.tag !== tag) P.anim.set(tag, true);
  P.anim.speed = moving ? clamp(Math.hypot(P.vx, P.vy) / DB_SWIM_V, 0.5, 1.1) : 0.6;
}
function dbSwimTag(moving) {
  if (moving) return pHas('swim') ? 'swim' : pHas('glide') ? 'glide' : 'jump_fall';
  return pHas('tread') ? 'tread' : pHas('swim') ? 'swim' : 'jump_fall';
}
// surface currents (spawn db_current): push anything afloat near the surface
SPAWNS.db_current = (s) => {
  dbEnsure();
  DBW.currents.push({ x0: s.x * TILE, x1: (s.x + (s.w || 4)) * TILE, y0: s.y * TILE, y1: (s.y + (s.h || 2)) * TILE, v: s.v || -120, gate: !!s.gate, seed: rand(0, 99) });
};
function dbCurrentAt(x, y, sf) {
  for (const c of DBW.currents) if (x >= c.x0 + (c.v > 0 ? 22 : 0) && x <= c.x1 - (c.v < 0 ? 22 : 0) && y >= c.y0 - 16 && y <= c.y1 && (!sf || sf.y <= c.y0 + 4)) return c;
  return null;
}

// ================================================================== rendering the water
function dbDrawWater() {
  const T = DBW.tide;
  if (DBW.body) g.drawImage(DBW.body, 0, 0);
  if (T) {
    g.save(); g.beginPath(); g.rect(0, T.y, room.pw, room.ph - T.y); g.clip(); g.drawImage(T.canvas, 0, 0); g.restore();
  }
  const x0 = cam.x - 16, x1 = cam.x + W + 16, y0 = cam.y - 16, y1 = cam.y + H + 16;
  // caustics: slow drifting light threads just under each surface
  for (const [tx, ty] of DBW.surf) {
    const px = tx * TILE, py = ty * TILE; if (px < x0 || px > x1 || py < y0 || py > y1) continue;
    dbSurfaceLine(px, px + TILE, py);
    const k = Math.floor(time * 5 + tx * 3) % 7;
    if (k < 3) { g.fillStyle = 'rgba(90,200,190,0.10)'; g.fillRect(px + ((tx * 5 + k * 4) % 12), py + 4 + k * 3, 4, 1); }
    if (hash2(tx, Math.floor(time * 0.7)) < 0.08) addLight(px + 8, py + 6, 22, '90,220,200', 0.18);
  }
  if (T) {
    const ya = Math.round(T.y);
    for (let tx = Math.max(1, Math.floor(x0 / TILE)); tx < Math.min(room.w - 1, Math.ceil(x1 / TILE)); tx++) {
      const c = dbCell(tx, Math.floor(ya / TILE)); if (isSolidT(c) && c !== T_PLAT) continue;
      dbSurfaceLine(tx * TILE, tx * TILE + TILE, ya);
    }
    for (let k = 0; k < 4; k++) addLight(cam.x + W * (k + 0.5) / 4, T.y + 2, 60, '70,190,180', 0.18);
  }
  // current streaks
  for (const c of DBW.currents) {
    const n = Math.floor((c.x1 - c.x0) / 22);
    for (let i = 0; i < n; i++) {
      const L = c.x1 - c.x0, off = ((i * 53 + c.seed * 7 + time * c.v) % L + L) % L, x = c.x0 + off, y = c.y0 + 3 + (i % 3) * 5 + Math.sin(time * 2 + i) * 1.5;
      if (x < x0 || x > x1) continue;
      const len = 5 + (i % 3) * 3;
      g.fillStyle = `rgba(170,230,220,${0.22 + (i % 2) * 0.14})`; g.fillRect(Math.round(x), Math.round(y), len, 1);
    }
  }
  // bubbles
  for (const b of DBW.bubbles) {
    if (b.x < x0 || b.x > x1 || b.y < y0 || b.y > y1) continue;
    g.fillStyle = 'rgba(170,230,225,0.7)'; g.fillRect(Math.round(b.x), Math.round(b.y), b.r, b.r);
    if (b.r > 1) { g.fillStyle = 'rgba(230,255,250,0.8)'; g.fillRect(Math.round(b.x), Math.round(b.y), 1, 1); }
  }
}
function dbSurfaceLine(xa, xb, y) {
  for (let x = xa; x < xb; x += 2) {
    const w = Math.sin(time * 2.4 + x * 0.21) * 0.8 + Math.sin(time * 1.3 - x * 0.07) * 0.6, yy = Math.round(y + w);
    g.fillStyle = 'rgba(120,215,205,0.55)'; g.fillRect(x, yy, 2, 1);
    g.fillStyle = 'rgba(4,14,16,0.5)'; g.fillRect(x, yy + 1, 2, 1);
    if (((x * 7 + Math.floor(time * 4)) % 23) === 0) { g.fillStyle = 'rgba(220,255,250,0.8)'; g.fillRect(x, yy, 1, 1); }
  }
}
function dbUpdateWaterFx(dt) {
  for (const b of DBW.bubbles) {
    b.y += b.vy * dt; b.x += Math.sin(time * 6 + b.y * 0.2) * 6 * dt; b.life -= dt;
    if (!dbDeepAt(b.x, b.y - 1)) { b.life = 0; if (Math.random() < 0.5) particles.push({ x: b.x, y: b.y, vx: rand(-10, 10), vy: -rand(10, 20), life: 0.25, kind: 'db_foam' }); }
  }
  DBW.bubbles = DBW.bubbles.filter(b => b.life > 0);
  // ambient: bubbles rising from the deep, luminous silt near water
  if (DBW.cells.length && Math.random() < Math.min(0.6, DBW.cells.length / 300)) {
    const [tx, ty] = DBW.cells[irand(0, DBW.cells.length - 1)], x = tx * TILE + rand(2, 14), y = ty * TILE + rand(4, 14);
    if (x > cam.x - 20 && x < cam.x + W + 20 && y > cam.y - 20 && y < cam.y + H + 20) DBW.bubbles.push({ x, y, vy: -rand(10, 26), life: 4, r: Math.random() < 0.2 ? 2 : 1 });
  }
  if (DBW.tide && Math.random() < 0.4) { const x = cam.x + rand(0, W), y = rand(DBW.tide.y + 10, room.ph - 20); if (dbDeepAt(x, y)) DBW.bubbles.push({ x, y, vy: -rand(10, 30), life: 4, r: 1 }); }
  if (dbIn() && Math.random() < 0.25) particles.push({ x: cam.x + rand(0, W), y: cam.y + rand(0, H), vx: rand(-3, 3), vy: -rand(1, 5), life: rand(2, 5), kind: 'db_glow' });
  if (DBW.rings) { for (const r of DBW.rings) { r.r += 160 * dt; r.life -= dt; } DBW.rings = DBW.rings.filter(r => r.life > 0); }
  const T = DBW.tide;
  if (T) { T.t += dt; if (Math.abs(T.target - T.y) > 0.3) T.y = approach(T.y, T.target, T.speed * dt); }
}

// ================================================================== hooks: update / render / HUD
HOOKS.update.push(dt => {
  dbEnsure();
  dbSwimUpdate(dt);
  dbUpdateWaterFx(dt);
  // the K2 grate: tell the player how to drop through
  const G = DBW.grate;
  if (G && P.ground && P.x > G.x0 && P.x < G.x1 && Math.abs(P.y - G.y) < 2 && !SAVE.hints.dbGrate) { SAVE.hints.dbGrate = 1; toast('A rusted grate over black water. ↓ + Space to drop through.', 3.5); }
});
// (the water itself is drawn by a render hook registered at the end of this file, after the Choir's platform redraw)
HOOKS.renderTop.push(() => {
  if (!P || !DBS.headIn || P.state === 'dead') return;
  // under the surface: a cold murk over everything, deepening as breath runs out
  const k = 1 - DBS.breath / dbBreathMax();
  g.fillStyle = `rgba(2,26,30,${0.26 + 0.2 * k})`; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 6; i++) { const y = ((i * 41 + time * 9) % (H + 20)) - 10; g.fillStyle = 'rgba(120,220,210,0.05)'; g.fillRect(0, Math.round(y), W, 1); }
  if (k > 0.75) { g.fillStyle = `rgba(0,0,0,${(k - 0.75) * 1.4})`; g.fillRect(0, 0, W, H); }
});
HOOKS.hud.push(() => {
  if (!P || !D || state === 'cut') return;
  // breath: a ring of bubbles over the head while it's being used, and a bar with the other statuses
  const bm = dbBreathMax(), f = DBS.breath / bm;
  if (DBS.showT > 0 && (DBS.headIn || f < 0.999)) {
    const n = 6, full = Math.ceil(f * n - 0.001), sx = P.x - cam.x, sy = P.y - cam.y - 42;
    for (let i = 0; i < n; i++) {
      const a = (i - (n - 1) / 2) * 0.34, x = sx + Math.sin(a) * 16, y = sy + (1 - Math.cos(a)) * 10;
      vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, 2.1 * scale, 0, 6.3);
      if (i < full) { vctx.fillStyle = f < 0.3 ? 'rgba(255,140,120,0.9)' : 'rgba(150,235,225,0.85)'; vctx.fill(); }
      vctx.lineWidth = Math.max(1, scale * 0.5); vctx.strokeStyle = 'rgba(200,250,245,0.7)'; vctx.stroke();
    }
    const y = 28 + ((P.rot > 0 || P.rotT > 0) ? 6 : 0);
    bar(10, y, 40, 2, f, 0, f < 0.3 ? '#e07a68' : '#6fd6c8');
    text(f <= 0 ? 'DROWNING' : charmOn('c_gill') ? 'breath (gill)' : 'breath', 54, y + 3, 5, '#bfeee8', 'left');
  }
  if (DBW.grate && P.ground && P.x > DBW.grate.x0 && P.x < DBW.grate.x1 && Math.abs(P.y - DBW.grate.y) < 2) {
    const sx = P.x - cam.x, sy = P.y - cam.y - 38, tw = textW('↓ + Space', 6) + 10;
    box(sx - tw / 2, sy - 8, tw, 11, 0.7); text('↓ + Space', sx, sy, 6, '#bfeee8', 'center', { weight: 500 });
  }
});

// ================================================================== decor props
const DB_DECO = { lamp: ['db_lamp', 'loop'], bones: ['db_bones', 'loop'], window: ['db_window', 'idle'], statue: ['db_statue', 'idle'], bell: ['db_bell', 'idle'] };
SPAWNS.db_prop = (s, c) => {
  dbEnsure();
  const d = DB_DECO[s.kind]; if (!d) return;
  const sh = sheet(d[0]);
  const p = { type: 'db_' + s.kind, x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, sh.has(d[1]) ? d[1] : Object.keys(sh.tags)[0] || d[1], true) };
  p.anim.t = rand(0, 400);
  if (s.kind === 'lamp') p.update = () => addLight(p.x, p.y - 32, 56 + Math.sin(time * 7 + p.x) * 3, '110,230,210', 0.85);
  if (s.kind === 'bones') p.update = () => addLight(p.x, p.y - 8, 30, '110,230,210', 0.45);
  if (s.kind === 'window') p.update = () => addLight(p.x, p.y - 36, 40, '120,200,210', 0.3);
  if (s.kind === 'bell') dbMakeBell(p, c);
  if (!sh.ok) p.draw = () => { g.fillStyle = s.kind === 'lamp' ? '#1d4a48' : '#2a3438'; g.fillRect(Math.round(p.x - 6), Math.round(p.y - 20), 12, 20); };
  props.push(p);
};
// drowned bells hang from the ceiling above their cell; strike one and its toll stuns what stands near (and falters the Choir's song)
function dbMakeBell(p, c) {
  p.y = c.fy - TILE; p.hung = true; p.cd = 0;
  let top = p.y; for (let k = 0; k < 8; k++) { if (isSolidT(tileAt(Math.floor(p.x / TILE), Math.floor((top - 1) / TILE)))) break; top -= TILE; }
  p.top = top;
  p.draw = () => {
    const sh = p.sh;
    if (p.top < p.y - 2) { g.fillStyle = '#1a2224'; g.fillRect(Math.round(p.x) - 1, Math.round(p.top), 2, Math.round(p.y - p.top)); }
    if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, 1, { pivot: [16, 0] });
    else { g.fillStyle = '#2f5f55'; g.fillRect(Math.round(p.x - 10), Math.round(p.y + 10), 20, 26); }
  };
  p.update = dt => { p.cd -= dt; if (p.anim.tag === 'ring' && p.anim.done) p.anim.set('idle', true); addLight(p.x, p.y + 30, 24, '110,220,200', 0.25); };
  p.hurtbox = () => rect(p.x - 11, p.y + 12, p.x + 11, p.y + 46);
  p.onHit = info => dbRingBell(p, info);
}
function dbRingBell(p) {
  if (p.cd > 0) return;
  p.cd = 1.2; p.anim.set(p.sh.has('ring') ? 'ring' : 'idle', false);
  dbSfx.toll(0.9 + (p.x % 7) * 0.02); shake = Math.max(shake, 3); hitstop = Math.max(hitstop, 0.05);
  DBW.rings = DBW.rings || []; DBW.rings.push({ x: p.x, y: p.y + 32, r: 6, life: 0.9 });
  for (const e of enemies) if (e.alive && Math.hypot(e.x - p.x, e.y - (p.y + 30)) < 110 && e.hit) e.hit({ dmg: 8, poise: 60, dir: sign(e.x - p.x), kind: 'env', x: e.x, y: e.y - 10, quiet: true });
  if (boss && boss.alive && boss.onBell) boss.onBell(p);
}
HOOKS.render.push(() => {
  if (!DBW.rings || !DBW.rings.length) return;
  for (const r of DBW.rings) {
    const a = Math.max(0, r.life / 0.9), n = Math.ceil(r.r * 0.6);
    for (let k = 0; k < n; k++) { const t = k / n * 6.283, x = r.x + Math.cos(t) * r.r, y = r.y + Math.sin(t) * r.r * 0.8; g.fillStyle = `rgba(160,240,225,${0.7 * a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); }
  }
});

// ================================================================== enemies
Object.assign(ENEMY, {
  db_pilgrim: { hp: 150, cinders: 150, speed: 19, aggro: 150, range: 46, poise: 22, stance: 70, dmg: { swing: 32, lunge: 28 }, cool: [1.0, 1.8], lunge: { lunge: 150 } },
  db_barnacle: { hp: 180, cinders: 170, speed: 19, aggro: 130, range: 38, poise: 40, stance: 110, dmg: { snap: 30 }, cool: [0.9, 1.6], guard: true },
  db_eel: { hp: 110, cinders: 160, speed: 70, aggro: 170, range: 150, poise: 16, stance: 60, dmg: { lunge: 34 }, cool: [2.2, 3.4], flying: true },
});
Object.assign(ATTACK_TAGS, { db_pilgrim: ['swing', 'lunge'], db_barnacle: ['snap'], db_eel: ['lunge'] });
function dbSpawnSpec(key) {
  const m = /:sp(\d+)$/.exec(key || ''); return m && room && room.def.spawns ? room.def.spawns[+m[1]] : null;
}

// ---- drowned pilgrim: shambles, swings its censer; some wait under the silt and rise when you pass
ENEMY_CLASSES.db_pilgrim = class extends Enemy {
  constructor(type, x, y, key) {
    super(type, x, y, key);
    const s = dbSpawnSpec(key);
    if (s && s.hidden && this.sh.has('rise')) { this.state = 'buried'; this.anim.set('rise', false); this.anim.i = 0; this.anim.t = 0; }
  }
  hit(info) { if (this.state === 'buried') this.emerge(); if (this.state === 'rise') { this.hp -= Math.round(info.dmg); this.flash = 1; popup(info.x, info.y - 10, Math.round(info.dmg)); sfx.hit(); if (this.hp <= 0) this.die(info); return; } super.hit(info); }
  emerge() { if (this.state !== 'buried') return; this.state = 'rise'; this.anim.set('rise', false); this.aggro = true; this.facePlayer(); dbSfx.splash(0.5); for (let i = 0; i < 8; i++) particles.push({ x: this.x + rand(-8, 8), y: this.y - 2, vx: rand(-30, 30), vy: -rand(20, 80), g: 300, life: 0.6, kind: 'dust' }); }
  update(dt) {
    if (this.state === 'buried') {
      this.flash = Math.max(0, this.flash - dt * 5);
      if (Math.abs(P.x - this.x) < 64 && Math.abs(P.y - this.y) < 40 && P.state !== 'dead') this.emerge();
      return;
    }
    if (this.state === 'rise') { this.anim.update(dt); this.flash = Math.max(0, this.flash - dt * 5); this.gravity(dt); if (this.anim.done) { this.setA('idle', 'idle'); this.cool = 0.5; } return; }
    super.update(dt);
    if (this.alive && Math.random() < 0.02) addLight(this.x + this.face * 8, this.y - 14, 18, '110,230,210', 0.5);
  }
  hurtbox() { return this.state === 'buried' ? null : super.hurtbox(); }
  draw() {
    if (this.state === 'buried') { if (Math.floor(time * 2 + this.id) % 3 === 0) { g.fillStyle = 'rgba(120,230,210,0.5)'; g.fillRect(Math.round(this.x) - 3, Math.round(this.y) - 2, 1, 1); g.fillRect(Math.round(this.x) + 2, Math.round(this.y) - 2, 1, 1); } return; }
    super.draw();
  }
};

// ---- barnacle crawler: guards its front with a crusted shell (heavy blows, backstabs and plunges crack it)
ENEMY_CLASSES.db_barnacle = class extends Enemy {
  hit(info) {
    const c = this.cfg;
    const blocks = c.guard && !info.crit && info.kind !== 'heavy' && ['idle', 'walk', 'guard'].includes(this.state) && info.dir === -this.face && info.kind !== 'spell';
    super.hit(info);
    if (blocks && this.alive && this.sh.has('shell')) { this.shellT = 0.7; this.anim.set('shell', false); }
  }
  update(dt) {
    if (this.shellT > 0 && ['idle', 'walk'].includes(this.state)) {
      this.shellT -= dt; this.anim.update(dt); if (this.anim.done) this.anim.hold();
      this.vx *= Math.pow(0.02, dt); this.gravity(dt); this.flash = Math.max(0, this.flash - dt * 5); this.cool -= dt;
      if (this.shellT <= 0) this.setA('idle', 'idle');
      return;
    }
    super.update(dt);
  }
};

// ---- lantern eel: glides under the surface; when you come near (or swim), its lure flares and it lunges — out of the water if need be
ENEMY_CLASSES.db_eel = class extends Enemy {
  constructor(type, x, y, key) {
    super(type, x, y, key);
    this.y = y - 8; this.hy = this.y; this.home = x; this.st = 'swim'; this.state = 'idle'; this.face = Math.random() < 0.5 ? -1 : 1;
    this.w = 30; this.h = 12; this.pool = this.findPool();
    this.anim.set(this.sh.has('swim') ? 'swim' : Object.keys(this.sh.tags)[0] || 'swim', true); this.anim.t = rand(0, 500);
  }
  findPool() {   // horizontal extent of the water around the spawn
    let x0 = this.x, x1 = this.x;
    while (x0 > 8 && dbDeepAt(x0 - 8, this.y)) x0 -= 8;
    while (x1 < room.pw - 8 && dbDeepAt(x1 + 8, this.y)) x1 += 8;
    const sf = dbSurface(this.x, this.y);
    let yb = this.y; while (yb < room.ph - 8 && dbDeepAt(this.x, yb + 8)) yb += 8;
    return { x0: x0 + 10, x1: x1 - 10, top: sf.y, bottom: yb };
  }
  hurtbox() {
    if (!this.alive) return null;
    const hx = 20, hy = 7;
    return rect(this.x - hx, this.y - hy, this.x + hx, this.y + hy);
  }
  critable() { return false; }
  hit(info) {
    if (!this.alive) return;
    const pre = this.state; super.hit(info);
    if (!this.alive) { this.vx = info.dir * 40; this.vy = -20; return; }
    if (this.state === 'hurt') { this.anim.set(this.sh.has('hurt') ? 'hurt' : 'swim', false); if (this.st === 'leap') this.vx = info.dir * 60; else { this.vx = info.dir * 90; this.vy = 0; } }
    if (this.state === 'stagger' || this.state === 'parried') this.anim.set(this.sh.has('hurt') ? 'hurt' : 'swim', false);
    if (pre === 'attack' && this.st === 'leap') this.state = 'attack';   // a leap is committed
  }
  onParried() { super.onParried(); if (this.st === 'leap') { this.vx = -this.vx * 0.5; } }
  update(dt) {
    const c = this.cfg;
    this.flash = Math.max(0, this.flash - dt * 5); this.poise = Math.max(0, this.poise - dt * 12); this.stance = Math.max(0, this.stance - dt * 6); this.dmgT -= dt;
    this.anim.update(dt); this.t += dt; this.cool -= dt;
    const wet = dbDeepAt(this.x, this.y);
    if (this.state === 'dead') {
      this.vx *= Math.pow(0.1, dt);
      if (wet) this.vy = approach(this.vy, 18, 60 * dt); else this.vy = Math.min(this.vy + 600 * dt, 300);
      this.x += this.vx * dt; this.y += this.vy * dt;
      if (solidAtPx(this.x, this.y + 4)) { this.y -= this.vy * dt; this.vy = 0; }
      if (this.anim.done && !this.gone) { this.gone = true; spawnFx(fxOr('death_ash', 'dust'), this.x, this.y + 8, this.face); for (let i = 0; i < 10; i++) DBW.bubbles.push({ x: this.x + rand(-10, 10), y: this.y, vy: -rand(20, 50), life: 3, r: 1 }); }
      return;
    }
    const P0 = this.pool, dx = P.x - this.x, pdy = (P.y - 14) - this.y;
    const pWet = dbDeepAt(P.x, P.y - 13);
    if (!this.aggro && Math.abs(dx) < c.aggro && Math.abs(pdy) < 120 && P.state !== 'dead') this.aggro = true;
    if (this.state === 'hurt' || this.state === 'stagger' || this.state === 'parried') {
      this.t2 = (this.t2 || 0) + dt;
      if (this.st === 'leap') this.leapPhys(dt);
      else { this.vx *= Math.pow(0.05, dt); this.vy *= Math.pow(0.05, dt); this.move(dt); }
      const T = this.state === 'hurt' ? 0.35 : this.state === 'stagger' ? 1.4 : 1.2;
      if (this.t2 > T && (this.st !== 'leap' || wet)) { this.t2 = 0; this.state = 'idle'; this.st = 'swim'; this.anim.set('swim', true); this.cool = Math.max(this.cool, 0.7); }
      return;
    }
    switch (this.st) {
      case 'swim': {
        if (this.anim.tag !== 'swim') this.anim.set('swim', true);
        let tx, ty;
        if (this.aggro) {
          tx = clamp(P.x - sign(dx || 1) * 40, P0.x0, P0.x1);
          ty = pWet ? clamp(P.y - 14, P0.top + 10, P0.bottom) : P0.top + 14;
        } else { tx = this.home + Math.sin(this.t * 0.5) * 50; ty = this.hy + Math.sin(this.t * 1.3) * 5; }
        tx = clamp(tx, P0.x0, P0.x1); ty = clamp(ty, P0.top + 10, P0.bottom);
        this.vx = approach(this.vx, clamp((tx - this.x) * 1.6, -c.speed, c.speed), 160 * dt);
        this.vy = approach(this.vy, clamp((ty - this.y) * 1.6, -c.speed * 0.6, c.speed * 0.6), 160 * dt);
        if (Math.abs(this.vx) > 6) this.face = sign(this.vx);
        this.move(dt);
        // strike: in reach, and you're in the water or hanging/standing close above it
        const inReach = Math.abs(dx) < (pWet ? 90 : 120) && (pWet ? Math.abs(pdy) < 50 : (P.y < P0.top + 20 && P.y > P0.top - 110));
        if (this.aggro && this.cool <= 0 && inReach && P.state !== 'dead' && (DBW.eelT || 0) < time) {
          this.st = 'coil'; this.state = 'attack'; this.face = sign(dx || 1); this.anim.set(this.sh.has('lunge') ? 'lunge' : 'swim', false);
          this.atkId = ++hazardId; this.hitIds = new Set(); this.t2 = 0; DBW.eelT = time + 0.6;
          this.tgt = { x: P.x, y: P.y - 14 }; this.wetStrike = pWet;
        }
        break;
      }
      case 'coil': {
        this.t2 += dt; this.vx *= Math.pow(0.02, dt); this.vy *= Math.pow(0.02, dt); this.move(dt);
        this.face = sign((P.x - this.x) || this.face); this.tgt = { x: P.x, y: P.y - 14 };
        const an = this.anim;
        if (an.i >= 3 || this.t2 > 0.9 || !this.sh.ok) {   // launch
          const sf = P0.top;
          if (this.wetStrike || dbDeepAt(P.x, P.y - 13)) {
            const a = Math.atan2(this.tgt.y - this.y, this.tgt.x - this.x); this.vx = Math.cos(a) * 240; this.vy = Math.sin(a) * 240;
          } else {
            const h = clamp(sf - (P.y - 18) + 10, 30, 130), gv = 620, vy0 = Math.sqrt(2 * gv * h), ta = vy0 / gv;
            let vx = (this.tgt.x - this.x) / ta;
            const lo = (P0.x0 - this.x) / (2 * ta), hi = (P0.x1 - this.x) / (2 * ta);
            vx = clamp(vx, Math.min(lo, hi), Math.max(lo, hi)); vx = clamp(vx, -260, 260);
            this.vx = vx; this.vy = -vy0; this.y = Math.min(this.y, sf + 6);
            spawnFx(fxOr('db_splash', 'dust'), this.x, sf + 2, 1, null, { bottom: true }); dbSfx.splash(0.6);
          }
          this.st = 'leap'; this.t2 = 0; sfx.swing(); this.leapWet = this.wetStrike;
        } else if (an.changed && an.i === 2) { spawnFx('telegraph', this.x + this.face * 14, this.y - 10, this.face); sfx.glint(); }
        addLight(this.x + this.face * 12, this.y - 8, 20 + this.t2 * 30, '120,240,220', 0.9);
        break;
      }
      case 'leap': {
        this.t2 += dt; this.leapPhys(dt);
        if (this.anim.tag === 'lunge' && this.anim.i >= 5 && this.t2 < 0.6) { this.anim.i = 4; this.anim.t = 0; }   // jaws stay open in flight
        const r = this.jawRect();
        if (!this.hitIds.has(0) && overlap(r, playerHurtbox()) && hurtPlayer(c.dmg.lunge * NGP.dmg, sign(this.vx || this.face), this.atkId, { parryable: true, src: this })) this.hitIds.add(0);
        if (this.t2 > 0.2 && dbDeepAt(this.x, this.y) && this.vy > 0 && !this.leapWet) { this.st = 'swim'; this.state = 'idle'; this.cool = rand(...c.cool); spawnFx(fxOr('db_splash', 'dust'), this.x, P0.top + 2, 1, null, { bottom: true }); dbSfx.splash(0.5); this.vy *= 0.3; this.vx *= 0.4; }
        if (this.leapWet && this.t2 > 0.5) { this.st = 'swim'; this.state = 'idle'; this.cool = rand(...c.cool); }
        if (this.t2 > 2.5) { this.x = this.home; this.y = this.hy; this.vx = this.vy = 0; this.st = 'swim'; this.state = 'idle'; this.cool = 1; }
        break;
      }
    }
    if (this.alive) addLight(this.x + this.face * 14, this.y - 8, 26, '110,235,215', this.st === 'coil' ? 1 : 0.55);
  }
  jawRect() { const x = this.x + this.face * 22; return rect(x - 11, this.y - 8, x + 11, this.y + 8); }
  leapPhys(dt) {
    const wet = dbDeepAt(this.x, this.y);
    if (this.leapWet) { this.vx *= Math.pow(0.4, dt); this.vy *= Math.pow(0.4, dt); }
    else if (!wet) this.vy = Math.min(this.vy + 620 * dt, 380);
    else { this.vy = approach(this.vy, 0, 500 * dt); }
    if (Math.abs(this.vx) > 5) this.face = sign(this.vx);
    this.move(dt, true);
  }
  move(dt, free) {
    const nx = this.x + this.vx * dt, ny = this.y + this.vy * dt;
    if (solidAtPx(nx + sign(this.vx) * 16, this.y)) this.vx = -this.vx * 0.4; else this.x = nx;
    if (solidAtPx(this.x, ny + sign(this.vy) * 7)) this.vy = -this.vy * 0.3; else this.y = ny;
    if (!free) { this.y = Math.max(this.y, this.pool.top + 8); this.x = clamp(this.x, this.pool.x0, this.pool.x1); }
    this.x = clamp(this.x, 10, room.pw - 10); this.y = clamp(this.y, 10, room.ph - 10);
  }
  draw() {
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' || this.state === 'parried' ? { flash: 0.18 + 0.12 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (this.state === 'dead' && this.anim.done) return;
    if (this.st === 'leap' || (this.state === 'dead' && !dbDeepAt(this.x, this.y))) opt.rot = Math.atan2(this.vy, Math.abs(this.vx) + 1) * 0.9;
    if (this.sh.ok) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
    else { g.fillStyle = '#1d3a36'; g.fillRect(Math.round(this.x - 18), Math.round(this.y - 4), 36, 8); g.fillStyle = '#8ff0e0'; g.fillRect(Math.round(this.x + this.face * 16), Math.round(this.y - 10), 2, 2); }
    if (this.hp < this.maxHp && this.alive && this.dmgT > -4) {
      const w = 20, x = Math.round(this.x - w / 2), y = Math.round(this.y - 16);
      g.fillStyle = 'rgba(10,6,8,0.8)'; g.fillRect(x - 1, y - 1, w + 2, 4); g.fillStyle = '#8a1a1a'; g.fillRect(x, y, Math.max(0, w * this.hp / this.maxHp), 2);
    }
  }
};

// ---- walkers that end up in deep water wade slowly (and never drown)
HOOKS.update.push(dt => {
  if (!DBW.cells.length && !DBW.tide) return;
  for (const e of enemies) if (e.alive && !e.cfg.flying && e.type !== 'db_eel' && dbDeepAt(e.x, e.y - 6)) { e.vx *= Math.pow(0.2, dt); if (e.vy > 40) e.vy = 40; }
});

// ---- debug / test helpers (see also the bosses below)
window.__db = { get DBW() { return DBW; }, get DBS() { return DBS; }, deep: dbDeepAt, surface: dbSurface, tideTo: dbTideTo };

// ================================================================== THE FERRYMAN'S BOAT (DB5): a drifting black platform
SPAWNS.db_boat = (s, c) => {
  dbEnsure();
  const surf = (s.y + 1) * TILE;                      // the mere's surface (the spawn row sits just above it)
  const B = { x: c.cx, deck: surf - 16, x0: s.x0 * TILE + 58, x1: s.x1 * TILE - 58, v: 0, dir: 1, wait: 0, face: 1, moved: 0, sh: sheet('db_boat'), carry: false };
  B.dyn = { x0: 0, x1: 0, y0: B.deck, y1: B.deck + 5, oneway: true, on: () => true };
  const sync = () => { B.dyn.x0 = B.x - 44; B.dyn.x1 = B.x + 44; };
  sync(); room.dyn.push(B.dyn); DBW.boat = B;
  B.anim = new Anim(B.sh, B.sh.has('rock') ? 'rock' : 'idle', true);
  props.push({ type: 'db_boat', x: B.x, y: B.deck + 20, face: 1, sh: B.sh, anim: B.anim,
    update(dt) { this.x = B.x; this.face = B.face; addLight(B.x + B.face * 53, B.deck - 4, 44, '110,235,215', 0.8); },
    draw() { if (B.sh.ok) drawSprite(B.sh, B.anim.frame, B.x, B.deck + 20, B.face, { bottom: true }); else { g.fillStyle = '#101418'; g.fillRect(Math.round(B.x - 50), B.deck, 100, 10); } } });
  B.sync = sync;
};
function dbBoatUpdate(dt) {
  const B = DBW.boat; if (!B) return;
  const onDeck = P.ground && P.x > B.dyn.x0 - 3 && P.x < B.dyn.x1 + 3 && Math.abs(P.y - B.deck) < 2;
  const fight = boss && boss.kind === 'ferryman' && boss.active && boss.alive;
  // it drifts back and forth while the Ferryman fights; afterwards it ferries whoever stands on it across
  let want = 0;
  if (fight || onDeck) {
    if (B.wait > 0) B.wait -= dt;
    else {
      if (!fight && onDeck && !B.trip) { B.trip = true; B.dir = (B.x - B.x0) < (B.x1 - B.x) ? 1 : -1; }
      want = B.dir * (fight ? 30 * (boss.phase === 2 ? 1.3 : 1) : 38);
      if ((B.dir > 0 && B.x >= B.x1) || (B.dir < 0 && B.x <= B.x0)) { B.dir = -B.dir; B.wait = fight ? 2.2 : 1e9; want = 0; }
    }
  } else { B.trip = false; if (B.wait > 100) B.wait = 0; }
  B.v = approach(B.v, want, 40 * dt);
  const dx = B.v * dt, nx = clamp(B.x + dx, B.x0, B.x1), real = nx - B.x;
  B.x = nx; if (Math.abs(B.v) > 3) B.face = sign(B.v);
  B.sync();
  if (onDeck && real) { const px = P.x + real; if (!solidAtPx(px + sign(real) * 6, P.y - 8)) P.x = px; }
  if (Math.abs(B.v) > 10 && Math.random() < 0.3) particles.push({ x: B.x - B.face * 52, y: B.deck + 12, vx: -B.face * 20, vy: -rand(5, 15), life: 0.5, kind: 'db_foam' });
}
HOOKS.update.push(dt => { if (DBW.boat) dbBoatUpdate(dt); });

// ================================================================== THE FERRYMAN (DB5 mini-boss)
BOSS_INFO.ferryman = { name: 'The Ferryman', hp: 1400, cinders: 5200, reward: ['w:barnacle_fang', 'emberstone'],
  quote: '“One breath for the crossing. You have not paid it.”' };
function dbWave(x, y, dir, src, dmg = 34) {
  const id = ++hazardId, lake = DBW.boat ? [DBW.boat.x0 - 58, DBW.boat.x1 + 58] : [0, room.pw];
  hazards.push({ x, y, vx: dir * 150, w: 22, h: 26, dmg: BOSS_DMG * dmg * NGP.dmg, id, life: 3.2, dir, dbWave: true,
    update(h, dt) {
      h.x += h.vx * dt; if (h.x < lake[0] || h.x > lake[1]) h.life = 0;
      if (Math.random() < 0.5) particles.push({ x: h.x + rand(-8, 8), y: h.y - rand(4, 18), vx: h.dir * 30, vy: -rand(20, 60), g: 300, life: 0.4, kind: 'db_foam' });
      addLight(h.x, h.y - 10, 30, '110,230,210', 0.5);
    } });
}
HOOKS.render.push(() => {
  const ws = fxSheet('db_wave');
  for (const h of hazards) if (h.dbWave) {
    if (ws.ok) drawSprite(ws, ws.first('fx_db_wave') + Math.floor(time * 11) % 4, h.x, h.y + 2, h.dir, { bottom: true });
    else { g.fillStyle = 'rgba(150,220,210,0.7)'; g.fillRect(Math.round(h.x - 8), Math.round(h.y - 16), 16, 16); }
  }
  for (const k of DBW.hooks || []) {
    const n = Math.ceil(Math.hypot(k.x - k.ox, k.y - k.oy) / 3);
    for (let i = 0; i <= n; i++) { const t = i / n; g.fillStyle = i % 2 ? '#3a3430' : '#6a5e52'; g.fillRect(Math.round(lerp(k.ox, k.x, t)), Math.round(lerp(k.oy, k.y, t) + Math.sin(t * 3.14) * 3), 1, 1); }
    const hs = fxSheet('db_hook');
    if (hs.ok) drawSprite(hs, hs.first('fx_db_hook') + Math.floor(time * 10) % 2, k.x, k.y, sign(k.vx || 1), { center: true });
    addLight(k.x, k.y, 30, '110,235,215', 0.8);
  }
});
function dbUpdateHooks(dt) {
  if (!DBW.hooks) return;
  for (const k of DBW.hooks) {
    const b = k.src, alive = b && b.alive && boss === b;
    if (alive) { const o = b.hookOrigin(); k.ox = o.x; k.oy = o.y; }
    k.t += dt;
    if (k.st === 'out') {
      k.x += k.vx * dt; k.y += k.vy * dt;
      if (overlap(rect(k.x - 5, k.y - 5, k.x + 5, k.y + 5), playerHurtbox()) && hurtPlayer(BOSS_DMG * 22 * NGP.dmg, sign(k.vx), k.id, { src: b })) { k.st = 'pull'; k.t = 0; sfx.hit(); }
      else if (k.t > 0.75 || solidAtPx(k.x, k.y)) { k.st = 'back'; k.t = 0; }
    } else if (k.st === 'pull') {
      // reel the player in toward the Ferryman's oar
      if (!alive || P.state === 'dead') { k.st = 'back'; continue; }
      const dx = (b.x + b.face * 44) - P.x;
      P.pushVx = sign(dx) * Math.min(260, Math.abs(dx) * 6); if (P.vy < 0) P.vy = 0;
      k.x = P.x; k.y = P.y - 14;
      if (k.t > 0.5 || Math.abs(dx) < 10) { k.st = 'back'; k.t = 0; if (b.state === 'attack' && b.atk === 'hook') b.start('sweep'); }
    } else {
      const dx = k.ox - k.x, dy = k.oy - k.y, d = Math.hypot(dx, dy) || 1;
      k.x += dx / d * Math.min(d, 420 * dt); k.y += dy / d * Math.min(d, 420 * dt);
      if (d < 6 || !alive) k.gone = true;
    }
  }
  DBW.hooks = DBW.hooks.filter(k => !k.gone);
}
class DbFerryman extends MetaBoss {
  get L() { return DBW.boat ? DBW.boat.x0 - 30 : 11 * TILE; }
  get R() { return DBW.boat ? DBW.boat.x1 + 30 : 39 * TILE; }
  setS(st, tag, loop = true) { if (tag === 'walk' || tag === 'glide' || tag === 'crawl') tag = 'stride'; super.setS(st, tag, loop); }
  start(m) { super.start(m); if (this.state === 'walk') this.setS('walk', 'stride'); }
  hookOrigin() { const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.hook; return sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 60, y: this.y - 76 }; }
  draw() {
    super.draw();
    if (this.alive && this.state !== 'dormant') { const o = this.hookOrigin(); if (!(this.state === 'attack' && this.atk === 'hook' && this.anim.i >= 5 && this.anim.i <= 9)) addLight(o.x, o.y + 8, 60, '110,235,215', 0.9); }
    addLight(this.x, this.y - 70, 26, '110,235,215', 0.35);
  }
}
function makeFerryman(x, y) {
  const b = new DbFerryman('ferryman', x, y, {
    sheets: ['ferryman'], stanceMax: 230, walkSpeed: 58, prefer: 80, p2at: 0.5, p2speed: 1.2, p2tag: 'flare', critRange: 64,
    introTag: 'idle', cool1: [0.9, 1.5], cool2: [0.55, 1.0], victory: 'FARE PAID', deathParticle: 'db_glow',
    weights(d, p2) {
      if (d < 100) return { sweep: 2.4, slam: 1.4, vault: 0.4, hook: 0.3, flare: p2 ? 0.8 : 0.3 };
      if (d < 220) return { walk: 1.6, hook: 1.8, slam: 1.0, vault: 1.0, flare: p2 ? 1.2 : 0.7 };
      return { walk: 2.0, hook: 1.4, vault: 1.4, flare: p2 ? 1.4 : 0.9 };
    },
    chains: { sweep(d) { return d < 100 ? 'slam' : 'vault'; }, slam(d) { return this.phase === 2 ? 'flare' : d < 100 ? 'sweep' : 'hook'; }, vault: 'sweep', flare: 'hook' },
    moves: {
      sweep: { dmg: [46], shake: 3, step: 30, parry: true },
      slam: { dmg: [54], shake: 7, spawn(at) {
        spawnFx(fxOr('db_splash', 'dust'), at.x, this.floor, 1, null, { bottom: true }); dbSfx.splash(1); sfx.boom();
        dbWave(at.x, this.floor, this.face, this);
        if (this.phase === 2) dbWave(at.x, this.floor, -this.face, this, 30);
      } },
      hook: { dmg: [], spawn(at) {
        const a = Math.atan2(P.y - 14 - at.y, P.x - at.x);
        (DBW.hooks = DBW.hooks || []).push({ x: at.x, y: at.y, ox: at.x, oy: at.y, vx: Math.cos(a) * 300, vy: Math.sin(a) * 300, t: 0, st: 'out', id: ++hazardId, src: this });
        sfx.shoot(); tone(420, 0.2, 0.05, 'triangle', 0.6);
      } },
      flare: { dmg: [], spawn(at) {
        const n = this.phase === 2 ? 5 : 3;
        for (let k = 0; k < n; k++) {
          const a = -Math.PI / 2 + (k - (n - 1) / 2) * 0.5;
          projectiles.push({ owner: 'enemy', kind: 'dbwisp', sh: 'fx_db_wisp', x: at.x, y: at.y, vx: Math.cos(a) * 110, vy: Math.sin(a) * 110, homing: 1.5, dmg: BOSS_DMG * 26 * NGP.dmg, life: 4.2, r: 4, t: 0, id: ++hazardId });
        }
        flashScreen = 0.15; sfx.glint(); tone(880, 0.5, 0.05, 'sine', 1.5);
      } },
      vault: { dmg: [44], shake: 8, leap: 3, height: 64, onLand() {
        spawnFx(fxOr('db_splash', 'dust'), this.x, this.floor, 1, null, { bottom: true }); dbSfx.splash(1);
        if (this.phase === 2) { dbWave(this.x, this.floor, 1, this, 28); dbWave(this.x, this.floor, -1, this, 28); }
      } },
    },
    wake() { return P.x > 7 * TILE && P.y > 6 * TILE && P.x < 44 * TILE; },
    ambient() { if (Math.random() < 0.2) particles.push({ x: this.x + rand(-12, 12), y: this.floor - 1, vx: rand(-10, 10), vy: -rand(4, 12), life: 0.6, kind: 'db_foam' }); },
    onPhase2() { toast('The lantern burns cold and bright.'); shake = 6; },
    onDeath() { DBW.hooks = []; victoryBanner = { text: 'FARE PAID', t: 0 }; setTimeout(() => dbSfx.toll(0.7), 600); },
  });
  b.floor = y; b.baseY = y;
  return b;
}
BOSS_SPAWN.ferryman = (cx, fy) => sheet('ferryman').ok ? makeFerryman(cx, fy) : null;
BOSS_CUTS.ferryman = b => [
  act(() => { b.face = -1; b.anim.set('idle', true); }),
  bossPan(b, 50, 1.2),
  say('', 'A figure stands on the black water, waiting for a fare.'),
  act(() => { holdAnim(b, 'flare'); }), wait(0.9),
  act(() => { flashScreen = 0.2; dbSfx.toll(0.8); shake = 4; }), wait(0.8),
];
PHASE2_LINES.ferryman = ['', 'The Ferryman lifts his lantern. Every soul he ever carried looks back at you.'];
HOOKS.enter.push(def => {
  DBW.hooks = [];
  if (def.id === 'DB5') room.dyn.push({ x0: 2 * TILE, x1: 6 * TILE, y0: 0, y1: TILE, on: () => !!(boss && boss.kind === 'ferryman' && boss.active && boss.alive) });
});
HOOKS.update.push(dt => dbUpdateHooks(dt));

// ================================================================== THE DROWNED CHOIR (DB6)
// A leviathan of fused drowned corpses, assembled along a swimming spine (art/gen_barrows_choir.py). Its song raises the
// arena's tide (platforms become islands); striking a drowned bell mid-song breaks it. Phase 2 (50%): faster, the water
// climbs higher and the crest faces tear loose as homing wraiths. Rewards: Tidebreath + the Choir's gear.
BOSS_INFO.choir = { name: 'The Drowned Choir', hp: 3000, cinders: 11000, reward: ['tidebreath', 'w:choir_harpoon', 'sp:drowning_hymn', 'c_pearl'],
  quote: '“Sing with us. Down here, everyone sings.”' };
const DBC = { N: 40, SEG: 9, ANGS: [], VSEQ: [0, 3, 1, 4, 2, 3, 0, 1, 4, 2, 1, 3] };
for (let i = 0; i < 17; i++) DBC.ANGS.push(-90 + i * 11.25);
DBC.rad = [];
for (let i = 0; i < DBC.N; i++) {
  const u = i / (DBC.N - 1); let r = 8.5 + 6.5 * Math.pow(Math.min(1, u / 0.28), 0.8);
  if (u > 0.42) r = 4 + (r - 4) * Math.pow(Math.max(0, 1 - (u - 0.42) / 0.58), 0.9);
  DBC.rad.push(Math.round(clamp(r, 4, 15)));
}
DBC.faces = []; for (let i = 3; i <= 23; i += 2) DBC.faces.push(i);
const dbcSeg = r => sheet('choir_seg_' + String(r).padStart(2, '0'));
function dbcMirror(a) {
  let d = a * 180 / Math.PI; const flip = Math.cos(a) < 0;
  if (flip) d = 180 - d; d = ((d + 180) % 360 + 360) % 360 - 180;
  let best = 0; for (let i = 1; i < 17; i++) if (Math.abs(DBC.ANGS[i] - d) < Math.abs(DBC.ANGS[best] - d)) best = i;
  return [best, flip];
}
const dbcDmg = d => BOSS_DMG * d * NGP.dmg;

class DbChoir extends BossBase {
  constructor(x, y) {
    super('choir', x, y);
    this.hp = this.maxHp = this.displayHp = Math.round(BOSS_INFO.choir.hp * NGP.hp);
    this.floor = y; this.sh = sheet('choir_face'); this.anim = new Anim(this.sh, 'calm', true);
    this.state = 'dormant'; this.stanceMax = 420; this.critRange = 80; this.cool = 1.2; this.bs = 'swim'; this.bt = 0;
    this.spine = []; this.hv = { x: 0, y: 0 };
    for (let i = 0; i < DBC.N; i++) this.spine.push({ x: x - 60 + i * DBC.SEG * 0.9, y: y - 20 - Math.sin(i * 0.3) * 6 });
    this.tgt = { x: x - 60, y: y - 20 }; this.hspd = 90; this.hacc = 3; this.mouthOpen = false; this.faceMode = 'calm';
    this.faceAlive = DBC.faces.map(() => true); this.faceRegrow = DBC.faces.map(() => 0);
    this.songs = 0; this.highT = 0; this.wraithCd = 6; this.side = 1; this.chainN = 0; this.parts = this.makeParts(); this.x = x; this.y = y;
  }
  get L() { return 7 * TILE; }
  get R() { return room.pw - 7 * TILE; }
  get tideY() { return DBW.tide ? DBW.tide.y : this.floor - 60; }
  get H() { return this.spine[0]; }
  // ---- parts: the head takes more, the coils less
  makeParts() {
    const B = this, alive = () => B.alive && B.active;
    const head = { name: 'head', boss: true, critRange: 80, x: 0, y: 0, face: 1, get alive() { return alive(); },
      hurtbox() { return B.headRect(); }, hit(info) { B.partHit(info, 1.25, 1.15, true); },
      critable() { return B.critable(); }, onCritStart() { B.onCritStart(); }, onParried() { B.onParried(); } };
    const parts = [head];
    for (const [a, c] of [[2, 8], [9, 15], [16, 22], [23, 30], [31, 38]])
      parts.push({ name: 'body', boss: true, critRange: 0, x: 0, y: 0, face: 1, get alive() { return alive(); },
        hurtbox() { return B.segRect(a, c); }, hit(info) { B.partHit(info, 0.75, 0.8, false); }, critable() { return false; }, onParried() {} });
    return parts;
  }
  updateParts() {
    const c = this.headC(); this.parts[0].x = c.x; this.parts[0].y = c.y + 12; this.parts[0].face = c.a < -Math.PI / 2 || c.a > Math.PI / 2 ? -1 : 1;
    for (let k = 1; k < this.parts.length; k++) { const r = this.parts[k].hurtbox(); if (r) { this.parts[k].x = (r.x0 + r.x1) / 2; this.parts[k].y = r.y1; } }
  }
  headC() { const H = this.spine[0], S1 = this.spine[1], a = Math.atan2(H.y - S1.y, H.x - S1.x); return { x: H.x + Math.cos(a) * 14, y: H.y + Math.sin(a) * 14, a }; }
  headRect() { if (this.state === 'dead') return null; const c = this.headC(); return rect(c.x - 17, c.y - 12, c.x + 17, c.y + 12); }
  segRect(a, c) {
    if (this.state === 'dead') return null;
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (let i = a; i <= c; i++) { const p = this.spine[i], r = DBC.rad[i] * 0.85; x0 = Math.min(x0, p.x - r); x1 = Math.max(x1, p.x + r); y0 = Math.min(y0, p.y - r); y1 = Math.max(y1, p.y + r); }
    return rect(x0, y0, x1, y1);
  }
  partHit(info, m, pm, head) {
    if (!this.alive) return;
    BossBase.prototype.hit.call(this, { ...info, dmg: info.dmg * m, poise: (info.poise || 0) * pm });
    for (let i = 0; i < 4; i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 90), vy: -rand(20, 90), g: 300, life: 0.5, kind: 'db_ink' });
    if (head && this.alive && this.bs !== 'stagger' && Math.random() < 0.25) this.faceScream(0.4);
  }
  critable() { return this.state === 'stagger' && !this.critDone && this.headC().y < this.tideY + 6; }
  canStagger() { return this.alive && this.bs !== 'intro'; }
  stagger() {
    this.critDone = false; this.stanceImmune = 7; this.staggers = (this.staggers || 0) + 1;
    this.stanceMax = Math.min(this.stanceMax * 1.15, (this.stanceBase || (this.stanceBase = this.stanceMax)) * 2);
    this.stance = 0; this.state = 'stagger'; this.go('stagger'); this.t = 2.4; this.mouthOpen = true; this.dbSong = null;
    const H = this.H; this.tgt = { x: clamp(H.x, this.L, this.R), y: this.tideY - 16 }; this.hspd = 200; this.hacc = 6;
    sfx.glint(); sfx.roar(); spawnFx(fxOr('parry_flash', 'parry_spark'), H.x, H.y, 1); shake = 8; this.faceScream(1.2);
    if (DBW.tide && DBW.tide.target < DBW.tide.y) dbTideTo(DBW.tide.y, 20);   // the song dies with the stagger
  }
  onBell(p) {
    if (!this.active || !this.alive) return;
    if (this.bs === 'song') {
      toast('The bell’s toll breaks the song!', 1.8);
      this.stance += 260; this.faceScream(1);
      if (this.stance >= this.stanceMax && this.canStagger() && !(this.stanceImmune > 0)) this.stagger();
      else { dbTideTo(DBW.tide.y, 18); this.toSwim(0.8); this.highT = Math.min(this.highT, 3); }
    } else this.stance += 40;
  }
  faceScream(t) { this.screamT = Math.max(this.screamT || 0, t); }
  go(bs) { this.bs = bs; this.bt = 0; this.hit0 = false; }
  activate() { super.activate(); }
  // ---- motion
  steer(dt) {
    const H = this.spine[0];
    let tx = this.tgt.x, ty = this.tgt.y;
    if (this.wob) { tx += Math.sin(time * 2.1) * this.wob; ty += Math.cos(time * 2.7) * this.wob * 0.6; }
    const dx = tx - H.x, dy = ty - H.y, dist = Math.hypot(dx, dy) || 1, want = Math.min(this.hspd * this.speed, dist * 3.2);
    const k = Math.min(1, dt * this.hacc);
    this.hv.x = lerp(this.hv.x, dx / dist * want, k); this.hv.y = lerp(this.hv.y, dy / dist * want, k);
    H.x += this.hv.x * dt; H.y += this.hv.y * dt;
    this.clampPt(H, 12);
  }
  clampPt(p, r) {
    // arena interior; the entry ledges are solid below their tops, so stay out of them
    p.x = clamp(p.x, 2 * TILE + r, room.pw - 2 * TILE - r); p.y = clamp(p.y, 2 * TILE + r, this.floor - r * 0.6);
    if (p.y > 16 * TILE - r * 0.5) p.x = Math.max(p.x, 6 * TILE + r);
    if (p.y > 12 * TILE - r * 0.5) p.x = Math.min(p.x, 50 * TILE - r);
  }
  sim(dt) {
    const S = this.spine, N = S.length;
    for (let i = 1; i < N; i++) {
      const b = S[i], u = i / N;
      b.x += Math.sin(time * 1.7 - i * 0.35) * dt * 14 * u; b.y += Math.cos(time * 1.3 - i * 0.31) * dt * 10 * u;
      if (i < N - 1) { const a = S[i - 1], c = S[i + 1]; b.x = lerp(b.x, (a.x + c.x) / 2, 0.05); b.y = lerp(b.y, (a.y + c.y) / 2, 0.05); }
    }
    for (let i = 1; i < N; i++) {
      const a = S[i - 1], b = S[i], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
      b.x = a.x + dx / d * DBC.SEG; b.y = a.y + dy / d * DBC.SEG;
      this.clampPt(b, DBC.rad[i]);
    }
    // black water streams off whatever is above the surface
    const T = this.tideY;
    if (Math.random() < 0.7) { const i = irand(0, N - 1), p = S[i]; if (p.y < T - 2) particles.push({ x: p.x + rand(-4, 4), y: p.y + DBC.rad[i] * 0.7, vx: 0, vy: rand(10, 40), g: 400, life: rand(0.4, 0.9), kind: 'db_ink' }); }
  }
  // ---- AI
  pick() {
    const H = this.H, d = Math.abs(P.x - H.x), p2 = this.phase === 2;
    const w = { bite: d < 200 ? 2.2 : 1.0, breach: 1.1, sweep: 1.0, wail: p2 ? 1.2 : 0.8, bile: d > 120 ? 1.3 : 0.6,
                song: this.highT <= 0 && (this.songs === 0 || (this.lastSongT || 0) < time - (p2 ? 16 : 22)) ? 2.5 : 0 };
    if (w[this.last]) w[this.last] *= 0.2;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((a, [, v]) => a + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return 'bite';
  }
  begin(m) { this.last = m; this.atkId = ++hazardId; this.hitIds = new Set(); this.go(m + '0'); this.state = 'attack'; this.atk = m; }
  toSwim(cool) {
    const nx = { bite: 'sweep', sweep: 'bite', breach: 'bile', bile: 'bite', wail: 'bite' }[this.last];
    if (nx && this.chainN < (this.phase === 2 ? 2 : 1) && this.bs !== 'stagger' && P.state !== 'dead' && Math.random() < (this.phase === 2 ? 0.55 : 0.3)) { this.chainN++; this.begin(nx); return; }
    this.chainN = 0; this.state = 'idle'; this.go('swim'); this.cool = cool ?? (this.phase === 2 ? rand(0.5, 0.9) : rand(0.9, 1.5)); this.mouthOpen = false; this.faceMode = 'calm';
    if (Math.random() < 0.4) this.side *= -1;
  }
  update(dt) {
    this.commonUpdate(dt);
    this.anim.update(dt); this.bt += dt; this.screamT = (this.screamT || 0) - dt;
    const S = this.spine, H = S[0], T = this.tideY, p2 = this.phase === 2;
    this.x = H.x; this.y = H.y + 20; this.camX = H.y < T + 10 ? lerp(P.x, H.x, 0.45) : P.x;
    if (this.state === 'dead') { this.deathUpdate(dt); this.steer(dt); this.sim(dt); this.updateParts(); return; }
    if (!this.active) {
      this.tgt = { x: this.x0 ?? (this.x0 = H.x), y: this.floor - 26 + Math.sin(time) * 4 }; this.hspd = 40; this.steer(dt); this.sim(dt); this.updateParts();
      if (P.x > 8 * TILE && P.x < 49 * TILE && !this.cutting) this.activate();
      return;
    }
    // tide: after a song the water holds high for a while, then drains back
    if (this.highT > 0) { this.highT -= dt; if (this.highT <= 0) dbTideTo(DBW.tide.base, 14); }
    // phase 2: faces tear loose as wraiths
    if (p2 && (this.wraithCd -= dt) <= 0 && this.bs !== 'stagger') { this.wraithCd = rand(6, 8.5); this.loseFaces(2); }
    for (let k = 0; k < this.faceAlive.length; k++) if (!this.faceAlive[k] && (this.faceRegrow[k] -= dt) <= 0) this.faceAlive[k] = true;
    if (this.phase === 1 && this.hp <= this.maxHp * 0.5 && !this.pendingPhase) {
      if (this.bs === 'swim' || this.bs === 'stagger') this.enterPhase2(); else this.pendingPhase = true;
    }
    const t = this.bt, dirP = P.x < H.x ? -1 : 1, sp = p2 ? 1.2 : 1;
    this.speed = sp; this.wob = 0;
    switch (this.bs) {
      case 'swim': {
        if (this.pendingPhase) { this.enterPhase2(); break; }
        this.state = 'idle'; this.faceMode = 'calm'; this.mouthOpen = false;
        this.tgt = { x: clamp(P.x + this.side * 110, this.L, this.R), y: Math.min(this.floor - 18, T + 46 + Math.sin(time * 1.3) * 12) }; this.wob = 10; this.hspd = 120; this.hacc = 3;
        this.cool -= dt;
        if (this.cool <= 0 && P.state !== 'dead') this.begin(this.pick());
        break;
      }
      // -- bite: surface beside you, eye flares, then a lunging bite; the head hangs exposed after
      case 'bite0': {
        this.tgt = { x: clamp(P.x - dirP * -1 * 0 + (H.x < P.x ? -80 : 80), this.L, this.R), y: T + 26 }; this.hspd = 200; this.hacc = 5;
        if (t > 0.9 || (Math.abs(H.x - this.tgt.x) < 24 && Math.abs(H.y - this.tgt.y) < 20)) { this.go('bite1'); dbSfx.hum(0.8); }
        break;
      }
      case 'bite1': {
        this.tgt = { x: H.x + (P.x - H.x) * 0.05, y: T + 4 }; this.hspd = 80; this.mouthOpen = t > 0.2;
        if (t < dt * 1.5) { const c = this.headC(); spawnFx('telegraph', c.x, c.y - 8, 1); sfx.glint(); }
        if (t > 0.5 / sp) { this.go('bite2'); this.lunge = { x: clamp(P.x + (P.x - H.x) * 0.25, this.L - 40, this.R + 40), y: Math.min(P.y - 14, T + 10) }; sfx.bossSwing(); dbSfx.splash(0.8); }
        break;
      }
      case 'bite2': {
        this.tgt = this.lunge; this.hspd = 460; this.hacc = 12; this.mouthOpen = true;
        this.headHit(52, true);
        if (t > 0.4 || Math.hypot(H.x - this.lunge.x, H.y - this.lunge.y) < 14) { this.go('bite3'); this.mouthOpen = false; shake = Math.max(shake, 4); sfx.hit(); }
        break;
      }
      case 'bite3': {   // the punish window: the head lingers, jaws shut, then sinks away
        this.tgt = { x: H.x, y: H.y + 6 }; this.hspd = 30;
        if (t > 0.65 / sp) this.toSwim();
        break;
      }
      // -- breach: foam boils where it will burst out, then a great arc across the arena (the coils hurt)
      case 'breach0': {
        if (t < dt * 1.5) { this.bx0 = clamp(P.x - dirP * 150, this.L, this.R); this.bx1 = clamp(P.x + dirP * 150, this.L, this.R); if (Math.abs(this.bx1 - this.bx0) < 200) this.bx1 = clamp(this.bx0 + dirP * 260, this.L, this.R); }
        this.tgt = { x: this.bx0, y: T + 60 }; this.hspd = 240; this.hacc = 5;
        if (Math.random() < 0.8) particles.push({ x: this.bx0 + rand(-20, 20), y: T, vx: rand(-20, 20), vy: -rand(20, 70), g: 260, life: 0.6, kind: 'db_foam' });
        if (t > 1.0 / sp) { this.go('breach1'); dbSfx.splash(1); sfx.roar(); spawnFx(fxOr('db_splash', 'dust'), this.bx0, T + 2, 1, null, { bottom: true }); }
        break;
      }
      case 'breach1': {
        const k = Math.min(1, t / (1.5 / sp)), x = lerp(this.bx0, this.bx1, k), y = T + 20 - Math.sin(k * Math.PI) * (p2 ? 130 : 110);
        this.tgt = { x, y }; this.hspd = 520; this.hacc = 14; this.mouthOpen = k > 0.2 && k < 0.7;
        this.bodyHits(40, 0, 24);
        if (k >= 1) { spawnFx(fxOr('db_splash', 'dust'), this.bx1, T + 2, 1, null, { bottom: true }); dbSfx.splash(1); shake = 6; this.go('breach2'); }
        break;
      }
      case 'breach2': this.tgt = { x: this.bx1, y: T + 70 }; this.hspd = 200; this.bodyHits(34, 0, 16); if (t > 0.6) this.toSwim(); break;
      // -- sweep: surfaces at one side, then skims the waterline across the whole arena
      case 'sweep0': {
        if (t < dt * 1.5) { this.sx0 = P.x < room.pw / 2 ? this.R + 20 : this.L - 20; this.sx1 = P.x < room.pw / 2 ? this.L - 30 : this.R + 30; }
        this.tgt = { x: this.sx0, y: T + 8 }; this.hspd = 260; this.hacc = 5;
        if (t > 1.1 / sp) { this.go('sweep1'); sfx.roar(); const c = this.headC(); spawnFx('telegraph', c.x, c.y - 10, 1); this.faceScream(0.5); }
        break;
      }
      case 'sweep1': {
        this.tgt = { x: this.sx0, y: T - 8 }; this.hspd = 100; this.mouthOpen = true;
        if (t > 0.45 / sp) this.go('sweep2');
        break;
      }
      case 'sweep2': {
        this.tgt = { x: this.sx1, y: T - 4 }; this.hspd = 270; this.hacc = 8; this.mouthOpen = true;
        this.headHit(46, false); this.bodyHits(38, 0, 18);
        if (Math.random() < 0.9) particles.push({ x: H.x + rand(-10, 10), y: T, vx: rand(-40, 40), vy: -rand(30, 90), g: 300, life: 0.5, kind: 'db_foam' });
        if (Math.abs(H.x - this.sx1) < 40 || t > 4) this.toSwim(0.9);
        break;
      }
      // -- wail: rears from the water, the faces scream; rings of sound roll out from the crest
      case 'wail0': {
        this.tgt = { x: clamp(P.x - dirP * 130, this.L, this.R), y: T - 70 }; this.hspd = 220; this.hacc = 5;
        this.faceMode = 'hum';
        if (t > 0.9 / sp) { this.go('wail1'); dbSfx.wail(1); this.faceScream(1.4); }
        break;
      }
      case 'wail1': {
        this.tgt = { x: H.x, y: T - 80 }; this.hspd = 40; this.mouthOpen = true;
        const n = p2 ? 3 : 2;
        for (let k = 0; k < n; k++) if (t >= k * 0.42 && !this['w' + k]) {
          this['w' + k] = true;
          const f = this.facePos(DBC.faces[3]) || H;
          (DBW.wails = DBW.wails || []).push({ x: f.x, y: f.y, r: 10, v: 190, id: ++hazardId, life: 2.2, src: this });
          shake = Math.max(shake, 3); dbSfx.wail(1 + k * 0.12);
        }
        if (t > 1.3) { for (let k = 0; k < 3; k++) this['w' + k] = false; this.toSwim(); }
        break;
      }
      // -- bile: teal bile spat in high arcs
      case 'bile0': {
        this.tgt = { x: clamp(P.x - dirP * 160, this.L, this.R), y: T - 40 }; this.hspd = 220; this.hacc = 5;
        if (t > 0.8 / sp) { this.go('bile1'); const c = this.headC(); spawnFx('telegraph', c.x, c.y, 1); sfx.glint(); }
        break;
      }
      case 'bile1': {
        this.tgt = { x: H.x, y: T - 50 }; this.hspd = 40; this.mouthOpen = t > 0.2;
        const n = p2 ? 5 : 3;
        if (t > 0.35 && !this.spat) {
          this.spat = true; const c = this.headC();
          for (let k = 0; k < n; k++) {
            const tx = P.x + (k - (n - 1) / 2) * 44, T0 = 0.9 + k * 0.05, dx = tx - c.x;
            (DBW.biles = DBW.biles || []).push({ x: c.x, y: c.y, vx: dx / T0, vy: -260, id: ++hazardId, t: 0 });
          }
          sfx.fire(); dbSfx.splash(0.4);
        }
        if (t > 1.0) { this.spat = false; this.toSwim(); }
        break;
      }
      // -- song: it surfaces, the crest hums, and the black water rises (strike a drowned bell to break it)
      case 'song0': {
        this.tgt = { x: clamp(room.pw / 2 + Math.sin(time) * 20, this.L, this.R), y: T - 30 }; this.hspd = 200; this.hacc = 4; this.faceMode = 'hum';
        if (t > 1.0) {
          this.go('song'); this.songs++; this.lastSongT = time; dbSfx.hum(1);
          const flood = p2 && this.songs % 3 === 0;
          const hi = (flood ? 7.5 : p2 ? 9.5 : 12.4) * TILE;
          dbTideTo(hi, flood ? 34 : 30); this.highT = 0;
          if (!SAVE.hints.dbBell) { SAVE.hints.dbBell = 1; toast('The drowned bells shiver with the song…', 3); }
          else toast(flood ? 'The Choir sings the flood.' : 'The Choir sings the tide up.', 1.6);
        }
        break;
      }
      case 'song': {
        this.tgt = { x: H.x + Math.sin(time * 0.8) * 0.5, y: T - 34 }; this.hspd = 60; this.faceMode = 'hum'; this.mouthOpen = Math.sin(time * 5) > 0;
        if (Math.floor(t * 2) !== Math.floor((t - dt) * 2)) dbSfx.hum(1 + (t % 2) * 0.1);
        if (t > 3.0) { this.highT = p2 ? 11 : 13; this.toSwim(0.6); }
        break;
      }
      case 'stagger': {
        this.tgt = { x: H.x, y: T - 14 + Math.sin(time * 3) * 3 }; this.hspd = 60; this.mouthOpen = true;
        this.t -= dt;
        if (this.t <= 0) { this.state = 'idle'; this.toSwim(0.4); }
        break;
      }
    }
    this.steer(dt); this.sim(dt); this.updateParts();
    this.updateHazards(dt);
    this.ambient(dt);
  }
  ambient() {
    const c = this.headC(); addLight(c.x, c.y - 4, this.mouthOpen ? 60 : 40, '110,240,220', 0.9);
    if (this.faceMode === 'hum' || this.screamT > 0) for (let k = 0; k < DBC.faces.length; k += 3) { const f = this.facePos(DBC.faces[k]); if (f) addLight(f.x, f.y, 26, '110,240,220', 0.6); }
  }
  headHit(dmg, parry) {
    if (this.hitIds.has('h')) return;
    const r = this.headRect(); if (r && overlap(r, playerHurtbox()) && hurtPlayer(dbcDmg(dmg), P.x < this.H.x ? -1 : 1, this.atkId * 10, { parryable: parry, src: this })) this.hitIds.add('h');
  }
  bodyHits(dmg, i0, i1) {
    if (this.hitIds.has('b')) return;
    const hb = playerHurtbox(), T = this.tideY;
    for (let i = i0; i <= i1; i++) {
      const p = this.spine[i], r = DBC.rad[i] * 0.85; if (p.y - r > T + 4) continue;
      if (overlap(rect(p.x - r, p.y - r, p.x + r, p.y + r), hb) && hurtPlayer(dbcDmg(dmg), P.x < p.x ? -1 : 1, this.atkId * 10 + 1, { src: this })) { this.hitIds.add('b'); return; }
    }
  }
  facePos(i) {
    const S = this.spine; if (!S[i + 1]) return null;
    const p0 = S[i], p1 = S[i + 1], a = Math.atan2(p0.y - p1.y, p0.x - p1.x);
    let nx = Math.sin(a), ny = -Math.cos(a); if (Math.cos(a) < 0) { nx = -nx; ny = -ny; }
    const off = DBC.rad[i] * 0.72 + 5;
    return { x: p0.x + nx * off, y: p0.y + ny * off - 2, nx, ny, a };
  }
  loseFaces(n) {
    const live = this.faceAlive.map((v, k) => v ? k : -1).filter(k => k >= 0);
    for (let j = 0; j < n && live.length; j++) {
      const k = live.splice(irand(0, live.length - 1), 1)[0], f = this.facePos(DBC.faces[k]); if (!f) continue;
      this.faceAlive[k] = false; this.faceRegrow[k] = 16;
      (DBW.wraiths = DBW.wraiths || []).push({ x: f.x, y: f.y - 6, vx: rand(-30, 30), vy: -90, t: 0, life: 6, id: ++hazardId, hp: 1 });
      dbSfx.wail(1.5);
    }
  }
  updateHazards(dt) {
    const T = this.tideY;
    for (const w of DBW.wails || []) {
      w.r += w.v * dt; w.life -= dt;
      const d = Math.hypot(P.x - w.x, P.y - 13 - w.y);
      if (Math.abs(d - w.r) < 8) hurtPlayer(dbcDmg(36), sign(P.x - w.x), w.id, { src: this });
    }
    if (DBW.wails) DBW.wails = DBW.wails.filter(w => w.life > 0 && w.r < 420);
    for (const b of DBW.biles || []) {
      b.t += dt; b.vy += 520 * dt; b.x += b.vx * dt; b.y += b.vy * dt;
      if (overlap(rect(b.x - 5, b.y - 5, b.x + 5, b.y + 5), playerHurtbox()) && hurtPlayer(dbcDmg(30), sign(b.vx), b.id, { src: this })) b.gone = true;
      if ((b.vy > 0 && b.y >= T) || solidAtPx(b.x, b.y) || b.t > 3) {
        b.gone = true; spawnFx(fxOr('db_bileburst', 'dust'), b.x, Math.min(b.y, T + 2), 1, null, { bottom: true }); dbSfx.splash(0.3);
        // a brief caustic slick where it lands
        hazards.push({ x: b.x, y: Math.min(b.y, T + 2), w: 26, h: 10, dmg: dbcDmg(12), id: ++hazardId, life: 1.2, tick: 0.4, pool: true, update(h) { if (Math.random() < 0.3) particles.push({ x: h.x + rand(-12, 12), y: h.y - 2, vx: 0, vy: -rand(10, 30), life: 0.5, kind: 'db_bile' }); } });
      }
    }
    if (DBW.biles) DBW.biles = DBW.biles.filter(b => !b.gone);
    for (const w of DBW.wraiths || []) {
      w.t += dt; w.life -= dt;
      if (w.t > 0.6) { const a = Math.atan2(P.y - 14 - w.y, P.x - w.x), sp = 105; w.vx = lerp(w.vx, Math.cos(a) * sp, Math.min(1, dt * 1.6)); w.vy = lerp(w.vy, Math.sin(a) * sp, Math.min(1, dt * 1.6)); }
      else { w.vy *= Math.pow(0.2, dt); }
      w.x += w.vx * dt; w.y += w.vy * dt;
      if (overlap(rect(w.x - 6, w.y - 6, w.x + 6, w.y + 6), playerHurtbox()) && hurtPlayer(dbcDmg(26), sign(w.vx), w.id, { src: this })) w.life = 0;
      addLight(w.x, w.y, 30, '110,240,220', 0.7);
    }
    if (DBW.wraiths) DBW.wraiths = DBW.wraiths.filter(w => w.life > 0);
  }
  enterPhase2() {
    this.phase = 2; this.pendingPhase = false; this.stance = 0; this.speed = 1.2;
    DBW.biles = []; DBW.wails = [];
    this.go('song0'); this.state = 'attack'; this.last = 'song'; this.faceScream(1.5); this.lastSongT = 0; this.highT = 0; this.wraithCd = 3;
    toast('The drowned voices rise to a shriek.'); shake = 8; sfx.roar();
    bossPhase2Scene(this);
  }
  die() {
    this.state = 'dead'; this.go('death'); this.deathK = 0; this.mouthOpen = true;
    hazards = []; DBW.biles = []; DBW.wails = []; DBW.wraiths = [];
    shake = 14; hitstop = 0.3; slowmo = 1.8; flashScreen = 0.7; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE CHOIR FALLS SILENT', t: 0 };
    dbTideTo(DBW.tide ? DBW.tide.base : 0, 26); this.highT = 0;
    this.rewards();
  }
  deathUpdate(dt) {
    this.deathK = Math.min(1, this.deathK + dt / 4);
    const H = this.H; this.tgt = { x: H.x + Math.sin(time * 2) * 10, y: lerp(this.tideY - 40, this.floor + 30, this.deathK) }; this.hspd = 50;
    if (Math.random() < 0.4 && this.deathK < 0.8) { const k = irand(0, this.faceAlive.length - 1); if (this.faceAlive[k]) { const f = this.facePos(DBC.faces[k]); this.faceAlive[k] = false; if (f) for (let i = 0; i < 8; i++) particles.push({ x: f.x, y: f.y, vx: rand(-20, 20), vy: -rand(30, 70), life: rand(1, 2), kind: 'db_glow' }); } }
    this.faceMode = 'scream';
  }
  // ---- drawing (called by renderWorld before the water, so the tide tints what's submerged)
  draw() {
    const S = this.spine, N = S.length, dead = this.state === 'dead';
    const cut = dead ? Math.max(2, Math.floor(N * (1 - this.deathK * 0.9))) : N;
    const opt = this.flash > 0 ? { flash: this.flash * 0.6 } : this.state === 'stagger' ? { flash: 0.12 + 0.08 * Math.sin(time * 20), flashColor: '#8ff0e0' } : {};
    const alpha = dead ? Math.max(0, 1 - this.deathK * 1.1) : 1;
    if (alpha <= 0) return;
    if (alpha < 1) opt.alpha = alpha;
    const fs = sheet('choir_face'), ftag = this.screamT > 0 || this.faceMode === 'scream' ? 'scream' : this.faceMode === 'hum' ? 'hum' : 'calm';
    for (const pas of ['line', 'fill']) {
      for (let i = Math.min(N - 2, cut - 2); i >= 0; i--) {
        const p0 = S[i], p1 = S[i + 1], sh = dbcSeg(DBC.rad[i]); if (!sh.ok) continue;
        const [fi, flip] = dbcMirror(Math.atan2(p0.y - p1.y, p0.x - p1.x)), tg = sh.tag(pas === 'line' ? 'line' : 'fill' + DBC.VSEQ[i % DBC.VSEQ.length]);
        drawSprite(sh, tg.from + fi, (p0.x + p1.x) / 2, (p0.y + p1.y) / 2, flip ? -1 : 1, pas === 'fill' ? { center: true, ...opt } : { center: true, alpha });
      }
      if (pas === 'line') {
        // dorsal spines and the choir's faces rise from the back (the body's fill covers their roots)
        for (let i = 4; i < Math.min(28, cut - 1); i += 2) {
          const f = this.facePos(i); if (!f) continue;
          const len = 7 + DBC.rad[i] * 0.3, bx = -Math.cos(f.a) * (Math.cos(f.a) < 0 ? -1 : 1);
          const ex = f.x + f.nx * len * 0.8 + (Math.cos(f.a) < 0 ? 1 : -1) * Math.abs(Math.cos(f.a)) * len * 0.5, ey = f.y + f.ny * len * 0.8 + 2;
          const n = Math.ceil(len);
          for (let k = 0; k <= n; k++) { const t = k / n; g.fillStyle = k < n * 0.6 ? '#0c1112' : '#1f2a28'; g.fillRect(Math.round(lerp(f.x, ex, t)), Math.round(lerp(f.y + 4, ey, t)), k < n * 0.4 ? 2 : 1, 1); }
          void bx;
        }
        if (fs.ok) for (let k = 0; k < DBC.faces.length; k++) {
          const i = DBC.faces[k]; if (i >= cut - 1 || !this.faceAlive[k]) continue;
          const f = this.facePos(i), tg = fs.tag(ftag), n = tg.to - tg.from + 1;
          drawSprite(fs, tg.from + Math.floor(time * (ftag === 'scream' ? 11 : 4) + k) % n, f.x, f.y + 9, f.nx < 0 ? -1 : 1, { alpha, ...(opt.flash ? { flash: opt.flash } : {}) });
        }
      }
    }
    const ts = sheet('choir_tail');
    if (ts.ok && cut >= N) { const a = Math.atan2(S[N - 1].y - S[N - 2].y, S[N - 1].x - S[N - 2].x), [fi, flip] = dbcMirror(a), tg = ts.tag(Math.floor(time * 3) % 2 ? 't1' : 't0'); drawSprite(ts, tg.from + fi, S[N - 1].x, S[N - 1].y, flip ? -1 : 1, { center: true, alpha }); }
    const hs = sheet('choir_head');
    if (hs.ok) { const a = Math.atan2(S[0].y - S[1].y, S[0].x - S[1].x), [fi, flip] = dbcMirror(a), tg = hs.tag(this.mouthOpen ? 'open' : 'closed'); drawSprite(hs, tg.from + fi, S[0].x, S[0].y, flip ? -1 : 1, { center: true, ...opt }); }
    else { g.fillStyle = '#687870'; for (const p of S) g.fillRect(Math.round(p.x) - 4, Math.round(p.y) - 4, 8, 8); }
    if (this.state === 'stagger' && this.critable()) { const c = this.headC(); g.fillStyle = '#8ff0e0'; const y = Math.round(c.y - 22 + Math.sin(time * 8) * 1.5); g.fillRect(Math.round(c.x) - 1, y, 3, 3); g.fillRect(Math.round(c.x), y - 1, 1, 5); g.fillRect(Math.round(c.x) - 2, y + 1, 5, 1); }
  }
}
BOSS_SPAWN.choir = (cx, fy) => sheet('choir_head').ok ? new DbChoir(cx, fy) : null;
HOOKS.render.push(() => {
  if (!boss || !(boss instanceof DbChoir)) return;
  // wail rings: teal arcs of sound (drawn only above the water)
  for (const w of DBW.wails || []) {
    const n = Math.ceil(w.r * 1.2), a = clamp(w.life / 1.2, 0.2, 1);
    for (let k = 0; k < n; k++) { const t = k / n * 6.283, x = w.x + Math.cos(t) * w.r, y = w.y + Math.sin(t) * w.r; g.fillStyle = `rgba(150,245,230,${0.85 * a})`; g.fillRect(Math.round(x), Math.round(y), 2, 1); }
    for (let k = 0; k < 6; k++) { const t = k / 6 * 6.283 + time; addLight(w.x + Math.cos(t) * w.r, w.y + Math.sin(t) * w.r, 30, '110,240,220', 0.5 * a); }
  }
  const bs = fxSheet('db_bile');
  for (const b of DBW.biles || []) { if (bs.ok) drawSprite(bs, bs.first('fx_db_bile') + Math.floor(time * 12) % 4, b.x, b.y, sign(b.vx), { center: true }); addLight(b.x, b.y, 26, '110,240,200', 0.8); }
  const ws = sheet('choir_wraith');
  for (const w of DBW.wraiths || []) if (ws.ok) drawRotated(ws, ws.first('fly') + Math.floor(time * 11) % 4, w.x, w.y, Math.atan2(w.vy, w.vx));
});
// the leviathan swims *behind* the arena's stone slabs: redraw the platform tiles over it
HOOKS.render.push(() => {
  if (!boss || !(boss instanceof DbChoir) || !room.front) return;
  const x0 = Math.max(0, Math.floor(cam.x / TILE)), x1 = Math.min(room.w - 1, Math.ceil((cam.x + W) / TILE));
  for (let ty = 0; ty < room.h; ty++) for (let tx = x0; tx <= x1; tx++) if (room.grid[ty * room.w + tx] === T_PLAT) {
    const px = tx * TILE, py = ty * TILE;
    g.drawImage(room.front, px, py, TILE, TILE, px, py, TILE, TILE);
  }
});
BOSS_CUTS.choir = b => {
  const hover = (dur, y) => ({ dur, tween: dt => { b.tgt = { x: b.H.x, y: y() }; b.hspd = 70; b.hacc = 3; b.steer(dt); b.sim(dt); } });
  return [
    act(() => { b.tgt = { x: b.H.x, y: b.floor - 26 }; }),
    { pan: { x: b.H.x, y: b.tideY - 30 }, dur: 1.2 },
    { dur: 1.4, tween: dt => { if (Math.random() < 0.8) DBW.bubbles.push({ x: b.H.x + rand(-60, 60), y: b.floor - rand(10, 40), vy: -rand(40, 90), life: 3, r: 1 + (Math.random() < 0.3) }); b.steer(dt); b.sim(dt); } },
    say('', 'Beneath the black water, a hundred drowned mouths open at once.'),
    act(() => { b.faceMode = 'hum'; dbSfx.hum(0.9); }),
    { dur: 2.4, tween: (dt, k) => { b.tgt = { x: b.H.x + 20, y: lerp(b.floor - 26, b.tideY - 80, k) }; b.hspd = 90; b.hacc = 3; b.steer(dt); b.sim(dt); const t = camTargetFor(b.H.x, Math.min(b.H.y, b.tideY) - 20); cam.x = lerp(cam.x, t.x, Math.min(1, dt * 3)); cam.y = lerp(cam.y, t.y, Math.min(1, dt * 3)); if (Math.random() < 0.8) particles.push({ x: b.H.x + rand(-40, 40), y: b.tideY, vx: rand(-40, 40), vy: -rand(40, 120), g: 300, life: 0.6, kind: 'db_foam' }); } },
    act(() => { b.mouthOpen = true; b.faceScream(1.5); sfx.roar(); dbSfx.wail(0.9); shake = 12; flashScreen = 0.35; }),
    hover(1.3, () => b.tideY - 80),
    act(() => { b.mouthOpen = false; b.faceMode = 'calm'; }),
  ];
};
PHASE2_LINES.choir = ['', 'The faces along its back tear free, shrieking, and the whole Hollow floods.'];
HOOKS.enter.push(() => { DBW.biles = []; DBW.wails = []; DBW.wraiths = []; });
Object.assign(window.__db, { choir: () => (boss instanceof DbChoir ? boss : null), boss: () => boss, SETTINGS, get hazards() { return hazards; }, get cam() { return cam; } });

HOOKS.render.push(() => { dbEnsure(); if (DBW.body || DBW.tide) dbDrawWater(); });
HOOKS.playerHurt.push((dmg, opt) => { if (window.__dbLog) window.__dbLog.push([Math.round(dmg), boss ? (boss.bs || boss.atk || boss.state) : '-', opt.src === boss ? 'boss' : (opt.src && opt.src.type) || 'env', Math.round(P.x), Math.round(P.y), P.state]); return dmg; });
window.__db.pool = (id, x0, x1, y0, y1) => { const d = ROOM_BY[id]; for (let y = y0; y <= y1; y++) d.map[y] = d.map[y].slice(0, x0) + '"'.repeat(x1 - x0 + 1) + d.map[y].slice(x1 + 1); };
window.__db.solidAt = (x, y) => isSolidT(tileAt(Math.floor(x / TILE), Math.floor(y / TILE)));
