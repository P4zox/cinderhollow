// ------------------------------------------------------------------ v16 FATALITIES: the agile group (agent `fagile`, docs/v16/fagile.md)
// Dual Blades "Crimson Requiem", Staff "Tempest Ascension", Whip "Thunder Leash", Martial Arts "Hundred Embers".
// Choreography on the fatality clock, in step with art/player_v16_fatal_agile.py (frame starts):
//   tw_fatal 0 coil | 90 deep coil | 200 LUNGE (blurs out) | 240..760 GONE (phantoms) | 760 reappear above | 840 hang
//            1000 X opens | 1040 X through | 1090 land low | 1350 rise | 1480 recover | 1600
//   st_fatal 0 plant | 100 push off | 190 VAULT KICK | 250 over | 320..840 four air spins | 840 hang | 1000 flip
//            1040 plunge | 1090 IMPACT | 1420 rise | 1560 recover | 1700
//   wh_fatal 0 coil | 80 cocked | 180 THROW | 230 extended | 360 YANK | 420 haul | 560..920 one turn | 920 arm high
//            1060 CRACK | 1110 low | 1170 hold | 1420 gather | 1570 recover | 1700
//   ft_fatal 0 guard | 120..600 eight Swift palms | 600 ROOT (to Iron) | 680 / 750 / 820 Iron blows | 900 sink
//            1030 ember gather | 1150 BOTH PALMS | 1230 hold | 1480 settle | 1700
// Shared helpers (ag*) stay in this file; nothing in 79_fatality.js is changed.

// ================================================================== helpers
// the target's box in the fatality's move frame (px along the starting facing from the start point; y relative to the start feet)
function agRel(F) {
  const hb = F.tc().hb, f = F.face0, X = x => (x - F.x0) * f;
  return { near: X(f > 0 ? hb.x0 : hb.x1), far: X(f > 0 ? hb.x1 : hb.x0), c: X((hb.x0 + hb.x1) / 2), top: hb.y0 - F.y0, h: hb.y1 - hb.y0, w: hb.x1 - hb.x0, hb };
}
// tween the player to (gx along the starting facing, gy) from wherever it is now (what a `move` step does, with computed goals)
function agMove(F, gx, gy, dur = 120, ease = 'out') {
  F.mv = { fx: (P.x - F.x0) * F.face0, fy: P.y - F.y0, tx: gx, ty: gy, t0: F.t, dur, ease };
}
// tween a SMALL target to (ox along the starting facing from where it began, oy px up) -- the framework's target motion, absolute goals
function agTarget(F, ox, oy, dur = 160, ease = 'out') {
  const t = F.target; if (!F.small || !fatAlive(t)) return;
  let cx = 0, cy = 0;
  if (F.tm) { const k = fatEase(F.tm.ease || 'out', (F.t - F.tm.t0) / Math.max(1, F.tm.dur)); cx = lerp(F.tm.fx, F.tm.tx, F.tm.dur > 0 ? k : 1); cy = lerp(F.tm.fy, F.tm.ty, F.tm.dur > 0 ? k : 1); }
  F.tm = { fx: cx, fy: cy, tx: ox, ty: oy, t0: F.t, dur, ease };
}
// a world point -> the target-motion frame
const agTOx = (F, wx) => (wx - F.tx0) * F.face0;
// pose space (the 64x40 sheet frame, feet on row 39, anchor 28,40) -> world, for the player's current facing
const agPose = (px, py) => ({ x: P.x + P.face * (px + 0.5 - 28), y: P.y + py + 0.5 - 40 });
const agTagFrame = (tag, i) => { const sh = pSheet(); return sh.ok && sh.has(tag) ? Math.min(sh.tag(tag).from + i, sh.tag(tag).to) : P.anim.frame; };
// a jagged lightning path a -> b (seeded): [[x, y], ...]
function agBolt(ax, ay, bx, by, seed, amp = 3, step = 5) {
  const L = Math.hypot(bx - ax, by - ay), n = Math.max(2, Math.round(L / step)), nx = -(by - ay) / (L || 1), ny = (bx - ax) / (L || 1), R = fatRng(seed), pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n, o = i === 0 || i === n ? 0 : (R() - 0.5) * 2 * amp; pts.push([ax + (bx - ax) * u + nx * o, ay + (by - ay) * u + ny * o]); }
  return pts;
}
function agPath(pts) { for (let i = 1; i < pts.length; i++) fatLine(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]); }
// one sprite silhouette (player body + the weapon overlay) in a flat colour, into the current layer
function agSil(f, x, y, face, col, a) {
  if (a <= 0.01) return;
  drawSprite(sheet('player'), f, x, y, face, { alpha: a, flash: 1, flashColor: `rgb(${col})` });
  const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')); if (ws.ok) drawSprite(ws, f, x, y, face, { alpha: a, flash: 1, flashColor: `rgb(${fatHot(col)})` });
}

// ================================================================== DUAL BLADES "Crimson Requiem"
// Coil, lunge -- and the knight is gone: crimson phantoms of him strike through the foe from every angle (each leaves a
// cut of light), a whirl of crimson round it; he reappears tucked above the foe, hangs with both blades crossed, and opens
// them in an X on the dive: a crimson cross that hangs burning in the air, then breaks apart into falling ash.
const TW_PH = [   // [at, dir along the facing, dir y, pose tag, frame]
  [250, 1, 0.08, 'tw_heavy', 3], [330, -0.7, 0.72, 'tw_crossfall', 3], [410, 0.45, -0.9, 'tw_skyward', 2], [490, -1, -0.06, 'tw_heavy', 3],
  [570, 0.65, 0.76, 'tw_crossfall', 3], [640, -0.5, -0.86, 'tw_skyward', 2], [690, 1, -0.3, 'tw_4', 1], [700, -1, -0.3, 'tw_4', 1],
];
function twPhantom(F, i) {
  const [, ux, uy, tag, fi] = TW_PH[i], L = Math.hypot(ux, uy), c = F.tc(), r = agRel(F);
  const dx = ux / L * F.face0, dy = uy / L, R = clamp(Math.max(r.w, r.h) * 0.55 + 16, 26, 62);
  F.fx(twPhantomFx, { life: 230, cx: c.x, cy: c.y, dx, dy, R, f: agTagFrame(tag, fi), face: dx >= 0 ? 1 : -1, len: clamp(Math.hypot(r.w, r.h) * 0.9, 36, 120), seed: i });
  try { noise(0.09, 2600 + i * 180, 1.2, 0.16, 'bandpass', 0.5); tone(1400 - i * 60, 0.08, 0.03, 'triangle', 0.6); } catch (e) {}
}
function twPhantomFx(gx, t, F, e) {
  const o = e.o, mv = fatEase('out', t / 70), fade = t < 70 ? 1 : 1 - (t - 70) / (o.life - 70);
  // the phantom: dashing along its strike line, two echoes behind it
  for (let k = 2; k >= 0; k--) {
    const u = Math.max(0, mv - k * 0.18), px = o.cx + o.dx * o.R * lerp(-1, 0.35, u), py = o.cy + o.dy * o.R * lerp(-1, 0.35, u);
    agSil(o.f, px, py + 17, o.face, F.col, (k ? 0.16 / k : 0.48) * fade * (t < 110 ? 1 : 0.5));
  }
  // the cut: a thin line of light through the foe along the strike, drawn in, held hot, then a dark-red scar
  const L = o.len / 2, x0 = o.cx - o.dx * L, y0 = o.cy - o.dy * L, x1 = o.cx + o.dx * L, y1 = o.cy + o.dy * L;
  if (t < 30) return;
  const k = fatEase('snap', (t - 30) / 40), xe = lerp(x0, x1, k), ye = lerp(y0, y1, k);
  if (t < 120) {
    g.fillStyle = `rgba(${F.col},0.55)`; fatLine(x0, y0 + 1, xe, ye + 1); fatLine(x0 + 1, y0, xe + 1, ye);
    g.fillStyle = `rgba(${fatHot(F.col)},1)`; fatLine(x0, y0, xe, ye);
    if (k < 1) mvStar(xe, ye, 3, fatHot(F.col), 1);
    addLight(o.cx, o.cy, 40, F.col, 0.25);
  } else {
    const a = 1 - (t - 120) / (o.life - 120);
    for (let i = 0, n = Math.ceil(o.len); i <= n; i++) {
      const x = Math.round(lerp(x0, x1, i / n)), y = Math.round(lerp(y0, y1, i / n));
      if (!fatDith(x, y, a * (1 - Math.abs(i / n - 0.5)))) continue;
      g.fillStyle = `rgba(${fatMix(F.col, '90,10,20', 0.4)},${0.8 * a})`; g.fillRect(x, y, 1, 1);
    }
  }
}
// the whirl: crimson arcs wheeling round the foe while the phantoms strike
function twWhirlFx(gx, t, F, e) {
  const o = e.o, c = F.tc(), r = agRel(F), R = clamp(Math.max(r.w, r.h) * 0.55 + 12, 24, 58), env = Math.min(1, t / 80, (o.life - t) / 120);
  for (let j = 0; j < 3; j++) {
    const rx = R * (0.75 + j * 0.16), ry = rx * (0.42 + j * 0.12), ph = t * (0.011 + j * 0.004) * (j % 2 ? -1 : 1) + j * 2.1, span = 1.7 + j * 0.3;
    for (let s = 0; s < 46; s++) {
      const u = s / 45, th = ph + u * span, x = Math.round(c.x + Math.cos(th) * rx), y = Math.round(c.y + Math.sin(th) * ry);
      if (!fatDith(x, y, env * (0.2 + 0.8 * u))) continue;
      g.fillStyle = `rgba(${u > 0.85 ? fatHot(F.col) : F.col},${0.75 * env})`; g.fillRect(x, y, 1, 1);
    }
  }
  addLight(c.x, c.y, R * 1.4, F.col, 0.3 * env);
}
// the crimson cross: two strokes cut in, it burns in the air (flickering edges, licks of flame, embers), then breaks apart
function twCrossFx(gx, t, F, e) {
  const o = e.o; if (!e.c) { const c = F.tc(), r = agRel(F); e.c = { x: Math.round(c.x), y: Math.round(c.y) }; e.L = clamp(r.h * 0.55, 24, 46); e.R = fatRng(F.n * 17 + 5); e.em = 0; }
  const { x: cx, y: cy } = e.c, L = e.L, life = o.life, brk = life - 380;
  const strokes = [[-1, -1, 1, 1, 0], [1, -1, -1, 1, 40]];   // first: from up-back to down-front (facing applied)
  const hot = fatHot(F.col), lite = fatLite(F.col), fl = fatMix(F.col, '255,150,60', 0.45);
  for (const [ax, ay, bx, by, d0] of strokes) {
    const tt = t - d0; if (tt < 0) continue;
    const x0 = cx + ax * L * F.face0, y0 = cy + ay * L, x1 = cx + bx * L * F.face0, y1 = cy + by * L;
    const k = fatEase('snap', tt / 45), n = Math.ceil(L * 2);
    if (t < brk) {
      const burn = clamp((t - 90) / 300, 0, 1), cool = clamp((t - 600) / (brk - 600), 0, 1), w = Math.round(2 - cool);
      for (let i = 0; i <= n * k; i++) {
        const x = Math.round(lerp(x0, x1, i / n)), y = Math.round(lerp(y0, y1, i / n)), fk = fatHash(i, Math.floor(t / 55) + d0);
        g.fillStyle = `rgba(${F.col},${0.7 - 0.3 * cool})`; for (let j = 1; j <= w; j++) { g.fillRect(x, y - j, 1, 1); g.fillRect(x, y + j, 1, 1); }
        g.fillStyle = `rgba(${fk < 0.25 * burn ? fl : (t < 140 || fk > 0.5 ? hot : lite)},1)`; g.fillRect(x, y, 1, 1);
        // licks of flame rising off the bar
        if (burn > 0 && fk > 0.82 - 0.1 * burn) { const h = 2 + Math.floor(((t * 0.02 + i * 0.37) % 1) * 4); for (let q = 2; q < h; q++) if (fatDith(x, y - q, 1 - q / h)) { g.fillStyle = `rgba(${q < 3 ? fl : F.col},${0.8 * (1 - q / h) * (1 - cool * 0.6)})`; g.fillRect(x, y - q - (w > 1 ? 1 : 0), 1, 1); } }
      }
    } else {   // break apart: segments drift and fall, dissolving
      const kb = (t - brk) / 380;
      for (let s = 0; s < n; s += 6) {
        const a0 = s / n, a1 = Math.min(1, (s + 5) / n), off = (fatHash(s, F.n + d0) - 0.5) * 16 * kb, drop = kb * kb * 22 * (0.5 + fatHash(s, 9));
        if (fatHash(s * 3, d0 + 1) < kb * 0.9) continue;
        g.fillStyle = `rgba(${lite},${1 - kb})`;
        fatLine(lerp(x0, x1, a0) + off, lerp(y0, y1, a0) + drop, lerp(x0, x1, a1) + off, lerp(y0, y1, a1) + drop);
      }
    }
  }
  if (t < 220) mvStar(cx, cy, 5 * (1 - t / 220) + 2, hot, 1 - t / 220);
  if (t < brk) {
    // embers shed by the burning cross
    while (e.em < Math.min(26, t / 40)) { e.em++; const u = e.R() * 2 - 1, s = e.R() < 0.5 ? 1 : -1; fatPart({ k: 'ember', x: cx + u * L * F.face0, y: cy + u * L * s, vx: (e.R() - 0.5) * 20, vy: -15 - e.R() * 30, col: fl, life: 0.6 + e.R() * 0.6, max: 1.2, g: -8, ph: e.R() * 6 }); }
    addLight(cx, cy, 80, F.col, 0.6 * (1 - clamp((t - 500) / (brk - 500), 0, 1) * 0.6));
  }
}
fatalityRegister('dual', {
  name: 'Crimson Requiem',
  col: '235,70,80',
  tag: 'tw_fatal', tags: ['tw_heavy', 'riposte'],
  dur: 1600,
  steps: [
    { at: 0, move: { gap: 8, dur: 100 } },
    { at: 95, sfx: () => { sfx.glint(); tone(220, 0.3, 0.05, 'sawtooth', 0.5); } },
    { at: 100, fx: 'soulWisps', o: { anchor: 'player', dy: -16, from: 'ring', r: 30, n: 8, rise: 40, dur: 160, stagger: 10, to: 'player' } },
    // the lunge blurs out of sight
    { at: 200, ghosts: { dur: 40, every: 13, life: 0.24, alpha: 0.55 }, fx: 'speedLines', o: { n: 9, dur: 220, band: [-30, -2] } },
    { at: 205, sfx: () => { noise(0.18, 1800, 0.8, 0.3, 'bandpass', 0.4); tone(90, 0.3, 0.12, 'sine', 0.5); } },
    { at: 236, call: F => { const r = agRel(F); F.twUp = { x: r.near - 14, y: clamp(r.top - 6, -58, -34) }; agMove(F, F.twUp.x, F.twUp.y, 0); } },
    { at: 240, fx: twWhirlFx, o: { life: 520 }, cine: { dark: 0.62 } },
    // phantoms from every angle (three of them land as beats)
    ...TW_PH.map((p, i) => ({ at: p[0], call: F => twPhantom(F, i) })),
    ...TW_PH.map((p, i) => ({ at: p[0] + 35, fx: 'sparkBurst', o: { n: 6, spd: 150, dir: Math.atan2(p[2], p[1]) * 57.3, arc: 50 } })),
    { at: 365, hit: 0.4, stop: 0.04, shake: 3, flash: 0.08, kick: 0.8, zoom: 0.3 },
    { at: 525, hit: 0.4, stop: 0.04, shake: 3, flash: 0.08, kick: 0.8, zoom: 0.3 },
    { at: 675, hit: 0.4, stop: 0.05, shake: 4, flash: 0.1, kick: 1, zoom: 0.35 },
    // the phantoms gather back into him, above the foe
    { at: 715, fx: 'soulWisps', o: { anchor: F => ({ x: F.x0 + F.face0 * F.twUp.x, y: F.y0 + F.twUp.y - 14 }), from: 'ring', r: 46, n: 12, rise: 30, dur: 200, stagger: 6, to: 'player' } },
    { at: 760, fx: 'impactFlash', o: { anchor: 'player', dy: -16, r: 18, dur: 150 }, sfx: () => { tone(1975, 0.15, 0.05, 'triangle', 0.7); noise(0.12, 3000, 1, 0.14, 'highpass'); }, cine: { dark: 0.5 } },
    { at: 760, fx: 'sparkBurst', o: { anchor: 'player', dy: -16, n: 12, spd: 140 } },
    { at: 900, sfx: () => sfx.glint() },
    { at: 960, fx: 'speedLines', o: { n: 8, dur: 160, band: [-50, -10] } },
    // the X: dive down the front of the foe and open both blades
    { at: 1000, call: F => { const r = agRel(F); agMove(F, r.near - 3, 0, 85, 'in'); }, sfx: () => sfx.heavySwing() },
    { at: 1005, fx: twCrossFx, o: { life: 1350 } },
    { at: 1050, hit: 3.8, slow: 0.45, stop: 0.14, shake: 10, flash: 0.5, boom: true, name: true, kick: 2.6 },
    { at: 1050, fx: 'impactFlash', o: { r: 40, dur: 180 } },
    { at: 1050, fx: 'sparkBurst', o: { n: 26, spd: 240 } },
    { at: 1052, sfx: () => { noise(0.4, 2200, 0.9, 0.3, 'bandpass', 0.3); tone(330, 0.5, 0.06, 'sawtooth', 0.4); } },
    { at: 1090, fx: 'shockwave', o: { anchor: 'player', dx: 6, r1: 46, sq: 0.22, rings: 1, dur: 320 } },
    { at: 1095, sfx: () => sfx.land() },
  ],
  // the gathering in the hang: a crimson breath round the knight
  draw(F, t) {
    if (t > 80 && t < 200) F.aura(0.08 * (t - 80) / 120);
    if (t >= 840 && t < 1000) { F.aura(0.07 + 0.05 * Math.sin(t * 0.03)); addLight(P.x, P.y - 24, 34, F.col, 0.5); }
  },
});

// ================================================================== STAFF "Tempest Ascension"
// Plant the staff and vault onto the foe feet-first; ride the vault up into four turns in the air, the staff level at
// the waist, each turn throwing a ring of wind (a small foe is carried up with you); hang with the staff overhead while
// the wind gathers, flip it point-down and plunge it into the floor: a vortex of wind and dust tears up out of the stone.
function stWindFx(gx, t, F, e) {   // wind streaks spiralling round the spinning knight
  const life = e.o.life, env = Math.min(1, t / 100, (life - t) / 120), cx = P.x, cy = P.y - 16;
  for (let j = 0; j < 4; j++) {
    const rx = 15 + j * 5, ry = 4 + j * 1.5, yo = (j - 1.5) * 7 - (t * 0.012) % 7, ph = t * (0.016 - j * 0.002) + j * 1.6;
    for (let s = 0; s < 34; s++) {
      const u = s / 33, th = ph + u * 2.4, x = Math.round(cx + Math.cos(th) * rx), y = Math.round(cy + yo + Math.sin(th) * ry);
      const front = Math.sin(th) > 0; if (!fatDith(x, y, env * u * (front ? 1 : 0.45))) continue;
      g.fillStyle = `rgba(${u > 0.8 && front ? fatHot(F.col) : F.col},${(front ? 0.8 : 0.4) * env})`; g.fillRect(x, y, 1, 1);
    }
  }
  addLight(cx, cy, 40, F.col, 0.3 * env);
}
function stVortexFx(gx, t, F, e) {   // the tornado: stacked rings widening upward, wheeling, dust riding it, then rising away
  const o = e.o, life = o.life, cx = e.x, fy = e.y;
  const grow = clamp(t / 170, 0, 1), dis = clamp((t - 750) / (life - 750), 0, 1), env = (1 - dis) * Math.min(1, t / 50);
  const N = 11, Hh = 112 * fatEase('out', grow), lift = dis * dis * 46, hot = fatHot(F.col), lite = fatLite(F.col);
  for (let j = 0; j < N; j++) {
    const hj = j / (N - 1); if (hj > grow * 1.05) continue;
    const y = fy - 3 - hj * Hh - lift * hj, rx = 6 + hj * 34 + dis * 12 + Math.sin(t * 0.01 + j) * 1.5, ry = rx * 0.24, ph = t * (0.022 - hj * 0.009) + j * 0.9;
    const a = env * (1 - hj * 0.3), wob = Math.sin(t * 0.006 + hj * 3) * hj * 6;
    for (let s = 0, n = Math.ceil(rx * 3.2); s < n; s++) {
      const th = s / n * 6.2832, front = Math.sin(th) > 0, dash = Math.sin(3 * th + ph);
      if (dash < (front ? -0.35 : 0.3)) continue;
      const x = Math.round(cx + wob + Math.cos(th) * rx), yy = Math.round(y + Math.sin(th) * ry);
      if (dis > 0 && !fatDith(x, yy, 1 - dis)) continue;
      if (!front) { if (!fatDith(x, yy, 0.55)) continue; g.fillStyle = `rgba(${F.col},${0.45 * a})`; g.fillRect(x, yy, 1, 1); continue; }
      g.fillStyle = `rgba(${dash > 0.75 ? hot : lite},${0.95 * a})`; g.fillRect(x, yy, 1, 1);
      if (dash > 0.2) { g.fillStyle = `rgba(${F.col},${0.5 * a})`; g.fillRect(x, yy + 1, 1, 1); }
    }
  }
  // dust and grit riding the spiral
  for (let k = 0; k < 40; k++) {
    const hk = ((t * 0.0011 + fatHash(k, 3)) % 1), y = fy - 2 - hk * Hh - lift * hk, rx = 6 + hk * 34 + dis * 12, th = t * 0.012 + k * 2.4;
    if (hk > grow) continue;
    const x = Math.round(cx + Math.cos(th) * rx), yy = Math.round(y + Math.sin(th) * rx * 0.24);
    g.fillStyle = `rgba(${k % 3 ? '214,200,172' : lite},${0.75 * env})`; g.fillRect(x, yy, 1, 1);
  }
  addLight(cx, fy - 40, 90, F.col, 0.6 * env);
}
function stDust(F, x, y, n, spd) {   // grey grit thrown out along the floor
  const R = fatRng(F.n * 29 + n);
  for (let i = 0; i < n; i++) { const s = R() < 0.5 ? -1 : 1; fatPart({ k: 'dust', x: x + s * R() * 6, y: y - 1 - R() * 3, vx: s * (40 + R() * spd), vy: -30 - R() * 70, col: i % 3 ? '170,158,140' : '214,204,184', life: 0.5 + R() * 0.5, max: 1, g: 260 }); }
}
fatalityRegister('staff', {
  name: 'Tempest Ascension',
  col: '190,235,215',
  tag: 'st_fatal', tags: ['st_bvault', 'riposte'],
  dur: 1700,
  steps: [
    { at: 0, move: { gap: 12, dur: 100 } },
    { at: 95, fx: 'sparkBurst', o: { anchor: 'player', dx: 18, dy: -1, n: 6, spd: 90, dir: -90, arc: 120 }, sfx: () => sfx.land() },
    // the vault onto the foe
    { at: 110, call: F => { const r = agRel(F); F.stUp = { x: r.near + clamp(r.w * 0.25, 4, 10), y: clamp(r.top - 4, -58, -34) }; agMove(F, F.stUp.x, F.stUp.y, 210, 'out'); }, sfx: () => sfx.jump() },
    { at: 120, fx: 'speedLines', o: { n: 8, dur: 200, band: [-30, 6], dir: 0 } },
    { at: 200, hit: 0.6, stop: 0.05, shake: 4, flash: 0.12, hy: 0.15, kick: 1 },
    { at: 200, fx: 'impactFlash', o: { anchor: 'top', dy: 4, r: 18, dur: 140 } },
    { at: 200, fx: 'shockwave', o: { anchor: 'top', dy: 4, r1: 30, sq: 0.45, rings: 1, dur: 260 } },
    // the rising spin: four turns, four rings of wind
    { at: 320, call: F => agMove(F, F.stUp.x, Math.max(-74, F.stUp.y - 16), 520, 'inout'), fx: stWindFx, o: { life: 580 }, target: { lift: 24, dur: 360 } },
    ...[320, 450, 580, 710].map((at, i) => ({ at, fx: 'shockwave', o: { anchor: 'player', dy: -14, r0: 6, r1: 34 + i * 4, sq: 0.28, rings: 1, dur: 300 } })),
    ...[322, 452, 582, 712].map(at => ({ at, sfx: () => noise(0.16, 1400, 0.8, 0.22, 'bandpass', 1.6) })),
    { at: 450, hit: 0.5, stop: 0.04, shake: 3, flash: 0.08, kick: 0.8, zoom: 0.3 },
    { at: 450, fx: 'sparkBurst', o: { n: 10, spd: 160 } },
    { at: 700, hit: 0.5, stop: 0.05, shake: 4, flash: 0.1, kick: 0.9, zoom: 0.35 },
    { at: 700, fx: 'sparkBurst', o: { n: 12, spd: 170 } },
    // the hang: the wind gathers into the staff
    { at: 850, fx: 'soulWisps', o: { anchor: 'player', dy: -20, from: 'ring', r: 50, n: 12, rise: 60, dur: 220, stagger: 8, to: 'tip' }, cine: { dark: 0.6 } },
    { at: 900, sfx: () => { sfx.glint(); tone(300, 0.3, 0.05, 'triangle', 2); } },
    // the plunge
    { at: 1000, call: F => { const r = agRel(F); agMove(F, r.near - 3, 0, 90, 'in'); }, fx: 'speedLines', o: { n: 10, dur: 120, band: [-60, -10], dir: 1 } },
    { at: 1060, target: { drop: true, dur: 50 } },
    { at: 1090, hit: 3.4, slow: 0.45, stop: 0.14, shake: 11, flash: 0.5, boom: true, name: true, kick: 2.6, kickY: 2, hy: 0.8, cine: { dark: 0.5 } },
    { at: 1090, fx: stVortexFx, o: { anchor: 'player', dx: 10, dy: 0, life: 1400 } },
    { at: 1090, fx: 'shockwave', o: { anchor: 'player', dx: 10, r1: 110, sq: 0.22, rings: 2, gap: 80, dur: 460 } },
    { at: 1090, fx: 'impactFlash', o: { anchor: 'player', dx: 10, dy: -2, r: 34, dur: 170 } },
    { at: 1090, call: F => stDust(F, P.x + F.face * 10, P.y, 22, 120) },
    { at: 1092, sfx: () => { noise(0.9, 900, 0.6, 0.35, 'bandpass', 0.3); noise(0.5, 200, 0.8, 0.4, 'lowpass'); } },
    { at: 1110, fx: 'emberBurst', o: { anchor: 'player', dx: 10, n: 14, w: 40, rise: 90, col: '210,220,205' } },
  ],
  draw(F, t) { if (t >= 840 && t < 1000) { F.aura(0.06 + 0.04 * Math.sin(t * 0.04)); const tp = F.tip(); addLight(tp.x, tp.y, 30, F.col, 0.5); } },
});

// ================================================================== WHIP "Thunder Leash"
// Fling the chain round the foe's neck (the hook whips round it twice), lean back and haul it taut, turn once with the
// chain whirled round you (a small foe is swung round with it), plant with the arm high while the static gathers, and
// crack it: thunder races down the chain into the foe, a bolt drops on it from above, and the lightning crawls over it
// after. The chain past the handle is drawn here (the sprite carries a stub), in step with wh_fatal's frames.
const WH_FR = [   // per frame of wh_fatal: [ms, hand x, hand y, angle, dx, dy, mirrored]   (art/player_v16_fatal_agile.py)
  [80, 30, 18, -130, -1, 1, 0], [100, 28, 16, -150, -2, 2, 0], [50, 38, 19, -30, 1, 1, 0], [130, 41, 21, -20, 2, 1, 0],
  [60, 30, 23, -8, -3, 1, 0], [140, 29, 24, -6, -3, 2, 0], [90, 33, 14, -100, -1, 0, 1], [90, 34, 12, -80, 0, -1, 1],
  [90, 32, 12, -100, 0, -1, 0], [90, 35, 14, -70, 0, 0, 0], [140, 29, 11, -130, -1, 1, 0], [50, 41, 26, 20, 2, 2, 0],
  [60, 42, 28, 30, 3, 3, 0], [250, 41, 29, 40, 3, 3, 0], [150, 36, 26, 10, 1, 1, 0], [130, 35, 27, -50, 0, 0, 0],
];
function whStart(t) {   // the chain's root (the stub's end) in world space at fatality time t
  let a = 0, i = 0; while (i < WH_FR.length - 1 && t >= a + WH_FR[i][0]) a += WH_FR[i++][0];
  const [, hx, hy, an, dx, dy, mir] = WH_FR[i], r = an * Math.PI / 180;
  let px = hx + dx + Math.cos(r) * 5, py = hy + dy + Math.sin(r) * 5; if (mir) px = 56 - px;
  return agPose(px, py);
}
function whNeck(F) { const c = F.tc(), hb = c.hb, h = hb.y1 - hb.y0, w = hb.x1 - hb.x0; return { x: c.x - F.face0 * w * 0.12, y: hb.y0 + clamp(h * 0.16, 4, 16), rx: clamp(w * 0.22, 4, 9) }; }
// the chain's shape now: { S, E (end), sag, vib, k (how far it reaches, 0..1), wrap (0..1), slack }
function whShape(F, t) {
  const S = whStart(t), N = whNeck(F);
  if (t < 180 || t >= 1450) return null;
  if (t < 250) { const k = fatEase('out', (t - 180) / 70); return { S, E: { x: lerp(S.x, N.x, k), y: lerp(S.y, N.y, k) }, sag: -9 * (1 - k), vib: 0, wrap: 0, N }; }
  if (t < 360) return { S, E: N, sag: 4 * (1 - (t - 250) / 110), vib: 0, wrap: clamp((t - 250) / 90, 0, 1), N };
  if (t < 1250) {
    const vib = t < 560 ? 1.6 * Math.exp(-(t - 360) / 90) : t >= 920 && t < 1060 ? 0.7 : 0.3;
    return { S, E: N, sag: t >= 560 && t < 920 ? 2 : 0, vib, wrap: 1, N };
  }
  // it lets go: the end falls off the neck and the chain drops slack in front, gathered back toward the hand
  const k = fatEase('in', (t - 1250) / 200), G0 = { x: P.x + F.face * 30, y: P.y - 1 };
  return { S, E: { x: lerp(N.x, lerp(G0.x, S.x, k * 0.6), Math.min(1, k * 1.4)), y: lerp(N.y, G0.y, Math.min(1, k * 1.4)) }, sag: 10 * k + 3, vib: 0, wrap: 1 - Math.min(1, k * 3), N, slack: k };
}
function whPts(F, sh, t) {
  const { S, E } = sh, L = Math.hypot(E.x - S.x, E.y - S.y), n = Math.max(2, Math.ceil(L)), pts = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, sg = Math.sin(u * Math.PI) * sh.sag, vb = sh.vib * Math.sin(u * Math.PI * 7 + t * 0.09) * Math.sin(u * Math.PI);
    pts.push([lerp(S.x, E.x, u), lerp(S.y, E.y, u) + sg + vb]);
  }
  return pts;
}
// the wrap round the neck: the front halves of two coils and the hook hanging off them
function whWrap(F, sh, lit) {
  if (!sh || sh.wrap <= 0) return;
  const N = sh.N;
  for (let c = 0; c < 2; c++) {
    const k = clamp(sh.wrap * 2 - c, 0, 1); if (k <= 0) continue;
    for (let s = 0; s <= 18 * k; s++) {
      const th = s / 18 * Math.PI, x = Math.round(N.x + Math.cos(th) * N.rx * F.face0), y = Math.round(N.y + c * 3 + Math.sin(th) * 2.2);
      g.fillStyle = lit ? (s % 2 ? 'rgb(118,116,136)' : 'rgb(196,196,212)') : `rgba(${F.col},0.5)`; g.fillRect(x, y, 1, 1);
    }
  }
  if (lit && sh.wrap >= 1) { const hx = Math.round(N.x - N.rx * F.face0), hy = Math.round(N.y + 5); g.fillStyle = 'rgb(200,204,220)'; g.fillRect(hx, hy, 1, 3); g.fillRect(hx + F.face0, hy + 3, 1, 1); g.fillStyle = 'rgb(240,244,255)'; g.fillRect(hx + 2 * F.face0, hy + 2, 1, 1); }
}
function whSky(F) { return (typeof cam !== 'undefined' ? cam.y : P.y - 120) - 4; }
function whBoltFx(gx, t, F, e) {   // a bolt from above the view down onto the neck, two flickers, forks
  const N = e.N || (e.N = whNeck(F)), on = t < 70 || (t > 110 && t < 170); if (!on) return;
  const a = t < 70 ? 1 : 0.7, sky = whSky(F), seed = F.n * 7 + (t < 70 ? 1 : 2);
  const main = agBolt(N.x + (fatHash(seed, 1) - 0.5) * 30, sky, N.x, N.y, seed, 5, 7);
  g.fillStyle = `rgba(${F.col},${0.55 * a})`; for (const d of [-1, 1]) agPath(main.map(p => [p[0] + d, p[1]]));
  g.fillStyle = `rgba(${fatHot(F.col)},${a})`; agPath(main);
  for (let b = 0; b < 3; b++) {   // forks off the trunk and down over the body
    const p = main[Math.floor(main.length * (0.45 + b * 0.18))], R = fatRng(seed * 5 + b), hb = F.tc().hb;
    const q = agBolt(p[0], p[1], lerp(hb.x0, hb.x1, R()), lerp(hb.y0, hb.y1, 0.4 + R() * 0.6), seed + b * 31, 3, 5);
    g.fillStyle = `rgba(${fatLite(F.col)},${0.8 * a})`; agPath(q);
  }
  addLight(N.x, N.y - 30, 90, F.col, 0.8 * a);
}
function whCrawlFx(gx, t, F, e) {   // the after-effect: little arcs crawling over the foe, thinning out
  const life = e.o.life, k = t / life, hb = F.tc().hb, b = Math.floor(t / 60);
  for (let i = 0; i < 3; i++) {
    if (fatHash(b, i + 7) < k * 1.1) continue;
    const R = fatRng(b * 13 + i * 101 + F.n), x0 = lerp(hb.x0, hb.x1, R()), y0 = lerp(hb.y0, hb.y1, R()), ang = R() * 6.28, L = 6 + R() * 12;
    g.fillStyle = `rgba(${R() < 0.5 ? fatHot(F.col) : fatLite(F.col)},${0.9 * (1 - k)})`;
    agPath(agBolt(x0, y0, x0 + Math.cos(ang) * L, y0 + Math.sin(ang) * L, b * 3 + i, 2, 3));
  }
  addLight((hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, 50, F.col, 0.45 * (1 - k) * (0.6 + 0.4 * Math.sin(t * 0.08)));
}
fatalityRegister('whip', {
  name: 'Thunder Leash',
  col: '150,195,255',
  tag: 'wh_fatal', tags: ['wh_heavy', 'riposte'],
  dur: 1700,
  steps: [
    { at: 0, move: { dx: -8, dur: 160 } },
    { at: 90, sfx: () => sfx.glint() },
    { at: 182, sfx: () => { sfx.shoot(); noise(0.2, 1500, 0.8, 0.2, 'bandpass', 1.8); } },
    // the wrap
    { at: 255, hit: 0.5, stop: 0.05, shake: 3, flash: 0.08, hy: 0.15, kick: 0.6, sfx: () => { sfx.parry(); noise(0.25, 3200, 1, 0.16, 'highpass'); } },
    { at: 255, fx: 'sparkBurst', o: { anchor: F => whNeck(F), n: 8, spd: 110, col: '220,224,240' } },
    // the yank (a small foe is dragged in)
    { at: 360, call: F => agTarget(F, agTOx(F, P.x + F.face0 * 22), 0, 160, 'out'), sfx: () => { noise(0.2, 500, 0.8, 0.35, 'lowpass'); tone(110, 0.2, 0.15, 'square', 0.6); } },
    { at: 380, hit: 0.8, stop: 0.07, shake: 6, flash: 0.12, hy: 0.15, kick: -1.6 },
    // one turn (the chain whirled round; a small foe swung round with it)
    { at: 560, sfx: () => noise(0.36, 900, 0.7, 0.25, 'bandpass', 2.2), cine: { dark: 0.58 } },
    { at: 740, sfx: () => noise(0.2, 1300, 0.7, 0.2, 'bandpass', 1.5) },
    { at: 930, sfx: () => { tone(98, 0.5, 0.08, 'sawtooth', 3); noise(0.4, 5000, 0.6, 0.1, 'highpass', 0.5); }, cine: { dark: 0.66 } },
    // the crack: thunder down the chain
    { at: 1060, sfx: () => { noise(0.12, 6000, 1, 0.5, 'highpass'); tone(2400, 0.1, 0.06, 'square', 0.3); } },
    { at: 1130, hit: 3.7, slow: 0.45, stop: 0.15, shake: 11, flash: 0.5, boom: true, name: true, kick: 2.4, hy: 0.25, cine: { dark: 0.5 } },
    { at: 1130, fx: whBoltFx, o: { life: 180 } },
    { at: 1130, fx: 'impactFlash', o: { anchor: F => whNeck(F), r: 34, dur: 170 } },
    { at: 1130, fx: 'shockwave', o: { anchor: F => whNeck(F), r1: 54, rings: 2, gap: 70, dur: 380 } },
    { at: 1130, fx: 'sparkBurst', o: { anchor: F => whNeck(F), n: 24, spd: 230 } },
    { at: 1130, fx: whCrawlFx, o: { life: 1300 } },
    { at: 1132, sfx: () => { noise(1.2, 160, 0.6, 0.7, 'lowpass', 0.4); noise(0.35, 2600, 0.8, 0.35, 'bandpass', 0.3); } },
    { at: 1130, call: F => agTarget(F, agTOx(F, P.x + F.face0 * 30), 0, 90, 'in') },
  ],
  // a small foe swung once round the knight on the chain (the orbit is set through the framework's target motion)
  tick(F) {
    const t = F.t, tg = F.target; if (!F.small || !fatAlive(tg) || t < 560 || t >= 1130) return;
    const hb = F.tc().hb, h = hb.y1 - hb.y0, k = fatEase('inout', clamp((t - 560) / 360, 0, 1)), a = k * Math.PI * 2;
    const cx = P.x + F.face0 * Math.cos(a) * 26, cy = P.y - 30 - Math.max(Math.sin(a), -0.25) * 22;
    const g0 = { x: P.x + F.face0 * 22, y: P.y - h / 2 }, m = Math.min(1, (t - 560) / 60);
    const wx = lerp(g0.x, cx, m), wy = lerp(g0.y, cy, m);
    F.tm = { fx: agTOx(F, wx), fy: F.ty0 - (wy + h / 2), tx: agTOx(F, wx), ty: F.ty0 - (wy + h / 2), t0: t, dur: 0 };
  },
  drawLit(F, t) {   // the chain itself (solid links)
    const sh = whShape(F, t); if (!sh) return;
    const pts = whPts(F, sh, t), fade = t > 1400 ? 1 - (t - 1400) / 50 : 1; if (fade <= 0) return;
    for (let i = 0; i < pts.length; i++) {
      if (fade < 1 && !fatDith(Math.round(pts[i][0]), Math.round(pts[i][1]), fade)) continue;
      g.fillStyle = Math.floor(i / 1.5) % 2 ? 'rgb(118,116,136)' : 'rgb(196,196,212)'; g.fillRect(Math.round(pts[i][0]), Math.round(pts[i][1]), 1, 1);
    }
    whWrap(F, sh, true);
    // the slack whirled round the knight in the turn: a ring of chain at the waist
    if (t >= 560 && t < 940) {
      const k = (t - 560) / 380, env = Math.sin(Math.PI * Math.min(1, k * 1.15)), ph = k * Math.PI * 4;
      for (let s = 0; s < 60; s++) {
        const th = ph + s / 60 * 6.2832, front = Math.sin(th) > 0, x = Math.round(P.x + Math.cos(th) * 18), y = Math.round(P.y - 30 + Math.sin(th) * 5);
        if (!front || !fatDith(x, y, env)) continue;
        g.fillStyle = s % 2 ? 'rgb(118,116,136)' : 'rgb(196,196,212)'; g.fillRect(x, y, 1, 1);
      }
    }
  },
  draw(F, t) {   // the glow on the chain: static in the turn, the thunder racing down it on the crack, cooling after
    const sh = whShape(F, t); if (!sh) return;
    const pts = whPts(F, sh, t), n = pts.length - 1;
    if (t >= 560 && t < 1060) {   // static crawling on the links, growing
      const k = clamp((t - 560) / 500, 0, 1), b = Math.floor(t / 45);
      for (let i = 0; i < 2 + k * 5; i++) {
        const u = fatHash(b, i + 3), p = pts[Math.floor(u * n)], R = fatRng(b * 17 + i);
        g.fillStyle = `rgba(${R() < 0.4 ? fatHot(F.col) : F.col},${0.5 + 0.5 * k})`; agPath(agBolt(p[0], p[1], p[0] + (R() - 0.5) * 8, p[1] + (R() - 0.5) * 6, b + i, 1.5, 2));
      }
      if (t >= 920) { const S = sh.S; mvStar(S.x, S.y, 2 + 2 * Math.abs(Math.sin(t * 0.05)), fatHot(F.col), 0.9); addLight(S.x, S.y, 30, F.col, 0.6); }
    }
    if (t >= 1060 && t < 1450) {
      const head = t < 1130 ? fatEase('in', (t - 1060) / 70) : 1, cool = t < 1130 ? 0 : clamp((t - 1130) / 300, 0, 1);
      const m = Math.floor(n * head), seg = pts.slice(0, m + 1);
      if (seg.length > 1) {
        const R = fatRng(Math.floor(t / 35) + F.n), jag = seg.map((p, i) => [p[0] + (i % 4 ? 0 : (R() - 0.5) * 3 * (1 - cool)), p[1] + (i % 4 ? 0 : (R() - 0.5) * 3 * (1 - cool))]);
        g.fillStyle = `rgba(${F.col},${0.6 * (1 - cool)})`; agPath(jag.map(p => [p[0], p[1] - 1])); agPath(jag.map(p => [p[0], p[1] + 1]));
        g.fillStyle = `rgba(${fatHot(F.col)},${1 - cool * 0.8})`; agPath(jag);
        const hp = seg[seg.length - 1]; if (t < 1130) { mvStar(hp[0], hp[1], 4, fatHot(F.col), 1); addLight(hp[0], hp[1], 40, F.col, 0.7); }
      }
      whWrap(F, sh, false);
    }
  },
});

// ================================================================== MARTIAL ARTS "Hundred Embers"
// A Swift palm flurry -- eight blows and a blur of phantom fists between them, pale steel-blue -- then the feet root
// mid-flurry and the style turns to Iron (the knuckles catch, the blows go ember and heavy); sink with both hands at the
// hip as the wraps take fire, and drive both palms out as one: a shockwave passes THROUGH the foe and out of its back,
// and a glowing palm print is left burned on it, cooling from white to ember to red to ash.
const FT_HY = [0.32, 0.5, 0.22, 0.42, 0.18, 0.56, 0.3, 0.45, 0.38, 0.28, 0.4, 0.34];
const FT_SW = '170,214,255', FT_IR = '255,140,60';
function ftFistFx(gx, t, F, e) {   // one blow: dash lines from the shoulder line into the foe and a 4-point star at the impact
  const o = e.o, a = 1 - t / o.life, hb = F.tc().hb, near = F.face0 > 0 ? hb.x0 : hb.x1;
  const ix = near + F.face0 * 2, iy = lerp(hb.y0, hb.y1, o.hy), sx = P.x + F.face0 * 8, sy = P.y - 21 + o.dy;
  const k = Math.min(1, t / 30);
  g.fillStyle = `rgba(${o.col},${0.55 * a})`;
  for (let j = -1; j <= 1; j++) { const y0 = Math.round(lerp(sy, iy, 0.3)) + j * 2, x0 = lerp(sx, ix, 0.25 + 0.12 * Math.abs(j)), x1 = lerp(sx, ix, k * 0.92); if ((x1 - x0) * F.face0 > 0) fatLine(x0, y0, x1, lerp(y0, iy, 0.6)); }
  if (t >= 25) { const s = o.big ? 5 : 3; mvStar(ix, iy, s * a + 1, fatHot(o.col), a); addLight(ix, iy, o.big ? 34 : 20, o.col, (o.big ? 0.55 : 0.35) * a); }
}
function ftBlow(F, i, iron, big) {
  const col = iron ? FT_IR : FT_SW;
  F.fx(ftFistFx, { life: big ? 150 : 100, hy: FT_HY[i % FT_HY.length], dy: (i % 3) - 1, col, big });
  if (!iron) for (let q = 1; q <= 2; q++) F.fx(ftFistFx, { life: 80, hy: FT_HY[(i * 3 + q * 5) % FT_HY.length], dy: q - 1, col: FT_SW });   // the blur of fists between
  try { if (iron) { noise(0.1, 500, 1, 0.3, 'lowpass'); tone(110, 0.1, 0.12, 'square', 0.6); } else noise(0.05, 2400 + i * 120, 1.2, 0.14, 'bandpass'); } catch (e) {}
}
// the palm print: 8 x 10, fingers up (thumb toward the knight)
const FT_PALM = ['.X.X....', '.X.X.X..', '.X.X.X.X', '.X.X.X.X', '.XXXXXXX', 'XXXXXXXX', 'XXXXXXX.', '.XXXXXX.', '..XXXXX.', '..XXXX..'];
function ftPrintFx(gx, t, F, e) {
  const o = e.o; if (!e.off) { const c = F.tc(), hb = c.hb, near = F.face0 > 0 ? hb.x0 : hb.x1; e.off = { x: near + F.face0 * 4 - c.x, y: lerp(hb.y0, hb.y1, 0.38) - c.y }; e.ash = false; }
  const c = F.tc(), x0 = Math.round(c.x + e.off.x - 4), y0 = Math.round(c.y + e.off.y - 5);
  const hotK = clamp(t / 140, 0, 1), cool = clamp((t - 600) / 900, 0, 1), ashK = clamp((t - 1500) / (o.life - 1500), 0, 1);
  const col = t < 140 ? fatMix('255,252,235', '255,190,110', hotK) : cool < 1 ? fatMix('255,150,60', '140,36,22', cool) : '120,108,100';
  for (let y = 0; y < FT_PALM.length; y++) for (let x = 0; x < 8; x++) {
    if (FT_PALM[y][x] !== 'X') continue;
    const px = F.face0 > 0 ? x0 + x : x0 + 7 - x, py = y0 + y, edge = !FT_PALM[y][x - 1] || FT_PALM[y][x - 1] !== 'X' || FT_PALM[y][x + 1] !== 'X' || !FT_PALM[y - 1] || FT_PALM[y - 1][x] !== 'X';
    if (ashK > 0 && fatHash(px, py) < ashK) continue;
    if (cool > 0.3 && !edge && fatHash(px * 3, py) < (cool - 0.3) * 0.7) continue;   // the middle cools first
    g.fillStyle = `rgba(${edge || t < 300 ? col : fatMix(col, '255,240,200', 0.35 * (1 - cool))},${ashK > 0 ? 0.5 * (1 - ashK) : 0.95})`; g.fillRect(px, py, 1, 1);
  }
  if (t < 260) { g.fillStyle = `rgba(${F.col},${0.4 * (1 - t / 260)})`; fatEllipse(x0 + 4, y0 + 5, 7 + t / 40, 8 + t / 40); }
  if (!e.ash && t >= 1500) { e.ash = true; const R = fatRng(F.n * 3 + 1); for (let i = 0; i < 14; i++) fatPart({ x: x0 + R() * 8, y: y0 + R() * 10, vx: (R() - 0.5) * 14, vy: -6 - R() * 10, col: '128,118,110', life: 0.7 + R() * 0.6, max: 1.3, g: 40 }); }
  if (cool < 1) addLight(x0 + 4, y0 + 5, 26, col, 0.6 * (1 - cool));
}
function ftThroughFx(gx, t, F, e) {   // the pressure wave passing through the foe and out of its back
  const o = e.o; if (!e.p) { const c = F.tc(), hb = c.hb; e.p = { x: (F.face0 > 0 ? hb.x0 : hb.x1) + F.face0 * 3, y: lerp(hb.y0, hb.y1, 0.4), h: clamp((hb.y1 - hb.y0) * 0.5, 14, 40) }; }
  for (let i = 0; i < 3; i++) {
    const tt = t - i * 45; if (tt < 0 || tt > 330) continue;
    const k = tt / 330, x = e.p.x + F.face0 * fatEase('out', k) * 150, ry = e.p.h * (0.7 + k * 0.6), rx = 2 + k * 5, a = (1 - k) * (i ? 0.6 : 1);
    g.fillStyle = `rgba(${fatHot(F.col)},${a})`; fatEllipse(x, e.p.y, rx, ry);
    g.fillStyle = `rgba(${F.col},${0.6 * a})`; fatEllipse(x - F.face0 * 2, e.p.y, Math.max(1, rx - 1), ry * 0.9);
  }
  addLight(e.p.x + F.face0 * 40, e.p.y, 70, F.col, 0.5 * (1 - t / o.life));
}
fatalityRegister('fist', {
  name: 'Hundred Embers',
  col: '255,125,60',
  tag: 'ft_fatal', tags: ['ft_ember', 'riposte'],
  dur: 1700,
  steps: [
    { at: 0, move: { gap: 3, dur: 110 }, call: () => { if (typeof ftSetStyle === 'function') ftSetStyle('swift', false); } },
    // the Swift flurry
    ...[120, 180, 240, 300, 360, 420, 480, 540].map((at, i) => ({ at, call: F => ftBlow(F, i, false) })),
    { at: 120, ghosts: { dur: 470, every: 60, col: `rgb(${FT_SW})`, life: 0.16, alpha: 0.24 } },
    { at: 250, hit: 0.35, stop: 0.03, shake: 2, flash: 0.06, kick: 0.6, zoom: 0.25 },
    { at: 430, hit: 0.35, stop: 0.03, shake: 3, flash: 0.06, kick: 0.6, zoom: 0.25 },
    // the switch: rooted, the knuckles catch
    { at: 600, call: F => { if (typeof ftSetStyle === 'function') ftSetStyle('iron', true); agMove(F, (P.x - F.x0) * F.face0 + 3, 0, 80); ftBlow(F, 8, true, true); } },
    { at: 600, fx: 'shockwave', o: { anchor: 'player', r0: 4, r1: 30, sq: 0.25, rings: 1, dur: 300 } },
    { at: 600, fx: 'groundCrack', o: { anchor: 'player', len: 10, branches: 2, dur: 900 } },
    { at: 600, fx: 'emberBurst', o: { anchor: 'player', dy: -14, dx: 6, n: 8, w: 10, rise: 50 } },
    ...[680, 750, 820].map((at, i) => ({ at, call: F => ftBlow(F, 9 + i, true, i === 2) })),
    { at: 755, hit: 0.7, stop: 0.06, shake: 5, flash: 0.14, kick: 1.4, zoom: 0.4 },
    { at: 755, fx: 'sparkBurst', o: { n: 10, spd: 150, dir: 0, arc: 80 } },
    // the Ember palm: rooted, the wraps take fire
    { at: 905, fx: 'groundCrack', o: { anchor: 'player', len: 16, branches: 4, dur: 1500 }, sfx: () => { sfx.fire(); tone(73, 0.6, 0.12, 'sawtooth', 0.7); }, cine: { dark: 0.62 } },
    { at: 910, fx: 'soulWisps', o: { anchor: 'player', dy: -14, from: 'ring', r: 40, n: 12, rise: 50, dur: 240, stagger: 10, to: F => agPose(24, 30) } },
    { at: 1150, call: F => agMove(F, (P.x - F.x0) * F.face0 + 5, 0, 50), sfx: () => sfx.heavySwing() },
    { at: 1160, hit: 3.6, slow: 0.45, stop: 0.15, shake: 12, flash: 0.5, boom: true, name: true, kick: 2.8, hy: 0.4, cine: { dark: 0.5 } },
    { at: 1160, fx: ftPrintFx, o: { life: 2300 } },
    { at: 1160, fx: ftThroughFx, o: { life: 420 } },
    { at: 1160, fx: 'impactFlash', o: { r: 40, dur: 180, anchor: F => { const hb = F.tc().hb; return { x: (F.face0 > 0 ? hb.x0 : hb.x1) + F.face0 * 3, y: lerp(hb.y0, hb.y1, 0.4) }; } } },
    { at: 1160, fx: 'shockwave', o: { anchor: 'ground', r1: 90, sq: 0.22, rings: 2, gap: 80, dur: 420 } },
    { at: 1160, fx: 'sparkBurst', o: { anchor: F => { const hb = F.tc().hb; return { x: F.face0 > 0 ? hb.x1 : hb.x0, y: lerp(hb.y0, hb.y1, 0.4) }; }, n: 24, spd: 240, dir: 0, arc: 60 } },
    { at: 1170, fx: 'emberBurst', o: { anchor: F => { const hb = F.tc().hb; return { x: F.face0 > 0 ? hb.x1 : hb.x0, y: lerp(hb.y0, hb.y1, 0.5) }; }, n: 16, w: 10, h: 20, rise: 60 } },
    { at: 1160, fx: 'speedLines', o: { n: 10, dur: 220, band: [-36, -6] } },
    { at: 1160, target: { knock: 34, lift: 6, dur: 200 } },
    { at: 1380, target: { drop: true, dur: 120 } },
  ],
  draw(F, t) {
    if (t >= 905 && t < 1160) { const k = (t - 905) / 255, h = agPose(24, 30); F.aura(0.05 + 0.08 * k); addLight(h.x, h.y, 20 + 20 * k, F.col, 0.4 + 0.35 * k); if (k > 0.3) mvStar(h.x, h.y, 2 + 2 * k, fatHot(F.col), 0.5 + 0.4 * k); }
  },
});
