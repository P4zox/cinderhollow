// ------------------------------------------------------------------ WM: Dual Blades (A7) + Staff (A9) + Whip (A10)
// ================================================================== Dual Blades: the frenzy
// I toggles Demon Mode: stamina drains 12/s (8 at Mastery IV) and doesn't regenerate, swings are 20% faster, the chain
// runs to 6, K becomes the demon flurry, L the demon dash (120 ms, 8 stam, chains twice). Hits in Demon Mode fill the
// gauge 3% each; full = Archdemon (20 s, 30 at V) where hold K = Blade Dance (empties it). Out of stamina = exhausted.
// Perfect dodge: a roll started <= 100 ms (demon dash <= 175 ms) before a blow: +25 stamina, +0.1 attack speed for 6 s
// (refreshes, doesn't stack), one per enemy attack; L (perfect) -> J = counter flurry.
const TW_PD_SECS = 6;
function twDemon(on) {
  if (on === !!P.demon) return;
  P.demon = on;
  if (on) { sfx.roar && tone(110, 0.4, 0.08, 'sawtooth', 0.7); flashScreen = Math.max(flashScreen, 0.06); for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(0, 30), vx: rand(-40, 40), vy: -rand(30, 90), life: 0.5, kind: 'blood' }); }
  else tone(220, 0.25, 0.05, 'triangle', 0.5);
}
mvRegister('dual', {
  light: ['tw_1', 'tw_2', 'tw_3', 'tw_4'], K: 'tw_heavy', up: 'tw_up', air: 'tw_air', down: 'tw_down',
  plunge: { dmg: 1.3, poise: 50, stam: 16 },
  speed() { return 1 + (P.demon ? 0.2 : 0) + (P.pdT > 0 ? 0.1 : 0); },
  dodge() { return P.demon ? { stam: 8, total: 120, inv: 0.12, dist: 52, move: 120, chain: 2, kind: 'ddash', tags: ['tw_ddash', 'ember_dash', 'roll'] } : { stam: 16, total: 420, inv: 0.28, dist: 74, tags: ['roll'] }; },
  rollJ(g) {
    if (g.kind === 'ddash' && mvHas(2)) return { id: 'tw_dthrough', mul: g.perfect ? 1.5 : 1 };
    if (g.perfect) return 'tw_cflurry';
    return 'tw_dashslash';
  },
  dodgeUpdate(dt, g) {
    if (g.perfect && P.st > -20 && peek('attack') && !(g.kind === 'ddash' && mvHas(2))) { take('attack'); P.dg = null; mvStart('tw_cflurry'); return true; }   // instant after a perfect dodge
    if (g.kind === 'ddash' && mvHas(5) && g.t < g.move) twTrail();
  },
  onK(ax) {
    if (P.arch && held.has('heavy')) return mvStart('tw_khold');
    return mvStart(P.demon ? 'tw_dflurry' : 'tw_heavy');
  },
  onI(ax) {
    if (!P.ground) return false;
    take('parry');
    if (!P.demon && P.st <= 0) { sfx.deny(); return true; }
    return mvStart('tw_demon');
  },
  regenMul() { return P.demon || P.exhT > 0 ? 0 : 1; },
  tickAll(dt, cur) {
    if (!cur) { if (P.demon) P.demon = false; return; }
    P.pdT = Math.max(0, (P.pdT || 0) - dt); P.exhT = Math.max(0, (P.exhT || 0) - dt);
    if (P.demon) {
      P.st -= (mvHas(4) ? 8 : 12) * dt;
      if (P.st <= 0) { P.st = 0; twDemon(false); P.exhT = 1.5; toast('Exhausted', 1); sfx.deny(); }
    }
    if (P.arch) { P.gauge -= dt / (mvHas(5) ? 30 : 20); if (P.gauge <= 0) { P.gauge = 0; P.arch = false; } }
    for (const s of TW_TRAIL) s.life -= dt;
    if (TW_TRAIL.length) {
      for (let i = TW_TRAIL.length - 1; i >= 0; i--) if (TW_TRAIL[i].life <= 0) TW_TRAIL.splice(i, 1);
      if ((P.twTrailTick = (P.twTrailTick || 0) - dt) <= 0) {   // V: the burning trail ticks 0.3
        P.twTrailTick = 0.3;
        for (const t of targets()) { if (t.prop) continue; const hb = hbOf(t); if (!hb) continue; if (TW_TRAIL.some(s => s.x > hb.x0 - 4 && s.x < hb.x1 + 4 && s.y > hb.y0 - 6 && s.y - 20 < hb.y1)) mvStrikeAt(rect(hb.x0, hb.y0, hb.x1, hb.y1), 0.3, 0, { only: t, fire: true, A: ATK.tw_heavy }); }
      }
    }
  },
  onHit(t, info) {
    if (!t || t.prop) return;
    if (P.demon && !P.arch) { P.gauge = Math.min(1, (P.gauge || 0) + 0.03); if (P.gauge >= 1) { P.arch = true; sfx.roar && tone(90, 0.6, 0.1, 'sawtooth', 0.6); flashScreen = Math.max(flashScreen, 0.12); toast('Archdemon', 1.2); } }
  },
  dodged0(g) { P.twDodge = g; },
  // the demon dash is over after 120 ms but its window runs to 175: a blow landing just after the dash still counts
  hurt(c) { const g = P.twDodge; if (!c.negate && g && g.kind === 'ddash' && P.state !== 'roll' && !g.perfect && (P.clk - g.start) * 1000 <= 175) { if (twPerfect(g, c.id, c.opt)) c.negate = true; } },
  dodged(dmg, dir, id, opt) { const g = P.dg; if (P.state !== 'roll' || !g || g.perfect) return; twPerfect(g, id, opt); },
  interrupted() {},
  render() {
    if (P.demon || P.arch) {   // the demon aura: red embers rising off the body, a low red light; Archdemon burns darker
      const a = P.arch ? '200,40,90' : '220,40,40';
      mvAura(P.arch ? '#a01858' : '#a01010', (P.arch ? 0.16 : 0.11) + 0.03 * Math.sin(P.clk * 10));
      addLight(P.x, P.y - 16, P.arch ? 40 : 30, a, 0.55 + 0.15 * Math.sin(P.clk * 12));
      if (Math.random() < (P.arch ? 0.9 : 0.6)) particles.push({ x: P.x + rand(-7, 7), y: P.y - rand(0, 26), vx: rand(-8, 8), vy: -rand(25, 60), life: rand(0.3, 0.55), kind: P.arch ? 'ink' : 'blood' });
      if (P.demon && P.anim && Math.random() < 0.12) MV.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.18, max: 0.18, col: P.arch ? '#801848' : '#a01818', alpha: 0.3, wf: P.anim.frame });
    }
    if (P.pdT > 0) addLight(P.x, P.y - 14, 16, '220,230,250', 0.25);
    if (TW_TRAIL.length) for (const s of TW_TRAIL) if (Math.random() < 0.3) particles.push({ x: s.x + rand(-3, 3), y: s.y - 2, vx: 0, vy: -rand(20, 50), life: 0.35, kind: 'fire' });
  },
  hud(x) {
    // demon gauge (red; violet while Archdemon), the stamina drain shown by a pulsing frame
    mvHudBar(x, 21, 34, 2.5, P.gauge || 0, P.arch ? '#b0306a' : '#c03030');
    if (P.demon) { vctx.strokeStyle = `rgba(230,60,60,${0.5 + 0.4 * Math.sin(P.clk * 10)})`; vctx.lineWidth = scale; vctx.strokeRect(ox + (x - 1) * scale, oy + 20 * scale, 36 * scale, 4.5 * scale); }
    // the perfect-dodge blade: a small blade with a ring for the 6 s left
    if (P.pdT > 0) {
      const bx = x + 42, by = 22.2;
      mvHudRing(bx, by, 3.4, P.pdT / TW_PD_SECS, '#dfe6f5');
      vctx.strokeStyle = '#f0f4ff'; vctx.lineWidth = 0.8 * scale; vctx.beginPath(); vctx.moveTo(ox + (bx - 1.6) * scale, oy + (by + 1.6) * scale); vctx.lineTo(ox + (bx + 1.6) * scale, oy + (by - 1.6) * scale); vctx.stroke();
    }
  },
  unlocks: [
    { rank: 2, id: 'tw_dthrough', name: 'Dash-through cut', input: 'demon dash → J', desc: 'Cut through the foe as you dash: 1.0 dmg, 15 poise. After a perfect dodge it deals 1.5.' },
    { rank: 3, id: 'tw_dance2', name: 'Blade Dance II', input: 'hold K (Archdemon)', desc: 'Three more hits and a cross-cut finisher (+1.5).' },
    { rank: 4, id: 'tw_lungs', name: 'Iron lungs', input: '–', desc: 'The Demon Mode drain drops from 12/s to 8/s.' },
    { rank: 5, id: 'tw_archfiend', name: 'Archfiend', input: '–', desc: 'Archdemon lasts 30 s, and your dashes leave a burning trail (0.3 per tick).' },
  ],
}, {
  tw_1: { tags: ['tw_1'], hits: [0.45, 0.45], gap: 60, poise: 6, stam: 8, wind: 100, total: 300, step: 0, fx: 'slash', next: { J: 'tw_2' } },
  tw_2: { tags: ['tw_2'], hits: [0.45, 0.45], gap: 60, poise: 6, stam: 8, wind: 100, total: 300, step: 1, fx: 'slash2', next: { J: 'tw_3' } },
  tw_3: { tags: ['tw_3'], hits: [0.5, 0.5], gap: 60, poise: 8, stam: 9, wind: 110, total: 300, step: 2, fx: 'slash_up', next: { J: 'tw_4' } },
  tw_4: { tags: ['tw_4'], dmg: 1.2, poise: 20, stam: 12, wind: 220, total: 520, step: 3, fin: true, spin: true, next: { J: () => (P.demon ? 'tw_d5' : '@J') } },
  tw_d5: { tags: ['tw_d5', 'tw_1'], hits: [0.5, 0.5], gap: 60, poise: 8, stam: 8, wind: 100, total: 280, step: 4, can: () => P.demon, fx: 'slash', next: { J: 'tw_d6' } },
  tw_d6: { tags: ['tw_d6', 'tw_5'], hits: [0.45, 0.45, 0.45], gap: 55, poise: 8, stam: 10, wind: 100, total: 280, step: 5, fin: true, can: () => P.demon, fx: 'slash3' },
  tw_heavy: { tags: ['tw_heavy'], kind: 'heavy', dmg: 1.1, poise: 15, stam: 12, wind: 200, total: 480, lunge: 60, fx: 'slash3' },
  tw_dflurry: { tags: ['tw_dflurry', 'tw_heavy'], kind: 'heavy', hits: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3], gap: 100, poise: 30, stam: 16, wind: 150, total: 800, fin: true, fx: 'slash', fxEach: true, lunge: 20 },
  tw_khold: { tags: ['tw_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt);
      if (!held.has('heavy')) { mvStart(P.demon ? 'tw_dflurry' : 'tw_heavy'); return 'stop'; }
      if (P.mvT >= 200) { mvStart(mvHas(3) ? 'tw_dance2' : 'tw_dance'); return 'stop'; }
    } } },
  tw_dance: { tags: ['tw_dance', 'tw_dflurry', 'tw_heavy'], kind: 'heavy', hits: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 1.0], gap: 140, poise: 60, stam: 0, wind: 150, total: 1400, fin: true, fxEach: true, fx: 'slash', armor: 0.3,
    can: () => P.arch, on: { start() { flashScreen = Math.max(flashScreen, 0.1); }, end() { P.gauge = 0; P.arch = false; } } },
  tw_dance2: { tags: ['tw_dance2', 'tw_dance', 'tw_dflurry', 'tw_heavy'], kind: 'heavy', rank: 3, hits: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 1.6], gap: 125, poise: 80, stam: 0, wind: 150, total: 1680, fin: true, fxEach: true, fx: 'slash', armor: 0.3,
    can: () => P.arch, on: { start() { flashScreen = Math.max(flashScreen, 0.1); }, end() { P.gauge = 0; P.arch = false; } } },
  tw_demon: { tags: ['tw_demon_on', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 0, wind: 200, total: 200, on: { start() { twDemon(!P.demon); } } },
  tw_cflurry: { tags: ['tw_counter', 'tw_dflurry', 'tw_1'], hits: [0.45, 0.45, 0.45], gap: 60, poise: 15, stam: 8, wind: 80, total: 300, counter: true, fin: true, fx: 'slash3', fxEach: true },
  tw_dashslash: { tags: ['tw_dashslash', 'tw_2'], dmg: 1.0, poise: 10, stam: 8, wind: 100, total: 320, lunge: 30, fx: 'slash2', next: { J: 'tw_2' } },
  tw_dthrough: { tags: ['tw_dashslash', 'tw_2'], rank: 2, dmg: 1.0, poise: 15, stam: 8, wind: 100, total: 320, lunge: 60, lungeLead: 100, inv: [0, 120], fx: 'slash3',
    on: { update() { if (mvHas(5) && P.mvT < 160) twTrail(); } } },
  tw_air: { tags: ['tw_air'], air: true, hits: [0.45, 0.45], gap: 60, poise: 8, stam: 9, wind: 120, total: 330, spin: true },
  tw_up: { tags: ['tw_up'], up: true, hits: [0.45, 0.45], gap: 60, poise: 8, stam: 9, wind: 140, total: 340 },
  tw_down: { tags: ['tw_down'], down: true, hits: [0.3, 0.3, 0.3], gap: 50, poise: 10, stam: 10, wind: 100, total: 320 },
});
function twPerfect(g, id, opt) {
    const win = g.kind === 'ddash' ? 175 : 100, el = g.t !== undefined && P.state === 'roll' && P.dg === g ? g.t : (P.clk - g.start) * 1000;
    if (el > win) return false;
    const key = id !== undefined ? id : (opt && opt.src ? opt.src : 'h') + ':' + Math.floor(P.clk / 0.6);
    P.pdKeys = P.pdKeys || new Set(); if (P.pdKeys.has(key)) return false;   // one perfect dodge per enemy attack
    P.pdKeys.add(key); if (P.pdKeys.size > 64) P.pdKeys = new Set([key]);
    g.perfect = true; P.pdT = TW_PD_SECS; P.st = Math.min(D.maxSt, P.st + 25); MV.pd = (MV.pd || 0) + 1;
    mvGain('perfect dodge');
    // feedback: a sharp silver chime, a flicker of time, a silver afterimage left behind
    tone(2093, 0.25, 0.06, 'triangle', 1.6); tone(3136, 0.35, 0.04, 'sine', 1.8, 0.04); slowmo = Math.max(slowmo, 0.09);
    const pt = pHas('tw_pdodge') && pSheet().tag('tw_pdodge');   // WA2's silver pose is the ghost left behind; the dodge itself keeps moving
    mvAfterimage('#e4ecf8', 0.45, 0.42, pt ? pt.from : undefined);
    mvSpark(P.x, P.y - 16, 8, '230,236,248', 160);
    return true;
}
const TW_TRAIL = [];
function twTrail() { if (P.ground && (!TW_TRAIL.length || Math.abs(TW_TRAIL[TW_TRAIL.length - 1].x - P.x) > 6)) TW_TRAIL.push({ x: P.x, y: P.y, life: 1.5 }); }
HOOKS.enter.push(() => { TW_TRAIL.length = 0; });

// ================================================================== Staff: master of the air
// I vaults (350 ms, ~2.2 tiles up and forward, invulnerable 0.2 s, 15 stam) -- not an attack. Combo hits strike in
// front and slightly behind. Each air hit adds a momentum stack (max 3, +8% each), kept until 0.5 s after landing (the
// first ground swing keeps them). Air K = aerial spin; air down J = dive kick (its bounce refunds one air attack).
// Mastery: roll vault (II), spin finisher (III), double vault (IV), gale (V).
function stVault(fromAir) {
  if (P.st <= 0) return false;
  spend(15); P.mvInv = 0.2; P.vaultT = 0; P.vaultAir = !!fromAir;
  setP('vault', pHas('st_vault') ? 'st_vault' : 'double_jump', false, pHas('st_vault') ? 1 : 0.8);
  if (!fromAir) spawnFx('dust', P.x, P.y, P.face);
  else { P.vy = -240; P.vx = P.face * 110; P.ground = false; mvSpark(P.x, P.y + 4, 6, '255,236,190', 120); }
  sfx.jump(); return true;
}
MV_STATES.vault = (dt, ax, grav) => {
  P.vaultT += dt;
  if (!P.vaultAir && P.vaultT < 0.13) { P.vx = approach(P.vx, 0, 900 * dt); grav(); return; }   // the staff plants first
  if (!P.vaultAir && !P.vaultUp) { P.vaultUp = true; P.vy = -235; P.vx = P.face * 115; P.ground = false; }
  if (ax) P.vx = approach(P.vx, ax * 125, 400 * dt);
  grav();
  if (P.vaultT >= 0.35 || (P.vaultT >= 0.22 && (peek('attack') || peek('heavy')))) { P.vaultUp = false; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
};
MV_STATES.vault.inv = () => false;
function stMomentumHit(A) {   // +1 stack per airborne move that connects (once per move)
  if (P.ground) return;   // only hits while airborne build momentum
  if (P.momMove === P.hitSet) return; P.momMove = P.hitSet;
  if ((P.mom || 0) < 3) { P.mom = (P.mom || 0) + 1; tone(880 + P.mom * 220, 0.12, 0.04, 'triangle', 1.4); }
  P.momLand = null;
}
mvRegister('staff', {
  light: ['st_1', 'st_2', 'st_3', 'st_4'], K: 'st_heavy', up: 'st_up', air: 'st_air', down: 'st_down',
  plunge: { dmg: 1.4, poise: 40, stam: 16 },
  rollJ: 'st_lowsweep',
  onK(ax) {
    if (mvHas(5) && (P.mom || 0) >= 3) return mvStart('st_gale');
    if (P.st < staffSpinCost() - 0.5) { sfx.deny(); P.denyT = 0.5; toast('The spin needs 30% of your stamina', 1.4); return true; }
    return mvStart('st_heavy');
  },
  onAirK(ax) {   // the aerial spin replaces the plunge (and counts toward the air limit like any air attack)
    take('heavy'); if (ax) P.face = ax;
    if (mvHas(5) && (P.mom || 0) >= 3) return mvStart('st_gale');
    return mvStart('st_aspin');
  },
  onI(ax) {
    if (P.ground) { take('parry'); if (ax) P.face = ax; return stVault(false); }
    // IV: double vault -- off a foe's head in the air, once per jump; refunds the air attacks
    if (mvHas(4) && !P.dvUsed && P.st > 0) {
      const foe = targets().find(t => !t.prop && !t.boss && Math.abs(t.x - P.x) < 34 && P.y < t.y + 4 && P.y > t.y - 70) || (boss && boss.active && boss.alive && Math.abs(boss.x - P.x) < 50 && P.y < boss.y ? boss : null);
      if (foe) { take('parry'); P.dvUsed = true; P.airN = 0; P.airLock = false; return stVault(true); }
    }
    return false;
  },
  dodgeUpdate(dt, g) { if (mvHas(2) && P.ground && peek('parry') && g.t >= 80) { take('parry'); P.dg = null; stVault(false); return true; } },   // II: roll vault
  hitMod(c) { if (P.mom > 0) c.mul *= 1 + 0.08 * P.mom; },
  onHit(t, info, A) { if (!t || t.prop) return; stMomentumHit(A); if (A.mv && A.mv.id === 'st_down' && !P.stRefund) { P.stRefund = true; airRefund(); } },
  started(A) {
    P.stRefund = false;
    if (P.ground && P.mom > 0) { if (P.momLand !== null && P.momLand !== undefined && P.clk - P.momLand <= 0.5) P.momKeep = A.mv.id; }
  },
  landed() { P.dvUsed = false; if (P.mom > 0) P.momLand = P.clk; },
  tick(dt) {
    if (P.mom > 0 && P.ground && P.momLand != null && P.clk - P.momLand > 0.5) {
      const A = ATK[P.state]; if (!(A && A.mv && P.momKeep === A.mv.id)) { P.mom = 0; P.momKeep = null; P.momLand = null; }
    }
  },
  interrupted() {},
  render() {
    for (let i = 0; i < (P.mom || 0); i++) {   // momentum: up to 3 motes orbiting the staff hand
      const a = P.clk * 5 + i * 2.094, x = P.x + Math.cos(a) * 11, y = P.y - 18 + Math.sin(a) * 5;
      addLight(x, y, 9, '160,220,255', 0.7);
      drawGlow(() => { g.fillStyle = 'rgba(190,230,255,0.95)'; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2); });
      if (Math.random() < 0.35) particles.push({ x, y, vx: 0, vy: -10, life: 0.25, kind: 'mote' });
    }
    if (P.state === 'vault' && P.vaultT < 0.2) addLight(P.x, P.y - 14, 20, '220,240,255', 0.4);
  },
  hud(x) { for (let i = 0; i < 3; i++) mvHudPip(x + 3 + i * 5, 22, i < (P.mom || 0), '#a8dcff'); },
  unlocks: [
    { rank: 2, id: 'st_rollvault', name: 'Roll vault', input: 'L → I', desc: 'Vault straight out of a roll.' },
    { rank: 3, id: 'st_aspin2', name: 'Spin finisher', input: 'air K → K', desc: 'A second aerial spin: 1.8 dmg, uses one air attack.' },
    { rank: 4, id: 'st_doublevault', name: 'Double vault', input: 'I in the air near a foe', desc: "Vault off the foe's head; refunds the air attacks once per jump." },
    { rank: 5, id: 'st_gale', name: 'Gale', input: 'K with 3 momentum stacks', desc: 'The spin becomes a travelling tornado: 3 hits of 0.6.' },
  ],
}, {
  st_1: { tags: ['st_1'], dmg: 0.85, poise: 12, stam: 10, wind: 140, total: 360, step: 0, back: 14, fx: 'slash_air', next: { J: 'st_2' } },
  st_2: { tags: ['st_2'], dmg: 0.85, poise: 12, stam: 10, wind: 140, total: 360, step: 1, back: 30, next: { J: 'st_3' } },
  st_3: { tags: ['st_3'], dmg: 0.9, poise: 16, stam: 11, wind: 160, total: 380, step: 2, back: 14, reel: true, ys: [-14, 0], next: { J: 'st_4' } },
  st_4: { tags: ['st_4'], dmg: 1.4, poise: 35, stam: 14, wind: 240, total: 560, step: 3, back: 14, fin: true, fx: 'heavy' },
  st_heavy: { tags: ['st_heavy'], kind: 'heavy', staffSpin: true, hits: [0.8, 0.8], gap: 180, poise: 60, stam: () => staffSpinCost(), wind: 220, total: 640, spin: true, reach: 40, backReach: 40, fin: true },
  st_gale: { tags: ['st_gale', 'st_heavy'], kind: 'heavy', rank: 5, noHit: true, airCount: true, dmg: 0.6, poise: 20, stam: 16, wind: 220, total: 640, airOk: true,
    on: { swing() { P.mom = 0; stGale(); } } },
  st_lowsweep: { tags: ['st_lowsweep', 'st_3'], dmg: 1.1, poise: 20, stam: 10, wind: 140, total: 380, back: 14, reel: true, ys: [-14, 0], next: { J: 'st_4' } },
  st_air: { tags: ['st_air'], air: true, dmg: 0.9, poise: 14, stam: 10, wind: 120, total: 320 },
  st_aspin: { tags: ['st_aspin', 'st_air'], air: true, kind: 'heavy', dmg: 1.4, poise: 40, stam: 16, wind: 180, total: 460, spin: true, reach: 38, ys: [-38, 2],
    next: { K: () => (mvHas(3) && !P.ground ? 'st_aspin2' : null) } },
  st_aspin2: { tags: ['st_aspin2', 'st_aspin', 'st_air'], air: true, kind: 'heavy', rank: 3, dmg: 1.8, poise: 45, stam: 16, wind: 120, total: 540, spin: true, reach: 40, ys: [-38, 2], fin: true,
    can: () => !P.airLock },
  st_up: { tags: ['st_twirl_up', 'st_up'], up: true, dmg: 0.9, poise: 14, stam: 10, wind: 140, total: 340 },
  st_down: { tags: ['st_divekick', 'st_down'], down: true, dmg: 1.0, poise: 30, stam: 10, wind: 100, total: 300 },
});
// V: gale -- a tornado that travels forward and strikes 3 times (0.6 each)
const ST_GALES = [];
function stGale() {
  ST_GALES.push({ x: P.x + P.face * 18, y: P.y, d: P.face, t: 0, n: 0 });
  sfx.heavySwing(); shake = Math.max(shake, 4);
}
HOOKS.enter.push(() => { ST_GALES.length = 0; });
HOOKS.update.push(dt => {
  for (const gl of ST_GALES) {
    gl.t += dt; gl.x += gl.d * 120 * dt;
    if (gl.t >= 0.15 + gl.n * 0.3 && gl.n < 3) { gl.n++; mvStrikeAt(rect(gl.x - 16, gl.y - 40, gl.x + 16, gl.y + 2), 0.6, 20, { A: ATK.st_gale, kind: 'heavy' }); tone(300 + gl.n * 80, 0.15, 0.04, 'sawtooth', 0.4); }
    if (Math.random() < 0.9) { const a = rand(0, 6.283); particles.push({ x: gl.x + Math.cos(a) * rand(4, 14), y: gl.y - rand(0, 38), vx: -Math.sin(a) * 60, vy: -rand(10, 40), life: 0.3, kind: 'dust' }); }
  }
  for (let i = ST_GALES.length - 1; i >= 0; i--) if (ST_GALES[i].t > 1.1) ST_GALES.splice(i, 1);
});
HOOKS.render.push(() => { for (const gl of ST_GALES) { addLight(gl.x, gl.y - 20, 30, '200,230,255', 0.6); g.strokeStyle = 'rgba(210,235,255,0.45)'; g.lineWidth = 1; for (let k = 0; k < 4; k++) { const r = 5 + k * 3, a = gl.t * 14 + k; g.beginPath(); g.ellipse(Math.round(gl.x), Math.round(gl.y - 6 - k * 9), r + 2, 2.5, 0, a, a + 4.2); g.stroke(); } } });

// ================================================================== Whip: control the space
// The tip: the last 25% of a lash's reach deals x1.3 and fills the crack meter (+10 light, +25 heavy). At 100 the next K
// is a thunderclap (3.2, 90 poise, a small blast). I grapples (64 px, 2 s cooldown): small foes are pulled in and
// stunned, large foes and hook rings pull you; never bosses. Mastery: snap counter (II), grapple slam (III), double
// crack (IV), thousand lashes (V).
const WH_REACH = MV_SR * 2;   // 80 px
function whTip(c) {
  const d = c.d, hb = c.hb;
  if (!d.tip) return;
  let dist, front;
  if (c.A.up) { dist = P.y - hb.y1; front = -c.A.ys[0]; }
  else { dist = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1; front = c.A.reach[1]; }
  if (dist >= front * 0.75) { c.tip = true; c.mul *= 1.3; }
  else if (d.tipOnly) c.skip = true;
}
function whTipFx(x, y, big) {   // the tip spark: a bright crack of light where the lash snaps
  sfx.parry(); if (typeof feelFlash === 'function') feelFlash(x, y, big ? 40 : 28, '255,245,220', 1.3, 0.1);
  mvSpark(x, y, big ? 12 : 7, '255,245,220', big ? 220 : 160);
  for (let i = 0; i < 4; i++) particles.push({ x, y, vx: P.face * rand(20, 90), vy: -rand(10, 70), g: 200, life: 0.3, kind: 'spark' });
}
mvRegister('whip', {
  light: ['wh_1', 'wh_2', 'wh_3'], K: 'wh_heavy', up: 'wh_up', air: 'wh_air', down: 'wh_down',
  plunge: { dmg: 1.3, poise: 50, stam: 16 },
  rollJ: 'wh_retreat',
  onK(ax) {
    if ((P.crack || 0) >= 100) return mvStart('wh_thunder');
    if (P.whPull && P.clk - P.whPull.t < 0.6 && mvHas(3) && P.whPull.t2 && P.whPull.t2.alive !== false) return mvStart('wh_slam');   // III: grapple -> K
    return mvStart('wh_heavy');
  },
  onI(ax) {
    if (P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax;
    if (mvHas(2)) P.snapT = 0.15;   // II: a blow within 150 ms of the press is snapped away
    if ((P.whCd || 0) > 0) { if (!(P.snapT > 0)) sfx.deny(); return true; }
    spend(14); P.whCd = 2; whGrapple(); return true;
  },
  hurt(c) {
    if (P.snapT > 0 && !c.negate && c.opt && (c.opt.src || c.id !== undefined)) {
      c.negate = true; P.snapT = 0; mvGain('counter');
      const s = c.opt.src; if (c.dir) P.face = -c.dir;
      sfx.parry(); hitstop = Math.max(hitstop, 0.1); whTipFx(P.x + P.face * 40, P.y - 18, true);
      if (s && s.alive !== false) {
        if (s.boss || s === boss) { if (typeof s.stance === 'number' && !(s.stanceImmune > 0) && s.state !== 'stagger') { s.stance += 60; if (s.stance >= s.stanceMax && s.stagger && (!s.canStagger || s.canStagger())) s.stagger(); } }
        else if (s.breakStance && !(s.cfg && s.cfg.elite) && s.state !== 'stagger') s.breakStance();
      }
      mvStart('wh_snap');
    }
  },
  hitMod(c) { whTip(c); },
  onHit(t, info, A, c) {
    if (!c || !c.tip || !t || t.prop) return;
    const big = A.kind === 'heavy';
    whTipFx(info.x, info.y, big);
    if (A.mv.id !== 'wh_thunder') {
      const was = P.crack || 0; P.crack = Math.min(100, was + (big ? 25 : 10));
      if (was < 100 && P.crack >= 100) { tone(1568, 0.3, 0.06, 'triangle', 1.6); sfx.glint(); }
    }
  },
  tick(dt) { P.whCd = Math.max(0, (P.whCd || 0) - dt); P.snapT = Math.max(0, (P.snapT || 0) - dt); },
  render() {
    if ((P.crack || 0) >= 100) { mvStar(P.x + P.face * 9, P.y - 17, 2 + 1.5 * Math.abs(Math.sin(P.clk * 9)), '210,225,255', 0.9); addLight(P.x + P.face * 8, P.y - 18, 20, '200,220,255', 0.6 + 0.3 * Math.sin(P.clk * 16)); if (Math.random() < 0.3) particles.push({ x: P.x + P.face * rand(4, 16), y: P.y - rand(10, 26), vx: 0, vy: -rand(10, 30), life: 0.25, kind: 'spark' }); }
    const gp = P.whGrap;
    if (gp && (P.state === 'grapple' || P.clk - gp.t < 0.2)) {   // the chain beyond the frame
      const tx = gp.x, ty = gp.y; g.strokeStyle = 'rgba(190,190,205,0.9)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(Math.round(P.x + P.face * 8) + 0.5, Math.round(P.y - 18) + 0.5); g.lineTo(Math.round(tx) + 0.5, Math.round(ty) + 0.5); g.stroke();
      addLight(tx, ty, 10, '255,240,210', 0.6);
    }
  },
  hud(x) {
    mvHudBar(x, 21, 34, 2.5, (P.crack || 0) / 100, (P.crack || 0) >= 100 ? '#cfe2ff' : '#8aa0c8');
    if ((P.whCd || 0) > 0) mvHudBar(x, 25, 34 * P.whCd / 2, 1, 1, 'rgba(200,200,215,0.5)', 'rgba(0,0,0,0)');
  },
  unlocks: [
    { rank: 2, id: 'wh_snap', name: 'Snap counter', input: 'I within 150 ms of a hit', desc: 'Lashes the attacker out of its move: the hit is negated, small foes stagger, a boss takes +60 stance.' },
    { rank: 3, id: 'wh_slam', name: 'Grapple slam', input: 'grapple → K', desc: 'Pull a small foe in and slam it: 1.6 dmg, stunned.' },
    { rank: 4, id: 'wh_double', name: 'Double crack', input: 'K → K', desc: 'A follow-up crack: 1.4 then 1.8, both with tip bonuses.' },
    { rank: 5, id: 'wh_thousand', name: 'Thousand lashes', input: 'hold J', desc: "A held flurry: 8 × 0.45, tip-only, so it's a spacing test." },
  ],
}, {
  wh_1: { tags: ['wh_1'], dmg: 0.8, poise: 8, stam: 9, wind: 160, total: 400, step: 0, reach: WH_REACH, tip: true, next: { J: 'wh_2' },
    on: { update() { if (mvHas(5) && P.mvT >= 250 && P.mvT < 300 && held.has('attack')) { mvStart('wh_thousand'); return 'stop'; } } } },
  wh_2: { tags: ['wh_2'], dmg: 0.8, poise: 8, stam: 9, wind: 160, total: 400, step: 1, reach: WH_REACH, tip: true, next: { J: 'wh_3' } },
  wh_3: { tags: ['wh_3'], dmg: 1.1, poise: 20, stam: 14, wind: 260, total: 620, step: 2, fin: true, spin: true, reach: WH_REACH },   // the whirl spans the whole lash, front and back
  wh_heavy: { tags: ['wh_heavy'], kind: 'heavy', dmg: 1.4, poise: 30, stam: 18, wind: 300, total: 680, reach: WH_REACH, tip: true,
    next: { K: () => (mvHas(4) ? 'wh_double' : '@K') },
    on: { update() { if (P.mvT >= 120 && P.mvT < 170 && held.has('heavy') && !P.mvO.noHold) { mvStart('wh_overhead_hold', { cost: 0 }); return 'stop'; } } } },
  wh_overhead_hold: { tags: ['wh_overhead_hold', 'wh_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000;
      if (P.mvT >= 380 && !P.whFull) { P.whFull = true; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); }
      if (!held.has('heavy') || P.mvT > 1800) { const f = P.whFull; P.whFull = false; if (f) mvStart('wh_overhead', { cost: 6, charged: true }); else mvStart('wh_heavy', { cost: 0, t0: 120, noHold: true }); return 'stop'; }
    }, start() { P.whFull = false; } } },
  wh_overhead: { tags: ['wh_overhead', 'wh_heavy'], kind: 'heavy', dmg: 2.0, poise: 45, stam: 24, wind: 300, total: 600, reach: MV_SR * 2.4, tip: true, fin: true },
  wh_thunder: { tags: ['wh_thunder', 'wh_heavy'], kind: 'heavy', dmg: 3.2, poise: 90, stam: 20, wind: 300, total: 700, reach: WH_REACH, fin: true,
    on: {
      start() { P.crack = 0; },
      swing(A) {   // the blast at the tip
        const tx = P.x + P.face * (WH_REACH - 10), ty = P.y - 18;
        whTipFx(tx, ty, true); flashScreen = Math.max(flashScreen, 0.12); shake = Math.max(shake, 6); sfx.boom();
        spawnFx('shockwave', tx, P.y, 1);
      },
      hit(t) { if (!t.boss && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger') t.breakStance(); },
    } },
  wh_double: { tags: ['wh_double', 'wh_heavy'], kind: 'heavy', rank: 4, dmg: 1.8, poise: 35, stam: 18, wind: 220, total: 550, reach: WH_REACH, tip: true, fin: true },
  wh_thousand: { tags: ['wh_thousand', 'wh_1'], rank: 5, hits: [0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45], gap: 110, poise: 32, stam: 20, wind: 80, total: 1000, reach: WH_REACH, tip: true, tipOnly: true, fxEach: false, animLoop: true },
  wh_retreat: { tags: ['wh_retreat', 'wh_1'], dmg: 1.0, poise: 10, stam: 10, wind: 160, total: 420, lunge: -40, lungeLead: 160, lungeTail: 200, reach: WH_REACH, tip: true },
  wh_snap: { tags: ['wh_snap', 'wh_1'], rank: 2, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 80, total: 320, inv: [0, 200] },
  wh_slam: { tags: ['wh_slam', 'wh_heavy'], kind: 'heavy', rank: 3, dmg: 1.6, poise: 60, stam: 16, wind: 250, total: 600, reach: 34, fin: true, slam: true, reel: true },
  wh_air: { tags: ['wh_air'], air: true, dmg: 0.9, poise: 12, stam: 10, wind: 160, total: 380, spin: true, reach: MV_SR * 1.4 },
  wh_up: { tags: ['wh_up'], up: true, dmg: 0.9, poise: 14, stam: 10, wind: 160, total: 380, tip: true, ys: [-70, -14] },
  wh_down: { tags: ['wh_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 120, total: 320, box: [-8, 14, -10, 44] },
});
// ---- the grapple: a thrown chain (64 px). Small foes come to you (stunned 0.5 s); large foes and hook rings pull you.
function whLarge(t) { const hb = t.hurtbox && t.hurtbox(); return !!(t.cfg && t.cfg.elite) || (hb && (hb.x1 - hb.x0 > 28 || hb.y1 - hb.y0 > 44)); }
function whGrapple() {
  const R = 64;
  let best = null, bd = 1e9;
  for (const h of (room.hooks || [])) {
    const dx = h.x - P.x, dy = h.y - (P.y - 20), d = Math.hypot(dx, dy);
    if (d > R + 16 || dx * P.face < -8) continue;
    if (d < bd && lineOfSight(P.x, P.y - 22, h.x, h.y + 6)) { bd = d; best = { ring: h, x: h.x, y: h.y }; }
  }
  for (const t of targets()) {
    if (t.prop || t.alive === false || t.boss || (boss && t === boss) || (boss && boss.parts && boss.parts.includes(t))) continue;   // never bosses
    const hb = hbOf(t); if (!hb) continue;
    const near = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1, dy = (hb.y0 + hb.y1) / 2 - (P.y - 14);
    if (near < -6 || near > R || Math.abs(dy) > 40) continue;
    if (near < bd) { bd = near; best = { foe: t, x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2 }; }
  }
  P.whGrap = { t: P.clk, x: P.x + P.face * R, y: P.y - 18 };
  setP('grapple', pHas('wh_grapple') ? 'wh_grapple' : 'wh_1', false);
  P.grT = 0; P.grTarget = best; sfx.shoot && sfx.shoot();
  if (best) { P.whGrap.x = best.x; P.whGrap.y = best.y; }
}
MV_STATES.grapple = (dt, ax, grav) => {
  P.grT += dt; const b = P.grTarget;
  if (!b) { P.vx = approach(P.vx, 0, 900 * dt); grav(); if (P.grT >= 0.3) setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); return; }
  if (b.foe && !whLarge(b.foe) && !b.done) {   // a small foe: reel it in, stunned
    b.done = true; const t = b.foe;
    P.whPull = { t: P.clk, t2: t };
    weaponPull(t, { chain: true });
    if (t.breakStance && t.state !== 'stagger') t.breakStance();
    t._whStun = 0.5; whTipFx(b.x, b.y, false);
    if (pHas('wh_grapple_pull')) P.anim.set('wh_grapple_pull', false);
  }
  if (b.foe && !whLarge(b.foe)) { P.vx = approach(P.vx, 0, 900 * dt); grav(); if (P.grT >= 0.3) setP('idle', 'idle', true); return; }
  // a large foe or a hook ring: the chain hauls you in
  if (P.grT < 0.08) { P.vx = 0; grav(); return; }
  if (pHas('wh_grapple_zip') && P.anim.tag !== 'wh_grapple_zip') P.anim.set('wh_grapple_zip', true);
  if (b.foe && b.foe.alive !== false) { const hb = hbOf(b.foe); if (hb) { b.x = P.x < b.x ? hb.x0 - 6 : hb.x1 + 6; b.y = P.y - 14; } }
  P.whGrap.x = b.x; P.whGrap.y = b.y;
  const dx = b.x - P.x, dy = (b.ring ? b.y + 30 : b.y + 14) - P.y, d = Math.hypot(dx, dy);
  if (d < 10 || P.grT > 0.7) { P.vy = b.ring ? -200 : -80; P.vx = Math.sign(dx || P.face) * 90; P.ground = false; setP('air', 'jump_up'); return; }
  P.vx = dx / d * 360; P.vy = dy / d * 360; P.ground = false;
};
HOOKS.update.push(dt => { for (const e of enemies) if (e._whStun > 0) { e._whStun -= dt; if (e.vx !== undefined) e.vx = 0; } });
