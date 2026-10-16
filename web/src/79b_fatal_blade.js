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
