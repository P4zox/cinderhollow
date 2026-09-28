// ------------------------------------------------------------------ world: rooms, tiles, collision, camera, lighting
const T_EMPTY = 0, T_SOLID = 1, T_PLAT = 2, T_SPIKE = 3, T_SPIKE_D = 4, T_BREAK = 5, T_WATER = 6, T_CRACK = 7;
const ROOM_BY = {}; for (const r of ROOMS) ROOM_BY[r.id] = r;
let room = null, cam = { x: 0, y: 0 }, fade = 0, fadeDir = 0, pendingRoom = null;
let props = [], enemies = [], projectiles = [], lights = [];

function roomAtGlobal(gx, gy) {   // global tile coords
  for (const r of ROOMS) if (gx >= r.gx && gx < r.gx + r.w && gy >= r.gy && gy < r.gy + r.h) return r;
  return null;
}
function charAt(def, x, y) { return def.map[y][x]; }
// ---- tile extensions (region files register new tile chars; ids 8+ — see docs/EXPANSION_CONTRACT.md)
const TILE_EXT = {}, TILE_DRAW = {}, SOLID_EXT = new Set(), TILE_BG = {};
function registerTile(ch, t, o = {}) { TILE_EXT[ch] = t; if (o.solid) SOLID_EXT.add(t); if (o.draw) TILE_DRAW[t] = o.draw; if (o.back) TILE_BG[t] = true; }
function cellType(ch) {
  switch (ch) {
    case '#': return T_SOLID; case '=': return T_PLAT; case '^': return T_SPIKE; case 'v': return T_SPIKE_D; case 'B': return T_BREAK; case '~': return T_WATER; case 'Y': return T_CRACK;
    default: return TILE_EXT[ch] ?? T_EMPTY;
  }
}
function brokenKey(def, x, y) { return `brk:${def.id}:${x},${y}`; }

function buildRoom(def) {
  const R = { def, id: def.id, w: def.w, h: def.h, pw: def.w * TILE, ph: def.h * TILE, grid: new Uint8Array(def.w * def.h), dyn: [] };
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    let t = cellType(charAt(def, x, y));
    if ((t === T_BREAK || t === T_CRACK) && SAVE.flags[brokenKey(def, x, y)]) t = T_EMPTY;
    R.grid[y * def.w + x] = t;
  }
  R.water = [];
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) if (R.grid[y * def.w + x] === T_WATER) R.water.push([x, y, y === 0 || R.grid[(y - 1) * def.w + x] !== T_WATER]);
  renderRoomLayers(R);
  return R;
}
// out-of-room cells: open only if a neighbouring room has open space there
function tileAt(tx, ty) { return tileAtR(room, tx, ty); }
function tileAtR(R, tx, ty) {
  if (tx >= 0 && ty >= 0 && tx < R.w && ty < R.h) return R.grid[ty * R.w + tx];
  const n = roomAtGlobal(R.def.gx + tx, R.def.gy + ty);
  if (!n) return (ty < 0 && !R.def.indoor) ? T_EMPTY : T_SOLID;
  const lx = R.def.gx + tx - n.gx, ly = R.def.gy + ty - n.gy, t = cellType(charAt(n, lx, ly));
  if (t === T_BREAK || t === T_CRACK) return SAVE.flags[brokenKey(n, lx, ly)] ? T_EMPTY : T_SOLID;   // a wall already broken from its own side is open
  return t;
}
const isSolidT = t => t === T_SOLID || t === T_BREAK || t === T_CRACK || SOLID_EXT.has(t);
function solidAtPx(x, y) {
  const t = tileAt(Math.floor(x / TILE), Math.floor(y / TILE));
  if (isSolidT(t)) return true;
  for (const d of room.dyn) if (d.on() && x >= d.x0 && x < d.x1 && y >= d.y0 && y < d.y1) return true;
  return false;
}

// ---- body physics. b: {x, y (feet), w, h, vx, vy, ground}
function moveBody(b, dt, opt = {}) {
  b.hitWall = 0; b.hitCeil = false;
  const wasGround = b.ground;
  let dx = b.vx * dt;
  const steps = Math.ceil(Math.abs(dx) / 6) || 1;
  for (let s = 0; s < steps; s++) {
    const nx = b.x + dx / steps, side = dx > 0 ? nx + b.w / 2 : nx - b.w / 2;
    let blocked = false;
    for (let yy = b.y - b.h + 1; yy <= b.y - 1; yy += Math.min(8, b.h - 2)) if (solidAtPx(side, yy)) blocked = true;
    if (!blocked && solidAtPx(side, b.y - 1)) blocked = true;
    if (blocked && b.assist && !b.ground && b.vy > -60) {
      // ledge assist: if only the bottom few pixels clip the ledge, pop up onto it
      let low = true;
      for (let yy = b.y - b.h + 1; yy <= b.y - 6; yy += 4) if (solidAtPx(side, yy)) low = false;
      if (low && !solidAtPx(side, b.y - 6)) {
        const top = Math.floor((b.y - 1) / TILE) * TILE;
        if (b.y - top <= 6 && !solidAtPx(nx, top - b.h + 1)) { b.y = top; b.vy = Math.min(b.vy, 0); blocked = false; }
      }
    }
    if (blocked) {
      if (dx > 0) b.x = Math.floor(side / TILE) * TILE - b.w / 2 - 0.01; else b.x = (Math.floor(side / TILE) + 1) * TILE + b.w / 2 + 0.01;
      // snap to dynamic solids too
      for (const d of room.dyn) if (d.on() && side >= d.x0 && side < d.x1) b.x = dx > 0 ? d.x0 - b.w / 2 - 0.01 : d.x1 + b.w / 2 + 0.01;
      b.hitWall = sign(dx); b.vx = 0; break;
    }
    b.x = nx;
  }
  const dy = b.vy * dt;
  const stepsY = Math.ceil(Math.abs(dy) / 6) || 1;
  b.ground = false;
  for (let s = 0; s < stepsY; s++) {
    const prevY = b.y, ny = b.y + dy / stepsY;
    if (dy >= 0) {
      let land = null;
      for (const xx of [b.x - b.w / 2 + 1, b.x, b.x + b.w / 2 - 1]) {
        const tx = Math.floor(xx / TILE), ty = Math.floor(ny / TILE), t = tileAt(tx, ty);
        const top = ty * TILE;
        const lt = isSolidT(t) ? top : dynTopAt(xx, ny, prevY);   // dyn solids land on their own top (kit movers sit between tile rows)
        if (lt !== null) land = land === null ? lt : Math.min(land, lt);
        else if (t === T_PLAT && !(b.drop > 0) && prevY <= top + 0.5) land = land === null ? top : Math.min(land, top);
      }
      if (land !== null) { b.y = land; b.vy = 0; b.ground = true; break; }
      b.y = ny;
    } else {
      let bonk = false;
      for (const xx of [b.x - b.w / 2 + 1, b.x, b.x + b.w / 2 - 1]) if (solidAtPx(xx, ny - b.h)) bonk = true;
      if (bonk && b.assist) {   // corner correction: slide around a ceiling corner clipped by a few pixels
        for (const nudge of [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]) {
          let clear = true;
          for (const xx of [b.x + nudge - b.w / 2 + 1, b.x + nudge, b.x + nudge + b.w / 2 - 1]) if (solidAtPx(xx, ny - b.h) || solidAtPx(xx, ny - b.h / 2)) clear = false;
          if (clear) { b.x += nudge; bonk = false; break; }
        }
      }
      if (bonk) { b.y = ceilAt(b, ny - b.h, prevY - b.h) + b.h; b.vy = 0; b.hitCeil = true; break; }
      b.y = ny;
    }
  }
  // stay grounded when standing still on a surface
  if (!b.ground && b.vy >= 0 && dy === 0) b.ground = groundBelow(b);
  b.landed = !wasGround && b.ground;
}
function solidDynAt(x, y) { for (const d of room.dyn) if (d.on() && x >= d.x0 && x < d.x1 && y >= d.y0 && y < d.y1) return true; return false; }
// landing height on a dyn solid at (x, y): its own top when the body came from above, else the old tile-row snap
function dynTopAt(x, y, prevY) { let r = null; for (const d of room.dyn) if (d.on() && x >= d.x0 && x < d.x1 && y >= d.y0 && y < d.y1) { const t = d.y0 >= prevY - 1 ? d.y0 : Math.floor(y / TILE) * TILE; r = r === null ? t : Math.min(r, t); } return r; }
// head bump: below the tile row, or flush under a dyn solid's underside when the head came from below it
function ceilAt(b, hy, prevHy) {
  let r = (Math.floor(hy / TILE) + 1) * TILE, dynOnly = true;
  for (const xx of [b.x - b.w / 2 + 1, b.x, b.x + b.w / 2 - 1]) { if (isSolidT(tileAt(Math.floor(xx / TILE), Math.floor(hy / TILE)))) dynOnly = false; }
  if (!dynOnly) return r;
  let d1 = null; for (const d of room.dyn) if (d.on() && hy >= d.y0 && hy < d.y1 && d.y1 <= prevHy + 1 && [b.x - b.w / 2 + 1, b.x, b.x + b.w / 2 - 1].some(xx => xx >= d.x0 && xx < d.x1)) d1 = Math.max(d1 ?? -1e9, d.y1);
  return d1 ?? r;
}
function groundBelow(b, off = 1) {
  for (const xx of [b.x - b.w / 2 + 1, b.x + b.w / 2 - 1]) {
    const t = tileAt(Math.floor(xx / TILE), Math.floor((b.y + off) / TILE));
    if (isSolidT(t) || (t === T_PLAT && Math.abs(b.y - Math.floor((b.y + off) / TILE) * TILE) < 1)) return true;
    if (solidDynAt(xx, b.y + off)) return true;
  }
  return false;
}
function wallAt(b, dir) {   // is there a solid wall touching the body's side?
  const x = dir > 0 ? b.x + b.w / 2 + 1 : b.x - b.w / 2 - 1;
  return solidAtPx(x, b.y - b.h * 0.3) && solidAtPx(x, b.y - b.h * 0.8);
}
function ledgeAhead(b, dir) {  // true if there's floor ahead for walkers
  const x = b.x + dir * (b.w / 2 + 3);
  const t = tileAt(Math.floor(x / TILE), Math.floor((b.y + 2) / TILE));
  return isSolidT(t) || t === T_PLAT;
}
function spikeHit(b) {
  const r = rect(b.x - b.w / 2 + 2, b.y - b.h + 2, b.x + b.w / 2 - 2, b.y - 1);
  for (let ty = Math.floor(r.y0 / TILE); ty <= Math.floor(r.y1 / TILE); ty++)
    for (let tx = Math.floor(r.x0 / TILE); tx <= Math.floor(r.x1 / TILE); tx++) {
      const t = tileAt(tx, ty);
      if (t === T_SPIKE && r.y1 > ty * TILE + 8) return true;
      if (t === T_SPIKE_D && r.y0 < ty * TILE + 8) return true;
    }
  return false;
}
function lineOfSight(x0, y0, x1, y1) {
  const n = Math.ceil(Math.hypot(x1 - x0, y1 - y0) / 8);
  for (let i = 1; i < n; i++) if (solidAtPx(lerp(x0, x1, i / n), lerp(y0, y1, i / n))) return false;
  return true;
}

// ---- room layers (prerendered): back = bg walls + decor, front = terrain
function tileSheet(biome) { return sheet('tiles_' + biome); }
function drawTile(ctx, sh, idx, x, y, alpha = 1) {
  if (sh.ok && sh.frames[idx]) {
    const f = sh.frames[idx]; ctx.globalAlpha = alpha;
    ctx.drawImage(sh.img, f.x, f.y, 16, 16, x, y, 16, 16); ctx.globalAlpha = 1; return;
  }
  // fallback colours if the tileset is missing
  const col = idx < 32 ? '#3a3548' : idx < 36 ? '#5a4a3a' : idx < 38 ? '#b0b0c0' : idx < 42 ? '#15131c' : null;
  if (!col) return;
  ctx.globalAlpha = alpha; ctx.fillStyle = col;
  if (idx >= 32 && idx < 36) ctx.fillRect(x, y, 16, 5); else ctx.fillRect(x, y, 16, 16);
  ctx.globalAlpha = 1;
}
function renderRoomLayers(R) {
  const def = R.def, sh = tileSheet(def.biome);
  const mk = () => { const c = document.createElement('canvas'); c.width = R.pw; c.height = R.ph; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
  const [bc, bx] = mk(), [fc, fx2] = mk();
  const air = (x, y) => !isSolidT(tileAtR(R, x, y));
  for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
    const t = R.grid[y * R.w + x], ch = charAt(def, x, y), px = x * TILE, py = y * TILE;
    if (!isSolidT(t) && def.indoor) {
      // background walls frame the play space; they fade out towards open space so the parallax shows through
      let d = 9;
      for (let yy = -3; yy <= 3; yy++) for (let xx = -3; xx <= 3; xx++) if (isSolidT(tileAtR(R, x + xx, y + yy))) d = Math.min(d, Math.max(Math.abs(xx), Math.abs(yy)));
      const a = d <= 1 ? 1 : d === 2 ? 0.8 : d === 3 ? 0.5 : 0.28;
      drawTile(bx, sh, 38 + Math.floor(hash2(x, y) * 4), px, py, a);
    }
    if (t === T_SOLID) {
      const m = (air(x, y - 1) ? 1 : 0) | (air(x + 1, y) ? 2 : 0) | (air(x, y + 1) ? 4 : 0) | (air(x - 1, y) ? 8 : 0);
      drawTile(fx2, sh, m + (hash2(x + 7, y * 3) < 0.28 ? 16 : 0), px, py);
      if ((m & 1) && hash2(x * 5, y) < 0.3) drawTile(fx2, sh, 47, px, py - 16);
    } else if (t === T_BREAK) drawTile(fx2, sh, 46, px, py);
    else if (t === T_CRACK) {   // slam-only cracked floor: breakable tile plus glowing ember fissures
      drawTile(fx2, sh, 46, px, py);
      fx2.fillStyle = 'rgba(20,10,8,0.9)'; fx2.fillRect(px + 3, py + 5, 10, 1); fx2.fillRect(px + 7, py + 2, 1, 9); fx2.fillRect(px + 9, py + 9, 5, 1);
      fx2.fillStyle = 'rgba(255,140,60,0.8)'; fx2.fillRect(px + 7, py + 5, 1, 1); fx2.fillRect(px + 11, py + 9, 1, 1);
    }
    else if (t === T_PLAT) {
      const L = charAt(def, x - 1, y) === '=' || false, Rr = x + 1 < R.w && charAt(def, x + 1, y) === '=';
      drawTile(fx2, sh, L && Rr ? 33 : Rr ? 32 : L ? 34 : 35, px, py);
    } else if (t === T_SPIKE) drawTile(fx2, sh, 36, px, py);
    else if (t === T_SPIKE_D) drawTile(fx2, sh, 37, px, py);
    else if (TILE_DRAW[t]) TILE_DRAW[t](fx2, sh, px, py, x, y, R, bx);
    const deco = { x: 42, r: 43, k: 44, b: 45 }[ch];
    if (deco !== undefined) drawTile(bx, sh, deco, px, py);
  }
  R.back = bc; R.front = fc;
}
function charAtSafe(def, x, y) { return (x < 0 || y < 0 || x >= def.w || y >= def.h) ? '#' : def.map[y][x]; }

// ---- parallax + lighting
function drawParallax() {
  const b = room.def.biome, far = sheet(`bg_${b}_far`), mid = sheet(`bg_${b}_mid`);
  const A = AREAS[b];
  g.fillStyle = A.tint; g.fillRect(0, 0, W, H);
  const tAnim = Math.floor(time * 6);
  const layer = (sh, fac, vfac) => {
    if (!sh.ok) return;
    const t = sh.tag('loop'), f = sh.frames[t.from + (tAnim % (t.to - t.from + 1))];
    const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
    for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h);
  };
  layer(far, 0.08, 0.02);
  layer(mid, 0.3, 0.08);
}
// o (optional): { flicker: true (lanterns, torches…), shadow: false (skip the tile-shadow test), height: px in front of the wall }
function addLight(x, y, r, color = '255,190,110', k = 1, o) { lights.push({ x, y, r, color, k, o }); }
// Classic lighting (shaders off, or Lighting = Classic): a darkness layer with soft holes. Dynamic lighting: 41_light.js
function renderLighting() {
  const A = AREAS[room.def.biome];
  let amb = typeof darkT !== 'undefined' && darkT > 0 ? Math.min(0.97, A.ambient + 0.4 * Math.min(1, darkT)) : A.ambient;
  amb = Math.min(0.97, amb * [1.15, 1, 0.72][SETTINGS.bright ?? 1]);   // Settings › Graphics › Brightness
  lg.globalCompositeOperation = 'source-over';
  lg.clearRect(0, 0, W, H);
  lg.fillStyle = `rgba(4,3,8,${amb})`; lg.fillRect(0, 0, W, H);
  lg.globalCompositeOperation = 'destination-out';
  for (const L of lights) {
    const x = L.x - cam.x, y = L.y - cam.y;
    if (x < -L.r || x > W + L.r || y < -L.r || y > H + L.r) continue;
    const gr = lg.createRadialGradient(x, y, 0, x, y, L.r);
    gr.addColorStop(0, `rgba(0,0,0,${Math.min(1, L.k)})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
    lg.fillStyle = gr; lg.fillRect(x - L.r, y - L.r, L.r * 2, L.r * 2);
  }
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(lightC, 0, 0);
  // warm additive glow
  g.globalCompositeOperation = 'lighter';
  for (const L of lights) {
    const x = L.x - cam.x, y = L.y - cam.y, r = L.r * 0.6;
    if (x < -r || x > W + r || y < -r || y > H + r) continue;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(${L.color},${0.16 * L.k})`); gr.addColorStop(1, `rgba(${L.color},0)`);
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  g.globalCompositeOperation = 'source-over';
}

// ---- camera
function updateCamera(dt, snap = false) {
  const lookT = clamp(P.vx * 0.3, -36, 36) + P.face * 20;
  cam.look = snap || cam.look === undefined ? lookT : lerp(cam.look, lookT, Math.min(1, dt * 2.6));
  const look = cam.look;
  let tx = P.x + look - W / 2, ty = P.y - 30 - H / 2 + (held.has('down') && P.ground && Math.abs(P.vx) < 5 ? 50 : 0) + (held.has('up') && P.ground && Math.abs(P.vx) < 5 ? -50 : 0);
  if (boss && boss.active && boss.camX !== undefined) tx = lerp(tx, boss.camX - W / 2, 0.35);
  const maxX = room.pw - W, maxY = room.ph - H;
  tx = maxX < 0 ? maxX / 2 : clamp(tx, 0, maxX);
  ty = maxY < 0 ? maxY / 2 : clamp(ty, 0, maxY);
  if (snap) { cam.x = tx; cam.y = ty; return; }
  cam.x += (tx - cam.x) * Math.min(1, dt * 7);
  cam.y += (ty - cam.y) * Math.min(1, dt * (P.vy > 200 ? 12 : 5));
}

function drawWater() {
  if (!room.water.length) return;
  for (const [x, y, surf] of room.water) {
    const px = x * TILE, py = y * TILE;
    g.fillStyle = 'rgba(40,78,34,0.72)'; g.fillRect(px, py, TILE, TILE);
    if (surf) {
      for (let i = 0; i < TILE; i += 2) { const w = Math.sin(time * 3 + (px + i) * 0.35) * 1.2; g.fillStyle = 'rgba(150,200,90,0.8)'; g.fillRect(px + i, Math.round(py + 1 + w), 2, 1); }
      if (Math.random() < 0.012) particles.push({ x: px + rand(2, 14), y: py + 2, vx: 0, vy: -rand(4, 12), life: 0.8, kind: 'spore' });
      addLight(px + 8, py + 4, 18, '140,210,90', 0.25);
    }
  }
}
