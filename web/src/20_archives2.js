// ------------------------------------------------------------------ Ashen Archives finale (agent A): The Unwritten, its ink, the Archives' loot hooks
// The Unwritten is the Hollow Scribe's unfinished story of the Root, given hunger. It fights in A6 "The Inkwell":
// ink bolts (fans, spirals), homing quills, tendrils out of the floor, it writes ink platforms and floods the floor
// with ink, sinks into the ink to reappear behind you, and at half health the room's pages invert (phase 2).

Object.assign(BOSS_INFO, {
  unwritten: { name: 'The Unwritten', hp: 2600, cinders: 7000, reward: ['hook', 'w:inkquill', 'sp:glyph_swarm', 'c_quill'],
               quote: '“What is never written cannot rest.”' },
});
if (BOSS_INFO.librarian) BOSS_INFO.librarian.reward = ['w:lantern_staff', 'c_lantern', 'shard'];
if (!CHARMS.c_lantern) registerGear({ charms: { c_lantern: { name: 'Librarian’s Lantern', desc: 'A wide circle of light that no darkness can snuff. Weak walls glimmer when you pass them.' } } }, 'ui_icons2');

const AR2_AMB = AREAS.archives.ambient;
const INK = { b: [], plats: [], floods: [], pages: [], drift: [], stairs: false, sealT: 0 };
const INV = { k: 0, target: 0, room: null, orig: null, inv: null, cb: null, cf: null, cx: 0, cy: 0, last: 0 };
const ar2Red = () => boss && boss.kind === 'unwritten' && boss.phase === 2;
const inkCol = red => red ? '226,71,47' : '138,105,216';

// ---- small sprite helpers
function ar2Frame(sh, tag, t, loop = true) {
  const tg = sh.tag(tag); let ms = t * 1000, f = tg.from, tot = 0;
  for (let i = tg.from; i <= tg.to; i++) tot += sh.frames[i].ms;
  if (loop && tot > 0) ms %= tot;
  while (f < tg.to && ms >= sh.frames[f].ms) { ms -= sh.frames[f].ms; f++; }
  return f;
}

// ================================================================== ink projectiles
function inkBolt(x, y, vx, vy, o = {}) {
  INK.b.push({ x, y, vx, vy, t: 0, life: o.life || 5, r: o.r || 4, dmg: BOSS_DMG * (o.dmg || 24) * NGP.dmg, id: ++hazardId,
               kind: o.kind || 'bolt', red: o.red ?? ar2Red(), aim: o.aim || 0, homeT: o.homeT || 0, turn: o.turn || 0,
               acc: o.acc || 0, vmax: o.vmax || 0, spd: o.spd || Math.hypot(vx, vy), ang: Math.atan2(vy, vx) });
}
function inkSplash(x, y, red) { const f = spawnFx('ink_splash', x, y, 1); if (f && red) f.anim.set('r', false); for (let i = 0; i < 5; i++) particles.push({ x, y, vx: rand(-50, 50), vy: rand(-60, 10), g: 220, life: 0.5, kind: 'ink' }); }
function updateInkBullets(dt) {
  for (const b of INK.b) {
    b.t += dt;
    if (b.kind === 'quill' && b.t < b.aim) {            // hovering, turning to aim at the player: the warning
      const a = Math.atan2(P.y - 14 - b.y, P.x - b.x); b.ang = a; if (b.follow) { b.x = b.follow.x + b.ox; b.y = b.follow.y + b.oy; }
      continue;
    }
    if (b.kind === 'quill') {
      const lt = b.t - b.aim;
      if (lt < b.homeT) {
        const a = Math.atan2(P.y - 14 - b.y, P.x - b.x); let d = a - b.ang;
        while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
        b.ang += clamp(d, -b.turn * dt, b.turn * dt);
      }
      b.spd = Math.min(b.vmax, b.spd + b.acc * dt);
      b.vx = Math.cos(b.ang) * b.spd; b.vy = Math.sin(b.ang) * b.spd;
      if (Math.random() < 0.5) particles.push({ x: b.x - b.vx * 0.03, y: b.y - b.vy * 0.03, vx: 0, vy: 0, life: 0.3, kind: 'ink' });
    }
    b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt;
    if (b.t > 0.08 && isSolidT(tileAt(Math.floor(b.x / TILE), Math.floor(b.y / TILE)))) { b.life = 0; inkSplash(b.x, b.y, b.red); continue; }
    if (b.x < -20 || b.x > room.pw + 20 || b.y < -20 || b.y > room.ph + 20) { b.life = 0; continue; }
    const r = rect(b.x - b.r, b.y - b.r, b.x + b.r, b.y + b.r);
    if (overlap(r, playerHurtbox()) && hurtPlayer(b.dmg, sign(b.vx) || 1, b.id)) { b.life = 0; inkSplash(b.x, b.y, b.red); }
  }
  INK.b = INK.b.filter(b => b.life > 0);
  let n = 0; for (const b of INK.b) if ((n++ & 1) === 0) addLight(b.x, b.y, b.kind === 'quill' ? 26 : 20, inkCol(b.red), 0.55);
}
function drawInkBullets() {
  const sb = fxSheet('ink_bolt'), sq = fxSheet('ink_quill');
  for (const b of INK.b) {
    const tag = b.red ? 'r' : 'v';
    if (b.kind === 'quill') {
      if (!sq.ok) continue;
      if (b.t < b.aim) {   // aim line: a faint dotted ruling toward the player
        const k = b.t / b.aim, n = 10;
        for (let i = 1; i <= n; i++) { if ((i + Math.floor(time * 16)) % 3) continue; g.fillStyle = `rgba(${inkCol(b.red)},${0.18 + 0.35 * k})`; g.fillRect(Math.round(b.x + Math.cos(b.ang) * i * 9), Math.round(b.y + Math.sin(b.ang) * i * 9), 1, 1); }
      }
      drawRotated(sq, ar2Frame(sq, tag, b.t), b.x, b.y, b.ang, b.t < 0.15 ? b.t / 0.15 : 1);
    } else if (sb.ok) drawSprite(sb, ar2Frame(sb, tag, b.t + b.id * 0.013), b.x, b.y, 1, { center: true });
  }
}

// ================================================================== written platforms + ink floods
function inkPlat(x0, row, life, delay = 0, perm = false) {
  const pl = { x0, x1: x0 + 48, y0: row * TILE, t: -delay, life, perm, solid: false };
  pl.dyn = { x0: pl.x0, x1: pl.x1, y0: pl.y0, y1: pl.y0 + 6, ar2: true, on: () => pl.solid && P.y <= pl.y0 + 0.5 };
  room.dyn.push(pl.dyn); INK.plats.push(pl); return pl;
}
function updateInkPlats(dt) {
  for (const p of INK.plats) {
    const was = p.t; p.t += dt;
    if (was < 0 && p.t >= 0) { sfx.bolt(); for (let i = 0; i < 8; i++) particles.push({ x: rand(p.x0, p.x1), y: p.y0 + 2, vx: rand(-20, 20), vy: -rand(10, 40), life: 0.5, kind: 'ink' }); }
    p.solid = p.t >= 0.12 && (p.perm || p.t < p.life + 0.2);
    if (p.t >= 0) addLight((p.x0 + p.x1) / 2, p.y0, 34, '138,105,216', 0.35);
    if (!p.perm && p.t > p.life + 0.45) p.gone = true;
  }
  for (const p of INK.plats) if (p.gone) room.dyn = room.dyn.filter(d => d !== p.dyn);
  INK.plats = INK.plats.filter(p => !p.gone);
}
function drawInkPlats() {
  const s = sheet('ar2_inkplat'); if (!s.ok) return;
  for (const p of INK.plats) {
    if (p.t < 0) continue;
    const f = p.t < 0.27 ? ar2Frame(s, 'write', p.t, false) : (!p.perm && p.t > p.life) ? ar2Frame(s, 'fade', p.t - p.life, false) : ar2Frame(s, 'loop', p.t);
    drawSprite(s, f, p.x0 + 24, p.y0 + 10, 1, { bottom: true });
    if (!p.perm && p.t > p.life - 0.8 && p.t < p.life && Math.floor(time * 10) % 2) { g.fillStyle = 'rgba(200,180,255,0.25)'; g.fillRect(p.x0, p.y0, 48, 6); }   // about to fade: flicker
  }
}
// The flood: after a warning, a wave of ink runs out from where the Unwritten stabbed the floor and covers the
// WHOLE floor; only the platforms it wrote stay above it.
function inkFlood(x0, x1, ox, tele, dur, red) {
  INK.floods.push({ x0: clamp(x0, TILE, room.pw - TILE), x1: clamp(x1, TILE, room.pw - TILE), ox, t: 0, tele, dur, red, spd: 380,
                    id: ++hazardId, fy: boss ? boss.floor : room.ph - TILE });
}
function floodH(f, x) {   // ink depth at x (px), with the travelling crest
  const ts = f.t - f.tele - Math.abs(x - f.ox) / f.spd;
  if (ts <= 0 || x < f.x0 || x > f.x1) return 0;
  let h = 19 * (1 - Math.pow(1 - Math.min(1, ts / 0.3), 2));
  if (ts < 0.3) h += 14 * (1 - ts / 0.3) * Math.min(1, ts / 0.06);
  const end = f.t - f.tele - f.dur;
  if (end > 0) h *= clamp(1 - end / 0.6, 0, 1);
  return h;
}
function updateInkFloods(dt) {
  for (const f of INK.floods) {
    const was = f.t; f.t += dt;
    const on = f.t >= f.tele && f.t < f.tele + f.dur + 0.3;
    if (was < f.tele && f.t >= f.tele) { sfx.fire(); sfx.boom(); shake = Math.max(shake, 5); }
    if (f.t < f.tele) {   // warning: the floor boils
      if (Math.random() < 0.6) particles.push({ x: rand(f.x0, f.x1), y: f.fy - 1, vx: 0, vy: -rand(20, 60), life: 0.5, kind: 'ink' });
      if (Math.floor(was * 3) !== Math.floor(f.t * 3)) { noise(0.3, 120, 0.6, 0.25, 'lowpass'); shake = Math.max(shake, 1.5); }
    }
    for (let x = f.x0 + 20; x < f.x1; x += 48) addLight(x, f.fy - 6, 34, inkCol(f.red), on ? 0.5 : 0.3 + 0.25 * Math.sin(time * 12));
    if (on) {
      const fd = (f.t - f.tele) * f.spd;
      for (const side of [-1, 1]) {   // spray at the running wave fronts
        const fx = f.ox + side * fd;
        if (fx > f.x0 && fx < f.x1) for (let i = 0; i < 4; i++) particles.push({ x: fx + rand(-4, 4), y: f.fy - 24, vx: side * rand(20, 90), vy: -rand(40, 130), g: 380, life: 0.6, kind: 'ink' });
      }
      if (P.state !== 'dead' && P.y >= f.fy - 3 && floodH(f, P.x) > 5) {
        if (hurtPlayer(BOSS_DMG * 36 * NGP.dmg, P.face || 1, f.id + '_' + Math.floor(f.t / 0.4))) P.vy = -250;   // it throws you up: find a platform
      }
      if (Math.random() < 0.3) particles.push({ x: rand(f.x0, f.x1), y: f.fy - 10, vx: 0, vy: -rand(8, 24), life: 0.6, kind: 'ink' });
    }
    if (f.t > f.tele + f.dur + 0.7) f.gone = true;
  }
  INK.floods = INK.floods.filter(f => !f.gone);
}
function drawInkFloods() {
  const s = sheet('fx_ink_pool');
  for (const f of INK.floods) {
    const pre = f.red ? 'r_' : '', crest = f.red ? ['226,71,47', '255,217,168'] : ['138,105,216', '242,236,255'];
    if (f.t < f.tele) {   // warning: the whole floor lights up with script, pulsing faster as it nears
      if (s.ok) { const fm = s.frames[ar2Frame(s, pre + 'tele', f.t)]; for (let x = f.x0; x < f.x1; x += 16) g.drawImage(s.img, fm.x, fm.y, Math.min(16, f.x1 - x), 12, Math.round(x), Math.round(f.fy - 12), Math.min(16, f.x1 - x), 12); }
      const k = f.t / f.tele, a = 0.35 + 0.35 * Math.sin(time * (10 + 18 * k));
      g.fillStyle = `rgba(${crest[0]},${a})`; g.fillRect(Math.round(f.x0), Math.round(f.fy - 1), Math.round(f.x1 - f.x0), 1);
      const gr = g.createLinearGradient(0, f.fy - 30, 0, f.fy);   // a haze of the coming ink hugging the whole floor
      gr.addColorStop(0, `rgba(${crest[0]},0)`); gr.addColorStop(1, `rgba(${crest[0]},${(0.12 + 0.3 * k) * (0.7 + 0.3 * Math.sin(time * 14))})`);
      g.fillStyle = gr; g.fillRect(Math.round(f.x0), Math.round(f.fy - 30), Math.round(f.x1 - f.x0), 30);
      for (let x = f.x0 + 8; x < f.x1; x += 32) {   // warning chevrons pointing up at the platforms
        const y = Math.round(f.fy - 16 - 3 * Math.sin(time * 8 + x * 0.05)), c = Math.round(x + 8 * Math.sin(x));
        g.fillStyle = `rgba(${crest[1]},${0.25 + 0.4 * k})`; g.fillRect(c, y, 1, 1); g.fillRect(c - 1, y + 1, 1, 1); g.fillRect(c + 1, y + 1, 1, 1); g.fillRect(c - 2, y + 2, 1, 1); g.fillRect(c + 2, y + 2, 1, 1);
      }
      const mh = Math.round(3 + 9 * k);   // the ink boiling up at the stab point
      g.fillStyle = 'rgba(10,7,16,0.95)'; g.beginPath(); g.ellipse(Math.round(f.ox), f.fy, 6 + 14 * k, mh, 0, Math.PI, 2 * Math.PI); g.fill();
      g.fillStyle = `rgba(${crest[0]},0.8)`; g.fillRect(Math.round(f.ox - 2), Math.round(f.fy - mh), 4, 1);
      continue;
    }
    const x0 = Math.round(f.x0), x1 = Math.round(f.x1);
    for (let x = x0; x < x1; x += 2) {
      const h = floodH(f, x + 1); if (h < 0.5) continue;
      const wv = h > 3 ? 1.2 * Math.sin(time * 5 + x * 0.12) + 0.6 * Math.sin(time * 3.1 - x * 0.07) : 0;
      const top = Math.round(f.fy - h + wv), bot = Math.round(f.fy + 2);
      g.fillStyle = 'rgba(8,6,14,0.97)'; g.fillRect(x, top + 3, 2, Math.max(0, bot - top - 3));
      g.fillStyle = f.red ? 'rgba(70,16,24,0.95)' : 'rgba(38,32,61,0.95)'; g.fillRect(x, top + 1, 2, 2);
      if (h > 8) { g.fillStyle = f.red ? 'rgba(110,17,25,0.5)' : 'rgba(55,47,85,0.5)'; g.fillRect(x, top + 5 + Math.round(2 * Math.sin(time * 2 + x * 0.2)), 2, 1); }
      const surge = h > 19.5;
      g.fillStyle = `rgba(${surge ? crest[1] : crest[0]},${surge ? 0.95 : 0.8})`; g.fillRect(x, top, 2, 1);
      if (((x + Math.floor(time * 40)) % 36) < 4 && h > 6) { g.fillStyle = `rgba(${crest[0]},0.35)`; g.fillRect(x, top + 4, 2, 1); }   // current streaks
    }
  }
}

// ================================================================== tendrils (engine hazards, drawn by fx_ink_tendril)
function inkTendril(x, floor, delay, red) {
  hazards.push({ x, y: floor, w: 12, h: 58, dmg: BOSS_DMG * 42 * NGP.dmg, id: ++hazardId, life: 4, delay: Math.max(0.001, delay), fx: null,
    onStart: h => { h.fx = spawnFx('ink_tendril', h.x, floor, 1, null, { bottom: true }); if (!h.fx) { h.life = 0; return; } if (red) h.fx.anim.set('r', false); },
    update: h => {
      if (!h.fx || h.fx.anim.done) { h.life = 0; return; }
      const i = h.fx.anim.i;
      if (i === 4 && h.fx.anim.changed) { sfx.pillar(); shake = Math.max(shake, 2.5); }
      if (i < 4) addLight(h.x, floor - 4, 20 + i * 5, inkCol(red), 0.45 + 0.15 * Math.sin(time * 20));
      else if (i <= 7) addLight(h.x, floor - 36, 46, inkCol(red), 0.7);
    },
    active: h => h.fx && h.fx.anim.i >= 4 && h.fx.anim.i <= 7 });
}

// ================================================================== pages: orbit the Unwritten; in phase 2 they are thrown
function updateInkPages(dt, B) {
  const alive = B && B.alive && B.active && !B.hidden;
  while (alive && INK.pages.filter(p => p.mode === 'orbit').length < 3 && !(INK.pageCd > 0)) {
    INK.pages.push({ mode: 'orbit', a: rand(0, 6.28), t: 0, x: B.x, y: B.y - 80, fade: 0, id: ++hazardId });
    INK.pageCd = 1.2;
  }
  INK.pageCd = (INK.pageCd || 0) - dt;
  const c = B ? { x: B.x - B.face * 4, y: B.y - 82 } : null;
  for (const p of INK.pages) {
    p.t += dt;
    if (p.mode === 'orbit') {
      if (!alive) { p.fade -= dt * 2; if (p.fade <= 0) p.gone = true; continue; }
      p.fade = Math.min(1, p.fade + dt * 2);
      p.a += dt * 1.25;
      const tx = c.x + Math.cos(p.a) * 50, ty = c.y + Math.sin(p.a) * 9 - Math.cos(p.a) * 12 + Math.sin(p.t * 2 + p.id) * 2;
      p.x = lerp(p.x, tx, Math.min(1, dt * 8)); p.y = lerp(p.y, ty, Math.min(1, dt * 8));
      p.front = Math.sin(p.a) > 0;
    } else if (p.mode === 'aim') {
      p.x = lerp(p.x, p.hx, Math.min(1, dt * 6)); p.y = lerp(p.y, p.hy, Math.min(1, dt * 6));
      if (p.t < p.aimT - 0.3) { p.tx = P.x; p.ty = P.y - 12; }   // tracks you, then locks for the last 0.3 s
      if (p.t >= p.aimT) { p.mode = 'dash'; p.t = 0; const a = Math.atan2(p.ty - p.y, p.tx - p.x); p.vx = Math.cos(a) * 330; p.vy = Math.sin(a) * 330; sfx.spear(); }
    } else if (p.mode === 'dash') {
      p.x += p.vx * dt; p.y += p.vy * dt;
      if (Math.random() < 0.6) particles.push({ x: p.x, y: p.y, vx: 0, vy: 0, life: 0.35, kind: 'fire' });
      const hit = overlap(rect(p.x - 5, p.y - 5, p.x + 5, p.y + 5), playerHurtbox()) && hurtPlayer(BOSS_DMG * 26 * NGP.dmg, sign(p.vx), p.id);
      if (hit || p.t > 1.6 || isSolidT(tileAt(Math.floor(p.x / TILE), Math.floor(p.y / TILE)))) { p.gone = true; inkSplash(p.x, p.y, true); }
      addLight(p.x, p.y, 22, '226,71,47', 0.6);
    }
  }
  INK.pages = INK.pages.filter(p => !p.gone);
}
function throwPages(B, n) {
  const orbit = INK.pages.filter(p => p.mode === 'orbit');
  for (let k = 0; k < n; k++) {
    let p = orbit[k];
    if (!p) { p = { x: rand(B.L, B.R), y: rand(50, 110), t: 0, fade: 1, id: ++hazardId }; INK.pages.push(p); for (let i = 0; i < 6; i++) particles.push({ x: p.x, y: p.y, vx: rand(-30, 30), vy: rand(-30, 30), life: 0.4, kind: 'ink' }); }
    const side = k % 2 ? -1 : 1;
    p.mode = 'aim'; p.t = 0; p.aimT = 0.75 + k * 0.17; p.id = ++hazardId;
    p.hx = clamp(P.x + side * rand(70, 150), B.L, B.R); p.hy = clamp(P.y - rand(70, 120), 44, P.y - 40);
    p.tx = P.x; p.ty = P.y - 12;
  }
  INK.pageCd = 3.5;
}
function drawInkPages() {
  const s = fxSheet('ink_page'); if (!s.ok) return;
  for (const p of INK.pages) {
    const red = p.mode !== 'orbit' || ar2Red();
    if (p.mode === 'aim') {   // ruled line to where it will fly
      const n = Math.floor(Math.hypot(p.tx - p.x, p.ty - p.y) / 6), k = p.t / p.aimT;
      for (let i = 1; i < n; i++) { if ((i + Math.floor(time * 20)) % 4 === 0) continue; g.fillStyle = `rgba(226,71,47,${0.15 + 0.45 * k})`; g.fillRect(Math.round(lerp(p.x, p.tx, i / n)), Math.round(lerp(p.y, p.ty, i / n)), 1, 1); }
    }
    drawSprite(s, ar2Frame(s, red ? 'r' : 'v', p.t * (p.mode === 'dash' ? 3 : 1) + p.id * 0.07), p.x, p.y, 1, { center: true, alpha: (p.fade ?? 1) * (p.mode === 'orbit' && !p.front ? 0.6 : 1) });
  }
  // phase 2: loose pages drift upward, weightless
  if (INV.k > 0.3) for (const d of INK.drift) drawSprite(s, ar2Frame(s, 'v', d.t + d.s), d.x, d.y, 1, { center: true, alpha: 0.55 * INV.k });
}
function updateDrift(dt) {
  if (INV.k <= 0.3) return;
  while (INK.drift.length < 12) INK.drift.push({ x: rand(20, room.pw - 20), y: room.ph + rand(0, 60), vy: -rand(12, 26), s: rand(0, 3), t: 0 });
  for (const d of INK.drift) { d.t += dt; d.y += d.vy * dt; d.x += Math.sin(d.t * 1.3 + d.s) * 8 * dt; if (d.y < 20) { d.y = room.ph + 10; d.x = rand(20, room.pw - 20); } }
}

// ================================================================== the page inverts (phase 2 look)
function invertCanvas(src, base) {
  const c = document.createElement('canvas'); c.width = src.width; c.height = src.height;
  const x = c.getContext('2d');
  if (base) { x.fillStyle = AREAS.archives.tint; x.fillRect(0, 0, c.width, c.height); }
  x.drawImage(src, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height), a = d.data;
  const paper = [214, 202, 178], ink = [34, 20, 30];
  for (let i = 0; i < a.length; i += 4) {
    if (!a[i + 3]) continue;
    const l = (0.3 * a[i] + 0.59 * a[i + 1] + 0.11 * a[i + 2]) / 255, t = Math.pow(Math.min(1, l * 1.7), 0.85);
    a[i] = paper[0] + (ink[0] - paper[0]) * t; a[i + 1] = paper[1] + (ink[1] - paper[1]) * t; a[i + 2] = paper[2] + (ink[2] - paper[2]) * t;
  }
  x.putImageData(d, 0, 0);
  return c;
}
function invStart(on, x, y) {
  if (!room || room.id !== 'A6') return;
  if (INV.room !== room) {
    INV.room = room; INV.orig = { back: room.back, front: room.front };
    INV.inv = { back: invertCanvas(room.back, true), front: invertCanvas(room.front, false) };
    const mk = () => { const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; return c; };
    INV.cb = mk(); INV.cf = mk();
  }
  INV.target = on ? 1 : 0; INV.cx = x; INV.cy = y; INV.last = time;
}
function renderInversion() {
  if (INV.room !== room || !INV.orig) return;
  const dt = Math.min(0.1, time - INV.last); INV.last = time;
  if (INV.k !== INV.target) INV.k = approach(INV.k, INV.target, dt * (INV.target ? 0.7 : 0.5));
  AREAS.archives.ambient = lerp(AR2_AMB, 0.3, INV.k);
  const R = INV.k * Math.hypot(room.pw, room.ph);
  if (INV.k <= 0) { room.back = INV.orig.back; room.front = INV.orig.front; return; }
  if (INV.k >= 1) { room.back = INV.inv.back; room.front = INV.inv.front; return; }
  for (const [dst, a, b] of [[INV.cb, INV.orig.back, INV.inv.back], [INV.cf, INV.orig.front, INV.inv.front]]) {
    const x = dst.getContext('2d'); x.clearRect(0, 0, dst.width, dst.height); x.drawImage(a, 0, 0);
    x.save(); x.beginPath(); x.arc(INV.cx, INV.cy, Math.max(0.5, R), 0, 6.3); x.clip(); x.clearRect(0, 0, dst.width, dst.height); x.drawImage(b, 0, 0); x.restore();
  }
  room.back = INV.cb; room.front = INV.cf;
  // the turning edge of the page
  g.strokeStyle = 'rgba(255,138,79,0.8)'; g.lineWidth = 2; g.beginPath(); g.arc(INV.cx, INV.cy, Math.max(1, R), 0, 6.3); g.stroke();
  if (R > 4) { g.strokeStyle = 'rgba(255,217,168,0.5)'; g.lineWidth = 1; g.beginPath(); g.arc(INV.cx, INV.cy, R - 3, 0, 6.3); g.stroke(); }
}

// ================================================================== The Unwritten
const UW_TAG = { reap: 'reap', fan: 'cast', quills: 'cast', spiral: 'cast', tendrils: 'write', blot: 'write', pages: 'write', sink: 'sink' };
class Unwritten extends MetaBoss {
  constructor(x, fy) {
    super('unwritten', x, fy, {
      sheets: ['unwritten', 'unwritten_p2'], stanceMax: 340, walkSpeed: 0, prefer: 100, p2at: 0.5, p2speed: 1.18, p2tag: 'transform',
      critRange: 58, floating: true, cool1: [0.85, 1.45], cool2: [0.5, 0.95], victory: 'THE STORY ENDS', deathParticle: 'ink',
    });
    this.alt = 0; this.altT = 14; this.altSpd = 70; this.vx = 0; this.hidden = true; this.sched = []; this.channel = 0; this.home = x;
  }
  canStagger() { return this.state !== 'sunk' && !this.hidden && !(this.state === 'attack' && ['sink', 'rise', 'transform'].includes(this.atk)); }
  hurtbox() {
    if (!this.alive || this.hidden || this.state === 'sunk' || this.state === 'dormant') return null;
    if (this.state === 'attack' && ((this.atk === 'sink' && this.anim.i >= 4) || (this.atk === 'rise' && this.anim.i <= 1))) return null;
    return metaRect(this.sh, this, this.sh.meta.hurtbox);
  }
  hit(info) { if (this.hidden || this.state === 'sunk') return; super.hit(info); }
  pt(name) { const m = this.sh.meta; return metaPoint(this.sh, this, (m.points && m.points[name]) || m.spawn[name].at); }
  later(t, fn) { this.sched.push({ t, fn }); }
  pickMove() {
    const d = Math.abs(P.x - this.x), p2 = this.phase === 2, blotOn = INK.floods.length > 0 || this.blotCd > 0;
    if (INK.floods.length) return ['fan', 'quills', 'fan', ...(p2 ? ['pages', 'spiral'] : [])][irand(0, p2 ? 4 : 2)];   // you are on the platforms: it shoots
    let w;
    if (d < 90) w = { reap: 2.2, retreat: 1.4, sink: 0.8, tendrils: 1.0, fan: 0.5 };
    else if (d < 210) w = { fan: 1.6, quills: 1.2, tendrils: 1.2, reap: 1.3, blot: blotOn ? 0 : 0.9, spiral: 0.8, sink: 0.6 };
    else w = { fan: 1.2, quills: 1.4, spiral: 1.2, sink: 1.3, blot: blotOn ? 0 : 0.6, tendrils: 0.8 };
    if (p2) { w.pages = 1.4; w.spiral = (w.spiral || 0) + 0.3; }
    if (this.rangedRun >= 3) { w.reap = (w.reap || 0) + 3; w.sink = (w.sink || 0) + 1.5; }
    if (this.meleeRun >= 2) { w.reap = 0; w.retreat = (w.retreat || 0) + 3; }
    if (w[this.last]) w[this.last] *= 0.25;
    const e = Object.entries(w).filter(([, v]) => v > 0);
    let r = Math.random() * e.reduce((s, [, v]) => s + v, 0);
    for (const [k, v] of e) if ((r -= v) <= 0) return k;
    return 'fan';
  }
  start(m) {
    this.facePlayer(); this.last = m; this.variant = m; this.altSpd = 70;
    this.rangedRun = ['fan', 'quills', 'spiral', 'blot', 'pages'].includes(m) ? (this.rangedRun || 0) + 1 : 0;
    this.meleeRun = m === 'reap' ? (this.meleeRun || 0) + 1 : m === 'retreat' ? 0 : (this.meleeRun || 0);
    const d = Math.abs(P.x - this.x);
    if (m === 'retreat') {   // drift away across the room, then open fire
      const away = (this.x - P.x) || -this.face, room_ = away > 0 ? this.R - this.x : this.x - this.L;
      const dir = room_ > 110 ? sign(away) : -sign(away);
      this.glideTx = clamp(P.x + dir * rand(140, 180), this.L + 10, this.R - 10);
      const opts = (this.phase === 2 ? ['fan', 'quills', 'spiral', 'pages', 'blot'] : ['fan', 'quills', 'spiral', 'blot']).filter(o => o !== 'blot' || !(this.blotCd > 0));
      this.state = 'glide'; this.after = opts[irand(0, opts.length - 1)]; this.t = 1.3; this.altT = 18;
      this.anim.set('drift', true, this.speed); return;
    }
    this.glideTx = null;
    if (m === 'reap' && d > 84) { this.state = 'glide'; this.after = 'reap'; this.t = 1.1; this.anim.set('drift', true, this.speed); this.altT = 8; return; }
    if (m === 'sink' || UW_TAG[m] === 'write') { this.altT = 0; this.altSpd = 170; }
    if (m === 'sink' && this.alt > 2) { this.state = 'descend'; this.after = m; this.t = 0.8; return; }
    if (m === 'spiral') { this.altT = 22; this.altSpd = 60; }
    else if (UW_TAG[m] === 'cast') this.altT = 20;
    else if (m === 'reap') this.altT = 6;
    this.startTag(UW_TAG[m]);
  }
  startTag(tag) {
    this.atk = tag; this.hitIds = new Set(); this.atkId = ++hazardId; this.fired = {}; this.state = 'attack'; this.channel = 0;
    this.anim.set(tag, false, this.speed); const w = metaWindows(this.sh, tag); this.firstActive = w.length ? w[0].active[0] : 99;
  }
  update(dt) {
    this.commonUpdate(dt);
    const an = this.anim; an.update(dt); this.hover += dt;
    if (this.blotCd > 0) this.blotCd -= dt;
    for (const s of this.sched) { s.t -= dt; if (s.t <= 0 && !s.done) { s.done = true; if (this.alive) s.fn.call(this); } }
    this.sched = this.sched.filter(s => !s.done);
    this.alt = approach(this.alt, this.altT, this.altSpd * dt);
    const still = ['stagger', 'dead', 'sunk', 'dormant', 'intro'].includes(this.state) || (this.state === 'attack' && ['sink', 'rise', 'write'].includes(this.atk));
    this.y = this.floor - this.alt - (still ? 0 : Math.sin(this.hover * 1.8) * 2);
    if (!this.active) {
      this.facePlayer(); this.hidden = true;
      if (P.x > 6 * TILE && P.x < this.x - 40 && P.ground && P.state !== 'dead') this.activate();
      return;
    }
    if (this.introT > 0) {   // (no cutscene: it was seen already) the Unwritten rises out of the book's ink
      if (this.state !== 'intro') { this.state = 'intro'; this.hidden = false; this.alt = this.altT = 0; this.anim.set('rise', false); ar2Burst(this.x, this.floor, false); sfx.fire(); this.introT = 1.6; }
      this.introT -= dt;
      if (this.anim.done && this.anim.tag === 'rise') this.anim.set('idle', true);
      if (this.introT <= 0) { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.6; this.altT = 14; }
      return;
    }
    if (this.hidden && this.state === 'idle') this.hidden = false;
    const d = Math.abs(P.x - this.x);
    switch (this.state) {
      case 'idle': {
        this.facePlayer(); this.cool -= dt;
        if (this.altT !== 14 && this.cool > 0.2 && !this.tired) this.altT = 14;
        const want = this.prefer, dx = P.x - this.x;
        let tv = 0; if (d < want - 40) tv = -sign(dx) * 40; else if (d > want + 50) tv = sign(dx) * 60;
        this.vx = approach(this.vx, tv * this.speed, 140 * dt); this.x = clamp(this.x + this.vx * dt, this.L, this.R);
        const fwd = this.vx * this.face > 30;
        if (fwd && this.anim.tag !== 'drift') this.anim.set('drift', true); else if (!fwd && this.anim.tag === 'drift') this.anim.set('idle', true);
        if (P.state === 'dead') break;
        if (this.cool <= 0) { this.tired = false; this.start(this.pickMove()); }
        break;
      }
      case 'glide': {
        this.t -= dt; const tx = this.glideTx != null ? this.glideTx : clamp(P.x - sign(P.x - this.x) * 60, this.L, this.R);
        this.face = tx < this.x ? -1 : 1; this.x = approach(this.x, tx, 190 * this.speed * dt);
        if (Math.random() < 0.5) particles.push({ x: this.x - this.face * rand(10, 40), y: this.y - rand(10, 70), vx: -this.face * 30, vy: 0, life: 0.5, kind: 'ink' });
        if (Math.abs(this.x - tx) < 6 || this.t <= 0) {
          this.vx = 0;
          if (this.after === 'reap') { this.altT = 6; this.startTag('reap'); }
          else { const m = this.after; this.glideTx = null; this.start(m); }
        }
        break;
      }
      case 'descend':
        this.t -= dt; this.facePlayer();
        if (this.alt <= 1 || this.t <= 0) { this.alt = 0; this.startTag(UW_TAG[this.after]); }
        break;
      case 'attack': this.atkUpdate(dt); break;
      case 'sunk': {   // travelling under the floor as a ripple of ink
        this.t -= dt;
        this.x = approach(this.x, this.tx, 250 * this.speed * dt);
        if (Math.random() < 0.7) particles.push({ x: this.x + rand(-8, 8), y: this.floor - 2, vx: rand(-20, 20), vy: -rand(20, 60), g: 200, life: 0.5, kind: 'ink' });
        addLight(this.x, this.floor - 4, 30, inkCol(this.phase === 2), 0.6);
        if (Math.abs(this.x - this.tx) < 3) this.riseT = (this.riseT || 0) + dt;
        if (this.riseT >= 0.45 * (this.phase === 2 ? 0.8 : 1)) { this.riseT = 0; this.hidden = false; this.facePlayer(); this.startTag('rise'); ar2Burst(this.x, this.floor, this.phase === 2); sfx.fire(); }
        break;
      }
      case 'stagger':
        this.t -= dt; this.altT = 0; this.altSpd = 120;
        if (an.i === an.n - 1 && this.t > 0.3) an.hold();
        if (an.done || this.t <= 0) { if (this.pendingPhase) this.enterPhase2(); else { this.state = 'idle'; this.anim.set('idle', true); this.cool = 0.35; this.altT = 14; } }
        break;
      case 'dead':
        if (Math.random() < 0.4 && this.anim.i < this.anim.n - 1) particles.push({ x: this.x + rand(-30, 30), y: this.y - rand(10, 120), vx: 0, vy: -rand(15, 45), life: rand(1, 2), kind: 'ink' });
        if (an.done) an.hold();
        break;
    }
    if (this.phase === 1 && this.hp <= this.maxHp * this.p2at && this.alive && !this.pendingPhase) {
      if (['attack', 'stagger', 'sunk', 'descend', 'glide'].includes(this.state)) this.pendingPhase = true; else this.enterPhase2();
    }
    if (this.pendingPhase && (this.state === 'glide' || this.state === 'descend')) this.enterPhase2();
    this.x = clamp(this.x, this.L, this.R);
  }
  atkUpdate(dt) {
    const an = this.anim, a = this.atk, sh = this.sh, M = UW_MOVES[a] || {};
    if ((a === 'reap' && an.i < this.firstActive - 1) || (a === 'cast' && an.i < 5)) this.facePlayer();
    const tel = sh.meta.telegraph && sh.meta.telegraph[a];
    if (tel && an.changed && an.i === tel.frame) { const p = metaPoint(sh, this, tel.at); spawnFx('telegraph', p.x, p.y, this.face); sfx.glint(); }
    metaWindows(sh, a).forEach((w, wi) => {
      if (an.i < w.active[0] || an.i > w.active[1]) return;
      if (an.changed && an.i === w.active[0]) { sfx.bossSwing(); shake = Math.max(shake, 3); }
      this.x = clamp(this.x + this.face * 70 * dt, this.L, this.R);
      if (this.hitIds.has(wi)) return;
      const rr = (sh.meta.attacks[a].rects || {})[an.i], r = metaRect(sh, this, rr || w.hit);
      if (overlap(r, playerHurtbox()) && hurtPlayer(BOSS_DMG * 58 * (this.phase === 2 ? 1.1 : 1) * NGP.dmg, P.x < this.x ? -1 : 1, this.atkId * 10 + wi, { parryable: true, src: this })) this.hitIds.add(wi);
    });
    if (an.changed && M.on && M.on[an.i] && !this.fired[an.i]) { this.fired[an.i] = true; M.on[an.i].call(this); }
    if (a === 'cast' && an.i === 6 && this.channel > 0) { this.channel -= dt; an.hold(); if (Math.random() < 0.4) { const p = this.pt('chest'); particles.push({ x: p.x + rand(-20, 20), y: p.y + rand(-20, 20), vx: 0, vy: -20, life: 0.4, kind: 'ink' }); } }
    if (an.done) this.atkDone();
  }
  atkDone() {
    if (this.pendingPhase) return this.enterPhase2();
    const a = this.atk, v = this.variant;
    if (a === 'sink') {
      this.state = 'sunk'; this.hidden = true; this.riseT = 0;
      const behind = P.x - (P.face || 1) * rand(60, 90), other = P.x + (P.face || 1) * rand(80, 110);
      this.tx = clamp(behind > this.L + 10 && behind < this.R - 10 ? behind : other, this.L + 10, this.R - 10);
      this.ambush = this.phase === 2 || Math.random() < 0.5; return;
    }
    this.state = 'idle'; this.anim.set('idle', true); this.altSpd = 70; this.altT = 14; this.vx = 0;
    this.cool = this.phase === 1 ? rand(...this.cool1) : rand(...this.cool2);
    if (a === 'rise' && this.ambush && Math.abs(P.x - this.x) < 130) { this.ambush = false; return this.start('reap'); }
    if (v === 'spiral') { this.altT = 6; this.cool += 1.0; this.tired = true; }       // spent: it sinks low -- the punish window
    if (a === 'reap') this.cool += 0.2;
    if (this.phase === 2 && (v === 'fan' || v === 'tendrils') && a !== 'rise' && !this.chained && Math.random() < 0.4) { this.chained = true; return this.start(v === 'fan' ? 'tendrils' : 'quills'); }
    this.chained = false;
  }
  // ---- patterns
  castPattern() {
    const v = this.variant, p2 = this.phase === 2, red = p2;
    if (v === 'fan') {
      const volleys = p2 ? 4 : 3, n = p2 ? 7 : 5, spread = (p2 ? 12 : 14) * Math.PI / 180, spd = p2 ? 160 : 140;
      for (let k = 0; k < volleys; k++) this.later(k * (p2 ? 0.3 : 0.42), function () {
        const p = metaPoint(this.sh, this, this.sh.meta.spawn.cast.at), a0 = Math.atan2(P.y - 14 - p.y, P.x - p.x) + (k % 2 ? spread / 2 : 0);
        for (let i = 0; i < n; i++) { const a = a0 + (i - (n - 1) / 2) * spread; inkBolt(p.x, p.y, Math.cos(a) * spd, Math.sin(a) * spd, { red }); }
        sfx.bolt(); inkSplash(p.x, p.y, red);
      });
    } else if (v === 'quills') {
      const n = p2 ? 6 : 4, c = this.pt('chest');
      for (let k = 0; k < n; k++) {
        const a = -Math.PI * (0.15 + 0.7 * k / (n - 1)), ox = Math.cos(a) * 46, oy = Math.sin(a) * 34 - 20;
        INK.b.push({ kind: 'quill', x: c.x + ox, y: c.y + oy, ox, oy: oy - 0, follow: null, vx: 0, vy: 0, t: 0, aim: 0.6 + k * 0.14, homeT: 0.85, turn: p2 ? 2.8 : 2.3,
                     spd: 80, acc: 520, vmax: p2 ? 270 : 240, life: 4, r: 4, dmg: BOSS_DMG * 28 * NGP.dmg, id: ++hazardId, red, ang: -Math.PI / 2 });
      }
      sfx.charge();
    } else if (v === 'spiral') {
      const dur = p2 ? 2.8 : 2.2; this.channel = dur;
      const sets = p2 ? [[3, 1.25], [3, -1.25]] : [[4, 1.05]], rate = p2 ? 0.2 : 0.17, spd = p2 ? 100 : 90;
      let rot = rand(0, 6.28);
      for (let t = 0, i = 0; t < dur; t += rate, i++) this.later(t, function () {
        const c = this.pt('chest');
        if (i % 4 === 3) return;   // every fourth beat is left blank: a readable gap in each arm to slip through
        sets.forEach(([arms, w], si) => { for (let k = 0; k < arms; k++) { const a = rot * Math.sign(w) + i * rate * w + k * 2 * Math.PI / arms + si * 0.5; inkBolt(c.x, c.y, Math.cos(a) * spd, Math.sin(a) * spd, { red, life: 6, dmg: 22 }); } });
        if (i % 3 === 0) sfx.bolt();
      });
    }
  }
  writeSpawn() {
    const v = this.variant, p2 = this.phase === 2, s = metaPoint(this.sh, this, this.sh.meta.spawn.write.at), fl = this.floor;
    shake = Math.max(shake, 6); sfx.boom(); ar2Burst(s.x, fl, p2);
    if (v === 'tendrils') {
      if (!p2) { const xs = [P.x, P.x - 62, P.x + 62]; xs.forEach((x, k) => inkTendril(clamp(x, this.L - 10, this.R + 10), fl, k ? 0.3 : 0, false)); }
      else {
        const dir = sign(P.x - s.x) || this.face;
        for (let k = 1; k <= 9; k++) { const x = s.x + dir * (24 + k * 34); if (x > TILE && x < room.pw - TILE) inkTendril(x, fl, k * 0.09, true); }
        inkTendril(clamp(P.x, this.L, this.R), fl, 0.45, true);
      }
    } else if (v === 'blot') {
      // the whole floor floods: written platforms spread across the arena first, one short jump above the floor
      const tele = p2 ? 1.5 : 1.8, dur = p2 ? 3.6 : 3.2, row = Math.floor(fl / TILE) - 3, n = 6;
      const lo = TILE + 8, hi = room.pw - TILE - 8 - 48;
      const lefts = []; for (let k = 0; k < n; k++) lefts.push(Math.round(lo + k * (hi - lo) / (n - 1)));
      if (p2) lefts.push(Math.round((lefts[1] + lefts[2]) / 2), Math.round((lefts[3] + lefts[4]) / 2));
      lefts.forEach((left, k) => {
        const upper = k >= n, dly = 0.08 + Math.abs(left + 24 - s.x) / 900 + (upper ? 0.3 : 0);
        inkPlat(left, row - (upper ? 3 : 0), tele + dur + 0.9 - dly, dly);
      });
      inkFlood(TILE, room.pw - TILE, s.x, tele, dur, p2);
      this.blotCd = p2 ? 11 : 14;
      if (!SAVE.hints.ar2_blot) { SAVE.hints.ar2_blot = 1; this.later(0.3, () => toast('The ink is rising — get onto the written platforms!', 3)); }
    } else if (v === 'pages') {
      throwPages(this, 6);
    }
  }
  enterPhase2() {
    this.phase = 2; this.speed = this.p2speed; this.pendingPhase = false; this.stance = 0; this.hidden = false; this.channel = 0;
    this.sched = []; this.sh = this.sheetsArr[1].ok ? this.sheetsArr[1] : this.sh; this.facePlayer(); this.altT = 10; this.altSpd = 80;
    flashScreen = 0.8; shake = 10; sfx.roar();
    const c = this.pt('chest'); invStart(true, c.x, c.y);
    this.startTag('transform');
    bossPhase2Scene(this);
  }
  stagger() { this.channel = 0; this.sched = []; this.hidden = false; this.alt = this.altT = 0; this.altSpd = 120; super.stagger(); }
  die() {
    this.hidden = false; this.altT = 0; this.alt = 0; this.sched = [];
    INK.b = []; INK.floods = []; for (const p of INK.plats) p.life = Math.min(p.life, p.t + 0.2); for (const p of INK.pages) p.gone = true;
    super.die();
    this.y = this.floor;
    if (INV.room === room) { INV.target = 0; INV.cx = this.x; INV.cy = this.y - 70; }
    INK.stairT = 5.2;   // game time: the spilled ink writes a stair once the victory banner has passed
  }
  ambient(dt) {
    if (this.hidden || !this.alive) return;
    const red = this.phase === 2, e = this.pt('eye');
    addLight(e.x, e.y, 50, red ? '255,110,70' : '170,140,255', 0.9);
    addLight(this.x, this.y - 70, 150, red ? '220,90,60' : '140,120,220', 0.9);
    if (Math.random() < 0.35) particles.push({ x: this.x + rand(-26, 20) - this.face * 10, y: this.y - rand(0, 30), vx: -this.face * rand(5, 20), vy: rand(10, 30), life: 0.7, kind: red ? 'fire' : 'ink' });
  }
  draw() {
    if (this.hidden) return;
    super.draw();
  }
}
const UW_MOVES = {
  reap: { on: { 6() { const p = metaPoint(this.sh, this, [this.sh.meta.attacks.reap.rects['6'][0] + 20, this.sh.fh - 4]); inkSplash(p.x, this.floor - 4, this.phase === 2); shake = Math.max(shake, 5); } } },
  cast: { on: { 5() { this.castPattern(); } } },
  write: { on: { 3() { sfx.bossSwing(); }, 4() { this.writeSpawn(); } } },
  sink: { on: { 1() { ar2Burst(this.x, this.floor, this.phase === 2); sfx.fire(); } } },
  rise: { on: { 4() { shake = Math.max(shake, 3); } } },
  transform: { on: { 4() { flashScreen = 0.6; shake = 8; } } },
};
function ar2Burst(x, y, red) { const f = spawnFx('ink_burst', x, y, 1, null, { bottom: true }); if (f && red) f.anim.set('r', false); }
BOSS_SPAWN.unwritten = (cx, fy) => sheet('unwritten').ok ? new Unwritten(cx, fy) : null;

// ================================================================== cutscenes
BOSS_CUTS.unwritten = b => {
  const bk = props.find(p => p.type === 'ar2_book'), bx = bk ? bk.x : b.x + 40;
  return [
    act(() => { b.hidden = true; b.alt = b.altT = 0; b.y = b.floor; if (bk) bk.anim.set('idle', true); }),
    { pan: { x: bx - 30, y: b.floor - 70 }, dur: 1.1 },
    act(() => { if (bk) bk.anim.set('bleed', false); sfx.fire(); shake = 2; for (let i = 0; i < 16; i++) particles.push({ x: bx + rand(-6, 6), y: b.floor - 30 - rand(0, 10), vx: rand(-20, 20), vy: -rand(10, 40), life: 1, kind: 'ink' }); }),
    wait(1.1),
    { do() { b.hidden = false; b.x = bx - 38; b.face = -1; b.alt = b.altT = 0; b.y = b.floor; b.anim.set('rise', false); ar2Burst(b.x, b.floor, false); sfx.roar(); shake = 5; if (bk) bk.anim.set('empty', false); }, always: true },
    wait(1.0),
    act(() => { b.anim.set('idle', true); }),
    say('The Unwritten', '“…and the Root fell. And no one wrote down why.”'),
    say('The Unwritten', F('s_met') ? '“The Scribe gave me every page but the last. You will do for an ending.”' : '“A reader. Hold still — I will write you in.”'),
    act(() => { holdAnim(b, 'cast'); }), wait(0.6),
    act(() => { flashScreen = 0.5; shake = 7; sfx.roar(); const p = b.pt('eye'); spawnFx('roar_ring', p.x, p.y, 1); }), wait(0.8),
  ];
};
PHASE2_LINES.unwritten = ['The Unwritten', '“Then I turn the page — and you with it.”'];

// ================================================================== props: the Scribe's book, the hidden folio
const AR2_BOOK_LORE = ['The Scribe’s unfinished book. Its last chapter is titled only “The Root”.',
  'Every line after the first has been drunk dry, as if something fed on the ink.',
  'One note survives in the margin: “I could not give it an ending. So it went looking for one.”'];
const AR2_FOLIO_LORE = ['A folio bound in black root-bark, hidden above the Inkwell. The hand is the Scribe’s.',
  '“I wrote the Root’s story to keep it alive — every name, every prayer, every fall. I wrote until the ink began to write back.”',
  '“A story with no ending grows hungry. It eats the names of those who read it. Forgive me, reader. I only wanted it to go on.”'];
SPAWNS.ar2_book = (s, c) => {
  const sh = sheet('ar2_book'), seen = SAVE.flags['cut:unwritten'] || SAVE.flags['boss:unwritten'];
  props.push({ type: 'ar2_book', x: c.cx, y: c.fy, face: -1, sh, anim: new Anim(sh, seen ? 'empty' : 'idle', !seen),
    lore: AR2_BOOK_LORE, canRead: () => !!SAVE.flags['boss:unwritten'],
    update() { addLight(this.x, this.y - 30, 40, '170,140,255', this.anim.tag === 'empty' ? 0.3 : 0.7); if (this.anim.tag === 'bleed' && Math.random() < 0.4) particles.push({ x: this.x + rand(-8, 8), y: this.y - 22, vx: 0, vy: -rand(10, 30), life: 0.6, kind: 'ink' }); },
    draw() { if (sh.ok) drawSprite(sh, this.anim.frame, this.x, this.y, 1, { bottom: true }); } });
};
SPAWNS.ar2_lore = (s, c) => {
  const sh = sheet('prop_lectern');
  props.push({ type: 'ar2_lore', x: c.cx, y: c.fy, face: 1, sh, anim: new Anim(sh, 'loop', true), lore: AR2_FOLIO_LORE,
    update() { addLight(this.x, this.y - 20, 50, '200,170,255', 0.8); },
    draw() { if (sh.ok) drawSprite(sh, this.anim.frame, this.x, this.y, 1, { bottom: true }); } });
};
function ar2Readable() {
  if (!P || !P.ground) return null;
  for (const p of props) if (p.lore && (!p.canRead || p.canRead()) && Math.abs(p.x - P.x) < 18 && Math.abs(p.y - P.y) < 24) return p;
  return null;
}

// ================================================================== falling shelves (Archives hazard): hanging cages drop, bookcases topple
const sfxCreak = () => { tone(72, 0.55, 0.12, 'sawtooth', 1.35); noise(0.45, 380, 2.5, 0.14, 'bandpass', 1.8); };
function floorBelow(x, y) {   // px y of the first floor (solid or one-way) under (x, y)
  for (let ty = Math.floor(y / TILE); ty < room.h; ty++) { const t = tileAt(Math.floor(x / TILE), ty); if (isSolidT(t) || t === T_PLAT) return ty * TILE; }
  return room.ph;
}
function crushEnemies(r, dir) {
  for (const e of enemies) { if (!e.alive) continue; const hb = e.hurtbox && e.hurtbox(); if (hb && overlap(r, hb)) e.hit({ dmg: 140, poise: 80, dir, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, big: true, melee: false }); }
}
function shelfDebris(x, y, n = 18) {
  for (let i = 0; i < n; i++) particles.push({ x: x + rand(-18, 18), y: y - rand(0, 12), vx: rand(-110, 110), vy: -rand(40, 170), g: 420, life: rand(0.6, 1.2), kind: Math.random() < 0.5 ? 'rock' : 'dust' });
}
SPAWNS.ar2_cage = (s, c) => {
  const sh = sheet('prop_shelfcage'), top = s.y * TILE, fl = floorBelow(c.cx, top + 50);
  props.push({ type: 'ar2_cage', x: c.cx, y: top, st: 'hang', t: 0, vy: 0, sh, anim: new Anim(sh, 'idle', false), id: ++hazardId,
    update(dt) {
      this.t += dt;
      if (this.st === 'hang' && P.state !== 'dead' && Math.abs(P.x - this.x) < 30 && P.y > this.y + 40 && P.y <= fl + 2) {
        this.st = 'creak'; this.t = 0; sfxCreak();
      } else if (this.st === 'creak') {
        if (Math.random() < 0.5) particles.push({ x: this.x + rand(-10, 10), y: this.y + rand(0, 4), vx: rand(-6, 6), vy: rand(20, 50), g: 150, life: 1, kind: 'dust' });
        if (this.t > 0.6) { this.st = 'fall'; this.t = 0; noise(0.15, 1800, 1, 0.2, 'highpass'); }
      } else if (this.st === 'fall') {
        this.vy = Math.min(560, this.vy + 900 * dt); this.y += this.vy * dt;
        const r = rect(this.x - 13, this.y + 6, this.x + 13, this.y + 46);
        if (overlap(r, playerHurtbox())) hurtPlayer(38 * NGP.dmg, P.x < this.x ? -1 : 1, this.id);
        crushEnemies(r, 1);
        if (this.y + 48 >= fl) {
          this.y = fl - 48; this.st = 'down'; shake = Math.max(shake, 6); sfx.crumble(); sfx.boom(); shelfDebris(this.x, fl);
          const rr = rect(this.x - 22, fl - 20, this.x + 22, fl);
          if (overlap(rr, playerHurtbox())) hurtPlayer(38 * NGP.dmg, P.x < this.x ? -1 : 1, this.id);
          crushEnemies(rr, 1);
        }
      }
    },
    draw() {
      if (!sh.ok) return;
      const jig = this.st === 'creak' ? Math.round(Math.sin(this.t * 60)) : 0;
      drawSprite(sh, sh.first('idle'), this.x + jig, this.y, 1, { pivot: [Math.floor(sh.fw / 2), 0], rot: this.st === 'down' ? 0.12 : 0 });
    } });
};
SPAWNS.ar2_topple = (s, c) => {
  const sh = sheet('ar2_bookshelf');
  props.push({ type: 'ar2_topple', x: c.cx, y: c.fy, st: 'stand', t: 0, ang: 0, av: 0, dir: 1, sh, anim: new Anim(sh, 'idle', false), id: ++hazardId,
    update(dt) {
      this.t += dt;
      if (this.st === 'stand' && P.state !== 'dead' && Math.abs(P.x - this.x) < 60 && Math.abs(P.y - this.y) < 24) {
        this.st = 'creak'; this.t = 0; this.dir = P.x < this.x ? -1 : 1; this.anim.set('creak', true); sfxCreak();
      } else if (this.st === 'creak') {
        this.ang = this.dir * 0.05 * Math.max(0, Math.sin(this.t * 22)) * (0.5 + this.t);   // rocking, toward you
        if (Math.random() < 0.6) particles.push({ x: this.x + rand(-12, 12), y: this.y - 60 + rand(-2, 2), vx: rand(-8, 8), vy: rand(10, 40), g: 160, life: 0.9, kind: 'dust' });
        if (this.t > 0.7) { this.st = 'fall'; this.t = 0; this.ang = this.dir * 0.08; this.av = this.dir * 0.8; sfxCreak(); }
      } else if (this.st === 'fall') {
        this.av += this.dir * 16 * dt; this.ang += this.av * dt;
        const a = Math.abs(this.ang);
        for (let k = 16; k <= 62; k += 8) {   // the falling top sweeps an arc: every point along it can hit
          const px = this.x + Math.sin(this.ang) * k, py = this.y - Math.cos(this.ang) * k;
          const r = rect(px - 6, py - 6, px + 6, py + 6);
          if (overlap(r, playerHurtbox())) hurtPlayer(34 * NGP.dmg, this.dir, this.id);
          if (a > 1.2) crushEnemies(r, this.dir);
        }
        if (a >= Math.PI / 2) {
          this.ang = this.dir * Math.PI / 2; this.st = 'down'; this.anim.set('idle', false); shake = Math.max(shake, 7); sfx.crumble(); sfx.boom();
          shelfDebris(this.x + this.dir * 36, this.y, 24);
        }
      }
    },
    draw() { if (sh.ok) drawSprite(sh, this.anim.frame, this.x, this.y, 1, { pivot: [16, 64], rot: this.ang }); } });
};

// ================================================================== A6: sealed shaft, the ink stair
const AR2_STAIRS = [[9, 12], [5, 9], [5, 6], [5, 4]];
function ar2Stairs(instant) {
  if (!room || room.id !== 'A6' || INK.stairs) return;
  INK.stairs = true;
  AR2_STAIRS.forEach(([c, r], i) => { const p = inkPlat(c * TILE, r, 1e9, instant ? 0 : i * 0.35, true); if (instant) p.t = 1; });
}

// ================================================================== hooks
HOOKS.enter.push(def => {
  INK.b = []; INK.floods = []; INK.pages = []; INK.drift = []; INK.plats = []; INK.stairs = false; INK.pageCd = 0; INK.stairT = 0;
  INV.room = null; INV.orig = null; INV.k = INV.target = 0; AREAS.archives.ambient = AR2_AMB;
  if (def.id !== 'A6') return;
  if (!SAVE.flags['boss:unwritten']) {
    room.dyn.push({ x0: 5 * TILE, x1: 8 * TILE, y0: 0, y1: 4 * TILE, on: () => !SAVE.flags['boss:unwritten'] });
    if (!SAVE.hints.ar2_a6) { SAVE.hints.ar2_a6 = 1; setTimeout(() => toast('Ink seeps across the floor, toward an open book.', 4), 1400); }
  } else ar2Stairs(true);
});
HOOKS.update.push(dt => {
  if (room && room.id === 'A6') {
    const B = boss && boss.kind === 'unwritten' ? boss : null;
    updateInkBullets(dt); updateInkPlats(dt); updateInkFloods(dt); updateInkPages(dt, B); updateDrift(dt);
    if (INK.stairT > 0 && (INK.stairT -= dt) <= 0) { ar2Stairs(false); toast('The spilled ink writes a stair into the dark above.', 3.5); }
  }
  // reading lecterns / the book
  if (state === 'play' && free() && peek('interact')) { const p = ar2Readable(); if (p) { take('interact'); startDialogue(p.lore.map(t => ({ t, lore: true })), null); } }
  // Librarian's Lantern: a wide light that the dark cannot snuff; weak walls glimmer nearby
  if (charmOn('c_lantern') && P && P.state !== 'dead') {
    lights.push({ x: P.x, y: P.y - 18, r: 170, color: '255,214,150', k: 0.7, snuffProof: true });
    INK.weak = [];
    const tx0 = Math.floor(P.x / TILE), ty0 = Math.floor((P.y - 12) / TILE);
    for (let ty = ty0 - 6; ty <= ty0 + 6; ty++) for (let tx = tx0 - 9; tx <= tx0 + 9; tx++) {
      if (tx < 0 || ty < 0 || tx >= room.w || ty >= room.h || room.grid[ty * room.w + tx] !== T_BREAK) continue;
      INK.weak.push([tx, ty]);
      lights.push({ x: tx * TILE + 8, y: ty * TILE + 8, r: 24, color: '255,200,120', k: 0.3 + 0.12 * Math.sin(time * 3 + tx + ty), snuffProof: true });
    }
  } else INK.weak = null;
});
HOOKS.render.push(() => {
  if (room && room.id === 'A6') {
    renderInversion();
    if (!SAVE.flags['boss:unwritten']) {   // the shaft to the Unbound Folio, sealed with a skin of ink
      for (let x = 5 * TILE; x < 8 * TILE; x++) { const w = Math.sin(time * 2 + x * 0.4) * 1.5; g.fillStyle = 'rgba(12,9,20,0.95)'; g.fillRect(x, 0, 1, 58 + w); g.fillStyle = 'rgba(138,105,216,0.6)'; g.fillRect(x, Math.round(58 + w), 1, 1); }
    }
    drawInkFloods(); drawInkPlats();
    const B = boss && boss.kind === 'unwritten' ? boss : null;
    if (B && B.state === 'sunk') {   // the ripple of the travelling ink, and where it will surface
      const k = (B.riseT || 0) / 0.45, red = B.phase === 2;
      g.fillStyle = `rgba(${inkCol(red)},0.7)`;
      for (let i = -6; i <= 6; i++) g.fillRect(Math.round(B.x + i * 2), Math.round(B.floor - 1 - Math.max(0, 3 - Math.abs(i) * 0.5) * (0.6 + 0.4 * Math.sin(time * 20 + i))), 2, 1);
      if (k > 0) { g.fillStyle = `rgba(10,7,16,0.9)`; g.beginPath(); g.ellipse(Math.round(B.x), B.floor - 1, 10 + 16 * k, 2.5, 0, 0, 6.3); g.fill(); g.strokeStyle = `rgba(${inkCol(red)},${0.5 + 0.4 * Math.sin(time * 30)})`; g.lineWidth = 1; g.stroke(); }
    }
    drawInkPages(); drawInkBullets();
  }
  if (INK.weak) for (const [tx, ty] of INK.weak) {   // faint golden cracks in weak walls
    const a = 0.22 + 0.12 * Math.sin(time * 3 + tx * 1.7 + ty), x = tx * TILE, y = ty * TILE;
    g.fillStyle = `rgba(255,210,130,${a})`;
    g.fillRect(x + 4, y + 3, 1, 5); g.fillRect(x + 5, y + 7, 4, 1); g.fillRect(x + 9, y + 8, 1, 4); g.fillRect(x + 10, y + 11, 3, 1); g.fillRect(x + 3, y + 12, 3, 1);
  }
});
HOOKS.hud.push(() => {
  if (state !== 'play' || nearbyPrompt()) return;
  const p = ar2Readable(); if (!p) return;
  const sx = P.x - cam.x, sy = P.y - cam.y - 38, tw = textW('E  Read', 6.5) + 10;
  box(sx - tw / 2, sy - 8, tw, 11, 0.7);
  text('E', sx - tw / 2 + 5, sy, 6.5, '#e6c77a', 'left'); text('Read', sx - tw / 2 + 13, sy, 6.5, '#e8dcc0', 'left', { weight: 500 });
});
HOOKS.death.push(() => { INK.b = []; INK.pages.forEach(p => { if (p.mode !== 'orbit') p.gone = true; }); });
try { window.__ar2 = { INK, INV, get hz() { return hazards; } }; } catch (e) {}   // debug handle for automated tests
