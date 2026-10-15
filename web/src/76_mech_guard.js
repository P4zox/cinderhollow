// ------------------------------------------------------------------ WM: Sword & Shield (A6) + Spear (A8)
// v15 (balance): guard costs follow the blow's size against YOUR health. Boss blows grow with the journey (their damage is
// scaled to keep pace with your HP) while stamina barely does, so a full bar held 2.8 typical boss blows at the start and
// 1.8 at the end (the Greatsword 2.3 -> 1.3). Costs are now scaled by GUARD_REF_HP (the expected build's HP at the first
// boss) over the HP a typical build of YOUR level has (69's stat order) -- by level, not by your Vigor, so pouring points
// into Vigor doesn't make blocks free. A full bar blocks a late blow about as often as an early one; never dearer than before.
const GUARD_REF_HP = 210, GUARD_LV = { L: -1, k: 1 };
function mvGuardScale() {
  if (typeof SAVE === 'undefined' || !SAVE || !SAVE.stats) return 1;
  const L = levelOf(SAVE.stats); if (L === GUARD_LV.L) return GUARD_LV.k;
  let v = BASE_STATS.vig; const order = ['vig', 'str', 'dex', 'end', 'vig', 'str', 'dex', 'mnd'];
  for (let i = 0, n = L - levelOf(BASE_STATS); i < n; i++) if (order[i % order.length] === 'vig') v++;
  const sv = softcap(v), hp = 60 + 10.5 * sv + 0.08 * sv * sv;
  GUARD_LV.L = L; GUARD_LV.k = Math.min(1, GUARD_REF_HP / hp);
  return GUARD_LV.k;
}
// v14 (guard pass, docs/revamp2/guard.md): perfect-rush timing fixed, parry window kept whole when you hold I, the
// perfect-guard bonus expires; the spear's guard poke opens the guard for its thrust, the charge dash's finisher costs
// stamina and needs a run, the charged counter needs a real 150 ms hold, hops keep you facing the foe. New combos:
// SnS J K (shield jab), J J J K (rim upper), L -> K (shield charge), J J . J (wheel cut, II);
// Spear J J J K (impaling drive), L -> K (hop lunge), J J . J (wheeling haft, II), counter -> J (rising sweep, III).
// ================================================================== Sword & Shield: safe and versatile
// Hold I to block (6 + 0.8 x dmg stamina, no chip), tap I to parry; I -> J guard counter. L is a backhop that leads into
// the leaping slash (J) or the shield charge (K). Flasks with the weapon out: 30% faster, and you can walk. Mastery:
// perfect rush + wheel cut (II), shield slam (III), falling bash (IV), perfect guard (V).
const SH_PAUSE = 100;   // J J (pause) J: a press 100-300 ms after the second cut ends is the wheel cut
// perfect timing (the flash): the last 150 ms of the move or 80 ms after it. mvPerfect misses a press made on the very frame
// the move ends: mvQueue stamps it after the clock has passed `total` (late < 0), so it counted as a miss.
function shPerfect(q, A) { const late = A.mv.total - q.t; return (late >= -80 && late <= 150) || (q.after !== undefined && q.after <= 80); }
mvRegister('sns', {
  light: ['sh_1', 'sh_2', 'sh_3', 'sh_4'], K: 'sh_heavy', up: 'sh_up', air: 'sh_air', down: 'sh_down',
  // IV: the falling bash replaces the plunge (air K; air down+K too while the Cinder Slam isn't yours -- that input is the slam's)
  plunge: () => (mvHas(4) ? { dmg: 1.6, poise: 80, stam: 16, pk: 'spark', bash: true, fallTag: 'sh_fallbash' } : { dmg: 1.4, poise: 70, stam: 16 }),
  dodge: { stam: 12, total: 300, inv: 0.14, dist: 44, back: true, hop: 120, tags: ['sh_backhop', 'jump_up'], keepTag: true, ghost: false },
  rollJ: g => (g.kind === 'roll' ? 'sh_leap' : null),
  rollK: g => (g.kind === 'roll' ? mvStart('sh_charge') : false),   // L -> K: the shield charge
  counter: () => 'sh_counter',
  healSpeed: 1.3, healWalk: 0.3,
  guardK() { if (mvHas(3) && P.ground) return mvStart('sh_slam'); return false; },   // III: block -> K
  guardCost(dmg) {
    const perfect = mvHas(5) && P.clk - (P.guardT0 ?? -9) <= 0.1;
    return { cost: perfect ? 0 : (6 + dmg * 0.8) * mvGuardScale() * (charmOn('c_aegis') ? 0.7 : 1), chip: 0, push: perfect ? 20 : 70, counterT: 0.6, perfect };
  },
  blocked(dmg, dir, opt, G, id) {
    if (!G.perfect) return;
    // V: perfect guard -- no stamina, projectiles fly back, the next counter (inside the 0.6 s counter window) deals +50%
    P.counterBonus = 1.5; sfx.glint(); flashScreen = Math.max(flashScreen, 0.1);
    if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 12, P.y - 18, 44, '255,245,215', 1.4, 0.14);
    // only real missiles bounce (not lingering clouds, ticking hazards or effect sprites); aimed back at the nearest foe
    const pr = projectiles.find(p => p.id === id && p.owner !== 'player' && !p.static && !p.tick && !p.fxName && !(p.delay > 0) && Math.hypot(p.vx || 0, p.vy || 0) > 30);
    if (pr) {
      pr.owner = 'player'; pr.homing = 0; pr.hits = new Set(); pr.pool = false; pr.life = Math.max(pr.life, 1.2);
      const v = Math.max(200, Math.hypot(pr.vx, pr.vy));
      let best = null, bd = 260; for (const t of targets()) { if (t.prop) continue; const hb = hbOf(t); if (!hb) continue; const cx = (hb.x0 + hb.x1) / 2, cy = (hb.y0 + hb.y1) / 2, d = Math.hypot(cx - pr.x, cy - pr.y); if (d < bd && Math.sign(cx - P.x) === P.face) { bd = d; best = { cx, cy }; } }
      if (best) { const a = Math.atan2(best.cy - pr.y, best.cx - pr.x); pr.vx = Math.cos(a) * v; pr.vy = Math.sin(a) * v; } else { pr.vx = P.face * v; pr.vy = -Math.abs(pr.vy || 0) * 0.3; }
      pr.g = (pr.g || 0) * 0.2; pr.face = Math.sign(pr.vx) || 1;
      spawnFx(fxOr('parry_spark', 'hit'), pr.x, pr.y, pr.face);
    }
  },
  onI(ax) {   // tap = parry (window 170 ms), hold = guard (04_player: startParry / updateGuard)
    if (!P.ground || P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax; startParry(); P.shRefund = true; return true;
  },
  parryUpdate() {
    if (!P.shieldParry || !held.has('parry')) return false;
    // holding I keeps the whole 170 ms parry window (it used to turn into the guard at ~95 ms, halving it) ...
    if (P.parryWin > 0 && !P.parried) return true;
    // ... then raises the guard; a press that only became a block gives the parry's 10 stamina back
    if (P.anim.i >= 2 && P.shRefund && !P.parried) { P.shRefund = false; P.st = Math.min(D.maxSt, P.st + 10); }
    return false;
  },
  tick() { if (P.counterBonus && P.gcT <= 0) P.counterBonus = 0; },   // the perfect-guard bonus lasts as long as its counter window
  interrupted() { P.shRush = false; },
  render() {
    // II: the perfect-rush flash -- the moment to press for a stronger next hit (on the 2nd cut only while the rush is alive)
    const A = ATK[P.state];
    if (mvHas(2) && A && A.mv && (A.mv.id === 'sh_1' || (A.mv.id === 'sh_2' && P.shRush)) && P.mvT >= A.mv.total - 150) { addLight(P.x + P.face * 10, P.y - 22, 20, '255,240,200', 0.9); if (!P.shFlashed) { P.shFlashed = true; mvSpark(P.x + P.face * 12, P.y - 22, 4, '255,240,200', 90); } }
    else P.shFlashed = false;
    if ((P.state === 'guard' || P.state === 'block') && mvHas(5) && P.clk - (P.guardT0 ?? -9) <= 0.1) addLight(P.x + P.face * 10, P.y - 18, 22, '255,245,215', 0.8);
  },
  unlocks: [
    { rank: 2, id: 'sh_prush', name: 'Perfect rush', input: 'J J K, each press on the flash', desc: 'Each timed hit is stronger: 0.85, 1.1, 1.8.' },
    { rank: 2, id: 'sh_wheel', name: 'Wheel cut', input: 'J J (pause) J', desc: 'A full turn: the blade cuts in front, the shield edge behind.' },
    { rank: 2, id: 'sh_aegis', name: 'Aegis plant', input: 'J J J J K', desc: 'The shield planted after the finisher: staggers both sides.' },
    { rank: 3, id: 'sh_slam', name: 'Shield slam', input: 'block → K', desc: 'A 1.6 slam with 110 poise.' },
    { rank: 4, id: 'sh_fallbash', name: 'Falling bash', input: 'air ↓K', desc: 'A 1.6 plunge with 80 poise that also pogos.' },
    { rank: 5, id: 'sh_pguard', name: 'Perfect guard', input: 'block within the last 100 ms', desc: 'Reflects projectiles, takes no stamina, and the next counter deals +50%.' },
  ],
  combos: [
    { name: 'Quick slash chain', input: 'J J J J', desc: 'Three fast cuts and a reeling shield-bash finisher.', rank: 1 },
    { name: 'Shield jab', input: 'J K', desc: 'A quick shield punch (28 poise); J carries on into the 3rd cut.', rank: 1 },
    { name: 'Rim upper', input: 'J J J K', desc: 'The shield rim driven up through the foe: launches small foes.', rank: 1 },
    { name: 'Backhand rim bash', input: 'J K K', desc: 'Jab, then the shield flung out edge-first: two bashes, 78 poise.', rank: 1 },
    { name: 'Aegis plant', input: 'J J J J K', desc: 'Plant the shield after the finisher: staggers both sides.', rank: 2 },
    { name: 'Wheel cut', input: 'J J (pause) J', desc: 'Wait a beat after the 2nd cut: a full turn, hits both sides.', rank: 2 },
    { name: 'Perfect rush', input: 'J J K on the flash', desc: 'Press each on the light flash: 0.85, 1.1, then a 1.8 bash.', rank: 2 },
    { name: 'Shield bash', input: 'K', desc: 'Drive the shield forward: 60 poise, small foes reel.', rank: 1 },
    { name: 'Under-rim cut', input: 'K J', desc: 'A low cut after the bash; J J go on to the 3rd cut and finisher.', rank: 1 },
    { name: 'Shield hammer', input: 'K K', desc: 'The shield raised overhead and its rim hammered down: 120 poise.', rank: 1 },
    { name: 'Charged shield rush', input: 'hold K', desc: 'Dash 70 px behind the shield; light hits do not stop it.', rank: 1 },
    { name: 'Block / parry', input: 'I (hold / tap)', desc: 'Hold to block anything frontal; tap to parry (170 ms).', rank: 1 },
    { name: 'Guard counter', input: 'block or parry → J', desc: 'A heavy thrust over the rim, 1.9.', rank: 1 },
    { name: 'Shield slam', input: 'block → K', desc: 'The shield brought down like a gate: 110 poise.', rank: 3 },
    { name: 'Perfect guard', input: 'I just before a blow', desc: 'Within 100 ms: free block, projectiles fly back, counter +50%.', rank: 5 },
    { name: 'Backhop', input: 'L', desc: 'A short hop back, 0.14 s invulnerable.', rank: 1 },
    { name: 'Leaping slash', input: 'L → J', desc: 'Spring forward off the backhop with an overhead cut.', rank: 1 },
    { name: 'Shield charge', input: 'L → K', desc: 'Land from the backhop and drive back in behind the shield.', rank: 1 },
    { name: 'Air slash', input: 'air J', desc: 'A low cut beneath the raised shield.', rank: 1 },
    { name: 'Shield uppercut', input: '↑J', desc: 'The shield punched overhead: for fliers.', rank: 1 },
    { name: 'Shield surf', input: 'air ↓J', desc: 'Ride the shield down: the widest pogo.', rank: 1 },
    { name: 'Falling slash', input: 'air K', desc: 'The plunge (IV: the falling bash, 1.6).', rank: 1 },
  ],
}, {
  sh_1: { tags: ['sh_1'], dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 320, step: 0, fx: 'slash',
    // the perfect flag rides on the route itself, so a press just after the cut (the 80 ms grace) still counts
    next: { J: q => (q.up ? 'sh_up' : { id: 'sh_2', step: 1, perfect: !q.peek && shPerfect(q, ATK.sh_1) }), K: 'sh_jab' } },
  sh_2: { tags: ['sh_2'], dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 320, step: 1, fx: 'slash2',
    on: { start(A, o) { P.shRush = mvHas(2) && !!o.perfect; if (P.shRush) P.mvMul = 1.1 / 0.85; } },
    next: { J: q => (q.up ? 'sh_up' : q.after !== undefined && q.after >= SH_PAUSE && mvHas(2) ? 'sh_wheel' : 'sh_3'),
      K: q => (mvHas(2) && P.shRush && shPerfect(q, ATK.sh_2) ? 'sh_prush' : '@K') } },
  sh_3: { tags: ['sh_3'], dmg: 0.9, poise: 12, stam: 10, wind: 140, total: 340, step: 2, fx: 'slash_air', next: { J: 'sh_4', K: 'sh_rim' } },
  sh_4: { tags: ['sh_4', 'sh_heavy'], dmg: 1.4, poise: 55, stam: 14, wind: 220, total: 560, step: 3, fin: true, reel: true, lunge: 20, box: [-2, 30, -30, -2],
    next: { K: () => (mvHas(2) ? 'sh_aegis' : null) } },
  // ---- v14c II: J J J J K -- the aegis plant: after the finisher, the shield planted rim-down; the ring of it staggers
  // whatever stands close on either side (a 1.0 hit both ways, 70 poise) -- room to breathe, not more damage
  sh_aegis: { tags: ['sh_aegis', 'sh_slam', 'sh_heavy'], rank: 2, kind: 'heavy', dmg: 1.0, poise: 70, stam: 14, wind: 200, total: 600, step: 4, fin: true, reel: true, spin: true, slam: true, reach: 30, backReach: 30, ys: [-20, 0], fx: null },
  // ---- v14: J K -- a quick shield jab in place of the 2nd cut (more poise, a little less damage); J goes on to the 3rd cut
  sh_jab: { tags: ['sh_jab', 'sh_heavy'], dmg: 0.7, poise: 28, stam: 9, wind: 110, total: 330, step: 1, lunge: 10, box: [-2, 30, -30, -4], fx: null, next: { J: 'sh_3', K: 'sh_jkk' } },
  // ---- v14c: J K K -- the backhand rim bash: the shield drawn across the chest and flung out edge-first (a bash pair)
  sh_jkk: { tags: ['sh_jkk', 'sh_heavy'], kind: 'heavy', dmg: 1.2, poise: 50, stam: 15, wind: 200, total: 520, step: 2, fin: true, reel: true, lunge: 16, box: [-2, 30, -30, -2], fx: null },
  // ---- v14: J J J K -- the rim upper: an alternative finisher that launches small foes (jump after it and keep cutting)
  sh_rim: { tags: ['sh_rim', 'sh_heavy'], kind: 'heavy', dmg: 1.2, poise: 50, stam: 14, wind: 200, total: 540, step: 3, fin: true, launch: 220, box: [-2, 30, -46, -2], fx: 'slash_up' },
  // ---- v14 II: J J (pause) J -- the wheel cut: a turn that cuts both sides (for crowds); 2 x 0.65
  sh_wheel: { tags: ['sh_wheel', 'sh_3'], rank: 2, hits: [0.6, 0.7], poise: 30, stam: 12, wind: 160, total: 560, step: 2, fin: true, spin: true, gap: 50, reach: 34, ys: [-30, -2], fx: 'slash' },
  sh_heavy: { tags: ['sh_heavy'], kind: 'heavy', dmg: 1.2, poise: 60, stam: 16, wind: 200, total: 520, reel: true, lunge: 24, box: [-2, 30, -30, -2],
    next: { J: 'sh_kj', K: 'sh_kk' },   // v14c: K -> J (under-rim cut, back into the chain), K -> K (shield hammer)
    on: { update() { if (P.mvT >= 120 && P.mvT < 170 && held.has('heavy') && !P.mvO.noHold) { mvStart('sh_rush_hold', { cost: 0 }); return 'stop'; } } } },
  // ---- v14c: K -> J -- the under-rim cut: the bash shoved the foe off the rim, a fast flat cut follows; J J go on (3rd cut, finisher)
  sh_kj: { tags: ['sh_kj', 'sh_2'], dmg: 0.9, poise: 15, stam: 9, wind: 110, total: 330, step: 1, reach: 36, ys: [-28, -4], fx: 'slash', next: { J: 'sh_3' } },
  // ---- v14c: K -> K -- the shield hammer: the shield hauled overhead and its rim brought down on the head (a stagger pair)
  sh_kk: { tags: ['sh_kk', 'sh_slam', 'sh_heavy'], kind: 'heavy', dmg: 1.3, poise: 60, stam: 16, wind: 220, total: 560, fin: true, reel: true, lunge: 8, box: [-2, 30, -34, 0], fx: null },
  sh_rush_hold: { tags: ['sh_rush_hold', 'sh_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000;
      if (P.mvT >= 230 && !P.shFull) { P.shFull = true; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); }
      if (!held.has('heavy') || P.mvT > 1800) { const f = P.shFull; P.shFull = false; if (f) mvStart('sh_rush', { cost: 8, charged: true }); else mvStart('sh_heavy', { cost: 0, t0: 120, noHold: true }); return 'stop'; }
    }, start() { P.shFull = false; } } },
  sh_rush: { tags: ['sh_rush', 'sh_heavy'], kind: 'heavy', dmg: 1.8, poise: 90, stam: 24, wind: 220, total: 450, lunge: 70, lungeLead: 200, lungeTail: 60, reel: true, fin: true, box: [-2, 32, -32, -2], armor: 0.3 },
  sh_prush: { tags: ['sh_heavy'], kind: 'heavy', rank: 2, dmg: 1.8, poise: 70, stam: 16, wind: 200, total: 520, reel: true, fin: true, lunge: 30, box: [-2, 32, -32, -2],
    on: { start() { if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 14, P.y - 20, 40, '255,240,200', 1.2, 0.14); sfx.glint(); } } },
  sh_counter: { tags: ['sh_counter'], dmg: 1.9, poise: 45, stam: 10, wind: 200, total: 520, counter: true, fin: true, lunge: 26, fx: 'slash_air' },
  sh_slam: { tags: ['sh_slam', 'sh_heavy'], kind: 'heavy', rank: 3, dmg: 1.6, poise: 110, stam: 18, wind: 260, total: 620, reel: true, fin: true, slam: true, box: [-2, 32, -32, 0] },
  sh_leap: { tags: ['sh_leap', 'sh_counter', 'attack4'], dmg: 1.8, poise: 40, stam: 16, wind: 320, total: 700, fin: true, lunge: 64, lungeLead: 300, fx: 'heavy',
    on: { start() { if (P.ground) { P.vy = -150; P.ground = false; } } }, airOk: true },
  // ---- v14: L -> K -- the shield charge: out of the backhop, straight back in behind the shield (stagger, not damage)
  sh_charge: { tags: ['sh_charge', 'sh_rush', 'sh_heavy'], kind: 'heavy', dmg: 1.1, poise: 60, stam: 14, wind: 200, total: 520, lunge: 52, lungeLead: 180, reel: true, fin: true, box: [-2, 32, -32, -2] },
  sh_air: { tags: ['sh_air'], air: true, dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 300 },
  sh_up: { tags: ['sh_up'], up: true, dmg: 0.9, poise: 20, stam: 10, wind: 150, total: 340 },
  sh_down: { tags: ['sh_down'], down: true, dmg: 0.9, poise: 20, stam: 10, wind: 100, total: 300, box: [-18, 18, -16, 24] },
});

// ================================================================== Spear: the walking wall
// Hold I: the heavy guard (5 + 0.5 x dmg, big hits chip 10%, hard pushback, walk slowly -- you can't turn while it's up:
// let go of I and press it again facing the other way). I + J: guard poke (the guard opens for the thrust itself);
// block -> K: counter-thrust (III: keep K held 150 ms for the charged counter). L is a hop that keeps you facing the foe
// (toward it with the direction held at it, else back; chain 2, 3 at Mastery II). Hold K while moving: charge dash.
// Mastery: triple hop + wheeling haft (II), charged counter + rising sweep (III), power guard (IV), thunder charge (V).
const SP_PAUSE = 100, SP_CC_HOLD = 150, SP_RUN_FULL = 400;   // SP_CC_HOLD: ms of real time K is held from its press (hitstop included)
function spGuardTag(moving) {
  if (P.spPower > 0 && !moving && pHas('sp_pguard')) return 'sp_pguard';
  if (moving && moving === -P.face && pHas('sp_guard_back')) return 'sp_guard_back';   // backing off behind the guard
  return moving && pHas('sp_guard_walk') ? 'sp_guard_walk' : pHas('sp_guard') ? 'sp_guard' : 'parry';
}
function spEnterGuard() {
  P.guardKind = 'spear'; P.guardT0 = P.clk;
  const t = spGuardTag(false); setP('guard', t, t !== 'parry'); if (t === 'parry') { P.anim.i = 1; P.anim.speed = 0; }
}
// the hop: toward the foe only when you push at it; otherwise back -- and never turning round
function spHop(ax, n = 1) {
  const fwd = ax && ax === P.face;
  const ok = mvDodge({ stam: 8, total: 260, inv: 0.14, dist: 40, hop: 90, chain: mvHas(2) ? 3 : 2, kind: 'hop', tags: ['sp_hop', 'jump_up'], keepTag: true, ghost: false, dir: fwd ? P.face : -P.face }, 0);
  if (ok && P.dg) P.dg.n = n;
  return ok;
}
mvRegister('spear', {
  light: ['sp_1', 'sp_2', 'sp_3'], K: 'sp_heavy', up: 'sp_up', air: 'sp_air', down: 'sp_down',
  plunge: { dmg: 1.5, poise: 70, stam: 18 },
  dodge: () => ({ stam: 8, total: 260, inv: 0.14, dist: 40, hop: 90, hopDir: true, chain: mvHas(2) ? 3 : 2, kind: 'hop', tags: ['sp_hop', 'jump_up'], keepTag: true, ghost: false }),
  onL(ax) { return spHop(ax, 1); },
  dodgeUpdate(dt, g, ax) {   // the hop chain, with the same facing rule (the engine's chain would turn you to the held direction)
    if (g.kind === 'hop' && g.chain && g.t >= g.total * 0.5 && P.st > 0 && (g.n || 1) < g.chain && peek('roll')) { take('roll'); spHop(ax, (g.n || 1) + 1); return true; }
    return false;
  },
  rollJ() {   // a hop -> J continues the poke chain where it left off
    const c = P.spChain;
    if (c && P.clk - c.t < 1.2) { const A = ATK[c.id]; let nx = A && A.mv.next && A.mv.next.J; if (typeof nx === 'function') nx = nx({ b: 'J', t: 0, at: P.clk }, A); if (nx && typeof nx === 'string' && ATK[nx]) return nx; }
    return 'sp_hpoke';
  },
  rollK: g => (g.kind === 'hop' ? mvStart('sp_hoplunge') : false),   // L -> K: the hop lunge
  counter: () => null,
  airRise() { if (!pHas('sp_jump')) return false; startSpDive(); return true; },
  onK(ax) { if (ax) return mvStart('sp_cwind'); return mvStart('sp_heavy'); },
  onI(ax) { if (!P.ground || P.st <= 0) return false; take('parry'); if (ax) P.face = ax; spEnterGuard(); return true; },
  started(A) { if (A.mv.step !== undefined) P.spChain = { id: A.mv.id, t: P.clk }; },
  guardUpdate(dt, ax, grav) {
    if (P.guardKind !== 'spear') return false;
    // walk slowly behind the guard (backwards too: the guard never turns)
    P.vx = approach(P.vx, ax * MAXV * 0.32, 700 * dt); grav();
    if (!P.ground) { P.guardKind = null; setP('air', 'jump_fall'); return true; }
    if (P.state === 'block' && P.anim.done) spEnterGuard();
    if (P.state === 'guard') { const t = spGuardTag(ax); if (P.anim.tag !== t && t !== 'parry') P.anim.set(t, true); }
    if (P.spPower > 0) { P.spPower -= dt; addLight(P.x + P.face * 10, P.y - 18, 26, '200,220,255', 0.7); }
    if (peek('attack') && P.st > 0) { take('attack'); mvStart('sp_gpoke'); return true; }   // I + J: the guard comes back after
    if (peek('heavy') && P.st > 0) {
      const kAt = buffered.get('heavy'); take('heavy');
      if (P.gcT > 0) { P.spKAt = kAt ?? performance.now(); mvStart('sp_counter'); return true; }   // block -> K (III: keep K held for the charged counter)
      if (mvHas(4)) {   // IV: power guard (I + K): 1 s (blocks cost x1.5 meanwhile), not re-armed while it's up
        if (P.spPower <= 0) { P.spPower = 1; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); if (P.state === 'guard' && pHas('sp_pguard')) P.anim.set('sp_pguard', true); }
        return true;
      }
      P.guardKind = null; mvStart('sp_heavy'); return true;
    }
    if (peek('roll') && P.st > 0) { take('roll'); P.guardKind = null; mvDodgeStart(ax); return true; }
    if (P.state === 'guard' && !held.has('parry')) { P.guardKind = null; P.spPower = 0; setP('idle', 'idle', true); return true; }
    return true;
  },
  blockPose() { setP('block', pHas('sp_pguard') && P.spPower > 0 ? 'sp_pguard' : spGuardTag(false), false); if (!pHas('sp_guard')) { P.anim.i = 1; P.anim.speed = 0.6; } },
  guardCost(dmg) {
    const pw = P.spPower > 0;
    return { cost: (5 + 0.5 * dmg) * mvGuardScale() * (pw ? 1.5 : 1) * (charmOn('c_aegis') ? 0.7 : 1), chip: !pw && dmg > D.maxHp * 0.3 ? 0.1 * dmg : 0, push: pw ? 0 : 260, counterT: 0.5 };
  },
  interrupted() { P.guardKind = null; P.spPower = 0; P.spHoldK = false; },
  render() {
    // the reach ghost: a sprite frame is 64 px wide with the feet at 28, so a thrust can draw its tip only ~34 px out while
    // it hits 52-64 px out. On each thrust's hit, two fading pale copies of the spear lance on along the thrust line to
    // the real reach, so what you see is what connects.
    { const A = ATK[P.state], d = A && A.mv, R = A && A._r;
      if (d && d.thrust !== undefined && R && R.real) {
        const hits = R.hitT || Array.from({ length: d.n }, (_, k) => d.wind + k * (d.gap || 70));
        let u = null; for (const h of hits) { const q = P.mvT - h; if (q >= -20 && q <= 140) u = q; }
        const ws = sheet('wpn_' + (SAVE.weapon || 'spear'));
        if (u !== null && ws.ok) {
          const f = u < 0 ? 0.45 : clamp(1 - u / 140, 0, 1), L = clamp((A.reach ? A.reach[1] : 60) - 36, 0, 28), a = d.thrust * Math.PI / 180;
          for (const [k, al] of [[0.5, 0.42], [1, 0.26]]) drawSprite(ws, P.anim.frame, P.x + P.face * Math.cos(a) * L * k, P.y + Math.sin(a) * L * k, P.face, { alpha: al * f, flash: 0.75, flashColor: '#b4c6ea' });
        }
      } }
    if (P.state === 'sp_run') { addLight(P.x + P.face * 20, P.y - 16, 22, mvHas(5) ? '170,200,255' : '255,220,170', 0.6); if (Math.random() < 0.6) particles.push({ x: P.x - P.face * rand(0, 10), y: P.y - rand(2, 6), vx: -P.face * 40, vy: -rand(10, 30), life: 0.3, kind: 'dust' }); }
    if (P.state === 'sp_cwind') { const f = clamp(P.mvT / 400, 0, 1); addLight(P.x + P.face * 16, P.y - 18, 12 + 16 * f, '255,220,170', 0.3 + 0.5 * f); }
    // III: the counter-thrust's tip warms while K is still held -- let go before it flashes for the quick one
    if (P.state === 'sp_counter' && mvHas(3) && P.spHoldK) addLight(P.x + P.face * 30, P.y - 16, 8 + 10 * clamp((performance.now() - (P.spKAt ?? 0)) / SP_CC_HOLD, 0, 1), '255,215,140', 0.7);
  },
  unlocks: [
    { rank: 2, id: 'sp_triplehop', name: 'Triple hop', input: 'L L L', desc: 'Chain three hops.' },
    { rank: 2, id: 'sp_wheel', name: 'Wheeling haft', input: 'J J (pause) J', desc: 'The spear spun flat round the waist: hits both sides.' },
    { rank: 2, id: 'sp_kk', name: 'Sky rake', input: 'K K', desc: 'A second, steeper high thrust that lifts small foes.' },
    { rank: 3, id: 'sp_ccounter', name: 'Charged counter', input: 'block → hold K', desc: 'Keep K held: a 3.0 counter-thrust with 90 poise.' },
    { rank: 3, id: 'sp_rsweep', name: 'Rising sweep', input: 'counter-thrust → J', desc: 'The haft swept up overhead: launches small foes.' },
    { rank: 4, id: 'sp_pguard', name: 'Power guard', input: 'I + K', desc: 'For 1 s: no pushback and no chip from anything; stamina cost ×1.5.' },
    { rank: 5, id: 'sp_thunder', name: 'Thunder charge', input: 'charge dash', desc: 'The dash pierces with lightning (+0.5 per hit) and the finisher deals 3.0.' },
  ],
  combos: [
    { name: 'Poke chain', input: 'J J J', desc: 'Three long pokes (1.5x sword reach), the last an overhead sweep.', rank: 1 },
    { name: 'Twin thrust', input: 'J K', desc: 'A poke at the knee, then the chest; J goes on to the sweep.', rank: 1 },
    { name: 'Recoil thrust', input: 'J J K', desc: 'Step back while thrusting: hit and keep your distance.', rank: 1 },
    { name: 'Impaling drive', input: 'J J J K', desc: 'Thrust it home, then twist and drive it deeper: 2 hits.', rank: 1 },
    { name: 'Wheeling haft', input: 'J J (pause) J', desc: 'Wait a beat after the 2nd poke: spin the haft, hits both sides.', rank: 2 },
    { name: 'High thrust', input: 'K', desc: 'An upward lunge: for fliers and tall foes.', rank: 1 },
    { name: 'Falling haft', input: 'K J', desc: 'Raise the spear and chop the haft down in front.', rank: 1 },
    { name: 'Sky rake', input: 'K K', desc: 'A second, steeper high thrust that lifts small foes.', rank: 2 },
    { name: 'Charge dash', input: 'hold K (moving)', desc: 'Run with the spear levelled; let go of K for the finishing thrust.', rank: 1 },
    { name: 'Heavy guard', input: 'I (hold)', desc: 'Blocks anything frontal; walk slowly behind it. Big hits chip 10%.', rank: 1 },
    { name: 'Guard poke', input: 'I + J', desc: 'A short thrust from the guard; the guard is back after it.', rank: 1 },
    { name: 'Counter-thrust', input: 'block → K', desc: 'Within 0.5 s of a block: a 2.0 lunge out of the guard.', rank: 1 },
    { name: 'Charged counter', input: 'block → hold K', desc: 'Keep K held 150 ms: a 3.0 piercing lunge, 90 poise.', rank: 3 },
    { name: 'Rising sweep', input: 'counter-thrust → J', desc: 'Sweep the haft up overhead after the counter: launches.', rank: 3 },
    { name: 'Power guard', input: 'I + K', desc: '1 s with no pushback or chip; blocks cost x1.5.', rank: 4 },
    { name: 'Hop', input: 'L', desc: 'A short hop that keeps you facing the foe; chain 2 (II: 3).', rank: 1 },
    { name: 'Hop poke', input: 'L → J', desc: 'Pokes on from where the chain left off.', rank: 1 },
    { name: 'Hop lunge', input: 'L → K', desc: 'Off the hop, a long low lunge at full stretch.', rank: 1 },
    { name: 'Jump thrust dive', input: 'air J (rising)', desc: 'Attack while rising after a jump: dive down the spear.', rank: 1 },
    { name: 'Sky thrust', input: '↑J', desc: 'Straight up at the sky: for fliers.', rank: 1 },
    { name: 'Tip-first strike', input: 'air ↓J', desc: 'Ride the spear tip down: the pogo.', rank: 1 },
    { name: 'Lance plunge', input: 'air K', desc: 'The plunge.', rank: 1 },
  ],
}, {
  sp_1: { tags: ['sp_1'], thrust: 0, dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 380, step: 0, reach: MV_SR * 1.5, fx: 'slash_air', next: { J: 'sp_2', K: 'sp_jk' } },
  // ---- v14c: J K -- the twin thrust: knee, then chest (2 hits); J carries on into the overhead sweep
  sp_jk: { tags: ['sp_jk', 'sp_1'], thrust: 0, hits: [0.5, 0.6], poise: 28, stam: 13, wind: 150, total: 520, step: 1, reach: MV_SR * 1.5, gap: 130, fx: 'slash_air', next: { J: 'sp_3' } },
  sp_2: { tags: ['sp_2'], thrust: -20, dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 380, step: 1, reach: MV_SR * 1.5, fx: 'slash_air',
    next: { J: q => (q.up ? 'sp_up' : q.after !== undefined && q.after >= SP_PAUSE && mvHas(2) ? 'sp_wheel' : 'sp_3'), K: 'sp_jjk' } },
  // ---- v14c: J J K -- the recoil thrust: the feet step back (18 px) while the arms drive the spear out -- poke and keep the wall
  sp_jjk: { tags: ['sp_jjk', 'sp_1'], thrust: 0, dmg: 1.1, poise: 25, stam: 12, wind: 160, total: 460, step: 2, fin: true, reach: MV_SR * 1.5, lunge: -18, lungeLead: 140, lungeTail: 60, fx: 'slash_air' },
  // the overhead sweep: its reach is the drawn arc (~44 px), not the thrusts' 60 (a sweep can't show a reach ghost)
  sp_3: { tags: ['sp_3'], dmg: 1.15, poise: 18, stam: 12, wind: 160, total: 420, step: 2, reach: 44, fin: true, fx: 'slash3', next: { K: 'sp_drive' } },
  // ---- v14: J J J K -- the impaling drive: thrust, then twist it a hand deeper (2 hits); stagger over damage
  sp_drive: { tags: ['sp_drive', 'sp_heavy'], thrust: 0, kind: 'heavy', hits: [0.75, 0.85], poise: 50, stam: 16, wind: 220, total: 660, step: 3, fin: true, reach: MV_SR * 1.5, lunge: 14, gap: 110, fx: 'slash3' },
  // ---- v14 II: J J (pause) J -- the wheeling haft: tip in front, butt behind (2 hits); the spear's answer to a crowd
  sp_wheel: { tags: ['sp_wheel', 'sp_3'], rank: 2, hits: [0.55, 0.7], poise: 30, stam: 13, wind: 180, total: 600, step: 2, fin: true, spin: true, gap: 50, reach: 46, ys: [-24, -2], fx: 'slash' },
  // the high thrust now has its own upward tag (v14 guard art); the box follows it: up to ~52 px high and 50 out
  sp_heavy: { tags: ['sp_high', 'sp_heavy'], thrust: -40, kind: 'heavy', dmg: 1.4, poise: 35, stam: 18, wind: 260, total: 600, box: [-4, 50, -52, -6], fx: 'slash_up',
    next: { J: 'sp_kj', K: () => (mvHas(2) ? 'sp_kk' : null) } },   // v14c: K -> J (falling haft), K -> K (II: sky rake)
  // ---- v14c: K -> J -- the falling haft: from the high thrust, the spear raised straight up and chopped down in front
  sp_kj: { tags: ['sp_kj', 'sp_3'], dmg: 1.2, poise: 40, stam: 12, wind: 180, total: 520, fin: true, box: [-4, 46, -40, 0], fx: 'slash3' },
  // ---- v14c II: K -> K -- the sky rake: a second, steeper high thrust that lifts small foes (the spear's anti-air string)
  sp_kk: { tags: ['sp_kk', 'sp_high', 'sp_up'], rank: 2, thrust: -58, kind: 'heavy', dmg: 1.3, poise: 40, stam: 15, wind: 200, total: 560, fin: true, launch: 200, lunge: 10, box: [-4, 40, -60, -10], fx: 'slash_up' },
  // the guard stays up through the coil and the recovery, not through the thrust itself (no more blocking 100% of the time
  // while poking at 2.25/s)
  sp_gpoke: { tags: ['sp_gpoke', 'sp_1'], thrust: -14, get guarding() { return P.state !== 'sp_gpoke' || P.mvT < 110 || P.mvT >= 260; }, dmg: 0.8, poise: 12, stam: 10, wind: 140, total: 380, reach: MV_SR * 1.5,
    on: { end() { if (held.has('parry') && P.ground) spEnterGuard(); } } },
  sp_counter: { tags: ['sp_counter', 'sp_heavy'], thrust: 0, dmg: 2.0, poise: 60, stam: 14, wind: 160, total: 520, counter: true, fin: true, reach: MV_SR * 1.5, lunge: 24, fx: 'slash3',
    next: { J: () => (mvHas(3) ? 'sp_rsweep' : null) },
    on: {
      start() { P.spHoldK = held.has('heavy'); },
      // III: K held without a break for 150 ms from its press (it used to be "held at any frame 100-140 ms into the move", so a
      // slightly long tap charged by accident) -> the charged counter, its coil carried on (the hit ~360 ms after the press)
      update() {
        if (!held.has('heavy')) P.spHoldK = false;
        if (mvHas(3) && P.spHoldK && P.mvT < 160 && performance.now() - (P.spKAt ?? 0) >= SP_CC_HOLD) { P.spHoldK = false; mvStart('sp_ccounter', { cost: 0, t0: P.mvT }); sfx.glint(); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 26, P.y - 16, 30, '255,215,140', 1.0, 0.1); return 'stop'; }
      } } },
  sp_ccounter: { tags: ['sp_ccounter', 'sp_heavy'], thrust: 0, rank: 3, kind: 'heavy', dmg: 3.0, poise: 90, stam: 6, wind: 360, total: 800, counter: true, fin: true, reach: MV_SR * 1.6, lunge: 36, fx: 'slash3',
    next: { J: () => (mvHas(3) ? 'sp_rsweep' : null) } },
  // ---- v14 III: counter-thrust -> J -- the rising sweep: the haft swept up overhead, launching small foes
  sp_rsweep: { tags: ['sp_rsweep', 'sp_up'], rank: 3, dmg: 1.2, poise: 40, stam: 12, wind: 160, total: 500, fin: true, launch: 220, box: [-4, 44, -56, -2], fx: 'slash_up' },
  sp_cwind: { tags: ['sp_charge_wind', 'sp_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.02, dt);
      if (!held.has('heavy')) { mvStart('sp_heavy'); return 'stop'; }
      if (peek('parry')) { take('parry'); setP('idle', 'idle', true); return 'stop'; }
      if (P.mvT >= 400) { mvStart('sp_run'); return 'stop'; }
    } } },
  sp_run: { tags: ['sp_charge_run', 'sp_1'], kind: 'heavy', loop: true, noHit: true, dmg: 0.4, poise: 15, stam: 0, wind: 1e9, total: 1e9, reach: MV_SR * 1.2, box: [-2, 46, -30, -4],
    on: {
      start() { P.spRunHit = 0; P.spRunMs = 0; },
      update(dt, A, ax, grav) {
        P.vx = P.face * 175; grav();
        P.st -= 8 * dt; P.stDelay = 0.6; P.spRunMs = P.mvT;
        P.spRunHit -= dt * 1000;
        if (P.spRunHit <= 0) { P.spRunHit = 300; mvStrikeAt(mvRect(A), 0.4 + (mvHas(5) ? 0.5 : 0), 15, { A, onHit: t => { if (mvHas(5)) { mvSpark(t.x, t.y - 14, 5, '190,215,255', 160); tone(1600, 0.06, 0.04, 'square', 0.5); } } }); }
        if (peek('parry')) { take('parry'); setP('idle', 'idle', true); return 'stop'; }
        if (!held.has('heavy') || P.mvT >= 3000 || P.st <= 0) { mvStart('sp_finish'); return 'stop'; }
        if (!P.ground) { setP('air', 'jump_fall'); return 'stop'; }
      },
    } },
  // the finishing thrust: 12 stamina; the full 2.2 (V: 3.0) / 70 poise only after a 400 ms run, a quick release is a 1.4
  // (it used to be free and full from a 0 ms run: wind-up -> release looped 2.74/s for ~0 stamina)
  sp_finish: { tags: ['sp_finish', 'sp_heavy'], thrust: 0, kind: 'heavy', dmg: 2.2, poise: 70, stam: 12, wind: 120, total: 480, fin: true, reach: MV_SR * 1.5, lunge: 20, fx: 'slash3',
    dmgFn: () => ((P.spRunMs || 0) >= SP_RUN_FULL ? (mvHas(5) ? 3.0 : 2.2) : (mvHas(5) ? 1.8 : 1.4)), poiseFn: () => ((P.spRunMs || 0) >= SP_RUN_FULL ? 70 : 40) },
  sp_hpoke: { tags: ['sp_hpoke', 'sp_1'], thrust: 0, dmg: 1.0, poise: 14, stam: 10, wind: 120, total: 360, reach: MV_SR * 1.5, fx: 'slash_air', next: { J: 'sp_2' } },
  // ---- v14: L -> K -- the hop lunge: off the hop (usually a back hop), a long low lunge back in
  sp_hoplunge: { tags: ['sp_hoplunge', 'sp_heavy'], thrust: 0, kind: 'heavy', dmg: 1.3, poise: 35, stam: 15, wind: 200, total: 540, fin: true, reach: MV_SR * 1.5, lunge: 50, lungeLead: 160, fx: 'slash3' },
  sp_dive: { tags: ['sp_dive'], air: true, dmg: 1.5, poise: 40, stam: 16, wind: 1, total: 1 },   // the jump thrust dive (04_player startSpDive): table row only
  sp_air: { tags: ['sp_air'], thrust: 0, air: true, dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 360, reach: MV_SR * 1.3 },
  sp_up: { tags: ['sp_up'], up: true, dmg: 1.1, poise: 20, stam: 12, wind: 180, total: 420 },
  sp_down: { tags: ['sp_down'], down: true, dmg: 0.9, poise: 14, stam: 10, wind: 100, total: 300 },
});
// v15 (balance): the walking wall leans on its thrusts: every spear strike carries 40% more poise (stance damage). Real-boss
// bot: it broke a boss's stance 0.7 times a fight (the Maul 3.6), so Executioner and Riposte Mastery did nothing for it.
for (const d of Object.values(MV.defs)) if (d.type === 'spear' && !d.noHit && (d.dmg || d.hits || d.dmgFn) && d.poise && !d._v15p) { d._v15p = 1; d.poise = Math.round(d.poise * 1.4); if (ATK[d.id]) ATK[d.id].poise = d.poise; }
