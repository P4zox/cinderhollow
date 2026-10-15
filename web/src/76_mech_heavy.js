// ------------------------------------------------------------------ WM: Greatsword (A4) + Maul (A5)
// ================================================================== Greatsword: one huge hit at a time
// Hold K: level 1 (0-400 ms) 1.8 / 50, level 2 (400-800) 2.6 / 70, level 3 (800-1300) 3.6 / 95; past 1.3 s it overcharges
// back to level 2 (Mastery V: a fourth level, wrath, 4.2 + a flame burst). K within 0.5 s of a charged slash: the strong
// charged slash (x1.25, +4 stam); Mastery III: K after that = the true charged slash (1.5 + 4.5). Charging is
// flinch-proof against hits under 30% max HP (x0.8 damage). I = blade guard (1.2 x dmg stamina, 25% chip, no parry).
const GS_LV = { dmg: [0, 1.8, 2.6, 3.6, 4.2], poise: [0, 50, 70, 95, 110], stam: [0, 28, 32, 36, 40] };
function gsLevel(ms) { if (ms > 1300) return mvHas(5) ? 4 : 2; return ms >= 800 ? 3 : ms >= 400 ? 2 : 1; }
const GS_CHARGES = { gs_charge: 'gs_charged', gs_scharge: 'gs_strong', gs_tcharge: 'gs_true1' };
function gsChargeDef(tags, rel) {
  return { tags, kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: {
      start(A, o) { P.gsMs = o.bank || 0; P.gsLv = gsLevel(P.gsMs); },
      update(dt, A, ax) {
        P.vx *= Math.pow(0.05, dt);
        P.gsMs += dt * 1000; P.charge = P.gsMs / 1000;
        const lv = gsLevel(P.gsMs);
        if (lv !== P.gsLv) {   // each level rings in: brighter glint, a pip lights over the head
          if (lv > P.gsLv || lv === 4) { sfx.glint(); tone(660 + lv * 220, 0.25, 0.05, 'triangle', 1.3); if (typeof feelFlash === 'function') feelFlash(P.x, P.y - 34, 30 + lv * 10, GS_GLOW[lv], 1.1, 0.12); if (lv === 3) spawnFx('telegraph', P.x - P.face * 2, P.y - 36, P.face); }
          else { sfx.deny(); }   // overcharged: the glow gutters
          P.gsLv = lv;
        }
        if (peek('roll') && P.st > 0) {   // II: shoulder tackle keeps the charge; otherwise the roll drops it
          take('roll');
          if (mvHas(2) && P.ground) { mvStart('gs_tackle', { resume: A.mv.id, bank: P.gsMs }); return 'stop'; }
          mvDodgeStart(ax); return 'stop';
        }
        if (!held.has('heavy') || P.gsMs > 2200) { mvStart(P.mvO.roll ? 'gs_rollheavy' : lv === 4 && rel === 'gs_charged' ? 'gs_wrath' : rel, { lv, charged: lv >= 2, bank: P.gsMs }); return 'stop'; }
      },
    } };
}
const GS_GLOW = ['255,200,120', '255,190,110', '255,150,60', '255,245,215', '255,90,40'];
function gsReleaseDef(tags, mulFn, extra, wind, total, more = {}) {
  return { tags, kind: 'heavy', dmg: 1.8, poise: 50, wind, total, fin: true, fx: 'heavy', lunge: 16, slam: true, chainK: 500,
    stam: o => GS_LV.stam[o.lv || 1] + extra,
    dmgFn: () => GS_LV.dmg[P.mvLv || 1] * mulFn(), poiseFn: () => GS_LV.poise[P.mvLv || 1],
    on: { start() { if (P.mvLv === 4) { sfx.fire(); flashScreen = Math.max(flashScreen, 0.12); } },
          hit(t, info) { if (P.mvLv === 4 && !P.gsBurst) { P.gsBurst = true; mvShockwave({ r: 44, dmg: 0.4, poise: 20, fire: true, pk: 'fire', onHit: q => mvBurn(q, 5, D.light * 0.1) }); mvBurn(t, 5, D.light * 0.1); } },
          end() { P.gsBurst = false; } },
    ...more };
}
mvRegister('greatsword', {
  light: ['gs_1', 'gs_2', 'gs_3'], K: 'gs_charge', heavyTag: 'gs_charged', up: 'gs_up', air: 'gs_air', down: 'gs_down',
  plunge: { dmg: 1.8, poise: 90, stam: 20 },
  dodge: { stam: 18, total: 520, inv: 0.28, dist: 70, tags: ['roll'] },
  rollJ: 'gs_1',
  rollK(g) { return mvStart('gs_charge', { bank: 200, roll: true }); },   // L -> K: the rolling heavy banks 200 ms of charge
  onI(ax) {
    if (!P.ground || P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax;
    P.guardKind = 'gs'; P.guardT0 = P.clk; setP('guard', pHas('gs_guard') ? 'gs_guard' : 'parry', pHas('gs_guard'));
    if (!pHas('gs_guard')) { P.anim.i = 1; P.anim.speed = 0; }
    return true;
  },
  guardUpdate(dt, ax, grav) {
    if (P.guardKind !== 'gs') return false;
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (!P.ground) { setP('air', 'jump_fall'); return true; }
    if (P.state === 'block' && P.anim.done) { setP('guard', pHas('gs_guard') ? 'gs_guard' : 'parry', pHas('gs_guard')); if (!pHas('gs_guard')) { P.anim.i = 1; P.anim.speed = 0; } }
    if (peek('heavy') && P.st > 0) { take('heavy'); if (mvHas(4)) mvStart('gs_tackle', { resume: 'gs_charge', bank: 400, guard: true }); else mvStart('gs_charge'); return true; }   // IV: guard tackle
    if (peek('attack') && P.st > 0) { take('attack'); mvStartLight(); return true; }
    if (peek('roll') && P.st > 0) { take('roll'); mvDodgeStart(ax); return true; }
    if (P.state === 'guard' && !held.has('parry')) { P.guardKind = null; setP('idle', 'idle', true); return true; }
    return true;
  },
  blockPose() { setP('block', pHas('gs_guard') ? 'gs_guard' : 'parry', false); P.anim.i = Math.min(1, P.anim.n - 1); P.anim.speed = 0.6; },
  guardCost(dmg) { return { cost: 1.2 * dmg * (charmOn('c_aegis') ? 0.7 : 1), chip: 0.25 * dmg, push: 150, counterT: 0 }; },
  hurt(c) {
    const A = ATK[P.state];
    if (A && A.mv && A.mv.charge && c.dmg < D.maxHp * 0.3) { c.armor = true; c.dmg *= 0.8; }   // flinch-proof charge
  },
  interrupted() { P.guardKind = null; },
  render() {
    const A = ATK[P.state]; if (!A || !A.mv || !A.mv.charge) return;
    // the charge glow: dim ember (1), orange (2), white-gold (3), red wrath (4); flickers when overcharged
    const lv = P.gsLv || 1, over = P.gsMs > 1300 && lv !== 4, fl = over ? 0.5 + 0.5 * Math.sin(P.clk * 40) : 1;
    addLight(P.x - P.face * 4, P.y - 26, 18 + lv * 10, GS_GLOW[lv], (0.45 + lv * 0.18) * fl);
    if (Math.random() < 0.25 + lv * 0.15) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(4, 34), vx: 0, vy: -rand(20, 60), life: 0.4, kind: lv >= 4 ? 'fire' : lv >= 3 ? 'gold' : 'ember' });
    for (let i = 1; i <= 3; i++) {   // three pips over the head
      g.fillStyle = i <= Math.min(3, lv) ? `rgba(${GS_GLOW[Math.min(lv, 4)]},${0.9 * fl})` : 'rgba(40,34,44,0.7)';
      g.fillRect(Math.round(P.x - 7 + (i - 1) * 6), Math.round(P.y - 40), 3, 3);
    }
  },
  unlocks: [
    { rank: 2, id: 'gs_tackle', name: 'Shoulder tackle', input: 'L while charging', desc: "A 300 ms tackle (0.6 dmg, 40 poise). You can't be flinched, take 60% less damage, and keep your charge level." },
    { rank: 3, id: 'gs_true1', name: 'True Charged Slash', input: 'K after a strong charged slash', desc: 'A two-part slash: 1.5 + 4.5 at full charge.' },
    { rank: 4, id: 'gs_guardtackle', name: 'Guard tackle', input: 'block → K', desc: 'Tackle out of a block straight into a level 2 charge.' },
    { rank: 5, id: 'gs_wrath', name: 'Wrath charge', input: 'hold past level 3', desc: 'A fourth level replaces the overcharge: 4.2 + a flame burst + burn.' },
  ],
}, {
  gs_1: { tags: ['gs_1'], dmg: 1.3, poise: 32, stam: 20, wind: 300, total: 700, step: 0, fx: 'heavy', lunge: 14, next: { J: 'gs_2' } },
  gs_2: { tags: ['gs_2'], dmg: 1.35, poise: 32, stam: 20, wind: 300, total: 700, step: 1, box: [-22, 44, -42, 0], fx: 'slash_up', next: { J: 'gs_3' } },
  gs_3: { tags: ['gs_3'], dmg: 1.6, poise: 45, stam: 22, wind: 320, total: 760, step: 2, fin: true, launch: 180, fx: 'slash3' },
  gs_charge: gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_charged'),
  gs_charged: gsReleaseDef(['gs_charged', 'gs_heavy'], () => 1, 0, 200, 500, { next: { K: 'gs_scharge' } }),
  gs_wrath: gsReleaseDef(['gs_wrath', 'gs_charged', 'gs_heavy'], () => 1, 0, 220, 640, { rank: 5, next: { K: 'gs_scharge' } }),
  gs_rollheavy: gsReleaseDef(['gs_rollheavy', 'gs_charged', 'gs_heavy'], () => 1, 0, 220, 600, { next: { K: 'gs_scharge' } }),
  gs_scharge: gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_strong'),
  gs_strong: gsReleaseDef(['gs_strong', 'gs_heavy'], () => 1.25, 4, 220, 560, { next: { K: q => (mvHas(3) ? 'gs_tcharge' : '@K') } }),
  gs_tcharge: { ...gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_true1'), rank: 3 },
  gs_true1: { tags: ['gs_true1', 'gs_heavy'], kind: 'heavy', rank: 3, dmg: 1.5, poise: 40, wind: 220, total: 420, fx: 'heavy', lunge: 20, stam: o => GS_LV.stam[o.lv || 1] + 8,
    on: { end() { const lv = P.mvLv; mvStart('gs_true2', { lv, cost: 0, charged: true }); } } },
  gs_true2: { tags: ['gs_true2', 'gs_heavy'], kind: 'heavy', rank: 3, dmg: 4.5, poise: 95, stam: 0, wind: 250, total: 700, fin: true, slam: true, fx: 'heavy', lunge: 24,
    dmgFn: () => 4.5 * GS_LV.dmg[Math.min(3, P.mvLv || 3)] / 3.6, poiseFn: () => GS_LV.poise[Math.min(3, P.mvLv || 3)] * 1.2 },
  gs_tackle: { tags: ['gs_tackle', 'sh_heavy', 'gs_1'], rank: 2, dmg: 0.6, poise: 40, stam: 10, wind: 120, total: 300, lunge: 40, lungeLead: 120, armor: true, dmgTaken: 0.4, box: [-2, 26, -32, -2],
    can: o => !o.guard || mvHas(4),
    on: { end(A) { const o = P.mvO; if (held.has('heavy')) mvStart(o.resume || 'gs_charge', { bank: o.bank }); else mvStart(GS_CHARGES[o.resume] || 'gs_charged', { lv: gsLevel(o.bank || 0), charged: true }); } } },
  gs_air: { tags: ['gs_air'], air: true, hang: true, dmg: 1.3, poise: 40, stam: 16, wind: 220, total: 560 },
  gs_up: { tags: ['gs_up'], up: true, dmg: 1.2, poise: 35, stam: 16, wind: 240, total: 560 },
  gs_down: { tags: ['gs_down'], down: true, dmg: 1.1, poise: 45, stam: 12, wind: 140, total: 390, box: [-16, 18, -16, 26] },
});

// ================================================================== Maul: the stunner
// Hold K to walk-charge at 60% speed: under 450 ms = charged upswing, 450-900 = double smash, over 900 released = big
// smash, kept held = spinning bludgeon (release = spin finisher). Maul hits fill stance x1.6 (x1.2 more high on the body).
// I = brace (600 ms: no flinch, half damage). Mastery: charge step (II), Big Bang (III), steered spin (IV), earthshaker (V).
function mlLevel(ms) { return ms >= 900 ? 3 : ms >= 450 ? 2 : 1; }
const ML_GLOW = ['255,200,120', '255,190,110', '255,150,60', '255,245,215'];
function mlStunFx(t) {
  if (!t || !t.boss || t._mlSt === t.state) { if (t) t._mlSt = t.state; return; }
  if (t.state === 'stagger') {   // the knockdown: the stun bar broke on a maul blow
    popups.push({ x: t.x, y: t.y - 60, v: 'STUNNED', color: '#ffd070', life: 1.1 });
    shake = Math.max(shake, 8); hitstop = Math.max(hitstop, 0.12); sfx.boom(); tone(220, 0.4, 0.08, 'square', 0.6);
    for (let i = 0; i < 5; i++) { const a = i / 5 * 6.283; particles.push({ x: t.x + Math.cos(a) * 10, y: t.y - 54, vx: Math.cos(a) * 20, vy: Math.sin(a) * 8, life: 1.0, kind: 'gold' }); }
  }
  t._mlSt = t.state;
}
mvRegister('maul', {
  light: ['ml_1', 'ml_2', 'ml_3'], K: 'ml_charge', heavyTag: 'ml_upswing', up: 'ml_up', air: 'ml_air', down: 'ml_down',
  plunge: { dmg: 1.8, poise: 100, stam: 20, shock: { r: 46, dmg: 0.4, poise: 30 } },
  dodge: { stam: 16, total: 460, inv: 0.28, dist: 72, tags: ['roll'] },
  rollJ: 'ml_rollswing',
  // II: after a charge step the charge picks up where it was if K is still held
  dodgeUpdate(dt, g) { if (g.t >= g.total && g.bank !== undefined && held.has('heavy') && P.ground) { P.dg = null; mvStart('ml_charge', { bank: g.bank }); return true; } },
  onI(ax) {
    if (!P.ground || P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax; spend(15);
    P.braceT = 0; setP('brace', pHas('ml_brace') ? 'ml_brace' : 'sh_guard', false);
    sfx.block(); return true;
  },
  hurt(c) {
    if (P.state === 'brace' && P.braceT <= 0.6 && !c.negate) {   // brace: the blow lands but can't move you
      c.armor = true; spend(0.5 * c.dmg); c.dmg *= 0.5; P.braceHit = 0.25;   // 15 on raising it + 0.5 x dmg per blow
      sfx.block(); shake = Math.max(shake, 3); spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 10, P.y - 18, P.face);
    }
  },
  poiseMod(t, poise, A, y) {   // the stun: x1.6, and x1.2 more on the upper half of the body
    if (!t || t.prop) return poise;
    const hb = t.hurtbox && t.hurtbox(); const high = hb && y < (hb.y0 + hb.y1) / 2;
    return poise * (A && A.mv && A.mv.stun || 1.6) * (high ? 1.2 : 1);
  },
  onHit(t) { mlStunFx(t); },
  interrupted() {},
  render() {
    const A = ATK[P.state];
    if (P.state === 'ml_charge') {
      const lv = mlLevel(P.mlMs || 0);
      addLight(P.x + P.face * 4, P.y - 30, 18 + lv * 9, ML_GLOW[lv], 0.45 + lv * 0.18);
      if (Math.random() < 0.2 + lv * 0.15) particles.push({ x: P.x + P.face * rand(-4, 12), y: P.y - rand(20, 38), vx: 0, vy: -rand(20, 50), life: 0.4, kind: lv >= 3 ? 'gold' : 'ember' });
      for (let i = 1; i <= 3; i++) { g.fillStyle = i <= lv ? `rgba(${ML_GLOW[lv]},0.9)` : 'rgba(40,34,44,0.7)'; g.fillRect(Math.round(P.x - 7 + (i - 1) * 6), Math.round(P.y - 40), 3, 3); }
    }
    if (P.state === 'brace') addLight(P.x + P.face * 6, P.y - 16, 22, '255,220,170', P.braceHit > 0 ? 1 : 0.45);
    if (A && A.mv && A.mv.id === 'ml_spin') addLight(P.x, P.y - 16, 30, '255,190,110', 0.6);
  },
  unlocks: [
    { rank: 2, id: 'ml_chargestep', name: 'Charge step', input: 'L while charging', desc: 'Roll without losing the charge.' },
    { rank: 3, id: 'ml_bb1', name: 'Big Bang', input: 'J J J → K → K → K → K', desc: 'A timed 4-hit chain: 1.0, 1.0, 1.2, 3.0 (stun ×2).' },
    { rank: 4, id: 'ml_steer', name: 'Steered spin', input: 'while spinning', desc: 'Steer the spin; each spin does 0.6.' },
    { rank: 5, id: 'ml_quake', name: 'Earthshaker', input: 'hold level 3 for 1.4 s', desc: 'The overcharge sends out a 64 px shockwave: 1.5 dmg, +100 stun.' },
  ],
}, {
  ml_1: { tags: ['ml_1', 'gs_1'], dmg: 1.2, poise: 40, stam: 18, wind: 260, total: 620, step: 0, reach: 34, fx: 'heavy', next: { J: 'ml_2' } },
  ml_2: { tags: ['ml_2', 'gs_2'], dmg: 1.25, poise: 40, stam: 18, wind: 260, total: 620, step: 1, reach: 34, fx: 'heavy', next: { J: 'ml_3' } },
  ml_3: { tags: ['ml_3', 'gs_3'], dmg: 1.6, poise: 70, stam: 22, wind: 300, total: 720, step: 2, reach: 34, fin: true, launch: 200, fx: 'slash_up', next: { K: q => (mvHas(3) ? 'ml_bb1' : '@K') } },
  ml_charge: { tags: ['ml_charge_walk', 'ml_charge_idle', 'gs_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    move(dt, A, ax) {},
    on: {
      start(A, o) { P.mlMs = o.bank || 0; P.mlLv = mlLevel(P.mlMs); },
      update(dt, A, ax, grav) {
        // walk while charging (60%)
        P.vx = approach(P.vx, ax * MAXV * 0.6, 900 * dt); if (ax) P.face = ax; grav();
        const want = ax && pHas('ml_charge_walk') ? 'ml_charge_walk' : pHas('ml_charge_idle') ? 'ml_charge_idle' : null;
        if (want && P.anim.tag !== want) P.anim.set(want, true, 1);
        if (!want) { const R = A._r; P.anim.i = Math.max(0, R.act[0] - 1); P.anim.t = 0; P.anim.speed = 0; }
        P.mlMs += dt * 1000; P.charge = P.mlMs / 1000;
        const lv = mlLevel(P.mlMs);
        if (lv !== P.mlLv) { P.mlLv = lv; sfx.glint(); tone(520 + lv * 180, 0.22, 0.05, 'triangle', 1.2); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 6, P.y - 34, 28 + lv * 8, ML_GLOW[lv], 1, 0.12); }
        if (peek('roll') && P.st > 0) {   // the roll drops the charge, unless Mastery II
          take('roll'); const bank = P.mlMs; mvDodgeStart(ax); if (mvHas(2) && P.dg) P.dg.bank = bank; return 'stop';
        }
        if (!P.ground) { setP('air', 'jump_fall'); return 'stop'; }
        // level 3 kept held: the spin (or, Mastery V standing still, the earthshaker at 1.4 s)
        if (held.has('heavy') && mvHas(5) && !ax && P.mlMs >= 1400) { mvStart('ml_quake', { quake: true }); return 'stop'; }
        if (held.has('heavy') && P.mlMs >= 1300 && (ax || !mvHas(5))) { mvStart('ml_spin'); return 'stop'; }
        if (!held.has('heavy')) { mvStart(lv === 1 ? 'ml_upswing' : lv === 2 ? 'ml_double' : 'ml_bigsmash', { charged: lv >= 2 }); return 'stop'; }
      },
    } },
  ml_upswing: { tags: ['ml_upswing', 'gs_3'], kind: 'heavy', dmg: 1.6, poise: 60, stam: 24, wind: 200, total: 520, reach: 36, launch: 200, fx: 'slash_up' },
  ml_double: { tags: ['ml_double', 'gs_1'], kind: 'heavy', hits: [1.2, 1.2], gap: 360, poise: 110, stam: 28, wind: 180, total: 900, reach: 36, fin: true, slam: true, fx: 'heavy', fxEach: true },
  ml_bigsmash: { tags: ['ml_bigsmash', 'gs_heavy'], kind: 'heavy', dmg: 3.0, poise: 90, stam: 32, wind: 300, total: 750, reach: 38, fin: true, slam: true, fx: 'heavy',
    on: { swing() { if (P.mvO.quake) { mvShockwave({ r: 64, dmg: 1.5, poise: 100, shake: 10 }); spawnFx('ground_crack', P.x - 30, P.y, -1); spawnFx('ground_crack', P.x + 30, P.y, 1); flashScreen = Math.max(flashScreen, 0.12); } } } },
  ml_quake: { tags: ['ml_quake', 'ml_bigsmash', 'gs_heavy'], kind: 'heavy', rank: 5, dmg: 3.0, poise: 90, stam: 32, wind: 300, total: 750, reach: 40, fin: true, slam: true, fx: 'heavy',
    on: { swing() { mvShockwave({ r: 64, dmg: 1.5, poise: 100, shake: 10 }); spawnFx('ground_crack', P.x - 30, P.y, -1); spawnFx('ground_crack', P.x + 30, P.y, 1); flashScreen = Math.max(flashScreen, 0.12); } } },
  ml_spin: { tags: ['ml_spin', 'gs_3'], kind: 'heavy', loop: true, dmg: 0.5, poise: 20, stam: 32, wind: 1e9, total: 1e9, spin: true, reach: 34, noHit: true,
    on: {
      start() { P.mlSpin = 0; P.mlSpinT = 0; },
      update(dt, A, ax, grav) {
        const steer = mvHas(4);
        P.vx = steer ? approach(P.vx, ax * MAXV * 0.7, 700 * dt) : P.face * 40; if (steer && ax) P.face = ax; grav();
        P.mlSpinT += dt * 1000;
        if (P.mlSpinT >= 320) {   // one revolution: one hit both sides
          P.mlSpinT -= 320; P.mlSpin++; P.hitSet = new Set(); P.mvHitK = 0;
          mvStrikeAt(mvRect(A), steer ? 0.6 : 0.5, 20, { A, kind: 'heavy' }); sfx.heavySwing();
          for (const t of targets()) mlStunFx(t);
        }
        if (!held.has('heavy') || P.mlSpin >= 4 || !P.ground) { mvStart('ml_spin_end'); return 'stop'; }
      },
    } },
  ml_spin_end: { tags: ['ml_spin_end', 'gs_heavy'], kind: 'heavy', dmg: 2.0, poise: 90, stam: 0, wind: 200, total: 500, reach: 38, fin: true, slam: true, fx: 'heavy' },
  ml_rollswing: { tags: ['ml_rollswing', 'gs_1'], dmg: 1.3, poise: 35, stam: 16, wind: 200, total: 560, reach: 36, fx: 'heavy' },
  ml_bb1: { tags: ['ml_bb1', 'gs_1'], rank: 3, dmg: 1.0, poise: 40, stam: 14, wind: 220, total: 520, reach: 36, fx: 'heavy', next: { K: 'ml_bb2' } },
  ml_bb2: { tags: ['ml_bb2', 'gs_2'], rank: 3, dmg: 1.0, poise: 40, stam: 14, wind: 220, total: 520, reach: 36, fx: 'heavy', next: { K: 'ml_bb3' } },
  ml_bb3: { tags: ['ml_bb3', 'gs_3'], rank: 3, dmg: 1.2, poise: 50, stam: 16, wind: 240, total: 560, reach: 36, fx: 'slash_up', next: { K: 'ml_bb4' } },
  ml_bb4: { tags: ['ml_bb4', 'gs_heavy'], rank: 3, kind: 'heavy', dmg: 3.0, poise: 90, stam: 24, wind: 360, total: 900, reach: 40, fin: true, slam: true, stun: 2, fx: 'heavy' },
  ml_air: { tags: ['ml_air', 'gs_air'], air: true, dmg: 1.2, poise: 30, stam: 16, wind: 200, total: 520, spin: true },
  ml_up: { tags: ['ml_up', 'gs_up'], up: true, dmg: 1.1, poise: 30, stam: 14, wind: 220, total: 520 },
  ml_down: { tags: ['ml_down', 'gs_down'], down: true, dmg: 1.0, poise: 50, stam: 12, wind: 140, total: 380, box: [-14, 16, -16, 26],
    on: { hit() { P.vy = -330; } } },   // the big bounce
});
// the brace (I): 600 ms window, then a short recovery
MV_STATES.brace = (dt, ax, grav) => {
  P.braceT = (P.braceT || 0) + dt; P.braceHit = (P.braceHit || 0) - dt;
  P.vx = approach(P.vx, 0, 900 * dt); grav();
  if (P.braceT >= 0.75) setP('idle', 'idle', true);
};
