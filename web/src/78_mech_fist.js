// ------------------------------------------------------------------ v15: Martial Arts (`fist`, prefix ft_, weapon penitent_knuckles)
// docs/WEAPON_REVAMP.md C3 (★★★★), write-up docs/v15/fist.md. Two styles, one body:
//  * SWIFT (quick, light, evasive; guard high, light on the feet) and IRON (slow, rooted; its wind-ups are armoured --
//    a blow under 20% of max HP doesn't flinch it -- and it breaks stance). P.ftStyle = 'swift' | 'iron'.
//  * I from neutral changes style (a 300 ms flourish). I DURING a ground move is a SHIFT STRIKE: the move cancels
//    50 ms after its hit into the other style's linking blow (x1.15): Swift -> Falling star (Iron heel drop, J carries on
//    with the Iron chain), Iron -> Wind cut (Swift flurry, J carries on with the Swift chain). A combo can run
//    Swift -> Iron -> Swift ... (a press up to 150 ms after the move ended still shifts).
//  * Hits build FLOW (5 pips, both styles; a move that lands +0.5, a Shift strike +1, a perfect slip +1). At 5 Flow:
//    I-IV the next Shift strike ignites (Ember shift: x1.3 and a burn) and spends it; at Mastery V the Flow is kept for
//    the Ember palm (hold I in neutral). Flow fades after 6 s without a hit.
// Mastery: II spinning backfist + hundred fists; III flowing counter + tempest to mountain; IV iron to wind release;
// V ember palm. 37 move rows (the plan's 33 entries; L→J / L→K, air J J and the two style flourishes split in two).
const FT_SHIFT_AT = 50, FT_FLOW_MAX = 5, FT_HOLD_K = 130, FT_HOLD_I = 220, FT_IRON_LV = [320, 900], FT_PERFECT_MS = 120;
const FT_COL = { swift: '170,214,255', iron: '255,140,60' }, FT_HEX = { swift: '#a8d4ff', iron: '#e8843c' };
function ftIron() { return !!P && P.ftStyle === 'iron'; }
function ftSetStyle(s, loud) {
  if (!P) return;
  const was = P.ftStyle || 'swift'; P.ftStyle = s;
  if (was === s || !loud) return;
  P.ftSwT = 0.35;   // the change flash (render)
  if (s === 'iron') { tone(98, 0.3, 0.12, 'sawtooth', 0.6); noise(0.18, 260, 0.7, 0.3, 'lowpass'); }
  else { tone(1175, 0.16, 0.05, 'triangle', 1.4); noise(0.12, 2600, 1.5, 0.12, 'bandpass', 0.5); }
}
function ftFlowAdd(n) {
  const f0 = P.ftFlow || 0; P.ftFlow = clamp(f0 + n, 0, FT_FLOW_MAX); P.ftFlowT = 6;
  if (f0 < FT_FLOW_MAX && P.ftFlow >= FT_FLOW_MAX) { tone(392, 0.4, 0.07, 'triangle', 1.5); tone(784, 0.5, 0.05, 'sine', 1, 0.08); P.ftFullT = 0.5; }
}
// the Shift strike out of move d (the other style's linking blow)
function ftShift(d) {
  P.ftShiftQ = null;
  const to = d.shift; if (!to || !ATK[to] || P.st <= 0) return false;
  const ax = inputX(); if (ax) P.face = ax;
  const ember = !mvHas(5) && (P.ftFlow || 0) >= FT_FLOW_MAX;
  const from = d.style || (ftIron() ? 'iron' : 'swift');
  const q = P.mvQ, q2 = P.mvQ2;   // a J / K already pressed behind the I plays after the Shift strike (J J J -> I -> K)
  if (!mvStart(to, { mul: ember ? 1.3 : 1.15, from: d.id, ember })) return false;
  if (q) { P.mvQ = { b: q.b, t: 30, at: P.clk, up: q.up }; P.mvQ2 = q2; P.mvCarry = null; }
  mvAfterimage(FT_HEX[from], 0.28, 0.45);
  if (ember) { P.ftFlow = 0; sfx.fire(); flashScreen = Math.max(flashScreen, 0.06); mvSpark(P.x + P.face * 10, P.y - 18, 10, '255,190,110', 160); }
  MV.ftShifts = (MV.ftShifts || 0) + 1;
  return true;
}
// the dives (Iron air J, air K): hang to `wind`, then dive at (dvx, dvy) until the floor, striking on the way;
// the dive frames are held (the clock waits at diveEnd) until you land, then the impact frames play
function ftDiveUpdate(dt, A) { const d = A.mv; if (!P.ftLanded && !P.ground && P.mvT >= d.diveEnd) P.mvT = d.diveEnd - 1; if (!P.ftLanded && P.mvT > 2600) { P.ftLanded = true; P.mvT = d.total; } }
function ftDiveMove(dt, A, ax, grav) {
  const d = A.mv;
  if (P.ftLanded) { if (P.ground) P.vx *= Math.pow(0.0002, dt); else P.vx = approach(P.vx, 0, 300 * dt); grav(); return; }
  if (P.mvT < d.wind) { P.vx *= Math.pow(0.05, dt); P.vy = Math.min(P.vy + 300 * dt, 30); if (P.ground) { P.ftLanded = true; P.mvT = d.diveEnd; ftDiveLand(A); } return; }
  if (!P.ground) {
    P.vx = P.face * d.dvx; P.vy = d.dvy;
    if (Math.random() < 0.6) particles.push({ x: P.x - P.face * rand(0, 6), y: P.y - rand(4, 24), vx: 0, vy: -rand(40, 90), life: 0.22, kind: ftIron() ? 'spark' : 'mote' });
    const box = rect(Math.min(P.x - P.face * 4, P.x + P.face * d.dreach), P.y - d.dtop, Math.max(P.x - P.face * 4, P.x + P.face * d.dreach), P.y + 8);
    const n = mvStrikeAt(box, d.dmg * (P.mvMul || 1), d.poise, { A, kind: 'heavy', big: true, onHit: (t, info) => { if (!t.prop) mvOnHit(t, info, A, { mul: d.dmg }); } });
    if (n) {   // a foe met in the air: bounce off it (no landing blow)
      P.ftLanded = true; P.vy = -230; P.vx = -P.face * 40; P.mvT = Math.max(P.mvT, d.diveEnd); hitstop = Math.max(hitstop, 0.06); shake = Math.max(shake, 4);
      spawnFx(fxOr('pogo', 'hit'), P.x + P.face * 6, P.y + 4, P.face); P.airDash = true;
    }
    return;
  }
  P.ftLanded = true; P.mvT = Math.max(P.mvT, d.diveEnd); ftDiveLand(A); grav();
}
function ftDiveLand(A) {
  const d = A.mv, x1 = P.x + P.face * d.lreach;
  mvStrikeAt(rect(Math.min(P.x - P.face * 8, x1), P.y - 22, Math.max(P.x - P.face * 8, x1), P.y + 2), d.dmg * (P.mvMul || 1), d.poise, { A, kind: 'heavy', big: true, onHit: (t, info) => { if (!t.prop) mvOnHit(t, info, A, { mul: d.dmg }); } });
  shake = Math.max(shake, d.id === 'ft_aheel' ? 5 : 4); sfx.land(); if (d.id === 'ft_aheel') tone(70, 0.3, 0.2, 'sine', 0.5);
  spawnFx('dust', P.x + P.face * 8, P.y, P.face); spawnFx('shockwave', P.x + P.face * 10, P.y, 1);
  for (let i = 0; i < 10; i++) particles.push({ x: P.x + P.face * 10 + rand(-12, 12), y: P.y - 2, vx: rand(-70, 70), vy: -rand(30, 100), g: 320, life: 0.5, kind: 'dust' });
}
// grapple throw: a small foe is heaved over your shoulder and lands behind you (a boss just takes the palm)
function ftThrow(t) {
  if (!t || t.prop || t.boss || t.alive === false || (t.cfg && (t.cfg.elite || t.cfg.flying)) || t.vy === undefined) return false;
  const nx = P.x - P.face * 18;
  if (typeof solidAtPx === 'function' && (solidAtPx(nx, t.y - 6) || solidAtPx(nx, t.y - 20))) return false;
  t.x = nx; t.vx = -P.face * 70; t.vy = -170; if (t.ground !== undefined) t.ground = false;
  if (t.breakStance && t.state !== 'stagger') t.breakStance();
  shake = Math.max(shake, 5); sfx.land(); spawnFx('dust', nx, P.y, -P.face); MV.ftThrows = (MV.ftThrows || 0) + 1;
  return true;
}
function ftNearestFoe(dx = 90) { let best = null; for (const t of targets()) { if (t.prop || t.alive === false) continue; const d = Math.abs(t.x - P.x); if (d < dx && Math.abs(t.y - P.y) < 40 && (!best || d < best.d)) best = { t, d }; } return best && best.t; }
const ftUp = fn => (q, A) => (q.up && !q.peek ? MV.types.fist.up : fn(q, A));   // a queued up+J on a function route
mvRegister('fist', {
  light: ['ft_jab', 'ft_cross', 'ft_hook', 'ft_knee'], K: 'ft_snap', heavyTag: 'ft_snap',
  get up() { return ftIron() ? 'ft_heaven' : 'ft_upper'; },
  get air() { return ftIron() ? 'ft_aelbow' : 'ft_akick'; },
  down: 'ft_astomp',
  light0: () => (ftIron() ? 'ft_palm' : 'ft_jab'),
  plunge: { dmg: 1.3, poise: 50, stam: 14 },
  dodge() {
    return ftIron() ? { stam: 12, total: 340, inv: 0.16, dist: 30, move: 220, kind: 'istep', tags: ['ft_istep', 'roll'] }
      : { stam: 8, total: 240, inv: 0.18, dist: 46, move: 170, kind: 'slip', tags: ['ft_slip', 'roll'] };
  },
  rollJ(g) { if (g.kind === 'istep') return 'ft_palm'; return g.perfect && mvHas(3) ? 'ft_fcounter' : 'ft_sjab'; },
  rollK(g) { const ax = inputX(); if (ax) P.face = ax; return mvStart(g.kind === 'istep' ? 'ft_bash' : 'ft_sweep'); },
  dodged0(g) { P.ftSlip = g; },
  dodged(dmg, dir, id, opt) {   // a blow met in the first 120 ms of the slip step: a perfect slip (Flowing counter at III)
    const g = P.dg; if (P.state !== 'roll' || !g || g.kind !== 'slip' || g.perfect || g.t > FT_PERFECT_MS) return;
    g.perfect = true; MV.ftPerfect = (MV.ftPerfect || 0) + 1; ftFlowAdd(1); mvGain('perfect slip');
    tone(1760, 0.2, 0.05, 'triangle', 1.5); tone(2637, 0.3, 0.03, 'sine', 1.2, 0.04); slowmo = Math.max(slowmo, 0.08);
    mvAfterimage('#d8ecff', 0.4, 0.45); mvSpark(P.x, P.y - 16, 7, '210,232,255', 150);
  },
  dodgeUpdate(dt, g) {   // III: the Flowing counter goes out at once, still inside the slip
    if (g.perfect && mvHas(3) && P.st > -10 && peek('attack')) { take('attack'); P.dg = null; const t = ftNearestFoe(); if (t) P.face = t.x > P.x ? 1 : -1; mvStart('ft_fcounter'); return true; }
  },
  onJ(ax) {   // Iron air J: the diving elbow (Swift: the air kick string, T.air)
    if (P.ground || !ftIron() || held.has('down') || held.has('up')) return false;
    take('attack'); if (ax) P.face = ax; return mvStart('ft_aelbow') || true;
  },
  onK(ax) {
    if (ftIron()) return mvStart(held.has('heavy') ? 'ft_ichg' : 'ft_hammer');
    if (held.has('heavy') && mvHas(2)) return mvStart('ft_khold');
    return mvStart('ft_snap');
  },
  onAirK(ax) { take('heavy'); if (ax) P.face = ax; return mvStart('ft_aheel') || true; },
  onI(ax) {
    take('parry');
    if (!P.ground) { ftSetStyle(ftIron() ? 'swift' : 'iron', true); mvAfterimage(FT_HEX[ftIron() ? 'swift' : 'iron'], 0.2, 0.4); return true; }   // in the air: an instant switch
    if (ax) P.face = ax;
    const c = P.mvChain;   // a late Shift: I just after a move ended
    if (c && P.clk - c.t < 0.15 && ATK[c.id] && ATK[c.id].mv.shift) { P.mvChain = null; if (ftShift(ATK[c.id].mv)) return true; }
    if (mvHas(5) && (P.ftFlow || 0) >= FT_FLOW_MAX && held.has('parry')) return mvStart('ft_ihold');
    return mvStart(ftIron() ? 'ft_toswift' : 'ft_toiron');
  },
  started(A, o) { P.ftShiftQ = P.ftShiftCarry && A.mv.shift ? { at: P.clk } : null; P.ftShiftCarry = false; P.ftFlowGot = false; P.ftLanded = false; P.ftShiftGain = false; },
  walkMul() { return ftIron() ? 0.82 : 1; },
  idleTag(want) { return ftIron() ? (want === 'run' ? 'ft_ir_walk' : 'ft_ir_idle') : (want === 'run' ? 'ft_sw_run' : 'ft_sw_idle'); },
  hurt(c) {   // Iron: the wind-ups (and the charge, the shoulder charge) don't flinch under 20% of max HP
    const A = ATK[P.state], d = A && A.mv; if (!d || d.type !== 'fist' || !d.iron || c.negate) return;
    if ((d.ironAll || P.mvT <= d.wind) && c.dmg < D.maxHp * 0.2) { c.armor = true; P.ftArmT = 0.18; }
  },
  onHit(t, info, A) {
    if (!t || t.prop) return;
    const d = A.mv || {};
    if (!P.ftFlowGot) { P.ftFlowGot = true; ftFlowAdd(d.flow !== undefined ? d.flow : 0.5); }
    if (d.shiftStrike && !P.ftShiftGain) { P.ftShiftGain = true; mvGain('shift'); }
    if (P.mvO && P.mvO.ember) mvBurn(t, 3, D.light * 0.08);
  },
  tick(dt) {
    P.ftSwT = Math.max(0, (P.ftSwT || 0) - dt); P.ftFullT = Math.max(0, (P.ftFullT || 0) - dt); P.ftArmT = Math.max(0, (P.ftArmT || 0) - dt);
    if (P.ftFlow > 0 && (P.ftFlowT = (P.ftFlowT || 0) - dt) <= 0) { P.ftFlow = Math.max(0, Math.floor(P.ftFlow - 0.01)); P.ftFlowT = 1.5; }
    const A = ATK[P.state], d = A && A.mv;
    if (!d || d.type !== 'fist' || d.loop) return;
    // a Shift: I latched from 30 ms in and fired once the hit is out. An I pressed behind a queued J/K belongs to the
    // move that press starts (it's carried over); I mid-move on a move that can't shift is dropped (mashing I during a
    // Shift strike doesn't queue a flourish) unless it comes in the last 150 ms
    if (P.mvT >= 30 && peek('parry')) {
      if (P.mvQ) { take('parry'); P.ftShiftCarry = true; }
      else if (d.shift) { if (!P.ftShiftQ) { take('parry'); P.ftShiftQ = { at: P.clk }; } }
      else if (d.total - P.mvT > 150) take('parry');
    }
    const hitT = A._r && A._r.hitT ? A._r.hitT[0] : d.wind;
    if (d.shift && P.ftShiftQ && P.mvT >= hitT + FT_SHIFT_AT) ftShift(d);
  },
  interrupted() { P.ftShiftQ = null; P.ftShiftCarry = false; },
  render() {
    const iron = ftIron(), hx = P.x + P.face * 9, hy = P.y - 19;
    if (P.ftSwT > 0) {   // the style change: a ring of the new style's colour and a breath of light
      const k = P.ftSwT / 0.35;
      addLight(P.x, P.y - 16, 22 + 18 * (1 - k), FT_COL[iron ? 'iron' : 'swift'], 0.6 * k);
      if (Math.random() < 0.6 * k) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(2, 30), vx: rand(-20, 20), vy: -rand(20, 60), life: 0.35, kind: iron ? 'fire' : 'mote' });
    }
    if (iron) {   // Iron: a low ember heat at the knuckles
      addLight(hx, hy, 12, FT_COL.iron, 0.22 + 0.06 * Math.sin(P.clk * 3));
      if (Math.random() < 0.05) particles.push({ x: hx + rand(-2, 2), y: hy + rand(-2, 2), vx: 0, vy: -rand(10, 30), life: 0.4, kind: 'spark' });
    }
    if ((P.ftFlow || 0) >= FT_FLOW_MAX) {   // full Flow: the wraps smoulder
      addLight(hx, hy, 16, '255,170,90', 0.35 + 0.15 * Math.sin(P.clk * 8) + (P.ftFullT || 0));
      if (Math.random() < 0.35) particles.push({ x: hx + rand(-3, 3), y: hy + rand(-2, 3), vx: rand(-6, 6), vy: -rand(20, 50), life: 0.4, kind: 'fire' });
    }
    if (P.state === 'ft_ichg') { const lv = P.ftLv || 0, f = clamp(P.mvT / FT_IRON_LV[1], 0, 1); addLight(P.x - P.face * 4, P.y - 16, 14 + 20 * f, lv >= 2 ? '255,230,180' : FT_COL.iron, 0.4 + 0.5 * f); }
    if (P.state === 'ft_ihold' || (P.state === 'ft_ember' && P.mvT < ATK.ft_ember.mv.wind)) { const f = clamp(P.mvT / 380, 0, 1); addLight(P.x + P.face * 4, P.y - 18, 18 + 26 * f, '255,180,90', 0.5 + 0.5 * f); }
    if (P.ftArmT > 0) mvAura('#e07030', 0.18 * P.ftArmT / 0.18);
  },
  hud(x) {
    // the style glyph (Swift: a pale double chevron; Iron: an ember block) and the 5 Flow pips
    const iron = ftIron(), X = v => ox + v * scale, Y = v => oy + v * scale, gx = x + 2, gy = 22;
    vctx.fillStyle = 'rgba(10,8,14,0.75)'; vctx.fillRect(X(gx - 2.5), Y(gy - 3.5), 7 * scale, 7 * scale);
    if (iron) { vctx.fillStyle = FT_HEX.iron; vctx.fillRect(X(gx - 1.5), Y(gy - 2.5), 5 * scale, 5 * scale); vctx.fillStyle = '#ffd2a0'; vctx.fillRect(X(gx - 1.5), Y(gy - 2.5), 5 * scale, 1 * scale); }
    else {
      vctx.strokeStyle = FT_HEX.swift; vctx.lineWidth = scale;
      for (const o of [-1.2, 1.2]) { vctx.beginPath(); vctx.moveTo(X(gx - 1.5 + o), Y(gy - 2.4)); vctx.lineTo(X(gx + 1 + o), Y(gy)); vctx.lineTo(X(gx - 1.5 + o), Y(gy + 2.4)); vctx.stroke(); }
    }
    const f = P.ftFlow || 0, full = f >= FT_FLOW_MAX, pulse = full ? 0.5 + 0.5 * Math.sin(P.clk * 8) : 0;
    for (let i = 0; i < FT_FLOW_MAX; i++) {
      const on = i < Math.floor(f + 1e-6), half = !on && i < f;
      mvHudPip(x + 10 + i * 5, gy, on || half, full ? `rgba(255,${190 + 50 * pulse | 0},120,1)` : half ? 'rgba(200,120,60,0.6)' : '#e89a50', 1.6);
    }
    if (full && mvHas(5)) mvHudRing(x + 30, gy, 3.2, 1, `rgba(255,200,130,${0.5 + 0.5 * pulse})`);
  },
  unlocks: [
    { rank: 2, id: 'ft_backfist', name: 'Spinning backfist', input: 'Swift: J J (pause) J', desc: 'Wait a beat after the cross: a full turn into a backfist (0.9, 14 poise).' },
    { rank: 2, id: 'ft_hundred', name: 'Hundred fists', input: 'Swift: hold K', desc: 'A storm of jabs while K is held: 0.15 every 65 ms, 16 stamina a second.' },
    { rank: 3, id: 'ft_fcounter', name: 'Flowing counter', input: 'Swift: L (perfect) → J', desc: 'Slip a blow in the first 0.12 s, then J: a 1.4 counter palm (30 poise).' },
    { rank: 3, id: 'ft_tempest', name: 'Tempest to mountain', input: 'Swift: J J J → I → K', desc: 'Out of the Falling star: a Swift flurry that ends in an Iron hammer fist (2.2).' },
    { rank: 4, id: 'ft_release', name: 'Iron to wind release', input: 'Iron: hold K → I', desc: 'Let the iron fist go as a Swift dash-punch through the foe (1.2 / 1.6 / 2.2).' },
    { rank: 5, id: 'ft_ember', name: 'Ember palm', input: 'hold I (5 Flow)', desc: 'Spend all the Flow on one burning palm: 3.0 dmg, 120 poise, a burn.' },
  ],
  combos: [
    { rank: 1, name: 'Change style', input: 'I', desc: 'Swift (fast, light, evasive) ⇄ Iron (slow, armoured, breaks stance).' },
    { rank: 1, name: 'Shift strike', input: 'I mid-combo', desc: 'Cancel on the hit into the other style’s linking blow (+15%).' },
    { rank: 1, name: 'Falling star', input: 'Swift: J J → I', desc: 'An Iron heel drop out of the Swift chain. J: the Iron chain goes on.' },
    { rank: 1, name: 'Wind cut', input: 'Iron: J → I', desc: 'Four quick Swift blows out of the Iron chain. J: the Swift chain.' },
    { rank: 1, name: 'Jab · Cross · Hook · Knee rush', input: 'Swift: J J J J', desc: 'Quick hands, then three driving knees (finisher).' },
    { rank: 1, name: 'Snap kick', input: 'Swift: K', desc: 'A fast front kick. J: back into the cross.' },
    { rank: 1, name: 'Double roundhouse', input: 'Swift: K K', desc: 'Two turning kicks, the second higher.' },
    { rank: 1, name: 'Rising knee', input: 'Swift: J K', desc: 'A jumping knee that pops light foes. J: the cross.' },
    { rank: 1, name: 'Whirlwind kick', input: 'Swift: J J K', desc: 'A spinning kick that hits both sides.' },
    { rank: 1, name: 'Rising uppercut', input: 'Swift: ↑J', desc: 'A springing uppercut: launches light foes, reaches fliers.' },
    { rank: 1, name: 'Slip step', input: 'Swift: L', desc: 'A quick weave: 8 stamina, 0.18 s invulnerable.' },
    { rank: 1, name: 'Shadow jab', input: 'Swift: L → J', desc: 'A jab out of the slip. J: the cross.' },
    { rank: 1, name: 'Sliding sweep', input: 'Swift: L → K', desc: 'Slide in low and kick the legs out: trips light foes.' },
    { rank: 1, name: 'Iron palm · Elbow · Shoulder charge', input: 'Iron: J J J', desc: 'Rooted blows; the shoulder charge is armoured through.' },
    { rank: 1, name: 'Hammer fist', input: 'Iron: K', desc: 'Both fists brought down overhead: 50 poise. J: the elbow.' },
    { rank: 1, name: 'Mountain stomp', input: 'Iron: K K', desc: 'A stamp that cracks the floor: a small shockwave both sides.' },
    { rank: 1, name: 'Iron fist', input: 'Iron: hold K', desc: 'Armoured charge, 2 levels: 1.8 / 2.6. Turnable.' },
    { rank: 1, name: 'Grapple throw', input: 'Iron: J K', desc: 'Throw a small foe over your shoulder; a boss takes the palm.' },
    { rank: 1, name: 'Pillar kick', input: 'Iron: J J K', desc: 'A rising heel straight up through the foe: launches.' },
    { rank: 1, name: 'Heaven’s uppercut', input: 'Iron: ↑J', desc: 'A rooted, rising uppercut with the whole body behind it.' },
    { rank: 1, name: 'Iron step · Shoulder bash', input: 'Iron: L / L → K', desc: 'A short planted step; K out of it drives the shoulder in.' },
    { rank: 1, name: 'Air kick · Triple air kick', input: 'Swift: air J / air J J', desc: 'A snapping kick, then three more scissoring.' },
    { rank: 1, name: 'Diving elbow', input: 'Iron: air J', desc: 'Drop elbow-first at a slant to the floor.' },
    { rank: 1, name: 'Diving heel', input: 'air K', desc: 'A steep heel-first dive; bounces off a foe it meets.' },
    { rank: 1, name: 'Stomp', input: 'air ↓J', desc: 'Stamp down: pogo off foes and spikes.' },
    { rank: 1, name: 'Ember shift', input: 'Shift at 5 Flow', desc: 'Full Flow ignites the next Shift strike: x1.3 and a burn.' },
    { rank: 2, name: 'Spinning backfist', input: 'Swift: J J (pause) J', desc: 'Wait a beat after the cross: turn into a backfist. J: knee rush.' },
    { rank: 2, name: 'Hundred fists', input: 'Swift: hold K', desc: 'Jabs as fast as the eye can follow while K is held.' },
    { rank: 3, name: 'Flowing counter', input: 'Swift: L (perfect) → J', desc: 'Slip a blow at the last moment and answer it with a 1.4 palm.' },
    { rank: 3, name: 'Tempest to mountain', input: 'Swift: J J J → I → K', desc: 'Falling star, then a Swift flurry into an Iron hammer fist.' },
    { rank: 4, name: 'Iron to wind release', input: 'Iron: hold K → I', desc: 'Loose the charge as a Swift dash-punch through the foe.' },
    { rank: 5, name: 'Ember palm', input: 'hold I (5 Flow)', desc: 'All the Flow in one burning palm: 3.0, 120 poise.' },
  ],
}, {
  // ---------------------------------------------------------------- SWIFT
  ft_jab: { tags: ['ft_jab', 'dg_1'], style: 'swift', dmg: 0.5, poise: 4, stam: 6, wind: 80, total: 220, step: 0, lunge: 6, fx: null, next: { J: 'ft_cross', K: 'ft_rknee' } },
  // J J (a beat) J: a press 110-300 ms after the cross ended is the spinning backfist (II); sooner it's the hook
  ft_cross: { tags: ['ft_cross', 'dg_2'], style: 'swift', dmg: 0.55, poise: 5, stam: 6, wind: 80, total: 220, step: 1, lunge: 8, fx: null,
    next: { J: ftUp(q => (mvHas(2) && q.after !== undefined && q.after >= 110 ? 'ft_backfist' : 'ft_hook')), K: 'ft_whirl' } },
  ft_hook: { tags: ['ft_hook', 'dg_2'], style: 'swift', dmg: 0.65, poise: 8, stam: 7, wind: 100, total: 260, step: 2, lunge: 6, fx: null, next: { J: 'ft_knee' } },
  ft_knee: { tags: ['ft_knee', 'dg_heavy'], style: 'swift', hits: [0.4, 0.4, 0.4], gap: 95, poise: 20, stam: 10, wind: 120, total: 480, step: 3, fin: true, lunge: 24, fx: null },
  ft_backfist: { tags: ['ft_backfist', 'dg_4'], style: 'swift', rank: 2, dmg: 0.9, poise: 14, stam: 8, wind: 140, total: 400, step: 2, lunge: 8, back: 10, fx: null, next: { J: 'ft_knee' } },
  ft_snap: { tags: ['ft_snap', 'dg_heavy'], style: 'swift', kind: 'heavy', dmg: 0.9, poise: 12, stam: 9, wind: 140, total: 380, lunge: 8, fx: null, next: { K: 'ft_round', J: 'ft_cross' } },
  ft_round: { tags: ['ft_round', 'dg_4'], style: 'swift', kind: 'heavy', hits: [0.6, 0.6], gap: 200, poise: 20, stam: 12, wind: 160, total: 560, fin: true, lunge: 10, fx: null },
  ft_rknee: { tags: ['ft_rknee', 'dg_heavy'], style: 'swift', kind: 'heavy', dmg: 0.8, poise: 14, stam: 9, wind: 120, total: 380, lunge: 12, launch: 150, airOk: true, fx: null, next: { J: 'ft_cross' },
    on: { start() { if (P.ground) { P.vy = -110; P.ground = false; } } } },
  ft_whirl: { tags: ['ft_whirl', 'dg_4'], style: 'swift', kind: 'heavy', hits: [0.5, 0.5], gap: 140, poise: 18, stam: 11, wind: 160, total: 520, fin: true, spin: true, lunge: 6, fx: null },
  ft_upper: { tags: ['ft_upper', 'dg_up'], style: 'swift', up: true, dmg: 0.8, poise: 16, stam: 9, wind: 120, total: 400, launch: 200, fx: null },
  // hold K (Swift): released inside 130 ms it's the snap kick (no added delay); held, the hundred fists (II)
  ft_khold: { tags: ['ft_snap', 'dg_heavy'], loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt, A, ax, grav) {
      P.vx *= Math.pow(0.02, dt); grav();
      if (!held.has('heavy')) { mvStart('ft_snap', { t0: Math.min(P.mvT, 60) }); return 'stop'; }
      if (P.mvT >= FT_HOLD_K) { mvStart('ft_hundred'); return 'stop'; }
    } } },
  // II: hundred fists -- 0.15 every 65 ms while K is held (2 poise a hit), 16 stamina a second, up to 3 s
  ft_hundred: { tags: ['ft_hundred', 'dg_1'], style: 'swift', rank: 2, loop: true, noHit: true, dmg: 0.15, poise: 2, stam: 4, wind: 1e9, total: 1e9,
    on: {
      start() { P.ftHT = 90; P.ftHN = 0; },
      update(dt, A, ax, grav) {
        P.vx = approach(P.vx, P.face * 10, 400 * dt); grav();
        P.st -= 16 * dt; P.stDelay = Math.max(P.stDelay || 0, 0.4);
        if ((P.ftHT -= dt * 1000) <= 0) {
          P.ftHT += 65; P.ftHN++;
          const y = P.y - 22 + ((P.ftHN * 5) % 9), x0 = P.x + P.face * 4, x1 = P.x + P.face * 30;
          const n = mvStrikeAt(rect(Math.min(x0, x1), P.y - 32, Math.max(x0, x1), P.y - 8), A.mv.dmg, A.mv.poise, { A });
          if (n) { ftFlowAdd(0.08); mvSpark(P.x + P.face * 22, y, 2, '255,236,210', 90); }
          if (P.ftHN % 2) sfx.swing();
        }
        if (!held.has('heavy') || P.st <= 0 || P.mvT > 3000) { mvEnd(A); return 'stop'; }
      } } },
  ft_sjab: { tags: ['ft_sjab', 'dg_1'], style: 'swift', dmg: 0.8, poise: 10, stam: 8, wind: 100, total: 320, lunge: 20, lungeLead: 100, fx: null, next: { J: 'ft_cross' } },
  ft_sweep: { tags: ['ft_sweep', 'dg_3'], style: 'swift', kind: 'heavy', dmg: 0.9, poise: 22, stam: 10, wind: 140, total: 460, lunge: 26, lungeLead: 140, reel: true, ys: [-16, 0], fin: true, fx: null },
  ft_fcounter: { tags: ['ft_fcounter', 'dg_heavy'], style: 'swift', rank: 3, dmg: 1.4, poise: 30, stam: 6, wind: 80, total: 400, counter: true, fin: true, lunge: 20, lungeLead: 80, flow: 1, fx: null,
    on: { start() { mvAfterimage('#d8ecff', 0.3, 0.5); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 14, P.y - 18, 30, '220,236,255', 1, 0.1); } } },
  // ---------------------------------------------------------------- IRON
  ft_palm: { tags: ['ft_palm', 'dg_1'], style: 'iron', iron: true, dmg: 1.1, poise: 30, stam: 12, wind: 260, total: 560, step: 0, lunge: 10, fx: null, next: { J: 'ft_elbow', K: 'ft_throw' } },
  ft_elbow: { tags: ['ft_elbow', 'dg_2'], style: 'iron', iron: true, dmg: 1.2, poise: 34, stam: 12, wind: 260, total: 560, step: 1, lunge: 10, fx: null, next: { J: 'ft_shoulder', K: 'ft_pillar' } },
  ft_shoulder: { tags: ['ft_shoulder', 'dg_3'], style: 'iron', iron: true, ironAll: true, dmg: 1.6, poise: 60, stam: 16, wind: 320, total: 740, step: 2, fin: true, lunge: 28, fx: null,
    on: { swing() { shake = Math.max(shake, 4); spawnFx('dust', P.x + P.face * 6, P.y, P.face); } } },
  ft_hammer: { tags: ['ft_hammer', 'dg_heavy'], style: 'iron', iron: true, kind: 'heavy', dmg: 1.5, poise: 50, stam: 16, wind: 340, total: 800, lunge: 8, fx: null, next: { K: 'ft_stomp', J: 'ft_elbow' },
    on: { swing() { shake = Math.max(shake, 3); } } },
  ft_stomp: { tags: ['ft_stomp', 'dg_heavy'], style: 'iron', iron: true, kind: 'heavy', dmg: 1.0, poise: 40, stam: 18, wind: 360, total: 900, fin: true, ys: [-24, 0],
    on: { swing() { mvShockwave({ r: 34, h: 18, dmg: 0.6, poise: 30, shake: 6 }); sfx.boom(); spawnFx('ground_crack', P.x + P.face * 10, P.y, 1); } } },
  // hold K (Iron): the armoured charge, 2 levels (320 / 900 ms); released early = the hammer fist; I at IV = the release
  ft_ichg: { tags: ['ft_ichg', 'dg_heavy'], style: 'iron', iron: true, ironAll: true, kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: {
      start() { P.ftLv = 0; },
      update(dt, A, ax, grav) {
        P.vx *= Math.pow(0.05, dt); grav(); if (ax && ax !== P.face) P.face = ax;
        const lv = P.mvT >= FT_IRON_LV[1] ? 2 : P.mvT >= FT_IRON_LV[0] ? 1 : 0;
        if (lv > (P.ftLv || 0)) { P.ftLv = lv; sfx.glint(); tone(lv === 2 ? 330 : 220, 0.25, 0.08, 'sawtooth', 1.3); spawnFx('telegraph', P.x - P.face * 2, P.y - 34, P.face); if (typeof feelFlash === 'function') feelFlash(P.x, P.y - 20, 24 + 12 * lv, '255,190,120', 1, 0.12); }
        if (Math.random() < 0.25 + 0.2 * lv) particles.push({ x: P.x + rand(-9, 9), y: P.y - rand(0, 28), vx: 0, vy: -rand(20, 50), life: 0.4, kind: lv >= 2 ? 'fire' : 'spark' });
        if (mvHas(4) && peek('parry') && P.st > 0) { take('parry'); mvStart('ft_release', { lv }); return 'stop'; }
        if (!held.has('heavy') || P.mvT > 2500) {
          if (!lv) mvStart('ft_hammer', { t0: Math.min(P.mvT, 120) });
          else mvStart('ft_ifist', { lv, charged: true, mul: lv === 2 ? 2.6 / 1.8 : 1 });
          return 'stop';
        }
      } } },
  ft_ifist: { tags: ['ft_ifist', 'dg_heavy'], style: 'iron', iron: true, ironAll: true, kind: 'heavy', dmg: 1.8, poise: 60, stam: 20, wind: 160, total: 620, fin: true, lunge: 18, lungeLead: 160,
    poiseFn: () => (P.mvO && P.mvO.lv === 2 ? 90 : 60),
    on: { swing() { shake = Math.max(shake, P.mvO && P.mvO.lv === 2 ? 6 : 4); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 24, P.y - 18, 34, '255,200,140', 1.2, 0.1); } } },
  ft_throw: { tags: ['ft_throw', 'dg_heavy'], style: 'iron', iron: true, kind: 'heavy', dmg: 1.6, poise: 50, stam: 16, wind: 240, total: 800, fin: true, lunge: 10,
    on: { hit(t) { ftThrow(t); } } },
  ft_pillar: { tags: ['ft_pillar', 'dg_up'], style: 'iron', iron: true, kind: 'heavy', dmg: 1.4, poise: 50, stam: 16, wind: 300, total: 760, fin: true, launch: 260, ys: [-50, -2] },
  ft_heaven: { tags: ['ft_heaven', 'dg_up'], style: 'iron', iron: true, up: true, dmg: 1.3, poise: 40, stam: 14, wind: 300, total: 700, launch: 240 },
  ft_bash: { tags: ['ft_bash', 'dg_3'], style: 'iron', iron: true, ironAll: true, kind: 'heavy', dmg: 1.2, poise: 50, stam: 14, wind: 200, total: 560, fin: true, lunge: 30, lungeLead: 200, dash: true,
    on: { swing() { shake = Math.max(shake, 4); } } },
  // ---------------------------------------------------------------- SWITCHING
  ft_toiron: { tags: ['ft_toiron', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 0, wind: 300, total: 300, on: { start() { ftSetStyle('iron', true); } } },
  ft_toswift: { tags: ['ft_toswift', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 0, wind: 300, total: 300, on: { start() { ftSetStyle('swift', true); } } },
  // Shift strikes (x1.15 from the move they cancel; x1.3 + burn as an Ember shift)
  ft_fstar: { tags: ['ft_fstar', 'dg_heavy'], shiftStrike: true, style: 'iron', iron: true, kind: 'heavy', dmg: 1.4, poise: 50, stam: 14, wind: 260, total: 640, flow: 1, airOk: true, lunge: 12, ys: [-44, 0],
    on: { start() { ftSetStyle('iron', true); if (P.ground) { P.vy = -120; P.ground = false; } }, update() { if (P.mvT >= 170 && !P.ground) P.vy = Math.max(P.vy, 380); },
      swing() { shake = Math.max(shake, 4); spawnFx('dust', P.x + P.face * 14, P.y, P.face); } },
    next: { J: 'ft_elbow', K: q => (P.mvO && P.mvO.from === 'ft_hook' && mvHas(3) ? 'ft_tempest' : 'ft_hammer') } },
  ft_wind: { tags: ['ft_wind', 'dg_4'], shiftStrike: true, style: 'swift', hits: [0.28, 0.28, 0.28, 0.28], gap: 70, poise: 20, stam: 12, wind: 120, total: 520, flow: 1, lunge: 14,
    on: { start() { ftSetStyle('swift', true); } }, next: { J: 'ft_cross', K: 'ft_snap' } },
  // III: Swift J J J -> I -> K: out of the Falling star, a Swift flurry that ends in the Iron hammer fist
  ft_tempest: { tags: ['ft_tempest', 'dg_4'], rank: 3, style: 'iron', kind: 'heavy', hits: [0.3, 0.3, 0.3, 0.3, 1.0], gap: 90, poise: 60, stam: 18, wind: 100, total: 900, fin: true, lunge: 12,
    on: { start() { ftSetStyle('swift', true); }, hitStart(k) { if (k === 4) { ftSetStyle('iron', true); shake = Math.max(shake, 5); spawnFx('dust', P.x + P.face * 16, P.y, P.face); } } } },
  // IV: Iron hold K -> I: the charge let go as a Swift dash-punch through the foe (1.2 / 1.6 / 2.2 by level)
  ft_release: { tags: ['ft_release', 'dg_3'], rank: 4, style: 'swift', dmg: 1.2, poise: 30, stam: 10, wind: 90, total: 480, lunge: 46, lungeLead: 90, lungeTail: 60, dash: true, inv: [0, 140], fin: true,
    dmgFn: () => [1.2, 1.6, 2.2][(P.mvO && P.mvO.lv) || 0], poiseFn: () => [30, 45, 70][(P.mvO && P.mvO.lv) || 0],
    on: { start() { ftSetStyle('swift', true); mvAfterimage(FT_HEX.iron, 0.35, 0.5); }, update() { if (P.mvT < 200 && Math.random() < 0.7) mvAfterimage(FT_HEX.swift, 0.18, 0.3); } },
    next: { J: 'ft_cross' } },
  // V: hold I with 5 Flow (a tap still changes style)
  ft_ihold: { tags: ['ft_ember', 'parry'], loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt, A, ax, grav) {
      P.vx *= Math.pow(0.02, dt); grav();
      if (!held.has('parry')) { mvStart(ftIron() ? 'ft_toswift' : 'ft_toiron'); return 'stop'; }
      if (P.mvT >= FT_HOLD_I) { mvStart('ft_ember', { t0: FT_HOLD_I * 0.5 }); return 'stop'; }
    } } },
  ft_ember: { tags: ['ft_ember', 'dg_heavy'], rank: 5, kind: 'heavy', dmg: 3.0, poise: 120, stam: 0, wind: 380, total: 900, commit: true, fin: true, lunge: 16, flow: 0, armor: 0.3,
    can: () => (P.ftFlow || 0) >= FT_FLOW_MAX,
    on: { start() { P.ftFlow = 0; sfx.fire(); tone(196, 0.6, 0.1, 'sawtooth', 1.6); },
      swing() { shake = Math.max(shake, 7); flashScreen = Math.max(flashScreen, 0.12); sfx.boom(); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 22, P.y - 18, 48, '255,190,110', 1.4, 0.14);
        for (let i = 0; i < 18; i++) particles.push({ x: P.x + P.face * rand(14, 34), y: P.y - rand(8, 30), vx: P.face * rand(40, 160), vy: -rand(10, 80), life: rand(0.3, 0.6), kind: 'fire' }); },
      hit(t) { mvBurn(t, 4, D.light * 0.1); } } },
  // ---------------------------------------------------------------- AIR
  ft_akick: { tags: ['ft_akick', 'dg_air'], style: 'swift', air: true, dmg: 0.7, poise: 10, stam: 8, wind: 110, total: 300, fx: null, next: { J: ftUp(() => (P.ground ? '@J' : 'ft_akick3')) } },
  // the triple kick floats you (the fall held to 35 px/s) so all three land even from a short hop
  ft_akick3: { tags: ['ft_akick3', 'dg_air'], style: 'swift', air: true, hits: [0.3, 0.3, 0.4], gap: 80, poise: 15, stam: 10, wind: 100, total: 440, fx: null,
    move(dt, A, ax, grav) { if (P.ground) { P.vx *= Math.pow(0.0002, dt); grav(); return; } P.vx = approach(P.vx, ax * MAXV * 0.5, 500 * dt); grav(); if (P.mvT < A.mv.total - 60) P.vy = Math.min(P.vy, 35); } },
  ft_aelbow: { tags: ['ft_aelbow', 'dg_down'], style: 'iron', airCount: true, airOk: true, noHit: true, kind: 'heavy', dmg: 1.2, poise: 34, stam: 12, wind: 160, total: 560, diveEnd: 300, dvx: 150, dvy: 300, dreach: 18, dtop: 26, lreach: 26,
    on: { update: ftDiveUpdate }, move: ftDiveMove },
  ft_aheel: { tags: ['ft_aheel', 'dg_down'], airCount: true, airOk: true, noHit: true, kind: 'heavy', dmg: 1.3, poise: 50, stam: 14, wind: 150, total: 620, diveEnd: 320, dvx: 110, dvy: 430, dreach: 14, dtop: 14, lreach: 24,
    on: { update: ftDiveUpdate }, move: ftDiveMove },
  ft_astomp: { tags: ['ft_astomp', 'dg_down'], down: true, dmg: 0.8, poise: 12, stam: 8, wind: 100, total: 280 },
});
// every ground move of a style can be Shift-cancelled into the other style's linking blow (not the Shift strikes,
// the holds, the specials that already cross styles, the air moves)
for (const d of Object.values(MV.defs)) {
  if (d.type !== 'fist' || !d.style || d.shiftStrike || d.loop || d.air || d.airCount || d.down || ['ft_tempest', 'ft_release', 'ft_ember'].includes(d.id)) continue;
  d.shift = d.style === 'swift' ? 'ft_fstar' : 'ft_wind';
}
