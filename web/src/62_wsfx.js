// ------------------------------------------------------------------ WC: weapon sounds (synthesised; same loudness as the stock sfx)
// A whoosh per class pitched by the weapon's weight, impacts that get heavier with the class, a crack at the whip's tip,
// a ring for the shield, a charged-heavy release, a landing thud. Built from tone() and a noise() twin that adds a start
// delay and an output node; everything WC plays goes through one soft clipper into `master`, so stacked layers can't clip.
// The stock sfx.swing / heavySwing / hit / bigHit / parry / block are wrapped: they only change when it's the player's
// own weapon making the sound (checked against the attack state, not tag names); everything else plays exactly as before.
const WSFX = { ac: null, master: null, bus: null, nb: null, matT: 0 };
function wsBus() {
  const ac = audio(); if (!ac || muted) return null;
  if (WSFX.ac !== ac || WSFX.master !== master || !WSFX.bus) {
    // a soft clipper, not a compressor: exactly linear below 0.7 (so levels match the stock sfx), then rounds off toward 0.98
    const c = ac.createWaveShaper(), n = 2048, cv = new Float32Array(n);
    for (let i = 0; i < n; i++) { const x = i / (n - 1) * 2 - 1, a = Math.abs(x); cv[i] = Math.sign(x) * (a <= 0.7 ? a : 0.7 + 0.28 * Math.tanh((a - 0.7) / 0.28)); }
    c.curve = cv; c.oversample = 'none';
    c.connect(master); Object.assign(WSFX, { ac, master, bus: c, nb: null });
  }
  return WSFX.bus;
}
// noise(), plus `delay` and routing into the WC bus; one shared 1 s white-noise buffer instead of a fresh one per sound
function wsNoise(dur, freq, q, vol, type = 'bandpass', slide = 0, delay = 0) {
  const bus = wsBus(); if (!bus) return;
  const ac = WSFX.ac, t0 = ac.currentTime + delay;
  if (!WSFX.nb) { const n = ac.sampleRate, b = ac.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = frand(-1, 1); WSFX.nb = b; }
  const src = ac.createBufferSource(); src.buffer = WSFX.nb;
  const f = ac.createBiquadFilter(); f.type = type; f.frequency.setValueAtTime(freq, t0); f.Q.value = q;
  if (slide) f.frequency.exponentialRampToValueAtTime(Math.max(40, freq * slide), t0 + dur);
  const gn = ac.createGain(); gn.gain.setValueAtTime(0.0001, ac.currentTime); gn.gain.setValueAtTime(vol, t0); gn.gain.linearRampToValueAtTime(0.0001, t0 + dur);   // same linear fade as noise()
  src.connect(f).connect(gn).connect(bus); src.start(t0, frand(0, 0.5)); src.stop(t0 + dur + 0.02);
}
function wsTone(freq, dur, vol, type = 'sine', slide = 1, delay = 0) { const bus = wsBus(); if (bus) tone(freq, dur, vol, type, slide, delay, bus); }

// ---- per-class whoosh: f = band centre, q, d = length, v = level (the stock swing is 2000 Hz / 0.12 s / 0.22)
const WS_CLS = {
  dagger: { f: 3300, q: 1.1, d: 0.075, v: 0.2, sl: 0.5 },
  sword: { f: 2000, q: 0.8, d: 0.12, v: 0.22, sl: 0.4 },
  katana: { f: 2700, q: 1.8, d: 0.11, v: 0.21, sl: 0.35, shing: true },
  spear: { f: 1400, q: 1.4, d: 0.11, v: 0.21, sl: 1.9 },   // rising: a thrust, not a cut
  staff: { f: 760, q: 1.0, d: 0.17, v: 0.24, sl: 0.6 },
  shield: { f: 1800, q: 0.8, d: 0.12, v: 0.22, sl: 0.4 },
  twin: { f: 2900, q: 1.0, d: 0.07, v: 0.17, sl: 0.5, dbl: 0.05 },
  scythe: { f: 1150, q: 0.9, d: 0.21, v: 0.24, sl: 0.33 },
  whip: { f: 1300, q: 1.0, d: 0.1, v: 0.16, sl: 2.2, crack: true },
  great: { f: 640, q: 0.7, d: 0.26, v: 0.3, sl: 0.3, sub: true },
};
function wsPitch() { const Wd = WEAPONS[SAVE.weapon] || {}; return Math.pow(clamp(Wd.speed || 1, 0.7, 1.45), 0.5); }
WSFX.swing = function (A) {
  const cls = feelCls(A), C = WS_CLS[cls] || WS_CLS.sword, pm = wsPitch(), heavy = A.kind === 'heavy', fin = feelFinisher(A);
  let f = C.f * pm, d = C.d / Math.sqrt(pm), v = C.v;
  if (heavy) { f *= 0.72; d *= 1.6; v = Math.min(0.35, v * 1.35); }   // the stock heavy swing peaks at 0.35
  else if (fin) { d *= 1.2; v = Math.min(0.32, v * 1.15); }
  wsNoise(d, f, C.q, v, 'bandpass', C.sl);
  if (C.dbl) wsNoise(d, f * 1.12, C.q, v * 0.85, 'bandpass', C.sl, C.dbl);   // twin blades: two cuts, a hair apart
  if (C.shing) wsTone(1900 * pm, 0.1, 0.018, 'sine', 0.55);                   // the katana's thin steel whistle
  if (C.sub) wsTone(70 * pm, d * 0.9, 0.07, 'sine', 0.6);                      // a hammer moves air you can feel
  if (C.crack) WSFX.crack(0.08, d * 0.55);                                     // the lash snaps at full extension even on a whiff
  if (heavy && P.charged) {   // charged release: a rising flare over the swing
    wsTone(240 * pm, 0.24, 0.05, 'triangle', 3.2);
    wsTone(480 * pm, 0.2, 0.025, 'sine', 2.4, 0.02);
    wsNoise(0.3, 2600, 0.8, 0.16, 'bandpass', 0.35);
  }
};
WSFX.crack = function (vol = 0.4, delay = 0) {   // whip tip: a hard, dry broadband snap
  wsNoise(0.035, 4200, 0.7, vol, 'highpass', 0, delay);
  wsNoise(0.07, 1300, 1.2, vol * 0.3, 'bandpass', 0.5, delay + 0.005);
  wsTone(2100, 0.03, vol * 0.12, 'square', 0.45, delay);
};
WSFX.ring = function (k = 1) {   // shield: a short bell-metal ring
  wsTone(1240, 0.34, 0.035 * k, 'triangle', 0.985);
  wsTone(1860, 0.24, 0.02 * k, 'sine', 0.99);
  wsTone(3100, 0.12, 0.01 * k, 'sine');
};
// impacts: the stock hit is lowpass noise 600 Hz / 0.45 + a 120 Hz square; heavier weapons go lower and longer, lighter ones snappier
WSFX.impact = function (A, big) {
  const w = feelWeight(A), cls = feelCls(A);
  if (!big) {
    wsNoise(0.07 + w * 0.07, 820 - w * 360, 1, 0.4 + w * 0.08, 'lowpass');
    wsTone(165 - w * 70, 0.08 + w * 0.07, 0.17 + w * 0.05, 'square', 0.5);
  } else {
    wsNoise(0.14 + w * 0.1, 540 - w * 200, 1, 0.52 + w * 0.03, 'lowpass');
    wsTone(104 - w * 36, 0.18 + w * 0.1, 0.26 + w * 0.02, 'square', 0.42);
    if (w > 0.7) wsTone(50, 0.26, 0.07, 'sine', 0.7);   // hammers: a sub thump under the crunch
  }
  if (cls === 'shield') WSFX.ring(big ? 1 : 0.7);
};
WSFX.mat = function (mat, w) {   // a thin material layer under the impact (rate-limited: a sweep through a crowd isn't a cymbal)
  if (FEEL.clock - WSFX.matT < 0.05) return; WSFX.matT = FEEL.clock;
  if (mat === 'metal') { wsTone(2300 + frand(-160, 160), 0.1, 0.03, 'triangle', 0.93); wsTone(3450 + frand(-120, 120), 0.07, 0.014, 'sine'); }
  else if (mat === 'stone') wsNoise(0.1, 340, 0.7, 0.12 + w * 0.04, 'lowpass', 0.6);
  else if (mat === 'frost') { wsTone(2900, 0.09, 0.018, 'sine', 1.25); wsNoise(0.06, 5200, 1, 0.08, 'highpass'); }
  else if (mat === 'ink') wsNoise(0.14, 1500, 2, 0.07, 'bandpass', 0.45);
};
WSFX.pogo = function () { wsTone(320, 0.09, 0.035, 'triangle', 1.8); };
WSFX.land = function (down, w) {   // after an air/down attack: a soft body thud (the stock land noise still plays on hard falls)
  wsTone(96 - w * 20, 0.13, 0.035 + w * 0.02 + (down ? 0.01 : 0), 'sine', 0.55);
  wsNoise(0.09, 230, 0.7, 0.08 + (down ? 0.03 : 0), 'lowpass', 0.7);
};

// ---- wrappers on the stock sounds
{
  const S = { swing: sfx.swing, heavySwing: sfx.heavySwing, hit: sfx.hit, bigHit: sfx.bigHit, parry: sfx.parry, block: sfx.block };
  // the player's swing is the one played from inside updatePlayer, on the first active frame of an ATK state
  const playerSwing = () => {
    if (FEEL.off || !FEEL.inPlayer || !P) return null;
    const A = ATK[P.state]; return A && P.anim.changed && P.anim.i === A.active[0] ? A : null;
  };
  sfx.swing = function () { const A = playerSwing(); if (!A) return S.swing.apply(this, arguments); feelOnSwing(A); WSFX.swing(A); };
  sfx.heavySwing = function () { const A = playerSwing(); if (!A) return S.heavySwing.apply(this, arguments); feelOnSwing(A); WSFX.swing(A); };
  // impacts while the player's strike is resolving (the target's hit() plays them) use the weapon's own impact
  sfx.hit = function () { if (FEEL.off || !FEEL.strikeA) return S.hit.apply(this, arguments); WSFX.impact(FEEL.strikeA, false); };
  sfx.bigHit = function () { if (FEEL.off || !FEEL.strikeA) return S.bigHit.apply(this, arguments); WSFX.impact(FEEL.strikeA, true); };
  // the whip's tip crack used the parry clang; it gets a real crack
  sfx.parry = function () { if (FEEL.off || !FEEL.strikeA || !FEEL.strikeA.crack) return S.parry.apply(this, arguments); WSFX.crack(0.3); };
  // a blow stopped on the shield rings the shield
  sfx.block = function () {
    S.block.apply(this, arguments);
    if (!FEEL.off && P && !FEEL.strikeA && wcls() === 'shield' && ['guard', 'block', 'parry'].includes(P.state)) WSFX.ring(0.9);
  };
}
if (typeof window !== 'undefined' && window.__game && window.__game.feel) window.__game.feel.WSFX = WSFX;
