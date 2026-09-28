// ------------------------------------------------------------------ THE HOARFROST AQUEDUCT (agent H)
// Biome, ice floors ('_'), freezing water (':'), frost buildup + frostbite, icicles (','), frozen waterfalls,
// enemies (frost wraith, ice golem, under-ice lurker), the Ice Golem Warden (mini-boss) and the Frostbound Twins.
Object.assign(AREAS, { hoarfrost: { name: 'The Hoarfrost Aqueduct', ambient: 0.42, amb: 'petal', tint: '#070a12' } });
Object.assign(SCALES, { hoarfrost: [0, 2, 3, 7, 8] });
Object.assign(ROOTS, { hoarfrost: 41.2 });

const T_ICE = 10, T_FWATER = 11;
const HF = { frost: 0, frostT: 0, slowT: 0, biteFlash: 0, shots: [], water: [], icicles: 0 };
const hfIn = () => room && room.def.biome === 'hoarfrost';
const hfSfx = {
  ice: () => { tone(2400, 0.12, 0.05, 'triangle', 0.6); noise(0.12, 5000, 2, 0.12, 'highpass'); },
  crack: () => { noise(0.25, 2600, 1.5, 0.25, 'bandpass', 0.5); tone(1300, 0.1, 0.05, 'square', 0.4); },
  shatter: () => { noise(0.5, 3200, 0.8, 0.4, 'highpass', 0.4); [2093, 2637, 3136].forEach((f, i) => tone(f, 0.25, 0.04, 'triangle', 0.8, i * 0.03)); },
  breath: () => noise(0.5, 1800, 0.6, 0.18, 'bandpass', 0.5),
  bubble: () => tone(rand(300, 500), 0.08, 0.04, 'sine', 1.6),
  splash: () => { noise(0.35, 900, 0.6, 0.35, 'lowpass', 0.5); noise(0.2, 3000, 1, 0.12, 'highpass'); },
  bite: () => { tone(1900, 0.4, 0.1, 'triangle', 0.5); noise(0.4, 4000, 1, 0.3, 'highpass', 0.3); tone(90, 0.3, 0.2, 'sine', 0.5); },
};

// ================================================================== tiles
function hfMask(R, x, y) {
  const air = (xx, yy) => !isSolidT(tileAtR(R, xx, yy));
  return (air(x, y - 1) ? 1 : 0) | (air(x + 1, y) ? 2 : 0) | (air(x, y + 1) ? 4 : 0) | (air(x - 1, y) ? 8 : 0);
}
registerTile('_', T_ICE, { solid: true, draw(ctx, sh, px, py, x, y, R) {
  const m = hfMask(R, x, y);
  if (sh.ok && sh.frames.length > 63) { drawTile(ctx, sh, 48 + m, px, py); return; }
  drawTile(ctx, sh, m, px, py);
  if (m & 1) { ctx.fillStyle = '#cdeefa'; ctx.fillRect(px, py, 16, 2); ctx.fillStyle = '#6fa8c8'; ctx.fillRect(px, py + 2, 16, 2); ctx.fillStyle = '#f4feff'; ctx.fillRect(px + (x * 5) % 11, py, 3, 1); }
} });
registerTile(':', T_FWATER, { draw() {} });   // rendered translucent over the scene in the render hook

function hfOnIce(b) {
  for (const xx of [b.x - b.w / 2 + 1, b.x + b.w / 2 - 1]) if (tileAt(Math.floor(xx / TILE), Math.floor((b.y + 1) / TILE)) === T_ICE) return true;
  return false;
}
function hfInWater(b) { return tileAt(Math.floor(b.x / TILE), Math.floor((b.y - 4) / TILE)) === T_FWATER; }
function hfFloorAt(x, y) {   // first solid top at or below y (px)
  for (let ty = Math.floor(y / TILE); ty < room.h; ty++) if (isSolidT(tileAt(Math.floor(x / TILE), ty))) return ty * TILE;
  return y;
}

// ================================================================== frost buildup
function hfFrost(n) {
  if (n <= 0 || !P || P.state === 'dead' || charmOn('c_frostheart')) return;
  HF.frost = Math.min(100, HF.frost + n); HF.frostT = 1.4;
}
function hfFrostbite() {
  HF.frost = 0; HF.slowT = 3; HF.biteFlash = 1;
  const dmg = Math.round(D.maxHp * 0.25);
  P.hp = Math.max(0, P.hp - dmg); P.flash = 1; popup(P.x, P.y - 34, dmg, '#bfe8ff');
  hfSfx.bite(); shake = Math.max(shake, 5); hitstop = 0.08; flashScreen = 0.25;
  spawnFx(fxOr('hf_shatter', 'parry_flash'), P.x, P.y - 14, 1, null, { alpha: 0.9 });
  for (let i = 0; i < 24; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(4, 24), vx: rand(-90, 90), vy: -rand(20, 110), g: 260, life: rand(0.5, 1), kind: 'frost' });
  toast('Frostbite', 1.8);
  if (P.hp <= 0) killPlayer(0);
}
HOOKS.playerHurt.push((dmg, opt) => {
  const s = opt.src, f = opt.frost ?? (s && (s.hfFrost || (s.cfg && s.cfg.frost)));
  if (f) hfFrost(f);
  return dmg;
});
HOOKS.rest.push(() => { HF.frost = 0; HF.slowT = 0; });
HOOKS.death.push(() => { HF.frost = 0; HF.slowT = 0; HF.shots = []; });

// ================================================================== shots: frost/flame waves, breath, lances (own list: they carry frost)
function hfShot(o) { const s = Object.assign({ t: 0, life: 2, vx: 0, vy: 0, g: 0, w: 10, h: 10, dmg: 20, frost: 0, id: ++hazardId, face: 1 }, o); HF.shots.push(s); return s; }
function hfWave(x, floor, dir, kind, dmg, frost, spd = 160) {
  return hfShot({ kind, x, y: floor, vx: dir * spd, face: dir, life: 1.8, w: 14, h: kind === 'flwave' ? 18 : 14, dmg, frost, wave: true });
}
function updateHfShots(dt) {
  for (const s of HF.shots) {
    if (s.delay > 0) { s.delay -= dt; continue; }
    s.t += dt; s.life -= dt;
    s.vy += s.g * dt; s.x += s.vx * dt; s.y += s.vy * dt;
    if (s.wave) {
      if (solidAtPx(s.x + sign(s.vx) * 7, s.y - 5) || !solidAtPx(s.x, s.y + 2)) s.life = 0;
      if (Math.random() < 0.5) particles.push({ x: s.x + rand(-5, 5), y: s.y - rand(0, 8), vx: 0, vy: -rand(20, 60), life: 0.4, kind: s.kind === 'flwave' ? 'fire' : 'frost' });
      addLight(s.x, s.y - 8, 34, s.kind === 'flwave' ? '255,150,60' : '150,210,255', 0.7);
    } else {
      if (s.kind === 'breath') { s.vx *= Math.pow(0.35, dt); s.vy *= Math.pow(0.35, dt); if (Math.random() < 0.4) particles.push({ x: s.x + rand(-4, 4), y: s.y + rand(-4, 4), vx: s.vx * 0.3, vy: rand(-10, 10), life: 0.4, kind: 'frost' }); }
      else if (s.kind === 'lance' || s.kind === 'firebolt') { if (Math.random() < 0.5) particles.push({ x: s.x, y: s.y, vx: 0, vy: 0, life: 0.3, kind: s.kind === 'lance' ? 'frost' : 'fire' }); }
      if (!s.ghost && solidAtPx(s.x, s.y)) { s.life = 0; hfBurst(s.x, s.y, s.kind === 'firebolt' ? 'fire' : 'frost', 8); }
      addLight(s.x, s.y, s.kind === 'breath' ? 24 : 30, s.kind === 'firebolt' ? '255,150,60' : '160,215,255', 0.6);
    }
    if (s.life <= 0) continue;
    const r = rect(s.x - s.w / 2, s.wave ? s.y - s.h : s.y - s.h / 2, s.x + s.w / 2, s.wave ? s.y : s.y + s.h / 2);
    if (overlap(r, playerHurtbox()) && hurtPlayer(s.dmg * NGP.dmg, sign(s.vx) || (P.x < s.x ? -1 : 1), s.id, { frost: s.frost })) {
      if (!s.wave && s.kind !== 'breath') { s.life = 0; hfBurst(s.x, s.y, s.kind === 'firebolt' ? 'fire' : 'frost', 10); }
    }
  }
  HF.shots = HF.shots.filter(s => s.life > 0);
}
function hfBurst(x, y, kind, n) { for (let i = 0; i < n; i++) particles.push({ x, y, vx: rand(-70, 70), vy: rand(-90, 20), g: 260, life: rand(0.3, 0.6), kind }); }
function drawHfShots() {
  for (const s of HF.shots) {
    if (s.delay > 0) continue;
    const nm = { fwave: 'hf_frostwave', flwave: 'hf_flamewave', breath: 'hf_breath', lance: 'hf_lance', firebolt: 'hf_firebolt' }[s.kind];
    const sh = fxSheet(nm);
    if (sh.ok) {
      const t = sh.tag(Object.keys(sh.tags)[0]), n = t.to - t.from + 1, f = t.from + Math.floor(s.t * 12) % n;
      if (s.wave) drawSprite(sh, f, s.x, s.y, s.face, { bottom: true });
      else if (s.kind === 'breath') drawSprite(sh, f, s.x, s.y, s.face, { center: true, alpha: clamp(s.life * 3, 0, 0.9) });
      else drawRotated(sh, f, s.x, s.y, Math.atan2(s.vy, s.vx));
    } else {
      g.fillStyle = s.kind === 'flwave' || s.kind === 'firebolt' ? '#ff9a40' : '#bfe8ff';
      if (s.wave) g.fillRect(Math.round(s.x - 4), Math.round(s.y - 12), 8, 12); else g.fillRect(Math.round(s.x - 3), Math.round(s.y - 3), 6, 6);
    }
  }
}
// ice spike / fire pillar erupting from the floor (fx frames 0-2 = telegraph crack, 3-5 = damaging)
function hfSpike(x, floor, delay, dmg, frost, kind = 'ice') {
  if (x < 20 || x > room.pw - 20) return;
  const id = ++hazardId;
  hazards.push({ x, y: floor, w: 0, h: 0, dmg: 0, id, life: 4, delay, fx: null, active: () => false,
    onStart: h => { h.fx = spawnFx(fxOr(kind === 'ice' ? 'hf_icespike' : 'hf_pillar', 'root_spike', 'pillar'), h.x, floor, 1, null, { bottom: true }); if (!h.fx) h.life = 0; else (kind === 'ice' ? hfSfx.crack : sfx.fire)(); },
    update: h => {
      if (!h.fx || h.fx.anim.done) { h.life = 0; return; }
      const i = h.fx.anim.i;
      if (i < 3 && Math.random() < 0.5) particles.push({ x: h.x + rand(-6, 6), y: floor - 1, vx: 0, vy: -rand(10, 40), life: 0.4, kind: kind === 'ice' ? 'frost' : 'ember' });
      if (i === 3 && h.fx.anim.changed) { shake = Math.max(shake, 2.5); if (kind === 'ice') hfSfx.ice(); else sfx.pillar(); }
      if (i >= 3 && i <= 5) {
        addLight(h.x, floor - 30, 50, kind === 'ice' ? '170,220,255' : '255,160,70', 0.9);
        if (overlap(rect(h.x - 7, floor - 54, h.x + 7, floor), playerHurtbox())) hurtPlayer(BOSS_DMG * dmg * NGP.dmg, P.x < h.x ? -1 : 1, id, { frost });
      }
    } });
}

// ================================================================== icicles (',' = hangs from the cell above)
function makeIcicle(x, top, sensor) {
  const sh = sheet('hf_icicle');
  const p = { type: 'hf_icicle', x, y: top, top, face: 1, sh, st: 'idle', t: 0, vy: 0, sensor, regrow: !sensor, hitSet: new Set(), id: ++hazardId,
              anim: new Anim(sh, 'idle', false) };
  p.fall = (delay = 0.55) => { if (p.st !== 'idle') return; p.st = 'shake'; p.t = delay; p.anim.set('shake', true); hfSfx.crack(); };
  p.hurtbox = () => p.st === 'idle' ? rect(x - 4, top, x + 4, top + 24) : null;
  p.onHit = () => { if (p.st === 'idle') { p.fall(0.12); hfSfx.ice(); } };
  p.update = dt => {
    if (p.st === 'idle') {
      if (p.sensor && P.state !== 'dead' && Math.abs(P.x - x) < 20 && P.y > top + 20 && P.y - top < 200 && lineOfSight(x, top + 30, P.x, P.y - 20)) p.fall();
    } else if (p.st === 'shake') {
      p.t -= dt;
      if (Math.random() < 0.3) particles.push({ x: x + rand(-3, 3), y: top + rand(2, 10), vx: 0, vy: rand(20, 50), g: 300, life: 0.5, kind: 'frost' });
      if (p.t <= 0) { p.st = 'fall'; p.anim.set('fall', false); p.vy = 40; }
    } else if (p.st === 'fall') {
      p.vy = Math.min(p.vy + 950 * dt, 520); p.y += p.vy * dt;
      const tip = p.y + 26;
      if (overlap(rect(x - 4, p.y + 8, x + 4, tip), playerHurtbox()) && hurtPlayer(30 * NGP.dmg, P.x < x ? -1 : 1, p.id, { frost: 30 })) p.smash(tip);
      for (const t of targets()) {
        if (t.prop || p.hitSet.has(t)) continue;
        const hb = t.hurtbox(); if (hb && overlap(rect(x - 5, p.y + 6, x + 5, tip), hb)) { p.hitSet.add(t); t.hit({ dmg: 70, poise: 40, dir: 1, kind: 'env', x, y: tip, big: true }); }
      }
      if (p.st === 'fall' && (solidAtPx(x, tip) || p.y > room.ph)) p.smash(Math.floor(tip / TILE) * TILE);
    } else if (p.st === 'shatter') {
      if (p.anim.done) { if (p.regrow) { p.st = 'gone'; p.t = 9; } else p.taken = true; }
    } else if (p.st === 'gone') {
      p.t -= dt; if (p.t <= 0) { p.st = 'idle'; p.y = top; p.hitSet = new Set(); p.grow = 1; p.anim.set('idle', false); }
    }
    if (p.grow > 0) p.grow = Math.max(0, p.grow - dt);
    if (p.st !== 'gone' && p.st !== 'shatter') addLight(x, p.y + 12, 18, '170,220,255', 0.35);
  };
  p.smash = y => { p.st = 'shatter'; p.y = y; p.anim.set('shatter', false); hfSfx.shatter(); shake = Math.max(shake, 2); hfBurst(x, y - 4, 'frost', 12); };
  p.draw = () => {
    if (p.st === 'gone') return;
    const wob = p.st === 'shake' ? Math.round(Math.sin(time * 60) * 1) : 0, al = p.grow > 0 ? 1 - p.grow : 1;
    if (sh.ok) {
      if (p.st === 'shatter') drawSprite(sh, p.anim.frame, x, p.y, 1, { pivot: [Math.floor(sh.fw / 2), sh.fh] });
      else drawSprite(sh, p.anim.frame, x + wob, p.y, 1, { pivot: [Math.floor(sh.fw / 2), 0], alpha: al });
      return;
    }
    if (p.st === 'shatter') return;
    g.globalAlpha = al; g.fillStyle = '#9fd4ee';
    g.beginPath(); g.moveTo(x - 3 + wob, p.y); g.lineTo(x + 3 + wob, p.y); g.lineTo(x + wob, p.y + 24); g.fill();
    g.fillStyle = '#e8fbff'; g.fillRect(Math.round(x - 1 + wob), Math.round(p.y + 1), 1, 12); g.globalAlpha = 1;
  };
  return p;
}
ROOM_CHARS[','] = ({ cx, y, def }) => props.push(makeIcicle(cx, y * TILE, !def.boss));
function hfShakeIcicles(x, radius, delay = 0.55) {
  for (const p of props) if (p.type === 'hf_icicle' && p.st === 'idle' && Math.abs(p.x - x) < radius) p.fall(delay + rand(0, 0.25));
}

// ================================================================== frozen waterfalls (decor spawns)
SPAWNS.hf_fall = (s, c) => {
  const sh = sheet('hf_icefall'), top = s.y * TILE, h = (s.h || 6) * TILE;
  const p = { type: 'hf_fall', x: c.cx, y: top, face: 1, sh, anim: new Anim(sh, sh.has('mid') ? 'mid' : Object.keys(sh.tags)[0] || 'mid', true) };
  p.update = () => { if (Math.random() < 0.02) particles.push({ x: p.x + rand(-8, 8), y: top + rand(0, h), vx: 0, vy: rand(4, 12), life: 1, kind: 'frost' }); addLight(p.x, top + h / 2, 44, '150,200,240', 0.25); };
  p.draw = () => {
    if (!sh.ok) { g.fillStyle = 'rgba(170,215,240,0.25)'; g.fillRect(p.x - 10, top, 20, h); g.fillStyle = 'rgba(230,250,255,0.35)'; g.fillRect(p.x - 4, top, 2, h); return; }
    const fh = sh.fh, fw = sh.fw, piv = [Math.floor(fw / 2), 0];
    drawSprite(sh, sh.first('top'), p.x, top, 1, { pivot: piv, alpha: 0.85 });
    for (let yy = top + fh; yy < top + h - fh; yy += fh) drawSprite(sh, p.anim.frame, p.x, yy, 1, { pivot: piv, alpha: 0.85 });
    drawSprite(sh, sh.first('bottom'), p.x, top + h, 1, { pivot: [piv[0], fh], alpha: 0.85 });
  };
  props.unshift(p);
};

// ================================================================== room enter / update / render / hud
HOOKS.enter.push(def => {
  HF.shots = []; HF.water = [];
  if (def.biome !== 'hoarfrost') return;
  for (let y = 0; y < room.h; y++) for (let x = 0; x < room.w; x++) if (room.grid[y * room.w + x] === T_FWATER) HF.water.push([x, y, y === 0 || room.grid[(y - 1) * room.w + x] !== T_FWATER]);
  const H = SAVE.hints;
  if (def.id === 'HF1' && !SAVE.items.hook && !H.hf_gap) { H.hf_gap = 1; setTimeout(() => toast('The span has fallen. Golden rings hang beneath the old channel…', 4.5), 900); }
  if (def.id === 'HF2' && !H.hf_ice) { H.hf_ice = 1; setTimeout(() => toast('Ice underfoot — and the cistern water bites. Cold builds into frostbite.', 4.5), 900); }
});
HOOKS.update.push(dt => {
  if (!room || !P) return;
  HF.frostT -= dt;
  if (HF.frostT <= 0) HF.frost = Math.max(0, HF.frost - 22 * dt);
  HF.biteFlash = Math.max(0, HF.biteFlash - dt * 1.5);
  if (HF.frost >= 100 && P.state !== 'dead') hfFrostbite();
  if (HF.slowT > 0) {
    HF.slowT -= dt;
    if (P.state !== 'dead') { P.pushVx = (P.pushVx || 0) - P.vx * 0.45; if (Math.random() < 0.4) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(2, 26), vx: 0, vy: rand(5, 20), life: 0.6, kind: 'frost' }); }
  }
  if (!hfIn()) { if (HF.shots.length) HF.shots = []; return; }
  for (const p of particles) if (p.amb && p.kind === 'petal') p.kind = 'frost';
  if (P.state !== 'dead') {
    P.fric = P.ground && hfOnIce(P) ? 0.22 : 1;
    if (hfInWater(P)) {
      hfFrost(34 * dt); P.pushVx = (P.pushVx || 0) - P.vx * 0.3;
      if (Math.random() < 0.25) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(4, 20), vx: 0, vy: -rand(10, 25), life: 0.5, kind: 'frost' });
      if (!P.hfWet) { P.hfWet = true; hfSfx.splash(); hfBurst(P.x, P.y - 6, 'frost', 10); }
    } else P.hfWet = false;
    if (P.ground && P.fric < 1 && Math.abs(P.vx) > 40 && Math.random() < 0.3) particles.push({ x: P.x - sign(P.vx) * 4, y: P.y - 1, vx: -P.vx * 0.2, vy: -rand(5, 20), life: 0.3, kind: 'frost' });
  }
  updateHfShots(dt);
});
function drawHfWater() {
  if (!HF.water.length) return;
  const sh = tileSheet('hoarfrost'), full = sh.ok && sh.frames.length > 65;
  for (const [x, y, surf] of HF.water) {
    const px = x * TILE, py = y * TILE;
    if (full) drawTile(g, sh, surf ? 64 : 65, px, py, 0.72);
    else { g.fillStyle = 'rgba(22,56,78,0.72)'; g.fillRect(px, py, TILE, TILE); }
    if (surf) {
      for (let i = 0; i < TILE; i += 2) { const w = Math.sin(time * 1.6 + (px + i) * 0.3) * 0.8; g.fillStyle = 'rgba(200,240,255,0.55)'; g.fillRect(px + i, Math.round(py + 1 + w), 2, 1); }
      if (Math.random() < 0.006) particles.push({ x: px + rand(2, 14), y: py + 1, vx: 0, vy: -rand(4, 10), life: 1, kind: 'frost' });
      addLight(px + 8, py + 4, 16, '120,200,240', 0.2);
    }
  }
}
HOOKS.render.push(() => {
  if (!hfIn()) return;
  drawHfWater();
  drawGlow(drawHfShots);
  if (boss && boss.drawOver) boss.drawOver();
});
HOOKS.renderTop.push(() => {
  if (!P) return;
  const k = Math.max(HF.frost / 100 * 0.8, HF.slowT > 0 ? 0.7 : 0, HF.biteFlash);
  if (k <= 0.05) return;
  const vg = g.createRadialGradient(W / 2, H / 2, 70, W / 2, H / 2, 230);
  vg.addColorStop(0, 'rgba(160,215,255,0)'); vg.addColorStop(1, `rgba(170,220,255,${0.32 * k})`);
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
  if (HF.biteFlash > 0) { g.fillStyle = `rgba(220,245,255,${0.25 * HF.biteFlash})`; g.fillRect(0, 0, W, H); }
});
HOOKS.hud.push(() => {
  if (!P || !D || state === 'cut') return;
  if (HF.frost > 0.5 || HF.slowT > 0) {
    const y = 28 + ((P.rot > 0 || P.rotT > 0) ? 6 : 0);
    const bite = HF.slowT > 0;
    bar(10, y, 40, 2, bite ? HF.slowT / 3 : HF.frost / 100, 0, bite ? '#e4f8ff' : '#6fbaf2');
    text(bite ? 'FROSTBITE' : charmOn('c_frostheart') ? 'frost (warded)' : 'frost', 54, y + 3, 5, '#bfe6f5', 'left');
  }
  if (!boss || !boss.active || !boss.alive) return;
  const bx = 156, by = 203, bw = 216;
  if (boss.kind === 'ice_warden' && boss.shell > 0) {
    bar(bx, by + 5, bw, 2, boss.shell / boss.shellMax, 0, '#9fdcf5');
    text('ice shell', bx + bw, by + 12, 5, '#bfe6f5', 'right');
  }
  if (boss.kind === 'twins' && boss.phase === 1) {
    const hw = bw / 2 - 4;
    boss.parts.forEach((q, i) => {
      const x = bx + i * (hw + 8);
      bar(x, by + 5, hw, 2, Math.max(0, q.hp) / q.maxHp, q.displayHp / q.maxHp, i === 0 ? '#c8502a' : '#5aa8e0');
      text(q.short, i === 0 ? x : x + hw, by + 12, 5, i === 0 ? '#f0a070' : '#a8d8f8', i === 0 ? 'left' : 'right');
    });
  }
});

// ================================================================== enemies
Object.assign(ENEMY, {
  hf_wraith: { hp: 120, cinders: 150, speed: 52, aggro: 210, range: 140, poise: 14, stance: 55, dmg: { dive: 30, breath: 12 }, cool: [1.5, 2.5], flying: true, frost: 18 },
  hf_golem: { hp: 540, cinders: 320, speed: 22, aggro: 170, range: 64, poise: 80, stance: 240, dmg: { slam: 62, swipe: 44 }, cool: [1.3, 2.1], lunge: { swipe: 50, slam: 20 }, frost: 26 },
  hf_lurker: { hp: 160, cinders: 170, speed: 70, aggro: 130, range: 56, poise: 20, stance: 70, dmg: { emerge: 34, grab: 40 }, cool: [0.8, 1.5], frost: 22 },
});
Object.assign(ATTACK_TAGS, { hf_golem: ['slam', 'swipe'], hf_wraith: ['dive'], hf_lurker: ['grab'] });

// ---- frost wraith: hovers, breathes cones of freezing mist, dives
ENEMY_CLASSES.hf_wraith = class extends Enemy {
  updateFlying(dt) {
    const c = this.cfg;
    if ((this.state === 'idle' || this.state === 'walk') && this.aggro && this.cool - dt <= 0 && this.sh.has('breath')) {
      const dx = P.x - this.x, dy = (P.y - 14) - this.y;
      if (Math.abs(dx) < 130 && Math.abs(dy) < 110 && Math.random() < 0.7 && lineOfSight(this.x, this.y, P.x, P.y - 14)) {
        this.startAttack('breath'); this.vx *= 0.3; this.vy *= 0.3; this.aim = null; this.cool = 0;
      }
    }
    if (this.state === 'attack' && this.atk === 'breath') {
      this.cool -= dt; this.t += dt;
      const an = this.anim, sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.breath, f0 = sp ? sp.frame : 4;
      const win = (metaWindows(this.sh, 'breath')[0] || { active: [f0, f0 + 3] }).active;
      if (an.i < f0) this.facePlayer();
      this.vx *= Math.pow(0.1, dt); this.vy *= Math.pow(0.1, dt); this.x += this.vx * dt; this.y += this.vy * dt;
      const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 10, y: this.y };
      if (an.i >= win[0] - 2 && an.i < win[0]) { if (Math.random() < 0.5) particles.push({ x: at.x + rand(-2, 2), y: at.y + rand(-2, 2), vx: 0, vy: 0, life: 0.3, kind: 'frost' }); addLight(at.x, at.y, 22, '170,220,255', 0.8); }
      if (an.i >= win[0] && an.i <= win[1]) {
        if (!this.aim) { const a = Math.atan2(P.y - 14 - at.y, P.x - at.x), base = this.face > 0 ? 0 : Math.PI; let d = a - base; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; this.aim = base + clamp(d, -0.9, 0.9); hfSfx.breath(); }
        this.puffT = (this.puffT || 0) - dt;
        if (this.puffT <= 0) {
          this.puffT = 0.055; const a = this.aim + rand(-0.12, 0.12), v = rand(150, 175);
          hfShot({ kind: 'breath', x: at.x, y: at.y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.5, w: 10, h: 10, dmg: c.dmg.breath, frost: 14, face: this.face, ghost: false });
        }
      }
      if (an.done) { this.setA('idle', this.sh.has('fly') ? 'fly' : 'idle'); this.cool = rand(...c.cool); }
      addLight(this.x, this.y, 26, '160,200,255', 0.5);
      return;
    }
    super.updateFlying(dt);
  }
};

// ---- ice golem: slow brute; the slam sends frost waves along the floor and shakes icicles loose
ENEMY_CLASSES.hf_golem = class extends Enemy {
  startAttack(tag) { super.startAttack(tag); this.slammed = false; }
  updateAttack(dt) {
    const an = this.anim;
    if (this.atk === 'slam' && !this.slammed) {
      const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.slam;
      if (an.i >= (sp ? sp.frame : 7)) {
        this.slammed = true;
        const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x + this.face * 24, y: this.y };
        shake = Math.max(shake, 6); sfx.boom(); hfSfx.crack();
        spawnFx('shockwave', at.x, this.y, 1);
        for (const d of [-1, 1]) hfWave(at.x, this.y, d, 'fwave', 26, 20, 150);
        hfBurst(at.x, this.y - 4, 'frost', 16);
        hfShakeIcicles(at.x, 90);
      }
    }
    super.updateAttack(dt);
    if (this.state === 'attack') addLight(this.x, this.y - 30, 40, '150,210,255', 0.4);
  }
};

// ---- under-ice lurker: glides beneath the surface, bursts up under you, grabs, sinks again
ENEMY_CLASSES.hf_lurker = class extends Enemy {
  constructor(type, x, y, key) {
    super(type, x, y, key);
    this.surf = y; this.state = 'lurk'; this.setA('lurk', this.sh.has('lurk') ? 'lurk' : 'idle'); this.cool = 0.8;
    const ty = Math.floor(y / TILE); let a = Math.floor(x / TILE), b = a;
    while (a > 0 && room.grid[ty * room.w + a - 1] === T_FWATER) a--;
    while (b < room.w - 1 && room.grid[ty * room.w + b + 1] === T_FWATER) b++;
    this.x0 = a * TILE + 10; this.x1 = (b + 1) * TILE - 10;
  }
  get hidden() { return this.state === 'lurk' || this.state === 'tell'; }
  hurtbox() { return this.hidden ? null : super.hurtbox(); }
  hit(info) { if (this.hidden) return; super.hit(info); }
  update(dt) {
    const c = this.cfg;
    this.flash = Math.max(0, this.flash - dt * 5); this.poise = Math.max(0, this.poise - dt * 12); this.stance = Math.max(0, this.stance - dt * 6);
    this.bleed = Math.max(0, this.bleed - dt * 6); this.dmgT -= dt;
    this.anim.update(dt); this.y = this.surf;
    if (this.state === 'dead') {
      this.sink = (this.sink || 0) + dt * 14; this.y = this.surf + this.sink;
      if (this.anim.done && !this.gone) { this.gone = true; hfBurst(this.x, this.surf - 4, 'frost', 14); }
      return;
    }
    const dx = P.x - this.x, adx = Math.abs(dx), near = P.y > this.surf - 100 && P.y < this.surf + 40 && P.state !== 'dead';
    this.cool -= dt;
    switch (this.state) {
      case 'lurk':
        if (near && adx < c.aggro) {
          const tx = clamp(P.x, this.x0, this.x1);
          this.x = approach(this.x, tx, c.speed * dt); this.face = tx < this.x ? -1 : 1;
          if (this.cool <= 0 && adx < 34) { this.state = 'tell'; this.t = 0.5; hfSfx.bubble(); }
        }
        if (Math.random() < 0.05) particles.push({ x: this.x + rand(-6, 6), y: this.surf - 1, vx: 0, vy: -rand(4, 12), life: 0.6, kind: 'frost' });
        break;
      case 'tell':
        this.t -= dt;
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-10, 10), y: this.surf - 1, vx: rand(-10, 10), vy: -rand(20, 50), life: 0.4, kind: 'frost' });
        if (Math.random() < 0.15) hfSfx.bubble();
        addLight(this.x, this.surf - 4, 30, '150,220,255', 0.7);
        if (this.t <= 0) { hfSfx.splash(); this.go('emerge'); }
        break;
      case 'attack': this.attackStep(dt); break;
      case 'up':
        this.facePlayer(); this.t -= dt;
        if (this.cool <= 0 && adx < c.range && near) { this.go('grab'); break; }
        if (this.t <= 0 || adx > 150 || !near) { this.state = 'sub'; this.setA('sub', this.sh.has('submerge') ? 'submerge' : 'idle', false); this.state = 'sub'; hfSfx.splash(); }
        break;
      case 'sub': if (this.anim.done) { this.state = 'lurk'; this.setA('lurk', this.sh.has('lurk') ? 'lurk' : 'idle'); this.state = 'lurk'; this.cool = 1.2; } break;
      case 'hurt': if (this.anim.done) this.toUp(0.4); break;
      case 'stagger': case 'parried':
        this.t -= dt; if (this.anim.i === this.anim.n - 1 || this.anim.done) this.anim.hold();
        if (this.t <= 0) this.toUp(0.3);
        break;
    }
  }
  toUp(cool) { this.state = 'up'; this.setA('up', this.sh.has('idle') ? 'idle' : 'lurk'); this.state = 'up'; this.t = rand(2, 3); this.cool = Math.max(this.cool, cool); }
  go(tag) { this.facePlayer(); this.atk = tag; this.hitIds = new Set(); this.atkId = ++hazardId; this.setA('attack', tag, false); this.state = 'attack'; }
  attackStep(dt) {
    const an = this.anim, c = this.cfg, wins = metaWindows(this.sh, this.atk);
    const tel = this.sh.meta && this.sh.meta.telegraph && this.sh.meta.telegraph[this.atk];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(this.sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    if (an.i < (wins[0] ? wins[0].active[0] : 3) - 1) this.facePlayer();
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.swing(); if (this.atk === 'grab') this.x = clamp(this.x + this.face * 10, this.x0, this.x1); }
      if (this.hitIds.has(wi) || !w.hit) return;
      if (overlap(metaRect(this.sh, this, w.hit), playerHurtbox()) && hurtPlayer(c.dmg[this.atk] || 30, this.face, this.atkId * 10 + wi, { parryable: this.atk === 'grab', src: this })) this.hitIds.add(wi);
    });
    if (this.atk === 'emerge' && an.changed && an.i === 1) hfBurst(this.x, this.surf - 4, 'frost', 18);
    if (an.done) this.toUp(this.atk === 'emerge' ? 0.5 : rand(...c.cool));
  }
  draw() {
    if (this.hidden) {
      if (this.sh.ok && this.sh.has('lurk')) drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, { alpha: 0.8 });
      else { g.fillStyle = 'rgba(10,20,30,0.5)'; g.fillRect(Math.round(this.x - 10), Math.round(this.surf + 2), 20, 4); }
      return;
    }
    super.draw();
  }
};

// ================================================================== mini-boss: the Ice Golem Warden (Sluice Gates)
BOSS_INFO.ice_warden = { name: 'The Ice Golem Warden', hp: 2200, cinders: 4200, reward: ['w:glacier_maul', 'c_aegis'],
  quote: 'Carved to hold the sluice. The ice has held it ever since.' };
PHASE2_LINES.ice_warden = ['', 'The ice shell bursts. Beneath it, the Warden quickens.'];
BOSS_CUTS.ice_warden = b => [
  act(() => { b.anim.set('idle', true); }),
  bossPan(b, 50, 1.2),
  say('', 'Ice has grown over the warden of the sluice, thick as a tomb.'),
  act(() => { holdAnim(b, 'stomp'); }), wait(0.65),
  act(() => { shake = 9; sfx.boom(); hfSfx.crack(); dustFall(24); for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-40, 40), y: b.y - rand(0, 90), vx: rand(-30, 30), vy: -rand(10, 50), life: rand(0.6, 1.2), kind: 'frost' }); }), wait(1.0),
];
BOSS_SPAWN.ice_warden = (cx, fy) => makeWarden(cx, fy);
function makeWarden(x, y) {
  const B = new MetaBoss('ice_warden', x, y, {
    sheets: ['ice_warden', 'ice_warden_p2'], stanceMax: 360, walkSpeed: 30, prefer: 70, p2at: -1, p2speed: 1.3, p2tag: 'stomp', critRange: 64,
    introTag: 'stomp', cool1: [1.1, 1.8], cool2: [0.55, 1.0], victory: 'THE SLUICE STANDS OPEN', deathParticle: 'frost', hfFrost: 20,
    onIntro() { sfx.roar(); shake = 6; },
    weights(d, p2) {
      if (d < 80) return { sweep: 2.6, slam: 1.5, stomp: p2 ? 1.4 : 0.8 };
      if (d < 170) return { slam: 2.2, stomp: 1.8, walk: 1.4, sweep: 0.3 };
      return { stomp: 2.2, walk: 2.4, slam: 0.5 };
    },
    chains: { sweep(d) { return d < 90 ? 'slam' : null; }, slam(d) { return this.phase === 2 ? 'stomp' : d < 80 ? 'sweep' : null; }, stomp: 'sweep' },
    moves: {
      slam: { dmg: [64], shake: 9, spawn(at) {
        shake = 10; sfx.boom(); hfSfx.crack(); spawnFx('shockwave', at.x, this.floor, 1); spawnFx(fxOr('hf_shatter', 'hit'), at.x, this.floor - 12, 1, null, { alpha: 0.8 });
        for (const d of [-1, 1]) hfWave(at.x, this.floor, d, 'fwave', BOSS_DMG * 36, 22, this.phase === 2 ? 190 : 160);
        hfShakeIcicles(P.x, this.phase === 2 ? 130 : 70, 0.5);
        if (this.phase === 2) for (let k = 0; k < 3; k++) hfSpike(clamp(P.x + (k - 1) * 30, this.L, this.R), this.floor, 0.45 + k * 0.15, 40, 20);
      } },
      sweep: { dmg: [50], body: true, shake: 3 },
      stomp: { dmg: [42], shake: 6, spawn(at) {
        const dir = P.x < this.x ? -1 : 1, n = this.phase === 2 ? 7 : 5;
        sfx.boom(); hfSfx.crack();
        for (let k = 1; k <= n; k++) hfSpike(at.x + dir * k * 30, this.floor, 0.1 + k * 0.1, 44, 24);
        if (this.phase === 2) for (let k = 1; k <= 3; k++) hfSpike(at.x - dir * k * 30, this.floor, 0.25 + k * 0.12, 44, 24);
      } },
    },
    wake() { return P.x < room.pw - 6 * TILE; },
    ambient() {
      if (Math.random() < 0.35) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(10, 90), vx: rand(-6, 6), vy: -rand(5, 15), life: 1.2, kind: 'frost' });
      addLight(this.x, this.y - 55, this.phase === 2 ? 90 : 70, this.phase === 2 ? '120,190,255' : '170,215,240', 0.7);
    },
    onDeath() { victoryBanner = { text: 'THE SLUICE STANDS OPEN', t: 0 }; HF.shots = []; },
  });
  B.shell = B.shellMax = Math.round(850 * NGP.hp);
  B.hit = function (info) {
    if (this.phase === 1 && this.shell > 0 && this.active && this.alive && this.state !== 'shatter') {
      const sd = info.dmg * (info.crit ? 1.2 : info.kind === 'heavy' ? 1.5 : 1) * (info.fire ? 1.35 : 1);
      this.shell = Math.max(0, this.shell - sd);
      popup(info.x, info.y - 14, sd, '#bfe8ff');
      hfSfx.ice(); hfBurst(info.x, info.y, 'frost', info.big ? 12 : 6);
      MetaBoss.prototype.hit.call(this, Object.assign({}, info, { dmg: info.dmg * 0.15 }));
      if (this.shell <= 0 && this.alive) { hfSfx.shatter(); toast('The ice shell cracks apart!', 2); if (['attack', 'stagger', 'backstep'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2(); }
      return;
    }
    if (this.state === 'shatter') { MetaBoss.prototype.hit.call(this, Object.assign({}, info, { poise: 0 })); return; }
    MetaBoss.prototype.hit.call(this, info);
  };
  B.enterPhase2 = function () {
    if (!this.shattered) {
      this.shattered = true; this.pendingPhase = false; this.air = null; this.y = this.floor;
      this.state = 'shatter'; this.anim.set(this.sh.has('shatter') ? 'shatter' : 'stagger', false, 1); this.burst = false;
      return;
    }
    MetaBoss.prototype.enterPhase2.call(this);
  };
  B.update = function (dt) {
    if (this.state === 'shatter') {
      this.commonUpdate(dt); this.anim.update(dt); this.facePlayer();
      const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn.shatter;
      if (!this.burst && this.anim.i >= (sp ? sp.frame : 6)) {
        this.burst = true; const at = sp ? metaPoint(this.sh, this, sp.at) : { x: this.x, y: this.y - 50 };
        spawnFx(fxOr('hf_shatter', 'parry_flash'), at.x, at.y, 1); spawnFx('shockwave', this.x, this.floor, 1);
        shake = 12; flashScreen = 0.45; hitstop = 0.12; hfSfx.shatter(); sfx.roar();
        for (let i = 0; i < 50; i++) particles.push({ x: at.x + rand(-20, 20), y: at.y + rand(-30, 30), vx: rand(-200, 200), vy: -rand(40, 220), g: 500, life: rand(0.6, 1.3), kind: i % 3 ? 'frost' : 'rock' });
        hfShakeIcicles(this.x, 9999, 0.3);
        if (Math.abs(P.x - this.x) < 60) hurtPlayer(BOSS_DMG * 30, P.x < this.x ? -1 : 1, ++hazardId, { frost: 20 });
      }
      this.ambient(dt);
      if (this.anim.done) { this.state = 'idle'; MetaBoss.prototype.enterPhase2.call(this); }
      return;
    }
    MetaBoss.prototype.update.call(this, dt);
  };
  const baseDraw = B.draw;
  B.draw = function () {
    baseDraw.call(this);
    if (this.phase === 1 && this.shell > 0 && this.shell < this.shellMax * 0.5 && Math.random() < 0.15) particles.push({ x: this.x + rand(-20, 20), y: this.y - rand(20, 80), vx: 0, vy: rand(10, 30), life: 0.5, kind: 'frost' });
  };
  return B;
}

// ================================================================== main boss: THE FROSTBOUND TWINS (dual boss)
// Two knights sharing one aggregate bar. Each has its own move set; a director keeps both pressuring (their strikes are
// staggered so two unrelated hits never land in the same instant), and runs three duo techniques: the crossing X-slash,
// the launcher (Hael throws you up into Rime's lances) and converging elemental waves. When one falls, the survivor
// absorbs the sibling's element and the bar refills to the full boss maximum.
BOSS_INFO.twins = { name: 'The Frostbound Twins', hp: 3400, cinders: 9000, reward: ['emberdash', 'w:twinborne', 'sp:frost_nova', 'c_twin'],
  quote: '“One oath, two blades. Neither may let the other fall.”' };
PHASE2_LINES.twins = ['', ''];
const TWIN = {
  hael: { name: 'Ser Hael, the Ember', short: 'Ser Hael', p2name: 'Ser Hael, Frostbound', stance: 260, walk: 52, prefer: 48, dash: 200,
    moves: {
      slash: { dmg: [42, 48], parry: true, step: 70, band: [0, 82], w: 3 },
      lunge: { dmg: [48], parry: true, lunge: [3, 4], band: [46, 175], w: 2.2 },
      bash: { dmg: [44], body: true, rush: [3, 5], rushV: 240, band: [40, 170], w: 1.3 },
      slam: { dmg: [58], shake: 8, band: [0, 95], w: 1.3 },
      wave: { dmg: [30], band: [95, 999], w: 2, ranged: true },
      leap: { dmg: [60], leap: [2, 7], height: 64, band: [120, 999], w: 1.7 },
      launch: { dmg: [30], band: [0, 58], w: 0.6, launch: true },
      plant: { dmg: [50], shake: 8, band: [0, 120], w: 1.8, p2: true },
    },
    chains: { slash: ['lunge', 'slam', 'bash'], lunge: ['slash', 'bash'], bash: ['slash', 'launch'], slam: ['wave', 'slash'],
              wave: ['leap', 'lunge'], leap: ['slash', 'plant'], launch: ['slash'], plant: ['slash', 'wave'] } },
  rime: { name: 'Dame Rime, the Hoarfrost', short: 'Dame Rime', p2name: 'Dame Rime, Emberbound', stance: 220, walk: 62, prefer: 58, dash: 230,
    moves: {
      combo: { dmg: [34, 38], parry: true, step: 80, band: [0, 82], w: 3 },
      thrust: { dmg: [50], parry: true, lunge: [3, 4], band: [46, 175], w: 2.4 },
      charge: { dmg: [42], body: true, rush: [3, 5], rushV: 250, band: [40, 170], w: 1.2 },
      cast: { dmg: [], band: [70, 999], w: 1.5, ranged: true },
      volley: { dmg: [], band: [90, 999], w: 2.2, ranged: true },
      spikes: { dmg: [36], band: [60, 999], w: 1.5, ranged: true },
      counter: { band: [0, 72], w: 0.8, stance: true },
      backstep: { band: [0, 60], w: 0.8 },
      riposte: { dmg: [46], parry: false, step: 60, band: [0, 0], w: 0 },
    },
    chains: { combo: ['thrust', 'backstep', 'counter'], thrust: ['combo', 'charge'], charge: ['combo', 'volley'], cast: ['thrust', 'volley'],
              volley: ['thrust', 'spikes'], spikes: ['charge', 'combo'], riposte: ['thrust', 'combo'], backstep: ['volley', 'cast', 'spikes'] } },
};
function animLead(sh, tag, upto, speed = 1) {   // seconds from the start of a tag until frame index `upto`
  const t = sh.tag(tag); let s = 0;
  for (let i = t.from; i < t.from + upto && i <= t.to; i++) s += sh.frames[i].ms;
  return s / 1000 / speed;
}
class TwinKnight {
  constructor(B, who, x, y) {
    const T = TWIN[who], meta = ASSETS['twins_' + who + '_meta'];
    Object.assign(this, { B, who, T, kind: 'twins', boss: true, name: T.name, short: T.short, x, y, floor: y, face: who === 'hael' ? 1 : -1,
      state: 'idle', cool: 1.0, t: 0, stance: 0, stanceMax: T.stance, flash: 0, dmgShown: 0, dmgT: 0, bleed: 0, critRange: 46,
      speed: 1, enraged: false, hitIds: new Set(), fired: {}, chain: 0, role: who === 'hael' ? 'press' : 'flank', nextHitAt: -9, air: null });
    this.hp = this.maxHp = this.displayHp = Math.round(1700 * NGP.hp * bossHpMul('twins'));
    this.sheets = [sheet('twins_' + who, { meta }), sheet('twins_' + who + '_p2', { meta })];
    this.sh = this.sheets[0]; this.anim = new Anim(this.sh, 'idle');
  }
  get alive() { return this.state !== 'dead'; }
  get L() { return TILE * 2 + 16; }
  get R() { return room.pw - TILE * 2 - 16; }
  other() { return this.B.parts.find(q => q !== this); }
  facePlayer() { this.face = P.x < this.x ? -1 : 1; }
  setA(tag, loop = true, speed = this.speed) { this.anim.set(this.sh.has(tag) ? tag : 'idle', loop, speed); }
  play(tag) { this.setA(tag, tag === 'idle' || tag === 'walk' || tag === 'guard' || tag === 'counter'); this.cutTag = tag; }
  hurtbox() { if (!this.alive) return null; const m = this.sh.meta; return m && m.hurtbox ? metaRect(this.sh, this, m.hurtbox) : rect(this.x - 10, this.y - 50, this.x + 10, this.y); }
  critable() { return this.state === 'stagger' && this.anim.i >= 1 && !this.critDone; }
  onCritStart() { this.critDone = true; this.t = Math.max(this.t || 0, 0.9); }
  firstActive(tag) { const w = metaWindows(this.sh, tag); if (w.length) return w[0].active[0]; const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn[tag]; return sp ? sp.frame : 4; }
  lastActive(tag) { const w = metaWindows(this.sh, tag); if (w.length) return w[w.length - 1].active[1]; const m = this.sh.meta && this.sh.meta.spawn_multi && this.sh.meta.spawn_multi[tag]; if (m) return Math.max(...Object.keys(m).map(Number)); const sp = this.sh.meta && this.sh.meta.spawn && this.sh.meta.spawn[tag]; return sp ? sp.frame : 5; }
  lead(tag) { return animLead(this.sh, tag, this.firstActive(tag), this.speed); }
  busy() { return (this.state === 'attack' && this.anim.i <= this.lastActive(this.atk)) || ['dash', 'ready', 'absorb'].includes(this.state); }
  frostOn() { return this.who === 'rime' ? 18 : this.enraged ? 14 : 0; }
  hit(info) {
    const B = this.B;
    if (!this.alive) return;
    if (!B.active) { B.activate(); return; }
    if (this.state === 'absorb') { spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); sfx.block(); return; }
    const front = info.dir === -this.face;
    if (this.state === 'counter' && info.melee && !info.crit && front) {
      if (info.kind === 'heavy' && info.charged) { this.stance = this.stanceMax; this.stagger(); return; }   // a full heavy shatters the stance
      sfx.parry(); hfSfx.ice(); hitstop = 0.12; shake = 4; flashScreen = 0.15;
      spawnFx(fxOr('parry_flash', 'parry_spark'), info.x, info.y, info.dir); hfBurst(info.x, info.y, 'frost', 14);
      P.vx = -P.face * 60; this.start('riposte'); return;
    }
    if (this.state === 'guard' && !info.crit && info.kind !== 'heavy' && front && info.melee) {
      sfx.block(); spawnFx(fxOr('parry_spark', 'hit'), info.x, info.y, info.dir); P.vx = -P.face * 100; P.st -= 10; hitstop = 0.06;
      this.stance += info.poise * 0.5; this.guardHit = true; return;
    }
    const elem = info.fire ? (this.who === 'rime' && !this.enraged ? 1.3 : this.who === 'hael' && !this.enraged ? 0.75 : 1) : 1;
    const dmg = Math.round(info.dmg * elem * (this.state === 'stagger' && !info.crit ? 1.3 : 1));
    this.hp = Math.max(0, this.hp - dmg); this.flash = 1;
    this.dmgShown = this.dmgT > 0 ? this.dmgShown + dmg : dmg; this.dmgT = 2.2;
    B.dmgShown = B.dmgT > 0 ? B.dmgShown + dmg : dmg; B.dmgT = 2.2;
    hitstop = Math.max(hitstop, info.big ? 0.1 : 0.05); shake = Math.max(shake, info.big ? 4 : 2);
    (info.big ? sfx.bigHit : sfx.hit)();
    spawnFx(info.big ? fxOr('parry_spark', 'hit') : 'hit', info.x, info.y, info.dir);
    for (let i = 0; i < (info.big ? 10 : 5); i++) particles.push({ x: info.x, y: info.y, vx: info.dir * rand(20, 90), vy: -rand(20, 90), g: 260, life: rand(0.3, 0.6), kind: this.who === 'hael' ? 'ember' : 'frost' });
    if (info.bleed) {
      this.bleed += info.bleed * 0.7;
      if (this.bleed >= 100) { this.bleed = 0; const bd = Math.round(this.maxHp * 0.06 + 40); this.hp = Math.max(0, this.hp - bd); this.dmgShown += bd; sfx.bleed(); spawnFx(fxOr('bleed', 'blood'), info.x, info.y, info.dir); }
    }
    if (this.hp <= 0) return this.die();
    if (info.crit) { this.stance = 0; this.t = Math.min(this.t || 0, 0.45); return; }
    if (this.stanceImmune > 0 || this.state === 'stagger' || this.air) return;
    this.stance += info.poise;
    if (this.stance >= this.stanceMax && !['dash', 'ready'].includes(this.state)) this.stagger();
  }
  onParried() { if (this.stanceImmune > 0 || this.state === 'stagger' || this.state === 'absorb') return; this.stance += 90; if (this.stance >= this.stanceMax) this.stagger(); }
  stagger() {
    this.critDone = false; this.stanceImmune = 7; this.stanceMax = Math.min(this.stanceMax * 1.15, this.T.stance * 2);
    this.stance = 0; this.state = 'stagger'; this.setA('stagger', false, 1); this.t = 2.0; this.chain = 0; this.air = null; this.y = this.floor;
    sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), this.x, this.y - 40, this.face);
    const o = this.other(); if (o && o.alive) { o.role = 'press'; o.cool = Math.min(o.cool, 0.5); this.role = 'flank'; }   // the twin covers the fallen one
    this.B.abortDuo();
  }
  die() {
    this.state = 'dead'; this.setA('death', false, 1); this.hp = 0; this.air = null; this.y = this.floor;
    shake = 10; hitstop = 0.25; slowmo = 1.0; flashScreen = 0.4; sfx.roar();
    this.B.partDown(this);
  }
  pickMove(d) {
    const e = this.enraged, flank = this.role === 'flank' && !e, mv = this.T.moves, w = {};
    for (const [k, M] of Object.entries(mv)) {
      if (!M.w || (M.p2 && !e) || d < M.band[0] || d > M.band[1]) continue;
      let v = M.w;
      if (flank) v *= M.ranged || M.leap || M.rush || M.lunge ? 1.8 : 0.35;
      if (e && (M.p2 || M.leap)) v *= 1.4;
      if (k === this.last) v *= 0.25;
      w[k] = v;
    }
    const en = Object.entries(w);
    if (!en.length) return 'walk';
    let r = Math.random() * en.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of en) if ((r -= v) <= 0) return k;
    return en[0][0];
  }
  start(m, opt = {}) {
    this.facePlayer(); this.last = m; this.atk = m; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.spawned = false; this.air = null; this.y = this.floor;
    this.duoWave = !!opt.duoWave; this.duo = opt.duo || null;
    if (m === 'walk') { this.state = 'walk'; this.goal = this.approachSpot(); this.t = rand(0.35, 0.6); this.cool = Math.max(this.cool, 0.3); this.setA('walk'); return; }
    if (m === 'guard') { this.state = 'guard'; this.setA('guard'); this.t = rand(0.6, 1.0); return; }
    if (m === 'counter') { this.state = 'counter'; this.setA('counter'); this.t = rand(0.9, 1.4); hfSfx.ice(); sfx.glint(); return; }
    if (m === 'backstep') { this.state = 'backstep'; this.setA('backstep', false); this.bs = { x0: this.x, t: 0 }; return; }
    this.state = 'attack'; this.setA(m, false, m === 'riposte' ? 0.75 : this.speed);
    const M = this.T.moves[m] || {};
    if (M.lunge) this.lungeD = clamp(Math.abs(P.x - this.x) - 24, 14, 140);
    this.nextHitAt = time + this.lead(m);
  }
  approachSpot() {
    const o = this.other();
    if (this.role === 'flank' && o && o.alive && !this.enraged) {
      let side = o.x < P.x ? 1 : -1, gx = P.x + side * 115;
      if (gx < this.L || gx > this.R) { side = -side; gx = P.x + side * 115; }
      return clamp(gx, this.L, this.R);
    }
    return clamp(P.x + (this.x < P.x ? -1 : 1) * this.T.prefer, this.L, this.R);
  }
  // would starting `m` now land a hit within 0.3 s of the sibling's next strike? (keeps two unrelated hits apart)
  clashes(m) {
    const o = this.other();
    if (!o || !o.alive || this.enraged) return false;
    const at = time + this.lead(m);
    return o.state === 'attack' && Math.abs(at - o.nextHitAt) < 0.3;
  }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt; this.stance = Math.max(0, this.stance - dt * 5);
    if (this.state !== 'stagger') this.stanceImmune = Math.max(0, (this.stanceImmune || 0) - dt);
    this.bleed = Math.max(0, this.bleed - dt * 5);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    this.anim.update(dt);
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': {
        this.facePlayer(); this.cool -= dt;
        if (P.state === 'dead' || this.B.duo || this.B.wantDuo) break;
        if (this.cool <= 0) {
          const m = this.pickMove(d);
          if (!['walk', 'guard', 'counter', 'backstep'].includes(m) && this.clashes(m)) { this.cool = 0.08; break; }
          this.start(m); break;
        }
        const gx = this.approachSpot();
        if (Math.abs(gx - this.x) > 24) { this.state = 'walk'; this.goal = gx; this.t = 0.4; this.setA('walk'); }
        break;
      }
      case 'walk': {
        this.t -= dt; this.cool -= dt;
        const dir = sign(this.goal - this.x);
        this.x += dir * this.T.walk * this.speed * dt; this.face = this.role === 'flank' && !this.enraged ? (P.x < this.x ? -1 : 1) : dir;
        if (this.anim.tag !== 'walk') this.setA('walk');
        if (this.t <= 0 || Math.abs(this.goal - this.x) < 4 || this.cool <= 0) { this.state = 'idle'; this.setA('idle'); this.facePlayer(); }
        break;
      }
      case 'dash': {
        const dir = sign(this.goal - this.x);
        this.x = approach(this.x, this.goal, this.T.dash * dt); this.face = dir;
        if (this.anim.tag !== 'walk') this.setA('walk', true, 1.9);
        if (Math.random() < 0.5) particles.push({ x: this.x - dir * 8, y: this.y - rand(0, 4), vx: -dir * 30, vy: -rand(5, 25), life: 0.4, kind: this.who === 'hael' ? 'ember' : 'frost' });
        if (Math.abs(this.goal - this.x) < 3) { this.state = 'ready'; this.facePlayer(); this.setA('guard'); }
        break;
      }
      case 'ready': this.facePlayer(); break;
      case 'recover':   // the punish window after a long chain or a duo technique
        this.t -= dt; this.facePlayer();
        if (Math.random() < 0.2) particles.push({ x: this.x + rand(-8, 8), y: this.y - rand(30, 50), vx: 0, vy: -rand(5, 15), life: 0.5, kind: this.who === 'hael' ? 'ember' : 'frost' });
        if (this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.1; }
        break;
      case 'attack': this.updateAttack(dt); break;
      case 'guard':
        this.facePlayer(); this.t -= dt;
        if (this.guardHit) { this.guardHit = false; this.start(this.who === 'hael' ? 'slash' : 'combo'); break; }
        if (this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.1; }
        break;
      case 'counter':
        this.facePlayer(); this.t -= dt;
        if (Math.random() < 0.4) particles.push({ x: this.x + rand(-14, 14), y: this.y - rand(0, 50), vx: 0, vy: -rand(4, 14), life: 0.5, kind: this.enraged ? 'fire' : 'frost' });
        addLight(this.x, this.y - 30, 50, '170,225,255', 0.8);
        if (this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.05; this.last = 'counter'; }
        break;
      case 'backstep': {
        this.bs.t += dt; const T = Math.max(0.3, this.anim.total()), k = Math.min(1, this.bs.t / T);
        this.x = clamp(this.bs.x0 - this.face * 84 * Math.sin(k * Math.PI / 2), this.L, this.R);
        if (this.anim.done || k >= 1) { const nx = ['volley', 'cast', 'spikes', 'thrust'][irand(0, 3)]; this.start(this.clashes(nx) ? 'thrust' : nx); }
        break;
      }
      case 'stagger':
        this.t -= dt;
        if (this.anim.i === this.anim.n - 1 && this.t > 0.3) this.anim.hold();
        if (Math.random() < 0.3) particles.push({ x: this.x + rand(-6, 6), y: this.y - 62, vx: 0, vy: -rand(10, 20), life: 0.4, kind: 'gold' });
        if (this.anim.done || this.t <= 0) { this.state = 'idle'; this.setA('idle'); this.cool = 0.25; }
        break;
      case 'absorb':
        if (this.anim.changed && this.anim.i === 6) {
          flashScreen = 0.6; shake = 10; sfx.roar(); hfSfx.shatter(); sfx.fire(); this.B.refillFrom = time;
          spawnFx(fxOr('hf_nova', 'roar_ring'), this.x, this.floor, 1, null, { bottom: true });
          for (let i = 0; i < 40; i++) particles.push({ x: this.x + rand(-10, 10), y: this.y - rand(10, 50), vx: rand(-160, 160), vy: -rand(30, 160), g: 200, life: rand(0.6, 1.2), kind: i % 2 ? 'fire' : 'frost' });
        }
        if (this.anim.done) { this.state = 'idle'; this.setA('idle'); this.cool = 0.3; }
        break;
      case 'dead':
        if (!this.anim.done && Math.random() < 0.4) particles.push({ x: this.x + rand(-16, 16), y: this.y - rand(0, 60), vx: 0, vy: -rand(15, 40), life: rand(0.8, 1.6), kind: this.who === 'hael' ? 'ember' : 'frost' });
        if (this.anim.done) this.anim.hold();
        break;
    }
    if (this.state !== 'dead') this.x = clamp(this.x, this.L, this.R);
  }
  updateAttack(dt) {
    const an = this.anim, sh = this.sh, a = this.atk, M = this.T.moves[a] || {}, wins = metaWindows(sh, a);
    const first = this.firstActive(a);
    if (an.i < first - 1 && !this.duo) this.facePlayer();
    const tel = sh.meta && sh.meta.telegraph && sh.meta.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    if (an.i > this.lastActive(a)) this.nextHitAt = -9;
    // ---- movement
    if (M.rush && an.i >= M.rush[0] && an.i <= M.rush[1]) {
      this.x += this.face * M.rushV * this.speed * dt;
      if (Math.random() < 0.6) particles.push({ x: this.x - this.face * 10, y: this.y - rand(0, 30), vx: -this.face * 40, vy: -rand(0, 20), life: 0.4, kind: (this.who === 'hael') !== this.enraged ? 'ember' : 'frost' });
    }
    if (M.lunge && an.i >= M.lunge[0] && an.i <= M.lunge[1]) {
      let T = 0; for (let i = M.lunge[0]; i <= M.lunge[1]; i++) T += an.ms(i); T = T / 1000 / an.speed;
      this.x += this.face * this.lungeD / T * dt;
      if (this.who === 'hael' && Math.random() < 0.7) particles.push({ x: this.x + this.face * rand(10, 30), y: this.y - rand(24, 34), vx: -this.face * 60, vy: -rand(0, 20), life: 0.3, kind: 'fire' });
    }
    if (M.leap) {
      if (an.changed && an.i === M.leap[0] && !this.air) {
        const T = animLead(sh, a, first, an.speed) - animLead(sh, a, M.leap[0], an.speed);
        this.air = { x0: this.x, tx: clamp(P.x - this.face * 14, this.L, this.R), t: 0, T: Math.max(0.2, T) }; sfx.jump(); sfx.bossSwing();
      }
      if (this.air) {
        this.air.t += dt; const k = Math.min(1, this.air.t / this.air.T);
        this.x = lerp(this.air.x0, this.air.tx, k); this.y = this.floor - Math.sin(k * Math.PI) * M.height;
        if (k >= 1) { this.air = null; this.y = this.floor; shake = 8; sfx.boom(); }
      }
    }
    // ---- strikes
    wins.forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); if (M.shake) shake = Math.max(shake, M.shake); if (this.duo === 'x' && wi === 0) this.B.xFlash(); }
      if (M.step) this.x += this.face * M.step * dt;
      if (this.hitIds.has(wi) || !w.hit) return;
      const r = metaRect(sh, this, (w.rects && w.rects[String(an.i)]) || w.hit);
      if (M.body) { if (this.face > 0) r.x0 = Math.min(r.x0, this.x); else r.x1 = Math.max(r.x1, this.x); }
      if (overlap(r, playerHurtbox())) {
        const dmg = (M.dmg ? (M.dmg[wi] ?? M.dmg[0]) : 40) * (this.enraged ? 1.12 : 1) * NGP.dmg;
        if (hurtPlayer(BOSS_DMG * dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: !!M.parry, src: this, frost: this.frostOn() })) {
          this.hitIds.add(wi);
          if (M.launch && P.state !== 'dead') { P.vy = -430; P.vx = this.face * 50; P.ground = false; P.y -= 2; setP('air', 'jump_up', false); P.airDash = true; this.B.launched = time; }
        }
      }
    });
    // ---- scripted spawns
    const sp = sh.meta && sh.meta.spawn && sh.meta.spawn[a];
    const multi = sh.meta && sh.meta.spawn_multi && sh.meta.spawn_multi[a];
    if (multi) { for (const [fi, at] of Object.entries(multi)) if (an.i >= +fi && !this.fired[fi]) { this.fired[fi] = true; this.special(a, metaPoint(sh, this, at), +fi); } }
    else if (sp && !this.spawned && an.i >= sp.frame) { this.spawned = true; this.special(a, metaPoint(sh, this, sp.at)); }
    if (an.done) {
      this.air = null; this.y = this.floor; this.nextHitAt = -9;
      if (this.duo) { this.duo = null; this.state = 'recover'; this.setA('idle', true, 0.6); this.t = 0.8; return; }
      const e = this.enraged, d = Math.abs(P.x - this.x);
      const maxChain = e ? 3 : 2, list = (this.T.chains[a] || []).filter(k => !this.T.moves[k] || !this.T.moves[k].p2 || e);
      if (list.length && this.chain < maxChain && Math.random() < (e ? 0.8 : 0.65) && !this.B.duo && !this.B.wantDuo) {
        let nx = list[irand(0, list.length - 1)];
        const NM = this.T.moves[nx];
        if (NM && NM.band && d > NM.band[1] + 20) nx = this.who === 'hael' ? (d > 175 ? 'leap' : 'lunge') : (d > 175 ? 'volley' : 'thrust');
        if (!this.clashes(nx)) { this.chain++; return this.start(nx); }
      }
      const long = this.chain >= 2;
      this.chain = 0;
      if (long) { this.state = 'recover'; this.setA('idle', true, 0.6); this.t = e ? 0.6 : 0.8; const o = this.other(); if (o && o.alive) o.cool = Math.max(o.cool, 0.55); return; }
      this.state = 'idle'; this.setA('idle');
      this.cool = e ? rand(0.12, 0.35) : this.role === 'flank' ? rand(0.4, 0.8) : rand(0.25, 0.55);
    }
  }
  special(a, at, k = 0) {
    const e = this.enraged, F = this.floor, dir = this.face;
    if (a === 'slam') {
      spawnFx('shockwave', at.x, F, 1); sfx.boom(); sfx.fire();
      hfWave(at.x, F, dir, 'flwave', BOSS_DMG * 36, e ? 16 : 0, 175);
      if (e) for (let j = 1; j <= 3; j++) hfSpike(this.x - dir * (30 + j * 30), F, 0.2 + j * 0.12, 42, 20, 'ice');
      hfBurst(at.x, F - 4, 'fire', 14);
    } else if (a === 'wave') {
      sfx.fire(); spawnFx('shockwave', at.x, F, 1);
      const spd = this.waveSpd || 175; this.waveSpd = 0;
      hfWave(at.x, F, dir, 'flwave', BOSS_DMG * 34, e ? 14 : 0, spd);
      if (e && !this.duoWave) { const w2 = hfWave(at.x, F, dir, 'fwave', BOSS_DMG * 30, 20, spd * 0.8); w2.delay = 0.3; }
    } else if (a === 'leap') {
      spawnFx('shockwave', at.x, F, 1); spawnFx(fxOr('hf_shatter', 'hit'), at.x, F - 10, 1, null, { alpha: 0.7 });
      for (const dd of [-1, 1]) hfWave(at.x, F, dd, dd === dir || !e ? 'flwave' : 'fwave', BOSS_DMG * 30, e ? 16 : 0, 165);
    } else if (a === 'plant') {
      sfx.boom(); flashScreen = 0.3; shake = 9;
      spawnFx(fxOr('hf_nova', 'roar_ring'), this.x, F, 1, null, { bottom: true });
      if (Math.abs(P.x - this.x) < 64 && Math.abs(P.y - F) < 40) hurtPlayer(BOSS_DMG * 44 * NGP.dmg, P.x < this.x ? -1 : 1, ++hazardId, { frost: 18 });
      for (const dd of [-1, 1]) for (let j = 1; j <= 6; j++) hfSpike(this.x + dd * (36 + j * 32), F, 0.2 + j * 0.13, 44, 20, j % 2 ? 'ice' : 'fire');
    } else if (a === 'cast') {
      hfSfx.crack(); sfx.charge();
      const n = e ? 5 : 3;
      for (let j = 0; j < n; j++) hfSpike(clamp(P.x + (j - (n - 1) / 2) * 28, this.L, this.R), F, 0.12 + Math.abs(j - (n - 1) / 2) * 0.14, 42, 22, e && j % 2 ? 'fire' : 'ice');
    } else if (a === 'volley') {
      const fire = e && k === 6, tx = P.x + P.vx * 0.25, ty = P.y - 14 + (P.ground ? 0 : P.vy * 0.12);
      const ang = Math.atan2(ty - at.y, tx - at.x) + (k - 6) * 0.05;
      hfShot({ kind: fire ? 'firebolt' : 'lance', x: at.x, y: at.y, vx: Math.cos(ang) * 240, vy: Math.sin(ang) * 240, life: 1.8, w: 8, h: 8, dmg: BOSS_DMG * 26, frost: fire ? 0 : 12 });
      hfSfx.ice(); for (let j = 0; j < 5; j++) particles.push({ x: at.x, y: at.y, vx: rand(-40, 40), vy: rand(-40, 40), life: 0.3, kind: fire ? 'fire' : 'frost' });
    } else if (a === 'spikes') {
      hfSfx.crack(); sfx.boom(); spawnFx('shockwave', at.x, F, 1);
      if (this.duoWave) { hfWave(at.x, F, dir, 'fwave', BOSS_DMG * 32, 22, this.waveSpd || 160); this.waveSpd = 0; }
      else for (let j = 1; j <= 6; j++) hfSpike(at.x + dir * j * 30, F, 0.08 + j * 0.11, 40, 22, e && j % 2 === 0 ? 'fire' : 'ice');
    }
  }
  draw() {
    if (!this.sh.ok) { g.fillStyle = this.who === 'hael' ? '#8a3020' : '#6a8ab0'; g.fillRect(Math.round(this.x - 10), Math.round(this.y - 56), 20, 56); return; }
    if (this.state === 'dead' && this.anim.done) return;
    const opt = this.flash > 0 ? { flash: this.flash * 0.7 } : this.state === 'stagger' ? { flash: 0.15 + 0.1 * Math.sin(time * 20), flashColor: '#ffd070' }
      : this.state === 'ready' ? { flash: 0.12 + 0.1 * Math.sin(time * 30), flashColor: this.who === 'hael' ? '#ff9040' : '#a0e0ff' }
      : this.state === 'counter' ? { flash: 0.18 + 0.12 * Math.sin(time * 16), flashColor: this.enraged ? '#ffb070' : '#bfefff' } : {};
    drawSprite(this.sh, this.anim.frame, this.x, this.y, this.face, opt);
  }
  light() {
    if (!this.alive) return;
    const hot = this.who === 'hael' ? '255,150,70' : '150,210,255';
    addLight(this.x + this.face * 10, this.y - 36, this.enraged ? 80 : 60, this.enraged ? (this.who === 'hael' ? '200,220,255' : '255,170,90') : hot, 0.7);
  }
}

class FrostboundTwins extends BossBase {
  constructor(x, y) {
    super('twins', x, y);
    this.parts = [new TwinKnight(this, 'hael', x - 36, y), new TwinKnight(this, 'rime', x + 36, y)];
    this.hp = this.maxHp = this.displayHp = this.fullMax = this.parts.reduce((s, q) => s + q.maxHp, 0);
    this.sh = this.parts[0].sh; this.anim = new Anim(this.sh, 'idle'); this.state = 'dormant'; this.duoT = rand(5, 7);
  }
  canStagger() { return false; }
  hurtbox() { return null; }
  get alivePs() { return this.parts.filter(q => q.alive); }
  facePlayer() { for (const q of this.parts) if (q.alive) q.facePlayer(); this.face = P.x < this.x ? -1 : 1; }
  clash(x, n) {
    const y = this.floor - 38;
    spawnFx(fxOr('hf_clash', 'parry_flash'), x, y, 1); sfx.parry(); hfSfx.ice(); shake = 3 + n; hitstop = 0.05;
    for (let i = 0; i < 16; i++) particles.push({ x, y, vx: rand(-110, 110), vy: -rand(20, 120), g: 300, life: rand(0.4, 0.8), kind: i % 2 ? 'fire' : 'frost' });
    if (n >= 3) flashScreen = 0.35;
  }
  update(dt) {
    this.flash = Math.max(0, this.flash - dt * 5); this.dmgT -= dt;
    const live = this.alivePs;
    if (this.phase === 2) {
      const s = live[0], k = this.refillFrom === undefined ? 0 : clamp((time - this.refillFrom) / 1.3, 0, 1);
      this.hp = s ? Math.min(s.hp, this.maxHp * (1 - Math.pow(1 - k, 2))) : 0;   // the bar visibly refills after the absorb
    } else this.hp = this.parts.reduce((s, q) => s + q.hp, 0);
    this.displayHp += (this.hp - this.displayHp) * Math.min(1, dt * (this.dmgT > 1.4 ? 0 : 3));
    if (this.state === 'dead') { this.anim.update(dt); for (const q of this.parts) q.update(dt); return; }
    if (!this.active) {
      for (const q of this.parts) { q.anim.update(dt); if (!this.cutting) q.facePlayer(); }
      if (!this.cutting && P.x > 6 * TILE && P.state !== 'dead') this.activate();
      this.track(); return;
    }
    if (this.state !== 'fight') {
      this.state = 'fight';
      for (const q of this.parts) { q.state = 'idle'; q.setA('idle'); q.facePlayer(); q.cool = q.who === 'hael' ? 0.35 : 0.9; }
    }
    if (this.introT > 0) {
      this.introT -= dt;
      for (const q of this.parts) { if (q.anim.tag !== 'guard') q.setA('guard'); q.facePlayer(); q.anim.update(dt); }
      if (this.introT <= 0) for (const q of this.parts) { q.setA('idle'); q.cool = 0.3; }
      this.track(); return;
    }
    if (this.phase === 1 && live.length === 2) {
      this.roleT = (this.roleT || 6) - dt;
      if (this.roleT <= 0 && !this.duo) { this.roleT = rand(5, 7); for (const q of this.parts) q.role = q.role === 'press' ? 'flank' : 'press'; }
      if (!this.duo) {
        this.duoT -= dt;
        if (this.duoT <= 0) this.wantDuo = (this.wantDuo || 0) + dt;   // hold new attacks so both twins come free
        if (this.wantDuo && P.state !== 'dead' && live.every(q => ['idle', 'walk', 'guard', 'recover', 'counter'].includes(q.state) || (q.state === 'attack' && q.anim.i > q.lastActive(q.atk)))) { this.wantDuo = 0; this.startDuo(); }
        else if (this.wantDuo > 3) { this.wantDuo = 0; this.duoT = 2; }
      } else this.updateDuo(dt);
    }
    for (const q of this.parts) q.update(dt);
    this.track();
    if (Math.random() < 0.3) particles.push({ x: this.x + rand(-160, 160), y: this.floor - rand(0, 4), vx: rand(-4, 4), vy: -rand(2, 8), life: 1.2, kind: 'frost' });
  }
  // ---------------------------------------------------------------- duo techniques
  startDuo() {
    const [h, r] = this.parts, cl = (q, x) => clamp(x, q.L, q.R);
    const roomL = P.x - h.L, roomR = h.R - P.x;
    const twoSided = Math.min(roomL, roomR) >= 80, wide = Math.min(roomL, roomR) >= 150;
    const opts = (twoSided ? ['x', 'launch'].concat(wide ? ['waves'] : []) : ['launch']).filter(k => k !== this.lastDuo || !twoSided);
    const kind = opts[irand(0, opts.length - 1)];
    let side = h.x < P.x ? -1 : 1, hx, rx;
    if (!twoSided) side = roomL > roomR ? -1 : 1;   // cornered: both come from the open side
    if (kind === 'x') { hx = P.x + side * 78; rx = P.x - side * 78; }
    else if (kind === 'launch') { hx = P.x + side * 36; rx = twoSided ? P.x - side * 118 : P.x + side * 120; }
    else { hx = P.x + side * 150; rx = P.x - side * 150; }
    if (Math.abs(cl(h, hx) - hx) > 30 || Math.abs(cl(r, rx) - rx) > 30) { this.duoT = 0.8; return; }
    this.duo = { kind, st: 'move', t: 0 }; this.lastDuo = kind;
    h.goal = cl(h, hx); r.goal = cl(r, rx);
    for (const q of this.parts) { q.state = 'dash'; q.chain = 0; }
    toast({ x: 'The twins cross their blades…', launch: 'Ser Hael lowers his blade…', waves: 'The twins part to either side…' }[kind], 1.3);
  }
  abortDuo() { this.wantDuo = 0; if (!this.duo) return; this.duo = null; this.duoT = rand(5, 7); for (const q of this.parts) if (q.alive && ['dash', 'ready'].includes(q.state)) { q.state = 'idle'; q.setA('idle'); q.cool = 0.3; } }
  updateDuo(dt) {
    const du = this.duo, [h, r] = this.parts;
    if (!h.alive || !r.alive) { this.abortDuo(); return; }
    du.t += dt;
    if (du.st === 'move') {
      if ((h.state === 'ready' && r.state === 'ready') || du.t > 1.4) {
        du.st = 'tell'; du.t = 0; for (const q of this.parts) { q.state = 'ready'; q.facePlayer(); }
        sfx.glint(); hfSfx.crack(); flashScreen = 0.12;
        if (du.kind === 'x') { const lh = h.lead('slash'), lr = r.lead('combo'); du.startH = 0.35 + Math.max(0, lr - lh); du.startR = 0.35 + Math.max(0, lh - lr); }
        else if (du.kind === 'launch') { du.startH = 0.3; du.startR = 0.3 + h.lead('launch') + 0.05; }
        else {
          // converging waves: both arrive at the player's position together
          const th = h.lead('wave'), tr = r.lead('spikes'), dh = Math.abs(P.x - h.x) - 30, dr = Math.abs(P.x - r.x) - 30, travel = 0.8;
          h.waveSpd = clamp(dh / travel, 110, 240); r.waveSpd = clamp(dr / travel, 110, 240);
          du.startH = 0.35 + Math.max(0, tr - th); du.startR = 0.35 + Math.max(0, th - tr);
        }
      }
    } else if (du.st === 'tell') {
      if (!du.h && du.t >= du.startH) { du.h = true; h.start({ x: 'slash', launch: 'launch', waves: 'wave' }[du.kind], { duo: du.kind, duoWave: du.kind === 'waves' }); if (du.kind === 'waves') h.waveSpd = h.waveSpd || 175; }
      if (!du.r && du.t >= du.startR) { du.r = true; r.start({ x: 'combo', launch: 'volley', waves: 'spikes' }[du.kind], { duo: du.kind, duoWave: du.kind === 'waves' }); }
      if (du.h && du.r) du.st = 'strike';
      for (const q of this.parts) if (q.state === 'ready') q.facePlayer();
    } else if (du.st === 'strike') {
      if (h.state !== 'attack' && r.state !== 'attack') { this.duo = null; this.duoT = rand(6, 9); }
    }
  }
  xFlash() {
    if (this.xFlashed === this.duo) return; this.xFlashed = this.duo;
    spawnFx(fxOr('hf_xslash', 'hf_clash'), P.x, P.y - 18, 1); flashScreen = 0.2; shake = 5; hfSfx.shatter(); sfx.fire();
  }
  track() {
    const live = this.alivePs;
    if (!live.length) return;
    let near = live[0]; for (const q of live) if (Math.abs(q.x - P.x) < Math.abs(near.x - P.x)) near = q;
    this.x = near.x; this.y = this.floor;
    const mid = live.reduce((s, q) => s + q.x, 0) / live.length;
    this.camX = Math.abs(live[0].x - (live[1] || live[0]).x) > 300 ? near.x : mid;
  }
  // ---------------------------------------------------------------- one twin falls: the survivor takes the other's element, the bar refills to full
  partDown(q) {
    const o = q.other();
    this.abortDuo();
    if (!(o && o.alive)) return this.die();
    this.phase = 2; this.name = o.T.p2name; o.enraged = true; o.role = 'press'; o.speed = 1.2; o.air = null; o.y = o.floor;
    if (o.sheets[1].ok) o.sh = o.sheets[1];
    o.maxHp = this.fullMax; o.hp = o.maxHp; o.displayHp = o.maxHp; o.stance = 0; o.stanceMax = o.T.stance * 1.3; o.chain = 0;
    this.maxHp = this.fullMax; this.hp = 0; this.displayHp = 0; this.dmgT = 0; this.refillFrom = undefined;
    o.state = 'absorb'; o.setA('absorb', false, 1); o.facePlayer();
    HF.shots = []; hazards = [];
    PHASE2_LINES.twins = o.who === 'hael' ? ['Ser Hael', 'Sister… your winter is mine. I will not fall alone.'] : ['Dame Rime', 'Brother… give me your fire. Burn with me.'];
    const stream = () => { for (let i = 0; i < 6; i++) { const t = rand(0, 1); particles.push({ x: lerp(q.x, o.x, t) + rand(-6, 6), y: q.y - rand(10, 50), vx: (o.x - q.x) * rand(0.9, 1.6), vy: -rand(0, 30), life: rand(0.4, 0.8), kind: q.who === 'hael' ? 'fire' : 'frost' }); } };
    if (SAVE.flags['cutp2:twins']) { this.x = o.x; for (let i = 0; i < 40; i++) stream(); return; }
    SAVE.flags['cutp2:twins'] = 1;
    o.anim.set('absorb', false, 0);   // kneel frozen until the camera reaches the survivor
    playCutscene([
      { pan: { x: q.x, y: q.y - 40 }, dur: 0.5 },
      { dur: 1.1, tween: () => { stream(); if (Math.random() < 0.2) hfSfx.bubble(); } },
      act(() => { o.setA('absorb', false, 1); }),
      { pan: { x: o.x, y: o.y - 40 }, dur: 0.5, tween: () => stream() },
      say(PHASE2_LINES.twins[0], PHASE2_LINES.twins[1], { dur: 2.2 }),
      { until: () => o.anim.i >= 7, max: 2.5 },
      wait(0.5),
      { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
    ], () => { if (o.state === 'absorb' && o.anim.i < 6) o.anim.i = 6; if (this.refillFrom === undefined) this.refillFrom = time; });
  }
  die() {
    this.state = 'dead'; this.hp = 0; this.anim = new Anim(this.parts[0].sh, 'death', false);
    hazards = []; HF.shots = []; projectiles = projectiles.filter(p => p.owner === 'player');
    shake = 12; hitstop = 0.3; slowmo = 1.6; flashScreen = 0.6; sfx.roar(); sfx.felled();
    victoryBanner = { text: 'THE TWINS ARE LAID TO REST', t: 0 };
    this.rewards();
  }
  ambient(dt) {   // cutscenes: keep the pair animating (updateCutscene only advances boss.anim)
    if (state === 'cut') for (const q of this.parts) {
      q.flash = Math.max(0, q.flash - dt * 5);
      q.anim.update(dt);
      if (q.state === 'absorb' && q.anim.changed && q.anim.i === 6) {
        flashScreen = 0.6; shake = 10; sfx.roar(); hfSfx.shatter(); sfx.fire();
        spawnFx(fxOr('hf_nova', 'roar_ring'), q.x, q.floor, 1, null, { bottom: true });
        for (let i = 0; i < 40; i++) particles.push({ x: q.x + rand(-10, 10), y: q.y - rand(10, 50), vx: rand(-160, 160), vy: -rand(30, 160), g: 200, life: rand(0.6, 1.2), kind: i % 2 ? 'fire' : 'frost' });
      }
      if (q.anim.done && q.cutTag && q.cutTag !== 'idle' && q.state !== 'dead' && q.state !== 'absorb') { q.cutTag = null; q.setA('idle'); }
    }
    for (const q of this.parts) q.light();
  }
  draw() {
    const shadow = (x, w) => { g.fillStyle = 'rgba(6,4,10,0.5)'; g.beginPath(); g.ellipse(Math.round(x), Math.round(this.floor) + 1, w, 2.5, 0, 0, 6.3); g.fill(); };
    for (const q of this.parts) if (!(q.state === 'dead' && q.anim.done) && (this.state === 'dormant' || this.state === 'dead' || q.x !== this.x)) shadow(q.x, q.air ? 10 : 16);
    for (const q of this.parts) if (q.state === 'dead') q.draw();
    for (const q of [...this.parts].sort((a, b) => (a.who === 'rime' ? -1 : 1))) if (q.state !== 'dead') q.draw();
    for (const q of this.parts) q.light();
  }
  drawOver() {   // duo tell: elemental lines race along the floor toward the player
    const du = this.duo; if (!du || du.st === 'move') return;
    const k = clamp(du.t / 0.35, 0, 1);
    for (const q of this.parts) {
      if (!q.alive) continue;
      const x0 = q.x, x1 = lerp(q.x, P.x, k), y = this.floor - 1;
      g.fillStyle = q.who === 'hael' ? 'rgba(255,150,60,0.85)' : 'rgba(170,225,255,0.85)';
      g.fillRect(Math.round(Math.min(x0, x1)), y, Math.round(Math.abs(x1 - x0)), 1);
      addLight(x1, y - 4, 20, q.who === 'hael' ? '255,150,60' : '170,225,255', 0.8);
    }
  }
}
BOSS_SPAWN.twins = (cx, fy) => new FrostboundTwins(cx, fy);
BOSS_CUTS.twins = b => {
  const [h, r] = b.parts, mid = (h.x + r.x) / 2;
  const face = () => { for (const q of b.parts) q.face = P.x < q.x ? -1 : 1; };
  return [
    act(() => { h.x = mid - 30; r.x = mid + 30; h.face = 1; r.face = -1; h.play('idle'); r.play('idle'); b.track(); }),
    { pan: { x: mid, y: b.floor - 40 }, dur: 1.0 },
    act(() => { h.play('slash'); r.play('guard'); }), wait(0.5), act(() => b.clash(mid, 1)), wait(0.4),
    act(() => { r.play('thrust'); h.play('guard'); }), wait(0.6), act(() => b.clash(mid, 2)), wait(0.3),
    act(() => { h.play('slash'); r.play('combo'); }), wait(0.42), act(() => { b.clash(mid, 3); spawnFx(fxOr('hf_xslash', 'hf_clash'), mid, b.floor - 40, 1); }), wait(0.45),
    say('Ser Hael', 'Hold, sister. Someone walks upon the ice.'),
    act(() => { face(); h.play('idle'); r.play('idle'); }),
    say('Dame Rime', 'Then our quarrel waits. Together, brother — as we swore.'),
    act(() => { face(); h.play('guard'); r.play('counter'); sfx.roar(); shake = 7; flashScreen = 0.3;
      for (const q of b.parts) for (let i = 0; i < 18; i++) particles.push({ x: q.x + rand(-14, 14), y: q.y - rand(0, 60), vx: rand(-30, 30), vy: -rand(20, 70), life: rand(0.6, 1.2), kind: q.who === 'hael' ? 'fire' : 'frost' }); }),
    wait(0.75),
  ];
};
