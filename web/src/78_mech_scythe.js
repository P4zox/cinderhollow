// ------------------------------------------------------------------ v15: Scythe (`scythe`, prefix scy_, weapon requiem_scythe)
// docs/WEAPON_REVAMP.md C4 (★★★), write-up docs/v15/scythe.md. The reaper: wide arcs that cut in front AND behind, a
// hooked tip that drags small foes in instead of knocking them away, souls harvested by the far edge, and a hook step
// that swings you round behind the foe.
//  * Souls (max 3, wisps orbiting the blade): a hit whose target sits in the far half of the arc (its near edge past
//    45% of the move's reach, either side) harvests one soul, once per move. They fade one at a time after 15 s
//    without a harvest, and a blow that lands on you scatters one.
//  * hold K: with souls = Reap (spends them all: 1.6 / 2.4 / 3.2, poise 50 / 70 / 90; IV: 2 souls already reap at full
//    strength; V: each Reap that connects restores 2% max HP per soul). With no souls = the charged crescent (full at
//    0.5 s, 2.0). Tapped K = the wide crescent (front + back), K K = twin crescent.
//  * I = Hook step: the blade catches behind the nearest foe ahead (64 px) and you swing round to its back, facing it,
//    invulnerable through the swing (bosses from Mastery III). I -> J (II) = backstab reap. No foe: a short hooking step.
//  * J chain: low reap, high reap, turning harvest (both sides), harvest moon. J J (pause) J (II) = pendulum, J K = hook
//    pull (drags small foes 30 px in), J J K = scything spiral. Up J = rising harvest. L -> J ghost slash, L -> K leg
//    sweep. Air J / air J J crescent dive, air down J pogo, air K grave plunge (the shared plunge with its own fall).
// Globals: scy* / SCY_* (sc* is 24_secrets'). Player state: P.scySouls, P.scyFade, P.scyTok, P.scyHarv, P.scyHook.
if (typeof WTYPE_INFO !== 'undefined' && WTYPE_INFO.scythe) Object.assign(WTYPE_INFO.scythe, { prefix: 'scy_', first: 'scy_1', alt: 'sc_1' });
Object.assign(PCOL, { scy_soul: '186,150,255', scy_pale: '232,224,255' });
const SCY_MAX = 3, SCY_FAR = 0.45, SCY_FADE = 15, SCY_PAUSE = [110, 450];
const SCY_REAP = [0, 1.6, 2.4, 3.2], SCY_REAP_P = [0, 50, 70, 90];
const SCY = { cx: 0, cy: 0, trail: [], fly: [], ready: false };
const SCY_COL = '186,150,255', SCY_HOT = '236,228,255';

function scySouls() { return P.scySouls || 0; }
function scyLarge(t) { const hb = t.hurtbox && t.hurtbox(); return !!(t.cfg && t.cfg.elite) || (hb && (hb.x1 - hb.x0 > 28 || hb.y1 - hb.y0 > 44)); }
function scySmall(t) { return t && !t.prop && !t.boss && t !== boss && t.alive !== false && !(t.cfg && (t.cfg.elite || t.cfg.flying)) && !scyLarge(t); }
// the hooked tip drags a small foe toward you along the floor (either side), stopping `stop` px from you
function scyPull(t, px, stop = 15) {
  if (!scySmall(t)) return;
  const side = t.x >= P.x ? 1 : -1, x0 = t.x, goal = Math.max(Math.abs(t.x - P.x) - px, stop), gx0 = P.x + side * goal;
  if (Math.abs(gx0 - x0) < 1.5) return;
  const dir = Math.sign(gx0 - x0); let gx = x0;
  for (let x = x0; (gx0 - x) * dir > 0; x += dir * 3) { if (solidAtPx(x + dir * 6, t.y - 6) || solidAtPx(x + dir * 6, t.y - 20)) break; gx = x; }
  if ((gx0 - gx) * dir < 3) gx = gx0;
  wfx({ life: 0.18, update() { if (t.alive === false) return false; t.x = x0 + (gx - x0) * Math.min(1, this.t / 0.15); if (t.vx !== undefined) t.vx = 0; } });
}
// where the blade's head is now (the soul orbit centre): the move's measured slash point, else over the shoulder
function scyHead() {
  const A = ATK[P.state];
  if (A && A.mv && A.cls === 'scythe' && P.mvHitK >= 0 && !A.mv.noHit) return [P.x + P.face * A.fxAt[0] * 0.85, P.y + Math.max(-40, A.fxAt[1]) - 2];
  if (P.state === 'roll') return [P.x - P.face * 4, P.y - 16];
  return [P.x + P.face * 17, P.y - 31];
}
function scyGain(x, y) {
  const n = scySouls(); P.scyFade = 0;
  if (n >= SCY_MAX) return;
  P.scySouls = n + 1; MV.scyHarvests = (MV.scyHarvests || 0) + 1;
  SCY.fly.push({ x0: x, y0: y, t: 0, dur: 0.32, to: true });
  tone(587 + n * 196, 0.28, 0.045, 'sine', 1.5); tone(1175 + n * 392, 0.2, 0.025, 'triangle', 1.2, 0.04);
  if (typeof feelFlash === 'function') feelFlash(x, y, 18, SCY_HOT, 0.9, 0.08);
  if (P.scySouls >= scyReapFull()) { SCY.ready = true; mvStar(P.x + P.face * 14, P.y - 30, 4, SCY_HOT, 0.9); }
}
function scyLose(n = 1, why) {
  const s = scySouls(); if (!s) return;
  const k = Math.min(n, s); P.scySouls = s - k;
  for (let i = 0; i < k; i++) { const [hx, hy] = scyHead(); for (let j = 0; j < 5; j++) particles.push({ x: hx + rand(-4, 4), y: hy + rand(-3, 3), vx: rand(-40, 40), vy: -rand(20, 70), life: rand(0.4, 0.7), kind: 'scy_soul' }); }
  if (why === 'hit') tone(392, 0.3, 0.04, 'sine', 0.6);
}
function scyReapFull() { return mvHas(4) ? 2 : 3; }
// the far half of the arc: the target's near edge (on the side it is struck from) past SCY_FAR of the reach
function scyFar(c) {
  const A = c.A, hb = c.hb;
  if (A.up) return P.y - hb.y1 >= -A.ys[0] * SCY_FAR;
  if (A.down) return true;
  const side = (hb.x0 + hb.x1) / 2 >= P.x ? 1 : -1;
  const dist = side > 0 ? hb.x0 - P.x : P.x - hb.x1, reach = side === P.face ? A.reach[1] : -A.reach[0];
  return reach > 8 && dist >= reach * SCY_FAR;
}
// hold K: the crescent starts; still held at 170 ms -> the Reap (souls) or the charge (none)
function scyHoldStart() { P.scyHoldK = held.has('heavy'); }
function scyHolding() { if (!held.has('heavy')) P.scyHoldK = false; return !!P.scyHoldK; }
// J K / J J K with K still held (from the press) at 150 ms and souls in hand: the Reap instead (hold K = Reap everywhere)
function scyHoldReap(spent) { return scyHolding() && P.mvT >= 150 && P.mvT < 200 && scySouls() > 0 && scyReapGo(spent); }
function scyReapGo(spent = 16) {
  const n = scySouls(); if (!n) return false;
  const lv = n >= scyReapFull() ? 3 : n;
  if (!mvStart('scy_reap', { mul: SCY_REAP[lv], souls: n, lv, cost: Math.max(0, 18 - spent) })) return false;
  const [hx, hy] = scyHead();
  for (let i = 0; i < n; i++) SCY.fly.push({ x0: hx + Math.cos(i * 2.1) * 9, y0: hy + Math.sin(i * 2.1) * 4, t: -i * 0.05, dur: 0.26, to: 'blade' });
  P.scySouls = 0; SCY.ready = false;
  tone(196, 0.7, 0.07, 'sawtooth', 0.5); tone(98, 0.8, 0.08, 'sine', 0.7);
  return true;
}

mvRegister('scythe', {
  light: ['scy_1', 'scy_2', 'scy_3', 'scy_4'], K: 'scy_heavy', heavyTag: 'scy_heavy', up: 'scy_up', air: 'scy_air', down: 'scy_down',
  plunge: { dmg: 1.5, poise: 70, stam: 18, fallTag: 'scy_plunge', pk: 'scy_soul' },
  dodge: MV_ROLL,
  rollJ: 'scy_rollj',
  rollK() { const ax = inputX(); if (ax) P.face = ax; return mvStart('scy_rollk'); },
  onJ(ax) {   // J J (pause) J: a press 110-450 ms after the high reap ended = the pendulum (II)
    const c = P.mvChain;
    if (!P.ground || !c || c.id !== 'scy_2' || held.has('up') || !mvHas(2)) return false;
    const ms = (P.clk - c.t) * 1000;
    if (ms < SCY_PAUSE[0] || ms > SCY_PAUSE[1]) return false;
    take('attack'); P.mvChain = null; if (ax) P.face = ax;
    return mvStart('scy_pend') || true;
  },
  onK(ax) { return mvStart('scy_heavy'); },
  onI(ax) {
    if (!P.ground) return false;
    take('parry');
    if (P.st <= 0) { sfx.deny(); return true; }
    if (ax) P.face = ax;
    return mvStart('scy_hstep') || true;
  },
  started(A) { P.scyTok = {}; },
  hitMod(c) { c.far = scyFar(c); },
  onHit(t, info, A, c) {
    if (!t || t.prop || !c) return;
    const d = A.mv;
    if (c.far && !d.noSoul && P.scyHarv !== P.scyTok) { P.scyHarv = P.scyTok; scyGain(info.x, info.y); }
    // the hooked tip: small foes come toward you instead of flying off -- but only as far as the sweet spot (the far half)
    if (c.far && !d.noPull && P.state === d.id) {
      const hb = c.hb, side = (hb.x0 + hb.x1) / 2 >= P.x ? 1 : -1, reach = side === P.face ? A.reach[1] : -A.reach[0];
      scyPull(t, d.pull || 8, reach * 0.5 + (hb.x1 - hb.x0) / 2);
    }
  },
  hurt(c) { if (!c.negate && !c.armor && c.dmg > 0 && !mvIframes()) scyLose(1, 'hit'); },
  tickAll(dt, cur) {
    if (!cur) return;
    if (scySouls() > 0) { P.scyFade = (P.scyFade || 0) + dt; if (P.scyFade >= SCY_FADE) { P.scyFade = SCY_FADE - 2.5; scyLose(1); } }
    // the orbit centre eases toward the blade's head; the wisp trail is sampled from it
    const [hx, hy] = scyHead(), k = Math.min(1, dt * 14);
    if (!SCY.cx || Math.abs(SCY.cx - hx) > 60 || Math.abs(SCY.cy - hy) > 60) { SCY.cx = hx; SCY.cy = hy; } else { SCY.cx += (hx - SCY.cx) * k; SCY.cy += (hy - SCY.cy) * k; }
    for (const f of SCY.fly) f.t += dt;
    if (SCY.fly.length) SCY.fly = SCY.fly.filter(f => f.t < f.dur);
  },
  render() {
    const n = scySouls(), t = P.clk || 0, cx = SCY.cx || P.x, cy = SCY.cy || P.y - 28;
    // the soul wisps: small violet flames on a tilted orbit round the blade's head, each with a short fading tail;
    // the far side of the orbit is dimmer (behind the blade). At Reap strength they burn whiter.
    if (n > 0) {
      const ready = n >= scyReapFull(), fadeK = P.scyFade > SCY_FADE - 3 ? 0.5 + 0.5 * Math.abs(Math.sin(t * 10)) : 1;
      const pos = (i, j) => { const a = t * 3.1 + i * 6.2832 / n - j * 0.16; return [cx + Math.cos(a) * 10, cy + Math.sin(a) * 3.5 - Math.cos(a) * 1.5, Math.sin(a) < 0]; };
      for (let i = 0; i < n; i++) {   // the body on the normal layer (reads on pale walls too): a tail along the orbit, then a small flame
        for (let j = 5; j >= 1; j--) { const [x, y, back] = pos(i, j); g.fillStyle = `rgba(120,86,210,${0.8 * (1 - j / 6) * (back ? 0.6 : 1) * fadeK})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); }
        const [x, y, back] = pos(i, 0), X = Math.round(x), Y = Math.round(y), al = (back ? 0.65 : 1) * fadeK, fl = Math.sin(t * 17 + i * 3) > 0 ? 1 : 0;
        g.fillStyle = `rgba(96,64,176,${al})`; g.fillRect(X - 1, Y, 3, 1); g.fillRect(X, Y + 1, 1, 1); g.fillRect(X + (fl ? 1 : -1), Y - 2, 1, 1);
        g.fillStyle = `rgba(170,136,248,${al})`; g.fillRect(X, Y - 1, 1, 1);
        g.fillStyle = `rgba(${ready ? '255,252,255' : '228,214,255'},${al})`; g.fillRect(X, Y, 1, 1);
      }
      drawGlow(() => {
        const o = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter';
        for (let i = 0; i < n; i++) {
          for (let j = 5; j >= 0; j--) {
            const a = t * 3.1 + i * 6.2832 / n - j * 0.16, x = cx + Math.cos(a) * 10, y = cy + Math.sin(a) * 3.5 - Math.cos(a) * 1.5;
            const back = Math.sin(a) < 0, al = (j ? 0.5 * (1 - j / 6) : 1) * (back ? 0.55 : 1) * fadeK;
            g.fillStyle = `rgba(${j ? SCY_COL : (ready ? SCY_HOT : '214,196,255')},${al})`;
            g.fillRect(Math.round(x), Math.round(y - (j ? 0 : 1)), 1, j ? 1 : 2);
            if (!j) { g.fillStyle = `rgba(${SCY_COL},${0.35 * al})`; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 3, 3); }
          }
        }
        g.globalCompositeOperation = o;
      });
      addLight(cx, cy, 16 + 5 * n, SCY_COL, (0.3 + 0.1 * n) * fadeK);
      if (Math.random() < 0.06 * n) particles.push({ x: cx + rand(-9, 9), y: cy + rand(-3, 3), vx: rand(-6, 6), vy: -rand(8, 22), life: rand(0.4, 0.7), kind: 'scy_soul' });
    }
    // souls in flight: harvested (hit point -> orbit) and spent (orbit -> the blade's arc)
    if (SCY.fly.length) drawGlow(() => {
      const o = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter';
      for (const f of SCY.fly) {
        if (f.t < 0) continue;
        const u = Math.min(1, f.t / f.dur), e = u * u * (3 - 2 * u);
        const [tx, ty] = f.to === 'blade' ? [P.x + P.face * 22, P.y - 30] : [cx, cy];
        for (let j = 0; j < 4; j++) {
          const v = Math.max(0, e - j * 0.08), x = f.x0 + (tx - f.x0) * v, y = f.y0 + (ty - f.y0) * v - Math.sin(v * Math.PI) * 10;
          g.fillStyle = `rgba(${j ? SCY_COL : SCY_HOT},${(1 - j / 4) * (1 - u * 0.3)})`; g.fillRect(Math.round(x), Math.round(y), j ? 1 : 2, j ? 1 : 2);
        }
      }
      g.globalCompositeOperation = o;
    });
    // the charge: a cold violet gleam gathering on the blade, a star when it is full
    if (P.state === 'scy_charge') {
      const f = Math.min(1, (P.mvT || 0) / 500);
      addLight(P.x + P.face * 10, P.y - 26, 10 + 14 * f, SCY_COL, 0.3 + 0.4 * f);
      if (f >= 1) mvStar(P.x + P.face * 16, P.y - 34, 2 + 1.5 * Math.abs(Math.sin(t * 12)), SCY_HOT, 0.9);
    }
    if (P.state === 'scy_reap' && P.mvT < 520) addLight(P.x + P.face * 12, P.y - 20, 30, SCY_COL, 0.7);
    if (P.state === 'scy_hstep' && P.scyHook && P.scyHook.t && P.mvT < 300) {   // the blade hooked behind the foe: a faint line of the haft's pull
      const h = P.scyHook; addLight(h.x, P.y - 18, 14, SCY_COL, 0.4);
    }
  },
  hud(x) {
    // three soul flames; the lit ones flicker, whiter once the Reap is at full strength; a thin line shows the fade
    const n = scySouls(), full = scyReapFull(), t = P.clk || 0;
    for (let i = 0; i < SCY_MAX; i++) {
      const on = i < n, px = ox + (x + 3 + i * 6) * scale, py = oy + 23 * scale, fl = on ? 0.15 * Math.sin(t * 9 + i * 2) : 0;
      vctx.fillStyle = on ? (n >= full ? '#ece4ff' : '#b896ff') : 'rgba(40,34,52,0.85)';
      vctx.beginPath(); vctx.moveTo(px, py - (3.6 + fl) * scale); vctx.quadraticCurveTo(px + 2 * scale, py - 0.6 * scale, px, py + 1.4 * scale);
      vctx.quadraticCurveTo(px - 2 * scale, py - 0.6 * scale, px, py - (3.6 + fl) * scale); vctx.fill();
      if (on) { vctx.fillStyle = 'rgba(255,255,255,0.85)'; vctx.fillRect(px - 0.4 * scale, py - 0.8 * scale, 0.8 * scale, 1.2 * scale); }
    }
    if (n > 0) mvHudBar(x + 1, 26, 16, 0.6, 1 - (P.scyFade || 0) / SCY_FADE, 'rgba(184,150,255,0.6)', 'rgba(0,0,0,0)');
  },
  unlocks: [
    { rank: 2, id: 'scy_pend', name: 'Pendulum', input: 'J J (pause) J', desc: 'Wait a beat after the high reap: out ahead, then back behind you.' },
    { rank: 2, id: 'scy_backstab', name: 'Backstab reap', input: 'I → J', desc: 'Out of the hook step, a reaping cut down its back: 1.6, 40 poise.' },
    { rank: 3, id: 'scy_hbosses', name: 'Grave hook', input: 'I near a boss', desc: 'The hook step catches bosses too: swing round behind them.' },
    { rank: 4, id: 'scy_reap2', name: 'Lean harvest', input: 'hold K (2 souls)', desc: 'Two souls already reap at full strength (3.2, 90 poise).' },
    { rank: 5, id: 'scy_reap3', name: 'Requiem', input: 'hold K (souls)', desc: 'A Reap that connects restores 2% of your max HP for every soul spent.' },
  ],
  combos: [
    { rank: 1, name: 'Low reap · High reap · Turning harvest · Harvest moon', input: 'J J J J', desc: 'Every reap also cuts just behind you. The far edge harvests a soul.' },
    { rank: 1, name: 'Hook pull', input: 'J K', desc: 'Sink the hook and haul: drags small foes 30 px in. J: high reap.' },
    { rank: 1, name: 'Scything spiral', input: 'J J K', desc: 'Three turns of the blade round you, front and back.' },
    { rank: 1, name: 'Wide crescent', input: 'K', desc: 'One huge flat arc that cuts ahead and behind.' },
    { rank: 1, name: 'Twin crescent', input: 'K K', desc: 'Two more crescents, round and back again: 40 poise.' },
    { rank: 1, name: 'Reap', input: 'hold K (souls)', desc: 'Every soul on one great arc: 1.6/2.4/3.2, both sides. Also J / J J.' },
    { rank: 1, name: 'Charged crescent', input: 'hold K (no souls)', desc: 'Hold till the blade gleams (0.5 s), release: 2.0, 50 poise.' },
    { rank: 1, name: 'Hook step', input: 'I', desc: 'Hook the blade behind the foe ahead and swing round to its back.' },
    { rank: 1, name: 'Rising harvest', input: '↑J', desc: 'The blade swept up overhead: lifts small foes, for fliers.' },
    { rank: 1, name: 'Ghost slash', input: 'L → J', desc: 'Out of the roll, a pale cut that leaves your shade behind.' },
    { rank: 1, name: 'Leg sweep', input: 'L → K', desc: 'A low turn at the ankles, both sides: trips small foes.' },
    { rank: 1, name: 'Air arc', input: 'air J', desc: 'A full circle of the blade round you in the air.' },
    { rank: 1, name: 'Crescent dive', input: 'air J J', desc: 'Out of the arc, dive to the floor at a slant behind the blade.' },
    { rank: 1, name: 'Grave pogo', input: 'air ↓J', desc: 'The blade hooked under your feet: pogo off a foe.' },
    { rank: 1, name: 'Grave plunge', input: 'air K', desc: 'Drop blade-first onto the floor or a foe below.' },
    { rank: 2, name: 'Pendulum', input: 'J J (pause) J', desc: 'Out ahead, then back behind you. J: harvest moon.' },
    { rank: 2, name: 'Backstab reap', input: 'I → J', desc: 'Swing round behind the foe and cut into its back: 1.6.' },
    { rank: 3, name: 'Grave hook', input: 'I near a boss', desc: 'The hook step swings you round bosses as well.' },
    { rank: 4, name: 'Lean harvest', input: 'hold K (2 souls)', desc: 'Two souls are enough for a full-strength Reap.' },
    { rank: 5, name: 'Requiem', input: 'hold K (souls)', desc: 'A Reap that connects heals 2% max HP per soul.' },
  ],
}, {
  // ---- the J chain (every reap cuts a little behind you too)
  scy_1: { tags: ['scy_1', 'sc_1'], reach: 44, dmg: 0.9, poise: 10, stam: 10, wind: 160, total: 360, step: 0, back: 12, fx: null, next: { J: 'scy_2', K: 'scy_hook' } },
  scy_2: { tags: ['scy_2', 'sc_up'], reach: 44, dmg: 0.95, poise: 12, stam: 10, wind: 160, total: 360, step: 1, back: 12, fx: null, next: { J: 'scy_3', K: 'scy_spiral' } },
  scy_3: { tags: ['scy_3', 'sc_2'], reach: 44, backReach: 40, hits: [0.65, 0.65], gap: 150, poise: 20, stam: 12, wind: 200, total: 540, step: 2, spin: true, fx: null, next: { J: 'scy_4' } },
  scy_4: { tags: ['scy_4', 'sc_3'], reach: 46, dmg: 1.7, poise: 40, stam: 14, wind: 280, total: 680, step: 3, fin: true, back: 10, fx: null,
    on: { swing() { shake = Math.max(shake, 3); } } },
  // J J (pause) J (II): out ahead, then back behind you; J: harvest moon
  scy_pend: { tags: ['scy_pend', 'sc_2'], reach: 44, backReach: 40, rank: 2, hits: [0.7, 0.7], gap: 170, poise: 24, stam: 12, wind: 180, total: 560, step: 2, spin: true, fx: null, next: { J: 'scy_4' } },
  // J K: sink the hook into the foe and haul -- small foes are dragged 30 px in (and stumble); J: high reap
  scy_hook: { tags: ['scy_hook', 'sc_1'], reach: 46, dmg: 0.8, poise: 20, stam: 12, wind: 200, total: 560, noPull: true, fx: null, next: { J: 'scy_2' },
    on: { start() { scyHoldStart(); }, update() { if (scyHoldReap(12)) return 'stop'; },
      hit(t) { if (scySmall(t)) { scyPull(t, 30, 14); if (t.breakStance && t.state !== 'stagger') { t.breakStance(); if (t.state === 'stagger' && typeof t.t === 'number') t.t = Math.min(t.t, 0.45); } } } } },
  // J J K: three turns of the blade round you
  scy_spiral: { tags: ['scy_spiral', 'sc_2'], reach: 42, backReach: 42, hits: [0.45, 0.45, 0.45], gap: 130, poise: 30, stam: 14, wind: 220, total: 700, step: 2, fin: true, spin: true, fx: null,
    on: { start() { scyHoldStart(); }, update() { if (scyHoldReap(14)) return 'stop'; } } },
  // ---- K: the crescents; hold K = Reap (souls) or the charged crescent (no souls)
  scy_heavy: { tags: ['scy_heavy', 'sc_heavy'], reach: 48, backReach: 42, kind: 'heavy', dmg: 1.3, poise: 30, stam: 16, wind: 280, total: 680, spin: true, lunge: 10, fx: null, next: { K: 'scy_twin' },
    on: { start() { scyHoldStart(); },
      update() { if (scyHolding() && !P.mvO.noHold && P.mvT >= 170 && P.mvT < 270) { if (scySouls() > 0) { if (scyReapGo()) return 'stop'; } else { mvStart('scy_charge', { cost: 0 }); return 'stop'; } } } } },
  scy_twin: { tags: ['scy_twin', 'sc_2'], reach: 46, backReach: 42, kind: 'heavy', hits: [0.8, 0.8], gap: 200, poise: 40, stam: 18, wind: 260, total: 760, spin: true, fin: true, fx: null },
  scy_charge: { tags: ['scy_charge', 'sc_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { start() { P.scyFull = false; },
      update(dt) {
        P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000;
        if (P.mvT >= 500 && !P.scyFull) { P.scyFull = true; sfx.glint(); tone(880, 0.3, 0.04, 'sine', 1.3); }
        if (!held.has('heavy') || P.mvT > 1600) { const f = P.scyFull; P.scyFull = false; if (f) mvStart('scy_charged', { cost: 4, charged: true }); else mvStart('scy_heavy', { cost: 0, t0: 170, noHold: true }); return 'stop'; }
      } } },
  scy_charged: { tags: ['scy_charged', 'sc_heavy'], reach: 50, backReach: 46, kind: 'heavy', dmg: 2.0, poise: 50, stam: 20, wind: 240, total: 720, spin: true, lunge: 12, fin: true, fx: null,
    on: { swing() { shake = Math.max(shake, 4); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 24, P.y - 18, 30, SCY_HOT, 1, 0.1); } } },
  scy_reap: { tags: ['scy_reap', 'sc_heavy'], reach: 52, backReach: 48, kind: 'heavy', dmg: 1, poise: 50, stam: 18, wind: 320, total: 1000, spin: true, lunge: 12, fin: true, noSoul: true, fx: null,
    poiseFn: () => SCY_REAP_P[(P.mvO && P.mvO.lv) || 1],
    on: {
      swing() {
        const lv = (P.mvO && P.mvO.lv) || 1;
        shake = Math.max(shake, 4 + lv); flashScreen = Math.max(flashScreen, 0.04 + 0.03 * lv); sfx.boom && lv >= 3 && sfx.boom();
        tone(1568, 0.5, 0.05, 'triangle', 0.5); tone(392, 0.6, 0.06, 'sine', 0.5);
        for (let i = 0; i < 10 + 6 * lv; i++) { const a = rand(-2.6, 0.2); particles.push({ x: P.x + P.face * Math.cos(a) * 30, y: P.y - 14 + Math.sin(a) * 16, vx: P.face * rand(-30, 60), vy: -rand(20, 70), life: rand(0.4, 0.8), kind: i % 3 ? 'scy_soul' : 'scy_pale' }); }
        if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 22, P.y - 18, 34 + 8 * lv, SCY_HOT, 1.1, 0.12);
      },
      hit(t, info) {
        if (P.scyHealed === P.scyTok) return; P.scyHealed = P.scyTok;
        if (mvHas(5) && !t.prop) { const h = Math.round(D.maxHp * 0.02 * ((P.mvO && P.mvO.souls) || 1)); P.hp = Math.min(D.maxHp, P.hp + h); popup(P.x, P.y - 34, h, '#c8b4ff'); }
      },
    } },
  // ---- I: the hook step (and I -> J, the backstab reap)
  scy_hstep: { tags: ['scy_hstep', 'sc_rollj'], noHit: true, dmg: 0, poise: 0, stam: 14, wind: 120, total: 380, commit: true, keepFace: true, next: { J: 'scy_backstab', K: '@K' },
    on: {
      start() { scyHookAim(); },
      update(dt) { const h = P.scyHook; if (h && h.t && !h.flipped && P.mvT >= 250) { h.flipped = true; P.face = h.side > 0 ? -1 : 1; } },
    },
    move(dt, A, ax, grav) {
      const h = P.scyHook, t = P.mvT;
      if (!h || t < 90) { P.vx *= Math.pow(0.0002, dt); grav(); return; }
      if (t < 300) { const u = Math.min(1, (t - 90) / 210), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2, want = h.x0 + (h.x1 - h.x0) * e; P.vx = (want - P.x) / Math.max(dt, 1e-3); P.vy = Math.min(P.vy, 0); if (Math.random() < 0.5) particles.push({ x: P.x + rand(-4, 4), y: P.y - rand(4, 26), vx: 0, vy: -rand(5, 20), life: 0.3, kind: 'scy_soul' });
        if (h.t && (P.scyGhT = (P.scyGhT || 0) - dt) <= 0) { P.scyGhT = 0.04; mvAfterimage('#8a70d8', 0.24, 0.3); } }   // the reaper's shade left along the swing
      else { if (!h.done) { h.done = true; P.vx = 0; } P.vx *= Math.pow(0.0002, dt); }   // planted where the swing ends
      grav();
    } },
  scy_backstab: { tags: ['scy_backstab', 'sc_up'], reach: 44, rank: 2, dmg: 1.6, poise: 40, stam: 10, wind: 120, total: 480, fin: true, back: 6, fx: null,
    on: { start() { mvAfterimage('#b8a0ff', 0.25, 0.35); }, swing() { tone(1319, 0.2, 0.04, 'triangle', 0.7); } } },
  // ---- up J, roll follow-ups
  scy_up: { tags: ['scy_up', 'sc_up'], up: true, dmg: 1.0, poise: 20, stam: 12, wind: 180, total: 460, launch: 200, fx: null },
  scy_rollj: { tags: ['scy_rollj', 'sc_1'], reach: 44, dmg: 1.0, poise: 14, stam: 12, wind: 140, total: 420, lunge: 24, fx: null, next: { J: 'scy_2' },
    on: { start() { mvAfterimage('#a890e8', 0.4, 0.45); } } },
  scy_rollk: { tags: ['scy_rollk', 'sc_2'], reach: 40, backReach: 40, kind: 'heavy', dmg: 1.1, poise: 30, stam: 14, wind: 200, total: 560, spin: true, fin: true, ys: [-18, 0], reel: true, fx: null },
  // ---- air
  scy_air: { tags: ['scy_air', 'sc_air'], reach: 40, backReach: 40, air: true, dmg: 0.9, poise: 12, stam: 10, wind: 150, total: 380, spin: true, fx: null,
    next: { J: q => (held.has('down') ? 'scy_down' : q.up ? '@J' : 'scy_dive') } },
  scy_dive: { tags: ['scy_dive', 'sc_down'], airCount: true, airOk: true, dmg: 1.2, poise: 20, stam: 12, wind: 150, total: 480, fx: null,
    move(dt, A, ax, grav) {
      if (P.ground) { if (!P.scyLanded) { P.scyLanded = true; shake = Math.max(shake, 3); sfx.land(); spawnFx('dust', P.x + P.face * 10, P.y, P.face); } P.vx *= Math.pow(0.0002, dt); grav(); return; }
      if (P.mvT < 110) { P.vy = Math.min(P.vy, 0) * Math.pow(0.001, dt); P.vx *= Math.pow(0.05, dt); return; }   // the hang
      P.vy = 380; P.vx = P.face * 90;
    },
    on: { start() { P.scyLanded = false; } } },
  scy_down: { tags: ['scy_down', 'sc_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300 },
});
// the hook step's aim: the nearest foe ahead (its near edge within 64 px, roughly level) -- bosses from Mastery III;
// you land 10 px past its far edge. A wall there (or nothing to hook) makes it a short hooking step instead.
function scyHookAim() {
  let best = null, bd = 1e9;
  for (const t of targets()) {
    if (t.prop || t.alive === false) continue;
    const isBoss = t.boss || t === boss || (boss && boss.parts && boss.parts.includes(t));
    if (isBoss && !mvHas(3)) continue;
    const hb = hbOf(t); if (!hb) continue;
    const near = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1, cy = (hb.y0 + hb.y1) / 2;
    if (near < -10 || near > 64 || cy < P.y - 60 || hb.y1 < P.y - 34 || hb.y0 > P.y) continue;
    if (near < bd) { bd = near; best = { t, hb }; }
  }
  const x0 = P.x;
  P.scyHook = { x0, x1: x0 + P.face * 26, side: P.face, t: null };
  if (best) {
    const hb = best.hb, far = P.face > 0 ? hb.x1 + 11 : hb.x0 - 11;
    let ok = !solidAtPx(far, P.y - 6) && !solidAtPx(far, P.y - 20) && solidAtPx(far, P.y + 4);
    for (let x = x0; ok && (far - x) * P.face > 0; x += P.face * 4) if (solidAtPx(x, P.y - 8) || solidAtPx(x, P.y - 24)) ok = false;
    if (ok) { P.scyHook = { x0, x1: far, side: P.face, t: best.t, x: P.face > 0 ? hb.x1 : hb.x0 }; P.mvInv = Math.max(P.mvInv || 0, 0.3); MV.scyHooks = (MV.scyHooks || 0) + 1; }
  }
  if (!P.scyHook.t) {   // nothing to swing round: a short hooking step (no i-frames), stopped by walls
    let x1 = x0; for (let x = x0; Math.abs(x - x0) < 26; x += P.face * 2) { if (solidAtPx(x + P.face * 6, P.y - 8) || solidAtPx(x + P.face * 6, P.y - 24)) break; x1 = x; }
    P.scyHook.x1 = x1;
  }
  sfx.swing(); tone(1047, 0.1, 0.03, 'triangle', 0.6);
  if (P.scyHook.t) { mvAfterimage('#9a80e0', 0.3, 0.4); tone(523, 0.25, 0.04, 'sine', 1.6, 0.08); }
}
HOOKS.enter.push(() => { SCY.fly = []; SCY.cx = 0; });
