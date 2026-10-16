// ------------------------------------------------------------------ v16 FATALITIES: the blade group (Longsword; the Katana is added here
// by the blade agent). Choreography on the fatality clock, in step with art/player_v16_fatal_blade.py (frame starts):
//   ls_fatal  0 step | 90 lift | 200 PLANT | 330 kneel | 450 gather peak | 530 RIP UP | 575 rising | 635 apex (hold)
//             835 GREAT SLASH | 875 impact | 925 low hold | 1225 rise | 1425 recover | 1600 end

// ================================================================== LONGSWORD "Ashen Verdict"
// Plant the blade point-down for a heartbeat while light gathers along it, wrench it up in a rising cut, then a huge
// descending slash: a translucent aura blade three times the sword follows the swing into the floor and leaves a crescent
// of light that lingers and shatters.
fatalityRegister('longsword', {
  name: 'Ashen Verdict',
  col: '255,222,170',
  tag: 'ls_fatal', tags: ['ls_crit', 'riposte'],
  dur: 1600,
  steps: [
    { at: 0, move: { gap: 10, dur: 120 } },
    // the plant: a thud, a hairline crack, sparks off the stone
    { at: 205, shake: 3, stop: 0.03, sfx: () => { sfx.land(); tone(160, 0.25, 0.1, 'triangle', 0.6); } },
    { at: 205, fx: 'groundCrack', o: { anchor: 'player', dx: 13, dy: 0, len: 16, branches: 2, dur: 900, col: '255,214,150' } },
    { at: 205, fx: 'sparkBurst', o: { anchor: 'player', dx: 13, dy: -1, n: 8, spd: 120, dir: -90, arc: 140 } },
    // the gathering: motes drawn in from a ring into the blade, the blade lighting from the point up
    { at: 230, fx: 'soulWisps', o: { anchor: 'player', dx: 10, dy: -14, from: 'ring', r: 48, n: 10, rise: 120, dur: 420, stagger: 18, to: 'tip' } },
    { at: 340, fx: 'soulWisps', o: { anchor: 'player', dx: 10, dy: -14, from: 'ring', r: 40, n: 8, rise: 90, dur: 300, stagger: 16, to: 'tip' } },
    { at: 460, sfx: () => sfx.glint() },
    // RIP UP: the rising cut (beat 1)
    { at: 540, hit: 1.0, stop: 0.07, shake: 5, flash: 0.2, kick: 1.4, hy: 0.55 },
    { at: 540, fx: 'crescent', o: { r: 34, thick: 9, a0: 92, a1: -100, grow: 45, linger: 110, shatter: 170, shards: 8 } },
    { at: 540, fx: 'sparkBurst', o: { n: 14, spd: 190 } },
    { at: 540, fx: 'emberBurst', o: { anchor: 'player', dx: 14, dy: 0, n: 12, rise: 80, col: '255,190,120' } },
    // the apex: the aura blade forms over the raised sword, waits, and follows the great slash into the floor
    { at: 590, fx: 'auraBlade', o: { len: 62, w: 9, keys: [[0, -100, 0], [60, -140, 0.8], [245, -148, 1], [295, 74, 1, 'snap'], [430, 72, 0.85], [560, 72, 0]] } },
    { at: 600, sfx: () => { tone(150, 0.28, 0.06, 'sawtooth', 2.4); noise(0.25, 1400, 0.8, 0.08, 'bandpass', 2); } },
    { at: 820, fx: 'speedLines', o: { n: 8, dur: 150, band: [-60, -6] } },
    { at: 835, sfx: () => sfx.heavySwing() },
    // THE VERDICT (beat 2): slow-mo, the flash, the boom, the name
    { at: 862, hit: 4.0, slow: 0.45, stop: 0.15, shake: 11, flash: 0.55, boom: true, name: true, kick: 2.6, hy: 0.45 },
    { at: 862, fx: 'crescent', o: { r: 66, thick: 19, a0: -152, a1: 74, grow: 40, linger: 430, shatter: 380, shards: 34, floor: true } },
    { at: 862, fx: 'impactFlash', o: { r: 42, dur: 180 } },
    { at: 862, fx: 'shockwave', o: { anchor: 'ground', r1: 104, sq: 0.22, rings: 2, gap: 80, dur: 460 } },
    { at: 862, fx: 'groundCrack', o: { anchor: 'player', dx: 30, len: 74, branches: 6, dur: 1300, col: '255,170,90' } },
    { at: 862, fx: 'sparkBurst', o: { n: 26, spd: 250 } },
    { at: 880, fx: 'emberBurst', o: { anchor: 'ground', n: 20, w: 40, rise: 100 } },
    { at: 1330, sfx: () => { noise(0.3, 4200, 1.4, 0.14, 'highpass'); tone(1900, 0.25, 0.04, 'triangle', 1.6); } },
  ],
  // the blade itself lights up from the point to the guard while it stands in the floor (230 .. 540 ms)
  draw(F, t) {
    if (t < 215 || t > 545) return;
    const tp = F.tip(), k = clamp((t - 215) / 260, 0, 1), x = Math.round(tp.x), y0 = Math.round(F.y0), y1 = Math.round(y0 - 3 - 15 * k);
    g.fillStyle = `rgba(${fatLite(F.col)},${0.55 + 0.35 * k})`; g.fillRect(x, y1, 1, y0 - y1);
    g.fillStyle = `rgba(${fatHot(F.col)},1)`; g.fillRect(x, y1, 1, 2);
    if (k >= 1 && typeof mvStar === 'function') mvStar(x, y1 - 1, 2 + Math.round(2 * Math.abs(Math.sin(t * 0.03))), fatHot(F.col), 0.9);
    addLight(x, y0 - 10, 30 + 24 * k, F.col, 0.35 + 0.35 * k);
  },
});

// ================================================================== shared bits (the blade group's own primitives)
// fbAnchorCut(F): the point the katana's cut passes through (the target's hurtbox at 42% of its height)
function fbCutPt(F) { const c = F.tc(), hb = c.hb; return { x: c.x, y: lerp(hb.y0, hb.y1, 0.42) }; }
// SPLIT: the target is drawn twice for a moment, clipped above / below a tilted line, the upper half slid along it (lights and
// glow of the second pass are muted so nothing doubles). F.split = { x, y, ang (deg), k (0..1 slide), dx px }
function fbSplitOn(F) {
  const t = F.target; if (!t || t._fbSplit) return;
  const own = Object.prototype.hasOwnProperty.call(t, 'draw') ? t.draw : undefined, base = own || Object.getPrototypeOf(t).draw;
  if (typeof base !== 'function') return;
  t._fbSplit = { own };
  t.draw = function () {
    const s = F.split; if (!s || !(s.k > 0.02)) return base.apply(this, arguments);
    const tn = Math.tan(s.ang * Math.PI / 180) * F.face0, X0 = s.x - 400, X1 = s.x + 400, yl = x => s.y + (x - s.x) * tn;
    const half = (up, fn) => { g.save(); g.beginPath(); g.moveTo(X0, yl(X0)); g.lineTo(X1, yl(X1)); g.lineTo(X1, up ? -1e5 : 1e5); g.lineTo(X0, up ? -1e5 : 1e5); g.closePath(); g.clip(); try { fn(); } finally { g.restore(); } };
    half(false, () => base.apply(this, arguments));
    const aL = addLight, dG = drawGlow;
    addLight = () => {}; drawGlow = () => {};
    try { half(true, () => { const d = s.dx * s.k; g.translate(Math.round(d * F.face0), Math.round(d * tn * F.face0) - (s.k > 0.5 ? 1 : 0)); base.apply(this, arguments); }); }
    finally { addLight = aL; drawGlow = dG; }
  };
}
function fbSplitOff(F) { const t = F && F.target; if (!t || !t._fbSplit) return; const o = t._fbSplit; delete t._fbSplit; if (o.own) t.draw = o.own; else delete t.draw; F.split = null; }

// ================================================================== KATANA "Moonsever"
// An iai crouch, a blink dash THROUGH the foe (the draw, afterimages), a still zanshin behind it, the chiburi flick, the
// blade slid home slowly -- CLICK -- and a screen-wide horizontal slash line splits the foe (its upper half slides along
// the cut) and the pale moon that rose behind it, holds, then bursts into pale light.
// kt_fatal: 0 crouch | 300 DASH | 345 through | 400 zanshin | 660 chiburi | 720 sheathe .. | 990 CLICK | 1200 stand | 1500
const KT_LINE = { len: 460, ang: -4, grow: 55, hold: 400, burst: 330 };
function ktMoon(c, t, F, e) {   // custom fx (spawned at 150 ms): a pale moon ring behind the foe, cut in two at the click
  if (!e.m) { const p = fbCutPt(F), hb = F.tc().hb; e.m = { x: Math.round(p.x), y: Math.round(p.y), r: Math.round(clamp((hb.y1 - hb.y0) * 0.7, 24, 56)) }; }
  const m = e.m, cut = 840, col = F.col;
  const ring = (r, a, half, ox, oy) => {   // half: 0 whole, -1 upper, 1 lower
    const n = Math.ceil(Math.PI * r * 2.4); let px = null, py = null;
    for (let i = 0; i < n; i++) {
      const q = i / n * 6.2832, x = Math.round(m.x + Math.cos(q) * r + ox), y0 = m.y + Math.sin(q) * r;
      if (half < 0 && y0 > m.y) continue; if (half > 0 && y0 <= m.y) continue;
      const y = Math.round(y0 + oy); if (x === px && y === py) continue; px = x; py = y;
      if (a < 1 && !fatDith(x, y, a)) continue;
      g.fillRect(x, y, 1, 1);
    }
  };
  if (t < cut) {
    const a = 0.32 * fatEase('inout', t / cut);
    g.fillStyle = `rgba(${fatLite(col)},${a})`; ring(m.r, 1, 0, 0, 0);
    g.fillStyle = `rgba(${col},${a * 0.6})`; ring(m.r - 3, 0.5, 0, 0, 0);
    if (t > cut - 160) addLight(m.x, m.y, m.r * 1.2, col, 0.25 * (t - cut + 160) / 160);
    return;
  }
  const u = t - cut, k = clamp(u / 900, 0, 1), s = 2 + 7 * fatEase('out', k), a = u < 60 ? 0.9 : 0.9 * (1 - k);
  if (a <= 0.02) return;
  const f = F.face0;
  g.fillStyle = `rgba(${fatHot(col)},${a})`; ring(m.r, 1 - k * 0.7, -1, s * f, -s * 0.25); ring(m.r, 1 - k * 0.7, 1, -s * f * 0.6, s * 0.2);
  g.fillStyle = `rgba(${col},${a * 0.55})`; ring(m.r - 3, 0.6 - k * 0.5, -1, s * f, -s * 0.25); ring(m.r - 3, 0.6 - k * 0.5, 1, -s * f * 0.6, s * 0.2);
}
function ktHair(c, t, F, e) {   // custom fx: the hairline the dash leaves through the foe (1 px, fading, a little sheen running along it)
  if (!e.m) { const p = fbCutPt(F), hb = F.tc().hb; e.m = { x0: hb.x0 - 14, x1: hb.x1 + 14, y: Math.round(p.y) }; }
  const m = e.m, a = 1 - t / e.life, tn = Math.tan(KT_LINE.ang * Math.PI / 180) * F.face0, cx = (m.x0 + m.x1) / 2;
  const yl = x => Math.round(m.y + (x - cx) * tn);
  g.fillStyle = `rgba(${fatLite(F.col)},${0.7 * a})`;
  for (let x = Math.round(m.x0); x <= m.x1; x++) if (fatDith(x, 0, 0.35 + 0.65 * a)) g.fillRect(x, yl(x), 1, 1);
  const sx = Math.round(lerp(F.face0 > 0 ? m.x0 : m.x1, F.face0 > 0 ? m.x1 : m.x0, clamp(t / 140, 0, 1)));
  g.fillStyle = `rgba(${fatHot(F.col)},${a})`; g.fillRect(sx - 3, yl(sx), 7, 1);
}
fatalityRegister('katana', {
  name: 'Moonsever',
  col: '205,225,255',
  tag: 'kt_fatal', tags: ['kt_heavy', 'riposte'],
  dur: 1500,
  steps: [
    { at: 0, move: { gap: 16, dur: 110 } },
    { at: 0, sfx: () => { tone(220, 0.6, 0.05, 'sine', 0.7); noise(0.4, 3000, 0.6, 0.03, 'highpass'); } },
    { at: 150, fx: ktMoon, o: { life: 1750 } },
    { at: 235, sfx: () => { sfx.glint(); tone(1760, 0.08, 0.03, 'triangle', 1); } },   // the thumb on the guard
    { at: 230, fx: 'soulWisps', o: { anchor: 'player', dy: -12, from: 'ring', r: 30, n: 6, rise: 80, dur: 260, stagger: 10, to: 'player' } },
    // THE BLINK: through the foe in 50 ms, afterimages strung along the dash
    { at: 300, move: { through: 30, dur: 55, ease: 'snap' }, ghosts: { dur: 110, every: 12, alpha: 0.42, life: 0.24, col: '#6a7db8' } },
    { at: 300, fx: 'speedLines', o: { n: 14, dur: 220, band: [-34, -2] } },
    { at: 300, sfx: () => { sfx.swing(); noise(0.18, 5200, 1.2, 0.1, 'highpass', 0.5); } },
    { at: 322, hit: 1.0, stop: 0.05, shake: 3, flash: 0.14, kick: 1.2, zoom: 0.3, hy: 0.42 },
    { at: 322, fx: ktHair, o: { life: 520 } },
    { at: 323, call: F => { const t = F.target; if (t && t.flash > 0.2) t.flash = 0.2; } },   // the cut isn't felt yet: no white hit flash
    { at: 322, fx: 'sparkBurst', o: { anchor: fbCutPt, n: 9, spd: 160, dir: 0, arc: 40 } },
    // zanshin: still. the chiburi flick, then the slow sheathe
    { at: 662, fx: 'sparkBurst', o: { anchor: 'tip', n: 5, spd: 90, dir: 70, arc: 40 } },
    { at: 662, sfx: () => noise(0.08, 2600, 1, 0.08, 'bandpass') },
    { at: 720, sfx: () => { noise(0.27, 6000, 0.5, 0.05, 'highpass', 0.7); tone(3200, 0.24, 0.012, 'sine', 0.8); } },
    // CLICK: home -- and the line splits the screen
    { at: 990, sfx: () => { tone(2600, 0.04, 0.12, 'square', 0.6); noise(0.05, 4000, 2, 0.12, 'bandpass'); } },
    { at: 990, hit: 4.0, slow: 0.5, stop: 0.16, shake: 10, flash: 0.5, boom: true, name: true, kick: 2.2, hy: 0.42 },
    { at: 990, fx: 'slashLine', o: { anchor: fbCutPt, len: KT_LINE.len, ang: KT_LINE.ang, thick: 2, grow: KT_LINE.grow, hold: KT_LINE.hold, burst: KT_LINE.burst, sparks: 34 } },
    { at: 990, fx: 'impactFlash', o: { anchor: fbCutPt, r: 34, dur: 170 } },
    { at: 990, call: F => { const p = fbCutPt(F); F.split = { x: p.x, y: Math.round(p.y), ang: KT_LINE.ang, k: 0, dx: 4 }; fbSplitOn(F); } },
    { at: 1000, cine: { dark: 0.62 } },
    { at: 1440, fx: 'emberBurst', o: { anchor: fbCutPt, n: 18, w: 90, h: 4, rise: 40, spd: 30, col: '226,236,255' } },
    { at: 1440, sfx: () => { noise(0.45, 5200, 1.3, 0.12, 'highpass'); tone(2093, 0.4, 0.035, 'triangle', 1.5); } },
  ],
  tick(F) {   // the upper half slides along the cut while the line holds, and drops back as it bursts
    const s = F.split; if (!s) return;
    const u = F.t - 990, burst = KT_LINE.grow + KT_LINE.hold;
    s.k = u < burst ? fatEase('out', clamp(u / 140, 0, 1)) : 1 - clamp((u - burst) / 90, 0, 1);
    if (u > burst + 100) fbSplitOff(F);
  },
  end(F) { fbSplitOff(F); },
  // the drawn blade carries a cold gleam while it's out (zanshin .. sheathe)
  draw(F, t) {
    if (t < 345 || t > 990) return;
    const tp = F.tip(), a = t < 700 ? 0.6 : 0.6 * (990 - t) / 290;
    addLight(tp.x, tp.y, 22, F.col, 0.35 * a);
    if (t > 560 && t < 660 && typeof mvStar === 'function') mvStar(Math.round(tp.x), Math.round(tp.y), 2 + Math.round(Math.abs(Math.sin(t * 0.04)) * 2), fatHot(F.col), a);
  },
});

// ================================================================== SWITCH AXE "Grinder's Mercy"
// The blade rammed into the foe, the mechanism unfolds INSIDE it (the axe head rides up, the blade swings back: the forms
// step sword -> axe on the cels), the chain grinds with sparks pouring and ember seams spreading through the foe from the
// head, then the phial bursts: a fireball out of the wound. Works from either form and ends in the one it started in:
// sx_fatal (sword: folds back after the burst) / sx_fatal_a (axe: the blade jack-knifes out for the stab, ends on the
// shoulder). The Switch Gauge, the lock and the form are frozen for the fatality (no drain, no vent, no bleed).
// sx_fatal(_a): 0 draw back | 280 STAB | 420 unlatch | 480 swing | 540 slide | 600 LOCK | 660 grind .. | 1150 BURST | 1200 thrown up | 1300 fold / carry | 1700
const SX_FAT = { ember: '255,150,60', hot: '255,236,170', deep: '196,72,30' };
function sxfHead(F) { const tp = F.tip(); return { x: tp.x - F.face0 * 4, y: tp.y }; }   // the axe head / blade point in the foe
function sxfSeams(c, t, F, e) {   // custom fx: molten seams branching through the foe from the head, cooling after the burst
  if (!e.m) {
    const hb = F.tc().hb, h = sxfHead(F), x = clamp(h.x, hb.x0 + 2, hb.x1 - 2), y = clamp(h.y, hb.y0 + 2, hb.y1 - 2), R = fatRng(F.n * 17 + 5), L = [];
    const big = Math.max(hb.x1 - hb.x0, hb.y1 - hb.y0);
    for (let i = 0; i < 11; i++) {
      let a = R() * 6.2832, px = x, py = y; const pts = [[px, py]], n = 3 + Math.floor(R() * 4), st = clamp(big / 10, 3, 9);
      for (let j = 0; j < n; j++) { a += (R() - 0.5) * 1.3; px += Math.cos(a) * st * (0.7 + R() * 0.6); py += Math.sin(a) * st * (0.7 + R() * 0.6); px = clamp(px, hb.x0, hb.x1); py = clamp(py, hb.y0, hb.y1); pts.push([px, py]); }
      L.push({ pts, d: R() * 0.5 });
    }
    e.m = { L, x, y };
  }
  const burstAt = 550, grow = clamp(t / burstAt, 0, 1), after = t > burstAt ? (t - burstAt) / (e.life - burstAt) : 0;
  const reach = after > 0 ? 1 : grow;
  for (const s of e.m.L) {
    const show = clamp((reach - s.d) / (1 - s.d), 0, 1), n = s.pts.length - 1, upto = show * n;
    for (let i = 0; i < n && i < upto; i++) {
      const [ax, ay] = s.pts[i], [bx, by] = s.pts[i + 1], f = Math.min(1, upto - i), q = i / n;
      const col = after < 0.15 && q < 0.5 ? SX_FAT.hot : after < 0.5 ? SX_FAT.ember : SX_FAT.deep;
      const a = after > 0 ? (1 - after) * (after < 0.08 ? 1 : 0.9) : (0.6 + 0.4 * Math.abs(Math.sin(t * 0.03 + i))) * (1 - q * 0.3);
      g.fillStyle = `rgba(${col},${a})`; fatLine(ax, ay, lerp(ax, bx, f), lerp(ay, by, f));
    }
  }
  if (after < 1) addLight(e.m.x, e.m.y, 30, SX_FAT.ember, 0.35 * (1 - after) * (0.6 + 0.4 * grow));
}
function sxfBlast(c, t, F, e) {   // custom fx: the phial burst -- a ragged ball of fire tongues out of the wound, cooling fast
  if (!e.m) { const h = sxfHead(F), R = fatRng(F.n * 29 + 3); e.m = { x: Math.round(h.x), y: Math.round(h.y), rays: Array.from({ length: 34 }, (_, i) => ({ a: i / 34 * 6.2832 + R() * 0.2, l: 0.55 + R() * 0.45, w: R() })) }; }
  const m = e.m, k = t / e.life, Rr = 46 * fatEase('snap', clamp(t / 200, 0, 1)), a = t < 140 ? 1 : 1 - (t - 140) / (e.life - 140);
  if (a <= 0) return;
  // the core: a dithered disc, white-hot then gone
  if (t < 220) {
    const rc = Math.round(Rr * 0.45), ak = 1 - t / 220;
    fatRaster(m.x - rc, m.y - rc, m.x + rc, m.y + rc, (x, y) => { const d = Math.hypot(x + 0.5 - m.x, y + 0.5 - m.y) / Math.max(1, rc); return d > 1 ? 0 : !fatDith(x, y, ak * (1.15 - d)) ? 0 : d < 0.5 ? 1 : 2; },
      [null, `rgba(${SX_FAT.hot},${ak})`, `rgba(${SX_FAT.ember},${0.8 * ak})`]);
  }
  // the tongues: 1-px rays, hot at the root, ember, then deep red tips, curling up as they cool
  for (const r of m.rays) {
    const L = Rr * r.l, lift = k * 10 * (0.5 + r.w), x0 = m.x + Math.cos(r.a) * L * 0.35, y0 = m.y + Math.sin(r.a) * L * 0.35;
    const x1 = m.x + Math.cos(r.a) * L, y1 = m.y + Math.sin(r.a) * L * 0.8 - lift;
    const xm = lerp(x0, x1, 0.5), ym = lerp(y0, y1, 0.5);
    g.fillStyle = `rgba(${k < 0.3 ? SX_FAT.hot : SX_FAT.ember},${a})`; fatLine(x0, y0, xm, ym);
    g.fillStyle = `rgba(${k < 0.5 ? SX_FAT.ember : SX_FAT.deep},${a * 0.8})`; fatLine(xm, ym, x1, y1);
  }
  addLight(m.x, m.y, 70, SX_FAT.ember, 0.8 * a);
}
fatalityRegister('saxe', {
  name: "Grinder's Mercy",
  col: '255,160,70',
  get tag() { try { return P && P.sxAxe ? 'sx_fatal_a' : 'sx_fatal'; } catch (e) { return 'sx_fatal'; } },
  tags: ['sx_release', 'sx_heavy', 'riposte'],
  dur: 1700,
  start(F) {
    F.sx = { g: P.sxG || 0, axe: !!P.sxAxe, lock: !!P.sxLock, rel: !!P.sxRel };
    // every blow lands where the head is (hip height, ~34 px out), not at the middle of a tall foe
    const hb = F.tc().hb, hy = clamp((P.y - 15 - hb.y0) / Math.max(1, hb.y1 - hb.y0), 0.15, 0.85);
    for (const s of F.steps) if (s.hit !== undefined) { s.hy = hy; s.x = 34; }
  },
  tick(F, dt) {
    const s = F.sx; if (s) { P.sxG = s.g; P.sxLock = s.lock; P.sxAxe = s.axe; P.sxVentDue = false; P.sxRel = false; P.sxIdleT = 0; }
    // the grind (660 .. 1150): sparks pouring off the head, the chain's scream, the frame shaking with it
    if (F.t >= 660 && F.t < 1150) {
      const h = sxfHead(F);
      F.sxS = (F.sxS || 0) - dt * 1000;
      if (F.sxS <= 0) {
        F.sxS = 30;
        for (let i = 0; i < 4; i++) fatSpark(h.x, h.y + rand(-3, 3), -F.face0 * rand(30, 170), -rand(30, 170), i ? SX_FAT.ember : SX_FAT.hot, rand(0.18, 0.4), 420);
        if (Math.random() < 0.5) fatSpark(h.x, h.y, F.face0 * rand(10, 60), rand(20, 80), SX_FAT.ember, 0.25, 300);
      }
      F.sxN = (F.sxN || 0) - dt * 1000;
      if (F.sxN <= 0) { F.sxN = 80; noise(0.07, 650 + rand(-80, 80), 2, 0.06, 'bandpass'); if (Math.random() < 0.6) tone(62 + rand(0, 10), 0.08, 0.035, 'sawtooth', 0.9); }
      shake = Math.max(shake, 1.6);
      addLight(h.x, h.y, 30, SX_FAT.ember, 0.45 + 0.2 * Math.random());
    }
  },
  end(F) { const s = F.sx; if (s) { P.sxG = s.g; P.sxLock = s.lock; P.sxAxe = s.axe; P.sxVentDue = false; P.sxRel = false; P.sxIdleT = 0; } },
  steps: [
    { at: 0, move: { gap: 12, dur: 120 } },
    { at: 110, sfx: () => { tone(110, 0.3, 0.06, 'sawtooth', 1.8); noise(0.2, 400, 1, 0.04, 'bandpass', 2); } },   // the phial lit
    { at: 240, fx: 'sparkBurst', o: { anchor: 'player', dx: 4, dy: -14, n: 5, spd: 60, dir: -90, arc: 80 } },
    // THE STAB
    { at: 280, sfx: () => sfx.heavySwing() },
    { at: 285, hit: 0.8, stop: 0.07, shake: 5, flash: 0.18, kick: 1.6, zoom: 0.4 },
    { at: 285, fx: 'sparkBurst', o: { anchor: sxfHead, n: 14, spd: 200, dir: 180, arc: 70 } },
    { at: 285, fx: 'impactFlash', o: { anchor: sxfHead, r: 20, dur: 120 } },
    // the unfold inside: unlatch, swing, slide, LOCK (each a clank and a jolt)
    { at: 420, sfx: () => { tone(240, 0.08, 0.06, 'square', 0.8); noise(0.06, 1400, 2, 0.05, 'bandpass'); }, shake: 2 },
    { at: 480, sfx: () => { tone(190, 0.08, 0.06, 'square', 0.8); noise(0.06, 1200, 2, 0.05, 'bandpass'); }, shake: 2 },
    { at: 480, fx: sxfSeams, o: { life: 1500 } },
    { at: 540, sfx: () => { noise(0.1, 900, 2, 0.06, 'bandpass', 0.6); }, shake: 2 },
    { at: 600, sfx: () => { tone(150, 0.14, 0.1, 'square', 0.5); noise(0.12, 500, 1.5, 0.1, 'bandpass'); tone(55, 0.5, 0.08, 'sawtooth', 1.4); }, shake: 5, stop: 0.05, flash: 0.12, kick: 1 },
    { at: 600, fx: 'impactFlash', o: { anchor: sxfHead, r: 24, dur: 140 } },
    { at: 600, fx: 'sparkBurst', o: { anchor: sxfHead, n: 12, spd: 170 } },
    // the grind (the sparks / noise / jitter are in tick): two bites
    { at: 760, hit: 0.6, stop: 0.03, shake: 4, flash: 0.06, kick: 0.8, zoom: 0.25 },
    { at: 960, hit: 0.6, stop: 0.03, shake: 4, flash: 0.06, kick: 0.8, zoom: 0.25 },
    { at: 1060, fx: 'emberBurst', o: { anchor: sxfHead, n: 8, w: 10, rise: 50 } },
    // PHIAL BURST
    { at: 1150, hit: 3.0, slow: 0.45, stop: 0.15, shake: 12, flash: 0.55, boom: true, name: true, kick: 2.8 },
    { at: 1150, fx: sxfBlast, o: { life: 620 } },
    { at: 1150, fx: 'impactFlash', o: { anchor: sxfHead, r: 46, dur: 180 } },
    { at: 1150, fx: 'shockwave', o: { anchor: 'ground', r1: 92, sq: 0.22, rings: 2, gap: 80, dur: 440 } },
    { at: 1150, fx: 'sparkBurst', o: { anchor: sxfHead, n: 30, spd: 260 } },
    { at: 1160, fx: 'emberBurst', o: { anchor: sxfHead, n: 22, w: 30, h: 16, rise: 90, col: '255,170,80' } },
    { at: 1160, call: F => { const h = sxfHead(F); for (let i = 0; i < 12; i++) particles.push({ x: h.x + rand(-8, 8), y: h.y + rand(-8, 6), vx: rand(-20, 20), vy: -rand(15, 45), life: rand(0.7, 1.3), kind: 'dust' }); } },
    { at: 1150, sfx: () => { noise(0.5, 300, 0.7, 0.3, 'lowpass', 0.5); noise(0.3, 1800, 1, 0.12, 'bandpass', 0.4); } },
    { at: 1200, move: { gap: 22, dur: 160 } },   // thrown back a step by the blast
    // folding back (sword) / onto the shoulder (axe)
    { at: 1320, sfx: F => { if (!F.sx.axe) { tone(200, 0.1, 0.05, 'square', 1.3); noise(0.06, 1300, 2, 0.04, 'bandpass'); } } },
    { at: 1450, sfx: F => { if (!F.sx.axe) { tone(300, 0.12, 0.06, 'square', 0.7); } else noise(0.12, 700, 2, 0.03, 'bandpass'); } },
    { at: 1310, call: F => { const h = sxfHead(F); for (let i = 0; i < 6; i++) particles.push({ x: h.x + rand(-4, 4), y: h.y + rand(-4, 4), vx: rand(-10, 10), vy: -rand(20, 45), life: rand(0.5, 0.9), kind: 'dust' }); } },
  ],
  // the phial burning under the hand while it's drawn back
  draw(F, t) {
    if (t >= 110 && t <= 300) { const x = P.x + F.face0 * 1, y = P.y - 14, k = clamp((t - 110) / 150, 0, 1); addLight(x, y, 18 + 10 * k, SX_FAT.ember, 0.35 + 0.3 * k); }
    if (t >= 600 && t < 1150 && typeof mvStar === 'function') {   // the head biting: a hot star flickering where the chain chews
      const h = sxfHead(F), r = 2 + Math.round(3 * Math.abs(Math.sin(t * 0.05)));
      mvStar(Math.round(h.x), Math.round(h.y), r, SX_FAT.hot, 0.85);
      g.fillStyle = `rgba(${SX_FAT.ember},0.5)`; fatEllipse(h.x, h.y, 4 + (Math.floor(t / 40) % 2), 3);
    }
  },
});

// ================================================================== SCYTHE "Last Harvest"
// A spectral reaper's blade grows out of the real one, hooks behind the foe's neck (the hook bites), hauls, then is pulled
// through the foe in one full circle round the body -- leaving a pale crescent moon that lingers and shatters -- and the
// foe's souls rise out of it and stream into the upright blade. The scythe's own souls are full (3) afterwards.
// scy_fatal: 0 raise | 240 HOOK | 300 set | 420 haul | 560 the circle .. | 760 low finish | 960 rise | 1110 harvest | 1420 rest | 1600
const SCY_FAT = { pale: '232,224,255', soul: '186,150,255' };
function scyfState(e, F, t) {   // the ghost scythe's pose at fx-time t: snath angle a (facing deg), alpha al, length L
  if (!e.m) {
    const sh = F.shoulder(), hb = F.tc().hb, far = F.face0 > 0 ? hb.x1 : hb.x0;
    const L = clamp(Math.hypot(far - F.face0 * 2 - sh.x, hb.y0 + 6 - sh.y), 52, 90);
    e.m = { L, bl: clamp(L * 0.55, 28, 44), hist: [] };
    e.keys = [[0, -100, 0], [120, -62, 0.7], [190, -18, 1, 'snap'], [320, -14, 1], [460, -10, 1], [660, 350, 1, 'inout'], [800, 354, 0]];
  }
  const m = e.m, K = e.keys;
  let a = K[0][1], al = 0;
  if (t >= K[K.length - 1][0]) { a = K[K.length - 1][1]; al = 0; }
  else for (let i = 1; i < K.length; i++) if (t <= K[i][0]) { const k = fatEase(K[i][3] || 'inout', (t - K[i - 1][0]) / (K[i][0] - K[i - 1][0])); a = lerp(K[i - 1][1], K[i][1], k); al = lerp(K[i - 1][2], K[i][2], k); break; }
  // the haul: the snath drawn in a few px while the hook is set
  const L = m.L - (t > 190 && t < 460 ? 5 * fatEase('inout', (t - 190) / 270) : t >= 460 && t < 520 ? 5 * (1 - (t - 460) / 60) : 0);
  return { m, a, al, L, sh: F.shoulder(), clipY: Math.round(F.y0) };
}
function scyfShape(m, sh, deg, L, f) {   // the snath's end and the blade: spine points sp, edge points ed
  const r = fatAng(deg, f), ex = sh.x + Math.cos(r) * L, ey = sh.y + Math.sin(r) * L;
  const n = 10, st = m.bl / n, sp = [[ex, ey]], ed = [[ex, ey]];
  let px = ex, py = ey;
  for (let i = 1; i <= n; i++) {   // heading down off the snath (deg + 100), curling back toward the pivot (+70)
    const s = i / n, dr = fatAng(deg + 100 + 70 * s * s, f);
    px += Math.cos(dr) * st; py += Math.sin(dr) * st;
    const nr = fatAng(deg + 100 + 70 * s * s + 90, f), w = m.bl * 0.24 * Math.pow(1 - s, 0.75);
    sp.push([px, py]); ed.push([px + Math.cos(nr) * w, py + Math.sin(nr) * w]);
  }
  return { ex, ey, sp, ed, n };
}
// the ghost scythe: a snath of length L round the shoulder at facing-angle a, the blade hanging off its end and curling back
function scyfGhost(c, t, F, e) {
  const S = scyfState(e, F, t); if (!S) return;
  const { m, a, al, L, sh, clipY } = S;
  m.hist.unshift(a); if (m.hist.length > 6) m.hist.pop();
  if (al <= 0.01) return;
  const f = F.face0;
  const one = (deg, A, fill) => {
    const { ex, ey, sp, ed, n } = scyfShape(m, sh, deg, L, f);
    const r = fatAng(deg, f);
    g.fillStyle = `rgba(${fatLite(F.col)},${0.6 * A})`; fatLine(sh.x + Math.cos(r) * 8, sh.y + Math.sin(r) * 8, ex, ey, clipY);
    if (fill) { g.fillStyle = `rgba(${F.col},${0.34 * A})`; for (let i = 0; i < n; i++) fatPoly([sp[i], sp[i + 1], ed[i + 1], ed[i]], clipY); }
    g.fillStyle = `rgba(${fatLite(F.col)},${0.85 * A})`; for (let i = 0; i < n; i++) fatLine(sp[i][0], sp[i][1], sp[i + 1][0], sp[i + 1][1], clipY);
    g.fillStyle = `rgba(${fatHot(F.col)},${A})`; for (let i = 0; i < n; i++) fatLine(ed[i][0], ed[i][1], ed[i + 1][0], ed[i + 1][1], clipY);
    return sp[n];
  };
  for (let i = m.hist.length - 1; i >= 1; i--) if (Math.abs(m.hist[i] - a) > 5) one(m.hist[i], al * 0.35 * (1 - i / m.hist.length), false);
  const tip = one(a, al, true);
  if (tip[1] <= clipY && typeof mvStar === 'function') mvStar(Math.round(tip[0]), Math.round(tip[1]), 2, fatHot(F.col), al);
  addLight(sh.x + Math.cos(fatAng(a, f)) * L * 0.8, sh.y + Math.sin(fatAng(a, f)) * L * 0.8, 50, F.col, 0.4 * al);
}
fatalityRegister('scythe', {
  name: 'Last Harvest',
  col: '205,185,255',
  tag: 'scy_fatal', tags: ['scy_reap', 'scy_hook', 'riposte'],
  dur: 1600,
  steps: [
    { at: 0, move: { gap: 6, dur: 120 } },
    { at: 100, fx: scyfGhost, o: { life: 820 } },
    { at: 100, sfx: () => { tone(196, 0.6, 0.05, 'sine', 0.7); noise(0.35, 2400, 0.8, 0.04, 'bandpass', 0.6); } },
    // THE HOOK bites behind the neck: a jolt toward you
    { at: 290, hit: 0.7, stop: 0.08, shake: 4, flash: 0.14, kick: -1.4, zoom: 0.35, hy: 0.12 },
    { at: 290, fx: 'sparkBurst', o: { anchor: 'top', dy: 4, n: 10, spd: 130, dir: 180, arc: 80 } },
    { at: 290, fx: 'impactFlash', o: { anchor: 'top', dy: 4, r: 16, dur: 120 } },
    { at: 290, sfx: () => { tone(1319, 0.2, 0.05, 'triangle', 0.7); noise(0.1, 1600, 2, 0.08, 'bandpass'); } },
    { at: 300, target: { knock: -5, dur: 240, ease: 'inout' } },   // a small foe is hauled a step in
    { at: 430, sfx: () => noise(0.25, 300, 1, 0.06, 'bandpass', 1.6), shake: 2 },
    // the full circle
    { at: 560, sfx: () => { sfx.heavySwing(); tone(392, 0.5, 0.05, 'sine', 0.5); } },
    { at: 560, fx: 'speedLines', o: { n: 8, dur: 160, band: [-50, -4] } },
    { at: 600, hit: 4.3, slow: 0.45, stop: 0.14, shake: 10, flash: 0.5, boom: true, name: true, kick: 2.4, hy: 0.3 },
    { at: 600, fx: 'impactFlash', o: { r: 36, dur: 170 } },
    { at: 600, fx: 'sparkBurst', o: { n: 22, spd: 230 } },
    { at: 610, target: { knock: 4, dur: 180 } },
    // the pale crescent moon the circle leaves (its upper half: behind, over, in front)
    { at: 655, fx: 'crescent', o: { anchor: 'player', dy: -19, r: 52, thick: 18, a0: 190, a1: 352, sq: 0.92, grow: 100, linger: 620, shatter: 420, shards: 30, floor: true, col: SCY_FAT.pale } },
    { at: 660, call: F => { const e = FAT.fx.find(q => q.k === 'crescent' && q.F === F); const g0 = FAT.fx.find(q => q.k === 'custom' && q.F === F && q.fn === scyfGhost); if (e && g0 && g0.m) e.r = Math.round(g0.m.L * 0.92); } },
    // the souls rise out of the foe and stream into the blade
    { at: 760, fx: 'soulWisps', o: { from: 'target', n: 14, rise: 300, dur: 1100, stagger: 45, to: 'tip' } },
    { at: 940, fx: 'soulWisps', o: { from: 'target', n: 8, rise: 260, dur: 900, stagger: 50, to: 'tip', col: SCY_FAT.pale } },
    { at: 780, fx: 'emberBurst', o: { anchor: 'ground', n: 10, w: 30, rise: 40, col: SCY_FAT.soul } },
    { at: 1150, sfx: () => { tone(587, 0.3, 0.04, 'sine', 1.5); } },
    { at: 1280, sfx: () => { tone(784, 0.3, 0.04, 'sine', 1.5); } },
    { at: 1410, sfx: () => { tone(988, 0.4, 0.045, 'sine', 1.5); tone(1976, 0.3, 0.02, 'triangle', 1.2, 0.04); } },
  ],
  drawLit(F) {   // a dusk-violet shade under the ghost blade so it still reads against a pale sky
    const e = FAT.fx.find(q => q.fn === scyfGhost && q.F === F); if (!e || !e.m) return;
    const S = scyfState(e, F, e.t); if (!S || S.al <= 0.05) return;
    const { ex, ey, sp, ed, n } = scyfShape(S.m, S.sh, S.a, S.L, F.face0), r = fatAng(S.a, F.face0);
    g.fillStyle = `rgba(28,16,52,${0.4 * S.al})`;
    for (let i = 0; i < n; i++) fatPoly([sp[i], sp[i + 1], ed[i + 1], ed[i]], S.clipY);
    fatLine(S.sh.x + Math.cos(r) * 8, S.sh.y + Math.sin(r) * 8 + 1, ex, ey + 1, S.clipY);
  },
  draw(F, t) {   // the upright blade fills with soul-light while they flow in
    if (t < 960 || t > 1500) return;
    const tp = F.tip(), k = clamp((t - 960) / 400, 0, 1), fade = t > 1420 ? (1500 - t) / 80 : 1;
    addLight(tp.x, tp.y, 18 + 16 * k, SCY_FAT.soul, (0.3 + 0.4 * k) * fade);
    if (typeof mvStar === 'function' && k > 0.3) mvStar(Math.round(tp.x), Math.round(tp.y), 2 + Math.round(2 * Math.abs(Math.sin(t * 0.025))), SCY_FAT.pale, 0.9 * fade);
  },
  end(F, aborted) {   // the harvest fills the scythe: all three souls orbit the blade
    if (aborted) return;
    try { if (typeof SCY_MAX !== 'undefined') { P.scySouls = SCY_MAX; P.scyFade = 0; if (typeof SCY !== 'undefined') SCY.ready = true; } } catch (e) {}
  },
});
// the Switch Axe's own per-frame upkeep (gauge drain / bleed / vent, 78_mech_saxe.js tickAll) pauses while its fatality
// plays: the form, the gauge and the lock come out exactly as they went in
if (MV.types.saxe && MV.types.saxe.tickAll && !MV.types.saxe._fbWrap) {
  const T = MV.types.saxe, own = T.tickAll; T._fbWrap = true;
  T.tickAll = function (dt, cur) { if (cur && FAT.on && FAT.on.type === 'saxe') return; return own.apply(this, arguments); };
}
