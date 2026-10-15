// ------------------------------------------------------------------ WM: Dual Blades (A7)  (Staff + Whip: 76_mech_reach.js)
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

