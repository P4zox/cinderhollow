// ------------------------------------------------------------------ procedural ambient score
const MUSIC = { mode: null, nodes: [], nextNote: 0, step: 0, gain: null };
const SCALES = { ramparts: [0, 3, 5, 7, 10], catacombs: [0, 1, 5, 7, 8], cathedral: [0, 2, 3, 7, 9], mire: [0, 1, 3, 6, 8], crown: [0, 2, 4, 7, 9], archives: [0, 1, 4, 5, 8], boss: [0, 1, 3, 6, 7] };
const ROOTS = { ramparts: 55, catacombs: 49, cathedral: 58.27, mire: 51.9, crown: 65.4, archives: 43.65, boss: 46.25 };
function musicMode() {
  if (state === 'title') return 'title';
  if (state === 'cine') return 'crown';
  if (!room || state === 'dead' || state === 'ending') return null;
  if (boss && boss.active && boss.alive) return 'boss';
  return room.def.biome;
}
function stopDrone() { for (const n of MUSIC.nodes) { try { n.stop(AC.currentTime + 1.5); } catch (e) {} } MUSIC.nodes = []; }
function startDrone(mode) {
  const ac = AC; if (!ac) return;
  if (!MUSIC.gain) { MUSIC.gain = ac.createGain(); MUSIC.gain.gain.value = 0.0001; MUSIC.gain.connect(ac.destination); }
  const key = mode === 'title' ? 'ramparts' : mode, root = ROOTS[key];
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = mode === 'boss' ? 700 : 420; lp.connect(MUSIC.gain);
  for (const [mul, det, vol] of [[1, 0, 0.05], [1.5, 4, 0.025], [2, -5, 0.02]]) {
    const o = ac.createOscillator(), gn = ac.createGain(), lfo = ac.createOscillator(), lg2 = ac.createGain();
    o.type = mode === 'boss' ? 'sawtooth' : 'triangle'; o.frequency.value = root * mul; o.detune.value = det;
    lfo.frequency.value = 0.07 + Math.random() * 0.08; lg2.gain.value = vol * 0.6; lfo.connect(lg2).connect(gn.gain);
    gn.gain.value = vol; o.connect(gn).connect(lp); o.start(); lfo.start();
    MUSIC.nodes.push(o, lfo);
  }
}
function updateMusic() {
  const ac = AC; if (!ac) return;
  const mode = muted ? null : musicMode();
  if (mode !== MUSIC.mode) {
    stopDrone(); MUSIC.mode = mode; MUSIC.step = 0;
    if (mode) startDrone(mode);
  }
  if (!MUSIC.gain) return;
  MUSIC.gain.gain.setTargetAtTime(mode ? (mode === 'boss' ? 0.9 : 0.7) * SETTINGS.music + 0.0001 : 0.0001, ac.currentTime, 0.8);
  if (!mode) return;
  const key = mode === 'title' ? 'ramparts' : mode, sc = SCALES[key], root = ROOTS[key] * 4;
  if (ac.currentTime < MUSIC.nextNote) return;
  if (mode === 'boss') {
    // pulse: low toms + a minor ostinato
    const beat = MUSIC.step % 8;
    if (beat % 4 === 0) tone(ROOTS.boss, 0.35, 0.2, 'sine', 0.5, 0, MUSIC.gain);
    if (beat === 6) noise(0.12, 300, 0.8, 0.12, 'lowpass');
    if (beat % 2 === 0) tone(root * Math.pow(2, sc[(MUSIC.step / 2 | 0) % sc.length] / 12), 0.28, 0.03, 'square', 1, 0, MUSIC.gain);
    MUSIC.step++; MUSIC.nextNote = ac.currentTime + 0.19;
  } else {
    // sparse bells
    const n = sc[Math.floor(Math.random() * sc.length)] + (Math.random() < 0.3 ? 12 : 0), f = root * Math.pow(2, n / 12);
    tone(f, 2.8, 0.045, 'sine', 1, 0, MUSIC.gain); tone(f * 2.01, 1.6, 0.018, 'sine', 1, 0, MUSIC.gain);
    if (Math.random() < 0.35) tone(f * 1.5, 2.4, 0.027, 'triangle', 1, 0.4, MUSIC.gain);
    MUSIC.nextNote = ac.currentTime + rand(2.2, 4.5);
  }
}
