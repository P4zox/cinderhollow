// ------------------------------------------------------------------ WM: Sword & Shield (A6) + Spear (A8)
// ================================================================== Sword & Shield: safe and versatile
// Hold I to block (6 + 0.8 x dmg stamina, no chip), tap I to parry; I -> J guard counter. L is a backhop that leads into
// the leaping slash. Flasks with the weapon out: 30% faster, and you can walk. Mastery: perfect rush (II), shield slam
// (III), falling bash (IV), perfect guard (V).
mvRegister('sns', {
  light: ['sh_1', 'sh_2', 'sh_3', 'sh_4'], K: 'sh_heavy', up: 'sh_up', air: 'sh_air', down: 'sh_down',
  // IV: the falling bash replaces the plunge (air K; air down+K too while the Cinder Slam isn't yours -- that input is the slam's)
  plunge: () => (mvHas(4) ? { dmg: 1.6, poise: 80, stam: 16, pk: 'spark', bash: true, fallTag: 'sh_fallbash' } : { dmg: 1.4, poise: 70, stam: 16 }),
  dodge: { stam: 12, total: 300, inv: 0.14, dist: 44, back: true, hop: 120, tags: ['sh_backhop', 'jump_up'], keepTag: true, ghost: false },
  rollJ: g => (g.kind === 'roll' ? 'sh_leap' : null),
  counter: () => 'sh_counter',
  healSpeed: 1.3, healWalk: 0.3,
  guardK() { if (mvHas(3) && P.ground) return mvStart('sh_slam'); return false; },   // III: block -> K
  guardCost(dmg) {
    const perfect = mvHas(5) && P.clk - (P.guardT0 ?? -9) <= 0.1;
    return { cost: perfect ? 0 : (6 + dmg * 0.8) * (charmOn('c_aegis') ? 0.7 : 1), chip: 0, push: perfect ? 20 : 70, counterT: 0.6, perfect };
  },
  blocked(dmg, dir, opt, G, id) {
    if (!G.perfect) return;
    // V: perfect guard -- no stamina, projectiles fly back, the next counter deals +50%
    P.counterBonus = 1.5; sfx.glint(); flashScreen = Math.max(flashScreen, 0.1);
    if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 12, P.y - 18, 44, '255,245,215', 1.4, 0.14);
    const pr = projectiles.find(p => p.id === id && p.owner !== 'player');
    if (pr) { pr.owner = 'player'; pr.vx = -pr.vx; pr.vy = -(pr.vy || 0) * 0.5; pr.hits = new Set(); pr.face = -(pr.face || 1); pr.life = Math.max(pr.life, 0.8); }
  },
  onI(ax) {   // tap = parry (window 170 ms), hold = guard (04_player: startParry / updateGuard)
    if (!P.ground || P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax; startParry(); return true;
  },
  render() {
    // II: the perfect-rush flash -- the moment to press for a stronger next hit
    const A = ATK[P.state];
    if (mvHas(2) && A && A.mv && (A.mv.id === 'sh_1' || A.mv.id === 'sh_2') && P.mvT >= A.mv.total - 150) { addLight(P.x + P.face * 10, P.y - 22, 20, '255,240,200', 0.9); if (!P.shFlashed) { P.shFlashed = true; mvSpark(P.x + P.face * 12, P.y - 22, 4, '255,240,200', 90); } }
    else P.shFlashed = false;
    if ((P.state === 'guard' || P.state === 'block') && mvHas(5) && P.clk - (P.guardT0 ?? -9) <= 0.1) addLight(P.x + P.face * 10, P.y - 18, 22, '255,245,215', 0.8);
  },
  unlocks: [
    { rank: 2, id: 'sh_prush', name: 'Perfect rush', input: 'J J K, each press on the flash', desc: 'Each timed hit is stronger: 1.0, 1.2, 2.0.' },
    { rank: 3, id: 'sh_slam', name: 'Shield slam', input: 'block → K', desc: 'A 1.6 slam with 110 poise.' },
    { rank: 4, id: 'sh_fallbash', name: 'Falling bash', input: 'air ↓K', desc: 'A 1.6 plunge with 80 poise that also pogos.' },
    { rank: 5, id: 'sh_pguard', name: 'Perfect guard', input: 'block within the last 100 ms', desc: 'Reflects projectiles, takes no stamina, and the next counter deals +50%.' },
  ],
}, {
  sh_1: { tags: ['sh_1'], dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 320, step: 0, fx: 'slash', next: { J: 'sh_2' } },
  sh_2: { tags: ['sh_2'], dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 320, step: 1, fx: 'slash2',
    on: { start(A, o) { P.shRush = mvHas(2) && !!o.perfect; if (P.shRush) P.mvMul = 1.2 / 0.85; } },
    next: { J: 'sh_3', K: q => (mvHas(2) && P.shRush && mvPerfect(q, ATK.sh_2) ? 'sh_prush' : '@K') } },
  sh_3: { tags: ['sh_3'], dmg: 0.9, poise: 12, stam: 10, wind: 140, total: 340, step: 2, fx: 'slash_air', next: { J: 'sh_4' } },
  sh_4: { tags: ['sh_4', 'sh_heavy'], dmg: 1.4, poise: 55, stam: 14, wind: 220, total: 560, step: 3, fin: true, reel: true, lunge: 20, box: [-2, 30, -30, -2] },
  sh_heavy: { tags: ['sh_heavy'], kind: 'heavy', dmg: 1.2, poise: 60, stam: 16, wind: 200, total: 520, reel: true, lunge: 24, box: [-2, 30, -30, -2],
    on: { update() { if (P.mvT >= 120 && P.mvT < 170 && held.has('heavy') && !P.mvO.noHold) { mvStart('sh_rush_hold', { cost: 0 }); return 'stop'; } } } },
  sh_rush_hold: { tags: ['sh_rush_hold', 'sh_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000;
      if (P.mvT >= 230 && !P.shFull) { P.shFull = true; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); }
      if (!held.has('heavy') || P.mvT > 1800) { const f = P.shFull; P.shFull = false; if (f) mvStart('sh_rush', { cost: 8, charged: true }); else mvStart('sh_heavy', { cost: 0, t0: 120, noHold: true }); return 'stop'; }
    }, start() { P.shFull = false; } } },
  sh_rush: { tags: ['sh_rush', 'sh_heavy'], kind: 'heavy', dmg: 1.8, poise: 90, stam: 24, wind: 220, total: 450, lunge: 70, lungeLead: 200, lungeTail: 60, reel: true, fin: true, box: [-2, 32, -32, -2], armor: 0.3 },
  sh_prush: { tags: ['sh_heavy'], kind: 'heavy', rank: 2, dmg: 2.0, poise: 70, stam: 16, wind: 200, total: 520, reel: true, fin: true, lunge: 30, box: [-2, 32, -32, -2],
    on: { start() { if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 14, P.y - 20, 40, '255,240,200', 1.2, 0.14); sfx.glint(); } } },
  sh_counter: { tags: ['sh_counter'], dmg: 1.9, poise: 45, stam: 10, wind: 200, total: 520, counter: true, fin: true, lunge: 26, fx: 'slash_air' },
  sh_slam: { tags: ['sh_slam', 'sh_heavy'], kind: 'heavy', rank: 3, dmg: 1.6, poise: 110, stam: 18, wind: 260, total: 620, reel: true, fin: true, slam: true, box: [-2, 32, -32, 0] },
  sh_leap: { tags: ['sh_leap', 'sh_counter', 'attack4'], dmg: 1.8, poise: 40, stam: 16, wind: 320, total: 700, fin: true, lunge: 64, lungeLead: 300, fx: 'heavy',
    on: { start() { if (P.ground) { P.vy = -150; P.ground = false; } } }, airOk: true },
  sh_air: { tags: ['sh_air'], air: true, dmg: 0.85, poise: 10, stam: 9, wind: 120, total: 300 },
  sh_up: { tags: ['sh_up'], up: true, dmg: 0.9, poise: 20, stam: 10, wind: 150, total: 340 },
  sh_down: { tags: ['sh_down'], down: true, dmg: 0.9, poise: 20, stam: 10, wind: 100, total: 300, box: [-18, 18, -16, 24] },
});

// ================================================================== Spear: the walking wall
// Hold I: the heavy guard (5 + 0.5 x dmg, big hits chip 10%, hard pushback, walk slowly). I + J: guard poke; block -> K:
// counter-thrust. L is a hop (chain 2; 3 at Mastery II). Hold K while moving: charge dash. Mastery: triple hop (II),
// charged counter (III), power guard (IV), thunder charge (V).
function spGuardTag(moving) { return moving && pHas('sp_guard_walk') ? 'sp_guard_walk' : pHas('sp_guard') ? 'sp_guard' : 'parry'; }
function spEnterGuard() {
  P.guardKind = 'spear'; P.guardT0 = P.clk;
  const t = spGuardTag(false); setP('guard', t, t !== 'parry'); if (t === 'parry') { P.anim.i = 1; P.anim.speed = 0; }
}
mvRegister('spear', {
  light: ['sp_1', 'sp_2', 'sp_3'], K: 'sp_heavy', up: 'sp_up', air: 'sp_air', down: 'sp_down',
  plunge: { dmg: 1.5, poise: 70, stam: 18 },
  dodge: () => ({ stam: 8, total: 260, inv: 0.14, dist: 40, hop: 90, hopDir: true, chain: mvHas(2) ? 3 : 2, kind: 'hop', tags: ['sp_hop', 'jump_up'], keepTag: true, ghost: false }),
  rollJ() {   // a hop -> J continues the poke chain where it left off
    const c = P.spChain; if (c && P.clk - c.t < 1.2) { const A = ATK[c.id]; const nx = A && A.mv.next && A.mv.next.J; if (nx) return nx; }
    return 'sp_hpoke';
  },
  counter: () => null,
  airRise() { if (!pHas('sp_jump')) return false; startSpDive(); return true; },
  onK(ax) { if (ax) return mvStart('sp_cwind'); return mvStart('sp_heavy'); },
  onI(ax) { if (!P.ground || P.st <= 0) return false; take('parry'); if (ax) P.face = ax; spEnterGuard(); return true; },
  started(A) { if (A.mv.step !== undefined) P.spChain = { id: A.mv.id, t: P.clk }; },
  guardUpdate(dt, ax, grav) {
    if (P.guardKind !== 'spear') return false;
    // walk slowly behind the guard; turning is slow (only when stopped)
    P.vx = approach(P.vx, ax * MAXV * 0.32, 700 * dt); grav();
    if (!P.ground) { P.guardKind = null; setP('air', 'jump_fall'); return true; }
    if (P.state === 'block' && P.anim.done) spEnterGuard();
    if (P.state === 'guard') { const t = spGuardTag(!!ax); if (P.anim.tag !== t && t !== 'parry') P.anim.set(t, true); }
    if (P.spPower > 0) { P.spPower -= dt; addLight(P.x + P.face * 10, P.y - 18, 26, '200,220,255', 0.7); }
    if (peek('attack') && P.st > 0) { take('attack'); mvStart('sp_gpoke'); return true; }   // I + J: the guard stays up after
    if (peek('heavy') && P.st > 0) {
      take('heavy');
      if (P.gcT > 0) { mvStart('sp_counter'); return true; }   // block -> K (III: hold for the charged counter)
      if (mvHas(4)) { P.spPower = 1; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); return true; }   // IV: power guard (I + K)
      P.guardKind = null; mvStart('sp_heavy'); return true;
    }
    if (peek('roll') && P.st > 0) { take('roll'); P.guardKind = null; mvDodgeStart(ax); return true; }
    if (P.state === 'guard' && !held.has('parry')) { P.guardKind = null; P.spPower = 0; setP('idle', 'idle', true); return true; }
    return true;
  },
  blockPose() { setP('block', pHas('sp_pguard') && P.spPower > 0 ? 'sp_pguard' : spGuardTag(false), false); if (!pHas('sp_guard')) { P.anim.i = 1; P.anim.speed = 0.6; } },
  guardCost(dmg) {
    const pw = P.spPower > 0;
    return { cost: (5 + 0.5 * dmg) * (pw ? 1.5 : 1) * (charmOn('c_aegis') ? 0.7 : 1), chip: !pw && dmg > D.maxHp * 0.3 ? 0.1 * dmg : 0, push: pw ? 0 : 260, counterT: 0.5 };
  },
  interrupted() { P.guardKind = null; P.spPower = 0; },
  render() {
    if (P.state === 'sp_run') { addLight(P.x + P.face * 20, P.y - 16, 22, mvHas(5) ? '170,200,255' : '255,220,170', 0.6); if (Math.random() < 0.6) particles.push({ x: P.x - P.face * rand(0, 10), y: P.y - rand(2, 6), vx: -P.face * 40, vy: -rand(10, 30), life: 0.3, kind: 'dust' }); }
    if (P.state === 'sp_cwind') { const f = clamp(P.mvT / 400, 0, 1); addLight(P.x + P.face * 16, P.y - 18, 12 + 16 * f, '255,220,170', 0.3 + 0.5 * f); }
  },
  unlocks: [
    { rank: 2, id: 'sp_triplehop', name: 'Triple hop', input: 'L L L', desc: 'Chain three hops.' },
    { rank: 3, id: 'sp_ccounter', name: 'Charged counter', input: 'block → hold K', desc: 'A 3.0 counter-thrust with 90 poise.' },
    { rank: 4, id: 'sp_pguard', name: 'Power guard', input: 'I + K', desc: 'For 1 s: no pushback and no chip from anything; stamina cost ×1.5.' },
    { rank: 5, id: 'sp_thunder', name: 'Thunder charge', input: 'charge dash', desc: 'The dash pierces with lightning (+0.5 per hit) and the finisher deals 3.0.' },
  ],
}, {
  sp_1: { tags: ['sp_1'], dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 380, step: 0, reach: MV_SR * 1.5, fx: 'slash_air', next: { J: 'sp_2' } },
  sp_2: { tags: ['sp_2'], dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 380, step: 1, reach: MV_SR * 1.5, fx: 'slash_air', next: { J: 'sp_3' } },
  sp_3: { tags: ['sp_3'], dmg: 1.15, poise: 18, stam: 12, wind: 160, total: 420, step: 2, reach: MV_SR * 1.5, fin: true, fx: 'slash3' },
  sp_heavy: { tags: ['sp_high', 'sp_heavy'], kind: 'heavy', dmg: 1.4, poise: 35, stam: 18, wind: 260, total: 600, box: [-4, MV_SR * 1.3, -64, -6], fx: 'slash_up' },
  sp_gpoke: { tags: ['sp_gpoke', 'sp_1'], guarding: true, dmg: 0.9, poise: 12, stam: 10, wind: 140, total: 380, reach: MV_SR * 1.5,
    on: { end() { if (held.has('parry') && P.ground) spEnterGuard(); } } },
  sp_counter: { tags: ['sp_counter', 'sp_heavy'], dmg: 2.0, poise: 60, stam: 14, wind: 160, total: 520, counter: true, fin: true, reach: MV_SR * 1.5, lunge: 24, fx: 'slash3',
    on: { update() { if (mvHas(3) && P.mvT >= 100 && P.mvT < 140 && held.has('heavy')) { mvStart('sp_ccounter', { cost: 0 }); return 'stop'; } } } },
  sp_ccounter: { tags: ['sp_ccounter', 'sp_heavy'], rank: 3, kind: 'heavy', dmg: 3.0, poise: 90, stam: 6, wind: 360, total: 800, counter: true, fin: true, reach: MV_SR * 1.6, lunge: 36, fx: 'slash3' },
  sp_cwind: { tags: ['sp_charge_wind', 'sp_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.02, dt);
      if (!held.has('heavy')) { mvStart('sp_heavy'); return 'stop'; }
      if (peek('parry')) { take('parry'); setP('idle', 'idle', true); return 'stop'; }
      if (P.mvT >= 400) { mvStart('sp_run'); return 'stop'; }
    } } },
  sp_run: { tags: ['sp_charge_run', 'sp_1'], kind: 'heavy', loop: true, noHit: true, dmg: 0.4, poise: 15, stam: 0, wind: 1e9, total: 1e9, reach: MV_SR * 1.2, box: [-2, 46, -30, -4],
    on: {
      start() { P.spRunHit = 0; },
      update(dt, A, ax, grav) {
        P.vx = P.face * 175; grav();
        P.st -= 8 * dt; P.stDelay = 0.6;
        P.spRunHit -= dt * 1000;
        if (P.spRunHit <= 0) { P.spRunHit = 300; mvStrikeAt(mvRect(A), 0.4 + (mvHas(5) ? 0.5 : 0), 15, { A, onHit: t => { if (mvHas(5)) { mvSpark(t.x, t.y - 14, 5, '190,215,255', 160); tone(1600, 0.06, 0.04, 'square', 0.5); } } }); }
        if (peek('parry')) { take('parry'); setP('idle', 'idle', true); return 'stop'; }
        if (!held.has('heavy') || P.mvT >= 3000 || P.st <= 0) { mvStart('sp_finish', { cost: 0 }); return 'stop'; }
        if (!P.ground) { setP('air', 'jump_fall'); return 'stop'; }
      },
    } },
  sp_finish: { tags: ['sp_finish', 'sp_heavy'], kind: 'heavy', dmg: 2.2, poise: 70, stam: 0, wind: 120, total: 480, fin: true, reach: MV_SR * 1.5, lunge: 20, fx: 'slash3',
    dmgFn: () => (mvHas(5) ? 3.0 : 2.2) },
  sp_hpoke: { tags: ['sp_hpoke', 'sp_1'], dmg: 1.0, poise: 14, stam: 10, wind: 120, total: 360, reach: MV_SR * 1.5, fx: 'slash_air', next: { J: 'sp_2' } },
  sp_dive: { tags: ['sp_dive'], air: true, dmg: 1.5, poise: 40, stam: 16, wind: 1, total: 1 },   // the jump thrust dive (04_player startSpDive): table row only
  sp_air: { tags: ['sp_air'], air: true, dmg: 1.0, poise: 14, stam: 11, wind: 140, total: 360, reach: MV_SR * 1.3 },
  sp_up: { tags: ['sp_up'], up: true, dmg: 1.1, poise: 20, stam: 12, wind: 180, total: 420 },
  sp_down: { tags: ['sp_down'], down: true, dmg: 0.9, poise: 14, stam: 10, wind: 100, total: 300 },
});
