// ------------------------------------------------------------------ v16 FATALITIES: the heavy group (agent `fheavy`, docs/v16/fheavy.md)
// GREATSWORD "Grave Sunder", MAUL "Death Knell", WARBELL "Grand Requiem". The weightiest three: long anticipation, huge
// hitstop, ground cracks, shockwaves, stone and dust thrown up. Choreography on the fatality clock, in step with
// art/player_v16_fatal_heavy.py (frame starts):
//   gs_fatal  0 haul | 100 coil | 260 SPRING | 350 apex (point-down) | 510 dive | 620 IMPALE | 690 molten kneel x3
//             1020 wrench | 1090 SUNDER (rising cleave) | 1135 overhead | 1210 hold high | 1400 shoulder | 1550 recover | 1700
//   ml_fatal  0 step | 90 spin x4 | 370 wheel up | 500 hang | 610 down | 650 CRASH | 720 hold | 840 rebound | 910 hang
//             1080 down | 1120 POUND | 1200 kneel | 1460 rise | 1550 recover | 1650
//   wb_fatal  0 step | 80 lift | 190 high | 350 drop | 400 TOLL I | 600 heave | 690 over the back | 770 down | 810 TOLL II
//             1020 wind | 1130 over the top | 1240 down | 1270 TOLL III | 1350 kneel | 1650 rise | 1800
// Shared here: FH (lit-layer stone chunks + dust clouds), fhBell (a struck bell: inharmonic partials), fhRumble.

const FH = { parts: [] };
const FH_STONE = '58,50,48', FH_DUST = '138,126,112';

// ================================================================== lit debris: stone chunks and dust clouds
// stone chunks thrown out of an impact (drawn on the lit layer, so the lights shade them); `hot` gives them a glowing face
function fhRocks(x, y, n, o = {}) {
  const floor = o.floor ?? y, face = o.face || 1;
  for (let i = 0; i < n; i++) {
    const a = (o.dir !== undefined ? o.dir : -90) + (Math.random() - 0.5) * (o.arc ?? 120), r = a * Math.PI / 180, v = (o.spd ?? 160) * (0.45 + Math.random() * 0.55);
    FH.parts.push({ k: 'rock', x: x + (Math.random() - 0.5) * (o.w ?? 10), y: y - Math.random() * 3, vx: Math.cos(r) * v * face, vy: Math.sin(r) * v,
      w: 1 + Math.floor(Math.random() * (o.size ?? 3)), h: 1 + Math.floor(Math.random() * 2), floor, life: 0.7 + Math.random() * 0.6, max: 1.3,
      hot: o.hot ? fatRGB(o.hot) : null, bounce: 0 });
  }
  if (FH.parts.length > 220) FH.parts.splice(0, FH.parts.length - 220);
}
// dust clouds rolling out along the floor and up (dithered discs that swell and thin out)
function fhDust(x, y, n, o = {}) {
  for (let i = 0; i < n; i++) {
    const side = i % 2 ? 1 : -1, v = (o.spd ?? 70) * (0.3 + Math.random() * 0.7);
    FH.parts.push({ k: 'dust', x: x + (Math.random() - 0.5) * (o.w ?? 12), y: y - Math.random() * 4, vx: side * v, vy: -(o.rise ?? 18) * Math.random() - 4,
      r: (o.r ?? 3) + Math.random() * 2, grow: (o.grow ?? 14) * (0.6 + Math.random() * 0.6), life: (o.life ?? 0.9) * (0.7 + Math.random() * 0.5), max: o.life ?? 0.9,
      col: o.col || FH_DUST, seed: Math.floor(Math.random() * 1000) });
  }
  if (FH.parts.length > 220) FH.parts.splice(0, FH.parts.length - 220);
}
HOOKS.update.push(dt => {
  if (!FH.parts.length) return;
  for (const p of FH.parts) {
    p.life -= dt;
    if (p.k === 'rock') {
      p.vy += 520 * dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.y > p.floor && p.vy > 0) { if (p.bounce++ < 1) { p.y = p.floor; p.vy *= -0.32; p.vx *= 0.5; } else { p.y = p.floor; p.vy = 0; p.vx *= 0.6; } }
    } else { p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= Math.pow(0.12, dt); p.vy *= Math.pow(0.3, dt); p.r += p.grow * dt; }
  }
  FH.parts = FH.parts.filter(p => p.life > 0);
});
HOOKS.render.push(() => {   // world space, lit layer (after the bodies)
  if (!FH.parts.length) return;
  for (const p of FH.parts) {
    const a = clamp(p.life / (p.max * 0.45), 0, 1);
    if (p.k === 'rock') {
      const x = Math.round(p.x), y = Math.round(p.y) - p.h;
      g.fillStyle = `rgba(${FH_STONE},${a})`; g.fillRect(x, y, p.w, p.h);
      g.fillStyle = `rgba(96,84,78,${a})`; g.fillRect(x, y, p.w, 1);
      if (p.hot) { const hk = clamp((p.life - 0.3) / 0.6, 0, 1); if (hk > 0) { g.fillStyle = `rgba(${p.hot},${hk})`; g.fillRect(x, y, 1, 1); } }
    } else {
      const k = 1 - p.life / p.max, al = 0.55 * a * (1 - k * 0.4), R = p.r, cx = p.x, cy = p.y;
      fatRaster(cx - R, cy - R, cx + R, cy + R * 0.7, (x, y) => {
        const d = Math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.25) / R; if (d > 1) return 0;
        const c = (1 - d) * (1.1 - k); if (!fatDith(x + p.seed, y, c * 1.4)) return 0;
        return d < 0.45 ? 1 : 2;
      }, [null, `rgba(${p.col},${al})`, `rgba(${fatDeep(p.col)},${al * 0.8})`]);
    }
  }
});
HOOKS.enter.push(() => { FH.parts = []; });

// ================================================================== sound
// a struck bell: hum (f/2), prime, minor-third tierce, quint, nominal, the strike's metallic partial, a burst of noise
function fhBell(f, v = 1, dur = 2, delay = 0) {
  try {
    const T = (fr, d, a, ty = 'sine') => tone(fr, d, a * v, ty, 0.998, delay);
    T(f * 0.5, dur * 1.3, 0.1); T(f, dur, 0.12); T(f * 1.2, dur * 0.7, 0.05); T(f * 1.5, dur * 0.5, 0.035); T(f * 2.0, dur * 0.65, 0.055);
    T(f * 2.74, dur * 0.28, 0.03); T(f * 4.1, 0.14, 0.05, 'triangle');
    noise(0.14, Math.min(6000, f * 9), 1.4, 0.14 * v, 'bandpass', 0.6);
  } catch (e) {}
}
const fhRumble = (v = 1, d = 0.5) => { try { noise(d, 90, 0.7, 0.32 * v, 'lowpass', 0.6); tone(46, d, 0.12 * v, 'sine', 0.8); } catch (e) {} };
const fhThud = (v = 1) => { try { noise(0.18, 260, 0.9, 0.5 * v, 'lowpass', 0.4); tone(72, 0.22, 0.25 * v, 'square', 0.5); } catch (e) {} };

// where the weapon meets the floor in front (frame x 42 = 14 px ahead of the feet, as the art)
const fhFront = (dx = 14) => F => ({ x: P.x + F.face * dx, y: F.y0 });

// ================================================================== custom glow fx (fn(ctx, t, F, e), e.x / e.y = the anchor)
// a ring of sound / force: wobbling 1-px circles that open out, dotted as they thin (o: r1, n, gap, dur, wob, sq, floor)
function fhRipple(ctx, t, F, e) {
  const o = e.o, n = o.n ?? 3, gap = o.gap ?? 110, d = o.dur ?? 640, sq = o.sq ?? 1, clip = o.floor ? F.y0 : undefined;
  for (let i = 0; i < n; i++) {
    const tt = t - i * gap; if (tt < 0 || tt > d) continue;
    const k = tt / d, r = lerp(o.r0 ?? 8, (o.r1 ?? 200) * (1 - i * 0.1), fatEase('out', k)), a = (1 - k) * (i ? 0.75 : 1);
    const m = Math.max(16, Math.ceil(r * 3.4)), wob = (o.wob ?? 1.6) * (1 - k);
    let px = null, py = null;
    for (let j = 0; j < m; j++) {
      const th = j / m * 6.2832, rr = r + Math.sin(th * 5 + tt * 0.02 + i) * wob, x = Math.round(e.x + Math.cos(th) * rr), y = Math.round(e.y + Math.sin(th) * rr * sq);
      if (x === px && y === py) continue; px = x; py = y;
      if (clip !== undefined && y > clip) continue;
      if (!fatDith(x, y, a * 1.25)) continue;
      g.fillStyle = `rgba(${k < 0.3 ? fatHot(e.col) : fatLite(e.col)},${a})`; g.fillRect(x, y, 1, 1);
    }
  }
  if (t < 200) addLight(e.x, e.y, 70, e.col, 0.4 * (1 - t / 200));
}
// vertical dive streaks rushing up past the falling knight
function fhDive(ctx, t, F, e) {
  const k = t / e.life, R = fatRng(F.n * 5 + 1);
  for (let i = 0; i < 7; i++) {
    const x = Math.round(P.x + (R() - 0.5) * 26), y0 = Math.round(P.y - 30 - R() * 30 + t * (0.4 + R() * 0.3)), L = 10 + R() * 22;
    g.fillStyle = `rgba(${fatLite(e.col)},${0.55 * (1 - k)})`; g.fillRect(x, y0 - Math.round(L), 1, Math.round(L));
  }
}

// ================================================================== GREATSWORD "Grave Sunder"
// Leap, drive the greatsword point-first down through the foe into the floor -- the ground cracks open in molten lines
// and the buried steel runs red-hot from the floor up -- then rip it free in one rising cleave that throws stone and
// embers and leaves a pillar of light burning where it came out.
fatalityRegister('greatsword', {
  name: 'Grave Sunder',
  col: '255,168,92',
  tag: 'gs_fatal', tags: ['gs_true2', 'gs_heavy', 'riposte'],
  dur: 1700,
  cine: { dark: 0.55 },
  steps: [
    { at: 0, move: { gap: 12, dur: 100 }, sfx: () => tone(70, 0.4, 0.08, 'sine', 0.8) },
    // the coil: dust stirs, the steel catches the light
    { at: 110, sfx: () => sfx.heavySwing() },
    { at: 150, fx: 'emberBurst', o: { anchor: 'player', n: 6, w: 20, rise: 30, spd: 30, col: '200,180,160' } },
    { at: 230, sfx: () => sfx.glint() },
    // SPRING: up ~30 px and a step closer, the floor kicked away
    { at: 260, move: { gap: 5, dy: -30, dur: 220, ease: 'out' }, shake: 3, sfx: () => { sfx.jump(); fhThud(0.6); } },
    { at: 260, call: F => fhDust(P.x, F.y0, 8, { spd: 60, r: 2, grow: 10, life: 0.6 }) },
    { at: 260, fx: 'shockwave', o: { anchor: 'start', r1: 34, sq: 0.22, rings: 1, dur: 300, col: '230,210,190' } },
    // the apex hang: point-down, a glint at the hilt; the light gathers
    { at: 380, fx: 'soulWisps', o: { anchor: 'player', dy: -34, from: 'ring', r: 40, n: 8, rise: 80, dur: 260, stagger: 14, to: 'tip' } },
    { at: 420, sfx: () => { tone(160, 0.35, 0.07, 'sawtooth', 2.2); noise(0.3, 1200, 0.8, 0.08, 'bandpass', 2.5); } },
    // the dive: ghosts and streaks
    { at: 500, move: { dy: 0, dur: 115, ease: 'in' }, ghosts: { dur: 100, every: 50, alpha: 0.18, life: 0.12 } },
    { at: 505, fx: fhDive, o: { life: 120 } },
    { at: 540, sfx: () => noise(0.12, 1800, 0.8, 0.22, 'bandpass', 0.3) },
    // IMPALE (beat 1): through the foe into the stone -- the floor splits in molten lines both ways
    { at: 620, hit: 1.5, stop: 0.13, shake: 10, flash: 0.3, kick: 1.2, kickY: 3, zoom: 0.7, x: 14, hy: 0.6,
      sfx: () => { fhThud(1.2); fhRumble(1, 0.8); tone(110, 0.3, 0.12, 'square', 0.4); } },
    { at: 620, target: { pin: true } },
    { at: 620, fx: 'impactFlash', o: { anchor: fhFront(), dy: -3, r: 30, dur: 160 } },
    { at: 620, fx: 'groundCrack', o: { anchor: fhFront(), len: 84, branches: 7, dur: 1700, col: '255,140,60' } },
    { at: 620, fx: 'shockwave', o: { anchor: fhFront(), r1: 96, sq: 0.2, rings: 2, gap: 70, dur: 420 } },
    { at: 620, fx: 'sparkBurst', o: { anchor: fhFront(), dy: -2, n: 22, spd: 220, dir: -90, arc: 150 } },
    { at: 620, call: F => { const p = fhFront()(F); fhRocks(p.x, p.y, 12, { spd: 170, arc: 140, floor: F.y0, hot: '255,150,70', face: F.face }); fhDust(p.x, p.y, 12, { spd: 90, r: 3, grow: 16, life: 1.0 }); } },
    // the molten kneel: the cracks breathe, the ground trembles, embers lift off the seams
    { at: 760, shake: 3, sfx: () => fhRumble(0.6, 0.5) },
    { at: 760, fx: 'emberBurst', o: { anchor: fhFront(), n: 10, w: 60, rise: 50, col: '255,150,70' } },
    { at: 900, shake: 4, sfx: () => { fhRumble(0.8, 0.5); noise(0.4, 600, 0.6, 0.08, 'bandpass', 1.6); } },
    { at: 900, fx: 'groundCrack', o: { anchor: fhFront(), len: 120, branches: 9, dur: 1400, col: '255,120,50' } },
    { at: 900, fx: 'emberBurst', o: { anchor: fhFront(), n: 12, w: 90, rise: 60, col: '255,170,90' } },
    { at: 990, sfx: () => tone(180, 0.18, 0.08, 'sawtooth', 3) },
    // THE SUNDER (beat 2): ripped free in one rising cleave -- stone, embers, a pillar of light
    { at: 1090, hit: 3.5, slow: 0.45, stop: 0.16, shake: 13, flash: 0.5, boom: true, name: true, kick: 2.6, kickY: -2, zoom: 1, x: 14, hy: 0.4,
      sfx: () => { sfx.heavySwing(); noise(0.5, 300, 0.8, 0.5, 'lowpass', 0.3); } },
    { at: 1090, target: { lift: 22, knock: 12, dur: 240, ease: 'out' } },
    { at: 1090, fx: 'crescent', o: { anchor: 'player', dy: -18, r: 44, thick: 13, a0: 105, a1: -102, grow: 45, linger: 320, shatter: 340, shards: 22, sq: 1 } },
    { at: 1090, fx: 'pillar', o: { anchor: fhFront(), w: 18, grow: 60, dur: 950 } },
    { at: 1090, fx: 'impactFlash', o: { anchor: fhFront(), dy: -12, r: 44, dur: 200 } },
    { at: 1090, fx: 'shockwave', o: { anchor: fhFront(), r1: 130, sq: 0.2, rings: 3, gap: 80, dur: 520 } },
    { at: 1090, fx: 'sparkBurst', o: { anchor: fhFront(), dy: -4, n: 30, spd: 260, dir: -80, arc: 70 } },
    { at: 1090, fx: 'emberBurst', o: { anchor: fhFront(), n: 26, w: 30, h: 20, rise: 150, spd: 90, col: '255,160,70' } },
    { at: 1090, call: F => { const p = fhFront()(F); fhRocks(p.x, p.y, 18, { spd: 260, dir: -82, arc: 70, floor: F.y0, size: 3, hot: '255,170,90', face: F.face }); fhDust(p.x, p.y, 16, { spd: 110, r: 4, grow: 20, life: 1.2, rise: 30 }); } },
    { at: 1180, fx: 'emberBurst', o: { anchor: fhFront(), dy: -40, n: 14, w: 16, h: 50, rise: 90, col: '255,190,120' } },
    { at: 1400, target: { drop: true } },
    { at: 1450, sfx: () => { noise(0.4, 3000, 1.2, 0.08, 'highpass'); tone(1400, 0.3, 0.03, 'triangle', 0.7); } },
  ],
  // the buried steel: a molten seam climbing the blade from the floor, a pool of light round where it went in
  draw(F, t) {
    if (t < 620 || t > 1100) return;
    const x = Math.round(P.x + F.face * 14), y0 = Math.round(F.y0) - 1, k = clamp((t - 640) / 360, 0, 1), top = Math.round(y0 - 2 - 17 * k);
    const pulse = 0.75 + 0.25 * Math.sin(t * 0.03);
    g.fillStyle = `rgba(${fatHot(F.col)},${0.7 * pulse})`; g.fillRect(x, top, 1, y0 - top + 1);
    const w = Math.round(3 + 9 * k);
    for (let i = -w; i <= w; i++) if (fatDith(x + i, y0, (1 - Math.abs(i) / (w + 1)) * pulse)) { g.fillStyle = `rgba(${Math.abs(i) < 3 ? fatHot(F.col) : F.col},${0.8 * pulse})`; g.fillRect(x + i, y0 + 1, 1, 1); }
    addLight(x, y0 - 6, 34 + 26 * k, F.col, (0.35 + 0.3 * k) * pulse);
  },
});

// ================================================================== MAUL "Death Knell"
// A full wind-up spin, the hammer wheeled over the top and hung there; it CRASHES down on the foe (concentric rings of
// force, dust and stone, the screen jolts); the rebound carries it straight back overhead, and the second pound drives it
// into the floor -- a bell-bright flash, a ring of light that opens across the room, the floor broken both ways.
fatalityRegister('maul', {
  name: 'Death Knell',
  col: '255,200,128',
  tag: 'ml_fatal', tags: ['ml_bb4', 'ml_bigsmash', 'riposte'],
  dur: 1650,
  steps: [
    { at: 0, move: { gap: 14, dur: 90 }, sfx: () => tone(66, 0.4, 0.08, 'sine', 0.8) },
    // the wind-up spin: one full turn, ghosts and dust whirled off the floor
    { at: 90, ghosts: { dur: 260, every: 70, alpha: 0.14, life: 0.12 } },
    { at: 100, sfx: () => sfx.bossSwing() },
    { at: 120, call: F => fhDust(P.x, F.y0, 6, { spd: 80, r: 2, grow: 10, life: 0.6, rise: 6 }) },
    { at: 240, sfx: () => sfx.bossSwing() },
    { at: 250, call: F => fhDust(P.x, F.y0, 6, { spd: 90, r: 2, grow: 10, life: 0.6, rise: 6 }) },
    { at: 380, sfx: () => sfx.heavySwing() },
    // the hang over the helm: the head drinks in the light
    { at: 500, sfx: () => { sfx.glint(); tone(130, 0.3, 0.06, 'sawtooth', 2); } },
    { at: 505, fx: 'soulWisps', o: { anchor: 'player', dy: -36, from: 'ring', r: 36, n: 8, rise: 70, dur: 220, stagger: 12, to: 'tip' } },
    { at: 615, sfx: () => noise(0.14, 900, 0.7, 0.3, 'bandpass', 0.3) },
    // CRASH (beat 1): rings of force round the foe, dust and stone, the screen jolts
    { at: 650, hit: 1.5, stop: 0.12, shake: 11, flash: 0.25, kick: 1.6, kickY: 4, zoom: 0.7, hy: 0.45,
      sfx: () => { fhThud(1.3); fhRumble(0.9, 0.6); try { tone(196, 0.5, 0.05, 'sine', 0.99); } catch (e) {} } },
    { at: 650, target: { pin: true } },
    { at: 650, fx: 'shockwave', o: { r0: 6, r1: 56, sq: 1, rings: 2, gap: 70, dur: 340, thick: 2 } },
    { at: 650, fx: 'shockwave', o: { anchor: fhFront(13), r1: 110, sq: 0.2, rings: 2, gap: 80, dur: 440 } },
    { at: 650, fx: 'impactFlash', o: { anchor: fhFront(13), dy: -4, r: 30, dur: 150 } },
    { at: 650, fx: 'groundCrack', o: { anchor: fhFront(13), len: 38, branches: 3, dur: 1200, col: '255,170,90' } },
    { at: 650, fx: 'sparkBurst', o: { anchor: fhFront(13), dy: -3, n: 18, spd: 200, dir: -90, arc: 160 } },
    { at: 650, call: F => { const p = fhFront(13)(F); fhDust(p.x, p.y, 14, { spd: 120, r: 3, grow: 18, life: 1.0, rise: 24 }); fhRocks(p.x, p.y, 10, { spd: 180, arc: 150, floor: F.y0, face: F.face }); } },
    // the rebound: straight back up, higher -- the head glowing white-hot at the top
    { at: 840, sfx: () => sfx.heavySwing() },
    { at: 930, sfx: () => { tone(150, 0.25, 0.07, 'sawtooth', 2.6); noise(0.2, 1600, 0.8, 0.08, 'bandpass', 2.2); } },
    { at: 1085, sfx: () => noise(0.12, 900, 0.7, 0.35, 'bandpass', 0.3) },
    // POUND (beat 2): into the floor -- the bell-bright flash and the knell, the floor broken both ways
    { at: 1120, hit: 3.5, slow: 0.45, stop: 0.17, shake: 14, flash: 0.55, boom: true, name: true, kick: 2.2, kickY: 5, zoom: 1, hy: 0.6,
      sfx: () => { fhThud(1.5); fhBell(73.4, 1.1, 2.4); fhRumble(1.2, 1.0); } },
    { at: 1120, target: { knock: 10, dur: 160 } },
    { at: 1120, fx: 'impactFlash', o: { anchor: fhFront(13), dy: -6, r: 54, dur: 230 } },
    { at: 1120, fx: fhRipple, o: { anchor: fhFront(13), dy: -2, r0: 6, r1: 120, n: 1, dur: 420, wob: 0, floor: true, life: 440 } },
    { at: 1120, fx: 'shockwave', o: { anchor: fhFront(13), r1: 175, sq: 0.18, rings: 3, gap: 85, dur: 560 } },
    { at: 1120, fx: 'shockwave', o: { r0: 10, r1: 96, sq: 1, rings: 2, gap: 90, dur: 420, thick: 2 } },
    { at: 1120, fx: 'groundCrack', o: { anchor: fhFront(13), len: 104, branches: 8, dur: 1800, col: '255,160,80' } },
    { at: 1120, fx: 'sparkBurst', o: { anchor: fhFront(13), dy: -3, n: 30, spd: 260, dir: -90, arc: 170 } },
    { at: 1120, fx: 'emberBurst', o: { anchor: fhFront(13), n: 16, w: 50, rise: 90 } },
    { at: 1120, call: F => { const p = fhFront(13)(F); fhDust(p.x, p.y, 22, { spd: 150, r: 4, grow: 24, life: 1.4, rise: 34, w: 20 }); fhRocks(p.x, p.y, 16, { spd: 240, arc: 160, floor: F.y0, size: 3, face: F.face }); } },
    // the knell's echo: a softer second ring as the dust settles
    { at: 1380, fx: 'shockwave', o: { anchor: fhFront(13), r0: 20, r1: 150, sq: 0.18, rings: 1, dur: 600, thick: 1 }, shake: 2 },
    { at: 1400, target: { drop: true } },
  ],
  // the head gathering light at the hangs (500..650, 910..1120)
  draw(F, t) {
    const hang = t >= 470 && t < 650 ? (t - 470) / 180 : t >= 900 && t < 1120 ? (t - 900) / 220 : -1;
    if (hang < 0) return;
    const tp = F.tip('a'), k = clamp(hang, 0, 1), big = t > 800 ? 1.4 : 1;
    if (typeof mvStar === 'function') mvStar(tp.x, tp.y, Math.round((2 + 3 * k) * big), fatHot(F.col), 0.5 + 0.5 * k);
    addLight(tp.x, tp.y, 26 + 30 * k * big, F.col, 0.35 + 0.35 * k);
  },
});

// ================================================================== WARBELL "Grand Requiem"
// Three tolls on the foe, rising in pitch (A, C, E -- a minor triad climbing to the last), each heavier: rings of sound
// ripple across the screen and everything shudders; the third shows a giant bell in light over the foe, ringing, that
// dissolves upward from the crown.
const FH_TOLLS = [400, 810, 1270];
// the giant bell silhouette: drops onto the foe's floor line, rings (its lip shivers), then dissolves from the crown
function fhGrandBell(ctx, t, F, e) {
  const c = F.tc(), tall = clamp((c.floor - c.top) * 1.25, 96, 132), R = tall * 0.46;
  const drop = fatEase('out', clamp(t / 70, 0, 1)), cx = Math.round(e.x), lip = Math.round(c.floor - (1 - drop) * 16), top = lip - tall;
  const ring = Math.max(0, 1 - t / 700), dis = clamp((t - 420) / (e.life - 420), 0, 1), a = (t < 70 ? 0.5 + 0.5 * drop : 1) * (1 - dis * 0.35);
  const hw = v => { let w = R * (0.35 + 0.15 * v + 0.5 * v * v * v); if (v < 0.09) w *= Math.sqrt(Math.max(0, 1 - Math.pow((0.09 - v) / 0.09, 2))); return w; };
  const sh = Math.round(Math.sin(t * 0.11) * 1.4 * ring);
  const pal = [null, `rgba(${fatHot(e.col)},${0.95 * a})`, `rgba(${fatLite(e.col)},${0.7 * a})`, `rgba(${e.col},${0.22 * a})`, `rgba(${fatLite(e.col)},${0.32 * a})`];
  fatRaster(cx - R - 3, top - 2, cx + R + 3, lip, (x, y) => {
    const v = (y + 0.5 - top) / tall; if (v < 0 || v > 1) return 0;
    if (dis > 0 && !fatDith(x, y, 1 - dis * (1.6 - v))) return 0;   // dissolves from the crown down
    const off = (y & 1) ? sh : -sh, d = hw(v) - Math.abs(x + 0.5 - cx - off * v);
    if (d < 0) return 0;
    if (d < 1) return 1;
    if (v > 0.955) return d < 2 ? 1 : 2;                                           // the lip
    if (Math.abs(v - 0.84) < 0.011 || Math.abs(v - 0.29) < 0.008) return 2;        // sound-bow and waist bands
    if (d < 2.2 && v > 0.2) return fatDith(x, y, 0.6) ? 4 : 3;
    return fatDith(x, y, 0.25 + 0.45 * v) ? 3 : 0;                                 // a faint body, brighter toward the mouth
  }, pal);
  // the crown loop and the clapper hanging in the mouth
  if (dis < 0.5) {
    g.fillStyle = pal[2]; fatEllipse(cx, top - Math.round(tall * 0.05), Math.round(R * 0.16), Math.round(tall * 0.05));
    const sw = Math.round(Math.sin(t * 0.016) * R * 0.18 * ring), y0 = top + Math.round(tall * 0.12), y1 = lip - Math.round(tall * 0.1);
    g.fillStyle = pal[2]; fatLine(cx, y0, cx + sw, y1);
    g.fillStyle = pal[1]; g.fillRect(cx + sw - 1, y1, 3, 2);
  }
  addLight(cx, lip - tall * 0.45, tall * 0.9, e.col, 0.55 * a * (1 - dis));
}
function fhToll(i) {   // one toll: the rings of sound, the shudder, the motes; i = 0, 1, 2
  const f = [110, 130.81, 164.81][i], big = i === 2;
  return [
    { at: FH_TOLLS[i], fx: fhRipple, o: { r0: 8, r1: [150, 210, 300][i], n: i + 2, gap: 120, dur: 620 + 120 * i, wob: 0.5 + 0.25 * i, life: 1200 + 120 * i } },
    { at: FH_TOLLS[i], fx: 'shockwave', o: { anchor: fhFront(15), r1: [70, 100, 180][i], sq: 0.2, rings: big ? 3 : 2, gap: 80, dur: 420 + 80 * i } },
    { at: FH_TOLLS[i], fx: 'impactFlash', o: { anchor: fhFront(15), dy: -5, r: [24, 32, 50][i], dur: 150 + 30 * i } },
    { at: FH_TOLLS[i], fx: 'emberBurst', o: { anchor: 'target', n: 6 + 5 * i, w: 40, h: 30, rise: 50 + 25 * i, spd: 40, col: '255,236,190' } },
    { at: FH_TOLLS[i], call: F => { const p = fhFront(15)(F); fhDust(p.x, p.y, 6 + 5 * i, { spd: 70 + 30 * i, r: 2 + i, grow: 12 + 5 * i, life: 0.8 + 0.2 * i }); if (big) fhRocks(p.x, p.y, 8, { spd: 150, floor: F.y0, face: F.face }); },
      sfx: () => { fhBell(f, 1 + 0.25 * i, 2.2 + 0.5 * i); if (big) fhBell(f * 0.5, 1.2, 3.4, 0.01); } },
  ];
}
fatalityRegister('bell', {
  name: 'Grand Requiem',
  col: '242,214,150',
  tag: 'wb_fatal', tags: ['wb_toll', 'wb_slam', 'riposte'],
  dur: 1800,
  steps: [
    { at: 0, move: { gap: 13, dur: 80 }, sfx: () => tone(73, 0.4, 0.07, 'sine', 0.8) },
    { at: 230, sfx: () => sfx.glint() },
    { at: 350, sfx: () => sfx.heavySwing() },
    // TOLL I
    { at: 400, hit: 1.0, stop: 0.09, shake: 6, flash: 0.18, kickY: 2, zoom: 0.4, hy: 0.4 },
    { at: 400, target: { knock: 4, dur: 120 } },
    ...fhToll(0),
    { at: 690, sfx: () => sfx.glint() },
    { at: 770, sfx: () => sfx.heavySwing() },
    // TOLL II
    { at: 810, hit: 1.2, stop: 0.11, shake: 8, flash: 0.26, kickY: 3, zoom: 0.55, hy: 0.4 },
    { at: 810, target: { knock: 8, dur: 120 } },
    ...fhToll(1),
    // the wind for the last: the bell hums, light gathering into it
    { at: 1030, fx: 'soulWisps', o: { anchor: 'player', dy: -30, from: 'ring', r: 50, n: 12, rise: 90, dur: 300, stagger: 12, to: 'tip' } },
    { at: 1060, sfx: () => { tone(220, 0.28, 0.05, 'sine', 1.5); tone(330, 0.24, 0.03, 'sine', 1.5, 0.04); } },
    { at: 1200, sfx: () => sfx.bossSwing() },
    // TOLL III: the grand toll -- the giant bell in light
    { at: 1270, hit: 2.8, slow: 0.5, stop: 0.16, shake: 13, flash: 0.5, boom: true, name: true, kick: 1.6, kickY: 4, zoom: 1, hy: 0.45 },
    { at: 1270, target: { knock: 14, dur: 180 } },
    ...fhToll(2),
    { at: 1262, fx: fhGrandBell, o: { life: 1300 } },
    { at: 1270, fx: 'sparkBurst', o: { anchor: fhFront(15), dy: -3, n: 26, spd: 240, dir: -90, arc: 170 } },
    { at: 1520, fx: fhRipple, o: { anchor: 'ground', r0: 30, r1: 160, n: 1, dur: 700, wob: 0.8, floor: true, life: 720 } },
  ],
  // after each toll everything shudders for a beat (a buzzing tremor that dies away); the bell glows as it winds
  tick(F) {
    FH_TOLLS.forEach((T, i) => { const d = F.t - T; if (d > 0 && d < 340) shake = Math.max(shake, (1.6 + 1.4 * i) * (1 - d / 340)); });
  },
  draw(F, t) {
    if (t < 1020 || t > 1270) return;
    const tp = F.tip('a'), k = clamp((t - 1020) / 220, 0, 1);
    if (typeof mvStar === 'function') mvStar(tp.x, tp.y, Math.round(2 + 3 * k), fatHot(F.col), 0.4 + 0.5 * k);
    addLight(tp.x, tp.y, 24 + 34 * k, F.col, 0.3 + 0.4 * k);
  },
});
