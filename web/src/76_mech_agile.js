// ------------------------------------------------------------------ WM: Dual Blades (A7)  (Staff + Whip: 76_mech_reach.js)
// ================================================================== Dual Blades: the frenzy
// I toggles Demon Mode: stamina drains 12/s (8 at Mastery IV) and doesn't regenerate, swings are 20% faster, the chain
// runs to 6, K becomes the demon flurry, L the demon dash (120 ms, 8 stam, chains twice). Hits in Demon Mode fill the
// gauge 3% each; full = Archdemon (20 s, 30 at V) where hold K = Blade Dance (empties it). Out of stamina = exhausted.
// Perfect dodge: a roll started <= 100 ms (demon dash <= 175 ms) before a blow: +0.1 attack speed for 6 s (refreshes,
// doesn't stack) and +25 stamina once per enemy attack (a multi-hit attack, a beam's ticks, a mist: one refund); bumping
// into a foe's body isn't a blow. L (perfect) -> J = counter flurry, -> K (III) = silver reversal.
// v14: Demon Mode attacks cost half stamina (the drain is the price: ~5 s of flurry from a full bar instead of ~3);
// the demon chain hits 5-6 are lighter (Demon x6 3.85 -> 3.4 dmg/s, as planned); the dash-through cut has no i-frames
// of its own (the dash before it has them); Blade Dance armour 0.3 -> 0.2 of max HP; the Archfiend trail is a glow, not
// a weapon (0.15 per 0.4 s, 1 s). New routes: J J (pause) J fang barrage, J J J K skyward fangs, air J J crossfall,
// Demon J x6 -> K rending cyclone (II), L -> K reversal cut (III).
const TW_PD_SECS = 6, TW_PAUSE = [110, 450];   // the "pause" of J J (pause) J: ms after the 2nd cut ends
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
  started(A, o) {   // Demon Mode: attacks cost half (refund the other half of what mvStart just spent)
    const d = A.mv, c = o.cost !== undefined ? o.cost : (typeof d.stam === 'number' ? d.stam : 0);
    if (P.demon && c > 0 && d.id !== 'tw_demon') P.st += c * 0.5;
  },
  onJ(ax) {   // J J (pause) J: a press 110-450 ms after the 2nd double slash ended = fang barrage
    const c = P.mvChain;
    if (!P.ground || !c || c.id !== 'tw_2' || held.has('up')) return false;
    const ms = (P.clk - c.t) * 1000;
    if (ms < TW_PAUSE[0] || ms > TW_PAUSE[1]) return false;
    take('attack'); P.mvChain = null; if (ax) P.face = ax;
    return mvStart('tw_barrage') || true;
  },
  rollK(g) {   // L -> K: the reversal cut (III; silver and x1.5 after a perfect dodge); otherwise the plain K out of the roll
    const ax = inputX(); if (ax) P.face = ax;
    if (mvHas(3) && (g.perfect || g.kind !== 'ddash')) return mvStart('tw_reversal', { pd: !!g.perfect, mul: g.perfect ? 1.5 : 1 });
    return MV.types.dual.onK(ax);
  },
  rollJ(g) {
    if (g.kind === 'ddash' && mvHas(2)) return { id: 'tw_dthrough', mul: g.perfect ? 1.5 : 1 };
    if (g.perfect) return 'tw_cflurry';
    return 'tw_dashslash';
  },
  dodgeUpdate(dt, g) {
    if (g.perfect && P.st > -20 && peek('attack') && !(g.kind === 'ddash' && mvHas(2))) { take('attack'); P.dg = null; mvStart('tw_cflurry'); return true; }   // instant after a perfect dodge
    if (g.perfect && P.st > -20 && mvHas(3) && peek('heavy')) { take('heavy'); P.dg = null; const ax = inputX(); if (ax) P.face = ax; mvStart('tw_reversal', { pd: true, mul: 1.5 }); return true; }
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
      const st0 = P.st; P.st -= (mvHas(4) ? 8 : 12) * dt;
      if (st0 > D.maxSt * 0.2 && P.st <= D.maxSt * 0.2) tone(330, 0.12, 0.05, 'square', 0.9);   // a warning tick: a fifth of the bar left
      if (P.st <= 0) { P.st = 0; twDemon(false); P.exhT = 1.5; toast('Exhausted', 1); sfx.deny(); }
    }
    if (P.arch) { P.gauge -= dt / (mvHas(5) ? 30 : 20); if (P.gauge <= 0) { P.gauge = 0; P.arch = false; } }
    for (const s of TW_TRAIL) s.life -= dt;
    if (TW_TRAIL.length) {
      for (let i = TW_TRAIL.length - 1; i >= 0; i--) if (TW_TRAIL[i].life <= 0) TW_TRAIL.splice(i, 1);
      if ((P.twTrailTick = (P.twTrailTick || 0) - dt) <= 0) {   // V: the burning trail ticks 0.15 every 0.4 s (an embellishment)
        P.twTrailTick = 0.4;
        for (const t of targets()) { if (t.prop) continue; const hb = hbOf(t); if (!hb) continue; if (TW_TRAIL.some(s => s.x > hb.x0 - 4 && s.x < hb.x1 + 4 && s.y > hb.y0 - 6 && s.y - 20 < hb.y1)) mvStrikeAt(rect(hb.x0, hb.y0, hb.x1, hb.y1), 0.15, 0, { only: t, fire: true, A: ATK.tw_heavy }); }
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
    { rank: 2, id: 'tw_dthrough', name: 'Dash-through cut', input: 'demon dash → J', desc: 'Cut through the foe out of the dash: 1.0 dmg, 15 poise. After a perfect dodge it deals 1.5.' },
    { rank: 2, id: 'tw_bwheel', name: 'Bloodwheel', input: 'Demon: K → J', desc: 'Somersault out of the demon flurry with three crimson cuts; J carries on into the demon chain.' },
    { rank: 2, id: 'tw_dfin', name: 'Rending cyclone', input: 'Demon: J ×6 → K', desc: 'Close the demon chain: two crimson spins and a leaping cross-cut (40 poise).' },
    { rank: 3, id: 'tw_dance2', name: 'Blade Dance II', input: 'hold K (Archdemon)', desc: 'Three more hits and a cross-cut finisher (+1.5).' },
    { rank: 3, id: 'tw_reversal', name: 'Reversal cut', input: 'L → K', desc: 'Turn out of the roll with a rising double cut. After a perfect dodge: silver, x1.5, big poise.' },
    { rank: 4, id: 'tw_lungs', name: 'Iron lungs', input: '–', desc: 'The Demon Mode drain drops from 12/s to 8/s.' },
    { rank: 5, id: 'tw_archfiend', name: 'Archfiend', input: '–', desc: 'Archdemon lasts 30 s, and your dashes leave a smouldering trail (0.15 per tick).' },
  ],
  combos: [
    { rank: 1, name: 'Twin slashes', input: 'J J J J', desc: 'Two double slashes, a rising cross, then a spinning finisher.' },
    { rank: 1, name: 'Fang barrage', input: 'J J (pause) J', desc: 'Wait a beat after the 2nd slash: five quick alternating stabs. J: spin' },
    { rank: 1, name: 'Skyward fangs', input: 'J J J K', desc: 'A rising double cut that carries you up, popping light foes. J: air J' },
    { rank: 1, name: 'Hooking cross', input: 'J J K', desc: 'Low hooks in from both sides; reels light foes. J: rising cross' },
    { rank: 1, name: 'Lunge', input: 'K', desc: 'Dash in and open the blades in an X.' },
    { rank: 1, name: 'Spiral pursuit', input: 'K J', desc: 'A drifting corkscrew of four cuts round you. J: back into the chain.' },
    { rank: 1, name: 'Fang pounce', input: 'K K', desc: 'Hop off the lunge and chop both blades down together: stagger.' },
    { rank: 1, name: 'Demon Mode', input: 'I (tap)', desc: 'Toggle: drains stamina, 20% faster swings, attacks cost half. No block' },
    { rank: 1, name: 'Demon chain', input: 'Demon: J ×6', desc: 'The chain runs on: a downward cut, then a spin with an upward rip.' },
    { rank: 1, name: 'Demon flurry', input: 'Demon: K', desc: 'Six alternating cuts, advancing. Hits fill the demon gauge.' },
    { rank: 1, name: 'Blade Dance', input: 'Archdemon: hold K', desc: 'Eight cuts and a crossed X (4.2). Light armour. Empties the gauge.' },
    { rank: 1, name: 'Perfect dodge', input: 'L just before a blow', desc: 'Roll ≤0.1 s (demon dash ≤0.175 s) before a hit: +25 stam, +10% speed.' },
    { rank: 1, name: 'Counter flurry', input: 'L (perfect) → J', desc: 'Straight out of a perfect dodge: three cuts at once.' },
    { rank: 1, name: 'Dash slash', input: 'L → J', desc: 'Spring out of the roll and cut through. J: back into the chain.' },
    { rank: 1, name: 'Scissor up-cut', input: '↑J', desc: 'Both blades scissored up past the head, for fliers.' },
    { rank: 1, name: 'Twin spin', input: 'air J', desc: 'Both blades brought through at once: an X opens in front.' },
    { rank: 1, name: 'Crossfall', input: 'air J J', desc: 'After the twin spin: a crossed dive to the floor, 2 hits.' },
    { rank: 1, name: 'Drill', input: 'air ↓J', desc: 'Blades crossed under the feet, twisting: pogo off foes.' },
    { rank: 1, name: 'Twin plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 2, name: 'Dash-through cut', input: 'demon dash → J', desc: 'Cut straight through out of the dash. x1.5 after a perfect dodge.' },
    { rank: 2, name: 'Bloodwheel', input: 'Demon: K J', desc: 'Out of the flurry, a somersault of crimson cuts. J: demon chain 5.' },
    { rank: 2, name: 'Rending cyclone', input: 'Demon: J ×6 → K', desc: 'Two crimson spins and a leaping cross-cut: the demon chain finisher.' },
    { rank: 3, name: 'Blade Dance II', input: 'Archdemon: hold K', desc: 'Three more cuts and a bigger cross-cut finisher.' },
    { rank: 3, name: 'Reversal cut', input: 'L → K', desc: 'Turn out of the roll with a rising double cut. Perfect: silver, x1.5.' },
  ],
}, {
  tw_1: { tags: ['tw_1'], hits: [0.45, 0.45], gap: 60, poise: 6, stam: 8, wind: 100, total: 300, step: 0, fx: 'slash', next: { J: 'tw_2' } },
  tw_2: { tags: ['tw_2'], hits: [0.45, 0.45], gap: 60, poise: 6, stam: 8, wind: 100, total: 300, step: 1, fx: 'slash2', next: { J: 'tw_3', K: 'tw_hook' } },
  tw_3: { tags: ['tw_3'], hits: [0.5, 0.5], gap: 60, poise: 8, stam: 9, wind: 110, total: 300, step: 2, fx: 'slash_up', next: { J: 'tw_4', K: 'tw_skyward' } },
  tw_4: { tags: ['tw_4'], dmg: 1.2, poise: 20, stam: 12, wind: 220, total: 520, step: 3, fin: true, spin: true, next: { J: () => (P.demon ? 'tw_d5' : '@J') } },
  // v14: 2 x 0.35 / 3 x 0.3 (were 2 x 0.5 / 3 x 0.45): Demon J x6 = 5.6 over 1.98 s / 1.2 = 3.4 dmg/s, the plan
  tw_d5: { tags: ['tw_d5', 'tw_1'], hits: [0.35, 0.35], gap: 60, poise: 8, stam: 8, wind: 100, total: 280, step: 4, can: () => P.demon, fx: 'slash', next: { J: 'tw_d6' } },
  tw_d6: { tags: ['tw_d6', 'tw_5'], hits: [0.3, 0.3, 0.3], gap: 55, poise: 10, stam: 10, wind: 100, total: 280, step: 5, fin: true, can: () => P.demon, fx: 'slash3',
    next: { K: () => (P.demon && mvHas(2) ? 'tw_dfin' : '@K') } },
  tw_heavy: { tags: ['tw_heavy'], kind: 'heavy', dmg: 1.1, poise: 15, stam: 12, wind: 200, total: 480, lunge: 60, fx: 'slash3', next: { J: 'tw_spiral', K: 'tw_pounce' } },
  tw_dflurry: { tags: ['tw_dflurry', 'tw_heavy'], kind: 'heavy', hits: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3], gap: 100, poise: 30, stam: 16, wind: 150, total: 800, fin: true, fx: 'slash', fxEach: true, lunge: 20,
    next: { J: () => (P.demon && mvHas(2) ? 'tw_bwheel' : '@J') } },
  tw_khold: { tags: ['tw_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt);
      if (!held.has('heavy')) { mvStart(P.demon ? 'tw_dflurry' : 'tw_heavy'); return 'stop'; }
      if (P.mvT >= 200) { mvStart(mvHas(3) ? 'tw_dance2' : 'tw_dance'); return 'stop'; }
    } } },
  tw_dance: { tags: ['tw_dance', 'tw_dflurry', 'tw_heavy'], kind: 'heavy', hits: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 1.0], gap: 140, poise: 60, stam: 0, wind: 150, total: 1400, fin: true, fxEach: true, fx: 'slash', armor: 0.2,
    can: () => P.arch, on: { start() { flashScreen = Math.max(flashScreen, 0.1); }, end() { P.gauge = 0; P.arch = false; } } },
  tw_dance2: { tags: ['tw_dance2', 'tw_dance', 'tw_dflurry', 'tw_heavy'], kind: 'heavy', rank: 3, hits: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 1.6], gap: 125, poise: 80, stam: 0, wind: 150, total: 1680, fin: true, fxEach: true, fx: 'slash', armor: 0.2,
    can: () => P.arch, on: { start() { flashScreen = Math.max(flashScreen, 0.1); }, end() { P.gauge = 0; P.arch = false; } } },
  tw_demon: { tags: ['tw_demon_on', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 0, wind: 200, total: 200, on: { start() { twDemon(!P.demon); } } },
  tw_cflurry: { tags: ['tw_counter', 'tw_dflurry', 'tw_1'], hits: [0.45, 0.45, 0.45], gap: 60, poise: 15, stam: 8, wind: 80, total: 300, counter: true, fin: true, fx: 'slash3', fxEach: true },
  tw_dashslash: { tags: ['tw_dashslash', 'tw_2'], dmg: 1.0, poise: 10, stam: 8, wind: 100, total: 320, lunge: 30, fx: 'slash2', next: { J: 'tw_2' } },
  // v14: no i-frames of its own (the demon dash before it has them): an attack is never also a dodge; 60 -> 44 px
  tw_dthrough: { tags: ['tw_dthrough', 'tw_dashslash', 'tw_2'], rank: 2, dmg: 1.0, poise: 15, stam: 8, wind: 100, total: 320, lunge: 44, lungeLead: 100, fx: 'slash3',
    on: { update() { if (mvHas(5) && P.mvT < 160) twTrail(); } } },
  tw_air: { tags: ['tw_air'], air: true, hits: [0.45, 0.45], gap: 60, poise: 8, stam: 9, wind: 120, total: 330, spin: true, next: { J: 'tw_crossfall' } },
  // ---- v14 routes
  // J J (pause) J: five alternating stabs, stepping in (pressure, status build-up); J after it: the spin finisher
  tw_barrage: { tags: ['tw_barrage', 'tw_d5', 'tw_1'], hits: [0.22, 0.22, 0.22, 0.22, 0.3], gap: 60, poise: 12, stam: 10, wind: 110, total: 470, step: 2, lunge: 14, reach: 34,   // no slash fx: the stabs draw their own streaks
    next: { J: 'tw_4' } },
  // J J J K: a rising double cut that springs you up ~50 px (light foes pop up with you); J: the twin spin, J: crossfall
  tw_skyward: { tags: ['tw_skyward', 'tw_up'], hits: [0.4, 0.5], gap: 90, poise: 22, stam: 12, wind: 130, total: 460, airOk: true, launch: 230, fx: 'slash_up',
    on: { hitStart(k) { if (k === 0 && P.ground) { P.vy = -250; P.ground = false; P.vx = P.face * 30; for (let i = 0; i < 6; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y - 1, vx: rand(-40, 40), vy: -rand(10, 50), g: 300, life: 0.4, kind: 'dust' }); } } },
    next: { J: () => (P.ground ? '@J' : 'tw_air') } },
  // air J J: hang, open an X, and dive to the floor at a slant (lands planted; counts as an air attack)
  tw_crossfall: { tags: ['tw_crossfall', 'tw_down'], airCount: true, airOk: true, hits: [0.45, 0.55], gap: 120, poise: 18, stam: 10, wind: 130, total: 480, fx: 'slash3', fxEach: true,
    move(dt, A, ax, grav) {
      if (P.ground) { if (!P.twLanded) { P.twLanded = true; shake = Math.max(shake, 3); sfx.land(); spawnFx('dust', P.x + P.face * 8, P.y, P.face); } P.vx *= Math.pow(0.0002, dt); grav(); return; }
      if (P.mvT < 110) { P.vy = Math.min(P.vy, 0) * Math.pow(0.001, dt); P.vx *= Math.pow(0.05, dt); return; }   // the hang
      P.vy = 400; P.vx = P.face * 95;
    },
    on: { start() { P.twLanded = false; } } },
  // ---- v14c: J/K mixes
  // K -> J: out of the lunge, a corkscrew -- two turns with the blades held out like a wheel, drifting forward (4 hits,
  // both sides); J after it rejoins the chain at the rising cross
  tw_spiral: { tags: ['tw_spiral', 'tw_4'], hits: [0.25, 0.25, 0.25, 0.35], gap: 75, poise: 12, stam: 10, wind: 120, total: 480, spin: true, lunge: 24, fx: 'slash', fxEach: true,
    next: { J: 'tw_3' } },
  // K -> K: hop off the lunge with both blades raised and chop them down together (one heavy hit, stagger)
  tw_pounce: { tags: ['tw_pounce', 'tw_5'], kind: 'heavy', dmg: 1.3, poise: 35, stam: 14, wind: 230, total: 600, lunge: 30, lungeLead: 200, airOk: true, fx: 'slash3',
    on: { start() { if (P.ground) { P.vy = -130; P.ground = false; } }, update() { if (P.mvT >= 175 && !P.ground) P.vy = Math.max(P.vy, 420); },   // drop onto the chop
      swing() { shake = Math.max(shake, 3); spawnFx('dust', P.x + P.face * 16, P.y, P.face); } } },
  // J J -> K: sink into a wide stance and hook both blades in from the outside at knee height, crossing (reels light
  // foes); J after it: the rising cross, K: skyward fangs -- J J K J K flows into the air string
  tw_hook: { tags: ['tw_hook', 'tw_3'], kind: 'heavy', hits: [0.45, 0.55], gap: 80, poise: 20, stam: 11, wind: 140, total: 440, step: 2, reel: true, lunge: 12, fx: 'slash2',
    next: { J: 'tw_3' } },
  // Demon K -> J (II): out of the demon flurry, a somersault -- both blades wheel overhead and down in front twice --
  // then J carries on into the demon chain (hit 5)
  tw_bwheel: { tags: ['tw_bwheel', 'tw_d6'], rank: 2, hits: [0.3, 0.3, 0.3], gap: 90, poise: 15, stam: 10, wind: 120, total: 440, airOk: true, lunge: 20, lungeLead: 160, fx: 'slash3', fxEach: true,
    can: () => P.demon, on: { start() { if (P.ground) { P.vy = -150; P.ground = false; } }, update() { if (P.mvT >= 260 && !P.ground) P.vy = Math.max(P.vy, 380); } },   // land on the 3rd cut
    next: { J: 'tw_d5' } },
  // Demon J x6 -> K (II): two crimson spins and a leaping crossed cut; closes the demon chain with stagger
  tw_dfin: { tags: ['tw_dfin', 'tw_d6', 'tw_5'], kind: 'heavy', rank: 2, hits: [0.3, 0.3, 0.3, 0.8], gap: 85, poise: 40, stam: 14, wind: 150, total: 640, fin: true, spin: true, lunge: 18, fx: 'slash', fxEach: true,
    can: () => P.demon, on: { hitStart(k) { if (k === 3) { shake = Math.max(shake, 4); flashScreen = Math.max(flashScreen, 0.05); } } } },
  // L -> K (III): turn out of the roll with a rising double cut; after a perfect dodge: silver, x1.5, 50 poise
  tw_reversal: { tags: ['tw_reversal', 'tw_heavy'], kind: 'heavy', rank: 3, hits: [0.45, 0.6], gap: 90, poise: 18, stam: 10, wind: 110, total: 420, lunge: 20, fx: 'slash_up',
    poiseFn: () => (P.mvO && P.mvO.pd ? 50 : 18) / 2,
    on: { start(A, o) { if (o.pd) { mvAfterimage('#e4ecf8', 0.3, 0.4); mvSpark(P.x + P.face * 12, P.y - 18, 6, '230,236,248', 120); tone(1568, 0.2, 0.05, 'triangle', 1.4); } } } },
  tw_up: { tags: ['tw_up'], up: true, hits: [0.45, 0.45], gap: 60, poise: 8, stam: 9, wind: 140, total: 340 },
  tw_down: { tags: ['tw_down'], down: true, hits: [0.3, 0.3, 0.3], gap: 50, poise: 10, stam: 10, wind: 100, total: 320 },
});
for (const d of Object.values(MV.defs)) if (d.type === 'dual' && !d.air && !d.airCount && !d.loop && d.id !== 'tw_demon' && d.id !== 'tw_skyward') d.next = { ...(d.next || {}), I: '@I' };   // I mid-chain: toggle Demon Mode as it ends
// the keys a blow is counted by: `blow` (one perfect dodge each: a beam's or mist's ticks id_<n> are one blow) and `atk`
// (one stamina refund each: a boss attack's windows share its atkId). Body contact ('c' + id + half-second) is no blow.
let TW_SRC = 0;
function twKeys(id, opt) {
  if (id === undefined || id === null) return null;
  const s = String(id), src = opt && opt.src && typeof opt.src === 'object' ? opt.src : null;
  if (!src && /^c\d/.test(s)) return null;
  const blow = s.replace(/_\d+$/, '');
  if (src && !src.__twk) src.__twk = ++TW_SRC;
  return { blow: (src ? 's' + src.__twk + ':' : '') + blow, atk: src && src.atkId != null ? 'a' + src.__twk + ':' + src.atkId : 'b' + blow };
}
function twPerfect(g, id, opt) {
    // +1: the window is inclusive of its last frame (6 frames at 60 fps = 100.000001 ms)
    const win = (g.kind === 'ddash' ? 175 : 100) + 1, el = g.t !== undefined && P.state === 'roll' && P.dg === g ? g.t : (P.clk - g.start) * 1000;
    if (el > win) return false;
    const k = twKeys(id, opt); if (!k) return false;
    P.pdKeys = P.pdKeys || new Set(); P.pdAtk = P.pdAtk || new Set();
    if (P.pdKeys.has(k.blow)) return false;   // one perfect dodge per blow
    P.pdKeys.add(k.blow); if (P.pdKeys.size > 64) P.pdKeys = new Set([k.blow]);
    g.perfect = true; P.pdT = TW_PD_SECS; MV.pd = (MV.pd || 0) + 1;
    if (!P.pdAtk.has(k.atk)) {   // the stamina (and the mastery call) once per enemy attack
      P.pdAtk.add(k.atk); if (P.pdAtk.size > 64) P.pdAtk = new Set([k.atk]);
      P.st = Math.min(D.maxSt, P.st + 25); MV.pdSt = (MV.pdSt || 0) + 1;
      mvGain('perfect dodge');
    }
    // feedback: a sharp silver chime, a flicker of time, a silver afterimage left behind
    tone(2093, 0.25, 0.06, 'triangle', 1.6); tone(3136, 0.35, 0.04, 'sine', 1.8, 0.04); slowmo = Math.max(slowmo, 0.09);
    const pt = pHas('tw_pdodge') && pSheet().tag('tw_pdodge');   // WA2's silver pose is the ghost left behind; the dodge itself keeps moving
    mvAfterimage('#e4ecf8', 0.45, 0.42, pt ? pt.from : undefined);
    mvSpark(P.x, P.y - 16, 8, '230,236,248', 160);
    return true;
}
const TW_TRAIL = [];
function twTrail() { if (P.ground && (!TW_TRAIL.length || Math.abs(TW_TRAIL[TW_TRAIL.length - 1].x - P.x) > 6)) TW_TRAIL.push({ x: P.x, y: P.y, life: 1.0 }); }
HOOKS.enter.push(() => { TW_TRAIL.length = 0; });

