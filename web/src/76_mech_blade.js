// ------------------------------------------------------------------ WM: Longsword (A2) + Katana (A3)
// ================================================================== Longsword: the all-rounder
// Branching light chain (J K, J J K, J J J K, J J J hold K), a charged overhead, parry -> riposte, roll -> J / K.
// Mastery: step slash + wheel slash (II), foresight cut (III), pommel strike (IV), ember edge (V). Keeps the v3 sword ids.
// v14: J K lifting cleave, L -> K wheeling cut, air J J falling crescent (I); J J (beat) J wheel slash (II). Pommel and
// ember edge read their real inputs (hold K ~0.15 s / a press in the last 160 ms of the poke), foresight costs and recovers.
// ember edge: "perfect" = J pressed in the last 160 ms of the move (20 ms grace past its end) or <= 100 ms after it ended
function lsPerfect(q, A) { const late = A.mv.total - q.t; return (late >= -20 && late <= 160) || (q.after !== undefined && q.after <= 100); }
// the nearest foe within dx px (either side), for the turning moves
function bladeNearest(dx = 100, dy = 40) {
  let best = null; for (const t of targets()) { if (t.prop || t.alive === false) continue; const d = Math.abs(t.x - P.x); if (d < dx && Math.abs(t.y - P.y) < dy && (!best || d < best.d)) best = { t, d }; }
  return best && best.t;
}
// J J J -> K: a tap is the heavy poke, K held 0.18 s (during the poke or into the next move) is the pommel strike (IV)
const LS_POMMEL_MS = 180;   // a deliberate hold: slow taps (~100-150 ms) stay the heavy poke
function lsPokeK(q) {
  if (!mvHas(4)) return 'ls_jjjk';
  const heldFor = ((q.rel != null ? q.rel : held.has('heavy') ? P.clk : q.at) - q.at) * 1000;
  if (heldFor >= LS_POMMEL_MS) return 'ls_pommel';
  return { id: 'ls_jjjk', pommelAt: q.rel == null && held.has('heavy') ? q.at : null };
}
// a queued up+J still plays the up slash when a J route is a function (mvEnd only checks that for string routes)
const lsUpJ = fn => (q, A) => (q.up && !q.peek ? 'attack_up' : fn(q, A));
// a held-charge stance turns with the stick (you can line the release up)
function bladeTurnHold(ax) { if (ax && ax !== P.face) P.face = ax; }
mvRegister('longsword', {
  light: ['attack1', 'attack2', 'attack3', 'attack4'], K: 'heavy', up: 'attack_up', air: 'air_attack', down: 'attack_down',
  plunge: { dmg: 1.5, poise: 70, stam: 18 },
  dodge: { stam: 16, total: 420, inv: 0.28, dist: 74, tags: ['roll'] },
  rollJ: 'ls_quick',
  rollK() { return mvStart('ls_rollk'); },
  counter: () => 'ls_riposte',
  // II: L forward -> J: the roll becomes a step-cut (cancelled inside its first 150 ms; the roll's stamina comes back)
  dodgeUpdate(dt, g) {
    if (mvHas(2) && g.kind === 'roll' && g.ax === P.face && P.ground && g.t <= 150 && P.st > -10 && peek('attack')) {
      take('attack'); P.st += g.stam * (has('quickstep') ? 0.7 : 1); P.dg = null; mvStart('ls_step'); return true;
    }
  },
  // III: I -> K, the foresight stance
  parryUpdate(dt, ax) {
    if (mvHas(3) && peek('heavy') && P.st > 0) { take('heavy'); if (ax) P.face = ax; mvStart('ls_fore'); return true; }
  },
  hurt(c) {
    if (P.state === 'ls_fore' && P.mvT <= ATK.ls_fore.mv.wind && !c.negate) {   // a blow during the stance: negated, answered with a 2.8 cut
      c.negate = true; mvGain('counter');
      sfx.parry(); hitstop = Math.max(hitstop, 0.12); flashScreen = Math.max(flashScreen, 0.12);
      if (c.dir) P.face = -c.dir;
      spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 18, P.face);
      mvStart('ls_fore_cut');
    }
  },
  unlocks: [
    { rank: 2, id: 'ls_step', name: 'Step slash', input: 'L forward → J', desc: 'A quick forward step-cut instead of a roll (1.2 dmg, 10 stam), to stay close.' },
    { rank: 2, id: 'ls_wheel', name: 'Wheel slash', input: 'J J (beat) J', desc: 'Pause a beat after the 2nd cut: a full turn that cuts both sides (2 × 0.8).' },
    { rank: 3, id: 'ls_fore', name: 'Foresight cut', input: 'I → K', desc: "A 0.32 s counter stance. If you're hit during it, the hit is negated and you answer with a 2.8 slash." },
    { rank: 4, id: 'ls_pommel', name: 'Pommel strike', input: 'J J J → hold K', desc: 'A pommel bash: 1.0 dmg with 90 poise, built to break stance.' },
    { rank: 5, id: 'ls_ember', name: 'Ember edge', input: 'J J J J with perfect timing', desc: 'The critical slash ignites and a burning follow-up hit lands (+1.2 + burn).' },
  ],
  combos: [
    { rank: 1, name: 'Light chain', input: 'J J J J', desc: 'Downward, rising, poke, then the critical slash (commits).' },
    { rank: 1, name: 'Lifting cleave', input: 'J K', desc: 'A low-to-high heave that pops light foes up. J after it: the poke.' },
    { rank: 1, name: 'Horizontal slash', input: 'J J K', desc: 'A wide flat sweep across the front for crowds.' },
    { rank: 1, name: 'Heavy poke', input: 'J J J K', desc: 'A long two-handed thrust to punish from range.' },
    { rank: 1, name: 'Overhead slash', input: 'K', desc: 'The simple heavy.' },
    { rank: 1, name: 'Return slash', input: 'K J', desc: 'The blade snaps back up off the floor. J J after it: poke, crit.' },
    { rank: 1, name: 'Crosswise strike', input: 'K K', desc: 'Hands flip overhead: a flat cut at head height for tall foes.' },
    { rank: 1, name: 'Splitting cleave', input: 'J K K', desc: 'Lift the foe, then bring the blade straight down into the floor.' },
    { rank: 1, name: 'Charged overhead', input: 'hold K', desc: 'Release when the blade flashes: 2.4 dmg, breaks stance. Turnable.' },
    { rank: 1, name: 'Riposte', input: 'I (parry) → J', desc: 'After a parry: a lunging 2.2 counter.' },
    { rank: 1, name: 'Quick slash', input: 'L → J', desc: 'A rising cut straight out of the roll.' },
    { rank: 1, name: 'Wheeling cut', input: 'L → K', desc: 'Roll through, then turn on the nearest foe with a wide cut.' },
    { rank: 1, name: 'Up slash', input: '↑J', desc: 'A rising overhead cut for fliers.' },
    { rank: 1, name: 'Falling crescent', input: 'air J J', desc: 'A second air cut: a big crescent from overhead down past the feet.' },
    { rank: 1, name: 'Plunge stab', input: 'air ↓J', desc: 'Pogo off foes and spikes.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 2, name: 'Step slash', input: 'L forward → J', desc: 'The roll becomes a gliding cut: stay in close.' },
    { rank: 2, name: 'Wheel slash', input: 'J J (beat) J', desc: 'Wait a beat after the 2nd cut: a turn that cuts both sides. J: crit.' },
    { rank: 3, name: 'Foresight cut', input: 'I → K', desc: 'A short stance: a blow in it is negated and answered with a 2.8 cut.' },
    { rank: 4, name: 'Pommel strike', input: 'J J J → hold K', desc: 'Hold K ~0.2 s after the poke: a pommel bash with huge poise.' },
    { rank: 5, name: 'Ember edge', input: 'J J J ·J (on the flash)', desc: 'Press the 4th J as the poke flashes: a burning follow-up (+1.2).' },
  ],
  render() {
    // charged overhead: the blade gathers light; flashes at full charge
    if (P.state === 'ls_kc_hold') { const f = clamp(P.mvT / 300, 0, 1); addLight(P.x - P.face * 2, P.y - 30, 18 + 26 * f, f >= 1 ? '255,245,220' : '255,210,140', 0.5 + 0.5 * f); }
    // ember edge: the rank-V cue -- the poke's tip catches fire for exactly the "perfect" window
    if ((P.state === 'attack3' || P.state === 'ls_wheel') && mvHas(5) && P.mvT >= ATK[P.state].mv.total - 160) {
      addLight(P.x + P.face * 14, P.y - 20, 24, '255,160,80', 0.8);
      if (!P.lsCue) { P.lsCue = true; tone(1480, 0.08, 0.035, 'triangle', 1.4); mvStar(P.x + P.face * 30, P.y - 22, 4, '255,190,120', 0.9); }
    } else P.lsCue = false;
  },
}, {
  attack1: { tags: ['attack1'], dmg: 1.0, poise: 12, stam: 12, wind: 160, total: 380, step: 0, fx: 'slash', next: { J: 'attack2', K: 'ls_jk' } },
  attack2: { tags: ['attack2'], dmg: 1.05, poise: 12, stam: 12, wind: 160, total: 380, step: 1, lunge: 16, fx: 'slash2',
    // J J (a beat) J: a press 110-300 ms after the rising cut ended is the wheel slash (II); pressed sooner it's the poke
    next: { J: lsUpJ(q => (mvHas(2) && q.after !== undefined && q.after >= 110 ? 'ls_wheel' : 'attack3')), K: 'ls_jjk' } },
  attack3: { tags: ['attack3'], dmg: 1.1, poise: 14, stam: 13, wind: 200, total: 420, step: 2, reach: MV_SR * 1.3, fx: 'slash3',
    lungeFn() {   // chases a backing foe
      let best = null; for (const t of targets()) { if (t.prop) continue; const dx = (t.x - P.x) * P.face; if (dx > 0 && dx < 110 && Math.abs(t.y - P.y) < 30 && (!best || dx < best.dx)) best = { t, dx }; }
      return best && (best.t.vx || 0) * P.face > 10 ? 34 : 18;
    },
    on: { update() { const q = P.mvQ; if (q && q.b === 'K' && q.rel == null && !held.has('heavy')) q.rel = P.clk; } },   // when the queued K was let go
    next: { J: lsUpJ(q => ({ id: 'attack4', perfect: lsPerfect(q, ATK.attack3) })), K: lsPokeK } },
  attack4: { tags: ['ls_crit', 'riposte'], dmg: 2.0, poise: 40, stam: 18, wind: 300, total: 650, step: 3, commit: true, fin: true, lunge: 20, fx: 'heavy',
    on: {
      start(A, o) { P.emberEdge = mvHas(5) && !!o.perfect; if (P.emberEdge) { sfx.fire(); for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * rand(0, 16), y: P.y - rand(8, 30), vx: 0, vy: -rand(20, 60), life: 0.5, kind: 'fire' }); } },
      update(dt, A) {
        if (P.emberEdge && P.fireT <= 0) addLight(P.x + P.face * 14, P.y - 18, 34, '255,140,60', 0.9);
        if (P.emberEdge && P.mvT >= A.mv.wind + 170) {   // the burning follow-up: +1.2 and a burn
          P.emberEdge = false;
          const r = mvRect(A); spawnFx(fxOr('slash3', 'slash'), P.x + P.face * 22, P.y - 16, P.face, null, { tint: '#ff9050' });
          mvStrikeAt(r, 1.2, 10, { fire: true, big: true, A, onHit: t => mvBurn(t, 4, D.light * 0.08) });
          sfx.fire(); shake = Math.max(shake, 4);
        }
      },
    } },
  heavy: { tags: ['heavy'], kind: 'heavy', dmg: 1.6, poise: 45, stam: 24, wind: 380, total: 700, lunge: 20, fx: 'heavy',
    next: { J: 'ls_kj', K: 'ls_kk' },
    // K still held since the press, 150 ms in (any frame up to 230 ms, so a slow frame can't miss it): the charge stance.
    // Once K has come up, a second press is the K K follow-up, never a charge.
    on: { start() { P.lsKUp = !held.has('heavy'); },
      update(dt, A) { if (!held.has('heavy')) P.lsKUp = true; if (P.mvT >= 150 && P.mvT < 230 && !P.lsKUp && !P.mvO.noHold) mvStart('ls_kc_hold', { cost: 0 }); } } },
  ls_kc_hold: { tags: ['ls_kc_hold', 'heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt, A, ax) {
      P.vx *= Math.pow(0.05, dt); bladeTurnHold(ax);
      const full = P.mvT >= 300; P.charge = P.mvT / 1000;
      if (full && !P.lsFull) { P.lsFull = true; sfx.glint(); spawnFx('telegraph', P.x - P.face * 2, P.y - 36, P.face); if (typeof feelFlash === 'function') feelFlash(P.x, P.y - 30, 40, '255,240,210', 1.2, 0.14); }
      if (Math.random() < 0.4) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(0, 30), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'gold' });
      if (!held.has('heavy') || P.mvT > 1800) { const f = P.lsFull; P.lsFull = false; if (f) mvStart('ls_kc', { cost: 6, charged: true }); else mvStart('heavy', { cost: 0, t0: 150, noHold: true }); return 'stop'; }
    }, start() { P.lsFull = false; } } },
  ls_kc: { tags: ['ls_kc', 'heavy'], kind: 'heavy', dmg: 2.4, poise: 70, stam: 30, wind: 380, total: 650, fin: true, lunge: 24, fx: 'heavy', next: { J: 'ls_kj' } },
  ls_jjk: { tags: ['ls_jjk', 'heavy'], kind: 'heavy', dmg: 1.7, poise: 35, stam: 22, wind: 330, total: 640, box: [-16, 46, -46, 0], fin: true, fx: 'heavy', next: { J: '@J' } },
  ls_jjjk: { tags: ['ls_jjjk', 'attack3'], kind: 'heavy', dmg: 1.9, poise: 38, stam: 24, wind: 350, total: 680, lunge: 30, reach: 58, fin: true, fx: 'slash3',
    on: { update() {   // J J J -> K pressed late in the poke and kept held: it becomes the pommel strike (IV), up to 230 ms in
      const at = P.mvO.pommelAt; if (at == null || P.mvT > 230) return;
      if (!held.has('heavy')) { P.mvO.pommelAt = null; return; }
      if ((P.clk - at) * 1000 >= LS_POMMEL_MS - 1) { P.st += 24; mvStart('ls_pommel'); return 'stop'; }
    } } },
  ls_pommel: { tags: ['ls_pommel', 'heavy'], kind: 'heavy', rank: 4, dmg: 1.0, poise: 90, stam: 16, wind: 260, total: 600, box: [-2, 32, -34, -6], fin: true,
    on: { hit(t) { if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 20, P.y - 20, 30, '255,230,170', 1); shake = Math.max(shake, 4); } } },
  ls_riposte: { tags: ['ls_riposte', 'riposte'], dmg: 2.2, poise: 50, stam: 10, wind: 250, total: 600, counter: true, fin: true, lunge: 22, fx: 'heavy' },
  ls_quick: { tags: ['ls_quick', 'attack1'], dmg: 1.2, poise: 14, stam: 12, wind: 140, total: 400, lunge: 20, fx: 'slash', next: { J: 'attack2' } },
  ls_step: { tags: ['ls_step', 'attack3'], rank: 2, dmg: 1.2, poise: 14, stam: 10, wind: 140, total: 400, lunge: 36, lungeLead: 140, fx: 'slash3', next: { J: 'attack2' } },
  // III: the stance holds 320 ms; a whiff leaves you standing 200 ms more (no free invulnerability on a loop)
  ls_fore: { tags: ['ls_fore_stance', 'parry'], rank: 3, noHit: true, dmg: 0, poise: 0, stam: 8, wind: 320, total: 520,
    on: { update() { if (P.mvT > 320) return; addLight(P.x + P.face * 6, P.y - 20, 26, '230,230,255', 0.6); if (Math.random() < 0.3) particles.push({ x: P.x + P.face * rand(4, 14), y: P.y - rand(10, 30), vx: 0, vy: -rand(10, 30), life: 0.3, kind: 'mote' }); } } },
  ls_fore_cut: { tags: ['ls_fore_cut', 'counter', 'riposte'], rank: 3, dmg: 2.8, poise: 50, stam: 0, wind: 120, total: 520, counter: true, fin: true, lunge: 28, inv: [0, 220], fx: 'heavy' },
  air_attack: { tags: ['air_attack'], air: true, dmg: 1.0, poise: 12, stam: 12, wind: 150, total: 330, fx: 'slash_air', next: { J: lsUpJ(q => (P.ground ? '@J' : 'ls_air2')) } },
  attack_up: { tags: ['attack_up'], up: true, dmg: 1.0, poise: 12, stam: 12, wind: 160, total: 360, fx: 'slash_up' },
  attack_down: { tags: ['attack_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300 },
  // ---- v14 combos
  // J K: lifting cleave -- a low-to-high two-handed heave; pops light foes into the air; J after it continues with the poke
  ls_jk: { tags: ['ls_jk', 'attack2'], kind: 'heavy', dmg: 1.4, poise: 28, stam: 18, wind: 260, total: 600, lunge: 12, launch: 170, ys: [-50, 0], fx: 'slash_up',
    next: { J: 'attack3', K: 'ls_jkk' } },
  // ---- v14c J/K mixes
  // K -> J (also charged overhead -> J): return slash -- the blade bites the floor, the wrists turn and it snaps back up;
  // a heavy that branches into the light chain (K J J J = overhead, return, poke, critical)
  ls_kj: { tags: ['ls_kj', 'attack2'], dmg: 1.0, poise: 14, stam: 12, wind: 150, total: 420, lunge: 10, fx: 'slash2', next: { J: 'attack3' } },
  // K K: crosswise strike (Zwerchhau) -- hands flip over the head, the blade crosses flat at head height: tall foes, fliers close in
  ls_kk: { tags: ['ls_kk', 'heavy'], kind: 'heavy', dmg: 1.5, poise: 38, stam: 22, wind: 300, total: 660, lunge: 12, reach: 46, ys: [-52, -12], fin: true, fx: 'heavy' },
  // J K K: splitting cleave -- from the lifting cleave's high finish straight down into the floor (launch, then smash)
  ls_jkk: { tags: ['ls_jkk', 'heavy'], kind: 'heavy', dmg: 1.7, poise: 50, stam: 22, wind: 260, total: 700, lunge: 10, slam: true, fin: true, fx: 'heavy' },
  // L -> K: wheeling cut -- out of the roll, pivot to the nearest foe (you rolled through it) and cut wide
  ls_rollk: { tags: ['ls_rollk', 'heavy'], kind: 'heavy', dmg: 1.5, poise: 32, stam: 18, wind: 240, total: 600, lunge: 14, lungeLead: 240, back: 8, fin: true, fx: 'heavy',
    on: { start() { const t = bladeNearest(100); const ax = inputX(); if (t) P.face = t.x > P.x ? 1 : -1; else if (ax) P.face = ax; } } },
  // air J J: falling crescent -- the second air cut, a big arc from overhead to below the feet (the 2nd of the 2 air attacks)
  ls_air2: { tags: ['ls_air2', 'air_attack'], air: true, dmg: 1.0, poise: 14, stam: 12, wind: 150, total: 360, ys: [-40, 12], fx: 'slash_air' },
  // II: J J (beat) J: wheel slash -- a full turn, the blade passes behind you and then in front (2 x 0.8); J: the critical slash
  ls_wheel: { tags: ['ls_wheel', 'attack1'], rank: 2, hits: [0.8, 0.8], gap: 140, poise: 30, stam: 18, wind: 200, total: 620, lunge: 10, spin: true, backReach: 34, ys: [-30, 0], fx: 'slash', fxEach: true,
    next: { J: lsUpJ(q => ({ id: 'attack4', perfect: lsPerfect(q, ATK.ls_wheel) })) } },
});

// ================================================================== Katana: the patient duelist
// The sheathe: I sheathes (300 ms). Sheathed: 70% walk, J = draw cut, K = Iai draw (tap: no added delay), hold K = focus
// draw, a timed I = Iai parry (6 stam; a whiff recovers 270 ms). K while drawn is a rushing draw that sheathes you again,
// so K -> K loops. Mastery: sheathed stride + turning draw (II), flash step (III), thousand cuts (IV), moonlit iai (V).
// v14: sheathed J draw cut, J J K crescent sheathe, Iai -> J swallow return (-> I sheathes) (I); focus draw -> K turning draw (II).
function ktSheathe(on) {
  if (on && !P.sheathed) { P.sheathed = true; P.ktGlint = 0.5; sfx.glint(); tone(1760, 0.18, 0.04, 'triangle', 1.2); if (typeof feelFlash === 'function') feelFlash(P.x - P.face * 6, P.y - 14, 26, '235,240,255', 1, 0.12); }
  else if (!on) P.sheathed = false;
}
const KT_MOONLIT_S = 8;   // the moonlit Iai waits this long for its draw, then fades
mvRegister('katana', {
  light: ['kt_1', 'kt_2', 'kt_3'], K: 'kt_rush', up: 'kt_up', air: 'kt_air', down: 'kt_down',
  light0: () => (P.sheathed && P.ground ? 'kt_draw' : 'kt_1'),
  plunge: { dmg: 1.5, poise: 60, stam: 18 },
  dodge: { stam: 10, total: 260, inv: 0.16, dist: 46, tags: ['kt_sidestep', 'roll'] },
  rollJ: 'kt_stepcut',
  onK(ax) {
    if (!P.sheathed) return mvStart('kt_rush');
    if (!held.has('heavy')) return mvStart('kt_iai');            // a tap: the Iai at once
    return mvStart('kt_focus_hold');                              // held: release early = Iai, 400 ms = focus draw
  },
  onI(ax) {
    if (!P.ground) return false;
    take('parry'); if (ax) P.face = ax;
    if (P.sheathed) return P.st > 0 ? mvStart('kt_iaiw') : true;
    if (P.st <= 0) return true;
    return mvStart('kt_sheathe');
  },
  onL(ax) {
    if (P.sheathed && mvHas(3) && P.ground && P.st > 0) { if (ax) P.face = ax; return mvStart('kt_flash'); }
    return false;
  },
  started(A) { if (!['kt_sheathe', 'kt_fsheathe', 'kt_iaiw', 'kt_focus_hold', 'kt_flash'].includes(A.mv.id)) ktSheathe(false); P.ktLastMv = A.mv.id; },
  walkMul() { return P.sheathed && !mvHas(2) ? 0.7 : 1; },
  idleTag(want) { return P.sheathed ? (want === 'run' ? 'kt_sheathed_walk' : 'kt_sheathed_idle') : null; },
  hurt(c) {
    // the Iai parry: any blow inside the 150 ms window is negated and answered by the counter-cut
    if (P.state === 'kt_iaiw' && P.mvT <= 150 && !c.negate) {
      c.negate = true; mvGain('counter');
      const perfect = mvHas(5) && P.mvT <= 60;
      if (c.dir) P.face = -c.dir;
      sfx.parry(); hitstop = Math.max(hitstop, 0.14); shake = Math.max(shake, 3);
      spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 18, P.face);
      mvSpark(P.x + P.face * 10, P.y - 18, 10, '235,240,255', 180);
      if (c.opt && c.opt.src && c.opt.src.onParried) c.opt.src.onParried();
      runHooks('parry', c.opt && c.opt.src);
      if (perfect) { P.moonlit = true; P.moonlitT = KT_MOONLIT_S; slowmo = Math.max(slowmo, 0.43); flashScreen = Math.max(flashScreen, 0.2); tone(1320, 0.6, 0.06, 'sine', 1.6); }
      mvStart('kt_iaicut');
    }
  },
  tick(dt) {
    P.ktGlint = (P.ktGlint || 0) - dt;
    if (P.sheathed && P.ktGlint <= 0) { P.ktGlint = 1.4; P.ktGlintT = 0.18; }
    P.ktGlintT = (P.ktGlintT || 0) - dt;
    if (P.moonlit && (P.moonlitT = (P.moonlitT ?? KT_MOONLIT_S) - dt) <= 0) P.moonlit = false;
  },
  interrupted() { if (P.state === 'kt_sheathe') ktSheathe(false); },
  render() {
    if (P.sheathed) {   // the sheathe glint: a cold gleam runs along the scabbard every 1.4 s
      const k = Math.max(0, P.ktGlintT || 0) / 0.18, hx = P.x - P.face * 4, hy = P.y - 13;
      addLight(hx, hy, 14 + 18 * k, '220,230,255', 0.35 + 0.6 * k);
      if (k > 0) mvStar(hx - P.face * (1 - k) * 8, hy, 2 + 4 * k, '235,242,255', k);   // the gleam runs back along the scabbard
      if (k > 0.5 && Math.random() < 0.5) particles.push({ x: hx + P.face * rand(-6, 2), y: hy + rand(-2, 2), vx: 0, vy: -10, life: 0.2, kind: 'spark' });
      if (P.moonlit) addLight(P.x, P.y - 20, 30, '170,200,255', 0.6);
    }
    if (P.state === 'kt_focus_hold') { const f = clamp(P.mvT / 400, 0, 1); addLight(P.x - P.face * 4, P.y - 14, 16 + 20 * f, f >= 1 ? '235,240,255' : '170,190,240', 0.4 + 0.6 * f); }
  },
  hud(x) {
    // a sheath pip: lit while sheathed; a pale ring when the moonlit Iai is ready
    mvHudPip(x + 3, 22, P.sheathed, '#dfe6ff', 2);
    if (P.moonlit) mvHudRing(x + 3, 22, 3.6, clamp((P.moonlitT ?? KT_MOONLIT_S) / KT_MOONLIT_S, 0, 1), '#9fc0ff');
  },
  unlocks: [
    { rank: 2, id: 'kt_stride', name: 'Sheathed stride', input: '–', desc: 'Walk at full speed while sheathed.' },
    { rank: 2, id: 'kt_turn', name: 'Turning draw', input: 'focus draw → K', desc: 'After dashing through, whirl round and cut back the way you came; sheathes.' },
    { rank: 3, id: 'kt_flash', name: 'Flash step', input: 'L while sheathed', desc: 'A short invulnerable blink (50 px) that stays sheathed: no cut, but K out of it is an Iai.' },
    { rank: 4, id: 'kt_thousand', name: 'Thousand cuts', input: 'J J J → I', desc: 'Each flurry hit echoes 0.5 s later (+0.9 total).' },
    { rank: 5, id: 'kt_moonlit', name: 'Moonlit iai', input: 'perfect Iai parry', desc: 'Time slows for a moment and your next Iai (within 8 s) deals 3.0.' },
  ],
  combos: [
    { rank: 1, name: 'Light chain', input: 'J J J', desc: 'Quick cut, return cut, then a triple flurry.' },
    { rank: 1, name: 'Flurry sheathe', input: 'J J J → I', desc: 'Slide the blade home straight out of the flurry.' },
    { rank: 1, name: 'Helm splitter', input: 'J J J K', desc: 'End the flurry with one raised vertical cut: the stagger it lacks.' },
    { rank: 1, name: 'Kesa cut', input: 'J K', desc: 'A stepping shoulder-to-hip cleave. J after it: back to the chain.' },
    { rank: 1, name: 'Crescent sheathe', input: 'J J K', desc: 'A wide turning cut that ends sheathed: K next is an Iai.' },
    { rank: 1, name: 'Sheathe', input: 'I', desc: 'Sheathe the blade (70% walk). Everything from the sheathe is a draw.' },
    { rank: 1, name: 'Draw cut', input: 'J (sheathed)', desc: 'A quick low draw-cut from the hip that flows into the chain.' },
    { rank: 1, name: 'Iai draw', input: 'K (sheathed)', desc: 'The fastest heavy in the game: 2.2 dmg.' },
    { rank: 1, name: 'Swallow return', input: 'Iai → J', desc: 'A reversed rising cut snapped back after the Iai. I: sheathe again.' },
    { rank: 1, name: 'Thrust home', input: 'Iai → J → K', desc: 'A lunging thrust, then the blade is sheathed: K next is an Iai.' },
    { rank: 1, name: 'Focus draw', input: 'hold K (sheathed)', desc: 'Hold 0.4 s, release: a dash-through cut, briefly invulnerable.' },
    { rank: 1, name: 'Iai parry', input: 'I (sheathed, timed)', desc: 'Just before a blow lands: negate it and counter-cut (2.4).' },
    { rank: 1, name: 'Rushing draw', input: 'K (drawn)', desc: 'Dash in with a rising cut and sheathe again: K → K loops.' },
    { rank: 1, name: 'Step cut', input: 'L → J', desc: 'A flat cut out of the sidestep.' },
    { rank: 1, name: 'Crescent', input: '↑J', desc: 'A rising crescent for fliers.' },
    { rank: 1, name: 'Air draw', input: 'air J', desc: 'An iaido draw in the air.' },
    { rank: 1, name: 'Needle stab', input: 'air ↓J', desc: 'Pogo off foes and spikes.' },
    { rank: 1, name: 'Falling draw', input: 'air K', desc: 'A plunge.' },
    { rank: 2, name: 'Turning draw', input: 'focus draw → K', desc: 'You dashed through: whirl round, cut back, sheathe.' },
    { rank: 3, name: 'Flash step', input: 'L (sheathed)', desc: 'An invulnerable blink that keeps the sheathe; K out of it is an Iai.' },
    { rank: 4, name: 'Thousand cuts', input: 'J J J → I', desc: 'The flurry sheathe makes every flurry hit echo (+0.3 each).' },
    { rank: 5, name: 'Moonlit iai', input: 'perfect Iai parry → K', desc: 'A parry in the first 60 ms: time slows, your next Iai deals 3.0.' },
  ],
}, {
  kt_1: { tags: ['kt_1'], dmg: 0.9, poise: 10, stam: 10, wind: 140, total: 380, step: 0, fx: 'slash2', next: { J: 'kt_2', K: 'kt_kesa' } },
  kt_2: { tags: ['kt_2'], dmg: 0.9, poise: 10, stam: 10, wind: 140, total: 380, step: 1, fx: 'slash', next: { J: 'kt_3', K: 'kt_jjk' } },
  kt_3: { tags: ['kt_flurry', 'kt_3'], hits: [0.45, 0.45, 0.45], gap: 100, poise: 18, stam: 16, wind: 200, total: 680, step: 2, fin: true, fx: 'slash3', fxEach: true,
    next: { I: 'kt_fsheathe', K: 'kt_kabuto' },
    on: { start() { P.ktFlurry = []; }, hit(t) { if (!t.prop) P.ktFlurry.push({ t, at: P.clk }); } } },
  kt_fsheathe: { tags: ['kt_sheathe', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 4, wind: 250, total: 250,
    on: {
      start() {
        // IV: thousand cuts -- every flurry hit echoes 0.5 s later (0.3 each); only straight out of the flurry
        if (!mvHas(4) || !P.ktFlurry || P.ktLastMv !== 'kt_3') { P.ktFlurry = []; return; }
        for (const h of P.ktFlurry) mvLater(Math.max(0.05, h.at + 0.5 - P.clk), () => {
          const t = h.t; if (t.alive === false) return; const hb = hbOf(t); if (!hb) return;
          mvStrikeAt(rect(hb.x0, hb.y0, hb.x1, hb.y1), 0.3, 4, { only: t, A: ATK.kt_3 });
          spawnFx(fxOr('slash2', 'slash'), (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face, null, { alpha: 0.7, tint: '#cfe0ff' }); mvSpark((hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, 4, '220,230,255');
        });
        P.ktFlurry = [];
      },
      end() { ktSheathe(true); },
    } },
  kt_sheathe: { tags: ['kt_sheathe', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 4, wind: 300, total: 300, on: { end() { ktSheathe(true); } } },
  kt_rush: { tags: ['kt_rush', 'kt_heavy'], kind: 'heavy', dmg: 1.3, poise: 22, stam: 24, wind: 300, total: 760, lunge: 30, fx: 'slash3', next: { K: '@K' },
    on: { end() { ktSheathe(true); } } },
  kt_iai: { tags: ['kt_iai', 'kt_heavy'], kind: 'heavy', dmg: 2.2, poise: 40, stam: 18, wind: 110, total: 600, lunge: 20, lungeLead: 110, fin: true, fx: 'slash3', next: { K: '@K', J: 'kt_tsubame' },
    on: { start(A) { if (P.moonlit) { P.moonlit = false; P.mvMul = 3.0 / 2.2; flashScreen = Math.max(flashScreen, 0.12); } if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 16, P.y - 18, 40, '235,240,255', 1.2, 0.1); } } },
  kt_focus_hold: { tags: ['kt_focus_hold', 'kt_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt, A, ax) {
      P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000; bladeTurnHold(ax);
      if (P.mvT >= 400 && !P.ktFocus) { P.ktFocus = true; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); }
      if (!held.has('heavy') || P.mvT > 2500) {
        const f = P.ktFocus; P.ktFocus = false;
        // released early: the Iai, its clock advanced by the time K was down (up to 60 ms), so a tap adds no delay
        if (f) mvStart('kt_focus'); else mvStart('kt_iai', { t0: Math.min(P.mvT, 60) });
        return 'stop';
      }
    }, start() { P.ktFocus = false; } } },
  kt_focus: { tags: ['kt_focus', 'kt_heavy'], kind: 'heavy', dmg: 2.6, poise: 55, stam: 28, wind: 140, total: 580, lunge: 60, lungeLead: 140, lungeTail: 60, inv: [0, 150], fin: true, fx: 'slash3',
    next: { K: 'kt_turn' },
    on: { start() { P.charged = true; P.ktFocusDir = P.face; } } },
  // the Iai parry: 6 stamina a try, a whiff stands you there 270 ms more (mashing I is no longer a wall)
  kt_iaiw: { tags: ['kt_iai_parry', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 6, wind: 150, total: 420,
    on: { update() { if (P.mvT <= 150) addLight(P.x + P.face * 6, P.y - 16, 22, '220,230,255', 0.7); } } },
  kt_iaicut: { tags: ['kt_iai', 'kt_heavy'], dmg: 2.4, poise: 60, stam: 12, wind: 70, total: 500, counter: true, fin: true, lunge: 24, lungeLead: 70, inv: [0, 260], fx: 'slash3' },
  kt_stepcut: { tags: ['kt_stepcut', 'kt_1'], dmg: 1.1, poise: 12, stam: 10, wind: 140, total: 400, lunge: 24, fx: 'slash2', next: { J: 'kt_2' } },
  kt_flash: { tags: ['kt_flash', 'kt_stepcut', 'kt_heavy'], rank: 3, noHit: true, dmg: 0, poise: 0, stam: 14, wind: 80, total: 380, lunge: 50, lungeLead: 80, lungeTail: 40, inv: [0, 240], fx: null,
    on: { start() { mvAfterimage('#cfe0ff', 0.3, 0.5); }, update() { if (P.mvT < 140 && Math.random() < 0.8) mvAfterimage('#cfe0ff', 0.2, 0.35); } } },
  kt_air: { tags: ['kt_air'], air: true, dmg: 1.0, poise: 12, stam: 12, wind: 150, total: 370 },
  kt_up: { tags: ['kt_up'], up: true, dmg: 1.0, poise: 14, stam: 12, wind: 180, total: 400 },
  kt_down: { tags: ['kt_down'], down: true, dmg: 0.9, poise: 10, stam: 10, wind: 100, total: 280 },
  // ---- v14 combos
  // J while sheathed: draw cut -- a low one-handed cut straight out of the scabbard, flowing into the chain
  kt_draw: { tags: ['kt_draw', 'kt_1'], dmg: 1.1, poise: 12, stam: 10, wind: 120, total: 400, step: 0, fx: 'slash2', next: { J: 'kt_2' },
    on: { start() { if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 12, P.y - 14, 26, '235,240,255', 0.8, 0.08); } } },
  // J J K: crescent sheathe -- a wide turning cut, the follow-through slides the blade home (you end sheathed: K = Iai)
  kt_jjk: { tags: ['kt_jjk', 'kt_3'], kind: 'heavy', dmg: 1.3, poise: 26, stam: 16, wind: 240, total: 660, lunge: 10, back: 12, fx: 'slash3', next: { K: '@K' },
    on: { end() { ktSheathe(true); } } },
  // Iai -> J: swallow return -- the blade snaps back the way it came in a reversed rising cut; I after it sheathes at once
  kt_tsubame: { tags: ['kt_tsubame', 'kt_2'], dmg: 1.1, poise: 14, stam: 10, wind: 100, total: 480, fin: true, ys: [-44, -2], fx: 'slash', next: { I: 'kt_fsheathe', K: 'kt_tsuki' } },
  // ---- v14c J/K mixes
  // J K: kesa cut -- a stepping diagonal cleave from the shoulder to the hip; a heavy that hands back to the chain (J: kt_2)
  kt_kesa: { tags: ['kt_kesa', 'kt_2'], kind: 'heavy', dmg: 1.4, poise: 32, stam: 18, wind: 260, total: 640, lunge: 14, ys: [-44, 0], fx: 'slash3', next: { J: 'kt_2' } },
  // J J J K: helm splitter (kabuto-wari) -- the flurry ends in a raised jodan and one vertical cut: the stagger the flurry lacks
  kt_kabuto: { tags: ['kt_kabuto', 'kt_heavy'], kind: 'heavy', dmg: 1.6, poise: 50, stam: 20, wind: 320, total: 760, lunge: 10, fin: true, fx: 'slash3' },
  // Iai J K: thrust home (tsuki) -- a lunging straight thrust, then the blade is flicked clean and sheathed: K next is an Iai
  kt_tsuki: { tags: ['kt_tsuki', 'kt_stepcut'], kind: 'heavy', dmg: 1.1, poise: 22, stam: 14, wind: 160, total: 640, lunge: 10, lungeLead: 160, reach: 56, back: 8, ys: [-30, -6], fx: 'slash3',
    next: { K: '@K' }, on: { end() { ktSheathe(true); } } },
  // II: focus draw -> K: turning draw -- whirl round to the foe you just passed (else back the way you came), cut, sheathe
  kt_turn: { tags: ['kt_turn', 'kt_iai'], rank: 2, kind: 'heavy', dmg: 1.6, poise: 35, stam: 16, wind: 160, total: 620, lunge: 16, lungeLead: 160, fin: true, fx: 'slash3',
    on: { start() { const t = bladeNearest(120); P.face = t ? (t.x > P.x ? 1 : -1) : -(P.ktFocusDir || P.face); }, end() { ktSheathe(true); } } },
});
