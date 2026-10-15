// ------------------------------------------------------------------ WM: Greatsword (A4) + Maul (A5)
// v14 pass (docs/revamp2/heavy.md):
//  * Both: a charge needs a real heave (GS 180 ms, Maul 150 ms) before a tap can release it -- a K tap no longer out-damages
//    the whole weapon. A K pressed during a finisher is dropped by the engine's mash rule, but if you KEEP K HELD it now
//    starts the charge when the move ends (hvHoldEnd) -- holding to pre-charge is never eaten.
//  * Greatsword: lv3 is 800-1400 ms (was 1300) and the pips blink in the last 200 ms before the overcharge; Mastery V's wrath
//    level only on the plain charge (1400-2100 ms) and it overcharges too; one shoulder tackle per charge (50% damage cut).
//    New: J -> K hilt bash (banks the charge), J J J -> K momentum cleave, block -> J retort, tackle -> J leaping wide slash.
//  * Maul: spin / earthshaker decided at one moment (1.4 s: moving = spin, still = earthshaker at V); lv3 window 900-1400;
//    earthshaker shockwave toned down; L -> K starts the charge; the big bounce is a little lower; the brace can be left
//    early once its window has passed. New: brace -> K payback, hold K + J haft jab, double smash -> K third pound, air J J spike.
// ================================================================== Greatsword: one huge hit at a time
// Hold K: level 1 (0-400 ms) 2.0 / 50, level 2 (400-800) 2.85 / 70, level 3 (800-1400) 3.9 / 95; past 1.4 s it overcharges
// back to level 2 (Mastery V, plain charge only: a fourth level, wrath, 1.4-2.1 s: 4.5 + a small flame burst). K within 0.5 s
// of a charged slash: the strong charged slash (x1.25, +4 stam); Mastery III: K after that = the true charged slash (1.5 + 4.9).
// Charging is flinch-proof against hits under 30% max HP (x0.8 damage). I = blade guard (1.2 x dmg stamina, 25% chip, no parry).
const GS_LV = { dmg: [0, 2.0, 2.85, 3.9, 4.5], poise: [0, 50, 70, 95, 110], stam: [0, 28, 32, 36, 40] };
const GS_MIN = 180, GS_OVER = 1400, GS_WRATH_OVER = 2100;
function gsLevel(ms, wrath) {
  if (ms > GS_OVER) return wrath && ms <= GS_WRATH_OVER ? 4 : 2;
  return ms >= 800 ? 3 : ms >= 400 ? 2 : 1;
}
const GS_CHARGES = { gs_charge: 'gs_charged', gs_scharge: 'gs_strong', gs_tcharge: 'gs_true1' };
function gsChargeDef(tags, rel) {
  return { tags, kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: {
      start(A, o) {
        P.gsMs = o.bank || 0; P.gsWrath = rel === 'gs_charged' && !o.roll && mvHas(5); P.gsLv = gsLevel(P.gsMs, P.gsWrath);
        if (!o.resumed) P.gsTackled = false;
      },
      update(dt, A, ax) {
        P.vx *= Math.pow(0.05, dt);
        P.gsMs += dt * 1000; P.charge = P.gsMs / 1000;
        const lv = gsLevel(P.gsMs, P.gsWrath);
        if (lv !== P.gsLv) {   // each level rings in: brighter glint, a pip lights over the head
          if (lv > P.gsLv || lv === 4) { sfx.glint(); tone(660 + lv * 220, 0.25, 0.05, 'triangle', 1.3); if (typeof feelFlash === 'function') feelFlash(P.x, P.y - 34, 30 + lv * 10, GS_GLOW[lv], 1.1, 0.12); if (lv === 3) spawnFx('telegraph', P.x - P.face * 2, P.y - 36, P.face); }
          else { sfx.deny(); }   // overcharged: the glow gutters
          P.gsLv = lv;
        }
        if (peek('roll') && P.st > 0) {   // II: shoulder tackle (once per charge) keeps the charge; otherwise the roll drops it
          take('roll');
          if (mvHas(2) && P.ground && !P.gsTackled) { mvStart('gs_tackle', { resume: A.mv.id, bank: P.gsMs }); return 'stop'; }
          mvDodgeStart(ax); return 'stop';
        }
        const over = P.gsWrath ? 2600 : 2200;   // held far too long: it swings on its own
        if ((!held.has('heavy') && P.gsMs >= GS_MIN) || P.gsMs > over) {
          const q = P.mvQ && P.mvQ.b === 'J' ? P.mvQ : null;   // a J pressed during the heave carries into the release (-> upheaval)
          if (mvStart(P.mvO.roll ? 'gs_rollheavy' : lv === 4 ? 'gs_wrath' : rel, { lv, charged: lv >= 2, bank: P.gsMs }) && q) { P.mvQ = { b: 'J', t: 0, at: P.clk }; P.hvQ = P.mvQ; }
          return 'stop';
        }
      },
    } };
}
const GS_GLOW = ['255,200,120', '255,190,110', '255,150,60', '255,245,215', '255,90,40'];
function gsReleaseDef(tags, mulFn, extra, wind, total, more = {}) {
  return { tags, kind: 'heavy', dmg: 1.8, poise: 50, wind, total, fin: true, fx: 'heavy', lunge: 16, slam: true, chainK: 500,
    stam: o => GS_LV.stam[o.lv || 1] + extra,
    dmgFn: () => GS_LV.dmg[P.mvLv || 1] * mulFn(), poiseFn: () => GS_LV.poise[P.mvLv || 1],
    on: { start() { if (P.mvLv === 4) { sfx.fire(); flashScreen = Math.max(flashScreen, 0.08); } },
          hit(t, info) { if (P.mvLv === 4 && !P.gsBurst) { P.gsBurst = true; mvShockwave({ r: 40, dmg: 0.4, poise: 20, fire: true, pk: 'fire', shake: 5, onHit: q => q !== t && mvBurn(q, 4, D.light * 0.1) }); mvBurn(t, 4, D.light * 0.1); } },
          end() { P.gsBurst = false; } },
    ...more };
}
mvRegister('greatsword', {
  light: ['gs_1', 'gs_2', 'gs_3'], K: 'gs_charge', heavyTag: 'gs_charged', up: 'gs_up', air: 'gs_air', down: 'gs_down',
  plunge: { dmg: 1.8, poise: 90, stam: 20 },
  dodge: { stam: 18, total: 520, inv: 0.28, dist: 70, tags: ['roll'] },
  rollJ: 'gs_1',
  rollK(g) { return mvStart('gs_charge', { bank: 200, roll: true }); },   // L -> K: the rolling heavy banks 200 ms of charge
  counter() { return 'gs_retort'; },   // J within 0.7 s of a blocked blow (the guard's counter window)
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
    if (peek('heavy') && P.st > 0) { take('heavy'); P.guardKind = null; if (mvHas(4)) mvStart('gs_tackle', { resume: 'gs_charge', bank: 400, guard: true }); else mvStart('gs_charge'); return true; }   // IV: guard tackle
    if (peek('attack') && P.st > 0) { take('attack'); P.guardKind = null; if (!(P.gcT > 0 && mvCounter())) mvStartLight(); return true; }   // a blow just blocked: the retort
    if (peek('roll') && P.st > 0) { take('roll'); P.guardKind = null; mvDodgeStart(ax); return true; }
    if (P.state === 'guard' && !held.has('parry')) { P.guardKind = null; setP('idle', 'idle', true); return true; }
    return true;
  },
  blockPose() { setP('block', pHas('gs_guard') ? 'gs_guard' : 'parry', false); P.anim.i = Math.min(1, P.anim.n - 1); P.anim.speed = 0.6; },
  guardCost(dmg) { return { cost: 1.2 * dmg * (charmOn('c_aegis') ? 0.7 : 1), chip: 0.25 * dmg, push: 150, counterT: 0.7 }; },
  hurt(c) {
    const A = ATK[P.state];
    if (A && A.mv && A.mv.charge && c.dmg < D.maxHp * 0.3) { c.armor = true; c.dmg *= 0.8; }   // flinch-proof charge
  },
  started() { hvStarted(); },
  tick() { hvTick(); },
  interrupted() { P.guardKind = null; },
  render() {
    const A = ATK[P.state]; if (!A || !A.mv || !A.mv.charge) return;
    // the charge glow: dim ember (1), orange (2), white-gold (3), red wrath (4); flickers when overcharged; the pips blink fast
    // in the last 200 ms before an overcharge (release now)
    const lv = P.gsLv || 1, over = P.gsMs > GS_OVER && lv !== 4, fl = over ? 0.5 + 0.5 * Math.sin(P.clk * 40) : 1;
    const edge = lv === 3 ? GS_OVER : lv === 4 ? GS_WRATH_OVER : 0, warn = edge && P.gsMs > edge - 200 && Math.sin(P.clk * 50) < 0;
    addLight(P.x - P.face * 4, P.y - 26, 18 + lv * 10, GS_GLOW[lv], (0.45 + lv * 0.18) * fl);
    if (Math.random() < 0.25 + lv * 0.15) particles.push({ x: P.x + rand(-10, 10), y: P.y - rand(4, 34), vx: 0, vy: -rand(20, 60), life: 0.4, kind: lv >= 4 ? 'fire' : lv >= 3 ? 'gold' : 'ember' });
    for (let i = 1; i <= 3; i++) {   // three pips over the head
      g.fillStyle = i <= Math.min(3, lv) && !warn ? `rgba(${GS_GLOW[Math.min(lv, 4)]},${0.9 * fl})` : 'rgba(40,34,44,0.7)';
      g.fillRect(Math.round(P.x - 7 + (i - 1) * 6), Math.round(P.y - 40), 3, 3);
    }
  },
  unlocks: [
    { rank: 2, id: 'gs_tackle', name: 'Shoulder tackle', input: 'L while charging', desc: "Once per charge: an unflinching tackle, half damage taken, charge kept." },
    { rank: 3, id: 'gs_true1', name: 'True Charged Slash', input: 'K after a strong charged slash', desc: 'A two-part slash: 1.5 + 4.9 at full charge.' },
    { rank: 3, id: 'gs_leap', name: 'Leaping wide slash', input: 'tackle → J', desc: 'Cash the charge in at once: a bounding sweep, 2.0 / 2.4 / 2.8.' },
    { rank: 2, id: 'gs_split', name: 'Earthsplitter', input: 'J J J → K → K', desc: 'Plough the buried blade forward and rip it out level (2.4).' },
    { rank: 4, id: 'gs_guardtackle', name: 'Guard tackle', input: 'block → K', desc: 'Tackle out of a block straight into a level 2 charge.' },
    { rank: 5, id: 'gs_wrath', name: 'Wrath charge', input: 'hold past level 3', desc: 'A 4th level (1.4-2.1 s) instead of overcharging: 4.5 + a flame burst.' },
  ],
  combos: [
    { rank: 1, name: 'Light chain', input: 'J J J', desc: 'Overhead hack, wide sweep, rising spin that lifts small foes.' },
    { rank: 1, name: 'Hilt bash', input: 'J → K  /  J J → K', desc: 'A pommel shove. Keep K held: the charge goes on from level 2.' },
    { rank: 1, name: 'Momentum cleave', input: 'J J J → K', desc: 'The spin rolls on into a full overhead cleave (2.6).' },
    { rank: 1, name: 'Turning sweep', input: 'J → K → J', desc: 'Off the hilt bash, the body wheels round in a flat sweep (2.0).' },
    { rank: 1, name: 'Charged slash', input: 'hold K', desc: 'Release on a pip: 2.0 / 2.85 / 3.9. Past 1.4 s it overcharges.' },
    { rank: 1, name: 'Upheaval', input: 'charged slash → J', desc: 'Wrench the buried blade up out of the floor (1.8, lifts). J: spin.' },
    { rank: 1, name: 'Strong charged slash', input: 'charged slash → hold K', desc: 'The same levels, ×1.25.' },
    { rank: 1, name: 'Keep charging', input: 'hold K through a swing', desc: 'Keep K held as a swing ends and the next charge starts at once.' },
    { rank: 1, name: 'Blade guard', input: 'hold I', desc: 'Block frontal blows: stamina and 25% chip, no parry.' },
    { rank: 1, name: 'Retort', input: 'block a blow → J', desc: 'Within 0.7 s of a block: the blade torn up out of the floor (1.8).' },
    { rank: 1, name: 'Rolling heavy', input: 'L → hold K', desc: 'A charged slash out of the roll, 200 ms already banked.' },
    { rank: 1, name: 'Great arc', input: '↑J', desc: 'One arc from the floor to the sky, for fliers.' },
    { rank: 1, name: 'Air cleave', input: 'air J', desc: 'Hangs a beat at the top, then cleaves down.' },
    { rank: 1, name: 'Two-handed plunge', input: 'air ↓J', desc: 'Pogo off foes and spikes (wide).' },
    { rank: 1, name: 'Earth plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 2, name: 'Shoulder tackle', input: 'hold K → L', desc: 'Once per charge: shoulder through a blow and keep charging.' },
    { rank: 2, name: 'Earthsplitter', input: 'J J J → K → K', desc: 'Plough the buried blade forward and rip it out level (2.4).' },
    { rank: 3, name: 'True charged slash', input: 'strong slash → hold K', desc: 'A rising backhand, then 4.9 at full charge.' },
    { rank: 3, name: 'Leaping wide slash', input: 'hold K → L → J', desc: 'Tackle, then cash the charge in at once with a bounding sweep.' },
    { rank: 4, name: 'Guard tackle', input: 'block → K', desc: 'Shoulder out of the guard into a level 2 charge.' },
    { rank: 5, name: 'Wrath', input: 'hold K past level 3', desc: 'A red fourth level (1.4-2.1 s): 4.5 and a small flame burst.' },
  ],
}, {
  gs_1: { tags: ['gs_1'], dmg: 1.45, poise: 32, stam: 20, wind: 350, total: 820, step: 0, fx: 'heavy', lunge: 14, next: { J: 'gs_2', K: 'gs_bash' } },
  gs_2: { tags: ['gs_2'], dmg: 1.5, poise: 32, stam: 20, wind: 350, total: 820, step: 1, box: [-22, 44, -42, 0], fx: 'slash_up', next: { J: 'gs_3', K: 'gs_bash' } },
  gs_3: { tags: ['gs_3'], dmg: 1.8, poise: 45, stam: 22, wind: 400, total: 920, step: 2, fin: true, launch: 180, fx: 'slash3', next: { K: 'gs_mcleave' } },
  // J (J) -> K: a pommel shove; K still held as it ends = the charge goes on from 400 ms (level 2)
  gs_bash: { tags: ['gs_bash', 'gs_tackle', 'gs_1'], kind: 'heavy', dmg: 0.8, poise: 45, stam: 12, wind: 220, total: 580, lunge: 10, fx: null, next: { J: 'gs_turn' },
    on: { swing() { spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 22, P.y - 21, P.face); },
          end() { if (held.has('heavy') && P.ground && P.st > 0) mvStart('gs_charge', { bank: 400 }); } } },
  // J J J -> K: the finisher's spin rolls on into a full overhead cleave
  gs_mcleave: { tags: ['gs_mcleave', 'gs_heavy'], kind: 'heavy', dmg: 2.6, poise: 70, stam: 26, wind: 430, total: 980, fin: true, slam: true, lunge: 14, fx: 'heavy',
    next: { K: q => (mvHas(2) ? (mvHeldK(q) ? '@K' : 'gs_split') : '@K') } },   // II: tap K = earthsplitter; K held = a fresh charge
  // v14c -- charged slash (any release but the true one) -> J: upheaval, the buried blade wrenched up; J again: the rising spin
  gs_heave: { tags: ['gs_heave', 'gs_up', 'gs_2'], kind: 'heavy', dmg: 1.8, poise: 55, stam: 20, wind: 440, total: 1000, launch: 200, reach: 40, fx: 'slash_up',
    on: { start() { spawnFx('ground_crack', P.x + P.face * 24, P.y, P.face); } }, next: { J: 'gs_3' } },
  // v14c -- J (J) -> K -> J: off the hilt bash's shoulder, a full turning sweep that covers the back too
  gs_turn: { tags: ['gs_turn', 'gs_3'], kind: 'heavy', dmg: 2.0, poise: 55, stam: 22, wind: 420, total: 1000, back: 20, fin: true, fx: 'slash3' },
  // v14c, II -- J J J -> K -> K (tap): earthsplitter, the buried slab ploughed forward through the floor and ripped out level
  gs_split: { tags: ['gs_split', 'gs_heavy'], kind: 'heavy', rank: 2, dmg: 2.4, poise: 85, stam: 26, wind: 520, total: 1200, lunge: 20, dash: true, fin: true, fx: 'heavy',
    on: { update() { if (P.mvT < 480 && Math.random() < 0.5) particles.push({ x: P.x + P.face * rand(18, 30), y: P.y - 1, vx: P.face * rand(10, 50), vy: -rand(20, 70), g: 320, life: 0.4, kind: 'dust' }); },
          swing() { spawnFx('ground_crack', P.x + P.face * 30, P.y, P.face); shake = Math.max(shake, 5); } } },
  // block a blow -> J (0.7 s): the blade torn up out of the floor
  gs_retort: { tags: ['gs_retort', 'gs_up', 'gs_2'], kind: 'heavy', counter: true, dmg: 1.8, poise: 60, stam: 14, wind: 170, total: 640, fin: true, fx: 'slash_up', reach: 38 },
  gs_charge: gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_charged'),
  gs_charged: gsReleaseDef(['gs_charged', 'gs_heavy'], () => 1, 0, 250, 620, { next: { K: 'gs_scharge', J: 'gs_heave' } }),
  gs_wrath: gsReleaseDef(['gs_wrath', 'gs_charged', 'gs_heavy'], () => 1, 0, 280, 800, { rank: 5, next: { K: 'gs_scharge', J: 'gs_heave' } }),
  gs_rollheavy: gsReleaseDef(['gs_rollheavy', 'gs_charged', 'gs_heavy'], () => 1, 0, 280, 750, { next: { K: 'gs_scharge', J: 'gs_heave' } }),
  gs_scharge: gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_strong'),
  gs_strong: gsReleaseDef(['gs_strong', 'gs_heavy'], () => 1.25, 4, 280, 700, { next: { K: q => (mvHas(3) ? 'gs_tcharge' : '@K'), J: 'gs_heave' } }),
  gs_tcharge: { ...gsChargeDef(['gs_charge_hold', 'gs_heavy'], 'gs_true1'), rank: 3 },
  gs_true1: { tags: ['gs_true1', 'gs_heavy'], kind: 'heavy', rank: 3, dmg: 1.5, poise: 40, wind: 280, total: 520, fx: 'heavy', lunge: 20, stam: o => GS_LV.stam[o.lv || 1] + 8,
    on: { end() { const lv = P.mvLv; mvStart('gs_true2', { lv, cost: 0, charged: true }); } } },
  gs_true2: { tags: ['gs_true2', 'gs_heavy'], kind: 'heavy', rank: 3, dmg: 4.5, poise: 95, stam: 0, wind: 310, total: 880, fin: true, slam: true, fx: 'heavy', lunge: 24,
    dmgFn: () => 4.5 * GS_LV.dmg[Math.min(3, P.mvLv || 3)] / 3.6, poiseFn: () => GS_LV.poise[Math.min(3, P.mvLv || 3)] * 1.2 },
  // II: L while charging, once per charge (the 2nd L is a plain roll). J during it (III): the leaping wide slash
  gs_tackle: { tags: ['gs_tackle', 'sh_heavy', 'gs_1'], rank: 2, dmg: 0.6, poise: 40, stam: 10, wind: 120, total: 300, lunge: 40, lungeLead: 120, armor: true, dmgTaken: 0.5, box: [-2, 26, -32, -2],
    can: o => !o.guard || mvHas(4),
    onQueue(q) { if (q.b === 'J') P.mvO.leap = true; },
    on: { start() { P.gsTackled = true; },
      end(A) {
        const o = P.mvO, lv = gsLevel(o.bank || 0, false);
        if (o.leap && mvHas(3) && P.st > 0 && mvStart('gs_leap', { lv, charged: lv >= 2 })) return;
        if (held.has('heavy')) mvStart(o.resume || 'gs_charge', { bank: o.bank, resumed: true });
        else mvStart(GS_CHARGES[o.resume] || 'gs_charged', { lv: gsLevel(o.bank || 0, P.gsWrath), charged: true });
      } } },
  gs_leap: { tags: ['gs_leap', 'gs_3'], kind: 'heavy', rank: 3, dmg: 2.0, poise: 70, stam: 20, wind: 310, total: 840, fin: true, lunge: 24, dash: true, fx: 'slash3', back: 14,
    dmgFn: () => 1.6 + 0.4 * (P.mvLv || 1) },
  gs_air: { tags: ['gs_air'], air: true, hang: true, dmg: 1.45, poise: 40, stam: 16, wind: 250, total: 640 },
  gs_up: { tags: ['gs_up'], up: true, dmg: 1.3, poise: 35, stam: 16, wind: 280, total: 640 },
  gs_down: { tags: ['gs_down'], down: true, dmg: 1.1, poise: 45, stam: 12, wind: 150, total: 430, box: [-16, 18, -16, 26] },
});

// ---- both heavies: K held through the end of a swing starts the charge (the engine drops a K pressed early in a finisher)
function hvStarted() { P.hvQ = null; P.hvPrevAt = P.hvMvAt ?? P.clk; P.hvMvAt = P.clk; }   // (a K pressed in the move before, still held, counts too)
function hvTick() { const h = held.has('heavy'); if (h && !P.hvKWas) P.hvKAt = P.clk; P.hvKWas = h; }
function hvHoldEnd(type, chargeId) {
  for (const d of Object.values(MV.defs)) {
    if (d.type !== type || d.loop) continue;
    const on = d.on = d.on || {}, end0 = on.end, q0 = d.onQueue;
    d.onQueue = (q, A) => { P.hvQ = q; if (q0) q0(q, A); };
    on.end = A => {
      if (end0) end0(A);
      if (P.state !== d.id || P.hvQ || !P.ground || P.st <= 0 || !held.has('heavy') || !(P.hvKAt >= P.hvPrevAt)) return;
      mvStart(chargeId);
    };
  }
}
hvHoldEnd('greatsword', 'gs_charge');

// ================================================================== Maul: the stunner
// Hold K to walk-charge at 60% speed: under 450 ms = charged upswing, 450-900 = double smash, 900-1400 released = big smash;
// kept held to 1.4 s = spinning bludgeon (release = spin finisher), or at Mastery V standing still, the earthshaker.
// Maul hits fill stance x1.6 (x1.2 more high on the body). I = brace (600 ms: no flinch, half damage; K after a blow = payback).
// Mastery: charge step + third pound (II), Big Bang (III), steered spin + hammer spike (IV), earthshaker (V).
const ML_MIN = 150, ML_SPIN = 1400;
function mlLevel(ms) { return ms >= 900 ? 3 : ms >= 450 ? 2 : 1; }
function mlRelease(lv) { return lv === 1 ? 'ml_upswing' : lv === 2 ? 'ml_double' : 'ml_bigsmash'; }
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
  dodge: { stam: 16, total: 460, inv: 0.28, dist: 72, tags: ['roll'], kAt: 280 },
  rollJ: 'ml_rollswing',
  rollK() { return P.ground && mvStart('ml_charge'); },   // L -> K: straight into the walk-charge (once the roll's i-frames are spent)
  // II: after a charge step the charge picks up where it was if K is still held
  dodgeUpdate(dt, g) { if (g.t >= g.total && g.bank !== undefined && held.has('heavy') && P.ground) { P.dg = null; mvStart('ml_charge', { bank: g.bank }); return true; } },
  onI(ax) {
    if (!P.ground || P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax; spend(15);
    P.braceT = 0; P.braceEnd = 0.75; P.braceAbs = false; setP('brace', pHas('ml_brace') ? 'ml_brace' : 'sh_guard', false);
    sfx.block(); return true;
  },
  hurt(c) {
    if (P.state === 'brace' && P.braceT <= 0.6 && !c.negate) {   // brace: the blow lands but can't move you
      c.armor = true; spend(0.5 * c.dmg); c.dmg *= 0.5; P.braceHit = 0.25;   // 15 on raising it + 0.5 x dmg per blow
      P.braceAbs = true; P.braceEnd = Math.max(P.braceEnd || 0.75, P.braceT + 0.4);   // K now: payback (0.4 s at least)
      sfx.block(); shake = Math.max(shake, 3); spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 10, P.y - 18, P.face);
    }
  },
  poiseMod(t, poise, A, y) {   // the stun: x1.6, and x1.2 more on the upper half of the body
    if (!t || t.prop) return poise;
    const hb = t.hurtbox && t.hurtbox(); const high = hb && y < (hb.y0 + hb.y1) / 2;
    return poise * (A && A.mv && A.mv.stun || 1.6) * (high ? 1.2 : 1);
  },
  onHit(t) { mlStunFx(t); },
  started() { hvStarted(); },
  tick() { hvTick(); },
  interrupted() {},
  render() {
    const A = ATK[P.state];
    if (P.state === 'ml_charge') {
      const lv = mlLevel(P.mlMs || 0), warn = lv === 3 && P.mlMs > ML_SPIN - 200 && Math.sin(P.clk * 50) < 0;   // blink: spin / quake next
      addLight(P.x + P.face * 4, P.y - 30, 18 + lv * 9, ML_GLOW[lv], 0.45 + lv * 0.18);
      if (Math.random() < 0.2 + lv * 0.15) particles.push({ x: P.x + P.face * rand(-4, 12), y: P.y - rand(20, 38), vx: 0, vy: -rand(20, 50), life: 0.4, kind: lv >= 3 ? 'gold' : 'ember' });
      for (let i = 1; i <= 3; i++) { g.fillStyle = i <= lv && !warn ? `rgba(${ML_GLOW[lv]},0.9)` : 'rgba(40,34,44,0.7)'; g.fillRect(Math.round(P.x - 7 + (i - 1) * 6), Math.round(P.y - 40), 3, 3); }
    }
    if (P.state === 'brace') addLight(P.x + P.face * 6, P.y - 16, 22, '255,220,170', P.braceHit > 0 ? 1 : P.braceAbs ? 0.7 : 0.45);
    if (A && A.mv && A.mv.id === 'ml_spin') addLight(P.x, P.y - 16, 30, '255,190,110', 0.6);
  },
  unlocks: [
    { rank: 2, id: 'ml_chargestep', name: 'Charge step', input: 'L while charging', desc: 'Roll without losing the charge.' },
    { rank: 2, id: 'ml_pound', name: 'Third pound', input: 'double smash → K', desc: 'A hop and a third blow into the same spot (1.6, heavy stun).' },
    { rank: 2, id: 'ml_backslam', name: 'Backswing slam', input: 'J → K → K', desc: 'Off the side blow, all the way round into an overhead slam (2.0).' },
    { rank: 3, id: 'ml_bb1', name: 'Big Bang', input: 'J J J → K K K K', desc: 'A 4-hit chain: 1.0, 1.0, 1.2, 3.0 (stun ×2).' },
    { rank: 4, id: 'ml_steer', name: 'Steered spin', input: 'while spinning', desc: 'Steer the spin; each spin does 0.6.' },
    { rank: 4, id: 'ml_spike', name: 'Hammer spike', input: 'air J J', desc: 'A second air blow that spikes small foes into the ground.' },
    { rank: 5, id: 'ml_quake', name: 'Earthshaker', input: 'hold K 1.4 s, standing still', desc: 'The overcharge slammed down: a 56 px shockwave (1.0, stuns).' },
  ],
  combos: [
    { rank: 1, name: 'Light chain', input: 'J J J', desc: 'Two overhead smashes, then a golf-swing upswing that lifts small foes.' },
    { rank: 1, name: 'Side blow', input: 'J → K  /  J J → K (tap)', desc: 'A flat hook that knocks small foes aside. J after it: the upswing.' },
    { rank: 1, name: 'Walk-charge', input: 'hold K', desc: 'Walk at 60% while charging. Release: upswing / double / big smash.' },
    { rank: 1, name: 'Hammer drop', input: 'K (upswing) → J', desc: 'The raised hammer comes straight down (1.4). J again: the upswing.' },
    { rank: 1, name: 'Spinning bludgeon', input: 'hold K 1.4 s (moving)', desc: 'Up to 4 spins (0.5 each); let go for the 2.0 spin finisher.' },
    { rank: 1, name: 'Haft jab', input: 'hold K → J', desc: 'Once per charge: a lunging jab (0.7) that keeps the charge going.' },
    { rank: 1, name: 'Keep charging', input: 'hold K through a swing', desc: 'Keep K held as a swing ends and the walk-charge starts at once.' },
    { rank: 1, name: 'Brace', input: 'I', desc: '0.6 s: blows can\'t flinch you and do half damage.' },
    { rank: 1, name: 'Payback', input: 'brace a blow → K', desc: 'The braced head torn up into an uppercut (2.0, stuns ×2).' },
    { rank: 1, name: 'Rolling swing', input: 'L → J', desc: 'A low-to-high sweep out of the roll.' },
    { rank: 1, name: 'Rolling charge', input: 'L → hold K', desc: 'Come out of the roll already charging.' },
    { rank: 1, name: 'Rising hammer', input: '↑J', desc: 'An upward blow for fliers.' },
    { rank: 1, name: 'Hammer spin', input: 'air J', desc: 'A spinning blow in the air.' },
    { rank: 1, name: 'Ground pound', input: 'air ↓J', desc: 'Pogo with a big bounce.' },
    { rank: 1, name: 'Meteor plunge', input: 'air K', desc: 'A falling slam with a small shockwave.' },
    { rank: 2, name: 'Charge step', input: 'hold K → L', desc: 'Roll without losing the charge.' },
    { rank: 2, name: 'Third pound', input: 'double smash → K', desc: 'A hop and a third blow into the same spot (1.6).' },
    { rank: 2, name: 'Backswing slam', input: 'J → K → K', desc: 'Off the side blow, all the way round into an overhead slam (2.0).' },
    { rank: 3, name: 'Big Bang', input: 'J J J → K K K K', desc: 'Hook, backhand, uppercut, then a leaping 3.0 that stuns ×2.' },
    { rank: 4, name: 'Steered spin', input: 'spin + ← / →', desc: 'Steer the spinning bludgeon; each spin deals 0.6.' },
    { rank: 4, name: 'Hammer spike', input: 'air J J', desc: 'Spike small foes into the ground and bounce off.' },
    { rank: 5, name: 'Earthshaker', input: 'hold K 1.4 s, standing still', desc: 'Slam the overcharge down: a shockwave both ways (1.0, stuns).' },
  ],
}, {
  ml_1: { tags: ['ml_1', 'gs_1'], dmg: 1.2, poise: 40, stam: 18, wind: 260, total: 620, step: 0, reach: 34, fx: 'heavy', next: { J: 'ml_2', K: q => (mvHeldK(q) ? '@K' : 'ml_side') } },
  ml_2: { tags: ['ml_2', 'gs_2'], dmg: 1.25, poise: 40, stam: 18, wind: 260, total: 620, step: 1, reach: 34, fx: 'heavy', next: { J: 'ml_3', K: q => (mvHeldK(q) ? '@K' : 'ml_side') } },
  // v14c -- J (J) -> K tap (K held = the walk-charge): side blow, a flat hook that knocks small foes aside. J: upswing; K (II): backswing slam
  ml_side: { tags: ['ml_side', 'ml_bb1', 'gs_1'], kind: 'heavy', dmg: 1.15, poise: 55, stam: 18, wind: 240, total: 660, reach: 36, back: 10, reel: true, fx: 'heavy',
    on: { hit(t) { if (t && !t.boss && !t.prop && !(t.cfg && t.cfg.elite) && t.vx !== undefined) t.vx = P.face * 160; } },
    next: { J: 'ml_3', K: q => (mvHas(2) ? (mvHeldK(q) ? '@K' : 'ml_backslam') : '@K') } },
  ml_backslam: { tags: ['ml_backslam', 'ml_bigsmash', 'gs_heavy'], kind: 'heavy', rank: 2, dmg: 2.0, poise: 90, stam: 26, wind: 320, total: 820, reach: 38, fin: true, slam: true, fx: 'heavy' },
  // v14c -- K (upswing) -> J: hammer drop, the raised hammer brought straight down on whatever went up. J: upswing
  ml_drop: { tags: ['ml_drop', 'ml_1', 'gs_1'], kind: 'heavy', dmg: 1.4, poise: 60, stam: 18, wind: 220, total: 600, reach: 36, fx: 'heavy',
    on: { hit(t) { if (t && !t.boss && !t.prop && !(t.cfg && t.cfg.elite) && t.vy !== undefined && t.vy < 0) t.vy = 260; } },
    next: { J: 'ml_3' } },
  ml_3: { tags: ['ml_3', 'gs_3'], dmg: 1.6, poise: 70, stam: 22, wind: 300, total: 720, step: 2, reach: 34, fin: true, launch: 200, fx: 'slash_up', next: { K: q => (mvHas(3) ? 'ml_bb1' : '@K') } },
  ml_charge: { tags: ['ml_charge_walk', 'ml_charge_idle', 'gs_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    move(dt, A, ax) {},
    on: {
      start(A, o) { P.mlMs = o.bank || 0; P.mlLv = mlLevel(P.mlMs); if (!o.resumed) P.mlJabbed = false; },
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
        // J while charging: the haft jab, once per charge (the charge is kept)
        if (peek('attack') && !P.mlJabbed && P.st > 0) { take('attack'); if (mvStart('ml_jab', { bank: P.mlMs })) return 'stop'; }
        // kept held to 1.4 s: moving = the spin; standing still at Mastery V = the earthshaker (else the spin too)
        if (held.has('heavy') && P.mlMs >= ML_SPIN) { mvStart(mvHas(5) && !ax ? 'ml_quake' : 'ml_spin'); return 'stop'; }
        if (!held.has('heavy') && P.mlMs >= ML_MIN) { mvStart(mlRelease(lv), { charged: lv >= 2 }); return 'stop'; }
      },
    } },
  ml_upswing: { tags: ['ml_upswing', 'gs_3'], kind: 'heavy', dmg: 1.6, poise: 50, stam: 24, wind: 200, total: 520, reach: 36, launch: 200, fx: 'slash_up', next: { J: 'ml_drop' } },
  // II: double smash -> K (tap): a third pound; K kept held as it ends = a fresh charge instead
  ml_double: { tags: ['ml_double', 'gs_1'], kind: 'heavy', hits: [1.2, 1.2], gap: 360, poise: 110, stam: 28, wind: 180, total: 900, reach: 36, fin: true, slam: true, fx: 'heavy', fxEach: true,
    next: { K: q => (mvHas(2) ? (mvHeldK(q) ? '@K' : 'ml_pound') : '@K') } },
  ml_pound: { tags: ['ml_pound', 'ml_bigsmash', 'gs_heavy'], kind: 'heavy', rank: 2, dmg: 1.6, poise: 80, stam: 22, wind: 260, total: 700, reach: 38, fin: true, slam: true, fx: 'heavy' },
  ml_bigsmash: { tags: ['ml_bigsmash', 'gs_heavy'], kind: 'heavy', dmg: 3.0, poise: 90, stam: 32, wind: 300, total: 750, reach: 38, fin: true, slam: true, fx: 'heavy' },
  ml_quake: { tags: ['ml_quake', 'ml_bigsmash', 'gs_heavy'], kind: 'heavy', rank: 5, dmg: 3.0, poise: 90, stam: 32, wind: 300, total: 750, reach: 40, fin: true, slam: true, fx: 'heavy',
    on: { swing() { mvShockwave({ r: 56, dmg: 1.0, poise: 60, shake: 8 }); spawnFx('ground_crack', P.x - 26, P.y, -1); spawnFx('ground_crack', P.x + 26, P.y, 1); flashScreen = Math.max(flashScreen, 0.08); } } },
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
  // hold K + J: the haft jab -- back to the charge if K is still held, else the charge releases at its level
  ml_jab: { tags: ['ml_jab', 'gs_tackle', 'gs_1'], dmg: 0.7, poise: 45, stam: 10, wind: 120, total: 360, reach: 40, lunge: 22, dash: true, fx: null,
    on: { start() { P.mlJabbed = true; },
      swing() { spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 30, P.y - 14, P.face); },
      end() { const b = P.mvO.bank || 0; if (!P.ground) return; if (held.has('heavy')) mvStart('ml_charge', { bank: b, resumed: true }); else mvStart(mlRelease(mlLevel(b)), { charged: b >= 450 }); } } },
  ml_rollswing: { tags: ['ml_rollswing', 'gs_1'], dmg: 1.3, poise: 35, stam: 16, wind: 200, total: 560, reach: 36, fx: 'heavy' },
  // brace a blow -> K: the payback uppercut (stun x2)
  ml_payback: { tags: ['ml_payback', 'ml_upswing', 'gs_3'], kind: 'heavy', counter: true, dmg: 2.0, poise: 80, stun: 2, stam: 18, wind: 160, total: 600, reach: 38, launch: 220, fin: true, fx: 'slash_up' },
  ml_bb1: { tags: ['ml_bb1', 'gs_1'], rank: 3, dmg: 1.0, poise: 40, stam: 14, wind: 220, total: 520, reach: 36, fx: 'heavy', next: { K: 'ml_bb2' } },
  ml_bb2: { tags: ['ml_bb2', 'gs_2'], rank: 3, dmg: 1.0, poise: 40, stam: 14, wind: 220, total: 520, reach: 36, fx: 'heavy', next: { K: 'ml_bb3' } },
  ml_bb3: { tags: ['ml_bb3', 'gs_3'], rank: 3, dmg: 1.2, poise: 50, stam: 16, wind: 240, total: 560, reach: 36, fx: 'slash_up', next: { K: 'ml_bb4' } },
  ml_bb4: { tags: ['ml_bb4', 'gs_heavy'], rank: 3, kind: 'heavy', dmg: 3.0, poise: 90, stam: 24, wind: 360, total: 900, reach: 40, fin: true, slam: true, stun: 2, fx: 'heavy' },
  ml_air: { tags: ['ml_air', 'gs_air'], air: true, dmg: 1.2, poise: 30, stam: 16, wind: 200, total: 520, spin: true, next: { J: 'ml_spike' },
    on: { update() { if (P.mvQ && P.mvQ.b === 'J' && P.mvT >= 320 && !P.ground && mvHas(4)) { P.mvQ = null; if (mvStart('ml_spike')) return 'stop'; } } } },   // IV: J J flows on once the spin's hit is out (a jump is short)
  // IV: air J J -- the second air blow spikes small foes down and bounces you a little
  ml_spike: { tags: ['ml_spike', 'gs_air'], air: true, rank: 4, dmg: 1.3, poise: 50, stam: 14, wind: 200, total: 500, reach: 34, ys: [-30, 14], fx: 'heavy',
    can: () => !P.ground,
    on: { hit(t) { if (t && !t.boss && !t.prop && !(t.cfg && t.cfg.elite) && t.vy !== undefined) t.vy = 320; if (P.vy > -160) P.vy = -160; } } },
  ml_up: { tags: ['ml_up', 'gs_up'], up: true, dmg: 1.1, poise: 30, stam: 14, wind: 220, total: 520 },
  ml_down: { tags: ['ml_down', 'gs_down'], down: true, dmg: 1.0, poise: 50, stam: 12, wind: 140, total: 380, box: [-14, 16, -16, 26],
    on: { start() { P.mlBig = false; },   // the big bounce: after the engine's pogo (245) has fired, lift it to 290 (a jump is 272)
          update() { if (P.pogoed && !P.mlBig) { P.mlBig = true; if (P.vy < 0) P.vy = Math.min(P.vy, -290); } } } },
});
hvHoldEnd('maul', 'ml_charge');
// the brace (I): 600 ms window, then a short recovery. A blow absorbed: K = payback. Past the window, any press leaves at once.
MV_STATES.brace = (dt, ax, grav) => {
  P.braceT = (P.braceT || 0) + dt; P.braceHit = (P.braceHit || 0) - dt;
  P.vx = approach(P.vx, 0, 900 * dt); grav();
  if (P.braceAbs && peek('heavy') && P.st > 0) { take('heavy'); if (ax) P.face = ax; P.braceAbs = false; mvStart('ml_payback'); return; }
  if (P.braceT >= 0.6 && (peek('attack') || peek('roll') || (!P.braceAbs && peek('heavy')))) { setP('idle', 'idle', true); return; }
  if (P.braceT >= (P.braceEnd || 0.75)) { P.braceAbs = false; setP('idle', 'idle', true); }
};
