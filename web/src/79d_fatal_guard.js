// ------------------------------------------------------------------ v16 FATALITIES: the guard group (role `fguard`, docs/v16/fguard.md)
// Sword & Shield "Bulwark's End", Spear "Skypiercer", Bow "Point-Blank Pyre". Choreography on the fatality clock, in step
// with art/player_v16_fatal_guard.py (frame starts):
//   sh_fatal        0 step | 90 coil | 220 BASH | 350 cock high | 560 STAB | 730 shield up | 980 SLAM | 1080 hold | 1300 rise
//   sp_fatal        0 coil | 200 IMPALE | 340 lever | 460 hoisted | 600 hold | 820 sink | 880 SKYWARD THRUST | 1200 lower
//   sp_fatal_vault  0 coil | 200 IMPALE | 340 spring | 410 swing | 500 apex | 810 DRIVE | 1060 drop | 1180 land | 1350 rise
//   bw_fatal        0 step | 90 chamber | 170 KICK | 300 set | 380 nock three | 480 full draw | 680 LOOSE | 850 sweep | 980 PYRE
// Feet-relative offsets below are in px along the facing (+ forward) and down (+) from the player's feet.

const FG = { log: [] };
const fgW = (F, fx, fy) => ({ x: P.x + F.face * fx, y: P.y + fy });   // feet-relative -> world (the player now)
const fgS = (F, fx, fy) => ({ x: F.x0 + F.face0 * fx, y: F.y0 + fy }); // relative to where the fatality began
// a step-function table [[ms, ...vals]]: the row in effect at t
function fgKey(rows, t) { let r = rows[0]; for (const q of rows) if (q[0] <= t) r = q; return r; }
// tween the player to (dx, dy) relative to the start (same as a `move` step, but from code: dx may depend on F)
function fgMove(F, dx, dy, dur = 120, ease = 'out') {
  const cur = { x: (P.x - F.x0) * F.face0, y: P.y - F.y0 };
  F.mv = { fx: cur.x, fy: cur.y, tx: dx, ty: dy, t0: F.t, dur, ease };
}
// a jagged lightning polyline from a to b (seeded, re-rolled every `cad` ms)
function fgBolt(a, b, seed, jit = 4, seg = 7) {
  const L = Math.hypot(b.x - a.x, b.y - a.y), n = Math.max(2, Math.round(L / seg)), R = fatRng(seed), nx = -(b.y - a.y) / (L || 1), ny = (b.x - a.x) / (L || 1);
  const pts = [[a.x, a.y]];
  for (let i = 1; i < n; i++) { const k = i / n, o = (R() - 0.5) * 2 * jit; pts.push([lerp(a.x, b.x, k) + nx * o, lerp(a.y, b.y, k) + ny * o]); }
  pts.push([b.x, b.y]); return pts;
}
function fgPoly(pts, k = 1) { const n = Math.max(1, Math.round((pts.length - 1) * k)); for (let i = 1; i <= n; i++) fatLine(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]); }
const fgCrackle = () => { try { noise(0.18, 3800, 2.5, 0.12, 'highpass', 0.6); tone(1400, 0.08, 0.03, 'square', 0.4); } catch (e) {} };
const fgThunder = () => { try { noise(0.5, 2400, 0.9, 0.26, 'bandpass', 0.25); noise(0.9, 140, 0.7, 0.5, 'lowpass', 0.4); tone(70, 0.6, 0.18, 'sawtooth', 0.5); } catch (e) {} };

// ================================================================== SWORD & SHIELD "Bulwark's End"
// A shield bash that rocks the foe, a step in and a downward stab, then the shield hauled overhead and slammed down rim
// first: the shield's crest (the heater, the ember-eye, the gold bar) blooms in light over the foe, holds, and dissolves.
// the heater shield (art/gen_player.py _heater): lx / ly in a w x h box centred on 0
function fgHeater(lx, ly, w, h) {
  const t = (ly + h / 2) / h; if (t < 0 || t > 1) return false;
  let hw = t < 0.45 ? w / 2 : w / 2 * Math.pow(Math.max(0, 1 - Math.pow((t - 0.45) / 0.55, 1.6)), 0.8);
  if (t < 0.06) hw -= (0.06 - t) * w * 0.9;
  return Math.abs(lx) <= hw;
}
// the crest drawn in light: o.h (px tall), o.bloom / o.hold / o.fade (ms), o.small (a quick imprint, no emblem rays)
function fgCrest(ctx, t, F, e) {
  const o = e.o, H0 = o.h || 60, W0 = H0 * 0.78, bl = o.bloom ?? 150, ho = o.hold ?? 620, fd = o.fade ?? 520;
  const kb = clamp(t / bl, 0, 1), s = 0.3 + 0.7 * fatEase('back', kb), kf = clamp((t - bl - ho) / fd, 0, 1);
  const a = (t < bl ? 0.6 + 0.4 * kb : 1) * (1 - kf * 0.35), h = H0 * s, w = W0 * s;
  const cx = Math.round(e.x), cy = Math.round(e.y - kf * 6), col = e.col, hot = fatHot(col), lite = fatLite(col);
  const ember = fatMix('255,120,50', col, 0.25);
  const pal = [null, `rgba(${hot},${0.95 * a})`, `rgba(${lite},${0.7 * a})`, `rgba(${col},${0.2 * a})`, `rgba(${ember},${a})`, `rgba(${fatHot(ember)},${a})`];
  const eyeY = -h * 0.1, rEye = h * 0.13, sweep = (t - bl) / 420;   // a glint band running down while it holds
  const inS = (x, y, k) => fgHeater((x + 0.5 - cx) / k, (y + 0.5 - cy) / k, w, h);
  fatRaster(cx - w / 2 - 2, cy - h / 2 - 2, cx + w / 2 + 2, cy + h / 2 + 2, (x, y) => {
    if (!inS(x, y, 1)) return 0;
    const lx = x + 0.5 - cx, ly = y + 0.5 - cy;
    // dissolve: the crest breaks up from its point upward
    if (kf > 0 && !fatDith(x, y, 1 - kf * (1.4 - (ly / h + 0.5) * 0.8))) return 0;
    const edge = !inS(x + 1, y, 1) || !inS(x - 1, y, 1) || !inS(x, y + 1, 1) || !inS(x, y - 1, 1);
    if (edge) return 1;
    if (!o.small) {
      const inner = !(inS(x, y, 0.84) && inS(x + 1, y, 0.84) && inS(x - 1, y, 0.84) && inS(x, y + 1, 0.84) && inS(x, y - 1, 0.84)) && inS(x, y, 0.84);
      if (inner) return 2;
      const r = Math.hypot(lx * 0.95, ly - eyeY);
      if (r < rEye * 0.42) return 5;
      if (r < rEye * 0.75) return 4;
      if (Math.abs(r - rEye) < 0.7) return 1;
      if (Math.abs(lx) < 0.8 && ly > -h * 0.4 && ly < h * 0.36 && r > rEye) return 2;   // the gold bar
      if (Math.abs(ly - eyeY) < 0.6 && Math.abs(lx) < w * 0.32 && Math.abs(lx) > rEye) return 2;   // the cross-arm
      if (sweep > 0 && sweep < 1.3 && Math.abs(ly / h + 0.5 - sweep) < 0.012) return 2;
    }
    return fatDith(x, y, 0.2) ? 3 : 0;
  }, pal);
  if (!o.small) {
    // rays round it while it blooms and holds
    const ra = a * (1 - kf) * (t < bl ? kb : 1 - clamp((t - bl) / (ho + 200), 0, 0.7));
    if (ra > 0.03) {
      g.fillStyle = `rgba(${lite},${0.45 * ra})`;
      for (let i = 0; i < 12; i++) {
        const an = i / 12 * 6.2832 + 0.26, r0 = h * 0.62, r1 = h * (0.8 + 0.18 * fatHash(i, F.n)) * (0.7 + 0.3 * kb);
        fatLine(cx + Math.cos(an) * r0, cy + Math.sin(an) * r0 * 0.9, cx + Math.cos(an) * r1, cy + Math.sin(an) * r1 * 0.9);
      }
    }
    // the bloom's echo: an outline thrown outward
    if (t < 380) { const k = t / 380, ek = 1 + k * 0.45; g.fillStyle = `rgba(${lite},${0.6 * (1 - k)})`;
      for (let y = Math.floor(cy - h * ek / 2); y <= cy + h * ek / 2; y++) for (const sd of [-1, 1]) {
        let x = cx; while (fgHeater((x + 0.5 - cx) / ek, (y + 0.5 - cy) / ek, w, h) && Math.abs(x - cx) < w) x += sd;
        if (Math.abs(x - cx) < w) g.fillRect(x, y, 1, 1);
      }
    }
    if (t >= bl + ho && !e.burst) {   // break up: gold motes lift off it
      e.burst = true;
      for (let i = 0; i < 26; i++) fatPart({ k: 'ember', x: cx + (Math.random() - 0.5) * w, y: cy + (Math.random() - 0.5) * h, vx: (Math.random() - 0.5) * 30, vy: -15 - Math.random() * 45, col: i % 3 ? col : hot, life: 0.6 + Math.random() * 0.7, max: 1.3, g: -12, ph: Math.random() * 6 });
      try { tone(1320, 0.5, 0.04, 'triangle', 1.3); noise(0.4, 5200, 1.2, 0.06, 'highpass'); } catch (err) {}
    }
  }
  addLight(cx, cy, h * 0.9, col, Math.min(0.6, 0.5 * a * (1 - kf)));
}
const fgShieldHigh = F => fgW(F, 12, -31);   // the raised shield (sh_fatal frames 8-9: off (34..35, 8..10), dx 3)
const fgSlamPt = F => fgW(F, 21, -2);        // the rim where it bites (frame 11: off (43, 28), dx 5, dy 5)
const fgCrestAt = F => { const c = F.tc(); return { x: c.x, y: c.y - 4 }; };
const fgCrestH = F => { const hb = F.tc().hb; return clamp((hb.y1 - hb.y0) * 0.85, 42, 74); };

fatalityRegister('sns', {
  name: "Bulwark's End",
  col: '255,212,120',
  tag: 'sh_fatal', tags: ['sh_heavy', 'riposte'],
  dur: 1500,
  steps: [
    { at: 0, move: { gap: 6, dur: 110 } },
    { at: 95, sfx: () => { tone(110, 0.25, 0.08, 'triangle', 0.7); noise(0.18, 600, 1, 0.08, 'lowpass'); } },
    // BASH (beat 1): the shield's face rings on the foe; a faint imprint of the crest flashes where it struck
    { at: 222, hit: 1.0, stop: 0.07, shake: 6, flash: 0.2, kick: 1.8, hy: 0.42, target: { knock: 9, dur: 120 },
      sfx: () => { sfx.block(); tone(220, 0.3, 0.1, 'triangle', 0.8); } },
    { at: 222, fx: fgCrest, o: { anchor: F => { const c = F.tc(); return { x: (F.face > 0 ? c.hb.x0 : c.hb.x1) + F.face * 2, y: P.y - 15 }; }, h: 20, small: true, bloom: 60, hold: 60, fade: 160, life: 280 } },
    { at: 222, fx: 'shockwave', o: { anchor: F => { const c = F.tc(); return { x: (F.face > 0 ? c.hb.x0 : c.hb.x1), y: P.y - 15 }; }, r0: 3, r1: 26, sq: 1.3, rings: 2, gap: 60, dur: 260, thick: 1 } },
    { at: 222, fx: 'sparkBurst', o: { anchor: F => fgW(F, 18, -15), n: 12, spd: 170, dir: 0, arc: 110 } },
    { at: 350, target: { pin: true } },
    { at: 360, sfx: () => sfx.glint() },
    // the STAB (beat 2): driven down into the foe, a line of light along the blade
    { at: 555, sfx: () => sfx.swing() },
    { at: 562, hit: 1.2, stop: 0.08, shake: 6, flash: 0.22, kick: 1.6, kickY: 1, hy: 0.6 },
    { at: 562, fx: 'slashLine', o: { anchor: F => fgW(F, 30, -14), ang: 38, len: 62, grow: 40, hold: 150, burst: 180, sparks: 8 } },
    { at: 562, fx: 'impactFlash', o: { anchor: F => fgW(F, 27, -16), r: 20, dur: 140 } },
    { at: 562, fx: 'sparkBurst', o: { anchor: F => fgW(F, 27, -16), n: 14, spd: 190, dir: 38, arc: 70 } },
    { at: 600, fx: 'emberBurst', o: { anchor: F => fgW(F, 27, -14), n: 8, w: 8, rise: 50 } },
    // the shield hauled up: light gathers into it
    { at: 735, sfx: () => { sfx.heavySwing(); tone(196, 0.5, 0.05, 'sine', 1.6); } },
    { at: 745, fx: 'soulWisps', o: { anchor: 'player', dx: 10, dy: -22, from: 'ring', r: 50, n: 12, rise: 110, dur: 330, stagger: 14, to: fgShieldHigh } },
    { at: 860, sfx: () => sfx.glint() },
    { at: 870, cine: { dark: 0.6 } },
    { at: 975, fx: 'speedLines', o: { anchor: F => fgW(F, 20, -30), n: 6, dur: 120, band: [-8, 24], dir: 0 } },
    // THE SLAM (beat 3): slow-mo, the boom, the name; the golden crest blooms over the foe
    { at: 1004, hit: 2.8, slow: 0.45, stop: 0.15, shake: 12, flash: 0.5, boom: true, name: true, kick: 2.4, kickY: 2.5, hy: 0.5 },
    { at: 1004, fx: fgCrest, o: { anchor: fgCrestAt, life: 1400, bloom: 150, hold: 640, fade: 560 }, call: (F, s) => { const e = FAT.fx[FAT.fx.length - 1]; if (e && e.fn === fgCrest) e.o.h = fgCrestH(F); } },
    { at: 1004, fx: 'impactFlash', o: { anchor: fgSlamPt, r: 34, dur: 170 } },
    { at: 1004, fx: 'shockwave', o: { anchor: 'ground', r1: 112, sq: 0.22, rings: 3, gap: 80, dur: 480 } },
    { at: 1004, fx: 'groundCrack', o: { anchor: F => fgSlamPt(F), len: 46, branches: 5, dur: 1200, col: '255,196,110' } },
    { at: 1004, fx: 'sparkBurst', o: { anchor: fgSlamPt, n: 22, spd: 230, dir: -90, arc: 150 } },
    { at: 1030, fx: 'emberBurst', o: { anchor: 'ground', n: 16, w: 46, rise: 90, col: '255,214,140' } },
    { at: 1010, sfx: () => { tone(392, 1.4, 0.06, 'triangle', 1); tone(587, 1.2, 0.04, 'sine', 1, 0.06); } },
    { at: 1300, target: { drop: true } },
  ],
});

// ================================================================== SPEAR "Skypiercer"
// Small foes: impaled and HOISTED on the spear (they ride its tip), lightning strikes them and spirals down the haft, then
// a skyward thrust pierces clean through with a long light lance and flings them off. Bosses never move: the spear drives
// in and stays, you vault up the haft, the lightning finds you at the apex and runs down the spear into the boss, and you
// drive it home with your whole weight -- the lance goes down through the boss into the floor.
// art hand / tip of sp_fatal per frame (feet-relative, from the art's hand + angle, reach 21)
const SP_HANDS = [[0, -3, -9, -4], [200, 14, -12, -2], [250, 13, -11, -3], [340, 8, -12, -28], [460, 8, -19, -46], [600, 8, -17, -47],
  [820, 3, -12, -50], [880, 12, -24, -58], [930, 12, -25, -59], [1200, 9, -15, -32], [1400, 6, -13, -8]];
// sp_fatal_vault: hand / angle (the spear's lower end is lost under the feet line: the tip is extended in code)
const SV_HANDS = [[0, -3, -9, -8], [200, 14, -13, -30], [250, 14, -11, -30], [340, 11, -18, -10], [410, 9, -16, 25], [500, 8, -16, 58],
  [650, 8, -16, 59], [810, 11, -11, 64], [1060, 6, -18, -30], [1180, 6, -8, -10], [1350, 5, -12, -8]];
const SP_REACH = 21;
function spHT(F, tbl) {   // world hand + tip + unit direction of the spear now
  const r = fgKey(tbl, F.t), a = r[3] * Math.PI / 180, h = fgW(F, r[1], r[2]);
  const d = { x: Math.cos(a) * F.face, y: Math.sin(a) };
  return { h, tip: { x: h.x + d.x * SP_REACH, y: h.y + d.y * SP_REACH }, d };
}
// the impaled foe rides the tip (small foes only; the framework's target motion, re-aimed every frame)
function spRide(F) {
  const t = F.target; if (!F.small || !fatAlive(t) || !F.ride) return;
  const { tip, d } = spHT(F, SP_HANDS), hb = F.tc().hb;
  if (!F.rideOff) F.rideOff = { dx: (hb.x0 + hb.x1) / 2 - t.x, dy: t.y - (hb.y0 + hb.y1) / 2 };
  const cx = tip.x - d.x * 4, cy = tip.y - d.y * 4;
  const ox = (cx - F.rideOff.dx - F.tx0) * F.face0, oy = F.ty0 - (cy + F.rideOff.dy);
  // no jump on the first frame: the gap between where it is and the tip closes over ~250 ms
  if (!F.rideBias) F.rideBias = { x: -ox, y: -oy, t: F.t };
  const kb = Math.max(0, 1 - (F.t - F.rideBias.t) / 250), tx = ox + F.rideBias.x * kb, ty = oy + F.rideBias.y * kb;
  const cur = F.tm ? { x: F.tm.tx, y: F.tm.ty } : { x: 0, y: 0 }, k = F.rideK ?? 0.3;
  const nx = lerp(cur.x, tx, k), ny = Math.max(0, lerp(cur.y, ty, k));
  F.tm = { fx: nx, fy: ny, tx: nx, ty: ny, t0: F.t, dur: 0 };
}
// the lightning spiral running down the haft from a (top) to b, progress k, two strands
function spSpiral(a, b, k, seed, col, alpha) {
  const L = Math.hypot(b.x - a.x, b.y - a.y) || 1, ux = (b.x - a.x) / L, uy = (b.y - a.y) / L, nx = -uy, ny = ux, R = fatRng(seed);
  const n = Math.max(2, Math.round(L * k / 2));
  for (const ph of [0, Math.PI]) {
    let px = null, py = null;
    for (let i = 0; i <= n; i++) {
      const s = i * 2, w = Math.sin(s / 3.2 + ph) * 3 + (R() - 0.5) * 1.6, x = a.x + ux * s + nx * w, y = a.y + uy * s + ny * w;
      if (px !== null) { g.fillStyle = `rgba(${ph ? col : fatHot(col)},${alpha * (ph ? 0.75 : 1)})`; fatLine(px, py, x, y); }
      px = x; py = y;
    }
  }
  const hx = a.x + ux * L * k, hy = a.y + uy * L * k;
  if (typeof mvStar === 'function') mvStar(hx, hy, 3, fatHot(col), alpha);
  addLight(hx, hy, 34, col, 0.55 * alpha);
}
// a bolt out of the sky onto a point
function spSkyBolt(ctx, t, F, e) {
  const p = e.o.to(F), top = { x: p.x + F.face * -10, y: Math.min(p.y - 120, cam.y - 6) }, k = t / e.life, cad = Math.floor(t / 40);
  const pts = fgBolt(top, p, F.n * 17 + cad, 6, 9), a = (1 - k) * (cad % 2 ? 0.8 : 1);
  g.fillStyle = `rgba(${e.col},${0.55 * a})`; for (let i = 1; i < pts.length; i++) fatLine(pts[i - 1][0] + 1, pts[i - 1][1], pts[i][0] + 1, pts[i][1]);
  g.fillStyle = `rgba(${fatHot(e.col)},${a})`; fgPoly(pts, clamp(t / 50, 0, 1));
  const br = fgBolt({ x: pts[3][0], y: pts[3][1] }, { x: pts[3][0] - F.face * 18, y: pts[3][1] + 22 }, F.n * 5 + cad, 4, 6);
  g.fillStyle = `rgba(${e.col},${0.6 * a})`; fgPoly(br);
  addLight(p.x, p.y - 30, 70, e.col, 0.7 * a);
}
// crackle left on the spear / in the wound
function spCrackle(ctx, t, F, e) {
  const o = e.o, p = o.at(F), k = t / e.life, cad = Math.floor(t / 45), R = fatRng(F.n * 3 + cad);
  if (R() < 0.25) return;
  for (let i = 0; i < (o.n || 3); i++) {
    const a = R() * 6.2832, r = (o.r || 10) * (0.5 + R()), q = { x: p.x + Math.cos(a) * r, y: p.y + Math.sin(a) * r * 0.8 };
    g.fillStyle = `rgba(${i ? e.col : fatHot(e.col)},${0.9 * (1 - k)})`; fgPoly(fgBolt(p, q, F.n * 11 + cad * 7 + i, 2.5, 4));
  }
  addLight(p.x, p.y, 26, e.col, 0.45 * (1 - k));
}
function spLance(F, from, d, len, o = {}) {   // the long light lance along d through `from`
  return F.fx('slashLine', { anchor: () => ({ x: from.x + d.x * len * 0.5, y: from.y + d.y * len * 0.5 }), ang: Math.atan2(d.y, d.x * F.face) * 57.2958,
    len, thick: 2, grow: 55, hold: o.hold ?? 360, burst: o.burst ?? 300, sparks: 26 });
}
const SP_COL = '170,210,255';
// the hoist (small foes): the default steps
const SP_SMALL = [
  { at: 0, move: { gap: 16, dur: 120 } },
  { at: 60, sfx: () => sfx.glint() },
  { at: 195, sfx: () => sfx.spear() },
  { at: 202, hit: 1.0, stop: 0.08, shake: 5, flash: 0.2, kick: 1.6, hy: 0.5, call: F => { F.ride = true; F.rideK = 1; } },
  { at: 202, fx: 'impactFlash', o: { anchor: F => spHT(F, SP_HANDS).tip, r: 20, dur: 140 } },
  { at: 202, fx: 'sparkBurst', o: { anchor: F => spHT(F, SP_HANDS).tip, n: 14, spd: 180, dir: 0, arc: 60 } },
  { at: 230, call: F => { F.rideK = 0.28; } },
  { at: 345, sfx: () => { sfx.heavySwing(); tone(140, 0.35, 0.08, 'sawtooth', 1.4); }, fx: 'groundCrack', o: { anchor: 'player', dx: 6, len: 16, branches: 2, dur: 700, col: SP_COL } },
  // the sky answers: a bolt onto the impaled foe, then it spirals down the haft into your hands
  { at: 540, fx: 'speedLines', o: { anchor: F => spHT(F, SP_HANDS).tip, n: 5, dur: 120, band: [-60, -10], dir: 0 } },
  { at: 580, fx: spSkyBolt, o: { to: F => spHT(F, SP_HANDS).tip, life: 170 }, sfx: fgThunder },
  { at: 582, hit: 0.8, stop: 0.06, shake: 6, flash: 0.32, kick: 1.0, kickY: -1 },
  { at: 590, fx: (c, t, F, e) => { const s = spHT(F, SP_HANDS); spSpiral(s.tip, s.h, clamp(t / 180, 0, 1), F.n * 7 + Math.floor(t / 50), e.col, t < 180 ? 1 : 1 - (t - 180) / 160); }, o: { life: 340 } },
  { at: 600, fx: spCrackle, o: { at: F => spHT(F, SP_HANDS).tip, n: 2, r: 9, life: 280 }, sfx: fgCrackle },
  { at: 830, cine: { dark: 0.62 } },
  // SKYPIERCER (beat 3): the thrust drives on through it and a lance of light goes up into the sky
  { at: 882, hit: 3.2, slow: 0.45, stop: 0.15, shake: 11, flash: 0.5, boom: true, name: true, kick: 2.2, kickY: -2, hy: 0.45 },
  { at: 882, call: F => { const s = spHT(F, SP_HANDS); spLance(F, s.h, s.d, 260); } },
  { at: 882, fx: 'impactFlash', o: { anchor: F => spHT(F, SP_HANDS).tip, r: 36, dur: 170 } },
  { at: 882, fx: 'shockwave', o: { anchor: F => spHT(F, SP_HANDS).tip, r1: 26, sq: 1, rings: 1, dur: 260, thick: 1 } },
  { at: 882, fx: 'sparkBurst', o: { anchor: F => spHT(F, SP_HANDS).tip, n: 24, spd: 240, dir: -56, arc: 50 } },
  { at: 885, fx: spCrackle, o: { at: F => spHT(F, SP_HANDS).tip, n: 3, r: 12, life: 520 } },
  { at: 900, sfx: () => { tone(1760, 0.5, 0.05, 'triangle', 0.6); noise(0.5, 5000, 1, 0.08, 'highpass', 0.5); } },
  // flung off the tip
  { at: 1030, call: F => { F.ride = false; if (F.small && fatAlive(F.target)) fatTargetMove(F, { knock: 16, lift: (F.tm ? F.tm.ty : 0) + 6, dur: 150 }); } },
  { at: 1190, target: { drop: true, dur: 220 } },
];
// the vault (bosses / elites): the spear stays in, you go up its haft
const SP_VAULT = [
  { at: 0, move: { gap: 25, dur: 120 }, call: F => { F.m1 = F.mv.tx; } },
  { at: 60, sfx: () => sfx.glint() },
  { at: 195, sfx: () => sfx.spear() },
  { at: 202, hit: 1.0, stop: 0.08, shake: 5, flash: 0.2, kick: 1.6, hy: 0.35, call: F => { F.T = fgS(F, F.m1 + 35, -23); } },
  { at: 202, fx: 'impactFlash', o: { anchor: F => F.T, r: 20, dur: 140 } },
  { at: 202, fx: 'sparkBurst', o: { anchor: F => F.T, n: 14, spd: 180, dir: -30, arc: 70 } },
  { at: 340, call: F => fgMove(F, F.m1 + 3, -2, 70, 'out'), sfx: () => sfx.jump() },
  { at: 340, fx: 'groundCrack', o: { anchor: 'player', dx: 2, len: 12, branches: 1, dur: 600, col: SP_COL } },
  { at: 410, call: F => fgMove(F, F.m1 + 7, -16, 90, 'linear') },
  { at: 500, call: F => fgMove(F, F.m1 + 18, -22, 130, 'out') },
  { at: 650, call: F => fgMove(F, F.m1 + 18, -24, 160, 'inout') },
  // the apex: the sky answers, a bolt onto you and down the spear into the boss
  { at: 540, fx: 'speedLines', o: { anchor: 'player', n: 6, dur: 140, band: [-50, -10], dir: 0 } },
  { at: 575, fx: spSkyBolt, o: { to: F => spHT(F, SV_HANDS).h, life: 170 }, sfx: fgThunder },
  { at: 590, fx: (c, t, F, e) => { const s = spHT(F, SV_HANDS); spSpiral(s.h, F.T, clamp(t / 190, 0, 1), F.n * 7 + Math.floor(t / 50), e.col, t < 190 ? 1 : 1 - (t - 190) / 180); }, o: { life: 370 } },
  { at: 770, hit: 0.8, stop: 0.06, shake: 6, flash: 0.32, kick: 1.0, x: 30, hy: 0.4 },
  { at: 770, fx: spCrackle, o: { at: F => F.T, n: 3, r: 11, life: 300 }, sfx: fgCrackle },
  { at: 780, cine: { dark: 0.62 } },
  // DRIVE IT HOME (beat 3): the whole weight down the haft, a lance of light down through the boss into the floor
  { at: 810, call: F => fgMove(F, F.m1 + 20, -16, 50, 'snap') },
  { at: 812, hit: 3.2, slow: 0.45, stop: 0.15, shake: 12, flash: 0.5, boom: true, name: true, kick: 2.2, kickY: 2.5, hy: 0.5 },
  { at: 812, call: F => {   // from above your head, down through the wound, into the floor
    const d = { x: Math.cos(1.05) * F.face, y: Math.sin(1.05) }, fl = F.tc().floor, E = { x: F.T.x + d.x * (fl - F.T.y) / d.y, y: fl };
    const L = (fl - (P.y - 70)) / d.y; spLance(F, { x: E.x - d.x * L, y: E.y - d.y * L }, d, L, { hold: 380 });
    F.fx('groundCrack', { anchor: () => E, len: 54, branches: 6, dur: 1300, col: SP_COL });
    F.fx('shockwave', { anchor: () => E, r1: 96, sq: 0.22, rings: 2, gap: 80, dur: 440 }); } },
  { at: 812, fx: 'impactFlash', o: { anchor: F => F.T, r: 36, dur: 170 } },
  { at: 812, fx: 'sparkBurst', o: { anchor: F => F.T, n: 24, spd: 240, dir: 60, arc: 60 } },
  { at: 815, fx: spCrackle, o: { at: F => F.T, n: 3, r: 14, life: 700 } },
  { at: 830, sfx: () => { tone(1760, 0.5, 0.05, 'triangle', 0.6); noise(0.5, 5000, 1, 0.08, 'highpass', 0.5); } },
  // wrench it free and drop back
  { at: 1060, call: F => fgMove(F, F.m1 + 6, 0, 140, 'in'), sfx: () => sfx.heavySwing() },
  { at: 1180, shake: 3, sfx: () => sfx.land(), fx: 'sparkBurst', o: { anchor: 'player', dx: 2, n: 6, spd: 90, dir: -90, arc: 160, col: '150,140,130' } },
];
const spShares = st => st.reduce((s, q) => s + (q.hit > 0 ? q.hit : 0), 0);
fatalityRegister('spear', {
  name: 'Skypiercer',
  col: SP_COL,
  tag: 'sp_fatal', tags: ['sp_drive', 'sp_heavy', 'riposte'],
  dur: 1600,
  steps: SP_SMALL,
  start(F) {
    F.variant = F.small ? 'hoist' : 'vault';
    if (!F.small) {   // bosses never move: the vault
      F.steps = SP_VAULT.map(s => ({ ...s })).sort((a, b) => a.at - b.at); F.si = 0; F.animAts = [];
      F.shareSum = spShares(F.steps);
      F.seg = fatSeg(F, ['sp_fatal_vault', 'sp_kk', 'sp_drive', 'riposte'], 0, F.dur);
      F.T = fgS(F, 60, -23);
    }
  },
  tick(F) { if (F.variant === 'hoist') spRide(F); },
  // the haft hums with light while it is lodged / while the foe rides it
  draw(F, t) {
    if (F.variant === 'vault' && F.T && t > 210 && t < 1060) {
      const s = spHT(F, SV_HANDS); if (t < 340) return;
      const a = 0.3 + 0.25 * Math.sin(t * 0.05);
      g.fillStyle = `rgba(${fatLite(F.col)},${a})`; fatLine(s.h.x, s.h.y, F.T.x, F.T.y);
    }
    if (F.variant === 'hoist' && t > 340 && t < 1030) { const s = spHT(F, SP_HANDS); F.light(s.tip.x, s.tip.y, 30, 0.35); }
  },
});

// ================================================================== BOW "Point-Blank Pyre"
// A kick that stuns, three arrows nocked at once (their heads smouldering at full draw), loosed point-blank into the foe;
// the bow is swept down and away like a struck match and the arrows ignite into a burning cross that flares and fades.
const BW_FIRE = { hot: '255,236,190', mid: '255,160,70', deep: '200,70,30', ash: '60,52,50' };
function pyArrowHead(F) {   // the nocked broadhead now (the overlay's own pixels), else the art's draw pose
  const tp = typeof bwTip === 'function' ? bwTip() : null;
  if (tp && Math.abs(tp.x - P.x) < 34 && tp.y < P.y - 4) return tp;
  return fgW(F, 20, -19);
}
function pyArrow(x, y, ang, len, a) {
  if (typeof bwDrawArrow === 'function') return bwDrawArrow(x, y, ang, len, a, 1, false);
  const c = Math.cos(ang), s = Math.sin(ang);
  for (let i = 0; i <= len; i++) { g.fillStyle = i <= 2 ? `rgba(232,238,252,${a})` : i >= len - 2 ? `rgba(190,60,50,${a})` : `rgba(176,150,110,${a})`; g.fillRect(Math.round(x - c * i), Math.round(y - s * i), 1, 1); }
}
// where the three arrows land: the foe's near face at mid height, a tight fan
function pyHits(F) {
  const c = F.tc(), hb = c.hb, near = F.face > 0 ? hb.x0 : hb.x1, nx = F.face > 0 ? Math.max(near + 7, P.x + 24) : Math.min(near - 7, P.x - 24), cy = clamp(P.y - 20, hb.y0 + 6, hb.y1 - 6);
  return [[-6, -0.12], [0, 0], [6, 0.12]].map(([dy, da]) => ({ x: nx + F.face * Math.abs(dy) * 0.3, y: cy + dy, ang: (F.face > 0 ? 0 : Math.PI) + da * F.face }));
}
// the burning cross: crossbar through the arrows, the stake from above them down to the floor
function pyCross(ctx, t, F, e) {
  const C = e.c, up = e.up, fl = e.fl, hw = e.hw, cad = Math.floor(t / 50), R = fatRng(F.n * 13 + cad);
  const grow = clamp(t / 110, 0, 1), flare = t < 240 ? 1 - t / 240 : 0, kf = clamp((t - 640) / 620, 0, 1), live = 1 - kf;
  const hot = fatMix(BW_FIRE.hot, F.col, 0.2), mid = fatMix(BW_FIRE.mid, F.col, 0.45), deep = fatMix(BW_FIRE.deep, F.col, 0.25);
  const cx = Math.round(C.x), cy = Math.round(C.y), top = Math.round(cy - up * grow), bot = Math.round(cy + (fl - cy) * grow);
  const x0 = Math.round(cx - hw * grow), x1 = Math.round(cx + hw * grow);
  const fh = (13 + 8 * flare) * (0.25 + 0.75 * live);
  // one tongue of flame licking up from (x, y): white-hot root, orange body, a dithered red tip that sways
  const tongue = (x, y, h, seed) => {
    const n = Math.round(h * (0.4 + 0.6 * fatHash(seed, cad))), sway = fatHash(seed * 7, cad) < 0.5 ? -1 : 1; if (n < 1) return;
    for (let i = 0; i < n; i++) {
      const k = i / n, xx = x + (k > 0.55 ? sway : 0) + (k > 0.85 ? sway : 0), yy = y - i;
      if (k > 0.5 && !fatDith(xx, yy, 1.25 - k)) continue;
      g.fillStyle = `rgba(${k < 0.25 ? hot : k < 0.6 ? mid : deep},${(1 - k * 0.5) * (0.35 + 0.65 * live)})`; g.fillRect(xx, yy, 1, 1);
    }
  };
  // the burning beams: 3 px cores, hot while they burn, cooling to ember red, then breaking up from the ends
  const core = kf < 0.45 ? hot : fatMix(mid, deep, clamp((kf - 0.45) / 0.55, 0, 1)), ca = kf < 0.85 ? 1 : (1 - kf) / 0.15;
  for (let y = top; y <= bot; y++) {
    const u = Math.abs((y - cy) / Math.max(1, y < cy ? up : fl - cy));
    if (kf > 0 && !fatDith(cx, y, 1 - kf * (0.5 + u))) continue;
    g.fillStyle = `rgba(${core},${ca})`; g.fillRect(cx - 1, y, 3, 1);
    if (live > 0.05 && y < bot - 1 && fatHash(y, cad) < 0.6) { const sd = fatHash(y * 3, cad) < 0.5 ? -2 : 2; tongue(cx + sd, y, fh * (0.3 + 0.35 * fatHash(y, 5)), y); if (fatHash(y, cad + 3) < 0.35) tongue(cx + sd + (sd > 0 ? 1 : -1), y + 1, fh * 0.25, y + 7); }
  }
  for (let x = x0; x <= x1; x++) {
    const u = Math.abs(x - cx) / Math.max(1, hw);
    if (kf > 0 && !fatDith(x, cy, 1 - kf * (0.5 + u))) continue;
    g.fillStyle = `rgba(${core},${ca})`; g.fillRect(x, cy - 1, 1, 3);
    if (live > 0.05) { tongue(x, cy - 2, fh * (1 - u * 0.55), x + 50); if (fatHash(x, cad + 1) < 0.3) { g.fillStyle = `rgba(${mid},${0.7 * live})`; g.fillRect(x, cy + 2, 1, 1); } }
  }
  if (live > 0.05) for (let i = -1; i <= 1; i++) tongue(cx + i, top - 1, fh * (1.3 - Math.abs(i) * 0.4), i + 99);
  // the heart of it, where the arrows went in
  if (t < 320 && typeof mvStar === 'function') mvStar(cx, cy, 4 + 5 * flare, hot, 1 - t / 320);
  if (live > 0 && R() < 0.8) fatPart({ k: 'ember', x: cx + (R() - 0.5) * hw * 2, y: cy - R() * up, vx: (R() - 0.5) * 20, vy: -25 - R() * 40, col: R() < 0.4 ? hot : mid, life: 0.5 + R() * 0.6, max: 1.1, g: -14, ph: R() * 6 });
  addLight(cx, cy - up * 0.3, 70 + 30 * flare, F.col, Math.min(0.8, (0.5 + 0.25 * flare) * live + 0.1 * (1 - kf)));
}
// the pyre as a toolkit primitive (own file): the fire in the glow layer, a smoky backing in the lit layer so it reads on a
// bright boss, and smoke that rises off it as it burns down
FATFX.fgPyre = {
  init(e) {   // o.c (centre, default the anchor), o.up (stake above it), o.hw (half crossbar), o.fl (floor y)
    const o = e.o; e.c = o.c || { x: e.x, y: e.y }; e.up = o.up ?? 36; e.hw = o.hw ?? 16; e.fl = Math.round(o.fl ?? fatTC(e.F).floor); e.life = o.life ?? 1500; e.smoke = [];
  },
  update(e, dt) {
    if (e.t > 500 && e.t < 1250 && Math.random() < 0.5) e.smoke.push({ x: e.c.x + (Math.random() - 0.5) * e.hw * 1.6, y: e.c.y - Math.random() * e.up, r: 2 + Math.random() * 2, vy: -14 - Math.random() * 12, vx: (Math.random() - 0.5) * 6, t: 0, max: 0.9 + Math.random() * 0.6 });
    for (const q of e.smoke) { q.t += dt; q.x += q.vx * dt; q.y += q.vy * dt; q.r += 3 * dt; }
    e.smoke = e.smoke.filter(q => q.t < q.max);
  },
  lit(e) {
    const k = clamp(e.t / 110, 0, 1) * (1 - clamp((e.t - 900) / 500, 0, 1)), cx = Math.round(e.c.x), cy = Math.round(e.c.y);
    if (k > 0.02) {   // soot behind the flames: a dithered dark band round both beams
      g.fillStyle = `rgba(14,8,8,${0.55 * k})`;
      for (let y = Math.round(cy - e.up - 6); y <= e.fl; y++) for (let x = cx - 4; x <= cx + 4; x++) if (fatDith(x, y, 0.55 - Math.abs(x - cx) * 0.09)) g.fillRect(x, y, 1, 1);
      for (let x = Math.round(cx - e.hw - 2); x <= cx + e.hw + 2; x++) for (let y = cy - 12; y <= cy + 3; y++) if (Math.abs(x - cx) > 4 && fatDith(x, y, (y < cy ? 0.5 - (cy - y) * 0.035 : 0.45 - (y - cy) * 0.12))) g.fillRect(x, y, 1, 1);
    }
    for (const q of e.smoke) {   // smoke rising off it
      const a = 0.45 * (1 - q.t / q.max), r = Math.round(q.r); g.fillStyle = `rgba(30,24,26,${a})`;
      for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) if (x * x + y * y <= r * r && fatDith(Math.round(q.x) + x, Math.round(q.y) + y, 0.6)) g.fillRect(Math.round(q.x) + x, Math.round(q.y) + y, 1, 1);
    }
  },
  glow(e) { if (e.t < 1300) pyCross(g, e.t, e.F, e); },
};
fatalityRegister('bow', {
  name: 'Point-Blank Pyre',
  col: '255,145,60',
  tag: 'bw_fatal', tags: ['bw_recoil', 'bw_power', 'riposte'],
  dur: 1500,
  steps: [
    { at: 0, move: { gap: 4, dur: 100 } },
    { at: 150, sfx: () => sfx.swing() },
    // the KICK (beat 1): a heel to the chest that stuns; small foes are shoved back to point-blank range
    { at: 175, hit: 0.8, stop: 0.08, shake: 5, flash: 0.15, kick: 1.6, hy: 0.55, target: { knock: 10, dur: 130 },
      sfx: () => { sfx.hit(); noise(0.15, 220, 1, 0.3, 'lowpass'); } },
    { at: 175, fx: 'shockwave', o: { anchor: F => fgW(F, 10, -13), r0: 2, r1: 20, sq: 1.3, rings: 2, gap: 50, dur: 220, thick: 1 } },
    { at: 175, fx: 'sparkBurst', o: { anchor: F => fgW(F, 10, -13), n: 8, spd: 120, dir: 0, arc: 100, col: '230,210,190' } },
    { at: 300, target: { pin: true } },
    // three arrows on the string; at full draw their heads catch
    { at: 385, sfx: () => { if (typeof bwCreak === 'function') bwCreak(2); } },
    { at: 500, sfx: () => { if (typeof bwCreak === 'function') bwCreak(3); noise(0.4, 700, 0.8, 0.06, 'bandpass', 1.4); } },
    { at: 640, cine: { dark: 0.6 } },
    // LOOSE (beat 2): point-blank, all three in a tight fan
    { at: 682, hit: 1.4, stop: 0.09, shake: 6, flash: 0.25, kick: 1.8, hy: 0.45, call: F => { F.hits = pyHits(F); F.shotAt = F.t; },
      sfx: () => { if (typeof bwTwang === 'function') { bwTwang(3); bwTwang(2); } sfx.hit(); } },
    { at: 682, fx: 'sparkBurst', o: { anchor: F => pyHits(F)[1], n: 12, spd: 160, dir: 180, arc: 80 } },
    { at: 682, fx: 'impactFlash', o: { anchor: F => pyHits(F)[1], r: 18, dur: 120 } },
    { at: 760, sfx: () => noise(0.5, 900, 0.7, 0.07, 'bandpass', 1.6) },
    { at: 900, sfx: () => noise(0.25, 1600, 1, 0.08, 'bandpass', 2) },
    // THE PYRE (beat 3)
    { at: 990, hit: 2.8, slow: 0.45, stop: 0.15, shake: 11, flash: 0.5, boom: true, name: true, kick: 2.2, hy: 0.45,
      sfx: () => { sfx.fire(); noise(0.9, 500, 0.6, 0.45, 'lowpass', 2.2); } },
    { at: 990, call: F => {
      const hs = F.hits || pyHits(F), c = F.tc(), C = { x: Math.round(hs[1].x), y: Math.round(hs[1].y) };
      const hb = c.hb, up = clamp((C.y - hb.y0) * 0.9 + 10, 24, 52), hw = clamp((hb.y1 - hb.y0) * 0.32, 13, 24);
      F.fx('fgPyre', { anchor: () => C, c: C, up, hw, fl: Math.round(c.floor), life: 1500 });
      F.fx('groundCrack', { anchor: () => ({ x: C.x, y: c.floor }), len: 30, branches: 4, dur: 1300, col: '255,150,60' });
      F.fx('shockwave', { anchor: () => ({ x: C.x, y: c.floor }), r1: 70, sq: 0.22, rings: 2, gap: 80, dur: 420 });
      F.fx('impactFlash', { anchor: () => C, r: 34, dur: 170 });
      F.fx('emberBurst', { anchor: () => ({ x: C.x, y: c.floor }), n: 22, w: 30, rise: 110, col: '255,170,80' });
      F.fx('sparkBurst', { anchor: () => C, n: 20, spd: 220, dir: -90, arc: 160 });
    } },
    { at: 1300, target: { drop: true } },
  ],
  // the extra shafts on the string, the shots in flight, the arrows standing in the foe
  drawLit(F, t) {
    if (t >= 380 && t < 682) {
      const tp = pyArrowHead(F), base = F.face > 0 ? 0 : Math.PI, nock = { x: tp.x - F.face * 13, y: tp.y };
      for (const da of [-0.14, 0.14]) { const a = base + da * F.face; pyArrow(nock.x + Math.cos(a) * 13, nock.y + Math.sin(a) * 13, a, 11, 1); }
    }
    if (F.hits) {
      const k = clamp((t - F.shotAt) / 40, 0, 1);
      for (const h of F.hits) {
        const char = clamp((t - 990) / 400, 0, 1);
        if (k < 1) { const sx = P.x + F.face * 14; pyArrow(lerp(sx, h.x, k), lerp(P.y - 20, h.y, k), h.ang, 11, 1); continue; }
        // stuck: only the back half shows; it chars once the pyre takes it
        const c = Math.cos(h.ang), s = Math.sin(h.ang);
        for (let i = 3; i <= 9; i++) { if (char > 0 && i > 9 - char * 7) continue; g.fillStyle = char > 0 ? `rgba(${Math.round(120 - 70 * char)},${Math.round(70 - 30 * char)},50,1)` : i >= 8 ? 'rgba(190,60,50,1)' : 'rgba(150,124,90,1)'; g.fillRect(Math.round(h.x - c * i), Math.round(h.y - s * i), 1, 1); }
      }
    }
  },
  draw(F, t) {
    // the heads smoulder at full draw
    if (t >= 470 && t < 682) {
      const tp = pyArrowHead(F), k = clamp((t - 470) / 200, 0, 1), base = F.face > 0 ? 0 : Math.PI, nock = { x: tp.x - F.face * 13, y: tp.y };
      for (const da of [-0.14, 0, 0.14]) { const a = base + da * F.face, x = Math.round(nock.x + Math.cos(a) * 13), y = Math.round(nock.y + Math.sin(a) * 13);
        g.fillStyle = `rgba(255,${150 + Math.round(60 * Math.random())},70,${0.5 + 0.5 * k})`; g.fillRect(x, y, 1, 1); if (k > 0.5 && Math.random() < 0.5) g.fillRect(x, y - 1, 1, 1);
        if (Math.random() < 0.12 * k) fatPart({ k: 'ember', x, y, vx: (Math.random() - 0.5) * 10, vy: -15 - Math.random() * 20, col: '255,160,70', life: 0.4, max: 0.4, g: -8, ph: 0 }); }
      F.light(tp.x, tp.y, 18 + 10 * k, 0.3 + 0.3 * k);
    }
    if (F.hits && t >= F.shotAt) {
      // the flight streaks, then the wounds glowing hotter until the pyre
      if (t - F.shotAt < 90) { const k = (t - F.shotAt) / 90; g.fillStyle = `rgba(${fatLite(F.col)},${0.8 * (1 - k)})`; for (const h of F.hits) fatLine(P.x + F.face * 14, P.y - 20, h.x, h.y); }
      if (t < 990) { const k = clamp((t - F.shotAt - 60) / 250, 0, 1);
        for (const h of F.hits) { g.fillStyle = `rgba(255,${120 + Math.round(80 * k)},60,${0.4 + 0.6 * k * (0.8 + 0.2 * Math.sin(t * 0.06 + h.y))})`; g.fillRect(Math.round(h.x), Math.round(h.y), 1, 1); g.fillRect(Math.round(h.x - Math.cos(h.ang)), Math.round(h.y), 1, 1);
          if (Math.random() < 0.15 * k) fatPart({ k: 'ember', x: h.x, y: h.y, vx: (Math.random() - 0.5) * 14, vy: -18 - Math.random() * 25, col: '255,150,60', life: 0.5, max: 0.5, g: -10, ph: 0 }); }
        F.light(F.hits[1].x, F.hits[1].y, 26 + 20 * k, 0.25 + 0.35 * k); }
    }
  },
});

// ================================================================== the spear's own guard K (76_mech_guard.js guardUpdate starts
// sp_heavy / the counter directly, not through the framework's K paths): on a critable foe, K out of the heavy guard is the
// fatality too, like the shield's guard K.
if (typeof MV !== 'undefined' && MV.types && MV.types.spear && typeof MV.types.spear.guardUpdate === 'function') {
  const T = MV.types.spear, own = T.guardUpdate;
  T.guardUpdate = function (dt, ax, grav) {
    if (P.guardKind === 'spear' && peek('heavy') && P.ground && typeof fatReady === 'function' && critTarget() && !FAT.on && state === 'play') {
      take('heavy'); P.guardKind = null; P.spPower = 0;
      if (fatalityStart()) return true;
    }
    return own.apply(this, arguments);
  };
}

if (typeof window !== 'undefined' && window.__game) window.__game.fguard = { FG, spHT, pyHits, SP_HANDS, SV_HANDS };
