// ------------------------------------------------------------------ THE SUNSCORCHED DUNES (agent DU): the buried desert of the sun-kings
// Rooms DU1-DU8 (tools/regions/74_dunes.py). Quicksand '-' (tile 55), sand-surfing slopes '/' (tile 56 + room.def.du_slopes),
// sand-falls, thermals over the glide gate, sandstorms (DU3), sun-altar beams (DU5), the sun-bronze hatch shortcut (DU1 <-> DU7),
// mummified sun-priests / scarab swarms / jackal-headed guardians / sand-soldiers, the Scarab Knight and the Veiled Pharaoh.
// Art: tiles_dunes*, bg_dunes_*, du_*, scarab*, pharaoh*, fx_du_* (art/gen_dunes*.py).
Object.assign(AREAS, { dunes: { name: 'The Sunscorched Dunes', ambient: 0.26, amb: 'dust', tint: '#2a1a0c', map: '#b8903c' } });
Object.assign(SCALES, { dunes: [0, 1, 4, 5, 8] });           // phrygian-dominant / hijaz colour
Object.assign(ROOTS, { dunes: 46.25 });
Object.assign(PCOL, { sand: '222,184,120', sandd: '160,120,70', sun: '255,236,170' });
const DU_T_QS = 55, DU_T_SLOPE = 56;
const DU_AMB = { DU1: 0.3, DU2: 0.24, DU3: 0.22, DU4: 0.42, DU5: 0.56, DU6: 0.46, DU7: 0.55, DU8: 0.5 };
const DU = { safe: null, safeT: 0, slopes: [], falls: [], storm: null, altars: [], hint: {}, qsT: 0, underT: 0, zones: [], shots: [], haz: [], marks: [] };
const duRoom = () => room && room.def.biome === 'dunes';
// per-room lists are reset lazily: SPAWNS run before HOOKS.enter, so whichever touches a new room first resets them
function duFresh() {
  if (DU.roomRef === room) return;
  DU.roomRef = room; DU.falls = []; DU.altars = []; DU.storm = null; DU.colossus = null; DU.zones = []; DU.shots = []; DU.haz = []; DU.marks = [];
}
const duDmg = d => BOSS_DMG * d * NGP.dmg;
const duFx = (...n) => fxOr(...n.map(k => k && (k.startsWith('fx_') ? k.slice(3) : k)));

// ================================================================== tiles
// quicksand: the cached layer only gets the dark sand body; the moving surface is drawn live from the render hook
registerTile('-', DU_T_QS, { draw(ctx, sh, px, py, x, y, R) {
  const top = y === 0 || R.grid[(y - 1) * R.w + x] !== DU_T_QS;
  ctx.fillStyle = top ? '#6a4a22' : '#4e3418'; ctx.fillRect(px, py, 16, 16);
  ctx.fillStyle = '#3a2610'; for (let i = 0; i < 6; i++) ctx.fillRect(px + ((x * 7 + i * 5 + y * 3) % 15), py + ((i * 7 + x) % 14) + 1, 1, 1);
} });
// dune slope wedge: sand below the slope line (the line itself is room.def.du_slopes); the top 3px get the lit lip
function duSlopeLines(R) {
  if (!R.duSl) R.duSl = (R.def.du_slopes || []).map(([x0, y0, x1, y1]) => ({ x0: x0 * TILE, y0: y0 * TILE, x1: x1 * TILE, y1: y1 * TILE,
    k: (y1 - y0) / (x1 - x0), dir: y1 > y0 ? 1 : -1 }));
  return R.duSl;
}
function duSlopeY(R, x) { for (const s of duSlopeLines(R)) if (x >= s.x0 && x <= s.x1) return { s, y: s.y0 + (x - s.x0) * s.k }; return null; }
registerTile('/', DU_T_SLOPE, { draw(ctx, sh, px, py, x, y, R) {
  const fx = sheet('tiles_dunes_fx'), sl = fx.ok && fx.has('slope') ? fx.frames[fx.first('slope')] : null, sd = fx.ok && fx.has('sand') ? fx.frames[fx.first('sand')] : null;
  for (let i = 0; i < 16; i++) {
    const hit = duSlopeY(R, px + i + 0.5); if (!hit) continue;
    const ly = Math.round(hit.y), j0 = Math.max(0, ly - py), cx = (px + i) % 16;
    if (j0 >= 16) continue;
    const d0 = py + j0 - ly, lipN = Math.max(0, Math.min(16 - j0, 16 - d0));   // rows of this column still inside the lip texture
    if (sl && sd) {
      if (lipN > 0) ctx.drawImage(fx.img, sl.x + cx, sl.y + d0, 1, lipN, px + i, py + j0, 1, lipN);
      for (let j = j0 + lipN; j < 16; j++) ctx.drawImage(fx.img, sd.x + cx, sd.y + ((py + j) % 16), 1, 1, px + i, py + j, 1, 1);
    } else for (let j = j0; j < 16; j++) { const dep = py + j - ly; ctx.fillStyle = dep < 1 ? '#f0d08a' : dep < 3 ? '#c89a52' : dep < 8 ? '#9a6e36' : '#6a4a26'; ctx.fillRect(px + i, py + j, 1, 1); }
  }
} });
// solid cells under a slope are the dune's body (deep sand); cells beside a slope need their exposed-edge mask recomputed
function duRepaintUnderSlopes(R) {
  if (!R.def.du_slopes) return;
  const sh = tileSheet(R.def.biome), ctx = R.front.getContext('2d'), fx = sheet('tiles_dunes_fx');
  const sd = fx.ok && fx.has('sand') ? fx.frames[fx.first('sand')] : null;
  const solid = (x, y) => { const t = tileAtR(R, x, y); return isSolidT(t) || t === DU_T_SLOPE; };
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    if (R.grid[y * R.w + x] !== T_SOLID) continue;
    let under = 0; for (let yy = y - 1; yy >= 0; yy--) { const t = R.grid[yy * R.w + x]; if (t === DU_T_SLOPE) { under = y - yy; break; } if (t !== T_SOLID) break; }
    if (under && sd) {
      ctx.clearRect(x * TILE, y * TILE, TILE, TILE);
      ctx.drawImage(fx.img, sd.x, sd.y, 16, 16, x * TILE, y * TILE, 16, 16);
      ctx.fillStyle = `rgba(26,14,6,${Math.min(0.55, 0.1 + under * 0.12)})`; ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
      continue;
    }
    let near = false;
    for (const [dx, dy] of [[0, -1], [1, 0], [-1, 0], [0, 1]]) if (tileAtR(R, x + dx, y + dy) === DU_T_SLOPE) near = true;
    if (!near) continue;
    const m = (solid(x, y - 1) ? 0 : 1) | (solid(x + 1, y) ? 0 : 2) | (solid(x, y + 1) ? 0 : 4) | (solid(x - 1, y) ? 0 : 8);
    ctx.clearRect(x * TILE, y * TILE, TILE, TILE);
    drawTile(ctx, sh, m + (hash2(x + 7, y * 3) < 0.28 ? 16 : 0), x * TILE, y * TILE);
  }
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) if (R.grid[y * R.w + x] === DU_T_SLOPE) {   // shade the wedges' depth too
    TILE_DRAW[DU_T_SLOPE](ctx, sh, x * TILE, y * TILE, x, y, R);
  }
}

// the open dune rooms: the far walls give way to the buried desert (only the courses right by the rock stay)
const DU_OPEN = new Set(['DU1', 'DU2', 'DU3', 'DU4']);
function duOpenBack(R) {
  const def = R.def, sh = tileSheet(def.biome), ctx = R.back.getContext('2d');
  ctx.clearRect(0, 0, R.pw, R.ph);
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    const t = R.grid[y * R.w + x];
    if (!isSolidT(t) && t !== DU_T_SLOPE) {
      let d = 9;
      for (let yy = -2; yy <= 2; yy++) for (let xx = -2; xx <= 2; xx++) { const q = tileAtR(R, x + xx, y + yy); if (isSolidT(q)) d = Math.min(d, Math.max(Math.abs(xx), Math.abs(yy))); }
      if (d <= 2) drawTile(ctx, sh, 38 + Math.floor(hash2(x, y) * 4), x * TILE, y * TILE, d <= 1 ? 0.85 : 0.35);
    }
    const deco = { x: 42, r: 43, k: 44, b: 45 }[def.map[y][x]];
    if (deco !== undefined) drawTile(ctx, sh, deco, x * TILE, y * TILE);
  }
}

// ================================================================== helpers
function duQsSurface(tx, ty) { let y = ty; while (y > 0 && tileAt(tx, y - 1) === DU_T_QS) y--; return y * TILE; }
function duInQs(b) {   // feet inside quicksand? returns depth below the surface (px) or -1
  const tx = Math.floor(b.x / TILE), ty = Math.floor((b.y - 1) / TILE);
  if (tileAt(tx, ty) !== DU_T_QS) return -1;
  return b.y - duQsSurface(tx, ty);
}
function duFloorBelow(x, y, max = 12 * TILE) {   // first solid/platform surface under (x, y)
  for (let yy = Math.floor(y / TILE); yy < Math.floor((y + max) / TILE); yy++) {
    const t = tileAt(Math.floor(x / TILE), yy);
    if (isSolidT(t) || t === T_PLAT) return yy * TILE;
    if (t === DU_T_QS) return duQsSurface(Math.floor(x / TILE), yy);
    if (t === DU_T_SLOPE) { const h = duSlopeY(room, x); if (h) return h.y; }
  }
  return null;
}
function duSand(x, y, n = 8, spread = 8, up = 70) {
  for (let i = 0; i < n; i++) particles.push({ x: x + rand(-spread, spread), y: y - rand(0, 4), vx: rand(-40, 40), vy: -rand(20, up), g: 300, life: rand(0.4, 0.9), kind: Math.random() < 0.5 ? 'sand' : 'sandd' });
}

// ================================================================== the swallow (abyss quicksand), safe ground
function duSwallow(frac = 0.2) {
  if (P.state === 'dead') return;
  const dmg = Math.round(D.maxHp * frac * NGP.dmg);
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; shake = 5; sfx.hurt(); popup(P.x, P.y - 30, dmg, '#e0b060');
  duSand(P.x, P.y - 4, 18, 10, 120);
  if (P.hp <= 0) return killPlayer(0);
  P.inv = 1.0; P.vx = 0; P.vy = 0;
  const to = DU.safe || P.safe;
  fadeTo(() => { P.x = to.x; P.y = to.y; P.vx = P.vy = 0; setP('idle', 'idle', true); updateCamera(0, true); });
  DU.underT = 0;
}
function duSafeHere() {
  if (!P.ground || P.state === 'hurt' || P.duSlope || duInQs(P) >= 0) return false;
  for (const dx of [-14, 0, 14]) { const tx = Math.floor((P.x + dx) / TILE), ty = Math.floor((P.y + 1) / TILE); const t = tileAt(tx, ty); if (t === DU_T_QS || t === DU_T_SLOPE || !(isSolidT(t) || t === T_PLAT)) return false; }
  for (const z of DU.zones) if (Math.abs(P.x - z.x) < z.w / 2 + 16) return false;
  return true;
}

// ================================================================== player: quicksand, slopes, sand-falls, storm push
function duQuicksandPlayer(dt) {
  if (P.state === 'dead' || P.state === 'hook' || P.state === 'rest') { DU.underT = 0; return; }
  const dep = duInQs(P);
  P.duSand = dep >= 0 ? dep : -1;
  if (dep < 0) { DU.underT = Math.max(0, DU.underT - dt * 2); DU.qsT = 0; return; }
  // sinking: the deeper you are the slower you move; a jump always gets you out (the sand still lets you kick free)
  if (P.vy > 0) P.vy = Math.min(P.vy, 14 + dep * 0.45);
  P.coyote = Math.max(P.coyote, 0.1);
  if (P.state === 'air' && P.vy >= 0) setP(Math.abs(P.vx) > 20 ? 'run' : 'idle', Math.abs(P.vx) > 20 ? 'run' : 'idle', true);
  P.pushVx = (P.pushVx || 0) - P.vx * Math.min(0.72, 0.38 + dep / 70);
  P.airDash = true;
  if (Math.random() < 0.35) particles.push({ x: P.x + rand(-7, 7), y: P.y - dep + rand(-1, 1), vx: rand(-10, 10), vy: -rand(5, 25), life: 0.4, kind: 'sand' });
  if (!DU.hint.qs) { DU.hint.qs = 1; if (!SAVE.hints.du_qs) { SAVE.hints.du_qs = 1; toast('Quicksand — jump to kick free before it closes over you', 3.5); } }
  const abyss = room.def.du_abyss;
  if (dep >= 23) {   // head under
    DU.underT += dt;
    if (abyss && DU.underT > 0.35) return duSwallow(0.2);
    DU.qsT -= dt;
    if (DU.qsT <= 0 && !abyss && P.inv <= 0 && !SETTINGS.god) {   // suffocating: steady damage, never a stagger (you can always kick free)
      DU.qsT = 0.6; const d = Math.round(Math.max(4, D.maxHp * 0.07) * NGP.dmg);
      P.hp = Math.max(0, P.hp - d); P.flash = 0.6; sfx.hurt(); popup(P.x, P.y - 30, d, '#e0b060');
      if (P.hp <= 0) killPlayer(0);
    }
  } else DU.underT = Math.max(0, DU.underT - dt);
  if (abyss && dep > 38) duSwallow(0.2);
}
function duSlopePlayer(dt) {
  const was = P.duSlope; P.duSlope = 0;
  if (!DU.slopes.length || ['dead', 'hook', 'rest', 'wall'].includes(P.state)) return;
  const h = duSlopeY(room, P.x); if (!h) return;
  const surf = h.y;
  if (P.vy < -1 || P.y < surf - (was ? 7 : 0.5) || P.y > surf + 30) return;
  const landing = !was && !P.ground;
  P.y = surf; P.vy = 0; P.ground = true; P.duSlope = h.s.dir; P.coyote = 0.12; P.airDash = true; if (SAVE.items.wings) P.airJumps = 1;
  if (landing && ['air', 'glide', 'slam'].includes(P.state)) { setP('land', pHas('land') ? 'land' : 'idle', false); spawnFx('dust', P.x, P.y, P.face); sfx.land(); }
  // sand-surfing: the dune carries you downhill; walking uphill is a slog
  if (['idle', 'run', 'land', 'roll'].includes(P.state)) {
    const ax = inputX(), d = h.s.dir;
    P.pushVx = (P.pushVx || 0) + d * (ax === d ? 118 : ax === 0 ? 92 : 36) * (P.state === 'roll' ? 0.6 : 1);
    if (Math.random() < 0.7) particles.push({ x: P.x - d * 6 + rand(-3, 3), y: P.y - 1, vx: -d * rand(20, 70), vy: -rand(15, 55), g: 260, life: 0.45, kind: Math.random() < 0.6 ? 'sand' : 'sandd' });
    if (!DU.hint.surf && !SAVE.hints.du_surf) { DU.hint.surf = 1; SAVE.hints.du_surf = 1; toast('The dune slides beneath you — ride it down', 3); }
  }
}
function duFallsPlayer(dt) {
  for (const f of DU.falls) {
    if (P.x + 4 < f.x0 || P.x - 4 > f.x1 || P.y - 24 > f.y1 || P.y < f.y0) continue;
    if (P.ground || P.state === 'hook') continue;
    if (P.state === 'glide') P.vy = approach(P.vy, 150, 1400 * dt);
    else if (P.vy > -60) P.vy = Math.min(P.vy + 500 * dt, FALL_MAX);
    if (Math.random() < 0.5) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 24), vx: rand(-20, 20), vy: rand(40, 90), life: 0.35, kind: 'sand' });
  }
}

// ================================================================== enemies in quicksand: the sand takes them
function duEnemySand(dt) {
  for (const e of enemies) {
    if (!e.alive || e.type === 'du_scarab' || (e.cfg && e.cfg.flying)) continue;
    const dep = duInQs(e); if (dep < 0) continue;
    e.vy = Math.min(e.vy, 16); e.vx *= Math.pow(0.05, dt); e.y += 10 * dt;
    e.duQsCd = (e.duQsCd || 0) - dt;
    if (e.duQsCd <= 0) { e.duQsCd = 0.5; e.hit({ dmg: e.maxHp * 0.22 + 6, poise: 0, dir: -e.face, kind: 'env', x: e.x, y: e.y - 8, quiet: true }); duSand(e.x, e.y - dep, 6); }
  }
}

// ================================================================== room features: sand-falls, hatch, steles, altars, storm, colossus
SPAWNS.du_sandfall = (s, c) => {
  duFresh();
  const w = s.thin ? 6 : 12, x = s.x * TILE + 8, f = { x, x0: x - w / 2, x1: x + w / 2, y0: s.y * TILE, y1: (s.y1 + 1) * TILE, w, seed: s.x * 13 + s.y };
  const bot = duFloorBelow(x, f.y1 - 2, 30 * TILE); f.y1 = bot ?? f.y1;
  DU.falls.push(f);
};
function duDrawFalls() {
  for (const f of DU.falls) {
    if (f.x1 < cam.x - 8 || f.x0 > cam.x + W + 8) continue;
    const y0 = Math.max(f.y0, cam.y - 4), y1 = Math.min(f.y1, cam.y + H + 4), sc = time * 150;
    for (let x = Math.floor(f.x0); x < f.x1; x++) {
      const k = (x - f.x0) / f.w, edge = k < 0.18 || k > 0.82;
      g.fillStyle = edge ? 'rgba(150,108,56,0.55)' : 'rgba(206,164,98,0.78)'; g.fillRect(x, y0, 1, y1 - y0);
      for (let y = y0 - ((sc + x * 37 + f.seed * 11) % 9); y < y1; y += 9) {
        g.fillStyle = (x + Math.floor(y / 9)) % 3 ? 'rgba(246,214,150,0.9)' : 'rgba(120,84,40,0.8)';
        g.fillRect(x, Math.round(y), 1, 3);
      }
    }
    if (f.y1 > cam.y && f.y1 < cam.y + H + 20) {   // splash where it lands
      for (let i = 0; i < 5; i++) { const px = f.x0 - 4 + ((time * 40 + i * 7) % (f.w + 8)), py = f.y1 - 2 - Math.abs(Math.sin(time * 9 + i)) * 4; g.fillStyle = 'rgba(232,196,128,0.85)'; g.fillRect(Math.round(px), Math.round(py), 2, 2); }
      if (Math.random() < 0.3) particles.push({ x: f.x0 + rand(0, f.w), y: f.y1 - 1, vx: rand(-40, 40), vy: -rand(20, 60), g: 300, life: 0.5, kind: 'sand' });
    }
    addLight((f.x0 + f.x1) / 2, Math.max(f.y0, cam.y) + 30, 40, '255,220,150', 0.25);
  }
}
// ---- the sun-bronze hatch (DU1 ledge <-> DU7 ceiling), opened by DU7's lever
SPAWNS.du_hatch = (s, c) => {
  const top = s.side === 'top', x0 = s.x * TILE, x1 = x0 + 2 * TILE, y0 = top ? s.y * TILE : 0, y1 = top ? y0 + TILE : TILE;
  const open = () => !!SAVE.flags['lever:DU7'];
  const hp = { type: 'du_hatch', x: x0 + TILE, y: top ? y0 : y1, face: 1, top, anim: { update() {} }, k: open() ? 1 : 0,
    update(dt) { this.k = approach(this.k, open() ? 1 : 0, dt * 1.6); if (open() && this.k < 1 && Math.random() < 0.4) particles.push({ x: rand(x0, x1), y: this.y, vx: rand(-20, 20), vy: rand(10, 60), g: 300, life: 0.6, kind: 'sand' });
      if (this.top && open() && Math.abs(P.x - (x0 + x1) / 2) < 16 && Math.abs(P.y - y0) < 3 && P.ground && !DU.hint.drop) { DU.hint.drop = 1; toast('Hold ↓ and press Space to drop through', 3); } },
    draw() { duDrawHatch(this, x0, x1); } };
  props.push(hp);
  room.dyn.push({ x0, x1, y0, y1, on: () => !open() });
};
function duDrawHatch(h, x0, x1) {
  const sh = sheet('du_props'), y = h.top ? h.y : h.y - TILE;
  if (h.k >= 0.99) {
    if (sh.ok && sh.has('hatch_open')) drawSprite(sh, sh.first('hatch_open'), x0 - 4, y, 1, { pivot: [0, 0] });
    else { g.fillStyle = '#6a4a22'; g.fillRect(x0 - 3, y, 3, 26); }
    if (h.top) duDropArrow((x0 + x1) / 2, y - 12);
    return;
  }
  if (sh.ok && sh.has('hatch')) { drawSprite(sh, sh.first('hatch'), x0, y, 1, { pivot: [0, 0], alpha: 1 - h.k * 0.7 }); return; }
  g.fillStyle = '#3a2814'; g.fillRect(x0, y, x1 - x0, 6);
  g.fillStyle = '#c89a3a'; for (let x = x0 + 2; x < x1; x += 5) g.fillRect(x, y, 2, 6);
}
function duDropArrow(x, y) {   // the ↓+Space marker over thin floors that are real exits
  const a = 0.45 + 0.35 * Math.sin(time * 4), X = Math.round(x), Y = Math.round(y + Math.sin(time * 4) * 1.5);
  g.save(); g.globalAlpha = a; g.fillStyle = '#ffe2a0';
  g.fillRect(X - 1, Y - 4, 2, 5); g.fillRect(X - 3, Y + 1, 6, 1); g.fillRect(X - 2, Y + 2, 4, 1); g.fillRect(X - 1, Y + 3, 2, 1);
  g.restore(); addLight(x, y, 18, '255,220,150', 0.5);
}
SPAWNS.du_dropmark = (s, c) => {
  props.push({ type: 'du_dropmark', x: c.cx, y: c.fy, face: 1, anim: { update() {} },
    update() { if (Math.abs(P.x - this.x) < 24 && Math.abs(P.y - this.y - TILE) < 4 && P.ground && !DU.hint.drop2) { DU.hint.drop2 = 1; toast('Hold ↓ and press Space to drop into the Sanctum', 3); } },
    draw() { duDropArrow(this.x, this.y - 6); } });
};
// ---- steles: hieroglyph tablets (lore)
const DU_LORE = {
  du_gate: ['A sun-disc cut into the rock. Beneath it: a line of little figures walking into the light, and not one walking back.'],
  du_shrine: ['The sun-kings raised their dead with the dawn and buried their living with the dusk.', 'Their priests were paid in shade.'],
  du_halls: ['“He who is veiled keeps the last noon. He counts the grains of the desert, and they are all his.”'],
  du_pharaoh: ['The last sun-king would not be buried. He had his own death sealed in a jar and set it on the altar, and ruled on.',
    'When the Pale Root fell, its shadow reached even here. He veiled his face so that he would not have to see the dusk.'],
  du_ante: ['Beyond this door the sand remembers every step. Kneel, or be knelt.'],
};
SPAWNS.du_stele = (s, c) => {
  const sh = sheet('du_stele'), lines = DU_LORE[s.lore] || ['…'];
  props.push({ type: 'du_stele', x: c.cx, y: c.fy, face: 1, sh, anim: sh.ok ? new Anim(sh, Object.keys(sh.tags)[0], true) : { update() {}, frame: 0 },
    prompt() { return 'Read'; },
    interact() { startDialogue(lines.map(t => ({ t, lore: true })), null); },
    update() { addLight(this.x, this.y - 14, 26, '255,210,130', 0.45 + 0.1 * Math.sin(time * 2 + this.x)); },
    draw() { if (sh.ok) drawSprite(sh, this.anim.frame, this.x, this.y, 1, { bottom: true }); else { g.fillStyle = '#8a6a3a'; g.fillRect(Math.round(this.x) - 6, Math.round(this.y) - 22, 12, 22); } } });
};
// ---- sun-altar beams: a sun-disc mirror in the ceiling focuses the light on a timer (DU5)
const DU_ALTAR = { idle: 1.5, charge: 0.8, fire: 0.9, cool: 0.3 };
SPAWNS.du_altar = (s, c) => {
  duFresh();
  const x = s.x * TILE + 8, y = (s.y + 1) * TILE - 2, bot = duFloorBelow(x, y + 4, 20 * TILE) ?? room.ph;
  const a = { x, y, bot, ph: s.ph || 0, t: 0, id: 0, st: 'idle' };
  DU.altars.push(a);
  const sh = sheet('du_altar');
  props.push({ type: 'du_altar', x, y, face: 1, sh, anim: { update() {} }, a,
    draw() { const glow = a.st === 'charge' ? 1 : a.st === 'fire' ? 2 : 0; if (sh.ok) drawSprite(sh, sh.first(glow ? 'glow' : 'idle') + (glow ? Math.floor(time * 12) % Math.max(1, sh.tag('glow').to - sh.tag('glow').from + 1) : 0), x, y - 2, 1, { pivot: [Math.floor(sh.fw / 2), 0] });
      else { g.fillStyle = glow ? '#ffe090' : '#b08a3a'; g.beginPath(); g.arc(x, y, 7, 0, 6.3); g.fill(); } } });
};
function duAltarCycle() { return DU_ALTAR.idle + DU_ALTAR.charge + DU_ALTAR.fire + DU_ALTAR.cool; }
function duUpdateAltars(dt) {
  const T = duAltarCycle();
  for (const a of DU.altars) {
    const t = ((time + a.ph) % T + T) % T, prev = a.st;
    a.st = t < DU_ALTAR.idle ? 'idle' : t < DU_ALTAR.idle + DU_ALTAR.charge ? 'charge' : t < DU_ALTAR.idle + DU_ALTAR.charge + DU_ALTAR.fire ? 'fire' : 'cool';
    if (a.st === 'charge' && prev !== 'charge' && Math.abs(P.x - a.x) < W) sfx.glint();
    if (a.st === 'fire' && prev !== 'fire') { a.id = ++hazardId; if (Math.abs(P.x - a.x) < W) { sfx.pillar(); shake = Math.max(shake, 1.5); } }
    if (a.st === 'charge') addLight(a.x, a.y + 4, 30 + (t - DU_ALTAR.idle) * 40, '255,230,160', 0.9);
    if (a.st === 'fire') {
      addLight(a.x, a.bot - 10, 70, '255,236,170', 1); addLight(a.x, (a.y + a.bot) / 2, 60, '255,236,170', 0.8);
      const r = rect(a.x - 8, a.y, a.x + 8, a.bot);
      if (overlap(r, playerHurtbox())) hurtPlayer(30 * NGP.dmg, P.x < a.x ? -1 : 1, a.id, { src: a, sun: true });
      for (const e of enemies) if (e.alive && e.hurtbox && e.hurtbox() && overlap(r, e.hurtbox()) && e.duBeam !== a.id) { e.duBeam = a.id; e.hit({ dmg: 60, poise: 30, dir: e.x < a.x ? -1 : 1, kind: 'env', x: e.x, y: e.y - 12 }); }
      if (Math.random() < 0.6) duSand(a.x, a.bot, 2, 6, 60);
    }
  }
}
function duDrawBeam(x, y0, y1, k = 1, w = 8, warn = false) {   // a vertical shaft of focused sunlight
  const Y0 = Math.round(y0), Y1 = Math.round(y1), X = Math.round(x);
  if (warn) {
    g.save(); g.globalAlpha = (0.35 + 0.35 * Math.sin(time * 40)) * k;
    g.fillStyle = '#ffe9b0'; g.fillRect(X, Y0, 1, Y1 - Y0);
    g.fillStyle = 'rgba(255,200,110,0.35)'; g.fillRect(X - 2, Y0, 5, Y1 - Y0);
    g.restore(); return;
  }
  const fl = 1 + Math.sin(time * 50) * 0.12;
  g.save(); g.globalCompositeOperation = 'lighter';
  g.fillStyle = `rgba(255,150,40,${0.25 * k})`; g.fillRect(X - Math.round(w * 1.4 * fl), Y0, Math.round(w * 2.8 * fl), Y1 - Y0);
  g.fillStyle = `rgba(255,200,90,${0.55 * k})`; g.fillRect(X - Math.round(w * fl), Y0, Math.round(w * 2 * fl), Y1 - Y0);
  g.fillStyle = `rgba(255,244,210,${0.9 * k})`; g.fillRect(X - Math.round(w * 0.45), Y0, Math.round(w * 0.9), Y1 - Y0);
  g.restore();
  g.fillStyle = `rgba(255,255,240,${k})`; g.fillRect(X - 1, Y0, 2, Y1 - Y0);
  for (let i = 0; i < 3; i++) { g.fillStyle = 'rgba(255,240,190,0.9)'; g.fillRect(X - w - 3 + ((time * 90 + i * 11) % (2 * w + 6)), Y1 - 2 - (i % 2) * 2, 2, 2); }
}
// ---- sandstorms (DU3; the Pharaoh's second phase keeps one raging)
SPAWNS.du_storm = (s, c) => { duFresh(); DU.storm = { t: 3, st: 'calm', dir: s.dir || 1, k: 0, n: 0 }; };
function duUpdateStorm(dt) {
  const S = DU.storm; if (!S) return;
  if (S.boss) {   // the boss storm: always up, gusts swing back and forth
    S.k = approach(S.k, S.on ? 1 : 0, dt * 0.7); S.t += dt;
    if (S.t > 4.5) { S.t = 0; S.dir *= -1; }
  } else {
    S.t -= dt;
    if (S.t <= 0) {
      if (S.st === 'calm') { S.st = 'warn'; S.t = 1.8; if (Math.abs(1) && !SAVE.hints.du_storm) { SAVE.hints.du_storm = 1; toast('The wind rises. Brace yourself — or use it.', 3.2); } sfx.howl(); }
      else if (S.st === 'warn') { S.st = 'storm'; S.t = 6; }
      else if (S.st === 'storm') { S.st = 'fade'; S.t = 1.6; }
      else { S.st = 'calm'; S.t = rand(8, 11); S.dir *= -1; S.n++; }
    }
    const want = S.st === 'storm' ? 1 : S.st === 'warn' ? 0.25 : 0;
    S.k = approach(S.k, want, dt * (S.st === 'storm' ? 0.9 : 0.6));
  }
  const k = S.k; if (k <= 0.01) return;
  if (P.state !== 'dead' && P.state !== 'hook' && P.state !== 'rest') P.pushVx = (P.pushVx || 0) + S.dir * (P.ground ? 52 : 72) * k * (S.boss ? 0.7 : 1);
  for (let i = 0; i < Math.round(9 * k); i++) particles.push({ x: S.dir > 0 ? cam.x - 10 : cam.x + W + 10, y: cam.y + rand(0, H), vx: S.dir * rand(180, 320), vy: rand(-10, 30), life: rand(1.2, 2.2), kind: Math.random() < 0.6 ? 'sand' : 'sandd' });
}
function duDrawStormOverlay() {
  const S = DU.storm; if (!S || S.k <= 0.01) return;
  const k = S.k;
  g.fillStyle = S.boss ? `rgba(46,28,12,${0.42 * k})` : `rgba(150,104,52,${0.3 * k})`; g.fillRect(0, 0, W, H);
  g.save(); g.globalAlpha = 0.5 * k;
  for (let i = 0; i < 26; i++) {
    const y = (i * 37 + Math.floor(time * 12) * 5) % H, len = 20 + (i * 13) % 50, x = ((i * 97 + time * 400 * S.dir) % (W + 80) + W + 80) % (W + 80) - 40;
    g.fillStyle = i % 3 ? 'rgba(230,190,120,0.6)' : 'rgba(120,80,40,0.6)'; g.fillRect(Math.round(x), y, len, 1);
  }
  g.restore();
}
// ---- the buried colossus (DU3): a sun-king's face the size of a house, painted into the room's back layer
SPAWNS.du_colossus = (s, c) => { duFresh(); DU.colossus = { x: s.x * TILE + 8, y: (s.y + 1) * TILE }; };
function duPaintColossus(R) {
  const C = DU.colossus, sh = sheet('du_colossus'); if (!C || !sh.ok) return;
  const ctx = R.back.getContext('2d'), f = sh.frames[0], bot = 19 * TILE;
  ctx.globalAlpha = 1; ctx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(C.x - f.w / 2), bot - f.h, f.w, f.h);
}

// ================================================================== update / render / enter
HOOKS.enter.push(def => {
  duFresh(); DU.hint.drop = DU.hint.drop2 = 0;
  DU.slopes = def.du_slopes ? duSlopeLines(room) : []; DU.safe = P ? { x: P.x, y: P.y } : null; DU.safeT = 0.3; DU.underT = 0;
  if (P) { P.duSlope = 0; P.duSand = -1; }
  if (def.biome !== 'dunes') return;
  AREAS.dunes.ambient = DU_AMB[def.id] ?? 0.3;
  if (DU_OPEN.has(def.id)) duOpenBack(room);
  duRepaintUnderSlopes(room);
  if (def.id === 'DU3') duPaintColossus(room);
  const H_ = SAVE.hints, once = (k, m, d = 4.5) => { if (!H_[k]) { H_[k] = 1; setTimeout(() => toast(m, d), 1200); } };
  if (def.id === 'DU1') once('du_enter', SAVE.items.gale ? 'Heat rises off the sun-baked sand. Glide from thermal to thermal.' : 'A chasm of sinking sand. Hot air rises off it — something light could ride it.');
  if (def.id === 'DU2') once('du_dunes', 'The Sunscorched Dunes. Somewhere far above, the sun still burns.');
  if (def.id === 'DU5') once('du_altars', 'Sun-mirrors in the ceiling. Watch their rhythm.');
  if (def.id === 'DU7') once('du_hatch', 'A sun-bronze hatch in the ceiling. The lever works it.');
});
HOOKS.update.push(dt => {
  if (!duRoom()) { if (P) P.duSlope = 0; return; }
  duSlopePlayer(dt);
  duQuicksandPlayer(dt);
  duFallsPlayer(dt);
  duUpdateStorm(dt);
  duUpdateAltars(dt);
  duEnemySand(dt);
  duUpdateZones(dt);
  duUpdateShots(dt);
  DU.safeT -= dt;
  if (DU.safeT <= 0 && duSafeHere()) { DU.safe = { x: P.x, y: P.y }; DU.safeT = 0.25; }
  if (DU.safe) P.safe = DU.safe;
  // drifting sand + sun glare
  if (Math.random() < 0.3) particles.push({ x: cam.x - 10, y: cam.y + rand(0, H), vx: rand(20, 60), vy: rand(-4, 6), life: rand(5, 9), kind: 'sand', amb: true, sway: rand(0, 6) });
  for (const u of room.updrafts || []) if (Math.random() < 0.35) particles.push({ x: rand(u.x0, u.x1), y: u.y1 - rand(0, 10), vx: rand(-6, 6), vy: -rand(50, 110), life: rand(0.8, 1.6), kind: Math.random() < 0.3 ? 'sun' : 'sand' });
});
function duDrawQuicksand() {
  const tx0 = Math.max(0, Math.floor(cam.x / TILE) - 1), tx1 = Math.min(room.w - 1, Math.floor((cam.x + W) / TILE) + 1);
  const ty0 = Math.max(0, Math.floor(cam.y / TILE) - 1), ty1 = Math.min(room.h - 1, Math.floor((cam.y + H) / TILE) + 1);
  const fx = sheet('tiles_dunes_fx');
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    if (room.grid[ty * room.w + tx] !== DU_T_QS) continue;
    const px = tx * TILE, py = ty * TILE, top = ty === 0 || room.grid[(ty - 1) * room.w + tx] !== DU_T_QS;
    const zone = DU.zones.find(z => z.cells && z.cells.some(c => c[0] === tx && c[1] === ty));
    const tag = top ? 'qs_top' : 'qs_body';
    if (fx.ok && fx.has(tag)) { const t = fx.tag(tag), n = t.to - t.from + 1, f = fx.frames[t.from + (Math.floor(time * (top ? 6 : 3)) + tx * 2 + ty) % n]; g.save(); if (zone) g.globalAlpha = zone.a; g.drawImage(fx.img, f.x, f.y, 16, 16, px, py, 16, 16); g.restore(); }
    else if (top) { g.fillStyle = zone ? `rgba(200,160,96,${zone.a})` : '#c8a060'; g.fillRect(px, py + 2, 16, 2); g.fillStyle = '#8a6632'; g.fillRect(px + ((Math.floor(time * 8) + tx * 5) % 14), py + 5, 3, 1); }
  }
}
HOOKS.render.push(() => {
  if (!room || !room.grid || !duRoom()) return;
  duDrawQuicksand();
  duDrawFalls();
  const T = duAltarCycle();
  for (const a of DU.altars) {
    const t = ((time + a.ph) % T + T) % T;
    if (a.st === 'charge') duDrawBeam(a.x, a.y, a.bot, (t - DU_ALTAR.idle) / DU_ALTAR.charge, 8, true);
    if (a.st === 'fire') duDrawBeam(a.x, a.y, a.bot, 1, 8);
  }
  duDrawShots();
  // sun shafts through the rifts (open dune rooms only)
  if (!['DU5', 'DU6', 'DU7', 'DU8'].includes(room.id) && !(DU.storm && DU.storm.k > 0.5)) {
    g.save(); g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 4; i++) {
      const bx = ((i * 211 + 60) % (room.pw + 200)) - 100, a = 0.05 + 0.025 * Math.sin(time * 0.6 + i * 1.7);
      if (bx < cam.x - 200 || bx > cam.x + W + 100) continue;
      g.fillStyle = `rgba(255,226,150,${a})`; g.beginPath(); g.moveTo(bx, 0); g.lineTo(bx + 34, 0); g.lineTo(bx + 34 + 140, room.ph); g.lineTo(bx + 140, room.ph); g.closePath(); g.fill();
    }
    g.restore();
  }
});
HOOKS.renderTop.push(() => { if (room && duRoom()) duDrawStormOverlay(); });
HOOKS.rest.push(() => { DU.underT = 0; });

// ================================================================== own shots + hazards (sun flares, discs, coffins)
// shot: {x,y,vx,vy,r,dmg,id,life,t,kind,home,draw}  haz: {x,y,w,h,dmg,id,life,t,delay,active(),update(),draw(),tick}
function duShot(o) { const s = { r: 6, life: 4, t: 0, id: ++hazardId, kind: 'orb', ...o }; DU.shots.push(s); return s; }
function duHaz(o) { const h = { w: 20, h: 12, life: 1, t: 0, id: ++hazardId, tick: 0, ...o }; DU.haz.push(h); return h; }
function duMark(x, y, life, w = 18, col = '255,210,120') { DU.marks.push({ x, y, life, t: 0, w, col }); }
function duUpdateShots(dt) {
  const hb = playerHurtbox();
  for (const s of DU.shots) {
    s.t += dt; s.life -= dt;
    if (s.update) s.update(s, dt);
    s.x += s.vx * dt; s.y += s.vy * dt;
    const r = rect(s.x - s.r, s.y - s.r, s.x + s.r, s.y + s.r);
    if (overlap(r, hb) && !(s.hitT > 0)) { if (hurtPlayer(s.dmg, sign(s.vx || (P.x - s.x)), s.id + (s.multi ? '_' + Math.floor(s.t / 0.6) : ''), { src: s.src, parryable: false })) { if (!s.multi) s.life = 0; s.hitT = 0.6; } }
    s.hitT = (s.hitT || 0) - dt;
    if (!s.ghost && solidAtPx(s.x, s.y)) { s.life = 0; duSand(s.x, s.y, 6); }
  }
  DU.shots = DU.shots.filter(s => s.life > 0);
  for (const h of DU.haz) {
    if (h.delay > 0) { h.delay -= dt; if (h.delay <= 0 && h.onStart) h.onStart(h); continue; }
    h.life -= dt; h.t += dt;
    if (h.update) h.update(h, dt);
    if (h.active === undefined || h.active(h)) {
      const r = h.rect ? h.rect(h) : rect(h.x - h.w / 2, h.y - h.h, h.x + h.w / 2, h.y);
      if (overlap(r, hb)) hurtPlayer(h.dmg, h.dir || (P.x < h.x ? -1 : 1), h.tick ? h.id + '_' + Math.floor(h.t / h.tick) : h.id, { parryable: false, src: h.src });
    }
  }
  DU.haz = DU.haz.filter(h => h.life > 0);
  for (const m of DU.marks) { m.t += dt; m.life -= dt; }
  DU.marks = DU.marks.filter(m => m.life > 0);
}
function duDrawShots() {
  for (const m of DU.marks) {   // floor warning sigils
    const a = Math.min(1, m.t * 4) * (0.55 + 0.45 * Math.sin(time * 18)), X = Math.round(m.x), Y = Math.round(m.y);
    g.fillStyle = `rgba(${m.col},${0.8 * a})`; g.fillRect(X - m.w / 2, Y - 1, m.w, 1);
    g.fillStyle = `rgba(${m.col},${0.45 * a})`; g.fillRect(X - m.w / 2 + 2, Y - 2, m.w - 4, 1); g.fillRect(X - 1, Y - 4, 2, 3);
    addLight(m.x, m.y - 4, m.w, m.col, 0.5 * a);
  }
  for (const h of DU.haz) if (!(h.delay > 0) && h.draw) h.draw(h);
  for (const s of DU.shots) if (s.draw) s.draw(s); else { g.fillStyle = '#ffe9a0'; g.fillRect(Math.round(s.x) - 2, Math.round(s.y) - 2, 4, 4); addLight(s.x, s.y, 30, '255,210,120', 0.8); }
}
// a sun-flare pillar: warning sigil on the floor, then a column of light from the sky
function duSunFlare(x, floor, delay, dmg, w = 9, src = null) {
  duMark(x, floor, delay + 0.05, w * 2 + 4);
  return duHaz({ x, y: floor, w: w * 2, h: 220, dmg, delay, life: 0.5, src, onStart: () => { sfx.pillar(); shake = Math.max(shake, 2); duSand(x, floor, 8, 8, 90); },
    update: h => { addLight(h.x, floor - 40, 70, '255,236,170', 1); },
    draw: h => duDrawBeam(h.x, Math.max(cam.y - 10, floor - 260), floor, Math.min(1, (0.5 - h.t) * 4 + 0.2), w) });
}

// ================================================================== sinking floor zones (the Pharaoh's storm): floor cells turn to quicksand for a while
function duZone(cx, floorY, halfCells, life, delay) {
  const ty = Math.floor(floorY / TILE), tx0 = Math.floor(cx / TILE) - halfCells, tx1 = Math.floor(cx / TILE) + halfCells, cells = [];
  for (let tx = tx0; tx <= tx1; tx++) if (tx > 0 && tx < room.w - 1 && room.grid[ty * room.w + tx] === T_SOLID) cells.push([tx, ty]);
  if (!cells.length) return null;
  const z = { x: (tx0 + tx1 + 1) * TILE / 2, w: (tx1 - tx0 + 1) * TILE, y: floorY, cells, life, delay, a: 0, on: false };
  duMark(z.x, floorY, delay, z.w, '230,180,100');
  DU.zones.push(z); return z;
}
function duUpdateZones(dt) {
  for (const z of DU.zones) {
    if (z.delay > 0) { z.delay -= dt; if (Math.random() < 0.3) duSand(z.x + rand(-z.w / 2, z.w / 2), z.y, 1, 2, 40); if (z.delay <= 0) { z.on = true; for (const [x, y] of z.cells) room.grid[y * room.w + x] = DU_T_QS; sfx.crumble(); } continue; }
    z.life -= dt; z.a = Math.min(1, z.a + dt * 4);
    if (z.life <= 0 && z.on) {
      z.on = false; for (const [x, y] of z.cells) room.grid[y * room.w + x] = T_SOLID;
      if (Math.abs(P.x - z.x) < z.w / 2 + 6 && P.y > z.y && P.y < z.y + 2 * TILE) { P.y = z.y; P.vy = Math.min(P.vy, 0); }   // the floor firms up under you: you're pushed out, never trapped
      for (const e of enemies) if (e.alive && Math.abs(e.x - z.x) < z.w / 2 + 6 && e.y > z.y && e.y < z.y + 2 * TILE) e.y = z.y;
      duSand(z.x, z.y, 10, z.w / 2, 60);
    }
  }
  DU.zones = DU.zones.filter(z => z.life > 0 || z.delay > 0);
}
function duClearZones() { for (const z of DU.zones) if (z.on) for (const [x, y] of z.cells) room.grid[y * room.w + x] = T_SOLID; DU.zones = []; }
HOOKS.death.push(() => { if (room) duClearZones(); });

// ================================================================== enemies
Object.assign(ENEMY, {
  du_priest: { hp: 105, cinders: 150, speed: 30, aggro: 200, range: 190, poise: 16, stance: 60, dmg: { swipe: 22, flare: 26 }, cool: [1.5, 2.4], lunge: { swipe: 50 } },
  du_scarab: { hp: 66, cinders: 90, speed: 64, aggro: 170, range: 30, poise: 10, stance: 40, dmg: { bite: 18, burst: 20 }, cool: [0.9, 1.6], lunge: { bite: 90 } },
  du_jackal: { hp: 290, cinders: 300, speed: 52, aggro: 190, range: 76, poise: 60, stance: 170, dmg: { combo: 32, lunge: 36 }, cool: [1.2, 2.0], lunge: { combo: 70, lunge: 190 }, guard: true, elite: true },
  du_soldier: { hp: 55, cinders: 0, speed: 46, aggro: 400, range: 44, poise: 14, stance: 50, dmg: { attack: 22 }, cool: [1.0, 1.8], lunge: { attack: 80 } },
});
Object.assign(ATTACK_TAGS, { du_priest: ['swipe'], du_scarab: ['bite'], du_jackal: ['combo', 'lunge'], du_soldier: ['attack'] });
const DU_LIVE = ['hurt', 'stagger', 'parried', 'dead'];
function duPre(e, dt) {
  e.flash = Math.max(0, e.flash - dt * 5); e.poise = Math.max(0, e.poise - dt * 12); e.stance = Math.max(0, e.stance - dt * 6);
  e.bleed = Math.max(0, e.bleed - dt * 6); e.dmgT -= dt;
  if (e.rotT > 0) { e.rotT -= dt; e.hp -= e.maxHp * 0.025 * dt; if (e.hp <= 0) { e.die({ dir: 0 }); return false; } }
  e.anim.update(dt);
  if (!e.aggro && e.canSee()) { e.aggro = true; e.cool = Math.max(e.cool, 0.5); }
  if (e.aggro && (Math.abs(e.dist()) > e.cfg.aggro * 1.9 || Math.abs(P.y - e.y) > 170 || P.state === 'dead')) { e.lostT += dt; if (e.lostT > 2.5) { e.aggro = false; e.lostT = 0; } } else e.lostT = 0;
  e.cool -= dt;
  return true;
}
function duMetaPt(e, key, fb) { const m = e.sh.meta && e.sh.meta.spawn && e.sh.meta.spawn[key]; return m ? metaPoint(e.sh, e, m.at) : fb; }

// ---- mummified sun-priest: keeps its distance and calls down sun-flares where you stand; a staff swipe up close
class DuPriest extends Enemy {
  canSee() {   // from a ledge it still watches the sand below (its flares fall on you wherever you stand)
    const dx = this.dist(), dy = P.y - this.y;
    if (Math.abs(dx) > this.cfg.aggro * (charmOn('c_veil') ? 0.65 : 1) || dy > 140 || dy < -70) return false;
    return lineOfSight(this.x, this.y - this.h * 0.7, P.x, P.y - 16);
  }
  update(dt) {
    if (DU_LIVE.includes(this.state)) return super.update(dt);
    if (!duPre(this, dt)) return;
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'idle': case 'walk': {
        if (!this.aggro) { this.patrol(dt); break; }
        this.facePlayer();
        if (adx < 40 && Math.abs(dy) < 26 && this.cool <= 0) { this.startAttack('swipe'); break; }
        if (this.cool <= 0 && adx < c.range && adx > 44 && dy < 140 && dy > -70 && this.canSee()) { this.startAttack('cast'); this.cast = null; break; }
        const want = adx < 64 ? -sign(dx) : adx > 150 ? sign(dx) : 0;
        this.walk(want, dt, want === -sign(dx) ? 0.8 : 1);
        break;
      }
      case 'attack': {
        const an = this.anim;
        if (this.atk === 'cast') {
          if (an.i < 5) this.facePlayer();
          const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.cast;
          if (an.changed && an.i === 2) { const p = duMetaPt(this, 'cast', { x: this.x + this.face * 6, y: this.y - 36 }); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
          if (!this.cast && an.i >= (sp ? sp.frame : 6)) {
            const fx0 = P.x + clamp(P.vx, -120, 120) * 0.25, fl = duFloorBelow(fx0, P.y - 20, 8 * TILE);
            this.cast = true;
            if (fl !== null) duSunFlare(fx0, fl, 0.8, c.dmg.flare * NGP.dmg, 8, this);
          }
          this.vx *= Math.pow(0.004, dt); this.gravity(dt);
          if (an.done) { this.setA('idle', 'idle'); this.cool = rand(...c.cool); }
        } else this.updateAttack(dt);
        break;
      }
    }
    addLight(this.x, this.y - 30, 26, '255,200,110', 0.5);
  }
}

// ---- scarab swarm: burrows, a ripple races under the sand toward you, and it bursts up at your feet
class DuScarab extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.state = 'under'; this.t = rand(0.6, 1.4); this.anim.set(this.sh.has('crawl') ? 'crawl' : 'idle', true); }
  hurtbox() { if (this.state === 'under' || this.state === 'surfacing') return null; return super.hurtbox(); }
  update(dt) {
    if (this.state === 'dead' || ['hurt', 'stagger', 'parried'].includes(this.state)) return super.update(dt);
    if (!duPre(this, dt)) return;
    const c = this.cfg, dx = this.dist(), adx = Math.abs(dx), dy = P.y - this.y;
    switch (this.state) {
      case 'under': {
        this.t -= dt;
        const tgt = this.aggro && Math.abs(dy) < 60 ? P.x : this.home + Math.sin(time * 0.6 + this.id) * 30;
        const d = Math.abs(tgt - this.x) > 4 ? sign(tgt - this.x) : 0;
        if (d && ledgeAhead(this, d) && !wallAt(this, d)) { this.x += d * 78 * dt; this.face = d; }
        this.vx = 0; this.vy = Math.min(this.vy + 800 * dt, 400); moveBody(this, dt); this.clampRoom();
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-7, 7), y: this.y - 1, vx: -this.face * rand(5, 30), vy: -rand(10, 40), g: 250, life: 0.4, kind: 'sandd' });
        if (this.aggro && this.t <= 0 && adx < 26 && Math.abs(dy) < 30) { this.state = 'surfacing'; this.t = 0.42; sfx.glint(); spawnFx('telegraph', this.x, this.y - 6, this.face); }
        break;
      }
      case 'surfacing':
        this.t -= dt; if (Math.random() < 0.9) duSand(this.x, this.y, 2, 8, 70);
        if (this.t <= 0) { this.facePlayer(); this.state = 'emerge'; this.anim.set(this.sh.has('emerge') ? 'emerge' : 'idle', false); this.atkId = ++hazardId; this.vy = -170; this.vx = this.face * 60; this.ground = false; duSand(this.x, this.y, 12, 10, 110); sfx.crumble(); }
        break;
      case 'emerge': {
        this.gravity(dt);
        if (overlap(super.hurtbox() || rect(this.x - 8, this.y - 14, this.x + 8, this.y), playerHurtbox())) hurtPlayer(c.dmg.burst * NGP.dmg, this.face, this.atkId, { src: this });
        if ((this.anim.done || !this.sh.has('emerge')) && this.ground && this.vy >= 0) { this.setA('idle', 'idle'); this.cool = 0.5; this.surfT = 0; }
        break;
      }
      case 'idle': case 'walk': {
        this.surfT = (this.surfT || 0) + dt;
        if (!this.aggro || this.surfT > 4.5 || adx > 120) { this.state = 'burrow'; this.anim.set(this.sh.has('burrow') ? 'burrow' : 'idle', false); break; }
        this.facePlayer();
        if (adx < 30 && Math.abs(dy) < 20 && this.cool <= 0) { this.startAttack('bite'); break; }
        this.walk(adx > 18 ? sign(dx) : 0, dt, 1);
        if (this.anim.tag === 'walk' && this.sh.has('crawl')) this.anim.set('crawl', true);
        break;
      }
      case 'burrow':
        this.vx *= Math.pow(0.01, dt); this.gravity(dt);
        if (this.anim.done || !this.sh.has('burrow')) { this.state = 'under'; this.t = rand(0.8, 1.6); duSand(this.x, this.y, 8); }
        break;
      case 'attack': this.updateAttack(dt); break;
    }
  }
  draw() {
    if (this.state === 'under' || this.state === 'surfacing') {   // a travelling sand ripple
      const X = Math.round(this.x), Y = Math.round(this.y), k = this.state === 'surfacing' ? 1.6 : 1;
      g.fillStyle = 'rgba(214,170,100,0.95)'; g.fillRect(X - 7, Y - Math.round(2 * k), 14, Math.round(2 * k));
      g.fillStyle = 'rgba(250,220,160,0.9)'; g.fillRect(X - 4, Y - Math.round(3 * k), 8, 1);
      g.fillStyle = 'rgba(120,84,40,0.9)'; g.fillRect(X - 7, Y - 1, 14, 1);
      if (this.state === 'surfacing') { g.fillStyle = 'rgba(255,200,90,0.9)'; g.fillRect(X - 1, Y - 5, 2, 1); }
      return;
    }
    super.draw();
  }
}

// ---- sand-soldier (the Pharaoh's summons): rises out of the sand, marches, crumbles when he falls
class DuSoldier extends Enemy {
  constructor(type, x, y, key) { super(type, x, y, key); this.state = 'rise'; this.anim.set(this.sh.has('rise') ? 'rise' : 'idle', false); this.aggro = true; }
  hurtbox() { if (this.state === 'rise' && this.anim.i < 2) return null; return super.hurtbox(); }
  update(dt) {
    if (this.state === 'rise') { this.anim.update(dt); this.gravity(dt); if (Math.random() < 0.4) duSand(this.x, this.y, 1, 8, 50); if (this.anim.done) { this.setA('idle', 'idle'); this.cool = 0.4; } return; }
    if (boss && boss.kind === 'pharaoh' && !boss.alive && this.alive) { this.die({ dir: 0 }); duSand(this.x, this.y - 10, 16, 8, 80); return; }
    if (this.alive && boss && boss.kind === 'pharaoh') { this.x = clamp(this.x, boss.L - 10, boss.R + 10); }
    super.update(dt);
  }
}
Object.assign(ENEMY_CLASSES, { du_priest: DuPriest, du_scarab: DuScarab, du_soldier: DuSoldier });

// ================================================================== THE SCARAB KNIGHT (mini-boss, DU6 The Scarab's Pit)
// A knight of the sun-kings grown a beetle's carapace in the long dark. Spear thrusts and wide sweeps; he BURROWS (a mound
// races under the sand and he erupts beneath you — watch the sand boil) and CHARGES horn-first (a rear-up telegraph; he
// crashes into the fog wall and reels: the punish window). Phase 2 (50%): faster, double eruptions, scarab swarms.
BOSS_INFO.scarab = { name: 'The Scarab Knight', hp: 1800, cinders: 6500, reward: ['w:scarab_spear', 'emberstone'],
  quote: 'The sun-kings asked their knights to guard them forever. Some of them listened.' };
class DuScarabKnight extends MetaBoss {
  get L() { return 2 * TILE + 24; }
  get R() { return 38 * TILE - 24; }
  constructor(x, y) {
    super('scarab', x, y, {
      sheets: ['scarab'], stanceMax: 260, walkSpeed: 44, prefer: 58, p2at: 0.5, p2speed: 1.2, p2tag: 'rear', critRange: 50,
      introTag: 'idle', cool1: [0.8, 1.4], cool2: [0.5, 1.0], victory: 'THE SCARAB KNIGHT IS BURIED', deathParticle: 'sand',
      weights(d, p2) {
        if (d < 64) return { thrust: 2.2, sweep: 2.6, burrow: p2 ? 1.2 : 0.6, rear: 0.4 };
        if (d < 160) return { thrust: 1.6, burrow: 1.6, rear: p2 ? 1.8 : 1.2, walk: 1 };
        return { rear: 2.2, burrow: 2, walk: 1.6 };
      },
      chains: { thrust: d => d < 70 ? 'sweep' : null, sweep: d => d > 90 ? 'rear' : null },
      moves: {
        thrust: { dmg: [44], parry: true, step: 130 },
        sweep: { dmg: [38, 44], parry: true, step: 40, shake: 2 },
        rear: { dmg: [] }, burrow: { dmg: [] }, emerge: { dmg: [52], shake: 6 },
      },
      wake() { return P.x < 35 * TILE && P.ground; },
      onIntro() { sfx.roar(); shake = 6; },
      onPhase2() { flashScreen = 0.3; shake = 7; sfx.roar(); toast('Its carapace splits — the swarm pours out', 3); this.swarm = 2; },
      ambient(dt) { addLight(this.x, this.y - 30, 60, '255,200,110', 0.5); },
    });
    this.meta = ASSETS.scarab_meta || {}; this.smap = this.meta.sheets || {};
    for (const n of new Set([...Object.values(this.smap), ...this.sheets])) sheet(n).configure({ meta: this.meta });   // sheets preloaded bare get the shared meta
    this.face = -1; this.swarm = 0;
  }
  hasTag(tag) { return this.smap[tag] ? sheet(this.smap[tag], { meta: this.meta }).has(tag) : this.sh.has(tag); }
  sheetFor(tag) { const n = this.smap[tag]; return n ? sheet(n, { meta: this.meta }) : this.sheetsArr[0]; }
  setS(st, tag, loop = true) { this.state = st; let sh = this.sheetFor(tag); if (!sh.has(tag)) { tag = 'idle'; sh = this.sheetFor('idle'); } this.sh = sh; this.anim = new Anim(sh, tag, loop, this.speed); }
  pickMove() {
    const d = Math.abs(P.x - this.x), w = this.weights(d, this.phase === 2);
    if (w[this.last]) w[this.last] *= 0.3;
    const e = Object.entries(w).filter(([k, v]) => v > 0 && (k === 'walk' || this.hasTag(k)));
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e.length ? e[0][0] : 'walk';
  }
  hurtbox() { if (['under', 'rising'].includes(this.state)) return null; if (this.state === 'attack' && this.atk === 'burrow' && this.anim.i >= this.anim.n - 3) return null; return super.hurtbox(); }
  canStagger() { return !['under', 'rising', 'charge'].includes(this.state) && !(this.state === 'attack' && ['burrow', 'emerge'].includes(this.atk)); }
  start(m) {
    super.start(m);
    if (m === 'rear') { spawnFx('telegraph', this.x + this.face * 20, this.y - 40, this.face); }
  }
  update(dt) {
    if (this.state === 'under' || this.state === 'rising' || this.state === 'charge' || this.state === 'crash') {
      this.commonUpdate(dt); this.anim.update(dt);
      if (this.state === 'under') this.underUpdate(dt);
      else if (this.state === 'rising') this.risingUpdate(dt);
      else if (this.state === 'charge') this.chargeUpdate(dt);
      else { this.t -= dt; if (this.t <= 0) { this.setS('idle', 'idle'); this.cool = 0.35; } }
      if (this.phase === 1 && this.hp <= this.maxHp * this.p2at && this.alive && !this.pendingPhase) this.pendingPhase = true;
      this.ambient(dt); this.x = clamp(this.x, this.L, this.R); return;
    }
    if (!this.sh.has(this.anim.tag)) this.setS(this.state, 'idle', true);
    super.update(dt);
    if (this.alive && this.active && this.phase === 2 && this.swarm > 0 && this.state === 'idle' && enemies.filter(e => e.alive && e.type === 'du_scarab').length < 2) {
      this.swarm--; const x = clamp(this.x - this.face * 40, this.L, this.R); enemies.push(makeEnemy('du_scarab', x, this.floor, 'DU6:swarm' + (++hazardId))); duSand(x, this.floor, 12);
    }
  }
  updateAttack(dt) {
    const an = this.anim;
    if (this.atk === 'burrow' || this.atk === 'rear') {   // wind-ups that hand over to the under/charge states
      if (this.atk === 'burrow' && Math.random() < 0.7) duSand(this.x + rand(-20, 20), this.floor, 2, 10, 80);
      if (this.atk === 'rear' && an.i < an.n - 2) this.facePlayer();
      if (an.done || !this.hasTag(this.atk)) { if (this.pendingPhase) return this.enterPhase2(); return this.atk === 'burrow' ? this.goUnder() : this.goCharge(); }
      return;
    }
    if (this.atk === 'emerge' && an.done && this.eruptions > 0 && !this.pendingPhase) { this.goUnder(true); this.t = 0.55; return; }
    super.updateAttack(dt);
  }
  stagger() { super.stagger(); const t = this.t; this.setS('stagger', 'stagger', false); this.t = t; }
  die() { super.die(); this.setS('dead', this.hasTag('death') ? 'death' : 'stagger', false); }
  goUnder(again = false) {
    this.state = 'under'; this.t = this.phase === 2 ? rand(0.9, 1.4) : rand(1.2, 1.8); this.moundX = this.x; if (!again) this.eruptions = this.phase === 2 ? 2 : 1;
    sfx.crumble(); duSand(this.x, this.floor, 16, 18, 100); shake = Math.max(shake, 3);
  }
  underUpdate(dt) {
    this.t -= dt;
    const tx = clamp(P.x, this.L, this.R), v = 150 * this.speed;
    this.x = approach(this.x, tx, v * dt);
    if (Math.random() < 0.8) particles.push({ x: this.x + rand(-12, 12), y: this.floor - 1, vx: rand(-30, 30), vy: -rand(20, 70), g: 300, life: 0.5, kind: Math.random() < 0.5 ? 'sand' : 'sandd' });
    if (Math.random() < 0.1) shake = Math.max(shake, 1);
    if (this.t <= 0 || (Math.abs(this.x - tx) < 6 && this.t < 0.8)) { this.state = 'rising'; this.t = 0.55; sfx.glint(); spawnFx('telegraph', this.x, this.floor - 10, this.face); }
  }
  risingUpdate(dt) {
    this.t -= dt;
    if (Math.random() < 0.9) duSand(this.x + rand(-10, 10), this.floor, 2, 8, 120);
    addLight(this.x, this.floor - 6, 40, '255,200,110', 0.8);
    if (this.t <= 0) {
      this.facePlayer(); this.atk = 'emerge'; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.spawned = false; this.air = null;
      this.setS('attack', 'emerge', false); const wins = metaWindows(this.sh, 'emerge'); this.firstActive = wins.length ? wins[0].active[0] : 2;
      duSand(this.x, this.floor, 20, 16, 160); shake = Math.max(shake, 6); sfx.boom();
      this.eruptions--;
    }
  }
  goCharge() {
    this.state = 'charge'; this.chargeDir = this.face; this.t = 2.2; this.atkId = ++hazardId; this.hitIds = new Set();
    this.setS('charge', this.hasTag('charge') ? 'charge' : 'walk', true); this.state = 'charge'; sfx.roar();
  }
  chargeUpdate(dt) {
    this.t -= dt;
    this.x += this.chargeDir * 290 * this.speed * dt;
    if (this.anim.changed && this.anim.i % 2 === 0) { shake = Math.max(shake, 2); sfx.step(); }
    if (Math.random() < 0.8) particles.push({ x: this.x - this.chargeDir * 30, y: this.floor - 2, vx: -this.chargeDir * rand(30, 90), vy: -rand(10, 60), g: 300, life: 0.5, kind: 'sand' });
    const hb = this.hurtboxRaw();
    if (hb && !this.hitIds.has(0) && overlap(hb, playerHurtbox()) && hurtPlayer(duDmg(50), this.chargeDir, this.atkId, { src: this })) { this.hitIds.add(0); P.vx = this.chargeDir * 220; }
    const wall = this.chargeDir > 0 ? this.x >= this.R - 2 : this.x <= this.L + 2;
    if (wall) {   // horn into the fog: he reels -- punish him
      this.x = clamp(this.x, this.L, this.R); shake = 9; sfx.boom(); spawnFx('shockwave', this.x + this.chargeDir * 30, this.floor, 1); duSand(this.x + this.chargeDir * 30, this.floor - 20, 18, 10, 120);
      if (this.phase === 2) for (const dd of [-1]) hazards.push({ x: this.x, y: this.floor, vx: dd * this.chargeDir * 160, w: 14, h: 14, dmg: duDmg(26), id: ++hazardId, life: 1.6, wave: true, dir: dd * this.chargeDir, color: 'root' });
      this.state = 'crash'; this.setS('crash', this.hasTag('stagger') ? 'stagger' : 'idle', false); this.state = 'crash'; this.t = 1.2;
    } else if (this.t <= 0 || ((this.x - P.x) * this.chargeDir > 130)) { this.setS('idle', 'idle'); this.cool = 0.5; }
  }
  hurtboxRaw() { const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 22, this.y - 50, this.x + 22, this.y); }
  critable() { return (this.state === 'stagger' || this.state === 'crash') && this.anim.i >= 1 && !this.critDone; }
  hit(info) {
    if (this.state === 'crash' && !info.crit) info = { ...info, dmg: info.dmg * 1.25 };
    super.hit(info);
  }
  draw() {
    if (this.state === 'under' || this.state === 'rising') {   // the mound under the sand
      const X = Math.round(this.x), Y = Math.round(this.floor), k = this.state === 'rising' ? 1 + (0.55 - this.t) * 2 : 1;
      g.fillStyle = 'rgba(190,146,80,0.95)'; g.beginPath(); g.ellipse(X, Y, 22 * k, 5 * k, 0, Math.PI, 0); g.fill();
      g.fillStyle = 'rgba(240,206,140,0.95)'; g.beginPath(); g.ellipse(X - 3, Y - 1, 14 * k, 3 * k, 0, Math.PI, 0); g.fill();
      if (this.state === 'rising') { g.fillStyle = '#ffd070'; g.fillRect(X - 1, Y - 8 - Math.round(k * 2), 2, 2); addLight(X, Y - 6, 30, '255,210,120', 0.9); }
      return;
    }
    if (!this.sh.has(this.anim.tag)) this.setS(this.state, 'idle', true);
    super.draw();
  }
}
BOSS_SPAWN.scarab = (cx, fy) => new DuScarabKnight(cx, fy);
BOSS_CUTS.scarab = b => [
  act(() => { b.state = 'under'; b.t = 99; b.x = clamp(P.x - 110, b.L + 20, b.R); b.face = 1; }),
  { pan: { x: P.x - 60, y: b.floor - 50 }, dur: 0.9 },
  { dur: 1.3, tween: (dt, k) => { b.x = lerp(b.x, P.x - 70, dt * 2.5); if (Math.random() < 0.8) duSand(b.x + rand(-12, 12), b.floor, 2, 8, 90); shake = Math.max(shake, 1.2); } },
  act(() => { b.state = 'intro'; b.setS('intro', b.hasTag('emerge') ? 'emerge' : 'idle', false); b.facePlayer(); duSand(b.x, b.floor, 26, 18, 160); shake = 8; sfx.boom(); sfx.roar(); }), wait(1.0),
  say('', 'A knight of the sun-kings, grown a beetle’s shell in the long dark.'),
  { do: () => { b.setS('idle', 'idle'); b.facePlayer(); }, always: true },
];
PHASE2_LINES.scarab = ['', 'The Scarab Knight’s carapace splits. Something skitters inside.'];

// ================================================================== THE VEILED PHARAOH (main boss, DU8 The Veiled Sanctum)
// The last sun-king, who would not be buried. Phase 1: khopesh strings (parry the first two), a sceptre sun-beam that sweeps
// down across the floor in front of him (roll through it, or get behind him), sand-coffins that rise where you stand and
// slam shut, sand-soldiers, and a sun-disc that hunts you. Phase 2 (50%): the SANDSTORM -- the sanctum goes dark and the
// wind never stops; he sinks into the sand and strikes out of the storm (only his amber eye gives him away), sun-eye beams
// cut down through the dark, and patches of the floor turn to quicksand.
BOSS_INFO.pharaoh = { name: 'The Veiled Pharaoh', hp: 4000, cinders: 21000, reward: ['w:pharaoh_khopesh', 'sp:sandstorm', 'c_sun'],
  quote: 'He counted every grain of his desert. He never counted the dusk.' };
const DU_PH_RANGED = new Set(['beam', 'coffin', 'summon', 'disc', 'eyes']);
class DuPharaoh extends MetaBoss {
  get L() { return 16 * TILE + 28; }
  get R() { return 55 * TILE - 28; }
  constructor(x, y) {
    super('pharaoh', x, y, {
      sheets: ['pharaoh_a'], stanceMax: 380, walkSpeed: 38, prefer: 70, p2at: 0.5, p2speed: 1.15, p2tag: 'summon', critRange: 56,
      introTag: 'idle', cool1: [0.9, 1.5], cool2: [0.6, 1.1], victory: 'THE LAST SUN SETS', deathParticle: 'sand',
      weights(d, p2) {
        const soldiers = enemies.filter(e => e.alive && e.type === 'du_soldier').length;
        const far = { beam: 2, coffin: 1.6, disc: this.discOut() ? 0 : 1.4, summon: soldiers < (p2 ? 2 : 3) && this.summonCd <= 0 ? 1.1 : 0, walk: 1.6 };
        if (p2) Object.assign(far, { strike: 2.4, eyes: 1.8, sink: this.sinkCd <= 0 ? 1.4 : 0, beam: 1.1, walk: 0.8 });
        if (this.rangedRun >= 2) { for (const k of DU_PH_RANGED) if (far[k]) far[k] *= 0.2; far.walk = (far.walk || 0) + 2; if (p2) far.strike = (far.strike || 0) + 2; }
        if (d < 80) return p2 ? { combo: 2.6, eyes: 1.0, sink: this.sinkCd <= 0 ? 1.0 : 0, backstep: 0.8, strike: 1.0, coffin: 0.5 }
                              : { combo: 3.2, beam: 0.6, coffin: 0.5, backstep: 0.8 };
        if (d < 170) return { combo: 1.1, ...far };
        return far;
      },
      chains: { combo: d => d > 100 ? 'beam' : null, backstep: d => d > 110 ? 'coffin' : 'disc', strike: d => d < 80 ? 'combo' : null },
      moves: {
        combo: { dmg: [40, 44, 58], parry: true, step: 60, fx: null },
        beam: { dmg: [] }, coffin: { dmg: [] }, summon: { dmg: [] }, disc: { dmg: [] },
        vanish: { dmg: [] }, emerge: { dmg: [54], shake: 7 },
      },
      wake() { return P.x > 17 * TILE + 8 && P.ground; },
      onIntro() { sfx.roar(); shake = 6; },
      onPhase2() { this.p2Storm(); },
      ambient(dt) { this.pAmbient(dt); },
      onDeath() { this.pDeath(); },
    });
    this.meta = ASSETS.pharaoh_meta || {}; this.smap = this.meta.sheets || {};
    for (const n of new Set([...Object.values(this.smap), ...this.sheets])) sheet(n).configure({ meta: this.meta });   // sheets preloaded bare get the shared meta
    this.face = -1; this.summonCd = 0; this.sinkCd = 0; this.recent = []; this.vis = 1; this.eye = 0.3; this.hidden = false;
    this.setS('dormant', this.hasTag('rise') ? 'rise' : 'idle', false); this.anim.speed = 0; this.state = 'dormant';   // a standing sarcophagus until woken
  }
  hasTag(tag) { return this.smap[tag] ? sheet(this.smap[tag], { meta: this.meta }).has(tag) : this.sh.has(tag); }
  sheetFor(tag) { const n = this.smap[tag]; return n ? sheet(n, { meta: this.meta }) : this.sheetsArr[0]; }
  setS(st, tag, loop = true) { this.state = st; let sh = this.sheetFor(tag); if (!sh.has(tag)) { tag = 'idle'; sh = this.sheetFor('idle'); } this.sh = sh; this.anim = new Anim(sh, tag, loop, this.speed); }
  discOut() { return DU.shots.some(s => s.kind === 'disc'); }
  pickMove() {
    const d = Math.abs(P.x - this.x), w = this.weights(d, this.phase === 2);
    if (w[this.last]) w[this.last] *= 0.25;
    if (this.recent[1] && w[this.recent[1]]) w[this.recent[1]] *= 0.6;
    const e = Object.entries(w).filter(([k, v]) => v > 0 && (['walk', 'backstep', 'strike', 'eyes', 'sink'].includes(k) || this.hasTag(k)));
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return e.length ? e[0][0] : 'walk';
  }
  start(m) {
    this.recent.unshift(m); this.recent.length = Math.min(3, this.recent.length);
    const rr = DU_PH_RANGED.has(m) ? (this.rangedRun || 0) + 1 : 0;
    this.pStart(m); this.rangedRun = rr;
  }
  pStart(m) {
    if (m === 'strike') { this.facePlayer(); this.last = m; this.atk = 'vanish'; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.setS('attack', this.hasTag('vanish') ? 'vanish' : 'idle', false); this.firstActive = 99; this.vanishing = true; return; }
    if (m === 'eyes' || m === 'sink') { const tag = m === 'eyes' ? 'beam' : 'coffin'; super.start(tag); this.atk = m; this.last = m; this.firstActive = 99; return; }
    if (m === 'backstep') { this.facePlayer(); this.last = m; this.atk = m; this.setS('backstep', this.hasTag('walk') ? 'walk' : 'idle', true); this.bs = { x0: this.x, t: 0 }; this.state = 'backstep'; return; }
    super.start(m);
    if (m === 'beam') { this.beam = { a0: -0.95, a1: 0.42, on: false, t: 0 }; }
    if (m === 'summon') this.summonCd = 9;
  }
  update(dt) {
    this.summonCd -= dt; this.sinkCd -= dt;
    if (this.state === 'backstep') {   // a gliding retreat across the sand (his feet never leave it)
      this.commonUpdate(dt); this.anim.update(dt); this.bs.t += dt;
      const k = Math.min(1, this.bs.t / 0.55); this.x = clamp(this.bs.x0 - this.face * 90 * Math.sin(k * Math.PI / 2), this.L, this.R);
      if (Math.random() < 0.8) duSand(this.x + this.face * 10, this.floor, 1, 10, 40);
      if (k >= 1) { const nx = this.chains.backstep.call(this, Math.abs(P.x - this.x)); this.start(nx); }
      this.ambient(dt); return;
    }
    if (this.state === 'buried') return this.buriedUpdate(dt);
    if (!this.sh.has(this.anim.tag)) this.setS(this.state, 'idle', true);
    super.update(dt);
    this.x = clamp(this.x, this.L, this.R);
  }
  // ---- scripted attack beats (driven off the animation frames; indices come from pharaoh_meta.events)
  ev(name, def) { const e = this.meta.events && this.meta.events[name]; return e ?? def; }
  updateAttack(dt) {
    const an = this.anim, a = this.atk;
    if (a === 'vanish') return this.vanishUpdate(dt);
    if (a === 'beam' || a === 'eyes') this.beamUpdate(dt);
    if (a === 'coffin' || a === 'sink') {
      if (an.changed && an.i === 1) { spawnFx('telegraph', this.x + this.face * 14, this.y - 70, this.face); sfx.glint(); }
      if (an.changed && an.i === this.ev('coffin', 6) && !this.fired.c) { this.fired.c = true; if (a === 'coffin') this.coffins(); else this.sinkZones(); }
    }
    if (a === 'summon' && an.changed && an.i === this.ev('summon', 7) && !this.fired.s) { this.fired.s = true; this.summonSoldiers(); }
    if (a === 'disc' && an.changed && an.i === this.ev('disc', 7) && !this.fired.d) { this.fired.d = true; this.throwDisc(); }
    if (a === 'disc' && an.i < this.ev('disc', 7)) { const p = this.sceptreTip(); addLight(p.x, p.y, 30 + an.i * 6, '255,210,110', 1); }
    super.updateAttack(dt);
  }
  sceptreTip() { const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.tip; const fr = sp && sp.frames && sp.frames[this.anim.tag]; const pt = fr ? fr[Math.min(this.anim.i, fr.length - 1)] : null; return pt ? metaPoint(this.sh, this, pt) : { x: this.x + this.face * 30, y: this.y - 96 }; }
  // sceptre sun-beam: an aim line first, then a beam that sweeps from high in front of him down across the floor
  beamUpdate(dt) {
    const an = this.anim, B = this.beam || (this.beam = { a0: -0.95, a1: 0.42, t: 0 });
    const f0 = this.ev('beam_on', 6), f1 = this.ev('beam_off', 10);
    if (this.atk === 'eyes') {   // phase 2: the eye glares and sun-eye beams cut down through the storm
      if (an.changed && an.i === 3 && !this.fired.e) {
        this.fired.e = true; sfx.howl(); flashScreen = 0.15;
        const n = 4, gap = 58, s = Math.random() < 0.5 ? -1 : 1;
        for (let k = 0; k < n; k++) { const x = clamp(P.x + s * (k - 1) * gap + rand(-8, 8), this.L - 10, this.R + 10); duSunFlare(x, this.floor, 0.75 + k * 0.28, duDmg(40), 10, this); }
      }
      return;
    }
    if (an.i < f0) { B.warn = true; B.on = false; const p = this.sceptreTip(); B.x = p.x; B.y = p.y; B.a = B.a0; addLight(p.x, p.y, 20 + an.i * 7, '255,230,160', 1); if (an.changed && an.i === f0 - 3) sfx.glint(); return; }
    if (an.i > f1) { B.on = false; B.warn = false; return; }
    if (!B.on) { B.on = true; B.warn = false; B.t = 0; B.id = ++hazardId; sfx.fire(); sfx.pillar(); shake = 4; }
    B.t += dt;
    let T = 0; for (let i = f0; i <= f1; i++) T += an.ms(i); T = T / 1000 / an.speed;
    const k = Math.min(1, B.t / T), p = this.sceptreTip();
    B.x = p.x; B.y = p.y; B.a = lerp(B.a0, B.a1, k * k * (3 - 2 * k));
    const dx = Math.cos(B.a) * this.face, dy = Math.sin(B.a);
    let L = 420; if (dy > 0.001) L = Math.min(L, (this.floor - B.y) / dy);
    B.L = L; B.ex = B.x + dx * L; B.ey = B.y + dy * L;
    const hb = playerHurtbox();
    for (let s = 10; s <= L; s += 6) { const px = B.x + dx * s, py = B.y + dy * s; if (overlap(rect(px - 7, py - 7, px + 7, py + 7), hb)) { hurtPlayer(duDmg(26), this.face, B.id + '_' + Math.floor(B.t / 0.3), { src: this }); break; } }
    for (let s = 20; s < L; s += 40) addLight(B.x + dx * s, B.y + dy * s, 50, '255,230,160', 1);
    if (dy > 0.05 && Math.random() < 0.7) duSand(B.ex, this.floor, 2, 6, 90);
  }
  coffins() {
    sfx.boom(); shake = 5; const n = this.phase === 2 ? 3 : 2;
    const xs = [P.x + clamp(P.vx, -120, 120) * 0.3];
    for (let k = 1; k < n; k++) xs.push(P.x + (k % 2 ? -1 : 1) * (46 + Math.floor((k - 1) / 2) * 40));
    xs.forEach((x0, k) => { const x = clamp(x0, this.L - 10, this.R + 10); this.coffin(x, 0.1 + k * 0.18); });
  }
  coffin(x, delay) {
    const fl = this.floor, sh = fxSheet('du_coffin'), self = this;
    duMark(x, fl, delay + 0.75, 30, '240,200,120');
    duHaz({ x, y: fl, w: 26, h: 50, dmg: duDmg(46), delay: delay, life: 2.2, src: this, t: 0,
      onStart: h => { h.fx = sh.ok ? { i: 0, t: 0 } : null; duSand(x, fl, 10, 12, 90); sfx.crumble(); },
      update: h => { if (h.fx) { h.fx.t += 1 / 60; } if (Math.random() < 0.3) duSand(x, fl, 1, 12, 40); if (h.t > 0.72 && h.t < 0.8 && !h.slam) { h.slam = true; sfx.boom(); shake = Math.max(shake, 4); duSand(x, fl - 30, 12, 12, 60); } },
      active: h => h.t > 0.72 && h.t < 1.0,   // the lid slams on whoever stands in it
      draw: h => {
        const k = Math.min(1, h.t / 0.45), close = clamp((h.t - 0.55) / 0.2, 0, 1), fade = h.life < 0.4 ? h.life / 0.4 : 1;
        if (sh.ok) { const t = sh.tag(Object.keys(sh.tags)[0]), n = t.to - t.from + 1, fi = h.t < 0.45 ? Math.floor(k * (n * 0.5)) : h.t < 0.55 ? Math.floor(n * 0.5) : Math.min(n - 1, Math.floor(n * 0.5) + Math.floor(close * (n * 0.5))); drawSprite(sh, t.from + clamp(fi, 0, n - 1), x, fl, 1, { bottom: true, alpha: fade }); }
        else { const hh = Math.round(52 * k); g.fillStyle = `rgba(150,110,50,${fade})`; g.fillRect(Math.round(x) - 12, fl - hh, 24, hh); g.fillStyle = `rgba(230,190,90,${fade})`; g.fillRect(Math.round(x) - 12 + Math.round((1 - close) * 14), fl - hh, 4, hh); }
        if (h.t > 0.5 && h.t < 0.8) addLight(x, fl - 26, 40, '255,210,120', 0.8);
      } });
  }
  summonSoldiers() {
    sfx.roar(); shake = 4; const n = this.phase === 2 ? 1 : 2;
    for (let k = 0; k < n; k++) {
      const side = k % 2 ? 1 : -1, x = clamp(P.x + side * rand(60, 90), this.L - 8, this.R + 8);
      duMark(x, this.floor, 0.5, 20, '230,190,110');
      duHaz({ x, y: this.floor, w: 0, h: 0, dmg: 0, delay: 0.45 + k * 0.18, life: 0.02, active: () => false,
        onStart: () => { if (!this.alive) return; enemies.push(makeEnemy('du_soldier', x, this.floor, 'DU8:sol' + (++hazardId))); duSand(x, this.floor, 16, 10, 100); } });
    }
  }
  throwDisc() {
    const p = this.sceptreTip(), self = this, sh = fxSheet('du_disc');
    sfx.fire(); shake = 3;
    duShot({ kind: 'disc', x: p.x, y: p.y, vx: this.face * 40, vy: -30, r: 9, dmg: duDmg(36), life: this.phase === 2 ? 5.5 : 4.6, src: this, ghost: true, multi: true,
      update: (s, dt) => {
        const tx = P.x, ty = P.y - 16, a = Math.atan2(ty - s.y, tx - s.x), sp = s.t < 0.5 ? 60 : 118 + (this.phase === 2 ? 20 : 0);
        s.vx = approach(s.vx, Math.cos(a) * sp, 170 * dt); s.vy = approach(s.vy, Math.sin(a) * sp, 170 * dt);
        if (!self.alive) s.life = Math.min(s.life, 0.3);
        addLight(s.x, s.y, 56, '255,200,90', 1);
        if (Math.random() < 0.6) particles.push({ x: s.x + rand(-6, 6), y: s.y + rand(-6, 6), vx: -s.vx * 0.2, vy: -s.vy * 0.2, life: 0.4, kind: Math.random() < 0.5 ? 'fire' : 'sun' });
      },
      draw: s => { const a = s.life < 0.5 ? s.life * 2 : 1;
        if (sh.ok) { const t = sh.tag(Object.keys(sh.tags)[0]), n = t.to - t.from + 1; drawSprite(sh, t.from + Math.floor(s.t * 14) % n, s.x, s.y, 1, { center: true, alpha: a }); }
        else { g.fillStyle = `rgba(255,220,120,${a})`; g.beginPath(); g.arc(s.x, s.y, 8, 0, 6.3); g.fill(); } } });
  }
  sinkZones() {
    sfx.crumble(); shake = 4; this.sinkCd = 8;
    const xs = [P.x, P.x + rand(70, 110) * (Math.random() < 0.5 ? -1 : 1)];
    xs.forEach((x, k) => duZone(clamp(x, this.L, this.R), this.floor, 1, 4.5, 0.7 + k * 0.25));
  }
  // ---- phase 2: into the sand, out of the storm
  vanishUpdate(dt) {
    const an = this.anim;
    this.facePlayer();
    if (Math.random() < 0.9) duSand(this.x + rand(-16, 16), this.floor, 2, 8, 90);
    if (an.done || !this.hasTag('vanish')) {
      this.state = 'buried'; this.t = rand(0.9, 1.3); this.hidden = true; this.eyeX = this.x;
      sfx.crumble(); shake = Math.max(shake, 3);
    }
  }
  buriedUpdate(dt) {
    this.commonUpdate(dt); this.anim.update(dt); this.t -= dt;
    const want = clamp(P.x - P.face * 42, this.L, this.R);
    if (!this.rise) {
      this.x = approach(this.x, want, 200 * dt);
      if (Math.random() < 0.5) particles.push({ x: this.x + rand(-10, 10), y: this.floor - 1, vx: rand(-20, 20), vy: -rand(20, 60), g: 300, life: 0.5, kind: 'sand' });
      if (this.t <= 0) { this.rise = 0.55; this.facePlayer(); spawnFx('telegraph', this.x, this.floor - 40, this.face); sfx.glint(); sfx.howl(); }
    } else {
      this.rise -= dt; if (Math.random() < 0.9) duSand(this.x + rand(-12, 12), this.floor, 2, 8, 130);
      if (this.rise <= 0) {
        this.rise = 0; this.hidden = false; this.facePlayer(); this.atk = 'emerge'; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {};
        this.setS('attack', 'emerge', false); const wins = metaWindows(this.sh, 'emerge'); this.firstActive = wins.length ? wins[0].active[0] : 3;
        duSand(this.x, this.floor, 22, 16, 160); shake = 6; sfx.boom();
      }
    }
    this.ambient(dt);
  }
  stagger() { super.stagger(); const t = this.t; this.setS('stagger', 'stagger', false); this.t = t; }
  die() { super.die(); this.hidden = false; this.setS('dead', this.hasTag('death') ? 'death' : 'stagger', false); }
  hurtbox() { if (this.hidden || this.state === 'buried' || this.state === 'dormant') return null; if (this.state === 'attack' && this.atk === 'vanish' && this.anim.i >= Math.max(2, this.anim.n - 3)) return null; return super.hurtbox(); }
  canStagger() { return !this.hidden && this.state !== 'buried' && !(this.state === 'attack' && ['vanish', 'summon'].includes(this.atk)); }
  p2Storm() {
    flashScreen = 0.5; shake = 8; sfx.howl(); sfx.roar();
    DU.storm = { boss: true, on: true, t: 0, dir: this.face > 0 ? -1 : 1, k: 0 };
    AREAS.dunes.ambient = 0.8; this.stormAmb = true;
    toast('The sandstorm swallows the sanctum', 3);
    for (const e of enemies) if (e.alive && e.type === 'du_soldier') { e.die({ dir: 0 }); duSand(e.x, e.y - 10, 12); }
  }
  pAmbient(dt) {
    const p2 = this.phase === 2 && this.alive;
    // in the storm he is hard to see -- more so when idle, fully when he commits to a blow (so every hit stays readable)
    const committing = this.state === 'attack' || this.state === 'stagger' || this.state === 'dead';
    this.vis = approach(this.vis, p2 && !committing ? 0.28 : 1, dt * (committing ? 4 : 1.4));
    this.eye = approach(this.eye, this.state === 'dormant' ? 0 : p2 ? 1 : 0.55, dt * 2);
    const ep = this.eyePt();
    if (this.state !== 'dormant' && !(this.state === 'buried' && !this.rise)) addLight(ep.x, ep.y, 20 + this.eye * 30, '255,170,60', 0.9 * this.eye);
    if (this.state === 'buried') addLight(this.x, this.floor - 4, 24, '255,170,60', 0.9);
    addLight(this.x, this.y - 70, p2 ? 50 : 70, '255,210,130', p2 ? 0.35 : 0.5);
    if (Math.random() < (p2 ? 0.5 : 0.25) && this.state !== 'buried' && this.state !== 'dormant') particles.push({ x: this.x - this.face * rand(4, 24), y: this.y - rand(10, 80), vx: -this.face * rand(10, 40) + (DU.storm ? DU.storm.dir * 60 * DU.storm.k : 0), vy: rand(-8, 12), life: rand(0.6, 1.2), kind: Math.random() < 0.6 ? 'sand' : 'sandd' });
    if (DU.storm && DU.storm.boss && !this.alive) DU.storm.on = false;
  }
  eyePt() { const e = this.meta.eye && this.meta.eye[this.anim.tag]; const pt = e ? e[Math.min(this.anim.i, e.length - 1)] : null; return pt ? metaPoint(this.sh, this, pt) : { x: this.x + this.face * 6, y: this.y - 92 }; }
  pDeath() {
    victoryBanner = { text: this.victory, t: 0 }; duClearZones(); DU.shots = []; DU.haz = [];
    if (DU.storm) DU.storm.on = false; AREAS.dunes.ambient = DU_AMB.DU8;
    for (const e of enemies) if (e.alive && e.type === 'du_soldier') { e.die({ dir: 0 }); duSand(e.x, e.y - 10, 12); }
    setTimeout(() => toast('“…so this is the dusk.”', 4), 2600);
  }
  draw() {
    if (this.state === 'buried') {   // under the storm-sand: a swell and the one amber eye
      const X = Math.round(this.x), Y = Math.round(this.floor), k = this.rise ? 1 + (0.55 - this.rise) * 1.5 : 1;
      g.fillStyle = 'rgba(180,136,74,0.9)'; g.beginPath(); g.ellipse(X, Y, 20 * k, 4 * k, 0, Math.PI, 0); g.fill();
      g.fillStyle = '#ffb040'; g.fillRect(X - 2, Y - Math.round(4 * k) - 2, 4, 1); g.fillStyle = '#fff0b0'; g.fillRect(X - 1, Y - Math.round(4 * k) - 2, 2, 1);
      return;
    }
    if (!this.sh.has(this.anim.tag) && this.state !== 'dormant') this.setS(this.state, 'idle', true);
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' } : {};
    if (!this.sh.ok) { g.fillStyle = `rgba(200,160,80,${this.vis})`; g.fillRect(Math.round(this.x - 14), Math.round(this.y - 100), 28, 100); }
    else drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, { ...opt, alpha: (opt.alpha ?? 1) * this.vis });
    if (this.state === 'dormant' && this.cutEye === undefined) return;
    const ep = this.eyePt(), e = this.cutEye ?? this.eye;
    if (e > 0.05) { g.fillStyle = `rgba(255,190,80,${e})`; g.fillRect(Math.round(ep.x) - 2, Math.round(ep.y), 4, 1); g.fillStyle = `rgba(255,250,210,${e})`; g.fillRect(Math.round(ep.x) - (this.face > 0 ? 0 : 1), Math.round(ep.y), 2, 1); }
    const B = this.beam;
    if (this.state === 'attack' && this.atk === 'beam' && B) {
      if (B.warn) {   // aim line: where the sweep will start
        const dx = Math.cos(B.a0) * this.face, dy = Math.sin(B.a0); g.save(); g.globalAlpha = 0.3 + 0.3 * Math.sin(time * 30);
        for (let d = 8; d < 260; d += 7) { g.fillStyle = d % 14 < 7 ? '#fff4c8' : '#e6b85c'; g.fillRect(Math.round(B.x + dx * d), Math.round(B.y + dy * d), 2, 1); }
        g.restore();
      } else if (B.on && B.L) duDrawRay(B.x, B.y, Math.atan2(Math.sin(B.a), Math.cos(B.a) * this.face), B.L);
    }
  }
}
function duDrawRay(x, y, a, L) {   // the sceptre beam: layered light along a line, flaring where it strikes the sand
  const dx = Math.cos(a), dy = Math.sin(a), fl = 1 + Math.sin(time * 60) * 0.15;
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const [w, col] of [[9 * fl, 'rgba(255,140,40,0.28)'], [6 * fl, 'rgba(255,196,90,0.5)'], [3, 'rgba(255,246,214,0.95)']]) {
    g.strokeStyle = col; g.lineWidth = w; g.beginPath(); g.moveTo(x, y); g.lineTo(x + dx * L, y + dy * L); g.stroke();
  }
  g.restore();
  g.fillStyle = '#fffbe8'; g.beginPath(); g.arc(x + dx * L, y + dy * L, 5 + Math.sin(time * 40) * 1.5, 0, 6.3); g.fill();
  g.fillStyle = 'rgba(255,220,140,0.9)'; g.beginPath(); g.arc(x, y, 4, 0, 6.3); g.fill();
}
BOSS_SPAWN.pharaoh = (cx, fy) => new DuPharaoh(cx, fy);
BOSS_CUTS.pharaoh = b => [
  act(() => { b.face = -1; b.cutEye = 0; b.setS('dormant', b.hasTag('rise') ? 'rise' : 'idle', false); b.anim.i = 0; b.anim.t = 0; b.anim.done = false; b.anim.speed = 0.0001; b.state = 'dormant'; }),
  { pan: { x: b.x - 40, y: b.floor - 70 }, dur: 1.6 },
  say('', 'Beneath the sand, a king who would not be buried.'),
  { dur: 0.9, tween: (dt, k) => { b.cutEye = k; if (Math.random() < 0.4) duSand(b.x + rand(-20, 20), b.floor, 1, 10, 50); } },
  act(() => { sfx.glint(); sfx.howl(); flashScreen = 0.2; b.anim.speed = 1; }),
  { dur: 1.6, tween: (dt, k) => { if (Math.random() < 0.8) particles.push({ x: b.x + rand(-26, 26), y: b.y - rand(10, 100), vx: rand(-30, 10), vy: -rand(10, 40), life: rand(0.6, 1.2), kind: Math.random() < 0.5 ? 'sand' : 'sun' }); shake = Math.max(shake, 1); } },
  say('The Veiled Pharaoh', 'Kneel. The sun has set on every kingdom but mine.'),
  act(() => { b.setS('intro', b.hasTag('summon') ? 'summon' : 'idle', false); b.state = 'dormant'; sfx.roar(); shake = 8; flashScreen = 0.4; duSand(b.x, b.floor, 30, 40, 140); }), wait(1.2),
  { do: () => { b.cutEye = undefined; b.setS('idle', 'idle'); b.facePlayer(); }, always: true },
];
PHASE2_LINES.pharaoh = ['The Veiled Pharaoh', 'Then let the desert take the light.'];

// ================================================================== boss-room housekeeping + HUD
HOOKS.update.push(dt => {
  if (!room || room.id !== 'DU8' || !boss || boss.kind !== 'pharaoh') return;
  if (boss.phase === 2 && boss.alive && DU.storm && DU.storm.boss) AREAS.dunes.ambient = approach(AREAS.dunes.ambient, 0.8, dt * 0.5);
});

// ================================================================== debug / test hooks
if (typeof window !== 'undefined' && window.__game) window.__game.du = {
  get DU() { return DU; }, slopeY: x => { const h = duSlopeY(room, x); return h && h.y; }, inQs: () => duInQs(P),
  storm(on = true) { if (DU.storm) { DU.storm.st = on ? 'storm' : 'calm'; DU.storm.t = on ? 6 : 9; DU.storm.k = on ? 1 : 0; } },
  zone: (x, life = 4) => duZone(x, boss ? boss.floor : P.y, 1, life, 0.05),
};
