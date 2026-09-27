// ------------------------------------------------------------------ EXPANSION 3 · agent RA: Ashen Ramparts, Rootbound Catacombs, Sunken Cathedral
// Rooms: tools/regions/80_ra.py (R5..R14, C7..C15, K5..K13). Art: art/gen_xra.py -> xra_deco (64x64 props), xra_tall
// (lancets, skull pillars), xra_rose (the rose window), xra_pano (the Hallow from the Watcher's Perch), xra_icons.
// Spawns: ra (decor: painted into the back layer, or a live prop when it moves or glows), ra_wall (back walls painted
// inside outdoor rooms), ra_amb (statue / booth / ceiling / niche / water ambushers), ra_chand (a kit crumble restyled
// as a candle chandelier), ra_water (knee-deep black water), ra_lock (holds a kit lift until its winch is freed),
// ra_hint (a gentle toast after three failed attempts at a puzzle, or when you come near something).
// Every top-level name is prefixed ra/RA (all region files share one scope).
const RA = { roomObj: null };
function raReset() {
  Object.assign(RA, { roomObj: room, back: [], walls: [], lights: [], amb: [], chands: [], waters: [], locks: [], hints: [], painted: null, toll: 0, tollT: 0, lockT: 0 });
}
function raEnsure() { if (RA.roomObj !== room) raReset(); }
Object.assign(PCOL, { ra_bone: '200,188,160', ra_ink: '20,22,34', ra_drop: '120,130,160', ra_wax: '255,214,150', ra_root: '120,88,56' });
const raSfx = {
  crack: () => { noise(0.45, 500, 0.8, 0.45, 'lowpass', 0.4); noise(0.2, 2400, 1.5, 0.2, 'highpass'); tone(70, 0.4, 0.2, 'sawtooth', 0.6); },
  curtain: () => { noise(0.35, 1400, 0.6, 0.3, 'bandpass', 0.6); tone(150, 0.2, 0.08, 'sawtooth', 0.7); },
  drop: () => { noise(0.4, 320, 0.7, 0.35, 'lowpass', 0.5); noise(0.2, 1600, 1, 0.15, 'bandpass'); },
  splash: () => { noise(0.35, 900, 0.7, 0.3, 'bandpass', 0.5); noise(0.2, 2800, 1, 0.1, 'highpass'); },
  crash: () => { noise(0.8, 700, 0.5, 0.5, 'bandpass', 0.35); [1760, 2349, 2637].forEach((f, i) => tone(f, 0.5, 0.05, 'triangle', 0.8, i * 0.05)); },
  toll: () => { tone(98, 4.2, 0.26, 'sine', 1); tone(147, 3.6, 0.12, 'triangle', 1); tone(196, 3, 0.07, 'sine', 1, 0.02); noise(0.5, 300, 0.6, 0.2, 'lowpass'); },
};

// ================================================================== decor props
// a: anchor ('b' bottom of the cell, 't' top of the cell) · live: drawn every frame (animated / emissive) · L: light
// [dx, dy, r, colour, k, flicker] · glow: into the emissive layer · sh: sheet (default xra_deco)
const RA_P = {
  wbanner: { a: 't', live: 1, fps: 5 }, pbanner: { live: 1, fps: 5 }, flag: { live: 1, fps: 6 },
  torch: { live: 1, fps: 9, dy: 10, L: [0, -26, 72, '255,170,90', 0.95, 1] }, slit: { dy: 8, L: [0, -18, 34, '150,160,230', 0.35] }, shields: { dy: 8 },
  hay: {}, rack: {}, bunk: {}, barrels: {}, horse: {}, cart: {}, winch: {}, dummy: {}, stall: {}, crenel: {}, trebuchet: {}, rubble: {},
  beacon: { live: 1, fps: 10, L: [0, -40, 150, '255,160,80', 1.3, 1] },
  bshelf: {}, coffin: {}, sarc: {}, skulls: {}, digger: {}, tomb: { f: 1 },
  rootc: { a: 't', live: 1, fps: 3 }, bonechand: { a: 't', live: 1, fps: 8, L: [0, 20, 96, '255,196,120', 0.95, 1] },
  kneel: {}, pew: {}, booth: { f: 1 }, organ: {}, altar: { L: [0, -14, 60, '255,200,130', 0.7, 1] }, saint: {},
  chand: { a: 't', live: 1, fps: 8, L: [0, 14, 80, '255,200,130', 0.9, 1] },
  votive: { live: 1, fps: 8, L: [0, -12, 46, '255,190,110', 0.7, 1] }, censer: { a: 't', live: 1, fps: 3 },
  emblem: { f: 1, a: 't', L: [0, 8, 18, '255,210,130', 0.4] },
  lancet: { sh: 'xra_tall', live: 1, glow: 1, L: [0, -48, 90, '190,200,255', 0.55] },
  skullpillar: { sh: 'xra_tall' }, rootheart: { sh: 'xra_big', a: 't', L: [0, 62, 170, '255,160,70', 1.3, 'pulse'] }, bigbell: { sh: 'prop_bell', tag: 'idle' },
};
function raFrame(sh, k, v) {   // first frame of tag k (+ variant v), or null
  if (!sh.ok) return null;
  const tag = RA_P[k] && RA_P[k].sh === 'xra_tall' && k === 'lancet' ? 'lancet_' + (v || 'gold') : k;
  const tg = (RA_P[k] && RA_P[k].tag) || tag;
  if (!sh.has(tg)) return null;
  const t = sh.tag(tg); return { t, i: t.from + (RA_P[k] && RA_P[k].f ? Math.min(v | 0, t.to - t.from) : 0) };
}
function raPos(s, c, P_) {   // pixel anchor of a decor spawn: bottom-centre of its cell, or top-centre for hung things
  return { x: c.cx + (s.dx || 0), y: (P_.a === 't' ? s.y * TILE : c.fy) + (s.dy ?? P_.dy ?? 0) };
}
SPAWNS.ra = (s, c) => {
  raEnsure();
  const P_ = RA_P[s.k]; if (!P_) return;
  const sh = sheet(P_.sh || 'xra_deco'), pos = raPos(s, c, P_), face = s.flip ? -1 : 1;
  if (P_.L) { const [dx, dy, r, col, k, fl] = P_.L; RA.lights.push([pos.x + dx * face, pos.y + dy, (s.lr || 1) * r, s.lc || col, (s.lk || 1) * k, fl]); }
  if (!(P_.live || s.live) || s.back === false) {
    if (s.back === false) { props.push(raStatic(sh, s, pos, face, P_)); return; }
    RA.back.push({ sh, s, pos, face, P_ }); return;
  }
  const p = { type: 'ra_' + s.k, x: pos.x, y: pos.y, face, anim: { update() {} }, glow: !!P_.glow, t0: rand(0, 10) };
  p.draw = () => {
    const F = raFrame(sh, s.k, s.v); if (!F) return;
    const n = F.t.to - F.t.from + 1, i = P_.f ? F.i : F.t.from + (n > 1 ? Math.floor((time + p.t0) * (P_.fps || 6)) % n : 0);
    drawSprite(sh, i, p.x, p.y, face, P_.a === 't' ? { pivot: [Math.floor(sh.frames[i].w / 2), 0], alpha: s.alpha } : { bottom: true, alpha: s.alpha });
  };
  props.push(p);
};
function raStatic(sh, s, pos, face, P_) {   // a still prop drawn in front of the room (e.g. a booth before a wall)
  return { type: 'ra_' + s.k, x: pos.x, y: pos.y, face, anim: { update() {} }, draw() { if (s.hideIf && !isSolidT(tileAt(s.hideIf[0], s.hideIf[1]))) return; const F = raFrame(sh, s.k, s.v); if (F) drawSprite(sh, F.i, pos.x, pos.y, face, P_.a === 't' ? { pivot: [32, 0] } : { bottom: true }); } };
}
// back walls inside outdoor rooms (tower interiors, the stables under the wall-walk): the indoor fade, on a rect
SPAWNS.ra_wall = (s, c) => { raEnsure(); RA.walls.push([s.x, s.y, s.w, s.h, s.a ?? 0.92]); };
function raPaint() {
  if (!room || !room.back) return;
  RA.painted = room.back;
  const bx = room.back.getContext('2d'), sh = tileSheet(room.def.biome);
  const walls = room.def.ra_bg ? RA.walls.concat([[0, 0, room.w, room.h, room.def.ra_bg]]) : RA.walls;   // ra_bg: an indoor room closed off from the sky
  for (const [x0, y0, w, h, A] of walls) for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) {
    if (x < 0 || y < 0 || x >= room.w || y >= room.h || isSolidT(room.grid[y * room.w + x])) continue;
    let d = 9;
    for (let yy = -3; yy <= 3; yy++) for (let xx = -3; xx <= 3; xx++) if (isSolidT(tileAtR(room, x + xx, y + yy))) d = Math.min(d, Math.max(Math.abs(xx), Math.abs(yy)));
    const fa = !room.def.indoor ? 0 : d <= 1 ? 1 : d === 2 ? 0.8 : d === 3 ? 0.5 : 0.28;
    if (fa < A) drawTile(bx, sh, 38 + Math.floor(hash2(x, y) * 4), x * TILE, y * TILE, 1 - (1 - A) / (1 - fa));   // tops the indoor fade up to A
  }
  for (const b of RA.back) {
    const F = raFrame(b.sh, b.s.k, b.s.v); if (!F) continue;
    const f = b.sh.frames[F.i], k = b.s.sc || 1, w = f.w * k, h = f.h * k, x = Math.round(b.pos.x - w / 2), y = Math.round(b.P_.a === 't' ? b.pos.y : b.pos.y - h);
    bx.save(); bx.globalAlpha = b.s.alpha ?? 1;
    if (b.face < 0) { bx.translate(x * 2 + w, 0); bx.scale(-1, 1); }
    bx.drawImage(b.sh.img, f.x, f.y, f.w, f.h, x, y, w, h); bx.restore();
  }
}

// ================================================================== ambushers: statues that stand up, booths, roots, niches, black water
SPAWNS.ra_amb = (s, c) => {
  raEnsure();
  const look = s.look || 'kneel', face = s.face || (P && P.x < c.cx ? -1 : 1);
  let booth = null;
  if (look === 'booth') { booth = { type: 'ra_booth', x: c.cx, y: c.fy, face: 1, open: false, anim: { update() {} } }; booth.draw = () => { const sh = sheet('xra_deco'); if (sh.ok) drawSprite(sh, sh.tag('booth').from + (booth.open ? 1 : 0), booth.x, booth.y, 1, { bottom: true }); }; props.push(booth); }
  if (killed.has(c.key)) { if (booth) booth.open = true; return; }
  const e = makeEnemy(s.type, c.cx, c.fy, c.key); e.face = face;
  const A = e.ra = { look, dormant: true, t: 0, booth, rise: 0 };
  const upd = e.update.bind(e), drw = e.draw.bind(e), hb = e.hurtbox.bind(e);
  if (look !== 'kneel') e.ground = false;
  e.hurtbox = () => A.dormant ? (look === 'kneel' ? rect(e.x - 9, e.y - 26, e.x + 9, e.y) : null) : hb();
  e.update = dt => {
    if (!A.dormant) { A.rise = Math.max(0, A.rise - dt); return upd(dt); }
    A.t += dt; e.vx = 0; e.vy = 0;
    if (!e.alive) { A.dormant = false; return upd(dt); }
    const dx = P.x - e.x, dy = P.y - e.y, adx = Math.abs(dx);
    let wake = e.hp < e.maxHp;
    if (look === 'kneel') wake = wake || (adx < 30 && Math.abs(dy) < 40);
    else if (look === 'booth') wake = wake || (adx < 26 && Math.abs(dy) < 32);
    else if (look === 'water') wake = wake || (adx < 44 && Math.abs(dy) < 34);
    else wake = wake || (adx < 30 && dy > -8 && dy < 220 && lineOfSight(e.x, e.y + 4, P.x, P.y - 12));   // ceiling / niche: drop on you
    if (wake && P.state !== 'dead') raWake(e);
  };
  e.draw = () => {
    if (!A.dormant) {
      drw();
      if (A.rise > 0 && look === 'kneel') { const sh = sheet('xra_deco'); if (sh.ok) drawSprite(sh, sh.first('kneel'), e.x, e.y, A.face0 || face, { bottom: true, alpha: A.rise / 0.45 }); }
      return;
    }
    const sh = sheet('xra_deco');
    if (look === 'kneel') { if (sh.ok) drawSprite(sh, sh.first('kneel'), e.x, e.y, face, { bottom: true }); if (Math.random() < 0.02) particles.push({ x: e.x + rand(-4, 4), y: e.y - 22, vx: 0, vy: -rand(4, 10), life: 1.2, kind: 'ash' }); return; }
    if (look === 'booth') return;
    // roots / niche / water: two small eyes, now and then
    const blink = Math.sin(A.t * 1.7 + e.id) > -0.8, ey = look === 'water' ? e.y - 3 : e.y - 5;
    if (look !== 'water') { g.fillStyle = 'rgba(40,28,18,0.95)'; g.beginPath(); g.ellipse(Math.round(e.x), Math.round(e.y - 6), 8, 6, 0, 0, 6.3); g.fill(); }
    if (blink) drawGlow(() => { g.fillStyle = look === 'water' ? 'rgba(170,220,120,0.85)' : 'rgba(255,170,90,0.9)'; g.fillRect(Math.round(e.x) - 3, Math.round(ey), 1, 1); g.fillRect(Math.round(e.x) + 2, Math.round(ey), 1, 1); });
    if (look === 'water' && Math.random() < 0.03) particles.push({ x: e.x + rand(-6, 6), y: e.y - 2, vx: 0, vy: -rand(3, 8), life: 0.6, kind: 'ra_drop' });
  };
  enemies.push(e); RA.amb.push(e);
};
function raWake(e) {
  const A = e.ra; if (!A.dormant) return;
  A.dormant = false; e.aggro = true; e.face = P.x < e.x ? -1 : 1; e.cool = Math.max(e.cool || 0, 0.45);
  if (A.look === 'kneel') {
    A.rise = 0.45; A.face0 = e.face; raSfx.crack(); shake = Math.max(shake, 2);
    for (let i = 0; i < 16; i++) particles.push({ x: e.x + rand(-8, 8), y: e.y - rand(2, 26), vx: rand(-70, 70), vy: -rand(20, 110), g: 420, life: rand(0.5, 1), kind: i % 3 ? 'rock' : 'dust' });
  } else if (A.look === 'booth') {
    if (A.booth) A.booth.open = true;
    raSfx.curtain(); e.vx = e.face * 140; e.ground = true;
    for (let i = 0; i < 8; i++) particles.push({ x: e.x + rand(-10, 10), y: e.y - rand(4, 30), vx: e.face * rand(20, 80), vy: -rand(0, 30), life: 0.6, kind: 'dust' });
  } else if (A.look === 'water') {
    raSfx.splash(); e.vy = -170;
    for (let i = 0; i < 14; i++) particles.push({ x: e.x + rand(-8, 8), y: e.y - 2, vx: rand(-60, 60), vy: -rand(60, 170), g: 520, life: rand(0.4, 0.8), kind: 'ra_drop' });
  } else {
    raSfx.drop(); e.vy = 40;
    for (let i = 0; i < 12; i++) particles.push({ x: e.x + rand(-8, 8), y: e.y - rand(0, 10), vx: rand(-30, 30), vy: rand(0, 60), g: 420, life: rand(0.5, 1), kind: i % 2 ? 'ra_root' : 'dust' });
  }
}

// ================================================================== chandeliers (K9): a kit crumble dressed as a candle hoop
SPAWNS.ra_chand = (s, c) => {
  raEnsure();
  const o = typeof KIT !== 'undefined' && KIT.byId[s.target]; if (!o || o.kind !== 'crumble') return;
  let top = o.d.y0; while (top > 0 && !isSolidT(tileAt(Math.floor(o.x / TILE), Math.floor((top - 1) / TILE)))) top -= TILE;
  const C = { o, top, sway: 0, sv: 0, fall: null, was: o.st, delay: s.delay || 1 };
  RA.chands.push(C);
  o.draw = () => raDrawChand(C);
};
function raDrawChand(C) {
  const o = C.o, sh = sheet('xra_deco'); if (!sh.ok) return;
  const t = sh.tag('chand'), fr = t.from + Math.floor(time * 7 + o.x) % (t.to - t.from + 1), f = sh.frames[fr];
  const draw = (x, y, rot, a) => {
    const cx = x, cy = y - 15 + f.h / 2;   // the hoop's rim sits on the slab's top edge
    if (rot) { const dx = Math.sin(rot) * (f.h / 2 - 15), dy = 0; drawRotated(sh, fr, cx + dx, cy + dy, rot, a); } else drawSprite(sh, fr, x, y - 15, 1, { pivot: [Math.floor(f.w / 2), 0], alpha: a });
  };
  if (C.fall) { if (C.fall.a > 0) draw(o.x, C.fall.y, C.fall.r, C.fall.a); }
  if (o.st === 'gone') return;
  const a = o.st === 'back' ? o.alpha : 1, x = o.x, y = o.d.y0;
  // the chain up to the vault, drawn with the sway
  g.fillStyle = 'rgba(40,36,46,1)';
  for (let yy = C.top; yy < y - 15; yy += 3) { const k = (yy - C.top) / Math.max(1, y - 15 - C.top); g.fillRect(Math.round(x + Math.sin(C.sway) * k * 6), yy, 1, 2); }
  draw(x, y, C.sway * 0.35, a);
}
function raTickChands(dt) {
  for (const C of RA.chands) {
    const o = C.o;
    if (o.st === 'shake' && C.was === 'idle') { C.sv += 2.4 * (P.x < o.x ? -1 : 1); tone(1320, 0.3, 0.03, 'triangle', 0.9); }
    if (o.st === 'shake') C.sv += Math.sin(time * 16) * dt * 6;
    C.sv += -C.sway * 30 * dt; C.sv *= Math.pow(0.25, dt); C.sway += C.sv * dt;
    if (o.st === 'gone' && C.was !== 'gone') { C.fall = { y: o.d.y0, v: 0, r: C.sway * 0.35, a: 1, hit: false }; tone(880, 0.2, 0.05, 'square', 0.6); }
    if (C.fall) {
      const F = C.fall; F.v = Math.min(F.v + 700 * dt, 520); F.y += F.v * dt; F.r += dt * 1.2;
      if (!F.hit && (F.y > room.ph - 4 || isSolidT(tileAt(Math.floor(o.x / TILE), Math.floor((F.y + 10) / TILE))) || tileAt(Math.floor(o.x / TILE), Math.floor((F.y + 10) / TILE)) === T_SPIKE)) {
        F.hit = true; F.v = 0; if (kitNear(o.x, F.y)) raSfx.crash();
        for (let i = 0; i < 14; i++) particles.push({ x: o.x + rand(-18, 18), y: F.y + 8, vx: rand(-90, 90), vy: -rand(30, 140), g: 460, life: rand(0.4, 0.9), kind: i % 2 ? 'ember' : 'ra_wax' });
      }
      if (F.hit) F.a -= dt * 2.5;
      if (F.a <= 0) C.fall = null;
    }
    if (o.st !== 'gone') addLight(o.x, o.d.y0 - 4, 76, '255,196,120', 0.85 * (o.st === 'back' ? o.alpha : 1), LX_FLICKER);
    C.was = o.st;
  }
}

// ================================================================== knee-deep black water (K6)
SPAWNS.ra_water = (s, c) => { raEnsure(); RA.waters.push({ x0: s.x * TILE, x1: (s.x + (s.w || 1)) * TILE, y: s.y * TILE + 7, y1: (s.y + 1) * TILE }); };
function raWaterAt(x, y) { for (const w of RA.waters) if (x >= w.x0 && x < w.x1 && y > w.y && y <= w.y1 + 1) return w; return null; }
function raDrawWater() {
  for (const w of RA.waters) {
    g.fillStyle = 'rgba(8,10,22,0.8)'; g.fillRect(w.x0, w.y, w.x1 - w.x0, w.y1 - w.y);
    for (let x = w.x0; x < w.x1; x += 2) {
      if (isSolidT(tileAt(Math.floor(x / TILE), Math.floor((w.y + 2) / TILE)))) continue;
      const k = Math.sin(time * 2.2 + x * 0.21) + Math.sin(time * 1.3 - x * 0.07);
      g.fillStyle = k > 1.1 ? 'rgba(190,200,240,0.8)' : 'rgba(90,100,140,0.75)'; g.fillRect(x, Math.round(w.y + k * 0.6), 2, 1);
    }
  }
}
function raTickWater(dt) {
  if (!RA.waters.length) return;
  const w = raWaterAt(P.x, P.y);
  if (w && P.ground && Math.abs(P.vx) > 30 && Math.random() < 0.25) particles.push({ x: P.x + rand(-5, 5), y: w.y, vx: -P.vx * 0.2 + rand(-20, 20), vy: -rand(30, 90), g: 480, life: rand(0.3, 0.6), kind: 'ra_drop' });
  if (w && P.landed) { raSfx.splash(); for (let i = 0; i < 10; i++) particles.push({ x: P.x + rand(-8, 8), y: w.y, vx: rand(-70, 70), vy: -rand(40, 130), g: 480, life: rand(0.3, 0.7), kind: 'ra_drop' }); }
  for (const e of enemies) if (e.alive && !(e.ra && e.ra.dormant) && e.landed && raWaterAt(e.x, e.y)) for (let i = 0; i < 5; i++) particles.push({ x: e.x + rand(-6, 6), y: e.y - 2, vx: rand(-50, 50), vy: -rand(30, 90), g: 480, life: 0.5, kind: 'ra_drop' });
}

// ================================================================== the Perch's sheer drop: a void that sends you back (like spikes), under a bank of mist
SPAWNS.ra_void = (s, c) => { raEnsure(); (RA.voids = RA.voids || []).push(rect(s.x * TILE, s.y * TILE, (s.x + s.w) * TILE, (s.y + s.h) * TILE)); };
SPAWNS.ra_mist = (s, c) => {
  raEnsure();
  const x0 = s.x * TILE, y0 = s.y * TILE, w = s.w * TILE, h = s.h * TILE;
  props.push({ type: 'ra_mist', x: x0, y: y0 + h, face: 1, anim: { update() {} }, draw() {
    for (let i = 0; i < 6; i++) {
      const y = y0 + i * h / 6, a = 0.12 + 0.13 * i;
      g.fillStyle = `rgba(92,70,104,${a})`; g.fillRect(x0, Math.round(y), w, Math.ceil(h / 6) + 1);
    }
    g.fillStyle = 'rgba(190,150,170,0.18)';
    for (let i = 0; i < 9; i++) { const x = ((time * (6 + i) + i * 131) % (w + 160)) - 80 + x0, y = y0 + 8 + (i * 23) % (h - 12); g.fillRect(Math.round(x), Math.round(y), 70 + (i * 17) % 60, 2); }
  } });
};
function raTickVoid() {
  if (!RA.voids || P.state === 'dead') return;
  const hb = playerHurtbox();
  for (const v of RA.voids) if (overlap(hb, v)) { spikeHurt(); return; }
}

// ================================================================== locks + hints
SPAWNS.ra_lock = (s, c) => { raEnsure(); RA.locks.push({ s, x: c.cx, y: c.fy }); };
function raTickLocks(dt) {
  RA.lockT = Math.max(0, RA.lockT - dt);
  for (const L of RA.locks) {
    const free = kitOn(L.s.src); kitForce(L.s.target, free ? null : false);
    const o = KIT.byId[L.s.target];
    if (!free && o && o.d && kitStands(P, o.d) && RA.lockT <= 0) { RA.lockT = 6; toast(L.s.text || 'It will not move.', 3); sfx.deny(); }
  }
}
SPAWNS.ra_hint = (s, c) => { raEnsure(); RA.hints.push({ s, x: c.cx, y: c.fy, n: 0, bad: 0, busy: false, shown: false }); };
function raTickHints() {
  for (const H of RA.hints) {
    const s = H.s;
    if (s.seq) {   // a kit seq: count wrong strikes (its `bad` flash)
      const q = KIT.byId[s.seq]; if (!q || q.active) continue;
      if (q.bad > 0.7 && H.bad <= 0.7) H.n++;
      H.bad = q.bad;
    } else if (s.watch) {   // timed sources feeding a gate: a try = any source flipped on, then all fell off with the gate shut
      if (kitOn(s.watch)) continue;
      const any = s.src.some(id => kitOn(id));
      if (any) H.busy = true; else if (H.busy) { H.busy = false; H.n++; }
    } else if (s.near && !H.shown && Math.abs(P.x - H.x) < s.near && Math.abs(P.y - H.y) < 48) { H.shown = true; if (!SAVE.hints['ra:' + room.id + H.x]) { SAVE.hints['ra:' + room.id + H.x] = 1; toast(s.text, 3.5); } }
    if (H.n >= 3) { H.n = 0; toast(s.text, 5); }
  }
}

// ================================================================== the Bellrope trial: the bell tolls at each third of par
function raTickToll(dt) {
  if (room.id !== 'K12' || typeof SYS === 'undefined') return;
  const T = SYS.trial;
  if (!T || T.room !== 'K12' || T.done) { RA.toll = 0; return; }
  const par = (T.s && T.s.par) || 40, n = Math.min(3, Math.floor(T.t / (par / 3)));
  if (n > RA.toll) {
    RA.toll = n; raSfx.toll(); shake = Math.max(shake, 2.5); RA.tollT = 1;
    toast(['', 'The bell tolls once.', 'The bell tolls twice.', 'The bell tolls a third time.'][n], 1.6);
  }
  RA.tollT = Math.max(0, RA.tollT - dt);
}

// ================================================================== the Watcher's Perch: the Hallow as a painted parallax band
const raParallaxBase = drawParallax;
drawParallax = function () {
  if (!room || room.id !== 'R11') return raParallaxBase();
  const far = sheet('bg_ramparts_far'), pano = sheet('xra_pano');
  g.fillStyle = AREAS.ramparts.tint; g.fillRect(0, 0, W, H);
  const band = (sh, i, fac, vfac, lift) => {
    const f = sh.frames[i], ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
    for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h) + lift, f.w, f.h);
  };
  if (far.ok) band(far, far.tag('loop').from + (Math.floor(time * 6) % (far.tag('loop').to - far.tag('loop').from + 1)), 0.05, 0.02, 0);
  if (pano.ok) { band(pano, pano.first('far'), 0.1, 0.04, 26); band(pano, pano.first('near'), 0.18, 0.06, 40); }
  // long clouds drifting across the dusk
  g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 5; i++) {
    const y = 30 + i * 13 + Math.sin(i * 7) * 6, x = ((time * (3 + i) + i * 97 - cam.x * 0.06) % (W + 200) + W + 200) % (W + 200) - 100;
    g.fillStyle = `rgba(255,150,120,${0.05 + 0.02 * (i % 2)})`; g.fillRect(Math.round(x), Math.round(y), 90 + i * 17, 2); g.fillRect(Math.round(x) + 20, Math.round(y) + 2, 50 + i * 9, 1);
  }
  g.globalCompositeOperation = 'source-over';
};

// ================================================================== the Rose Window (K11)
SPAWNS.ra_rose = (s, c) => {
  raEnsure();
  const x = c.cx + (s.dx || 0), y = s.y * TILE, p = { type: 'ra_rose', x, y, face: 1, glow: true, anim: { update() {} } };
  p.draw = () => {
    const sh = sheet('xra_rose'); if (!sh.ok) return;
    drawSprite(sh, sh.first('lit'), x, y, 1, { pivot: [80, 0] });
    // shafts of coloured light falling to the floor
    g.save(); g.globalCompositeOperation = 'lighter';
    const cols = ['255,120,150', '120,160,255', '255,210,120', '140,230,160'];
    for (let i = 0; i < 4; i++) {
      const k = 0.05 + 0.025 * Math.sin(time * 0.7 + i * 1.7), x0 = x - 56 + i * 30, w = 22;
      g.fillStyle = `rgba(${cols[i]},${k})`; g.beginPath(); g.moveTo(x0, y + 60); g.lineTo(x0 + w, y + 60); g.lineTo(x0 + w + 60, room.ph - 48); g.lineTo(x0 + 40, room.ph - 48); g.closePath(); g.fill();
    }
    g.restore();
    if (Math.random() < 0.2) particles.push({ x: x + rand(-70, 90), y: y + rand(60, 200), vx: rand(2, 6), vy: rand(-3, 3), life: rand(2, 4), kind: 'gold' });
  };
  props.push(p);
  RA.lights.push([x, y + 80, 190, '230,200,255', 1.1, 0], [x - 40, y + 60, 90, '255,140,170', 0.5, 0], [x + 40, y + 60, 90, '140,170,255', 0.5, 0]);
};

// ================================================================== the loop
HOOKS.enter.push(def => { raEnsure(); raPaint(); if (def.id === 'R7' && !SAVE.hints.raward) { SAVE.hints.raward = 1; setTimeout(() => toast('Shield wardens turn light blows aside. Strike behind the shield, break it with heavies, or parry (I) as a blow lands.', 5), 1400); } });
HOOKS.update.push(dt => {
  if (!room || RA.roomObj !== room) return;
  if (room.back !== RA.painted) raPaint();   // a broken wall re-renders the room: paint the decor back in
  for (const [x, y, r, c, k, fl] of RA.lights) addLight(x, y, fl === 'pulse' ? r * (0.92 + 0.08 * Math.sin(time * 1.6)) : r, c, fl === 'pulse' ? k * (0.85 + 0.15 * Math.sin(time * 1.6)) : k, fl === 1 ? LX_FLICKER : undefined);
  if (RA.chands.length) raTickChands(dt);
  raTickWater(dt); raTickVoid(); if (RA.locks.length) raTickLocks(dt); if (RA.hints.length) raTickHints(); raTickToll(dt);
});
HOOKS.render.push(() => { if (RA.roomObj === room && RA.waters.length) raDrawWater(); });

// ================================================================== the trial charm: Chime of Ascent
registerGear({ charms: { c_x3_chime: { name: 'Chime of Ascent', iconSheet: 'xra_icons',
  desc: 'A lamplighter’s hand-bell from the Bellrope tower. Its note lingers under your feet: the second jump carries 15% higher.' } } });
ICON_SHEETS.push('xra_icons');
{
  const raJump = doJump;
  doJump = function (v, dbl) { if (dbl && charmOn('c_x3_chime')) { v *= 1.0724; for (let i = 0; i < 4; i++) particles.push({ x: P.x + rand(-5, 5), y: P.y, vx: rand(-20, 20), vy: rand(10, 30), life: 0.5, kind: 'spark' }); tone(1568, 0.4, 0.04, 'triangle', 1); } return raJump.call(this, v, dbl); };
}

// ================================================================== the Hallow Chronicle: RA's pages
Object.assign(LORE_PAGES, {
  ra_1: { region: 'ramparts', title: 'The Night the Ash Fell', text: 'The watch-log of the Perch. Its last page.\nThird bell. No stars. The sea has gone quiet.\nFourth bell. A pale light rose over the Hallow where the Root stands, and did not set. The ash began at midnight, soft as snow and warm.\nFifth bell. The signal fires will not take; the ash smothers them. We lit them with our cloaks.\nNo one answers from the Crown. We keep the watch.' },
  ra_2: { region: 'ramparts', title: 'A Stablehand’s Tally', text: 'Horses stabled beneath the Long Wall: forty. After the ash: nine.\nThe rest would not eat. They stood in their stalls facing the Root until their legs gave.\nThe captain says we ride out when it thins. It has not thinned.' },
  ra_3: { region: 'ramparts', title: 'Orders to the Undercroft', text: 'By order of the Warden of the Wall: the lift to the First Shrine is to be chained from above, and the winch locked.\nNone come up from the landing. None.\nWhat climbs up out of the ash is not a pilgrim, whatever it says to you.' },
  ra_4: { region: 'ramparts', title: 'The Winchman’s Mark', text: 'Two drums, one gate. Each holds the portcullis only a short while alone.\nStrike the low winch and run the stair. Strike the high one while the first still holds, and the gate will rise for you.' },
  ra_5: { region: 'ramparts', title: 'The Sentry’s Letter', text: 'Mother,\nThey walled me in to keep the stores until relief came. The wall is thin by the stables; I hear them walking on the other side.\nI have eaten the last of the bread. The stone keeps warm. I am not afraid. The Root sings through the mortar at night, and it is almost kind.' },
  ra_6: { region: 'catacombs', title: 'The Ossuary Keeper’s Rule', text: 'Every bone in the Ossuary had a name once. We cut the names into the shelves, and the roots have eaten them since.\nWe did not bury the dead of the Hallow. We lent them to the Root, and the Root kept them.\nNow it gives them back, one at a time, walking.' },
  ra_7: { region: 'catacombs', title: 'The Lantern Rite', text: 'Here lie the four wardens of the crypt, each beneath his numeral.\nKindle their lanterns as they were laid down, the first before the second, and the vault in their keeping will open.\nKindle them out of order and they will not know you.' },
  ra_8: { region: 'catacombs', title: 'The Gravedigger’s Confession', text: 'I sold what I dug up. Rings, mostly. A sword, once. The rest I hid behind the false tomb, where the wardens never looked.\nThen the dead began to sit up, and I found I could not sell to them.\nWhoever reads this: take it. It was never mine.' },
  ra_9: { region: 'cathedral', title: 'The Hymn of the Four Hours', text: 'Sung at the four hours, at the great organ, stop by stop.\nAt the first hour, the SUN, that rises over the Root.\nAt the second, the BELL, that calls the faithful in.\nAt the third, the MOON, by whose light we kept the vigil.\nAt the last, the ROOT, to which we give our final breath.\nThe carvings above the stops show the same four.' },
  ra_10: { region: 'cathedral', title: 'The Church of the Pale Root', text: 'The first church was a clearing where the Root broke the ground, and the first priests were the ones who would not leave it.\nThey raised the nave around the trunk and set the great window toward the dawn, so that the light would pass through the Root before it reached them.\nWhen the Root fell, the water rose through the floor. The light kept coming through the glass as if nothing had happened.' },
  ra_11: { region: 'cathedral', title: 'The Sacristan’s Inventory', text: 'One chalice, gilt. One censer, its chain broken. Vestments for the four hours; the Moon set moth-eaten.\nOne relic of the Root, a splinter, in a box of glass. Given to the Omen for safekeeping.\nThe Omen did not return it. The Omen returns nothing.' },
  ra_12: { region: 'cathedral', title: 'The Lamplighters', text: 'The clerestory walk belonged to the lamplighters, who lit the high windows from within so the nave was never dark.\nThere were forty of them. They carried their lamps up the ropes of the bell tower each dusk, and some of them are up there still.' },
});

// test harness hook (tools/shots/ra): render a whole room, camera panned tile by tile (no HUD), for contact sheets
try { window.__ra = {
  get room() { return room; }, RA,
  sheet() {
    const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; const X = c.getContext('2d'); shake = 0;
    const span = (full, v, m) => { if (full <= v) return [[(full - v) / 2, 0, full]]; const out = []; for (let a = 0; ; a += v - 2 * m) { const cpos = Math.min(a, full - v); out.push([cpos, cpos === 0 ? 0 : cpos + m, cpos + v >= full ? full : cpos + v - m]); if (cpos >= full - v) break; } return out; };
    for (const [cy, y0, y1] of span(room.ph, H, 40)) for (const [cx, x0, x1] of span(room.pw, W, 60)) {
      cam.x = cx; cam.y = cy; renderWorld(); presentWorld();
      const sx = ox + (Math.max(x0, 0) - cx) * scale, sy = oy + (Math.max(y0, 0) - cy) * scale;
      X.drawImage(view, sx, sy, (x1 - Math.max(x0, 0)) * scale, (y1 - Math.max(y0, 0)) * scale, Math.max(x0, 0), Math.max(y0, 0), x1 - Math.max(x0, 0), y1 - Math.max(y0, 0));
    }
    return c.toDataURL('image/png');
  },
}; } catch (e) {}
