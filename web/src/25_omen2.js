// ------------------------------------------------------------------ Morvain, phase 2 (agent M): the Throne of Ash dissolves into the Eclipsed Crown
// At half health a ring of light spreads from Morvain's heart; inside it the hall burns away (ceiling, upper walls, the
// back wall) and the sky beyond is a black sun wearing a crown of light (bg_omen_far / bg_omen_mid). Two colossal
// echoes of Morvain rise behind the arena and the Crown itself fights: lane sweeps by the colossi, eclipse beams,
// falling crown shards, spear volleys from the spectral choir on the far ledge. The director interleaves these with
// Morvain's own strings (omBgCall is also triggered by his invoke and by your flask use).
PHASE2_LINES.omen = ['Morvain', 'Kneel beneath the black sun. My brothers never left this hall.'];

const OM2_AMB = AREAS.cathedral.ambient;
const OM2 = { k: 0, target: 0, R: 0, room: null, orig: null, alt: null, cb: null, cf: null, cx: 0, cy: 0, last: 0,
              bg: [], cd: 0, lastBg: null, glint: 0, sun: 0, sink: 0,
              col: [{ side: -1, wx: 70, tag: 'idle', t: 0 }, { side: 1, wx: 698, tag: 'idle', t: 1.3 }] };
const omB = () => (boss && boss.kind === 'omen' ? boss : null);
function omFrame(sh, tag, t, loop = true) {
  const tg = sh.tag(tag); let ms = t * 1000, f = tg.from, tot = 0;
  for (let i = tg.from; i <= tg.to; i++) tot += sh.frames[i].ms;
  if (loop && tot > 0) ms %= tot;
  while (f < tg.to && ms >= sh.frames[f].ms) { ms -= sh.frames[f].ms; f++; }
  return f;
}

// ================================================================== the hall burns away
function omBuildAlt() {
  const mk = () => { const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
  const [bc, bx] = mk(), [fc, fx2] = mk();
  // back wall: only the base of the throne hall survives, gilded by the eclipse
  bx.drawImage(room.back, 0, 0);
  bx.globalCompositeOperation = 'destination-in';
  const gr = bx.createLinearGradient(0, 0, 0, room.ph);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.66, 'rgba(0,0,0,0)'); gr.addColorStop(0.76, 'rgba(0,0,0,0.6)'); gr.addColorStop(0.8, 'rgba(0,0,0,0.9)');
  bx.fillStyle = gr; bx.fillRect(0, 0, room.pw, room.ph);
  bx.globalCompositeOperation = 'source-atop'; bx.fillStyle = 'rgba(255,160,70,0.14)'; bx.fillRect(0, 0, room.pw, room.ph);
  // terrain: the vault and the upper walls crumble away along a broken edge
  fx2.drawImage(room.front, 0, 0);
  fx2.globalCompositeOperation = 'destination-out';
  const cut = 5 * TILE;
  for (let x = 0; x < room.pw; x += 2) fx2.fillRect(x, 0, 2, cut - 8 + Math.floor(hash2(x >> 1, 7) * 12) + ((x >> 4) % 3 === 0 ? 5 : 0));
  fx2.globalCompositeOperation = 'source-atop'; fx2.fillStyle = 'rgba(255,150,60,0.1)'; fx2.fillRect(0, 0, room.pw, room.ph);
  fx2.globalCompositeOperation = 'source-over';
  const d = fx2.getImageData(0, 0, room.pw, 8 * TILE), a = d.data;
  for (let x = 0; x < room.pw; x++) for (let y = 0; y < 8 * TILE; y++) {   // gilded lip on each broken top
    const i = (y * room.pw + x) * 4;
    if (a[i + 3]) { a[i] = 255; a[i + 1] = 214; a[i + 2] = 120; if (y + 1 < 8 * TILE) { const j = i + room.pw * 4; if (a[j + 3]) { a[j] = 178; a[j + 1] = 120; a[j + 2] = 50; } } break; }
  }
  fx2.putImageData(d, 0, 0);
  return { back: bc, front: fc };
}
function omPhase2Begin(b) {
  if (!room || room.id !== 'K4') return;
  if (OM2.room !== room) {
    OM2.room = room; OM2.orig = { back: room.back, front: room.front }; OM2.alt = omBuildAlt();
    const mk = () => { const c = document.createElement('canvas'); c.width = room.pw; c.height = room.ph; return c; };
    OM2.cb = mk(); OM2.cf = mk();
  }
  OM2.target = 1; OM2.cx = b.x; OM2.cy = b.y - 70; OM2.last = time; OM2.cd = 3.2; OM2.bg = []; OM2.sink = 0;
  sfx.charge(); sfx.roar();
}
function omPhase2End(b) {
  OM2.bg = []; OM2.target = 0; OM2.cx = b.x; OM2.cy = b.y - 60; OM2.sink = 0.001;
}
function omAdvance() {   // runs from both update and render so the reveal also plays on during the phase-2 scene
  if (OM2.room !== room || !OM2.orig) return;
  const dt = clamp(time - OM2.last, 0, 0.25); OM2.last = time;
  if (OM2.k !== OM2.target) OM2.k = approach(OM2.k, OM2.target, dt * (OM2.target ? 0.5 : 0.3));
  if (OM2.sink > 0) OM2.sink = Math.min(1, OM2.sink + dt * 0.35);
  AREAS.cathedral.ambient = lerp(OM2_AMB, 0.38, OM2.k);
}
function omRenderReveal() {
  if (OM2.room !== room || !OM2.orig) return;
  omAdvance();
  const R = OM2.R = OM2.k * Math.hypot(room.pw, room.ph);
  if (OM2.k <= 0) { room.back = OM2.orig.back; room.front = OM2.orig.front; return; }
  // lanterns hanging from the vanished vault fall away as the ring reaches them
  for (const p of props) if (p.type === 'lantern' && !p.omGone && Math.hypot(p.x - OM2.cx, p.y - OM2.cy) < R) {
    p.omGone = true; for (let i = 0; i < 16; i++) particles.push({ x: p.x + rand(-4, 4), y: p.y + rand(0, 30), vx: rand(-30, 30), vy: -rand(0, 40), g: 120, life: rand(0.6, 1.2), kind: 'gold' });
  }
  if (props.some(p => p.omGone)) props = props.filter(p => !p.omGone);
  if (OM2.k >= 1) { room.back = OM2.alt.back; room.front = OM2.alt.front; return; }
  for (const [dst, o, n] of [[OM2.cb, OM2.orig.back, OM2.alt.back], [OM2.cf, OM2.orig.front, OM2.alt.front]]) {
    const x = dst.getContext('2d'); x.clearRect(0, 0, dst.width, dst.height); x.drawImage(o, 0, 0);
    x.save(); x.beginPath(); x.arc(OM2.cx, OM2.cy, Math.max(0.5, R), 0, 6.3); x.clip(); x.clearRect(0, 0, dst.width, dst.height); x.drawImage(n, 0, 0); x.restore();
  }
  room.back = OM2.cb; room.front = OM2.cf;
  // the burning edge of the eclipse
  g.strokeStyle = 'rgba(255,214,120,0.85)'; g.lineWidth = 2; g.beginPath(); g.arc(OM2.cx, OM2.cy, Math.max(1, R), 0, 6.3); g.stroke();
  if (R > 5) { g.strokeStyle = 'rgba(255,250,220,0.5)'; g.lineWidth = 1; g.beginPath(); g.arc(OM2.cx, OM2.cy, R - 4, 0, 6.3); g.stroke(); }
  for (let i = 0; i < 6; i++) { const a = rand(0, 6.28); particles.push({ x: OM2.cx + Math.cos(a) * R, y: OM2.cy + Math.sin(a) * R, vx: 0, vy: -rand(10, 40), life: rand(0.4, 0.9), kind: 'gold' }); }
}

// ================================================================== the sky (drawn in the parallax pass, behind everything)
function omLayer(sh, fac, vfac, alpha = 1) {
  if (!sh.ok) return null;
  const t = sh.tag('loop'), f = sh.frames[t.from];
  const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20)) + (H - f.h);
  g.globalAlpha = alpha;
  for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy, f.w, f.h);
  g.globalAlpha = 1;
  return { ox, oy, w: f.w };
}
function omDrawSky() {
  g.fillStyle = '#07050c'; g.fillRect(0, 0, W, H);
  const far = omLayer(sheet('bg_omen_far'), 0.05, 0.02);
  if (far && OM2.sun > 0) {   // the black sun flares before its beams
    for (const sx of [far.ox + 212, far.ox + 212 + far.w]) {
      const sy = far.oy + 58, r = 40 + 30 * OM2.sun;
      const gr = g.createRadialGradient(sx, sy, 20, sx, sy, r);
      gr.addColorStop(0, `rgba(255,236,170,${0.7 * OM2.sun})`); gr.addColorStop(1, 'rgba(255,180,80,0)');
      g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.fillRect(sx - r, sy - r, r * 2, r * 2); g.globalCompositeOperation = 'source-over';
      g.fillStyle = '#030206'; g.beginPath(); g.arc(sx, sy, 25, 0, 6.3); g.fill();
    }
  }
  // the colossal echoes rise behind the far ledge
  const cs = sheet('omen_colossus', { native: -1 });
  if (cs.ok) {
    const rise = clamp((OM2.k - 0.25) / 0.75, 0, 1), off = (1 - Math.pow(rise, 0.6)) * 230 + OM2.sink * 260;
    for (const c of OM2.col) {
      const sx = W / 2 + (c.wx - (cam.x + W / 2)) * 0.55, sy = H + 104 + off - cam.y * 0.1;
      if (sx < -200 || sx > W + 200) continue;
      const loop = c.tag === 'idle', fr = omFrame(cs, c.tag, c.t, loop);
      drawSprite(cs, fr, sx, sy, -c.side, { alpha: (c.tag === 'idle' ? 0.5 : 0.88) * (1 - OM2.sink) });
      if (c.tag === 'raise' || c.tag === 'swing') { const gr = g.createRadialGradient(sx, sy - 190, 4, sx, sy - 190, 60); gr.addColorStop(0, 'rgba(255,220,140,0.35)'); gr.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = gr; g.fillRect(sx - 60, sy - 250, 120, 120); }
    }
  }
  const mid = omLayer(sheet('bg_omen_mid'), 0.3, 0.08);
  if (mid && OM2.glint > 0) {   // the spear choir raises its spears: tips flare along the ledge
    for (let x0 = 8, i = 0; x0 < 512; x0 += 22, i++) {
      const lx = x0 + (i % 2) * 4 + Math.max(3, Math.floor((17 + i % 3) / 4)) + 1;
      for (const bx of [mid.ox + lx, mid.ox + lx + mid.w]) {
        if (bx < -4 || bx > W + 4) continue;
        const by = mid.oy + 150 - (17 + i % 3) - 13, a = OM2.glint * (0.6 + 0.4 * Math.sin(time * 30 + i));
        g.fillStyle = `rgba(255,246,210,${a})`; g.fillRect(Math.round(bx) - 2, Math.round(by), 5, 1); g.fillRect(Math.round(bx), Math.round(by) - 3, 1, 7);
        if (i % 3 === 0) addLight(bx + cam.x, by + cam.y, 22, '255,230,160', 0.8 * OM2.glint);
      }
    }
  }
}
const omParallaxBase = drawParallax;
drawParallax = function () {   // (reassigns the engine's parallax pass; see NEEDS in the agent-M report for a hook)
  omParallaxBase();
  if (!room || room.id !== 'K4' || OM2.room !== room || !(OM2.k > 0)) return;
  g.save();
  if (OM2.k < 1) { g.beginPath(); g.arc(OM2.cx - cam.x, OM2.cy - cam.y, Math.max(0.5, OM2.R), 0, 6.3); g.clip(); }
  omDrawSky();
  g.restore();
};

// ================================================================== the Crown fights: background attacks
function omBgCall(kind, o = {}) {
  const B = omB(); if (!B || !B.alive || OM2.k < 0.9) return;
  const fl = B.floor, id = ++hazardId;
  OM2.lastBg = kind;
  if (kind === 'lane') {
    const c = OM2.col[P.x < room.pw / 2 ? 0 : 1];   // the colossus on your side swings across the whole hall
    const low = o.low ?? (Math.random() < 0.55);
    OM2.bg.push({ kind, major: true, t: 0, tele: B.hp < B.maxHp * 0.25 ? 0.95 : 1.15, sweep: 0.42, side: c.side, col: c, low,
                  y0: low ? fl - 22 : fl - 66, y1: low ? fl : fl - 34, id, edge: null });
    c.tag = 'raise'; c.t = 0; omSfx.lane();
    if (!SAVE.hints.om_lane) { SAVE.hints.om_lane = 1; toast('Jump the low sweeps. Stay on the ground under the high ones.', 3.5); }
  } else if (kind === 'beams') {
    OM2.bg.push({ kind, major: true, t: 0, n: B.hp < B.maxHp * 0.25 ? 5 : 4, fired: 0, id }); OM2.sun = 1; omSfx.beam();
  } else if (kind === 'shards') {
    const list = [];
    for (let k = 0; k < 8; k++) list.push({ x: clamp(k === 0 ? P.x : P.x + rand(-160, 160), B.L, B.R), t0: 0.2 + k * 0.14, done: false, id: ++hazardId });
    OM2.bg.push({ kind, major: true, t: 0, list });
    sfx.glint(); shake = Math.max(shake, 2);
  } else if (kind === 'choir') {
    OM2.bg.push({ kind, major: true, t: 0, side: Math.random() < 0.5 ? -1 : 1, fired: false }); OM2.glint = 1; sfx.glint();
  }
}
function omBgPunish() { if (!OM2.bg.some(b => b.major)) omBgCall('beams'); }
function omBgUpdate(dt, B) {
  OM2.glint = Math.max(0, OM2.glint - dt * 0.6); OM2.sun = Math.max(0, OM2.sun - dt * 0.4);
  for (const c of OM2.col) {
    c.t += dt;
    const sh = sheet('omen_colossus', { native: -1 });
    if (c.tag !== 'idle' && sh.ok) { const tg = sh.tag(c.tag); let tot = 0; for (let i = tg.from; i <= tg.to; i++) tot += sh.frames[i].ms; if (c.t * 1000 > tot + (c.tag === 'raise' ? 9999 : 0)) { c.tag = c.tag === 'swing' ? 'recover' : 'idle'; c.t = 0; } }
  }
  for (const e of OM2.bg) {
    e.t += dt;
    if (e.kind === 'lane') {
      if (e.t >= e.tele && e.col.tag === 'raise') { e.col.tag = 'swing'; e.col.t = 0; sfx.bossSwing(); omSfx.blade(); shake = Math.max(shake, 6); }
      const u = (e.t - e.tele) / e.sweep;
      if (u >= 0 && u <= 1) {
        const from = e.side < 0 ? TILE : room.pw - TILE, to = e.side < 0 ? room.pw - TILE : TILE;
        const prev = e.edge ?? from; e.edge = lerp(from, to, u);
        const r = rect(Math.min(prev, e.edge) - 8, e.y0, Math.max(prev, e.edge) + 8, e.y1);
        if (overlap(r, playerHurtbox())) hurtPlayer(BOSS_DMG * 44 * NGP.dmg, -e.side, e.id, { src: B });
        for (let i = 0; i < 3; i++) particles.push({ x: e.edge, y: rand(e.y0, e.y1), vx: -e.side * rand(20, 80), vy: -rand(0, 30), life: 0.4, kind: 'gold' });
        addLight(e.edge, (e.y0 + e.y1) / 2, 70, '255,220,140', 1);
      }
      if (u > 1.9) e.gone = true;
    } else if (e.kind === 'beams') {
      const gap = 0.36;
      while (e.fired < e.n && e.t >= 0.5 + e.fired * gap) {
        const k = e.fired++, x = clamp(k % 2 === 0 ? P.x + (k === 0 ? 0 : rand(-20, 20)) : P.x + (k % 4 === 1 ? 64 : -64), B.L, B.R);
        B.pillar(x, 0.72); OM2.bg.push({ kind: 'ray', t: 0, x, life: 0.72 + 0.35 });
      }
      if (e.fired >= e.n && e.t > 0.5 + e.n * gap + 1) e.gone = true;
    } else if (e.kind === 'ray') {
      if (e.t > e.life) e.gone = true;
    } else if (e.kind === 'shards') {
      for (const s of e.list) {
        if (s.done || e.t < s.t0 + 0.75) continue;
        const fall = (e.t - s.t0 - 0.75) / 0.22;
        if (fall >= 1) {
          s.done = true; shake = Math.max(shake, 2.5); sfx.crumble ? sfx.crumble() : sfx.boom();
          spawnFx(fxOr('shards', 'spear_impact'), s.x, B.floor - 6, 1);
          for (let i = 0; i < 8; i++) particles.push({ x: s.x, y: B.floor - 4, vx: rand(-70, 70), vy: -rand(30, 110), g: 320, life: rand(0.4, 0.7), kind: 'gold' });
          hazards.push({ x: s.x, y: B.floor, w: 18, h: 34, dmg: BOSS_DMG * 34 * NGP.dmg, id: s.id, life: 0.12 });
        }
      }
      if (e.list.every(s => s.done)) e.gone = true;
    } else if (e.kind === 'choir') {
      if (!e.fired && e.t >= 0.9) {
        e.fired = true; sfx.spear();
        const x0 = e.side < 0 ? cam.x + 16 : cam.x + W - 16, n = B.hp < B.maxHp * 0.25 ? 7 : 6;
        for (let k = 0; k < n; k++) B.spear(x0 - e.side * k * 22, Math.max(6, cam.y + 12 + (k % 2) * 10), 0.45 + k * 0.15, { spd: 330, dmg: 26, spread: (k - n / 2) * 4 });
      }
      if (e.t > 3) e.gone = true;
    }
  }
  OM2.bg = OM2.bg.filter(e => !e.gone);
}
function omDirector(dt, B) {
  if (OM2.k < 1 || !B.alive || !B.active || P.state === 'dead') return;
  OM2.cd -= dt;
  if (OM2.cd > 0 || OM2.bg.some(e => e.major)) return;
  if (B.caught || B.state === 'stagger' || B.state === 'roar') return;
  const busy = B.state === 'attack' ? B.atk : null;
  const w = { lane: 1.4, beams: 1.1, shards: 1.0, choir: 1.0 };
  if (busy && ['throw', 'invoke', 'cast', 'ward'].includes(busy)) { w.choir = 0.2; w.beams = 0.4; }   // his own projectiles are already out
  if (OM2.lastBg) w[OM2.lastBg] *= 0.25;
  const e = Object.entries(w); let r = Math.random() * e.reduce((s, [, v]) => s + v, 0), kind = 'lane';
  for (const [k, v] of e) if ((r -= v) <= 0) { kind = k; break; }
  // never ask for opposite answers at once: low moves of his (jump) pair with a low sweep only
  const lowMove = busy && ['sweep', 'plunge', 'rising', 'leap', 'drag', 'flurry', 'counter'].includes(busy);
  omBgCall(kind, kind === 'lane' && lowMove ? { low: true } : {});
  OM2.cd = rand(3.2, 5.0) * (B.hp < B.maxHp * 0.25 ? 0.8 : 1);
}
function omBgDraw(B) {
  const fl = B ? B.floor : room.ph - 3 * TILE;
  for (const e of OM2.bg) {
    if (e.kind === 'lane') {
      const x0 = TILE, x1 = room.pw - TILE, ym = Math.round((e.y0 + e.y1) / 2);
      if (e.t < e.tele) {   // the warning: the lane itself glows, brighter as the colossus winds up
        const k = e.t / e.tele, a = Math.min(1, 0.35 + 0.55 * k + (k > 0.7 ? 0.25 * Math.sin(time * 40) : 0));
        g.fillStyle = `rgba(255,190,90,${0.06 + 0.16 * k})`; g.fillRect(x0, Math.round(e.y0), x1 - x0, Math.round(e.y1 - e.y0));
        for (let x = x0; x < x1; x += 8) { if ((Math.floor(x / 8) + Math.floor(time * 16) * -e.side) % 3 === 0) continue; g.fillStyle = `rgba(255,232,160,${a})`; g.fillRect(x, ym - 1, 5, 2); }
        g.fillStyle = `rgba(255,214,120,${a * 0.6})`; g.fillRect(x0, Math.round(e.y0), x1 - x0, 1); g.fillRect(x0, Math.round(e.y1) - 1, x1 - x0, 1);
        addLight(P.x, ym, 50, '255,210,120', 0.3 + 0.4 * k);
        const sx = e.side < 0 ? x0 : x1 - 1;   // where it comes from
        g.fillStyle = `rgba(255,246,210,${a})`; g.fillRect(sx - 1, Math.round(e.y0), 3, Math.round(e.y1 - e.y0));
      } else if (e.edge != null) {
        const from = e.side < 0 ? x0 : x1, u = clamp((e.t - e.tele) / e.sweep, 0, 2), fade = u > 1 ? Math.max(0, 1 - (u - 1) * 1.2) : 1;
        const lo = Math.min(from, e.edge), hi = Math.max(from, e.edge);
        for (let y = Math.round(e.y0); y < e.y1; y++) {
          const f = Math.abs(y - (e.y0 + e.y1) / 2) / ((e.y1 - e.y0) / 2);
          g.fillStyle = `rgba(255,${Math.round(236 - f * 70)},${Math.round(170 - f * 110)},${(0.75 - f * 0.5) * fade})`;
          g.fillRect(Math.round(lo), y, Math.round(hi - lo), 1);
        }
        if (u <= 1) { g.fillStyle = 'rgba(255,255,240,0.95)'; g.fillRect(Math.round(e.edge) - 2, Math.round(e.y0) - 3, 4, Math.round(e.y1 - e.y0) + 6); }
      }
    } else if (e.kind === 'ray') {   // eclipse beam: a hairline of light from the sky onto its mark
      const k = e.t / 0.72, a = e.t < 0.72 ? 0.25 + 0.5 * k * (0.7 + 0.3 * Math.sin(time * 40)) : Math.max(0, 1 - (e.t - 0.72) * 3);
      const top = Math.round(cam.y);
      g.fillStyle = `rgba(255,236,170,${a})`; g.fillRect(Math.round(e.x), top, 1, fl - top);
      if (e.t < 0.72) { g.fillStyle = `rgba(255,200,110,${a * 0.4})`; g.fillRect(Math.round(e.x) - 3 - Math.round(k * 4), top, 7 + Math.round(k * 8), fl - top); }
      g.strokeStyle = `rgba(255,220,140,${a})`; g.lineWidth = 1; g.beginPath(); g.ellipse(Math.round(e.x), fl - 1, 8 + 8 * (1 - Math.min(1, k)), 2.5, 0, 0, 6.3); g.stroke();
    } else if (e.kind === 'shards') {
      const ss = sheet('fx_om_shard');
      for (const s of e.list) {
        if (s.done || e.t < s.t0) continue;
        const w = e.t - s.t0;
        if (w < 0.75) {   // its shadow and a glint where it will land
          const k = w / 0.75, a = 0.3 + 0.5 * k;
          g.fillStyle = `rgba(10,6,14,${0.3 + 0.4 * k})`; g.beginPath(); g.ellipse(Math.round(s.x), fl - 1, 3 + 7 * k, 2, 0, 0, 6.3); g.fill();
          g.fillStyle = `rgba(255,220,140,${a * (0.6 + 0.4 * Math.sin(time * 30))})`; g.fillRect(Math.round(s.x) - 1, fl - 3, 3, 1);
          g.fillStyle = `rgba(255,226,150,${0.12 + 0.25 * k})`; g.fillRect(Math.round(s.x), Math.round(cam.y), 1, Math.round(fl - cam.y));
          addLight(s.x, fl - 4, 16 + 10 * k, '255,210,120', 0.5);
        } else {
          const fall = Math.min(1, (w - 0.75) / 0.22), y = lerp(cam.y - 30, fl, fall * fall);
          if (ss.ok) drawSprite(ss, ss.tag('fall').from + Math.floor(time * 14) % 4, s.x, y, 1, { bottom: true });
          addLight(s.x, y - 16, 30, '255,220,140', 0.9);
        }
      }
    }
  }
}

// ================================================================== hooks
HOOKS.enter.push(def => {
  OM2.room = null; OM2.orig = null; OM2.alt = null; OM2.k = OM2.target = 0; OM2.R = 0; OM2.bg = []; OM2.sink = 0; OM2.glint = 0; OM2.sun = 0;
  for (const c of OM2.col) { c.tag = 'idle'; c.t = rand(0, 1); }
  AREAS.cathedral.ambient = OM2_AMB;
});
HOOKS.update.push(dt => {
  if (!room || room.id !== 'K4') return;
  const B = omB();
  omAdvance();
  if (B && B.phase === 2) omDirector(dt, B);
  if (OM2.room === room) omBgUpdate(dt, B || { floor: room.ph - 3 * TILE, L: TILE, R: room.pw - TILE, hp: 1, maxHp: 1, alive: false, pillar() {}, spear() {} });
});
HOOKS.render.push(() => {
  if (!room || room.id !== 'K4') return;
  omRenderReveal();
  if (OM2.room === room) omBgDraw(omB());
});
HOOKS.death.push(() => { OM2.bg = []; });
try { window.__om = { OM2, call: omBgCall }; } catch (e) {}   // debug handle for automated tests
