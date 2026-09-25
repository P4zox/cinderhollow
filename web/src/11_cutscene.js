// ------------------------------------------------------------------ in-engine cutscenes: letterbox, camera, subtitles, scripted boss beats
let cut = null;
function playCutscene(steps, onEnd) {
  cut = { steps, i: -1, st: 0, bars: 0, sub: null, onEnd, cam: null, tween: null };
  state = 'cut'; clearBuffer(); P.vx = 0;
  if (!['idle', 'run', 'land', 'air'].includes(P.state)) setP('idle', 'idle', true);
  nextCutStep();
}
function nextCutStep() {
  while (true) {
    cut.i++; cut.st = 0; cut.tween = null;
    // hold the camera where the last pan left it; only a new pan step moves it again
    if (cut.cam) { const k = cut.cam; cam.x = k.to.x; cam.y = k.to.y; cut.cam = null; }
    const s = cut.steps[cut.i];
    if (!s) return endCutscene();
    if (s.do) { s.do(); continue; }
    if (s.pan) { cut.cam = { from: { x: cam.x, y: cam.y }, to: camTargetFor(s.pan.x, s.pan.y), dur: s.dur || 1 }; }
    if (s.say) { cut.sub = { who: s.say[0], text: s.say[1], t: 0 }; sfx.menu(); }
    if (s.tween) cut.tween = s.tween;
    return;
  }
}
function camTargetFor(x, y) {
  const maxX = room.pw - W, maxY = room.ph - H;
  return { x: maxX < 0 ? maxX / 2 : clamp(x - W / 2, 0, maxX), y: maxY < 0 ? maxY / 2 : clamp(y - H / 2, 0, maxY) };
}
function endCutscene() {
  const f = cut && cut.onEnd; cut = null; state = 'play'; clearBuffer();
  f && f();
}
function skipCutscene() {
  if (!cut) return;
  // run any remaining setup steps so the scene ends in the right state
  for (let k = cut.i + 1; k < cut.steps.length; k++) { const s = cut.steps[k]; if (s.do && s.always) s.do(); }
  endCutscene();
}
function updateCutscene(dt) {
  if (!cut) return;
  cut.st += dt; cut.bars = Math.min(1, cut.bars + dt * 2.5);
  const s = cut.steps[cut.i] || {};
  if (cut.cam) {
    const k = Math.min(1, cut.st / cut.cam.dur), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    cam.x = lerp(cut.cam.from.x, cut.cam.to.x, e); cam.y = lerp(cut.cam.from.y, cut.cam.to.y, e);
  }
  if (cut.tween) cut.tween(dt, Math.min(1, cut.st / (s.dur || 1)));
  if (cut.sub) cut.sub.t += dt;
  if (boss) { boss.anim.update(dt); boss.ambient && boss.ambient(dt); boss.commonUpdate && (boss.flash = Math.max(0, boss.flash - dt * 5)); }
  P.anim.update(dt); if (!P.ground) { P.vy = Math.min(P.vy + 800 * dt, 400); moveBody(P, dt); }
  lights = []; updateProps(dt); updateFx(dt); ambientParticles(dt); updateParticles(dt);
  shake = Math.max(0, shake - dt * 18);
  const dur = s.dur ?? (s.say ? Math.max(1.6, s.say[1].length * 0.03 + 0.9) : 0.8);
  if (s.until ? (s.until() || cut.st > (s.max || 6)) : cut.st >= dur) { if (s.say && !s.keep) cut.sub = null; nextCutStep(); }
}
function cutInput(a) {
  if (['pause', 'back'].includes(a)) { skipCutscene(); return; }
  // confirm speeds through a line
  if (['confirm', 'attack', 'jump', 'interact'].includes(a) && cut && cut.steps[cut.i] && cut.steps[cut.i].say && cut.st > 0.5) { cut.sub = null; nextCutStep(); }
}
function renderCutsceneOverlay() {
  if (!cut) return;
  const hb = 26 * cut.bars;
  vctx.fillStyle = '#000';
  vctx.fillRect(ox, oy, W * scale, hb * scale); vctx.fillRect(ox, oy + (H - hb) * scale, W * scale, hb * scale);
  if (cut.sub) {
    const a = clamp(cut.sub.t * 4, 0, 1), shown = cut.sub.text.slice(0, Math.floor(cut.sub.t * 50));
    if (cut.sub.who) text(cut.sub.who, W / 2, H - 16, 6.5, '#e6c77a', 'center', { alpha: a, spacing: 1 });
    text(shown, W / 2, H - (cut.sub.who ? 6 : 10), 7, cut.sub.who ? '#f1e6c8' : '#c9bda2', 'center', { alpha: a, weight: cut.sub.who ? 500 : 400 });
  }
  text('Esc — skip', W - 8, 10, 5, '#6f6656', 'right', { alpha: 0.8 * cut.bars });
}

// ---- scene scripts
const say = (who, t, extra = {}) => ({ say: [who, t], ...extra });
const wait = s => ({ dur: s });
const act = fn => ({ do: fn });
function bossPan(b, dy = 50, dur = 1.2) { return { pan: { x: b.x, y: b.y - dy }, dur }; }
function dustFall(n = 30) { for (let i = 0; i < n; i++) particles.push({ x: cam.x + rand(0, W), y: cam.y + rand(-10, 20), vx: rand(-5, 5), vy: rand(30, 90), g: 120, life: rand(1, 2), kind: 'dust' }); }
function holdAnim(b, tag) { b.anim.set(b.sh.has(tag) ? tag : 'idle', false); }
const BOSS_CUTS = {
  hound: b => [
    act(() => { holdAnim(b, 'stagger'); b.anim.i = b.anim.n - 1; b.anim.done = true; }),
    bossPan(b, 40, 1.6), wait(0.4),
    say('', 'Beneath the roots, something vast is sleeping.'),
    act(() => { shake = 3; sfx.boom(); dustFall(20); }), wait(0.6),
    act(() => { b.anim.set('idle', true); b.facePlayer(); }), wait(0.7),
    act(() => { holdAnim(b, 'howl'); sfx.howl(); shake = 9; flashScreen = 0.2; dustFall(50); }), wait(1.8),
  ],
  omen: b => [
    act(() => { holdAnim(b, 'stagger'); b.anim.i = Math.min(2, b.anim.n - 1); b.anim.done = true; }),
    bossPan(b, 60, 1.5),
    say('Morvain', '…Another pilgrim. Another ember that would climb to the Crown.'),
    say('Morvain', 'The Root set me here to guard its heart. It never told me when to stop.'),
    act(() => { b.anim.set('idle', true); sfx.glint(); }), wait(0.8),
    act(() => { holdAnim(b, 'roar'); }), wait(0.5),
    act(() => { sfx.roar(); shake = 10; flashScreen = 0.5; spawnFx('roar_ring', b.x, b.y - 50, 1); for (let i = 0; i < 30; i++) particles.push({ x: b.x + rand(-40, 40), y: b.y - rand(0, 100), vx: 0, vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'gold' }); }), wait(1.4),
  ],
  kalden: b => {
    const met = F('k_met1');
    return [
      act(() => { holdAnim(b, 'stagger'); b.anim.i = b.anim.n - 1; b.anim.done = true; b.face = 1; }),
      bossPan(b, 40, 1.4),
      ...(met ? [say('Ser Kalden', 'You came. Good… then the Bell will not go to the unworthy.'),
                 say('Ser Kalden', 'Iselle, forgive me. The rot has my arm… and soon the rest.'),
                 say('Ser Kalden', 'Draw your blade, friend. Do not let me win.')]
              : [say('Ser Kalden', 'Who goes there? …Another thief come for the Bell.'),
                 say('Ser Kalden', 'I swore on her grave. None shall take it.')]),
      act(() => { b.anim.set('idle', true); b.facePlayer(); }), wait(0.6),
      act(() => { holdAnim(b, 'guard'); sfx.fire(); shake = 5; for (let i = 0; i < 26; i++) particles.push({ x: b.x + rand(-16, 16), y: b.y - rand(10, 50), vx: rand(-30, 30), vy: -rand(10, 50), life: rand(0.6, 1.2), kind: 'spore' }); }), wait(1.2),
    ];
  },
  sovereign: b => [
    act(() => { b.baseY = b.floor - 170; b.y = b.baseY; b.anim.set(b.sh.has('glide') ? 'glide' : 'idle', true); }),
    { pan: { x: b.x, y: b.floor - 150 }, dur: 1.2 },
    { dur: 2.6, tween: (dt, k) => { b.baseY = lerp(b.floor - 170, b.floor, 1 - Math.pow(1 - k, 3)); b.y = b.baseY - 10; const t = camTargetFor(b.x, b.y - 60); cam.x = lerp(cam.x, t.x, Math.min(1, dt * 3)); cam.y = lerp(cam.y, t.y, Math.min(1, dt * 3)); if (Math.random() < 0.8) particles.push({ x: b.x + rand(-70, 70), y: b.y - rand(20, 140), vx: rand(-10, 10), vy: rand(10, 30), life: 2, kind: 'petal' }); } },
    act(() => { b.baseY = b.floor; b.anim.set('idle', true); }),
    say('The Pale Sovereign', 'So. The little ember climbed all the way to my heart.'),
    say('The Pale Sovereign', F('v_truth') ? 'And you brought my seedling’s blessing with you. How sweet. I will take you both.' : 'Kneel, and I will make you a root. Stand, and I will make you ash.'),
    act(() => { holdAnim(b, 'nova'); }), wait(0.7),
    act(() => { flashScreen = 0.8; shake = 10; sfx.roar(); spawnFx(fxOr('sov_nova', 'roar_ring'), b.x, b.y - 70, 1); }), wait(1.2),
  ],
};
const PHASE2_LINES = {
  hound: ['', 'The roots on its back catch fire.'],
  omen: ['Morvain', 'Then witness the light of the Crown!'],
  kalden: ['Ser Kalden', 'No… not yet… Iselle— run—'],
  sovereign: ['The Pale Sovereign', 'You would break my crown? Then burn with it.'],
};
// wrap each boss kind's activation and phase change with a scene (first time only)
function bossCutsceneStart(b) {
  const make = BOSS_CUTS[b.kind];
  if (!make || SAVE.flags['cut:' + b.kind]) return false;
  b.cutting = true;
  // ease the camera back to the player before handing control back
  playCutscene([...make(b), { pan: { x: P.x, y: P.y - 30 }, dur: 0.7 }], () => {
    SAVE.flags['cut:' + b.kind] = 1; b.cutting = false; b.active = true; b.introT = 0;
    if (b.floating) { b.baseY = b.floor; }
    else b.y = b.floor;
    b.state = 'idle'; b.anim.set('idle', true); b.cool = 0.7; b.facePlayer();
    bossBanner = { name: b.name, t: 0 }; saveGame();
  });
  return true;
}
function bossPhase2Scene(b) {
  const line = PHASE2_LINES[b.kind];
  if (!line || SAVE.flags['cutp2:' + b.kind]) return;
  SAVE.flags['cutp2:' + b.kind] = 1;
  const px = cam.x, py = cam.y;
  playCutscene([
    { pan: { x: b.x, y: b.y - 60 }, dur: 0.5 },
    act(() => { flashScreen = 0.6; shake = 8; for (let i = 0; i < 40; i++) particles.push({ x: b.x + rand(-50, 50), y: b.y - rand(0, 110), vx: rand(-40, 40), vy: -rand(20, 90), life: rand(0.6, 1.4), kind: b.kind === 'kalden' ? 'spore' : b.kind === 'sovereign' ? 'fire' : 'gold' }); b.flash = 1; }),
    say(line[0], line[1], { dur: 2.2 }),
    { pan: { x: P.x, y: P.y - 30 }, dur: 0.4 },
  ], () => { cam.x = cam.x; });
}
